#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
if __package__ in {None, ""}:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from research.prognostics.heuristic_display_registry_v1 import (
        DISPLAY_HEURISTIC_NAME_MAP,
        display_heuristic_name as shared_display_heuristic_name,
    )
else:
    from .heuristic_display_registry_v1 import (
        DISPLAY_HEURISTIC_NAME_MAP,
        display_heuristic_name as shared_display_heuristic_name,
    )

RELEASE_ROOT = REPO_ROOT / "release" / "conalog_full_runtime_v1"
PACKAGE_ROOT = RELEASE_ROOT / "package"
PACKAGE_APP_ROOT = PACKAGE_ROOT / "app"
ENGINE_SRC = REPO_ROOT / "pv_ae" / "panel_day_engine.py"
ENGINE_DST = PACKAGE_ROOT / "pv_ae" / "panel_day_engine.py"
IMPORT_ANY_CSV_SRC = REPO_ROOT / "research" / "prognostics" / "import_any_csv_root_v1.py"
IMPORT_ANY_CSV_DST = PACKAGE_APP_ROOT / "import_any_csv_root.py"
VERDICT_PATH = REPO_ROOT / "_share" / "panel_day_engine_panel_multiaxis_verdict_v1.csv"
HEURISTIC_PATH = REPO_ROOT / "_share" / "panel_day_engine_cause_candidate_heuristics_v1.csv"
LEGACY_INTEGRATED_TABLE_PATH = REPO_ROOT / "_share" / "panel_day_engine_integrated_result_table_v1.csv"
FAULT6_ARTIFACT_PATH = PACKAGE_ROOT / "artifacts" / "fault6_fixed_result_table_v1.csv"
FAULT6_PREVIEW_ARTIFACT_PATH = PACKAGE_ROOT / "artifacts" / "fault6_label_and_algorithm_preview_v1.csv"
KTC_FAULT2_PREVIEW_ARTIFACT_PATH = PACKAGE_ROOT / "artifacts" / "ktc_fault2_label_and_algorithm_preview_v1.csv"
FAULT6_PROVENANCE_PATH = PACKAGE_ROOT / "artifacts" / "fault6_fixed_result_provenance_v1.json"
BASELINE_MANIFEST_PATH = PACKAGE_ROOT / "artifacts" / "input_baseline_manifest_v1.json"
CORE_BASELINE_DIGEST_PATH = PACKAGE_ROOT / "artifacts" / "panel_day_core_baseline_digest_v1.json"
DEPENDENCY_AUDIT_JSON_PATH = PACKAGE_ROOT / "artifacts" / "runtime_chain_dependency_audit_v1.json"
DEPENDENCY_AUDIT_MD_PATH = PACKAGE_ROOT / "artifacts" / "runtime_chain_dependency_audit_v1.md"
SUMMARY_PATH = RELEASE_ROOT / "pack_summary_v1.json"
STAGING_PS1_PATH = PACKAGE_ROOT / "bin" / "stage_recent_120d.ps1"
SNAPSHOT_COPY_PS1_PATH = PACKAGE_ROOT / "bin" / "snapshot_copy.ps1"
DAILY_RUN_BAT_PATH = PACKAGE_ROOT / "bin" / "daily_run.bat"
INCREMENTAL_RUN_BAT_PATH = PACKAGE_ROOT / "bin" / "incremental_run.bat"
RUN_DEMO_BAT_PATH = PACKAGE_ROOT / "bin" / "run_demo.bat"
RUN_DEMO_KTC_FAULT2_BAT_PATH = PACKAGE_ROOT / "bin" / "run_demo_ktc_fault2.bat"
RUN_GUIDED_REAL_BAT_PATH = PACKAGE_ROOT / "bin" / "run_guided_real.bat"
RUN_IMPORTED_REAL_BAT_PATH = PACKAGE_ROOT / "bin" / "run_imported_real.bat"
RESOLVE_PYTHON_BAT_PATH = PACKAGE_ROOT / "bin" / "resolve_python.bat"
PACKAGE_RESEARCH_ROOT = PACKAGE_ROOT / "research" / "prognostics"
PACKAGE_SHARE_ROOT = PACKAGE_ROOT / "_share"
PACKAGE_RUNTIME_ROOT = PACKAGE_ROOT / "runtime"
WINDOWS_RUNTIME_ROOT = PACKAGE_RUNTIME_ROOT / "windows_x64"
WINDOWS_RUNTIME_PYTHON_ROOT = WINDOWS_RUNTIME_ROOT / "python"
WINDOWS_RUNTIME_WHEELHOUSE = WINDOWS_RUNTIME_ROOT / "wheelhouse"
WINDOWS_RUNTIME_CACHE = WINDOWS_RUNTIME_ROOT / "cache"
WINDOWS_RUNTIME_MANIFEST_PATH = WINDOWS_RUNTIME_ROOT / "runtime_manifest_v1.json"
WINDOWS_RUNTIME_README_PATH = WINDOWS_RUNTIME_ROOT / "README_WINDOWS_RUNTIME.md"
WINDOWS_EMBED_PYTHON_VERSION = "3.11.9"
WINDOWS_EMBED_ZIP_URL = (
    f"https://www.python.org/ftp/python/{WINDOWS_EMBED_PYTHON_VERSION}/"
    f"python-{WINDOWS_EMBED_PYTHON_VERSION}-embed-amd64.zip"
)
WINDOWS_RUNTIME_PRIMARY_PACKAGES = [
    "numpy==2.3.4",
    "pandas==2.3.3",
    "tqdm==4.67.1",
    "torch==2.9.1",
    "openpyxl==3.1.5",
]

FAULT6_REQUIRED_COLS = [
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
VERDICT_FAULT_REQUIRED_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
]
HEURISTIC_REQUIRED_COLS = [
    "site",
    "panel_id",
    "원인후보_top1_ko",
    "원인후보_top2_ko",
    "원인후보_top3_ko",
]
BASELINE_SITES = ["conalog", "gangui", "ktc_ess"]
PREVIEW_OUTPUT_COLS = [
    "site",
    "panel_id",
    "전조날짜",
    "고장 기준일",
    "운영 판정",
    "급락 종결 관측",
    "점진 저하 누적",
    "사건 종결 요약",
    "상위 해석 후보",
    "기존 알고리즘 source",
]
MAIL_BUCKET_ALGORITHM_MAP = {
    ("conalog", "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0"): "panel-bypass",
    ("conalog", "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"): "disconnection",
    ("gangui", "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7"): "panel-bypass",
    ("gangui", "bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16"): "panel-bypass",
}
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
REQUIRED_VERDICT_SHARE_INPUTS = [
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
]
REQUIRED_GPVS_INPUTS = [
    "panel_day_engine_panel_multiaxis_verdict_v1.csv",
    "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv",
    "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv",
    "panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv",
    "panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv",
]
REQUIRED_HEURISTIC_INPUTS = [
    "panel_day_engine_gpvs_evidence_pack_v1.csv",
    "panel_day_engine_panel_multiaxis_verdict_v1.csv",
]
REQUIRED_FAULT_EVENT_AUDIT_INPUTS = [
    "panel_day_engine_panel_multiaxis_verdict_v1.csv",
    "panel_day_engine_abrupt6_symptom_map_v1.csv",
    "panel_day_engine_precursor_onset_truth_v1.csv",
    "panel_date_reaudit_working.csv",
    "vendor_reply_adjudication_latest.csv (optional)",
    "data/<site>/out/panel_day_core.csv",
    "data/<site>/out/ae_simple_local_precursor_gate_daily.csv",
]
PACKAGED_RUNTIME_CHAIN_SCRIPTS = [
    REPO_ROOT / "research" / "prognostics" / "runtime_rawonly_chain_common_v1.py",
    REPO_ROOT / "research" / "prognostics" / "heuristic_display_registry_v1.py",
    REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_bootstrap_verdict_v1.py",
    REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_fault_panel_event_audit_v1.py",
    REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_panel_multiaxis_verdict_v1.py",
    REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_gpvs_evidence_pack_v1.py",
    REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_cause_candidate_heuristics_v1.py",
    REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_runtime_fault_event_audit_v1.py",
    REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_runtime_final_verdict_v1.py",
    REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_runtime_heuristic_v1.py",
]
OPTIONAL_PACKAGED_SHARE_INPUTS = {
    "vendor_reply_adjudication_latest.csv",
}
PACKAGED_RUNTIME_CHAIN_SHARE_INPUTS = sorted(
    set(REQUIRED_VERDICT_SHARE_INPUTS)
    | set(REQUIRED_GPVS_INPUTS)
    | set(REQUIRED_HEURISTIC_INPUTS)
    | {"panel_date_reaudit_working.csv", "vendor_reply_adjudication_latest.csv"}
)


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def utc_now_text() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def metadata_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        try:
            return path.absolute().relative_to(REPO_ROOT.absolute()).as_posix()
        except ValueError:
            return path.as_posix()


