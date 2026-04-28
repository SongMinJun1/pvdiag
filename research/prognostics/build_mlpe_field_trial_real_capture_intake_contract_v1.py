#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from build_mlpe_field_trial_capture_schema_v1 import (
    CAPTURE_COLUMNS,
    CAPTURE_REQUIRED_WHEN_NOT_PLANNED,
    CONTROLLED_VALUES,
    SUBTYPES_BY_FAMILY,
    check_capture,
    normalize_text,
)


OWNER_BRANCH = "BR-20260425-129"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_real_capture_intake_contract_br129_check"

CONTRACT_OUTPUT_NAME = "mlpe_field_trial_real_capture_intake_contract_v1.csv"
VALIDATION_OUTPUT_NAME = "mlpe_field_trial_real_capture_intake_validation_v1.csv"
ISSUES_OUTPUT_NAME = "mlpe_field_trial_real_capture_intake_issues_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_real_capture_intake_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_real_capture_intake_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_real_capture_intake_contract_v1.json"

APPROVAL_FIELDS = ["operator_promotion_allowed", "engine_patch_allowed", "threshold_patch_allowed"]
REQUIRED_PATH_FIELDS = ["raw_data_path", "peer_data_path", "waveform_slice_path"]
OPTIONAL_PATH_FIELDS = ["weather_data_path"]

CONTRACT_COLUMNS = [
    "owner_branch",
    "field",
    "field_group",
    "required_policy",
    "allowed_values_csv",
    "path_policy",
    "intake_rule",
]

VALIDATION_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "row_index",
    "capture_status",
    "intake_validation_status",
    "schema_error_count",
    "schema_warning_count",
    "missing_required_path_count",
    "missing_existing_path_count",
    "approval_flag_violation_flag",
    "label_attached_flag",
    "real_capture_intake_ready_flag",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "capture_input_path",
    "intake_next_action",
]

ISSUE_COLUMNS = ["owner_branch", "trial_event_id", "row_index", "issue_type", "field", "observed_value", "expected_policy"]


def int_value(value: object) -> int:
    text = normalize_text(value)
    if not text:
        return 0
    return int(float(text))


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def build_contract() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for field in CAPTURE_COLUMNS:
        if field in CAPTURE_REQUIRED_WHEN_NOT_PLANNED:
            required_policy = "required_when_capture_status_not_planned"
        elif field in APPROVAL_FIELDS:
            required_policy = "must_remain_zero"
        elif field.startswith("final_") or field == "label_status":
            required_policy = "label_lifecycle_controlled"
        else:
            required_policy = "optional_or_template_controlled"

        if field in REQUIRED_PATH_FIELDS:
            path_policy = "required_path_after_capture; existence checked when --require-existing-paths is set"
        elif field in OPTIONAL_PATH_FIELDS:
            path_policy = "optional_path; existence checked only when non-empty and --require-existing-paths is set"
        else:
            path_policy = ""

        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "field": field,
                "field_group": field_group(field),
                "required_policy": required_policy,
                "allowed_values_csv": ",".join(CONTROLLED_VALUES.get(field, [])),
                "path_policy": path_policy,
                "intake_rule": intake_rule(field),
            }
        )
    return pd.DataFrame(rows).reindex(columns=CONTRACT_COLUMNS)


def field_group(field: str) -> str:
    if field in {"trial_event_id", "site", "root_id", "panel_id", "mlpe_device_id"}:
        return "identity"
    if field in {"start_ts", "end_ts", "capture_status"}:
        return "time_status"
    if field.startswith("planned_") or field in {"injection_case", "affected_scope", "injection_mode", "injection_strength", "expected_signature", "mlpe_state"}:
        return "planned_fault_metadata"
    if field in REQUIRED_PATH_FIELDS or field in OPTIONAL_PATH_FIELDS:
        return "evidence_path"
    if field in {"timestamp_quality", "communication_quality"}:
        return "quality_clearance"
    if field.startswith("final_") or field == "label_status":
        return "future_label"
    if field in APPROVAL_FIELDS:
        return "approval_boundary"
    return "review"


