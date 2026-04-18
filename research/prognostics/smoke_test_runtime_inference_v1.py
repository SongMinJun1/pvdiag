#!/usr/bin/env python3
from __future__ import annotations

import json
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_SCRIPT = REPO_ROOT / "app/run_realtime.py"
RUNTIME_CONFIG = REPO_ROOT / "config/runtime.yaml"
MEASURE_SCRIPT = REPO_ROOT / "research/prognostics/measure_runtime_inference_v1.py"
SMOKE_SCRIPT = REPO_ROOT / "research/prognostics/smoke_test_runtime_inference_v1.py"
HANDOFF_BUILD_SCRIPT = REPO_ROOT / "research/prognostics/build_conalog_handoff_pack_v1.py"
HANDOFF_EXAMPLE_INPUT = REPO_ROOT / "delivery/conalog_handoff_v1/examples/input_sample.csv"
LATENCY_OUTPUT = REPO_ROOT / "_share/panel_day_engine_runtime_latency_report_v1.csv"
READINESS_OUTPUT = REPO_ROOT / "_share/panel_day_engine_runtime_readiness_summary_v1.csv"

WATCH_OUTPUTS = [
    REPO_ROOT / "_share/panel_day_engine_panel_multiaxis_verdict_v1.csv",
    REPO_ROOT / "_share/panel_day_engine_gpvs_evidence_pack_v1.csv",
    REPO_ROOT / "_share/panel_day_engine_integrated_result_table_v1.csv",
    REPO_ROOT / "_share/panel_day_engine_cause_candidate_heuristics_v1.csv",
]

LATENCY_COLS = ["measurement_scope", "metric_name", "metric_value", "unit", "note_ko"]
READINESS_COLS = [
    "runtime_mode_ko",
    "measured_flag",
    "latest_run_possible_flag",
    "include_experimental_supported_flag",
    "note_ko",
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


def main() -> None:
    py_compile.compile(str(REPO_ROOT / "pv_ae/panel_day_engine.py"), doraise=True)
    py_compile.compile(str(RUNTIME_SCRIPT), doraise=True)
    py_compile.compile(str(MEASURE_SCRIPT), doraise=True)
    py_compile.compile(str(SMOKE_SCRIPT), doraise=True)

    ensure_handoff_pack()
    before_signatures = {path: file_signature(path) for path in WATCH_OUTPUTS}

    help_result = run([sys.executable, str(RUNTIME_SCRIPT), "--help"])
    assert_true(help_result.returncode == 0, f"--help failed: {help_result.stderr or help_result.stdout}")
    help_text = help_result.stdout
    for token in [
        "--input-root",
        "--output-root",
        "--config",
        "--mode",
        "--poll-seconds",
        "--include-experimental",
        "--dry-run",
    ]:
        assert_true(token in help_text, f"--help must expose {token}")

    with tempfile.TemporaryDirectory(prefix="pvdiag_runtime_dryrun_") as dryrun_dir:
        dry_run_result = run(
            [
                sys.executable,
                str(RUNTIME_SCRIPT),
                "--dry-run",
                "--input-root",
                ".",
                "--output-root",
                str(Path(dryrun_dir)),
                "--config",
                str(RUNTIME_CONFIG),
                "--mode",
                "once",
                "--include-experimental",
                "off",
            ]
        )
        assert_true(dry_run_result.returncode == 0, f"dry-run failed: {dry_run_result.stderr or dry_run_result.stdout}")
        metadata_path = Path(dryrun_dir) / "latest/conalog_run_metadata_v1.json"
        runtime_log_path = Path(dryrun_dir) / "latest/runtime_log_v1.jsonl"
        failure_log_path = Path(dryrun_dir) / "latest/failure_log_v1.jsonl"
        assert_true(metadata_path.exists(), f"missing dry-run metadata: {metadata_path}")
        assert_true(runtime_log_path.exists(), f"missing runtime log: {runtime_log_path}")
        assert_true(failure_log_path.exists(), f"missing failure log: {failure_log_path}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert_true(metadata.get("dry_run") is True, "dry_run metadata flag must be true")
        assert_true(metadata.get("runtime_mode") == "once", "dry-run runtime_mode mismatch")

    with tempfile.TemporaryDirectory(prefix="pvdiag_runtime_input_") as input_dir, tempfile.TemporaryDirectory(
        prefix="pvdiag_runtime_output_"
    ) as output_dir:
        shutil.copy2(HANDOFF_EXAMPLE_INPUT, Path(input_dir) / "input_sample.csv")
        once_result = run(
            [
                sys.executable,
                str(RUNTIME_SCRIPT),
                "--input-root",
                str(Path(input_dir)),
                "--output-root",
                str(Path(output_dir)),
                "--config",
                str(RUNTIME_CONFIG),
                "--mode",
                "once",
                "--include-experimental",
                "off",
            ]
        )
        assert_true(once_result.returncode == 0, f"once mode failed: {once_result.stderr or once_result.stdout}")
        latest_dir = Path(output_dir) / "latest"
        for required in [
            latest_dir / "conalog_panel_result_v1.csv",
            latest_dir / "conalog_site_summary_v1.csv",
            latest_dir / "conalog_run_metadata_v1.json",
            latest_dir / "runtime_log_v1.jsonl",
            latest_dir / "failure_log_v1.jsonl",
        ]:
            assert_true(required.exists(), f"missing once-mode output: {required}")

    measure_result = run([sys.executable, str(MEASURE_SCRIPT)])
    assert_true(measure_result.returncode == 0, f"measurement script failed: {measure_result.stderr or measure_result.stdout}")
    assert_true(LATENCY_OUTPUT.exists(), f"missing latency report: {LATENCY_OUTPUT}")
    assert_true(READINESS_OUTPUT.exists(), f"missing readiness summary: {READINESS_OUTPUT}")

    latency_df = pd.read_csv(LATENCY_OUTPUT, low_memory=False, encoding="utf-8-sig")
    readiness_df = pd.read_csv(READINESS_OUTPUT, low_memory=False, encoding="utf-8-sig")
    assert_true(latency_df.columns.tolist() == LATENCY_COLS, f"latency report schema mismatch: {latency_df.columns.tolist()}")
    assert_true(readiness_df.columns.tolist() == READINESS_COLS, f"readiness summary schema mismatch: {readiness_df.columns.tolist()}")
    assert_true(readiness_df["runtime_mode_ko"].isin(["once", "poll"]).all(), "readiness summary mode values mismatch")

    after_signatures = {path: file_signature(path) for path in WATCH_OUTPUTS}
    for path in WATCH_OUTPUTS:
        assert_true(before_signatures[path] == after_signatures[path], f"frozen production output changed: {path}")


if __name__ == "__main__":
    main()
