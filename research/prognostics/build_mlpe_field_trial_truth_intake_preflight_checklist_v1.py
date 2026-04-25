#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-124"
DEFAULT_CANDIDATE_PACKAGE = "/private/tmp/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_br123_check/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.csv"
DEFAULT_BLOCKED = "/private/tmp/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_br123_check/mlpe_field_trial_truth_seed_future_truth_intake_blocked_rows_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_truth_intake_preflight_checklist_br124_check"

PREFLIGHT_OUTPUT_NAME = "mlpe_field_trial_truth_intake_preflight_v1.csv"
CHECKLIST_OUTPUT_NAME = "mlpe_field_trial_truth_intake_preflight_checklist_v1.csv"
BLOCKED_OUTPUT_NAME = "mlpe_field_trial_truth_intake_preflight_blocked_carryover_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_truth_intake_preflight_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_truth_intake_preflight_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_truth_intake_preflight_v1.json"

APPROVAL_FIELDS = ["canonical_truth_write_allowed", "truth_intake_allowed", "threshold_patch_allowed", "engine_patch_allowed"]

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

SOURCE_BLOCKED_COLUMNS = [
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

BLOCKED_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "truth_intake_preflight_status",
    "source_row_kind",
    "truth_candidate_role",
    "truth_seed_reviewer_decision",
    "source_candidate_status",
    "blocker_reason",
    "source_issue_count",
    "source_candidate_package_path",
    "source_blocked_path",
    "blocked_next_action",
]

