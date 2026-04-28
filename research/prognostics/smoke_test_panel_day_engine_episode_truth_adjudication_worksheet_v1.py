#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


WORKSHEET_NAME = "panel_day_engine_episode_truth_adjudication_worksheet_v1.csv"
DRAFT_NAME = "panel_day_engine_episode_truth_review_input_draft_v1.csv"
SUMMARY_NAME = "panel_day_engine_episode_truth_adjudication_worksheet_summary_v1.csv"
JSON_NAME = "panel_day_engine_episode_truth_adjudication_worksheet_v1.json"


TRACE_COLUMNS = [
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
    "source_reference",
    "source_artifact",
    "source_current_event_type_ko",
    "source_current_final_pattern_ko",
    "source_algorithm_family_ko",
    "source_heuristic_top1_ko",
    "source_gap_days",
    "source_episode_class_shadow",
    "source_precursor_promotion_shadow_decision",
    "source_shadow_reason_ko",
    "evidence_card_exists",
    "template_row_exists",
    "template_blank_label",
    "template_blank_evidence_path",
    "trace_ready",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]


INDEX_COLUMNS = [
    "reviewed_truth_row_id",
    "review_packet_id",
    "evidence_card_path",
    "reviewer_truth_label",
    "reviewer_evidence_path",
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
    "source_lens_count",
    "source_artifacts",
    "source_case_ids",
    "episode_truth_case_ids",
    "candidate_reading",
    "default_review_disposition",
    "must_prove_axes",
    "must_reject_axes",
    "review_question",
    "allowed_reviewer_truth_labels",
    "reviewer_next_action",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def trace_row(
    review_packet_id: str,
    source_reference: str,
    review_track: str,
    site: str,
    panel_id: str,
    gap_days: int,
    episode_class: str,
    promotion_decision: str,
    source_event_type: str,
) -> dict[str, object]:
    return {
        "reviewed_truth_row_id": review_packet_id.replace("BR082-EPR", "BR084-RTR"),
        "review_packet_id": review_packet_id,
        "review_priority": "P0" if review_track == "long_gap_backdating_review" else "P1",
        "review_track": review_track,
        "episode_truth_bucket": f"{review_track}_bucket",
        "site": site,
        "panel_id": panel_id,
        "family_key": "fixture_family",
        "subtype_key": "fixture_subtype",
        "episode_anchor_date": "2025-01-29",
        "strict_trigger_date": "2025-10-26",
        "source_reference": source_reference,
        "source_artifact": "fixture_source",
        "source_current_event_type_ko": source_event_type,
        "source_current_final_pattern_ko": "fixture_pattern",
        "source_algorithm_family_ko": "fixture_algorithm_family",
        "source_heuristic_top1_ko": "fixture_heuristic",
        "source_gap_days": gap_days,
        "source_episode_class_shadow": episode_class,
        "source_precursor_promotion_shadow_decision": promotion_decision,
        "source_shadow_reason_ko": f"{review_track} fixture reason",
        "evidence_card_exists": 1,
        "template_row_exists": 1,
        "template_blank_label": 1,
        "template_blank_evidence_path": 1,
        "trace_ready": 1,
        "operator_facing_change_allowed": 0,
        "engine_patch_allowed": 0,
        "threshold_patch_allowed": 0,
    }


def index_row(
    root: Path,
    review_packet_id: str,
    review_track: str,
    site: str,
    panel_id: str,
    gap_days: int,
) -> dict[str, object]:
    card_path = root / "cards" / f"{review_packet_id}.md"
    card_path.parent.mkdir(exist_ok=True)
    card_path.write_text(f"# {review_packet_id}\n", encoding="utf-8")
    return {
        "reviewed_truth_row_id": review_packet_id.replace("BR082-EPR", "BR084-RTR"),
        "review_packet_id": review_packet_id,
        "evidence_card_path": str(card_path),
        "reviewer_truth_label": "",
        "reviewer_evidence_path": "",
        "review_priority": "P0" if review_track == "long_gap_backdating_review" else "P1",
        "review_track": review_track,
        "episode_truth_bucket": f"{review_track}_bucket",
        "site": site,
        "panel_id": panel_id,
        "family_key": "fixture_family",
        "subtype_key": "fixture_subtype",
        "episode_anchor_date": "2025-01-29",
        "strict_trigger_date": "2025-10-26",
        "gap_days": gap_days,
        "signal_day_count": 1,
        "common_cause_flag_sum": 0,
        "strict_trigger_proximal_common_cause_flag": 0,
        "source_lens_count": 2 if review_track == "long_gap_backdating_review" else 1,
        "source_artifacts": "fixture_source",
        "source_case_ids": "fixture:1",
        "episode_truth_case_ids": "fixture_episode_truth",
        "candidate_reading": "fixture candidate reading",
        "default_review_disposition": "hold until manually adjudicated",
        "must_prove_axes": "continuity; same-family morphology",
        "must_reject_axes": "common-cause; measurement artifact",
        "review_question": "fixture question",
        "allowed_reviewer_truth_labels": (
            "real_precursor; episode_only_or_backdating; strict_sudden_no_precursor; "
            "common_cause_or_measurement_hold; insufficient_evidence_hold"
        ),
        "reviewer_next_action": "manual adjudication",
        "operator_facing_change_allowed": 0,
        "engine_patch_allowed": 0,
        "threshold_patch_allowed": 0,
    }


def write_fixtures(root: Path) -> tuple[Path, Path]:
    trace_path = root / "trace.csv"
    index_path = root / "index.csv"
    trace_rows = [
        trace_row(
            "BR082-EPR-001",
            "fixture_source:1",
            "long_gap_backdating_review",
            "ktc_ess",
            "panel-a",
            270,
            "long_gap_one_day_episode_hold",
            "block_precursor_backdating",
            "급작 고장",
        ),
        trace_row(
            "BR082-EPR-001",
            "fixture_source:2",
            "long_gap_backdating_review",
            "ktc_ess",
            "panel-a",
            270,
            "long_gap_one_day_episode_hold",
            "block_precursor_backdating",
            "급작 고장",
        ),
        trace_row(
            "BR082-EPR-002",
            "fixture_source:3",
            "strict_sudden_prior_episode_review",
            "ktc_ess",
            "panel-b",
            0,
            "sudden_fault_strict_anchor",
            "no_precursor_promotion",
            "급작 고장",
        ),
        trace_row(
            "BR082-EPR-003",
            "fixture_source:4",
            "durable_precursor_review",
            "conalog",
            "panel-c",
            54,
            "intermittent_precursor_candidate",
            "manual_review_candidate",
            "전조형 고장",
        ),
    ]
    index_rows = [
        index_row(root, "BR082-EPR-001", "long_gap_backdating_review", "ktc_ess", "panel-a", 270),
        index_row(root, "BR082-EPR-002", "strict_sudden_prior_episode_review", "ktc_ess", "panel-b", 0),
        index_row(root, "BR082-EPR-003", "durable_precursor_review", "conalog", "panel-c", 54),
    ]
    pd.DataFrame(trace_rows).reindex(columns=TRACE_COLUMNS).to_csv(trace_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(index_rows).reindex(columns=INDEX_COLUMNS).to_csv(index_path, index=False, encoding="utf-8-sig")
    return trace_path, index_path


def run_builder(repo_root: Path, trace_path: Path, index_path: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
    return run(
        [
            sys.executable,
            "research/prognostics/build_panel_day_engine_episode_truth_adjudication_worksheet_v1.py",
            "--repo-root",
            str(repo_root),
            "--trace-input",
            str(trace_path),
            "--index-input",
            str(index_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=repo_root,
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        trace_path, index_path = write_fixtures(root)
        output_dir = root / "out"

        proc = run_builder(repo_root, trace_path, index_path, output_dir)
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)

        worksheet = pd.read_csv(output_dir / WORKSHEET_NAME, encoding="utf-8-sig")
        draft = pd.read_csv(output_dir / DRAFT_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(output_dir / SUMMARY_NAME, encoding="utf-8-sig")
        payload = json.loads((output_dir / JSON_NAME).read_text(encoding="utf-8"))

        assert_true(len(worksheet) == 3, f"expected 3 worksheet rows, got {len(worksheet)}")
        assert_true(len(draft) == 3, f"expected 3 draft rows, got {len(draft)}")
        directions = set(worksheet["suggested_review_direction"])
        assert_true("negative_or_hold_candidate" in directions, "missing long-gap negative/hold direction")
        assert_true("strict_sudden_negative_candidate" in directions, "missing strict-sudden negative direction")
        assert_true("manual_positive_or_hold_candidate" in directions, "missing durable manual positive/hold direction")
        assert_true(int(worksheet["source_reference_count"].sum()) == 4, "source reference compression changed")
        assert_true(int(worksheet["trace_ready_all"].sum()) == 3, "trace-ready rows should all be ready")
        assert_true(int(worksheet["threshold_replay_input_allowed"].sum()) == 0, "worksheet must not allow replay")
        assert_true(int(worksheet["operator_facing_change_allowed"].sum()) == 0, "worksheet must not authorize operator change")
        assert_true(int(worksheet["engine_patch_allowed"].sum()) == 0, "worksheet must not authorize engine patch")
        assert_true(int(worksheet["threshold_patch_allowed"].sum()) == 0, "worksheet must not authorize threshold patch")
        assert_true(draft["reviewer_truth_label"].fillna("").eq("").all(), "draft labels must stay blank")
        assert_true(draft["reviewer_evidence_path"].fillna("").eq("").all(), "draft evidence paths must stay blank")
        assert_true(payload["worksheet_rows"] == 3, "json worksheet row count mismatch")
        assert_true(payload["reviewer_truth_label_assigned_count"] == 0, "json should not assign labels")
        assert_true(payload["threshold_replay_ready_count"] == 0, "json should block replay")
        assert_true(int(summary["threshold_replay_ready_count"].sum()) == 0, "summary should block replay")

        unsafe_index = pd.read_csv(index_path, encoding="utf-8-sig")
        unsafe_index["reviewer_truth_label"] = unsafe_index["reviewer_truth_label"].fillna("").astype(str)
        unsafe_index.loc[0, "reviewer_truth_label"] = "real_precursor"
        unsafe_path = root / "unsafe_index_label.csv"
        unsafe_index.to_csv(unsafe_path, index=False, encoding="utf-8-sig")
        unsafe_proc = run_builder(repo_root, trace_path, unsafe_path, root / "unsafe_out_label")
        assert_true(unsafe_proc.returncode != 0, "filled labels should fail safe-input guard")

        unsafe_index = pd.read_csv(index_path, encoding="utf-8-sig")
        unsafe_index.loc[0, "engine_patch_allowed"] = 1
        unsafe_path = root / "unsafe_index_engine.csv"
        unsafe_index.to_csv(unsafe_path, index=False, encoding="utf-8-sig")
        unsafe_proc = run_builder(repo_root, trace_path, unsafe_path, root / "unsafe_out_engine")
        assert_true(unsafe_proc.returncode != 0, "engine patch authorization should fail safe-input guard")

    print("smoke ok: panel_day_engine_episode_truth_adjudication_worksheet_v1")


if __name__ == "__main__":
    main()
