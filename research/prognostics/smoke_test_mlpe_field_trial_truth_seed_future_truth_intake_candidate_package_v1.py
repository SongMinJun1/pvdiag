#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="mlpe_truth_intake_candidate_package_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        validation = tmp / "validation.csv"
        issues = tmp / "issues.csv"
        output_dir = tmp / "candidate_package"

        validation.write_text(
            "owner_branch,trial_event_id,truth_seed_reviewer_decision,truth_candidate_role,duplicate_decision_event_id_flag,required_fields_missing_flag,allowed_value_violation_flag,approval_flag_violation_flag,approval_requirements_failed_flag,reviewer_decision_complete_flag,decision_validation_failed_flag,future_truth_intake_candidate_flag,canonical_truth_write_allowed,truth_intake_allowed,threshold_patch_allowed,engine_patch_allowed,decision_validation_bucket,missing_required_fields_csv,invalid_allowed_value_fields_csv,approval_flag_violation_fields_csv,approval_requirement_failures_csv,next_action\n"
            "BR-20260425-122,CANDIDATE_OK,approve_for_future_truth_intake,positive_truth_candidate,0,0,0,0,0,1,0,1,0,0,0,0,validated_future_truth_intake_candidate,,,,,candidate ok\n"
            "BR-20260425-122,REJECT_OK,reject_not_truth_seed,negative_truth_candidate,0,0,0,0,0,1,0,0,0,0,0,0,validated_reject_not_truth_seed,,,,,reject ok\n"
            "BR-20260425-122,DEFER_OK,defer_needs_more_evidence,positive_truth_candidate,0,0,0,0,0,1,0,0,0,0,0,0,validated_defer_needs_more_evidence,,,,,defer ok\n"
            "BR-20260425-122,FAILED_APPROVE,approve_for_future_truth_intake,positive_truth_candidate,0,0,0,0,1,0,1,0,0,0,0,0,blocked_approval_requirements_failed,,,,truth_seed_independent_evidence_status,approval failed\n"
            "BR-20260425-122,WRITE_VIOLATION,approve_for_future_truth_intake,positive_truth_candidate,0,0,0,0,0,1,0,1,1,0,0,0,validated_future_truth_intake_candidate,,,,,write violation\n",
            encoding="utf-8",
        )
        issues.write_text(
            "owner_branch,trial_event_id,issue_type,field,observed_value,expected_policy\n"
            "BR-20260425-122,FAILED_APPROVE,approval_requirement_failed,truth_seed_independent_evidence_status,single_source_only,required_for_approve_for_future_truth_intake\n"
            "BR-20260425-122,WRITE_VIOLATION,approval_flag_violation,canonical_truth_write_allowed,1,must_remain_0_before_explicit_truth_intake_branch\n",
            encoding="utf-8",
        )

        proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.py",
                "--repo-root",
                str(repo_root),
                "--validation",
                str(validation),
                "--issues",
                str(issues),
                "--output-dir",
                str(output_dir),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["source_decision_rows"] == 5, payload)
        assert_true(payload["source_valid_decision_rows"] == 4, payload)
        assert_true(payload["source_validation_failed_rows"] == 1, payload)
        assert_true(payload["source_future_truth_intake_candidate_rows"] == 2, payload)
        assert_true(payload["candidate_package_rows"] == 1, payload)
        assert_true(payload["blocked_before_candidate_package_rows"] == 4, payload)
        assert_true(payload["source_issue_rows"] == 2, payload)
        assert_true(payload["source_write_flag_violation_rows"] == 1, payload)
        assert_true(payload["canonical_truth_write_allowed_sum"] == 0, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)

        candidate_df = pd.read_csv(payload["outputs"]["candidate_package"], encoding="utf-8-sig")
        blocked_df = pd.read_csv(payload["outputs"]["blocked"], encoding="utf-8-sig")
        assert_true(candidate_df["trial_event_id"].tolist() == ["CANDIDATE_OK"], candidate_df.to_dict("records"))
        assert_true(set(blocked_df["trial_event_id"].tolist()) == {"REJECT_OK", "DEFER_OK", "FAILED_APPROVE", "WRITE_VIOLATION"}, blocked_df.to_dict("records"))
        assert_true("source_write_flag_violation" in set(blocked_df["blocker_reason"].tolist()), blocked_df.to_dict("records"))

        print(
            json.dumps(
                {
                    "smoke": "ok",
                    "candidate_package_rows": 1,
                    "blocked_before_candidate_package_rows": 4,
                    "source_write_flag_violation_rows": 1,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