CHECKLIST_ITEMS = [
    (
        "BR124-CHECK-001",
        "exact_source_trace_confirmed",
        "source_trace",
        "Exact candidate source rows and reviewer decision trace are resolved.",
    ),
    (
        "BR124-CHECK-002",
        "independent_evidence_attached",
        "evidence_attachment",
        "Independent physical, inspection, maintenance, or field-trial evidence is attached.",
    ),
    (
        "BR124-CHECK-003",
        "common_cause_final_clearance_confirmed",
        "clearance",
        "Common-cause or site-level event risk is explicitly cleared for panel-local truth use.",
    ),
    (
        "BR124-CHECK-004",
        "measurement_artifact_final_clearance_confirmed",
        "clearance",
        "Measurement, communication, sensor, and data-artifact risk is explicitly cleared.",
    ),
    (
        "BR124-CHECK-005",
        "counterexample_final_clearance_confirmed",
        "counterexample",
        "Known counterexample and regression-pressure rows were checked with no blocker.",
    ),
    (
        "BR124-CHECK-006",
        "truth_write_boundary_reviewed",
        "approval_boundary",
        "Reviewer confirms this preflight is still sidecar-only and not a canonical write.",
    ),
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


def source_write_violation(row: pd.Series) -> bool:
    return any(int_value(row.get(field, "0")) != 0 for field in APPROVAL_FIELDS)


def candidate_source_blocker(row: pd.Series) -> str:
    event_id = normalize_text(row.get("trial_event_id", ""))
    status = normalize_text(row.get("truth_seed_future_truth_intake_candidate_status", ""))
    if not event_id:
        return "missing_trial_event_id"
    if source_write_violation(row):
        return "source_candidate_write_flag_violation"
    if status != "sidecar_future_truth_intake_candidate":
        return "source_candidate_status_not_sidecar_candidate"
    return ""


def build_preflight(candidate_package: pd.DataFrame, blocked_source: pd.DataFrame, candidate_path: Path, blocked_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    preflight_rows = []
    checklist_rows = []
    blocked_rows = []

    for _, row in candidate_package.iterrows():
        event_id = normalize_text(row.get("trial_event_id", ""))
        blocker = candidate_source_blocker(row)
        if blocker:
            blocked_rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "truth_intake_preflight_status": "blocked_before_truth_intake_preflight",
                    "source_row_kind": "candidate_package",
                    "truth_candidate_role": normalize_text(row.get("truth_candidate_role", "")),
                    "truth_seed_reviewer_decision": normalize_text(row.get("truth_seed_reviewer_decision", "")),
                    "source_candidate_status": normalize_text(row.get("truth_seed_future_truth_intake_candidate_status", "")),
                    "blocker_reason": blocker,
                    "source_issue_count": int_value(row.get("source_issue_count", "0")),
                    "source_candidate_package_path": str(candidate_path),
                    "source_blocked_path": str(blocked_path),
                    "blocked_next_action": "Fix the BR-123 candidate package source row before creating truth-intake preflight checks.",
                }
            )
            continue

        preflight_rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": event_id,
                "truth_intake_preflight_status": "pending_checklist_completion",
                "truth_candidate_role": normalize_text(row.get("truth_candidate_role", "")),
                "truth_seed_reviewer_decision": normalize_text(row.get("truth_seed_reviewer_decision", "")),
                "source_candidate_status": normalize_text(row.get("truth_seed_future_truth_intake_candidate_status", "")),
                "source_issue_count": int_value(row.get("source_issue_count", "0")),
                "required_checklist_item_count": len(CHECKLIST_ITEMS),
                "passed_checklist_item_count": 0,
                "truth_intake_preflight_ready_flag": 0,
                "canonical_truth_write_allowed": 0,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "source_candidate_package_path": str(candidate_path),
                "source_blocked_path": str(blocked_path),
                "preflight_next_action": "Fill every required checklist item in a later reviewed preflight input before any truth-intake branch.",
            }
        )

        for check_id, check_name, check_group, expected in CHECKLIST_ITEMS:
            checklist_rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "check_id": check_id,
                    "check_name": check_name,
                    "check_group": check_group,
                    "required_for_truth_intake": 1,
                    "check_status": "unchecked",
                    "check_passed_flag": 0,
                    "expected_evidence_or_clearance": expected,
                    "preflight_operator_note": "unchecked means blocked; fill in a later reviewed input, not in this generator.",
                }
            )

    for _, row in blocked_source.iterrows():
        blocked_rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": normalize_text(row.get("trial_event_id", "")),
                "truth_intake_preflight_status": "source_blocked_before_truth_intake_preflight",
                "source_row_kind": "br123_blocked_carryover",
                "truth_candidate_role": normalize_text(row.get("truth_candidate_role", "")),
                "truth_seed_reviewer_decision": normalize_text(row.get("truth_seed_reviewer_decision", "")),
                "source_candidate_status": normalize_text(row.get("truth_seed_future_truth_intake_candidate_status", "")),
                "blocker_reason": normalize_text(row.get("blocker_reason", "")) or "source_blocked_before_candidate_package",
                "source_issue_count": int_value(row.get("source_issue_count", "0")),
                "source_candidate_package_path": str(candidate_path),
                "source_blocked_path": str(blocked_path),
                "blocked_next_action": "Resolve BR-123 blocker before this row can receive a truth-intake preflight checklist.",
            }
        )

    return (
        pd.DataFrame(preflight_rows).reindex(columns=PREFLIGHT_COLUMNS),
        pd.DataFrame(checklist_rows).reindex(columns=CHECKLIST_COLUMNS),
        pd.DataFrame(blocked_rows).reindex(columns=BLOCKED_COLUMNS),
    )


