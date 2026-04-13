#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

CANDIDATES_NAME = "panel_day_engine_run_label_expansion_candidates_v1.csv"
FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
V0_SCORES_NAME = "panel_day_engine_run_ranker_v0_scores.csv"
WATCHLIST_NOW_PANELS_NAME = "panel_day_engine_operator_run_watchlist_now_panels_v1.csv"
WATCHLIST_REVIEW_NAME = "panel_day_engine_operator_run_watchlist_review_v1.csv"
FATE_CASES_NAME = "panel_day_engine_local_seed_carry_fate_cases_v1.csv"
REAUDIT_NAME = "panel_date_reaudit_working.csv"

BATCH_OUTPUT_NAME = "panel_day_engine_run_label_expansion_review_batch_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_run_label_expansion_review_batch_summary_v1.csv"
EVIDENCE_OUTPUT_NAME = "panel_day_engine_run_label_expansion_review_evidence_v1.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
TRACK_ORDER = {
    "positive_review_batch": 1,
    "monitor_review_batch": 2,
    "common_cause_review_batch": 3,
}
PRIORITY_ORDER = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
TRUTH_OVERLAP_TOLERANCE_DAYS = 5

CANDIDATE_REQUIRED_COLS = [
    *KEY_COLS,
    "run_day_count",
    "run_shape_class",
    "label_bucket_v2",
    "candidate_class",
    "candidate_priority_band",
    "site_positive_gap_flag",
    "site_negative_gap_flag",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
    "global_score_rank",
    "site_score_rank",
    "watch_now_panel_ref_flag",
    "watch_review_run_ref_flag",
    "common_cause_descriptive_ref_flag",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "expansion_reason_ko",
]
FEATURE_REQUIRED_COLS = [
    *KEY_COLS,
    "run_day_count",
    "run_shape_class",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
]
V0_REQUIRED_COLS = [*KEY_COLS, "electrical_core_score", "electrical_core_minus_broadshape_050"]
WATCHLIST_NOW_REQUIRED_COLS = ["site", "panel_id", "any_future_fault_linked_flag_ref", "any_future_truth_linked_flag_ref"]
WATCHLIST_REVIEW_REQUIRED_COLS = [*KEY_COLS, "future_fault_linked_flag", "future_truth_linked_flag"]
FATE_REQUIRED_COLS = [
    *KEY_COLS,
    "future_confirmed_fault_7d",
    "future_critical_fault_7d",
    "future_final_fault_7d",
    "future_confirmed_fault_30d",
    "future_critical_fault_30d",
    "future_final_fault_30d",
    "future_confirmed_fault_60d",
    "future_critical_fault_60d",
    "future_final_fault_60d",
    "future_truth_overlap_30d",
    "future_truth_overlap_60d",
    "future_truth_candidate_validities",
    "future_truth_case_ids",
]
REAUDIT_REQUIRED_COLS = ["site", "panel_id", "strict_trigger_date", "candidate_validity", "review_priority"]

BATCH_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "label_bucket_v2",
    "candidate_class",
    "candidate_priority_band",
    "review_track",
    "review_priority_rank",
    "review_priority_reason_ko",
    "suggested_label_action",
    "suggested_label_action_reason_ko",
    "site_positive_gap_flag",
    "site_negative_gap_flag",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
    "global_score_rank",
    "site_score_rank",
    "watch_now_panel_ref_flag",
    "watch_review_run_ref_flag",
    "common_cause_descriptive_ref_flag",
    "expansion_reason_ko",
]

EVIDENCE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "review_track",
    "candidate_class",
    "candidate_priority_band",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
    "global_score_rank",
    "site_score_rank",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "overlapping_truth_case_ids",
    "overlapping_truth_candidate_validities",
    "future_fault_linked_ref_flag",
    "future_truth_linked_ref_flag",
    "review_evidence_reason_ko",
]

