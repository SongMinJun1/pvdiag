#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
DEFAULT_SITES = ["conalog", "gangui", "ktc_ess"]
CORE_DIGEST_COLUMNS = [
    "date",
    "panel_id",
    "confirmed_fault",
    "critical_fault",
    "critical_source",
    "final_fault",
    "anom_level",
    "anom_subtype",
]
DISPLAY_HEURISTIC_NAME_MAP = {
    "다이오드·서브스트링형": "다이오드·국소 회로 이상형",
    "접속·부분개방형": "접촉 끊김 형",
    "센서·피드백형": "장치 측정 이상형",
    "제어응답형": "장치 응답 이상형",
    "전력변환부형": "전력변환부 이상형",
    "외부계통교란형": "외부 전원 흔들림형",
}
LIVE_FAULT_OUTPUT_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
    "1순위_의심원인_ko",
    "2순위_의심원인_ko",
    "3순위_의심원인_ko",
]
LIVE_PREVIEW_OUTPUT_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "라벨된 fault",
    "1순위_의심원인_ko",
    "2순위_의심원인_ko",
    "3순위_의심원인_ko",
    "커널로그 기존 알고리즘",
]
ROOT_LIVE_FAULT_NAME = "fault_panel_result_current_v1.csv"
ROOT_LIVE_PREVIEW_NAME = "fault_panel_result_current_preview_v1.csv"
ROOT_LIVE_SUMMARY_NAME = "live_chain_summary_v1.json"
ROOT_LIVE_REPORT_NAME = "fault_panel_result_current_report_v1.md"
ROOT_RAWONLY_FAULT_NAME = "fault_panel_result_raw_only_current_v1.csv"
ROOT_RAWONLY_PREVIEW_NAME = "fault_panel_result_raw_only_current_preview_v1.csv"
ROOT_RAWONLY_SUMMARY_NAME = "raw_only_chain_summary_v1.json"
ROOT_RAWONLY_REPORT_NAME = "fault_panel_result_raw_only_current_report_v1.md"
ROOT_MASTER_REPORT_NAME = "fault_panel_result_master_report_v1.md"
MAIL_BUCKET_ALGORITHM_MAP = {
    ("conalog", "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0"): "panel-bypass",
    ("conalog", "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"): "disconnection",
    ("gangui", "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7"): "panel-bypass",
    ("gangui", "bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16"): "panel-bypass",
    ("ktc_ess", "10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12"): "panel-bypass",
    ("ktc_ess", "70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4"): "panel-bypass",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the real panel_day_engine.py for the packaged baseline sites under a data root, "
            "export the fixed fault result artifacts, and write a shadow-compare report for engine core outputs."
        )
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        required=True,
        help="Folder containing site/raw subdirectories such as data-root/conalog/raw.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="Folder where site-wise engine outputs and fixed result tables will be written.",
    )
    parser.add_argument(
        "--sites",
        default=",".join(DEFAULT_SITES),
        help="Comma-separated site list. Defaults to conalog,gangui,ktc_ess.",
    )
    parser.add_argument(
        "--train-days",
        type=int,
        default=60,
        help="Maximum number of early days to reserve for training window proposal.",
    )
    parser.add_argument("--pattern", default="*.csv", help="Filename pattern for raw daily CSVs.")
    parser.add_argument("--epochs", type=int, default=40, help="Engine epochs. Defaults to panel_day_engine.py default.")
    parser.add_argument("--latent", type=int, default=16, help="Engine latent size. Defaults to panel_day_engine.py default.")
    parser.add_argument("--device", default="cpu", help="Torch device to pass through to panel_day_engine.py.")
    parser.add_argument(
        "--prefer-existing-site-outs",
        choices=["auto", "on", "off"],
        default="auto",
        help=(
            "Whether to automatically reuse data-root/<site>/out when available. "
            "Defaults to auto."
        ),
    )
    parser.add_argument(
        "--reuse-existing-site-outs-root",
        type=Path,
        default=None,
        help=(
            "Optional root containing precomputed data/<site>/out trees. "
            "When provided, the runner copies those outputs into the runtime workspace and skips engine execution."
        ),
    )
    parser.add_argument(
        "--run-live-chain",
        choices=["on", "off"],
        default="on",
        help="After engine execution, run the packaged bootstrap verdict -> audit -> final verdict live chain. Defaults to on.",
    )
    parser.add_argument(
        "--run-raw-only-chain",
        choices=["on", "off"],
        default="on",
        help="After engine execution, run the packaged raw-only audit -> verdict -> heuristic chain. Defaults to on.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate paths and emit the execution plan without running the engine.")
    return parser.parse_args()


def package_root() -> Path:
    return Path(__file__).resolve().parents[1]


def engine_path() -> Path:
    return package_root() / "pv_ae" / "panel_day_engine.py"


def fixed_fault6_table_path() -> Path:
    return package_root() / "artifacts" / "fault6_fixed_result_table_v1.csv"


def fixed_fault6_preview_path() -> Path:
    return package_root() / "artifacts" / "fault6_label_and_algorithm_preview_v1.csv"


def baseline_manifest_path() -> Path:
    return package_root() / "artifacts" / "input_baseline_manifest_v1.json"


def baseline_core_digest_path() -> Path:
    return package_root() / "artifacts" / "panel_day_core_baseline_digest_v1.json"


def fault6_provenance_path() -> Path:
    return package_root() / "artifacts" / "fault6_fixed_result_provenance_v1.json"


def dependency_audit_json_path() -> Path:
    return package_root() / "artifacts" / "runtime_chain_dependency_audit_v1.json"


def dependency_audit_md_path() -> Path:
    return package_root() / "artifacts" / "runtime_chain_dependency_audit_v1.md"


def packaged_share_root() -> Path:
    return package_root() / "_share"


def packaged_pipeline_root() -> Path:
    return package_root() / "research" / "prognostics"


def packaged_script_path(name: str) -> Path:
    return packaged_pipeline_root() / name


def extract_date_from_name(path: Path) -> pd.Timestamp:
    match = DATE_RE.search(path.name)
    if not match:
        return pd.NaT
    return pd.to_datetime(match.group(1), errors="coerce").normalize()


def normalize_sites(raw_sites: str) -> list[str]:
    sites = [token.strip() for token in str(raw_sites).split(",") if token.strip()]
    if not sites:
        raise SystemExit("at least one site must be provided")
    return sites


def scan_site_files(data_root: Path, site: str, pattern: str) -> tuple[pd.Timestamp, pd.Timestamp, list[Path]]:
    raw_dir = data_root / site / "raw"
    if not raw_dir.exists():
        raise SystemExit(f"missing raw dir for site={site}: {raw_dir}")
    files = sorted(path for path in raw_dir.glob(pattern) if path.is_file() and path.suffix.lower() == ".csv")
    if not files:
        raise SystemExit(f"raw csv not found for site={site}: {raw_dir}")
    valid_dates = [value for value in (extract_date_from_name(path) for path in files) if pd.notna(value)]
    if not valid_dates:
        raise SystemExit(f"no YYYY-MM-DD found in filenames for site={site}: {raw_dir}")
    return min(valid_dates), max(valid_dates), files


