#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
CASE_ERROR_REQUIRED_COLS = [
    "truth_mode",
    "prediction_mode",
    "source_split",
    "site",
    "panel_id",
    "strict_trigger_date",
    "truth_source",
    "truth_label",
    "actionability_v3",
    "derived_actionability_v3",
    "final_actionability_v3",
    "error_type",
    "prediction_source",
    "parsed_strict_method",
    "parsed_shadow_frac",
    "parsed_group_off_frac",
    "parsed_recovery_reset",
    "vendor_reply_class",
    "vendor_fault_family",
    "review_priority",
    "note",
]
SUMMARY_REQUIRED_COLS = [
    "truth_mode",
    "prediction_mode",
    "source_split",
    "f1",
    "scored_rows",
    "primary_coverage",
    "effective_coverage",
]
ACTIONABILITY_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "critical_phenotype_v3",
    "actionability_v3",
]
ONSET_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
]
VENDOR_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "vendor_reply_class",
    "vendor_fault_family",
]
CASES_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "appears_in_strict",
    "appears_in_lenient",
    "truth_source",
    "prediction_source",
    "critical_phenotype_v3",
    "actionability_v3",
    "current_actionability_v3",
    "derived_actionability_v3",
    "final_actionability_v3",
    "parsed_strict_method",
    "parsed_shadow_frac",
    "parsed_group_off_frac",
    "parsed_recovery_reset",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "gap_bucket",
    "promotion_hypothesis",
    "vendor_reply_class",
    "vendor_fault_family",
    "review_priority",
    "note",
]
PROMOTION_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "gap_bucket",
    "promotion_hypothesis",
    "parsed_strict_method",
    "parsed_shadow_frac",
    "parsed_group_off_frac",
    "parsed_recovery_reset",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "vendor_fault_family",
    "note",
]
SUMMARY_COLS = [
    "record_type",
    "total_unique_gap_cases",
    "strict_case_count",
    "lenient_case_count",
    "count_clean_confirmed_fault_review_gap",
    "count_primary_singleton_review_gap",
    "count_confounded_review_gap",
    "count_other_gap",
    "count_candidate_for_maintenance_shadow",
    "count_keep_as_review",
    "count_needs_rule_review",
    "strict_operational_f1",
    "lenient_operational_f1",
    "strict_operational_effective_coverage",
    "lenient_operational_effective_coverage",
    "gap_bucket",
    "vendor_fault_family",
    "row_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit remaining maintenance false-negative gaps after full_algorithm_f1_v3 without changing predictions."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
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


def to_float(value: object) -> float | None:
    text = normalize_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def safe_metric(numer: int | float, denom: int | float) -> float:
    if denom <= 0:
        return 0.0
    return round(float(numer / denom), 6)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def first_nonblank(series: pd.Series) -> object:
    for value in series:
        text = normalize_text(value)
        if text:
            return value
    if series.dtype.kind in {"f", "i", "u"}:
        return float("nan")
    return ""


def build_gap_bucket(row: pd.Series) -> str:
    prediction_source = normalize_text(row["prediction_source"])
    strict_method = normalize_text(row["parsed_strict_method"])
    recovery_reset = normalize_text(row["parsed_recovery_reset"])
    shadow_frac = row["parsed_shadow_frac"]
    group_off_frac = row["parsed_group_off_frac"]

    shadow_zero = shadow_frac is not None and shadow_frac == 0.0
    group_zero = group_off_frac is not None and group_off_frac == 0.0
    shadow_positive = shadow_frac is not None and shadow_frac > 0.0
    group_positive = group_off_frac is not None and group_off_frac > 0.0

    if (
        prediction_source == "confirmed_fault_clean"
        and strict_method == "confirmed_fault_flag"
        and shadow_zero
        and group_zero
        and recovery_reset == "no"
    ):
        return "clean_confirmed_fault_review_gap"
    if (
        prediction_source == "primary_actionability_v3"
        and normalize_text(row["final_actionability_v3"]) == "singleton_review"
    ):
        return "primary_singleton_review_gap"
    if (
        prediction_source == "confirmed_fault_confounded"
        or shadow_positive
        or group_positive
        or recovery_reset == "yes"
    ):
        return "confounded_review_gap"
    return "other_gap"


def build_promotion_hypothesis(gap_bucket: str) -> str:
    if gap_bucket == "clean_confirmed_fault_review_gap":
        return "candidate_for_maintenance_shadow"
    if gap_bucket in {"primary_singleton_review_gap", "confounded_review_gap"}:
        return "keep_as_review"
    return "needs_rule_review"


def aggregate_case_errors(df: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for key, group in df.groupby(KEY_COLS, dropna=False):
        truth_modes = {normalize_text(value) for value in group["truth_mode"]}
        record = {
            "site": key[0],
            "panel_id": key[1],
            "strict_trigger_date": key[2],
            "appears_in_strict": 1 if "strict" in truth_modes else 0,
            "appears_in_lenient": 1 if "lenient" in truth_modes else 0,
        }
        for col in [
            "truth_source",
            "truth_label",
            "actionability_v3",
            "derived_actionability_v3",
            "final_actionability_v3",
            "prediction_source",
            "parsed_strict_method",
            "parsed_shadow_frac",
            "parsed_group_off_frac",
            "parsed_recovery_reset",
            "vendor_reply_class",
            "vendor_fault_family",
            "review_priority",
            "note",
        ]:
            record[col] = first_nonblank(group[col])
        records.append(record)
    aggregated = pd.DataFrame(records)
    if aggregated.empty:
        return pd.DataFrame(
            columns=[
                "site",
                "panel_id",
                "strict_trigger_date",
                "appears_in_strict",
                "appears_in_lenient",
                "truth_source",
                "truth_label",
                "actionability_v3",
                "derived_actionability_v3",
                "final_actionability_v3",
                "prediction_source",
                "parsed_strict_method",
                "parsed_shadow_frac",
                "parsed_group_off_frac",
                "parsed_recovery_reset",
                "vendor_reply_class",
                "vendor_fault_family",
                "review_priority",
                "note",
            ]
        )
    aggregated["parsed_shadow_frac"] = pd.to_numeric(aggregated["parsed_shadow_frac"], errors="coerce")
    aggregated["parsed_group_off_frac"] = pd.to_numeric(aggregated["parsed_group_off_frac"], errors="coerce")
    return aggregated


def build_joined(root: Path) -> tuple[pd.DataFrame, dict[str, float]]:
    errors_df = read_csv(root / "_share" / "full_algorithm_case_errors_v3.csv")
    summary_df = read_csv(root / "_share" / "full_algorithm_f1_summary_v3.csv")
    actionability_df = read_csv(root / "_share" / "critical_actionability_shadow_v3_latest.csv")
    onset_df = read_csv(root / "_share" / "panel_onset_shadow_latest.csv")
    vendor_df = read_csv(root / "_share" / "vendor_reply_adjudication_latest.csv")

    ensure_columns(errors_df, CASE_ERROR_REQUIRED_COLS, "full_algorithm_case_errors_v3.csv")
    ensure_columns(summary_df, SUMMARY_REQUIRED_COLS, "full_algorithm_f1_summary_v3.csv")
    ensure_columns(actionability_df, ACTIONABILITY_REQUIRED_COLS, "critical_actionability_shadow_v3_latest.csv")
    ensure_columns(onset_df, ONSET_REQUIRED_COLS, "panel_onset_shadow_latest.csv")
    ensure_columns(vendor_df, VENDOR_REQUIRED_COLS, "vendor_reply_adjudication_latest.csv")

    for df in [errors_df, actionability_df, onset_df, vendor_df]:
        for col in ["site", "panel_id"]:
            df[col] = df[col].map(normalize_text)
        df["strict_trigger_date"] = df["strict_trigger_date"].map(normalize_date)

    for col in [
        "truth_mode",
        "prediction_mode",
        "source_split",
        "truth_source",
        "truth_label",
        "actionability_v3",
        "derived_actionability_v3",
        "final_actionability_v3",
        "error_type",
        "prediction_source",
        "parsed_strict_method",
        "parsed_recovery_reset",
        "vendor_reply_class",
        "vendor_fault_family",
        "review_priority",
        "note",
    ]:
        errors_df[col] = errors_df[col].map(normalize_text)
    errors_df["parsed_shadow_frac"] = pd.to_numeric(errors_df["parsed_shadow_frac"], errors="coerce")
    errors_df["parsed_group_off_frac"] = pd.to_numeric(errors_df["parsed_group_off_frac"], errors="coerce")

    fn_rows = errors_df.loc[
        errors_df["prediction_mode"].eq("maintenance")
        & errors_df["source_split"].eq("overall")
        & errors_df["error_type"].eq("fn")
    ].copy()
    aggregated = aggregate_case_errors(fn_rows)

    actionability_lookup = (
        actionability_df.loc[:, ACTIONABILITY_REQUIRED_COLS]
        .drop_duplicates(subset=KEY_COLS)
        .rename(columns={"actionability_v3": "current_actionability_v3"})
    )
    for col in ["critical_phenotype_v3", "current_actionability_v3"]:
        actionability_lookup[col] = actionability_lookup[col].map(normalize_text)

    onset_lookup = onset_df.loc[:, ONSET_REQUIRED_COLS].drop_duplicates(subset=KEY_COLS).copy()
    onset_lookup["days_earlier_than_trigger"] = pd.to_numeric(
        onset_lookup["days_earlier_than_trigger"], errors="coerce"
    )
    for col in ["onset_confidence", "onset_method"]:
        onset_lookup[col] = onset_lookup[col].map(normalize_text)

    vendor_lookup = vendor_df.loc[:, VENDOR_REQUIRED_COLS].drop_duplicates(subset=KEY_COLS).copy()
    for col in ["vendor_reply_class", "vendor_fault_family"]:
        vendor_lookup[col] = vendor_lookup[col].map(normalize_text)

    joined = aggregated.merge(actionability_lookup, on=KEY_COLS, how="left")
    joined = joined.merge(onset_lookup, on=KEY_COLS, how="left")
    joined = joined.merge(
        vendor_lookup.rename(
            columns={
                "vendor_reply_class": "vendor_reply_class_join",
                "vendor_fault_family": "vendor_fault_family_join",
            }
        ),
        on=KEY_COLS,
        how="left",
    )
    joined["critical_phenotype_v3"] = joined["critical_phenotype_v3"].fillna("").map(normalize_text)
    joined["current_actionability_v3"] = joined["current_actionability_v3"].fillna("").map(normalize_text)
    joined["onset_confidence"] = joined["onset_confidence"].fillna("").map(normalize_text)
    joined["onset_method"] = joined["onset_method"].fillna("").map(normalize_text)
    joined["days_earlier_than_trigger"] = pd.to_numeric(joined["days_earlier_than_trigger"], errors="coerce")
    joined["vendor_reply_class"] = joined.apply(
        lambda row: normalize_text(row["vendor_reply_class"])
        or normalize_text(row.get("vendor_reply_class_join", "")),
        axis=1,
    )
    joined["vendor_fault_family"] = joined.apply(
        lambda row: normalize_text(row["vendor_fault_family"])
        or normalize_text(row.get("vendor_fault_family_join", "")),
        axis=1,
    )
    joined["gap_bucket"] = joined.apply(build_gap_bucket, axis=1)
    joined["promotion_hypothesis"] = joined["gap_bucket"].map(build_promotion_hypothesis)

    summary_lookup: dict[str, float] = {}
    for truth_mode in ["strict", "lenient"]:
        row = summary_df.loc[
            summary_df["truth_mode"].map(normalize_text).eq(truth_mode)
            & summary_df["prediction_mode"].map(normalize_text).eq("operational")
            & summary_df["source_split"].map(normalize_text).eq("overall")
        ]
        if row.empty:
            summary_lookup[f"{truth_mode}_operational_f1"] = float("nan")
            summary_lookup[f"{truth_mode}_operational_effective_coverage"] = float("nan")
            continue
        first = row.iloc[0]
        summary_lookup[f"{truth_mode}_operational_f1"] = float(first["f1"])
        summary_lookup[f"{truth_mode}_operational_effective_coverage"] = float(first["effective_coverage"])

    return joined, summary_lookup


def build_summary(cases_df: pd.DataFrame, summary_lookup: dict[str, float]) -> pd.DataFrame:
    summary_row = {
        "record_type": "summary",
        "total_unique_gap_cases": int(len(cases_df)),
        "strict_case_count": int(cases_df["appears_in_strict"].sum()) if not cases_df.empty else 0,
        "lenient_case_count": int(cases_df["appears_in_lenient"].sum()) if not cases_df.empty else 0,
        "count_clean_confirmed_fault_review_gap": int(
            cases_df["gap_bucket"].eq("clean_confirmed_fault_review_gap").sum()
        )
        if not cases_df.empty
        else 0,
        "count_primary_singleton_review_gap": int(
            cases_df["gap_bucket"].eq("primary_singleton_review_gap").sum()
        )
        if not cases_df.empty
        else 0,
        "count_confounded_review_gap": int(cases_df["gap_bucket"].eq("confounded_review_gap").sum())
        if not cases_df.empty
        else 0,
        "count_other_gap": int(cases_df["gap_bucket"].eq("other_gap").sum()) if not cases_df.empty else 0,
        "count_candidate_for_maintenance_shadow": int(
            cases_df["promotion_hypothesis"].eq("candidate_for_maintenance_shadow").sum()
        )
        if not cases_df.empty
        else 0,
        "count_keep_as_review": int(cases_df["promotion_hypothesis"].eq("keep_as_review").sum())
        if not cases_df.empty
        else 0,
        "count_needs_rule_review": int(cases_df["promotion_hypothesis"].eq("needs_rule_review").sum())
        if not cases_df.empty
        else 0,
        "strict_operational_f1": summary_lookup.get("strict_operational_f1", float("nan")),
        "lenient_operational_f1": summary_lookup.get("lenient_operational_f1", float("nan")),
        "strict_operational_effective_coverage": summary_lookup.get(
            "strict_operational_effective_coverage", float("nan")
        ),
        "lenient_operational_effective_coverage": summary_lookup.get(
            "lenient_operational_effective_coverage", float("nan")
        ),
        "gap_bucket": "",
        "vendor_fault_family": "",
        "row_count": "",
    }
    rows = [summary_row]
    if not cases_df.empty:
        crosstab = (
            cases_df.groupby(["gap_bucket", "vendor_fault_family"], dropna=False)
            .size()
            .reset_index(name="row_count")
        )
        for row in crosstab.itertuples(index=False):
            rows.append(
                {
                    "record_type": "crosstab",
                    "total_unique_gap_cases": "",
                    "strict_case_count": "",
                    "lenient_case_count": "",
                    "count_clean_confirmed_fault_review_gap": "",
                    "count_primary_singleton_review_gap": "",
                    "count_confounded_review_gap": "",
                    "count_other_gap": "",
                    "count_candidate_for_maintenance_shadow": "",
                    "count_keep_as_review": "",
                    "count_needs_rule_review": "",
                    "strict_operational_f1": "",
                    "lenient_operational_f1": "",
                    "strict_operational_effective_coverage": "",
                    "lenient_operational_effective_coverage": "",
                    "gap_bucket": normalize_text(row.gap_bucket),
                    "vendor_fault_family": normalize_text(row.vendor_fault_family),
                    "row_count": int(row.row_count),
                }
            )
    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"

    cases_df, summary_lookup = build_joined(root)
    summary_df = build_summary(cases_df, summary_lookup)
    promotion_df = cases_df.loc[
        cases_df["promotion_hypothesis"].eq("candidate_for_maintenance_shadow"), PROMOTION_COLS
    ].copy()

    cases_df.loc[:, CASES_COLS].to_csv(
        share_dir / "maintenance_gap_audit_cases_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    summary_df.to_csv(
        share_dir / "maintenance_gap_audit_summary_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    promotion_df.to_csv(
        share_dir / "maintenance_gap_promotion_candidates_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    print(f"maintenance_gap_audit_rows_v1={len(cases_df)}")


if __name__ == "__main__":
    main()
