#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def write_source_resolution(path: Path) -> None:
    rows = []
    for event_id, ready in [("EV_CLEAR", 1), ("EV_SOURCE_BLOCKED", 0)]:
        for group in [
            "capture_validation_row",
            "capture_row",
            "raw_data_slice",
            "peer_context_slice",
            "waveform_slice",
            "weather_context",
        ]:
            required = 0 if group == "weather_context" else 1
            blocking = 0 if ready or not required else 1
            rows.append(
                {
                    "trial_event_id": event_id,
                    "real_capture_intake_ready_flag": ready,
                    "evidence_required_flag": required,
                    "source_evidence_blocking_flag": blocking,
                    "source_evidence_resolved_flag": 1 if ready or not required else 0,
                    "canonical_truth_write_allowed": 0,
                    "truth_intake_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "engine_patch_allowed": 0,
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def write_clearance(path: Path, bad: bool = False) -> None:
    rows = [
        {
            "trial_event_id": "EV_CLEAR",
            "site": "ktc_ess",
            "root_id": "root_001",
            "panel_id": "panel_001",
            "event_date": "2026-04-27",
            "timestamp_quality": "bad" if bad else "ok",
            "communication_quality": "dropout" if bad else "ok",
            "telemetry_dropout_flag": 1 if bad else 0,
            "telemetry_stuck_flag": 1 if bad else 0,
            "impossible_value_flag": 0,
            "sensor_offset_suspect_flag": 0,
            "mlpe_state": "clipping" if bad else "normal",
            "optimizer_state_known_flag": 0 if bad else 1,
            "mlpe_control_fault_suspect_flag": 1 if bad else 0,
            "rapid_shutdown_or_safety_state_flag": 0,
            "panel_physical_evidence_flag": 0 if bad else 1,
            "reviewer_artifact_clearance_flag": 0 if bad else 1,
            "reviewer_mlpe_control_clearance_flag": 0 if bad else 1,
            "artifact_mlpe_control_clearance_note": "" if bad else "timestamp, communication, artifact, and MLPE-control blockers cleared in fixture",
            "canonical_truth_write_allowed": 0,
            "truth_intake_allowed": 0,
            "threshold_patch_allowed": 0,
            "engine_patch_allowed": 0,
        },
        {
            "trial_event_id": "EV_SOURCE_BLOCKED",
            "site": "ktc_ess",
            "root_id": "root_002",
            "panel_id": "panel_002",
            "event_date": "2026-04-27",
            "timestamp_quality": "ok",
            "communication_quality": "ok",
            "telemetry_dropout_flag": 0,
            "telemetry_stuck_flag": 0,
            "impossible_value_flag": 0,
            "sensor_offset_suspect_flag": 0,
            "mlpe_state": "normal",
            "optimizer_state_known_flag": 1,
            "mlpe_control_fault_suspect_flag": 0,
            "rapid_shutdown_or_safety_state_flag": 0,
            "panel_physical_evidence_flag": 1,
            "reviewer_artifact_clearance_flag": 1,
            "reviewer_mlpe_control_clearance_flag": 1,
            "artifact_mlpe_control_clearance_note": "would pass if source evidence were ready",
            "canonical_truth_write_allowed": 0,
            "truth_intake_allowed": 0,
            "threshold_patch_allowed": 0,
            "engine_patch_allowed": 0,
        },
    ]
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="mlpe_artifact_mlpe_control_clearance_contract_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        base_cmd = [
            sys.executable,
            "research/prognostics/build_mlpe_field_trial_artifact_mlpe_control_clearance_contract_v1.py",
            "--repo-root",
            str(repo_root),
        ]

        missing_out = tmp / "missing"
        missing_proc = run(base_cmd + ["--output-dir", str(missing_out)], repo_root)
        assert_true(missing_proc.returncode == 0, missing_proc.stderr or missing_proc.stdout)
        missing_payload = json.loads(missing_proc.stdout)
        assert_true(missing_payload["contract_rows"] == 7, missing_payload)
        assert_true(missing_payload["events"] == 0, missing_payload)
        assert_true(missing_payload["artifact_mlpe_control_clearance_ready_events"] == 0, missing_payload)
        assert_true(missing_payload["clearance_blocked_rows"] == 1, missing_payload)
        assert_true(missing_payload["issue_rows"] == 1, missing_payload)

        source = tmp / "source_resolution.csv"
        clearance = tmp / "clearance.csv"
        write_source_resolution(source)
        write_clearance(clearance)

        good_out = tmp / "good"
        good_proc = run(
            base_cmd
            + [
                "--source-evidence-resolution",
                str(source),
                "--artifact-mlpe-control-clearance-input",
                str(clearance),
                "--output-dir",
                str(good_out),
            ],
            repo_root,
        )
        assert_true(good_proc.returncode == 0, good_proc.stderr or good_proc.stdout)
        good_payload = json.loads(good_proc.stdout)
        assert_true(good_payload["contract_rows"] == 7, good_payload)
        assert_true(good_payload["events"] == 2, good_payload)
        assert_true(good_payload["clearance_rows"] == 14, good_payload)
        assert_true(good_payload["artifact_mlpe_control_clearance_ready_events"] == 1, good_payload)
        assert_true(good_payload["clearance_blocked_rows"] == 7, good_payload)
        assert_true(good_payload["truth_intake_allowed_sum"] == 0, good_payload)
        assert_true(good_payload["threshold_patch_allowed_sum"] == 0, good_payload)
        assert_true(good_payload["engine_patch_allowed_sum"] == 0, good_payload)

        bad_clearance = tmp / "bad_clearance.csv"
        write_clearance(bad_clearance, bad=True)
        bad_out = tmp / "bad"
        bad_proc = run(
            base_cmd
            + [
                "--source-evidence-resolution",
                str(source),
                "--artifact-mlpe-control-clearance-input",
                str(bad_clearance),
                "--output-dir",
                str(bad_out),
            ],
            repo_root,
        )
        assert_true(bad_proc.returncode == 0, bad_proc.stderr or bad_proc.stdout)
        bad_payload = json.loads(bad_proc.stdout)
        assert_true(bad_payload["events"] == 2, bad_payload)
        assert_true(bad_payload["artifact_mlpe_control_clearance_ready_events"] == 0, bad_payload)
        assert_true(bad_payload["issue_rows"] >= 5, bad_payload)

        dry_run = pd.read_csv(bad_payload["outputs"]["clearance"], encoding="utf-8-sig")
        statuses = set(dry_run["artifact_mlpe_control_clearance_status"])
        assert_true("blocked_timestamp_quality_not_cleared" in statuses, statuses)
        assert_true("blocked_communication_quality_not_cleared" in statuses, statuses)
        assert_true("blocked_telemetry_artifact_not_cleared" in statuses, statuses)
        assert_true("blocked_mlpe_control_state_not_cleared" in statuses, statuses)
        assert_true("blocked_panel_physical_evidence_missing" in statuses, statuses)

        print(
            json.dumps(
                {
                    "smoke": "ok",
                    "missing_blocked_rows": int(missing_payload["clearance_blocked_rows"]),
                    "good_ready_events": int(good_payload["artifact_mlpe_control_clearance_ready_events"]),
                    "bad_ready_events": int(bad_payload["artifact_mlpe_control_clearance_ready_events"]),
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
