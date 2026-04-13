#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
LABEL_PACK_V2_NAME = "panel_day_engine_run_label_pack_v2.csv"
V0_SCORES_NAME = "panel_day_engine_run_ranker_v0_scores.csv"
V2_HOLDOUT_SUMMARY_NAME = "panel_day_engine_run_ranker_v2_holdout_summary.csv"
WATCHLIST_NOW_PANELS_NAME = "panel_day_engine_operator_run_watchlist_now_panels_v1.csv"
WATCHLIST_REVIEW_NAME = "panel_day_engine_operator_run_watchlist_review_v1.csv"
COMMON_CAUSE_RETROFIT_NAME = "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv"

CANDIDATES_OUTPUT_NAME = "panel_day_engine_run_label_expansion_candidates_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_run_label_expansion_summary_v1.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
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
LABEL_REQUIRED_COLS = [*KEY_COLS, "label_bucket_v2", "training_label_v2"]
V0_REQUIRED_COLS = [*KEY_COLS, "electrical_core_score", "electrical_core_minus_broadshape_050"]
HOLDOUT_REQUIRED_COLS = [
    "score_name",
    "fold_type",
    "delta_mean_top20_positive_minus_negative_vs_v1",
]
WATCH_NOW_REQUIRED_COLS = ["site", "panel_id"]
WATCHLIST_REVIEW_REQUIRED_COLS = [*KEY_COLS]
COMMON_CAUSE_REQUIRED_COLS = ["eval_bucket_v2", "site", "panel_id", "combined_marker_flag"]

POSITIVE_REVIEW_SHAPES = {"medium_alert_run", "chronic_alert_run"}
PRIORITY_ORDER = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
CLASS_ORDER = {
    "positive_review_candidate": 1,
    "monitor_review_candidate": 2,
    "common_cause_review_candidate": 3,
    "low_priority_unlabeled": 4,
}

CANDIDATE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
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

SUMMARY_COLS = [
    "record_type",
    "site",
    "excluded_run_count",
    "positive_review_candidate_count",
    "monitor_review_candidate_count",
    "common_cause_review_candidate_count",
    "low_priority_unlabeled_count",
    "p1_count",
    "p2_count",
    "p3_count",
    "p4_count",
    "site_positive_gap_flag",
    "site_negative_gap_flag",
    "logistic_v2_loso_delta_top20_vs_v1",
    "logistic_v2_time_delta_top20_vs_v1",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Identify the highest-value excluded runs to expand labels for the next scorer iteration."
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


def load_label_pack_v2(root: Path) -> pd.DataFrame:
    path = root / "_share" / LABEL_PACK_V2_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, LABEL_REQUIRED_COLS, path.name)
    df = normalize_key_cols(df)
    df["label_bucket_v2"] = df["label_bucket_v2"].map(normalize_text)
    df["training_label_v2"] = df["training_label_v2"].map(normalize_text)
    return df.loc[:, LABEL_REQUIRED_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_v0_scores(root: Path) -> pd.DataFrame:
    path = root / "_share" / V0_SCORES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, V0_REQUIRED_COLS, path.name)
    df = normalize_key_cols(df)
    for col in ["electrical_core_score", "electrical_core_minus_broadshape_050"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, V0_REQUIRED_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_holdout_summary(root: Path) -> dict[str, float | None]:
    path = root / "_share" / V2_HOLDOUT_SUMMARY_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, HOLDOUT_REQUIRED_COLS, path.name)
    df["score_name"] = df["score_name"].map(normalize_text)
    df["fold_type"] = df["fold_type"].map(normalize_text)
    df["delta_mean_top20_positive_minus_negative_vs_v1"] = pd.to_numeric(
        df["delta_mean_top20_positive_minus_negative_vs_v1"], errors="coerce"
    )
    logistic_df = df.loc[df["score_name"].eq("logistic_v2_holdout")].copy()
    if logistic_df.empty:
        raise SystemExit(f"{path.name} missing logistic_v2_holdout rows")
    loso = logistic_df.loc[logistic_df["fold_type"].eq("leave_one_site_out"), "delta_mean_top20_positive_minus_negative_vs_v1"]
    time = logistic_df.loc[logistic_df["fold_type"].eq("time_holdout_70_30"), "delta_mean_top20_positive_minus_negative_vs_v1"]
    return {
        "logistic_v2_loso_delta_top20_vs_v1": None if loso.empty else float(loso.iloc[0]),
        "logistic_v2_time_delta_top20_vs_v1": None if time.empty else float(time.iloc[0]),
    }


