#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from mlpe_field_trial_user_input_contract_v1 import require_explicit_user_filled_input
except ImportError:
    from research.prognostics.mlpe_field_trial_user_input_contract_v1 import require_explicit_user_filled_input


OWNER_BRANCH = "BR-20260425-122"
DEFAULT_DECISION_INPUT = "/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_schema_br121_check/mlpe_field_trial_truth_seed_reviewer_decision_template_v1.csv"
DEFAULT_SCHEMA = "research/prognostics/contracts/mlpe_field_trial_v1/truth_seed_reviewer_decision_schema/mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.csv"
DEFAULT_ALLOWED_VALUES = "research/prognostics/contracts/mlpe_field_trial_v1/truth_seed_reviewer_decision_schema/mlpe_field_trial_truth_seed_reviewer_decision_allowed_values_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_validator_br122_check"

VALIDATION_OUTPUT_NAME = "mlpe_field_trial_truth_seed_reviewer_decision_validation_v1.csv"
ISSUE_OUTPUT_NAME = "mlpe_field_trial_truth_seed_reviewer_decision_validation_issues_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_truth_seed_reviewer_decision_validation_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_truth_seed_reviewer_decision_validation_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_truth_seed_reviewer_decision_validation_v1.json"

APPROVAL_FIELDS = ["canonical_truth_write_allowed", "truth_intake_allowed", "threshold_patch_allowed", "engine_patch_allowed"]

DECISION_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "truth_seed_review_packet_status",
    "truth_candidate_role",
    "reviewer_final_fault_family",
    "reviewer_final_fault_subtype",
    "reviewer_truth_confidence",
    "reviewer_common_cause_clearance",
    "reviewer_measurement_artifact_clearance",
    "reviewer_label_source",
    "truth_gate_bucket",
    "truth_seed_reviewer_decision",
    "truth_seed_reviewer_confidence",
    "truth_seed_independent_evidence_status",
    "truth_seed_common_cause_final_clearance",
    "truth_seed_measurement_artifact_final_clearance",
    "truth_seed_counterexample_check_status",
    "truth_seed_reviewer_decision_source",
    "truth_seed_reviewer",
    "truth_seed_reviewed_at",
    "truth_seed_reviewer_notes",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

SCHEMA_COLUMNS = ["column", "required_when_packet_row_exists", "edit_policy"]
ALLOWED_VALUE_COLUMNS = ["field", "allowed_value"]

VALIDATION_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "truth_seed_reviewer_decision",
    "truth_candidate_role",
    "duplicate_decision_event_id_flag",
    "required_fields_missing_flag",
    "allowed_value_violation_flag",
    "approval_flag_violation_flag",
    "approval_requirements_failed_flag",
    "reviewer_decision_complete_flag",
    "decision_validation_failed_flag",
    "future_truth_intake_candidate_flag",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "decision_validation_bucket",
    "missing_required_fields_csv",
    "invalid_allowed_value_fields_csv",
    "approval_flag_violation_fields_csv",
    "approval_requirement_failures_csv",
    "next_action",
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


def resolve_decision_input(
    repo_root: Path,
    decision_input_value: str | Path,
    manifest: dict[str, Any],
    explicit_flags: set[str],
) -> tuple[Path, str]:
    if "--decision-input" in explicit_flags:
        return resolve_path(repo_root, decision_input_value), "explicit_cli"
    if manifest:
        manifest_value = manifest_path_value(manifest, "decision_input")
        if not manifest_value:
            raise KeyError(
                "MLPE field-trial input manifest is missing `decision_input`; "
                "pass --decision-input explicitly or add inputs.decision_input"
            )
        return resolve_path(repo_root, manifest_value), "input_manifest"
    return resolve_path(repo_root, decision_input_value), "legacy_default"


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


def required_fields(schema: pd.DataFrame) -> list[str]:
    rows = schema[schema["required_when_packet_row_exists"].map(normalize_text).eq("1")]
    return [normalize_text(value) for value in rows["column"].tolist() if normalize_text(value)]


