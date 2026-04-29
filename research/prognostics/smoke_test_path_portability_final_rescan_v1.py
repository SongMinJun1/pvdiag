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
    builder = repo_root / "research/prognostics/build_path_portability_final_rescan_v1.py"
    with tempfile.TemporaryDirectory(prefix="path_portability_final_rescan_") as tmpdir:
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
            (output_dir / "path_portability_final_rescan_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "path_portability_final_rescan_v1.csv")
        summary = pd.read_csv(output_dir / "path_portability_final_rescan_summary_v1.csv")
        note = (output_dir / "path_portability_final_rescan_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["path_portability_total_matches"] > 0, payload)
        assert_true(payload["path_portability_zero_literal_cleanup_complete"] == 0, payload)
        assert_true(payload["p0_stale_worktree_rows"] == 0, payload)
        assert_true(payload["latest_handoff_residual_rows"] == 0, payload)
        assert_true(payload["evidence_manifest_residual_rows"] == 0, payload)
        assert_true(payload["current_action_required_rows"] == 0, payload)
        assert_true(payload["unexpected_generated_residual_rows"] == 0, payload)
        assert_true(payload["generated_residual_closure_complete"] == 1, payload)
        assert_true(payload["blocking_open_rows"] == 0, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["operator_facing_change_allowed_rows"] == 0, payload)
        assert_true(payload["bulk_rewrite_allowed_rows"] == 0, payload)
        assert_true(payload["final_rescan_complete"] == 1, payload)
        assert_true(
            payload["closure_claim"] == "current_blocking_gate_clear_not_zero_literal_cleanup",
            payload,
        )

        expected_lanes = {
            "p0_stale_worktree",
            "latest_handoff_generated_repro_residual",
            "evidence_manifest_generated_repro_residual",
            "generated_residual_action_required",
            "unexpected_generated_residual",
            "p1_live_temp_reference_broad_scan",
            "p2_historical_evidence_reference",
            "p2_historical_repro_reference",
        }
        assert_true(expected_lanes.issubset(set(detail["lane"])), detail.to_dict("records"))
        assert_true(
            int(summary[summary["key"].eq("final_rescan_complete")]["count"].iloc[0]) == 1,
            summary.to_dict("records"),
        )
        assert_true("does not claim that every historical path literal is gone" in note, note)
        assert_true("currently blocking stale-worktree" in note, note)

    print("smoke ok: path_portability_final_rescan_v1")


if __name__ == "__main__":
    main()