SUMMARY_COLS = [
    "record_type",
    "site",
    "positive_review_batch_count",
    "monitor_review_batch_count",
    "common_cause_review_batch_count",
    "p1_included_count",
    "p2_included_count",
    "site_positive_gap_flag",
    "site_negative_gap_flag",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a small prioritized review batch from the broad run label expansion candidate pool."
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


def normalize_date(value: object) -> str:
    text = normalize_text(value)
    return text[:10] if len(text) >= 10 else text


def parse_date(value: object) -> pd.Timestamp:
    text = normalize_date(value)
    if text == "":
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


def normalize_key_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["site"] = out["site"].map(normalize_text)
    out["panel_id"] = out["panel_id"].map(normalize_text)
    out["run_start_date"] = out["run_start_date"].map(normalize_date)
    out["run_end_date"] = out["run_end_date"].map(normalize_date)
    return out


def split_csv_values(value: object) -> list[str]:
    text = normalize_text(value)
    if text == "":
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def join_unique_csv(values: list[str]) -> str:
    seen: dict[str, None] = {}
    for value in values:
        text = normalize_text(value)
        if text:
            seen[text] = None
    return ",".join(seen.keys())


def load_candidates(root: Path) -> pd.DataFrame:
    path = root / "_share" / CANDIDATES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, CANDIDATE_REQUIRED_COLS, path.name)
    df = normalize_key_cols(df)
    string_cols = [
        "run_shape_class",
        "label_bucket_v2",
        "candidate_class",
        "candidate_priority_band",
        "expansion_reason_ko",
    ]
    for col in string_cols:
        df[col] = df[col].map(normalize_text)
    numeric_cols = [
        "run_day_count",
        "site_positive_gap_flag",
        "site_negative_gap_flag",
        "electrical_core_score",
        "electrical_core_minus_broadshape_050",
        "global_score_rank",
        "site_score_rank",
        "watch_now_panel_ref_flag",
        "watch_review_run_ref_flag",
        "common_cause_descriptive_ref_flag",
        "max_v_drop",
        "min_mid_v_ratio",
        "min_mid_ratio",
        "cond_evt_only_day_ratio",
        "ae_mid_or_hi_early_day_ratio",
        "mean_signal_count",
        "max_signal_count",
        "p95_recon_error",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, CANDIDATE_REQUIRED_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_feature_table(root: Path) -> pd.DataFrame:
    path = root / "_share" / FEATURE_TABLE_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, FEATURE_REQUIRED_COLS, path.name)
    df = normalize_key_cols(df)
    df["run_shape_class"] = df["run_shape_class"].map(normalize_text)
    for col in FEATURE_REQUIRED_COLS:
        if col in KEY_COLS or col == "run_shape_class":
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, FEATURE_REQUIRED_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_v0_scores(root: Path) -> pd.DataFrame:
    path = root / "_share" / V0_SCORES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, V0_REQUIRED_COLS, path.name)
    df = normalize_key_cols(df)
    for col in ["electrical_core_score", "electrical_core_minus_broadshape_050"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, V0_REQUIRED_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_watch_now_panels(root: Path) -> pd.DataFrame:
    path = root / "_share" / WATCHLIST_NOW_PANELS_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, WATCHLIST_NOW_REQUIRED_COLS, path.name)
    df["site"] = df["site"].map(normalize_text)
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["watch_now_future_fault_ref_flag"] = df["any_future_fault_linked_flag_ref"].map(to_int_flag).astype(int)
    df["watch_now_future_truth_ref_flag"] = df["any_future_truth_linked_flag_ref"].map(to_int_flag).astype(int)
    return df.loc[:, ["site", "panel_id", "watch_now_future_fault_ref_flag", "watch_now_future_truth_ref_flag"]].drop_duplicates(
        subset=["site", "panel_id"], keep="first"
    )


