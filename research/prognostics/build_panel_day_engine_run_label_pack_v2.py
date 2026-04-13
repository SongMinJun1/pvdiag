#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
LABEL_PACK_V1_NAME = "panel_day_engine_run_label_pack_v1.csv"
TAXONOMY_V2_NAME = "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv"
PRECURSOR_ONSET_TRUTH_NAME = "panel_day_engine_precursor_onset_truth_v1.csv"
PRECURSOR_PERFORMANCE_NAME = "panel_day_engine_precursor_performance_cases_v1.csv"
NON_PRECURSOR_PERFORMANCE_NAME = "panel_day_engine_non_precursor_performance_cases_v1.csv"
COMMON_CAUSE_RETROFIT_NAME = "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv"
FATE_CASES_NAME = "panel_day_engine_local_seed_carry_fate_cases_v1.csv"

LABEL_PACK_V2_OUTPUT_NAME = "panel_day_engine_run_label_pack_v2.csv"
SUMMARY_V2_OUTPUT_NAME = "panel_day_engine_run_label_pack_summary_v2.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
FEATURE_REQUIRED_COLS = [
    *KEY_COLS,
    "run_day_count",
    "run_shape_class",
    "overlap_case_class",
    "delta_run_class",
    "fate_class",
    "cohort_hint",
    "recurring_run_within_60d",
    "future_fault_linked_flag",
    "future_truth_linked_flag",
]
V1_REQUIRED_COLS = [
    *KEY_COLS,
    "label_bucket",
    "training_label",
    "label_confidence",
    "label_sources_csv",
    "label_reason_ko",
]
FATE_REQUIRED_COLS = [*KEY_COLS, "fate_class"]
TAXONOMY_REQUIRED_COLS = ["eval_bucket_v2"]
ONSET_REQUIRED_COLS = ["site", "panel_id", "fault_start_date", "preferred_precursor_onset_date"]
PRECURSOR_PERFORMANCE_REQUIRED_COLS = ["site", "panel_id", "fault_start_date", "preferred_precursor_onset_date"]
NON_PRECURSOR_REQUIRED_COLS = [
    "eval_bucket_v2",
    "site",
    "panel_id",
    "anchor_date",
    "final_fault_hit_by_anchor_flag",
    "final_fault_hit_within_3d_after_flag",
]
COMMON_CAUSE_REQUIRED_COLS = ["eval_bucket_v2", "site", "panel_id", "anchor_date", "combined_marker_flag"]

CASE_OVERLAP_TOLERANCE_DAYS = 5

OUTPUT_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "overlap_case_class",
    "delta_run_class",
    "cohort_hint",
    "fate_class",
    "recurring_run_within_60d",
    "future_fault_linked_flag",
    "future_truth_linked_flag",
    "label_bucket",
    "training_label",
    "label_confidence",
    "label_sources_csv",
    "label_reason_ko",
    "precursor_onset_support_flag",
    "precursor_performance_support_flag",
    "abrupt_positive_case_flag",
    "abrupt_hit_by_anchor_flag",
    "abrupt_hit_within_3d_flag",
    "common_cause_descriptive_case_flag",
    "label_bucket_v2",
    "training_label_v2",
    "label_confidence_v2",
    "label_sources_csv_v2",
    "label_reason_ko_v2",
]

SUMMARY_COLS = [
    "record_type",
    "site",
    "total_run_count",
    "positive_like_count",
    "negative_like_count",
    "monitor_like_count",
    "common_cause_like_count",
    "unlabeled_other_count",
    "positive_training_count",
    "negative_training_count",
    "excluded_training_count",
    "strong_label_count",
    "medium_label_count",
    "weak_label_count",
    "positive_training_increment_vs_v1",
    "negative_training_increment_vs_v1",
]

