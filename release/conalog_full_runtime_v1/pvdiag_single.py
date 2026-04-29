#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


GENERATED_BY = "tools/build_pvdiag_single_py.py"
GENERATED_AT_UTC = "2026-04-29T19:27:17.876626+00:00"
PAYLOAD_MODE = "source_text"
PAYLOAD_TEXT_SHA256 = "2a8d406edeff59ba839e5efd8e8cb593993f09b4fab68c6199d662c5885fabfb"
PAYLOAD_TEXT_BYTES = 422550
PAYLOAD_FILE_COUNT = 11
PAYLOAD_STRUCTURE_NOTE = (
    "This generated file embeds the modular pvdiag runtime as source-text payload. "
    "Use --single-list-payload to inspect module roles or --single-extract-source DIR "
    "to unpack readable sources."
)

PAYLOAD_FILE_INDEX = [
    {"bytes": 168800, "lines": 3601, "path": "release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py", "role": "entry_runner", "sha256": "21ab958f989db374028b1e96755a46f4f65d09fe391252e08f590b4e21ccd920"},
    {"bytes": 1341, "lines": 7, "path": "release/conalog_full_runtime_v1/package/artifacts/fault6_fixed_result_table_v1.csv", "role": "frozen_fault_reference", "sha256": "93eb336dfdbba36159e802726e9e94d98f782b74ef2e62b5cea46f4a22f93581"},
    {"bytes": 1125, "lines": 7, "path": "release/conalog_full_runtime_v1/package/artifacts/fault6_label_and_algorithm_preview_v1.csv", "role": "required_result_preview", "sha256": "58e321a5bfcd7bf62e398aecde38701a533c5a64cbef2d18935b57bc4a39e20a"},
    {"bytes": 2236, "lines": 65, "path": "release/conalog_full_runtime_v1/package/artifacts/input_baseline_manifest_v1.json", "role": "baseline_fingerprint", "sha256": "8f6e69e526de55fb976e0fd9ecb5c1304816c3d3d48a7f8ef758989d6914ee2c"},
    {"bytes": 2864, "lines": 99, "path": "release/conalog_full_runtime_v1/package/artifacts/panel_day_core_baseline_digest_v1.json", "role": "shadow_compare_reference", "sha256": "15b339b68502e6e1d930987d35e3e67f0a6a5c7a308c3a37a4e8190e10f8b250"},
    {"bytes": 136596, "lines": 3278, "path": "release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py", "role": "core_engine", "sha256": "2cf3ae3f93bc23a5b1e1eeb19418f5ef9a2e12e84f9a583bd0fdaf636ecafbb3"},
    {"bytes": 36363, "lines": 731, "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py", "role": "raw_only_audit_builder", "sha256": "68524c0aa151b9c45c36b7c6c03a91d61391d5e6617230ec780e1f82bddbe49e"},
    {"bytes": 8601, "lines": 191, "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_final_verdict_v1.py", "role": "raw_only_verdict_builder", "sha256": "d23f1a31463f8367d09d23d1c6973d67448b966e89a30f3785e7403ed7dcaccb"},
    {"bytes": 10893, "lines": 299, "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_heuristic_v1.py", "role": "raw_only_heuristic_builder", "sha256": "18275385e1bc22bca4cb442978ec2b817742637983b6edf77ebaa92aab12768a"},
    {"bytes": 3281, "lines": 68, "path": "release/conalog_full_runtime_v1/package/research/prognostics/heuristic_display_registry_v1.py", "role": "display_label_registry", "sha256": "d7cbf8bd24a2274e040231e166eed32098c256c1ba3ce19ba3d667ae6f1f4876"},
    {"bytes": 49430, "lines": 1177, "path": "release/conalog_full_runtime_v1/package/research/prognostics/runtime_rawonly_chain_common_v1.py", "role": "raw_only_shared_utils", "sha256": "62b04b108695ef611f1aa97f7abde111f71d994f38904e1ace2feae595d11ac1"},
]

EMBEDDED_TEXT_FILES: dict[str, str] = {}
EMBEDDED_FILE_SHA256: dict[str, str] = {}

REQUIRED_MODULES = {
    "pandas": "pandas",
    "numpy": "numpy",
    "torch": "torch",
    "openpyxl": "openpyxl",
    "tqdm": "tqdm",
}


def script_dir() -> Path:
    try:
        return Path(__file__).resolve().parent
    except NameError:
        return Path.cwd()


def parse_args(argv: list[str] | None = None) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description=(
            "Run the PV panel fault/precursor diagnosis algorithm from one generated Python file. "
            "External packages and input CSV data are expected separately."
        )
    )
    parser.add_argument("--data-root", type=Path, default=None, help="Input data root. If omitted, ./data next to this file is used when present.")
    parser.add_argument("--output-root", type=Path, default=None, help="Output root. If omitted, pvdiag_results/run_YYYYMMDD_HHMMSS is created next to this file.")
    parser.add_argument("--single-self-test", action="store_true", help="Extract payload and verify the embedded runner without running the algorithm.")
    parser.add_argument("--single-list-payload", action="store_true", help="Print the embedded module/artifact structure and exit.")
    parser.add_argument("--single-extract-source", type=Path, default=None, help="Extract the embedded readable source tree to DIR and exit.")
    parser.add_argument("--single-keep-runtime", action="store_true", help="Keep the extracted temporary runtime folder for debugging.")
    return parser.parse_known_args(argv)


def missing_dependencies() -> list[str]:
    missing: list[str] = []
    for module_name, package_name in REQUIRED_MODULES.items():
        if importlib.util.find_spec(module_name) is None:
            missing.append(package_name)
    return missing


def print_dependency_help(missing: list[str]) -> None:
    print("[pvdiag_single] missing required Python packages:")
    for package in missing:
        print(f"  - {package}")
    print("[pvdiag_single] install example:")
    print("  pip install pandas numpy torch openpyxl tqdm")
    print("[pvdiag_single] after installing packages, run the same command again.")


def print_data_root_help(output_root: Path) -> None:
    print("[pvdiag_single] how to provide input data:")
    print("  1. run with --data-root /path/to/data")
    print("  2. or place a data/ folder next to pvdiag_single.py")
    print("[pvdiag_single] output/log directory:")
    print(f"  {output_root}")


def resolve_data_root(value: Path | None, output_root: Path) -> Path | None:
    if value is not None:
        return value.expanduser().resolve()
    sibling_data = script_dir() / "data"
    if sibling_data.exists():
        return sibling_data.resolve()
    if not sys.stdin.isatty():
        print("[pvdiag_single] data-root was not provided and sibling data/ was not found.")
        print(f"[pvdiag_single] looked for: {sibling_data}")
        print_data_root_help(output_root)
        return None
    try:
        typed = input("[pvdiag_single] Input data-root folder path: ").strip()
    except EOFError as exc:
        print("[pvdiag_single] data-root was not provided and interactive input is unavailable.")
        print(f"[pvdiag_single] looked for: {sibling_data}")
        print_data_root_help(output_root)
        return None
    if not typed:
        print("[pvdiag_single] data-root is required.")
        print_data_root_help(output_root)
        return None
    return Path(typed).expanduser().resolve()


def resolve_output_root(value: Path | None) -> Path:
    if value is not None:
        output_root = value.expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = script_dir() / "pvdiag_results" / f"run_{stamp}"
    output_root.mkdir(parents=True, exist_ok=True)
    return output_root


def single_source_path() -> Path:
    try:
        return Path(__file__).resolve()
    except NameError:
        return Path(sys.argv[0]).resolve()


def load_embedded_payload_from_source() -> tuple[dict[str, str], dict[str, str]]:
    source = single_source_path()
    try:
        source_lines = source.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SystemExit(f"could not read generated single-file source: {source}") from exc

    start_prefix = "# pvdiag_payload_file "
    line_prefix = "#|"
    payload: dict[str, str] = {}
    hashes: dict[str, str] = {}
    current_meta: dict[str, object] | None = None
    current_lines: list[str] = []

    for line_no, line in enumerate(source_lines, start=1):
        if line.startswith(start_prefix):
            if current_meta is not None:
                raise SystemExit(f"nested embedded payload block at line {line_no}")
            try:
                current_meta = json.loads(line[len(start_prefix) :])
            except json.JSONDecodeError as exc:
                raise SystemExit(f"invalid embedded payload metadata at line {line_no}") from exc
            current_lines = []
            continue
        if line == "# pvdiag_payload_end":
            if current_meta is None:
                raise SystemExit(f"embedded payload end without start at line {line_no}")
            path = str(current_meta.get("path", ""))
            if not path:
                raise SystemExit(f"embedded payload metadata missing path before line {line_no}")
            text = "\n".join(current_lines)
            if bool(current_meta.get("endswith_newline", False)):
                text += "\n"
            payload[path] = text
            hashes[path] = str(current_meta.get("sha256", ""))
            current_meta = None
            current_lines = []
            continue
        if current_meta is not None:
            if not line.startswith(line_prefix):
                raise SystemExit(f"embedded payload source line missing '#|' prefix at line {line_no}")
            current_lines.append(line[len(line_prefix) :])

    if current_meta is not None:
        raise SystemExit("unterminated embedded payload block")
    if not payload:
        raise SystemExit("generated single-file source does not contain readable embedded payload blocks")
    return payload, hashes


def embedded_payload_bytes() -> bytes:
    return b"".join(
        path.encode("utf-8") + b"\0" + text.encode("utf-8") + b"\0"
        for path, text in sorted(EMBEDDED_TEXT_FILES.items())
    )


def verify_embedded_payload() -> None:
    if len(EMBEDDED_TEXT_FILES) != PAYLOAD_FILE_COUNT:
        raise SystemExit(
            f"embedded payload file-count mismatch: expected {PAYLOAD_FILE_COUNT}, got {len(EMBEDDED_TEXT_FILES)}"
        )
    payload_bytes = embedded_payload_bytes()
    if len(payload_bytes) != PAYLOAD_TEXT_BYTES:
        raise SystemExit(
            f"embedded payload byte mismatch: expected {PAYLOAD_TEXT_BYTES}, got {len(payload_bytes)}"
        )
    digest = hashlib.sha256(payload_bytes).hexdigest()
    if digest != PAYLOAD_TEXT_SHA256:
        raise SystemExit(f"embedded payload sha256 mismatch: expected {PAYLOAD_TEXT_SHA256}, got {digest}")
    for path, text in EMBEDDED_TEXT_FILES.items():
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        expected = EMBEDDED_FILE_SHA256.get(path)
        if expected != digest:
            raise SystemExit(f"embedded file sha256 mismatch: {path}")


def safe_target(runtime_root: Path, embedded_path: str) -> Path:
    target = (runtime_root / embedded_path).resolve()
    runtime_root_resolved = runtime_root.resolve()
    if target != runtime_root_resolved and not str(target).startswith(str(runtime_root_resolved) + os.sep):
        raise SystemExit(f"unsafe embedded path: {embedded_path}")
    return target


def extract_embedded_files(runtime_root: Path) -> None:
    verify_embedded_payload()
    runtime_root.mkdir(parents=True, exist_ok=True)
    for embedded_path, text in EMBEDDED_TEXT_FILES.items():
        target = safe_target(runtime_root, embedded_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")


def print_payload_index() -> None:
    verify_embedded_payload()
    print("[pvdiag_single] payload structure")
    print(f"[pvdiag_single] note: {PAYLOAD_STRUCTURE_NOTE}")
    print(f"[pvdiag_single] files: {PAYLOAD_FILE_COUNT}, bytes: {PAYLOAD_TEXT_BYTES}")
    for row in PAYLOAD_FILE_INDEX:
        print(
            "[pvdiag_single] "
            f"{row['role']:<34} "
            f"{row['bytes']:>8} bytes "
            f"{row['sha256'][:12]} "
            f"{row['path']}"
        )
    print("[pvdiag_single] readable source extraction:")
    print("  python pvdiag_single.py --single-extract-source /tmp/pvdiag_single_source")


def extract_source_tree(destination: Path) -> None:
    target_root = destination.expanduser().resolve()
    if target_root.exists() and not target_root.is_dir():
        raise SystemExit(f"source extraction target is not a directory: {target_root}")
    extract_embedded_files(target_root)
    runner = target_root / "release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py"
    engine = target_root / "release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py"
    print("[pvdiag_single] source extraction ok")
    print(f"[pvdiag_single] extracted files: {PAYLOAD_FILE_COUNT}")
    print(f"[pvdiag_single] source root: {target_root}")
    print(f"[pvdiag_single] runner: {runner}")
    print(f"[pvdiag_single] core engine: {engine}")


def inner_runner(runtime_root: Path) -> Path:
    path = runtime_root / "release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py"
    if not path.exists():
        raise SystemExit(f"embedded runner not found after extraction: {path}")
    return path


def has_option(args: list[str], option: str) -> bool:
    return any(token == option or token.startswith(option + "=") for token in args)


def run_command(cmd: list[str], output_root: Path) -> int:
    log_path = output_root / "pvdiag_single_run.log"
    print("[pvdiag_single] command:", flush=True)
    print(" ".join(str(part) for part in cmd), flush=True)
    print(f"[pvdiag_single] log: {log_path}", flush=True)
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            cmd,
            cwd=Path.cwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="", flush=True)
            log.write(line)
        return proc.wait()


def main(argv: list[str] | None = None) -> int:
    args, passthrough = parse_args(argv)
    if args.single_list_payload:
        print_payload_index()
        return 0
    if args.single_extract_source is not None:
        extract_source_tree(args.single_extract_source)
        return 0

    runtime_root: Path
    cleanup_runtime = not args.single_keep_runtime
    temp_obj = None
    if cleanup_runtime:
        temp_obj = tempfile.TemporaryDirectory(prefix="pvdiag_single_runtime_")
        runtime_root = Path(temp_obj.name)
    else:
        runtime_root = Path(tempfile.mkdtemp(prefix="pvdiag_single_runtime_keep_"))

    try:
        extract_embedded_files(runtime_root)
        runner = inner_runner(runtime_root)
        if args.single_self_test:
            print("[pvdiag_single] self-test ok")
            print(f"[pvdiag_single] generated_at_utc: {GENERATED_AT_UTC}")
            print(f"[pvdiag_single] payload_mode: {PAYLOAD_MODE}")
            print(f"[pvdiag_single] payload_files: {PAYLOAD_FILE_COUNT}")
            print(f"[pvdiag_single] payload_text_bytes: {PAYLOAD_TEXT_BYTES}")
            print(f"[pvdiag_single] payload_structure_note: {PAYLOAD_STRUCTURE_NOTE}")
            print(f"[pvdiag_single] runtime_root: {runtime_root}")
            print(f"[pvdiag_single] runner: {runner}")
            return 0

        missing = missing_dependencies()
        if missing:
            print_dependency_help(missing)
            if args.single_keep_runtime:
                print(f"[pvdiag_single] kept runtime: {runtime_root}")
            return 2

        output_root = resolve_output_root(args.output_root)
        data_root = resolve_data_root(args.data_root, output_root)
        if data_root is None:
            if args.single_keep_runtime:
                print(f"[pvdiag_single] kept runtime: {runtime_root}")
            return 3
        if not data_root.exists():
            print(f"[pvdiag_single] data-root does not exist: {data_root}")
            print_data_root_help(output_root)
            if args.single_keep_runtime:
                print(f"[pvdiag_single] kept runtime: {runtime_root}")
            return 3

        cmd = [
            sys.executable,
            str(runner),
            "--data-root",
            str(data_root),
            "--output-root",
            str(output_root),
            *passthrough,
        ]
        if not has_option(passthrough, "--workspace-retention"):
            cmd.extend(["--workspace-retention", "result-only"])

        code = run_command(cmd, output_root)
        if code != 0:
            print(f"[pvdiag_single] failed with exit code {code}")
            print(f"[pvdiag_single] log: {output_root / 'pvdiag_single_run.log'}")
            if args.single_keep_runtime:
                print(f"[pvdiag_single] kept runtime: {runtime_root}")
            return code

        print("[pvdiag_single] completed successfully")
        print(f"[pvdiag_single] result root: {output_root}")
        print(f"[pvdiag_single] master report: {output_root / 'result' / 'fault_panel_result_master_report_v1.md'}")
        print(f"[pvdiag_single] detailed xlsx: {output_root / 'result' / 'fault_panel_result_detailed_report_v1.xlsx'}")
        return 0
    finally:
        if temp_obj is not None:
            temp_obj.cleanup()
        elif cleanup_runtime and runtime_root.exists():
            shutil.rmtree(runtime_root, ignore_errors=True)


# region Embedded readable source payload (auto-generated; collapse this block in VS Code)
# The lines below are the original payload files, stored as readable comments.
# Each '#|' line becomes one source line when pvdiag_single.py restores the runtime.
# Use --single-list-payload to inspect roles or --single-extract-source DIR to unpack normal files.
# -----------------------------------------------------------------------------
# region payload: entry_runner
# pvdiag_payload_file {"bytes": 168800, "endswith_newline": true, "lines": 3601, "path": "release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py", "role": "entry_runner", "sha256": "21ab958f989db374028b1e96755a46f4f65d09fe391252e08f590b4e21ccd920"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|import argparse
#|import hashlib
#|import json
#|import re
#|import shutil
#|import subprocess
#|import sys
#|from datetime import datetime, timezone
#|from pathlib import Path
#|
#|import pandas as pd
#|
#|PACKAGE_ROOT = Path(__file__).resolve().parents[1]
#|if str(PACKAGE_ROOT) not in sys.path:
#|    sys.path.insert(0, str(PACKAGE_ROOT))
#|from research.prognostics.heuristic_display_registry_v1 import (
#|    DISPLAY_HEURISTIC_NAME_MAP,
#|    HEURISTIC_DISPLAY_NOTE_MAP,
#|    display_heuristic_name as shared_display_heuristic_name,
#|    display_heuristic_note as shared_display_heuristic_note,
#|)
#|
#|DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
#|DEFAULT_SITES = ["conalog", "gangui", "ktc_ess"]
#|CORE_DIGEST_COLUMNS = [
#|    "date",
#|    "panel_id",
#|    "confirmed_fault",
#|    "critical_fault",
#|    "critical_source",
#|    "final_fault",
#|    "anom_level",
#|    "anom_subtype",
#|]
#|LIVE_FAULT_COMPARE_COLS = [
#|    "site",
#|    "panel_id",
#|    "패널고장여부_ko",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "커널로그_원인군_ko",
#|    "1순위_의심원인_ko",
#|    "2순위_의심원인_ko",
#|    "3순위_의심원인_ko",
#|]
#|LIVE_FAULT_OUTPUT_COLS = [
#|    *LIVE_FAULT_COMPARE_COLS,
#|    "전조날짜",
#|    "고장날짜",
#|]
#|LIVE_PREVIEW_OUTPUT_COLS = [
#|    "site",
#|    "panel_id",
#|    "패널고장여부_ko",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "전조날짜",
#|    "고장날짜",
#|    "라벨된 fault",
#|    "1순위_의심원인_ko",
#|    "2순위_의심원인_ko",
#|    "3순위_의심원인_ko",
#|    "커널로그 기존 알고리즘",
#|]
#|USER_PREVIEW_OUTPUT_COLS = [
#|    "site",
#|    "panel_id",
#|    "전조날짜",
#|    "고장 기준일",
#|    "운영 판정",
#|    "급락 종결 관측",
#|    "점진 저하 누적",
#|    "사건 종결 요약",
#|    "상위 해석 후보",
#|    "기존 알고리즘 source",
#|]
#|SIGNAL_PREVIEW_OUTPUT_COLS = [
#|    "site",
#|    "panel_id",
#|    "전조날짜",
#|    "신호 기준일",
#|    "운영 판정",
#|    "급락 종결 관측",
#|    "점진 저하 누적",
#|    "사건 종결 요약",
#|    "상위 해석 후보",
#|    "기존 알고리즘 source",
#|]
#|PRECURSOR_REPORT_OUTPUT_COLS = [
#|    "site",
#|    "panel_id",
#|    "운영 판정",
#|    "판정 근거",
#|    "전조날짜",
#|    "전조 축",
#|    "대표 전조 신호",
#|    "전조 요약",
#|    "상위 해석 후보",
#|    "기존 알고리즘 source",
#|    "패턴 설명",
#|    "모니터링 권고",
#|    "공통원인 위험",
#|    "권고 검토 레인",
#|    "EWS 전조 일수",
#|    "pre_alarm 일수",
#|    "pre_ews 일수",
#|    "Option B 유효 일수",
#|    "공통원인 겹침 일수",
#|    "AE 전조 조건 일수",
#|    "DTW 전조 조건 일수",
#|]
#|FAULT_SIGNAL_REPORT_OUTPUT_COLS = [
#|    "site",
#|    "group root",
#|    "subgroup base",
#|    "subgroup cluster",
#|    "panel_id",
#|    "동일 subgroup row 수",
#|    "동일 cluster row 수",
#|    "운영 판정",
#|    "확정 경로",
#|    "고장 신호 요약",
#|    "전조 시작일",
#|    "신호 기준일",
#|    "사건유형",
#|    "사건 종결 요약",
#|    "근접 공통원인",
#|    "상위 해석 후보",
#|    "기존 알고리즘 source",
#|    "패턴 설명",
#|    "현장 점검 권고",
#|]
#|ROOT_LIVE_FAULT_NAME = "fault_panel_result_current_v1.csv"
#|ROOT_LIVE_PREVIEW_NAME = "fault_panel_result_current_preview_v1.csv"
#|ROOT_LIVE_SUMMARY_NAME = "live_chain_summary_v1.json"
#|ROOT_LIVE_REPORT_NAME = "fault_panel_result_current_report_v1.md"
#|ROOT_RAWONLY_FAULT_NAME = "fault_panel_result_raw_only_current_v1.csv"
#|ROOT_RAWONLY_PREVIEW_NAME = "fault_panel_result_raw_only_current_preview_v1.csv"
#|ROOT_RAWONLY_SUMMARY_NAME = "raw_only_chain_summary_v1.json"
#|ROOT_RAWONLY_REPORT_NAME = "fault_panel_result_raw_only_current_report_v1.md"
#|ROOT_MASTER_REPORT_NAME = "fault_panel_result_master_report_v1.md"
#|ROOT_DETAILED_REPORT_NAME = "fault_panel_result_detailed_report_v1.xlsx"
#|ROOT_PRECURSOR_REPORT_NAME = "fault_panel_result_precursor_report_v1.csv"
#|ROOT_FAULT_SIGNAL_REPORT_NAME = "fault_panel_result_raw_only_fault_signal_report_v1.csv"
#|RAW_ONLY_STRICT_CURRENT_GRADES = {"확정"}
#|FAULT_SIGNAL_CLUSTER_GAP_DAYS = 3
#|MAIL_BUCKET_ALGORITHM_MAP = {
#|    ("conalog", "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0"): "panel-bypass",
#|    ("conalog", "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"): "disconnection",
#|    ("gangui", "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7"): "panel-bypass",
#|    ("gangui", "bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16"): "panel-bypass",
#|    ("ktc_ess", "10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12"): "panel-bypass",
#|    ("ktc_ess", "70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4"): "panel-bypass",
#|}
#|
#|
#|def parse_args() -> argparse.Namespace:
#|    parser = argparse.ArgumentParser(
#|        description=(
#|            "Run the real panel_day_engine.py for the packaged baseline sites under a data root, "
#|            "export the fixed fault result artifacts, and write a shadow-compare report for engine core outputs."
#|        )
#|    )
#|    parser.add_argument(
#|        "--data-root",
#|        type=Path,
#|        required=True,
#|        help="Folder containing site/raw subdirectories such as data-root/conalog/raw.",
#|    )
#|    parser.add_argument(
#|        "--output-root",
#|        type=Path,
#|        required=True,
#|        help="Folder where site-wise engine outputs and fixed result tables will be written.",
#|    )
#|    parser.add_argument(
#|        "--sites",
#|        default=",".join(DEFAULT_SITES),
#|        help="Comma-separated site list. Defaults to conalog,gangui,ktc_ess.",
#|    )
#|    parser.add_argument(
#|        "--train-days",
#|        type=int,
#|        default=60,
#|        help="Maximum number of early days to reserve for training window proposal.",
#|    )
#|    parser.add_argument("--pattern", default="*.csv", help="Filename pattern for raw daily CSVs.")
#|    parser.add_argument("--epochs", type=int, default=40, help="Engine epochs. Defaults to panel_day_engine.py default.")
#|    parser.add_argument("--latent", type=int, default=16, help="Engine latent size. Defaults to panel_day_engine.py default.")
#|    parser.add_argument("--device", default="cpu", help="Torch device to pass through to panel_day_engine.py.")
#|    parser.add_argument(
#|        "--prefer-existing-site-outs",
#|        choices=["auto", "on", "off"],
#|        default="auto",
#|        help=(
#|            "Whether to automatically reuse data-root/<site>/out when available. "
#|            "Defaults to auto."
#|        ),
#|    )
#|    parser.add_argument(
#|        "--reuse-existing-site-outs-root",
#|        type=Path,
#|        default=None,
#|        help=(
#|            "Optional root containing precomputed data/<site>/out trees. "
#|            "When provided, the runner copies those outputs into the runtime workspace and skips engine execution."
#|        ),
#|    )
#|    parser.add_argument(
#|        "--run-live-chain",
#|        choices=["on", "off"],
#|        default="on",
#|        help="After engine execution, run the packaged bootstrap verdict -> audit -> final verdict live chain. Defaults to on.",
#|    )
#|    parser.add_argument(
#|        "--run-raw-only-chain",
#|        choices=["on", "off"],
#|        default="on",
#|        help="After engine execution, run the packaged raw-only audit -> verdict -> heuristic chain. Defaults to on.",
#|    )
#|    parser.add_argument(
#|        "--workspace-retention",
#|        choices=["full", "result-only"],
#|        default="full",
#|        help=(
#|            "Controls post-run retention for large intermediate workspaces. "
#|            "full keeps the historical behavior. result-only keeps result artifacts and share outputs, "
#|            "then removes duplicate site/output and chain data copies."
#|        ),
#|    )
#|    parser.add_argument("--dry-run", action="store_true", help="Validate paths and emit the execution plan without running the engine.")
#|    return parser.parse_args()
#|
#|
#|def package_root() -> Path:
#|    return Path(__file__).resolve().parents[1]
#|
#|
#|def engine_path() -> Path:
#|    return package_root() / "pv_ae" / "panel_day_engine.py"
#|
#|
#|def fixed_fault6_table_path() -> Path:
#|    return package_root() / "artifacts" / "fault6_fixed_result_table_v1.csv"
#|
#|
#|def fixed_fault6_preview_path() -> Path:
#|    return package_root() / "artifacts" / "fault6_label_and_algorithm_preview_v1.csv"
#|
#|
#|def baseline_manifest_path() -> Path:
#|    return package_root() / "artifacts" / "input_baseline_manifest_v1.json"
#|
#|
#|def baseline_core_digest_path() -> Path:
#|    return package_root() / "artifacts" / "panel_day_core_baseline_digest_v1.json"
#|
#|
#|def fault6_provenance_path() -> Path:
#|    return package_root() / "artifacts" / "fault6_fixed_result_provenance_v1.json"
#|
#|
#|def dependency_audit_json_path() -> Path:
#|    return package_root() / "artifacts" / "runtime_chain_dependency_audit_v1.json"
#|
#|
#|def dependency_audit_md_path() -> Path:
#|    return package_root() / "artifacts" / "runtime_chain_dependency_audit_v1.md"
#|
#|
#|def optional_artifact_path_text(path: Path) -> str:
#|    return str(path) if path.exists() else ""
#|
#|
#|def packaged_share_root() -> Path:
#|    return package_root() / "_share"
#|
#|
#|def packaged_pipeline_root() -> Path:
#|    return package_root() / "research" / "prognostics"
#|
#|
#|def packaged_script_path(name: str) -> Path:
#|    return packaged_pipeline_root() / name
#|
#|
#|def extract_date_from_name(path: Path) -> pd.Timestamp:
#|    match = DATE_RE.search(path.name)
#|    if not match:
#|        return pd.NaT
#|    return pd.to_datetime(match.group(1), errors="coerce").normalize()
#|
#|
#|def normalize_sites(raw_sites: str) -> list[str]:
#|    sites = [token.strip() for token in str(raw_sites).split(",") if token.strip()]
#|    if not sites:
#|        raise SystemExit("at least one site must be provided")
#|    return sites
#|
#|
#|def scan_site_files(data_root: Path, site: str, pattern: str) -> tuple[pd.Timestamp, pd.Timestamp, list[Path]]:
#|    raw_dir = data_root / site / "raw"
#|    if not raw_dir.exists():
#|        raise SystemExit(f"missing raw dir for site={site}: {raw_dir}")
#|    files = sorted(path for path in raw_dir.glob(pattern) if path.is_file() and path.suffix.lower() == ".csv")
#|    if not files:
#|        raise SystemExit(f"raw csv not found for site={site}: {raw_dir}")
#|    valid_dates = [value for value in (extract_date_from_name(path) for path in files) if pd.notna(value)]
#|    if not valid_dates:
#|        raise SystemExit(f"no YYYY-MM-DD found in filenames for site={site}: {raw_dir}")
#|    return min(valid_dates), max(valid_dates), files
#|
#|
#|def propose_windows(min_date: pd.Timestamp, max_date: pd.Timestamp, train_days: int) -> dict[str, str]:
#|    span_days = int((max_date - min_date).days)
#|    proposed = min(int(train_days) - 1, max(14, int(span_days * 0.30)))
#|    if proposed < 1:
#|        proposed = 1
#|
#|    train_start = min_date
#|    train_end = min_date + pd.Timedelta(days=proposed)
#|    if train_end >= max_date:
#|        train_end = max_date - pd.Timedelta(days=1)
#|    if train_end < min_date:
#|        raise SystemExit("date span too short to propose train/eval windows")
#|
#|    eval_start = train_end + pd.Timedelta(days=1)
#|    eval_end = max_date
#|    if eval_start > eval_end:
#|        raise SystemExit("date span too short to propose eval window")
#|
#|    return {
#|        "train_start": str(train_start.date()),
#|        "train_end": str(train_end.date()),
#|        "eval_start": str(eval_start.date()),
#|        "eval_end": str(eval_end.date()),
#|        "input_date_min": str(min_date.date()),
#|        "input_date_max": str(max_date.date()),
#|    }
#|
#|
#|def site_manifest(files: list[Path]) -> dict[str, object]:
#|    date_tokens = [match.group(1) for path in files if (match := DATE_RE.search(path.name))]
#|    return {
#|        "file_count": int(len(files)),
#|        "total_bytes": int(sum(path.stat().st_size for path in files)),
#|        "first_filenames": [path.name for path in files[:5]],
#|        "last_filenames": [path.name for path in files[-5:]],
#|        "min_date": min(date_tokens) if date_tokens else "",
#|        "max_date": max(date_tokens) if date_tokens else "",
#|    }
#|
#|
#|def build_site_plan(args: argparse.Namespace, site: str) -> tuple[dict[str, object], list[str]]:
#|    data_root = args.data_root.expanduser().resolve()
#|    output_root = args.output_root.expanduser().resolve()
#|    site_output_dir = output_root / "sites" / site / "output"
#|    site_log_dir = output_root / "sites" / site / "log"
#|    site_output_dir.mkdir(parents=True, exist_ok=True)
#|    site_log_dir.mkdir(parents=True, exist_ok=True)
#|
#|    min_date, max_date, files = scan_site_files(data_root, site, args.pattern)
#|    windows = propose_windows(min_date, max_date, args.train_days)
#|    cmd = [
#|        sys.executable,
#|        str(engine_path()),
#|        "--site",
#|        site,
#|        "--data-root",
#|        str(data_root),
#|        "--out-dir",
#|        str(site_output_dir),
#|        "--log-dir",
#|        str(site_log_dir),
#|        "--pattern",
#|        args.pattern,
#|        "--train-start",
#|        windows["train_start"],
#|        "--train-end",
#|        windows["train_end"],
#|        "--eval-start",
#|        windows["eval_start"],
#|        "--eval-end",
#|        windows["eval_end"],
#|        "--epochs",
#|        str(args.epochs),
#|        "--latent",
#|        str(args.latent),
#|        "--device",
#|        args.device,
#|    ]
#|    plan = {
#|        "site": site,
#|        "raw_dir": str(data_root / site / "raw"),
#|        "output_dir": str(site_output_dir),
#|        "log_dir": str(site_log_dir),
#|        "windows": windows,
#|        "file_manifest": site_manifest(files),
#|        "command": cmd,
#|    }
#|    return plan, cmd
#|
#|
#|def write_json(path: Path, payload: dict[str, object]) -> None:
#|    path.parent.mkdir(parents=True, exist_ok=True)
#|    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
#|
#|
#|def write_text(path: Path, text: str) -> None:
#|    path.parent.mkdir(parents=True, exist_ok=True)
#|    path.write_text(text, encoding="utf-8")
#|
#|
#|def emit_progress(percent: int, message: str) -> None:
#|    safe_percent = max(0, min(100, int(percent)))
#|    print(f"[{safe_percent:03d}%] {message}", flush=True)
#|
#|
#|def load_baseline_manifest() -> dict[str, object]:
#|    path = baseline_manifest_path()
#|    if not path.exists():
#|        raise SystemExit(f"missing packaged baseline manifest: {path}")
#|    return json.loads(path.read_text(encoding="utf-8"))
#|
#|
#|def compare_to_baseline(site_plans: list[dict[str, object]]) -> dict[str, object]:
#|    baseline = load_baseline_manifest()
#|    comparison: dict[str, object] = {"all_sites_match": True, "sites": {}}
#|    baseline_sites = baseline.get("sites", {})
#|    for plan in site_plans:
#|        site = str(plan["site"])
#|        actual = plan["file_manifest"]
#|        expected = baseline_sites.get(site, {})
#|        site_match = True
#|        diffs: list[str] = []
#|        for key in ["file_count", "total_bytes", "min_date", "max_date"]:
#|            if actual.get(key) != expected.get(key):
#|                site_match = False
#|                diffs.append(f"{key}: expected={expected.get(key)} actual={actual.get(key)}")
#|        comparison["sites"][site] = {
#|            "match": site_match,
#|            "expected": expected,
#|            "actual": actual,
#|            "diffs": diffs,
#|        }
#|        if not site_match:
#|            comparison["all_sites_match"] = False
#|    comparison["note_ko"] = (
#|        "all_sites_match=1 이면 packaged fixed result table을 만든 baseline raw corpus와 현재 입력의 경량 fingerprint가 일치한다. "
#|        "일치하지 않으면 engine은 실행될 수 있어도 fixed result table exact replay 보장은 약해진다."
#|    )
#|    return comparison
#|
#|
#|def copy_fixed_results(output_root: Path) -> dict[str, str]:
#|    output_dir = output_root / "result"
#|    output_dir.mkdir(parents=True, exist_ok=True)
#|    fault6_dest = output_dir / "fault6_fixed_result_table_v1.csv"
#|    preview_dest = output_dir / "fault6_label_and_algorithm_preview_v1.csv"
#|    shutil.copy2(fixed_fault6_table_path(), fault6_dest)
#|    if fixed_fault6_preview_path().exists():
#|        preview_df = pd.read_csv(fixed_fault6_preview_path(), encoding="utf-8-sig", low_memory=False)
#|        to_user_preview_schema(preview_df).to_csv(preview_dest, index=False, encoding="utf-8-sig")
#|    return {
#|        "fault6_fixed_result_table_v1": str(fault6_dest),
#|        "fault6_label_and_algorithm_preview_v1": str(preview_dest),
#|    }
#|
#|
#|def copy_tree(source: Path, target: Path) -> None:
#|    if not source.exists():
#|        raise SystemExit(f"missing source tree: {source}")
#|    target.parent.mkdir(parents=True, exist_ok=True)
#|    shutil.copytree(source, target, dirs_exist_ok=True)
#|
#|
#|def path_size_bytes(path: Path) -> int:
#|    if not path.exists():
#|        return 0
#|    if path.is_file() or path.is_symlink():
#|        return int(path.lstat().st_size)
#|    total = 0
#|    for child in path.rglob("*"):
#|        try:
#|            total += int(child.lstat().st_size)
#|        except OSError:
#|            continue
#|    return total
#|
#|
#|def remove_workspace_path(path: Path) -> dict[str, object]:
#|    exists_before = path.exists() or path.is_symlink()
#|    size_before = path_size_bytes(path)
#|    if exists_before:
#|        if path.is_dir() and not path.is_symlink():
#|            shutil.rmtree(path)
#|        else:
#|            path.unlink()
#|    return {
#|        "path": str(path),
#|        "exists_before": bool(exists_before),
#|        "size_bytes_before": int(size_before),
#|        "removed": bool(exists_before),
#|    }
#|
#|
#|def apply_workspace_retention(output_root: Path, retention: str) -> dict[str, object]:
#|    report: dict[str, object] = {
#|        "workspace_retention": retention,
#|        "status": "full_workspace_retained",
#|        "removed_paths": [],
#|        "kept_paths": [
#|            str(output_root / "result"),
#|            str(output_root / "shadow_compare_v1.json"),
#|            str(output_root / "run_metadata_v1.json"),
#|        ],
#|        "bytes_removed_estimate": 0,
#|        "note_ko": (
#|            "full 모드는 기존처럼 site output/workspace data를 모두 보존한다. "
#|            "result-only 모드는 재생성 가능한 대용량 중복 data copy만 제거하고 result 및 _share 산출물은 보존한다."
#|        ),
#|    }
#|    if retention == "full":
#|        return report
#|
#|    removable_paths = [
#|        output_root / "sites",
#|        output_root / "live_chain_workspace" / "data",
#|        output_root / "raw_only_chain_workspace" / "data",
#|    ]
#|    removed = [remove_workspace_path(path) for path in removable_paths]
#|    report["removed_paths"] = removed
#|    report["bytes_removed_estimate"] = int(sum(int(item["size_bytes_before"]) for item in removed))
#|    report["status"] = "result_and_share_artifacts_retained"
#|    for share_path in [
#|        output_root / "live_chain_workspace" / "_share",
#|        output_root / "raw_only_chain_workspace" / "_share",
#|    ]:
#|        if share_path.exists():
#|            report["kept_paths"].append(str(share_path))
#|    return report
#|
#|
#|def copy_existing_site_outs(reuse_root: Path, output_root: Path, sites: list[str]) -> dict[str, str]:
#|    copied: dict[str, str] = {}
#|    for site in sites:
#|        source = reuse_root / site / "out"
#|        target = output_root / "sites" / site / "output"
#|        if not source.exists():
#|            raise SystemExit(f"missing precomputed out dir for site={site}: {source}")
#|        if target.exists():
#|            shutil.rmtree(target)
#|        copy_tree(source, target)
#|        copied[site] = str(target)
#|    return copied
#|
#|
#|def site_outs_available(root: Path, sites: list[str]) -> bool:
#|    for site in sites:
#|        if not (root / site / "out" / "panel_day_core.csv").exists():
#|            return False
#|    return True
#|
#|
#|def raw_latest_mtime(root: Path, site: str) -> float | None:
#|    raw_dir = root / site / "raw"
#|    if not raw_dir.exists():
#|        return None
#|    mtimes = [path.stat().st_mtime for path in raw_dir.glob("*.csv") if path.is_file()]
#|    return max(mtimes) if mtimes else None
#|
#|
#|def site_outs_freshness(root: Path, sites: list[str]) -> dict[str, object]:
#|    site_entries: dict[str, object] = {}
#|    all_fresh = True
#|    for site in sites:
#|        out_path = root / site / "out" / "panel_day_core.csv"
#|        raw_mtime = raw_latest_mtime(root, site)
#|        out_exists = out_path.exists()
#|        out_mtime = out_path.stat().st_mtime if out_exists else None
#|        fresh = bool(out_exists and raw_mtime is not None and out_mtime is not None and out_mtime >= raw_mtime)
#|        site_entries[site] = {
#|            "panel_day_core_exists": out_exists,
#|            "raw_latest_mtime": raw_mtime,
#|            "panel_day_core_mtime": out_mtime,
#|            "fresh_enough": fresh,
#|        }
#|        if not fresh:
#|            all_fresh = False
#|    return {"all_fresh": all_fresh, "sites": site_entries}
#|
#|
#|def resolve_reuse_existing_site_outs_root(
#|    data_root: Path,
#|    explicit_reuse_root: Path | None,
#|    prefer_existing_site_outs: str,
#|    sites: list[str],
#|) -> tuple[Path | None, str, dict[str, object]]:
#|    if explicit_reuse_root is not None:
#|        return explicit_reuse_root, "explicit", {"mode": "explicit", "sites": {}}
#|
#|    if prefer_existing_site_outs == "off":
#|        return None, "disabled", {"mode": "disabled", "sites": {}}
#|
#|    if site_outs_available(data_root, sites):
#|        freshness = site_outs_freshness(data_root, sites)
#|        if freshness["all_fresh"]:
#|            return data_root, "auto_fresh" if prefer_existing_site_outs == "auto" else "forced_fresh", freshness
#|        if prefer_existing_site_outs == "on":
#|            raise SystemExit(
#|                "prefer-existing-site-outs=on 이지만 data-root/<site>/out 가 raw보다 오래되었음"
#|            )
#|        return None, "auto_stale_out", freshness
#|
#|    if prefer_existing_site_outs == "on":
#|        raise SystemExit(
#|            f"prefer-existing-site-outs=on 이지만 data-root 아래 precomputed out를 찾지 못함: {data_root}"
#|        )
#|
#|    return None, "not_available", {"mode": "not_available", "sites": {}}
#|
#|
#|def normalize_text(value: object) -> str:
#|    if value is None:
#|        return ""
#|    if isinstance(value, float) and pd.isna(value):
#|        return ""
#|    text = str(value).strip()
#|    if text.lower() == "nan":
#|        return ""
#|    return text
#|
#|
#|def truthy_mask(series: pd.Series) -> pd.Series:
#|    lowered = series.astype(str).str.strip().str.lower()
#|    return lowered.isin({"1", "true", "t", "yes"})
#|
#|
#|def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
#|    missing = [column for column in required if column not in df.columns]
#|    if missing:
#|        raise SystemExit(f"{name} missing columns: {missing}")
#|
#|
#|def row_key(site: object, panel_id: object) -> tuple[str, str]:
#|    return normalize_text(site), normalize_text(panel_id)
#|
#|
#|def display_heuristic_name(raw_label: object) -> str:
#|    return shared_display_heuristic_name(raw_label)
#|
#|
#|def display_heuristic_note(raw_label: object) -> str:
#|    return shared_display_heuristic_note(raw_label)
#|
#|
#|def choose_display_precursor_date(
#|    event_type_ko: object,
#|    interpreted_onset_date: object,
#|    first_warning_date: object,
#|) -> str:
#|    if normalize_text(event_type_ko) != "전조형 고장":
#|        return ""
#|    onset_date = normalize_text(interpreted_onset_date)
#|    if onset_date:
#|        return onset_date
#|    return normalize_text(first_warning_date)
#|
#|
#|def choose_display_fault_date(
#|    fault_date: object,
#|    strict_trigger_date: object,
#|    first_final_fault_date: object,
#|) -> str:
#|    for candidate in [fault_date, strict_trigger_date, first_final_fault_date]:
#|        text = normalize_text(candidate)
#|        if text:
#|            return text
#|    return ""
#|
#|
#|def display_preview_precursor_date(value: object) -> str:
#|    text = normalize_text(value)
#|    return text if text else "전조없음"
#|
#|
#|def display_signal_grade(row: pd.Series) -> str:
#|    grade = normalize_text(row.get("운영해석등급_ko"))
#|    if not grade:
#|        grade = normalize_text(row.get("운영 판정"))
#|    if not grade:
#|        grade = normalize_text(row.get("현재상태"))
#|    if grade:
#|        if grade in {"고장 신호 포착", "고장 확정"}:
#|            return "확정"
#|        if grade == "강한 이상징후":
#|            return "고위험 관찰"
#|        if grade == "이상징후":
#|            return "관찰"
#|        return grade
#|    if normalize_text(row.get("패널고장여부_ko")) == "고장":
#|        return "확정"
#|    return ""
#|
#|
#|def display_existing_algorithm_source(value: object) -> str:
#|    text = normalize_text(value)
#|    if not text:
#|        return "미검출"
#|    if text.lower() == "none":
#|        return "미검출"
#|    if text == "기존 알고리즘 미검출":
#|        return "미검출"
#|    return text
#|
#|
#|def as_int(value: object) -> int:
#|    try:
#|        parsed = int(float(value))
#|    except (TypeError, ValueError):
#|        return 0
#|    return parsed
#|
#|
#|def is_truthy_scalar(value: object) -> bool:
#|    text = normalize_text(value).lower()
#|    return text in {"1", "true", "t", "yes", "y"}
#|
#|
#|def event_summary_from_labels(event_type: object, terminal_pattern: object) -> str:
#|    event = normalize_text(event_type)
#|    terminal = normalize_text(terminal_pattern)
#|    mapping = {
#|        ("전조형 고장", "급격 종료"): "전조 후 급격 종료",
#|        ("전조형 고장", "진행성 악화"): "전조 후 진행 악화",
#|        ("급작 고장", "급작 발생"): "급작 발생",
#|    }
#|    return mapping.get((event, terminal), "")
#|
#|
#|def event_display_fields(record: pd.Series | dict[str, object]) -> dict[str, str]:
#|    existing_abrupt = normalize_text(record.get("급락 종결 관측"))
#|    existing_progressive = normalize_text(record.get("점진 저하 누적"))
#|    existing_summary = normalize_text(record.get("사건 종결 요약"))
#|    if existing_abrupt or existing_progressive or existing_summary:
#|        return {
#|            "급락 종결 관측": existing_abrupt or "없음",
#|            "점진 저하 누적": existing_progressive or "없음",
#|            "사건 종결 요약": existing_summary,
#|        }
#|
#|    event_type = normalize_text(record.get("사건유형_ko")) or normalize_text(record.get("사건 해석"))
#|    terminal_pattern = normalize_text(record.get("최종고장양상_ko")) or normalize_text(
#|        record.get("최종고장양상")
#|    )
#|    precursor_date = display_preview_precursor_date(record.get("전조날짜"))
#|    grade = normalize_text(record.get("운영해석등급_ko")) or normalize_text(record.get("운영 판정"))
#|    if not grade and isinstance(record, pd.Series):
#|        grade = display_signal_grade(record)
#|
#|    abrupt_observed = (
#|        terminal_pattern in {"급격 종료", "급작 발생"}
#|        or as_int(record.get("final_days")) > 0
#|        or is_truthy_scalar(record.get("대표final_fault"))
#|        or is_truthy_scalar(record.get("final_fault"))
#|    )
#|    progressive_observed = (
#|        terminal_pattern == "진행성 악화"
#|        or event_type == "전조형 고장"
#|        or "degradation" in normalize_text(record.get("anom_subtypes_csv")).lower()
#|        or "degradation" in normalize_text(record.get("대표anom_subtype")).lower()
#|        or as_int(record.get("ews_warning_days")) > 0
#|        or as_int(record.get("pre_alarm_days")) > 0
#|        or as_int(record.get("pre_ews_days")) > 0
#|        or as_int(record.get("prefault_cond_ae_days")) > 0
#|        or as_int(record.get("prefault_cond_dtw_days")) > 0
#|        or precursor_date != "전조없음"
#|    )
#|
#|    summary = ""
#|    if grade == "확정" or normalize_text(record.get("패널고장여부_ko")) == "고장":
#|        summary = event_summary_from_labels(event_type, terminal_pattern)
#|        if not summary:
#|            if abrupt_observed and progressive_observed and precursor_date != "전조없음":
#|                summary = "전조 후 급격 종료"
#|            elif progressive_observed and precursor_date != "전조없음":
#|                summary = "전조 후 진행 악화"
#|            elif abrupt_observed:
#|                summary = "급작 발생" if precursor_date == "전조없음" else "급격 종료 관측"
#|
#|    return {
#|        "급락 종결 관측": "있음" if abrupt_observed else "없음",
#|        "점진 저하 누적": "있음" if progressive_observed else "없음",
#|        "사건 종결 요약": summary,
#|    }
#|
#|
#|def has_precursor_signal(record: dict[str, object] | pd.Series) -> bool:
#|    if normalize_text(record.get("전조날짜")):
#|        return True
#|    for field in [
#|        "ews_warning_days",
#|        "pre_alarm_days",
#|        "pre_ews_days",
#|        "prefault_cond_ae_days",
#|        "prefault_cond_dtw_days",
#|        "prefault_cond_ews_days",
#|    ]:
#|        if as_int(record.get(field)) > 0:
#|            return True
#|    return False
#|
#|
#|def has_hard_fault_evidence(record: dict[str, object] | pd.Series) -> bool:
#|    return any(
#|        [
#|            as_int(record.get("final_days")) > 0,
#|            as_int(record.get("critical_days")) > 0,
#|            as_int(record.get("critical_confirmed_days")) > 0,
#|            is_truthy_scalar(record.get("final_fault")),
#|            is_truthy_scalar(record.get("critical_fault")),
#|            is_truthy_scalar(record.get("critical_confirmed")),
#|            is_truthy_scalar(record.get("대표final_fault")),
#|            is_truthy_scalar(record.get("대표critical_fault")),
#|            is_truthy_scalar(record.get("대표critical_confirmed")),
#|        ]
#|    )
#|
#|
#|def as_float(value: object) -> float | None:
#|    try:
#|        parsed = float(value)
#|    except (TypeError, ValueError):
#|        return None
#|    if pd.isna(parsed):
#|        return None
#|    return parsed
#|
#|
#|def format_ratio(value: object, digits: int = 2) -> str:
#|    parsed = as_float(value)
#|    if parsed is None:
#|        return ""
#|    return f"{parsed:.{digits}f}"
#|
#|
#|def representative_signal_row(panel_core: pd.DataFrame) -> pd.Series:
#|    panel_df = panel_core.sort_values("date").copy()
#|    if panel_df.empty:
#|        return pd.Series(dtype=object)
#|    subtype_mask = panel_df.get("anom_subtype", pd.Series(dtype=object)).astype(str).str.contains(
#|        "degradation|fault_like|shadow_like|critical|confirmed_fault",
#|        case=False,
#|        na=False,
#|    )
#|    signal_mask = (
#|        truthy_mask(panel_df["final_fault"])
#|        | truthy_mask(panel_df["critical_fault"])
#|        | truthy_mask(panel_df["fault_like_day"])
#|        | truthy_mask(panel_df.get("event_A", pd.Series(False, index=panel_df.index)))
#|        | subtype_mask
#|    )
#|    focus_df = panel_df.loc[signal_mask].copy()
#|    if focus_df.empty:
#|        focus_df = panel_df.copy()
#|    if "mid_ratio" in focus_df.columns and focus_df["mid_ratio"].notna().any():
#|        return focus_df.sort_values(["mid_ratio", "date"], ascending=[True, True]).iloc[0]
#|    if "dtw_dist" in focus_df.columns and focus_df["dtw_dist"].notna().any():
#|        return focus_df.sort_values(["dtw_dist", "date"], ascending=[False, True]).iloc[0]
#|    return focus_df.iloc[0]
#|
#|
#|def signal_grade_explainer(evidence_row: dict[str, object]) -> str:
#|    text = normalize_text(evidence_row.get("운영해석등급_ko"))
#|    final_days = int(evidence_row.get("final_days", 0) or 0)
#|    critical_days = int(evidence_row.get("critical_days", 0) or 0)
#|    critical_confirmed_days = int(evidence_row.get("critical_confirmed_days", 0) or 0)
#|    ews_warning_days = int(evidence_row.get("ews_warning_days", 0) or 0)
#|    pre_alarm_days = int(evidence_row.get("pre_alarm_days", 0) or 0)
#|    pre_ews_days = int(evidence_row.get("pre_ews_days", 0) or 0)
#|    prefault_cond_ae_days = int(evidence_row.get("prefault_cond_ae_days", 0) or 0)
#|    prefault_cond_dtw_days = int(evidence_row.get("prefault_cond_dtw_days", 0) or 0)
#|    critical_sources = normalize_text(evidence_row.get("critical_sources_csv"))
#|    if text == "확정":
#|        signal_labels: list[str] = []
#|        if final_days > 0:
#|            signal_labels.append("최종 고장 신호")
#|        if critical_confirmed_days > 0:
#|            signal_labels.append("강한 고장 신호 확정")
#|        elif critical_days > 0:
#|            signal_labels.append("강한 고장 신호")
#|        if "vdrop" in critical_sources:
#|            signal_labels.append("vdrop 전기 신호")
#|        signal_summary = " / ".join(signal_labels) if signal_labels else "확정 신호"
#|        return (
#|            f"다음 확정 신호가 관측돼 확정({final_days + critical_days + critical_confirmed_days}일): "
#|            f"{signal_summary}. 원인명은 후보 단계"
#|        )
#|    if text == "고위험 관찰":
#|        return (
#|            f"EWS({ews_warning_days}일)·pre_alarm({pre_alarm_days}일)·pre_ews({pre_ews_days}일)"
#|            f"와 AE/DTW 전조 조건(ae={prefault_cond_ae_days}, dtw={prefault_cond_dtw_days})이 누적돼 강한 이상징후로 분류"
#|        )
#|    if text == "관찰":
#|        return "약한 전조 신호만 보여 계속 관찰이 필요한 상태로 분류"
#|    if normalize_text(evidence_row.get("패널고장여부_ko")) == "고장":
#|        return "고정 결과표 기준 fault. 원인명은 후보 단계"
#|    return ""
#|
#|
#|def pattern_explainer(
#|    evidence_row: dict[str, object], *, soften_hard_language: bool = False
#|) -> str:
#|    mid_v_ratio = as_float(evidence_row.get("대표mid_v_ratio"))
#|    mid_i_ratio = as_float(evidence_row.get("대표mid_i_ratio"))
#|    mid_ratio = as_float(evidence_row.get("대표mid_ratio"))
#|    recon_error = as_float(evidence_row.get("대표recon_error"))
#|    dtw_dist = as_float(evidence_row.get("대표dtw_dist"))
#|    hs_score = as_float(evidence_row.get("대표hs_score"))
#|    critical_source = normalize_text(evidence_row.get("대표critical_source"))
#|    anom_subtype = normalize_text(evidence_row.get("대표anom_subtype"))
#|    final_flag = normalize_text(evidence_row.get("대표final_fault")) == "True"
#|    critical_flag = normalize_text(evidence_row.get("대표critical_fault")) == "True"
#|    event_flag = normalize_text(evidence_row.get("대표event_A")) == "True"
#|
#|    reasons: list[str] = []
#|    if "vdrop" in critical_source:
#|        if soften_hard_language:
#|            reasons.append("상대 전압 이탈 징후가 반복 관측됨")
#|        else:
#|            reasons.append("전압강하형 전기 신호가 직접 관측됨")
#|    if mid_v_ratio is not None and mid_i_ratio is not None:
#|        if mid_v_ratio >= 0.9 and mid_i_ratio <= 0.4:
#|            if soften_hard_language:
#|                reasons.append(
#|                    f"전압 대비 전류 저하 징후가 나타남(mid_v={mid_v_ratio:.2f}, mid_i={mid_i_ratio:.2f})"
#|                )
#|            else:
#|                reasons.append(
#|                    f"전압은 비교적 유지되지만 전류가 크게 낮아짐(mid_v={mid_v_ratio:.2f}, mid_i={mid_i_ratio:.2f})"
#|                )
#|        elif mid_v_ratio <= 0.8 and mid_i_ratio <= 0.8:
#|            if soften_hard_language:
#|                reasons.append(
#|                    f"전압과 전류가 함께 낮아지는 징후가 이어짐(mid_v={mid_v_ratio:.2f}, mid_i={mid_i_ratio:.2f})"
#|                )
#|            else:
#|                reasons.append(
#|                    f"전압과 전류가 함께 낮아짐(mid_v={mid_v_ratio:.2f}, mid_i={mid_i_ratio:.2f})"
#|                )
#|        elif mid_i_ratio <= 0.4:
#|            if soften_hard_language:
#|                reasons.append(f"전류 저하 징후가 두드러짐(mid_i={mid_i_ratio:.2f})")
#|            else:
#|                reasons.append(f"전류가 크게 낮아진 패턴(mid_i={mid_i_ratio:.2f})")
#|    if mid_ratio is not None:
#|        if mid_ratio <= 0.1:
#|            reasons.append(f"중간 출력이 거의 0에 가까움(mid_ratio={mid_ratio:.2f})")
#|        elif mid_ratio <= 0.5:
#|            reasons.append(f"중간 출력이 뚜렷하게 낮아짐(mid_ratio={mid_ratio:.2f})")
#|    if final_flag:
#|        reasons.append("급락 종결 패턴이 직접 관측됨")
#|    elif critical_flag:
#|        reasons.append("critical fault 신호가 직접 나타남")
#|    elif event_flag:
#|        reasons.append("이상 이벤트(event_A)가 반복적으로 나타남")
#|    if "degradation" in anom_subtype:
#|        reasons.append("degradation subtype이 반복돼 점진적 저하 경향이 보임")
#|    if recon_error is not None and recon_error >= 0.05:
#|        reasons.append(f"정상 곡선 대비 복원 오차가 큼(recon={recon_error:.3f})")
#|    if dtw_dist is not None and dtw_dist >= 20:
#|        reasons.append(f"기준 곡선과 형태 차이가 큼(dtw={dtw_dist:.1f})")
#|    if hs_score is not None and hs_score >= 0.3:
#|        reasons.append(f"시계열 흔들림이 큼(hs={hs_score:.3f})")
#|    if not reasons:
#|        reasons.append("대표 관측일의 곡선/출력 변화가 정상 패턴과 다르게 나타남")
#|    return " / ".join(reasons[:3])
#|
#|
#|def to_user_preview_schema(df: pd.DataFrame) -> pd.DataFrame:
#|    if df is None or df.empty:
#|        return pd.DataFrame(columns=USER_PREVIEW_OUTPUT_COLS)
#|
#|    def pick_text(row: pd.Series, *columns: str) -> str:
#|        for column in columns:
#|            if column in row.index:
#|                text = normalize_text(row.get(column))
#|                if text:
#|                    return text
#|        return ""
#|
#|    def pick_algorithm_source(row: pd.Series) -> str:
#|        source = pick_text(
#|            row,
#|            "기존 알고리즘 source",
#|            "커널로그 기존 알고리즘 판정",
#|            "커널로그 기존 알고리즘",
#|            "critical_source",
#|        )
#|        if not source:
#|            source = MAIL_BUCKET_ALGORITHM_MAP.get(
#|                (normalize_text(row.get("site")), normalize_text(row.get("panel_id"))),
#|                "",
#|            )
#|        return display_existing_algorithm_source(source)
#|
#|    rows: list[dict[str, str]] = []
#|    for _, row in df.fillna("").iterrows():
#|        event_fields = event_display_fields(row)
#|        rows.append(
#|            {
#|                "site": normalize_text(row.get("site")),
#|                "panel_id": normalize_text(row.get("panel_id")),
#|                "전조날짜": display_preview_precursor_date(row.get("전조날짜")),
#|                "고장 기준일": pick_text(row, "고장 기준일", "고장날짜", "신호 기준일"),
#|                "운영 판정": display_signal_grade(row),
#|                **event_fields,
#|                "상위 해석 후보": pick_text(
#|                    row,
#|                    "상위 해석 후보",
#|                    "원인 추정",
#|                    "알고리즘 해석 원인",
#|                    "원인",
#|                    "1순위_의심원인_ko",
#|                ),
#|                "기존 알고리즘 source": pick_algorithm_source(row),
#|            }
#|        )
#|    return pd.DataFrame(rows).reindex(columns=USER_PREVIEW_OUTPUT_COLS)
#|
#|
#|def to_signal_preview_schema(df: pd.DataFrame) -> pd.DataFrame:
#|    if df is None or df.empty:
#|        return pd.DataFrame(columns=SIGNAL_PREVIEW_OUTPUT_COLS)
#|
#|    def pick_text(row: pd.Series, *columns: str) -> str:
#|        for column in columns:
#|            if column in row.index:
#|                text = normalize_text(row.get(column))
#|                if text:
#|                    return text
#|        return ""
#|
#|    def pick_algorithm_source(row: pd.Series) -> str:
#|        source = pick_text(
#|            row,
#|            "기존 알고리즘 source",
#|            "커널로그 기존 알고리즘 판정",
#|            "커널로그 기존 알고리즘",
#|            "critical_source",
#|        )
#|        if not source:
#|            source = MAIL_BUCKET_ALGORITHM_MAP.get(
#|                (normalize_text(row.get("site")), normalize_text(row.get("panel_id"))),
#|                "",
#|            )
#|        return display_existing_algorithm_source(source)
#|
#|    rows: list[dict[str, str]] = []
#|    for _, row in df.fillna("").iterrows():
#|        event_fields = event_display_fields(row)
#|        rows.append(
#|            {
#|                "site": normalize_text(row.get("site")),
#|                "panel_id": normalize_text(row.get("panel_id")),
#|                "전조날짜": display_preview_precursor_date(row.get("전조날짜")),
#|                "신호 기준일": pick_text(row, "신호 기준일", "고장날짜", "고장 기준일"),
#|                "운영 판정": display_signal_grade(row),
#|                **event_fields,
#|                "상위 해석 후보": pick_text(
#|                    row,
#|                    "상위 해석 후보",
#|                    "원인 추정",
#|                    "알고리즘 해석 원인",
#|                    "원인",
#|                    "1순위_의심원인_ko",
#|                ),
#|                "기존 알고리즘 source": pick_algorithm_source(row),
#|            }
#|        )
#|    return pd.DataFrame(rows).reindex(columns=SIGNAL_PREVIEW_OUTPUT_COLS)
#|
#|
#|def load_raw_only_common_module():
#|    package = package_root()
#|    if str(package) not in sys.path:
#|        sys.path.insert(0, str(package))
#|    from research.prognostics import runtime_rawonly_chain_common_v1 as raw_only_common_mod
#|
#|    return raw_only_common_mod
#|
#|
#|def load_runtime_heuristic_module():
#|    package = package_root()
#|    if str(package) not in sys.path:
#|        sys.path.insert(0, str(package))
#|    from research.prognostics import (
#|        build_panel_day_engine_runtime_heuristic_v1 as runtime_heuristic_mod,
#|    )
#|
#|    return runtime_heuristic_mod
#|
#|
#|def packaged_live_chain_support() -> dict[str, object]:
#|    required_scripts = [
#|        "build_panel_day_engine_bootstrap_verdict_v1.py",
#|        "build_panel_day_engine_fault_panel_event_audit_v1.py",
#|        "build_panel_day_engine_panel_multiaxis_verdict_v1.py",
#|        "build_panel_day_engine_gpvs_evidence_pack_v1.py",
#|        "build_panel_day_engine_cause_candidate_heuristics_v1.py",
#|    ]
#|    required_share_inputs = [
#|        "panel_day_engine_operator_workflow_default_v1.csv",
#|        "panel_day_engine_abrupt6_symptom_map_v1.csv",
#|        "panel_day_engine_kernellog_project_mapping_v1.csv",
#|        "panel_day_engine_gpv7_perf_summary_v1.csv",
#|        "panel_day_engine_project_final_decision_pack_v1.csv",
#|        "panel_day_engine_precursor_onset_truth_v1.csv",
#|        "panel_day_engine_non_precursor_performance_cases_v1.csv",
#|        "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv",
#|        "panel_day_engine_gpvs_panel_attach_inventory_v1.csv",
#|        "panel_day_engine_gpvs_panel_attach_feasibility_v1.csv",
#|        "panel_day_engine_gpvs_panel_attach_candidates_v1.csv",
#|        "panel_day_engine_precursor_abrupt_consistency_cases_v1.csv",
#|        "panel_day_engine_precursor_abrupt_consistency_summary_v1.csv",
#|        "panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv",
#|        "panel_day_engine_c42997_1_1_forensic_summary_v1.csv",
#|        "panel_day_engine_fault_panel_event_audit_v1.csv",
#|        "panel_day_engine_detailed_fault_bridge_audit_v1.csv",
#|        "panel_day_engine_detailed_fault_bridge_summary_v1.csv",
#|        "panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv",
#|        "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv",
#|        "panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv",
#|        "panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv",
#|        "panel_day_engine_gpvs_canonical_dictionary_v1.csv",
#|        "panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv",
#|        "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv",
#|        "panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv",
#|        "panel_day_engine_gpvs_evidence_pack_v1.csv",
#|        "panel_day_engine_panel_multiaxis_verdict_v1.csv",
#|        "panel_date_reaudit_working.csv",
#|    ]
#|    missing_scripts = [name for name in required_scripts if not packaged_script_path(name).exists()]
#|    missing_share = [name for name in required_share_inputs if not (packaged_share_root() / name).exists()]
#|    supported = not missing_scripts and not missing_share
#|    return {
#|        "supported": supported,
#|        "required_scripts": required_scripts,
#|        "required_share_inputs": required_share_inputs,
#|        "missing_scripts": missing_scripts,
#|        "missing_share_inputs": missing_share,
#|        "note_ko": (
#|            "live chain은 package 내부에 복사된 bootstrap/audit/verdict/evidence/heuristic 스크립트와 "
#|            "frozen share 입력을 사용해 workspace-only로 재계산한다."
#|        ),
#|    }
#|
#|
#|def packaged_raw_only_chain_support() -> dict[str, object]:
#|    required_scripts = [
#|        "runtime_rawonly_chain_common_v1.py",
#|        "build_panel_day_engine_runtime_fault_event_audit_v1.py",
#|        "build_panel_day_engine_runtime_final_verdict_v1.py",
#|        "build_panel_day_engine_runtime_heuristic_v1.py",
#|    ]
#|    missing_scripts = [name for name in required_scripts if not packaged_script_path(name).exists()]
#|    return {
#|        "supported": not missing_scripts,
#|        "required_scripts": required_scripts,
#|        "missing_scripts": missing_scripts,
#|        "note_ko": (
#|            "raw-only chain은 package 내부에 복사된 runtime audit/verdict/heuristic 스크립트만 사용한다. "
#|            "frozen share truth/support asset은 참조하지 않는다."
#|        ),
#|    }
#|
#|
#|def normalize_core_digest_frame(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
#|    ensure_columns(df, CORE_DIGEST_COLUMNS, source_name)
#|    digest_df = df.loc[:, CORE_DIGEST_COLUMNS].copy()
#|    digest_df["date"] = pd.to_datetime(digest_df["date"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
#|    for column in CORE_DIGEST_COLUMNS:
#|        if column == "date":
#|            continue
#|        digest_df[column] = digest_df[column].map(normalize_text)
#|    digest_df["panel_id"] = digest_df["panel_id"].astype(str)
#|    return digest_df.sort_values(["panel_id", "date"]).reset_index(drop=True)
#|
#|
#|def build_core_digest_payload(df: pd.DataFrame, source_name: str) -> dict[str, object]:
#|    digest_df = normalize_core_digest_frame(df, source_name)
#|    joined_rows = "\n".join(
#|        "|".join(normalize_text(value) for value in row)
#|        for row in digest_df.itertuples(index=False, name=None)
#|    )
#|    return {
#|        "columns": CORE_DIGEST_COLUMNS,
#|        "row_count": int(len(digest_df)),
#|        "digest_sha256": hashlib.sha256(joined_rows.encode("utf-8")).hexdigest(),
#|        "critical_source_counts": {
#|            key: int(value)
#|            for key, value in digest_df["critical_source"].value_counts(dropna=False).sort_index().items()
#|        },
#|        "anom_level_counts": {
#|            key: int(value)
#|            for key, value in digest_df["anom_level"].value_counts(dropna=False).sort_index().items()
#|        },
#|        "confirmed_fault_true_count": int(truthy_mask(digest_df["confirmed_fault"]).sum()),
#|        "critical_fault_true_count": int(truthy_mask(digest_df["critical_fault"]).sum()),
#|        "final_fault_true_count": int(truthy_mask(digest_df["final_fault"]).sum()),
#|    }
#|
#|
#|def load_core_baseline_digest() -> dict[str, object]:
#|    path = baseline_core_digest_path()
#|    if not path.exists():
#|        raise SystemExit(f"missing packaged core baseline digest: {path}")
#|    return json.loads(path.read_text(encoding="utf-8"))
#|
#|
#|def compare_single_site_digest(expected: dict[str, object], actual: dict[str, object]) -> list[str]:
#|    diffs: list[str] = []
#|    for key in [
#|        "row_count",
#|        "digest_sha256",
#|        "confirmed_fault_true_count",
#|        "critical_fault_true_count",
#|        "final_fault_true_count",
#|    ]:
#|        if expected.get(key) != actual.get(key):
#|            diffs.append(f"{key}: expected={expected.get(key)} actual={actual.get(key)}")
#|    if expected.get("columns") != actual.get("columns"):
#|        diffs.append("columns: expected reference columns differ from actual columns")
#|    if expected.get("critical_source_counts") != actual.get("critical_source_counts"):
#|        diffs.append("critical_source_counts: expected reference counts differ from actual counts")
#|    if expected.get("anom_level_counts") != actual.get("anom_level_counts"):
#|        diffs.append("anom_level_counts: expected reference counts differ from actual counts")
#|    return diffs
#|
#|
#|def load_panel_day_core_from_workspace(workspace_root: Path, site: str) -> pd.DataFrame:
#|    path = workspace_root / "data" / site / "out" / "panel_day_core.csv"
#|    if not path.exists():
#|        raise SystemExit(f"missing workspace panel_day_core: {path}")
#|    df = pd.read_csv(path, low_memory=False)
#|    ensure_columns(
#|        df,
#|        ["panel_id", "date", "final_fault", "critical_fault", "fault_like_day", "critical_source"],
#|        path.name,
#|    )
#|    df["panel_id"] = df["panel_id"].astype(str)
#|    df["date"] = pd.to_datetime(df["date"], errors="coerce")
#|    return df
#|
#|
#|def representative_algorithm_fields(site: str, core_df: pd.DataFrame, panel_id: str) -> dict[str, str]:
#|    mapped = MAIL_BUCKET_ALGORITHM_MAP.get((normalize_text(site), normalize_text(panel_id)), "")
#|    if mapped:
#|        return {"커널로그 기존 알고리즘": mapped}
#|    panel_df = core_df.loc[core_df["panel_id"].eq(str(panel_id))].copy().sort_values("date")
#|    if panel_df.empty:
#|        return {"커널로그 기존 알고리즘": ""}
#|
#|    final_days = panel_df.loc[truthy_mask(panel_df["final_fault"])]
#|    critical_days = panel_df.loc[truthy_mask(panel_df["critical_fault"])]
#|    fault_like_days = panel_df.loc[truthy_mask(panel_df["fault_like_day"])]
#|
#|    if not final_days.empty:
#|        representative = final_days.iloc[0]
#|    elif not critical_days.empty:
#|        representative = critical_days.iloc[0]
#|    elif not fault_like_days.empty:
#|        representative = fault_like_days.iloc[0]
#|    else:
#|        representative = panel_df.iloc[-1]
#|
#|    return {"커널로그 기존 알고리즘": normalize_text(representative.get("critical_source"))}
#|
#|
#|def build_live_fault_table(workspace_root: Path) -> pd.DataFrame:
#|    verdict_path = workspace_root / "_share" / "panel_day_engine_panel_multiaxis_verdict_v1.csv"
#|    heuristic_path = workspace_root / "_share" / "panel_day_engine_cause_candidate_heuristics_v1.csv"
#|    audit_path = workspace_root / "_share" / "panel_day_engine_fault_panel_event_audit_v1.csv"
#|    verdict_df = pd.read_csv(verdict_path, encoding="utf-8-sig", low_memory=False)
#|    heuristic_df = pd.read_csv(heuristic_path, encoding="utf-8-sig", low_memory=False)
#|    audit_df = pd.read_csv(audit_path, encoding="utf-8-sig", low_memory=False)
#|    ensure_columns(
#|        verdict_df,
#|        ["site", "panel_id", "패널고장여부_ko", "사건유형_ko", "최종고장양상_ko", "커널로그_원인군_ko"],
#|        verdict_path.name,
#|    )
#|    ensure_columns(
#|        heuristic_df,
#|        ["site", "panel_id", "원인후보_top1_ko", "원인후보_top2_ko", "원인후보_top3_ko"],
#|        heuristic_path.name,
#|    )
#|    ensure_columns(
#|        audit_df,
#|        [
#|            "site",
#|            "panel_id",
#|            "earliest_warning_date",
#|            "strict_trigger_date",
#|            "first_final_fault_date",
#|        ],
#|        audit_path.name,
#|    )
#|
#|    heuristic_lookup = {
#|        row_key(row["site"], row["panel_id"]): row
#|        for row in heuristic_df.to_dict(orient="records")
#|    }
#|    audit_lookup = {
#|        row_key(row["site"], row["panel_id"]): row
#|        for row in audit_df.to_dict(orient="records")
#|    }
#|    rows: list[dict[str, str]] = []
#|    for row in verdict_df.loc[verdict_df["패널고장여부_ko"].map(normalize_text).eq("고장")].to_dict(orient="records"):
#|        key = row_key(row["site"], row["panel_id"])
#|        heuristic_row = heuristic_lookup.get(key)
#|        if heuristic_row is None:
#|            raise SystemExit(f"missing heuristic row for fault panel: {key}")
#|        audit_row = audit_lookup.get(key, {})
#|        rows.append(
#|            {
#|                "site": normalize_text(row["site"]),
#|                "panel_id": normalize_text(row["panel_id"]),
#|                "패널고장여부_ko": normalize_text(row["패널고장여부_ko"]),
#|                "사건유형_ko": normalize_text(row["사건유형_ko"]),
#|                "최종고장양상_ko": normalize_text(row["최종고장양상_ko"]),
#|                "커널로그_원인군_ko": normalize_text(row["커널로그_원인군_ko"]),
#|                "1순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top1_ko"]),
#|                "2순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top2_ko"]),
#|                "3순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top3_ko"]),
#|                "전조날짜": choose_display_precursor_date(
#|                    event_type_ko=row.get("사건유형_ko"),
#|                    interpreted_onset_date=row.get("사건해석상전조시작일"),
#|                    first_warning_date=audit_row.get("earliest_warning_date"),
#|                ),
#|                "고장날짜": choose_display_fault_date(
#|                    fault_date=row.get("세부fault_기준일"),
#|                    strict_trigger_date=audit_row.get("strict_trigger_date"),
#|                    first_final_fault_date=audit_row.get("first_final_fault_date"),
#|                ),
#|            }
#|        )
#|    return (
#|        pd.DataFrame(rows)
#|        .reindex(columns=LIVE_FAULT_OUTPUT_COLS)
#|        .sort_values(["site", "panel_id"], ascending=[True, True])
#|        .reset_index(drop=True)
#|    )
#|
#|
#|def build_live_fault_preview(workspace_root: Path, fault_df: pd.DataFrame) -> pd.DataFrame:
#|    per_site_core = {
#|        site: load_panel_day_core_from_workspace(workspace_root, site)
#|        for site in sorted(fault_df["site"].astype(str).unique())
#|    }
#|    rows: list[dict[str, str]] = []
#|    for _, row in fault_df.iterrows():
#|        site = normalize_text(row["site"])
#|        panel_id = normalize_text(row["panel_id"])
#|        rows.append(
#|            {
#|                "site": site,
#|                "panel_id": panel_id,
#|                "패널고장여부_ko": normalize_text(row["패널고장여부_ko"]),
#|                "사건유형_ko": normalize_text(row["사건유형_ko"]),
#|                "최종고장양상_ko": normalize_text(row["최종고장양상_ko"]),
#|                "전조날짜": normalize_text(row.get("전조날짜")),
#|                "고장날짜": normalize_text(row.get("고장날짜")),
#|                "라벨된 fault": normalize_text(row["커널로그_원인군_ko"]),
#|                "1순위_의심원인_ko": normalize_text(row["1순위_의심원인_ko"]),
#|                "2순위_의심원인_ko": normalize_text(row["2순위_의심원인_ko"]),
#|                "3순위_의심원인_ko": normalize_text(row["3순위_의심원인_ko"]),
#|                **representative_algorithm_fields(site, per_site_core[site], panel_id),
#|            }
#|        )
#|    return pd.DataFrame(rows).reindex(columns=LIVE_PREVIEW_OUTPUT_COLS)
#|
#|
#|def compare_live_fault_to_fixed(live_fault_df: pd.DataFrame) -> dict[str, object]:
#|    fixed_path = fixed_fault6_table_path()
#|    if not fixed_path.exists():
#|        return {
#|            "fixed_reference_available": False,
#|            "exact_match": False,
#|            "diff_columns": [],
#|        }
#|    fixed_df = pd.read_csv(fixed_path, encoding="utf-8-sig", low_memory=False).sort_values(["site", "panel_id"]).reset_index(drop=True)
#|    live_df = live_fault_df.sort_values(["site", "panel_id"]).reset_index(drop=True)
#|    diff_columns: list[str] = []
#|    if len(fixed_df) != len(live_df):
#|        diff_columns.append("__row_count__")
#|    else:
#|        for column in LIVE_FAULT_OUTPUT_COLS:
#|            if column not in LIVE_FAULT_COMPARE_COLS:
#|                continue
#|            left = fixed_df[column].fillna("").astype(str)
#|            right = live_df[column].fillna("").astype(str)
#|            if not left.equals(right):
#|                diff_columns.append(column)
#|    return {
#|        "fixed_reference_available": True,
#|        "exact_match": not diff_columns,
#|        "diff_columns": diff_columns,
#|        "fixed_row_count": int(len(fixed_df)),
#|        "live_row_count": int(len(live_df)),
#|    }
#|
#|
#|def publish_live_chain_outputs(output_root: Path, result_dir: Path, summary_path: Path) -> dict[str, str]:
#|    root_result_dir = output_root / "result"
#|    root_result_dir.mkdir(parents=True, exist_ok=True)
#|
#|    mapping = {
#|        result_dir / "fault_panel_result_live_v1.csv": root_result_dir / ROOT_LIVE_FAULT_NAME,
#|        result_dir / "fault_panel_result_live_preview_v1.csv": root_result_dir / ROOT_LIVE_PREVIEW_NAME,
#|    }
#|    published: dict[str, str] = {}
#|    for source, target in mapping.items():
#|        if not source.exists():
#|            raise SystemExit(f"missing live chain output for publish step: {source}")
#|        shutil.copy2(source, target)
#|        published[target.name] = str(target)
#|    return published
#|
#|
#|def publish_raw_only_chain_outputs(output_root: Path, result_dir: Path) -> dict[str, str]:
#|    root_result_dir = output_root / "result"
#|    root_result_dir.mkdir(parents=True, exist_ok=True)
#|    mapping = {
#|        result_dir / "fault_panel_result_raw_only_v1.csv": root_result_dir / ROOT_RAWONLY_FAULT_NAME,
#|        result_dir / "fault_panel_result_raw_only_preview_v1.csv": root_result_dir / ROOT_RAWONLY_PREVIEW_NAME,
#|    }
#|    published: dict[str, str] = {}
#|    for source, target in mapping.items():
#|        if not source.exists():
#|            raise SystemExit(f"missing raw-only chain output for publish step: {source}")
#|        shutil.copy2(source, target)
#|        published[target.name] = str(target)
#|    return published
#|
#|
#|def build_strict_raw_only_current_outputs(
#|    raw_only_chain_result: dict[str, object],
#|    evidence_df: pd.DataFrame,
#|) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
#|    candidate_fault_path = Path(
#|        str(raw_only_chain_result.get("generated_outputs", {}).get("fault_panel_result_raw_only_v1", ""))
#|    )
#|    candidate_preview_path = Path(
#|        str(raw_only_chain_result.get("generated_outputs", {}).get("fault_panel_result_raw_only_preview_v1", ""))
#|    )
#|    if not candidate_fault_path.exists() or not candidate_preview_path.exists():
#|        raise SystemExit("missing candidate raw-only outputs for strict current publish")
#|
#|    candidate_fault_df = pd.read_csv(candidate_fault_path, encoding="utf-8-sig", low_memory=False)
#|    candidate_preview_df = pd.read_csv(candidate_preview_path, encoding="utf-8-sig", low_memory=False)
#|    strict_keys = {
#|        row_key(row["site"], row["panel_id"])
#|        for row in evidence_df.to_dict(orient="records")
#|        if normalize_text(row.get("운영해석등급_ko")) in RAW_ONLY_STRICT_CURRENT_GRADES
#|    }
#|    if strict_keys:
#|        strict_fault_df = candidate_fault_df.loc[
#|            candidate_fault_df.apply(lambda row: row_key(row["site"], row["panel_id"]) in strict_keys, axis=1)
#|        ].copy()
#|        strict_preview_df = candidate_preview_df.loc[
#|            candidate_preview_df.apply(lambda row: row_key(row["site"], row["panel_id"]) in strict_keys, axis=1)
#|        ].copy()
#|    else:
#|        strict_fault_df = candidate_fault_df.iloc[0:0].copy()
#|        strict_preview_df = candidate_preview_df.iloc[0:0].copy()
#|
#|    strict_fault_df = strict_fault_df.sort_values(["site", "panel_id"]).reset_index(drop=True)
#|    strict_preview_df = strict_preview_df.sort_values(["site", "panel_id"]).reset_index(drop=True)
#|    date_lookup = {
#|        row_key(row["site"], row["panel_id"]): {
#|            "전조날짜": normalize_text(row.get("전조날짜")),
#|            "고장날짜": normalize_text(row.get("고장날짜")),
#|        }
#|        for row in evidence_df.to_dict(orient="records")
#|    }
#|    for df in [strict_fault_df, strict_preview_df]:
#|        if df.empty:
#|            continue
#|        df["전조날짜"] = df.apply(
#|            lambda row: date_lookup.get(row_key(row["site"], row["panel_id"]), {}).get("전조날짜", ""),
#|            axis=1,
#|        )
#|        df["고장날짜"] = df.apply(
#|            lambda row: date_lookup.get(row_key(row["site"], row["panel_id"]), {}).get("고장날짜", ""),
#|            axis=1,
#|        )
#|        ordered_cols = [column for column in df.columns if column not in {"전조날짜", "고장날짜"}]
#|        insert_at = ordered_cols.index("최종고장양상_ko") + 1 if "최종고장양상_ko" in ordered_cols else len(ordered_cols)
#|        ordered_cols[insert_at:insert_at] = ["전조날짜", "고장날짜"]
#|        df = df.reindex(columns=ordered_cols)
#|        if df is strict_fault_df:
#|            strict_fault_df = df
#|        else:
#|            strict_preview_df = df
#|    meta = {
#|        "publish_policy_ko": "raw_only current는 운영해석등급_ko=확정 strict subset만 노출",
#|        "strict_grade_csv": ",".join(sorted(RAW_ONLY_STRICT_CURRENT_GRADES)),
#|        "candidate_row_count": int(len(candidate_fault_df)),
#|        "published_current_row_count": int(len(strict_fault_df)),
#|        "dropped_candidate_row_count": int(len(candidate_fault_df) - len(strict_fault_df)),
#|    }
#|    return strict_fault_df, strict_preview_df, meta
#|
#|
#|def publish_raw_only_current_outputs(
#|    output_root: Path,
#|    strict_fault_df: pd.DataFrame,
#|    strict_preview_df: pd.DataFrame,
#|) -> dict[str, str]:
#|    root_result_dir = output_root / "result"
#|    root_result_dir.mkdir(parents=True, exist_ok=True)
#|    fault_path = root_result_dir / ROOT_RAWONLY_FAULT_NAME
#|    preview_path = root_result_dir / ROOT_RAWONLY_PREVIEW_NAME
#|    strict_fault_df.to_csv(fault_path, index=False, encoding="utf-8-sig")
#|    strict_preview_df.to_csv(preview_path, index=False, encoding="utf-8-sig")
#|    return {
#|        ROOT_RAWONLY_FAULT_NAME: str(fault_path),
#|        ROOT_RAWONLY_PREVIEW_NAME: str(preview_path),
#|    }
#|
#|
#|def markdown_table_from_df(df: pd.DataFrame) -> str:
#|    if df.empty:
#|        return "_empty_"
#|    safe_df = df.fillna("").astype(str)
#|    headers = safe_df.columns.tolist()
#|    lines = [
#|        "| " + " | ".join(headers) + " |",
#|        "| " + " | ".join(["---"] * len(headers)) + " |",
#|    ]
#|    for row in safe_df.itertuples(index=False, name=None):
#|        lines.append("| " + " | ".join(str(value) for value in row) + " |")
#|    return "\n".join(lines)
#|
#|
#|def truncate_report_df(df: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
#|    if df.empty or len(df) <= limit:
#|        return df
#|    return df.head(limit).copy()
#|
#|
#|def build_live_report_markdown(
#|    sites: list[str],
#|    baseline_comparison: dict[str, object],
#|    compare: dict[str, object],
#|    published_outputs: dict[str, str],
#|    live_preview_df: pd.DataFrame,
#|) -> str:
#|    site_lines = "\n".join(f"- `{site}`" for site in sites)
#|    baseline_site_lines = []
#|    for site in sites:
#|        site_entry = baseline_comparison.get("sites", {}).get(site, {})
#|        baseline_site_lines.append(
#|            f"- `{site}`: `match={site_entry.get('match')}`"
#|        )
#|    baseline_block = "\n".join(baseline_site_lines)
#|    output_lines = "\n".join(
#|        f"- `{name}`: `{path}`" for name, path in sorted(published_outputs.items())
#|    )
#|    return (
#|        "# fault_panel_result_current_report_v1\n\n"
#|        "## 목적\n"
#|        "현재 runtime 실행에서 운영자가 바로 확인할 `운영 공식 current` 결과를 한 곳에 모아 보여준다.\n\n"
#|        "## 실행 대상 site\n"
#|        f"{site_lines}\n\n"
#|        "## baseline 입력 비교\n"
#|        f"- `all_sites_match`: `{baseline_comparison.get('all_sites_match')}`\n"
#|        f"{baseline_block}\n\n"
#|        "## live chain 상태\n"
#|        f"- `fixed_fault_reference_exact_match`: `{compare.get('exact_match')}`\n"
#|        f"- `baseline_input_all_sites_match`: `{compare.get('baseline_input_all_sites_match')}`\n"
#|        f"- `diff_columns`: `{compare.get('diff_columns', [])}`\n\n"
#|        "## 읽는 법\n"
#|        "- 이 report는 `official current` 설명용 문서다.\n"
#|        "- `fault_panel_result_current_preview_v1.csv`와 함께 현재 운영 공식 결과를 먼저 읽는 기본 문서다.\n"
#|        "- `raw-only` 보조표나 analyst artifact를 대신하지 않는다.\n"
#|        "- `fault_panel_result_master_report_v1.md`는 artifact 안내와 fallback 설명용 문서이며, 이 report를 대체하지 않는다.\n\n"
#|        "## 주요 산출물\n"
#|        f"{output_lines}\n\n"
#|        "## 현재 preview 표\n"
#|        f"{markdown_table_from_df(live_preview_df)}\n"
#|    )
#|
#|
#|def build_raw_only_report_markdown(
#|    sites: list[str],
#|    compare: dict[str, object],
#|    published_outputs: dict[str, str],
#|    live_preview_df: pd.DataFrame,
#|    publish_meta: dict[str, object] | None = None,
#|) -> str:
#|    site_lines = "\n".join(f"- `{site}`" for site in sites)
#|    output_lines = "\n".join(
#|        f"- `{name}`: `{path}`" for name, path in sorted(published_outputs.items())
#|    )
#|    publish_meta = publish_meta or {}
#|    return (
#|        "# fault_panel_result_raw_only_current_report_v1\n\n"
#|        "## 목적\n"
#|        "raw-only algorithm candidate chain 중 운영 strict current로 승격된 현재 결과를 `분석용/운영 보조표`로 확인한다.\n\n"
#|        "## 실행 대상 site\n"
#|        f"{site_lines}\n\n"
#|        "## raw-only vs fixed reference 비교\n"
#|        f"- `status_ko`: `{compare.get('status_ko')}`\n"
#|        f"- `reference_available`: `{compare.get('reference_available')}`\n"
#|        f"- `row_key_match`: `{compare.get('row_key_match')}`\n"
#|        f"- `decision_columns_match`: `{compare.get('decision_columns_match')}`\n"
#|        f"- `overlap_decision_columns_match`: `{compare.get('overlap_decision_columns_match')}`\n"
#|        f"- `exact_match`: `{compare.get('exact_match')}`\n"
#|        f"- `reference_row_count`: `{compare.get('reference_row_count')}`\n"
#|        f"- `candidate_row_count`: `{compare.get('candidate_row_count')}`\n"
#|        f"- `matched_row_key_count`: `{compare.get('matched_row_key_count')}`\n"
#|        f"- `diff_columns`: `{compare.get('diff_columns', [])}`\n\n"
#|        f"- `overlap_diff_columns`: `{compare.get('overlap_diff_columns', [])}`\n\n"
#|        "## current 출력 정책\n"
#|        f"- `publish_policy_ko`: `{publish_meta.get('publish_policy_ko', '')}`\n"
#|        f"- `strict_grade_csv`: `{publish_meta.get('strict_grade_csv', '')}`\n"
#|        f"- `published_current_row_count`: `{publish_meta.get('published_current_row_count', '')}`\n"
#|        f"- `candidate_row_count`: `{publish_meta.get('candidate_row_count', '')}`\n"
#|        f"- `dropped_candidate_row_count`: `{publish_meta.get('dropped_candidate_row_count', '')}`\n\n"
#|        "## 주의\n"
#|        "- `커널로그_원인군_ko` 컬럼명은 유지하지만, 이 report에서는 raw-only algorithm-derived family 의미다.\n"
#|        "- 이 chain은 frozen truth/support asset을 참조하지 않는다.\n\n"
#|        "- 이 report는 `official current report`가 아니며, 운영 공식 결과를 대체하지 않는다.\n"
#|        "- 운영자 기본 진입점은 `fault_panel_result_current_*` 계열이고, 이 report는 analyst/support 확인용이다.\n\n"
#|        "- preview 표의 `사건 종결 요약`은 관측 플래그를 먼저 본 뒤, 확정 row에서만 채워지는 요약이다.\n\n"
#|        "- `result/raw_only_chain/*`에는 전체 candidate가 남고, `result/fault_panel_result_raw_only_current_*`는 strict current subset만 노출한다.\n\n"
#|        "## 주요 산출물\n"
#|        f"{output_lines}\n\n"
#|        "## 현재 preview 표\n"
#|        f"{markdown_table_from_df(truncate_report_df(live_preview_df))}\n"
#|    )
#|
#|
#|def build_master_report_markdown(
#|    sites: list[str],
#|    baseline_comparison: dict[str, object],
#|    live_chain_result: dict[str, object],
#|    raw_only_chain_result: dict[str, object],
#|    live_preview_df: pd.DataFrame,
#|    raw_only_preview_df: pd.DataFrame,
#|    precursor_report_df: pd.DataFrame | None = None,
#|    fault_signal_report_df: pd.DataFrame | None = None,
#|    detailed_report_path: Path | None = None,
#|    precursor_report_path: Path | None = None,
#|    fault_signal_report_path: Path | None = None,
#|) -> str:
#|    site_lines = "\n".join(f"- `{site}`" for site in sites)
#|    baseline_site_lines = []
#|    for site in sites:
#|        site_entry = baseline_comparison.get("sites", {}).get(site, {})
#|        baseline_site_lines.append(f"- `{site}`: `match={site_entry.get('match')}`")
#|    baseline_block = "\n".join(baseline_site_lines)
#|    live_compare = live_chain_result.get("fixed_fault_reference_compare", {})
#|    raw_only_compare = raw_only_chain_result.get("fixed_fault_reference_compare", {})
#|    primary_output_lines = []
#|    analyst_output_lines = []
#|    for name, path in sorted(live_chain_result.get("published_outputs", {}).items()):
#|        primary_output_lines.append(f"- `live::{name}`: `{path}`")
#|    for name, path in sorted(raw_only_chain_result.get("published_outputs", {}).items()):
#|        analyst_output_lines.append(f"- `raw_only::{name}`: `{path}`")
#|    primary_output_block = "\n".join(primary_output_lines) if primary_output_lines else "_none_"
#|    analyst_output_block = "\n".join(analyst_output_lines) if analyst_output_lines else "_none_"
#|    precursor_report_df = precursor_report_df if precursor_report_df is not None else pd.DataFrame()
#|    fault_signal_report_df = fault_signal_report_df if fault_signal_report_df is not None else pd.DataFrame()
#|    precursor_keys = set(
#|        zip(
#|            precursor_report_df.get("site", pd.Series(dtype=object)).astype(str),
#|            precursor_report_df.get("panel_id", pd.Series(dtype=object)).astype(str),
#|        )
#|    )
#|    fault_signal_keys = set(
#|        zip(
#|            fault_signal_report_df.get("site", pd.Series(dtype=object)).astype(str),
#|            fault_signal_report_df.get("panel_id", pd.Series(dtype=object)).astype(str),
#|        )
#|    )
#|    overlap_row_count = len(precursor_keys & fault_signal_keys)
#|    fault_signal_subgroup_summary = pd.DataFrame(
#|        columns=["site", "group root", "subgroup base", "row_count"]
#|    )
#|    fault_signal_cluster_summary = pd.DataFrame(
#|        columns=[
#|            "site",
#|            "group root",
#|            "subgroup base",
#|            "subgroup cluster",
#|            "row_count",
#|            "min_signal_date",
#|            "max_signal_date",
#|        ]
#|    )
#|    if fault_signal_report_df is not None and not fault_signal_report_df.empty:
#|        working = fault_signal_report_df.copy()
#|        working["group root"] = working["group root"].map(normalize_text)
#|        working["subgroup base"] = working["subgroup base"].map(normalize_text)
#|        working["subgroup cluster"] = working["subgroup cluster"].map(normalize_text)
#|        working["신호 기준일_dt"] = pd.to_datetime(working["신호 기준일"], errors="coerce")
#|        working = working.loc[working["subgroup base"].ne("")].copy()
#|        if not working.empty:
#|            fault_signal_subgroup_summary = (
#|                working.groupby(["site", "group root", "subgroup base"], dropna=False)
#|                .size()
#|                .rename("row_count")
#|                .reset_index()
#|                .sort_values(
#|                    ["row_count", "site", "group root", "subgroup base"],
#|                    ascending=[False, True, True, True],
#|                )
#|                .reset_index(drop=True)
#|            )
#|            fault_signal_cluster_summary = (
#|                working.groupby(
#|                    ["site", "group root", "subgroup base", "subgroup cluster"], dropna=False
#|                )
#|                .agg(
#|                    row_count=("panel_id", "size"),
#|                    min_signal_date=("신호 기준일_dt", "min"),
#|                    max_signal_date=("신호 기준일_dt", "max"),
#|                )
#|                .reset_index()
#|                .sort_values(
#|                    ["row_count", "site", "group root", "subgroup base", "subgroup cluster"],
#|                    ascending=[False, True, True, True, True],
#|                )
#|                .reset_index(drop=True)
#|            )
#|            for column in ["min_signal_date", "max_signal_date"]:
#|                fault_signal_cluster_summary[column] = pd.to_datetime(
#|                    fault_signal_cluster_summary[column], errors="coerce"
#|                ).dt.strftime("%Y-%m-%d")
#|    fault_signal_unique_group_root_count = (
#|        int(len(fault_signal_subgroup_summary[["site", "group root"]].drop_duplicates()))
#|        if not fault_signal_subgroup_summary.empty
#|        else 0
#|    )
#|    fault_signal_unique_subgroup_base_count = (
#|        int(len(fault_signal_subgroup_summary[["site", "subgroup base"]].drop_duplicates()))
#|        if not fault_signal_subgroup_summary.empty
#|        else 0
#|    )
#|    fault_signal_unique_subgroup_cluster_count = (
#|        int(len(fault_signal_cluster_summary[["site", "subgroup cluster"]].drop_duplicates()))
#|        if not fault_signal_cluster_summary.empty
#|        else 0
#|    )
#|    fault_signal_top_subgroup_block = (
#|        markdown_table_from_df(fault_signal_subgroup_summary.head(10))
#|        if not fault_signal_subgroup_summary.empty
#|        else "_none_"
#|    )
#|    fault_signal_top_cluster_block = (
#|        markdown_table_from_df(fault_signal_cluster_summary.head(10))
#|        if not fault_signal_cluster_summary.empty
#|        else "_none_"
#|    )
#|    detailed_report_block = (
#|        f"- `fault_panel_result_detailed_report_v1.xlsx`: `{detailed_report_path}`\n\n"
#|        if detailed_report_path is not None
#|        else ""
#|    )
#|    precursor_report_block = (
#|        f"- `fault_panel_result_precursor_report_v1.csv`: `{precursor_report_path}`\n\n"
#|        if precursor_report_path is not None
#|        else ""
#|    )
#|    fault_signal_report_block = (
#|        f"- `{ROOT_FAULT_SIGNAL_REPORT_NAME}`: `{fault_signal_report_path}`\n\n"
#|        if fault_signal_report_path is not None
#|        else ""
#|    )
#|    return (
#|        "# fault_panel_result_master_report_v1\n\n"
#|        "## 목적\n"
#|        "frozen-support live chain과 raw-only algorithm candidate chain을 비교하고, 어떤 artifact를 어떤 순서로 읽을지 안내한다.\n\n"
#|        "## 실행 대상 site\n"
#|        f"{site_lines}\n\n"
#|        "## baseline 입력 비교\n"
#|        f"- `all_sites_match`: `{baseline_comparison.get('all_sites_match')}`\n"
#|        f"{baseline_block}\n\n"
#|        "## frozen-support live chain 요약\n"
#|        f"- `status_ko`: `{live_chain_result.get('status_ko')}`\n"
#|        f"- `fixed_fault_reference_exact_match`: `{live_compare.get('exact_match')}`\n"
#|        f"- `baseline_input_all_sites_match`: `{live_compare.get('baseline_input_all_sites_match')}`\n"
#|        f"- `diff_columns`: `{live_compare.get('diff_columns', [])}`\n\n"
#|        "## raw-only algorithm candidate chain 요약\n"
#|        f"- `status_ko`: `{raw_only_compare.get('status_ko')}`\n"
#|        f"- `reference_available`: `{raw_only_compare.get('reference_available')}`\n"
#|        f"- `overlap_decision_columns_match`: `{raw_only_compare.get('overlap_decision_columns_match')}`\n"
#|        f"- `reference_row_count`: `{raw_only_compare.get('reference_row_count')}`\n"
#|        f"- `candidate_row_count`: `{raw_only_compare.get('candidate_row_count')}`\n"
#|        f"- `published_current_row_count`: `{raw_only_chain_result.get('publish_meta', {}).get('published_current_row_count', '')}`\n"
#|        f"- `matched_row_key_count`: `{raw_only_compare.get('matched_row_key_count')}`\n"
#|        f"- `overlap_diff_columns`: `{raw_only_compare.get('overlap_diff_columns', [])}`\n\n"
#|        "## report split 요약\n"
#|        f"- `precursor_candidate_row_count`: `{len(precursor_report_df)}`\n"
#|        f"- `raw_only_fault_signal_row_count`: `{len(fault_signal_report_df)}`\n"
#|        f"- `raw_only_fault_signal_unique_group_root_count`: `{fault_signal_unique_group_root_count}`\n"
#|        f"- `raw_only_fault_signal_unique_subgroup_base_count`: `{fault_signal_unique_subgroup_base_count}`\n"
#|        f"- `raw_only_fault_signal_unique_subgroup_cluster_count`: `{fault_signal_unique_subgroup_cluster_count}`\n"
#|        f"- `report_row_overlap_count`: `{overlap_row_count}`\n\n"
#|        "## 먼저 보는 법\n"
#|        "- `fault_panel_result_current_*`: frozen-support live chain 기준의 공식 current 결과를 먼저 확인한다. current preview/current report가 있으면 그쪽이 공식 current 설명의 주 문서다.\n"
#|        "- `fault_panel_result_precursor_report_v1.csv`: 아직 고장 신호는 없지만 추적 가치가 있는 precursor candidate를 본다.\n"
#|        "- raw-only artifact는 operator 기본 읽기 순서가 아니라 아래 `analyst/support 추가 자료` 섹션에서 필요 시 확인한다.\n\n"
#|        "## 해석 가이드\n"
#|        "- 이 문서는 공식 current 설명 문서를 대체하지 않는 안내/fallback 문서다. current preview/current report가 있으면 그쪽을 먼저 읽는다.\n"
#|        "- `fault_panel_result_current_*`는 frozen-support live chain 기준 결과다.\n"
#|        "- `fault_panel_result_raw_only_current_*`는 raw-only candidate 중 strict current subset만 보여준다.\n"
#|        "- `fault_panel_result_precursor_report_v1.csv`는 고장 신호가 아직 없는 precursor candidate만 보여준다.\n"
#|        f"- `{ROOT_FAULT_SIGNAL_REPORT_NAME}`는 raw-only candidate 우주에서 고장 신호가 이미 관측된 panel만 모은 analyst/support 보조표다.\n"
#|        "- raw-only chain의 `커널로그_원인군_ko`는 기존 라벨 family가 아니라 algorithm-derived family 의미다.\n"
#|        "- preview 표의 `운영 판정`은 현재 신호 단계, `상위 해석 후보`는 가장 가까운 원인 후보를 뜻한다.\n"
#|        "- `급락 종결 관측`과 `점진 저하 누적`은 관측 축이고, `사건 종결 요약`은 확정 row에서만 채워지는 사건 요약이다.\n"
#|        "- `고장 기준일`은 확정 고장일만 뜻하는 칼럼이 아니라 판단 기준으로 삼은 날짜다.\n"
#|        "- `기존 알고리즘 source`의 `미검출`은 legacy source 태그가 없다는 뜻이다.\n"
#|        "- precursor report와 raw-only fault signal report는 row가 중복되지 않게 분리해 읽어야 한다.\n"
#|        "- raw-only fault signal report의 row 수는 `panel_id` 기준 count이고, 같은 `subgroup base` 아래 여러 panel이 함께 잡히면 여러 row로 보일 수 있다.\n"
#|        f"- `subgroup cluster`는 같은 subgroup base 안에서 `신호 기준일` 간격이 `{FAULT_SIGNAL_CLUSTER_GAP_DAYS}`일 이하인 row를 하나의 보조 cluster로 묶은 analyst/support 휴리스틱이다.\n"
#|        "- 운영자는 기본적으로 current -> precursor 순서로 읽고, raw-only artifact는 analyst/support 추가 자료가 필요할 때만 연다.\n"
#|        "- 전체 candidate universe는 `result/raw_only_chain/*`와 detailed report 안에 그대로 남는다.\n\n"
#|        "## 컬럼 읽는 법\n"
#|        "- precursor report의 `전조 축`은 EWS/AE/DTW/규칙징후 중 어떤 축이 전조로 묶였는지 보여준다.\n"
#|        "- precursor report의 `대표 전조 신호`는 전조 후보를 만든 누적 신호를 짧게 풀어쓴 요약이다.\n"
#|        "- precursor report의 `모니터링 권고`는 다음 수집 주기에 무엇을 먼저 확인할지 알려주는 운영 메모다.\n"
#|        "- precursor report의 `공통원인 위험`과 `권고 검토 레인`은 panel-local precursor로 읽기 전에 공통 외란 가능성을 얼마나 먼저 볼지 정리한 보조 값이다.\n"
#|        "- raw-only fault signal report의 `group root`는 넓은 family root, `subgroup base`는 common-cause 검토에 더 가까운 하위 묶음이다.\n"
#|        "- raw-only fault signal report의 `동일 subgroup row 수`는 같은 subgroup base 아래 함께 잡힌 panel row 수다.\n"
#|        "- raw-only fault signal report의 `subgroup cluster`와 `동일 cluster row 수`는 `사건 수`를 직접 뜻하지 않고, 같은 subgroup base 안에서 가까운 날짜 row를 묶어 읽기 쉽게 만든 보조 값이다.\n"
#|        "- raw-only fault signal report의 `확정 경로`는 주 경로 하나만 보여주고, `고장 신호 요약`은 일수와 보조 근거를 덧붙인다.\n"
#|        "- raw-only fault signal report의 `근접 공통원인`은 strict_trigger 기준 ±3일 안의 common-cause만 적고, warning-anchor 기준 common-cause는 audit 전용으로 남긴다.\n"
#|        "- raw-only fault signal report의 `현장 점검 권고`는 첫 현장 액션의 우선순위를 짧게 적은 값이다.\n\n"
#|        "## 주요 산출물\n"
#|        f"{primary_output_block}\n\n"
#|        "## analyst/support 추가 자료\n"
#|        f"{analyst_output_block}\n\n"
#|        "## 상세 리포트\n"
#|        f"{detailed_report_block}"
#|        "## 전조 리포트\n"
#|        f"{precursor_report_block}"
#|        "## raw-only 고장 신호 리포트\n"
#|        f"{fault_signal_report_block}"
#|        "## raw-only 고장 신호 subgroup base 요약 (앞 10행)\n"
#|        f"{fault_signal_top_subgroup_block}\n\n"
#|        "## raw-only 고장 신호 subgroup cluster 요약 (앞 10행)\n"
#|        f"{fault_signal_top_cluster_block}\n\n"
#|        "## current preview 표\n"
#|        f"{markdown_table_from_df(truncate_report_df(live_preview_df))}\n\n"
#|        "## precursor 후보 표 (앞 20행)\n"
#|        f"{markdown_table_from_df(truncate_report_df(precursor_report_df, limit=20))}\n\n"
#|        "## analyst/support 참고 메모\n"
#|        f"- `{ROOT_FAULT_SIGNAL_REPORT_NAME}`와 `fault_panel_result_raw_only_current_*`는 master report에서 경로만 안내하는 보조 artifact다.\n"
#|        "- raw-only preview/fault signal row는 operator 기본 읽기 흐름에 직접 전개하지 않는다.\n"
#|        f"- raw-only strict current preview row count: `{len(raw_only_preview_df)}`\n"
#|        f"- raw-only fault signal row count: `{len(fault_signal_report_df)}`\n"
#|    )
#|
#|
#|def panel_group_root(panel_id: object) -> str:
#|    text = normalize_text(panel_id)
#|    tokens = text.split(".")
#|    if len(tokens) >= 3:
#|        return ".".join(tokens[:-2])
#|    return text
#|
#|
#|def panel_subgroup_base(panel_id: object) -> str:
#|    text = normalize_text(panel_id)
#|    tokens = text.split(".")
#|    if len(tokens) >= 2:
#|        return ".".join(tokens[:-1])
#|    return text
#|
#|
#|def attach_fault_signal_cluster_columns(df: pd.DataFrame) -> pd.DataFrame:
#|    if df is None or df.empty:
#|        working = df.copy() if df is not None else pd.DataFrame()
#|        if "subgroup cluster" not in working.columns:
#|            working["subgroup cluster"] = pd.Series(dtype=object)
#|        if "동일 cluster row 수" not in working.columns:
#|            working["동일 cluster row 수"] = pd.Series(dtype=int)
#|        return working
#|
#|    working = df.copy()
#|    working["신호 기준일_dt"] = pd.to_datetime(working["신호 기준일"], errors="coerce")
#|    cluster_key_by_index: dict[int, str] = {}
#|    cluster_size_by_index: dict[int, int] = {}
#|
#|    for (_, subgroup_base), subgroup_rows in working.groupby(
#|        ["site", "subgroup base"], sort=False, dropna=False
#|    ):
#|        subgroup_rows = subgroup_rows.sort_values(
#|            ["신호 기준일_dt", "panel_id"], ascending=[True, True]
#|        ).copy()
#|        cluster_ids: list[int] = []
#|        cluster_id = 0
#|        prev_date = None
#|        for _, subgroup_row in subgroup_rows.iterrows():
#|            current_date = subgroup_row.get("신호 기준일_dt")
#|            if pd.isna(current_date):
#|                cluster_id += 1
#|            elif prev_date is None or (current_date - prev_date).days > FAULT_SIGNAL_CLUSTER_GAP_DAYS:
#|                cluster_id += 1
#|                prev_date = current_date
#|            else:
#|                prev_date = current_date
#|            cluster_ids.append(cluster_id)
#|        subgroup_rows["cluster_id"] = cluster_ids
#|
#|        cluster_meta = (
#|            subgroup_rows.groupby("cluster_id", dropna=False)
#|            .agg(
#|                cluster_rows=("panel_id", "size"),
#|                start_date=("신호 기준일_dt", "min"),
#|                end_date=("신호 기준일_dt", "max"),
#|            )
#|            .reset_index()
#|        )
#|        label_map: dict[int, str] = {}
#|        size_map: dict[int, int] = {}
#|        for cluster_row in cluster_meta.to_dict(orient="records"):
#|            cid = int(cluster_row["cluster_id"])
#|            start_date = cluster_row.get("start_date")
#|            end_date = cluster_row.get("end_date")
#|            if pd.notna(start_date) and pd.notna(end_date):
#|                start_text = pd.Timestamp(start_date).strftime("%Y-%m-%d")
#|                end_text = pd.Timestamp(end_date).strftime("%Y-%m-%d")
#|                if start_text == end_text:
#|                    label = f"{normalize_text(subgroup_base)} @ {start_text}"
#|                else:
#|                    label = f"{normalize_text(subgroup_base)} @ {start_text}~{end_text}"
#|            else:
#|                label = f"{normalize_text(subgroup_base)} @ undated#{cid}"
#|            label_map[cid] = label
#|            size_map[cid] = int(cluster_row.get("cluster_rows", 0) or 0)
#|
#|        subgroup_rows["subgroup cluster"] = subgroup_rows["cluster_id"].map(label_map)
#|        subgroup_rows["동일 cluster row 수"] = subgroup_rows["cluster_id"].map(size_map)
#|        cluster_key_by_index.update(subgroup_rows["subgroup cluster"].to_dict())
#|        cluster_size_by_index.update(subgroup_rows["동일 cluster row 수"].to_dict())
#|
#|    working["subgroup cluster"] = working.index.map(cluster_key_by_index.get)
#|    working["동일 cluster row 수"] = working.index.map(cluster_size_by_index.get)
#|    return working.drop(columns=["신호 기준일_dt"], errors="ignore")
#|
#|
#|def bool_count(df: pd.DataFrame, column: str) -> int:
#|    if column not in df.columns or df.empty:
#|        return 0
#|    return int(truthy_mask(df[column]).sum())
#|
#|
#|def unique_csv(series: pd.Series) -> str:
#|    values = sorted({normalize_text(value) for value in series if normalize_text(value)})
#|    return ",".join(values)
#|
#|
#|def load_gate_from_workspace(workspace_root: Path, site: str) -> pd.DataFrame:
#|    path = workspace_root / "data" / site / "out" / "ae_simple_local_precursor_gate_daily.csv"
#|    if not path.exists():
#|        raise SystemExit(f"missing workspace precursor gate output: {path}")
#|    df = pd.read_csv(path, low_memory=False)
#|    ensure_columns(df, ["panel_id", "date"], path.name)
#|    df["panel_id"] = df["panel_id"].astype(str)
#|    df["date"] = pd.to_datetime(df["date"], errors="coerce")
#|    return df
#|
#|
#|def report_attention_grade(evidence_row: dict[str, object]) -> str:
#|    final_days = int(evidence_row.get("final_days", 0) or 0)
#|    critical_days = int(evidence_row.get("critical_days", 0) or 0)
#|    critical_confirmed_days = int(evidence_row.get("critical_confirmed_days", 0) or 0)
#|    fault_like_days = int(evidence_row.get("fault_like_days", 0) or 0)
#|    ews_warning_days = int(evidence_row.get("ews_warning_days", 0) or 0)
#|    pre_alarm_days = int(evidence_row.get("pre_alarm_days", 0) or 0)
#|    pre_ews_days = int(evidence_row.get("pre_ews_days", 0) or 0)
#|    prefault_cond_ae_days = int(evidence_row.get("prefault_cond_ae_days", 0) or 0)
#|    prefault_cond_dtw_days = int(evidence_row.get("prefault_cond_dtw_days", 0) or 0)
#|    critical_sources = normalize_text(evidence_row.get("critical_sources_csv"))
#|
#|    if final_days > 0 or critical_days > 0 or critical_confirmed_days > 0:
#|        return "확정"
#|    if (
#|        "vdrop" in critical_sources
#|        or ews_warning_days >= 15
#|        or pre_alarm_days >= 10
#|        or pre_ews_days >= 50
#|        or prefault_cond_ae_days >= 120
#|        or prefault_cond_dtw_days >= 120
#|        or fault_like_days >= 2
#|    ):
#|        return "고위험 관찰"
#|    return "관찰"
#|
#|
#|def report_reason_text(evidence_row: dict[str, object]) -> str:
#|    grade = normalize_text(evidence_row.get("운영해석등급_ko"))
#|    top1 = normalize_text(evidence_row.get("1순위_의심원인_ko"))
#|    final_days = int(evidence_row.get("final_days", 0) or 0)
#|    critical_days = int(evidence_row.get("critical_days", 0) or 0)
#|    critical_confirmed_days = int(evidence_row.get("critical_confirmed_days", 0) or 0)
#|    ews_warning_days = int(evidence_row.get("ews_warning_days", 0) or 0)
#|    pre_ews_days = int(evidence_row.get("pre_ews_days", 0) or 0)
#|    prefault_B_effective_days = int(evidence_row.get("prefault_B_effective_days", 0) or 0)
#|    prefault_B_common_cause_overlap_days = int(evidence_row.get("prefault_B_common_cause_overlap_days", 0) or 0)
#|    prefault_cond_ae_days = int(evidence_row.get("prefault_cond_ae_days", 0) or 0)
#|    prefault_cond_dtw_days = int(evidence_row.get("prefault_cond_dtw_days", 0) or 0)
#|    critical_sources = normalize_text(evidence_row.get("critical_sources_csv"))
#|    subtypes = normalize_text(evidence_row.get("anom_subtypes_csv"))
#|    subgroup_candidate_count = int(evidence_row.get("subgroup_candidate_panel_count", 0) or 0)
#|
#|    if grade == "확정":
#|        signal_labels: list[str] = []
#|        if final_days > 0:
#|            signal_labels.append("최종 고장 신호")
#|        if critical_confirmed_days > 0:
#|            signal_labels.append("강한 고장 신호 확정")
#|        elif critical_days > 0:
#|            signal_labels.append("강한 고장 신호")
#|        if "vdrop" in critical_sources:
#|            signal_labels.append("vdrop 전기 신호")
#|        signal_summary = " / ".join(signal_labels) if signal_labels else "확정 신호"
#|        return f"{signal_summary}가 나타나 고장 신호가 뚜렷하게 포착됨"
#|
#|    reasons: list[str] = []
#|    if "degradation" in subtypes:
#|        reasons.append("degradation subtype 반복")
#|    if ews_warning_days > 0 or pre_ews_days > 0:
#|        reasons.append(f"EWS 전조 누적(ews={ews_warning_days}, pre_ews={pre_ews_days})")
#|    if prefault_B_effective_days > 0:
#|        reasons.append(f"Option B 유효 전조 누적({prefault_B_effective_days}일)")
#|    if prefault_cond_ae_days > 0 or prefault_cond_dtw_days > 0:
#|        reasons.append(
#|            f"AE/DTW 전조 조건 누적(ae={prefault_cond_ae_days}, dtw={prefault_cond_dtw_days})"
#|        )
#|    if prefault_B_common_cause_overlap_days > 0:
#|        reasons.append(f"공통원인 겹침 option B({prefault_B_common_cause_overlap_days}일)는 별도 분리")
#|    if subgroup_candidate_count >= 3:
#|        reasons.append(f"동일 subgroup 동시 흔들림({subgroup_candidate_count} panels)")
#|    if top1:
#|        reasons.append(f"가장 가까운 후보는 {top1}")
#|    if not reasons:
#|        reasons.append("약한 이상 신호만 있어 관찰 대상으로 해석")
#|    return " / ".join(reasons)
#|
#|
#|def report_precursor_axes_text(evidence_row: dict[str, object]) -> str:
#|    axes: list[str] = []
#|    ews_warning_days = int(evidence_row.get("ews_warning_days", 0) or 0)
#|    pre_alarm_days = int(evidence_row.get("pre_alarm_days", 0) or 0)
#|    pre_ews_days = int(evidence_row.get("pre_ews_days", 0) or 0)
#|    prefault_cond_ae_days = int(evidence_row.get("prefault_cond_ae_days", 0) or 0)
#|    prefault_cond_dtw_days = int(evidence_row.get("prefault_cond_dtw_days", 0) or 0)
#|    event_A_days = int(evidence_row.get("event_A_days", 0) or 0)
#|    fault_like_days = int(evidence_row.get("fault_like_days", 0) or 0)
#|    final_days = int(evidence_row.get("final_days", 0) or 0)
#|    critical_days = int(evidence_row.get("critical_days", 0) or 0)
#|    critical_sources = normalize_text(evidence_row.get("critical_sources_csv"))
#|    subtypes = normalize_text(evidence_row.get("anom_subtypes_csv"))
#|
#|    if ews_warning_days > 0 or pre_ews_days > 0:
#|        axes.append("EWS")
#|    if prefault_cond_ae_days > 0 or event_A_days > 0 or "degradation" in subtypes:
#|        axes.append("AE")
#|    if prefault_cond_dtw_days > 0:
#|        axes.append("DTW")
#|    if (
#|        pre_alarm_days > 0
#|        or fault_like_days > 0
#|        or final_days > 0
#|        or critical_days > 0
#|        or "vdrop" in critical_sources
#|    ):
#|        axes.append("규칙징후")
#|    return "+".join(axes)
#|
#|
#|def report_precursor_signal_text(evidence_row: dict[str, object]) -> str:
#|    signals: list[str] = []
#|    ews_warning_days = int(evidence_row.get("ews_warning_days", 0) or 0)
#|    pre_alarm_days = int(evidence_row.get("pre_alarm_days", 0) or 0)
#|    pre_ews_days = int(evidence_row.get("pre_ews_days", 0) or 0)
#|    prefault_B_effective_days = int(evidence_row.get("prefault_B_effective_days", 0) or 0)
#|    prefault_B_common_cause_overlap_days = int(evidence_row.get("prefault_B_common_cause_overlap_days", 0) or 0)
#|    prefault_cond_ae_days = int(evidence_row.get("prefault_cond_ae_days", 0) or 0)
#|    prefault_cond_dtw_days = int(evidence_row.get("prefault_cond_dtw_days", 0) or 0)
#|    critical_sources = normalize_text(evidence_row.get("critical_sources_csv"))
#|    subtypes = normalize_text(evidence_row.get("anom_subtypes_csv"))
#|
#|    if ews_warning_days > 0 or pre_ews_days > 0:
#|        signals.append(f"EWS 전조 누적(ews={ews_warning_days}, pre_ews={pre_ews_days})")
#|    if prefault_B_effective_days > 0:
#|        signals.append(f"Option B 유효 누적({prefault_B_effective_days}일)")
#|    if prefault_cond_ae_days > 0:
#|        signals.append(f"AE 전조 조건 누적({prefault_cond_ae_days}일)")
#|    if prefault_cond_dtw_days > 0:
#|        signals.append(f"DTW 전조 조건 누적({prefault_cond_dtw_days}일)")
#|    if pre_alarm_days > 0:
#|        signals.append(f"pre_alarm 누적({pre_alarm_days}일)")
#|    if "vdrop" in critical_sources:
#|        signals.append("상대 전압 이탈 징후")
#|    if "degradation" in subtypes:
#|        signals.append("degradation subtype 반복")
#|    if prefault_B_common_cause_overlap_days > 0:
#|        signals.append(f"공통원인 겹침 option B({prefault_B_common_cause_overlap_days}일)")
#|    return " / ".join(signals)
#|
#|
#|def precursor_common_cause_risk_text(evidence_row: dict[str, object]) -> str:
#|    prefault_B_common_cause_overlap_days = int(
#|        evidence_row.get("prefault_B_common_cause_overlap_days", 0) or 0
#|    )
#|    subgroup_candidate_count = int(evidence_row.get("subgroup_candidate_panel_count", 0) or 0)
#|    if prefault_B_common_cause_overlap_days > 0 and subgroup_candidate_count >= 3:
#|        return "높음"
#|    if prefault_B_common_cause_overlap_days > 0 or subgroup_candidate_count >= 3:
#|        return "중간"
#|    return "낮음"
#|
#|
#|def precursor_review_lane_text(evidence_row: dict[str, object]) -> str:
#|    risk = precursor_common_cause_risk_text(evidence_row)
#|    grade = normalize_text(evidence_row.get("운영해석등급_ko"))
#|    if risk == "높음":
#|        return "공통원인 검토"
#|    if risk == "중간":
#|        return "공통원인 우선 확인"
#|    if grade == "고위험 관찰":
#|        return "단일 패널 우선 추적"
#|    return "일반 모니터링"
#|
#|
#|def precursor_monitoring_action_text(evidence_row: dict[str, object]) -> str:
#|    grade = normalize_text(evidence_row.get("운영해석등급_ko"))
#|    top1 = normalize_text(evidence_row.get("1순위_의심원인_ko"))
#|    axes = report_precursor_axes_text(evidence_row)
#|    prefault_B_effective_days = int(evidence_row.get("prefault_B_effective_days", 0) or 0)
#|    prefault_B_common_cause_overlap_days = int(evidence_row.get("prefault_B_common_cause_overlap_days", 0) or 0)
#|    subgroup_candidate_count = int(evidence_row.get("subgroup_candidate_panel_count", 0) or 0)
#|    if prefault_B_common_cause_overlap_days > 0 and subgroup_candidate_count >= 3:
#|        return "site_event/group_off 및 동일 subgroup 동시 흔들림을 먼저 재확인"
#|    if prefault_B_common_cause_overlap_days > 0 and prefault_B_effective_days == 0:
#|        return "site_event/group_off 공통원인 여부를 먼저 재확인"
#|    if subgroup_candidate_count >= 3 and prefault_B_effective_days == 0:
#|        return "동일 subgroup 동시 흔들림과 공통 외란 여부를 먼저 재확인"
#|    if "오염" in top1:
#|        return "세척 전후 추세 비교와 추가 관찰 권고"
#|    if "음영" in top1:
#|        return "인접 음영 구조와 시간대별 반복 여부 재확인 권고"
#|    if "접촉" in top1 or "끊김" in top1:
#|        return "다음 수집 주기 재확인 후 접속부 점검 여부 판단"
#|    if grade == "고위험 관찰":
#|        return "가까운 주기 재확인과 현장 비교 점검 권고"
#|    if axes:
#|        return f"{axes} 축 모니터링 유지"
#|    return "지속 모니터링 유지"
#|
#|
#|def strict_trigger_common_cause_text(evidence_row: dict[str, object]) -> str:
#|    if bool(evidence_row.get("strict_trigger_proximal_common_cause_flag")):
#|        return "strict_trigger 근처 공통원인 흔들림 동반"
#|    return ""
#|
#|
#|def fault_signal_path_text(evidence_row: dict[str, object]) -> str:
#|    final_days = int(evidence_row.get("final_days", 0) or 0)
#|    critical_days = int(evidence_row.get("critical_days", 0) or 0)
#|    critical_confirmed_days = int(evidence_row.get("critical_confirmed_days", 0) or 0)
#|    critical_sources = normalize_text(evidence_row.get("critical_sources_csv"))
#|    if final_days > 0:
#|        return "최종 고장 신호 경로"
#|    if critical_confirmed_days > 0:
#|        return "강한 고장 신호 확정 경로"
#|    if critical_days > 0:
#|        return "vdrop 강신호 경로" if "vdrop" in critical_sources else "강한 고장 신호 경로"
#|    return "고장 신호 관측"
#|
#|
#|def fault_signal_summary_text(evidence_row: dict[str, object]) -> str:
#|    final_days = int(evidence_row.get("final_days", 0) or 0)
#|    critical_days = int(evidence_row.get("critical_days", 0) or 0)
#|    critical_confirmed_days = int(evidence_row.get("critical_confirmed_days", 0) or 0)
#|    critical_sources = normalize_text(evidence_row.get("critical_sources_csv"))
#|    parts: list[str] = []
#|    if final_days > 0:
#|        parts.append(f"최종 고장 신호 {final_days}일")
#|        if critical_confirmed_days > 0:
#|            parts.append("강한 고장 신호 확정이 함께 관측됨")
#|        elif critical_days > 0:
#|            parts.append("강한 고장 신호가 함께 관측됨")
#|    elif critical_confirmed_days > 0:
#|        parts.append(f"강한 고장 신호 확정 {critical_confirmed_days}일")
#|    elif critical_days > 0:
#|        parts.append(f"강한 고장 신호 {critical_days}일")
#|    if "vdrop" in critical_sources:
#|        parts.append("vdrop 전기 신호 동반")
#|    if bool(evidence_row.get("strict_trigger_proximal_common_cause_flag")):
#|        parts.append("strict_trigger 근처 공통원인 흔들림 동반")
#|    return " / ".join(parts) if parts else "고장 신호 관측"
#|
#|
#|def fault_signal_action_text(evidence_row: dict[str, object]) -> str:
#|    top1 = normalize_text(evidence_row.get("1순위_의심원인_ko"))
#|    if bool(evidence_row.get("strict_trigger_proximal_common_cause_flag")):
#|        return "패널 국소 고장 신호와 함께 strict_trigger 근처 공통원인 여부도 동시 확인"
#|    if "다이오드" in top1 or "국소 회로" in top1:
#|        return "현장 점검 후 다이오드·국소 회로 이상 여부 우선 확인"
#|    if "접촉" in top1 or "끊김" in top1 or "개방" in top1:
#|        return "배선·접속부 우선 점검"
#|    if "측정" in top1 or "응답" in top1:
#|        return "MLPE/계측값과 접속 상태 동시 점검"
#|    if "외부 전원" in top1:
#|        return "패널 국소 이상보다 외부 전원/공통 원인 먼저 확인"
#|    return "현장 점검과 최근 작업 이력 확인 권고"
#|
#|
#|def build_precursor_report_df(evidence_df: pd.DataFrame) -> pd.DataFrame:
#|    if evidence_df is None or evidence_df.empty:
#|        return pd.DataFrame(columns=PRECURSOR_REPORT_OUTPUT_COLS)
#|
#|    rows: list[dict[str, object]] = []
#|    for _, row in evidence_df.fillna("").iterrows():
#|        precursor_date = normalize_text(row.get("전조날짜"))
#|        evidence_row = row.to_dict()
#|        if not precursor_date or not has_precursor_signal(evidence_row) or has_hard_fault_evidence(evidence_row):
#|            continue
#|        rows.append(
#|            {
#|                "site": normalize_text(row.get("site")),
#|                "panel_id": normalize_text(row.get("panel_id")),
#|                "운영 판정": normalize_text(row.get("운영해석등급_ko")) or "전조 후보",
#|                "판정 근거": report_reason_text(evidence_row),
#|                "전조날짜": precursor_date,
#|                "전조 축": report_precursor_axes_text(evidence_row),
#|                "대표 전조 신호": report_precursor_signal_text(evidence_row),
#|                "전조 요약": normalize_text(row.get("근거요약_ko")),
#|                "상위 해석 후보": normalize_text(row.get("1순위_의심원인_ko")),
#|                "기존 알고리즘 source": display_existing_algorithm_source(
#|                    row.get("커널로그 기존 알고리즘")
#|                ),
#|                "패턴 설명": pattern_explainer(evidence_row, soften_hard_language=True),
#|                "모니터링 권고": precursor_monitoring_action_text(evidence_row),
#|                "공통원인 위험": precursor_common_cause_risk_text(evidence_row),
#|                "권고 검토 레인": precursor_review_lane_text(evidence_row),
#|                "EWS 전조 일수": int(row.get("ews_warning_days", 0) or 0),
#|                "pre_alarm 일수": int(row.get("pre_alarm_days", 0) or 0),
#|                "pre_ews 일수": int(row.get("pre_ews_days", 0) or 0),
#|                "Option B 유효 일수": int(row.get("prefault_B_effective_days", 0) or 0),
#|                "공통원인 겹침 일수": int(row.get("prefault_B_common_cause_overlap_days", 0) or 0),
#|                "AE 전조 조건 일수": int(row.get("prefault_cond_ae_days", 0) or 0),
#|                "DTW 전조 조건 일수": int(row.get("prefault_cond_dtw_days", 0) or 0),
#|            }
#|        )
#|    return (
#|        pd.DataFrame(rows)
#|        .reindex(columns=PRECURSOR_REPORT_OUTPUT_COLS)
#|        .sort_values(["site", "panel_id"], ascending=[True, True])
#|        .reset_index(drop=True)
#|    )
#|
#|
#|def build_fault_signal_report_df(evidence_df: pd.DataFrame) -> pd.DataFrame:
#|    if evidence_df is None or evidence_df.empty:
#|        return pd.DataFrame(columns=FAULT_SIGNAL_REPORT_OUTPUT_COLS)
#|
#|    rows: list[dict[str, object]] = []
#|    for _, row in evidence_df.fillna("").iterrows():
#|        evidence_row = row.to_dict()
#|        if not has_hard_fault_evidence(evidence_row):
#|            continue
#|        event_fields = event_display_fields(evidence_row)
#|        rows.append(
#|            {
#|                "site": normalize_text(row.get("site")),
#|                "group root": normalize_text(row.get("group_root")),
#|                "subgroup base": normalize_text(row.get("subgroup_base")),
#|                "panel_id": normalize_text(row.get("panel_id")),
#|                "동일 subgroup row 수": int(row.get("subgroup_candidate_panel_count", 0) or 0),
#|                "운영 판정": normalize_text(row.get("운영해석등급_ko")) or display_signal_grade(row),
#|                "확정 경로": fault_signal_path_text(evidence_row),
#|                "고장 신호 요약": fault_signal_summary_text(evidence_row),
#|                "전조 시작일": normalize_text(row.get("전조날짜")),
#|                "신호 기준일": normalize_text(row.get("고장날짜")),
#|                "사건유형": normalize_text(row.get("사건유형_ko")),
#|                "사건 종결 요약": event_fields.get("사건 종결 요약", ""),
#|                "근접 공통원인": strict_trigger_common_cause_text(evidence_row),
#|                "상위 해석 후보": normalize_text(row.get("1순위_의심원인_ko")),
#|                "기존 알고리즘 source": display_existing_algorithm_source(
#|                    row.get("커널로그 기존 알고리즘")
#|                ),
#|                "패턴 설명": pattern_explainer(evidence_row),
#|                "현장 점검 권고": fault_signal_action_text(evidence_row),
#|            }
#|        )
#|    working = pd.DataFrame(rows)
#|    working = attach_fault_signal_cluster_columns(working)
#|    working = (
#|        working.reindex(columns=FAULT_SIGNAL_REPORT_OUTPUT_COLS)
#|        .sort_values(["site", "subgroup base", "신호 기준일", "panel_id"], ascending=[True, True, True, True])
#|        .reset_index(drop=True)
#|    )
#|    if "동일 cluster row 수" in working.columns:
#|        working["동일 cluster row 수"] = working["동일 cluster row 수"].fillna(0).astype(int)
#|    return working
#|
#|
#|def nonempty_sheet_df(df: pd.DataFrame, note: str) -> pd.DataFrame:
#|    if not df.empty:
#|        return df
#|    return pd.DataFrame([{"note": note}])
#|
#|
#|def signal_label_text(record: dict[str, object]) -> str:
#|    labels: list[str] = []
#|    if bool(record.get("event_A")):
#|        labels.append("event_A")
#|    if bool(record.get("v_drop")):
#|        labels.append("v_drop")
#|    if bool(record.get("critical_fault")):
#|        labels.append("critical_fault")
#|    if bool(record.get("critical_suspect")):
#|        labels.append("critical_suspect")
#|    if bool(record.get("critical_confirmed")):
#|        labels.append("critical_confirmed")
#|    if bool(record.get("fault_like_day")):
#|        labels.append("fault_like")
#|    if bool(record.get("final_fault")):
#|        labels.append("final_fault")
#|    if bool(record.get("ews_warning")):
#|        labels.append("ews_warning")
#|    if bool(record.get("pre_alarm")):
#|        labels.append("pre_alarm")
#|    if bool(record.get("pre_ews")):
#|        labels.append("pre_ews")
#|    if bool(record.get("site_event_soft")):
#|        labels.append("site_event_soft")
#|    if bool(record.get("site_event_hard")):
#|        labels.append("site_event_hard")
#|    if bool(record.get("group_off_date")):
#|        labels.append("group_off")
#|    if bool(record.get("prefault_B")):
#|        labels.append("prefault_B")
#|    if bool(record.get("prefault_B_effective")):
#|        labels.append("prefault_B_effective")
#|    if bool(record.get("prefault_B_common_cause_overlap")):
#|        labels.append("prefault_B_common_cause_overlap")
#|    if bool(record.get("prefault_cond_mid")):
#|        labels.append("prefault_mid")
#|    if bool(record.get("prefault_cond_ae")):
#|        labels.append("prefault_ae")
#|    if bool(record.get("prefault_cond_dtw")):
#|        labels.append("prefault_dtw")
#|    if bool(record.get("prefault_cond_ews")):
#|        labels.append("prefault_ews")
#|    subtype = normalize_text(record.get("anom_subtype"))
#|    if subtype:
#|        labels.append(f"subtype:{subtype}")
#|    return ",".join(labels)
#|
#|
#|def auto_fit_workbook_columns(path: Path) -> None:
#|    try:
#|        from openpyxl import load_workbook
#|        from openpyxl.utils import get_column_letter
#|    except ModuleNotFoundError as exc:
#|        raise SystemExit(
#|            "openpyxl is required to generate fault_panel_result_detailed_report_v1.xlsx"
#|        ) from exc
#|
#|    workbook = load_workbook(path)
#|    for worksheet in workbook.worksheets:
#|        if worksheet.max_row >= 2:
#|            worksheet.freeze_panes = "A2"
#|            worksheet.auto_filter.ref = worksheet.dimensions
#|        for column_cells in worksheet.columns:
#|            column_letter = get_column_letter(column_cells[0].column)
#|            max_len = max(
#|                len(str(cell.value)) if cell.value is not None else 0
#|                for cell in column_cells
#|            )
#|            worksheet.column_dimensions[column_letter].width = min(max(max_len + 2, 10), 60)
#|    workbook.save(path)
#|
#|
#|def build_detailed_report_frames(
#|    output_root: Path,
#|    sites: list[str],
#|    baseline_comparison: dict[str, object],
#|    live_chain_result: dict[str, object],
#|    raw_only_chain_result: dict[str, object],
#|    live_preview_df: pd.DataFrame,
#|    raw_only_preview_df: pd.DataFrame,
#|) -> dict[str, pd.DataFrame]:
#|    overview_df = pd.DataFrame(
#|        [
#|            {"section": "sites", "key": "sites_csv", "value": ",".join(sites)},
#|            {
#|                "section": "baseline",
#|                "key": "all_sites_match",
#|                "value": str(baseline_comparison.get("all_sites_match")),
#|            },
#|            {
#|                "section": "live_chain",
#|                "key": "status_ko",
#|                "value": normalize_text(live_chain_result.get("status_ko")),
#|            },
#|            {
#|                "section": "live_chain",
#|                "key": "fixed_fault_reference_exact_match",
#|                "value": str(
#|                    live_chain_result.get("fixed_fault_reference_compare", {}).get("exact_match")
#|                ),
#|            },
#|            {
#|                "section": "raw_only_chain",
#|                "key": "status_ko",
#|                "value": normalize_text(raw_only_chain_result.get("status_ko")),
#|            },
#|            {
#|                "section": "raw_only_chain",
#|                "key": "compare_status_ko",
#|                "value": normalize_text(
#|                    raw_only_chain_result.get("fixed_fault_reference_compare", {}).get("status_ko")
#|                ),
#|            },
#|            {
#|                "section": "raw_only_chain",
#|                "key": "candidate_row_count",
#|                "value": str(
#|                    raw_only_chain_result.get("fixed_fault_reference_compare", {}).get(
#|                        "candidate_row_count"
#|                    )
#|                ),
#|            },
#|            {
#|                "section": "raw_only_chain",
#|                "key": "reference_row_count",
#|                "value": str(
#|                    raw_only_chain_result.get("fixed_fault_reference_compare", {}).get(
#|                        "reference_row_count"
#|                    )
#|                ),
#|            },
#|            {
#|                "section": "notes",
#|                "key": "attention_grade_note_ko",
#|                "value": (
#|                    "운영해석등급_ko는 상세 리포트용 보조 등급이다. core verdict를 바꾸지 않고 "
#|                    "확정/고위험 관찰/관찰을 사람이 읽기 쉽게 정리한다."
#|                ),
#|            },
#|        ]
#|    )
#|
#|    frames: dict[str, pd.DataFrame] = {
#|        "overview": overview_df,
#|        "current_preview": nonempty_sheet_df(
#|            live_preview_df.copy(),
#|            "live current preview not available",
#|        ),
#|        "raw_only_preview": nonempty_sheet_df(
#|            raw_only_preview_df.copy(),
#|            "raw-only preview not available",
#|        ),
#|    }
#|
#|    if not raw_only_chain_result.get("requested") or normalize_text(raw_only_chain_result.get("status_ko")) != "completed":
#|        frames["raw_only_evidence"] = pd.DataFrame(
#|            [{"note": "raw-only chain not completed; detailed evidence unavailable"}]
#|        )
#|        frames["raw_only_candidate_scores"] = pd.DataFrame(
#|            [{"note": "raw-only chain not completed; candidate score matrix unavailable"}]
#|        )
#|        frames["raw_only_timeline"] = pd.DataFrame(
#|            [{"note": "raw-only chain not completed; timeline unavailable"}]
#|        )
#|        frames["raw_only_daily_log"] = pd.DataFrame(
#|            [{"note": "raw-only chain not completed; all-date log unavailable"}]
#|        )
#|        frames["raw_only_cluster"] = pd.DataFrame(
#|            [{"note": "raw-only chain not completed; cluster summary unavailable"}]
#|        )
#|        frames["precursor_report"] = pd.DataFrame(columns=PRECURSOR_REPORT_OUTPUT_COLS)
#|        frames["fault_signal_report"] = pd.DataFrame(columns=FAULT_SIGNAL_REPORT_OUTPUT_COLS)
#|        frames["definitions"] = pd.DataFrame(
#|            [
#|                {
#|                    "항목": "확정",
#|                    "설명": "최종 고장 신호 또는 강한 고장 신호가 관측된 상태",
#|                },
#|                {
#|                    "항목": "고위험 관찰",
#|                    "설명": "즉시 확정에 쓰는 신호는 없지만 EWS/AE/DTW 전조가 강하게 누적",
#|                },
#|                {"항목": "관찰", "설명": "약한 이상 또는 간헐 이상으로 계속 관찰 필요"},
#|            ]
#|        )
#|        return frames
#|
#|    workspace_root = Path(str(raw_only_chain_result["workspace_root"]))
#|    raw_only_common = load_raw_only_common_module()
#|    runtime_heuristic = load_runtime_heuristic_module()
#|    audit_path = workspace_root / "_share" / raw_only_common.RUNTIME_AUDIT_OUTPUT_NAME
#|    heuristic_path = workspace_root / "_share" / raw_only_common.RUNTIME_HEURISTIC_OUTPUT_NAME
#|    verdict_path = workspace_root / "_share" / raw_only_common.RUNTIME_VERDICT_OUTPUT_NAME
#|    audit_df = pd.read_csv(audit_path, encoding="utf-8-sig", low_memory=False)
#|    heuristic_df = pd.read_csv(heuristic_path, encoding="utf-8-sig", low_memory=False)
#|    verdict_df = pd.read_csv(verdict_path, encoding="utf-8-sig", low_memory=False)
#|    audit_df["site"] = audit_df["site"].astype(str)
#|    audit_df["panel_id"] = audit_df["panel_id"].astype(str)
#|    heuristic_df["site"] = heuristic_df["site"].astype(str)
#|    heuristic_df["panel_id"] = heuristic_df["panel_id"].astype(str)
#|    verdict_df["site"] = verdict_df["site"].astype(str)
#|    verdict_df["panel_id"] = verdict_df["panel_id"].astype(str)
#|
#|    audit_lookup = {
#|        row_key(row["site"], row["panel_id"]): row for row in audit_df.to_dict(orient="records")
#|    }
#|    heuristic_lookup = {
#|        row_key(row["site"], row["panel_id"]): row for row in heuristic_df.to_dict(orient="records")
#|    }
#|    verdict_lookup = {
#|        row_key(row["site"], row["panel_id"]): row for row in verdict_df.to_dict(orient="records")
#|    }
#|
#|    per_site_core = {site: load_panel_day_core_from_workspace(workspace_root, site) for site in sites}
#|    per_site_gate = {site: load_gate_from_workspace(workspace_root, site) for site in sites}
#|    preview_with_group_keys = raw_only_preview_df.copy()
#|    if not preview_with_group_keys.empty:
#|        preview_with_group_keys["group_root"] = preview_with_group_keys["panel_id"].map(
#|            panel_group_root
#|        )
#|        preview_with_group_keys["subgroup_base"] = preview_with_group_keys["panel_id"].map(
#|            panel_subgroup_base
#|        )
#|    group_root_counts = (
#|        preview_with_group_keys.groupby(["site", "group_root"]).size().to_dict()
#|        if not preview_with_group_keys.empty
#|        else {}
#|    )
#|    subgroup_counts = (
#|        preview_with_group_keys.groupby(["site", "subgroup_base"]).size().to_dict()
#|        if not preview_with_group_keys.empty
#|        else {}
#|    )
#|
#|    evidence_rows: list[dict[str, object]] = []
#|    candidate_score_rows: list[dict[str, object]] = []
#|    timeline_rows: list[dict[str, object]] = []
#|    all_date_rows: list[dict[str, object]] = []
#|    for _, preview_row in raw_only_preview_df.iterrows():
#|        site = normalize_text(preview_row.get("site"))
#|        panel_id = normalize_text(preview_row.get("panel_id"))
#|        group_root = panel_group_root(panel_id)
#|        subgroup_base = panel_subgroup_base(panel_id)
#|        base = group_root
#|        key = row_key(site, panel_id)
#|        audit_row = audit_lookup.get(key, {})
#|        heuristic_row = heuristic_lookup.get(key, {})
#|        verdict_row = verdict_lookup.get(key, {})
#|        merged_for_scores = dict(verdict_row)
#|        merged_for_scores.update(audit_row)
#|        score_map, score_notes = runtime_heuristic.score_row(merged_for_scores)
#|        ranked_candidates = runtime_heuristic.choose_ranked_candidates(score_map)
#|        top_score = ranked_candidates[0][1] if ranked_candidates else 0
#|        panel_core = per_site_core[site].loc[per_site_core[site]["panel_id"].eq(panel_id)].copy()
#|        panel_gate = per_site_gate[site].loc[per_site_gate[site]["panel_id"].eq(panel_id)].copy()
#|        representative = representative_signal_row(panel_core)
#|
#|        evidence_row: dict[str, object] = {
#|            "site": site,
#|            "panel_id": panel_id,
#|            "base": group_root,
#|            "group_root": group_root,
#|            "subgroup_base": subgroup_base,
#|            "base_candidate_panel_count": int(group_root_counts.get((site, group_root), 0)),
#|            "subgroup_candidate_panel_count": int(subgroup_counts.get((site, subgroup_base), 0)),
#|            "패널고장여부_ko": normalize_text(preview_row.get("패널고장여부_ko")),
#|            "사건유형_ko": normalize_text(preview_row.get("사건유형_ko")),
#|            "최종고장양상_ko": normalize_text(preview_row.get("최종고장양상_ko")),
#|            "라벨된 fault": normalize_text(preview_row.get("라벨된 fault")),
#|            "1순위_의심원인_ko": normalize_text(preview_row.get("1순위_의심원인_ko")),
#|            "2순위_의심원인_ko": normalize_text(preview_row.get("2순위_의심원인_ko")),
#|            "3순위_의심원인_ko": normalize_text(preview_row.get("3순위_의심원인_ko")),
#|            "커널로그 기존 알고리즘": normalize_text(preview_row.get("커널로그 기존 알고리즘")),
#|            "final_days": bool_count(panel_core, "final_fault"),
#|            "critical_days": bool_count(panel_core, "critical_fault"),
#|            "fault_like_days": bool_count(panel_core, "fault_like_day"),
#|            "event_A_days": bool_count(panel_core, "event_A"),
#|            "ews_warning_days": bool_count(panel_gate, "ews_warning"),
#|            "pre_alarm_days": bool_count(panel_gate, "pre_alarm"),
#|            "pre_ews_days": bool_count(panel_gate, "pre_ews"),
#|            "critical_confirmed_days": bool_count(panel_core, "critical_confirmed"),
#|            "prefault_B_days": bool_count(panel_gate, "prefault_B"),
#|            "prefault_B_effective_days": bool_count(panel_gate, "prefault_B_effective"),
#|            "prefault_B_common_cause_overlap_days": bool_count(panel_gate, "prefault_B_common_cause_overlap"),
#|            "prefault_cond_mid_days": bool_count(panel_gate, "prefault_cond_mid"),
#|            "prefault_cond_ae_days": bool_count(panel_gate, "prefault_cond_ae"),
#|            "prefault_cond_dtw_days": bool_count(panel_gate, "prefault_cond_dtw"),
#|            "prefault_cond_ews_days": bool_count(panel_gate, "prefault_cond_ews"),
#|            "critical_sources_csv": unique_csv(panel_core.get("critical_source", pd.Series(dtype=object))),
#|            "anom_subtypes_csv": unique_csv(panel_core.get("anom_subtype", pd.Series(dtype=object))),
#|            "원인후보_top1_score": heuristic_row.get("원인후보_top1_score", ""),
#|            "원인후보_top2_score": heuristic_row.get("원인후보_top2_score", ""),
#|            "원인후보_top3_score": heuristic_row.get("원인후보_top3_score", ""),
#|            "원인후보_경합상태_ko": normalize_text(heuristic_row.get("원인후보_경합상태_ko")),
#|            "원인후보_공동상위후보_csv": normalize_text(heuristic_row.get("원인후보_공동상위후보_csv")),
#|            "원인후보_실증우선확인_ko": normalize_text(heuristic_row.get("원인후보_실증우선확인_ko")),
#|            "원인후보_신뢰도_ko": normalize_text(heuristic_row.get("원인후보_신뢰도_ko")),
#|            "원인후보_해석메모_ko": normalize_text(heuristic_row.get("원인후보_해석메모_ko")),
#|            "사건이력_ko": normalize_text(verdict_row.get("사건이력_ko")),
#|            "대표판정_ko": normalize_text(verdict_row.get("대표판정_ko")),
#|            "운영최초전조발견일": normalize_text(verdict_row.get("운영최초전조발견일")),
#|            "사건해석상전조시작일": normalize_text(verdict_row.get("사건해석상전조시작일")),
#|            "세부fault_기준일": normalize_text(verdict_row.get("세부fault_기준일")),
#|            "판정주의_ko": normalize_text(verdict_row.get("판정주의_ko")),
#|            "strict_trigger_proximal_common_cause_flag": int(
#|                audit_row.get("strict_trigger_proximal_common_cause_flag", 0) or 0
#|            ),
#|            "warning_proximal_common_cause_flag": int(
#|                audit_row.get("warning_proximal_common_cause_flag", 0) or 0
#|            ),
#|            "대표critical_source": normalize_text(representative.get("critical_source")),
#|            "대표anom_subtype": normalize_text(representative.get("anom_subtype")),
#|            "대표mid_ratio": representative.get("mid_ratio", ""),
#|            "대표mid_v_ratio": representative.get("mid_v_ratio", ""),
#|            "대표mid_i_ratio": representative.get("mid_i_ratio", ""),
#|            "대표recon_error": representative.get("recon_error", ""),
#|            "대표dtw_dist": representative.get("dtw_dist", ""),
#|            "대표hs_score": representative.get("hs_score", ""),
#|            "대표event_A": normalize_text(representative.get("event_A")),
#|            "대표critical_fault": normalize_text(representative.get("critical_fault")),
#|            "대표critical_confirmed": normalize_text(representative.get("critical_confirmed")),
#|            "대표final_fault": normalize_text(representative.get("final_fault")),
#|        }
#|        evidence_row["전조날짜"] = choose_display_precursor_date(
#|            event_type_ko=preview_row.get("사건유형_ko"),
#|            interpreted_onset_date=verdict_row.get("사건해석상전조시작일"),
#|            first_warning_date=audit_row.get("earliest_warning_date"),
#|        )
#|        evidence_row["고장날짜"] = choose_display_fault_date(
#|            fault_date=verdict_row.get("세부fault_기준일"),
#|            strict_trigger_date=audit_row.get("strict_trigger_date"),
#|            first_final_fault_date=audit_row.get("first_final_fault_date"),
#|        )
#|        evidence_row["운영해석등급_ko"] = report_attention_grade(evidence_row)
#|        evidence_row["근거요약_ko"] = report_reason_text(evidence_row)
#|        evidence_rows.append(evidence_row)
#|        for rank_idx, (candidate, score) in enumerate(ranked_candidates, start=1):
#|            candidate_score_rows.append(
#|                {
#|                    "site": site,
#|                    "panel_id": panel_id,
#|                    "base": base,
#|                    "운영해석등급_ko": evidence_row["운영해석등급_ko"],
#|                    "패널고장여부_ko": evidence_row["패널고장여부_ko"],
#|                    "사건유형_ko": evidence_row["사건유형_ko"],
#|                    "최종고장양상_ko": evidence_row["최종고장양상_ko"],
#|                    "라벨된 fault": evidence_row["라벨된 fault"],
#|                    "후보순위": rank_idx,
#|                    "후보canonical_ko": candidate,
#|                    "후보표시명_ko": display_heuristic_name(candidate),
#|                    "후보점수": score,
#|                    "top1_flag": rank_idx == 1,
#|                    "공동상위_flag": bool(score == top_score and top_score > 0),
#|                    "원인후보_경합상태_ko": normalize_text(heuristic_row.get("원인후보_경합상태_ko")),
#|                    "원인후보_신뢰도_ko": normalize_text(heuristic_row.get("원인후보_신뢰도_ko")),
#|                    "커널로그 기존 알고리즘": evidence_row["커널로그 기존 알고리즘"],
#|                    "critical_sources_csv": evidence_row["critical_sources_csv"],
#|                    "anom_subtypes_csv": evidence_row["anom_subtypes_csv"],
#|                    "점수근거메모_ko": ", ".join(score_notes),
#|                    "후보해석메모_ko": normalize_text(heuristic_row.get("원인후보_해석메모_ko")),
#|                }
#|            )
#|
#|        core_cols = [
#|            "date",
#|            "recon_error",
#|            "dtw_dist",
#|            "hs_score",
#|            "mid_ratio",
#|            "mid_peer",
#|            "mid_v_ratio",
#|            "mid_i_ratio",
#|            "last_ratio",
#|            "last_peer",
#|            "event_A",
#|            "v_drop",
#|            "critical_fault",
#|            "critical_suspect",
#|            "critical_confirmed",
#|            "group_off_like",
#|            "fault_like_day",
#|            "final_fault",
#|            "critical_source",
#|            "anom_level",
#|            "anom_subtype",
#|        ]
#|        gate_cols = [
#|            "date",
#|            "ews_warning",
#|            "pre_alarm",
#|            "pre_ews",
#|            "site_event_soft",
#|            "site_event_hard",
#|            "group_off_date",
#|            "prefault_B",
#|            "prefault_B_effective",
#|            "prefault_B_common_cause_overlap",
#|            "prefault_cond_mid",
#|            "prefault_cond_ae",
#|            "prefault_cond_dtw",
#|            "prefault_cond_ews",
#|        ]
#|        merged = panel_core.loc[:, [c for c in core_cols if c in panel_core.columns]].merge(
#|            panel_gate.loc[:, [c for c in gate_cols if c in panel_gate.columns]],
#|            on="date",
#|            how="outer",
#|        )
#|        signal_cols = [
#|            "event_A",
#|            "critical_fault",
#|            "critical_suspect",
#|            "critical_confirmed",
#|            "group_off_like",
#|            "fault_like_day",
#|            "final_fault",
#|            "ews_warning",
#|            "pre_alarm",
#|            "pre_ews",
#|            "site_event_soft",
#|            "site_event_hard",
#|            "group_off_date",
#|            "prefault_B",
#|            "prefault_B_effective",
#|            "prefault_B_common_cause_overlap",
#|            "prefault_cond_mid",
#|            "prefault_cond_ae",
#|            "prefault_cond_dtw",
#|            "prefault_cond_ews",
#|        ]
#|        available_signal_cols = [column for column in signal_cols if column in merged.columns]
#|        signal_mask = merged[available_signal_cols].fillna(False).astype(bool).any(axis=1)
#|        subtype_mask = merged.get("anom_subtype", pd.Series(dtype=object)).astype(str).str.contains(
#|            "degradation|fault_like|shadow_like|critical",
#|            case=False,
#|            na=False,
#|        )
#|        merged = merged.sort_values("date").reset_index(drop=True)
#|        merged["신호있는날_flag"] = (signal_mask | subtype_mask).reset_index(drop=True)
#|        for record in merged.to_dict(orient="records"):
#|            all_date_rows.append(
#|                {
#|                    "site": site,
#|                    "panel_id": panel_id,
#|                    "base": base,
#|                    "운영해석등급_ko": evidence_row["운영해석등급_ko"],
#|                    "1순위_의심원인_ko": evidence_row["1순위_의심원인_ko"],
#|                    "date": pd.to_datetime(record.get("date"), errors="coerce"),
#|                    "신호있는날_flag": bool(record.get("신호있는날_flag")),
#|                    "관찰포인트_csv": signal_label_text(record),
#|                    "recon_error": record.get("recon_error"),
#|                    "dtw_dist": record.get("dtw_dist"),
#|                    "hs_score": record.get("hs_score"),
#|                    "mid_ratio": record.get("mid_ratio"),
#|                    "mid_peer": record.get("mid_peer"),
#|                    "mid_v_ratio": record.get("mid_v_ratio"),
#|                    "mid_i_ratio": record.get("mid_i_ratio"),
#|                    "last_ratio": record.get("last_ratio"),
#|                    "last_peer": record.get("last_peer"),
#|                    "event_A": record.get("event_A"),
#|                    "v_drop": record.get("v_drop"),
#|                    "critical_fault": record.get("critical_fault"),
#|                    "critical_suspect": record.get("critical_suspect"),
#|                    "critical_confirmed": record.get("critical_confirmed"),
#|                    "fault_like_day": record.get("fault_like_day"),
#|                    "final_fault": record.get("final_fault"),
#|                    "ews_warning": record.get("ews_warning"),
#|                    "pre_alarm": record.get("pre_alarm"),
#|                    "pre_ews": record.get("pre_ews"),
#|                    "site_event_soft": record.get("site_event_soft"),
#|                    "site_event_hard": record.get("site_event_hard"),
#|                    "group_off_date": record.get("group_off_date"),
#|                    "prefault_B": record.get("prefault_B"),
#|                    "prefault_B_effective": record.get("prefault_B_effective"),
#|                    "prefault_B_common_cause_overlap": record.get("prefault_B_common_cause_overlap"),
#|                    "prefault_cond_mid": record.get("prefault_cond_mid"),
#|                    "prefault_cond_ae": record.get("prefault_cond_ae"),
#|                    "prefault_cond_dtw": record.get("prefault_cond_dtw"),
#|                    "prefault_cond_ews": record.get("prefault_cond_ews"),
#|                    "critical_source": normalize_text(record.get("critical_source")),
#|                    "anom_level": normalize_text(record.get("anom_level")),
#|                    "anom_subtype": normalize_text(record.get("anom_subtype")),
#|                }
#|            )
#|        for record in merged.loc[merged["신호있는날_flag"]].to_dict(orient="records"):
#|            timeline_rows.append(
#|                {
#|                    "site": site,
#|                    "panel_id": panel_id,
#|                    "base": base,
#|                    "운영해석등급_ko": evidence_row["운영해석등급_ko"],
#|                    "1순위_의심원인_ko": evidence_row["1순위_의심원인_ko"],
#|                    "date": pd.to_datetime(record.get("date"), errors="coerce"),
#|                    "recon_error": record.get("recon_error"),
#|                    "dtw_dist": record.get("dtw_dist"),
#|                    "hs_score": record.get("hs_score"),
#|                    "mid_ratio": record.get("mid_ratio"),
#|                    "mid_peer": record.get("mid_peer"),
#|                    "mid_v_ratio": record.get("mid_v_ratio"),
#|                    "mid_i_ratio": record.get("mid_i_ratio"),
#|                    "last_ratio": record.get("last_ratio"),
#|                    "last_peer": record.get("last_peer"),
#|                    "event_A": record.get("event_A"),
#|                    "v_drop": record.get("v_drop"),
#|                    "critical_fault": record.get("critical_fault"),
#|                    "critical_suspect": record.get("critical_suspect"),
#|                    "critical_confirmed": record.get("critical_confirmed"),
#|                    "fault_like_day": record.get("fault_like_day"),
#|                    "final_fault": record.get("final_fault"),
#|                    "ews_warning": record.get("ews_warning"),
#|                    "pre_alarm": record.get("pre_alarm"),
#|                    "pre_ews": record.get("pre_ews"),
#|                    "site_event_soft": record.get("site_event_soft"),
#|                    "site_event_hard": record.get("site_event_hard"),
#|                    "group_off_date": record.get("group_off_date"),
#|                    "prefault_B": record.get("prefault_B"),
#|                    "prefault_B_effective": record.get("prefault_B_effective"),
#|                    "prefault_B_common_cause_overlap": record.get("prefault_B_common_cause_overlap"),
#|                    "prefault_cond_mid": record.get("prefault_cond_mid"),
#|                    "prefault_cond_ae": record.get("prefault_cond_ae"),
#|                    "prefault_cond_dtw": record.get("prefault_cond_dtw"),
#|                    "prefault_cond_ews": record.get("prefault_cond_ews"),
#|                    "critical_source": normalize_text(record.get("critical_source")),
#|                    "anom_level": normalize_text(record.get("anom_level")),
#|                    "anom_subtype": normalize_text(record.get("anom_subtype")),
#|                }
#|            )
#|
#|    evidence_df = pd.DataFrame(evidence_rows).sort_values(["site", "base", "panel_id"]).reset_index(drop=True)
#|    cluster_df = (
#|        evidence_df.groupby(["site", "base"], dropna=False)
#|        .agg(
#|            candidate_panels=("panel_id", "nunique"),
#|            확정_panel_count=("운영해석등급_ko", lambda s: int((s == "확정").sum())),
#|            고위험관찰_panel_count=("운영해석등급_ko", lambda s: int((s == "고위험 관찰").sum())),
#|            관찰_panel_count=("운영해석등급_ko", lambda s: int((s == "관찰").sum())),
#|            final_days_total=("final_days", "sum"),
#|            critical_days_total=("critical_days", "sum"),
#|            fault_like_days_total=("fault_like_days", "sum"),
#|            event_A_days_total=("event_A_days", "sum"),
#|            ews_warning_total=("ews_warning_days", "sum"),
#|            pre_ews_total=("pre_ews_days", "sum"),
#|            top1_candidates_csv=("1순위_의심원인_ko", lambda s: ",".join(sorted({normalize_text(v) for v in s if normalize_text(v)}))),
#|            labeled_fault_csv=("라벨된 fault", lambda s: ",".join(sorted({normalize_text(v) for v in s if normalize_text(v)}))),
#|        )
#|        .reset_index()
#|    )
#|    if not cluster_df.empty:
#|        cluster_df["군집해석_ko"] = cluster_df.apply(
#|            lambda row: (
#|                "군집 내 hard fault 포함"
#|                if int(row["확정_panel_count"]) > 0
#|                else "여러 패널이 함께 흔들려 공통 원인 가능성"
#|                if int(row["candidate_panels"]) >= 3
#|                else "소수 패널 관찰"
#|            ),
#|            axis=1,
#|        )
#|
#|    heuristic_definition_rows = [
#|        {
#|            "항목": "1/2/3순위_의심원인_ko",
#|            "설명": "한국어 표시용 heuristic candidate 라벨이며, internal code를 대신하지 않는다. 라벨은 엔지니어 친화적으로 유지하고 쉬운 설명은 definitions에서 별도로 붙인다",
#|        },
#|        *[
#|            {
#|                "항목": display_name,
#|                "설명": display_heuristic_note(display_name),
#|            }
#|            for display_name in DISPLAY_HEURISTIC_NAME_MAP.values()
#|        ],
#|    ]
#|
#|    definitions_df = pd.DataFrame(
#|        [
#|            {
#|                "항목": "definitions 시트",
#|                "설명": "상세 리포트 안에서 artifact 역할과 주요 컬럼 뜻을 짧게 설명하는 analyst/support glossary로, 읽기 순서나 auto-open 정책을 대신하지 않는다",
#|            },
#|            {
#|                "항목": "detailed report",
#|                "설명": "여러 row universe와 lineage를 함께 담는 analyst primary 문서로, current/master report를 대체하지 않는다",
#|            },
#|            {
#|                "항목": "official current",
#|                "설명": "frozen-support live chain 기준의 운영 공식 결과 묶음으로, detailed definitions에서는 역할과 공식성 차이만 짧게 설명한다",
#|            },
#|            {
#|                "항목": "raw_only current",
#|                "설명": "raw-only candidate 우주에서 strict current subset만 따로 보여주는 analyst/support 추가 자료로, official current를 대체하지 않는다",
#|            },
#|            {
#|                "항목": "운영해석등급_ko",
#|                "설명": "상세 리포트용 보조 등급으로 core verdict를 바꾸지 않고 사람이 읽기 쉽게 정리한 값",
#|            },
#|            {
#|                "항목": "확정",
#|                "설명": "최종 고장 신호 또는 강한 고장 신호가 존재하는 패널",
#|            },
#|            {
#|                "항목": "고위험 관찰",
#|                "설명": "즉시 확정에 쓰는 신호는 없지만 EWS, prefault_cond_ae/dtw/ews, fault_like 누적이 강한 패널",
#|            },
#|            {
#|                "항목": "관찰",
#|                "설명": "약한 이상 또는 간헐 이상으로 추가 추적이 필요한 패널",
#|            },
#|            {
#|                "항목": "precursor_report",
#|                "설명": "고장 신호가 아직 없는 precursor candidate만 따로 정리한 watchlist 성격의 보조표로, current artifact를 대체하지 않는다",
#|            },
#|            {
#|                "항목": "fault_signal_report",
#|                "설명": "raw-only candidate 우주에서 고장 신호가 이미 관측된 패널만 따로 정리한 analyst/support 보조표로, operator 기본 읽기 순서에는 직접 포함되지 않는다",
#|            },
#|            {
#|                "항목": "전조 축",
#|                "설명": "EWS/AE/DTW/규칙징후 중 어떤 축이 precursor candidate를 만들었는지 보여주는 묶음",
#|            },
#|            {
#|                "항목": "규칙징후",
#|                "설명": "pre_alarm, fault_like, 상대 전압 이탈 같은 규칙 기반 이상 징후를 완곡하게 묶은 표현",
#|            },
#|            {
#|                "항목": "Option B 유효 일수",
#|                "설명": "prefault_B 중 site_event/group_off 공통원인 겹침을 제외하고 실제 precursor 승격 설명에 반영한 일수",
#|            },
#|            {
#|                "항목": "공통원인 겹침 일수",
#|                "설명": "prefault_B가 켜졌지만 site_event/group_off와 직접 겹쳐 operator-facing precursor 승격에서는 별도 분리한 일수",
#|            },
#|            {
#|                "항목": "대표 전조 신호",
#|                "설명": "전조 표에서 누적된 핵심 신호를 짧게 요약한 값",
#|            },
#|            {
#|                "항목": "모니터링 권고",
#|                "설명": "precursor candidate에 대해 다음 수집 주기에서 무엇을 먼저 볼지 안내하는 운영 메모",
#|            },
#|            {
#|                "항목": "공통원인 위험",
#|                "설명": "site_event/group_off 겹침과 동일 subgroup 동시 흔들림을 바탕으로 panel-local precursor 해석을 얼마나 보수적으로 볼지 적은 보조 라벨",
#|            },
#|            {
#|                "항목": "권고 검토 레인",
#|                "설명": "일반 모니터링, 단일 패널 우선 추적, 공통원인 검토 중 다음 확인 방향을 짧게 정리한 값",
#|            },
#|            {
#|                "항목": "근접 공통원인",
#|                "설명": "raw-only 고장 신호 표에서 strict_trigger 기준 ±3일 안에 common-cause 이력이 같이 있으면 채우는 analyst/support 보조 값",
#|            },
#|            {
#|                "항목": "group root",
#|                "설명": "panel_id에서 마지막 두 서브인덱스를 제외한 넓은 family root로, 같은 상위 군집인지 보기 위한 값",
#|            },
#|            {
#|                "항목": "subgroup base",
#|                "설명": "panel_id에서 마지막 서브인덱스 하나만 제외한 하위 묶음으로, runtime common-cause 검토 단위에 더 가까운 값",
#|            },
#|            {
#|                "항목": "동일 subgroup row 수",
#|                "설명": "같은 raw-only current/fault-signal 우주에서 동일 subgroup base 아래 함께 잡힌 panel row 수로, row 수와 독립 사건 수를 혼동하지 않도록 돕는 값",
#|            },
#|            {
#|                "항목": "subgroup cluster",
#|                "설명": f"같은 subgroup base 안에서 신호 기준일 간격이 {FAULT_SIGNAL_CLUSTER_GAP_DAYS}일 이하인 row를 하나의 보조 cluster로 묶어 읽기 쉽게 만든 값",
#|            },
#|            {
#|                "항목": "동일 cluster row 수",
#|                "설명": "같은 subgroup cluster 안에 함께 들어간 panel row 수로, 대략적인 사건 뭉치를 읽기 쉽게 보조하는 값",
#|            },
#|            {
#|                "항목": "확정 경로",
#|                "설명": "raw-only 고장 신호 표에서 주된 고장 신호 경로 하나만 표시한 값",
#|            },
#|            {
#|                "항목": "고장 신호 요약",
#|                "설명": "고장 신호 지속 일수와 vdrop 같은 보조 근거를 함께 적은 요약",
#|            },
#|            {
#|                "항목": "현장 점검 권고",
#|                "설명": "raw-only 고장 신호 표에서 첫 현장 액션 우선순위를 짧게 적은 값",
#|            },
#|            {
#|                "항목": "strict_trigger_proximal_common_cause_flag",
#|                "설명": "raw-only audit에서 strict_trigger 기준 ±3일 안의 common-cause 이력을 잡는 내부 analyst flag",
#|            },
#|            {
#|                "항목": "warning_proximal_common_cause_flag",
#|                "설명": "raw-only audit에서 earliest_warning 기준 ±3일 안의 common-cause 이력을 잡는 내부 analyst flag로, 현재는 audit 전용",
#|            },
#|            {
#|                "항목": "raw_only_chain 주의",
#|                "설명": "raw-only candidate chain은 current/frozen 공식 결과보다 넓은 후보 우주를 보여주며, official current를 대체하지 않는다",
#|            },
#|            *heuristic_definition_rows,
#|        ]
#|    )
#|
#|    frames["raw_only_evidence"] = nonempty_sheet_df(
#|        evidence_df,
#|        "raw-only evidence rows unavailable",
#|    )
#|    frames["raw_only_candidate_scores"] = nonempty_sheet_df(
#|        pd.DataFrame(candidate_score_rows).sort_values(["site", "base", "panel_id", "후보순위"]).reset_index(drop=True),
#|        "raw-only candidate score matrix unavailable",
#|    )
#|    frames["raw_only_timeline"] = nonempty_sheet_df(
#|        pd.DataFrame(timeline_rows).sort_values(["site", "panel_id", "date"]).reset_index(drop=True),
#|        "raw-only timeline rows unavailable",
#|    )
#|    frames["raw_only_daily_log"] = nonempty_sheet_df(
#|        pd.DataFrame(all_date_rows).sort_values(["site", "panel_id", "date"]).reset_index(drop=True),
#|        "raw-only all-date log unavailable",
#|    )
#|    frames["raw_only_cluster"] = nonempty_sheet_df(
#|        cluster_df,
#|        "raw-only cluster summary unavailable",
#|    )
#|    frames["precursor_report"] = build_precursor_report_df(evidence_df)
#|    frames["fault_signal_report"] = build_fault_signal_report_df(evidence_df)
#|    frames["definitions"] = definitions_df
#|    return frames
#|
#|
#|def write_detailed_report_xlsx(path: Path, frames: dict[str, pd.DataFrame]) -> None:
#|    path.parent.mkdir(parents=True, exist_ok=True)
#|    with pd.ExcelWriter(path, engine="openpyxl") as writer:
#|        for sheet_name, df in frames.items():
#|            df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
#|    auto_fit_workbook_columns(path)
#|
#|
#|def stage_live_chain_workspace(output_root: Path, sites: list[str]) -> Path:
#|    workspace_root = output_root / "live_chain_workspace"
#|    if workspace_root.exists():
#|        shutil.rmtree(workspace_root)
#|    copy_tree(packaged_share_root(), workspace_root / "_share")
#|    for site in sites:
#|        copy_tree(output_root / "sites" / site / "output", workspace_root / "data" / site / "out")
#|    return workspace_root
#|
#|
#|def stage_raw_only_chain_workspace(output_root: Path, sites: list[str]) -> Path:
#|    workspace_root = output_root / "raw_only_chain_workspace"
#|    if workspace_root.exists():
#|        shutil.rmtree(workspace_root)
#|    for site in sites:
#|        copy_tree(output_root / "sites" / site / "output", workspace_root / "data" / site / "out")
#|    return workspace_root
#|
#|
#|def run_live_chain(output_root: Path, sites: list[str], baseline_comparison: dict[str, object]) -> dict[str, object]:
#|    support = packaged_live_chain_support()
#|    result_dir = output_root / "result" / "live_chain"
#|    result_dir.mkdir(parents=True, exist_ok=True)
#|    payload: dict[str, object] = {
#|        "requested": True,
#|        "supported": bool(support["supported"]),
#|        "support": support,
#|        "workspace_root": "",
#|        "result_dir": str(result_dir),
#|        "status_ko": "",
#|        "generated_outputs": {},
#|        "fixed_fault_reference_compare": {},
#|        "note_ko": (
#|            "live chain은 package 내부의 bootstrap verdict -> fault_event_audit -> final verdict -> gpvs evidence -> heuristic "
#|            "경로를 workspace-only로 수행한다."
#|        ),
#|    }
#|    if not support["supported"]:
#|        payload["status_ko"] = "packaged live chain assets missing"
#|        return payload
#|    if sorted(sites) != sorted(DEFAULT_SITES):
#|        payload["status_ko"] = "current live chain supports baseline tri-site universe only"
#|        return payload
#|
#|    workspace_root = stage_live_chain_workspace(output_root, sites)
#|    payload["workspace_root"] = str(workspace_root)
#|    commands = [
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_bootstrap_verdict_v1.py")), "--root", str(workspace_root), "--write-panel-verdict-alias"],
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_fault_panel_event_audit_v1.py")), "--root", str(workspace_root)],
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_panel_multiaxis_verdict_v1.py")), "--root", str(workspace_root)],
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_gpvs_evidence_pack_v1.py")), "--root", str(workspace_root)],
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_cause_candidate_heuristics_v1.py")), "--root", str(workspace_root)],
#|    ]
#|    for cmd in commands:
#|        subprocess.run(cmd, cwd=package_root(), check=True)
#|
#|    live_fault_df = build_live_fault_table(workspace_root)
#|    live_preview_df = build_live_fault_preview(workspace_root, live_fault_df)
#|    live_fault_path = result_dir / "fault_panel_result_live_v1.csv"
#|    live_preview_path = result_dir / "fault_panel_result_live_preview_v1.csv"
#|    live_fault_df.to_csv(live_fault_path, index=False, encoding="utf-8-sig")
#|    live_preview_df.to_csv(live_preview_path, index=False, encoding="utf-8-sig")
#|
#|    generated = {
#|        "bootstrap_verdict": str(workspace_root / "_share" / "panel_day_engine_bootstrap_verdict_v1.csv"),
#|        "fault_event_audit": str(workspace_root / "_share" / "panel_day_engine_fault_panel_event_audit_v1.csv"),
#|        "final_verdict": str(workspace_root / "_share" / "panel_day_engine_panel_multiaxis_verdict_v1.csv"),
#|        "gpvs_evidence": str(workspace_root / "_share" / "panel_day_engine_gpvs_evidence_pack_v1.csv"),
#|        "heuristic": str(workspace_root / "_share" / "panel_day_engine_cause_candidate_heuristics_v1.csv"),
#|        "fault_panel_result_live_v1": str(live_fault_path),
#|        "fault_panel_result_live_preview_v1": str(live_preview_path),
#|    }
#|    for name, source in [
#|        ("panel_day_engine_bootstrap_verdict_v1.csv", workspace_root / "_share" / "panel_day_engine_bootstrap_verdict_v1.csv"),
#|        ("panel_day_engine_fault_panel_event_audit_v1.csv", workspace_root / "_share" / "panel_day_engine_fault_panel_event_audit_v1.csv"),
#|        ("panel_day_engine_panel_multiaxis_verdict_v1.csv", workspace_root / "_share" / "panel_day_engine_panel_multiaxis_verdict_v1.csv"),
#|        ("panel_day_engine_gpvs_evidence_pack_v1.csv", workspace_root / "_share" / "panel_day_engine_gpvs_evidence_pack_v1.csv"),
#|        ("panel_day_engine_cause_candidate_heuristics_v1.csv", workspace_root / "_share" / "panel_day_engine_cause_candidate_heuristics_v1.csv"),
#|    ]:
#|        target = result_dir / name
#|        shutil.copy2(source, target)
#|        generated[name] = str(target)
#|
#|    compare = compare_live_fault_to_fixed(live_fault_df)
#|    compare["baseline_input_all_sites_match"] = bool(baseline_comparison.get("all_sites_match", False))
#|    payload["generated_outputs"] = generated
#|    payload["fixed_fault_reference_compare"] = compare
#|    payload["status_ko"] = "completed"
#|    summary_path = result_dir / "live_chain_summary_v1.json"
#|    write_json(summary_path, payload)
#|    payload["summary_path"] = str(summary_path)
#|    payload["published_outputs"] = publish_live_chain_outputs(output_root, result_dir, summary_path)
#|    write_json(summary_path, payload)
#|    root_summary_path = output_root / "result" / ROOT_LIVE_SUMMARY_NAME
#|    shutil.copy2(summary_path, root_summary_path)
#|    payload["published_outputs"][ROOT_LIVE_SUMMARY_NAME] = str(root_summary_path)
#|    root_report_path = output_root / "result" / ROOT_LIVE_REPORT_NAME
#|    write_text(
#|        root_report_path,
#|        build_live_report_markdown(
#|            sites=sites,
#|            baseline_comparison=baseline_comparison,
#|            compare=compare,
#|            published_outputs=payload["published_outputs"],
#|            live_preview_df=live_preview_df,
#|        ),
#|    )
#|    payload["published_outputs"][ROOT_LIVE_REPORT_NAME] = str(root_report_path)
#|    write_json(summary_path, payload)
#|    shutil.copy2(summary_path, root_summary_path)
#|    return payload
#|
#|
#|def run_raw_only_chain(output_root: Path, sites: list[str]) -> dict[str, object]:
#|    support = packaged_raw_only_chain_support()
#|    result_dir = output_root / "result" / "raw_only_chain"
#|    result_dir.mkdir(parents=True, exist_ok=True)
#|    payload: dict[str, object] = {
#|        "requested": True,
#|        "supported": bool(support["supported"]),
#|        "support": support,
#|        "workspace_root": "",
#|        "result_dir": str(result_dir),
#|        "status_ko": "",
#|        "generated_outputs": {},
#|        "fixed_fault_reference_compare": {},
#|        "note_ko": (
#|            "raw-only chain은 panel_day_core와 precursor gate만 사용해 audit -> final verdict -> heuristic를 다시 계산한다. "
#|            "커널로그_원인군_ko는 algorithm-derived family 의미로 해석해야 한다."
#|        ),
#|    }
#|    if not support["supported"]:
#|        payload["status_ko"] = "packaged raw-only chain assets missing"
#|        return payload
#|
#|    workspace_root = stage_raw_only_chain_workspace(output_root, sites)
#|    payload["workspace_root"] = str(workspace_root)
#|    commands = [
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_runtime_fault_event_audit_v1.py")), "--root", str(workspace_root)],
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_runtime_final_verdict_v1.py")), "--root", str(workspace_root)],
#|        [sys.executable, str(packaged_script_path("build_panel_day_engine_runtime_heuristic_v1.py")), "--root", str(workspace_root)],
#|    ]
#|    for cmd in commands:
#|        subprocess.run(cmd, cwd=package_root(), check=True)
#|
#|    raw_only_common = load_raw_only_common_module()
#|    raw_only_fault_df = raw_only_common.build_fault_table_from_outputs(
#|        workspace_root=workspace_root,
#|        verdict_name=raw_only_common.RUNTIME_VERDICT_OUTPUT_NAME,
#|        heuristic_name=raw_only_common.RUNTIME_HEURISTIC_OUTPUT_NAME,
#|    )
#|    raw_only_preview_df = raw_only_common.build_fault_preview(workspace_root, raw_only_fault_df)
#|    raw_only_fault_path = result_dir / "fault_panel_result_raw_only_v1.csv"
#|    raw_only_preview_path = result_dir / "fault_panel_result_raw_only_preview_v1.csv"
#|    raw_only_fault_df.to_csv(raw_only_fault_path, index=False, encoding="utf-8-sig")
#|    raw_only_preview_df.to_csv(raw_only_preview_path, index=False, encoding="utf-8-sig")
#|
#|    generated = {
#|        "runtime_audit": str(workspace_root / "_share" / raw_only_common.RUNTIME_AUDIT_OUTPUT_NAME),
#|        "runtime_verdict": str(workspace_root / "_share" / raw_only_common.RUNTIME_VERDICT_OUTPUT_NAME),
#|        "runtime_heuristic": str(workspace_root / "_share" / raw_only_common.RUNTIME_HEURISTIC_OUTPUT_NAME),
#|        "fault_panel_result_raw_only_v1": str(raw_only_fault_path),
#|        "fault_panel_result_raw_only_preview_v1": str(raw_only_preview_path),
#|    }
#|    for name, source in [
#|        (raw_only_common.RUNTIME_AUDIT_OUTPUT_NAME, workspace_root / "_share" / raw_only_common.RUNTIME_AUDIT_OUTPUT_NAME),
#|        (raw_only_common.RUNTIME_VERDICT_OUTPUT_NAME, workspace_root / "_share" / raw_only_common.RUNTIME_VERDICT_OUTPUT_NAME),
#|        (raw_only_common.RUNTIME_HEURISTIC_OUTPUT_NAME, workspace_root / "_share" / raw_only_common.RUNTIME_HEURISTIC_OUTPUT_NAME),
#|    ]:
#|        target = result_dir / name
#|        shutil.copy2(source, target)
#|        generated[name] = str(target)
#|
#|    compare = raw_only_common.compare_fault_table_to_reference(raw_only_fault_df, fixed_fault6_table_path())
#|    payload["generated_outputs"] = generated
#|    payload["fixed_fault_reference_compare"] = compare
#|    payload["status_ko"] = "completed"
#|    summary_path = result_dir / "raw_only_chain_summary_v1.json"
#|    write_json(summary_path, payload)
#|    payload["summary_path"] = str(summary_path)
#|    return payload
#|
#|
#|def build_shadow_compare_report(
#|    output_root: Path,
#|    site_plans: list[dict[str, object]],
#|    baseline_comparison: dict[str, object],
#|) -> dict[str, object]:
#|    reference = load_core_baseline_digest()
#|    report: dict[str, object] = {
#|        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
#|        "reference_path": str(baseline_core_digest_path()),
#|        "note_ko": (
#|            "이 shadow compare는 동일 baseline raw corpus로 runtime pack을 다시 실행했을 때 "
#|            "panel_day_core.csv가 reference digest와 같은지 점검한다. "
#|            "현재는 full-chain verdict/evidence/heuristic live compare가 아니라 engine core compare만 수행한다."
#|        ),
#|        "sites": {},
#|        "compared_site_count": 0,
#|        "matched_site_count": 0,
#|        "all_compared_sites_match": True,
#|    }
#|    reference_sites = reference.get("sites", {})
#|
#|    for plan in site_plans:
#|        site = str(plan["site"])
#|        site_entry: dict[str, object] = {
#|            "baseline_input_match": bool(baseline_comparison["sites"].get(site, {}).get("match", False)),
#|            "compared": False,
#|            "match": None,
#|            "skipped_reason": "",
#|            "expected": {},
#|            "actual": {},
#|            "diffs": [],
#|        }
#|        expected = reference_sites.get(site)
#|        if not expected:
#|            site_entry["skipped_reason"] = "missing_packaged_reference_digest"
#|            report["sites"][site] = site_entry
#|            continue
#|        if not site_entry["baseline_input_match"]:
#|            site_entry["skipped_reason"] = "input_manifest_mismatch"
#|            site_entry["expected"] = expected
#|            report["sites"][site] = site_entry
#|            continue
#|
#|        core_path = output_root / "sites" / site / "output" / "panel_day_core.csv"
#|        if not core_path.exists():
#|            site_entry["skipped_reason"] = "missing_generated_panel_day_core"
#|            site_entry["expected"] = expected
#|            report["sites"][site] = site_entry
#|            continue
#|
#|        actual_df = pd.read_csv(core_path, low_memory=False)
#|        actual_digest = build_core_digest_payload(actual_df, core_path.name)
#|        diffs = compare_single_site_digest(expected, actual_digest)
#|        site_entry.update(
#|            {
#|                "compared": True,
#|                "match": not diffs,
#|                "expected": expected,
#|                "actual": actual_digest,
#|                "diffs": diffs,
#|            }
#|        )
#|        report["sites"][site] = site_entry
#|        report["compared_site_count"] += 1
#|        if not diffs:
#|            report["matched_site_count"] += 1
#|        else:
#|            report["all_compared_sites_match"] = False
#|
#|    if report["compared_site_count"] == 0:
#|        report["all_compared_sites_match"] = False
#|    return report
#|
#|
#|def main() -> None:
#|    args = parse_args()
#|    if not engine_path().exists():
#|        raise SystemExit(f"missing packaged engine: {engine_path()}")
#|
#|    emit_progress(1, "실행 준비를 시작합니다.")
#|    data_root = args.data_root.expanduser().resolve()
#|    output_root = args.output_root.expanduser().resolve()
#|    output_root.mkdir(parents=True, exist_ok=True)
#|    reuse_existing_site_outs_root = (
#|        args.reuse_existing_site_outs_root.expanduser().resolve()
#|        if args.reuse_existing_site_outs_root is not None
#|        else None
#|    )
#|
#|    sites = normalize_sites(args.sites)
#|    effective_reuse_existing_site_outs_root, reuse_decision, reuse_freshness = resolve_reuse_existing_site_outs_root(
#|        data_root=data_root,
#|        explicit_reuse_root=reuse_existing_site_outs_root,
#|        prefer_existing_site_outs=args.prefer_existing_site_outs,
#|        sites=sites,
#|    )
#|    site_plans: list[dict[str, object]] = []
#|    commands: list[list[str]] = []
#|    for site in sites:
#|        plan, cmd = build_site_plan(args, site)
#|        site_plans.append(plan)
#|        commands.append(cmd)
#|
#|    emit_progress(8, "입력 CSV 구조와 실행 계획을 점검했습니다.")
#|    fixed_outputs = copy_fixed_results(output_root)
#|    baseline_comparison = compare_to_baseline(site_plans)
#|    live_chain_support = packaged_live_chain_support()
#|    raw_only_chain_support = packaged_raw_only_chain_support()
#|    live_chain_plan = {
#|        "requested": args.run_live_chain == "on",
#|        "supported": bool(live_chain_support["supported"]),
#|        "support": live_chain_support,
#|        "status_ko": "",
#|    }
#|    if not live_chain_plan["requested"]:
#|        live_chain_plan["status_ko"] = "disabled by option"
#|    elif sorted(sites) != sorted(DEFAULT_SITES):
#|        live_chain_plan["status_ko"] = "current live chain supports baseline tri-site universe only"
#|    elif not live_chain_plan["supported"]:
#|        live_chain_plan["status_ko"] = "packaged live chain assets missing"
#|    else:
#|        live_chain_plan["status_ko"] = (
#|            "will run after precomputed out reuse"
#|            if effective_reuse_existing_site_outs_root is not None
#|            else "will run after engine execution"
#|        )
#|    raw_only_chain_plan = {
#|        "requested": args.run_raw_only_chain == "on",
#|        "supported": bool(raw_only_chain_support["supported"]),
#|        "support": raw_only_chain_support,
#|        "status_ko": "",
#|    }
#|    if not raw_only_chain_plan["requested"]:
#|        raw_only_chain_plan["status_ko"] = "disabled by option"
#|    elif not raw_only_chain_plan["supported"]:
#|        raw_only_chain_plan["status_ko"] = "packaged raw-only chain assets missing"
#|    else:
#|        raw_only_chain_plan["status_ko"] = (
#|            "will run after precomputed out reuse"
#|            if effective_reuse_existing_site_outs_root is not None
#|            else "will run after engine execution"
#|        )
#|
#|    plan = {
#|        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
#|        "package_root": str(package_root()),
#|        "engine_path": str(engine_path()),
#|        "data_root": str(data_root),
#|        "output_root": str(output_root),
#|        "reuse_existing_site_outs_root": str(reuse_existing_site_outs_root) if reuse_existing_site_outs_root else "",
#|        "effective_reuse_existing_site_outs_root": (
#|            str(effective_reuse_existing_site_outs_root)
#|            if effective_reuse_existing_site_outs_root
#|            else ""
#|        ),
#|        "prefer_existing_site_outs": args.prefer_existing_site_outs,
#|        "reuse_decision_ko": reuse_decision,
#|        "reuse_freshness": reuse_freshness,
#|        "execution_mode_ko": (
#|            "auto_reuse_existing_site_outs"
#|            if effective_reuse_existing_site_outs_root is not None and reuse_decision == "auto_fresh"
#|            else "reuse_precomputed_site_outs"
#|            if effective_reuse_existing_site_outs_root is not None
#|            else "run_engine_then_live_chain"
#|        ),
#|        "sites": sites,
#|        "site_plans": site_plans,
#|        "fixed_outputs": fixed_outputs,
#|        "baseline_comparison": baseline_comparison,
#|        "live_chain": live_chain_plan,
#|        "raw_only_chain": raw_only_chain_plan,
#|        "workspace_retention": args.workspace_retention,
#|        "shadow_compare_reference_path": str(baseline_core_digest_path()),
#|        "fault6_provenance_path": optional_artifact_path_text(fault6_provenance_path()),
#|        "dependency_audit_json_path": optional_artifact_path_text(dependency_audit_json_path()),
#|        "dependency_audit_md_path": optional_artifact_path_text(dependency_audit_md_path()),
#|        "shadow_compare_report_path": str(output_root / "shadow_compare_v1.json"),
#|        "workspace_cleanup_report_path": str(output_root / "workspace_cleanup_v1.json"),
#|        "dry_run": bool(args.dry_run),
#|        "note_ko": (
#|            "이 pack은 conalog/gangui/ktc_ess baseline sites에 대해 실제 panel_day_engine.py 를 실행하고, "
#|            "현재 frozen fault 결과표도 함께 export 한다. "
#|            "fault6 결과표 provenance가 package에 포함된 경우 해당 경로도 함께 남긴다. "
#|            "추가로 baseline core output shadow compare 경로를 남겨, same baseline 입력일 때 engine core output이 유지되는지도 점검한다. "
#|            "workspace_retention=result-only를 사용하면 재생성 가능한 대용량 site/workspace data copy를 실행 후 제거한다."
#|        ),
#|    }
#|
#|    if args.dry_run:
#|        write_json(output_root / "run_plan_v1.json", plan)
#|        emit_progress(100, "dry-run 계획 파일 생성을 완료했습니다.")
#|        print(f"[OK] dry-run plan written: {output_root / 'run_plan_v1.json'}")
#|        return
#|
#|    reused_site_outs: dict[str, str] = {}
#|    if effective_reuse_existing_site_outs_root is not None:
#|        emit_progress(15, "기존 site out 산출물을 재사용합니다.")
#|        reused_site_outs = copy_existing_site_outs(effective_reuse_existing_site_outs_root, output_root, sites)
#|    else:
#|        site_count = max(1, len(commands))
#|        for idx, cmd in enumerate(commands, start=1):
#|            site_name = str(site_plans[idx - 1]["site"])
#|            start_pct = 15 + int((idx - 1) * 45 / site_count)
#|            done_pct = 15 + int(idx * 45 / site_count)
#|            emit_progress(start_pct, f"메인 엔진 실행 시작: {site_name}")
#|            subprocess.run(cmd, check=True)
#|            emit_progress(done_pct, f"메인 엔진 실행 완료: {site_name}")
#|
#|    emit_progress(65, "engine core 결과를 shadow compare 기준으로 점검합니다.")
#|    shadow_compare = build_shadow_compare_report(output_root, site_plans, baseline_comparison)
#|    write_json(output_root / "shadow_compare_v1.json", shadow_compare)
#|    live_chain_result = {"requested": False, "status_ko": "not requested"}
#|    if args.run_live_chain == "on":
#|        emit_progress(75, "live chain 결과표를 생성합니다.")
#|        live_chain_result = run_live_chain(output_root, sites, baseline_comparison)
#|    raw_only_chain_result = {"requested": False, "status_ko": "not requested"}
#|    if args.run_raw_only_chain == "on":
#|        emit_progress(88, "raw-only candidate chain 결과를 생성합니다.")
#|        raw_only_chain_result = run_raw_only_chain(output_root, sites)
#|
#|    master_report_path = output_root / "result" / ROOT_MASTER_REPORT_NAME
#|    detailed_report_path = output_root / "result" / ROOT_DETAILED_REPORT_NAME
#|    precursor_report_path = output_root / "result" / ROOT_PRECURSOR_REPORT_NAME
#|    fault_signal_report_path = output_root / "result" / ROOT_FAULT_SIGNAL_REPORT_NAME
#|    live_preview_path = output_root / "result" / ROOT_LIVE_PREVIEW_NAME
#|    live_preview_df = pd.read_csv(live_preview_path, encoding="utf-8-sig", low_memory=False) if live_preview_path.exists() else pd.DataFrame()
#|    raw_only_candidate_preview_path = output_root / "result" / "raw_only_chain" / "fault_panel_result_raw_only_preview_v1.csv"
#|    raw_only_candidate_preview_df = (
#|        pd.read_csv(raw_only_candidate_preview_path, encoding="utf-8-sig", low_memory=False)
#|        if raw_only_candidate_preview_path.exists()
#|        else pd.DataFrame()
#|    )
#|    detailed_frames = build_detailed_report_frames(
#|        output_root=output_root,
#|        sites=sites,
#|        baseline_comparison=baseline_comparison,
#|        live_chain_result=live_chain_result,
#|        raw_only_chain_result=raw_only_chain_result,
#|        live_preview_df=live_preview_df,
#|        raw_only_preview_df=raw_only_candidate_preview_df,
#|    )
#|    raw_only_current_preview_df = raw_only_candidate_preview_df.copy()
#|    if raw_only_chain_result.get("requested") and normalize_text(raw_only_chain_result.get("status_ko")) == "completed":
#|        strict_fault_df, strict_preview_df, publish_meta = build_strict_raw_only_current_outputs(
#|            raw_only_chain_result=raw_only_chain_result,
#|            evidence_df=detailed_frames["raw_only_evidence"],
#|        )
#|        raw_only_chain_result["publish_meta"] = publish_meta
#|        raw_only_chain_result["published_outputs"] = publish_raw_only_current_outputs(
#|            output_root,
#|            strict_fault_df,
#|            strict_preview_df,
#|        )
#|        root_summary_path = output_root / "result" / ROOT_RAWONLY_SUMMARY_NAME
#|        raw_only_chain_result["published_outputs"][ROOT_RAWONLY_SUMMARY_NAME] = str(root_summary_path)
#|        root_report_path = output_root / "result" / ROOT_RAWONLY_REPORT_NAME
#|        write_text(
#|            root_report_path,
#|            build_raw_only_report_markdown(
#|                sites=sites,
#|                compare=raw_only_chain_result.get("fixed_fault_reference_compare", {}),
#|                published_outputs=raw_only_chain_result["published_outputs"],
#|                live_preview_df=to_user_preview_schema(strict_preview_df),
#|                publish_meta=publish_meta,
#|            ),
#|        )
#|        raw_only_chain_result["published_outputs"][ROOT_RAWONLY_REPORT_NAME] = str(root_report_path)
#|        raw_only_current_preview_df = strict_preview_df.copy()
#|        summary_path = Path(str(raw_only_chain_result.get("summary_path", "")))
#|        if summary_path.exists():
#|            write_json(summary_path, raw_only_chain_result)
#|            shutil.copy2(summary_path, root_summary_path)
#|    live_preview_display_df = to_user_preview_schema(live_preview_df)
#|    raw_only_current_preview_display_df = to_user_preview_schema(raw_only_current_preview_df)
#|    detailed_frames["current_preview"] = nonempty_sheet_df(
#|        live_preview_display_df.copy(),
#|        "live current preview not available",
#|    )
#|    detailed_frames["raw_only_preview"] = nonempty_sheet_df(
#|        raw_only_current_preview_display_df.copy(),
#|        "raw-only preview not available",
#|    )
#|    precursor_report_df = detailed_frames.get(
#|        "precursor_report",
#|        pd.DataFrame(columns=PRECURSOR_REPORT_OUTPUT_COLS),
#|    )
#|    fault_signal_report_df = detailed_frames.get(
#|        "fault_signal_report",
#|        pd.DataFrame(columns=FAULT_SIGNAL_REPORT_OUTPUT_COLS),
#|    )
#|    precursor_report_df.to_csv(precursor_report_path, index=False, encoding="utf-8-sig")
#|    fault_signal_report_df.to_csv(fault_signal_report_path, index=False, encoding="utf-8-sig")
#|    write_detailed_report_xlsx(
#|        detailed_report_path,
#|        detailed_frames,
#|    )
#|    write_text(
#|        master_report_path,
#|        build_master_report_markdown(
#|            sites=sites,
#|            baseline_comparison=baseline_comparison,
#|            live_chain_result=live_chain_result,
#|            raw_only_chain_result=raw_only_chain_result,
#|            live_preview_df=live_preview_display_df,
#|            raw_only_preview_df=raw_only_current_preview_display_df,
#|            precursor_report_df=precursor_report_df,
#|            fault_signal_report_df=fault_signal_report_df,
#|            detailed_report_path=detailed_report_path,
#|            precursor_report_path=precursor_report_path,
#|            fault_signal_report_path=fault_signal_report_path,
#|        ),
#|    )
#|    if live_preview_path.exists():
#|        live_preview_display_df.to_csv(live_preview_path, index=False, encoding="utf-8-sig")
#|    raw_only_current_preview_path = output_root / "result" / ROOT_RAWONLY_PREVIEW_NAME
#|    if raw_only_current_preview_path.exists():
#|        raw_only_current_preview_display_df.to_csv(
#|            raw_only_current_preview_path,
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|
#|    workspace_cleanup = apply_workspace_retention(output_root, args.workspace_retention)
#|    workspace_cleanup_path = output_root / "workspace_cleanup_v1.json"
#|    write_json(workspace_cleanup_path, workspace_cleanup)
#|    metadata = {
#|        **plan,
#|        "dry_run": False,
#|        "reused_site_outs": reused_site_outs,
#|        "shadow_compare": shadow_compare,
#|        "live_chain": live_chain_result,
#|        "raw_only_chain": raw_only_chain_result,
#|        "workspace_cleanup": workspace_cleanup,
#|        "detailed_report_path": str(detailed_report_path),
#|        "precursor_report_path": str(precursor_report_path),
#|        "fault_signal_report_path": str(fault_signal_report_path),
#|        "master_report_path": str(master_report_path),
#|    }
#|    write_json(output_root / "run_metadata_v1.json", metadata)
#|    emit_progress(100, "실행 완료. 결과 리포트를 열 수 있습니다.")
#|    print(f"[OK] result dir: {output_root / 'result'}")
#|    print(f"[OK] shadow compare: {output_root / 'shadow_compare_v1.json'}")
#|    print(f"[OK] detailed report: {detailed_report_path}")
#|    print(f"[OK] precursor report: {precursor_report_path}")
#|    print(f"[OK] raw-only fault signal report: {fault_signal_report_path}")
#|    print(f"[OK] master report: {master_report_path}")
#|    print(f"[OK] workspace cleanup: {workspace_cleanup_path}")
#|    if live_chain_result.get("requested"):
#|        print(f"[OK] live chain status: {live_chain_result.get('status_ko')}")
#|    if raw_only_chain_result.get("requested"):
#|        print(f"[OK] raw-only chain status: {raw_only_chain_result.get('status_ko')}")
#|    if args.workspace_retention == "full":
#|        for site in sites:
#|            print(f"[OK] site output: {output_root / 'sites' / site / 'output' / 'panel_day_core.csv'}")
#|    else:
#|        removed_bytes = int(workspace_cleanup.get("bytes_removed_estimate", 0))
#|        print(f"[OK] workspace retention: result-only removed approximately {removed_bytes} bytes")
#|
#|
#|if __name__ == "__main__":
#|    main()
# pvdiag_payload_end
# endregion
# -----------------------------------------------------------------------------
# region payload: frozen_fault_reference
# pvdiag_payload_file {"bytes": 1341, "endswith_newline": true, "lines": 7, "path": "release/conalog_full_runtime_v1/package/artifacts/fault6_fixed_result_table_v1.csv", "role": "frozen_fault_reference", "sha256": "93eb336dfdbba36159e802726e9e94d98f782b74ef2e62b5cea46f4a22f93581"}
#|﻿site,panel_id,패널고장여부_ko,사건유형_ko,최종고장양상_ko,커널로그_원인군_ko,1순위_의심원인_ko,2순위_의심원인_ko,3순위_의심원인_ko
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,고장,전조형 고장,진행성 악화,다이오드형,다이오드·서브스트링 이상형,부분음영형,열화형
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,고장,전조형 고장,급격 종료,개방/장치이상형,센서·계측 피드백 이상형,접속 불량·부분 개방형,제어 응답 이상형
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,고장,급작 고장,급작 발생,다이오드형,다이오드·서브스트링 이상형,센서·계측 피드백 이상형,접속 불량·부분 개방형
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,고장,급작 고장,급작 발생,다이오드형,다이오드·서브스트링 이상형,센서·계측 피드백 이상형,접속 불량·부분 개방형
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,고장,급작 고장,급작 발생,다이오드형,다이오드·서브스트링 이상형,부분음영형,접속 불량·부분 개방형
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,고장,전조형 고장,진행성 악화,모듈손상형,열화형,센서·계측 피드백 이상형,다이오드·서브스트링 이상형
# pvdiag_payload_end
# endregion
# -----------------------------------------------------------------------------
# region payload: required_result_preview
# pvdiag_payload_file {"bytes": 1125, "endswith_newline": true, "lines": 7, "path": "release/conalog_full_runtime_v1/package/artifacts/fault6_label_and_algorithm_preview_v1.csv", "role": "required_result_preview", "sha256": "58e321a5bfcd7bf62e398aecde38701a533c5a64cbef2d18935b57bc4a39e20a"}
#|﻿site,panel_id,전조날짜,고장 기준일,운영 판정,급락 종결 관측,점진 저하 누적,사건 종결 요약,상위 해석 후보,기존 알고리즘 source
#|conalog,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0,2024-11-06,2024-11-26,확정,없음,있음,전조 후 진행 악화,다이오드·서브스트링 이상형,panel-bypass
#|conalog,c42997a6-5881-47e7-9035-7de8a2673b54.1.1,2025-01-20,2025-03-21,확정,있음,있음,전조 후 급격 종료,센서·계측 피드백 이상형,disconnection
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7,전조없음,2025-06-08,확정,있음,없음,급작 발생,다이오드·서브스트링 이상형,panel-bypass
#|gangui,bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16,전조없음,2025-06-08,확정,있음,없음,급작 발생,다이오드·서브스트링 이상형,panel-bypass
#|ktc_ess,10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12,전조없음,2025-08-16,확정,있음,없음,급작 발생,다이오드·서브스트링 이상형,미검출
#|ktc_ess,70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4,2025-01-25,2025-02-02,확정,없음,있음,전조 후 진행 악화,열화형,미검출
# pvdiag_payload_end
# endregion
# -----------------------------------------------------------------------------
# region payload: baseline_fingerprint
# pvdiag_payload_file {"bytes": 2236, "endswith_newline": false, "lines": 65, "path": "release/conalog_full_runtime_v1/package/artifacts/input_baseline_manifest_v1.json", "role": "baseline_fingerprint", "sha256": "8f6e69e526de55fb976e0fd9ecb5c1304816c3d3d48a7f8ef758989d6914ee2c"}
#|{
#|  "sites": {
#|    "conalog": {
#|      "file_count": 536,
#|      "total_bytes": 3831367301,
#|      "first_filenames": [
#|        "2024-09-06-커널로그1호-5m.csv",
#|        "2024-09-07-커널로그1호-5m.csv",
#|        "2024-09-08-커널로그1호-5m.csv",
#|        "2024-09-09-커널로그1호-5m.csv",
#|        "2024-09-10-커널로그1호-5m.csv"
#|      ],
#|      "last_filenames": [
#|        "ae_simple_ews_warnings.csv",
#|        "ae_simple_fault_candidates.csv",
#|        "ae_simple_panel_alarms.csv",
#|        "ae_simple_prefault_B_daily.csv",
#|        "ae_simple_scores.csv"
#|      ],
#|      "min_date": "2024-09-06",
#|      "max_date": "2026-02-18"
#|    },
#|    "gangui": {
#|      "file_count": 325,
#|      "total_bytes": 1551009589,
#|      "first_filenames": [
#|        "2025-04-08-극동대학교 강의동-5m.csv",
#|        "2025-04-09-극동대학교 강의동-5m.csv",
#|        "2025-04-10-극동대학교 강의동-5m.csv",
#|        "2025-04-11-극동대학교 강의동-5m.csv",
#|        "2025-04-12-극동대학교 강의동-5m.csv"
#|      ],
#|      "last_filenames": [
#|        "ae_simple_ews_warnings.csv",
#|        "ae_simple_fault_candidates.csv",
#|        "ae_simple_panel_alarms.csv",
#|        "ae_simple_prefault_B_daily.csv",
#|        "ae_simple_scores.csv"
#|      ],
#|      "min_date": "2025-04-08",
#|      "max_date": "2026-02-19"
#|    },
#|    "ktc_ess": {
#|      "file_count": 541,
#|      "total_bytes": 2101249399,
#|      "first_filenames": [
#|        "2024-08-13-KTC ESS시험동 옥상-5m.csv",
#|        "2024-08-14-KTC ESS시험동 옥상-5m.csv",
#|        "2024-08-15-KTC ESS시험동 옥상-5m.csv",
#|        "2024-08-16-KTC ESS시험동 옥상-5m.csv",
#|        "2024-08-17-KTC ESS시험동 옥상-5m.csv"
#|      ],
#|      "last_filenames": [
#|        "ae_simple_ews_warnings.csv",
#|        "ae_simple_fault_candidates.csv",
#|        "ae_simple_panel_alarms.csv",
#|        "ae_simple_prefault_B_daily.csv",
#|        "ae_simple_scores.csv"
#|      ],
#|      "min_date": "2024-08-13",
#|      "max_date": "2026-02-19"
#|    }
#|  },
#|  "note_ko": "이 manifest는 고정 fault6 결과표가 만들어진 현재 baseline raw corpus의 경량 fingerprint다. target 환경에서 파일 수/총용량/날짜 범위를 비교해 exact replay 여부를 점검한다."
#|}
# pvdiag_payload_end
# endregion
# -----------------------------------------------------------------------------
# region payload: shadow_compare_reference
# pvdiag_payload_file {"bytes": 2864, "endswith_newline": false, "lines": 99, "path": "release/conalog_full_runtime_v1/package/artifacts/panel_day_core_baseline_digest_v1.json", "role": "shadow_compare_reference", "sha256": "15b339b68502e6e1d930987d35e3e67f0a6a5c7a308c3a37a4e8190e10f8b250"}
#|{
#|  "generated_at_utc": "2026-04-28T13:46:50Z",
#|  "sites": {
#|    "conalog": {
#|      "columns": [
#|        "date",
#|        "panel_id",
#|        "confirmed_fault",
#|        "critical_fault",
#|        "critical_source",
#|        "final_fault",
#|        "anom_level",
#|        "anom_subtype"
#|      ],
#|      "row_count": 155723,
#|      "digest_sha256": "f8a5640a480d098bf791f21936345ff5c990470be27418be02eec9a00cbb9309",
#|      "critical_source_counts": {
#|        "legacy": 69,
#|        "none": 155323,
#|        "vdrop": 295,
#|        "vdrop_suspect": 36
#|      },
#|      "anom_level_counts": {
#|        "confirmed_fault": 504,
#|        "degraded_or_shadow": 58,
#|        "fault_like": 46,
#|        "normal": 155096,
#|        "shadow_like": 19
#|      },
#|      "confirmed_fault_true_count": 428,
#|      "critical_fault_true_count": 76,
#|      "final_fault_true_count": 504,
#|      "source_path": "data/conalog/out/panel_day_core.csv"
#|    },
#|    "gangui": {
#|      "columns": [
#|        "date",
#|        "panel_id",
#|        "confirmed_fault",
#|        "critical_fault",
#|        "critical_source",
#|        "final_fault",
#|        "anom_level",
#|        "anom_subtype"
#|      ],
#|      "row_count": 57608,
#|      "digest_sha256": "fb0837562dc01943a6bf3aa22b9467635f4cd50bef276954b05ac213eac4123d",
#|      "critical_source_counts": {
#|        "legacy": 393,
#|        "none": 56528,
#|        "vdrop": 664,
#|        "vdrop_suspect": 23
#|      },
#|      "anom_level_counts": {
#|        "confirmed_fault": 664,
#|        "degraded_or_shadow": 74,
#|        "fault_like": 65,
#|        "group_off_like": 91,
#|        "normal": 56710,
#|        "shadow_like": 4
#|      },
#|      "confirmed_fault_true_count": 255,
#|      "critical_fault_true_count": 616,
#|      "final_fault_true_count": 664,
#|      "source_path": "data/gangui/out/panel_day_core.csv"
#|    },
#|    "ktc_ess": {
#|      "columns": [
#|        "date",
#|        "panel_id",
#|        "confirmed_fault",
#|        "critical_fault",
#|        "critical_source",
#|        "final_fault",
#|        "anom_level",
#|        "anom_subtype"
#|      ],
#|      "row_count": 86688,
#|      "digest_sha256": "e7e3a6a335122ad36f820984953086dd35b4bbfb2d113bef96fa996a756acab5",
#|      "critical_source_counts": {
#|        "legacy": 2,
#|        "none": 86379,
#|        "vdrop": 307
#|      },
#|      "anom_level_counts": {
#|        "confirmed_fault": 122,
#|        "degraded_or_shadow": 231,
#|        "fault_like": 31,
#|        "normal": 86297,
#|        "shadow_like": 7
#|      },
#|      "confirmed_fault_true_count": 0,
#|      "critical_fault_true_count": 191,
#|      "final_fault_true_count": 122,
#|      "source_path": "data/ktc_ess/out/panel_day_core.csv"
#|    }
#|  },
#|  "note_ko": "이 digest는 baseline raw corpus에서 이미 산출된 panel_day_core.csv의 정규화 hash/reference다. runtime pack이 동일 baseline 입력으로 재실행될 때 engine core output이 같은지 shadow compare할 때 사용한다."
#|}
# pvdiag_payload_end
# endregion
# -----------------------------------------------------------------------------
# region payload: core_engine
# pvdiag_payload_file {"bytes": 136596, "endswith_newline": true, "lines": 3278, "path": "release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py", "role": "core_engine", "sha256": "2cf3ae3f93bc23a5b1e1eeb19418f5ef9a2e12e84f9a583bd0fdaf636ecafbb3"}
#|# ====== panel_day_engine.py: AE + 최소 룰 기반 버전 ======
#|import argparse
#|import json
#|import pathlib
#|import re
#|from typing import Dict, Any, Tuple, List
#|
#|import numpy as np
#|import pandas as pd
#|import torch
#|import torch.nn as nn
#|import torch.optim as optim
#|from tqdm import tqdm
#|
#|
#|# ========= 유틸 =========
#|
#|# ======== Filename date helper (SSOT) ========
#|_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
#|
#|def extract_date_from_filename(fname: str) -> pd.Timestamp:
#|    """Extract first YYYY-MM-DD from filename and return normalized Timestamp.
#|    Returns pd.NaT when not found / parse fails.
#|    """
#|    m = _DATE_RE.search(str(fname))
#|    if not m:
#|        return pd.NaT
#|    return pd.to_datetime(m.group(1), errors="coerce").normalize()
#|
#|
#|def find_col(df: pd.DataFrame, *names: str) -> str:
#|    """CSV 컬럼 이름이 조금씩 달라도 비슷한 걸 찾아주는 헬퍼."""
#|    low = {c.lower(): c for c in df.columns}
#|    for n in names:
#|        if n.lower() in low:
#|            return low[n.lower()]
#|    base = names[0].lower().replace(" ", "").replace("_", "")
#|    for c in df.columns:
#|        if base in c.lower().replace(" ", "").replace("_", ""):
#|            return c
#|    raise KeyError(f"column not found: {names}")
#|
#|
#|def to_fixed_length(ts: pd.Series, target_len: int = 96) -> np.ndarray:
#|    """1일 시계열을 0~1 구간에서 선형보간 → 길이 target_len 벡터."""
#|    if len(ts) == 0:
#|        return np.zeros(target_len, dtype=float)
#|    x = np.linspace(0, 1, num=len(ts))
#|    y = ts.values.astype(float)
#|    xi = np.linspace(0, 1, num=target_len)
#|    yi = np.interp(xi, x, y)
#|    yi = np.nan_to_num(yi, nan=0.0, posinf=0.0, neginf=0.0)
#|    return yi
#|
#|
#|def estimate_interval_minutes(dt_index: pd.DatetimeIndex) -> float:
#|    """Robustly estimate sampling interval (minutes) from timestamp diffs.
#|
#|    - Uses median of positive diffs (seconds) to avoid outliers.
#|    - Fallback to 5.0 when estimation fails.
#|    """
#|    try:
#|        if dt_index is None or len(dt_index) < 3:
#|            return 5.0
#|        diffs = dt_index.to_series().diff().dt.total_seconds().to_numpy()
#|        diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
#|        if len(diffs) == 0:
#|            return 5.0
#|        med_sec = float(np.median(diffs))
#|        if not np.isfinite(med_sec) or med_sec <= 0:
#|            return 5.0
#|        return med_sec / 60.0
#|    except Exception:
#|        return 5.0
#|
#|
#|# ==== nanmean_or: np.nanmean with empty-slice guard ====
#|def nanmean_or(arr: np.ndarray | list, default: float = np.nan) -> float:
#|    """np.nanmean with an explicit empty-slice guard.
#|
#|    Returns `default` when there are no finite values.
#|    """
#|    a = np.asarray(arr, dtype=float)
#|    a = a[np.isfinite(a)]
#|    if a.size == 0:
#|        return float(default)
#|    return float(np.mean(a))
#|
#|
#|# ======== Panel group key helper ========
#|def panel_group_key(pid: str) -> str:
#|    """Best-effort grouping key from panel_id.
#|
#|    Many of our panel_id values look like:
#|      <uuid>.<string>.<panel>
#|    For peer baselines, we should compare within the same <uuid>.<string> group to
#|    avoid false V-drop signals caused by different string designs/MPPT voltages.
#|
#|    If the format is not like that, fall back to the first token.
#|    """
#|    s = str(pid)
#|    parts = s.split(".")
#|    if len(parts) >= 3:
#|        return parts[0] + "." + parts[1]
#|    if len(parts) == 2:
#|        return parts[0]
#|    return s
#|
#|
#|def _normalize_name_key(text: Any) -> str:
#|    s = str(text).strip().lower()
#|    s = re.sub(r"\d+", "", s)
#|    s = re.sub(r"[^a-z0-9]+", "", s)
#|    return s
#|
#|
#|def _panel_name_key_for_pmax(panel_id: Any) -> str:
#|    token = str(panel_id).split(".")[-1]
#|    k = _normalize_name_key(token)
#|    if k:
#|        return k
#|    return _normalize_name_key(panel_id)
#|
#|
#|def _resolve_col_by_normalized_key(df: pd.DataFrame, candidates: List[str]) -> str:
#|    cols = { _normalize_name_key(c): c for c in df.columns }
#|    for cand in candidates:
#|        k = _normalize_name_key(cand)
#|        if k in cols:
#|            return cols[k]
#|    for ck, c in cols.items():
#|        for cand in candidates:
#|            if _normalize_name_key(cand) in ck:
#|                return c
#|    raise KeyError(f"required column not found. candidates={candidates}, columns={list(df.columns)}")
#|
#|
#|def _parse_numeric_series(s: pd.Series) -> pd.Series:
#|    return pd.to_numeric(
#|        s.astype(str).str.replace(",", ".", regex=False).str.extract(r"([-+]?\d*\.?\d+)")[0],
#|        errors="coerce",
#|    )
#|
#|
#|def _load_pmax_name_map(pmax_info_csv: str) -> Dict[str, float]:
#|    p = pathlib.Path(pmax_info_csv).expanduser().resolve()
#|    if not p.exists():
#|        raise RuntimeError(f"--pmax-info-csv not found: {p}")
#|    try:
#|        info = pd.read_csv(p, sep=";", encoding="utf-8-sig")
#|    except Exception:
#|        info = pd.read_csv(p, sep=";")
#|
#|    c_name = _resolve_col_by_normalized_key(info, ["Name"])
#|    c_pmax = _resolve_col_by_normalized_key(
#|        info,
#|        [
#|            "PV MODULE Maximum Power STC(Pmax)",
#|            "Maximum Power STC(Pmax)",
#|            "Pmax",
#|        ],
#|    )
#|
#|    work = pd.DataFrame(
#|        {
#|            "name_key": info[c_name].map(_normalize_name_key),
#|            "pmax": _parse_numeric_series(info[c_pmax]),
#|        }
#|    )
#|    work = work[work["name_key"].astype(str).str.len() > 0].copy()
#|    work = work[np.isfinite(work["pmax"]) & (work["pmax"] > 0)].copy()
#|    if work.empty:
#|        raise RuntimeError(f"no valid Pmax rows found in {p}")
#|
#|    # Duplicate key guard: conflicting Pmax values for same normalized name are ambiguous.
#|    dup = (
#|        work.groupby("name_key")["pmax"]
#|        .agg(lambda s: int(pd.Series(np.round(s.to_numpy(dtype=float), 6)).nunique()))
#|        .reset_index(name="nuniq")
#|    )
#|    bad_dup = dup[dup["nuniq"] > 1]
#|    if not bad_dup.empty:
#|        keys = bad_dup["name_key"].astype(str).tolist()
#|        raise RuntimeError(f"conflicting Pmax values for normalized Name keys: {keys}")
#|
#|    return work.groupby("name_key", sort=False)["pmax"].first().astype(float).to_dict()
#|
#|
#|def _collect_panel_ids_from_files(files: List[pathlib.Path]) -> List[str]:
#|    panel_ids: set[str] = set()
#|    for fp in files:
#|        try:
#|            try:
#|                df = pd.read_csv(fp, encoding="utf-8-sig")
#|            except Exception:
#|                df = pd.read_csv(fp)
#|            c_id = find_col(df, "map_id", "panel_id", "id")
#|            panel_ids.update(df[c_id].dropna().astype(str).unique().tolist())
#|        except Exception as e:
#|            raise RuntimeError(f"failed to collect panel_id from {fp}: {e}")
#|    return sorted(panel_ids)
#|
#|
#|def _build_panel_pmax_map_for_panels(pmax_info_csv: str, panel_ids: List[str]) -> Dict[str, float]:
#|    name_map = _load_pmax_name_map(pmax_info_csv)
#|    panel_map: Dict[str, float] = {}
#|    missing: list[tuple[str, str]] = []
#|    for pid in panel_ids:
#|        k = _panel_name_key_for_pmax(pid)
#|        if k not in name_map:
#|            missing.append((str(pid), k))
#|            continue
#|        panel_map[str(pid)] = float(name_map[k])
#|    if missing:
#|        msg_lines = ["Pmax mapping failed for panel_ids (panel_id -> normalized_key):"]
#|        msg_lines.extend([f"- {pid} -> {k}" for pid, k in missing])
#|        raise RuntimeError("\n".join(msg_lines))
#|    return panel_map
#|
#|
#|def _resolve_panel_column(columns: List[Any], panel_id: str) -> Any | None:
#|    target = str(panel_id)
#|    for c in columns:
#|        if str(c) == target:
#|            return c
#|    return None
#|
#|
#|def _build_peer_series(
#|    p_tbl: pd.DataFrame,
#|    group_cols: Dict[str, List[Any]],
#|    mode: str = "median",
#|    quantile: float = 0.80,
#|    ref_panel: str = "",
#|) -> Dict[str, pd.Series]:
#|    peer_by_group: Dict[str, pd.Series] = {}
#|    mode_s = str(mode).strip().lower()
#|    q = float(quantile)
#|    if not np.isfinite(q):
#|        q = 0.80
#|    q = min(1.0, max(0.0, q))
#|
#|    ref_col = _resolve_panel_column(list(p_tbl.columns), str(ref_panel)) if ref_panel else None
#|    ref_series = p_tbl[ref_col].astype(float) if ref_col is not None else pd.Series(np.nan, index=p_tbl.index)
#|
#|    for gk, gcols in group_cols.items():
#|        sub = p_tbl[gcols]
#|        if mode_s == "median":
#|            peer_by_group[gk] = sub.median(axis=1)
#|            continue
#|        q_series = sub.quantile(q, axis=1, interpolation="linear")
#|        if mode_s == "quantile":
#|            peer_by_group[gk] = q_series
#|            continue
#|        if mode_s == "ref":
#|            # Ref panel missing at timestamp -> quantile fallback.
#|            s = ref_series.reindex(sub.index)
#|            peer_by_group[gk] = s.where(s.notna(), q_series)
#|            continue
#|        raise RuntimeError(f"unsupported peer-mode: {mode}")
#|    return peer_by_group
#|
#|
#|def compute_run_streak(panel_ids, flags) -> list[int]:
#|    """Compute consecutive true-run length per panel in row order."""
#|    streaks: list[int] = []
#|    current_panel = None
#|    cnt = 0
#|    for pid, flag in zip(panel_ids, flags):
#|        if pid != current_panel:
#|            current_panel = pid
#|            cnt = 0
#|        if flag:
#|            cnt += 1
#|        else:
#|            cnt = 0
#|        streaks.append(cnt)
#|    return streaks
#|
#|
#|def _safe_report_write(df: pd.DataFrame, path: pathlib.Path, label: str, **kwargs) -> bool:
#|    """Best-effort CSV writer for report outputs."""
#|    try:
#|        df.to_csv(path, **kwargs)
#|        return True
#|    except Exception as e:
#|        print(f"[WARN] failed to write {label}: {e}")
#|        return False
#|
#|
#|_EV_DEFAULTS: dict[str, Any] = {
#|    "drop_time": "",
#|    "sustain_mins": 0,
#|    "recovered": False,
#|    "last_ratio": np.nan,
#|    "last_peer": np.nan,
#|    "mid_ratio": np.nan,
#|    "mid_peer": np.nan,
#|    "mid_v_ratio": np.nan,
#|    "mid_i_ratio": np.nan,
#|    "coverage": np.nan,
#|    "co_drop_frac": np.nan,
#|    "recovered_any": False,
#|    "recovered_sustained": False,
#|    "re_drop": False,
#|    "coverage_mid": np.nan,
#|    "seg_count": 0,
#|    "total_low_mins": 0,
#|    "min_ratio": np.nan,
#|    "p10_ratio": np.nan,
#|    "p50_ratio": np.nan,
#|    "low_area": np.nan,
#|}
#|
#|
#|def _extract_event_values(ev: dict[str, Any]) -> dict[str, Any]:
#|    vals: dict[str, Any] = {}
#|    for key, default in _EV_DEFAULTS.items():
#|        raw = ev.get(key, default)
#|        if isinstance(default, bool):
#|            vals[key] = bool(raw)
#|        elif isinstance(default, int):
#|            vals[key] = int(raw)
#|        elif isinstance(default, float):
#|            vals[key] = float(raw)
#|        else:
#|            vals[key] = raw
#|    return vals
#|
#|# ======== 1D k-means (k=2) and train-only vbin builder ========
#|
#|def kmeans_1d_2(x: np.ndarray, iters: int = 20) -> tuple[float, float, float]:
#|    """Simple 1D k-means for k=2 without sklearn.
#|
#|    Returns (c0, c1, split) where split is midpoint between centroids.
#|    Assumes x is finite and len(x) >= 2.
#|    """
#|    x = np.asarray(x, dtype=float)
#|    x = x[np.isfinite(x)]
#|    if len(x) < 2:
#|        m = float(np.nanmedian(x)) if len(x) else 0.0
#|        return m, m, m
#|
#|    # init: 25th and 75th percentiles
#|    c0 = float(np.quantile(x, 0.25))
#|    c1 = float(np.quantile(x, 0.75))
#|    if not np.isfinite(c0):
#|        c0 = float(np.nanmin(x))
#|    if not np.isfinite(c1):
#|        c1 = float(np.nanmax(x))
#|    if c0 == c1:
#|        c1 = c0 + 1e-6
#|
#|    for _ in range(int(iters)):
#|        d0 = np.abs(x - c0)
#|        d1 = np.abs(x - c1)
#|        m0 = x[d0 <= d1]
#|        m1 = x[d0 > d1]
#|        if len(m0) > 0:
#|            c0_new = float(np.mean(m0))
#|        else:
#|            c0_new = c0
#|        if len(m1) > 0:
#|            c1_new = float(np.mean(m1))
#|        else:
#|            c1_new = c1
#|        # convergence
#|        if abs(c0_new - c0) < 1e-6 and abs(c1_new - c1) < 1e-6:
#|            c0, c1 = c0_new, c1_new
#|            break
#|        c0, c1 = c0_new, c1_new
#|
#|    # order centroids
#|    if c0 > c1:
#|        c0, c1 = c1, c0
#|    split = 0.5 * (c0 + c1)
#|    return float(c0), float(c1), float(split)
#|
#|
#|def build_vbin_map_from_train(
#|    train_files: list[pathlib.Path],
#|    critical_peer_min: float,
#|    mid_peer_alive_thr: float,
#|    mid_ratio_dead_thr: float,
#|    coverage_min: float,
#|    panel_pmax_map: Dict[str, float] | None = None,
#|    peer_mode: str = "median",
#|    peer_quantile: float = 0.80,
#|    peer_ref_panel: str = "",
#|) -> tuple[dict[str, int], dict[str, any]]:
#|    """Build a stable per-panel voltage-bin map from TRAIN period only.
#|
#|    Purpose:
#|    - Some group_key contain mixed string designs / MPPT voltages.
#|    - v_ref_span becomes large and v_ref_ok blocks v_drop.
#|    - We split group_key into sub-groups (vbin=0/1) based on panel-level typical mid_v_ratio.
#|
#|    Rules:
#|    - Use TRAIN files only (no leakage).
#|    - Exclude data_bad and dead-like rows when estimating panel typical mid_v_ratio.
#|    - Assign vbin per base group_key using 1D k-means (k=2) on panel medians.
#|    - If group is unimodal (small separation), do not split.
#|
#|    Returns:
#|      vbin_map: panel_id(str) -> 0 or 1
#|      diag: diagnostics dict for logging
#|    """
#|    # Collect mid_v_ratio observations for each panel across train days
#|    # NOTE (Gangui finding): `mid_peer` can be consistently around ~0.4 on clear days
#|    # depending on daylight/mid-window definition. If we gate too hard (e.g., 0.5),
#|    # vbin training observations become empty and vbin_map degenerates to n=0.
#|    # We therefore use a slightly more permissive peer gate ONLY for building vbin_map.
#|    vbin_peer_min = min(float(mid_peer_alive_thr), 0.35)
#|    obs: dict[str, list[float]] = {}
#|    obs_gk: dict[str, str] = {}
#|
#|    for p in train_files:
#|        try:
#|            ev_map = compute_event_features(
#|                p,
#|                panel_pmax_map=panel_pmax_map,
#|                peer_mode=peer_mode,
#|                peer_quantile=peer_quantile,
#|                peer_ref_panel=peer_ref_panel,
#|            )
#|        except Exception:
#|            continue
#|        for pid, ev in ev_map.items():
#|            pid_s = str(pid)
#|            mv = ev.get("mid_v_ratio", np.nan)
#|            mp = ev.get("mid_peer", np.nan)
#|            mr = ev.get("mid_ratio", np.nan)
#|            cov = ev.get("coverage_mid", ev.get("coverage", np.nan))
#|
#|            # train-time quality gates
#|            if not np.isfinite(mv) or not np.isfinite(mp) or not np.isfinite(mr):
#|                continue
#|            if float(mp) < float(vbin_peer_min):
#|                continue
#|            if float(cov) < float(coverage_min):
#|                continue
#|            # exclude dead-like
#|            if float(mr) <= float(mid_ratio_dead_thr):
#|                continue
#|
#|            gk = panel_group_key(pid_s)
#|            obs.setdefault(pid_s, []).append(float(mv))
#|            obs_gk[pid_s] = gk
#|
#|    # Panel-level typical mid_v_ratio (median)
#|    panel_med: dict[str, float] = {}
#|    for pid_s, lst in obs.items():
#|        arr = np.asarray(lst, dtype=float)
#|        arr = arr[np.isfinite(arr)]
#|        if len(arr) == 0:
#|            continue
#|        panel_med[pid_s] = float(np.median(arr))
#|
#|    # Group panels by base group_key
#|    by_gk: dict[str, list[tuple[str, float]]] = {}
#|    for pid_s, mv_med in panel_med.items():
#|        gk = obs_gk.get(pid_s) or panel_group_key(pid_s)
#|        by_gk.setdefault(gk, []).append((pid_s, float(mv_med)))
#|
#|    vbin_map: dict[str, int] = {}
#|    diag: dict[str, any] = {
#|        "groups_total": int(len(by_gk)),
#|        "groups_split": 0,
#|        "groups_unsplit": 0,
#|        "panels_assigned": 0,
#|        "rule": "train-only panel_median mid_v_ratio; kmeans1d k=2; split only if separation is meaningful",
#|        "groups": {},
#|    }
#|
#|    # Heuristic thresholds
#|    # - We normally require >=2 panels per bin to avoid unstable references.
#|    # - However, for small groups (n=3~5) with *very* strong separation, we allow 1 panel in the smaller bin.
#|    #   This is specifically to avoid permanent legacy fallback when a group_key has only 3~5 panels.
#|    min_panels_to_split = 4
#|    min_sep = 0.18        # typical separation threshold
#|    min_sep_strong = 0.30 # strong separation threshold (allow split even when group is small)
#|    min_bin_size = 2      # normal requirement
#|    min_bin_size_small = 1  # allowed only when sep is strong and group is small
#|
#|    for gk, pairs in by_gk.items():
#|        pairs = [(pid_s, mv) for (pid_s, mv) in pairs if np.isfinite(mv)]
#|        if len(pairs) < 2:
#|            for pid_s, _mv in pairs:
#|                vbin_map[pid_s] = 0
#|            diag["groups"][gk] = {"n": len(pairs), "split": False, "reason": "too_few_panels"}
#|            diag["groups_unsplit"] += 1
#|            continue
#|
#|        xs = np.asarray([mv for (_pid_s, mv) in pairs], dtype=float)
#|        xs = xs[np.isfinite(xs)]
#|        if len(xs) < 2:
#|            for pid_s, _mv in pairs:
#|                vbin_map[pid_s] = 0
#|            diag["groups"][gk] = {"n": len(pairs), "split": False, "reason": "no_finite"}
#|            diag["groups_unsplit"] += 1
#|            continue
#|
#|        c0, c1, split = kmeans_1d_2(xs)
#|        sep = float(abs(c1 - c0))
#|
#|        # Split decision:
#|        # - Normal case: enough panels AND meaningful separation
#|        # - Strong-sep case: even if group is small, split when sep is very large
#|        do_split = (
#|            ((len(pairs) >= int(min_panels_to_split)) and (sep >= float(min_sep)))
#|            or ((sep >= float(min_sep_strong)) and (len(pairs) >= 3))
#|        )
#|
#|        if not do_split:
#|            for pid_s, _mv in pairs:
#|                vbin_map[pid_s] = 0
#|            diag["groups"][gk] = {
#|                "n": len(pairs),
#|                "split": False,
#|                "reason": "unimodal_or_small",
#|                "c0": c0,
#|                "c1": c1,
#|                "sep": sep,
#|                "split_at": split,
#|            }
#|            diag["groups_unsplit"] += 1
#|            continue
#|
#|        # Bin-size safety:
#|        # - default: require >=2 panels per bin
#|        # - small group + strong separation: allow 1 panel in the smaller bin
#|        b0 = int(sum(1 for (_pid_s, mv) in pairs if float(mv) <= float(split)))
#|        b1 = int(sum(1 for (_pid_s, mv) in pairs if float(mv) > float(split)))
#|
#|        eff_min_bin = int(min_bin_size)
#|        if (len(pairs) <= 5) and (sep >= float(min_sep_strong)):
#|            eff_min_bin = int(min_bin_size_small)
#|
#|        if (b0 < eff_min_bin) or (b1 < eff_min_bin):
#|            for pid_s, _mv in pairs:
#|                vbin_map[pid_s] = 0
#|            diag["groups"][gk] = {
#|                "n": len(pairs),
#|                "split": False,
#|                "reason": "tiny_bin",
#|                "c0": c0,
#|                "c1": c1,
#|                "sep": sep,
#|                "split_at": split,
#|                "bin0": b0,
#|                "bin1": b1,
#|                "eff_min_bin": eff_min_bin,
#|            }
#|            diag["groups_unsplit"] += 1
#|            continue
#|
#|        # Assign bins by split point
#|        for pid_s, mv in pairs:
#|            vbin_map[pid_s] = 0 if float(mv) <= float(split) else 1
#|
#|        diag["groups"][gk] = {
#|            "n": len(pairs),
#|            "split": True,
#|            "c0": c0,
#|            "c1": c1,
#|            "sep": sep,
#|            "split_at": split,
#|            "bin0": int(sum(1 for (_pid_s, mv) in pairs if float(mv) <= float(split))),
#|            "bin1": int(sum(1 for (_pid_s, mv) in pairs if float(mv) > float(split))),
#|        }
#|        diag["groups_split"] += 1
#|
#|    diag["panels_assigned"] = int(len(vbin_map))
#|    return vbin_map, diag
#|
#|
#|def mark_run_segments(
#|    df: pd.DataFrame,
#|    key_col: str,
#|    date_col: str,
#|    cond_col: str,
#|    min_len: int,
#|    out_col: str,
#|) -> pd.DataFrame:
#|    """Mark whole consecutive-true segments when run length >= min_len."""
#|    df[out_col] = False
#|    if min_len <= 1:
#|        df[out_col] = df[cond_col].fillna(False).astype(bool)
#|        return df
#|
#|    df = df.sort_values([key_col, date_col]).copy()
#|    for pid, g in df.groupby(key_col, sort=False):
#|        idxs = g.index.to_list()
#|        flags = g[cond_col].fillna(False).astype(bool).to_list()
#|
#|        start = None
#|        run_len = 0
#|        for k, flag in enumerate(flags + [False]):  # sentinel
#|            if flag:
#|                if start is None:
#|                    start = k
#|                    run_len = 1
#|                else:
#|                    run_len += 1
#|            else:
#|                if start is not None and run_len >= int(min_len):
#|                    seg_idxs = idxs[start : start + run_len]
#|                    df.loc[seg_idxs, out_col] = True
#|                start = None
#|                run_len = 0
#|    return df
#|
#|
#|def compute_vdrop_labels(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
#|    """Single SSOT for critical-like labels.
#|
#|    Output columns (defined exactly once here):
#|      - critical_like_raw / critical_like_suspect_raw
#|      - critical_like_eff / critical_like / critical_like_suspect / critical_like_suspect_eff
#|      - critical_like_legacy / critical_source / vdrop_trust
#|    """
#|    out = df.copy()
#|    args = params["args"]
#|    tuning_level = str(params.get("tuning_level", "p2")).lower().strip()
#|
#|    def _bool_col(name: str) -> pd.Series:
#|        if name not in out.columns:
#|            return pd.Series(False, index=out.index)
#|        s = pd.to_numeric(out[name], errors="coerce").fillna(0.0)
#|        return s.ne(0)
#|
#|    def _num_col(name: str) -> pd.Series:
#|        if name in out.columns:
#|            return pd.to_numeric(out[name], errors="coerce")
#|        return pd.Series(np.nan, index=out.index, dtype=float)
#|
#|    v_ref_ok = _bool_col("v_ref_ok")
#|    data_bad = _bool_col("data_bad")
#|    group_off_like = _bool_col("group_off_like")
#|    mid_peer_ok = _num_col("mid_peer") >= float(args.mid_peer_alive_thr)
#|
#|    # V-drop hit evidence (trust-agnostic): preserve legacy guard set used in existing vdrop_condition_post.
#|    v_drop = _num_col("v_drop")
#|    mid_i = _num_col("mid_i_ratio")
#|    mid_r = _num_col("mid_ratio")
#|    vdrop_hit_any = (
#|        v_drop.notna()
#|        & np.isfinite(v_drop.to_numpy(dtype=float))
#|        & (v_drop >= float(args.v_drop_thr))
#|        & mid_i.notna()
#|        & (mid_i >= float(args.mid_i_ratio_healthy_thr))
#|        & mid_r.notna()
#|        & (mid_r >= float(args.critical_mid_ratio_min))
#|        & (mid_r <= float(args.critical_mid_ratio_max))
#|    )
#|
#|    out["critical_like_raw"] = (vdrop_hit_any & v_ref_ok).astype(int)
#|    out["critical_like_suspect_raw"] = (vdrop_hit_any & (~v_ref_ok)).astype(int)
#|
#|    # Legacy fallback semantics are preserved for p2 only.
#|    legacy_hit = pd.Series(False, index=out.index)
#|    if tuning_level == "p2":
#|        use_vdrop = v_ref_ok & np.isfinite(v_drop.to_numpy(dtype=float))
#|        cov_mid = _num_col("coverage_mid").fillna(0.0)
#|        mid_v = _num_col("mid_v_ratio")
#|        legacy_hit = (
#|            (~data_bad)
#|            & mid_peer_ok
#|            & (~use_vdrop)
#|            & (cov_mid >= float(args.coverage_min))
#|            & mid_v.notna()
#|            & (mid_v <= float(args.mid_v_ratio_critical_thr))
#|            & (mid_i >= float(args.mid_i_ratio_healthy_thr))
#|            & (mid_r >= float(args.critical_mid_ratio_min))
#|            & (mid_r <= float(args.critical_mid_ratio_max))
#|        )
#|    out["critical_like_legacy"] = legacy_hit.astype(int)
#|
#|    # Effective labels (after quality + group-off gates) are defined once here.
#|    eff_vdrop = (
#|        (out["critical_like_raw"].astype(int) == 1)
#|        & (~data_bad)
#|        & mid_peer_ok
#|        & (~group_off_like)
#|    )
#|    eff_legacy = (
#|        legacy_hit.astype(bool)
#|        & (~group_off_like)
#|    )
#|    out["critical_like_eff"] = (eff_vdrop | eff_legacy).astype(bool)
#|    out["critical_like"] = out["critical_like_eff"].astype(bool)
#|
#|    out["critical_like_suspect"] = (
#|        (out["critical_like_suspect_raw"].astype(int) == 1)
#|        & (~data_bad)
#|        & mid_peer_ok
#|        & (~group_off_like)
#|        & (~out["critical_like_eff"].astype(bool))
#|    ).astype(bool)
#|    out["critical_like_suspect_eff"] = out["critical_like_suspect"].astype(bool)
#|
#|    out["vdrop_trust"] = v_ref_ok.astype(int)
#|
#|    # Source is set once: legacy > vdrop > vdrop_suspect precedence.
#|    out["critical_source"] = "none"
#|    out.loc[out["critical_like_suspect"].astype(bool), "critical_source"] = "vdrop_suspect"
#|    out.loc[out["critical_like_eff"].astype(bool) & (~legacy_hit.astype(bool)), "critical_source"] = "vdrop"
#|    out.loc[legacy_hit.astype(bool) & out["critical_like_eff"].astype(bool), "critical_source"] = "legacy"
#|
#|    return out
#|
#|
#|def _max_run_by_panel(df: pd.DataFrame, flag_col: str) -> pd.DataFrame:
#|    """Compute max consecutive-day run length per panel for a boolean/int flag."""
#|    tmp = df[["panel_id", "date", flag_col]].copy()
#|    tmp[flag_col] = pd.to_numeric(tmp[flag_col], errors="coerce").fillna(0).astype(int)
#|    tmp = tmp.sort_values(["panel_id", "date"])
#|
#|    runs = []
#|    for pid, g in tmp.groupby("panel_id", sort=False):
#|        vals = g[flag_col].to_numpy(dtype=int)
#|        best = 0
#|        cur = 0
#|        for v in vals:
#|            if v == 1:
#|                cur += 1
#|                if cur > best:
#|                    best = cur
#|            else:
#|                cur = 0
#|        runs.append((pid, int(best)))
#|    return pd.DataFrame(runs, columns=["panel_id", f"{flag_col}_max_run"]).sort_values(
#|        f"{flag_col}_max_run", ascending=False
#|    )
#|
#|# ======== DTW & Hampel Score Helpers =========
#|
#|def dtw_distance(curve: np.ndarray, ref: np.ndarray, band: int | None = None) -> float:
#|    """
#|    Compute Dynamic Time Warping (DTW) distance between two 1D arrays.
#|    - Truncate to min(len(curve), len(ref))
#|    - Use squared difference as cost
#|    - NaNs treated as 0.0
#|    - O(N^2) baseline; if `band` is provided, apply Sakoe–Chiba constraint to speed up.
#|
#|    Parameters
#|    ----------
#|    curve, ref : np.ndarray
#|        1D arrays.
#|    band : int | None
#|        If not None, only compute cells where |i-j| <= band.
#|        Use a small band (e.g., 8~16 for length 96) to reduce compute.
#|    """
#|    a = np.nan_to_num(curve, nan=0.0, posinf=0.0, neginf=0.0)
#|    b = np.nan_to_num(ref, nan=0.0, posinf=0.0, neginf=0.0)
#|    n = min(len(a), len(b))
#|    a = a[:n]
#|    b = b[:n]
#|
#|    # If band is None, default to full DTW.
#|    if band is None:
#|        band = n  # effectively unconstrained
#|    else:
#|        band = int(max(0, band))
#|
#|    INF = 1e30
#|    D = np.full((n, n), INF, dtype=float)
#|
#|    # Initialize start
#|    D[0, 0] = (a[0] - b[0]) ** 2
#|
#|    # Initialize first column/row within band
#|    for i in range(1, n):
#|        if i <= band:
#|            D[i, 0] = D[i - 1, 0] + (a[i] - b[0]) ** 2
#|    for j in range(1, n):
#|        if j <= band:
#|            D[0, j] = D[0, j - 1] + (a[0] - b[j]) ** 2
#|
#|    # Main DP with band constraint
#|    for i in range(1, n):
#|        j_start = max(1, i - band)
#|        j_end = min(n - 1, i + band)
#|        for j in range(j_start, j_end + 1):
#|            cost = (a[i] - b[j]) ** 2
#|            D[i, j] = cost + min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])
#|
#|    return float(D[n - 1, n - 1])
#|
#|def compute_hs(curve: np.ndarray) -> float:
#|    """
#|    Compute a Hampel-like turbulence score for a 1D array.
#|    - NaNs/infs replaced with 0.0
#|    - Uses median/MAD, fallback to std if MAD too small, else 0.0
#|    - Returns fraction of |z| >= 2.5
#|    """
#|    x = np.nan_to_num(curve, nan=0.0, posinf=0.0, neginf=0.0)
#|    med = np.median(x)
#|    mad = np.median(np.abs(x - med))
#|    scale = mad if mad >= 1e-6 else np.std(x)
#|    if scale < 1e-6:
#|        return 0.0
#|    z = (x - med) / scale
#|    return float(np.mean(np.abs(z) >= 2.5))
#|
#|
#|# ========= 하루 power ratio 곡선 (AE용) =========
#|
#|def load_day_curves(
#|    csv_path: pathlib.Path,
#|    daylight_frac: float = 0.10,
#|    peer_eps: float = 1e-6,
#|    use_log_ratio: bool = False,
#|    panel_pmax_map: Dict[str, float] | None = None,
#|    peer_mode: str = "median",
#|    peer_quantile: float = 0.80,
#|    peer_ref_panel: str = "",
#|) -> Dict[str, np.ndarray]:
#|    """
#|    - P = V * I (or Pnorm = P/Pmax when panel_pmax_map is provided)
#|    - peer median P 기준으로 P_ratio = P / peerP
#|    - peerP가 max의 daylight_frac 이상인 구간만 사용
#|    - 각 패널 곡선을 길이 96으로 보간
#|    """
#|    try:
#|        df = pd.read_csv(csv_path, encoding="utf-8-sig")
#|    except Exception:
#|        df = pd.read_csv(csv_path)
#|
#|    c_dt = find_col(df, "date_time", "datetime", "timestamp", "time")
#|    c_id = find_col(df, "map_id", "panel_id", "id")
#|    c_v = find_col(df, "v_in (v)", "v_in", "vin", "input_voltage")
#|    c_i = find_col(df, "i_out (a)", "i_out", "i", "current")
#|
#|    df["_dt"] = pd.to_datetime(df[c_dt], errors="coerce")
#|    df = df.dropna(subset=["_dt"]).sort_values("_dt")
#|
#|    v = pd.to_numeric(df[c_v], errors="coerce")
#|    i = pd.to_numeric(df[c_i], errors="coerce")
#|    df["p_calc"] = (v * i).astype(float).clip(lower=0)
#|
#|    P = df.pivot_table(index="_dt", columns=c_id, values="p_calc")
#|    if panel_pmax_map:
#|        pmax_vec = pd.Series(
#|            {
#|                col: float(panel_pmax_map.get(str(col), np.nan))
#|                for col in P.columns
#|            }
#|        )
#|        if pmax_vec.isna().any():
#|            missing = [str(c) for c in P.columns if not np.isfinite(float(pmax_vec.get(c, np.nan)))]
#|            raise RuntimeError(f"Pmax missing for panels in {csv_path.name}: {missing}")
#|        P = P.divide(pmax_vec, axis=1)
#|
#|    # Site-level peer (for daylight detection)
#|    peerP_site = P.median(axis=1)
#|    if len(peerP_site) == 0 or np.nanmax(peerP_site.values) <= 0:
#|        return {}
#|
#|    # Daylight mask based on site-level peer
#|    mask = peerP_site >= float(np.nanmax(peerP_site.values)) * daylight_frac
#|    P_use = P.loc[mask]
#|
#|    # Build per-group peer medians to avoid false anomalies from heterogeneous strings
#|    # IMPORTANT: keep original column labels for safe DataFrame indexing (do not index by str(...) blindly).
#|    group_cols: Dict[str, List[Any]] = {}
#|    for pid in P_use.columns:
#|        pid_s = str(pid)
#|        group_cols.setdefault(panel_group_key(pid_s), []).append(pid)
#|    peerP_group = _build_peer_series(
#|        P_use,
#|        group_cols,
#|        mode=peer_mode,
#|        quantile=peer_quantile,
#|        ref_panel=peer_ref_panel,
#|    )
#|
#|    curves: Dict[str, np.ndarray] = {}
#|    for pid in P_use.columns:
#|        pid_s = str(pid)
#|        s = P_use[pid].astype(float)
#|        if s.notna().sum() < 10:
#|            continue
#|        gk = panel_group_key(pid_s)
#|        peer_use = peerP_group.get(gk)
#|        if peer_use is None or len(peer_use) == 0:
#|            continue
#|        peer_aligned = peer_use.reindex(s.index, method="nearest")
#|
#|        # Robust ratio: avoid division blow-up when peer baseline is tiny.
#|        # Optionally use log-stabilized ratio for heavy-tailed / low-irradiance robustness.
#|        peer_aligned_v = pd.to_numeric(peer_aligned, errors="coerce").astype(float)
#|        s_v = pd.to_numeric(s, errors="coerce").astype(float)
#|
#|        if use_log_ratio:
#|            # log1p ratio proxy: log(P+1) - log(peer+1)
#|            ratio_vals = (np.log1p(s_v.clip(lower=0.0)) - np.log1p(peer_aligned_v.clip(lower=0.0)))
#|        else:
#|            safe_peer = peer_aligned_v.where(peer_aligned_v >= float(peer_eps), np.nan)
#|            with np.errstate(divide="ignore", invalid="ignore"):
#|                ratio_vals = s_v / safe_peer
#|
#|        ratio = pd.Series(
#|            np.nan_to_num(ratio_vals.to_numpy(), nan=0.0, posinf=0.0, neginf=0.0),
#|            index=s.index,
#|        )
#|        curves[pid_s] = to_fixed_length(ratio, 96)
#|    return curves
#|
#|
#|# ========= 하루 이벤트 feature (룰용) =========
#|
#|def compute_event_features(
#|    csv_path: pathlib.Path,
#|    drop_thr: float = 0.90,
#|    sustain_thr: float = 0.80,
#|    last_minutes: int = 60,
#|    recovered_consec: int = 3,
#|    recovered_sustain_mins: int = 15,
#|    co_drop_thr: float = 0.15,
#|    daylight_event_thr: float = 0.2,
#|    peer_eps: float = 1e-6,
#|    panel_pmax_map: Dict[str, float] | None = None,
#|    peer_mode: str = "median",
#|    peer_quantile: float = 0.80,
#|    peer_ref_panel: str = "",
#|) -> Dict[str, Dict[str, Any]]:
#|    """
#|    패널별로:
#|      - drop_time: P_ratio가 sustain_thr 이하로 가장 길게 유지된 구간의 시작 시각 (daylight 안에서)
#|      - sustain_mins: drop 이후 P_ratio <= sustain_thr 인 연속 구간 최장 길이 (분)
#|      - recovered: drop 이후 P_ratio >= drop_thr 가 연속 recovered_consec 샘플 이상 유지되면 True
#|      - last_ratio: 마지막 last_minutes 동안 P_ratio 평균
#|      - last_peer: 마지막 last_minutes 동안 peerP_frac 평균
#|      - mid_ratio: 11시~15시 사이 daylight 구간에서 P_ratio 평균
#|      - mid_peer: 11시~15시 사이 daylight 구간에서 peerP_frac 평균
#|      - co_drop_frac: 최장 저하구간 동안 sustain_thr 이하에 들어간 패널 비율의 평균 (공간 동시성 지표)
#|      - NOTE: event daylight threshold is `daylight_event_thr` (default 0.2) and ratio uses `peer_eps` guard.
#|    """
#|    try:
#|        df = pd.read_csv(csv_path, encoding="utf-8-sig")
#|    except Exception:
#|        df = pd.read_csv(csv_path)
#|
#|    c_dt = find_col(df, "date_time", "datetime", "timestamp", "time")
#|    c_id = find_col(df, "map_id", "panel_id", "id")
#|    c_v = find_col(df, "v_in (v)", "v_in", "vin", "input_voltage")
#|    c_i = find_col(df, "i_out (a)", "i_out", "i", "current")
#|
#|    df["_dt"] = pd.to_datetime(df[c_dt], errors="coerce")
#|    df = df.dropna(subset=["_dt"]).sort_values("_dt")
#|
#|    V = df.pivot_table(index="_dt", columns=c_id, values=c_v)
#|    I = df.pivot_table(index="_dt", columns=c_id, values=c_i)
#|    V = V.apply(pd.to_numeric, errors="coerce").clip(lower=0)
#|    I = I.apply(pd.to_numeric, errors="coerce").clip(lower=0)
#|    P = (V * I).clip(lower=0)
#|    if panel_pmax_map:
#|        pmax_vec = pd.Series(
#|            {
#|                col: float(panel_pmax_map.get(str(col), np.nan))
#|                for col in P.columns
#|            }
#|        )
#|        if pmax_vec.isna().any():
#|            missing = [str(c) for c in P.columns if not np.isfinite(float(pmax_vec.get(c, np.nan)))]
#|            raise RuntimeError(f"Pmax missing for panels in {csv_path.name}: {missing}")
#|        P = P.divide(pmax_vec, axis=1)
#|
#|    # Site-level peer (for daylight/midday gating)
#|    peerP_site = P.median(axis=1)
#|    peerV_site = V.median(axis=1)
#|    peerI_site = I.median(axis=1)
#|    if len(peerP_site) == 0 or np.nanmax(peerP_site.values) <= 0:
#|        return {}
#|
#|    # Build per-group peer baselines (uuid.string) for ratio features
#|    # IMPORTANT: keep original column labels for safe DataFrame indexing.
#|    group_cols: Dict[str, List[Any]] = {}
#|    for pid in P.columns:
#|        pid_s = str(pid)
#|        group_cols.setdefault(panel_group_key(pid_s), []).append(pid)
#|    peerP_by_group: Dict[str, pd.Series] = {}
#|    peerV_by_group: Dict[str, pd.Series] = {}
#|    peerI_by_group: Dict[str, pd.Series] = {}
#|
#|    peerP_by_group = _build_peer_series(
#|        P,
#|        group_cols,
#|        mode=peer_mode,
#|        quantile=peer_quantile,
#|        ref_panel=peer_ref_panel,
#|    )
#|    for gk, gcols in group_cols.items():
#|        peerV_by_group[gk] = V[gcols].median(axis=1)
#|        peerI_by_group[gk] = I[gcols].median(axis=1)
#|
#|    # Fallbacks (degenerate guards)
#|    for gk in list(peerP_by_group.keys()):
#|        if len(peerP_by_group[gk]) == 0 or np.nanmax(peerP_by_group[gk].values) <= 0:
#|            peerP_by_group[gk] = peerP_site.copy()
#|        if len(peerV_by_group[gk]) == 0 or np.nanmax(peerV_by_group[gk].values) <= 0:
#|            # DO NOT fallback to power baseline (unit mismatch). Use site-level V median if available.
#|            if len(peerV_site) > 0 and np.nanmax(peerV_site.values) > 0:
#|                peerV_by_group[gk] = peerV_site.copy()
#|            else:
#|                peerV_by_group[gk] = pd.Series(np.nan, index=peerP_site.index)
#|        if len(peerI_by_group[gk]) == 0 or np.nanmax(peerI_by_group[gk].values) <= 0:
#|            # Prefer site-level I median; fallback to 1.0 only when everything is missing.
#|            if len(peerI_site) > 0 and np.nanmax(peerI_site.values) > 0:
#|                peerI_by_group[gk] = peerI_site.copy()
#|            else:
#|                peerI_by_group[gk] = pd.Series(1.0, index=peerP_site.index)
#|
#|    # Robust interval estimation (minutes)
#|    interval_min = estimate_interval_minutes(P.index)
#|    if not np.isfinite(interval_min) or interval_min <= 0:
#|        interval_min = 5.0
#|
#|    # Normalize site-level peer power to [0,1] for daylight and mid-window gating.
#|    # NOTE: peerP_site can have NaNs at timestamps where all panels are missing.
#|    # If we later take a mean over a slice that is all-NaN, np.nanmean returns NaN,
#|    # which then propagates to mid_peer/last_peer and breaks gates downstream.
#|    peerP_frac = peerP_site / float(np.nanmax(peerP_site.values))
#|    peerP_frac = peerP_frac.astype(float)
#|    peerP_frac_arr = np.nan_to_num(peerP_frac.to_numpy(), nan=0.0, posinf=0.0, neginf=0.0)
#|    # daylight (event): peerP_frac >= daylight_event_thr
#|    daylight_thr = float(daylight_event_thr)
#|    daylight_mask = peerP_frac_arr >= daylight_thr
#|
#|    daylight_mask_np = np.asarray(daylight_mask, dtype=bool)
#|
#|    times = P.index.to_numpy()
#|    times_idx = P.index
#|
#|    # midday mask: daylight and hour in [11,15)
#|    mid_mask = np.array([
#|        (pf >= daylight_thr) and (11 <= ts.hour < 15)
#|        for pf, ts in zip(peerP_frac_arr, times_idx)
#|    ])
#|
#|    # Site-level ratio table only for spatial concurrence (co-drop) diagnostics
#|    with np.errstate(divide="ignore", invalid="ignore"):
#|        R_tbl_site = P.div(peerP_site, axis=0)
#|
#|    out: Dict[str, Dict[str, Any]] = {}
#|
#|    for pid in P.columns:
#|        pid_s = str(pid)
#|        gk = panel_group_key(pid_s)
#|        peerP = peerP_by_group.get(gk, peerP_site)
#|        peerV = peerV_by_group.get(gk, peerV_site)
#|        peerI = peerI_by_group.get(gk, peerI_site)
#|        p = P[pid].astype(float).to_numpy()
#|        if np.sum(np.isfinite(p)) < 5:
#|            continue
#|
#|        # coverage: daylight 구간 중 실제 측정이 있는 비율
#|        valid_day = np.isfinite(p) & daylight_mask_np
#|        daylight_count = int(daylight_mask_np.sum())
#|        if daylight_count > 0:
#|            coverage = float(valid_day.sum() / daylight_count)
#|        else:
#|            coverage = 0.0
#|
#|        # coverage within mid-window (11~15) to avoid "noon holes" masking issues
#|        if int(np.sum(mid_mask)) > 0:
#|            valid_mid = np.isfinite(p) & mid_mask
#|            coverage_mid = float(np.sum(valid_mid) / int(np.sum(mid_mask)))
#|        else:
#|            coverage_mid = float(coverage)
#|
#|        # EVENT ratio with peer-eps gating (SSOT): peer < eps -> NaN (avoid 0/0, x/0 blow-ups)
#|        peer_arr = pd.to_numeric(peerP, errors="coerce").astype(float).to_numpy()
#|        safe_peer = np.where(peer_arr >= float(peer_eps), peer_arr, np.nan)
#|        with np.errstate(divide="ignore", invalid="ignore"):
#|            r = p / safe_peer
#|        # Keep NaNs here; downstream masks/np.isfinite() will exclude invalid points deterministically.
#|
#|        # V/I ratio arrays (panel vs *group* peer)
#|        v_arr = V[pid].astype(float).to_numpy()
#|        i_arr = I[pid].astype(float).to_numpy()
#|        with np.errstate(divide="ignore", invalid="ignore"):
#|            vr = v_arr / peerV.to_numpy()
#|            ir = i_arr / peerI.to_numpy()
#|        vr = np.nan_to_num(vr, nan=0.0, posinf=0.0, neginf=0.0)
#|        ir = np.nan_to_num(ir, nan=0.0, posinf=0.0, neginf=0.0)
#|
#|        # daylight-masked versions
#|        vr_day = vr.copy()
#|        ir_day = ir.copy()
#|        vr_day[~daylight_mask_np] = np.nan
#|        ir_day[~daylight_mask_np] = np.nan
#|
#|        # Spatial concurrence helper series for this panel/day
#|        # Fraction of panels that are also <= sustain_thr at each timestamp (within daylight)
#|        # NOTE: Uses median peer baseline; if a large fraction drops together, it's more likely environmental.
#|        with np.errstate(invalid="ignore"):
#|            co_series = (R_tbl_site <= sustain_thr).mean(axis=1).to_numpy(dtype=float)
#|            co_series = np.nan_to_num(co_series, nan=0.0, posinf=0.0, neginf=0.0)
#|        co_series_day = co_series.copy()
#|        co_series_day[~daylight_mask_np] = np.nan
#|
#|        # daylight 부분만 고려
#|        r_day = r.copy()
#|        r_day[~daylight_mask_np] = np.nan
#|
#|        # longest low segment: P_ratio <= sustain_thr within daylight
#|        cond = np.isfinite(r_day) & (r_day <= sustain_thr)
#|
#|        # Feature expansion: segment counts / total low minutes / quantiles / low-area
#|        r_day_f = r_day.copy()
#|        valid_mask = np.isfinite(r_day_f)
#|
#|        if np.any(valid_mask):
#|            min_ratio = float(np.nanmin(r_day_f))
#|            p10_ratio = float(np.nanpercentile(r_day_f[valid_mask], 10))
#|            p50_ratio = float(np.nanpercentile(r_day_f[valid_mask], 50))
#|        else:
#|            min_ratio = 0.0
#|            p10_ratio = 0.0
#|            p50_ratio = 0.0
#|
#|        # total low minutes
#|        total_low_pts = int(np.sum(cond))
#|        total_low_mins = int(round(total_low_pts * float(interval_min)))
#|
#|        # low area: sum(thr - ratio) where ratio < thr
#|        low_area = float(np.nansum(np.maximum(0.0, float(sustain_thr) - np.nan_to_num(r_day_f, nan=np.nan))))
#|
#|        # segment count: number of low segments
#|        seg_count = 0
#|        prev = False
#|        for flag in cond:
#|            if flag and (not prev):
#|                seg_count += 1
#|            prev = bool(flag)
#|
#|        # compute mid_ratio and mid_peer_val (+ NEW: mid_v_ratio, mid_i_ratio)
#|        if np.any(mid_mask):
#|            mid_ratio = nanmean_or(r[mid_mask], default=np.nan)
#|            mid_peer_val = float(np.mean(peerP_frac_arr[mid_mask])) if np.any(mid_mask) else float(np.mean(peerP_frac_arr))
#|            mid_v_ratio = nanmean_or(vr[mid_mask], default=np.nan)
#|            mid_i_ratio = nanmean_or(ir[mid_mask], default=np.nan)
#|        else:
#|            mid_ratio = nanmean_or(r_day, default=np.nan)
#|            mid_peer_val = float(np.mean(peerP_frac_arr))
#|            mid_v_ratio = nanmean_or(vr_day, default=np.nan)
#|            mid_i_ratio = nanmean_or(ir_day, default=np.nan)
#|
#|        if not np.any(cond):
#|            # no meaningful low segment
#|            out[pid_s] = {
#|                "drop_time": "",
#|                "sustain_mins": 0,
#|                "recovered": False,
#|                "last_ratio": nanmean_or(r_day, default=np.nan),
#|                "last_peer": float(np.mean(peerP_frac_arr)),
#|                "mid_ratio": float(mid_ratio),
#|                "mid_peer": float(mid_peer_val),
#|                "mid_v_ratio": float(mid_v_ratio) if 'mid_v_ratio' in locals() else nanmean_or(vr_day, default=np.nan),
#|                "mid_i_ratio": float(mid_i_ratio) if 'mid_i_ratio' in locals() else nanmean_or(ir_day, default=np.nan),
#|                "coverage": float(coverage),
#|                "co_drop_frac": 0.0,
#|                "recovered_any": False,
#|                "recovered_sustained": False,
#|                "re_drop": False,
#|                "coverage_mid": float(coverage_mid),
#|                "seg_count": int(seg_count),
#|                "total_low_mins": int(total_low_mins),
#|                "min_ratio": float(min_ratio),
#|                "p10_ratio": float(p10_ratio),
#|                "p50_ratio": float(p50_ratio),
#|                "low_area": float(low_area),
#|            }
#|            continue
#|
#|        # find longest consecutive True segment in cond
#|        max_len = 0
#|        best_start = None
#|        best_end = None
#|        current_start = None
#|        current_len = 0
#|
#|        for idx, flag in enumerate(cond):
#|            if flag:
#|                if current_start is None:
#|                    current_start = idx
#|                    current_len = 1
#|                else:
#|                    current_len += 1
#|                if current_len > max_len:
#|                    max_len = current_len
#|                    best_start = current_start
#|                    best_end = idx
#|            else:
#|                current_start = None
#|                current_len = 0
#|
#|        drop_idx = best_start
#|        if drop_idx is None:
#|            # fallback: treat as no drop
#|            out[pid_s] = {
#|                "drop_time": "",
#|                "sustain_mins": 0,
#|                "recovered": False,
#|                "last_ratio": nanmean_or(r_day, default=np.nan),
#|                "last_peer": float(np.mean(peerP_frac_arr)),
#|                "mid_ratio": float(mid_ratio),
#|                "mid_peer": float(mid_peer_val),
#|                "mid_v_ratio": float(mid_v_ratio) if 'mid_v_ratio' in locals() else nanmean_or(vr_day, default=np.nan),
#|                "mid_i_ratio": float(mid_i_ratio) if 'mid_i_ratio' in locals() else nanmean_or(ir_day, default=np.nan),
#|                "coverage": float(coverage),
#|                "co_drop_frac": 0.0,
#|                "recovered_any": False,
#|                "recovered_sustained": False,
#|                "re_drop": False,
#|                "coverage_mid": float(coverage_mid),
#|                "seg_count": int(seg_count),
#|                "total_low_mins": int(total_low_mins),
#|                "min_ratio": float(min_ratio),
#|                "p10_ratio": float(p10_ratio),
#|                "p50_ratio": float(p50_ratio),
#|                "low_area": float(low_area),
#|            }
#|            continue
#|
#|        # Spatial concurrence score for the chosen (longest) low segment
#|        # Average fraction of panels that are also low during this segment
#|        if best_end is not None and best_start is not None:
#|            seg = co_series_day[best_start : best_end + 1]
#|            co_drop_frac = nanmean_or(seg, default=0.0)
#|        else:
#|            co_drop_frac = 0.0
#|
#|        drop_time = pd.Timestamp(times[drop_idx]).isoformat()
#|        sustain_mins = int(round(max_len * float(interval_min)))
#|
#|        # recovered definitions
#|        # recovered_any: any post-segment ratio >= drop_thr
#|        # recovered_sustained: post-segment ratio >= drop_thr sustained for recovered_sustain_mins
#|        # re_drop: after sustained recovery, drops again to sustain_thr or below
#|        recovered_any = False
#|        recovered_sustained = False
#|        re_drop = False
#|
#|        if best_end is not None and best_end + 1 < len(r):
#|            tail = r[best_end + 1 :]
#|            tail_ok = np.isfinite(tail) & (tail >= float(drop_thr))
#|            recovered_any = bool(np.any(tail_ok))
#|
#|            # sustain requirement in points (time-based)
#|            sustain_pts = int(max(1, np.ceil(float(recovered_sustain_mins) / float(interval_min))))
#|
#|            # longest consecutive True run
#|            run = 0
#|            best_run = 0
#|            for flag in tail_ok:
#|                if flag:
#|                    run += 1
#|                    best_run = max(best_run, run)
#|                else:
#|                    run = 0
#|
#|            recovered_sustained = bool(best_run >= sustain_pts)
#|
#|            # re_drop: only meaningful after sustained recovery
#|            if recovered_sustained:
#|                # find first index where sustained recovery starts
#|                run = 0
#|                start_idx = None
#|                for k, flag in enumerate(tail_ok):
#|                    if flag:
#|                        run += 1
#|                        if run >= sustain_pts:
#|                            start_idx = k - sustain_pts + 1
#|                            break
#|                    else:
#|                        run = 0
#|
#|                if start_idx is not None:
#|                    after_rec = tail[start_idx + sustain_pts :]
#|                    after_low = np.isfinite(after_rec) & (after_rec <= float(sustain_thr))
#|                    re_drop = bool(np.any(after_low))
#|
#|        # backward-compatible alias (old field)
#|        recovered = bool(recovered_sustained)
#|
#|        # 마지막 last_minutes 동안 평균
#|        if len(times) > 0:
#|            last_dt = pd.Timestamp(times[-1])
#|            start_last = last_dt - pd.Timedelta(minutes=last_minutes)
#|            last_mask = (times >= np.datetime64(start_last)) & (times <= np.datetime64(last_dt))
#|        else:
#|            last_mask = np.zeros_like(r, dtype=bool)
#|
#|        if np.any(last_mask):
#|            last_ratio = nanmean_or(r[last_mask], default=np.nan)
#|            last_peer = float(np.mean(peerP_frac_arr[last_mask])) if np.any(last_mask) else float(np.mean(peerP_frac_arr))
#|        else:
#|            last_ratio = nanmean_or(r_day, default=np.nan)
#|            last_peer = float(np.mean(peerP_frac_arr))
#|
#|        out[pid_s] = {
#|            "drop_time": drop_time,
#|            "sustain_mins": sustain_mins,
#|            "recovered": bool(recovered),
#|            "last_ratio": last_ratio,
#|            "last_peer": last_peer,
#|            "mid_ratio": float(mid_ratio),
#|            "mid_peer": float(mid_peer_val),
#|            "mid_v_ratio": float(mid_v_ratio),
#|            "mid_i_ratio": float(mid_i_ratio),
#|            "coverage": float(coverage),
#|            "co_drop_frac": float(co_drop_frac),
#|            "recovered_any": bool(recovered_any),
#|            "recovered_sustained": bool(recovered_sustained),
#|            "re_drop": bool(re_drop),
#|            "coverage_mid": float(coverage_mid),
#|            "seg_count": int(seg_count),
#|            "total_low_mins": int(total_low_mins),
#|            "min_ratio": float(min_ratio),
#|            "p10_ratio": float(p10_ratio),
#|            "p50_ratio": float(p50_ratio),
#|            "low_area": float(low_area),
#|        }
#|
#|    return out
#|
#|
#|# ========= Autoencoder =========
#|
#|class AE(nn.Module):
#|    def __init__(self, dim: int = 96, latent: int = 16):
#|        super().__init__()
#|        self.encoder = nn.Sequential(
#|            nn.Linear(dim, 64),
#|            nn.ReLU(),
#|            nn.Linear(64, latent),
#|        )
#|        self.decoder = nn.Sequential(
#|            nn.Linear(latent, 64),
#|            nn.ReLU(),
#|            nn.Linear(64, dim),
#|        )
#|
#|    def forward(self, x: torch.Tensor) -> torch.Tensor:
#|        z = self.encoder(x)
#|        out = self.decoder(z)
#|        return out
#|
#|
#|def train_ae(train_mat: np.ndarray, latent: int, epochs: int, device: str) -> Tuple[AE, np.ndarray]:
#|    x = torch.tensor(train_mat, dtype=torch.float32)
#|    model = AE(dim=train_mat.shape[1], latent=latent).to(device)
#|    opt = optim.Adam(model.parameters(), lr=1e-3)
#|    loss_fn = nn.MSELoss()
#|
#|    ds = torch.utils.data.TensorDataset(x)
#|    loader = torch.utils.data.DataLoader(ds, batch_size=64, shuffle=True)
#|
#|    model.train()
#|    for _ in range(epochs):
#|        for (batch,) in loader:
#|            batch = batch.to(device)
#|            opt.zero_grad()
#|            rec = model(batch)
#|            loss = loss_fn(rec, batch)
#|            loss.backward()
#|            opt.step()
#|
#|    model.eval()
#|    with torch.no_grad():
#|        rec = model(x.to(device)).cpu().numpy()
#|    train_err = ((train_mat - rec) ** 2).mean(axis=1)
#|    return model, train_err
#|
#|
#|# ========= CLI =========
#|
#|def parse_args():
#|    ap = argparse.ArgumentParser()
#|    ap.add_argument("--dir", required=False,
#|                    help="Input directory containing daily CSVs. Prefer --site for portable runs.")
#|    ap.add_argument("--site", default=None,
#|                    help="Site key to use data/<site>/raw as input (portable, recommended).")
#|    ap.add_argument("--data-root", default=None,
#|                    help="Project data root. Defaults to <project_root>/data if omitted.")
#|    ap.add_argument("--out-dir", default=None,
#|                    help="Output directory. Defaults to data/<site>/out (or <dir>/out).")
#|    ap.add_argument("--log-dir", default=None,
#|                    help="Log directory. Defaults to data/<site>/log (or <dir>/log).")
#|    ap.add_argument("--pattern", default="*.csv")
#|    ap.add_argument("--train-start", required=True)
#|    ap.add_argument("--train-end", required=True)
#|    ap.add_argument("--eval-start", required=True)
#|    ap.add_argument("--eval-end", required=True)
#|    ap.add_argument("--epochs", type=int, default=40)
#|    ap.add_argument("--latent", type=int, default=16)
#|    ap.add_argument("--contam", type=float, default=0.10)
#|    ap.add_argument("--recon-mult", type=float, default=1.0)
#|    ap.add_argument("--device", default="cpu")
#|    ap.add_argument("--seed", type=int, default=42,
#|                    help="Random seed for reproducible training/eval (default 42).")
#|    # 튜닝 단계 스위치 (엄격 진행)
#|    ap.add_argument(
#|        "--tuning-level",
#|        choices=["p0", "p1", "p2"],
#|        default="p2",
#|        help=(
#|            "Tuning stage switch. p0=baseline(dead/confirmed only), p1=+group_off_like gate, p2=full (critical/shadow/EWS/etc)."
#|        ),
#|    )
#|
#|    # 룰 파라미터
#|    ap.add_argument("--sustain-mins", type=int, default=40)
#|    ap.add_argument("--drop-thr", type=float, default=0.90)
#|    ap.add_argument("--sustain-thr", type=float, default=0.80)
#|    ap.add_argument("--last-ratio-thr", type=float, default=0.80)
#|    ap.add_argument("--last-peer-thr", type=float, default=0.40)
#|
#|    # 추가 룰 파라미터
#|    ap.add_argument("--event-sustain-mins", type=int, default=15)
#|    ap.add_argument("--mid-peer-alive-thr", type=float, default=0.5)
#|    ap.add_argument("--mid-ratio-dead-thr", type=float, default=0.2)
#|
#|    # critical-like (V-drop) parameters (for bypass-diode-short-like patterns)
#|    # NOTE: In real systems, V-drop levels are not always exactly ~33%.
#|    # We therefore prefer a *relative* drop vs per-(date, group_key) peer V reference.
#|    ap.add_argument(
#|        "--v-drop-thr",
#|        type=float,
#|        default=0.20,
#|        help="Critical-like V-drop threshold expressed as v_drop = 1 - mid_v_ratio/v_ref (default 0.20).",
#|    )
#|    ap.add_argument(
#|        "--v-ref-min",
#|        type=float,
#|        default=0.30,
#|        help="Minimum v_ref (group median mid_v_ratio) required to evaluate v_drop (default 0.30).",
#|    )
#|    ap.add_argument(
#|        "--v-ref-vspan-max",
#|        type=float,
#|        default=0.12,
#|        help="Maximum allowed v_ref span (p90-p10 of mid_v_ratio within (date,group_key)) to trust v_ref/v_drop (default 0.12).",
#|    )
#|    ap.add_argument(
#|        "--v-ref-min-n",
#|        type=int,
#|        default=6,
#|        help="Minimum number of reference panels within (date, group_key) required to trust v_ref/v_drop (default 6).",
#|    )
#|
#|    # Backward-compat (legacy): keep old absolute threshold; not used when v_drop is available.
#|    ap.add_argument(
#|        "--mid-v-ratio-critical-thr",
#|        type=float,
#|        default=0.75,
#|        help="(Legacy) Absolute critical-like threshold for mid_v_ratio. Prefer --v-drop-thr.",
#|    )
#|    ap.add_argument(
#|        "--mid-i-ratio-healthy-thr",
#|        type=float,
#|        default=0.85,
#|        help="Healthy-ish current threshold for mid_i_ratio when labeling V-drop critical-like (default 0.85).",
#|    )
#|    ap.add_argument(
#|        "--critical_mid_ratio_min",
#|        type=float,
#|        default=0.40,
#|        help="Minimum mid_ratio required to treat V-drop as critical-like (exclude near-dead/off cases). Default 0.40.",
#|    )
#|    ap.add_argument(
#|        "--critical_mid_ratio_max",
#|        type=float,
#|        default=0.95,
#|        help="Maximum mid_ratio allowed for critical-like (exclude fully-normal days). Default 0.95.",
#|    )
#|    ap.add_argument(
#|        "--critical-days",
#|        type=int,
#|        default=5,
#|        help="Number of consecutive critical-like days to confirm critical_fault (default 5).",
#|    )
#|
#|    # critical 2-stage split (confirmed vs suspect)
#|    ap.add_argument("--critical-peer-min", type=float, default=0.6,
#|                    help="Only evaluate critical stability on days with mid_peer >= this value (default 0.6).")
#|    ap.add_argument("--critical-vspan-max", type=float, default=0.12,
#|                    help="Max allowed v_span (p90-p10 of mid_v_ratio) for confirmed critical panels (default 0.12).")
#|    ap.add_argument("--critical-min-days", type=int, default=5,
#|                    help="Minimum number of critical-like days for confirmed critical panels (default 5).")
#|
#|    # shadow-like refinement parameters
#|    ap.add_argument("--shadow-seg-min", type=int, default=2,
#|                    help="Minimum number of low segments (seg_count) for shadow_like refinement (default 2).")
#|    ap.add_argument("--shadow-min-ratio-floor", type=float, default=0.30,
#|                    help="Minimum min_ratio floor to keep shadow_like from capturing near-dead patterns (default 0.30).")
#|    ap.add_argument("--dead-days", type=int, default=2)
#|    ap.add_argument("--coverage-min", type=float, default=0.5)
#|
#|    ap.add_argument("--ews-quantile", type=float, default=0.9,
#|                    help="전체 사이트 분포에서 EWS 롤링 지표 상위 분위수 (기본 0.9)")
#|    ap.add_argument("--ews-k-sigma", type=float, default=1.0,
#|                    help="월별 베이스라인(mean + k*sigma) 보정 시 사용할 k 값 (기본 1.0)")
#|    ap.add_argument("--dtw-band", type=int, default=12,
#|                    help="DTW Sakoe–Chiba band width (None/<=0 means unconstrained). Default 12 for length-96 curves.")
#|    ap.add_argument("--recovered-consec", type=int, default=3,
#|                    help="Recovered 판단 시 drop_thr 이상을 연속으로 만족해야 하는 최소 샘플 수 (기본 3).")
#|    ap.add_argument("--shadow-co-drop-thr", type=float, default=0.15,
#|                    help="shadow_like 정제 시 co_drop_frac(공간 동시성) 최소 임계값 (기본 0.15).")
#|    ap.add_argument("--recovered-sustain-mins", type=int, default=15,
#|                    help="Recovered_sustained 판단을 위한 최소 유지 시간(분). interval 기반으로 points로 변환.")
#|    ap.add_argument("--peer-eps", type=float, default=1e-6,
#|                    help="ratio 계산 시 peer baseline이 이 값보다 작으면 제외(division blow-up 방지).")
#|    ap.add_argument("--daylight-event-thr", type=float, default=0.2,
#|                    help="Event/daylight gate threshold on peerP_frac for compute_event_features (default 0.2; site override allowed).")
#|    ap.add_argument("--use-log-ratio", action="store_true",
#|                    help="AE 입력 ratio를 log1p(P)-log1p(peer)로 안정화하여 사용.")
#|    ap.add_argument("--pmax-info-csv", default="",
#|                    help="Optional TECNALIA module info CSV(semicolon-separated). When set, power axis uses Pnorm=P/Pmax(panel).")
#|    ap.add_argument("--peer-mode", choices=["median", "quantile", "ref"], default="median",
#|                    help="Peer baseline mode for ratio features: median(legacy), quantile, ref.")
#|    ap.add_argument("--peer-quantile", type=float, default=0.80,
#|                    help="Peer quantile used when --peer-mode quantile/ref fallback (default 0.80).")
#|    ap.add_argument("--peer-ref-panel", default="",
#|                    help="Reference panel_id when --peer-mode ref. Missing timestamps fall back to peer-quantile.")
#|
#|    # group/string-level OFF-like detection (protect against mislabeling string events as panel faults)
#|    ap.add_argument("--group-off-min-panels", type=int, default=10,
#|                    help="(Group-level) If >= this many panels in the SAME group_key are simultaneously dead-like (state_dead) on a day, consider group-off candidate.")
#|    ap.add_argument("--group-off-min-frac", type=float, default=0.50,
#|                    help="(Group-level) Minimum dead-like fraction within group_key to consider group-off candidate.")
#|    ap.add_argument("--group-off-max-frac", type=float, default=1.00,
#|                    help="(Group-level) Maximum dead-like fraction within group_key (set high; site-wide protection is handled elsewhere).")
#|    ap.add_argument("--group-off-jaccard", type=float, default=0.80,
#|                    help="Jaccard similarity threshold between consecutive days' dead-like panel sets to confirm a persistent group-off event.")
#|    ap.add_argument("--group-off-allow-single-day", action="store_true",
#|                    help="If set, allow single-day group-off labeling even without consecutive-day set stability.")
#|    return ap.parse_args()
#|
#|
#|def _setup_paths(args, seed: int):
#|    """Resolve input/output/log paths and split train/eval files by filename date."""
#|    # ---- Portable path resolution (project-root relative) ----
#|    script_path = pathlib.Path(__file__).resolve()
#|    project_root = script_path.parents[1]  # pvdiag/
#|
#|    # Determine data root
#|    if args.data_root is not None:
#|        data_root = pathlib.Path(args.data_root).expanduser().resolve()
#|    else:
#|        data_root = (project_root / "data").resolve()
#|
#|    # Determine input directory
#|    if args.site:
#|        site = str(args.site).strip()
#|        data_dir = (data_root / site / "raw").resolve()
#|    elif args.dir:
#|        data_dir = pathlib.Path(args.dir).expanduser().resolve()
#|        site = None
#|    else:
#|        raise RuntimeError("Must provide either --site <name> or --dir <path>.")
#|
#|    # Determine output/log directories
#|    if args.out_dir is not None:
#|        out_dir = pathlib.Path(args.out_dir).expanduser().resolve()
#|    else:
#|        out_dir = ((data_root / site / "out") if site else (data_dir / "out")).resolve()
#|
#|    if args.log_dir is not None:
#|        log_dir = pathlib.Path(args.log_dir).expanduser().resolve()
#|    else:
#|        log_dir = ((data_root / site / "log") if site else (data_dir / "log")).resolve()
#|
#|    out_dir.mkdir(parents=True, exist_ok=True)
#|    log_dir.mkdir(parents=True, exist_ok=True)
#|
#|    # Record run configuration for reproducibility
#|    import sys
#|    from datetime import datetime
#|    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#|    run_info_path = log_dir / f"run_{run_ts}.json"
#|    try:
#|        run_info = {
#|            "timestamp": run_ts,
#|            "cwd": str(pathlib.Path.cwd()),
#|            "script": str(script_path),
#|            "project_root": str(project_root),
#|            "data_root": str(data_root),
#|            "site": site,
#|            "data_dir": str(data_dir),
#|            "out_dir": str(out_dir),
#|            "log_dir": str(log_dir),
#|            "argv": sys.argv,
#|            "python": sys.version,
#|            "seed": seed,
#|        }
#|        run_info_path.write_text(json.dumps(run_info, ensure_ascii=False, indent=2), encoding="utf-8")
#|        print(f"[OK] wrote run config: {run_info_path}")
#|    except Exception as e:
#|        print(f"[WARN] failed to write run config: {e}")
#|
#|    if not data_dir.exists():
#|        raise RuntimeError(f"input directory not found: {data_dir}")
#|
#|    def in_range(p: pathlib.Path, s: str, e: str) -> bool:
#|        """Filename date filter.
#|        - Extracts first occurrence of YYYY-MM-DD anywhere in the filename.
#|        - Compares as dates to avoid lexicographic corner cases.
#|        """
#|        d = extract_date_from_filename(p.name)
#|        if pd.isna(d):
#|            return False
#|        sdt = pd.to_datetime(s, errors="coerce").normalize()
#|        edt = pd.to_datetime(e, errors="coerce").normalize()
#|        if pd.isna(sdt) or pd.isna(edt):
#|            return False
#|        return (d >= sdt) and (d <= edt)
#|
#|    files = sorted(
#|        p for p in data_dir.glob(args.pattern)
#|        if p.is_file() and p.suffix.lower() == ".csv"
#|    )
#|
#|    print(f"[INFO] input_dir = {data_dir}")
#|    print(f"[INFO] out_dir   = {out_dir}")
#|    print(f"[INFO] log_dir   = {log_dir}")
#|
#|    train_files = [p for p in files if in_range(p, args.train_start, args.train_end)]
#|    eval_files = [p for p in files if in_range(p, args.eval_start, args.eval_end)]
#|
#|    # Diagnostics: show detected date range in filenames
#|    try:
#|        import re
#|        ds = []
#|        for p in files:
#|            m = re.search(r"(\d{4}-\d{2}-\d{2})", p.name)
#|            if m:
#|                d = pd.to_datetime(m.group(1), errors="coerce")
#|                if pd.notna(d):
#|                    ds.append(d)
#|        if ds:
#|            print(f"[INFO] detected file date range: {min(ds).date()} ~ {max(ds).date()} (n={len(ds)})")
#|    except Exception:
#|        pass
#|
#|    if not train_files:
#|        raise RuntimeError(
#|            f"no training files in range: {args.train_start} ~ {args.train_end} (pattern={args.pattern})"
#|        )
#|    if not eval_files:
#|        raise RuntimeError(
#|            f"no eval files in range: {args.eval_start} ~ {args.eval_end} (pattern={args.pattern})"
#|        )
#|
#|    return data_dir, out_dir, log_dir, site, train_files, eval_files
#|
#|
#|def _detect_group_off(out: pd.DataFrame, args) -> pd.DataFrame:
#|    # ---- Group-off / string-off like event detection (group_key-level) ----
#|    # What we observed in Gangui:
#|    # - Only ~10~15% of site panels are dead-like on those days,
#|    # - but within specific group_key (string-like groups), dead_frac can be 50~80%.
#|    # Site-level detection is too coarse; it can over-gate unrelated panels.
#|    #
#|    # New behavior:
#|    # - Detect OFF-like events per (date, group_key)
#|    # - Mark only those panels in the affected group_key as group_off_like
#|    # - Keep group_off_date as a convenience (any group-off group on that date)
#|    out["group_off_group"] = False  # row-level: panel belongs to a group_key flagged as OFF-like on that date
#|
#|    flagged_pairs: set[tuple[pd.Timestamp, str]] = set()
#|
#|    # For each group_key, track previous day's dead-set to compute Jaccard stability
#|    prev_dead_set_by_gk: Dict[str, set] = {}
#|    prev_date_by_gk: Dict[str, pd.Timestamp] = {}
#|    prev_candidate_by_gk: Dict[str, bool] = {}
#|
#|    # Iterate by date then by group_key
#|    for d in sorted(out["date"].dropna().unique()):
#|        gd = out[out["date"] == d]
#|        for gk, gg in gd.groupby("group_key"):
#|            # dead-like set within good data only (within this group)
#|            dead_set = set(
#|                gg.loc[(~gg["data_bad"].astype(bool)) & (gg["state_dead"].astype(bool)), "panel_id"].astype(str).tolist()
#|            )
#|            n_dead = len(dead_set)
#|            n_total = int(gg["panel_id"].nunique())
#|            frac = (n_dead / n_total) if n_total > 0 else 0.0
#|
#|            # Candidate definition is applied per-group now.
#|            candidate = (
#|                (n_dead >= int(args.group_off_min_panels))
#|                & (frac >= float(args.group_off_min_frac))
#|                & (frac <= float(args.group_off_max_frac))
#|            )
#|
#|            confirmed_today = False
#|
#|            # Allow single-day labeling when explicitly enabled
#|            if candidate and bool(args.group_off_allow_single_day):
#|                confirmed_today = True
#|
#|            # Consecutive-day stability check (Jaccard)
#|            if candidate and prev_candidate_by_gk.get(gk, False):
#|                prev_dead = prev_dead_set_by_gk.get(gk)
#|                if prev_dead is not None:
#|                    inter = len(dead_set & prev_dead)
#|                    union = len(dead_set | prev_dead)
#|                    jacc = (inter / union) if union > 0 else 0.0
#|                    if jacc >= float(args.group_off_jaccard):
#|                        confirmed_today = True
#|                        # also mark previous day as group-off for this group_key
#|                        prev_d = prev_date_by_gk.get(gk)
#|                        if prev_d is not None:
#|                            flagged_pairs.add((prev_d, gk))
#|
#|            if confirmed_today:
#|                flagged_pairs.add((d, gk))
#|
#|            # update trackers
#|            prev_dead_set_by_gk[gk] = dead_set
#|            prev_date_by_gk[gk] = d
#|            prev_candidate_by_gk[gk] = bool(candidate)
#|
#|    if flagged_pairs:
#|        # row-level membership in flagged (date, group_key)
#|        pair_series = list(zip(out["date"], out["group_key"]))
#|        out["group_off_group"] = [((dd, ggk) in flagged_pairs) for (dd, ggk) in pair_series]
#|
#|    # convenience flag: any group-off group exists on that date
#|    group_dates = {dd for (dd, _gk) in flagged_pairs}
#|    out["group_off_date"] = out["date"].isin(group_dates)
#|
#|    # group_off_like is now precise: only dead-like panels in the flagged group_key
#|    out["group_off_like"] = (
#|        out["group_off_group"].astype(bool)
#|        & (~out["data_bad"].astype(bool))
#|        & out["state_dead"].astype(bool)
#|    )
#|    # --- P1/P2 safety: group_off_like must never contribute to V-drop/critical signals ---
#|    # Rationale: group/string OFF events can produce apparent V-drop rows and confuse downstream checks.
#|    # We keep group_off_like as its own category and mask V-drop-related fields on those rows.
#|    go_mask = out["group_off_like"].fillna(False).astype(bool)
#|    if go_mask.any():
#|        out.loc[go_mask, "v_drop"] = np.nan
#|        out.loc[go_mask, "v_ref_ok"] = False
#|        # keep ops visibility: treat as no usable reference for these rows
#|        if "no_ref" in out.columns:
#|            out.loc[go_mask, "no_ref"] = True
#|    return out
#|
#|
#|def _compute_ews(out: pd.DataFrame, args) -> pd.DataFrame:
#|    q = float(args.ews_quantile)
#|    k_sigma = float(args.ews_k_sigma)
#|
#|    out["ews_month"] = out["date"].dt.month
#|
#|    # Pre-allocate causal baseline columns (for transparency/debugging)
#|    out["mid_base_mean"] = np.nan
#|    out["mid_base_std"] = np.nan
#|    out["dtw_base_mean"] = np.nan
#|    out["dtw_base_std"] = np.nan
#|    out["hs_base_mean"] = np.nan
#|    out["hs_base_std"] = np.nan
#|
#|    # Causal conditions (filled date-by-date)
#|    cond_var = pd.Series(False, index=out.index)
#|    cond_dtw = pd.Series(False, index=out.index)
#|    cond_hs = pd.Series(False, index=out.index)
#|
#|    # eventA 빈도: 최근 7일 중 절반 이상 event_A 발생 (행 단위로 바로 계산 가능)
#|    cond_evt = out["ews_eventA_freq_7d"] >= 0.5
#|
#|    # Date-by-date causal thresholds/baselines
#|    for d in sorted(out["date"].dropna().unique()):
#|        mask_d = out["date"] == d
#|        past = out.loc[out["date"] < d]
#|
#|        # If no past, leave conditions as False for this date
#|        if past.empty:
#|            continue
#|
#|        # Global (site-wide) thresholds from past only
#|        def _past_thr(series: pd.Series, qq: float) -> float:
#|            vals = series.to_numpy()
#|            if np.isfinite(vals).any():
#|                return float(np.nanquantile(vals, qq))
#|            return np.nan
#|
#|        var_thr = _past_thr(past["ews_mid_var_7d"], q)
#|        dtw_thr = _past_thr(past["ews_dtw_mean_7d"], q)
#|        hs_thr = _past_thr(past["ews_hs_mean_7d"], q)
#|
#|        # Panel×Month baseline from past only
#|        base = (
#|            past.groupby(["panel_id", "ews_month"])[
#|                ["ews_mid_var_7d", "ews_dtw_mean_7d", "ews_hs_mean_7d"]
#|            ]
#|            .agg(["mean", "std"])
#|        )
#|
#|        # Helper to fetch baseline stats for current rows
#|        def _get_base(metric: str, stat: str) -> pd.Series:
#|            s = base[(metric, stat)]
#|            # align by (panel_id, ews_month)
#|            key = list(zip(out.loc[mask_d, "panel_id"], out.loc[mask_d, "ews_month"]))
#|            return pd.Series([s.get(k, np.nan) for k in key], index=out.index[mask_d])
#|
#|        # Fill baseline columns for this date (debug visibility)
#|        out.loc[mask_d, "mid_base_mean"] = _get_base("ews_mid_var_7d", "mean")
#|        out.loc[mask_d, "mid_base_std"] = _get_base("ews_mid_var_7d", "std")
#|        out.loc[mask_d, "dtw_base_mean"] = _get_base("ews_dtw_mean_7d", "mean")
#|        out.loc[mask_d, "dtw_base_std"] = _get_base("ews_dtw_mean_7d", "std")
#|        out.loc[mask_d, "hs_base_mean"] = _get_base("ews_hs_mean_7d", "mean")
#|        out.loc[mask_d, "hs_base_std"] = _get_base("ews_hs_mean_7d", "std")
#|
#|        # Apply both gates (global quantile + seasonal baseline) using past-only statistics
#|        if np.isfinite(var_thr) and var_thr > 0:
#|            cv = out.loc[mask_d, "ews_mid_var_7d"] >= var_thr
#|        else:
#|            cv = pd.Series(False, index=out.index[mask_d])
#|        mid_thr_base = out.loc[mask_d, "mid_base_mean"] + k_sigma * out.loc[mask_d, "mid_base_std"].fillna(0.0)
#|        cv = cv & out.loc[mask_d, "mid_base_mean"].notna() & (out.loc[mask_d, "ews_mid_var_7d"] >= mid_thr_base)
#|        cond_var.loc[mask_d] = cv.fillna(False)
#|
#|        if np.isfinite(dtw_thr) and dtw_thr > 0:
#|            cd = out.loc[mask_d, "ews_dtw_mean_7d"] >= dtw_thr
#|        else:
#|            cd = pd.Series(False, index=out.index[mask_d])
#|        dtw_thr_base = out.loc[mask_d, "dtw_base_mean"] + k_sigma * out.loc[mask_d, "dtw_base_std"].fillna(0.0)
#|        cd = cd & out.loc[mask_d, "dtw_base_mean"].notna() & (out.loc[mask_d, "ews_dtw_mean_7d"] >= dtw_thr_base)
#|        cond_dtw.loc[mask_d] = cd.fillna(False)
#|
#|        if np.isfinite(hs_thr) and hs_thr > 0:
#|            ch = out.loc[mask_d, "ews_hs_mean_7d"] >= hs_thr
#|        else:
#|            ch = pd.Series(False, index=out.index[mask_d])
#|        hs_thr_base = out.loc[mask_d, "hs_base_mean"] + k_sigma * out.loc[mask_d, "hs_base_std"].fillna(0.0)
#|        ch = ch & out.loc[mask_d, "hs_base_mean"].notna() & (out.loc[mask_d, "ews_hs_mean_7d"] >= hs_thr_base)
#|        cond_hs.loc[mask_d] = ch.fillna(False)
#|
#|    out["cond_var"] = cond_var.astype(bool)
#|    out["cond_evt"] = cond_evt.astype(bool)
#|    out["cond_dtw"] = cond_dtw.astype(bool)
#|    out["cond_hs"] = cond_hs.astype(bool)
#|
#|    # 패널-날짜별로 high 신호 개수 계산 (4개 중 2개 이상)
#|    signal_count = (
#|        cond_var.astype(int)
#|        + cond_evt.astype(int)
#|        + cond_dtw.astype(int)
#|        + cond_hs.astype(int)
#|    )
#|    out["signal_count"] = signal_count.astype(int)
#|
#|    # data_bad가 아니고, high 신호가 2개 이상인 날을 "잠정 전조 신호"로 본다.
#|    pre_ews = (~out["data_bad"]) & (signal_count >= 2)
#|    out["pre_ews"] = pre_ews.astype(bool)
#|
#|    # 4) 연속성 조건: 같은 패널에서 5일 이상 연속 pre_ews가 유지되면 EWS 경고로 확정 (방안 C)
#|    out["ews_runlen"] = compute_run_streak(out["panel_id"], pre_ews)
#|
#|    out["ews_warning"] = False
#|    out.loc[pre_ews & (out["ews_runlen"] >= 5), "ews_warning"] = True
#|
#|    # 이미 고장 확정(final_fault)인 날은 EWS 경고는 별도로 끈다
#|    out.loc[out["final_fault"], "ews_warning"] = False
#|    return out
#|
#|
#|def _compute_site_events(out: pd.DataFrame) -> pd.DataFrame:
#|    # ===== Site event day (soft/hard) + reason =====
#|    # Goal: protect ops from site-wide irradiance/weather/comm events.
#|    # Uses only per-day aggregates available in `out`.
#|    def _site_event_reason_for_day(g: pd.DataFrame) -> tuple[bool, bool, str]:
#|        reasons = []
#|
#|        # 1) peer energy collapse proxy (mid_peer very low)
#|        mid_peer_med = float(np.nanmedian(g["mid_peer"].to_numpy())) if len(g) else np.nan
#|        if np.isfinite(mid_peer_med) and mid_peer_med < 0.35:
#|            reasons.append("peer_peak_low")
#|
#|        # 2) widespread low concurrence proxy
#|        co_med = float(np.nanmedian(g["co_drop_frac"].fillna(0.0).to_numpy())) if len(g) else 0.0
#|        if np.isfinite(co_med) and co_med >= 0.45:
#|            reasons.append("co_drop_surge")
#|
#|        # 3) degraded surge
#|        deg_frac = float(np.mean(g["degraded_candidate"].fillna(False).to_numpy(dtype=bool))) if len(g) else 0.0
#|        if deg_frac >= 0.35:
#|            reasons.append("degraded_ratio_surge")
#|
#|        # 4) shadow-like surge
#|        sh_frac = float(np.mean(g["shadow_like"].fillna(False).to_numpy(dtype=bool))) if len(g) else 0.0
#|        if sh_frac >= 0.35:
#|            reasons.append("shadow_like_surge")
#|
#|        soft = len(reasons) > 0
#|
#|        # hard condition: peer collapse OR extreme concurrence OR extreme surge
#|        hard = False
#|        if ("peer_peak_low" in reasons) or (co_med >= 0.60) or (deg_frac >= 0.60):
#|            hard = True
#|
#|        return soft, hard, ";".join(reasons)
#|
#|    # compute day-wise flags (pandas groupby.apply FutureWarning-safe)
#|    def _day_flags_apply(df: pd.DataFrame) -> pd.DataFrame:
#|        try:
#|            # pandas newer versions
#|            return df.groupby("date", group_keys=False).apply(
#|                lambda g: pd.Series(
#|                    _site_event_reason_for_day(g),
#|                    index=["site_event_soft", "site_event_hard", "site_event_reason"],
#|                ),
#|                include_groups=False,
#|            )
#|        except TypeError:
#|            # pandas older versions (no include_groups)
#|            return df.groupby("date", group_keys=False).apply(
#|                lambda g: pd.Series(
#|                    _site_event_reason_for_day(g),
#|                    index=["site_event_soft", "site_event_hard", "site_event_reason"],
#|                )
#|            )
#|
#|    day_flags = _day_flags_apply(out)
#|    out = out.merge(day_flags, left_on="date", right_index=True, how="left")
#|    out["site_event_soft"] = out["site_event_soft"].fillna(False).astype(bool)
#|    out["site_event_hard"] = out["site_event_hard"].fillna(False).astype(bool)
#|    out["site_event_reason"] = out["site_event_reason"].fillna("").astype(str)
#|    return out
#|
#|
#|def main():
#|    args = parse_args()
#|
#|    # ---- Reproducibility ----
#|    seed = int(getattr(args, "seed", 42))
#|    np.random.seed(seed)
#|    try:
#|        import random
#|        random.seed(seed)
#|    except Exception:
#|        pass
#|    try:
#|        torch.manual_seed(seed)
#|        if torch.cuda.is_available():
#|            torch.cuda.manual_seed_all(seed)
#|        # Best-effort determinism (may have perf impact)
#|        torch.backends.cudnn.deterministic = True
#|        torch.backends.cudnn.benchmark = False
#|    except Exception:
#|        pass
#|
#|    data_dir, out_dir, log_dir, site, train_files, eval_files = _setup_paths(args, seed)
#|
#|    peer_mode = str(getattr(args, "peer_mode", "median")).strip().lower()
#|    peer_quantile = float(getattr(args, "peer_quantile", 0.80))
#|    peer_ref_panel = str(getattr(args, "peer_ref_panel", "")).strip()
#|    pmax_info_csv = str(getattr(args, "pmax_info_csv", "")).strip()
#|    if not np.isfinite(peer_quantile):
#|        raise RuntimeError(f"invalid --peer-quantile: {peer_quantile}")
#|    if peer_quantile < 0.0 or peer_quantile > 1.0:
#|        raise RuntimeError(f"--peer-quantile must be in [0,1], got {peer_quantile}")
#|
#|    panel_pmax_map: Dict[str, float] = {}
#|    panel_ids_seen: List[str] = []
#|    if pmax_info_csv or peer_mode == "ref":
#|        panel_ids_seen = _collect_panel_ids_from_files(train_files + eval_files)
#|        if peer_mode == "ref":
#|            if not peer_ref_panel:
#|                raise RuntimeError("--peer-mode ref requires --peer-ref-panel <panel_id>")
#|            if peer_ref_panel not in set(panel_ids_seen):
#|                raise RuntimeError(f"--peer-ref-panel not found in train/eval period: {peer_ref_panel}")
#|        if pmax_info_csv:
#|            panel_pmax_map = _build_panel_pmax_map_for_panels(pmax_info_csv, panel_ids_seen)
#|            print(f"[INFO] Pmax normalization enabled: mapped {len(panel_pmax_map)} panels from {pmax_info_csv}")
#|
#|    # ===== Build train-only voltage-bin map (vbin) for stable group references =====
#|    # This prevents mixed-string designs from inflating v_ref_span and forcing legacy critical.
#|    vbin_map: dict[str, int] = {}
#|    vbin_diag: dict[str, any] = {}
#|    try:
#|        vbin_map, vbin_diag = build_vbin_map_from_train(
#|            train_files=train_files,
#|            critical_peer_min=float(args.critical_peer_min),
#|            mid_peer_alive_thr=float(args.mid_peer_alive_thr),
#|            mid_ratio_dead_thr=float(args.mid_ratio_dead_thr),
#|            coverage_min=float(args.coverage_min),
#|            panel_pmax_map=panel_pmax_map,
#|            peer_mode=peer_mode,
#|            peer_quantile=peer_quantile,
#|            peer_ref_panel=peer_ref_panel,
#|        )
#|        # Persist for reproducibility
#|        (log_dir / "vbin_map.json").write_text(
#|            json.dumps(vbin_map, ensure_ascii=False, indent=2), encoding="utf-8"
#|        )
#|        (log_dir / "vbin_diag.json").write_text(
#|            json.dumps(vbin_diag, ensure_ascii=False, indent=2), encoding="utf-8"
#|        )
#|        print(f"[OK] wrote vbin_map.json (n={len(vbin_map)}) and vbin_diag.json")
#|    except Exception as e:
#|        print(f"[WARN] failed to build vbin_map (will run without vbin split): {e}")
#|        vbin_map = {}
#|
#|    # ===== AE 학습 (정상 기간) =====
#|    X_train: List[np.ndarray] = []
#|    train_index: List[Tuple[str, str]] = []
#|    train_curves_by_pid: Dict[str, List[np.ndarray]] = {}
#|
#|    for p in tqdm(train_files, desc="train-curves"):
#|        curves = load_day_curves(
#|            p,
#|            peer_eps=float(args.peer_eps),
#|            use_log_ratio=bool(args.use_log_ratio),
#|            panel_pmax_map=panel_pmax_map,
#|            peer_mode=peer_mode,
#|            peer_quantile=peer_quantile,
#|            peer_ref_panel=peer_ref_panel,
#|        )
#|        fname = p.name
#|        for pid, curve in curves.items():
#|            X_train.append(curve)
#|            train_index.append((fname, pid))
#|            train_curves_by_pid.setdefault(pid, []).append(curve)
#|
#|    if not X_train:
#|        raise RuntimeError("no training curves")
#|
#|    X_train_mat = np.vstack(X_train)
#|    # Compute global and per-panel reference curves
#|    global_ref_curve = np.median(X_train_mat, axis=0)
#|    panel_ref: Dict[str, np.ndarray] = {}
#|    for pid, lst in train_curves_by_pid.items():
#|        panel_ref[pid] = np.median(np.vstack(lst), axis=0)
#|
#|    device = args.device
#|
#|    model, train_err = train_ae(X_train_mat, args.latent, args.epochs, device)
#|    ae_thr_ae = float(np.quantile(train_err, 1.0 - args.contam))
#|
#|    # ===== 평가 (고장 후보 기간) =====
#|    rows = []
#|    with torch.no_grad():
#|        for p in tqdm(eval_files, desc="eval"):
#|            csv_path = p
#|            fname = p.name
#|
#|            # 이벤트 feature 계산
#|            ev_map = compute_event_features(
#|                csv_path,
#|                drop_thr=args.drop_thr,
#|                sustain_thr=args.sustain_thr,
#|                recovered_consec=int(args.recovered_consec),
#|                recovered_sustain_mins=int(args.recovered_sustain_mins),
#|                co_drop_thr=float(args.shadow_co_drop_thr),
#|                daylight_event_thr=float(getattr(args, "daylight_event_thr", 0.2)),
#|                peer_eps=float(args.peer_eps),
#|                panel_pmax_map=panel_pmax_map,
#|                peer_mode=peer_mode,
#|                peer_quantile=peer_quantile,
#|                peer_ref_panel=peer_ref_panel,
#|            )
#|
#|            curves = load_day_curves(
#|                csv_path,
#|                peer_eps=float(args.peer_eps),
#|                use_log_ratio=bool(args.use_log_ratio),
#|                panel_pmax_map=panel_pmax_map,
#|                peer_mode=peer_mode,
#|                peer_quantile=peer_quantile,
#|                peer_ref_panel=peer_ref_panel,
#|            )
#|            for pid, curve in curves.items():
#|                x = torch.tensor(curve[None, :], dtype=torch.float32).to(device)
#|                rec = model(x).cpu().numpy()[0]
#|                recon_err = float(np.mean((curve - rec) ** 2))
#|
#|                ev = ev_map.get(str(pid), {})
#|                ev_vals = _extract_event_values(ev)
#|
#|                is_ae_abn = recon_err >= ae_thr_ae
#|                is_ae_strong = recon_err >= (args.recon_mult * ae_thr_ae)
#|
#|                # --- DTW & HS ---
#|                ref_curve = panel_ref.get(pid, global_ref_curve)
#|                band = int(args.dtw_band)
#|                dtw = float(dtw_distance(curve, ref_curve, band=None if band <= 0 else band))
#|                hs = float(compute_hs(curve))
#|
#|                # --- V-drop reference & labels are computed AFTER dataframe-level v_ref merge ---
#|
#|                # (Remove per-row cache to avoid duplicate computation / label overwrite.)
#|
#|                group_key = panel_group_key(pid)
#|
#|                vbin = vbin_map.get(pid, 0)
#|
#|                group_key_ref = f"{group_key}.v{vbin}"
#|
#|
#|                # Placeholders (computed post-merge)
#|                v_ref = np.nan
#|                v_ref_span = np.nan
#|                n_ref = np.nan
#|                n_total = np.nan
#|                v_ref_ok = False
#|                v_drop = np.nan
#|
#|
#|                # Assemble output row with required fields
#|                rows.append(
#|                    {
#|                        "date": extract_date_from_filename(fname),
#|                        "panel_id": str(pid),
#|                        "v_ref_ok": v_ref_ok,
#|                        "v_drop": v_drop,
#|                        "v_ref": v_ref,
#|                        "v_ref_span": v_ref_span,
#|                        "n_ref": n_ref,
#|                        "n_total": n_total,
#|                        "group_key_ref": group_key_ref,
#|                        "recon_error": recon_err,
#|                        "ae_thr_used": ae_thr_ae,
#|                        "drop_time": ev_vals["drop_time"],
#|                        "sustain_mins": ev_vals["sustain_mins"],
#|                        "recovered": ev_vals["recovered"],
#|                        "last_ratio": ev_vals["last_ratio"],
#|                        "last_peer": ev_vals["last_peer"],
#|                        "mid_ratio": ev_vals["mid_ratio"],
#|                        "mid_peer": ev_vals["mid_peer"],
#|                        "mid_v_ratio": ev_vals["mid_v_ratio"],
#|                        "mid_i_ratio": ev_vals["mid_i_ratio"],
#|                        "coverage": ev_vals["coverage"],
#|                        "co_drop_frac": ev_vals["co_drop_frac"],
#|                        "is_ae_abn": bool(is_ae_abn),
#|                        "is_ae_strong": bool(is_ae_strong),
#|                        "source_csv": fname,
#|                        "dtw_dist": dtw,
#|                        "hs_score": hs,
#|                        "recovered_any": ev_vals["recovered_any"],
#|                        "recovered_sustained": ev_vals["recovered_sustained"],
#|                        "re_drop": ev_vals["re_drop"],
#|                        "coverage_mid": ev_vals["coverage_mid"],
#|                        "seg_count": ev_vals["seg_count"],
#|                        "total_low_mins": ev_vals["total_low_mins"],
#|                        "min_ratio": ev_vals["min_ratio"],
#|                        "p10_ratio": ev_vals["p10_ratio"],
#|                        "p50_ratio": ev_vals["p50_ratio"],
#|                        "low_area": ev_vals["low_area"],
#|                    }
#|                )
#|
#|    out = pd.DataFrame(rows)
#|    # Normalize date to midnight to avoid merge key mismatches
#|    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
#|    out["drop_time"] = pd.to_datetime(out["drop_time"], errors="coerce")
#|
#|    cov_min = float(args.coverage_min)
#|    tuning_level = str(getattr(args, "tuning_level", "p2")).lower().strip()
#|    if tuning_level not in {"p0", "p1", "p2"}:
#|        tuning_level = "p2"
#|    print(f"[INFO] tuning_level = {tuning_level}")
#|    print(f"[INFO] daylight_event_thr = {float(getattr(args, 'daylight_event_thr', 0.2))}")
#|    print("[INFO] segment-labeling: confirmed_fault/critical_fault now mark whole sustained segments (not only tail days)")
#|
#|    # rule-based flags
#|    out["event_A"] = out["drop_time"].notna() & (out["sustain_mins"] >= int(args.event_sustain_mins))
#|    out["data_bad"] = (out["coverage"] < cov_min) | (out["coverage_mid"].fillna(0.0) < cov_min)
#|
#|    # ---- Group-aware V reference and relative V-drop (for critical_like) ----
#|    # Goal: derive a per-(date, group_key) voltage reference from good rows, then compute
#|    #       v_drop = 1 - (mid_v_ratio / v_ref).
#|    # Key requirement: NEVER crash when v_ref is unavailable. Always keep `v_ref` column.
#|
#|    # Base group_key (string-like) from panel_id
#|    out["group_key_base"] = out["panel_id"].astype(str).map(panel_group_key)
#|
#|    # vbin-aware group_key: split base group when train-only medians show mixed voltage levels.
#|    # IMPORTANT: vbin is fixed from TRAIN only to avoid leakage and day-to-day instability.
#|    if isinstance(vbin_map, dict) and len(vbin_map) > 0:
#|        vb = out["panel_id"].astype(str).map(lambda s: vbin_map.get(str(s), 0)).astype(int)
#|        out["vbin"] = vb
#|        out["group_key"] = out["group_key_base"].astype(str) + ".v" + vb.astype(str)
#|    else:
#|        out["vbin"] = 0
#|        out["group_key"] = out["group_key_base"].astype(str)
#|
#|    # A안 적용: v_ref(전압 참조)는 vbin까지 포함한 group_key 단위로 계산한다.
#|    # 이유: base group_key_ref(=uuid.string) 안에 서로 다른 설계/MPPT 전압 스트링이 섞이면
#|    #       v_ref_span이 폭발하고 v_ref_ok가 막혀 v_drop 판정이 불안정해진다.
#|    # 따라서 v_ref를 (date, group_key=vbin 포함) 기준으로 산출/적용하여 혼선을 제거한다.
#|    out["group_key_ref"] = out["group_key"].astype(str)
#|
#|    # Ensure n_total is always available for downstream v_ref_ok logic and for CSV outputs.
#|    # n_total = number of unique panels per (date, group_key). Always recompute from the raw rows
#|    # so it is never missing even when v_ref is unavailable.
#|    out["n_total"] = out.groupby(["date", "group_key"])["panel_id"].transform("nunique").astype(float)
#|
#|    # If this script is re-run in an interactive environment, or if the dataframe is
#|    # processed twice by accident, prior merge artifacts can remain and cause pandas
#|    # suffixes (_x/_y), which then breaks downstream v_ref_span selection and can leave
#|    # v_drop as all-NaN. Clean them up before recomputing.
#|    _merge_artifact_cols = [
#|        c for c in out.columns
#|        if (
#|            c.startswith("v_ref_tmp")
#|            or c.startswith("v_p10_grp")
#|            or c.startswith("v_p90_grp")
#|            or c.startswith("v_ref_span_grp")
#|        )
#|    ]
#|    if _merge_artifact_cols:
#|        out = out.drop(columns=_merge_artifact_cols)
#|
#|    # Always materialize columns up-front to avoid KeyError in any branch.
#|    # IMPORTANT: v_ref/v_drop must preserve NaN when unusable.
#|    # Setting v_drop=0.0 on missing v_ref hides data-quality issues and can cause unintended fallback behaviour.
#|    out["v_ref"] = pd.to_numeric(out.get("v_ref", np.nan), errors="coerce")
#|    out["v_drop"] = np.nan
#|    out["v_ref_span"] = np.nan  # group-level span only (avoid merge collisions)
#|    out["n_ref"] = np.nan
#|    out["no_ref"] = False
#|
#|    # Convenience flag: whether v_ref is usable for v_drop evaluation.
#|    # NOTE: v_ref_ok MUST be recomputed after v_ref is derived (merge step below).
#|    out["v_ref_ok"] = out["v_ref"].notna() & (out["v_ref"] >= float(args.v_ref_min))
#|
#|    if tuning_level == "p2":
#|        # For building v_ref only, we must not over-gate by mid_peer.
#|        # Gangui finding: clear-day mid_peer can sit around ~0.4 depending on daylight/mid-window definition.
#|        # Use a slightly more permissive peer threshold ONLY for v_ref computation (no leakage; still uses eval-day rows).
#|        vref_peer_min = min(float(args.mid_peer_alive_thr), 0.35)
#|        # Exclude near-dead/off panels from V reference computation.
#|        # Otherwise a panel/string OFF event can leak into v_ref and distort v_drop.
#|        dead_like_tmp = (
#|            (~out["data_bad"].astype(bool))
#|            & (out["mid_peer"] >= float(vref_peer_min))
#|            & (out["mid_ratio"] <= float(args.mid_ratio_dead_thr))
#|        )
#|
#|        base_mask = (
#|            (~out["data_bad"].astype(bool))
#|            & (out["mid_peer"] >= float(vref_peer_min))
#|            & (np.isfinite(out["mid_v_ratio"]))
#|            & (~dead_like_tmp)
#|        )
#|
#|        if base_mask.any():
#|            # Robust healthy-cluster v_ref: use upper cluster to avoid low-V contamination
#|            def _vref_robust_stats(x: pd.Series) -> pd.Series:
#|                xx = pd.to_numeric(x, errors="coerce").astype(float)
#|                xx = xx[np.isfinite(xx)]
#|                if len(xx) == 0:
#|                    return pd.Series({"v_ref_tmp": np.nan, "v_p10_grp": np.nan, "v_p90_grp": np.nan, "n_ref": 0})
#|
#|                # Use the upper cluster as the reference (protect against low-V fault contamination)
#|                # Keep it simple and deterministic: filter by an upper quantile then take median.
#|                q = float(np.nanquantile(xx, 0.60))
#|                xh = xx[xx >= q]
#|                if len(xh) < 2:
#|                    xh = xx  # fallback when too few remain
#|
#|                return pd.Series({
#|                    "v_ref_tmp": float(np.nanmedian(xh)),
#|                    "v_p10_grp": float(np.nanquantile(xh, 0.10)) if len(xh) > 0 else np.nan,
#|                    "v_p90_grp": float(np.nanquantile(xh, 0.90)) if len(xh) > 0 else np.nan,
#|                    "n_ref": int(len(xh)),
#|                })
#|
#|            # NOTE: pandas groupby.apply with `as_index=False` can produce length/index
#|            # mismatches when the applied function returns a Series. Use groupby.apply
#|            # (without as_index=False) and reset_index safely.
#|            v_ref_tbl = (
#|                out.loc[base_mask]
#|                .groupby(["date", "group_key_ref"])
#|                .apply(lambda g: _vref_robust_stats(g["mid_v_ratio"]))
#|                .reset_index()
#|            )
#|            v_ref_tbl["v_ref_span_grp"] = v_ref_tbl["v_p90_grp"] - v_ref_tbl["v_p10_grp"]
#|            # dtype guards (avoid object columns after apply)
#|            for c in ["v_ref_tmp", "v_p10_grp", "v_p90_grp", "v_ref_span_grp", "n_ref"]:
#|                if c in v_ref_tbl.columns:
#|                    v_ref_tbl[c] = pd.to_numeric(v_ref_tbl[c], errors="coerce")
#|
#|            # Normalize date for safe merge (guard against time components)
#|            v_ref_tbl["date"] = pd.to_datetime(v_ref_tbl["date"], errors="coerce").dt.normalize()
#|
#|            # Persist v_ref table for debugging/ops visibility
#|            try:
#|                v_ref_tbl.to_csv(log_dir / "v_ref_tbl.csv", index=False)
#|                print(f"[OK] wrote v_ref_tbl.csv (n={len(v_ref_tbl)})")
#|                print("[DBG] v_ref_tbl rows by date (top 10):")
#|                print(v_ref_tbl.groupby(v_ref_tbl["date"].dt.date).size().sort_values(ascending=False).head(10).to_string())
#|            except Exception as e:
#|                print(f"[WARN] failed to write v_ref_tbl.csv: {e}")
#|
#|            # Merge with a TEMP column name to avoid pandas suffix traps.
#|            if len(v_ref_tbl) > 0:
#|                # Extra guard: normalize out["date"] before merge (in case other code paths modified it)
#|                out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
#|                out = out.merge(v_ref_tbl, on=["date", "group_key_ref"], how="left")
#|
#|                # Recover v_ref_tmp even if pandas added suffixes.
#|                if "v_ref_tmp" not in out.columns:
#|                    for cand in ["v_ref_tmp_y", "v_ref_tmp_x"]:
#|                        if cand in out.columns:
#|                            out["v_ref_tmp"] = out[cand]
#|                            break
#|
#|                # Choose the best available span column by non-null count.
#|                span_candidates = [c for c in out.columns if c.startswith("v_ref_span_grp")]
#|                span_col = None
#|                if span_candidates:
#|                    nn = {c: int(pd.to_numeric(out[c], errors="coerce").notna().sum()) for c in span_candidates}
#|                    span_col = max(nn, key=nn.get)
#|
#|                # Capture n_ref column name (may be suffixed after merges)
#|                nref_col = None
#|                for cand in ["n_ref", "n_ref_y", "n_ref_x"]:
#|                    if cand in out.columns:
#|                        nref_col = cand
#|                        break
#|
#|                if "v_ref_tmp" in out.columns:
#|                    # Stable, non-suffixed outputs
#|                    out["v_ref"] = pd.to_numeric(out["v_ref_tmp"], errors="coerce")
#|                    out["n_ref"] = pd.to_numeric(out[nref_col], errors="coerce") if nref_col is not None else np.nan
#|                    # Keep n_total stable: recompute from rows (do not trust merge artifacts).
#|                    out["n_total"] = out.groupby(["date", "group_key"])["panel_id"].transform("nunique").astype(float)
#|
#|                    if span_col is not None:
#|                        out["v_ref_span"] = pd.to_numeric(out[span_col], errors="coerce")
#|                    else:
#|                        out["v_ref_span"] = np.nan
#|
#|                    # v_ref_ok: usable v_ref AND stable group span AND enough reference panels
#|                    v_ref_min_n = int(getattr(args, "v_ref_min_n", 6))
#|                    span_ok = out["v_ref_span"].notna() & (out["v_ref_span"] <= float(args.v_ref_vspan_max))
#|
#|                    # Adaptive min-N based on reference-bin availability within (date, group_key_ref)
#|                    # (i.e., how many v1 panels exist to form a stable voltage reference).
#|                    v_ref_min_n = int(getattr(args, "v_ref_min_n", 6))
#|                    required_n = out["n_total"].apply(lambda x: max(2, min(v_ref_min_n, int(x))) if pd.notna(x) else v_ref_min_n)
#|                    n_ok = out["n_ref"].notna() & (out["n_ref"] >= required_n)
#|                    out["v_ref_ok"] = out["v_ref"].notna() & (out["v_ref"] >= float(args.v_ref_min)) & span_ok & n_ok
#|
#|                    # no_ref: reference not available or too small (ops visibility)
#|                    out["no_ref"] = out["v_ref"].isna() | (~n_ok)
#|
#|                    # Drop merge helper columns (including any suffixed variants)
#|                    drop_cols = []
#|                    for c in [
#|                        "v_ref_tmp", "v_ref_tmp_x", "v_ref_tmp_y",
#|                        "v_p10_grp", "v_p10_grp_x", "v_p10_grp_y",
#|                        "v_p90_grp", "v_p90_grp_x", "v_p90_grp_y",
#|                        "n_ref_x", "n_ref_y",
#|                        "v_ref_span_grp", "v_ref_span_grp_x", "v_ref_span_grp_y",
#|                    ]:
#|                        # Keep stable output columns `n_ref` and `n_total`; drop only temporary/suffixed merge helpers.
#|                        if c in out.columns and c not in {"n_ref", "n_total"}:
#|                            drop_cols.append(c)
#|                    if drop_cols:
#|                        out = out.drop(columns=drop_cols)
#|
#|                    # Compute relative V-drop using group reference.
#|                    # Keep NaN when v_ref is missing/unusable; do NOT default to 0.0.
#|                    out["v_drop"] = np.nan
#|
#|                    # Ensure numeric dtypes (avoid silent all-False masks when objects sneak in)
#|                    out["mid_v_ratio"] = pd.to_numeric(out["mid_v_ratio"], errors="coerce")
#|                    out["v_ref"] = pd.to_numeric(out["v_ref"], errors="coerce")
#|
#|                    drop_mask = (
#|                        out["v_ref"].notna()
#|                        & out["mid_v_ratio"].notna()
#|                        & np.isfinite(out["mid_v_ratio"].to_numpy(dtype=float))
#|                        & np.isfinite(out["v_ref"].to_numpy(dtype=float))
#|                        & (out["v_ref"] > 0)
#|                    )
#|                    out.loc[drop_mask, "v_drop"] = 1.0 - (
#|                        out.loc[drop_mask, "mid_v_ratio"].astype(float)
#|                        / out.loc[drop_mask, "v_ref"].astype(float)
#|                    )
#|                    # Safety: n_total must never be missing.
#|                    out["n_total"] = out.groupby(["date", "group_key"])["panel_id"].transform("nunique").astype(float)
#|
#|    out["state_dead"] = (
#|        (~out["data_bad"])
#|        & (out["mid_peer"] >= float(args.mid_peer_alive_thr))
#|        & (out["mid_ratio"] <= float(args.mid_ratio_dead_thr))
#|    )
#|
#|    # ---- Stage gating (p0/p1/p2) ----
#|    # p0: dead/confirmed only (no group_off gate, no critical/shadow/EWS)
#|    # p1: +group_off_like gate (still no critical/shadow/EWS)
#|    # p2: full (critical_like + group_off_like + downstream refinement)
#|
#|    # ---- Ops visibility: why a row is low-trust (suspect) ----
#|    # Derived from FINAL (post-merge) trust-gate components.
#|    if "vdrop_trust_reason" not in out.columns:
#|        out["vdrop_trust_reason"] = ""
#|
#|    try:
#|        v_ref_min_n = int(getattr(args, "v_ref_min_n", 6))
#|        v_ref_min = float(getattr(args, "v_ref_min", 0.30))
#|        v_ref_vspan_max = float(getattr(args, "v_ref_vspan_max", 0.12))
#|
#|        n_ref_s = pd.to_numeric(out.get("n_ref", np.nan), errors="coerce")
#|        v_ref_s = pd.to_numeric(out.get("v_ref", np.nan), errors="coerce")
#|        vspan_s = pd.to_numeric(out.get("v_ref_span", np.nan), errors="coerce")
#|
#|        # Match the adaptive required_n logic used in v_ref_ok computation.
#|        required_n = n_ref_s.apply(
#|            lambda x: (max(2, min(v_ref_min_n, int(x))) if pd.notna(x) else v_ref_min_n)
#|        )
#|
#|        low_vref = v_ref_s.isna() | (~np.isfinite(v_ref_s.to_numpy(dtype=float))) | (v_ref_s < v_ref_min)
#|        high_vspan = vspan_s.isna() | (~np.isfinite(vspan_s.to_numpy(dtype=float))) | (vspan_s > v_ref_vspan_max)
#|        low_nref = n_ref_s.isna() | (~np.isfinite(n_ref_s.to_numpy(dtype=float))) | (n_ref_s < required_n)
#|
#|        # Build reason strings (order-stable)
#|        r = np.where(low_vref, "low_v_ref", "")
#|        r = np.where(high_vspan, np.where(r != "", r + "+high_vspan", "high_vspan"), r)
#|        r = np.where(low_nref, np.where(r != "", r + "+low_n_ref", "low_n_ref"), r)
#|
#|        # Only keep reason when FINAL trust is low (suspect); else keep blank.
#|        out["vdrop_trust_reason"] = np.where(out["v_ref_ok"].fillna(False).astype(bool), "", r)
#|    except Exception as _e:
#|        # Never fail the pipeline due to a diagnostics column.
#|        out["vdrop_trust_reason"] = ""
#|
#|    # critical labels are finalized after group_off_like is known.
#|
#|    out["group_off_date"] = False
#|    out["group_off_like"] = False
#|    out["group_off_group"] = False
#|
#|    if tuning_level in {"p1", "p2"}:
#|        out = _detect_group_off(out, args)
#|
#|    # Effective dead for panel-fault confirmation
#|    # p0: no group_off gating
#|    # p1/p2: exclude group_off_like days
#|    if tuning_level == "p0":
#|        out["state_dead_eff"] = out["state_dead"].astype(bool)
#|    else:
#|        out["state_dead_eff"] = out["state_dead"].astype(bool) & (~out["group_off_like"].astype(bool))
#|
#|    # Final critical labels (SSOT): define once after group_off_like is known.
#|    out = compute_vdrop_labels(
#|        out,
#|        {
#|            "args": args,
#|            "tuning_level": tuning_level,
#|        },
#|    )
#|
#|    # dead streak and confirmed fault (always computed)
#|    out = out.sort_values(["panel_id", "date"])
#|    out["dead_streak"] = compute_run_streak(out["panel_id"], out["state_dead_eff"])
#|    # Mark whole dead-like segments when they reach the minimum length (ops-friendly)
#|    out = mark_run_segments(out, key_col="panel_id", date_col="date", cond_col="state_dead_eff", min_len=int(args.dead_days), out_col="confirmed_fault")
#|
#|    # ---- Critical-like (V-drop sustained run) ----
#|    out["crit_streak"] = 0
#|    out["critical_fault"] = False
#|
#|    if tuning_level == "p2":
#|        # ---- Critical-like streak ----
#|        out["crit_streak"] = compute_run_streak(out["panel_id"], out["critical_like_eff"])
#|        # Mark whole critical-like segments when they reach the minimum length (ops-friendly)
#|        out = mark_run_segments(out, key_col="panel_id", date_col="date", cond_col="critical_like_eff", min_len=int(args.critical_days), out_col="critical_fault")
#|
#|    # ===== critical 2-stage split (confirmed vs suspect) =====
#|    # Compute after `critical_fault` is available.
#|    out["critical_confirmed"] = False
#|    out["critical_suspect"] = False
#|    # Ops-friendly stage label (none/like/suspect/confirmed)
#|    out["critical_stage"] = "none"
#|
#|    if tuning_level == "p2":
#|        critical_fault_mask = out["critical_fault"].fillna(False).astype(bool)
#|        crit_rows = out[critical_fault_mask & (out["mid_peer"] >= float(args.critical_peer_min))].copy()
#|        if len(crit_rows) > 0:
#|            g = (crit_rows.groupby("panel_id")
#|                         .agg(days=("date", "nunique"),
#|                              v_p10=("mid_v_ratio", lambda x: x.quantile(0.10)),
#|                              v_p90=("mid_v_ratio", lambda x: x.quantile(0.90)))
#|                         .reset_index())
#|            g["v_span"] = g["v_p90"] - g["v_p10"]
#|
#|            confirmed_panels = set(
#|                g[(g["days"] >= int(args.critical_min_days)) & (g["v_span"] <= float(args.critical_vspan_max))]["panel_id"].astype(str).tolist()
#|            )
#|            suspect_panels = set(
#|                g[(g["days"] >= int(args.critical_min_days)) & (g["v_span"] > float(args.critical_vspan_max))]["panel_id"].astype(str).tolist()
#|            )
#|
#|            out.loc[out["panel_id"].astype(str).isin(confirmed_panels) & critical_fault_mask, "critical_confirmed"] = True
#|            out.loc[out["panel_id"].astype(str).isin(suspect_panels) & critical_fault_mask, "critical_suspect"] = True
#|            # Stage labeling priority: confirmed > suspect > like
#|            out.loc[out["critical_like_eff"].astype(bool), "critical_stage"] = "like"
#|            out.loc[out["critical_suspect"].astype(bool), "critical_stage"] = "suspect"
#|            out.loc[out["critical_confirmed"].astype(bool), "critical_stage"] = "confirmed"
#|
#|    # final_fault
#|    if tuning_level == "p2":
#|        # Final fault should only use CONFIRMED critical (V/I-decomposed and stability-checked).
#|        # Anything else stays as critical_like / critical_suspect for downstream review.
#|        out["final_fault"] = out["confirmed_fault"] | out["critical_confirmed"]
#|    else:
#|        out["final_fault"] = out["confirmed_fault"]
#|
#|    # ---- Online diagnosis dates (panel-wise first confirmed day) ----
#|    # Keep date normalization explicit before first-true day extraction.
#|    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
#|
#|    dead_days_thr = int(args.dead_days)
#|    critical_days_thr = int(args.critical_days)
#|
#|    out["dead_diag_on_day"] = (
#|        out["state_dead_eff"].fillna(False).astype(bool)
#|        & (pd.to_numeric(out["dead_streak"], errors="coerce").fillna(0) >= dead_days_thr)
#|    )
#|    dead_diag_first = (
#|        out.loc[out["dead_diag_on_day"], ["panel_id", "date"]]
#|        .groupby("panel_id", sort=False)["date"]
#|        .min()
#|    )
#|    out["dead_diag_date"] = out["panel_id"].map(dead_diag_first)
#|
#|    if tuning_level == "p2":
#|        out["critical_diag_on_day"] = (
#|            out["critical_like_eff"].fillna(False).astype(bool)
#|            & (pd.to_numeric(out["crit_streak"], errors="coerce").fillna(0) >= critical_days_thr)
#|        )
#|        critical_diag_first = (
#|            out.loc[out["critical_diag_on_day"], ["panel_id", "date"]]
#|            .groupby("panel_id", sort=False)["date"]
#|            .min()
#|        )
#|        out["critical_diag_date"] = out["panel_id"].map(critical_diag_first)
#|    else:
#|        out["critical_diag_on_day"] = False
#|        out["critical_diag_date"] = pd.NaT
#|        critical_diag_first = pd.Series(dtype="datetime64[ns]")
#|
#|    out["diagnosis_date_online"] = pd.concat(
#|        [
#|            pd.to_datetime(out["dead_diag_date"], errors="coerce"),
#|            pd.to_datetime(out["critical_diag_date"], errors="coerce"),
#|        ],
#|        axis=1,
#|    ).min(axis=1)
#|
#|    final_fault_first = (
#|        out.loc[out["final_fault"].fillna(False).astype(bool), ["panel_id", "date"]]
#|        .groupby("panel_id", sort=False)["date"]
#|        .min()
#|    )
#|    panel_diag = pd.DataFrame({"panel_id": out["panel_id"].astype(str).drop_duplicates()})
#|    panel_diag["dead_diag_date"] = panel_diag["panel_id"].map(dead_diag_first)
#|    panel_diag["critical_diag_date"] = panel_diag["panel_id"].map(critical_diag_first)
#|    panel_diag["diagnosis_date_online"] = pd.concat(
#|        [
#|            pd.to_datetime(panel_diag["dead_diag_date"], errors="coerce"),
#|            pd.to_datetime(panel_diag["critical_diag_date"], errors="coerce"),
#|        ],
#|        axis=1,
#|    ).min(axis=1)
#|    panel_diag["final_fault_first_date"] = panel_diag["panel_id"].map(final_fault_first)
#|    panel_diag["dead_days"] = dead_days_thr
#|    panel_diag["critical_days"] = critical_days_thr
#|    panel_diag["tuning_level"] = tuning_level
#|    panel_diag_path = out_dir / "panel_diagnosis_summary.csv"
#|    panel_diag.to_csv(panel_diag_path, index=False, encoding="utf-8-sig")
#|    print(f"[OK] wrote output: {panel_diag_path} (n={len(panel_diag)})")
#|
#|    # Sanity checks for critical label consistency after single-pass SSOT assignment.
#|    try:
#|        bad_overlap = int(
#|            (
#|                out["critical_like_raw"].astype(bool)
#|                & out["critical_like_suspect_raw"].astype(bool)
#|            ).sum()
#|        )
#|        if bad_overlap > 0:
#|            raise AssertionError(
#|                f"critical raw overlap detected (n={bad_overlap}); raw and suspect_raw must be exclusive"
#|            )
#|
#|        # Legacy path may legitimately bypass v_ref_ok; trust check applies to non-legacy rows only.
#|        leak_nonlegacy = int(
#|            (
#|                out["critical_like_eff"].astype(bool)
#|                & (~out["v_ref_ok"].fillna(False).astype(bool))
#|                & (~out["critical_like_legacy"].astype(bool))
#|            ).sum()
#|        )
#|        if leak_nonlegacy > 0:
#|            raise AssertionError(
#|                f"non-legacy critical leak detected with v_ref_ok==0 (n={leak_nonlegacy})"
#|            )
#|        print(f"[CHK] critical_raw_overlap = {bad_overlap}, nonlegacy_vref_leak = {leak_nonlegacy}")
#|    except Exception as _e:
#|        raise
#|
#|    # ---- Reports: confirmed vs suspect (after final critical labels are fixed) ----
#|    try:
#|        if tuning_level == "p2":
#|            rep_confirm = _max_run_by_panel(out, "critical_like")
#|            rep_suspect = _max_run_by_panel(out, "critical_like_suspect")
#|
#|            def _attach_ctx(df_run: pd.DataFrame, flag_col: str) -> pd.DataFrame:
#|                top_pids = df_run.loc[df_run[f"{flag_col}_max_run"] > 0, "panel_id"].astype(str).tolist()
#|                if not top_pids:
#|                    return df_run
#|                sub = out[out["panel_id"].astype(str).isin(top_pids)].copy()
#|                sub = sub.sort_values(["panel_id", "date"])
#|                ctx = (
#|                    sub.groupby("panel_id")
#|                    .tail(1)[
#|                        [
#|                            "panel_id",
#|                            "group_key_ref",
#|                            "n_ref",
#|                            "n_total",
#|                            "v_ref_span",
#|                            "mid_peer",
#|                            "mid_ratio",
#|                            "mid_v_ratio",
#|                            "v_drop",
#|                        ]
#|                    ]
#|                    .copy()
#|                )
#|                return df_run.merge(ctx, on="panel_id", how="left")
#|
#|            rep_confirm_ctx = _attach_ctx(rep_confirm, "critical_like")
#|            rep_suspect_ctx = _attach_ctx(rep_suspect, "critical_like_suspect")
#|
#|            ok_critical_reports = True
#|            ok_critical_reports &= _safe_report_write(
#|                rep_confirm_ctx,
#|                log_dir / "report_critical_confirmed_runs.csv",
#|                "report_critical_confirmed_runs(log)",
#|                index=False,
#|            )
#|            ok_critical_reports &= _safe_report_write(
#|                rep_suspect_ctx,
#|                log_dir / "report_critical_suspect_runs.csv",
#|                "report_critical_suspect_runs(log)",
#|                index=False,
#|            )
#|            ok_critical_reports &= _safe_report_write(
#|                rep_confirm_ctx,
#|                out_dir / "report_critical_confirmed_runs.csv",
#|                "report_critical_confirmed_runs(out)",
#|                index=False,
#|            )
#|            ok_critical_reports &= _safe_report_write(
#|                rep_suspect_ctx,
#|                out_dir / "report_critical_suspect_runs.csv",
#|                "report_critical_suspect_runs(out)",
#|                index=False,
#|            )
#|            if ok_critical_reports:
#|                print("[OK] wrote reports: report_critical_confirmed_runs.csv / report_critical_suspect_runs.csv")
#|
#|            print("\n[TOP] critical_like confirmed max_run (TOP40)")
#|            print(rep_confirm.head(40).to_string(index=False))
#|            print("\n[TOP] critical_like SUSPECT max_run (TOP40)")
#|            print(rep_suspect.head(40).to_string(index=False))
#|    except Exception as _e:
#|        print(f"[WARN] critical report generation failed: {_e}")
#|
#|    # helper flags for daily fault-like events and degraded candidates
#|    fault_sustain = 90            # minutes of sustained low ratio to consider the day fault-like
#|    fault_last_ratio_thr = 0.10   # if last_ratio <= 0.1, treated as nearly dead at end of day
#|    degraded_upper = 0.60         # upper bound for degraded mid_ratio (0.2 ~ 0.6)
#|
#|    out["fault_like_day"] = (
#|        (~out["data_bad"])
#|        & out["event_A"]
#|        & (out["sustain_mins"] >= fault_sustain)
#|        & (out["last_ratio"] <= fault_last_ratio_thr)
#|        & (out["mid_peer"] >= float(args.mid_peer_alive_thr))
#|    )
#|
#|    out["degraded_candidate"] = (
#|        (~out["data_bad"])
#|        & (~out["state_dead"])
#|        & (out["mid_peer"] >= float(args.mid_peer_alive_thr))
#|        & (out["mid_ratio"] > float(args.mid_ratio_dead_thr))
#|        & (out["mid_ratio"] <= degraded_upper)
#|    )
#|
#|    # shadow-like events (basic): degraded days that recovered at least once
#|    # NOTE: refined later using HS/DTW strengths to better match transient cloud/shading behaviour.
#|    out["shadow_like_basic"] = (
#|        (~out["data_bad"])
#|        & out["degraded_candidate"]
#|        & out["recovered_sustained"]
#|    )
#|
#|    # Refined shadow-like: require spatial concurrence OR segmented behaviour, and avoid near-dead patterns
#|    out["shadow_like"] = (
#|        out["shadow_like_basic"]
#|        & (
#|            (out["co_drop_frac"].fillna(0.0) >= float(args.shadow_co_drop_thr))
#|            | (out["seg_count"].fillna(0).astype(int) >= int(args.shadow_seg_min))
#|        )
#|        & (out["min_ratio"].fillna(1.0) >= float(args.shadow_min_ratio_floor))
#|    )
#|
#|    # Guard: group/string OFF events should not contaminate other event categories
#|    if "group_off_like" in out.columns:
#|        mask_go = out["group_off_like"].fillna(False).astype(bool)
#|        if mask_go.any():
#|            for col in ["fault_like_day", "degraded_candidate", "shadow_like_basic", "shadow_like"]:
#|                if col in out.columns:
#|                    out.loc[mask_go, col] = False
#|
#|    # textual anomaly level for easier downstream use
#|    out["anom_level"] = "normal"
#|    out.loc[out["degraded_candidate"], "anom_level"] = "degraded_or_shadow"
#|    out.loc[out["shadow_like"], "anom_level"] = "shadow_like"
#|    out.loc[out["fault_like_day"], "anom_level"] = "fault_like"
#|    out.loc[out["group_off_like"], "anom_level"] = "group_off_like"
#|    out.loc[out["final_fault"], "anom_level"] = "confirmed_fault"
#|
#|    # Layer 2: AE 기반 강도 / 서브타입 태깅
#|    # 날짜별 AE 재구성오차 분위수 (0~1)
#|    out["recon_rank_day"] = out.groupby("date")["recon_error"].rank(pct=True)
#|
#|    # AE 강도 수준
#|    out["ae_strength"] = "low"
#|    out.loc[out["recon_rank_day"] >= 0.7, "ae_strength"] = "mid"
#|    out.loc[out["recon_rank_day"] >= 0.9, "ae_strength"] = "high"
#|    # is_ae_strong=True인 경우는 무조건 high로 승격
#|    out.loc[out["is_ae_strong"], "ae_strength"] = "high"
#|
#|    # 이상 서브타입 태그
#|    out["anom_subtype"] = "normal"
#|    out.loc[out["group_off_like"], "anom_subtype"] = "group_off_event"
#|
#|    # shadow-like: 음영/날씨성 이벤트를 AE 강도 기준으로 세분화
#|    out.loc[out["shadow_like"] & (~out["is_ae_strong"]), "anom_subtype"] = "shadow_like_mild"
#|    out.loc[out["shadow_like"] & out["is_ae_strong"], "anom_subtype"] = "shadow_like_strong"
#|
#|    # 열화 후보: shadow_like로 이미 태깅된 패널은 제외하고, AE 강도로 구분
#|    out.loc[
#|        out["degraded_candidate"] & (~out["shadow_like"]) & (~out["is_ae_strong"]),
#|        "anom_subtype",
#|    ] = "degradation_mild"
#|    out.loc[
#|        out["degraded_candidate"] & (~out["shadow_like"]) & out["is_ae_strong"],
#|        "anom_subtype",
#|    ] = "degradation_strong"
#|
#|    # 하루 고장 패턴: fault-like day
#|    out.loc[
#|        out["fault_like_day"] & (~out["is_ae_strong"]),
#|        "anom_subtype",
#|    ] = "fault_like_weak"
#|    out.loc[
#|        out["fault_like_day"] & out["is_ae_strong"],
#|        "anom_subtype",
#|    ] = "fault_like_strong"
#|
#|    # 최종 confirmed fault는 항상 confirmed_fault로 override
#|    out.loc[out["confirmed_fault"], "anom_subtype"] = "confirmed_fault"
#|    out.loc[(out["critical_fault"]) & (~out["confirmed_fault"]), "anom_subtype"] = "critical_fault_vdrop"
#|
#|    # Layer 3: EWS(전조) 지표 – 4종 (mid_var, eventA_freq, dtw_mean, hs_mean)
#|    # 패널별 날짜 순으로 정렬 후 롤링 통계 계산
#|    out = out.sort_values(["panel_id", "date"])
#|    grp = out.groupby("panel_id", group_keys=False)
#|
#|    # 1) 기본 롤링 지표 4개
#|    out["ews_mid_var_7d"] = grp["mid_ratio"].transform(
#|        lambda s: s.rolling(window=7, min_periods=3).var()
#|    )
#|    out["ews_eventA_freq_7d"] = grp["event_A"].transform(
#|        lambda s: s.rolling(window=7, min_periods=3).mean()
#|    )
#|    out["ews_dtw_mean_7d"] = grp["dtw_dist"].transform(
#|        lambda s: s.rolling(window=7, min_periods=3).mean()
#|    )
#|    out["ews_hs_mean_7d"] = grp["hs_score"].transform(
#|        lambda s: s.rolling(window=7, min_periods=3).mean()
#|    )
#|
#|    # 2) 운영(인과성) 관점: 전역 임계값과 월별 베이스라인은 "과거 데이터"로만 산정
#|    #    - 날짜 d에서의 판단은 date < d 구간의 분포/베이스라인만 사용 (미래 데이터 누수 방지)
#|
#|    # ==== EXPORT: Save main output CSV with n_total defensively included ====
#|    # Ensure n_total is exported for ops/debug (number of panels per (date, group_key))
#|    if "n_total" not in out.columns:
#|        out["n_total"] = out.groupby(["date", "group_key"])["panel_id"].transform("nunique").astype(float)
#|
#|    # Define output columns (OUT_COLS): insert n_total after n_ref if present, else near v_ref-related cols
#|    OUT_COLS = [
#|        "date", "panel_id",
#|        "recon_error", "ae_thr_used",
#|        "drop_time", "sustain_mins", "recovered",
#|        "last_ratio", "last_peer",
#|        "mid_ratio", "mid_peer", "mid_v_ratio", "mid_i_ratio",
#|        "coverage", "co_drop_frac",
#|        "is_ae_abn", "is_ae_strong", "source_csv",
#|        "dtw_dist", "hs_score", "recovered_any", "recovered_sustained", "re_drop",
#|        "coverage_mid", "seg_count", "total_low_mins", "min_ratio", "p10_ratio", "p50_ratio", "low_area",
#|        "event_A", "data_bad",
#|        "group_key_base", "vbin", "group_key",
#|        "v_ref", "v_ref_span", "v_ref_ok", "n_ref",  # v_ref-related section
#|        # n_total will be inserted after n_ref or after v_ref-related cols below
#|        "no_ref", "v_drop",
#|        "state_dead", "state_dead_eff", "dead_streak", "confirmed_fault",
#|        "dead_diag_on_day", "dead_diag_date",
#|        "critical_like", "critical_like_eff", "crit_streak", "critical_fault", "critical_source",
#|        "critical_diag_on_day", "critical_diag_date", "diagnosis_date_online",
#|        "critical_confirmed", "critical_suspect", "final_fault",
#|        "group_off_date", "group_off_like", "group_off_group",
#|        "base_day_panel_count", "base_day_degraded_panel_count", "subgroup_common_cause_candidate",
#|        "fault_like_day", "degraded_candidate", "shadow_like_basic", "shadow_like",
#|        "anom_level", "recon_rank_day", "ae_strength", "anom_subtype",
#|        "ews_mid_var_7d", "ews_eventA_freq_7d", "ews_dtw_mean_7d", "ews_hs_mean_7d"
#|    ]
#|    # Insert n_total after n_ref if present, else after v_ref_ok, v_ref_span, or v_ref
#|    if "n_total" not in OUT_COLS:
#|        try:
#|            idx = OUT_COLS.index("n_ref") + 1
#|        except ValueError:
#|            # Try after v_ref_ok or v_ref_span or v_ref
#|            for key in ["v_ref_ok", "v_ref_span", "v_ref"]:
#|                if key in OUT_COLS:
#|                    idx = OUT_COLS.index(key) + 1
#|                    break
#|            else:
#|                idx = len(OUT_COLS)
#|        OUT_COLS.insert(idx, "n_total")
#|
#|    # Final save is performed once at the end of main().
#|
#|    out = _compute_ews(out, args)
#|    out = _compute_site_events(out)
#|
#|    # Gate: site event day should not produce EWS/prefault escalation.
#|    out.loc[out["site_event_soft"], "ews_warning"] = False
#|    out.loc[out["site_event_hard"], "ews_warning"] = False
#|    # Gate: group/string-level OFF events should not escalate into EWS/prefault
#|    out.loc[out["group_off_date"].astype(bool), "ews_warning"] = False
#|
#|    # ---- DTW/HS ranking and subtype refinement ----
#|    # 1) Add daily DTW and HS ranks
#|    out["dtw_rank_day"] = out.groupby("date")["dtw_dist"].rank(pct=True)
#|    out["hs_rank_day"] = out.groupby("date")["hs_score"].rank(pct=True)
#|
#|    # 2) Add categorical strengths
#|    out["dtw_strength"] = "low"
#|    out.loc[out["dtw_rank_day"] >= 0.7, "dtw_strength"] = "mid"
#|    out.loc[out["dtw_rank_day"] >= 0.9, "dtw_strength"] = "high"
#|    out["hs_strength"] = "low"
#|    out.loc[out["hs_rank_day"] >= 0.7, "hs_strength"] = "mid"
#|    out.loc[out["hs_rank_day"] >= 0.9, "hs_strength"] = "high"
#|
#|    # Refine shadow-like using HS/DTW strengths to better capture transient cloud/shading
#|    # - require turbulence (HS mid/high)
#|    # - avoid cases where the panel is strongly off its own reference (DTW high)
#|    # - require spatial concurrence (co_drop_frac >= co_drop_thr)
#|    out["shadow_like"] = (
#|        out["shadow_like_basic"].astype(bool)
#|        & out["hs_strength"].isin(["mid", "high"])
#|        & (~out["dtw_strength"].isin(["high"]))
#|        & (out["co_drop_frac"].fillna(0.0) >= float(args.shadow_co_drop_thr))
#|    )
#|
#|    # Update anom_level after refining shadow_like
#|    # (keep confirmed_fault highest priority)
#|    out.loc[out["shadow_like"], "anom_level"] = "shadow_like"
#|    out.loc[out["shadow_like_basic"] & (~out["shadow_like"]), "anom_level"] = "degraded_or_shadow"
#|    out.loc[out["final_fault"], "anom_level"] = "confirmed_fault"
#|
#|    # 3) Refine anom_subtype using DTW/HS
#|    # For shadow-like days
#|    out.loc[out["shadow_like"] & (out["hs_strength"] != "high"), "anom_subtype"] = "shadow_like_mild"
#|    out.loc[
#|        out["shadow_like"] & (out["hs_strength"] == "high") & (out["dtw_strength"].isin(["mid", "high"])),
#|        "anom_subtype"
#|    ] = "shadow_like_strong"
#|
#|    # For degraded candidates (excluding shadow_like and confirmed faults)
#|    mask_deg = out["degraded_candidate"] & (~out["shadow_like"]) & (~out["final_fault"])
#|    out.loc[
#|        mask_deg & (out["hs_strength"] == "low") & (out["dtw_strength"].isin(["low", "mid"])),
#|        "anom_subtype"
#|    ] = "degradation_steady"
#|    out.loc[
#|        mask_deg & (out["dtw_strength"] == "high"),
#|        "anom_subtype"
#|    ] = "degradation_strong"
#|
#|    # For fault-like days not yet final_fault
#|    mask_fault_like = out["fault_like_day"] & (~out["final_fault"])
#|
#|    # 기본값은 fault_like_weak으로 태깅
#|    out.loc[mask_fault_like, "anom_subtype"] = "fault_like_weak"
#|
#|    # DTW가 강하게 틀어지고, HS 난류가 너무 높지 않은 경우를 strong으로 승격
#|    out.loc[
#|        mask_fault_like
#|        & (out["dtw_strength"] == "high")
#|        & (out["hs_strength"].isin(["low", "mid"])),
#|        "anom_subtype"
#|    ] = "fault_like_strong"
#|
#|    # 4) Confirmed faults always override
#|    out.loc[out["final_fault"], "anom_subtype"] = "confirmed_fault"
#|
#|    # 최종 저장 전에는 다시 날짜+패널 기준 정렬
#|    out = out.sort_values(["date", "panel_id"])
#|
#|    # ===== Layer 4: 1.1-style pre-fault template engine (Option B, 엔진 1.0) =====
#|    # 최근 40일 기준으로 패널별 요약 지표를 만들고,
#|    # 1.1 패널에서 관찰된 패턴과 비슷한 경우를 "전조 후보"로 본다.
#|
#|    # 패널-날짜 순으로 한 번 더 정렬하고 그룹 생성
#|    out = out.sort_values(["panel_id", "date"])
#|    grp_pf = out.groupby("panel_id", group_keys=False)
#|
#|    # AE/DTW/HS mid 이상 여부를 0/1 플래그로 변환
#|    out["ae_mid_flag"] = out["ae_strength"].isin(["mid", "high"]).astype(float)
#|    out["dtw_mid_flag"] = out["dtw_strength"].isin(["mid", "high"]).astype(float)
#|
#|    # 최근 40일 롤링 윈도우 (일 데이터 기준), 최소 20일 이상 관측이 있을 때만 유효
#|    window = 40
#|    min_periods = 20
#|
#|    out["pf40_mid_mean"] = grp_pf["mid_ratio"].transform(
#|        lambda s: s.rolling(window=window, min_periods=min_periods).mean()
#|    )
#|    out["pf40_ae_ratio"] = grp_pf["ae_mid_flag"].transform(
#|        lambda s: s.rolling(window=window, min_periods=min_periods).mean()
#|    )
#|    out["pf40_dtw_ratio"] = grp_pf["dtw_mid_flag"].transform(
#|        lambda s: s.rolling(window=window, min_periods=min_periods).mean()
#|    )
#|    out["pf40_ews_ratio"] = grp_pf["ews_warning"].transform(
#|        lambda s: s.rolling(window=window, min_periods=min_periods).mean()
#|    )
#|
#|    # Option B 템플릿 임계값 (1.1 pre-fault 윈도우를 기준으로 잡은 보수적 구간)
#|    mid_low = 0.5      # 평균 mid_ratio가 너무 낮지도(완전 dead) 너무 높지도(완전 정상) 않은 구간
#|    mid_high = 0.9
#|    pf_ae_ratio_thr = 0.7    # 최근 40일 중 AE mid/high 비율
#|    pf_dtw_ratio_thr = 0.7   # 최근 40일 중 DTW mid/high 비율
#|    pf_ews_ratio_thr = 0.05  # 최근 40일 중 EWS_warning 비율 (대략 40일 중 2일 이상)
#|
#|    cond_mid = (out["pf40_mid_mean"] >= mid_low) & (out["pf40_mid_mean"] <= mid_high)
#|    cond_ae = out["pf40_ae_ratio"] >= pf_ae_ratio_thr
#|    cond_dtw = out["pf40_dtw_ratio"] >= pf_dtw_ratio_thr
#|    cond_ews = out["pf40_ews_ratio"] >= pf_ews_ratio_thr
#|    out["prefault_cond_mid"] = cond_mid.astype(bool)
#|    out["prefault_cond_ae"] = cond_ae.astype(bool)
#|    out["prefault_cond_dtw"] = cond_dtw.astype(bool)
#|    out["prefault_cond_ews"] = cond_ews.astype(bool)
#|
#|    # 실제 전조 엔진 플래그 (b안):
#|    # - 데이터 품질이 나쁘지 않고(data_bad=False)
#|    # - 아직 최종 고장(final_fault)이 아닌 상태에서
#|    # - 위 네 조건을 동시에 만족하면 해당 날짜-패널을 "전조 후보"로 표시
#|    out["prefault_B"] = (
#|        (~out["data_bad"]) & (~out["final_fault"]) &
#|        out["prefault_cond_mid"] & out["prefault_cond_ae"] & out["prefault_cond_dtw"] & out["prefault_cond_ews"]
#|    )
#|    out["base_day_panel_count"] = (
#|        out.groupby(["date", "group_key_base"])["panel_id"].transform("nunique").fillna(0).astype(int)
#|    )
#|    out["base_day_degraded_panel_count"] = (
#|        out.groupby(["date", "group_key_base"])["degraded_candidate"]
#|        .transform(lambda s: s.astype(bool).sum())
#|        .fillna(0)
#|        .astype(int)
#|    )
#|    out["subgroup_common_cause_candidate"] = (
#|        out["degraded_candidate"].astype(bool)
#|        & (~out["site_event_soft"].astype(bool))
#|        & (~out["site_event_hard"].astype(bool))
#|        & (~out["group_off_date"].astype(bool))
#|        & (~out["group_off_like"].astype(bool))
#|        & out["base_day_degraded_panel_count"].ge(3)
#|    )
#|    prefault_common_cause_overlap = (
#|        out["prefault_B"].astype(bool)
#|        & (
#|            out["site_event_soft"].astype(bool)
#|            | out["site_event_hard"].astype(bool)
#|            | out["group_off_date"].astype(bool)
#|            | out["group_off_like"].astype(bool)
#|        )
#|    )
#|    out["prefault_B_common_cause_overlap"] = prefault_common_cause_overlap
#|    out["prefault_B_effective"] = out["prefault_B"].astype(bool) & (~prefault_common_cause_overlap)
#|
#|    # ===== Helper reports: daily summaries & candidate lists =====
#|    # 1) 날짜별 anom_level 요약 테이블
#|    try:
#|        daily_level = (
#|            out.pivot_table(
#|                index="date",
#|                columns="anom_level",
#|                values="panel_id",
#|                aggfunc="count",
#|                fill_value=0,
#|            )
#|            .reset_index()
#|        )
#|        daily_level_path = out_dir / "ae_simple_daily_anom_level.csv"
#|        _safe_report_write(
#|            daily_level,
#|            daily_level_path,
#|            "daily anom_level summary",
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|    except Exception as e:
#|        print("[WARN] failed to write daily anom_level summary:", e)
#|
#|    # 2) 날짜별 anom_subtype 요약 테이블
#|    try:
#|        daily_subtype = (
#|            out.pivot_table(
#|                index="date",
#|                columns="anom_subtype",
#|                values="panel_id",
#|                aggfunc="count",
#|                fill_value=0,
#|            )
#|            .reset_index()
#|        )
#|        daily_subtype_path = out_dir / "ae_simple_daily_anom_subtype.csv"
#|        _safe_report_write(
#|            daily_subtype,
#|            daily_subtype_path,
#|            "daily anom_subtype summary",
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|    except Exception as e:
#|        print("[WARN] failed to write daily anom_subtype summary:", e)
#|
#|    # 3) 고장/후보 패널 리스트 (final_fault / fault_like_day / degraded_candidate)
#|    try:
#|        mask_candidates = (
#|            out["final_fault"].astype(bool)
#|            | out["fault_like_day"].astype(bool)
#|            | out["degraded_candidate"].astype(bool)
#|        )
#|        fault_candidates = out.loc[mask_candidates].copy()
#|        candidates_path = out_dir / "ae_simple_fault_candidates.csv"
#|        _safe_report_write(
#|            fault_candidates,
#|            candidates_path,
#|            "fault candidate list",
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|    except Exception as e:
#|        print("[WARN] failed to write fault candidate list:", e)
#|
#|    # 4) EWS 경고 패널 리스트
#|    try:
#|        ews_list = out[out["ews_warning"].astype(bool)].copy()
#|        ews_path = out_dir / "ae_simple_ews_warnings.csv"
#|        _safe_report_write(
#|            ews_list,
#|            ews_path,
#|            "EWS warning list",
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|    except Exception as e:
#|        print("[WARN] failed to write EWS warning list:", e)
#|
#|    # 5) 전조 엔진(Option B) 알람 리스트 – 날짜·패널 단위
#|    # canonical 이름은 option_b를 명시해 의미를 드러내고,
#|    # 기존 template-B 파일명은 backward-compatible alias로 유지한다.
#|    try:
#|        prefault_list = out[out["prefault_B"].astype(bool)].copy()
#|        pf_path = out_dir / "ae_simple_prefault_option_b_daily.csv"
#|        pf_legacy_path = out_dir / "ae_simple_prefault_B_daily.csv"
#|        _safe_report_write(
#|            prefault_list,
#|            pf_path,
#|            "pre-fault option-b list",
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|        _safe_report_write(
#|            prefault_list,
#|            pf_legacy_path,
#|            "legacy pre-fault template-B alias",
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|    except Exception as e:
#|        print("[WARN] failed to write pre-fault option-b list:", e)
#|
#|    # B안 pre-alarm 플래그: 이미 고장 확정된 날은 제외하고,
#|    # EWS 경고 + (AE/DTW/HS 중 하나 이상 mid 이상) 인 날만 전조 후보로 간주
#|    out["prealarm_cond_ae_mid_or_hi"] = out["ae_strength"].isin(["mid", "high"]).astype(bool)
#|    out["prealarm_cond_dtw_mid_or_hi"] = out["dtw_strength"].isin(["mid", "high"]).astype(bool)
#|    out["prealarm_cond_hs_mid_or_hi"] = out["hs_strength"].isin(["mid", "high"]).astype(bool)
#|    out["pre_alarm"] = (
#|        (~out["final_fault"].astype(bool))
#|        & out["ews_warning"].astype(bool)
#|        & (
#|            out["prealarm_cond_ae_mid_or_hi"]
#|            | out["prealarm_cond_dtw_mid_or_hi"]
#|            | out["prealarm_cond_hs_mid_or_hi"]
#|        )
#|    )
#|
#|    # 6) local precursor gate states helper sidecar
#|    try:
#|        gate_daily = out.loc[
#|            :,
#|            [
#|                "panel_id",
#|                "date",
#|                "data_bad",
#|                "cond_var",
#|                "cond_evt",
#|                "cond_dtw",
#|                "cond_hs",
#|                "pre_ews",
#|                "signal_count",
#|                "ews_runlen",
#|                "ews_warning",
#|                "site_event_soft",
#|                "site_event_hard",
#|                "group_off_date",
#|                "base_day_panel_count",
#|                "base_day_degraded_panel_count",
#|                "subgroup_common_cause_candidate",
#|                "prefault_B",
#|                "prefault_B_common_cause_overlap",
#|                "prefault_B_effective",
#|                "pre_alarm",
#|                "prefault_cond_mid",
#|                "prefault_cond_ae",
#|                "prefault_cond_dtw",
#|                "prefault_cond_ews",
#|                "prealarm_cond_ae_mid_or_hi",
#|                "prealarm_cond_dtw_mid_or_hi",
#|                "prealarm_cond_hs_mid_or_hi",
#|            ],
#|        ].copy()
#|        gate_daily.insert(0, "site", site)
#|        gate_path = out_dir / "ae_simple_local_precursor_gate_daily.csv"
#|        _safe_report_write(
#|            gate_daily,
#|            gate_path,
#|            "local precursor gate daily",
#|            index=False,
#|            encoding="utf-8-sig",
#|        )
#|    except Exception as e:
#|        print("[WARN] failed to write local precursor gate daily:", e)
#|
#|    # 7) 패널별 전조/만성 이상 요약 (전조 엔진 1.0, B안 로직)
#|    try:
#|
#|        # 패널별 집계: 기간, 고장 여부, EWS/전조 일수 등
#|        grp_panel = out.groupby("panel_id")
#|        panel_summary = grp_panel.agg(
#|            first_date=("date", "min"),
#|            last_date=("date", "max"),
#|            has_fault=("final_fault", "any"),
#|            n_fault_days=("final_fault", "sum"),
#|            any_ews=("ews_warning", "any"),
#|            n_ews_days=("ews_warning", "sum"),
#|            any_pre_alarm=("pre_alarm", "any"),
#|            n_pre_alarm_days=("pre_alarm", "sum"),
#|        )
#|
#|        # 패널별 최초 고장일과 최초 전조일
#|        fault_start = (
#|            out[out["final_fault"].astype(bool)]
#|            .groupby("panel_id")["date"]
#|            .min()
#|            .rename("fault_start_date")
#|        )
#|        pre_alarm_start = (
#|            out[out["pre_alarm"].astype(bool)]
#|            .groupby("panel_id")["date"]
#|            .min()
#|            .rename("pre_alarm_start")
#|        )
#|
#|        panel_summary = panel_summary.join(fault_start, how="left").join(pre_alarm_start, how="left")
#|
#|        # 전조 알람 리드타임 (일 단위)
#|        panel_summary["lead_days"] = (
#|            panel_summary["fault_start_date"] - panel_summary["pre_alarm_start"]
#|        ).dt.days
#|
#|        # 패턴 분류 함수: 전조 vs 만성 vs 기타
#|        def _classify_alarm_pattern(row):
#|            # 전조 후보 자체가 없는 패널
#|            if not row["any_pre_alarm"]:
#|                return "no_pre_alarm"
#|
#|            # 실제 고장 패널: 전조 리드타임이 3일 이상이면 전조 후보로 간주
#|            if row["has_fault"]:
#|                if pd.notna(row["lead_days"]) and row["lead_days"] >= 3:
#|                    return "pre_fault_candidate"  # 고장 전에 전조가 선행
#|                else:
#|                    return "near_or_post_fault"  # 고장 직전/직후만 튄 케이스
#|
#|            # 아직 고장은 아니지만, 전조 알람이 장기간 누적된 만성 이상 패널
#|            span_days = (row["last_date"] - row["first_date"]).days
#|            if (row["n_pre_alarm_days"] >= 20) and (span_days >= 60):
#|                return "chronic_abnormal"  # 장기간 만성 이상 패턴
#|
#|            # 나머지: 단기 이상 / 일시적 이상
#|            return "short_abnormal"
#|
#|        panel_summary["alarm_pattern"] = panel_summary.apply(_classify_alarm_pattern, axis=1)
#|
#|        # 패널 요약 리포트 저장
#|        panel_alarm_path = out_dir / "ae_simple_panel_alarms.csv"
#|        _safe_report_write(
#|            panel_summary,
#|            panel_alarm_path,
#|            "panel alarm summary",
#|            index=True,
#|            encoding="utf-8-sig",
#|        )
#|    except Exception as e:
#|        print("[WARN] failed to write panel alarm summary:", e)
#|
#|    out_path = out_dir / "panel_day_core.csv"
#|    out.to_csv(
#|        out_path,
#|        index=False,
#|        encoding="utf-8-sig",
#|        columns=[c for c in OUT_COLS if c in out.columns],
#|    )
#|
#|    meta = {
#|        "args": vars(args),
#|        "ae_threshold_global": ae_thr_ae,
#|        "train_files": [p.name for p in train_files],
#|        "eval_files": [p.name for p in eval_files],
#|    }
#|    meta["tuning_level"] = tuning_level
#|    suffix = "" if tuning_level == "p2" else f"_{tuning_level}"
#|    meta_path = out_dir / f"ae_simple_meta{suffix}.json"
#|    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
#|
#|    print("[OK] wrote", out_path)
#|    print("[OK] tuning_level =", tuning_level)
#|    print("[OK] ae_threshold_global =", ae_thr_ae)
#|
#|
#|if __name__ == "__main__":
#|    main()
#|# __write_probe__
#|
#|# __write_probe__
# pvdiag_payload_end
# endregion
# -----------------------------------------------------------------------------
# region payload: raw_only_audit_builder
# pvdiag_payload_file {"bytes": 36363, "endswith_newline": true, "lines": 731, "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py", "role": "raw_only_audit_builder", "sha256": "68524c0aa151b9c45c36b7c6c03a91d61391d5e6617230ec780e1f82bddbe49e"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|import argparse
#|import sys
#|from pathlib import Path
#|
#|import pandas as pd
#|
#|
#|REPO_ROOT = Path(__file__).resolve().parents[2]
#|if str(REPO_ROOT) not in sys.path:
#|    sys.path.insert(0, str(REPO_ROOT))
#|
#|from research.prognostics import runtime_rawonly_chain_common_v1 as common
#|
#|
#|AUDIT_COLS = [
#|    "site",
#|    "panel_id",
#|    "현재표_사건유형_ko",
#|    "현재표_최종고장양상_ko",
#|    "earliest_warning_date",
#|    "retrospective_onset_date",
#|    "strict_trigger_date",
#|    "first_final_fault_date",
#|    "dead_diag_date",
#|    "onset_confidence",
#|    "onset_method",
#|    "전조흔적_flag",
#|    "순수급작_flag",
#|    "전조평가셋편입_flag",
#|    "급작평가셋편입_flag",
#|    "사건유형_재판정_ko",
#|    "최종고장양상_재판정_ko",
#|    "재판정_근거_ko",
#|    "현재표_보정필요여부_flag",
#|    "패널고장여부_ko",
#|    "대표critical_source",
#|    "대표anom_level",
#|    "대표anom_subtype",
#|    "algorithm_family_ko",
#|    "algorithm_symptom_ko",
#|    "detailed_fault_code",
#|    "detailed_fault_label_ko",
#|    "gap_days",
#|    "degradation_onset_backdate_guard_flag",
#|    "degradation_onset_backdate_guard_name",
#|    "degradation_onset_backdate_guard_reason",
#|    "degradation_onset_backdate_guard_degrade_days",
#|    "g1_suppressed_event_shadow_flag",
#|    "g1_suppressed_event_shadow_rule_name",
#|    "g1_suppressed_event_shadow_current_onset_date",
#|    "g1_suppressed_event_shadow_strict_trigger_date",
#|    "g1_suppressed_event_shadow_current_event_type_ko",
#|    "g1_suppressed_event_shadow_current_final_pattern_ko",
#|    "g1_suppressed_event_shadow_event_type_if_applied_ko",
#|    "g1_suppressed_event_shadow_final_pattern_if_applied_ko",
#|    "g1_suppressed_event_shadow_transition_class",
#|    "g1_suppressed_event_shadow_reason",
#|    "g1_suppressed_event_guard_applied_flag",
#|    "g1_suppressed_event_guard_apply_reason",
#|    "secondary_window_candidate_flag",
#|    "secondary_window_selected_onset_date",
#|    "secondary_window_selected_marker",
#|    "secondary_window_selected_gap_days",
#|    "secondary_window_qualified_count",
#|    "secondary_window_too_early_count",
#|    "secondary_window_change_class",
#|    "secondary_window_review_tier",
#|    "secondary_window_reason",
#|    "promotion_decision_bucket",
#|    "promotion_decision_reason",
#|    "common_cause_anchor_date",
#|    "common_cause_anchor_kind",
#|    "site_event_history_flag",
#|    "group_off_history_flag",
#|    "subgroup_common_cause_history_flag",
#|    "common_cause_history_flag",
#|    "strict_trigger_proximal_common_cause_flag",
#|    "warning_proximal_common_cause_flag",
#|    "trigger_proximal_common_cause_flag",
#|    "fault_family_hypothesis_shadow_ko",
#|    "fault_subtype_hypothesis_shadow_ko",
#|    "subtype_evidence_tags",
#|    "subtype_confidence_shadow",
#|    "subtype_shape_confidence_shadow",
#|    "subtype_promotion_blocker_shadow",
#|    "subtype_promotion_blocker_detail_shadow",
#|    "subtype_promotion_blocker_reason_ko",
#|    "subtype_hold_reason_ko",
#|    "subtype_production_write_allowed",
#|]
#|SUMMARY_COLS = [
#|    "전체_패널수",
#|    "고장_패널수",
#|    "비고장_패널수",
#|    "미확정_패널수",
#|    "전조형_고장수",
#|    "급작_고장수",
#|    "전조평가셋_패널수",
#|    "급작평가셋_패널수",
#|    "algorithm_family_다이오드형_패널수",
#|    "algorithm_family_개방장치이상형_패널수",
#|    "algorithm_family_모듈손상형_패널수",
#|    "algorithm_family_불충분_패널수",
#|    "secondary_window_candidate_패널수",
#|    "secondary_window_trigger_only_to_precursor_패널수",
#|    "secondary_window_review_required_패널수",
#|    "promotion_decision_promote_candidate_패널수",
#|    "promotion_decision_manual_review_패널수",
#|    "promotion_decision_blocked_cluster_risk_패널수",
#|    "promotion_decision_hold_shadow_only_패널수",
#|    "promotion_decision_backdate_suppression_candidate_패널수",
#|    "promotion_decision_audit_provenance_only_패널수",
#|    "g1_suppressed_event_shadow_candidate_패널수",
#|    "g1_suppressed_event_shadow_precursor_to_sudden_패널수",
#|    "g1_suppressed_event_guard_applied_패널수",
#|    "g1_suppressed_event_guard_hold_review_패널수",
#|    "subtype_shadow_populated_패널수",
#|    "subtype_confidence_high_패널수",
#|    "subtype_confidence_medium_패널수",
#|    "subtype_confidence_low_패널수",
#|    "subtype_confidence_hold_패널수",
#|    "subtype_shape_confidence_high_패널수",
#|    "subtype_shape_confidence_medium_패널수",
#|    "subtype_shape_confidence_low_패널수",
#|    "subtype_shape_confidence_hold_패널수",
#|    "subtype_promotion_blocker_common_cause_패널수",
#|    "subtype_promotion_blocker_insufficient_recurrence_패널수",
#|    "subtype_promotion_blocker_backdating_risk_패널수",
#|    "subtype_promotion_blocker_measurement_quality_패널수",
#|    "subtype_promotion_blocker_insufficient_evidence_패널수",
#|    "subtype_promotion_blocker_none_패널수",
#|    "subtype_promotion_blocker_detail_site_event_패널수",
#|    "subtype_promotion_blocker_detail_strict_trigger_proximal_패널수",
#|    "subtype_promotion_blocker_detail_subgroup_common_cause_패널수",
#|    "subtype_promotion_blocker_detail_group_off_패널수",
#|    "subtype_promotion_blocker_detail_common_cause_history_패널수",
#|    "subtype_promotion_blocker_detail_backdating_risk_패널수",
#|    "subtype_promotion_blocker_detail_none_패널수",
#|    "subtype_production_write_allowed_sum",
#|    "note_ko",
#|]
#|
#|
#|def parse_args() -> argparse.Namespace:
#|    parser = argparse.ArgumentParser(
#|        description=(
#|            "Build a raw-only runtime fault-event audit from panel_day_core and "
#|            "ae_simple_local_precursor_gate_daily without frozen truth/support assets."
#|        )
#|    )
#|    parser.add_argument(
#|        "--root",
#|        type=Path,
#|        default=REPO_ROOT,
#|        help="Workspace root containing data/<site>/out.",
#|    )
#|    return parser.parse_args()
#|
#|
#|def subtype_shadow_row(metrics: common.PanelRuntimeMetrics) -> dict[str, object]:
#|    event_type = common.normalize_text(metrics.사건유형_재판정_ko)
#|    fault_status = common.normalize_text(metrics.패널고장여부_ko)
#|    algorithm_family = common.normalize_text(metrics.algorithm_family_ko)
#|    representative_source = common.normalize_text(metrics.대표critical_source)
#|    representative_subtype = common.normalize_text(metrics.대표anom_subtype)
#|    detailed_code = common.normalize_text(metrics.detailed_fault_code)
#|
#|    def pack(
#|        family: str,
#|        subtype: str,
#|        confidence: str,
#|        hold_reason: str,
#|        tags: list[str],
#|        shape_confidence: str | None = None,
#|        promotion_blocker: str = "none",
#|        promotion_blocker_detail: str = "",
#|        promotion_blocker_reason: str = "",
#|    ) -> dict[str, object]:
#|        compact_tags = list(dict.fromkeys(tag for tag in tags if tag))
#|        family_text = common.normalize_text(family)
#|        subtype_text = common.normalize_text(subtype)
#|        blocker = common.normalize_text(promotion_blocker)
#|        if not family_text and not subtype_text:
#|            blocker = ""
#|        elif not blocker:
#|            blocker = "none"
#|        blocker_detail = common.normalize_text(promotion_blocker_detail)
#|        if blocker == "common_cause" and not blocker_detail:
#|            blocker_detail = "common_cause_history"
#|        elif blocker and not blocker_detail:
#|            blocker_detail = blocker
#|        shape_confidence_text = common.normalize_text(shape_confidence)
#|        if not shape_confidence_text:
#|            shape_confidence_text = common.normalize_text(confidence)
#|        blocker_reason = promotion_blocker_reason
#|        if blocker == "none" and not blocker_reason and (family_text or subtype_text):
#|            blocker_reason = (
#|                "no subtype-specific promotion blocker classified; production write remains "
#|                "disabled by shadow-only branch policy"
#|            )
#|        return {
#|            "fault_family_hypothesis_shadow_ko": family,
#|            "fault_subtype_hypothesis_shadow_ko": subtype,
#|            "subtype_evidence_tags": ",".join(compact_tags),
#|            "subtype_confidence_shadow": confidence,
#|            "subtype_shape_confidence_shadow": shape_confidence_text,
#|            "subtype_promotion_blocker_shadow": blocker,
#|            "subtype_promotion_blocker_detail_shadow": blocker_detail,
#|            "subtype_promotion_blocker_reason_ko": blocker_reason,
#|            "subtype_hold_reason_ko": hold_reason,
#|            "subtype_production_write_allowed": 0,
#|        }
#|
#|    def empty(reason: str = "") -> dict[str, object]:
#|        return pack("", "", "", reason, [], shape_confidence="", promotion_blocker="", promotion_blocker_detail="")
#|
#|    if fault_status != "고장" and not event_type:
#|        return empty("no runtime fault event; subtype hypothesis not assigned")
#|
#|    base_tags = [
#|        f"event_type={event_type}" if event_type else "",
#|        f"algorithm_family={algorithm_family}" if algorithm_family else "",
#|        f"critical_source={representative_source}" if representative_source else "",
#|        f"anom_subtype={representative_subtype}" if representative_subtype else "",
#|        f"gap_days={metrics.gap_days}" if metrics.gap_days else "",
#|        f"onset_method={metrics.onset_method}" if metrics.onset_method else "",
#|    ]
#|    common_cause_tags: list[str] = []
#|    common_cause_blocker = ""
#|    common_cause_blocker_detail = ""
#|    common_cause_hold_reason = ""
#|    if metrics.has_site_event or metrics.has_strict_trigger_proximal_common_cause:
#|        common_cause_tags.append("site_or_strict_proximal_common_cause")
#|        common_cause_blocker = "common_cause"
#|        if metrics.has_site_event:
#|            common_cause_blocker_detail = "site_event"
#|        else:
#|            common_cause_blocker_detail = "strict_trigger_proximal"
#|        common_cause_hold_reason = (
#|            "candidate subtype is held because site/strict-proximal common-cause evidence "
#|            "blocks individual panel precursor promotion"
#|        )
#|    elif metrics.has_subgroup_common_cause or metrics.has_group_off:
#|        common_cause_tags.append("root_or_group_common_cause")
#|        common_cause_blocker = "common_cause"
#|        if metrics.has_subgroup_common_cause:
#|            common_cause_blocker_detail = "subgroup_common_cause"
#|        else:
#|            common_cause_blocker_detail = "group_off"
#|        common_cause_hold_reason = (
#|            "candidate subtype is held because root/group common-cause evidence must be "
#|            "separated before individual panel promotion"
#|        )
#|    elif metrics.has_common_cause_history:
#|        common_cause_tags.append("common_cause_history")
#|        common_cause_blocker = "common_cause"
#|        common_cause_blocker_detail = "common_cause_history"
#|        common_cause_hold_reason = (
#|            "candidate subtype is held because broad common-cause history is episode evidence"
#|        )
#|
#|    if metrics.g1_suppressed_event_shadow_flag:
#|        tags = base_tags + [
#|            "family=degradation_soiling_shadow",
#|            "g1_shadow",
#|            "long_gap",
#|            "one_day_degradation",
#|            "strict_common_cause=1" if metrics.has_strict_trigger_proximal_common_cause else "",
#|        ]
#|        return pack(
#|            "열화·오염·음영 계열",
#|            "장기 gap 단일 저하 보류형",
#|            "hold",
#|            "BR-018 subtype hypothesis: one-day long-gap degradation is backdating-risk evidence, not a confirmed precursor",
#|            tags,
#|            shape_confidence="low",
#|            promotion_blocker="backdating_risk",
#|            promotion_blocker_detail="backdating_risk",
#|            promotion_blocker_reason=(
#|                "one-day degradation marker is too far from the strict trigger to promote as "
#|                "a confirmed precursor"
#|            ),
#|        )
#|
#|    source_text = f"{representative_source} {representative_subtype} {detailed_code}".lower()
#|    if any(token in source_text for token in ["sensor", "feedback", "dropout", "freeze", "scale", "timestamp"]):
#|        tags = base_tags + ["family=measurement_feedback", "measurement_signature"]
#|        if any(token in source_text for token in ["dropout", "freeze"]):
#|            subtype = "센서 dropout·freeze형"
#|        elif "timestamp" in source_text:
#|            subtype = "timestamp·채널 매칭 이상형"
#|        else:
#|            subtype = "센서 scale drift형"
#|        return pack(
#|            "센서·피드백·계측 이상 계열",
#|            subtype,
#|            "hold",
#|            "measurement-feedback subtype is data-quality evidence and is not promoted as panel fault",
#|            tags,
#|            shape_confidence="low",
#|            promotion_blocker="measurement_quality",
#|            promotion_blocker_detail="measurement_quality",
#|            promotion_blocker_reason=(
#|                "measurement-feedback signatures must be separated from physical panel faults"
#|            ),
#|        )
#|
#|    if algorithm_family == "다이오드형" or metrics.has_vdrop:
#|        tags = base_tags + common_cause_tags + ["family=diode_substring", "vi_ratio_shape"]
#|        if "substring" in representative_subtype.lower() or "sub" in representative_subtype.lower():
#|            subtype = "서브스트링 전류 제한형"
#|        else:
#|            subtype = "bypass diode 동작·고장 의심형"
#|        shape_confidence = "medium" if fault_status == "고장" else "low"
#|        confidence = "hold" if common_cause_hold_reason else shape_confidence
#|        return pack(
#|            "다이오드·서브스트링 계열",
#|            subtype,
#|            confidence,
#|            common_cause_hold_reason
#|            or "shadow-only subtype; requires VI curve review before operator-facing label use",
#|            tags,
#|            shape_confidence=shape_confidence,
#|            promotion_blocker=common_cause_blocker or "none",
#|            promotion_blocker_detail=common_cause_blocker_detail or "none",
#|            promotion_blocker_reason=common_cause_hold_reason,
#|        )
#|
#|    if algorithm_family == "모듈손상형" or (
#|        algorithm_family not in {"개방/장치이상형", "다이오드형"}
#|        and (metrics.has_degradation or metrics.has_shadow)
#|    ):
#|        tags = base_tags + common_cause_tags + ["family=degradation_soiling_shadow"]
#|        if metrics.has_shadow and not metrics.has_degradation:
#|            subtype = "국소 음영 패턴형"
#|            tags.append("shadow_pattern")
#|            confidence = "low"
#|            shape_confidence = "low"
#|            promotion_blocker = "insufficient_recurrence"
#|            promotion_blocker_detail = "insufficient_recurrence"
#|            promotion_blocker_reason = "shading-like hypothesis requires repeated time-of-day shape evidence"
#|            hold_reason = "shading-like hypothesis requires repeated time-of-day shape evidence"
#|        elif event_type == "전조형 고장" and metrics.gap_days >= 7:
#|            subtype = "누적 오염·열화형"
#|            tags.extend(["duration_or_gap_support", "precursor_event"])
#|            confidence = "medium"
#|            shape_confidence = "medium"
#|            promotion_blocker = "none"
#|            promotion_blocker_detail = "none"
#|            promotion_blocker_reason = ""
#|            hold_reason = "shadow-only subtype; keep production label unchanged until recurrence/continuity is reviewed"
#|        else:
#|            subtype = "일시 환경 episode형"
#|            tags.append("transient_or_sparse_degradation")
#|            confidence = "hold"
#|            shape_confidence = "low"
#|            promotion_blocker = "insufficient_recurrence"
#|            promotion_blocker_detail = "insufficient_recurrence"
#|            promotion_blocker_reason = "sparse degradation/shadow evidence lacks recurrence or continuity support"
#|            hold_reason = "sparse degradation/shadow evidence is held as an episode, not confirmed precursor"
#|        if common_cause_hold_reason:
#|            confidence = "hold"
#|            hold_reason = common_cause_hold_reason
#|            promotion_blocker = common_cause_blocker
#|            promotion_blocker_detail = common_cause_blocker_detail
#|            promotion_blocker_reason = common_cause_hold_reason
#|        return pack(
#|            "열화·오염·음영 계열",
#|            subtype,
#|            confidence,
#|            hold_reason,
#|            tags,
#|            shape_confidence=shape_confidence,
#|            promotion_blocker=promotion_blocker,
#|            promotion_blocker_detail=promotion_blocker_detail,
#|            promotion_blocker_reason=promotion_blocker_reason,
#|        )
#|
#|    if algorithm_family == "개방/장치이상형":
#|        tags = base_tags + common_cause_tags + ["family=open_connection_partial"]
#|        if metrics.secondary_window_candidate_flag or metrics.secondary_window_qualified_count >= 2:
#|            subtype = "간헐 접촉저항형"
#|            tags.append("recurrence_or_secondary_window")
#|            confidence = "low"
#|            shape_confidence = "medium"
#|            promotion_blocker = "none"
#|            promotion_blocker_detail = "none"
#|            promotion_blocker_reason = ""
#|        elif metrics.has_final_fault or metrics.has_fault_like:
#|            subtype = "부분 개방 진행형"
#|            tags.append("strict_or_final_fault_anchor")
#|            confidence = "medium"
#|            shape_confidence = "medium"
#|            promotion_blocker = "none"
#|            promotion_blocker_detail = "none"
#|            promotion_blocker_reason = ""
#|        else:
#|            subtype = "커넥터·단자·퓨즈 계열 의심형"
#|            tags.append("open_connection_proxy")
#|            confidence = "low"
#|            shape_confidence = "low"
#|            promotion_blocker = "insufficient_recurrence"
#|            promotion_blocker_detail = "insufficient_recurrence"
#|            promotion_blocker_reason = "open-connection proxy lacks recurrence or shape-similarity support"
#|        if common_cause_hold_reason:
#|            confidence = "hold"
#|            promotion_blocker = common_cause_blocker
#|            promotion_blocker_detail = common_cause_blocker_detail
#|            promotion_blocker_reason = common_cause_hold_reason
#|        return pack(
#|            "접속 불량·부분 개방 계열",
#|            subtype,
#|            confidence,
#|            common_cause_hold_reason
#|            or "manual-review subtype hypothesis; recurrence and shape similarity are required before promotion",
#|            tags,
#|            shape_confidence=shape_confidence,
#|            promotion_blocker=promotion_blocker,
#|            promotion_blocker_detail=promotion_blocker_detail,
#|            promotion_blocker_reason=promotion_blocker_reason,
#|        )
#|
#|    if common_cause_hold_reason:
#|        tags = base_tags + common_cause_tags + ["family=external_common_cause"]
#|        if metrics.has_site_event or metrics.has_strict_trigger_proximal_common_cause:
#|            subtype = "site-wide grid/inverter 교란형"
#|        elif metrics.has_subgroup_common_cause or metrics.has_group_off:
#|            subtype = "root·MPPT group 공통 episode형"
#|        else:
#|            subtype = "날씨·일사 공통 episode형"
#|        return pack(
#|            "외부계통·공통원인 계열",
#|            subtype,
#|            "hold",
#|            common_cause_hold_reason,
#|            tags,
#|            shape_confidence="medium",
#|            promotion_blocker=common_cause_blocker,
#|            promotion_blocker_detail=common_cause_blocker_detail,
#|            promotion_blocker_reason=common_cause_hold_reason,
#|        )
#|
#|    if event_type == "급작 고장":
#|        tags = base_tags + ["family=strict_anchor_sudden", "strict_trigger_anchor"]
#|        return pack(
#|            "strict trigger anchored sudden fault",
#|            "strict 근접 급작형",
#|            "medium",
#|            "no confirmed precursor recurrence before strict trigger",
#|            tags,
#|            shape_confidence="medium",
#|            promotion_blocker="none",
#|            promotion_blocker_detail="none",
#|        )
#|
#|    return pack(
#|        "불충분",
#|        "세부가설 불충분",
#|        "hold",
#|        "available runtime evidence is insufficient for subtype hypothesis assignment",
#|        base_tags + ["family=insufficient"],
#|        shape_confidence="hold",
#|        promotion_blocker="insufficient_evidence",
#|        promotion_blocker_detail="insufficient_evidence",
#|        promotion_blocker_reason="available runtime evidence is insufficient for subtype hypothesis assignment",
#|    )
#|
#|
#|def build_rows(root: Path) -> pd.DataFrame:
#|    rows: list[dict[str, object]] = []
#|    for site in common.discover_sites(root):
#|        core_df, gate_df = common.load_site_outputs(root, site)
#|        for panel_id in common.panel_keys(core_df, gate_df):
#|            metrics = common.compute_panel_metrics(site, panel_id, core_df, gate_df)
#|            subtype_shadow = subtype_shadow_row(metrics)
#|            rows.append(
#|                {
#|                    "site": metrics.site,
#|                    "panel_id": metrics.panel_id,
#|                    "현재표_사건유형_ko": metrics.사건유형_재판정_ko,
#|                    "현재표_최종고장양상_ko": metrics.최종고장양상_재판정_ko,
#|                    "earliest_warning_date": metrics.earliest_warning_date,
#|                    "retrospective_onset_date": metrics.retrospective_onset_date,
#|                    "strict_trigger_date": metrics.strict_trigger_date,
#|                    "first_final_fault_date": metrics.first_final_fault_date,
#|                    "dead_diag_date": metrics.dead_diag_date,
#|                    "onset_confidence": metrics.onset_confidence,
#|                    "onset_method": metrics.onset_method,
#|                    "전조흔적_flag": metrics.전조흔적_flag,
#|                    "순수급작_flag": metrics.순수급작_flag,
#|                    "전조평가셋편입_flag": metrics.전조평가셋편입_flag,
#|                    "급작평가셋편입_flag": metrics.급작평가셋편입_flag,
#|                    "사건유형_재판정_ko": metrics.사건유형_재판정_ko,
#|                    "최종고장양상_재판정_ko": metrics.최종고장양상_재판정_ko,
#|                    "재판정_근거_ko": metrics.재판정_근거_ko,
#|                    "현재표_보정필요여부_flag": metrics.현재표_보정필요여부_flag,
#|                    "패널고장여부_ko": metrics.패널고장여부_ko,
#|                    "대표critical_source": metrics.대표critical_source,
#|                    "대표anom_level": metrics.대표anom_level,
#|                    "대표anom_subtype": metrics.대표anom_subtype,
#|                    "algorithm_family_ko": metrics.algorithm_family_ko,
#|                    "algorithm_symptom_ko": metrics.algorithm_symptom_ko,
#|                    "detailed_fault_code": metrics.detailed_fault_code,
#|                    "detailed_fault_label_ko": metrics.detailed_fault_label_ko,
#|                    "gap_days": metrics.gap_days,
#|                    "degradation_onset_backdate_guard_flag": int(
#|                        metrics.degradation_onset_backdate_guard_flag
#|                    ),
#|                    "degradation_onset_backdate_guard_name": (
#|                        metrics.degradation_onset_backdate_guard_name
#|                    ),
#|                    "degradation_onset_backdate_guard_reason": (
#|                        metrics.degradation_onset_backdate_guard_reason
#|                    ),
#|                    "degradation_onset_backdate_guard_degrade_days": (
#|                        metrics.degradation_onset_backdate_guard_degrade_days
#|                    ),
#|                    "g1_suppressed_event_shadow_flag": int(
#|                        metrics.g1_suppressed_event_shadow_flag
#|                    ),
#|                    "g1_suppressed_event_shadow_rule_name": (
#|                        metrics.g1_suppressed_event_shadow_rule_name
#|                    ),
#|                    "g1_suppressed_event_shadow_current_onset_date": (
#|                        metrics.g1_suppressed_event_shadow_current_onset_date
#|                    ),
#|                    "g1_suppressed_event_shadow_strict_trigger_date": (
#|                        metrics.g1_suppressed_event_shadow_strict_trigger_date
#|                    ),
#|                    "g1_suppressed_event_shadow_current_event_type_ko": (
#|                        metrics.g1_suppressed_event_shadow_current_event_type_ko
#|                    ),
#|                    "g1_suppressed_event_shadow_current_final_pattern_ko": (
#|                        metrics.g1_suppressed_event_shadow_current_final_pattern_ko
#|                    ),
#|                    "g1_suppressed_event_shadow_event_type_if_applied_ko": (
#|                        metrics.g1_suppressed_event_shadow_event_type_if_applied_ko
#|                    ),
#|                    "g1_suppressed_event_shadow_final_pattern_if_applied_ko": (
#|                        metrics.g1_suppressed_event_shadow_final_pattern_if_applied_ko
#|                    ),
#|                    "g1_suppressed_event_shadow_transition_class": (
#|                        metrics.g1_suppressed_event_shadow_transition_class
#|                    ),
#|                    "g1_suppressed_event_shadow_reason": (
#|                        metrics.g1_suppressed_event_shadow_reason
#|                    ),
#|                    "g1_suppressed_event_guard_applied_flag": int(
#|                        metrics.g1_suppressed_event_guard_applied_flag
#|                    ),
#|                    "g1_suppressed_event_guard_apply_reason": (
#|                        metrics.g1_suppressed_event_guard_apply_reason
#|                    ),
#|                    "secondary_window_candidate_flag": int(metrics.secondary_window_candidate_flag),
#|                    "secondary_window_selected_onset_date": (
#|                        metrics.secondary_window_selected_onset_date
#|                    ),
#|                    "secondary_window_selected_marker": metrics.secondary_window_selected_marker,
#|                    "secondary_window_selected_gap_days": metrics.secondary_window_selected_gap_days,
#|                    "secondary_window_qualified_count": metrics.secondary_window_qualified_count,
#|                    "secondary_window_too_early_count": metrics.secondary_window_too_early_count,
#|                    "secondary_window_change_class": metrics.secondary_window_change_class,
#|                    "secondary_window_review_tier": metrics.secondary_window_review_tier,
#|                    "secondary_window_reason": metrics.secondary_window_reason,
#|                    "promotion_decision_bucket": metrics.promotion_decision_bucket,
#|                    "promotion_decision_reason": metrics.promotion_decision_reason,
#|                    "common_cause_anchor_date": metrics.common_cause_anchor_date,
#|                    "common_cause_anchor_kind": metrics.common_cause_anchor_kind,
#|                    "site_event_history_flag": int(metrics.has_site_event),
#|                    "group_off_history_flag": int(metrics.has_group_off),
#|                    "subgroup_common_cause_history_flag": int(metrics.has_subgroup_common_cause),
#|                    "common_cause_history_flag": int(metrics.has_common_cause_history),
#|                    "strict_trigger_proximal_common_cause_flag": int(
#|                        metrics.has_strict_trigger_proximal_common_cause
#|                    ),
#|                    "warning_proximal_common_cause_flag": int(
#|                        metrics.has_warning_proximal_common_cause
#|                    ),
#|                    "trigger_proximal_common_cause_flag": int(metrics.has_trigger_proximal_common_cause),
#|                    **subtype_shadow,
#|                }
#|            )
#|    if not rows:
#|        raise SystemExit("runtime fault-event audit must not be empty")
#|    return pd.DataFrame(rows).reindex(columns=AUDIT_COLS).sort_values(["site", "panel_id"]).reset_index(drop=True)
#|
#|
#|def build_summary(df: pd.DataFrame) -> pd.DataFrame:
#|    promotion_bucket = df["promotion_decision_bucket"].map(common.normalize_text)
#|    g1_shadow_transition = df["g1_suppressed_event_shadow_transition_class"].map(common.normalize_text)
#|    g1_shadow_flag = pd.to_numeric(
#|        df["g1_suppressed_event_shadow_flag"], errors="coerce"
#|    ).fillna(0)
#|    g1_guard_applied = pd.to_numeric(
#|        df["g1_suppressed_event_guard_applied_flag"], errors="coerce"
#|    ).fillna(0)
#|    subtype_confidence = df["subtype_confidence_shadow"].map(common.normalize_text)
#|    subtype_shape_confidence = df["subtype_shape_confidence_shadow"].map(common.normalize_text)
#|    subtype_promotion_blocker = df["subtype_promotion_blocker_shadow"].map(common.normalize_text)
#|    subtype_promotion_blocker_detail = df["subtype_promotion_blocker_detail_shadow"].map(common.normalize_text)
#|    subtype_production_write_allowed = pd.to_numeric(
#|        df["subtype_production_write_allowed"], errors="coerce"
#|    ).fillna(0)
#|    row = {
#|        "전체_패널수": int(len(df)),
#|        "고장_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("고장").sum()),
#|        "비고장_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("비고장").sum()),
#|        "미확정_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("미확정").sum()),
#|        "전조형_고장수": int(df["사건유형_재판정_ko"].map(common.normalize_text).eq("전조형 고장").sum()),
#|        "급작_고장수": int(df["사건유형_재판정_ko"].map(common.normalize_text).eq("급작 고장").sum()),
#|        "전조평가셋_패널수": int(pd.to_numeric(df["전조평가셋편입_flag"], errors="coerce").fillna(0).sum()),
#|        "급작평가셋_패널수": int(pd.to_numeric(df["급작평가셋편입_flag"], errors="coerce").fillna(0).sum()),
#|        "algorithm_family_다이오드형_패널수": int(df["algorithm_family_ko"].map(common.normalize_text).eq("다이오드형").sum()),
#|        "algorithm_family_개방장치이상형_패널수": int(df["algorithm_family_ko"].map(common.normalize_text).eq("개방/장치이상형").sum()),
#|        "algorithm_family_모듈손상형_패널수": int(df["algorithm_family_ko"].map(common.normalize_text).eq("모듈손상형").sum()),
#|        "algorithm_family_불충분_패널수": int(df["algorithm_family_ko"].map(common.normalize_text).eq("불충분").sum()),
#|        "secondary_window_candidate_패널수": int(
#|            pd.to_numeric(df["secondary_window_candidate_flag"], errors="coerce").fillna(0).sum()
#|        ),
#|        "secondary_window_trigger_only_to_precursor_패널수": int(
#|            df["secondary_window_change_class"]
#|            .map(common.normalize_text)
#|            .eq("trigger_only_to_precursor")
#|            .sum()
#|        ),
#|        "secondary_window_review_required_패널수": int(
#|            df["secondary_window_review_tier"]
#|            .map(common.normalize_text)
#|            .str.startswith("review_")
#|            .sum()
#|        ),
#|        "promotion_decision_promote_candidate_패널수": int(promotion_bucket.eq("promote_candidate").sum()),
#|        "promotion_decision_manual_review_패널수": int(promotion_bucket.eq("manual_review").sum()),
#|        "promotion_decision_blocked_cluster_risk_패널수": int(
#|            promotion_bucket.eq("blocked_cluster_risk").sum()
#|        ),
#|        "promotion_decision_hold_shadow_only_패널수": int(promotion_bucket.eq("hold_shadow_only").sum()),
#|        "promotion_decision_backdate_suppression_candidate_패널수": int(
#|            promotion_bucket.eq("backdate_suppression_candidate").sum()
#|        ),
#|        "promotion_decision_audit_provenance_only_패널수": int(
#|            promotion_bucket.eq("audit_provenance_only").sum()
#|        ),
#|        "g1_suppressed_event_shadow_candidate_패널수": int(
#|            g1_shadow_flag.sum()
#|        ),
#|        "g1_suppressed_event_shadow_precursor_to_sudden_패널수": int(
#|            g1_shadow_transition.eq("전조형 고장 -> 급작 고장").sum()
#|        ),
#|        "g1_suppressed_event_guard_applied_패널수": int(g1_guard_applied.sum()),
#|        "g1_suppressed_event_guard_hold_review_패널수": int(
#|            ((g1_shadow_flag == 1) & (g1_guard_applied == 0)).sum()
#|        ),
#|        "subtype_shadow_populated_패널수": int(
#|            df["fault_subtype_hypothesis_shadow_ko"].map(common.normalize_text).ne("").sum()
#|        ),
#|        "subtype_confidence_high_패널수": int(subtype_confidence.eq("high").sum()),
#|        "subtype_confidence_medium_패널수": int(subtype_confidence.eq("medium").sum()),
#|        "subtype_confidence_low_패널수": int(subtype_confidence.eq("low").sum()),
#|        "subtype_confidence_hold_패널수": int(subtype_confidence.eq("hold").sum()),
#|        "subtype_shape_confidence_high_패널수": int(subtype_shape_confidence.eq("high").sum()),
#|        "subtype_shape_confidence_medium_패널수": int(subtype_shape_confidence.eq("medium").sum()),
#|        "subtype_shape_confidence_low_패널수": int(subtype_shape_confidence.eq("low").sum()),
#|        "subtype_shape_confidence_hold_패널수": int(subtype_shape_confidence.eq("hold").sum()),
#|        "subtype_promotion_blocker_common_cause_패널수": int(
#|            subtype_promotion_blocker.eq("common_cause").sum()
#|        ),
#|        "subtype_promotion_blocker_insufficient_recurrence_패널수": int(
#|            subtype_promotion_blocker.eq("insufficient_recurrence").sum()
#|        ),
#|        "subtype_promotion_blocker_backdating_risk_패널수": int(
#|            subtype_promotion_blocker.eq("backdating_risk").sum()
#|        ),
#|        "subtype_promotion_blocker_measurement_quality_패널수": int(
#|            subtype_promotion_blocker.eq("measurement_quality").sum()
#|        ),
#|        "subtype_promotion_blocker_insufficient_evidence_패널수": int(
#|            subtype_promotion_blocker.eq("insufficient_evidence").sum()
#|        ),
#|        "subtype_promotion_blocker_none_패널수": int(subtype_promotion_blocker.eq("none").sum()),
#|        "subtype_promotion_blocker_detail_site_event_패널수": int(
#|            subtype_promotion_blocker_detail.eq("site_event").sum()
#|        ),
#|        "subtype_promotion_blocker_detail_strict_trigger_proximal_패널수": int(
#|            subtype_promotion_blocker_detail.eq("strict_trigger_proximal").sum()
#|        ),
#|        "subtype_promotion_blocker_detail_subgroup_common_cause_패널수": int(
#|            subtype_promotion_blocker_detail.eq("subgroup_common_cause").sum()
#|        ),
#|        "subtype_promotion_blocker_detail_group_off_패널수": int(
#|            subtype_promotion_blocker_detail.eq("group_off").sum()
#|        ),
#|        "subtype_promotion_blocker_detail_common_cause_history_패널수": int(
#|            subtype_promotion_blocker_detail.eq("common_cause_history").sum()
#|        ),
#|        "subtype_promotion_blocker_detail_backdating_risk_패널수": int(
#|            subtype_promotion_blocker_detail.eq("backdating_risk").sum()
#|        ),
#|        "subtype_promotion_blocker_detail_none_패널수": int(subtype_promotion_blocker_detail.eq("none").sum()),
#|        "subtype_production_write_allowed_sum": int(subtype_production_write_allowed.sum()),
#|        "note_ko": (
#|            "이 runtime audit는 raw-only 경로다. panel_day_core와 precursor gate만 사용하며, "
#|            "수동 truth/adjudication/frozen audit snapshot은 참조하지 않는다. "
#|            "BR-022 subtype blocker detail columns are shadow-only and "
#|            "do not change production verdict semantics."
#|        ),
#|    }
#|    return pd.DataFrame([row]).reindex(columns=SUMMARY_COLS)
#|
#|
#|def main() -> None:
#|    args = parse_args()
#|    root = args.root.resolve()
#|    share_dir = root / "_share"
#|    share_dir.mkdir(parents=True, exist_ok=True)
#|
#|    audit_df = build_rows(root)
#|    summary_df = build_summary(audit_df)
#|
#|    audit_path = share_dir / common.RUNTIME_AUDIT_OUTPUT_NAME
#|    summary_path = share_dir / common.RUNTIME_AUDIT_SUMMARY_NAME
#|    audit_df.to_csv(audit_path, index=False, encoding="utf-8-sig")
#|    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
#|    print(f"[OK] wrote runtime raw-only audit: {audit_path}")
#|
#|
#|if __name__ == "__main__":
#|    main()
# pvdiag_payload_end
# endregion
# -----------------------------------------------------------------------------
# region payload: raw_only_verdict_builder
# pvdiag_payload_file {"bytes": 8601, "endswith_newline": true, "lines": 191, "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_final_verdict_v1.py", "role": "raw_only_verdict_builder", "sha256": "d23f1a31463f8367d09d23d1c6973d67448b966e89a30f3785e7403ed7dcaccb"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|import argparse
#|import sys
#|from pathlib import Path
#|
#|import pandas as pd
#|
#|
#|REPO_ROOT = Path(__file__).resolve().parents[2]
#|if str(REPO_ROOT) not in sys.path:
#|    sys.path.insert(0, str(REPO_ROOT))
#|
#|from research.prognostics import runtime_rawonly_chain_common_v1 as common
#|
#|
#|VERDICT_COLS = [
#|    "site",
#|    "panel_id",
#|    "사건유형_ko",
#|    "사건유형_해석_ko",
#|    "최종고장양상_ko",
#|    "대표판정_ko",
#|    "사건이력_ko",
#|    "전조흔적_flag",
#|    "순수급작_flag",
#|    "전조평가셋편입_flag",
#|    "급작평가셋편입_flag",
#|    "해석대평가차이_ko",
#|    "운영최초전조발견일",
#|    "운영최초전조마커",
#|    "사건해석상전조시작일",
#|    "benchmark전조시작일",
#|    "전조형이력_flag",
#|    "급작고장이력_flag",
#|    "공통원인이력_flag",
#|    "반복이상이력_flag",
#|    "패널고장여부_ko",
#|    "GPVS_적용대상_ko",
#|    "커널로그_증상명_ko",
#|    "커널로그_원인군_ko",
#|    "GPVS_부착상태_ko",
#|    "GPVS_내부참고유형_ko",
#|    "GPVS_외부참조패턴_ko",
#|    "GPVS_참조사용등급_ko",
#|    "GPVS_참조설명_ko",
#|    "세부fault_type_code",
#|    "세부fault_type_label_ko",
#|    "세부fault_부착상태_ko",
#|    "세부fault_근거파일_ko",
#|    "세부fault_기준일",
#|    "세부fault_보류사유_ko",
#|    "운영위치_ko",
#|    "판정주의_ko",
#|]
#|SUMMARY_COLS = [
#|    "전체_패널수",
#|    "고장_패널수",
#|    "비고장_패널수",
#|    "미확정_패널수",
#|    "전조형_고장수",
#|    "급작_고장수",
#|    "커널로그_원인군_다이오드형_패널수",
#|    "커널로그_원인군_개방장치이상형_패널수",
#|    "커널로그_원인군_모듈손상형_패널수",
#|    "커널로그_원인군_불충분_패널수",
#|    "note_ko",
#|]
#|
#|
#|def parse_args() -> argparse.Namespace:
#|    parser = argparse.ArgumentParser(
#|        description=(
#|            "Build a raw-only runtime final verdict. Column names are preserved where practical, "
#|            "but 커널로그_원인군_ko is algorithm-derived from panel_day_core/gate."
#|        )
#|    )
#|    parser.add_argument(
#|        "--root",
#|        type=Path,
#|        default=REPO_ROOT,
#|        help="Workspace root containing _share runtime audit and data/<site>/out.",
#|    )
#|    return parser.parse_args()
#|
#|
#|def build_rows(audit_df: pd.DataFrame) -> pd.DataFrame:
#|    rows: list[dict[str, object]] = []
#|    for row in audit_df.to_dict(orient="records"):
#|        status = common.normalize_text(row.get("패널고장여부_ko"))
#|        event_type = common.normalize_text(row.get("사건유형_재판정_ko"))
#|        terminal = common.normalize_text(row.get("최종고장양상_재판정_ko"))
#|        family = common.normalize_text(row.get("algorithm_family_ko"))
#|        if status == "고장":
#|            representative = event_type or "고장"
#|            event_history = event_type or "고장"
#|        elif status == "미확정":
#|            representative = "미확정"
#|            event_history = "반복 이상"
#|        else:
#|            representative = "비고장"
#|            event_history = "비고장"
#|        rows.append(
#|            {
#|                "site": common.normalize_text(row.get("site")),
#|                "panel_id": common.normalize_text(row.get("panel_id")),
#|                "사건유형_ko": event_type,
#|                "사건유형_해석_ko": event_type,
#|                "최종고장양상_ko": terminal,
#|                "대표판정_ko": representative,
#|                "사건이력_ko": event_history,
#|                "전조흔적_flag": int(row.get("전조흔적_flag") or 0),
#|                "순수급작_flag": int(row.get("순수급작_flag") or 0),
#|                "전조평가셋편입_flag": int(row.get("전조평가셋편입_flag") or 0),
#|                "급작평가셋편입_flag": int(row.get("급작평가셋편입_flag") or 0),
#|                "해석대평가차이_ko": "",
#|                "운영최초전조발견일": common.normalize_text(row.get("earliest_warning_date")),
#|                "운영최초전조마커": common.normalize_text(row.get("onset_method")),
#|                "사건해석상전조시작일": common.normalize_text(row.get("retrospective_onset_date")),
#|                "benchmark전조시작일": "",
#|                "전조형이력_flag": int(event_type == "전조형 고장"),
#|                "급작고장이력_flag": int(event_type == "급작 고장"),
#|                "공통원인이력_flag": int(row.get("common_cause_history_flag") or 0),
#|                "반복이상이력_flag": int(status == "미확정"),
#|                "패널고장여부_ko": status,
#|                "GPVS_적용대상_ko": "raw-only 미사용",
#|                "커널로그_증상명_ko": common.normalize_text(row.get("algorithm_symptom_ko")),
#|                "커널로그_원인군_ko": family,
#|                "GPVS_부착상태_ko": "raw-only 미사용",
#|                "GPVS_내부참고유형_ko": "",
#|                "GPVS_외부참조패턴_ko": "",
#|                "GPVS_참조사용등급_ko": "",
#|                "GPVS_참조설명_ko": "raw-only strict chain에서는 GPVS reference를 사용하지 않음",
#|                "세부fault_type_code": common.normalize_text(row.get("detailed_fault_code")),
#|                "세부fault_type_label_ko": common.normalize_text(row.get("detailed_fault_label_ko")),
#|                "세부fault_부착상태_ko": "algorithm-derived" if family else "",
#|                "세부fault_근거파일_ko": "panel_day_core.csv + ae_simple_local_precursor_gate_daily.csv" if family else "",
#|                "세부fault_기준일": common.normalize_text(row.get("strict_trigger_date")) or common.normalize_text(row.get("first_final_fault_date")),
#|                "세부fault_보류사유_ko": "" if family and family != "불충분" else "raw-only family confidence limited",
#|                "운영위치_ko": "raw-only runtime",
#|                "판정주의_ko": (
#|                    "커널로그_원인군_ko 컬럼명은 유지하지만, 의미는 raw-only algorithm-derived family로 해석해야 한다. "
#|                    "수동 truth/frozen label을 참조하지 않는다."
#|                ),
#|            }
#|        )
#|    return pd.DataFrame(rows).reindex(columns=VERDICT_COLS).sort_values(["site", "panel_id"]).reset_index(drop=True)
#|
#|
#|def build_summary(df: pd.DataFrame) -> pd.DataFrame:
#|    families = df["커널로그_원인군_ko"].map(common.normalize_text)
#|    row = {
#|        "전체_패널수": int(len(df)),
#|        "고장_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("고장").sum()),
#|        "비고장_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("비고장").sum()),
#|        "미확정_패널수": int(df["패널고장여부_ko"].map(common.normalize_text).eq("미확정").sum()),
#|        "전조형_고장수": int(df["사건유형_ko"].map(common.normalize_text).eq("전조형 고장").sum()),
#|        "급작_고장수": int(df["사건유형_ko"].map(common.normalize_text).eq("급작 고장").sum()),
#|        "커널로그_원인군_다이오드형_패널수": int(families.eq("다이오드형").sum()),
#|        "커널로그_원인군_개방장치이상형_패널수": int(families.eq("개방/장치이상형").sum()),
#|        "커널로그_원인군_모듈손상형_패널수": int(families.eq("모듈손상형").sum()),
#|        "커널로그_원인군_불충분_패널수": int(families.eq("불충분").sum()),
#|        "note_ko": (
#|            "runtime final verdict는 raw-only strict chain용이다. "
#|            "커널로그_원인군_ko는 algorithm-derived family이며, 기존 frozen label field와 의미가 다를 수 있다."
#|        ),
#|    }
#|    return pd.DataFrame([row]).reindex(columns=SUMMARY_COLS)
#|
#|
#|def main() -> None:
#|    args = parse_args()
#|    root = args.root.resolve()
#|    share_dir = root / "_share"
#|    audit_path = share_dir / common.RUNTIME_AUDIT_OUTPUT_NAME
#|    audit_df = common.read_csv(audit_path)
#|    summary_dir = share_dir
#|
#|    verdict_df = build_rows(audit_df)
#|    summary_df = build_summary(verdict_df)
#|
#|    verdict_path = summary_dir / common.RUNTIME_VERDICT_OUTPUT_NAME
#|    summary_path = summary_dir / common.RUNTIME_VERDICT_SUMMARY_NAME
#|    verdict_df.to_csv(verdict_path, index=False, encoding="utf-8-sig")
#|    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
#|    print(f"[OK] wrote runtime raw-only verdict: {verdict_path}")
#|
#|
#|if __name__ == "__main__":
#|    main()
# pvdiag_payload_end
# endregion
# -----------------------------------------------------------------------------
# region payload: raw_only_heuristic_builder
# pvdiag_payload_file {"bytes": 10893, "endswith_newline": true, "lines": 299, "path": "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_heuristic_v1.py", "role": "raw_only_heuristic_builder", "sha256": "18275385e1bc22bca4cb442978ec2b817742637983b6edf77ebaa92aab12768a"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|import argparse
#|import sys
#|from pathlib import Path
#|
#|import pandas as pd
#|
#|
#|REPO_ROOT = Path(__file__).resolve().parents[2]
#|if str(REPO_ROOT) not in sys.path:
#|    sys.path.insert(0, str(REPO_ROOT))
#|
#|from research.prognostics import runtime_rawonly_chain_common_v1 as common
#|
#|
#|CANDIDATES = [
#|    "부분음영형",
#|    "오염형",
#|    "열화형",
#|    "다이오드·서브스트링형",
#|    "접속·부분개방형",
#|    "센서·피드백형",
#|    "제어응답형",
#|    "외부계통교란형",
#|    "전력변환부형",
#|    "원인미확정",
#|]
#|TIE_PRIORITY = {
#|    "다이오드·서브스트링형": 0,
#|    "접속·부분개방형": 1,
#|    "열화형": 2,
#|    "부분음영형": 3,
#|    "오염형": 4,
#|    "센서·피드백형": 5,
#|    "제어응답형": 6,
#|    "외부계통교란형": 7,
#|    "전력변환부형": 8,
#|    "원인미확정": 9,
#|}
#|MAIN_COLS = [
#|    "site",
#|    "panel_id",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "커널로그_원인군_ko",
#|    "GPVS_내부참고유형_ko",
#|    "GPVS_외부참조패턴_ko",
#|    "원인후보_top1_ko",
#|    "원인후보_top1_score",
#|    "원인후보_top2_ko",
#|    "원인후보_top2_score",
#|    "원인후보_top3_ko",
#|    "원인후보_top3_score",
#|    "원인후보_경합상태_ko",
#|    "원인후보_공동상위후보_csv",
#|    "원인후보_실증우선확인_ko",
#|    "원인후보_신뢰도_ko",
#|    "원인후보_해석메모_ko",
#|]
#|SUMMARY_COLS = [
#|    "fault_panel_count",
#|    "top1_다이오드서브스트링형_count",
#|    "top1_접속부분개방형_count",
#|    "top1_열화형_count",
#|    "top1_부분음영형_count",
#|    "top1_센서피드백형_count",
#|    "top1_원인미확정_count",
#|    "note_ko",
#|]
#|
#|FAMILY_BASE_RULES = {
#|    "다이오드형": {
#|        "다이오드·서브스트링형": 5,
#|        "접속·부분개방형": 2,
#|        "부분음영형": 1,
#|    },
#|    "개방/장치이상형": {
#|        "센서·피드백형": 4,
#|        "접속·부분개방형": 3,
#|        "제어응답형": 2,
#|    },
#|    "모듈손상형": {
#|        "열화형": 5,
#|        "부분음영형": 2,
#|        "오염형": 2,
#|        "다이오드·서브스트링형": 1,
#|    },
#|    "불충분": {
#|        "원인미확정": 4,
#|    },
#|}
#|TEMPORAL_RULES = {
#|    ("전조형 고장", "진행성 악화"): {
#|        "열화형": 2,
#|        "오염형": 1,
#|    },
#|    ("전조형 고장", "급격 종료"): {
#|        "접속·부분개방형": 1,
#|        "다이오드·서브스트링형": 1,
#|    },
#|    ("급작 고장", "급작 발생"): {
#|        "접속·부분개방형": 1,
#|        "센서·피드백형": 1,
#|        "다이오드·서브스트링형": 1,
#|    },
#|}
#|SOURCE_RULES = {
#|    "vdrop": {"다이오드·서브스트링형": 2},
#|    "vdrop_suspect": {"다이오드·서브스트링형": 1},
#|    "legacy": {"접속·부분개방형": 2},
#|    "none": {"센서·피드백형": 1},
#|}
#|SUBTYPE_RULES = {
#|    "degradation": {"열화형": 2, "오염형": 1},
#|    "shadow": {"부분음영형": 2},
#|    "critical_fault_vdrop": {"다이오드·서브스트링형": 2},
#|    "confirmed_fault": {"다이오드·서브스트링형": 1},
#|}
#|
#|
#|def parse_args() -> argparse.Namespace:
#|    parser = argparse.ArgumentParser(
#|        description="Build a raw-only runtime cause-candidate heuristic from runtime final verdict."
#|    )
#|    parser.add_argument(
#|        "--root",
#|        type=Path,
#|        default=REPO_ROOT,
#|        help="Workspace root containing runtime verdict and audit outputs.",
#|    )
#|    return parser.parse_args()
#|
#|
#|def score_row(row: dict[str, object]) -> tuple[dict[str, int], list[str]]:
#|    scores = {candidate: 0 for candidate in CANDIDATES}
#|    notes: list[str] = []
#|    family = common.normalize_text(row.get("커널로그_원인군_ko"))
#|    event_type = common.normalize_text(row.get("사건유형_ko"))
#|    terminal = common.normalize_text(row.get("최종고장양상_ko"))
#|    temporal_event_type = event_type
#|    temporal_terminal = terminal
#|    if int(row.get("g1_suppressed_event_guard_applied_flag") or 0):
#|        temporal_event_type = (
#|            common.normalize_text(row.get("g1_suppressed_event_shadow_current_event_type_ko"))
#|            or event_type
#|        )
#|        temporal_terminal = (
#|            common.normalize_text(row.get("g1_suppressed_event_shadow_current_final_pattern_ko"))
#|            or terminal
#|        )
#|    source = common.normalize_text(row.get("대표critical_source"))
#|    subtype = common.normalize_text(row.get("대표anom_subtype"))
#|
#|    for candidate, weight in FAMILY_BASE_RULES.get(family, {"원인미확정": 2}).items():
#|        scores[candidate] += weight
#|    notes.append(f"family={family or 'blank'}")
#|
#|    for candidate, weight in TEMPORAL_RULES.get((temporal_event_type, temporal_terminal), {}).items():
#|        scores[candidate] += weight
#|    if temporal_event_type or temporal_terminal:
#|        notes.append(f"temporal={temporal_event_type}/{temporal_terminal}")
#|    if int(row.get("g1_suppressed_event_guard_applied_flag") or 0):
#|        notes.append("g1_guard_temporal_basis=pre_guard")
#|
#|    for candidate, weight in SOURCE_RULES.get(source, {}).items():
#|        scores[candidate] += weight
#|    if source:
#|        notes.append(f"critical_source={source}")
#|
#|    lowered_subtype = subtype.lower()
#|    for token, rule in SUBTYPE_RULES.items():
#|        if token in lowered_subtype:
#|            for candidate, weight in rule.items():
#|                scores[candidate] += weight
#|            notes.append(f"anom_subtype~={token}")
#|
#|    if max(scores.values()) <= 0:
#|        scores["원인미확정"] = 1
#|    return scores, notes
#|
#|
#|def choose_ranked_candidates(scores: dict[str, int]) -> list[tuple[str, int]]:
#|    return sorted(scores.items(), key=lambda item: (-item[1], TIE_PRIORITY[item[0]], item[0]))
#|
#|
#|def competition_state(top_scores: list[int]) -> tuple[str, str]:
#|    if len(top_scores) < 2:
#|        return "단일우세", ""
#|    max_score = top_scores[0]
#|    tied = [idx for idx, score in enumerate(top_scores) if score == max_score]
#|    if len(tied) == 1:
#|        return "단일우세", ""
#|    if len(tied) == 2:
#|        return "2강경합", "top1_tie"
#|    return "다자경합", "multi_tie"
#|
#|
#|def confidence_label(top1: int, top2: int) -> str:
#|    gap = top1 - top2
#|    if top1 >= 6 and gap >= 2:
#|        return "높음"
#|    if top1 >= 4 and gap >= 1:
#|        return "중간"
#|    return "보통"
#|
#|
#|def build_outputs(verdict_df: pd.DataFrame, audit_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
#|    audit_lookup = {
#|        (common.normalize_text(row["site"]), common.normalize_text(row["panel_id"])): row
#|        for row in audit_df.to_dict(orient="records")
#|    }
#|    rows: list[dict[str, object]] = []
#|    summary_counts = {key: 0 for key in [
#|        "다이오드·서브스트링형",
#|        "접속·부분개방형",
#|        "열화형",
#|        "부분음영형",
#|        "센서·피드백형",
#|        "원인미확정",
#|    ]}
#|    fault_count = 0
#|
#|    for row in verdict_df.to_dict(orient="records"):
#|        if common.normalize_text(row.get("패널고장여부_ko")) != "고장":
#|            continue
#|        fault_count += 1
#|        key = (common.normalize_text(row["site"]), common.normalize_text(row["panel_id"]))
#|        merged = dict(row)
#|        merged.update(audit_lookup.get(key, {}))
#|        scores, notes = score_row(merged)
#|        ranked = choose_ranked_candidates(scores)
#|        top3 = ranked[:3]
#|        top_scores = [score for _, score in top3]
#|        competition, tie_note = competition_state(top_scores)
#|        top1, top2, top3_item = top3
#|        summary_counts[top1[0]] = summary_counts.get(top1[0], 0) + 1
#|        notes_text = ", ".join(notes + ([tie_note] if tie_note else []))
#|        rows.append(
#|            {
#|                "site": key[0],
#|                "panel_id": key[1],
#|                "사건유형_ko": common.normalize_text(row.get("사건유형_ko")),
#|                "최종고장양상_ko": common.normalize_text(row.get("최종고장양상_ko")),
#|                "커널로그_원인군_ko": common.normalize_text(row.get("커널로그_원인군_ko")),
#|                "GPVS_내부참고유형_ko": "",
#|                "GPVS_외부참조패턴_ko": "",
#|                "원인후보_top1_ko": top1[0],
#|                "원인후보_top1_score": top1[1],
#|                "원인후보_top2_ko": top2[0],
#|                "원인후보_top2_score": top2[1],
#|                "원인후보_top3_ko": top3_item[0],
#|                "원인후보_top3_score": top3_item[1],
#|                "원인후보_경합상태_ko": competition,
#|                "원인후보_공동상위후보_csv": ",".join(candidate for candidate, score in top3 if score == top1[1]),
#|                "원인후보_실증우선확인_ko": common.display_heuristic_name(top1[0]),
#|                "원인후보_신뢰도_ko": confidence_label(top1[1], top2[1]),
#|                "원인후보_해석메모_ko": notes_text,
#|            }
#|        )
#|
#|    main_df = pd.DataFrame(rows).reindex(columns=MAIN_COLS).sort_values(["site", "panel_id"]).reset_index(drop=True)
#|    summary_df = pd.DataFrame(
#|        [
#|            {
#|                "fault_panel_count": fault_count,
#|                "top1_다이오드서브스트링형_count": int(summary_counts.get("다이오드·서브스트링형", 0)),
#|                "top1_접속부분개방형_count": int(summary_counts.get("접속·부분개방형", 0)),
#|                "top1_열화형_count": int(summary_counts.get("열화형", 0)),
#|                "top1_부분음영형_count": int(summary_counts.get("부분음영형", 0)),
#|                "top1_센서피드백형_count": int(summary_counts.get("센서·피드백형", 0)),
#|                "top1_원인미확정_count": int(summary_counts.get("원인미확정", 0)),
#|                "note_ko": (
#|                    "이 runtime heuristic는 raw-only strict chain용 deterministic triage 규칙이다. "
#|                    "family/event/source/subtype만 사용하며 GPVS/frozen label은 사용하지 않는다."
#|                ),
#|            }
#|        ]
#|    ).reindex(columns=SUMMARY_COLS)
#|    return main_df, summary_df
#|
#|
#|def main() -> None:
#|    args = parse_args()
#|    root = args.root.resolve()
#|    share_dir = root / "_share"
#|    verdict_df = common.read_csv(share_dir / common.RUNTIME_VERDICT_OUTPUT_NAME)
#|    audit_df = common.read_csv(share_dir / common.RUNTIME_AUDIT_OUTPUT_NAME)
#|    main_df, summary_df = build_outputs(verdict_df, audit_df)
#|    output_path = share_dir / common.RUNTIME_HEURISTIC_OUTPUT_NAME
#|    summary_path = share_dir / common.RUNTIME_HEURISTIC_SUMMARY_NAME
#|    main_df.to_csv(output_path, index=False, encoding="utf-8-sig")
#|    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
#|    print(f"[OK] wrote runtime raw-only heuristic: {output_path}")
#|
#|
#|if __name__ == "__main__":
#|    main()
# pvdiag_payload_end
# endregion
# -----------------------------------------------------------------------------
# region payload: display_label_registry
# pvdiag_payload_file {"bytes": 3281, "endswith_newline": true, "lines": 68, "path": "release/conalog_full_runtime_v1/package/research/prognostics/heuristic_display_registry_v1.py", "role": "display_label_registry", "sha256": "d7cbf8bd24a2274e040231e166eed32098c256c1ba3ce19ba3d667ae6f1f4876"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|import math
#|
#|
#|# `_ko` fields are Korean display labels. Keep them operator/engineer-readable,
#|# and prefer precise field-facing terminology over overly softened wording.
#|# This registry intentionally covers only remapped heuristic-family labels and
#|# their short glossary notes. Longer report/README prose stays outside.
#|DISPLAY_HEURISTIC_NAME_MAP = {
#|    "다이오드·서브스트링형": "다이오드·서브스트링 이상형",
#|    "접속·부분개방형": "접속 불량·부분 개방형",
#|    "센서·피드백형": "센서·계측 피드백 이상형",
#|    "제어응답형": "제어 응답 이상형",
#|    "전력변환부형": "전력변환부 이상형",
#|    "외부계통교란형": "외부 계통 교란형",
#|}
#|
#|HEURISTIC_DISPLAY_NOTE_MAP = {
#|    "다이오드·서브스트링 이상형": "서브스트링 단위 전류 불균형이나 바이패스 다이오드 이상처럼 국소 회로 문제를 우선 의심하는 라벨",
#|    "접속 불량·부분 개방형": "커넥터, 접속부, 배선 일부 개방처럼 접촉 저항 증가나 단속성 단선을 우선 의심하는 라벨",
#|    "센서·계측 피드백 이상형": "센서값, 계측 피드백, 측정 체인 이상 때문에 전기적 이상처럼 보일 수 있는 경우를 가리키는 라벨",
#|    "제어 응답 이상형": "MLPE나 제어기가 패널 상태 변화에 비정상적으로 응답하거나 추종이 흔들리는 경우를 가리키는 라벨",
#|    "전력변환부 이상형": "인버터, 전력변환부, 내부 전력 전자 회로 영향 가능성을 우선 두는 라벨",
#|    "외부 계통 교란형": "계통 전압 변동, 외부 전원 품질 저하, 공통 외란처럼 패널 외부 요인 가능성을 우선 두는 라벨",
#|}
#|
#|LEGACY_HEURISTIC_DISPLAY_NAME_MAP = {
#|    "다이오드·국소 회로 이상형": "다이오드·서브스트링 이상형",
#|    "접촉 끊김 형": "접속 불량·부분 개방형",
#|    "장치 측정 이상형": "센서·계측 피드백 이상형",
#|    "장치 응답 이상형": "제어 응답 이상형",
#|    "외부 전원 흔들림형": "외부 계통 교란형",
#|}
#|
#|LEGACY_HEURISTIC_DISPLAY_NAMES = frozenset(LEGACY_HEURISTIC_DISPLAY_NAME_MAP)
#|
#|
#|def normalize_display_text(value: object) -> str:
#|    if value is None:
#|        return ""
#|    if isinstance(value, float) and math.isnan(value):
#|        return ""
#|    text = str(value).strip()
#|    return "" if text.lower() == "nan" else text
#|
#|
#|def display_heuristic_name(raw_label: object) -> str:
#|    normalized = normalize_display_text(raw_label)
#|    if not normalized:
#|        return ""
#|    if normalized in DISPLAY_HEURISTIC_NAME_MAP:
#|        return DISPLAY_HEURISTIC_NAME_MAP[normalized]
#|    if normalized in HEURISTIC_DISPLAY_NOTE_MAP:
#|        return normalized
#|    if normalized in LEGACY_HEURISTIC_DISPLAY_NAME_MAP:
#|        return LEGACY_HEURISTIC_DISPLAY_NAME_MAP[normalized]
#|    return normalized
#|
#|
#|def display_heuristic_note(raw_label: object) -> str:
#|    normalized = display_heuristic_name(raw_label)
#|    return HEURISTIC_DISPLAY_NOTE_MAP.get(normalized, "")
#|
#|
#|def contains_legacy_heuristic_display_name(value: object) -> bool:
#|    return normalize_display_text(value) in LEGACY_HEURISTIC_DISPLAY_NAMES
# pvdiag_payload_end
# endregion
# -----------------------------------------------------------------------------
# region payload: raw_only_shared_utils
# pvdiag_payload_file {"bytes": 49430, "endswith_newline": true, "lines": 1177, "path": "release/conalog_full_runtime_v1/package/research/prognostics/runtime_rawonly_chain_common_v1.py", "role": "raw_only_shared_utils", "sha256": "62b04b108695ef611f1aa97f7abde111f71d994f38904e1ace2feae595d11ac1"}
#|#!/usr/bin/env python3
#|from __future__ import annotations
#|
#|from dataclasses import dataclass
#|from pathlib import Path
#|
#|import pandas as pd
#|
#|if __package__ in {None, ""}:
#|    import sys
#|
#|    REPO_ROOT = Path(__file__).resolve().parents[2]
#|    if str(REPO_ROOT) not in sys.path:
#|        sys.path.insert(0, str(REPO_ROOT))
#|    from research.prognostics.heuristic_display_registry_v1 import (
#|        DISPLAY_HEURISTIC_NAME_MAP,
#|        HEURISTIC_DISPLAY_NOTE_MAP,
#|        display_heuristic_name as shared_display_heuristic_name,
#|        display_heuristic_note as shared_display_heuristic_note,
#|    )
#|else:
#|    from .heuristic_display_registry_v1 import (
#|        DISPLAY_HEURISTIC_NAME_MAP,
#|        HEURISTIC_DISPLAY_NOTE_MAP,
#|        display_heuristic_name as shared_display_heuristic_name,
#|        display_heuristic_note as shared_display_heuristic_note,
#|    )
#|
#|
#|RUNTIME_AUDIT_OUTPUT_NAME = "panel_day_engine_runtime_fault_event_audit_v1.csv"
#|RUNTIME_AUDIT_SUMMARY_NAME = "panel_day_engine_runtime_fault_event_audit_summary_v1.csv"
#|RUNTIME_VERDICT_OUTPUT_NAME = "panel_day_engine_runtime_final_verdict_v1.csv"
#|RUNTIME_VERDICT_SUMMARY_NAME = "panel_day_engine_runtime_final_verdict_summary_v1.csv"
#|RUNTIME_HEURISTIC_OUTPUT_NAME = "panel_day_engine_runtime_cause_candidate_heuristics_v1.csv"
#|RUNTIME_HEURISTIC_SUMMARY_NAME = "panel_day_engine_runtime_cause_candidate_summary_v1.csv"
#|
#|RUNTIME_DECISION_COMPARE_COLS = [
#|    "site",
#|    "panel_id",
#|    "패널고장여부_ko",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "커널로그_원인군_ko",
#|    "1순위_의심원인_ko",
#|    "2순위_의심원인_ko",
#|    "3순위_의심원인_ko",
#|]
#|RUNTIME_FAULT_OUTPUT_COLS = [
#|    *RUNTIME_DECISION_COMPARE_COLS,
#|    "전조날짜",
#|    "고장날짜",
#|]
#|RUNTIME_PREVIEW_OUTPUT_COLS = [
#|    "site",
#|    "panel_id",
#|    "패널고장여부_ko",
#|    "사건유형_ko",
#|    "최종고장양상_ko",
#|    "전조날짜",
#|    "고장날짜",
#|    "커널로그_원인군_ko",
#|    "1순위_의심원인_ko",
#|    "2순위_의심원인_ko",
#|    "3순위_의심원인_ko",
#|    "커널로그 기존 알고리즘",
#|]
#|
#|PRIMARY_WARNING_COLS = [
#|    "ews_warning",
#|    "pre_alarm",
#|]
#|SECONDARY_WARNING_COLS = [
#|    "pre_ews",
#|    "prefault_cond_mid",
#|    "prefault_cond_ae",
#|    "prefault_cond_dtw",
#|    "prefault_cond_ews",
#|    "prealarm_cond_ae_mid_or_hi",
#|    "prealarm_cond_dtw_mid_or_hi",
#|    "prealarm_cond_hs_mid_or_hi",
#|]
#|ALL_WARNING_COLS = PRIMARY_WARNING_COLS + SECONDARY_WARNING_COLS
#|PRIMARY_WARNING_MAX_GAP_DAYS = 120
#|SECONDARY_WARNING_MIN_GAP_DAYS = 7
#|SECONDARY_WARNING_MAX_GAP_DAYS = 120
#|PREFERRED_PREFAULT_B_WARNING_COLS = ["prefault_B_effective", "prefault_B"]
#|PROXIMAL_COMMON_CAUSE_WINDOW_DAYS = 3
#|DEGRADATION_ONSET_BACKDATE_GUARD_NAME = "G1_extreme_longgap_one_day"
#|DEGRADATION_ONSET_BACKDATE_GUARD_MIN_GAP_DAYS = 30
#|DEGRADATION_ONSET_BACKDATE_GUARD_MAX_DEGRADE_DAYS = 1
#|PROMOTION_DECISION_ONSET_SIGNAL_COLS = [
#|    "signal_count",
#|    "pre_ews",
#|    "ews_warning",
#|    "pre_alarm",
#|]
#|PROMOTION_DECISION_ONSET_SIGNAL_LOOKAHEAD_DAYS = 10
#|
#|
#|@dataclass(frozen=True)
#|class PanelRuntimeMetrics:
#|    site: str
#|    panel_id: str
#|    earliest_warning_date: str
#|    earliest_warning_marker: str
#|    retrospective_onset_date: str
#|    strict_trigger_date: str
#|    first_final_fault_date: str
#|    dead_diag_date: str
#|    onset_confidence: str
#|    onset_method: str
#|    패널고장여부_ko: str
#|    전조흔적_flag: int
#|    순수급작_flag: int
#|    전조평가셋편입_flag: int
#|    급작평가셋편입_flag: int
#|    사건유형_재판정_ko: str
#|    최종고장양상_재판정_ko: str
#|    재판정_근거_ko: str
#|    현재표_보정필요여부_flag: int
#|    대표critical_source: str
#|    대표anom_level: str
#|    대표anom_subtype: str
#|    algorithm_family_ko: str
#|    algorithm_symptom_ko: str
#|    detailed_fault_code: str
#|    detailed_fault_label_ko: str
#|    gap_days: int
#|    degradation_onset_backdate_guard_flag: bool
#|    degradation_onset_backdate_guard_name: str
#|    degradation_onset_backdate_guard_reason: str
#|    degradation_onset_backdate_guard_degrade_days: int
#|    g1_suppressed_event_shadow_flag: bool
#|    g1_suppressed_event_shadow_rule_name: str
#|    g1_suppressed_event_shadow_current_onset_date: str
#|    g1_suppressed_event_shadow_strict_trigger_date: str
#|    g1_suppressed_event_shadow_current_event_type_ko: str
#|    g1_suppressed_event_shadow_current_final_pattern_ko: str
#|    g1_suppressed_event_shadow_event_type_if_applied_ko: str
#|    g1_suppressed_event_shadow_final_pattern_if_applied_ko: str
#|    g1_suppressed_event_shadow_transition_class: str
#|    g1_suppressed_event_shadow_reason: str
#|    g1_suppressed_event_guard_applied_flag: bool
#|    g1_suppressed_event_guard_apply_reason: str
#|    secondary_window_candidate_flag: bool
#|    secondary_window_selected_onset_date: str
#|    secondary_window_selected_marker: str
#|    secondary_window_selected_gap_days: int
#|    secondary_window_qualified_count: int
#|    secondary_window_too_early_count: int
#|    secondary_window_change_class: str
#|    secondary_window_review_tier: str
#|    secondary_window_reason: str
#|    promotion_decision_bucket: str
#|    promotion_decision_reason: str
#|    common_cause_anchor_date: str
#|    common_cause_anchor_kind: str
#|    has_final_fault: bool
#|    has_critical_fault: bool
#|    has_fault_like: bool
#|    has_degradation: bool
#|    has_shadow: bool
#|    has_vdrop: bool
#|    has_site_event: bool
#|    has_group_off: bool
#|    has_subgroup_common_cause: bool
#|    has_common_cause_history: bool
#|    has_strict_trigger_proximal_common_cause: bool
#|    has_warning_proximal_common_cause: bool
#|    has_trigger_proximal_common_cause: bool
#|
#|
#|def normalize_text(value: object) -> str:
#|    if value is None:
#|        return ""
#|    if isinstance(value, float) and pd.isna(value):
#|        return ""
#|    text = str(value).strip()
#|    return "" if text.lower() == "nan" else text
#|
#|
#|def truthy_mask(series: pd.Series) -> pd.Series:
#|    lowered = series.astype(str).str.strip().str.lower()
#|    return lowered.isin({"1", "true", "t", "yes"})
#|
#|
#|def read_csv(path: Path, required: bool = True) -> pd.DataFrame:
#|    if not path.exists():
#|        if required:
#|            raise SystemExit(f"missing input: {path}")
#|        return pd.DataFrame()
#|    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
#|
#|
#|def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
#|    missing = [column for column in required if column not in df.columns]
#|    if missing:
#|        raise SystemExit(f"{name} missing columns: {missing}")
#|
#|
#|def to_timestamp(value: object) -> pd.Timestamp | None:
#|    if pd.isna(value):
#|        return None
#|    ts = pd.to_datetime(value, errors="coerce")
#|    if pd.isna(ts):
#|        return None
#|    return ts.normalize()
#|
#|
#|def format_date(value: object) -> str:
#|    ts = to_timestamp(value)
#|    return "" if ts is None else ts.strftime("%Y-%m-%d")
#|
#|
#|def min_ts(values: list[pd.Timestamp | None]) -> pd.Timestamp | None:
#|    parsed = [value for value in values if value is not None]
#|    return min(parsed) if parsed else None
#|
#|
#|def first_true_date(df: pd.DataFrame, column: str) -> pd.Timestamp | None:
#|    if df.empty or column not in df.columns or "date" not in df.columns:
#|        return None
#|    working = df.loc[truthy_mask(df[column]), "date"]
#|    if working.empty:
#|        return None
#|    ts = pd.to_datetime(working, errors="coerce").dropna()
#|    return None if ts.empty else ts.min().normalize()
#|
#|
#|def true_date_set(df: pd.DataFrame, columns: list[str]) -> set[pd.Timestamp]:
#|    if df.empty or "date" not in df.columns:
#|        return set()
#|    dates: set[pd.Timestamp] = set()
#|    for column in columns:
#|        if column not in df.columns:
#|            continue
#|        working = pd.to_datetime(df.loc[truthy_mask(df[column]), "date"], errors="coerce").dropna()
#|        dates.update(pd.Timestamp(ts).normalize() for ts in working.tolist())
#|    return dates
#|
#|
#|def first_true_marker(df: pd.DataFrame, columns: list[str]) -> tuple[pd.Timestamp | None, str]:
#|    candidates: list[tuple[pd.Timestamp, str]] = []
#|    for column in columns:
#|        ts = first_true_date(df, column)
#|        if ts is not None:
#|            candidates.append((ts, column))
#|    if not candidates:
#|        return None, ""
#|    candidates.sort(key=lambda item: (item[0], item[1]))
#|    return candidates[0]
#|
#|
#|def true_marker_candidates(df: pd.DataFrame, columns: list[str]) -> list[tuple[pd.Timestamp, str]]:
#|    candidates: list[tuple[pd.Timestamp, str]] = []
#|    if df.empty or "date" not in df.columns:
#|        return candidates
#|    for column in dict.fromkeys(columns):
#|        if column not in df.columns:
#|            continue
#|        dates = pd.to_datetime(df.loc[truthy_mask(df[column]), "date"], errors="coerce").dropna()
#|        candidates.extend((pd.Timestamp(ts).normalize(), column) for ts in dates.tolist())
#|    candidates.sort(key=lambda item: (item[0], item[1]))
#|    return candidates
#|
#|
#|def first_true_marker_in_gap_window(
#|    df: pd.DataFrame,
#|    columns: list[str],
#|    strict_trigger: pd.Timestamp | None,
#|    min_gap_days: int,
#|    max_gap_days: int,
#|) -> tuple[pd.Timestamp | None, str, int, int, int]:
#|    if strict_trigger is None:
#|        return None, "", 0, 0, 0
#|
#|    qualified: list[tuple[pd.Timestamp, str, int]] = []
#|    too_early_count = 0
#|    for ts, marker in true_marker_candidates(df, columns):
#|        if ts >= strict_trigger:
#|            continue
#|        gap_days = int((strict_trigger - ts).days)
#|        if min_gap_days <= gap_days <= max_gap_days:
#|            qualified.append((ts, marker, gap_days))
#|        elif gap_days > max_gap_days:
#|            too_early_count += 1
#|
#|    if not qualified:
#|        return None, "", 0, 0, too_early_count
#|    qualified.sort(key=lambda item: (item[0], item[1]))
#|    selected_ts, selected_marker, selected_gap = qualified[0]
#|    return selected_ts, selected_marker, selected_gap, len(qualified), too_early_count
#|
#|
#|def resolve_secondary_window_warning_cols(df: pd.DataFrame) -> list[str]:
#|    prefault_col = next(
#|        (column for column in PREFERRED_PREFAULT_B_WARNING_COLS if column in df.columns),
#|        "prefault_B",
#|    )
#|    secondary_cols = [column for column in SECONDARY_WARNING_COLS if column != "prefault_B"]
#|    return list(dict.fromkeys(["pre_ews", prefault_col, *secondary_cols]))
#|
#|
#|def discover_sites(root: Path) -> list[str]:
#|    data_root = root / "data"
#|    if not data_root.exists():
#|        raise SystemExit(f"missing data root: {data_root}")
#|    sites = sorted(
#|        path.name
#|        for path in data_root.iterdir()
#|        if path.is_dir() and (path / "out" / "panel_day_core.csv").exists()
#|    )
#|    if not sites:
#|        raise SystemExit(f"no site outputs found under: {data_root}")
#|    return sites
#|
#|
#|def load_site_outputs(root: Path, site: str) -> tuple[pd.DataFrame, pd.DataFrame]:
#|    out_dir = root / "data" / site / "out"
#|    core_path = out_dir / "panel_day_core.csv"
#|    gate_path = out_dir / "ae_simple_local_precursor_gate_daily.csv"
#|    core_df = read_csv(core_path)
#|    ensure_columns(
#|        core_df,
#|        [
#|            "date",
#|            "panel_id",
#|            "critical_source",
#|            "final_fault",
#|            "critical_fault",
#|            "fault_like_day",
#|            "anom_level",
#|            "anom_subtype",
#|        ],
#|        core_path.name,
#|    )
#|    core_df["date"] = pd.to_datetime(core_df["date"], errors="coerce")
#|    core_df["panel_id"] = core_df["panel_id"].astype(str)
#|    gate_df = read_csv(gate_path, required=False)
#|    if not gate_df.empty:
#|        ensure_columns(gate_df, ["date", "panel_id"], gate_path.name)
#|        gate_df["date"] = pd.to_datetime(gate_df["date"], errors="coerce")
#|        gate_df["panel_id"] = gate_df["panel_id"].astype(str)
#|    return core_df, gate_df
#|
#|
#|def panel_keys(core_df: pd.DataFrame, gate_df: pd.DataFrame) -> list[str]:
#|    keys = set(core_df["panel_id"].astype(str).tolist())
#|    if not gate_df.empty and "panel_id" in gate_df.columns:
#|        keys.update(gate_df["panel_id"].astype(str).tolist())
#|    return sorted(key for key in keys if normalize_text(key))
#|
#|
#|def representative_row(panel_core: pd.DataFrame) -> pd.Series:
#|    final_rows = panel_core.loc[truthy_mask(panel_core["final_fault"])]
#|    critical_rows = panel_core.loc[truthy_mask(panel_core["critical_fault"])]
#|    fault_like_rows = panel_core.loc[truthy_mask(panel_core["fault_like_day"])]
#|    if not final_rows.empty:
#|        return final_rows.sort_values("date").iloc[0]
#|    if not critical_rows.empty:
#|        return critical_rows.sort_values("date").iloc[0]
#|    if not fault_like_rows.empty:
#|        return fault_like_rows.sort_values("date").iloc[0]
#|    return panel_core.sort_values("date").iloc[-1]
#|
#|
#|def subgroup_common_cause_date_set(panel_core: pd.DataFrame, panel_gate: pd.DataFrame) -> set[pd.Timestamp]:
#|    return true_date_set(panel_core, ["subgroup_common_cause_candidate"]) | true_date_set(
#|        panel_gate,
#|        ["subgroup_common_cause_candidate"],
#|    )
#|
#|
#|def panel_abnormal_date_set(panel_core: pd.DataFrame, panel_gate: pd.DataFrame) -> set[pd.Timestamp]:
#|    core_dates = true_date_set(
#|        panel_core,
#|        [
#|            "degraded_candidate",
#|            "fault_like_day",
#|            "critical_fault",
#|            "final_fault",
#|            "shadow_like",
#|            "group_off_like",
#|        ],
#|    )
#|    gate_dates = true_date_set(
#|        panel_gate,
#|        [
#|            "ews_warning",
#|            "pre_alarm",
#|            "pre_ews",
#|            "prefault_B",
#|            "prefault_B_effective",
#|            "prefault_B_common_cause_overlap",
#|        ],
#|    )
#|    return core_dates | gate_dates
#|
#|
#|def count_degradation_days_between(
#|    panel_core: pd.DataFrame,
#|    onset: pd.Timestamp | None,
#|    strict_trigger: pd.Timestamp | None,
#|) -> int:
#|    if onset is None or strict_trigger is None or panel_core.empty or "date" not in panel_core.columns:
#|        return 0
#|
#|    dates = pd.to_datetime(panel_core["date"], errors="coerce")
#|    window_mask = dates.notna() & dates.ge(onset) & dates.le(strict_trigger)
#|    if not window_mask.any():
#|        return 0
#|
#|    degrade_mask = pd.Series(False, index=panel_core.index)
#|    if "degraded_candidate" in panel_core.columns:
#|        degrade_mask = truthy_mask(panel_core["degraded_candidate"])
#|    subtype_mask = pd.Series(False, index=panel_core.index)
#|    if "anom_subtype" in panel_core.columns:
#|        subtype_mask = panel_core["anom_subtype"].astype(str).str.contains("degradation", case=False, na=False)
#|
#|    matched_dates = dates.loc[window_mask & (degrade_mask | subtype_mask)].dt.normalize().dropna()
#|    return int(matched_dates.nunique())
#|
#|
#|def count_onset_window_signal_days(
#|    panel_gate: pd.DataFrame,
#|    onset: pd.Timestamp | None,
#|    strict_trigger: pd.Timestamp | None,
#|) -> int:
#|    if onset is None or strict_trigger is None or panel_gate.empty or "date" not in panel_gate.columns:
#|        return 0
#|
#|    dates = pd.to_datetime(panel_gate["date"], errors="coerce")
#|    window_end = min(strict_trigger, onset + pd.Timedelta(days=PROMOTION_DECISION_ONSET_SIGNAL_LOOKAHEAD_DAYS))
#|    window_mask = dates.notna() & dates.ge(onset) & dates.le(window_end)
#|    if not window_mask.any():
#|        return 0
#|
#|    matched_dates: set[pd.Timestamp] = set()
#|    for column in PROMOTION_DECISION_ONSET_SIGNAL_COLS:
#|        if column not in panel_gate.columns:
#|            continue
#|        if column == "signal_count":
#|            signal_mask = pd.to_numeric(panel_gate[column], errors="coerce").fillna(0).gt(0)
#|        else:
#|            signal_mask = truthy_mask(panel_gate[column])
#|        signal_dates = dates.loc[window_mask & signal_mask].dt.normalize().dropna()
#|        matched_dates.update(pd.Timestamp(ts).normalize() for ts in signal_dates.tolist())
#|    return len(matched_dates)
#|
#|
#|def classify_promotion_decision_bucket(
#|    *,
#|    degradation_guard_flag: bool,
#|    secondary_window_change_class: str,
#|    secondary_window_review_tier: str,
#|    secondary_window_selected_marker: str,
#|    onset_window_signal_days: int,
#|) -> tuple[str, str]:
#|    if degradation_guard_flag:
#|        return (
#|            "backdate_suppression_candidate",
#|            "BR008: G1 degradation backdate guard candidate; shadow suppression review only",
#|        )
#|
#|    if secondary_window_review_tier in {"audit_provenance_only", "audit_no_event_flip"}:
#|        return (
#|            "audit_provenance_only",
#|            f"BR008: {secondary_window_review_tier}; audit/provenance only and no event flip",
#|        )
#|
#|    if secondary_window_change_class != "trigger_only_to_precursor":
#|        return "", ""
#|
#|    if secondary_window_review_tier == "review_persistent_secondary_only":
#|        return (
#|            "blocked_cluster_risk",
#|            "BR008: persistent secondary-only candidate; blocked from promotion by cluster false-positive risk",
#|        )
#|
#|    if secondary_window_review_tier == "review_supported_context":
#|        if secondary_window_selected_marker == "prealarm_cond_dtw_mid_or_hi" and onset_window_signal_days == 0:
#|            return (
#|                "hold_shadow_only",
#|                "BR008: supported context exists, but selected onset is DTW prealarm with zero independent onset-window signal",
#|            )
#|        return (
#|            "manual_review",
#|            "BR008: supported context requires raw/audit review before any operator-facing promotion",
#|        )
#|
#|    if secondary_window_review_tier.startswith("review_"):
#|        return (
#|            "manual_review",
#|            "BR008: trigger-only precursor candidate lacks hard promotion support",
#|        )
#|
#|    return "", ""
#|
#|
#|def first_available_anchor(
#|    strict_trigger: pd.Timestamp | None,
#|    earliest_warning: pd.Timestamp | None,
#|    retrospective_onset: pd.Timestamp | None,
#|) -> tuple[pd.Timestamp | None, str]:
#|    if strict_trigger is not None:
#|        return strict_trigger, "strict_trigger"
#|    if earliest_warning is not None:
#|        return earliest_warning, "earliest_warning"
#|    if retrospective_onset is not None:
#|        return retrospective_onset, "retrospective_onset"
#|    return None, ""
#|
#|
#|def choose_algorithm_family(
#|    representative_source: str,
#|    representative_subtype: str,
#|    event_type_ko: str,
#|    has_final_fault: bool,
#|    has_critical_fault: bool,
#|    has_degradation: bool,
#|    has_shadow: bool,
#|) -> tuple[str, str, str, str]:
#|    if event_type_ko != "전조형 고장" and event_type_ko != "급작 고장":
#|        return "", "", "", ""
#|
#|    if has_degradation and event_type_ko == "전조형 고장" and not has_final_fault:
#|        return ("모듈손상형", "출력 저하형", "RAW_MODULE_PROGRESSIVE", "알고리즘상 진행성 열화 계열")
#|    if representative_source == "legacy":
#|        return ("개방/장치이상형", "전압 변화형", "RAW_OPEN_LEGACY", "알고리즘상 legacy/open 계열")
#|    if representative_source == "none" and has_final_fault and not has_critical_fault:
#|        return ("개방/장치이상형", "전압 변화형", "RAW_OPEN_NOCRIT", "확정고장이지만 vdrop/critical 증거가 약한 계열")
#|    if representative_source in {"vdrop", "vdrop_suspect"} or "vdrop" in representative_subtype:
#|        return ("다이오드형", "전압 변화형", "RAW_DIODE_VDROP", "알고리즘상 vdrop 계열")
#|    if has_shadow and event_type_ko == "전조형 고장":
#|        return ("모듈손상형", "출력 저하형", "RAW_MODULE_SHADOW", "그림자/열화 진행 계열")
#|    return ("불충분", "불충분", "RAW_UNCERTAIN", "raw-only family 신뢰도가 충분치 않음")
#|
#|
#|def compute_panel_metrics(
#|    site: str,
#|    panel_id: str,
#|    core_df: pd.DataFrame,
#|    gate_df: pd.DataFrame,
#|) -> PanelRuntimeMetrics:
#|    panel_core = core_df.loc[core_df["panel_id"].eq(panel_id)].copy().sort_values("date")
#|    if panel_core.empty:
#|        raise SystemExit(f"panel core rows must not be empty: {(site, panel_id)}")
#|    panel_gate = gate_df.loc[gate_df["panel_id"].eq(panel_id)].copy().sort_values("date") if not gate_df.empty else pd.DataFrame()
#|
#|    first_final_fault = first_true_date(panel_core, "final_fault")
#|    first_critical_fault = first_true_date(panel_core, "critical_fault")
#|    first_fault_like = first_true_date(panel_core, "fault_like_day")
#|    strict_trigger = min_ts([first_critical_fault, first_final_fault, first_fault_like])
#|    first_primary_warning, first_primary_marker = first_true_marker(panel_gate, PRIMARY_WARNING_COLS)
#|    first_secondary_warning, first_secondary_marker = first_true_marker(panel_gate, SECONDARY_WARNING_COLS)
#|    (
#|        secondary_window_onset,
#|        secondary_window_marker,
#|        secondary_window_gap_days,
#|        secondary_window_qualified_count,
#|        secondary_window_too_early_count,
#|    ) = first_true_marker_in_gap_window(
#|        panel_gate,
#|        resolve_secondary_window_warning_cols(panel_gate),
#|        strict_trigger,
#|        SECONDARY_WARNING_MIN_GAP_DAYS,
#|        SECONDARY_WARNING_MAX_GAP_DAYS,
#|    )
#|
#|    has_degradation = panel_core["anom_subtype"].astype(str).str.contains("degradation", case=False, na=False).any()
#|    has_shadow = panel_core["anom_subtype"].astype(str).str.contains("shadow", case=False, na=False).any()
#|    representative = representative_row(panel_core)
#|    representative_source = normalize_text(representative.get("critical_source"))
#|    representative_level = normalize_text(representative.get("anom_level"))
#|    representative_subtype = normalize_text(representative.get("anom_subtype"))
#|    has_vdrop = representative_source in {"vdrop", "vdrop_suspect"} or "vdrop" in representative_subtype
#|    abnormal_dates = panel_abnormal_date_set(panel_core, panel_gate)
#|    site_event_dates = true_date_set(panel_gate, ["site_event_soft", "site_event_hard"])
#|    site_event_overlap_dates = abnormal_dates & site_event_dates
#|    group_off_overlap_dates = abnormal_dates & (
#|        true_date_set(panel_core, ["group_off_date", "group_off_like"])
#|        | true_date_set(panel_gate, ["group_off_date", "group_off_like"])
#|    )
#|    has_group_off = (
#|        (not panel_gate.empty and first_true_date(panel_gate, "group_off_date") is not None)
#|        or panel_core["anom_level"].astype(str).str.contains("group_off", case=False, na=False).any()
#|    )
#|    subgroup_common_cause_dates = subgroup_common_cause_date_set(panel_core, panel_gate)
#|    has_site_event = bool(site_event_overlap_dates)
#|    has_subgroup_common_cause = bool(subgroup_common_cause_dates)
#|    common_cause_dates = site_event_overlap_dates | group_off_overlap_dates | subgroup_common_cause_dates
#|    has_common_cause_history = bool(common_cause_dates)
#|
#|    earliest_warning = first_primary_warning
#|    earliest_marker = first_primary_marker
#|    if earliest_warning is None:
#|        earliest_warning = first_secondary_warning
#|        earliest_marker = first_secondary_marker
#|
#|    retrospective_onset = None
#|    primary_gap_days = (
#|        (strict_trigger - first_primary_warning).days
#|        if strict_trigger is not None and first_primary_warning is not None
#|        else None
#|    )
#|    secondary_gap_days = (
#|        (strict_trigger - first_secondary_warning).days
#|        if strict_trigger is not None and first_secondary_warning is not None
#|        else None
#|    )
#|    primary_warning_accepted = (
#|        first_primary_warning is not None
#|        and strict_trigger is not None
#|        and first_primary_warning < strict_trigger
#|        and primary_gap_days is not None
#|        and primary_gap_days <= PRIMARY_WARNING_MAX_GAP_DAYS
#|    )
#|    if strict_trigger is not None:
#|        if primary_warning_accepted:
#|            retrospective_onset = first_primary_warning
#|        elif (
#|            first_secondary_warning is not None
#|            and first_secondary_warning < strict_trigger
#|            and secondary_gap_days is not None
#|            and SECONDARY_WARNING_MIN_GAP_DAYS <= secondary_gap_days <= SECONDARY_WARNING_MAX_GAP_DAYS
#|        ):
#|            retrospective_onset = first_secondary_warning
#|        elif has_degradation:
#|            degradation_rows = panel_core.loc[
#|                panel_core["anom_subtype"].astype(str).str.contains("degradation", case=False, na=False)
#|            ]
#|            if not degradation_rows.empty:
#|                degradation_ts = to_timestamp(degradation_rows.iloc[0]["date"])
#|                if degradation_ts is not None and degradation_ts <= strict_trigger:
#|                    retrospective_onset = degradation_ts
#|                    earliest_marker = "anom_subtype:degradation"
#|
#|    has_final = first_final_fault is not None
#|    has_critical = first_critical_fault is not None
#|    has_fault_like = first_fault_like is not None
#|
#|    if has_final or has_critical or has_fault_like:
#|        fault_status = "고장"
#|    elif earliest_warning is not None:
#|        fault_status = "미확정"
#|    else:
#|        fault_status = "비고장"
#|
#|    gap_days = 0
#|    if retrospective_onset is not None and strict_trigger is not None:
#|        gap_days = max(int((strict_trigger - retrospective_onset).days), 0)
#|
#|    degradation_guard_degrade_days = count_degradation_days_between(
#|        panel_core,
#|        retrospective_onset,
#|        strict_trigger,
#|    )
#|    degradation_guard_flag = (
#|        earliest_marker == "anom_subtype:degradation"
#|        and gap_days >= DEGRADATION_ONSET_BACKDATE_GUARD_MIN_GAP_DAYS
#|        and degradation_guard_degrade_days <= DEGRADATION_ONSET_BACKDATE_GUARD_MAX_DEGRADE_DAYS
#|    )
#|    degradation_guard_reason = ""
#|    if degradation_guard_flag:
#|        degradation_guard_reason = (
#|            f"{DEGRADATION_ONSET_BACKDATE_GUARD_NAME}: "
#|            f"onset_method=anom_subtype:degradation, gap_days>="
#|            f"{DEGRADATION_ONSET_BACKDATE_GUARD_MIN_GAP_DAYS}, "
#|            f"degrade_days_between_onset_and_strict<="
#|            f"{DEGRADATION_ONSET_BACKDATE_GUARD_MAX_DEGRADE_DAYS}"
#|        )
#|
#|    common_cause_anchor_ts, common_cause_anchor_kind = first_available_anchor(
#|        strict_trigger,
#|        earliest_warning,
#|        retrospective_onset,
#|    )
#|    has_strict_trigger_proximal_common_cause = False
#|    has_warning_proximal_common_cause = False
#|    has_trigger_proximal_common_cause = False
#|    if common_cause_dates:
#|        if strict_trigger is not None:
#|            has_strict_trigger_proximal_common_cause = any(
#|                abs(int((date - strict_trigger).days)) <= PROXIMAL_COMMON_CAUSE_WINDOW_DAYS
#|                for date in common_cause_dates
#|            )
#|        if earliest_warning is not None:
#|            has_warning_proximal_common_cause = any(
#|                abs(int((date - earliest_warning).days)) <= PROXIMAL_COMMON_CAUSE_WINDOW_DAYS
#|                for date in common_cause_dates
#|            )
#|        if common_cause_anchor_ts is not None:
#|            has_trigger_proximal_common_cause = any(
#|                abs(int((date - common_cause_anchor_ts).days)) <= PROXIMAL_COMMON_CAUSE_WINDOW_DAYS
#|                for date in common_cause_dates
#|            )
#|    has_trigger_proximal_common_cause = (
#|        has_trigger_proximal_common_cause
#|        or has_strict_trigger_proximal_common_cause
#|        or has_warning_proximal_common_cause
#|    )
#|
#|    precursor_flag = int(fault_status == "고장" and retrospective_onset is not None)
#|    abrupt_flag = int(fault_status == "고장" and not precursor_flag)
#|    precursor_eval_flag = precursor_flag
#|    abrupt_eval_flag = abrupt_flag
#|
#|    if fault_status != "고장":
#|        event_type = ""
#|        terminal_pattern = ""
#|        onset_confidence = ""
#|        onset_method = ""
#|        current_needs_correction = 0
#|    elif precursor_flag:
#|        event_type = "전조형 고장"
#|        if has_degradation or not has_final or (has_vdrop and gap_days >= 7):
#|            terminal_pattern = "진행성 악화"
#|        else:
#|            terminal_pattern = "급격 종료"
#|        if gap_days >= 14:
#|            onset_confidence = "high"
#|        elif gap_days >= 3:
#|            onset_confidence = "medium"
#|        else:
#|            onset_confidence = "low"
#|        onset_method = earliest_marker or "runtime_precursor_gate"
#|        current_needs_correction = 1
#|    else:
#|        event_type = "급작 고장"
#|        terminal_pattern = "급작 발생"
#|        onset_confidence = "low"
#|        onset_method = "runtime_trigger_only"
#|        current_needs_correction = 0
#|
#|    g1_shadow_flag = degradation_guard_flag and fault_status == "고장" and strict_trigger is not None
#|    g1_shadow_event_type = "급작 고장" if g1_shadow_flag else ""
#|    g1_shadow_final_pattern = "급작 발생" if g1_shadow_flag else ""
#|    g1_shadow_current_onset_date = format_date(retrospective_onset) if g1_shadow_flag else ""
#|    g1_shadow_current_event_type = event_type if g1_shadow_flag else ""
#|    g1_shadow_current_final_pattern = terminal_pattern if g1_shadow_flag else ""
#|    g1_shadow_transition_class = ""
#|    g1_shadow_reason = ""
#|    if g1_shadow_flag:
#|        g1_shadow_transition_class = f"{g1_shadow_current_event_type} -> {g1_shadow_event_type}"
#|        g1_shadow_reason = (
#|            "BR013: audit-only G1 suppressed-event shadow; suppress extreme long-gap "
#|            "one-day degradation onset while keeping strict trigger as event anchor"
#|        )
#|
#|    secondary_window_candidate_flag = (
#|        strict_trigger is not None
#|        and not primary_warning_accepted
#|        and secondary_window_onset is not None
#|        and (
#|            format_date(secondary_window_onset) != format_date(retrospective_onset)
#|            or secondary_window_marker != onset_method
#|            or onset_method == "runtime_trigger_only"
#|        )
#|    )
#|    secondary_window_change_class = ""
#|    if secondary_window_candidate_flag:
#|        selected_onset_date = format_date(secondary_window_onset)
#|        current_onset_date = format_date(retrospective_onset)
#|        if (
#|            event_type == "전조형 고장"
#|            and selected_onset_date == current_onset_date
#|            and secondary_window_marker != onset_method
#|        ):
#|            secondary_window_change_class = "method_provenance_only_primary_marker_mismatch"
#|        elif onset_method == "anom_subtype:degradation":
#|            secondary_window_change_class = (
#|                "g1_degradation_fallback_replaced_by_secondary"
#|                if degradation_guard_flag
#|                else "degradation_fallback_replaced_by_secondary"
#|            )
#|        elif onset_method == "runtime_trigger_only" and fault_status == "고장":
#|            secondary_window_change_class = "trigger_only_to_precursor"
#|        elif event_type == "전조형 고장" and selected_onset_date != current_onset_date:
#|            secondary_window_change_class = "onset_date_shift_without_event_flip"
#|        else:
#|            secondary_window_change_class = "secondary_window_candidate"
#|
#|    secondary_window_review_tier = ""
#|    if secondary_window_change_class == "trigger_only_to_precursor":
#|        if has_strict_trigger_proximal_common_cause or has_site_event or has_subgroup_common_cause:
#|            secondary_window_review_tier = "review_supported_context"
#|        elif secondary_window_qualified_count >= 30:
#|            secondary_window_review_tier = "review_persistent_secondary_only"
#|        else:
#|            secondary_window_review_tier = "review_sparse_secondary_only"
#|    elif secondary_window_change_class == "method_provenance_only_primary_marker_mismatch":
#|        secondary_window_review_tier = "audit_provenance_only"
#|    elif secondary_window_change_class:
#|        secondary_window_review_tier = "audit_no_event_flip"
#|
#|    secondary_window_reason = ""
#|    if secondary_window_candidate_flag:
#|        secondary_window_reason = (
#|            "BR004_secondary_warning_window_shadow: "
#|            f"first_secondary_gap_days={secondary_gap_days if secondary_gap_days is not None else ''}, "
#|            f"selected_gap_days={secondary_window_gap_days}, "
#|            f"qualified_secondary_count={secondary_window_qualified_count}, "
#|            f"too_early_secondary_count={secondary_window_too_early_count}, "
#|            f"change_class={secondary_window_change_class}, "
#|            f"review_tier={secondary_window_review_tier}"
#|        )
#|
#|    onset_window_signal_days = count_onset_window_signal_days(
#|        panel_gate,
#|        secondary_window_onset,
#|        strict_trigger,
#|    )
#|    promotion_decision_bucket, promotion_decision_reason = classify_promotion_decision_bucket(
#|        degradation_guard_flag=degradation_guard_flag,
#|        secondary_window_change_class=secondary_window_change_class,
#|        secondary_window_review_tier=secondary_window_review_tier,
#|        secondary_window_selected_marker=secondary_window_marker,
#|        onset_window_signal_days=onset_window_signal_days,
#|    )
#|
#|    algorithm_family, algorithm_symptom, detailed_code, detailed_label = choose_algorithm_family(
#|        representative_source=representative_source,
#|        representative_subtype=representative_subtype,
#|        event_type_ko=event_type,
#|        has_final_fault=has_final,
#|        has_critical_fault=has_critical,
#|        has_degradation=has_degradation,
#|        has_shadow=has_shadow,
#|    )
#|
#|    g1_guard_applied_flag = g1_shadow_flag and has_strict_trigger_proximal_common_cause
#|    g1_guard_apply_reason = ""
#|    if g1_guard_applied_flag:
#|        event_type = g1_shadow_event_type
#|        terminal_pattern = g1_shadow_final_pattern
#|        precursor_flag = 0
#|        abrupt_flag = 1
#|        precursor_eval_flag = 0
#|        abrupt_eval_flag = 1
#|        retrospective_onset = None
#|        earliest_warning = None
#|        earliest_marker = ""
#|        onset_method = "runtime_trigger_only"
#|        onset_confidence = "low"
#|        current_needs_correction = 0
#|        g1_guard_apply_reason = (
#|            "BR016: applied strict-proximal-supported G1 guard; "
#|            "one-day long-gap degradation onset suppressed from operator-facing event semantics"
#|        )
#|
#|    evidence_bits: list[str] = []
#|    if earliest_marker:
#|        evidence_bits.append(f"warning={earliest_marker}")
#|    if representative_source:
#|        evidence_bits.append(f"critical_source={representative_source}")
#|    if representative_subtype:
#|        evidence_bits.append(f"anom_subtype={representative_subtype}")
#|    if g1_guard_applied_flag:
#|        evidence_bits.append(f"g1_suppressed_backdate_gap_days={gap_days}")
#|    elif gap_days:
#|        evidence_bits.append(f"precursor_gap_days={gap_days}")
#|    if has_site_event:
#|        evidence_bits.append("site_event_signal=1")
#|    if has_group_off:
#|        evidence_bits.append("group_off_signal=1")
#|    if g1_guard_applied_flag:
#|        evidence_bits.append("g1_guard_applied=1")
#|
#|    return PanelRuntimeMetrics(
#|        site=site,
#|        panel_id=panel_id,
#|        earliest_warning_date=format_date(earliest_warning),
#|        earliest_warning_marker=earliest_marker,
#|        retrospective_onset_date=format_date(retrospective_onset),
#|        strict_trigger_date=format_date(strict_trigger),
#|        first_final_fault_date=format_date(first_final_fault),
#|        dead_diag_date=format_date(first_true_date(panel_gate, "group_off_date")),
#|        onset_confidence=onset_confidence,
#|        onset_method=onset_method,
#|        패널고장여부_ko=fault_status,
#|        전조흔적_flag=precursor_flag,
#|        순수급작_flag=abrupt_flag,
#|        전조평가셋편입_flag=precursor_eval_flag,
#|        급작평가셋편입_flag=abrupt_eval_flag,
#|        사건유형_재판정_ko=event_type,
#|        최종고장양상_재판정_ko=terminal_pattern,
#|        재판정_근거_ko="; ".join(evidence_bits),
#|        현재표_보정필요여부_flag=current_needs_correction,
#|        대표critical_source=representative_source,
#|        대표anom_level=representative_level,
#|        대표anom_subtype=representative_subtype,
#|        algorithm_family_ko=algorithm_family,
#|        algorithm_symptom_ko=algorithm_symptom,
#|        detailed_fault_code=detailed_code,
#|        detailed_fault_label_ko=detailed_label,
#|        gap_days=gap_days,
#|        degradation_onset_backdate_guard_flag=degradation_guard_flag,
#|        degradation_onset_backdate_guard_name=(
#|            DEGRADATION_ONSET_BACKDATE_GUARD_NAME if degradation_guard_flag else ""
#|        ),
#|        degradation_onset_backdate_guard_reason=degradation_guard_reason,
#|        degradation_onset_backdate_guard_degrade_days=degradation_guard_degrade_days,
#|        g1_suppressed_event_shadow_flag=g1_shadow_flag,
#|        g1_suppressed_event_shadow_rule_name=(
#|            DEGRADATION_ONSET_BACKDATE_GUARD_NAME if g1_shadow_flag else ""
#|        ),
#|        g1_suppressed_event_shadow_current_onset_date=(
#|            g1_shadow_current_onset_date
#|        ),
#|        g1_suppressed_event_shadow_strict_trigger_date=(
#|            format_date(strict_trigger) if g1_shadow_flag else ""
#|        ),
#|        g1_suppressed_event_shadow_current_event_type_ko=g1_shadow_current_event_type,
#|        g1_suppressed_event_shadow_current_final_pattern_ko=(
#|            g1_shadow_current_final_pattern
#|        ),
#|        g1_suppressed_event_shadow_event_type_if_applied_ko=g1_shadow_event_type,
#|        g1_suppressed_event_shadow_final_pattern_if_applied_ko=g1_shadow_final_pattern,
#|        g1_suppressed_event_shadow_transition_class=g1_shadow_transition_class,
#|        g1_suppressed_event_shadow_reason=g1_shadow_reason,
#|        g1_suppressed_event_guard_applied_flag=g1_guard_applied_flag,
#|        g1_suppressed_event_guard_apply_reason=g1_guard_apply_reason,
#|        secondary_window_candidate_flag=secondary_window_candidate_flag,
#|        secondary_window_selected_onset_date=(
#|            format_date(secondary_window_onset) if secondary_window_candidate_flag else ""
#|        ),
#|        secondary_window_selected_marker=secondary_window_marker if secondary_window_candidate_flag else "",
#|        secondary_window_selected_gap_days=(
#|            secondary_window_gap_days if secondary_window_candidate_flag else 0
#|        ),
#|        secondary_window_qualified_count=secondary_window_qualified_count,
#|        secondary_window_too_early_count=secondary_window_too_early_count,
#|        secondary_window_change_class=secondary_window_change_class,
#|        secondary_window_review_tier=secondary_window_review_tier,
#|        secondary_window_reason=secondary_window_reason,
#|        promotion_decision_bucket=promotion_decision_bucket,
#|        promotion_decision_reason=promotion_decision_reason,
#|        common_cause_anchor_date=format_date(common_cause_anchor_ts),
#|        common_cause_anchor_kind=common_cause_anchor_kind,
#|        has_final_fault=has_final,
#|        has_critical_fault=has_critical,
#|        has_fault_like=has_fault_like,
#|        has_degradation=has_degradation,
#|        has_shadow=has_shadow,
#|        has_vdrop=has_vdrop,
#|        has_site_event=has_site_event,
#|        has_group_off=has_group_off,
#|        has_subgroup_common_cause=has_subgroup_common_cause,
#|        has_common_cause_history=has_common_cause_history,
#|        has_strict_trigger_proximal_common_cause=has_strict_trigger_proximal_common_cause,
#|        has_warning_proximal_common_cause=has_warning_proximal_common_cause,
#|        has_trigger_proximal_common_cause=has_trigger_proximal_common_cause,
#|    )
#|
#|
#|def display_heuristic_name(value: object) -> str:
#|    return shared_display_heuristic_name(value)
#|
#|
#|def display_heuristic_note(value: object) -> str:
#|    return shared_display_heuristic_note(value)
#|
#|
#|def display_family_name(value: object) -> str:
#|    text = normalize_text(value)
#|    if text == "불충분":
#|        return ""
#|    return text
#|
#|
#|def choose_display_precursor_date(
#|    event_type_ko: object,
#|    interpreted_onset_date: object,
#|    first_warning_date: object,
#|) -> str:
#|    if normalize_text(event_type_ko) != "전조형 고장":
#|        return ""
#|    onset_date = normalize_text(interpreted_onset_date)
#|    if onset_date:
#|        return onset_date
#|    return normalize_text(first_warning_date)
#|
#|
#|def choose_display_fault_date(
#|    fault_date: object,
#|    strict_trigger_date: object,
#|    first_final_fault_date: object,
#|) -> str:
#|    for candidate in [fault_date, strict_trigger_date, first_final_fault_date]:
#|        text = normalize_text(candidate)
#|        if text:
#|            return text
#|    return ""
#|
#|
#|def load_runtime_core_from_workspace(workspace_root: Path, site: str) -> pd.DataFrame:
#|    core_path = workspace_root / "data" / site / "out" / "panel_day_core.csv"
#|    core_df = read_csv(core_path)
#|    ensure_columns(
#|        core_df,
#|        ["panel_id", "date", "final_fault", "critical_fault", "fault_like_day", "critical_source"],
#|        core_path.name,
#|    )
#|    core_df["panel_id"] = core_df["panel_id"].astype(str)
#|    core_df["date"] = pd.to_datetime(core_df["date"], errors="coerce")
#|    return core_df
#|
#|
#|def representative_algorithm_fields(core_df: pd.DataFrame, panel_id: str) -> dict[str, str]:
#|    panel_df = core_df.loc[core_df["panel_id"].eq(str(panel_id))].copy().sort_values("date")
#|    if panel_df.empty:
#|        return {"커널로그 기존 알고리즘": ""}
#|    representative = representative_row(panel_df)
#|    return {"커널로그 기존 알고리즘": normalize_text(representative.get("critical_source"))}
#|
#|
#|def build_fault_table_from_outputs(
#|    workspace_root: Path,
#|    verdict_name: str,
#|    heuristic_name: str,
#|) -> pd.DataFrame:
#|    verdict_path = workspace_root / "_share" / verdict_name
#|    heuristic_path = workspace_root / "_share" / heuristic_name
#|    audit_path = workspace_root / "_share" / RUNTIME_AUDIT_OUTPUT_NAME
#|    verdict_df = read_csv(verdict_path)
#|    heuristic_df = read_csv(heuristic_path)
#|    audit_df = read_csv(audit_path)
#|    ensure_columns(
#|        verdict_df,
#|        ["site", "panel_id", "패널고장여부_ko", "사건유형_ko", "최종고장양상_ko", "커널로그_원인군_ko"],
#|        verdict_path.name,
#|    )
#|    ensure_columns(
#|        heuristic_df,
#|        ["site", "panel_id", "원인후보_top1_ko", "원인후보_top2_ko", "원인후보_top3_ko"],
#|        heuristic_path.name,
#|    )
#|    ensure_columns(
#|        audit_df,
#|        ["site", "panel_id", "earliest_warning_date", "strict_trigger_date", "first_final_fault_date"],
#|        audit_path.name,
#|    )
#|    heuristic_lookup = {
#|        (normalize_text(row["site"]), normalize_text(row["panel_id"])): row
#|        for row in heuristic_df.to_dict(orient="records")
#|    }
#|    audit_lookup = {
#|        (normalize_text(row["site"]), normalize_text(row["panel_id"])): row
#|        for row in audit_df.to_dict(orient="records")
#|    }
#|    rows: list[dict[str, str]] = []
#|    fault_rows = verdict_df.loc[verdict_df["패널고장여부_ko"].map(normalize_text).eq("고장")].copy()
#|    for row in fault_rows.to_dict(orient="records"):
#|        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
#|        heuristic_row = heuristic_lookup.get(key)
#|        if heuristic_row is None:
#|            raise SystemExit(f"missing heuristic row for runtime fault panel: {key}")
#|        audit_row = audit_lookup.get(key, {})
#|        rows.append(
#|            {
#|                "site": key[0],
#|                "panel_id": key[1],
#|                "패널고장여부_ko": normalize_text(row["패널고장여부_ko"]),
#|                "사건유형_ko": normalize_text(row["사건유형_ko"]),
#|                "최종고장양상_ko": normalize_text(row["최종고장양상_ko"]),
#|                "커널로그_원인군_ko": display_family_name(row["커널로그_원인군_ko"]),
#|                "1순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top1_ko"]),
#|                "2순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top2_ko"]),
#|                "3순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top3_ko"]),
#|                "전조날짜": choose_display_precursor_date(
#|                    event_type_ko=row.get("사건유형_ko"),
#|                    interpreted_onset_date=row.get("사건해석상전조시작일"),
#|                    first_warning_date=audit_row.get("earliest_warning_date"),
#|                ),
#|                "고장날짜": choose_display_fault_date(
#|                    fault_date=row.get("세부fault_기준일"),
#|                    strict_trigger_date=audit_row.get("strict_trigger_date"),
#|                    first_final_fault_date=audit_row.get("first_final_fault_date"),
#|                ),
#|            }
#|        )
#|    return pd.DataFrame(rows).reindex(columns=RUNTIME_FAULT_OUTPUT_COLS).sort_values(["site", "panel_id"]).reset_index(drop=True)
#|
#|
#|def build_fault_preview(workspace_root: Path, fault_df: pd.DataFrame) -> pd.DataFrame:
#|    per_site_core = {
#|        site: load_runtime_core_from_workspace(workspace_root, site)
#|        for site in sorted(fault_df["site"].astype(str).unique())
#|    }
#|    rows: list[dict[str, str]] = []
#|    for _, row in fault_df.iterrows():
#|        site = normalize_text(row["site"])
#|        panel_id = normalize_text(row["panel_id"])
#|        rows.append(
#|            {
#|                "site": site,
#|                "panel_id": panel_id,
#|                "패널고장여부_ko": normalize_text(row["패널고장여부_ko"]),
#|                "사건유형_ko": normalize_text(row["사건유형_ko"]),
#|                "최종고장양상_ko": normalize_text(row["최종고장양상_ko"]),
#|                "전조날짜": normalize_text(row.get("전조날짜")),
#|                "고장날짜": normalize_text(row.get("고장날짜")),
#|                "커널로그_원인군_ko": display_family_name(row["커널로그_원인군_ko"]),
#|                "1순위_의심원인_ko": normalize_text(row["1순위_의심원인_ko"]),
#|                "2순위_의심원인_ko": normalize_text(row["2순위_의심원인_ko"]),
#|                "3순위_의심원인_ko": normalize_text(row["3순위_의심원인_ko"]),
#|                **representative_algorithm_fields(per_site_core[site], panel_id),
#|            }
#|        )
#|    return pd.DataFrame(rows).reindex(columns=RUNTIME_PREVIEW_OUTPUT_COLS)
#|
#|
#|def compare_fault_table_to_reference(fault_df: pd.DataFrame, reference_path: Path) -> dict[str, object]:
#|    payload = {
#|        "reference_path": str(reference_path),
#|        "reference_available": reference_path.exists(),
#|        "exact_match": False,
#|        "row_key_match": False,
#|        "decision_columns_match": False,
#|        "overlap_decision_columns_match": False,
#|        "overlap_exact_match": False,
#|        "reference_row_count": 0,
#|        "candidate_row_count": int(len(fault_df)),
#|        "matched_row_key_count": 0,
#|        "diff_columns": [],
#|        "overlap_diff_columns": [],
#|    }
#|    if not reference_path.exists():
#|        return payload
#|    reference_df = read_csv(reference_path).sort_values(["site", "panel_id"]).reset_index(drop=True)
#|    candidate_df = fault_df.sort_values(["site", "panel_id"]).reset_index(drop=True)
#|    reference_keys = list(zip(reference_df["site"].astype(str), reference_df["panel_id"].astype(str)))
#|    candidate_keys = list(zip(candidate_df["site"].astype(str), candidate_df["panel_id"].astype(str)))
#|    payload["reference_row_count"] = int(len(reference_df))
#|    payload["candidate_row_count"] = int(len(candidate_df))
#|    payload["row_key_match"] = reference_keys == candidate_keys
#|    payload["matched_row_key_count"] = int(len(set(reference_keys) & set(candidate_keys)))
#|    diff_columns: list[str] = []
#|    if len(reference_df) != len(candidate_df):
#|        diff_columns.append("__row_count__")
#|    else:
#|        for column in RUNTIME_DECISION_COMPARE_COLS:
#|            if column not in reference_df.columns:
#|                diff_columns.append(f"missing_reference:{column}")
#|                continue
#|            left = reference_df[column].fillna("").astype(str)
#|            right = candidate_df[column].fillna("").astype(str)
#|            if not left.equals(right):
#|                diff_columns.append(column)
#|    payload["diff_columns"] = diff_columns
#|    payload["exact_match"] = not diff_columns and payload["row_key_match"]
#|    decision_columns = ["패널고장여부_ko", "사건유형_ko", "최종고장양상_ko"]
#|    payload["decision_columns_match"] = payload["row_key_match"] and not any(
#|        column in diff_columns for column in decision_columns
#|    )
#|    overlap = reference_df.merge(candidate_df, on=["site", "panel_id"], how="inner", suffixes=("_reference", "_candidate"))
#|    overlap_diff_columns: list[str] = []
#|    if not overlap.empty:
#|        for column in RUNTIME_DECISION_COMPARE_COLS[2:]:
#|            left = overlap[f"{column}_reference"].fillna("").astype(str)
#|            right = overlap[f"{column}_candidate"].fillna("").astype(str)
#|            if not left.equals(right):
#|                overlap_diff_columns.append(column)
#|    payload["overlap_diff_columns"] = overlap_diff_columns
#|    payload["overlap_exact_match"] = payload["matched_row_key_count"] == payload["reference_row_count"] and not overlap_diff_columns
#|    payload["overlap_decision_columns_match"] = payload["matched_row_key_count"] == payload["reference_row_count"] and not any(
#|        column in overlap_diff_columns for column in decision_columns
#|    )
#|    if payload["exact_match"]:
#|        payload["status_ko"] = "fixed fault reference exact match"
#|    elif payload["overlap_decision_columns_match"]:
#|        payload["status_ko"] = "overlap decision columns preserved and raw-only candidate universe expanded by design"
#|    elif payload["matched_row_key_count"] > 0:
#|        payload["status_ko"] = "overlap exists but decision drift detected"
#|    else:
#|        payload["status_ko"] = "no overlapping fixed reference keys"
#|    return payload
# pvdiag_payload_end
# endregion
# endregion


EMBEDDED_TEXT_FILES, EMBEDDED_FILE_SHA256 = load_embedded_payload_from_source()


if __name__ == "__main__":
    raise SystemExit(main())
