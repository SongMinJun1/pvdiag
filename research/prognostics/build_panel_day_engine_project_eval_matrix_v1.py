#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

FAULT_TAXONOMY_NAME = "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv"
PRECURSOR_ONSET_TRUTH_NAME = "panel_day_engine_precursor_onset_truth_v1.csv"
PRECURSOR_ONSET_SUMMARY_NAME = "panel_day_engine_precursor_onset_summary_v1.csv"
PRECURSOR_PERFORMANCE_CASES_NAME = "panel_day_engine_precursor_performance_cases_v1.csv"
NON_PRECURSOR_PERFORMANCE_CASES_NAME = "panel_day_engine_non_precursor_performance_cases_v1.csv"
COMMON_CAUSE_CASES_NAME = "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv"
BASELINE_ATTENTION_NAME = "panel_day_engine_operator_attention_now_v1.csv"
PANEL_PREVIEW_NAME = "panel_day_engine_operator_attention_plus_discovery_preview_v1.csv"
NARROW_PREVIEW_NAME = "panel_day_engine_operator_attention_plus_discovery_preview_narrow_v1.csv"
CLUSTER_PREVIEW_NAME = "panel_day_engine_operator_attention_plus_discovery_cluster_preview_v1.csv"
WORKFLOW_DEFAULT_NAME = "panel_day_engine_operator_workflow_default_v1.csv"
CLUSTER_ROLLUP_NAME = "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.csv"
REAUDIT_NAME = "panel_date_reaudit_working.csv"
ELIGIBILITY_CASES_NAME = "panel_day_engine_local_precursor_eligibility_cases_v1.csv"
ABRUPT6_SYMPTOM_MAP_NAME = "panel_day_engine_abrupt6_symptom_map_v1.csv"
PRECURSOR_ABRUPT_CONSISTENCY_CASES_NAME = "panel_day_engine_precursor_abrupt_consistency_cases_v1.csv"
PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME = "panel_day_engine_precursor_abrupt_consistency_summary_v1.csv"
PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME = "panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv"
FORENSIC_SUMMARY_NAME = "panel_day_engine_c42997_1_1_forensic_summary_v1.csv"
FAULT_PANEL_EVENT_AUDIT_NAME = "panel_day_engine_fault_panel_event_audit_v1.csv"
FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME = "panel_day_engine_fault_panel_event_audit_summary_v1.csv"
GATE_DAILY_NAME = "ae_simple_local_precursor_gate_daily.csv"
CORE_NAME = "panel_day_core.csv"

MATRIX_OUTPUT_NAME = "panel_day_engine_project_eval_matrix_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_project_eval_matrix_summary_v1.csv"
NOTES_OUTPUT_NAME = "panel_day_engine_project_eval_notes_v1.csv"

WINDOW_DAYS = 30
ABRUPT_LOOKBACK_DAYS = 3
ABRUPT_LOOKAHEAD_DAYS = 7

FORENSIC_HOLDOUT_SITE = "conalog"
FORENSIC_HOLDOUT_PANEL_ID = "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"
FORENSIC_HOLDOUT_WARNING_DATE = "2025-01-20"
FORENSIC_HOLDOUT_TRIGGER_DATE = "2025-03-21"

STEP2_TARGETS = [
    "preferred_precursor_onset",
    "first_cond_evt",
    "first_cond_evt_corroborated",
    "first_signalcount2",
    "first_pre_ews",
    "first_ews_warning",
    "first_pre_alarm",
]
STEP3_MARKERS = [
    "first_cond_evt",
    "first_cond_evt_corroborated",
    "first_signalcount2",
    "first_pre_ews",
    "first_ews_warning",
    "first_pre_alarm",
]
STEP4A_TARGETS = [
    "final_fault_hit_by_anchor",
    "final_fault_hit_within_3d_after",
    "final_fault_hit_within_7d_after",
    "critical_fault_hit_within_7d_after",
    "confirmed_fault_hit_within_7d_after",
]
STEP4B_TARGETS = [
    "current_marker_only",
    "breadth_marker_only",
    "combined_marker",
]
OPERATOR_POLICIES = [
    "baseline_only",
    "baseline_plus_discovery_panel",
    "baseline_plus_discovery_narrow",
    "baseline_plus_discovery_cluster",
    "workflow_default",
]

MATRIX_COLS = [
    "eval_scope",
    "eval_part_name",
    "metric_kind",
    "unit_type",
    "positive_set_name",
    "negative_set_name",
    "target_name",
    "support_positive",
    "support_negative",
    "tp",
    "fp",
    "fn",
    "tn",
    "recall",
    "precision",
    "f1",
    "note_ko",
]

SUMMARY_COLS = [
    "eval_scope",
    "best_target_name",
    "best_f1",
    "best_recall",
    "best_precision",
    "note_ko",
]

