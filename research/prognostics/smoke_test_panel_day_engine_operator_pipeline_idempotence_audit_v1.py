#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import hashlib
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
run_count_path = share / "stub_pipeline_run_count.txt"
run_count = int(run_count_path.read_text(encoding="utf-8")) if run_count_path.exists() else 0
run_count += 1
run_count_path.write_text(str(run_count), encoding="utf-8")

attention_count = 18
queue_count = 7
watch_now_count = 24
watch_review_count = 56
backlog_count = 1014
cluster_preview_count = 23
discovery_cluster_count = 5
cluster_delta_current_count = 5
unified_digest_count = 23
workflow_default_count = 23

if mode == "steady":
    overall_changed_count = 3 if run_count == 1 else 0
    cluster_delta_changed_count = 2 if run_count == 1 else 0
    unified_digest_changed_count = 2 if run_count == 1 else 0
    workflow_default_changed_count = 2 if run_count == 1 else 0
    final_pipeline_pass_flag = 1
    qa_pass_flag = 1
    qa_fail_count = 0
    qa_warn_count = 0
elif mode == "spurious_second_run":
    overall_changed_count = 3 if run_count == 1 else 1
    cluster_delta_changed_count = 2 if run_count == 1 else 1
    unified_digest_changed_count = 2 if run_count == 1 else 1
    workflow_default_changed_count = 2 if run_count == 1 else 1
    final_pipeline_pass_flag = 1
    qa_pass_flag = 1
    qa_fail_count = 0
    qa_warn_count = 0
else:
    overall_changed_count = 3 if run_count == 1 else 1
    cluster_delta_changed_count = 2 if run_count == 1 else 1
    unified_digest_changed_count = 2 if run_count == 1 else 1
    workflow_default_changed_count = 2 if run_count == 1 else 1
    final_pipeline_pass_flag = 1 if run_count == 1 else 0
    qa_pass_flag = 1 if run_count == 1 else 0
    qa_fail_count = 0 if run_count == 1 else 1
    qa_warn_count = 0

final_recommended_exit_code = 0 if final_pipeline_pass_flag == 1 else 1
pipeline_started_at_utc = "2026-04-08T00:00:00Z" if run_count == 1 else "2026-04-08T00:10:00Z"
pipeline_finished_at_utc = "2026-04-08T00:05:00Z" if run_count == 1 else "2026-04-08T00:15:00Z"

pipeline_manifest = pd.DataFrame([{
    "pipeline_started_at_utc": pipeline_started_at_utc,
    "pipeline_finished_at_utc": pipeline_finished_at_utc,
    "requested_sites_csv": args.sites,
    "refresh_succeeded_site_count": len([site for site in args.sites.split(",") if site.strip()]),
    "refresh_failed_site_count": 0,
    "refresh_baseline_built_flag": 1,
    "qa_executed_flag": 1,
    "qa_skip_reason": "",
    "qa_pass_flag": qa_pass_flag,
    "final_pipeline_pass_flag": final_pipeline_pass_flag,
    "final_recommended_exit_code": final_recommended_exit_code,
    "overall_attention_count": attention_count,
    "overall_queue_count": queue_count,
    "overall_watch_now_count": watch_now_count,
    "overall_watch_review_count": watch_review_count,
    "overall_backlog_count": backlog_count,
    "overall_changed_count": overall_changed_count,
    "overall_cluster_preview_count": cluster_preview_count,
    "overall_discovery_cluster_count": discovery_cluster_count,
    "overall_cluster_delta_current_count": cluster_delta_current_count,
    "overall_cluster_delta_changed_count": cluster_delta_changed_count,
    "overall_unified_digest_count": unified_digest_count,
    "overall_unified_digest_changed_count": unified_digest_changed_count,
    "overall_workflow_default_count": workflow_default_count,
    "overall_workflow_default_changed_count": workflow_default_changed_count,
}])
pipeline_manifest.to_csv(share / "panel_day_engine_operator_pipeline_manifest_v1.csv", index=False, encoding="utf-8-sig")

qa_summary = pd.DataFrame([{
    "generated_at_utc": pipeline_finished_at_utc,
    "qa_pass_flag": qa_pass_flag,
    "fail_count": qa_fail_count,
    "warn_count": qa_warn_count,
    "overall_cluster_delta_changed_count": cluster_delta_changed_count,
    "overall_unified_digest_changed_count": unified_digest_changed_count,
    "overall_workflow_default_changed_count": workflow_default_changed_count,
}])
qa_summary.to_csv(share / "panel_day_engine_operator_refresh_qa_summary_v1.csv", index=False, encoding="utf-8-sig")

baseline_manifest = pd.DataFrame([{
    "generated_at_utc": pipeline_finished_at_utc,
    "attention_count": attention_count,
    "queue_count": queue_count,
    "workflow_default_item_count": workflow_default_count,
}])
baseline_manifest.to_csv(share / "panel_day_engine_operator_baseline_manifest_v1.csv", index=False, encoding="utf-8-sig")

