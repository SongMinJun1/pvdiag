#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


PACKET_INPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_packet_v1.csv"
FAMILY_INPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_family_summary_v1.csv"
MAP_INPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_candidate_map_v1.csv"

REQUEST_OUTPUT_NAME = "panel_day_engine_voltage_preserved_evidence_request_packet_v1.csv"
CHECKLIST_OUTPUT_NAME = "panel_day_engine_voltage_preserved_evidence_request_checklist_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_voltage_preserved_evidence_request_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_voltage_preserved_evidence_request_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_voltage_preserved_evidence_request_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_voltage_preserved_evidence_request_packet_v1.json"

DEFAULT_CONFIRMATION_DIR = "/private/tmp/panel_day_engine_voltage_preserved_confirmation_packet_br093_check"
DEFAULT_OUTPUT_DIR = "/private/tmp/panel_day_engine_voltage_preserved_evidence_request_packet_br095_check"

PACKET_REQUIRED_COLUMNS = [
    "confirmation_packet_row_id",
    "confirmation_family_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "review_priority",
    "confirmation_status",
    "representative_candidate_row_id",
    "representative_candidate_tier",
    "representative_anchor_date",
    "representative_onset_date",
    "representative_gap_days",
    "candidate_rows_for_panel",
    "unique_anchor_dates_for_panel",
    "min_gap_days_for_panel",
    "median_gap_days_for_panel",
    "max_gap_days_for_panel",
    "max_candidate_tier_rank_for_panel",
    "max_voltage_low_current_ok_days_for_panel",
    "max_event_A_days_for_panel",
    "max_low_mid_days_for_panel",
    "same_root_known_positive_seed_count",
    "same_root_known_negative_overlap_count",
    "same_root_known_hold_overlap_count",
    "same_panel_known_positive_seed_count",
    "same_panel_known_negative_overlap_count",
    "counterexample_risk_flag",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

REQUEST_COLUMNS = [
    "owner_branch",
    "evidence_request_id",
    "source_confirmation_packet_row_id",
    "source_confirmation_family_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "request_priority",
    "evidence_request_status",
    "confirmation_status_inherited",
    "review_priority_inherited",
    "request_reason",
    "representative_candidate_row_id",
    "representative_candidate_tier",
    "representative_anchor_date",
    "representative_onset_date",
    "representative_gap_days",
    "candidate_rows_for_panel",
    "unique_anchor_dates_for_panel",
    "min_gap_days_for_panel",
    "median_gap_days_for_panel",
    "max_gap_days_for_panel",
    "max_candidate_tier_rank_for_panel",
    "max_voltage_low_current_ok_days_for_panel",
    "max_event_A_days_for_panel",
    "max_low_mid_days_for_panel",
    "same_root_known_positive_seed_count",
    "same_root_known_negative_overlap_count",
    "same_root_known_hold_overlap_count",
    "same_panel_known_positive_seed_count",
    "same_panel_known_negative_overlap_count",
    "counterexample_risk_flag",
    "required_evidence_axes",
    "missing_evidence_axes",
    "raw_waveform_request_required",
    "raw_waveform_is_independent_confirmation",
    "physical_measurement_or_iv_required",
    "maintenance_or_inspection_required",
    "common_cause_clearance_required",
    "measurement_artifact_clearance_required",
    "counterexample_clearance_required",
    "minimum_independent_axes_required",
    "independent_axes_attached",
    "evidence_ready_for_truth_use",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "next_review_action",
    "notes",
]

CHECKLIST_COLUMNS = [
    "owner_branch",
    "evidence_request_id",
    "checklist_row_id",
    "source_confirmation_packet_row_id",
    "site",
    "root_id",
    "panel_id",
    "confirmation_axis",
    "axis_required_for_truth_use",
    "axis_status",
    "satisfies_independent_confirmation",
    "current_attachment_count",
    "source_evidence_role",
    "why_it_matters",
    "requested_evidence",
    "acceptance_boundary",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "summary_scope",
    "summary_key",
    "request_rows",
    "checklist_rows",
    "p0_request_rows",
    "p1_request_rows",
    "counterexample_risk_rows",
    "counterexample_clearance_required_rows",
    "raw_waveform_support_requested_rows",
    "raw_waveform_independent_confirmation_rows",
    "minimum_independent_axes_required_sum",
    "independent_axes_attached_sum",
    "evidence_ready_for_truth_use_sum",
    "positive_truth_candidate_approved_sum",
    "threshold_tuning_approved_sum",
    "operator_facing_change_allowed_sum",
    "engine_patch_allowed_sum",
    "threshold_patch_allowed_sum",
    "min_gap_days",
    "median_gap_days",
    "max_gap_days",
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

BASE_AXES = [
    {
        "axis": "raw_waveform_attachment",
        "required": 1,
        "independent": 0,
        "role": "algorithmic_raw_support",
        "why": "Raw waveform windows preserve the morphology trace but do not independently confirm a physical fault.",
        "requested": "attach exact panel raw daily waveform/window rows and BR-092 source candidate references",
        "boundary": "Useful support only; cannot approve truth or threshold tuning by itself.",
    },
    {
        "axis": "physical_measurement_or_iv_curve",
        "required": 1,
        "independent": 1,
        "role": "independent_physical_confirmation",
        "why": "Voltage-preserved morphology needs an external physical/electrical artifact before becoming truth support.",
        "requested": "attach exact-panel IV curve, voltage/current measurement, inverter/string trace, or field waveform capture",
        "boundary": "Must identify the same panel/root and overlap the reviewed episode window.",
    },
    {
        "axis": "maintenance_or_inspection_record",
        "required": 1,
        "independent": 1,
        "role": "independent_field_confirmation",
        "why": "A maintenance or inspection record makes the morphology review auditable outside the algorithm.",
        "requested": "attach exact-panel maintenance, inspection, repair, replacement, or work-order record",
        "boundary": "Site-level notes alone are context unless they identify the same panel/root and episode.",
    },
    {
        "axis": "common_cause_clearance",
        "required": 1,
        "independent": 0,
        "role": "blocker_clearance",
        "why": "Spatial/common-cause motion must be cleared before an individual panel truth row can be trusted.",
        "requested": "attach peer/root/site comparison showing the episode is not explained by site-wide or group-off behavior",
        "boundary": "If common-cause remains plausible, keep the row as hold/regression material.",
    },
    {
        "axis": "measurement_artifact_clearance",
        "required": 1,
        "independent": 0,
        "role": "blocker_clearance",
        "why": "Sensor/reference/instrument effects can mimic voltage-preserved panel morphology.",
        "requested": "attach sensor/reference/instrumentation exclusion evidence or reviewer note",
        "boundary": "If measurement artifact remains plausible, do not promote to positive truth.",
    },
]

COUNTEREXAMPLE_AXIS = {
    "axis": "counterexample_clearance",
    "required": 1,
    "independent": 0,
    "role": "counterexample_blocker_clearance",
    "why": "Same-root known negative overlap means the family needs stronger clearance before truth use.",
    "requested": "attach reviewer decision separating this packet row from the known negative overlap pattern",
    "boundary": "Without explicit clearance, keep the family out of truth rebuild and threshold replay.",
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


def rounded(value: object) -> float:
    return round(numeric_float(value), 6)


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def load_input_manifest(repo_root: Path, value: str | Path | None) -> tuple[Path | None, dict[str, Any]]:
    if value is None or str(value).strip() == "":
        return None, {}
    path = resolve_path(repo_root, value)
    if not path.exists():
        raise FileNotFoundError(f"missing input manifest: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"input manifest must be a JSON object: {path}")
    return path, payload


def manifest_path_value(manifest: dict[str, Any], key: str) -> str:
    raw = manifest.get(key)
    if raw is None and isinstance(manifest.get("inputs"), dict):
        raw = manifest["inputs"].get(key)
    if isinstance(raw, dict):
        for field in ["path", "artifact_path", "static_path"]:
            if raw.get(field):
                return str(raw[field])
        return ""
    return "" if raw is None else str(raw)


def cli_flag_provided(flag: str, argv: list[str]) -> bool:
    return any(item == flag or item.startswith(f"{flag}=") for item in argv)


def resolve_packet_input(
    repo_root: Path,
    packet_input_value: str | Path,
    confirmation_dir_value: str | Path,
    manifest: dict[str, Any],
    explicit_flags: set[str],
) -> tuple[Path, str]:
    if "--packet-input" in explicit_flags:
        return resolve_path(repo_root, packet_input_value), "explicit_cli"
    if "--confirmation-dir" in explicit_flags:
        return resolve_path(repo_root, confirmation_dir_value) / PACKET_INPUT_NAME, "explicit_cli"
    if manifest:
        manifest_value = manifest_path_value(manifest, "packet_input")
        if not manifest_value:
            raise KeyError(
                "panel-day evidence input manifest is missing `packet_input`; "
                "pass --packet-input/--confirmation-dir explicitly or add inputs.packet_input"
            )
        return resolve_path(repo_root, manifest_value), "input_manifest"
    return resolve_path(repo_root, confirmation_dir_value) / PACKET_INPUT_NAME, "legacy_default"


def read_required_csv(path: Path, required_cols: list[str], name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing required input {name}: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")
    return df


def normalize_packet(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    text_cols = [
        "confirmation_packet_row_id",
        "confirmation_family_id",
        "site",
        "root_id",
        "panel_group_key",
        "panel_id",
        "review_priority",
        "confirmation_status",
        "representative_candidate_row_id",
        "representative_candidate_tier",
        "representative_anchor_date",
        "representative_onset_date",
    ]
    for col in text_cols:
        out[col] = out[col].map(normalize_text)
    numeric_cols = [col for col in PACKET_REQUIRED_COLUMNS if col not in text_cols]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    return out.sort_values(["site", "root_id", "panel_group_key", "panel_id"]).reset_index(drop=True)


def assert_safe_input(packet_df: pd.DataFrame) -> None:
    for col in [
        "positive_truth_candidate_approved",
        "threshold_tuning_approved",
        "operator_facing_change_allowed",
        "engine_patch_allowed",
        "threshold_patch_allowed",
    ]:
        total = int(pd.to_numeric(packet_df[col], errors="coerce").fillna(0).sum())
        if total != 0:
            raise ValueError(f"BR-095 requires non-authorizing BR-093 input; {col} sum is {total}")


def request_priority(review_priority: str, counterexample_risk: int) -> str:
    if counterexample_risk:
        return "P0_counterexample_guarded_evidence_request"
    if review_priority.startswith("P0"):
        return "P0_independent_evidence_request"
    if review_priority.startswith("P1"):
        return "P1_shape_evidence_request"
    return "P2_context_evidence_request"


def request_reason(review_priority: str, counterexample_risk: int) -> str:
    if counterexample_risk:
        return "same-root known negative overlap requires counterexample clearance before any truth use"
    if review_priority.startswith("P0"):
        return "strong voltage-preserved repeated morphology needs independent confirmation before truth use"
    if review_priority.startswith("P1"):
        return "repeated voltage-preserved context needs evidence attachment before any escalation"
    return "context-only candidate needs evidence before review escalation"


def axes_for_row(counterexample_risk: int) -> list[dict[str, object]]:
    axes = [dict(axis) for axis in BASE_AXES]
    if counterexample_risk:
        axes.append(dict(COUNTEREXAMPLE_AXIS))
    return axes


def build_requests(owner_branch: str, packet_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    request_rows: list[dict[str, object]] = []
    checklist_rows: list[dict[str, object]] = []
    for idx, row in enumerate(packet_df.to_dict(orient="records"), start=1):
        risk = numeric_int(row["counterexample_risk_flag"])
        inherited_priority = normalize_text(row["review_priority"])
        request_id = f"BR095-VPER-{idx:03d}"
        axes = axes_for_row(risk)
        required_axes = [normalize_text(axis["axis"]) for axis in axes if numeric_int(axis["required"]) == 1]
        independent_required = sum(
            numeric_int(axis["required"]) for axis in axes if numeric_int(axis["independent"]) == 1
        )
        request_rows.append(
            {
                "owner_branch": owner_branch,
                "evidence_request_id": request_id,
                "source_confirmation_packet_row_id": normalize_text(row["confirmation_packet_row_id"]),
                "source_confirmation_family_id": normalize_text(row["confirmation_family_id"]),
                "site": normalize_text(row["site"]),
                "root_id": normalize_text(row["root_id"]),
                "panel_group_key": normalize_text(row["panel_group_key"]),
                "panel_id": normalize_text(row["panel_id"]),
                "request_priority": request_priority(inherited_priority, risk),
                "evidence_request_status": "needs_evidence_attachment",
                "confirmation_status_inherited": normalize_text(row["confirmation_status"]),
                "review_priority_inherited": inherited_priority,
                "request_reason": request_reason(inherited_priority, risk),
                "representative_candidate_row_id": normalize_text(row["representative_candidate_row_id"]),
                "representative_candidate_tier": normalize_text(row["representative_candidate_tier"]),
                "representative_anchor_date": normalize_text(row["representative_anchor_date"]),
                "representative_onset_date": normalize_text(row["representative_onset_date"]),
                "representative_gap_days": numeric_int(row["representative_gap_days"]),
                "candidate_rows_for_panel": numeric_int(row["candidate_rows_for_panel"]),
                "unique_anchor_dates_for_panel": numeric_int(row["unique_anchor_dates_for_panel"]),
                "min_gap_days_for_panel": numeric_int(row["min_gap_days_for_panel"]),
                "median_gap_days_for_panel": rounded(row["median_gap_days_for_panel"]),
                "max_gap_days_for_panel": numeric_int(row["max_gap_days_for_panel"]),
                "max_candidate_tier_rank_for_panel": numeric_int(row["max_candidate_tier_rank_for_panel"]),
                "max_voltage_low_current_ok_days_for_panel": numeric_int(
                    row["max_voltage_low_current_ok_days_for_panel"]
                ),
                "max_event_A_days_for_panel": numeric_int(row["max_event_A_days_for_panel"]),
                "max_low_mid_days_for_panel": numeric_int(row["max_low_mid_days_for_panel"]),
                "same_root_known_positive_seed_count": numeric_int(row["same_root_known_positive_seed_count"]),
                "same_root_known_negative_overlap_count": numeric_int(
                    row["same_root_known_negative_overlap_count"]
                ),
                "same_root_known_hold_overlap_count": numeric_int(row["same_root_known_hold_overlap_count"]),
                "same_panel_known_positive_seed_count": numeric_int(row["same_panel_known_positive_seed_count"]),
                "same_panel_known_negative_overlap_count": numeric_int(
                    row["same_panel_known_negative_overlap_count"]
                ),
                "counterexample_risk_flag": risk,
                "required_evidence_axes": ";".join(required_axes),
                "missing_evidence_axes": ";".join(required_axes),
                "raw_waveform_request_required": 1,
                "raw_waveform_is_independent_confirmation": 0,
                "physical_measurement_or_iv_required": 1,
                "maintenance_or_inspection_required": 1,
                "common_cause_clearance_required": 1,
                "measurement_artifact_clearance_required": 1,
                "counterexample_clearance_required": risk,
                "minimum_independent_axes_required": independent_required,
                "independent_axes_attached": 0,
                "evidence_ready_for_truth_use": 0,
                "positive_truth_candidate_approved": 0,
                "threshold_tuning_approved": 0,
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "next_review_action": (
                    "resolve_counterexample_clearance_then_attach_independent_evidence"
                    if risk
                    else "attach_raw_and_independent_physical_field_evidence"
                ),
                "notes": "Evidence request only; no truth, threshold, operator-facing, or engine approval.",
            }
        )
        for axis_idx, axis in enumerate(axes, start=1):
            checklist_rows.append(
                {
                    "owner_branch": owner_branch,
                    "evidence_request_id": request_id,
                    "checklist_row_id": f"{request_id}-AX{axis_idx:02d}",
                    "source_confirmation_packet_row_id": normalize_text(row["confirmation_packet_row_id"]),
                    "site": normalize_text(row["site"]),
                    "root_id": normalize_text(row["root_id"]),
                    "panel_id": normalize_text(row["panel_id"]),
                    "confirmation_axis": normalize_text(axis["axis"]),
                    "axis_required_for_truth_use": numeric_int(axis["required"]),
                    "axis_status": "missing",
                    "satisfies_independent_confirmation": numeric_int(axis["independent"]),
                    "current_attachment_count": 0,
                    "source_evidence_role": normalize_text(axis["role"]),
                    "why_it_matters": normalize_text(axis["why"]),
                    "requested_evidence": normalize_text(axis["requested"]),
                    "acceptance_boundary": normalize_text(axis["boundary"]),
                    "operator_facing_change_allowed": 0,
                    "engine_patch_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "notes": "Checklist row is an evidence request, not an approval.",
                }
            )
    return (
        pd.DataFrame(request_rows).reindex(columns=REQUEST_COLUMNS),
        pd.DataFrame(checklist_rows).reindex(columns=CHECKLIST_COLUMNS),
    )


def summarize_group(
    owner_branch: str,
    request_df: pd.DataFrame,
    checklist_df: pd.DataFrame,
    summary_scope: str,
    summary_key: str,
) -> dict[str, object]:
    if request_df.empty:
        return {
            "owner_branch": owner_branch,
            "summary_scope": summary_scope,
            "summary_key": summary_key,
            "request_rows": 0,
            "checklist_rows": 0,
            "p0_request_rows": 0,
            "p1_request_rows": 0,
            "counterexample_risk_rows": 0,
            "counterexample_clearance_required_rows": 0,
            "raw_waveform_support_requested_rows": 0,
            "raw_waveform_independent_confirmation_rows": 0,
            "minimum_independent_axes_required_sum": 0,
            "independent_axes_attached_sum": 0,
            "evidence_ready_for_truth_use_sum": 0,
            "positive_truth_candidate_approved_sum": 0,
            "threshold_tuning_approved_sum": 0,
            "operator_facing_change_allowed_sum": 0,
            "engine_patch_allowed_sum": 0,
            "threshold_patch_allowed_sum": 0,
            "min_gap_days": 0,
            "median_gap_days": 0.0,
            "max_gap_days": 0,
            "notes": "empty group",
        }
    request_ids = set(request_df["evidence_request_id"].map(normalize_text))
    checklist_subset = checklist_df.loc[checklist_df["evidence_request_id"].map(normalize_text).isin(request_ids)]
    return {
        "owner_branch": owner_branch,
        "summary_scope": summary_scope,
        "summary_key": summary_key,
        "request_rows": int(len(request_df)),
        "checklist_rows": int(len(checklist_subset)),
        "p0_request_rows": int(request_df["request_priority"].map(normalize_text).str.startswith("P0").sum()),
        "p1_request_rows": int(request_df["request_priority"].map(normalize_text).str.startswith("P1").sum()),
        "counterexample_risk_rows": int(request_df["counterexample_risk_flag"].sum()),
        "counterexample_clearance_required_rows": int(request_df["counterexample_clearance_required"].sum()),
        "raw_waveform_support_requested_rows": int(request_df["raw_waveform_request_required"].sum()),
        "raw_waveform_independent_confirmation_rows": int(
            request_df["raw_waveform_is_independent_confirmation"].sum()
        ),
        "minimum_independent_axes_required_sum": int(request_df["minimum_independent_axes_required"].sum()),
        "independent_axes_attached_sum": int(request_df["independent_axes_attached"].sum()),
        "evidence_ready_for_truth_use_sum": int(request_df["evidence_ready_for_truth_use"].sum()),
        "positive_truth_candidate_approved_sum": int(request_df["positive_truth_candidate_approved"].sum()),
        "threshold_tuning_approved_sum": int(request_df["threshold_tuning_approved"].sum()),
        "operator_facing_change_allowed_sum": int(request_df["operator_facing_change_allowed"].sum()),
        "engine_patch_allowed_sum": int(request_df["engine_patch_allowed"].sum()),
        "threshold_patch_allowed_sum": int(request_df["threshold_patch_allowed"].sum()),
        "min_gap_days": numeric_int(request_df["min_gap_days_for_panel"].min()),
        "median_gap_days": rounded(request_df["median_gap_days_for_panel"].median()),
        "max_gap_days": numeric_int(request_df["max_gap_days_for_panel"].max()),
        "notes": "raw waveform support requested but not counted as independent confirmation",
    }


def build_summary(owner_branch: str, request_df: pd.DataFrame, checklist_df: pd.DataFrame) -> pd.DataFrame:
    rows = [summarize_group(owner_branch, request_df, checklist_df, "overall", "all")]
    if not request_df.empty:
        for site, group in request_df.groupby("site", sort=True):
            rows.append(summarize_group(owner_branch, group, checklist_df, "site", normalize_text(site)))
        for priority, group in request_df.groupby("request_priority", sort=True):
            rows.append(summarize_group(owner_branch, group, checklist_df, "request_priority", normalize_text(priority)))
    return pd.DataFrame(rows).reindex(columns=SUMMARY_COLUMNS)


def build_action_queue(owner_branch: str, request_df: pd.DataFrame) -> pd.DataFrame:
    total = int(len(request_df))
    p0_rows = 0 if request_df.empty else int(request_df["request_priority"].map(normalize_text).str.startswith("P0").sum())
    risk_rows = 0 if request_df.empty else int(request_df["counterexample_risk_flag"].sum())
    rows = [
        {
            "owner_branch": owner_branch,
            "sequence": 1,
            "action_id": "BR095-ACT-001",
            "action": "attach raw waveform context without treating it as independent confirmation",
            "input_filter": "all evidence request rows",
            "purpose": "make each packet row reviewable from source morphology while preserving the evidence boundary",
            "success_boundary": f"raw waveform context attached for request rows={total}; approvals remain 0",
            "recommended_next_artifact": "voltage_preserved_evidence_attachment_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Raw support can explain the candidate but cannot approve truth or threshold tuning alone.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 2,
            "action_id": "BR095-ACT-002",
            "action": "collect independent exact-panel physical or maintenance evidence",
            "input_filter": "request_priority starts with P0 or P1",
            "purpose": "separate confirmed physical faults from algorithmic morphology candidates",
            "success_boundary": f"P0/P1 request rows={p0_rows + int((request_df['request_priority'].map(normalize_text).str.startswith('P1')).sum()) if not request_df.empty else 0}; independent axes filled by reviewer",
            "recommended_next_artifact": "voltage_preserved_independent_confirmation_attachment_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "At least physical/electrical measurement or maintenance/inspection evidence should be attached.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 3,
            "action_id": "BR095-ACT-003",
            "action": "clear common-cause and measurement-artifact blockers",
            "input_filter": "all evidence request rows",
            "purpose": "prevent site/root/sensor effects from being promoted as panel-local truth",
            "success_boundary": "common-cause and artifact clearance fields are explicitly reviewed",
            "recommended_next_artifact": "voltage_preserved_blocker_clearance_review_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Rows with uncleared blockers stay hold/regression material.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 4,
            "action_id": "BR095-ACT-004",
            "action": "resolve counterexample-risk rows separately",
            "input_filter": "counterexample_risk_flag=1",
            "purpose": "avoid turning same-root negative-overlap families into positive truth by volume",
            "success_boundary": f"counterexample-risk rows={risk_rows}; explicit clearance required before truth rebuild",
            "recommended_next_artifact": "voltage_preserved_counterexample_clearance_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Counterexample-risk rows cannot be used for positive truth until this action is closed.",
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


def write_note(
    path: Path,
    owner_branch: str,
    packet_input: Path,
    request_df: pd.DataFrame,
    checklist_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> None:
    source_map = input_resolution_sources or {}
    priority_counts = (
        request_df["request_priority"].value_counts().sort_index().to_dict() if not request_df.empty else {}
    )
    axis_counts = (
        checklist_df["confirmation_axis"].value_counts().sort_index().to_dict() if not checklist_df.empty else {}
    )
    summary_cols = [
        "summary_scope",
        "summary_key",
        "request_rows",
        "checklist_rows",
        "counterexample_risk_rows",
        "evidence_ready_for_truth_use_sum",
        "positive_truth_candidate_approved_sum",
        "threshold_tuning_approved_sum",
        "engine_patch_allowed_sum",
    ]
    lines = [
        "# panel_day_engine_voltage_preserved_evidence_request_packet_v1",
        "",
        "## Purpose",
        "- Convert BR-093 confirmation packet rows into explicit evidence requests and checklist axes.",
        "- Keep raw waveform evidence as support, not independent physical confirmation.",
        "- Keep positive truth, threshold tuning, operator-facing promotion, and engine patch approvals blocked.",
        "",
        "## Input",
        f"- BR-093 packet: `{packet_input}`",
        f"- evidence input manifest: `{input_manifest_path if input_manifest_path is not None else 'not provided'}`",
        "",
        "## Input Resolution Sources",
        f"- `packet_input`: `{source_map.get('packet_input', 'legacy_default')}`",
        "",
        "## Real Result",
        f"- owner_branch: `{owner_branch}`",
        f"- evidence request rows: `{len(request_df)}`",
        f"- checklist rows: `{len(checklist_df)}`",
        f"- request priority counts: `{json.dumps(priority_counts, ensure_ascii=False, sort_keys=True)}`",
        f"- checklist axis counts: `{json.dumps(axis_counts, ensure_ascii=False, sort_keys=True)}`",
        f"- counterexample-risk request rows: `{int(request_df['counterexample_risk_flag'].sum()) if not request_df.empty else 0}`",
        f"- raw waveform independent confirmation rows: `{int(request_df['raw_waveform_is_independent_confirmation'].sum()) if not request_df.empty else 0}`",
        f"- evidence ready for truth use sum: `{int(request_df['evidence_ready_for_truth_use'].sum()) if not request_df.empty else 0}`",
        f"- positive truth candidate approved sum: `{int(request_df['positive_truth_candidate_approved'].sum()) if not request_df.empty else 0}`",
        f"- threshold tuning approved sum: `{int(request_df['threshold_tuning_approved'].sum()) if not request_df.empty else 0}`",
        f"- engine patch allowed sum: `{int(request_df['engine_patch_allowed'].sum()) if not request_df.empty else 0}`",
        "",
        "## Summary",
        dataframe_to_markdown(summary_df.loc[:, summary_cols] if not summary_df.empty else summary_df),
        "",
        "## Safety Boundary",
        "- BR-095 is an evidence request packet only.",
        "- Request rows are not truth labels and do not approve threshold tuning.",
        "- Raw waveform context is requested, but `raw_waveform_is_independent_confirmation=0` by design.",
        "- Counterexample-risk rows require explicit clearance before truth rebuild.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(
    path: Path,
    owner_branch: str,
    repo_root: Path,
    output_dir: Path,
    packet_input: Path,
    request_df: pd.DataFrame,
    checklist_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "packet_input": str(packet_input),
        "input_manifest": str(input_manifest_path) if input_manifest_path is not None else "",
        "input_resolution_sources": input_resolution_sources or {},
        "evidence_request_rows": int(len(request_df)),
        "checklist_rows": int(len(checklist_df)),
        "request_priority_counts": request_df["request_priority"].value_counts().sort_index().to_dict()
        if not request_df.empty
        else {},
        "checklist_axis_counts": checklist_df["confirmation_axis"].value_counts().sort_index().to_dict()
        if not checklist_df.empty
        else {},
        "counterexample_risk_request_rows": int(request_df["counterexample_risk_flag"].sum())
        if not request_df.empty
        else 0,
        "counterexample_clearance_required_rows": int(request_df["counterexample_clearance_required"].sum())
        if not request_df.empty
        else 0,
        "raw_waveform_independent_confirmation_rows": int(
            request_df["raw_waveform_is_independent_confirmation"].sum()
        )
        if not request_df.empty
        else 0,
        "evidence_ready_for_truth_use_sum": int(request_df["evidence_ready_for_truth_use"].sum())
        if not request_df.empty
        else 0,
        "positive_truth_candidate_approved_sum": int(request_df["positive_truth_candidate_approved"].sum())
        if not request_df.empty
        else 0,
        "threshold_tuning_approved_sum": int(request_df["threshold_tuning_approved"].sum())
        if not request_df.empty
        else 0,
        "operator_facing_change_allowed_sum": int(request_df["operator_facing_change_allowed"].sum())
        if not request_df.empty
        else 0,
        "engine_patch_allowed_sum": int(request_df["engine_patch_allowed"].sum()) if not request_df.empty else 0,
        "threshold_patch_allowed_sum": int(request_df["threshold_patch_allowed"].sum())
        if not request_df.empty
        else 0,
        "summary_rows": int(len(summary_df)),
        "recommended_next_branch": "voltage_preserved_evidence_attachment_v1",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "request_packet": str(output_dir / REQUEST_OUTPUT_NAME),
            "checklist": str(output_dir / CHECKLIST_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build BR-095 evidence request/checklist packet from BR-093 voltage-preserved confirmation rows."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument(
        "--input-manifest",
        default=None,
        help="Optional JSON manifest for the BR-093 packet input.",
    )
    parser.add_argument("--confirmation-dir", default=DEFAULT_CONFIRMATION_DIR, help="BR-093 confirmation output dir.")
    parser.add_argument("--packet-input", default="", help="Optional direct BR-093 packet CSV.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory for BR-095 artifacts.")
    parser.add_argument("--owner-branch", default="BR-20260425-095")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    input_manifest_path, input_manifest = load_input_manifest(repo_root, args.input_manifest)
    argv = sys.argv[1:]
    explicit_flags = {
        flag
        for flag in [
            "--packet-input",
            "--confirmation-dir",
        ]
        if cli_flag_provided(flag, argv)
    }
    packet_input, packet_input_source = resolve_packet_input(
        repo_root,
        args.packet_input,
        args.confirmation_dir,
        input_manifest,
        explicit_flags,
    )
    input_resolution_sources = {
        "packet_input": packet_input_source,
    }
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    packet_df = normalize_packet(read_required_csv(packet_input, PACKET_REQUIRED_COLUMNS, "BR-093 packet"))
    assert_safe_input(packet_df)
    request_df, checklist_df = build_requests(args.owner_branch, packet_df)
    summary_df = build_summary(args.owner_branch, request_df, checklist_df)
    action_df = build_action_queue(args.owner_branch, request_df)

    request_df.to_csv(output_dir / REQUEST_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    checklist_df.to_csv(output_dir / CHECKLIST_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(
        output_dir / NOTE_OUTPUT_NAME,
        args.owner_branch,
        packet_input,
        request_df,
        checklist_df,
        summary_df,
        input_manifest_path,
        input_resolution_sources,
    )
    write_json(
        output_dir / JSON_OUTPUT_NAME,
        args.owner_branch,
        repo_root,
        output_dir,
        packet_input,
        request_df,
        checklist_df,
        summary_df,
        input_manifest_path,
        input_resolution_sources,
    )

    print(
        json.dumps(
            {
                "owner_branch": args.owner_branch,
                "evidence_request_rows": int(len(request_df)),
                "checklist_rows": int(len(checklist_df)),
                "summary_rows": int(len(summary_df)),
                "request_priority_counts": request_df["request_priority"].value_counts().sort_index().to_dict()
                if not request_df.empty
                else {},
                "checklist_axis_counts": checklist_df["confirmation_axis"].value_counts().sort_index().to_dict()
                if not checklist_df.empty
                else {},
                "counterexample_risk_request_rows": int(request_df["counterexample_risk_flag"].sum())
                if not request_df.empty
                else 0,
                "raw_waveform_independent_confirmation_rows": int(
                    request_df["raw_waveform_is_independent_confirmation"].sum()
                )
                if not request_df.empty
                else 0,
                "evidence_ready_for_truth_use_sum": int(request_df["evidence_ready_for_truth_use"].sum())
                if not request_df.empty
                else 0,
                "positive_truth_candidate_approved_sum": int(request_df["positive_truth_candidate_approved"].sum())
                if not request_df.empty
                else 0,
                "threshold_tuning_approved_sum": int(request_df["threshold_tuning_approved"].sum())
                if not request_df.empty
                else 0,
                "outputs": {
                    "request_packet": str(output_dir / REQUEST_OUTPUT_NAME),
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