NOTES_COLS = [
    "eval_scope",
    "why_prf_is_valid_or_not",
    "caveat_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an integrated project evaluation matrix that reports structural coverage, true case metrics, and retrospective operator proxy metrics where meaningful."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the project root.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def normalize_date_text(value: object) -> str:
    text = normalize_text(value)
    return text[:10] if len(text) >= 10 else text


def parse_timestamp(value: object) -> pd.Timestamp | pd.NaT:
    text = normalize_date_text(value)
    if not text:
        return pd.NaT
    return pd.to_datetime(text, errors="coerce")


def to_int_flag(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"", "0", "0.0", "false", "f", "n", "no"}:
        return 0
    if text in {"1", "1.0", "true", "t", "y", "yes"}:
        return 1
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return int(bool(numeric)) if not pd.isna(numeric) else 0


def numeric_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return 0
    return int(numeric)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def drop_repeated_header_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    header_mask = pd.Series(True, index=df.index)
    for col in df.columns:
        header_mask &= df[col].map(normalize_text).eq(col)
    return df.loc[~header_mask].reset_index(drop=True)


def read_site_subset_csv(
    path: Path,
    *,
    requested_cols: list[str],
    panels: set[str],
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
    site: str,
) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")

    chunks: list[pd.DataFrame] = []
    usecols = lambda col: col in requested_cols
    for chunk in pd.read_csv(
        path,
        usecols=usecols,
        chunksize=100_000,
        low_memory=False,
        encoding="utf-8-sig",
    ):
        chunk = drop_repeated_header_rows(chunk)
        if chunk.empty:
            continue
        chunk["panel_id"] = chunk["panel_id"].map(normalize_text)
        chunk = chunk.loc[chunk["panel_id"].isin(panels)].copy()
        if chunk.empty:
            continue
        chunk["date"] = chunk["date"].map(parse_timestamp)
        chunk = chunk.loc[chunk["date"].notna()].copy()
        chunk = chunk.loc[chunk["date"].ge(window_start) & chunk["date"].le(window_end)].copy()
        if chunk.empty:
            continue
        chunk["site"] = site
        chunks.append(chunk)

    if not chunks:
        return pd.DataFrame(columns=["site", *requested_cols])
    return pd.concat(chunks, ignore_index=True)


def load_site_daily(root: Path, site: str, panels: set[str], window_start: pd.Timestamp, window_end: pd.Timestamp) -> pd.DataFrame:
    out_dir = root / "data" / site / "out"
    gate_df = read_site_subset_csv(
        out_dir / GATE_DAILY_NAME,
        requested_cols=[
            "panel_id",
            "date",
            "cond_var",
            "cond_evt",
            "cond_dtw",
            "cond_hs",
            "pre_ews",
            "signal_count",
            "ews_warning",
            "pre_alarm",
            "group_off_date",
        ],
        panels=panels,
        window_start=window_start,
        window_end=window_end,
        site=site,
    )
    core_df = read_site_subset_csv(
        out_dir / CORE_NAME,
        requested_cols=[
            "panel_id",
            "date",
            "confirmed_fault",
            "critical_fault",
            "final_fault",
            "group_off_like",
            "shadow_like",
        ],
        panels=panels,
        window_start=window_start,
        window_end=window_end,
        site=site,
    )

    ensure_columns(gate_df, ["site", "panel_id", "date"], f"{site}/{GATE_DAILY_NAME}")
    ensure_columns(core_df, ["site", "panel_id", "date"], f"{site}/{CORE_NAME}")

    gate_df = gate_df.loc[:, ["site", "panel_id", "date", "cond_var", "cond_evt", "cond_dtw", "cond_hs", "pre_ews", "signal_count", "ews_warning", "pre_alarm", "group_off_date"]].copy()
    core_df = core_df.loc[:, ["site", "panel_id", "date", "confirmed_fault", "critical_fault", "final_fault", "group_off_like", "shadow_like"]].copy()

    daily = core_df.merge(gate_df, on=["site", "panel_id", "date"], how="outer")
    for col in [
        "cond_var",
        "cond_evt",
        "cond_dtw",
        "cond_hs",
        "pre_ews",
        "signal_count",
        "ews_warning",
        "pre_alarm",
        "group_off_date",
        "confirmed_fault",
        "critical_fault",
        "final_fault",
        "group_off_like",
        "shadow_like",
    ]:
        daily[col] = daily.get(col, 0).fillna(0).map(to_int_flag).astype(int)
    daily["cond_evt_corroborated_flag"] = (
        daily["cond_evt"].eq(1) & daily[["cond_var", "cond_dtw", "cond_hs"]].max(axis=1).eq(1)
    ).astype(int)
    daily["date"] = daily["date"].map(parse_timestamp)
    return daily.sort_values(["panel_id", "date"]).reset_index(drop=True)


def load_daily_windows(root: Path, cases_df: pd.DataFrame, *, anchor_col: str, lookback_days: int, lookahead_days: int) -> pd.DataFrame:
    if cases_df.empty:
        return pd.DataFrame(
            columns=[
                "site",
                "panel_id",
                "date",
                "cond_var",
                "cond_evt",
                "cond_dtw",
                "cond_hs",
                "pre_ews",
                "signal_count",
                "ews_warning",
                "pre_alarm",
                "group_off_date",
                "confirmed_fault",
                "critical_fault",
                "final_fault",
                "group_off_like",
                "shadow_like",
                "cond_evt_corroborated_flag",
            ]
        )

    site_frames: list[pd.DataFrame] = []
    for site, site_cases in cases_df.groupby("site"):
        panels = set(site_cases["panel_id"].astype(str))
        anchors = site_cases[anchor_col].map(parse_timestamp)
        window_start = anchors.min() - pd.Timedelta(days=lookback_days)
        window_end = anchors.max() + pd.Timedelta(days=lookahead_days)
        site_frames.append(load_site_daily(root, site, panels, window_start, window_end))
    return pd.concat(site_frames, ignore_index=True) if site_frames else pd.DataFrame()


def safe_div(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator)


def compute_prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    recall = safe_div(tp, tp + fn)
    precision = safe_div(tp, tp + fp)
    f1 = 0.0 if (precision + recall) == 0 else (2.0 * precision * recall) / (precision + recall)
    return recall, precision, f1


def format_metric(value: float | None, *, blank: bool = False) -> object:
    if blank or value is None:
        return ""
    return float(value)


def load_required_inputs(root: Path) -> dict[str, pd.DataFrame]:
    share_dir = root / "_share"
    frames = {
        "taxonomy": drop_repeated_header_rows(read_csv(share_dir / FAULT_TAXONOMY_NAME)),
        "onset_truth": drop_repeated_header_rows(read_csv(share_dir / PRECURSOR_ONSET_TRUTH_NAME)),
        "onset_summary": drop_repeated_header_rows(read_csv(share_dir / PRECURSOR_ONSET_SUMMARY_NAME)),
        "precursor_perf": drop_repeated_header_rows(read_csv(share_dir / PRECURSOR_PERFORMANCE_CASES_NAME)),
        "nonprec": drop_repeated_header_rows(read_csv(share_dir / NON_PRECURSOR_PERFORMANCE_CASES_NAME)),
        "common_cause": drop_repeated_header_rows(read_csv(share_dir / COMMON_CAUSE_CASES_NAME)),
        "baseline_attention": drop_repeated_header_rows(read_csv(share_dir / BASELINE_ATTENTION_NAME)),
        "panel_preview": drop_repeated_header_rows(read_csv(share_dir / PANEL_PREVIEW_NAME)),
        "narrow_preview": drop_repeated_header_rows(read_csv(share_dir / NARROW_PREVIEW_NAME)),
        "cluster_preview": drop_repeated_header_rows(read_csv(share_dir / CLUSTER_PREVIEW_NAME)),
        "workflow_default": drop_repeated_header_rows(read_csv(share_dir / WORKFLOW_DEFAULT_NAME)),
        "cluster_rollup": drop_repeated_header_rows(read_csv(share_dir / CLUSTER_ROLLUP_NAME)),
        "reaudit": drop_repeated_header_rows(read_csv(share_dir / REAUDIT_NAME)),
        "eligibility": drop_repeated_header_rows(read_csv(share_dir / ELIGIBILITY_CASES_NAME)),
        "abrupt6": drop_repeated_header_rows(read_csv(share_dir / ABRUPT6_SYMPTOM_MAP_NAME)),
        "consistency_cases": drop_repeated_header_rows(read_csv(share_dir / PRECURSOR_ABRUPT_CONSISTENCY_CASES_NAME)),
        "consistency_summary": drop_repeated_header_rows(read_csv(share_dir / PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME)),
        "consistency_recommendation": drop_repeated_header_rows(read_csv(share_dir / PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME)),
        "forensic_summary": drop_repeated_header_rows(read_csv(share_dir / FORENSIC_SUMMARY_NAME)),
        "fault_event_audit": drop_repeated_header_rows(read_csv(share_dir / FAULT_PANEL_EVENT_AUDIT_NAME)),
        "fault_event_audit_summary": drop_repeated_header_rows(read_csv(share_dir / FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME)),
    }

    ensure_columns(frames["taxonomy"], ["fault_family_id", "eval_bucket_v2"], FAULT_TAXONOMY_NAME)
    ensure_columns(frames["onset_truth"], ["site", "panel_id", "fault_start_date", "preferred_precursor_onset_date"], PRECURSOR_ONSET_TRUTH_NAME)
    ensure_columns(frames["onset_summary"], ["summary_type", "marker_name", "case_count", "available_case_count"], PRECURSOR_ONSET_SUMMARY_NAME)
    ensure_columns(frames["precursor_perf"], ["site", "panel_id", "fault_start_date"], PRECURSOR_PERFORMANCE_CASES_NAME)
    ensure_columns(frames["nonprec"], ["eval_bucket_v2", "site", "panel_id", "anchor_date", "truth_case_id"], NON_PRECURSOR_PERFORMANCE_CASES_NAME)
    ensure_columns(frames["common_cause"], ["eval_bucket_v2", "site", "panel_id"], COMMON_CAUSE_CASES_NAME)
    ensure_columns(frames["baseline_attention"], ["attention_class", "site", "panel_id", "attention_any_future_fault_linked_ref_flag", "attention_any_future_truth_linked_ref_flag"], BASELINE_ATTENTION_NAME)
    ensure_columns(frames["panel_preview"], ["preview_attention_class", "site", "panel_id", "attention_any_future_fault_linked_ref_flag", "attention_any_future_truth_linked_ref_flag"], PANEL_PREVIEW_NAME)
    ensure_columns(frames["narrow_preview"], ["preview_attention_class", "site", "panel_id", "attention_any_future_fault_linked_ref_flag", "attention_any_future_truth_linked_ref_flag"], NARROW_PREVIEW_NAME)
    ensure_columns(frames["cluster_preview"], ["preview_attention_class", "site", "display_entity_id", "linked_ref_flag", "truth_ref_flag"], CLUSTER_PREVIEW_NAME)
    ensure_columns(frames["workflow_default"], ["preview_attention_class", "site", "display_entity_id", "linked_ref_flag", "truth_ref_flag"], WORKFLOW_DEFAULT_NAME)
    ensure_columns(frames["cluster_rollup"], ["site", "cluster_id", "panel_ids_csv"], CLUSTER_ROLLUP_NAME)
    ensure_columns(frames["reaudit"], ["site", "panel_id", "strict_trigger_date"], REAUDIT_NAME)
    ensure_columns(frames["eligibility"], ["site", "panel_id", "fault_start_date"], ELIGIBILITY_CASES_NAME)
    ensure_columns(
        frames["abrupt6"],
        ["site", "panel_id", "고장시점", "사건유형_ko", "최종고장양상_ko", "순수급작_flag"],
        ABRUPT6_SYMPTOM_MAP_NAME,
    )
    ensure_columns(
        frames["consistency_cases"],
        ["site", "panel_id", "same_event_flag", "distinct_event_flag", "consistency_judgment_ko"],
        PRECURSOR_ABRUPT_CONSISTENCY_CASES_NAME,
    )
    ensure_columns(
        frames["consistency_summary"],
        ["overlap_panel_count", "same_event_count", "corrected_pure_abrupt_fault_count"],
        PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME,
    )
    ensure_columns(
        frames["consistency_recommendation"],
        ["recommended_next_handling", "rationale_ko"],
        PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME,
    )
    ensure_columns(
        frames["forensic_summary"],
        ["site", "panel_id", "전조흔적_시작일", "강한트리거일", "사건시간양상_판정_ko", "현재표_보정필요여부_flag"],
        FORENSIC_SUMMARY_NAME,
    )
    ensure_columns(
        frames["fault_event_audit"],
        ["site", "panel_id", "사건유형_재판정_ko", "최종고장양상_재판정_ko", "전조평가셋편입_flag", "급작평가셋편입_flag"],
        FAULT_PANEL_EVENT_AUDIT_NAME,
    )
    ensure_columns(
        frames["fault_event_audit_summary"],
        [
            "고유_고장패널수",
            "사건유형_재판정_전조형수",
            "사건유형_재판정_급작수",
            "사건유형_재판정_보류수",
            "전조흔적_패널수",
            "순수급작_패널수",
            "전조평가셋편입_패널수",
            "급작평가셋편입_패널수",
            "해석과평가셋불일치_패널수",
        ],
        FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME,
    )
    return frames


def load_same_event_overlap_keys(frames: dict[str, pd.DataFrame]) -> set[tuple[str, str]]:
    recommendation_df = frames["consistency_recommendation"]
    if len(recommendation_df) != 1:
        raise SystemExit(
            f"{PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME} must contain exactly one row, found {len(recommendation_df)}"
        )
    recommendation = normalize_text(recommendation_df.iloc[0]["recommended_next_handling"])
    if recommendation != "relabel_overlap_as_precursor_led_faults":
        raise SystemExit(
            "precursor/abrupt consistency recommendation must be relabel_overlap_as_precursor_led_faults to build the corrected eval matrix; "
            f"got {recommendation or '<blank>'}"
        )

    cases_df = frames["consistency_cases"]
    same_event_df = cases_df.loc[pd.to_numeric(cases_df["same_event_flag"], errors="coerce").fillna(0).eq(1)].copy()
    overlap_keys = {
        (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        for row in same_event_df.to_dict(orient="records")
        if normalize_text(row["site"]) and normalize_text(row["panel_id"])
    }
    summary_row = frames["consistency_summary"].iloc[0].to_dict()
    expected_overlap = int(pd.to_numeric(summary_row["overlap_panel_count"], errors="raise"))
    expected_same = int(pd.to_numeric(summary_row["same_event_count"], errors="raise"))
    corrected_pure_abrupt = int(pd.to_numeric(summary_row["corrected_pure_abrupt_fault_count"], errors="raise"))
    if expected_overlap != expected_same:
        raise SystemExit(
            f"{PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME} must keep overlap_panel_count == same_event_count for this reconciliation"
        )
    if len(overlap_keys) != expected_same:
        raise SystemExit(
            f"same-event overlap count mismatch between cases and summary: cases={len(overlap_keys)}, summary={expected_same}"
        )
    if corrected_pure_abrupt != 4:
        raise SystemExit(f"expected corrected pure abrupt fault count to be 4, found {corrected_pure_abrupt}")
    return overlap_keys


def load_fault_event_audit_summary(frames: dict[str, pd.DataFrame]) -> dict[str, int]:
    summary_df = frames["fault_event_audit_summary"]
    if len(summary_df) != 1:
        raise SystemExit(
            f"{FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME} must contain exactly one row, found {len(summary_df)}"
        )
    row = summary_df.iloc[0].to_dict()
    summary = {
        "fault_panel_count": numeric_int(row["고유_고장패널수"]),
        "interpreted_precursor_count": numeric_int(row["사건유형_재판정_전조형수"]),
        "interpreted_abrupt_count": numeric_int(row["사건유형_재판정_급작수"]),
        "holdout_count": numeric_int(row["사건유형_재판정_보류수"]),
        "precursor_trace_count": numeric_int(row["전조흔적_패널수"]),
        "pure_abrupt_eval_count": numeric_int(row["순수급작_패널수"]),
    }
    if summary["fault_panel_count"] != 6:
        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME} fault panel count must be 6")
    if summary["interpreted_precursor_count"] != 3 or summary["interpreted_abrupt_count"] != 3:
        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME} must keep interpretation precursor/abrupt split 3/3")
    if summary["holdout_count"] != 0:
        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME} holdout count must be 0")
    if summary["pure_abrupt_eval_count"] != 3:
        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME} pure abrupt benchmark support must be 3")
    return summary


