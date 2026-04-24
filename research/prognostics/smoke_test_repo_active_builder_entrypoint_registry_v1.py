#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


REGISTRY_NAME = "repo_active_builder_entrypoint_registry_v1.csv"
SUMMARY_NAME = "repo_active_builder_entrypoint_summary_v1.csv"
JSON_NAME = "repo_active_builder_entrypoint_summary_v1.json"


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def git(cmd: list[str], cwd: Path) -> None:
    completed = run(["git", *cmd], cwd)
    if completed.returncode != 0:
        raise SystemExit(completed.stderr or completed.stdout)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_fixture(repo_root: Path) -> None:
    write_text(repo_root / "research" / "prognostics" / "build_alpha_v1.py", "# build alpha\n")
    write_text(repo_root / "research" / "prognostics" / "smoke_test_alpha_v1.py", "# smoke alpha\n")
    write_text(repo_root / "research" / "prognostics" / "build_packaged_v1.py", "# packaged source\n")
    write_text(repo_root / "release" / "conalog_full_runtime_v1" / "package" / "research" / "prognostics" / "build_packaged_v1.py", "# packaged mirror\n")
    write_text(repo_root / "research" / "prognostics" / "build_unpaired_v1.py", "# build only\n")
    write_text(repo_root / "research" / "prognostics" / "smoke_test_fixture_only_v1.py", "# smoke only\n")
    write_text(repo_root / "docs" / "OPS_CONALOG_RUNTIME_ALPHA_V1.md", "run build_alpha_v1.py and smoke_test_fixture_only_v1.py\n")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_repo_active_builder_entrypoint_registry_v1.py"

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_repo_active_builder_entrypoint_registry_v1.py",
            "research/prognostics/smoke_test_repo_active_builder_entrypoint_registry_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="repo_active_builder_registry_") as tmp_dir:
        tmp_root = Path(tmp_dir) / "fixture_repo"
        tmp_root.mkdir(parents=True, exist_ok=True)
        git(["init"], tmp_root)
        git(["config", "user.email", "fixture@example.com"], tmp_root)
        git(["config", "user.name", "Fixture"], tmp_root)
        build_fixture(tmp_root)
        git(["add", "."], tmp_root)
        git(["commit", "-m", "init"], tmp_root)
        write_text(tmp_root / "research" / "prognostics" / "build_unpaired_v1.py", "# changed\n")

        out_dir = tmp_root / "_builder_registry_out"
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

        registry_df = pd.read_csv(out_dir / REGISTRY_NAME, encoding="utf-8-sig")
        summary_df = pd.read_csv(out_dir / SUMMARY_NAME, encoding="utf-8-sig")
        payload = json.loads((out_dir / JSON_NAME).read_text(encoding="utf-8"))

        statuses = set(registry_df["registry_status"])
        assert_true("documented_paired_entrypoint" in statuses, registry_df.to_string())
        assert_true("packaged_runtime_entrypoint" in statuses, registry_df.to_string())
        assert_true("unpaired_builder_review" in statuses, registry_df.to_string())
        assert_true("documented_unpaired_entrypoint" in statuses, registry_df.to_string())
        assert_true(payload["owner_branch"] == "fixture-branch", payload)
        assert_true(payload["entrypoint_total"] == len(registry_df), payload)
        assert_true(payload["pair_missing_total"] >= 2, payload)
        assert_true("registry_status" in set(summary_df["kind"]), summary_df.to_string())


if __name__ == "__main__":
    main()
