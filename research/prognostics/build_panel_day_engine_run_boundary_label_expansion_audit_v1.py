#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
LABEL_PACK_V2_NAME = "panel_day_engine_run_label_pack_v2.csv"
REFERENCE_GAP_CASES_NAME = "panel_day_engine_run_ranker_reference_gap_cases_v1.csv"
REVIEW_BATCH_NAME = "panel_day_engine_run_label_expansion_review_batch_v1.csv"
V0_SCORES_NAME = "panel_day_engine_run_ranker_v0_scores.csv"

CANDIDATES_OUTPUT_NAME = "panel_day_engine_run_boundary_label_expansion_candidates_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_run_boundary_label_expansion_summary_v1.csv"
PROTOTYPES_OUTPUT_NAME = "panel_day_engine_run_boundary_label_expansion_prototypes_v1.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
DISTANCE_FEATURE_COLS = [
    "run_day_count",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "electrical_core_minus_broadshape_050",
]
FEATURE_REQUIRED_COLS = [*KEY_COLS, "run_shape_class", *DISTANCE_FEATURE_COLS[:-1]]
LABEL_REQUIRED_COLS = [*KEY_COLS, "label_bucket_v2", "training_label_v2"]
REFERENCE_GAP_REQUIRED_COLS = [
    *KEY_COLS,
    "label_bucket_v2",
    "gap_class",
    "electrical_core_minus_broadshape_050",
    "global_score_rank",
    "site_score_rank",
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
REVIEW_BATCH_REQUIRED_COLS = [
    *KEY_COLS,
    "review_track",
    "candidate_priority_band",
]
V0_REQUIRED_COLS = [*KEY_COLS, "electrical_core_minus_broadshape_050"]

POSITIVE_BOUNDARY_GAP_CLASSES = {
    "positive_top50_global_not_top20",
    "positive_below_top50_global",
}
HARD_NEGATIVE_GAP_CLASS = "negative_top20_global"
HOLDOUT_BUCKETS = {"common_cause_like", "monitor_like"}

CANDIDATE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "label_bucket_v2",
    "candidate_class",
    "candidate_priority_band",
    "positive_boundary_distance",
    "hard_negative_distance",
    "boundary_margin",
    "electrical_core_minus_broadshape_050",
    "global_score_rank",
    "site_score_rank",
    "run_day_count",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "boundary_reason_ko",
]
PROTOTYPE_COLS = [
    "prototype_pool_name",
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "label_bucket_v2",
    "gap_class",
    "electrical_core_minus_broadshape_050",
    "global_score_rank",
    "site_score_rank",
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
SUMMARY_COLS = [
    "record_type",
    "site",
    "excluded_run_count",
    "positive_promotion_candidate_count",
    "hard_negative_review_candidate_count",
    "monitor_or_common_cause_holdout_count",
    "low_priority_unlabeled_count",
    "p1_count",
    "p2_count",
    "p3_count",
    "p4_count",
    "site_positive_gap_flag",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Identify narrow boundary-based label expansion candidates for the next run scorer iteration."
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
    for col in DISTANCE_FEATURE_COLS[:-1]:
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


def load_reference_gap_cases(root: Path) -> pd.DataFrame:
    path = root / "_share" / REFERENCE_GAP_CASES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REFERENCE_GAP_REQUIRED_COLS, path.name)
    df = normalize_key_cols(df)
    for col in ["label_bucket_v2", "gap_class", "run_shape_class"]:
        df[col] = df[col].map(normalize_text)
    numeric_cols = [col for col in REFERENCE_GAP_REQUIRED_COLS if col not in KEY_COLS and col not in {"label_bucket_v2", "gap_class", "run_shape_class"}]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, REFERENCE_GAP_REQUIRED_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_review_batch(root: Path) -> pd.DataFrame:
    path = root / "_share" / REVIEW_BATCH_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REVIEW_BATCH_REQUIRED_COLS, path.name)
    df = normalize_key_cols(df)
    df["review_track"] = df["review_track"].map(normalize_text)
    df["candidate_priority_band"] = df["candidate_priority_band"].map(normalize_text)
    df["in_existing_review_batch_flag"] = 1
    return (
        df.loc[:, [*KEY_COLS, "review_track", "candidate_priority_band", "in_existing_review_batch_flag"]]
        .drop_duplicates(subset=KEY_COLS, keep="first")
        .reset_index(drop=True)
    )


