#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


PACKET_COLUMNS = [
    "confirmation_packet_row_id",
    "confirmation_family_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "review_priority",
    "confirmation_status",
    "representative_candidate_row_id",
    "representative_candidate_tier",
    "representative_anchor_date",
    "representative_onset_date",
    "representative_gap_days",
    "candidate_rows_for_panel",
    "unique_anchor_dates_for_panel",
    "min_gap_days_for_panel",
    "median_gap_days_for_panel",
    "max_gap_days_for_panel",
    "max_candidate_tier_rank_for_panel",
    "max_voltage_low_current_ok_days_for_panel",
    "max_event_A_days_for_panel",
    "max_low_mid_days_for_panel",
    "same_root_known_positive_seed_count",
    "same_root_known_negative_overlap_count",
    "same_root_known_hold_overlap_count",
    "same_panel_known_positive_seed_count",
    "same_panel_known_negative_overlap_count",
    "counterexample_risk_flag",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def packet_row(
    row_id: str,
    family_id: str,
    panel_id: str,
    review_priority: str,
    candidate_row: str,
    gap: int,
    candidate_rows: int,
    anchors: int,
    risk: int,
) -> dict[str, object]:
    root_id = panel_id.split(".")[0]
    panel_group_key = ".".join(panel_id.split(".")[:2])
    return {
        "confirmation_packet_row_id": row_id,
        "confirmation_family_id": family_id,
        "site": "fixture",
        "root_id": root_id,
        "panel_group_key": panel_group_key,
        "panel_id": panel_id,
        "review_priority": review_priority,
        "confirmation_status": "needs_independent_confirmation",
        "representative_candidate_row_id": candidate_row,
        "representative_candidate_tier": "strong_b089_like",
        "representative_anchor_date": "2025-07-20",
        "representative_onset_date": "2025-03-23",
        "representative_gap_days": gap,
        "candidate_rows_for_panel": candidate_rows,
        "unique_anchor_dates_for_panel": anchors,
        "min_gap_days_for_panel": max(1, gap - 3),
        "median_gap_days_for_panel": float(gap),
        "max_gap_days_for_panel": gap + 3,
        "max_candidate_tier_rank_for_panel": 3 if review_priority.startswith("P0") else 2,
        "max_voltage_low_current_ok_days_for_panel": 10,
        "max_event_A_days_for_panel": 8,
        "max_low_mid_days_for_panel": 7,
        "same_root_known_positive_seed_count": 0,
        "same_root_known_negative_overlap_count": risk,
        "same_root_known_hold_overlap_count": 0,
        "same_panel_known_positive_seed_count": 0,
        "same_panel_known_negative_overlap_count": 0,
        "counterexample_risk_flag": risk,
        "positive_truth_candidate_approved": 0,
        "threshold_tuning_approved": 0,
        "operator_facing_change_allowed": 0,
        "engine_patch_allowed": 0,
        "threshold_patch_allowed": 0,
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        confirmation_dir = tmp_root / "confirmation"
        output_dir = tmp_root / "out"
        confirmation_dir.mkdir(parents=True)
        packet_input = confirmation_dir / "panel_day_engine_voltage_preserved_confirmation_packet_v1.csv"
        rows = [
            packet_row(
                "BR093-VPCP-001",
                "BR093-VPCF-001",
                "rootA.1.0",
                "P0_multi_anchor_strong_voltage_preserved",
                "BR092-VPPS-001",
                55,
                2,
                2,
                0,
            ),
            packet_row(
                "BR093-VPCP-002",
                "BR093-VPCF-002",
                "rootB.1.0",
                "P0_single_anchor_strong_voltage_preserved",
                "BR092-VPPS-002",
                119,
                1,
                1,
                1,
            ),
            packet_row(
                "BR093-VPCP-003",
                "BR093-VPCF-003",
                "rootC.1.0",
                "P1_repeated_voltage_preserved_10d",
                "BR092-VPPS-003",
                21,
                3,
                3,
                0,
            ),
        ]
        pd.DataFrame(rows).reindex(columns=PACKET_COLUMNS).to_csv(
            packet_input, index=False, encoding="utf-8-sig"
        )

        cmd = [
            sys.executable,
            "research/prognostics/build_panel_day_engine_voltage_preserved_evidence_request_packet_v1.py",
            "--repo-root",
            str(repo_root),
            "--confirmation-dir",
            str(confirmation_dir),
            "--output-dir",
            str(output_dir),
        ]
        proc = run(cmd, repo_root)
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["evidence_request_rows"] == 3, payload)
        assert_true(payload["checklist_rows"] == 16, payload)
        assert_true(payload["counterexample_risk_request_rows"] == 1, payload)
        assert_true(payload["raw_waveform_independent_confirmation_rows"] == 0, payload)
        assert_true(payload["evidence_ready_for_truth_use_sum"] == 0, payload)
        assert_true(payload["positive_truth_candidate_approved_sum"] == 0, payload)
        assert_true(payload["threshold_tuning_approved_sum"] == 0, payload)

        request = pd.read_csv(
            output_dir / "panel_day_engine_voltage_preserved_evidence_request_packet_v1.csv"
        )
        checklist = pd.read_csv(
            output_dir / "panel_day_engine_voltage_preserved_evidence_request_checklist_v1.csv"
        )
        summary = pd.read_csv(
            output_dir / "panel_day_engine_voltage_preserved_evidence_request_summary_v1.csv"
        )
        assert_true(int(request["engine_patch_allowed"].sum()) == 0, request)
        assert_true(int(request["threshold_patch_allowed"].sum()) == 0, request)
        assert_true(set(request["request_priority"]) == {
            "P0_counterexample_guarded_evidence_request",
            "P0_independent_evidence_request",
            "P1_shape_evidence_request",
        }, request)
        assert_true("counterexample_clearance" in set(checklist["confirmation_axis"]), checklist)
        assert_true(
            int(
                checklist.loc[
                    checklist["confirmation_axis"].eq("raw_waveform_attachment"),
                    "satisfies_independent_confirmation",
                ].sum()
            )
            == 0,
            checklist,
        )
        assert_true(int(summary.loc[summary["summary_scope"].eq("overall"), "request_rows"].iloc[0]) == 3, summary)
        print(json.dumps({"smoke": "ok", "request_rows": int(len(request))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
