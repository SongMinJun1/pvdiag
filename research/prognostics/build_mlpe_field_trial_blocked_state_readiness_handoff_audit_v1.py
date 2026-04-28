#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-149-precheck"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_blocked_state_readiness_handoff_br149_check"
DEFAULT_QUEUE = "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_128_TO_150_EXECUTION_QUEUE_V1.csv"

AUDIT_OUTPUT_NAME = "mlpe_field_trial_blocked_state_readiness_handoff_audit_v1.csv"
ISSUES_OUTPUT_NAME = "mlpe_field_trial_blocked_state_readiness_handoff_issues_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_blocked_state_readiness_handoff_summary_v1.csv"
NEXT_OUTPUT_NAME = "mlpe_field_trial_blocked_state_readiness_handoff_next_actions_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_blocked_state_readiness_handoff_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_blocked_state_readiness_handoff_v1.json"

EXPECTED_COMPLETE = {
    "BR-20260425-128",
    "BR-20260425-129",
    "BR-20260425-131",
    "BR-20260425-133",
    "BR-20260425-135",
    "BR-20260425-137",
    "BR-20260425-139",
    "BR-20260425-143",
}

EXPECTED_BLOCKED = {
    "BR-20260425-130",
    "BR-20260425-132",
    "BR-20260425-134",
    "BR-20260425-136",
    "BR-20260425-138",
    "BR-20260425-140",
    "BR-20260425-141",
    "BR-20260425-142",
    "BR-20260425-144",
    "BR-20260425-145",
    "BR-20260425-146",
    "BR-20260425-147",
    "BR-20260425-148",
    "BR-20260425-149",
    "BR-20260425-150",
}

REQUIRED_DOCS = {
    "BR-20260425-129": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_129_REAL_CAPTURE_INTAKE_CONTRACT_V1.md",
    "BR-20260425-131": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_131_SOURCE_EVIDENCE_RESOLVER_CONTRACT_V1.md",
    "BR-20260425-133": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_133_COMMON_CAUSE_CLEARANCE_CONTRACT_V1.md",
    "BR-20260425-135": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_135_ARTIFACT_MLPE_CONTROL_CLEARANCE_CONTRACT_V1.md",
    "BR-20260425-137": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_137_SIDECAR_TRUTH_PACKAGE_CONTRACT_V1.md",
    "BR-20260425-139": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_139_TRUTH_REPLAY_SCORECARD_CONTRACT_V1.md",
    "BR-20260425-143": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_143_PANEL_ENGINE_PREPATCH_GATE_REFRESH_V1.md",
}

REQUIRED_BUILDERS = {
    "BR-20260425-129": "research/prognostics/build_mlpe_field_trial_real_capture_intake_contract_v1.py",
    "BR-20260425-131": "research/prognostics/build_mlpe_field_trial_source_evidence_resolver_contract_v1.py",
    "BR-20260425-133": "research/prognostics/build_mlpe_field_trial_common_cause_clearance_contract_v1.py",
    "BR-20260425-135": "research/prognostics/build_mlpe_field_trial_artifact_mlpe_control_clearance_contract_v1.py",
    "BR-20260425-137": "research/prognostics/build_mlpe_field_trial_sidecar_truth_package_contract_v1.py",
    "BR-20260425-139": "research/prognostics/build_mlpe_field_trial_truth_replay_scorecard_contract_v1.py",
    "BR-20260425-143": "research/prognostics/build_mlpe_field_trial_panel_engine_prepatch_gate_refresh_v1.py",
}

REQUIRED_SMOKES = {
    "BR-20260425-129": "research/prognostics/smoke_test_mlpe_field_trial_real_capture_intake_contract_v1.py",
    "BR-20260425-131": "research/prognostics/smoke_test_mlpe_field_trial_source_evidence_resolver_contract_v1.py",
    "BR-20260425-133": "research/prognostics/smoke_test_mlpe_field_trial_common_cause_clearance_contract_v1.py",
    "BR-20260425-135": "research/prognostics/smoke_test_mlpe_field_trial_artifact_mlpe_control_clearance_contract_v1.py",
    "BR-20260425-137": "research/prognostics/smoke_test_mlpe_field_trial_sidecar_truth_package_contract_v1.py",
    "BR-20260425-139": "research/prognostics/smoke_test_mlpe_field_trial_truth_replay_scorecard_contract_v1.py",
    "BR-20260425-143": "research/prognostics/smoke_test_mlpe_field_trial_panel_engine_prepatch_gate_refresh_v1.py",
}