def build_step1_rows(taxonomy_df: pd.DataFrame) -> list[dict[str, object]]:
    taxonomy_df = taxonomy_df.copy()
    taxonomy_df["eval_bucket_v2"] = taxonomy_df["eval_bucket_v2"].map(normalize_text)
    taxonomy_df["fault_family_id"] = taxonomy_df["fault_family_id"].map(normalize_text)
    counts = (
        taxonomy_df.loc[taxonomy_df["eval_bucket_v2"].ne("")]
        .groupby("eval_bucket_v2")["fault_family_id"]
        .nunique()
        .sort_index()
    )
    rows: list[dict[str, object]] = []
    for bucket_name, family_count in counts.items():
        rows.append(
            {
                "eval_scope": "step1_taxonomy",
                "eval_part_name": "taxonomy_support",
                "metric_kind": "structural_coverage_metric",
                "unit_type": "family",
                "positive_set_name": bucket_name,
                "negative_set_name": "",
                "target_name": bucket_name,
                "support_positive": int(family_count),
                "support_negative": "",
                "tp": "",
                "fp": "",
                "fn": "",
                "tn": "",
                "recall": "",
                "precision": "",
                "f1": "",
                "note_ko": "taxonomy/support only row이며 classifier precision/recall/F1로 해석하면 안 된다.",
            }
        )
    return rows


