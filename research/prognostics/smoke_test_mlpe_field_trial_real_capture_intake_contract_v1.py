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
    with tempfile.TemporaryDirectory(prefix="mlpe_real_capture_intake_contract_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        missing_out = tmp / "missing_out"
        base_cmd = [
            sys.executable,
            "research/prognostics/build_mlpe_field_trial_real_capture_intake_contract_v1.py",
            "--repo-root",
            str(repo_root),
        ]

        missing_proc = run(base_cmd + ["--output-dir", str(missing_out)], repo_root)
        assert_true(missing_proc.returncode == 0, missing_proc.stderr or missing_proc.stdout)
        missing_payload = json.loads(missing_proc.stdout)
        assert_true(missing_payload["capture_rows"] == 1, missing_payload)
        assert_true(missing_payload["real_capture_intake_ready_rows"] == 0, missing_payload)
        assert_true(missing_payload["blocked_rows"] == 1, missing_payload)
        assert_true(missing_payload["issue_rows"] == 1, missing_payload)

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
        template = pd.read_csv(schema_out / "mlpe_field_trial_capture_template_v1.csv", encoding="utf-8-sig")
        good = template.head(1).astype(object).copy()
        for field in ["site", "root_id", "panel_id", "mlpe_device_id"]:
            good.loc[good.index[0], field] = f"{field}_001"
        good.loc[good.index[0], "capture_status"] = "captured"
        good.loc[good.index[0], "start_ts"] = "2026-04-26T10:00:00+09:00"
        good.loc[good.index[0], "end_ts"] = "2026-04-26T11:00:00+09:00"
        good.loc[good.index[0], "injection_strength"] = "baseline"
        good.loc[good.index[0], "raw_data_path"] = "raw.csv"
        good.loc[good.index[0], "peer_data_path"] = "peer.csv"
        good.loc[good.index[0], "waveform_slice_path"] = "waveform.csv"
        good.loc[good.index[0], "timestamp_quality"] = "ok"
        good.loc[good.index[0], "communication_quality"] = "ok"
        good_path = tmp / "good_capture.csv"
        good.to_csv(good_path, index=False, encoding="utf-8-sig")

        good_out = tmp / "good_out"
        good_proc = run(base_cmd + ["--capture-input", str(good_path), "--output-dir", str(good_out)], repo_root)
        assert_true(good_proc.returncode == 0, good_proc.stderr or good_proc.stdout)
        good_payload = json.loads(good_proc.stdout)
        assert_true(good_payload["capture_rows"] == 1, good_payload)
        assert_true(good_payload["real_capture_intake_ready_rows"] == 1, good_payload)
        assert_true(good_payload["blocked_rows"] == 0, good_payload)
        assert_true(good_payload["canonical_truth_write_allowed_sum"] == 0, good_payload)
        assert_true(good_payload["truth_intake_allowed_sum"] == 0, good_payload)

        bad = good.copy()
        bad.loc[bad.index[0], "peer_data_path"] = ""
        bad.loc[bad.index[0], "engine_patch_allowed"] = 1
        bad.loc[bad.index[0], "label_status"] = "label_attached"
        bad.loc[bad.index[0], "final_label_attached"] = 1
        bad_path = tmp / "bad_capture.csv"
        bad.to_csv(bad_path, index=False, encoding="utf-8-sig")

        bad_out = tmp / "bad_out"
        bad_proc = run(base_cmd + ["--capture-input", str(bad_path), "--output-dir", str(bad_out)], repo_root)
        assert_true(bad_proc.returncode == 0, bad_proc.stderr or bad_proc.stdout)
        bad_payload = json.loads(bad_proc.stdout)
        assert_true(bad_payload["capture_rows"] == 1, bad_payload)
        assert_true(bad_payload["real_capture_intake_ready_rows"] == 0, bad_payload)
        assert_true(bad_payload["blocked_rows"] == 1, bad_payload)
        assert_true(bad_payload["issue_rows"] >= 3, bad_payload)
        validation = pd.read_csv(bad_payload["outputs"]["validation"], encoding="utf-8-sig")
        assert_true(validation.loc[0, "intake_validation_status"] != "real_capture_intake_ready", validation.to_dict())

        print(
            json.dumps(
                {
                    "smoke": "ok",
                    "missing_blocked_rows": int(missing_payload["blocked_rows"]),
                    "good_ready_rows": int(good_payload["real_capture_intake_ready_rows"]),
                    "bad_blocked_rows": int(bad_payload["blocked_rows"]),
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
