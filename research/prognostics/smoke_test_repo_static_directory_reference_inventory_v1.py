#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


EXPECTED_STATIC_DIRECTORY_ROWS = 48
EXPECTED_WORKFLOW_COUNTS = {
    "panel_day_engine_evidence": 20,
    "panel_engine_common_cause": 8,
    "panel_engine_episode_truth": 12,
    "panel_engine_prepatch_scorecard": 4,
    "panel_engine_voltage_preserved": 4,
}


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research/prognostics/build_repo_static_directory_reference_inventory_v1.py"
    with tempfile.TemporaryDirectory(prefix="repo_static_directory_reference_inventory_smoke_") as tmpdir:
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
            (output_dir / "repo_static_directory_reference_inventory_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "repo_static_directory_reference_inventory_v1.csv")
        summary = pd.read_csv(output_dir / "repo_static_directory_reference_inventory_summary_v1.csv")
        note = (output_dir / "repo_static_directory_reference_inventory_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["static_directory_rows"] == EXPECTED_STATIC_DIRECTORY_ROWS, payload)
        assert_true(payload["source_file_count"] == 29, payload)
        assert_true(
            payload["requires_manifest_or_explicit_directory_rows"]
            == EXPECTED_STATIC_DIRECTORY_ROWS,
            payload,
        )
        assert_true(payload["immediate_patch_allowed_rows"] == 0, payload)
        assert_true(payload["bulk_rewrite_allowed_rows"] == 0, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["inventory_complete"] == 1, payload)
        assert_true(payload["workflow_lane_counts"] == EXPECTED_WORKFLOW_COUNTS, payload)
        assert_true(len(detail) == EXPECTED_STATIC_DIRECTORY_ROWS, detail.to_dict("records"))
        assert_true(
            detail["requires_manifest_or_explicit_directory_flag"].astype(int).sum()
            == EXPECTED_STATIC_DIRECTORY_ROWS,
            detail.to_dict("records"),
        )
        assert_true(detail["immediate_patch_allowed_flag"].astype(int).sum() == 0, detail.to_dict("records"))
        assert_true(detail["bulk_rewrite_allowed_flag"].astype(int).sum() == 0, detail.to_dict("records"))
        assert_true(
            payload["static_directory_rows"]
            == int(summary[summary["key"].eq("static_directory_rows")]["count"].iloc[0]),
            payload,
        )
        assert_true("Do not bulk-rewrite" in note, note)

    print("smoke ok: repo_static_directory_reference_inventory_v1")


if __name__ == "__main__":
    main()
