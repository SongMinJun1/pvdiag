#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd


TRUTH_TEMPLATE_COLS = [
    "site",
    "episode_id",
    "episode_start_date",
    "episode_end_date",
    "matched_review_group",
    "our_interpretation",
    "field_issue_detected_date",
    "field_issue_started_estimated_date",
    "actual_issue_type",
    "actual_primary_view",
    "action_taken",
    "episode_match_manual",
    "note",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def overlaps_any(site: str, start: pd.Timestamp, end: pd.Timestamp, high_df: pd.DataFrame) -> bool:
    subset = high_df.loc[high_df["site"].eq(site)]
    if subset.empty:
        return False
    return bool(((subset["start_dt"] <= end) & (subset["end_dt"] >= start)).any())


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    share_dir = root / "_share"

    build_script = root / "research" / "prognostics" / "build_episode_review_pack.py"
    smoke_weather = root / "research" / "prognostics" / "smoke_test_site_weather_history.py"
    smoke_event = root / "research" / "prognostics" / "smoke_test_site_event_dataset.py"
    smoke_frame = root / "research" / "prognostics" / "smoke_test_site_day_event_frame.py"
    smoke_episode = root / "research" / "prognostics" / "smoke_test_site_day_alert_episodes.py"
    smoke_field = root / "research" / "prognostics" / "smoke_test_field_truth_validation.py"

    build_res = run([sys.executable, str(build_script)], root)
    assert_true(build_res.returncode == 0, f"episode review pack build failed:\n{build_res.stdout}\n{build_res.stderr}")

    pack_path = share_dir / "episode_review_pack_latest.csv"
    truth_path = share_dir / "episode_truth_template.csv"
    summary_path = share_dir / "episode_review_summary.csv"
    episodes_path = share_dir / "site_day_alert_episodes_latest.csv"

    assert_true(pack_path.exists(), "episode_review_pack_latest.csv was not generated")
    assert_true(truth_path.exists(), "episode_truth_template.csv was not generated")
    assert_true(summary_path.exists(), "episode_review_summary.csv was not generated")

    pack = pd.read_csv(pack_path, low_memory=False, encoding="utf-8-sig")
    truth = pd.read_csv(truth_path, low_memory=False, encoding="utf-8-sig")
    episodes = pd.read_csv(episodes_path, low_memory=False, encoding="utf-8-sig")

    for col in TRUTH_TEMPLATE_COLS:
        assert_true(col in truth.columns, f"episode_truth_template.csv missing column: {col}")
    assert_true(
        truth.duplicated(["site", "episode_id"]).sum() == 0,
        "episode_truth_template.csv has duplicate (site, episode_id)",
    )

    high = episodes.loc[episodes["trigger_mode"].astype(str).eq("high_only")].copy()
    medium = episodes.loc[episodes["trigger_mode"].astype(str).eq("medium_or_higher")].copy()
    selected_high = pack.loc[pack["trigger_mode"].astype(str).eq("high_only")].copy()
    selected_medium = pack.loc[pack["trigger_mode"].astype(str).eq("medium_or_higher")].copy()

    high["episode_id"] = high["episode_id"].astype(str).str.zfill(4)
    medium["episode_id"] = medium["episode_id"].astype(str).str.zfill(4)
    selected_high["episode_id"] = selected_high["episode_id"].astype(str).str.zfill(4)
    selected_medium["episode_id"] = selected_medium["episode_id"].astype(str).str.zfill(4)

    expected_high_keys = set(zip(high["site"], high["episode_id"]))
    selected_high_keys = set(zip(selected_high["site"], selected_high["episode_id"]))
    assert_true(expected_high_keys <= selected_high_keys, "not all high_only episodes were included in review pack")

    high["start_dt"] = pd.to_datetime(high["episode_start_date"], errors="coerce")
    high["end_dt"] = pd.to_datetime(high["episode_end_date"], errors="coerce")
    medium["start_dt"] = pd.to_datetime(medium["episode_start_date"], errors="coerce")
    medium["end_dt"] = pd.to_datetime(medium["episode_end_date"], errors="coerce")
    medium["overlaps_high"] = medium.apply(
        lambda row: overlaps_any(row["site"], row["start_dt"], row["end_dt"], high),
        axis=1,
    )
    expected_medium_keys = set(
        zip(
            medium.loc[~medium["overlaps_high"], "site"],
            medium.loc[~medium["overlaps_high"], "episode_id"],
        )
    )
    selected_medium_keys = set(zip(selected_medium["site"], selected_medium["episode_id"]))
    assert_true(
        selected_medium_keys == expected_medium_keys,
        "medium_or_higher selection does not match non-overlap de-duplication rule",
    )

    smoke_weather_res = run([sys.executable, str(smoke_weather)], root)
    assert_true(smoke_weather_res.returncode == 0, f"weather smoke failed:\n{smoke_weather_res.stdout}\n{smoke_weather_res.stderr}")

    smoke_event_res = run([sys.executable, str(smoke_event)], root)
    assert_true(smoke_event_res.returncode == 0, f"site event dataset smoke failed:\n{smoke_event_res.stdout}\n{smoke_event_res.stderr}")

    smoke_frame_res = run([sys.executable, str(smoke_frame)], root)
    assert_true(smoke_frame_res.returncode == 0, f"site-day frame smoke failed:\n{smoke_frame_res.stdout}\n{smoke_frame_res.stderr}")

    smoke_episode_res = run([sys.executable, str(smoke_episode)], root)
    assert_true(smoke_episode_res.returncode == 0, f"episode smoke failed:\n{smoke_episode_res.stdout}\n{smoke_episode_res.stderr}")

    smoke_field_res = run([sys.executable, str(smoke_field)], root)
    assert_true(smoke_field_res.returncode == 0, f"field truth smoke failed:\n{smoke_field_res.stdout}\n{smoke_field_res.stderr}")

    print("[OK] episode review outputs generated")
    print("[OK] all high_only episodes are included")
    print("[OK] overlapping medium_or_higher episodes are de-duplicated against high_only")
    print("[OK] episode truth template columns verified")
    print("[OK] episode truth template identifiers are unique per site")
    print("[OK] existing weather/event/frame/episode/truth smoke paths still pass")


if __name__ == "__main__":
    main()