def propose_windows(min_date: pd.Timestamp, max_date: pd.Timestamp, train_days: int) -> dict[str, str]:
    span_days = int((max_date - min_date).days)
    proposed = min(int(train_days) - 1, max(14, int(span_days * 0.30)))
    if proposed < 1:
        proposed = 1

    train_start = min_date
    train_end = min_date + pd.Timedelta(days=proposed)
    if train_end >= max_date:
        train_end = max_date - pd.Timedelta(days=1)
    if train_end < min_date:
        raise SystemExit("date span too short to propose train/eval windows")

    eval_start = train_end + pd.Timedelta(days=1)
    eval_end = max_date
    if eval_start > eval_end:
        raise SystemExit("date span too short to propose eval window")

    return {
        "train_start": str(train_start.date()),
        "train_end": str(train_end.date()),
        "eval_start": str(eval_start.date()),
        "eval_end": str(eval_end.date()),
        "input_date_min": str(min_date.date()),
        "input_date_max": str(max_date.date()),
    }


def site_manifest(files: list[Path]) -> dict[str, object]:
    date_tokens = [match.group(1) for path in files if (match := DATE_RE.search(path.name))]
    return {
        "file_count": int(len(files)),
        "total_bytes": int(sum(path.stat().st_size for path in files)),
        "first_filenames": [path.name for path in files[:5]],
        "last_filenames": [path.name for path in files[-5:]],
        "min_date": min(date_tokens) if date_tokens else "",
        "max_date": max(date_tokens) if date_tokens else "",
    }


