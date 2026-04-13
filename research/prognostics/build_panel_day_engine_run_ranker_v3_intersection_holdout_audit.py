#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression

import build_panel_day_engine_run_ranker_v2_holdout_audit as holdout_base

STRATEGY_NAME = "panel_day_engine_run_boundary_distance_hygiene_strategy_v1.csv"
BOUNDARY_CANDIDATES_NAME = "panel_day_engine_run_boundary_label_expansion_candidates_v1.csv"
REVIEW_BATCH_NAME = "panel_day_engine_run_label_expansion_review_batch_v1.csv"
LABEL_PACK_V2_NAME = "panel_day_engine_run_label_pack_v2.csv"
V2_HOLDOUT_SUMMARY_NAME = "panel_day_engine_run_ranker_v2_holdout_summary.csv"

LABEL_PACK_V3_OUTPUT_NAME = "panel_day_engine_run_label_pack_v3_intersection.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_run_ranker_v3_intersection_holdout_summary.csv"
TOPK_OUTPUT_NAME = "panel_day_engine_run_ranker_v3_intersection_holdout_topk_yield.csv"

EXPECTED_STRATEGY = "use_boundary_intersection_with_review_batch"
PROMOTION_SOURCE = "boundary_intersection_weak_positive"
PROMOTION_CONFIDENCE = "medium"
PROMOTION_BUCKET = "positive_like"
PROMOTION_TRAINING_LABEL = "positive"
POSITIVE_TRACK = "positive_review_batch"

KEY_COLS = holdout_base.KEY_COLS
EVALUATION_GROUPS = holdout_base.EVALUATION_GROUPS
LABELED_GROUPS = holdout_base.LABELED_GROUPS
TRAIN_LABELS = holdout_base.TRAIN_LABELS
TOP_K_VALUES = holdout_base.TOP_K_VALUES
TRAIN_FEATURES = holdout_base.TRAIN_FEATURES
SCORE_NAMES = [
    "logistic_v3_intersection_holdout",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
]

REQUIRED_STRATEGY_COLS = ["recommended_strategy", "recommended_reason_ko"]
REQUIRED_CANDIDATE_COLS = [*KEY_COLS, "candidate_class"]
REQUIRED_REVIEW_BATCH_COLS = [*KEY_COLS, "review_track"]
REQUIRED_LABEL_PACK_V2_COLS = [
    *KEY_COLS,
    "label_bucket_v2",
    "training_label_v2",
    "label_confidence_v2",
    "label_sources_csv_v2",
    "label_reason_ko_v2",
]
REQUIRED_V2_SUMMARY_COLS = [
    "score_name",
    "fold_type",
    "mean_top10_positive_minus_negative",
    "mean_top20_positive_minus_negative",
]

SUMMARY_COLS = [
    "score_name",
    "fold_type",
    "valid_fold_count",
    "mean_labeled_test_auc",
    "mean_labeled_test_average_precision",
    "mean_top10_positive_minus_negative",
    "mean_top20_positive_minus_negative",
    "delta_mean_top10_vs_v2_logistic",
    "delta_mean_top20_vs_v2_logistic",
    "delta_mean_top10_vs_reference",
    "delta_mean_top20_vs_reference",
    "promoted_positive_count",
    "promoted_sites_csv",
    "note_ko",
]
TOPK_COLS = [
    "fold_type",
    "fold_id",
    "score_name",
    "top_k",
    "topk_positive_like_count",
    "topk_negative_like_count",
    "topk_monitor_like_count",
    "topk_common_cause_like_count",
    "topk_unlabeled_other_count",
    "topk_positive_minus_negative",
]
FOLD_SCORE_COLS = [
    "fold_type",
    "fold_id",
    "score_name",
    "test_site",
    "train_labeled_count",
    "train_positive_count",
    "train_negative_count",
    "test_run_count",
    "test_positive_like_count",
    "test_negative_like_count",
    "test_monitor_like_count",
    "test_common_cause_like_count",
    "test_unlabeled_other_count",
    "labeled_test_auc",
    "labeled_test_average_precision",
    "top10_positive_like_count",
    "top10_negative_like_count",
    "top10_monitor_like_count",
    "top10_common_cause_like_count",
    "top10_unlabeled_other_count",
    "top20_positive_like_count",
    "top20_negative_like_count",
    "top20_monitor_like_count",
    "top20_common_cause_like_count",
    "top20_unlabeled_other_count",
    "top10_positive_minus_negative",
    "top20_positive_minus_negative",
    "skip_reason",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a v3 scorer using the recommended boundary-intersection narrow promotion strategy."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the project root.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def drop_repeated_header_rows(df: pd.DataFrame) -> pd.DataFrame:
    return holdout_base.drop_repeated_header_rows(df)


def normalize_key_cols(df: pd.DataFrame) -> pd.DataFrame:
    return holdout_base.normalize_key_cols(df)


def normalize_text(value: object) -> str:
    return holdout_base.normalize_text(value)


def load_strategy(root: Path) -> pd.DataFrame:
    path = root / "_share" / STRATEGY_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_STRATEGY_COLS, path.name)
    if len(df) != 1:
        raise SystemExit(f"{path.name} must contain exactly one row")
    df["recommended_strategy"] = df["recommended_strategy"].map(normalize_text)
    df["recommended_reason_ko"] = df["recommended_reason_ko"].map(normalize_text)
    strategy = df.iloc[0]["recommended_strategy"]
    if strategy != EXPECTED_STRATEGY:
        raise SystemExit(
            f"recommended_strategy must be {EXPECTED_STRATEGY}, got {strategy}. "
            "Boundary hygiene did not approve the intersection strategy."
        )
    return df.loc[:, REQUIRED_STRATEGY_COLS].copy()


