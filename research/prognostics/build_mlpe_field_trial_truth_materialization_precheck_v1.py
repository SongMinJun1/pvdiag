#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-127"
DEFAULT_REVIEW_VALIDATION = "/private/tmp/mlpe_field_trial_truth_intake_preflight_review_validator_br125_check/mlpe_field_trial_truth_intake_preflight_review_validation_v1.csv"
DEFAULT_REVIEW_ISSUES = "/private/tmp/mlpe_field_trial_truth_intake_preflight_review_validator_br125_check/mlpe_field_trial_truth_intake_preflight_review_issues_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_truth_materialization_precheck_br127_check"

PRECHECK_OUTPUT_NAME = "mlpe_field_trial_truth_materialization_precheck_v1.csv"
ISSUES_OUTPUT_NAME = "mlpe_field_trial_truth_materialization_precheck_issues_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_truth_materialization_precheck_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_truth_materialization_precheck_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_truth_materialization_precheck_v1.json"

APPROVAL_FIELDS = ["canonical_truth_write_allowed", "truth_intake_allowed", "threshold_patch_allowed", "engine_patch_allowed"]
REQUIRED_EVIDENCE_GROUPS = [
    "source_trace",
    "independent_evidence",
    "common_cause_clearance",
    "measurement_artifact_clearance",
    "counterexample_clearance",
    "write_boundary_review",
]