def load_watchlist_review(root: Path) -> pd.DataFrame:
    path = root / "_share" / WATCHLIST_REVIEW_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, WATCHLIST_REVIEW_REQUIRED_COLS, path.name)
    df = normalize_key_cols(df)
    df["watch_review_future_fault_ref_flag"] = df["future_fault_linked_flag"].map(to_int_flag).astype(int)
    df["watch_review_future_truth_ref_flag"] = df["future_truth_linked_flag"].map(to_int_flag).astype(int)
    return df.loc[
        :,
        [*KEY_COLS, "watch_review_future_fault_ref_flag", "watch_review_future_truth_ref_flag"],
    ].drop_duplicates(subset=KEY_COLS, keep="first")


def load_fate_cases(root: Path) -> pd.DataFrame:
    path = root / "_share" / FATE_CASES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, FATE_REQUIRED_COLS, path.name)
    df = normalize_key_cols(df)
    fault_cols = [
        "future_confirmed_fault_7d",
        "future_critical_fault_7d",
        "future_final_fault_7d",
        "future_confirmed_fault_30d",
        "future_critical_fault_30d",
        "future_final_fault_30d",
        "future_confirmed_fault_60d",
        "future_critical_fault_60d",
        "future_final_fault_60d",
    ]
    truth_cols = ["future_truth_overlap_30d", "future_truth_overlap_60d"]
    for col in fault_cols + truth_cols:
        df[col] = df[col].map(to_int_flag).astype(int)
    df["fate_future_fault_ref_flag"] = 0
    for col in fault_cols:
        df["fate_future_fault_ref_flag"] |= df[col]
    df["fate_future_truth_ref_flag"] = 0
    for col in truth_cols:
        df["fate_future_truth_ref_flag"] |= df[col]
    df["future_truth_case_ids"] = df["future_truth_case_ids"].map(normalize_text)
    df["future_truth_candidate_validities"] = df["future_truth_candidate_validities"].map(normalize_text)
    return df.loc[
        :,
        [
            *KEY_COLS,
            "fate_future_fault_ref_flag",
            "fate_future_truth_ref_flag",
            "future_truth_case_ids",
            "future_truth_candidate_validities",
        ],
    ].drop_duplicates(subset=KEY_COLS, keep="first")


def load_reaudit(root: Path) -> pd.DataFrame:
    path = root / "_share" / REAUDIT_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REAUDIT_REQUIRED_COLS, path.name)
    df["site"] = df["site"].map(normalize_text)
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["strict_trigger_date"] = df["strict_trigger_date"].map(parse_date)
    df["candidate_validity"] = df["candidate_validity"].map(normalize_text)
    df["review_priority"] = df["review_priority"].map(normalize_text)
    df["truth_case_id"] = df.apply(
        lambda row: f"reaudit|{row['site']}|{row['panel_id']}|{row['strict_trigger_date'].date()}"
        if pd.notna(row["strict_trigger_date"])
        else "",
        axis=1,
    )
    return df.loc[:, ["site", "panel_id", "strict_trigger_date", "candidate_validity", "review_priority", "truth_case_id"]]


def merge_fill(base: pd.DataFrame, ref: pd.DataFrame, *, cols: list[str], on: list[str], suffix: str) -> pd.DataFrame:
    merged = base.merge(ref, on=on, how="left", suffixes=("", suffix))
    for col in cols:
        ref_col = f"{col}{suffix}"
        if ref_col not in merged.columns:
            continue
        if merged[col].dtype.kind in {"O", "U", "S"}:
            merged[col] = merged[col].where(merged[col].map(normalize_text).ne(""), merged[ref_col])
        else:
            merged[col] = merged[col].where(merged[col].notna(), merged[ref_col])
        merged = merged.drop(columns=[ref_col], errors="ignore")
    return merged


