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


OWNER_BRANCH = "BR-20260425-116"
DEFAULT_LABEL_INPUT = "/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_template_v1.csv"
DEFAULT_SCHEMA = "research/prognostics/contracts/mlpe_field_trial_v1/final_label_intake_schema/mlpe_field_trial_final_label_intake_schema_v1.csv"
DEFAULT_ALLOWED_VALUES = "research/prognostics/contracts/mlpe_field_trial_v1/final_label_intake_schema/mlpe_field_trial_final_label_allowed_values_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_final_label_validator_br116_check"

VALIDATION_OUTPUT_NAME = "mlpe_field_trial_final_label_validation_v1.csv"
ISSUE_OUTPUT_NAME = "mlpe_field_trial_final_label_validation_issues_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_final_label_validation_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_final_label_validation_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_final_label_validation_v1.json"

APPROVAL_FIELDS = ["truth_intake_allowed", "threshold_patch_allowed", "engine_patch_allowed"]

LABEL_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "packet_status",
    "source_preflight_bucket",
    "reviewer_final_fault_family",
    "reviewer_final_fault_subtype",
    "reviewer_truth_confidence",
    "reviewer_common_cause_clearance",
    "reviewer_measurement_artifact_clearance",
    "reviewer_label_source",
    "reviewer",
    "reviewed_at",
    "reviewer_notes",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

SCHEMA_COLUMNS = ["column", "required_when_packet_row_exists", "edit_policy"]
ALLOWED_VALUE_COLUMNS = ["field", "allowed_value"]

VALIDATION_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "packet_status",
    "source_preflight_bucket",
    "duplicate_label_event_id_flag",
    "required_fields_missing_flag",
    "allowed_value_violation_flag",
    "approval_flag_violation_flag",
    "reviewer_label_complete_flag",
    "label_validation_failed_flag",
    "truth_gate_candidate_flag",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "label_validation_bucket",
    "missing_required_fields_csv",
    "invalid_allowed_value_fields_csv",
    "approval_flag_violation_fields_csv",
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


def resolve_label_input(
    repo_root: Path,
    label_input_value: str | Path,
    manifest: dict[str, Any],
    explicit_flags: set[str],
) -> tuple[Path, str]:
    if "--label-input" in explicit_flags:
        return resolve_path(repo_root, label_input_value), "explicit_cli"
    if manifest:
        manifest_value = manifest_path_value(manifest, "label_input")
        if not manifest_value:
            raise KeyError(
                "MLPE field-trial input manifest is missing `label_input`; "
                "pass --label-input explicitly or add inputs.label_input"
            )
        return resolve_path(repo_root, manifest_value), "input_manifest"
    return resolve_path(repo_root, label_input_value), "legacy_default"


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