def build_site_plan(args: argparse.Namespace, site: str) -> tuple[dict[str, object], list[str]]:
    data_root = args.data_root.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    site_output_dir = output_root / "sites" / site / "output"
    site_log_dir = output_root / "sites" / site / "log"
    site_output_dir.mkdir(parents=True, exist_ok=True)
    site_log_dir.mkdir(parents=True, exist_ok=True)

    min_date, max_date, files = scan_site_files(data_root, site, args.pattern)
    windows = propose_windows(min_date, max_date, args.train_days)
    cmd = [
        sys.executable,
        str(engine_path()),
        "--site",
        site,
        "--data-root",
        str(data_root),
        "--out-dir",
        str(site_output_dir),
        "--log-dir",
        str(site_log_dir),
        "--pattern",
        args.pattern,
        "--train-start",
        windows["train_start"],
        "--train-end",
        windows["train_end"],
        "--eval-start",
        windows["eval_start"],
        "--eval-end",
        windows["eval_end"],
        "--epochs",
        str(args.epochs),
        "--latent",
        str(args.latent),
        "--device",
        args.device,
    ]
    plan = {
        "site": site,
        "raw_dir": str(data_root / site / "raw"),
        "output_dir": str(site_output_dir),
        "log_dir": str(site_log_dir),
        "windows": windows,
        "file_manifest": site_manifest(files),
        "command": cmd,
    }
    return plan, cmd


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_baseline_manifest() -> dict[str, object]:
    path = baseline_manifest_path()
    if not path.exists():
        raise SystemExit(f"missing packaged baseline manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def compare_to_baseline(site_plans: list[dict[str, object]]) -> dict[str, object]:
    baseline = load_baseline_manifest()
    comparison: dict[str, object] = {"all_sites_match": True, "sites": {}}
    baseline_sites = baseline.get("sites", {})
    for plan in site_plans:
        site = str(plan["site"])
        actual = plan["file_manifest"]
        expected = baseline_sites.get(site, {})
        site_match = True
        diffs: list[str] = []
        for key in ["file_count", "total_bytes", "min_date", "max_date"]:
            if actual.get(key) != expected.get(key):
                site_match = False
                diffs.append(f"{key}: expected={expected.get(key)} actual={actual.get(key)}")
        comparison["sites"][site] = {
            "match": site_match,
            "expected": expected,
            "actual": actual,
            "diffs": diffs,
        }
        if not site_match:
            comparison["all_sites_match"] = False
    comparison["note_ko"] = (
        "all_sites_match=1 이면 packaged fixed result table을 만든 baseline raw corpus와 현재 입력의 경량 fingerprint가 일치한다. "
        "일치하지 않으면 engine은 실행될 수 있어도 fixed result table exact replay 보장은 약해진다."
    )
    return comparison


def copy_fixed_results(output_root: Path) -> dict[str, str]:
    output_dir = output_root / "result"
    output_dir.mkdir(parents=True, exist_ok=True)
    fault6_dest = output_dir / "fault6_fixed_result_table_v1.csv"
    preview_dest = output_dir / "fault6_label_and_algorithm_preview_v1.csv"
    shutil.copy2(fixed_fault6_table_path(), fault6_dest)
    if fixed_fault6_preview_path().exists():
        shutil.copy2(fixed_fault6_preview_path(), preview_dest)
    return {
        "fault6_fixed_result_table_v1": str(fault6_dest),
        "fault6_label_and_algorithm_preview_v1": str(preview_dest),
    }


def copy_tree(source: Path, target: Path) -> None:
    if not source.exists():
        raise SystemExit(f"missing source tree: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, dirs_exist_ok=True)


def copy_existing_site_outs(reuse_root: Path, output_root: Path, sites: list[str]) -> dict[str, str]:
    copied: dict[str, str] = {}
    for site in sites:
        source = reuse_root / site / "out"
        target = output_root / "sites" / site / "output"
        if not source.exists():
            raise SystemExit(f"missing precomputed out dir for site={site}: {source}")
        if target.exists():
            shutil.rmtree(target)
        copy_tree(source, target)
        copied[site] = str(target)
    return copied


def site_outs_available(root: Path, sites: list[str]) -> bool:
    for site in sites:
        if not (root / site / "out" / "panel_day_core.csv").exists():
            return False
    return True


def raw_latest_mtime(root: Path, site: str) -> float | None:
    raw_dir = root / site / "raw"
    if not raw_dir.exists():
        return None
    mtimes = [path.stat().st_mtime for path in raw_dir.glob("*.csv") if path.is_file()]
    return max(mtimes) if mtimes else None


def site_outs_freshness(root: Path, sites: list[str]) -> dict[str, object]:
    site_entries: dict[str, object] = {}
    all_fresh = True
    for site in sites:
        out_path = root / site / "out" / "panel_day_core.csv"
        raw_mtime = raw_latest_mtime(root, site)
        out_exists = out_path.exists()
        out_mtime = out_path.stat().st_mtime if out_exists else None
        fresh = bool(out_exists and raw_mtime is not None and out_mtime is not None and out_mtime >= raw_mtime)
        site_entries[site] = {
            "panel_day_core_exists": out_exists,
            "raw_latest_mtime": raw_mtime,
            "panel_day_core_mtime": out_mtime,
            "fresh_enough": fresh,
        }
        if not fresh:
            all_fresh = False
    return {"all_fresh": all_fresh, "sites": site_entries}


def resolve_reuse_existing_site_outs_root(
    data_root: Path,
    explicit_reuse_root: Path | None,
    prefer_existing_site_outs: str,
    sites: list[str],
) -> tuple[Path | None, str, dict[str, object]]:
    if explicit_reuse_root is not None:
        return explicit_reuse_root, "explicit", {"mode": "explicit", "sites": {}}

    if prefer_existing_site_outs == "off":
        return None, "disabled", {"mode": "disabled", "sites": {}}

    if site_outs_available(data_root, sites):
        freshness = site_outs_freshness(data_root, sites)
        if freshness["all_fresh"]:
            return data_root, "auto_fresh" if prefer_existing_site_outs == "auto" else "forced_fresh", freshness
        if prefer_existing_site_outs == "on":
            raise SystemExit(
                "prefer-existing-site-outs=on 이지만 data-root/<site>/out 가 raw보다 오래되었음"
            )
        return None, "auto_stale_out", freshness

    if prefer_existing_site_outs == "on":
        raise SystemExit(
            f"prefer-existing-site-outs=on 이지만 data-root 아래 precomputed out를 찾지 못함: {data_root}"
        )

    return None, "not_available", {"mode": "not_available", "sites": {}}


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def truthy_mask(series: pd.Series) -> pd.Series:
    lowered = series.astype(str).str.strip().str.lower()
    return lowered.isin({"1", "true", "t", "yes"})


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def row_key(site: object, panel_id: object) -> tuple[str, str]:
    return normalize_text(site), normalize_text(panel_id)


def display_heuristic_name(raw_label: object) -> str:
    normalized = normalize_text(raw_label)
    return DISPLAY_HEURISTIC_NAME_MAP.get(normalized, normalized)


def load_raw_only_common_module():
    package = package_root()
    if str(package) not in sys.path:
        sys.path.insert(0, str(package))
    from research.prognostics import runtime_rawonly_chain_common_v1 as raw_only_common_mod

    return raw_only_common_mod


def packaged_live_chain_support() -> dict[str, object]:
    required_scripts = [
        "build_panel_day_engine_bootstrap_verdict_v1.py",
        "build_panel_day_engine_fault_panel_event_audit_v1.py",
        "build_panel_day_engine_panel_multiaxis_verdict_v1.py",
        "build_panel_day_engine_gpvs_evidence_pack_v1.py",
        "build_panel_day_engine_cause_candidate_heuristics_v1.py",
    ]
    required_share_inputs = [
        "panel_day_engine_operator_workflow_default_v1.csv",
        "panel_day_engine_abrupt6_symptom_map_v1.csv",
        "panel_day_engine_kernellog_project_mapping_v1.csv",
        "panel_day_engine_gpv7_perf_summary_v1.csv",
        "panel_day_engine_project_final_decision_pack_v1.csv",
        "panel_day_engine_precursor_onset_truth_v1.csv",
        "panel_day_engine_non_precursor_performance_cases_v1.csv",
        "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv",
        "panel_day_engine_gpvs_panel_attach_inventory_v1.csv",
        "panel_day_engine_gpvs_panel_attach_feasibility_v1.csv",
        "panel_day_engine_gpvs_panel_attach_candidates_v1.csv",
        "panel_day_engine_precursor_abrupt_consistency_cases_v1.csv",
        "panel_day_engine_precursor_abrupt_consistency_summary_v1.csv",
        "panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv",
        "panel_day_engine_c42997_1_1_forensic_summary_v1.csv",
        "panel_day_engine_fault_panel_event_audit_v1.csv",
        "panel_day_engine_detailed_fault_bridge_audit_v1.csv",
        "panel_day_engine_detailed_fault_bridge_summary_v1.csv",
        "panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv",
        "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv",
        "panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv",
        "panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv",
        "panel_day_engine_gpvs_canonical_dictionary_v1.csv",
        "panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv",
        "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv",
        "panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv",
        "panel_day_engine_gpvs_evidence_pack_v1.csv",
        "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        "panel_date_reaudit_working.csv",
    ]
    missing_scripts = [name for name in required_scripts if not packaged_script_path(name).exists()]
    missing_share = [name for name in required_share_inputs if not (packaged_share_root() / name).exists()]
    supported = not missing_scripts and not missing_share
    return {
        "supported": supported,
        "required_scripts": required_scripts,
        "required_share_inputs": required_share_inputs,
        "missing_scripts": missing_scripts,
        "missing_share_inputs": missing_share,
        "note_ko": (
            "live chain은 package 내부에 복사된 bootstrap/audit/verdict/evidence/heuristic 스크립트와 "
            "frozen share 입력을 사용해 workspace-only로 재계산한다."
        ),
    }


def packaged_raw_only_chain_support() -> dict[str, object]:
    required_scripts = [
        "runtime_rawonly_chain_common_v1.py",
        "build_panel_day_engine_runtime_fault_event_audit_v1.py",
        "build_panel_day_engine_runtime_final_verdict_v1.py",
        "build_panel_day_engine_runtime_heuristic_v1.py",
    ]
    missing_scripts = [name for name in required_scripts if not packaged_script_path(name).exists()]
    return {
        "supported": not missing_scripts,
        "required_scripts": required_scripts,
        "missing_scripts": missing_scripts,
        "note_ko": (
            "raw-only chain은 package 내부에 복사된 runtime audit/verdict/heuristic 스크립트만 사용한다. "
            "frozen share truth/support asset은 참조하지 않는다."
        ),
    }


def normalize_core_digest_frame(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    ensure_columns(df, CORE_DIGEST_COLUMNS, source_name)
    digest_df = df.loc[:, CORE_DIGEST_COLUMNS].copy()
    digest_df["date"] = pd.to_datetime(digest_df["date"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    for column in CORE_DIGEST_COLUMNS:
        if column == "date":
            continue
        digest_df[column] = digest_df[column].map(normalize_text)
    digest_df["panel_id"] = digest_df["panel_id"].astype(str)
    return digest_df.sort_values(["panel_id", "date"]).reset_index(drop=True)


def build_core_digest_payload(df: pd.DataFrame, source_name: str) -> dict[str, object]:
    digest_df = normalize_core_digest_frame(df, source_name)
    joined_rows = "\n".join(
        "|".join(normalize_text(value) for value in row)
        for row in digest_df.itertuples(index=False, name=None)
    )
    return {
        "columns": CORE_DIGEST_COLUMNS,
        "row_count": int(len(digest_df)),
        "digest_sha256": hashlib.sha256(joined_rows.encode("utf-8")).hexdigest(),
        "critical_source_counts": {
            key: int(value)
            for key, value in digest_df["critical_source"].value_counts(dropna=False).sort_index().items()
        },
        "anom_level_counts": {
            key: int(value)
            for key, value in digest_df["anom_level"].value_counts(dropna=False).sort_index().items()
        },
        "confirmed_fault_true_count": int(truthy_mask(digest_df["confirmed_fault"]).sum()),
        "critical_fault_true_count": int(truthy_mask(digest_df["critical_fault"]).sum()),
        "final_fault_true_count": int(truthy_mask(digest_df["final_fault"]).sum()),
    }


def load_core_baseline_digest() -> dict[str, object]:
    path = baseline_core_digest_path()
    if not path.exists():
        raise SystemExit(f"missing packaged core baseline digest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def compare_single_site_digest(expected: dict[str, object], actual: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for key in [
        "row_count",
        "digest_sha256",
        "confirmed_fault_true_count",
        "critical_fault_true_count",
        "final_fault_true_count",
    ]:
        if expected.get(key) != actual.get(key):
            diffs.append(f"{key}: expected={expected.get(key)} actual={actual.get(key)}")
    if expected.get("columns") != actual.get("columns"):
        diffs.append("columns: expected reference columns differ from actual columns")
    if expected.get("critical_source_counts") != actual.get("critical_source_counts"):
        diffs.append("critical_source_counts: expected reference counts differ from actual counts")
    if expected.get("anom_level_counts") != actual.get("anom_level_counts"):
        diffs.append("anom_level_counts: expected reference counts differ from actual counts")
    return diffs


def load_panel_day_core_from_workspace(workspace_root: Path, site: str) -> pd.DataFrame:
    path = workspace_root / "data" / site / "out" / "panel_day_core.csv"
    if not path.exists():
        raise SystemExit(f"missing workspace panel_day_core: {path}")
    df = pd.read_csv(path, low_memory=False)
    ensure_columns(
        df,
        ["panel_id", "date", "final_fault", "critical_fault", "fault_like_day", "critical_source"],
        path.name,
    )
    df["panel_id"] = df["panel_id"].astype(str)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def representative_algorithm_fields(site: str, core_df: pd.DataFrame, panel_id: str) -> dict[str, str]:
    mapped = MAIL_BUCKET_ALGORITHM_MAP.get((normalize_text(site), normalize_text(panel_id)), "")
    if mapped:
        return {"커널로그 기존 알고리즘": mapped}
    panel_df = core_df.loc[core_df["panel_id"].eq(str(panel_id))].copy().sort_values("date")
    if panel_df.empty:
        return {"커널로그 기존 알고리즘": ""}

    final_days = panel_df.loc[truthy_mask(panel_df["final_fault"])]
    critical_days = panel_df.loc[truthy_mask(panel_df["critical_fault"])]
    fault_like_days = panel_df.loc[truthy_mask(panel_df["fault_like_day"])]

    if not final_days.empty:
        representative = final_days.iloc[0]
    elif not critical_days.empty:
        representative = critical_days.iloc[0]
    elif not fault_like_days.empty:
        representative = fault_like_days.iloc[0]
    else:
        representative = panel_df.iloc[-1]

    return {"커널로그 기존 알고리즘": normalize_text(representative.get("critical_source"))}


def build_live_fault_table(workspace_root: Path) -> pd.DataFrame:
    verdict_path = workspace_root / "_share" / "panel_day_engine_panel_multiaxis_verdict_v1.csv"
    heuristic_path = workspace_root / "_share" / "panel_day_engine_cause_candidate_heuristics_v1.csv"
    verdict_df = pd.read_csv(verdict_path, encoding="utf-8-sig", low_memory=False)
    heuristic_df = pd.read_csv(heuristic_path, encoding="utf-8-sig", low_memory=False)
    ensure_columns(
        verdict_df,
        ["site", "panel_id", "패널고장여부_ko", "사건유형_ko", "최종고장양상_ko", "커널로그_원인군_ko"],
        verdict_path.name,
    )
    ensure_columns(
        heuristic_df,
        ["site", "panel_id", "원인후보_top1_ko", "원인후보_top2_ko", "원인후보_top3_ko"],
        heuristic_path.name,
    )

    heuristic_lookup = {
        row_key(row["site"], row["panel_id"]): row
        for row in heuristic_df.to_dict(orient="records")
    }
    rows: list[dict[str, str]] = []
    for row in verdict_df.loc[verdict_df["패널고장여부_ko"].map(normalize_text).eq("고장")].to_dict(orient="records"):
        key = row_key(row["site"], row["panel_id"])
        heuristic_row = heuristic_lookup.get(key)
        if heuristic_row is None:
            raise SystemExit(f"missing heuristic row for fault panel: {key}")
        rows.append(
            {
                "site": normalize_text(row["site"]),
                "panel_id": normalize_text(row["panel_id"]),
                "패널고장여부_ko": normalize_text(row["패널고장여부_ko"]),
                "사건유형_ko": normalize_text(row["사건유형_ko"]),
                "최종고장양상_ko": normalize_text(row["최종고장양상_ko"]),
                "커널로그_원인군_ko": normalize_text(row["커널로그_원인군_ko"]),
                "1순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top1_ko"]),
                "2순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top2_ko"]),
                "3순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top3_ko"]),
            }
        )
    return (
        pd.DataFrame(rows)
        .reindex(columns=LIVE_FAULT_OUTPUT_COLS)
        .sort_values(["site", "panel_id"], ascending=[True, True])
        .reset_index(drop=True)
    )