def add_stable_generated_at(output_path: Path, payload: dict[str, object]) -> dict[str, object]:
    generated_at = utc_now_text()
    if output_path.exists():
        try:
            existing = json.loads(output_path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
        existing_body = {
            key: value for key, value in existing.items() if key != "generated_at_utc"
        }
        existing_generated_at = normalize_text(existing.get("generated_at_utc"))
        if existing_body == payload and existing_generated_at:
            generated_at = existing_generated_at
    return {"generated_at_utc": generated_at, **payload}


def truthy_mask(series: pd.Series) -> pd.Series:
    lowered = series.astype(str).str.strip().str.lower()
    return lowered.isin({"1", "true", "t", "yes"})


def row_key(site: object, panel_id: object) -> tuple[str, str]:
    return normalize_text(site), normalize_text(panel_id)


def validate_unique_keys(df: pd.DataFrame, name: str) -> None:
    if df[["site", "panel_id"]].duplicated().any():
        dup = df.loc[df[["site", "panel_id"]].duplicated(keep=False), ["site", "panel_id"]]
        raise SystemExit(f"{name} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}")


def display_heuristic_name(raw_label: object) -> str:
    return shared_display_heuristic_name(raw_label)


def choose_display_precursor_date(
    event_type_ko: object,
    interpreted_onset_date: object,
    first_warning_date: object,
) -> str:
    if normalize_text(event_type_ko) != "전조형 고장":
        return ""
    onset_date = normalize_text(interpreted_onset_date)
    if onset_date:
        return onset_date
    return normalize_text(first_warning_date)


def choose_display_fault_date(
    fault_date: object,
    strict_trigger_date: object,
    first_final_fault_date: object,
) -> str:
    for candidate in [fault_date, strict_trigger_date, first_final_fault_date]:
        text = normalize_text(candidate)
        if text:
            return text
    return ""


def display_preview_precursor_date(value: object) -> str:
    text = normalize_text(value)
    return text if text else "전조없음"


def display_signal_grade(row: pd.Series) -> str:
    if normalize_text(row.get("패널고장여부_ko")) == "고장":
        return "확정"
    return ""


def display_existing_algorithm_source(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return "미검출"
    if text.lower() == "none":
        return "미검출"
    if text == "기존 알고리즘 미검출":
        return "미검출"
    return text


def event_summary_from_labels(event_type: object, terminal_pattern: object) -> str:
    event = normalize_text(event_type)
    terminal = normalize_text(terminal_pattern)
    mapping = {
        ("전조형 고장", "급격 종료"): "전조 후 급격 종료",
        ("전조형 고장", "진행성 악화"): "전조 후 진행 악화",
        ("급작 고장", "급작 발생"): "급작 발생",
    }
    return mapping.get((event, terminal), "")


def build_fault6_artifact() -> pd.DataFrame:
    if not VERDICT_PATH.exists():
        raise SystemExit(f"missing verdict output: {VERDICT_PATH}")
    if not HEURISTIC_PATH.exists():
        raise SystemExit(f"missing heuristic output: {HEURISTIC_PATH}")

    verdict_df = pd.read_csv(VERDICT_PATH, encoding="utf-8-sig", low_memory=False)
    heuristic_df = pd.read_csv(HEURISTIC_PATH, encoding="utf-8-sig", low_memory=False)
    ensure_columns(verdict_df, VERDICT_FAULT_REQUIRED_COLS, VERDICT_PATH.name)
    ensure_columns(heuristic_df, HEURISTIC_REQUIRED_COLS, HEURISTIC_PATH.name)
    validate_unique_keys(verdict_df, VERDICT_PATH.name)
    validate_unique_keys(heuristic_df, HEURISTIC_PATH.name)

    fault_df = verdict_df.loc[
        verdict_df["패널고장여부_ko"].map(normalize_text).eq("고장"),
        VERDICT_FAULT_REQUIRED_COLS,
    ].copy()
    if len(fault_df) != 6:
        raise SystemExit(f"expected 6 fault rows in verdict output, found {len(fault_df)}")

    heuristic_lookup = {
        row_key(row["site"], row["panel_id"]): row
        for row in heuristic_df.to_dict(orient="records")
    }
    missing_fault_keys = sorted(
        row_key(row["site"], row["panel_id"])
        for row in fault_df.to_dict(orient="records")
        if row_key(row["site"], row["panel_id"]) not in heuristic_lookup
    )
    if missing_fault_keys:
        raise SystemExit(f"{HEURISTIC_PATH.name} missing fault rows: {missing_fault_keys[:5]}")

    rows: list[dict[str, str]] = []
    for row in fault_df.to_dict(orient="records"):
        heuristic_row = heuristic_lookup[row_key(row["site"], row["panel_id"])]
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
        .reindex(columns=FAULT6_REQUIRED_COLS)
        .sort_values(["site", "panel_id"], ascending=[True, True])
        .reset_index(drop=True)
    )


def build_baseline_manifest() -> dict[str, object]:
    data_root = REPO_ROOT / "data"
    manifest: dict[str, object] = {"sites": {}}
    for site in BASELINE_SITES:
        raw_dir = data_root / site / "raw"
        if not raw_dir.exists():
            raise SystemExit(f"missing baseline raw dir: {raw_dir}")
        files = sorted(path for path in raw_dir.glob("*.csv") if path.is_file())
        if not files:
            raise SystemExit(f"no baseline csv files under: {raw_dir}")
        dated = []
        for path in files:
            match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
            if match:
                dated.append(match.group(1))
        manifest["sites"][site] = {
            "file_count": len(files),
            "total_bytes": int(sum(path.stat().st_size for path in files)),
            "first_filenames": [path.name for path in files[:5]],
            "last_filenames": [path.name for path in files[-5:]],
            "min_date": min(dated) if dated else "",
            "max_date": max(dated) if dated else "",
        }
    manifest["note_ko"] = (
        "이 manifest는 고정 fault6 결과표가 만들어진 현재 baseline raw corpus의 경량 fingerprint다. "
        "target 환경에서 파일 수/총용량/날짜 범위를 비교해 exact replay 여부를 점검한다."
    )
    return manifest


def load_panel_day_core(site: str) -> pd.DataFrame:
    path = REPO_ROOT / "data" / site / "out" / "panel_day_core.csv"
    if not path.exists():
        raise SystemExit(f"missing panel_day_core for preview build: {path}")
    df = pd.read_csv(path, low_memory=False)
    required = [
        "panel_id",
        "date",
        "final_fault",
        "critical_fault",
        "fault_like_day",
        "critical_source",
    ]
    ensure_columns(df, required, path.name)
    df["panel_id"] = df["panel_id"].astype(str)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def build_fault6_preview_artifact(fault_df: pd.DataFrame) -> pd.DataFrame:
    audit_path = REPO_ROOT / "_share" / "panel_day_engine_fault_panel_event_audit_v1.csv"
    verdict_df = pd.read_csv(VERDICT_PATH, encoding="utf-8-sig", low_memory=False)
    audit_df = pd.read_csv(audit_path, encoding="utf-8-sig", low_memory=False)
    ensure_columns(
        verdict_df,
        ["site", "panel_id", "사건유형_ko", "운영최초전조발견일", "사건해석상전조시작일", "세부fault_기준일"],
        VERDICT_PATH.name,
    )
    ensure_columns(
        audit_df,
        [
            "site",
            "panel_id",
            "earliest_warning_date",
            "retrospective_onset_date",
            "strict_trigger_date",
            "first_final_fault_date",
        ],
        audit_path.name,
    )
    verdict_lookup = {
        row_key(row["site"], row["panel_id"]): row
        for row in verdict_df.to_dict(orient="records")
    }
    audit_lookup = {
        row_key(row["site"], row["panel_id"]): row
        for row in audit_df.to_dict(orient="records")
    }
    preview_rows: list[dict[str, str]] = []
    for _, row in fault_df.iterrows():
        site = normalize_text(row["site"])
        panel_id = normalize_text(row["panel_id"])
        verdict_row = verdict_lookup.get(row_key(site, panel_id), {})
        audit_row = audit_lookup.get(row_key(site, panel_id), {})
        preview_rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "전조날짜": display_preview_precursor_date(
                    choose_display_precursor_date(
                        event_type_ko=verdict_row.get("사건유형_ko", row.get("사건유형_ko")),
                        interpreted_onset_date=verdict_row.get("사건해석상전조시작일"),
                        first_warning_date=audit_row.get("earliest_warning_date"),
                    )
                ),
                "고장 기준일": choose_display_fault_date(
                    fault_date=verdict_row.get("세부fault_기준일"),
                    strict_trigger_date=audit_row.get("strict_trigger_date"),
                    first_final_fault_date=audit_row.get("first_final_fault_date"),
                ),
                "운영 판정": display_signal_grade(row),
                "급락 종결 관측": "있음"
                if normalize_text(row["최종고장양상_ko"]) in {"급격 종료", "급작 발생"}
                else "없음",
                "점진 저하 누적": "있음"
                if normalize_text(verdict_row.get("사건유형_ko", row.get("사건유형_ko"))) == "전조형 고장"
                else "없음",
                "사건 종결 요약": event_summary_from_labels(
                    verdict_row.get("사건유형_ko", row.get("사건유형_ko")),
                    row.get("최종고장양상_ko"),
                ),
                "상위 해석 후보": normalize_text(row["1순위_의심원인_ko"]),
                "기존 알고리즘 source": display_existing_algorithm_source(
                    MAIL_BUCKET_ALGORITHM_MAP.get((site, panel_id), "")
                ),
            }
        )
    preview_df = pd.DataFrame(preview_rows).reindex(columns=PREVIEW_OUTPUT_COLS)
    if len(preview_df) != 6:
        raise SystemExit(f"expected 6 preview rows, found {len(preview_df)}")
    return preview_df


