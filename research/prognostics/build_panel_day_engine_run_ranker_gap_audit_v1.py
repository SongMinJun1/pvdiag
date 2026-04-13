#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
LABEL_PACK_V2_NAME = "panel_day_engine_run_label_pack_v2.csv"
PROMOTION_SCENARIOS_NAME = "panel_day_engine_run_label_promotion_scenarios_v1.csv"
V0_SCORES_NAME = "panel_day_engine_run_ranker_v0_scores.csv"
V2_HOLDOUT_SUMMARY_NAME = "panel_day_engine_run_ranker_v2_holdout_summary.csv"
V3_SCENARIO_SUMMARY_NAME = "panel_day_engine_run_ranker_v3_scenario_holdout_summary_v1.csv"

FOLDS_OUTPUT_NAME = "panel_day_engine_run_ranker_gap_audit_folds_v1.csv"
CASES_OUTPUT_NAME = "panel_day_engine_run_ranker_gap_audit_cases_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_run_ranker_gap_audit_summary_v1.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
STRING_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "run_shape_class", "cohort_hint"]
FIXED_SCENARIO_NAME = "p1_plus_site_balanced_p2"
LOGISTIC_METHOD_NAME = "logistic_v3_candidate"
REFERENCE_METHOD_NAME = "electrical_core_minus_broadshape_050"
COMPARISON_TARGET = f"{LOGISTIC_METHOD_NAME}_vs_{REFERENCE_METHOD_NAME}"
TOP_K_VALUES = [10, 20]
TRAIN_LABELS = {"positive", "negative"}
LABELED_GROUPS = {"positive_like", "negative_like"}
EVALUATION_GROUPS = {
    "positive_like",
    "negative_like",
    "monitor_like",
    "common_cause_like",
    "unlabeled_other",
}
TRAIN_FEATURES = [
    "run_day_count",
    "pre_ews_day_count",
    "ews_warning_day_count",
    "pre_alarm_day_count",
    "prefault_B_day_count",
    "pre_alarm_max_run",
    "max_signal_count",
    "mean_signal_count",
    "any_data_bad",
    "data_bad_day_ratio",
    "cond_evt_day_ratio",
    "cond_evt_only_day_ratio",
    "cond_evt_same_day_early_corroborated_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "dtw_mid_or_hi_early_day_ratio",
    "hs_mid_or_hi_early_day_ratio",
    "max_recon_error",
    "p95_recon_error",
    "max_dtw_dist",
    "p95_dtw_dist",
    "max_hs_score",
    "p95_hs_score",
    "min_mid_ratio",
    "min_mid_v_ratio",
    "min_mid_i_ratio",
    "max_v_drop",
]
DISAGREEMENT_CLASSES = [
    "positive_captured_by_reference_not_logistic",
    "positive_captured_by_logistic_not_reference",
    "negative_promoted_by_logistic_not_reference",
    "negative_promoted_by_reference_not_logistic",
]
REQUIRED_FEATURE_TABLE_COLS = list(
    dict.fromkeys([*KEY_COLS, "run_day_count", "run_shape_class", "cohort_hint", *TRAIN_FEATURES])
)
REQUIRED_LABEL_PACK_COLS = [*KEY_COLS, "label_bucket_v2", "training_label_v2"]
REQUIRED_PROMOTION_COLS = [*KEY_COLS, "scenario_name"]
REQUIRED_V0_SCORE_COLS = [*KEY_COLS, "electrical_core_score", "electrical_core_minus_broadshape_050"]
REQUIRED_V2_SUMMARY_COLS = ["score_name", "fold_type", "mean_top20_positive_minus_negative"]
REQUIRED_V3_SUMMARY_COLS = ["scenario_name", "loso_mean_top20_positive_minus_negative", "time_mean_top20_positive_minus_negative"]