def build_live_fault_preview(workspace_root: Path, fault_df: pd.DataFrame) -> pd.DataFrame:
    per_site_core = {
        site: load_panel_day_core_from_workspace(workspace_root, site)
        for site in sorted(fault_df["site"].astype(str).unique())
    }
    rows: list[dict[str, str]] = []
    for _, row in fault_df.iterrows():
        site = normalize_text(row["site"])
        panel_id = normalize_text(row["panel_id"])
        rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "패널고장여부_ko": normalize_text(row["패널고장여부_ko"]),
                "사건유형_ko": normalize_text(row["사건유형_ko"]),
                "최종고장양상_ko": normalize_text(row["최종고장양상_ko"]),
                "라벨된 fault": normalize_text(row["커널로그_원인군_ko"]),
                "1순위_의심원인_ko": normalize_text(row["1순위_의심원인_ko"]),
                "2순위_의심원인_ko": normalize_text(row["2순위_의심원인_ko"]),
                "3순위_의심원인_ko": normalize_text(row["3순위_의심원인_ko"]),
                **representative_algorithm_fields(site, per_site_core[site], panel_id),
            }
        )
    return pd.DataFrame(rows).reindex(columns=LIVE_PREVIEW_OUTPUT_COLS)


def compare_live_fault_to_fixed(live_fault_df: pd.DataFrame) -> dict[str, object]:
    fixed_path = fixed_fault6_table_path()
    if not fixed_path.exists():
        return {
            "fixed_reference_available": False,
            "exact_match": False,
            "diff_columns": [],
        }
    fixed_df = pd.read_csv(fixed_path, encoding="utf-8-sig", low_memory=False).sort_values(["site", "panel_id"]).reset_index(drop=True)
    live_df = live_fault_df.sort_values(["site", "panel_id"]).reset_index(drop=True)
    diff_columns: list[str] = []
    if len(fixed_df) != len(live_df):
        diff_columns.append("__row_count__")
    else:
        for column in LIVE_FAULT_OUTPUT_COLS:
            left = fixed_df[column].fillna("").astype(str)
            right = live_df[column].fillna("").astype(str)
            if not left.equals(right):
                diff_columns.append(column)
    return {
        "fixed_reference_available": True,
        "exact_match": not diff_columns,
        "diff_columns": diff_columns,
        "fixed_row_count": int(len(fixed_df)),
        "live_row_count": int(len(live_df)),
    }


def publish_live_chain_outputs(output_root: Path, result_dir: Path, summary_path: Path) -> dict[str, str]:
    root_result_dir = output_root / "result"
    root_result_dir.mkdir(parents=True, exist_ok=True)

    mapping = {
        result_dir / "fault_panel_result_live_v1.csv": root_result_dir / ROOT_LIVE_FAULT_NAME,
        result_dir / "fault_panel_result_live_preview_v1.csv": root_result_dir / ROOT_LIVE_PREVIEW_NAME,
    }
    published: dict[str, str] = {}
    for source, target in mapping.items():
        if not source.exists():
            raise SystemExit(f"missing live chain output for publish step: {source}")
        shutil.copy2(source, target)
        published[target.name] = str(target)
    return published


def publish_raw_only_chain_outputs(output_root: Path, result_dir: Path) -> dict[str, str]:
    root_result_dir = output_root / "result"
    root_result_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        result_dir / "fault_panel_result_raw_only_v1.csv": root_result_dir / ROOT_RAWONLY_FAULT_NAME,
        result_dir / "fault_panel_result_raw_only_preview_v1.csv": root_result_dir / ROOT_RAWONLY_PREVIEW_NAME,
    }
    published: dict[str, str] = {}
    for source, target in mapping.items():
        if not source.exists():
            raise SystemExit(f"missing raw-only chain output for publish step: {source}")
        shutil.copy2(source, target)
        published[target.name] = str(target)
    return published


