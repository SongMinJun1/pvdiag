#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_common_cause_manual_trace_review_v1.csv"
SUMMARY_NAME = "panel_day_engine_common_cause_manual_trace_review_summary_v1.csv"
NOTE_NAME = "panel_day_engine_common_cause_manual_trace_review_note_v1.md"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write_blockers(path: Path) -> None:
    rows = [
        {
            "review_case_id": "BR073-001",
            "source_search_case_id": "BR072-001",
            "source_candidate_case_id": "BR064-001",
            "site": "site_a",
            "panel_id": "root.0.1",
            "panel_root_id": "root.0",
            "structural_blocker_subtype": "official_current_date_displaced",
            "blocker_axis": "report_layer_date_alignment",
            "patch_readiness_bucket": "manual_trace_review_only",
            "manual_trace_review_flag": 1,
            "structural_patch_target_review_flag": 1,
            "raw_direct_common_cause_row_count": 1,
            "raw_direct_common_cause_dates": "2026-01-10",
            "raw_direct_common_cause_family": "site_event_soft",
            "official_current_entry_flag": 1,
            "official_current_dates": "2026-01-10",
            "nearest_official_current_gap_days": 0,
            "report_lane_presence": "official_current",
            "best_report_lane": "official_current",
            "synchrony_bucket": "site_event_synchrony",
            "friction_blocker_types": "current_date_displaced",
        },
        {
            "review_case_id": "BR073-002",
            "source_search_case_id": "BR072-002",
            "source_candidate_case_id": "BR064-002",
            "site": "site_a",
            "panel_id": "root.0.2",
            "panel_root_id": "root.0",
            "structural_blocker_subtype": "official_current_date_displaced",
            "blocker_axis": "report_layer_date_alignment",
            "patch_readiness_bucket": "manual_trace_review_only",
            "manual_trace_review_flag": 1,
            "structural_patch_target_review_flag": 1,
            "raw_direct_common_cause_row_count": 1,
            "raw_direct_common_cause_dates": "2026-03-12",
            "raw_direct_common_cause_family": "site_event_soft",
            "official_current_entry_flag": 1,
            "official_current_dates": "2026-01-01",
            "nearest_official_current_gap_days": 70,
            "report_lane_presence": "official_current",
            "best_report_lane": "official_current",
            "synchrony_bucket": "site_event_synchrony",
            "friction_blocker_types": "current_date_displaced",
        },
        {
            "review_case_id": "BR073-003",
            "source_search_case_id": "BR072-003",
            "source_candidate_case_id": "BR064-003",
            "site": "site_a",
            "panel_id": "root.0.3",
            "panel_root_id": "root.0",
            "structural_blocker_subtype": "rawonly_near_signal_anchor",
            "blocker_axis": "rawonly_report_trace",
            "patch_readiness_bucket": "manual_trace_review_only",
            "manual_trace_review_flag": 1,
            "structural_patch_target_review_flag": 1,
            "raw_direct_common_cause_row_count": 1,
            "raw_direct_common_cause_dates": "2026-02-12",
            "raw_direct_common_cause_family": "group_off_date",
            "official_current_entry_flag": 0,
            "official_current_dates": "",
            "nearest_official_current_gap_days": "",
            "report_lane_presence": "rawonly_signal",
            "best_report_lane": "rawonly_current",
            "synchrony_bucket": "group_off_synchrony",
            "friction_blocker_types": "rawonly_near_signal_anchor",
        },
        {
            "review_case_id": "BR073-004",
            "source_search_case_id": "BR072-004",
            "source_candidate_case_id": "BR064-004",
            "site": "site_a",
            "panel_id": "root.0.4",
            "panel_root_id": "root.0",
            "structural_blocker_subtype": "rawonly_near_signal_anchor",
            "blocker_axis": "rawonly_report_trace",
            "patch_readiness_bucket": "manual_trace_review_only",
            "manual_trace_review_flag": 1,
            "structural_patch_target_review_flag": 1,
            "raw_direct_common_cause_row_count": 1,
            "raw_direct_common_cause_dates": "2026-02-20",
            "raw_direct_common_cause_family": "group_off_date",
            "official_current_entry_flag": 0,
            "official_current_dates": "",
            "nearest_official_current_gap_days": "",
            "report_lane_presence": "rawonly_signal",
            "best_report_lane": "rawonly_current",
            "synchrony_bucket": "group_off_synchrony",
            "friction_blocker_types": "rawonly_date_displaced",
        },
    ]
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def write_reports(root: Path) -> tuple[Path, Path, Path]:
    current = root / "current.csv"
    precursor = root / "precursor.csv"
    rawonly = root / "rawonly.csv"
    pd.DataFrame(
        [
            {"site": "site_a", "panel_id": "root.0.1", "고장날짜": "2026-01-10"},
            {"site": "site_a", "panel_id": "root.0.2", "고장날짜": "2026-01-01"},
        ]
    ).to_csv(current, index=False, encoding="utf-8-sig")
    pd.DataFrame(
        [
            {"site": "site_a", "panel_id": "root.0.4", "전조날짜": "2026-02-01"},
        ]
    ).to_csv(precursor, index=False, encoding="utf-8-sig")
    pd.DataFrame(
        [
            {"site": "site_a", "panel_id": "root.0.3", "신호 기준일": "2026-02-10", "전조 시작일": ""},
            {"site": "site_a", "panel_id": "root.0.4", "신호 기준일": "2026-02-01", "전조 시작일": ""},
        ]
    ).to_csv(rawonly, index=False, encoding="utf-8-sig")
    return current, precursor, rawonly