def allowed_value_map(allowed_values: pd.DataFrame) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for _, row in allowed_values.iterrows():
        field = normalize_text(row["field"])
        value = normalize_text(row["allowed_value"])
        if field and value:
            out.setdefault(field, set()).add(value)
    return out


def approval_requirement_failures(row: pd.Series) -> list[str]:
    if normalize_text(row.get("truth_seed_reviewer_decision", "")) != "approve_for_future_truth_intake":
        return []
    required_values = {
        "truth_seed_reviewer_confidence": "confirmed",
        "truth_seed_independent_evidence_status": "independent_evidence_confirmed",
        "truth_seed_common_cause_final_clearance": "final_cleared_panel_local",
        "truth_seed_measurement_artifact_final_clearance": "final_cleared_physical",
        "truth_seed_counterexample_check_status": "checked_no_counterexample",
    }
    return [field for field, expected in required_values.items() if normalize_text(row.get(field, "")) != expected]


def build_validation(decision_input: pd.DataFrame, schema: pd.DataFrame, allowed_values: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    req_fields = required_fields(schema)
    allowed = allowed_value_map(allowed_values)
    decision_input = decision_input.copy()
    for col in DECISION_COLUMNS:
        if col not in decision_input.columns:
            decision_input[col] = ""

    duplicate_ids = set(
        decision_input[decision_input["trial_event_id"].astype(str).duplicated(keep=False)]["trial_event_id"].map(normalize_text).tolist()
    )
    validation_rows = []
    issue_rows = []

    for _, row in decision_input.iterrows():
        event_id = normalize_text(row["trial_event_id"])
        duplicate_flag = int(bool(event_id and event_id in duplicate_ids))
        missing_fields = [field for field in req_fields if not normalize_text(row.get(field, ""))]
        invalid_allowed_fields = []
        approval_violations = []
        approval_failures = approval_requirement_failures(row)

        for field, valid_values in allowed.items():
            observed = normalize_text(row.get(field, ""))
            if observed and observed not in valid_values:
                invalid_allowed_fields.append(field)
                issue_rows.append(
                    {
                        "owner_branch": OWNER_BRANCH,
                        "trial_event_id": event_id,
                        "issue_type": "allowed_value_violation",
                        "field": field,
                        "observed_value": observed,
                        "expected_policy": "|".join(sorted(valid_values)),
                    }
                )

        for field in missing_fields:
            issue_rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "issue_type": "required_field_missing",
                    "field": field,
                    "observed_value": "",
                    "expected_policy": "required_when_packet_row_exists",
                }
            )

        for field in APPROVAL_FIELDS:
            observed = normalize_text(row.get(field, ""))
            if observed != "0":
                approval_violations.append(field)
                issue_rows.append(
                    {
                        "owner_branch": OWNER_BRANCH,
                        "trial_event_id": event_id,
                        "issue_type": "approval_flag_violation",
                        "field": field,
                        "observed_value": observed,
                        "expected_policy": "must_remain_0_before_explicit_truth_intake_branch",
                    }
                )

        if duplicate_flag:
            issue_rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "issue_type": "duplicate_decision_event_id",
                    "field": "trial_event_id",
                    "observed_value": event_id,
                    "expected_policy": "unique",
                }
            )

        for field in approval_failures:
            issue_rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "issue_type": "approval_requirement_failed",
                    "field": field,
                    "observed_value": normalize_text(row.get(field, "")),
                    "expected_policy": "required_for_approve_for_future_truth_intake",
                }
            )

        failed = int(bool(duplicate_flag or missing_fields or invalid_allowed_fields or approval_violations or approval_failures))
        decision_complete = int(not failed and bool(event_id))
        decision = normalize_text(row.get("truth_seed_reviewer_decision", ""))
        future_candidate = int(decision_complete and decision == "approve_for_future_truth_intake")

        if duplicate_flag:
            bucket = "duplicate_decision_event_id"
            next_action = "Deduplicate reviewer decision rows before validation can proceed."
        elif approval_violations:
            bucket = "blocked_approval_flag_violation"
            next_action = "Reset approval fields to 0; reviewer decisions cannot self-authorize writes or patches."
        elif missing_fields:
            bucket = "blocked_required_fields_missing"
            next_action = "Complete required reviewer decision fields."
        elif invalid_allowed_fields:
            bucket = "blocked_allowed_value_violation"
            next_action = "Use only BR-121 allowed decision values or update schema in a separate branch."
        elif approval_failures:
            bucket = "blocked_approval_requirements_failed"
            next_action = "Approve decisions require confirmed evidence, final clearances, and counterexample check."
        elif future_candidate:
            bucket = "validated_future_truth_intake_candidate"
            next_action = "Candidate may enter a later explicit sidecar truth-intake package; do not write canonical truth."
        elif decision == "reject_not_truth_seed":
            bucket = "validated_reject_not_truth_seed"
            next_action = "Keep out of truth intake; retain as reviewed negative/reject evidence."
        elif decision == "defer_needs_more_evidence":
            bucket = "validated_defer_needs_more_evidence"
            next_action = "Keep in evidence request queue until more support arrives."
        elif decision_complete:
            bucket = "validated_non_approve_decision"
            next_action = "No truth-intake candidate created."
        else:
            bucket = "blocked_empty_event_id"
            next_action = "Attach reviewer decision row to a trial_event_id."

        validation_rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": event_id,
                "truth_seed_reviewer_decision": decision,
                "truth_candidate_role": normalize_text(row.get("truth_candidate_role", "")),
                "duplicate_decision_event_id_flag": duplicate_flag,
                "required_fields_missing_flag": int(bool(missing_fields)),
                "allowed_value_violation_flag": int(bool(invalid_allowed_fields)),
                "approval_flag_violation_flag": int(bool(approval_violations)),
                "approval_requirements_failed_flag": int(bool(approval_failures)),
                "reviewer_decision_complete_flag": decision_complete,
                "decision_validation_failed_flag": failed,
                "future_truth_intake_candidate_flag": future_candidate,
                "canonical_truth_write_allowed": 0,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "decision_validation_bucket": bucket,
                "missing_required_fields_csv": ",".join(missing_fields),
                "invalid_allowed_value_fields_csv": ",".join(invalid_allowed_fields),
                "approval_flag_violation_fields_csv": ",".join(approval_violations),
                "approval_requirement_failures_csv": ",".join(approval_failures),
                "next_action": next_action,
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
            "decision_rows": int(len(validation)),
            "valid_decision_rows": int(validation["reviewer_decision_complete_flag"].sum()) if len(validation) else 0,
            "validation_failed_rows": int(validation["decision_validation_failed_flag"].sum()) if len(validation) else 0,
            "future_truth_intake_candidate_rows": int(validation["future_truth_intake_candidate_flag"].sum()) if len(validation) else 0,
            "issue_rows": int(len(issues)),
            "canonical_truth_write_allowed_sum": int(validation["canonical_truth_write_allowed"].sum()) if len(validation) else 0,
            "truth_intake_allowed_sum": int(validation["truth_intake_allowed"].sum()) if len(validation) else 0,
            "threshold_patch_allowed_sum": int(validation["threshold_patch_allowed"].sum()) if len(validation) else 0,
            "engine_patch_allowed_sum": int(validation["engine_patch_allowed"].sum()) if len(validation) else 0,
        }
    ]
    if len(validation):
        for bucket, sub in validation.groupby("decision_validation_bucket", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "decision_validation_bucket",
                    "summary_key": bucket,
                    "decision_rows": int(len(sub)),
                    "valid_decision_rows": int(sub["reviewer_decision_complete_flag"].sum()),
                    "validation_failed_rows": int(sub["decision_validation_failed_flag"].sum()),
                    "future_truth_intake_candidate_rows": int(sub["future_truth_intake_candidate_flag"].sum()),
                    "issue_rows": int(len(issues[issues["trial_event_id"].isin(sub["trial_event_id"])])) if len(issues) else 0,
                    "canonical_truth_write_allowed_sum": int(sub["canonical_truth_write_allowed"].sum()),
                    "truth_intake_allowed_sum": int(sub["truth_intake_allowed"].sum()),
                    "threshold_patch_allowed_sum": int(sub["threshold_patch_allowed"].sum()),
                    "engine_patch_allowed_sum": int(sub["engine_patch_allowed"].sum()),
                }
            )
    return pd.DataFrame(rows)


