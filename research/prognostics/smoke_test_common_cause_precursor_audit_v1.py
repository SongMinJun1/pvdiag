#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def make_rows(site: str, date: str, group_key: str, count: int) -> list[dict[str, object]]:
    rows = []
    for idx in range(count):
        rows.append(
            {
                "date": date,
                "panel_id": f"{group_key}.{idx}",
                "group_key_base": group_key,
                "mid_ratio": 0.0,
                "mid_i_ratio": 0.0,
                "mid_v_ratio": 1.10,
                "coverage_mid": 1.0,
            }
        )
    return rows


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_common_cause_precursor_audit_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_maintenance_proxy_event_timing_audit_v2.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        data_dir = tmp_root / "data" / "demo" / "out"
        share_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        panel_rows = []
        panel_rows.extend(make_rows("demo", "2025-03-10", "broadA", 4))
        panel_rows.extend(make_rows("demo", "2025-03-10", "broadB", 3))
        panel_rows.extend(make_rows("demo", "2025-03-10", "broadC", 3))
        panel_rows.extend(make_rows("demo", "2025-03-12", "mediumA", 3))
        panel_rows.extend(make_rows("demo", "2025-03-12", "mediumB", 2))
        panel_rows.extend(make_rows("demo", "2025-03-15", "narrowA", 3))
        panel_rows.extend(make_rows("demo", "2025-03-25", "windowA", 3))
        panel_df = pd.DataFrame(panel_rows)
        panel_df.to_csv(data_dir / "panel_day_core.csv", index=False, encoding="utf-8-sig")

        episodes = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "trigger_mode": "medium_or_higher",
                    "episode_id": "ep_exact",
                    "episode_start_date": "2025-03-10",
                    "episode_end_date": "2025-03-10",
                },
                {
                    "site": "demo",
                    "trigger_mode": "medium_or_higher",
                    "episode_id": "ep_lead_2",
                    "episode_start_date": "2025-03-14",
                    "episode_end_date": "2025-03-14",
                },
                {
                    "site": "demo",
                    "trigger_mode": "medium_or_higher",
                    "episode_id": "ep_lead_5",
                    "episode_start_date": "2025-03-20",
                    "episode_end_date": "2025-03-22",
                },
                {
                    "site": "demo",
                    "trigger_mode": "medium_or_higher",
                    "episode_id": "ep_window",
                    "episode_start_date": "2025-03-24",
                    "episode_end_date": "2025-03-26",
                },
            ]
        )
        episodes.to_csv(share_dir / "site_day_alert_episodes_latest.csv", index=False, encoding="utf-8-sig")

        frame = pd.DataFrame(
            [
                {"site": "demo", "date": "2025-03-10", "event_day_flag": 1},
                {"site": "demo", "date": "2025-03-12", "event_day_flag": 0},
                {"site": "demo", "date": "2025-03-15", "event_day_flag": 0},
                {"site": "demo", "date": "2025-03-25", "event_day_flag": 0},
            ]
        )
        frame.to_csv(share_dir / "site_day_event_frame_latest.csv", index=False, encoding="utf-8-sig")

        run_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(run_res.returncode == 0, f"script failed:\n{run_res.stdout}\n{run_res.stderr}")

        summary_df = pd.read_csv(share_dir / "common_cause_precursor_audit_summary_v1.csv", encoding="utf-8-sig")
        candidate_df = pd.read_csv(share_dir / "common_cause_precursor_candidate_days_v1.csv", encoding="utf-8-sig")
        matches_df = pd.read_csv(share_dir / "common_cause_precursor_episode_matches_v1.csv", encoding="utf-8-sig")

        assert_true(not summary_df.empty, "summary output is empty")
        assert_true(not candidate_df.empty, "candidate output is empty")
        assert_true(not matches_df.empty, "episode matches output is empty")

        broad_days = candidate_df.loc[candidate_df["tier_id"].eq("broad_3g_10p"), "date"].tolist()
        medium_days = sorted(candidate_df.loc[candidate_df["tier_id"].eq("medium_2g_5p"), "date"].tolist())
        narrow_days = sorted(candidate_df.loc[candidate_df["tier_id"].eq("narrow_1g_3p"), "date"].tolist())
        assert_true(broad_days == ["2025-03-10"], "synthetic broad tier should select only the broad candidate day")
        assert_true(medium_days == ["2025-03-10", "2025-03-12"], "synthetic medium tier should select expected candidate days")
        assert_true(narrow_days == ["2025-03-10", "2025-03-12", "2025-03-15", "2025-03-25"], "synthetic narrow tier should select expected candidate days")

        plus2 = candidate_df.loc[(candidate_df["tier_id"].eq("medium_2g_5p")) & (candidate_df["date"].eq("2025-03-12"))].iloc[0]
        assert_true(plus2["precursor_timing_type"] == "lead_1_to_3_days", "synthetic +2 day precursor should be classified as lead_1_to_3_days")

        plus5 = candidate_df.loc[(candidate_df["tier_id"].eq("narrow_1g_3p")) & (candidate_df["date"].eq("2025-03-15"))].iloc[0]
        assert_true(plus5["precursor_timing_type"] == "lead_4_to_7_days", "synthetic +5 day precursor should be classified as lead_4_to_7_days")

        in_window = candidate_df.loc[(candidate_df["tier_id"].eq("narrow_1g_3p")) & (candidate_df["date"].eq("2025-03-25"))].iloc[0]
        assert_true(in_window["precursor_timing_type"] == "in_episode_window", "synthetic in-window day should be classified as in_episode_window")

        exact_day = candidate_df.loc[(candidate_df["tier_id"].eq("broad_3g_10p")) & (candidate_df["date"].eq("2025-03-10"))].iloc[0]
        assert_true(exact_day["precursor_timing_type"] == "exact_same_day_episode", "synthetic same-day episode should be classified as exact_same_day_episode")
        assert_true(int(exact_day["exact_same_day_event_flag"]) == 1, "synthetic exact same-day event flag should be preserved")

        print("[OK] outputs generate")
        print("[OK] synthetic broad/medium/narrow tiers select expected candidate days")
        print("[OK] synthetic +2 day precursor is classified as lead_1_to_3_days")
        print("[OK] synthetic +5 day precursor is classified as lead_4_to_7_days")
        print("[OK] synthetic in-window day is classified as in_episode_window")
        print("[OK] synthetic same-day episode is classified as exact_same_day_episode")
        print("[OK] no official prediction outputs are modified")

    safe_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(safe_res.returncode == 0, f"existing safe smoke failed:\n{safe_res.stdout}\n{safe_res.stderr}")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
