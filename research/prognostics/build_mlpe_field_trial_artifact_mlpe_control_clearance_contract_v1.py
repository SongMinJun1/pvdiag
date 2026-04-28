#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-135"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_artifact_mlpe_control_clearance_contract_br135_check"

CONTRACT_OUTPUT_NAME = "mlpe_field_trial_artifact_mlpe_control_clearance_contract_v1.csv"
CLEARANCE_OUTPUT_NAME = "mlpe_field_trial_artifact_mlpe_control_clearance_dry_run_v1.csv"
ISSUES_OUTPUT_NAME = "mlpe_field_trial_artifact_mlpe_control_clearance_contract_issues_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_artifact_mlpe_control_clearance_contract_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_artifact_mlpe_control_clearance_contract_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_artifact_mlpe_control_clearance_contract_v1.json"

APPROVAL_FIELDS = [
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

SOURCE_RESOLUTION_COLUMNS = [
    "trial_event_id",
    "real_capture_intake_ready_flag",
    "evidence_required_flag",
    "source_evidence_blocking_flag",
    "source_evidence_resolved_flag",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

CLEARANCE_INPUT_COLUMNS = [
    "trial_event_id",
    "site",
    "root_id",
    "panel_id",
    "event_date",
    "timestamp_quality",
    "communication_quality",
    "telemetry_dropout_flag",
    "telemetry_stuck_flag",
    "impossible_value_flag",
    "sensor_offset_suspect_flag",
    "mlpe_state",
    "optimizer_state_known_flag",
    "mlpe_control_fault_suspect_flag",
    "rapid_shutdown_or_safety_state_flag",
    "panel_physical_evidence_flag",
    "reviewer_artifact_clearance_flag",
    "reviewer_mlpe_control_clearance_flag",
    "artifact_mlpe_control_clearance_note",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

CLEARANCE_GROUPS = [
    {
        "clearance_group": "source_evidence_ready",
        "required_flag": 1,
        "required_fields_csv": "BR-131 event-level source_evidence_ready",
        "pass_condition": "BR-131 required groups have no source_evidence_blocking_flag",
        "blocked_status": "blocked_source_evidence_not_ready",
        "next_gate_use": "BR-136 input eligibility",
    },
    {
        "clearance_group": "timestamp_quality_clearance",
        "required_flag": 1,
        "required_fields_csv": "timestamp_quality",
        "pass_condition": "timestamp_quality=ok",
        "blocked_status": "blocked_timestamp_quality_not_cleared",
        "next_gate_use": "measurement artifact blocker",
    },
    {
        "clearance_group": "communication_quality_clearance",
        "required_flag": 1,
        "required_fields_csv": "communication_quality",
        "pass_condition": "communication_quality=ok",
        "blocked_status": "blocked_communication_quality_not_cleared",
        "next_gate_use": "measurement artifact blocker",
    },
    {
        "clearance_group": "telemetry_artifact_clearance",
        "required_flag": 1,
        "required_fields_csv": "telemetry_dropout_flag,telemetry_stuck_flag,impossible_value_flag,sensor_offset_suspect_flag,reviewer_artifact_clearance_flag",
        "pass_condition": "artifact flags all 0 and reviewer_artifact_clearance_flag=1",
        "blocked_status": "blocked_telemetry_artifact_not_cleared",
        "next_gate_use": "separate measurement artifact from physical fault",
    },
    {
        "clearance_group": "mlpe_control_state_clearance",
        "required_flag": 1,
        "required_fields_csv": "mlpe_state,optimizer_state_known_flag,mlpe_control_fault_suspect_flag,rapid_shutdown_or_safety_state_flag,reviewer_mlpe_control_clearance_flag",
        "pass_condition": "optimizer state known, no MLPE-control/safety suspect flags, reviewer_mlpe_control_clearance_flag=1",
        "blocked_status": "blocked_mlpe_control_state_not_cleared",
        "next_gate_use": "separate MLPE/control from panel physical fault",
    },
    {
        "clearance_group": "panel_physical_separation_clearance",
        "required_flag": 1,
        "required_fields_csv": "panel_physical_evidence_flag",
        "pass_condition": "panel_physical_evidence_flag=1 after artifact and MLPE/control blockers clear",
        "blocked_status": "blocked_panel_physical_evidence_missing",
        "next_gate_use": "avoid promoting artifact/control as physical panel fault",
    },
    {
        "clearance_group": "reviewer_clearance_note",
        "required_flag": 1,
        "required_fields_csv": "artifact_mlpe_control_clearance_note",
        "pass_condition": "note is non-empty",
        "blocked_status": "blocked_reviewer_clearance_missing",
        "next_gate_use": "audit trail before sidecar truth package",
    },
]

CONTRACT_COLUMNS = [
    "owner_branch",
    "clearance_group",
    "required_flag",
    "required_fields_csv",
    "pass_condition",
    "blocked_status",
    "next_gate_use",
]

CLEARANCE_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "site",
    "root_id",
    "panel_id",
    "event_date",
    "clearance_group",
    "required_flag",
    "source_evidence_ready_flag",
    "clearance_row_present_flag",
    "clearance_passed_flag",
    "clearance_blocking_flag",
    "artifact_mlpe_control_clearance_status",
    "timestamp_quality",
    "communication_quality",
    "telemetry_artifact_flag_sum",
    "mlpe_state",
    "mlpe_control_blocker_flag_sum",
    "panel_physical_evidence_flag",
    "artifact_mlpe_control_clearance_note",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "clearance_next_action",
]

ISSUE_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "issue_type",
    "field",
    "observed_value",
    "expected_policy",
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def int_value(value: object) -> int:
    text = normalize_text(value)
    if not text:
        return 0
    return int(float(text))


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_csv(path: Path, required_columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing input: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    for col in required_columns:
        if col not in df.columns:
            df[col] = ""
    out = df.copy()
    for col in out.columns:
        out[col] = out[col].map(normalize_text)
    return out


def build_contract() -> pd.DataFrame:
    rows = [{"owner_branch": OWNER_BRANCH, **group} for group in CLEARANCE_GROUPS]
    return pd.DataFrame(rows).reindex(columns=CONTRACT_COLUMNS)


def add_issue(issues: list[dict[str, object]], event_id: str, issue_type: str, field: str, observed: str, expected: str) -> None:
    issues.append(
        {
            "owner_branch": OWNER_BRANCH,
            "trial_event_id": event_id,
            "issue_type": issue_type,
            "field": field,
            "observed_value": observed,
            "expected_policy": expected,
        }
    )


def approval_violation(row: pd.Series) -> bool:
    return any(int_value(row.get(field, "0")) != 0 for field in APPROVAL_FIELDS)


def source_ready_by_event(source_resolution: pd.DataFrame) -> dict[str, int]:
    ready: dict[str, int] = {}
    for event_id, sub in source_resolution[source_resolution["trial_event_id"].map(normalize_text).ne("")].groupby("trial_event_id"):
        required = sub[sub["evidence_required_flag"].map(int_value).eq(1)]
        event_ready = int(sub["real_capture_intake_ready_flag"].map(int_value).max()) == 1 if len(sub) else False
        no_blocking = int(required["source_evidence_blocking_flag"].map(int_value).sum()) == 0 if len(required) else False
        no_write = not any(approval_violation(row) for _, row in sub.iterrows())
        ready[event_id] = int(event_ready and no_blocking and no_write)
    return ready


def build_missing_input_rows() -> tuple[pd.DataFrame, pd.DataFrame]:
    clearance = pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": "",
                "site": "",
                "root_id": "",
                "panel_id": "",
                "event_date": "",
                "clearance_group": "contract_input",
                "required_flag": 1,
                "source_evidence_ready_flag": 0,
                "clearance_row_present_flag": 0,
                "clearance_passed_flag": 0,
                "clearance_blocking_flag": 1,
                "artifact_mlpe_control_clearance_status": "blocked_missing_source_evidence_resolution",
                "timestamp_quality": "",
                "communication_quality": "",
                "telemetry_artifact_flag_sum": 0,
                "mlpe_state": "",
                "mlpe_control_blocker_flag_sum": 0,
                "panel_physical_evidence_flag": 0,
                "artifact_mlpe_control_clearance_note": "",
                "canonical_truth_write_allowed": 0,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "clearance_next_action": "Run BR-131/132 source-evidence resolution before artifact/MLPE-control clearance.",
            }
        ]
    ).reindex(columns=CLEARANCE_COLUMNS)
    issues = pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": "",
                "issue_type": "missing_source_evidence_resolution",
                "field": "source_evidence_resolution",
                "observed_value": "",
                "expected_policy": "BR-131/132 source-evidence resolution rows",
            }
        ]
    ).reindex(columns=ISSUE_COLUMNS)
    return clearance, issues


