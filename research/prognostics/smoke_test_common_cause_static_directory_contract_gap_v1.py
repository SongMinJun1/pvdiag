#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


EXPECTED_ROWS = 8
EXPECTED_SOURCE_FILES = 5
EXPECTED_CLOSED_ROWS = 3
EXPECTED_GAP_ROWS = 5
EXPECTED_MISSING_CHECKS = 10


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research/prognostics/build_common_cause_static_directory_contract_gap_v1.py"
    with tempfile.TemporaryDirectory(prefix="common_cause_static_directory_contract_gap_smoke_") as tmpdir:
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
            (output_dir / "common_cause_static_directory_contract_gap_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "common_cause_static_directory_contract_gap_v1.csv")
        summary = pd.read_csv(output_dir / "common_cause_static_directory_contract_gap_summary_v1.csv")
        note = (output_dir / "common_cause_static_directory_contract_gap_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["common_cause_directory_rows"] == EXPECTED_ROWS, payload)
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
        assert_true(payload["contract_complete"] == 0, payload)
        assert_true(len(detail) == EXPECTED_ROWS, detail.to_dict("records"))
        assert_true(set(detail["contract_status"]) == {"closed", "needs_patch"}, detail.to_dict("records"))
        assert_true(
            payload["common_cause_directory_rows"]
            == int(summary[summary["key"].eq("common_cause_directory_rows")]["count"].iloc[0]),
            payload,
        )
        assert_true("not fully contract-closed" in note, note)

    print("smoke ok: common_cause_static_directory_contract_gap_v1")


if __name__ == "__main__":
    main()
