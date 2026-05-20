#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_ROOT = REPO_ROOT / "release" / "conalog_full_runtime_v1"
PACKAGE_ROOT = RELEASE_ROOT / "package"
DEFAULT_OUTPUT = RELEASE_ROOT / "pvdiag_single.py"
DEFAULT_DELIVERY_COPY = Path.home() / "Desktop" / "pvdiag_professor_delivery" / "pvdiag_single.py"


ROLE_BY_RELATIVE_PATH = {
    "release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py": "entry_runner",
    "release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py": "core_engine",
    "release/conalog_full_runtime_v1/package/research/__init__.py": "package_marker",
    "release/conalog_full_runtime_v1/package/research/prognostics/__init__.py": "package_marker",
    "release/conalog_full_runtime_v1/package/research/prognostics/heuristic_display_registry_v1.py": "display_label_registry",
    "release/conalog_full_runtime_v1/package/research/prognostics/runtime_rawonly_chain_common_v1.py": "raw_only_shared_utils",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_bootstrap_verdict_v1.py": "live_bootstrap_builder",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_fault_panel_event_audit_v1.py": "live_audit_builder",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_panel_multiaxis_verdict_v1.py": "live_verdict_builder",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_gpvs_evidence_pack_v1.py": "live_gpvs_builder",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_cause_candidate_heuristics_v1.py": "live_heuristic_builder",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py": "raw_only_audit_builder",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_final_verdict_v1.py": "raw_only_verdict_builder",
    "release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_heuristic_v1.py": "raw_only_heuristic_builder",
}


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def payload_paths() -> list[Path]:
    paths = [
        PACKAGE_ROOT / "app" / "run_full_algorithm_pack.py",
        PACKAGE_ROOT / "pv_ae" / "panel_day_engine.py",
        PACKAGE_ROOT / "research" / "__init__.py",
        PACKAGE_ROOT / "research" / "prognostics" / "__init__.py",
        *sorted((PACKAGE_ROOT / "research" / "prognostics").glob("*.py")),
        *sorted((PACKAGE_ROOT / "artifacts").glob("*")),
        *sorted((PACKAGE_ROOT / "_share").glob("*")),
    ]
    seen: set[Path] = set()
    deduped: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(path)
    return deduped


def role_for(relative_path: str) -> str:
    if relative_path in ROLE_BY_RELATIVE_PATH:
        return ROLE_BY_RELATIVE_PATH[relative_path]
    if "/artifacts/" in relative_path:
        return "runtime_reference_artifact"
    if "/_share/" in relative_path:
        return "frozen_share_input"
    return "embedded_runtime_file"


def read_payload(path: Path) -> tuple[str, bool]:
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("utf-8-sig")
    return text, text.endswith("\n")


def build_payload_index(paths: list[Path]) -> tuple[list[dict[str, object]], dict[str, str]]:
    index: list[dict[str, object]] = []
    text_by_path: dict[str, str] = {}
    for path in paths:
        if not path.exists():
            raise SystemExit(f"payload source missing: {path}")
        if not path.is_file():
            raise SystemExit(f"payload source is not a file: {path}")
        relative = repo_relative(path)
        text, _ = read_payload(path)
        encoded = text.encode("utf-8")
        text_by_path[relative] = text
        index.append(
            {
                "path": relative,
                "role": role_for(relative),
                "bytes": len(encoded),
                "lines": len(text.splitlines()),
                "sha256": hashlib.sha256(encoded).hexdigest(),
            }
        )
    return index, text_by_path


def payload_bytes(text_by_path: dict[str, str]) -> bytes:
    return b"".join(
        path.encode("utf-8") + b"\0" + text.encode("utf-8") + b"\0"
        for path, text in sorted(text_by_path.items())
    )


def payload_blocks(index: list[dict[str, object]], text_by_path: dict[str, str]) -> str:
    blocks: list[str] = [
        "# region Embedded readable source payload (auto-generated; collapse this block in VS Code)",
        "# The lines below are original payload files, stored as readable comments.",
        "# Each '#|' line becomes one source line when pvdiag_single.py restores the runtime.",
        "# Use --single-list-payload to inspect roles or --single-extract-source DIR to unpack normal files.",
        "# -----------------------------------------------------------------------------",
    ]
    for item in index:
        path = str(item["path"])
        text = text_by_path[path]
        metadata = {
            "path": path,
            "role": item["role"],
            "bytes": item["bytes"],
            "lines": item["lines"],
            "sha256": item["sha256"],
            "endswith_newline": text.endswith("\n"),
        }
        blocks.append(f"# region payload: {item['role']}")
        blocks.append(f"# pvdiag_payload_file {json.dumps(metadata, ensure_ascii=False, sort_keys=True)}")
        for line in text.splitlines():
            blocks.append(f"#|{line}")
        blocks.append("# pvdiag_payload_end")
        blocks.append("# endregion")
    blocks.append("# endregion")
    return "\n".join(blocks) + "\n"


