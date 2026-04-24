#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_patch_safety_gate_v1.csv"
SUMMARY_NAME = "panel_day_engine_patch_safety_gate_summary_v1.csv"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_paths(path: Path, paths: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(paths) + "\n", encoding="utf-8")


def run_gate(script: Path, repo_root: Path, tmp_root: Path, paths: list[str], label: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    changed = tmp_root / f"{label}_paths.txt"
    output_dir = tmp_root / label
    write_paths(changed, paths)
    cmd = [
        sys.executable,
        str(script),
        "--changed-paths-file",
        str(changed),
        "--output-dir",
        str(output_dir),
    ]
    completed = run(cmd, repo_root)
    assert_true(completed.returncode == 0, completed.stderr or completed.stdout)
    detail_df = pd.read_csv(output_dir / DETAIL_NAME, encoding="utf-8-sig")
    summary_df = pd.read_csv(output_dir / SUMMARY_NAME, encoding="utf-8-sig")
    return detail_df, summary_df


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "check_panel_day_engine_patch_safety_gate_v1.py"
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)

        no_engine_detail, no_engine_summary = run_gate(
            script,
            repo_root,
            tmp_root,
            [
                "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_053_PANEL_ENGINE_PATCH_SAFETY_GATE_V1.md",
                "research/prognostics/check_panel_day_engine_patch_safety_gate_v1.py",
            ],
            "no_engine",
        )
        assert_true(int(no_engine_summary.iloc[0]["engine_change_detected"]) == 0, no_engine_summary.to_string())
        assert_true(no_engine_summary.iloc[0]["overall_status"] == "pass", no_engine_summary.to_string())
        assert_true(no_engine_detail["status"].isin(["pass", "not_applicable"]).all(), no_engine_detail.to_string())

        missing_detail, missing_summary = run_gate(
            script,
            repo_root,
            tmp_root,
            ["pv_ae/panel_day_engine.py"],
            "missing",
        )
        assert_true(int(missing_summary.iloc[0]["engine_change_detected"]) == 1, missing_summary.to_string())
        assert_true(missing_summary.iloc[0]["overall_status"] == "fail", missing_summary.to_string())
        required_failures = set(missing_detail.loc[missing_detail["status"].eq("fail"), "gate_id"].tolist())
        assert_true("G01_branch_doc_present" in required_failures, str(required_failures))
        assert_true("G08_source_package_sync_present" in required_failures, str(required_failures))

        full_paths = [
            "pv_ae/panel_day_engine.py",
            "release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py",
            "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_099_ENGINE_PATCH_V1.md",
            "docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_099_V1.md",
            "docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md",
            "docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md",
            "ONEPAGER.md",
            "research/prognostics/build_panel_day_engine_patch_shadow_simulation_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_patch_shadow_simulation_v1.py",
        ]
        full_detail, full_summary = run_gate(script, repo_root, tmp_root, full_paths, "full")
        assert_true(int(full_summary.iloc[0]["engine_change_detected"]) == 1, full_summary.to_string())
        assert_true(full_summary.iloc[0]["overall_status"] == "pass", full_summary.to_string())
        assert_true(not full_detail["status"].eq("fail").any(), full_detail.to_string())


if __name__ == "__main__":
    main()
