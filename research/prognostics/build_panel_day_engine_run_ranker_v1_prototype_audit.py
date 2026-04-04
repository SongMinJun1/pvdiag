#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
V0_SCORES_NAME = "panel_day_engine_run_ranker_v0_scores.csv"
V0_TOPK_NAME = "panel_day_engine_run_ranker_v0_topk_yield_summary.csv"
SCORES_OUTPUT_NAME = "panel_day_engine_run_ranker_v1_scores.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_run_ranker_v1_summary.csv"
TOPK_YIELD_OUTPUT_NAME = "panel_day_engine_run_ranker_v1_topk_yield_summary.csv"
TOPRUNS_OUTPUT_NAME = "panel_day_engine_run_ranker_v1_topruns.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
STRING_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "run_shape_class", "cohort_hint"]
TOP_K_VALUES = [10, 20, 50, 100]
EPSILON = 1e-9
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
REQUIRED_FEATURE_TABLE_COLS = list(
    dict.fromkeys([*KEY_COLS, "run_day_count", "run_shape_class", "cohort_hint", *TRAIN_FEATURES])
)
REQUIRED_V0_SCORE_COLS = [*KEY_COLS, "electrical_core_score", "electrical_core_minus_broadshape_050"]
REQUIRED_V0_TOPK_COLS = ["score_name", "top_k", "precision_minus_nuisance"]
POSITIVE_LIKE = {"eligible_local", "future_fault_linked"}
NEGATIVE_LIKE = {"nuisance_alert", "isolated_unexplained"}
MONITOR_LIKE = {"recurring_monitor_like"}
UNLABELED_OTHER = {"unmatched_other"}
EVAL_SCORE_NAMES = [
    "logistic_v1_score",
    "hgb_v1_score",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
]
SCORES_OUTPUT_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "cohort_hint",
    "logistic_v1_score",
    "hgb_v1_score",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
]
TOPK_YIELD_COLS = [
    "score_name",
    "top_k",
    "topk_positive_like_count",
    "topk_negative_like_count",
    "topk_monitor_like_count",
    "topk_unlabeled_other_count",
    "topk_positive_like_rate",
    "topk_negative_like_rate",
    "topk_monitor_like_rate",
    "topk_unlabeled_other_rate",
    "positive_minus_negative",
    "positive_lift_vs_base",
    "negative_lift_vs_base",
]
TOPRUNS_COLS = [
    "score_name",
    "rank",
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "cohort_hint",
    "score_value",
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
    "score_name",
    "train_positive_count",
    "train_negative_count",
    "top10_positive_like_count",
    "top10_negative_like_count",
    "top20_positive_like_count",
    "top20_negative_like_count",
    "top50_positive_like_count",
    "top50_negative_like_count",
    "best_positive_minus_negative_across_k",
    "note",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a learned run-level scorer prototype audit using existing run features."
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
    if text.lower() == "nan":
        return ""
    return text


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


def robust_scale(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.dropna().empty:
        return pd.Series(0.0, index=series.index)
    median = float(numeric.median())
    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    iqr = q3 - q1
    denom = iqr if abs(iqr) > 1e-9 else 1.0
    scaled = (numeric.fillna(median) - median) / denom
    return scaled.clip(-5.0, 5.0)


def evaluation_group(cohort_hint: str) -> str:
    if cohort_hint in POSITIVE_LIKE:
        return "positive_like"
    if cohort_hint in NEGATIVE_LIKE:
        return "negative_like"
    if cohort_hint in MONITOR_LIKE:
        return "monitor_like"
    return "unlabeled_other"


def load_feature_table(root: Path) -> pd.DataFrame:
    path = root / "_share" / FEATURE_TABLE_NAME
    df = read_csv(path)
    ensure_columns(df, REQUIRED_FEATURE_TABLE_COLS, path.name)
    df = drop_repeated_header_rows(df).copy()
    for col in STRING_COLS:
        normalizer = normalize_date if col in {"run_start_date", "run_end_date"} else normalize_text
        df[col] = df[col].map(normalizer)
    for col in REQUIRED_FEATURE_TABLE_COLS:
        if col in STRING_COLS:
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.loc[:, REQUIRED_FEATURE_TABLE_COLS].copy()
    return df.drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_v0_scores(root: Path) -> pd.DataFrame:
    path = root / "_share" / V0_SCORES_NAME
    df = read_csv(path)
    ensure_columns(df, REQUIRED_V0_SCORE_COLS, path.name)
    df = drop_repeated_header_rows(df).copy()
    for col in KEY_COLS:
        normalizer = normalize_date if col in {"run_start_date", "run_end_date"} else normalize_text
        df[col] = df[col].map(normalizer)
    for col in ["electrical_core_score", "electrical_core_minus_broadshape_050"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, REQUIRED_V0_SCORE_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_v0_topk_summary(root: Path) -> pd.DataFrame:
    path = root / "_share" / V0_TOPK_NAME
    df = read_csv(path)
    ensure_columns(df, REQUIRED_V0_TOPK_COLS, path.name)
    df = drop_repeated_header_rows(df).copy()
    df["score_name"] = df["score_name"].map(normalize_text)
    df["top_k"] = pd.to_numeric(df["top_k"], errors="coerce").astype("Int64")
    df["precision_minus_nuisance"] = pd.to_numeric(df["precision_minus_nuisance"], errors="coerce")
    return df.loc[:, REQUIRED_V0_TOPK_COLS].copy()


def build_training_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = df.loc[:, TRAIN_FEATURES].copy()
    for col in TRAIN_FEATURES:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
    medians = raw.median(numeric_only=True)
    raw_imputed = raw.fillna(medians)
    scaled = pd.DataFrame({col: robust_scale(raw_imputed[col]) for col in TRAIN_FEATURES}, index=df.index)
    return raw_imputed, scaled


def fit_prototype_models(df: pd.DataFrame) -> pd.DataFrame:
    raw_imputed, scaled = build_training_matrix(df)
    out = df.copy()
    out["evaluation_group"] = out["cohort_hint"].map(evaluation_group)
    train_mask = out["evaluation_group"].isin({"positive_like", "negative_like"})
    train_df = out.loc[train_mask].copy()
    if train_df.empty:
        raise SystemExit("no training rows found for positive_like/negative_like")
    y_train = train_df["evaluation_group"].eq("positive_like").astype(int)
    if y_train.nunique() < 2:
        raise SystemExit("training labels must contain both positive_like and negative_like")

    counts = y_train.value_counts().to_dict()
    sample_weights = y_train.map({
        1: len(y_train) / (2.0 * counts.get(1, 1)),
        0: len(y_train) / (2.0 * counts.get(0, 1)),
    }).astype(float)

    logistic = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=0,
    )
    logistic.fit(scaled.loc[train_mask, TRAIN_FEATURES], y_train)
    out["logistic_v1_score"] = logistic.predict_proba(scaled.loc[:, TRAIN_FEATURES])[:, 1]

    hgb = HistGradientBoostingClassifier(
        loss="log_loss",
        learning_rate=0.05,
        max_iter=200,
        max_depth=3,
        min_samples_leaf=1,
        random_state=0,
    )
    hgb.fit(raw_imputed.loc[train_mask, TRAIN_FEATURES], y_train, sample_weight=sample_weights)
    out["hgb_v1_score"] = hgb.predict_proba(raw_imputed.loc[:, TRAIN_FEATURES])[:, 1]
    return out


def rank_runs(df: pd.DataFrame, score_name: str) -> pd.DataFrame:
    ranked = df.sort_values(
        [score_name, "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[False, False, True, True, True, True],
        kind="stable",
    ).copy()
    ranked["score_value"] = ranked[score_name]
    ranked["rank"] = range(1, len(ranked) + 1)
    return ranked


def build_topk_yield(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    labeled_mask = df["evaluation_group"].isin({"positive_like", "negative_like"})
    total_labeled_count = int(labeled_mask.sum())
    positive_like_count = int(df["evaluation_group"].eq("positive_like").sum())
    negative_like_count = int(df["evaluation_group"].eq("negative_like").sum())
    base_positive_like_rate = positive_like_count / (total_labeled_count + EPSILON)
    base_negative_like_rate = negative_like_count / (total_labeled_count + EPSILON)

    for score_name in EVAL_SCORE_NAMES:
        ranked = rank_runs(df, score_name)
        for top_k in TOP_K_VALUES:
            top_df = ranked.head(top_k).copy()
            selected_count = len(top_df)
            denom = selected_count if selected_count > 0 else 1
            topk_positive_like_count = int(top_df["evaluation_group"].eq("positive_like").sum())
            topk_negative_like_count = int(top_df["evaluation_group"].eq("negative_like").sum())
            topk_monitor_like_count = int(top_df["evaluation_group"].eq("monitor_like").sum())
            topk_unlabeled_other_count = int(top_df["evaluation_group"].eq("unlabeled_other").sum())
            topk_positive_like_rate = topk_positive_like_count / denom
            topk_negative_like_rate = topk_negative_like_count / denom
            topk_monitor_like_rate = topk_monitor_like_count / denom
            topk_unlabeled_other_rate = topk_unlabeled_other_count / denom
            rows.append(
                {
                    "score_name": score_name,
                    "top_k": top_k,
                    "topk_positive_like_count": topk_positive_like_count,
                    "topk_negative_like_count": topk_negative_like_count,
                    "topk_monitor_like_count": topk_monitor_like_count,
                    "topk_unlabeled_other_count": topk_unlabeled_other_count,
                    "topk_positive_like_rate": topk_positive_like_rate,
                    "topk_negative_like_rate": topk_negative_like_rate,
                    "topk_monitor_like_rate": topk_monitor_like_rate,
                    "topk_unlabeled_other_rate": topk_unlabeled_other_rate,
                    "positive_minus_negative": topk_positive_like_rate - topk_negative_like_rate,
                    "positive_lift_vs_base": topk_positive_like_rate / (base_positive_like_rate + EPSILON),
                    "negative_lift_vs_base": topk_negative_like_rate / (base_negative_like_rate + EPSILON),
                }
            )
    return pd.DataFrame(rows).reindex(columns=TOPK_YIELD_COLS)


def build_topruns(df: pd.DataFrame) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for score_name in EVAL_SCORE_NAMES:
        ranked = rank_runs(df, score_name).head(30).copy()
        ranked.insert(0, "score_name", score_name)
        parts.append(ranked.loc[:, TOPRUNS_COLS].copy())
    if not parts:
        return pd.DataFrame(columns=TOPRUNS_COLS)
    return pd.concat(parts, ignore_index=True)


def build_summary(df: pd.DataFrame, topk_df: pd.DataFrame, v0_topk_df: pd.DataFrame) -> pd.DataFrame:
    train_positive_count = int(df["evaluation_group"].eq("positive_like").sum())
    train_negative_count = int(df["evaluation_group"].eq("negative_like").sum())
    v0_reference_best = float(
        v0_topk_df.loc[
            v0_topk_df["score_name"].isin({"electrical_core_score", "electrical_core_minus_broadshape_050"}),
            "precision_minus_nuisance",
        ].max()
    )
    rows: list[dict[str, object]] = []
    for score_name in EVAL_SCORE_NAMES:
        score_topk = topk_df.loc[topk_df["score_name"].eq(score_name)].copy()
        by_k = score_topk.set_index("top_k")
        best_pmneg = float(score_topk["positive_minus_negative"].max()) if not score_topk.empty else float("nan")
        if score_name in {"logistic_v1_score", "hgb_v1_score"}:
            delta = best_pmneg - v0_reference_best
            comparison = "beats" if delta > 0 else "below_or_ties"
            note = (
                "optimistic_full_fit;"
                f"{comparison}_best_v0_reference_by={delta:.4f};"
                f"reference_best={v0_reference_best:.4f}"
            )
        else:
            note = "v0_reference_from_existing_scores"
        rows.append(
            {
                "score_name": score_name,
                "train_positive_count": train_positive_count,
                "train_negative_count": train_negative_count,
                "top10_positive_like_count": int(by_k.loc[10, "topk_positive_like_count"]),
                "top10_negative_like_count": int(by_k.loc[10, "topk_negative_like_count"]),
                "top20_positive_like_count": int(by_k.loc[20, "topk_positive_like_count"]),
                "top20_negative_like_count": int(by_k.loc[20, "topk_negative_like_count"]),
                "top50_positive_like_count": int(by_k.loc[50, "topk_positive_like_count"]),
                "top50_negative_like_count": int(by_k.loc[50, "topk_negative_like_count"]),
                "best_positive_minus_negative_across_k": best_pmneg,
                "note": note,
            }
        )
    return pd.DataFrame(rows).reindex(columns=SUMMARY_COLS)


def write_csv(path: Path, df: pd.DataFrame, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    feature_table = load_feature_table(root)
    v0_scores = load_v0_scores(root)
    v0_topk = load_v0_topk_summary(root)

    merged = feature_table.merge(v0_scores, on=KEY_COLS, how="left", validate="one_to_one")
    if merged[["electrical_core_score", "electrical_core_minus_broadshape_050"]].isna().any().any():
        raise SystemExit("failed to align v0 reference scores onto run feature table")

    scored = fit_prototype_models(merged)
    topk_yield = build_topk_yield(scored)
    summary = build_summary(scored, topk_yield, v0_topk)
    topruns = build_topruns(scored)

    share_dir = root / "_share"
    write_csv(share_dir / SCORES_OUTPUT_NAME, scored.loc[:, SCORES_OUTPUT_COLS].copy(), SCORES_OUTPUT_COLS)
    write_csv(share_dir / SUMMARY_OUTPUT_NAME, summary, SUMMARY_COLS)
    write_csv(share_dir / TOPK_YIELD_OUTPUT_NAME, topk_yield, TOPK_YIELD_COLS)
    write_csv(share_dir / TOPRUNS_OUTPUT_NAME, topruns, TOPRUNS_COLS)


if __name__ == "__main__":
    main()