def intake_rule(field: str) -> str:
    if field in APPROVAL_FIELDS:
        return "must be 0; intake never authorizes operator, threshold, or engine writes"
    if field in REQUIRED_PATH_FIELDS:
        return "must be non-empty after capture_status leaves planned"
    if field in OPTIONAL_PATH_FIELDS:
        return "optional, but if supplied should resolve under repo-root or absolute path"
    if field in {"final_fault_family", "final_fault_subtype", "final_truth_confidence"}:
        return "must stay blank while label_status=label_pending"
    if field == "final_label_attached":
        return "0 until final label intake"
    if field == "label_status":
        return "label_pending is expected for BR-129 real capture intake"
    return "use BR-102 capture schema rule"


def add_issue(issues: list[dict[str, object]], event_id: str, row_index: int, issue_type: str, field: str, observed: str, expected: str) -> None:
    issues.append(
        {
            "owner_branch": OWNER_BRANCH,
            "trial_event_id": event_id,
            "row_index": row_index,
            "issue_type": issue_type,
            "field": field,
            "observed_value": observed,
            "expected_policy": expected,
        }
    )


def read_capture_input(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing capture input: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    return df.copy()


def normalize_capture_for_row_checks(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in CAPTURE_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    out = out.reindex(columns=CAPTURE_COLUMNS)
    for col in out.columns:
        out[col] = out[col].map(normalize_text)
    return out


def path_exists(repo_root: Path, value: str) -> bool:
    if not value:
        return False
    return resolve_path(repo_root, value).exists()


def schema_issue_counts(schema_checks: pd.DataFrame) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    if schema_checks.empty or "trial_event_id" not in schema_checks.columns:
        return counts
    for _, row in schema_checks.iterrows():
        severity = normalize_text(row.get("severity", ""))
        event_id = normalize_text(row.get("trial_event_id", ""))
        if not event_id:
            event_id = "__global__"
        if severity not in {"error", "warning"}:
            continue
        bucket = counts.setdefault(event_id, {"error": 0, "warning": 0})
        bucket[severity] += 1
    return counts


def validate_capture(repo_root: Path, capture_path: Path | None, require_existing_paths: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    if capture_path is None:
        validation = pd.DataFrame(
            [
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": "",
                    "row_index": 0,
                    "capture_status": "missing_capture_csv",
                    "intake_validation_status": "blocked_missing_capture_csv",
                    "schema_error_count": 0,
                    "schema_warning_count": 0,
                    "missing_required_path_count": 0,
                    "missing_existing_path_count": 0,
                    "approval_flag_violation_flag": 0,
                    "label_attached_flag": 0,
                    "real_capture_intake_ready_flag": 0,
                    "canonical_truth_write_allowed": 0,
                    "truth_intake_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "engine_patch_allowed": 0,
                    "capture_input_path": "",
                    "intake_next_action": "Provide a real KTC ESS capture CSV and rerun BR-129 before BR-130.",
                }
            ]
        ).reindex(columns=VALIDATION_COLUMNS)
        issues = pd.DataFrame(
            [
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": "",
                    "row_index": 0,
                    "issue_type": "missing_capture_csv",
                    "field": "capture_input",
                    "observed_value": "",
                    "expected_policy": "real KTC ESS capture CSV path",
                }
            ]
        ).reindex(columns=ISSUE_COLUMNS)
        return validation, issues

    raw = read_capture_input(capture_path)
    schema_checks = check_capture(raw)
    schema_counts = schema_issue_counts(schema_checks)
    normalized = normalize_capture_for_row_checks(raw)
    validation_rows: list[dict[str, object]] = []
    issue_rows: list[dict[str, object]] = []

    for _, check in schema_checks.iterrows():
        severity = normalize_text(check.get("severity", ""))
        if severity not in {"error", "warning"}:
            continue
        event_id = normalize_text(check.get("trial_event_id", ""))
        add_issue(
            issue_rows,
            event_id,
            0,
            f"schema_{severity}",
            normalize_text(check.get("field", "")),
            normalize_text(check.get("message", "")),
            "BR-102 capture schema must pass",
        )

    for idx, row in normalized.iterrows():
        event_id = normalize_text(row.get("trial_event_id", "")) or f"row_{idx + 1}"
        capture_status = normalize_text(row.get("capture_status", ""))
        row_counts = schema_counts.get(event_id, {"error": 0, "warning": 0})
        missing_required_path_count = 0
        missing_existing_path_count = 0

        if capture_status != "planned":
            for field in REQUIRED_PATH_FIELDS:
                value = normalize_text(row.get(field, ""))
                if not value:
                    missing_required_path_count += 1
                    add_issue(issue_rows, event_id, idx + 1, "missing_required_path", field, "", "required after capture_status leaves planned")
                elif require_existing_paths and not path_exists(repo_root, value):
                    missing_existing_path_count += 1
                    add_issue(issue_rows, event_id, idx + 1, "path_not_found", field, value, "path exists")

        if require_existing_paths:
            for field in OPTIONAL_PATH_FIELDS:
                value = normalize_text(row.get(field, ""))
                if value and not path_exists(repo_root, value):
                    missing_existing_path_count += 1
                    add_issue(issue_rows, event_id, idx + 1, "optional_path_not_found", field, value, "path exists or field blank")

        approval_violation = any(int_value(row.get(field, "0")) != 0 for field in APPROVAL_FIELDS)
        if approval_violation:
            add_issue(issue_rows, event_id, idx + 1, "approval_flag_violation", "approval_fields", "nonzero", "all approval fields remain 0")

        label_attached = int_value(row.get("final_label_attached", "0")) != 0 or normalize_text(row.get("label_status", "")) == "label_attached"
        if label_attached:
            add_issue(issue_rows, event_id, idx + 1, "label_attached_too_early", "label_status", normalize_text(row.get("label_status", "")), "BR-129 expects capture intake before final label attachment")

        ready = int(
            row_counts.get("error", 0) == 0
            and missing_required_path_count == 0
            and missing_existing_path_count == 0
            and not approval_violation
            and not label_attached
            and capture_status != "planned"
        )
        if ready:
            status = "real_capture_intake_ready"
            next_action = "May enter BR-130 real capture intake run; still no truth/threshold/engine approval."
        elif capture_status == "planned":
            status = "blocked_still_planned"
            next_action = "Fill real capture metadata before BR-130."
        elif row_counts.get("error", 0):
            status = "blocked_schema_errors"
            next_action = "Fix BR-102 schema errors before BR-130."
        elif missing_required_path_count or missing_existing_path_count:
            status = "blocked_path_policy"
            next_action = "Attach required raw/peer/waveform paths before BR-130."
        elif approval_violation:
            status = "blocked_approval_flag_violation"
            next_action = "Reset approval flags to 0."
        elif label_attached:
            status = "blocked_label_attached_too_early"
            next_action = "Use label intake gates later; BR-129 is capture intake only."
        else:
            status = "blocked_review_required"
            next_action = "Review unresolved capture intake blockers before BR-130."

        validation_rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": event_id,
                "row_index": idx + 1,
                "capture_status": capture_status,
                "intake_validation_status": status,
                "schema_error_count": row_counts.get("error", 0),
                "schema_warning_count": row_counts.get("warning", 0),
                "missing_required_path_count": missing_required_path_count,
                "missing_existing_path_count": missing_existing_path_count,
                "approval_flag_violation_flag": int(approval_violation),
                "label_attached_flag": int(label_attached),
                "real_capture_intake_ready_flag": ready,
                "canonical_truth_write_allowed": 0,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "capture_input_path": str(capture_path),
                "intake_next_action": next_action,
            }
        )

    return (
        pd.DataFrame(validation_rows).reindex(columns=VALIDATION_COLUMNS),
        pd.DataFrame(issue_rows).reindex(columns=ISSUE_COLUMNS),
    )


