#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
ELIGIBILITY_CASES_NAME = "panel_day_engine_local_precursor_eligibility_cases_v1.csv"
PRE_EWS_REPLAY_NAME = "panel_day_engine_local_pre_ews_replay_cases_v1.csv"
FATE_CASES_NAME = "panel_day_engine_local_seed_carry_fate_cases_v1.csv"
DELTA_REGISTRY_NAME = "panel_day_engine_local_seed_carry_delta_run_registry_v1.csv"
WATCHLIST_NAME = "panel_day_engine_operator_run_watchlist_v1.csv"

LABEL_PACK_OUTPUT_NAME = "panel_day_engine_run_label_pack_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_run_label_pack_summary_v1.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
STRING_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_shape_class",
    "overlap_case_class",
    "delta_run_class",
    "fate_class",
    "cohort_hint",
]
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
FATE_REQUIRED_COLS = [*KEY_COLS, "fate_class", "recurring_run_within_60d"]
DELTA_REQUIRED_COLS = [*KEY_COLS]

LABEL_PACK_COLS = [
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
    "eligibility_case_flag",
    "pre_ews_replay_case_flag",
    "seed_carry_fate_case_flag",
    "delta_run_registry_flag",
    "operator_watchlist_flag",
    "watchlist_bucket",
    "watchlist_tier",
    "label_bucket",
    "training_label",
    "label_confidence",
    "label_sources_csv",
    "label_reason_ko",
]

SUMMARY_COLS = [
    "record_type",
    "site",
    "total_run_count",
    "positive_like_count",
    "nuisance_like_count",
    "monitor_like_count",
    "unlabeled_other_count",
    "positive_training_count",
    "negative_training_count",
    "excluded_training_count",
    "strong_label_count",
    "medium_label_count",
    "weak_label_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a reusable run-level label pack from current feature/cohort/fate/operator evidence."
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


def read_csv_if_exists(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
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
    out["run_start_date"] = out["run_start_date"].map(normalize_date)
    out["run_end_date"] = out["run_end_date"].map(normalize_date)
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


def load_panel_flag(root: Path, file_name: str, *, flag_col_name: str, source_cols: list[str], flag_logic: str = "any") -> pd.DataFrame:
    path = root / "_share" / file_name
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, ["site", "panel_id", *source_cols], path.name)
    df["site"] = df["site"].map(normalize_text)
    df["panel_id"] = df["panel_id"].map(normalize_text)
    if flag_logic == "any":
        flag = pd.Series(False, index=df.index)
        for col in source_cols:
            flag |= pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float).gt(0)
    else:
        flag = df[source_cols[0]].map(to_int_flag).astype(int).eq(1)
    out = df.loc[flag, ["site", "panel_id"]].drop_duplicates().copy()
    out[flag_col_name] = 1
    return out


def load_fate_cases(root: Path) -> pd.DataFrame:
    path = root / "_share" / FATE_CASES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, FATE_REQUIRED_COLS, path.name)
    df = normalize_run_keys(df)
    df["fate_class"] = df["fate_class"].map(normalize_text)
    df["recurring_run_within_60d"] = df["recurring_run_within_60d"].map(to_int_flag).astype(int)

    future_fault_cols = [
        "future_fault_linked_flag",
        "future_confirmed_fault_30d",
        "future_critical_fault_30d",
        "future_final_fault_30d",
        "future_confirmed_fault_60d",
        "future_critical_fault_60d",
        "future_final_fault_60d",
    ]
    future_truth_cols = [
        "future_truth_linked_flag",
        "future_truth_overlap_30d",
        "future_truth_overlap_60d",
    ]
    df["future_fault_linked_flag"] = 0
    for col in future_fault_cols:
        if col in df.columns:
            df["future_fault_linked_flag"] |= df[col].map(to_int_flag)
    df["future_truth_linked_flag"] = 0
    for col in future_truth_cols:
        if col in df.columns:
            df["future_truth_linked_flag"] |= df[col].map(to_int_flag)
    df["future_fault_linked_flag"] = df["future_fault_linked_flag"].astype(int)
    df["future_truth_linked_flag"] = df["future_truth_linked_flag"].astype(int)
    df["seed_carry_fate_case_flag"] = 1
    return df.loc[
        :,
        [
            *KEY_COLS,
            "fate_class",
            "recurring_run_within_60d",
            "future_fault_linked_flag",
            "future_truth_linked_flag",
            "seed_carry_fate_case_flag",
        ],
    ].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_delta_registry(root: Path) -> pd.DataFrame:
    path = root / "_share" / DELTA_REGISTRY_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, DELTA_REQUIRED_COLS, path.name)
    df = normalize_run_keys(df)
    if "version" in df.columns:
        df["version"] = df["version"].map(normalize_text)
        current_df = df.loc[df["version"].eq("current_seed_carry1")].copy()
        if not current_df.empty:
            df = current_df
    if "overlap_case_class" in df.columns:
        df["overlap_case_class"] = df["overlap_case_class"].map(normalize_text)
    else:
        df["overlap_case_class"] = ""
    if "delta_run_class" in df.columns:
        df["delta_run_class"] = df["delta_run_class"].map(normalize_text)
    else:
        df["delta_run_class"] = ""
    df["delta_run_registry_flag"] = 1
    return df.loc[:, [*KEY_COLS, "overlap_case_class", "delta_run_class", "delta_run_registry_flag"]].drop_duplicates(
        subset=KEY_COLS, keep="first"
    )


