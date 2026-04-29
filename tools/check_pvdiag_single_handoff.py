#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REQUIRED_PAYLOAD_PATHS = {
    "release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py",
    "release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py",
    "release/conalog_full_runtime_v1/package/research/prognostics/runtime_rawonly_chain_common_v1.py",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_final_verdict_v1.py",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_heuristic_v1.py",
    "release/conalog_full_runtime_v1/package/research/prognostics/heuristic_display_registry_v1.py",
}

EXCLUDED_PAYLOAD_PATHS = {
    "release/conalog_full_runtime_v1/package/app/import_any_csv_root.py",
    "release/conalog_full_runtime_v1/package/requirements.txt",
    "release/conalog_full_runtime_v1/package/artifacts/fault6_fixed_result_provenance_v1.json",
    "release/conalog_full_runtime_v1/package/artifacts/ktc_fault2_label_and_algorithm_preview_v1.csv",
    "release/conalog_full_runtime_v1/package/artifacts/runtime_chain_dependency_audit_v1.json",
    "release/conalog_full_runtime_v1/package/artifacts/runtime_chain_dependency_audit_v1.md",
    "release/conalog_full_runtime_v1/package/research/__init__.py",
    "release/conalog_full_runtime_v1/package/research/prognostics/__init__.py",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_bootstrap_verdict_v1.py",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_fault_panel_event_audit_v1.py",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_panel_multiaxis_verdict_v1.py",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_gpvs_evidence_pack_v1.py",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_cause_candidate_heuristics_v1.py",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check that the generated pvdiag_single.py handoff artifact is ready to send."
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--single", type=Path, default=Path("release/conalog_full_runtime_v1/pvdiag_single.py"))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("release/conalog_full_runtime_v1/pvdiag_single_manifest_v1.json"),
    )
    parser.add_argument("--skip-self-test", action="store_true")
    return parser.parse_args()


def fail(message: str) -> None:
    raise SystemExit(message)


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    single = resolve(repo_root, args.single)
    manifest = resolve(repo_root, args.manifest)
    if not single.exists():
        fail(f"missing single-file artifact: {single}")
    if not manifest.exists():
        fail(f"missing single-file manifest: {manifest}")

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    single_text = single.read_text(encoding="utf-8")
    files = {str(row.get("path", "")) for row in payload.get("files", [])}
    missing = sorted(REQUIRED_PAYLOAD_PATHS - files)
    if missing:
        fail("manifest missing required payload paths:\n" + "\n".join(missing))
    unexpected = sorted(EXCLUDED_PAYLOAD_PATHS & files)
    if unexpected:
        fail("manifest still includes single-file excluded payload paths:\n" + "\n".join(unexpected))
    if payload.get("payload_mode") != "source_text":
        fail(f"unexpected payload mode: {payload.get('payload_mode')}")
    if payload.get("payload_container") != "json_chunks":
        fail(f"unexpected payload container: {payload.get('payload_container')}")
    runtime_rows = sorted(path for path in files if "/runtime/windows_x64/" in path or path.endswith(".pyc"))
    if runtime_rows:
        fail("single payload contains excluded runtime/cache rows:\n" + "\n".join(runtime_rows[:20]))
    single_line_count = len(single_text.splitlines())
    if single_line_count > 1_000:
        fail(f"single-file artifact is too line-heavy: {single_line_count} lines")
    if int(payload.get("payload_text_bytes", 0)) > 8_000_000:
        fail(f"payload too large: {payload.get('payload_text_bytes')}")
    if int(payload.get("payload_file_count", 0)) != len(files):
        fail(
            f"payload file count mismatch: manifest={payload.get('payload_file_count')} actual={len(files)}"
        )
    if "PAYLOAD_B64" in single_text or "import base64" in single_text or "import zipfile" in single_text:
        fail("single-file artifact still contains the old base64/zip payload path")
    if "EMBEDDED_TEXT_JSON_CHUNKS" not in single_text or "PAYLOAD_MODE = \"source_text\"" not in single_text:
        fail("single-file artifact does not expose the source-text payload markers")
    if "PAYLOAD_FILE_INDEX" not in single_text or "PAYLOAD_STRUCTURE_NOTE" not in single_text:
        fail("single-file artifact does not expose the visible payload structure index")

    compile_proc = subprocess.run(
        [sys.executable, "-m", "py_compile", str(single)],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if compile_proc.returncode != 0:
        fail(compile_proc.stderr or compile_proc.stdout)

    if not args.skip_self_test:
        self_test = subprocess.run(
            [sys.executable, str(single), "--single-self-test"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if self_test.returncode != 0:
            fail(self_test.stderr or self_test.stdout)
        if "self-test ok" not in self_test.stdout:
            fail("single self-test did not print expected success marker")
        if "payload_structure_note" not in self_test.stdout:
            fail("single self-test did not print payload structure guidance")

        list_payload = subprocess.run(
            [sys.executable, str(single), "--single-list-payload"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if list_payload.returncode != 0:
            fail(list_payload.stderr or list_payload.stdout)
        for marker in ["entry_runner", "core_engine", "raw_only_shared_utils"]:
            if marker not in list_payload.stdout:
                fail(f"single payload list missing marker: {marker}")

        with tempfile.TemporaryDirectory(prefix="pvdiag_single_handoff_extract_") as tmp:
            extract_source = subprocess.run(
                [sys.executable, str(single), "--single-extract-source", tmp],
                cwd=repo_root,
                text=True,
                capture_output=True,
                check=False,
            )
            if extract_source.returncode != 0:
                fail(extract_source.stderr or extract_source.stdout)
            extracted_root = Path(tmp)
            if not (extracted_root / "release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py").exists():
                fail("source extraction did not write the embedded runner")
            if not (extracted_root / "release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py").exists():
                fail("source extraction did not write the embedded core engine")

    print(
        json.dumps(
            {
                "handoff_ready": 1,
                "single_file": str(single),
                "manifest": str(manifest),
                "payload_mode": str(payload.get("payload_mode")),
                "payload_container": str(payload.get("payload_container")),
                "payload_file_count": int(payload.get("payload_file_count", 0)),
                "payload_text_bytes": int(payload.get("payload_text_bytes", 0)),
                "single_line_count": single_line_count,
                "visible_payload_index": int("PAYLOAD_FILE_INDEX" in single_text),
                "excluded_runtime_windows_x64": bool(payload.get("excluded_runtime_windows_x64")),
                "self_test_ran": int(not args.skip_self_test),
                "payload_list_ran": int(not args.skip_self_test),
                "source_extract_ran": int(not args.skip_self_test),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