def generated_header(index: list[dict[str, object]], text_by_path: dict[str, str]) -> str:
    embedded = payload_bytes(text_by_path)
    generated_at = datetime.now(timezone.utc).isoformat()
    return f'''#!/usr/bin/env python3
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
GENERATED_AT_UTC = {generated_at!r}
PAYLOAD_MODE = "source_text"
PAYLOAD_TEXT_SHA256 = {hashlib.sha256(embedded).hexdigest()!r}
PAYLOAD_TEXT_BYTES = {len(embedded)}
PAYLOAD_FILE_COUNT = {len(index)}
PAYLOAD_STRUCTURE_NOTE = (
    "This generated file embeds the modular pvdiag runtime as source-text payload. "
    "Use --single-list-payload to inspect module roles or --single-extract-source DIR "
    "to unpack readable sources."
)

PAYLOAD_FILE_INDEX = {json.dumps(index, ensure_ascii=False, indent=4)}

EMBEDDED_TEXT_FILES: dict[str, str] = {{}}
EMBEDDED_FILE_SHA256: dict[str, str] = {{}}

REQUIRED_MODULES = {{
    "pandas": "pandas",
    "numpy": "numpy",
    "torch": "torch",
    "openpyxl": "openpyxl",
    "tqdm": "tqdm",
}}
RECOMMENDED_PACKAGE_VERSIONS = {{
    "pandas": "2.3.3",
    "numpy": "2.3.4",
    "torch": "2.9.1",
    "openpyxl": "3.1.5",
    "tqdm": "4.67.1",
}}
MIN_PYTHON_VERSION = (3, 10)


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
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help="Input data root. If omitted, ./data next to this file is used when present.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Output root. If omitted, pvdiag_results/run_YYYYMMDD_HHMMSS is created next to this file.",
    )
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


def package_versions() -> dict[str, str]:
    versions: dict[str, str] = {{}}
    for module_name in REQUIRED_MODULES:
        if importlib.util.find_spec(module_name) is None:
            continue
        module = __import__(module_name)
        versions[module_name] = str(getattr(module, "__version__", "unknown"))
    return versions


def print_environment_summary() -> None:
    print(
        "[pvdiag_single] environment:",
        f"python={{sys.version_info.major}}.{{sys.version_info.minor}}.{{sys.version_info.micro}}",
        f"executable={{sys.executable}}",
    )
    versions = package_versions()
    if versions:
        print("[pvdiag_single] installed package versions:")
        for module_name, version in versions.items():
            recommended = RECOMMENDED_PACKAGE_VERSIONS.get(module_name, "")
            suffix = f" (recommended {{recommended}})" if recommended and version != recommended else ""
            print(f"  - {{module_name}}=={{version}}{{suffix}}")


def python_version_supported() -> bool:
    return sys.version_info >= MIN_PYTHON_VERSION


def print_python_version_help() -> None:
    required = ".".join(str(part) for part in MIN_PYTHON_VERSION)
    current = f"{{sys.version_info.major}}.{{sys.version_info.minor}}.{{sys.version_info.micro}}"
    print(f"[pvdiag_single] Python {{required}}+ is required. Current Python is {{current}}.")
    print("[pvdiag_single] recommended: Python 3.11 with pandas/numpy/torch/openpyxl/tqdm installed.")


def print_dependency_help(missing: list[str]) -> None:
    print("[pvdiag_single] missing required Python packages:")
    for package in missing:
        print(f"  - {{package}}")
    print("[pvdiag_single] install example:")
    print("  pip install pandas==2.3.3 numpy==2.3.4 torch==2.9.1 openpyxl==3.1.5 tqdm==4.67.1")
    print("[pvdiag_single] after installing packages, run the same command again.")


def print_data_root_help(output_root: Path) -> None:
    print("[pvdiag_single] how to provide input data:")
    print("  1. run with --data-root /path/to/data")
    print("  2. or place a data/ folder next to pvdiag_single.py")
    print("[pvdiag_single] output/log directory:")
    print(f"  {{output_root}}")


def resolve_data_root(value: Path | None, output_root: Path) -> Path | None:
    if value is not None:
        return value.expanduser().resolve()
    sibling_data = script_dir() / "data"
    if sibling_data.exists():
        return sibling_data.resolve()
    if not sys.stdin.isatty():
        print("[pvdiag_single] data-root was not provided and sibling data/ was not found.")
        print(f"[pvdiag_single] looked for: {{sibling_data}}")
        print_data_root_help(output_root)
        return None
    try:
        typed = input("[pvdiag_single] Input data-root folder path: ").strip()
    except EOFError:
        print("[pvdiag_single] data-root was not provided and interactive input is unavailable.")
        print(f"[pvdiag_single] looked for: {{sibling_data}}")
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
        output_root = script_dir() / "pvdiag_results" / f"run_{{stamp}}"
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
        raise SystemExit(f"could not read generated single-file source: {{source}}") from exc

    start_prefix = "# pvdiag_payload_file "
    line_prefix = "#|"
    payload: dict[str, str] = {{}}
    hashes: dict[str, str] = {{}}
    current_meta: dict[str, object] | None = None
    current_lines: list[str] = []

    for line_no, line in enumerate(source_lines, start=1):
        if line.startswith(start_prefix):
            if current_meta is not None:
                raise SystemExit(f"nested embedded payload block at line {{line_no}}")
            try:
                current_meta = json.loads(line[len(start_prefix):])
            except json.JSONDecodeError as exc:
                raise SystemExit(f"invalid embedded payload metadata at line {{line_no}}") from exc
            current_lines = []
            continue
        if line == "# pvdiag_payload_end":
            if current_meta is None:
                raise SystemExit(f"embedded payload end without start at line {{line_no}}")
            path = str(current_meta.get("path", ""))
            if not path:
                raise SystemExit(f"embedded payload metadata missing path before line {{line_no}}")
            text = "\\n".join(current_lines)
            if bool(current_meta.get("endswith_newline", False)):
                text += "\\n"
            payload[path] = text
            hashes[path] = str(current_meta.get("sha256", ""))
            current_meta = None
            current_lines = []
            continue
        if current_meta is not None:
            if not line.startswith(line_prefix):
                raise SystemExit(f"embedded payload source line missing '#|' prefix at line {{line_no}}")
            current_lines.append(line[len(line_prefix):])

    if current_meta is not None:
        raise SystemExit("unterminated embedded payload block")
    if not payload:
        raise SystemExit("generated single-file source does not contain readable embedded payload blocks")
    return payload, hashes


def embedded_payload_bytes() -> bytes:
    return b"".join(
        path.encode("utf-8") + b"\\0" + text.encode("utf-8") + b"\\0"
        for path, text in sorted(EMBEDDED_TEXT_FILES.items())
    )


def verify_embedded_payload() -> None:
    if len(EMBEDDED_TEXT_FILES) != PAYLOAD_FILE_COUNT:
        raise SystemExit(
            f"embedded payload file-count mismatch: expected {{PAYLOAD_FILE_COUNT}}, got {{len(EMBEDDED_TEXT_FILES)}}"
        )
    payload_data = embedded_payload_bytes()
    if len(payload_data) != PAYLOAD_TEXT_BYTES:
        raise SystemExit(
            f"embedded payload byte mismatch: expected {{PAYLOAD_TEXT_BYTES}}, got {{len(payload_data)}}"
        )
    digest = hashlib.sha256(payload_data).hexdigest()
    if digest != PAYLOAD_TEXT_SHA256:
        raise SystemExit(f"embedded payload sha256 mismatch: expected {{PAYLOAD_TEXT_SHA256}}, got {{digest}}")
    for path, text in EMBEDDED_TEXT_FILES.items():
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        expected = EMBEDDED_FILE_SHA256.get(path)
        if expected != digest:
            raise SystemExit(f"embedded file sha256 mismatch: {{path}}")


def safe_target(runtime_root: Path, embedded_path: str) -> Path:
    target = (runtime_root / embedded_path).resolve()
    runtime_root_resolved = runtime_root.resolve()
    if target != runtime_root_resolved and not str(target).startswith(str(runtime_root_resolved) + os.sep):
        raise SystemExit(f"unsafe embedded path: {{embedded_path}}")
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
    print(f"[pvdiag_single] note: {{PAYLOAD_STRUCTURE_NOTE}}")
    print(f"[pvdiag_single] files: {{PAYLOAD_FILE_COUNT}}, bytes: {{PAYLOAD_TEXT_BYTES}}")
    for row in PAYLOAD_FILE_INDEX:
        print(
            "[pvdiag_single] "
            f"{{row['role']:<34}} "
            f"{{row['bytes']:>8}} bytes "
            f"{{row['sha256'][:12]}} "
            f"{{row['path']}}"
        )
    print("[pvdiag_single] readable source extraction:")
    print("  python pvdiag_single.py --single-extract-source /tmp/pvdiag_single_source")


def extract_source_tree(destination: Path) -> None:
    target_root = destination.expanduser().resolve()
    if target_root.exists() and not target_root.is_dir():
        raise SystemExit(f"source extraction target is not a directory: {{target_root}}")
    extract_embedded_files(target_root)
    runner = target_root / "release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py"
    engine = target_root / "release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py"
    print("[pvdiag_single] source extraction ok")
    print(f"[pvdiag_single] extracted files: {{PAYLOAD_FILE_COUNT}}")
    print(f"[pvdiag_single] source root: {{target_root}}")
    print(f"[pvdiag_single] runner: {{runner}}")
    print(f"[pvdiag_single] core engine: {{engine}}")


def inner_runner(runtime_root: Path) -> Path:
    path = runtime_root / "release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py"
    if not path.exists():
        raise SystemExit(f"embedded runner not found after extraction: {{path}}")
    return path


def run_command(cmd: list[str], output_root: Path) -> int:
    log_path = output_root / "pvdiag_single_run.log"
    print("[pvdiag_single] command:", flush=True)
    print(" ".join(str(part) for part in cmd), flush=True)
    print(f"[pvdiag_single] log: {{log_path}}", flush=True)
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
            print(f"[pvdiag_single] generated_at_utc: {{GENERATED_AT_UTC}}")
            print(f"[pvdiag_single] payload_mode: {{PAYLOAD_MODE}}")
            print(f"[pvdiag_single] payload_files: {{PAYLOAD_FILE_COUNT}}")
            print(f"[pvdiag_single] payload_text_bytes: {{PAYLOAD_TEXT_BYTES}}")
            print(f"[pvdiag_single] payload_structure_note: {{PAYLOAD_STRUCTURE_NOTE}}")
            print(f"[pvdiag_single] runtime_root: {{runtime_root}}")
            print(f"[pvdiag_single] runner: {{runner}}")
            print_environment_summary()
            return 0

        if not python_version_supported():
            print_python_version_help()
            if args.single_keep_runtime:
                print(f"[pvdiag_single] kept runtime: {{runtime_root}}")
            return 2

        missing = missing_dependencies()
        if missing:
            print_dependency_help(missing)
            if args.single_keep_runtime:
                print(f"[pvdiag_single] kept runtime: {{runtime_root}}")
            return 2

        output_root = resolve_output_root(args.output_root)
        data_root = resolve_data_root(args.data_root, output_root)
        if data_root is None:
            if args.single_keep_runtime:
                print(f"[pvdiag_single] kept runtime: {{runtime_root}}")
            return 3
        if not data_root.exists():
            print(f"[pvdiag_single] data-root does not exist: {{data_root}}")
            print_data_root_help(output_root)
            if args.single_keep_runtime:
                print(f"[pvdiag_single] kept runtime: {{runtime_root}}")
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

        code = run_command(cmd, output_root)
        if code != 0:
            print(f"[pvdiag_single] failed with exit code {{code}}")
            print(f"[pvdiag_single] log: {{output_root / 'pvdiag_single_run.log'}}")
            if args.single_keep_runtime:
                print(f"[pvdiag_single] kept runtime: {{runtime_root}}")
            return code

        print("[pvdiag_single] completed successfully")
        print(f"[pvdiag_single] result root: {{output_root}}")
        print(f"[pvdiag_single] master report: {{output_root / 'result' / 'fault_panel_result_master_report_v1.md'}}")
        print(f"[pvdiag_single] detailed xlsx: {{output_root / 'result' / 'fault_panel_result_detailed_report_v1.xlsx'}}")
        return 0
    finally:
        if temp_obj is not None:
            temp_obj.cleanup()
        elif cleanup_runtime and runtime_root.exists():
            shutil.rmtree(runtime_root, ignore_errors=True)


'''


