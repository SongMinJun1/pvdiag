#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACK_ROOT.parents[1]
APP_SCRIPT = REPO_ROOT / "app/run_conalog_infer.py"
CONFIG_PATH = PACK_ROOT / "config/default.yaml"
INPUT_ROOT = PACK_ROOT / "examples"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)


def main() -> None:
    for path in [
        PACK_ROOT / "README.md",
        PACK_ROOT / "INPUT_SCHEMA.md",
        PACK_ROOT / "OUTPUT_SCHEMA.md",
        PACK_ROOT / "ALGORITHM_SPEC.md",
        PACK_ROOT / "RUNBOOK.md",
        PACK_ROOT / "KNOWN_LIMITS.md",
        PACK_ROOT / "CHANGELOG.md",
        CONFIG_PATH,
        INPUT_ROOT / "input_sample.csv",
        APP_SCRIPT,
    ]:
        assert_true(path.exists(), f"missing required path: {path}")

    help_result = run([sys.executable, str(APP_SCRIPT), "--help"])
    assert_true(help_result.returncode == 0, f"--help failed: {help_result.stderr or help_result.stdout}")

    with tempfile.TemporaryDirectory(prefix="conalog_handoff_pack_") as tmp_dir:
        output_root = Path(tmp_dir) / "dry_run"
        result = run(
            [
                sys.executable,
                str(APP_SCRIPT),
                "--dry-run",
                "--input-root",
                str(INPUT_ROOT),
                "--output-root",
                str(output_root),
                "--config",
                str(CONFIG_PATH),
                "--include-experimental",
                "off",
            ]
        )
        assert_true(result.returncode == 0, f"dry-run failed: {result.stderr or result.stdout}")
        metadata_path = output_root / "output/run_metadata_v1.json"
        error_log_path = output_root / "output/error_log_v1.csv"
        assert_true(metadata_path.exists(), f"missing metadata: {metadata_path}")
        assert_true(error_log_path.exists(), f"missing error log: {error_log_path}")
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert_true(payload.get("dry_run") is True, "dry_run metadata flag must be true")
        assert_true(payload.get("include_experimental") == "off", "include_experimental metadata mismatch")


if __name__ == "__main__":
    main()