def load_boundary_candidates(root: Path) -> pd.DataFrame:
    path = root / "_share" / BOUNDARY_CANDIDATES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_CANDIDATE_COLS, path.name)
    df = normalize_key_cols(df)
    df["candidate_class"] = df["candidate_class"].map(normalize_text)
    return (
        df.loc[df["candidate_class"].eq("positive_promotion_candidate"), REQUIRED_CANDIDATE_COLS]
        .drop_duplicates(subset=KEY_COLS, keep="first")
        .reset_index(drop=True)
    )


def load_review_batch(root: Path) -> pd.DataFrame:
    path = root / "_share" / REVIEW_BATCH_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_REVIEW_BATCH_COLS, path.name)
    df = normalize_key_cols(df)
    df["review_track"] = df["review_track"].map(normalize_text)
    return (
        df.loc[df["review_track"].eq(POSITIVE_TRACK), REQUIRED_REVIEW_BATCH_COLS]
        .drop_duplicates(subset=KEY_COLS, keep="first")
        .reset_index(drop=True)
    )


def build_promoted_intersection(root: Path) -> pd.DataFrame:
    boundary_df = load_boundary_candidates(root)
    review_df = load_review_batch(root)
    intersection = boundary_df.loc[:, KEY_COLS].merge(review_df.loc[:, KEY_COLS], on=KEY_COLS, how="inner")
    intersection = intersection.drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)
    if intersection.empty:
        raise SystemExit("boundary-review intersection is empty; cannot build a v3 intersection label pack")
    return intersection


def load_label_pack_v2(root: Path) -> pd.DataFrame:
    path = root / "_share" / LABEL_PACK_V2_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_LABEL_PACK_V2_COLS, path.name)
    df = normalize_key_cols(df)
    for col in ["label_bucket_v2", "training_label_v2", "label_confidence_v2", "label_sources_csv_v2", "label_reason_ko_v2"]:
        df[col] = df[col].map(normalize_text)
    return df.copy()


def load_v2_summary(root: Path) -> pd.DataFrame:
    path = root / "_share" / V2_HOLDOUT_SUMMARY_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_V2_SUMMARY_COLS, path.name)
    df["score_name"] = df["score_name"].map(normalize_text)
    df["fold_type"] = df["fold_type"].map(normalize_text)
    for col in ["mean_top10_positive_minus_negative", "mean_top20_positive_minus_negative"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, REQUIRED_V2_SUMMARY_COLS].copy()


