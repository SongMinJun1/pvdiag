#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


INDEX_NAME = "panel_day_engine_episode_truth_evidence_attachment_index_v1.csv"
TEMPLATE_NAME = "panel_day_engine_episode_truth_review_input_template_v1.csv"
SUMMARY_NAME = "panel_day_engine_episode_truth_evidence_attachment_summary_v1.csv"
ACTION_NAME = "panel_day_engine_episode_truth_evidence_attachment_action_queue_v1.csv"
NOTE_NAME = "panel_day_engine_episode_truth_evidence_attachment_note_v1.md"
JSON_NAME = "panel_day_engine_episode_truth_evidence_attachment_v1.json"
CARDS_DIR_NAME = "panel_day_engine_episode_truth_evidence_cards_v1"


ROW_COLUMNS = [
    "owner_branch",
    "reviewed_truth_row_id",
    "review_packet_id",
    "review_status",
    "truth_role",
    "reviewer_truth_label",
    "truth_label_source",
    "reviewer_evidence_path",
    "reviewer_notes",
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
    "review_question",
    "threshold_replay_input_allowed",
    "threshold_replay_role",
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


def run_builder(
    repo_root: Path,
    script: Path,
    rows_path: Path | None,
    output_dir: Path,
    input_manifest: Path | None = None,
    owner_branch: str = "BR-TEST-085",
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(script),
        "--repo-root",
        str(repo_root),
        "--output-dir",
        str(output_dir),
        "--owner-branch",
        owner_branch,
    ]
    if rows_path is not None:
        cmd.extend(["--reviewed-rows-input", str(rows_path)])
    if input_manifest is not None:
        cmd.extend(["--input-manifest", str(input_manifest)])
    return run(cmd, repo_root)


def write_rows(path: Path, *, unsafe: bool = False) -> None:
    rows = [
        {
            "owner_branch": "BR-084",
            "reviewed_truth_row_id": "BR084-RTR-001",
            "review_packet_id": "BR082-EPR-001",
            "review_status": "needs_evidence",
            "truth_role": "unassigned",
            "reviewer_truth_label": "",
            "truth_label_source": "none",
            "reviewer_evidence_path": "",
            "reviewer_notes": "",
            "review_priority": "P0",
            "review_track": "long_gap_backdating_review",
            "episode_truth_bucket": "long_gap_backdating_hold",
            "site": "ktc_ess",
            "panel_id": "panel-a",
            "family_key": "degradation_soiling_shadow",
            "family_label_ko": "family-a",
            "subtype_key": "long_gap_one_day_stress",
            "subtype_label_ko": "subtype-a",
            "episode_anchor_date": "2025-01-29",
            "episode_anchor_kind": "g1_original_suppressed_onset",
            "strict_trigger_date": "2025-10-26",
            "gap_days": 270,
            "signal_start_date": "2025-01-29",
            "signal_end_date": "2025-10-26",
            "signal_span_days": 270,
            "signal_day_count": 3,
            "duration_proxy_days": 3,
            "recurrence_proxy_days": 7,
            "warning_proxy_days": 15,
            "common_cause_flag_sum": 2,
            "strict_trigger_proximal_common_cause_flag": 1,
            "source_lens_count": 2,
            "source_artifacts": "br017_episode_shadow; br017_g1_longgap_cases",
            "source_case_ids": "br017_episode_shadow:121; br017_g1_longgap_cases:1",
            "episode_truth_case_ids": "BR081-EPS-121; BR081-G1-001",
            "candidate_reading": "possible_over_backdated_precursor_or_sparse_episode",
            "default_review_disposition": "hold_backdating_until_prior_signal_chain_is_proven",
            "must_prove_axes": "same-panel prior signal chain; continuity or recurrence; common-cause exclusion",
            "must_reject_axes": "one-day sparse signal; long normal gap; no same-panel continuity",
            "review_question": "Was the distant onset real?",
            "threshold_replay_input_allowed": 0,
            "threshold_replay_role": "not_replay_input",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 1 if unsafe else 0,
            "threshold_patch_allowed": 0,
            "notes": "",
        },
        {
            "owner_branch": "BR-084",
            "reviewed_truth_row_id": "BR084-RTR-002",
            "review_packet_id": "BR082-EPR-002",
            "review_status": "needs_evidence",
            "truth_role": "unassigned",
            "reviewer_truth_label": "",
            "truth_label_source": "none",
            "reviewer_evidence_path": "",
            "reviewer_notes": "",
            "review_priority": "P1",
            "review_track": "durable_precursor_review",
            "episode_truth_bucket": "durable_precursor_candidate_review",
            "site": "conalog",
            "panel_id": "panel-b",
            "family_key": "open_connection_partial",
            "family_label_ko": "family-b",
            "subtype_key": "",
            "subtype_label_ko": "",
            "episode_anchor_date": "2024-11-06",
            "episode_anchor_kind": "retrospective_onset_date",
            "strict_trigger_date": "2024-11-26",
            "gap_days": 20,
            "signal_start_date": "2024-11-06",
            "signal_end_date": "2024-11-26",
            "signal_span_days": 20,
            "signal_day_count": 0,
            "duration_proxy_days": 4,
            "recurrence_proxy_days": 0,
            "warning_proxy_days": 0,
            "common_cause_flag_sum": 0,
            "strict_trigger_proximal_common_cause_flag": 0,
            "source_lens_count": 1,
            "source_artifacts": "br017_episode_shadow",
            "source_case_ids": "br017_episode_shadow:23",
            "episode_truth_case_ids": "BR081-EPS-023",
            "candidate_reading": "plausible_durable_precursor_candidate",
            "default_review_disposition": "manual_review_no_promotion_yet",
            "must_prove_axes": "duration or recurrence; family-shape match; common-cause exclusion",
            "must_reject_axes": "common-cause overlap; weak one-day signal; mismatched fault family",
            "review_question": "Does the signal predict later fault family?",
            "threshold_replay_input_allowed": 0,
            "threshold_replay_role": "not_replay_input",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "",
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=ROW_COLUMNS).to_csv(path, index=False, encoding="utf-8-sig")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research/prognostics/build_panel_day_engine_episode_truth_evidence_attachment_v1.py"
    with tempfile.TemporaryDirectory(prefix="episode_truth_evidence_attachment_smoke_") as tmpdir:
        root = Path(tmpdir)
        rows_path = root / "br084_rows.csv"
        write_rows(rows_path)
        out_dir = root / "out"
        completed = run_builder(repo_root, script, rows_path, out_dir)
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)
        index_df = pd.read_csv(out_dir / INDEX_NAME, encoding="utf-8-sig")
        template_df = pd.read_csv(out_dir / TEMPLATE_NAME, encoding="utf-8-sig")
        summary_df = pd.read_csv(out_dir / SUMMARY_NAME, encoding="utf-8-sig")
        action_df = pd.read_csv(out_dir / ACTION_NAME, encoding="utf-8-sig")
        payload = json.loads((out_dir / JSON_NAME).read_text(encoding="utf-8"))
        cards = sorted((out_dir / CARDS_DIR_NAME).glob("*.md"))

        assert_true(len(index_df) == 2, index_df.to_string())
        assert_true(len(template_df) == 2, template_df.to_string())
        assert_true(len(cards) == 2, [str(path) for path in cards])
        assert_true(len(summary_df) == 2, summary_df.to_string())
        assert_true(len(action_df) == 3, action_df.to_string())
        assert_true(set(index_df["evidence_status"]) == {"card_created_needs_reviewer_label"}, index_df.to_string())
        assert_true(int(index_df["threshold_replay_input_allowed"].sum()) == 0, index_df.to_string())
        assert_true(int(index_df["engine_patch_allowed"].sum()) == 0, index_df.to_string())
        assert_true(template_df["reviewer_truth_label"].fillna("").eq("").all(), template_df.to_string())
        assert_true(template_df["reviewer_evidence_path"].fillna("").eq("").all(), template_df.to_string())
        assert_true(payload["input_rows"] == 2, payload)
        assert_true(payload["evidence_card_count"] == 2, payload)
        assert_true(payload["review_input_template_rows"] == 2, payload)
        assert_true(payload["reviewer_truth_label_assigned_count"] == 0, payload)
        assert_true(payload["threshold_replay_ready_count"] == 0, payload)
        assert_true(payload["reviewed_rows_input_source"] == "explicit_cli", payload)
        assert_true("not a truth label" in cards[0].read_text(encoding="utf-8"), cards[0])

        manifest_path = root / "episode_truth_evidence_attachment_inputs.json"
        manifest_path.write_text(
            json.dumps({"inputs": {"reviewed_rows_input": str(rows_path)}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest_out = root / "manifest_out"
        manifest_completed = run_builder(repo_root, script, None, manifest_out, manifest_path)
        assert_true(manifest_completed.returncode == 0, manifest_completed.stderr or manifest_completed.stdout)
        manifest_payload = json.loads((manifest_out / JSON_NAME).read_text(encoding="utf-8"))
        assert_true(manifest_payload["input_rows"] == 2, manifest_payload)
        assert_true(manifest_payload["input_manifest"] == str(manifest_path), manifest_payload)
        assert_true(manifest_payload["reviewed_rows_input_source"] == "input_manifest", manifest_payload)

        bad_manifest_path = root / "bad_episode_truth_evidence_attachment_inputs.json"
        bad_manifest_path.write_text(
            json.dumps(
                {"inputs": {"reviewed_rows_input": str(root / "missing_br084_rows.csv")}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_out = root / "override_out"
        override_completed = run_builder(repo_root, script, rows_path, override_out, bad_manifest_path)
        assert_true(override_completed.returncode == 0, override_completed.stderr or override_completed.stdout)
        override_payload = json.loads((override_out / JSON_NAME).read_text(encoding="utf-8"))
        assert_true(override_payload["reviewed_rows_input_source"] == "explicit_cli", override_payload)

        missing_key_manifest_path = root / "missing_key_episode_truth_evidence_attachment_inputs.json"
        missing_key_manifest_path.write_text(
            json.dumps({"inputs": {}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        missing_key_completed = run_builder(repo_root, script, None, root / "missing_key_out", missing_key_manifest_path)
        assert_true(missing_key_completed.returncode != 0, missing_key_completed.stdout)
        assert_true("missing `reviewed_rows_input`" in missing_key_completed.stderr, missing_key_completed.stderr)

        unsafe_rows_path = root / "unsafe_rows.csv"
        write_rows(unsafe_rows_path, unsafe=True)
        unsafe_completed = run_builder(repo_root, script, unsafe_rows_path, root / "unsafe_out")
        assert_true(unsafe_completed.returncode != 0, unsafe_completed.stdout)
        assert_true("non-authorizing BR-084 input" in unsafe_completed.stderr, unsafe_completed.stderr)

    print("smoke_test_panel_day_engine_episode_truth_evidence_attachment_v1.py: PASS")


if __name__ == "__main__":
    main()
