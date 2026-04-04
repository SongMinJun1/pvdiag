#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
V0_SCORES_NAME = "panel_day_engine_run_ranker_v0_scores.csv"
FATE_CASES_NAME = "panel_day_engine_local_seed_carry_fate_cases_v1.csv"
RUN_REGISTRY_OUTPUT_NAME = "panel_day_engine_operator_run_registry_v1.csv"
RUN_QUEUE_OUTPUT_NAME = "panel_day_engine_operator_run_queue_v1.csv"
RUN_BACKLOG_OUTPUT_NAME = "panel_day_engine_operator_run_backlog_v1.csv"
RUN_SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_run_summary_v1.csv"
RUN_WATCHLIST_OUTPUT_NAME = "panel_day_engine_operator_run_watchlist_v1.csv"
RUN_WATCHLIST_SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_run_watchlist_summary_v1.csv"
RUN_WATCHLIST_NOW_OUTPUT_NAME = "panel_day_engine_operator_run_watchlist_now_v1.csv"
RUN_WATCHLIST_REVIEW_OUTPUT_NAME = "panel_day_engine_operator_run_watchlist_review_v1.csv"
RUN_WATCHLIST_NOW_PANELS_OUTPUT_NAME = "panel_day_engine_operator_run_watchlist_now_panels_v1.csv"
RUN_WATCHLIST_NOW_PANELS_SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_run_watchlist_now_panels_summary_v1.csv"
RUN_ATTENTION_NOW_OUTPUT_NAME = "panel_day_engine_operator_attention_now_v1.csv"
RUN_ATTENTION_SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_attention_summary_v1.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
STRING_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "run_shape_class", "overlap_case_class", "fate_class", "cohort_hint"]
REQUIRED_FEATURE_COLS = [
    *KEY_COLS,
    "run_day_count",
    "run_shape_class",
    "overlap_case_class",
    "fate_class",
    "cohort_hint",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "recurring_run_within_60d",
    "future_fault_linked_flag",
    "future_truth_linked_flag",
]
REQUIRED_SCORE_COLS = [*KEY_COLS, "electrical_core_score", "electrical_core_minus_broadshape_050"]
OPTIONAL_FATE_COLS = [*KEY_COLS, "fate_class"]
RAW_OPERATOR_SCORE_COL = "raw_operator_score"
CLIPPED_OPERATOR_SCORE_COL = "clipped_operator_score"
RAW_RANK_COL = "raw_rank_within_site"
CLIPPED_RANK_COL = "clipped_rank_within_site"
RANK_SHIFT_ABS_COL = "rank_shift_abs"
SCORE_HYGIENE_FLAG_COL = "score_hygiene_flag"
SCORE_HYGIENE_REASON_COL = "score_hygiene_reason_ko"
EPSILON = 1e-9
TOP_K_VALUES = [20, 50, 100]
CLIP_INPUT_COLS = [
    "core_vdrop_input",
    "core_midv_input",
    "core_mid_input",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
]
SUSPICIOUS_COLS = [*CLIP_INPUT_COLS, "electrical_core_score", RAW_OPERATOR_SCORE_COL]
STATUS_PRIORITY = {
    "ongoing_run": 0,
    "new_run": 1,
    "recurring_run": 2,
    "recovered_run": 3,
    "historical_run": 4,
}
PRIORITY_PRIORITY = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
ACTION_BUCKET_PRIORITY = {
    "investigate_now": 0,
    "monitor_active": 1,
    "recurring_backlog": 2,
    "recovered_backlog": 3,
    "historical_archive": 4,
}
WATCHLIST_BUCKET_PRIORITY = {
    "recurring_watch_p1": 0,
    "recurring_watch_p2": 1,
    "none": 2,
}
REGISTRY_OUTPUT_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "cohort_hint",
    "fate_class",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
    RAW_OPERATOR_SCORE_COL,
    CLIPPED_OPERATOR_SCORE_COL,
    RAW_RANK_COL,
    CLIPPED_RANK_COL,
    RANK_SHIFT_ABS_COL,
    SCORE_HYGIENE_FLAG_COL,
    SCORE_HYGIENE_REASON_COL,
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "status",
    "priority_band",
    "action_bucket",
    "queue_eligible_flag",
    "backlog_flag",
    "watchlist_flag",
    "watchlist_bucket",
    "watchlist_reason_ko",
    "watchlist_tier",
    "watch_now_flag",
    "watch_review_flag",
    "watchlist_tier_reason_ko",
    "queue_reason_ko",
    "overlap_case_class",
    "future_fault_linked_flag",
    "future_truth_linked_flag",
]
SUMMARY_OUTPUT_COLS = [
    "record_type",
    "site",
    "total_runs",
    "ongoing_run_count",
    "new_run_count",
    "recurring_run_count",
    "recovered_run_count",
    "chronic_run_count",
    "p1_run_count",
    "p2_run_count",
    "investigate_now_count",
    "monitor_active_count",
    "recurring_backlog_count",
    "recovered_backlog_count",
    "historical_archive_count",
    "queue_count",
    "backlog_count",
    "queue_chronic_count",
    "backlog_chronic_count",
    "queue_future_fault_linked_count",
    "queue_future_truth_linked_count",
    "clipped_top20_overlap_vs_raw",
    "clipped_top50_overlap_vs_raw",
    "clipped_top100_overlap_vs_raw",
    "score_hygiene_flag_count",
    "score_hygiene_queue_count",
    "score_hygiene_backlog_count",
    "watchlist_count",
    "watchlist_p1_count",
    "watchlist_p2_count",
    "watchlist_chronic_count",
    "watch_now_count",
    "watch_review_count",
]
WATCHLIST_OUTPUT_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "status",
    "priority_band",
    "action_bucket",
    "overlap_case_class",
    RAW_OPERATOR_SCORE_COL,
    CLIPPED_OPERATOR_SCORE_COL,
    RAW_RANK_COL,
    CLIPPED_RANK_COL,
    SCORE_HYGIENE_FLAG_COL,
    SCORE_HYGIENE_REASON_COL,
    "future_fault_linked_flag",
    "future_truth_linked_flag",
    "watchlist_bucket",
    "watchlist_tier",
    "watchlist_reason_ko",
    "watchlist_tier_reason_ko",
]
WATCHLIST_SUMMARY_OUTPUT_COLS = [
    "record_type",
    "site",
    "watchlist_count",
    "watchlist_p1_count",
    "watchlist_p2_count",
    "watch_now_count",
    "watch_review_count",
    "watch_now_panel_count",
    "panels_with_multiple_watch_now_runs",
    "median_watch_now_runs_per_panel",
    "watchlist_chronic_count",
    "watchlist_unmatched_to_review_count",
    "watchlist_eligible_local_overlap_count",
    "watchlist_nuisance_overlap_count",
    "watchlist_future_fault_linked_count",
    "watchlist_future_truth_linked_count",
    "watch_now_future_fault_linked_count",
    "watch_now_future_truth_linked_count",
    "watch_review_future_fault_linked_count",
    "watch_review_future_truth_linked_count",
]
WATCH_NOW_PANEL_OUTPUT_COLS = [
    "site",
    "panel_id",
    "representative_run_start_date",
    "representative_run_end_date",
    "representative_run_day_count",
    "representative_run_shape_class",
    "representative_status",
    "representative_priority_band",
    "representative_action_bucket",
    "representative_overlap_case_class",
    "representative_raw_operator_score",
    "representative_clipped_operator_score",
    "representative_raw_rank_within_site",
    "representative_clipped_rank_within_site",
    "representative_score_hygiene_flag",
    "representative_score_hygiene_reason_ko",
    "watch_now_run_count_for_panel",
    "watch_now_total_day_count_for_panel",
    "earliest_watch_now_run_start_date",
    "latest_watch_now_run_end_date",
    "max_clipped_operator_score_for_panel",
    "any_future_fault_linked_flag_ref",
    "any_future_truth_linked_flag_ref",
    "overlap_case_class_set",
    "panel_rollup_reason_ko",
]
WATCH_NOW_PANEL_SUMMARY_OUTPUT_COLS = [
    "record_type",
    "site",
    "watch_now_panel_count",
    "watch_now_run_count",
    "panels_with_multiple_watch_now_runs",
    "median_watch_now_runs_per_panel",
    "max_watch_now_runs_per_panel",
    "panels_with_future_fault_linked_ref_count",
    "panels_with_future_truth_linked_ref_count",
]
ATTENTION_CLASS_PRIORITY = {"queue_run": 0, "watch_now_panel": 1}
ATTENTION_OUTPUT_COLS = [
    "attention_class",
    "site",
    "panel_id",
    "display_start_date",
    "display_end_date",
    "display_day_count",
    "display_shape_class",
    "display_status_or_tier",
    "priority_band",
    CLIPPED_OPERATOR_SCORE_COL,
    RAW_OPERATOR_SCORE_COL,
    "overlap_case_class",
    "action_bucket",
    "watchlist_bucket",
    SCORE_HYGIENE_FLAG_COL,
    SCORE_HYGIENE_REASON_COL,
    "future_fault_linked_flag_ref",
    "future_truth_linked_flag_ref",
    "panel_has_watch_now_overlap_flag",
    "panel_watch_now_run_count",
    "panel_watch_now_total_day_count",
    "panel_watch_now_earliest_start_date",
    "panel_watch_now_latest_end_date",
    "panel_any_future_fault_linked_ref",
    "panel_any_future_truth_linked_ref",
    "panel_overlap_case_class_set",
    "panel_rollup_reason_ko",
    "attention_any_future_fault_linked_ref_flag",
    "attention_any_future_truth_linked_ref_flag",
    "attention_merge_reason_ko",
    "attention_reason_ko",
]
ATTENTION_SUMMARY_OUTPUT_COLS = [
    "record_type",
    "site",
    "attention_count",
    "queue_run_attention_count",
    "watch_now_panel_attention_count",
    "deduped_panel_overlap_count",
    "deduped_overlap_future_fault_linked_ref_count",
    "deduped_overlap_future_truth_linked_ref_count",
    "attention_future_fault_linked_ref_count",
    "attention_future_truth_linked_ref_count",
    "attention_any_future_fault_linked_ref_count",
    "attention_any_future_truth_linked_ref_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build operator-facing consolidated run artifacts from panel_day_engine run tables."
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
    if text.lower() == "nan":
        return ""
    return text


def normalize_date(value: object) -> str:
    text = normalize_text(value)
    return text[:10] if len(text) >= 10 else text


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


def robust_scale(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.dropna().empty:
        return pd.Series(0.0, index=series.index)
    median = float(numeric.median())
    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    iqr = q3 - q1
    denom = iqr if abs(iqr) > EPSILON else 1.0
    return ((numeric.fillna(median) - median) / denom).clip(-5.0, 5.0)


def compute_stats(series: pd.Series) -> dict[str, float | None]:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return {"median": None, "iqr": None, "p99": None, "p99_5": None}
    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    return {
        "median": float(numeric.median()),
        "iqr": float(q3 - q1),
        "p99": float(numeric.quantile(0.99)),
        "p99_5": float(numeric.quantile(0.995)),
    }


def rank_frame(df: pd.DataFrame, score_col: str) -> pd.DataFrame:
    ranked = df.sort_values(
        [score_col, "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[False, False, True, True, True, True],
        kind="mergesort",
    ).copy()
    ranked["rank"] = range(1, len(ranked) + 1)
    return ranked.loc[:, [*KEY_COLS, "rank"]]


def add_rank_within_site(df: pd.DataFrame, score_col: str, rank_col: str) -> pd.DataFrame:
    ranked_parts: list[pd.DataFrame] = []
    for site, site_df in df.groupby("site", sort=True, dropna=False):
        ranked_site = site_df.sort_values(
            [score_col, "run_day_count", "panel_id", "run_start_date", "run_end_date"],
            ascending=[False, False, True, True, True],
            kind="mergesort",
        ).copy()
        ranked_site[rank_col] = range(1, len(ranked_site) + 1)
        ranked_parts.append(ranked_site.loc[:, [*KEY_COLS, rank_col]])
    ranks = pd.concat(ranked_parts, axis=0) if ranked_parts else pd.DataFrame(columns=[*KEY_COLS, rank_col])
    return df.merge(ranks, on=KEY_COLS, how="left", validate="one_to_one")


def dominant_reason(feature_name: str) -> str:
    mapping = {
        "p95_recon_error": "p95_recon_error 영향 큼",
        "core_mid_input": "min_mid_ratio 영향 큼",
        "core_midv_input": "min_mid_v_ratio 영향 큼",
        "core_vdrop_input": "max_v_drop 영향 큼",
        "mean_signal_count": "signal_count 영향 큼",
        "max_signal_count": "signal_count 영향 큼",
        "ae_mid_or_hi_early_day_ratio": "broadshape 영향 큼",
        "electrical_core_score": "raw score extreme",
        RAW_OPERATOR_SCORE_COL: "raw score extreme",
    }
    return mapping.get(feature_name, "clipping 영향 적음")


def load_feature_table(root: Path) -> pd.DataFrame:
    path = root / "_share" / FEATURE_TABLE_NAME
    df = read_csv(path)
    ensure_columns(df, REQUIRED_FEATURE_COLS, path.name)
    df = drop_repeated_header_rows(df).copy()
    for col in STRING_COLS:
        normalizer = normalize_date if col in {"run_start_date", "run_end_date"} else normalize_text
        df[col] = df[col].map(normalizer)
    for col in REQUIRED_FEATURE_COLS:
        if col in STRING_COLS:
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.loc[:, REQUIRED_FEATURE_COLS].copy()
    return df.drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_v0_scores(root: Path) -> pd.DataFrame:
    path = root / "_share" / V0_SCORES_NAME
    df = read_csv(path)
    ensure_columns(df, REQUIRED_SCORE_COLS, path.name)
    df = drop_repeated_header_rows(df).copy()
    for col in KEY_COLS:
        normalizer = normalize_date if col in {"run_start_date", "run_end_date"} else normalize_text
        df[col] = df[col].map(normalizer)
    for col in ["electrical_core_score", "electrical_core_minus_broadshape_050"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.loc[:, REQUIRED_SCORE_COLS].copy()
    return df.drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_optional_fate_cases(root: Path) -> pd.DataFrame:
    path = root / "_share" / FATE_CASES_NAME
    if not path.exists():
        return pd.DataFrame(columns=OPTIONAL_FATE_COLS)
    df = read_csv(path)
    ensure_columns(df, OPTIONAL_FATE_COLS, path.name)
    df = drop_repeated_header_rows(df).copy()
    for col in KEY_COLS:
        normalizer = normalize_date if col in {"run_start_date", "run_end_date"} else normalize_text
        df[col] = df[col].map(normalizer)
    df["fate_class"] = df["fate_class"].map(normalize_text)
    df = df.loc[:, OPTIONAL_FATE_COLS].copy()
    return df.drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def add_operator_score_fields(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out[RAW_OPERATOR_SCORE_COL] = pd.to_numeric(out["electrical_core_minus_broadshape_050"], errors="coerce")
    out["core_vdrop_input"] = pd.to_numeric(out["max_v_drop"], errors="coerce")
    out["core_midv_input"] = 1.0 - pd.to_numeric(out["min_mid_v_ratio"], errors="coerce")
    out["core_mid_input"] = 1.0 - pd.to_numeric(out["min_mid_ratio"], errors="coerce")

    site_clip_map: dict[tuple[str, str], float | None] = {}
    suspicious_stats: dict[tuple[str, str], dict[str, float | None]] = {}
    for site, site_df in out.groupby("site", sort=True, dropna=False):
        for col in CLIP_INPUT_COLS:
            site_clip_map[(site, col)] = compute_stats(site_df[col])["p99"]
        for col in SUSPICIOUS_COLS:
            suspicious_stats[(site, col)] = compute_stats(site_df[col])

    changed_features: list[str] = []
    suspicious_flags: list[bool] = []
    suspicious_reasons: list[str] = []
    for idx, row in out.iterrows():
        site = row["site"]
        local_changes: dict[str, float] = {}
        suspicious_hits: list[str] = []
        for col in CLIP_INPUT_COLS:
            threshold = site_clip_map.get((site, col))
            value = pd.to_numeric(row[col], errors="coerce")
            clipped_col = f"{col}_clipped"
            out.at[idx, clipped_col] = value
            if pd.notna(value) and threshold is not None and pd.notna(threshold) and value > float(threshold):
                out.at[idx, clipped_col] = float(threshold)
                local_changes[col] = float(value) - float(threshold)

        for col in SUSPICIOUS_COLS:
            stats = suspicious_stats.get((site, col), {})
            value = pd.to_numeric(row[col], errors="coerce")
            if pd.isna(value):
                continue
            p99_5 = stats.get("p99_5")
            if p99_5 is not None and pd.notna(p99_5) and float(value) > float(p99_5):
                suspicious_hits.append(col)
                continue
            median = stats.get("median")
            iqr = stats.get("iqr")
            if median is None or iqr is None or pd.isna(median):
                continue
            denom = float(iqr) if abs(float(iqr)) > EPSILON else EPSILON
            if (float(value) - float(median)) / denom > 8.0:
                suspicious_hits.append(col)

        if local_changes:
            dominant_feature = max(local_changes, key=local_changes.get)
        elif suspicious_hits:
            dominant_feature = suspicious_hits[0]
        else:
            dominant_feature = ""
        changed_features.append(dominant_feature)
        suspicious_flags.append(bool(suspicious_hits))
        suspicious_reasons.append(dominant_reason(dominant_feature))

    out["clipped_core_vdrop_term"] = robust_scale(out["core_vdrop_input_clipped"])
    out["clipped_core_midv_term"] = robust_scale(out["core_midv_input_clipped"])
    out["clipped_core_mid_term"] = robust_scale(out["core_mid_input_clipped"])
    out["clipped_broadshape_ae_term"] = robust_scale(out["ae_mid_or_hi_early_day_ratio_clipped"])
    out["clipped_broadshape_mean_signal_term"] = robust_scale(out["mean_signal_count_clipped"])
    out["clipped_broadshape_max_signal_term"] = robust_scale(out["max_signal_count_clipped"])
    out["clipped_broadshape_recon_term"] = robust_scale(out["p95_recon_error_clipped"])
    out[CLIPPED_OPERATOR_SCORE_COL] = (
        out["clipped_core_vdrop_term"]
        + out["clipped_core_midv_term"]
        + out["clipped_core_mid_term"]
        - 0.50
        * (
            out["clipped_broadshape_ae_term"]
            + out["clipped_broadshape_mean_signal_term"]
            + out["clipped_broadshape_max_signal_term"]
            + out["clipped_broadshape_recon_term"]
        )
    )

    out = add_rank_within_site(out, RAW_OPERATOR_SCORE_COL, RAW_RANK_COL)
    out = add_rank_within_site(out, CLIPPED_OPERATOR_SCORE_COL, CLIPPED_RANK_COL)
    out[RANK_SHIFT_ABS_COL] = (
        pd.to_numeric(out[CLIPPED_RANK_COL], errors="coerce") - pd.to_numeric(out[RAW_RANK_COL], errors="coerce")
    ).abs().fillna(0).astype(int)
    out[SCORE_HYGIENE_FLAG_COL] = (
        out[RANK_SHIFT_ABS_COL].ge(20) | pd.Series(suspicious_flags, index=out.index)
    ).astype(int)
    out[SCORE_HYGIENE_REASON_COL] = pd.Series(suspicious_reasons, index=out.index)
    out.loc[out[SCORE_HYGIENE_FLAG_COL].eq(0), SCORE_HYGIENE_REASON_COL] = "clipping 영향 적음"
    return out


def compute_overlap_rates(scope_df: pd.DataFrame) -> dict[str, float | None]:
    if scope_df.empty:
        return {f"top{k}": None for k in TOP_K_VALUES}
    raw_ranks = rank_frame(scope_df, RAW_OPERATOR_SCORE_COL).rename(columns={"rank": "raw_rank"})
    clipped_ranks = rank_frame(scope_df, CLIPPED_OPERATOR_SCORE_COL).rename(columns={"rank": "clipped_rank"})
    ranked = scope_df.merge(raw_ranks, on=KEY_COLS, how="left", validate="one_to_one")
    ranked = ranked.merge(clipped_ranks, on=KEY_COLS, how="left", validate="one_to_one")
    overlaps: dict[str, float | None] = {}
    for top_k in TOP_K_VALUES:
        denom = min(top_k, len(ranked))
        if denom == 0:
            overlaps[f"top{top_k}"] = None
            continue
        raw_top = set(tuple(row) for row in ranked.loc[ranked["raw_rank"].le(denom), KEY_COLS].itertuples(index=False, name=None))
        clipped_top = set(tuple(row) for row in ranked.loc[ranked["clipped_rank"].le(denom), KEY_COLS].itertuples(index=False, name=None))
        overlaps[f"top{top_k}"] = len(raw_top & clipped_top) / float(denom)
    return overlaps


def assign_site_priority_bands(site_df: pd.DataFrame) -> pd.DataFrame:
    ordered = site_df.sort_values(
        [RAW_RANK_COL, "run_day_count", "panel_id", "run_start_date", "run_end_date"],
        ascending=[True, False, True, True, True],
        kind="mergesort",
    ).copy()
    n_rows = len(ordered)
    p1_cut = max(1, math.ceil(n_rows * 0.05))
    p2_cut = max(p1_cut, math.ceil(n_rows * 0.20))
    p3_cut = max(p2_cut, math.ceil(n_rows * 0.50))
    ordered["site_score_rank"] = pd.to_numeric(ordered[RAW_RANK_COL], errors="coerce")
    if ordered["site_score_rank"].isna().any():
        ordered["site_score_rank"] = range(1, n_rows + 1)
    ordered["priority_band"] = "P4"
    ordered.loc[ordered["site_score_rank"] <= p3_cut, "priority_band"] = "P3"
    ordered.loc[ordered["site_score_rank"] <= p2_cut, "priority_band"] = "P2"
    ordered.loc[ordered["site_score_rank"] <= p1_cut, "priority_band"] = "P1"
    return ordered


def assign_status(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["run_start_dt"] = pd.to_datetime(out["run_start_date"], errors="coerce")
    out["run_end_dt"] = pd.to_datetime(out["run_end_date"], errors="coerce")
    out["site_max_run_end_dt"] = out.groupby("site", dropna=False)["run_end_dt"].transform("max")

    start_delta = (out["site_max_run_end_dt"] - out["run_start_dt"]).dt.days
    end_delta = (out["site_max_run_end_dt"] - out["run_end_dt"]).dt.days

    ongoing = end_delta.between(0, 1, inclusive="both")
    new_run = start_delta.between(0, 3, inclusive="both")
    recurring = pd.to_numeric(out["recurring_run_within_60d"], errors="coerce").fillna(0).astype(int).eq(1)
    recovered = (~ongoing) & end_delta.between(0, 7, inclusive="both")

    status = pd.Series("historical_run", index=out.index)
    status.loc[recovered] = "recovered_run"
    status.loc[recurring] = "recurring_run"
    status.loc[new_run] = "new_run"
    status.loc[ongoing] = "ongoing_run"
    out["status"] = status
    return out


def assign_action_buckets(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    ongoing_or_new = out["status"].isin({"ongoing_run", "new_run"})
    investigate_now = ongoing_or_new & out["priority_band"].isin({"P1", "P2"})
    monitor_active = (
        ongoing_or_new
        & out["priority_band"].eq("P3")
        & out["run_shape_class"].isin({"medium_alert_run", "chronic_alert_run"})
    )
    recurring_backlog = out["status"].eq("recurring_run")
    recovered_backlog = out["status"].eq("recovered_run")

    action_bucket = pd.Series("historical_archive", index=out.index)
    action_bucket.loc[recovered_backlog] = "recovered_backlog"
    action_bucket.loc[recurring_backlog] = "recurring_backlog"
    action_bucket.loc[monitor_active] = "monitor_active"
    action_bucket.loc[investigate_now] = "investigate_now"
    out["action_bucket"] = action_bucket

    out["queue_eligible_flag"] = out["action_bucket"].isin({"investigate_now", "monitor_active"}).astype(int)
    out["backlog_flag"] = out["action_bucket"].isin({"recurring_backlog", "recovered_backlog"}).astype(int)

    reason = pd.Series("과거 archive", index=out.index)
    reason.loc[out["action_bucket"].eq("recovered_backlog")] = "최근 종료 backlog"
    reason.loc[out["action_bucket"].eq("recurring_backlog")] = "반복 chronic backlog"
    reason.loc[out["action_bucket"].eq("monitor_active")] = "진행중이며 중간 우선순위 chronic"
    reason.loc[out["action_bucket"].eq("investigate_now")] = "신규/진행중이며 상위 우선순위"
    out["queue_reason_ko"] = reason
    return out


def assign_watchlist(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    recurring_chronic_backlog = (
        out["backlog_flag"].eq(1)
        & out["status"].eq("recurring_run")
        & out["run_shape_class"].eq("chronic_alert_run")
        & out["overlap_case_class"].ne("nuisance_overlap")
    )
    watch_p1 = recurring_chronic_backlog & out["priority_band"].eq("P1")
    watch_p2 = recurring_chronic_backlog & out["priority_band"].eq("P2")

    bucket = pd.Series("none", index=out.index)
    bucket.loc[watch_p2] = "recurring_watch_p2"
    bucket.loc[watch_p1] = "recurring_watch_p1"
    out["watchlist_bucket"] = bucket
    out["watchlist_flag"] = out["watchlist_bucket"].ne("none").astype(int)

    reason = pd.Series("watchlist 제외", index=out.index)
    reason.loc[out["watchlist_bucket"].eq("recurring_watch_p2")] = "반복 chronic 중간 우선순위"
    reason.loc[out["watchlist_bucket"].eq("recurring_watch_p1")] = "반복 chronic 상위 우선순위"
    out["watchlist_reason_ko"] = reason
    return out


def assign_watchlist_tiers(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    tier = pd.Series("none", index=out.index)
    tier.loc[out["watchlist_bucket"].eq("recurring_watch_p2")] = "watch_review"
    tier.loc[out["watchlist_bucket"].eq("recurring_watch_p1")] = "watch_now"
    out["watchlist_tier"] = tier
    out["watch_now_flag"] = out["watchlist_tier"].eq("watch_now").astype(int)
    out["watch_review_flag"] = out["watchlist_tier"].eq("watch_review").astype(int)

    reason = pd.Series("watchlist tier 제외", index=out.index)
    reason.loc[out["watchlist_tier"].eq("watch_review")] = "검토용 반복 chronic"
    reason.loc[out["watchlist_tier"].eq("watch_now")] = "즉시 주시할 상위 반복 chronic"
    out["watchlist_tier_reason_ko"] = reason
    return out


def build_registry(root: Path) -> pd.DataFrame:
    feature_df = load_feature_table(root)
    v0_scores = load_v0_scores(root)
    fate_df = load_optional_fate_cases(root).rename(columns={"fate_class": "fate_class_fate"})

    merged = feature_df.merge(v0_scores, on=KEY_COLS, how="left", validate="one_to_one")
    if not fate_df.empty:
        merged = merged.merge(fate_df, on=KEY_COLS, how="left", validate="one_to_one")
        merged["fate_class"] = merged["fate_class"].map(normalize_text)
        merged["fate_class_fate"] = merged["fate_class_fate"].map(normalize_text)
        merged["fate_class"] = merged["fate_class"].where(merged["fate_class"].ne(""), merged["fate_class_fate"])
        merged = merged.drop(columns=["fate_class_fate"])
    else:
        merged["fate_class"] = merged["fate_class"].map(normalize_text)

    if merged["electrical_core_minus_broadshape_050"].isna().any():
        raise SystemExit("missing electrical_core_minus_broadshape_050 after merge")
    if merged["electrical_core_score"].isna().any():
        raise SystemExit("missing electrical_core_score after merge")

    merged["future_fault_linked_flag"] = pd.to_numeric(merged["future_fault_linked_flag"], errors="coerce").fillna(0).astype(int)
    merged["future_truth_linked_flag"] = pd.to_numeric(merged["future_truth_linked_flag"], errors="coerce").fillna(0).astype(int)

    merged = add_operator_score_fields(merged)
    merged = assign_status(merged)

    banded_parts = []
    for _, site_df in merged.groupby("site", sort=True, dropna=False):
        banded_parts.append(assign_site_priority_bands(site_df))
    registry = pd.concat(banded_parts, axis=0).sort_index()
    registry = assign_action_buckets(registry)
    registry = assign_watchlist(registry)
    registry = assign_watchlist_tiers(registry)
    registry = registry.sort_values(
        ["site", RAW_RANK_COL, "run_day_count", "panel_id", "run_start_date", "run_end_date"],
        ascending=[True, True, False, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    return registry


def build_queue(registry: pd.DataFrame) -> pd.DataFrame:
    queue = registry.loc[registry["queue_eligible_flag"].eq(1)].copy()
    queue["_action_order"] = queue["action_bucket"].map(ACTION_BUCKET_PRIORITY).fillna(99)
    queue["_priority_order"] = queue["priority_band"].map(PRIORITY_PRIORITY).fillna(99)
    queue = queue.sort_values(
        [
            "_action_order",
            "_priority_order",
            CLIPPED_OPERATOR_SCORE_COL,
            "run_day_count",
            "site",
            "panel_id",
            "run_start_date",
        ],
        ascending=[True, True, False, False, True, True, True],
        kind="mergesort",
    ).drop(columns=["_action_order", "_priority_order"])
    return queue.reset_index(drop=True)


def build_backlog(registry: pd.DataFrame) -> pd.DataFrame:
    backlog = registry.loc[registry["backlog_flag"].eq(1)].copy()
    backlog["_action_order"] = backlog["action_bucket"].map(ACTION_BUCKET_PRIORITY).fillna(99)
    backlog = backlog.sort_values(
        [
            "_action_order",
            CLIPPED_OPERATOR_SCORE_COL,
            "run_day_count",
            "site",
            "panel_id",
            "run_start_date",
        ],
        ascending=[True, False, False, True, True, True],
        kind="mergesort",
    ).drop(columns=["_action_order"])
    return backlog.reset_index(drop=True)


def build_watchlist(registry: pd.DataFrame) -> pd.DataFrame:
    watchlist = registry.loc[registry["watchlist_flag"].eq(1)].copy()
    watchlist["_bucket_order"] = watchlist["watchlist_bucket"].map(WATCHLIST_BUCKET_PRIORITY).fillna(99)
    watchlist = watchlist.sort_values(
        [
            "_bucket_order",
            CLIPPED_OPERATOR_SCORE_COL,
            "run_day_count",
            "site",
            "panel_id",
            "run_start_date",
        ],
        ascending=[True, False, False, True, True, True],
        kind="mergesort",
    ).drop(columns=["_bucket_order"])
    return watchlist.reset_index(drop=True)


def build_watchlist_tier(registry: pd.DataFrame, tier: str) -> pd.DataFrame:
    watchlist_tier = registry.loc[registry["watchlist_tier"].eq(tier)].copy()
    watchlist_tier = watchlist_tier.sort_values(
        [
            CLIPPED_OPERATOR_SCORE_COL,
            "run_day_count",
            "site",
            "panel_id",
            "run_start_date",
        ],
        ascending=[False, False, True, True, True],
        kind="mergesort",
    )
    return watchlist_tier.reset_index(drop=True)


def choose_watch_now_representative(panel_df: pd.DataFrame) -> pd.Series:
    ranked = panel_df.copy()
    ranked["_run_end_dt"] = pd.to_datetime(ranked["run_end_date"], errors="coerce")
    ranked["_run_start_dt"] = pd.to_datetime(ranked["run_start_date"], errors="coerce")
    ranked = ranked.sort_values(
        [
            CLIPPED_OPERATOR_SCORE_COL,
            "_run_end_dt",
            "run_day_count",
            "_run_start_dt",
            "panel_id",
        ],
        ascending=[False, False, False, True, True],
        kind="mergesort",
    )
    return ranked.iloc[0]


def summarize_overlap_case_classes(panel_df: pd.DataFrame) -> str:
    values = [normalize_text(value) for value in panel_df["overlap_case_class"].tolist()]
    unique_values = sorted({value for value in values if value})
    return "|".join(unique_values)


def build_watch_now_panel_rollup(watch_now: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (site, panel_id), panel_df in watch_now.groupby(["site", "panel_id"], sort=True, dropna=False):
        representative = choose_watch_now_representative(panel_df)
        any_future_fault = int(panel_df["future_fault_linked_flag"].eq(1).any())
        any_future_truth = int(panel_df["future_truth_linked_flag"].eq(1).any())
        run_count = int(len(panel_df))
        if any_future_fault or any_future_truth:
            reason = "future linkage reference 있음"
        elif run_count > 1:
            reason = "반복 run 다수, 대표 run만 표시"
        else:
            reason = "단일 run panel"
        rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "representative_run_start_date": representative["run_start_date"],
                "representative_run_end_date": representative["run_end_date"],
                "representative_run_day_count": int(pd.to_numeric(representative["run_day_count"], errors="coerce")),
                "representative_run_shape_class": representative["run_shape_class"],
                "representative_status": representative["status"],
                "representative_priority_band": representative["priority_band"],
                "representative_action_bucket": representative["action_bucket"],
                "representative_overlap_case_class": representative["overlap_case_class"],
                "representative_raw_operator_score": float(pd.to_numeric(representative[RAW_OPERATOR_SCORE_COL], errors="coerce")),
                "representative_clipped_operator_score": float(pd.to_numeric(representative[CLIPPED_OPERATOR_SCORE_COL], errors="coerce")),
                "representative_raw_rank_within_site": int(pd.to_numeric(representative[RAW_RANK_COL], errors="coerce")),
                "representative_clipped_rank_within_site": int(pd.to_numeric(representative[CLIPPED_RANK_COL], errors="coerce")),
                "representative_score_hygiene_flag": int(pd.to_numeric(representative[SCORE_HYGIENE_FLAG_COL], errors="coerce")),
                "representative_score_hygiene_reason_ko": representative[SCORE_HYGIENE_REASON_COL],
                "watch_now_run_count_for_panel": run_count,
                "watch_now_total_day_count_for_panel": int(pd.to_numeric(panel_df["run_day_count"], errors="coerce").fillna(0).sum()),
                "earliest_watch_now_run_start_date": min(panel_df["run_start_date"].map(normalize_date)),
                "latest_watch_now_run_end_date": max(panel_df["run_end_date"].map(normalize_date)),
                "max_clipped_operator_score_for_panel": float(pd.to_numeric(panel_df[CLIPPED_OPERATOR_SCORE_COL], errors="coerce").max()),
                "any_future_fault_linked_flag_ref": any_future_fault,
                "any_future_truth_linked_flag_ref": any_future_truth,
                "overlap_case_class_set": summarize_overlap_case_classes(panel_df),
                "panel_rollup_reason_ko": reason,
            }
        )
    out = pd.DataFrame(rows, columns=WATCH_NOW_PANEL_OUTPUT_COLS)
    if out.empty:
        return out
    out = out.sort_values(
        [
            "representative_clipped_operator_score",
            "watch_now_run_count_for_panel",
            "representative_run_day_count",
            "site",
            "panel_id",
        ],
        ascending=[False, False, False, True, True],
        kind="mergesort",
    )
    return out.reset_index(drop=True)


def summarize_watch_now_panels_scope(
    record_type: str,
    site: str,
    watch_now_panels: pd.DataFrame,
    watch_now: pd.DataFrame,
) -> dict[str, object]:
    run_counts = pd.to_numeric(watch_now_panels["watch_now_run_count_for_panel"], errors="coerce").dropna()
    median_runs = float(run_counts.median()) if not run_counts.empty else 0.0
    max_runs = int(run_counts.max()) if not run_counts.empty else 0
    return {
        "record_type": record_type,
        "site": site,
        "watch_now_panel_count": int(len(watch_now_panels)),
        "watch_now_run_count": int(len(watch_now)),
        "panels_with_multiple_watch_now_runs": int(watch_now_panels["watch_now_run_count_for_panel"].gt(1).sum()),
        "median_watch_now_runs_per_panel": median_runs,
        "max_watch_now_runs_per_panel": max_runs,
        "panels_with_future_fault_linked_ref_count": int(watch_now_panels["any_future_fault_linked_flag_ref"].eq(1).sum()),
        "panels_with_future_truth_linked_ref_count": int(watch_now_panels["any_future_truth_linked_flag_ref"].eq(1).sum()),
    }


def build_watch_now_panels_summary(watch_now_panels: pd.DataFrame, watch_now: pd.DataFrame) -> pd.DataFrame:
    rows = [summarize_watch_now_panels_scope("overall", "", watch_now_panels, watch_now)]
    for site, site_watch_now in watch_now.groupby("site", sort=True, dropna=False):
        site_panels = watch_now_panels.loc[watch_now_panels["site"].eq(site)].copy()
        rows.append(summarize_watch_now_panels_scope("site", site, site_panels, site_watch_now))
    if watch_now.empty and watch_now_panels.empty:
        rows = [summarize_watch_now_panels_scope("overall", "", watch_now_panels, watch_now)]
    return pd.DataFrame(rows, columns=WATCH_NOW_PANEL_SUMMARY_OUTPUT_COLS)


def panel_key_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["site", "panel_id"])
    return df.loc[:, ["site", "panel_id"]].drop_duplicates().reset_index(drop=True)


def panel_overlap_count(queue: pd.DataFrame, watch_now_panels: pd.DataFrame) -> int:
    if queue.empty or watch_now_panels.empty:
        return 0
    queue_keys = set(tuple(row) for row in panel_key_frame(queue).itertuples(index=False, name=None))
    watch_keys = set(tuple(row) for row in panel_key_frame(watch_now_panels).itertuples(index=False, name=None))
    return len(queue_keys & watch_keys)


def build_watch_now_panel_ref_frame(watch_now_panels: pd.DataFrame) -> pd.DataFrame:
    if watch_now_panels.empty:
        return pd.DataFrame(
            columns=[
                "site",
                "panel_id",
                "panel_has_watch_now_overlap_flag",
                "panel_watch_now_run_count",
                "panel_watch_now_total_day_count",
                "panel_watch_now_earliest_start_date",
                "panel_watch_now_latest_end_date",
                "panel_any_future_fault_linked_ref",
                "panel_any_future_truth_linked_ref",
                "panel_overlap_case_class_set",
                "panel_rollup_reason_ko",
            ]
        )
    ref = watch_now_panels.loc[
        :,
        [
            "site",
            "panel_id",
            "watch_now_run_count_for_panel",
            "watch_now_total_day_count_for_panel",
            "earliest_watch_now_run_start_date",
            "latest_watch_now_run_end_date",
            "any_future_fault_linked_flag_ref",
            "any_future_truth_linked_flag_ref",
            "overlap_case_class_set",
            "panel_rollup_reason_ko",
        ],
    ].copy()
    ref = ref.rename(
        columns={
            "watch_now_run_count_for_panel": "panel_watch_now_run_count",
            "watch_now_total_day_count_for_panel": "panel_watch_now_total_day_count",
            "earliest_watch_now_run_start_date": "panel_watch_now_earliest_start_date",
            "latest_watch_now_run_end_date": "panel_watch_now_latest_end_date",
            "any_future_fault_linked_flag_ref": "panel_any_future_fault_linked_ref",
            "any_future_truth_linked_flag_ref": "panel_any_future_truth_linked_ref",
            "overlap_case_class_set": "panel_overlap_case_class_set",
        }
    )
    ref["panel_has_watch_now_overlap_flag"] = 1
    return ref


def build_attention_now(queue: pd.DataFrame, watch_now_panels: pd.DataFrame) -> pd.DataFrame:
    watch_panel_ref = build_watch_now_panel_ref_frame(watch_now_panels)
    queue_items = queue.copy()
    queue_items["attention_class"] = "queue_run"
    queue_items["display_start_date"] = queue_items["run_start_date"]
    queue_items["display_end_date"] = queue_items["run_end_date"]
    queue_items["display_day_count"] = pd.to_numeric(queue_items["run_day_count"], errors="coerce")
    queue_items["display_shape_class"] = queue_items["run_shape_class"]
    queue_items["display_status_or_tier"] = queue_items["status"]
    queue_items["future_fault_linked_flag_ref"] = pd.to_numeric(queue_items["future_fault_linked_flag"], errors="coerce").fillna(0).astype(int)
    queue_items["future_truth_linked_flag_ref"] = pd.to_numeric(queue_items["future_truth_linked_flag"], errors="coerce").fillna(0).astype(int)
    queue_items["attention_reason_ko"] = "즉시 대응 queue run"
    queue_items = queue_items.merge(watch_panel_ref, on=["site", "panel_id"], how="left")
    queue_items["panel_has_watch_now_overlap_flag"] = pd.to_numeric(
        queue_items["panel_has_watch_now_overlap_flag"],
        errors="coerce",
    ).fillna(0).astype(int)
    queue_items["panel_watch_now_run_count"] = pd.to_numeric(
        queue_items["panel_watch_now_run_count"],
        errors="coerce",
    ).fillna(0).astype(int)
    queue_items["panel_watch_now_total_day_count"] = pd.to_numeric(
        queue_items["panel_watch_now_total_day_count"],
        errors="coerce",
    ).fillna(0).astype(int)
    queue_items["panel_any_future_fault_linked_ref"] = pd.to_numeric(
        queue_items["panel_any_future_fault_linked_ref"],
        errors="coerce",
    ).fillna(0).astype(int)
    queue_items["panel_any_future_truth_linked_ref"] = pd.to_numeric(
        queue_items["panel_any_future_truth_linked_ref"],
        errors="coerce",
    ).fillna(0).astype(int)
    for col in [
        "panel_watch_now_earliest_start_date",
        "panel_watch_now_latest_end_date",
        "panel_overlap_case_class_set",
        "panel_rollup_reason_ko",
    ]:
        queue_items[col] = queue_items[col].map(normalize_text)
    queue_items["attention_merge_reason_ko"] = "queue 단독"
    queue_items.loc[
        queue_items["panel_has_watch_now_overlap_flag"].eq(1),
        "attention_merge_reason_ko",
    ] = "queue 우선, panel reference 병합"

    watch_items = watch_now_panels.copy()
    if not queue.empty and not watch_now_panels.empty:
        watch_items = watch_items.merge(
            panel_key_frame(queue).assign(_in_queue=1),
            on=["site", "panel_id"],
            how="left",
        )
        watch_items = watch_items.loc[watch_items["_in_queue"].fillna(0).eq(0)].drop(columns=["_in_queue"])
    watch_items["attention_class"] = "watch_now_panel"
    watch_items["display_start_date"] = watch_items["representative_run_start_date"]
    watch_items["display_end_date"] = watch_items["representative_run_end_date"]
    watch_items["display_day_count"] = pd.to_numeric(watch_items["representative_run_day_count"], errors="coerce")
    watch_items["display_shape_class"] = watch_items["representative_run_shape_class"]
    watch_items["display_status_or_tier"] = "watch_now"
    watch_items["priority_band"] = watch_items["representative_priority_band"]
    watch_items[CLIPPED_OPERATOR_SCORE_COL] = pd.to_numeric(watch_items["representative_clipped_operator_score"], errors="coerce")
    watch_items[RAW_OPERATOR_SCORE_COL] = pd.to_numeric(watch_items["representative_raw_operator_score"], errors="coerce")
    watch_items["overlap_case_class"] = watch_items["representative_overlap_case_class"]
    watch_items["action_bucket"] = watch_items["representative_action_bucket"]
    watch_items["watchlist_bucket"] = "recurring_watch_p1"
    watch_items[SCORE_HYGIENE_FLAG_COL] = pd.to_numeric(watch_items["representative_score_hygiene_flag"], errors="coerce").fillna(0).astype(int)
    watch_items[SCORE_HYGIENE_REASON_COL] = watch_items["representative_score_hygiene_reason_ko"].map(normalize_text)
    watch_items["future_fault_linked_flag_ref"] = pd.to_numeric(watch_items["any_future_fault_linked_flag_ref"], errors="coerce").fillna(0).astype(int)
    watch_items["future_truth_linked_flag_ref"] = pd.to_numeric(watch_items["any_future_truth_linked_flag_ref"], errors="coerce").fillna(0).astype(int)
    watch_items["panel_has_watch_now_overlap_flag"] = 1
    watch_items["panel_watch_now_run_count"] = pd.to_numeric(watch_items["watch_now_run_count_for_panel"], errors="coerce").fillna(0).astype(int)
    watch_items["panel_watch_now_total_day_count"] = pd.to_numeric(
        watch_items["watch_now_total_day_count_for_panel"],
        errors="coerce",
    ).fillna(0).astype(int)
    watch_items["panel_watch_now_earliest_start_date"] = watch_items["earliest_watch_now_run_start_date"].map(normalize_text)
    watch_items["panel_watch_now_latest_end_date"] = watch_items["latest_watch_now_run_end_date"].map(normalize_text)
    watch_items["panel_any_future_fault_linked_ref"] = pd.to_numeric(
        watch_items["any_future_fault_linked_flag_ref"],
        errors="coerce",
    ).fillna(0).astype(int)
    watch_items["panel_any_future_truth_linked_ref"] = pd.to_numeric(
        watch_items["any_future_truth_linked_flag_ref"],
        errors="coerce",
    ).fillna(0).astype(int)
    watch_items["panel_overlap_case_class_set"] = watch_items["overlap_case_class_set"].map(normalize_text)
    watch_items["attention_merge_reason_ko"] = "watch panel 단독"
    watch_items["attention_reason_ko"] = "반복 chronic 대표 panel 주시"

    attention = pd.concat(
        [
            queue_items.reindex(columns=ATTENTION_OUTPUT_COLS),
            watch_items.reindex(columns=ATTENTION_OUTPUT_COLS),
        ],
        axis=0,
        ignore_index=True,
    )
    if attention.empty:
        return attention.reindex(columns=ATTENTION_OUTPUT_COLS)
    attention["attention_any_future_fault_linked_ref_flag"] = (
        pd.to_numeric(attention["future_fault_linked_flag_ref"], errors="coerce").fillna(0).astype(int).eq(1)
        | pd.to_numeric(attention["panel_any_future_fault_linked_ref"], errors="coerce").fillna(0).astype(int).eq(1)
    ).astype(int)
    attention["attention_any_future_truth_linked_ref_flag"] = (
        pd.to_numeric(attention["future_truth_linked_flag_ref"], errors="coerce").fillna(0).astype(int).eq(1)
        | pd.to_numeric(attention["panel_any_future_truth_linked_ref"], errors="coerce").fillna(0).astype(int).eq(1)
    ).astype(int)
    attention["_class_order"] = attention["attention_class"].map(ATTENTION_CLASS_PRIORITY).fillna(99)
    attention["_priority_order"] = attention["priority_band"].map(PRIORITY_PRIORITY).fillna(99)
    attention = attention.sort_values(
        [
            "_class_order",
            "_priority_order",
            CLIPPED_OPERATOR_SCORE_COL,
            "display_day_count",
            "site",
            "panel_id",
            "display_start_date",
        ],
        ascending=[True, True, False, False, True, True, True],
        kind="mergesort",
    ).drop(columns=["_class_order", "_priority_order"])
    return attention.reset_index(drop=True)


def summarize_attention_scope(
    record_type: str,
    site: str,
    attention: pd.DataFrame,
    queue: pd.DataFrame,
    watch_now_panels: pd.DataFrame,
) -> dict[str, object]:
    return {
        "record_type": record_type,
        "site": site,
        "attention_count": int(len(attention)),
        "queue_run_attention_count": int(attention["attention_class"].eq("queue_run").sum()),
        "watch_now_panel_attention_count": int(attention["attention_class"].eq("watch_now_panel").sum()),
        "deduped_panel_overlap_count": panel_overlap_count(queue, watch_now_panels),
        "deduped_overlap_future_fault_linked_ref_count": int(
            (
                attention["attention_class"].eq("queue_run")
                & attention["panel_has_watch_now_overlap_flag"].eq(1)
                & attention["panel_any_future_fault_linked_ref"].eq(1)
            ).sum()
        ),
        "deduped_overlap_future_truth_linked_ref_count": int(
            (
                attention["attention_class"].eq("queue_run")
                & attention["panel_has_watch_now_overlap_flag"].eq(1)
                & attention["panel_any_future_truth_linked_ref"].eq(1)
            ).sum()
        ),
        "attention_future_fault_linked_ref_count": int(attention["future_fault_linked_flag_ref"].eq(1).sum()),
        "attention_future_truth_linked_ref_count": int(attention["future_truth_linked_flag_ref"].eq(1).sum()),
        "attention_any_future_fault_linked_ref_count": int(
            pd.to_numeric(attention["attention_any_future_fault_linked_ref_flag"], errors="coerce").fillna(0).eq(1).sum()
        ),
        "attention_any_future_truth_linked_ref_count": int(
            pd.to_numeric(attention["attention_any_future_truth_linked_ref_flag"], errors="coerce").fillna(0).eq(1).sum()
        ),
    }


def build_attention_summary(attention: pd.DataFrame, queue: pd.DataFrame, watch_now_panels: pd.DataFrame) -> pd.DataFrame:
    rows = [summarize_attention_scope("overall", "", attention, queue, watch_now_panels)]
    sites = sorted(set(attention["site"].dropna().tolist()) | set(queue["site"].dropna().tolist()) | set(watch_now_panels["site"].dropna().tolist()))
    for site in sites:
        site_attention = attention.loc[attention["site"].eq(site)].copy()
        site_queue = queue.loc[queue["site"].eq(site)].copy()
        site_watch_now_panels = watch_now_panels.loc[watch_now_panels["site"].eq(site)].copy()
        rows.append(summarize_attention_scope("site", site, site_attention, site_queue, site_watch_now_panels))
    return pd.DataFrame(rows, columns=ATTENTION_SUMMARY_OUTPUT_COLS)


def summarize_group(
    record_type: str,
    site: str,
    group: pd.DataFrame,
    queue: pd.DataFrame,
    backlog: pd.DataFrame,
    watchlist: pd.DataFrame,
    watch_now: pd.DataFrame,
    watch_review: pd.DataFrame,
) -> dict[str, object]:
    overlaps = compute_overlap_rates(group)
    return {
        "record_type": record_type,
        "site": site,
        "total_runs": int(len(group)),
        "ongoing_run_count": int(group["status"].eq("ongoing_run").sum()),
        "new_run_count": int(group["status"].eq("new_run").sum()),
        "recurring_run_count": int(group["status"].eq("recurring_run").sum()),
        "recovered_run_count": int(group["status"].eq("recovered_run").sum()),
        "chronic_run_count": int(group["run_shape_class"].eq("chronic_alert_run").sum()),
        "p1_run_count": int(group["priority_band"].eq("P1").sum()),
        "p2_run_count": int(group["priority_band"].eq("P2").sum()),
        "investigate_now_count": int(group["action_bucket"].eq("investigate_now").sum()),
        "monitor_active_count": int(group["action_bucket"].eq("monitor_active").sum()),
        "recurring_backlog_count": int(group["action_bucket"].eq("recurring_backlog").sum()),
        "recovered_backlog_count": int(group["action_bucket"].eq("recovered_backlog").sum()),
        "historical_archive_count": int(group["action_bucket"].eq("historical_archive").sum()),
        "queue_count": int(len(queue)),
        "backlog_count": int(len(backlog)),
        "queue_chronic_count": int(queue["run_shape_class"].eq("chronic_alert_run").sum()),
        "backlog_chronic_count": int(backlog["run_shape_class"].eq("chronic_alert_run").sum()),
        "queue_future_fault_linked_count": int(queue["future_fault_linked_flag"].eq(1).sum()),
        "queue_future_truth_linked_count": int(queue["future_truth_linked_flag"].eq(1).sum()),
        "clipped_top20_overlap_vs_raw": overlaps["top20"],
        "clipped_top50_overlap_vs_raw": overlaps["top50"],
        "clipped_top100_overlap_vs_raw": overlaps["top100"],
        "score_hygiene_flag_count": int(group[SCORE_HYGIENE_FLAG_COL].eq(1).sum()),
        "score_hygiene_queue_count": int(queue[SCORE_HYGIENE_FLAG_COL].eq(1).sum()),
        "score_hygiene_backlog_count": int(backlog[SCORE_HYGIENE_FLAG_COL].eq(1).sum()),
        "watchlist_count": int(len(watchlist)),
        "watchlist_p1_count": int(watchlist["watchlist_bucket"].eq("recurring_watch_p1").sum()),
        "watchlist_p2_count": int(watchlist["watchlist_bucket"].eq("recurring_watch_p2").sum()),
        "watchlist_chronic_count": int(watchlist["run_shape_class"].eq("chronic_alert_run").sum()),
        "watch_now_count": int(len(watch_now)),
        "watch_review_count": int(len(watch_review)),
    }


def build_summary(
    registry: pd.DataFrame,
    queue: pd.DataFrame,
    backlog: pd.DataFrame,
    watchlist: pd.DataFrame,
    watch_now: pd.DataFrame,
    watch_review: pd.DataFrame,
) -> pd.DataFrame:
    rows = [summarize_group("overall", "", registry, queue, backlog, watchlist, watch_now, watch_review)]
    for site, site_group in registry.groupby("site", sort=True, dropna=False):
        site_queue = queue.loc[queue["site"].eq(site)].copy()
        site_backlog = backlog.loc[backlog["site"].eq(site)].copy()
        site_watchlist = watchlist.loc[watchlist["site"].eq(site)].copy()
        site_watch_now = watch_now.loc[watch_now["site"].eq(site)].copy()
        site_watch_review = watch_review.loc[watch_review["site"].eq(site)].copy()
        rows.append(
            summarize_group(
                "site",
                site,
                site_group,
                site_queue,
                site_backlog,
                site_watchlist,
                site_watch_now,
                site_watch_review,
            )
        )
    return pd.DataFrame(rows, columns=SUMMARY_OUTPUT_COLS)


def summarize_watchlist_scope(
    record_type: str,
    site: str,
    watchlist: pd.DataFrame,
    watch_now: pd.DataFrame,
    watch_review: pd.DataFrame,
    watch_now_panels: pd.DataFrame,
) -> dict[str, object]:
    watch_now_panel_counts = pd.to_numeric(watch_now_panels["watch_now_run_count_for_panel"], errors="coerce").dropna()
    return {
        "record_type": record_type,
        "site": site,
        "watchlist_count": int(len(watchlist)),
        "watchlist_p1_count": int(watchlist["watchlist_bucket"].eq("recurring_watch_p1").sum()),
        "watchlist_p2_count": int(watchlist["watchlist_bucket"].eq("recurring_watch_p2").sum()),
        "watch_now_count": int(len(watch_now)),
        "watch_review_count": int(len(watch_review)),
        "watch_now_panel_count": int(len(watch_now_panels)),
        "panels_with_multiple_watch_now_runs": int(watch_now_panels["watch_now_run_count_for_panel"].gt(1).sum()),
        "median_watch_now_runs_per_panel": float(watch_now_panel_counts.median()) if not watch_now_panel_counts.empty else 0.0,
        "watchlist_chronic_count": int(watchlist["run_shape_class"].eq("chronic_alert_run").sum()),
        "watchlist_unmatched_to_review_count": int(watchlist["overlap_case_class"].eq("unmatched_to_review").sum()),
        "watchlist_eligible_local_overlap_count": int(watchlist["overlap_case_class"].eq("eligible_local_overlap").sum()),
        "watchlist_nuisance_overlap_count": int(watchlist["overlap_case_class"].eq("nuisance_overlap").sum()),
        "watchlist_future_fault_linked_count": int(watchlist["future_fault_linked_flag"].eq(1).sum()),
        "watchlist_future_truth_linked_count": int(watchlist["future_truth_linked_flag"].eq(1).sum()),
        "watch_now_future_fault_linked_count": int(watch_now["future_fault_linked_flag"].eq(1).sum()),
        "watch_now_future_truth_linked_count": int(watch_now["future_truth_linked_flag"].eq(1).sum()),
        "watch_review_future_fault_linked_count": int(watch_review["future_fault_linked_flag"].eq(1).sum()),
        "watch_review_future_truth_linked_count": int(watch_review["future_truth_linked_flag"].eq(1).sum()),
    }


def build_watchlist_summary(
    watchlist: pd.DataFrame,
    watch_now: pd.DataFrame,
    watch_review: pd.DataFrame,
    watch_now_panels: pd.DataFrame,
    registry: pd.DataFrame,
) -> pd.DataFrame:
    rows = [summarize_watchlist_scope("overall", "", watchlist, watch_now, watch_review, watch_now_panels)]
    for site, _ in registry.groupby("site", sort=True, dropna=False):
        site_watchlist = watchlist.loc[watchlist["site"].eq(site)].copy()
        site_watch_now = watch_now.loc[watch_now["site"].eq(site)].copy()
        site_watch_review = watch_review.loc[watch_review["site"].eq(site)].copy()
        site_watch_now_panels = watch_now_panels.loc[watch_now_panels["site"].eq(site)].copy()
        rows.append(
            summarize_watchlist_scope(
                "site",
                site,
                site_watchlist,
                site_watch_now,
                site_watch_review,
                site_watch_now_panels,
            )
        )
    return pd.DataFrame(rows, columns=WATCHLIST_SUMMARY_OUTPUT_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    registry = build_registry(root)
    queue = build_queue(registry)
    backlog = build_backlog(registry)
    watchlist = build_watchlist(registry)
    watch_now = build_watchlist_tier(registry, "watch_now")
    watch_review = build_watchlist_tier(registry, "watch_review")
    watch_now_panels = build_watch_now_panel_rollup(watch_now)
    watch_now_panels_summary = build_watch_now_panels_summary(watch_now_panels, watch_now)
    attention_now = build_attention_now(queue, watch_now_panels)
    attention_summary = build_attention_summary(attention_now, queue, watch_now_panels)
    summary = build_summary(registry, queue, backlog, watchlist, watch_now, watch_review)
    watchlist_summary = build_watchlist_summary(watchlist, watch_now, watch_review, watch_now_panels, registry)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    registry.loc[:, REGISTRY_OUTPUT_COLS].to_csv(
        share_dir / RUN_REGISTRY_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    queue.loc[:, REGISTRY_OUTPUT_COLS].to_csv(
        share_dir / RUN_QUEUE_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    backlog.loc[:, REGISTRY_OUTPUT_COLS].to_csv(
        share_dir / RUN_BACKLOG_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    watchlist.loc[:, WATCHLIST_OUTPUT_COLS].to_csv(
        share_dir / RUN_WATCHLIST_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    watch_now.loc[:, WATCHLIST_OUTPUT_COLS].to_csv(
        share_dir / RUN_WATCHLIST_NOW_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    watch_now_panels.loc[:, WATCH_NOW_PANEL_OUTPUT_COLS].to_csv(
        share_dir / RUN_WATCHLIST_NOW_PANELS_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    attention_now.loc[:, ATTENTION_OUTPUT_COLS].to_csv(
        share_dir / RUN_ATTENTION_NOW_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    watch_review.loc[:, WATCHLIST_OUTPUT_COLS].to_csv(
        share_dir / RUN_WATCHLIST_REVIEW_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    summary.to_csv(
        share_dir / RUN_SUMMARY_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    watchlist_summary.to_csv(
        share_dir / RUN_WATCHLIST_SUMMARY_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    watch_now_panels_summary.to_csv(
        share_dir / RUN_WATCHLIST_NOW_PANELS_SUMMARY_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    attention_summary.to_csv(
        share_dir / RUN_ATTENTION_SUMMARY_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    main()