REQUIRED_EVAL_BUCKETS = {
    "precursor_bearing_detectable_now",
    "abrupt_or_no_precursor_now",
    "non_panel_or_common_cause",
    "unknown_needs_review",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build run-level label pack v2 using the completed taxonomy/onset/performance/common-cause audit stack."
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


def to_int_flag(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"", "0", "0.0", "false", "f", "no", "n"}:
        return 0
    if text in {"1", "1.0", "true", "t", "yes", "y"}:
        return 1
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return int(bool(numeric)) if not pd.isna(numeric) else 0


def parse_date(value: object) -> pd.Timestamp:
    text = normalize_date_text(value)
    if text == "":
        return pd.NaT
    return pd.to_datetime(text, errors="coerce")


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


def normalize_run_keys(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["site"] = out["site"].map(normalize_text)
    out["panel_id"] = out["panel_id"].map(normalize_text)
    out["run_start_date"] = out["run_start_date"].map(normalize_date_text)
    out["run_end_date"] = out["run_end_date"].map(normalize_date_text)
    return out


def normalize_panel_anchor_keys(df: pd.DataFrame, *, date_col: str) -> pd.DataFrame:
    out = df.copy()
    out["site"] = out["site"].map(normalize_text)
    out["panel_id"] = out["panel_id"].map(normalize_text)
    out[date_col] = out[date_col].map(parse_date)
    return out


def normalize_panel_window_keys(df: pd.DataFrame, *, start_col: str, end_col: str) -> pd.DataFrame:
    out = df.copy()
    out["site"] = out["site"].map(normalize_text)
    out["panel_id"] = out["panel_id"].map(normalize_text)
    out[start_col] = out[start_col].map(parse_date)
    out[end_col] = out[end_col].map(parse_date)
    return out


def load_feature_table(root: Path) -> pd.DataFrame:
    path = root / "_share" / FEATURE_TABLE_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, FEATURE_REQUIRED_COLS, path.name)
    df = normalize_run_keys(df)
    for col in ["run_shape_class", "overlap_case_class", "delta_run_class", "fate_class", "cohort_hint"]:
        df[col] = df[col].map(normalize_text)
    for col in ["run_day_count", "recurring_run_within_60d", "future_fault_linked_flag", "future_truth_linked_flag"]:
        df[col] = df[col].map(to_int_flag).astype(int)
    return df.loc[:, FEATURE_REQUIRED_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_label_pack_v1(root: Path) -> pd.DataFrame:
    path = root / "_share" / LABEL_PACK_V1_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, V1_REQUIRED_COLS, path.name)
    df = normalize_run_keys(df)
    for col in ["label_bucket", "training_label", "label_confidence", "label_sources_csv", "label_reason_ko"]:
        df[col] = df[col].map(normalize_text)
    return df.loc[:, V1_REQUIRED_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_fate_cases(root: Path) -> pd.DataFrame:
    path = root / "_share" / FATE_CASES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, FATE_REQUIRED_COLS, path.name)
    df = normalize_run_keys(df)
    df["fate_class"] = df["fate_class"].map(normalize_text)
    return df.loc[:, FATE_REQUIRED_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_taxonomy_eval_buckets(root: Path) -> pd.DataFrame:
    path = root / "_share" / TAXONOMY_V2_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, TAXONOMY_REQUIRED_COLS, path.name)
    df["eval_bucket_v2"] = df["eval_bucket_v2"].map(normalize_text)
    available = set(df["eval_bucket_v2"].tolist())
    missing = sorted(REQUIRED_EVAL_BUCKETS - available)
    if missing:
        raise SystemExit(f"{path.name} missing eval buckets: {missing}")
    return df


def load_precursor_onset_truth(root: Path) -> pd.DataFrame:
    path = root / "_share" / PRECURSOR_ONSET_TRUTH_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, ONSET_REQUIRED_COLS, path.name)
    df = normalize_panel_window_keys(df, start_col="preferred_precursor_onset_date", end_col="fault_start_date")
    return df.loc[
        df["preferred_precursor_onset_date"].notna() & df["fault_start_date"].notna(),
        ["site", "panel_id", "preferred_precursor_onset_date", "fault_start_date"],
    ].drop_duplicates(ignore_index=True)


def load_precursor_performance_cases(root: Path) -> pd.DataFrame:
    path = root / "_share" / PRECURSOR_PERFORMANCE_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, PRECURSOR_PERFORMANCE_REQUIRED_COLS, path.name)
    df = normalize_panel_window_keys(df, start_col="preferred_precursor_onset_date", end_col="fault_start_date")
    return df.loc[
        df["preferred_precursor_onset_date"].notna() & df["fault_start_date"].notna(),
        ["site", "panel_id", "preferred_precursor_onset_date", "fault_start_date"],
    ].drop_duplicates(ignore_index=True)


def load_non_precursor_cases(root: Path) -> pd.DataFrame:
    path = root / "_share" / NON_PRECURSOR_PERFORMANCE_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, NON_PRECURSOR_REQUIRED_COLS, path.name)
    df = normalize_panel_anchor_keys(df, date_col="anchor_date")
    df["eval_bucket_v2"] = df["eval_bucket_v2"].map(normalize_text)
    df["final_fault_hit_by_anchor_flag"] = df["final_fault_hit_by_anchor_flag"].map(to_int_flag).astype(int)
    df["final_fault_hit_within_3d_after_flag"] = df["final_fault_hit_within_3d_after_flag"].map(to_int_flag).astype(int)
    return df.loc[:, NON_PRECURSOR_REQUIRED_COLS].drop_duplicates(ignore_index=True)


