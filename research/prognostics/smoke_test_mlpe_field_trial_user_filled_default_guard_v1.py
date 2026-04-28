#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPTS = {
    "build_mlpe_field_trial_capture_return_validator_v1.py": "--returned-capture",
    "build_mlpe_field_trial_capture_return_evidence_resolver_v1.py": "--returned-capture",
    "build_mlpe_field_trial_final_label_validator_v1.py": "--label-input",
    "build_mlpe_field_trial_label_to_truth_gate_v1.py": "--label-input",
    "build_mlpe_field_trial_real_label_intake_runbook_v1.py": "--label-input",
    "build_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py": "--reviewed-checklist",
    "build_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py": "--decision-input",
}


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    checked = []
    with tempfile.TemporaryDirectory(prefix="mlpe_user_filled_default_guard_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        for script, explicit_flag in SCRIPTS.items():
            proc = subprocess.run(
                [
                    sys.executable,
                    str(repo_root / "research" / "prognostics" / script),
                    "--repo-root",
                    str(repo_root),
                    "--output-dir",
                    str(tmp / script.replace(".py", "")),
                ],
                cwd=repo_root,
                text=True,
                capture_output=True,
                check=False,
            )
            combined = f"{proc.stdout}\n{proc.stderr}"
            assert_true(proc.returncode != 0, script)
            assert_true("user-filled MLPE field-trial input" in combined, combined)
            assert_true("Refusing to read the default template path as real evidence." in combined, combined)
            assert_true("Provide an explicit real input path" in combined, combined)
            assert_true(explicit_flag in combined, combined)
            assert_true("--allow-user-filled-default" in combined, combined)
            checked.append(script)

    print(json.dumps({"smoke": "ok", "guarded_scripts": checked}, ensure_ascii=False))


if __name__ == "__main__":
    main()
