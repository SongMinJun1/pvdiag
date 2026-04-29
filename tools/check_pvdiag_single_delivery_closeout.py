#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REQUIRED_EXTERNAL_PACKAGES = ["pandas", "numpy", "torch", "openpyxl", "tqdm"]
REQUIRED_RESULT_ARTIFACTS = [
    "result/fault_panel_result_master_report_v1.md",
    "result/fault_panel_result_detailed_report_v1.xlsx",
    "result/fault_panel_result_precursor_report_v1.csv",
    "result/fault_panel_result_raw_only_fault_signal_report_v1.csv",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Close out the pvdiag_single.py delivery path: export one file, "
            "self-test it, check handoff docs, and write a checksum snapshot."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--export-output-dir", type=Path, required=True)
    parser.add_argument(
        "--snapshot-output",
        type=Path,
        default=Path("release/conalog_full_runtime_v1/pvdiag_single_delivery_snapshot_v1.json"),
    )
    parser.add_argument("--clean-output-dir", action="store_true")
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def fail(message: str) -> None:
    raise SystemExit(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_checked(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        fail(
            "command failed:\n"
            f"{' '.join(command)}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )
    return proc


def load_single_manifest(repo_root: Path) -> dict[str, object]:
    manifest = repo_root / "release/conalog_full_runtime_v1/pvdiag_single_manifest_v1.json"
    if not manifest.exists():
        fail(f"missing single-file build manifest: {manifest}")
    return json.loads(manifest.read_text(encoding="utf-8"))


def check_doc(path: Path, required_snippets: list[str]) -> list[str]:
    if not path.exists():
        fail(f"missing handoff doc: {path}")
    text = path.read_text(encoding="utf-8")
    missing = [snippet for snippet in required_snippets if snippet not in text]
    if missing:
        fail(f"{path} missing required snippets: {missing}")
    return required_snippets


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    export_output_dir = args.export_output_dir.resolve()
    snapshot_output = resolve(repo_root, args.snapshot_output)
    single_source = repo_root / "release/conalog_full_runtime_v1/pvdiag_single.py"
    exporter = repo_root / "tools/export_pvdiag_single_delivery.py"

    if not single_source.exists():
        fail(f"missing generated single-file artifact: {single_source}")
    if not exporter.exists():
        fail(f"missing delivery exporter: {exporter}")

    with tempfile.TemporaryDirectory(prefix="pvdiag_single_closeout_") as tmp:
        internal_manifest = Path(tmp) / "export_manifest.json"
        export_cmd = [
            sys.executable,
            str(exporter),
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(export_output_dir),
            "--manifest-output",
            str(internal_manifest),
        ]
        if args.clean_output_dir:
            export_cmd.append("--clean-output-dir")
        export_proc = run_checked(export_cmd, repo_root)

        export_summary = json.loads(export_proc.stdout)
        exported_file = Path(export_summary["exported_file"])
        if sorted(path.name for path in export_output_dir.iterdir()) != ["pvdiag_single.py"]:
            fail(f"export output is not exactly one file: {export_output_dir}")
        if sha256_file(single_source) != sha256_file(exported_file):
            fail("source/export checksum mismatch after export")

        self_test = run_checked([sys.executable, str(exported_file), "--single-self-test"], export_output_dir)
        if "self-test ok" not in self_test.stdout:
            fail("exported pvdiag_single.py did not print the self-test success marker")

    quickstart = repo_root / "release/conalog_full_runtime_v1/PVDIAG_SINGLE_QUICKSTART.md"
    checklist = repo_root / "release/conalog_full_runtime_v1/PVDIAG_SINGLE_DELIVERY_CHECKLIST.md"
    quickstart_checks = check_doc(
        quickstart,
        [
            "python tools/export_pvdiag_single_delivery.py --output-dir /tmp/pvdiag_professor_delivery",
            "pvdiag_single.py",
            "pip install pandas numpy torch openpyxl tqdm",
            "--data-root",
            "--output-root",
        ],
    )
    checklist_checks = check_doc(
        checklist,
        [
            "보낼 파일은 `pvdiag_single.py` 한 개",
            "pandas numpy torch openpyxl tqdm",
            "python pvdiag_single.py --single-self-test",
            "실증 CSV",
        ],
    )

    single_manifest = load_single_manifest(repo_root)
    snapshot = {
        "snapshot_schema": "pvdiag_single_delivery_snapshot_v1",
        "release_id": "pvdiag_single_br247_20260430",
        "professor_deliverable_file_count": 1,
        "professor_deliverable_files": ["pvdiag_single.py"],
        "single_file": {
            "path": "release/conalog_full_runtime_v1/pvdiag_single.py",
            "bytes": single_source.stat().st_size,
            "sha256": sha256_file(single_source),
        },
        "embedded_payload": {
            "payload_file_count": int(single_manifest.get("payload_file_count", 0)),
            "payload_zip_bytes": int(single_manifest.get("payload_zip_bytes", 0)),
            "generated_at_utc": str(single_manifest.get("generated_at_utc", "")),
            "excluded_runtime_windows_x64": bool(single_manifest.get("excluded_runtime_windows_x64")),
        },
        "external_package_prerequisites": REQUIRED_EXTERNAL_PACKAGES,
        "expected_result_artifacts": REQUIRED_RESULT_ARTIFACTS,
        "validation_scope": {
            "handoff_check_ran": 1,
            "export_one_file_check": 1,
            "checksum_equality_check": 1,
            "exported_self_test_check": 1,
            "handoff_doc_snippet_check": 1,
            "algorithm_semantics_changed": 0,
            "field_trial_csv_required_for_truth_label_evaluation": 1,
        },
        "handoff_docs_checked": {
            "quickstart": str(quickstart.relative_to(repo_root)),
            "quickstart_snippets": quickstart_checks,
            "checklist": str(checklist.relative_to(repo_root)),
            "checklist_snippets": checklist_checks,
        },
        "field_trial_next_step": (
            "When real ktc_ess CSVs arrive, run the exported pvdiag_single.py with "
            "--data-root and review the expected result artifacts before any truth-label claim."
        ),
    }

    snapshot_output.parent.mkdir(parents=True, exist_ok=True)
    snapshot_output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "closeout_ready": 1,
                "release_id": snapshot["release_id"],
                "export_output_dir": str(export_output_dir),
                "snapshot_output": str(snapshot_output),
                "single_sha256": snapshot["single_file"]["sha256"],
                "single_bytes": snapshot["single_file"]["bytes"],
                "professor_deliverable_file_count": 1,
                "algorithm_semantics_changed": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