def load_watch_now_panels(root: Path) -> pd.DataFrame:
    path = root / "_share" / WATCHLIST_NOW_PANELS_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, WATCH_NOW_REQUIRED_COLS, path.name)
    out = df.loc[:, WATCH_NOW_REQUIRED_COLS].copy()
    out["site"] = out["site"].map(normalize_text)
    out["panel_id"] = out["panel_id"].map(normalize_text)
    out["watch_now_panel_ref_flag"] = 1
    return out.drop_duplicates(subset=["site", "panel_id"], keep="first").reset_index(drop=True)


def load_watchlist_review(root: Path) -> pd.DataFrame:
    path = root / "_share" / WATCHLIST_REVIEW_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, WATCHLIST_REVIEW_REQUIRED_COLS, path.name)
    out = normalize_key_cols(df.loc[:, WATCHLIST_REVIEW_REQUIRED_COLS].copy())
    out["watch_review_run_ref_flag"] = 1
    return out.drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_common_cause_retrofit(root: Path) -> pd.DataFrame:
    path = root / "_share" / COMMON_CAUSE_RETROFIT_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, COMMON_CAUSE_REQUIRED_COLS, path.name)
    df["eval_bucket_v2"] = df["eval_bucket_v2"].map(normalize_text)
    df["site"] = df["site"].map(normalize_text)
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["combined_marker_flag"] = df["combined_marker_flag"].map(to_int_flag).astype(int)
    df = df.loc[
        df["eval_bucket_v2"].eq("non_panel_or_common_cause") & df["combined_marker_flag"].eq(1),
        ["site", "panel_id"],
    ].copy()
    df["common_cause_descriptive_ref_flag"] = 1
    return df.drop_duplicates(subset=["site", "panel_id"], keep="first").reset_index(drop=True)


def compute_site_coverage(label_df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        label_df.groupby("site", dropna=False)
        .agg(
            positive_training_count=("training_label_v2", lambda s: int(s.astype(str).eq("positive").sum())),
            negative_training_count=("training_label_v2", lambda s: int(s.astype(str).eq("negative").sum())),
            excluded_training_count=("training_label_v2", lambda s: int(s.astype(str).eq("exclude").sum())),
        )
        .reset_index()
    )
    grouped["site_positive_gap_flag"] = grouped["positive_training_count"].eq(0).astype(int)
    grouped["site_negative_gap_flag"] = grouped["negative_training_count"].eq(0).astype(int)
    return grouped


