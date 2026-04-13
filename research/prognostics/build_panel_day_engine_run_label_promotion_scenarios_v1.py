#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
LABEL_PACK_V2_NAME = "panel_day_engine_run_label_pack_v2.csv"
REVIEW_BATCH_NAME = "panel_day_engine_run_label_expansion_review_batch_v1.csv"
V2_HOLDOUT_SUMMARY_NAME = "panel_day_engine_run_ranker_v2_holdout_summary.csv"
V0_SCORES_NAME = "panel_day_engine_run_ranker_v0_scores.csv"

SCENARIO_OUTPUT_NAME = "panel_day_engine_run_label_promotion_scenarios_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_run_ranker_v3_scenario_holdout_summary_v1.csv"
TOPK_OUTPUT_NAME = "panel_day_engine_run_ranker_v3_scenario_topk_yield_v1.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
STRING_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "run_shape_class"]
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
SCENARIO_ORDER = {
    "p1_only": 1,
    "p1_plus_watchnow_ref": 2,
    "p1_plus_site_balanced_p2": 3,
    "p1_plus_watchnow_ref_plus_site_balanced": 4,
}
TRACK_NAME = "positive_review_batch"
ACTION_NAME = "inspect_for_positive_promotion"
SCENARIO_LABEL_SOURCE = "weak_positive_promotion"
SCENARIO_MODEL_NAME = "scenario_logistic_v3"
REFERENCE_SCORE_NAMES = ["electrical_core_score", "electrical_core_minus_broadshape_050"]
ALL_SCORE_NAMES = [SCENARIO_MODEL_NAME, *REFERENCE_SCORE_NAMES]
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
REQUIRED_REVIEW_BATCH_COLS = [
    *KEY_COLS,
    "candidate_priority_band",
    "review_track",
    "suggested_label_action",
    "electrical_core_minus_broadshape_050",
    "watch_now_panel_ref_flag",
    "site_positive_gap_flag",
]
REQUIRED_V2_SUMMARY_COLS = ["score_name", "fold_type", "mean_top20_positive_minus_negative"]
REQUIRED_V0_SCORE_COLS = [*KEY_COLS, "electrical_core_score", "electrical_core_minus_broadshape_050"]

SCENARIO_LISTING_COLS = [
    "scenario_name",
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "candidate_priority_band",
    "electrical_core_minus_broadshape_050",
    "watch_now_panel_ref_flag",
    "site_positive_gap_flag",
    "scenario_label_source",
    "promotion_reason_ko",
]
SUMMARY_COLS = [
    "scenario_name",
    "promoted_positive_count",
    "promoted_sites_csv",
    "loso_valid_fold_count",
    "loso_mean_top10_positive_minus_negative",
    "loso_mean_top20_positive_minus_negative",
    "time_valid_fold_count",
    "time_mean_top10_positive_minus_negative",
    "time_mean_top20_positive_minus_negative",
    "delta_loso_top20_vs_v2_logistic",
    "delta_time_top20_vs_v2_logistic",
    "note_ko",
]
TOPK_COLS = [
    "scenario_name",
    "fold_type",
    "fold_id",
    "top_k",
    "topk_positive_like_count",
    "topk_negative_like_count",
    "topk_monitor_like_count",
    "topk_common_cause_like_count",
    "topk_unlabeled_other_count",
    "topk_positive_minus_negative",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test weak-label promotion scenarios for the next run scorer iteration."
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


def load_review_batch(root: Path) -> pd.DataFrame:
    path = root / "_share" / REVIEW_BATCH_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_REVIEW_BATCH_COLS, path.name)
    df = normalize_key_cols(df)
    df["candidate_priority_band"] = df["candidate_priority_band"].map(normalize_text)
    df["review_track"] = df["review_track"].map(normalize_text)
    df["suggested_label_action"] = df["suggested_label_action"].map(normalize_text)
    df["electrical_core_minus_broadshape_050"] = pd.to_numeric(
        df["electrical_core_minus_broadshape_050"], errors="coerce"
    )
    df["watch_now_panel_ref_flag"] = pd.to_numeric(df["watch_now_panel_ref_flag"], errors="coerce").fillna(0).astype(int)
    df["site_positive_gap_flag"] = pd.to_numeric(df["site_positive_gap_flag"], errors="coerce").fillna(0).astype(int)
    df = df.loc[
        df["review_track"].eq(TRACK_NAME) & df["suggested_label_action"].eq(ACTION_NAME),
        :,
    ].copy()
    return sort_candidates(df).drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_v2_summary(root: Path) -> pd.DataFrame:
    path = root / "_share" / V2_HOLDOUT_SUMMARY_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_V2_SUMMARY_COLS, path.name)
    df["score_name"] = df["score_name"].map(normalize_text)
    df["fold_type"] = df["fold_type"].map(normalize_text)
    df["mean_top20_positive_minus_negative"] = pd.to_numeric(df["mean_top20_positive_minus_negative"], errors="coerce")
    return df.loc[:, REQUIRED_V2_SUMMARY_COLS].copy()


