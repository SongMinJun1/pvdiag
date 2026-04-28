#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "research" / "prognostics" / "build_mlpe_field_trial_panel_engine_prepatch_gate_refresh_v1.py"


def run_builder(*args: str) -> dict[str, object]:
    result = subprocess.run(
        ["python3", str(BUILDER), "--repo-root", str(ROOT), *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def good_candidate() -> dict[str, object]:
    return {
        "patch_candidate_id": "PATCH-OK",
        "selected_rule_candidate_flag": 1,
        "truth_replay_scorecard_ready_flag": 1,
        "positive_support_count": 5,
        "negative_support_count": 5,
        "shadow_apply_ready_flag": 1,
        "shadow_result_delta_intended_only_flag": 1,
        "unintended_result_drift_count": 0,
        "source_package_sync_plan_flag": 1,
        "public_behavior_doc_update_plan_flag": 1,
        "operator_facing_change_expected_flag": 1,
        "py_compile_validation_plan_flag": 1,
        "full_runtime_smoke_validation_plan_flag": 1,
        "result_delta_compare_validation_plan_flag": 1,
        "result_delta_acceptance_criteria": "changed rows must be intended-only and unsupported performance claims remain blocked",
        "large_data_paths_in_scope_flag": 0,
        "reviewer_prepatch_review_flag": 1,
        "reviewer_prepatch_note": "synthetic reviewer approval for smoke",
        "canonical_truth_write_allowed": 0,
        "truth_intake_allowed": 0,
        "threshold_patch_allowed": 0,
        "engine_patch_allowed": 0,
    }


def good_runbook() -> dict[str, object]:
    return {
        "overall_status": "pass",
        "gate_count": 3,
        "passed_gate_count": 3,
        "failed_gate_count": 0,
        "panel_engine_gate_status": "pass",
        "fault_family_gate_status": "pass",
        "common_cause_gate_status": "pass",
        "engine_change_detected": 0,
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        out_dir = Path(td) / "missing"
        missing = run_builder("--output-dir", str(out_dir))
        assert missing["contract_rows"] == 12
        assert missing["patch_candidates"] == 0
        assert missing["prepatch_ready_candidates"] == 0
        assert missing["gate_blocked_rows"] == 1
        assert missing["issue_rows"] == 1

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        candidate = root / "candidate.csv"
        runbook = root / "runbook.csv"
        out_dir = root / "good_out"
        write_csv(candidate, [good_candidate()])
        write_csv(runbook, [good_runbook()])
        good = run_builder(
            "--prepatch-candidate-input",
            str(candidate),
            "--prepatch-runbook-summary",
            str(runbook),
            "--output-dir",
            str(out_dir),
        )
        assert good["patch_candidates"] == 1
        assert good["prepatch_ready_candidates"] == 1
        assert good["gate_rows"] == 12
        assert good["gate_blocked_rows"] == 0
        assert good["engine_patch_allowed_sum"] == 0

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        candidate = root / "candidate.csv"
        runbook = root / "runbook.csv"
        out_dir = root / "bad_out"
        bad_row = good_candidate()
        bad_row.update(
            {
                "patch_candidate_id": "PATCH-BAD",
                "selected_rule_candidate_flag": 0,
                "truth_replay_scorecard_ready_flag": 0,
                "positive_support_count": 0,
                "negative_support_count": 0,
                "shadow_apply_ready_flag": 0,
                "unintended_result_drift_count": 2,
                "source_package_sync_plan_flag": 0,
                "operator_facing_change_expected_flag": 1,
                "public_behavior_doc_update_plan_flag": 0,
                "py_compile_validation_plan_flag": 0,
                "result_delta_acceptance_criteria": "",
                "large_data_paths_in_scope_flag": 1,
                "reviewer_prepatch_review_flag": 0,
                "reviewer_prepatch_note": "",
                "engine_patch_allowed": 1,
            }
        )
        bad_runbook = good_runbook()
        bad_runbook.update({"overall_status": "fail", "failed_gate_count": 1})
        write_csv(candidate, [bad_row])
        write_csv(runbook, [bad_runbook])
        bad = run_builder(
            "--prepatch-candidate-input",
            str(candidate),
            "--prepatch-runbook-summary",
            str(runbook),
            "--output-dir",
            str(out_dir),
        )
        assert bad["patch_candidates"] == 1
        assert bad["prepatch_ready_candidates"] == 0
        assert bad["gate_blocked_rows"] >= 9
        assert bad["engine_patch_allowed_sum"] == 0
        status_df = pd.read_csv(out_dir / "mlpe_field_trial_panel_engine_prepatch_gate_refresh_dry_run_v1.csv", encoding="utf-8-sig")
        statuses = set(status_df["panel_engine_prepatch_gate_status"])
        assert "blocked_no_selected_rule_candidate" in statuses
        assert "blocked_truth_replay_support_not_ready" in statuses
        assert "blocked_shadow_apply_result_not_ready" in statuses
        assert "blocked_three_gate_prepatch_runbook_not_ready" in statuses
        assert "blocked_source_package_mirror_plan_missing" in statuses
        assert "blocked_public_behavior_docs_plan_missing" in statuses
        assert "blocked_result_delta_acceptance_plan_missing" in statuses
        assert "blocked_large_data_paths_in_scope" in statuses
        assert "blocked_reviewer_prepatch_approval_missing" in statuses
        assert "blocked_write_boundary_violation" in statuses
        assert "blocked_engine_patch_authorization_leak" in statuses

    print(
        json.dumps(
            {
                "smoke": "ok",
                "missing_blocked_rows": missing["gate_blocked_rows"],
                "good_ready_candidates": good["prepatch_ready_candidates"],
                "bad_ready_candidates": bad["prepatch_ready_candidates"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
