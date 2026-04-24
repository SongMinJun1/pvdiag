#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_patch_safety_gate_v1.csv"
SUMMARY_NAME = "panel_day_engine_patch_safety_gate_summary_v1.csv"
SOURCE_ENGINE = "pv_ae/panel_day_engine.py"
PACKAGE_ENGINE = "release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py"
BR_DOC = "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_099_ENGINE_PATCH_V1.md"
DL_DOC = "docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_099_V1.md"
ACTIVE_REGISTER = "docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md"
GATE7_DOC = "docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md"
ONEPAGER = "ONEPAGER.md"
SHADOW_BUILDER = "research/prognostics/build_panel_day_engine_patch_shadow_simulation_v1.py"
SMOKE_TEST = "research/prognostics/smoke_test_panel_day_engine_patch_shadow_simulation_v1.py"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_paths(path: Path, paths: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(paths) + "\n", encoding="utf-8")


def write_file(repo_root: Path, path: str, content: str) -> None:
    file_path = repo_root / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def make_fake_repo(tmp_root: Path, label: str, package_text: str | None = None) -> Path:
    repo_root = tmp_root / f"{label}_repo"
    source_text = "def marker():\n    return 'panel_day_engine safety source'\n"
    if package_text is None:
        package_text = source_text
    write_file(repo_root, SOURCE_ENGINE, source_text)
    write_file(repo_root, PACKAGE_ENGINE, package_text)
    write_file(repo_root, BR_DOC, "# panel_day_engine safety branch note\n")
    write_file(repo_root, DL_DOC, "# panel_day_engine safety decision log\n")
    write_file(repo_root, ACTIVE_REGISTER, "# active register\n")
    write_file(repo_root, GATE7_DOC, "# Gate7 panel_day_engine safety order\n")
    write_file(repo_root, ONEPAGER, "# panel_day_engine behavior note\n")
    write_file(repo_root, SHADOW_BUILDER, "# panel_day_engine shadow builder\n")
    write_file(repo_root, SMOKE_TEST, "# panel_day_engine smoke test\n")
    return repo_root


def run_gate(script: Path, repo_root: Path, tmp_root: Path, paths: list[str], label: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    changed = tmp_root / f"{label}_paths.txt"
    output_dir = tmp_root / label
    write_paths(changed, paths)
    cmd = [
        sys.executable,
        str(script),
        "--repo-root",
        str(repo_root),
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

        fake_repo = make_fake_repo(tmp_root, "full_pass")
        missing_detail, missing_summary = run_gate(
            script,
            fake_repo,
            tmp_root,
            [SOURCE_ENGINE],
            "missing",
        )
        assert_true(int(missing_summary.iloc[0]["engine_change_detected"]) == 1, missing_summary.to_string())
        assert_true(missing_summary.iloc[0]["overall_status"] == "fail", missing_summary.to_string())
        required_failures = set(missing_detail.loc[missing_detail["status"].eq("fail"), "gate_id"].tolist())
        assert_true("G01_branch_doc_present" in required_failures, str(required_failures))
        assert_true("G08_source_package_pair_changed_together" in required_failures, str(required_failures))

        full_paths = [
            SOURCE_ENGINE,
            PACKAGE_ENGINE,
            BR_DOC,
            DL_DOC,
            ACTIVE_REGISTER,
            GATE7_DOC,
            ONEPAGER,
            SHADOW_BUILDER,
            SMOKE_TEST,
        ]
        full_detail, full_summary = run_gate(script, fake_repo, tmp_root, full_paths, "full")
        assert_true(int(full_summary.iloc[0]["engine_change_detected"]) == 1, full_summary.to_string())
        assert_true(full_summary.iloc[0]["overall_status"] == "pass", full_summary.to_string())
        assert_true(not full_detail["status"].eq("fail").any(), full_detail.to_string())

        package_only_detail, package_only_summary = run_gate(
            script,
            fake_repo,
            tmp_root,
            [
                PACKAGE_ENGINE,
                BR_DOC,
                DL_DOC,
                ACTIVE_REGISTER,
                GATE7_DOC,
                ONEPAGER,
                SHADOW_BUILDER,
                SMOKE_TEST,
            ],
            "package_only",
        )
        assert_true(package_only_summary.iloc[0]["overall_status"] == "fail", package_only_summary.to_string())
        package_only_failures = set(package_only_detail.loc[package_only_detail["status"].eq("fail"), "gate_id"].tolist())
        assert_true("G08_source_package_pair_changed_together" in package_only_failures, str(package_only_failures))

        mismatch_repo = make_fake_repo(
            tmp_root,
            "mismatch",
            package_text="def marker():\n    return 'panel_day_engine divergent package'\n",
        )
        mismatch_detail, mismatch_summary = run_gate(script, mismatch_repo, tmp_root, full_paths, "mismatch")
        assert_true(mismatch_summary.iloc[0]["overall_status"] == "fail", mismatch_summary.to_string())
        mismatch_failures = set(mismatch_detail.loc[mismatch_detail["status"].eq("fail"), "gate_id"].tolist())
        assert_true("G09_source_package_content_equal" in mismatch_failures, str(mismatch_failures))

        deleted_detail, deleted_summary = run_gate(
            script,
            fake_repo,
            tmp_root,
            [
                SOURCE_ENGINE,
                PACKAGE_ENGINE,
                f"D\t{BR_DOC}",
                DL_DOC,
                ACTIVE_REGISTER,
                GATE7_DOC,
                ONEPAGER,
                SHADOW_BUILDER,
                SMOKE_TEST,
            ],
            "deleted_evidence",
        )
        assert_true(deleted_summary.iloc[0]["overall_status"] == "fail", deleted_summary.to_string())
        deleted_failures = set(deleted_detail.loc[deleted_detail["status"].eq("fail"), "gate_id"].tolist())
        assert_true("G01_branch_doc_present" in deleted_failures, str(deleted_failures))
        assert_true("G10_no_deleted_required_evidence" in deleted_failures, str(deleted_failures))


if __name__ == "__main__":
    main()
