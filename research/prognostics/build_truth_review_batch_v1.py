#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
ROUND1_BUCKETS = [
    "urgent_official_error_context",
    "vendor_backed_unlabeled",
    "high_actionability_unlabeled",
]
ROUND1_BUCKET_RANKS = {
    "urgent_official_error_context": 1,
    "vendor_backed_unlabeled": 2,
    "high_actionability_unlabeled": 3,
}
REVIEW_FOCUS_MAP = {
    "urgent_official_error_context": "official_error_reaudit",
    "vendor_backed_unlabeled": "vendor_field_log_compare",
    "high_actionability_unlabeled": "actionability_sanity_check",
}
REVIEW_CHECKLIST_MAP = {
    "official_error_reaudit": "기존 오탐/미탐 맥락 재확인, candidate_validity/date_judgement 우선 입력",
    "vendor_field_log_compare": "vendor 회신과 현장/O&M 로그 대조 후 candidate_validity 입력",
    "actionability_sanity_check": "현재 phenotype/actionability가 유지보수/리뷰 해석과 맞는지 확인",
}
KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
CASE_OUTPUT_COLS = [
    "round1_review_order",
    "round1_bucket_rank",
    "site",
    "panel_id",
    "strict_trigger_date",
    "review_priority_bucket",
    "priority_score",
    "review_focus",
    "review_checklist",
    "recommended_review_action",
    "vendor_reply_class",
    "vendor_fault_family",
    "critical_phenotype_v3",
    "actionability_v3",
    "official_error_modes",
    "official_error_types",
    "prediction_source",
    "gap_bucket",
    "promotion_hypothesis",
    "review_priority",
    "note",
    "vendor_note",
]
SITE_PACKET_COLS = [
    "site",
    "review_priority_bucket",
    "case_count",
    "top_priority_score",
    "example_panel_ids",
    "review_focus",
]
COPYBACK_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity",
    "date_judgement",
    "note",
    "review_owner",
    "review_status",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package round-1 manual truth review cases from the truth coverage priority audit."
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


def parse_expected_round1_count(summary_df: pd.DataFrame) -> int:
    if summary_df.empty:
        raise SystemExit("truth_coverage_priority_summary_v1.csv is empty")

    if "record_type" in summary_df.columns:
        summary_rows = summary_df.loc[summary_df["record_type"].map(normalize_text).eq("summary")]
    else:
        summary_rows = summary_df.iloc[:1]
    if summary_rows.empty:
        summary_rows = summary_df.iloc[:1]

    summary_row = summary_rows.iloc[0]
    expected = 0
    for col in [
        "urgent_official_error_context_count",
        "vendor_backed_unlabeled_count",
        "high_actionability_unlabeled_count",
    ]:
        expected += int(pd.to_numeric(summary_row.get(col, 0), errors="coerce") or 0)
    return int(expected)


