#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-102"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_capture_schema_br102_check"

TEMPLATE_OUTPUT_NAME = "mlpe_field_trial_capture_template_v1.csv"
SCHEMA_OUTPUT_NAME = "mlpe_field_trial_capture_schema_v1.csv"
ALLOWED_VALUES_OUTPUT_NAME = "mlpe_field_trial_capture_allowed_values_v1.csv"
CHECK_OUTPUT_NAME = "mlpe_field_trial_capture_check_v1.csv"
CHECK_SUMMARY_OUTPUT_NAME = "mlpe_field_trial_capture_check_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_capture_schema_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_capture_schema_v1.json"

FAMILIES = [
    "normal",
    "panel_surface_environment_fault",
    "panel_physical_degradation_fault",
    "panel_electrical_submodule_fault",
    "connection_or_open_fault",
    "mlpe_device_or_control_fault",
    "measurement_or_communication_artifact",
    "inverter_or_group_side_fault",
    "site_common_cause_event",
    "unknown_or_compound",
]

SUBTYPES_BY_FAMILY = {
    "normal": ["normal_clear_day_baseline"],
    "panel_surface_environment_fault": [
        "partial_shading",
        "uniform_soiling",
        "moving_shadow",
        "snow_or_cover",
        "localized_obstruction",
    ],
    "panel_physical_degradation_fault": [
        "degradation_emulation",
        "series_resistance_degradation",
        "crack_or_damage_proxy",
        "hotspot_like_thermal_stress",
    ],
    "panel_electrical_submodule_fault": [
        "bypass_diode_open",
        "bypass_diode_short",
        "substring_loss",
        "cell_mismatch",
        "voltage_preserved_current_drop",
    ],
    "connection_or_open_fault": [
        "intermittent_connection",
        "high_contact_resistance",
        "partial_open",
        "full_open",
        "connector_recovery",
    ],
    "mlpe_device_or_control_fault": [
        "optimizer_current_limit",
        "optimizer_clipping",
        "mppt_tracking_anomaly",
        "rapid_shutdown_state",
        "control_response_delay",
    ],
    "measurement_or_communication_artifact": [
        "telemetry_dropout",
        "telemetry_stuck",
        "sensor_offset",
        "timestamp_skew",
        "missing_packet_burst",
    ],
    "inverter_or_group_side_fault": [
        "group_curtailment",
        "string_shutdown",
        "inverter_limit",
        "root_level_drop",
        "multi_panel_zero_output",
    ],
    "site_common_cause_event": [
        "cloud_or_irradiance_event",
        "site_control_action",
        "grid_event",
        "maintenance_window",
        "site_wide_reference_shift",
    ],
    "unknown_or_compound": ["compound_fault", "unknown_unresolved"],
}

INJECTION_CASES = [
    "normal_clear_day_baseline",
    "partial_shading_panel_local",
    "uniform_soiling_or_cover",
    "high_contact_resistance_or_series_resistance",
    "partial_open_or_full_open",
    "bypass_diode_or_substring_loss",
    "optimizer_current_limit_or_clipping",
    "telemetry_dropout_or_stuck_value",
    "group_or_inverter_curtailment",
    "site_or_root_common_cause_event",
    "mppt_tracking_anomaly",
    "rapid_shutdown_or_safety_state",
    "degradation_emulation",
    "compound_fault",
]

SIGNATURES = [
    "normal_reference",
    "v_drop_i_preserved",
    "i_drop_v_preserved",
    "p_drop_both",
    "voltage_current_ratio_shift",
    "zero_or_near_zero_output",
    "stale_or_missing_telemetry",
    "multi_panel_synchronous_drop",
    "unknown",
]

CAPTURE_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "site",
    "root_id",
    "panel_id",
    "mlpe_device_id",
    "start_ts",
    "end_ts",
    "capture_status",
    "injection_case",
    "planned_fault_family",
    "planned_fault_subtype",
    "affected_scope",
    "injection_mode",
    "injection_strength",
    "expected_signature",
    "planned_panel_local_flag",
    "planned_common_cause_flag",
    "planned_measurement_artifact_flag",
    "mlpe_state",
    "raw_data_path",
    "peer_data_path",
    "weather_data_path",
    "waveform_slice_path",
    "timestamp_quality",
    "communication_quality",
    "final_fault_family",
    "final_fault_subtype",
    "final_truth_confidence",
    "final_label_attached",
    "label_status",
    "operator_promotion_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "reviewer",
    "review_note",
]

