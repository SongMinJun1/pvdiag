#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression

FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
LABEL_PACK_V2_NAME = "panel_day_engine_run_label_pack_v2.csv"
PROMOTION_SCENARIOS_NAME = "panel_day_engine_run_label_promotion_scenarios_v1.csv"
V0_SCORES_NAME = "panel_day_engine_run_ranker_v0_scores.csv"
SITE_SCALING_SUMMARY_NAME = "panel_day_engine_run_ranker_site_conditioned_scaling_summary_v1.csv"

SUMMARY_OUTPUT_NAME = "panel_day_engine_run_ranker_hybrid_summary_v1.csv"
TOPK_OUTPUT_NAME = "panel_day_engine_run_ranker_hybrid_topk_yield_v1.csv"
CASES_OUTPUT_NAME = "panel_day_engine_run_ranker_hybrid_cases_v1.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
STRING_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "run_shape_class", "cohort_hint"]
TOP_K_VALUES = [10, 20]
TRAIN_LABELS = {"positive", "negative"}
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
REFERENCE_METHOD_NAME = "reference_only"
REFERENCE_SCORE_COL = "electrical_core_minus_broadshape_050"
GLOBAL_BASELINE_METHOD_NAME = "logistic_v3_global_scaling"
GLOBAL_LEARNED_SCORE_COL = "logistic_global_scaling_score"
SITE_LEARNED_SCORE_COL = "logistic_site_conditioned_scaling_score"

HYBRID_SPECS = [
    {"method_name": "hybrid_ref50_global", "shortlist_size": 50, "learned_score_col": GLOBAL_LEARNED_SCORE_COL},
    {"method_name": "hybrid_ref100_global", "shortlist_size": 100, "learned_score_col": GLOBAL_LEARNED_SCORE_COL},
    {"method_name": "hybrid_ref50_site", "shortlist_size": 50, "learned_score_col": SITE_LEARNED_SCORE_COL},
    {"method_name": "hybrid_ref100_site", "shortlist_size": 100, "learned_score_col": SITE_LEARNED_SCORE_COL},
]
VISIBLE_METHOD_NAMES = [REFERENCE_METHOD_NAME, *[spec["method_name"] for spec in HYBRID_SPECS]]
DISAGREEMENT_CLASSES = [
    "positive_captured_by_hybrid_not_reference",
    "positive_captured_by_reference_not_hybrid",
    "negative_promoted_by_hybrid_not_reference",
]

REQUIRED_FEATURE_TABLE_COLS = list(
    dict.fromkeys([*KEY_COLS, "run_day_count", "run_shape_class", "cohort_hint", *TRAIN_FEATURES])
)
REQUIRED_LABEL_PACK_COLS = [*KEY_COLS, "label_bucket_v2", "training_label_v2"]
REQUIRED_PROMOTION_COLS = [*KEY_COLS, "scenario_name"]
REQUIRED_V0_SCORE_COLS = [*KEY_COLS, REFERENCE_SCORE_COL]
REQUIRED_SITE_SCALING_SUMMARY_COLS = ["method_name", "fold_type", "mean_top20_positive_minus_negative"]