def telemetry_artifact_flag_sum(row: pd.Series) -> int:
    return sum(
        int_value(row.get(field, "0"))
        for field in ["telemetry_dropout_flag", "telemetry_stuck_flag", "impossible_value_flag", "sensor_offset_suspect_flag"]
    )


def mlpe_control_blocker_flag_sum(row: pd.Series) -> int:
    return int_value(row.get("mlpe_control_fault_suspect_flag", "0")) + int_value(row.get("rapid_shutdown_or_safety_state_flag", "0"))


def clearance_status_for_group(group_name: str, source_ready: int, row: pd.Series | None) -> tuple[str, int, int]:
    if source_ready != 1:
        return "blocked_source_evidence_not_ready", 0, 1
    if row is None:
        return "blocked_missing_artifact_mlpe_control_clearance_row", 0, 1
    if approval_violation(row):
        return "blocked_clearance_approval_flag_violation", 0, 1

    if group_name == "source_evidence_ready":
        return "artifact_mlpe_control_clearance_passed", 1, 0
    if group_name == "timestamp_quality_clearance":
        passed = normalize_text(row.get("timestamp_quality", "")).lower() == "ok"
        return ("artifact_mlpe_control_clearance_passed", 1, 0) if passed else ("blocked_timestamp_quality_not_cleared", 0, 1)
    if group_name == "communication_quality_clearance":
        passed = normalize_text(row.get("communication_quality", "")).lower() == "ok"
        return ("artifact_mlpe_control_clearance_passed", 1, 0) if passed else ("blocked_communication_quality_not_cleared", 0, 1)
    if group_name == "telemetry_artifact_clearance":
        passed = telemetry_artifact_flag_sum(row) == 0 and int_value(row.get("reviewer_artifact_clearance_flag", "0")) == 1
        return ("artifact_mlpe_control_clearance_passed", 1, 0) if passed else ("blocked_telemetry_artifact_not_cleared", 0, 1)
    if group_name == "mlpe_control_state_clearance":
        state = normalize_text(row.get("mlpe_state", "")).lower()
        state_clear = state in {"normal", "baseline", "stable", "none"}
        passed = (
            state_clear
            and int_value(row.get("optimizer_state_known_flag", "0")) == 1
            and mlpe_control_blocker_flag_sum(row) == 0
            and int_value(row.get("reviewer_mlpe_control_clearance_flag", "0")) == 1
        )
        return ("artifact_mlpe_control_clearance_passed", 1, 0) if passed else ("blocked_mlpe_control_state_not_cleared", 0, 1)
    if group_name == "panel_physical_separation_clearance":
        passed = int_value(row.get("panel_physical_evidence_flag", "0")) == 1
        return ("artifact_mlpe_control_clearance_passed", 1, 0) if passed else ("blocked_panel_physical_evidence_missing", 0, 1)
    if group_name == "reviewer_clearance_note":
        passed = bool(normalize_text(row.get("artifact_mlpe_control_clearance_note", "")))
        return ("artifact_mlpe_control_clearance_passed", 1, 0) if passed else ("blocked_reviewer_clearance_missing", 0, 1)
    return "blocked_unknown_clearance_group", 0, 1


