#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
METHOD_HINTS_NAME = "panel_day_engine_run_feature_method_hints_v1.csv"
SCORES_OUTPUT_NAME = "panel_day_engine_run_ranker_v0_scores.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_run_ranker_v0_summary.csv"
TOPRUNS_OUTPUT_NAME = "panel_day_engine_run_ranker_v0_topruns.csv"
TOPK_YIELD_SUMMARY_OUTPUT_NAME = "panel_day_engine_run_ranker_v0_topk_yield_summary.csv"
TOPK_YIELD_ROWS_OUTPUT_NAME = "panel_day_engine_run_ranker_v0_topk_yield_rows.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
STRING_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "run_shape_class", "cohort_hint"]
TOP_K_VALUES = [10, 20, 50, 100]
EPSILON = 1e-9
RAW_SCORE_FEATURES = [
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
]
TABLE_REQUIRED_COLS = [
    *KEY_COLS,
    "run_day_count",
    "run_shape_class",
    "cohort_hint",
    *RAW_SCORE_FEATURES,
]
METHOD_HINT_REQUIRED_COLS = [
    "feature_name",
    "comparison_target",
    "normalized_gap",
    "directional_hint",
    "method_relevance_class",
]
SCORE_NAMES = [
    "electrical_core_score",
    "electrical_evt_score",
    "electrical_evt_minus_broadshape_score",
    "electrical_core_minus_broadshape_025",
    "electrical_core_minus_broadshape_050",
    "electrical_core_minus_broadshape_075",
    "electrical_core_plus_evtonly_minus_broadshape_025",
    "electrical_core_plus_evtonly_minus_broadshape_050",
]
TWO_STAGE_CANDIDATE_NAMES = [
    "two_stage_core50_penalty050",
    "two_stage_core100_penalty050",
]
TOPK_CANDIDATE_NAMES = [*SCORE_NAMES, *TWO_STAGE_CANDIDATE_NAMES]
SCORES_OUTPUT_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "cohort_hint",
    *SCORE_NAMES,
]
SUMMARY_OUTPUT_COLS = [
    "score_name",
    "positive_like_count",
    "nuisance_like_count",
    "monitor_like_count",
    "unlabeled_other_count",
    "positive_like_median",
    "nuisance_like_median",
    "monitor_like_median",
    "unlabeled_other_median",
    "positive_vs_nuisance_gap",
    "positive_vs_monitor_gap",
    "top10_positive_like_count",
    "top10_nuisance_like_count",
    "top10_monitor_like_count",
    "top20_positive_like_count",
    "top20_nuisance_like_count",
    "top20_monitor_like_count",
]
TOPRUNS_OUTPUT_COLS = [
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
TOPK_YIELD_SUMMARY_COLS = [
    "score_name",
    "top_k",
    "topk_positive_like_count",
    "topk_nuisance_like_count",
    "topk_monitor_like_count",
    "topk_unlabeled_other_count",
    "topk_positive_like_rate",
    "topk_nuisance_like_rate",
    "topk_monitor_like_rate",
    "topk_unlabeled_other_rate",
    "topk_eligible_local_count",
    "topk_future_fault_linked_count",
    "topk_nuisance_alert_count",
    "topk_isolated_unexplained_count",
    "topk_recurring_monitor_like_count",
    "base_positive_like_rate",
    "base_nuisance_like_rate",
    "positive_like_lift",
    "nuisance_like_lift",
    "precision_minus_nuisance",
]
TOPK_YIELD_ROWS_COLS = [
    "score_name",
    "top_k",
    "rank",
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "cohort_hint",
    "score_value",
    "stage1_core_rank",
    "stage2_rerank_score",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
]
POSITIVE_LIKE = {"eligible_local", "future_fault_linked"}
NUISANCE_LIKE = {"nuisance_alert", "isolated_unexplained"}
MONITOR_LIKE = {"recurring_monitor_like"}
UNLABELED_OTHER = {"unmatched_other"}
ALL_SCORE_FEATURES = set(RAW_SCORE_FEATURES)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a run-level ranker v0 audit using existing run feature artifacts."
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


def load_feature_table(root: Path) -> pd.DataFrame:
    path = root / "_share" / FEATURE_TABLE_NAME
    df = read_csv(path)
    ensure_columns(df, TABLE_REQUIRED_COLS, path.name)
    df = drop_repeated_header_rows(df).copy()
    for col in STRING_COLS:
        normalizer = normalize_date if col in {"run_start_date", "run_end_date"} else normalize_text
        df[col] = df[col].map(normalizer)
    for col in TABLE_REQUIRED_COLS:
        if col in STRING_COLS:
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.loc[:, TABLE_REQUIRED_COLS].copy()
    return df.drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_method_hints(root: Path) -> pd.DataFrame:
    path = root / "_share" / METHOD_HINTS_NAME
    df = read_csv(path)
    ensure_columns(df, METHOD_HINT_REQUIRED_COLS, path.name)
    df = drop_repeated_header_rows(df).copy()
    df["feature_name"] = df["feature_name"].map(normalize_text)
    missing = sorted(ALL_SCORE_FEATURES - set(df["feature_name"]))
    if missing:
        raise SystemExit(
            "run feature method hints are missing required score features: "
            f"{missing}"
        )
    return df


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
    if cohort_hint in NUISANCE_LIKE:
        return "nuisance_like"
    if cohort_hint in MONITOR_LIKE:
        return "monitor_like"
    return "unlabeled_other"


def median_or_none(series: pd.Series) -> float | None:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return None
    return float(numeric.median())


def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    components = {
        "max_v_drop_z": robust_scale(out["max_v_drop"]),
        "one_minus_min_mid_v_ratio_z": robust_scale(1.0 - out["min_mid_v_ratio"]),
        "one_minus_min_mid_ratio_z": robust_scale(1.0 - out["min_mid_ratio"]),
        "cond_evt_only_day_ratio_z": robust_scale(out["cond_evt_only_day_ratio"]),
        "ae_mid_or_hi_early_day_ratio_z": robust_scale(out["ae_mid_or_hi_early_day_ratio"]),
        "mean_signal_count_z": robust_scale(out["mean_signal_count"]),
        "max_signal_count_z": robust_scale(out["max_signal_count"]),
        "p95_recon_error_z": robust_scale(out["p95_recon_error"]),
    }
    out = out.assign(**components)
    out["electrical_core_score"] = (
        out["max_v_drop_z"]
        + out["one_minus_min_mid_v_ratio_z"]
        + out["one_minus_min_mid_ratio_z"]
    )
    out["broadshape_penalty"] = (
        out["ae_mid_or_hi_early_day_ratio_z"]
        + out["mean_signal_count_z"]
        + out["max_signal_count_z"]
        + out["p95_recon_error_z"]
    )
    out["evtonly_bonus"] = out["cond_evt_only_day_ratio_z"]
    out["electrical_evt_score"] = (
        out["electrical_core_score"]
        + out["evtonly_bonus"]
    )
    out["electrical_evt_minus_broadshape_score"] = (
        out["electrical_core_score"]
        + out["evtonly_bonus"]
        - out["broadshape_penalty"]
    )
    out["electrical_core_minus_broadshape_025"] = (
        out["electrical_core_score"] - 0.25 * out["broadshape_penalty"]
    )
    out["electrical_core_minus_broadshape_050"] = (
        out["electrical_core_score"] - 0.50 * out["broadshape_penalty"]
    )
    out["electrical_core_minus_broadshape_075"] = (
        out["electrical_core_score"] - 0.75 * out["broadshape_penalty"]
    )
    out["electrical_core_plus_evtonly_minus_broadshape_025"] = (
        out["electrical_core_score"]
        + 0.25 * out["evtonly_bonus"]
        - 0.25 * out["broadshape_penalty"]
    )
    out["electrical_core_plus_evtonly_minus_broadshape_050"] = (
        out["electrical_core_score"]
        + 0.25 * out["evtonly_bonus"]
        - 0.50 * out["broadshape_penalty"]
    )
    out["evaluation_group"] = out["cohort_hint"].map(evaluation_group)
    return out


def top_k_group_count(df: pd.DataFrame, score_name: str, *, top_k: int, group_name: str) -> int:
    ranked = rank_runs(df, score_name).head(top_k)
    return int(ranked["evaluation_group"].eq(group_name).sum())


def rank_runs(df: pd.DataFrame, score_name: str) -> pd.DataFrame:
    ranked = df.sort_values(
        [score_name, "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[False, False, True, True, True, True],
        kind="stable",
    ).copy()
    ranked["score_value"] = ranked[score_name]
    ranked["rank"] = range(1, len(ranked) + 1)
    return ranked


def rank_two_stage(
    df: pd.DataFrame,
    *,
    shortlist_size: int,
    candidate_name: str,
) -> pd.DataFrame:
    stage1 = rank_runs(df, "electrical_core_score").copy()
    stage1["stage1_core_rank"] = stage1["rank"].astype(int)
    stage1["stage2_rerank_score"] = stage1["electrical_core_minus_broadshape_050"]
    shortlist = stage1.loc[stage1["stage1_core_rank"].le(shortlist_size)].copy()
    remainder = stage1.loc[stage1["stage1_core_rank"].gt(shortlist_size)].copy()

    if not shortlist.empty:
        shortlist = shortlist.sort_values(
            ["stage2_rerank_score", "stage1_core_rank"],
            ascending=[False, True],
            kind="stable",
        ).copy()
    final = pd.concat([shortlist, remainder], ignore_index=True)
    final["rank"] = range(1, len(final) + 1)
    final["score_name"] = candidate_name
    final["score_value"] = final["stage2_rerank_score"]
    return final


def rank_topk_candidate(df: pd.DataFrame, candidate_name: str) -> pd.DataFrame:
    if candidate_name in SCORE_NAMES:
        ranked = rank_runs(df, candidate_name).copy()
        ranked["stage1_core_rank"] = pd.NA
        ranked["stage2_rerank_score"] = pd.NA
        ranked["score_name"] = candidate_name
        return ranked
    if candidate_name == "two_stage_core50_penalty050":
        return rank_two_stage(df, shortlist_size=50, candidate_name=candidate_name)
    if candidate_name == "two_stage_core100_penalty050":
        return rank_two_stage(df, shortlist_size=100, candidate_name=candidate_name)
    raise SystemExit(f"unknown top-k candidate: {candidate_name}")


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for score_name in SCORE_NAMES:
        positive = df.loc[df["evaluation_group"].eq("positive_like"), score_name]
        nuisance = df.loc[df["evaluation_group"].eq("nuisance_like"), score_name]
        monitor = df.loc[df["evaluation_group"].eq("monitor_like"), score_name]
        unlabeled = df.loc[df["evaluation_group"].eq("unlabeled_other"), score_name]
        positive_median = median_or_none(positive)
        nuisance_median = median_or_none(nuisance)
        monitor_median = median_or_none(monitor)
        unlabeled_median = median_or_none(unlabeled)
        rows.append(
            {
                "score_name": score_name,
                "positive_like_count": int(df["evaluation_group"].eq("positive_like").sum()),
                "nuisance_like_count": int(df["evaluation_group"].eq("nuisance_like").sum()),
                "monitor_like_count": int(df["evaluation_group"].eq("monitor_like").sum()),
                "unlabeled_other_count": int(df["evaluation_group"].eq("unlabeled_other").sum()),
                "positive_like_median": positive_median,
                "nuisance_like_median": nuisance_median,
                "monitor_like_median": monitor_median,
                "unlabeled_other_median": unlabeled_median,
                "positive_vs_nuisance_gap": (
                    None if positive_median is None or nuisance_median is None else positive_median - nuisance_median
                ),
                "positive_vs_monitor_gap": (
                    None if positive_median is None or monitor_median is None else positive_median - monitor_median
                ),
                "top10_positive_like_count": top_k_group_count(df, score_name, top_k=10, group_name="positive_like"),
                "top10_nuisance_like_count": top_k_group_count(df, score_name, top_k=10, group_name="nuisance_like"),
                "top10_monitor_like_count": top_k_group_count(df, score_name, top_k=10, group_name="monitor_like"),
                "top20_positive_like_count": top_k_group_count(df, score_name, top_k=20, group_name="positive_like"),
                "top20_nuisance_like_count": top_k_group_count(df, score_name, top_k=20, group_name="nuisance_like"),
                "top20_monitor_like_count": top_k_group_count(df, score_name, top_k=20, group_name="monitor_like"),
            }
        )
    return pd.DataFrame(rows).reindex(columns=SUMMARY_OUTPUT_COLS)


def build_topruns(df: pd.DataFrame) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for score_name in SCORE_NAMES:
        ranked = rank_runs(df, score_name).head(30).copy()
        ranked.insert(0, "score_name", score_name)
        parts.append(ranked.loc[:, TOPRUNS_OUTPUT_COLS].copy())
    if not parts:
        return pd.DataFrame(columns=TOPRUNS_OUTPUT_COLS)
    return pd.concat(parts, ignore_index=True)


def build_topk_yield(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    row_parts: list[pd.DataFrame] = []
    total_labeled_count = int(df["evaluation_group"].ne("unlabeled_other").sum())
    positive_like_count = int(df["evaluation_group"].eq("positive_like").sum())
    nuisance_like_count = int(df["evaluation_group"].eq("nuisance_like").sum())
    base_positive_like_rate = positive_like_count / (total_labeled_count + EPSILON)
    base_nuisance_like_rate = nuisance_like_count / (total_labeled_count + EPSILON)

    for score_name in TOPK_CANDIDATE_NAMES:
        ranked = rank_topk_candidate(df, score_name)
        for top_k in TOP_K_VALUES:
            top_df = ranked.head(top_k).copy()
            selected_count = len(top_df)
            denom = selected_count if selected_count > 0 else 1
            topk_positive_like_count = int(top_df["evaluation_group"].eq("positive_like").sum())
            topk_nuisance_like_count = int(top_df["evaluation_group"].eq("nuisance_like").sum())
            topk_monitor_like_count = int(top_df["evaluation_group"].eq("monitor_like").sum())
            topk_unlabeled_other_count = int(top_df["evaluation_group"].eq("unlabeled_other").sum())
            topk_positive_like_rate = topk_positive_like_count / denom
            topk_nuisance_like_rate = topk_nuisance_like_count / denom
            topk_monitor_like_rate = topk_monitor_like_count / denom
            topk_unlabeled_other_rate = topk_unlabeled_other_count / denom

            summary_rows.append(
                {
                    "score_name": score_name,
                    "top_k": top_k,
                    "topk_positive_like_count": topk_positive_like_count,
                    "topk_nuisance_like_count": topk_nuisance_like_count,
                    "topk_monitor_like_count": topk_monitor_like_count,
                    "topk_unlabeled_other_count": topk_unlabeled_other_count,
                    "topk_positive_like_rate": topk_positive_like_rate,
                    "topk_nuisance_like_rate": topk_nuisance_like_rate,
                    "topk_monitor_like_rate": topk_monitor_like_rate,
                    "topk_unlabeled_other_rate": topk_unlabeled_other_rate,
                    "topk_eligible_local_count": int(top_df["cohort_hint"].eq("eligible_local").sum()),
                    "topk_future_fault_linked_count": int(top_df["cohort_hint"].eq("future_fault_linked").sum()),
                    "topk_nuisance_alert_count": int(top_df["cohort_hint"].eq("nuisance_alert").sum()),
                    "topk_isolated_unexplained_count": int(top_df["cohort_hint"].eq("isolated_unexplained").sum()),
                    "topk_recurring_monitor_like_count": int(top_df["cohort_hint"].eq("recurring_monitor_like").sum()),
                    "base_positive_like_rate": base_positive_like_rate,
                    "base_nuisance_like_rate": base_nuisance_like_rate,
                    "positive_like_lift": topk_positive_like_rate / (base_positive_like_rate + EPSILON),
                    "nuisance_like_lift": topk_nuisance_like_rate / (base_nuisance_like_rate + EPSILON),
                    "precision_minus_nuisance": topk_positive_like_rate - topk_nuisance_like_rate,
                }
            )

            if selected_count > 0:
                selected = top_df.loc[:, TOPK_YIELD_ROWS_COLS[2:]].copy()
                selected.insert(0, "top_k", top_k)
                selected.insert(0, "score_name", score_name)
                row_parts.append(selected)

    summary_df = pd.DataFrame(summary_rows).reindex(columns=TOPK_YIELD_SUMMARY_COLS)
    rows_df = pd.concat(row_parts, ignore_index=True) if row_parts else pd.DataFrame(columns=TOPK_YIELD_ROWS_COLS)
    return summary_df, rows_df.reindex(columns=TOPK_YIELD_ROWS_COLS)


def write_csv(path: Path, df: pd.DataFrame, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    feature_table = load_feature_table(root)
    _method_hints = load_method_hints(root)
    scored = compute_scores(feature_table)
    summary = build_summary(scored)
    topruns = build_topruns(scored)
    topk_yield_summary, topk_yield_rows = build_topk_yield(scored)

    share_dir = root / "_share"
    write_csv(share_dir / SCORES_OUTPUT_NAME, scored.loc[:, SCORES_OUTPUT_COLS].copy(), SCORES_OUTPUT_COLS)
    write_csv(share_dir / SUMMARY_OUTPUT_NAME, summary, SUMMARY_OUTPUT_COLS)
    write_csv(share_dir / TOPRUNS_OUTPUT_NAME, topruns, TOPRUNS_OUTPUT_COLS)
    write_csv(share_dir / TOPK_YIELD_SUMMARY_OUTPUT_NAME, topk_yield_summary, TOPK_YIELD_SUMMARY_COLS)
    write_csv(share_dir / TOPK_YIELD_ROWS_OUTPUT_NAME, topk_yield_rows, TOPK_YIELD_ROWS_COLS)


if __name__ == "__main__":
    main()
