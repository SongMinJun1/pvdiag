#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


SUMMARY_NAME = "panel_day_engine_result_delta_scorecard_compare_summary_v1.csv"
DETAIL_NAME = "panel_day_engine_result_delta_scorecard_compare_v1.csv"
NOTE_NAME = "panel_day_engine_result_delta_scorecard_compare_note_v1.md"


def write_summary(path: Path, **overrides: object) -> None:
    row = {
        "overall_status": "pass",
        "core_compared_site_count": 1,
        "core_matched_site_count": 1,
        "core_all_compared_sites_match": 1,
        "core_total_diff_count": 0,
        "raw_only_candidate_row_count": 72,
        "published_current_row_count": 72,
        "precursor_candidate_row_count": 0,
        "raw_only_fault_signal_row_count": 72,
        "fault_panel_count": 72,
        "unresolved_panel_count": 277,
        "proximal_common_cause_fault_signal_count": 64,
        "proximal_common_cause_fault_signal_ratio": 0.888889,
        "fixed_reference_row_count": 6,
        "fixed_reference_matched_row_key_count": 2,
        "fixed_reference_overlap_decision_columns_match": 0,
        "prepatch_runbook_status": "pass",
        "performance_improvement_claim_allowed": "no_truth_label_not_claimed",
        "result_change_claim_ko": "core_result_delta_0",
        "next_required_action": "fixture",
    }
    row.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([row]).to_csv(path, index=False, encoding="utf-8-sig")


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_input_manifest(path: Path, baseline: Path, post: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "inputs": {
                    "baseline_scorecard_summary": str(baseline),
                    "post_scorecard_summary": str(post),
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "compare_panel_day_engine_result_delta_scorecards_v1.py"
    with tempfile.TemporaryDirectory(prefix="result_delta_scorecard_compare_") as tmp_dir:
        root = Path(tmp_dir)
        baseline = root / "baseline.csv"
        post_same = root / "post_same.csv"
        post_changed = root / "post_changed.csv"
        write_summary(baseline)
        write_summary(post_same)
        write_summary(post_changed, raw_only_candidate_row_count=73, fault_panel_count=73)
        neutral_manifest = root / "neutral_manifest.json"
        changed_manifest = root / "changed_manifest.json"
        write_input_manifest(neutral_manifest, baseline, post_same)
        write_input_manifest(changed_manifest, baseline, post_changed)

        neutral_out = root / "neutral_out"
        neutral = run(
            [
                sys.executable,
                str(script),
                "--input-manifest",
                str(neutral_manifest),
                "--output-dir",
                str(neutral_out),
            ],
            repo_root,
        )
        assert_true(neutral.returncode == 0, neutral.stderr or neutral.stdout)
        neutral_summary = pd.read_csv(neutral_out / SUMMARY_NAME, encoding="utf-8-sig")
        neutral_detail = pd.read_csv(neutral_out / DETAIL_NAME, encoding="utf-8-sig")
        neutral_note = (neutral_out / NOTE_NAME).read_text(encoding="utf-8")
        assert_true(neutral_summary.iloc[0]["overall_status"] == "pass", neutral_summary.to_string())
        assert_true(int(neutral_summary.iloc[0]["changed_metric_count"]) == 0, neutral_summary.to_string())
        assert_true(int(neutral_detail["changed_flag"].sum()) == 0, neutral_detail.to_string())
        assert_true("none" in neutral_note, neutral_note)
        assert_true("`baseline_scorecard_summary`: `input_manifest`" in neutral_note, neutral_note)
        assert_true("`post_scorecard_summary`: `input_manifest`" in neutral_note, neutral_note)

        changed_out = root / "changed_out"
        changed = run(
            [
                sys.executable,
                str(script),
                "--input-manifest",
                str(changed_manifest),
                "--output-dir",
                str(changed_out),
            ],
            repo_root,
        )
        assert_true(changed.returncode == 0, changed.stderr or changed.stdout)
        changed_summary = pd.read_csv(changed_out / SUMMARY_NAME, encoding="utf-8-sig")
        assert_true(changed_summary.iloc[0]["overall_status"] == "review", changed_summary.to_string())
        assert_true(
            int(changed_summary.iloc[0]["raw_only_candidate_row_count_delta"]) == 1,
            changed_summary.to_string(),
        )
        assert_true(
            changed_summary.iloc[0]["result_change_summary_ko"]
            == "candidate_context_change_detected_review_required",
            changed_summary.to_string(),
        )


if __name__ == "__main__":
    main()