def assign_score_ranks(df: pd.DataFrame) -> pd.DataFrame:
    ranked = df.copy()
    ranked["_score_sort"] = pd.to_numeric(ranked["electrical_core_minus_broadshape_050"], errors="coerce").fillna(float("-inf"))
    ranked = ranked.sort_values(
        ["_score_sort", "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[False, False, True, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    ranked["global_score_rank"] = range(1, len(ranked) + 1)
    ranked["site_score_rank"] = ranked.groupby("site", dropna=False).cumcount() + 1
    return ranked.drop(columns=["_score_sort"])


def assign_candidate_class(row: pd.Series, global_top_cutoff_rank: int) -> str:
    label_bucket_v2 = normalize_text(row["label_bucket_v2"])
    run_shape_class = normalize_text(row["run_shape_class"])
    global_score_rank = int(row["global_score_rank"])
    site_score_rank = int(row["site_score_rank"])

    if label_bucket_v2 == "common_cause_like":
        return "common_cause_review_candidate"
    if label_bucket_v2 == "monitor_like":
        return "monitor_review_candidate"
    if (
        label_bucket_v2 == "unlabeled_other"
        and run_shape_class in POSITIVE_REVIEW_SHAPES
        and (global_score_rank <= global_top_cutoff_rank or site_score_rank <= 5)
    ):
        return "positive_review_candidate"
    return "low_priority_unlabeled"


def assign_priority_band(row: pd.Series) -> str:
    candidate_class = normalize_text(row["candidate_class"])
    site_positive_gap_flag = int(row["site_positive_gap_flag"])
    if candidate_class == "positive_review_candidate" and site_positive_gap_flag == 1:
        return "P1"
    if candidate_class == "positive_review_candidate":
        return "P2"
    if candidate_class in {"monitor_review_candidate", "common_cause_review_candidate"}:
        return "P3"
    return "P4"


def build_reason(row: pd.Series, global_top_cutoff_rank: int) -> str:
    candidate_class = normalize_text(row["candidate_class"])
    site_positive_gap_flag = int(row["site_positive_gap_flag"])
    watch_now_panel_ref_flag = int(row["watch_now_panel_ref_flag"])
    watch_review_run_ref_flag = int(row["watch_review_run_ref_flag"])
    global_score_rank = int(row["global_score_rank"])
    site_score_rank = int(row["site_score_rank"])

    if candidate_class == "common_cause_review_candidate":
        return "common-cause descriptive run이라 routing truth 검토 우선"
    if candidate_class == "monitor_review_candidate":
        return "monitor-like 제외 run이라 direct train 대신 monitor review 우선"
    if candidate_class == "positive_review_candidate":
        reason_bits = ["점수 상위 medium/chronic unlabeled run"]
        if site_positive_gap_flag == 1:
            reason_bits.append("site positive gap 보강 필요")
        if global_score_rank <= global_top_cutoff_rank:
            reason_bits.append("global top10% score")
        elif site_score_rank <= 5:
            reason_bits.append("site top5 score")
        if watch_now_panel_ref_flag == 1:
            reason_bits.append("watch_now panel 연관")
        elif watch_review_run_ref_flag == 1:
            reason_bits.append("watch_review run 연관")
        return ", ".join(reason_bits)
    return "shape/score 우선순위가 낮은 unlabeled run"


def build_candidates(root: Path) -> tuple[pd.DataFrame, dict[str, float | None]]:
    feature_df = load_feature_table(root)
    label_df = load_label_pack_v2(root)
    v0_df = load_v0_scores(root)
    holdout_context = load_holdout_summary(root)
    watch_now_df = load_watch_now_panels(root)
    watch_review_df = load_watchlist_review(root)
    common_cause_df = load_common_cause_retrofit(root)
    site_coverage_df = compute_site_coverage(label_df)

    universe = feature_df.merge(label_df, on=KEY_COLS, how="left", validate="one_to_one")
    universe = universe.merge(v0_df, on=KEY_COLS, how="left", validate="one_to_one")
    universe = universe.merge(site_coverage_df, on="site", how="left", validate="many_to_one")
    universe = universe.merge(watch_now_df, on=["site", "panel_id"], how="left", validate="many_to_one")
    universe = universe.merge(watch_review_df, on=KEY_COLS, how="left", validate="one_to_one")
    universe = universe.merge(common_cause_df, on=["site", "panel_id"], how="left", validate="many_to_one")

    for col in ["label_bucket_v2", "training_label_v2", "run_shape_class"]:
        universe[col] = universe[col].fillna("").map(normalize_text)
    for col in [
        "electrical_core_score",
        "electrical_core_minus_broadshape_050",
        "max_v_drop",
        "min_mid_v_ratio",
        "min_mid_ratio",
        "cond_evt_only_day_ratio",
        "ae_mid_or_hi_early_day_ratio",
        "mean_signal_count",
        "max_signal_count",
        "p95_recon_error",
    ]:
        universe[col] = pd.to_numeric(universe[col], errors="coerce")
    for col in [
        "site_positive_gap_flag",
        "site_negative_gap_flag",
        "watch_now_panel_ref_flag",
        "watch_review_run_ref_flag",
        "common_cause_descriptive_ref_flag",
    ]:
        universe[col] = universe[col].fillna(0).map(to_int_flag).astype(int)

    if universe["label_bucket_v2"].eq("").any():
        missing_count = int(universe["label_bucket_v2"].eq("").sum())
        raise SystemExit(f"missing v2 label rows for {missing_count} runs")
    if universe["electrical_core_minus_broadshape_050"].isna().any():
        missing_count = int(universe["electrical_core_minus_broadshape_050"].isna().sum())
        raise SystemExit(f"missing v0 broadshape scores for {missing_count} runs")

    ranked = assign_score_ranks(universe)
    excluded = ranked.loc[ranked["training_label_v2"].eq("exclude")].copy()
    global_top_cutoff_rank = max(1, int(math.ceil(len(ranked) * 0.10)))

    excluded["candidate_class"] = excluded.apply(
        lambda row: assign_candidate_class(row, global_top_cutoff_rank), axis=1
    )
    excluded["candidate_priority_band"] = excluded.apply(assign_priority_band, axis=1)
    excluded["expansion_reason_ko"] = excluded.apply(
        lambda row: build_reason(row, global_top_cutoff_rank), axis=1
    )

    excluded["_priority_order"] = excluded["candidate_priority_band"].map(PRIORITY_ORDER).fillna(99)
    excluded["_class_order"] = excluded["candidate_class"].map(CLASS_ORDER).fillna(99)
    excluded = excluded.sort_values(
        [
            "_priority_order",
            "site_positive_gap_flag",
            "electrical_core_minus_broadshape_050",
            "run_day_count",
            "_class_order",
            "site",
            "panel_id",
            "run_start_date",
            "run_end_date",
        ],
        ascending=[True, False, False, False, True, True, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    excluded = excluded.drop(columns=["_priority_order", "_class_order"], errors="ignore")

    return excluded.reindex(columns=CANDIDATE_COLS), holdout_context


def count_eq(df: pd.DataFrame, col: str, value: str) -> int:
    return int(df[col].astype(str).eq(value).sum())


def build_summary(candidates_df: pd.DataFrame, holdout_context: dict[str, float | None]) -> pd.DataFrame:
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
                "excluded_run_count": int(len(subset)),
                "positive_review_candidate_count": count_eq(subset, "candidate_class", "positive_review_candidate"),
                "monitor_review_candidate_count": count_eq(subset, "candidate_class", "monitor_review_candidate"),
                "common_cause_review_candidate_count": count_eq(
                    subset, "candidate_class", "common_cause_review_candidate"
                ),
                "low_priority_unlabeled_count": count_eq(subset, "candidate_class", "low_priority_unlabeled"),
                "p1_count": count_eq(subset, "candidate_priority_band", "P1"),
                "p2_count": count_eq(subset, "candidate_priority_band", "P2"),
                "p3_count": count_eq(subset, "candidate_priority_band", "P3"),
                "p4_count": count_eq(subset, "candidate_priority_band", "P4"),
                "site_positive_gap_flag": site_positive_gap_flag,
                "site_negative_gap_flag": site_negative_gap_flag,
                "logistic_v2_loso_delta_top20_vs_v1": holdout_context["logistic_v2_loso_delta_top20_vs_v1"],
                "logistic_v2_time_delta_top20_vs_v1": holdout_context["logistic_v2_time_delta_top20_vs_v1"],
            }
        )

    append_summary("overall", "", candidates_df)
    for site, site_df in candidates_df.groupby("site", sort=True):
        append_summary("site", str(site), site_df.reset_index(drop=True))
    return pd.DataFrame(records).reindex(columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    candidates_df, holdout_context = build_candidates(root)
    summary_df = build_summary(candidates_df, holdout_context)

    candidates_df.to_csv(share_dir / CANDIDATES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
