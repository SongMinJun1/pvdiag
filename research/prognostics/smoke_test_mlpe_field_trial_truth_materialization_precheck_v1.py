#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


REQUIRED_GROUPS = [
    "source_trace",
    "independent_evidence",
    "common_cause_clearance",
    "measurement_artifact_clearance",
    "counterexample_clearance",
    "write_boundary_review",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def validation_row(event_id: str, passed: int, write_flag: int = 0) -> str:
    failed = 0 if passed else 1
    bucket = "reviewed_preflight_all_checks_passed" if passed else "blocked_required_check_not_passed"
    return (
        f"BR-20260425-125,{event_id},pending_checklist_completion,positive_truth_candidate,"
        f"approve_for_future_truth_intake,6,6,{6 if passed else 5},0,0,0,{0 if passed else 1},"
        f"{write_flag},0,{failed},{passed},{passed},{write_flag},0,0,0,{bucket},,,,,next\n"
    )


def evidence_rows(event_id: str, missing_group: str = "") -> list[str]:
    rows = []
    for group in REQUIRED_GROUPS:
        if group == missing_group:
            continue
        rows.append(f"{event_id},{group},/tmp/{event_id}_{group}.csv,1,1,1,ok\n")
    return rows


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="mlpe_materialization_precheck_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        validation = tmp / "review_validation.csv"
        review_issues = tmp / "review_issues.csv"
        evidence = tmp / "materialization_evidence_manifest.csv"
        output_dir = tmp / "precheck"

        validation.write_text(
            "owner_branch,trial_event_id,source_preflight_status,truth_candidate_role,truth_seed_reviewer_decision,required_checklist_item_count,observed_checklist_item_count,passed_checklist_item_count,duplicate_check_id_flag,missing_required_check_flag,invalid_check_status_flag,failed_required_check_flag,source_write_flag_violation_flag,source_preflight_status_invalid_flag,reviewed_preflight_validation_failed_flag,reviewed_preflight_all_checks_passed_flag,future_truth_materialization_precheck_candidate_flag,canonical_truth_write_allowed,truth_intake_allowed,threshold_patch_allowed,engine_patch_allowed,review_validation_bucket,missing_check_ids_csv,invalid_check_ids_csv,failed_check_ids_csv,duplicate_check_ids_csv,next_action\n"
            + validation_row("PASS_OK", 1)
            + validation_row("MISSING_EVIDENCE", 1)
            + validation_row("BAD_SOURCE", 0)
            + validation_row("BAD_WRITE", 1, write_flag=1),
            encoding="utf-8",
        )
        review_issues.write_text(
            "owner_branch,trial_event_id,issue_type,field,observed_value,expected_policy\n"
            "BR-20260425-125,BAD_SOURCE,required_check_not_passed,check_passed_flag,BR124-CHECK-003,passed\n",
            encoding="utf-8",
        )
        evidence.write_text(
            "trial_event_id,evidence_group,evidence_path,materialization_required_flag,evidence_exists_flag,reviewer_signed_flag,evidence_note\n"
            + "".join(evidence_rows("PASS_OK"))
            + "".join(evidence_rows("MISSING_EVIDENCE", missing_group="independent_evidence"))
            + "".join(evidence_rows("BAD_WRITE")),
            encoding="utf-8",
        )

        proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_truth_materialization_precheck_v1.py",
                "--repo-root",
                str(repo_root),
                "--review-validation",
                str(validation),
                "--review-issues",
                str(review_issues),
                "--materialization-evidence-manifest",
                str(evidence),
                "--output-dir",
                str(output_dir),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["source_review_validation_rows"] == 4, payload)
        assert_true(payload["materialization_precheck_passed_rows"] == 1, payload)
        assert_true(payload["future_sidecar_truth_package_candidate_rows"] == 1, payload)
        assert_true(payload["materialization_precheck_blocked_rows"] == 3, payload)
        assert_true(payload["materialization_issue_rows"] == 3, payload)
        assert_true(payload["canonical_truth_write_allowed_sum"] == 0, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)

        precheck_df = pd.read_csv(payload["outputs"]["precheck"], encoding="utf-8-sig")
        buckets = dict(zip(precheck_df["trial_event_id"], precheck_df["materialization_precheck_status"], strict=True))
        assert_true(buckets["PASS_OK"] == "materialization_precheck_passed_sidecar_candidate", buckets)
        assert_true(buckets["MISSING_EVIDENCE"] == "blocked_missing_or_failed_materialization_evidence", buckets)
        assert_true(buckets["BAD_SOURCE"] == "blocked_reviewed_preflight_failed", buckets)
        assert_true(buckets["BAD_WRITE"] == "blocked_source_write_flag_violation", buckets)

        print(
            json.dumps(
                {
                    "smoke": "ok",
                    "passed_rows": 1,
                    "blocked_rows": 3,
                    "issue_rows": 3,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
