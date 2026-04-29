#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


TRACE_NAME = "panel_day_engine_episode_truth_source_trace_audit_v1.csv"
SUMMARY_NAME = "panel_day_engine_episode_truth_source_trace_audit_summary_v1.csv"
ACTION_NAME = "panel_day_engine_episode_truth_source_trace_audit_action_queue_v1.csv"
NOTE_NAME = "panel_day_engine_episode_truth_source_trace_audit_note_v1.md"
JSON_NAME = "panel_day_engine_episode_truth_source_trace_audit_v1.json"


INDEX_COLUMNS = [
    "owner_branch",
    "attachment_row_id",
    "reviewed_truth_row_id",
    "review_packet_id",
    "evidence_status",
    "evidence_card_path",
    "review_input_template_ready",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "threshold_replay_input_allowed",
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
    "must_prove_axis_count",
    "must_reject_axis_count",
    "review_question",
    "allowed_reviewer_truth_labels",
    "reviewer_next_action",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]


TEMPLATE_COLUMNS = [
    "review_packet_id",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "reviewer_notes",
    "reviewed_truth_row_id",
    "evidence_card_path",
]


SOURCE_COLUMNS = [
    "site",
    "panel_id",
    "current_event_type_ko",
    "current_final_pattern_ko",
    "algorithm_family_ko",
    "heuristic_top1_ko",
    "episode_basis_date",
    "episode_basis_kind",
    "strict_trigger_date",
    "gap_days",
    "episode_class_shadow",
    "precursor_promotion_shadow_decision",
    "shadow_reason_ko",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_fixture_repo(root: Path) -> tuple[Path, Path]:
    source_dir = root / "docs"
    source_dir.mkdir(parents=True, exist_ok=True)
    shadow_rows = [
        {
            "site": "ktc_ess",
            "panel_id": "panel-a",
            "current_event_type_ko": "급작 고장",
            "current_final_pattern_ko": "급작 발생",
            "algorithm_family_ko": "모듈손상형",
            "heuristic_top1_ko": "열화형",
            "episode_basis_date": "2025-01-29",
            "episode_basis_kind": "g1_original_suppressed_onset",
            "strict_trigger_date": "2025-10-26",
            "gap_days": 270,
            "episode_class_shadow": "long_gap_one_day_episode_hold",
            "precursor_promotion_shadow_decision": "block_precursor_backdating",
            "shadow_reason_ko": "one-day degradation with gap>120 days",
        },
        {
            "site": "conalog",
            "panel_id": "panel-b",
            "current_event_type_ko": "전조형 고장",
            "current_final_pattern_ko": "급격 종료",
            "algorithm_family_ko": "개방/장치이상형",
            "heuristic_top1_ko": "센서·피드백형",
            "episode_basis_date": "2024-11-06",
            "episode_basis_kind": "retrospective_onset_date",
            "strict_trigger_date": "2024-11-26",
            "gap_days": 20,
            "episode_class_shadow": "manual_review_episode",
            "precursor_promotion_shadow_decision": "manual_review",
            "shadow_reason_ko": "threshold candidate inconclusive",
        },
    ]
    pd.DataFrame(shadow_rows).reindex(columns=SOURCE_COLUMNS).to_csv(
        source_dir / "OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_EPISODE_SHADOW_PANEL_V1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame([shadow_rows[0]]).reindex(columns=SOURCE_COLUMNS).to_csv(
        source_dir / "OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_G1_LONGGAP_CASES_V1.csv",
        index=False,
        encoding="utf-8-sig",
    )

    card_dir = root / "cards"
    card_dir.mkdir()
    card1 = card_dir / "card-1.md"
    card2 = card_dir / "card-2.md"
    card1.write_text("# card 1\n", encoding="utf-8")
    card2.write_text("# card 2\n", encoding="utf-8")

    index_path = root / "index.csv"
    template_path = root / "template.csv"
    index_rows = [
        {
            "owner_branch": "BR-085",
            "attachment_row_id": "BR085-EVA-001",
            "reviewed_truth_row_id": "BR084-RTR-001",
            "review_packet_id": "BR082-EPR-001",
            "evidence_status": "card_created_needs_reviewer_label",
            "evidence_card_path": str(card1),
            "review_input_template_ready": 1,
            "reviewer_truth_label": "",
            "reviewer_evidence_path": "",
            "threshold_replay_input_allowed": 0,
            "review_priority": "P0",
            "review_track": "long_gap_backdating_review",
            "episode_truth_bucket": "long_gap_backdating_hold",
            "site": "ktc_ess",
            "panel_id": "panel-a",
            "family_key": "degradation_soiling_shadow",
            "family_label_ko": "family",
            "subtype_key": "long_gap_one_day_stress",
            "subtype_label_ko": "subtype",
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
            "source_case_ids": "br017_episode_shadow:1; br017_g1_longgap_cases:1",
            "episode_truth_case_ids": "BR081-EPS-001",
            "candidate_reading": "candidate",
            "default_review_disposition": "hold",
            "must_prove_axes": "axis-a; axis-b",
            "must_reject_axes": "reject-a",
            "must_prove_axis_count": 2,
            "must_reject_axis_count": 1,
            "review_question": "question",
            "allowed_reviewer_truth_labels": "real_precursor; episode_only_or_backdating",
            "reviewer_next_action": "review",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "",
        },
        {
            "owner_branch": "BR-085",
            "attachment_row_id": "BR085-EVA-002",
            "reviewed_truth_row_id": "BR084-RTR-002",
            "review_packet_id": "BR082-EPR-002",
            "evidence_status": "card_created_needs_reviewer_label",
            "evidence_card_path": str(card2),
            "review_input_template_ready": 1,
            "reviewer_truth_label": "",
            "reviewer_evidence_path": "",
            "threshold_replay_input_allowed": 0,
            "review_priority": "P1",
            "review_track": "durable_precursor_review",
            "episode_truth_bucket": "durable_precursor_candidate_review",
            "site": "conalog",
            "panel_id": "panel-b",
            "family_key": "open_connection_partial",
            "family_label_ko": "family",
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
            "source_case_ids": "br017_episode_shadow:2",
            "episode_truth_case_ids": "BR081-EPS-002",
            "candidate_reading": "candidate",
            "default_review_disposition": "review",
            "must_prove_axes": "axis-c",
            "must_reject_axes": "reject-c",
            "must_prove_axis_count": 1,
            "must_reject_axis_count": 1,
            "review_question": "question",
            "allowed_reviewer_truth_labels": "real_precursor; strict_sudden_no_precursor",
            "reviewer_next_action": "review",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "",
        },
    ]
    pd.DataFrame(index_rows).reindex(columns=INDEX_COLUMNS).to_csv(index_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(
        [
            {
                "review_packet_id": "BR082-EPR-001",
                "reviewer_truth_label": "",
                "reviewer_evidence_path": "",
                "reviewer_notes": "",
                "reviewed_truth_row_id": "BR084-RTR-001",
                "evidence_card_path": str(card1),
            },
            {
                "review_packet_id": "BR082-EPR-002",
                "reviewer_truth_label": "",
                "reviewer_evidence_path": "",
                "reviewer_notes": "",
                "reviewed_truth_row_id": "BR084-RTR-002",
                "evidence_card_path": str(card2),
            },
        ]
    ).reindex(columns=TEMPLATE_COLUMNS).to_csv(template_path, index=False, encoding="utf-8-sig")
    return index_path, template_path


def run_builder(
    repo_root: Path,
    script: Path,
    fixture_repo: Path,
    index_input: Path | None,
    template_input: Path | None,
    output_dir: Path,
    input_manifest: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(script),
        "--repo-root",
        str(fixture_repo),
        "--output-dir",
        str(output_dir),
        "--owner-branch",
        "BR-TEST-086",
    ]
    if index_input is not None:
        cmd.extend(["--index-input", str(index_input)])
    if template_input is not None:
        cmd.extend(["--template-input", str(template_input)])
    if input_manifest is not None:
        cmd.extend(["--input-manifest", str(input_manifest)])
    return run(cmd, repo_root)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research/prognostics/build_panel_day_engine_episode_truth_source_trace_audit_v1.py"
    with tempfile.TemporaryDirectory(prefix="episode_truth_source_trace_smoke_") as tmpdir:
        root = Path(tmpdir)
        fixture_repo = root / "fixture_repo"
        fixture_repo.mkdir()
        index_path, template_path = write_fixture_repo(fixture_repo)
        out_dir = root / "out"
        completed = run_builder(repo_root, script, fixture_repo, index_path, template_path, out_dir)
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)
        trace_df = pd.read_csv(out_dir / TRACE_NAME, encoding="utf-8-sig")
        summary_df = pd.read_csv(out_dir / SUMMARY_NAME, encoding="utf-8-sig")
        action_df = pd.read_csv(out_dir / ACTION_NAME, encoding="utf-8-sig")
        payload = json.loads((out_dir / JSON_NAME).read_text(encoding="utf-8"))
        note = (out_dir / NOTE_NAME).read_text(encoding="utf-8")

        assert_true(len(trace_df) == 3, trace_df.to_string())
        assert_true(int(trace_df["source_file_exists"].sum()) == 3, trace_df.to_string())
        assert_true(int(trace_df["source_row_resolved"].sum()) == 3, trace_df.to_string())
        assert_true(int(trace_df["source_identity_match"].sum()) == 3, trace_df.to_string())
        assert_true(int(trace_df["trace_ready"].sum()) == 3, trace_df.to_string())
        assert_true(set(trace_df["label_fill_status"]) == {"trace_ready_needs_human_label"}, trace_df.to_string())
        assert_true(int(trace_df["operator_facing_change_allowed"].sum()) == 0, trace_df.to_string())
        assert_true(int(trace_df["engine_patch_allowed"].sum()) == 0, trace_df.to_string())
        assert_true(int(trace_df["threshold_patch_allowed"].sum()) == 0, trace_df.to_string())
        assert_true(len(summary_df) == 2, summary_df.to_string())
        assert_true(len(action_df) == 3, action_df.to_string())
        assert_true(payload["source_reference_count"] == 3, payload)
        assert_true(payload["trace_ready_count"] == 3, payload)
        assert_true(payload["threshold_replay_ready_count"] == 0, payload)
        assert_true(payload["input_manifest"] == "", payload)
        assert_true(payload["index_input_source"] == "explicit_cli", payload)
        assert_true(payload["template_input_source"] == "explicit_cli", payload)
        assert_true("no truth label" in note, note)

        manifest_path = root / "episode_truth_source_trace_inputs.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "inputs": {
                        "index_input": str(index_path),
                        "template_input": str(template_path),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_out = root / "manifest_out"
        manifest_completed = run_builder(repo_root, script, fixture_repo, None, None, manifest_out, manifest_path)
        assert_true(manifest_completed.returncode == 0, manifest_completed.stderr or manifest_completed.stdout)
        manifest_payload = json.loads((manifest_out / JSON_NAME).read_text(encoding="utf-8"))
        assert_true(manifest_payload["source_reference_count"] == payload["source_reference_count"], manifest_payload)
        assert_true(manifest_payload["trace_ready_count"] == payload["trace_ready_count"], manifest_payload)
        assert_true(manifest_payload["input_manifest"] == str(manifest_path), manifest_payload)
        assert_true(manifest_payload["index_input_source"] == "input_manifest", manifest_payload)
        assert_true(manifest_payload["template_input_source"] == "input_manifest", manifest_payload)

        bad_manifest_path = root / "bad_episode_truth_source_trace_inputs.json"
        bad_manifest_path.write_text(
            json.dumps(
                {
                    "inputs": {
                        "index_input": str(root / "missing_index.csv"),
                        "template_input": str(root / "missing_template.csv"),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_out = root / "override_out"
        override_completed = run_builder(
            repo_root,
            script,
            fixture_repo,
            index_path,
            template_path,
            override_out,
            bad_manifest_path,
        )
        assert_true(override_completed.returncode == 0, override_completed.stderr or override_completed.stdout)
        override_payload = json.loads((override_out / JSON_NAME).read_text(encoding="utf-8"))
        assert_true(override_payload["index_input_source"] == "explicit_cli", override_payload)
        assert_true(override_payload["template_input_source"] == "explicit_cli", override_payload)

        missing_key_manifest_path = root / "missing_key_episode_truth_source_trace_inputs.json"
        missing_key_manifest_path.write_text(
            json.dumps({"inputs": {"index_input": str(index_path)}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        missing_key_completed = run_builder(
            repo_root,
            script,
            fixture_repo,
            None,
            None,
            root / "missing_key_out",
            missing_key_manifest_path,
        )
        assert_true(missing_key_completed.returncode != 0, missing_key_completed.stdout)
        assert_true("missing `template_input`" in missing_key_completed.stderr, missing_key_completed.stderr)

        unsafe = pd.read_csv(index_path, encoding="utf-8-sig")
        unsafe.loc[0, "engine_patch_allowed"] = 1
        unsafe_path = root / "unsafe_index.csv"
        unsafe.to_csv(unsafe_path, index=False, encoding="utf-8-sig")
        unsafe_completed = run_builder(repo_root, script, fixture_repo, unsafe_path, template_path, root / "unsafe_out")
        assert_true(unsafe_completed.returncode != 0, unsafe_completed.stdout)
        assert_true("non-authorizing BR-085 input" in unsafe_completed.stderr, unsafe_completed.stderr)

    print("smoke_test_panel_day_engine_episode_truth_source_trace_audit_v1.py: PASS")


if __name__ == "__main__":
    main()