FOLD_COLS = [
    "fold_type",
    "fold_id",
    "method_name",
    "test_site",
    "train_positive_count",
    "train_negative_count",
    "test_positive_like_count",
    "test_negative_like_count",
    "test_monitor_like_count",
    "test_common_cause_like_count",
    "test_unlabeled_other_count",
    "top10_positive_like_count",
    "top10_negative_like_count",
    "top20_positive_like_count",
    "top20_negative_like_count",
    "top10_positive_minus_negative",
    "top20_positive_minus_negative",
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
    "run_day_count",
    "run_shape_class",
    "cohort_hint",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
    "logistic_v3_candidate_score",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "gap_reason_ko",
]
SUMMARY_COLS = [
    "summary_type",
    "fold_type",
    "comparison_target",
    "disagreement_class",
    "run_count",
    "median_run_day_count",
    "median_max_v_drop",
    "median_min_mid_v_ratio",
    "median_min_mid_ratio",
    "median_cond_evt_only_day_ratio",
    "median_ae_mid_or_hi_early_day_ratio",
    "median_mean_signal_count",
    "median_max_signal_count",
    "median_p95_recon_error",
    "recommended_next_direction",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose why the best weak-label promotion scenario still does not beat the deterministic reference."
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
    ensure_columns(df, REQUIRED_FEATURE_TABLE_COLS, path.name)
    df = normalize_key_cols(df)
    for col in REQUIRED_FEATURE_TABLE_COLS:
        if col in STRING_COLS:
            df[col] = df[col].map(normalize_text)
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, REQUIRED_FEATURE_TABLE_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_label_pack_v2(root: Path) -> pd.DataFrame:
    path = root / "_share" / LABEL_PACK_V2_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_LABEL_PACK_COLS, path.name)
    df = normalize_key_cols(df)
    df["label_bucket_v2"] = df["label_bucket_v2"].map(normalize_text)
    df["training_label_v2"] = df["training_label_v2"].map(normalize_text)
    df["evaluation_group"] = df["label_bucket_v2"].where(df["label_bucket_v2"].isin(EVALUATION_GROUPS), "unlabeled_other")
    return df.loc[:, [*KEY_COLS, "label_bucket_v2", "training_label_v2", "evaluation_group"]].drop_duplicates(
        subset=KEY_COLS, keep="first"
    )


def load_promotions(root: Path) -> pd.DataFrame:
    path = root / "_share" / PROMOTION_SCENARIOS_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_PROMOTION_COLS, path.name)
    df = normalize_key_cols(df)
    df["scenario_name"] = df["scenario_name"].map(normalize_text)
    df = df.loc[df["scenario_name"].eq(FIXED_SCENARIO_NAME), :].copy()
    if df.empty:
        raise SystemExit(f"scenario not found in promotion listing: {FIXED_SCENARIO_NAME}")
    return df.loc[:, [*KEY_COLS, "scenario_name"]].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_v0_scores(root: Path) -> pd.DataFrame:
    path = root / "_share" / V0_SCORES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_V0_SCORE_COLS, path.name)
    df = normalize_key_cols(df)
    for col in ["electrical_core_score", "electrical_core_minus_broadshape_050"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, REQUIRED_V0_SCORE_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_v2_summary(root: Path) -> pd.DataFrame:
    path = root / "_share" / V2_HOLDOUT_SUMMARY_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_V2_SUMMARY_COLS, path.name)
    df["score_name"] = df["score_name"].map(normalize_text)
    df["fold_type"] = df["fold_type"].map(normalize_text)
    df["mean_top20_positive_minus_negative"] = pd.to_numeric(df["mean_top20_positive_minus_negative"], errors="coerce")
    return df.loc[:, REQUIRED_V2_SUMMARY_COLS].copy()


