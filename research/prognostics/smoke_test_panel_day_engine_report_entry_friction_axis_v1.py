#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_report_entry_friction_axis_v1.csv"
SUMMARY_NAME = "panel_day_engine_report_entry_friction_axis_summary_v1.csv"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture(root: Path) -> None:
    data_root = root / "data" / "conalog" / "out"
    result_root = root / "result"
    write_csv(
        data_root / "ae_simple_fault_candidates.csv",
        [
            {
                "date": "2025-01-10",
                "panel_id": "panel.noentry",
                "group_off_date": 1,
                "site_event_soft": 0,
                "site_event_hard": 0,
                "pre_ews": 1,
                "prefault_B": 0,
                "fault_like_day": 0,
                "final_fault": 0,
                "critical_fault": 0,
                "critical_source": "none",
                "recovered_any": 0,
                "recovered_sustained": 0,
                "re_drop": 0,
                "subgroup_common_cause_candidate": 0,
            },
            {
                "date": "2025-01-10",
                "panel_id": "panel.prec",
                "group_off_date": 1,
                "site_event_soft": 0,
                "site_event_hard": 0,
                "pre_ews": 1,
                "prefault_B": 0,
                "fault_like_day": 1,
                "final_fault": 0,
                "critical_fault": 0,
                "critical_source": "none",
                "recovered_any": 0,
                "recovered_sustained": 0,
                "re_drop": 0,
                "subgroup_common_cause_candidate": 0,
            },
            {
                "date": "2025-01-20",
                "panel_id": "panel.rawnear",
                "group_off_date": 0,
                "site_event_soft": 1,
                "site_event_hard": 0,
                "pre_ews": 0,
                "prefault_B": 0,
                "fault_like_day": 1,
                "final_fault": 0,
                "critical_fault": 0,
                "critical_source": "none",
                "recovered_any": 0,
                "recovered_sustained": 0,
                "re_drop": 0,
                "subgroup_common_cause_candidate": 0,
            },
            {
                "date": "2025-01-20",
                "panel_id": "panel.rawfar",
                "group_off_date": 0,
                "site_event_soft": 1,
                "site_event_hard": 0,
                "pre_ews": 0,
                "prefault_B": 0,
                "fault_like_day": 0,
                "final_fault": 1,
                "critical_fault": 1,
                "critical_source": "vdrop",
                "recovered_any": 0,
                "recovered_sustained": 0,
                "re_drop": 0,
                "subgroup_common_cause_candidate": 0,
            },
            {
                "date": "2025-01-30",
                "panel_id": "panel.current",
                "group_off_date": 0,
                "site_event_soft": 0,
                "site_event_hard": 1,
                "pre_ews": 0,
                "prefault_B": 0,
                "fault_like_day": 0,
                "final_fault": 1,
                "critical_fault": 1,
                "critical_source": "vdrop",
                "recovered_any": 0,
                "recovered_sustained": 0,
                "re_drop": 0,
                "subgroup_common_cause_candidate": 1,
            },
        ],
        columns=[
            "date",
            "panel_id",
            "group_off_date",
            "site_event_soft",
            "site_event_hard",
            "pre_ews",
            "prefault_B",
            "fault_like_day",
            "final_fault",
            "critical_fault",
            "critical_source",
            "recovered_any",
            "recovered_sustained",
            "re_drop",
            "subgroup_common_cause_candidate",
        ],
    )

    write_csv(
        result_root / "fault_panel_result_precursor_report_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": "panel.prec",
                "전조날짜": "2025-01-16",
            },
        ],
        columns=["site", "panel_id", "전조날짜"],
    )
    write_csv(
        result_root / "fault_panel_result_raw_only_current_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": "panel.rawnear",
                "전조날짜": "2025-01-07",
                "고장날짜": "2025-01-22",
            },
            {
                "site": "conalog",
                "panel_id": "panel.rawfar",
                "전조날짜": "2025-01-01",
                "고장날짜": "2025-02-10",
            },
        ],
        columns=["site", "panel_id", "전조날짜", "고장날짜"],
    )
    write_csv(
        result_root / "fault_panel_result_raw_only_fault_signal_report_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": "panel.rawnear",
                "전조 시작일": "2025-01-07",
                "신호 기준일": "2025-01-22",
            },
            {
                "site": "conalog",
                "panel_id": "panel.rawfar",
                "전조 시작일": "2025-01-01",
                "신호 기준일": "2025-02-10",
            },
        ],
        columns=["site", "panel_id", "전조 시작일", "신호 기준일"],
    )
    write_csv(
        result_root / "fault_panel_result_current_preview_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": "panel.current",
                "고장 기준일": "2025-01-30",
            },
        ],
        columns=["site", "panel_id", "고장 기준일"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_panel_day_engine_report_entry_friction_axis_v1.py"
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        build_fixture(tmp_root)
        out_dir = tmp_root / "out"
        cmd = [
            sys.executable,
            str(script),
            "--data-root",
            str(tmp_root / "data"),
            "--result-root",
            str(tmp_root / "result"),
            "--output-dir",
            str(out_dir),
            "--sites",
            "conalog",
        ]
        completed = run(cmd, repo_root)
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)

        detail_df = pd.read_csv(out_dir / DETAIL_NAME, encoding="utf-8-sig")
        summary_df = pd.read_csv(out_dir / SUMMARY_NAME, encoding="utf-8-sig")
        assert_true(len(detail_df) == 5, f"unexpected detail rows: {len(detail_df)}")

        blocker_map = {
            (row["direct_flag_family"], row["panel_id"]): row["blocker_type"]
            for row in detail_df.to_dict(orient="records")
        }
        assert_true(blocker_map[("group_off_date", "panel.noentry")] == "no_report_lane_entry", blocker_map)
        assert_true(blocker_map[("group_off_date", "panel.prec")] == "precursor_carryover_without_exact_overlap", blocker_map)
        assert_true(blocker_map[("site_event", "panel.rawnear")] == "rawonly_near_signal_anchor", blocker_map)
        assert_true(blocker_map[("site_event", "panel.rawfar")] == "rawonly_date_displaced", blocker_map)
        assert_true(blocker_map[("site_event", "panel.current")] == "current_exact_overlap", blocker_map)

        site_event_summary = summary_df.loc[summary_df["direct_flag_family"].eq("site_event")]
        assert_true(int(site_event_summary["panels"].sum()) == 3, site_event_summary.to_string())


if __name__ == "__main__":
    main()
