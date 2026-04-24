#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ONECLICK_SCRIPT = REPO_ROOT / "app/run_oneclick.py"
STREAMLIT_APP = REPO_ROOT / "app/app_streamlit.py"
DAILY_REPORT_SCRIPT = REPO_ROOT / "research/prognostics/build_daily_report_v1.py"
SMOKE_SCRIPT = REPO_ROOT / "research/prognostics/smoke_test_ops_oneclick_report_v1.py"
HANDOFF_BUILD_SCRIPT = REPO_ROOT / "research/prognostics/build_conalog_handoff_pack_v1.py"
RUNTIME_CONFIG = REPO_ROOT / "config/runtime.yaml"
HANDOFF_EXAMPLE_INPUT = REPO_ROOT / "delivery/conalog_handoff_v1/examples/input_sample.csv"

WATCH_OUTPUTS = [
    REPO_ROOT / "_share/panel_day_engine_panel_multiaxis_verdict_v1.csv",
    REPO_ROOT / "_share/panel_day_engine_gpvs_evidence_pack_v1.csv",
    REPO_ROOT / "_share/panel_day_engine_cause_candidate_heuristics_v1.csv",
]
OPTIONAL_EXPERIMENTAL_EXPORTS = {
    "gpvs_evidence_pack_v1.csv": REPO_ROOT / "_share/panel_day_engine_gpvs_evidence_pack_v1.csv",
    "cause_candidate_heuristics_v1.csv": REPO_ROOT / "_share/panel_day_engine_cause_candidate_heuristics_v1.csv",
}

EXPECTED_LATEST_FILES = [
    "conalog_panel_result_v1.csv",
    "conalog_site_summary_v1.csv",
    "conalog_run_metadata_v1.json",
    "daily_report_v1.md",
    "runtime_log_v1.jsonl",
    "failure_log_v1.jsonl",
]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)


def file_signature(path: Path) -> tuple[int, int] | None:
    if not path.exists():
        return None
    stat = path.stat()
    return (stat.st_size, stat.st_mtime_ns)


def ensure_handoff_pack() -> None:
    if HANDOFF_EXAMPLE_INPUT.exists():
        return
    result = run([sys.executable, str(HANDOFF_BUILD_SCRIPT)])
    assert_true(result.returncode == 0, f"handoff pack build failed: {result.stderr or result.stdout}")


def import_module_safely(path: Path) -> None:
    spec = importlib.util.spec_from_file_location("app_streamlit_foundation", path)
    assert_true(spec is not None and spec.loader is not None, f"failed to create import spec: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


def main() -> None:
    py_compile.compile(str(REPO_ROOT / "pv_ae/panel_day_engine.py"), doraise=True)
    py_compile.compile(str(ONECLICK_SCRIPT), doraise=True)
    py_compile.compile(str(STREAMLIT_APP), doraise=True)
    py_compile.compile(str(DAILY_REPORT_SCRIPT), doraise=True)
    py_compile.compile(str(SMOKE_SCRIPT), doraise=True)

    ensure_handoff_pack()
    before_signatures = {path: file_signature(path) for path in WATCH_OUTPUTS}

    help_result = run([sys.executable, str(ONECLICK_SCRIPT), "--help"])
    assert_true(help_result.returncode == 0, f"--help failed: {help_result.stderr or help_result.stdout}")

    with tempfile.TemporaryDirectory(prefix="pvdiag_oneclick_dryrun_") as dryrun_dir:
        dry_run_result = run(
            [
                sys.executable,
                str(ONECLICK_SCRIPT),
                "--dry-run",
                "--input-root",
                ".",
                "--output-root",
                str(Path(dryrun_dir)),
                "--config",
                str(RUNTIME_CONFIG),
                "--include-experimental",
                "off",
                "--report",
                "on",
            ]
        )
        assert_true(dry_run_result.returncode == 0, f"oneclick dry-run failed: {dry_run_result.stderr or dry_run_result.stdout}")
        latest_dir = Path(dryrun_dir) / "latest"
        assert_true((latest_dir / "conalog_run_metadata_v1.json").exists(), "dry-run must create runtime metadata")
        assert_true((latest_dir / "runtime_log_v1.jsonl").exists(), "dry-run must create runtime log")
        assert_true((latest_dir / "failure_log_v1.jsonl").exists(), "dry-run must create failure log")
        assert_true((latest_dir / "oneclick_plan_v1.json").exists(), "dry-run must create oneclick plan")

        report_result = run(
            [
                sys.executable,
                str(DAILY_REPORT_SCRIPT),
                "--output-root",
                str(Path(dryrun_dir)),
            ]
        )
        assert_true(report_result.returncode == 0, f"daily report build on dry-run root failed: {report_result.stderr or report_result.stdout}")
        assert_true((latest_dir / "daily_report_v1.md").exists(), "daily report must be generated")

    with tempfile.TemporaryDirectory(prefix="pvdiag_oneclick_input_") as input_dir, tempfile.TemporaryDirectory(
        prefix="pvdiag_oneclick_output_"
    ) as output_dir:
        shutil.copy2(HANDOFF_EXAMPLE_INPUT, Path(input_dir) / "input_sample.csv")
        oneclick_result = run(
            [
                sys.executable,
                str(ONECLICK_SCRIPT),
                "--input-root",
                str(Path(input_dir)),
                "--output-root",
                str(Path(output_dir)),
                "--config",
                str(RUNTIME_CONFIG),
                "--include-experimental",
                "on",
                "--report",
                "on",
            ]
        )
        assert_true(oneclick_result.returncode == 0, f"oneclick non-dry-run failed: {oneclick_result.stderr or oneclick_result.stdout}")
        latest_dir = Path(output_dir) / "latest"
        for filename in EXPECTED_LATEST_FILES:
            assert_true((latest_dir / filename).exists(), f"missing expected latest file: {latest_dir / filename}")
        assert_true((latest_dir / "conalog_reference_sidecar_v1.csv").exists(), "experimental sidecar must exist when enabled")
        plan = json.loads((latest_dir / "oneclick_plan_v1.json").read_text(encoding="utf-8"))
        optional_missing = set(plan.get("optional_missing_exports", []))
        for export_name, source_path in OPTIONAL_EXPERIMENTAL_EXPORTS.items():
            latest_export_path = latest_dir / export_name
            if source_path.exists():
                assert_true(latest_export_path.exists(), f"experimental export must exist when source exists: {latest_export_path}")
                assert_true(export_name not in optional_missing, f"present export should not be marked optional-missing: {export_name}")
            else:
                assert_true(not latest_export_path.exists(), f"missing optional export should not be fabricated: {latest_export_path}")
                assert_true(export_name in optional_missing, f"missing optional export should be recorded in plan: {export_name}")
        metadata = json.loads((latest_dir / "conalog_run_metadata_v1.json").read_text(encoding="utf-8"))
        assert_true(metadata.get("dry_run") is False, "non-dry-run metadata flag mismatch")

    import_module_safely(STREAMLIT_APP)

    after_signatures = {path: file_signature(path) for path in WATCH_OUTPUTS}
    for path in WATCH_OUTPUTS:
        assert_true(before_signatures[path] == after_signatures[path], f"frozen production output changed: {path}")


if __name__ == "__main__":
    main()
