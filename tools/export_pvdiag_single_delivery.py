#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export the professor-facing delivery folder with exactly one file: "
            "pvdiag_single.py."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--single", type=Path, default=Path("release/conalog_full_runtime_v1/pvdiag_single.py"))
    parser.add_argument(
        "--manifest-output",
        type=Path,
        help="Optional internal manifest path. This is not written into the professor delivery folder by default.",
    )
    parser.add_argument(
        "--skip-handoff-check",
        action="store_true",
        help="Skip tools/check_pvdiag_single_handoff.py. Intended only for debugging.",
    )
    parser.add_argument(
        "--clean-output-dir",
        action="store_true",
        help="Remove existing files inside --output-dir before exporting.",
    )
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


def clean_dir(path: Path) -> None:
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def assert_single_file_output(output_dir: Path) -> Path:
    entries = sorted(output_dir.iterdir(), key=lambda item: item.name)
    if [entry.name for entry in entries] != ["pvdiag_single.py"]:
        fail(
            "professor delivery folder must contain exactly one file named pvdiag_single.py; "
            f"found: {[entry.name for entry in entries]}"
        )
    exported = entries[0]
    if not exported.is_file():
        fail(f"exported pvdiag_single.py is not a regular file: {exported}")
    return exported


def run_handoff_check(repo_root: Path) -> None:
    checker = repo_root / "tools/check_pvdiag_single_handoff.py"
    if not checker.exists():
        fail(f"missing handoff checker: {checker}")
    proc = subprocess.run(
        [sys.executable, str(checker)],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        fail(
            "handoff checker failed before export.\n"
            f"command: {sys.executable} {checker}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    source = resolve(repo_root, args.single)
    output_dir = args.output_dir.resolve()
    manifest_output = resolve(repo_root, args.manifest_output) if args.manifest_output else None

    if not source.exists():
        fail(f"missing source single-file artifact: {source}")
    if source.name != "pvdiag_single.py":
        fail(f"source single-file artifact must be named pvdiag_single.py: {source}")

    if not args.skip_handoff_check:
        run_handoff_check(repo_root)

    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        if not args.clean_output_dir:
            fail(
                f"output directory is not empty: {output_dir}\n"
                "Use a fresh directory, or pass --clean-output-dir to replace its contents."
            )
        clean_dir(output_dir)

    destination = output_dir / "pvdiag_single.py"
    shutil.copy2(source, destination)
    exported = assert_single_file_output(output_dir)

    source_sha = sha256_file(source)
    exported_sha = sha256_file(exported)
    if source_sha != exported_sha:
        fail(f"export checksum mismatch: source={source_sha} exported={exported_sha}")

    summary = {
        "delivery_ready": 1,
        "professor_deliverable_file_count": 1,
        "professor_deliverable_files": ["pvdiag_single.py"],
        "output_dir": str(output_dir),
        "exported_file": str(exported),
        "source_file": str(source),
        "sha256": exported_sha,
        "bytes": exported.stat().st_size,
        "handoff_check_ran": int(not args.skip_handoff_check),
    }
    if manifest_output:
        manifest_output.parent.mkdir(parents=True, exist_ok=True)
        manifest_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary["manifest_output"] = str(manifest_output)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
