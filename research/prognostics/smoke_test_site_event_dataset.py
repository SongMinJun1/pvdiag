#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

ALLOWED_EVENT_CONFIDENCE = {"high", "medium", "low", "unknown"}
ALLOWED_WEATHER_CONFOUND = {"", "0", "1"}


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def normalize_flag_series(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    share_dir = root / "_share"
    build_script = root / "research" / "prognostics" / "build_site_event_dataset.py"
    stable_smoke = root / "research" / "prognostics" / "smoke_test_field_truth_validation.py"
    manual_weather = root / "data" / "manual" / "site_weather_daily.csv"
    manual_backup = manual_weather.with_suffix(manual_weather.suffix + ".bak_site_event_dataset_smoke")

    moved_manual = False
    try:
        if manual_weather.exists():
            manual_backup.parent.mkdir(parents=True, exist_ok=True)
            if manual_backup.exists():
                manual_backup.unlink()
            shutil.move(str(manual_weather), str(manual_backup))
            moved_manual = True

        build_res = run([sys.executable, str(build_script)], root)
        assert_true(build_res.returncode == 0, f"event dataset build failed without manual weather:\n{build_res.stdout}\n{build_res.stderr}")

        dataset_path = share_dir / "site_event_dataset_latest.csv"
        weather_template_path = share_dir / "site_weather_daily_template.csv"
        groups_path = share_dir / "site_event_groups_latest.csv"

        assert_true(dataset_path.exists(), "site_event_dataset_latest.csv was not generated")
        assert_true(weather_template_path.exists(), "site_weather_daily_template.csv was not generated")

        dataset = pd.read_csv(dataset_path, low_memory=False, encoding="utf-8-sig")
        weather_template = pd.read_csv(weather_template_path, low_memory=False, encoding="utf-8-sig")
        groups = pd.read_csv(groups_path, low_memory=False, encoding="utf-8-sig")

        assert_true(len(dataset) == len(groups), "site_event_dataset_latest.csv row count must equal event group count")
        assert_true(len(weather_template) == len(groups[["site", "representative_date"]].drop_duplicates()), "weather template row count mismatch")

        confidence_values = set(normalize_flag_series(dataset["event_confidence_level"]))
        assert_true(confidence_values <= ALLOWED_EVENT_CONFIDENCE, f"invalid event_confidence_level values: {sorted(confidence_values)}")

        confound_values = set(normalize_flag_series(dataset["weather_confound_flag"]))
        assert_true(confound_values <= ALLOWED_WEATHER_CONFOUND, f"invalid weather_confound_flag values: {sorted(confound_values)}")

        if "weather_available" in dataset.columns:
            unavailable = pd.to_numeric(dataset["weather_available"], errors="coerce").fillna(0).eq(0)
            assert_true(unavailable.all(), "weather_available must be 0 when manual weather file is absent in smoke test")

        stable_res = run([sys.executable, str(stable_smoke)], root)
        assert_true(stable_res.returncode == 0, f"stable validation smoke failed:\n{stable_res.stdout}\n{stable_res.stderr}")
    finally:
        if moved_manual and manual_backup.exists():
            manual_weather.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(manual_backup), str(manual_weather))

    print("[OK] site_event_dataset_latest.csv generated")
    print(f"[OK] dataset_rows={len(dataset)}")
    print(f"[OK] weather_template_rows={len(weather_template)}")
    print("[OK] build succeeds when manual weather file is absent")
    print("[OK] stable validation smoke path still passes")
    print("[OK] event_confidence_level values valid")
    print("[OK] weather_confound_flag values valid")


if __name__ == "__main__":
    main()
