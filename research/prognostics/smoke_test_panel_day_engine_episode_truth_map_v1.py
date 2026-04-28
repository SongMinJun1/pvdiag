#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


MAP_NAME = "panel_day_engine_episode_truth_map_v1.csv"
SUMMARY_NAME = "panel_day_engine_episode_truth_map_summary_v1.csv"
ACTION_NAME = "panel_day_engine_episode_truth_map_action_queue_v1.csv"
NOTE_NAME = "panel_day_engine_episode_truth_map_note_v1.md"
JSON_NAME = "panel_day_engine_episode_truth_map_v1.json"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture(root: Path) -> dict[str, Path]:
    episode = root / "episode.csv"
    episode_cols = [
        "site",
        "panel_id",
        "algorithm_family_ko",
        "episode_basis_date",
        "episode_basis_kind",
        "strict_trigger_date",
        "gap_days",
        "degradation_days_in_window",
        "shadow_days_in_window",
        "low_mid_ratio_days_in_window",
        "event_A_days_after_onset",
        "low_mid_ratio_days_after_onset",
        "pre_ews_days_in_window",
        "ews_warning_days_in_window",
        "pre_alarm_days_in_window",
        "prefault_B_effective_days_in_window",
        "subgroup_common_cause_history_flag",
        "strict_trigger_proximal_common_cause_flag",
        "group_event_A_fraction_on_episode",
        "g1_suppressed_event_shadow_flag",
        "episode_class_shadow",
        "fault_family_hypothesis_shadow_ko",
        "precursor_promotion_shadow_decision",
        "shadow_reason_ko",
    ]
    write_csv(
        episode,
        [
            {
                "site": "ktc_ess",
                "panel_id": "p-long",
                "algorithm_family_ko": "모듈손상형",
                "episode_basis_date": "2025-01-01",
                "episode_basis_kind": "g1_original_suppressed_onset",
                "strict_trigger_date": "2025-10-01",
                "gap_days": 273,
                "degradation_days_in_window": 1,
                "shadow_days_in_window": 0,
                "low_mid_ratio_days_in_window": 1,
                "event_A_days_after_onset": 0,
                "low_mid_ratio_days_after_onset": 0,
                "pre_ews_days_in_window": 0,
                "ews_warning_days_in_window": 0,
                "pre_alarm_days_in_window": 0,
                "prefault_B_effective_days_in_window": 0,
                "subgroup_common_cause_history_flag": 0,
                "strict_trigger_proximal_common_cause_flag": 1,
                "group_event_A_fraction_on_episode": 0,
                "g1_suppressed_event_shadow_flag": 1,
                "episode_class_shadow": "long_gap_one_day_episode_hold",
                "fault_family_hypothesis_shadow_ko": "열화·오염·음영 계열 후보 보류",
                "precursor_promotion_shadow_decision": "block_precursor_backdating",
                "shadow_reason_ko": "one day long gap",
            },
            {
                "site": "conalog",
                "panel_id": "p-durable",
                "algorithm_family_ko": "모듈손상형",
                "episode_basis_date": "2025-01-01",
                "episode_basis_kind": "retrospective_onset_date",
                "strict_trigger_date": "2025-02-01",
                "gap_days": 31,
                "degradation_days_in_window": 3,
                "shadow_days_in_window": 0,
                "low_mid_ratio_days_in_window": 3,
                "event_A_days_after_onset": 2,
                "low_mid_ratio_days_after_onset": 2,
                "pre_ews_days_in_window": 2,
                "ews_warning_days_in_window": 0,
                "pre_alarm_days_in_window": 0,
                "prefault_B_effective_days_in_window": 0,
                "subgroup_common_cause_history_flag": 0,
                "strict_trigger_proximal_common_cause_flag": 0,
                "group_event_A_fraction_on_episode": 0,
                "g1_suppressed_event_shadow_flag": 0,
                "episode_class_shadow": "manual_review_episode",
                "fault_family_hypothesis_shadow_ko": "열화·오염·음영 계열",
                "precursor_promotion_shadow_decision": "manual_review",
                "shadow_reason_ko": "durable candidate",
            },
        ],
        episode_cols,
    )

    g1 = root / "g1.csv"
    write_csv(g1, [pd.read_csv(episode).iloc[0].to_dict()], episode_cols)

    shape = root / "shape.csv"
    write_csv(
        shape,
        [
            {
                "shape_case_id": "S1",
                "site": "conalog",
                "panel_id": "p-rec",
                "candidate_family_track": "unassigned_family_needs_shape_review",
                "candidate_family_label_ko": "unassigned_family_needs_shape_review",
                "family_shape_judgment_bucket": "recovery_recurrence_only_no_family_shape_hold",
                "signal_day_count": 40,
                "first_signal_date": "2025-01-01",
                "last_signal_date": "2025-06-01",
                "signal_span_days": 151,
                "re_drop_days": 40,
                "recovered_sustained_days": 0,
                "subgroup_common_cause_days": 0,
                "max_co_drop_frac": 0,
                "review_note": "recovery only",
            }
        ],
        [
            "shape_case_id",
            "site",
            "panel_id",
            "candidate_family_track",
            "candidate_family_label_ko",
            "family_shape_judgment_bucket",
            "signal_day_count",
            "first_signal_date",
            "last_signal_date",
            "signal_span_days",
            "re_drop_days",
            "recovered_sustained_days",
            "subgroup_common_cause_days",
            "max_co_drop_frac",
            "review_note",
        ],
    )

    blocker = root / "blocker.csv"
    write_csv(
        blocker,
        [
            {
                "review_packet_id": "B1",
                "site": "gangui",
                "panel_id": "p-group",
                "fault_family_hypothesis_shadow_ko": "다이오드·서브스트링 계열",
                "fault_subtype_hypothesis_shadow_ko": "bypass diode 동작·고장 의심형",
                "retrospective_onset_date": "",
                "strict_trigger_date": "2025-11-11",
                "gap_days": 0,
                "earliest_warning_date": "2025-11-10",
                "onset_method": "runtime_trigger_only",
                "site_event_history_flag": 0,
                "group_off_history_flag": 1,
                "subgroup_common_cause_history_flag": 0,
                "common_cause_history_flag": 1,
                "strict_trigger_proximal_common_cause_flag": 0,
                "secondary_window_qualified_count": 4,
                "subtype_promotion_blocker_detail_shadow": "group_off",
                "promotion_decision_bucket": "blocked_cluster_risk",
                "review_question_ko": "group off?",
            }
        ],
        [
            "review_packet_id",
            "site",
            "panel_id",
            "fault_family_hypothesis_shadow_ko",
            "fault_subtype_hypothesis_shadow_ko",
            "retrospective_onset_date",
            "strict_trigger_date",
            "gap_days",
            "earliest_warning_date",
            "onset_method",
            "site_event_history_flag",
            "group_off_history_flag",
            "subgroup_common_cause_history_flag",
            "common_cause_history_flag",
            "strict_trigger_proximal_common_cause_flag",
            "secondary_window_qualified_count",
            "subtype_promotion_blocker_detail_shadow",
            "promotion_decision_bucket",
            "review_question_ko",
        ],
    )

    backlog = root / "backlog.csv"
    write_csv(
        backlog,
        [
            {
                "backlog_case_id": "BR080-001",
                "family_key": "degradation_soiling_shadow",
                "family_label_ko": "열화·오염·음영 계열",
                "subtype_key": "progressive_soiling_or_degradation",
                "subtype_label_ko": "누적 오염·열화형",
                "recommended_next_artifact": "panel_day_engine_episode_truth_map_v1",
                "required_positive_evidence_axes": "duration and recurrence",
                "review_question_ko": "durable?",
            }
        ],
        [
            "backlog_case_id",
            "family_key",
            "family_label_ko",
            "subtype_key",
            "subtype_label_ko",
            "recommended_next_artifact",
            "required_positive_evidence_axes",
            "review_question_ko",
        ],
    )
    return {"episode": episode, "g1": g1, "shape": shape, "blocker": blocker, "backlog": backlog}


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research/prognostics/build_panel_day_engine_episode_truth_map_v1.py"

    with tempfile.TemporaryDirectory(prefix="episode_truth_map_smoke_") as tmpdir:
        fixture_root = Path(tmpdir) / "fixture"
        fixture_root.mkdir(parents=True, exist_ok=True)
        inputs = build_fixture(fixture_root)
        output_dir = Path(tmpdir) / "out"
        cmd = [
            sys.executable,
            str(script),
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--owner-branch",
            "BR-TEST-081",
            "--episode-input",
            str(inputs["episode"]),
            "--g1-input",
            str(inputs["g1"]),
            "--shape-input",
            str(inputs["shape"]),
            "--blocker-input",
            str(inputs["blocker"]),
            "--backlog-input",
            str(inputs["backlog"]),
        ]
        completed = run(cmd, repo_root)
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)

        map_df = pd.read_csv(output_dir / MAP_NAME, encoding="utf-8-sig")
        summary_df = pd.read_csv(output_dir / SUMMARY_NAME, encoding="utf-8-sig")
        action_df = pd.read_csv(output_dir / ACTION_NAME, encoding="utf-8-sig")
        payload = json.loads((output_dir / JSON_NAME).read_text(encoding="utf-8"))
        note_text = (output_dir / NOTE_NAME).read_text(encoding="utf-8")

        buckets = set(map_df["episode_truth_bucket"].astype(str))
        assert_true("long_gap_backdating_hold" in buckets, map_df.to_string())
        assert_true("durable_precursor_candidate_review" in buckets, map_df.to_string())
        assert_true("recovery_recurrence_observation" in buckets, map_df.to_string())
        assert_true("common_cause_or_group_episode_hold" in buckets, map_df.to_string())
        assert_true("episode_truth_requirement" in buckets, map_df.to_string())

        assert_true((map_df["episode_truth_status"] == "truth_pending").all(), map_df.to_string())
        assert_true(int(map_df["operator_facing_change_allowed"].sum()) == 0, map_df.to_string())
        assert_true(int(map_df["engine_patch_allowed"].sum()) == 0, map_df.to_string())
        assert_true(int(map_df["threshold_patch_allowed"].sum()) == 0, map_df.to_string())
        assert_true(payload["episode_truth_map_rows"] == len(map_df), payload)
        assert_true(payload["truth_status_counts"] == {"truth_pending": len(map_df)}, payload)
        assert_true(payload["missing_optional_input_count"] == 0, payload)
        assert_true(len(summary_df) >= 5, summary_df.to_string())
        assert_true(action_df["sequence"].tolist() == sorted(action_df["sequence"].tolist()), action_df.to_string())
        assert_true(action_df.iloc[0]["action_id"] == "ACT-001", action_df.to_string())
        assert_true("truth_pending" in note_text, note_text)

    print("smoke_test_panel_day_engine_episode_truth_map_v1.py: PASS")


if __name__ == "__main__":
    main()
