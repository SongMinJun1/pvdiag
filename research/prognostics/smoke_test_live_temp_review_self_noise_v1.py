#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


EXPECTED_LIVE_ROWS = 68
EXPECTED_STATIC_DIRECTORY_ROWS = 48
EXPECTED_STATIC_ARTIFACT_ROWS = 10
EXPECTED_RUNTIME_RESULT_BUNDLE_ROWS = 4
SELF_NOISE_SOURCE = "research/prognostics/build_static_artifact_reference_contract_gap_v1.py"


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research/prognostics/build_repo_live_temp_reference_review_v1.py"
    with tempfile.TemporaryDirectory(prefix="live_temp_review_self_noise_") as tmpdir:
        output_dir = Path(tmpdir) / "out"
        proc = subprocess.run(
            [
                sys.executable,
                str(builder),
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(output_dir),
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)

        payload = json.loads(
            (output_dir / "repo_live_temp_reference_review_v1.json").read_text(encoding="utf-8")
        )
        detail = pd.read_csv(output_dir / "repo_live_temp_reference_review_v1.csv")
        kind_counts = payload["live_reference_kind_counts"]

        assert_true(payload["live_temp_reference_rows"] == EXPECTED_LIVE_ROWS, payload)
        assert_true(kind_counts["static_upstream_directory_input"] == EXPECTED_STATIC_DIRECTORY_ROWS, payload)
        assert_true(kind_counts["static_upstream_artifact_input"] == EXPECTED_STATIC_ARTIFACT_ROWS, payload)
        assert_true(kind_counts["runtime_result_bundle_input"] == EXPECTED_RUNTIME_RESULT_BUNDLE_ROWS, payload)
        assert_true(not detail["source_file"].eq(SELF_NOISE_SOURCE).any(), detail.to_dict("records"))

    print("smoke ok: live_temp_review_self_noise_v1")


if __name__ == "__main__":
    main()
