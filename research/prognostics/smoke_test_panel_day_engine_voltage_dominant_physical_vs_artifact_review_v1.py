#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.csv"
SUMMARY_NAME = "panel_day_engine_voltage_dominant_physical_vs_artifact_review_summary_v1.csv"
NOTE_NAME = "panel_day_engine_voltage_dominant_physical_vs_artifact_review_note_v1.md"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def panel_day_row(day: int, panel_id: str, mid: float, mid_v: float, mid_i: float, *, data_bad: str = "false") -> str:
    return (
        f"2026-01-{day:02d},{panel_id},{mid},{mid_v},{mid_i},0.95,0.02,"
        "false,false,true,false,true,false,"
        f"{data_bad},false,false,false,true"
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py"
    with tempfile.TemporaryDirectory(prefix="voltage_dominant_artifact_review_") as tmp_dir:
        root = Path(tmp_dir)
        shape = root / "shape.csv"
        data_root = root / "data"
        out_dir = root / "out"
        write_text(
            shape,
            "\n".join(
                [
                    "shape_case_id,source_candidate_case_id,site,panel_id,family_shape_judgment_bucket",
                    "BR065-001,BR064-001,site_a,panel.physical,voltage_dominant_hard_signal_review",
                    "BR065-002,BR064-002,site_b,panel.artifact,voltage_dominant_hard_signal_review",
                    "BR065-003,BR064-003,site_a,panel.hold,recovery_recurrence_only_no_family_shape_hold",
                ]
            )
            + "\n",
        )
        rows_a = [
            "date,panel_id,mid_ratio,mid_v_ratio,mid_i_ratio,coverage,co_drop_frac,fault_like_day,final_fault,critical_fault,degraded_candidate,event_A,re_drop,data_bad,subgroup_common_cause_candidate,group_off_like,no_ref,v_ref_ok"
        ]
        for day in range(1, 11):
            rows_a.append(panel_day_row(day, "panel.physical", 0.60, 0.55, 1.02))
            rows_a.append(panel_day_row(day, "peer.normal.a", 1.00, 1.00, 1.00))
            rows_a.append(panel_day_row(day, "peer.normal.b", 1.00, 1.00, 1.00))
        write_text(data_root / "site_a" / "out" / "panel_day_core.csv", "\n".join(rows_a) + "\n")

        rows_b = [
            "date,panel_id,mid_ratio,mid_v_ratio,mid_i_ratio,coverage,co_drop_frac,fault_like_day,final_fault,critical_fault,degraded_candidate,event_A,re_drop,data_bad,subgroup_common_cause_candidate,group_off_like,no_ref,v_ref_ok"
        ]
        for day in range(1, 11):
            rows_b.append(panel_day_row(day, "panel.artifact", 0.60, 0.55, 1.02, data_bad="true"))
            rows_b.append(panel_day_row(day, "peer.artifact.a", 0.60, 0.55, 1.01, data_bad="true"))
            rows_b.append(panel_day_row(day, "peer.artifact.b", 0.60, 0.55, 1.01, data_bad="true"))
        write_text(data_root / "site_b" / "out" / "panel_day_core.csv", "\n".join(rows_b) + "\n")

        cmd = [
            "python3",
            str(script),
            "--shape-input",
            str(shape),
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
        assert_true(len(detail) == 2, f"unexpected voltage-dominant rows: {len(detail)}")
        assert_true("physical_leaning_voltage_axis_review" in set(detail["physical_vs_artifact_bucket"]), detail)
        assert_true("artifact_or_reference_risk_hold_review" in set(detail["physical_vs_artifact_bucket"]), detail)
        assert_true(int(detail["operator_promotion_allowed_flag"].sum()) == 0, "promotion must stay zero")
        assert_true(int(detail["engine_patch_candidate_flag"].sum()) == 0, "engine patch must stay zero")
        assert_true(int(detail["two_axis_review_ready_flag"].sum()) == 1, "only physical-leaning row is review-ready")
        assert_true(len(summary) == 2, f"unexpected summary rows: {len(summary)}")
        assert_true("engine patch candidate sum: `0`" in note, "note missing engine guardrail")
        assert_true("evidence input manifest: `not provided`" in note, "note missing no-manifest marker")
        assert_true("`shape_input`: `explicit_cli`" in note, "note missing explicit shape source")

        manifest = root / "voltage_artifact_inputs.json"
        manifest.write_text(
            json.dumps({"inputs": {"shape_input": str(shape)}}, ensure_ascii=False, indent=2) + "\n",
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
            manifest_detail["physical_vs_artifact_bucket"].tolist()
            == detail["physical_vs_artifact_bucket"].tolist(),
            "manifest buckets drifted",
        )
        assert_true(f"evidence input manifest: `{manifest}`" in manifest_note, "note missing manifest path")
        assert_true("`shape_input`: `input_manifest`" in manifest_note, "note missing manifest shape source")

        bad_manifest = root / "bad_voltage_artifact_inputs.json"
        bad_manifest.write_text(
            json.dumps({"inputs": {"shape_input": str(root / "missing_shape.csv")}}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        override_out = root / "override_out"
        override_cmd = [
            "python3",
            str(script),
            "--shape-input",
            str(shape),
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
        assert_true("`shape_input`: `explicit_cli`" in override_note, "override shape source drifted")

        missing_key_manifest = root / "missing_key_voltage_artifact_inputs.json"
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
            "missing `shape_input`" in (missing_key_result.stderr + missing_key_result.stdout),
            missing_key_result.stderr + missing_key_result.stdout,
        )
    print("smoke ok: panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1")


if __name__ == "__main__":
    main()
