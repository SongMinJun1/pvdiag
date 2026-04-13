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


def add_group_rows(
    rows: list[dict[str, object]],
    date: str,
    group_key: str,
    group_like_count: int,
    other_count: int,
) -> None:
    for idx in range(group_like_count):
        rows.append(
            {
                "date": date,
                "panel_id": f"{group_key}.g{idx}",
                "group_key_base": group_key,
                "mid_ratio": 0.0,
                "mid_i_ratio": 0.0,
                "mid_v_ratio": 1.10,
                "coverage_mid": 1.0,
            }
        )
    for idx in range(other_count):
        rows.append(
            {
                "date": date,
                "panel_id": f"{group_key}.o{idx}",
                "group_key_base": group_key,
                "mid_ratio": 1.0,
                "mid_i_ratio": 1.0,
                "mid_v_ratio": 1.0,
                "coverage_mid": 1.0,
            }
        )


def make_day(rows: list[dict[str, object]], date: str, total_rows: int, qualifying_groups: list[tuple[str, int]]) -> None:
    used = 0
    for group_key, group_like_count in qualifying_groups:
        add_group_rows(rows, date, group_key, group_like_count, 0)
        used += group_like_count
    remaining = total_rows - used
    if remaining < 0:
        raise ValueError(f"total_rows too small for {date}")
    for idx in range(remaining):
        rows.append(
            {
                "date": date,
                "panel_id": f"bg.{date.replace('-', '')}.{idx}",
                "group_key_base": f"bg.{date.replace('-', '')}",
                "mid_ratio": 1.0,
                "mid_i_ratio": 1.0,
                "mid_v_ratio": 1.0,
                "coverage_mid": 1.0,
            }
        )