AUDIT_COLUMNS = [
    "owner_branch",
    "branch",
    "sequence_no",
    "runway_stage",
    "status",
    "status_family",
    "expected_state",
    "state_ok_flag",
    "operator_facing_change",
    "operator_change_safe_flag",
    "required_doc_path",
    "required_doc_present_flag",
    "required_builder_path",
    "required_builder_present_flag",
    "required_smoke_path",
    "required_smoke_present_flag",
    "blocked_by",
    "next_action",
]

ISSUE_COLUMNS = [
    "owner_branch",
    "issue_type",
    "branch",
    "field",
    "observed_value",
    "expected_policy",
]

NEXT_COLUMNS = [
    "owner_branch",
    "next_action_order",
    "action_id",
    "action_type",
    "blocked_by",
    "action_detail",
    "safe_to_do_without_real_data_flag",
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


def resolve(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_queue(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    for col in [
        "branch",
        "sequence_no",
        "runway_stage",
        "status",
        "blocked_by",
        "next_action",
        "operator_facing_change",
    ]:
        if col not in df.columns:
            df[col] = ""
    out = df.copy()
    for col in out.columns:
        out[col] = out[col].map(normalize_text)
    return out


def status_family(status: str) -> str:
    if status == "complete_this_branch":
        return "complete"
    if status == "open_now":
        return "open"
    if status.startswith("blocked_"):
        return "blocked"
    return "unknown"


def expected_state(branch: str) -> str:
    if branch in EXPECTED_COMPLETE:
        return "complete"
    if branch in EXPECTED_BLOCKED:
        return "blocked"
    return "unknown"


def add_issue(
    issues: list[dict[str, object]],
    issue_type: str,
    branch: str,
    field: str,
    observed: str,
    expected: str,
) -> None:
    issues.append(
        {
            "owner_branch": OWNER_BRANCH,
            "issue_type": issue_type,
            "branch": branch,
            "field": field,
            "observed_value": observed,
            "expected_policy": expected,
        }
    )


def read_commit_scope_payload(path: Path | None) -> dict[str, object]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_audit(repo_root: Path, queue: pd.DataFrame, commit_payload: dict[str, object]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []

    if len(queue) != 23:
        add_issue(issues, "queue_row_count_mismatch", "", "queue_rows", str(len(queue)), "23 rows")
    try:
        seq = [int_value(x) for x in queue["sequence_no"].tolist()]
    except Exception:
        seq = []
    if seq != list(range(1, 24)):
        add_issue(issues, "queue_sequence_not_contiguous", "", "sequence_no", ",".join(map(str, seq)), "1..23")

    branches = set(queue["branch"].tolist())
    for branch in sorted(EXPECTED_COMPLETE | EXPECTED_BLOCKED):
        if branch not in branches:
            add_issue(issues, "expected_branch_missing", branch, "branch", "", "present in queue")

    for _, item in queue.iterrows():
        branch = normalize_text(item.get("branch", ""))
        status = normalize_text(item.get("status", ""))
        family = status_family(status)
        expected = expected_state(branch)
        state_ok = int(expected != "unknown" and family == expected)
        op_change = normalize_text(item.get("operator_facing_change", ""))
        op_safe = int(not (family == "complete" and op_change != "no"))

        doc_path = REQUIRED_DOCS.get(branch, "")
        builder_path = REQUIRED_BUILDERS.get(branch, "")
        smoke_path = REQUIRED_SMOKES.get(branch, "")
        doc_present = int(not doc_path or resolve(repo_root, doc_path).exists())
        builder_present = int(not builder_path or resolve(repo_root, builder_path).exists())
        smoke_present = int(not smoke_path or resolve(repo_root, smoke_path).exists())

        if expected != "unknown" and not state_ok:
            add_issue(issues, "branch_state_mismatch", branch, "status", status, expected)
        if family == "open":
            add_issue(issues, "open_branch_remaining", branch, "status", status, "no open branch in current blocked-state handoff")
        if not op_safe:
            add_issue(issues, "completed_operator_change_not_safe", branch, "operator_facing_change", op_change, "completed rows must be no")
        if not doc_present:
            add_issue(issues, "required_doc_missing", branch, "required_doc_path", doc_path, "present")
        if not builder_present:
            add_issue(issues, "required_builder_missing", branch, "required_builder_path", builder_path, "present")
        if not smoke_present:
            add_issue(issues, "required_smoke_missing", branch, "required_smoke_path", smoke_path, "present")

        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "branch": branch,
                "sequence_no": int_value(item.get("sequence_no", "0")),
                "runway_stage": normalize_text(item.get("runway_stage", "")),
                "status": status,
                "status_family": family,
                "expected_state": expected,
                "state_ok_flag": state_ok,
                "operator_facing_change": op_change,
                "operator_change_safe_flag": op_safe,
                "required_doc_path": doc_path,
                "required_doc_present_flag": doc_present,
                "required_builder_path": builder_path,
                "required_builder_present_flag": builder_present,
                "required_smoke_path": smoke_path,
                "required_smoke_present_flag": smoke_present,
                "blocked_by": normalize_text(item.get("blocked_by", "")),
                "next_action": normalize_text(item.get("next_action", "")),
            }
        )

    if not commit_payload:
        add_issue(
            issues,
            "commit_scope_precheck_missing",
            "BR-20260425-148-precheck",
            "commit_scope_payload",
            "",
            "BR-148-precheck JSON attached",
        )
    else:
        for field in [
            "risk_files",
            "issue_rows",
            "engine_source_dirty",
            "large_data_dirty",
            "release_generated_dirty",
            "unclassified_dirty",
            "canonical_truth_write_allowed_sum",
            "truth_intake_allowed_sum",
            "threshold_patch_allowed_sum",
            "engine_patch_allowed_sum",
        ]:
            if int_value(commit_payload.get(field, 0)) != 0:
                add_issue(
                    issues,
                    "commit_scope_precheck_not_clean",
                    "BR-20260425-148-precheck",
                    field,
                    str(commit_payload.get(field, "")),
                    "0",
                )
        if int_value(commit_payload.get("commit_scope_ready_flag", 0)) != 1:
            add_issue(
                issues,
                "commit_scope_precheck_not_ready",
                "BR-20260425-148-precheck",
                "commit_scope_ready_flag",
                str(commit_payload.get("commit_scope_ready_flag", "")),
                "1",
            )

    return pd.DataFrame(rows).reindex(columns=AUDIT_COLUMNS), pd.DataFrame(issues).reindex(columns=ISSUE_COLUMNS)


def build_next_actions() -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "next_action_order": 1,
            "action_id": "stage_scope_if_requested",
            "action_type": "bookkeeping",
            "blocked_by": "user approval to stage/commit",
            "action_detail": "Use the BR-148-precheck file manifest; do not use git add .",
            "safe_to_do_without_real_data_flag": 1,
        },
        {
            "owner_branch": OWNER_BRANCH,
            "next_action_order": 2,
            "action_id": "resume_real_capture_intake",
            "action_type": "real_data",
            "blocked_by": "real KTC ESS capture CSV/labels absent",
            "action_detail": "Run BR-130 after user supplies real capture bundle.",
            "safe_to_do_without_real_data_flag": 0,
        },
        {
            "owner_branch": OWNER_BRANCH,
            "next_action_order": 3,
            "action_id": "resume_rule_shadow_path",
            "action_type": "semantic_gate",
            "blocked_by": "truth replay, selected rule, shadow result absent",
            "action_detail": "Run BR-140/141/142 before any BR-144 panel-engine patch discussion.",
            "safe_to_do_without_real_data_flag": 0,
        },
    ]
    return pd.DataFrame(rows).reindex(columns=NEXT_COLUMNS)


