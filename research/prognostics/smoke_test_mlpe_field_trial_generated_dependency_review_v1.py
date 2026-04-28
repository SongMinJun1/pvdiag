#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="mlpe_generated_dependency_review_smoke_") as tmpdir:
        output_dir = Path(tmpdir) / "out"
        proc = subprocess.run(
            [
                sys.executable,
                str(repo_root / "research/prognostics/build_mlpe_field_trial_generated_dependency_review_v1.py"),
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(output_dir),
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)

        payload = json.loads((output_dir / "mlpe_field_trial_generated_dependency_review_v1.json").read_text())
        detail = pd.read_csv(output_dir / "mlpe_field_trial_generated_dependency_review_v1.csv")
        summary = pd.read_csv(output_dir / "mlpe_field_trial_generated_dependency_review_summary_v1.csv")

        assert_true(payload["dependency_rows"] == len(detail), payload)
        assert_true(payload["dependency_rows"] == int(summary[summary["key"].eq("dependency_rows")]["count"].iloc[0]), payload)
        assert_true(payload["dependency_rows"] == 1, payload)
        assert_true(payload["next_patch_lane_counts"].get("mlpe_capture_chain_manifest", 0) == 0, payload)
        assert_true(payload["next_patch_lane_counts"].get("mlpe_truth_intake_chain_manifest", 0) == 0, payload)
        assert_true(payload["next_patch_lane_counts"].get("mlpe_truth_replay_chain_manifest", 0) == 1, payload)
        assert_true(payload["safe_repo_contract_replacement_rows"] == 0, payload)
        assert_true(payload["requires_upstream_generation_rows"] == payload["dependency_rows"], payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(detail["default_variable"].astype(str).str.startswith("DEFAULT_").all(), detail.to_dict("records"))
        assert_true(set(detail["requires_explicit_input_or_manifest_flag"].astype(int)) == {1}, detail.to_dict("records"))
        assert_true(not summary.empty, "empty summary")

    print(json.dumps({"smoke": "ok", "dependency_rows": int(payload["dependency_rows"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
