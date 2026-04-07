#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import hashlib
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
    refresh_script = """#!/usr/bin/env python3
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
sites = [site.strip() for site in args.sites.split(",") if site.strip()]
(share / "refresh_call.txt").write_text(args.sites, encoding="utf-8")

if mode == "refresh_fail":
    manifest = pd.DataFrame([{
        "refresh_started_at_utc": "2026-04-05T00:00:00Z",
        "refresh_finished_at_utc": "2026-04-05T00:05:00Z",
        "requested_site_count": len(sites),
        "succeeded_site_count": max(len(sites) - 1, 0),
        "failed_site_count": 1,
        "baseline_built_flag": 0,
        "baseline_builder_return_code": "",
        "requested_sites_csv": args.sites,
        "succeeded_sites_csv": ",".join(sites[:-1]),
        "failed_sites_csv": sites[-1] if sites else "",
    }])
    manifest.to_csv(share / "panel_day_engine_operator_refresh_manifest_v1.csv", index=False, encoding="utf-8-sig")
    raise SystemExit(1)

manifest = pd.DataFrame([{
    "refresh_started_at_utc": "2026-04-05T00:00:00Z",
    "refresh_finished_at_utc": "2026-04-05T00:05:00Z",
    "requested_site_count": len(sites),
    "succeeded_site_count": len(sites),
    "failed_site_count": 0,
    "baseline_built_flag": 1,
    "baseline_builder_return_code": 0,
    "requested_sites_csv": args.sites,
    "succeeded_sites_csv": args.sites,
    "failed_sites_csv": "",
}])
manifest.to_csv(share / "panel_day_engine_operator_refresh_manifest_v1.csv", index=False, encoding="utf-8-sig")
"""
    qa_script = """#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
args = ap.parse_args()

root = Path(args.root)
share = root / "_share"
mode = (share / "mode.txt").read_text(encoding="utf-8").strip()
(share / "qa_called.txt").write_text("called", encoding="utf-8")

qa_pass_flag = 0 if mode == "qa_fail" else 1
summary = pd.DataFrame([{
    "generated_at_utc": "2026-04-05T00:06:00Z",
    "qa_pass_flag": qa_pass_flag,
    "fail_count": 1 if qa_pass_flag == 0 else 0,
    "warn_count": 0,
    "pass_count": 10 if qa_pass_flag == 1 else 9,
    "skip_count": 0,
    "overall_attention_count": 18,
    "overall_queue_count": 7,
    "overall_watch_now_count": 24,
    "overall_watch_review_count": 56,
    "overall_backlog_count": 1014,
    "overall_changed_count": 3,
    "overall_cluster_preview_count": 23,
    "overall_discovery_cluster_count": 5,
    "overall_cluster_preview_future_fault_linked_ref_count": 5,
    "overall_cluster_preview_future_truth_linked_ref_count": 0,
}])
summary.to_csv(share / "panel_day_engine_operator_refresh_qa_summary_v1.csv", index=False, encoding="utf-8-sig")
"""
    write_script(root / "research/prognostics/build_panel_day_engine_operator_refresh_v1.py", refresh_script)
    write_script(root / "research/prognostics/build_panel_day_engine_operator_refresh_qa_v1.py", qa_script)
    (root / "_share").mkdir(parents=True, exist_ok=True)
    (root / "_share" / "mode.txt").write_text(mode, encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_operator_pipeline_v1.py"
    build_module = load_module(build_path, "operator_pipeline_build")

    assert_true(
        build_module.parse_sites_csv(None) == ["conalog", "gangui", "ktc_ess", "sinhyo"],
        "default site parsing mismatch",
    )
    assert_true(
        build_module.parse_sites_csv("conalog, gangui") == ["conalog", "gangui"],
        "explicit site parsing mismatch",
    )

    official_paths = [repo_root / "_share" / "panel_day_engine_operator_pipeline_manifest_v1.csv"]
    official_digests_before = {path: file_digest(path) for path in official_paths}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_operator_pipeline_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_operator_pipeline_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="operator_pipeline_happy_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_stub_root(tmp_root, mode="happy")
        result = run(
            [sys.executable, str(build_path), "--root", str(tmp_root), "--sites", "alpha,beta"],
            repo_root,
        )
        assert_true(result.returncode == 0, result.stderr or result.stdout)
        manifest = pd.read_csv(tmp_root / "_share" / "panel_day_engine_operator_pipeline_manifest_v1.csv", encoding="utf-8-sig")
        assert_true(
            manifest.columns.tolist() == build_module.PIPELINE_MANIFEST_COLS,
            "pipeline manifest schema should include discovery preview enrichment fields",
        )
        row = manifest.iloc[0]
        assert_true(int(row["refresh_succeeded_site_count"]) == 2, "happy path succeeded count mismatch")
        assert_true(int(row["refresh_failed_site_count"]) == 0, "happy path failed count mismatch")
        assert_true(int(row["refresh_baseline_built_flag"]) == 1, "happy path baseline flag mismatch")
        assert_true(int(row["qa_executed_flag"]) == 1, "happy path qa should execute")
        assert_true(str(row["qa_skip_reason"]).strip() in {"", "nan"}, "happy path qa_skip_reason should be blank")
        assert_true(int(row["qa_pass_flag"]) == 1, "happy path qa_pass_flag mismatch")
        assert_true(int(row["final_pipeline_pass_flag"]) == 1, "happy path final pass mismatch")
        assert_true(int(row["final_recommended_exit_code"]) == 0, "happy path exit code mismatch")
        assert_true(int(row["overall_attention_count"]) == 18, "happy path overall_attention_count mismatch")
        assert_true(int(row["overall_queue_count"]) == 7, "happy path overall_queue_count mismatch")
        assert_true(int(row["overall_watch_now_count"]) == 24, "happy path overall_watch_now_count mismatch")
        assert_true(int(row["overall_watch_review_count"]) == 56, "happy path overall_watch_review_count mismatch")
        assert_true(int(row["overall_backlog_count"]) == 1014, "happy path overall_backlog_count mismatch")
        assert_true(int(row["overall_changed_count"]) == 3, "happy path overall_changed_count mismatch")
        assert_true(int(row["overall_cluster_preview_count"]) == 23, "happy path overall_cluster_preview_count mismatch")
        assert_true(int(row["overall_discovery_cluster_count"]) == 5, "happy path overall_discovery_cluster_count mismatch")
        assert_true(
            int(row["overall_cluster_preview_future_fault_linked_ref_count"]) == 5,
            "happy path overall_cluster_preview_future_fault_linked_ref_count mismatch",
        )
        assert_true(
            int(row["overall_cluster_preview_future_truth_linked_ref_count"]) == 0,
            "happy path overall_cluster_preview_future_truth_linked_ref_count mismatch",
        )
        assert_true(row["note_ko"] == "전체 operator pipeline 정상", "happy path note mismatch")
        assert_true(
            (tmp_root / "_share" / "refresh_call.txt").read_text(encoding="utf-8") == "alpha,beta",
            "refresh should receive requested sites",
        )
        assert_true((tmp_root / "_share" / "qa_called.txt").exists(), "QA should run on happy path")

    with tempfile.TemporaryDirectory(prefix="operator_pipeline_refresh_fail_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_stub_root(tmp_root, mode="refresh_fail")
        result = run(
            [sys.executable, str(build_path), "--root", str(tmp_root), "--sites", "alpha,beta,gamma"],
            repo_root,
        )
        assert_true(result.returncode == 1, "refresh-fail path should exit 1")
        manifest = pd.read_csv(tmp_root / "_share" / "panel_day_engine_operator_pipeline_manifest_v1.csv", encoding="utf-8-sig")
        row = manifest.iloc[0]
        assert_true(int(row["refresh_failed_site_count"]) == 1, "refresh-fail failed count mismatch")
        assert_true(int(row["refresh_baseline_built_flag"]) == 0, "refresh-fail baseline flag mismatch")
        assert_true(int(row["qa_executed_flag"]) == 0, "QA should be skipped when baseline not built")
        assert_true(row["qa_skip_reason"] == "baseline 미완료로 QA 건너뜀", "refresh-fail qa_skip_reason mismatch")
        assert_true(int(row["final_pipeline_pass_flag"]) == 0, "refresh-fail final pass mismatch")
        assert_true(int(row["final_recommended_exit_code"]) == 1, "refresh-fail recommended code mismatch")
        assert_true(int(row["overall_cluster_preview_count"]) == 0, "refresh-fail cluster preview count should remain zero")
        assert_true(
            int(row["overall_discovery_cluster_count"]) == 0,
            "refresh-fail discovery cluster count should remain zero",
        )
        assert_true(
            int(row["overall_cluster_preview_future_fault_linked_ref_count"]) == 0,
            "refresh-fail fault linked ref count should remain zero",
        )
        assert_true(
            int(row["overall_cluster_preview_future_truth_linked_ref_count"]) == 0,
            "refresh-fail truth linked ref count should remain zero",
        )
        assert_true(row["note_ko"] == "site refresh 실패로 baseline/QA 미완료", "refresh-fail note mismatch")
        assert_true(not (tmp_root / "_share" / "qa_called.txt").exists(), "QA should not run after refresh failure")

    with tempfile.TemporaryDirectory(prefix="operator_pipeline_qa_fail_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_stub_root(tmp_root, mode="qa_fail")
        result = run(
            [sys.executable, str(build_path), "--root", str(tmp_root), "--sites", "alpha,beta"],
            repo_root,
        )
        assert_true(result.returncode == 1, "qa-fail path should exit 1")
        manifest = pd.read_csv(tmp_root / "_share" / "panel_day_engine_operator_pipeline_manifest_v1.csv", encoding="utf-8-sig")
        row = manifest.iloc[0]
        assert_true(int(row["refresh_failed_site_count"]) == 0, "qa-fail refresh failure count mismatch")
        assert_true(int(row["refresh_baseline_built_flag"]) == 1, "qa-fail baseline flag mismatch")
        assert_true(int(row["qa_executed_flag"]) == 1, "qa-fail qa should execute")
        assert_true(str(row["qa_skip_reason"]).strip() in {"", "nan"}, "qa-fail qa_skip_reason should be blank")
        assert_true(int(row["qa_pass_flag"]) == 0, "qa-fail qa_pass_flag mismatch")
        assert_true(int(row["final_pipeline_pass_flag"]) == 0, "qa-fail final pass mismatch")
        assert_true(int(row["final_recommended_exit_code"]) == 1, "qa-fail recommended code mismatch")
        assert_true(int(row["overall_cluster_preview_count"]) == 23, "qa-fail overall_cluster_preview_count mismatch")
        assert_true(int(row["overall_discovery_cluster_count"]) == 5, "qa-fail overall_discovery_cluster_count mismatch")
        assert_true(
            int(row["overall_cluster_preview_future_fault_linked_ref_count"]) == 5,
            "qa-fail overall_cluster_preview_future_fault_linked_ref_count mismatch",
        )
        assert_true(
            int(row["overall_cluster_preview_future_truth_linked_ref_count"]) == 0,
            "qa-fail overall_cluster_preview_future_truth_linked_ref_count mismatch",
        )
        assert_true(row["note_ko"] == "QA 미통과로 운영 배포 보류", "qa-fail note mismatch")
        assert_true((tmp_root / "_share" / "qa_called.txt").exists(), "qa-fail path should still run QA")

    official_digests_after = {path: file_digest(path) for path in official_paths}
    assert_true(
        official_digests_after == official_digests_before,
        "smoke test must not modify official pipeline manifest under repository _share",
    )


if __name__ == "__main__":
    main()
