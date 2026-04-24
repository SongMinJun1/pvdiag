#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_common_cause_synchrony_axis_v1.csv"
SUMMARY_NAME = "panel_day_engine_common_cause_synchrony_axis_summary_v1.csv"


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
    rows = [
        {
            "date": "2025-01-10",
            "panel_id": "panel.siteevent",
            "pre_ews": 1,
            "prefault_B": 0,
            "prefault_B_effective": 0,
            "fault_like_day": 1,
            "final_fault": 0,
            "critical_fault": 0,
            "site_event_soft": 1,
            "site_event_hard": 0,
            "site_event_reason": "co_drop_surge",
            "group_off_date": 0,
            "group_off_like": 0,
            "group_off_group": "",
            "subgroup_common_cause_candidate": 0,
            "prefault_B_common_cause_overlap": 0,
            "co_drop_frac": 0.20,
            "base_day_panel_count": 10,
            "base_day_degraded_panel_count": 2,
        },
        {
            "date": "2025-01-11",
            "panel_id": "panel.groupoff",
            "pre_ews": 0,
            "prefault_B": 0,
            "prefault_B_effective": 0,
            "fault_like_day": 1,
            "final_fault": 0,
            "critical_fault": 0,
            "site_event_soft": 0,
            "site_event_hard": 0,
            "site_event_reason": "",
            "group_off_date": 1,
            "group_off_like": 0,
            "group_off_group": "group-a",
            "subgroup_common_cause_candidate": 0,
            "prefault_B_common_cause_overlap": 0,
            "co_drop_frac": 0.18,
            "base_day_panel_count": 12,
            "base_day_degraded_panel_count": 1,
        },
        {
            "date": "2025-01-12",
            "panel_id": "panel.prefb_overlap",
            "pre_ews": 0,
            "prefault_B": 1,
            "prefault_B_effective": 1,
            "fault_like_day": 0,
            "final_fault": 0,
            "critical_fault": 0,
            "site_event_soft": 0,
            "site_event_hard": 0,
            "site_event_reason": "",
            "group_off_date": 0,
            "group_off_like": 0,
            "group_off_group": "",
            "subgroup_common_cause_candidate": 0,
            "prefault_B_common_cause_overlap": 1,
            "co_drop_frac": 0.22,
            "base_day_panel_count": 9,
            "base_day_degraded_panel_count": 2,
        },
        {
            "date": "2025-01-13",
            "panel_id": "panel.subgroup",
            "pre_ews": 0,
            "prefault_B": 0,
            "prefault_B_effective": 0,
            "fault_like_day": 0,
            "final_fault": 1,
            "critical_fault": 0,
            "site_event_soft": 0,
            "site_event_hard": 0,
            "site_event_reason": "",
            "group_off_date": 0,
            "group_off_like": 0,
            "group_off_group": "",
            "subgroup_common_cause_candidate": 1,
            "prefault_B_common_cause_overlap": 0,
            "co_drop_frac": 0.19,
            "base_day_panel_count": 14,
            "base_day_degraded_panel_count": 3,
        },
        {
            "date": "2025-01-14",
            "panel_id": "panel.codrop",
            "pre_ews": 0,
            "prefault_B": 0,
            "prefault_B_effective": 0,
            "fault_like_day": 0,
            "final_fault": 0,
            "critical_fault": 0,
            "site_event_soft": 0,
            "site_event_hard": 0,
            "site_event_reason": "",
            "group_off_date": 0,
            "group_off_like": 0,
            "group_off_group": "",
            "subgroup_common_cause_candidate": 0,
            "prefault_B_common_cause_overlap": 0,
            "co_drop_frac": 0.40,
            "base_day_panel_count": 15,
            "base_day_degraded_panel_count": 6,
        },
        {
            "date": "2025-01-15",
            "panel_id": "panel.local",
            "pre_ews": 1,
            "prefault_B": 0,
            "prefault_B_effective": 0,
            "fault_like_day": 1,
            "final_fault": 0,
            "critical_fault": 0,
            "site_event_soft": 0,
            "site_event_hard": 0,
            "site_event_reason": "",
            "group_off_date": 0,
            "group_off_like": 0,
            "group_off_group": "",
            "subgroup_common_cause_candidate": 0,
            "prefault_B_common_cause_overlap": 0,
            "co_drop_frac": 0.10,
            "base_day_panel_count": 8,
            "base_day_degraded_panel_count": 1,
        },
    ]
    columns = list(rows[0].keys())
    write_csv(data_root / "ae_simple_fault_candidates.csv", rows, columns=columns)

    write_csv(
        result_root / "fault_panel_result_current_preview_v1.csv",
        [{"site": "conalog", "panel_id": "panel.siteevent", "고장 기준일": "2025-01-10"}],
        columns=["site", "panel_id", "고장 기준일"],
    )
    write_csv(
        result_root / "fault_panel_result_precursor_report_v1.csv",
        [{"site": "conalog", "panel_id": "panel.prefb_overlap", "전조날짜": "2025-01-12"}],
        columns=["site", "panel_id", "전조날짜"],
    )
    write_csv(
        result_root / "fault_panel_result_raw_only_fault_signal_report_v1.csv",
        [{"site": "conalog", "panel_id": "panel.groupoff", "신호 기준일": "2025-01-11"}],
        columns=["site", "panel_id", "신호 기준일"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_panel_day_engine_common_cause_synchrony_axis_v1.py"
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
            "--co-drop-hint-thr",
            "0.35",
        ]
        completed = run(cmd, repo_root)
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)

        detail_df = pd.read_csv(out_dir / DETAIL_NAME, encoding="utf-8-sig")
        summary_df = pd.read_csv(out_dir / SUMMARY_NAME, encoding="utf-8-sig")
        assert_true(len(detail_df) == 6, f"unexpected detail rows: {len(detail_df)}")

        bucket_map = {
            row["panel_id"]: (row["synchrony_bucket"], row["best_report_lane"])
            for row in detail_df.to_dict(orient="records")
        }
        assert_true(bucket_map["panel.siteevent"] == ("site_event_synchrony", "official_current"), str(bucket_map))
        assert_true(bucket_map["panel.groupoff"] == ("group_off_synchrony", "rawonly_signal"), str(bucket_map))
        assert_true(bucket_map["panel.prefb_overlap"] == ("prefault_B_common_cause_overlap", "precursor"), str(bucket_map))
        assert_true(bucket_map["panel.subgroup"] == ("subgroup_synchrony_candidate", "none"), str(bucket_map))
        assert_true(bucket_map["panel.codrop"] == ("co_drop_breadth_hint", "none"), str(bucket_map))
        assert_true(bucket_map["panel.local"] == ("panel_local_or_weak_synchrony", "none"), str(bucket_map))

        site_event = detail_df.loc[detail_df["panel_id"].eq("panel.siteevent")].iloc[0]
        assert_true(site_event["site_event_reasons"] == "co_drop_surge", site_event.to_string())
        assert_true(int(detail_df["common_cause_row_count"].sum()) == 5, detail_df.to_string())
        assert_true(
            int(summary_df.loc[summary_df["synchrony_bucket"].eq("group_off_synchrony"), "panels"].sum()) == 1,
            summary_df.to_string(),
        )


if __name__ == "__main__":
    main()