def markdown_table_from_df(df: pd.DataFrame) -> str:
    if df.empty:
        return "_empty_"
    safe_df = df.fillna("").astype(str)
    headers = safe_df.columns.tolist()
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in safe_df.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def truncate_report_df(df: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
    if df.empty or len(df) <= limit:
        return df
    return df.head(limit).copy()


def build_live_report_markdown(
    sites: list[str],
    baseline_comparison: dict[str, object],
    compare: dict[str, object],
    published_outputs: dict[str, str],
    live_preview_df: pd.DataFrame,
) -> str:
    site_lines = "\n".join(f"- `{site}`" for site in sites)
    baseline_site_lines = []
    for site in sites:
        site_entry = baseline_comparison.get("sites", {}).get(site, {})
        baseline_site_lines.append(
            f"- `{site}`: `match={site_entry.get('match')}`"
        )
    baseline_block = "\n".join(baseline_site_lines)
    output_lines = "\n".join(
        f"- `{name}`: `{path}`" for name, path in sorted(published_outputs.items())
    )
    return (
        "# fault_panel_result_current_report_v1\n\n"
        "## 목적\n"
        "현재 runtime 실행에서 운영자가 바로 확인할 핵심 결과를 한 곳에 모아 보여준다.\n\n"
        "## 실행 대상 site\n"
        f"{site_lines}\n\n"
        "## baseline 입력 비교\n"
        f"- `all_sites_match`: `{baseline_comparison.get('all_sites_match')}`\n"
        f"{baseline_block}\n\n"
        "## live chain 상태\n"
        f"- `fixed_fault_reference_exact_match`: `{compare.get('exact_match')}`\n"
        f"- `baseline_input_all_sites_match`: `{compare.get('baseline_input_all_sites_match')}`\n"
        f"- `diff_columns`: `{compare.get('diff_columns', [])}`\n\n"
        "## 주요 산출물\n"
        f"{output_lines}\n\n"
        "## 현재 preview 표\n"
        f"{markdown_table_from_df(live_preview_df)}\n"
    )


def build_raw_only_report_markdown(
    sites: list[str],
    compare: dict[str, object],
    published_outputs: dict[str, str],
    live_preview_df: pd.DataFrame,
) -> str:
    site_lines = "\n".join(f"- `{site}`" for site in sites)
    output_lines = "\n".join(
        f"- `{name}`: `{path}`" for name, path in sorted(published_outputs.items())
    )
    return (
        "# fault_panel_result_raw_only_current_report_v1\n\n"
        "## 목적\n"
        "raw-only algorithm candidate chain으로 계산한 현재 결과를 한 번에 확인한다.\n\n"
        "## 실행 대상 site\n"
        f"{site_lines}\n\n"
        "## raw-only vs fixed reference 비교\n"
        f"- `status_ko`: `{compare.get('status_ko')}`\n"
        f"- `reference_available`: `{compare.get('reference_available')}`\n"
        f"- `row_key_match`: `{compare.get('row_key_match')}`\n"
        f"- `decision_columns_match`: `{compare.get('decision_columns_match')}`\n"
        f"- `overlap_decision_columns_match`: `{compare.get('overlap_decision_columns_match')}`\n"
        f"- `exact_match`: `{compare.get('exact_match')}`\n"
        f"- `reference_row_count`: `{compare.get('reference_row_count')}`\n"
        f"- `candidate_row_count`: `{compare.get('candidate_row_count')}`\n"
        f"- `matched_row_key_count`: `{compare.get('matched_row_key_count')}`\n"
        f"- `diff_columns`: `{compare.get('diff_columns', [])}`\n\n"
        f"- `overlap_diff_columns`: `{compare.get('overlap_diff_columns', [])}`\n\n"
        "## 주의\n"
        "- `커널로그_원인군_ko` 컬럼명은 유지하지만, 이 report에서는 raw-only algorithm-derived family 의미다.\n"
        "- 이 chain은 frozen truth/support asset을 참조하지 않는다.\n\n"
        "- 후보 row 수가 fixed fault6보다 커질 수 있으며, 이 출력은 다른 점수/운영 신호와 함께 보는 algorithm candidate chain으로 해석한다.\n\n"
        "## 주요 산출물\n"
        f"{output_lines}\n\n"
        "## 현재 preview 표\n"
        f"{markdown_table_from_df(truncate_report_df(live_preview_df))}\n"
    )


def build_master_report_markdown(
    sites: list[str],
    baseline_comparison: dict[str, object],
    live_chain_result: dict[str, object],
    raw_only_chain_result: dict[str, object],
    live_preview_df: pd.DataFrame,
    raw_only_preview_df: pd.DataFrame,
) -> str:
    site_lines = "\n".join(f"- `{site}`" for site in sites)
    baseline_site_lines = []
    for site in sites:
        site_entry = baseline_comparison.get("sites", {}).get(site, {})
        baseline_site_lines.append(f"- `{site}`: `match={site_entry.get('match')}`")
    baseline_block = "\n".join(baseline_site_lines)
    live_compare = live_chain_result.get("fixed_fault_reference_compare", {})
    raw_only_compare = raw_only_chain_result.get("fixed_fault_reference_compare", {})
    output_lines = []
    for name, path in sorted(live_chain_result.get("published_outputs", {}).items()):
        output_lines.append(f"- `live::{name}`: `{path}`")
    for name, path in sorted(raw_only_chain_result.get("published_outputs", {}).items()):
        output_lines.append(f"- `raw_only::{name}`: `{path}`")
    output_block = "\n".join(output_lines) if output_lines else "_none_"
    return (
        "# fault_panel_result_master_report_v1\n\n"
        "## 목적\n"
        "frozen-support live chain과 raw-only algorithm candidate chain을 한 번에 같이 확인한다.\n\n"
        "## 실행 대상 site\n"
        f"{site_lines}\n\n"
        "## baseline 입력 비교\n"
        f"- `all_sites_match`: `{baseline_comparison.get('all_sites_match')}`\n"
        f"{baseline_block}\n\n"
        "## frozen-support live chain 요약\n"
        f"- `status_ko`: `{live_chain_result.get('status_ko')}`\n"
        f"- `fixed_fault_reference_exact_match`: `{live_compare.get('exact_match')}`\n"
        f"- `baseline_input_all_sites_match`: `{live_compare.get('baseline_input_all_sites_match')}`\n"
        f"- `diff_columns`: `{live_compare.get('diff_columns', [])}`\n\n"
        "## raw-only algorithm candidate chain 요약\n"
        f"- `status_ko`: `{raw_only_compare.get('status_ko')}`\n"
        f"- `reference_available`: `{raw_only_compare.get('reference_available')}`\n"
        f"- `overlap_decision_columns_match`: `{raw_only_compare.get('overlap_decision_columns_match')}`\n"
        f"- `reference_row_count`: `{raw_only_compare.get('reference_row_count')}`\n"
        f"- `candidate_row_count`: `{raw_only_compare.get('candidate_row_count')}`\n"
        f"- `matched_row_key_count`: `{raw_only_compare.get('matched_row_key_count')}`\n"
        f"- `overlap_diff_columns`: `{raw_only_compare.get('overlap_diff_columns', [])}`\n\n"
        "## 해석 가이드\n"
        "- `fault_panel_result_current_*`는 frozen-support live chain 기준 결과다.\n"
        "- `fault_panel_result_raw_only_current_*`는 raw-only algorithm candidate chain 기준 결과다.\n"
        "- raw-only chain의 `커널로그_원인군_ko`는 기존 라벨 family가 아니라 algorithm-derived family 의미다.\n"
        "- raw-only 후보 수가 더 많을 수 있으며, 이는 다른 점수/운영 신호와 함께 보는 candidate universe로 해석한다.\n\n"
        "## 주요 산출물\n"
        f"{output_block}\n\n"
        "## current preview 표\n"
        f"{markdown_table_from_df(truncate_report_df(live_preview_df))}\n\n"
        "## raw-only preview 표 (앞 20행)\n"
        f"{markdown_table_from_df(truncate_report_df(raw_only_preview_df, limit=20))}\n"
    )


def stage_live_chain_workspace(output_root: Path, sites: list[str]) -> Path:
    workspace_root = output_root / "live_chain_workspace"
    if workspace_root.exists():
        shutil.rmtree(workspace_root)
    copy_tree(packaged_share_root(), workspace_root / "_share")
    for site in sites:
        copy_tree(output_root / "sites" / site / "output", workspace_root / "data" / site / "out")
    return workspace_root


def stage_raw_only_chain_workspace(output_root: Path, sites: list[str]) -> Path:
    workspace_root = output_root / "raw_only_chain_workspace"
    if workspace_root.exists():
        shutil.rmtree(workspace_root)
    for site in sites:
        copy_tree(output_root / "sites" / site / "output", workspace_root / "data" / site / "out")
    return workspace_root


def run_live_chain(output_root: Path, sites: list[str], baseline_comparison: dict[str, object]) -> dict[str, object]:
    support = packaged_live_chain_support()
    result_dir = output_root / "result" / "live_chain"
    result_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "requested": True,
        "supported": bool(support["supported"]),
        "support": support,
        "workspace_root": "",
        "result_dir": str(result_dir),
        "status_ko": "",
        "generated_outputs": {},
        "fixed_fault_reference_compare": {},
        "note_ko": (
            "live chain은 package 내부의 bootstrap verdict -> fault_event_audit -> final verdict -> gpvs evidence -> heuristic "
            "경로를 workspace-only로 수행한다."
        ),
    }
    if not support["supported"]:
        payload["status_ko"] = "packaged live chain assets missing"
        return payload
    if sorted(sites) != sorted(DEFAULT_SITES):
        payload["status_ko"] = "current live chain supports baseline tri-site universe only"
        return payload

    workspace_root = stage_live_chain_workspace(output_root, sites)
    payload["workspace_root"] = str(workspace_root)
    commands = [
        [sys.executable, str(packaged_script_path("build_panel_day_engine_bootstrap_verdict_v1.py")), "--root", str(workspace_root), "--write-panel-verdict-alias"],
        [sys.executable, str(packaged_script_path("build_panel_day_engine_fault_panel_event_audit_v1.py")), "--root", str(workspace_root)],
        [sys.executable, str(packaged_script_path("build_panel_day_engine_panel_multiaxis_verdict_v1.py")), "--root", str(workspace_root)],
        [sys.executable, str(packaged_script_path("build_panel_day_engine_gpvs_evidence_pack_v1.py")), "--root", str(workspace_root)],
        [sys.executable, str(packaged_script_path("build_panel_day_engine_cause_candidate_heuristics_v1.py")), "--root", str(workspace_root)],
    ]
    for cmd in commands:
        subprocess.run(cmd, cwd=package_root(), check=True)

    live_fault_df = build_live_fault_table(workspace_root)
    live_preview_df = build_live_fault_preview(workspace_root, live_fault_df)
    live_fault_path = result_dir / "fault_panel_result_live_v1.csv"
    live_preview_path = result_dir / "fault_panel_result_live_preview_v1.csv"
    live_fault_df.to_csv(live_fault_path, index=False, encoding="utf-8-sig")
    live_preview_df.to_csv(live_preview_path, index=False, encoding="utf-8-sig")

    generated = {
        "bootstrap_verdict": str(workspace_root / "_share" / "panel_day_engine_bootstrap_verdict_v1.csv"),
        "fault_event_audit": str(workspace_root / "_share" / "panel_day_engine_fault_panel_event_audit_v1.csv"),
        "final_verdict": str(workspace_root / "_share" / "panel_day_engine_panel_multiaxis_verdict_v1.csv"),
        "gpvs_evidence": str(workspace_root / "_share" / "panel_day_engine_gpvs_evidence_pack_v1.csv"),
        "heuristic": str(workspace_root / "_share" / "panel_day_engine_cause_candidate_heuristics_v1.csv"),
        "fault_panel_result_live_v1": str(live_fault_path),
        "fault_panel_result_live_preview_v1": str(live_preview_path),
    }
    for name, source in [
        ("panel_day_engine_bootstrap_verdict_v1.csv", workspace_root / "_share" / "panel_day_engine_bootstrap_verdict_v1.csv"),
        ("panel_day_engine_fault_panel_event_audit_v1.csv", workspace_root / "_share" / "panel_day_engine_fault_panel_event_audit_v1.csv"),
        ("panel_day_engine_panel_multiaxis_verdict_v1.csv", workspace_root / "_share" / "panel_day_engine_panel_multiaxis_verdict_v1.csv"),
        ("panel_day_engine_gpvs_evidence_pack_v1.csv", workspace_root / "_share" / "panel_day_engine_gpvs_evidence_pack_v1.csv"),
        ("panel_day_engine_cause_candidate_heuristics_v1.csv", workspace_root / "_share" / "panel_day_engine_cause_candidate_heuristics_v1.csv"),
    ]:
        target = result_dir / name
        shutil.copy2(source, target)
        generated[name] = str(target)

    compare = compare_live_fault_to_fixed(live_fault_df)
    compare["baseline_input_all_sites_match"] = bool(baseline_comparison.get("all_sites_match", False))
    payload["generated_outputs"] = generated
    payload["fixed_fault_reference_compare"] = compare
    payload["status_ko"] = "completed"
    summary_path = result_dir / "live_chain_summary_v1.json"
    write_json(summary_path, payload)
    payload["summary_path"] = str(summary_path)
    payload["published_outputs"] = publish_live_chain_outputs(output_root, result_dir, summary_path)
    write_json(summary_path, payload)
    root_summary_path = output_root / "result" / ROOT_LIVE_SUMMARY_NAME
    shutil.copy2(summary_path, root_summary_path)
    payload["published_outputs"][ROOT_LIVE_SUMMARY_NAME] = str(root_summary_path)
    root_report_path = output_root / "result" / ROOT_LIVE_REPORT_NAME
    write_text(
        root_report_path,
        build_live_report_markdown(
            sites=sites,
            baseline_comparison=baseline_comparison,
            compare=compare,
            published_outputs=payload["published_outputs"],
            live_preview_df=live_preview_df,
        ),
    )
    payload["published_outputs"][ROOT_LIVE_REPORT_NAME] = str(root_report_path)
    write_json(summary_path, payload)
    shutil.copy2(summary_path, root_summary_path)
    return payload


