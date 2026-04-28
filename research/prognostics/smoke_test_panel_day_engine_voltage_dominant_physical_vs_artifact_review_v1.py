#!/usr/bin/env python3
from __future__ import annotations

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
    print("smoke ok: panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1")


if __name__ == "__main__":
    main()