def build_summary(candidate_package: pd.DataFrame, blocked_source: pd.DataFrame, preflight: pd.DataFrame, checklist: pd.DataFrame, blocked: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "source_candidate_package_rows": int(len(candidate_package)),
            "source_blocked_rows": int(len(blocked_source)),
            "truth_intake_preflight_rows": int(len(preflight)),
            "preflight_checklist_rows": int(len(checklist)),
            "preflight_unchecked_rows": int(checklist["check_status"].eq("unchecked").sum()) if len(checklist) else 0,
            "truth_intake_preflight_ready_rows": int(preflight["truth_intake_preflight_ready_flag"].map(int_value).sum()) if len(preflight) else 0,
            "blocked_before_preflight_rows": int(len(blocked)),
            "canonical_truth_write_allowed_sum": int(preflight["canonical_truth_write_allowed"].sum()) if len(preflight) else 0,
            "truth_intake_allowed_sum": int(preflight["truth_intake_allowed"].sum()) if len(preflight) else 0,
            "threshold_patch_allowed_sum": int(preflight["threshold_patch_allowed"].sum()) if len(preflight) else 0,
            "engine_patch_allowed_sum": int(preflight["engine_patch_allowed"].sum()) if len(preflight) else 0,
        }
    ]
    if len(blocked):
        for reason, sub in blocked.groupby("blocker_reason", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "blocker_reason",
                    "summary_key": reason,
                    "source_candidate_package_rows": int(len(candidate_package)),
                    "source_blocked_rows": int(len(blocked_source)),
                    "truth_intake_preflight_rows": 0,
                    "preflight_checklist_rows": 0,
                    "preflight_unchecked_rows": 0,
                    "truth_intake_preflight_ready_rows": 0,
                    "blocked_before_preflight_rows": int(len(sub)),
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
        "# BR-124 MLPE Field-Trial Truth-Intake Preflight Checklist",
        "",
        "## Purpose",
        "- Create unchecked preflight checklist rows for BR-123 sidecar future truth-intake candidates.",
        "- Keep source-blocked rows and malformed candidate package rows out of preflight.",
        "- Keep truth materialization blocked until the checklist is explicitly reviewed in a later branch.",
        "",
        "## Result",
        f"- source candidate package rows: `{overall['source_candidate_package_rows']}`",
        f"- source blocked rows: `{overall['source_blocked_rows']}`",
        f"- truth-intake preflight rows: `{overall['truth_intake_preflight_rows']}`",
        f"- preflight checklist rows: `{overall['preflight_checklist_rows']}`",
        f"- preflight unchecked rows: `{overall['preflight_unchecked_rows']}`",
        f"- truth-intake preflight ready rows: `{overall['truth_intake_preflight_ready_rows']}`",
        f"- blocked before preflight rows: `{overall['blocked_before_preflight_rows']}`",
        f"- canonical truth write allowed sum: `{overall['canonical_truth_write_allowed_sum']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Unchecked checklist rows are blockers, not approvals.",
        "- Preflight rows are not canonical truth rows.",
        "- Approval/write fields remain locked to `0`.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--candidate-package", default=DEFAULT_CANDIDATE_PACKAGE)
    parser.add_argument("--blocked", default=DEFAULT_BLOCKED)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    candidate_path = resolve_path(repo_root, args.candidate_package)
    blocked_path = resolve_path(repo_root, args.blocked)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    candidate_package = read_csv(candidate_path, CANDIDATE_COLUMNS)
    blocked_source = read_csv(blocked_path, SOURCE_BLOCKED_COLUMNS)
    preflight, checklist, blocked = build_preflight(candidate_package, blocked_source, candidate_path, blocked_path)
    summary = build_summary(candidate_package, blocked_source, preflight, checklist, blocked)

    preflight_path = output_dir / PREFLIGHT_OUTPUT_NAME
    checklist_path = output_dir / CHECKLIST_OUTPUT_NAME
    blocked_out_path = output_dir / BLOCKED_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    preflight.to_csv(preflight_path, index=False, encoding="utf-8-sig")
    checklist.to_csv(checklist_path, index=False, encoding="utf-8-sig")
    blocked.to_csv(blocked_out_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "source_candidate_package_rows": int(overall["source_candidate_package_rows"]),
        "source_blocked_rows": int(overall["source_blocked_rows"]),
        "truth_intake_preflight_rows": int(overall["truth_intake_preflight_rows"]),
        "preflight_checklist_rows": int(overall["preflight_checklist_rows"]),
        "preflight_unchecked_rows": int(overall["preflight_unchecked_rows"]),
        "truth_intake_preflight_ready_rows": int(overall["truth_intake_preflight_ready_rows"]),
        "blocked_before_preflight_rows": int(overall["blocked_before_preflight_rows"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "preflight": str(preflight_path),
            "checklist": str(checklist_path),
            "blocked": str(blocked_out_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
