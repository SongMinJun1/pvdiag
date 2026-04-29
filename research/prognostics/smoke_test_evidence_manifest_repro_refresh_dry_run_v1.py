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
    builder = repo_root / "research/prognostics/build_evidence_manifest_repro_refresh_dry_run_v1.py"
    with tempfile.TemporaryDirectory(prefix="evidence_manifest_repro_refresh_dry_run_") as tmpdir:
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
            (output_dir / "evidence_manifest_repro_refresh_dry_run_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "evidence_manifest_repro_refresh_dry_run_v1.csv")
        patch_plan = pd.read_csv(
            output_dir / "evidence_manifest_repro_refresh_source_patch_plan_v1.csv"
        )
        summary = pd.read_csv(
            output_dir / "evidence_manifest_repro_refresh_dry_run_summary_v1.csv"
        )
        note = (output_dir / "evidence_manifest_repro_refresh_dry_run_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["artifact_spec_rows"] == 23, payload)
        assert_true(payload["changed_artifact_spec_rows"] == 20, payload)
        assert_true(payload["unchanged_artifact_spec_rows"] == 3, payload)
        assert_true(payload["runtime_artifact_spec_rows"] == 14, payload)
        assert_true(payload["builder_artifact_spec_rows"] == 6, payload)
        assert_true(payload["manual_oneoff_artifact_spec_rows"] == 3, payload)
        assert_true(payload["placeholder_root_used_artifact_rows"] == 20, payload)
        assert_true(payload["unique_source_command_rows"] == 4, payload)
        assert_true(payload["source_patch_required_command_rows"] == 4, payload)
        assert_true(payload["artifact_row_old_private_tmp_literal_rows"] == 26, payload)
        assert_true(payload["artifact_row_proposed_private_tmp_literal_rows"] == 0, payload)
        assert_true(payload["unique_command_old_private_tmp_literal_rows"] == 7, payload)
        assert_true(payload["unique_command_proposed_private_tmp_literal_rows"] == 0, payload)
        assert_true(payload["manual_literal_edit_allowed_rows"] == 0, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["operator_facing_change_allowed_rows"] == 0, payload)
        assert_true(payload["dry_run_complete"] == 1, payload)

        changed = detail[detail["command_changed"].eq(1)]
        unchanged = detail[detail["command_changed"].eq(0)]
        assert_true(len(changed) == 20, detail.to_dict("records"))
        assert_true(len(unchanged) == 3, detail.to_dict("records"))
        assert_true(
            changed["proposed_repro_command"].str.contains("/private/tmp/").sum() == 0,
            changed[["source_constant", "proposed_repro_command"]].to_dict("records"),
        )
        assert_true(
            changed["proposed_repro_command"].str.contains(
                "${EVIDENCE_MANIFEST_OUTPUT_ROOT}",
                regex=False,
            ).all(),
            changed[["source_constant", "proposed_repro_command"]].to_dict("records"),
        )
        assert_true(
            set(unchanged["repro_mode"]) == {"manual_oneoff"},
            unchanged[["repro_mode", "old_repro_command"]].to_dict("records"),
        )
        assert_true(len(patch_plan) == 4, patch_plan.to_dict("records"))
        assert_true(int(patch_plan["source_patch_required"].sum()) == 4, patch_plan.to_dict("records"))
        assert_true(
            patch_plan["proposed_repro_command"].str.contains("/private/tmp/").sum() == 0,
            patch_plan[["source_constant", "proposed_repro_command"]].to_dict("records"),
        )
        assert_true(
            int(summary[summary["key"].eq("dry_run_complete")]["count"].iloc[0]) == 1,
            summary.to_dict("records"),
        )
        assert_true("Dry-runs the BR-234" in note, note)
        assert_true("evidence_manifest_repro_refresh_apply_builder" in note, note)

    print("smoke ok: evidence_manifest_repro_refresh_dry_run_v1")


if __name__ == "__main__":
    main()
