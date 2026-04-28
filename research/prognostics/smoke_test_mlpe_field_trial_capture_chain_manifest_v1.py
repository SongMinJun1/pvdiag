#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

from mlpe_field_trial_chain_manifest_v1 import (
    DEFAULT_CAPTURE_CHAIN_MANIFEST,
    resolve_capture_chain_dependency,
    resolve_manifest_artifact,
)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    schema_dir = resolve_manifest_artifact(repo_root, "capture_schema_dir", DEFAULT_CAPTURE_CHAIN_MANIFEST)
    readiness_packet = resolve_manifest_artifact(repo_root, "capture_readiness_packet", DEFAULT_CAPTURE_CHAIN_MANIFEST)
    explicit = resolve_capture_chain_dependency(repo_root, "explicit.csv", "capture_readiness_packet", DEFAULT_CAPTURE_CHAIN_MANIFEST)
    assert_true(schema_dir.exists(), schema_dir)
    assert_true(readiness_packet.name == "mlpe_field_trial_capture_readiness_packet_v1.csv", readiness_packet)
    assert_true(explicit == repo_root / "explicit.csv", explicit)

    with tempfile.TemporaryDirectory(prefix="mlpe_capture_chain_manifest_smoke_") as tmpdir:
        output_dir = Path(tmpdir) / "audit"
        proc = subprocess.run(
            [
                sys.executable,
                str(repo_root / "research/prognostics/build_repo_path_portability_audit_v1.py"),
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
        detail = pd.read_csv(output_dir / "repo_path_portability_detail_v1.csv")
        counts = detail["dependency_contract"].value_counts(dropna=False).to_dict()
        assert_true(counts.get("mlpe_upstream_generated_artifact_input", 0) == 12, counts)
        assert_true(counts.get("mlpe_chain_directory_bundle_input", 0) == 1, counts)
        assert_true(counts.get("mlpe_user_filled_input", 0) == 7, counts)

    print(json.dumps({"smoke": "ok", "remaining_upstream": 12, "remaining_chain_dir": 1}, ensure_ascii=False))


if __name__ == "__main__":
    main()
