#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


ROWS_NAME = "panel_day_engine_reviewed_episode_truth_rows_v1.csv"
SUMMARY_NAME = "panel_day_engine_reviewed_episode_truth_rows_summary_v1.csv"
ACTION_NAME = "panel_day_engine_reviewed_episode_truth_rows_action_queue_v1.csv"
NOTE_NAME = "panel_day_engine_reviewed_episode_truth_rows_note_v1.md"
JSON_NAME = "panel_day_engine_reviewed_episode_truth_rows_v1.json"


PACKET_COLUMNS = [
    "owner_branch",
    "review_packet_id",
    "review_priority",
    "review_track",
    "episode_truth_bucket",
    "site",
    "panel_id",
    "family_key",
    "family_label_ko",
    "subtype_key",
    "subtype_label_ko",
    "episode_anchor_date",
    "episode_anchor_kind",
    "strict_trigger_date",
    "gap_days",
    "signal_start_date",
    "signal_end_date",
    "signal_span_days",
    "signal_day_count",
    "duration_proxy_days",
    "recurrence_proxy_days",
    "warning_proxy_days",
    "common_cause_flag_sum",
    "strict_trigger_proximal_common_cause_flag",
    "source_lens_count",
    "source_artifacts",
    "source_case_ids",
    "episode_truth_case_ids",
    "candidate_reading",
    "default_review_disposition",
    "must_prove_axes",
    "must_reject_axes",
    "allowed_reviewer_truth_labels",
    "review_question",
    "recommended_next_if_positive",
    "recommended_next_if_negative",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "reviewer_notes",
    "notes",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_packet(path: Path) -> None:
    rows = []
    for idx, track in enumerate(
        ["long_gap_backdating_review", "strict_sudden_prior_episode_review", "durable_precursor_review"],
        start=1,
    ):
        rows.append(
            {
                "owner_branch": "BR-082",
                "review_packet_id": f"BR082-EPR-{idx:03d}",
                "review_priority": "P0" if idx < 3 else "P1",
                "review_track": track,
                "episode_truth_bucket": "long_gap_backdating_hold" if idx == 1 else "strict_anchor_sudden_review" if idx == 2 else "durable_precursor_candidate_review",
                "site": "site",
                "panel_id": f"panel-{idx}",
                "family_key": "family",
                "family_label_ko": "family",
                "subtype_key": "",
                "subtype_label_ko": "",
                "episode_anchor_date": "2025-01-01",
                "episode_anchor_kind": "anchor",
                "strict_trigger_date": "2025-02-01",
                "gap_days": 31,
                "signal_start_date": "2025-01-01",
                "signal_end_date": "2025-02-01",
                "signal_span_days": 31,
                "signal_day_count": 1,
                "duration_proxy_days": 1,
                "recurrence_proxy_days": 2,
                "warning_proxy_days": 0,
                "common_cause_flag_sum": 0,
                "strict_trigger_proximal_common_cause_flag": 0,
                "source_lens_count": 2 if idx == 1 else 1,
                "source_artifacts": "br017_episode_shadow; br017_g1_longgap_cases" if idx == 1 else "br017_episode_shadow",
                "source_case_ids": "case",
                "episode_truth_case_ids": "truth-case",
                "candidate_reading": "candidate",
                "default_review_disposition": "hold",
                "must_prove_axes": "prove",
                "must_reject_axes": "reject",
                "allowed_reviewer_truth_labels": "real_precursor; episode_only_or_backdating; strict_sudden_no_precursor; common_cause_or_measurement_hold; insufficient_evidence_hold",
                "review_question": "question",
                "recommended_next_if_positive": "positive next",
                "recommended_next_if_negative": "negative next",
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "reviewer_truth_label": "",
                "reviewer_evidence_path": "",
                "reviewer_notes": "",
                "notes": "",
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=PACKET_COLUMNS).to_csv(path, index=False, encoding="utf-8-sig")


def write_guard(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "fail_count": 0,
                "p0_fail_count": 0,
                "operator_facing_change_allowed_sum": 0,
                "engine_patch_allowed_sum": 0,
                "threshold_patch_allowed_sum": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_review_input(path: Path) -> None:
    pd.DataFrame(
        [
            {
                "review_packet_id": "BR082-EPR-001",
                "reviewer_truth_label": "real_precursor",
                "reviewer_evidence_path": "/evidence/panel-1.md",
                "reviewer_notes": "positive evidence",
            },
            {
                "review_packet_id": "BR082-EPR-002",
                "reviewer_truth_label": "strict_sudden_no_precursor",
                "reviewer_evidence_path": "/evidence/panel-2.md",
                "reviewer_notes": "negative evidence",
            },
            {
                "review_packet_id": "BR082-EPR-003",
                "reviewer_truth_label": "insufficient_evidence_hold",
                "reviewer_evidence_path": "/evidence/panel-3.md",
                "reviewer_notes": "hold",
            },
        ]
    ).to_csv(path, index=False, encoding="utf-8-sig")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research/prognostics/build_panel_day_engine_reviewed_episode_truth_rows_v1.py"
    with tempfile.TemporaryDirectory(prefix="reviewed_episode_truth_rows_smoke_") as tmpdir:
        root = Path(tmpdir)
        packet = root / "packet.csv"
        guard = root / "guard.json"
        write_packet(packet)
        write_guard(guard)

        # Default run: no reviewer labels, therefore no replay-ready rows.
        default_out = root / "default_out"
        completed = run(
            [
                sys.executable,
                str(script),
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(default_out),
                "--owner-branch",
                "BR-TEST-084",
                "--packet-input",
                str(packet),
                "--guard-json-input",
                str(guard),
            ],
            repo_root,
        )
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)
        rows = pd.read_csv(default_out / ROWS_NAME, encoding="utf-8-sig")
        payload = json.loads((default_out / JSON_NAME).read_text(encoding="utf-8"))
        assert_true(len(rows) == 3, rows.to_string())
        assert_true(set(rows["review_status"]) == {"needs_evidence"}, rows.to_string())
        assert_true(set(rows["truth_role"]) == {"unassigned"}, rows.to_string())
        assert_true(int(rows["threshold_replay_input_allowed"].sum()) == 0, rows.to_string())
        assert_true(payload["reviewer_truth_label_assigned_count"] == 0, payload)
        assert_true(payload["threshold_replay_ready_count"] == 0, payload)

        # Evidence-attached run: positive and negative labels are replay inputs, hold is not.
        review_input = root / "review_input.csv"
        write_review_input(review_input)
        reviewed_out = root / "reviewed_out"
        completed = run(
            [
                sys.executable,
                str(script),
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(reviewed_out),
                "--owner-branch",
                "BR-TEST-084",
                "--packet-input",
                str(packet),
                "--guard-json-input",
                str(guard),
                "--review-input",
                str(review_input),
            ],
            repo_root,
        )
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)
        rows = pd.read_csv(reviewed_out / ROWS_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(reviewed_out / SUMMARY_NAME, encoding="utf-8-sig")
        action = pd.read_csv(reviewed_out / ACTION_NAME, encoding="utf-8-sig")
        payload = json.loads((reviewed_out / JSON_NAME).read_text(encoding="utf-8"))
        note_text = (reviewed_out / NOTE_NAME).read_text(encoding="utf-8")

        assert_true(payload["reviewer_truth_label_assigned_count"] == 3, payload)
        assert_true(payload["threshold_replay_ready_count"] == 2, payload)
        assert_true(int(rows["operator_facing_change_allowed"].sum()) == 0, rows.to_string())
        assert_true(int(rows["engine_patch_allowed"].sum()) == 0, rows.to_string())
        assert_true(int(rows["threshold_patch_allowed"].sum()) == 0, rows.to_string())
        assert_true(set(rows["review_status"]) == {"reviewed_positive", "reviewed_negative", "reviewed_hold"}, rows.to_string())
        assert_true(set(rows["truth_role"]) == {"positive_precursor_truth", "negative_counterexample", "hold_or_insufficient_evidence"}, rows.to_string())
        assert_true(len(summary) == 3, summary.to_string())
        assert_true(action["sequence"].tolist() == sorted(action["sequence"].tolist()), action.to_string())
        assert_true(action.iloc[0]["action_id"] == "ACT-001", action.to_string())
        assert_true("BR-076" in note_text, note_text)

    print("smoke_test_panel_day_engine_reviewed_episode_truth_rows_v1.py: PASS")


if __name__ == "__main__":
    main()
