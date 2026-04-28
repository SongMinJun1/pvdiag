#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-104"
DEFAULT_CAPTURE_INPUT = "/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv"
DEFAULT_READINESS_INPUT = "/private/tmp/mlpe_field_trial_capture_readiness_br103_check/mlpe_field_trial_capture_readiness_packet_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_operator_intake_br104_check"

CHECKLIST_OUTPUT_NAME = "mlpe_field_trial_operator_intake_checklist_v1.csv"
FIELD_GUIDE_OUTPUT_NAME = "mlpe_field_trial_operator_intake_field_guide_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_operator_intake_summary_v1.csv"
RUNBOOK_OUTPUT_NAME = "mlpe_field_trial_operator_intake_runbook_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_operator_intake_guide_v1.json"

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

READINESS_COLUMNS = [
    "trial_event_id",
    "readiness_bucket",
    "metadata_ready_flag",
    "required_evidence_paths_filled_flag",
    "required_evidence_paths_exist_flag",
]

REQUIRED_CAPTURE_METADATA = [
    "site",
    "root_id",
    "panel_id",
    "mlpe_device_id",
    "start_ts",
    "end_ts",
    "injection_strength",
    "timestamp_quality",
    "communication_quality",
]

REQUIRED_CONTEXT_METADATA = [
    "capture_status",
    "injection_case",
    "planned_fault_family",
    "planned_fault_subtype",
    "affected_scope",
    "injection_mode",
    "expected_signature",
    "mlpe_state",
]

REQUIRED_EVIDENCE_PATHS = ["raw_data_path", "peer_data_path", "waveform_slice_path"]
OPTIONAL_EVIDENCE_PATHS = ["weather_data_path"]
REQUIRED_RECHECK_VALUES = {
    "timestamp_quality": {"", "unchecked"},
    "communication_quality": {"", "unchecked"},
}

FIELD_GUIDE_ROWS = [
    ("planning", "trial_event_id", "always", "Stable row identifier used by later readiness and adjudication packets.", "free text"),
    ("planning", "capture_status", "always", "Use planned before capture and captured after data collection.", "planned|captured"),
    ("planning", "injection_case", "always", "Keeps the intended MLPE/PV test scenario attached to the row.", "BR-102 controlled value"),
    ("planning", "planned_fault_family", "always", "Top-level planned family; this is not the final label.", "BR-101 family"),
    ("planning", "planned_fault_subtype", "always", "Planned subtype under the selected family; this is not the final label.", "BR-101 subtype"),
    ("planning", "affected_scope", "always", "Panel, substring, root, site, or unknown scope planned for the event.", "panel|substring|string|root|site|unknown"),
    ("planning", "injection_mode", "always", "How the event is created or observed.", "physical|electrical_emulator|mlpe_control|telemetry|environment|observed_only"),
    ("planning", "expected_signature", "always", "Expected V/I/P morphology family before field capture.", "BR-102 controlled value"),
    ("capture", "site", "when capture_status != planned", "Site identifier for grouping and common-cause review.", "free text"),
    ("capture", "root_id", "when available", "Root/string/group context for synchrony and common-cause review.", "free text"),
    ("capture", "panel_id", "when capture_status != planned", "Exact target panel; needed before panel-local evidence can be trusted.", "free text"),
    ("capture", "mlpe_device_id", "when capture_status != planned", "Exact MLPE device identifier paired to the panel.", "free text"),
    ("capture", "start_ts", "when capture_status != planned", "Capture window start in a stable timestamp convention.", "ISO-like timestamp"),
    ("capture", "end_ts", "when capture_status != planned", "Capture window end in a stable timestamp convention.", "ISO-like timestamp"),
    ("capture", "injection_strength", "when capture_status != planned", "Operator-entered intensity or descriptive strength for the event.", "free text"),
    ("capture", "mlpe_state", "when capture_status != planned", "MLPE state observed during the event.", "normal|clipping|mppt_anomaly|rapid_shutdown|dropout|control_delay|unknown"),
    ("capture", "raw_data_path", "when capture_status != planned", "Exact raw data slice path for the event.", "path"),
    ("capture", "peer_data_path", "when capture_status != planned", "Peer/reference panel data path for common-cause and artifact clearance.", "path"),
    ("capture", "waveform_slice_path", "when capture_status != planned", "Waveform or high-resolution slice path for morphology review.", "path"),
    ("capture", "weather_data_path", "optional but recommended", "Weather/irradiance context path; useful for environmental/common-cause separation.", "path"),
    ("capture", "timestamp_quality", "when capture_status != planned", "Timestamp quality guard before event alignment.", "unchecked|ok|skewed|missing|mixed"),
    ("capture", "communication_quality", "when capture_status != planned", "Communication quality guard before treating the row as physical evidence.", "unchecked|ok|dropout|stale|missing|mixed"),
    ("adjudication", "final_fault_family", "final adjudication only", "Final label family; leave blank until labels are formally attached.", "BR-101 family"),
    ("adjudication", "final_fault_subtype", "final adjudication only", "Final label subtype; leave blank until labels are formally attached.", "BR-101 subtype"),
    ("adjudication", "final_truth_confidence", "final adjudication only", "Confidence level for final truth row.", "confirmed_injected|confirmed_observed|probable|ambiguous|negative_control"),
    ("adjudication", "final_label_attached", "final adjudication only", "Must stay 0 until final labels are formally attached.", "0|1"),
]

