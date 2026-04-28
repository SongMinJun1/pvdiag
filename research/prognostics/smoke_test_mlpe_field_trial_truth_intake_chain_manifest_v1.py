#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

from mlpe_field_trial_chain_manifest_v1 import (
    DEFAULT_TRUTH_INTAKE_CHAIN_MANIFEST,
    resolve_manifest_artifact,
    resolve_truth_intake_chain_dependency,
)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    packet = resolve_manifest_artifact(repo_root, "truth_seed_review_packet", DEFAULT_TRUTH_INTAKE_CHAIN_MANIFEST)
    runbook_dir = resolve_manifest_artifact(repo_root, "real_label_intake_runbook_dir", DEFAULT_TRUTH_INTAKE_CHAIN_MANIFEST)
    explicit = resolve_truth_intake_chain_dependency(
        repo_root,
        "explicit.csv",
        "truth_seed_review_packet",
        DEFAULT_TRUTH_INTAKE_CHAIN_MANIFEST,
    )
    assert_true(packet.name == "mlpe_field_trial_truth_seed_review_packet_v1.csv", packet)
    assert_true(runbook_dir.name == "mlpe_field_trial_real_label_intake_runbook_br119_check", runbook_dir)
    assert_true(explicit == repo_root / "explicit.csv", explicit)

    with tempfile.TemporaryDirectory(prefix="mlpe_truth_intake_chain_manifest_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        candidate_package = tmp / "candidate_package.csv"
        blocked = tmp / "blocked.csv"
        manifest = tmp / "truth_intake_manifest.csv"
        preflight_output = tmp / "preflight"
        output_dir = tmp / "audit"

        candidate_package.write_text(
            "owner_branch,trial_event_id,truth_seed_future_truth_intake_candidate_status,truth_candidate_role,truth_seed_reviewer_decision,decision_validation_bucket,source_issue_count,canonical_truth_write_allowed,truth_intake_allowed,threshold_patch_allowed,engine_patch_allowed,source_validation_path,source_issues_path,candidate_package_next_action\n"
            "BR-20260425-123,CANDIDATE_OK,sidecar_future_truth_intake_candidate,positive_truth_candidate,approve_for_future_truth_intake,validated_future_truth_intake_candidate,0,0,0,0,0,/tmp/validation.csv,/tmp/issues.csv,ok\n",
            encoding="utf-8",
        )
        blocked.write_text(
            "owner_branch,trial_event_id,truth_seed_future_truth_intake_candidate_status,truth_candidate_role,truth_seed_reviewer_decision,decision_validation_bucket,blocker_reason,source_issue_count,source_validation_failed_flag,source_future_truth_intake_candidate_flag,source_write_flag_violation_flag,source_validation_path,source_issues_path,blocked_next_action\n",
            encoding="utf-8",
        )
        manifest.write_text(
            "artifact_key,path_kind,static_path,producer_script,producer_output_constant,artifact_name,description\n"
            f"future_truth_intake_candidate_package,file,{candidate_package},,,,fixture candidate package\n"
            f"future_truth_intake_blocked_rows,file,{blocked},,,,fixture blocked rows\n",
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                sys.executable,
                str(repo_root / "research/prognostics/build_mlpe_field_trial_truth_intake_preflight_checklist_v1.py"),
                "--repo-root",
                str(repo_root),
                "--truth-intake-chain-manifest",
                str(manifest),
                "--output-dir",
                str(preflight_output),
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["truth_intake_preflight_rows"] == 1, payload)
        assert_true(payload["preflight_checklist_rows"] == 6, payload)

        output_dir = tmp / "audit"
        proc = subprocess.run(
            [
                sys.executable,
                str(repo_root / "research/prognostics/build_repo_path_portability_audit_v1.py"),
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(output_dir),
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        detail = pd.read_csv(output_dir / "repo_path_portability_detail_v1.csv")
        counts = detail["dependency_contract"].value_counts(dropna=False).to_dict()
        assert_true(counts.get("mlpe_upstream_generated_artifact_input", 0) == 1, counts)
        assert_true(counts.get("mlpe_chain_directory_bundle_input", 0) == 0, counts)
        assert_true(counts.get("mlpe_user_filled_input", 0) == 7, counts)

    print(json.dumps({"smoke": "ok", "remaining_upstream": 1, "remaining_chain_dir": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
