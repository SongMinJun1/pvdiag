#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import build_panel_day_engine_run_ranker_v2_holdout_audit as holdout_base

DISCOVERY_NAME = "panel_day_engine_operator_secondary_discovery_v1.csv"
FATE_CASES_NAME = "panel_day_engine_operator_secondary_discovery_fate_cases_v1.csv"

SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_separability_summary_v1.csv"
CASES_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_separability_cases_v1.csv"
RECOMMENDATION_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_separability_recommendation_v1.csv"

KEY_COLS = holdout_base.KEY_COLS
NUMERIC_FEATURES = [
    "logistic_v3_discovery_score",
    "electrical_core_minus_broadshape_050",
    "run_day_count",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
]
CURRENT_STATE_COLS = [
    *KEY_COLS,
    "run_day_count",
    "run_shape_class",
    "logistic_v3_discovery_score",
    "electrical_core_minus_broadshape_050",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
]
REQUIRED_FATE_COLS = [*KEY_COLS, "discovery_fate_class"]
TARGET_FATE_GROUPS = [
    "future_fault_linked",
    "recurring_monitor_like",
    "isolated_unexplained",
]
COMPARISON_GROUPS = [
    ("future_fault_linked", "recurring_monitor_like"),
    ("future_fault_linked", "isolated_unexplained"),
]
LINKED_CLASSES = {"future_fault_linked", "future_truth_linked"}
CASE_SORT_ORDER = {
    "future_fault_linked": 0,
    "future_truth_linked": 1,
    "recurring_monitor_like": 2,
    "isolated_unexplained": 3,
}
SUMMARY_COLS = [
    "record_type",
    "fate_group",
    "feature_name",
    "run_count",
    "median_value",
    "p25_value",
    "p75_value",
    "lhs_group",
    "rhs_group",
    "lhs_median",
    "rhs_median",
    "median_gap",
    "normalized_gap",
    "site",
    "selected_discovery_count",
    "future_fault_linked_count",
    "future_truth_linked_count",
    "recurring_monitor_like_count",
    "isolated_unexplained_count",
    "future_fault_or_truth_linked_rate",
    "recurring_monitor_like_rate",
    "isolated_unexplained_rate",
    "note_ko",
]
CASE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "logistic_v3_discovery_score",
    "electrical_core_minus_broadshape_050",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "discovery_fate_class",
    "separability_reason_ko",
]
RECOMMENDATION_COLS = ["recommended_next_direction", "rationale_ko"]
CLEAR_FEATURE_GAP_THRESHOLD = 1.0
WEAK_FEATURE_GAP_THRESHOLD = 0.75
SITE_DOMINANCE_THRESHOLD = 0.40
EPS = 1e-9


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit whether the operator secondary discovery lane can be split into hidden-value vs monitor/noisy sublanes using current-state features only."
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


def load_discovery(root: Path) -> pd.DataFrame:
    path = root / "_share" / DISCOVERY_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, CURRENT_STATE_COLS, path.name)
    df = holdout_base.normalize_key_cols(df)
    df["run_shape_class"] = df["run_shape_class"].map(holdout_base.normalize_text)
    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return (
        df.loc[:, CURRENT_STATE_COLS]
        .drop_duplicates(subset=KEY_COLS, keep="first")
        .reset_index(drop=True)
    )


def load_fate_cases(root: Path) -> pd.DataFrame:
    path = root / "_share" / FATE_CASES_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_FATE_COLS, path.name)
    df = holdout_base.normalize_key_cols(df)
    df["discovery_fate_class"] = df["discovery_fate_class"].map(holdout_base.normalize_text)
    return (
        df.loc[:, [*KEY_COLS, "discovery_fate_class"]]
        .drop_duplicates(subset=KEY_COLS, keep="first")
        .reset_index(drop=True)
    )