raise SystemExit(final_recommended_exit_code)
"""
    write_script(root / "research/prognostics/build_panel_day_engine_operator_pipeline_v1.py", pipeline_script)
    (root / "_share").mkdir(parents=True, exist_ok=True)
    (root / "_share" / "mode.txt").write_text(mode, encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder_path = repo_root / "research/prognostics/build_panel_day_engine_operator_pipeline_idempotence_audit_v1.py"
    builder_mod = load_module(builder_path, "operator_pipeline_idempotence_audit")

    assert_true(
        builder_mod.parse_sites_csv(None) == ["conalog", "gangui", "ktc_ess", "sinhyo"],
        "default site parsing mismatch",
    )
    assert_true(
        builder_mod.parse_sites_csv("alpha, beta") == ["alpha", "beta"],
        "explicit site parsing mismatch",
    )

    official_paths = [
        repo_root / "_share" / "panel_day_engine_operator_pipeline_idempotence_report_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_pipeline_idempotence_summary_v1.csv",
    ]
    official_digests_before = {path: file_digest(path) for path in official_paths}

    py_compile.compile(str(builder_path), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="operator_pipeline_idempotence_steady_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_stub_root(tmp_root, mode="steady")
        result = run(
            [sys.executable, str(builder_path), "--root", str(tmp_root), "--sites", "alpha,beta"],
            repo_root,
        )
        assert_true(result.returncode == 0, result.stderr or result.stdout)

        report = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_operator_pipeline_idempotence_report_v1.csv",
            encoding="utf-8-sig",
        )
        summary = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_operator_pipeline_idempotence_summary_v1.csv",
            encoding="utf-8-sig",
        )
        assert_true(report.columns.tolist() == builder_mod.REPORT_COLS, "report schema mismatch")
        assert_true(summary.columns.tolist() == builder_mod.SUMMARY_COLS, "summary schema mismatch")
        for check_name in [
            "first_run_pipeline_pass",
            "second_run_pipeline_pass",
            "second_run_changed_count_zero",
            "second_run_cluster_delta_changed_zero",
            "second_run_unified_digest_changed_zero",
            "second_run_workflow_default_changed_zero",
            "first_vs_second_attention_count_equal",
            "first_vs_second_queue_count_equal",
            "first_vs_second_cluster_preview_count_equal",
            "first_vs_second_discovery_cluster_count_equal",
            "first_vs_second_workflow_default_count_equal",
            "first_vs_second_qa_pass_equal",
        ]:
            row = report.loc[report["check_name"].astype(str).eq(check_name)].iloc[0]
            assert_true(row["status"] == "pass", f"steady-state check should pass: {check_name}")
        summary_row = summary.iloc[0]
        assert_true(int(summary_row["idempotence_pass_flag"]) == 1, "steady-state summary should pass")
        assert_true(int(summary_row["fail_count"]) == 0, "steady-state hard fail_count should be zero")
        assert_true(int(summary_row["second_run_changed_count"]) == 0, "steady-state second_run_changed_count mismatch")
        assert_true(
            int(summary_row["second_run_cluster_delta_changed_count"]) == 0,
            "steady-state second_run_cluster_delta_changed_count mismatch",
        )
        assert_true(
            int(summary_row["second_run_unified_digest_changed_count"]) == 0,
            "steady-state second_run_unified_digest_changed_count mismatch",
        )
        assert_true(
            int(summary_row["second_run_workflow_default_changed_count"]) == 0,
            "steady-state second_run_workflow_default_changed_count mismatch",
        )

    with tempfile.TemporaryDirectory(prefix="operator_pipeline_idempotence_fail_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_stub_root(tmp_root, mode="spurious_second_run")
        result = run(
            [sys.executable, str(builder_path), "--root", str(tmp_root), "--sites", "alpha,beta"],
            repo_root,
        )
        assert_true(result.returncode == 0, result.stderr or result.stdout)

        report = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_operator_pipeline_idempotence_report_v1.csv",
            encoding="utf-8-sig",
        )
        summary = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_operator_pipeline_idempotence_summary_v1.csv",
            encoding="utf-8-sig",
        )
        for check_name in [
            "second_run_changed_count_zero",
            "second_run_cluster_delta_changed_zero",
            "second_run_unified_digest_changed_zero",
            "second_run_workflow_default_changed_zero",
        ]:
            row = report.loc[report["check_name"].astype(str).eq(check_name)].iloc[0]
            assert_true(row["status"] == "fail", f"spurious second-run change should fail: {check_name}")
        summary_row = summary.iloc[0]
        assert_true(int(summary_row["idempotence_pass_flag"]) == 0, "spurious second-run case should fail idempotence")
        assert_true(int(summary_row["fail_count"]) >= 1, "spurious second-run case should increment hard fail_count")

    official_digests_after = {path: file_digest(path) for path in official_paths}
    assert_true(
        official_digests_after == official_digests_before,
        "smoke test must not modify official idempotence audit outputs under repository _share",
    )

    print("smoke_test_panel_day_engine_operator_pipeline_idempotence_audit_v1.py: PASS")


if __name__ == "__main__":
    main()
