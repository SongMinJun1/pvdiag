#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-123"
DEFAULT_VALIDATION = "/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_validator_br122_check/mlpe_field_trial_truth_seed_reviewer_decision_validation_v1.csv"
DEFAULT_ISSUES = "/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_validator_br122_check/mlpe_field_trial_truth_seed_reviewer_decision_validation_issues_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_br123_check"

CANDIDATE_OUTPUT_NAME = "mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.csv"
BLOCKED_OUTPUT_NAME = "mlpe_field_trial_truth_seed_future_truth_intake_blocked_rows_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.json"

APPROVAL_FIELDS = ["canonical_truth_write_allowed", "truth_intake_allowed", "threshold_patch_allowed", "engine_patch_allowed"]

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

ISSUE_COLUMNS = ["owner_branch", "trial_event_id", "issue_type", "field", "observed_value", "expected_policy"]

CANDIDATE_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "truth_seed_future_truth_intake_candidate_status",
    "truth_candidate_role",
    "truth_seed_reviewer_decision",
    "decision_validation_bucket",
    "source_issue_count",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "source_validation_path",
    "source_issues_path",
    "candidate_package_next_action",
]

BLOCKED_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "truth_seed_future_truth_intake_candidate_status",
    "truth_candidate_role",
    "truth_seed_reviewer_decision",
    "decision_validation_bucket",
    "blocker_reason",
    "source_issue_count",
    "source_validation_failed_flag",
    "source_future_truth_intake_candidate_flag",
    "source_write_flag_violation_flag",
    "source_validation_path",
    "source_issues_path",
    "blocked_next_action",
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


def issue_count_map(issues: pd.DataFrame) -> dict[str, int]:
    if issues.empty or "trial_event_id" not in issues.columns:
        return {}
    ids = issues["trial_event_id"].map(normalize_text)
    return ids.value_counts().to_dict()


def source_write_violation(row: pd.Series) -> bool:
    return any(int_value(row.get(field, "0")) != 0 for field in APPROVAL_FIELDS)


def blocker_reason(row: pd.Series, write_violation: bool) -> str:
    if write_violation:
        return "source_write_flag_violation"
    if int_value(row.get("decision_validation_failed_flag", "0")):
        return "source_decision_validation_failed"
    if not int_value(row.get("reviewer_decision_complete_flag", "0")):
        return "source_reviewer_decision_incomplete"
    if not int_value(row.get("future_truth_intake_candidate_flag", "0")):
        return "not_approved_for_future_truth_intake"
    return "not_candidate_after_safety_checks"


def build_package(validation: pd.DataFrame, issues: pd.DataFrame, validation_path: Path, issues_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    counts = issue_count_map(issues)
    candidate_rows = []
    blocked_rows = []

    for _, row in validation.iterrows():
        event_id = normalize_text(row.get("trial_event_id", ""))
        issue_count = int(counts.get(event_id, 0))
        write_violation = source_write_violation(row)
        validation_failed = int_value(row.get("decision_validation_failed_flag", "0"))
        decision_complete = int_value(row.get("reviewer_decision_complete_flag", "0"))
        future_candidate = int_value(row.get("future_truth_intake_candidate_flag", "0"))
        eligible = bool(future_candidate and decision_complete and not validation_failed and not write_violation)

        if eligible:
            candidate_rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "truth_seed_future_truth_intake_candidate_status": "sidecar_future_truth_intake_candidate",
                    "truth_candidate_role": normalize_text(row.get("truth_candidate_role", "")),
                    "truth_seed_reviewer_decision": normalize_text(row.get("truth_seed_reviewer_decision", "")),
                    "decision_validation_bucket": normalize_text(row.get("decision_validation_bucket", "")),
                    "source_issue_count": issue_count,
                    "canonical_truth_write_allowed": 0,
                    "truth_intake_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "engine_patch_allowed": 0,
                    "source_validation_path": str(validation_path),
                    "source_issues_path": str(issues_path),
                    "candidate_package_next_action": "Use in a later explicit sidecar truth-intake review; do not write canonical truth here.",
                }
            )
        else:
            blocked_rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "truth_seed_future_truth_intake_candidate_status": "blocked_before_future_truth_intake_package",
                    "truth_candidate_role": normalize_text(row.get("truth_candidate_role", "")),
                    "truth_seed_reviewer_decision": normalize_text(row.get("truth_seed_reviewer_decision", "")),
                    "decision_validation_bucket": normalize_text(row.get("decision_validation_bucket", "")),
                    "blocker_reason": blocker_reason(row, write_violation),
                    "source_issue_count": issue_count,
                    "source_validation_failed_flag": validation_failed,
                    "source_future_truth_intake_candidate_flag": future_candidate,
                    "source_write_flag_violation_flag": int(write_violation),
                    "source_validation_path": str(validation_path),
                    "source_issues_path": str(issues_path),
                    "blocked_next_action": "Resolve reviewer validation and safety blockers before any truth-intake candidate packaging.",
                }
            )

    return (
        pd.DataFrame(candidate_rows).reindex(columns=CANDIDATE_COLUMNS),
        pd.DataFrame(blocked_rows).reindex(columns=BLOCKED_COLUMNS),
    )


