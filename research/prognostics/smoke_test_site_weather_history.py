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

    build_history = root / "research" / "prognostics" / "build_site_weather_history.py"
    build_event = root / "research" / "prognostics" / "build_site_event_dataset.py"
    smoke_event = root / "research" / "prognostics" / "smoke_test_site_event_dataset.py"
    smoke_field = root / "research" / "prognostics" / "smoke_test_field_truth_validation.py"

    history_res = run([sys.executable, str(build_history)], root)
    assert_true(history_res.returncode == 0, f"weather history build failed:\n{history_res.stdout}\n{history_res.stderr}")

    history_path = share_dir / "site_weather_history_latest.csv"
    coverage_path = share_dir / "site_weather_history_coverage.csv"
    request_path = share_dir / "site_weather_request_template.csv"
    groups_path = share_dir / "site_event_groups_latest.csv"

    assert_true(history_path.exists(), "site_weather_history_latest.csv was not generated")
    assert_true(coverage_path.exists(), "site_weather_history_coverage.csv was not generated")
    assert_true(request_path.exists(), "site_weather_request_template.csv was not generated")

    history = pd.read_csv(history_path, low_memory=False, encoding="utf-8-sig")
    coverage = pd.read_csv(coverage_path, low_memory=False, encoding="utf-8-sig")
    request = pd.read_csv(request_path, low_memory=False, encoding="utf-8-sig")
    groups = pd.read_csv(groups_path, low_memory=False, encoding="utf-8-sig")

    assert_true(len(history) > len(groups), "weather history row count must be greater than event group count")
    assert_true(history.duplicated(["site", "date"]).sum() == 0, "site_weather_history_latest.csv has duplicate (site,date)")

    event_res = run([sys.executable, str(build_event)], root)
    assert_true(event_res.returncode == 0, f"event dataset rebuild failed after weather history build:\n{event_res.stdout}\n{event_res.stderr}")

    smoke_event_res = run([sys.executable, str(smoke_event)], root)
    assert_true(smoke_event_res.returncode == 0, f"site event dataset smoke failed:\n{smoke_event_res.stdout}\n{smoke_event_res.stderr}")

    smoke_field_res = run([sys.executable, str(smoke_field)], root)
    assert_true(smoke_field_res.returncode == 0, f"field truth smoke failed:\n{smoke_field_res.stdout}\n{smoke_field_res.stderr}")

    assert_true(not coverage.empty, "site_weather_history_coverage.csv is unexpectedly empty")
    assert_true(request.columns.tolist() == ["site", "address", "date", "reason"], "request template schema drifted")

    print("[OK] site_weather_history_latest.csv generated")
    print(f"[OK] history_rows={len(history)}")
    print(f"[OK] request_rows={len(request)}")
    print("[OK] (site,date) duplicates are zero")
    print("[OK] coverage and request template generated")
    print("[OK] existing site event dataset smoke still passes")
    print("[OK] existing field truth validation smoke still passes")


if __name__ == "__main__":
    main()
