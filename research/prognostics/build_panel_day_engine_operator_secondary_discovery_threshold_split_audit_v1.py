#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import build_panel_day_engine_run_ranker_v2_holdout_audit as holdout_base

DISCOVERY_NAME = "panel_day_engine_operator_secondary_discovery_v1.csv"
FATE_CASES_NAME = "panel_day_engine_operator_secondary_discovery_fate_cases_v1.csv"
SEPARABILITY_SUMMARY_NAME = "panel_day_engine_operator_secondary_discovery_separability_summary_v1.csv"

SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_threshold_split_summary_v1.csv"
CASES_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_threshold_split_cases_v1.csv"
RECOMMENDATION_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_threshold_split_recommendation_v1.csv"

KEY_COLS = holdout_base.KEY_COLS
POSITIVE_GROUP = "future_fault_linked"
NEGATIVE_GROUPS = {"recurring_monitor_like", "isolated_unexplained"}
ALLOWED_FATE_GROUPS = {POSITIVE_GROUP, *NEGATIVE_GROUPS}

LOGISTIC_THRESHOLDS = [0.95, 0.97, 0.99]
ELECTRICAL_THRESHOLDS = [6, 8, 10, 12]
AE_THRESHOLDS = [0.0, 0.25, 0.5]
RECON_THRESHOLDS = [0.005, 0.01, 0.02, 0.05]
SWEEP_HINT_FEATURES = {
    "logistic_v3_discovery_score",
    "electrical_core_minus_broadshape_050",
    "ae_mid_or_hi_early_day_ratio",
    "p95_recon_error",
    "max_v_drop",
    "min_mid_ratio",
}

BASE_REQUIRED_FATE_COLS = [
    *KEY_COLS,
    "run_day_count",
    "run_shape_class",
    "logistic_v3_discovery_score",
    "electrical_core_minus_broadshape_050",
    "discovery_fate_class",
]
OPTIONAL_CURRENT_STATE_COLS = [
    "ae_mid_or_hi_early_day_ratio",
    "p95_recon_error",
    "max_v_drop",
    "min_mid_ratio",
]
REQUIRED_DISCOVERY_FALLBACK_COLS = [
    *KEY_COLS,
    "run_day_count",
    "run_shape_class",
    "logistic_v3_discovery_score",
    "electrical_core_minus_broadshape_050",
    *OPTIONAL_CURRENT_STATE_COLS,
]
REQUIRED_SEPARABILITY_COLS = ["record_type", "feature_name", "lhs_group", "rhs_group", "normalized_gap"]

