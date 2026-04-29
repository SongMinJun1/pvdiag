#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import stat
import textwrap
import zipfile
from datetime import datetime, timezone
from pathlib import Path


PACKAGE_ROOT = Path("release/conalog_full_runtime_v1/package")
DEFAULT_OUTPUT = Path("release/conalog_full_runtime_v1/pvdiag_single.py")

INCLUDE_PREFIXES = (
    "app/",
    "artifacts/",
    "pv_ae/",
    "research/",
)
INCLUDE_FILES = {"requirements.txt"}
INCLUDE_SUFFIXES = {".py", ".json", ".csv", ".md", ".txt"}
EXCLUDE_PREFIXES = (
    "runtime/",
    "bin/",
)
EXCLUDE_PARTS = {"__pycache__"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}

MAX_FILE_BYTES = 2_000_000
MAX_PAYLOAD_BYTES = 8_000_000


SINGLE_TEMPLATE = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import zipfile
from datetime import datetime
from pathlib import Path


GENERATED_BY = "tools/build_pvdiag_single_py.py"
GENERATED_AT_UTC = "__GENERATED_AT_UTC__"
PAYLOAD_SHA256 = "__PAYLOAD_SHA256__"
PAYLOAD_FILE_COUNT = __PAYLOAD_FILE_COUNT__
PAYLOAD_B64 = """
__PAYLOAD_B64__
"""

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
    parser.add_argument("--single-keep-runtime", action="store_true", help="Keep the extracted temporary runtime folder for debugging.")
    return parser.parse_known_args(argv)


def missing_dependencies() -> list[str]:
    missing: list[str] = []
    for module_name, package_name in REQUIRED_MODULES.items():
        if importlib.util.find_spec(module_name) is None:
            missing.append(package_name)
    return missing


def resolve_data_root(value: Path | None) -> Path:
    if value is not None:
        return value.expanduser().resolve()
    sibling_data = script_dir() / "data"
    if sibling_data.exists():
        return sibling_data.resolve()
    try:
        typed = input("Input data-root folder path: ").strip()
    except EOFError as exc:
        raise SystemExit(
            "data-root was not provided, sibling data/ was not found, and interactive input is unavailable"
        ) from exc
    if not typed:
        raise SystemExit("data-root is required")
    return Path(typed).expanduser().resolve()


def resolve_output_root(value: Path | None) -> Path:
    if value is not None:
        output_root = value.expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = script_dir() / "pvdiag_results" / f"run_{stamp}"
    output_root.mkdir(parents=True, exist_ok=True)
    return output_root


def decode_payload() -> bytes:
    payload = base64.b64decode("".join(PAYLOAD_B64.split()))
    digest = hashlib.sha256(payload).hexdigest()
    if digest != PAYLOAD_SHA256:
        raise SystemExit(f"embedded payload sha256 mismatch: expected {PAYLOAD_SHA256}, got {digest}")
    return payload


def safe_extract(payload: bytes, runtime_root: Path) -> None:
    runtime_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        members = zf.infolist()
        if len(members) != PAYLOAD_FILE_COUNT:
            raise SystemExit(f"embedded payload file-count mismatch: expected {PAYLOAD_FILE_COUNT}, got {len(members)}")
        for info in members:
            target = (runtime_root / info.filename).resolve()
            if not str(target).startswith(str(runtime_root.resolve()) + os.sep):
                raise SystemExit(f"unsafe payload path: {info.filename}")
        zf.extractall(runtime_root)


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
    missing = missing_dependencies()
    if missing:
        print("[pvdiag_single] missing required Python packages:")
        for package in missing:
            print(f"  - {package}")
        print("[pvdiag_single] install example:")
        print("  pip install pandas numpy torch openpyxl tqdm")
        return 2

    output_root = resolve_output_root(args.output_root)
    runtime_root: Path
    cleanup_runtime = not args.single_keep_runtime
    temp_obj = None
    if cleanup_runtime:
        temp_obj = tempfile.TemporaryDirectory(prefix="pvdiag_single_runtime_")
        runtime_root = Path(temp_obj.name)
    else:
        runtime_root = Path(tempfile.mkdtemp(prefix="pvdiag_single_runtime_keep_"))

    try:
        safe_extract(decode_payload(), runtime_root)
        runner = inner_runner(runtime_root)
        if args.single_self_test:
            print("[pvdiag_single] self-test ok")
            print(f"[pvdiag_single] generated_at_utc: {GENERATED_AT_UTC}")
            print(f"[pvdiag_single] payload_files: {PAYLOAD_FILE_COUNT}")
            print(f"[pvdiag_single] runtime_root: {runtime_root}")
            print(f"[pvdiag_single] runner: {runner}")
            return 0

        data_root = resolve_data_root(args.data_root)
        if not data_root.exists():
            print(f"[pvdiag_single] data-root does not exist: {data_root}")
            print(f"[pvdiag_single] log directory: {output_root}")
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


