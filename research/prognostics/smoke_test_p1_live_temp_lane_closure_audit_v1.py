#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


EXPECTED_TOTAL_ROWS = 68
EXPECTED_REQUIRES_INPUT_ROWS = 62
EXPECTED_LITERAL_OR_REPRO_ROWS = 6
EXPECTED_DETAIL_ROWS = 9
EXPECTED_KIND_COUNTS = {
    "static_upstream_directory_input": 48,
    "static_upstream_artifact_input": 10,
    "runtime_result_bundle_input": 4,
    "embedded_note_repro_command": 4,
    "intentional_temp_detection_literal": 2,
}


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research/prognostics/build_p1_live_temp_lane_closure_audit_v1.py"
    with tempfile.TemporaryDirectory(prefix="p1_live_temp_lane_closure_audit_") as tmpdir:
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
            (output_dir / "p1_live_temp_lane_closure_audit_v1.json").read_text(encoding="utf-8")
        )
        detail = pd.read_csv(output_dir / "p1_live_temp_lane_closure_audit_v1.csv")
        summary = pd.read_csv(output_dir / "p1_live_temp_lane_closure_audit_summary_v1.csv")
        note = (output_dir / "p1_live_temp_lane_closure_audit_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["live_temp_reference_rows"] == EXPECTED_TOTAL_ROWS, payload)
        assert_true(
            payload["requires_manifest_or_explicit_input_rows"] == EXPECTED_REQUIRES_INPUT_ROWS,
            payload,
        )
        assert_true(payload["literal_or_repro_only_rows"] == EXPECTED_LITERAL_OR_REPRO_ROWS, payload)
        assert_true(payload["open_contract_gap_rows"] == 0, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["bulk_rewrite_allowed_rows"] == 0, payload)
        assert_true(payload["expected_kind_match"] == 1, payload)
        assert_true(payload["expected_directory_workflow_match"] == 1, payload)
        assert_true(payload["closure_complete"] == 1, payload)
        assert_true(payload["detail_rows"] == EXPECTED_DETAIL_ROWS, payload)
        for key, count in EXPECTED_KIND_COUNTS.items():
            assert_true(payload["live_reference_kind_counts"][key] == count, payload)
        assert_true(set(detail["closure_status"]) == {"closed"}, detail.to_dict("records"))
        assert_true(int(detail["open_contract_gap_rows"].sum()) == 0, detail.to_dict("records"))
        assert_true(
            payload["live_temp_reference_rows"]
            == int(summary[summary["key"].eq("live_temp_reference_rows")]["count"].iloc[0]),
            payload,
        )
        assert_true("closure complete" in note, note)

    print("smoke ok: p1_live_temp_lane_closure_audit_v1")


if __name__ == "__main__":
    main()
