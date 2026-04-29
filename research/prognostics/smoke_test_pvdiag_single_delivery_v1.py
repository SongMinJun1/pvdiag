#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "tools/build_pvdiag_single_py.py"
    single = repo_root / "release/conalog_full_runtime_v1/pvdiag_single.py"
    manifest = repo_root / "release/conalog_full_runtime_v1/pvdiag_single_manifest_v1.json"

    build = subprocess.run(
        [sys.executable, str(builder), "--repo-root", str(repo_root)],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(build.returncode == 0, build.stderr or build.stdout)
    assert_true(single.exists(), single)
    assert_true(manifest.exists(), manifest)

    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    single_text = single.read_text(encoding="utf-8")
    assert_true(manifest_payload["payload_mode"] == "source_text", manifest_payload)
    assert_true(manifest_payload["payload_file_count"] >= 10, manifest_payload)
    assert_true(manifest_payload["payload_text_bytes"] < 8_000_000, manifest_payload)
    assert_true(manifest_payload["excluded_runtime_windows_x64"] is True, manifest_payload)
    assert_true("EMBEDDED_TEXT_FILES" in single_text, single)
    assert_true("PAYLOAD_B64" not in single_text, single)
    assert_true("import base64" not in single_text, single)
    assert_true("import zipfile" not in single_text, single)
    paths = {row["path"] for row in manifest_payload["files"]}
    assert_true("release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py" in paths, paths)
    assert_true("release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py" in paths, paths)
    assert_true(
        "release/conalog_full_runtime_v1/package/research/prognostics/runtime_rawonly_chain_common_v1.py"
        in paths,
        paths,
    )
    assert_true(not any("/runtime/windows_x64/" in path for path in paths), paths)

    compile_single = subprocess.run(
        [sys.executable, "-m", "py_compile", str(single)],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(compile_single.returncode == 0, compile_single.stderr or compile_single.stdout)

    self_test = subprocess.run(
        [sys.executable, str(single), "--single-self-test"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(self_test.returncode == 0, self_test.stderr or self_test.stdout)
    assert_true("self-test ok" in self_test.stdout, self_test.stdout)

    print("smoke ok: pvdiag_single_delivery_v1")


if __name__ == "__main__":
    main()
