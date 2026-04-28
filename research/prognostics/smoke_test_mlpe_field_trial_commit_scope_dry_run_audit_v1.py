#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "research" / "prognostics" / "build_mlpe_field_trial_commit_scope_dry_run_audit_v1.py"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, check=True, text=True, capture_output=True)


def write(path: Path, text: str = "x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def init_repo(root: Path) -> None:
    run(["git", "init", "-q"], cwd=root)
    write(root / "README.md", "seed\n")
    run(["git", "add", "README.md"], cwd=root)
    run(["git", "-c", "user.email=smoke@example.invalid", "-c", "user.name=Smoke", "commit", "-q", "-m", "seed"], cwd=root)


def run_builder(repo_root: Path, out_dir: Path) -> dict[str, object]:
    result = run(
        ["python3", str(BUILDER), "--repo-root", str(repo_root), "--output-dir", str(out_dir)],
        cwd=ROOT,
    )
    return json.loads(result.stdout)


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "good_repo"
        repo.mkdir()
        init_repo(repo)
        write(repo / "docs" / "OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md")
        write(repo / "docs" / "OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_143_PANEL_ENGINE_PREPATCH_GATE_REFRESH_V1.md")
        write(repo / "research" / "prognostics" / "build_mlpe_field_trial_real_capture_intake_contract_v1.py")
        write(repo / "research" / "prognostics" / "smoke_test_mlpe_field_trial_real_capture_intake_contract_v1.py")
        good = run_builder(repo, Path(td) / "good_out")
        assert good["dirty_files"] == 4
        assert good["risk_files"] == 0
        assert good["issue_rows"] == 0
        assert good["commit_scope_ready_flag"] == 1

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "bad_repo"
        repo.mkdir()
        init_repo(repo)
        write(repo / "pv_ae" / "panel_day_engine.py")
        write(repo / "data" / "conalog" / "raw" / "sample.csv")
        write(repo / "release" / "conalog_full_runtime_v1" / "pack_summary_v1.json", "{}\n")
        write(repo / "misc" / "unknown.txt")
        bad = run_builder(repo, Path(td) / "bad_out")
        assert bad["dirty_files"] == 4
        assert bad["risk_files"] == 4
        assert bad["issue_rows"] == 4
        assert bad["engine_source_dirty"] == 1
        assert bad["large_data_dirty"] == 1
        assert bad["release_generated_dirty"] == 1
        assert bad["unclassified_dirty"] == 1
        assert bad["commit_scope_ready_flag"] == 0
        issues = pd.read_csv(Path(td) / "bad_out" / "mlpe_field_trial_commit_scope_dry_run_issues_v1.csv", encoding="utf-8-sig")
        issue_types = set(issues["issue_type"])
        assert "panel_engine_source_dirty" in issue_types
        assert "large_site_data_dirty" in issue_types
        assert "generated_release_artifact_dirty" in issue_types
        assert "unclassified_dirty_path" in issue_types

    print(json.dumps({"smoke": "ok", "good_ready": 1, "bad_ready": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
