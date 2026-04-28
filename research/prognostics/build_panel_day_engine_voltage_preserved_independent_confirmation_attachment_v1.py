#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


GAP_REVIEW_INPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_gap_review_v1.csv"

ATTACHMENT_OUTPUT_NAME = "panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.csv"
SOURCE_SCAN_OUTPUT_NAME = "panel_day_engine_voltage_preserved_independent_confirmation_source_scan_v1.csv"
CLEARANCE_OUTPUT_NAME = "panel_day_engine_voltage_preserved_blocker_clearance_attachment_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_voltage_preserved_independent_confirmation_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_voltage_preserved_independent_confirmation_action_queue_v1.csv"
INDEPENDENT_TEMPLATE_OUTPUT_NAME = "panel_day_engine_voltage_preserved_independent_confirmation_input_template_v1.csv"
CLEARANCE_TEMPLATE_OUTPUT_NAME = "panel_day_engine_voltage_preserved_blocker_clearance_input_template_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_voltage_preserved_independent_confirmation_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.json"

DEFAULT_GAP_REVIEW_DIR = "/private/tmp/panel_day_engine_voltage_preserved_confirmation_gap_review_br097_check"
DEFAULT_VENDOR_INPUT = str(Path(__file__).resolve().parents[2] / "data" / "manual" / "vendor_reply_cases.csv")
DEFAULT_MANUAL_SITE_INPUT = "docs/internal/manual_field_evidence_latest.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/panel_day_engine_voltage_preserved_independent_confirmation_br098_check"

