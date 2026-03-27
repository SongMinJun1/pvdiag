#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


VALID_DISPUTE_TYPES = {
    "agree_positive",
    "agree_group_issue",
    "ours_positive_vendor_rejected",
    "ours_positive_vendor_no_info",
    "vendor_positive_not_in_ours",
    "needs_date_anchor_review",
}


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def parse_counts(text: str) -> dict[str, int]:
    if not text:
        return {}
    counts: dict[str, int] = {}
    for part in str(text).split("|"):
        if not part:
            continue
        key, value = part.rsplit(":", 1)
        counts[key] = int(value)
    return counts


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_vendor_reply_adjudication.py"
    smoke_weather = root / "research" / "prognostics" / "smoke_test_site_weather_history.py"
    smoke_event = root / "research" / "prognostics" / "smoke_test_site_event_dataset.py"
    smoke_frame = root / "research" / "prognostics" / "smoke_test_site_day_event_frame.py"
    smoke_episode = root / "research" / "prognostics" / "smoke_test_site_day_alert_episodes.py"
    smoke_onset = root / "research" / "prognostics" / "smoke_test_panel_onset_shadow.py"
    smoke_field = root / "research" / "prognostics" / "smoke_test_field_truth_validation.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        manual_dir = tmp_root / "data" / "manual"
        share_dir.mkdir(parents=True, exist_ok=True)
        manual_dir.mkdir(parents=True, exist_ok=True)

        onset_df = pd.DataFrame(
            [
                {"site": "demo", "panel_id": "p1", "strict_trigger_date": "2025-01-10", "first_warning_date": "2025-01-05", "retrospective_onset_date": "2025-01-05", "days_earlier_than_trigger": 5, "onset_confidence": "high", "onset_method": "persistent_5of7", "reason_summary": "demo1"},
                {"site": "demo", "panel_id": "p2", "strict_trigger_date": "2025-01-11", "first_warning_date": "2025-01-08", "retrospective_onset_date": "2025-01-08", "days_earlier_than_trigger": 3, "onset_confidence": "medium", "onset_method": "persistent_5of7", "reason_summary": "demo2"},
                {"site": "demo", "panel_id": "p3", "strict_trigger_date": "2025-01-12", "first_warning_date": "2025-01-12", "retrospective_onset_date": "2025-01-12", "days_earlier_than_trigger": 0, "onset_confidence": "medium", "onset_method": "strict_trigger_fallback", "reason_summary": "demo3"},
                {"site": "demo", "panel_id": "p4", "strict_trigger_date": "2025-01-13", "first_warning_date": "2025-01-13", "retrospective_onset_date": "2025-01-13", "days_earlier_than_trigger": 0, "onset_confidence": "low", "onset_method": "strict_trigger_fallback_confound", "reason_summary": "demo4"},
            ]
        )
        onset_df.to_csv(share_dir / "panel_onset_shadow_latest.csv", index=False, encoding="utf-8-sig")

        vendor_df = pd.DataFrame(
            [
                {"site": "demo", "panel_id": "p1", "vendor_reply_class": "field_confirmed_positive", "vendor_fault_family": "electrical", "field_confirmed_flag": 1, "adjudication_weight": 1.0, "vendor_note": "confirmed"},
                {"site": "demo", "panel_id": "p2", "vendor_reply_class": "vendor_pattern_positive", "vendor_fault_family": "group_pattern", "field_confirmed_flag": 0, "adjudication_weight": 0.8, "vendor_note": "pattern"},
                {"site": "demo", "panel_id": "p3", "vendor_reply_class": "vendor_rejected", "vendor_fault_family": "none", "field_confirmed_flag": 0, "adjudication_weight": 0.6, "vendor_note": "reject"},
                {"site": "demo", "panel_id": "p4", "vendor_reply_class": "vendor_no_info", "vendor_fault_family": "unknown", "field_confirmed_flag": 0, "adjudication_weight": 0.2, "vendor_note": "no info"},
                {"site": "demo", "panel_id": "p_missing", "vendor_reply_class": "vendor_likely_positive", "vendor_fault_family": "shape", "field_confirmed_flag": 0, "adjudication_weight": 0.5, "vendor_note": "missing in ours"},
                {"site": "demo", "panel_id": "p_missing_2", "vendor_reply_class": "vendor_rejected", "vendor_fault_family": "none", "field_confirmed_flag": 0, "adjudication_weight": 0.4, "vendor_note": "needs anchor review"},
            ]
        )
        vendor_df.to_csv(manual_dir / "vendor_reply_cases.csv", index=False, encoding="utf-8-sig")

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(build_res.returncode == 0, f"adjudication build failed:\n{build_res.stdout}\n{build_res.stderr}")

        latest = pd.read_csv(share_dir / "vendor_reply_adjudication_latest.csv", low_memory=False, encoding="utf-8-sig")
        summary = pd.read_csv(share_dir / "vendor_reply_confusion_summary.csv", low_memory=False, encoding="utf-8-sig")
        disputes = pd.read_csv(share_dir / "vendor_reply_disputes.csv", low_memory=False, encoding="utf-8-sig")

        assert_true(len(latest) == len(vendor_df), "join did not preserve vendor reply rows")
        assert_true(set(latest["dispute_type"]).issubset(VALID_DISPUTE_TYPES), "invalid dispute_type emitted")

        by_panel = latest.set_index("panel_id")
        assert_true(by_panel.loc["p1", "dispute_type"] == "agree_positive", "p1 should agree positive")
        assert_true(by_panel.loc["p2", "dispute_type"] == "agree_group_issue", "p2 should agree as group issue")
        assert_true(by_panel.loc["p3", "dispute_type"] == "ours_positive_vendor_rejected", "p3 should be ours_positive_vendor_rejected")
        assert_true(by_panel.loc["p4", "dispute_type"] == "ours_positive_vendor_no_info", "p4 should be ours_positive_vendor_no_info")
        assert_true(by_panel.loc["p_missing", "dispute_type"] == "vendor_positive_not_in_ours", "missing positive should map to vendor_positive_not_in_ours")
        assert_true(by_panel.loc["p_missing_2", "dispute_type"] == "needs_date_anchor_review", "missing rejected should need date anchor review")

        summary_row = summary.iloc[0]
        assert_true(int(summary_row["total_rows"]) == len(vendor_df), "summary total_rows mismatch")
        assert_true(int(summary_row["matched_rows"]) == int(latest["panel_found_in_ours"].eq(1).sum()), "summary matched_rows mismatch")
        assert_true(int(summary_row["unmatched_rows"]) == int(latest["panel_found_in_ours"].eq(0).sum()), "summary unmatched_rows mismatch")
        assert_true(sum(parse_counts(summary_row["count_by_dispute_type"]).values()) == len(vendor_df), "dispute summary counts inconsistent")
        assert_true(sum(parse_counts(summary_row["count_by_vendor_reply_class"]).values()) == len(vendor_df), "vendor class summary counts inconsistent")
        assert_true(not disputes.empty, "disputes file should not be empty for synthetic disagreements")

    smoke_weather_res = run([sys.executable, str(smoke_weather)], root)
    assert_true(smoke_weather_res.returncode == 0, f"weather smoke failed:\n{smoke_weather_res.stdout}\n{smoke_weather_res.stderr}")

    smoke_event_res = run([sys.executable, str(smoke_event)], root)
    assert_true(smoke_event_res.returncode == 0, f"site event dataset smoke failed:\n{smoke_event_res.stdout}\n{smoke_event_res.stderr}")

    smoke_frame_res = run([sys.executable, str(smoke_frame)], root)
    assert_true(smoke_frame_res.returncode == 0, f"site-day frame smoke failed:\n{smoke_frame_res.stdout}\n{smoke_frame_res.stderr}")

    smoke_episode_res = run([sys.executable, str(smoke_episode)], root)
    assert_true(smoke_episode_res.returncode == 0, f"episode smoke failed:\n{smoke_episode_res.stdout}\n{smoke_episode_res.stderr}")

    smoke_onset_res = run([sys.executable, str(smoke_onset)], root)
    assert_true(smoke_onset_res.returncode == 0, f"onset shadow smoke failed:\n{smoke_onset_res.stdout}\n{smoke_onset_res.stderr}")

    smoke_field_res = run([sys.executable, str(smoke_field)], root)
    assert_true(smoke_field_res.returncode == 0, f"field truth smoke failed:\n{smoke_field_res.stdout}\n{smoke_field_res.stderr}")

    print("[OK] outputs generate when manual CSV exists")
    print("[OK] joins preserve vendor reply rows")
    print("[OK] dispute_type values valid")
    print("[OK] summary counts are consistent")
    print("[OK] existing weather/event/frame/episode/onset shadow smoke paths still pass")


if __name__ == "__main__":
    main()
