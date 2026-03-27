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


def make_rows(panel_id: str, strict_date: str, pattern: str) -> pd.DataFrame:
    strict_dt = pd.Timestamp(strict_date)
    dates = pd.date_range(strict_dt - pd.Timedelta(days=7), strict_dt + pd.Timedelta(days=7), freq="D")
    rows: list[dict[str, object]] = []
    for i, date_dt in enumerate(dates):
        base = {
            "date": date_dt.date().isoformat(),
            "panel_id": panel_id,
            "mid_ratio": 0.95,
            "last_ratio": 0.95,
            "mid_v_ratio": 0.95,
            "mid_i_ratio": 0.95,
            "v_drop": 0.10,
            "v_ref_ok": True,
            "coverage_mid": 1.0,
            "shadow_like": False,
            "group_off_like": False,
        }
        if pattern == "diode" and date_dt == strict_dt - pd.Timedelta(days=1):
            base.update({"mid_ratio": 0.70, "last_ratio": 0.71, "mid_v_ratio": 0.60, "mid_i_ratio": 0.96, "v_drop": 0.35})
        elif pattern == "open" and date_dt == strict_dt + pd.Timedelta(days=1):
            base.update({"mid_ratio": 0.05, "last_ratio": 0.05, "mid_v_ratio": 0.05, "mid_i_ratio": 0.70, "v_drop": 0.98})
        elif pattern == "group" and date_dt == strict_dt:
            base.update({"mid_ratio": 0.05, "last_ratio": 0.05, "mid_v_ratio": 1.10, "mid_i_ratio": 0.05, "v_drop": 0.40})
        elif pattern == "weak" and date_dt == strict_dt:
            base.update({"mid_ratio": 0.85, "last_ratio": 0.85, "mid_v_ratio": 0.88, "mid_i_ratio": 0.88, "v_drop": 0.20, "shadow_like": True})
        rows.append(base)
    return pd.DataFrame(rows)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_critical_phenotype_shadow.py"
    smoke_weather = root / "research" / "prognostics" / "smoke_test_site_weather_history.py"
    smoke_event = root / "research" / "prognostics" / "smoke_test_site_event_dataset.py"
    smoke_frame = root / "research" / "prognostics" / "smoke_test_site_day_event_frame.py"
    smoke_episode = root / "research" / "prognostics" / "smoke_test_site_day_alert_episodes.py"
    smoke_onset = root / "research" / "prognostics" / "smoke_test_panel_onset_shadow.py"
    smoke_vendor = root / "research" / "prognostics" / "smoke_test_vendor_reply_adjudication.py"
    smoke_field = root / "research" / "prognostics" / "smoke_test_field_truth_validation.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        out_dir = tmp_root / "data" / "demo" / "out"
        share_dir.mkdir(parents=True, exist_ok=True)
        out_dir.mkdir(parents=True, exist_ok=True)

        onset_df = pd.DataFrame(
            [
                {"site": "demo", "panel_id": "p_diode", "strict_trigger_date": "2025-03-10", "first_warning_date": "2025-03-08", "retrospective_onset_date": "2025-03-08", "days_earlier_than_trigger": 2, "onset_confidence": "high", "onset_method": "persistent_5of7", "reason_summary": "strict_method=critical_fault_flag|demo"},
                {"site": "demo", "panel_id": "p_open", "strict_trigger_date": "2025-03-10", "first_warning_date": "2025-03-10", "retrospective_onset_date": "2025-03-10", "days_earlier_than_trigger": 0, "onset_confidence": "medium", "onset_method": "persistent_5of7", "reason_summary": "strict_method=critical_fault_flag|demo"},
                {"site": "demo", "panel_id": "p_group", "strict_trigger_date": "2025-03-10", "first_warning_date": "2025-03-10", "retrospective_onset_date": "2025-03-10", "days_earlier_than_trigger": 0, "onset_confidence": "medium", "onset_method": "persistent_5of7", "reason_summary": "strict_method=critical_fault_flag|demo"},
                {"site": "demo", "panel_id": "p_weak", "strict_trigger_date": "2025-03-10", "first_warning_date": "2025-03-10", "retrospective_onset_date": "2025-03-10", "days_earlier_than_trigger": 0, "onset_confidence": "low", "onset_method": "strict_trigger_fallback", "reason_summary": "strict_method=critical_fault_flag|demo"},
                {"site": "demo", "panel_id": "p_noncritical", "strict_trigger_date": "2025-03-10", "first_warning_date": "2025-03-10", "retrospective_onset_date": "2025-03-10", "days_earlier_than_trigger": 0, "onset_confidence": "low", "onset_method": "strict_trigger_fallback", "reason_summary": "strict_method=confirmed_fault_flag|demo"},
            ]
        )
        onset_df.to_csv(share_dir / "panel_onset_shadow_latest.csv", index=False, encoding="utf-8-sig")

        vendor_df = pd.DataFrame(
            [
                {"site": "demo", "panel_id": "p_diode", "vendor_reply_class": "field_confirmed_positive", "vendor_fault_family": "module", "field_confirmed_flag": 1, "adjudication_weight": 1.0, "vendor_note": "x", "strict_trigger_date": "2025-03-10", "first_warning_date": "2025-03-08", "retrospective_onset_date": "2025-03-08", "days_earlier_than_trigger": 2, "onset_confidence": "high", "onset_method": "persistent_5of7", "reason_summary": "strict_method=critical_fault_flag|demo", "panel_found_in_ours": 1, "dispute_type": "agree_positive"},
                {"site": "demo", "panel_id": "p_open", "vendor_reply_class": "vendor_likely_positive", "vendor_fault_family": "device", "field_confirmed_flag": 0, "adjudication_weight": 0.8, "vendor_note": "x", "strict_trigger_date": "2025-03-10", "first_warning_date": "2025-03-10", "retrospective_onset_date": "2025-03-10", "days_earlier_than_trigger": 0, "onset_confidence": "medium", "onset_method": "persistent_5of7", "reason_summary": "strict_method=critical_fault_flag|demo", "panel_found_in_ours": 1, "dispute_type": "agree_positive"},
            ]
        )
        vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

        core_df = pd.concat(
            [
                make_rows("p_diode", "2025-03-10", "diode"),
                make_rows("p_open", "2025-03-10", "open"),
                make_rows("p_group", "2025-03-10", "group"),
                make_rows("p_weak", "2025-03-10", "weak"),
                make_rows("p_noncritical", "2025-03-10", "weak"),
            ],
            ignore_index=True,
        )
        core_df.to_csv(out_dir / "panel_day_core.csv", index=False, encoding="utf-8-sig")

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(build_res.returncode == 0, f"critical phenotype build failed:\n{build_res.stdout}\n{build_res.stderr}")

        latest = pd.read_csv(share_dir / "critical_phenotype_shadow_latest.csv", low_memory=False, encoding="utf-8-sig")
        summary = pd.read_csv(share_dir / "critical_phenotype_shadow_summary.csv", low_memory=False, encoding="utf-8-sig")
        matrix = pd.read_csv(share_dir / "critical_phenotype_vendor_matrix.csv", low_memory=False, encoding="utf-8-sig")

        assert_true(len(latest) == 4, "no new candidates should be created and noncritical rows should be excluded")
        assert_true(set(latest["panel_id"]) == {"p_diode", "p_open", "p_group", "p_weak"}, "candidate conservation failed")

        by_panel = latest.set_index("panel_id")
        assert_true(by_panel.loc["p_diode", "anchor_date"] == "2025-03-09", "anchor selection should pick max-v_drop diode day")
        assert_true(by_panel.loc["p_diode", "critical_phenotype"] == "diode_or_module_damage_like", "diode case misclassified")
        assert_true(by_panel.loc["p_open", "critical_phenotype"] == "open_or_device_issue_like", "open case misclassified")
        assert_true(by_panel.loc["p_group", "critical_phenotype"] == "group_or_inverter_side_like", "group case misclassified")
        assert_true(by_panel.loc["p_weak", "critical_phenotype"] == "weak_critical_candidate", "weak case misclassified")

        assert_true(int(summary.iloc[0]["total_critical_cases"]) == 4, "summary total critical cases mismatch")
        assert_true(not matrix.empty, "vendor matrix should not be empty when vendor rows exist")

    smoke_weather_res = run([sys.executable, str(smoke_weather)], root)
    assert_true(smoke_weather_res.returncode == 0, f"weather smoke failed:\n{smoke_weather_res.stdout}\n{smoke_weather_res.stderr}")
    smoke_event_res = run([sys.executable, str(smoke_event)], root)
    assert_true(smoke_event_res.returncode == 0, f"site event smoke failed:\n{smoke_event_res.stdout}\n{smoke_event_res.stderr}")
    smoke_frame_res = run([sys.executable, str(smoke_frame)], root)
    assert_true(smoke_frame_res.returncode == 0, f"site day frame smoke failed:\n{smoke_frame_res.stdout}\n{smoke_frame_res.stderr}")
    smoke_episode_res = run([sys.executable, str(smoke_episode)], root)
    assert_true(smoke_episode_res.returncode == 0, f"episode smoke failed:\n{smoke_episode_res.stdout}\n{smoke_episode_res.stderr}")
    smoke_onset_res = run([sys.executable, str(smoke_onset)], root)
    assert_true(smoke_onset_res.returncode == 0, f"onset smoke failed:\n{smoke_onset_res.stdout}\n{smoke_onset_res.stderr}")
    smoke_vendor_res = run([sys.executable, str(smoke_vendor)], root)
    assert_true(smoke_vendor_res.returncode == 0, f"vendor adjudication smoke failed:\n{smoke_vendor_res.stdout}\n{smoke_vendor_res.stderr}")
    smoke_field_res = run([sys.executable, str(smoke_field)], root)
    assert_true(smoke_field_res.returncode == 0, f"field truth smoke failed:\n{smoke_field_res.stdout}\n{smoke_field_res.stderr}")

    print("[OK] scripts compile")
    print("[OK] no new candidates are created")
    print("[OK] local peak anchor selection works on synthetic fixtures")
    print("[OK] obvious synthetic diode/open/group cases are classified as expected")
    print("[OK] existing weather/event/frame/episode/onset/adjudication smoke paths still pass")


if __name__ == "__main__":
    main()
