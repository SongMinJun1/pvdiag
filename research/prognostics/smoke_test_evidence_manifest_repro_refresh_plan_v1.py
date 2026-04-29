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
    builder = repo_root / "research/prognostics/build_evidence_manifest_repro_refresh_plan_v1.py"
    with tempfile.TemporaryDirectory(prefix="evidence_manifest_repro_refresh_plan_") as tmpdir:
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
            (output_dir / "evidence_manifest_repro_refresh_plan_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "evidence_manifest_repro_refresh_plan_v1.csv")
        summary = pd.read_csv(
            output_dir / "evidence_manifest_repro_refresh_plan_summary_v1.csv"
        )
        note = (output_dir / "evidence_manifest_repro_refresh_plan_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["plan_literal_rows"] == 7, payload)
        assert_true(payload["command_group_rows"] == 4, payload)
        assert_true(payload["artifact_specs_rows"] == 23, payload)
        assert_true(payload["runtime_artifact_specs_rows"] == 14, payload)
        assert_true(payload["builder_artifact_specs_rows"] == 6, payload)
        assert_true(payload["manual_oneoff_artifact_specs_rows"] == 3, payload)
        assert_true(payload["manual_oneoff_command_rows_preserved"] == 2, payload)
        assert_true(payload["old_private_tmp_literal_rows"] == 0, payload)
        assert_true(payload["proposed_private_tmp_literal_rows"] == 0, payload)
        assert_true(payload["runtime_output_root_literal_rows"] == 1, payload)
        assert_true(payload["sidecar_result_root_literal_rows"] == 3, payload)
        assert_true(payload["sidecar_output_dir_literal_rows"] == 3, payload)
        assert_true(payload["pending_replacement_literal_rows"] == 0, payload)
        assert_true(payload["already_applied_literal_rows"] == 7, payload)
        assert_true(payload["manual_literal_edit_allowed_rows"] == 0, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["operator_facing_change_allowed_rows"] == 0, payload)
        assert_true(payload["plan_complete"] == 1, payload)
        assert_true(payload["closure_complete"] == 1, payload)

        assert_true(set(detail["source_constant"]) == {
            "RUNTIME_REPRO_COMMAND",
            "REPORT_ENTRY_REPRO_COMMAND",
            "RECOVERY_REPRO_COMMAND",
            "COMMON_CAUSE_REPRO_COMMAND",
        }, detail.to_dict("records"))
        assert_true(set(detail["literal_role"]) == {
            "runtime_output_root",
            "sidecar_result_root",
            "sidecar_output_dir",
        }, detail.to_dict("records"))
        assert_true(
            detail["proposed_repro_command"].str.contains("/private/tmp/").sum() == 0,
            detail[["source_constant", "proposed_repro_command"]].to_dict("records"),
        )
        assert_true(
            set(detail["literal_apply_status"]) == {"already_applied"},
            detail[["source_constant", "literal_apply_status"]].to_dict("records"),
        )
        assert_true(
            detail["proposed_repro_command"].str.contains("${EVIDENCE_MANIFEST_OUTPUT_ROOT}", regex=False).all(),
            detail[["source_constant", "proposed_repro_command"]].to_dict("records"),
        )
        assert_true(
            int(summary[summary["key"].eq("plan_complete")]["count"].iloc[0]) == 1,
            summary.to_dict("records"),
        )
        assert_true("plan-only" in note, note)
        assert_true("evidence_manifest_repro_refresh_dry_run" in note, note)

    print("smoke ok: evidence_manifest_repro_refresh_plan_v1")


if __name__ == "__main__":
    main()
