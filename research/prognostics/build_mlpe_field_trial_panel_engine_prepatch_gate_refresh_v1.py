#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-143"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_panel_engine_prepatch_gate_refresh_br143_check"

CONTRACT_OUTPUT_NAME = "mlpe_field_trial_panel_engine_prepatch_gate_refresh_contract_v1.csv"
GATE_OUTPUT_NAME = "mlpe_field_trial_panel_engine_prepatch_gate_refresh_dry_run_v1.csv"
ISSUES_OUTPUT_NAME = "mlpe_field_trial_panel_engine_prepatch_gate_refresh_issues_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_panel_engine_prepatch_gate_refresh_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_panel_engine_prepatch_gate_refresh_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_panel_engine_prepatch_gate_refresh_v1.json"

APPROVAL_FIELDS = [
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

CANDIDATE_COLUMNS = [
    "patch_candidate_id",
    "selected_rule_candidate_flag",
    "truth_replay_scorecard_ready_flag",
    "positive_support_count",
    "negative_support_count",
    "shadow_apply_ready_flag",
    "shadow_result_delta_intended_only_flag",
    "unintended_result_drift_count",
    "source_package_sync_plan_flag",
    "public_behavior_doc_update_plan_flag",
    "operator_facing_change_expected_flag",
    "py_compile_validation_plan_flag",
    "full_runtime_smoke_validation_plan_flag",
    "result_delta_compare_validation_plan_flag",
    "result_delta_acceptance_criteria",
    "large_data_paths_in_scope_flag",
    "reviewer_prepatch_review_flag",
    "reviewer_prepatch_note",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

RUNBOOK_COLUMNS = [
    "overall_status",
    "gate_count",
    "passed_gate_count",
    "failed_gate_count",
    "panel_engine_gate_status",
    "fault_family_gate_status",
    "common_cause_gate_status",
    "engine_change_detected",
]

CONTRACT_GROUPS = [
    {
        "gate_group": "selected_rule_candidate_ready",
        "required_flag": 1,
        "required_fields_csv": "selected_rule_candidate_flag",
        "pass_condition": "exactly one rule/semantic candidate is selected before BR-144",
        "blocked_status": "blocked_no_selected_rule_candidate",
        "next_gate_use": "BR-144 semantic patch entry condition",
    },
    {
        "gate_group": "truth_replay_support_ready",
        "required_flag": 1,
        "required_fields_csv": "truth_replay_scorecard_ready_flag,positive_support_count,negative_support_count",
        "pass_condition": "truth replay exists with positive and negative support",
        "blocked_status": "blocked_truth_replay_support_not_ready",
        "next_gate_use": "avoid threshold/rule patch without truth replay",
    },
    {
        "gate_group": "shadow_apply_result_ready",
        "required_flag": 1,
        "required_fields_csv": "shadow_apply_ready_flag,shadow_result_delta_intended_only_flag,unintended_result_drift_count",
        "pass_condition": "shadow apply exists and result delta is intended-only",
        "blocked_status": "blocked_shadow_apply_result_not_ready",
        "next_gate_use": "prove intended-only effect before code semantics",
    },
    {
        "gate_group": "three_gate_prepatch_runbook_ready",
        "required_flag": 1,
        "required_fields_csv": "prepatch_runbook_summary",
        "pass_condition": "BR-076 3-gate runbook passes: panel-engine, fault-family, common-cause",
        "blocked_status": "blocked_three_gate_prepatch_runbook_not_ready",
        "next_gate_use": "minimum direct panel-engine patch safety gate",
    },
    {
        "gate_group": "source_package_mirror_plan_ready",
        "required_flag": 1,
        "required_fields_csv": "source_package_sync_plan_flag",
        "pass_condition": "source/package sync plan is explicit before engine patch",
        "blocked_status": "blocked_source_package_mirror_plan_missing",
        "next_gate_use": "prevent source/package mirror drift",
    },
    {
        "gate_group": "public_behavior_docs_plan_ready",
        "required_flag": 1,
        "required_fields_csv": "public_behavior_doc_update_plan_flag,operator_facing_change_expected_flag",
        "pass_condition": "public behavior docs are planned when behavior may change",
        "blocked_status": "blocked_public_behavior_docs_plan_missing",
        "next_gate_use": "paper_pack/ONEPAGER/data dictionary sync before behavior change",
    },
    {
        "gate_group": "validation_commands_plan_ready",
        "required_flag": 1,
        "required_fields_csv": "py_compile_validation_plan_flag,full_runtime_smoke_validation_plan_flag,result_delta_compare_validation_plan_flag",
        "pass_condition": "py_compile, full runtime smoke, and result-delta compare are planned",
        "blocked_status": "blocked_validation_commands_plan_missing",
        "next_gate_use": "make BR-144/145/146 reproducible",
    },
    {
        "gate_group": "result_delta_acceptance_plan_ready",
        "required_flag": 1,
        "required_fields_csv": "result_delta_acceptance_criteria",
        "pass_condition": "intended-only result delta acceptance criteria are non-empty",
        "blocked_status": "blocked_result_delta_acceptance_plan_missing",
        "next_gate_use": "avoid unsupported drift acceptance",
    },
    {
        "gate_group": "large_data_exclusion_locked",
        "required_flag": 1,
        "required_fields_csv": "large_data_paths_in_scope_flag",
        "pass_condition": "large data/raw/out paths are not in patch scope",
        "blocked_status": "blocked_large_data_paths_in_scope",
        "next_gate_use": "keep repo/package scope clean",
    },
    {
        "gate_group": "reviewer_prepatch_approval_note",
        "required_flag": 1,
        "required_fields_csv": "reviewer_prepatch_review_flag,reviewer_prepatch_note",
        "pass_condition": "reviewer prepatch approval flag is 1 and note is non-empty",
        "blocked_status": "blocked_reviewer_prepatch_approval_missing",
        "next_gate_use": "human review before BR-144 semantic patch",
    },
    {
        "gate_group": "write_boundary_locked",
        "required_flag": 1,
        "required_fields_csv": "canonical_truth_write_allowed,truth_intake_allowed,threshold_patch_allowed,engine_patch_allowed",
        "pass_condition": "BR-143 itself authorizes no truth, threshold, or engine writes",
        "blocked_status": "blocked_write_boundary_violation",
        "next_gate_use": "separate gate readiness from patch authorization",
    },
    {
        "gate_group": "engine_patch_authorization_blocked_until_br144",
        "required_flag": 1,
        "required_fields_csv": "engine_patch_allowed",
        "pass_condition": "engine_patch_allowed remains 0 in BR-143",
        "blocked_status": "blocked_engine_patch_authorization_leak",
        "next_gate_use": "BR-143 is gate refresh only; BR-144 is separate",
    },
]

CONTRACT_COLUMNS = [
    "owner_branch",
    "gate_group",
    "required_flag",
    "required_fields_csv",
    "pass_condition",
    "blocked_status",
    "next_gate_use",
]

GATE_COLUMNS = [
    "owner_branch",
    "patch_candidate_id",
    "gate_group",
    "required_flag",
    "candidate_row_present_flag",
    "runbook_summary_present_flag",
    "gate_passed_flag",
    "gate_blocking_flag",
    "panel_engine_prepatch_gate_status",
    "selected_rule_candidate_flag",
    "truth_replay_scorecard_ready_flag",
    "positive_support_count",
    "negative_support_count",
    "shadow_apply_ready_flag",
    "shadow_result_delta_intended_only_flag",
    "unintended_result_drift_count",
    "prepatch_runbook_overall_status",
    "prepatch_runbook_gate_count",
    "source_package_sync_plan_flag",
    "public_behavior_doc_update_plan_flag",
    "operator_facing_change_expected_flag",
    "py_compile_validation_plan_flag",
    "full_runtime_smoke_validation_plan_flag",
    "result_delta_compare_validation_plan_flag",
    "result_delta_acceptance_criteria",
    "large_data_paths_in_scope_flag",
    "reviewer_prepatch_review_flag",
    "reviewer_prepatch_note",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "gate_next_action",
]

ISSUE_COLUMNS = [
    "owner_branch",
    "patch_candidate_id",
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


def approval_violation(row: pd.Series | None) -> bool:
    if row is None:
        return False
    return any(int_value(row.get(field, "0")) != 0 for field in APPROVAL_FIELDS)


def build_contract() -> pd.DataFrame:
    rows = [{"owner_branch": OWNER_BRANCH, **group} for group in CONTRACT_GROUPS]
    return pd.DataFrame(rows).reindex(columns=CONTRACT_COLUMNS)


def add_issue(issues: list[dict[str, object]], candidate_id: str, issue_type: str, field: str, observed: str, expected: str) -> None:
    issues.append(
        {
            "owner_branch": OWNER_BRANCH,
            "patch_candidate_id": candidate_id,
            "issue_type": issue_type,
            "field": field,
            "observed_value": observed,
            "expected_policy": expected,
        }
    )


def build_missing_input_rows() -> tuple[pd.DataFrame, pd.DataFrame]:
    gate = pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "patch_candidate_id": "",
                "gate_group": "contract_input",
                "required_flag": 1,
                "candidate_row_present_flag": 0,
                "runbook_summary_present_flag": 0,
                "gate_passed_flag": 0,
                "gate_blocking_flag": 1,
                "panel_engine_prepatch_gate_status": "blocked_missing_prepatch_candidate_input",
                "engine_patch_allowed": 0,
                "gate_next_action": "Select a shadow rule candidate and attach replay/shadow/runbook evidence before BR-144.",
            }
        ]
    ).reindex(columns=GATE_COLUMNS, fill_value="")
    issues = pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "patch_candidate_id": "",
                "issue_type": "missing_prepatch_candidate_input",
                "field": "prepatch_candidate_input",
                "observed_value": "",
                "expected_policy": "candidate row with replay, shadow, validation, and reviewer fields before BR-144",
            }
        ]
    ).reindex(columns=ISSUE_COLUMNS)
    return gate, issues


