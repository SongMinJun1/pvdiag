#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression

import build_panel_day_engine_run_ranker_v2_holdout_audit as holdout_base

FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
LABEL_PACK_V3_NAME = "panel_day_engine_run_label_pack_v3_intersection.csv"
V0_SCORES_NAME = "panel_day_engine_run_ranker_v0_scores.csv"

FOLD_SUMMARY_OUTPUT_NAME = "panel_day_engine_run_ranker_complement_fold_summary_v1.csv"
CASES_OUTPUT_NAME = "panel_day_engine_run_ranker_complement_cases_v1.csv"
RECOMMENDATION_OUTPUT_NAME = "panel_day_engine_run_ranker_complement_recommendation_v1.csv"

KEY_COLS = holdout_base.KEY_COLS
TRAIN_LABELS = holdout_base.TRAIN_LABELS
EVALUATION_GROUPS = holdout_base.EVALUATION_GROUPS
TOP_K = 20

REFERENCE_METHOD_NAME = "reference_only"
REFERENCE_SCORE_COL = "electrical_core_minus_broadshape_050"
LOGISTIC_METHOD_NAME = "logistic_v3_intersection_holdout"
LOGISTIC_SCORE_COL = "logistic_v3_intersection_score"

REQUIRED_LABEL_PACK_V3_COLS = [*KEY_COLS, "label_bucket_v3", "training_label_v3"]
REQUIRED_V0_SCORE_COLS = [*KEY_COLS, REFERENCE_SCORE_COL]

FOLD_SUMMARY_COLS = [
    "fold_type",
    "fold_id",
    "test_site",
    "reference_positive_top20_count",
    "reference_negative_top20_count",
    "logistic_positive_top20_count",
    "logistic_negative_top20_count",
    "positive_in_both_count",
    "positive_reference_only_count",
    "positive_logistic_only_count",
    "negative_in_both_count",
    "negative_reference_only_count",
    "negative_logistic_only_count",
    "top20_overlap_count",
    "top20_overlap_rate",
    "logistic_incremental_positive_minus_negative",
    "skip_reason",
]

CASE_COLS = [
    "fold_type",
    "fold_id",
    "test_site",
    "disagreement_class",
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_shape_class",
    "label_bucket_v3",
    REFERENCE_SCORE_COL,
    LOGISTIC_SCORE_COL,
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "complement_reason_ko",
]

RECOMMENDATION_COLS = [
    "recommended_next_direction",
    "rationale_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate whether logistic_v3_intersection_holdout has complementary value to the deterministic run reference."
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


def load_label_pack_v3(root: Path) -> pd.DataFrame:
    path = root / "_share" / LABEL_PACK_V3_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_LABEL_PACK_V3_COLS, path.name)
    df = holdout_base.normalize_key_cols(df)
    df["label_bucket_v3"] = df["label_bucket_v3"].map(holdout_base.normalize_text)
    df["training_label_v3"] = df["training_label_v3"].map(holdout_base.normalize_text)
    df["evaluation_group"] = df["label_bucket_v3"].where(
        df["label_bucket_v3"].isin(EVALUATION_GROUPS),
        "unlabeled_other",
    )
    return (
        df.loc[:, [*KEY_COLS, "label_bucket_v3", "training_label_v3", "evaluation_group"]]
        .drop_duplicates(subset=KEY_COLS, keep="first")
        .reset_index(drop=True)
    )


def load_v0_scores(root: Path) -> pd.DataFrame:
    path = root / "_share" / V0_SCORES_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_V0_SCORE_COLS, path.name)
    df = holdout_base.normalize_key_cols(df)
    df[REFERENCE_SCORE_COL] = pd.to_numeric(df[REFERENCE_SCORE_COL], errors="coerce")
    return (
        df.loc[:, REQUIRED_V0_SCORE_COLS]
        .drop_duplicates(subset=KEY_COLS, keep="first")
        .reset_index(drop=True)
    )


