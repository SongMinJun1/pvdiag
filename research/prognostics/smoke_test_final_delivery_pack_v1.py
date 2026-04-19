#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "research/prognostics/build_final_delivery_pack_v1.py"
RELEASE_ROOT = REPO_ROOT / "release/final_delivery_v1"
PACKAGE_ROOT = RELEASE_ROOT / "package"
MANIFEST_PATH = RELEASE_ROOT / "final_delivery_manifest_v1.csv"
SUMMARY_PATH = RELEASE_ROOT / "final_delivery_summary_v1.json"

REQUIRED_TOP_LEVEL_DOCS = [
    RELEASE_ROOT / "README.md",
    RELEASE_ROOT / "QUICKSTART.md",
    RELEASE_ROOT / "RELEASE_NOTES.md",
    RELEASE_ROOT / "KNOWN_LIMITS.md",
    RELEASE_ROOT / "DELIVERY_MANIFEST.md",
]

REQUIRED_PACKAGE_DIRS = [
    PACKAGE_ROOT / "docs",
    PACKAGE_ROOT / "stable_handoff",
    PACKAGE_ROOT / "runtime",
    PACKAGE_ROOT / "oneclick",
    PACKAGE_ROOT / "examples",
]

WATCHED_FROZEN_OUTPUTS = [
    REPO_ROOT / "_share/panel_day_engine_panel_multiaxis_verdict_v1.csv",
    REPO_ROOT / "_share/panel_day_engine_gpvs_evidence_pack_v1.csv",
    REPO_ROOT / "_share/panel_day_engine_integrated_result_table_v1.csv",
    REPO_ROOT / "_share/panel_day_engine_integrated_result_summary_v1.csv",
    REPO_ROOT / "_share/panel_day_engine_cause_candidate_heuristics_v1.csv",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise SystemExit(result.stderr or result.stdout or f"command failed: {' '.join(cmd)}")


def assert_exists(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"missing required artifact: {path}")


def main() -> None:
    run([sys.executable, "-m", "py_compile", "pv_ae/panel_day_engine.py"])
    run([sys.executable, "-m", "py_compile", str(BUILD_SCRIPT)])
    run([sys.executable, "-m", "py_compile", str(Path(__file__))])

    before_hashes = {path: sha256(path) for path in WATCHED_FROZEN_OUTPUTS}

    run([sys.executable, str(BUILD_SCRIPT)])

    assert_exists(PACKAGE_ROOT)
    assert_exists(MANIFEST_PATH)
    assert_exists(SUMMARY_PATH)

    for path in REQUIRED_TOP_LEVEL_DOCS + REQUIRED_PACKAGE_DIRS:
        assert_exists(path)

    with MANIFEST_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    required_manifest_cols = {
        "relative_path",
        "artifact_kind",
        "stability_level_ko",
        "included_flag",
        "note_ko",
    }
    if set(reader.fieldnames or []) != required_manifest_cols:
        raise SystemExit(f"unexpected manifest columns: {reader.fieldnames}")
    if not rows:
        raise SystemExit("manifest must not be empty")

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    required_summary_keys = {
        "generated_at_utc",
        "git_branch",
        "git_head",
        "official_freeze_tag_before_release",
        "delivery_pack_version",
        "stable_artifact_count",
        "reference_only_artifact_count",
        "triage_only_artifact_count",
        "documentation_count",
        "note_ko",
    }
    missing_summary_keys = sorted(required_summary_keys - set(summary))
    if missing_summary_keys:
        raise SystemExit(f"summary missing keys: {missing_summary_keys}")

    sample_paths = [
        PACKAGE_ROOT / "stable_handoff/examples/output_panel_result_sample.csv",
        PACKAGE_ROOT / "examples/integrated_result_table_v1.csv",
        PACKAGE_ROOT / "runtime/panel_day_engine_runtime_latency_report_v1.csv",
        PACKAGE_ROOT / "oneclick/OPS_ONECLICK_OPERATION_GUIDE_V1.md",
    ]
    for path in sample_paths:
        assert_exists(path)

    after_hashes = {path: sha256(path) for path in WATCHED_FROZEN_OUTPUTS}
    if before_hashes != after_hashes:
        raise SystemExit("frozen production outputs changed during final delivery pack build")

    print("[OK] final delivery pack smoke test passed")


if __name__ == "__main__":
    main()