def build_label_pack_v3(label_pack_v2: pd.DataFrame, promoted_df: pd.DataFrame) -> tuple[pd.DataFrame, set[tuple[str, str, str, str]], str]:
    promoted_keys = set(map(tuple, promoted_df[KEY_COLS].itertuples(index=False, name=None)))
    promoted_sites_csv = ",".join(sorted(promoted_df["site"].map(normalize_text).unique().tolist()))

    out = label_pack_v2.copy()
    key_series = out[KEY_COLS].apply(tuple, axis=1)
    out["promoted_intersection_positive_flag"] = key_series.isin(promoted_keys).astype(int)
    out["training_label_v3"] = out["training_label_v2"].map(normalize_text)
    out["label_bucket_v3"] = out["label_bucket_v2"].map(normalize_text)
    out["label_confidence_v3"] = out["label_confidence_v2"].map(normalize_text)
    out["label_source_v3"] = out["label_sources_csv_v2"].map(normalize_text)
    out["label_reason_ko_v3"] = out["label_reason_ko_v2"].map(normalize_text)

    promoted_mask = out["promoted_intersection_positive_flag"].eq(1)
    out.loc[promoted_mask, "training_label_v3"] = PROMOTION_TRAINING_LABEL
    out.loc[promoted_mask, "label_bucket_v3"] = PROMOTION_BUCKET
    out.loc[promoted_mask, "label_confidence_v3"] = PROMOTION_CONFIDENCE
    out.loc[promoted_mask, "label_source_v3"] = PROMOTION_SOURCE
    out.loc[promoted_mask, "label_reason_ko_v3"] = (
        "boundary hygiene가 승인한 boundary-review intersection weak positive를 v3 narrow promotion으로 승격"
    )

    desired_cols = [
        *list(label_pack_v2.columns),
        "promoted_intersection_positive_flag",
        "label_bucket_v3",
        "training_label_v3",
        "label_confidence_v3",
        "label_source_v3",
        "label_reason_ko_v3",
    ]
    return out.loc[:, desired_cols].copy(), promoted_keys, promoted_sites_csv


def prepare_universe(root: Path, label_pack_v3: pd.DataFrame) -> pd.DataFrame:
    feature_df = holdout_base.load_feature_table(root)
    v0_df = holdout_base.load_v0_scores(root)

    label_df = label_pack_v3.loc[
        :,
        [*KEY_COLS, "label_bucket_v3", "training_label_v3"],
    ].copy()
    label_df["evaluation_group"] = label_df["label_bucket_v3"].where(
        label_df["label_bucket_v3"].isin(EVALUATION_GROUPS),
        "unlabeled_other",
    )

    merged = feature_df.merge(label_df, on=KEY_COLS, how="left", validate="one_to_one")
    merged = merged.merge(v0_df, on=KEY_COLS, how="left", validate="one_to_one")

    if merged["evaluation_group"].isna().any():
        missing_count = int(merged["evaluation_group"].isna().sum())
        raise SystemExit(f"missing v3 label rows for {missing_count} runs")

    missing_ref_cols = [
        col
        for col in ["electrical_core_score", "electrical_core_minus_broadshape_050"]
        if merged[col].isna().any()
    ]
    if missing_ref_cols:
        raise SystemExit(f"merged run universe missing reference scores: {missing_ref_cols}")

    merged["training_label_v3"] = merged["training_label_v3"].fillna("").map(normalize_text)
    merged["run_start_dt"] = pd.to_datetime(merged["run_start_date"], errors="coerce")
    return merged


