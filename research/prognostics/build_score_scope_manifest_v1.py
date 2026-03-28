#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
MANUAL_SCORED_VALUES = {"true_positive", "group_side", "false_positive"}
LENIENT_VENDOR_SCORED_VALUES = {
    "field_confirmed_positive",
    "vendor_pattern_positive",
    "vendor_likely_positive",
    "vendor_rejected",
}
STRICT_VENDOR_SCORED_VALUES = {
    "field_confirmed_positive",
    "vendor_pattern_positive",
    "vendor_rejected",
}
CASE_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "manual_truth_present_flag",
    "vendor_truth_present_flag",
    "official_scored_flag",
    "scope_class",
    "review_priority_bucket",
    "priority_score",
    "recommended_review_action",
    "critical_phenotype_v3",
    "actionability_v3",
    "vendor_reply_class",
    "vendor_fault_family",
    "in_truth_review_batch_v1_flag",
]
SITE_COLS = [
    "site",
    "total_cases",
    "official_scored_count",
    "manual_scored_count",
    "vendor_scored_count",
    "deferred_unlabeled_high_actionability_count",
    "deferred_unlabeled_other_count",
    "recommended_site_handling",
]
SUMMARY_COLS = [
    "record_type",
    "total_strict_cases",
    "official_scored_count",
    "manual_scored_count",
    "vendor_scored_count",
    "deferred_unlabeled_high_actionability_count",
    "deferred_unlabeled_other_count",
    "excluded_labeled_needs_more_info_count",
    "excluded_vendor_no_info_count",
    "excluded_other_count",
    "site",
    "total_cases",
]
VALID_SCOPE_CLASSES = {
    "manual_scored",
    "vendor_scored",
    "deferred_unlabeled_high_actionability",
    "deferred_unlabeled_other",
    "excluded_labeled_needs_more_info",
    "excluded_vendor_no_info",
    "excluded_other",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Make current full-algorithm scoring scope explicit without changing official evaluation logic."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    parser.add_argument(
        "--sites",
        nargs="*",
        default=SITES,
        help="Sites to include. Defaults to the stable known sites.",
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


def first_nonblank(series: pd.Series) -> object:
    for value in series.tolist():
        if normalize_text(value):
            return value
    if series.dtype.kind in {"f", "i", "u"}:
        return float("nan")
    return ""


def dedupe(df: pd.DataFrame, name: str, cols: list[str]) -> pd.DataFrame:
    dupes = df.loc[df.duplicated(subset=cols, keep=False), cols]
    if not dupes.empty:
        raise SystemExit(f"{name} has duplicate rows on {cols}")
    return df


def coalesce_text(left: object, right: object) -> str:
    left_text = normalize_text(left)
    if left_text:
        return left_text
    return normalize_text(right)


def drop_embedded_header_rows(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    if any(col not in df.columns for col in cols):
        return df
    header_mask = pd.Series(True, index=df.index)
    for col in cols:
        header_mask &= df[col].map(normalize_text).eq(col)
    if not bool(header_mask.any()):
        return df
    return df.loc[~header_mask].copy()


def manual_truth_label(candidate_validity: object) -> str:
    value = normalize_text(candidate_validity)
    if value in {"true_positive", "group_side"}:
        return "positive"
    if value == "false_positive":
        return "negative"
    return "exclude"


def vendor_truth_label(vendor_reply_class: object, truth_mode: str) -> str:
    value = normalize_text(vendor_reply_class)
    if truth_mode == "strict":
        if value in STRICT_VENDOR_SCORED_VALUES - {"vendor_rejected"}:
            return "positive"
        if value == "vendor_rejected":
            return "negative"
        return "exclude"
    if truth_mode == "lenient":
        if value in LENIENT_VENDOR_SCORED_VALUES - {"vendor_rejected"}:
            return "positive"
        if value == "vendor_rejected":
            return "negative"
        return "exclude"
    raise ValueError(truth_mode)


def hybrid_truth_label(candidate_validity: object, vendor_reply_class: object, truth_mode: str) -> str:
    candidate_value = normalize_text(candidate_validity)
    if candidate_value:
        return manual_truth_label(candidate_value)
    vendor_value = normalize_text(vendor_reply_class)
    if vendor_value:
        return vendor_truth_label(vendor_value, truth_mode)
    return "exclude"


def build_scope_class(row: pd.Series) -> str:
    candidate_validity = normalize_text(row["candidate_validity"])
    vendor_reply_class = normalize_text(row["vendor_reply_class"])
    review_priority_bucket = normalize_text(row["review_priority_bucket"])
    manual_truth_present_flag = int(row["manual_truth_present_flag"])
    vendor_truth_present_flag = int(row["vendor_truth_present_flag"])

    if manual_truth_present_flag == 1 and candidate_validity in MANUAL_SCORED_VALUES:
        return "manual_scored"
    if (
        manual_truth_present_flag == 0
        and vendor_truth_present_flag == 1
        and vendor_reply_class in LENIENT_VENDOR_SCORED_VALUES
    ):
        return "vendor_scored"
    if (
        manual_truth_present_flag == 0
        and vendor_truth_present_flag == 0
        and review_priority_bucket == "high_actionability_unlabeled"
    ):
        return "deferred_unlabeled_high_actionability"
    if manual_truth_present_flag == 0 and vendor_truth_present_flag == 0:
        return "deferred_unlabeled_other"
    if candidate_validity == "needs_more_info":
        return "excluded_labeled_needs_more_info"
    if manual_truth_present_flag == 0 and vendor_reply_class == "vendor_no_info":
        return "excluded_vendor_no_info"
    return "excluded_other"


def count_scope(case_output: pd.DataFrame, scope_class: str, site: str | None = None) -> int:
    subset = case_output
    if site is not None:
        subset = subset.loc[subset["site"].eq(site)]
    return int(subset["scope_class"].eq(scope_class).sum())


def summarize_sites(case_output: pd.DataFrame, sites: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for site in sites:
        site_df = case_output.loc[case_output["site"].eq(site)].copy()
        official_scored_count = int(site_df["official_scored_flag"].eq(1).sum())
        deferred_high_count = count_scope(case_output, "deferred_unlabeled_high_actionability", site=site)
        if deferred_high_count > 0 and official_scored_count > 0:
            recommended = "score_with_deferred_note"
        elif deferred_high_count > 0 and official_scored_count == 0:
            recommended = "do_not_drop_site_only_defer_rows"
        else:
            recommended = "continue_scoring_normally"

        rows.append(
            {
                "site": site,
                "total_cases": int(len(site_df)),
                "official_scored_count": official_scored_count,
                "manual_scored_count": count_scope(case_output, "manual_scored", site=site),
                "vendor_scored_count": count_scope(case_output, "vendor_scored", site=site),
                "deferred_unlabeled_high_actionability_count": deferred_high_count,
                "deferred_unlabeled_other_count": count_scope(case_output, "deferred_unlabeled_other", site=site),
                "recommended_site_handling": recommended,
            }
        )
    return pd.DataFrame(rows, columns=SITE_COLS)


def summarize_overall(case_output: pd.DataFrame, site_output: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "record_type": "summary",
            "total_strict_cases": int(len(case_output)),
            "official_scored_count": int(case_output["official_scored_flag"].eq(1).sum()),
            "manual_scored_count": count_scope(case_output, "manual_scored"),
            "vendor_scored_count": count_scope(case_output, "vendor_scored"),
            "deferred_unlabeled_high_actionability_count": count_scope(
                case_output, "deferred_unlabeled_high_actionability"
            ),
            "deferred_unlabeled_other_count": count_scope(case_output, "deferred_unlabeled_other"),
            "excluded_labeled_needs_more_info_count": count_scope(
                case_output, "excluded_labeled_needs_more_info"
            ),
            "excluded_vendor_no_info_count": count_scope(case_output, "excluded_vendor_no_info"),
            "excluded_other_count": count_scope(case_output, "excluded_other"),
            "site": "",
            "total_cases": int(len(case_output)),
        }
    ]

    for row in site_output.to_dict(orient="records"):
        rows.append(
            {
                "record_type": "site",
                "total_strict_cases": pd.NA,
                "official_scored_count": row["official_scored_count"],
                "manual_scored_count": row["manual_scored_count"],
                "vendor_scored_count": row["vendor_scored_count"],
                "deferred_unlabeled_high_actionability_count": row[
                    "deferred_unlabeled_high_actionability_count"
                ],
                "deferred_unlabeled_other_count": row["deferred_unlabeled_other_count"],
                "excluded_labeled_needs_more_info_count": pd.NA,
                "excluded_vendor_no_info_count": pd.NA,
                "excluded_other_count": pd.NA,
                "site": row["site"],
                "total_cases": row["total_cases"],
            }
        )

    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def validate_official_summary(case_output: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    ensure_columns(
        summary_df,
        ["truth_mode", "prediction_mode", "source_split", "scored_rows", "excluded_rows"],
        "full_algorithm_f1_summary_v3.csv",
    )
    summary_df = summary_df.copy()
    for col in ["truth_mode", "prediction_mode", "source_split"]:
        summary_df[col] = summary_df[col].map(normalize_text)
    for col in ["scored_rows", "excluded_rows"]:
        summary_df[col] = pd.to_numeric(summary_df[col], errors="coerce")

    def expected_count(truth_mode: str, field: str) -> int:
        subset = summary_df.loc[
            summary_df["source_split"].eq("overall") & summary_df["truth_mode"].eq(truth_mode),
            ["prediction_mode", field],
        ].copy()
        if subset.empty:
            raise SystemExit(f"full_algorithm_f1_summary_v3.csv missing overall rows for truth_mode={truth_mode}")
        values = {int(value) for value in subset[field].dropna().tolist()}
        if len(values) != 1:
            raise SystemExit(
                f"full_algorithm_f1_summary_v3.csv has inconsistent {field} values for truth_mode={truth_mode}"
            )
        return int(next(iter(values)))

    strict_expected = expected_count("strict", "scored_rows")
    strict_excluded_expected = expected_count("strict", "excluded_rows")
    lenient_expected = expected_count("lenient", "scored_rows")
    lenient_excluded_expected = expected_count("lenient", "excluded_rows")

    strict_actual = int(case_output["strict_truth_scored_flag"].eq(1).sum())
    lenient_actual = int(case_output["official_scored_flag"].eq(1).sum())
    strict_excluded_actual = int(case_output["strict_truth_scored_flag"].eq(0).sum())
    lenient_excluded_actual = int(case_output["official_scored_flag"].eq(0).sum())

    if strict_actual != strict_expected:
        raise SystemExit(
            f"strict scored scope mismatch: manifest={strict_actual}, full_algorithm_f1_summary_v3={strict_expected}"
        )
    if lenient_actual != lenient_expected:
        raise SystemExit(
            f"lenient scored scope mismatch: manifest={lenient_actual}, full_algorithm_f1_summary_v3={lenient_expected}"
        )
    if strict_excluded_actual != strict_excluded_expected:
        raise SystemExit(
            "strict excluded scope mismatch: "
            f"manifest={strict_excluded_actual}, full_algorithm_f1_summary_v3={strict_excluded_expected}"
        )
    if lenient_excluded_actual != lenient_excluded_expected:
        raise SystemExit(
            "lenient excluded scope mismatch: "
            f"manifest={lenient_excluded_actual}, full_algorithm_f1_summary_v3={lenient_excluded_expected}"
        )


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base_df = drop_embedded_header_rows(read_csv(root / "_share" / "panel_date_reaudit_working.csv"), KEY_COLS)
    vendor_df = drop_embedded_header_rows(read_csv(root / "_share" / "vendor_reply_adjudication_latest.csv"), KEY_COLS)
    priority_df = drop_embedded_header_rows(read_csv(root / "_share" / "truth_coverage_priority_cases_v1.csv"), KEY_COLS)
    summary_df = drop_embedded_header_rows(read_csv(root / "_share" / "full_algorithm_f1_summary_v3.csv"), ["truth_mode"])
    batch_df = drop_embedded_header_rows(read_csv(root / "_share" / "truth_review_batch_v1.csv"), KEY_COLS)

    ensure_columns(base_df, [*KEY_COLS, "candidate_validity"], "panel_date_reaudit_working.csv")
    ensure_columns(vendor_df, KEY_COLS, "vendor_reply_adjudication_latest.csv")
    ensure_columns(priority_df, KEY_COLS, "truth_coverage_priority_cases_v1.csv")
    ensure_columns(batch_df, KEY_COLS, "truth_review_batch_v1.csv")

    for df in [base_df, vendor_df, priority_df, batch_df]:
        df["site"] = df["site"].map(normalize_text)
        df["panel_id"] = df["panel_id"].map(normalize_text)
        df["strict_trigger_date"] = df["strict_trigger_date"].map(normalize_date)

    base_df = base_df.loc[base_df["site"].isin(sites)].copy()
    if base_df.empty:
        raise SystemExit("panel_date_reaudit_working.csv produced an empty strict-case universe")

    for col in ["candidate_validity", "vendor_reply_class", "vendor_fault_family"]:
        if col not in base_df.columns:
            base_df[col] = ""
        base_df[col] = base_df[col].map(normalize_text)

    base_unique = dedupe(
        base_df.loc[:, [*KEY_COLS, "candidate_validity", "vendor_reply_class", "vendor_fault_family"]],
        "panel_date_reaudit_working.csv",
        KEY_COLS,
    )

    for col in ["vendor_reply_class", "vendor_fault_family"]:
        if col not in vendor_df.columns:
            vendor_df[col] = ""
        vendor_df[col] = vendor_df[col].map(normalize_text)
    vendor_unique = (
        vendor_df.loc[:, [*KEY_COLS, "vendor_reply_class", "vendor_fault_family"]]
        .groupby(KEY_COLS, as_index=False)
        .agg(
            vendor_reply_class=("vendor_reply_class", first_nonblank),
            vendor_fault_family=("vendor_fault_family", first_nonblank),
        )
    ).rename(
        columns={
            "vendor_reply_class": "vendor_reply_class_vendor",
            "vendor_fault_family": "vendor_fault_family_vendor",
        }
    )

    priority_cols = [
        "review_priority_bucket",
        "priority_score",
        "recommended_review_action",
        "critical_phenotype_v3",
        "actionability_v3",
    ]
    for col in priority_cols:
        if col not in priority_df.columns:
            priority_df[col] = ""
    text_priority_cols = [
        "review_priority_bucket",
        "recommended_review_action",
        "critical_phenotype_v3",
        "actionability_v3",
    ]
    for col in text_priority_cols:
        priority_df[col] = priority_df[col].map(normalize_text)
    priority_df["priority_score"] = pd.to_numeric(priority_df["priority_score"], errors="coerce")
    priority_unique = (
        priority_df.loc[:, [*KEY_COLS, *priority_cols]]
        .groupby(KEY_COLS, as_index=False)
        .agg(
            review_priority_bucket=("review_priority_bucket", first_nonblank),
            priority_score=("priority_score", "max"),
            recommended_review_action=("recommended_review_action", first_nonblank),
            critical_phenotype_v3=("critical_phenotype_v3", first_nonblank),
            actionability_v3=("actionability_v3", first_nonblank),
        )
    )

    batch_keys = dedupe(
        batch_df.loc[:, KEY_COLS].drop_duplicates().assign(in_truth_review_batch_v1_flag=1),
        "truth_review_batch_v1.csv",
        KEY_COLS,
    )

    case_output = (
        base_unique
        .merge(vendor_unique, on=KEY_COLS, how="left")
        .merge(priority_unique, on=KEY_COLS, how="left")
        .merge(batch_keys, on=KEY_COLS, how="left")
    )

    case_output["vendor_reply_class"] = case_output.apply(
        lambda row: coalesce_text(row["vendor_reply_class"], row.get("vendor_reply_class_vendor", "")),
        axis=1,
    )
    case_output["vendor_fault_family"] = case_output.apply(
        lambda row: coalesce_text(row["vendor_fault_family"], row.get("vendor_fault_family_vendor", "")),
        axis=1,
    )

    for col in ["review_priority_bucket", "recommended_review_action", "critical_phenotype_v3", "actionability_v3"]:
        if col not in case_output.columns:
            case_output[col] = ""
        case_output[col] = case_output[col].fillna("").map(normalize_text)
    if "priority_score" not in case_output.columns:
        case_output["priority_score"] = 0
    case_output["priority_score"] = pd.to_numeric(case_output["priority_score"], errors="coerce")
    case_output["priority_score"] = case_output["priority_score"].fillna(0).astype(int)
    if "in_truth_review_batch_v1_flag" not in case_output.columns:
        case_output["in_truth_review_batch_v1_flag"] = 0
    case_output["in_truth_review_batch_v1_flag"] = pd.to_numeric(
        case_output["in_truth_review_batch_v1_flag"], errors="coerce"
    ).fillna(0).astype(int)

    case_output["manual_truth_present_flag"] = case_output["candidate_validity"].map(
        lambda value: 1 if normalize_text(value) else 0
    )
    case_output["vendor_truth_present_flag"] = case_output["vendor_reply_class"].map(
        lambda value: 1 if normalize_text(value) else 0
    )
    case_output["strict_truth_scored_flag"] = case_output.apply(
        lambda row: 1 if hybrid_truth_label(row["candidate_validity"], row["vendor_reply_class"], "strict") != "exclude" else 0,
        axis=1,
    )
    case_output["official_scored_flag"] = case_output.apply(
        lambda row: 1 if hybrid_truth_label(row["candidate_validity"], row["vendor_reply_class"], "lenient") != "exclude" else 0,
        axis=1,
    )
    case_output["scope_class"] = case_output.apply(build_scope_class, axis=1)

    invalid_scope = sorted(set(case_output["scope_class"]) - VALID_SCOPE_CLASSES)
    if invalid_scope:
        raise SystemExit(f"invalid scope_class values: {invalid_scope}")

    expected_official_flag = case_output["scope_class"].isin({"manual_scored", "vendor_scored"}).astype(int)
    if not bool(case_output["official_scored_flag"].eq(expected_official_flag).all()):
        raise SystemExit("official_scored_flag does not match scope classification")

    validate_official_summary(case_output, summary_df)

    site_rank = {site: idx for idx, site in enumerate(sites)}
    case_output["_site_rank"] = case_output["site"].map(lambda value: site_rank.get(value, len(site_rank)))
    case_output = case_output.sort_values(
        ["_site_rank", "strict_trigger_date", "panel_id"],
        ascending=[True, True, True],
    ).reset_index(drop=True)

    site_output = summarize_sites(case_output, sites)
    summary_output = summarize_overall(case_output, site_output)

    case_output = case_output.loc[:, CASE_COLS]
    site_output = site_output.loc[:, SITE_COLS]
    summary_output = summary_output.loc[:, SUMMARY_COLS]
    return summary_output, site_output, case_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_output, site_output, case_output = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_output.to_csv(out_dir / "score_scope_manifest_summary_v1.csv", index=False, encoding="utf-8-sig")
    site_output.to_csv(out_dir / "score_scope_manifest_sites_v1.csv", index=False, encoding="utf-8-sig")
    case_output.to_csv(out_dir / "score_scope_manifest_cases_v1.csv", index=False, encoding="utf-8-sig")
    print(f"score_scope_manifest_cases_v1={len(case_output)}")


if __name__ == "__main__":
    main()
