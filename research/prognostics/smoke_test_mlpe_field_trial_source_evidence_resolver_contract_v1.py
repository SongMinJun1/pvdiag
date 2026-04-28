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


def write_validation(path: Path, ready_event: str = "EV_READY", blocked_event: str = "EV_BLOCKED") -> None:
    path.write_text(
        "owner_branch,trial_event_id,row_index,capture_status,intake_validation_status,"
        "real_capture_intake_ready_flag,capture_input_path,canonical_truth_write_allowed,"
        "truth_intake_allowed,threshold_patch_allowed,engine_patch_allowed\n"
        f"BR-20260425-129,{ready_event},1,captured,real_capture_intake_ready,1,capture.csv,0,0,0,0\n"
        f"BR-20260425-129,{blocked_event},2,planned,blocked_still_planned,0,capture.csv,0,0,0,0\n",
        encoding="utf-8",
    )


def write_capture(path: Path, root: Path, bad: bool = False) -> None:
    raw = root / "raw.csv"
    peer = root / "peer.csv"
    wave = root / "waveform.csv"
    for file_path in [raw, peer, wave]:
        file_path.write_text("date,value\n2026-04-27,1\n", encoding="utf-8")

    ready_peer = "" if bad else str(peer)
    ready_wave = str(root / "missing_waveform.csv") if bad else str(wave)
    df = pd.DataFrame(
        [
            {
                "trial_event_id": "EV_READY",
                "raw_data_path": str(raw),
                "peer_data_path": ready_peer,
                "weather_data_path": "",
                "waveform_slice_path": ready_wave,
            },
            {
                "trial_event_id": "EV_BLOCKED",
                "raw_data_path": "",
                "peer_data_path": "",
                "weather_data_path": "",
                "waveform_slice_path": "",
            },
        ]
    )
    df.to_csv(path, index=False, encoding="utf-8-sig")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="mlpe_source_evidence_resolver_contract_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        base_cmd = [
            sys.executable,
            "research/prognostics/build_mlpe_field_trial_source_evidence_resolver_contract_v1.py",
            "--repo-root",
            str(repo_root),
        ]

        missing_out = tmp / "missing"
        missing_proc = run(base_cmd + ["--output-dir", str(missing_out)], repo_root)
        assert_true(missing_proc.returncode == 0, missing_proc.stderr or missing_proc.stdout)
        missing_payload = json.loads(missing_proc.stdout)
        assert_true(missing_payload["contract_rows"] == 6, missing_payload)
        assert_true(missing_payload["events"] == 0, missing_payload)
        assert_true(missing_payload["source_evidence_ready_events"] == 0, missing_payload)
        assert_true(missing_payload["source_evidence_blocked_rows"] == 1, missing_payload)
        assert_true(missing_payload["issue_rows"] == 1, missing_payload)

        validation = tmp / "capture_validation.csv"
        capture = tmp / "capture.csv"
        write_validation(validation)
        write_capture(capture, tmp)

        good_out = tmp / "good"
        good_proc = run(
            base_cmd
            + [
                "--capture-validation",
                str(validation),
                "--capture-input",
                str(capture),
                "--output-dir",
                str(good_out),
            ],
            repo_root,
        )
        assert_true(good_proc.returncode == 0, good_proc.stderr or good_proc.stdout)
        good_payload = json.loads(good_proc.stdout)
        assert_true(good_payload["contract_rows"] == 6, good_payload)
        assert_true(good_payload["events"] == 2, good_payload)
        assert_true(good_payload["resolution_rows"] == 12, good_payload)
        assert_true(good_payload["source_evidence_ready_events"] == 1, good_payload)
        assert_true(good_payload["source_evidence_blocked_rows"] == 5, good_payload)
        assert_true(good_payload["canonical_truth_write_allowed_sum"] == 0, good_payload)
        assert_true(good_payload["truth_intake_allowed_sum"] == 0, good_payload)
        assert_true(good_payload["threshold_patch_allowed_sum"] == 0, good_payload)
        assert_true(good_payload["engine_patch_allowed_sum"] == 0, good_payload)

        bad_capture = tmp / "bad_capture.csv"
        write_capture(bad_capture, tmp, bad=True)
        bad_out = tmp / "bad"
        bad_proc = run(
            base_cmd
            + [
                "--capture-validation",
                str(validation),
                "--capture-input",
                str(bad_capture),
                "--output-dir",
                str(bad_out),
            ],
            repo_root,
        )
        assert_true(bad_proc.returncode == 0, bad_proc.stderr or bad_proc.stdout)
        bad_payload = json.loads(bad_proc.stdout)
        assert_true(bad_payload["events"] == 2, bad_payload)
        assert_true(bad_payload["source_evidence_ready_events"] == 0, bad_payload)
        assert_true(bad_payload["source_evidence_blocked_rows"] >= 7, bad_payload)
        assert_true(bad_payload["issue_rows"] >= 2, bad_payload)

        resolution = pd.read_csv(bad_payload["outputs"]["resolution"], encoding="utf-8-sig")
        statuses = set(resolution["source_evidence_resolution_status"])
        assert_true("blocked_required_path_missing" in statuses, statuses)
        assert_true("blocked_file_not_found" in statuses, statuses)

        print(
            json.dumps(
                {
                    "smoke": "ok",
                    "missing_blocked_rows": int(missing_payload["source_evidence_blocked_rows"]),
                    "good_ready_events": int(good_payload["source_evidence_ready_events"]),
                    "bad_ready_events": int(bad_payload["source_evidence_ready_events"]),
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
