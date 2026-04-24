#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DIRTY_NAME = "repo_organization_dirty_summary_v1.csv"
SURFACE_NAME = "repo_organization_surface_inventory_v1.csv"
DOCREF_NAME = "repo_organization_doc_tmp_root_inventory_v1.csv"
LANE_NAME = "repo_organization_cleanup_lanes_v1.csv"
JSON_NAME = "repo_organization_inventory_summary_v1.json"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git(cmd: list[str], cwd: Path) -> None:
    completed = run(["git", *cmd], cwd)
    if completed.returncode != 0:
        raise SystemExit(completed.stderr or completed.stdout)


def build_fixture(repo_root: Path) -> None:
    write_text(repo_root / "docs" / "OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md", "ref /private/tmp/br010_packet_keep\nref /private/tmp/evidence_manifest_pack_check\n")
    write_text(repo_root / "pv_ae" / "panel_day_engine.py", "# core\n")
    write_text(repo_root / "research" / "prognostics" / "build_panel_day_engine_alpha_audit_v1.py", "# build\n")
    write_text(repo_root / "research" / "prognostics" / "smoke_test_panel_day_engine_alpha_audit_v1.py", "# smoke\n")
    write_text(repo_root / "release" / "conalog_full_runtime_v1" / "package" / "runtime" / "windows_x64" / "runtime.bin", "x")
    write_text(repo_root / "release" / "final_delivery_v1" / "package" / "docs" / "README.md", "final docs\n")
    write_text(repo_root / "outputs" / "tmp.txt", "clutter\n")
    write_text(repo_root / "nested" / "pvdiag" / ".keep", "nested\n")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_repo_organization_inventory_v1.py"

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_repo_organization_inventory_v1.py",
            "research/prognostics/smoke_test_repo_organization_inventory_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="repo_org_inventory_") as tmp_dir:
        tmp_root = Path(tmp_dir) / "fixture_repo"
        tmp_root.mkdir(parents=True, exist_ok=True)
        git(["init"], tmp_root)
        git(["config", "user.email", "fixture@example.com"], tmp_root)
        git(["config", "user.name", "Fixture"], tmp_root)

        build_fixture(tmp_root)
        git(["add", "."], tmp_root)
        git(["commit", "-m", "init"], tmp_root)

        write_text(tmp_root / "docs" / "OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md", "ref /private/tmp/br010_packet_keep\nref /private/tmp/evidence_manifest_pack_check\nref /private/tmp/pvdiag_postmerge_j\n")
        write_text(tmp_root / "research" / "prognostics" / "build_panel_day_engine_alpha_audit_v1.py", "# build changed\n")
        write_text(tmp_root / "docs" / "OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md", "new doc\n")

        out_dir = tmp_root / "_inventory_out"
        completed = run(
            [
                sys.executable,
                str(script),
                "--repo-root",
                str(tmp_root),
                "--output-dir",
                str(out_dir),
            ],
            repo_root,
        )
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)

        dirty_df = pd.read_csv(out_dir / DIRTY_NAME, encoding="utf-8-sig")
        surface_df = pd.read_csv(out_dir / SURFACE_NAME, encoding="utf-8-sig")
        docref_df = pd.read_csv(out_dir / DOCREF_NAME, encoding="utf-8-sig")
        lane_df = pd.read_csv(out_dir / LANE_NAME, encoding="utf-8-sig")
        payload = json.loads((out_dir / JSON_NAME).read_text(encoding="utf-8"))

        assert_true("top_level" in set(dirty_df["kind"]), dirty_df.to_string())
        assert_true("docs" in set(dirty_df.loc[dirty_df["kind"].eq("top_level"), "key"]), dirty_df.to_string())
        assert_true("source_research" in set(surface_df["surface_family"]), surface_df.to_string())
        assert_true("runtime_bundle_hygiene" in set(lane_df["cleanup_lane"]), lane_df.to_string())
        classes = set(docref_df["root_class"])
        assert_true("historical_br" in classes, docref_df.to_string())
        assert_true("current_evidence" in classes, docref_df.to_string())
        assert_true(payload["cleanup_lane_total"] == len(lane_df), payload)


if __name__ == "__main__":
    main()
