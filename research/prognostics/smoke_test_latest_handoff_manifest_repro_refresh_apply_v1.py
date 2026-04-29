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
    checker = repo_root / "research/prognostics/check_latest_handoff_manifest_repro_refresh_apply_v1.py"
    with tempfile.TemporaryDirectory(prefix="latest_handoff_repro_apply_check_") as tmpdir:
        output_dir = Path(tmpdir) / "out"
        proc = subprocess.run(
            [
                sys.executable,
                str(checker),
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
            (output_dir / "latest_handoff_manifest_repro_refresh_apply_check_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "latest_handoff_manifest_repro_refresh_apply_check_v1.csv")
        summary = pd.read_csv(
            output_dir / "latest_handoff_manifest_repro_refresh_apply_check_summary_v1.csv"
        )
        note = (output_dir / "latest_handoff_manifest_repro_refresh_apply_check_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["branch_spec_rows"] == 14, payload)
        assert_true(payload["applied_manifestized_repro_rows"] == 12, payload)
        assert_true(payload["repo_doc_preserved_rows"] == 2, payload)
        assert_true(payload["manual_review_rows"] == 0, payload)
        assert_true(payload["repro_private_tmp_literal_rows"] == 0, payload)
        assert_true(payload["artifact_private_tmp_literal_rows"] == 0, payload)
        assert_true(payload["br230_old_repro_temp_literal_rows"] == 41, payload)
        assert_true(payload["applied_repro_temp_literal_drop_rows"] == 41, payload)
        assert_true(payload["input_manifest_command_rows"] == 12, payload)
        assert_true(payload["manifest_dir_placeholder_rows"] == 12, payload)
        assert_true(payload["output_root_placeholder_rows"] == 12, payload)
        assert_true(payload["repo_root_pwd_rows"] == 1, payload)
        assert_true(payload["parameterized_artifact_rows"] == 12, payload)
        assert_true(payload["repo_artifact_rows"] == 2, payload)
        assert_true(payload["operator_promotion_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["br230_expectation_match"] == 1, payload)
        assert_true(payload["apply_check_complete"] == 1, payload)

        assert_true(
            set(detail["row_status"]) == {"applied_manifestized_repro", "repo_doc_preserved"},
            detail.to_dict("records"),
        )
        assert_true(
            int(summary[summary["key"].eq("apply_check_complete")]["count"].iloc[0]) == 1,
            summary.to_dict("records"),
        )
        assert_true("Checks that the latest handoff generator now emits portable repro text" in note, note)

    print("smoke ok: latest_handoff_manifest_repro_refresh_apply_v1")


if __name__ == "__main__":
    main()