def build_clearance(
    source_resolution: pd.DataFrame | None,
    clearance_input: pd.DataFrame | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if source_resolution is None:
        return build_missing_input_rows()

    ready_by_event = source_ready_by_event(source_resolution)
    rows: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    clearance_by_event: dict[str, pd.Series] = {}

    if clearance_input is not None:
        duplicate_ids = clearance_input["trial_event_id"][clearance_input["trial_event_id"].duplicated()].map(normalize_text).tolist()
        for event_id in duplicate_ids:
            add_issue(issues, event_id, "duplicate_clearance_row", "trial_event_id", event_id, "one clearance row per trial_event_id")
        for _, row in clearance_input.iterrows():
            event_id = normalize_text(row.get("trial_event_id", ""))
            if event_id and event_id not in clearance_by_event:
                clearance_by_event[event_id] = row

    if not ready_by_event:
        return build_missing_input_rows()

    for event_id, source_ready in ready_by_event.items():
        clearance_row = clearance_by_event.get(event_id)
        if clearance_input is None and source_ready == 1:
            add_issue(issues, event_id, "missing_artifact_mlpe_control_clearance_input", "artifact_mlpe_control_clearance_input", "", "required when source/evidence is ready")
        elif clearance_row is None and source_ready == 1:
            add_issue(issues, event_id, "missing_artifact_mlpe_control_clearance_row", "trial_event_id", event_id, "one clearance row per ready event")
        elif clearance_row is not None and approval_violation(clearance_row):
            add_issue(issues, event_id, "clearance_approval_flag_violation", "approval_fields", "nonzero", "all approval/write fields remain 0")

        for group in CLEARANCE_GROUPS:
            group_name = str(group["clearance_group"])
            status, passed, blocking = clearance_status_for_group(group_name, source_ready, clearance_row)
            if blocking and status not in {"blocked_source_evidence_not_ready", "blocked_missing_artifact_mlpe_control_clearance_row"}:
                add_issue(issues, event_id, status, group_name, "not passed", str(group["pass_condition"]))
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "site": normalize_text(clearance_row.get("site", "")) if clearance_row is not None else "",
                    "root_id": normalize_text(clearance_row.get("root_id", "")) if clearance_row is not None else "",
                    "panel_id": normalize_text(clearance_row.get("panel_id", "")) if clearance_row is not None else "",
                    "event_date": normalize_text(clearance_row.get("event_date", "")) if clearance_row is not None else "",
                    "clearance_group": group_name,
                    "required_flag": int(group["required_flag"]),
                    "source_evidence_ready_flag": source_ready,
                    "clearance_row_present_flag": int(clearance_row is not None),
                    "clearance_passed_flag": passed,
                    "clearance_blocking_flag": blocking,
                    "artifact_mlpe_control_clearance_status": status,
                    "timestamp_quality": normalize_text(clearance_row.get("timestamp_quality", "")) if clearance_row is not None else "",
                    "communication_quality": normalize_text(clearance_row.get("communication_quality", "")) if clearance_row is not None else "",
                    "telemetry_artifact_flag_sum": telemetry_artifact_flag_sum(clearance_row) if clearance_row is not None else 0,
                    "mlpe_state": normalize_text(clearance_row.get("mlpe_state", "")) if clearance_row is not None else "",
                    "mlpe_control_blocker_flag_sum": mlpe_control_blocker_flag_sum(clearance_row) if clearance_row is not None else 0,
                    "panel_physical_evidence_flag": int_value(clearance_row.get("panel_physical_evidence_flag", "0")) if clearance_row is not None else 0,
                    "artifact_mlpe_control_clearance_note": normalize_text(clearance_row.get("artifact_mlpe_control_clearance_note", "")) if clearance_row is not None else "",
                    "canonical_truth_write_allowed": 0,
                    "truth_intake_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "engine_patch_allowed": 0,
                    "clearance_next_action": next_action(status),
                }
            )

    return pd.DataFrame(rows).reindex(columns=CLEARANCE_COLUMNS), pd.DataFrame(issues).reindex(columns=ISSUE_COLUMNS)


