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
        / "research/prognostics/build_latest_handoff_manifest_portability_closure_audit_v1.py"
    )
    with tempfile.TemporaryDirectory(prefix="latest_handoff_portability_closure_") as tmpdir:
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
            (output_dir / "latest_handoff_manifest_portability_closure_audit_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "latest_handoff_manifest_portability_closure_audit_v1.csv")
        summary = pd.read_csv(
            output_dir / "latest_handoff_manifest_portability_closure_audit_summary_v1.csv"
        )
        generated_detail = pd.read_csv(
            output_dir
            / "_generated_latest_handoff_manifest"
            / "panel_day_engine_latest_evidence_handoff_manifest_v1.csv"
        )
        note = (output_dir / "latest_handoff_manifest_portability_closure_audit_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["generated_manifest_detail_rows"] == 14, payload)
        assert_true(payload["parameterized_rows"] == 12, payload)
        assert_true(payload["repo_doc_rows"] == 2, payload)
        assert_true(payload["parameterized_manifestized_rows"] == 12, payload)
        assert_true(payload["repo_doc_preserved_rows"] == 2, payload)
        assert_true(payload["closure_fail_count"] == 0, payload)
        assert_true(payload["repro_private_tmp_literal_rows"] == 0, payload)
        assert_true(payload["artifact_private_tmp_literal_rows"] == 0, payload)
        assert_true(payload["input_manifest_rows"] == 12, payload)
        assert_true(payload["manifest_dir_placeholder_rows"] == 12, payload)
        assert_true(payload["output_root_repro_rows"] == 12, payload)
        assert_true(payload["output_root_artifact_rows"] == 12, payload)
        assert_true(payload["repro_required_if_missing_rows"] == 12, payload)
        assert_true(payload["primary_doc_missing_rows"] == 0, payload)
        assert_true(payload["patch_authorization_sum"] == 0, payload)
        assert_true(payload["generator_json_branch_count"] == 14, payload)
        assert_true(payload["generator_json_temp_artifact_missing_count"] == 12, payload)
        assert_true(payload["generator_json_repo_doc_missing_count"] == 0, payload)
        assert_true(payload["generated_note_private_tmp_legacy_phrase_count"] == 0, payload)
        assert_true(payload["generated_note_parameterized_phrase_count"] >= 1, payload)
        assert_true(payload["expected_temp_literal_drop_rows"] == 41, payload)
        assert_true(payload["closure_complete"] == 1, payload)

        assert_true(
            set(detail["closure_status"])
            == {"closed_parameterized_manifestized", "closed_repo_doc_preserved"},
            detail.to_dict("records"),
        )
        assert_true(
            not generated_detail["repro_command"].astype(str).str.contains("/private/tmp", regex=False).any(),
            generated_detail[["branch_id", "repro_command"]].to_string(),
        )
        assert_true(
            int(summary[summary["key"].eq("closure_complete")]["count"].iloc[0]) == 1,
            summary.to_dict("records"),
        )
        assert_true("Regenerates the latest evidence handoff manifest" in note, note)

    print("smoke ok: latest_handoff_manifest_portability_closure_audit_v1")


if __name__ == "__main__":
    main()
