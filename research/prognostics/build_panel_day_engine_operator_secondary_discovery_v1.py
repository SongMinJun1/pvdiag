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
THRESHOLD_SPLIT_RECOMMENDATION_NAME = "panel_day_engine_operator_secondary_discovery_threshold_split_recommendation_v1.csv"
FATE_CASES_NAME = "panel_day_engine_operator_secondary_discovery_fate_cases_v1.csv"
OPERATOR_ATTENTION_NOW_NAME = "panel_day_engine_operator_attention_now_v1.csv"
V0_SCORES_NAME = "panel_day_engine_run_ranker_v0_scores.csv"

DISCOVERY_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_summary_v1.csv"
VALUE_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_value_v1.csv"
MONITOR_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_monitor_v1.csv"

EXPECTED_RECOMMENDATION = "use_logistic_as_secondary_discovery_lane"
EXPECTED_SPLIT_DIRECTION = "split_secondary_discovery_into_value_vs_monitor"
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
REQUIRED_SPLIT_RECOMMENDATION_COLS = ["recommended_split_rule", "recommended_next_direction", "rationale_ko"]
REQUIRED_ATTENTION_COLS = ["site", "panel_id"]
REQUIRED_V0_COLS = [*KEY_COLS, REFERENCE_SCORE_COL]
REQUIRED_FATE_CASES_COLS = [*KEY_COLS, "discovery_fate_class"]
ALLOWED_SPLIT_FAMILIES = {
    "electrical_only",
    "logistic_only",
    "electrical_and_low_ae",
    "electrical_and_low_recon",
    "logistic_and_low_ae",
    "logistic_and_low_recon",
}