def load_common_cause_retrofit_cases(root: Path) -> pd.DataFrame:
    path = root / "_share" / COMMON_CAUSE_RETROFIT_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, COMMON_CAUSE_REQUIRED_COLS, path.name)
    df = normalize_panel_anchor_keys(df, date_col="anchor_date")
    df["eval_bucket_v2"] = df["eval_bucket_v2"].map(normalize_text)
    df["combined_marker_flag"] = df["combined_marker_flag"].map(to_int_flag).astype(int)
    return df.loc[:, COMMON_CAUSE_REQUIRED_COLS].drop_duplicates(ignore_index=True)


def add_window_overlap_flag(
    runs_df: pd.DataFrame,
    cases_df: pd.DataFrame,
    *,
    start_col: str,
    end_col: str,
    flag_col: str,
) -> None:
    runs_df[flag_col] = 0
    if cases_df.empty:
        return
    for row in cases_df.itertuples(index=False):
        start_date = getattr(row, start_col)
        end_date = getattr(row, end_col)
        if pd.isna(start_date) or pd.isna(end_date):
            continue
        mask = (
            runs_df["site"].eq(getattr(row, "site"))
            & runs_df["panel_id"].eq(getattr(row, "panel_id"))
            & runs_df["_run_start_dt"].le(end_date)
            & runs_df["_run_end_dt"].ge(start_date)
        )
        runs_df.loc[mask, flag_col] = 1
    runs_df[flag_col] = runs_df[flag_col].astype(int)


def add_abrupt_positive_flags(runs_df: pd.DataFrame, cases_df: pd.DataFrame) -> None:
    runs_df["abrupt_hit_by_anchor_flag"] = 0
    runs_df["abrupt_hit_within_3d_flag"] = 0
    if cases_df.empty:
        runs_df["abrupt_positive_case_flag"] = 0
        return

    abrupt_df = cases_df.loc[
        cases_df["eval_bucket_v2"].eq("abrupt_or_no_precursor_now")
        & (
            cases_df["final_fault_hit_by_anchor_flag"].eq(1)
            | cases_df["final_fault_hit_within_3d_after_flag"].eq(1)
        )
    ].copy()
    for row in abrupt_df.itertuples(index=False):
        if pd.isna(row.anchor_date):
            continue
        lower = row.anchor_date - pd.Timedelta(days=CASE_OVERLAP_TOLERANCE_DAYS)
        upper = row.anchor_date + pd.Timedelta(days=CASE_OVERLAP_TOLERANCE_DAYS)
        mask = (
            runs_df["site"].eq(row.site)
            & runs_df["panel_id"].eq(row.panel_id)
            & runs_df["_run_start_dt"].le(upper)
            & runs_df["_run_end_dt"].ge(lower)
        )
        if row.final_fault_hit_by_anchor_flag == 1:
            runs_df.loc[mask, "abrupt_hit_by_anchor_flag"] = 1
        if row.final_fault_hit_within_3d_after_flag == 1:
            runs_df.loc[mask, "abrupt_hit_within_3d_flag"] = 1

    runs_df["abrupt_hit_by_anchor_flag"] = runs_df["abrupt_hit_by_anchor_flag"].astype(int)
    runs_df["abrupt_hit_within_3d_flag"] = runs_df["abrupt_hit_within_3d_flag"].astype(int)
    runs_df["abrupt_positive_case_flag"] = (
        runs_df["abrupt_hit_by_anchor_flag"].eq(1) | runs_df["abrupt_hit_within_3d_flag"].eq(1)
    ).astype(int)


def add_common_cause_flags(runs_df: pd.DataFrame, cases_df: pd.DataFrame) -> None:
    runs_df["common_cause_descriptive_case_flag"] = 0
    if cases_df.empty:
        return

    common_df = cases_df.loc[
        cases_df["eval_bucket_v2"].eq("non_panel_or_common_cause") & cases_df["combined_marker_flag"].eq(1)
    ].copy()
    for row in common_df.itertuples(index=False):
        if pd.isna(row.anchor_date):
            continue
        lower = row.anchor_date - pd.Timedelta(days=CASE_OVERLAP_TOLERANCE_DAYS)
        upper = row.anchor_date + pd.Timedelta(days=CASE_OVERLAP_TOLERANCE_DAYS)
        mask = (
            runs_df["site"].eq(row.site)
            & runs_df["panel_id"].eq(row.panel_id)
            & runs_df["_run_start_dt"].le(upper)
            & runs_df["_run_end_dt"].ge(lower)
        )
        runs_df.loc[mask, "common_cause_descriptive_case_flag"] = 1
    runs_df["common_cause_descriptive_case_flag"] = runs_df["common_cause_descriptive_case_flag"].astype(int)