if __name__ == "__main__":
    raise SystemExit(main())
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the generated single-file pvdiag delivery runner."
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest-output", type=Path, default=Path("release/conalog_full_runtime_v1/pvdiag_single_manifest_v1.json"))
    return parser.parse_args()


def should_include(path: Path, package_root: Path) -> bool:
    rel = path.relative_to(package_root).as_posix()
    if any(part in EXCLUDE_PARTS for part in path.parts):
        return False
    if path.suffix in EXCLUDE_SUFFIXES:
        return False
    if any(rel.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
        return False
    if rel in INCLUDE_FILES:
        return True
    if not any(rel.startswith(prefix) for prefix in INCLUDE_PREFIXES):
        return False
    return path.suffix in INCLUDE_SUFFIXES


def collect_files(repo_root: Path) -> list[Path]:
    package_root = repo_root / PACKAGE_ROOT
    if not package_root.exists():
        raise SystemExit(f"package root not found: {package_root}")
    files = sorted(path for path in package_root.rglob("*") if path.is_file() and should_include(path, package_root))
    if not files:
        raise SystemExit("no files selected for pvdiag_single payload")
    oversized = [path for path in files if path.stat().st_size > MAX_FILE_BYTES]
    if oversized:
        joined = "\n".join(str(path.relative_to(repo_root)) for path in oversized)
        raise SystemExit(f"payload file exceeds max bytes:\n{joined}")
    return files


def build_zip(repo_root: Path, files: list[Path]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            arcname = path.relative_to(repo_root).as_posix()
            zf.write(path, arcname)
    payload = buffer.getvalue()
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise SystemExit(f"payload too large: {len(payload)} > {MAX_PAYLOAD_BYTES}")
    return payload


def render_single(payload: bytes, file_count: int) -> str:
    encoded = base64.b64encode(payload).decode("ascii")
    wrapped = "\n".join(textwrap.wrap(encoded, width=76))
    digest = hashlib.sha256(payload).hexdigest()
    generated_at = datetime.now(timezone.utc).isoformat()
    return (
        SINGLE_TEMPLATE.replace("__GENERATED_AT_UTC__", generated_at)
        .replace("__PAYLOAD_SHA256__", digest)
        .replace("__PAYLOAD_FILE_COUNT__", str(file_count))
        .replace("__PAYLOAD_B64__", wrapped)
    )


def write_manifest(path: Path, repo_root: Path, files: list[Path], payload: bytes) -> None:
    rows = []
    for file_path in files:
        data = file_path.read_bytes()
        rows.append(
            {
                "path": file_path.relative_to(repo_root).as_posix(),
                "bytes": file_path.stat().st_size,
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    payload_obj = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generated_by": "tools/build_pvdiag_single_py.py",
        "delivery_artifact": DEFAULT_OUTPUT.as_posix(),
        "payload_file_count": len(files),
        "payload_zip_bytes": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "excluded_runtime_windows_x64": True,
        "max_payload_file_bytes": MAX_FILE_BYTES,
        "files": rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output = args.output if args.output.is_absolute() else repo_root / args.output
    manifest_output = args.manifest_output if args.manifest_output.is_absolute() else repo_root / args.manifest_output
    files = collect_files(repo_root)
    payload = build_zip(repo_root, files)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_single(payload, len(files)), encoding="utf-8")
    output.chmod(output.stat().st_mode | stat.S_IXUSR)
    write_manifest(manifest_output, repo_root, files, payload)
    print(
        json.dumps(
            {
                "output": str(output),
                "manifest": str(manifest_output),
                "payload_file_count": len(files),
                "payload_zip_bytes": len(payload),
                "single_file_bytes": output.stat().st_size,
                "excluded_runtime_windows_x64": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
