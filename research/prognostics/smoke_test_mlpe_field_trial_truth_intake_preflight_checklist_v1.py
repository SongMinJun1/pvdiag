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
    with tempfile.TemporaryDirectory(prefix="mlpe_truth_intake_preflight_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        candidate_package = tmp / "candidate_package.csv"
        blocked = tmp / "blocked.csv"
        output_dir = tmp / "preflight"

        candidate_package.write_text(
            "owner_branch,trial_event_id,truth_seed_future_truth_intake_candidate_status,truth_candidate_role,truth_seed_reviewer_decision,decision_validation_bucket,source_issue_count,canonical_truth_write_allowed,truth_intake_allowed,threshold_patch_allowed,engine_patch_allowed,source_validation_path,source_issues_path,candidate_package_next_action\n"
            "BR-20260425-123,CANDIDATE_OK,sidecar_future_truth_intake_candidate,positive_truth_candidate,approve_for_future_truth_intake,validated_future_truth_intake_candidate,0,0,0,0,0,/tmp/validation.csv,/tmp/issues.csv,ok\n"
            "BR-20260425-123,CANDIDATE_BAD_WRITE,sidecar_future_truth_intake_candidate,positive_truth_candidate,approve_for_future_truth_intake,validated_future_truth_intake_candidate,1,1,0,0,0,/tmp/validation.csv,/tmp/issues.csv,bad write flag\n",
            encoding="utf-8",
        )
        blocked.write_text(
            "owner_branch,trial_event_id,truth_seed_future_truth_intake_candidate_status,truth_candidate_role,truth_seed_reviewer_decision,decision_validation_bucket,blocker_reason,source_issue_count,source_validation_failed_flag,source_future_truth_intake_candidate_flag,source_write_flag_violation_flag,source_validation_path,source_issues_path,blocked_next_action\n"
            "BR-20260425-123,REJECTED,blocked_before_future_truth_intake_package,negative_truth_candidate,reject_not_truth_seed,validated_reject_not_truth_seed,not_approved_for_future_truth_intake,0,0,0,0,/tmp/validation.csv,/tmp/issues.csv,rejected\n",
            encoding="utf-8",
        )

        proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_truth_intake_preflight_checklist_v1.py",
                "--repo-root",
                str(repo_root),
                "--candidate-package",
                str(candidate_package),
                "--blocked",
                str(blocked),
                "--output-dir",
                str(output_dir),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["source_candidate_package_rows"] == 2, payload)
        assert_true(payload["source_blocked_rows"] == 1, payload)
        assert_true(payload["truth_intake_preflight_rows"] == 1, payload)
        assert_true(payload["preflight_checklist_rows"] == 6, payload)
        assert_true(payload["preflight_unchecked_rows"] == 6, payload)
        assert_true(payload["truth_intake_preflight_ready_rows"] == 0, payload)
        assert_true(payload["blocked_before_preflight_rows"] == 2, payload)
        assert_true(payload["canonical_truth_write_allowed_sum"] == 0, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)

        preflight_df = pd.read_csv(payload["outputs"]["preflight"], encoding="utf-8-sig")
        checklist_df = pd.read_csv(payload["outputs"]["checklist"], encoding="utf-8-sig")
        blocked_df = pd.read_csv(payload["outputs"]["blocked"], encoding="utf-8-sig")
        assert_true(preflight_df["trial_event_id"].tolist() == ["CANDIDATE_OK"], preflight_df.to_dict("records"))
        assert_true(checklist_df["trial_event_id"].tolist() == ["CANDIDATE_OK"] * 6, checklist_df.to_dict("records"))
        assert_true(set(blocked_df["trial_event_id"].tolist()) == {"CANDIDATE_BAD_WRITE", "REJECTED"}, blocked_df.to_dict("records"))
        assert_true("source_candidate_write_flag_violation" in set(blocked_df["blocker_reason"].tolist()), blocked_df.to_dict("records"))

        print(
            json.dumps(
                {
                    "smoke": "ok",
                    "truth_intake_preflight_rows": 1,
                    "preflight_checklist_rows": 6,
                    "blocked_before_preflight_rows": 2,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
