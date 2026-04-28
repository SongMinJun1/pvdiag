#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


MANIFEST_NAME = "repo_role_boundary_manifest_v1.csv"
STATUS_NAME = "repo_role_boundary_status_v1.csv"
SUMMARY_NAME = "repo_role_boundary_summary_v1.csv"
JSON_NAME = "repo_role_boundary_summary_v1.json"


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
    write_text(repo_root / "docs" / "OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md", "runtime docs\n")
    write_text(repo_root / "pv_ae" / "panel_day_engine.py", "# engine\n")
    write_text(repo_root / "research" / "prognostics" / "build_alpha_v1.py", "# builder\n")
    write_text(repo_root / "research" / "prognostics" / "smoke_test_alpha_v1.py", "# smoke\n")
    write_text(repo_root / "release" / "conalog_full_runtime_v1" / "package" / "research" / "prognostics" / "build_alpha_v1.py", "# mirror\n")
    write_text(repo_root / "release" / "conalog_full_runtime_v1" / "package" / "runtime" / "windows_x64" / "runtime.bin", "x")
    write_text(repo_root / "release" / "final_delivery_v1" / "package" / "docs" / "README.md", "final docs\n")
    write_text(repo_root / "outputs" / "local.csv", "x\n")
    write_text(repo_root / "pvdiag" / ".gitkeep", "nested placeholder\n")
    write_text(repo_root / ".gitattributes", "*.dll filter=lfs\n")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_repo_role_boundary_manifest_v1.py"

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_repo_role_boundary_manifest_v1.py",
            "research/prognostics/smoke_test_repo_role_boundary_manifest_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="repo_role_boundary_") as tmp_dir:
        tmp_root = Path(tmp_dir) / "fixture_repo"
        tmp_root.mkdir(parents=True, exist_ok=True)
        git(["init"], tmp_root)
        git(["config", "user.email", "fixture@example.com"], tmp_root)
        git(["config", "user.name", "Fixture"], tmp_root)

        build_fixture(tmp_root)
        git(["add", "."], tmp_root)
        git(["commit", "-m", "init"], tmp_root)

        write_text(tmp_root / "docs" / "OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md", "runtime docs changed\n")
        write_text(tmp_root / "research" / "prognostics" / "build_alpha_v1.py", "# builder changed\n")
        write_text(tmp_root / "release" / "conalog_full_runtime_v1" / "package" / "research" / "prognostics" / "build_alpha_v1.py", "# mirror changed\n")
        write_text(tmp_root / "outputs" / "local.csv", "changed\n")
        write_text(tmp_root / "scratch.tmp", "unknown\n")

        out_dir = tmp_root / "_role_boundary_out"
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

        manifest_df = pd.read_csv(out_dir / MANIFEST_NAME, encoding="utf-8-sig")
        status_df = pd.read_csv(out_dir / STATUS_NAME, encoding="utf-8-sig")
        summary_df = pd.read_csv(out_dir / SUMMARY_NAME, encoding="utf-8-sig")
        payload = json.loads((out_dir / JSON_NAME).read_text(encoding="utf-8"))

        assert_true("runtime_decision_docs" in set(manifest_df["role_id"]), manifest_df.to_string())
        assert_true("mixed_scope_disentangle" in set(manifest_df["cleanup_lane"]), manifest_df.to_string())
        assert_true("source_vs_packaged_mirror_boundary" in set(manifest_df["cleanup_lane"]), manifest_df.to_string())
        assert_true("active_builder_entrypoint_registry" in set(manifest_df["cleanup_lane"]), manifest_df.to_string())

        by_path = {row["path"]: row for _, row in status_df.iterrows()}
        assert_true(by_path["docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md"]["role_id"] == "runtime_decision_docs", status_df.to_string())
        assert_true(by_path["research/prognostics/build_alpha_v1.py"]["role_id"] == "research_builders", status_df.to_string())
        assert_true(by_path["release/conalog_full_runtime_v1/package/research/prognostics/build_alpha_v1.py"]["role_id"] == "packaged_research_mirror", status_df.to_string())
        assert_true(by_path["outputs/local.csv"]["role_id"] == "generated_outputs_workspace", status_df.to_string())
        assert_true(by_path["scratch.tmp"]["role_id"] == "unclassified", status_df.to_string())

        assert_true(payload["owner_branch"] == "fixture-branch", payload)
        assert_true(payload["unclassified_dirty_entry_total"] == 1, payload)
        assert_true("role_id" in set(summary_df["kind"]), summary_df.to_string())


if __name__ == "__main__":
    main()