def run_raw_only_chain(output_root: Path, sites: list[str]) -> dict[str, object]:
    support = packaged_raw_only_chain_support()
    result_dir = output_root / "result" / "raw_only_chain"
    result_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "requested": True,
        "supported": bool(support["supported"]),
        "support": support,
        "workspace_root": "",
        "result_dir": str(result_dir),
        "status_ko": "",
        "generated_outputs": {},
        "fixed_fault_reference_compare": {},
        "note_ko": (
            "raw-only chain은 panel_day_core와 precursor gate만 사용해 audit -> final verdict -> heuristic를 다시 계산한다. "
            "커널로그_원인군_ko는 algorithm-derived family 의미로 해석해야 한다."
        ),
    }
    if not support["supported"]:
        payload["status_ko"] = "packaged raw-only chain assets missing"
        return payload

    workspace_root = stage_raw_only_chain_workspace(output_root, sites)
    payload["workspace_root"] = str(workspace_root)
    commands = [
        [sys.executable, str(packaged_script_path("build_panel_day_engine_runtime_fault_event_audit_v1.py")), "--root", str(workspace_root)],
        [sys.executable, str(packaged_script_path("build_panel_day_engine_runtime_final_verdict_v1.py")), "--root", str(workspace_root)],
        [sys.executable, str(packaged_script_path("build_panel_day_engine_runtime_heuristic_v1.py")), "--root", str(workspace_root)],
    ]
    for cmd in commands:
        subprocess.run(cmd, cwd=package_root(), check=True)

    raw_only_common = load_raw_only_common_module()
    raw_only_fault_df = raw_only_common.build_fault_table_from_outputs(
        workspace_root=workspace_root,
        verdict_name=raw_only_common.RUNTIME_VERDICT_OUTPUT_NAME,
        heuristic_name=raw_only_common.RUNTIME_HEURISTIC_OUTPUT_NAME,
    )
    raw_only_preview_df = raw_only_common.build_fault_preview(workspace_root, raw_only_fault_df)
    raw_only_fault_path = result_dir / "fault_panel_result_raw_only_v1.csv"
    raw_only_preview_path = result_dir / "fault_panel_result_raw_only_preview_v1.csv"
    raw_only_fault_df.to_csv(raw_only_fault_path, index=False, encoding="utf-8-sig")
    raw_only_preview_df.to_csv(raw_only_preview_path, index=False, encoding="utf-8-sig")

    generated = {
        "runtime_audit": str(workspace_root / "_share" / raw_only_common.RUNTIME_AUDIT_OUTPUT_NAME),
        "runtime_verdict": str(workspace_root / "_share" / raw_only_common.RUNTIME_VERDICT_OUTPUT_NAME),
        "runtime_heuristic": str(workspace_root / "_share" / raw_only_common.RUNTIME_HEURISTIC_OUTPUT_NAME),
        "fault_panel_result_raw_only_v1": str(raw_only_fault_path),
        "fault_panel_result_raw_only_preview_v1": str(raw_only_preview_path),
    }
    for name, source in [
        (raw_only_common.RUNTIME_AUDIT_OUTPUT_NAME, workspace_root / "_share" / raw_only_common.RUNTIME_AUDIT_OUTPUT_NAME),
        (raw_only_common.RUNTIME_VERDICT_OUTPUT_NAME, workspace_root / "_share" / raw_only_common.RUNTIME_VERDICT_OUTPUT_NAME),
        (raw_only_common.RUNTIME_HEURISTIC_OUTPUT_NAME, workspace_root / "_share" / raw_only_common.RUNTIME_HEURISTIC_OUTPUT_NAME),
    ]:
        target = result_dir / name
        shutil.copy2(source, target)
        generated[name] = str(target)

    compare = raw_only_common.compare_fault_table_to_reference(raw_only_fault_df, fixed_fault6_table_path())
    payload["generated_outputs"] = generated
    payload["fixed_fault_reference_compare"] = compare
    payload["status_ko"] = "completed"
    summary_path = result_dir / "raw_only_chain_summary_v1.json"
    write_json(summary_path, payload)
    payload["summary_path"] = str(summary_path)
    payload["published_outputs"] = publish_raw_only_chain_outputs(output_root, result_dir)
    root_summary_path = output_root / "result" / ROOT_RAWONLY_SUMMARY_NAME
    shutil.copy2(summary_path, root_summary_path)
    payload["published_outputs"][ROOT_RAWONLY_SUMMARY_NAME] = str(root_summary_path)
    root_report_path = output_root / "result" / ROOT_RAWONLY_REPORT_NAME
    write_text(
        root_report_path,
        build_raw_only_report_markdown(
            sites=sites,
            compare=compare,
            published_outputs=payload["published_outputs"],
            live_preview_df=raw_only_preview_df,
        ),
    )
    payload["published_outputs"][ROOT_RAWONLY_REPORT_NAME] = str(root_report_path)
    write_json(summary_path, payload)
    shutil.copy2(summary_path, root_summary_path)
    return payload