def sort_for_selection(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = out.sort_values(
        [
            "electrical_core_minus_broadshape_050",
            "run_day_count",
            "global_score_rank",
            "site_score_rank",
            "site",
            "panel_id",
            "run_start_date",
            "run_end_date",
        ],
        ascending=[False, False, True, True, True, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    return out


def assign_review_action(candidate_class: str) -> tuple[str, str]:
    if candidate_class == "positive_review_candidate":
        return ("inspect_for_positive_promotion", "high-score unlabeled run이라 positive 승격 가능성을 우선 검토")
    if candidate_class == "monitor_review_candidate":
        return ("inspect_for_monitor_confirmation", "monitor-like burden인지 확인해 scorer 제외 bucket을 안정화")
    if candidate_class == "common_cause_review_candidate":
        return ("inspect_for_common_cause_confirmation", "common-cause routing/descriptive bucket 확인이 우선")
    return ("inspect_for_negative_promotion", "negative 승격 근거가 있는지 보조 검토")


def assign_priority_reason(selection_source: str, row: pd.Series) -> str:
    if selection_source == "positive_p1_all":
        return "site positive gap이 있는 P1 candidate라 전부 포함"
    if selection_source == "positive_p2_site_top5":
        return "site별 상위 P2 5건 내라 균형 있게 우선 포함"
    if selection_source == "positive_p2_global_topup":
        return "site top5 이후 남은 P2 중 global 상위 점수라 top-up 포함"
    if selection_source == "monitor_top10_global":
        return "monitor review candidate 중 global 상위 10건"
    if selection_source == "common_cause_all":
        return "common-cause review candidate는 수가 작아 전부 포함"
    return "review batch 기본 우선순위"


def build_base_universe(root: Path) -> pd.DataFrame:
    candidates_df = load_candidates(root)
    feature_df = load_feature_table(root)
    v0_df = load_v0_scores(root)
    watch_now_df = load_watch_now_panels(root)
    watch_review_df = load_watchlist_review(root)
    fate_df = load_fate_cases(root)

    merged = candidates_df.copy()
    merged = merge_fill(
        merged,
        feature_df,
        cols=[
            "run_day_count",
            "run_shape_class",
            "max_v_drop",
            "min_mid_v_ratio",
            "min_mid_ratio",
            "cond_evt_only_day_ratio",
            "ae_mid_or_hi_early_day_ratio",
            "mean_signal_count",
            "max_signal_count",
            "p95_recon_error",
        ],
        on=KEY_COLS,
        suffix="_feature",
    )
    merged = merge_fill(
        merged,
        v0_df,
        cols=["electrical_core_score", "electrical_core_minus_broadshape_050"],
        on=KEY_COLS,
        suffix="_v0",
    )
    merged = merged.merge(watch_now_df, on=["site", "panel_id"], how="left", validate="many_to_one")
    merged = merged.merge(watch_review_df, on=KEY_COLS, how="left", validate="one_to_one")
    merged = merged.merge(fate_df, on=KEY_COLS, how="left", validate="one_to_one")

    for col in [
        "run_shape_class",
        "label_bucket_v2",
        "candidate_class",
        "candidate_priority_band",
        "expansion_reason_ko",
        "future_truth_case_ids",
        "future_truth_candidate_validities",
    ]:
        merged[col] = merged[col].fillna("").map(normalize_text)
    numeric_cols = [
        "run_day_count",
        "site_positive_gap_flag",
        "site_negative_gap_flag",
        "electrical_core_score",
        "electrical_core_minus_broadshape_050",
        "global_score_rank",
        "site_score_rank",
        "watch_now_panel_ref_flag",
        "watch_review_run_ref_flag",
        "common_cause_descriptive_ref_flag",
        "watch_now_future_fault_ref_flag",
        "watch_now_future_truth_ref_flag",
        "watch_review_future_fault_ref_flag",
        "watch_review_future_truth_ref_flag",
        "fate_future_fault_ref_flag",
        "fate_future_truth_ref_flag",
        "max_v_drop",
        "min_mid_v_ratio",
        "min_mid_ratio",
        "cond_evt_only_day_ratio",
        "ae_mid_or_hi_early_day_ratio",
        "mean_signal_count",
        "max_signal_count",
        "p95_recon_error",
    ]
    for col in numeric_cols:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")
    for col in [
        "site_positive_gap_flag",
        "site_negative_gap_flag",
        "watch_now_panel_ref_flag",
        "watch_review_run_ref_flag",
        "common_cause_descriptive_ref_flag",
        "watch_now_future_fault_ref_flag",
        "watch_now_future_truth_ref_flag",
        "watch_review_future_fault_ref_flag",
        "watch_review_future_truth_ref_flag",
        "fate_future_fault_ref_flag",
        "fate_future_truth_ref_flag",
    ]:
        merged[col] = merged[col].fillna(0).map(to_int_flag).astype(int)
    return merged


def select_positive_batch(df: pd.DataFrame) -> pd.DataFrame:
    positive_df = df.loc[df["candidate_class"].eq("positive_review_candidate")].copy()
    p1_df = sort_for_selection(positive_df.loc[positive_df["candidate_priority_band"].eq("P1")].copy())
    if not p1_df.empty:
        p1_df["selection_source"] = "positive_p1_all"

    p2_df = sort_for_selection(positive_df.loc[positive_df["candidate_priority_band"].eq("P2")].copy())
    per_site_rows: list[pd.DataFrame] = []
    for site, site_df in p2_df.groupby("site", sort=True):
        top_site = site_df.head(5).copy()
        if not top_site.empty:
            top_site["selection_source"] = "positive_p2_site_top5"
            per_site_rows.append(top_site)
    p2_site_top5 = pd.concat(per_site_rows, ignore_index=True) if per_site_rows else p2_df.iloc[0:0].copy()

    selected_keys = set(map(tuple, p2_site_top5[KEY_COLS].itertuples(index=False, name=None)))
    remaining_mask = ~p2_df[KEY_COLS].apply(tuple, axis=1).isin(selected_keys)
    p2_remaining = p2_df.loc[remaining_mask].copy()
    p2_global_topup = sort_for_selection(p2_remaining).head(20).copy()
    if not p2_global_topup.empty:
        p2_global_topup["selection_source"] = "positive_p2_global_topup"

    selected = pd.concat([p1_df, p2_site_top5, p2_global_topup], ignore_index=True)
    if selected.empty:
        return selected
    selected = selected.drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)
    selected["review_track"] = "positive_review_batch"
    return selected


def select_monitor_batch(df: pd.DataFrame) -> pd.DataFrame:
    monitor_df = sort_for_selection(df.loc[df["candidate_class"].eq("monitor_review_candidate")].copy()).head(10)
    if monitor_df.empty:
        return monitor_df
    monitor_df["selection_source"] = "monitor_top10_global"
    monitor_df["review_track"] = "monitor_review_batch"
    return monitor_df.reset_index(drop=True)


def select_common_cause_batch(df: pd.DataFrame) -> pd.DataFrame:
    common_df = sort_for_selection(df.loc[df["candidate_class"].eq("common_cause_review_candidate")].copy())
    if common_df.empty:
        return common_df
    common_df["selection_source"] = "common_cause_all"
    common_df["review_track"] = "common_cause_review_batch"
    return common_df.reset_index(drop=True)


def build_review_batch(root: Path) -> pd.DataFrame:
    base_df = build_base_universe(root)
    positive_batch = select_positive_batch(base_df)
    monitor_batch = select_monitor_batch(base_df)
    common_batch = select_common_cause_batch(base_df)
    batch = pd.concat([positive_batch, monitor_batch, common_batch], ignore_index=True)
    if batch.empty:
        return pd.DataFrame(columns=BATCH_COLS)

    action_values = batch["candidate_class"].map(assign_review_action)
    batch["suggested_label_action"] = action_values.map(lambda item: item[0])
    batch["suggested_label_action_reason_ko"] = action_values.map(lambda item: item[1])
    batch["review_priority_reason_ko"] = batch.apply(
        lambda row: assign_priority_reason(str(row["selection_source"]), row), axis=1
    )

    batch["_track_order"] = batch["review_track"].map(TRACK_ORDER).fillna(99)
    batch["_priority_order"] = batch["candidate_priority_band"].map(PRIORITY_ORDER).fillna(99)
    batch = batch.sort_values(
        [
            "_track_order",
            "_priority_order",
            "site_positive_gap_flag",
            "electrical_core_minus_broadshape_050",
            "run_day_count",
            "site",
            "panel_id",
            "run_start_date",
            "run_end_date",
        ],
        ascending=[True, True, False, False, False, True, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    batch["review_priority_rank"] = batch.groupby("review_track", dropna=False).cumcount() + 1
    batch = batch.drop(columns=["_track_order", "_priority_order"], errors="ignore")
    return batch


def build_truth_overlap_fields(batch_df: pd.DataFrame, reaudit_df: pd.DataFrame) -> tuple[list[str], list[str]]:
    overlap_case_ids: list[str] = []
    overlap_validities: list[str] = []
    for row in batch_df.itertuples(index=False):
        run_start = parse_date(getattr(row, "run_start_date"))
        run_end = parse_date(getattr(row, "run_end_date"))
        if pd.isna(run_start) or pd.isna(run_end):
            overlap_case_ids.append("")
            overlap_validities.append("")
            continue
        lower = run_start - pd.Timedelta(days=TRUTH_OVERLAP_TOLERANCE_DAYS)
        upper = run_end + pd.Timedelta(days=TRUTH_OVERLAP_TOLERANCE_DAYS)
        matches = reaudit_df.loc[
            reaudit_df["site"].eq(getattr(row, "site"))
            & reaudit_df["panel_id"].eq(getattr(row, "panel_id"))
            & reaudit_df["strict_trigger_date"].notna()
            & reaudit_df["strict_trigger_date"].between(lower, upper),
            :,
        ].copy()
        case_ids = matches["truth_case_id"].map(normalize_text).tolist()
        validities = matches["candidate_validity"].map(normalize_text).tolist()
        overlap_case_ids.append(join_unique_csv(case_ids))
        overlap_validities.append(join_unique_csv(validities))
    return overlap_case_ids, overlap_validities


def build_evidence(batch_df: pd.DataFrame, root: Path) -> pd.DataFrame:
    if batch_df.empty:
        return pd.DataFrame(columns=EVIDENCE_COLS)

    reaudit_df = load_reaudit(root)
    evidence = batch_df.copy()
    truth_case_ids, truth_validities = build_truth_overlap_fields(evidence, reaudit_df)
    evidence["overlapping_truth_case_ids_reaudit"] = truth_case_ids
    evidence["overlapping_truth_candidate_validities_reaudit"] = truth_validities

    combined_case_ids: list[str] = []
    combined_validities: list[str] = []
    for row in evidence.itertuples(index=False):
        case_values = split_csv_values(getattr(row, "future_truth_case_ids", "")) + split_csv_values(
            getattr(row, "overlapping_truth_case_ids_reaudit", "")
        )
        validity_values = split_csv_values(getattr(row, "future_truth_candidate_validities", "")) + split_csv_values(
            getattr(row, "overlapping_truth_candidate_validities_reaudit", "")
        )
        combined_case_ids.append(join_unique_csv(case_values))
        combined_validities.append(join_unique_csv(validity_values))

    evidence["overlapping_truth_case_ids"] = combined_case_ids
    evidence["overlapping_truth_candidate_validities"] = combined_validities
    evidence["future_fault_linked_ref_flag"] = (
        evidence["fate_future_fault_ref_flag"]
        | evidence["watch_now_future_fault_ref_flag"]
        | evidence["watch_review_future_fault_ref_flag"]
    ).astype(int)
    evidence["future_truth_linked_ref_flag"] = (
        evidence["fate_future_truth_ref_flag"]
        | evidence["watch_now_future_truth_ref_flag"]
        | evidence["watch_review_future_truth_ref_flag"]
    ).astype(int)

    def evidence_reason(row: pd.Series) -> str:
        if normalize_text(row["overlapping_truth_case_ids"]) != "":
            return "근접 truth overlap 또는 future truth reference가 있어 review 근거가 비교적 명확함"
        if int(row["future_fault_linked_ref_flag"]) == 1 or int(row["future_truth_linked_ref_flag"]) == 1:
            return "future linkage reference가 있어 라벨 승격/제외 판단 보조 근거가 있음"
        if int(row["watch_now_panel_ref_flag"]) == 1:
            return "operator watch_now panel 연관이 있어 수동 검토 가치가 높음"
        if int(row["watch_review_run_ref_flag"]) == 1:
            return "operator watch_review run 연관이 있어 검토 우선순위가 올라감"
        if normalize_text(row["candidate_class"]) == "monitor_review_candidate":
            return "monitor-like run이라 recurrence burden 확인 중심의 검토가 필요함"
        if normalize_text(row["candidate_class"]) == "common_cause_review_candidate":
            return "common-cause descriptive run이라 routing 확인 중심의 검토가 필요함"
        return "score 상위 unlabeled run이라 추가 라벨 검토 가치가 있음"

    evidence["review_evidence_reason_ko"] = evidence.apply(evidence_reason, axis=1)
    return evidence.reindex(columns=EVIDENCE_COLS)


def build_summary(batch_df: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []

    def append_summary(record_type: str, site: str, subset: pd.DataFrame) -> None:
        if subset.empty:
            site_positive_gap_flag = 0
            site_negative_gap_flag = 0
        elif record_type == "overall":
            site_positive_gap_flag = int(subset["site_positive_gap_flag"].max())
            site_negative_gap_flag = int(subset["site_negative_gap_flag"].max())
        else:
            site_positive_gap_flag = int(subset["site_positive_gap_flag"].iloc[0])
            site_negative_gap_flag = int(subset["site_negative_gap_flag"].iloc[0])

        records.append(
            {
                "record_type": record_type,
                "site": site,
                "positive_review_batch_count": int(subset["review_track"].astype(str).eq("positive_review_batch").sum()),
                "monitor_review_batch_count": int(subset["review_track"].astype(str).eq("monitor_review_batch").sum()),
                "common_cause_review_batch_count": int(
                    subset["review_track"].astype(str).eq("common_cause_review_batch").sum()
                ),
                "p1_included_count": int(subset["candidate_priority_band"].astype(str).eq("P1").sum()),
                "p2_included_count": int(subset["candidate_priority_band"].astype(str).eq("P2").sum()),
                "site_positive_gap_flag": site_positive_gap_flag,
                "site_negative_gap_flag": site_negative_gap_flag,
                "note_ko": (
                    "P1 전량 + site별 상위 P2 + global top-up, monitor/common-cause는 별도 track 유지"
                    if record_type == "overall"
                    else "site별 review batch 구성"
                ),
            }
        )

    append_summary("overall", "", batch_df)
    for site, site_df in batch_df.groupby("site", sort=True):
        append_summary("site", str(site), site_df.reset_index(drop=True))
    return pd.DataFrame(records).reindex(columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    batch_df = build_review_batch(root)
    evidence_df = build_evidence(batch_df, root)
    summary_df = build_summary(batch_df)

    batch_out = batch_df.reindex(columns=BATCH_COLS)

    batch_out.to_csv(share_dir / BATCH_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    evidence_df.to_csv(share_dir / EVIDENCE_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