def build_ktc_fault2_preview_artifact(preview_df: pd.DataFrame) -> pd.DataFrame:
    ktc_df = (
        preview_df.loc[preview_df["site"].astype(str).eq("ktc_ess")]
        .sort_values(["site", "panel_id"], ascending=[True, True])
        .reset_index(drop=True)
    )
    if len(ktc_df) != 2:
        raise SystemExit(f"expected 2 ktc fault rows in preview artifact, found {len(ktc_df)}")
    return ktc_df.reindex(columns=PREVIEW_OUTPUT_COLS)


def build_fault6_provenance_payload(fault_df: pd.DataFrame) -> dict[str, object]:
    payload: dict[str, object] = {
        "source_chain_ko": "frozen verdict plus frozen heuristic with integrated display-name mapping",
        "verdict_source_path": metadata_path(VERDICT_PATH),
        "heuristic_source_path": metadata_path(HEURISTIC_PATH),
        "legacy_integrated_source_path": metadata_path(LEGACY_INTEGRATED_TABLE_PATH),
        "fault_row_count": int(len(fault_df)),
        "display_name_map": DISPLAY_HEURISTIC_NAME_MAP,
        "legacy_integrated_exact_match": False,
        "legacy_integrated_diff_columns": [],
        "note_ko": (
            "이 provenance는 runtime pack의 fault6 고정 결과표가 더 이상 integrated snapshot을 직접 절단하지 않고, "
            "frozen verdict와 frozen heuristic를 현재 integrated builder와 동일한 표시명 매핑으로 다시 조합해 만든 것임을 설명한다."
        ),
    }

    if not LEGACY_INTEGRATED_TABLE_PATH.exists():
        payload["legacy_integrated_compare_status_ko"] = "legacy integrated snapshot missing"
        return add_stable_generated_at(FAULT6_PROVENANCE_PATH, payload)

    legacy_df = pd.read_csv(LEGACY_INTEGRATED_TABLE_PATH, encoding="utf-8-sig", low_memory=False)
    ensure_columns(legacy_df, FAULT6_REQUIRED_COLS, LEGACY_INTEGRATED_TABLE_PATH.name)
    legacy_fault_df = (
        legacy_df.loc[legacy_df["패널고장여부_ko"].map(normalize_text).eq("고장"), FAULT6_REQUIRED_COLS]
        .copy()
        .sort_values(["site", "panel_id"], ascending=[True, True])
        .reset_index(drop=True)
    )
    current_fault_df = fault_df.sort_values(["site", "panel_id"], ascending=[True, True]).reset_index(drop=True)
    payload["legacy_fault_row_count"] = int(len(legacy_fault_df))

    differing_columns: list[str] = []
    for column in FAULT6_REQUIRED_COLS:
        left = current_fault_df[column].fillna("").astype(str)
        right = legacy_fault_df[column].fillna("").astype(str)
        if not left.equals(right):
            differing_columns.append(column)

    payload["legacy_integrated_exact_match"] = not differing_columns
    payload["legacy_integrated_diff_columns"] = differing_columns
    payload["legacy_integrated_compare_status_ko"] = (
        "exact match" if not differing_columns else "difference detected"
    )
    return add_stable_generated_at(FAULT6_PROVENANCE_PATH, payload)


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


def build_core_baseline_digest() -> dict[str, object]:
    payload: dict[str, object] = {
        "sites": {},
        "note_ko": (
            "이 digest는 baseline raw corpus에서 이미 산출된 panel_day_core.csv의 정규화 hash/reference다. "
            "runtime pack이 동일 baseline 입력으로 재실행될 때 engine core output이 같은지 shadow compare할 때 사용한다."
        ),
    }
    for site in BASELINE_SITES:
        path = REPO_ROOT / "data" / site / "out" / "panel_day_core.csv"
        if not path.exists():
            raise SystemExit(f"missing baseline core output: {path}")
        df = pd.read_csv(path, low_memory=False)
        payload["sites"][site] = {
            **build_core_digest_payload(df, path.name),
            "source_path": metadata_path(path),
        }
    return add_stable_generated_at(CORE_BASELINE_DIGEST_PATH, payload)


def build_dependency_audit_payload() -> dict[str, object]:
    payload: dict[str, object] = {
        "runtime_live_full_chain_ready_flag": False,
        "current_pack_mode_ko": "engine_live_plus_fixed_fault_artifacts",
        "hard_cycle": {
            "verified_flag": True,
            "nodes": [
                "build_panel_day_engine_panel_multiaxis_verdict_v1.py",
                "build_panel_day_engine_fault_panel_event_audit_v1.py",
            ],
            "verdict_requires": [
                "panel_day_engine_fault_panel_event_audit_v1.csv",
                "사건유형_재판정_ko",
                "최종고장양상_재판정_ko",
                "재판정_근거_ko",
            ],
            "fault_event_audit_requires": [
                "panel_day_engine_panel_multiaxis_verdict_v1.csv",
                "패널고장여부_ko",
                "사건유형_ko",
                "최종고장양상_ko",
                "전조흔적_flag",
                "순수급작_flag",
                "전조평가셋편입_flag",
                "급작평가셋편입_flag",
            ],
            "impact_ko": (
                "현재 구조 그대로는 verdict와 fault_event_audit가 서로를 선행 입력으로 요구하므로, "
                "integrated snapshot 없이 단방향 live runtime chain을 바로 만들 수 없다."
            ),
        },
        "required_runtime_layers": [
            "pv_ae/panel_day_engine.py",
            "build_panel_day_engine_panel_multiaxis_verdict_v1.py",
            "build_panel_day_engine_gpvs_evidence_pack_v1.py",
            "build_panel_day_engine_cause_candidate_heuristics_v1.py",
        ],
        "required_verdict_share_inputs": REQUIRED_VERDICT_SHARE_INPUTS,
        "required_gpvs_evidence_inputs": REQUIRED_GPVS_INPUTS,
        "required_heuristic_inputs": REQUIRED_HEURISTIC_INPUTS,
        "required_fault_event_audit_inputs": REQUIRED_FAULT_EVENT_AUDIT_INPUTS,
        "recommended_next_step_ko": (
            "runtime chain에서는 fault_event_audit를 validation-only로 분리하고, "
            "별도 shadow-compare 경로에서 기존 frozen chain 결과와 diff를 먼저 점검하는 것이 안전하다."
        ),
        "note_ko": (
            "이 audit는 현재 repo 기준의 full-chain live runtime blocker를 문서화한 것이다. "
            "pack 자체의 공식 결과표 의미는 바꾸지 않고, 왜 아직 fixed fault artifact를 함께 들고 가는지 설명한다."
        ),
    }
    return add_stable_generated_at(DEPENDENCY_AUDIT_JSON_PATH, payload)