def runbook_passed(runbook_summary: pd.DataFrame | None) -> tuple[int, str, int]:
    if runbook_summary is None or runbook_summary.empty:
        return 0, "", 0
    row = runbook_summary.iloc[0]
    status = normalize_text(row.get("overall_status", ""))
    gate_count = int_value(row.get("gate_count", "0"))
    panel = normalize_text(row.get("panel_engine_gate_status", ""))
    fault = normalize_text(row.get("fault_family_gate_status", ""))
    common = normalize_text(row.get("common_cause_gate_status", ""))
    passed = int(status == "pass" and gate_count >= 3 and panel == "pass" and fault == "pass" and common == "pass")
    return passed, status, gate_count


def group_status(group_name: str, candidate: pd.Series, runbook_summary: pd.DataFrame | None) -> tuple[str, int, int]:
    runbook_ready, _, _ = runbook_passed(runbook_summary)
    selected_count_ok = int_value(candidate.get("selected_rule_candidate_flag", "0")) == 1
    if group_name == "selected_rule_candidate_ready":
        passed = selected_count_ok
    elif group_name == "truth_replay_support_ready":
        passed = (
            int_value(candidate.get("truth_replay_scorecard_ready_flag", "0")) == 1
            and int_value(candidate.get("positive_support_count", "0")) > 0
            and int_value(candidate.get("negative_support_count", "0")) > 0
        )
    elif group_name == "shadow_apply_result_ready":
        passed = (
            int_value(candidate.get("shadow_apply_ready_flag", "0")) == 1
            and int_value(candidate.get("shadow_result_delta_intended_only_flag", "0")) == 1
            and int_value(candidate.get("unintended_result_drift_count", "0")) == 0
        )
    elif group_name == "three_gate_prepatch_runbook_ready":
        passed = runbook_ready == 1
    elif group_name == "source_package_mirror_plan_ready":
        passed = int_value(candidate.get("source_package_sync_plan_flag", "0")) == 1
    elif group_name == "public_behavior_docs_plan_ready":
        behavior_change = int_value(candidate.get("operator_facing_change_expected_flag", "0")) == 1
        passed = (not behavior_change) or int_value(candidate.get("public_behavior_doc_update_plan_flag", "0")) == 1
    elif group_name == "validation_commands_plan_ready":
        passed = (
            int_value(candidate.get("py_compile_validation_plan_flag", "0")) == 1
            and int_value(candidate.get("full_runtime_smoke_validation_plan_flag", "0")) == 1
            and int_value(candidate.get("result_delta_compare_validation_plan_flag", "0")) == 1
        )
    elif group_name == "result_delta_acceptance_plan_ready":
        passed = bool(normalize_text(candidate.get("result_delta_acceptance_criteria", "")))
    elif group_name == "large_data_exclusion_locked":
        passed = int_value(candidate.get("large_data_paths_in_scope_flag", "0")) == 0
    elif group_name == "reviewer_prepatch_approval_note":
        passed = int_value(candidate.get("reviewer_prepatch_review_flag", "0")) == 1 and bool(
            normalize_text(candidate.get("reviewer_prepatch_note", ""))
        )
    elif group_name == "write_boundary_locked":
        passed = not approval_violation(candidate)
    elif group_name == "engine_patch_authorization_blocked_until_br144":
        passed = int_value(candidate.get("engine_patch_allowed", "0")) == 0
    else:
        passed = False

    if passed:
        return "panel_engine_prepatch_gate_group_passed", 1, 0
    for group in CONTRACT_GROUPS:
        if group["gate_group"] == group_name:
            return str(group["blocked_status"]), 0, 1
    return "blocked_unknown_prepatch_gate_group", 0, 1


