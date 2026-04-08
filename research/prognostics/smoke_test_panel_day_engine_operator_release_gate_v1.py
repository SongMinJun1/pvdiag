#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert_true(spec is not None and spec.loader is not None, f"failed to load module: {path.name}")
    spec.loader.exec_module(module)
    return module


def write_script(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_stub_root(root: Path, *, mode: str) -> None:
    pipeline_script = """#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--sites", required=True)
ap.add_argument("--root", required=True)
args = ap.parse_args()

root = Path(args.root)
share = root / "_share"
share.mkdir(parents=True, exist_ok=True)
mode = (share / "mode.txt").read_text(encoding="utf-8").strip()

pipeline_pass_flag = 0 if mode == "pipeline_fail" else 1
exit_code = 0 if pipeline_pass_flag == 1 else 1

manifest = pd.DataFrame([{
    "pipeline_started_at_utc": "2026-04-08T10:00:00Z",
    "pipeline_finished_at_utc": "2026-04-08T10:05:00Z",
    "requested_sites_csv": args.sites,
    "refresh_succeeded_site_count": len([site for site in args.sites.split(",") if site.strip()]),
    "refresh_failed_site_count": 0 if pipeline_pass_flag == 1 else 1,
    "refresh_baseline_built_flag": pipeline_pass_flag,
    "qa_executed_flag": pipeline_pass_flag,
    "qa_skip_reason": "" if pipeline_pass_flag == 1 else "pipeline fixture fail",
    "qa_pass_flag": pipeline_pass_flag,
    "final_pipeline_pass_flag": pipeline_pass_flag,
    "final_recommended_exit_code": exit_code,
    "overall_attention_count": 18,
    "overall_queue_count": 7,
    "overall_watch_now_count": 24,
    "overall_watch_review_count": 56,
    "overall_backlog_count": 1014,
    "overall_changed_count": 0,
    "overall_cluster_preview_count": 23,
    "overall_discovery_cluster_count": 5,
    "overall_cluster_delta_current_count": 5,
    "overall_cluster_delta_changed_count": 0,
    "overall_unified_digest_count": 23,
    "overall_unified_digest_changed_count": 0,
    "overall_workflow_default_count": 23,
    "overall_workflow_default_changed_count": 0,
}])
manifest.to_csv(share / "panel_day_engine_operator_pipeline_manifest_v1.csv", index=False, encoding="utf-8-sig")

raise SystemExit(exit_code)
"""
    idempotence_script = """#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--sites", required=True)
ap.add_argument("--root", required=True)
args = ap.parse_args()

root = Path(args.root)
share = root / "_share"
share.mkdir(parents=True, exist_ok=True)
mode = (share / "mode.txt").read_text(encoding="utf-8").strip()
(share / "idempotence_called.txt").write_text("1", encoding="utf-8")

idempotence_pass_flag = 1 if mode == "happy" else 0
exit_code = 0 if idempotence_pass_flag == 1 else 1

summary = pd.DataFrame([{
    "audit_started_at_utc": "2026-04-08T10:06:00Z",
    "audit_finished_at_utc": "2026-04-08T10:09:00Z",
    "idempotence_pass_flag": idempotence_pass_flag,
    "fail_count": 0 if idempotence_pass_flag == 1 else 1,
    "pass_count": 12 if idempotence_pass_flag == 1 else 8,
    "first_run_pipeline_pass_flag": 1,
    "second_run_pipeline_pass_flag": 1 if idempotence_pass_flag == 1 else 0,
    "second_run_changed_count": 0 if idempotence_pass_flag == 1 else 1,
    "second_run_cluster_delta_changed_count": 0 if idempotence_pass_flag == 1 else 1,
    "second_run_unified_digest_changed_count": 0 if idempotence_pass_flag == 1 else 1,
    "second_run_workflow_default_changed_count": 0 if idempotence_pass_flag == 1 else 1,
    "note_ko": "fixture idempotence summary",
}])
summary.to_csv(share / "panel_day_engine_operator_pipeline_idempotence_summary_v1.csv", index=False, encoding="utf-8-sig")

raise SystemExit(exit_code)
"""
    write_script(root / "research/prognostics/build_panel_day_engine_operator_pipeline_v1.py", pipeline_script)
    write_script(
        root / "research/prognostics/build_panel_day_engine_operator_pipeline_idempotence_audit_v1.py",
        idempotence_script,
    )
    (root / "_share").mkdir(parents=True, exist_ok=True)
    (root / "_share" / "mode.txt").write_text(mode, encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder_path = repo_root / "research/prognostics/build_panel_day_engine_operator_release_gate_v1.py"
    builder_mod = load_module(builder_path, "operator_release_gate")

    assert_true(
        builder_mod.parse_sites_csv(None) == ["conalog", "gangui", "ktc_ess", "sinhyo"],
        "default site parsing mismatch",
    )
    assert_true(
        builder_mod.parse_sites_csv("alpha, beta") == ["alpha", "beta"],
        "explicit site parsing mismatch",
    )

    official_paths = [
        repo_root / "_share" / "panel_day_engine_operator_release_gate_manifest_v1.csv",
    ]
    official_digests_before = {path: file_digest(path) for path in official_paths}

    py_compile.compile(str(builder_path), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="operator_release_gate_happy_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_stub_root(tmp_root, mode="happy")
        result = run(
            [sys.executable, str(builder_path), "--root", str(tmp_root), "--sites", "alpha,beta"],
            repo_root,
        )
        assert_true(result.returncode == 0, result.stderr or result.stdout)
        manifest = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_operator_release_gate_manifest_v1.csv",
            encoding="utf-8-sig",
        )
        assert_true(manifest.columns.tolist() == builder_mod.RELEASE_GATE_MANIFEST_COLS, "manifest schema mismatch")
        row = manifest.iloc[0]
        assert_true(int(row["pipeline_executed_flag"]) == 1, "happy path should execute pipeline")
        assert_true(int(row["pipeline_pass_flag"]) == 1, "happy path pipeline_pass_flag mismatch")
        assert_true(int(row["idempotence_executed_flag"]) == 1, "happy path should execute idempotence audit")
        assert_true(int(row["idempotence_pass_flag"]) == 1, "happy path idempotence_pass_flag mismatch")
        assert_true(int(row["final_release_gate_pass_flag"]) == 1, "happy path final pass mismatch")
        assert_true(int(row["final_recommended_exit_code"]) == 0, "happy path exit code mismatch")
        assert_true(str(row["note_ko"]) == "operator stack release gate 통과", "happy path note mismatch")

    with tempfile.TemporaryDirectory(prefix="operator_release_gate_pipeline_fail_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_stub_root(tmp_root, mode="pipeline_fail")
        result = run(
            [sys.executable, str(builder_path), "--root", str(tmp_root), "--sites", "alpha,beta"],
            repo_root,
        )
        assert_true(result.returncode == 1, "pipeline-fail path should return exit 1")
        manifest = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_operator_release_gate_manifest_v1.csv",
            encoding="utf-8-sig",
        )
        row = manifest.iloc[0]
        assert_true(int(row["pipeline_pass_flag"]) == 0, "pipeline-fail path pipeline_pass_flag mismatch")
        assert_true(int(row["idempotence_executed_flag"]) == 0, "pipeline-fail path should skip idempotence")
        assert_true(int(row["idempotence_pass_flag"]) == 0, "pipeline-fail path idempotence_pass_flag mismatch")
        assert_true(int(row["final_release_gate_pass_flag"]) == 0, "pipeline-fail path final pass mismatch")
        assert_true(int(row["final_recommended_exit_code"]) == 1, "pipeline-fail path exit code mismatch")
        assert_true(
            str(row["note_ko"]) == "pipeline 실패로 idempotence 생략",
            "pipeline-fail path note mismatch",
        )
        assert_true(
            not (tmp_root / "_share" / "idempotence_called.txt").exists(),
            "pipeline-fail path must not call idempotence audit",
        )

    with tempfile.TemporaryDirectory(prefix="operator_release_gate_idempotence_fail_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_stub_root(tmp_root, mode="idempotence_fail")
        result = run(
            [sys.executable, str(builder_path), "--root", str(tmp_root), "--sites", "alpha,beta"],
            repo_root,
        )
        assert_true(result.returncode == 1, "idempotence-fail path should return exit 1")
        manifest = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_operator_release_gate_manifest_v1.csv",
            encoding="utf-8-sig",
        )
        row = manifest.iloc[0]
        assert_true(int(row["pipeline_pass_flag"]) == 1, "idempotence-fail path pipeline_pass_flag mismatch")
        assert_true(int(row["idempotence_executed_flag"]) == 1, "idempotence-fail path should execute audit")
        assert_true(int(row["idempotence_pass_flag"]) == 0, "idempotence-fail path idempotence_pass_flag mismatch")
        assert_true(int(row["final_release_gate_pass_flag"]) == 0, "idempotence-fail path final pass mismatch")
        assert_true(int(row["final_recommended_exit_code"]) == 1, "idempotence-fail path exit code mismatch")
        assert_true(
            str(row["note_ko"]) == "idempotence 미통과로 release 보류",
            "idempotence-fail path note mismatch",
        )
        assert_true(
            (tmp_root / "_share" / "idempotence_called.txt").exists(),
            "idempotence-fail path should call idempotence audit",
        )

    official_digests_after = {path: file_digest(path) for path in official_paths}
    assert_true(
        official_digests_after == official_digests_before,
        "smoke test must not modify official release gate outputs under repository _share",
    )

    print("smoke_test_panel_day_engine_operator_release_gate_v1.py: PASS")


if __name__ == "__main__":
    main()