SUMMARY_COLS = [
    "rule_family",
    "threshold_spec",
    "selected_count",
    "positive_count",
    "recurring_count",
    "isolated_count",
    "positive_capture_rate",
    "recurring_contamination_rate",
    "isolated_contamination_rate",
    "precision_minus_recurring",
    "precision_minus_all_negative",
    "note_ko",
]
CASE_COLS = [
    "rule_family",
    "threshold_spec",
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "logistic_v3_discovery_score",
    "electrical_core_minus_broadshape_050",
    "ae_mid_or_hi_early_day_ratio",
    "p95_recon_error",
    "max_v_drop",
    "min_mid_ratio",
    "discovery_fate_class",
    "split_reason_ko",
]
RECOMMENDATION_COLS = [
    "recommended_split_rule",
    "recommended_next_direction",
    "rationale_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sweep simple current-state threshold splits for the operator secondary discovery lane."
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


def fmt_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def load_fate_cases(root: Path) -> pd.DataFrame:
    path = root / "_share" / FATE_CASES_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, BASE_REQUIRED_FATE_COLS, path.name)
    df = holdout_base.normalize_key_cols(df)
    df["run_shape_class"] = df["run_shape_class"].map(holdout_base.normalize_text)
    df["discovery_fate_class"] = df["discovery_fate_class"].map(holdout_base.normalize_text)
    for col in [
        "run_day_count",
        "logistic_v3_discovery_score",
        "electrical_core_minus_broadshape_050",
        "ae_mid_or_hi_early_day_ratio",
        "p95_recon_error",
        "max_v_drop",
        "min_mid_ratio",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    missing_optional = [col for col in OPTIONAL_CURRENT_STATE_COLS if col not in df.columns]
    if missing_optional:
        discovery_path = root / "_share" / DISCOVERY_NAME
        discovery_df = holdout_base.drop_repeated_header_rows(read_csv(discovery_path))
        ensure_columns(discovery_df, REQUIRED_DISCOVERY_FALLBACK_COLS, discovery_path.name)
        discovery_df = holdout_base.normalize_key_cols(discovery_df)
        discovery_df["run_shape_class"] = discovery_df["run_shape_class"].map(holdout_base.normalize_text)
        for col in [
            "run_day_count",
            "logistic_v3_discovery_score",
            "electrical_core_minus_broadshape_050",
            *OPTIONAL_CURRENT_STATE_COLS,
        ]:
            discovery_df[col] = pd.to_numeric(discovery_df[col], errors="coerce")
        df = df.merge(
            discovery_df.loc[:, REQUIRED_DISCOVERY_FALLBACK_COLS].drop_duplicates(subset=KEY_COLS, keep="first"),
            on=KEY_COLS,
            how="left",
            suffixes=("", "__fallback"),
            validate="one_to_one",
        )
        for col in [
            "run_day_count",
            "run_shape_class",
            "logistic_v3_discovery_score",
            "electrical_core_minus_broadshape_050",
            *OPTIONAL_CURRENT_STATE_COLS,
        ]:
            fallback_col = f"{col}__fallback"
            if fallback_col not in df.columns:
                continue
            if col == "run_shape_class":
                df[col] = df[col].fillna(df[fallback_col]).map(holdout_base.normalize_text)
            else:
                df[col] = df[col].where(df[col].notna(), df[fallback_col])
            df = df.drop(columns=fallback_col)

    required_cols = [*BASE_REQUIRED_FATE_COLS, *OPTIONAL_CURRENT_STATE_COLS]
    ensure_columns(df, required_cols, path.name)
    return df.loc[:, required_cols].drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_separability_hint(root: Path) -> tuple[str, float]:
    path = root / "_share" / SEPARABILITY_SUMMARY_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_SEPARABILITY_COLS, path.name)
    df["record_type"] = df["record_type"].map(holdout_base.normalize_text)
    df["feature_name"] = df["feature_name"].map(holdout_base.normalize_text)
    df["lhs_group"] = df["lhs_group"].map(holdout_base.normalize_text)
    df["rhs_group"] = df["rhs_group"].map(holdout_base.normalize_text)
    df["normalized_gap"] = pd.to_numeric(df["normalized_gap"], errors="coerce")
    comparison_df = df.loc[
        df["record_type"].eq("comparison_summary")
        & df["lhs_group"].eq(POSITIVE_GROUP)
        & df["rhs_group"].eq("recurring_monitor_like")
        & df["feature_name"].isin(SWEEP_HINT_FEATURES)
    ].copy()
    if comparison_df.empty:
        return "", 0.0
    comparison_df["abs_gap"] = comparison_df["normalized_gap"].abs()
    best_row = comparison_df.sort_values(
        ["abs_gap", "feature_name"],
        ascending=[False, True],
        kind="stable",
    ).iloc[0]
    return str(best_row["feature_name"]), float(best_row["abs_gap"])


def rule_specs() -> list[dict[str, object]]:
    specs: list[dict[str, object]] = []
    for t in LOGISTIC_THRESHOLDS:
        specs.append(
            {
                "rule_family": "logistic_only",
                "threshold_spec": f"logistic_v3_discovery_score>={fmt_number(t)}",
                "t": t,
            }
        )
    for t in ELECTRICAL_THRESHOLDS:
        specs.append(
            {
                "rule_family": "electrical_only",
                "threshold_spec": f"electrical_core_minus_broadshape_050>={fmt_number(t)}",
                "t": t,
            }
        )
    for t in ELECTRICAL_THRESHOLDS:
        for u in AE_THRESHOLDS:
            specs.append(
                {
                    "rule_family": "electrical_and_low_ae",
                    "threshold_spec": (
                        f"electrical_core_minus_broadshape_050>={fmt_number(t)}"
                        f"|ae_mid_or_hi_early_day_ratio<={fmt_number(u)}"
                    ),
                    "t": t,
                    "u": u,
                }
            )
    for t in ELECTRICAL_THRESHOLDS:
        for u in RECON_THRESHOLDS:
            specs.append(
                {
                    "rule_family": "electrical_and_low_recon",
                    "threshold_spec": (
                        f"electrical_core_minus_broadshape_050>={fmt_number(t)}"
                        f"|p95_recon_error<={fmt_number(u)}"
                    ),
                    "t": t,
                    "u": u,
                }
            )
    for t in LOGISTIC_THRESHOLDS:
        for u in AE_THRESHOLDS:
            specs.append(
                {
                    "rule_family": "logistic_and_low_ae",
                    "threshold_spec": (
                        f"logistic_v3_discovery_score>={fmt_number(t)}"
                        f"|ae_mid_or_hi_early_day_ratio<={fmt_number(u)}"
                    ),
                    "t": t,
                    "u": u,
                }
            )
    for t in LOGISTIC_THRESHOLDS:
        for u in RECON_THRESHOLDS:
            specs.append(
                {
                    "rule_family": "logistic_and_low_recon",
                    "threshold_spec": (
                        f"logistic_v3_discovery_score>={fmt_number(t)}"
                        f"|p95_recon_error<={fmt_number(u)}"
                    ),
                    "t": t,
                    "u": u,
                }
            )
    return specs


