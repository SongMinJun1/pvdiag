#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="mlpe_truth_gate_fixture_matrix_smoke_") as tmpdir:
        output_dir = Path(tmpdir) / "matrix"
        proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_truth_gate_fixture_matrix_v1.py",
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(output_dir),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["fixture_rows"] == 16, payload)
        assert_true(payload["case_pass_rows"] == 16, payload)
        assert_true(payload["mismatch_rows"] == 0, payload)
        assert_true(payload["expected_ready_rows"] == 3, payload)
        assert_true(payload["actual_ready_rows"] == 3, payload)
        assert_true(payload["expected_blocked_rows"] == 13, payload)
        assert_true(payload["actual_blocked_rows"] == 13, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)
        assert_true(Path(payload["outputs"]["mismatches"]).exists(), payload)
        print(json.dumps({"smoke": "ok", "fixture_rows": 16, "mismatch_rows": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
