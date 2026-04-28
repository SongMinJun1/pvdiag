#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_recovery_recurrence_axis_v1.csv"
SUMMARY_NAME = "panel_day_engine_recovery_recurrence_axis_summary_v1.csv"


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
                "panel_id": "panel.transient",
                "pre_ews": 1,
                "prefault_B": 0,
                "fault_like_day": 1,
                "final_fault": 0,
                "critical_fault": 0,
                "recovered_any": 1,
                "recovered_sustained": 0,
                "re_drop": 0,
                "sustain_mins": 35,
                "drop_time": "2025-01-10 12:10:00",
                "group_off_date": 0,
                "site_event_soft": 0,
                "site_event_hard": 0,
                "subgroup_common_cause_candidate": 0,
            },
            {
                "date": "2025-01-11",
                "panel_id": "panel.sustained",
                "pre_ews": 0,
                "prefault_B": 1,
                "fault_like_day": 0,
                "final_fault": 0,
                "critical_fault": 0,
                "recovered_any": 1,
                "recovered_sustained": 1,
                "re_drop": 0,
                "sustain_mins": 180,
                "drop_time": "2025-01-11 10:00:00",
                "group_off_date": 1,
                "site_event_soft": 0,
                "site_event_hard": 0,
                "subgroup_common_cause_candidate": 0,
            },
            {
                "date": "2025-01-12",
                "panel_id": "panel.redrop",
                "pre_ews": 0,
                "prefault_B": 0,
                "fault_like_day": 0,
                "final_fault": 1,
                "critical_fault": 1,
                "recovered_any": 1,
                "recovered_sustained": 1,
                "re_drop": 1,
                "sustain_mins": 240,
                "drop_time": "2025-01-12 11:20:00",
                "group_off_date": 0,
                "site_event_soft": 1,
                "site_event_hard": 0,
                "subgroup_common_cause_candidate": 1,
            },
            {
                "date": "2025-01-13",
                "panel_id": "panel.persistent",
                "pre_ews": 1,
                "prefault_B": 0,
                "fault_like_day": 1,
                "final_fault": 0,
                "critical_fault": 0,
                "recovered_any": 0,
                "recovered_sustained": 0,
                "re_drop": 0,
                "sustain_mins": 320,
                "drop_time": "2025-01-13 13:00:00",
                "group_off_date": 0,
                "site_event_soft": 0,
                "site_event_hard": 0,
                "subgroup_common_cause_candidate": 0,
            },
        ],
        columns=[
            "date",
            "panel_id",
            "pre_ews",
            "prefault_B",
            "fault_like_day",
            "final_fault",
            "critical_fault",
            "recovered_any",
            "recovered_sustained",
            "re_drop",
            "sustain_mins",
            "drop_time",
            "group_off_date",
            "site_event_soft",
            "site_event_hard",
            "subgroup_common_cause_candidate",
        ],
    )

    write_csv(
        result_root / "fault_panel_result_precursor_report_v1.csv",
        [
            {"site": "conalog", "panel_id": "panel.transient", "전조날짜": "2025-01-10"},
        ],
        columns=["site", "panel_id", "전조날짜"],
    )
    write_csv(
        result_root / "fault_panel_result_raw_only_current_v1.csv",
        [
            {"site": "conalog", "panel_id": "panel.redrop", "전조날짜": "2025-01-05", "고장날짜": "2025-01-12"},
        ],
        columns=["site", "panel_id", "전조날짜", "고장날짜"],
    )
    write_csv(
        result_root / "fault_panel_result_raw_only_fault_signal_report_v1.csv",
        [
            {"site": "conalog", "panel_id": "panel.sustained", "전조 시작일": "2025-01-11", "신호 기준일": "2025-01-21"},
        ],
        columns=["site", "panel_id", "전조 시작일", "신호 기준일"],
    )
    write_csv(
        result_root / "fault_panel_result_current_preview_v1.csv",
        [
            {"site": "conalog", "panel_id": "panel.redrop", "고장 기준일": "2025-01-12"},
        ],
        columns=["site", "panel_id", "고장 기준일"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_panel_day_engine_recovery_recurrence_axis_v1.py"
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
        assert_true(len(detail_df) == 4, f"unexpected detail rows: {len(detail_df)}")

        bucket_map = {
            row["panel_id"]: (row["recovery_bucket"], row["best_report_lane"])
            for row in detail_df.to_dict(orient="records")
        }
        assert_true(bucket_map["panel.transient"] == ("transient_recovery", "precursor"), str(bucket_map))
        assert_true(bucket_map["panel.sustained"] == ("sustained_recovery", "rawonly_signal"), str(bucket_map))
        assert_true(bucket_map["panel.redrop"] == ("re_drop_cycle", "official_current"), str(bucket_map))
        assert_true(bucket_map["panel.persistent"] == ("persistent_non_recovery", "none"), str(bucket_map))

        assert_true(
            int(summary_df.loc[summary_df["recovery_bucket"].eq("re_drop_cycle"), "panels"].sum()) == 1,
            summary_df.to_string(),
        )


if __name__ == "__main__":
    main()
