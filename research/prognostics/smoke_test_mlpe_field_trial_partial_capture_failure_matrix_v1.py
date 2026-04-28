#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="mlpe_field_trial_failure_matrix_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        schema_dir = tmp / "schema"
        matrix_dir = tmp / "matrix"
        readiness_dir = tmp / "readiness"
        intake_dir = tmp / "intake"
        manifest_dir = tmp / "manifest"
        guard_dir = tmp / "guard"

        commands = [
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_schema_v1.py",
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(schema_dir),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_partial_capture_failure_matrix_v1.py",
                "--repo-root",
                str(repo_root),
                "--capture-input",
                str(schema_dir / "mlpe_field_trial_capture_template_v1.csv"),
                "--output-dir",
                str(matrix_dir),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py",
                "--repo-root",
                str(repo_root),
                "--capture-input",
                str(matrix_dir / "mlpe_field_trial_partial_capture_failure_matrix_input_v1.csv"),
                "--output-dir",
                str(readiness_dir),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_operator_intake_guide_v1.py",
                "--repo-root",
                str(repo_root),
                "--capture-input",
                str(matrix_dir / "mlpe_field_trial_partial_capture_failure_matrix_input_v1.csv"),
                "--readiness-input",
                str(readiness_dir / "mlpe_field_trial_capture_readiness_packet_v1.csv"),
                "--output-dir",
                str(intake_dir),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_package_manifest_v1.py",
                "--repo-root",
                str(repo_root),
                "--schema-dir",
                str(schema_dir),
                "--readiness-dir",
                str(readiness_dir),
                "--intake-dir",
                str(intake_dir),
                "--output-dir",
                str(manifest_dir),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_adjudication_handoff_guard_v1.py",
                "--repo-root",
                str(repo_root),
                "--readiness-input",
                str(readiness_dir / "mlpe_field_trial_capture_readiness_packet_v1.csv"),
                "--manifest-summary-input",
                str(manifest_dir / "mlpe_field_trial_package_manifest_summary_v1.csv"),
                "--output-dir",
                str(guard_dir),
            ],
        ]
        for cmd in commands:
            proc = run(cmd, repo_root)
            assert_true(proc.returncode == 0, proc.stderr or proc.stdout)

        expected = pd.read_csv(matrix_dir / "mlpe_field_trial_partial_capture_expected_buckets_v1.csv")
        readiness = pd.read_csv(readiness_dir / "mlpe_field_trial_capture_readiness_packet_v1.csv")
        guard = pd.read_csv(guard_dir / "mlpe_field_trial_adjudication_handoff_guard_v1.csv")
        merged = expected.merge(readiness[["trial_event_id", "readiness_bucket"]], on="trial_event_id", how="left")
        merged = merged.merge(guard[["trial_event_id", "guard_bucket", "truth_intake_allowed"]], on="trial_event_id", how="left")
        assert_true((merged["expected_readiness_bucket"] == merged["readiness_bucket"]).all(), merged)
        assert_true((merged["expected_guard_bucket"] == merged["guard_bucket"]).all(), merged)
        assert_true(guard["adjudication_handoff_allowed"].sum() == 1, guard)
        assert_true(guard["truth_intake_allowed"].sum() == 0, guard)
        assert_true(guard["engine_patch_allowed"].sum() == 0, guard)
        print(json.dumps({"smoke": "ok", "rows": int(len(merged))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
