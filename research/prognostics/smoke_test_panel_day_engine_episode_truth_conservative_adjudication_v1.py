#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


ADJUDICATION_NAME = "panel_day_engine_episode_truth_conservative_adjudication_v1.csv"
REVIEW_INPUT_NAME = "panel_day_engine_episode_truth_review_input_conservative_v1.csv"
SUMMARY_NAME = "panel_day_engine_episode_truth_conservative_adjudication_summary_v1.csv"
JSON_NAME = "panel_day_engine_episode_truth_conservative_adjudication_v1.json"


WORKSHEET_COLUMNS = [
    "owner_branch",
    "worksheet_row_id",
    "adjudication_status",
    "suggested_review_direction",
    "suggested_label_options",
    "must_not_auto_apply_label",
    "reviewed_truth_row_id",
    "review_packet_id",
    "review_priority",
    "review_track",
    "episode_truth_bucket",
    "site",
    "panel_id",
    "family_key",
    "subtype_key",
    "episode_anchor_date",
    "strict_trigger_date",
    "gap_days",
    "signal_day_count",
    "common_cause_flag_sum",
    "strict_trigger_proximal_common_cause_flag",
    "source_reference_count",
    "trace_ready_count",
    "trace_ready_all",
    "source_event_types",
    "source_final_patterns",
    "source_algorithm_families",
    "source_heuristic_top1_values",
    "source_gap_days_min",
    "source_gap_days_max",
    "source_episode_classes",
    "source_precursor_promotion_decisions",
    "source_shadow_reasons",
    "source_references",
    "evidence_card_path",
    "evidence_card_exists",
    "review_question",
    "must_prove_axes",
    "must_reject_axes",
    "candidate_reading",
    "default_review_disposition",
    "reviewer_next_action",
    "allowed_reviewer_truth_labels",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "reviewer_notes_seed",
    "threshold_replay_input_allowed",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def worksheet_row(
    root: Path,
    idx: int,
    review_track: str,
    suggested_direction: str,
    source_decision: str,
    source_class: str,
    source_gap: int,
    signal_day_count: int,
) -> dict[str, object]:
    card_path = root / "cards" / f"card-{idx}.md"
    card_path.parent.mkdir(exist_ok=True)
    card_path.write_text(f"# card {idx}\n", encoding="utf-8")
    if review_track == "long_gap_backdating_review":
        site = "ktc_ess"
        panel = "panel-long"
    elif review_track == "strict_sudden_prior_episode_review":
        site = "gangui"
        panel = "panel-strict"
    else:
        site = "conalog"
        panel = "panel-durable"
    return {
        "owner_branch": "BR-20260425-087",
        "worksheet_row_id": f"BR087-ADJ-{idx:03d}",
        "adjudication_status": "ready_for_human_adjudication",
        "suggested_review_direction": suggested_direction,
        "suggested_label_options": "fixture options",
        "must_not_auto_apply_label": 1,
        "reviewed_truth_row_id": f"BR084-RTR-{idx:03d}",
        "review_packet_id": f"BR082-EPR-{idx:03d}",
        "review_priority": "P0",
        "review_track": review_track,
        "episode_truth_bucket": f"{review_track}_bucket",
        "site": site,
        "panel_id": panel,
        "family_key": "fixture_family",
        "subtype_key": "fixture_subtype",
        "episode_anchor_date": "2025-01-01",
        "strict_trigger_date": "2025-01-01",
        "gap_days": source_gap,
        "signal_day_count": signal_day_count,
        "common_cause_flag_sum": 0,
        "strict_trigger_proximal_common_cause_flag": 0,
        "source_reference_count": 1,
        "trace_ready_count": 1,
        "trace_ready_all": 1,
        "source_event_types": "fixture event",
        "source_final_patterns": "fixture pattern",
        "source_algorithm_families": "fixture family",
        "source_heuristic_top1_values": "fixture heuristic",
        "source_gap_days_min": source_gap,
        "source_gap_days_max": source_gap,
        "source_episode_classes": source_class,
        "source_precursor_promotion_decisions": source_decision,
        "source_shadow_reasons": "fixture reason",
        "source_references": f"fixture:{idx}",
        "evidence_card_path": str(card_path),
        "evidence_card_exists": 1,
        "review_question": "fixture question",
        "must_prove_axes": "fixture prove axes",
        "must_reject_axes": "fixture reject axes",
        "candidate_reading": "fixture candidate",
        "default_review_disposition": "fixture disposition",
        "reviewer_next_action": "fixture next action",
        "allowed_reviewer_truth_labels": (
            "real_precursor; episode_only_or_backdating; strict_sudden_no_precursor; "
            "common_cause_or_measurement_hold; insufficient_evidence_hold"
        ),
        "reviewer_truth_label": "",
        "reviewer_evidence_path": "",
        "reviewer_notes_seed": "",
        "threshold_replay_input_allowed": 0,
        "operator_facing_change_allowed": 0,
        "engine_patch_allowed": 0,
        "threshold_patch_allowed": 0,
        "notes": "",
    }


def write_fixture(root: Path) -> Path:
    worksheet_path = root / "worksheet.csv"
    rows = [
        worksheet_row(
            root,
            1,
            "long_gap_backdating_review",
            "negative_or_hold_candidate",
            "block_precursor_backdating",
            "long_gap_one_day_episode_hold",
            270,
            3,
        ),
        worksheet_row(
            root,
            2,
            "strict_sudden_prior_episode_review",
            "strict_sudden_negative_candidate",
            "no_precursor_promotion",
            "sudden_fault_strict_anchor",
            0,
            0,
        ),
        worksheet_row(
            root,
            3,
            "durable_precursor_review",
            "manual_positive_or_hold_candidate",
            "manual_review_candidate",
            "intermittent_precursor_candidate",
            49,
            2,
        ),
    ]
    pd.DataFrame(rows).reindex(columns=WORKSHEET_COLUMNS).to_csv(worksheet_path, index=False, encoding="utf-8-sig")
    return worksheet_path


def run_builder(repo_root: Path, worksheet_path: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
    return run(
        [
            sys.executable,
            "research/prognostics/build_panel_day_engine_episode_truth_conservative_adjudication_v1.py",
            "--repo-root",
            str(repo_root),
            "--worksheet-input",
            str(worksheet_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=repo_root,
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        worksheet_path = write_fixture(root)
        out_dir = root / "out"
        proc = run_builder(repo_root, worksheet_path, out_dir)
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)

        adjudication = pd.read_csv(out_dir / ADJUDICATION_NAME, encoding="utf-8-sig")
        review_input = pd.read_csv(out_dir / REVIEW_INPUT_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(out_dir / SUMMARY_NAME, encoding="utf-8-sig")
        payload = json.loads((out_dir / JSON_NAME).read_text(encoding="utf-8"))

        assert_true(len(adjudication) == 3, f"expected 3 adjudication rows, got {len(adjudication)}")
        assert_true(len(review_input) == 3, f"expected 3 review input rows, got {len(review_input)}")
        labels = set(review_input["reviewer_truth_label"].fillna(""))
        assert_true("episode_only_or_backdating" in labels, "missing long-gap negative label")
        assert_true("strict_sudden_no_precursor" in labels, "missing strict-sudden negative label")
        assert_true("" in labels, "durable row should stay unfilled")
        assert_true(int(adjudication["negative_replay_candidate"].sum()) == 2, "expected 2 negative rows")
        assert_true(int(adjudication["positive_replay_candidate"].sum()) == 0, "must not create positives")
        assert_true(int(adjudication["threshold_replay_input_allowed_candidate"].sum()) == 2, "expected 2 replay candidate rows")
        assert_true(int(summary["filled_positive_rows"].sum()) == 0, "summary must report zero positives")
        assert_true(payload["filled_negative_rows"] == 2, "json negative count mismatch")
        assert_true(payload["filled_positive_rows"] == 0, "json should not create positives")
        assert_true(payload["deferred_rows"] == 1, "json deferred count mismatch")

        unsafe = pd.read_csv(worksheet_path, encoding="utf-8-sig")
        unsafe["engine_patch_allowed"] = 0
        unsafe.loc[0, "engine_patch_allowed"] = 1
        unsafe_path = root / "unsafe_engine.csv"
        unsafe.to_csv(unsafe_path, index=False, encoding="utf-8-sig")
        unsafe_proc = run_builder(repo_root, unsafe_path, root / "unsafe_out")
        assert_true(unsafe_proc.returncode != 0, "engine patch authorization should fail")

    print("smoke ok: panel_day_engine_episode_truth_conservative_adjudication_v1")


if __name__ == "__main__":
    main()
