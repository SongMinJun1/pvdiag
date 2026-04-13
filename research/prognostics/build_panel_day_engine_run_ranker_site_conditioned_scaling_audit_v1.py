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
V3_SCENARIO_SUMMARY_NAME = "panel_day_engine_run_ranker_v3_scenario_holdout_summary_v1.csv"

FOLD_SCORES_OUTPUT_NAME = "panel_day_engine_run_ranker_site_conditioned_scaling_fold_scores_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_run_ranker_site_conditioned_scaling_summary_v1.csv"
CASES_OUTPUT_NAME = "panel_day_engine_run_ranker_site_conditioned_scaling_cases_v1.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
STRING_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "run_shape_class", "cohort_hint"]
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

FIXED_SCENARIO_NAME = "p1_plus_site_balanced_p2"
GLOBAL_METHOD_NAME = "logistic_v3_global_scaling"
SITE_METHOD_NAME = "logistic_v3_site_conditioned_scaling"
REFERENCE_METHOD_NAME = "electrical_core_minus_broadshape_050"
METHOD_NAMES = [GLOBAL_METHOD_NAME, SITE_METHOD_NAME, REFERENCE_METHOD_NAME]
DISAGREEMENT_CLASSES = [
    "positive_captured_by_site_scaled_not_global",
    "positive_captured_by_reference_not_site_scaled",
    "negative_promoted_by_site_scaled_not_global",
]

REQUIRED_FEATURE_TABLE_COLS = list(
    dict.fromkeys([*KEY_COLS, "run_day_count", "run_shape_class", "cohort_hint", *TRAIN_FEATURES])
)
REQUIRED_LABEL_PACK_COLS = [*KEY_COLS, "label_bucket_v2", "training_label_v2"]
REQUIRED_PROMOTION_COLS = [*KEY_COLS, "scenario_name"]
REQUIRED_V0_SCORE_COLS = [*KEY_COLS, "electrical_core_minus_broadshape_050"]
REQUIRED_V3_SUMMARY_COLS = [
    "scenario_name",
    "loso_mean_top20_positive_minus_negative",
    "time_mean_top20_positive_minus_negative",
]