def prepare_analysis_df(root: Path) -> pd.DataFrame:
    discovery_df = load_discovery(root)
    fate_df = load_fate_cases(root)

    discovery_keys = {
        tuple(row)
        for row in discovery_df.loc[:, KEY_COLS].itertuples(index=False, name=None)
    }
    fate_keys = {
        tuple(row)
        for row in fate_df.loc[:, KEY_COLS].itertuples(index=False, name=None)
    }
    if discovery_keys != fate_keys:
        missing_in_fate = sorted(discovery_keys - fate_keys)[:5]
        missing_in_discovery = sorted(fate_keys - discovery_keys)[:5]
        raise SystemExit(
            "secondary discovery and fate case keys must match exactly; "
            f"missing_in_fate={missing_in_fate}, missing_in_discovery={missing_in_discovery}"
        )

    merged = discovery_df.merge(
        fate_df,
        on=KEY_COLS,
        how="inner",
        validate="one_to_one",
    )
    return merged.copy()


def quantile(values: pd.Series, q: float) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return float("nan")
    return float(clean.quantile(q))


def median(values: pd.Series) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return float("nan")
    return float(clean.median())


def build_group_feature_rows(analysis_df: pd.DataFrame) -> tuple[list[dict[str, object]], dict[tuple[str, str], dict[str, float]]]:
    rows: list[dict[str, object]] = []
    stats_map: dict[tuple[str, str], dict[str, float]] = {}
    for fate_group in TARGET_FATE_GROUPS:
        group_df = analysis_df.loc[analysis_df["discovery_fate_class"].eq(fate_group)].copy()
        for feature in NUMERIC_FEATURES:
            feature_values = pd.to_numeric(group_df[feature], errors="coerce")
            row = {
                "record_type": "group_feature_summary",
                "fate_group": fate_group,
                "feature_name": feature,
                "run_count": int(feature_values.notna().sum()),
                "median_value": median(feature_values),
                "p25_value": quantile(feature_values, 0.25),
                "p75_value": quantile(feature_values, 0.75),
                "note_ko": "fate group별 current-state numeric feature 분포",
            }
            rows.append(row)
            stats_map[(fate_group, feature)] = {
                "run_count": row["run_count"],
                "median": row["median_value"],
                "p25": row["p25_value"],
                "p75": row["p75_value"],
            }
    return rows, stats_map


