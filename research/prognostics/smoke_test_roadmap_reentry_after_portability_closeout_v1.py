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
    builder = repo_root / "research/prognostics/build_roadmap_reentry_after_portability_closeout_v1.py"
    with tempfile.TemporaryDirectory(prefix="roadmap_reentry_after_portability_closeout_") as tmpdir:
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
            (output_dir / "roadmap_reentry_after_portability_closeout_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "roadmap_reentry_after_portability_closeout_v1.csv")
        next_actions = pd.read_csv(
            output_dir / "roadmap_reentry_after_portability_closeout_next_actions_v1.csv"
        )
        summary = pd.read_csv(
            output_dir / "roadmap_reentry_after_portability_closeout_summary_v1.csv"
        )
        note = (output_dir / "roadmap_reentry_after_portability_closeout_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["roadmap_reentry_ready"] == 1, payload)
        assert_true(payload["path_portability_axis_closeout_ready"] == 1, payload)
        assert_true(payload["final_cleanup_pr_required"] == 0, payload)
        assert_true(payload["queue_rows"] == 23, payload)
        assert_true(payload["queue_sequence_ok"] == 1, payload)
        assert_true(payload["queue_open_rows"] == 0, payload)
        assert_true(payload["br130_waiting_real_data"] == 1, payload)
        assert_true(payload["br144_waiting_prepatch"] == 1, payload)
        assert_true(payload["real_capture_required_to_continue"] == 1, payload)
        assert_true(payload["truth_intake_allowed_rows"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_rows"] == 0, payload)
        assert_true(payload["engine_patch_allowed_rows"] == 0, payload)
        assert_true(payload["operator_facing_change_allowed_rows"] == 0, payload)
        assert_true(set(detail["checkpoint_status"]) == {"pass"}, detail.to_dict("records"))
        assert_true(int(next_actions["safe_without_real_data_flag"].sum()) == 1, next_actions)
        assert_true(
            int(summary[summary["key"].eq("roadmap_reentry_ready")]["count"].iloc[0]) == 1,
            summary.to_dict("records"),
        )
        assert_true("real KTC ESS capture/label evidence" in note, note)
        assert_true("does not claim algorithm completion" in note, note)

    print("smoke ok: roadmap_reentry_after_portability_closeout_v1")


if __name__ == "__main__":
    main()
