#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


CANDIDATE_COLUMNS = [
    "search_candidate_row_id",
    "site",
    "panel_id",
    "hard_episode_anchor_date",
    "onset_candidate_date",
    "gap_days",
    "candidate_tier",
    "candidate_tier_rank",
    "known_review_role",
    "truth_search_action",
    "candidate_priority",
    "manual_review_ready",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "window_day_rows",
    "window_signal_days",
    "event_A_days",
    "low_mid_days",
    "voltage_low_current_ok_days",
    "current_low_voltage_ok_days",
    "both_low_vi_days",
    "hard_anchor_days",
    "common_cause_days",
    "data_bad_days",
    "median_signal_mid_ratio",
    "median_signal_mid_v_ratio",
    "median_signal_mid_i_ratio",
    "min_window_mid_ratio",
    "median_signal_dtw_dist",
    "max_window_dtw_dist",
    "max_window_co_drop_frac",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def candidate(
    row_id: str,
    panel_id: str,
    anchor: str,
    onset: str,
    gap: int,
    tier: str,
    tier_rank: int,
    known_role: str,
    manual_ready: int,
    vlow_days: int,
) -> dict[str, object]:
    return {
        "search_candidate_row_id": row_id,
        "site": "fixture",
        "panel_id": panel_id,
        "hard_episode_anchor_date": anchor,
        "onset_candidate_date": onset,
        "gap_days": gap,
        "candidate_tier": tier,
        "candidate_tier_rank": tier_rank,
        "known_review_role": known_role,
        "truth_search_action": "review_new_candidate_before_truth_use",
        "candidate_priority": "P0_independent_confirmation_review" if tier_rank >= 3 else "P1_shape_confirmation_review",
        "manual_review_ready": manual_ready,
        "positive_truth_candidate_approved": 0,
        "threshold_tuning_approved": 0,
        "window_day_rows": gap + 1,
        "window_signal_days": gap,
        "event_A_days": gap,
        "low_mid_days": gap,
        "voltage_low_current_ok_days": vlow_days,
        "current_low_voltage_ok_days": 0,
        "both_low_vi_days": 0,
        "hard_anchor_days": 1,
        "common_cause_days": 0,
        "data_bad_days": 0,
        "median_signal_mid_ratio": 0.65,
        "median_signal_mid_v_ratio": 0.66,
        "median_signal_mid_i_ratio": 0.97,
        "min_window_mid_ratio": 0.61,
        "median_signal_dtw_dist": 1.2,
        "max_window_dtw_dist": 3.4,
        "max_window_co_drop_frac": 0.1,
        "operator_facing_change_allowed": 0,
        "engine_patch_allowed": 0,
        "threshold_patch_allowed": 0,
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        candidate_input = tmp_root / "candidates.csv"
        output_dir = tmp_root / "out"
        rows = [
            candidate("BR092-001", "rootA.1.0", "2025-03-01", "2025-02-01", 28, "strong_b089_like", 3, "new_search_candidate", 1, 28),
            candidate("BR092-002", "rootA.1.0", "2025-03-10", "2025-02-03", 35, "strong_b089_like", 3, "new_search_candidate", 1, 32),
            candidate("BR092-003", "rootA.2.0", "2025-04-01", "2025-03-01", 31, "voltage_preserved_10d", 2, "new_search_candidate", 1, 12),
            candidate("BR092-004", "rootA.9.9", "2025-05-01", "2025-01-01", 120, "voltage_preserved_10d", 2, "known_negative_counterexample", 0, 12),
            candidate("BR092-005", "rootB.1.0", "2025-06-01", "2025-05-20", 12, "voltage_preserved_2d_review", 1, "new_search_candidate", 0, 5),
        ]
        pd.DataFrame(rows).reindex(columns=CANDIDATE_COLUMNS).to_csv(candidate_input, index=False, encoding="utf-8-sig")

        cmd = [
            sys.executable,
            "research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_packet_v1.py",
            "--repo-root",
            str(repo_root),
            "--candidate-input",
            str(candidate_input),
            "--output-dir",
            str(output_dir),
        ]
        proc = run(cmd, repo_root)
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["source_candidate_map_rows"] == 3, payload)
        assert_true(payload["confirmation_packet_rows"] == 2, payload)
        assert_true(payload["confirmation_family_rows"] == 1, payload)
        assert_true(payload["counterexample_risk_packet_rows"] == 2, payload)
        assert_true(payload["counterexample_risk_families"] == 1, payload)
        assert_true(payload["positive_truth_candidate_approved_sum"] == 0, payload)
        assert_true(payload["threshold_tuning_approved_sum"] == 0, payload)

        artifact_payload = json.loads(
            (output_dir / "panel_day_engine_voltage_preserved_confirmation_packet_v1.json").read_text(
                encoding="utf-8"
            )
        )
        note = (output_dir / "panel_day_engine_voltage_preserved_confirmation_note_v1.md").read_text(
            encoding="utf-8"
        )
        assert_true(
            artifact_payload["input_resolution_sources"]["candidate_input"] == "explicit_cli",
            artifact_payload,
        )
        assert_true("evidence input manifest: `not provided`" in note, note)
        assert_true("`candidate_input`: `explicit_cli`" in note, note)

        packet = pd.read_csv(output_dir / "panel_day_engine_voltage_preserved_confirmation_packet_v1.csv")
        family = pd.read_csv(output_dir / "panel_day_engine_voltage_preserved_confirmation_family_summary_v1.csv")
        candidate_map = pd.read_csv(output_dir / "panel_day_engine_voltage_preserved_confirmation_candidate_map_v1.csv")
        assert_true(set(packet["review_priority"]) == {
            "P0_multi_anchor_strong_voltage_preserved",
            "P1_repeated_voltage_preserved_10d",
        }, packet)
        assert_true(int(packet["engine_patch_allowed"].sum()) == 0, packet)
        assert_true(int(packet["counterexample_risk_flag"].sum()) == 2, packet)
        assert_true(int(family["source_candidate_rows"].sum()) == 3, family)
        assert_true(len(candidate_map) == 3, candidate_map)

        manifest_path = tmp_root / "confirmation_inputs.json"
        manifest_path.write_text(
            json.dumps({"inputs": {"candidate_input": str(candidate_input)}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest_out = tmp_root / "manifest_out"
        manifest = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_packet_v1.py",
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(manifest_path),
                "--output-dir",
                str(manifest_out),
            ],
            repo_root,
        )
        assert_true(manifest.returncode == 0, manifest.stderr or manifest.stdout)
        manifest_packet = pd.read_csv(
            manifest_out / "panel_day_engine_voltage_preserved_confirmation_packet_v1.csv",
            encoding="utf-8-sig",
        )
        manifest_payload = json.loads(
            (manifest_out / "panel_day_engine_voltage_preserved_confirmation_packet_v1.json").read_text(
                encoding="utf-8"
            )
        )
        manifest_note = (manifest_out / "panel_day_engine_voltage_preserved_confirmation_note_v1.md").read_text(
            encoding="utf-8"
        )
        assert_true(manifest_payload["confirmation_packet_rows"] == payload["confirmation_packet_rows"], manifest_payload)
        assert_true(
            manifest_packet["review_priority"].tolist() == packet["review_priority"].tolist(),
            manifest_packet.to_string(),
        )
        assert_true(
            manifest_payload["input_resolution_sources"]["candidate_input"] == "input_manifest",
            manifest_payload,
        )
        assert_true(f"evidence input manifest: `{manifest_path}`" in manifest_note, manifest_note)
        assert_true("`candidate_input`: `input_manifest`" in manifest_note, manifest_note)

        bad_manifest_path = tmp_root / "bad_confirmation_inputs.json"
        bad_manifest_path.write_text(
            json.dumps({"inputs": {"candidate_input": str(tmp_root / "missing_candidates.csv")}}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        override_out = tmp_root / "override_out"
        override = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_packet_v1.py",
                "--repo-root",
                str(repo_root),
                "--candidate-input",
                str(candidate_input),
                "--input-manifest",
                str(bad_manifest_path),
                "--output-dir",
                str(override_out),
            ],
            repo_root,
        )
        assert_true(override.returncode == 0, override.stderr or override.stdout)
        override_payload = json.loads(
            (override_out / "panel_day_engine_voltage_preserved_confirmation_packet_v1.json").read_text(
                encoding="utf-8"
            )
        )
        assert_true(
            override_payload["input_resolution_sources"]["candidate_input"] == "explicit_cli",
            override_payload,
        )

        missing_key_manifest_path = tmp_root / "missing_key_confirmation_inputs.json"
        missing_key_manifest_path.write_text(
            json.dumps({"inputs": {}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        missing_key = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_packet_v1.py",
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(missing_key_manifest_path),
                "--output-dir",
                str(tmp_root / "missing_key_out"),
            ],
            repo_root,
        )
        assert_true(missing_key.returncode != 0, "missing-key manifest unexpectedly passed")
        assert_true("missing `candidate_input`" in (missing_key.stderr + missing_key.stdout), missing_key.stderr)
        print(json.dumps({"smoke": "ok", "packet_rows": int(len(packet))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
