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
    with tempfile.TemporaryDirectory(prefix="mlpe_field_trial_operator_intake_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        schema_out = tmp / "schema"
        readiness_out = tmp / "readiness"
        intake_out = tmp / "operator_intake"

        schema_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_schema_v1.py",
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(schema_out),
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
                str(schema_out / "mlpe_field_trial_capture_template_v1.csv"),
                "--output-dir",
                str(readiness_out),
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
                str(schema_out / "mlpe_field_trial_capture_template_v1.csv"),
                "--readiness-input",
                str(readiness_out / "mlpe_field_trial_capture_readiness_packet_v1.csv"),
                "--output-dir",
                str(intake_out),
            ],
            repo_root,
        )
        assert_true(intake_proc.returncode == 0, intake_proc.stderr or intake_proc.stdout)
        payload = json.loads(intake_proc.stdout)
        assert_true(payload["rows"] == 14, payload)
        assert_true(payload["planning_rows"] == 14, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)

        checklist = pd.read_csv(intake_out / "mlpe_field_trial_operator_intake_checklist_v1.csv")
        field_guide = pd.read_csv(intake_out / "mlpe_field_trial_operator_intake_field_guide_v1.csv")
        assert_true(set(checklist["operator_phase"]) == {"planning"}, checklist)
        assert_true(checklist["br103_readiness_bucket"].eq("planned_waiting_for_capture").all(), checklist)
        assert_true("raw_data_path" in set(field_guide["field_name"]), field_guide)
        assert_true("final_fault_family" in set(field_guide["field_name"]), field_guide)
        print(json.dumps({"smoke": "ok", "rows": int(len(checklist))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
