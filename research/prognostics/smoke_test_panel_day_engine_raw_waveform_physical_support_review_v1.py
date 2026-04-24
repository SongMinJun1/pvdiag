#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_raw_waveform_physical_support_review_v1.csv"
SUMMARY_NAME = "panel_day_engine_raw_waveform_physical_support_review_summary_v1.csv"
NOTE_NAME = "panel_day_engine_raw_waveform_physical_support_review_note_v1.md"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def raw_row(ts: str, map_id: str, v_in: float, i_out: float, p: float) -> str:
    return f"{ts},panel,{map_id},{i_out},{v_in},{v_in},{p},0,0,25"


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_panel_day_engine_raw_waveform_physical_support_review_v1.py"
    with tempfile.TemporaryDirectory(prefix="raw_waveform_physical_support_") as tmp_dir:
        root = Path(tmp_dir)
        review = root / "review.csv"
        data_root = root / "data"
        out_dir = root / "out"
        write_text(
            review,
            "\n".join(
                [
                    "review_case_id,source_shape_case_id,source_candidate_case_id,site,panel_id,physical_vs_artifact_bucket",
                    "BR067-001,BR065-001,BR064-001,site_a,panel.support,physical_leaning_voltage_axis_review",
                    "BR067-002,BR065-002,BR064-002,site_a,panel.missing,physical_leaning_voltage_axis_review",
                    "BR067-003,BR065-003,BR064-003,site_a,panel.artifact,artifact_or_reference_risk_hold_review",
                ]
            )
            + "\n",
        )

        core_rows = [
            "date,panel_id,source_csv,mid_v_ratio,mid_i_ratio,fault_like_day,final_fault,critical_fault,degraded_candidate,event_A,re_drop"
        ]
        raw_header = "date_time,map_type,map_id,i_out (A),v_in (V),v_out (V),p (W),energy (Wh),cumulative_energy (Wh),die_temp (°C)"
        for day in range(1, 31):
            date = f"2026-01-{day:02d}"
            source = f"{date}-site-a-5m.csv"
            core_rows.append(f"{date},panel.support,{source},0.60,1.00,false,false,true,false,true,false")
            core_rows.append(f"{date},panel.missing,missing-{source},0.60,1.00,false,false,true,false,true,false")
            raw_rows = [raw_header]
            for idx in range(40):
                ts = f"{date} 12:{idx:02d}"
                raw_rows.append(raw_row(ts, "panel.support", 18.0, 3.0, 54.0))
                raw_rows.append(raw_row(ts, "peer.a", 30.0, 3.0, 90.0))
                raw_rows.append(raw_row(ts, "peer.b", 30.0, 3.0, 90.0))
            write_text(data_root / "site_a" / "raw" / source, "\n".join(raw_rows) + "\n")
        write_text(data_root / "site_a" / "out" / "panel_day_core.csv", "\n".join(core_rows) + "\n")

        cmd = [
            "python3",
            str(script),
            "--review-input",
            str(review),
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
        assert_true(len(detail) == 2, f"unexpected review rows: {len(detail)}")
        assert_true("raw_waveform_physical_support_review" in set(detail["raw_waveform_support_bucket"]), detail)
        assert_true("raw_waveform_support_insufficient_hold" in set(detail["raw_waveform_support_bucket"]), detail)
        assert_true(int(detail["operator_promotion_allowed_flag"].sum()) == 0, "promotion must stay zero")
        assert_true(int(detail["engine_patch_candidate_flag"].sum()) == 0, "engine patch must stay zero")
        support = detail.loc[detail["panel_id"].eq("panel.support")].iloc[0]
        assert_true(int(support["raw_active_timestamp_rows"]) == 1200, support)
        assert_true(float(support["raw_vlow_iok_timestamp_frac"]) == 1.0, support)
        assert_true(len(summary) == 2, f"unexpected summary rows: {len(summary)}")
        assert_true("engine patch candidate sum: `0`" in note, "note missing engine guardrail")
    print("smoke ok: panel_day_engine_raw_waveform_physical_support_review_v1")


if __name__ == "__main__":
    main()