def build_step2_rows(onset_truth_df: pd.DataFrame, onset_summary_df: pd.DataFrame) -> list[dict[str, object]]:
    onset_truth_df = onset_truth_df.copy()
    onset_truth_df["preferred_precursor_onset_date"] = onset_truth_df["preferred_precursor_onset_date"].map(normalize_date_text)
    case_count = len(onset_truth_df)
    onset_summary_df = onset_summary_df.copy()
    onset_summary_df["summary_type"] = onset_summary_df["summary_type"].map(normalize_text)
    onset_summary_df["marker_name"] = onset_summary_df["marker_name"].map(normalize_text)

    marker_summary = onset_summary_df.loc[onset_summary_df["summary_type"].eq("onset_marker")].copy()
    marker_summary["case_count"] = pd.to_numeric(marker_summary["case_count"], errors="coerce").fillna(0).astype(int)
    marker_summary["available_case_count"] = (
        pd.to_numeric(marker_summary["available_case_count"], errors="coerce").fillna(0).astype(int)
    )
    marker_map = {normalize_text(row["marker_name"]): row for _, row in marker_summary.iterrows()}

    rows: list[dict[str, object]] = []
    preferred_available = int(onset_truth_df["preferred_precursor_onset_date"].ne("").sum())
    rows.append(
        {
            "eval_scope": "step2_onset_truth",
            "eval_part_name": "onset_coverage",
            "metric_kind": "structural_coverage_metric",
            "unit_type": "case",
            "positive_set_name": "onset_truth_cases",
            "negative_set_name": "",
            "target_name": "preferred_precursor_onset",
            "support_positive": int(case_count),
            "support_negative": "",
            "tp": preferred_available,
            "fp": "",
            "fn": int(case_count - preferred_available),
            "tn": "",
            "recall": "",
            "precision": "",
            "f1": "",
            "note_ko": "preferred precursor onset는 coverage/lead reference이며 classifier precision/recall/F1 대상이 아니다.",
        }
    )
    for marker_name in STEP3_MARKERS:
        row = marker_map.get(marker_name)
        marker_case_count = int(row["case_count"]) if row is not None else int(case_count)
        available_case_count = int(row["available_case_count"]) if row is not None else 0
        rows.append(
            {
                "eval_scope": "step2_onset_truth",
                "eval_part_name": "onset_coverage",
                "metric_kind": "structural_coverage_metric",
                "unit_type": "case",
                "positive_set_name": "onset_truth_cases",
                "negative_set_name": "",
                "target_name": marker_name,
                "support_positive": marker_case_count,
                "support_negative": "",
                "tp": available_case_count,
                "fp": "",
                "fn": int(marker_case_count - available_case_count),
                "tn": "",
                "recall": "",
                "precision": "",
                "f1": "",
                "note_ko": "onset marker row는 truth coverage/lead 확인용이라 classifier precision/recall/F1로 해석하면 안 된다.",
            }
        )
    return rows


def build_step3_negative_hits(root: Path, nonprec_df: pd.DataFrame) -> dict[tuple[str, str], dict[str, int]]:
    negative_cases = nonprec_df.loc[
        nonprec_df["eval_bucket_v2"].map(normalize_text).isin(["abrupt_or_no_precursor_now", "non_panel_or_common_cause"])
    ].copy()
    negative_cases["site"] = negative_cases["site"].map(normalize_text)
    negative_cases["panel_id"] = negative_cases["panel_id"].map(normalize_text)
    negative_cases["truth_case_id"] = negative_cases["truth_case_id"].map(normalize_text)
    negative_cases["anchor_date"] = negative_cases["anchor_date"].map(normalize_date_text)
    negative_cases = negative_cases.drop_duplicates(subset=["truth_case_id"], keep="first")
    if negative_cases.empty:
        return {}

    daily_df = load_daily_windows(root, negative_cases.loc[:, ["site", "panel_id", "anchor_date"]], anchor_col="anchor_date", lookback_days=WINDOW_DAYS, lookahead_days=0)
    hits: dict[tuple[str, str], dict[str, int]] = {}
    for case in negative_cases.to_dict(orient="records"):
        site = normalize_text(case["site"])
        panel_id = normalize_text(case["panel_id"])
        truth_case_id = normalize_text(case["truth_case_id"])
        anchor_ts = parse_timestamp(case["anchor_date"])
        window_df = daily_df.loc[
            daily_df["site"].eq(site)
            & daily_df["panel_id"].eq(panel_id)
            & daily_df["date"].ge(anchor_ts - pd.Timedelta(days=WINDOW_DAYS))
            & daily_df["date"].lt(anchor_ts)
        ].copy()
        marker_hits = {
            "first_cond_evt": int(window_df["cond_evt"].eq(1).any()),
            "first_cond_evt_corroborated": int(window_df["cond_evt_corroborated_flag"].eq(1).any()),
            "first_signalcount2": int(window_df["signal_count"].ge(2).any()),
            "first_pre_ews": int(window_df["pre_ews"].eq(1).any()),
            "first_ews_warning": int(window_df["ews_warning"].eq(1).any()),
            "first_pre_alarm": int(window_df["pre_alarm"].eq(1).any()),
        }
        hits[(site, truth_case_id)] = marker_hits
    return hits