def apply_rule(df: pd.DataFrame, spec: dict[str, object]) -> pd.Series:
    family = str(spec["rule_family"])
    t = float(spec["t"])
    if family == "logistic_only":
        return df["logistic_v3_discovery_score"].ge(t)
    if family == "electrical_only":
        return df["electrical_core_minus_broadshape_050"].ge(t)

    u = float(spec["u"])
    if family == "electrical_and_low_ae":
        return (
            df["electrical_core_minus_broadshape_050"].ge(t)
            & df["ae_mid_or_hi_early_day_ratio"].le(u)
        )
    if family == "electrical_and_low_recon":
        return (
            df["electrical_core_minus_broadshape_050"].ge(t)
            & df["p95_recon_error"].le(u)
        )
    if family == "logistic_and_low_ae":
        return (
            df["logistic_v3_discovery_score"].ge(t)
            & df["ae_mid_or_hi_early_day_ratio"].le(u)
        )
    if family == "logistic_and_low_recon":
        return (
            df["logistic_v3_discovery_score"].ge(t)
            & df["p95_recon_error"].le(u)
        )
    raise SystemExit(f"unsupported rule_family: {family}")


def safe_rate(numerator: int, denominator: int) -> float:
    return float(numerator / denominator) if denominator else 0.0


def build_split_reason(row: pd.Series, spec: dict[str, object]) -> str:
    family = str(spec["rule_family"])
    threshold_spec = str(spec["threshold_spec"])
    fate_class = holdout_base.normalize_text(row["discovery_fate_class"])
    if fate_class == POSITIVE_GROUP:
        return f"{family} rule({threshold_spec})을 통과했고 retrospective fate가 future_fault_linked라 hidden value split 후보에 해당한다."
    if fate_class == "recurring_monitor_like":
        return f"{family} rule({threshold_spec})을 통과했지만 recurring_monitor_like라 monitor contamination 사례다."
    if fate_class == "isolated_unexplained":
        return f"{family} rule({threshold_spec})을 통과했지만 isolated_unexplained라 noisy contamination 사례다."
    return f"{family} rule({threshold_spec})을 통과한 discovery row다."