def load_watchlist_optional(root: Path) -> pd.DataFrame:
    path = root / "_share" / WATCHLIST_NAME
    df = read_csv_if_exists(path)
    if df is None:
        return pd.DataFrame(columns=[*KEY_COLS, "operator_watchlist_flag", "watchlist_bucket", "watchlist_tier"])
    df = drop_repeated_header_rows(df)
    ensure_columns(df, [*KEY_COLS, "watchlist_bucket", "watchlist_tier"], path.name)
    df = normalize_run_keys(df)
    df["watchlist_bucket"] = df["watchlist_bucket"].map(normalize_text)
    df["watchlist_tier"] = df["watchlist_tier"].map(normalize_text)
    df["operator_watchlist_flag"] = 1
    return df.loc[:, [*KEY_COLS, "operator_watchlist_flag", "watchlist_bucket", "watchlist_tier"]].drop_duplicates(
        subset=KEY_COLS, keep="first"
    )


def merge_evidence(root: Path) -> pd.DataFrame:
    feature_df = load_feature_table(root)
    eligibility_df = load_panel_flag(
        root,
        ELIGIBILITY_CASES_NAME,
        flag_col_name="eligibility_case_flag",
        source_cols=["precursor_eligible_flag"],
        flag_logic="direct",
    )
    replay_df = load_panel_flag(
        root,
        PRE_EWS_REPLAY_NAME,
        flag_col_name="pre_ews_replay_case_flag",
        source_cols=[
            "any_pre_ews_replay_hit_flag",
            "any_ews_warning_replay_hit_flag",
            "any_pre_alarm_replay_hit_flag",
        ],
    )
    fate_df = load_fate_cases(root)
    delta_df = load_delta_registry(root)
    watchlist_df = load_watchlist_optional(root)

    merged = feature_df.merge(delta_df, on=KEY_COLS, how="left", suffixes=("", "_registry"))
    merged = merged.merge(fate_df, on=KEY_COLS, how="left", suffixes=("", "_fate"))
    merged = merged.merge(eligibility_df, on=["site", "panel_id"], how="left")
    merged = merged.merge(replay_df, on=["site", "panel_id"], how="left")
    merged = merged.merge(watchlist_df, on=KEY_COLS, how="left")

    merged["overlap_case_class"] = merged["overlap_case_class"].where(
        merged["overlap_case_class"].map(normalize_text).ne(""),
        merged["overlap_case_class_registry"].map(normalize_text),
    )
    merged["delta_run_class"] = merged["delta_run_class"].where(
        merged["delta_run_class"].map(normalize_text).ne(""),
        merged["delta_run_class_registry"].map(normalize_text),
    )
    merged["fate_class"] = merged["fate_class"].where(
        merged["fate_class"].map(normalize_text).ne(""),
        merged["fate_class_fate"].map(normalize_text),
    )

    merged["recurring_run_within_60d"] = (
        merged["recurring_run_within_60d"].map(to_int_flag)
        | merged["recurring_run_within_60d_fate"].fillna(0).map(to_int_flag)
    ).astype(int)
    merged["future_fault_linked_flag"] = (
        merged["future_fault_linked_flag"].map(to_int_flag)
        | merged["future_fault_linked_flag_fate"].fillna(0).map(to_int_flag)
    ).astype(int)
    merged["future_truth_linked_flag"] = (
        merged["future_truth_linked_flag"].map(to_int_flag)
        | merged["future_truth_linked_flag_fate"].fillna(0).map(to_int_flag)
    ).astype(int)

    for col in [
        "eligibility_case_flag",
        "pre_ews_replay_case_flag",
        "seed_carry_fate_case_flag",
        "delta_run_registry_flag",
        "operator_watchlist_flag",
    ]:
        merged[col] = merged[col].fillna(0).map(to_int_flag).astype(int)
    for col in ["watchlist_bucket", "watchlist_tier"]:
        merged[col] = merged[col].fillna("").map(normalize_text)

    drop_cols = [
        "overlap_case_class_registry",
        "delta_run_class_registry",
        "fate_class_fate",
        "recurring_run_within_60d_fate",
        "future_fault_linked_flag_fate",
        "future_truth_linked_flag_fate",
    ]
    merged = merged.drop(columns=[col for col in drop_cols if col in merged.columns], errors="ignore")
    return merged