def build_site_packets(round1_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (site, bucket), group in round1_df.groupby(["site", "review_priority_bucket"], dropna=False):
        ranked = group.sort_values(
            ["priority_score", "strict_trigger_date", "panel_id"],
            ascending=[False, True, True],
        ).reset_index(drop=True)
        rows.append(
            {
                "site": site,
                "review_priority_bucket": bucket,
                "case_count": int(len(group)),
                "top_priority_score": int(pd.to_numeric(group["priority_score"], errors="coerce").fillna(0).max()),
                "example_panel_ids": "|".join(ranked["panel_id"].map(normalize_text).drop_duplicates().head(3).tolist()),
                "review_focus": REVIEW_FOCUS_MAP[bucket],
            }
        )

    packets_df = pd.DataFrame(rows, columns=SITE_PACKET_COLS)
    if packets_df.empty:
        return packets_df
    return packets_df.sort_values(
        ["site", "top_priority_score", "case_count", "review_priority_bucket"],
        ascending=[True, False, False, True],
    ).reset_index(drop=True)


def build_copyback_template(round1_df: pd.DataFrame) -> pd.DataFrame:
    copyback_df = round1_df.loc[:, KEY_COLS].copy()
    for col in ["candidate_validity", "date_judgement", "note", "review_owner", "review_status"]:
        copyback_df[col] = ""
    return copyback_df.loc[:, COPYBACK_COLS]


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cases_df = read_csv(root / "_share" / "truth_coverage_priority_cases_v1.csv")
    summary_df = read_csv(root / "_share" / "truth_coverage_priority_summary_v1.csv")

    for col in KEY_COLS:
        if col not in cases_df.columns:
            raise SystemExit(f"missing required column in truth_coverage_priority_cases_v1.csv: {col}")
        if col == "strict_trigger_date":
            cases_df[col] = cases_df[col].map(normalize_date)
        else:
            cases_df[col] = cases_df[col].map(normalize_text)

    cases_df = cases_df.loc[cases_df["site"].isin(sites)].copy()

    text_cols = [
        "review_priority_bucket",
        "recommended_review_action",
        "vendor_reply_class",
        "vendor_fault_family",
        "critical_phenotype_v3",
        "actionability_v3",
        "official_error_modes",
        "official_error_types",
        "prediction_source",
        "gap_bucket",
        "promotion_hypothesis",
        "review_priority",
        "note",
        "vendor_note",
    ]
    for col in text_cols:
        if col not in cases_df.columns:
            cases_df[col] = ""
        cases_df[col] = cases_df[col].map(normalize_text)

    if "priority_score" not in cases_df.columns:
        raise SystemExit("missing required column in truth_coverage_priority_cases_v1.csv: priority_score")
    cases_df["priority_score"] = pd.to_numeric(cases_df["priority_score"], errors="coerce").fillna(0).astype(int)

    round1_df = cases_df.loc[cases_df["review_priority_bucket"].isin(ROUND1_BUCKETS)].copy()
    if round1_df.empty:
        raise SystemExit("round-1 selection is empty")

    round1_df = (
        round1_df.groupby(KEY_COLS, as_index=False)
        .agg(
            review_priority_bucket=("review_priority_bucket", first_nonblank),
            priority_score=("priority_score", "max"),
            recommended_review_action=("recommended_review_action", first_nonblank),
            vendor_reply_class=("vendor_reply_class", first_nonblank),
            vendor_fault_family=("vendor_fault_family", first_nonblank),
            critical_phenotype_v3=("critical_phenotype_v3", first_nonblank),
            actionability_v3=("actionability_v3", first_nonblank),
            official_error_modes=("official_error_modes", first_nonblank),
            official_error_types=("official_error_types", first_nonblank),
            prediction_source=("prediction_source", first_nonblank),
            gap_bucket=("gap_bucket", first_nonblank),
            promotion_hypothesis=("promotion_hypothesis", first_nonblank),
            review_priority=("review_priority", first_nonblank),
            note=("note", first_nonblank),
            vendor_note=("vendor_note", first_nonblank),
        )
    )

    round1_df["round1_bucket_rank"] = round1_df["review_priority_bucket"].map(ROUND1_BUCKET_RANKS).astype(int)
    round1_df["review_focus"] = round1_df["review_priority_bucket"].map(REVIEW_FOCUS_MAP)
    round1_df["review_checklist"] = round1_df["review_focus"].map(REVIEW_CHECKLIST_MAP)
    round1_df = round1_df.sort_values(
        ["priority_score", "site", "strict_trigger_date", "panel_id"],
        ascending=[False, True, True, True],
    ).reset_index(drop=True)
    round1_df["round1_review_order"] = range(1, len(round1_df) + 1)
    round1_df = round1_df.loc[:, CASE_OUTPUT_COLS]

    expected_round1_count = parse_expected_round1_count(summary_df)
    if len(round1_df) != expected_round1_count:
        raise SystemExit(
            "round-1 batch count mismatch: "
            f"selected={len(round1_df)} expected={expected_round1_count} from truth_coverage_priority_summary_v1.csv"
        )

    packets_df = build_site_packets(round1_df)
    copyback_df = build_copyback_template(round1_df)
    return round1_df, packets_df, copyback_df


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    batch_df, packets_df, copyback_df = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    batch_df.to_csv(out_dir / "truth_review_batch_v1.csv", index=False, encoding="utf-8-sig")
    packets_df.to_csv(out_dir / "truth_review_site_packets_v1.csv", index=False, encoding="utf-8-sig")
    copyback_df.to_csv(out_dir / "truth_review_copyback_template_v1.csv", index=False, encoding="utf-8-sig")
    print(f"truth_review_batch_v1={len(batch_df)}")


if __name__ == "__main__":
    main()