def merge_evidence(root: Path) -> pd.DataFrame:
    feature_df = load_feature_table(root)
    v1_df = load_label_pack_v1(root)
    fate_df = load_fate_cases(root)
    load_taxonomy_eval_buckets(root)
    onset_truth_df = load_precursor_onset_truth(root)
    precursor_perf_df = load_precursor_performance_cases(root)
    non_precursor_df = load_non_precursor_cases(root)
    common_cause_df = load_common_cause_retrofit_cases(root)

    merged = feature_df.merge(v1_df, on=KEY_COLS, how="left")
    merged = merged.merge(fate_df, on=KEY_COLS, how="left", suffixes=("", "_fate"))
    merged["fate_class"] = merged["fate_class"].where(
        merged["fate_class"].map(normalize_text).ne(""),
        merged["fate_class_fate"].map(normalize_text),
    )
    merged["fate_class"] = merged["fate_class"].map(normalize_text)
    merged = merged.drop(columns=[col for col in ["fate_class_fate"] if col in merged.columns], errors="ignore")

    merged["_run_start_dt"] = merged["run_start_date"].map(parse_date)
    merged["_run_end_dt"] = merged["run_end_date"].map(parse_date)

    add_window_overlap_flag(
        merged,
        onset_truth_df,
        start_col="preferred_precursor_onset_date",
        end_col="fault_start_date",
        flag_col="precursor_onset_support_flag",
    )
    add_window_overlap_flag(
        merged,
        precursor_perf_df,
        start_col="preferred_precursor_onset_date",
        end_col="fault_start_date",
        flag_col="precursor_performance_support_flag",
    )
    add_abrupt_positive_flags(merged, non_precursor_df)
    add_common_cause_flags(merged, common_cause_df)

    for col in [
        "label_bucket",
        "training_label",
        "label_confidence",
        "label_sources_csv",
        "label_reason_ko",
    ]:
        merged[col] = merged[col].fillna("").map(normalize_text)

    merged = merged.drop(columns=["_run_start_dt", "_run_end_dt"], errors="ignore")
    return merged


def assign_label_row_v2(row: pd.Series) -> dict[str, str]:
    cohort_hint = normalize_text(row["cohort_hint"])
    fate_class = normalize_text(row["fate_class"])
    future_fault = int(row["future_fault_linked_flag"]) == 1
    future_truth = int(row["future_truth_linked_flag"]) == 1
    abrupt_by_anchor = int(row["abrupt_hit_by_anchor_flag"]) == 1
    abrupt_within_3d = int(row["abrupt_hit_within_3d_flag"]) == 1
    common_cause = int(row["common_cause_descriptive_case_flag"]) == 1

    source_tags: list[str] = []
    if cohort_hint == "eligible_local":
        source_tags.append("eligible_local")
    if future_fault:
        source_tags.append("future_fault_linked")
    if future_truth:
        source_tags.append("future_truth_linked")
    if abrupt_by_anchor:
        source_tags.append("abrupt_hit_by_anchor")
    if abrupt_within_3d:
        source_tags.append("abrupt_hit_within_3d")
    if cohort_hint == "nuisance_alert":
        source_tags.append("nuisance_alert")
    if fate_class == "isolated_unexplained":
        source_tags.append("isolated_unexplained")
    if cohort_hint == "recurring_monitor_like" or fate_class == "recurring_chronic_monitor_like":
        source_tags.append("recurring_monitor_like")
    if common_cause:
        source_tags.append("common_cause_descriptive")

    if cohort_hint == "eligible_local" or future_fault or future_truth or abrupt_by_anchor or abrupt_within_3d:
        label_bucket_v2 = "positive_like"
        training_label_v2 = "positive"
        if cohort_hint == "eligible_local" or future_fault or future_truth or abrupt_by_anchor:
            label_confidence_v2 = "strong"
        else:
            label_confidence_v2 = "medium"
        if abrupt_by_anchor or abrupt_within_3d:
            label_reason_ko_v2 = "전조 linkage 또는 적시 abrupt hit"
        else:
            label_reason_ko_v2 = "전조 eligible 또는 후행 fault linkage"
    elif cohort_hint == "nuisance_alert" or fate_class == "isolated_unexplained":
        label_bucket_v2 = "negative_like"
        training_label_v2 = "negative"
        label_confidence_v2 = "medium"
        label_reason_ko_v2 = "nuisance 또는 isolated burden"
    elif cohort_hint == "recurring_monitor_like" or fate_class == "recurring_chronic_monitor_like":
        label_bucket_v2 = "monitor_like"
        training_label_v2 = "exclude"
        label_confidence_v2 = "medium"
        label_reason_ko_v2 = "반복 chronic monitor형"
    elif common_cause:
        label_bucket_v2 = "common_cause_like"
        training_label_v2 = "exclude"
        label_confidence_v2 = "medium"
        label_reason_ko_v2 = "공통원인 설명형 run"
    else:
        label_bucket_v2 = "unlabeled_other"
        training_label_v2 = "exclude"
        label_confidence_v2 = "weak"
        label_reason_ko_v2 = "아직 라벨 부족"

    if not source_tags:
        source_tags.append("unmatched_other")

    return {
        "label_bucket_v2": label_bucket_v2,
        "training_label_v2": training_label_v2,
        "label_confidence_v2": label_confidence_v2,
        "label_sources_csv_v2": ",".join(dict.fromkeys(source_tags)),
        "label_reason_ko_v2": label_reason_ko_v2,
    }


