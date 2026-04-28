#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_GAP_REVIEW_INPUT = Path(
    "/private/tmp/no_report_heuristic_gap_review_check/panel_day_engine_no_report_heuristic_gap_review_v1.csv"
)
DETAIL_OUTPUT_NAME = "panel_day_engine_non_fault_morphology_observation_sidecar_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_non_fault_morphology_observation_sidecar_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_non_fault_morphology_observation_sidecar_note_v1.md"
ELIGIBLE_DATE_GAP = "near_anchor_1_3d"
ELIGIBLE_HEURISTIC_GAP = "expected_absent_non_fault_status_gate"
OBSERVATION_SCOPE = "near_anchor_non_fault_morphology"
OBSERVATION_LABEL_KO = "미확정 근접 관찰 신호"
RECOMMENDED_ACTION = "keep_sidecar_review_only"

SOURCE_COLS = [
    "site",
    "panel_id",
    "source_search_status",
    "recovery_bucket",
    "synchrony_bucket",
    "anchor_dates",
    "raw_candidate_dates",
    "nearest_raw_candidate_date",
    "nearest_anchor_date",
    "min_abs_gap_days",
    "gap_direction",
    "date_alignment_gap_type",
    "raw_candidate_row_count",
    "raw_signal_row_count",
    "raw_recovery_row_count",
    "raw_pre_ews_row_count",
    "raw_prefault_B_effective_row_count",
    "raw_fault_like_row_count",
    "raw_final_fault_row_count",
    "raw_critical_fault_row_count",
    "raw_re_drop_row_count",
    "raw_common_cause_row_count",
    "signal_basis_type",
    "raw_audit_status_ko",
    "raw_final_status_ko",
    "raw_audit_anom_subtype",
    "raw_audit_critical_source",
    "raw_heuristic_row_present_flag",
    "any_operator_report_row_present_flag",
    "report_attachment_gap_type",
    "heuristic_attachment_gap_type",
    "engine_patch_candidate_flag",
    "report_patch_candidate_flag",
    "review_note",
]

DETAIL_COLS = [
    "site",
    "panel_id",
    "observation_scope",
    "observation_label_ko",
    "source_gap_review_status",
    "anchor_dates",
    "raw_candidate_dates",
    "nearest_raw_candidate_date",
    "nearest_anchor_date",
    "min_abs_gap_days",
    "gap_direction",
    "date_alignment_gap_type",
    "signal_basis_type",
    "recovery_bucket",
    "synchrony_bucket",
    "raw_candidate_row_count",
    "raw_signal_row_count",
    "raw_recovery_row_count",
    "raw_pre_ews_row_count",
    "raw_prefault_B_effective_row_count",
    "raw_fault_like_row_count",
    "raw_final_fault_row_count",
    "raw_critical_fault_row_count",
    "raw_re_drop_row_count",
    "raw_common_cause_row_count",
    "raw_audit_status_ko",
    "raw_final_status_ko",
    "raw_audit_anom_subtype",
    "raw_audit_critical_source",
    "raw_heuristic_row_present_flag",
    "any_operator_report_row_present_flag",
    "report_attachment_gap_type",
    "heuristic_attachment_gap_type",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "report_observation_sidecar_flag",
    "recommended_action",
    "review_note",
]