def build_summary(validation: pd.DataFrame, issues: pd.DataFrame, candidates: pd.DataFrame, blocked: pd.DataFrame) -> pd.DataFrame:
    source_valid = int(validation["reviewer_decision_complete_flag"].map(int_value).sum()) if len(validation) else 0
    source_failed = int(validation["decision_validation_failed_flag"].map(int_value).sum()) if len(validation) else 0
    source_future = int(validation["future_truth_intake_candidate_flag"].map(int_value).sum()) if len(validation) else 0
    source_write_violations = int(validation.apply(source_write_violation, axis=1).sum()) if len(validation) else 0
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "source_decision_rows": int(len(validation)),
            "source_valid_decision_rows": source_valid,
            "source_validation_failed_rows": source_failed,
            "source_future_truth_intake_candidate_rows": source_future,
            "candidate_package_rows": int(len(candidates)),
            "blocked_before_candidate_package_rows": int(len(blocked)),
            "source_issue_rows": int(len(issues)),
            "source_write_flag_violation_rows": source_write_violations,
            "canonical_truth_write_allowed_sum": int(candidates["canonical_truth_write_allowed"].sum()) if len(candidates) else 0,
            "truth_intake_allowed_sum": int(candidates["truth_intake_allowed"].sum()) if len(candidates) else 0,
            "threshold_patch_allowed_sum": int(candidates["threshold_patch_allowed"].sum()) if len(candidates) else 0,
            "engine_patch_allowed_sum": int(candidates["engine_patch_allowed"].sum()) if len(candidates) else 0,
        }
    ]
    if len(candidates):
        for role, sub in candidates.groupby("truth_candidate_role", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "truth_candidate_role",
                    "summary_key": role,
                    "source_decision_rows": int(len(validation)),
                    "source_valid_decision_rows": source_valid,
                    "source_validation_failed_rows": source_failed,
                    "source_future_truth_intake_candidate_rows": source_future,
                    "candidate_package_rows": int(len(sub)),
                    "blocked_before_candidate_package_rows": 0,
                    "source_issue_rows": int(len(issues)),
                    "source_write_flag_violation_rows": source_write_violations,
                    "canonical_truth_write_allowed_sum": int(sub["canonical_truth_write_allowed"].sum()),
                    "truth_intake_allowed_sum": int(sub["truth_intake_allowed"].sum()),
                    "threshold_patch_allowed_sum": int(sub["threshold_patch_allowed"].sum()),
                    "engine_patch_allowed_sum": int(sub["engine_patch_allowed"].sum()),
                }
            )
    if len(blocked):
        for reason, sub in blocked.groupby("blocker_reason", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "blocker_reason",
                    "summary_key": reason,
                    "source_decision_rows": int(len(validation)),
                    "source_valid_decision_rows": source_valid,
                    "source_validation_failed_rows": source_failed,
                    "source_future_truth_intake_candidate_rows": source_future,
                    "candidate_package_rows": 0,
                    "blocked_before_candidate_package_rows": int(len(sub)),
                    "source_issue_rows": int(len(issues)),
                    "source_write_flag_violation_rows": source_write_violations,
                    "canonical_truth_write_allowed_sum": 0,
                    "truth_intake_allowed_sum": 0,
                    "threshold_patch_allowed_sum": 0,
                    "engine_patch_allowed_sum": 0,
                }
            )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, summary: pd.DataFrame) -> Path:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-123 MLPE Field-Trial Future Truth-Intake Candidate Package",
        "",
        "## Purpose",
        "- Package only BR-122 validated future truth-intake candidates.",
        "- Keep rejected, deferred, incomplete, failed, and write-flag-violating decisions out of the candidate package.",
        "- Preserve the sidecar-only boundary before any explicit truth-intake branch.",
        "",
        "## Result",
        f"- source decision rows: `{overall['source_decision_rows']}`",
        f"- source valid decision rows: `{overall['source_valid_decision_rows']}`",
        f"- source validation-failed rows: `{overall['source_validation_failed_rows']}`",
        f"- source future truth-intake candidate rows: `{overall['source_future_truth_intake_candidate_rows']}`",
        f"- candidate package rows: `{overall['candidate_package_rows']}`",
        f"- blocked before candidate package rows: `{overall['blocked_before_candidate_package_rows']}`",
        f"- source issue rows: `{overall['source_issue_rows']}`",
        f"- source write-flag violation rows: `{overall['source_write_flag_violation_rows']}`",
        f"- canonical truth write allowed sum: `{overall['canonical_truth_write_allowed_sum']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Candidate package rows are not canonical truth rows.",
        "- Candidate package rows do not authorize threshold or engine patches.",
        "- Approval/write fields remain locked to `0`.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--validation", default=DEFAULT_VALIDATION)
    parser.add_argument("--issues", default=DEFAULT_ISSUES)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    validation_path = resolve_path(repo_root, args.validation)
    issues_path = resolve_path(repo_root, args.issues)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    validation = read_csv(validation_path, VALIDATION_COLUMNS)
    issues = read_csv(issues_path, ISSUE_COLUMNS)
    candidates, blocked = build_package(validation, issues, validation_path, issues_path)
    summary = build_summary(validation, issues, candidates, blocked)

    candidate_path = output_dir / CANDIDATE_OUTPUT_NAME
    blocked_path = output_dir / BLOCKED_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    candidates.to_csv(candidate_path, index=False, encoding="utf-8-sig")
    blocked.to_csv(blocked_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "source_decision_rows": int(overall["source_decision_rows"]),
        "source_valid_decision_rows": int(overall["source_valid_decision_rows"]),
        "source_validation_failed_rows": int(overall["source_validation_failed_rows"]),
        "source_future_truth_intake_candidate_rows": int(overall["source_future_truth_intake_candidate_rows"]),
        "candidate_package_rows": int(overall["candidate_package_rows"]),
        "blocked_before_candidate_package_rows": int(overall["blocked_before_candidate_package_rows"]),
        "source_issue_rows": int(overall["source_issue_rows"]),
        "source_write_flag_violation_rows": int(overall["source_write_flag_violation_rows"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "candidate_package": str(candidate_path),
            "blocked": str(blocked_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