def build_step3_rows(root: Path, precursor_perf_df: pd.DataFrame, nonprec_df: pd.DataFrame) -> list[dict[str, object]]:
    precursor_perf_df = precursor_perf_df.copy()
    precursor_perf_df["site"] = precursor_perf_df["site"].map(normalize_text)
    precursor_perf_df["panel_id"] = precursor_perf_df["panel_id"].map(normalize_text)
    precursor_perf_df["fault_start_date"] = precursor_perf_df["fault_start_date"].map(normalize_date_text)
    precursor_perf_df["truth_case_id"] = (
        "precursor|"
        + precursor_perf_df["site"].astype(str)
        + "|"
        + precursor_perf_df["panel_id"].astype(str)
        + "|"
        + precursor_perf_df["fault_start_date"].astype(str)
    )
    precursor_perf_df = precursor_perf_df.drop_duplicates(subset=["truth_case_id"], keep="first")

    negative_cases = nonprec_df.loc[
        nonprec_df["eval_bucket_v2"].map(normalize_text).isin(["abrupt_or_no_precursor_now", "non_panel_or_common_cause"])
    ].copy()
    negative_cases["site"] = negative_cases["site"].map(normalize_text)
    negative_cases["truth_case_id"] = negative_cases["truth_case_id"].map(normalize_text)
    negative_cases = negative_cases.drop_duplicates(subset=["truth_case_id"], keep="first")

    negative_hits = build_step3_negative_hits(root, nonprec_df)
    rows: list[dict[str, object]] = []
    support_positive = int(len(precursor_perf_df))
    support_negative = int(len(negative_cases))
    for marker_name in STEP3_MARKERS:
        available_col = f"{marker_name}_available_flag"
        precursor_perf_df[available_col] = precursor_perf_df.get(available_col, 0).map(to_int_flag).astype(int)
        tp = int(precursor_perf_df[available_col].sum())
        fn = int(support_positive - tp)
        fp = 0
        for case in negative_cases.to_dict(orient="records"):
            fp += int(negative_hits.get((normalize_text(case["site"]), normalize_text(case["truth_case_id"])), {}).get(marker_name, 0))
        tn = int(support_negative - fp)
        recall, precision, f1 = compute_prf(tp, fp, fn)
        rows.append(
            {
                "eval_scope": "step3_precursor_performance",
                "eval_part_name": "precursor_bearing_marker_performance",
                "metric_kind": "true_case_metric",
                "unit_type": "case",
                "positive_set_name": "precursor_bearing_detectable_now",
                "negative_set_name": "abrupt_or_no_precursor_now + non_panel_or_common_cause",
                "target_name": marker_name,
                "support_positive": support_positive,
                "support_negative": support_negative,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
                "recall": recall,
                "precision": precision,
                "f1": f1,
                "note_ko": "positive는 audited event-semantics benchmark reset 이후 precursor benchmark 3건이고, negative는 pre-anchor 30일 window에서 같은 marker hit를 재구성해 계산한 true case metric이다. c42997a6-5881-47e7-9035-7de8a2673b54.1.1 은 precursor benchmark에 포함되고 pure abrupt benchmark에서는 제외된다. old precursor support 2 wording은 obsolete 다.",
            }
        )
    return rows


def first_flag_date(df: pd.DataFrame, flag_col: str) -> pd.Timestamp | pd.NaT:
    matched = df.loc[df[flag_col].eq(1)].sort_values("date")
    if matched.empty:
        return pd.NaT
    return pd.Timestamp(matched.iloc[0]["date"])


def evaluate_marker_window(marker_date: pd.Timestamp | pd.NaT, anchor_date: pd.Timestamp | pd.NaT) -> tuple[int, int, int]:
    if pd.isna(marker_date) or pd.isna(anchor_date):
        return (0, 0, 0)
    delta_days = int((pd.Timestamp(marker_date) - pd.Timestamp(anchor_date)).days)
    return (int(delta_days <= 0), int(1 <= delta_days <= 3), int(1 <= delta_days <= 7))


def build_precursor_abrupt_negative_hits(root: Path, precursor_perf_df: pd.DataFrame) -> pd.DataFrame:
    cases = precursor_perf_df.loc[:, ["site", "panel_id", "fault_start_date"]].copy()
    cases["site"] = cases["site"].map(normalize_text)
    cases["panel_id"] = cases["panel_id"].map(normalize_text)
    cases["fault_start_date"] = cases["fault_start_date"].map(normalize_date_text)
    cases = cases.drop_duplicates(subset=["site", "panel_id", "fault_start_date"], keep="first")
    if cases.empty:
        return pd.DataFrame(
            columns=[
                "site",
                "panel_id",
                "fault_start_date",
                "final_fault_hit_by_anchor_flag",
                "final_fault_hit_within_3d_after_flag",
                "final_fault_hit_within_7d_after_flag",
                "critical_fault_hit_within_7d_after_flag",
                "confirmed_fault_hit_within_7d_after_flag",
            ]
        )

    daily_df = load_daily_windows(root, cases.rename(columns={"fault_start_date": "anchor_date"}), anchor_col="anchor_date", lookback_days=ABRUPT_LOOKBACK_DAYS, lookahead_days=ABRUPT_LOOKAHEAD_DAYS)
    rows: list[dict[str, object]] = []
    for case in cases.to_dict(orient="records"):
        site = normalize_text(case["site"])
        panel_id = normalize_text(case["panel_id"])
        anchor_ts = parse_timestamp(case["fault_start_date"])
        window_df = daily_df.loc[
            daily_df["site"].eq(site)
            & daily_df["panel_id"].eq(panel_id)
            & daily_df["date"].ge(anchor_ts - pd.Timedelta(days=ABRUPT_LOOKBACK_DAYS))
            & daily_df["date"].le(anchor_ts + pd.Timedelta(days=ABRUPT_LOOKAHEAD_DAYS))
        ].copy()
        first_confirmed = first_flag_date(window_df, "confirmed_fault")
        first_critical = first_flag_date(window_df, "critical_fault")
        first_final = first_flag_date(window_df, "final_fault")
        _, _, confirmed_7 = evaluate_marker_window(first_confirmed, anchor_ts)
        _, _, critical_7 = evaluate_marker_window(first_critical, anchor_ts)
        final_by_anchor, final_3, final_7 = evaluate_marker_window(first_final, anchor_ts)
        rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "fault_start_date": normalize_text(case["fault_start_date"]),
                "final_fault_hit_by_anchor_flag": final_by_anchor,
                "final_fault_hit_within_3d_after_flag": final_3,
                "final_fault_hit_within_7d_after_flag": final_7,
                "critical_fault_hit_within_7d_after_flag": critical_7,
                "confirmed_fault_hit_within_7d_after_flag": confirmed_7,
            }
        )
    return pd.DataFrame(rows)


def build_pure_abrupt_positive_hits(
    root: Path,
    abrupt6_df: pd.DataFrame,
    pure_abrupt_expected: int,
) -> pd.DataFrame:
    cases = abrupt6_df.copy()
    cases["site"] = cases["site"].map(normalize_text)
    cases["panel_id"] = cases["panel_id"].map(normalize_text)
    cases["고장시점"] = cases["고장시점"].map(normalize_date_text)
    pure_mask = pd.to_numeric(cases["순수급작_flag"], errors="coerce").fillna(0).astype(int).eq(1)
    cases = cases.loc[pure_mask, ["site", "panel_id", "고장시점"]].drop_duplicates(subset=["site", "panel_id", "고장시점"], keep="first")
    if len(cases) != pure_abrupt_expected:
        raise SystemExit(
            f"pure abrupt symptom-map support must stay {pure_abrupt_expected}, found {len(cases)}"
        )
    if cases.empty:
        return pd.DataFrame(
            columns=[
                "site",
                "panel_id",
                "fault_start_date",
                "final_fault_hit_by_anchor_flag",
                "final_fault_hit_within_3d_after_flag",
                "final_fault_hit_within_7d_after_flag",
                "critical_fault_hit_within_7d_after_flag",
                "confirmed_fault_hit_within_7d_after_flag",
            ]
        )

    daily_df = load_daily_windows(
        root,
        cases.rename(columns={"고장시점": "anchor_date"}),
        anchor_col="anchor_date",
        lookback_days=ABRUPT_LOOKBACK_DAYS,
        lookahead_days=ABRUPT_LOOKAHEAD_DAYS,
    )
    rows: list[dict[str, object]] = []
    for case in cases.to_dict(orient="records"):
        site = normalize_text(case["site"])
        panel_id = normalize_text(case["panel_id"])
        anchor_ts = parse_timestamp(case["고장시점"])
        window_df = daily_df.loc[
            daily_df["site"].eq(site)
            & daily_df["panel_id"].eq(panel_id)
            & daily_df["date"].ge(anchor_ts - pd.Timedelta(days=ABRUPT_LOOKBACK_DAYS))
            & daily_df["date"].le(anchor_ts + pd.Timedelta(days=ABRUPT_LOOKAHEAD_DAYS))
        ].copy()
        first_confirmed = first_flag_date(window_df, "confirmed_fault")
        first_critical = first_flag_date(window_df, "critical_fault")
        first_final = first_flag_date(window_df, "final_fault")
        _, _, confirmed_7 = evaluate_marker_window(first_confirmed, anchor_ts)
        _, _, critical_7 = evaluate_marker_window(first_critical, anchor_ts)
        final_by_anchor, final_3, final_7 = evaluate_marker_window(first_final, anchor_ts)
        rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "fault_start_date": normalize_text(case["고장시점"]),
                "final_fault_hit_by_anchor_flag": final_by_anchor,
                "final_fault_hit_within_3d_after_flag": final_3,
                "final_fault_hit_within_7d_after_flag": final_7,
                "critical_fault_hit_within_7d_after_flag": critical_7,
                "confirmed_fault_hit_within_7d_after_flag": confirmed_7,
            }
        )
    return pd.DataFrame(rows)


