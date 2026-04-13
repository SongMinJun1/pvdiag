#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REQUIRED_VENDOR_COLS = [
    "site",
    "panel_id",
    "vendor_reply_class",
    "vendor_fault_family",
    "field_confirmed_flag",
    "adjudication_weight",
    "vendor_note",
]
ONSET_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "first_warning_date",
    "retrospective_onset_date",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "reason_summary",
]
OUTPUT_COLS = [
    "site",
    "panel_id",
    "vendor_reply_class",
    "vendor_fault_family",
    "field_confirmed_flag",
    "adjudication_weight",
    "vendor_note",
    "strict_trigger_date",
    "first_warning_date",
    "retrospective_onset_date",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "reason_summary",
    "panel_found_in_ours",
    "dispute_type",
]
DISPUTE_COLS = [
    "site",
    "panel_id",
    "vendor_reply_class",
    "vendor_fault_family",
    "strict_trigger_date",
    "retrospective_onset_date",
    "onset_confidence",
    "reason_summary",
    "dispute_type",
    "vendor_note",
]
SUMMARY_COLS = [
    "manual_input_present",
    "total_rows",
    "matched_rows",
    "unmatched_rows",
    "count_by_vendor_reply_class",
    "count_by_vendor_fault_family",
    "count_by_dispute_type",
    "count_by_field_confirmed_flag",
]
VALID_VENDOR_REPLY_CLASSES = {
    "field_confirmed_positive",
    "vendor_pattern_positive",
    "vendor_likely_positive",
    "vendor_rejected",
    "vendor_no_info",
}
VALID_DISPUTE_TYPES = {
    "agree_positive",
    "agree_group_issue",
    "ours_positive_vendor_rejected",
    "ours_positive_vendor_no_info",
    "vendor_positive_not_in_ours",
    "needs_date_anchor_review",
}
POSITIVE_VENDOR_CLASSES = {
    "field_confirmed_positive",
    "vendor_pattern_positive",
    "vendor_likely_positive",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build structured vendor reply adjudication over mailed candidate panels.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def bool_text(value: object) -> str:
    text = normalize_text(value).lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return "1"
    if text in {"0", "false", "f", "no", "n"}:
        return "0"
    return ""


def ensure_columns(df: pd.DataFrame, expected: list[str], name: str) -> pd.DataFrame:
    missing = [col for col in expected if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")
    return df.copy()


def format_counts(series: pd.Series) -> str:
    if series.empty:
        return ""
    counts = series.fillna("").astype(str).map(normalize_text).replace("", "blank").value_counts(sort=False)
    return "|".join(f"{key}:{int(value)}" for key, value in counts.items())


def classify_dispute(row: pd.Series) -> str:
    vendor_class = normalize_text(row.get("vendor_reply_class"))
    panel_found = int(row.get("panel_found_in_ours", 0)) == 1
    field_confirmed = bool_text(row.get("field_confirmed_flag"))
    onset_conf = normalize_text(row.get("onset_confidence"))

    if panel_found:
        if field_confirmed == "1" or vendor_class == "field_confirmed_positive":
            return "agree_positive"
        if vendor_class == "vendor_pattern_positive":
            return "agree_group_issue"
        if vendor_class == "vendor_likely_positive":
            return "agree_positive"
        if vendor_class == "vendor_rejected":
            if onset_conf == "low":
                return "needs_date_anchor_review"
            return "ours_positive_vendor_rejected"
        if vendor_class == "vendor_no_info":
            return "ours_positive_vendor_no_info"
        return "needs_date_anchor_review"

    if vendor_class in POSITIVE_VENDOR_CLASSES or field_confirmed == "1":
        return "vendor_positive_not_in_ours"
    return "needs_date_anchor_review"


def empty_outputs(share_dir: Path) -> None:
    latest = pd.DataFrame(columns=OUTPUT_COLS)
    disputes = pd.DataFrame(columns=DISPUTE_COLS)
    summary = pd.DataFrame(
        [
            {
                "manual_input_present": 0,
                "total_rows": 0,
                "matched_rows": 0,
                "unmatched_rows": 0,
                "count_by_vendor_reply_class": "",
                "count_by_vendor_fault_family": "",
                "count_by_dispute_type": "",
                "count_by_field_confirmed_flag": "",
            }
        ],
        columns=SUMMARY_COLS,
    )
    latest.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")
    disputes.to_csv(share_dir / "vendor_reply_disputes.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / "vendor_reply_confusion_summary.csv", index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    vendor_path = root / "data" / "manual" / "vendor_reply_cases.csv"
    onset_path = share_dir / "panel_onset_shadow_latest.csv"

    if not vendor_path.exists():
        empty_outputs(share_dir)
        print("manual_input_present=0")
        print("vendor_reply_rows=0")
        return

    if not onset_path.exists():
        raise SystemExit(f"missing onset shadow input: {onset_path}")

    vendor_df = ensure_columns(read_csv(vendor_path), REQUIRED_VENDOR_COLS, "vendor_reply_cases.csv")
    onset_df = ensure_columns(read_csv(onset_path), ONSET_COLS, "panel_onset_shadow_latest.csv")

    for col in ["site", "panel_id", "vendor_reply_class", "vendor_fault_family", "vendor_note"]:
        vendor_df[col] = vendor_df[col].map(normalize_text)
    vendor_df["field_confirmed_flag"] = vendor_df["field_confirmed_flag"].map(bool_text)
    vendor_df["adjudication_weight"] = pd.to_numeric(vendor_df["adjudication_weight"], errors="coerce")

    invalid_vendor = sorted(set(vendor_df["vendor_reply_class"]) - VALID_VENDOR_REPLY_CLASSES - {""})
    if invalid_vendor:
        raise SystemExit(f"vendor_reply_cases.csv has invalid vendor_reply_class values: {invalid_vendor}")

    onset_df["site"] = onset_df["site"].map(normalize_text)
    onset_df["panel_id"] = onset_df["panel_id"].map(normalize_text)

    merged = vendor_df.merge(onset_df, on=["site", "panel_id"], how="left", indicator=True)
    merged["panel_found_in_ours"] = merged["_merge"].eq("both").astype(int)
    merged["dispute_type"] = merged.apply(classify_dispute, axis=1)

    invalid_disputes = sorted(set(merged["dispute_type"]) - VALID_DISPUTE_TYPES)
    if invalid_disputes:
        raise SystemExit(f"internal error: invalid dispute_type values: {invalid_disputes}")

    latest_df = merged.loc[:, OUTPUT_COLS].copy()
    disputes_df = latest_df.loc[latest_df["dispute_type"].isin([
        "ours_positive_vendor_rejected",
        "ours_positive_vendor_no_info",
        "vendor_positive_not_in_ours",
        "needs_date_anchor_review",
    ]), DISPUTE_COLS].copy()

    summary_df = pd.DataFrame(
        [
            {
                "manual_input_present": 1,
                "total_rows": int(len(latest_df)),
                "matched_rows": int(latest_df["panel_found_in_ours"].eq(1).sum()),
                "unmatched_rows": int(latest_df["panel_found_in_ours"].eq(0).sum()),
                "count_by_vendor_reply_class": format_counts(latest_df["vendor_reply_class"]),
                "count_by_vendor_fault_family": format_counts(latest_df["vendor_fault_family"]),
                "count_by_dispute_type": format_counts(latest_df["dispute_type"]),
                "count_by_field_confirmed_flag": format_counts(latest_df["field_confirmed_flag"]),
            }
        ],
        columns=SUMMARY_COLS,
    )

    latest_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / "vendor_reply_confusion_summary.csv", index=False, encoding="utf-8-sig")
    disputes_df.to_csv(share_dir / "vendor_reply_disputes.csv", index=False, encoding="utf-8-sig")

    print("manual_input_present=1")
    print(f"vendor_reply_rows={len(latest_df)}")
    print(f"matched_rows={int(latest_df['panel_found_in_ours'].eq(1).sum())}")


if __name__ == "__main__":
    main()
