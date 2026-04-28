#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="mlpe_returned_capture_adjudication_packet_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        preflight = tmp / "preflight.csv"
        output_dir = tmp / "packet"
        preflight.write_text(
            "trial_event_id,validation_bucket,required_evidence_rows,required_evidence_resolved_rows,required_evidence_problem_rows,readiness_handoff_rerun_allowed,post_return_rerun_bucket\n"
            "READY,returned_capture_ready_label_pending,3,3,0,1,ready_for_readiness_handoff_rerun\n"
            "WAITING,still_waiting_for_real_capture,3,0,0,0,blocked_waiting_for_real_capture\n"
            "BAD_EVIDENCE,returned_capture_ready_label_pending,3,2,1,0,blocked_required_evidence_problem\n",
            encoding="utf-8",
        )
        proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_returned_capture_adjudication_packet_v1.py",
                "--repo-root",
                str(repo_root),
                "--preflight",
                str(preflight),
                "--output-dir",
                str(output_dir),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["packet_rows"] == 1, payload)
        assert_true(payload["blocked_rows"] == 2, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)
        print(json.dumps({"smoke": "ok", "packet_rows": 1, "blocked_rows": 2}, ensure_ascii=False))


if __name__ == "__main__":
    main()
