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


def make_panel_rows(panel_id: str, strict_date: str, start: str, end: str, case_kind: str) -> pd.DataFrame:
    dates = pd.date_range(start, end, freq="D")
    strict_dt = pd.Timestamp(strict_date)
    rows: list[dict[str, object]] = []
    for date_dt in dates:
        mid_ratio = 1.0
        last_ratio = 1.0
        v_drop = 0.0
        coverage_mid = 1.0
        shadow_like = False
        group_off_like = False
        recon_error = 0.001

        if case_kind == "abrupt":
            if date_dt >= strict_dt:
                mid_ratio = 0.80
                last_ratio = 0.82
                v_drop = 0.14
                recon_error = 0.05
        elif case_kind == "gradual":
            if strict_dt - pd.Timedelta(days=14) <= date_dt <= strict_dt:
                progress = max(0.0, min(1.0, (date_dt - (strict_dt - pd.Timedelta(days=14))).days / 14.0))
                mid_ratio = 0.97 - 0.08 * progress
                last_ratio = 0.97 - 0.07 * progress
                v_drop = 0.03 + 0.04 * progress
                recon_error = 0.01 + 0.02 * progress
        elif case_kind == "recovery_break":
            if strict_dt - pd.Timedelta(days=40) <= date_dt <= strict_dt - pd.Timedelta(days=30):
                mid_ratio = 0.90
                last_ratio = 0.91
                v_drop = 0.08
                recon_error = 0.03
            if strict_dt - pd.Timedelta(days=8) <= date_dt <= strict_dt:
                mid_ratio = 0.88
                last_ratio = 0.89
                v_drop = 0.09
                recon_error = 0.04
        elif case_kind == "confounded":
            if strict_dt - pd.Timedelta(days=18) <= date_dt <= strict_dt:
                mid_ratio = 0.90
                last_ratio = 0.91
                v_drop = 0.07
                recon_error = 0.03
                shadow_like = True
                group_off_like = True
        else:
            raise ValueError(case_kind)

        rows.append(
            {
                "date": date_dt.date().isoformat(),
                "panel_id": panel_id,
                "mid_ratio": mid_ratio,
                "last_ratio": last_ratio,
                "v_drop": v_drop,
                "v_ref_ok": True,
                "coverage_mid": coverage_mid,
                "shadow_like": shadow_like,
                "group_off_like": group_off_like,
                "recon_error": recon_error,
                "confirmed_fault": False,
                "critical_fault": False,
                "final_fault": False,
                "critical_diag_on_day": False,
                "dead_diag_on_day": False,
                "diagnosis_date_online": strict_dt.date().isoformat(),
                "critical_diag_date": "",
                "dead_diag_date": "",
                "data_bad": False,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_panel_onset_shadow.py"
    smoke_weather = root / "research" / "prognostics" / "smoke_test_site_weather_history.py"
    smoke_event = root / "research" / "prognostics" / "smoke_test_site_event_dataset.py"
    smoke_frame = root / "research" / "prognostics" / "smoke_test_site_day_event_frame.py"
    smoke_episode = root / "research" / "prognostics" / "smoke_test_site_day_alert_episodes.py"
    smoke_field = root / "research" / "prognostics" / "smoke_test_field_truth_validation.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        out_dir = tmp_root / "data" / "demo" / "out"
        share_dir = tmp_root / "_share"
        out_dir.mkdir(parents=True, exist_ok=True)
        share_dir.mkdir(parents=True, exist_ok=True)

        strict_date = "2025-03-01"
        status_df = pd.DataFrame(
            [
                {"site": "demo", "panel_id": "p_abrupt", "date": strict_date, "diagnosis_date_online": strict_date, "critical_diag_date": "", "dead_diag_date": "", "final_fault": False},
                {"site": "demo", "panel_id": "p_gradual", "date": strict_date, "diagnosis_date_online": strict_date, "critical_diag_date": "", "dead_diag_date": "", "final_fault": False},
                {"site": "demo", "panel_id": "p_recovery", "date": strict_date, "diagnosis_date_online": strict_date, "critical_diag_date": "", "dead_diag_date": "", "final_fault": False},
                {"site": "demo", "panel_id": "p_confound", "date": strict_date, "diagnosis_date_online": strict_date, "critical_diag_date": "", "dead_diag_date": "", "final_fault": False},
            ]
        )
        status_df.to_csv(out_dir / "latest_panel_status_enriched.csv", index=False, encoding="utf-8-sig")

        core_df = pd.concat(
            [
                make_panel_rows("p_abrupt", strict_date, "2025-01-01", "2025-03-01", "abrupt"),
                make_panel_rows("p_gradual", strict_date, "2025-01-01", "2025-03-01", "gradual"),
                make_panel_rows("p_recovery", strict_date, "2025-01-01", "2025-03-01", "recovery_break"),
                make_panel_rows("p_confound", strict_date, "2025-01-01", "2025-03-01", "confounded"),
            ],
            ignore_index=True,
        )
        core_df.to_csv(out_dir / "panel_day_core.csv", index=False, encoding="utf-8-sig")

        build_res = run(
            [
                sys.executable,
                str(build_script),
                "--root",
                str(tmp_root),
                "--sites",
                "demo",
                "--lookback-days",
                "60",
            ],
            root,
        )
        assert_true(build_res.returncode == 0, f"shadow build failed:\n{build_res.stdout}\n{build_res.stderr}")

        latest = pd.read_csv(share_dir / "panel_onset_shadow_latest.csv", low_memory=False, encoding="utf-8-sig")
        suspicious = pd.read_csv(share_dir / "panel_onset_shadow_suspicious.csv", low_memory=False, encoding="utf-8-sig")

        assert_true(len(latest) == len(status_df), "strict case count was not preserved exactly")
        assert_true(latest["panel_id"].nunique() == len(status_df), "new panel candidates were created")

        abrupt = latest.loc[latest["panel_id"].eq("p_abrupt")].iloc[0]
        gradual = latest.loc[latest["panel_id"].eq("p_gradual")].iloc[0]
        recovery = latest.loc[latest["panel_id"].eq("p_recovery")].iloc[0]
        confound = latest.loc[latest["panel_id"].eq("p_confound")].iloc[0]

        assert_true(abrupt["retrospective_onset_date"] == abrupt["strict_trigger_date"], "abrupt fault onset should stay near strict trigger")
        assert_true(gradual["retrospective_onset_date"] < gradual["strict_trigger_date"], "gradual drift should move onset earlier")
        assert_true(recovery["retrospective_onset_date"] >= "2025-02-21", "recovery break should reset onset near late drift")
        assert_true(confound["onset_confidence"] != "high", "confounded case must not produce high-confidence early onset")
        assert_true((pd.to_numeric(confound["shadow_like_fraction"]) >= 0.5) or (pd.to_numeric(confound["group_off_like_fraction"]) >= 0.5), "confounded case should retain high confound fraction")
        assert_true(not suspicious.empty, "suspicious rows should be emitted for confounded or low-confidence cases")

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

    print("[OK] abrupt fault onset stays near strict trigger")
    print("[OK] gradual drift onset moves earlier than strict trigger")
    print("[OK] recovery break resets onset")
    print("[OK] confounded case does not produce high-confidence early onset")
    print("[OK] strict case count is preserved exactly")
    print("[OK] no new panel candidates are created")
    print("[OK] existing weather/event/frame/episode/truth smoke paths still pass")


if __name__ == "__main__":
    main()