def build_summary(validation: pd.DataFrame, issues: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "capture_rows": int(len(validation)),
            "real_capture_intake_ready_rows": int(validation["real_capture_intake_ready_flag"].sum()) if len(validation) else 0,
            "blocked_rows": int((validation["real_capture_intake_ready_flag"].map(int_value) == 0).sum()) if len(validation) else 0,
            "issue_rows": int(len(issues)),
            "canonical_truth_write_allowed_sum": int(validation["canonical_truth_write_allowed"].sum()) if len(validation) else 0,
            "truth_intake_allowed_sum": int(validation["truth_intake_allowed"].sum()) if len(validation) else 0,
            "threshold_patch_allowed_sum": int(validation["threshold_patch_allowed"].sum()) if len(validation) else 0,
            "engine_patch_allowed_sum": int(validation["engine_patch_allowed"].sum()) if len(validation) else 0,
        }
    ]
    if len(validation):
        for status, sub in validation.groupby("intake_validation_status", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "intake_validation_status",
                    "summary_key": status,
                    "capture_rows": int(len(sub)),
                    "real_capture_intake_ready_rows": int(sub["real_capture_intake_ready_flag"].sum()),
                    "blocked_rows": int((sub["real_capture_intake_ready_flag"].map(int_value) == 0).sum()),
                    "issue_rows": int(len(issues[issues["trial_event_id"].isin(sub["trial_event_id"])])) if len(issues) else 0,
                    "canonical_truth_write_allowed_sum": int(sub["canonical_truth_write_allowed"].sum()),
                    "truth_intake_allowed_sum": int(sub["truth_intake_allowed"].sum()),
                    "threshold_patch_allowed_sum": int(sub["threshold_patch_allowed"].sum()),
                    "engine_patch_allowed_sum": int(sub["engine_patch_allowed"].sum()),
                }
            )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, summary: pd.DataFrame, capture_input: Path | None, require_existing_paths: bool) -> Path:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-129 MLPE Field-Trial Real Capture Intake Contract",
        "",
        "## Purpose",
        "- Define and dry-run the real KTC ESS capture CSV intake contract before accepting real rows.",
        "- Reuse BR-102 capture schema instead of inventing a second schema.",
        "- Keep final labels, truth intake, threshold patch, and engine patch blocked.",
        "",
        "## Result",
        f"- capture input: `{str(capture_input) if capture_input else ''}`",
        f"- require existing paths: `{int(require_existing_paths)}`",
        f"- capture rows: `{overall['capture_rows']}`",
        f"- intake-ready rows: `{overall['real_capture_intake_ready_rows']}`",
        f"- blocked rows: `{overall['blocked_rows']}`",
        f"- issue rows: `{overall['issue_rows']}`",
        f"- canonical truth write allowed sum: `{overall['canonical_truth_write_allowed_sum']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Missing capture CSV is a valid fail-closed dry-run state.",
        "- Intake-ready rows are not truth rows.",
        "- Final labels must stay out of BR-129.",
        "- Approval/write fields remain locked to `0`.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--capture-input", default="")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--require-existing-paths", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    capture_input = normalize_text(args.capture_input)
    capture_path = resolve_path(repo_root, capture_input) if capture_input else None
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    contract = build_contract()
    validation, issues = validate_capture(repo_root, capture_path, bool(args.require_existing_paths))
    summary = build_summary(validation, issues)

    contract_path = output_dir / CONTRACT_OUTPUT_NAME
    validation_path = output_dir / VALIDATION_OUTPUT_NAME
    issues_path = output_dir / ISSUES_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    contract.to_csv(contract_path, index=False, encoding="utf-8-sig")
    validation.to_csv(validation_path, index=False, encoding="utf-8-sig")
    issues.to_csv(issues_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary, capture_path, bool(args.require_existing_paths))

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "capture_rows": int(overall["capture_rows"]),
        "real_capture_intake_ready_rows": int(overall["real_capture_intake_ready_rows"]),
        "blocked_rows": int(overall["blocked_rows"]),
        "issue_rows": int(overall["issue_rows"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "contract": str(contract_path),
            "validation": str(validation_path),
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
