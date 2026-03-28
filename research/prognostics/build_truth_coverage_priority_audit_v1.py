#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
PRIORITY_BASE_SCORES = {
    "urgent_official_error_context": 100,
    "maintenance_definition_gap": 80,
    "vendor_backed_unlabeled": 70,
    "high_actionability_unlabeled": 60,
    "precursor_note_context": 50,
    "monitor_only_backlog": 30,
    "already_labeled": 0,
}
CASE_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "manual_truth_present_flag",
    "candidate_validity",
    "manual_truth_label_if_present",
    "vendor_reply_class",
    "vendor_fault_family",
    "critical_phenotype_v3",
    "actionability_v3",
    "in_official_error_context_flag",
    "official_error_modes",
    "official_error_types",
    "prediction_source",
    "in_maintenance_gap_flag",
    "gap_bucket",
    "promotion_hypothesis",
    "in_site_specific_precursor_note_context_flag",
    "review_priority_bucket",
    "priority_score",
    "recommended_review_action",
    "review_priority",
    "note",
    "vendor_note",
]
SITE_QUEUE_COLS = [
    "site",
    "review_priority_bucket",
    "case_count",
    "top_priority_score",
    "example_panel_ids",
]
SUMMARY_COLS = [
    "record_type",
    "total_strict_cases",
    "manual_truth_present_count",
    "manual_truth_missing_count",
    "urgent_official_error_context_count",
    "maintenance_definition_gap_count",
    "vendor_backed_unlabeled_count",
    "high_actionability_unlabeled_count",
    "precursor_note_context_count",
    "monitor_only_backlog_count",
    "site",
    "total_cases",
    "highest_priority_bucket",
    "highest_priority_bucket_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prioritize manual truth collection across the full strict-case universe."
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
        help="Sites to include. Defaults to stable known sites.",
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


def first_nonblank(series: pd.Series) -> object:
    for value in series.tolist():
        if normalize_text(value):
            return value
    if series.dtype.kind in {"f", "i", "u"}:
        return float("nan")
    return ""


def map_manual_truth_label(candidate_validity: object) -> str:
    value = normalize_text(candidate_validity)
    if value in {"true_positive", "group_side"}:
        return "positive"
    if value == "false_positive":
        return "negative"
    if value == "needs_more_info":
        return "exclude"
    return ""


def aggregate_official_errors(errors_df: pd.DataFrame) -> pd.DataFrame:
    if errors_df.empty:
        return pd.DataFrame(
            columns=[
                *KEY_COLS,
                "in_official_error_context_flag",
                "official_error_modes",
                "official_error_types",
                "prediction_source",
            ]
        )

    filtered = errors_df.loc[errors_df["source_split"].map(normalize_text).eq("overall")].copy()
    if filtered.empty:
        return pd.DataFrame(
            columns=[
                *KEY_COLS,
                "in_official_error_context_flag",
                "official_error_modes",
                "official_error_types",
                "prediction_source",
            ]
        )

    rows: list[dict[str, object]] = []
    for key, group in filtered.groupby(KEY_COLS, dropna=False):
        mode_values = sorted(
            {
                f"{normalize_text(truth_mode)}:{normalize_text(pred_mode)}"
                for truth_mode, pred_mode in zip(group["truth_mode"], group["prediction_mode"])
                if normalize_text(truth_mode) or normalize_text(pred_mode)
            }
        )
        type_values = sorted({normalize_text(value) for value in group["error_type"] if normalize_text(value)})
        prediction_values = sorted(
            {normalize_text(value) for value in group.get("prediction_source", pd.Series(dtype=object)) if normalize_text(value)}
        )
        rows.append(
            {
                "site": key[0],
                "panel_id": key[1],
                "strict_trigger_date": key[2],
                "in_official_error_context_flag": 1,
                "official_error_modes": "|".join(mode_values),
                "official_error_types": "|".join(type_values),
                "prediction_source": "|".join(prediction_values),
            }
        )
    return pd.DataFrame(rows)


def aggregate_maintenance_gap(gap_df: pd.DataFrame) -> pd.DataFrame:
    if gap_df.empty:
        return pd.DataFrame(columns=[*KEY_COLS, "in_maintenance_gap_flag", "gap_bucket", "promotion_hypothesis"])

    rows: list[dict[str, object]] = []
    for key, group in gap_df.groupby(KEY_COLS, dropna=False):
        rows.append(
            {
                "site": key[0],
                "panel_id": key[1],
                "strict_trigger_date": key[2],
                "in_maintenance_gap_flag": 1,
                "gap_bucket": first_nonblank(group["gap_bucket"]),
                "promotion_hypothesis": first_nonblank(group["promotion_hypothesis"]),
            }
        )
    return pd.DataFrame(rows)


def aggregate_precursor_context(precursor_cases: pd.DataFrame) -> pd.DataFrame:
    if precursor_cases.empty:
        return pd.DataFrame(columns=["site", "strict_trigger_date", "in_site_specific_precursor_note_context_flag"])

    precursor_cases["site"] = precursor_cases["site"].map(normalize_text)
    precursor_cases["date"] = precursor_cases["date"].map(normalize_date)
    precursor_cases["include_in_site_specific_note_flag"] = pd.to_numeric(
        precursor_cases["include_in_site_specific_note_flag"], errors="coerce"
    ).fillna(0).astype(int)

    aggregated = (
        precursor_cases.groupby(["site", "date"], as_index=False)
        .agg(in_site_specific_precursor_note_context_flag=("include_in_site_specific_note_flag", "max"))
        .rename(columns={"date": "strict_trigger_date"})
    )
    return aggregated


def build_review_priority_bucket(row: pd.Series) -> str:
    manual_truth_present_flag = int(row["manual_truth_present_flag"])
    vendor_reply_class = normalize_text(row["vendor_reply_class"])
    actionability = normalize_text(row["actionability_v3"])
    promotion_hypothesis = normalize_text(row["promotion_hypothesis"])

    if manual_truth_present_flag == 1:
        return "already_labeled"
    if int(row["in_official_error_context_flag"]) == 1:
        return "urgent_official_error_context"
    if (
        int(row["in_maintenance_gap_flag"]) == 1
        and promotion_hypothesis in {"candidate_for_maintenance_shadow", "keep_as_review"}
    ):
        return "maintenance_definition_gap"
    if vendor_reply_class:
        return "vendor_backed_unlabeled"
    if actionability in {"maintenance_candidate", "common_cause_review", "singleton_review"}:
        return "high_actionability_unlabeled"
    if int(row["in_site_specific_precursor_note_context_flag"]) == 1:
        return "precursor_note_context"
    return "monitor_only_backlog"


def build_priority_score(row: pd.Series) -> int:
    bucket = normalize_text(row["review_priority_bucket"])
    vendor_reply_class = normalize_text(row["vendor_reply_class"])
    actionability = normalize_text(row["actionability_v3"])
    score = PRIORITY_BASE_SCORES.get(bucket, 0)
    if vendor_reply_class == "field_confirmed_positive":
        score += 5
    if vendor_reply_class == "vendor_pattern_positive":
        score += 3
    if actionability == "maintenance_candidate":
        score += 2
    if actionability in {"common_cause_review", "singleton_review"}:
        score += 1
    return int(score)


def build_recommended_review_action(bucket: str) -> str:
    if bucket == "already_labeled":
        return "no_action_needed"
    if bucket == "urgent_official_error_context":
        return "manual_reaudit_first"
    if bucket == "maintenance_definition_gap":
        return "inspect_actionability_definition"
    if bucket == "vendor_backed_unlabeled":
        return "compare_with_vendor_and_field_logs"
    if bucket == "high_actionability_unlabeled":
        return "manual_reaudit_first"
    if bucket == "precursor_note_context":
        return "compare_with_vendor_and_field_logs"
    return "defer_until_backlog_review"


def build_site_queue(case_output: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (site, bucket), group in case_output.groupby(["site", "review_priority_bucket"], dropna=False):
        ranked = group.sort_values(["priority_score", "panel_id"], ascending=[False, True]).reset_index(drop=True)
        example_ids = "|".join(ranked["panel_id"].map(normalize_text).drop_duplicates().head(3).tolist())
        rows.append(
            {
                "site": site,
                "review_priority_bucket": bucket,
                "case_count": int(len(group)),
                "top_priority_score": int(group["priority_score"].max()),
                "example_panel_ids": example_ids,
            }
        )
    queue = pd.DataFrame(rows, columns=SITE_QUEUE_COLS)
    if queue.empty:
        return queue
    return queue.sort_values(
        ["site", "top_priority_score", "case_count", "review_priority_bucket"],
        ascending=[True, False, False, True],
    ).reset_index(drop=True)


def build_summary(case_output: pd.DataFrame, sites: list[str]) -> pd.DataFrame:
    def count_bucket(label: str) -> int:
        return int(case_output["review_priority_bucket"].eq(label).sum())

    summary_rows = [
        {
            "record_type": "summary",
            "total_strict_cases": int(len(case_output)),
            "manual_truth_present_count": int(case_output["manual_truth_present_flag"].eq(1).sum()),
            "manual_truth_missing_count": int(case_output["manual_truth_present_flag"].eq(0).sum()),
            "urgent_official_error_context_count": count_bucket("urgent_official_error_context"),
            "maintenance_definition_gap_count": count_bucket("maintenance_definition_gap"),
            "vendor_backed_unlabeled_count": count_bucket("vendor_backed_unlabeled"),
            "high_actionability_unlabeled_count": count_bucket("high_actionability_unlabeled"),
            "precursor_note_context_count": count_bucket("precursor_note_context"),
            "monitor_only_backlog_count": count_bucket("monitor_only_backlog"),
            "site": "",
            "total_cases": pd.NA,
            "highest_priority_bucket": "",
            "highest_priority_bucket_count": pd.NA,
        }
    ]

    for site in sites:
        site_df = case_output.loc[case_output["site"].eq(site)].copy()
        if site_df.empty:
            highest_bucket = ""
            highest_count = 0
        else:
            bucket_rank = (
                site_df.groupby("review_priority_bucket", as_index=False)
                .agg(top_priority_score=("priority_score", "max"), bucket_case_count=("panel_id", "size"))
                .sort_values(["top_priority_score", "bucket_case_count", "review_priority_bucket"], ascending=[False, False, True])
                .reset_index(drop=True)
            )
            highest_bucket = normalize_text(bucket_rank.iloc[0]["review_priority_bucket"])
            highest_count = int(bucket_rank.iloc[0]["bucket_case_count"])

        summary_rows.append(
            {
                "record_type": "site",
                "total_strict_cases": pd.NA,
                "manual_truth_present_count": int(site_df["manual_truth_present_flag"].eq(1).sum()),
                "manual_truth_missing_count": int(site_df["manual_truth_present_flag"].eq(0).sum()),
                "urgent_official_error_context_count": pd.NA,
                "maintenance_definition_gap_count": pd.NA,
                "vendor_backed_unlabeled_count": pd.NA,
                "high_actionability_unlabeled_count": pd.NA,
                "precursor_note_context_count": pd.NA,
                "monitor_only_backlog_count": pd.NA,
                "site": site,
                "total_cases": int(len(site_df)),
                "highest_priority_bucket": highest_bucket,
                "highest_priority_bucket_count": highest_count,
            }
        )

    return pd.DataFrame(summary_rows, columns=SUMMARY_COLS)


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base_df = read_csv(root / "_share" / "panel_date_reaudit_working.csv")
    vendor_df = read_csv(root / "_share" / "vendor_reply_adjudication_latest.csv")
    actionability_df = read_csv(root / "_share" / "critical_actionability_shadow_v3_latest.csv")
    errors_df = read_csv(root / "_share" / "full_algorithm_case_errors_v3.csv")
    maintenance_gap_df = read_csv(root / "_share" / "maintenance_gap_audit_cases_v1.csv")
    precursor_cases_df = read_csv(root / "_share" / "common_cause_precursor_decision_cases_v1.csv")

    site_context_path = root / "_share" / "common_cause_precursor_decision_sites_v1.csv"
    if site_context_path.exists():
        _site_context_df = read_csv(site_context_path)

    for df in [base_df, vendor_df, actionability_df, errors_df, maintenance_gap_df]:
        df["site"] = df["site"].map(normalize_text)
        df["panel_id"] = df["panel_id"].map(normalize_text)
        df["strict_trigger_date"] = df["strict_trigger_date"].map(normalize_date)

    base_df = base_df.loc[base_df["site"].isin(sites)].copy()
    if base_df.empty:
        raise SystemExit("panel_date_reaudit_working.csv produced an empty strict-case universe")

    for col in ["candidate_validity", "review_priority", "note"]:
        if col not in base_df.columns:
            base_df[col] = ""
        base_df[col] = base_df[col].map(normalize_text)

    base_output = (
        base_df.loc[:, ["site", "panel_id", "strict_trigger_date", "candidate_validity", "review_priority", "note"]]
        .groupby(KEY_COLS, as_index=False)
        .agg(
            candidate_validity=("candidate_validity", first_nonblank),
            review_priority=("review_priority", first_nonblank),
            note=("note", first_nonblank),
        )
    )
    base_output["manual_truth_present_flag"] = base_output["candidate_validity"].map(lambda value: 1 if normalize_text(value) else 0)
    base_output["manual_truth_label_if_present"] = base_output["candidate_validity"].map(map_manual_truth_label)

    vendor_cols = ["site", "panel_id", "strict_trigger_date", "vendor_reply_class", "vendor_fault_family", "vendor_note"]
    for col in ["vendor_reply_class", "vendor_fault_family", "vendor_note"]:
        if col not in vendor_df.columns:
            vendor_df[col] = ""
        vendor_df[col] = vendor_df[col].map(normalize_text)
    vendor_df = (
        vendor_df.loc[:, vendor_cols]
        .groupby(KEY_COLS, as_index=False)
        .agg(
            vendor_reply_class=("vendor_reply_class", first_nonblank),
            vendor_fault_family=("vendor_fault_family", first_nonblank),
            vendor_note=("vendor_note", first_nonblank),
        )
    )

    for col in ["critical_phenotype_v3", "actionability_v3"]:
        if col not in actionability_df.columns:
            actionability_df[col] = ""
        actionability_df[col] = actionability_df[col].map(normalize_text)
    actionability_df = (
        actionability_df.loc[:, ["site", "panel_id", "strict_trigger_date", "critical_phenotype_v3", "actionability_v3"]]
        .groupby(KEY_COLS, as_index=False)
        .agg(
            critical_phenotype_v3=("critical_phenotype_v3", first_nonblank),
            actionability_v3=("actionability_v3", first_nonblank),
        )
    )

    official_errors = aggregate_official_errors(errors_df)
    maintenance_gap = aggregate_maintenance_gap(maintenance_gap_df)
    precursor_context = aggregate_precursor_context(precursor_cases_df)

    case_output = (
        base_output
        .merge(vendor_df, on=KEY_COLS, how="left")
        .merge(actionability_df, on=KEY_COLS, how="left")
        .merge(official_errors, on=KEY_COLS, how="left")
        .merge(maintenance_gap, on=KEY_COLS, how="left")
        .merge(precursor_context, on=["site", "strict_trigger_date"], how="left")
    )

    fill_text_cols = [
        "vendor_reply_class",
        "vendor_fault_family",
        "vendor_note",
        "critical_phenotype_v3",
        "actionability_v3",
        "official_error_modes",
        "official_error_types",
        "prediction_source",
        "gap_bucket",
        "promotion_hypothesis",
    ]
    for col in fill_text_cols:
        if col not in case_output.columns:
            case_output[col] = ""
        case_output[col] = case_output[col].map(normalize_text)

    for col in [
        "in_official_error_context_flag",
        "in_maintenance_gap_flag",
        "in_site_specific_precursor_note_context_flag",
    ]:
        if col not in case_output.columns:
            case_output[col] = 0
        case_output[col] = pd.to_numeric(case_output[col], errors="coerce").fillna(0).astype(int)

    case_output["review_priority_bucket"] = case_output.apply(build_review_priority_bucket, axis=1)
    case_output["priority_score"] = case_output.apply(build_priority_score, axis=1)
    case_output["recommended_review_action"] = case_output["review_priority_bucket"].map(build_recommended_review_action)

    case_output = case_output.loc[:, CASE_COLS].sort_values(
        ["priority_score", "site", "strict_trigger_date", "panel_id"],
        ascending=[False, True, True, True],
    ).reset_index(drop=True)

    site_queue_output = build_site_queue(case_output)
    summary_output = build_summary(case_output, sites)
    return summary_output, case_output, site_queue_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_output, case_output, site_queue_output = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_output.to_csv(out_dir / "truth_coverage_priority_summary_v1.csv", index=False, encoding="utf-8-sig")
    case_output.to_csv(out_dir / "truth_coverage_priority_cases_v1.csv", index=False, encoding="utf-8-sig")
    site_queue_output.to_csv(out_dir / "truth_coverage_site_review_queue_v1.csv", index=False, encoding="utf-8-sig")
    print(f"truth_coverage_priority_cases_v1={len(case_output)}")


if __name__ == "__main__":
    main()