def write_note(
    output_dir: Path,
    summary: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> Path:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    source_map = input_resolution_sources or {}
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-122 MLPE Field-Trial Truth-Seed Reviewer Decision Validator",
        "",
        "## Purpose",
        "- Validate filled BR-121 reviewer decisions before any future truth-intake candidate package.",
        "- Keep reviewer decisions separate from canonical truth writes and algorithm patches.",
        "",
        "## Inputs",
        f"- truth-seed reviewer decision input manifest: `{input_manifest_path if input_manifest_path is not None else 'not provided'}`",
        "",
        "## Input Resolution Sources",
        f"- `decision_input`: `{source_map.get('decision_input', 'legacy_default')}`",
        "",
        "## Result",
        f"- decision rows: `{overall['decision_rows']}`",
        f"- valid decision rows: `{overall['valid_decision_rows']}`",
        f"- validation-failed rows: `{overall['validation_failed_rows']}`",
        f"- future truth-intake candidate rows: `{overall['future_truth_intake_candidate_rows']}`",
        f"- issue rows: `{overall['issue_rows']}`",
        f"- canonical truth write allowed sum: `{overall['canonical_truth_write_allowed_sum']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- A validated future truth-intake candidate is still not a canonical truth write.",
        "- Approval/write fields remain locked to `0`.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--input-manifest", default=None)
    parser.add_argument("--decision-input", default=DEFAULT_DECISION_INPUT)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA)
    parser.add_argument("--allowed-values", default=DEFAULT_ALLOWED_VALUES)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--allow-user-filled-default", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    input_manifest_path, input_manifest = load_input_manifest(repo_root, args.input_manifest)
    explicit_flags = {
        flag
        for flag in ["--decision-input"]
        if cli_flag_provided(flag, sys.argv[1:])
    }
    decision_path, decision_source = resolve_decision_input(
        repo_root,
        args.decision_input,
        input_manifest,
        explicit_flags,
    )
    input_resolution_sources = {"decision_input": decision_source}
    schema_path = resolve_path(repo_root, args.schema)
    allowed_values_path = resolve_path(repo_root, args.allowed_values)
    output_dir = resolve_path(repo_root, args.output_dir)
    require_explicit_user_filled_input(
        input_name="truth-seed reviewer decision input",
        input_path=decision_path,
        default_path=DEFAULT_DECISION_INPUT,
        allow_user_filled_default=args.allow_user_filled_default,
        explicit_flag="--decision-input",
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    decision_input = read_csv(decision_path, DECISION_COLUMNS)
    schema = read_csv(schema_path, SCHEMA_COLUMNS)
    allowed_values = read_csv(allowed_values_path, ALLOWED_VALUE_COLUMNS)
    validation, issues = build_validation(decision_input, schema, allowed_values)
    summary = build_summary(validation, issues)

    validation_path = output_dir / VALIDATION_OUTPUT_NAME
    issues_path = output_dir / ISSUE_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    validation.to_csv(validation_path, index=False, encoding="utf-8-sig")
    issues.to_csv(issues_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary, input_manifest_path, input_resolution_sources)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "decision_rows": int(overall["decision_rows"]),
        "valid_decision_rows": int(overall["valid_decision_rows"]),
        "validation_failed_rows": int(overall["validation_failed_rows"]),
        "future_truth_intake_candidate_rows": int(overall["future_truth_intake_candidate_rows"]),
        "issue_rows": int(overall["issue_rows"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "input_manifest": str(input_manifest_path) if input_manifest_path is not None else "",
        "input_resolution_sources": input_resolution_sources,
        "outputs": {
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