def evaluate_rules(df: pd.DataFrame, hint_feature: str, hint_gap: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    analysis_df = df.loc[df["discovery_fate_class"].isin(ALLOWED_FATE_GROUPS)].copy()
    total_positive = int(analysis_df["discovery_fate_class"].eq(POSITIVE_GROUP).sum())

    summary_rows: list[dict[str, object]] = []
    case_rows: list[dict[str, object]] = []

    for spec in rule_specs():
        mask = apply_rule(analysis_df, spec).fillna(False)
        selected = analysis_df.loc[mask].copy()
        selected_count = int(len(selected))
        positive_count = int(selected["discovery_fate_class"].eq(POSITIVE_GROUP).sum()) if selected_count else 0
        recurring_count = int(selected["discovery_fate_class"].eq("recurring_monitor_like").sum()) if selected_count else 0
        isolated_count = int(selected["discovery_fate_class"].eq("isolated_unexplained").sum()) if selected_count else 0

        positive_capture_rate = safe_rate(positive_count, total_positive)
        recurring_contam = safe_rate(recurring_count, selected_count)
        isolated_contam = safe_rate(isolated_count, selected_count)
        positive_precision = safe_rate(positive_count, selected_count)
        recurring_precision = safe_rate(recurring_count, selected_count)
        all_negative_precision = safe_rate(recurring_count + isolated_count, selected_count)

        summary_rows.append(
            {
                "rule_family": spec["rule_family"],
                "threshold_spec": spec["threshold_spec"],
                "selected_count": selected_count,
                "positive_count": positive_count,
                "recurring_count": recurring_count,
                "isolated_count": isolated_count,
                "positive_capture_rate": positive_capture_rate,
                "recurring_contamination_rate": recurring_contam,
                "isolated_contamination_rate": isolated_contam,
                "precision_minus_recurring": positive_precision - recurring_precision,
                "precision_minus_all_negative": positive_precision - all_negative_precision,
                "note_ko": (
                    f"양성 capture {positive_count}/{total_positive}, recurring contamination {recurring_contam:.3f}; "
                    f"separability hint={hint_feature or 'none'}({hint_gap:.3f})"
                ),
            }
        )

        if selected_count == 0:
            continue
        selected = selected.copy()
        selected["rule_family"] = spec["rule_family"]
        selected["threshold_spec"] = spec["threshold_spec"]
        selected["split_reason_ko"] = selected.apply(build_split_reason, axis=1, spec=spec)
        case_rows.extend(selected.loc[:, CASE_COLS].to_dict("records"))

    summary_df = pd.DataFrame(summary_rows, columns=SUMMARY_COLS)
    summary_df = summary_df.sort_values(
        [
            "positive_capture_rate",
            "recurring_contamination_rate",
            "isolated_contamination_rate",
            "selected_count",
            "rule_family",
            "threshold_spec",
        ],
        ascending=[False, True, True, True, True, True],
        kind="stable",
    ).reset_index(drop=True)

    case_df = pd.DataFrame(case_rows, columns=CASE_COLS)
    if not case_df.empty:
        case_df = case_df.sort_values(
            [
                "rule_family",
                "threshold_spec",
                "logistic_v3_discovery_score",
                "electrical_core_minus_broadshape_050",
                "run_day_count",
                "site",
                "panel_id",
                "run_start_date",
                "run_end_date",
            ],
            ascending=[True, True, False, False, False, True, True, True, True],
            kind="stable",
        ).reset_index(drop=True)
    return summary_df, case_df


def build_recommendation(summary_df: pd.DataFrame, hint_feature: str, hint_gap: float) -> pd.DataFrame:
    best = summary_df.iloc[0]
    rule_name = f"{best['rule_family']}|{best['threshold_spec']}"
    capture = float(best["positive_capture_rate"])
    precision_minus_all_negative = float(best["precision_minus_all_negative"])
    recurring_contam = float(best["recurring_contamination_rate"])
    isolated_contam = float(best["isolated_contamination_rate"])

    if capture >= 0.5 and precision_minus_all_negative > 0:
        direction = "split_secondary_discovery_into_value_vs_monitor"
        rationale = (
            f"{rule_name} 규칙이 capture={capture:.3f}, recurring contamination={recurring_contam:.3f}, "
            f"isolated contamination={isolated_contam:.3f}로 가장 낫고 precision_minus_all_negative={precision_minus_all_negative:.3f} > 0이라 "
            "secondary discovery를 value vs monitor 하위 lane으로 나눠볼 근거가 있다."
        )
        if hint_feature:
            rationale += f" separability audit의 주요 gap feature는 {hint_feature}({hint_gap:.3f})였다."
    else:
        direction = "keep_secondary_discovery_as_analyst_only"
        rationale = (
            f"최선 규칙 {rule_name}도 capture={capture:.3f}, precision_minus_all_negative={precision_minus_all_negative:.3f}라 "
            "운영 split으로 쓰기엔 아직 약해 secondary discovery는 analyst-only lane으로 두는 편이 안전하다."
        )
    return pd.DataFrame(
        [
            {
                "recommended_split_rule": rule_name,
                "recommended_next_direction": direction,
                "rationale_ko": rationale,
            }
        ],
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

    fate_df = load_fate_cases(root)
    hint_feature, hint_gap = load_separability_hint(root)
    summary_df, case_df = evaluate_rules(fate_df, hint_feature, hint_gap)
    recommendation_df = build_recommendation(summary_df, hint_feature, hint_gap)
    save_outputs(root, summary_df, case_df, recommendation_df)


if __name__ == "__main__":
    main()
