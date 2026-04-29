#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


EXPECTED_TOTAL_PATH_MATCHES = 1935
EXPECTED_P1_LIVE_TEMP_ROWS = 68
EXPECTED_P1_TEMP_INPUT_ROWS = 15
EXPECTED_CLOSED_ROWS = 14
EXPECTED_OPEN_GAP_ROWS = 1
EXPECTED_WORKFLOW_COUNTS = {
    "mlpe_field_trial": 7,
    "panel_engine_common_cause": 2,
    "panel_engine_prepatch_scorecard": 1,
    "panel_engine_voltage_preserved": 5,
}
EXPECTED_OPEN_GAP_FILE = "research/prognostics/build_panel_day_engine_result_delta_scorecard_v1.py"


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research/prognostics/build_p1_temp_input_default_gap_audit_v1.py"
    with tempfile.TemporaryDirectory(prefix="p1_temp_input_default_gap_audit_") as tmpdir:
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
            (output_dir / "p1_temp_input_default_gap_audit_v1.json").read_text(encoding="utf-8")
        )
        detail = pd.read_csv(output_dir / "p1_temp_input_default_gap_audit_v1.csv")
        summary = pd.read_csv(output_dir / "p1_temp_input_default_gap_audit_summary_v1.csv")
        note = (output_dir / "p1_temp_input_default_gap_audit_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["path_portability_total_matches"] == EXPECTED_TOTAL_PATH_MATCHES, payload)
        assert_true(payload["p0_stale_worktree_rows"] == 0, payload)
        assert_true(payload["p1_live_temp_reference_rows"] == EXPECTED_P1_LIVE_TEMP_ROWS, payload)
        assert_true(payload["p1_temp_input_default_rows"] == EXPECTED_P1_TEMP_INPUT_ROWS, payload)
        assert_true(payload["closed_rows"] == EXPECTED_CLOSED_ROWS, payload)
        assert_true(payload["open_gap_rows"] == EXPECTED_OPEN_GAP_ROWS, payload)
        assert_true(payload["mlpe_guarded_user_filled_rows"] == 7, payload)
        assert_true(payload["non_mlpe_manifest_or_explicit_closed_rows"] == 7, payload)
        assert_true(payload["explicit_cli_only_open_rows"] == 1, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["bulk_rewrite_allowed_rows"] == 0, payload)
        assert_true(payload["expected_counts_match"] == 1, payload)
        assert_true(payload["expected_workflow_match"] == 1, payload)
        assert_true(payload["closure_complete"] == 1, payload)
        assert_true(payload["open_gap_files"] == [EXPECTED_OPEN_GAP_FILE], payload)
        for key, count in EXPECTED_WORKFLOW_COUNTS.items():
            assert_true(payload["workflow_lane_counts"][key] == count, payload)

        open_rows = detail[detail["closure_status"].eq("needs_patch")]
        assert_true(len(open_rows) == 1, detail.to_dict("records"))
        open_row = open_rows.iloc[0]
        assert_true(open_row["relative_path"] == EXPECTED_OPEN_GAP_FILE, open_row.to_dict())
        assert_true(open_row["default_constant"] == "DEFAULT_RUNTIME_ROOT", open_row.to_dict())
        assert_true(open_row["explicit_cli_flag"] == "--runtime-root", open_row.to_dict())
        assert_true(int(open_row["has_explicit_cli_arg"]) == 1, open_row.to_dict())
        assert_true(int(open_row["has_input_manifest_arg"]) == 1, open_row.to_dict())
        assert_true(int(open_row["has_source_specific_manifest_resolver"]) == 0, open_row.to_dict())
        assert_true("explicit-CLI-only legacy default" in note, note)
        assert_true(
            int(summary[summary["key"].eq("open_gap_rows")]["count"].iloc[0])
            == EXPECTED_OPEN_GAP_ROWS,
            summary.to_dict("records"),
        )

    print("smoke ok: p1_temp_input_default_gap_audit_v1")


if __name__ == "__main__":
    main()
