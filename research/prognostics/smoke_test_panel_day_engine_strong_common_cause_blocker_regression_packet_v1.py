#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_strong_common_cause_blocker_regression_packet_v1.csv"
SUMMARY_NAME = "panel_day_engine_strong_common_cause_blocker_regression_summary_v1.csv"
NOTE_NAME = "panel_day_engine_strong_common_cause_blocker_regression_note_v1.md"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def row(
    candidate_case_id: str,
    panel_id: str,
    judgment_bucket: str,
    review_focus_bucket: str,
    synchrony_bucket: str,
    group_off: int,
    site_event: int,
) -> str:
    values = [
        candidate_case_id,
        "site_a",
        panel_id,
        judgment_bucket,
        "외부계통·공통원인 계열",
        "external_common_cause",
        2,
        1,
        0,
        1,
        1,
        review_focus_bucket,
        "rawonly_date_displaced",
        1,
        1,
        site_event,
        "transient_recovery",
        0,
        0,
        synchrony_bucket,
        max(group_off, site_event, 1),
        site_event,
        group_off,
        0,
        0.25,
        0,
        0,
        "spatiality_blocks_panel_local_promotion",
    ]
    return ",".join(str(value) for value in values)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = (
        repo_root
        / "research"
        / "prognostics"
        / "build_panel_day_engine_strong_common_cause_blocker_regression_packet_v1.py"
    )
    with tempfile.TemporaryDirectory(prefix="strong_common_cause_blocker_") as tmp_dir:
        root = Path(tmp_dir)
        input_csv = root / "judgment.csv"
        input_manifest = root / "input_manifest.json"
        out_dir = root / "out"
        header = [
            "candidate_case_id",
            "site",
            "panel_id",
            "judgment_bucket",
            "candidate_family_label_ko",
            "candidate_family_track",
            "axis_presence_count",
            "duration_gap_axis_flag",
            "continuity_recurrence_axis_flag",
            "spatiality_common_cause_axis_flag",
            "candidate_evidence_axis_count",
            "review_focus_bucket",
            "friction_blocker_types",
            "friction_direct_row_count",
            "friction_group_off_row_count",
            "friction_site_event_row_count",
            "recovery_bucket",
            "re_drop_row_count",
            "recovered_sustained_row_count",
            "synchrony_bucket",
            "common_cause_row_count",
            "site_event_row_count",
            "group_off_row_count",
            "subgroup_common_cause_row_count",
            "max_co_drop_frac",
            "operator_promotion_allowed_flag",
            "engine_patch_candidate_flag",
            "threshold_candidate_role",
        ]
        lines = [
            ",".join(header),
            row(
                "BR064-001",
                "panel.root.1",
                "block_individual_precursor_common_cause",
                "strong_common_cause_hold_review",
                "group_off_synchrony",
                2,
                0,
            ),
            row(
                "BR064-002",
                "panel.root.2",
                "hold_subgroup_or_breadth_context",
                "subgroup_context_hold_review",
                "subgroup_context",
                0,
                0,
            ),
            row(
                "BR064-003",
                "panel.root.3",
                "block_individual_precursor_common_cause",
                "strong_common_cause_hold_review",
                "site_event_synchrony",
                0,
                3,
            ),
        ]
        write_text(input_csv, "\n".join(lines) + "\n")
        write_text(
            input_manifest,
            json.dumps({"inputs": {"judgment_input": str(input_csv)}}, indent=2) + "\n",
        )
        result = subprocess.run(
            [
                "python3",
                str(script),
                "--input-manifest",
                str(input_manifest),
                "--output-dir",
                str(out_dir),
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
        )
        assert_true(result.returncode == 0, f"builder failed:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}")
        detail = pd.read_csv(out_dir / DETAIL_NAME, low_memory=False)
        summary = pd.read_csv(out_dir / SUMMARY_NAME, low_memory=False)
        note = (out_dir / NOTE_NAME).read_text(encoding="utf-8")
        assert_true(len(detail) == 2, f"unexpected detail rows: {len(detail)}")
        assert_true(set(detail["common_cause_blocker_type"]) == {"group_off_synchrony_blocker", "site_event_synchrony_blocker"}, detail)
        assert_true(int(detail["operator_promotion_allowed_flag"].sum()) == 0, "promotion must stay zero")
        assert_true(int(detail["engine_patch_candidate_flag"].sum()) == 0, "engine patch must stay zero")
        assert_true(int(detail["threshold_patch_allowed_flag"].sum()) == 0, "threshold patch must stay zero")
        assert_true(int(detail["panel_local_promotion_blocked_flag"].sum()) == 2, detail)
        assert_true(len(summary) == 2, f"unexpected summary rows: {len(summary)}")
        assert_true("threshold patch allowed sum: `0`" in note, "note missing threshold guardrail")
        assert_true("`judgment_input`: `input_manifest`" in note, "note missing manifest source")
    print("smoke ok: panel_day_engine_strong_common_cause_blocker_regression_packet_v1")


if __name__ == "__main__":
    main()
