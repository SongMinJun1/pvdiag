#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_CONFIRMATION_INPUT = Path(
    "/private/tmp/physical_confirmation_requirements_review_check/"
    "panel_day_engine_physical_confirmation_requirements_review_v1.csv"
)
DEFAULT_CHECKLIST_INPUT = Path(
    "/private/tmp/physical_confirmation_requirements_review_check/"
    "panel_day_engine_physical_confirmation_requirements_checklist_v1.csv"
)

REQUEST_OUTPUT_NAME = "panel_day_engine_physical_evidence_request_packet_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_physical_evidence_request_packet_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_physical_evidence_request_packet_note_v1.md"

CONFIRMATION_REQUIRED_COLS = [
    "confirmation_case_id",
    "source_raw_support_case_id",
    "site",
    "panel_id",
    "confirmation_bucket",
    "candidate_fault_family_label_ko",
    "target_vdom_signal_days",
    "raw_daily_support_frac",
    "raw_median_v_ratio",
    "raw_median_i_ratio",
    "independent_confirmation_required_axes_met",
    "independent_confirmation_required_axes_total",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "threshold_patch_allowed_flag",
]

CHECKLIST_REQUIRED_COLS = [
    "confirmation_case_id",
    "site",
    "panel_id",
    "confirmation_axis",
    "axis_required_for_packet_flag",
    "axis_status",
    "satisfies_axis_flag",
    "next_action",
]

REQUEST_COLS = [
    "evidence_request_id",
    "confirmation_case_id",
    "source_raw_support_case_id",
    "site",
    "panel_id",
    "request_priority",
    "request_status",
    "requested_evidence_bundle",
    "required_axis_count",
    "missing_required_axis_count",
    "optional_axis_count",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "threshold_patch_allowed_flag",
    "candidate_fault_family_label_ko",
    "current_confirmation_bucket",
    "target_vdom_signal_days",
    "raw_daily_support_frac",
    "raw_median_v_ratio",
    "raw_median_i_ratio",
    "direct_physical_measurement_request",
    "maintenance_or_inspection_request",
    "optional_field_reproducibility_request",
    "optional_artifact_exclusion_request",
    "acceptance_criteria",
    "why_needed",
    "handoff_note",
]

SUMMARY_COLS = [
    "request_priority",
    "request_status",
    "current_confirmation_bucket",
    "site",
    "requests",
    "missing_required_axis_count_sum",
    "operator_promotion_allowed_sum",
    "engine_patch_candidate_sum",
    "threshold_patch_allowed_sum",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert BR-069 physical confirmation gaps into an exact-panel evidence request packet."
        )
    )
    parser.add_argument("--confirmation-input", type=Path, default=DEFAULT_CONFIRMATION_INPUT)
    parser.add_argument("--checklist-input", type=Path, default=DEFAULT_CHECKLIST_INPUT)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def numeric_value(value: object) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0.0 if pd.isna(numeric) else float(numeric)


def int_value(value: object) -> int:
    return int(round(numeric_value(value)))


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def require_columns(df: pd.DataFrame, cols: list[str], label: str) -> None:
    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise SystemExit(f"{label} is missing columns: {missing}")


def missing_axes(checklist: pd.DataFrame, confirmation_case_id: str, required_only: bool) -> list[str]:
    rows = checklist.loc[checklist["confirmation_case_id"].map(normalize_text).eq(confirmation_case_id)].copy()
    if required_only:
        rows = rows.loc[rows["axis_required_for_packet_flag"].map(int_value).eq(1)].copy()
    rows = rows.loc[rows["satisfies_axis_flag"].map(int_value).eq(0)].copy()
    return [normalize_text(value) for value in rows["confirmation_axis"].tolist()]


def request_priority(missing_required_count: int, raw_daily_support_frac: float) -> str:
    if missing_required_count > 0 and raw_daily_support_frac >= 0.80:
        return "high_evidence_gap_priority"
    if missing_required_count > 0:
        return "standard_evidence_gap_priority"
    return "packet_review_priority"


