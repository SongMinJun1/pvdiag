#!/usr/bin/env python3
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
if __package__ in {None, ""}:
    import sys

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from research.prognostics.heuristic_display_registry_v1 import DISPLAY_HEURISTIC_NAME_MAP
else:
    from .heuristic_display_registry_v1 import DISPLAY_HEURISTIC_NAME_MAP


FAULT6_TABLE_PATH = REPO_ROOT / "release/conalog_full_runtime_v1/package/artifacts/fault6_fixed_result_table_v1.csv"
FAULT6_PREVIEW_PATH = REPO_ROOT / "release/conalog_full_runtime_v1/package/artifacts/fault6_label_and_algorithm_preview_v1.csv"
INTEGRATED_TABLE_EXAMPLE_PATH = REPO_ROOT / "release/final_delivery_v1/package/examples/integrated_result_table_v1.csv"
INTEGRATED_SUMMARY_EXAMPLE_PATH = REPO_ROOT / "release/final_delivery_v1/package/examples/integrated_result_summary_v1.csv"
EVIDENCE_SUMMARY_EXAMPLE_PATH = REPO_ROOT / "release/final_delivery_v1/package/examples/panel_day_engine_gpvs_evidence_summary_v1.csv"
CAUSE_SUMMARY_EXAMPLE_PATH = REPO_ROOT / "release/final_delivery_v1/package/examples/panel_day_engine_cause_candidate_summary_v1.csv"
COVERAGE_MATRIX_EXAMPLE_PATH = REPO_ROOT / "release/final_delivery_v1/package/docs/panel_day_engine_fault_coverage_matrix_v1.csv"
MODEL_METRICS_EXAMPLE_PATH = REPO_ROOT / "release/final_delivery_v1/package/docs/panel_day_engine_model_metrics_v1.csv"
RUNTIME_LATENCY_EXAMPLE_PATH = REPO_ROOT / "release/final_delivery_v1/package/runtime/panel_day_engine_runtime_latency_report_v1.csv"
RUNTIME_READINESS_EXAMPLE_PATH = REPO_ROOT / "release/final_delivery_v1/package/runtime/panel_day_engine_runtime_readiness_summary_v1.csv"

VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
GPVS_EVIDENCE_PACK_NAME = "panel_day_engine_gpvs_evidence_pack_v1.csv"
HEURISTIC_NAME = "panel_day_engine_cause_candidate_heuristics_v1.csv"
FAULT_EVENT_AUDIT_NAME = "panel_day_engine_fault_panel_event_audit_v1.csv"
INTEGRATED_TABLE_NAME = "panel_day_engine_integrated_result_table_v1.csv"
INTEGRATED_SUMMARY_NAME = "panel_day_engine_integrated_result_summary_v1.csv"
EVIDENCE_SUMMARY_NAME = "panel_day_engine_gpvs_evidence_summary_v1.csv"
CAUSE_SUMMARY_NAME = "panel_day_engine_cause_candidate_summary_v1.csv"
COVERAGE_MATRIX_NAME = "panel_day_engine_fault_coverage_matrix_v1.csv"
MODEL_METRICS_NAME = "panel_day_engine_model_metrics_v1.csv"
RUNTIME_LATENCY_NAME = "panel_day_engine_runtime_latency_report_v1.csv"
RUNTIME_READINESS_NAME = "panel_day_engine_runtime_readiness_summary_v1.csv"

DISPLAY_TO_RAW_LABEL = {display: raw for raw, display in DISPLAY_HEURISTIC_NAME_MAP.items()}
CORE_REFERENCE_KEYS = {
    ("conalog", "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0"),
    ("conalog", "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"),
}
HEURISTIC_CONTEXT = {
    ("conalog", "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0"): {
        "competition_state": "단일우세",
        "competition_csv": "다이오드·서브스트링형",
        "action_note": "다이오드·서브스트링형 우선 점검",
    },
    ("conalog", "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"): {
        "competition_state": "2자경합",
        "competition_csv": "센서·피드백형,접속·부분개방형",
        "action_note": "센서·피드백형과 접속·부분개방형을 함께 우선 점검",
    },
    ("gangui", "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7"): {
        "competition_state": "다자경합",
        "competition_csv": "다이오드·서브스트링형,센서·피드백형,접속·부분개방형",
        "action_note": "다이오드·서브스트링형, 센서·피드백형, 접속·부분개방형을 함께 우선 점검",
    },
    ("gangui", "bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16"): {
        "competition_state": "다자경합",
        "competition_csv": "다이오드·서브스트링형,센서·피드백형,접속·부분개방형",
        "action_note": "다이오드·서브스트링형, 센서·피드백형, 접속·부분개방형을 함께 우선 점검",
    },
    ("ktc_ess", "10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12"): {
        "competition_state": "단일우세",
        "competition_csv": "다이오드·서브스트링형",
        "action_note": "다이오드·서브스트링형 우선 점검",
    },
    ("ktc_ess", "70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4"): {
        "competition_state": "다자경합",
        "competition_csv": "열화형,센서·피드백형,다이오드·서브스트링형",
        "action_note": "열화형, 센서·피드백형, 다이오드·서브스트링형을 함께 우선 점검",
    },
}


