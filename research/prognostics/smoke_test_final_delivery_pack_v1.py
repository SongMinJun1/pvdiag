#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import tempfile
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
    PACKAGE_ROOT / "app",
    PACKAGE_ROOT / "bin",
    PACKAGE_ROOT / "config",
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
        PACKAGE_ROOT / "app/run_conalog_infer.py",
        PACKAGE_ROOT / "app/run_realtime.py",
        PACKAGE_ROOT / "app/run_oneclick.py",
        PACKAGE_ROOT / "app/app_streamlit.py",
        PACKAGE_ROOT / "config/runtime.yaml",
        PACKAGE_ROOT / "bin/run_demo.bat",
        PACKAGE_ROOT / "bin/run_real.bat",
        PACKAGE_ROOT / "bin/open_results.bat",
        PACKAGE_ROOT / "bin/settings.template.json",
        PACKAGE_ROOT / "stable_handoff/examples/output_panel_result_sample.csv",
        PACKAGE_ROOT / "examples/integrated_result_table_v1.csv",
        PACKAGE_ROOT / "runtime/panel_day_engine_runtime_latency_report_v1.csv",
        PACKAGE_ROOT / "oneclick/OPS_ONECLICK_OPERATION_GUIDE_V1.md",
    ]
    for path in sample_paths:
        assert_exists(path)

    run(
        [
            sys.executable,
            "-c",
            (
                "import py_compile; "
                f"py_compile.compile(r'{PACKAGE_ROOT / 'app/run_conalog_infer.py'}', cfile='/tmp/final_delivery_run_conalog_infer.pyc', doraise=True); "
                f"py_compile.compile(r'{PACKAGE_ROOT / 'app/run_realtime.py'}', cfile='/tmp/final_delivery_run_realtime.pyc', doraise=True); "
                f"py_compile.compile(r'{PACKAGE_ROOT / 'app/run_oneclick.py'}', cfile='/tmp/final_delivery_run_oneclick.pyc', doraise=True); "
                f"py_compile.compile(r'{PACKAGE_ROOT / 'app/app_streamlit.py'}', cfile='/tmp/final_delivery_app_streamlit.pyc', doraise=True)"
            ),
        ]
    )

    metadata_files = [str(path.relative_to(PACKAGE_ROOT)) for path in PACKAGE_ROOT.rglob("._*")]
    if metadata_files:
        raise SystemExit(f"AppleDouble metadata files must not remain in package: {metadata_files}")

    integrated_source = REPO_ROOT / "_share/panel_day_engine_integrated_result_table_v1.csv"
    with integrated_source.open("r", encoding="utf-8-sig", newline="") as handle:
        source_reader = csv.DictReader(handle)
        source_columns = source_reader.fieldnames or []
    with (PACKAGE_ROOT / "examples/integrated_result_table_v1.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        packaged_reader = csv.DictReader(handle)
        packaged_columns = packaged_reader.fieldnames or []
    if source_columns != packaged_columns:
        raise SystemExit(
            "final integrated table schema changed inside delivery pack: "
            f"source={source_columns}, packaged={packaged_columns}"
        )

    readme_text = (RELEASE_ROOT / "README.md").read_text(encoding="utf-8")
    known_limits_text = (RELEASE_ROOT / "KNOWN_LIMITS.md").read_text(encoding="utf-8")
    delivery_manifest_text = (RELEASE_ROOT / "DELIVERY_MANIFEST.md").read_text(encoding="utf-8")
    required_phrases = [
        "reference-only",
        "triage-only",
        "run_demo.bat",
        "run_real.bat",
        "package/app/run_conalog_infer.py",
        "git metadata",
    ]
    combined_text = "\n".join([readme_text, known_limits_text, delivery_manifest_text])
    missing_phrases = [phrase for phrase in required_phrases if phrase not in combined_text]
    if missing_phrases:
        raise SystemExit(f"delivery docs missing boundary/executable phrases: {missing_phrases}")

    package_config = PACKAGE_ROOT / "stable_handoff/config/default.yaml"
    package_input_root = PACKAGE_ROOT / "stable_handoff/examples"
    with tempfile.TemporaryDirectory(prefix="final_delivery_gitless_") as tmp_dir:
        dryrun_output_root = Path(tmp_dir)
        env = dict(os.environ)
        env["PATH"] = ""
        result = subprocess.run(
            [
                sys.executable,
                str(PACKAGE_ROOT / "app/run_conalog_infer.py"),
                "--dry-run",
                "--input-root",
                str(package_input_root),
                "--output-root",
                str(dryrun_output_root),
                "--config",
                str(package_config),
                "--include-experimental",
                "off",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
        if result.returncode != 0:
            raise SystemExit(result.stderr or result.stdout or "gitless package dry-run failed")
        metadata_path = dryrun_output_root / "output/run_metadata_v1.json"
        error_log_path = dryrun_output_root / "output/error_log_v1.csv"
        assert_exists(metadata_path)
        assert_exists(error_log_path)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("git_branch") != "git_unavailable" or metadata.get("git_head") != "git_unavailable":
            raise SystemExit(f"gitless dry-run metadata must mark git_unavailable, got: {metadata}")

    after_hashes = {path: sha256(path) for path in WATCHED_FROZEN_OUTPUTS}
    if before_hashes != after_hashes:
        raise SystemExit("frozen production outputs changed during final delivery pack build")

    print("[OK] final delivery pack smoke test passed")


if __name__ == "__main__":
    main()
