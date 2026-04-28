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
    with tempfile.TemporaryDirectory(prefix="mlpe_field_trial_dry_run_gate_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        schema_dir = tmp / "schema"
        br107_root = tmp / "br107"
        br108_root = tmp / "br108"
        gate_dir = tmp / "gate"

        setup_commands = [
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
                "research/prognostics/build_mlpe_field_trial_filled_capture_fixture_v1.py",
                "--repo-root",
                str(repo_root),
                "--capture-input",
                str(schema_dir / "mlpe_field_trial_capture_template_v1.csv"),
                "--output-dir",
                str(br107_root),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py",
                "--repo-root",
                str(repo_root),
                "--capture-input",
                str(br107_root / "mlpe_field_trial_filled_capture_fixture_v1.csv"),
                "--output-dir",
                str(br107_root / "readiness"),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_operator_intake_guide_v1.py",
                "--repo-root",
                str(repo_root),
                "--capture-input",
                str(br107_root / "mlpe_field_trial_filled_capture_fixture_v1.csv"),
                "--readiness-input",
                str(br107_root / "readiness/mlpe_field_trial_capture_readiness_packet_v1.csv"),
                "--output-dir",
                str(br107_root / "intake"),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_package_manifest_v1.py",
                "--repo-root",
                str(repo_root),
                "--schema-dir",
                str(schema_dir),
                "--readiness-dir",
                str(br107_root / "readiness"),
                "--intake-dir",
                str(br107_root / "intake"),
                "--output-dir",
                str(br107_root / "manifest"),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_adjudication_handoff_guard_v1.py",
                "--repo-root",
                str(repo_root),
                "--readiness-input",
                str(br107_root / "readiness/mlpe_field_trial_capture_readiness_packet_v1.csv"),
                "--manifest-summary-input",
                str(br107_root / "manifest/mlpe_field_trial_package_manifest_summary_v1.csv"),
                "--output-dir",
                str(br107_root / "guard"),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_partial_capture_failure_matrix_v1.py",
                "--repo-root",
                str(repo_root),
                "--capture-input",
                str(schema_dir / "mlpe_field_trial_capture_template_v1.csv"),
                "--output-dir",
                str(br108_root),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py",
                "--repo-root",
                str(repo_root),
                "--capture-input",
                str(br108_root / "mlpe_field_trial_partial_capture_failure_matrix_input_v1.csv"),
                "--output-dir",
                str(br108_root / "readiness"),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_operator_intake_guide_v1.py",
                "--repo-root",
                str(repo_root),
                "--capture-input",
                str(br108_root / "mlpe_field_trial_partial_capture_failure_matrix_input_v1.csv"),
                "--readiness-input",
                str(br108_root / "readiness/mlpe_field_trial_capture_readiness_packet_v1.csv"),
                "--output-dir",
                str(br108_root / "intake"),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_package_manifest_v1.py",
                "--repo-root",
                str(repo_root),
                "--schema-dir",
                str(schema_dir),
                "--readiness-dir",
                str(br108_root / "readiness"),
                "--intake-dir",
                str(br108_root / "intake"),
                "--output-dir",
                str(br108_root / "manifest"),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_adjudication_handoff_guard_v1.py",
                "--repo-root",
                str(repo_root),
                "--readiness-input",
                str(br108_root / "readiness/mlpe_field_trial_capture_readiness_packet_v1.csv"),
                "--manifest-summary-input",
                str(br108_root / "manifest/mlpe_field_trial_package_manifest_summary_v1.csv"),
                "--output-dir",
                str(br108_root / "guard"),
            ],
        ]
        for cmd in setup_commands:
            proc = run(cmd, repo_root)
            assert_true(proc.returncode == 0, proc.stderr or proc.stdout)

        proc = run(
            [
                sys.executable,
                "research/prognostics/check_mlpe_field_trial_pre_adjudication_dry_run_gate_v1.py",
                "--repo-root",
                str(repo_root),
                "--br107-root",
                str(br107_root),
                "--br108-root",
                str(br108_root),
                "--output-dir",
                str(gate_dir),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["gate_rows"] == 8, payload)
        assert_true(payload["failed_rows"] == 0, payload)
        assert_true(payload["overall_passed_flag"] == 1, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        print(json.dumps({"smoke": "ok", "rows": payload["gate_rows"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