def write_raw(data_root: Path) -> None:
    out_dir = data_root / "site_a" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "date": "2026-01-10",
            "panel_id": "root.0.1",
            "group_off_date": False,
            "site_event_soft": 1,
            "site_event_hard": 0,
            "pre_ews": True,
            "prefault_B": False,
            "fault_like_day": True,
            "final_fault": False,
            "critical_fault": False,
            "mid_ratio": 0.10,
            "mid_v_ratio": 0.90,
            "mid_i_ratio": 0.11,
            "co_drop_frac": 0.20,
            "source_csv": "day1.csv",
        },
        {
            "date": "2026-03-12",
            "panel_id": "root.0.2",
            "group_off_date": False,
            "site_event_soft": 1,
            "site_event_hard": 0,
            "pre_ews": True,
            "prefault_B": False,
            "fault_like_day": True,
            "final_fault": False,
            "critical_fault": False,
            "mid_ratio": 0.00,
            "mid_v_ratio": 1.08,
            "mid_i_ratio": 0.00,
            "co_drop_frac": 0.47,
            "source_csv": "day2.csv",
        },
        {
            "date": "2026-02-12",
            "panel_id": "root.0.3",
            "group_off_date": True,
            "site_event_soft": 0,
            "site_event_hard": 0,
            "pre_ews": False,
            "prefault_B": False,
            "fault_like_day": True,
            "final_fault": False,
            "critical_fault": False,
            "mid_ratio": 0.16,
            "mid_v_ratio": 1.01,
            "mid_i_ratio": 0.02,
            "co_drop_frac": 0.25,
            "source_csv": "day3.csv",
        },
        {
            "date": "2026-02-20",
            "panel_id": "root.0.4",
            "group_off_date": True,
            "site_event_soft": 0,
            "site_event_hard": 0,
            "pre_ews": False,
            "prefault_B": False,
            "fault_like_day": True,
            "final_fault": False,
            "critical_fault": False,
            "mid_ratio": 0.18,
            "mid_v_ratio": 1.02,
            "mid_i_ratio": 0.03,
            "co_drop_frac": 0.26,
            "source_csv": "day4.csv",
        },
    ]
    pd.DataFrame(rows).to_csv(out_dir / "ae_simple_fault_candidates.csv", index=False)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = (
        repo_root
        / "research"
        / "prognostics"
        / "build_panel_day_engine_common_cause_manual_trace_review_v1.py"
    )
    with tempfile.TemporaryDirectory(prefix="common_cause_manual_trace_") as tmp_dir:
        root = Path(tmp_dir)
        blocker_input = root / "blockers.csv"
        data_root = root / "data"
        out_dir = root / "out"
        write_blockers(blocker_input)
        current, precursor, rawonly = write_reports(root)
        write_raw(data_root)
        result = subprocess.run(
            [
                "python3",
                str(script),
                "--blocker-input",
                str(blocker_input),
                "--current-input",
                str(current),
                "--precursor-input",
                str(precursor),
                "--rawonly-signal-input",
                str(rawonly),
                "--data-root",
                str(data_root),
                "--output-dir",
                str(out_dir),
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
        )
        assert_true(result.returncode == 0, f"builder failed:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}")
        detail = pd.read_csv(out_dir / DETAIL_NAME, low_memory=False)
        summary = pd.read_csv(out_dir / SUMMARY_NAME, low_memory=False)
        note = (out_dir / NOTE_NAME).read_text(encoding="utf-8")
        by_panel = detail.set_index("panel_id")
        assert_true(len(detail) == 4, detail.to_string())
        assert_true(
            by_panel.loc["root.0.1", "trace_outcome_bucket"] == "exact_current_bridge_review",
            detail.to_string(),
        )
        assert_true(int(by_panel.loc["root.0.1", "official_current_bridge_candidate_flag"]) == 1, detail.to_string())
        assert_true(
            by_panel.loc["root.0.2", "trace_outcome_bucket"] == "post_current_common_cause_late_event_hold",
            detail.to_string(),
        )
        assert_true(
            by_panel.loc["root.0.3", "trace_outcome_bucket"] == "rawonly_near_anchor_trace_only",
            detail.to_string(),
        )
        assert_true(int(by_panel.loc["root.0.3", "rawonly_report_bridge_candidate_flag"]) == 1, detail.to_string())
        assert_true(
            by_panel.loc["root.0.4", "trace_outcome_bucket"] == "manual_trace_hold_unresolved",
            detail.to_string(),
        )
        assert_true(int(detail["semantic_patch_candidate_flag"].sum()) == 0, "semantic patch must stay zero")
        assert_true(int(detail["operator_promotion_allowed_flag"].sum()) == 0, "promotion must stay zero")
        assert_true(int(detail["engine_patch_candidate_flag"].sum()) == 0, "engine patch must stay zero")
        assert_true(int(detail["threshold_patch_allowed_flag"].sum()) == 0, "threshold patch must stay zero")
        assert_true(int(summary["cases"].sum()) == 4, summary.to_string())
        assert_true("semantic patch candidate sum: `0`" in note, "note missing semantic guardrail")
    print("smoke ok: panel_day_engine_common_cause_manual_trace_review_v1")


if __name__ == "__main__":
    main()
