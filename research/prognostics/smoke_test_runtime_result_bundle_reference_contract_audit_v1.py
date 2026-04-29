#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


EXPECTED_ROWS = 4
EXPECTED_SOURCE_FILES = 2
EXPECTED_CLOSED_ROWS = 4
EXPECTED_GAP_ROWS = 0
EXPECTED_MISSING_CHECKS = 0
SELF_NOISE_SOURCE = "research/prognostics/build_runtime_result_bundle_reference_contract_audit_v1.py"


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research/prognostics/build_runtime_result_bundle_reference_contract_audit_v1.py"
    live_review_builder = repo_root / "research/prognostics/build_repo_live_temp_reference_review_v1.py"
    with tempfile.TemporaryDirectory(prefix="runtime_result_bundle_reference_contract_audit_") as tmpdir:
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
            (output_dir / "runtime_result_bundle_reference_contract_audit_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "runtime_result_bundle_reference_contract_audit_v1.csv")
        summary = pd.read_csv(
            output_dir / "runtime_result_bundle_reference_contract_audit_summary_v1.csv"
        )
        note = (
            output_dir / "runtime_result_bundle_reference_contract_audit_note_v1.md"
        ).read_text(encoding="utf-8")

        assert_true(payload["runtime_result_bundle_rows"] == EXPECTED_ROWS, payload)
        assert_true(payload["source_file_count"] == EXPECTED_SOURCE_FILES, payload)
        assert_true(payload["contract_closed_rows"] == EXPECTED_CLOSED_ROWS, payload)
        assert_true(payload["contract_gap_rows"] == EXPECTED_GAP_ROWS, payload)
        assert_true(payload["input_manifest_arg_rows"] == EXPECTED_CLOSED_ROWS, payload)
        assert_true(payload["manifest_resolver_rows"] == EXPECTED_CLOSED_ROWS, payload)
        assert_true(payload["explicit_cli_arg_rows"] == EXPECTED_ROWS, payload)
        assert_true(payload["legacy_default_retained_rows"] == EXPECTED_ROWS, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["bulk_rewrite_allowed_rows"] == 0, payload)
        assert_true(payload["missing_check_count"] == EXPECTED_MISSING_CHECKS, payload)
        assert_true(payload["contract_complete"] == 1, payload)
        assert_true(len(detail) == EXPECTED_ROWS, detail.to_dict("records"))
        assert_true(set(detail["contract_status"]) == {"closed"}, detail.to_dict("records"))
        assert_true(
            payload["runtime_result_bundle_rows"]
            == int(summary[summary["key"].eq("runtime_result_bundle_rows")]["count"].iloc[0]),
            payload,
        )
        assert_true("fully contract-closed" in note, note)

        live_output_dir = Path(tmpdir) / "live_review"
        proc = subprocess.run(
            [
                sys.executable,
                str(live_review_builder),
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(live_output_dir),
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        live_detail = pd.read_csv(live_output_dir / "repo_live_temp_reference_review_v1.csv")
        assert_true(not live_detail["source_file"].eq(SELF_NOISE_SOURCE).any(), live_detail.to_dict("records"))

    print("smoke ok: runtime_result_bundle_reference_contract_audit_v1")


if __name__ == "__main__":
    main()