REVIEW_VALIDATION_COLUMNS = [
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

REVIEW_ISSUE_COLUMNS = ["owner_branch", "trial_event_id", "issue_type", "field", "observed_value", "expected_policy"]

EVIDENCE_MANIFEST_COLUMNS = [
    "trial_event_id",
    "evidence_group",
    "evidence_path",
    "materialization_required_flag",
    "evidence_exists_flag",
    "reviewer_signed_flag",
    "evidence_note",
]

PRECHECK_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "source_review_validation_bucket",
    "truth_candidate_role",
    "truth_seed_reviewer_decision",
    "source_reviewed_preflight_all_checks_passed_flag",
    "source_reviewed_preflight_validation_failed_flag",
    "source_future_materialization_candidate_flag",
    "source_review_issue_count",
    "source_write_flag_violation_flag",
    "materialization_precheck_status",
    "source_trace_materialized_flag",
    "independent_evidence_materialized_flag",
    "common_cause_clearance_materialized_flag",
    "measurement_artifact_clearance_materialized_flag",
    "counterexample_clearance_materialized_flag",
    "write_boundary_materialized_flag",
    "missing_evidence_groups_csv",
    "failed_evidence_groups_csv",
    "materialization_precheck_passed_flag",
    "future_sidecar_truth_package_candidate_flag",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "review_validation_path",
    "review_issues_path",
    "materialization_evidence_manifest_path",
    "precheck_next_action",
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
    return any(int_value(row.get(field, "0")) != 0 for field in APPROVAL_FIELDS) or int_value(row.get("source_write_flag_violation_flag", "0")) != 0


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


def evidence_group_status(evidence: pd.DataFrame | None, event_id: str, group: str) -> str:
    if evidence is None:
        return "missing_manifest"
    sub = evidence[
        evidence["trial_event_id"].map(normalize_text).eq(event_id)
        & evidence["evidence_group"].map(normalize_text).eq(group)
        & evidence["materialization_required_flag"].map(int_value).eq(1)
    ]
    if sub.empty:
        return "missing_required_group"
    passed = (
        sub["evidence_path"].map(normalize_text).ne("")
        & sub["evidence_exists_flag"].map(int_value).eq(1)
        & sub["reviewer_signed_flag"].map(int_value).eq(1)
    )
    return "passed" if bool(passed.any()) else "required_group_not_materialized"


def add_issue(issue_rows: list[dict[str, object]], event_id: str, issue_type: str, field: str, observed: str, expected: str) -> None:
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


def build_precheck(
    validation: pd.DataFrame,
    review_issues: pd.DataFrame,
    evidence: pd.DataFrame | None,
    validation_path: Path,
    review_issues_path: Path,
    evidence_path: Path | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    precheck_rows: list[dict[str, object]] = []
    issue_rows: list[dict[str, object]] = []
    review_issue_counts = review_issues.groupby("trial_event_id").size().to_dict() if len(review_issues) else {}
    duplicate_event_ids = set(duplicate_values([normalize_text(value) for value in validation["trial_event_id"].tolist()]))

    for _, row in validation.iterrows():
        event_id = normalize_text(row.get("trial_event_id", ""))
        missing_groups: list[str] = []
        failed_groups: list[str] = []
        group_flags = {group: 0 for group in REQUIRED_EVIDENCE_GROUPS}

        if not event_id:
            status = "blocked_missing_trial_event_id"
            add_issue(issue_rows, event_id, "missing_trial_event_id", "trial_event_id", "", "non-empty trial_event_id")
        elif event_id in duplicate_event_ids:
            status = "blocked_duplicate_review_validation_row"
            add_issue(issue_rows, event_id, "duplicate_review_validation_row", "trial_event_id", event_id, "unique BR-125 validation row per event")
        elif source_write_violation(row):
            status = "blocked_source_write_flag_violation"
            add_issue(issue_rows, event_id, "source_write_flag_violation", "approval_fields", "nonzero", "all source approval/write fields remain 0")
        elif int_value(row.get("reviewed_preflight_validation_failed_flag", "0")) != 0:
            status = "blocked_reviewed_preflight_failed"
            add_issue(issue_rows, event_id, "reviewed_preflight_validation_failed", "reviewed_preflight_validation_failed_flag", "1", "0")
        elif int_value(row.get("reviewed_preflight_all_checks_passed_flag", "0")) != 1 or int_value(row.get("future_truth_materialization_precheck_candidate_flag", "0")) != 1:
            status = "blocked_reviewed_preflight_not_candidate"
            add_issue(issue_rows, event_id, "reviewed_preflight_not_candidate", "future_truth_materialization_precheck_candidate_flag", normalize_text(row.get("future_truth_materialization_precheck_candidate_flag", "")), "1")
        elif int(review_issue_counts.get(event_id, 0)) > 0:
            status = "blocked_source_review_issues_present"
            add_issue(issue_rows, event_id, "source_review_issues_present", "review_issue_count", str(review_issue_counts.get(event_id, 0)), "0")
        else:
            for group in REQUIRED_EVIDENCE_GROUPS:
                group_status = evidence_group_status(evidence, event_id, group)
                if group_status == "passed":
                    group_flags[group] = 1
                elif group_status == "missing_required_group":
                    missing_groups.append(group)
                    add_issue(issue_rows, event_id, "missing_required_evidence_group", "evidence_group", group, "one required, existing, signed evidence row")
                elif group_status == "required_group_not_materialized":
                    failed_groups.append(group)
                    add_issue(issue_rows, event_id, "required_evidence_group_not_materialized", "evidence_group", group, "evidence_path non-empty, evidence_exists_flag=1, reviewer_signed_flag=1")
                elif group_status == "missing_manifest":
                    failed_groups.append(group)
            if evidence is None:
                status = "blocked_missing_materialization_evidence_manifest"
                add_issue(
                    issue_rows,
                    event_id,
                    "missing_materialization_evidence_manifest",
                    "materialization_evidence_manifest",
                    "",
                    "required when BR-125 materialization candidates exist",
                )
            elif missing_groups or failed_groups:
                status = "blocked_missing_or_failed_materialization_evidence"
            else:
                status = "materialization_precheck_passed_sidecar_candidate"

        passed = int(status == "materialization_precheck_passed_sidecar_candidate")
        precheck_rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": event_id,
                "source_review_validation_bucket": normalize_text(row.get("review_validation_bucket", "")),
                "truth_candidate_role": normalize_text(row.get("truth_candidate_role", "")),
                "truth_seed_reviewer_decision": normalize_text(row.get("truth_seed_reviewer_decision", "")),
                "source_reviewed_preflight_all_checks_passed_flag": int_value(row.get("reviewed_preflight_all_checks_passed_flag", "0")),
                "source_reviewed_preflight_validation_failed_flag": int_value(row.get("reviewed_preflight_validation_failed_flag", "0")),
                "source_future_materialization_candidate_flag": int_value(row.get("future_truth_materialization_precheck_candidate_flag", "0")),
                "source_review_issue_count": int(review_issue_counts.get(event_id, 0)),
                "source_write_flag_violation_flag": int(source_write_violation(row)),
                "materialization_precheck_status": status,
                "source_trace_materialized_flag": group_flags["source_trace"],
                "independent_evidence_materialized_flag": group_flags["independent_evidence"],
                "common_cause_clearance_materialized_flag": group_flags["common_cause_clearance"],
                "measurement_artifact_clearance_materialized_flag": group_flags["measurement_artifact_clearance"],
                "counterexample_clearance_materialized_flag": group_flags["counterexample_clearance"],
                "write_boundary_materialized_flag": group_flags["write_boundary_review"],
                "missing_evidence_groups_csv": ",".join(missing_groups),
                "failed_evidence_groups_csv": ",".join(failed_groups),
                "materialization_precheck_passed_flag": passed,
                "future_sidecar_truth_package_candidate_flag": passed,
                "canonical_truth_write_allowed": 0,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "review_validation_path": str(validation_path),
                "review_issues_path": str(review_issues_path),
                "materialization_evidence_manifest_path": str(evidence_path) if evidence_path else "",
                "precheck_next_action": "May enter a later sidecar truth package; still no canonical truth write." if passed else "Resolve blockers before sidecar truth package discussion.",
            }
        )

    return (
        pd.DataFrame(precheck_rows).reindex(columns=PRECHECK_COLUMNS),
        pd.DataFrame(issue_rows).reindex(columns=ISSUE_COLUMNS),
    )


