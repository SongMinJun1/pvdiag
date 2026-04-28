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
    with tempfile.TemporaryDirectory(prefix="mlpe_field_trial_capture_schema_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        out = tmp / "out"
        cmd = [
            sys.executable,
            "research/prognostics/build_mlpe_field_trial_capture_schema_v1.py",
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(out),
        ]
        proc = run(cmd, repo_root)
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["template_rows"] == 14, payload)
        assert_true(payload["schema_fields"] >= 30, payload)
        assert_true(payload["check_error_count"] == 0, payload)
        assert_true(payload["check_passed"] == 1, payload)

        template = pd.read_csv(out / "mlpe_field_trial_capture_template_v1.csv")
        assert_true(int(template["engine_patch_allowed"].sum()) == 0, template)
        assert_true(set(template["label_status"]) == {"label_pending"}, template)
        assert_true(template["final_fault_family"].fillna("").eq("").all(), template)

        bad = template.astype(object).copy()
        bad.loc[0, "capture_status"] = "captured"
        bad.loc[0, "panel_id"] = ""
        bad.loc[1, "engine_patch_allowed"] = 1
        bad_input = tmp / "bad_capture.csv"
        bad.to_csv(bad_input, index=False, encoding="utf-8-sig")
        bad_out = tmp / "bad_out"
        bad_proc = run(cmd + ["--output-dir", str(bad_out), "--capture-input", str(bad_input)], repo_root)
        assert_true(bad_proc.returncode != 0, bad_proc.stdout)
        bad_checks = pd.read_csv(bad_out / "mlpe_field_trial_capture_check_v1.csv")
        messages = "\n".join(bad_checks["message"].astype(str).tolist())
        assert_true("required after capture_status leaves planned" in messages, messages)
        assert_true("approval flag must remain 0" in messages, messages)
        print(json.dumps({"smoke": "ok", "template_rows": int(len(template))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