def next_action(status: str) -> str:
    if status == "panel_engine_prepatch_gate_group_passed":
        return "Keep as prepatch evidence only; BR-143 does not authorize code changes."
    if status == "blocked_no_selected_rule_candidate":
        return "Wait for BR-141/142 selected shadow candidate evidence."
    if status == "blocked_truth_replay_support_not_ready":
        return "Run BR-140 replay with enough positive and negative support."
    if status == "blocked_three_gate_prepatch_runbook_not_ready":
        return "Run the BR-076 panel-engine/fault-family/common-cause runbook and attach its passing summary."
    if status == "blocked_write_boundary_violation":
        return "Clear all write/approval fields; BR-143 is not a write approval branch."
    return "Resolve this prepatch gate before BR-144 semantic patch discussion."


def build_gate(candidate_input: pd.DataFrame, runbook_summary: pd.DataFrame | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    runbook_ready, runbook_status, runbook_gate_count = runbook_passed(runbook_summary)

    duplicate_ids = candidate_input["patch_candidate_id"].map(normalize_text).value_counts()
    duplicate_ids = {idx for idx, count in duplicate_ids.items() if idx and count > 1}
    selected_count = int(candidate_input["selected_rule_candidate_flag"].map(int_value).sum()) if len(candidate_input) else 0

    for _, candidate in candidate_input.iterrows():
        candidate_id = normalize_text(candidate.get("patch_candidate_id", ""))
        if not candidate_id:
            add_issue(issues, candidate_id, "missing_patch_candidate_id", "patch_candidate_id", "", "non-empty patch_candidate_id")
        if candidate_id in duplicate_ids:
            add_issue(issues, candidate_id, "duplicate_patch_candidate_id", "patch_candidate_id", candidate_id, "unique patch_candidate_id")
        if selected_count != 1:
            add_issue(issues, candidate_id, "selected_rule_candidate_count_not_one", "selected_rule_candidate_flag", str(selected_count), "exactly one selected candidate")

        for group in CONTRACT_GROUPS:
            group_name = str(group["gate_group"])
            status, passed, blocking = group_status(group_name, candidate, runbook_summary)
            if blocking:
                add_issue(issues, candidate_id, status, group_name, "not passed", str(group["pass_condition"]))
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "patch_candidate_id": candidate_id,
                    "gate_group": group_name,
                    "required_flag": int(group["required_flag"]),
                    "candidate_row_present_flag": 1,
                    "runbook_summary_present_flag": int(runbook_summary is not None and not runbook_summary.empty),
                    "gate_passed_flag": passed,
                    "gate_blocking_flag": blocking,
                    "panel_engine_prepatch_gate_status": status,
                    "selected_rule_candidate_flag": int_value(candidate.get("selected_rule_candidate_flag", "0")),
                    "truth_replay_scorecard_ready_flag": int_value(candidate.get("truth_replay_scorecard_ready_flag", "0")),
                    "positive_support_count": int_value(candidate.get("positive_support_count", "0")),
                    "negative_support_count": int_value(candidate.get("negative_support_count", "0")),
                    "shadow_apply_ready_flag": int_value(candidate.get("shadow_apply_ready_flag", "0")),
                    "shadow_result_delta_intended_only_flag": int_value(candidate.get("shadow_result_delta_intended_only_flag", "0")),
                    "unintended_result_drift_count": int_value(candidate.get("unintended_result_drift_count", "0")),
                    "prepatch_runbook_overall_status": runbook_status,
                    "prepatch_runbook_gate_count": runbook_gate_count,
                    "source_package_sync_plan_flag": int_value(candidate.get("source_package_sync_plan_flag", "0")),
                    "public_behavior_doc_update_plan_flag": int_value(candidate.get("public_behavior_doc_update_plan_flag", "0")),
                    "operator_facing_change_expected_flag": int_value(candidate.get("operator_facing_change_expected_flag", "0")),
                    "py_compile_validation_plan_flag": int_value(candidate.get("py_compile_validation_plan_flag", "0")),
                    "full_runtime_smoke_validation_plan_flag": int_value(candidate.get("full_runtime_smoke_validation_plan_flag", "0")),
                    "result_delta_compare_validation_plan_flag": int_value(candidate.get("result_delta_compare_validation_plan_flag", "0")),
                    "result_delta_acceptance_criteria": normalize_text(candidate.get("result_delta_acceptance_criteria", "")),
                    "large_data_paths_in_scope_flag": int_value(candidate.get("large_data_paths_in_scope_flag", "0")),
                    "reviewer_prepatch_review_flag": int_value(candidate.get("reviewer_prepatch_review_flag", "0")),
                    "reviewer_prepatch_note": normalize_text(candidate.get("reviewer_prepatch_note", "")),
                    "canonical_truth_write_allowed": 0,
                    "truth_intake_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "engine_patch_allowed": 0,
                    "gate_next_action": next_action(status),
                }
            )
        if runbook_ready != 1:
            add_issue(
                issues,
                candidate_id,
                "three_gate_prepatch_runbook_not_ready",
                "prepatch_runbook_summary",
                runbook_status or "missing",
                "overall_status=pass with gate_count>=3 and all sub-gates pass",
            )

    return pd.DataFrame(rows).reindex(columns=GATE_COLUMNS), pd.DataFrame(issues).reindex(columns=ISSUE_COLUMNS)


