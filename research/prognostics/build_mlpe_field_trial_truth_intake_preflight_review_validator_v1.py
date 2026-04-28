#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from mlpe_field_trial_user_input_contract_v1 import require_explicit_user_filled_input
except ImportError:
    from research.prognostics.mlpe_field_trial_user_input_contract_v1 import require_explicit_user_filled_input


OWNER_BRANCH = "BR-20260425-125"
DEFAULT_PREFLIGHT = "/private/tmp/mlpe_field_trial_truth_intake_preflight_checklist_br124_check/mlpe_field_trial_truth_intake_preflight_v1.csv"
DEFAULT_REVIEWED_CHECKLIST = "/private/tmp/mlpe_field_trial_truth_intake_preflight_checklist_br124_check/mlpe_field_trial_truth_intake_preflight_checklist_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_truth_intake_preflight_review_validator_br125_check"

VALIDATION_OUTPUT_NAME = "mlpe_field_trial_truth_intake_preflight_review_validation_v1.csv"
ISSUES_OUTPUT_NAME = "mlpe_field_trial_truth_intake_preflight_review_issues_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_truth_intake_preflight_review_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_truth_intake_preflight_review_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_truth_intake_preflight_review_validation_v1.json"

APPROVAL_FIELDS = ["canonical_truth_write_allowed", "truth_intake_allowed", "threshold_patch_allowed", "engine_patch_allowed"]
ALLOWED_CHECK_STATUSES = {"unchecked", "passed", "failed", "blocked"}
REQUIRED_CHECK_IDS = [
    "BR124-CHECK-001",
    "BR124-CHECK-002",
    "BR124-CHECK-003",
    "BR124-CHECK-004",
    "BR124-CHECK-005",
    "BR124-CHECK-006",
]

PREFLIGHT_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "truth_intake_preflight_status",
    "truth_candidate_role",
    "truth_seed_reviewer_decision",
    "source_candidate_status",
    "source_issue_count",
    "required_checklist_item_count",
    "passed_checklist_item_count",
    "truth_intake_preflight_ready_flag",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "source_candidate_package_path",
    "source_blocked_path",
    "preflight_next_action",
]

CHECKLIST_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "check_id",
    "check_name",
    "check_group",
    "required_for_truth_intake",
    "check_status",
    "check_passed_flag",
    "expected_evidence_or_clearance",
    "preflight_operator_note",
]

VALIDATION_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "source_preflight_status",
    "truth_candidate_role",
    "truth_seed_reviewer_decision",
    "required_checklist_item_count",
    "observed_checklist_item_count",
    "passed_checklist_item_count",
    "duplicate_check_id_flag",
    "missing_required_check_flag",
    "invalid_check_status_flag",
    "failed_required_check_flag",
    "source_write_flag_violation_flag",
    "source_preflight_status_invalid_flag",
    "reviewed_preflight_validation_failed_flag",
    "reviewed_preflight_all_checks_passed_flag",
    "future_truth_materialization_precheck_candidate_flag",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "review_validation_bucket",
    "missing_check_ids_csv",
    "invalid_check_ids_csv",
    "failed_check_ids_csv",
    "duplicate_check_ids_csv",
    "next_action",
]

ISSUE_COLUMNS = ["owner_branch", "trial_event_id", "issue_type", "field", "observed_value", "expected_policy"]


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


def source_write_violation(row: pd.Series) -> bool:
    return any(int_value(row.get(field, "0")) != 0 for field in APPROVAL_FIELDS)


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for value in values:
        if not value:
            continue
        if value in seen:
            dupes.add(value)
        seen.add(value)
    return sorted(dupes)