def build_label_pack_v2(root: Path) -> pd.DataFrame:
    merged = merge_evidence(root).copy()
    label_rows = [assign_label_row_v2(row) for _, row in merged.iterrows()]
    label_df = pd.DataFrame(label_rows, index=merged.index)
    out = pd.concat([merged, label_df], axis=1)
    out = out.sort_values(KEY_COLS, kind="stable").reset_index(drop=True)
    return out.reindex(columns=OUTPUT_COLS)


def count_eq(df: pd.DataFrame, col: str, value: str) -> int:
    return int(df[col].astype(str).eq(value).sum())


def v1_training_counts(df: pd.DataFrame) -> tuple[int, int]:
    return (
        count_eq(df, "training_label", "positive"),
        count_eq(df, "training_label", "negative"),
    )


def build_summary(label_pack_v2_df: pd.DataFrame, label_pack_v1_df: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []

    def append_summary(record_type: str, site: str, subset_v2: pd.DataFrame, subset_v1: pd.DataFrame) -> None:
        v1_positive, v1_negative = v1_training_counts(subset_v1)
        v2_positive = count_eq(subset_v2, "training_label_v2", "positive")
        v2_negative = count_eq(subset_v2, "training_label_v2", "negative")
        records.append(
            {
                "record_type": record_type,
                "site": site,
                "total_run_count": int(len(subset_v2)),
                "positive_like_count": count_eq(subset_v2, "label_bucket_v2", "positive_like"),
                "negative_like_count": count_eq(subset_v2, "label_bucket_v2", "negative_like"),
                "monitor_like_count": count_eq(subset_v2, "label_bucket_v2", "monitor_like"),
                "common_cause_like_count": count_eq(subset_v2, "label_bucket_v2", "common_cause_like"),
                "unlabeled_other_count": count_eq(subset_v2, "label_bucket_v2", "unlabeled_other"),
                "positive_training_count": v2_positive,
                "negative_training_count": v2_negative,
                "excluded_training_count": count_eq(subset_v2, "training_label_v2", "exclude"),
                "strong_label_count": count_eq(subset_v2, "label_confidence_v2", "strong"),
                "medium_label_count": count_eq(subset_v2, "label_confidence_v2", "medium"),
                "weak_label_count": count_eq(subset_v2, "label_confidence_v2", "weak"),
                "positive_training_increment_vs_v1": int(v2_positive - v1_positive),
                "negative_training_increment_vs_v1": int(v2_negative - v1_negative),
            }
        )

    append_summary("overall", "", label_pack_v2_df, label_pack_v1_df)
    for site, site_df in label_pack_v2_df.groupby("site", sort=True):
        site_v1_df = label_pack_v1_df.loc[label_pack_v1_df["site"].eq(str(site))].reset_index(drop=True)
        append_summary("site", str(site), site_df.reset_index(drop=True), site_v1_df)

    return pd.DataFrame(records).reindex(columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    label_pack_v1_df = load_label_pack_v1(root)
    label_pack_v2_df = build_label_pack_v2(root)
    summary_df = build_summary(label_pack_v2_df, label_pack_v1_df)

    label_pack_v2_df.to_csv(share_dir / LABEL_PACK_V2_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_V2_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