CONTROLLED_VALUES = {
    "capture_status": ["planned", "captured", "label_pending", "label_attached", "discarded"],
    "injection_case": INJECTION_CASES,
    "planned_fault_family": FAMILIES,
    "affected_scope": ["panel", "substring", "string", "root", "site", "unknown"],
    "injection_mode": ["physical", "electrical_emulator", "mlpe_control", "telemetry", "environment", "observed_only"],
    "expected_signature": SIGNATURES,
    "planned_panel_local_flag": ["0", "1"],
    "planned_common_cause_flag": ["0", "1"],
    "planned_measurement_artifact_flag": ["0", "1"],
    "mlpe_state": ["normal", "clipping", "mppt_anomaly", "rapid_shutdown", "dropout", "control_delay", "unknown"],
    "timestamp_quality": ["unchecked", "ok", "skewed", "missing", "mixed"],
    "communication_quality": ["unchecked", "ok", "dropout", "stale", "missing", "mixed"],
    "final_fault_family": FAMILIES,
    "final_truth_confidence": ["confirmed_injected", "confirmed_observed", "probable", "ambiguous", "negative_control"],
    "final_label_attached": ["0", "1"],
    "label_status": ["label_pending", "label_attached", "discarded"],
    "operator_promotion_allowed": ["0"],
    "engine_patch_allowed": ["0"],
    "threshold_patch_allowed": ["0"],
}

CAPTURE_REQUIRED_WHEN_NOT_PLANNED = [
    "trial_event_id",
    "site",
    "panel_id",
    "mlpe_device_id",
    "start_ts",
    "end_ts",
    "injection_case",
    "planned_fault_family",
    "planned_fault_subtype",
    "affected_scope",
    "injection_mode",
    "injection_strength",
    "expected_signature",
    "mlpe_state",
    "raw_data_path",
    "peer_data_path",
    "waveform_slice_path",
    "timestamp_quality",
    "communication_quality",
]

INJECTION_DEFAULTS = {
    "normal_clear_day_baseline": ("normal", "normal_clear_day_baseline", "panel", "observed_only", "normal_reference", 1, 0, 0, "normal"),
    "partial_shading_panel_local": ("panel_surface_environment_fault", "partial_shading", "panel", "environment", "i_drop_v_preserved", 1, 0, 0, "normal"),
    "uniform_soiling_or_cover": ("panel_surface_environment_fault", "uniform_soiling", "panel", "environment", "p_drop_both", 1, 0, 0, "normal"),
    "high_contact_resistance_or_series_resistance": ("connection_or_open_fault", "high_contact_resistance", "panel", "electrical_emulator", "voltage_current_ratio_shift", 1, 0, 0, "normal"),
    "partial_open_or_full_open": ("connection_or_open_fault", "partial_open", "panel", "electrical_emulator", "zero_or_near_zero_output", 1, 0, 0, "normal"),
    "bypass_diode_or_substring_loss": ("panel_electrical_submodule_fault", "substring_loss", "substring", "electrical_emulator", "voltage_current_ratio_shift", 1, 0, 0, "normal"),
    "optimizer_current_limit_or_clipping": ("mlpe_device_or_control_fault", "optimizer_current_limit", "panel", "mlpe_control", "i_drop_v_preserved", 0, 0, 0, "clipping"),
    "telemetry_dropout_or_stuck_value": ("measurement_or_communication_artifact", "telemetry_dropout", "panel", "telemetry", "stale_or_missing_telemetry", 0, 0, 1, "dropout"),
    "group_or_inverter_curtailment": ("inverter_or_group_side_fault", "group_curtailment", "root", "observed_only", "multi_panel_synchronous_drop", 0, 1, 0, "normal"),
    "site_or_root_common_cause_event": ("site_common_cause_event", "site_control_action", "site", "observed_only", "multi_panel_synchronous_drop", 0, 1, 0, "normal"),
    "mppt_tracking_anomaly": ("mlpe_device_or_control_fault", "mppt_tracking_anomaly", "panel", "mlpe_control", "voltage_current_ratio_shift", 0, 0, 0, "mppt_anomaly"),
    "rapid_shutdown_or_safety_state": ("mlpe_device_or_control_fault", "rapid_shutdown_state", "root", "mlpe_control", "zero_or_near_zero_output", 0, 1, 0, "rapid_shutdown"),
    "degradation_emulation": ("panel_physical_degradation_fault", "degradation_emulation", "panel", "electrical_emulator", "p_drop_both", 1, 0, 0, "normal"),
    "compound_fault": ("unknown_or_compound", "compound_fault", "unknown", "observed_only", "unknown", 0, 0, 0, "unknown"),
}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def build_template() -> pd.DataFrame:
    rows = []
    for idx, case in enumerate(INJECTION_CASES, start=1):
        family, subtype, scope, mode, signature, local, common, artifact, mlpe_state = INJECTION_DEFAULTS[case]
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": f"BR102-MFTC-{idx:03d}",
                "site": "",
                "root_id": "",
                "panel_id": "",
                "mlpe_device_id": "",
                "start_ts": "",
                "end_ts": "",
                "capture_status": "planned",
                "injection_case": case,
                "planned_fault_family": family,
                "planned_fault_subtype": subtype,
                "affected_scope": scope,
                "injection_mode": mode,
                "injection_strength": "",
                "expected_signature": signature,
                "planned_panel_local_flag": local,
                "planned_common_cause_flag": common,
                "planned_measurement_artifact_flag": artifact,
                "mlpe_state": mlpe_state,
                "raw_data_path": "",
                "peer_data_path": "",
                "weather_data_path": "",
                "waveform_slice_path": "",
                "timestamp_quality": "unchecked",
                "communication_quality": "unchecked",
                "final_fault_family": "",
                "final_fault_subtype": "",
                "final_truth_confidence": "",
                "final_label_attached": 0,
                "label_status": "label_pending",
                "operator_promotion_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "reviewer": "",
                "review_note": "Template row; fill capture metadata during field trial. Final labels stay blank until adjudication.",
            }
        )
    return pd.DataFrame(rows).reindex(columns=CAPTURE_COLUMNS)