def assign_label_row(row: pd.Series) -> dict[str, str]:
    cohort_hint = normalize_text(row["cohort_hint"])
    fate_class = normalize_text(row["fate_class"])
    future_fault = int(row["future_fault_linked_flag"]) == 1
    future_truth = int(row["future_truth_linked_flag"]) == 1

    source_tags: list[str] = []
    if cohort_hint == "eligible_local":
        source_tags.append("eligible_local")
    if future_fault:
        source_tags.append("future_fault_linked")
    if future_truth:
        source_tags.append("future_truth_linked")
    if cohort_hint == "nuisance_alert":
        source_tags.append("nuisance_alert")
    if fate_class == "isolated_unexplained":
        source_tags.append("isolated_unexplained")
    if cohort_hint == "recurring_monitor_like" or fate_class == "recurring_chronic_monitor_like":
        source_tags.append("recurring_monitor_like")

    if cohort_hint == "eligible_local" or future_fault or future_truth:
        label_bucket = "positive_like"
        training_label = "positive"
        label_confidence = "strong"
        label_reason_ko = "전조 eligible 또는 후행 fault linkage"
    elif cohort_hint == "nuisance_alert" or fate_class == "isolated_unexplained":
        label_bucket = "nuisance_like"
        training_label = "negative"
        label_confidence = "medium"
        label_reason_ko = "nuisance 또는 isolated burden"
    elif cohort_hint == "recurring_monitor_like" or fate_class == "recurring_chronic_monitor_like":
        label_bucket = "monitor_like"
        training_label = "excluded"
        label_confidence = "medium"
        label_reason_ko = "반복 chronic monitor형"
    else:
        label_bucket = "unlabeled_other"
        training_label = "excluded"
        label_confidence = "weak"
        label_reason_ko = "아직 라벨 부족"

    if not source_tags:
        source_tags.append("unmatched_other")

    return {
        "label_bucket": label_bucket,
        "training_label": training_label,
        "label_confidence": label_confidence,
        "label_sources_csv": ",".join(dict.fromkeys(source_tags)),
        "label_reason_ko": label_reason_ko,
    }


def build_label_pack(root: Path) -> pd.DataFrame:
    merged = merge_evidence(root).copy()
    label_rows = [assign_label_row(row) for _, row in merged.iterrows()]
    label_df = pd.DataFrame(label_rows, index=merged.index)
    out = pd.concat([merged, label_df], axis=1)
    return out.reindex(columns=LABEL_PACK_COLS)


def count_eq(df: pd.DataFrame, col: str, value: str) -> int:
    return int(df[col].astype(str).eq(value).sum())


def build_summary(label_pack_df: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []

    def append_summary(record_type: str, site: str, subset: pd.DataFrame) -> None:
        records.append(
            {
                "record_type": record_type,
                "site": site,
                "total_run_count": int(len(subset)),
                "positive_like_count": count_eq(subset, "label_bucket", "positive_like"),
                "nuisance_like_count": count_eq(subset, "label_bucket", "nuisance_like"),
                "monitor_like_count": count_eq(subset, "label_bucket", "monitor_like"),
                "unlabeled_other_count": count_eq(subset, "label_bucket", "unlabeled_other"),
                "positive_training_count": count_eq(subset, "training_label", "positive"),
                "negative_training_count": count_eq(subset, "training_label", "negative"),
                "excluded_training_count": count_eq(subset, "training_label", "excluded"),
                "strong_label_count": count_eq(subset, "label_confidence", "strong"),
                "medium_label_count": count_eq(subset, "label_confidence", "medium"),
                "weak_label_count": count_eq(subset, "label_confidence", "weak"),
            }
        )

    append_summary("overall", "", label_pack_df)
    for site, site_df in label_pack_df.groupby("site", sort=True):
        append_summary("site", str(site), site_df.reset_index(drop=True))

    return pd.DataFrame(records).reindex(columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    label_pack = build_label_pack(root)
    summary = build_summary(label_pack)

    label_pack.to_csv(share_dir / LABEL_PACK_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
