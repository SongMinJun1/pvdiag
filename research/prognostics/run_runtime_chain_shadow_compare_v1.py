#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_RUNTIME_PACK_SCRIPT = REPO_ROOT / "research" / "prognostics" / "build_conalog_full_runtime_pack_v1.py"
PACK_RUNNER = REPO_ROOT / "release" / "conalog_full_runtime_v1" / "package" / "app" / "run_full_algorithm_pack.py"
FAULT_EVENT_AUDIT_SCRIPT = REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_fault_panel_event_audit_v1.py"
VERDICT_SCRIPT = REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_panel_multiaxis_verdict_v1.py"
GPVS_EVIDENCE_SCRIPT = REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_gpvs_evidence_pack_v1.py"
HEURISTIC_SCRIPT = REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_cause_candidate_heuristics_v1.py"
BASELINE_SITES = ["conalog", "gangui", "ktc_ess"]

COMPARE_TARGETS = [
    "panel_day_engine_fault_panel_event_audit_v1.csv",
    "panel_day_engine_fault_panel_event_audit_summary_v1.csv",
    "panel_day_engine_panel_multiaxis_verdict_v1.csv",
    "panel_day_engine_panel_multiaxis_verdict_summary_v1.csv",
    "panel_day_engine_gpvs_evidence_pack_v1.csv",
    "panel_day_engine_gpvs_evidence_summary_v1.csv",
    "panel_day_engine_cause_candidate_heuristics_v1.csv",
    "panel_day_engine_cause_candidate_summary_v1.csv",
]

KEYED_DIFF_COLUMNS: dict[str, list[str]] = {
    "panel_day_engine_fault_panel_event_audit_v1.csv": [
        "site",
        "panel_id",
        "현재표_사건유형_ko",
        "현재표_최종고장양상_ko",
        "earliest_warning_date",
        "retrospective_onset_date",
        "strict_trigger_date",
        "first_final_fault_date",
        "dead_diag_date",
        "onset_confidence",
        "onset_method",
        "전조흔적_flag",
        "순수급작_flag",
        "전조평가셋편입_flag",
        "급작평가셋편입_flag",
        "사건유형_재판정_ko",
        "최종고장양상_재판정_ko",
        "재판정_근거_ko",
        "현재표_보정필요여부_flag",
    ],
    "panel_day_engine_panel_multiaxis_verdict_v1.csv": [
        "site",
        "panel_id",
        "사건유형_ko",
        "최종고장양상_ko",
        "대표판정_ko",
        "패널고장여부_ko",
        "커널로그_원인군_ko",
        "GPVS_적용대상_ko",
        "판정주의_ko",
    ],
    "panel_day_engine_gpvs_evidence_pack_v1.csv": [
        "site",
        "panel_id",
        "사건유형_ko",
        "최종고장양상_ko",
        "커널로그_원인군_ko",
        "GPVS_내부판정_ko",
        "GPVS_외부참조패턴_ko",
        "GPVS_호환성판정_ko",
        "GPVS_매칭정책_ko",
        "GPVS_최종사용권고_ko",
    ],
    "panel_day_engine_cause_candidate_heuristics_v1.csv": [
        "site",
        "panel_id",
        "사건유형_ko",
        "최종고장양상_ko",
        "커널로그_원인군_ko",
        "원인후보_top1_ko",
        "원인후보_top2_ko",
        "원인후보_top3_ko",
        "원인후보_경합상태_ko",
        "원인후보_실증우선확인_ko",
        "원인후보_신뢰도_ko",
    ],
}

DECISION_COLUMNS: dict[str, list[str]] = {
    "panel_day_engine_fault_panel_event_audit_v1.csv": [
        "사건유형_재판정_ko",
        "최종고장양상_재판정_ko",
        "현재표_보정필요여부_flag",
    ],
    "panel_day_engine_panel_multiaxis_verdict_v1.csv": [
        "사건유형_ko",
        "최종고장양상_ko",
        "대표판정_ko",
        "패널고장여부_ko",
        "커널로그_원인군_ko",
        "GPVS_적용대상_ko",
    ],
    "panel_day_engine_gpvs_evidence_pack_v1.csv": [
        "사건유형_ko",
        "최종고장양상_ko",
        "커널로그_원인군_ko",
        "GPVS_내부판정_ko",
        "GPVS_외부참조패턴_ko",
        "GPVS_호환성판정_ko",
        "GPVS_매칭정책_ko",
        "GPVS_최종사용권고_ko",
    ],
    "panel_day_engine_cause_candidate_heuristics_v1.csv": [
        "사건유형_ko",
        "최종고장양상_ko",
        "커널로그_원인군_ko",
        "원인후보_top1_ko",
        "원인후보_top2_ko",
        "원인후보_top3_ko",
        "원인후보_경합상태_ko",
        "원인후보_실증우선확인_ko",
        "원인후보_신뢰도_ko",
    ],
}

