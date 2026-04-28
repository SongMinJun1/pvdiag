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
    with tempfile.TemporaryDirectory(prefix="mlpe_field_trial_handoff_guard_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        schema_dir = tmp / "schema"
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
                "research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py",
                "--repo-root",
                str(repo_root),
                "--capture-input",
                str(schema_dir / "mlpe_field_trial_capture_template_v1.csv"),
                "--output-dir",
                str(readiness_dir),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_operator_intake_guide_v1.py",
                "--repo-root",
                str(repo_root),
                "--capture-input",
                str(schema_dir / "mlpe_field_trial_capture_template_v1.csv"),
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
        ]
        for cmd in commands:
            proc = run(cmd, repo_root)
            assert_true(proc.returncode == 0, proc.stderr or proc.stdout)

        guard_proc = run(
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
            repo_root,
        )
        assert_true(guard_proc.returncode == 0, guard_proc.stderr or guard_proc.stdout)
        payload = json.loads(guard_proc.stdout)
        assert_true(payload["rows"] == 14, payload)
        assert_true(payload["adjudication_handoff_allowed_rows"] == 0, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)

        guard = pd.read_csv(guard_dir / "mlpe_field_trial_adjudication_handoff_guard_v1.csv")
        assert_true(set(guard["guard_bucket"]) == {"blocked_planned_capture"}, guard)
        print(json.dumps({"smoke": "ok", "rows": int(len(guard))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