GAP_REVIEW_REQUIRED_COLUMNS = [
    "gap_review_row_id",
    "evidence_request_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "request_priority",
    "review_bucket",
    "raw_source_trace_attached",
    "vendor_exact_rows",
    "vendor_positive_pattern_rows",
    "vendor_likely_positive_rows",
    "vendor_rejected_rows",
    "vendor_field_confirmed_rows",
    "common_cause_data_clearance_candidate",
    "measurement_artifact_data_clearance_candidate",
    "counterexample_clearance_required",
    "independent_physical_or_maintenance_confirmation_met",
    "evidence_ready_for_truth_use",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
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

INDEPENDENT_INPUT_COLUMNS = [
    "site",
    "panel_id",
    "evidence_type",
    "evidence_status",
    "evidence_date",
    "evidence_path",
    "evidence_note",
    "reviewer",
]

CLEARANCE_INPUT_COLUMNS = [
    "site",
    "panel_id",
    "clearance_axis",
    "clearance_status",
    "clearance_date",
    "clearance_evidence_path",
    "clearance_note",
    "reviewer",
]

ATTACHMENT_COLUMNS = [
    "owner_branch",
    "attachment_row_id",
    "gap_review_row_id",
    "evidence_request_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "request_priority",
    "review_bucket",
    "raw_source_trace_attached",
    "exact_vendor_rows",
    "exact_vendor_positive_or_likely_rows",
    "exact_vendor_rejected_rows",
    "exact_vendor_field_confirmed_rows",
    "same_site_reference_field_confirmed_rows",
    "manual_site_context_rows",
    "manual_site_exact_usable_rows",
    "exact_independent_evidence_rows",
    "exact_physical_measurement_rows",
    "exact_maintenance_or_inspection_rows",
    "independent_confirmation_attached",
    "independent_confirmation_status",
    "common_cause_data_clearance_candidate",
    "measurement_artifact_data_clearance_candidate",
    "counterexample_clearance_required",
    "explicit_common_cause_clearance_attached",
    "explicit_measurement_artifact_clearance_attached",
    "explicit_counterexample_clearance_attached",
    "all_required_clearances_attached",
    "truth_intake_ready",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "recommended_next_action",
    "notes",
]

SOURCE_SCAN_COLUMNS = [
    "owner_branch",
    "source_scan_row_id",
    "gap_review_row_id",
    "evidence_request_id",
    "site",
    "panel_id",
    "source_type",
    "source_rows",
    "exact_panel_match",
    "independent_confirmation_role",
    "usable_for_truth_intake",
    "support_status",
    "notes",
]

CLEARANCE_COLUMNS = [
    "owner_branch",
    "clearance_row_id",
    "gap_review_row_id",
    "evidence_request_id",
    "site",
    "panel_id",
    "review_bucket",
    "common_cause_data_clearance_candidate",
    "measurement_artifact_data_clearance_candidate",
    "counterexample_clearance_required",
    "explicit_common_cause_clearance_attached",
    "explicit_measurement_artifact_clearance_attached",
    "explicit_counterexample_clearance_attached",
    "all_required_clearances_attached",
    "clearance_status",
    "recommended_next_action",
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
    "exact_vendor_support_rows",
    "exact_vendor_positive_or_likely_rows",
    "exact_vendor_field_confirmed_rows",
    "same_site_reference_field_confirmed_rows",
    "manual_site_exact_usable_rows",
    "exact_independent_evidence_rows",
    "independent_confirmation_attached_rows",
    "data_clearance_candidate_rows",
    "explicit_all_clearance_rows",
    "counterexample_clearance_required_rows",
    "truth_intake_ready_rows",
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

INDEPENDENT_TYPES = {
    "physical_measurement",
    "iv_curve",
    "string_trace",
    "inverter_trace",
    "maintenance_record",
    "inspection_record",
    "repair_record",
    "field_confirmation",
}

INDEPENDENT_STATUSES = {
    "confirmed",
    "field_confirmed",
    "attached_confirmed",
    "reviewed_positive",
}

CLEARANCE_AXES = {
    "common_cause_clearance",
    "measurement_artifact_clearance",
    "counterexample_clearance",
}

CLEARANCE_STATUSES = {
    "cleared",
    "reviewed_clear",
    "attached_clear",
}


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


def read_optional_csv(path: Path, required_cols: list[str], name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=required_cols)
    return read_required_csv(path, required_cols, name)


def normalize_frame(df: pd.DataFrame, text_cols: set[str], numeric_cols: set[str]) -> pd.DataFrame:
    out = df.copy()
    for col in text_cols:
        if col in out.columns:
            out[col] = out[col].map(normalize_text)
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    return out


def normalize_gap_review(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = {
        "raw_source_trace_attached",
        "vendor_exact_rows",
        "vendor_positive_pattern_rows",
        "vendor_likely_positive_rows",
        "vendor_rejected_rows",
        "vendor_field_confirmed_rows",
        "common_cause_data_clearance_candidate",
        "measurement_artifact_data_clearance_candidate",
        "counterexample_clearance_required",
        "independent_physical_or_maintenance_confirmation_met",
        "evidence_ready_for_truth_use",
        "positive_truth_candidate_approved",
        "threshold_tuning_approved",
        "operator_facing_change_allowed",
        "engine_patch_allowed",
        "threshold_patch_allowed",
    }
    out = normalize_frame(df, set(GAP_REVIEW_REQUIRED_COLUMNS) - numeric_cols, numeric_cols)
    return out.sort_values(["site", "root_id", "panel_group_key", "panel_id"]).reset_index(drop=True)


def normalize_vendor(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = {"field_confirmed_flag", "adjudication_weight"}
    return normalize_frame(df, set(VENDOR_REQUIRED_COLUMNS) - numeric_cols, numeric_cols)


def normalize_manual_site(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = {"related_panel_count"}
    return normalize_frame(df, set(MANUAL_SITE_REQUIRED_COLUMNS) - numeric_cols, numeric_cols)


def normalize_independent(df: pd.DataFrame) -> pd.DataFrame:
    return normalize_frame(df, set(INDEPENDENT_INPUT_COLUMNS), set())


def normalize_clearance(df: pd.DataFrame) -> pd.DataFrame:
    return normalize_frame(df, set(CLEARANCE_INPUT_COLUMNS), set())


def assert_safe_start(review_df: pd.DataFrame) -> None:
    for col in [
        "evidence_ready_for_truth_use",
        "positive_truth_candidate_approved",
        "threshold_tuning_approved",
        "operator_facing_change_allowed",
        "engine_patch_allowed",
        "threshold_patch_allowed",
    ]:
        total = int(pd.to_numeric(review_df[col], errors="coerce").fillna(0).sum())
        if total != 0:
            raise ValueError(f"BR-098 must start from non-authorizing BR-097 output; {col} sum is {total}")


def independent_usable_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    evidence_type = df["evidence_type"].map(normalize_text).str.lower()
    evidence_status = df["evidence_status"].map(normalize_text).str.lower()
    evidence_path = df["evidence_path"].map(normalize_text)
    usable = evidence_type.isin(INDEPENDENT_TYPES) & evidence_status.isin(INDEPENDENT_STATUSES) & evidence_path.ne("")
    return df.loc[usable].copy()


def clearance_usable_rows(df: pd.DataFrame, axis: str) -> pd.DataFrame:
    if df.empty:
        return df
    clearance_axis = df["clearance_axis"].map(normalize_text).str.lower()
    clearance_status = df["clearance_status"].map(normalize_text).str.lower()
    evidence_path = df["clearance_evidence_path"].map(normalize_text)
    usable = clearance_axis.eq(axis) & clearance_status.isin(CLEARANCE_STATUSES) & evidence_path.ne("")
    return df.loc[usable].copy()


def recommended_attachment_action(independent_attached: int, vendor_positive: int, rejected: int) -> str:
    if independent_attached:
        return "review attached independent evidence, then attach explicit blocker clearances before truth intake"
    if vendor_positive:
        return "collect exact-panel physical measurement, IV curve, maintenance, inspection, or repair evidence"
    if rejected:
        return "hold unless new exact-panel independent evidence overturns vendor rejection"
    return "collect exact-panel independent evidence; raw/source trace remains support-only"


def clearance_status(common_attached: int, artifact_attached: int, counter_required: int, counter_attached: int) -> str:
    if counter_required and not counter_attached:
        return "counterexample_clearance_missing"
    if not common_attached or not artifact_attached:
        return "explicit_blocker_clearance_missing"
    return "all_required_clearances_attached"


def build_attachment(
    owner_branch: str,
    review_df: pd.DataFrame,
    vendor_df: pd.DataFrame,
    manual_site_df: pd.DataFrame,
    independent_df: pd.DataFrame,
    clearance_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(review_df.to_dict(orient="records"), start=1):
        site = normalize_text(row["site"])
        panel_id = normalize_text(row["panel_id"])
        exact_vendor = vendor_df.loc[vendor_df["site"].eq(site) & vendor_df["panel_id"].eq(panel_id)].copy()
        same_site_reference = vendor_df.loc[
            vendor_df["site"].eq(site)
            & vendor_df["panel_id"].ne(panel_id)
            & pd.to_numeric(vendor_df["field_confirmed_flag"], errors="coerce").fillna(0).gt(0)
        ].copy()
        manual_rows = manual_site_df.loc[manual_site_df["site"].eq(site)].copy()
        independent_rows = independent_usable_rows(
            independent_df.loc[independent_df["site"].eq(site) & independent_df["panel_id"].eq(panel_id)].copy()
        )
        physical_rows = independent_rows.loc[
            independent_rows["evidence_type"].map(normalize_text).str.lower().isin(
                {"physical_measurement", "iv_curve", "string_trace", "inverter_trace", "field_confirmation"}
            )
        ]
        maintenance_rows = independent_rows.loc[
            independent_rows["evidence_type"].map(normalize_text).str.lower().isin(
                {"maintenance_record", "inspection_record", "repair_record"}
            )
        ]
        exact_vendor_confirmed = int(pd.to_numeric(exact_vendor["field_confirmed_flag"], errors="coerce").fillna(0).sum())
        vendor_positive = int(
            exact_vendor["vendor_reply_class"].map(normalize_text).str.contains("positive", na=False).sum()
        )
        vendor_rejected = int(
            exact_vendor["vendor_reply_class"].map(normalize_text).str.contains("rejected", na=False).sum()
        )
        independent_attached = int(exact_vendor_confirmed > 0 or len(independent_rows) > 0)
        common_attached = int(
            len(
                clearance_usable_rows(
                    clearance_df.loc[clearance_df["site"].eq(site) & clearance_df["panel_id"].eq(panel_id)].copy(),
                    "common_cause_clearance",
                )
            )
            > 0
        )
        artifact_attached = int(
            len(
                clearance_usable_rows(
                    clearance_df.loc[clearance_df["site"].eq(site) & clearance_df["panel_id"].eq(panel_id)].copy(),
                    "measurement_artifact_clearance",
                )
            )
            > 0
        )
        counter_attached = int(
            len(
                clearance_usable_rows(
                    clearance_df.loc[clearance_df["site"].eq(site) & clearance_df["panel_id"].eq(panel_id)].copy(),
                    "counterexample_clearance",
                )
            )
            > 0
        )
        counter_required = numeric_int(row["counterexample_clearance_required"])
        all_clearances = int(common_attached and artifact_attached and (not counter_required or counter_attached))
        truth_ready = int(independent_attached and all_clearances)
        rows.append(
            {
                "owner_branch": owner_branch,
                "attachment_row_id": f"BR098-VPIC-{idx:03d}",
                "gap_review_row_id": normalize_text(row["gap_review_row_id"]),
                "evidence_request_id": normalize_text(row["evidence_request_id"]),
                "site": site,
                "root_id": normalize_text(row["root_id"]),
                "panel_group_key": normalize_text(row["panel_group_key"]),
                "panel_id": panel_id,
                "request_priority": normalize_text(row["request_priority"]),
                "review_bucket": normalize_text(row["review_bucket"]),
                "raw_source_trace_attached": numeric_int(row["raw_source_trace_attached"]),
                "exact_vendor_rows": int(len(exact_vendor)),
                "exact_vendor_positive_or_likely_rows": vendor_positive,
                "exact_vendor_rejected_rows": vendor_rejected,
                "exact_vendor_field_confirmed_rows": exact_vendor_confirmed,
                "same_site_reference_field_confirmed_rows": int(len(same_site_reference)),
                "manual_site_context_rows": int(len(manual_rows)),
                "manual_site_exact_usable_rows": int(
                    manual_rows["usable_for_exact_validation"].map(normalize_text).str.lower().isin({"yes", "true", "1"}).sum()
                )
                if not manual_rows.empty
                else 0,
                "exact_independent_evidence_rows": int(len(independent_rows)),
                "exact_physical_measurement_rows": int(len(physical_rows)),
                "exact_maintenance_or_inspection_rows": int(len(maintenance_rows)),
                "independent_confirmation_attached": independent_attached,
                "independent_confirmation_status": "attached" if independent_attached else "missing",
                "common_cause_data_clearance_candidate": numeric_int(row["common_cause_data_clearance_candidate"]),
                "measurement_artifact_data_clearance_candidate": numeric_int(
                    row["measurement_artifact_data_clearance_candidate"]
                ),
                "counterexample_clearance_required": counter_required,
                "explicit_common_cause_clearance_attached": common_attached,
                "explicit_measurement_artifact_clearance_attached": artifact_attached,
                "explicit_counterexample_clearance_attached": counter_attached,
                "all_required_clearances_attached": all_clearances,
                "truth_intake_ready": truth_ready,
                "positive_truth_candidate_approved": 0,
                "threshold_tuning_approved": 0,
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "recommended_next_action": recommended_attachment_action(independent_attached, vendor_positive, vendor_rejected),
                "notes": "Exact independent evidence and explicit clearances are required before truth intake.",
            }
        )
    return pd.DataFrame(rows).reindex(columns=ATTACHMENT_COLUMNS)


def build_source_scan(
    owner_branch: str,
    review_df: pd.DataFrame,
    vendor_df: pd.DataFrame,
    manual_site_df: pd.DataFrame,
    independent_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    idx = 1
    for row in review_df.to_dict(orient="records"):
        site = normalize_text(row["site"])
        panel_id = normalize_text(row["panel_id"])
        gap_id = normalize_text(row["gap_review_row_id"])
        request_id = normalize_text(row["evidence_request_id"])
        exact_vendor = vendor_df.loc[vendor_df["site"].eq(site) & vendor_df["panel_id"].eq(panel_id)].copy()
        vendor_confirmed = int(pd.to_numeric(exact_vendor["field_confirmed_flag"], errors="coerce").fillna(0).sum())
        vendor_positive = int(
            exact_vendor["vendor_reply_class"].map(normalize_text).str.contains("positive", na=False).sum()
        )
        manual_rows = manual_site_df.loc[manual_site_df["site"].eq(site)].copy()
        manual_usable = int(
            manual_rows["usable_for_exact_validation"].map(normalize_text).str.lower().isin({"yes", "true", "1"}).sum()
        ) if not manual_rows.empty else 0
        same_site_reference = vendor_df.loc[
            vendor_df["site"].eq(site)
            & vendor_df["panel_id"].ne(panel_id)
            & pd.to_numeric(vendor_df["field_confirmed_flag"], errors="coerce").fillna(0).gt(0)
        ].copy()
        independent_rows = independent_usable_rows(
            independent_df.loc[independent_df["site"].eq(site) & independent_df["panel_id"].eq(panel_id)].copy()
        )
        scan_defs = [
            (
                "exact_vendor_reply",
                int(len(exact_vendor)),
                1,
                "field_confirmation" if vendor_confirmed else "context_only",
                int(vendor_confirmed > 0),
                "field_confirmed" if vendor_confirmed else ("pattern_context" if vendor_positive else "not_positive_or_missing"),
                "Exact vendor rows help only when field_confirmed_flag > 0.",
            ),
            (
                "manual_site_context",
                int(len(manual_rows)),
                0,
                "context_only",
                0,
                "site_context_only" if len(manual_rows) else "missing",
                f"Manual site rows exact-usable count={manual_usable}; no panel_id-level validation column is present.",
            ),
            (
                "same_site_field_confirmed_reference",
                int(len(same_site_reference)),
                0,
                "reference_only",
                0,
                "reference_only" if len(same_site_reference) else "missing",
                "Same-site confirmed cases are useful examples, not exact-panel confirmation.",
            ),
            (
                "exact_independent_evidence_input",
                int(len(independent_rows)),
                1,
                "independent_confirmation",
                int(len(independent_rows) > 0),
                "attached" if len(independent_rows) else "missing",
                "Optional independent evidence input can close this axis when exact-panel evidence is attached.",
            ),
        ]
        for source_type, count, exact_match, role, usable, status, notes in scan_defs:
            rows.append(
                {
                    "owner_branch": owner_branch,
                    "source_scan_row_id": f"BR098-VPIS-{idx:03d}",
                    "gap_review_row_id": gap_id,
                    "evidence_request_id": request_id,
                    "site": site,
                    "panel_id": panel_id,
                    "source_type": source_type,
                    "source_rows": count,
                    "exact_panel_match": exact_match,
                    "independent_confirmation_role": role,
                    "usable_for_truth_intake": usable,
                    "support_status": status,
                    "notes": notes,
                }
            )
            idx += 1
    return pd.DataFrame(rows).reindex(columns=SOURCE_SCAN_COLUMNS)


def build_clearance(owner_branch: str, attachment_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(attachment_df.to_dict(orient="records"), start=1):
        status = clearance_status(
            numeric_int(row["explicit_common_cause_clearance_attached"]),
            numeric_int(row["explicit_measurement_artifact_clearance_attached"]),
            numeric_int(row["counterexample_clearance_required"]),
            numeric_int(row["explicit_counterexample_clearance_attached"]),
        )
        if status == "all_required_clearances_attached":
            action = "review independent confirmation and move to a separate truth-intake gate if still warranted"
        elif status == "counterexample_clearance_missing":
            action = "attach explicit same-root counterexample clearance before truth intake"
        else:
            action = "attach explicit common-cause and measurement-artifact clearance review"
        rows.append(
            {
                "owner_branch": owner_branch,
                "clearance_row_id": f"BR098-VPBC-{idx:03d}",
                "gap_review_row_id": normalize_text(row["gap_review_row_id"]),
                "evidence_request_id": normalize_text(row["evidence_request_id"]),
                "site": normalize_text(row["site"]),
                "panel_id": normalize_text(row["panel_id"]),
                "review_bucket": normalize_text(row["review_bucket"]),
                "common_cause_data_clearance_candidate": numeric_int(row["common_cause_data_clearance_candidate"]),
                "measurement_artifact_data_clearance_candidate": numeric_int(
                    row["measurement_artifact_data_clearance_candidate"]
                ),
                "counterexample_clearance_required": numeric_int(row["counterexample_clearance_required"]),
                "explicit_common_cause_clearance_attached": numeric_int(
                    row["explicit_common_cause_clearance_attached"]
                ),
                "explicit_measurement_artifact_clearance_attached": numeric_int(
                    row["explicit_measurement_artifact_clearance_attached"]
                ),
                "explicit_counterexample_clearance_attached": numeric_int(
                    row["explicit_counterexample_clearance_attached"]
                ),
                "all_required_clearances_attached": numeric_int(row["all_required_clearances_attached"]),
                "clearance_status": status,
                "recommended_next_action": action,
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "notes": "Data-derived clearance candidates are not explicit clearance attachments.",
            }
        )
    return pd.DataFrame(rows).reindex(columns=CLEARANCE_COLUMNS)


def summarize_group(owner_branch: str, scope: str, key: str, df: pd.DataFrame) -> dict[str, object]:
    if df.empty:
        return {col: 0 for col in SUMMARY_COLUMNS} | {
            "owner_branch": owner_branch,
            "summary_scope": scope,
            "summary_key": key,
            "notes": "empty",
        }
    data_clearance = (
        df["common_cause_data_clearance_candidate"].astype(int).eq(1)
        & df["measurement_artifact_data_clearance_candidate"].astype(int).eq(1)
        & df["counterexample_clearance_required"].astype(int).eq(0)
    )
    return {
        "owner_branch": owner_branch,
        "summary_scope": scope,
        "summary_key": key,
        "review_rows": int(len(df)),
        "raw_source_trace_attached_rows": int(df["raw_source_trace_attached"].sum()),
        "exact_vendor_support_rows": int((df["exact_vendor_rows"] > 0).sum()),
        "exact_vendor_positive_or_likely_rows": int((df["exact_vendor_positive_or_likely_rows"] > 0).sum()),
        "exact_vendor_field_confirmed_rows": int((df["exact_vendor_field_confirmed_rows"] > 0).sum()),
        "same_site_reference_field_confirmed_rows": int((df["same_site_reference_field_confirmed_rows"] > 0).sum()),
        "manual_site_exact_usable_rows": int((df["manual_site_exact_usable_rows"] > 0).sum()),
        "exact_independent_evidence_rows": int((df["exact_independent_evidence_rows"] > 0).sum()),
        "independent_confirmation_attached_rows": int(df["independent_confirmation_attached"].sum()),
        "data_clearance_candidate_rows": int(data_clearance.sum()),
        "explicit_all_clearance_rows": int(df["all_required_clearances_attached"].sum()),
        "counterexample_clearance_required_rows": int(df["counterexample_clearance_required"].sum()),
        "truth_intake_ready_rows": int(df["truth_intake_ready"].sum()),
        "positive_truth_candidate_approved_sum": int(df["positive_truth_candidate_approved"].sum()),
        "threshold_tuning_approved_sum": int(df["threshold_tuning_approved"].sum()),
        "operator_facing_change_allowed_sum": int(df["operator_facing_change_allowed"].sum()),
        "engine_patch_allowed_sum": int(df["engine_patch_allowed"].sum()),
        "threshold_patch_allowed_sum": int(df["threshold_patch_allowed"].sum()),
        "notes": "truth intake remains blocked until independent evidence and explicit clearances are both attached",
    }


def build_summary(owner_branch: str, attachment_df: pd.DataFrame) -> pd.DataFrame:
    rows = [summarize_group(owner_branch, "overall", "all", attachment_df)]
    for site, group in attachment_df.groupby("site", sort=True):
        rows.append(summarize_group(owner_branch, "site", site, group))
    for bucket, group in attachment_df.groupby("review_bucket", sort=True):
        rows.append(summarize_group(owner_branch, "review_bucket", bucket, group))
    return pd.DataFrame(rows).reindex(columns=SUMMARY_COLUMNS)


def build_action_queue(owner_branch: str, attachment_df: pd.DataFrame) -> pd.DataFrame:
    vendor_positive = int((attachment_df["exact_vendor_positive_or_likely_rows"] > 0).sum())
    missing_independent = int(attachment_df["independent_confirmation_attached"].eq(0).sum())
    counter_required = int(attachment_df["counterexample_clearance_required"].sum())
    blocker_missing = int(attachment_df["all_required_clearances_attached"].eq(0).sum())
    rows = [
        {
            "owner_branch": owner_branch,
            "sequence": 1,
            "action_id": "BR098-ACT-001",
            "action": "fill exact-panel independent confirmation template",
            "input_filter": "independent_confirmation_attached=0",
            "purpose": "turn vendor/raw support into reviewable physical or maintenance evidence only when exact-panel records exist",
            "success_boundary": f"missing independent confirmation rows={missing_independent}; truth intake stays 0 until filled",
            "recommended_next_artifact": INDEPENDENT_TEMPLATE_OUTPUT_NAME,
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": f"Vendor positive/likely rows needing exact confirmation={vendor_positive}.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 2,
            "action_id": "BR098-ACT-002",
            "action": "fill explicit blocker clearance template",
            "input_filter": "all_required_clearances_attached=0",
            "purpose": "separate data-derived no-blocker candidates from explicit reviewer clearance",
            "success_boundary": f"rows missing explicit all-clearance={blocker_missing}; counterexample rows={counter_required}",
            "recommended_next_artifact": CLEARANCE_TEMPLATE_OUTPUT_NAME,
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Counterexample clearance is mandatory for the guarded gangui rows.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 3,
            "action_id": "BR098-ACT-003",
            "action": "rebuild BR-098 with filled templates before truth intake",
            "input_filter": "truth_intake_ready_rows should remain 0 until templates are populated",
            "purpose": "avoid converting support-only evidence into labels by implication",
            "success_boundary": "truth intake rows are created only by a later branch after explicit evidence attachment",
            "recommended_next_artifact": "voltage_preserved_confirmed_truth_intake_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "This branch is an attachment gate, not a label generator.",
        },
    ]
    return pd.DataFrame(rows).reindex(columns=ACTION_COLUMNS)


def build_independent_template(owner_branch: str, attachment_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in attachment_df.to_dict(orient="records"):
        rows.append(
            {
                "owner_branch": owner_branch,
                "gap_review_row_id": normalize_text(row["gap_review_row_id"]),
                "evidence_request_id": normalize_text(row["evidence_request_id"]),
                "site": normalize_text(row["site"]),
                "panel_id": normalize_text(row["panel_id"]),
                "evidence_type": "",
                "evidence_status": "",
                "evidence_date": "",
                "evidence_path": "",
                "evidence_note": "",
                "reviewer": "",
                "allowed_evidence_type_values": ";".join(sorted(INDEPENDENT_TYPES)),
                "allowed_confirmed_status_values": ";".join(sorted(INDEPENDENT_STATUSES)),
                "notes": "Fill only with exact-panel physical/electrical/maintenance/inspection/repair evidence.",
            }
        )
    return pd.DataFrame(rows)


def build_clearance_template(owner_branch: str, attachment_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in attachment_df.to_dict(orient="records"):
        for axis in sorted(CLEARANCE_AXES):
            rows.append(
                {
                    "owner_branch": owner_branch,
                    "gap_review_row_id": normalize_text(row["gap_review_row_id"]),
                    "evidence_request_id": normalize_text(row["evidence_request_id"]),
                    "site": normalize_text(row["site"]),
                    "panel_id": normalize_text(row["panel_id"]),
                    "clearance_axis": axis,
                    "clearance_status": "",
                    "clearance_date": "",
                    "clearance_evidence_path": "",
                    "clearance_note": "",
                    "reviewer": "",
                    "allowed_clear_status_values": ";".join(sorted(CLEARANCE_STATUSES)),
                    "notes": "Fill with explicit reviewer/evidence clearance; data-derived candidate flags are not enough.",
                }
            )
    return pd.DataFrame(rows)


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


def write_note(path: Path, owner_branch: str, gap_input: Path, attachment_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    summary_cols = [
        "summary_scope",
        "summary_key",
        "review_rows",
        "exact_vendor_positive_or_likely_rows",
        "exact_vendor_field_confirmed_rows",
        "same_site_reference_field_confirmed_rows",
        "independent_confirmation_attached_rows",
        "data_clearance_candidate_rows",
        "explicit_all_clearance_rows",
        "counterexample_clearance_required_rows",
        "truth_intake_ready_rows",
        "engine_patch_allowed_sum",
    ]
    lines = [
        "# panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1",
        "",
        "## Purpose",
        "- Attach exact-panel independent confirmation and explicit blocker-clearance evidence after BR-097.",
        "- Preserve the distinction between vendor/raw support, same-site references, and exact-panel confirmation.",
        "- Keep truth, threshold, operator-facing, and engine approvals blocked.",
        "",
        "## Inputs",
        f"- BR-097 gap review: `{gap_input}`",
        "",
        "## Real Result",
        f"- owner_branch: `{owner_branch}`",
        f"- attachment rows: `{len(attachment_df)}`",
        f"- exact vendor positive/likely rows: `{int((attachment_df['exact_vendor_positive_or_likely_rows'] > 0).sum()) if not attachment_df.empty else 0}`",
        f"- exact vendor field-confirmed rows: `{int((attachment_df['exact_vendor_field_confirmed_rows'] > 0).sum()) if not attachment_df.empty else 0}`",
        f"- same-site reference field-confirmed rows: `{int((attachment_df['same_site_reference_field_confirmed_rows'] > 0).sum()) if not attachment_df.empty else 0}`",
        f"- independent confirmation attached rows: `{int(attachment_df['independent_confirmation_attached'].sum()) if not attachment_df.empty else 0}`",
        f"- explicit all-clearance rows: `{int(attachment_df['all_required_clearances_attached'].sum()) if not attachment_df.empty else 0}`",
        f"- truth intake ready rows: `{int(attachment_df['truth_intake_ready'].sum()) if not attachment_df.empty else 0}`",
        f"- threshold tuning approved sum: `{int(attachment_df['threshold_tuning_approved'].sum()) if not attachment_df.empty else 0}`",
        f"- engine patch allowed sum: `{int(attachment_df['engine_patch_allowed'].sum()) if not attachment_df.empty else 0}`",
        "",
        "## Summary",
        dataframe_to_markdown(summary_df.loc[:, summary_cols] if not summary_df.empty else summary_df),
        "",
        "## Safety Boundary",
        "- Same-site field-confirmed examples are reference-only when panel_id does not match.",
        "- Vendor pattern support is not exact physical confirmation unless field confirmation or independent evidence is attached.",
        "- Data-derived clearance candidates are not explicit blocker clearance.",
        "- No truth rebuild, threshold replay, operator-facing promotion, or direct `panel_day_engine.py` edit is approved.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(
    path: Path,
    owner_branch: str,
    repo_root: Path,
    output_dir: Path,
    gap_input: Path,
    independent_input: Path | None,
    clearance_input: Path | None,
    attachment_df: pd.DataFrame,
    source_scan_df: pd.DataFrame,
    clearance_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    payload: dict[str, Any] = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "gap_review_input": str(gap_input),
        "independent_evidence_input": str(independent_input) if independent_input else "",
        "blocker_clearance_input": str(clearance_input) if clearance_input else "",
        "attachment_rows": int(len(attachment_df)),
        "source_scan_rows": int(len(source_scan_df)),
        "clearance_rows": int(len(clearance_df)),
        "summary_rows": int(len(summary_df)),
        "exact_vendor_positive_or_likely_rows": int((attachment_df["exact_vendor_positive_or_likely_rows"] > 0).sum())
        if not attachment_df.empty
        else 0,
        "exact_vendor_field_confirmed_rows": int((attachment_df["exact_vendor_field_confirmed_rows"] > 0).sum())
        if not attachment_df.empty
        else 0,
        "same_site_reference_field_confirmed_rows": int(
            (attachment_df["same_site_reference_field_confirmed_rows"] > 0).sum()
        )
        if not attachment_df.empty
        else 0,
        "independent_confirmation_attached_rows": int(attachment_df["independent_confirmation_attached"].sum())
        if not attachment_df.empty
        else 0,
        "explicit_all_clearance_rows": int(attachment_df["all_required_clearances_attached"].sum())
        if not attachment_df.empty
        else 0,
        "truth_intake_ready_rows": int(attachment_df["truth_intake_ready"].sum()) if not attachment_df.empty else 0,
        "positive_truth_candidate_approved_sum": int(attachment_df["positive_truth_candidate_approved"].sum())
        if not attachment_df.empty
        else 0,
        "threshold_tuning_approved_sum": int(attachment_df["threshold_tuning_approved"].sum())
        if not attachment_df.empty
        else 0,
        "engine_patch_allowed_sum": int(attachment_df["engine_patch_allowed"].sum()) if not attachment_df.empty else 0,
        "recommended_next_branch": "voltage_preserved_independent_confirmation_template_fill_or_blocker_clearance_review",
        "outputs": {
            "attachment": str(output_dir / ATTACHMENT_OUTPUT_NAME),
            "source_scan": str(output_dir / SOURCE_SCAN_OUTPUT_NAME),
            "clearance": str(output_dir / CLEARANCE_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "independent_template": str(output_dir / INDEPENDENT_TEMPLATE_OUTPUT_NAME),
            "clearance_template": str(output_dir / CLEARANCE_TEMPLATE_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Attach exact independent confirmation and explicit blocker-clearance evidence after BR-097."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--gap-review-dir", default=DEFAULT_GAP_REVIEW_DIR, help="BR-097 output directory.")
    parser.add_argument("--gap-review-input", default="", help="Optional direct BR-097 review CSV.")
    parser.add_argument("--vendor-input", default=DEFAULT_VENDOR_INPUT, help="Exact-panel vendor/manual reply CSV.")
    parser.add_argument("--manual-site-input", default=DEFAULT_MANUAL_SITE_INPUT, help="Site-level manual evidence CSV.")
    parser.add_argument("--independent-evidence-input", default="", help="Optional exact-panel physical/maintenance evidence CSV.")
    parser.add_argument("--blocker-clearance-input", default="", help="Optional explicit blocker clearance CSV.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory for BR-098 artifacts.")
    parser.add_argument("--owner-branch", default="BR-20260425-098")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    gap_review_dir = resolve_path(repo_root, args.gap_review_dir)
    gap_input = (
        resolve_path(repo_root, args.gap_review_input)
        if normalize_text(args.gap_review_input)
        else gap_review_dir / GAP_REVIEW_INPUT_NAME
    )
    vendor_input = resolve_path(repo_root, args.vendor_input)
    manual_site_input = resolve_path(repo_root, args.manual_site_input)
    independent_input = (
        resolve_path(repo_root, args.independent_evidence_input)
        if normalize_text(args.independent_evidence_input)
        else None
    )
    clearance_input = (
        resolve_path(repo_root, args.blocker_clearance_input)
        if normalize_text(args.blocker_clearance_input)
        else None
    )
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    review_df = normalize_gap_review(read_required_csv(gap_input, GAP_REVIEW_REQUIRED_COLUMNS, "BR-097 gap review"))
    vendor_df = normalize_vendor(read_required_csv(vendor_input, VENDOR_REQUIRED_COLUMNS, "vendor evidence"))
    manual_site_df = normalize_manual_site(
        read_required_csv(manual_site_input, MANUAL_SITE_REQUIRED_COLUMNS, "manual site evidence")
    )
    independent_df = normalize_independent(
        read_optional_csv(independent_input, INDEPENDENT_INPUT_COLUMNS, "independent evidence")
        if independent_input
        else pd.DataFrame(columns=INDEPENDENT_INPUT_COLUMNS)
    )
    clearance_input_df = normalize_clearance(
        read_optional_csv(clearance_input, CLEARANCE_INPUT_COLUMNS, "blocker clearance")
        if clearance_input
        else pd.DataFrame(columns=CLEARANCE_INPUT_COLUMNS)
    )
    assert_safe_start(review_df)

    attachment_df = build_attachment(
        args.owner_branch,
        review_df,
        vendor_df,
        manual_site_df,
        independent_df,
        clearance_input_df,
    )
    source_scan_df = build_source_scan(args.owner_branch, review_df, vendor_df, manual_site_df, independent_df)
    clearance_df = build_clearance(args.owner_branch, attachment_df)
    summary_df = build_summary(args.owner_branch, attachment_df)
    action_df = build_action_queue(args.owner_branch, attachment_df)
    independent_template_df = build_independent_template(args.owner_branch, attachment_df)
    clearance_template_df = build_clearance_template(args.owner_branch, attachment_df)

    attachment_df.to_csv(output_dir / ATTACHMENT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    source_scan_df.to_csv(output_dir / SOURCE_SCAN_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    clearance_df.to_csv(output_dir / CLEARANCE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    independent_template_df.to_csv(output_dir / INDEPENDENT_TEMPLATE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    clearance_template_df.to_csv(output_dir / CLEARANCE_TEMPLATE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir / NOTE_OUTPUT_NAME, args.owner_branch, gap_input, attachment_df, summary_df)
    write_json(
        output_dir / JSON_OUTPUT_NAME,
        args.owner_branch,
        repo_root,
        output_dir,
        gap_input,
        independent_input,
        clearance_input,
        attachment_df,
        source_scan_df,
        clearance_df,
        summary_df,
    )

    print(
        json.dumps(
            {
                "owner_branch": args.owner_branch,
                "attachment_rows": int(len(attachment_df)),
                "source_scan_rows": int(len(source_scan_df)),
                "clearance_rows": int(len(clearance_df)),
                "summary_rows": int(len(summary_df)),
                "exact_vendor_positive_or_likely_rows": int(
                    (attachment_df["exact_vendor_positive_or_likely_rows"] > 0).sum()
                )
                if not attachment_df.empty
                else 0,
                "exact_vendor_field_confirmed_rows": int(
                    (attachment_df["exact_vendor_field_confirmed_rows"] > 0).sum()
                )
                if not attachment_df.empty
                else 0,
                "same_site_reference_field_confirmed_rows": int(
                    (attachment_df["same_site_reference_field_confirmed_rows"] > 0).sum()
                )
                if not attachment_df.empty
                else 0,
                "independent_confirmation_attached_rows": int(
                    attachment_df["independent_confirmation_attached"].sum()
                )
                if not attachment_df.empty
                else 0,
                "explicit_all_clearance_rows": int(attachment_df["all_required_clearances_attached"].sum())
                if not attachment_df.empty
                else 0,
                "truth_intake_ready_rows": int(attachment_df["truth_intake_ready"].sum())
                if not attachment_df.empty
                else 0,
                "threshold_tuning_approved_sum": int(attachment_df["threshold_tuning_approved"].sum())
                if not attachment_df.empty
                else 0,
                "outputs": {
                    "attachment": str(output_dir / ATTACHMENT_OUTPUT_NAME),
                    "source_scan": str(output_dir / SOURCE_SCAN_OUTPUT_NAME),
                    "clearance": str(output_dir / CLEARANCE_OUTPUT_NAME),
                    "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
                    "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
                    "independent_template": str(output_dir / INDEPENDENT_TEMPLATE_OUTPUT_NAME),
                    "clearance_template": str(output_dir / CLEARANCE_TEMPLATE_OUTPUT_NAME),
                    "note": str(output_dir / NOTE_OUTPUT_NAME),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
