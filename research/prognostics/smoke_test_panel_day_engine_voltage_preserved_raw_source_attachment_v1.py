#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


REQUEST_COLUMNS = [
    "evidence_request_id",
    "source_confirmation_packet_row_id",
    "source_confirmation_family_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "request_priority",
    "evidence_request_status",
    "representative_candidate_row_id",
    "representative_anchor_date",
    "representative_onset_date",
    "representative_gap_days",
    "candidate_rows_for_panel",
    "unique_anchor_dates_for_panel",
    "min_gap_days_for_panel",
    "median_gap_days_for_panel",
    "max_gap_days_for_panel",
    "counterexample_risk_flag",
    "raw_waveform_request_required",
    "raw_waveform_is_independent_confirmation",
    "physical_measurement_or_iv_required",
    "maintenance_or_inspection_required",
    "common_cause_clearance_required",
    "measurement_artifact_clearance_required",
    "counterexample_clearance_required",
    "evidence_ready_for_truth_use",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

SOURCE_MAP_COLUMNS = [
    "confirmation_packet_row_id",
    "search_candidate_row_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "hard_episode_anchor_date",
    "onset_candidate_date",
    "gap_days",
    "candidate_tier",
    "candidate_priority",
    "known_review_role",
    "manual_review_ready",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

CORE_COLUMNS = [
    "date",
    "panel_id",
    "source_csv",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "event_A",
    "degraded_candidate",
    "fault_like_day",
    "data_bad",
    "co_drop_frac",
    "dtw_dist",
    "hs_score",
    "critical_fault",
    "final_fault",
    "group_off_like",
    "subgroup_common_cause_candidate",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def request(row_id: str, packet_id: str, panel_id: str, priority: str, risk: int) -> dict[str, object]:
    root_id = panel_id.split(".")[0]
    return {
        "evidence_request_id": row_id,
        "source_confirmation_packet_row_id": packet_id,
        "source_confirmation_family_id": packet_id.replace("VPCP", "VPCF"),
        "site": "fixture",
        "root_id": root_id,
        "panel_group_key": ".".join(panel_id.split(".")[:2]),
        "panel_id": panel_id,
        "request_priority": priority,
        "evidence_request_status": "needs_evidence_attachment",
        "representative_candidate_row_id": f"{packet_id}-SRC",
        "representative_anchor_date": "2025-01-03",
        "representative_onset_date": "2025-01-01",
        "representative_gap_days": 2,
        "candidate_rows_for_panel": 1,
        "unique_anchor_dates_for_panel": 1,
        "min_gap_days_for_panel": 2,
        "median_gap_days_for_panel": 2.0,
        "max_gap_days_for_panel": 2,
        "counterexample_risk_flag": risk,
        "raw_waveform_request_required": 1,
        "raw_waveform_is_independent_confirmation": 0,
        "physical_measurement_or_iv_required": 1,
        "maintenance_or_inspection_required": 1,
        "common_cause_clearance_required": 1,
        "measurement_artifact_clearance_required": 1,
        "counterexample_clearance_required": risk,
        "evidence_ready_for_truth_use": 0,
        "positive_truth_candidate_approved": 0,
        "threshold_tuning_approved": 0,
        "operator_facing_change_allowed": 0,
        "engine_patch_allowed": 0,
        "threshold_patch_allowed": 0,
    }


def source(packet_id: str, row_id: str, panel_id: str, onset: str, anchor: str, gap: int) -> dict[str, object]:
    root_id = panel_id.split(".")[0]
    return {
        "confirmation_packet_row_id": packet_id,
        "search_candidate_row_id": row_id,
        "site": "fixture",
        "root_id": root_id,
        "panel_group_key": ".".join(panel_id.split(".")[:2]),
        "panel_id": panel_id,
        "hard_episode_anchor_date": anchor,
        "onset_candidate_date": onset,
        "gap_days": gap,
        "candidate_tier": "strong_b089_like",
        "candidate_priority": "P0_independent_confirmation_review",
        "known_review_role": "new_search_candidate",
        "manual_review_ready": 1,
        "positive_truth_candidate_approved": 0,
        "threshold_tuning_approved": 0,
        "operator_facing_change_allowed": 0,
        "engine_patch_allowed": 0,
        "threshold_patch_allowed": 0,
    }


def core_row(panel_id: str, date: str, v_ratio: float, i_ratio: float, group_off: int = 0) -> dict[str, object]:
    return {
        "date": date,
        "panel_id": panel_id,
        "source_csv": f"{date}-fixture.csv",
        "mid_ratio": round(v_ratio * i_ratio, 6),
        "mid_v_ratio": v_ratio,
        "mid_i_ratio": i_ratio,
        "event_A": int(v_ratio <= 0.75),
        "degraded_candidate": int(v_ratio <= 0.75),
        "fault_like_day": int(v_ratio <= 0.75),
        "data_bad": 0,
        "co_drop_frac": 0.0,
        "dtw_dist": 1.2,
        "hs_score": 0.4,
        "critical_fault": 0,
        "final_fault": 0,
        "group_off_like": group_off,
        "subgroup_common_cause_candidate": 0,
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="voltage_preserved_raw_source_attachment_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        request_dir = tmp / "request"
        request_dir.mkdir()
        data_root = tmp / "data"
        source_map_path = tmp / "source_map.csv"
        output_dir = tmp / "out"
        panel_a = "rootA.1.0"
        panel_b = "rootB.1.0"
        requests = [
            request("BR095-VPER-001", "BR093-VPCP-001", panel_a, "P0_independent_evidence_request", 0),
            request("BR095-VPER-002", "BR093-VPCP-002", panel_b, "P0_counterexample_guarded_evidence_request", 1),
        ]
        pd.DataFrame(requests).reindex(columns=REQUEST_COLUMNS).to_csv(
            request_dir / "panel_day_engine_voltage_preserved_evidence_request_packet_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )
        sources = [
            source("BR093-VPCP-001", "BR092-VPPS-001", panel_a, "2025-01-01", "2025-01-03", 2),
            source("BR093-VPCP-002", "BR092-VPPS-002", panel_b, "2025-01-02", "2025-01-04", 2),
        ]
        pd.DataFrame(sources).reindex(columns=SOURCE_MAP_COLUMNS).to_csv(
            source_map_path, index=False, encoding="utf-8-sig"
        )
        out_dir = data_root / "fixture" / "out"
        raw_dir = data_root / "fixture" / "raw"
        out_dir.mkdir(parents=True)
        raw_dir.mkdir(parents=True)
        core_rows = [
            core_row(panel_a, "2025-01-01", 0.70, 0.95),
            core_row(panel_a, "2025-01-02", 0.69, 0.96),
            core_row(panel_a, "2025-01-03", 0.68, 0.97),
            core_row(panel_b, "2025-01-02", 0.72, 0.94, group_off=1),
            core_row(panel_b, "2025-01-03", 0.71, 0.95, group_off=1),
            core_row(panel_b, "2025-01-04", 0.70, 0.96, group_off=1),
        ]
        pd.DataFrame(core_rows).reindex(columns=CORE_COLUMNS).to_csv(
            out_dir / "panel_day_core.csv", index=False, encoding="utf-8-sig"
        )
        for row in core_rows:
            (raw_dir / row["source_csv"]).write_text("date_time,map_type,map_id,i_out (A),v_in (V),p (W)\n", encoding="utf-8")

        cmd = [
            sys.executable,
            "research/prognostics/build_panel_day_engine_voltage_preserved_raw_source_attachment_v1.py",
            "--repo-root",
            str(repo_root),
            "--request-dir",
            str(request_dir),
            "--source-map-input",
            str(source_map_path),
            "--data-root",
            str(data_root),
            "--output-dir",
            str(output_dir),
        ]
        proc = run(cmd, repo_root)
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["attachment_rows"] == 2, payload)
        assert_true(payload["source_candidate_trace_rows"] == 2, payload)
        assert_true(payload["daily_trace_rows"] == 6, payload)
        assert_true(payload["attachment_status_counts"] == {"raw_source_trace_attached": 2}, payload)
        assert_true(payload["raw_file_refs_missing_sum"] == 0, payload)
        assert_true(payload["raw_waveform_independent_confirmation_sum"] == 0, payload)
        assert_true(payload["physical_or_maintenance_evidence_attached_sum"] == 0, payload)
        assert_true(payload["evidence_ready_for_truth_use_sum"] == 0, payload)
        assert_true(payload["threshold_tuning_approved_sum"] == 0, payload)

        attachment = pd.read_csv(output_dir / "panel_day_engine_voltage_preserved_raw_source_attachment_index_v1.csv")
        daily = pd.read_csv(output_dir / "panel_day_engine_voltage_preserved_raw_source_daily_trace_v1.csv")
        assert_true(int(attachment["engine_patch_allowed"].sum()) == 0, attachment)
        assert_true(int(daily["voltage_preserved_core_signal"].sum()) == 6, daily)
        assert_true(int(daily["common_cause_context_flag"].sum()) == 3, daily)
        print(json.dumps({"smoke": "ok", "attachment_rows": int(len(attachment))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
