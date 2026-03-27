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


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_maintenance_proxy_event_timing_audit_v2.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_maintenance_proxy_event_overlap_audit_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        share_dir.mkdir(parents=True, exist_ok=True)

        clusters = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "strict_trigger_date": "2025-03-10",
                    "site_event_id": "demo:2025-03-10",
                    "group_cluster_id": "demo:2025-03-10:g1",
                    "fallback_group_proxy": "g1",
                    "member_panel_count": 2,
                    "cluster_interpretation": "concentrated_group_cluster",
                    "recommended_use": "common_cause_group_signal",
                },
                {
                    "site": "demo",
                    "strict_trigger_date": "2025-03-08",
                    "site_event_id": "demo:2025-03-08",
                    "group_cluster_id": "demo:2025-03-08:g2",
                    "fallback_group_proxy": "g2",
                    "member_panel_count": 2,
                    "cluster_interpretation": "concentrated_group_cluster",
                    "recommended_use": "common_cause_group_signal",
                },
                {
                    "site": "demo",
                    "strict_trigger_date": "2025-03-12",
                    "site_event_id": "demo:2025-03-12",
                    "group_cluster_id": "demo:2025-03-12:g3",
                    "fallback_group_proxy": "g3",
                    "member_panel_count": 1,
                    "cluster_interpretation": "singleton_cluster",
                    "recommended_use": "panel_level_review_signal",
                },
                {
                    "site": "demo",
                    "strict_trigger_date": "2025-03-15",
                    "site_event_id": "demo:2025-03-15",
                    "group_cluster_id": "demo:2025-03-15:g4",
                    "fallback_group_proxy": "g4",
                    "member_panel_count": 1,
                    "cluster_interpretation": "singleton_cluster",
                    "recommended_use": "panel_level_review_signal",
                },
            ]
        )
        clusters_csv_before = clusters.to_csv(index=False)
        clusters.to_csv(share_dir / "maintenance_proxy_event_overlap_clusters_v1.csv", index=False, encoding="utf-8-sig")

        frame = pd.DataFrame(
            [
                {"site": "demo", "date": "2025-03-10", "event_today": 1, "event_within_7d": 1},
                {"site": "demo", "date": "2025-03-08", "event_today": 0, "event_within_7d": 1},
                {"site": "demo", "date": "2025-03-12", "event_today": 0, "event_within_7d": 0},
                {"site": "demo", "date": "2025-03-15", "event_today": 0, "event_within_7d": 0},
            ]
        )
        frame.to_csv(share_dir / "site_day_event_frame_latest.csv", index=False, encoding="utf-8-sig")

        episodes = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "trigger_mode": "high_only",
                    "episode_id": "ep_lead",
                    "episode_start_date": "2025-03-14",
                    "episode_end_date": "2025-03-16",
                },
                {
                    "site": "demo",
                    "trigger_mode": "high_only",
                    "episode_id": "ep_window",
                    "episode_start_date": "2025-03-14",
                    "episode_end_date": "2025-03-16",
                },
            ]
        )
        episodes.to_csv(share_dir / "site_day_alert_episodes_latest.csv", index=False, encoding="utf-8-sig")

        run_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(run_res.returncode == 0, f"script failed:\n{run_res.stdout}\n{run_res.stderr}")

        summary_df = pd.read_csv(share_dir / "maintenance_proxy_event_timing_summary_v2.csv", encoding="utf-8-sig")
        clusters_df = pd.read_csv(share_dir / "maintenance_proxy_event_timing_clusters_v2.csv", encoding="utf-8-sig")
        matches_df = pd.read_csv(share_dir / "maintenance_proxy_event_timing_matches_v2.csv", encoding="utf-8-sig")

        assert_true(not summary_df.empty, "summary output is empty")
        assert_true(not clusters_df.empty, "cluster output is empty")
        assert_true(not matches_df.empty, "matches output is empty")
        assert_true(len(clusters_df) == len(clusters), "cluster universe must be preserved exactly")
        assert_true(set(clusters_df["group_cluster_id"]) == set(clusters["group_cluster_id"]), "output clusters must match input universe")

        exact_row = clusters_df.loc[clusters_df["group_cluster_id"].eq("demo:2025-03-10:g1")].iloc[0]
        assert_true(exact_row["timing_overlap_type"] == "exact_same_day_event_overlap", "synthetic exact same-day event should stay exact_same_day_event_overlap")

        window_row = clusters_df.loc[clusters_df["group_cluster_id"].eq("demo:2025-03-08:g2")].iloc[0]
        assert_true(window_row["timing_overlap_type"] == "within_frame_window_only", "event_within_7d-only case should become within_frame_window_only")
        assert_true(int(window_row["exact_same_day_event_flag"]) == 0, "event_within_7d-only case must not be marked exact")

        lead_row = clusters_df.loc[clusters_df["group_cluster_id"].eq("demo:2025-03-12:g3")].iloc[0]
        assert_true(lead_row["timing_overlap_type"] == "lead_before_episode", "synthetic +2 day episode case should become lead_before_episode")

        in_window_row = clusters_df.loc[clusters_df["group_cluster_id"].eq("demo:2025-03-15:g4")].iloc[0]
        assert_true(in_window_row["timing_overlap_type"] == "episode_window_overlap", "synthetic in-window case should become episode_window_overlap")

        clusters_csv_after = (share_dir / "maintenance_proxy_event_overlap_clusters_v1.csv").read_text(encoding="utf-8-sig")
        assert_true(clusters_csv_after == clusters_csv_before, "official overlap-v1 cluster input must not be modified")

        print("[OK] outputs generate")
        print("[OK] synthetic exact same-day event stays exact_same_day_event_overlap")
        print("[OK] synthetic event_within_7d-only case becomes within_frame_window_only, not exact")
        print("[OK] synthetic +2 day episode case becomes lead_before_episode")
        print("[OK] synthetic in-window case becomes episode_window_overlap")
        print("[OK] no official prediction outputs are modified")

    safe_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(safe_res.returncode == 0, f"existing safe smoke failed:\n{safe_res.stdout}\n{safe_res.stderr}")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
