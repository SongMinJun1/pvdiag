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


def write_csv(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_fixture(root: Path) -> None:
    write_csv(
        root / "data" / "conalog" / "out" / "latest_panel_status.csv",
        "site,panel_id,date\n"
        "conalog,p1,2026-02-18\n"
        "conalog,p2,2026-02-18\n",
    )
    write_csv(
        root / "data" / "gangui" / "out" / "latest_panel_status.csv",
        "site,panel_id,date\n"
        "gangui,p3,2026-02-19\n",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research" / "prognostics" / "build_topology_inventory.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], repo_root)
    assert_true(compile_res.returncode == 0, f"py_compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory(prefix="topology_inventory_smoke_") as tmpdir:
        root = Path(tmpdir)
        build_fixture(root)

        absent_res = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(
            absent_res.returncode == 0,
            f"build failed when topology input is absent:\n{absent_res.stdout}\n{absent_res.stderr}",
        )

        coverage_path = root / "_share" / "site_topology_coverage.csv"
        missing_path = root / "_share" / "site_topology_missing.csv"
        duplicates_path = root / "_share" / "site_topology_duplicates.csv"

        assert_true(coverage_path.exists(), "site_topology_coverage.csv was not generated")
        assert_true(missing_path.exists(), "site_topology_missing.csv was not generated")
        assert_true(duplicates_path.exists(), "site_topology_duplicates.csv was not generated")

        coverage = pd.read_csv(coverage_path, low_memory=False, encoding="utf-8-sig")
        missing = pd.read_csv(missing_path, low_memory=False, encoding="utf-8-sig")
        duplicates = pd.read_csv(duplicates_path, low_memory=False, encoding="utf-8-sig")

        expected_coverage_cols = {
            "site",
            "total_panels",
            "matched_panels",
            "coverage_rate",
            "string_coverage_rate",
            "mppt_coverage_rate",
            "inverter_coverage_rate",
        }
        assert_true(expected_coverage_cols <= set(coverage.columns), "coverage columns are missing")
        assert_true(duplicates.empty, "duplicates output must be empty when topology file is absent")
        assert_true(len(missing) == 3, "all inventory panels should be missing when topology file is absent")

        write_csv(
            root / "data" / "manual" / "site_topology.csv",
            "site,panel_id,string_id,mppt_id,inverter_id,note\n"
            "conalog,p1,s1,m1,i1,first\n"
            "conalog,p1,s2,m1,i1,duplicate_conflict\n"
            "wrongsite,p2,s3,m2,i2,site_mismatch\n"
            "gangui,p3,,m3,,partial\n",
        )

        present_res = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(
            present_res.returncode == 0,
            f"build failed with synthetic topology input:\n{present_res.stdout}\n{present_res.stderr}",
        )

        coverage = pd.read_csv(coverage_path, low_memory=False, encoding="utf-8-sig")
        missing = pd.read_csv(missing_path, low_memory=False, encoding="utf-8-sig")
        duplicates = pd.read_csv(duplicates_path, low_memory=False, encoding="utf-8-sig")

        assert_true(not duplicates.empty, "duplicates/conflicts should be detected on synthetic topology input")
        p1_dup = duplicates.loc[duplicates["panel_id"].astype(str).eq("p1")]
        assert_true(not p1_dup.empty, "duplicate panel p1 must appear in duplicates output")
        assert_true(int(p1_dup.iloc[0]["row_count"]) == 2, "p1 duplicate row_count mismatch")
        p2_missing = missing.loc[(missing["site"].astype(str) == "conalog") & (missing["panel_id"].astype(str) == "p2")]
        assert_true(not p2_missing.empty, "site-mismatched panel p2 must remain missing for conalog inventory")
        p3_missing = missing.loc[(missing["site"].astype(str) == "gangui") & (missing["panel_id"].astype(str) == "p3")]
        assert_true(not p3_missing.empty, "partial topology for p3 must appear in missing output")
        assert_true(int(p3_missing.iloc[0]["missing_string"]) == 1, "p3 missing_string must be 1")
        assert_true(int(p3_missing.iloc[0]["missing_inverter"]) == 1, "p3 missing_inverter must be 1")

    print("[OK] topology inventory scripts compile")
    print("[OK] outputs generate when site_topology.csv is absent")
    print("[OK] coverage columns exist")
    print("[OK] duplicates/conflicts detected on synthetic topology fixture")


if __name__ == "__main__":
    main()