FOLD_SCORE_COLS = [
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
    "labeled_test_auc",
    "labeled_test_average_precision",
    "top10_positive_like_count",
    "top10_negative_like_count",
    "top20_positive_like_count",
    "top20_negative_like_count",
    "top10_positive_minus_negative",
    "top20_positive_minus_negative",
    "skip_reason",
]
SUMMARY_COLS = [
    "method_name",
    "fold_type",
    "valid_fold_count",
    "mean_labeled_test_auc",
    "mean_labeled_test_average_precision",
    "mean_top10_positive_minus_negative",
    "mean_top20_positive_minus_negative",
    "delta_mean_top10_vs_global_logistic",
    "delta_mean_top20_vs_global_logistic",
    "delta_mean_top10_vs_reference",
    "delta_mean_top20_vs_reference",
    "note_ko",
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
    "cohort_hint",
    "electrical_core_minus_broadshape_050",
    "logistic_v3_global_scaling_score",
    "logistic_v3_site_conditioned_scaling_score",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "scaling_gap_reason_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit whether site-conditioned scaling improves the learned run scorer under the best weak-label promotion scenario."
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
        subset=KEY_COLS,
        keep="first",
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
    df["electrical_core_minus_broadshape_050"] = pd.to_numeric(
        df["electrical_core_minus_broadshape_050"], errors="coerce"
    )
    return df.loc[:, REQUIRED_V0_SCORE_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_v3_summary(root: Path) -> pd.Series:
    path = root / "_share" / V3_SCENARIO_SUMMARY_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_V3_SUMMARY_COLS, path.name)
    df["scenario_name"] = df["scenario_name"].map(normalize_text)
    for col in ["loso_mean_top20_positive_minus_negative", "time_mean_top20_positive_minus_negative"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    target = df.loc[df["scenario_name"].eq(FIXED_SCENARIO_NAME), :].copy()
    if target.empty:
        raise SystemExit(f"scenario summary missing row for: {FIXED_SCENARIO_NAME}")
    return target.iloc[0]


def prepare_universe(root: Path) -> pd.DataFrame:
    feature_df = load_feature_table(root)
    label_df = load_label_pack_v2(root)
    v0_df = load_v0_scores(root)

    merged = feature_df.merge(label_df, on=KEY_COLS, how="left", validate="one_to_one")
    merged = merged.merge(v0_df, on=KEY_COLS, how="left", validate="one_to_one")

    if merged["evaluation_group"].isna().any():
        missing_count = int(merged["evaluation_group"].isna().sum())
        raise SystemExit(f"missing v2 label rows for {missing_count} runs")

    if merged["electrical_core_minus_broadshape_050"].isna().any():
        raise SystemExit("merged run universe missing deterministic reference scores")

    merged["training_label_v2"] = merged["training_label_v2"].fillna("").map(normalize_text)
    merged["run_start_dt"] = pd.to_datetime(merged["run_start_date"], errors="coerce")
    return merged


def apply_promotions(universe: pd.DataFrame, promotions: pd.DataFrame) -> pd.DataFrame:
    promoted_keys = set(map(tuple, promotions[KEY_COLS].itertuples(index=False, name=None)))
    out = universe.copy()
    out["scenario_training_label"] = out["training_label_v2"]
    mask = out[KEY_COLS].apply(tuple, axis=1).isin(promoted_keys)
    out.loc[mask, "scenario_training_label"] = "positive"
    if int(mask.sum()) != len(promotions):
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


def fit_site_conditioned_scaler(observable_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    raw = build_raw_feature_matrix(observable_df)
    raw["site"] = observable_df["site"].map(normalize_text).values

    grouped = raw.groupby("site", dropna=False)
    site_medians = grouped[TRAIN_FEATURES].median()
    q1 = grouped[TRAIN_FEATURES].quantile(0.25)
    q3 = grouped[TRAIN_FEATURES].quantile(0.75)
    site_iqr = (q3 - q1).where((q3 - q1).abs() > 1e-9, 1.0)

    fallback_medians, fallback_iqr = fit_robust_scaler(raw.loc[:, TRAIN_FEATURES])
    return site_medians, site_iqr, fallback_medians, fallback_iqr


def apply_site_conditioned_scaler(
    df: pd.DataFrame,
    site_medians: pd.DataFrame,
    site_iqr: pd.DataFrame,
    fallback_medians: pd.Series,
    fallback_iqr: pd.Series,
) -> pd.DataFrame:
    raw = build_raw_feature_matrix(df)
    merged = raw.copy()
    merged["site"] = df["site"].map(normalize_text).values

    medians_lookup = site_medians.add_suffix("__median").reset_index()
    iqr_lookup = site_iqr.add_suffix("__iqr").reset_index()
    merged = merged.merge(medians_lookup, on="site", how="left")
    merged = merged.merge(iqr_lookup, on="site", how="left")

    scaled = pd.DataFrame(index=df.index)
    for col in TRAIN_FEATURES:
        median_values = pd.to_numeric(merged.get(f"{col}__median"), errors="coerce").fillna(fallback_medians[col])
        iqr_values = pd.to_numeric(merged.get(f"{col}__iqr"), errors="coerce").fillna(fallback_iqr[col])
        iqr_values = iqr_values.where(iqr_values.abs() > 1e-9, 1.0)
        values = pd.to_numeric(merged[col], errors="coerce").fillna(median_values)
        scaled[col] = ((values - median_values) / iqr_values).clip(-5.0, 5.0).to_numpy()
    return scaled


def rank_runs(df: pd.DataFrame, score_name: str) -> pd.DataFrame:
    ranked = df.copy()
    ranked["_score_value"] = pd.to_numeric(ranked[score_name], errors="coerce").fillna(float("-inf"))
    ranked = ranked.sort_values(
        ["_score_value", "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[False, False, True, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    return ranked


def compute_holdout_metrics(test_df: pd.DataFrame, score_name: str) -> dict[str, object]:
    ranked = rank_runs(test_df, score_name)
    labeled = ranked.loc[ranked["evaluation_group"].isin(LABELED_GROUPS)].copy()

    auc = None
    ap = None
    if not labeled.empty and labeled["evaluation_group"].nunique() == 2:
        y_true = labeled["evaluation_group"].eq("positive_like").astype(int)
        auc = float(roc_auc_score(y_true, labeled["_score_value"]))
        ap = float(average_precision_score(y_true, labeled["_score_value"]))

    top_stats: dict[int, dict[str, float]] = {}
    for top_k in TOP_K_VALUES:
        top = ranked.head(top_k).copy()
        counts = compute_group_counts(top)
        denom = float(len(top)) if len(top) else 1.0
        positive_rate = counts["positive_like"] / denom if len(top) else 0.0
        negative_rate = counts["negative_like"] / denom if len(top) else 0.0
        top_stats[top_k] = {
            "positive_like": counts["positive_like"],
            "negative_like": counts["negative_like"],
            "positive_minus_negative": positive_rate - negative_rate,
        }

    return {
        "labeled_test_auc": auc,
        "labeled_test_average_precision": ap,
        "top10_positive_like_count": top_stats[10]["positive_like"],
        "top10_negative_like_count": top_stats[10]["negative_like"],
        "top20_positive_like_count": top_stats[20]["positive_like"],
        "top20_negative_like_count": top_stats[20]["negative_like"],
        "top10_positive_minus_negative": top_stats[10]["positive_minus_negative"],
        "top20_positive_minus_negative": top_stats[20]["positive_minus_negative"],
    }


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


def top_key_set(ranked: pd.DataFrame, top_k: int) -> set[tuple[str, str, str, str]]:
    if ranked.empty:
        return set()
    return set(map(tuple, ranked.head(top_k)[KEY_COLS].itertuples(index=False, name=None)))


def scaling_gap_reason(row: pd.Series, disagreement_class: str) -> str:
    if disagreement_class == "positive_captured_by_site_scaled_not_global":
        return "site별 분포로 정규화하니 같은 site 내부 상대 이상도가 더 선명해져 global scaling보다 상향됨"
    if disagreement_class == "positive_captured_by_reference_not_site_scaled":
        return "deterministic electrical severity는 높지만 site-conditioned scaling 이후에도 learned rank가 reference top20을 못 따라감"
    return "site-conditioned scaling이 site 내부 상대 이상도를 강조하면서 negative-like run을 과상향했을 가능성"


def build_disagreement_cases(
    fold_type: str,
    fold_id: str,
    test_site: str,
    scored_test: pd.DataFrame,
) -> pd.DataFrame:
    site_ranked = rank_runs(scored_test, SITE_METHOD_NAME)
    global_ranked = rank_runs(scored_test, GLOBAL_METHOD_NAME)
    reference_ranked = rank_runs(scored_test, REFERENCE_METHOD_NAME)

    site_top20 = top_key_set(site_ranked, 20)
    global_top20 = top_key_set(global_ranked, 20)
    reference_top20 = top_key_set(reference_ranked, 20)

    test_df = scored_test.copy()
    test_df["_key"] = test_df[KEY_COLS].apply(tuple, axis=1)
    positive_mask = test_df["evaluation_group"].eq("positive_like")
    negative_mask = test_df["evaluation_group"].eq("negative_like")

    disagreements = {
        "positive_captured_by_site_scaled_not_global": positive_mask
        & test_df["_key"].isin(site_top20)
        & ~test_df["_key"].isin(global_top20),
        "positive_captured_by_reference_not_site_scaled": positive_mask
        & test_df["_key"].isin(reference_top20)
        & ~test_df["_key"].isin(site_top20),
        "negative_promoted_by_site_scaled_not_global": negative_mask
        & test_df["_key"].isin(site_top20)
        & ~test_df["_key"].isin(global_top20),
    }

    rows: list[pd.DataFrame] = []
    for disagreement_class in DISAGREEMENT_CLASSES:
        subset = test_df.loc[disagreements[disagreement_class], :].copy()
        if subset.empty:
            continue
        subset["fold_type"] = fold_type
        subset["fold_id"] = fold_id
        subset["test_site"] = test_site
        subset["disagreement_class"] = disagreement_class
        subset["logistic_v3_global_scaling_score"] = pd.to_numeric(subset[GLOBAL_METHOD_NAME], errors="coerce")
        subset["logistic_v3_site_conditioned_scaling_score"] = pd.to_numeric(subset[SITE_METHOD_NAME], errors="coerce")
        subset["scaling_gap_reason_ko"] = subset.apply(
            lambda row: scaling_gap_reason(row, disagreement_class),
            axis=1,
        )
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

    skip_reason = ""
    if test_df.empty:
        skip_reason = "empty_test_universe"
    elif train_labeled.empty or train_positive_count == 0 or train_negative_count == 0:
        skip_reason = "train_labeled_missing_class"

    if skip_reason:
        rows: list[dict[str, object]] = []
        for method_name in METHOD_NAMES:
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
                    "labeled_test_auc": None,
                    "labeled_test_average_precision": None,
                    "top10_positive_like_count": None,
                    "top10_negative_like_count": None,
                    "top20_positive_like_count": None,
                    "top20_negative_like_count": None,
                    "top10_positive_minus_negative": None,
                    "top20_positive_minus_negative": None,
                    "skip_reason": skip_reason,
                }
            )
        return rows, pd.DataFrame(columns=CASE_COLS)

    raw_train = build_raw_feature_matrix(train_labeled)
    global_medians, global_iqr = fit_robust_scaler(raw_train)
    global_train = apply_robust_scaler(raw_train, global_medians, global_iqr)

    observable_df = pd.concat([train_df, test_df], ignore_index=True)
    site_medians, site_iqr, fallback_medians, fallback_iqr = fit_site_conditioned_scaler(observable_df)
    site_train = apply_site_conditioned_scaler(train_labeled, site_medians, site_iqr, fallback_medians, fallback_iqr)

    y_train = train_labeled["scenario_training_label"].eq("positive").astype(int)

    global_model = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=0)
    global_model.fit(global_train, y_train)

    site_model = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=0)
    site_model.fit(site_train, y_train)

    raw_test = build_raw_feature_matrix(test_df)
    global_test = apply_robust_scaler(raw_test, global_medians, global_iqr)
    site_test = apply_site_conditioned_scaler(test_df, site_medians, site_iqr, fallback_medians, fallback_iqr)

    scored_test = test_df.copy()
    scored_test[GLOBAL_METHOD_NAME] = global_model.predict_proba(global_test)[:, 1]
    scored_test[SITE_METHOD_NAME] = site_model.predict_proba(site_test)[:, 1]

    fold_rows: list[dict[str, object]] = []
    for method_name in METHOD_NAMES:
        metric_row = compute_holdout_metrics(scored_test, method_name)
        fold_rows.append(
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
                **metric_row,
                "skip_reason": "",
            }
        )

    case_df = build_disagreement_cases(fold_type, fold_id, test_site, scored_test)
    return fold_rows, case_df