def prepare_universe(root: Path) -> pd.DataFrame:
    feature_df = holdout_base.load_feature_table(root)
    label_df = load_label_pack_v3(root)
    v0_df = load_v0_scores(root)

    merged = feature_df.merge(label_df, on=KEY_COLS, how="left", validate="one_to_one")
    merged = merged.merge(v0_df, on=KEY_COLS, how="left", validate="one_to_one")

    if merged["evaluation_group"].isna().any():
        missing_count = int(merged["evaluation_group"].isna().sum())
        raise SystemExit(f"missing v3 label rows for {missing_count} runs")
    if merged[REFERENCE_SCORE_COL].isna().any():
        raise SystemExit(f"merged run universe missing reference score: {REFERENCE_SCORE_COL}")

    merged["training_label_v3"] = merged["training_label_v3"].fillna("").map(holdout_base.normalize_text)
    merged["run_start_dt"] = pd.to_datetime(merged["run_start_date"], errors="coerce")
    return merged


def key_tuple_from_row(row: pd.Series) -> tuple[str, str, str, str]:
    return tuple(str(row[col]) for col in KEY_COLS)


def rows_by_key(df: pd.DataFrame) -> dict[tuple[str, str, str, str], pd.Series]:
    mapping: dict[tuple[str, str, str, str], pd.Series] = {}
    for _, row in df.iterrows():
        mapping[key_tuple_from_row(row)] = row
    return mapping


def count_group_members(keys: set[tuple[str, str, str, str]], by_key: dict[tuple[str, str, str, str], pd.Series], group_name: str) -> int:
    return sum(1 for key in keys if holdout_base.normalize_text(by_key[key]["evaluation_group"]) == group_name)


def disagreement_reason(disagreement_class: str) -> str:
    reason_map = {
        "positive_logistic_only": "deterministic top20 밖 positive-like run을 learned v3가 추가로 끌어올려 secondary discovery 후보로 볼 수 있다.",
        "positive_reference_only": "deterministic reference가 잡은 positive-like run을 learned v3는 아직 top20에 올리지 못한다.",
        "negative_logistic_only": "learned v3가 reference에는 없던 negative-like run을 top20에 올려 contamination risk를 만든다.",
        "negative_reference_only": "deterministic reference가 negative-like run을 더 강하게 밀어올렸고 learned v3는 이를 일부 누른다.",
    }
    return reason_map[disagreement_class]


def build_case_rows(
    scored_test: pd.DataFrame,
    fold_type: str,
    fold_id: str,
    test_site: str,
    ref_only: set[tuple[str, str, str, str]],
    log_only: set[tuple[str, str, str, str]],
) -> list[dict[str, object]]:
    by_key = rows_by_key(scored_test)
    case_rows: list[dict[str, object]] = []

    for disagreement_class, key_set in (
        ("positive_logistic_only", log_only),
        ("positive_reference_only", ref_only),
        ("negative_logistic_only", log_only),
        ("negative_reference_only", ref_only),
    ):
        expected_group = "positive_like" if "positive_" in disagreement_class else "negative_like"
        for key in sorted(key_set):
            row = by_key.get(key)
            if row is None:
                continue
            if holdout_base.normalize_text(row["evaluation_group"]) != expected_group:
                continue
            case_rows.append(
                {
                    "fold_type": fold_type,
                    "fold_id": fold_id,
                    "test_site": test_site,
                    "disagreement_class": disagreement_class,
                    "site": holdout_base.normalize_text(row["site"]),
                    "panel_id": holdout_base.normalize_text(row["panel_id"]),
                    "run_start_date": holdout_base.normalize_text(row["run_start_date"]),
                    "run_end_date": holdout_base.normalize_text(row["run_end_date"]),
                    "run_shape_class": holdout_base.normalize_text(row["run_shape_class"]),
                    "label_bucket_v3": holdout_base.normalize_text(row["label_bucket_v3"]),
                    REFERENCE_SCORE_COL: pd.to_numeric(row[REFERENCE_SCORE_COL], errors="coerce"),
                    LOGISTIC_SCORE_COL: pd.to_numeric(row[LOGISTIC_SCORE_COL], errors="coerce"),
                    "max_v_drop": pd.to_numeric(row["max_v_drop"], errors="coerce"),
                    "min_mid_v_ratio": pd.to_numeric(row["min_mid_v_ratio"], errors="coerce"),
                    "min_mid_ratio": pd.to_numeric(row["min_mid_ratio"], errors="coerce"),
                    "cond_evt_only_day_ratio": pd.to_numeric(row["cond_evt_only_day_ratio"], errors="coerce"),
                    "ae_mid_or_hi_early_day_ratio": pd.to_numeric(row["ae_mid_or_hi_early_day_ratio"], errors="coerce"),
                    "mean_signal_count": pd.to_numeric(row["mean_signal_count"], errors="coerce"),
                    "max_signal_count": pd.to_numeric(row["max_signal_count"], errors="coerce"),
                    "p95_recon_error": pd.to_numeric(row["p95_recon_error"], errors="coerce"),
                    "complement_reason_ko": disagreement_reason(disagreement_class),
                }
            )

    return case_rows


