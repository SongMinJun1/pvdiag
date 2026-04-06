#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression

import build_panel_day_engine_run_ranker_v2_holdout_audit as holdout_base

FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
LABEL_PACK_V3_NAME = "panel_day_engine_run_label_pack_v3_intersection.csv"
COMPLEMENT_RECOMMENDATION_NAME = "panel_day_engine_run_ranker_complement_recommendation_v1.csv"
OPERATOR_ATTENTION_NOW_NAME = "panel_day_engine_operator_attention_now_v1.csv"
V0_SCORES_NAME = "panel_day_engine_run_ranker_v0_scores.csv"

DISCOVERY_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_summary_v1.csv"

EXPECTED_RECOMMENDATION = "use_logistic_as_secondary_discovery_lane"
KEY_COLS = holdout_base.KEY_COLS
TRAIN_LABELS = holdout_base.TRAIN_LABELS
EVALUATION_GROUPS = holdout_base.EVALUATION_GROUPS
REFERENCE_SCORE_COL = "electrical_core_minus_broadshape_050"
DISCOVERY_SCORE_COL = "logistic_v3_discovery_score"
SITE_TOP_K = 5
GLOBAL_TOP_K = 20
SHAPE_BUCKETS = {
    "selected_chronic_count": "chronic_alert_run",
    "selected_medium_count": "medium_alert_run",
    "selected_short_count": "short_alert_run",
}

REQUIRED_LABEL_PACK_V3_COLS = [*KEY_COLS, "label_bucket_v3", "training_label_v3"]
REQUIRED_RECOMMENDATION_COLS = ["recommended_next_direction", "rationale_ko"]
REQUIRED_ATTENTION_COLS = ["site", "panel_id"]
REQUIRED_V0_COLS = [*KEY_COLS, REFERENCE_SCORE_COL]

DISCOVERY_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    DISCOVERY_SCORE_COL,
    REFERENCE_SCORE_COL,
    "global_discovery_rank",
    "site_discovery_rank",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "discovery_reason_ko",
]

SUMMARY_COLS = [
    "record_type",
    "site",
    "candidate_universe_count",
    "selected_discovery_count",
    "selected_chronic_count",
    "selected_medium_count",
    "selected_short_count",
    "median_discovery_score",
    "max_discovery_score",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an operator-facing secondary discovery lane from the learned v3 scorer."
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


def load_guardrail(root: Path) -> pd.DataFrame:
    path = root / "_share" / COMPLEMENT_RECOMMENDATION_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_RECOMMENDATION_COLS, path.name)
    if len(df) != 1:
        raise SystemExit(f"{path.name} must contain exactly one row")
    df["recommended_next_direction"] = df["recommended_next_direction"].map(holdout_base.normalize_text)
    strategy = df.iloc[0]["recommended_next_direction"]
    if strategy != EXPECTED_RECOMMENDATION:
        raise SystemExit(
            f"recommended_next_direction must be {EXPECTED_RECOMMENDATION}, got {strategy}. "
            "Secondary discovery lane is disabled by the complement audit guardrail."
        )
    return df.copy()


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


def load_attention_panels(root: Path) -> set[tuple[str, str]]:
    path = root / "_share" / OPERATOR_ATTENTION_NOW_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_ATTENTION_COLS, path.name)
    df["site"] = df["site"].map(holdout_base.normalize_text)
    df["panel_id"] = df["panel_id"].map(holdout_base.normalize_text)
    return set(map(tuple, df.loc[:, ["site", "panel_id"]].drop_duplicates().itertuples(index=False, name=None)))


def load_v0_scores(root: Path) -> pd.DataFrame:
    path = root / "_share" / V0_SCORES_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_V0_COLS, path.name)
    df = holdout_base.normalize_key_cols(df)
    df[REFERENCE_SCORE_COL] = pd.to_numeric(df[REFERENCE_SCORE_COL], errors="coerce")
    return (
        df.loc[:, REQUIRED_V0_COLS]
        .drop_duplicates(subset=KEY_COLS, keep="first")
        .reset_index(drop=True)
    )


def prepare_scored_universe(root: Path) -> pd.DataFrame:
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
    train_labeled = merged.loc[merged["training_label_v3"].isin(TRAIN_LABELS)].copy()
    if train_labeled.empty:
        raise SystemExit("no v3 labeled rows available for discovery-lane training")
    if not train_labeled["training_label_v3"].eq("positive").any() or not train_labeled["training_label_v3"].eq("negative").any():
        raise SystemExit("v3 training labels must contain both positive and negative classes")

    raw_train = holdout_base.build_raw_feature_matrix(train_labeled)
    medians, iqr = holdout_base.fit_robust_scaler(raw_train)
    scaled_train = holdout_base.apply_robust_scaler(raw_train, medians, iqr)
    y_train = train_labeled["training_label_v3"].eq("positive").astype(int)

    logistic = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=0)
    logistic.fit(scaled_train, y_train)

    raw_all = holdout_base.build_raw_feature_matrix(merged)
    scaled_all = holdout_base.apply_robust_scaler(raw_all, medians, iqr)
    merged = merged.copy()
    merged[DISCOVERY_SCORE_COL] = logistic.predict_proba(scaled_all)[:, 1]
    return merged


