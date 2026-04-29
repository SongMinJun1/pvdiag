#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


CHECK_IDS = [
    "BR124-CHECK-001",
    "BR124-CHECK-002",
    "BR124-CHECK-003",
    "BR124-CHECK-004",
    "BR124-CHECK-005",
    "BR124-CHECK-006",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def preflight_row(event_id: str, canonical_allowed: int = 0) -> str:
    return (
        f"BR-20260425-124,{event_id},pending_checklist_completion,positive_truth_candidate,"
        "approve_for_future_truth_intake,sidecar_future_truth_intake_candidate,0,6,0,0,"
        f"{canonical_allowed},0,0,0,/tmp/candidate.csv,/tmp/blocked.csv,pending review\n"
    )


def checklist_rows(event_id: str, skip_check_id: str = "", fail_check_id: str = "") -> list[str]:
    rows = []
    for check_id in CHECK_IDS:
        if check_id == skip_check_id:
            continue
        status = "failed" if check_id == fail_check_id else "passed"
        passed_flag = 0 if check_id == fail_check_id else 1
        rows.append(
            f"BR-20260425-124,{event_id},{check_id},check_name,check_group,1,{status},{passed_flag},expected,note\n"
        )
    return rows


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="mlpe_preflight_review_validator_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        preflight = tmp / "preflight.csv"
        checklist = tmp / "reviewed_checklist.csv"
        output_dir = tmp / "validation"

        preflight.write_text(
            "owner_branch,trial_event_id,truth_intake_preflight_status,truth_candidate_role,truth_seed_reviewer_decision,source_candidate_status,source_issue_count,required_checklist_item_count,passed_checklist_item_count,truth_intake_preflight_ready_flag,canonical_truth_write_allowed,truth_intake_allowed,threshold_patch_allowed,engine_patch_allowed,source_candidate_package_path,source_blocked_path,preflight_next_action\n"
            + preflight_row("PASS_OK")
            + preflight_row("MISSING_CHECK")
            + preflight_row("FAILED_CHECK")
            + preflight_row("BAD_WRITE", canonical_allowed=1),
            encoding="utf-8",
        )
        checklist.write_text(
            "owner_branch,trial_event_id,check_id,check_name,check_group,required_for_truth_intake,check_status,check_passed_flag,expected_evidence_or_clearance,preflight_operator_note\n"
            + "".join(checklist_rows("PASS_OK"))
            + "".join(checklist_rows("MISSING_CHECK", skip_check_id="BR124-CHECK-006"))
            + "".join(checklist_rows("FAILED_CHECK", fail_check_id="BR124-CHECK-003"))
            + "".join(checklist_rows("BAD_WRITE")),
            encoding="utf-8",
        )

        proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py",
                "--repo-root",
                str(repo_root),
                "--preflight",
                str(preflight),
                "--reviewed-checklist",
                str(checklist),
                "--output-dir",
                str(output_dir),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["reviewed_preflight_rows"] == 4, payload)
        assert_true(payload["reviewed_preflight_all_checks_passed_rows"] == 1, payload)
        assert_true(payload["future_truth_materialization_precheck_candidate_rows"] == 1, payload)
        assert_true(payload["reviewed_preflight_validation_failed_rows"] == 3, payload)
        assert_true(payload["issue_rows"] == 3, payload)
        assert_true(payload["canonical_truth_write_allowed_sum"] == 0, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)

        validation_df = pd.read_csv(payload["outputs"]["validation"], encoding="utf-8-sig")
        buckets = dict(zip(validation_df["trial_event_id"], validation_df["review_validation_bucket"], strict=True))
        assert_true(buckets["PASS_OK"] == "reviewed_preflight_all_checks_passed", buckets)
        assert_true(buckets["MISSING_CHECK"] == "blocked_missing_required_check", buckets)
        assert_true(buckets["FAILED_CHECK"] == "blocked_required_check_not_passed", buckets)
        assert_true(buckets["BAD_WRITE"] == "blocked_source_write_flag_violation", buckets)

        explicit_artifact = json.loads(
            (
                output_dir / "mlpe_field_trial_truth_intake_preflight_review_validation_v1.json"
            ).read_text(encoding="utf-8")
        )
        explicit_note = (
            output_dir / "mlpe_field_trial_truth_intake_preflight_review_note_v1.md"
        ).read_text(encoding="utf-8")
        assert_true(
            explicit_artifact["input_resolution_sources"]["reviewed_checklist"] == "explicit_cli",
            explicit_artifact,
        )
        assert_true("reviewed preflight input manifest: `not provided`" in explicit_note, explicit_note)
        assert_true("`reviewed_checklist`: `explicit_cli`" in explicit_note, explicit_note)

        manifest_path = tmp / "preflight_review_validator_inputs.json"
        manifest_path.write_text(
            json.dumps(
                {"inputs": {"reviewed_checklist": str(checklist)}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_output_dir = tmp / "manifest_validation"
        manifest_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py",
                "--repo-root",
                str(repo_root),
                "--preflight",
                str(preflight),
                "--input-manifest",
                str(manifest_path),
                "--output-dir",
                str(manifest_output_dir),
            ],
            repo_root,
        )
        assert_true(manifest_proc.returncode == 0, manifest_proc.stderr or manifest_proc.stdout)
        manifest_payload = json.loads(manifest_proc.stdout)
        manifest_artifact = json.loads(
            (
                manifest_output_dir / "mlpe_field_trial_truth_intake_preflight_review_validation_v1.json"
            ).read_text(encoding="utf-8")
        )
        manifest_note = (
            manifest_output_dir / "mlpe_field_trial_truth_intake_preflight_review_note_v1.md"
        ).read_text(encoding="utf-8")
        assert_true(
            manifest_payload["future_truth_materialization_precheck_candidate_rows"]
            == payload["future_truth_materialization_precheck_candidate_rows"],
            manifest_payload,
        )
        assert_true(
            manifest_artifact["input_resolution_sources"]["reviewed_checklist"] == "input_manifest",
            manifest_artifact,
        )
        assert_true(f"reviewed preflight input manifest: `{manifest_path}`" in manifest_note, manifest_note)
        assert_true("`reviewed_checklist`: `input_manifest`" in manifest_note, manifest_note)

        bad_manifest_path = tmp / "bad_preflight_review_validator_inputs.json"
        bad_manifest_path.write_text(
            json.dumps(
                {"inputs": {"reviewed_checklist": str(tmp / "missing_reviewed_checklist.csv")}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py",
                "--repo-root",
                str(repo_root),
                "--preflight",
                str(preflight),
                "--input-manifest",
                str(bad_manifest_path),
                "--reviewed-checklist",
                str(checklist),
                "--output-dir",
                str(tmp / "override_validation"),
            ],
            repo_root,
        )
        assert_true(override_proc.returncode == 0, override_proc.stderr or override_proc.stdout)
        override_payload = json.loads(override_proc.stdout)
        assert_true(
            override_payload["input_resolution_sources"]["reviewed_checklist"] == "explicit_cli",
            override_payload,
        )

        missing_key_manifest = tmp / "missing_key_preflight_review_validator_inputs.json"
        missing_key_manifest.write_text(json.dumps({"inputs": {}}, indent=2) + "\n", encoding="utf-8")
        missing_key_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py",
                "--repo-root",
                str(repo_root),
                "--preflight",
                str(preflight),
                "--input-manifest",
                str(missing_key_manifest),
                "--output-dir",
                str(tmp / "missing_key_validation"),
            ],
            repo_root,
        )
        assert_true(missing_key_proc.returncode != 0, "missing-key manifest unexpectedly passed")
        assert_true(
            "missing `reviewed_checklist`" in (missing_key_proc.stderr + missing_key_proc.stdout),
            missing_key_proc.stderr,
        )

        print(
            json.dumps(
                {
                    "smoke": "ok",
                    "all_checks_passed_rows": 1,
                    "validation_failed_rows": 3,
                    "issue_rows": 3,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