BASE_DISCOVERY_COLS = [
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

DISCOVERY_COLS = [
    *[col for col in BASE_DISCOVERY_COLS if col != "discovery_reason_ko"],
    "discovery_split_class",
    "value_lane_flag",
    "monitor_lane_flag",
    "split_rule_name",
    "split_reason_ko",
    "discovery_reason_ko",
]

SUMMARY_COLS = [
    "record_type",
    "site",
    "candidate_universe_count",
    "selected_discovery_count",
    "value_lane_count",
    "monitor_lane_count",
    "selected_chronic_count",
    "selected_medium_count",
    "selected_short_count",
    "value_lane_chronic_count",
    "value_lane_medium_count",
    "value_lane_short_count",
    "monitor_lane_chronic_count",
    "monitor_lane_medium_count",
    "monitor_lane_short_count",
    "value_lane_future_fault_linked_ref_count",
    "value_lane_future_truth_linked_ref_count",
    "monitor_lane_future_fault_linked_ref_count",
    "monitor_lane_future_truth_linked_ref_count",
    "split_rule_name",
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


def parse_numeric(text: str) -> float:
    try:
        return float(text)
    except ValueError as exc:
        raise SystemExit(f"invalid numeric threshold: {text}") from exc


def parse_split_rule(rule_name: str) -> dict[str, object]:
    text = holdout_base.normalize_text(rule_name)
    if not text or "|" not in text:
        raise SystemExit(f"recommended_split_rule must be '<family>|<threshold_spec>', got: {rule_name}")
    family, threshold_spec = text.split("|", 1)
    family = holdout_base.normalize_text(family)
    threshold_spec = holdout_base.normalize_text(threshold_spec)
    if family not in ALLOWED_SPLIT_FAMILIES:
        raise SystemExit(f"unsupported split rule family: {family}")
    clauses: list[tuple[str, str, float]] = []
    for part in threshold_spec.split("|"):
        part = holdout_base.normalize_text(part)
        if ">=" in part:
            field, value = part.split(">=", 1)
            op = ">="
        elif "<=" in part:
            field, value = part.split("<=", 1)
            op = "<="
        else:
            raise SystemExit(f"unsupported threshold clause: {part}")
        clauses.append((holdout_base.normalize_text(field), op, parse_numeric(holdout_base.normalize_text(value))))

    expected_fields = {
        "electrical_only": ["electrical_core_minus_broadshape_050"],
        "logistic_only": ["logistic_v3_discovery_score"],
        "electrical_and_low_ae": ["electrical_core_minus_broadshape_050", "ae_mid_or_hi_early_day_ratio"],
        "electrical_and_low_recon": ["electrical_core_minus_broadshape_050", "p95_recon_error"],
        "logistic_and_low_ae": ["logistic_v3_discovery_score", "ae_mid_or_hi_early_day_ratio"],
        "logistic_and_low_recon": ["logistic_v3_discovery_score", "p95_recon_error"],
    }[family]
    observed_fields = [field for field, _, _ in clauses]
    if observed_fields != expected_fields:
        raise SystemExit(
            f"split rule {family} expects fields {expected_fields}, got {observed_fields} in {threshold_spec}"
        )
    return {
        "rule_name": text,
        "rule_family": family,
        "threshold_spec": threshold_spec,
        "clauses": clauses,
    }


def load_split_guardrail(root: Path) -> dict[str, object]:
    path = root / "_share" / THRESHOLD_SPLIT_RECOMMENDATION_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_SPLIT_RECOMMENDATION_COLS, path.name)
    if len(df) != 1:
        raise SystemExit(f"{path.name} must contain exactly one row")
    recommended_next_direction = holdout_base.normalize_text(df.iloc[0]["recommended_next_direction"])
    if recommended_next_direction != EXPECTED_SPLIT_DIRECTION:
        raise SystemExit(
            f"recommended_next_direction must be {EXPECTED_SPLIT_DIRECTION}, got {recommended_next_direction}. "
            "Secondary discovery value/monitor split is disabled by the threshold split guardrail."
        )
    recommended_split_rule = holdout_base.normalize_text(df.iloc[0]["recommended_split_rule"])
    if not recommended_split_rule:
        raise SystemExit(f"{path.name} must provide recommended_split_rule")
    return parse_split_rule(recommended_split_rule)


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


def load_fate_references(root: Path) -> pd.DataFrame:
    path = root / "_share" / FATE_CASES_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_FATE_CASES_COLS, path.name)
    df = holdout_base.normalize_key_cols(df)
    df["discovery_fate_class"] = df["discovery_fate_class"].map(holdout_base.normalize_text)
    df["future_fault_linked_ref_flag"] = df["discovery_fate_class"].eq("future_fault_linked").astype(int)
    df["future_truth_linked_ref_flag"] = df["discovery_fate_class"].eq("future_truth_linked").astype(int)
    return (
        df.loc[:, [*KEY_COLS, "future_fault_linked_ref_flag", "future_truth_linked_ref_flag"]]
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
        return candidate_df.loc[:, BASE_DISCOVERY_COLS].copy()

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
    return selected.loc[:, BASE_DISCOVERY_COLS].copy()


def apply_split_rule(df: pd.DataFrame, split_rule: dict[str, object]) -> pd.Series:
    mask = pd.Series(True, index=df.index, dtype=bool)
    for field, op, threshold in split_rule["clauses"]:
        values = pd.to_numeric(df[field], errors="coerce")
        if op == ">=":
            mask &= values.ge(threshold)
        elif op == "<=":
            mask &= values.le(threshold)
        else:
            raise SystemExit(f"unsupported operator: {op}")
    return mask.fillna(False)


def split_reason(row: pd.Series, split_rule: dict[str, object]) -> str:
    family = str(split_rule["rule_family"])
    if int(row["value_lane_flag"]) == 1:
        if family.startswith("electrical"):
            return "전기 severity 기준 상위 value 후보"
        return "learned discovery score 기준 상위 value 후보"
    if family.endswith("low_recon"):
        return "broadshape/recon 경향 monitor 후보"
    if family.endswith("low_ae"):
        return "broadshape/AE 경향 monitor 후보"
    return "learned discovery 보조 lane의 monitor 후보"


def apply_discovery_split(discovery_df: pd.DataFrame, split_rule: dict[str, object]) -> pd.DataFrame:
    enriched = discovery_df.copy()
    value_mask = apply_split_rule(enriched, split_rule)
    enriched["value_lane_flag"] = value_mask.astype(int)
    enriched["monitor_lane_flag"] = (~value_mask).astype(int)
    enriched["discovery_split_class"] = enriched["value_lane_flag"].map(
        lambda flag: "value_candidate_lane" if int(flag) == 1 else "monitor_candidate_lane"
    )
    enriched["split_rule_name"] = str(split_rule["rule_name"])
    enriched["split_reason_ko"] = enriched.apply(split_reason, axis=1, split_rule=split_rule)
    return enriched.loc[:, DISCOVERY_COLS].copy()


def build_lane_outputs(discovery_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    value_df = discovery_df.loc[discovery_df["value_lane_flag"].eq(1)].copy()
    monitor_df = discovery_df.loc[discovery_df["monitor_lane_flag"].eq(1)].copy()
    value_df = value_df.sort_values(
        [REFERENCE_SCORE_COL, DISCOVERY_SCORE_COL, "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[False, False, False, True, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    monitor_df = monitor_df.sort_values(
        [DISCOVERY_SCORE_COL, REFERENCE_SCORE_COL, "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[False, False, False, True, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    return value_df, monitor_df


def build_summary(candidate_df: pd.DataFrame, selected_df: pd.DataFrame, fate_ref_df: pd.DataFrame, split_rule_name: str) -> pd.DataFrame:
    selected_df = selected_df.merge(
        fate_ref_df,
        on=KEY_COLS,
        how="left",
        validate="one_to_one",
    )
    for col in ["future_fault_linked_ref_flag", "future_truth_linked_ref_flag"]:
        selected_df[col] = pd.to_numeric(selected_df[col], errors="coerce").fillna(0).astype(int)
    rows: list[dict[str, object]] = []

    def summarize(site: str, record_type: str) -> None:
        if record_type == "overall":
            cand = candidate_df.copy()
            sel = selected_df.copy()
        else:
            cand = candidate_df.loc[candidate_df["site"].eq(site)].copy()
            sel = selected_df.loc[selected_df["site"].eq(site)].copy()
        value_sel = sel.loc[sel["value_lane_flag"].eq(1)].copy()
        monitor_sel = sel.loc[sel["monitor_lane_flag"].eq(1)].copy()

        row = {
            "record_type": record_type,
            "site": site,
            "candidate_universe_count": int(len(cand)),
            "selected_discovery_count": int(len(sel)),
            "value_lane_count": int(len(value_sel)),
            "monitor_lane_count": int(len(monitor_sel)),
            "selected_chronic_count": 0,
            "selected_medium_count": 0,
            "selected_short_count": 0,
            "value_lane_chronic_count": 0,
            "value_lane_medium_count": 0,
            "value_lane_short_count": 0,
            "monitor_lane_chronic_count": 0,
            "monitor_lane_medium_count": 0,
            "monitor_lane_short_count": 0,
            "value_lane_future_fault_linked_ref_count": int(value_sel["future_fault_linked_ref_flag"].sum()) if not value_sel.empty else 0,
            "value_lane_future_truth_linked_ref_count": int(value_sel["future_truth_linked_ref_flag"].sum()) if not value_sel.empty else 0,
            "monitor_lane_future_fault_linked_ref_count": int(monitor_sel["future_fault_linked_ref_flag"].sum()) if not monitor_sel.empty else 0,
            "monitor_lane_future_truth_linked_ref_count": int(monitor_sel["future_truth_linked_ref_flag"].sum()) if not monitor_sel.empty else 0,
            "split_rule_name": split_rule_name,
            "median_discovery_score": sel[DISCOVERY_SCORE_COL].median() if not sel.empty else None,
            "max_discovery_score": sel[DISCOVERY_SCORE_COL].max() if not sel.empty else None,
            "note_ko": "main operator baseline은 그대로 두고, learned secondary discovery를 value vs monitor 하위 lane으로만 분리",
        }
        for col_name, shape_name in SHAPE_BUCKETS.items():
            row[col_name] = int(sel["run_shape_class"].eq(shape_name).sum()) if not sel.empty else 0
        shape_to_lane_cols = {
            "chronic_alert_run": ("value_lane_chronic_count", "monitor_lane_chronic_count"),
            "medium_alert_run": ("value_lane_medium_count", "monitor_lane_medium_count"),
            "short_alert_run": ("value_lane_short_count", "monitor_lane_short_count"),
        }
        for shape_name, (value_col, monitor_col) in shape_to_lane_cols.items():
            row[value_col] = int(value_sel["run_shape_class"].eq(shape_name).sum()) if not value_sel.empty else 0
            row[monitor_col] = int(monitor_sel["run_shape_class"].eq(shape_name).sum()) if not monitor_sel.empty else 0
        rows.append(row)

    summarize("", "overall")
    for site in sorted(candidate_df["site"].dropna().map(holdout_base.normalize_text).unique()):
        summarize(site, "site")

    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def save_outputs(root: Path, discovery_df: pd.DataFrame, summary_df: pd.DataFrame, value_df: pd.DataFrame, monitor_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    discovery_df.to_csv(share_dir / DISCOVERY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    value_df.to_csv(share_dir / VALUE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    monitor_df.to_csv(share_dir / MONITOR_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    load_guardrail(root)
    split_rule = load_split_guardrail(root)
    scored_universe = prepare_scored_universe(root)
    attention_panels = load_attention_panels(root)
    candidate_df = build_candidate_universe(scored_universe, attention_panels)
    discovery_df = select_discovery_lane(candidate_df)
    discovery_df = apply_discovery_split(discovery_df, split_rule)
    value_df, monitor_df = build_lane_outputs(discovery_df)
    fate_ref_df = load_fate_references(root)
    summary_df = build_summary(candidate_df, discovery_df, fate_ref_df, str(split_rule["rule_name"]))
    save_outputs(root, discovery_df, summary_df, value_df, monitor_df)


if __name__ == "__main__":
    main()
