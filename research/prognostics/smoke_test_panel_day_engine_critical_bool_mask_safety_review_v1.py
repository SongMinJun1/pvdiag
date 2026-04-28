#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


SUMMARY_NAME = "panel_day_engine_critical_bool_mask_safety_review_summary_v1.csv"


def write_engine_pair(root: Path, content: str) -> None:
    for rel in [
        "pv_ae/panel_day_engine.py",
        "release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py",
    ]:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_panel_day_engine_critical_bool_mask_safety_review_v1.py"
    good_content = '''
def panel_day_engine_fixture(out):
    critical_fault_mask = out["critical_fault"].fillna(False).astype(bool)
    return out[critical_fault_mask].copy()
'''
    bad_content = '''
def panel_day_engine_fixture(out):
    return out[out["critical_fault"] == True].copy()
'''
    with tempfile.TemporaryDirectory(prefix="critical_bool_mask_safety_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        good_root = tmp_root / "good"
        bad_root = tmp_root / "bad"
        write_engine_pair(good_root, good_content)
        write_engine_pair(bad_root, bad_content)

        good_out = tmp_root / "good_out"
        good = run([sys.executable, str(script), "--repo-root", str(good_root), "--output-dir", str(good_out)], repo_root)
        assert_true(good.returncode == 0, good.stderr or good.stdout)
        good_summary = pd.read_csv(good_out / SUMMARY_NAME, encoding="utf-8-sig")
        assert_true(good_summary.iloc[0]["overall_status"] == "pass", good_summary.to_string())
        assert_true(int(good_summary.iloc[0]["source_new_mask_count"]) == 1, good_summary.to_string())

        bad_out = tmp_root / "bad_out"
        bad = run([sys.executable, str(script), "--repo-root", str(bad_root), "--output-dir", str(bad_out)], repo_root)
        assert_true(bad.returncode != 0, "bad critical bool mask fixture unexpectedly passed")
        bad_summary = pd.read_csv(bad_out / SUMMARY_NAME, encoding="utf-8-sig")
        assert_true(bad_summary.iloc[0]["overall_status"] == "fail", bad_summary.to_string())
        assert_true(int(bad_summary.iloc[0]["source_old_bool_equality_count"]) == 1, bad_summary.to_string())


if __name__ == "__main__":
    main()
