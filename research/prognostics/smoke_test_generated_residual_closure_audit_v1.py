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
    builder = repo_root / "research/prognostics/build_generated_residual_closure_audit_v1.py"
    with tempfile.TemporaryDirectory(prefix="generated_residual_closure_audit_") as tmpdir:
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
            (output_dir / "generated_residual_closure_audit_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "generated_residual_closure_audit_v1.csv")
        summary = pd.read_csv(output_dir / "generated_residual_closure_audit_summary_v1.csv")
        note = (output_dir / "generated_residual_closure_audit_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["generated_residual_rows"] == 2, payload)
        assert_true(payload["latest_handoff_residual_rows"] == 0, payload)
        assert_true(payload["evidence_manifest_residual_rows"] == 0, payload)
        assert_true(payload["episode_note_deferred_rows"] == 1, payload)
        assert_true(payload["validation_output_preserved_rows"] == 1, payload)
        assert_true(payload["current_action_required_rows"] == 0, payload)
        assert_true(payload["safe_to_leave_in_place_rows"] == 2, payload)
        assert_true(payload["deferred_until_touched_rows"] == 1, payload)
        assert_true(payload["intentional_output_destination_rows"] == 1, payload)
        assert_true(payload["unexpected_generated_residual_rows"] == 0, payload)
        assert_true(payload["manual_literal_edit_allowed_rows"] == 0, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["operator_facing_change_allowed_rows"] == 0, payload)
        assert_true(payload["generated_residual_closure_complete"] == 1, payload)

        assert_true(
            set(detail["closure_bucket"])
            == {
                "deferred_note_repro_only",
                "intentional_validation_output_destination",
            },
            detail.to_dict("records"),
        )
        assert_true(
            int(summary[summary["key"].eq("generated_residual_closure_complete")]["count"].iloc[0])
            == 1,
            summary.to_dict("records"),
        )
        assert_true("validation output literal is preserved" in note, note)
        assert_true("episode note repro row is deferred" in note, note)

    print("smoke ok: generated_residual_closure_audit_v1")


if __name__ == "__main__":
    main()
