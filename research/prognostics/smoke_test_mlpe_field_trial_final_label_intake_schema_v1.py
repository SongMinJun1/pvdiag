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
    with tempfile.TemporaryDirectory(prefix="mlpe_final_label_intake_schema_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        packet = tmp / "packet.csv"
        output_dir = tmp / "label_intake"
        packet.write_text(
            "trial_event_id,packet_status,source_preflight_bucket\n"
            "READY,ready_for_final_adjudication_packet,ready_for_readiness_handoff_rerun\n",
            encoding="utf-8",
        )
        proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_final_label_intake_schema_v1.py",
                "--repo-root",
                str(repo_root),
                "--packet",
                str(packet),
                "--output-dir",
                str(output_dir),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["template_rows"] == 1, payload)
        assert_true(payload["schema_rows"] >= 16, payload)
        assert_true(payload["allowed_value_rows"] >= 10, payload)
        assert_true(payload["reviewer_label_attached_rows"] == 0, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["threshold_patch_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)
        print(json.dumps({"smoke": "ok", "template_rows": 1}, ensure_ascii=False))


if __name__ == "__main__":
    main()