def build_summary(fold_scores: pd.DataFrame, v3_summary_row: pd.Series) -> pd.DataFrame:
    if fold_scores.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)

    rows: list[dict[str, object]] = []
    all_fold_counts = (
        fold_scores[["fold_type", "fold_id"]].drop_duplicates().groupby("fold_type", dropna=False).size().to_dict()
    )

    aggregates: dict[tuple[str, str], dict[str, object]] = {}
    for (method_name, fold_type), group in fold_scores.groupby(["method_name", "fold_type"], dropna=False):
        valid_group = group.loc[group["skip_reason"].eq("")].copy()
        total_folds = int(all_fold_counts.get(fold_type, 0))
        if valid_group.empty:
            aggregates[(str(method_name), str(fold_type))] = {
                "valid_fold_count": 0,
                "mean_labeled_test_auc": None,
                "mean_labeled_test_average_precision": None,
                "mean_top10_positive_minus_negative": None,
                "mean_top20_positive_minus_negative": None,
                "total_folds": total_folds,
            }
            continue

        aggregates[(str(method_name), str(fold_type))] = {
            "valid_fold_count": int(len(valid_group)),
            "mean_labeled_test_auc": float(valid_group["labeled_test_auc"].mean()),
            "mean_labeled_test_average_precision": float(valid_group["labeled_test_average_precision"].mean()),
            "mean_top10_positive_minus_negative": float(valid_group["top10_positive_minus_negative"].mean()),
            "mean_top20_positive_minus_negative": float(valid_group["top20_positive_minus_negative"].mean()),
            "total_folds": total_folds,
        }

    prior_v3_top20 = {
        "leave_one_site_out": float(v3_summary_row["loso_mean_top20_positive_minus_negative"]),
        "time_holdout_70_30": float(v3_summary_row["time_mean_top20_positive_minus_negative"]),
    }

    for method_name in METHOD_NAMES:
        for fold_type in ["leave_one_site_out", "time_holdout_70_30"]:
            agg = aggregates.get((method_name, fold_type))
            if agg is None:
                continue
            global_agg = aggregates.get((GLOBAL_METHOD_NAME, fold_type), {})
            reference_agg = aggregates.get((REFERENCE_METHOD_NAME, fold_type), {})
            current_top10 = agg["mean_top10_positive_minus_negative"]
            current_top20 = agg["mean_top20_positive_minus_negative"]
            global_top10 = global_agg.get("mean_top10_positive_minus_negative")
            global_top20 = global_agg.get("mean_top20_positive_minus_negative")
            reference_top10 = reference_agg.get("mean_top10_positive_minus_negative")
            reference_top20 = reference_agg.get("mean_top20_positive_minus_negative")

            delta_top10_vs_global = None if current_top10 is None or global_top10 is None else current_top10 - global_top10
            delta_top20_vs_global = None if current_top20 is None or global_top20 is None else current_top20 - global_top20
            delta_top10_vs_reference = None if current_top10 is None or reference_top10 is None else current_top10 - reference_top10
            delta_top20_vs_reference = None if current_top20 is None or reference_top20 is None else current_top20 - reference_top20

            if agg["valid_fold_count"] == 0:
                note_ko = f"유효 fold 없음 ({agg['total_folds']}개 중 0개); fixed scenario={FIXED_SCENARIO_NAME}"
            elif method_name == SITE_METHOD_NAME:
                note_ko = (
                    "site observable distribution을 이용한 exploratory scaling audit; "
                    f"fixed scenario baseline top20={prior_v3_top20[fold_type]:.4f}"
                )
            elif method_name == GLOBAL_METHOD_NAME:
                note_ko = f"global robust scaling baseline; fixed scenario prior top20={prior_v3_top20[fold_type]:.4f}"
            else:
                note_ko = "deterministic reference for comparison only"

            rows.append(
                {
                    "method_name": method_name,
                    "fold_type": fold_type,
                    "valid_fold_count": agg["valid_fold_count"],
                    "mean_labeled_test_auc": agg["mean_labeled_test_auc"],
                    "mean_labeled_test_average_precision": agg["mean_labeled_test_average_precision"],
                    "mean_top10_positive_minus_negative": current_top10,
                    "mean_top20_positive_minus_negative": current_top20,
                    "delta_mean_top10_vs_global_logistic": delta_top10_vs_global,
                    "delta_mean_top20_vs_global_logistic": delta_top20_vs_global,
                    "delta_mean_top10_vs_reference": delta_top10_vs_reference,
                    "delta_mean_top20_vs_reference": delta_top20_vs_reference,
                    "note_ko": note_ko,
                }
            )

    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    universe = prepare_universe(root)
    promotions = load_promotions(root)
    v3_summary_row = load_v3_summary(root)
    scenario_universe = apply_promotions(universe, promotions)

    fold_rows: list[dict[str, object]] = []
    case_frames: list[pd.DataFrame] = []
    for spec in fold_specs(scenario_universe):
        rows, case_df = evaluate_fold(scenario_universe, spec)
        fold_rows.extend(rows)
        if not case_df.empty:
            case_frames.append(case_df)

    fold_scores = pd.DataFrame(fold_rows, columns=FOLD_SCORE_COLS)
    case_output = (
        pd.concat(case_frames, ignore_index=True).reindex(columns=CASE_COLS)
        if case_frames
        else pd.DataFrame(columns=CASE_COLS)
    )
    summary = build_summary(fold_scores, v3_summary_row)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    fold_scores.to_csv(share_dir / FOLD_SCORES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    case_output.to_csv(share_dir / CASES_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