def bundle_name(required_axes: list[str]) -> str:
    if "direct_physical_measurement" in required_axes and "maintenance_or_inspection_record" in required_axes:
        return "exact_panel_physical_measurement_plus_inspection"
    if "direct_physical_measurement" in required_axes:
        return "exact_panel_physical_measurement"
    if "maintenance_or_inspection_record" in required_axes:
        return "exact_panel_inspection_or_maintenance"
    return "confirmation_packet_review"


def build_requests(confirmation: pd.DataFrame, checklist: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    target = confirmation.loc[
        confirmation["confirmation_bucket"].map(normalize_text).eq("raw_supported_confirmation_gap_hold")
    ].copy()
    for idx, row in target.sort_values(["site", "panel_id"]).reset_index(drop=True).iterrows():
        case_id = normalize_text(row["confirmation_case_id"])
        required_missing = missing_axes(checklist, case_id, required_only=True)
        optional_missing = missing_axes(checklist, case_id, required_only=False)
        required_total = int_value(row["independent_confirmation_required_axes_total"])
        required_met = int_value(row["independent_confirmation_required_axes_met"])
        missing_required_count = max(required_total - required_met, 0)
        raw_daily_support_frac = round(numeric_value(row["raw_daily_support_frac"]), 6)
        priority = request_priority(missing_required_count, raw_daily_support_frac)
        requested_bundle = bundle_name(required_missing)
        rows.append(
            {
                "evidence_request_id": f"BR070-{idx + 1:03d}",
                "confirmation_case_id": case_id,
                "source_raw_support_case_id": normalize_text(row["source_raw_support_case_id"]),
                "site": normalize_text(row["site"]),
                "panel_id": normalize_text(row["panel_id"]),
                "request_priority": priority,
                "request_status": "open_exact_panel_evidence_request" if missing_required_count else "ready_for_confirmation_packet_review",
                "requested_evidence_bundle": requested_bundle,
                "required_axis_count": required_total,
                "missing_required_axis_count": missing_required_count,
                "optional_axis_count": len([axis for axis in optional_missing if axis not in required_missing]),
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
                "threshold_patch_allowed_flag": 0,
                "candidate_fault_family_label_ko": normalize_text(row["candidate_fault_family_label_ko"]),
                "current_confirmation_bucket": normalize_text(row["confirmation_bucket"]),
                "target_vdom_signal_days": int_value(row["target_vdom_signal_days"]),
                "raw_daily_support_frac": raw_daily_support_frac,
                "raw_median_v_ratio": round(numeric_value(row["raw_median_v_ratio"]), 6),
                "raw_median_i_ratio": round(numeric_value(row["raw_median_i_ratio"]), 6),
                "direct_physical_measurement_request": (
                    "exact-panel IV curve, waveform capture, thermal/IR, or measured voltage/current artifact"
                    if "direct_physical_measurement" in required_missing
                    else "satisfied_or_not_required"
                ),
                "maintenance_or_inspection_request": (
                    "exact-panel maintenance, inspection, repair, work-order, or ticket record"
                    if "maintenance_or_inspection_record" in required_missing
                    else "satisfied_or_not_required"
                ),
                "optional_field_reproducibility_request": (
                    "exact-panel field reproducibility note if available"
                    if "field_reproducibility_confirmation" in optional_missing
                    else "satisfied_or_not_required"
                ),
                "optional_artifact_exclusion_request": (
                    "exact-panel sensor/reference/instrumentation exclusion note if available"
                    if "independent_artifact_exclusion" in optional_missing
                    else "satisfied_or_not_required"
                ),
                "acceptance_criteria": (
                    "evidence must include exact site, exact panel_id, date/time or inspection date, evidence type, "
                    "and whether it is usable for exact validation"
                ),
                "why_needed": (
                    "BR-068 raw waveform support is strong, but BR-069 blocks thresholding until independent "
                    "physical and inspection axes are present."
                ),
                "handoff_note": (
                    "attach evidence to manual field evidence or a linked review packet, then rerun BR-069 and BR-070"
                ),
            }
        )
    return pd.DataFrame(rows).reindex(columns=REQUEST_COLS)


def build_summary(requests: pd.DataFrame) -> pd.DataFrame:
    if requests.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary = (
        requests.groupby(["request_priority", "request_status", "current_confirmation_bucket", "site"], dropna=False)
        .agg(
            requests=("evidence_request_id", "nunique"),
            missing_required_axis_count_sum=("missing_required_axis_count", "sum"),
            operator_promotion_allowed_sum=("operator_promotion_allowed_flag", "sum"),
            engine_patch_candidate_sum=("engine_patch_candidate_flag", "sum"),
            threshold_patch_allowed_sum=("threshold_patch_allowed_flag", "sum"),
        )
        .reset_index()
    )
    return summary.reindex(columns=SUMMARY_COLS).sort_values(["request_priority", "site"])


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    header = "| " + " | ".join(df.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows = [
        "| " + " | ".join(normalize_text(row[col]) for col in df.columns) + " |"
        for row in df.to_dict(orient="records")
    ]
    return "\n".join([header, separator] + rows)


def write_note(output_dir: Path, requests: pd.DataFrame, summary: pd.DataFrame) -> None:
    display_cols = [
        "site",
        "panel_id",
        "request_priority",
        "requested_evidence_bundle",
        "missing_required_axis_count",
        "raw_daily_support_frac",
        "raw_median_v_ratio",
        "raw_median_i_ratio",
    ]
    lines = [
        "# panel_day_engine_physical_evidence_request_packet_note_v1",
        "",
        "## Purpose",
        "- Convert BR-069 confirmation gaps into exact-panel evidence requests.",
        "- Keep acquisition work separate from operator-facing promotion and engine thresholding.",
        "",
        "## Guardrails",
        f"- request rows: `{len(requests)}`",
        f"- operator promotion allowed sum: `{int(requests['operator_promotion_allowed_flag'].sum()) if len(requests) else 0}`",
        f"- engine patch candidate sum: `{int(requests['engine_patch_candidate_flag'].sum()) if len(requests) else 0}`",
        f"- threshold patch allowed sum: `{int(requests['threshold_patch_allowed_flag'].sum()) if len(requests) else 0}`",
        "",
        "## Summary",
        dataframe_to_markdown(summary),
        "",
        "## Request Snapshot",
        dataframe_to_markdown(requests[display_cols] if not requests.empty else requests),
        "",
        "## Interpretation",
        "- This packet does not add new physical truth.",
        "- It makes the missing truth request explicit, exact-panel scoped, and rerunnable through BR-069.",
    ]
    (output_dir / NOTE_OUTPUT_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    confirmation = read_csv(args.confirmation_input)
    checklist = read_csv(args.checklist_input)
    require_columns(confirmation, CONFIRMATION_REQUIRED_COLS, "confirmation input")
    require_columns(checklist, CHECKLIST_REQUIRED_COLS, "checklist input")
    requests = build_requests(confirmation, checklist)
    summary = build_summary(requests)
    if len(requests) and int(requests["operator_promotion_allowed_flag"].sum()) != 0:
        raise SystemExit("evidence request packet must not allow operator promotion")
    if len(requests) and int(requests["engine_patch_candidate_flag"].sum()) != 0:
        raise SystemExit("evidence request packet must not allow engine patch")
    if len(requests) and int(requests["threshold_patch_allowed_flag"].sum()) != 0:
        raise SystemExit("evidence request packet must not allow threshold patch")
    requests.to_csv(args.output_dir / REQUEST_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(args.output_dir, requests, summary)


if __name__ == "__main__":
    main()