def evaluate_fold(universe: pd.DataFrame, spec: dict[str, object]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    fold_type = str(spec["fold_type"])
    fold_id = str(spec["fold_id"])
    test_site = str(spec["test_site"])
    train_index = list(spec["train_index"])
    test_index = list(spec["test_index"])

    train_df = universe.loc[train_index].copy()
    test_df = universe.loc[test_index].copy()
    train_labeled = train_df.loc[train_df["training_label_v3"].isin(TRAIN_LABELS)].copy()
    train_positive_count = int(train_labeled["training_label_v3"].eq("positive").sum())
    train_negative_count = int(train_labeled["training_label_v3"].eq("negative").sum())
    empty_counts = {name: 0 for name in EVALUATION_GROUPS}
    test_counts = holdout_base.compute_group_counts(test_df) if not test_df.empty else empty_counts

    skip_reason = ""
    if test_df.empty:
        skip_reason = "empty_test_universe"
    elif train_labeled.empty or train_positive_count == 0 or train_negative_count == 0:
        skip_reason = "train_labeled_missing_class"

    if skip_reason:
        skipped_rows = []
        for score_name in SCORE_NAMES:
            skipped_rows.append(
                {
                    "fold_type": fold_type,
                    "fold_id": fold_id,
                    "score_name": score_name,
                    "test_site": test_site,
                    "train_labeled_count": int(len(train_labeled)),
                    "train_positive_count": train_positive_count,
                    "train_negative_count": train_negative_count,
                    "test_run_count": int(len(test_df)),
                    "test_positive_like_count": test_counts["positive_like"],
                    "test_negative_like_count": test_counts["negative_like"],
                    "test_monitor_like_count": test_counts["monitor_like"],
                    "test_common_cause_like_count": test_counts["common_cause_like"],
                    "test_unlabeled_other_count": test_counts["unlabeled_other"],
                    "labeled_test_auc": None,
                    "labeled_test_average_precision": None,
                    "top10_positive_like_count": None,
                    "top10_negative_like_count": None,
                    "top10_monitor_like_count": None,
                    "top10_common_cause_like_count": None,
                    "top10_unlabeled_other_count": None,
                    "top20_positive_like_count": None,
                    "top20_negative_like_count": None,
                    "top20_monitor_like_count": None,
                    "top20_common_cause_like_count": None,
                    "top20_unlabeled_other_count": None,
                    "top10_positive_minus_negative": None,
                    "top20_positive_minus_negative": None,
                    "skip_reason": skip_reason,
                }
            )
        return skipped_rows, []

    raw_train = holdout_base.build_raw_feature_matrix(train_labeled)
    medians, iqr = holdout_base.fit_robust_scaler(raw_train)
    scaled_train = holdout_base.apply_robust_scaler(raw_train, medians, iqr)
    y_train = train_labeled["training_label_v3"].eq("positive").astype(int)

    logistic = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=0)
    logistic.fit(scaled_train, y_train)

    raw_test = holdout_base.build_raw_feature_matrix(test_df)
    scaled_test = holdout_base.apply_robust_scaler(raw_test, medians, iqr)
    scored_test = test_df.copy()
    scored_test["logistic_v3_intersection_holdout"] = logistic.predict_proba(scaled_test)[:, 1]

    fold_rows: list[dict[str, object]] = []
    topk_rows: list[dict[str, object]] = []
    for score_name in SCORE_NAMES:
        metric_row, metric_topk_rows = holdout_base.compute_holdout_metrics(scored_test, score_name)
        fold_rows.append(
            {
                "fold_type": fold_type,
                "fold_id": fold_id,
                "score_name": score_name,
                "test_site": test_site,
                "train_labeled_count": int(len(train_labeled)),
                "train_positive_count": train_positive_count,
                "train_negative_count": train_negative_count,
                "test_run_count": int(len(test_df)),
                "test_positive_like_count": test_counts["positive_like"],
                "test_negative_like_count": test_counts["negative_like"],
                "test_monitor_like_count": test_counts["monitor_like"],
                "test_common_cause_like_count": test_counts["common_cause_like"],
                "test_unlabeled_other_count": test_counts["unlabeled_other"],
                **metric_row,
                "skip_reason": "",
            }
        )
        for row in metric_topk_rows:
            topk_rows.append(
                {
                    "fold_type": fold_type,
                    "fold_id": fold_id,
                    "score_name": score_name,
                    "top_k": int(row["top_k"]),
                    "topk_positive_like_count": int(row["topk_positive_like_count"]),
                    "topk_negative_like_count": int(row["topk_negative_like_count"]),
                    "topk_monitor_like_count": int(row["topk_monitor_like_count"]),
                    "topk_common_cause_like_count": int(row["topk_common_cause_like_count"]),
                    "topk_unlabeled_other_count": int(row["topk_unlabeled_other_count"]),
                    "topk_positive_minus_negative": float(row["topk_positive_minus_negative"]),
                }
            )

    return fold_rows, topk_rows