def load_v3_summary(root: Path) -> pd.DataFrame:
    path = root / "_share" / V3_SCENARIO_SUMMARY_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_V3_SUMMARY_COLS, path.name)
    df["scenario_name"] = df["scenario_name"].map(normalize_text)
    for col in ["loso_mean_top20_positive_minus_negative", "time_mean_top20_positive_minus_negative"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    target = df.loc[df["scenario_name"].eq(FIXED_SCENARIO_NAME), :].copy()
    if target.empty:
        raise SystemExit(f"scenario summary missing row for: {FIXED_SCENARIO_NAME}")
    return target.reset_index(drop=True)


def prepare_universe(root: Path) -> pd.DataFrame:
    feature_df = load_feature_table(root)
    label_df = load_label_pack_v2(root)
    v0_df = load_v0_scores(root)
    merged = feature_df.merge(label_df, on=KEY_COLS, how="left", validate="one_to_one")
    merged = merged.merge(v0_df, on=KEY_COLS, how="left", validate="one_to_one")

    if merged["evaluation_group"].isna().any():
        missing_count = int(merged["evaluation_group"].isna().sum())
        raise SystemExit(f"missing v2 label rows for {missing_count} runs")

    missing_ref_cols = [
        col
        for col in ["electrical_core_score", "electrical_core_minus_broadshape_050"]
        if merged[col].isna().any()
    ]
    if missing_ref_cols:
        raise SystemExit(f"merged run universe missing reference scores: {missing_ref_cols}")

    merged["training_label_v2"] = merged["training_label_v2"].fillna("").map(normalize_text)
    merged["run_start_dt"] = pd.to_datetime(merged["run_start_date"], errors="coerce")
    return merged


def apply_promotions(universe: pd.DataFrame, promotions: pd.DataFrame) -> pd.DataFrame:
    promoted_keys = set(map(tuple, promotions[KEY_COLS].itertuples(index=False, name=None)))
    out = universe.copy()
    out["scenario_training_label"] = out["training_label_v2"]
    mask = out[KEY_COLS].apply(tuple, axis=1).isin(promoted_keys)
    out.loc[mask, "scenario_training_label"] = "positive"
    promoted_count = int(mask.sum())
    if promoted_count != len(promotions):
        raise SystemExit("promotion rows missing from run universe")
    return out


def compute_group_counts(df: pd.DataFrame) -> dict[str, int]:
    counts = df["evaluation_group"].value_counts(dropna=False)
    return {
        "positive_like": int(counts.get("positive_like", 0)),
        "negative_like": int(counts.get("negative_like", 0)),
        "monitor_like": int(counts.get("monitor_like", 0)),
        "common_cause_like": int(counts.get("common_cause_like", 0)),
        "unlabeled_other": int(counts.get("unlabeled_other", 0)),
    }


def build_raw_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    raw = df.loc[:, TRAIN_FEATURES].copy()
    for col in TRAIN_FEATURES:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
    return raw


def fit_robust_scaler(train_raw: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    medians = train_raw.median(numeric_only=True)
    q1 = train_raw.quantile(0.25, numeric_only=True)
    q3 = train_raw.quantile(0.75, numeric_only=True)
    iqr = q3 - q1
    iqr = iqr.where(iqr.abs() > 1e-9, 1.0)
    return medians, iqr


def apply_robust_scaler(raw: pd.DataFrame, medians: pd.Series, iqr: pd.Series) -> pd.DataFrame:
    imputed = raw.fillna(medians)
    scaled = (imputed - medians) / iqr
    return scaled.clip(-5.0, 5.0)


def rank_runs(df: pd.DataFrame, score_name: str) -> pd.DataFrame:
    ranked = df.copy()
    ranked["_score_value"] = pd.to_numeric(ranked[score_name], errors="coerce").fillna(float("-inf"))
    ranked = ranked.sort_values(
        ["_score_value", "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[False, False, True, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    return ranked


def fold_specs(universe: pd.DataFrame) -> list[dict[str, object]]:
    specs: list[dict[str, object]] = []
    for site in sorted(universe["site"].dropna().map(normalize_text).unique()):
        specs.append(
            {
                "fold_type": "leave_one_site_out",
                "fold_id": site,
                "test_site": site,
                "test_index": universe.index[universe["site"].eq(site)],
                "train_index": universe.index[~universe["site"].eq(site)],
            }
        )

    ordered = universe.sort_values(
        ["run_start_dt", "site", "panel_id", "run_end_date"],
        ascending=[True, True, True, True],
        na_position="last",
        kind="mergesort",
    ).reset_index()
    split_idx = int(len(ordered) * 0.7)
    specs.append(
        {
            "fold_type": "time_holdout_70_30",
            "fold_id": "time_holdout_70_30",
            "test_site": "",
            "test_index": ordered.loc[split_idx:, "index"] if split_idx < len(ordered) else pd.Index([], dtype=int),
            "train_index": ordered.loc[: split_idx - 1, "index"] if split_idx > 0 else pd.Index([], dtype=int),
        }
    )
    return specs


def compute_top_counts(ranked: pd.DataFrame, top_k: int) -> dict[str, object]:
    top_df = ranked.head(top_k).copy()
    counts = compute_group_counts(top_df)
    denom = float(len(top_df)) if len(top_df) else 1.0
    positive_rate = counts["positive_like"] / denom if len(top_df) else 0.0
    negative_rate = counts["negative_like"] / denom if len(top_df) else 0.0
    return {
        "positive_like_count": counts["positive_like"],
        "negative_like_count": counts["negative_like"],
        "monitor_like_count": counts["monitor_like"],
        "common_cause_like_count": counts["common_cause_like"],
        "unlabeled_other_count": counts["unlabeled_other"],
        "positive_minus_negative": positive_rate - negative_rate,
    }


def build_fold_row(
    fold_type: str,
    fold_id: str,
    test_site: str,
    method_name: str,
    train_positive_count: int,
    train_negative_count: int,
    test_counts: dict[str, int],
    ranked: pd.DataFrame,
) -> dict[str, object]:
    top10 = compute_top_counts(ranked, 10)
    top20 = compute_top_counts(ranked, 20)
    return {
        "fold_type": fold_type,
        "fold_id": fold_id,
        "method_name": method_name,
        "test_site": test_site,
        "train_positive_count": train_positive_count,
        "train_negative_count": train_negative_count,
        "test_positive_like_count": test_counts["positive_like"],
        "test_negative_like_count": test_counts["negative_like"],
        "test_monitor_like_count": test_counts["monitor_like"],
        "test_common_cause_like_count": test_counts["common_cause_like"],
        "test_unlabeled_other_count": test_counts["unlabeled_other"],
        "top10_positive_like_count": top10["positive_like_count"],
        "top10_negative_like_count": top10["negative_like_count"],
        "top20_positive_like_count": top20["positive_like_count"],
        "top20_negative_like_count": top20["negative_like_count"],
        "top10_positive_minus_negative": top10["positive_minus_negative"],
        "top20_positive_minus_negative": top20["positive_minus_negative"],
    }


def top_key_set(ranked: pd.DataFrame, top_k: int) -> set[tuple[str, str, str, str]]:
    if ranked.empty:
        return set()
    return set(map(tuple, ranked.head(top_k)[KEY_COLS].itertuples(index=False, name=None)))


def gap_reason(row: pd.Series, disagreement_class: str) -> str:
    if disagreement_class == "positive_captured_by_reference_not_logistic":
        if float(row["electrical_core_minus_broadshape_050"]) >= float(row["logistic_v3_candidate_score"]):
            return "deterministic reference는 높은 electrical severity를 반영했지만 learned scorer는 top20까지 올리지 못함"
        return "positive-like run인데 learned scorer ranking이 reference보다 낮아 누락됨"
    if disagreement_class == "positive_captured_by_logistic_not_reference":
        return "learned scorer가 precursor-like feature 조합을 더 강하게 반영해 reference보다 먼저 상향함"
    if disagreement_class == "negative_promoted_by_logistic_not_reference":
        return "learned scorer가 negative-like run의 전조형 패턴을 과대평가해 false promotion을 만들었을 가능성"
    return "reference가 sharp electrical severity를 높게 보지만 learned scorer는 negative-like 패턴으로 눌렀을 가능성"


def build_disagreement_cases(
    fold_type: str,
    fold_id: str,
    test_site: str,
    scored_test: pd.DataFrame,
) -> pd.DataFrame:
    logistic_ranked = rank_runs(scored_test, LOGISTIC_METHOD_NAME)
    reference_ranked = rank_runs(scored_test, REFERENCE_METHOD_NAME)
    logistic_top20 = top_key_set(logistic_ranked, 20)
    reference_top20 = top_key_set(reference_ranked, 20)

    test_df = scored_test.copy()
    test_df["_key"] = test_df[KEY_COLS].apply(tuple, axis=1)
    positive_mask = test_df["evaluation_group"].eq("positive_like")
    negative_mask = test_df["evaluation_group"].eq("negative_like")

    disagreements = {
        "positive_captured_by_reference_not_logistic": positive_mask
        & test_df["_key"].isin(reference_top20)
        & ~test_df["_key"].isin(logistic_top20),
        "positive_captured_by_logistic_not_reference": positive_mask
        & test_df["_key"].isin(logistic_top20)
        & ~test_df["_key"].isin(reference_top20),
        "negative_promoted_by_logistic_not_reference": negative_mask
        & test_df["_key"].isin(logistic_top20)
        & ~test_df["_key"].isin(reference_top20),
        "negative_promoted_by_reference_not_logistic": negative_mask
        & test_df["_key"].isin(reference_top20)
        & ~test_df["_key"].isin(logistic_top20),
    }

    rows: list[pd.DataFrame] = []
    for disagreement_class, mask in disagreements.items():
        subset = test_df.loc[mask, :].copy()
        if subset.empty:
            continue
        subset["fold_type"] = fold_type
        subset["fold_id"] = fold_id
        subset["test_site"] = test_site
        subset["disagreement_class"] = disagreement_class
        subset["logistic_v3_candidate_score"] = pd.to_numeric(subset[LOGISTIC_METHOD_NAME], errors="coerce")
        subset["gap_reason_ko"] = subset.apply(lambda row: gap_reason(row, disagreement_class), axis=1)
        rows.append(subset)

    if not rows:
        return pd.DataFrame(columns=CASE_COLS)

    combined = pd.concat(rows, ignore_index=True)
    return combined.reindex(columns=CASE_COLS)


def evaluate_fold(universe: pd.DataFrame, spec: dict[str, object]) -> tuple[list[dict[str, object]], pd.DataFrame]:
    fold_type = str(spec["fold_type"])
    fold_id = str(spec["fold_id"])
    test_site = str(spec["test_site"])
    train_index = list(spec["train_index"])
    test_index = list(spec["test_index"])

    train_df = universe.loc[train_index].copy()
    test_df = universe.loc[test_index].copy()
    train_labeled = train_df.loc[train_df["scenario_training_label"].isin(TRAIN_LABELS)].copy()
    train_positive_count = int(train_labeled["scenario_training_label"].eq("positive").sum())
    train_negative_count = int(train_labeled["scenario_training_label"].eq("negative").sum())
    test_counts = compute_group_counts(test_df) if not test_df.empty else {name: 0 for name in EVALUATION_GROUPS}

    if test_df.empty or train_labeled.empty or train_positive_count == 0 or train_negative_count == 0:
        rows = []
        for method_name in [LOGISTIC_METHOD_NAME, "electrical_core_score", REFERENCE_METHOD_NAME]:
            rows.append(
                {
                    "fold_type": fold_type,
                    "fold_id": fold_id,
                    "method_name": method_name,
                    "test_site": test_site,
                    "train_positive_count": train_positive_count,
                    "train_negative_count": train_negative_count,
                    "test_positive_like_count": test_counts["positive_like"],
                    "test_negative_like_count": test_counts["negative_like"],
                    "test_monitor_like_count": test_counts["monitor_like"],
                    "test_common_cause_like_count": test_counts["common_cause_like"],
                    "test_unlabeled_other_count": test_counts["unlabeled_other"],
                    "top10_positive_like_count": None,
                    "top10_negative_like_count": None,
                    "top20_positive_like_count": None,
                    "top20_negative_like_count": None,
                    "top10_positive_minus_negative": None,
                    "top20_positive_minus_negative": None,
                }
            )
        return rows, pd.DataFrame(columns=CASE_COLS)

    raw_train = build_raw_feature_matrix(train_labeled)
    medians, iqr = fit_robust_scaler(raw_train)
    scaled_train = apply_robust_scaler(raw_train, medians, iqr)
    y_train = train_labeled["scenario_training_label"].eq("positive").astype(int)
    logistic = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=0)
    logistic.fit(scaled_train, y_train)

    raw_test = build_raw_feature_matrix(test_df)
    scaled_test = apply_robust_scaler(raw_test, medians, iqr)
    scored_test = test_df.copy()
    scored_test[LOGISTIC_METHOD_NAME] = logistic.predict_proba(scaled_test)[:, 1]

    fold_rows = []
    for method_name in [LOGISTIC_METHOD_NAME, "electrical_core_score", REFERENCE_METHOD_NAME]:
        ranked = rank_runs(scored_test, method_name)
        fold_rows.append(
            build_fold_row(
                fold_type=fold_type,
                fold_id=fold_id,
                test_site=test_site,
                method_name=method_name,
                train_positive_count=train_positive_count,
                train_negative_count=train_negative_count,
                test_counts=test_counts,
                ranked=ranked,
            )
        )

    cases = build_disagreement_cases(fold_type, fold_id, test_site, scored_test)
    return fold_rows, cases


def recommendation_note(direction: str) -> str:
    mapping = {
        "try_site_conditioned_scaling": "positive miss가 특정 site에 몰려 있어 site-conditioned scaling 점검이 우선",
        "try_deterministic_plus_learned_hybrid": "reference가 높은 electrical severity positive를 더 잘 잡아 hybrid가 더 현실적임",
        "expand_positive_labels_further": "positive-like coverage가 아직 얕아 weak promotion보다 추가 label expansion이 우선",
        "stop_learned_scorer_for_now": "뚜렷한 구조보다 noisy disagreement가 많아 learned scorer를 당분간 보류하는 편이 안전",
    }
    return mapping.get(direction, "")


def choose_recommendation(
    cases_df: pd.DataFrame,
    promotions: pd.DataFrame,
    v2_summary: pd.DataFrame,
    v3_summary: pd.DataFrame,
) -> tuple[str, str]:
    positive_ref = cases_df.loc[cases_df["disagreement_class"].eq("positive_captured_by_reference_not_logistic")].copy()
    positive_log = cases_df.loc[cases_df["disagreement_class"].eq("positive_captured_by_logistic_not_reference")].copy()
    negative_log = cases_df.loc[cases_df["disagreement_class"].eq("negative_promoted_by_logistic_not_reference")].copy()

    loso_ref = v2_summary.loc[
        v2_summary["score_name"].eq(REFERENCE_METHOD_NAME) & v2_summary["fold_type"].eq("leave_one_site_out"),
        "mean_top20_positive_minus_negative",
    ]
    loso_v3 = pd.to_numeric(v3_summary.loc[0, "loso_mean_top20_positive_minus_negative"], errors="coerce")
    ref_gap = float(loso_ref.iloc[0] - loso_v3) if not loso_ref.empty and pd.notna(loso_v3) else 0.0

    if not positive_ref.empty:
        dominant_share = float(positive_ref["site"].value_counts(normalize=True).max())
        if dominant_share >= 0.6 and len(positive_ref) >= 2:
            return "try_site_conditioned_scaling", recommendation_note("try_site_conditioned_scaling")

        positive_log_median = (
            float(positive_log["electrical_core_minus_broadshape_050"].median()) if not positive_log.empty else float("-inf")
        )
        if (
            float(positive_ref["electrical_core_minus_broadshape_050"].median()) > max(positive_log_median, 0.7)
            and ref_gap >= 0.0
        ):
            return "try_deterministic_plus_learned_hybrid", recommendation_note("try_deterministic_plus_learned_hybrid")

    promoted_sites = promotions["site"].dropna().map(normalize_text).nunique()
    if ref_gap >= 0.0 and (len(positive_ref) >= len(negative_log) or promoted_sites <= 4):
        return "expand_positive_labels_further", recommendation_note("expand_positive_labels_further")

    return "stop_learned_scorer_for_now", recommendation_note("stop_learned_scorer_for_now")


def build_summary(
    cases_df: pd.DataFrame,
    promotions: pd.DataFrame,
    v2_summary: pd.DataFrame,
    v3_summary: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for fold_type in ["leave_one_site_out", "time_holdout_70_30"]:
        for disagreement_class in DISAGREEMENT_CLASSES:
            subset = cases_df.loc[
                cases_df["fold_type"].eq(fold_type) & cases_df["disagreement_class"].eq(disagreement_class),
                :,
            ].copy()
            rows.append(
                {
                    "summary_type": "disagreement_summary",
                    "fold_type": fold_type,
                    "comparison_target": COMPARISON_TARGET,
                    "disagreement_class": disagreement_class,
                    "run_count": int(len(subset)),
                    "median_run_day_count": subset["run_day_count"].median() if not subset.empty else None,
                    "median_max_v_drop": subset["max_v_drop"].median() if not subset.empty else None,
                    "median_min_mid_v_ratio": subset["min_mid_v_ratio"].median() if not subset.empty else None,
                    "median_min_mid_ratio": subset["min_mid_ratio"].median() if not subset.empty else None,
                    "median_cond_evt_only_day_ratio": subset["cond_evt_only_day_ratio"].median() if not subset.empty else None,
                    "median_ae_mid_or_hi_early_day_ratio": subset["ae_mid_or_hi_early_day_ratio"].median()
                    if not subset.empty
                    else None,
                    "median_mean_signal_count": subset["mean_signal_count"].median() if not subset.empty else None,
                    "median_max_signal_count": subset["max_signal_count"].median() if not subset.empty else None,
                    "median_p95_recon_error": subset["p95_recon_error"].median() if not subset.empty else None,
                    "recommended_next_direction": "",
                    "note_ko": (
                        "해당 disagreement class가 없어 추가 해석 없음"
                        if subset.empty
                        else {
                            "positive_captured_by_reference_not_logistic": "reference가 잡는 positive-like run을 learned scorer가 놓친 패턴",
                            "positive_captured_by_logistic_not_reference": "learned scorer가 reference보다 먼저 끌어올린 positive-like run 패턴",
                            "negative_promoted_by_logistic_not_reference": "learned scorer의 false promotion 성향을 보여 주는 negative-like run 패턴",
                            "negative_promoted_by_reference_not_logistic": "reference의 false promotion 성향을 보여 주는 negative-like run 패턴",
                        }.get(disagreement_class, "")
                    ),
                }
            )

    recommended_next_direction, rec_note = choose_recommendation(cases_df, promotions, v2_summary, v3_summary)
    rows.append(
        {
            "summary_type": "overall_recommendation",
            "fold_type": "overall",
            "comparison_target": COMPARISON_TARGET,
            "disagreement_class": "",
            "run_count": None,
            "median_run_day_count": None,
            "median_max_v_drop": None,
            "median_min_mid_v_ratio": None,
            "median_min_mid_ratio": None,
            "median_cond_evt_only_day_ratio": None,
            "median_ae_mid_or_hi_early_day_ratio": None,
            "median_mean_signal_count": None,
            "median_max_signal_count": None,
            "median_p95_recon_error": None,
            "recommended_next_direction": recommended_next_direction,
            "note_ko": rec_note,
        }
    )
    return pd.DataFrame(rows).reindex(columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    promotions = load_promotions(root)
    v2_summary = load_v2_summary(root)
    v3_summary = load_v3_summary(root)
    universe = apply_promotions(prepare_universe(root), promotions)

    fold_rows: list[dict[str, object]] = []
    case_frames: list[pd.DataFrame] = []
    for spec in fold_specs(universe):
        rows, cases = evaluate_fold(universe, spec)
        fold_rows.extend(rows)
        if not cases.empty:
            case_frames.append(cases)

    folds_df = pd.DataFrame(fold_rows).reindex(columns=FOLD_COLS)
    cases_df = pd.concat(case_frames, ignore_index=True) if case_frames else pd.DataFrame(columns=CASE_COLS)
    summary_df = build_summary(cases_df, promotions, v2_summary, v3_summary)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    folds_df.to_csv(share_dir / FOLDS_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    cases_df.to_csv(share_dir / CASES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