def generated_footer() -> str:
    return '''

EMBEDDED_TEXT_FILES, EMBEDDED_FILE_SHA256 = load_embedded_payload_from_source()


if __name__ == "__main__":
    raise SystemExit(main())
'''


def build_single_file() -> str:
    paths = payload_paths()
    index, text_by_path = build_payload_index(paths)
    return generated_header(index, text_by_path) + payload_blocks(index, text_by_path) + generated_footer()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the generated pvdiag_single.py delivery artifact.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"Output file. Defaults to {DEFAULT_OUTPUT}.")
    parser.add_argument(
        "--delivery-copy",
        type=Path,
        default=None,
        help="Optional extra copy path, e.g. ~/Desktop/pvdiag_professor_delivery/pvdiag_single.py.",
    )
    parser.add_argument(
        "--copy-to-default-delivery",
        action="store_true",
        help=f"Also copy to {DEFAULT_DELIVERY_COPY}.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    text = build_single_file()
    output.write_text(text, encoding="utf-8")
    output.chmod(0o755)
    print(f"[OK] wrote {output}")
    print(f"[OK] bytes={len(text.encode('utf-8'))}")

    copy_targets: list[Path] = []
    if args.delivery_copy is not None:
        copy_targets.append(args.delivery_copy.expanduser().resolve())
    if args.copy_to_default_delivery:
        copy_targets.append(DEFAULT_DELIVERY_COPY.expanduser().resolve())
    for target in copy_targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output, target)
        target.chmod(0o755)
        print(f"[OK] copied {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
