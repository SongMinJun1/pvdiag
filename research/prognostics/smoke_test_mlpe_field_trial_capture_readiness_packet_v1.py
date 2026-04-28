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


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="mlpe_field_trial_capture_readiness_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        schema_out = tmp / "schema"
        schema_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_schema_v1.py",
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(schema_out),
            ],
            repo_root,
        )
        assert_true(schema_proc.returncode == 0, schema_proc.stderr or schema_proc.stdout)

        capture = pd.read_csv(schema_out / "mlpe_field_trial_capture_template_v1.csv").astype(object)
        raw = tmp / "raw.csv"
        peer = tmp / "peer.csv"
        wave = tmp / "wave.csv"
        for path in [raw, peer, wave]:
            path.write_text("ts,v,i,p\n2026-01-01T00:00:00Z,1,1,1\n", encoding="utf-8")

        capture.loc[0, ["site", "panel_id", "mlpe_device_id", "start_ts", "end_ts", "injection_strength"]] = [
            "fixture",
            "panel-A",
            "mlpe-A",
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:10:00Z",
            "baseline",
        ]
        capture.loc[0, ["capture_status", "raw_data_path", "peer_data_path", "waveform_slice_path"]] = [
            "captured",
            str(raw),
            str(peer),
            str(wave),
        ]
        capture.loc[0, ["timestamp_quality", "communication_quality"]] = ["ok", "ok"]

        capture.loc[1, "capture_status"] = "captured"
        capture.loc[1, "site"] = "fixture"
        capture.loc[1, "panel_id"] = "panel-B"

        capture_input = tmp / "capture.csv"
        capture.to_csv(capture_input, index=False, encoding="utf-8-sig")
        out = tmp / "readiness"
        proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py",
                "--repo-root",
                str(repo_root),
                "--capture-input",
                str(capture_input),
                "--output-dir",
                str(out),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["rows"] == 14, payload)
        assert_true(payload["metadata_ready_rows"] == 1, payload)
        assert_true(payload["evidence_paths_exist_rows"] == 1, payload)
        assert_true(payload["capture_ready_label_pending_rows"] == 1, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)

        readiness = pd.read_csv(out / "mlpe_field_trial_capture_readiness_packet_v1.csv")
        assert_true("capture_ready_label_pending" in set(readiness["readiness_bucket"]), readiness)
        assert_true("capture_metadata_incomplete" in set(readiness["readiness_bucket"]), readiness)
        print(json.dumps({"smoke": "ok", "rows": int(len(readiness))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