def _normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def _share_path(root: Path, filename: str) -> Path:
    return root / "_share" / filename


def _discover_worktree_primary_data_root(root: Path) -> Path | None:
    git_pointer = root / ".git"
    if not git_pointer.exists() or not git_pointer.is_file():
        return None
    text = git_pointer.read_text(encoding="utf-8").strip()
    prefix = "gitdir:"
    if not text.startswith(prefix):
        return None
    gitdir = Path(text[len(prefix) :].strip()).resolve()
    common_git_dir = gitdir.parents[1]
    candidate = common_git_dir.parent / "data"
    return candidate if candidate.exists() else None


def _discover_worktree_primary_share_root(root: Path) -> Path | None:
    git_pointer = root / ".git"
    if not git_pointer.exists() or not git_pointer.is_file():
        return None
    text = git_pointer.read_text(encoding="utf-8").strip()
    prefix = "gitdir:"
    if not text.startswith(prefix):
        return None
    gitdir = Path(text[len(prefix) :].strip()).resolve()
    common_git_dir = gitdir.parents[1]
    candidate = common_git_dir.parent / "_share"
    return candidate if candidate.exists() else None


def _copy_csv_fixture(path: Path, source: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(source.read_bytes())


def _build_verdict_fixture_df() -> pd.DataFrame:
    integrated_df = pd.read_csv(INTEGRATED_TABLE_EXAMPLE_PATH, low_memory=False, encoding="utf-8-sig")
    preview_df = pd.read_csv(FAULT6_PREVIEW_PATH, low_memory=False, encoding="utf-8-sig")
    preview_lookup = {
        (_normalize_text(row["site"]), _normalize_text(row["panel_id"])): row
        for row in preview_df.to_dict(orient="records")
    }
    rows: list[dict[str, str]] = []
    for row in integrated_df.to_dict(orient="records"):
        key = (_normalize_text(row["site"]), _normalize_text(row["panel_id"]))
        preview_row = preview_lookup.get(key, {})
        precursor_date = _normalize_text(preview_row.get("전조날짜"))
        if precursor_date == "전조없음":
            precursor_date = ""
        rows.append(
            {
                "site": key[0],
                "panel_id": key[1],
                "패널고장여부_ko": _normalize_text(row["패널고장여부_ko"]),
                "사건유형_ko": _normalize_text(row["사건유형_ko"]),
                "최종고장양상_ko": _normalize_text(row["최종고장양상_ko"]),
                "커널로그_원인군_ko": _normalize_text(row["커널로그_원인군_ko"]),
                "운영최초전조발견일": precursor_date,
                "사건해석상전조시작일": precursor_date,
                "세부fault_기준일": _normalize_text(preview_row.get("고장 기준일")),
            }
        )
    return pd.DataFrame(rows)


def _raw_label(display_label: object) -> str:
    normalized = _normalize_text(display_label)
    return DISPLAY_TO_RAW_LABEL.get(normalized, normalized)


def _build_heuristic_fixture_df() -> pd.DataFrame:
    fault_df = pd.read_csv(FAULT6_TABLE_PATH, low_memory=False, encoding="utf-8-sig")
    rows: list[dict[str, str]] = []
    for row in fault_df.to_dict(orient="records"):
        key = (_normalize_text(row["site"]), _normalize_text(row["panel_id"]))
        context = HEURISTIC_CONTEXT[key]
        rows.append(
            {
                "site": key[0],
                "panel_id": key[1],
                "원인후보_top1_ko": _raw_label(row["1순위_의심원인_ko"]),
                "원인후보_top2_ko": _raw_label(row["2순위_의심원인_ko"]),
                "원인후보_top3_ko": _raw_label(row["3순위_의심원인_ko"]),
                "원인후보_경합상태_ko": context["competition_state"],
                "원인후보_공동상위후보_csv": context["competition_csv"],
                "원인후보_실증우선확인_ko": context["action_note"],
            }
        )
    return pd.DataFrame(rows)


def _build_gpvs_evidence_pack_df() -> pd.DataFrame:
    fault_df = pd.read_csv(FAULT6_TABLE_PATH, low_memory=False, encoding="utf-8-sig")
    rows: list[dict[str, str]] = []
    for row in fault_df.to_dict(orient="records"):
        key = (_normalize_text(row["site"]), _normalize_text(row["panel_id"]))
        rows.append(
            {
                "site": key[0],
                "panel_id": key[1],
                "GPVS_최종사용권고_ko": "핵심참조" if key in CORE_REFERENCE_KEYS else "보조참조",
            }
        )
    return pd.DataFrame(rows)


def _build_fault_event_audit_fixture_df() -> pd.DataFrame:
    preview_df = pd.read_csv(FAULT6_PREVIEW_PATH, low_memory=False, encoding="utf-8-sig")
    rows: list[dict[str, str]] = []
    for row in preview_df.to_dict(orient="records"):
        precursor_date = _normalize_text(row["전조날짜"])
        if precursor_date == "전조없음":
            precursor_date = ""
        fault_date = _normalize_text(row["고장 기준일"])
        rows.append(
            {
                "site": _normalize_text(row["site"]),
                "panel_id": _normalize_text(row["panel_id"]),
                "earliest_warning_date": precursor_date,
                "retrospective_onset_date": precursor_date,
                "strict_trigger_date": fault_date,
                "first_final_fault_date": fault_date,
            }
        )
    return pd.DataFrame(rows)


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def _write_placeholder_csv(path: Path, filename: str) -> None:
    _write_csv(pd.DataFrame([{"fixture_name": filename, "note_ko": "smoke placeholder fixture"}]), path)


def write_share_fixture(root: Path, filename: str) -> None:
    path = _share_path(root, filename)
    primary_share_root = _discover_worktree_primary_share_root(root)
    if primary_share_root is not None:
        primary_source = primary_share_root / filename
        if primary_source.exists():
            _copy_csv_fixture(path, primary_source)
            return
    if filename == VERDICT_NAME:
        _write_csv(_build_verdict_fixture_df(), path)
        return
    if filename == GPVS_EVIDENCE_PACK_NAME:
        _write_csv(_build_gpvs_evidence_pack_df(), path)
        return
    if filename == HEURISTIC_NAME:
        _write_csv(_build_heuristic_fixture_df(), path)
        return
    if filename == FAULT_EVENT_AUDIT_NAME:
        _write_csv(_build_fault_event_audit_fixture_df(), path)
        return
    copy_sources = {
        INTEGRATED_TABLE_NAME: INTEGRATED_TABLE_EXAMPLE_PATH,
        INTEGRATED_SUMMARY_NAME: INTEGRATED_SUMMARY_EXAMPLE_PATH,
        EVIDENCE_SUMMARY_NAME: EVIDENCE_SUMMARY_EXAMPLE_PATH,
        CAUSE_SUMMARY_NAME: CAUSE_SUMMARY_EXAMPLE_PATH,
        COVERAGE_MATRIX_NAME: COVERAGE_MATRIX_EXAMPLE_PATH,
        MODEL_METRICS_NAME: MODEL_METRICS_EXAMPLE_PATH,
        RUNTIME_LATENCY_NAME: RUNTIME_LATENCY_EXAMPLE_PATH,
        RUNTIME_READINESS_NAME: RUNTIME_READINESS_EXAMPLE_PATH,
    }
    source = copy_sources.get(filename)
    if source is None:
        _write_placeholder_csv(path, filename)
        return
    _copy_csv_fixture(path, source)


@contextmanager
def stage_missing_share_fixtures(root: Path, filenames: list[str]):
    root = root.resolve()
    (root / "_share").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "outputs" / "validation").mkdir(parents=True, exist_ok=True)

    originals: dict[Path, bytes | None] = {}
    for filename in filenames:
        path = _share_path(root, filename)
        originals[path] = path.read_bytes() if path.exists() else None
        if originals[path] is None:
            write_share_fixture(root, filename)
    try:
        yield
    finally:
        for path, payload in originals.items():
            if payload is None:
                if path.exists():
                    path.unlink()
                continue
            path.write_bytes(payload)


@contextmanager
def stage_missing_repo_data_link(root: Path):
    root = root.resolve()
    data_path = root / "data"
    if data_path.exists():
        yield
        return
    source = _discover_worktree_primary_data_root(root)
    if source is None:
        yield
        return
    data_path.symlink_to(source, target_is_directory=True)
    try:
        yield
    finally:
        if data_path.is_symlink():
            data_path.unlink()
