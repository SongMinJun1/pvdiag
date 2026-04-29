#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


DETAIL_NAME = "mlpe_field_trial_user_filled_manifest_resolution_closure_v1.csv"
SUMMARY_NAME = "mlpe_field_trial_user_filled_manifest_resolution_closure_summary_v1.csv"
NOTE_NAME = "mlpe_field_trial_user_filled_manifest_resolution_closure_note_v1.md"
JSON_NAME = "mlpe_field_trial_user_filled_manifest_resolution_closure_v1.json"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research/prognostics/build_mlpe_field_trial_user_filled_manifest_resolution_closure_v1.py"
    with tempfile.TemporaryDirectory(prefix="mlpe_user_filled_manifest_closure_smoke_") as tmpdir:
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

        detail = read_csv(output_dir / DETAIL_NAME)
        summary_rows = read_csv(output_dir / SUMMARY_NAME)
        note = (output_dir / NOTE_NAME).read_text(encoding="utf-8")
        payload = json.loads((output_dir / JSON_NAME).read_text(encoding="utf-8"))

        assert_true(len(detail) == 7, detail)
        assert_true(len(summary_rows) == 1, summary_rows)
        summary = summary_rows[0]

        assert_true(payload["expected_consumer_count"] == 7, payload)
        assert_true(payload["manifest_binding_count"] == 7, payload)
        assert_true(payload["distinct_manifest_key_count"] == 4, payload)
        assert_true(payload["closure_pass_count"] == 7, payload)
        assert_true(payload["closure_fail_count"] == 0, payload)
        assert_true(payload["unresolved_manifest_consumer_count"] == 0, payload)
        assert_true(payload["missing_check_count"] == 0, payload)
        assert_true(payload["operator_facing_change_allowed_sum"] == 0, payload)
        assert_true(payload["truth_write_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)
        assert_true(payload["closure_complete"] == 1, payload)

        assert_true(int(summary["expected_consumer_count"]) == 7, summary)
        assert_true(int(summary["closure_pass_count"]) == 7, summary)
        assert_true(int(summary["closure_fail_count"]) == 0, summary)
        assert_true(int(summary["closure_complete"]) == 1, summary)

        expected_keys = {"returned_capture", "label_input", "reviewed_checklist", "decision_input"}
        assert_true({row["manifest_key"] for row in detail} == expected_keys, detail)
        assert_true(all(row["closure_status"] == "closed" for row in detail), detail)
        assert_true(all(row["missing_checks"] == "" for row in detail), detail)
        assert_true(sum(int(row["operator_facing_change_allowed"]) for row in detail) == 0, detail)
        assert_true(sum(int(row["truth_write_allowed"]) for row in detail) == 0, detail)
        assert_true(sum(int(row["threshold_patch_allowed"]) for row in detail) == 0, detail)
        assert_true(sum(int(row["engine_patch_allowed"]) for row in detail) == 0, detail)

        assert_true("BR-202..BR-208" in note, note)
        assert_true("no runtime, truth, threshold, engine" in note, note)
        assert_true(
            payload["recommended_next_branch"] == "mlpe_user_filled_manifest_resolution_closed_continue_next_cleanup_lane",
            payload,
        )

    print("smoke ok: mlpe_field_trial_user_filled_manifest_resolution_closure_v1")


if __name__ == "__main__":
    main()