TOPK_COLS = [
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
    "skip_reason",
]
SUMMARY_COLS = [
    "method_name",
    "fold_type",
    "valid_fold_count",
    "mean_top10_positive_minus_negative",
    "mean_top20_positive_minus_negative",
    "delta_mean_top10_vs_reference",
    "delta_mean_top20_vs_reference",
    "delta_mean_top10_vs_global_logistic",
    "delta_mean_top20_vs_global_logistic",
    "note_ko",
]
CASE_COLS = [
    "fold_type",
    "fold_id",
    "test_site",
    "method_name",
    "disagreement_class",
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "cohort_hint",
    "electrical_core_minus_broadshape_050",
    "logistic_global_scaling_score",
    "logistic_site_conditioned_scaling_score",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "hybrid_gap_reason_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit deterministic-plus-learned hybrid run ranking."
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
    df[REFERENCE_SCORE_COL] = pd.to_numeric(df[REFERENCE_SCORE_COL], errors="coerce")
    return df.loc[:, REQUIRED_V0_SCORE_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_site_scaling_summary(root: Path) -> pd.DataFrame:
    path = root / "_share" / SITE_SCALING_SUMMARY_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_SITE_SCALING_SUMMARY_COLS, path.name)
    df["method_name"] = df["method_name"].map(normalize_text)
    df["fold_type"] = df["fold_type"].map(normalize_text)
    df["mean_top20_positive_minus_negative"] = pd.to_numeric(df["mean_top20_positive_minus_negative"], errors="coerce")
    return df.loc[:, REQUIRED_SITE_SCALING_SUMMARY_COLS].copy()


def prepare_universe(root: Path) -> pd.DataFrame:
    feature_df = load_feature_table(root)
    label_df = load_label_pack_v2(root)
    v0_df = load_v0_scores(root)
    merged = feature_df.merge(label_df, on=KEY_COLS, how="left", validate="one_to_one")
    merged = merged.merge(v0_df, on=KEY_COLS, how="left", validate="one_to_one")

    if merged["evaluation_group"].isna().any():
        raise SystemExit(f"missing v2 label rows for {int(merged['evaluation_group'].isna().sum())} runs")
    if merged[REFERENCE_SCORE_COL].isna().any():
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
    iqr = (q3 - q1).where((q3 - q1).abs() > 1e-9, 1.0)
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


def score_test_universe(train_df: pd.DataFrame, test_df: pd.DataFrame, train_labeled: pd.DataFrame) -> pd.DataFrame:
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
    scored_test[GLOBAL_LEARNED_SCORE_COL] = global_model.predict_proba(global_test)[:, 1]
    scored_test[SITE_LEARNED_SCORE_COL] = site_model.predict_proba(site_test)[:, 1]
    return scored_test


def build_hybrid_ranking(scored_test: pd.DataFrame, learned_score_col: str, shortlist_size: int) -> pd.DataFrame:
    reference_ranked = rank_runs(scored_test, REFERENCE_SCORE_COL).copy()
    reference_ranked["_reference_rank"] = range(len(reference_ranked))
    shortlist_keys = set(map(tuple, reference_ranked.head(shortlist_size)[KEY_COLS].itertuples(index=False, name=None)))
    reference_ranked["_key"] = reference_ranked[KEY_COLS].apply(tuple, axis=1)
    reference_ranked["_in_shortlist"] = reference_ranked["_key"].isin(shortlist_keys)

    shortlist_df = reference_ranked.loc[reference_ranked["_in_shortlist"]].copy()
    shortlist_df["_learned_score"] = pd.to_numeric(shortlist_df[learned_score_col], errors="coerce").fillna(float("-inf"))
    shortlist_df = shortlist_df.sort_values(
        ["_learned_score", REFERENCE_SCORE_COL, "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[False, False, False, True, True, True, True],
        kind="mergesort",
    )

    outside_df = reference_ranked.loc[~reference_ranked["_in_shortlist"]].copy()
    outside_df = outside_df.sort_values("_reference_rank", ascending=True, kind="mergesort")

    hybrid = pd.concat([shortlist_df, outside_df], ignore_index=True)
    return hybrid.drop(columns=["_reference_rank", "_key", "_in_shortlist", "_learned_score"], errors="ignore")


def compute_ranked_metrics(ranked: pd.DataFrame) -> dict[str, object]:
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
    return set(map(tuple, ranked.head(top_k)[KEY_COLS].itertuples(index=False, name=None)))


def hybrid_gap_reason(disagreement_class: str, method_name: str) -> str:
    if disagreement_class == "positive_captured_by_hybrid_not_reference":
        if method_name.endswith("_site"):
            return "deterministic shortlist는 유지하면서 exploratory site-conditioned learned rerank가 positive-like run을 shortlist 상단으로 끌어올림"
        return "deterministic shortlist는 유지하면서 global learned rerank가 positive-like run을 shortlist 상단으로 끌어올림"
    if disagreement_class == "positive_captured_by_reference_not_hybrid":
        return "deterministic reference는 잡던 positive-like run인데 hybrid 내부 재정렬에서 밀려 top20 밖으로 내려감"
    return "hybrid shortlist 내부 learned rerank가 negative-like run을 과상향했을 가능성"


def build_case_rows(
    fold_type: str,
    fold_id: str,
    test_site: str,
    method_name: str,
    ranked_hybrid: pd.DataFrame,
    ranked_reference: pd.DataFrame,
    scored_test: pd.DataFrame,
) -> pd.DataFrame:
    hybrid_top20 = top_key_set(ranked_hybrid, 20)
    reference_top20 = top_key_set(ranked_reference, 20)

    test_df = scored_test.copy()
    test_df["_key"] = test_df[KEY_COLS].apply(tuple, axis=1)
    positive_mask = test_df["evaluation_group"].eq("positive_like")
    negative_mask = test_df["evaluation_group"].eq("negative_like")

    class_masks = {
        "positive_captured_by_hybrid_not_reference": positive_mask
        & test_df["_key"].isin(hybrid_top20)
        & ~test_df["_key"].isin(reference_top20),
        "positive_captured_by_reference_not_hybrid": positive_mask
        & test_df["_key"].isin(reference_top20)
        & ~test_df["_key"].isin(hybrid_top20),
        "negative_promoted_by_hybrid_not_reference": negative_mask
        & test_df["_key"].isin(hybrid_top20)
        & ~test_df["_key"].isin(reference_top20),
    }

    frames: list[pd.DataFrame] = []
    for disagreement_class in DISAGREEMENT_CLASSES:
        subset = test_df.loc[class_masks[disagreement_class], :].copy()
        if subset.empty:
            continue
        subset["fold_type"] = fold_type
        subset["fold_id"] = fold_id
        subset["test_site"] = test_site
        subset["method_name"] = method_name
        subset["disagreement_class"] = disagreement_class
        subset["hybrid_gap_reason_ko"] = hybrid_gap_reason(disagreement_class, method_name)
        frames.append(subset)

    if not frames:
        return pd.DataFrame(columns=CASE_COLS)

    combined = pd.concat(frames, ignore_index=True)
    return combined.reindex(columns=CASE_COLS)


def evaluate_fold(
    universe: pd.DataFrame,
    spec: dict[str, object],
) -> tuple[list[dict[str, object]], list[dict[str, object]], pd.DataFrame]:
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

    visible_rows: list[dict[str, object]] = []
    hidden_baseline_rows: list[dict[str, object]] = []
    if skip_reason:
        for method_name in VISIBLE_METHOD_NAMES:
            visible_rows.append(
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
                    "skip_reason": skip_reason,
                }
            )
        hidden_baseline_rows.append({**visible_rows[0], "method_name": GLOBAL_BASELINE_METHOD_NAME})
        return visible_rows, hidden_baseline_rows, pd.DataFrame(columns=CASE_COLS)

    scored_test = score_test_universe(train_df, test_df, train_labeled)
    ranked_reference = rank_runs(scored_test, REFERENCE_SCORE_COL)

    baseline_metrics = compute_ranked_metrics(rank_runs(scored_test, GLOBAL_LEARNED_SCORE_COL))
    hidden_baseline_rows.append(
        {
            "fold_type": fold_type,
            "fold_id": fold_id,
            "method_name": GLOBAL_BASELINE_METHOD_NAME,
            "test_site": test_site,
            "train_positive_count": train_positive_count,
            "train_negative_count": train_negative_count,
            "test_positive_like_count": test_counts["positive_like"],
            "test_negative_like_count": test_counts["negative_like"],
            "test_monitor_like_count": test_counts["monitor_like"],
            "test_common_cause_like_count": test_counts["common_cause_like"],
            "test_unlabeled_other_count": test_counts["unlabeled_other"],
            **baseline_metrics,
            "skip_reason": "",
        }
    )

    reference_metrics = compute_ranked_metrics(ranked_reference)
    visible_rows.append(
        {
            "fold_type": fold_type,
            "fold_id": fold_id,
            "method_name": REFERENCE_METHOD_NAME,
            "test_site": test_site,
            "train_positive_count": train_positive_count,
            "train_negative_count": train_negative_count,
            "test_positive_like_count": test_counts["positive_like"],
            "test_negative_like_count": test_counts["negative_like"],
            "test_monitor_like_count": test_counts["monitor_like"],
            "test_common_cause_like_count": test_counts["common_cause_like"],
            "test_unlabeled_other_count": test_counts["unlabeled_other"],
            **reference_metrics,
            "skip_reason": "",
        }
    )

    case_frames: list[pd.DataFrame] = []
    for spec_item in HYBRID_SPECS:
        method_name = str(spec_item["method_name"])
        shortlist_size = int(spec_item["shortlist_size"])
        learned_score_col = str(spec_item["learned_score_col"])
        ranked_hybrid = build_hybrid_ranking(scored_test, learned_score_col, shortlist_size)
        visible_rows.append(
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
                **compute_ranked_metrics(ranked_hybrid),
                "skip_reason": "",
            }
        )
        case_df = build_case_rows(fold_type, fold_id, test_site, method_name, ranked_hybrid, ranked_reference, scored_test)
        if not case_df.empty:
            case_frames.append(case_df)

    case_output = pd.concat(case_frames, ignore_index=True) if case_frames else pd.DataFrame(columns=CASE_COLS)
    return visible_rows, hidden_baseline_rows, case_output.reindex(columns=CASE_COLS)