def build_event_validation(row: pd.Series, checklist: pd.DataFrame, preflight_path: Path, checklist_path: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    event_id = normalize_text(row.get("trial_event_id", ""))
    sub = checklist[checklist["trial_event_id"].map(normalize_text).eq(event_id)].copy()
    check_ids = [normalize_text(value) for value in sub["check_id"].tolist()]
    duplicate_check_ids = duplicate_values(check_ids)
    observed_ids = {value for value in check_ids if value}
    missing_check_ids = [check_id for check_id in REQUIRED_CHECK_IDS if check_id not in observed_ids]
    invalid_check_ids = []
    failed_check_ids = []
    issue_rows = []

    for _, check_row in sub.iterrows():
        check_id = normalize_text(check_row.get("check_id", ""))
        check_status = normalize_text(check_row.get("check_status", ""))
        if check_status not in ALLOWED_CHECK_STATUSES:
            invalid_check_ids.append(check_id or "<missing_check_id>")

    for check_id in REQUIRED_CHECK_IDS:
        check_rows = sub[sub["check_id"].map(normalize_text).eq(check_id)]
        if check_rows.empty:
            continue
        first = check_rows.iloc[0]
        passed = normalize_text(first.get("check_status", "")) == "passed" and int_value(first.get("check_passed_flag", "0")) == 1
        if not passed:
            failed_check_ids.append(check_id)

    source_write_flag = source_write_violation(row)
    source_status = normalize_text(row.get("truth_intake_preflight_status", ""))
    source_status_invalid = source_status != "pending_checklist_completion"
    failed = bool(
        duplicate_check_ids
        or missing_check_ids
        or invalid_check_ids
        or failed_check_ids
        or source_write_flag
        or source_status_invalid
    )
    all_checks_passed = int(not failed)
    future_precheck_candidate = all_checks_passed

    def add_issue(issue_type: str, field: str, observed: str, expected: str) -> None:
        issue_rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": event_id,
                "issue_type": issue_type,
                "field": field,
                "observed_value": observed,
                "expected_policy": expected,
            }
        )

    for check_id in duplicate_check_ids:
        add_issue("duplicate_required_check_id", "check_id", check_id, "unique per trial_event_id")
    for check_id in missing_check_ids:
        add_issue("missing_required_check", "check_id", check_id, "all BR-124 required checks present")
    for check_id in invalid_check_ids:
        add_issue("invalid_check_status", "check_status", check_id, "|".join(sorted(ALLOWED_CHECK_STATUSES)))
    for check_id in failed_check_ids:
        add_issue("required_check_not_passed", "check_passed_flag", check_id, "check_status=passed and check_passed_flag=1")
    if source_write_flag:
        add_issue("source_write_flag_violation", "approval_fields", "nonzero", "all source approval fields remain 0")
    if source_status_invalid:
        add_issue("source_preflight_status_invalid", "truth_intake_preflight_status", source_status, "pending_checklist_completion")

    if source_write_flag:
        bucket = "blocked_source_write_flag_violation"
        next_action = "Reset source approval/write fields to 0 before review validation."
    elif source_status_invalid:
        bucket = "blocked_source_preflight_status_invalid"
        next_action = "Use only BR-124 pending checklist rows for reviewed preflight validation."
    elif duplicate_check_ids:
        bucket = "blocked_duplicate_required_check"
        next_action = "Deduplicate reviewed checklist rows before validation."
    elif missing_check_ids:
        bucket = "blocked_missing_required_check"
        next_action = "Attach every required BR-124 checklist item before validation."
    elif invalid_check_ids:
        bucket = "blocked_invalid_check_status"
        next_action = "Use only controlled checklist status values."
    elif failed_check_ids:
        bucket = "blocked_required_check_not_passed"
        next_action = "Resolve failed/unchecked checklist items before truth-intake discussion."
    else:
        bucket = "reviewed_preflight_all_checks_passed"
        next_action = "May enter a later explicit truth materialization precheck; still no canonical write here."

    validation_row = {
        "owner_branch": OWNER_BRANCH,
        "trial_event_id": event_id,
        "source_preflight_status": source_status,
        "truth_candidate_role": normalize_text(row.get("truth_candidate_role", "")),
        "truth_seed_reviewer_decision": normalize_text(row.get("truth_seed_reviewer_decision", "")),
        "required_checklist_item_count": len(REQUIRED_CHECK_IDS),
        "observed_checklist_item_count": int(len(sub)),
        "passed_checklist_item_count": int(
            (
                sub["check_status"].map(normalize_text).eq("passed")
                & sub["check_passed_flag"].map(int_value).eq(1)
            ).sum()
        )
        if len(sub)
        else 0,
        "duplicate_check_id_flag": int(bool(duplicate_check_ids)),
        "missing_required_check_flag": int(bool(missing_check_ids)),
        "invalid_check_status_flag": int(bool(invalid_check_ids)),
        "failed_required_check_flag": int(bool(failed_check_ids)),
        "source_write_flag_violation_flag": int(source_write_flag),
        "source_preflight_status_invalid_flag": int(source_status_invalid),
        "reviewed_preflight_validation_failed_flag": int(failed),
        "reviewed_preflight_all_checks_passed_flag": all_checks_passed,
        "future_truth_materialization_precheck_candidate_flag": future_precheck_candidate,
        "canonical_truth_write_allowed": 0,
        "truth_intake_allowed": 0,
        "threshold_patch_allowed": 0,
        "engine_patch_allowed": 0,
        "review_validation_bucket": bucket,
        "missing_check_ids_csv": ",".join(missing_check_ids),
        "invalid_check_ids_csv": ",".join(invalid_check_ids),
        "failed_check_ids_csv": ",".join(failed_check_ids),
        "duplicate_check_ids_csv": ",".join(duplicate_check_ids),
        "next_action": next_action,
    }
    return validation_row, issue_rows