def build_step4a_rows(
    root: Path,
    precursor_perf_df: pd.DataFrame,
    abrupt6_df: pd.DataFrame,
    nonprec_df: pd.DataFrame,
    fault_event_summary: dict[str, int],
) -> list[dict[str, object]]:
    nonprec_df = nonprec_df.copy()
    nonprec_df["eval_bucket_v2"] = nonprec_df["eval_bucket_v2"].map(normalize_text)
    nonpanel_df = nonprec_df.loc[nonprec_df["eval_bucket_v2"].eq("non_panel_or_common_cause")].drop_duplicates(subset=["truth_case_id"], keep="first").copy()
    abrupt_df = build_pure_abrupt_positive_hits(root, abrupt6_df, fault_event_summary["pure_abrupt_eval_count"])
    precursor_negative_df = build_precursor_abrupt_negative_hits(root, precursor_perf_df)

    support_positive = int(len(abrupt_df))
    if support_positive != fault_event_summary["pure_abrupt_eval_count"]:
        raise SystemExit(
            f"corrected pure abrupt positive support must be {fault_event_summary['pure_abrupt_eval_count']}, found {support_positive}"
        )
    support_negative = int(len(nonpanel_df) + len(precursor_negative_df))
    rows: list[dict[str, object]] = []
    col_map = {
        "final_fault_hit_by_anchor": "final_fault_hit_by_anchor_flag",
        "final_fault_hit_within_3d_after": "final_fault_hit_within_3d_after_flag",
        "final_fault_hit_within_7d_after": "final_fault_hit_within_7d_after_flag",
        "critical_fault_hit_within_7d_after": "critical_fault_hit_within_7d_after_flag",
        "confirmed_fault_hit_within_7d_after": "confirmed_fault_hit_within_7d_after_flag",
    }
    for target_name, col_name in col_map.items():
        abrupt_flags = abrupt_df.get(col_name, 0).map(to_int_flag).astype(int)
        nonpanel_flags = nonpanel_df.get(col_name, 0).map(to_int_flag).astype(int)
        precursor_flags = precursor_negative_df.get(col_name, 0).map(to_int_flag).astype(int)
        tp = int(abrupt_flags.sum())
        fn = int(support_positive - tp)
        fp = int(nonpanel_flags.sum() + precursor_flags.sum())
        tn = int(support_negative - fp)
        recall, precision, f1 = compute_prf(tp, fp, fn)
        rows.append(
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "eval_part_name": "abrupt_no_precursor_performance",
                "metric_kind": "true_case_metric",
                "unit_type": "case",
                "positive_set_name": "pure_abrupt_or_no_precursor_now",
                "negative_set_name": "precursor_bearing_detectable_now + non_panel_or_common_cause",
                "target_name": target_name,
                "support_positive": support_positive,
                "support_negative": support_negative,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
                "recall": recall,
                "precision": precision,
                "f1": f1,
                "note_ko": (
                    "pure abrupt/no-precursor true case에 대해 benchmark reset 이후 순수 급작 benchmark 3건만을 positive로 두고 anchor 전후 hard fault marker hit를 계산한 true case metric이다. "
                    f"사건 해석상 전조형 고장 패널은 {fault_event_summary['interpreted_precursor_count']}개이고, 순수 급작 benchmark support는 {fault_event_summary['pure_abrupt_eval_count']}개다. "
                    "c42997a6-5881-47e7-9035-7de8a2673b54.1.1 은 전조형 고장/급격 종료로 해석하며 precursor benchmark에는 포함되고 pure abrupt benchmark에서는 제외된다. old benchmark split wording은 obsolete 다."
                ),
            }
        )
    return rows


def build_step4b_rows(common_cause_df: pd.DataFrame) -> list[dict[str, object]]:
    common_cause_df = common_cause_df.copy()
    common_cause_df["eval_bucket_v2"] = common_cause_df["eval_bucket_v2"].map(normalize_text)
    positive_df = common_cause_df.loc[common_cause_df["eval_bucket_v2"].eq("non_panel_or_common_cause")].copy()
    negative_df = common_cause_df.loc[
        common_cause_df["eval_bucket_v2"].isin(["precursor_bearing_detectable_now", "abrupt_or_no_precursor_now"])
    ].copy()
    support_positive = int(len(positive_df))
    support_negative = int(len(negative_df))

    rows: list[dict[str, object]] = []
    col_map = {
        "current_marker_only": "current_marker_only_flag",
        "breadth_marker_only": "breadth_marker_only_flag",
        "combined_marker": "combined_marker_flag",
    }
    for target_name, col_name in col_map.items():
        positive_flags = positive_df.get(col_name, 0).map(to_int_flag).astype(int)
        negative_flags = negative_df.get(col_name, 0).map(to_int_flag).astype(int)
        tp = int(positive_flags.sum())
        fn = int(support_positive - tp)
        fp = int(negative_flags.sum())
        tn = int(support_negative - fp)
        recall, precision, f1 = compute_prf(tp, fp, fn)
        rows.append(
            {
                "eval_scope": "step4_common_cause_routing",
                "eval_part_name": "common_cause_routing_performance",
                "metric_kind": "true_case_metric",
                "unit_type": "case",
                "positive_set_name": "non_panel_or_common_cause",
                "negative_set_name": "precursor_bearing_detectable_now + abrupt_or_no_precursor_now",
                "target_name": target_name,
                "support_positive": support_positive,
                "support_negative": support_negative,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
                "recall": recall,
                "precision": precision,
                "f1": f1,
                "note_ko": "common-cause routing row는 non-panel/common-cause true case를 다른 case bucket과 구분하는 true case metric이다.",
            }
        )
    return rows


def normalize_baseline_policy(df: pd.DataFrame) -> pd.DataFrame:
    out = df.loc[:, ["attention_class", "site", "panel_id", "attention_any_future_fault_linked_ref_flag", "attention_any_future_truth_linked_ref_flag"]].copy()
    out["policy_name"] = "baseline_only"
    out["preview_attention_class"] = out["attention_class"].map(normalize_text)
    out["site"] = out["site"].map(normalize_text)
    out["panel_id"] = out["panel_id"].map(normalize_text)
    out["linked_ref_flag"] = out["attention_any_future_fault_linked_ref_flag"].map(to_int_flag).astype(int)
    out["truth_ref_flag"] = out["attention_any_future_truth_linked_ref_flag"].map(to_int_flag).astype(int)
    return out.loc[:, ["policy_name", "preview_attention_class", "site", "panel_id", "linked_ref_flag", "truth_ref_flag"]]