CHECKLIST_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "injection_case",
    "planned_fault_family",
    "planned_fault_subtype",
    "affected_scope",
    "expected_signature",
    "br103_readiness_bucket",
    "operator_phase",
    "capture_metadata_to_fill_csv",
    "evidence_paths_to_attach_csv",
    "optional_context_to_attach_csv",
    "do_not_fill_final_label_until_adjudication",
    "truth_intake_allowed",
    "operator_promotion_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "next_operator_action",
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_capture(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing capture input: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    for col in CAPTURE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    out = df.reindex(columns=CAPTURE_COLUMNS).copy()
    for col in CAPTURE_COLUMNS:
        out[col] = out[col].map(normalize_text)
    return out


def read_readiness(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=READINESS_COLUMNS)
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    for col in READINESS_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    out = df.reindex(columns=READINESS_COLUMNS).copy()
    for col in READINESS_COLUMNS:
        out[col] = out[col].map(normalize_text)
    return out


def build_field_guide() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "operator_phase": phase,
                "field_name": field,
                "required_when": required_when,
                "operator_purpose": purpose,
                "value_hint": hint,
            }
            for phase, field, required_when, purpose, hint in FIELD_GUIDE_ROWS
        ]
    )


def build_checklist(capture: pd.DataFrame, readiness: pd.DataFrame) -> pd.DataFrame:
    readiness_map = {
        row["trial_event_id"]: row
        for _, row in readiness.iterrows()
        if normalize_text(row.get("trial_event_id", ""))
    }
    rows = []
    for _, row in capture.iterrows():
        trial_event_id = row["trial_event_id"]
        read_row = readiness_map.get(trial_event_id, {})
        bucket = normalize_text(read_row.get("readiness_bucket", "")) or "readiness_not_run"
        captured = row["capture_status"] != "planned"

        metadata_fields = []
        for field in [*REQUIRED_CAPTURE_METADATA, *REQUIRED_CONTEXT_METADATA]:
            value = row[field]
            if not value or value in REQUIRED_RECHECK_VALUES.get(field, set()):
                metadata_fields.append(field)
        evidence_fields = [field for field in REQUIRED_EVIDENCE_PATHS if not row[field]]
        optional_fields = [field for field in OPTIONAL_EVIDENCE_PATHS if not row[field]]

        if not captured:
            operator_phase = "planning"
            next_action = "Plan the field-trial event, then fill capture metadata and evidence paths during capture."
        elif bucket == "capture_ready_label_pending":
            operator_phase = "adjudication_ready"
            next_action = "Send to final adjudication; do not promote to truth intake until labels are attached."
        else:
            operator_phase = "capture_cleanup"
            next_action = "Resolve missing metadata, raw, peer, and waveform evidence before adjudication."

        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": trial_event_id,
                "injection_case": row["injection_case"],
                "planned_fault_family": row["planned_fault_family"],
                "planned_fault_subtype": row["planned_fault_subtype"],
                "affected_scope": row["affected_scope"],
                "expected_signature": row["expected_signature"],
                "br103_readiness_bucket": bucket,
                "operator_phase": operator_phase,
                "capture_metadata_to_fill_csv": ",".join(metadata_fields),
                "evidence_paths_to_attach_csv": ",".join(evidence_fields),
                "optional_context_to_attach_csv": ",".join(optional_fields),
                "do_not_fill_final_label_until_adjudication": 1,
                "truth_intake_allowed": 0,
                "operator_promotion_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "next_operator_action": next_action,
            }
        )
    return pd.DataFrame(rows).reindex(columns=CHECKLIST_COLUMNS)