def build_summary(audit: pd.DataFrame, issues: pd.DataFrame, commit_payload: dict[str, object]) -> pd.DataFrame:
    completed = int(audit["status_family"].eq("complete").sum()) if len(audit) else 0
    blocked = int(audit["status_family"].eq("blocked").sum()) if len(audit) else 0
    open_count = int(audit["status_family"].eq("open").sum()) if len(audit) else 0
    required_docs_missing = int((audit["required_doc_present_flag"].map(int_value) == 0).sum()) if len(audit) else 0
    required_builders_missing = int((audit["required_builder_present_flag"].map(int_value) == 0).sum()) if len(audit) else 0
    required_smokes_missing = int((audit["required_smoke_present_flag"].map(int_value) == 0).sum()) if len(audit) else 0
    state_mismatch = int((audit["state_ok_flag"].map(int_value) == 0).sum()) if len(audit) else 0
    commit_ready = int_value(commit_payload.get("commit_scope_ready_flag", 0)) if commit_payload else 0
    handoff_ready = int(
        len(audit) == 23
        and completed == len(EXPECTED_COMPLETE)
        and blocked == len(EXPECTED_BLOCKED)
        and open_count == 0
        and required_docs_missing == 0
        and required_builders_missing == 0
        and required_smokes_missing == 0
        and state_mismatch == 0
        and len(issues) == 0
        and commit_ready == 1
    )
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "queue_rows": int(len(audit)),
            "completed_rows": completed,
            "blocked_rows": blocked,
            "open_rows": open_count,
            "state_mismatch_rows": state_mismatch,
            "required_docs_missing": required_docs_missing,
            "required_builders_missing": required_builders_missing,
            "required_smokes_missing": required_smokes_missing,
            "commit_scope_ready_flag": commit_ready,
            "issue_rows": int(len(issues)),
            "blocked_state_handoff_ready_flag": handoff_ready,
            "real_data_required_to_continue_flag": 1,
            "engine_patch_allowed_sum": 0,
            "threshold_patch_allowed_sum": 0,
            "truth_intake_allowed_sum": 0,
            "canonical_truth_write_allowed_sum": 0,
        }
    ]
    if len(audit):
        for family, sub in audit.groupby("status_family"):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "status_family",
                    "summary_key": family,
                    "queue_rows": int(len(sub)),
                    "completed_rows": int(sub["status_family"].eq("complete").sum()),
                    "blocked_rows": int(sub["status_family"].eq("blocked").sum()),
                    "open_rows": int(sub["status_family"].eq("open").sum()),
                    "state_mismatch_rows": int((sub["state_ok_flag"].map(int_value) == 0).sum()),
                    "required_docs_missing": int((sub["required_doc_present_flag"].map(int_value) == 0).sum()),
                    "required_builders_missing": int((sub["required_builder_present_flag"].map(int_value) == 0).sum()),
                    "required_smokes_missing": int((sub["required_smoke_present_flag"].map(int_value) == 0).sum()),
                    "commit_scope_ready_flag": 0,
                    "issue_rows": 0,
                    "blocked_state_handoff_ready_flag": 0,
                    "real_data_required_to_continue_flag": 1,
                    "engine_patch_allowed_sum": 0,
                    "threshold_patch_allowed_sum": 0,
                    "truth_intake_allowed_sum": 0,
                    "canonical_truth_write_allowed_sum": 0,
                }
            )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, summary: pd.DataFrame) -> None:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    text = "\n".join(
        [
            "# BR-20260425-149 precheck blocked-state readiness handoff",
            "",
            f"- queue rows: `{overall['queue_rows']}`",
            f"- completed rows: `{overall['completed_rows']}`",
            f"- blocked rows: `{overall['blocked_rows']}`",
            f"- open rows: `{overall['open_rows']}`",
            f"- state mismatch rows: `{overall['state_mismatch_rows']}`",
            f"- required docs missing: `{overall['required_docs_missing']}`",
            f"- required builders missing: `{overall['required_builders_missing']}`",
            f"- required smokes missing: `{overall['required_smokes_missing']}`",
            f"- commit-scope ready flag: `{overall['commit_scope_ready_flag']}`",
            f"- issue rows: `{overall['issue_rows']}`",
            f"- blocked-state handoff ready flag: `{overall['blocked_state_handoff_ready_flag']}`",
            f"- real data required to continue flag: `{overall['real_data_required_to_continue_flag']}`",
            "",
            "This precheck does not mark official BR-149 complete.",
            "It only proves the current blocked state is readable and safe to hand off.",
            "",
        ]
    )
    (output_dir / NOTE_OUTPUT_NAME).write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a blocked-state readiness/handoff audit for the BR-128..150 runway.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--queue-input", type=Path, default=Path(DEFAULT_QUEUE))
    parser.add_argument("--commit-scope-json", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    queue_path = resolve(repo_root, args.queue_input)
    commit_path = resolve(repo_root, args.commit_scope_json) if args.commit_scope_json else None
    output_dir = args.output_dir if args.output_dir.is_absolute() else repo_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    queue = read_queue(queue_path)
    commit_payload = read_commit_scope_payload(commit_path)
    audit, issues = build_audit(repo_root, queue, commit_payload)
    next_actions = build_next_actions()
    summary = build_summary(audit, issues, commit_payload)

    audit.to_csv(output_dir / AUDIT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    issues.to_csv(output_dir / ISSUES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    next_actions.to_csv(output_dir / NEXT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "queue_rows": int(overall["queue_rows"]),
        "completed_rows": int(overall["completed_rows"]),
        "blocked_rows": int(overall["blocked_rows"]),
        "open_rows": int(overall["open_rows"]),
        "state_mismatch_rows": int(overall["state_mismatch_rows"]),
        "required_docs_missing": int(overall["required_docs_missing"]),
        "required_builders_missing": int(overall["required_builders_missing"]),
        "required_smokes_missing": int(overall["required_smokes_missing"]),
        "commit_scope_ready_flag": int(overall["commit_scope_ready_flag"]),
        "issue_rows": int(overall["issue_rows"]),
        "blocked_state_handoff_ready_flag": int(overall["blocked_state_handoff_ready_flag"]),
        "real_data_required_to_continue_flag": int(overall["real_data_required_to_continue_flag"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
        "outputs": {
            "audit": str(output_dir / AUDIT_OUTPUT_NAME),
            "issues": str(output_dir / ISSUES_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "next_actions": str(output_dir / NEXT_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
            "json": str(output_dir / JSON_OUTPUT_NAME),
        },
    }
    (output_dir / JSON_OUTPUT_NAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