KNOWN_NON_DECISION_DELTAS: dict[str, list[dict[str, str]]] = {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a workspace-only 2-pass shadow compare for fault_event_audit -> verdict -> gpvs evidence -> "
            "heuristic without changing the frozen official outputs."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root. Defaults to the current project root.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="Folder where workspace, live-engine outputs, and compare reports will be written.",
    )
    parser.add_argument(
        "--sites",
        default=",".join(BASELINE_SITES),
        help="Sites to refresh with live engine before the 2-pass compare. Non-selected baseline sites reuse existing out/.",
    )
    parser.add_argument(
        "--reuse-existing-site-outs",
        action="store_true",
        help="Skip the live engine refresh and seed all baseline sites from the repo's current data/<site>/out.",
    )
    parser.add_argument("--epochs", type=int, default=1, help="Epochs to pass to the packaged runtime engine when refreshing sites.")
    parser.add_argument("--device", default="cpu", help="Torch device to pass to the packaged runtime engine.")
    parser.add_argument(
        "--keep-workspace",
        action="store_true",
        help="Keep any existing workspace directory instead of removing it first.",
    )
    return parser.parse_args()


def normalize_sites(raw_sites: str) -> list[str]:
    sites = [token.strip() for token in str(raw_sites).split(",") if token.strip()]
    unknown = [site for site in sites if site not in BASELINE_SITES]
    if unknown:
        raise SystemExit(f"unsupported sites for shadow compare: {unknown}")
    return sites or BASELINE_SITES.copy()


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def copy_tree(source: Path, target: Path) -> None:
    if not source.exists():
        raise SystemExit(f"missing source tree: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, dirs_exist_ok=True)


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def prepare_live_engine_outputs(root: Path, output_root: Path, live_sites: list[str], epochs: int, device: str) -> Path:
    run([sys.executable, str(BUILD_RUNTIME_PACK_SCRIPT)], cwd=root)
    live_output_root = output_root / "live_engine"
    if live_output_root.exists():
        shutil.rmtree(live_output_root)
    cmd = [
        sys.executable,
        str(PACK_RUNNER),
        "--data-root",
        str(root / "data"),
        "--output-root",
        str(live_output_root),
        "--sites",
        ",".join(live_sites),
        "--epochs",
        str(epochs),
        "--device",
        device,
    ]
    run(cmd, cwd=root)
    return live_output_root


def seed_workspace(root: Path, workspace_root: Path, live_output_root: Path | None, live_sites: list[str]) -> dict[str, str]:
    if workspace_root.exists():
        shutil.rmtree(workspace_root)
    (workspace_root / "_share").mkdir(parents=True, exist_ok=True)
    (workspace_root / "data").mkdir(parents=True, exist_ok=True)

    copy_tree(root / "_share", workspace_root / "_share")

    site_seed_mode: dict[str, str] = {}
    for site in BASELINE_SITES:
        target_out = workspace_root / "data" / site / "out"
        if live_output_root is not None and site in live_sites:
            source_out = live_output_root / "sites" / site / "output"
            site_seed_mode[site] = "live_engine_refresh"
        else:
            source_out = root / "data" / site / "out"
            site_seed_mode[site] = "repo_existing_out"
        copy_tree(source_out, target_out)
    return site_seed_mode


def run_shadow_chain(root: Path, workspace_root: Path) -> None:
    for script in [
        FAULT_EVENT_AUDIT_SCRIPT,
        VERDICT_SCRIPT,
        GPVS_EVIDENCE_SCRIPT,
        HEURISTIC_SCRIPT,
    ]:
        run([sys.executable, str(script), "--root", str(workspace_root)], cwd=root)


def csv_digest(path: Path) -> dict[str, object]:
    if not path.exists():
        return {
            "exists": False,
            "row_count": 0,
            "columns": [],
            "digest_sha256": "",
        }
    df = pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
    if {"site", "panel_id"}.issubset(df.columns):
        df = df.sort_values(["site", "panel_id"]).reset_index(drop=True)
    normalized = df.copy()
    for column in normalized.columns:
        normalized[column] = normalized[column].map(normalize_text)
    rows_text = "\n".join(
        "|".join(normalize_text(value) for value in row)
        for row in normalized.itertuples(index=False, name=None)
    )
    return {
        "exists": True,
        "row_count": int(len(normalized)),
        "columns": [str(column) for column in normalized.columns.tolist()],
        "digest_sha256": hashlib.sha256(rows_text.encode("utf-8")).hexdigest(),
    }


def compare_target(root: Path, workspace_root: Path, name: str) -> dict[str, object]:
    reference_path = root / "_share" / name
    candidate_path = workspace_root / "_share" / name
    reference = csv_digest(reference_path)
    candidate = csv_digest(candidate_path)
    diffs: list[str] = []
    for key in ["exists", "row_count", "columns", "digest_sha256"]:
        if reference.get(key) != candidate.get(key):
            diffs.append(f"{key}: reference={reference.get(key)} candidate={candidate.get(key)}")
    return {
        "reference_path": str(reference_path),
        "candidate_path": str(candidate_path),
        "match": not diffs,
        "reference": reference,
        "candidate": candidate,
        "diffs": diffs,
    }


def csv_column_diff_summary(reference_path: Path, candidate_path: Path, name: str) -> dict[str, object]:
    columns = KEYED_DIFF_COLUMNS.get(name)
    if not columns:
        return {}
    if not reference_path.exists() or not candidate_path.exists():
        return {}

    ref_df = pd.read_csv(reference_path, low_memory=False, encoding="utf-8-sig")
    cand_df = pd.read_csv(candidate_path, low_memory=False, encoding="utf-8-sig")
    available = [column for column in columns if column in ref_df.columns and column in cand_df.columns]
    if not {"site", "panel_id"}.issubset(available):
        return {}

    ref_df = ref_df.loc[:, available].copy()
    cand_df = cand_df.loc[:, available].copy()
    merged = ref_df.merge(cand_df, on=["site", "panel_id"], how="outer", suffixes=("_reference", "_candidate"), indicator=True)

    merge_counts = {key: int(value) for key, value in merged["_merge"].value_counts().sort_index().items()}
    differing_columns: dict[str, int] = {}
    differing_rows_by_column: dict[str, list[dict[str, str]]] = {}
    decision_diff_columns: list[str] = []
    decision_columns = set(DECISION_COLUMNS.get(name, []))
    known_delta_lookup = {
        (entry["site"], entry["panel_id"], entry["column"]): entry["reason_ko"]
        for entry in KNOWN_NON_DECISION_DELTAS.get(name, [])
    }
    matched_known_deltas: list[dict[str, str]] = []
    unexpected_deltas: list[dict[str, str]] = []

    for column in available:
        if column in {"site", "panel_id"}:
            continue
        left = merged[f"{column}_reference"].fillna("").astype(str)
        right = merged[f"{column}_candidate"].fillna("").astype(str)
        diff_mask = left != right
        diff_count = int(diff_mask.sum())
        if diff_count:
            differing_columns[column] = diff_count
            sample_rows = []
            for _, row in merged.loc[diff_mask, ["site", "panel_id", f"{column}_reference", f"{column}_candidate"]].head(5).iterrows():
                sample_rows.append(
                    {
                        "site": normalize_text(row["site"]),
                        "panel_id": normalize_text(row["panel_id"]),
                        "reference": normalize_text(row[f"{column}_reference"]),
                        "candidate": normalize_text(row[f"{column}_candidate"]),
                    }
                )
            differing_rows_by_column[column] = sample_rows
            for sample in sample_rows:
                key = (sample["site"], sample["panel_id"], column)
                if key in known_delta_lookup:
                    matched_known_deltas.append(
                        {
                            "site": sample["site"],
                            "panel_id": sample["panel_id"],
                            "column": column,
                            "reason_ko": known_delta_lookup[key],
                        }
                    )
                else:
                    unexpected_deltas.append(
                        {
                            "site": sample["site"],
                            "panel_id": sample["panel_id"],
                            "column": column,
                        }
                    )
            if column in decision_columns:
                decision_diff_columns.append(column)

    classification = "exact_match"
    explainable = True
    explainable_reason = ""
    if differing_columns:
        if decision_diff_columns:
            classification = "decision_delta"
            explainable = False
            explainable_reason = "decision columns changed"
        elif matched_known_deltas and not unexpected_deltas:
            classification = "known_non_decision_delta"
            explainable = True
            explainable_reason = "only known non-decision delta rows changed"
        else:
            classification = "non_decision_delta"
            explainable = True
            explainable_reason = "only meta/explanation/eval-set fields changed"

    return {
        "available_columns": available,
        "merge_counts": merge_counts,
        "differing_columns": differing_columns,
        "differing_rows_by_column": differing_rows_by_column,
        "decision_columns": sorted(decision_columns),
        "decision_diff_columns": decision_diff_columns,
        "matched_known_deltas": matched_known_deltas,
        "unexpected_deltas": unexpected_deltas,
        "classification": classification,
        "explainable_flag": explainable,
        "explainable_reason_ko": explainable_reason,
    }


def build_report(
    root: Path,
    output_root: Path,
    workspace_root: Path,
    live_output_root: Path | None,
    live_sites: list[str],
    site_seed_mode: dict[str, str],
) -> dict[str, object]:
    report = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": str(root),
        "workspace_root": str(workspace_root),
        "live_output_root": str(live_output_root) if live_output_root is not None else "",
        "live_sites": live_sites,
        "site_seed_mode": site_seed_mode,
        "all_targets_match": True,
        "all_decision_targets_match": True,
        "all_nonexact_deltas_explainable": True,
        "all_known_nondecision_deltas_accounted_for": True,
        "targets": {},
        "note_ko": (
            "이 report는 frozen verdict를 seed로 fault_event_audit를 먼저 만들고, 그 뒤 verdict -> gpvs evidence -> heuristic를 "
            "workspace에서만 다시 계산해 frozen reference와 diff를 비교한 결과다. 공식 _share 산출물은 건드리지 않는다."
        ),
    }
    for name in COMPARE_TARGETS:
        target_result = compare_target(root, workspace_root, name)
        target_result["column_analysis"] = csv_column_diff_summary(
            root / "_share" / name,
            workspace_root / "_share" / name,
            name,
        )
        report["targets"][name] = target_result
        if not target_result["match"]:
            report["all_targets_match"] = False
        column_analysis = target_result.get("column_analysis", {})
        if column_analysis:
            if column_analysis.get("decision_diff_columns"):
                report["all_decision_targets_match"] = False
            if column_analysis.get("classification") != "exact_match" and not column_analysis.get("explainable_flag", False):
                report["all_nonexact_deltas_explainable"] = False
            if column_analysis.get("unexpected_deltas"):
                report["all_known_nondecision_deltas_accounted_for"] = False

    report["topline_ko"] = (
        "decision columns are preserved"
        if report["all_decision_targets_match"]
        else "decision columns changed"
    )
    report_path = output_root / "runtime_chain_shadow_compare_v1.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    workspace_root = output_root / "workspace"

    live_sites = normalize_sites(args.sites)
    if workspace_root.exists() and not args.keep_workspace:
        shutil.rmtree(workspace_root)

    live_output_root: Path | None = None
    if not args.reuse_existing_site_outs:
        live_output_root = prepare_live_engine_outputs(root, output_root, live_sites, args.epochs, args.device)

    site_seed_mode = seed_workspace(root, workspace_root, live_output_root, live_sites if live_output_root else [])
    run_shadow_chain(root, workspace_root)
    report = build_report(root, output_root, workspace_root, live_output_root, live_sites, site_seed_mode)
    report_path = output_root / "runtime_chain_shadow_compare_v1.json"
    print(f"[OK] shadow compare report: {report_path}")
    print(f"[OK] all_targets_match={report['all_targets_match']}")


if __name__ == "__main__":
    main()
