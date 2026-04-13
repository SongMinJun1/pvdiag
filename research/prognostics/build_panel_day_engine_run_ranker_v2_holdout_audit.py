#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
LABEL_PACK_V2_NAME = "panel_day_engine_run_label_pack_v2.csv"
V1_HOLDOUT_SUMMARY_NAME = "panel_day_engine_run_ranker_v1_holdout_summary.csv"
V0_SCORES_NAME = "panel_day_engine_run_ranker_v0_scores.csv"

FOLD_SCORES_OUTPUT_NAME = "panel_day_engine_run_ranker_v2_holdout_fold_scores.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_run_ranker_v2_holdout_summary.csv"
TOPK_OUTPUT_NAME = "panel_day_engine_run_ranker_v2_holdout_topk_yield.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
STRING_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "run_shape_class"]
TOP_K_VALUES = [10, 20]
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
REQUIRED_FEATURE_TABLE_COLS = list(dict.fromkeys([*KEY_COLS, "run_day_count", "run_shape_class", *TRAIN_FEATURES]))
REQUIRED_LABEL_PACK_COLS = [*KEY_COLS, "label_bucket_v2", "training_label_v2"]
REQUIRED_V0_SCORE_COLS = [*KEY_COLS, "electrical_core_score", "electrical_core_minus_broadshape_050"]
REQUIRED_V1_SUMMARY_COLS = [
    "score_name",
    "fold_type",
    "mean_top10_positive_minus_negative",
    "mean_top20_positive_minus_negative",
]
EVALUATION_GROUPS = {
    "positive_like",
    "negative_like",
    "monitor_like",
    "common_cause_like",
    "unlabeled_other",
}
LABELED_GROUPS = {"positive_like", "negative_like"}
TRAIN_LABELS = {"positive", "negative"}
SCORE_NAMES = [
    "logistic_v2_holdout",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
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
SUMMARY_COLS = [
    "score_name",
    "fold_type",
    "valid_fold_count",
    "mean_labeled_test_auc",
    "mean_labeled_test_average_precision",
    "mean_top10_positive_minus_negative",
    "mean_top20_positive_minus_negative",
    "mean_top10_positive_like_count",
    "mean_top10_negative_like_count",
    "mean_top20_positive_like_count",
    "mean_top20_negative_like_count",
    "delta_mean_top10_positive_minus_negative_vs_v1",
    "delta_mean_top20_positive_minus_negative_vs_v1",
    "note",
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
    "topk_positive_like_rate",
    "topk_negative_like_rate",
    "topk_positive_minus_negative",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate whether run_label_pack_v2 improves the run-level scorer under holdout."
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


def load_v0_scores(root: Path) -> pd.DataFrame:
    path = root / "_share" / V0_SCORES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_V0_SCORE_COLS, path.name)
    df = normalize_key_cols(df)
    for col in ["electrical_core_score", "electrical_core_minus_broadshape_050"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, REQUIRED_V0_SCORE_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_v1_summary(root: Path) -> pd.DataFrame:
    path = root / "_share" / V1_HOLDOUT_SUMMARY_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_V1_SUMMARY_COLS, path.name)
    df["score_name"] = df["score_name"].map(normalize_text)
    df["fold_type"] = df["fold_type"].map(normalize_text)
    for col in ["mean_top10_positive_minus_negative", "mean_top20_positive_minus_negative"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, REQUIRED_V1_SUMMARY_COLS].copy()


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


def compute_topk_counts(top_df: pd.DataFrame) -> dict[str, int]:
    counts = compute_group_counts(top_df)
    return {
        "positive_like": counts["positive_like"],
        "negative_like": counts["negative_like"],
        "monitor_like": counts["monitor_like"],
        "common_cause_like": counts["common_cause_like"],
        "unlabeled_other": counts["unlabeled_other"],
    }


def compute_holdout_metrics(test_df: pd.DataFrame, score_name: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    ranked = rank_runs(test_df, score_name)
    labeled = ranked.loc[ranked["evaluation_group"].isin(LABELED_GROUPS)].copy()

    auc = None
    ap = None
    if not labeled.empty and labeled["evaluation_group"].nunique() == 2:
        y_true = labeled["evaluation_group"].eq("positive_like").astype(int)
        auc = float(roc_auc_score(y_true, labeled["_score_value"]))
        ap = float(average_precision_score(y_true, labeled["_score_value"]))

    topk_rows: list[dict[str, object]] = []
    top_stats: dict[int, dict[str, object]] = {}
    for top_k in TOP_K_VALUES:
        top = ranked.head(top_k).copy()
        counts = compute_topk_counts(top)
        denom = float(len(top)) if len(top) else 1.0
        positive_rate = counts["positive_like"] / denom if len(top) else 0.0
        negative_rate = counts["negative_like"] / denom if len(top) else 0.0
        positive_minus_negative = positive_rate - negative_rate
        top_stats[top_k] = {
            "positive_like": counts["positive_like"],
            "negative_like": counts["negative_like"],
            "monitor_like": counts["monitor_like"],
            "common_cause_like": counts["common_cause_like"],
            "unlabeled_other": counts["unlabeled_other"],
            "positive_minus_negative": positive_minus_negative,
        }
        topk_rows.append(
            {
                "score_name": score_name,
                "top_k": top_k,
                "topk_positive_like_count": counts["positive_like"],
                "topk_negative_like_count": counts["negative_like"],
                "topk_monitor_like_count": counts["monitor_like"],
                "topk_common_cause_like_count": counts["common_cause_like"],
                "topk_unlabeled_other_count": counts["unlabeled_other"],
                "topk_positive_like_rate": positive_rate,
                "topk_negative_like_rate": negative_rate,
                "topk_positive_minus_negative": positive_minus_negative,
            }
        )

    return (
        {
            "labeled_test_auc": auc,
            "labeled_test_average_precision": ap,
            "top10_positive_like_count": top_stats[10]["positive_like"],
            "top10_negative_like_count": top_stats[10]["negative_like"],
            "top10_monitor_like_count": top_stats[10]["monitor_like"],
            "top10_common_cause_like_count": top_stats[10]["common_cause_like"],
            "top10_unlabeled_other_count": top_stats[10]["unlabeled_other"],
            "top20_positive_like_count": top_stats[20]["positive_like"],
            "top20_negative_like_count": top_stats[20]["negative_like"],
            "top20_monitor_like_count": top_stats[20]["monitor_like"],
            "top20_common_cause_like_count": top_stats[20]["common_cause_like"],
            "top20_unlabeled_other_count": top_stats[20]["unlabeled_other"],
            "top10_positive_minus_negative": top_stats[10]["positive_minus_negative"],
            "top20_positive_minus_negative": top_stats[20]["positive_minus_negative"],
        },
        topk_rows,
    )


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


def evaluate_fold(universe: pd.DataFrame, spec: dict[str, object]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    fold_type = str(spec["fold_type"])
    fold_id = str(spec["fold_id"])
    test_site = str(spec["test_site"])
    train_index = list(spec["train_index"])
    test_index = list(spec["test_index"])

    train_df = universe.loc[train_index].copy()
    test_df = universe.loc[test_index].copy()
    train_labeled = train_df.loc[train_df["training_label_v2"].isin(TRAIN_LABELS)].copy()
    train_positive_count = int(train_labeled["training_label_v2"].eq("positive").sum())
    train_negative_count = int(train_labeled["training_label_v2"].eq("negative").sum())
    empty_counts = {name: 0 for name in EVALUATION_GROUPS}
    test_counts = compute_group_counts(test_df) if not test_df.empty else empty_counts

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

    raw_train = build_raw_feature_matrix(train_labeled)
    medians, iqr = fit_robust_scaler(raw_train)
    scaled_train = apply_robust_scaler(raw_train, medians, iqr)
    y_train = train_labeled["training_label_v2"].eq("positive").astype(int)
    logistic = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=0)
    logistic.fit(scaled_train, y_train)

    raw_test = build_raw_feature_matrix(test_df)
    scaled_test = apply_robust_scaler(raw_test, medians, iqr)
    scored_test = test_df.copy()
    scored_test["logistic_v2_holdout"] = logistic.predict_proba(scaled_test)[:, 1]

    fold_rows: list[dict[str, object]] = []
    topk_rows: list[dict[str, object]] = []
    for score_name in SCORE_NAMES:
        metric_row, metric_topk_rows = compute_holdout_metrics(scored_test, score_name)
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
        for topk_row in metric_topk_rows:
            topk_rows.append({"fold_type": fold_type, "fold_id": fold_id, **topk_row})

    return fold_rows, topk_rows


def baseline_score_name(score_name: str) -> str:
    return "logistic_v1_holdout" if score_name == "logistic_v2_holdout" else score_name


def build_summary(fold_scores: pd.DataFrame, v1_summary: pd.DataFrame) -> pd.DataFrame:
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
                    "mean_top10_positive_like_count": None,
                    "mean_top10_negative_like_count": None,
                    "mean_top20_positive_like_count": None,
                    "mean_top20_negative_like_count": None,
                    "delta_mean_top10_positive_minus_negative_vs_v1": None,
                    "delta_mean_top20_positive_minus_negative_vs_v1": None,
                    "note": f"no_valid_folds;total_folds={total_folds}",
                }
            )
            continue

        current_top10 = float(valid_group["top10_positive_minus_negative"].mean())
        current_top20 = float(valid_group["top20_positive_minus_negative"].mean())
        base_name = baseline_score_name(str(score_name))
        baseline_row = v1_summary.loc[
            v1_summary["score_name"].eq(base_name) & v1_summary["fold_type"].eq(str(fold_type))
        ]

        delta_top10 = None
        delta_top20 = None
        if not baseline_row.empty:
            delta_top10 = current_top10 - float(baseline_row.iloc[0]["mean_top10_positive_minus_negative"])
            delta_top20 = current_top20 - float(baseline_row.iloc[0]["mean_top20_positive_minus_negative"])

        note = f"valid_folds={len(valid_group)}/{total_folds};baseline={base_name}"
        if delta_top20 is not None:
            note = f"{note};delta_top20_vs_v1={delta_top20:.4f}"
        else:
            note = f"{note};baseline_missing"

        rows.append(
            {
                "score_name": score_name,
                "fold_type": fold_type,
                "valid_fold_count": int(len(valid_group)),
                "mean_labeled_test_auc": valid_group["labeled_test_auc"].mean(),
                "mean_labeled_test_average_precision": valid_group["labeled_test_average_precision"].mean(),
                "mean_top10_positive_minus_negative": current_top10,
                "mean_top20_positive_minus_negative": current_top20,
                "mean_top10_positive_like_count": valid_group["top10_positive_like_count"].mean(),
                "mean_top10_negative_like_count": valid_group["top10_negative_like_count"].mean(),
                "mean_top20_positive_like_count": valid_group["top20_positive_like_count"].mean(),
                "mean_top20_negative_like_count": valid_group["top20_negative_like_count"].mean(),
                "delta_mean_top10_positive_minus_negative_vs_v1": delta_top10,
                "delta_mean_top20_positive_minus_negative_vs_v1": delta_top20,
                "note": note,
            }
        )

    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    universe = prepare_universe(root)
    v1_summary = load_v1_summary(root)

    fold_rows: list[dict[str, object]] = []
    topk_rows: list[dict[str, object]] = []
    for spec in fold_specs(universe):
        rows, topk = evaluate_fold(universe, spec)
        fold_rows.extend(rows)
        topk_rows.extend(topk)

    fold_scores = pd.DataFrame(fold_rows, columns=FOLD_SCORE_COLS)
    topk_yield = pd.DataFrame(topk_rows, columns=TOPK_COLS)
    summary = build_summary(fold_scores, v1_summary)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    fold_scores.to_csv(share_dir / FOLD_SCORES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    topk_yield.to_csv(share_dir / TOPK_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