def normalize_panel_policy(df: pd.DataFrame, policy_name: str) -> pd.DataFrame:
    out = df.loc[:, ["preview_attention_class", "site", "panel_id", "attention_any_future_fault_linked_ref_flag", "attention_any_future_truth_linked_ref_flag"]].copy()
    out["policy_name"] = policy_name
    out["preview_attention_class"] = out["preview_attention_class"].map(normalize_text)
    out["site"] = out["site"].map(normalize_text)
    out["panel_id"] = out["panel_id"].map(normalize_text)
    out["linked_ref_flag"] = out["attention_any_future_fault_linked_ref_flag"].map(to_int_flag).astype(int)
    out["truth_ref_flag"] = out["attention_any_future_truth_linked_ref_flag"].map(to_int_flag).astype(int)
    return out.loc[:, ["policy_name", "preview_attention_class", "site", "panel_id", "linked_ref_flag", "truth_ref_flag"]]


def build_cluster_member_map(cluster_rollup_df: pd.DataFrame) -> dict[tuple[str, str], list[str]]:
    mapping: dict[tuple[str, str], list[str]] = {}
    for row in cluster_rollup_df.to_dict(orient="records"):
        site = normalize_text(row["site"])
        cluster_id = normalize_text(row["cluster_id"])
        panels = [item.strip() for item in normalize_text(row["panel_ids_csv"]).split(",") if item.strip()]
        mapping[(site, cluster_id)] = panels
    return mapping


def build_direct_panel_flag_lookup(panel_rows: pd.DataFrame) -> dict[tuple[str, str], tuple[int, int]]:
    if panel_rows.empty:
        return {}
    grouped = (
        panel_rows.groupby(["site", "panel_id"], as_index=False)[["linked_ref_flag", "truth_ref_flag"]]
        .max()
        .reset_index(drop=True)
    )
    return {
        (normalize_text(row["site"]), normalize_text(row["panel_id"])): (
            int(row["linked_ref_flag"]),
            int(row["truth_ref_flag"]),
        )
        for _, row in grouped.iterrows()
    }


