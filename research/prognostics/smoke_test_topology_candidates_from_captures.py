#!/usr/bin/env python3
from __future__ import annotations

import json
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


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_explicit_fixture(root: Path) -> None:
    capture_dir = root / "data" / "manual" / "webapp_captures"
    write_json(
        capture_dir / "conalog_reports.json",
        {"panelCount": 10, "inverterCount": 2, "address": "Busan"},
    )
    write_json(
        capture_dir / "conalog_latest_state.json",
        {
            "panels": [
                {"panel_id": "p1"},
                {"panel_id": "p2"},
            ]
        },
    )
    write_json(
        capture_dir / "conalog_panelmaps.json",
        {
            "items": [
                {"panel_id": "p1", "string_id": "s1", "mppt_id": "m1", "inverter_id": "i1"},
                {"panel_id": "p2", "string_id": "s2", "inverter_id": "i1"},
            ]
        },
    )
    write_json(
        capture_dir / "conalog_inverter.json",
        {
            "panels": [
                {"panel_id": "p2", "string_id": "s9", "inverter_id": "i1"},
            ]
        },
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research" / "prognostics" / "build_topology_candidates_from_captures.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], repo_root)
    assert_true(compile_res.returncode == 0, f"py_compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory(prefix="topology_captures_smoke_") as tmpdir:
        root = Path(tmpdir)

        missing_res = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(
            missing_res.returncode == 0,
            f"build failed when captures are missing:\n{missing_res.stdout}\n{missing_res.stderr}",
        )

        summary_path = root / "_share" / "site_topology_capture_summary.csv"
        candidates_path = root / "_share" / "site_topology_candidate_rows.csv"
        conflicts_path = root / "_share" / "site_topology_candidate_conflicts.csv"
        missing_path = root / "_share" / "site_topology_missing_sources.csv"

        assert_true(summary_path.exists(), "site_topology_capture_summary.csv was not generated")
        assert_true(candidates_path.exists(), "site_topology_candidate_rows.csv was not generated")
        assert_true(conflicts_path.exists(), "site_topology_candidate_conflicts.csv was not generated")
        assert_true(missing_path.exists(), "site_topology_missing_sources.csv was not generated")

        summary = pd.read_csv(summary_path, low_memory=False, encoding="utf-8-sig")
        candidates = pd.read_csv(candidates_path, low_memory=False, encoding="utf-8-sig")
        conflicts = pd.read_csv(conflicts_path, low_memory=False, encoding="utf-8-sig")

        assert_true(not summary.empty, "summary should contain per-site rows when captures are missing")
        assert_true(candidates.empty, "candidate rows should be empty when captures are missing")
        assert_true(conflicts.empty, "conflicts should be empty when captures are missing")

        build_explicit_fixture(root)
        present_res = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(
            present_res.returncode == 0,
            f"build failed with synthetic captures:\n{present_res.stdout}\n{present_res.stderr}",
        )

        summary = pd.read_csv(summary_path, low_memory=False, encoding="utf-8-sig")
        candidates = pd.read_csv(candidates_path, low_memory=False, encoding="utf-8-sig")
        conflicts = pd.read_csv(conflicts_path, low_memory=False, encoding="utf-8-sig")

        assert_true(not candidates.empty, "explicit synthetic captures should emit candidate rows")
        conalog_summary = summary.loc[summary["site"].astype(str).eq("conalog")].iloc[0]
        assert_true(int(conalog_summary["reports_present"]) == 1, "reports_present mismatch")
        assert_true(int(conalog_summary["panelmaps_present"]) == 1, "panelmaps_present mismatch")
        assert_true(int(conalog_summary["candidate_rows"]) >= 2, "candidate_rows should be populated")
        assert_true(int(conalog_summary["strong_candidate_rows"]) >= 1, "strong candidate rows should be detected")
        assert_true(not conflicts.empty, "conflicting synthetic captures should emit conflict rows")

    print("[OK] topology candidates from captures scripts compile")
    print("[OK] outputs generate even when captures are missing")
    print("[OK] tiny synthetic captures with explicit fields produce candidate rows")
    print("[OK] conflicting synthetic captures produce conflict rows")


if __name__ == "__main__":
    main()