def build_schema() -> pd.DataFrame:
    descriptions = {
        "trial_event_id": "Stable field-trial event id.",
        "site": "Site id.",
        "root_id": "Root/string/group id, if available.",
        "panel_id": "Target panel id.",
        "mlpe_device_id": "Optimizer/MLPE id or mapped device id.",
        "start_ts": "Injection or observed event start timestamp.",
        "end_ts": "Injection or observed event end timestamp.",
        "capture_status": "Capture lifecycle state.",
        "injection_case": "Planned or observed injection case.",
        "planned_fault_family": "Planned/injection family, not final truth.",
        "planned_fault_subtype": "Planned/injection subtype under planned family.",
        "affected_scope": "Intended or observed electrical scope.",
        "injection_mode": "How the event is introduced or observed.",
        "injection_strength": "Numeric or structured intensity, e.g. shade ratio/resistance/current limit.",
        "expected_signature": "Expected V/I/P/telemetry shape.",
        "planned_panel_local_flag": "1 only when event is panel-local by design.",
        "planned_common_cause_flag": "1 when event intentionally affects site/root/group.",
        "planned_measurement_artifact_flag": "1 for telemetry/sensor/data manipulation.",
        "mlpe_state": "Observed/planned MLPE control state.",
        "raw_data_path": "Path to target raw data slice.",
        "peer_data_path": "Path to same root/group/site peer data slice.",
        "weather_data_path": "Optional weather/irradiance proxy path.",
        "waveform_slice_path": "Path to curated start/peak/recovery waveform slice.",
        "timestamp_quality": "Timestamp quality status.",
        "communication_quality": "MLPE communication quality status.",
        "final_fault_family": "Blank until final adjudication.",
        "final_fault_subtype": "Blank until final adjudication.",
        "final_truth_confidence": "Blank until final adjudication.",
        "final_label_attached": "0 until final label is attached.",
        "label_status": "Label lifecycle state.",
        "operator_promotion_allowed": "Always 0 in capture schema branch.",
        "engine_patch_allowed": "Always 0 in capture schema branch.",
        "threshold_patch_allowed": "Always 0 in capture schema branch.",
        "reviewer": "Reviewer id/name.",
        "review_note": "Free-form note.",
    }
    rows = []
    for col in CAPTURE_COLUMNS:
        allowed = CONTROLLED_VALUES.get(col)
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "field": col,
                "required_stage": "not_planned_capture" if col in CAPTURE_REQUIRED_WHEN_NOT_PLANNED else "template_or_optional",
                "allowed_values_csv": ",".join(allowed) if allowed else "",
                "blank_allowed_when": "capture_status=planned" if col in CAPTURE_REQUIRED_WHEN_NOT_PLANNED else "always_or_by_label_status",
                "description": descriptions.get(col, ""),
            }
        )
    return pd.DataFrame(rows)


