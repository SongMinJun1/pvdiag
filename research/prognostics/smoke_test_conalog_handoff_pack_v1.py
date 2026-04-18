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
APP_SCRIPT = REPO_ROOT / "app/run_conalog_infer.py"
BUILD_SCRIPT = REPO_ROOT / "research/prognostics/build_conalog_handoff_pack_v1.py"
SELF_SCRIPT = REPO_ROOT / "research/prognostics/smoke_test_conalog_handoff_pack_v1.py"
PACK_ROOT = REPO_ROOT / "delivery/conalog_handoff_v1"
PACK_SMOKE = PACK_ROOT / "tests/smoke_test_conalog_handoff.py"

WATCH_OUTPUTS = [
    REPO_ROOT / "_share/panel_day_engine_panel_multiaxis_verdict_v1.csv",
    REPO_ROOT / "_share/panel_day_engine_gpvs_evidence_pack_v1.csv",
    REPO_ROOT / "_share/panel_day_engine_integrated_result_table_v1.csv",
    REPO_ROOT / "_share/panel_day_engine_cause_candidate_heuristics_v1.csv",
]

EXPECTED_PACK_FILES = [
    PACK_ROOT / "README.md",
    PACK_ROOT / "INPUT_SCHEMA.md",
    PACK_ROOT / "OUTPUT_SCHEMA.md",
    PACK_ROOT / "ALGORITHM_SPEC.md",
    PACK_ROOT / "RUNBOOK.md",
    PACK_ROOT / "KNOWN_LIMITS.md",
    PACK_ROOT / "CHANGELOG.md",
    PACK_ROOT / "config/default.yaml",
    PACK_ROOT / "docker/Dockerfile",
    PACK_ROOT / "examples/input_sample.csv",
    PACK_ROOT / "examples/output_panel_result_sample.csv",
    PACK_ROOT / "tests/smoke_test_conalog_handoff.py",
]

EXPECTED_PANEL_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "conalog_원인군_ko",
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


def main() -> None:
    py_compile.compile(str(REPO_ROOT / "pv_ae/panel_day_engine.py"), doraise=True)
    py_compile.compile(str(APP_SCRIPT), doraise=True)
    py_compile.compile(str(BUILD_SCRIPT), doraise=True)
    py_compile.compile(str(SELF_SCRIPT), doraise=True)

    before_signatures = {path: file_signature(path) for path in WATCH_OUTPUTS}

    help_result = run([sys.executable, str(APP_SCRIPT), "--help"])
    assert_true(help_result.returncode == 0, f"--help failed: {help_result.stderr or help_result.stdout}")

    build_result = run([sys.executable, str(BUILD_SCRIPT)])
    assert_true(build_result.returncode == 0, f"build failed: {build_result.stderr or build_result.stdout}")

    for path in EXPECTED_PACK_FILES:
        assert_true(path.exists(), f"missing pack file: {path}")

    with tempfile.TemporaryDirectory(prefix="conalog_handoff_smoke_input_") as input_dir, tempfile.TemporaryDirectory(
        prefix="conalog_handoff_smoke_output_"
    ) as output_dir:
        temp_input_root = Path(input_dir)
        shutil.copy2(PACK_ROOT / "examples/input_sample.csv", temp_input_root / "input_sample.csv")
        dry_run_result = run(
            [
                sys.executable,
                str(APP_SCRIPT),
                "--dry-run",
                "--input-root",
                str(temp_input_root),
                "--output-root",
                str(Path(output_dir)),
                "--config",
                str(PACK_ROOT / "config/default.yaml"),
                "--include-experimental",
                "off",
            ]
        )
        assert_true(dry_run_result.returncode == 0, f"dry-run failed: {dry_run_result.stderr or dry_run_result.stdout}")
        metadata_path = Path(output_dir) / "output/run_metadata_v1.json"
        error_log_path = Path(output_dir) / "output/error_log_v1.csv"
        assert_true(metadata_path.exists(), f"missing dry-run metadata: {metadata_path}")
        assert_true(error_log_path.exists(), f"missing dry-run error log: {error_log_path}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert_true(metadata.get("dry_run") is True, "dry_run metadata flag must be true")
        assert_true(metadata.get("include_experimental") == "off", "include_experimental metadata mismatch")

    sample_df = pd.read_csv(
        PACK_ROOT / "examples/output_panel_result_sample.csv",
        low_memory=False,
        encoding="utf-8-sig",
    )
    assert_true(sample_df.columns.tolist() == EXPECTED_PANEL_COLS, f"sample panel result schema mismatch: {sample_df.columns.tolist()}")
    assert_true(len(sample_df) >= 1, "sample panel result must contain at least one row")

    pack_smoke_result = run([sys.executable, str(PACK_SMOKE)])
    assert_true(pack_smoke_result.returncode == 0, f"delivery pack smoke failed: {pack_smoke_result.stderr or pack_smoke_result.stdout}")

    after_signatures = {path: file_signature(path) for path in WATCH_OUTPUTS}
    for path in WATCH_OUTPUTS:
        assert_true(before_signatures[path] == after_signatures[path], f"frozen production output changed: {path}")


if __name__ == "__main__":
    main()