def load_v0_scores(root: Path) -> pd.DataFrame:
    path = root / "_share" / V0_SCORES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_V0_SCORE_COLS, path.name)
    df = normalize_key_cols(df)
    for col in ["electrical_core_score", "electrical_core_minus_broadshape_050"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.loc[:, REQUIRED_V0_SCORE_COLS].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def prepare_universe(root: Path) -> pd.DataFrame:
    feature_df = load_feature_table(root)
    label_df = load_label_pack_v2(root)
    v0_df = load_v0_scores(root)

    merged = feature_df.merge(label_df, on=KEY_COLS, how="left", validate="one_to_one")
    merged = merged.merge(v0_df, on=KEY_COLS, how="left", validate="one_to_one")

    if merged["evaluation_group"].isna().any():
        missing_count = int(merged["evaluation_group"].isna().sum())
        raise SystemExit(f"missing label rows for {missing_count} runs")

    missing_score_cols = [
        col
        for col in ["electrical_core_score", "electrical_core_minus_broadshape_050"]
        if merged[col].isna().any()
    ]
    if missing_score_cols:
        raise SystemExit(f"merged universe missing reference scores: {missing_score_cols}")

    merged["training_label_v2"] = merged["training_label_v2"].fillna("").map(normalize_text)
    merged["run_start_dt"] = pd.to_datetime(merged["run_start_date"], errors="coerce")
    return merged


def sort_candidates(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    return df.sort_values(
        ["electrical_core_minus_broadshape_050", "site_positive_gap_flag", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[False, False, True, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)


def key_set(df: pd.DataFrame) -> set[tuple[str, str, str, str]]:
    if df.empty:
        return set()
    return set(map(tuple, df[KEY_COLS].itertuples(index=False, name=None)))


def append_and_dedupe(frames: list[pd.DataFrame]) -> pd.DataFrame:
    non_empty = [frame.copy() for frame in frames if not frame.empty]
    if not non_empty:
        return pd.DataFrame(columns=REQUIRED_REVIEW_BATCH_COLS)
    return pd.concat(non_empty, ignore_index=True).drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def select_p1(review_df: pd.DataFrame) -> pd.DataFrame:
    df = sort_candidates(review_df.loc[review_df["candidate_priority_band"].eq("P1")].copy())
    if not df.empty:
        df["promotion_basis"] = "p1_base"
    return df


def select_watchnow(review_df: pd.DataFrame, exclude_keys: set[tuple[str, str, str, str]] | None = None) -> pd.DataFrame:
    exclude_keys = exclude_keys or set()
    df = sort_candidates(review_df.loc[review_df["watch_now_panel_ref_flag"].eq(1)].copy())
    if exclude_keys:
        df = df.loc[~df[KEY_COLS].apply(tuple, axis=1).isin(exclude_keys)].copy()
    if not df.empty:
        df["promotion_basis"] = "watch_now_ref"
    return df


def select_top_p2_per_site(
    review_df: pd.DataFrame,
    top_n: int,
    basis_name: str,
    exclude_keys: set[tuple[str, str, str, str]] | None = None,
) -> pd.DataFrame:
    exclude_keys = exclude_keys or set()
    p2_df = sort_candidates(review_df.loc[review_df["candidate_priority_band"].eq("P2")].copy())
    if exclude_keys:
        p2_df = p2_df.loc[~p2_df[KEY_COLS].apply(tuple, axis=1).isin(exclude_keys)].copy()
    selected: list[pd.DataFrame] = []
    for site, site_df in p2_df.groupby("site", sort=True):
        top_df = site_df.head(top_n).copy()
        if not top_df.empty:
            top_df["promotion_basis"] = basis_name
            selected.append(top_df)
    if not selected:
        return p2_df.iloc[0:0].copy()
    return pd.concat(selected, ignore_index=True)


def build_scenario_listing(review_df: pd.DataFrame) -> pd.DataFrame:
    p1_df = select_p1(review_df)
    watch_df = select_watchnow(review_df)
    site_top2_df = select_top_p2_per_site(review_df, top_n=2, basis_name="site_balanced_top2")

    existing_for_d = key_set(append_and_dedupe([p1_df, watch_df]))
    site_top1_remaining_df = select_top_p2_per_site(
        review_df,
        top_n=1,
        basis_name="site_balanced_top1_remaining",
        exclude_keys=existing_for_d,
    )

    scenario_map = {
        "p1_only": append_and_dedupe([p1_df]),
        "p1_plus_watchnow_ref": append_and_dedupe([p1_df, watch_df]),
        "p1_plus_site_balanced_p2": append_and_dedupe([p1_df, site_top2_df]),
        "p1_plus_watchnow_ref_plus_site_balanced": append_and_dedupe([p1_df, watch_df, site_top1_remaining_df]),
    }

    rows: list[pd.DataFrame] = []
    for scenario_name, scenario_df in scenario_map.items():
        if scenario_df.empty:
            continue
        scenario_df = scenario_df.copy()
        scenario_df["scenario_name"] = scenario_name
        scenario_df["scenario_label_source"] = SCENARIO_LABEL_SOURCE
        scenario_df["promotion_reason_ko"] = scenario_df["promotion_basis"].map(
            {
                "p1_base": "review batch의 P1 candidate라 우선 weak positive promotion 대상으로 포함",
                "watch_now_ref": "watch_now panel reference가 있어 weak positive promotion 보강 대상으로 포함",
                "site_balanced_top2": "site별 상위 P2 2건으로 균형 있게 weak positive promotion",
                "site_balanced_top1_remaining": "watch_now 포함 뒤 남은 P2 중 site별 1건을 추가 보강",
            }
        ).fillna("weak positive promotion scenario에 포함")
        rows.append(
            scenario_df.loc[
                :,
                [
                    "scenario_name",
                    *KEY_COLS,
                    "candidate_priority_band",
                    "electrical_core_minus_broadshape_050",
                    "watch_now_panel_ref_flag",
                    "site_positive_gap_flag",
                    "scenario_label_source",
                    "promotion_reason_ko",
                ],
            ]
        )

    if not rows:
        return pd.DataFrame(columns=SCENARIO_LISTING_COLS)

    listing = pd.concat(rows, ignore_index=True)
    listing["_scenario_order"] = listing["scenario_name"].map(SCENARIO_ORDER).fillna(99)
    listing = listing.sort_values(
        [
            "_scenario_order",
            "electrical_core_minus_broadshape_050",
            "site_positive_gap_flag",
            "site",
            "panel_id",
            "run_start_date",
            "run_end_date",
        ],
        ascending=[True, False, False, True, True, True, True],
        kind="mergesort",
    ).drop(columns="_scenario_order")
    return listing.reindex(columns=SCENARIO_LISTING_COLS).reset_index(drop=True)


def build_scenario_universe(
    universe: pd.DataFrame,
    scenario_listing: pd.DataFrame,
    scenario_name: str,
) -> pd.DataFrame:
    scenario_universe = universe.copy()
    scenario_universe["scenario_name"] = scenario_name
    scenario_universe["scenario_training_label"] = scenario_universe["training_label_v2"]
    scenario_universe["scenario_label_source"] = scenario_universe["training_label_v2"].map(
        {
            "positive": "original_positive",
            "negative": "original_negative",
            "exclude": "original_exclude",
        }
    ).fillna("original_exclude")

    promoted = scenario_listing.loc[scenario_listing["scenario_name"].eq(scenario_name), KEY_COLS].drop_duplicates().copy()
    if promoted.empty:
        return scenario_universe

    promoted_keys = set(map(tuple, promoted[KEY_COLS].itertuples(index=False, name=None)))
    mask = scenario_universe[KEY_COLS].apply(tuple, axis=1).isin(promoted_keys)
    scenario_universe.loc[mask, "scenario_training_label"] = "positive"
    scenario_universe.loc[mask, "scenario_label_source"] = SCENARIO_LABEL_SOURCE

    if int(mask.sum()) != len(promoted):
        raise SystemExit(f"scenario promotions missing from run universe: {scenario_name}")

    return scenario_universe


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
        counts = compute_group_counts(top)
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
                "topk_positive_minus_negative": positive_minus_negative,
            }
        )

    return (
        {
            "labeled_test_auc": auc,
            "labeled_test_average_precision": ap,
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


def evaluate_fold(
    scenario_name: str,
    scenario_universe: pd.DataFrame,
    spec: dict[str, object],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    fold_type = str(spec["fold_type"])
    fold_id = str(spec["fold_id"])
    train_index = list(spec["train_index"])
    test_index = list(spec["test_index"])

    train_df = scenario_universe.loc[train_index].copy()
    test_df = scenario_universe.loc[test_index].copy()
    train_labeled = train_df.loc[train_df["scenario_training_label"].isin(TRAIN_LABELS)].copy()
    train_positive_count = int(train_labeled["scenario_training_label"].eq("positive").sum())
    train_negative_count = int(train_labeled["scenario_training_label"].eq("negative").sum())

    skip_reason = ""
    if test_df.empty:
        skip_reason = "empty_test_universe"
    elif train_labeled.empty or train_positive_count == 0 or train_negative_count == 0:
        skip_reason = "train_labeled_missing_class"

    if skip_reason:
        return (
            [
                {
                    "scenario_name": scenario_name,
                    "fold_type": fold_type,
                    "fold_id": fold_id,
                    "score_name": score_name,
                    "labeled_test_auc": None,
                    "labeled_test_average_precision": None,
                    "top10_positive_minus_negative": None,
                    "top20_positive_minus_negative": None,
                    "skip_reason": skip_reason,
                }
                for score_name in ALL_SCORE_NAMES
            ],
            [],
        )

    raw_train = build_raw_feature_matrix(train_labeled)
    medians, iqr = fit_robust_scaler(raw_train)
    scaled_train = apply_robust_scaler(raw_train, medians, iqr)
    y_train = train_labeled["scenario_training_label"].eq("positive").astype(int)
    logistic = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=0)
    logistic.fit(scaled_train, y_train)

    raw_test = build_raw_feature_matrix(test_df)
    scaled_test = apply_robust_scaler(raw_test, medians, iqr)
    scored_test = test_df.copy()
    scored_test[SCENARIO_MODEL_NAME] = logistic.predict_proba(scaled_test)[:, 1]

    fold_rows: list[dict[str, object]] = []
    topk_rows: list[dict[str, object]] = []
    for score_name in ALL_SCORE_NAMES:
        metric_row, metric_topk_rows = compute_holdout_metrics(scored_test, score_name)
        fold_rows.append(
            {
                "scenario_name": scenario_name,
                "fold_type": fold_type,
                "fold_id": fold_id,
                "score_name": score_name,
                **metric_row,
                "skip_reason": "",
            }
        )
        for topk_row in metric_topk_rows:
            topk_rows.append({"scenario_name": scenario_name, "fold_type": fold_type, "fold_id": fold_id, **topk_row})
    return fold_rows, topk_rows


def build_summary(
    scenario_listing: pd.DataFrame,
    fold_scores: pd.DataFrame,
    v2_summary: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    baseline_loso = v2_summary.loc[
        v2_summary["score_name"].eq("logistic_v2_holdout") & v2_summary["fold_type"].eq("leave_one_site_out"),
        "mean_top20_positive_minus_negative",
    ]
    baseline_time = v2_summary.loc[
        v2_summary["score_name"].eq("logistic_v2_holdout") & v2_summary["fold_type"].eq("time_holdout_70_30"),
        "mean_top20_positive_minus_negative",
    ]
    ref_best_loso = v2_summary.loc[
        v2_summary["score_name"].isin(REFERENCE_SCORE_NAMES) & v2_summary["fold_type"].eq("leave_one_site_out"),
        "mean_top20_positive_minus_negative",
    ]
    ref_best_time = v2_summary.loc[
        v2_summary["score_name"].isin(REFERENCE_SCORE_NAMES) & v2_summary["fold_type"].eq("time_holdout_70_30"),
        "mean_top20_positive_minus_negative",
    ]

    for scenario_name in sorted(scenario_listing["scenario_name"].unique(), key=lambda name: SCENARIO_ORDER.get(name, 99)):
        promoted = scenario_listing.loc[scenario_listing["scenario_name"].eq(scenario_name)].copy()
        scenario_scores = fold_scores.loc[
            fold_scores["scenario_name"].eq(scenario_name) & fold_scores["score_name"].eq(SCENARIO_MODEL_NAME)
        ].copy()
        loso_valid = scenario_scores.loc[
            scenario_scores["fold_type"].eq("leave_one_site_out") & scenario_scores["skip_reason"].eq("")
        ].copy()
        time_valid = scenario_scores.loc[
            scenario_scores["fold_type"].eq("time_holdout_70_30") & scenario_scores["skip_reason"].eq("")
        ].copy()

        loso_top20 = float(loso_valid["top20_positive_minus_negative"].mean()) if not loso_valid.empty else None
        time_top20 = float(time_valid["top20_positive_minus_negative"].mean()) if not time_valid.empty else None
        delta_loso = None if baseline_loso.empty or loso_top20 is None else loso_top20 - float(baseline_loso.iloc[0])
        delta_time = None if baseline_time.empty or time_top20 is None else time_top20 - float(baseline_time.iloc[0])

        note_parts = [f"promoted={len(promoted)}"]
        if delta_loso is not None:
            note_parts.append(f"loso_delta_vs_v2={delta_loso:.4f}")
        if delta_time is not None:
            note_parts.append(f"time_delta_vs_v2={delta_time:.4f}")
        if not ref_best_loso.empty and loso_top20 is not None:
            note_parts.append(f"loso_best_ref={float(ref_best_loso.max()):.4f}")
        if not ref_best_time.empty and time_top20 is not None:
            note_parts.append(f"time_best_ref={float(ref_best_time.max()):.4f}")

        rows.append(
            {
                "scenario_name": scenario_name,
                "promoted_positive_count": int(len(promoted)),
                "promoted_sites_csv": ",".join(sorted(promoted["site"].dropna().map(normalize_text).unique())),
                "loso_valid_fold_count": int(len(loso_valid)),
                "loso_mean_top10_positive_minus_negative": loso_valid["top10_positive_minus_negative"].mean()
                if not loso_valid.empty
                else None,
                "loso_mean_top20_positive_minus_negative": loso_top20,
                "time_valid_fold_count": int(len(time_valid)),
                "time_mean_top10_positive_minus_negative": time_valid["top10_positive_minus_negative"].mean()
                if not time_valid.empty
                else None,
                "time_mean_top20_positive_minus_negative": time_top20,
                "delta_loso_top20_vs_v2_logistic": delta_loso,
                "delta_time_top20_vs_v2_logistic": delta_time,
                "note_ko": "; ".join(note_parts),
            }
        )
    return pd.DataFrame(rows).reindex(columns=SUMMARY_COLS)


def build_topk_output(topk_rows: pd.DataFrame) -> pd.DataFrame:
    if topk_rows.empty:
        return pd.DataFrame(columns=TOPK_COLS)
    output = topk_rows.loc[topk_rows["score_name"].eq(SCENARIO_MODEL_NAME)].copy()
    output = output.sort_values(
        ["scenario_name", "fold_type", "fold_id", "top_k"],
        ascending=[True, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    return output.reindex(columns=TOPK_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    universe = prepare_universe(root)
    review_df = load_review_batch(root)
    v2_summary = load_v2_summary(root)

    scenario_listing = build_scenario_listing(review_df)
    fold_rows: list[dict[str, object]] = []
    topk_rows: list[dict[str, object]] = []
    for scenario_name in sorted(scenario_listing["scenario_name"].unique(), key=lambda name: SCENARIO_ORDER.get(name, 99)):
        scenario_df = build_scenario_universe(universe, scenario_listing, scenario_name)
        for spec in fold_specs(scenario_df):
            rows, topk = evaluate_fold(scenario_name, scenario_df, spec)
            fold_rows.extend(rows)
            topk_rows.extend(topk)

    fold_scores = pd.DataFrame(fold_rows)
    topk_yield = build_topk_output(pd.DataFrame(topk_rows))
    summary = build_summary(scenario_listing, fold_scores, v2_summary)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    scenario_listing.to_csv(share_dir / SCENARIO_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    topk_yield.to_csv(share_dir / TOPK_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
