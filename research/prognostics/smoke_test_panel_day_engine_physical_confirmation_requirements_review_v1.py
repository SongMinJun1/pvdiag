#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_physical_confirmation_requirements_review_v1.csv"
CHECKLIST_NAME = "panel_day_engine_physical_confirmation_requirements_checklist_v1.csv"
SUMMARY_NAME = "panel_day_engine_physical_confirmation_requirements_summary_v1.csv"
NOTE_NAME = "panel_day_engine_physical_confirmation_requirements_note_v1.md"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = (
        repo_root
        / "research"
        / "prognostics"
        / "build_panel_day_engine_physical_confirmation_requirements_review_v1.py"
    )
    with tempfile.TemporaryDirectory(prefix="physical_confirmation_requirements_") as tmp_dir:
        root = Path(tmp_dir)
        raw_review = root / "raw_review.csv"
        manual = root / "manual_field_evidence.csv"
        out_dir = root / "out"
        write_text(
            raw_review,
            "\n".join(
                [
                    "raw_support_case_id,source_review_case_id,source_shape_case_id,source_candidate_case_id,site,panel_id,raw_waveform_support_bucket,candidate_fault_family_label_ko,target_vdom_signal_days,raw_daily_support_frac,raw_median_v_ratio,raw_median_i_ratio,physical_support_score,raw_evidence_limitation_score",
                    "BR068-001,BR067-001,BR065-001,BR064-001,site_a,panel.ready,raw_waveform_physical_support_review,접속 불량·부분 개방 계열 검토,30,1.0,0.55,1.02,12,0",
                    "BR068-002,BR067-002,BR065-002,BR064-002,site_a,panel.gap,raw_waveform_physical_support_review,접속 불량·부분 개방 계열 검토,30,1.0,0.58,1.01,12,0",
                    "BR068-003,BR067-003,BR065-003,BR064-003,site_a,panel.skip,raw_waveform_support_insufficient_hold,unassigned_voltage_axis_review,3,0.0,0.0,0.0,1,5",
                ]
            )
            + "\n",
        )
        write_text(
            manual,
            "\n".join(
                [
                    "site,panel_id,evidence_type,description,expected_family,time_type,time_value,related_panel_count,evidence_strength,usable_for_exact_validation,note",
                    "site_a,panel.ready,iv_curve_capture,exact panel IV curve shows low voltage with current preserved,electrical,measured_time,2026-01-01,1,high,yes,artifact_excluded by field instrument",
                    "site_a,panel.ready,maintenance_inspection,exact panel connector inspection recorded partial open,electrical,inspection_time,2026-01-02,1,high,yes,repair ticket confirms connector issue",
                    "site_a,,module_output_drop,site-level output drop context only,electrical,detected_time,2026-01-01,5,medium,no,not exact-panel validation",
                ]
            )
            + "\n",
        )
        cmd = [
            "python3",
            str(script),
            "--raw-review-input",
            str(raw_review),
            "--manual-evidence-input",
            str(manual),
            "--output-dir",
            str(out_dir),
        ]
        result = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
        assert_true(result.returncode == 0, f"builder failed:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}")
        detail = pd.read_csv(out_dir / DETAIL_NAME, low_memory=False)
        checklist = pd.read_csv(out_dir / CHECKLIST_NAME, low_memory=False)
        summary = pd.read_csv(out_dir / SUMMARY_NAME, low_memory=False)
        note = (out_dir / NOTE_NAME).read_text(encoding="utf-8")

        assert_true(len(detail) == 2, f"unexpected detail rows: {len(detail)}")
        assert_true(len(checklist) == 10, f"unexpected checklist rows: {len(checklist)}")
        assert_true("independent_confirmation_packet_ready_review" in set(detail["confirmation_bucket"]), detail)
        assert_true("raw_supported_confirmation_gap_hold" in set(detail["confirmation_bucket"]), detail)
        assert_true(int(detail["operator_promotion_allowed_flag"].sum()) == 0, "promotion must stay zero")
        assert_true(int(detail["engine_patch_candidate_flag"].sum()) == 0, "engine patch must stay zero")
        assert_true(int(detail["threshold_patch_allowed_flag"].sum()) == 0, "threshold patch must stay zero")

        ready = detail.loc[detail["panel_id"].eq("panel.ready")].iloc[0]
        gap = detail.loc[detail["panel_id"].eq("panel.gap")].iloc[0]
        assert_true(int(ready["independent_confirmation_met_flag"]) == 1, ready)
        assert_true(int(ready["independent_confirmation_required_axes_met"]) == 2, ready)
        assert_true(int(gap["independent_confirmation_met_flag"]) == 0, gap)
        assert_true("direct_physical_measurement" in str(gap["required_next_evidence"]), gap)
        assert_true(len(summary) == 2, f"unexpected summary rows: {len(summary)}")
        assert_true("threshold patch allowed sum: `0`" in note, "note missing threshold guardrail")
        assert_true("evidence input manifest: `not provided`" in note, "note missing no-manifest marker")
        assert_true("`raw_review_input`: `explicit_cli`" in note, "note missing explicit raw review source")

        manifest = root / "physical_confirmation_inputs.json"
        manifest.write_text(
            json.dumps({"inputs": {"raw_review_input": str(raw_review)}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest_out = root / "manifest_out"
        manifest_cmd = [
            "python3",
            str(script),
            "--input-manifest",
            str(manifest),
            "--manual-evidence-input",
            str(manual),
            "--output-dir",
            str(manifest_out),
        ]
        manifest_result = subprocess.run(manifest_cmd, cwd=repo_root, text=True, capture_output=True)
        assert_true(
            manifest_result.returncode == 0,
            f"manifest builder failed:\nSTDOUT={manifest_result.stdout}\nSTDERR={manifest_result.stderr}",
        )
        manifest_detail = pd.read_csv(manifest_out / DETAIL_NAME, low_memory=False)
        manifest_note = (manifest_out / NOTE_NAME).read_text(encoding="utf-8")
        assert_true(
            manifest_detail["confirmation_bucket"].tolist()
            == detail["confirmation_bucket"].tolist(),
            "manifest buckets drifted",
        )
        assert_true(f"evidence input manifest: `{manifest}`" in manifest_note, "note missing manifest path")
        assert_true("`raw_review_input`: `input_manifest`" in manifest_note, "note missing manifest raw review source")

        bad_manifest = root / "bad_physical_confirmation_inputs.json"
        bad_manifest.write_text(
            json.dumps(
                {"inputs": {"raw_review_input": str(root / "missing_raw_review.csv")}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_out = root / "override_out"
        override_cmd = [
            "python3",
            str(script),
            "--raw-review-input",
            str(raw_review),
            "--manual-evidence-input",
            str(manual),
            "--input-manifest",
            str(bad_manifest),
            "--output-dir",
            str(override_out),
        ]
        override_result = subprocess.run(override_cmd, cwd=repo_root, text=True, capture_output=True)
        assert_true(
            override_result.returncode == 0,
            f"override builder failed:\nSTDOUT={override_result.stdout}\nSTDERR={override_result.stderr}",
        )
        override_note = (override_out / NOTE_NAME).read_text(encoding="utf-8")
        assert_true("`raw_review_input`: `explicit_cli`" in override_note, "override raw review source drifted")

        missing_key_manifest = root / "missing_key_physical_confirmation_inputs.json"
        missing_key_manifest.write_text(json.dumps({"inputs": {}}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        missing_key_cmd = [
            "python3",
            str(script),
            "--input-manifest",
            str(missing_key_manifest),
            "--manual-evidence-input",
            str(manual),
            "--output-dir",
            str(root / "missing_key_out"),
        ]
        missing_key_result = subprocess.run(missing_key_cmd, cwd=repo_root, text=True, capture_output=True)
        assert_true(missing_key_result.returncode != 0, "missing-key manifest unexpectedly passed")
        assert_true(
            "missing `raw_review_input`" in (missing_key_result.stderr + missing_key_result.stdout),
            missing_key_result.stderr + missing_key_result.stdout,
        )
    print("smoke ok: panel_day_engine_physical_confirmation_requirements_review_v1")


if __name__ == "__main__":
    main()
