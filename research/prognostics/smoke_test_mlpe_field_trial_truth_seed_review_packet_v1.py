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
    with tempfile.TemporaryDirectory(prefix="mlpe_truth_seed_review_packet_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        packet = tmp / "packet.csv"
        schema_dir = tmp / "schema"
        label_input = tmp / "real_labels.csv"
        runbook_dir = tmp / "runbook"
        output_dir = tmp / "truth_seed_review_packet"

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

        runbook_proc = run(
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
                str(runbook_dir),
            ],
            repo_root,
        )
        assert_true(runbook_proc.returncode == 0, runbook_proc.stderr or runbook_proc.stdout)

        proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_truth_seed_review_packet_v1.py",
                "--repo-root",
                str(repo_root),
                "--runbook-dir",
                str(runbook_dir),
                "--output-dir",
                str(output_dir),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["fixture_mismatch_rows"] == 0, payload)
        assert_true(payload["source_gate_rows"] == 3, payload)
        assert_true(payload["source_truth_gate_ready_rows"] == 2, payload)
        assert_true(payload["source_truth_gate_blocked_rows"] == 1, payload)
        assert_true(payload["truth_seed_review_packet_rows"] == 2, payload)
        assert_true(payload["positive_truth_seed_review_rows"] == 1, payload)
        assert_true(payload["negative_truth_seed_review_rows"] == 1, payload)
        assert_true(payload["blocked_before_truth_seed_review_rows"] == 1, payload)
        assert_true(payload["canonical_truth_write_allowed_sum"] == 0, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)
        print(json.dumps({"smoke": "ok", "packet_rows": 2, "blocked_rows": 1}, ensure_ascii=False))


if __name__ == "__main__":
    main()