def build_summary(
    visible_fold_rows: pd.DataFrame,
    hidden_baseline_rows: pd.DataFrame,
    prior_site_scaling_summary: pd.DataFrame,
) -> pd.DataFrame:
    if visible_fold_rows.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)

    all_rows = pd.concat([visible_fold_rows, hidden_baseline_rows], ignore_index=True)
    all_fold_counts = (
        all_rows[["fold_type", "fold_id"]].drop_duplicates().groupby("fold_type", dropna=False).size().to_dict()
    )

    aggregates: dict[tuple[str, str], dict[str, object]] = {}
    for (method_name, fold_type), group in all_rows.groupby(["method_name", "fold_type"], dropna=False):
        valid_group = group.loc[group["skip_reason"].eq("")].copy()
        total_folds = int(all_fold_counts.get(fold_type, 0))
        if valid_group.empty:
            aggregates[(str(method_name), str(fold_type))] = {
                "valid_fold_count": 0,
                "mean_top10_positive_minus_negative": None,
                "mean_top20_positive_minus_negative": None,
                "total_folds": total_folds,
            }
        else:
            aggregates[(str(method_name), str(fold_type))] = {
                "valid_fold_count": int(len(valid_group)),
                "mean_top10_positive_minus_negative": float(valid_group["top10_positive_minus_negative"].mean()),
                "mean_top20_positive_minus_negative": float(valid_group["top20_positive_minus_negative"].mean()),
                "total_folds": total_folds,
            }

    prior_site_map = {
        (row["method_name"], row["fold_type"]): float(row["mean_top20_positive_minus_negative"])
        for _, row in prior_site_scaling_summary.iterrows()
        if pd.notna(row["mean_top20_positive_minus_negative"])
    }

    rows: list[dict[str, object]] = []
    for method_name in VISIBLE_METHOD_NAMES:
        for fold_type in ["leave_one_site_out", "time_holdout_70_30"]:
            current = aggregates.get((method_name, fold_type))
            if current is None:
                continue

            reference = aggregates.get((REFERENCE_METHOD_NAME, fold_type), {})
            global_baseline = aggregates.get((GLOBAL_BASELINE_METHOD_NAME, fold_type), {})
            current_top10 = current["mean_top10_positive_minus_negative"]
            current_top20 = current["mean_top20_positive_minus_negative"]
            ref_top10 = reference.get("mean_top10_positive_minus_negative")
            ref_top20 = reference.get("mean_top20_positive_minus_negative")
            global_top10 = global_baseline.get("mean_top10_positive_minus_negative")
            global_top20 = global_baseline.get("mean_top20_positive_minus_negative")

            delta_top10_vs_reference = None if current_top10 is None or ref_top10 is None else current_top10 - ref_top10
            delta_top20_vs_reference = None if current_top20 is None or ref_top20 is None else current_top20 - ref_top20
            delta_top10_vs_global = None if current_top10 is None or global_top10 is None else current_top10 - global_top10
            delta_top20_vs_global = None if current_top20 is None or global_top20 is None else current_top20 - global_top20

            prior_site_only = prior_site_map.get(("logistic_v3_site_conditioned_scaling", fold_type))
            prior_global_only = prior_site_map.get(("logistic_v3_global_scaling", fold_type))

            if current["valid_fold_count"] == 0:
                note_ko = f"유효 fold 없음 ({current['total_folds']}개 중 0개); fixed scenario={FIXED_SCENARIO_NAME}"
            elif method_name == REFERENCE_METHOD_NAME:
                note_ko = "deterministic retrieval baseline; learned rerank 없이 reference 순서를 그대로 사용"
            elif method_name == "hybrid_ref50_global":
                note_ko = (
                    "reference top50 shortlist 안에서 global learned score로만 재정렬"
                    + (f"; prior global-only top20={prior_global_only:.4f}" if prior_global_only is not None else "")
                )
            elif method_name == "hybrid_ref100_global":
                note_ko = (
                    "reference top100 shortlist 안에서 global learned score로만 재정렬"
                    + (f"; prior global-only top20={prior_global_only:.4f}" if prior_global_only is not None else "")
                )
            elif method_name == "hybrid_ref50_site":
                note_ko = (
                    "reference top50 shortlist 안에서 exploratory site-conditioned learned score로 재정렬"
                    + (f"; prior site-only top20={prior_site_only:.4f}" if prior_site_only is not None else "")
                )
            else:
                note_ko = (
                    "reference top100 shortlist 안에서 exploratory site-conditioned learned score로 재정렬"
                    + (f"; prior site-only top20={prior_site_only:.4f}" if prior_site_only is not None else "")
                )

            rows.append(
                {
                    "method_name": method_name,
                    "fold_type": fold_type,
                    "valid_fold_count": current["valid_fold_count"],
                    "mean_top10_positive_minus_negative": current_top10,
                    "mean_top20_positive_minus_negative": current_top20,
                    "delta_mean_top10_vs_reference": delta_top10_vs_reference,
                    "delta_mean_top20_vs_reference": delta_top20_vs_reference,
                    "delta_mean_top10_vs_global_logistic": delta_top10_vs_global,
                    "delta_mean_top20_vs_global_logistic": delta_top20_vs_global,
                    "note_ko": note_ko,
                }
            )

    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    universe = prepare_universe(root)
    promotions = load_promotions(root)
    prior_site_scaling_summary = load_site_scaling_summary(root)
    scenario_universe = apply_promotions(universe, promotions)

    visible_rows: list[dict[str, object]] = []
    hidden_rows: list[dict[str, object]] = []
    case_frames: list[pd.DataFrame] = []
    for spec in fold_specs(scenario_universe):
        fold_visible_rows, fold_hidden_rows, fold_case_df = evaluate_fold(scenario_universe, spec)
        visible_rows.extend(fold_visible_rows)
        hidden_rows.extend(fold_hidden_rows)
        if not fold_case_df.empty:
            case_frames.append(fold_case_df)

    topk_yield = pd.DataFrame(visible_rows, columns=TOPK_COLS)
    hidden_baselines = pd.DataFrame(hidden_rows, columns=TOPK_COLS)
    cases = pd.concat(case_frames, ignore_index=True).reindex(columns=CASE_COLS) if case_frames else pd.DataFrame(columns=CASE_COLS)
    summary = build_summary(topk_yield, hidden_baselines, prior_site_scaling_summary)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    topk_yield.to_csv(share_dir / TOPK_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    cases.to_csv(share_dir / CASES_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
