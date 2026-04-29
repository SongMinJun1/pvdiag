#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


PACKET_NAME = "panel_day_engine_episode_truth_review_packet_v1.csv"
SUMMARY_NAME = "panel_day_engine_episode_truth_review_packet_summary_v1.csv"
ACTION_NAME = "panel_day_engine_episode_truth_review_action_queue_v1.csv"
NOTE_NAME = "panel_day_engine_episode_truth_review_packet_note_v1.md"
JSON_NAME = "panel_day_engine_episode_truth_review_packet_v1.json"

MAP_COLUMNS = [
    "owner_branch",
    "episode_truth_case_id",
    "source_artifact",
    "source_case_id",
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
    "episode_truth_bucket",
    "episode_truth_status",
    "promotion_reading",
    "required_next_evidence",
    "recommended_next_artifact",
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


def write_map(path: Path) -> None:
    rows = [
        {
            "owner_branch": "BR-081",
            "episode_truth_case_id": "BR081-EPS-001",
            "source_artifact": "br017_episode_shadow",
            "source_case_id": "br017_episode_shadow:1",
            "site": "ktc_ess",
            "panel_id": "p-long",
            "family_key": "degradation_soiling_shadow",
            "family_label_ko": "degradation",
            "subtype_key": "long_gap_one_day_stress",
            "subtype_label_ko": "long gap",
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
            "episode_truth_bucket": "long_gap_backdating_hold",
            "episode_truth_status": "truth_pending",
            "promotion_reading": "block_precursor_backdating",
            "required_next_evidence": "confirm long gap",
            "recommended_next_artifact": "panel_day_engine_episode_truth_review_packet_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "long gap lens A",
        },
        {
            "owner_branch": "BR-081",
            "episode_truth_case_id": "BR081-G1-001",
            "source_artifact": "br017_g1_longgap_cases",
            "source_case_id": "br017_g1_longgap_cases:1",
            "site": "ktc_ess",
            "panel_id": "p-long",
            "family_key": "degradation_soiling_shadow",
            "family_label_ko": "degradation",
            "subtype_key": "long_gap_one_day_stress",
            "subtype_label_ko": "long gap",
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
            "episode_truth_bucket": "long_gap_backdating_hold",
            "episode_truth_status": "truth_pending",
            "promotion_reading": "block_precursor_backdating",
            "required_next_evidence": "confirm long gap",
            "recommended_next_artifact": "panel_day_engine_episode_truth_review_packet_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "long gap lens B",
        },
        {
            "owner_branch": "BR-081",
            "episode_truth_case_id": "BR081-EPS-002",
            "source_artifact": "br017_episode_shadow",
            "source_case_id": "br017_episode_shadow:2",
            "site": "gangui",
            "panel_id": "p-sudden",
            "family_key": "strict_anchor_sudden",
            "family_label_ko": "strict sudden",
            "subtype_key": "",
            "subtype_label_ko": "",
            "episode_anchor_date": "2025-06-08",
            "episode_anchor_kind": "strict_trigger_date",
            "strict_trigger_date": "2025-06-08",
            "gap_days": 0,
            "signal_start_date": "2025-06-08",
            "signal_end_date": "2025-06-08",
            "signal_span_days": 0,
            "signal_day_count": 0,
            "duration_proxy_days": 0,
            "recurrence_proxy_days": 0,
            "warning_proxy_days": 0,
            "common_cause_flag_sum": 0,
            "strict_trigger_proximal_common_cause_flag": 0,
            "episode_truth_bucket": "strict_anchor_sudden_review",
            "episode_truth_status": "truth_pending",
            "promotion_reading": "no_precursor_promotion_without_prior_episode",
            "required_next_evidence": "prove prior episode",
            "recommended_next_artifact": "panel_day_engine_episode_truth_review_packet_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "sudden",
        },
        {
            "owner_branch": "BR-081",
            "episode_truth_case_id": "BR081-EPS-003",
            "source_artifact": "br017_episode_shadow",
            "source_case_id": "br017_episode_shadow:3",
            "site": "conalog",
            "panel_id": "p-durable",
            "family_key": "open_connection_partial",
            "family_label_ko": "open",
            "subtype_key": "",
            "subtype_label_ko": "",
            "episode_anchor_date": "2024-11-05",
            "episode_anchor_kind": "retrospective_onset_date",
            "strict_trigger_date": "2024-12-29",
            "gap_days": 54,
            "signal_start_date": "2024-11-05",
            "signal_end_date": "2024-12-29",
            "signal_span_days": 54,
            "signal_day_count": 0,
            "duration_proxy_days": 0,
            "recurrence_proxy_days": 4,
            "warning_proxy_days": 1,
            "common_cause_flag_sum": 0,
            "strict_trigger_proximal_common_cause_flag": 0,
            "episode_truth_bucket": "durable_precursor_candidate_review",
            "episode_truth_status": "truth_pending",
            "promotion_reading": "manual_review_before_promotion",
            "required_next_evidence": "prove durable precursor",
            "recommended_next_artifact": "panel_day_engine_episode_truth_review_packet_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "durable",
        },
        {
            "owner_branch": "BR-081",
            "episode_truth_case_id": "BR081-EPS-004",
            "source_artifact": "br017_episode_shadow",
            "source_case_id": "br017_episode_shadow:4",
            "site": "conalog",
            "panel_id": "p-held",
            "family_key": "external_common_cause",
            "family_label_ko": "common",
            "subtype_key": "",
            "subtype_label_ko": "",
            "episode_anchor_date": "2025-01-01",
            "episode_anchor_kind": "retrospective_onset_date",
            "strict_trigger_date": "2025-01-02",
            "gap_days": 1,
            "signal_start_date": "2025-01-01",
            "signal_end_date": "2025-01-02",
            "signal_span_days": 1,
            "signal_day_count": 1,
            "duration_proxy_days": 1,
            "recurrence_proxy_days": 1,
            "warning_proxy_days": 0,
            "common_cause_flag_sum": 2,
            "strict_trigger_proximal_common_cause_flag": 1,
            "episode_truth_bucket": "common_cause_or_group_episode_hold",
            "episode_truth_status": "truth_pending",
            "promotion_reading": "block_individual_precursor",
            "required_next_evidence": "common-cause review",
            "recommended_next_artifact": "panel_day_engine_episode_common_cause_review_packet_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "not selected",
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=MAP_COLUMNS).to_csv(path, index=False, encoding="utf-8-sig")


def run_builder(
    repo_root: Path,
    script: Path,
    episode_map_input: Path | None,
    output_dir: Path,
    input_manifest: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(script),
        "--repo-root",
        str(repo_root),
        "--output-dir",
        str(output_dir),
        "--owner-branch",
        "BR-TEST-082",
    ]
    if episode_map_input is not None:
        cmd.extend(["--episode-map-input", str(episode_map_input)])
    if input_manifest is not None:
        cmd.extend(["--input-manifest", str(input_manifest)])
    return run(cmd, repo_root)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research/prognostics/build_panel_day_engine_episode_truth_review_packet_v1.py"
    with tempfile.TemporaryDirectory(prefix="episode_truth_review_packet_smoke_") as tmpdir:
        root = Path(tmpdir)
        input_path = root / "map.csv"
        output_dir = root / "out"
        write_map(input_path)
        completed = run_builder(repo_root, script, input_path, output_dir)
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)

        packet = pd.read_csv(output_dir / PACKET_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(output_dir / SUMMARY_NAME, encoding="utf-8-sig")
        action = pd.read_csv(output_dir / ACTION_NAME, encoding="utf-8-sig")
        payload = json.loads((output_dir / JSON_NAME).read_text(encoding="utf-8"))
        note_text = (output_dir / NOTE_NAME).read_text(encoding="utf-8")

        assert_true(len(packet) == 3, packet.to_string())
        assert_true(payload["selected_source_lens_rows"] == 4, payload)
        assert_true(payload["review_packet_rows"] == 3, payload)
        assert_true(payload["collapsed_duplicate_lens_count"] == 1, payload)
        assert_true(payload["input_manifest"] == "", payload)
        assert_true(payload["episode_map_input_source"] == "explicit_cli", payload)
        assert_true(set(packet["review_track"]) == {
            "long_gap_backdating_review",
            "strict_sudden_prior_episode_review",
            "durable_precursor_review",
        }, packet.to_string())
        long_gap = packet.loc[packet["review_track"].eq("long_gap_backdating_review")].iloc[0]
        assert_true(int(long_gap["source_lens_count"]) == 2, long_gap.to_string())
        assert_true("br017_episode_shadow" in long_gap["source_artifacts"], long_gap.to_string())
        assert_true("br017_g1_longgap_cases" in long_gap["source_artifacts"], long_gap.to_string())
        assert_true((packet["reviewer_truth_label"].fillna("") == "").all(), packet.to_string())
        assert_true(int(packet["operator_facing_change_allowed"].sum()) == 0, packet.to_string())
        assert_true(int(packet["engine_patch_allowed"].sum()) == 0, packet.to_string())
        assert_true(int(packet["threshold_patch_allowed"].sum()) == 0, packet.to_string())
        assert_true(len(summary) == 3, summary.to_string())
        assert_true(action["sequence"].tolist() == sorted(action["sequence"].tolist()), action.to_string())
        assert_true(action.iloc[0]["action_id"] == "ACT-001", action.to_string())
        assert_true("review-only" in note_text, note_text)

        manifest_path = root / "episode_truth_review_packet_inputs.json"
        manifest_path.write_text(
            json.dumps({"inputs": {"episode_map_input": str(input_path)}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest_out = root / "manifest_out"
        manifest_completed = run_builder(repo_root, script, None, manifest_out, manifest_path)
        assert_true(manifest_completed.returncode == 0, manifest_completed.stderr or manifest_completed.stdout)
        manifest_payload = json.loads((manifest_out / JSON_NAME).read_text(encoding="utf-8"))
        assert_true(manifest_payload["review_packet_rows"] == payload["review_packet_rows"], manifest_payload)
        assert_true(manifest_payload["collapsed_duplicate_lens_count"] == payload["collapsed_duplicate_lens_count"], manifest_payload)
        assert_true(manifest_payload["input_manifest"] == str(manifest_path), manifest_payload)
        assert_true(manifest_payload["episode_map_input_source"] == "input_manifest", manifest_payload)

        bad_manifest_path = root / "bad_episode_truth_review_packet_inputs.json"
        bad_manifest_path.write_text(
            json.dumps(
                {"inputs": {"episode_map_input": str(root / "missing_episode_map.csv")}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_out = root / "override_out"
        override_completed = run_builder(repo_root, script, input_path, override_out, bad_manifest_path)
        assert_true(override_completed.returncode == 0, override_completed.stderr or override_completed.stdout)
        override_payload = json.loads((override_out / JSON_NAME).read_text(encoding="utf-8"))
        assert_true(override_payload["episode_map_input_source"] == "explicit_cli", override_payload)

        missing_key_manifest_path = root / "missing_key_episode_truth_review_packet_inputs.json"
        missing_key_manifest_path.write_text(json.dumps({"inputs": {}}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        missing_key_completed = run_builder(repo_root, script, None, root / "missing_key_out", missing_key_manifest_path)
        assert_true(missing_key_completed.returncode != 0, missing_key_completed.stdout)
        assert_true("missing `episode_map_input`" in missing_key_completed.stderr, missing_key_completed.stderr)

    print("smoke_test_panel_day_engine_episode_truth_review_packet_v1.py: PASS")


if __name__ == "__main__":
    main()
