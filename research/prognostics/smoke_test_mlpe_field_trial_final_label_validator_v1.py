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
    with tempfile.TemporaryDirectory(prefix="mlpe_final_label_validator_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        packet = tmp / "packet.csv"
        schema_dir = tmp / "schema"
        label_input = tmp / "label_input.csv"
        output_dir = tmp / "validation"

        packet.write_text(
            "trial_event_id,packet_status,source_preflight_bucket\n"
            "VALID,ready_for_final_adjudication_packet,ready_for_readiness_handoff_rerun\n"
            "MISSING,ready_for_final_adjudication_packet,ready_for_readiness_handoff_rerun\n"
            "BAD_ALLOWED,ready_for_final_adjudication_packet,ready_for_readiness_handoff_rerun\n"
            "BAD_APPROVAL,ready_for_final_adjudication_packet,ready_for_readiness_handoff_rerun\n",
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
        template = schema_dir / "mlpe_field_trial_final_label_intake_template_v1.csv"
        schema = schema_dir / "mlpe_field_trial_final_label_intake_schema_v1.csv"
        allowed = schema_dir / "mlpe_field_trial_final_label_allowed_values_v1.csv"

        label_input.write_text(
            "owner_branch,trial_event_id,packet_status,source_preflight_bucket,reviewer_final_fault_family,reviewer_final_fault_subtype,reviewer_truth_confidence,reviewer_common_cause_clearance,reviewer_measurement_artifact_clearance,reviewer_label_source,reviewer,reviewed_at,reviewer_notes,truth_intake_allowed,threshold_patch_allowed,engine_patch_allowed\n"
            "BR-20260425-115,VALID,ready_for_final_adjudication_packet,ready_for_readiness_handoff_rerun,panel_surface_environment_fault,partial_shading,confirmed_injected,cleared_panel_local,cleared_physical,field_trial_injection_log,reviewer_a,2026-04-25T00:00:00Z,valid row,0,0,0\n"
            "BR-20260425-115,MISSING,ready_for_final_adjudication_packet,ready_for_readiness_handoff_rerun,panel_surface_environment_fault,,confirmed_injected,cleared_panel_local,cleared_physical,field_trial_injection_log,reviewer_b,2026-04-25T00:00:00Z,missing subtype,0,0,0\n"
            "BR-20260425-115,BAD_ALLOWED,ready_for_final_adjudication_packet,ready_for_readiness_handoff_rerun,panel_surface_environment_fault,partial_shading,not_allowed,cleared_panel_local,cleared_physical,field_trial_injection_log,reviewer_c,2026-04-25T00:00:00Z,bad allowed,0,0,0\n"
            "BR-20260425-115,BAD_APPROVAL,ready_for_final_adjudication_packet,ready_for_readiness_handoff_rerun,panel_surface_environment_fault,partial_shading,confirmed_injected,cleared_panel_local,cleared_physical,field_trial_injection_log,reviewer_d,2026-04-25T00:00:00Z,bad approval,1,0,0\n",
            encoding="utf-8",
        )
        assert_true(template.exists(), template)
        proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_final_label_validator_v1.py",
                "--repo-root",
                str(repo_root),
                "--label-input",
                str(label_input),
                "--schema",
                str(schema),
                "--allowed-values",
                str(allowed),
                "--output-dir",
                str(output_dir),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["label_rows"] == 4, payload)
        assert_true(payload["valid_label_rows"] == 1, payload)
        assert_true(payload["validation_failed_rows"] == 3, payload)
        assert_true(payload["truth_gate_candidate_rows"] == 1, payload)
        assert_true(payload["issue_rows"] >= 3, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)
        print(json.dumps({"smoke": "ok", "valid_label_rows": 1, "validation_failed_rows": 3}, ensure_ascii=False))


if __name__ == "__main__":
    main()
