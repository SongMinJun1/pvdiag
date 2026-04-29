#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_local_morphology_family_shape_review_v1.csv"
SUMMARY_NAME = "panel_day_engine_local_morphology_family_shape_review_summary_v1.csv"
NOTE_NAME = "panel_day_engine_local_morphology_family_shape_review_note_v1.md"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_panel_day_engine_local_morphology_family_shape_review_v1.py"
    with tempfile.TemporaryDirectory(prefix="local_morphology_shape_review_") as tmp_dir:
        root = Path(tmp_dir)
        packet = root / "packet.csv"
        data_root = root / "data"
        out_dir = root / "out"
        write_text(
            packet,
            "\n".join(
                [
                    "candidate_case_id,site,panel_id,judgment_bucket,recovery_bucket,synchrony_bucket,max_co_drop_frac,candidate_evidence_axis_count",
                    "BR064-001,conalog,panel.recovery,local_morphology_family_candidate_review,re_drop_cycle,panel_local_or_weak_synchrony,0.05,1",
                    "BR064-002,conalog,panel.voltage,local_morphology_family_candidate_review,re_drop_cycle,panel_local_or_weak_synchrony,0.04,1",
                    "BR064-003,conalog,panel.diode,local_morphology_family_candidate_review,re_drop_cycle,panel_local_or_weak_synchrony,0.03,1",
                    "BR064-004,conalog,panel.common,hold_subgroup_or_breadth_context,re_drop_cycle,subgroup_synchrony_candidate,0.30,1",
                ]
            )
            + "\n",
        )
        write_text(
            data_root / "conalog" / "out" / "panel_day_core.csv",
            "\n".join(
                [
                    "date,panel_id,mid_ratio,mid_v_ratio,mid_i_ratio,co_drop_frac,fault_like_day,final_fault,critical_fault,degraded_candidate,event_A,re_drop,recovered_sustained,data_bad,subgroup_common_cause_candidate",
                    "2026-01-01,panel.recovery,0.99,1.00,0.99,0.01,false,false,false,false,false,true,true,false,false",
                    "2026-01-02,panel.recovery,0.98,1.00,0.98,0.02,false,false,false,false,false,true,true,false,false",
                    "2026-01-01,panel.voltage,0.65,0.50,1.00,0.01,false,false,true,false,true,false,false,false,false",
                    "2026-01-02,panel.voltage,0.68,0.55,1.02,0.01,false,false,true,false,true,false,false,false,false",
                    "2026-01-03,panel.voltage,0.70,0.60,1.01,0.01,false,false,true,false,true,false,false,false,false",
                    "2026-01-04,panel.voltage,0.66,0.52,0.99,0.01,false,false,true,false,true,false,false,false,false",
                    "2026-01-05,panel.voltage,0.69,0.58,1.01,0.01,false,false,true,false,true,false,false,false,false",
                    "2026-01-06,panel.voltage,0.67,0.54,1.03,0.01,false,false,true,false,true,false,false,false,false",
                    "2026-01-07,panel.voltage,0.71,0.56,1.00,0.01,false,false,true,false,true,false,false,false,false",
                    "2026-01-08,panel.voltage,0.72,0.57,1.02,0.01,false,false,true,false,true,false,false,false,false",
                    "2026-01-09,panel.voltage,0.70,0.53,1.01,0.01,false,false,true,false,true,false,false,false,false",
                    "2026-01-10,panel.voltage,0.69,0.51,1.02,0.01,false,false,true,false,true,false,false,false,false",
                    "2026-01-01,panel.diode,0.55,0.95,0.55,0.01,false,false,true,false,true,false,false,false,false",
                    "2026-01-02,panel.diode,0.54,0.96,0.54,0.01,false,false,true,false,true,false,false,false,false",
                ]
            )
            + "\n",
        )
        cmd = [
            "python3",
            str(script),
            "--packet-input",
            str(packet),
            "--data-root",
            str(data_root),
            "--output-dir",
            str(out_dir),
        ]
        result = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
        assert_true(result.returncode == 0, f"builder failed:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}")
        detail = pd.read_csv(out_dir / DETAIL_NAME, low_memory=False)
        summary = pd.read_csv(out_dir / SUMMARY_NAME, low_memory=False)
        note = (out_dir / NOTE_NAME).read_text(encoding="utf-8")
        assert_true(len(detail) == 3, f"unexpected local morphology rows: {len(detail)}")
        assert_true("recovery_recurrence_only_no_family_shape_hold" in set(detail["family_shape_judgment_bucket"]), detail)
        assert_true("voltage_dominant_hard_signal_review" in set(detail["family_shape_judgment_bucket"]), detail)
        assert_true("diode_substring_shape_review" in set(detail["family_shape_judgment_bucket"]), detail)
        assert_true(int(detail["operator_promotion_allowed_flag"].sum()) == 0, "promotion must stay zero")
        assert_true(int(detail["engine_patch_candidate_flag"].sum()) == 0, "engine patch must stay zero")
        assert_true(int(detail["two_axis_review_ready_flag"].sum()) == 2, "exactly two synthetic rows should be review-ready")
        assert_true(len(summary) == 3, f"unexpected summary rows: {len(summary)}")
        assert_true("engine patch candidate sum: `0`" in note, "note missing engine guardrail")
        assert_true("evidence input manifest: `not provided`" in note, "note missing no-manifest marker")
        assert_true("`packet_input`: `explicit_cli`" in note, "note missing explicit packet source")

        manifest = root / "local_shape_inputs.json"
        manifest.write_text(
            json.dumps({"inputs": {"packet_input": str(packet)}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest_out = root / "manifest_out"
        manifest_cmd = [
            "python3",
            str(script),
            "--input-manifest",
            str(manifest),
            "--data-root",
            str(data_root),
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
            manifest_detail["family_shape_judgment_bucket"].tolist()
            == detail["family_shape_judgment_bucket"].tolist(),
            "manifest shape buckets drifted",
        )
        assert_true(f"evidence input manifest: `{manifest}`" in manifest_note, "note missing manifest path")
        assert_true("`packet_input`: `input_manifest`" in manifest_note, "note missing manifest packet source")

        bad_manifest = root / "bad_local_shape_inputs.json"
        bad_manifest.write_text(
            json.dumps({"inputs": {"packet_input": str(root / "missing_packet.csv")}}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        override_out = root / "override_out"
        override_cmd = [
            "python3",
            str(script),
            "--packet-input",
            str(packet),
            "--data-root",
            str(data_root),
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
        assert_true("`packet_input`: `explicit_cli`" in override_note, "override packet source drifted")

        missing_key_manifest = root / "missing_key_local_shape_inputs.json"
        missing_key_manifest.write_text(json.dumps({"inputs": {}}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        missing_key_cmd = [
            "python3",
            str(script),
            "--input-manifest",
            str(missing_key_manifest),
            "--data-root",
            str(data_root),
            "--output-dir",
            str(root / "missing_key_out"),
        ]
        missing_key_result = subprocess.run(missing_key_cmd, cwd=repo_root, text=True, capture_output=True)
        assert_true(missing_key_result.returncode != 0, "missing-key manifest unexpectedly passed")
        assert_true(
            "missing `packet_input`" in (missing_key_result.stderr + missing_key_result.stdout),
            missing_key_result.stderr + missing_key_result.stdout,
        )

        empty_packet = root / "packet_no_local.csv"
        empty_out_dir = root / "out_empty"
        write_text(
            empty_packet,
            "\n".join(
                [
                    "candidate_case_id,site,panel_id,judgment_bucket,recovery_bucket,synchrony_bucket,max_co_drop_frac,candidate_evidence_axis_count",
                    "BR064-999,conalog,panel.common,hold_subgroup_or_breadth_context,re_drop_cycle,subgroup_synchrony_candidate,0.30,1",
                ]
            )
            + "\n",
        )
        empty_cmd = [
            "python3",
            str(script),
            "--packet-input",
            str(empty_packet),
            "--data-root",
            str(data_root),
            "--output-dir",
            str(empty_out_dir),
        ]
        empty_result = subprocess.run(empty_cmd, cwd=repo_root, text=True, capture_output=True)
        assert_true(
            empty_result.returncode == 0,
            f"empty builder failed:\nSTDOUT={empty_result.stdout}\nSTDERR={empty_result.stderr}",
        )
        empty_detail = pd.read_csv(empty_out_dir / DETAIL_NAME, low_memory=False)
        empty_summary = pd.read_csv(empty_out_dir / SUMMARY_NAME, low_memory=False)
        empty_note = (empty_out_dir / NOTE_NAME).read_text(encoding="utf-8")
        assert_true(empty_detail.empty, f"empty detail should have no rows: {empty_detail}")
        assert_true(empty_summary.empty, f"empty summary should have no rows: {empty_summary}")
        assert_true("detail rows: `0`" in empty_note, "empty note missing zero-row guardrail")
    print("smoke ok: panel_day_engine_local_morphology_family_shape_review_v1")


if __name__ == "__main__":
    main()
