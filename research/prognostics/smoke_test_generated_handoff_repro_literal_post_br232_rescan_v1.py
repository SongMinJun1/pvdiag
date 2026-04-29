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
    builder = (
        repo_root
        / "research/prognostics/build_generated_handoff_repro_literal_post_br232_rescan_v1.py"
    )
    with tempfile.TemporaryDirectory(prefix="generated_handoff_post_br232_rescan_") as tmpdir:
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
            (output_dir / "generated_handoff_repro_literal_post_br232_rescan_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "generated_handoff_repro_literal_post_br232_rescan_v1.csv")
        summary = pd.read_csv(
            output_dir / "generated_handoff_repro_literal_post_br232_rescan_summary_v1.csv"
        )
        note = (output_dir / "generated_handoff_repro_literal_post_br232_rescan_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["post_br232_generated_handoff_repro_literal_rows"] == 2, payload)
        assert_true(payload["latest_handoff_manifest_repro_rows"] == 0, payload)
        assert_true(payload["evidence_manifest_repro_rows"] == 0, payload)
        assert_true(payload["episode_note_repro_rows"] == 1, payload)
        assert_true(payload["validation_output_literal_rows"] == 1, payload)
        assert_true(payload["manifestized_rebuild_candidate_rows"] == 0, payload)
        assert_true(payload["intentional_validation_output_literal_rows"] == 1, payload)
        assert_true(payload["manual_literal_edit_allowed_rows"] == 0, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["operator_facing_change_allowed_rows"] == 0, payload)
        assert_true(payload["br228_generated_literal_rows"] == 50, payload)
        assert_true(payload["br228_latest_handoff_rows"] == 41, payload)
        assert_true(payload["generated_literal_drop_since_br228"] == 48, payload)
        assert_true(payload["latest_handoff_drop_since_br228"] == 41, payload)
        assert_true(payload["latest_handoff_closed_after_br232"] == 1, payload)
        assert_true(payload["evidence_manifest_closed_after_br236"] == 1, payload)
        assert_true(payload["residual_rescan_complete"] == 1, payload)

        assert_true(
            set(detail["post_br232_residual_lane"])
            == {
                "episode_note_repro_deferred",
                "validation_output_destination_preserved",
            },
            detail.to_dict("records"),
        )
        assert_true(
            int(summary[summary["key"].eq("residual_rescan_complete")]["count"].iloc[0]) == 1,
            summary.to_dict("records"),
        )
        assert_true("latest handoff lane is closed" in note, note)

    print("smoke ok: generated_handoff_repro_literal_post_br232_rescan_v1")


if __name__ == "__main__":
    main()
