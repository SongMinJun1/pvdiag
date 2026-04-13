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
    build_script = root / "research" / "prognostics" / "build_maintenance_proxy_event_overlap_audit_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_maintenance_proxy_cluster_audit_v1.py"

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
                    "member_panels": "a.0|a.1",
                    "representative_panel_id": "a.0",
                    "site_event_selected_count": 2,
                    "site_event_group_cluster_count": 1,
                    "cluster_interpretation": "concentrated_group_cluster",
                    "recommended_use": "common_cause_group_signal",
                },
                {
                    "site": "demo",
                    "strict_trigger_date": "2025-03-11",
                    "site_event_id": "demo:2025-03-11",
                    "group_cluster_id": "demo:2025-03-11:g2",
                    "fallback_group_proxy": "g2",
                    "member_panel_count": 2,
                    "member_panels": "b.0|b.1",
                    "representative_panel_id": "b.0",
                    "site_event_selected_count": 2,
                    "site_event_group_cluster_count": 1,
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
                    "member_panels": "c.0",
                    "representative_panel_id": "c.0",
                    "site_event_selected_count": 1,
                    "site_event_group_cluster_count": 1,
                    "cluster_interpretation": "singleton_cluster",
                    "recommended_use": "panel_level_review_signal",
                },
                {
                    "site": "demo",
                    "strict_trigger_date": "2025-03-20",
                    "site_event_id": "demo:2025-03-20",
                    "group_cluster_id": "demo:2025-03-20:g4",
                    "fallback_group_proxy": "g4",
                    "member_panel_count": 1,
                    "member_panels": "d.0",
                    "representative_panel_id": "d.0",
                    "site_event_selected_count": 1,
                    "site_event_group_cluster_count": 1,
                    "cluster_interpretation": "singleton_cluster",
                    "recommended_use": "panel_level_review_signal",
                },
            ]
        )
        clusters.to_csv(share_dir / "maintenance_proxy_cluster_audit_clusters_v1.csv", index=False, encoding="utf-8-sig")

        cases = pd.DataFrame(
            [
                {"site": "demo", "panel_id": "a.0", "strict_trigger_date": "2025-03-10", "site_event_id": "demo:2025-03-10", "group_cluster_id": "demo:2025-03-10:g1"},
                {"site": "demo", "panel_id": "a.1", "strict_trigger_date": "2025-03-10", "site_event_id": "demo:2025-03-10", "group_cluster_id": "demo:2025-03-10:g1"},
                {"site": "demo", "panel_id": "b.0", "strict_trigger_date": "2025-03-11", "site_event_id": "demo:2025-03-11", "group_cluster_id": "demo:2025-03-11:g2"},
                {"site": "demo", "panel_id": "b.1", "strict_trigger_date": "2025-03-11", "site_event_id": "demo:2025-03-11", "group_cluster_id": "demo:2025-03-11:g2"},
                {"site": "demo", "panel_id": "c.0", "strict_trigger_date": "2025-03-12", "site_event_id": "demo:2025-03-12", "group_cluster_id": "demo:2025-03-12:g3"},
                {"site": "demo", "panel_id": "d.0", "strict_trigger_date": "2025-03-20", "site_event_id": "demo:2025-03-20", "group_cluster_id": "demo:2025-03-20:g4"},
            ]
        )
        cases_csv_before = cases.to_csv(index=False)
        cases.to_csv(share_dir / "maintenance_proxy_cluster_audit_cases_v1.csv", index=False, encoding="utf-8-sig")

        frame = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "date": "2025-03-10",
                    "event_day_flag": 1,
                },
                {
                    "site": "demo",
                    "date": "2025-03-11",
                    "event_day_flag": 0,
                },
                {
                    "site": "demo",
                    "date": "2025-03-12",
                    "event_day_flag": 0,
                },
                {
                    "site": "demo",
                    "date": "2025-03-20",
                    "event_day_flag": 0,
                },
            ]
        )
        frame.to_csv(share_dir / "site_day_event_frame_latest.csv", index=False, encoding="utf-8-sig")

        episodes = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "trigger_mode": "high_only",
                    "episode_id": "ep_window",
                    "episode_start_date": "2025-03-11",
                    "episode_end_date": "2025-03-11",
                },
                {
                    "site": "demo",
                    "trigger_mode": "high_only",
                    "episode_id": "ep_lead",
                    "episode_start_date": "2025-03-14",
                    "episode_end_date": "2025-03-16",
                },
            ]
        )
        episodes.to_csv(share_dir / "site_day_alert_episodes_latest.csv", index=False, encoding="utf-8-sig")

        event_dataset = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "representative_date": "2025-03-10",
                    "event_start_date": "2025-03-10",
                    "event_end_date": "2025-03-10",
                    "event_confidence_level": "high",
                    "weather_confound_flag": 0,
                }
            ]
        )
        event_dataset.to_csv(share_dir / "site_event_dataset_latest.csv", index=False, encoding="utf-8-sig")

        run_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(run_res.returncode == 0, f"script failed:\n{run_res.stdout}\n{run_res.stderr}")

        summary_df = pd.read_csv(share_dir / "maintenance_proxy_event_overlap_summary_v1.csv", encoding="utf-8-sig")
        clusters_df = pd.read_csv(share_dir / "maintenance_proxy_event_overlap_clusters_v1.csv", encoding="utf-8-sig")
        matches_df = pd.read_csv(share_dir / "maintenance_proxy_event_overlap_matches_v1.csv", encoding="utf-8-sig")

        assert_true(not summary_df.empty, "summary output is empty")
        assert_true(not clusters_df.empty, "cluster output is empty")
        assert_true(not matches_df.empty, "matches output is empty")
        assert_true(len(clusters_df) == len(clusters), "selected cluster universe must be preserved exactly")
        assert_true(set(clusters_df["group_cluster_id"]) == set(clusters["group_cluster_id"]), "output clusters must match input cluster universe")

        exact_row = clusters_df.loc[clusters_df["group_cluster_id"].eq("demo:2025-03-10:g1")].iloc[0]
        assert_true(exact_row["overlap_type"] == "exact_frame_event_overlap", "same-day frame event should become exact_frame_event_overlap")

        window_row = clusters_df.loc[clusters_df["group_cluster_id"].eq("demo:2025-03-11:g2")].iloc[0]
        assert_true(window_row["overlap_type"] == "episode_window_overlap", "episode-window case should become episode_window_overlap")

        lead_row = clusters_df.loc[clusters_df["group_cluster_id"].eq("demo:2025-03-12:g3")].iloc[0]
        assert_true(lead_row["overlap_type"] == "lead_before_episode", "lead-before-episode case should become lead_before_episode")

        none_row = clusters_df.loc[clusters_df["group_cluster_id"].eq("demo:2025-03-20:g4")].iloc[0]
        assert_true(none_row["overlap_type"] == "no_existing_event_overlap", "no-overlap case should become no_existing_event_overlap")

        cases_csv_after = (share_dir / "maintenance_proxy_cluster_audit_cases_v1.csv").read_text(encoding="utf-8-sig")
        assert_true(cases_csv_after == cases_csv_before, "official cluster-audit case input must not be modified")

        print("[OK] outputs generate")
        print("[OK] selected cluster universe is preserved exactly")
        print("[OK] synthetic exact same-day frame event becomes exact_frame_event_overlap")
        print("[OK] synthetic episode-window case becomes episode_window_overlap")
        print("[OK] synthetic lead-before-episode case becomes lead_before_episode")
        print("[OK] synthetic no-overlap case becomes no_existing_event_overlap")
        print("[OK] no official prediction outputs are modified")

    safe_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(safe_res.returncode == 0, f"existing safe smoke failed:\n{safe_res.stdout}\n{safe_res.stderr}")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
