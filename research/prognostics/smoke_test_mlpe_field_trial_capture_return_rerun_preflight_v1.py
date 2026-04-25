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
    with tempfile.TemporaryDirectory(prefix="mlpe_capture_return_rerun_preflight_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        validation = tmp / "validation.csv"
        evidence = tmp / "evidence.csv"
        output_dir = tmp / "preflight"

        validation.write_text(
            "trial_event_id,validation_bucket,returned_ready_for_adjudication_flag,still_waiting_for_real_capture_flag,validation_failed_flag,label_attached_flag\n"
            "WAITING,still_waiting_for_real_capture,0,1,0,0\n"
            "READY,returned_capture_ready_label_pending,1,0,0,0\n"
            "BAD_VALIDATION,returned_metadata_incomplete,0,0,1,0\n"
            "BAD_EVIDENCE,returned_capture_ready_label_pending,1,0,0,0\n",
            encoding="utf-8",
        )
        evidence.write_text(
            "trial_event_id,evidence_required_flag,evidence_file_exists_flag,evidence_resolution_bucket\n"
            "WAITING,1,0,waiting_for_real_capture\n"
            "WAITING,1,0,waiting_for_real_capture\n"
            "WAITING,1,0,waiting_for_real_capture\n"
            "READY,1,1,evidence_file_resolved\n"
            "READY,1,1,evidence_file_resolved\n"
            "READY,1,1,evidence_file_resolved\n"
            "BAD_VALIDATION,1,1,evidence_file_resolved\n"
            "BAD_VALIDATION,1,1,evidence_file_resolved\n"
            "BAD_VALIDATION,1,1,evidence_file_resolved\n"
            "BAD_EVIDENCE,1,1,evidence_file_resolved\n"
            "BAD_EVIDENCE,1,0,evidence_file_not_found\n"
            "BAD_EVIDENCE,1,1,evidence_file_resolved\n",
            encoding="utf-8",
        )
        proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_return_rerun_preflight_v1.py",
                "--repo-root",
                str(repo_root),
                "--validation",
                str(validation),
                "--evidence-resolution",
                str(evidence),
                "--output-dir",
                str(output_dir),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["rows"] == 4, payload)
        assert_true(payload["waiting_rows"] == 1, payload)
        assert_true(payload["rerun_allowed_rows"] == 1, payload)
        assert_true(payload["validation_failed_rows"] == 1, payload)
        assert_true(payload["required_evidence_problem_rows"] == 1, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        print(json.dumps({"smoke": "ok", "rerun_allowed_rows": 1}, ensure_ascii=False))


if __name__ == "__main__":
    main()