def evaluate_fold(universe: pd.DataFrame, spec: dict[str, object]) -> tuple[dict[str, object], list[dict[str, object]]]:
    fold_type = str(spec["fold_type"])
    fold_id = str(spec["fold_id"])
    test_site = str(spec["test_site"])
    train_df = universe.loc[list(spec["train_index"])].copy()
    test_df = universe.loc[list(spec["test_index"])].copy()

    train_labeled = train_df.loc[train_df["training_label_v3"].isin(TRAIN_LABELS)].copy()
    train_positive_count = int(train_labeled["training_label_v3"].eq("positive").sum())
    train_negative_count = int(train_labeled["training_label_v3"].eq("negative").sum())

    if test_df.empty:
        return (
            {
                "fold_type": fold_type,
                "fold_id": fold_id,
                "test_site": test_site,
                "reference_positive_top20_count": None,
                "reference_negative_top20_count": None,
                "logistic_positive_top20_count": None,
                "logistic_negative_top20_count": None,
                "positive_in_both_count": None,
                "positive_reference_only_count": None,
                "positive_logistic_only_count": None,
                "negative_in_both_count": None,
                "negative_reference_only_count": None,
                "negative_logistic_only_count": None,
                "top20_overlap_count": None,
                "top20_overlap_rate": None,
                "logistic_incremental_positive_minus_negative": None,
                "skip_reason": "empty_test_universe",
            },
            [],
        )

    if train_labeled.empty or train_positive_count == 0 or train_negative_count == 0:
        return (
            {
                "fold_type": fold_type,
                "fold_id": fold_id,
                "test_site": test_site,
                "reference_positive_top20_count": None,
                "reference_negative_top20_count": None,
                "logistic_positive_top20_count": None,
                "logistic_negative_top20_count": None,
                "positive_in_both_count": None,
                "positive_reference_only_count": None,
                "positive_logistic_only_count": None,
                "negative_in_both_count": None,
                "negative_reference_only_count": None,
                "negative_logistic_only_count": None,
                "top20_overlap_count": None,
                "top20_overlap_rate": None,
                "logistic_incremental_positive_minus_negative": None,
                "skip_reason": "train_labeled_missing_class",
            },
            [],
        )

    raw_train = holdout_base.build_raw_feature_matrix(train_labeled)
    medians, iqr = holdout_base.fit_robust_scaler(raw_train)
    scaled_train = holdout_base.apply_robust_scaler(raw_train, medians, iqr)
    y_train = train_labeled["training_label_v3"].eq("positive").astype(int)

    logistic = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=0)
    logistic.fit(scaled_train, y_train)

    raw_test = holdout_base.build_raw_feature_matrix(test_df)
    scaled_test = holdout_base.apply_robust_scaler(raw_test, medians, iqr)
    scored_test = test_df.copy()
    scored_test[LOGISTIC_SCORE_COL] = logistic.predict_proba(scaled_test)[:, 1]

    top_k = min(TOP_K, len(scored_test))
    reference_top = holdout_base.rank_runs(scored_test, REFERENCE_SCORE_COL).head(top_k).copy()
    logistic_top = holdout_base.rank_runs(scored_test, LOGISTIC_SCORE_COL).head(top_k).copy()

    ref_keys = {key_tuple_from_row(row) for _, row in reference_top.iterrows()}
    log_keys = {key_tuple_from_row(row) for _, row in logistic_top.iterrows()}
    both_keys = ref_keys & log_keys
    ref_only = ref_keys - log_keys
    log_only = log_keys - ref_keys
    by_key = rows_by_key(scored_test)

    summary_row = {
        "fold_type": fold_type,
        "fold_id": fold_id,
        "test_site": test_site,
        "reference_positive_top20_count": count_group_members(ref_keys, by_key, "positive_like"),
        "reference_negative_top20_count": count_group_members(ref_keys, by_key, "negative_like"),
        "logistic_positive_top20_count": count_group_members(log_keys, by_key, "positive_like"),
        "logistic_negative_top20_count": count_group_members(log_keys, by_key, "negative_like"),
        "positive_in_both_count": count_group_members(both_keys, by_key, "positive_like"),
        "positive_reference_only_count": count_group_members(ref_only, by_key, "positive_like"),
        "positive_logistic_only_count": count_group_members(log_only, by_key, "positive_like"),
        "negative_in_both_count": count_group_members(both_keys, by_key, "negative_like"),
        "negative_reference_only_count": count_group_members(ref_only, by_key, "negative_like"),
        "negative_logistic_only_count": count_group_members(log_only, by_key, "negative_like"),
        "top20_overlap_count": len(both_keys),
        "top20_overlap_rate": len(both_keys) / float(top_k) if top_k else 0.0,
        "logistic_incremental_positive_minus_negative": count_group_members(log_only, by_key, "positive_like")
        - count_group_members(log_only, by_key, "negative_like"),
        "skip_reason": "",
    }
    case_rows = build_case_rows(scored_test, fold_type, fold_id, test_site, ref_only, log_only)
    return summary_row, case_rows