def build_validation(label_input: pd.DataFrame, schema: pd.DataFrame, allowed_values: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    req_fields = required_fields(schema)
    allowed = allowed_value_map(allowed_values)
    label_input = label_input.copy()
    for col in LABEL_COLUMNS:
        if col not in label_input.columns:
            label_input[col] = ""

    duplicate_ids = set(
        label_input[label_input["trial_event_id"].astype(str).duplicated(keep=False)]["trial_event_id"].map(normalize_text).tolist()
    )
    validation_rows = []
    issue_rows = []

    for _, row in label_input.iterrows():
        event_id = normalize_text(row["trial_event_id"])
        duplicate_flag = int(bool(event_id and event_id in duplicate_ids))
        missing_fields = [field for field in req_fields if not normalize_text(row.get(field, ""))]
        invalid_allowed_fields = []
        approval_violations = []

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
                        "expected_policy": "must_remain_0_before_truth_gate",
                    }
                )

        if duplicate_flag:
            issue_rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "issue_type": "duplicate_label_event_id",
                    "field": "trial_event_id",
                    "observed_value": event_id,
                    "expected_policy": "unique",
                }
            )

        failed = int(bool(duplicate_flag or missing_fields or invalid_allowed_fields or approval_violations))
        complete = int(not failed and bool(event_id))
        truth_gate_candidate = complete
        if duplicate_flag:
            bucket = "duplicate_label_event_id"
            next_action = "Deduplicate label rows before validation can proceed."
        elif approval_violations:
            bucket = "blocked_approval_flag_violation"
            next_action = "Reset approval flags to 0; labels cannot self-authorize truth or patches."
        elif missing_fields:
            bucket = "blocked_required_fields_missing"
            next_action = "Complete required reviewer label fields."
        elif invalid_allowed_fields:
            bucket = "blocked_allowed_value_violation"
            next_action = "Use only BR-115 allowed values or update schema in a separate branch."
        elif complete:
            bucket = "label_valid_truth_gate_required"
            next_action = "Send valid labels to a separate truth-intake gate; do not promote directly."
        else:
            bucket = "blocked_empty_event_id"
            next_action = "Attach label row to a packet trial_event_id."

        validation_rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": event_id,
                "packet_status": normalize_text(row.get("packet_status", "")),
                "source_preflight_bucket": normalize_text(row.get("source_preflight_bucket", "")),
                "duplicate_label_event_id_flag": duplicate_flag,
                "required_fields_missing_flag": int(bool(missing_fields)),
                "allowed_value_violation_flag": int(bool(invalid_allowed_fields)),
                "approval_flag_violation_flag": int(bool(approval_violations)),
                "reviewer_label_complete_flag": complete,
                "label_validation_failed_flag": failed,
                "truth_gate_candidate_flag": truth_gate_candidate,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "label_validation_bucket": bucket,
                "missing_required_fields_csv": ",".join(missing_fields),
                "invalid_allowed_value_fields_csv": ",".join(invalid_allowed_fields),
                "approval_flag_violation_fields_csv": ",".join(approval_violations),
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
            "label_rows": int(len(validation)),
            "valid_label_rows": int(validation["reviewer_label_complete_flag"].sum()) if len(validation) else 0,
            "validation_failed_rows": int(validation["label_validation_failed_flag"].sum()) if len(validation) else 0,
            "truth_gate_candidate_rows": int(validation["truth_gate_candidate_flag"].sum()) if len(validation) else 0,
            "issue_rows": int(len(issues)),
            "truth_intake_allowed_sum": int(validation["truth_intake_allowed"].sum()) if len(validation) else 0,
            "threshold_patch_allowed_sum": int(validation["threshold_patch_allowed"].sum()) if len(validation) else 0,
            "engine_patch_allowed_sum": int(validation["engine_patch_allowed"].sum()) if len(validation) else 0,
        }
    ]
    if len(validation):
        for bucket, sub in validation.groupby("label_validation_bucket", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "label_validation_bucket",
                    "summary_key": bucket,
                    "label_rows": int(len(sub)),
                    "valid_label_rows": int(sub["reviewer_label_complete_flag"].sum()),
                    "validation_failed_rows": int(sub["label_validation_failed_flag"].sum()),
                    "truth_gate_candidate_rows": int(sub["truth_gate_candidate_flag"].sum()),
                    "issue_rows": int(len(issues[issues["trial_event_id"].isin(sub["trial_event_id"])])) if len(issues) else 0,
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
        "# BR-116 MLPE Field-Trial Final Label Validator",
        "",
        "## Purpose",
        "- Validate filled BR-115 reviewer labels before any truth-intake gate.",
        "- Keep label validity separate from truth, threshold, and engine approval.",
        "",
        "## Inputs",
        f"- label input manifest: `{input_manifest_path if input_manifest_path is not None else 'not provided'}`",
        "",
        "## Input Resolution Sources",
        f"- `label_input`: `{source_map.get('label_input', 'legacy_default')}`",
        "",
        "## Real Result",
        f"- label rows: `{overall['label_rows']}`",
        f"- valid label rows: `{overall['valid_label_rows']}`",
        f"- validation-failed rows: `{overall['validation_failed_rows']}`",
        f"- truth-gate candidate rows: `{overall['truth_gate_candidate_rows']}`",
        f"- issue rows: `{overall['issue_rows']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Valid labels still require BR-117 truth-intake gating.",
        "- Labels cannot self-authorize threshold or engine patches.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--input-manifest", default=None)
    parser.add_argument("--label-input", default=DEFAULT_LABEL_INPUT)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA)
    parser.add_argument("--allowed-values", default=DEFAULT_ALLOWED_VALUES)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--allow-user-filled-default", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    input_manifest_path, input_manifest = load_input_manifest(repo_root, args.input_manifest)
    explicit_flags = {
        flag
        for flag in ["--label-input"]
        if cli_flag_provided(flag, sys.argv[1:])
    }
    label_path, label_input_source = resolve_label_input(
        repo_root,
        args.label_input,
        input_manifest,
        explicit_flags,
    )
    input_resolution_sources = {"label_input": label_input_source}
    schema_path = resolve_path(repo_root, args.schema)
    allowed_values_path = resolve_path(repo_root, args.allowed_values)
    output_dir = resolve_path(repo_root, args.output_dir)
    require_explicit_user_filled_input(
        input_name="final label input",
        input_path=label_path,
        default_path=DEFAULT_LABEL_INPUT,
        allow_user_filled_default=args.allow_user_filled_default,
        explicit_flag="--label-input",
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    label_input = read_csv(label_path, LABEL_COLUMNS)
    schema = read_csv(schema_path, SCHEMA_COLUMNS)
    allowed_values = read_csv(allowed_values_path, ALLOWED_VALUE_COLUMNS)
    validation, issues = build_validation(label_input, schema, allowed_values)
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
        "label_rows": int(overall["label_rows"]),
        "valid_label_rows": int(overall["valid_label_rows"]),
        "validation_failed_rows": int(overall["validation_failed_rows"]),
        "truth_gate_candidate_rows": int(overall["truth_gate_candidate_rows"]),
        "issue_rows": int(overall["issue_rows"]),
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
