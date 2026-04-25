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
    with tempfile.TemporaryDirectory(prefix="mlpe_field_trial_manifest_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        schema_dir = tmp / "schema"
        readiness_dir = tmp / "readiness"
        intake_dir = tmp / "intake"
        manifest_dir = tmp / "manifest"

        schema_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_schema_v1.py",
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(schema_dir),
            ],
            repo_root,
        )
        assert_true(schema_proc.returncode == 0, schema_proc.stderr or schema_proc.stdout)

        readiness_proc = run(
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
            repo_root,
        )
        assert_true(readiness_proc.returncode == 0, readiness_proc.stderr or readiness_proc.stdout)

        intake_proc = run(
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
            repo_root,
        )
        assert_true(intake_proc.returncode == 0, intake_proc.stderr or intake_proc.stdout)

        manifest_proc = run(
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
            repo_root,
        )
        assert_true(manifest_proc.returncode == 0, manifest_proc.stderr or manifest_proc.stdout)
        payload = json.loads(manifest_proc.stdout)
        assert_true(payload["rows"] == 13, payload)
        assert_true(payload["required_missing_rows"] == 0, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)

        manifest = pd.read_csv(manifest_dir / "mlpe_field_trial_package_manifest_v1.csv")
        assert_true(manifest["exists_flag"].eq(1).all(), manifest)
        assert_true({"taxonomy", "capture_schema", "readiness", "operator_intake", "handoff"} <= set(manifest["stage"]), manifest)
        print(json.dumps({"smoke": "ok", "rows": int(len(manifest))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