def load_v0_scores(root: Path) -> pd.DataFrame:
    path = root / "_share" / V0_SCORES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, V0_REQUIRED_COLS, path.name)
    df = normalize_key_cols(df)
    df["electrical_core_minus_broadshape_050"] = pd.to_numeric(df["electrical_core_minus_broadshape_050"], errors="coerce")
    return df.loc[:, V0_REQUIRED_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def compute_site_coverage(label_df: pd.DataFrame) -> pd.DataFrame:
    grouped = label_df.groupby("site", dropna=False)
    rows: list[dict[str, object]] = []
    for site, site_df in grouped:
        positive_training_count = int(site_df["training_label_v2"].eq("positive").sum())
        negative_training_count = int(site_df["training_label_v2"].eq("negative").sum())
        excluded_training_count = int(site_df["training_label_v2"].eq("exclude").sum())
        rows.append(
            {
                "site": normalize_text(site),
                "positive_training_count": positive_training_count,
                "negative_training_count": negative_training_count,
                "excluded_training_count": excluded_training_count,
                "site_positive_gap_flag": int(positive_training_count == 0),
            }
        )
    return pd.DataFrame(rows)


def compute_score_ranks(score_df: pd.DataFrame) -> pd.DataFrame:
    ordered = (
        score_df.sort_values(
            by=["electrical_core_minus_broadshape_050", "site", "panel_id", "run_start_date", "run_end_date"],
            ascending=[False, True, True, True, True],
            na_position="last",
        )
        .reset_index(drop=True)
        .copy()
    )
    ordered["global_score_rank"] = ordered.index + 1
    ordered["site_score_rank"] = (
        ordered.groupby("site", dropna=False)["electrical_core_minus_broadshape_050"]
        .rank(method="first", ascending=False, na_option="bottom")
        .astype(int)
    )
    return ordered.loc[:, [*KEY_COLS, "electrical_core_minus_broadshape_050", "global_score_rank", "site_score_rank"]]


def build_prototype_output(reference_gap_df: pd.DataFrame) -> pd.DataFrame:
    positive_df = reference_gap_df.loc[reference_gap_df["gap_class"].isin(POSITIVE_BOUNDARY_GAP_CLASSES)].copy()
    hard_negative_df = reference_gap_df.loc[reference_gap_df["gap_class"].eq(HARD_NEGATIVE_GAP_CLASS)].copy()
    if positive_df.empty:
        raise SystemExit("reference gap audit missing positive boundary prototypes")
    if hard_negative_df.empty:
        raise SystemExit("reference gap audit missing hard negative prototypes")

    positive_df["prototype_pool_name"] = "positive_boundary_prototype_pool"
    hard_negative_df["prototype_pool_name"] = "hard_negative_prototype_pool"
    prototypes = pd.concat([positive_df, hard_negative_df], ignore_index=True)
    return prototypes.loc[:, PROTOTYPE_COLS].reset_index(drop=True)


def robust_scale_combined(prototypes: pd.DataFrame, candidates: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    combined = pd.concat(
        [
            prototypes.loc[:, [*KEY_COLS, *DISTANCE_FEATURE_COLS]].assign(_row_source="prototype"),
            candidates.loc[:, [*KEY_COLS, *DISTANCE_FEATURE_COLS]].assign(_row_source="candidate"),
        ],
        ignore_index=True,
    )
    numeric = combined.loc[:, DISTANCE_FEATURE_COLS].apply(pd.to_numeric, errors="coerce")
    medians = numeric.median()
    q1 = numeric.quantile(0.25)
    q3 = numeric.quantile(0.75)
    iqr = (q3 - q1).replace(0, np.nan).fillna(1.0)
    filled = numeric.fillna(medians)
    scaled = (filled - medians) / iqr

    combined_scaled = pd.concat([combined.loc[:, [*KEY_COLS, "_row_source"]], scaled], axis=1)
    prototype_scaled = combined_scaled.loc[combined_scaled["_row_source"].eq("prototype")].drop(columns="_row_source").reset_index(drop=True)
    candidate_scaled = combined_scaled.loc[combined_scaled["_row_source"].eq("candidate")].drop(columns="_row_source").reset_index(drop=True)
    return prototype_scaled, candidate_scaled


def keyed_frame(df: pd.DataFrame, extra_cols: list[str]) -> pd.DataFrame:
    return df.loc[:, [*KEY_COLS, *extra_cols]].copy()


def make_key_tuple_frame(df: pd.DataFrame) -> pd.Series:
    return df[KEY_COLS].apply(tuple, axis=1)


def euclidean_min_distance(candidates: np.ndarray, prototypes: np.ndarray) -> np.ndarray:
    if prototypes.size == 0:
        return np.full((candidates.shape[0],), np.nan, dtype=float)
    deltas = candidates[:, None, :] - prototypes[None, :, :]
    distances = np.sqrt(np.sum(np.square(deltas), axis=2))
    return np.min(distances, axis=1)


def compute_boundary_distances(candidate_df: pd.DataFrame, prototype_output_df: pd.DataFrame) -> pd.DataFrame:
    prototype_scaled, candidate_scaled = robust_scale_combined(prototype_output_df, candidate_df)

    prototype_with_pool = prototype_output_df.loc[:, ["prototype_pool_name", *KEY_COLS]].merge(
        prototype_scaled,
        on=KEY_COLS,
        how="inner",
    )
    candidate_with_scale = candidate_df.loc[:, KEY_COLS].merge(candidate_scaled, on=KEY_COLS, how="inner")

    positive_proto = prototype_with_pool.loc[
        prototype_with_pool["prototype_pool_name"].eq("positive_boundary_prototype_pool"),
        DISTANCE_FEATURE_COLS,
    ].to_numpy(dtype=float)
    hard_negative_proto = prototype_with_pool.loc[
        prototype_with_pool["prototype_pool_name"].eq("hard_negative_prototype_pool"),
        DISTANCE_FEATURE_COLS,
    ].to_numpy(dtype=float)
    candidate_matrix = candidate_with_scale.loc[:, DISTANCE_FEATURE_COLS].to_numpy(dtype=float)

    positive_distances = euclidean_min_distance(candidate_matrix, positive_proto)
    hard_negative_distances = euclidean_min_distance(candidate_matrix, hard_negative_proto)

    out = candidate_df.copy()
    out["positive_boundary_distance"] = positive_distances
    out["hard_negative_distance"] = hard_negative_distances
    out["boundary_margin"] = out["hard_negative_distance"] - out["positive_boundary_distance"]
    return out


def classify_candidates(candidate_df: pd.DataFrame, total_scored_run_count: int) -> pd.DataFrame:
    out = candidate_df.copy()
    global_top_cutoff = max(1, int(math.ceil(total_scored_run_count * 0.15)))
    out["is_global_top15pct"] = out["global_score_rank"].le(global_top_cutoff).astype(int)
    out["is_site_top10"] = out["site_score_rank"].le(10).astype(int)
    out["score_gate_flag"] = (out["is_global_top15pct"].eq(1) | out["is_site_top10"].eq(1)).astype(int)
    out["positive_promotion_excluded_flag"] = out["label_bucket_v2"].isin(HOLDOUT_BUCKETS).astype(int)

    def candidate_class(row: pd.Series) -> str:
        if row["label_bucket_v2"] in HOLDOUT_BUCKETS:
            return "monitor_or_common_cause_holdout"
        if row["boundary_margin"] > 0 and row["score_gate_flag"] == 1:
            return "positive_promotion_candidate"
        if row["boundary_margin"] <= 0 and row["is_global_top15pct"] == 1:
            return "hard_negative_review_candidate"
        return "low_priority_unlabeled"

    out["candidate_class"] = out.apply(candidate_class, axis=1)

    positive_candidates = out.loc[out["candidate_class"].eq("positive_promotion_candidate")].copy()
    positive_keys_in_top_half: set[tuple[str, str, str, str]] = set()
    if not positive_candidates.empty:
        positive_candidates = positive_candidates.sort_values(
            by=["boundary_margin", "electrical_core_minus_broadshape_050", "site", "panel_id", "run_start_date", "run_end_date"],
            ascending=[False, False, True, True, True, True],
        ).reset_index(drop=True)
        top_half_count = int(math.ceil(len(positive_candidates) / 2.0))
        positive_keys_in_top_half = set(make_key_tuple_frame(positive_candidates.head(top_half_count)))

    def priority_band(row: pd.Series) -> str:
        key = (row["site"], row["panel_id"], row["run_start_date"], row["run_end_date"])
        if row["candidate_class"] == "positive_promotion_candidate" and int(row["site_positive_gap_flag"]) == 1:
            return "P1"
        if row["candidate_class"] == "positive_promotion_candidate" and key in positive_keys_in_top_half:
            return "P2"
        if row["candidate_class"] == "hard_negative_review_candidate":
            return "P3"
        return "P4"

    out["candidate_priority_band"] = out.apply(priority_band, axis=1)
    return out


def build_boundary_reason(row: pd.Series) -> str:
    overlap_note = ""
    if int(row.get("in_existing_review_batch_flag", 0)) == 1:
        overlap_note = ", 기존 broad review batch와도 겹침"

    if row["candidate_class"] == "positive_promotion_candidate":
        gap_note = "site positive gap 보강 필요, " if int(row["site_positive_gap_flag"]) == 1 else ""
        return (
            f"{gap_note}missed positive boundary prototype 쪽 거리가 더 가깝고 "
            f"hard negative 대비 margin이 양수라 narrow positive promotion 후보로 본다{overlap_note}"
        )
    if row["candidate_class"] == "hard_negative_review_candidate":
        return (
            "hard negative boundary prototype에 더 가깝고 score가 여전히 높아 "
            f"false-positive 방어용 review 후보로 본다{overlap_note}"
        )
    if row["candidate_class"] == "monitor_or_common_cause_holdout":
        return "monitor/common-cause bucket은 positive promotion 대상에서 제외하고 별도 holdout으로 유지한다"
    return "boundary margin 또는 score gate가 약해 이번 narrow expansion 우선순위에서는 뒤로 둔다"


def build_candidate_output(candidate_df: pd.DataFrame) -> pd.DataFrame:
    out = candidate_df.copy()
    out["boundary_reason_ko"] = out.apply(build_boundary_reason, axis=1)
    return (
        out.loc[:, CANDIDATE_COLS]
        .sort_values(
            by=[
                "candidate_priority_band",
                "candidate_class",
                "boundary_margin",
                "electrical_core_minus_broadshape_050",
                "site",
                "panel_id",
                "run_start_date",
                "run_end_date",
            ],
            ascending=[True, True, False, False, True, True, True, True],
            na_position="last",
        )
        .reset_index(drop=True)
    )


def build_summary(candidate_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def append_row(site_value: str, site_df: pd.DataFrame, record_type: str) -> None:
        rows.append(
            {
                "record_type": record_type,
                "site": site_value,
                "excluded_run_count": int(len(site_df)),
                "positive_promotion_candidate_count": int(site_df["candidate_class"].eq("positive_promotion_candidate").sum()),
                "hard_negative_review_candidate_count": int(site_df["candidate_class"].eq("hard_negative_review_candidate").sum()),
                "monitor_or_common_cause_holdout_count": int(site_df["candidate_class"].eq("monitor_or_common_cause_holdout").sum()),
                "low_priority_unlabeled_count": int(site_df["candidate_class"].eq("low_priority_unlabeled").sum()),
                "p1_count": int(site_df["candidate_priority_band"].eq("P1").sum()),
                "p2_count": int(site_df["candidate_priority_band"].eq("P2").sum()),
                "p3_count": int(site_df["candidate_priority_band"].eq("P3").sum()),
                "p4_count": int(site_df["candidate_priority_band"].eq("P4").sum()),
                "site_positive_gap_flag": int(site_df["site_positive_gap_flag"].max()) if not site_df.empty else 0,
                "note_ko": (
                    "reference gap boundary prototype 거리 기반으로 narrow expansion 후보를 고른 결과"
                    if record_type == "overall"
                    else "site별 boundary-based candidate 분포"
                ),
            }
        )

    append_row("", candidate_df, "overall")
    for site, site_df in candidate_df.groupby("site", dropna=False):
        append_row(normalize_text(site), site_df.copy(), "site")
    return pd.DataFrame(rows).reindex(columns=SUMMARY_COLS)


def build_joined_universe(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    feature_df = load_feature_table(root)
    label_df = load_label_pack_v2(root)
    v0_df = load_v0_scores(root)
    review_batch_df = load_review_batch(root)
    coverage_df = compute_site_coverage(label_df)
    ranks_df = compute_score_ranks(v0_df)

    merged = feature_df.merge(label_df, on=KEY_COLS, how="inner")
    merged = merged.merge(ranks_df, on=KEY_COLS, how="left")
    merged = merged.merge(coverage_df, on="site", how="left")
    merged = merged.merge(review_batch_df, on=KEY_COLS, how="left")
    merged["in_existing_review_batch_flag"] = merged["in_existing_review_batch_flag"].fillna(0).astype(int)
    merged["site_positive_gap_flag"] = merged["site_positive_gap_flag"].fillna(0).astype(int)

    missing_scores = merged["electrical_core_minus_broadshape_050"].isna()
    if missing_scores.any():
        raise SystemExit("some runs are missing electrical_core_minus_broadshape_050 after merge")

    excluded_df = merged.loc[merged["training_label_v2"].eq("exclude")].copy().reset_index(drop=True)
    if excluded_df.empty:
        raise SystemExit("run_label_pack_v2 has no excluded rows to audit")
    return excluded_df, load_reference_gap_cases(root), int(len(ranks_df))


def save_outputs(root: Path, candidates: pd.DataFrame, summary_df: pd.DataFrame, prototype_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(share_dir / CANDIDATES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    prototype_df.to_csv(share_dir / PROTOTYPES_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    excluded_df, reference_gap_df, total_scored_run_count = build_joined_universe(root)
    prototype_df = build_prototype_output(reference_gap_df)
    with_distances = compute_boundary_distances(excluded_df, prototype_df)
    classified = classify_candidates(with_distances, total_scored_run_count=total_scored_run_count)
    candidate_output = build_candidate_output(classified)
    summary_df = build_summary(classified)

    save_outputs(root, candidate_output, summary_df, prototype_df)


if __name__ == "__main__":
    main()
