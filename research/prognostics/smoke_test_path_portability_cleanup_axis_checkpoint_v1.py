#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research/prognostics/build_path_portability_cleanup_axis_checkpoint_v1.py"
    with tempfile.TemporaryDirectory(prefix="path_portability_cleanup_axis_checkpoint_") as tmpdir:
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
            (output_dir / "path_portability_cleanup_axis_checkpoint_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "path_portability_cleanup_axis_checkpoint_v1.csv")
        summary = pd.read_csv(
            output_dir / "path_portability_cleanup_axis_checkpoint_summary_v1.csv"
        )
        note = (output_dir / "path_portability_cleanup_axis_checkpoint_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["checkpoint_ready"] == 1, payload)
        assert_true(payload["checkpoint_fail_rows"] == 0, payload)
        assert_true(payload["path_portability_axis_current_blocker_rows"] == 0, payload)
        assert_true(payload["path_portability_axis_currently_blocking"] == 0, payload)
        assert_true(payload["path_portability_axis_closed_as_current_blocker"] == 1, payload)
        assert_true(payload["path_portability_zero_literal_cleanup_claim"] == 0, payload)
        assert_true(payload["path_portability_total_matches"] > 0, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["operator_facing_change_allowed_rows"] == 0, payload)
        assert_true(payload["engine_patch_allowed_rows"] == 0, payload)
        assert_true(payload["bulk_rewrite_allowed_rows"] == 0, payload)
        assert_true(payload["return_to_algorithm_or_field_trial_readiness_allowed"] == 1, payload)
        assert_true(set(detail["checkpoint_status"]) == {"pass"}, detail.to_dict("records"))
        assert_true(
            int(summary[summary["key"].eq("checkpoint_ready")]["count"].iloc[0]) == 1,
            summary.to_dict("records"),
        )
        assert_true("does not claim every path literal has been removed" in note, note)
        assert_true("no longer treated as the active blocker" in note, note)

    print("smoke ok: path_portability_cleanup_axis_checkpoint_v1")


if __name__ == "__main__":
    main()