SUMMARY_COLS = [
    "site",
    "observation_scope",
    "date_alignment_gap_type",
    "signal_basis_type",
    "panels",
    "operator_promotion_allowed_sum",
    "engine_patch_candidate_sum",
    "report_observation_sidecar_sum",
    "raw_pre_ews_rows",
    "raw_recovery_rows",
    "raw_fault_like_rows",
    "raw_final_fault_rows",
    "raw_critical_fault_rows",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an evidence-only sidecar for near-anchor non-fault morphology rows "
            "found by the no-report heuristic gap review."
        )
    )
    parser.add_argument("--gap-review-input", type=Path, default=DEFAULT_GAP_REVIEW_INPUT)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def to_flag(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return 1
    if text in {"0", "false", "f", "no", "n", ""}:
        return 0
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(float(numeric) > 0)


def to_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


def read_gap_review(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing gap review input: {path}")
    df = pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
    missing = [col for col in SOURCE_COLS if col not in df.columns]
    if missing:
        raise SystemExit(f"gap review input is missing columns: {missing}")
    out = df.copy()
    for col in SOURCE_COLS:
        if col.endswith("_flag"):
            out[col] = out[col].map(to_flag)
        elif col.endswith("_count") or col in {"min_abs_gap_days"}:
            out[col] = out[col].map(to_int)
        else:
            out[col] = out[col].map(normalize_text)
    return out


def select_observation_rows(df: pd.DataFrame) -> pd.DataFrame:
    hard_signal_sum = (
        df["raw_fault_like_row_count"]
        + df["raw_final_fault_row_count"]
        + df["raw_critical_fault_row_count"]
    )
    mask = (
        (df["report_patch_candidate_flag"] == 1)
        & (df["engine_patch_candidate_flag"] == 0)
        & (df["date_alignment_gap_type"] == ELIGIBLE_DATE_GAP)
        & (df["heuristic_attachment_gap_type"] == ELIGIBLE_HEURISTIC_GAP)
        & (df["raw_audit_status_ko"] == "미확정")
        & (df["raw_final_status_ko"] == "미확정")
        & (hard_signal_sum == 0)
    )
    return df.loc[mask].copy()


def build_detail(rows: pd.DataFrame) -> pd.DataFrame:
    detail = pd.DataFrame(columns=DETAIL_COLS)
    if rows.empty:
        return detail
    detail = rows.rename(columns={"source_search_status": "source_gap_review_status"}).copy()
    detail["observation_scope"] = OBSERVATION_SCOPE
    detail["observation_label_ko"] = OBSERVATION_LABEL_KO
    detail["operator_promotion_allowed_flag"] = 0
    detail["report_observation_sidecar_flag"] = 1
    detail["recommended_action"] = RECOMMENDED_ACTION
    detail["review_note"] = detail.apply(make_review_note, axis=1)
    return detail[DETAIL_COLS].sort_values(["site", "panel_id"]).reset_index(drop=True)


def make_review_note(row: pd.Series) -> str:
    return (
        f"non-fault near-anchor morphology only: status={row['raw_audit_status_ko']}, "
        f"gap={row['min_abs_gap_days']}d/{row['gap_direction']}, "
        f"basis={row['signal_basis_type']}, hard_signal_rows=0; "
        "keep outside operator fault promotion"
    )


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    grouped = (
        detail.groupby(
            ["site", "observation_scope", "date_alignment_gap_type", "signal_basis_type"],
            dropna=False,
        )
        .agg(
            panels=("panel_id", "nunique"),
            operator_promotion_allowed_sum=("operator_promotion_allowed_flag", "sum"),
            engine_patch_candidate_sum=("engine_patch_candidate_flag", "sum"),
            report_observation_sidecar_sum=("report_observation_sidecar_flag", "sum"),
            raw_pre_ews_rows=("raw_pre_ews_row_count", "sum"),
            raw_recovery_rows=("raw_recovery_row_count", "sum"),
            raw_fault_like_rows=("raw_fault_like_row_count", "sum"),
            raw_final_fault_rows=("raw_final_fault_row_count", "sum"),
            raw_critical_fault_rows=("raw_critical_fault_row_count", "sum"),
        )
        .reset_index()
    )
    return grouped[SUMMARY_COLS].sort_values(["site", "signal_basis_type"]).reset_index(drop=True)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No selected rows._"
    header = "| " + " | ".join(df.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows = [
        "| " + " | ".join(normalize_text(row[col]) for col in df.columns) + " |"
        for row in df.to_dict(orient="records")
    ]
    return "\n".join([header, separator] + rows)


def write_note(output_dir: Path, detail: pd.DataFrame, summary: pd.DataFrame, source_path: Path) -> None:
    site_counts = detail["site"].value_counts().sort_index().to_dict() if not detail.empty else {}
    basis_counts = (
        detail["signal_basis_type"].value_counts().sort_index().to_dict() if not detail.empty else {}
    )
    text = "\n".join(
        [
            "# BR-056 Non-Fault Morphology Observation Sidecar",
            "",
            "## Source",
            f"- input: `{source_path}`",
            "",
            "## Selection Rule",
            f"- `report_patch_candidate_flag == 1`",
            f"- `engine_patch_candidate_flag == 0`",
            f"- `date_alignment_gap_type == {ELIGIBLE_DATE_GAP}`",
            f"- `heuristic_attachment_gap_type == {ELIGIBLE_HEURISTIC_GAP}`",
            "- `raw_audit_status_ko == 미확정` and `raw_final_status_ko == 미확정`",
            "- hard fault row counts are all zero",
            "",
            "## Result",
            f"- observation rows: `{len(detail)}`",
            f"- site counts: `{site_counts}`",
            f"- signal basis counts: `{basis_counts}`",
            f"- operator promotion allowed sum: `{int(detail['operator_promotion_allowed_flag'].sum()) if not detail.empty else 0}`",
            f"- engine patch candidate sum: `{int(detail['engine_patch_candidate_flag'].sum()) if not detail.empty else 0}`",
            "",
            "## Interpretation",
            "- These rows are retained as analyst/review evidence only.",
            "- They do not close the exact-family gap.",
            "- They do not justify a `panel_day_engine.py` rule or threshold patch.",
            "- They may help explain near-anchor morphology around non-fault status-gated rows.",
            "",
            "## Summary Table",
            dataframe_to_markdown(summary),
            "",
        ]
    )
    (output_dir / NOTE_OUTPUT_NAME).write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    gap_review = read_gap_review(args.gap_review_input)
    selected = select_observation_rows(gap_review)
    detail = build_detail(selected)
    summary = build_summary(detail)
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(args.output_dir, detail, summary, args.gap_review_input)


if __name__ == "__main__":
    main()
