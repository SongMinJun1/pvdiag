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
    with tempfile.TemporaryDirectory(prefix="mlpe_real_label_intake_runbook_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        packet = tmp / "packet.csv"
        schema_dir = tmp / "schema"
        label_input = tmp / "real_labels.csv"
        output_dir = tmp / "runbook"

        packet.write_text(
            "trial_event_id,packet_status,source_preflight_bucket\n"
            "POS,ready_for_final_adjudication_packet,ready_for_readiness_handoff_rerun\n"
            "NEG,ready_for_final_adjudication_packet,ready_for_readiness_handoff_rerun\n"
            "PROB,ready_for_final_adjudication_packet,ready_for_readiness_handoff_rerun\n",
            encoding="utf-8",
        )
        schema_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_final_label_intake_schema_v1.py",
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

        label_input.write_text(
            "owner_branch,trial_event_id,packet_status,source_preflight_bucket,reviewer_final_fault_family,reviewer_final_fault_subtype,reviewer_truth_confidence,reviewer_common_cause_clearance,reviewer_measurement_artifact_clearance,reviewer_label_source,reviewer,reviewed_at,reviewer_notes,truth_intake_allowed,threshold_patch_allowed,engine_patch_allowed\n"
            "BR-20260425-115,POS,ready_for_final_adjudication_packet,ready_for_readiness_handoff_rerun,panel_surface_environment_fault,partial_shading,confirmed_observed,cleared_panel_local,cleared_physical,field_inspection,reviewer_a,2026-04-25T00:00:00Z,positive,0,0,0\n"
            "BR-20260425-115,NEG,ready_for_final_adjudication_packet,ready_for_readiness_handoff_rerun,normal,normal_clear_day_baseline,negative_control,cleared_panel_local,cleared_physical,field_inspection,reviewer_b,2026-04-25T00:00:00Z,negative,0,0,0\n"
            "BR-20260425-115,PROB,ready_for_final_adjudication_packet,ready_for_readiness_handoff_rerun,panel_surface_environment_fault,partial_shading,probable,cleared_panel_local,cleared_physical,manual_expert_review,reviewer_c,2026-04-25T00:00:00Z,probable,0,0,0\n",
            encoding="utf-8",
        )

        proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_real_label_intake_runbook_v1.py",
                "--repo-root",
                str(repo_root),
                "--label-input",
                str(label_input),
                "--schema",
                str(schema_dir / "mlpe_field_trial_final_label_intake_schema_v1.csv"),
                "--allowed-values",
                str(schema_dir / "mlpe_field_trial_final_label_allowed_values_v1.csv"),
                "--output-dir",
                str(output_dir),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["fixture_mismatch_rows"] == 0, payload)
        assert_true(payload["label_rows"] == 3, payload)
        assert_true(payload["valid_label_rows"] == 3, payload)
        assert_true(payload["validation_blocked_rows"] == 0, payload)
        assert_true(payload["truth_gate_ready_rows"] == 2, payload)
        assert_true(payload["truth_gate_blocked_rows"] == 1, payload)
        assert_true(payload["truth_seed_review_candidate_rows"] == 2, payload)
        assert_true(payload["hard_stop_rows"] == 0, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)

        explicit_artifact = json.loads(
            (output_dir / "mlpe_field_trial_real_label_intake_runbook_v1.json").read_text(encoding="utf-8")
        )
        explicit_note = (output_dir / "mlpe_field_trial_real_label_intake_runbook_note_v1.md").read_text(
            encoding="utf-8"
        )
        assert_true(explicit_artifact["input_resolution_sources"]["label_input"] == "explicit_cli", explicit_artifact)
        assert_true("real-label runbook input manifest: `not provided`" in explicit_note, explicit_note)
        assert_true("`label_input`: `explicit_cli`" in explicit_note, explicit_note)

        manifest_path = tmp / "real_label_runbook_inputs.json"
        manifest_path.write_text(
            json.dumps(
                {"inputs": {"label_input": str(label_input)}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_output_dir = tmp / "manifest_runbook"
        manifest_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_real_label_intake_runbook_v1.py",
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(manifest_path),
                "--schema",
                str(schema_dir / "mlpe_field_trial_final_label_intake_schema_v1.csv"),
                "--allowed-values",
                str(schema_dir / "mlpe_field_trial_final_label_allowed_values_v1.csv"),
                "--output-dir",
                str(manifest_output_dir),
            ],
            repo_root,
        )
        assert_true(manifest_proc.returncode == 0, manifest_proc.stderr or manifest_proc.stdout)
        manifest_payload = json.loads(manifest_proc.stdout)
        manifest_artifact = json.loads(
            (manifest_output_dir / "mlpe_field_trial_real_label_intake_runbook_v1.json").read_text(encoding="utf-8")
        )
        manifest_note = (
            manifest_output_dir / "mlpe_field_trial_real_label_intake_runbook_note_v1.md"
        ).read_text(encoding="utf-8")
        validator_artifact = json.loads(
            (
                manifest_output_dir
                / "br116_real_label_validation"
                / "mlpe_field_trial_final_label_validation_v1.json"
            ).read_text(encoding="utf-8")
        )
        gate_artifact = json.loads(
            (
                manifest_output_dir
                / "br117_label_to_truth_gate"
                / "mlpe_field_trial_label_to_truth_gate_v1.json"
            ).read_text(encoding="utf-8")
        )
        assert_true(
            manifest_payload["truth_seed_review_candidate_rows"] == payload["truth_seed_review_candidate_rows"],
            manifest_payload,
        )
        assert_true(manifest_artifact["input_resolution_sources"]["label_input"] == "input_manifest", manifest_artifact)
        assert_true(validator_artifact["input_resolution_sources"]["label_input"] == "input_manifest", validator_artifact)
        assert_true(gate_artifact["input_resolution_sources"]["label_input"] == "input_manifest", gate_artifact)
        assert_true(f"real-label runbook input manifest: `{manifest_path}`" in manifest_note, manifest_note)
        assert_true("`label_input`: `input_manifest`" in manifest_note, manifest_note)

        bad_manifest_path = tmp / "bad_real_label_runbook_inputs.json"
        bad_manifest_path.write_text(
            json.dumps(
                {"inputs": {"label_input": str(tmp / "missing_label_input.csv")}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_real_label_intake_runbook_v1.py",
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(bad_manifest_path),
                "--label-input",
                str(label_input),
                "--schema",
                str(schema_dir / "mlpe_field_trial_final_label_intake_schema_v1.csv"),
                "--allowed-values",
                str(schema_dir / "mlpe_field_trial_final_label_allowed_values_v1.csv"),
                "--output-dir",
                str(tmp / "override_runbook"),
            ],
            repo_root,
        )
        assert_true(override_proc.returncode == 0, override_proc.stderr or override_proc.stdout)
        override_payload = json.loads(override_proc.stdout)
        assert_true(override_payload["input_resolution_sources"]["label_input"] == "explicit_cli", override_payload)

        missing_key_manifest = tmp / "missing_key_real_label_runbook_inputs.json"
        missing_key_manifest.write_text(json.dumps({"inputs": {}}, indent=2) + "\n", encoding="utf-8")
        missing_key_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_real_label_intake_runbook_v1.py",
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(missing_key_manifest),
                "--schema",
                str(schema_dir / "mlpe_field_trial_final_label_intake_schema_v1.csv"),
                "--allowed-values",
                str(schema_dir / "mlpe_field_trial_final_label_allowed_values_v1.csv"),
                "--output-dir",
                str(tmp / "missing_key_runbook"),
            ],
            repo_root,
        )
        assert_true(missing_key_proc.returncode != 0, "missing-key manifest unexpectedly passed")
        assert_true(
            "missing `label_input`" in (missing_key_proc.stderr + missing_key_proc.stdout),
            missing_key_proc.stderr,
        )
        print(json.dumps({"smoke": "ok", "truth_seed_review_candidate_rows": 2, "truth_gate_blocked_rows": 1}, ensure_ascii=False))


if __name__ == "__main__":
    main()
