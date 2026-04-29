#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def write_gap_review_fixture(path: Path) -> None:
    columns = [
        "site",
        "panel_id",
        "source_search_status",
        "recovery_bucket",
        "synchrony_bucket",
        "anchor_dates",
        "raw_candidate_dates",
        "nearest_raw_candidate_date",
        "nearest_anchor_date",
        "min_abs_gap_days",
        "gap_direction",
        "date_alignment_gap_type",
        "raw_candidate_row_count",
        "raw_signal_row_count",
        "raw_recovery_row_count",
        "raw_pre_ews_row_count",
        "raw_prefault_B_effective_row_count",
        "raw_fault_like_row_count",
        "raw_final_fault_row_count",
        "raw_critical_fault_row_count",
        "raw_re_drop_row_count",
        "raw_common_cause_row_count",
        "signal_basis_type",
        "raw_audit_status_ko",
        "raw_final_status_ko",
        "raw_audit_anom_subtype",
        "raw_audit_critical_source",
        "raw_heuristic_row_present_flag",
        "any_operator_report_row_present_flag",
        "report_attachment_gap_type",
        "heuristic_attachment_gap_type",
        "engine_patch_candidate_flag",
        "report_patch_candidate_flag",
        "review_note",
    ]
    row = {
        "site": "fixture_site",
        "panel_id": "P001",
        "source_search_status": "fixture",
        "recovery_bucket": "recovery_only",
        "synchrony_bucket": "local",
        "anchor_dates": "2026-01-02",
        "raw_candidate_dates": "2026-01-01",
        "nearest_raw_candidate_date": "2026-01-01",
        "nearest_anchor_date": "2026-01-02",
        "min_abs_gap_days": 1,
        "gap_direction": "before_anchor",
        "date_alignment_gap_type": "near_anchor_1_3d",
        "raw_candidate_row_count": 1,
        "raw_signal_row_count": 1,
        "raw_recovery_row_count": 1,
        "raw_pre_ews_row_count": 1,
        "raw_prefault_B_effective_row_count": 0,
        "raw_fault_like_row_count": 0,
        "raw_final_fault_row_count": 0,
        "raw_critical_fault_row_count": 0,
        "raw_re_drop_row_count": 0,
        "raw_common_cause_row_count": 0,
        "signal_basis_type": "fixture_shape",
        "raw_audit_status_ko": "미확정",
        "raw_final_status_ko": "미확정",
        "raw_audit_anom_subtype": "",
        "raw_audit_critical_source": "",
        "raw_heuristic_row_present_flag": 1,
        "any_operator_report_row_present_flag": 0,
        "report_attachment_gap_type": "near_anchor",
        "heuristic_attachment_gap_type": "expected_absent_non_fault_status_gate",
        "engine_patch_candidate_flag": 0,
        "report_patch_candidate_flag": 1,
        "review_note": "fixture",
    }
    pd.DataFrame([row], columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def write_packet_fixture(path: Path) -> None:
    rows: list[dict[str, object]] = []
    for idx in range(1, 12):
        first_bucket = idx <= 5
        rows.append(
            {
                "packet_case_id": f"fixture-{idx:03d}",
                "site": "fixture_site",
                "panel_id": f"P{idx:03d}",
                "packet_bucket": (
                    "non_target_hard_same_day_fault_family_seed"
                    if first_bucket
                    else "sensor_feedback_hard_same_day_ambiguity_pressure"
                ),
                "counterexample_bucket": "fault_family_boundary_pressure" if first_bucket else "mlpe_ambiguous",
                "source_closure_class": "fixture",
                "evidence_grade": "fixture",
                "raw_top1_ko": "fixture",
                "same_day_fault_like_row_count": 1,
                "same_day_final_fault_row_count": 1,
                "same_day_common_cause_row_count": 0,
                "target_exact_closure_candidate_flag": 0,
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
                "expected_reading": "regression pressure only",
                "prohibited_overgeneralization": "do not promote",
                "regression_assertion": "must stay non-promoting",
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def run_cmd(cmd: list[str], repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True, check=False)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    sidecar = repo_root / "research/prognostics/build_panel_day_engine_non_fault_morphology_observation_sidecar_v1.py"
    gate = repo_root / "research/prognostics/check_panel_day_engine_fault_family_regression_prepatch_gate_v1.py"
    with tempfile.TemporaryDirectory(prefix="static_artifact_contract_closure_inputs_") as tmpdir:
        root = Path(tmpdir)
        gap_input = root / "gap_review.csv"
        packet_input = root / "packet.csv"
        manifest = root / "inputs.json"
        write_gap_review_fixture(gap_input)
        write_packet_fixture(packet_input)
        manifest.write_text(
            json.dumps(
                {
                    "inputs": {
                        "gap_review_input": str(gap_input),
                        "packet_input": str(packet_input),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        sidecar_out = root / "sidecar_manifest"
        proc = run_cmd(
            [
                sys.executable,
                str(sidecar),
                "--input-manifest",
                str(manifest),
                "--output-dir",
                str(sidecar_out),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        sidecar_detail = pd.read_csv(
            sidecar_out / "panel_day_engine_non_fault_morphology_observation_sidecar_v1.csv"
        )
        sidecar_note = (
            sidecar_out / "panel_day_engine_non_fault_morphology_observation_sidecar_note_v1.md"
        ).read_text(encoding="utf-8")
        assert_true(len(sidecar_detail) == 1, sidecar_detail.to_dict("records"))
        assert_true("`gap_review_input`: `input_manifest`" in sidecar_note, sidecar_note)

        gate_out = root / "gate_manifest"
        proc = run_cmd(
            [
                sys.executable,
                str(gate),
                "--input-manifest",
                str(manifest),
                "--output-dir",
                str(gate_out),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        gate_summary = pd.read_csv(
            gate_out / "panel_day_engine_fault_family_regression_prepatch_gate_summary_v1.csv"
        )
        assert_true(gate_summary.iloc[0]["overall_status"] == "pass", gate_summary.to_dict("records"))

    print("smoke ok: static_artifact_contract_closure_inputs_v1")


if __name__ == "__main__":
    main()
