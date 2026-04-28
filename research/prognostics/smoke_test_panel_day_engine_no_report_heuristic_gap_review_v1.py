#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_no_report_heuristic_gap_review_v1.csv"
SUMMARY_NAME = "panel_day_engine_no_report_heuristic_gap_review_summary_v1.csv"
NOTE_NAME = "panel_day_engine_no_report_heuristic_gap_review_note_v1.md"
LOCAL_NAME = "panel_day_engine_local_morphology_exact_seed_search_v1.csv"
RAW_AUDIT_NAME = "panel_day_engine_runtime_fault_event_audit_v1.csv"
RAW_FINAL_NAME = "panel_day_engine_runtime_final_verdict_v1.csv"
RAW_HEUR_NAME = "panel_day_engine_runtime_cause_candidate_heuristics_v1.csv"
RAW_CANDIDATE_NAME = "ae_simple_fault_candidates.csv"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_panel_day_engine_no_report_heuristic_gap_review_v1.py"
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        local_root = root / "local"
        data_root = root / "data"
        share_root = root / "share"
        result_root = root / "result"
        out_root = root / "out"

        panels = [
            ("test", "near_nonfault", "2026-01-04", "2026-01-01"),
            ("test", "hard_fault_missing", "2026-02-01", "2026-02-01"),
            ("test", "date_displaced", "2026-03-01", "2026-01-01"),
        ]
        write_csv(
            local_root / LOCAL_NAME,
            [
                {
                    "site": site,
                    "panel_id": panel_id,
                    "search_status": "no_report_heuristic_match",
                    "recovery_bucket": "sustained_recovery",
                    "synchrony_bucket": "panel_local_or_weak_synchrony",
                    "anchor_dates": anchor,
                }
                for site, panel_id, _raw_date, anchor in panels
            ],
        )
        write_csv(
            data_root / "test" / "out" / RAW_CANDIDATE_NAME,
            [
                {
                    "date": raw_date,
                    "panel_id": panel_id,
                    "pre_ews": panel_id != "hard_fault_missing",
                    "prefault_B": False,
                    "prefault_B_effective": False,
                    "fault_like_day": panel_id == "hard_fault_missing",
                    "final_fault": panel_id == "hard_fault_missing",
                    "critical_fault": False,
                    "recovered_any": panel_id != "hard_fault_missing",
                    "recovered_sustained": panel_id != "hard_fault_missing",
                    "re_drop": False,
                    "site_event_soft": False,
                    "site_event_hard": False,
                    "group_off_date": False,
                    "group_off_like": False,
                    "subgroup_common_cause_candidate": False,
                    "prefault_B_common_cause_overlap": False,
                }
                for _site, panel_id, raw_date, _anchor in panels
            ],
        )
        write_csv(
            share_root / RAW_AUDIT_NAME,
            [
                {
                    "site": "test",
                    "panel_id": panel_id,
                    "패널고장여부_ko": "고장" if panel_id == "hard_fault_missing" else "미확정",
                    "사건유형_재판정_ko": "급작 고장" if panel_id == "hard_fault_missing" else "",
                    "대표anom_subtype": "confirmed_fault" if panel_id == "hard_fault_missing" else "normal",
                    "대표critical_source": "vdrop" if panel_id == "hard_fault_missing" else "none",
                }
                for _site, panel_id, _raw_date, _anchor in panels
            ],
        )
        write_csv(
            share_root / RAW_FINAL_NAME,
            [
                {
                    "site": "test",
                    "panel_id": panel_id,
                    "패널고장여부_ko": "고장" if panel_id == "hard_fault_missing" else "미확정",
                }
                for _site, panel_id, _raw_date, _anchor in panels
            ],
        )
        write_csv(share_root / RAW_HEUR_NAME, [{"site": "test", "panel_id": "other", "원인후보_top1_ko": "열화형"}])
        for name in [
            "fault_panel_result_current_v1.csv",
            "fault_panel_result_current_preview_v1.csv",
            "fault_panel_result_raw_only_current_v1.csv",
            "fault_panel_result_raw_only_current_preview_v1.csv",
            "fault_panel_result_precursor_report_v1.csv",
            "fault_panel_result_raw_only_fault_signal_report_v1.csv",
        ]:
            write_csv(result_root / name, [{"site": "test", "panel_id": "other"}])

        cmd = [
            sys.executable,
            str(script),
            "--local-search-root",
            str(local_root),
            "--data-root",
            str(data_root),
            "--result-root",
            str(result_root),
            "--raw-only-share-root",
            str(share_root),
            "--output-dir",
            str(out_root),
            "--sites",
            "test",
        ]
        completed = run(cmd, repo_root)
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)
        detail = pd.read_csv(out_root / DETAIL_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(out_root / SUMMARY_NAME, encoding="utf-8-sig")
        assert_true((out_root / NOTE_NAME).exists(), "missing note output")
        assert_true(len(detail) == 3, detail.to_string())
        by_panel = {row["panel_id"]: row for row in detail.to_dict(orient="records")}
        assert_true(by_panel["near_nonfault"]["heuristic_attachment_gap_type"] == "expected_absent_non_fault_status_gate", detail.to_string())
        assert_true(by_panel["near_nonfault"]["report_patch_candidate_flag"] == 1, detail.to_string())
        assert_true(by_panel["hard_fault_missing"]["engine_patch_candidate_flag"] == 1, detail.to_string())
        assert_true(by_panel["hard_fault_missing"]["heuristic_attachment_gap_type"] == "unexpected_missing_for_fault_signal", detail.to_string())
        assert_true(by_panel["date_displaced"]["date_alignment_gap_type"] == "date_displaced_gt14d", detail.to_string())
        assert_true(int(summary["panels"].sum()) == 3, summary.to_string())


if __name__ == "__main__":
    main()
