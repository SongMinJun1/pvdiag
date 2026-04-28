#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


ATTACHMENT_INPUT_NAME = "panel_day_engine_voltage_preserved_raw_source_attachment_index_v1.csv"
DAILY_TRACE_INPUT_NAME = "panel_day_engine_voltage_preserved_raw_source_daily_trace_v1.csv"

REVIEW_OUTPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_gap_review_v1.csv"
CHECKLIST_OUTPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_gap_checklist_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_gap_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_gap_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_gap_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_gap_review_v1.json"

DEFAULT_ATTACHMENT_DIR = "/private/tmp/panel_day_engine_voltage_preserved_raw_source_attachment_br096_check"
DEFAULT_VENDOR_INPUT = str(Path(__file__).resolve().parents[2] / "data" / "manual" / "vendor_reply_cases.csv")
DEFAULT_MANUAL_SITE_INPUT = "docs/internal/manual_field_evidence_latest.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/panel_day_engine_voltage_preserved_confirmation_gap_review_br097_check"

ATTACHMENT_REQUIRED_COLUMNS = [
    "attachment_row_id",
    "evidence_request_id",
    "source_confirmation_packet_row_id",
    "source_confirmation_family_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "request_priority",
    "attachment_status",
    "source_candidate_rows_attached",
    "core_window_rows_attached",
    "core_signal_days_attached",
    "core_voltage_preserved_days_attached",
    "core_common_cause_flag_days",
    "core_measurement_artifact_hold_days",
    "raw_file_refs_total",
    "raw_file_refs_found",
    "raw_file_refs_missing",
    "raw_waveform_is_independent_confirmation",
    "physical_or_maintenance_evidence_attached",
    "common_cause_clearance_attached",
    "measurement_artifact_clearance_attached",
    "counterexample_clearance_attached",
    "evidence_ready_for_truth_use",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

DAILY_REQUIRED_COLUMNS = [
    "evidence_request_id",
    "site",
    "root_id",
    "panel_id",
    "date",
    "raw_csv_exists",
    "voltage_preserved_core_signal",
    "common_cause_context_flag",
    "measurement_artifact_hold_flag",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

VENDOR_REQUIRED_COLUMNS = [
    "site",
    "panel_id",
    "vendor_reply_class",
    "vendor_fault_family",
    "field_confirmed_flag",
    "adjudication_weight",
    "vendor_note",
]

MANUAL_SITE_REQUIRED_COLUMNS = [
    "site",
    "evidence_type",
    "description",
    "expected_family",
    "time_type",
    "time_value",
    "related_panel_count",
    "evidence_strength",
    "usable_for_exact_validation",
    "note",
]

REVIEW_COLUMNS = [
    "owner_branch",
    "gap_review_row_id",
    "source_attachment_row_id",
    "evidence_request_id",
    "source_confirmation_packet_row_id",
    "source_confirmation_family_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "request_priority",
    "review_bucket",
    "raw_source_trace_attached",
    "raw_source_trace_status",
    "source_candidate_rows_attached",
    "daily_trace_rows",
    "core_signal_days_attached",
    "core_voltage_preserved_days_attached",
    "raw_file_refs_found",
    "raw_file_refs_missing",
    "vendor_exact_rows",
    "vendor_positive_pattern_rows",
    "vendor_likely_positive_rows",
    "vendor_rejected_rows",
    "vendor_field_confirmed_rows",
    "vendor_fault_family_list",
    "vendor_support_bucket",
    "manual_site_context_rows",
    "manual_site_exact_usable_rows",
    "manual_site_usable_for_exact_validation",
    "common_cause_flag_days",
    "measurement_artifact_hold_days",
    "counterexample_clearance_required",
    "common_cause_data_clearance_candidate",
    "measurement_artifact_data_clearance_candidate",
    "counterexample_clearance_candidate",
    "independent_physical_or_maintenance_confirmation_met",
    "all_clearance_axes_candidate_met",
    "evidence_ready_for_truth_use",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "recommended_next_action",
    "notes",
]

CHECKLIST_COLUMNS = [
    "owner_branch",
    "gap_review_row_id",
    "checklist_row_id",
    "evidence_request_id",
    "site",
    "panel_id",
    "confirmation_axis",
    "axis_status",
    "axis_required_for_truth_use",
    "satisfies_independent_confirmation",
    "supporting_row_count",
    "support_source",
    "why_it_matters",
    "next_action",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "summary_scope",
    "summary_key",
    "review_rows",
    "raw_source_trace_attached_rows",
    "vendor_exact_support_rows",
    "vendor_positive_or_likely_rows",
    "vendor_rejected_rows",
    "vendor_field_confirmed_rows",
    "manual_site_context_rows_sum",
    "common_cause_data_clearance_candidate_rows",
    "measurement_artifact_data_clearance_candidate_rows",
    "counterexample_clearance_required_rows",
    "independent_confirmation_met_rows",
    "all_clearance_axes_candidate_met_rows",
    "evidence_ready_for_truth_use_sum",
    "positive_truth_candidate_approved_sum",
    "threshold_tuning_approved_sum",
    "operator_facing_change_allowed_sum",
    "engine_patch_allowed_sum",
    "threshold_patch_allowed_sum",
    "notes",
]

ACTION_COLUMNS = [
    "owner_branch",
    "sequence",
    "action_id",
    "action",
    "input_filter",
    "purpose",
    "success_boundary",
    "recommended_next_artifact",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def numeric_float(value: object) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0.0 if pd.isna(numeric) else float(numeric)


def numeric_int(value: object) -> int:
    return int(round(numeric_float(value)))


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_required_csv(path: Path, required_cols: list[str], name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing required input {name}: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")
    return df


def normalize_frame(df: pd.DataFrame, text_cols: set[str], numeric_cols: set[str]) -> pd.DataFrame:
    out = df.copy()
    for col in text_cols:
        if col in out.columns:
            out[col] = out[col].map(normalize_text)
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    return out


def normalize_attachment(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = {
        "source_candidate_rows_attached",
        "core_window_rows_attached",
        "core_signal_days_attached",
        "core_voltage_preserved_days_attached",
        "core_common_cause_flag_days",
        "core_measurement_artifact_hold_days",
        "raw_file_refs_total",
        "raw_file_refs_found",
        "raw_file_refs_missing",
        "raw_waveform_is_independent_confirmation",
        "physical_or_maintenance_evidence_attached",
        "common_cause_clearance_attached",
        "measurement_artifact_clearance_attached",
        "counterexample_clearance_attached",
        "evidence_ready_for_truth_use",
        "positive_truth_candidate_approved",
        "threshold_tuning_approved",
        "operator_facing_change_allowed",
        "engine_patch_allowed",
        "threshold_patch_allowed",
    }
    out = normalize_frame(df, set(ATTACHMENT_REQUIRED_COLUMNS) - numeric_cols, numeric_cols)
    return out.sort_values(["site", "root_id", "panel_group_key", "panel_id"]).reset_index(drop=True)


def normalize_vendor(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = {"field_confirmed_flag", "adjudication_weight"}
    out = normalize_frame(df, set(VENDOR_REQUIRED_COLUMNS) - numeric_cols, numeric_cols)
    return out


def normalize_manual_site(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = {"related_panel_count"}
    out = normalize_frame(df, set(MANUAL_SITE_REQUIRED_COLUMNS) - numeric_cols, numeric_cols)
    return out


def assert_safe_input(attachment_df: pd.DataFrame, daily_df: pd.DataFrame) -> None:
    for name, df in [("BR-096 attachment", attachment_df), ("BR-096 daily", daily_df)]:
        for col in ["operator_facing_change_allowed", "engine_patch_allowed", "threshold_patch_allowed"]:
            total = int(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())
            if total != 0:
                raise ValueError(f"BR-097 requires non-authorizing input; {name} {col} sum is {total}")
    for col in ["positive_truth_candidate_approved", "threshold_tuning_approved", "evidence_ready_for_truth_use"]:
        total = int(pd.to_numeric(attachment_df[col], errors="coerce").fillna(0).sum())
        if total != 0:
            raise ValueError(f"BR-097 must start before truth/replay approval; {col} sum is {total}")


def vendor_support_bucket(vendor_rows: pd.DataFrame) -> str:
    if vendor_rows.empty:
        return "no_exact_vendor_record"
    if int(vendor_rows["field_confirmed_flag"].sum()) > 0:
        return "field_confirmed_vendor_record"
    if vendor_rows["vendor_reply_class"].map(normalize_text).str.contains("rejected", case=False, na=False).any():
        return "exact_vendor_rejection_or_none_visible"
    if vendor_rows["vendor_reply_class"].map(normalize_text).str.contains("positive", case=False, na=False).any():
        return "exact_vendor_pattern_support_unconfirmed"
    return "exact_vendor_context_unconfirmed"


def manual_site_exact_usable(manual_rows: pd.DataFrame) -> int:
    if manual_rows.empty:
        return 0
    usable = manual_rows["usable_for_exact_validation"].map(normalize_text).str.lower().isin({"yes", "true", "1"})
    return int(usable.sum())


def classify_review_bucket(
    raw_attached: int,
    vendor_bucket: str,
    common_clear_candidate: int,
    artifact_clear_candidate: int,
    counterexample_required: int,
) -> str:
    if not raw_attached:
        return "raw_source_trace_missing_hold"
    if counterexample_required:
        return "counterexample_guarded_hold"
    if not common_clear_candidate or not artifact_clear_candidate:
        return "blocker_clearance_hold"
    if vendor_bucket == "field_confirmed_vendor_record":
        return "field_confirmed_review_ready"
    if vendor_bucket == "exact_vendor_pattern_support_unconfirmed":
        return "vendor_supported_needs_physical_confirmation"
    if vendor_bucket == "exact_vendor_rejection_or_none_visible":
        return "vendor_rejected_or_none_visible_hold"
    return "raw_supported_needs_independent_confirmation"


def recommended_action(bucket: str) -> str:
    if bucket == "counterexample_guarded_hold":
        return "resolve counterexample clearance before any truth rebuild"
    if bucket == "blocker_clearance_hold":
        return "review common-cause and measurement-artifact blockers before confirmation"
    if bucket == "vendor_supported_needs_physical_confirmation":
        return "attach exact-panel physical measurement or maintenance record to validate vendor pattern support"
    if bucket == "vendor_rejected_or_none_visible_hold":
        return "treat as negative/hold unless new exact-panel evidence overturns the vendor rejection"
    if bucket == "field_confirmed_review_ready":
        return "review field-confirmed record and build a separate confirmed-positive intake only if axes are complete"
    return "collect independent exact-panel physical or maintenance evidence"


def build_review(
    owner_branch: str,
    attachment_df: pd.DataFrame,
    vendor_df: pd.DataFrame,
    manual_site_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(attachment_df.to_dict(orient="records"), start=1):
        site = normalize_text(row["site"])
        panel_id = normalize_text(row["panel_id"])
        vendor_rows = vendor_df.loc[vendor_df["site"].eq(site) & vendor_df["panel_id"].eq(panel_id)].copy()
        manual_rows = manual_site_df.loc[manual_site_df["site"].eq(site)].copy()
        vendor_positive = int(
            vendor_rows["vendor_reply_class"].map(normalize_text).str.contains("pattern_positive", na=False).sum()
        )
        vendor_likely = int(
            vendor_rows["vendor_reply_class"].map(normalize_text).str.contains("likely_positive", na=False).sum()
        )
        vendor_rejected = int(
            vendor_rows["vendor_reply_class"].map(normalize_text).str.contains("rejected", na=False).sum()
        )
        vendor_confirmed = int(vendor_rows["field_confirmed_flag"].sum()) if not vendor_rows.empty else 0
        vendor_bucket = vendor_support_bucket(vendor_rows)
        raw_attached = int(normalize_text(row["attachment_status"]) == "raw_source_trace_attached")
        common_days = numeric_int(row["core_common_cause_flag_days"])
        artifact_days = numeric_int(row["core_measurement_artifact_hold_days"])
        counterexample_required = int("counterexample_guarded" in normalize_text(row["request_priority"]))
        common_candidate = int(common_days == 0)
        artifact_candidate = int(artifact_days == 0)
        counterexample_candidate = int(not counterexample_required)
        independent_met = int(vendor_confirmed > 0 or numeric_int(row["physical_or_maintenance_evidence_attached"]) > 0)
        clear_candidate = int(common_candidate and artifact_candidate and counterexample_candidate)
        bucket = classify_review_bucket(
            raw_attached,
            vendor_bucket,
            common_candidate,
            artifact_candidate,
            counterexample_required,
        )
        rows.append(
            {
                "owner_branch": owner_branch,
                "gap_review_row_id": f"BR097-VPCG-{idx:03d}",
                "source_attachment_row_id": normalize_text(row["attachment_row_id"]),
                "evidence_request_id": normalize_text(row["evidence_request_id"]),
                "source_confirmation_packet_row_id": normalize_text(row["source_confirmation_packet_row_id"]),
                "source_confirmation_family_id": normalize_text(row["source_confirmation_family_id"]),
                "site": site,
                "root_id": normalize_text(row["root_id"]),
                "panel_group_key": normalize_text(row["panel_group_key"]),
                "panel_id": panel_id,
                "request_priority": normalize_text(row["request_priority"]),
                "review_bucket": bucket,
                "raw_source_trace_attached": raw_attached,
                "raw_source_trace_status": normalize_text(row["attachment_status"]),
                "source_candidate_rows_attached": numeric_int(row["source_candidate_rows_attached"]),
                "daily_trace_rows": numeric_int(row["core_window_rows_attached"]),
                "core_signal_days_attached": numeric_int(row["core_signal_days_attached"]),
                "core_voltage_preserved_days_attached": numeric_int(row["core_voltage_preserved_days_attached"]),
                "raw_file_refs_found": numeric_int(row["raw_file_refs_found"]),
                "raw_file_refs_missing": numeric_int(row["raw_file_refs_missing"]),
                "vendor_exact_rows": int(len(vendor_rows)),
                "vendor_positive_pattern_rows": vendor_positive,
                "vendor_likely_positive_rows": vendor_likely,
                "vendor_rejected_rows": vendor_rejected,
                "vendor_field_confirmed_rows": vendor_confirmed,
                "vendor_fault_family_list": ";".join(
                    list(dict.fromkeys(vendor_rows["vendor_fault_family"].map(normalize_text).tolist()))
                )
                if not vendor_rows.empty
                else "",
                "vendor_support_bucket": vendor_bucket,
                "manual_site_context_rows": int(len(manual_rows)),
                "manual_site_exact_usable_rows": manual_site_exact_usable(manual_rows),
                "manual_site_usable_for_exact_validation": int(manual_site_exact_usable(manual_rows) > 0),
                "common_cause_flag_days": common_days,
                "measurement_artifact_hold_days": artifact_days,
                "counterexample_clearance_required": counterexample_required,
                "common_cause_data_clearance_candidate": common_candidate,
                "measurement_artifact_data_clearance_candidate": artifact_candidate,
                "counterexample_clearance_candidate": counterexample_candidate,
                "independent_physical_or_maintenance_confirmation_met": independent_met,
                "all_clearance_axes_candidate_met": clear_candidate,
                "evidence_ready_for_truth_use": 0,
                "positive_truth_candidate_approved": 0,
                "threshold_tuning_approved": 0,
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "recommended_next_action": recommended_action(bucket),
                "notes": "Gap review only; data-derived clearance candidates and vendor pattern support are not truth approval.",
            }
        )
    return pd.DataFrame(rows).reindex(columns=REVIEW_COLUMNS)


AXES = [
    (
        "raw_source_traceability",
        1,
        0,
        "raw/source support",
        "Raw/source trace closes traceability but is not independent confirmation.",
    ),
    (
        "vendor_exact_panel_support",
        0,
        0,
        "vendor/manual support",
        "Vendor pattern support is useful context, but field_confirmed_flag=0 is not physical confirmation.",
    ),
    (
        "direct_physical_or_maintenance_confirmation",
        1,
        1,
        "independent confirmation",
        "Confirmed truth needs exact-panel physical, electrical, inspection, maintenance, or repair evidence.",
    ),
    (
        "common_cause_clearance",
        1,
        0,
        "blocker clearance",
        "Common-cause context must be absent or explicitly reviewed before panel-local truth use.",
    ),
    (
        "measurement_artifact_clearance",
        1,
        0,
        "blocker clearance",
        "Measurement/data-artifact holds must be absent or explicitly reviewed before truth use.",
    ),
    (
        "counterexample_clearance",
        1,
        0,
        "counterexample clearance",
        "Same-root negative overlap requires explicit clearance before truth rebuild.",
    ),
]


def axis_status(axis: str, row: dict[str, object]) -> tuple[str, int, str]:
    if axis == "raw_source_traceability":
        count = numeric_int(row["raw_source_trace_attached"])
        return ("attached_support_only" if count else "missing", count, "review BR-096 raw/source attachment")
    if axis == "vendor_exact_panel_support":
        count = numeric_int(row["vendor_exact_rows"])
        if numeric_int(row["vendor_rejected_rows"]):
            return "vendor_rejected_or_none_visible", count, "hold unless new evidence overturns vendor rejection"
        if count:
            return "vendor_pattern_support_unconfirmed", count, "use only as context until field/physical confirmation exists"
        return "missing", 0, "collect exact-panel external/vendor/field evidence"
    if axis == "direct_physical_or_maintenance_confirmation":
        count = numeric_int(row["independent_physical_or_maintenance_confirmation_met"])
        return ("met" if count else "missing", count, "attach exact-panel physical measurement or maintenance record")
    if axis == "common_cause_clearance":
        count = numeric_int(row["common_cause_data_clearance_candidate"])
        if count:
            return "data_clearance_candidate", count, "review data-derived no-common-cause candidate before truth use"
        return "hold_needs_review", numeric_int(row["common_cause_flag_days"]), "review common-cause flagged days"
    if axis == "measurement_artifact_clearance":
        count = numeric_int(row["measurement_artifact_data_clearance_candidate"])
        if count:
            return "data_clearance_candidate", count, "review data-derived no-artifact candidate before truth use"
        return "hold_needs_review", numeric_int(row["measurement_artifact_hold_days"]), "review measurement/data-artifact hold days"
    if axis == "counterexample_clearance":
        required = numeric_int(row["counterexample_clearance_required"])
        if not required:
            return "not_required", 0, "no same-root counterexample guard on this row"
        return "required_missing", 0, "attach explicit counterexample clearance decision"
    return "unknown", 0, "review manually"


def build_checklist(owner_branch: str, review_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in review_df.to_dict(orient="records"):
        for idx, (axis, required, independent, source, why) in enumerate(AXES, start=1):
            status, count, next_action = axis_status(axis, row)
            gap_id = normalize_text(row["gap_review_row_id"])
            rows.append(
                {
                    "owner_branch": owner_branch,
                    "gap_review_row_id": gap_id,
                    "checklist_row_id": f"{gap_id}-AX{idx:02d}",
                    "evidence_request_id": normalize_text(row["evidence_request_id"]),
                    "site": normalize_text(row["site"]),
                    "panel_id": normalize_text(row["panel_id"]),
                    "confirmation_axis": axis,
                    "axis_status": status,
                    "axis_required_for_truth_use": required,
                    "satisfies_independent_confirmation": independent if status == "met" else 0,
                    "supporting_row_count": count,
                    "support_source": source,
                    "why_it_matters": why,
                    "next_action": next_action,
                    "operator_facing_change_allowed": 0,
                    "engine_patch_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "notes": "Checklist status is review guidance only, not an approval.",
                }
            )
    return pd.DataFrame(rows).reindex(columns=CHECKLIST_COLUMNS)


def summarize_group(owner_branch: str, scope: str, key: str, df: pd.DataFrame) -> dict[str, object]:
    if df.empty:
        return {col: 0 for col in SUMMARY_COLUMNS} | {
            "owner_branch": owner_branch,
            "summary_scope": scope,
            "summary_key": key,
            "notes": "empty",
        }
    return {
        "owner_branch": owner_branch,
        "summary_scope": scope,
        "summary_key": key,
        "review_rows": int(len(df)),
        "raw_source_trace_attached_rows": int(df["raw_source_trace_attached"].sum()),
        "vendor_exact_support_rows": int((df["vendor_exact_rows"] > 0).sum()),
        "vendor_positive_or_likely_rows": int(
            ((df["vendor_positive_pattern_rows"] + df["vendor_likely_positive_rows"]) > 0).sum()
        ),
        "vendor_rejected_rows": int((df["vendor_rejected_rows"] > 0).sum()),
        "vendor_field_confirmed_rows": int((df["vendor_field_confirmed_rows"] > 0).sum()),
        "manual_site_context_rows_sum": int(df["manual_site_context_rows"].sum()),
        "common_cause_data_clearance_candidate_rows": int(df["common_cause_data_clearance_candidate"].sum()),
        "measurement_artifact_data_clearance_candidate_rows": int(
            df["measurement_artifact_data_clearance_candidate"].sum()
        ),
        "counterexample_clearance_required_rows": int(df["counterexample_clearance_required"].sum()),
        "independent_confirmation_met_rows": int(df["independent_physical_or_maintenance_confirmation_met"].sum()),
        "all_clearance_axes_candidate_met_rows": int(df["all_clearance_axes_candidate_met"].sum()),
        "evidence_ready_for_truth_use_sum": int(df["evidence_ready_for_truth_use"].sum()),
        "positive_truth_candidate_approved_sum": int(df["positive_truth_candidate_approved"].sum()),
        "threshold_tuning_approved_sum": int(df["threshold_tuning_approved"].sum()),
        "operator_facing_change_allowed_sum": int(df["operator_facing_change_allowed"].sum()),
        "engine_patch_allowed_sum": int(df["engine_patch_allowed"].sum()),
        "threshold_patch_allowed_sum": int(df["threshold_patch_allowed"].sum()),
        "notes": "vendor support and data-clearance candidates are not truth approval",
    }


def build_summary(owner_branch: str, review_df: pd.DataFrame) -> pd.DataFrame:
    rows = [summarize_group(owner_branch, "overall", "all", review_df)]
    for site, group in review_df.groupby("site", sort=True):
        rows.append(summarize_group(owner_branch, "site", site, group))
    for bucket, group in review_df.groupby("review_bucket", sort=True):
        rows.append(summarize_group(owner_branch, "review_bucket", bucket, group))
    return pd.DataFrame(rows).reindex(columns=SUMMARY_COLUMNS)


def build_action_queue(owner_branch: str, review_df: pd.DataFrame) -> pd.DataFrame:
    vendor_supported = int(
        ((review_df["vendor_positive_pattern_rows"] + review_df["vendor_likely_positive_rows"]) > 0).sum()
    )
    blockers = int(
        (
            (review_df["common_cause_data_clearance_candidate"].eq(0))
            | (review_df["measurement_artifact_data_clearance_candidate"].eq(0))
            | (review_df["counterexample_clearance_required"].eq(1))
        ).sum()
    )
    rows = [
        {
            "owner_branch": owner_branch,
            "sequence": 1,
            "action_id": "BR097-ACT-001",
            "action": "review vendor-supported unconfirmed rows",
            "input_filter": "vendor_positive_pattern_rows + vendor_likely_positive_rows > 0",
            "purpose": "separate useful external pattern support from field-confirmed physical evidence",
            "success_boundary": f"vendor-supported rows={vendor_supported}; field-confirmed rows remain explicit",
            "recommended_next_artifact": "voltage_preserved_independent_confirmation_attachment_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Vendor pattern support is not a truth label without physical/field confirmation.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 2,
            "action_id": "BR097-ACT-002",
            "action": "clear blocker-held rows",
            "input_filter": "common-cause, artifact, or counterexample blocker present",
            "purpose": "prevent raw/source-supported morphology from becoming truth while blockers remain open",
            "success_boundary": f"blocker-held rows={blockers}; approvals remain 0",
            "recommended_next_artifact": "voltage_preserved_blocker_clearance_attachment_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Counterexample guarded rows require an explicit clearance decision.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 3,
            "action_id": "BR097-ACT-003",
            "action": "collect exact-panel physical or maintenance records",
            "input_filter": "independent_physical_or_maintenance_confirmation_met=0",
            "purpose": "close the remaining independent confirmation gap before truth rebuild",
            "success_boundary": "truth rebuild remains blocked until independent confirmation rows are explicitly attached",
            "recommended_next_artifact": "voltage_preserved_independent_confirmation_attachment_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "This is the main remaining bottleneck after BR-097.",
        },
    ]
    return pd.DataFrame(rows).reindex(columns=ACTION_COLUMNS)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_empty_"
    lines = [
        "| " + " | ".join(str(col) for col in df.columns) + " |",
        "| " + " | ".join(["---"] * len(df.columns)) + " |",
    ]
    for row in df.to_dict(orient="records"):
        values = [normalize_text(row.get(col)) for col in df.columns]
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in values) + " |")
    return "\n".join(lines)


def write_note(path: Path, owner_branch: str, attachment_input: Path, vendor_input: Path, review_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    bucket_counts = review_df["review_bucket"].value_counts().sort_index().to_dict() if not review_df.empty else {}
    summary_cols = [
        "summary_scope",
        "summary_key",
        "review_rows",
        "vendor_exact_support_rows",
        "vendor_positive_or_likely_rows",
        "vendor_rejected_rows",
        "common_cause_data_clearance_candidate_rows",
        "measurement_artifact_data_clearance_candidate_rows",
        "counterexample_clearance_required_rows",
        "independent_confirmation_met_rows",
        "evidence_ready_for_truth_use_sum",
        "engine_patch_allowed_sum",
    ]
    lines = [
        "# panel_day_engine_voltage_preserved_confirmation_gap_review_v1",
        "",
        "## Purpose",
        "- Review the remaining independent-confirmation and blocker-clearance gaps after BR-096 raw/source attachment.",
        "- Keep vendor/manual support, data-derived clearance candidates, and truth approvals as separate layers.",
        "- Keep threshold, operator-facing, and engine approvals blocked.",
        "",
        "## Inputs",
        f"- BR-096 attachment: `{attachment_input}`",
        f"- vendor/manual evidence: `{vendor_input}`",
        "",
        "## Real Result",
        f"- owner_branch: `{owner_branch}`",
        f"- review rows: `{len(review_df)}`",
        f"- review bucket counts: `{json.dumps(bucket_counts, ensure_ascii=False, sort_keys=True)}`",
        f"- raw source attached rows: `{int(review_df['raw_source_trace_attached'].sum()) if not review_df.empty else 0}`",
        f"- vendor exact support rows: `{int((review_df['vendor_exact_rows'] > 0).sum()) if not review_df.empty else 0}`",
        f"- vendor positive/likely rows: `{int(((review_df['vendor_positive_pattern_rows'] + review_df['vendor_likely_positive_rows']) > 0).sum()) if not review_df.empty else 0}`",
        f"- vendor field-confirmed rows: `{int((review_df['vendor_field_confirmed_rows'] > 0).sum()) if not review_df.empty else 0}`",
        f"- all-clearance candidate rows: `{int(review_df['all_clearance_axes_candidate_met'].sum()) if not review_df.empty else 0}`",
        f"- independent confirmation met rows: `{int(review_df['independent_physical_or_maintenance_confirmation_met'].sum()) if not review_df.empty else 0}`",
        f"- evidence ready for truth use sum: `{int(review_df['evidence_ready_for_truth_use'].sum()) if not review_df.empty else 0}`",
        f"- threshold tuning approved sum: `{int(review_df['threshold_tuning_approved'].sum()) if not review_df.empty else 0}`",
        f"- engine patch allowed sum: `{int(review_df['engine_patch_allowed'].sum()) if not review_df.empty else 0}`",
        "",
        "## Summary",
        dataframe_to_markdown(summary_df.loc[:, summary_cols] if not summary_df.empty else summary_df),
        "",
        "## Safety Boundary",
        "- BR-097 is a gap review only.",
        "- Vendor pattern support is not field confirmation when `field_confirmed_flag=0`.",
        "- Data-derived blocker clearance candidates are not truth approvals.",
        "- No truth rebuild, threshold replay, operator-facing promotion, or direct `panel_day_engine.py` edit is approved.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(
    path: Path,
    owner_branch: str,
    repo_root: Path,
    output_dir: Path,
    attachment_input: Path,
    daily_input: Path,
    vendor_input: Path,
    manual_site_input: Path,
    review_df: pd.DataFrame,
    checklist_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    payload: dict[str, Any] = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "attachment_input": str(attachment_input),
        "daily_input": str(daily_input),
        "vendor_input": str(vendor_input),
        "manual_site_input": str(manual_site_input),
        "review_rows": int(len(review_df)),
        "checklist_rows": int(len(checklist_df)),
        "summary_rows": int(len(summary_df)),
        "review_bucket_counts": review_df["review_bucket"].value_counts().sort_index().to_dict()
        if not review_df.empty
        else {},
        "raw_source_attached_rows": int(review_df["raw_source_trace_attached"].sum()) if not review_df.empty else 0,
        "vendor_exact_support_rows": int((review_df["vendor_exact_rows"] > 0).sum()) if not review_df.empty else 0,
        "vendor_positive_or_likely_rows": int(
            ((review_df["vendor_positive_pattern_rows"] + review_df["vendor_likely_positive_rows"]) > 0).sum()
        )
        if not review_df.empty
        else 0,
        "vendor_field_confirmed_rows": int((review_df["vendor_field_confirmed_rows"] > 0).sum())
        if not review_df.empty
        else 0,
        "common_cause_data_clearance_candidate_rows": int(review_df["common_cause_data_clearance_candidate"].sum())
        if not review_df.empty
        else 0,
        "measurement_artifact_data_clearance_candidate_rows": int(
            review_df["measurement_artifact_data_clearance_candidate"].sum()
        )
        if not review_df.empty
        else 0,
        "counterexample_clearance_required_rows": int(review_df["counterexample_clearance_required"].sum())
        if not review_df.empty
        else 0,
        "independent_confirmation_met_rows": int(
            review_df["independent_physical_or_maintenance_confirmation_met"].sum()
        )
        if not review_df.empty
        else 0,
        "evidence_ready_for_truth_use_sum": int(review_df["evidence_ready_for_truth_use"].sum())
        if not review_df.empty
        else 0,
        "threshold_tuning_approved_sum": int(review_df["threshold_tuning_approved"].sum())
        if not review_df.empty
        else 0,
        "engine_patch_allowed_sum": int(review_df["engine_patch_allowed"].sum()) if not review_df.empty else 0,
        "recommended_next_branch": "voltage_preserved_independent_confirmation_attachment_v1",
        "outputs": {
            "review": str(output_dir / REVIEW_OUTPUT_NAME),
            "checklist": str(output_dir / CHECKLIST_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Review remaining confirmation and blocker gaps after BR-096 voltage-preserved raw/source attachment."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--attachment-dir", default=DEFAULT_ATTACHMENT_DIR, help="BR-096 attachment output dir.")
    parser.add_argument("--attachment-input", default="", help="Optional direct BR-096 attachment index CSV.")
    parser.add_argument("--daily-trace-input", default="", help="Optional direct BR-096 daily trace CSV.")
    parser.add_argument("--vendor-input", default=DEFAULT_VENDOR_INPUT, help="Exact-panel vendor/manual reply CSV.")
    parser.add_argument("--manual-site-input", default=DEFAULT_MANUAL_SITE_INPUT, help="Site-level manual evidence CSV.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory for BR-097 artifacts.")
    parser.add_argument("--owner-branch", default="BR-20260425-097")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    attachment_dir = resolve_path(repo_root, args.attachment_dir)
    attachment_input = (
        resolve_path(repo_root, args.attachment_input)
        if normalize_text(args.attachment_input)
        else attachment_dir / ATTACHMENT_INPUT_NAME
    )
    daily_input = (
        resolve_path(repo_root, args.daily_trace_input)
        if normalize_text(args.daily_trace_input)
        else attachment_dir / DAILY_TRACE_INPUT_NAME
    )
    vendor_input = resolve_path(repo_root, args.vendor_input)
    manual_site_input = resolve_path(repo_root, args.manual_site_input)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    attachment_df = normalize_attachment(read_required_csv(attachment_input, ATTACHMENT_REQUIRED_COLUMNS, "BR-096 attachment"))
    daily_df = read_required_csv(daily_input, DAILY_REQUIRED_COLUMNS, "BR-096 daily trace")
    vendor_df = normalize_vendor(read_required_csv(vendor_input, VENDOR_REQUIRED_COLUMNS, "vendor evidence"))
    manual_site_df = normalize_manual_site(
        read_required_csv(manual_site_input, MANUAL_SITE_REQUIRED_COLUMNS, "manual site evidence")
    )
    assert_safe_input(attachment_df, daily_df)

    review_df = build_review(args.owner_branch, attachment_df, vendor_df, manual_site_df)
    checklist_df = build_checklist(args.owner_branch, review_df)
    summary_df = build_summary(args.owner_branch, review_df)
    action_df = build_action_queue(args.owner_branch, review_df)

    review_df.to_csv(output_dir / REVIEW_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    checklist_df.to_csv(output_dir / CHECKLIST_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir / NOTE_OUTPUT_NAME, args.owner_branch, attachment_input, vendor_input, review_df, summary_df)
    write_json(
        output_dir / JSON_OUTPUT_NAME,
        args.owner_branch,
        repo_root,
        output_dir,
        attachment_input,
        daily_input,
        vendor_input,
        manual_site_input,
        review_df,
        checklist_df,
        summary_df,
    )

    print(
        json.dumps(
            {
                "owner_branch": args.owner_branch,
                "review_rows": int(len(review_df)),
                "checklist_rows": int(len(checklist_df)),
                "summary_rows": int(len(summary_df)),
                "review_bucket_counts": review_df["review_bucket"].value_counts().sort_index().to_dict()
                if not review_df.empty
                else {},
                "raw_source_attached_rows": int(review_df["raw_source_trace_attached"].sum())
                if not review_df.empty
                else 0,
                "vendor_exact_support_rows": int((review_df["vendor_exact_rows"] > 0).sum())
                if not review_df.empty
                else 0,
                "vendor_positive_or_likely_rows": int(
                    ((review_df["vendor_positive_pattern_rows"] + review_df["vendor_likely_positive_rows"]) > 0).sum()
                )
                if not review_df.empty
                else 0,
                "vendor_field_confirmed_rows": int((review_df["vendor_field_confirmed_rows"] > 0).sum())
                if not review_df.empty
                else 0,
                "independent_confirmation_met_rows": int(
                    review_df["independent_physical_or_maintenance_confirmation_met"].sum()
                )
                if not review_df.empty
                else 0,
                "evidence_ready_for_truth_use_sum": int(review_df["evidence_ready_for_truth_use"].sum())
                if not review_df.empty
                else 0,
                "threshold_tuning_approved_sum": int(review_df["threshold_tuning_approved"].sum())
                if not review_df.empty
                else 0,
                "outputs": {
                    "review": str(output_dir / REVIEW_OUTPUT_NAME),
                    "checklist": str(output_dir / CHECKLIST_OUTPUT_NAME),
                    "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
                    "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
                    "note": str(output_dir / NOTE_OUTPUT_NAME),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