def ready_candidate_count(gate: pd.DataFrame) -> int:
    ready = 0
    for _, sub in gate[gate["patch_candidate_id"].map(normalize_text).ne("")].groupby("patch_candidate_id"):
        required = sub[sub["required_flag"].map(int_value).eq(1)]
        if len(required) and int(required["gate_blocking_flag"].map(int_value).sum()) == 0:
            ready += 1
    return ready


def build_summary(gate: pd.DataFrame, issues: pd.DataFrame, contract: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "contract_rows": int(len(contract)),
            "patch_candidates": int(gate["patch_candidate_id"].map(normalize_text).replace("", pd.NA).dropna().nunique()) if len(gate) else 0,
            "prepatch_ready_candidates": ready_candidate_count(gate),
            "gate_rows": int(len(gate)),
            "gate_passed_rows": int(gate["gate_passed_flag"].map(int_value).sum()) if len(gate) else 0,
            "gate_blocked_rows": int(gate["gate_blocking_flag"].map(int_value).sum()) if len(gate) else 0,
            "issue_rows": int(len(issues)),
            "canonical_truth_write_allowed_sum": int(gate["canonical_truth_write_allowed"].map(int_value).sum()) if len(gate) else 0,
            "truth_intake_allowed_sum": int(gate["truth_intake_allowed"].map(int_value).sum()) if len(gate) else 0,
            "threshold_patch_allowed_sum": int(gate["threshold_patch_allowed"].map(int_value).sum()) if len(gate) else 0,
            "engine_patch_allowed_sum": int(gate["engine_patch_allowed"].map(int_value).sum()) if len(gate) else 0,
        }
    ]
    if len(gate):
        for status, sub in gate.groupby("panel_engine_prepatch_gate_status", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "panel_engine_prepatch_gate_status",
                    "summary_key": status,
                    "contract_rows": int(len(contract)),
                    "patch_candidates": int(sub["patch_candidate_id"].map(normalize_text).replace("", pd.NA).dropna().nunique()),
                    "prepatch_ready_candidates": 0,
                    "gate_rows": int(len(sub)),
                    "gate_passed_rows": int(sub["gate_passed_flag"].map(int_value).sum()),
                    "gate_blocked_rows": int(sub["gate_blocking_flag"].map(int_value).sum()),
                    "issue_rows": int(len(issues)),
                    "canonical_truth_write_allowed_sum": 0,
                    "truth_intake_allowed_sum": 0,
                    "threshold_patch_allowed_sum": 0,
                    "engine_patch_allowed_sum": 0,
                }
            )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, summary: pd.DataFrame) -> None:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    text = "\n".join(
        [
            "# BR-20260425-143 panel-engine prepatch gate refresh",
            "",
            f"- contract rows: `{overall['contract_rows']}`",
            f"- patch candidates: `{overall['patch_candidates']}`",
            f"- prepatch-ready candidates: `{overall['prepatch_ready_candidates']}`",
            f"- gate rows: `{overall['gate_rows']}`",
            f"- gate passed rows: `{overall['gate_passed_rows']}`",
            f"- gate blocked rows: `{overall['gate_blocked_rows']}`",
            f"- issue rows: `{overall['issue_rows']}`",
            f"- canonical truth write allowed sum: `{overall['canonical_truth_write_allowed_sum']}`",
            f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
            f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
            f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
            "",
            "This is a prepatch gate refresh only.",
            "It does not authorize BR-144, canonical truth writes, threshold patches, or direct panel-engine edits.",
            "",
        ]
    )
    (output_dir / NOTE_OUTPUT_NAME).write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the BR-143 panel-engine prepatch gate refresh contract.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--prepatch-candidate-input", type=Path, default=None)
    parser.add_argument("--prepatch-runbook-summary", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    candidate_path = resolve_path(repo_root, args.prepatch_candidate_input) if args.prepatch_candidate_input else None
    runbook_path = resolve_path(repo_root, args.prepatch_runbook_summary) if args.prepatch_runbook_summary else None
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    contract = build_contract()
    if candidate_path is None or not candidate_path.exists():
        gate, issues = build_missing_input_rows()
    else:
        candidate_input = read_csv(candidate_path, CANDIDATE_COLUMNS)
        runbook_summary = read_csv(runbook_path, RUNBOOK_COLUMNS) if runbook_path and runbook_path.exists() else None
        gate, issues = build_gate(candidate_input, runbook_summary)

    summary = build_summary(gate, issues, contract)

    contract.to_csv(output_dir / CONTRACT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    gate.to_csv(output_dir / GATE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    issues.to_csv(output_dir / ISSUES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "contract_rows": int(overall["contract_rows"]),
        "patch_candidates": int(overall["patch_candidates"]),
        "prepatch_ready_candidates": int(overall["prepatch_ready_candidates"]),
        "gate_rows": int(overall["gate_rows"]),
        "gate_passed_rows": int(overall["gate_passed_rows"]),
        "gate_blocked_rows": int(overall["gate_blocked_rows"]),
        "issue_rows": int(overall["issue_rows"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "contract": str(output_dir / CONTRACT_OUTPUT_NAME),
            "gate": str(output_dir / GATE_OUTPUT_NAME),
            "issues": str(output_dir / ISSUES_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
            "json": str(output_dir / JSON_OUTPUT_NAME),
        },
    }
    (output_dir / JSON_OUTPUT_NAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