def build_comparison_rows(stats_map: dict[tuple[str, str], dict[str, float]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for lhs_group, rhs_group in COMPARISON_GROUPS:
        for feature in NUMERIC_FEATURES:
            lhs = stats_map.get((lhs_group, feature), {})
            rhs = stats_map.get((rhs_group, feature), {})
            lhs_iqr = float(lhs.get("p75", float("nan")) - lhs.get("p25", float("nan")))
            rhs_iqr = float(rhs.get("p75", float("nan")) - rhs.get("p25", float("nan")))
            pooled_iqr = (
                ((lhs_iqr if pd.notna(lhs_iqr) else 0.0) + (rhs_iqr if pd.notna(rhs_iqr) else 0.0)) / 2.0
            )
            lhs_median = lhs.get("median", float("nan"))
            rhs_median = rhs.get("median", float("nan"))
            median_gap = (
                float(lhs_median - rhs_median)
                if pd.notna(lhs_median) and pd.notna(rhs_median)
                else float("nan")
            )
            normalized_gap = (
                float(median_gap / (pooled_iqr + EPS))
                if pd.notna(median_gap)
                else float("nan")
            )
            rows.append(
                {
                    "record_type": "comparison_summary",
                    "feature_name": feature,
                    "run_count": int(lhs.get("run_count", 0)) + int(rhs.get("run_count", 0)),
                    "lhs_group": lhs_group,
                    "rhs_group": rhs_group,
                    "lhs_median": lhs_median,
                    "rhs_median": rhs_median,
                    "median_gap": median_gap,
                    "normalized_gap": normalized_gap,
                    "note_ko": "future fate group 사이 current-state feature median gap과 robust normalized gap",
                }
            )
    return rows


def build_site_rows(analysis_df: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for site in sorted(analysis_df["site"].dropna().map(holdout_base.normalize_text).unique()):
        site_df = analysis_df.loc[analysis_df["site"].eq(site)].copy()
        selected_count = int(len(site_df))
        linked_count = int(site_df["discovery_fate_class"].isin(LINKED_CLASSES).sum())
        rows.append(
            {
                "record_type": "site_effect_summary",
                "site": site,
                "selected_discovery_count": selected_count,
                "future_fault_linked_count": int(site_df["discovery_fate_class"].eq("future_fault_linked").sum()),
                "future_truth_linked_count": int(site_df["discovery_fate_class"].eq("future_truth_linked").sum()),
                "recurring_monitor_like_count": int(site_df["discovery_fate_class"].eq("recurring_monitor_like").sum()),
                "isolated_unexplained_count": int(site_df["discovery_fate_class"].eq("isolated_unexplained").sum()),
                "future_fault_or_truth_linked_rate": (linked_count / selected_count) if selected_count else 0.0,
                "recurring_monitor_like_rate": (
                    int(site_df["discovery_fate_class"].eq("recurring_monitor_like").sum()) / selected_count
                    if selected_count else 0.0
                ),
                "isolated_unexplained_rate": (
                    int(site_df["discovery_fate_class"].eq("isolated_unexplained").sum()) / selected_count
                    if selected_count else 0.0
                ),
                "note_ko": "site별 discovery fate mix로 current-state separability보다 site effect가 큰지 점검",
            }
        )
    return rows


def build_summary_df(analysis_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    group_rows, stats_map = build_group_feature_rows(analysis_df)
    comparison_rows = build_comparison_rows(stats_map)
    site_rows = build_site_rows(analysis_df)
    summary_df = pd.DataFrame(
        [*group_rows, *comparison_rows, *site_rows],
        columns=SUMMARY_COLS,
    ).reindex(columns=SUMMARY_COLS)
    comparison_df = summary_df.loc[summary_df["record_type"].eq("comparison_summary")].copy()
    return summary_df, comparison_df


def build_reason(row: pd.Series, group_medians: dict[str, dict[str, float]]) -> str:
    fate_class = holdout_base.normalize_text(row["discovery_fate_class"])
    fault_median = group_medians.get("future_fault_linked", {})
    recurring_median = group_medians.get("recurring_monitor_like", {})
    fault_score = fault_median.get("electrical_core_minus_broadshape_050", float("nan"))
    recurring_score = recurring_median.get("electrical_core_minus_broadshape_050", float("nan"))
    electrical_score = pd.to_numeric(pd.Series([row["electrical_core_minus_broadshape_050"]]), errors="coerce").iloc[0]
    run_shape = holdout_base.normalize_text(row["run_shape_class"])

    if fate_class == "future_fault_linked":
        if pd.notna(fault_score) and electrical_score >= fault_score:
            return "현재 electrical severity가 linked group 중앙값 이상이라 hidden value 쪽 current profile이 비교적 뚜렷하다."
        return "현재 electrical severity와 ratio profile이 recurring burden보다는 hidden value 쪽에 더 가깝다."
    if fate_class == "recurring_monitor_like":
        if pd.notna(recurring_score) and electrical_score <= recurring_score:
            return "현재 electrical severity가 linked group보다 낮고 반복 burden형 분포에 가까워 monitor lane 해석이 더 자연스럽다."
        return "현재 score는 있지만 run shape와 corroboration 조합이 recurring monitor burden 쪽에 더 가깝다."
    if fate_class == "isolated_unexplained":
        if run_shape == "short_alert_run":
            return "현재 short run 중심 profile이고 linked/recurring 쪽 current-state 구분 신호가 약해 analyst-only 확인이 필요하다."
        return "현재 electrical severity와 corroboration이 linked group 대비 약해 isolated discovery로 남는 profile이다."
    return "현재 state 기준으로는 linked/monitor 경계가 애매해 analyst 확인이 필요한 discovery profile이다."


def build_case_df(analysis_df: pd.DataFrame) -> pd.DataFrame:
    group_medians = {
        fate_group: {
            feature: median(group_df[feature])
            for feature in NUMERIC_FEATURES
        }
        for fate_group, group_df in analysis_df.groupby("discovery_fate_class", sort=False)
    }
    case_df = analysis_df.loc[:, [*CURRENT_STATE_COLS, "discovery_fate_class"]].copy()
    case_df["separability_reason_ko"] = case_df.apply(build_reason, axis=1, group_medians=group_medians)
    case_df["_class_order"] = case_df["discovery_fate_class"].map(CASE_SORT_ORDER).fillna(9).astype(int)
    case_df = case_df.sort_values(
        ["_class_order", "logistic_v3_discovery_score", "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[True, False, False, True, True, True, True],
        kind="stable",
    ).drop(columns="_class_order")
    return case_df.reindex(columns=CASE_COLS).reset_index(drop=True)


def site_effect_strength(summary_df: pd.DataFrame) -> float:
    site_df = summary_df.loc[summary_df["record_type"].eq("site_effect_summary")].copy()
    if site_df.empty:
        return 0.0
    linked_range = float(site_df["future_fault_or_truth_linked_rate"].max() - site_df["future_fault_or_truth_linked_rate"].min())
    recurring_range = float(site_df["recurring_monitor_like_rate"].max() - site_df["recurring_monitor_like_rate"].min())
    isolated_range = float(site_df["isolated_unexplained_rate"].max() - site_df["isolated_unexplained_rate"].min())
    return max(linked_range, recurring_range, isolated_range)


def build_recommendation_df(summary_df: pd.DataFrame, comparison_df: pd.DataFrame) -> pd.DataFrame:
    target_cmp = comparison_df.loc[
        comparison_df["lhs_group"].eq("future_fault_linked")
        & comparison_df["rhs_group"].eq("recurring_monitor_like")
    ].copy()
    target_cmp["abs_normalized_gap"] = target_cmp["normalized_gap"].abs()
    top_gap_row = (
        target_cmp.sort_values(["abs_normalized_gap", "feature_name"], ascending=[False, True], kind="stable").iloc[0]
        if not target_cmp.empty else None
    )
    max_abs_gap = float(top_gap_row["abs_normalized_gap"]) if top_gap_row is not None and pd.notna(top_gap_row["abs_normalized_gap"]) else 0.0
    top_feature = str(top_gap_row["feature_name"]) if top_gap_row is not None else ""
    site_strength = site_effect_strength(summary_df)

    if site_strength >= SITE_DOMINANCE_THRESHOLD and max_abs_gap < WEAK_FEATURE_GAP_THRESHOLD:
        direction = "try_site_conditioned_discovery_policy"
        rationale = (
            f"site별 discovery fate mix 차이 최대폭이 {site_strength:.3f}로 큰 반면 "
            f"future_fault_linked vs recurring_monitor_like current-state gap 최대치는 {max_abs_gap:.3f}로 약해 "
            "site-conditioned discovery policy를 먼저 시험하는 편이 더 자연스럽다."
        )
    elif max_abs_gap >= CLEAR_FEATURE_GAP_THRESHOLD:
        direction = "try_feature_threshold_split"
        rationale = (
            f"{top_feature}에서 future_fault_linked vs recurring_monitor_like normalized_gap={max_abs_gap:.3f}로 벌어져 "
            "current-state threshold split으로 hidden value lane과 monitor burden lane을 나눠볼 근거가 있다."
        )
    else:
        direction = "keep_secondary_discovery_as_analyst_only"
        rationale = (
            f"site effect 최대폭 {site_strength:.3f}, current-state gap 최대치 {max_abs_gap:.3f} 모두 결정적이지 않아 "
            "지금은 secondary discovery를 analyst-only lane으로 유지하는 편이 안전하다."
        )

    return pd.DataFrame(
        [{"recommended_next_direction": direction, "rationale_ko": rationale}],
        columns=RECOMMENDATION_COLS,
    )


def save_outputs(root: Path, summary_df: pd.DataFrame, case_df: pd.DataFrame, recommendation_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    case_df.to_csv(share_dir / CASES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    recommendation_df.to_csv(share_dir / RECOMMENDATION_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    analysis_df = prepare_analysis_df(root)
    summary_df, comparison_df = build_summary_df(analysis_df)
    case_df = build_case_df(analysis_df)
    recommendation_df = build_recommendation_df(summary_df, comparison_df)
    save_outputs(root, summary_df, case_df, recommendation_df)


if __name__ == "__main__":
    main()