def build_summary(
    fold_scores: pd.DataFrame,
    v2_summary: pd.DataFrame,
    promoted_positive_count: int,
    promoted_sites_csv: str,
) -> pd.DataFrame:
    if fold_scores.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)

    rows: list[dict[str, object]] = []
    all_fold_counts = (
        fold_scores[["fold_type", "fold_id"]].drop_duplicates().groupby("fold_type", dropna=False).size().to_dict()
    )

    for (score_name, fold_type), group in fold_scores.groupby(["score_name", "fold_type"], dropna=False):
        valid_group = group.loc[group["skip_reason"].eq("")].copy()
        total_folds = int(all_fold_counts.get(fold_type, 0))
        if valid_group.empty:
            rows.append(
                {
                    "score_name": score_name,
                    "fold_type": fold_type,
                    "valid_fold_count": 0,
                    "mean_labeled_test_auc": None,
                    "mean_labeled_test_average_precision": None,
                    "mean_top10_positive_minus_negative": None,
                    "mean_top20_positive_minus_negative": None,
                    "delta_mean_top10_vs_v2_logistic": None,
                    "delta_mean_top20_vs_v2_logistic": None,
                    "delta_mean_top10_vs_reference": None,
                    "delta_mean_top20_vs_reference": None,
                    "promoted_positive_count": promoted_positive_count,
                    "promoted_sites_csv": promoted_sites_csv,
                    "note_ko": f"no_valid_folds; total_folds={total_folds}",
                }
            )
            continue

        current_top10 = float(valid_group["top10_positive_minus_negative"].mean())
        current_top20 = float(valid_group["top20_positive_minus_negative"].mean())

        v2_logistic_row = v2_summary.loc[
            v2_summary["score_name"].eq("logistic_v2_holdout") & v2_summary["fold_type"].eq(str(fold_type))
        ]
        reference_row = v2_summary.loc[
            v2_summary["score_name"].eq("electrical_core_minus_broadshape_050") & v2_summary["fold_type"].eq(str(fold_type))
        ]

        delta_top10_vs_v2 = None
        delta_top20_vs_v2 = None
        if not v2_logistic_row.empty:
            delta_top10_vs_v2 = current_top10 - float(v2_logistic_row.iloc[0]["mean_top10_positive_minus_negative"])
            delta_top20_vs_v2 = current_top20 - float(v2_logistic_row.iloc[0]["mean_top20_positive_minus_negative"])

        delta_top10_vs_ref = None
        delta_top20_vs_ref = None
        if not reference_row.empty:
            delta_top10_vs_ref = current_top10 - float(reference_row.iloc[0]["mean_top10_positive_minus_negative"])
            delta_top20_vs_ref = current_top20 - float(reference_row.iloc[0]["mean_top20_positive_minus_negative"])

        note = (
            f"valid_folds={len(valid_group)}/{total_folds}; promoted={promoted_positive_count}; "
            f"promoted_sites={promoted_sites_csv or 'none'}"
        )

        rows.append(
            {
                "score_name": score_name,
                "fold_type": fold_type,
                "valid_fold_count": int(len(valid_group)),
                "mean_labeled_test_auc": valid_group["labeled_test_auc"].mean(),
                "mean_labeled_test_average_precision": valid_group["labeled_test_average_precision"].mean(),
                "mean_top10_positive_minus_negative": current_top10,
                "mean_top20_positive_minus_negative": current_top20,
                "delta_mean_top10_vs_v2_logistic": delta_top10_vs_v2,
                "delta_mean_top20_vs_v2_logistic": delta_top20_vs_v2,
                "delta_mean_top10_vs_reference": delta_top10_vs_ref,
                "delta_mean_top20_vs_reference": delta_top20_vs_ref,
                "promoted_positive_count": promoted_positive_count,
                "promoted_sites_csv": promoted_sites_csv,
                "note_ko": note,
            }
        )

    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def save_outputs(root: Path, label_pack_v3: pd.DataFrame, summary_df: pd.DataFrame, topk_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    label_pack_v3.to_csv(share_dir / LABEL_PACK_V3_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    topk_df.to_csv(share_dir / TOPK_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    load_strategy(root)
    promoted_df = build_promoted_intersection(root)
    label_pack_v2 = load_label_pack_v2(root)
    label_pack_v3, _, promoted_sites_csv = build_label_pack_v3(label_pack_v2, promoted_df)
    universe = prepare_universe(root, label_pack_v3)
    v2_summary = load_v2_summary(root)

    fold_rows: list[dict[str, object]] = []
    topk_rows: list[dict[str, object]] = []
    for spec in holdout_base.fold_specs(universe):
        rows, topk = evaluate_fold(universe, spec)
        fold_rows.extend(rows)
        topk_rows.extend(topk)

    fold_scores = pd.DataFrame(fold_rows, columns=FOLD_SCORE_COLS)
    topk_df = pd.DataFrame(topk_rows, columns=TOPK_COLS)
    summary_df = build_summary(
        fold_scores=fold_scores,
        v2_summary=v2_summary,
        promoted_positive_count=int(len(promoted_df)),
        promoted_sites_csv=promoted_sites_csv,
    )

    save_outputs(root, label_pack_v3, summary_df, topk_df)


if __name__ == "__main__":
    main()