def build_dependency_audit_markdown(payload: dict[str, object]) -> str:
    cycle = payload["hard_cycle"]
    verdict_inputs = "\n".join(f"- `{name}`" for name in payload["required_verdict_share_inputs"])
    gpvs_inputs = "\n".join(f"- `{name}`" for name in payload["required_gpvs_evidence_inputs"])
    heuristic_inputs = "\n".join(f"- `{name}`" for name in payload["required_heuristic_inputs"])
    audit_inputs = "\n".join(f"- `{name}`" for name in payload["required_fault_event_audit_inputs"])
    runtime_layers = "\n".join(f"- `{name}`" for name in payload["required_runtime_layers"])
    return (
        "# runtime_chain_dependency_audit_v1\n\n"
        "## 목적\n"
        "현재 conalog full runtime pack이 어디까지 live이고, full-chain runtime으로 가려면 어떤 blocker가 남는지 고정 설명으로 남긴다.\n\n"
        "## 현재 상태\n"
        f"- `runtime_live_full_chain_ready_flag`: `{payload['runtime_live_full_chain_ready_flag']}`\n"
        f"- `current_pack_mode_ko`: `{payload['current_pack_mode_ko']}`\n\n"
        "## Hard Cycle\n"
        f"- verdict node: `{cycle['nodes'][0]}`\n"
        f"- fault-event-audit node: `{cycle['nodes'][1]}`\n"
        f"- impact: {cycle['impact_ko']}\n\n"
        "### verdict가 직접 요구하는 fault_event_audit 축\n"
        + "\n".join(f"- `{name}`" for name in cycle["verdict_requires"])
        + "\n\n### fault_event_audit가 다시 요구하는 verdict 축\n"
        + "\n".join(f"- `{name}`" for name in cycle["fault_event_audit_requires"])
        + "\n\n## Runtime에 필요한 레이어\n"
        + runtime_layers
        + "\n\n## verdict 필수 share 입력\n"
        + verdict_inputs
        + "\n\n## GPVS evidence 필수 입력\n"
        + gpvs_inputs
        + "\n\n## heuristic 필수 입력\n"
        + heuristic_inputs
        + "\n\n## fault_event_audit 필수 입력\n"
        + audit_inputs
        + "\n\n## 권장 다음 단계\n"
        f"- {payload['recommended_next_step_ko']}\n"
    )


