#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


AUDIT_NAME = "panel_day_engine_direction_assumption_audit_v1.csv"
SUMMARY_NAME = "panel_day_engine_direction_assumption_audit_summary_v1.csv"
ACTION_NAME = "panel_day_engine_direction_assumption_audit_action_queue_v1.csv"
NOTE_NAME = "panel_day_engine_direction_assumption_audit_note_v1.md"
JSON_NAME = "panel_day_engine_direction_assumption_audit_v1.json"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_br079(root: Path) -> None:
    write_csv(
        root / "panel_day_engine_algorithm_evolution_layer_map_v1.csv",
        [
            {
                "layer_id": f"L{i:02d}",
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
            }
            for i in range(1, 11)
        ],
    )
    write_csv(
        root / "panel_day_engine_algorithm_evolution_gap_audit_v1.csv",
        [
            {
                "gap_id": f"G{i:02d}",
                "priority": "P0" if i <= 4 else "P1",
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
            }
            for i in range(1, 8)
        ],
    )
    write_csv(
        root / "panel_day_engine_algorithm_evolution_action_queue_v1.csv",
        [
            {
                "action_id": f"ACT-{i:03d}",
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
            }
            for i in range(1, 7)
        ],
    )
    write_json(
        root / "panel_day_engine_algorithm_evolution_map_v1.json",
        {
            "layer_count": 10,
            "gap_count": 7,
            "p0_gap_count": 4,
            "action_count": 6,
            "operator_facing_change_allowed_sum": 0,
            "engine_patch_allowed_sum": 0,
            "threshold_patch_allowed_sum": 0,
            "recommended_next_branch": "panel_day_engine_subtype_truth_expansion_backlog_v1",
            "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        },
    )


def build_br080(root: Path) -> None:
    rows = []
    for i in range(1, 18):
        rows.append(
            {
                "backlog_case_id": f"BR080-{i:03d}",
                "truth_priority": "P0" if i <= 12 else "P1",
                "current_exact_truth_support_count": 0,
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
            }
        )
    write_csv(root / "panel_day_engine_subtype_truth_expansion_backlog_v1.csv", rows)
    write_json(
        root / "panel_day_engine_subtype_truth_expansion_backlog_v1.json",
        {
            "subtype_backlog_rows": 17,
            "p0_subtype_backlog_rows": 12,
            "current_exact_truth_support_sum": 0,
            "missing_optional_input_count": 0,
            "operator_facing_change_allowed_sum": 0,
            "engine_patch_allowed_sum": 0,
            "threshold_patch_allowed_sum": 0,
            "recommended_next_branch": "panel_day_engine_episode_truth_map_v1",
            "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        },
    )


def build_br081(root: Path) -> None:
    rows: list[dict[str, object]] = []

    def add(bucket: str, count: int, *, source: str = "br017_episode_shadow", common: int = 0) -> None:
        start = len(rows) + 1
        for i in range(start, start + count):
            rows.append(
                {
                    "episode_truth_case_id": f"BR081-EPS-{i:03d}",
                    "source_artifact": source,
                    "episode_truth_bucket": bucket,
                    "episode_truth_status": "truth_pending",
                    "common_cause_flag_sum": common,
                    "operator_facing_change_allowed": 0,
                    "engine_patch_allowed": 0,
                    "threshold_patch_allowed": 0,
                }
            )

    add("common_cause_or_group_episode_hold", 204, common=2)
    add("recovery_recurrence_observation", 12)
    add("long_gap_backdating_hold", 6, source="br017_episode_shadow", common=2)
    add("long_gap_backdating_hold", 6, source="br017_g1_longgap_cases", common=2)
    add("common_cause_or_group_episode_hold", 1, source="br017_g1_longgap_cases", common=1)
    add("durable_precursor_candidate_review", 7, common=0)
    add("episode_truth_requirement", 5)
    add("strict_anchor_sudden_review", 3)
    assert len(rows) == 244
    write_csv(root / "panel_day_engine_episode_truth_map_v1.csv", rows)
    write_json(
        root / "panel_day_engine_episode_truth_map_v1.json",
        {
            "episode_truth_map_rows": 244,
            "bucket_counts": {
                "common_cause_or_group_episode_hold": 205,
                "recovery_recurrence_observation": 12,
                "long_gap_backdating_hold": 12,
                "durable_precursor_candidate_review": 7,
                "episode_truth_requirement": 5,
                "strict_anchor_sudden_review": 3,
            },
            "truth_status_counts": {"truth_pending": 244},
            "missing_optional_input_count": 0,
            "operator_facing_change_allowed_sum": 0,
            "engine_patch_allowed_sum": 0,
            "threshold_patch_allowed_sum": 0,
            "recommended_next_branch": "panel_day_engine_episode_truth_review_packet_v1",
            "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        },
    )


def build_br082(root: Path) -> None:
    rows = []
    for i in range(1, 7):
        rows.append(
            {
                "review_packet_id": f"BR082-EPR-{i:03d}",
                "review_track": "long_gap_backdating_review",
                "review_priority": "P0",
                "source_lens_count": 2,
                "source_artifacts": "br017_episode_shadow; br017_g1_longgap_cases",
                "reviewer_truth_label": "",
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
            }
        )
    for i in range(7, 10):
        rows.append(
            {
                "review_packet_id": f"BR082-EPR-{i:03d}",
                "review_track": "strict_sudden_prior_episode_review",
                "review_priority": "P0",
                "source_lens_count": 1,
                "source_artifacts": "br017_episode_shadow",
                "reviewer_truth_label": "",
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
            }
        )
    for i in range(10, 17):
        rows.append(
            {
                "review_packet_id": f"BR082-EPR-{i:03d}",
                "review_track": "durable_precursor_review",
                "review_priority": "P1",
                "source_lens_count": 1,
                "source_artifacts": "br017_episode_shadow",
                "reviewer_truth_label": "",
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
            }
        )
    write_csv(root / "panel_day_engine_episode_truth_review_packet_v1.csv", rows)
    write_json(
        root / "panel_day_engine_episode_truth_review_packet_v1.json",
        {
            "input_episode_map_rows": 244,
            "selected_source_lens_rows": 22,
            "review_packet_rows": 16,
            "collapsed_duplicate_lens_count": 6,
            "review_track_counts": {
                "durable_precursor_review": 7,
                "long_gap_backdating_review": 6,
                "strict_sudden_prior_episode_review": 3,
            },
            "review_priority_counts": {"P0": 9, "P1": 7},
            "reviewer_truth_label_assigned_count": 0,
            "operator_facing_change_allowed_sum": 0,
            "engine_patch_allowed_sum": 0,
            "threshold_patch_allowed_sum": 0,
            "recommended_next_branch": "panel_day_engine_reviewed_episode_truth_rows_v1",
            "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        },
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research/prognostics/build_panel_day_engine_direction_assumption_audit_v1.py"
    with tempfile.TemporaryDirectory(prefix="direction_assumption_audit_smoke_") as tmpdir:
        fixture = Path(tmpdir) / "fixture"
        br079 = fixture / "br079"
        br080 = fixture / "br080"
        br081 = fixture / "br081"
        br082 = fixture / "br082"
        build_br079(br079)
        build_br080(br080)
        build_br081(br081)
        build_br082(br082)
        output_dir = Path(tmpdir) / "out"
        completed = run(
            [
                sys.executable,
                str(script),
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(output_dir),
                "--owner-branch",
                "BR-TEST-083",
                "--br079-root",
                str(br079),
                "--br080-root",
                str(br080),
                "--br081-root",
                str(br081),
                "--br082-root",
                str(br082),
            ],
            repo_root,
        )
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)

        audit = pd.read_csv(output_dir / AUDIT_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(output_dir / SUMMARY_NAME, encoding="utf-8-sig")
        action = pd.read_csv(output_dir / ACTION_NAME, encoding="utf-8-sig")
        payload = json.loads((output_dir / JSON_NAME).read_text(encoding="utf-8"))
        note_text = (output_dir / NOTE_NAME).read_text(encoding="utf-8")

        assert_true(len(audit) >= 35, audit.to_string())
        assert_true((audit["audit_status"] == "PASS").all(), audit.to_string())
        assert_true(payload["fail_count"] == 0, payload)
        assert_true(payload["p0_fail_count"] == 0, payload)
        assert_true(payload["operator_facing_change_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["recommended_next_branch"] == "panel_day_engine_reviewed_episode_truth_rows_v1", payload)
        assert_true("g1_longgap_lens_preserved" in set(audit["check_name"]), audit.to_string())
        assert_true("source_lens_collapse_counts" in set(audit["check_name"]), audit.to_string())
        assert_true(len(summary) >= 8, summary.to_string())
        assert_true(action["sequence"].tolist() == sorted(action["sequence"].tolist()), action.to_string())
        assert_true(action.iloc[0]["action_id"] == "ACT-001", action.to_string())
        assert_true("BR-076" in note_text, note_text)
        assert_true(payload["input_manifest"] == "", payload)
        assert_true(payload["br079_root_source"] == "explicit_cli", payload)
        assert_true(payload["br080_root_source"] == "explicit_cli", payload)
        assert_true(payload["br081_root_source"] == "explicit_cli", payload)
        assert_true(payload["br082_root_source"] == "explicit_cli", payload)

        manifest_path = Path(tmpdir) / "direction_assumption_inputs.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "inputs": {
                        "br079_root": str(br079),
                        "br080_root": str(br080),
                        "br081_root": str(br081),
                        "br082_root": str(br082),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_out = Path(tmpdir) / "manifest_out"
        manifest_completed = run(
            [
                sys.executable,
                str(script),
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(manifest_out),
                "--owner-branch",
                "BR-TEST-083",
                "--input-manifest",
                str(manifest_path),
            ],
            repo_root,
        )
        assert_true(manifest_completed.returncode == 0, manifest_completed.stderr or manifest_completed.stdout)
        manifest_payload = json.loads((manifest_out / JSON_NAME).read_text(encoding="utf-8"))
        assert_true(manifest_payload["total_checks"] == payload["total_checks"], manifest_payload)
        assert_true(manifest_payload["fail_count"] == 0, manifest_payload)
        assert_true(manifest_payload["input_manifest"] == str(manifest_path), manifest_payload)
        assert_true(manifest_payload["br079_root_source"] == "input_manifest", manifest_payload)
        assert_true(manifest_payload["br080_root_source"] == "input_manifest", manifest_payload)
        assert_true(manifest_payload["br081_root_source"] == "input_manifest", manifest_payload)
        assert_true(manifest_payload["br082_root_source"] == "input_manifest", manifest_payload)

        bad_manifest_path = Path(tmpdir) / "bad_direction_assumption_inputs.json"
        bad_manifest_path.write_text(
            json.dumps(
                {
                    "inputs": {
                        "br079_root": str(Path(tmpdir) / "missing_br079"),
                        "br080_root": str(Path(tmpdir) / "missing_br080"),
                        "br081_root": str(Path(tmpdir) / "missing_br081"),
                        "br082_root": str(Path(tmpdir) / "missing_br082"),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_out = Path(tmpdir) / "override_out"
        override_completed = run(
            [
                sys.executable,
                str(script),
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(override_out),
                "--owner-branch",
                "BR-TEST-083",
                "--br079-root",
                str(br079),
                "--br080-root",
                str(br080),
                "--br081-root",
                str(br081),
                "--br082-root",
                str(br082),
                "--input-manifest",
                str(bad_manifest_path),
            ],
            repo_root,
        )
        assert_true(override_completed.returncode == 0, override_completed.stderr or override_completed.stdout)
        override_payload = json.loads((override_out / JSON_NAME).read_text(encoding="utf-8"))
        assert_true(override_payload["br079_root_source"] == "explicit_cli", override_payload)
        assert_true(override_payload["br080_root_source"] == "explicit_cli", override_payload)
        assert_true(override_payload["br081_root_source"] == "explicit_cli", override_payload)
        assert_true(override_payload["br082_root_source"] == "explicit_cli", override_payload)

        missing_key_manifest_path = Path(tmpdir) / "missing_key_direction_assumption_inputs.json"
        missing_key_manifest_path.write_text(
            json.dumps(
                {
                    "inputs": {
                        "br079_root": str(br079),
                        "br080_root": str(br080),
                        "br081_root": str(br081),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        missing_key_completed = run(
            [
                sys.executable,
                str(script),
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(Path(tmpdir) / "missing_key_out"),
                "--owner-branch",
                "BR-TEST-083",
                "--input-manifest",
                str(missing_key_manifest_path),
            ],
            repo_root,
        )
        assert_true(missing_key_completed.returncode != 0, missing_key_completed.stdout)
        assert_true("missing `br082_root`" in missing_key_completed.stderr, missing_key_completed.stderr)

    print("smoke_test_panel_day_engine_direction_assumption_audit_v1.py: PASS")


if __name__ == "__main__":
    main()
