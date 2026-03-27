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

    build_script = root / "research" / "prognostics" / "build_site_day_event_frame.py"
    build_weather = root / "research" / "prognostics" / "build_site_weather_history.py"
    build_event = root / "research" / "prognostics" / "build_site_event_dataset.py"
    smoke_event = root / "research" / "prognostics" / "smoke_test_site_event_dataset.py"
    smoke_field = root / "research" / "prognostics" / "smoke_test_field_truth_validation.py"

    build_res = run([sys.executable, str(build_script)], root)
    assert_true(build_res.returncode == 0, f"site-day event frame build failed:\n{build_res.stdout}\n{build_res.stderr}")

    frame_path = share_dir / "site_day_event_frame_latest.csv"
    risk_path = share_dir / "site_day_event_risk_latest.csv"
    summary_path = share_dir / "site_day_event_risk_summary.csv"
    weather_path = share_dir / "site_weather_history_latest.csv"

    assert_true(frame_path.exists(), "site_day_event_frame_latest.csv was not generated")
    assert_true(risk_path.exists(), "site_day_event_risk_latest.csv was not generated")
    assert_true(summary_path.exists(), "site_day_event_risk_summary.csv was not generated")

    frame = pd.read_csv(frame_path, low_memory=False, encoding="utf-8-sig")
    risk = pd.read_csv(risk_path, low_memory=False, encoding="utf-8-sig")
    summary = pd.read_csv(summary_path, low_memory=False, encoding="utf-8-sig")
    weather = pd.read_csv(weather_path, low_memory=False, encoding="utf-8-sig")

    assert_true(len(frame) == len(weather), "frame row count must equal weather history row count")
    assert_true(frame.duplicated(["site", "date"]).sum() == 0, "site_day_event_frame_latest.csv has duplicate (site,date)")
    for col in ["next_event_confidence_level", "future_event_low_confidence_flag"]:
        assert_true(col in frame.columns, f"{col} is missing from site_day_event_frame_latest.csv")
    for col in ["eligible_1d", "eligible_3d", "eligible_7d"]:
        assert_true(col in frame.columns, f"{col} is missing from site_day_event_frame_latest.csv")
    for col in ["event_today", "event_within_1d", "event_within_3d", "event_within_7d"]:
        values = set(pd.to_numeric(frame[col], errors="coerce").fillna(-1).astype(int).tolist())
        assert_true(values <= {0, 1}, f"{col} must be binary, got {sorted(values)}")
    for col in ["eligible_1d", "eligible_3d", "eligible_7d"]:
        values = set(pd.to_numeric(frame[col], errors="coerce").fillna(-1).astype(int).tolist())
        assert_true(values <= {0, 1}, f"{col} must be binary, got {sorted(values)}")
        assert_true(pd.to_numeric(frame[col], errors="coerce").fillna(0).eq(0).any(), f"{col} must include some site-tail 0 rows")

    summary_row = summary.iloc[0]
    assert_true(int(summary_row["eligible_days_1d"]) == int(pd.to_numeric(frame["eligible_1d"], errors="coerce").fillna(0).sum()), "eligible_days_1d mismatch")
    assert_true(int(summary_row["eligible_days_3d"]) == int(pd.to_numeric(frame["eligible_3d"], errors="coerce").fillna(0).sum()), "eligible_days_3d mismatch")
    assert_true(int(summary_row["eligible_days_7d"]) == int(pd.to_numeric(frame["eligible_7d"], errors="coerce").fillna(0).sum()), "eligible_days_7d mismatch")
    for col in ["risk_band_q90", "risk_band_q98"]:
        assert_true(col in summary.columns, f"{col} is missing from site_day_event_risk_summary.csv")

    for band in ["high", "medium", "low"]:
        band_mask = risk["risk_band"].astype(str).eq(band)
        for horizon in ["1d", "3d", "7d"]:
            eligible_col = f"eligible_{horizon}"
            label_col = f"event_within_{horizon}"
            summary_eligible_col = f"{band}_eligible_days_{horizon}"
            summary_rate_col = f"{band}_positive_rate_{horizon}"

            eligible_mask = band_mask & pd.to_numeric(risk[eligible_col], errors="coerce").fillna(0).eq(1)
            eligible_count = int(eligible_mask.sum())
            assert_true(int(summary_row[summary_eligible_col]) == eligible_count, f"{summary_eligible_col} mismatch")

            if eligible_count == 0:
                assert_true(pd.isna(summary_row[summary_rate_col]), f"{summary_rate_col} must be blank/NaN when eligible days are zero")
            else:
                expected_rate = round(float(risk.loc[eligible_mask, label_col].mean()), 6)
                assert_true(round(float(summary_row[summary_rate_col]), 6) == expected_rate, f"{summary_rate_col} mismatch")

    eligible_any = frame[["eligible_1d", "eligible_3d", "eligible_7d"]].eq(1).any(axis=1)
    high_mask = risk["risk_band"].astype(str).eq("high")
    medium_mask = risk["risk_band"].astype(str).eq("medium")
    assert_true((high_mask & eligible_any).any(), "at least one eligible row must be assigned to high")
    assert_true(medium_mask.any(), "medium band must remain nonempty")

    weather_res = run([sys.executable, str(build_weather)], root)
    assert_true(weather_res.returncode == 0, f"weather history build failed:\n{weather_res.stdout}\n{weather_res.stderr}")

    event_res = run([sys.executable, str(build_event)], root)
    assert_true(event_res.returncode == 0, f"event dataset build failed:\n{event_res.stdout}\n{event_res.stderr}")

    smoke_event_res = run([sys.executable, str(smoke_event)], root)
    assert_true(smoke_event_res.returncode == 0, f"site event dataset smoke failed:\n{smoke_event_res.stdout}\n{smoke_event_res.stderr}")

    smoke_field_res = run([sys.executable, str(smoke_field)], root)
    assert_true(smoke_field_res.returncode == 0, f"field truth smoke failed:\n{smoke_field_res.stdout}\n{smoke_field_res.stderr}")

    print("[OK] site_day_event_frame_latest.csv generated")
    print(f"[OK] frame_rows={len(frame)}")
    print(f"[OK] risk_rows={len(risk)}")
    print("[OK] (site,date) duplicates are zero")
    print("[OK] event labels are binary")
    print("[OK] eligibility columns and per-band eligible denominators verified")
    print("[OK] quantile-calibrated high band includes eligible rows")
    print("[OK] medium band remains nonempty")
    print("[OK] existing weather history/event dataset/field truth smoke paths still pass")


if __name__ == "__main__":
    main()
