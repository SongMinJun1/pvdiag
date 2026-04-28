#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "repo_mirror_boundary_manifest_v1.csv"
SUMMARY_NAME = "repo_mirror_boundary_summary_v1.csv"
JSON_NAME = "repo_mirror_boundary_summary_v1.json"


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_fixture(repo_root: Path) -> None:
    write_text(repo_root / "research" / "prognostics" / "same.py", "same\n")
    write_text(repo_root / "release" / "conalog_full_runtime_v1" / "package" / "research" / "prognostics" / "same.py", "same\n")
    write_text(repo_root / "research" / "prognostics" / "drift.py", "source\n")
    write_text(repo_root / "release" / "conalog_full_runtime_v1" / "package" / "research" / "prognostics" / "drift.py", "mirror\n")
    write_text(repo_root / "release" / "conalog_full_runtime_v1" / "package" / "research" / "prognostics" / "mirror_only.py", "mirror only\n")
    write_text(repo_root / "pv_ae" / "panel_day_engine.py", "# engine\n")
    write_text(repo_root / "release" / "conalog_full_runtime_v1" / "package" / "pv_ae" / "panel_day_engine.py", "# engine\n")
    write_text(repo_root / "docs" / "OPS_CONALOG_HANDOFF_PACK_V1.md", "doc\n")
    write_text(repo_root / "release" / "final_delivery_v1" / "package" / "docs" / "OPS_CONALOG_HANDOFF_PACK_V1.md", "doc\n")
    write_text(repo_root / "release" / "final_delivery_v1" / "package" / "docs" / "metric.csv", "a,b\n")
    write_text(repo_root / "release" / "conalog_full_runtime_v1" / "package" / "app" / "run_full_algorithm_pack.py", "# app\n")
    write_text(repo_root / "release" / "conalog_full_runtime_v1" / "package" / "artifacts" / "preview.csv", "x\n")
    write_text(repo_root / "release" / "final_delivery_v1" / "package" / "examples" / "example.csv", "x\n")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_repo_mirror_boundary_manifest_v1.py"

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_repo_mirror_boundary_manifest_v1.py",
            "research/prognostics/smoke_test_repo_mirror_boundary_manifest_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="repo_mirror_boundary_") as tmp_dir:
        tmp_root = Path(tmp_dir) / "fixture_repo"
        tmp_root.mkdir(parents=True, exist_ok=True)
        build_fixture(tmp_root)
        out_dir = tmp_root / "_mirror_boundary_out"
        completed = run(
            [
                sys.executable,
                str(script),
                "--repo-root",
                str(tmp_root),
                "--output-dir",
                str(out_dir),
                "--owner-branch",
                "fixture-branch",
            ],
            repo_root,
        )
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)

        detail_df = pd.read_csv(out_dir / DETAIL_NAME, encoding="utf-8-sig")
        summary_df = pd.read_csv(out_dir / SUMMARY_NAME, encoding="utf-8-sig")
        payload = json.loads((out_dir / JSON_NAME).read_text(encoding="utf-8"))

        statuses = set(detail_df["sync_status"])
        families = set(detail_df["mirror_family"])
        assert_true("in_sync" in statuses, detail_df.to_string())
        assert_true("content_drift" in statuses, detail_df.to_string())
        assert_true("packaged_only_no_source_pair" in statuses, detail_df.to_string())
        assert_true("runtime_package_app_surface" in families, detail_df.to_string())
        assert_true("runtime_packaged_artifacts" in families, detail_df.to_string())
        assert_true("final_delivery_examples" in families, detail_df.to_string())
        assert_true(payload["owner_branch"] == "fixture-branch", payload)
        assert_true(payload["sync_status_counts"]["content_drift"] >= 1, payload)
        assert_true("sync_status" in set(summary_df["kind"]), summary_df.to_string())


if __name__ == "__main__":
    main()