def normalize_cluster_policy(
    df: pd.DataFrame,
    *,
    policy_name: str,
    cluster_member_map: dict[tuple[str, str], list[str]],
    direct_panel_flags: dict[tuple[str, str], tuple[int, int]],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for raw in df.to_dict(orient="records"):
        attention_class = normalize_text(raw["preview_attention_class"])
        site = normalize_text(raw["site"])
        entity_id = normalize_text(raw["display_entity_id"])
        row_linked = to_int_flag(raw.get("linked_ref_flag"))
        row_truth = to_int_flag(raw.get("truth_ref_flag"))
        if attention_class in {"queue_run", "watch_now_panel"}:
            rows.append(
                {
                    "policy_name": policy_name,
                    "preview_attention_class": attention_class,
                    "site": site,
                    "panel_id": entity_id,
                    "linked_ref_flag": row_linked,
                    "truth_ref_flag": row_truth,
                }
            )
            continue
        if attention_class != "secondary_value_cluster":
            continue
        cluster_members = cluster_member_map.get((site, entity_id))
        if not cluster_members:
            raise SystemExit(f"missing cluster members for {policy_name}: {(site, entity_id)}")
        for panel_id in cluster_members:
            linked_ref_flag, truth_ref_flag = direct_panel_flags.get((site, panel_id), (row_linked, row_truth))
            rows.append(
                {
                    "policy_name": policy_name,
                    "preview_attention_class": attention_class,
                    "site": site,
                    "panel_id": panel_id,
                    "linked_ref_flag": int(linked_ref_flag),
                    "truth_ref_flag": int(truth_ref_flag),
                }
            )
    return pd.DataFrame(rows, columns=["policy_name", "preview_attention_class", "site", "panel_id", "linked_ref_flag", "truth_ref_flag"])


def build_operator_rows(
    baseline_df: pd.DataFrame,
    panel_preview_df: pd.DataFrame,
    narrow_preview_df: pd.DataFrame,
    cluster_preview_df: pd.DataFrame,
    workflow_default_df: pd.DataFrame,
    cluster_rollup_df: pd.DataFrame,
) -> list[dict[str, object]]:
    baseline_rows = normalize_baseline_policy(baseline_df)
    panel_rows = normalize_panel_policy(panel_preview_df, "baseline_plus_discovery_panel")
    narrow_rows = normalize_panel_policy(narrow_preview_df, "baseline_plus_discovery_narrow")
    direct_rows = pd.concat([baseline_rows, panel_rows, narrow_rows], ignore_index=True)
    cluster_member_map = build_cluster_member_map(cluster_rollup_df)
    direct_flags = build_direct_panel_flag_lookup(direct_rows)
    cluster_rows = normalize_cluster_policy(
        cluster_preview_df,
        policy_name="baseline_plus_discovery_cluster",
        cluster_member_map=cluster_member_map,
        direct_panel_flags=direct_flags,
    )
    workflow_rows = normalize_cluster_policy(
        workflow_default_df,
        policy_name="workflow_default",
        cluster_member_map=cluster_member_map,
        direct_panel_flags=direct_flags,
    )

    policy_frames = [baseline_rows, panel_rows, narrow_rows, cluster_rows, workflow_rows]
    all_rows = pd.concat(policy_frames, ignore_index=True)
    if all_rows.empty:
        return []

    all_rows = (
        all_rows.groupby(["policy_name", "site", "panel_id"], as_index=False)[["linked_ref_flag", "truth_ref_flag"]]
        .max()
        .reset_index(drop=True)
    )
    universe_df = (
        all_rows.groupby(["site", "panel_id"], as_index=False)[["linked_ref_flag", "truth_ref_flag"]]
        .max()
        .reset_index(drop=True)
    )
    universe_keys = {(normalize_text(row["site"]), normalize_text(row["panel_id"])) for _, row in universe_df.iterrows()}
    positive_keys = {
        (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        for _, row in universe_df.iterrows()
        if int(row["linked_ref_flag"]) == 1 or int(row["truth_ref_flag"]) == 1
    }
    negative_keys = universe_keys - positive_keys

    rows: list[dict[str, object]] = []
    for policy_name in OPERATOR_POLICIES:
        selected_df = all_rows.loc[all_rows["policy_name"].eq(policy_name)].copy()
        selected_keys = {(normalize_text(row["site"]), normalize_text(row["panel_id"])) for _, row in selected_df.iterrows()}
        tp = int(len(selected_keys & positive_keys))
        fp = int(len(selected_keys & negative_keys))
        fn = int(len(positive_keys - selected_keys))
        tn = int(len(negative_keys - selected_keys))
        recall, precision, f1 = compute_prf(tp, fp, fn)
        rows.append(
            {
                "eval_scope": "operator_policy_proxy",
                "eval_part_name": "operator_workflow_policy_proxy",
                "metric_kind": "retrospective_proxy_metric",
                "unit_type": "panel",
                "positive_set_name": "proxy_linked_or_truth_panels",
                "negative_set_name": "proxy_non_linked_panels",
                "target_name": policy_name,
                "support_positive": int(len(positive_keys)),
                "support_negative": int(len(negative_keys)),
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
                "recall": recall,
                "precision": precision,
                "f1": f1,
                "note_ko": "operator policy row는 미래 fault/truth linkage를 panel-level proxy label로 사용한 retrospective proxy metric이며 prospective 운영 성능을 직접 뜻하지 않는다.",
            }
        )
    return rows


def build_summary_rows(matrix_df: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scope_notes = {
        "step1_taxonomy": "taxonomy support/coverage row라 best precision/recall/F1가 적용되지 않는다.",
        "step2_onset_truth": "onset coverage/availability row라 best precision/recall/F1가 적용되지 않는다.",
        "step3_precursor_performance": "benchmark reset 이후 precursor benchmark 3건을 positive로 둔 marker들 중 F1가 가장 높은 true case metric을 요약한다.",
        "step4_abrupt_no_precursor": "benchmark reset 이후 순수 급작 benchmark 3건만을 positive로 둔 target들 중 F1가 가장 높은 true case metric을 요약한다.",
        "step4_common_cause_routing": "common-cause routing marker들 중 F1가 가장 높은 true case metric을 요약한다.",
        "operator_policy_proxy": "operator policy는 retrospective proxy metric이라 workload/운영성 해석은 별도 audit와 함께 봐야 한다.",
    }
    for scope in [
        "step1_taxonomy",
        "step2_onset_truth",
        "step3_precursor_performance",
        "step4_abrupt_no_precursor",
        "step4_common_cause_routing",
        "operator_policy_proxy",
    ]:
        scope_df = matrix_df.loc[matrix_df["eval_scope"].eq(scope)].copy()
        scope_df["f1_numeric"] = pd.to_numeric(scope_df["f1"], errors="coerce")
        scope_df["recall_numeric"] = pd.to_numeric(scope_df["recall"], errors="coerce")
        scope_df["precision_numeric"] = pd.to_numeric(scope_df["precision"], errors="coerce")
        valid_df = scope_df.loc[scope_df["f1_numeric"].notna()].copy()
        if valid_df.empty:
            rows.append(
                {
                    "eval_scope": scope,
                    "best_target_name": "",
                    "best_f1": "",
                    "best_recall": "",
                    "best_precision": "",
                    "note_ko": scope_notes[scope],
                }
            )
            continue
        valid_df = valid_df.sort_values(
            ["f1_numeric", "recall_numeric", "precision_numeric", "target_name"],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)
        best = valid_df.iloc[0]
        rows.append(
            {
                "eval_scope": scope,
                "best_target_name": normalize_text(best["target_name"]),
                "best_f1": float(best["f1_numeric"]),
                "best_recall": float(best["recall_numeric"]),
                "best_precision": float(best["precision_numeric"]),
                "note_ko": scope_notes[scope],
            }
        )
    return rows


def build_notes_rows() -> list[dict[str, object]]:
    return [
        {
            "eval_scope": "step1_taxonomy",
            "why_prf_is_valid_or_not": "유효하지 않음. taxonomy bucket은 family support를 정리한 구조적 coverage 표이며 분류기의 positive/negative prediction이 아니다.",
            "caveat_ko": "family 수가 많다고 detector 성능이 높다는 뜻은 아니고, 현재 project가 어느 fault family까지 평가 bucket을 갖췄는지 보여주는 support row다.",
        },
        {
            "eval_scope": "step2_onset_truth",
            "why_prf_is_valid_or_not": "유효하지 않음. onset truth row는 marker availability와 lead coverage를 보는 reference coverage task이지 classifier yes/no task가 아니다.",
            "caveat_ko": "available_case_count가 높아도 onset date quality와 lead distribution은 별도로 읽어야 하며, precision/F1로 과장 해석하면 안 된다.",
        },
        {
            "eval_scope": "step3_precursor_performance",
            "why_prf_is_valid_or_not": "유효함. precursor-bearing true case를 positive로 두고 abrupt/common-cause case의 pre-anchor window를 negative로 재구성한 true case classifier metric이다.",
            "caveat_ko": "negative reconstruction window는 retrospective helper/core 재생성이므로 marker contamination 여부를 함께 해석해야 한다. benchmark reset 이후 precursor benchmark positive support는 3이며 c42997a6-5881-47e7-9035-7de8a2673b54.1.1 이 여기에 포함된다. old support 2 wording은 obsolete 다.",
        },
        {
            "eval_scope": "step4_abrupt_no_precursor",
            "why_prf_is_valid_or_not": "유효함. pure abrupt/no-precursor true case에서 hard fault marker hit를 계산하고 다른 case bucket을 negative로 둔 true case metric이다.",
            "caveat_ko": "event type과 terminal failure pattern은 다르다. benchmark reset 이후 precursor benchmark positive support는 3이고 pure abrupt benchmark positive support도 3이다. c42997a6-5881-47e7-9035-7de8a2673b54.1.1 은 전조형 고장/급격 종료로 해석하며 pure abrupt benchmark에서는 제외한다. old benchmark counts 는 obsolete 다.",
        },
        {
            "eval_scope": "step4_common_cause_routing",
            "why_prf_is_valid_or_not": "유효함. non-panel/common-cause true case를 positive로 두고 routing marker가 다른 bucket과 구분되는지를 본 true case metric이다.",
            "caveat_ko": "descriptive retrofit marker를 쓰므로 routing explanation력은 보이지만, 현장 action policy를 바로 결정하는 지표로 과장하면 안 된다.",
        },
        {
            "eval_scope": "operator_policy_proxy",
            "why_prf_is_valid_or_not": "부분적으로만 유효함. 미래 linkage/truth ref를 panel-level retrospective proxy label로 사용하므로 operator selection의 retrospective value proxy는 볼 수 있다.",
            "caveat_ko": "proxy metric은 실제 prospective operator workflow efficiency, load, review latency를 직접 측정하지 않으므로 별도 policy/load audit와 함께 읽어야 한다.",
        },
    ]


def build_matrix(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frames = load_required_inputs(root)
    fault_event_summary = load_fault_event_audit_summary(frames)
    matrix_rows: list[dict[str, object]] = []
    matrix_rows.extend(build_step1_rows(frames["taxonomy"]))
    matrix_rows.extend(build_step2_rows(frames["onset_truth"], frames["onset_summary"]))
    matrix_rows.extend(build_step3_rows(root, frames["precursor_perf"], frames["nonprec"]))
    matrix_rows.extend(
        build_step4a_rows(
            root,
            frames["precursor_perf"],
            frames["abrupt6"],
            frames["nonprec"],
            fault_event_summary,
        )
    )
    matrix_rows.extend(build_step4b_rows(frames["common_cause"]))
    matrix_rows.extend(
        build_operator_rows(
            frames["baseline_attention"],
            frames["panel_preview"],
            frames["narrow_preview"],
            frames["cluster_preview"],
            frames["workflow_default"],
            frames["cluster_rollup"],
        )
    )

    matrix_df = pd.DataFrame(matrix_rows, columns=MATRIX_COLS)
    summary_df = pd.DataFrame(build_summary_rows(matrix_df), columns=SUMMARY_COLS)
    notes_df = pd.DataFrame(build_notes_rows(), columns=NOTES_COLS)
    return matrix_df, summary_df, notes_df


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    matrix_df, summary_df, notes_df = build_matrix(root)
    matrix_df.to_csv(share_dir / MATRIX_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    notes_df.to_csv(share_dir / NOTES_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
