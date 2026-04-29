#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_latest_evidence_handoff_manifest_v1.csv"
SUMMARY_NAME = "panel_day_engine_latest_evidence_handoff_manifest_summary_v1.csv"
NOTE_NAME = "panel_day_engine_latest_evidence_handoff_manifest_note_v1.md"
JSON_NAME = "panel_day_engine_latest_evidence_handoff_manifest_v1.json"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research/prognostics/build_panel_day_engine_latest_evidence_handoff_manifest_v1.py"
    with tempfile.TemporaryDirectory(prefix="latest_evidence_handoff_manifest_smoke_") as tmpdir:
        output_dir = Path(tmpdir) / "out"
        cmd = [
            sys.executable,
            str(script),
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--owner-branch",
            "codex/test-latest-handoff",
        ]
        completed = run(cmd, repo_root)
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)

        detail_df = pd.read_csv(output_dir / DETAIL_NAME, encoding="utf-8-sig")
        summary_df = pd.read_csv(output_dir / SUMMARY_NAME, encoding="utf-8-sig")
        payload = json.loads((output_dir / JSON_NAME).read_text(encoding="utf-8"))
        note_text = (output_dir / NOTE_NAME).read_text(encoding="utf-8")

        expected_branches = {f"BR-20260424-{idx:03d}" for idx in range(64, 78)}
        actual_branches = set(detail_df["branch_id"].astype(str))
        assert_true(actual_branches == expected_branches, f"branch coverage mismatch: {sorted(actual_branches)}")

        required_cols = {
            "owner_branch",
            "branch_id",
            "evidence_layer",
            "handoff_state",
            "primary_doc_exists",
            "primary_artifact_exists",
            "artifact_location_type",
            "repro_command",
            "repro_required_if_missing",
            "engine_patch_allowed",
            "threshold_patch_allowed",
        }
        assert_true(required_cols.issubset(detail_df.columns), f"missing columns: {required_cols - set(detail_df.columns)}")
        assert_true((detail_df["owner_branch"] == "codex/test-latest-handoff").all(), detail_df.to_string())
        assert_true(int(detail_df["primary_doc_exists"].sum()) == len(expected_branches), detail_df.to_string())
        assert_true(int(detail_df["engine_patch_allowed"].sum()) == 0, "engine patch must stay disallowed")
        assert_true(int(detail_df["threshold_patch_allowed"].sum()) == 0, "threshold patch must stay disallowed")
        assert_true(int(detail_df["operator_promotion_allowed"].sum()) == 0, "operator promotion must stay disallowed")
        assert_true(
            not detail_df["repro_command"].astype(str).str.contains("/private/tmp", regex=False).any(),
            detail_df[["branch_id", "repro_command"]].to_string(),
        )
        assert_true(
            int(detail_df["repro_command"].astype(str).str.contains("--input-manifest", regex=False).sum()) == 12,
            detail_df[["branch_id", "repro_command"]].to_string(),
        )
        assert_true(
            int(detail_df["primary_artifact_path"].astype(str).str.contains("LATEST_HANDOFF_OUTPUT_ROOT", regex=False).sum()) == 12,
            detail_df[["branch_id", "primary_artifact_path"]].to_string(),
        )

        br076 = detail_df.loc[detail_df["branch_id"].eq("BR-20260424-076")].iloc[0]
        assert_true(br076["handoff_state"] == "required_before_algorithm_review", br076.to_string())
        assert_true("3-gate" in br076["next_action"], br076.to_string())

        br077 = detail_df.loc[detail_df["branch_id"].eq("BR-20260424-077")].iloc[0]
        assert_true(br077["artifact_location_type"] == "repo", br077.to_string())
        assert_true(int(br077["primary_artifact_exists"]) == 1, br077.to_string())

        assert_true("prepatch_safety_gate" in set(summary_df["evidence_layer"]), summary_df.to_string())
        assert_true(payload["branch_count"] == len(expected_branches), payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)
        assert_true("Missing parameterized/temp artifacts are not failures" in note_text, note_text)

    print("smoke_test_panel_day_engine_latest_evidence_handoff_manifest_v1.py: PASS")


if __name__ == "__main__":
    main()
