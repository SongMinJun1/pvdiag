#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="mlpe_truth_seed_decision_validator_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        packet = tmp / "packet.csv"
        schema_dir = tmp / "decision_schema"
        decision_input = tmp / "filled_decisions.csv"
        output_dir = tmp / "decision_validation"

        packet.write_text(
            "trial_event_id,truth_seed_review_packet_status,truth_candidate_role,reviewer_final_fault_family,reviewer_final_fault_subtype,reviewer_truth_confidence,reviewer_common_cause_clearance,reviewer_measurement_artifact_clearance,reviewer_label_source,truth_gate_bucket,canonical_truth_write_allowed,truth_intake_allowed,threshold_patch_allowed,engine_patch_allowed\n"
            "APPROVE_OK,ready_for_sidecar_truth_seed_review,positive_truth_candidate,panel_surface_environment_fault,partial_shading,confirmed_observed,cleared_panel_local,cleared_physical,field_inspection,truth_gate_ready_for_truth_intake_review,0,0,0,0\n"
            "APPROVE_WEAK,ready_for_sidecar_truth_seed_review,positive_truth_candidate,panel_surface_environment_fault,partial_shading,confirmed_observed,cleared_panel_local,cleared_physical,field_inspection,truth_gate_ready_for_truth_intake_review,0,0,0,0\n"
            "REJECT_OK,ready_for_sidecar_truth_seed_review,negative_truth_candidate,normal,normal_clear_day_baseline,negative_control,cleared_panel_local,cleared_physical,field_inspection,truth_gate_ready_for_truth_intake_review,0,0,0,0\n"
            "DEFER_OK,ready_for_sidecar_truth_seed_review,positive_truth_candidate,panel_surface_environment_fault,partial_shading,confirmed_observed,cleared_panel_local,cleared_physical,manual_expert_review,truth_gate_ready_for_truth_intake_review,0,0,0,0\n"
            "MISSING_REVIEWER,ready_for_sidecar_truth_seed_review,positive_truth_candidate,panel_surface_environment_fault,partial_shading,confirmed_observed,cleared_panel_local,cleared_physical,field_inspection,truth_gate_ready_for_truth_intake_review,0,0,0,0\n"
            "BAD_ALLOWED,ready_for_sidecar_truth_seed_review,positive_truth_candidate,panel_surface_environment_fault,partial_shading,confirmed_observed,cleared_panel_local,cleared_physical,field_inspection,truth_gate_ready_for_truth_intake_review,0,0,0,0\n"
            "BAD_APPROVAL,ready_for_sidecar_truth_seed_review,positive_truth_candidate,panel_surface_environment_fault,partial_shading,confirmed_observed,cleared_panel_local,cleared_physical,field_inspection,truth_gate_ready_for_truth_intake_review,0,0,0,0\n",
            encoding="utf-8",
        )
        schema_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.py",
                "--repo-root",
                str(repo_root),
                "--packet",
                str(packet),
                "--output-dir",
                str(schema_dir),
            ],
            repo_root,
        )
        assert_true(schema_proc.returncode == 0, schema_proc.stderr or schema_proc.stdout)

        decision_input.write_text(
            "owner_branch,trial_event_id,truth_seed_review_packet_status,truth_candidate_role,reviewer_final_fault_family,reviewer_final_fault_subtype,reviewer_truth_confidence,reviewer_common_cause_clearance,reviewer_measurement_artifact_clearance,reviewer_label_source,truth_gate_bucket,truth_seed_reviewer_decision,truth_seed_reviewer_confidence,truth_seed_independent_evidence_status,truth_seed_common_cause_final_clearance,truth_seed_measurement_artifact_final_clearance,truth_seed_counterexample_check_status,truth_seed_reviewer_decision_source,truth_seed_reviewer,truth_seed_reviewed_at,truth_seed_reviewer_notes,canonical_truth_write_allowed,truth_intake_allowed,threshold_patch_allowed,engine_patch_allowed\n"
            "BR-20260425-121,APPROVE_OK,ready_for_sidecar_truth_seed_review,positive_truth_candidate,panel_surface_environment_fault,partial_shading,confirmed_observed,cleared_panel_local,cleared_physical,field_inspection,truth_gate_ready_for_truth_intake_review,approve_for_future_truth_intake,confirmed,independent_evidence_confirmed,final_cleared_panel_local,final_cleared_physical,checked_no_counterexample,field_trial_packet_review,reviewer_a,2026-04-25T00:00:00Z,approve good,0,0,0,0\n"
            "BR-20260425-121,APPROVE_WEAK,ready_for_sidecar_truth_seed_review,positive_truth_candidate,panel_surface_environment_fault,partial_shading,confirmed_observed,cleared_panel_local,cleared_physical,field_inspection,truth_gate_ready_for_truth_intake_review,approve_for_future_truth_intake,confirmed,single_source_only,final_cleared_panel_local,final_cleared_physical,checked_no_counterexample,field_trial_packet_review,reviewer_b,2026-04-25T00:00:00Z,approve weak,0,0,0,0\n"
            "BR-20260425-121,REJECT_OK,ready_for_sidecar_truth_seed_review,negative_truth_candidate,normal,normal_clear_day_baseline,negative_control,cleared_panel_local,cleared_physical,field_inspection,truth_gate_ready_for_truth_intake_review,reject_not_truth_seed,ambiguous,not_confirmed,final_common_cause_risk,final_measurement_artifact_risk,counterexample_risk,expert_panel_review,reviewer_c,2026-04-25T00:00:00Z,reject ok,0,0,0,0\n"
            "BR-20260425-121,DEFER_OK,ready_for_sidecar_truth_seed_review,positive_truth_candidate,panel_surface_environment_fault,partial_shading,confirmed_observed,cleared_panel_local,cleared_physical,manual_expert_review,truth_gate_ready_for_truth_intake_review,defer_needs_more_evidence,probable,single_source_only,unknown,unknown,unknown,expert_panel_review,reviewer_d,2026-04-25T00:00:00Z,defer ok,0,0,0,0\n"
            "BR-20260425-121,MISSING_REVIEWER,ready_for_sidecar_truth_seed_review,positive_truth_candidate,panel_surface_environment_fault,partial_shading,confirmed_observed,cleared_panel_local,cleared_physical,field_inspection,truth_gate_ready_for_truth_intake_review,approve_for_future_truth_intake,confirmed,independent_evidence_confirmed,final_cleared_panel_local,final_cleared_physical,checked_no_counterexample,field_trial_packet_review,,2026-04-25T00:00:00Z,missing reviewer,0,0,0,0\n"
            "BR-20260425-121,BAD_ALLOWED,ready_for_sidecar_truth_seed_review,positive_truth_candidate,panel_surface_environment_fault,partial_shading,confirmed_observed,cleared_panel_local,cleared_physical,field_inspection,truth_gate_ready_for_truth_intake_review,ship_it,confirmed,independent_evidence_confirmed,final_cleared_panel_local,final_cleared_physical,checked_no_counterexample,field_trial_packet_review,reviewer_f,2026-04-25T00:00:00Z,bad allowed,0,0,0,0\n"
            "BR-20260425-121,BAD_APPROVAL,ready_for_sidecar_truth_seed_review,positive_truth_candidate,panel_surface_environment_fault,partial_shading,confirmed_observed,cleared_panel_local,cleared_physical,field_inspection,truth_gate_ready_for_truth_intake_review,approve_for_future_truth_intake,confirmed,independent_evidence_confirmed,final_cleared_panel_local,final_cleared_physical,checked_no_counterexample,field_trial_packet_review,reviewer_g,2026-04-25T00:00:00Z,bad approval,1,0,0,0\n",
            encoding="utf-8",
        )

        proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py",
                "--repo-root",
                str(repo_root),
                "--decision-input",
                str(decision_input),
                "--schema",
                str(schema_dir / "mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.csv"),
                "--allowed-values",
                str(schema_dir / "mlpe_field_trial_truth_seed_reviewer_decision_allowed_values_v1.csv"),
                "--output-dir",
                str(output_dir),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["decision_rows"] == 7, payload)
        assert_true(payload["valid_decision_rows"] == 3, payload)
        assert_true(payload["validation_failed_rows"] == 4, payload)
        assert_true(payload["future_truth_intake_candidate_rows"] == 1, payload)
        assert_true(payload["issue_rows"] == 5, payload)
        assert_true(payload["canonical_truth_write_allowed_sum"] == 0, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)

        explicit_artifact = json.loads(
            (
                output_dir / "mlpe_field_trial_truth_seed_reviewer_decision_validation_v1.json"
            ).read_text(encoding="utf-8")
        )
        explicit_note = (
            output_dir / "mlpe_field_trial_truth_seed_reviewer_decision_validation_note_v1.md"
        ).read_text(encoding="utf-8")
        assert_true(
            explicit_artifact["input_resolution_sources"]["decision_input"] == "explicit_cli",
            explicit_artifact,
        )
        assert_true(
            "truth-seed reviewer decision input manifest: `not provided`" in explicit_note,
            explicit_note,
        )
        assert_true("`decision_input`: `explicit_cli`" in explicit_note, explicit_note)

        manifest_path = tmp / "truth_seed_reviewer_decision_validator_inputs.json"
        manifest_path.write_text(
            json.dumps(
                {"inputs": {"decision_input": str(decision_input)}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_output_dir = tmp / "manifest_decision_validation"
        manifest_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py",
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(manifest_path),
                "--schema",
                str(schema_dir / "mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.csv"),
                "--allowed-values",
                str(schema_dir / "mlpe_field_trial_truth_seed_reviewer_decision_allowed_values_v1.csv"),
                "--output-dir",
                str(manifest_output_dir),
            ],
            repo_root,
        )
        assert_true(manifest_proc.returncode == 0, manifest_proc.stderr or manifest_proc.stdout)
        manifest_payload = json.loads(manifest_proc.stdout)
        manifest_artifact = json.loads(
            (
                manifest_output_dir / "mlpe_field_trial_truth_seed_reviewer_decision_validation_v1.json"
            ).read_text(encoding="utf-8")
        )
        manifest_note = (
            manifest_output_dir / "mlpe_field_trial_truth_seed_reviewer_decision_validation_note_v1.md"
        ).read_text(encoding="utf-8")
        assert_true(
            manifest_payload["future_truth_intake_candidate_rows"]
            == payload["future_truth_intake_candidate_rows"],
            manifest_payload,
        )
        assert_true(
            manifest_artifact["input_resolution_sources"]["decision_input"] == "input_manifest",
            manifest_artifact,
        )
        assert_true(
            f"truth-seed reviewer decision input manifest: `{manifest_path}`" in manifest_note,
            manifest_note,
        )
        assert_true("`decision_input`: `input_manifest`" in manifest_note, manifest_note)

        bad_manifest_path = tmp / "bad_truth_seed_reviewer_decision_validator_inputs.json"
        bad_manifest_path.write_text(
            json.dumps(
                {"inputs": {"decision_input": str(tmp / "missing_decision_input.csv")}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py",
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(bad_manifest_path),
                "--decision-input",
                str(decision_input),
                "--schema",
                str(schema_dir / "mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.csv"),
                "--allowed-values",
                str(schema_dir / "mlpe_field_trial_truth_seed_reviewer_decision_allowed_values_v1.csv"),
                "--output-dir",
                str(tmp / "override_decision_validation"),
            ],
            repo_root,
        )
        assert_true(override_proc.returncode == 0, override_proc.stderr or override_proc.stdout)
        override_payload = json.loads(override_proc.stdout)
        assert_true(
            override_payload["input_resolution_sources"]["decision_input"] == "explicit_cli",
            override_payload,
        )

        missing_key_manifest = tmp / "missing_key_truth_seed_reviewer_decision_validator_inputs.json"
        missing_key_manifest.write_text(json.dumps({"inputs": {}}, indent=2) + "\n", encoding="utf-8")
        missing_key_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py",
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(missing_key_manifest),
                "--schema",
                str(schema_dir / "mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.csv"),
                "--allowed-values",
                str(schema_dir / "mlpe_field_trial_truth_seed_reviewer_decision_allowed_values_v1.csv"),
                "--output-dir",
                str(tmp / "missing_key_decision_validation"),
            ],
            repo_root,
        )
        assert_true(missing_key_proc.returncode != 0, "missing-key manifest unexpectedly passed")
        assert_true(
            "missing `decision_input`" in (missing_key_proc.stderr + missing_key_proc.stdout),
            missing_key_proc.stderr,
        )
        print(
            json.dumps(
                {"smoke": "ok", "future_truth_intake_candidate_rows": 1, "validation_failed_rows": 4, "issue_rows": 5},
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