def build_shadow_compare_report(
    output_root: Path,
    site_plans: list[dict[str, object]],
    baseline_comparison: dict[str, object],
) -> dict[str, object]:
    reference = load_core_baseline_digest()
    report: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reference_path": str(baseline_core_digest_path()),
        "note_ko": (
            "이 shadow compare는 동일 baseline raw corpus로 runtime pack을 다시 실행했을 때 "
            "panel_day_core.csv가 reference digest와 같은지 점검한다. "
            "현재는 full-chain verdict/evidence/heuristic live compare가 아니라 engine core compare만 수행한다."
        ),
        "sites": {},
        "compared_site_count": 0,
        "matched_site_count": 0,
        "all_compared_sites_match": True,
    }
    reference_sites = reference.get("sites", {})

    for plan in site_plans:
        site = str(plan["site"])
        site_entry: dict[str, object] = {
            "baseline_input_match": bool(baseline_comparison["sites"].get(site, {}).get("match", False)),
            "compared": False,
            "match": None,
            "skipped_reason": "",
            "expected": {},
            "actual": {},
            "diffs": [],
        }
        expected = reference_sites.get(site)
        if not expected:
            site_entry["skipped_reason"] = "missing_packaged_reference_digest"
            report["sites"][site] = site_entry
            continue
        if not site_entry["baseline_input_match"]:
            site_entry["skipped_reason"] = "input_manifest_mismatch"
            site_entry["expected"] = expected
            report["sites"][site] = site_entry
            continue

        core_path = output_root / "sites" / site / "output" / "panel_day_core.csv"
        if not core_path.exists():
            site_entry["skipped_reason"] = "missing_generated_panel_day_core"
            site_entry["expected"] = expected
            report["sites"][site] = site_entry
            continue

        actual_df = pd.read_csv(core_path, low_memory=False)
        actual_digest = build_core_digest_payload(actual_df, core_path.name)
        diffs = compare_single_site_digest(expected, actual_digest)
        site_entry.update(
            {
                "compared": True,
                "match": not diffs,
                "expected": expected,
                "actual": actual_digest,
                "diffs": diffs,
            }
        )
        report["sites"][site] = site_entry
        report["compared_site_count"] += 1
        if not diffs:
            report["matched_site_count"] += 1
        else:
            report["all_compared_sites_match"] = False

    if report["compared_site_count"] == 0:
        report["all_compared_sites_match"] = False
    return report


