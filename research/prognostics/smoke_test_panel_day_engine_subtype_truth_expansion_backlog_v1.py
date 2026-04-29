#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


BACKLOG_NAME = "panel_day_engine_subtype_truth_expansion_backlog_v1.csv"
SUMMARY_NAME = "panel_day_engine_subtype_truth_expansion_backlog_summary_v1.csv"
ACTION_NAME = "panel_day_engine_subtype_truth_expansion_action_queue_v1.csv"
NOTE_NAME = "panel_day_engine_subtype_truth_expansion_note_v1.md"
JSON_NAME = "panel_day_engine_subtype_truth_expansion_backlog_v1.json"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture(root: Path) -> dict[str, Path]:
    docs = root / "docs"
    tmp = root / "tmp"
    docs.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)

    subtype_map = docs / "subtype_map.csv"
    write_csv(
        subtype_map,
        [
            {
                "family_key": "degradation_soiling_shadow",
                "family_label_ko": "열화·오염·음영 계열",
                "subtype_key": "progressive_soiling_or_degradation",
                "subtype_label_ko": "누적 오염·열화형",
                "primary_signature_ko": "여러 날 누적 저하",
                "secondary_signature_ko": "",
                "negative_signature_ko": "",
                "minimum_evidence_shadow_ko": "2일 이상 저하",
                "recommended_shadow_action": "shadow_subtype_candidate",
                "notes_ko": "",
            },
            {
                "family_key": "open_connection_partial",
                "family_label_ko": "접속 불량·부분 개방 계열",
                "subtype_key": "partial_open_circuit",
                "subtype_label_ko": "부분 개방 진행형",
                "primary_signature_ko": "전압축 hard signal",
                "secondary_signature_ko": "",
                "negative_signature_ko": "",
                "minimum_evidence_shadow_ko": "VI shape + recurrence",
                "recommended_shadow_action": "shadow_subtype_candidate",
                "notes_ko": "",
            },
            {
                "family_key": "external_common_cause",
                "family_label_ko": "외부계통·공통원인 계열",
                "subtype_key": "root_mppt_group_common",
                "subtype_label_ko": "root·MPPT group 공통 episode형",
                "primary_signature_ko": "group synchrony",
                "secondary_signature_ko": "",
                "negative_signature_ko": "",
                "minimum_evidence_shadow_ko": "official bridge",
                "recommended_shadow_action": "block_individual_precursor",
                "notes_ko": "",
            },
            {
                "family_key": "strict_anchor_sudden",
                "family_label_ko": "strict trigger anchored sudden fault",
                "subtype_key": "strict_trigger_sudden_fault",
                "subtype_label_ko": "strict 근접 급작형",
                "primary_signature_ko": "strict trigger first",
                "secondary_signature_ko": "",
                "negative_signature_ko": "",
                "minimum_evidence_shadow_ko": "prior normal review",
                "recommended_shadow_action": "no_precursor_promotion",
                "notes_ko": "",
            },
        ],
        [
            "family_key",
            "family_label_ko",
            "subtype_key",
            "subtype_label_ko",
            "primary_signature_ko",
            "secondary_signature_ko",
            "negative_signature_ko",
            "minimum_evidence_shadow_ko",
            "recommended_shadow_action",
            "notes_ko",
        ],
    )

    atlas = docs / "morphology_atlas.csv"
    write_csv(
        atlas,
        [
            {"family_key": "degradation_soiling_shadow", "family_label_ko": "열화·오염·음영 계열"},
            {"family_key": "open_connection_partial", "family_label_ko": "접속 불량·부분 개방 계열"},
            {"family_key": "external_common_cause", "family_label_ko": "외부계통·공통원인 계열"},
            {"family_key": "strict_anchor_sudden", "family_label_ko": "strict trigger anchored sudden fault"},
        ],
        ["family_key", "family_label_ko"],
    )

    gap = docs / "br079_gap.csv"
    write_csv(
        gap,
        [
            {
                "gap_id": "GAP-001",
                "gap_family": "fault_subtype_truth",
                "priority": "P0",
                "recommended_artifact": "panel_day_engine_subtype_truth_expansion_backlog_v1",
            }
        ],
        ["gap_id", "gap_family", "priority", "recommended_artifact"],
    )

    shadow = docs / "shadow_summary.csv"
    write_csv(
        shadow,
        [
            {
                "fault_family_hypothesis_shadow_ko": "접속 불량·부분 개방 계열",
                "fault_subtype_hypothesis_shadow_ko": "부분 개방 진행형",
                "subtype_confidence_shadow": "hold",
                "panel_count": 2,
            }
        ],
        [
            "fault_family_hypothesis_shadow_ko",
            "fault_subtype_hypothesis_shadow_ko",
            "subtype_confidence_shadow",
            "panel_count",
        ],
    )

    packet = tmp / "packet.csv"
    write_csv(
        packet,
        [
            {
                "candidate_family_track": "open_connection_partial",
                "candidate_family_label_ko": "접속 불량·부분 개방 계열",
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
            },
            {
                "candidate_family_track": "external_common_cause",
                "candidate_family_label_ko": "외부계통·공통원인 계열",
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
            },
        ],
        ["candidate_family_track", "candidate_family_label_ko", "operator_promotion_allowed_flag", "engine_patch_candidate_flag"],
    )

    shape = tmp / "shape.csv"
    write_csv(
        shape,
        [
            {
                "candidate_family_track": "open_connection_or_measurement_voltage_axis",
                "family_shape_judgment_bucket": "voltage_dominant_hard_signal_review",
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
            }
        ],
        ["candidate_family_track", "family_shape_judgment_bucket", "operator_promotion_allowed_flag", "engine_patch_candidate_flag"],
    )

    confirmation = tmp / "confirmation.csv"
    write_csv(
        confirmation,
        [
            {
                "confirmation_bucket": "raw_supported_confirmation_gap_hold",
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
                "threshold_patch_allowed_flag": 0,
            }
        ],
        ["confirmation_bucket", "operator_promotion_allowed_flag", "engine_patch_candidate_flag", "threshold_patch_allowed_flag"],
    )

    common = tmp / "common.csv"
    write_csv(
        common,
        [
            {
                "candidate_reservoir_flag": 1,
                "structural_blocker_flag": 0,
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
                "threshold_patch_allowed_flag": 0,
            },
            {
                "candidate_reservoir_flag": 0,
                "structural_blocker_flag": 1,
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
                "threshold_patch_allowed_flag": 0,
            },
        ],
        [
            "candidate_reservoir_flag",
            "structural_blocker_flag",
            "operator_promotion_allowed_flag",
            "engine_patch_candidate_flag",
            "threshold_patch_allowed_flag",
        ],
    )

    return {
        "subtype": subtype_map,
        "atlas": atlas,
        "gap": gap,
        "shadow": shadow,
        "packet": packet,
        "shape": shape,
        "confirmation": confirmation,
        "common": common,
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research/prognostics/build_panel_day_engine_subtype_truth_expansion_backlog_v1.py"

    with tempfile.TemporaryDirectory(prefix="subtype_truth_expansion_smoke_") as tmpdir:
        fixture_root = Path(tmpdir) / "fixture"
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
            "BR-TEST-080",
            "--subtype-map",
            str(inputs["subtype"]),
            "--morphology-atlas",
            str(inputs["atlas"]),
            "--br079-gap-input",
            str(inputs["gap"]),
            "--shadow-summary-input",
            str(inputs["shadow"]),
            "--candidate-packet-input",
            str(inputs["packet"]),
            "--shape-review-input",
            str(inputs["shape"]),
            "--physical-confirmation-input",
            str(inputs["confirmation"]),
            "--common-cause-search-input",
            str(inputs["common"]),
        ]
        completed = run(cmd, repo_root)
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)

        backlog_df = pd.read_csv(output_dir / BACKLOG_NAME, encoding="utf-8-sig")
        summary_df = pd.read_csv(output_dir / SUMMARY_NAME, encoding="utf-8-sig")
        action_df = pd.read_csv(output_dir / ACTION_NAME, encoding="utf-8-sig")
        payload = json.loads((output_dir / JSON_NAME).read_text(encoding="utf-8"))
        note_text = (output_dir / NOTE_NAME).read_text(encoding="utf-8")

        assert_true(len(backlog_df) == 4, backlog_df.to_string())
        assert_true(payload["subtype_backlog_rows"] == 4, payload)
        assert_true(payload["current_exact_truth_support_sum"] == 0, payload)
        assert_true(payload["missing_optional_input_count"] == 0, payload)
        assert_true((backlog_df["owner_branch"] == "BR-TEST-080").all(), backlog_df.to_string())
        assert_true(int(backlog_df["operator_facing_change_allowed"].sum()) == 0, backlog_df.to_string())
        assert_true(int(backlog_df["engine_patch_allowed"].sum()) == 0, backlog_df.to_string())
        assert_true(int(backlog_df["threshold_patch_allowed"].sum()) == 0, backlog_df.to_string())

        open_row = backlog_df.loc[backlog_df["family_key"].eq("open_connection_partial")].iloc[0]
        assert_true(open_row["truth_priority"] == "P0", open_row.to_string())
        assert_true(int(open_row["current_shadow_panel_count"]) == 2, open_row.to_string())
        assert_true(int(open_row["current_candidate_pool_count"]) == 1, open_row.to_string())
        assert_true(int(open_row["current_physical_confirmation_gap_count"]) == 1, open_row.to_string())

        common_row = backlog_df.loc[backlog_df["family_key"].eq("external_common_cause")].iloc[0]
        assert_true(common_row["truth_target_role"] == "common_cause_bridge_truth", common_row.to_string())
        assert_true(int(common_row["current_common_cause_reservoir_count"]) == 2, common_row.to_string())

        strict_row = backlog_df.loc[backlog_df["family_key"].eq("strict_anchor_sudden")].iloc[0]
        assert_true(strict_row["recommended_next_artifact"] == "panel_day_engine_episode_truth_map_v1", strict_row.to_string())

        assert_true(len(summary_df) == 4, summary_df.to_string())
        assert_true(action_df["sequence"].tolist() == sorted(action_df["sequence"].tolist()), action_df.to_string())
        assert_true(action_df.iloc[0]["action_id"] == "ACT-001", action_df.to_string())
        assert_true("current_exact_truth_support_count" in note_text, note_text)
        assert_true(payload["input_manifest"] == "", payload)
        assert_true(payload["br079_gap_input_source"] == "explicit_cli", payload)
        assert_true(payload["candidate_packet_input_source"] == "explicit_cli", payload)
        assert_true(payload["shape_review_input_source"] == "explicit_cli", payload)
        assert_true(payload["physical_confirmation_input_source"] == "explicit_cli", payload)
        assert_true(payload["common_cause_search_input_source"] == "explicit_cli", payload)

        manifest_path = Path(tmpdir) / "subtype_truth_expansion_inputs.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "inputs": {
                        "br079_gap_input": str(inputs["gap"]),
                        "candidate_packet_input": str(inputs["packet"]),
                        "shape_review_input": str(inputs["shape"]),
                        "physical_confirmation_input": str(inputs["confirmation"]),
                        "common_cause_search_input": str(inputs["common"]),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_out = Path(tmpdir) / "manifest_out"
        manifest_cmd = [
            sys.executable,
            str(script),
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(manifest_out),
            "--owner-branch",
            "BR-TEST-080",
            "--subtype-map",
            str(inputs["subtype"]),
            "--morphology-atlas",
            str(inputs["atlas"]),
            "--shadow-summary-input",
            str(inputs["shadow"]),
            "--input-manifest",
            str(manifest_path),
        ]
        manifest_completed = run(manifest_cmd, repo_root)
        assert_true(manifest_completed.returncode == 0, manifest_completed.stderr or manifest_completed.stdout)
        manifest_payload = json.loads((manifest_out / JSON_NAME).read_text(encoding="utf-8"))
        assert_true(manifest_payload["subtype_backlog_rows"] == payload["subtype_backlog_rows"], manifest_payload)
        assert_true(manifest_payload["current_exact_truth_support_sum"] == payload["current_exact_truth_support_sum"], manifest_payload)
        assert_true(manifest_payload["input_manifest"] == str(manifest_path), manifest_payload)
        assert_true(manifest_payload["br079_gap_input_source"] == "input_manifest", manifest_payload)
        assert_true(manifest_payload["candidate_packet_input_source"] == "input_manifest", manifest_payload)
        assert_true(manifest_payload["shape_review_input_source"] == "input_manifest", manifest_payload)
        assert_true(manifest_payload["physical_confirmation_input_source"] == "input_manifest", manifest_payload)
        assert_true(manifest_payload["common_cause_search_input_source"] == "input_manifest", manifest_payload)

        bad_manifest_path = Path(tmpdir) / "bad_subtype_truth_expansion_inputs.json"
        bad_manifest_path.write_text(
            json.dumps(
                {
                    "inputs": {
                        "br079_gap_input": str(Path(tmpdir) / "missing_gap.csv"),
                        "candidate_packet_input": str(Path(tmpdir) / "missing_packet.csv"),
                        "shape_review_input": str(Path(tmpdir) / "missing_shape.csv"),
                        "physical_confirmation_input": str(Path(tmpdir) / "missing_confirmation.csv"),
                        "common_cause_search_input": str(Path(tmpdir) / "missing_common.csv"),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_out = Path(tmpdir) / "override_out"
        override_cmd = [arg if arg != str(output_dir) else str(override_out) for arg in cmd]
        override_cmd.extend(["--input-manifest", str(bad_manifest_path)])
        override_completed = run(override_cmd, repo_root)
        assert_true(override_completed.returncode == 0, override_completed.stderr or override_completed.stdout)
        override_payload = json.loads((override_out / JSON_NAME).read_text(encoding="utf-8"))
        assert_true(override_payload["br079_gap_input_source"] == "explicit_cli", override_payload)
        assert_true(override_payload["candidate_packet_input_source"] == "explicit_cli", override_payload)
        assert_true(override_payload["shape_review_input_source"] == "explicit_cli", override_payload)
        assert_true(override_payload["physical_confirmation_input_source"] == "explicit_cli", override_payload)
        assert_true(override_payload["common_cause_search_input_source"] == "explicit_cli", override_payload)

        missing_key_manifest_path = Path(tmpdir) / "missing_key_subtype_truth_expansion_inputs.json"
        missing_key_manifest_path.write_text(
            json.dumps(
                {
                    "inputs": {
                        "br079_gap_input": str(inputs["gap"]),
                        "candidate_packet_input": str(inputs["packet"]),
                        "shape_review_input": str(inputs["shape"]),
                        "physical_confirmation_input": str(inputs["confirmation"]),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        missing_key_cmd = [
            sys.executable,
            str(script),
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(Path(tmpdir) / "missing_key_out"),
            "--owner-branch",
            "BR-TEST-080",
            "--subtype-map",
            str(inputs["subtype"]),
            "--morphology-atlas",
            str(inputs["atlas"]),
            "--shadow-summary-input",
            str(inputs["shadow"]),
            "--input-manifest",
            str(missing_key_manifest_path),
        ]
        missing_key_completed = run(missing_key_cmd, repo_root)
        assert_true(missing_key_completed.returncode != 0, missing_key_completed.stdout)
        assert_true("missing `common_cause_search_input`" in missing_key_completed.stderr, missing_key_completed.stderr)

    print("smoke_test_panel_day_engine_subtype_truth_expansion_backlog_v1.py: PASS")


if __name__ == "__main__":
    main()
