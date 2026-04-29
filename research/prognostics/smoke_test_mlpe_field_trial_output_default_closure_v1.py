#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


EXPECTED_OUTPUT_DEFAULT_ROWS = 37


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research/prognostics/build_mlpe_field_trial_output_default_closure_v1.py"
    with tempfile.TemporaryDirectory(prefix="mlpe_output_default_closure_smoke_") as tmpdir:
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
            (output_dir / "mlpe_field_trial_output_default_closure_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "mlpe_field_trial_output_default_closure_v1.csv")
        summary = pd.read_csv(output_dir / "mlpe_field_trial_output_default_closure_summary_v1.csv")
        note = (output_dir / "mlpe_field_trial_output_default_closure_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["output_default_rows"] == EXPECTED_OUTPUT_DEFAULT_ROWS, payload)
        assert_true(payload["distinct_source_file_count"] == EXPECTED_OUTPUT_DEFAULT_ROWS, payload)
        assert_true(payload["closure_pass_count"] == EXPECTED_OUTPUT_DEFAULT_ROWS, payload)
        assert_true(payload["closure_fail_count"] == 0, payload)
        assert_true(payload["missing_cli_output_dir_override_rows"] == 0, payload)
        assert_true(payload["input_dependency_rows"] == 0, payload)
        assert_true(payload["generated_dependency_rows"] == 0, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["mass_rewrite_recommended_rows"] == 0, payload)
        assert_true(payload["missing_check_count"] == 0, payload)
        assert_true(payload["closure_complete"] == 1, payload)
        assert_true(len(detail) == EXPECTED_OUTPUT_DEFAULT_ROWS, detail.to_dict("records"))
        assert_true(set(detail["closure_status"]) == {"closed"}, detail.to_dict("records"))
        assert_true(detail["missing_checks"].fillna("").eq("").all(), detail.to_dict("records"))
        assert_true(
            payload["output_default_rows"]
            == int(summary[summary["key"].eq("output_default_rows")]["count"].iloc[0]),
            payload,
        )
        assert_true("BR-209 added one" in note, note)
        assert_true("does not add another" in note, note)

    print("smoke ok: mlpe_field_trial_output_default_closure_v1")


if __name__ == "__main__":
    main()