def main() -> None:
    args = parse_args()
    if not engine_path().exists():
        raise SystemExit(f"missing packaged engine: {engine_path()}")

    data_root = args.data_root.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    reuse_existing_site_outs_root = (
        args.reuse_existing_site_outs_root.expanduser().resolve()
        if args.reuse_existing_site_outs_root is not None
        else None
    )

    sites = normalize_sites(args.sites)
    effective_reuse_existing_site_outs_root, reuse_decision, reuse_freshness = resolve_reuse_existing_site_outs_root(
        data_root=data_root,
        explicit_reuse_root=reuse_existing_site_outs_root,
        prefer_existing_site_outs=args.prefer_existing_site_outs,
        sites=sites,
    )
    site_plans: list[dict[str, object]] = []
    commands: list[list[str]] = []
    for site in sites:
        plan, cmd = build_site_plan(args, site)
        site_plans.append(plan)
        commands.append(cmd)

    fixed_outputs = copy_fixed_results(output_root)
    baseline_comparison = compare_to_baseline(site_plans)
    live_chain_support = packaged_live_chain_support()
    raw_only_chain_support = packaged_raw_only_chain_support()
    live_chain_plan = {
        "requested": args.run_live_chain == "on",
        "supported": bool(live_chain_support["supported"]),
        "support": live_chain_support,
        "status_ko": "",
    }
    if not live_chain_plan["requested"]:
        live_chain_plan["status_ko"] = "disabled by option"
    elif sorted(sites) != sorted(DEFAULT_SITES):
        live_chain_plan["status_ko"] = "current live chain supports baseline tri-site universe only"
    elif not live_chain_plan["supported"]:
        live_chain_plan["status_ko"] = "packaged live chain assets missing"
    else:
        live_chain_plan["status_ko"] = (
            "will run after precomputed out reuse"
            if effective_reuse_existing_site_outs_root is not None
            else "will run after engine execution"
        )
    raw_only_chain_plan = {
        "requested": args.run_raw_only_chain == "on",
        "supported": bool(raw_only_chain_support["supported"]),
        "support": raw_only_chain_support,
        "status_ko": "",
    }
    if not raw_only_chain_plan["requested"]:
        raw_only_chain_plan["status_ko"] = "disabled by option"
    elif not raw_only_chain_plan["supported"]:
        raw_only_chain_plan["status_ko"] = "packaged raw-only chain assets missing"
    else:
        raw_only_chain_plan["status_ko"] = (
            "will run after precomputed out reuse"
            if effective_reuse_existing_site_outs_root is not None
            else "will run after engine execution"
        )

    plan = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "package_root": str(package_root()),
        "engine_path": str(engine_path()),
        "data_root": str(data_root),
        "output_root": str(output_root),
        "reuse_existing_site_outs_root": str(reuse_existing_site_outs_root) if reuse_existing_site_outs_root else "",
        "effective_reuse_existing_site_outs_root": (
            str(effective_reuse_existing_site_outs_root)
            if effective_reuse_existing_site_outs_root
            else ""
        ),
        "prefer_existing_site_outs": args.prefer_existing_site_outs,
        "reuse_decision_ko": reuse_decision,
        "reuse_freshness": reuse_freshness,
        "execution_mode_ko": (
            "auto_reuse_existing_site_outs"
            if effective_reuse_existing_site_outs_root is not None and reuse_decision == "auto_fresh"
            else "reuse_precomputed_site_outs"
            if effective_reuse_existing_site_outs_root is not None
            else "run_engine_then_live_chain"
        ),
        "sites": sites,
        "site_plans": site_plans,
        "fixed_outputs": fixed_outputs,
        "baseline_comparison": baseline_comparison,
        "live_chain": live_chain_plan,
        "raw_only_chain": raw_only_chain_plan,
        "shadow_compare_reference_path": str(baseline_core_digest_path()),
        "fault6_provenance_path": str(fault6_provenance_path()),
        "dependency_audit_json_path": str(dependency_audit_json_path()),
        "dependency_audit_md_path": str(dependency_audit_md_path()),
        "shadow_compare_report_path": str(output_root / "shadow_compare_v1.json"),
        "dry_run": bool(args.dry_run),
        "note_ko": (
            "이 pack은 conalog/gangui/ktc_ess baseline sites에 대해 실제 panel_day_engine.py 를 실행하고, "
            "현재 frozen fault 결과표도 함께 export 한다. "
            "fault6 결과표 provenance도 함께 남겨, 이 표가 frozen verdict+heuristic direct assembly인지 확인할 수 있다. "
            "추가로 baseline core output shadow compare 경로를 남겨, same baseline 입력일 때 engine core output이 유지되는지도 점검한다."
        ),
    }

    if args.dry_run:
        write_json(output_root / "run_plan_v1.json", plan)
        print(f"[OK] dry-run plan written: {output_root / 'run_plan_v1.json'}")
        return

    reused_site_outs: dict[str, str] = {}
    if effective_reuse_existing_site_outs_root is not None:
        reused_site_outs = copy_existing_site_outs(effective_reuse_existing_site_outs_root, output_root, sites)
    else:
        for cmd in commands:
            subprocess.run(cmd, check=True)

    shadow_compare = build_shadow_compare_report(output_root, site_plans, baseline_comparison)
    write_json(output_root / "shadow_compare_v1.json", shadow_compare)
    live_chain_result = {"requested": False, "status_ko": "not requested"}
    if args.run_live_chain == "on":
        live_chain_result = run_live_chain(output_root, sites, baseline_comparison)
    raw_only_chain_result = {"requested": False, "status_ko": "not requested"}
    if args.run_raw_only_chain == "on":
        raw_only_chain_result = run_raw_only_chain(output_root, sites)

    master_report_path = output_root / "result" / ROOT_MASTER_REPORT_NAME
    live_preview_path = output_root / "result" / ROOT_LIVE_PREVIEW_NAME
    raw_only_preview_path = output_root / "result" / ROOT_RAWONLY_PREVIEW_NAME
    live_preview_df = pd.read_csv(live_preview_path, encoding="utf-8-sig", low_memory=False) if live_preview_path.exists() else pd.DataFrame()
    raw_only_preview_df = pd.read_csv(raw_only_preview_path, encoding="utf-8-sig", low_memory=False) if raw_only_preview_path.exists() else pd.DataFrame()
    write_text(
        master_report_path,
        build_master_report_markdown(
            sites=sites,
            baseline_comparison=baseline_comparison,
            live_chain_result=live_chain_result,
            raw_only_chain_result=raw_only_chain_result,
            live_preview_df=live_preview_df,
            raw_only_preview_df=raw_only_preview_df,
        ),
    )

    metadata = {
        **plan,
        "dry_run": False,
        "reused_site_outs": reused_site_outs,
        "shadow_compare": shadow_compare,
        "live_chain": live_chain_result,
        "raw_only_chain": raw_only_chain_result,
        "master_report_path": str(master_report_path),
    }
    write_json(output_root / "run_metadata_v1.json", metadata)
    print(f"[OK] result dir: {output_root / 'result'}")
    print(f"[OK] shadow compare: {output_root / 'shadow_compare_v1.json'}")
    print(f"[OK] master report: {master_report_path}")
    if live_chain_result.get("requested"):
        print(f"[OK] live chain status: {live_chain_result.get('status_ko')}")
    if raw_only_chain_result.get("requested"):
        print(f"[OK] raw-only chain status: {raw_only_chain_result.get('status_ko')}")
    for site in sites:
        print(f"[OK] site output: {output_root / 'sites' / site / 'output' / 'panel_day_core.csv'}")


if __name__ == "__main__":
    main()