def next_action(status: str) -> str:
    if status == "artifact_mlpe_control_clearance_passed":
        return "Keep as artifact/MLPE-control-cleared attachment; no truth, threshold, or engine approval."
    if status == "blocked_source_evidence_not_ready":
        return "Resolve BR-132 source/evidence first."
    if status == "blocked_missing_artifact_mlpe_control_clearance_row":
        return "Attach one artifact/MLPE-control clearance row for this event."
    return "Resolve artifact or MLPE-control blocker before panel-physical eligibility or sidecar truth discussion."


def event_ready_count(clearance: pd.DataFrame) -> int:
    ready = 0
    for _, sub in clearance[clearance["trial_event_id"].map(normalize_text).ne("")].groupby("trial_event_id"):
        required = sub[sub["required_flag"].map(int_value).eq(1)]
        if len(required) and int(required["clearance_blocking_flag"].map(int_value).sum()) == 0:
            ready += 1
    return ready


def build_summary(clearance: pd.DataFrame, issues: pd.DataFrame, contract: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "contract_rows": int(len(contract)),
            "events": int(clearance["trial_event_id"].map(normalize_text).replace("", pd.NA).dropna().nunique()) if len(clearance) else 0,
            "artifact_mlpe_control_clearance_ready_events": event_ready_count(clearance),
            "clearance_rows": int(len(clearance)),
            "clearance_passed_rows": int(clearance["clearance_passed_flag"].map(int_value).sum()) if len(clearance) else 0,
            "clearance_blocked_rows": int(clearance["clearance_blocking_flag"].map(int_value).sum()) if len(clearance) else 0,
            "issue_rows": int(len(issues)),
            "canonical_truth_write_allowed_sum": int(clearance["canonical_truth_write_allowed"].map(int_value).sum()) if len(clearance) else 0,
            "truth_intake_allowed_sum": int(clearance["truth_intake_allowed"].map(int_value).sum()) if len(clearance) else 0,
            "threshold_patch_allowed_sum": int(clearance["threshold_patch_allowed"].map(int_value).sum()) if len(clearance) else 0,
            "engine_patch_allowed_sum": int(clearance["engine_patch_allowed"].map(int_value).sum()) if len(clearance) else 0,
        }
    ]
    if len(clearance):
        for status, sub in clearance.groupby("artifact_mlpe_control_clearance_status", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "artifact_mlpe_control_clearance_status",
                    "summary_key": status,
                    "contract_rows": int(len(contract)),
                    "events": int(sub["trial_event_id"].map(normalize_text).replace("", pd.NA).dropna().nunique()),
                    "artifact_mlpe_control_clearance_ready_events": 0,
                    "clearance_rows": int(len(sub)),
                    "clearance_passed_rows": int(sub["clearance_passed_flag"].map(int_value).sum()),
                    "clearance_blocked_rows": int(sub["clearance_blocking_flag"].map(int_value).sum()),
                    "issue_rows": int(len(issues[issues["trial_event_id"].isin(sub["trial_event_id"])])) if len(issues) else 0,
                    "canonical_truth_write_allowed_sum": int(sub["canonical_truth_write_allowed"].map(int_value).sum()),
                    "truth_intake_allowed_sum": int(sub["truth_intake_allowed"].map(int_value).sum()),
                    "threshold_patch_allowed_sum": int(sub["threshold_patch_allowed"].map(int_value).sum()),
                    "engine_patch_allowed_sum": int(sub["engine_patch_allowed"].map(int_value).sum()),
                }
            )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, summary: pd.DataFrame, source_path: Path | None, clearance_path: Path | None) -> Path:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-135 MLPE Field-Trial Artifact / MLPE-Control Clearance Contract",
        "",
        "## Purpose",
        "- Define measurement-artifact and MLPE-control clearance before BR-136 real-row execution.",
        "- Require source/evidence readiness plus timestamp, communication, telemetry artifact, MLPE/control state, panel-physical separation, and reviewer-note clearance.",
        "- Fail closed when source/evidence rows or artifact/MLPE-control clearance rows are absent.",
        "",
        "## Result",
        f"- source/evidence resolution input: `{str(source_path) if source_path else ''}`",
        f"- artifact/MLPE-control clearance input: `{str(clearance_path) if clearance_path else ''}`",
        f"- contract rows: `{overall['contract_rows']}`",
        f"- events: `{overall['events']}`",
        f"- artifact/MLPE-control-clearance-ready events: `{overall['artifact_mlpe_control_clearance_ready_events']}`",
        f"- clearance rows: `{overall['clearance_rows']}`",
        f"- clearance passed rows: `{overall['clearance_passed_rows']}`",
        f"- clearance blocked rows: `{overall['clearance_blocked_rows']}`",
        f"- issue rows: `{overall['issue_rows']}`",
        f"- canonical truth write allowed sum: `{overall['canonical_truth_write_allowed_sum']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Passing this contract only clears measurement-artifact and MLPE-control blockers for a later sidecar flow.",
        "- It does not create truth labels, threshold approval, or panel-local physical-fault promotion.",
        "- MLPE/control and telemetry artifact rows remain separate from panel physical faults unless explicitly cleared.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--source-evidence-resolution", default="")
    parser.add_argument("--artifact-mlpe-control-clearance-input", default="")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    source_arg = normalize_text(args.source_evidence_resolution)
    clearance_arg = normalize_text(args.artifact_mlpe_control_clearance_input)
    source_path = resolve_path(repo_root, source_arg) if source_arg else None
    clearance_path = resolve_path(repo_root, clearance_arg) if clearance_arg else None
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    contract = build_contract()
    source_resolution = read_csv(source_path, SOURCE_RESOLUTION_COLUMNS) if source_path else None
    clearance_input = read_csv(clearance_path, CLEARANCE_INPUT_COLUMNS) if clearance_path else None
    clearance, issues = build_clearance(source_resolution, clearance_input)
    summary = build_summary(clearance, issues, contract)

    contract_path = output_dir / CONTRACT_OUTPUT_NAME
    clearance_output_path = output_dir / CLEARANCE_OUTPUT_NAME
    issues_path = output_dir / ISSUES_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    contract.to_csv(contract_path, index=False, encoding="utf-8-sig")
    clearance.to_csv(clearance_output_path, index=False, encoding="utf-8-sig")
    issues.to_csv(issues_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary, source_path, clearance_path)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "contract_rows": int(overall["contract_rows"]),
        "events": int(overall["events"]),
        "artifact_mlpe_control_clearance_ready_events": int(overall["artifact_mlpe_control_clearance_ready_events"]),
        "clearance_rows": int(overall["clearance_rows"]),
        "clearance_passed_rows": int(overall["clearance_passed_rows"]),
        "clearance_blocked_rows": int(overall["clearance_blocked_rows"]),
        "issue_rows": int(overall["issue_rows"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "contract": str(contract_path),
            "clearance": str(clearance_output_path),
            "issues": str(issues_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
