#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


EXPECTED_ROWS = 6
EXPECTED_EMBEDDED_REPRO_ROWS = 4
EXPECTED_DETECTOR_LITERAL_ROWS = 2
EXPECTED_SOURCE_FILES = 6


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research/prognostics/build_live_temp_literal_repro_closure_audit_v1.py"
    with tempfile.TemporaryDirectory(prefix="live_temp_literal_repro_closure_audit_") as tmpdir:
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
            (output_dir / "live_temp_literal_repro_closure_audit_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "live_temp_literal_repro_closure_audit_v1.csv")
        summary = pd.read_csv(output_dir / "live_temp_literal_repro_closure_audit_summary_v1.csv")
        note = (output_dir / "live_temp_literal_repro_closure_audit_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["literal_or_repro_rows"] == EXPECTED_ROWS, payload)
        assert_true(payload["embedded_note_repro_command_rows"] == EXPECTED_EMBEDDED_REPRO_ROWS, payload)
        assert_true(
            payload["intentional_temp_detection_literal_rows"] == EXPECTED_DETECTOR_LITERAL_ROWS,
            payload,
        )
        assert_true(payload["source_file_count"] == EXPECTED_SOURCE_FILES, payload)
        assert_true(payload["requires_manifest_or_explicit_input_rows"] == 0, payload)
        assert_true(payload["input_contract_gap_rows"] == 0, payload)
        assert_true(payload["operator_action_required_rows"] == 0, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["bulk_rewrite_allowed_rows"] == 0, payload)
        assert_true(payload["closure_complete"] == 1, payload)
        assert_true(len(detail) == EXPECTED_ROWS, detail.to_dict("records"))
        assert_true(
            set(detail["closure_class"])
            == {"closed_embedded_repro_command", "closed_intentional_detector_literal"},
            detail.to_dict("records"),
        )
        assert_true(
            payload["literal_or_repro_rows"]
            == int(summary[summary["key"].eq("literal_or_repro_rows")]["count"].iloc[0]),
            payload,
        )
        assert_true("closure complete" in note, note)

    print("smoke ok: live_temp_literal_repro_closure_audit_v1")


if __name__ == "__main__":
    main()
