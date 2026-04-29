#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_episode_truth_manifest_resolution_closure_v1.csv"
SUMMARY_NAME = "panel_day_engine_episode_truth_manifest_resolution_closure_summary_v1.csv"
NOTE_NAME = "panel_day_engine_episode_truth_manifest_resolution_closure_note_v1.md"
JSON_NAME = "panel_day_engine_episode_truth_manifest_resolution_closure_v1.json"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research/prognostics/build_panel_day_engine_episode_truth_manifest_resolution_closure_v1.py"
    with tempfile.TemporaryDirectory(prefix="episode_truth_manifest_resolution_closure_smoke_") as tmpdir:
        output_dir = Path(tmpdir) / "out"
        completed = run(
            [
                sys.executable,
                str(script),
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(output_dir),
            ],
            repo_root,
        )
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)

        detail = pd.read_csv(output_dir / DETAIL_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(output_dir / SUMMARY_NAME, encoding="utf-8-sig")
        note = (output_dir / NOTE_NAME).read_text(encoding="utf-8")
        payload = json.loads((output_dir / JSON_NAME).read_text(encoding="utf-8"))

        assert_true(payload["expected_consumer_count"] == 8, payload)
        assert_true(payload["expected_manifest_key_count"] == 12, payload)
        assert_true(payload["closure_fail_count"] == 0, payload)
        assert_true(payload["missing_check_count"] == 0, payload)
        assert_true(payload["unresolved_manifest_consumer_count"] == 0, payload)
        assert_true(payload["operator_facing_change_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["closure_complete"] == 1, payload)

        summary_row = summary.iloc[0].to_dict()
        assert_true(int(summary_row["expected_consumer_count"]) == 8, summary_row)
        assert_true(int(summary_row["expected_manifest_key_count"]) == 12, summary_row)
        assert_true(int(summary_row["closure_pass_count"]) == 8, summary_row)
        assert_true(int(summary_row["closure_fail_count"]) == 0, summary_row)
        assert_true(int(summary_row["closure_complete"]) == 1, summary_row)

        assert_true(len(detail) == 8, detail.to_string())
        assert_true(detail["closure_status"].eq("closed").all(), detail.to_string())
        assert_true(int(detail["operator_facing_change_allowed"].sum()) == 0, detail.to_string())
        assert_true(int(detail["engine_patch_allowed"].sum()) == 0, detail.to_string())
        assert_true(int(detail["threshold_patch_allowed"].sum()) == 0, detail.to_string())
        assert_true(detail["missing_checks"].fillna("").eq("").all(), detail.to_string())

        assert_true("BR-170" in note, note)
        assert_true("no runtime" in note.lower(), note)
        assert_true(
            payload["recommended_next_branch"] == "br170_manifest_resolution_complete_proceed_to_next_cleanup_lane",
            payload,
        )

    print("smoke ok: panel_day_engine_episode_truth_manifest_resolution_closure_v1")


if __name__ == "__main__":
    main()