def write_text_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in {".bat", ".cmd"}:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
        path.write_text(normalized, encoding="utf-8-sig")
        return
    path.write_text(text, encoding="utf-8")


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def extract_zip(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(destination)


def configure_embedded_python(python_root: Path) -> Path:
    pth_files = sorted(python_root.glob("python*._pth"))
    if not pth_files:
        raise SystemExit(f"missing embedded python _pth file under: {python_root}")
    pth_path = pth_files[0]
    site_packages_dir = python_root / "Lib" / "site-packages"
    site_packages_dir.mkdir(parents=True, exist_ok=True)
    python_zip_name = f"{pth_path.stem}.zip"
    pth_contents = "\n".join(
        [
            python_zip_name,
            ".",
            "Lib",
            "Lib\\site-packages",
            "import site",
        ]
    )
    pth_path.write_text(pth_contents + "\n", encoding="utf-8")
    return site_packages_dir


def extract_wheels_into_site_packages(wheelhouse: Path, site_packages_dir: Path) -> None:
    site_packages_dir.mkdir(parents=True, exist_ok=True)
    for wheel_path in sorted(wheelhouse.glob("*.whl")):
        with zipfile.ZipFile(wheel_path) as wheel_archive:
            wheel_archive.extractall(site_packages_dir)


def bundled_runtime_ready() -> bool:
    manifest_exists = WINDOWS_RUNTIME_MANIFEST_PATH.exists()
    python_exists = (WINDOWS_RUNTIME_PYTHON_ROOT / "python.exe").exists()
    import_helper_exists = IMPORT_ANY_CSV_DST.exists()
    if not (manifest_exists and python_exists and import_helper_exists):
        return False
    try:
        manifest = json.loads(WINDOWS_RUNTIME_MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception:
        return False
    primary_packages = set(manifest.get("primary_packages", []))
    return set(WINDOWS_RUNTIME_PRIMARY_PACKAGES).issubset(primary_packages)


def materialize_windows_portable_runtime() -> dict[str, object]:
    if bundled_runtime_ready():
        return json.loads(WINDOWS_RUNTIME_MANIFEST_PATH.read_text(encoding="utf-8"))

    WINDOWS_RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    WINDOWS_RUNTIME_CACHE.mkdir(parents=True, exist_ok=True)
    embed_zip_path = WINDOWS_RUNTIME_CACHE / f"python-{WINDOWS_EMBED_PYTHON_VERSION}-embed-amd64.zip"

    if WINDOWS_RUNTIME_PYTHON_ROOT.exists():
        shutil.rmtree(WINDOWS_RUNTIME_PYTHON_ROOT)
    if WINDOWS_RUNTIME_WHEELHOUSE.exists():
        shutil.rmtree(WINDOWS_RUNTIME_WHEELHOUSE)

    if not embed_zip_path.exists():
        download_file(WINDOWS_EMBED_ZIP_URL, embed_zip_path)

    extract_zip(embed_zip_path, WINDOWS_RUNTIME_PYTHON_ROOT)
    site_packages_dir = configure_embedded_python(WINDOWS_RUNTIME_PYTHON_ROOT)

    WINDOWS_RUNTIME_WHEELHOUSE.mkdir(parents=True, exist_ok=True)
    download_cmd = [
        sys.executable,
        "-m",
        "pip",
        "download",
        "--only-binary=:all:",
        "--dest",
        str(WINDOWS_RUNTIME_WHEELHOUSE),
        "--platform",
        "win_amd64",
        "--python-version",
        "311",
        "--implementation",
        "cp",
        "--abi",
        "cp311",
        *WINDOWS_RUNTIME_PRIMARY_PACKAGES,
    ]
    subprocess.run(download_cmd, check=True)
    extract_wheels_into_site_packages(WINDOWS_RUNTIME_WHEELHOUSE, site_packages_dir)

    manifest = {
        "python_runtime_kind": "windows_embeddable_python",
        "python_version": WINDOWS_EMBED_PYTHON_VERSION,
        "python_exe_path": metadata_path(WINDOWS_RUNTIME_PYTHON_ROOT / "python.exe"),
        "python_embed_zip_url": WINDOWS_EMBED_ZIP_URL,
        "wheelhouse_path": metadata_path(WINDOWS_RUNTIME_WHEELHOUSE),
        "site_packages_path": metadata_path(site_packages_dir),
        "primary_packages": WINDOWS_RUNTIME_PRIMARY_PACKAGES,
        "wheel_count": len(list(WINDOWS_RUNTIME_WHEELHOUSE.glob("*.whl"))),
        "note_ko": (
            "이 runtime은 Windows embeddable Python 3.11.9와 필요한 win_amd64 wheel을 미리 포함해, "
            "현장 PC에 별도 Python/pip 설치 없이 실행할 수 있도록 만든 포터블 런타임이다."
        ),
    }
    manifest = add_stable_generated_at(WINDOWS_RUNTIME_MANIFEST_PATH, manifest)
    WINDOWS_RUNTIME_MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    WINDOWS_RUNTIME_README_PATH.write_text(
        (
            "# Windows Portable Runtime\n\n"
            "이 폴더는 `conalog_full_runtime_v1` USB pack이 Windows에서 별도 Python 설치 없이 실행되도록 "
            "포함한 portable runtime 자산입니다.\n\n"
            f"- Embedded Python: `{WINDOWS_EMBED_PYTHON_VERSION}`\n"
            f"- Primary packages: `{', '.join(WINDOWS_RUNTIME_PRIMARY_PACKAGES)}`\n"
            "- Wrapper는 `runtime\\windows_x64\\python\\python.exe`를 먼저 찾고, 없을 때만 시스템 Python을 찾습니다.\n"
        ),
        encoding="utf-8",
    )
    return manifest


def materialize_runtime_chain_assets() -> None:
    package_research_parent = PACKAGE_RESEARCH_ROOT.parent
    package_research_parent.mkdir(parents=True, exist_ok=True)
    PACKAGE_RESEARCH_ROOT.mkdir(parents=True, exist_ok=True)
    write_text_file(package_research_parent / "__init__.py", "")
    write_text_file(PACKAGE_RESEARCH_ROOT / "__init__.py", "")

    for source in PACKAGED_RUNTIME_CHAIN_SCRIPTS:
        if not source.exists():
            raise SystemExit(f"missing runtime chain script source: {source}")
        shutil.copy2(source, PACKAGE_RESEARCH_ROOT / source.name)

    if not IMPORT_ANY_CSV_SRC.exists():
        raise SystemExit(f"missing import helper source: {IMPORT_ANY_CSV_SRC}")
    shutil.copy2(IMPORT_ANY_CSV_SRC, IMPORT_ANY_CSV_DST)

    PACKAGE_SHARE_ROOT.mkdir(parents=True, exist_ok=True)
    for filename in PACKAGED_RUNTIME_CHAIN_SHARE_INPUTS:
        source = REPO_ROOT / "_share" / filename
        target = PACKAGE_SHARE_ROOT / filename
        if source.exists():
            shutil.copy2(source, target)
            continue
        if filename in OPTIONAL_PACKAGED_SHARE_INPUTS:
            if target.exists():
                target.unlink()
            continue
        raise SystemExit(f"missing runtime chain share input: {source}")


def materialize_ops_scripts() -> None:
    write_text_file(
        RUN_DEMO_BAT_PATH,
        """@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PACKAGE_ROOT=%%~fI"

if exist "%PACKAGE_ROOT%\\artifacts\\fault6_label_and_algorithm_preview_v1.csv" start "" "%PACKAGE_ROOT%\\artifacts\\fault6_label_and_algorithm_preview_v1.csv"
if not exist "%PACKAGE_ROOT%\\artifacts\\fault6_label_and_algorithm_preview_v1.csv" (
  echo fault6_label_and_algorithm_preview_v1.csv를 찾지 못했습니다.
  if "%PVDIAG_NO_PAUSE%"=="" pause
  exit /b 1
)

exit /b 0
""",
    )
    write_text_file(
        RUN_DEMO_KTC_FAULT2_BAT_PATH,
        """@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PACKAGE_ROOT=%%~fI"

if exist "%PACKAGE_ROOT%\\artifacts\\ktc_fault2_label_and_algorithm_preview_v1.csv" start "" "%PACKAGE_ROOT%\\artifacts\\ktc_fault2_label_and_algorithm_preview_v1.csv"
if not exist "%PACKAGE_ROOT%\\artifacts\\ktc_fault2_label_and_algorithm_preview_v1.csv" (
  echo ktc_fault2_label_and_algorithm_preview_v1.csv를 찾지 못했습니다.
  if "%PVDIAG_NO_PAUSE%"=="" pause
  exit /b 1
)

exit /b 0
""",
    )
    write_text_file(
        RUN_GUIDED_REAL_BAT_PATH,
        """@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PACKAGE_ROOT=%%~fI"
set "APP_PATH=%PACKAGE_ROOT%\\app\\run_full_algorithm_pack.py"
set "IMPORT_APP=%PACKAGE_ROOT%\\app\\import_any_csv_root.py"
call "%PACKAGE_ROOT%\\bin\\resolve_python.bat"
if errorlevel 1 goto FAIL

where powershell >nul 2>nul
if errorlevel 1 (
  echo Windows PowerShell을 찾을 수 없습니다.
  goto FAIL
)

set "DATA_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='CSV 파일이 들어 있는 상위 폴더를 선택하십시오'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "DATA_ROOT=%%I"

if "%DATA_ROOT%"=="" (
  echo 입력 폴더 경로를 다시 확인하십시오.
  goto CANCEL
)

set "RUN_TS="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; Get-Date -Format yyyyMMdd_HHmmss"`) do set "RUN_TS=%%I"
if "%RUN_TS%"=="" set "RUN_TS=manual"

set "OUTPUT_ROOT=%PACKAGE_ROOT%\\showcase_runs\\run_%RUN_TS%"
echo [005%%] 입력 폴더 선택 완료
echo [010%%] 결과 폴더 자동 생성: %OUTPUT_ROOT%

set "EFFECTIVE_DATA_ROOT=%DATA_ROOT%"
set "EFFECTIVE_SITES=conalog,gangui,ktc_ess"

if exist "%DATA_ROOT%\\conalog\\raw" if exist "%DATA_ROOT%\\gangui\\raw" if exist "%DATA_ROOT%\\ktc_ess\\raw" goto RUN_ENGINE
if exist "%DATA_ROOT%\\data\\conalog\\raw" if exist "%DATA_ROOT%\\data\\gangui\\raw" if exist "%DATA_ROOT%\\data\\ktc_ess\\raw" (
  set "EFFECTIVE_DATA_ROOT=%DATA_ROOT%\\data"
  goto RUN_ENGINE
)

echo [020%%] CSV 구조를 점검하고 자동 staging을 준비합니다.
set "IMPORT_STAGE_ROOT=%OUTPUT_ROOT%\\imported_data"
set "IMPORT_ENV=%IMPORT_STAGE_ROOT%\\import_env.bat"
set "IMPORT_MANIFEST=%IMPORT_STAGE_ROOT%\\import_any_csv_manifest_v1.json"

%PYTHON_CMD% "%IMPORT_APP%" --input-root "%DATA_ROOT%" --output-root "%IMPORT_STAGE_ROOT%" --clear-output --manifest-path "%IMPORT_MANIFEST%" --env-bat-path "%IMPORT_ENV%"
if errorlevel 1 goto FAIL

call "%IMPORT_ENV%"
if errorlevel 1 goto FAIL
set "EFFECTIVE_DATA_ROOT=%IMPORTED_DATA_ROOT%"
set "EFFECTIVE_SITES=%IMPORTED_SITES%"

:RUN_ENGINE
echo [040%%] 학습/추론 및 결과표 생성을 시작합니다.
%PYTHON_CMD% "%APP_PATH%" --data-root "%EFFECTIVE_DATA_ROOT%" --output-root "%OUTPUT_ROOT%" --sites "%EFFECTIVE_SITES%"
if errorlevel 1 goto FAIL

echo [100%%] 실행 완료. 결과 리포트를 엽니다.
if exist "%OUTPUT_ROOT%\\result\\fault_panel_result_current_preview_v1.csv" (
  start "" "%OUTPUT_ROOT%\\result\\fault_panel_result_current_preview_v1.csv"
) else if exist "%OUTPUT_ROOT%\\result\\fault_panel_result_current_report_v1.md" (
  start "" "%OUTPUT_ROOT%\\result\\fault_panel_result_current_report_v1.md"
) else if exist "%OUTPUT_ROOT%\\result\\fault_panel_result_master_report_v1.md" (
  start "" "%OUTPUT_ROOT%\\result\\fault_panel_result_master_report_v1.md"
) else if exist "%OUTPUT_ROOT%\\result" (
  start "" "%OUTPUT_ROOT%\\result"
)
echo 결과 폴더: %OUTPUT_ROOT%
goto SUCCESS

:CANCEL
echo 작업이 취소되었습니다.
if "%PVDIAG_NO_PAUSE%"=="" pause
exit /b 0

:FAIL
set "EXIT_CODE=%ERRORLEVEL%"
if "%EXIT_CODE%"=="" set "EXIT_CODE=1"
echo 실행이 중단되었습니다. 위 메시지를 확인하십시오.
if "%PVDIAG_NO_PAUSE%"=="" pause
exit /b %EXIT_CODE%

:SUCCESS
if "%PVDIAG_NO_PAUSE%"=="" pause
exit /b 0
""",
    )
    write_text_file(
        RESOLVE_PYTHON_BAT_PATH,
        """@echo off
chcp 65001 >nul
if "%PACKAGE_ROOT%"=="" (
  echo PACKAGE_ROOT 환경변수가 비어 있습니다.
  exit /b 1
)

set "PYTHON_CMD=%PACKAGE_ROOT%\\runtime\\windows_x64\\python\\python.exe"
if exist "%PYTHON_CMD%" (
  set "PYTHON_RUNTIME_KIND=embedded"
  exit /b 0
)

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=py -3"
  set "PYTHON_RUNTIME_KIND=system_py_launcher"
  exit /b 0
)

where python >nul 2>nul
if errorlevel 1 (
  echo Python 3를 찾지 못했습니다. package\\runtime\\windows_x64\\python\\python.exe 또는 시스템 Python 3를 준비하십시오.
  exit /b 1
)

set "PYTHON_CMD=python"
set "PYTHON_RUNTIME_KIND=system_python"
exit /b 0
""",
    )
    write_text_file(
        STAGING_PS1_PATH,
        """param(
    [Parameter(Mandatory=$true)][string]$ArchiveRoot,
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [int]$WindowDays = 120,
    [string]$Sites = "conalog,gangui,ktc_ess"
)

$siteList = $Sites.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
$cutoff = (Get-Date).AddDays(-1 * $WindowDays)

foreach ($site in $siteList) {
    $candidates = @(
        (Join-Path $ArchiveRoot "$site\\raw"),
        (Join-Path $ArchiveRoot "$site\\raw_all"),
        (Join-Path $ArchiveRoot "data\\$site\\raw"),
        (Join-Path $ArchiveRoot "data\\$site\\raw_all")
    )
    $sourceDir = $null
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $sourceDir = $candidate
            break
        }
    }
    if (-not $sourceDir) {
        throw "source raw dir not found for site=$site under $ArchiveRoot"
    }

    $targetDir = Join-Path $RuntimeRoot "$site\\raw"
    if (Test-Path $targetDir) {
        Remove-Item $targetDir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

    Get-ChildItem $sourceDir -Filter *.csv | ForEach-Object {
        if ($_.Name -match '(\\d{4}-\\d{2}-\\d{2})') {
            $day = [datetime]::ParseExact($matches[1], 'yyyy-MM-dd', $null)
            if ($day -ge $cutoff) {
                Copy-Item $_.FullName -Destination $targetDir
            }
        }
    }
}

Write-Host "[OK] staged recent raw files into $RuntimeRoot"
""",
    )
    write_text_file(
        SNAPSHOT_COPY_PS1_PATH,
        """param(
    [Parameter(Mandatory=$true)][string]$IngestRoot,
    [Parameter(Mandatory=$true)][string]$SnapshotRoot,
    [int]$StableMinutes = 10,
    [string]$Sites = "conalog,gangui,ktc_ess",
    [string]$Pattern = "*.csv"
)

$siteList = $Sites.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
$cutoff = (Get-Date).AddMinutes(-1 * $StableMinutes)
$copiedCount = 0
$skippedRecentCount = 0

foreach ($site in $siteList) {
    $candidates = @(
        (Join-Path $IngestRoot "$site\\raw"),
        (Join-Path $IngestRoot "data\\$site\\raw")
    )
    $sourceDir = $null
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $sourceDir = $candidate
            break
        }
    }
    if (-not $sourceDir) {
        throw "source raw dir not found for site=$site under $IngestRoot"
    }

    $targetDir = Join-Path $SnapshotRoot "$site\\raw"
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

    Get-ChildItem $sourceDir -Filter $Pattern | Where-Object { -not $_.PSIsContainer } | ForEach-Object {
        $sourceFile = $_.FullName
        $targetFile = Join-Path $targetDir $_.Name
        $tempFile = "$targetFile.__copying__"

        if ($_.LastWriteTime -gt $cutoff) {
            $script:skippedRecentCount += 1
            return
        }

        Copy-Item $sourceFile -Destination $tempFile -Force
        Move-Item $tempFile $targetFile -Force
        $script:copiedCount += 1
    }
}

Write-Host "[OK] snapshot copy completed"
Write-Host "[OK] copied_count=$copiedCount"
Write-Host "[OK] skipped_recent_count=$skippedRecentCount"
Write-Host "[OK] snapshot_root=$SnapshotRoot"
""",
    )
    write_text_file(
        DAILY_RUN_BAT_PATH,
        """@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PACKAGE_ROOT=%%~fI"
set "STAGING_PS1=%PACKAGE_ROOT%\\bin\\stage_recent_120d.ps1"
set "APP_PATH=%PACKAGE_ROOT%\\app\\run_full_algorithm_pack.py"
call "%PACKAGE_ROOT%\\bin\\resolve_python.bat"
if errorlevel 1 exit /b %errorlevel%

set /p ARCHIVE_ROOT=archive_data 루트 경로를 입력하십시오 ^(예: D:\\pvdiag\\archive_data^): 
if "%ARCHIVE_ROOT%"=="" (
    echo archive_data 루트 경로를 다시 확인하십시오.
  exit /b 0
)
if not exist "%ARCHIVE_ROOT%" (
  echo archive_data 루트 경로를 다시 확인하십시오.
  exit /b 0
)

set /p RUNTIME_ROOT=runtime_data 경로를 입력하십시오 [기본값: %PACKAGE_ROOT%\\..\\runtime_data]: 
if "%RUNTIME_ROOT%"=="" set "RUNTIME_ROOT=%PACKAGE_ROOT%\\..\\runtime_data"

set /p OUTPUT_ROOT=출력 폴더 경로를 입력하십시오 [기본값: %PACKAGE_ROOT%\\..\\runtime_output\\daily_run]: 
if "%OUTPUT_ROOT%"=="" set "OUTPUT_ROOT=%PACKAGE_ROOT%\\..\\runtime_output\\daily_run"

echo [010%%] 최근 120일 raw staging 경로를 준비했습니다.

powershell -ExecutionPolicy Bypass -File "%STAGING_PS1%" -ArchiveRoot "%ARCHIVE_ROOT%" -RuntimeRoot "%RUNTIME_ROOT%" -WindowDays 120
if errorlevel 1 exit /b %errorlevel%

echo [040%%] 학습/추론 및 결과표 생성을 시작합니다.

%PYTHON_CMD% "%APP_PATH%" --data-root "%RUNTIME_ROOT%" --output-root "%OUTPUT_ROOT%"
if errorlevel 1 exit /b %errorlevel%

echo [100%%] 실행 완료. 결과 리포트를 엽니다.

if exist "%OUTPUT_ROOT%\\result\\fault_panel_result_current_preview_v1.csv" (
  start "" "%OUTPUT_ROOT%\\result\\fault_panel_result_current_preview_v1.csv"
) else if exist "%OUTPUT_ROOT%\\result\\fault_panel_result_current_report_v1.md" (
  start "" "%OUTPUT_ROOT%\\result\\fault_panel_result_current_report_v1.md"
) else if exist "%OUTPUT_ROOT%\\result\\fault_panel_result_master_report_v1.md" (
  start "" "%OUTPUT_ROOT%\\result\\fault_panel_result_master_report_v1.md"
) else if exist "%OUTPUT_ROOT%\\result" (
  start "" "%OUTPUT_ROOT%\\result"
)
exit /b 0
""",
    )
    write_text_file(
        INCREMENTAL_RUN_BAT_PATH,
        """@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PACKAGE_ROOT=%%~fI"
set "APP_PATH=%PACKAGE_ROOT%\\app\\run_full_algorithm_pack.py"
set "IMPORT_APP=%PACKAGE_ROOT%\\app\\import_any_csv_root.py"
set "DEFAULT_SNAPSHOT_ROOT=%PACKAGE_ROOT%\\..\\runtime_snapshot_data"
set "DEFAULT_OUTPUT=%PACKAGE_ROOT%\\..\\runtime_output\\incremental_run"

call "%PACKAGE_ROOT%\\bin\\resolve_python.bat"
if errorlevel 1 goto FAIL

where powershell >nul 2>nul
if errorlevel 1 (
  echo Windows PowerShell을 찾을 수 없습니다.
  goto FAIL
)

set "INGEST_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='MLPE ingest 루트 폴더를 선택하십시오 (conalog\\raw, gangui\\raw, ktc_ess\\raw 포함)'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "INGEST_ROOT=%%I"

if "%INGEST_ROOT%"=="" (
  echo 입력 폴더 경로를 다시 확인하십시오.
  goto CANCEL
)

set "SNAPSHOT_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='snapshot 루트 폴더를 선택하십시오 (취소 시 기본값 사용)'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "SNAPSHOT_ROOT=%%I"
if "%SNAPSHOT_ROOT%"=="" set "SNAPSHOT_ROOT=%DEFAULT_SNAPSHOT_ROOT%"

set "OUTPUT_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='출력 폴더를 선택하십시오 (취소 시 기본값 사용)'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "OUTPUT_ROOT=%%I"
if "%OUTPUT_ROOT%"=="" set "OUTPUT_ROOT=%DEFAULT_OUTPUT%"

set /p STABLE_MINUTES=안정화 대기 분을 입력하십시오 [기본값: 10]: 
if "%STABLE_MINUTES%"=="" set "STABLE_MINUTES=10"

set "IMPORT_ENV=%SNAPSHOT_ROOT%\\import_env.bat"
set "IMPORT_MANIFEST=%SNAPSHOT_ROOT%\\import_any_csv_manifest_v1.json"

echo [010%%] snapshot 경로와 출력 경로를 준비했습니다.
echo [020%%] 안정화된 CSV만 snapshot으로 가져옵니다.

%PYTHON_CMD% "%IMPORT_APP%" --input-root "%INGEST_ROOT%" --output-root "%SNAPSHOT_ROOT%" --clear-output --stable-minutes %STABLE_MINUTES% --manifest-path "%IMPORT_MANIFEST%" --env-bat-path "%IMPORT_ENV%"
if errorlevel 1 goto FAIL

call "%IMPORT_ENV%"
if errorlevel 1 goto FAIL

echo [040%%] 학습/추론 및 결과표 생성을 시작합니다.

%PYTHON_CMD% "%APP_PATH%" --data-root "%IMPORTED_DATA_ROOT%" --output-root "%OUTPUT_ROOT%" --sites "%IMPORTED_SITES%"
if errorlevel 1 goto FAIL

echo [100%%] 실행 완료. 결과 리포트를 엽니다.

if exist "%OUTPUT_ROOT%\\result\\fault_panel_result_current_preview_v1.csv" (
  start "" "%OUTPUT_ROOT%\\result\\fault_panel_result_current_preview_v1.csv"
) else if exist "%OUTPUT_ROOT%\\result\\fault_panel_result_current_report_v1.md" (
  start "" "%OUTPUT_ROOT%\\result\\fault_panel_result_current_report_v1.md"
) else if exist "%OUTPUT_ROOT%\\result\\fault_panel_result_master_report_v1.md" (
  start "" "%OUTPUT_ROOT%\\result\\fault_panel_result_master_report_v1.md"
) else if exist "%OUTPUT_ROOT%\\result" (
  start "" "%OUTPUT_ROOT%\\result"
)
goto SUCCESS

:CANCEL
echo 작업이 취소되었습니다.
if "%PVDIAG_NO_PAUSE%"=="" pause
exit /b 0

:FAIL
set "EXIT_CODE=%ERRORLEVEL%"
if "%EXIT_CODE%"=="" set "EXIT_CODE=1"
echo 실행이 중단되었습니다. 위 메시지를 확인하십시오.
if "%PVDIAG_NO_PAUSE%"=="" pause
exit /b %EXIT_CODE%

:SUCCESS
if "%PVDIAG_NO_PAUSE%"=="" pause
exit /b 0
""",
    )
    write_text_file(
        PACKAGE_ROOT / "bin" / "run_real.bat",
        """@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PACKAGE_ROOT=%%~fI"
set "APP_PATH=%PACKAGE_ROOT%\\app\\run_full_algorithm_pack.py"
set "IMPORT_APP=%PACKAGE_ROOT%\\app\\import_any_csv_root.py"
set "DEFAULT_OUTPUT=%PACKAGE_ROOT%\\real_output"
call "%PACKAGE_ROOT%\\bin\\resolve_python.bat"
if errorlevel 1 goto FAIL

where powershell >nul 2>nul
if errorlevel 1 (
  echo Windows PowerShell을 찾을 수 없습니다.
  goto FAIL
)

set "DATA_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='data 루트 폴더를 선택하십시오 (conalog\\raw, gangui\\raw, ktc_ess\\raw 포함)'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "DATA_ROOT=%%I"

if "%DATA_ROOT%"=="" (
  echo 입력 폴더 경로를 다시 확인하십시오.
  goto CANCEL
)

echo [005%%] 입력 폴더 선택 완료: %DATA_ROOT%

set "OUTPUT_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='출력 폴더를 선택하십시오 (취소 시 기본값 사용)'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "OUTPUT_ROOT=%%I"
if "%OUTPUT_ROOT%"=="" set "OUTPUT_ROOT=%DEFAULT_OUTPUT%"

echo [010%%] 결과 폴더 준비 완료: %OUTPUT_ROOT%

set "EFFECTIVE_DATA_ROOT=%DATA_ROOT%"
set "EFFECTIVE_SITES=conalog,gangui,ktc_ess"

if exist "%DATA_ROOT%\\conalog\\raw" if exist "%DATA_ROOT%\\gangui\\raw" if exist "%DATA_ROOT%\\ktc_ess\\raw" goto RUN_ENGINE
if exist "%DATA_ROOT%\\data\\conalog\\raw" if exist "%DATA_ROOT%\\data\\gangui\\raw" if exist "%DATA_ROOT%\\data\\ktc_ess\\raw" (
  set "EFFECTIVE_DATA_ROOT=%DATA_ROOT%\\data"
  goto RUN_ENGINE
)

set "IMPORT_STAGE_ROOT=%OUTPUT_ROOT%\\imported_data"
set "IMPORT_ENV=%IMPORT_STAGE_ROOT%\\import_env.bat"
set "IMPORT_MANIFEST=%IMPORT_STAGE_ROOT%\\import_any_csv_manifest_v1.json"

echo [020%%] CSV 구조를 점검하고 자동 staging 여부를 결정합니다.

%PYTHON_CMD% "%IMPORT_APP%" --input-root "%DATA_ROOT%" --output-root "%IMPORT_STAGE_ROOT%" --clear-output --manifest-path "%IMPORT_MANIFEST%" --env-bat-path "%IMPORT_ENV%"
if errorlevel 1 goto FAIL

call "%IMPORT_ENV%"
if errorlevel 1 goto FAIL
set "EFFECTIVE_DATA_ROOT=%IMPORTED_DATA_ROOT%"
set "EFFECTIVE_SITES=%IMPORTED_SITES%"

:RUN_ENGINE
echo [040%%] 학습/추론 및 결과표 생성을 시작합니다.

%PYTHON_CMD% "%APP_PATH%" --data-root "%EFFECTIVE_DATA_ROOT%" --output-root "%OUTPUT_ROOT%" --sites "%EFFECTIVE_SITES%"
if errorlevel 1 goto FAIL

echo [100%%] 실행 완료. 결과 리포트를 엽니다.

if exist "%OUTPUT_ROOT%\\result\\fault_panel_result_current_preview_v1.csv" (
  start "" "%OUTPUT_ROOT%\\result\\fault_panel_result_current_preview_v1.csv"
) else if exist "%OUTPUT_ROOT%\\result\\fault_panel_result_current_report_v1.md" (
  start "" "%OUTPUT_ROOT%\\result\\fault_panel_result_current_report_v1.md"
) else if exist "%OUTPUT_ROOT%\\result\\fault_panel_result_master_report_v1.md" (
  start "" "%OUTPUT_ROOT%\\result\\fault_panel_result_master_report_v1.md"
) else if exist "%OUTPUT_ROOT%\\result" (
  start "" "%OUTPUT_ROOT%\\result"
)
goto SUCCESS

:CANCEL
echo 작업이 취소되었습니다.
if "%PVDIAG_NO_PAUSE%"=="" pause
exit /b 0

:FAIL
set "EXIT_CODE=%ERRORLEVEL%"
if "%EXIT_CODE%"=="" set "EXIT_CODE=1"
echo 실행이 중단되었습니다. 위 메시지를 확인하십시오.
if "%PVDIAG_NO_PAUSE%"=="" pause
exit /b %EXIT_CODE%

:SUCCESS
if "%PVDIAG_NO_PAUSE%"=="" pause
exit /b 0
""",
    )
    write_text_file(
        RUN_IMPORTED_REAL_BAT_PATH,
        """@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PACKAGE_ROOT=%%~fI"
set "APP_PATH=%PACKAGE_ROOT%\\app\\run_full_algorithm_pack.py"
set "IMPORT_APP=%PACKAGE_ROOT%\\app\\import_any_csv_root.py"
set "DEFAULT_OUTPUT=%PACKAGE_ROOT%\\real_output_imported"

call "%PACKAGE_ROOT%\\bin\\resolve_python.bat"
if errorlevel 1 goto FAIL

where powershell >nul 2>nul
if errorlevel 1 (
  echo Windows PowerShell을 찾을 수 없습니다.
  goto FAIL
)

set "DATA_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='CSV가 들어 있는 임의 루트 폴더를 선택하십시오'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "DATA_ROOT=%%I"

if "%DATA_ROOT%"=="" (
  echo 입력 폴더 경로를 다시 확인하십시오.
  goto CANCEL
)

echo [005%%] 입력 폴더 선택 완료: %DATA_ROOT%

set "OUTPUT_ROOT="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description='출력 폴더를 선택하십시오 (취소 시 기본값 사용)'; if ($dialog.ShowDialog() -eq 'OK') { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output $dialog.SelectedPath }"`) do set "OUTPUT_ROOT=%%I"
if "%OUTPUT_ROOT%"=="" set "OUTPUT_ROOT=%DEFAULT_OUTPUT%"

set "IMPORT_STAGE_ROOT=%OUTPUT_ROOT%\\imported_data"
set "IMPORT_ENV=%IMPORT_STAGE_ROOT%\\import_env.bat"
set "IMPORT_MANIFEST=%IMPORT_STAGE_ROOT%\\import_any_csv_manifest_v1.json"

echo [010%%] 결과 폴더 준비 완료: %OUTPUT_ROOT%
echo [020%%] CSV 파일을 재귀 수집해 실행 구조로 staging합니다.

%PYTHON_CMD% "%IMPORT_APP%" --input-root "%DATA_ROOT%" --output-root "%IMPORT_STAGE_ROOT%" --clear-output --manifest-path "%IMPORT_MANIFEST%" --env-bat-path "%IMPORT_ENV%"
if errorlevel 1 goto FAIL

call "%IMPORT_ENV%"
if errorlevel 1 goto FAIL

echo [040%%] 학습/추론 및 결과표 생성을 시작합니다.

%PYTHON_CMD% "%APP_PATH%" --data-root "%IMPORTED_DATA_ROOT%" --output-root "%OUTPUT_ROOT%" --sites "%IMPORTED_SITES%"
if errorlevel 1 goto FAIL

echo [100%%] 실행 완료. 결과 리포트를 엽니다.

if exist "%OUTPUT_ROOT%\\result\\fault_panel_result_current_preview_v1.csv" (
  start "" "%OUTPUT_ROOT%\\result\\fault_panel_result_current_preview_v1.csv"
) else if exist "%OUTPUT_ROOT%\\result\\fault_panel_result_current_report_v1.md" (
  start "" "%OUTPUT_ROOT%\\result\\fault_panel_result_current_report_v1.md"
) else if exist "%OUTPUT_ROOT%\\result\\fault_panel_result_master_report_v1.md" (
  start "" "%OUTPUT_ROOT%\\result\\fault_panel_result_master_report_v1.md"
) else if exist "%OUTPUT_ROOT%\\result" (
  start "" "%OUTPUT_ROOT%\\result"
)
goto SUCCESS

:CANCEL
echo 작업이 취소되었습니다.
if "%PVDIAG_NO_PAUSE%"=="" pause
exit /b 0

:FAIL
set "EXIT_CODE=%ERRORLEVEL%"
if "%EXIT_CODE%"=="" set "EXIT_CODE=1"
echo 실행이 중단되었습니다. 위 메시지를 확인하십시오.
if "%PVDIAG_NO_PAUSE%"=="" pause
exit /b %EXIT_CODE%

:SUCCESS
if "%PVDIAG_NO_PAUSE%"=="" pause
exit /b 0
""",
    )


def main() -> None:
    if not ENGINE_SRC.exists():
        raise SystemExit(f"missing engine source: {ENGINE_SRC}")

    for path in [
        RELEASE_ROOT,
        PACKAGE_APP_ROOT,
        PACKAGE_ROOT / "artifacts",
        PACKAGE_ROOT / "bin",
        PACKAGE_ROOT / "pv_ae",
        PACKAGE_RESEARCH_ROOT,
        PACKAGE_SHARE_ROOT,
    ]:
        path.mkdir(parents=True, exist_ok=True)

    shutil.copy2(ENGINE_SRC, ENGINE_DST)

    for pycache_dir in PACKAGE_ROOT.rglob("__pycache__"):
        shutil.rmtree(pycache_dir, ignore_errors=True)

    fault_df = build_fault6_artifact()
    fault_df.to_csv(FAULT6_ARTIFACT_PATH, index=False, encoding="utf-8-sig")
    preview_df = build_fault6_preview_artifact(fault_df)
    preview_df.to_csv(FAULT6_PREVIEW_ARTIFACT_PATH, index=False, encoding="utf-8-sig")
    ktc_fault2_preview_df = build_ktc_fault2_preview_artifact(preview_df)
    ktc_fault2_preview_df.to_csv(KTC_FAULT2_PREVIEW_ARTIFACT_PATH, index=False, encoding="utf-8-sig")
    FAULT6_PROVENANCE_PATH.write_text(
        json.dumps(build_fault6_provenance_payload(fault_df), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    stale_integrated_artifact = PACKAGE_ROOT / "artifacts" / "integrated_result_table_fixed_v1.csv"
    if stale_integrated_artifact.exists():
        stale_integrated_artifact.unlink()

    BASELINE_MANIFEST_PATH.write_text(
        json.dumps(build_baseline_manifest(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    CORE_BASELINE_DIGEST_PATH.write_text(
        json.dumps(build_core_baseline_digest(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    dependency_payload = build_dependency_audit_payload()
    DEPENDENCY_AUDIT_JSON_PATH.write_text(
        json.dumps(dependency_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    DEPENDENCY_AUDIT_MD_PATH.write_text(
        build_dependency_audit_markdown(dependency_payload),
        encoding="utf-8",
    )
    materialize_runtime_chain_assets()
    runtime_manifest = materialize_windows_portable_runtime()
    materialize_ops_scripts()
    write_text_file(
        PACKAGE_ROOT / "requirements.txt",
        "\n".join(WINDOWS_RUNTIME_PRIMARY_PACKAGES) + "\n",
    )

    summary = {
        "release_root": metadata_path(RELEASE_ROOT),
        "package_root": metadata_path(PACKAGE_ROOT),
        "engine_path": metadata_path(ENGINE_DST),
        "import_any_csv_path": metadata_path(IMPORT_ANY_CSV_DST),
        "windows_runtime_root": metadata_path(WINDOWS_RUNTIME_ROOT),
        "windows_runtime_manifest_path": metadata_path(WINDOWS_RUNTIME_MANIFEST_PATH),
        "windows_runtime_python_exe": metadata_path(WINDOWS_RUNTIME_PYTHON_ROOT / "python.exe"),
        "windows_runtime_primary_packages": runtime_manifest.get("primary_packages", []),
        "fault6_artifact_path": metadata_path(FAULT6_ARTIFACT_PATH),
        "fault6_preview_artifact_path": metadata_path(FAULT6_PREVIEW_ARTIFACT_PATH),
        "ktc_fault2_preview_artifact_path": metadata_path(KTC_FAULT2_PREVIEW_ARTIFACT_PATH),
        "fault6_provenance_path": metadata_path(FAULT6_PROVENANCE_PATH),
        "baseline_manifest_path": metadata_path(BASELINE_MANIFEST_PATH),
        "core_baseline_digest_path": metadata_path(CORE_BASELINE_DIGEST_PATH),
        "dependency_audit_json_path": metadata_path(DEPENDENCY_AUDIT_JSON_PATH),
        "dependency_audit_md_path": metadata_path(DEPENDENCY_AUDIT_MD_PATH),
        "packaged_runtime_chain_script_count": len(PACKAGED_RUNTIME_CHAIN_SCRIPTS),
        "packaged_runtime_chain_share_input_count": len(PACKAGED_RUNTIME_CHAIN_SHARE_INPUTS),
        "fault6_row_count": int(len(fault_df)),
        "fault6_preview_row_count": int(len(preview_df)),
        "ktc_fault2_preview_row_count": int(len(ktc_fault2_preview_df)),
        "run_demo_bat_path": metadata_path(RUN_DEMO_BAT_PATH),
        "run_demo_ktc_fault2_bat_path": metadata_path(RUN_DEMO_KTC_FAULT2_BAT_PATH),
        "run_guided_real_bat_path": metadata_path(RUN_GUIDED_REAL_BAT_PATH),
        "run_imported_real_bat_path": metadata_path(RUN_IMPORTED_REAL_BAT_PATH),
        "resolve_python_bat_path": metadata_path(RESOLVE_PYTHON_BAT_PATH),
        "root_live_fault_output_name": "fault_panel_result_current_v1.csv",
        "root_live_preview_output_name": "fault_panel_result_current_preview_v1.csv",
        "root_live_report_output_name": "fault_panel_result_current_report_v1.md",
        "root_master_report_output_name": "fault_panel_result_master_report_v1.md",
        "root_detailed_report_output_name": "fault_panel_result_detailed_report_v1.xlsx",
        "root_fault_signal_report_output_name": "fault_panel_result_raw_only_fault_signal_report_v1.csv",
        "root_raw_only_fault_output_name": "fault_panel_result_raw_only_current_v1.csv",
        "root_raw_only_preview_output_name": "fault_panel_result_raw_only_current_preview_v1.csv",
        "root_raw_only_report_output_name": "fault_panel_result_raw_only_current_report_v1.md",
        "snapshot_copy_script_name": "snapshot_copy.ps1",
        "incremental_run_script_name": "incremental_run.bat",
        "note_ko": (
            "이 pack은 실제 panel_day_engine.py 본체를 포함하는 최소 실행 pack이다. "
            "공식 결과 의미는 그대로 두고, 고정된 fault6 결과표와 preview artifact를 유지한다. "
            "fault6 결과표는 이제 frozen verdict와 heuristic를 직접 조합하고, legacy integrated 6행과 exact match 여부를 provenance로 함께 남긴다. "
            "또한 runtime용 bootstrap verdict와 full-chain 스크립트, 필요한 frozen share 입력을 package 내부에도 함께 실어 "
            "data 폴더 연결 후 live chain 실험을 package 안에서 직접 돌릴 수 있게 준비한다. "
            "동시에 raw-only strict chain도 별도로 포함해, panel_day_core와 precursor gate만으로 계산한 verdict/heuristic 결과를 "
            "current report와 별도 raw-only report로 함께 확인할 수 있게 한다. "
            "추가로 fault_panel_result_detailed_report_v1.xlsx를 자동 생성해, 메인표/근거요약/타임라인/군집요약을 한 파일로 확인할 수 있게 한다. "
            "추가로 baseline core output shadow compare reference와 full-chain dependency audit를 함께 넣어 "
            "현재 pack이 어디까지 live이고 어디서 blocker가 남는지 스스로 설명한다."
        ),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] conalog_full_runtime_v1 ready: {PACKAGE_ROOT}")


if __name__ == "__main__":
    main()
