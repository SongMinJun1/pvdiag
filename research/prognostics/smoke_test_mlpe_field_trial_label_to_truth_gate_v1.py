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
    with tempfile.TemporaryDirectory(prefix="mlpe_label_to_truth_gate_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        label_input = tmp / "labels.csv"
        validation = tmp / "validation.csv"
        output_dir = tmp / "gate"

        label_input.write_text(
            "trial_event_id,reviewer_final_fault_family,reviewer_final_fault_subtype,reviewer_truth_confidence,reviewer_common_cause_clearance,reviewer_measurement_artifact_clearance,reviewer_label_source,reviewer,reviewed_at,reviewer_notes\n"
            "POS,panel_surface_environment_fault,partial_shading,confirmed_injected,cleared_panel_local,cleared_physical,field_trial_injection_log,reviewer_a,2026-04-25T00:00:00Z,positive\n"
            "NEG,normal,normal_clear_day_baseline,negative_control,cleared_panel_local,cleared_physical,field_trial_injection_log,reviewer_b,2026-04-25T00:00:00Z,negative\n"
            "PROB,panel_surface_environment_fault,partial_shading,probable,cleared_panel_local,cleared_physical,manual_expert_review,reviewer_c,2026-04-25T00:00:00Z,probable\n"
            "COMMON,panel_surface_environment_fault,partial_shading,confirmed_injected,common_cause_suspected,cleared_physical,manual_expert_review,reviewer_d,2026-04-25T00:00:00Z,common\n"
            "ARTIFACT,panel_surface_environment_fault,partial_shading,confirmed_injected,cleared_panel_local,measurement_artifact_suspected,manual_expert_review,reviewer_e,2026-04-25T00:00:00Z,artifact\n"
            "INVALID,panel_surface_environment_fault,partial_shading,confirmed_injected,cleared_panel_local,cleared_physical,manual_expert_review,reviewer_f,2026-04-25T00:00:00Z,invalid\n",
            encoding="utf-8",
        )
        validation.write_text(
            "trial_event_id,reviewer_label_complete_flag,label_validation_failed_flag,truth_gate_candidate_flag,label_validation_bucket\n"
            "POS,1,0,1,label_valid_truth_gate_required\n"
            "NEG,1,0,1,label_valid_truth_gate_required\n"
            "PROB,1,0,1,label_valid_truth_gate_required\n"
            "COMMON,1,0,1,label_valid_truth_gate_required\n"
            "ARTIFACT,1,0,1,label_valid_truth_gate_required\n"
            "INVALID,0,1,0,blocked_required_fields_missing\n",
            encoding="utf-8",
        )
        proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_label_to_truth_gate_v1.py",
                "--repo-root",
                str(repo_root),
                "--label-input",
                str(label_input),
                "--label-validation",
                str(validation),
                "--output-dir",
                str(output_dir),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["label_rows"] == 6, payload)
        assert_true(payload["truth_gate_ready_rows"] == 2, payload)
        assert_true(payload["truth_gate_blocked_rows"] == 4, payload)
        assert_true(payload["positive_truth_candidate_rows"] == 1, payload)
        assert_true(payload["negative_truth_candidate_rows"] == 1, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)
        print(json.dumps({"smoke": "ok", "truth_gate_ready_rows": 2, "blocked_rows": 4}, ensure_ascii=False))


if __name__ == "__main__":
    main()