def build_allowed_values() -> pd.DataFrame:
    rows = []
    for field, values in CONTROLLED_VALUES.items():
        for value in values:
            rows.append({"owner_branch": OWNER_BRANCH, "field": field, "allowed_value": value})
    for family, subtypes in SUBTYPES_BY_FAMILY.items():
        for subtype in subtypes:
            rows.append({"owner_branch": OWNER_BRANCH, "field": f"subtype_for:{family}", "allowed_value": subtype})
    return pd.DataFrame(rows)


def read_capture(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing capture input: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    for col in CAPTURE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df.reindex(columns=CAPTURE_COLUMNS)


def add_check(checks: list[dict[str, object]], severity: str, row_id: str, field: str, message: str) -> None:
    checks.append(
        {
            "owner_branch": OWNER_BRANCH,
            "severity": severity,
            "trial_event_id": row_id,
            "field": field,
            "message": message,
        }
    )


def check_capture(df: pd.DataFrame) -> pd.DataFrame:
    checks: list[dict[str, object]] = []
    missing_cols = [col for col in CAPTURE_COLUMNS if col not in df.columns]
    for col in missing_cols:
        add_check(checks, "error", "", col, "missing required schema column")
    if missing_cols:
        return pd.DataFrame(checks)

    normalized = df.copy()
    for col in CAPTURE_COLUMNS:
        normalized[col] = normalized[col].map(normalize_text)

    duplicated = normalized["trial_event_id"].ne("") & normalized["trial_event_id"].duplicated(keep=False)
    for _, row in normalized[duplicated].iterrows():
        add_check(checks, "error", row["trial_event_id"], "trial_event_id", "duplicate non-empty trial_event_id")

    for idx, row in normalized.iterrows():
        row_id = row["trial_event_id"] or f"row_{idx + 1}"
        for field, allowed in CONTROLLED_VALUES.items():
            value = row[field]
            if value and value not in allowed:
                add_check(checks, "error", row_id, field, f"value {value!r} not in allowed set")

        family = row["planned_fault_family"]
        subtype = row["planned_fault_subtype"]
        if family and subtype and subtype not in SUBTYPES_BY_FAMILY.get(family, []):
            add_check(checks, "error", row_id, "planned_fault_subtype", "subtype is not allowed for planned_fault_family")

        status = row["capture_status"]
        if status and status != "planned":
            for field in CAPTURE_REQUIRED_WHEN_NOT_PLANNED:
                if not row[field]:
                    add_check(checks, "error", row_id, field, "required after capture_status leaves planned")

        if row["label_status"] == "label_pending":
            for field in ["final_fault_family", "final_fault_subtype", "final_truth_confidence"]:
                if row[field]:
                    add_check(checks, "error", row_id, field, "final label field must stay blank while label_status=label_pending")

        if row["label_status"] == "label_attached":
            for field in ["final_fault_family", "final_fault_subtype", "final_truth_confidence"]:
                if not row[field]:
                    add_check(checks, "error", row_id, field, "required when label_status=label_attached")
            if row["final_fault_family"] and row["final_fault_subtype"]:
                allowed_subtypes = SUBTYPES_BY_FAMILY.get(row["final_fault_family"], [])
                if row["final_fault_subtype"] not in allowed_subtypes:
                    add_check(checks, "error", row_id, "final_fault_subtype", "final subtype is not allowed for final family")

        if row["planned_measurement_artifact_flag"] == "1" and family != "measurement_or_communication_artifact":
            add_check(checks, "error", row_id, "planned_measurement_artifact_flag", "artifact flag requires measurement_or_communication_artifact family")

        if row["planned_panel_local_flag"] == "1" and row["planned_common_cause_flag"] == "1":
            add_check(checks, "error", row_id, "planned_panel_local_flag", "panel-local and common-cause flags cannot both be 1")

        if row["planned_common_cause_flag"] == "1" and row["affected_scope"] == "panel":
            add_check(checks, "warning", row_id, "affected_scope", "common-cause planned rows usually need string/root/site scope")

        for field in ["operator_promotion_allowed", "engine_patch_allowed", "threshold_patch_allowed"]:
            if row[field] != "0":
                add_check(checks, "error", row_id, field, "approval flag must remain 0 in capture schema gate")

    if not checks:
        add_check(checks, "ok", "", "", "all capture schema checks passed")
    return pd.DataFrame(checks)


def summarize_checks(check_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for severity in ["error", "warning", "ok"]:
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "severity": severity,
                "count": int(check_df["severity"].eq(severity).sum()) if "severity" in check_df.columns else 0,
            }
        )
    rows.append(
        {
            "owner_branch": OWNER_BRANCH,
            "severity": "check_passed",
            "count": int(not check_df["severity"].isin(["error"]).any()) if "severity" in check_df.columns else 0,
        }
    )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, template_rows: int, check_summary: pd.DataFrame) -> Path:
    error_count = int(check_summary.loc[check_summary["severity"].eq("error"), "count"].iloc[0])
    warning_count = int(check_summary.loc[check_summary["severity"].eq("warning"), "count"].iloc[0])
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-102 MLPE Field-Trial Capture Schema",
        "",
        "## Purpose",
        "- Create a label-ready capture template before final labels exist.",
        "- Keep planned injection metadata separate from final truth labels.",
        "- Block operator, threshold, and engine approvals during capture/schema validation.",
        "",
        "## Real Result",
        f"- template rows: `{template_rows}`",
        f"- check errors: `{error_count}`",
        f"- check warnings: `{warning_count}`",
        "- final label fields are intentionally blank in the template.",
        "- promotion/threshold/engine approval fields are locked to `0`.",
        "",
        "## Boundary",
        "- This branch does not create truth labels.",
        "- This branch does not tune thresholds.",
        "- This branch does not edit `panel_day_engine.py`.",
        "- Final labels must be attached later through a separate adjudication/truth-intake gate.",
        "",
        "## Next Path",
        "1. Use `mlpe_field_trial_capture_template_v1.csv` during 실증 setup.",
        "2. Fill capture metadata and raw/peer/waveform paths as events are injected or observed.",
        "3. Keep `label_status=label_pending` until final adjudication.",
        "4. Re-run this checker before any truth intake or threshold replay.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--capture-input", default="")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    template = build_template()
    schema = build_schema()
    allowed = build_allowed_values()
    capture_for_check = read_capture(resolve_path(repo_root, args.capture_input)) if args.capture_input else template
    check = check_capture(capture_for_check)
    summary = summarize_checks(check)

    template_path = output_dir / TEMPLATE_OUTPUT_NAME
    schema_path = output_dir / SCHEMA_OUTPUT_NAME
    allowed_path = output_dir / ALLOWED_VALUES_OUTPUT_NAME
    check_path = output_dir / CHECK_OUTPUT_NAME
    summary_path = output_dir / CHECK_SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    template.to_csv(template_path, index=False, encoding="utf-8-sig")
    schema.to_csv(schema_path, index=False, encoding="utf-8-sig")
    allowed.to_csv(allowed_path, index=False, encoding="utf-8-sig")
    check.to_csv(check_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, int(len(template)), summary)

    payload = {
        "owner_branch": OWNER_BRANCH,
        "template_rows": int(len(template)),
        "schema_fields": int(len(schema)),
        "allowed_value_rows": int(len(allowed)),
        "check_error_count": int(summary.loc[summary["severity"].eq("error"), "count"].iloc[0]),
        "check_warning_count": int(summary.loc[summary["severity"].eq("warning"), "count"].iloc[0]),
        "check_passed": int(summary.loc[summary["severity"].eq("check_passed"), "count"].iloc[0]),
        "outputs": {
            "template": str(template_path),
            "schema": str(schema_path),
            "allowed_values": str(allowed_path),
            "check": str(check_path),
            "check_summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["check_error_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