def build_summary(checklist: pd.DataFrame, field_guide: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "rows": int(len(checklist)),
            "field_guide_rows": int(len(field_guide)),
            "planning_rows": int(checklist["operator_phase"].eq("planning").sum()),
            "capture_cleanup_rows": int(checklist["operator_phase"].eq("capture_cleanup").sum()),
            "adjudication_ready_rows": int(checklist["operator_phase"].eq("adjudication_ready").sum()),
            "truth_intake_allowed_sum": int(checklist["truth_intake_allowed"].sum()),
            "engine_patch_allowed_sum": int(checklist["engine_patch_allowed"].sum()),
            "threshold_patch_allowed_sum": int(checklist["threshold_patch_allowed"].sum()),
        }
    ]
    for phase, sub in checklist.groupby("operator_phase", dropna=False):
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "operator_phase",
                "summary_key": phase,
                "rows": int(len(sub)),
                "field_guide_rows": 0,
                "planning_rows": int(sub["operator_phase"].eq("planning").sum()),
                "capture_cleanup_rows": int(sub["operator_phase"].eq("capture_cleanup").sum()),
                "adjudication_ready_rows": int(sub["operator_phase"].eq("adjudication_ready").sum()),
                "truth_intake_allowed_sum": int(sub["truth_intake_allowed"].sum()),
                "engine_patch_allowed_sum": int(sub["engine_patch_allowed"].sum()),
                "threshold_patch_allowed_sum": int(sub["threshold_patch_allowed"].sum()),
            }
        )
    return pd.DataFrame(rows)


def write_runbook(output_dir: Path, checklist: pd.DataFrame, summary: pd.DataFrame) -> Path:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    runbook_path = output_dir / RUNBOOK_OUTPUT_NAME
    lines = [
        "# BR-104 MLPE Field-Trial Operator Intake Guide",
        "",
        "## Purpose",
        "- Convert the BR-102 capture template and BR-103 readiness packet into an operator-facing intake checklist.",
        "- Tell the field team what metadata and evidence paths must be filled before adjudication.",
        "- Keep final labels, truth intake, threshold tuning, and engine patches blocked.",
        "",
        "## Real Result",
        f"- checklist rows: `{overall['rows']}`",
        f"- field guide rows: `{overall['field_guide_rows']}`",
        f"- planning rows: `{overall['planning_rows']}`",
        f"- capture cleanup rows: `{overall['capture_cleanup_rows']}`",
        f"- adjudication-ready rows: `{overall['adjudication_ready_rows']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        "",
        "## Operator Rule",
        "- Fill site, panel, MLPE, time window, timestamp quality, communication quality, raw path, peer path, and waveform path first.",
        "- Leave final labels blank until final adjudication.",
        "- Re-run BR-103 readiness after rows are filled.",
        "- Only rows that become `capture_ready_label_pending` should move to final adjudication.",
        "",
        "## Boundary",
        "- This guide is not a truth table.",
        "- This guide does not approve operator promotion, threshold tuning, or engine changes.",
    ]
    runbook_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return runbook_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--capture-input", default=DEFAULT_CAPTURE_INPUT)
    parser.add_argument("--readiness-input", default=DEFAULT_READINESS_INPUT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    capture_input = resolve_path(repo_root, args.capture_input)
    readiness_input = resolve_path(repo_root, args.readiness_input)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    capture = read_capture(capture_input)
    readiness = read_readiness(readiness_input)
    field_guide = build_field_guide()
    checklist = build_checklist(capture, readiness)
    summary = build_summary(checklist, field_guide)

    checklist_path = output_dir / CHECKLIST_OUTPUT_NAME
    field_guide_path = output_dir / FIELD_GUIDE_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    checklist.to_csv(checklist_path, index=False, encoding="utf-8-sig")
    field_guide.to_csv(field_guide_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    runbook_path = write_runbook(output_dir, checklist, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "rows": int(overall["rows"]),
        "field_guide_rows": int(overall["field_guide_rows"]),
        "planning_rows": int(overall["planning_rows"]),
        "capture_cleanup_rows": int(overall["capture_cleanup_rows"]),
        "adjudication_ready_rows": int(overall["adjudication_ready_rows"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "outputs": {
            "checklist": str(checklist_path),
            "field_guide": str(field_guide_path),
            "summary": str(summary_path),
            "runbook": str(runbook_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
