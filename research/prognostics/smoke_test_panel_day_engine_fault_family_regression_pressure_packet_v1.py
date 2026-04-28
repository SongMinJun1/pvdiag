#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_fault_family_regression_pressure_packet_v1.csv"
SUMMARY_NAME = "panel_day_engine_fault_family_regression_pressure_packet_summary_v1.csv"
NOTE_NAME = "panel_day_engine_fault_family_regression_pressure_packet_note_v1.md"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def readiness_row(panel_id: str, closure_class: str, regression_flag: int, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "site": "test",
        "panel_id": panel_id,
        "source_search_status": "same_day_local_non_target",
        "post_br056_closure_class": closure_class,
        "evidence_grade": "strong_non_target_fault_family_seed",
        "raw_top1_ko": "다이오드·서브스트링형",
        "raw_top1_score": 8,
        "raw_top2_ko": "접속·부분개방형",
        "raw_top3_ko": "열화형",
        "live_top1_ko": "",
        "live_external_gpvs_ko": "",
        "gpvs_pack_external_ko": "",
        "recovery_bucket": "re_drop_cycle",
        "synchrony_bucket": "panel_local_or_weak_synchrony",
        "anchor_dates": "2026-01-01",
        "same_day_dates": "2026-01-01",
        "target_exact_top1_flag": 0,
        "device_response_external_flag": 0,
        "sensor_feedback_top1_flag": 0,
        "recovery_recurrence_flag": 1,
        "exact_same_day_local_morphology_flag": 1,
        "same_day_fault_like_row_count": 0,
        "same_day_final_fault_row_count": 1,
        "same_day_common_cause_row_count": 0,
        "target_exact_closure_candidate_flag": 0,
        "fault_family_regression_seed_flag": regression_flag,
        "operator_promotion_allowed_flag": 0,
        "engine_patch_candidate_flag": 0,
    }
    row.update(overrides)
    return row


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = (
        repo_root
        / "research"
        / "prognostics"
        / "build_panel_day_engine_fault_family_regression_pressure_packet_v1.py"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        input_path = root / "readiness.csv"
        out_root = root / "out"
        write_csv(
            input_path,
            [
                readiness_row(
                    "hard_non_target",
                    "hard_same_day_non_target_fault_family_seed",
                    1,
                ),
                readiness_row(
                    "sensor_pressure",
                    "sensor_feedback_hard_same_day_pressure",
                    1,
                    evidence_grade="ambiguity_pressure_seed",
                    raw_top1_ko="센서·피드백형",
                    raw_top1_score=6,
                    sensor_feedback_top1_flag=1,
                    same_day_fault_like_row_count=1,
                ),
                readiness_row(
                    "closed_blocker",
                    "closed_non_fault_near_anchor_observation",
                    0,
                    evidence_grade="closed_non_closing_status_blocker",
                    raw_top1_ko="",
                    same_day_final_fault_row_count=0,
                    exact_same_day_local_morphology_flag=0,
                ),
            ],
        )
        completed = run(
            [
                sys.executable,
                str(script),
                "--readiness-input",
                str(input_path),
                "--output-dir",
                str(out_root),
            ],
            repo_root,
        )
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)
        detail = pd.read_csv(out_root / DETAIL_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(out_root / SUMMARY_NAME, encoding="utf-8-sig")
        note = (out_root / NOTE_NAME).read_text(encoding="utf-8")
        assert_true(len(detail) == 2, detail.to_string())
        assert_true(list(detail["packet_case_id"]) == ["BR058-001", "BR058-002"], detail.to_string())
        assert_true(set(detail["packet_bucket"]) == {
            "non_target_hard_same_day_fault_family_seed",
            "sensor_feedback_hard_same_day_ambiguity_pressure",
        }, detail.to_string())
        assert_true(int(detail["target_exact_closure_candidate_flag"].sum()) == 0, detail.to_string())
        assert_true(int(detail["operator_promotion_allowed_flag"].sum()) == 0, detail.to_string())
        assert_true(int(detail["engine_patch_candidate_flag"].sum()) == 0, detail.to_string())
        assert_true(int(summary["cases"].sum()) == 2, summary.to_string())
        assert_true("does not close target exact-family evidence" in note, note)


if __name__ == "__main__":
    main()