def build_validation(preflight: pd.DataFrame, checklist: pd.DataFrame, preflight_path: Path, checklist_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    validation_rows = []
    issue_rows = []
    preflight_ids = {normalize_text(value) for value in preflight["trial_event_id"].tolist() if normalize_text(value)}

    for _, row in preflight.iterrows():
        validation_row, event_issues = build_event_validation(row, checklist, preflight_path, checklist_path)
        validation_rows.append(validation_row)
        issue_rows.extend(event_issues)

    checklist_ids = {normalize_text(value) for value in checklist["trial_event_id"].tolist() if normalize_text(value)}
    for orphan_event_id in sorted(checklist_ids - preflight_ids):
        validation_rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": orphan_event_id,
                "source_preflight_status": "missing_preflight_row",
                "truth_candidate_role": "",
                "truth_seed_reviewer_decision": "",
                "required_checklist_item_count": len(REQUIRED_CHECK_IDS),
                "observed_checklist_item_count": int(checklist["trial_event_id"].map(normalize_text).eq(orphan_event_id).sum()),
                "passed_checklist_item_count": 0,
                "duplicate_check_id_flag": 0,
                "missing_required_check_flag": 0,
                "invalid_check_status_flag": 0,
                "failed_required_check_flag": 0,
                "source_write_flag_violation_flag": 0,
                "source_preflight_status_invalid_flag": 1,
                "reviewed_preflight_validation_failed_flag": 1,
                "reviewed_preflight_all_checks_passed_flag": 0,
                "future_truth_materialization_precheck_candidate_flag": 0,
                "canonical_truth_write_allowed": 0,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "review_validation_bucket": "blocked_missing_preflight_row",
                "missing_check_ids_csv": "",
                "invalid_check_ids_csv": "",
                "failed_check_ids_csv": "",
                "duplicate_check_ids_csv": "",
                "next_action": "Attach checklist rows to a BR-124 preflight row before validation.",
            }
        )
        issue_rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": orphan_event_id,
                "issue_type": "missing_preflight_row",
                "field": "trial_event_id",
                "observed_value": orphan_event_id,
                "expected_policy": "checklist event must exist in BR-124 preflight table",
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
            "reviewed_preflight_rows": int(len(validation)),
            "reviewed_preflight_all_checks_passed_rows": int(validation["reviewed_preflight_all_checks_passed_flag"].sum()) if len(validation) else 0,
            "future_truth_materialization_precheck_candidate_rows": int(validation["future_truth_materialization_precheck_candidate_flag"].sum()) if len(validation) else 0,
            "reviewed_preflight_validation_failed_rows": int(validation["reviewed_preflight_validation_failed_flag"].sum()) if len(validation) else 0,
            "issue_rows": int(len(issues)),
            "canonical_truth_write_allowed_sum": int(validation["canonical_truth_write_allowed"].sum()) if len(validation) else 0,
            "truth_intake_allowed_sum": int(validation["truth_intake_allowed"].sum()) if len(validation) else 0,
            "threshold_patch_allowed_sum": int(validation["threshold_patch_allowed"].sum()) if len(validation) else 0,
            "engine_patch_allowed_sum": int(validation["engine_patch_allowed"].sum()) if len(validation) else 0,
        }
    ]
    if len(validation):
        for bucket, sub in validation.groupby("review_validation_bucket", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "review_validation_bucket",
                    "summary_key": bucket,
                    "reviewed_preflight_rows": int(len(sub)),
                    "reviewed_preflight_all_checks_passed_rows": int(sub["reviewed_preflight_all_checks_passed_flag"].sum()),
                    "future_truth_materialization_precheck_candidate_rows": int(sub["future_truth_materialization_precheck_candidate_flag"].sum()),
                    "reviewed_preflight_validation_failed_rows": int(sub["reviewed_preflight_validation_failed_flag"].sum()),
                    "issue_rows": int(len(issues[issues["trial_event_id"].isin(sub["trial_event_id"])])) if len(issues) else 0,
                    "canonical_truth_write_allowed_sum": int(sub["canonical_truth_write_allowed"].sum()),
                    "truth_intake_allowed_sum": int(sub["truth_intake_allowed"].sum()),
                    "threshold_patch_allowed_sum": int(sub["threshold_patch_allowed"].sum()),
                    "engine_patch_allowed_sum": int(sub["engine_patch_allowed"].sum()),
                }
            )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, summary: pd.DataFrame) -> Path:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-125 MLPE Field-Trial Reviewed Preflight Validator",
        "",
        "## Purpose",
        "- Validate reviewed BR-124 preflight checklist rows.",
        "- Require all six required checks to be present and passed before a row can become a later materialization-precheck candidate.",
        "- Keep the result sidecar-only; do not authorize canonical truth, threshold, or engine writes.",
        "",
        "## Result",
        f"- reviewed preflight rows: `{overall['reviewed_preflight_rows']}`",
        f"- all-checks-passed rows: `{overall['reviewed_preflight_all_checks_passed_rows']}`",
        f"- future truth materialization precheck candidate rows: `{overall['future_truth_materialization_precheck_candidate_rows']}`",
        f"- validation-failed rows: `{overall['reviewed_preflight_validation_failed_rows']}`",
        f"- issue rows: `{overall['issue_rows']}`",
        f"- canonical truth write allowed sum: `{overall['canonical_truth_write_allowed_sum']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Passing this validator is still not canonical truth materialization.",
        "- Approval/write fields remain locked to `0`.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--preflight", default=DEFAULT_PREFLIGHT)
    parser.add_argument("--reviewed-checklist", default=DEFAULT_REVIEWED_CHECKLIST)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--allow-user-filled-default", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    preflight_path = resolve_path(repo_root, args.preflight)
    checklist_path = resolve_path(repo_root, args.reviewed_checklist)
    output_dir = resolve_path(repo_root, args.output_dir)
    require_explicit_user_filled_input(
        input_name="reviewed preflight checklist",
        input_path=checklist_path,
        default_path=DEFAULT_REVIEWED_CHECKLIST,
        allow_user_filled_default=args.allow_user_filled_default,
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    preflight = read_csv(preflight_path, PREFLIGHT_COLUMNS)
    checklist = read_csv(checklist_path, CHECKLIST_COLUMNS)
    validation, issues = build_validation(preflight, checklist, preflight_path, checklist_path)
    summary = build_summary(validation, issues)

    validation_path = output_dir / VALIDATION_OUTPUT_NAME
    issues_path = output_dir / ISSUES_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    validation.to_csv(validation_path, index=False, encoding="utf-8-sig")
    issues.to_csv(issues_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "reviewed_preflight_rows": int(overall["reviewed_preflight_rows"]),
        "reviewed_preflight_all_checks_passed_rows": int(overall["reviewed_preflight_all_checks_passed_rows"]),
        "future_truth_materialization_precheck_candidate_rows": int(overall["future_truth_materialization_precheck_candidate_rows"]),
        "reviewed_preflight_validation_failed_rows": int(overall["reviewed_preflight_validation_failed_rows"]),
        "issue_rows": int(overall["issue_rows"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
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