def build_recommendation(fold_summary_df: pd.DataFrame) -> pd.DataFrame:
    if fold_summary_df.empty:
        return pd.DataFrame(
            [
                {
                    "recommended_next_direction": "stop_learned_scorer_for_now",
                    "rationale_ko": "유효 fold가 없어 learned scorer의 보완 가치를 판단할 수 없다.",
                }
            ],
            columns=RECOMMENDATION_COLS,
        )

    valid = fold_summary_df.loc[fold_summary_df["skip_reason"].eq("")].copy()
    if valid.empty:
        return pd.DataFrame(
            [
                {
                    "recommended_next_direction": "stop_learned_scorer_for_now",
                    "rationale_ko": "모든 fold가 skip되어 secondary discovery lane으로 유지할 근거가 없다.",
                }
            ],
            columns=RECOMMENDATION_COLS,
        )

    mean_increment = float(valid["logistic_incremental_positive_minus_negative"].mean())
    any_positive_logistic_only = bool(valid["positive_logistic_only_count"].gt(0).any())
    if mean_increment > 0.0 and any_positive_logistic_only:
        rationale = (
            f"logistic-only positive가 있는 fold가 존재하고 평균 incremental positive-minus-negative={mean_increment:.3f}라 "
            "deterministic primary scorer 옆의 secondary discovery lane으로는 유지할 가치가 있다."
        )
        direction = "use_logistic_as_secondary_discovery_lane"
    else:
        rationale = (
            f"평균 incremental positive-minus-negative={mean_increment:.3f} 이고 logistic-only positive 이득이 충분하지 않아 "
            "learned scorer를 별도 discovery lane으로 유지할 근거가 약하다."
        )
        direction = "stop_learned_scorer_for_now"

    return pd.DataFrame(
        [{"recommended_next_direction": direction, "rationale_ko": rationale}],
        columns=RECOMMENDATION_COLS,
    )


def save_outputs(root: Path, fold_summary_df: pd.DataFrame, cases_df: pd.DataFrame, recommendation_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    fold_summary_df.to_csv(share_dir / FOLD_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    cases_df.to_csv(share_dir / CASES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    recommendation_df.to_csv(share_dir / RECOMMENDATION_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    universe = prepare_universe(root)
    fold_rows: list[dict[str, object]] = []
    case_rows: list[dict[str, object]] = []
    for spec in holdout_base.fold_specs(universe):
        fold_row, fold_cases = evaluate_fold(universe, spec)
        fold_rows.append(fold_row)
        case_rows.extend(fold_cases)

    fold_summary_df = pd.DataFrame(fold_rows, columns=FOLD_SUMMARY_COLS)
    cases_df = pd.DataFrame(case_rows, columns=CASE_COLS)
    recommendation_df = build_recommendation(fold_summary_df)
    save_outputs(root, fold_summary_df, cases_df, recommendation_df)


if __name__ == "__main__":
    main()