def build_summary(precheck: pd.DataFrame, issues: pd.DataFrame, evidence: pd.DataFrame | None) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "source_review_validation_rows": int(len(precheck)),
            "materialization_precheck_passed_rows": int(precheck["materialization_precheck_passed_flag"].sum()) if len(precheck) else 0,
            "future_sidecar_truth_package_candidate_rows": int(precheck["future_sidecar_truth_package_candidate_flag"].sum()) if len(precheck) else 0,
            "materialization_precheck_blocked_rows": int((precheck["materialization_precheck_passed_flag"].map(int_value) == 0).sum()) if len(precheck) else 0,
            "materialization_issue_rows": int(len(issues)),
            "materialization_evidence_manifest_rows": int(len(evidence)) if evidence is not None else 0,
            "canonical_truth_write_allowed_sum": int(precheck["canonical_truth_write_allowed"].sum()) if len(precheck) else 0,
            "truth_intake_allowed_sum": int(precheck["truth_intake_allowed"].sum()) if len(precheck) else 0,
            "threshold_patch_allowed_sum": int(precheck["threshold_patch_allowed"].sum()) if len(precheck) else 0,
            "engine_patch_allowed_sum": int(precheck["engine_patch_allowed"].sum()) if len(precheck) else 0,
        }
    ]
    if len(precheck):
        for status, sub in precheck.groupby("materialization_precheck_status", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "materialization_precheck_status",
                    "summary_key": status,
                    "source_review_validation_rows": int(len(sub)),
                    "materialization_precheck_passed_rows": int(sub["materialization_precheck_passed_flag"].sum()),
                    "future_sidecar_truth_package_candidate_rows": int(sub["future_sidecar_truth_package_candidate_flag"].sum()),
                    "materialization_precheck_blocked_rows": int((sub["materialization_precheck_passed_flag"].map(int_value) == 0).sum()),
                    "materialization_issue_rows": int(len(issues[issues["trial_event_id"].isin(sub["trial_event_id"])])) if len(issues) else 0,
                    "materialization_evidence_manifest_rows": int(len(evidence)) if evidence is not None else 0,
                    "canonical_truth_write_allowed_sum": int(sub["canonical_truth_write_allowed"].sum()),
                    "truth_intake_allowed_sum": int(sub["truth_intake_allowed"].sum()),
                    "threshold_patch_allowed_sum": int(sub["threshold_patch_allowed"].sum()),
                    "engine_patch_allowed_sum": int(sub["engine_patch_allowed"].sum()),
                }
            )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, summary: pd.DataFrame, evidence_path: Path | None) -> Path:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-127 MLPE Field-Trial Truth Materialization Precheck",
        "",
        "## Purpose",
        "- Build the source/evidence materialization precheck after BR-125 reviewed-preflight validation.",
        "- Require a candidate to have passed reviewed preflight and to have required source/evidence/clearance/write-boundary manifest rows.",
        "- Keep the output sidecar-only; do not authorize canonical truth, threshold, or engine writes.",
        "",
        "## Result",
        f"- source review validation rows: `{overall['source_review_validation_rows']}`",
        f"- materialization precheck passed rows: `{overall['materialization_precheck_passed_rows']}`",
        f"- future sidecar truth package candidate rows: `{overall['future_sidecar_truth_package_candidate_rows']}`",
        f"- blocked rows: `{overall['materialization_precheck_blocked_rows']}`",
        f"- issue rows: `{overall['materialization_issue_rows']}`",
        f"- evidence manifest rows: `{overall['materialization_evidence_manifest_rows']}`",
        f"- evidence manifest path: `{str(evidence_path) if evidence_path else ''}`",
        f"- canonical truth write allowed sum: `{overall['canonical_truth_write_allowed_sum']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Passing this precheck means only future sidecar truth package eligibility.",
        "- It is not canonical truth materialization.",
        "- Approval/write fields remain locked to `0`.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--review-validation", default=DEFAULT_REVIEW_VALIDATION)
    parser.add_argument("--review-issues", default=DEFAULT_REVIEW_ISSUES)
    parser.add_argument("--materialization-evidence-manifest", default="")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    validation_path = resolve_path(repo_root, args.review_validation)
    review_issues_path = resolve_path(repo_root, args.review_issues)
    evidence_path = resolve_path(repo_root, args.materialization_evidence_manifest) if normalize_text(args.materialization_evidence_manifest) else None
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    validation = read_csv(validation_path, REVIEW_VALIDATION_COLUMNS)
    review_issues = read_csv(review_issues_path, REVIEW_ISSUE_COLUMNS)
    evidence = read_csv(evidence_path, EVIDENCE_MANIFEST_COLUMNS) if evidence_path else None

    precheck, issues = build_precheck(validation, review_issues, evidence, validation_path, review_issues_path, evidence_path)
    summary = build_summary(precheck, issues, evidence)

    precheck_path = output_dir / PRECHECK_OUTPUT_NAME
    issues_path = output_dir / ISSUES_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    precheck.to_csv(precheck_path, index=False, encoding="utf-8-sig")
    issues.to_csv(issues_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary, evidence_path)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "source_review_validation_rows": int(overall["source_review_validation_rows"]),
        "materialization_precheck_passed_rows": int(overall["materialization_precheck_passed_rows"]),
        "future_sidecar_truth_package_candidate_rows": int(overall["future_sidecar_truth_package_candidate_rows"]),
        "materialization_precheck_blocked_rows": int(overall["materialization_precheck_blocked_rows"]),
        "materialization_issue_rows": int(overall["materialization_issue_rows"]),
        "materialization_evidence_manifest_rows": int(overall["materialization_evidence_manifest_rows"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "precheck": str(precheck_path),
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
