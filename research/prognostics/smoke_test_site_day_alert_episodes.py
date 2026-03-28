#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    share_dir = root / "_share"

    build_script = root / "research" / "prognostics" / "build_site_day_alert_episodes.py"
    smoke_weather = root / "research" / "prognostics" / "smoke_test_site_weather_history.py"
    smoke_frame = root / "research" / "prognostics" / "smoke_test_site_day_event_frame.py"
    smoke_event = root / "research" / "prognostics" / "smoke_test_site_event_dataset.py"
    smoke_field = root / "research" / "prognostics" / "smoke_test_field_truth_validation.py"

    build_res = run([sys.executable, str(build_script)], root)
    assert_true(build_res.returncode == 0, f"alert episode build failed:\n{build_res.stdout}\n{build_res.stderr}")

    episodes_path = share_dir / "site_day_alert_episodes_latest.csv"
    summary_path = share_dir / "site_day_alert_episode_summary.csv"
    risk_path = share_dir / "site_day_event_risk_latest.csv"

    assert_true(episodes_path.exists(), "site_day_alert_episodes_latest.csv was not generated")
    assert_true(summary_path.exists(), "site_day_alert_episode_summary.csv was not generated")

    episodes = pd.read_csv(episodes_path, low_memory=False, encoding="utf-8-sig")
    summary = pd.read_csv(summary_path, low_memory=False, encoding="utf-8-sig")
    risk = pd.read_csv(risk_path, low_memory=False, encoding="utf-8-sig")

    assert_true(
        episodes.duplicated(["site", "trigger_mode", "episode_id"]).sum() == 0,
        "site_day_alert_episodes_latest.csv has duplicate (site, trigger_mode, episode_id)",
    )

    for trigger_mode, risk_mask in {
        "high_only": risk["risk_band"].astype(str).eq("high"),
        "medium_or_higher": risk["risk_band"].astype(str).isin(["high", "medium"]),
    }.items():
        alert_days_by_site = (
            risk.loc[risk_mask].groupby("site", dropna=False)["date"].count().to_dict()
        )
        episode_counts_by_site = (
            episodes.loc[episodes["trigger_mode"].astype(str).eq(trigger_mode)]
            .groupby("site", dropna=False)["episode_id"]
            .count()
            .to_dict()
        )
        summary_subset = summary.loc[summary["trigger_mode"].astype(str).eq(trigger_mode)]
        for row in summary_subset.itertuples(index=False):
            alert_days = int(alert_days_by_site.get(row.site, 0))
            episode_count = int(episode_counts_by_site.get(row.site, 0))
            assert_true(int(row.alert_days) == alert_days, f"alert_days mismatch for {row.site}/{trigger_mode}")
            assert_true(int(row.total_episodes) == episode_count, f"total_episodes mismatch for {row.site}/{trigger_mode}")
            assert_true(int(row.total_episodes) <= int(row.alert_days), f"episodes exceed alert_days for {row.site}/{trigger_mode}")
            if int(row.total_episodes) == 0:
                assert_true(pd.isna(row.compression_ratio), f"compression_ratio must be blank/NaN for {row.site}/{trigger_mode} when total_episodes=0")
            elif int(row.alert_days) > int(row.total_episodes):
                assert_true(float(row.compression_ratio) > 1.0, f"compression_ratio must be > 1 for {row.site}/{trigger_mode} when alert_days > total_episodes")

    smoke_weather_res = run([sys.executable, str(smoke_weather)], root)
    assert_true(smoke_weather_res.returncode == 0, f"weather smoke failed:\n{smoke_weather_res.stdout}\n{smoke_weather_res.stderr}")

    smoke_frame_res = run([sys.executable, str(smoke_frame)], root)
    assert_true(smoke_frame_res.returncode == 0, f"site-day frame smoke failed:\n{smoke_frame_res.stdout}\n{smoke_frame_res.stderr}")

    smoke_event_res = run([sys.executable, str(smoke_event)], root)
    assert_true(smoke_event_res.returncode == 0, f"site event dataset smoke failed:\n{smoke_event_res.stdout}\n{smoke_event_res.stderr}")

    smoke_field_res = run([sys.executable, str(smoke_field)], root)
    assert_true(smoke_field_res.returncode == 0, f"field truth smoke failed:\n{smoke_field_res.stdout}\n{smoke_field_res.stderr}")

    print("[OK] site_day_alert_episodes_latest.csv generated")
    print("[OK] site_day_alert_episode_summary.csv generated")
    print("[OK] episode counts do not exceed alert_days")
    print("[OK] compression_ratio semantics verified")
    print("[OK] (site, trigger_mode, episode_id) uniqueness verified")
    print("[OK] existing weather/event/truth/site-day frame smoke paths still pass")


if __name__ == "__main__":
    main()
