#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

from mlpe_field_trial_chain_manifest_v1 import (
    DEFAULT_TRUTH_REPLAY_CHAIN_MANIFEST,
    resolve_manifest_artifact,
    resolve_truth_replay_chain_dependency,
)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def sidecar_rows(event_id: str) -> str:
    groups = [
        "materialization_precheck_ready",
        "common_cause_clearance_ready",
        "artifact_mlpe_control_clearance_ready",
        "sidecar_payload_identity",
        "sidecar_truth_label_payload",
        "source_evidence_provenance_attached",
        "write_boundary_locked",
        "reviewer_package_approval_note",
    ]
    header = (
        "trial_event_id,site,root_id,panel_id,event_date,package_group,required_flag,package_group_blocking_flag,"
        "sidecar_truth_package_status,sidecar_truth_package_id,sidecar_truth_label,sidecar_fault_family,"
        "sidecar_event_type,sidecar_onset_date,sidecar_fault_date,canonical_truth_write_allowed,"
        "truth_intake_allowed,threshold_patch_allowed,engine_patch_allowed\n"
    )
    body = ""
    for group in groups:
        body += (
            f"{event_id},ktc_ess,R1,P1,2026-04-25,{group},1,0,sidecar_truth_package_group_passed,"
            f"PKG-{event_id},confirmed_panel_fault,panel_physical_fault,abrupt_fault,2026-04-24,2026-04-25,0,0,0,0\n"
        )
    return header + body


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    sidecar = resolve_manifest_artifact(repo_root, "sidecar_truth_package", DEFAULT_TRUTH_REPLAY_CHAIN_MANIFEST)
    explicit = resolve_truth_replay_chain_dependency(
        repo_root,
        "explicit.csv",
        "sidecar_truth_package",
        DEFAULT_TRUTH_REPLAY_CHAIN_MANIFEST,
    )
    assert_true(sidecar.name == "mlpe_field_trial_sidecar_truth_package_dry_run_v1.csv", sidecar)
    assert_true(explicit == repo_root / "explicit.csv", explicit)

    with tempfile.TemporaryDirectory(prefix="mlpe_truth_replay_chain_manifest_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        sidecar_fixture = tmp / "sidecar.csv"
        manifest = tmp / "truth_replay_manifest.csv"
        scorecard_output = tmp / "scorecard"
        output_dir = tmp / "audit"

        sidecar_fixture.write_text(sidecar_rows("EV_POS"), encoding="utf-8")
        manifest.write_text(
            "artifact_key,path_kind,static_path,producer_script,producer_output_constant,artifact_name,description\n"
            f"sidecar_truth_package,file,{sidecar_fixture},,,,fixture sidecar package\n",
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                sys.executable,
                str(repo_root / "research/prognostics/build_mlpe_field_trial_truth_replay_scorecard_contract_v1.py"),
                "--repo-root",
                str(repo_root),
                "--truth-replay-chain-manifest",
                str(manifest),
                "--output-dir",
                str(scorecard_output),
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["events"] == 1, payload)
        assert_true(payload["scorecard_rows"] == 10, payload)
        assert_true(payload["performance_improvement_claim_allowed_sum"] == 0, payload)

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
        assert_true(counts.get("mlpe_upstream_generated_artifact_input", 0) == 0, counts)
        assert_true(counts.get("mlpe_chain_directory_bundle_input", 0) == 0, counts)
        assert_true(counts.get("mlpe_user_filled_input", 0) == 7, counts)

    print(json.dumps({"smoke": "ok", "remaining_upstream": 0, "remaining_chain_dir": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