def rank_candidate_universe(candidate_df: pd.DataFrame) -> pd.DataFrame:
    ranked = candidate_df.copy()
    ranked[DISCOVERY_SCORE_COL] = pd.to_numeric(ranked[DISCOVERY_SCORE_COL], errors="coerce")
    ranked["run_day_count"] = pd.to_numeric(ranked["run_day_count"], errors="coerce")
    ranked = ranked.sort_values(
        [DISCOVERY_SCORE_COL, "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[False, False, True, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    ranked["global_discovery_rank"] = ranked.index + 1
    ranked["site_discovery_rank"] = (
        ranked.groupby("site", dropna=False).cumcount() + 1
    )
    return ranked


def build_candidate_universe(scored_universe: pd.DataFrame, attention_panels: set[tuple[str, str]]) -> pd.DataFrame:
    candidate_df = scored_universe.loc[
        scored_universe["training_label_v3"].eq("exclude")
        & scored_universe["label_bucket_v3"].eq("unlabeled_other")
    ].copy()
    candidate_df["attention_panel_flag"] = candidate_df.apply(
        lambda row: (holdout_base.normalize_text(row["site"]), holdout_base.normalize_text(row["panel_id"])) in attention_panels,
        axis=1,
    )
    candidate_df = candidate_df.loc[~candidate_df["attention_panel_flag"]].copy()
    candidate_df = rank_candidate_universe(candidate_df)
    return candidate_df


def discovery_reason(row: pd.Series) -> str:
    reasons: list[str] = ["현재 operator attention_now에 없는 hidden panel candidate"]
    global_rank = int(row["global_discovery_rank"])
    site_rank = int(row["site_discovery_rank"])
    if global_rank <= GLOBAL_TOP_K:
        reasons.append("global top20 learned discovery score")
    if site_rank <= SITE_TOP_K:
        reasons.append("site top5 learned discovery score")
    shape_class = holdout_base.normalize_text(row["run_shape_class"])
    if shape_class:
        reasons.append(f"{shape_class} shape")
    return ", ".join(reasons)


def select_discovery_lane(candidate_df: pd.DataFrame) -> pd.DataFrame:
    if candidate_df.empty:
        return candidate_df.loc[:, DISCOVERY_COLS].copy()

    per_site = (
        candidate_df.groupby("site", dropna=False, group_keys=False)
        .head(SITE_TOP_K)
        .copy()
    )
    overall = candidate_df.head(GLOBAL_TOP_K).copy()
    selected = (
        pd.concat([per_site, overall], ignore_index=True)
        .drop_duplicates(subset=KEY_COLS, keep="first")
        .sort_values(
            [DISCOVERY_SCORE_COL, "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
            ascending=[False, False, True, True, True, True],
            kind="mergesort",
        )
        .reset_index(drop=True)
    )
    selected["discovery_reason_ko"] = selected.apply(discovery_reason, axis=1)
    return selected.loc[:, DISCOVERY_COLS].copy()


def build_summary(candidate_df: pd.DataFrame, selected_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def summarize(site: str, record_type: str) -> None:
        if record_type == "overall":
            cand = candidate_df.copy()
            sel = selected_df.copy()
        else:
            cand = candidate_df.loc[candidate_df["site"].eq(site)].copy()
            sel = selected_df.loc[selected_df["site"].eq(site)].copy()

        row = {
            "record_type": record_type,
            "site": site,
            "candidate_universe_count": int(len(cand)),
            "selected_discovery_count": int(len(sel)),
            "selected_chronic_count": 0,
            "selected_medium_count": 0,
            "selected_short_count": 0,
            "median_discovery_score": sel[DISCOVERY_SCORE_COL].median() if not sel.empty else None,
            "max_discovery_score": sel[DISCOVERY_SCORE_COL].max() if not sel.empty else None,
            "note_ko": "hidden unlabeled_other non-attention run만 learned secondary discovery lane으로 별도 노출",
        }
        for col_name, shape_name in SHAPE_BUCKETS.items():
            row[col_name] = int(sel["run_shape_class"].eq(shape_name).sum()) if not sel.empty else 0
        rows.append(row)

    summarize("", "overall")
    for site in sorted(candidate_df["site"].dropna().map(holdout_base.normalize_text).unique()):
        summarize(site, "site")

    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def save_outputs(root: Path, discovery_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    discovery_df.to_csv(share_dir / DISCOVERY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    load_guardrail(root)
    scored_universe = prepare_scored_universe(root)
    attention_panels = load_attention_panels(root)
    candidate_df = build_candidate_universe(scored_universe, attention_panels)
    discovery_df = select_discovery_lane(candidate_df)
    summary_df = build_summary(candidate_df, discovery_df)
    save_outputs(root, discovery_df, summary_df)


if __name__ == "__main__":
    main()