def add_background_window(rows: list[dict[str, object]], dates: list[str], total_rows: int = 10) -> None:
    for date in dates:
        make_day(rows, date, total_rows=total_rows, qualifying_groups=[])


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_common_cause_precursor_case_forensics_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_common_cause_precursor_audit_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        data_dir = tmp_root / "data" / "demo" / "out"
        share_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        candidate_days = pd.DataFrame(
            [
                {
                    "tier_id": "broad_3g_10p",
                    "site": "demo",
                    "date": "2025-03-10",
                    "matched_episode_id": "ep_lead",
                    "matched_trigger_mode": "medium_or_higher",
                    "matched_episode_start_date": "2025-03-12",
                    "matched_episode_end_date": "2025-03-15",
                    "days_to_episode_start": 2,
                    "days_to_episode_end": 5,
                    "precursor_timing_type": "lead_1_to_3_days",
                },
                {
                    "tier_id": "medium_2g_5p",
                    "site": "demo",
                    "date": "2025-03-10",
                    "matched_episode_id": "ep_lead",
                    "matched_trigger_mode": "medium_or_higher",
                    "matched_episode_start_date": "2025-03-12",
                    "matched_episode_end_date": "2025-03-15",
                    "days_to_episode_start": 2,
                    "days_to_episode_end": 5,
                    "precursor_timing_type": "lead_1_to_3_days",
                },
                {
                    "tier_id": "narrow_1g_3p",
                    "site": "demo",
                    "date": "2025-03-12",
                    "matched_episode_id": "ep_exact",
                    "matched_trigger_mode": "medium_or_higher",
                    "matched_episode_start_date": "2025-03-12",
                    "matched_episode_end_date": "2025-03-14",
                    "days_to_episode_start": 0,
                    "days_to_episode_end": 2,
                    "precursor_timing_type": "exact_same_day_episode",
                },
                {
                    "tier_id": "medium_2g_5p",
                    "site": "demo",
                    "date": "2025-03-20",
                    "matched_episode_id": "ep_old",
                    "matched_trigger_mode": "medium_or_higher",
                    "matched_episode_start_date": "2025-03-01",
                    "matched_episode_end_date": "2025-03-02",
                    "days_to_episode_start": -19,
                    "days_to_episode_end": -18,
                    "precursor_timing_type": "no_episode_within_7d",
                },
                {
                    "tier_id": "medium_2g_5p",
                    "site": "demo",
                    "date": "2025-03-21",
                    "matched_episode_id": "ep_old",
                    "matched_trigger_mode": "medium_or_higher",
                    "matched_episode_start_date": "2025-03-01",
                    "matched_episode_end_date": "2025-03-02",
                    "days_to_episode_start": -20,
                    "days_to_episode_end": -19,
                    "precursor_timing_type": "no_episode_within_7d",
                },
                {
                    "tier_id": "narrow_1g_3p",
                    "site": "demo",
                    "date": "2025-03-30",
                    "matched_episode_id": "ep_far",
                    "matched_trigger_mode": "medium_or_higher",
                    "matched_episode_start_date": "2025-04-20",
                    "matched_episode_end_date": "2025-04-21",
                    "days_to_episode_start": 21,
                    "days_to_episode_end": 22,
                    "precursor_timing_type": "no_episode_within_7d",
                },
            ]
        )
        candidate_days.to_csv(
            share_dir / "common_cause_precursor_candidate_days_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )

        episode_matches = pd.DataFrame(
            [
                {
                    "tier_id": "broad_3g_10p",
                    "site": "demo",
                    "matched_episode_id": "ep_lead",
                    "matched_trigger_mode": "medium_or_higher",
                    "matched_episode_start_date": "2025-03-12",
                    "candidate_day_count_for_episode": 1,
                    "earliest_candidate_date": "2025-03-10",
                    "latest_candidate_date": "2025-03-10",
                    "best_lead_days": 2,
                    "has_exact_same_day_candidate": 0,
                    "has_lead_1_to_3_candidate": 1,
                    "has_lead_4_to_7_candidate": 0,
                }
            ]
        )
        episode_matches.to_csv(
            share_dir / "common_cause_precursor_episode_matches_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )

        panel_rows: list[dict[str, object]] = []
        add_background_window(
            panel_rows,
            [
                "2025-03-03",
                "2025-03-04",
                "2025-03-05",
                "2025-03-06",
                "2025-03-07",
                "2025-03-08",
                "2025-03-09",
                "2025-03-11",
                "2025-03-13",
                "2025-03-14",
                "2025-03-15",
                "2025-03-16",
                "2025-03-17",
                "2025-03-18",
                "2025-03-19",
                "2025-03-22",
                "2025-03-23",
                "2025-03-24",
                "2025-03-25",
                "2025-03-26",
                "2025-03-27",
                "2025-03-28",
                "2025-03-29",
                "2025-03-31",
                "2025-04-01",
                "2025-04-02",
                "2025-04-03",
                "2025-04-04",
                "2025-04-05",
                "2025-04-06",
            ],
            total_rows=10,
        )
        make_day(panel_rows, "2025-03-10", total_rows=10, qualifying_groups=[("lead.a", 2)])
        make_day(panel_rows, "2025-03-12", total_rows=10, qualifying_groups=[("exact.a", 3)])
        make_day(panel_rows, "2025-03-20", total_rows=10, qualifying_groups=[("persist.a", 2)])
        make_day(panel_rows, "2025-03-21", total_rows=10, qualifying_groups=[("persist.b", 2)])
        make_day(panel_rows, "2025-03-30", total_rows=80, qualifying_groups=[("sparse.a", 3)])

        panel_df = pd.DataFrame(panel_rows)
        panel_df.to_csv(data_dir / "panel_day_core.csv", index=False, encoding="utf-8-sig")

        run_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(run_res.returncode == 0, f"script failed:\n{run_res.stdout}\n{run_res.stderr}")

        summary_df = pd.read_csv(share_dir / "common_cause_precursor_case_forensics_summary_v1.csv", encoding="utf-8-sig")
        days_df = pd.read_csv(share_dir / "common_cause_precursor_case_forensics_days_v1.csv", encoding="utf-8-sig")
        groups_df = pd.read_csv(share_dir / "common_cause_precursor_case_forensics_groups_v1.csv", encoding="utf-8-sig")

        assert_true(not summary_df.empty, "summary output is empty")
        assert_true(not days_df.empty, "day output is empty")
        assert_true(not groups_df.empty, "group output is empty")

        expected_dates = {"2025-03-10", "2025-03-12", "2025-03-20", "2025-03-21", "2025-03-30"}
        assert_true(set(days_df["date"]) == expected_dates, "unique site/date universe should be preserved exactly")

        plausible_row = days_df.loc[days_df["date"].eq("2025-03-10")].iloc[0]
        assert_true(
            plausible_row["forensic_hypothesis"] == "plausible_precursor_day",
            "synthetic lead_1_to_3 + stable local baseline should become plausible_precursor_day",
        )

        exact_row = days_df.loc[days_df["date"].eq("2025-03-12")].iloc[0]
        assert_true(
            exact_row["forensic_hypothesis"] == "episode_aligned_day",
            "synthetic exact_same_day_episode should become episode_aligned_day",
        )

        persistent_rows = days_df.loc[days_df["date"].isin(["2025-03-20", "2025-03-21"])]
        assert_true(
            persistent_rows["forensic_hypothesis"].eq("likely_persistent_site_pattern").all(),
            "synthetic no_episode_within_7d + 2-day run should become likely_persistent_site_pattern",
        )

        sparse_row = days_df.loc[days_df["date"].eq("2025-03-30")].iloc[0]
        assert_true(
            sparse_row["forensic_hypothesis"] == "likely_sparse_site_pattern",
            "synthetic sparse day should become likely_sparse_site_pattern",
        )

        lead_group_top = groups_df.loc[groups_df["date"].eq("2025-03-10")].sort_values("rank_by_group_like_zero_like_count").iloc[0]
        assert_true(
            lead_group_top["fallback_group_proxy"] == "lead.a",
            "top-ranked lead day group should match the qualifying proxy",
        )

        print("[OK] outputs generate")
        print("[OK] unique site/date universe is preserved exactly")
        print("[OK] synthetic lead_1_to_3 + stable local baseline becomes plausible_precursor_day")
        print("[OK] synthetic exact_same_day_episode becomes episode_aligned_day")
        print("[OK] synthetic no_episode_within_7d + 2-day run becomes likely_persistent_site_pattern")
        print("[OK] synthetic sparse day becomes likely_sparse_site_pattern")
        print("[OK] no official outputs are modified")

    safe_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(safe_res.returncode == 0, f"existing safe smoke failed:\n{safe_res.stdout}\n{safe_res.stderr}")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
