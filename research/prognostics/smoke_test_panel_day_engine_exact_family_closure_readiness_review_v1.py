#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_exact_family_closure_readiness_review_v1.csv"
SUMMARY_NAME = "panel_day_engine_exact_family_closure_readiness_review_summary_v1.csv"
NOTE_NAME = "panel_day_engine_exact_family_closure_readiness_review_note_v1.md"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def local_row(panel_id: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "site": "test",
        "panel_id": panel_id,
        "search_status": "same_day_local_non_target",
        "recovery_bucket": "re_drop_cycle",
        "synchrony_bucket": "panel_local_or_weak_synchrony",
        "anchor_dates": "2026-01-01",
        "same_day_dates": "2026-01-01",
        "raw_top1_ko": "다이오드·서브스트링형",
        "raw_top1_score": 8,
        "raw_top2_ko": "접속·부분개방형",
        "raw_top3_ko": "열화형",
        "live_top1_ko": "",
        "live_external_gpvs_ko": "",
        "gpvs_pack_external_ko": "",
        "target_exact_top1_flag": 0,
        "device_response_external_flag": 0,
        "sensor_feedback_top1_flag": 0,
        "recovery_recurrence_flag": 1,
        "exact_same_day_local_morphology_flag": 1,
        "same_day_fault_like_row_count": 0,
        "same_day_final_fault_row_count": 1,
        "same_day_common_cause_row_count": 0,
        "supportive_seed_candidate_flag": 0,
        "exact_family_candidate_flag": 0,
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
        / "build_panel_day_engine_exact_family_closure_readiness_review_v1.py"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        local_path = root / "local.csv"
        gap_path = root / "gap.csv"
        observation_path = root / "observation.csv"
        out_root = root / "out"

        write_csv(
            local_path,
            [
                local_row(
                    "target_exact",
                    raw_top1_ko="장치 응답 이상형",
                    target_exact_top1_flag=1,
                    exact_family_candidate_flag=1,
                ),
                local_row("hard_non_target"),
                local_row(
                    "sensor_pressure",
                    raw_top1_ko="센서·피드백형",
                    sensor_feedback_top1_flag=1,
                ),
                local_row(
                    "no_report_sidecar",
                    search_status="no_report_heuristic_match",
                    raw_top1_ko="",
                    same_day_dates="",
                    exact_same_day_local_morphology_flag=0,
                    same_day_final_fault_row_count=0,
                ),
                local_row(
                    "no_report_date_displaced",
                    search_status="no_report_heuristic_match",
                    raw_top1_ko="",
                    same_day_dates="",
                    exact_same_day_local_morphology_flag=0,
                    same_day_final_fault_row_count=0,
                ),
                local_row(
                    "supportive_device_response",
                    search_status="supportive_device_response_recovery_seed",
                    raw_top1_ko="열화형",
                    device_response_external_flag=1,
                    supportive_seed_candidate_flag=1,
                    same_day_final_fault_row_count=0,
                ),
            ],
        )
        write_csv(
            gap_path,
            [
                {
                    "site": "test",
                    "panel_id": "no_report_sidecar",
                    "date_alignment_gap_type": "near_anchor_1_3d",
                    "heuristic_attachment_gap_type": "expected_absent_non_fault_status_gate",
                    "report_attachment_gap_type": "final_verdict_all_rows_only_non_fault",
                    "raw_audit_status_ko": "미확정",
                    "raw_final_status_ko": "미확정",
                },
                {
                    "site": "test",
                    "panel_id": "no_report_date_displaced",
                    "date_alignment_gap_type": "date_displaced_gt14d",
                    "heuristic_attachment_gap_type": "expected_absent_non_fault_status_gate",
                    "report_attachment_gap_type": "final_verdict_all_rows_only_non_fault",
                    "raw_audit_status_ko": "미확정",
                    "raw_final_status_ko": "미확정",
                },
            ],
        )
        write_csv(observation_path, [{"site": "test", "panel_id": "no_report_sidecar"}])

        completed = run(
            [
                sys.executable,
                str(script),
                "--local-morphology-input",
                str(local_path),
                "--gap-review-input",
                str(gap_path),
                "--observation-sidecar-input",
                str(observation_path),
                "--output-dir",
                str(out_root),
            ],
            repo_root,
        )
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)
        detail = pd.read_csv(out_root / DETAIL_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(out_root / SUMMARY_NAME, encoding="utf-8-sig")
        note = (out_root / NOTE_NAME).read_text(encoding="utf-8")
        by_panel = {row["panel_id"]: row for row in detail.to_dict(orient="records")}
        assert_true(by_panel["target_exact"]["post_br056_closure_class"] == "target_exact_family_closure_candidate", detail.to_string())
        assert_true(by_panel["hard_non_target"]["post_br056_closure_class"] == "hard_same_day_non_target_fault_family_seed", detail.to_string())
        assert_true(by_panel["sensor_pressure"]["post_br056_closure_class"] == "sensor_feedback_hard_same_day_pressure", detail.to_string())
        assert_true(by_panel["no_report_sidecar"]["post_br056_closure_class"] == "closed_non_fault_near_anchor_observation", detail.to_string())
        assert_true(by_panel["no_report_date_displaced"]["post_br056_closure_class"] == "closed_non_fault_date_displaced_evidence", detail.to_string())
        assert_true(by_panel["supportive_device_response"]["post_br056_closure_class"] == "supportive_device_response_recovery_seed", detail.to_string())
        assert_true(int(detail["target_exact_closure_candidate_flag"].sum()) == 1, detail.to_string())
        assert_true(int(detail["fault_family_regression_seed_flag"].sum()) == 3, detail.to_string())
        assert_true(int(detail["operator_promotion_allowed_flag"].sum()) == 0, detail.to_string())
        assert_true(int(detail["engine_patch_candidate_flag"].sum()) == 0, detail.to_string())
        assert_true(int(summary["panels"].sum()) == 6, summary.to_string())
        assert_true("manual adjudication before any patch" in note, note)


if __name__ == "__main__":
    main()
