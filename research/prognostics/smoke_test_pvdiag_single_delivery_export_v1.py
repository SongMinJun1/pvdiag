#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    exporter = repo_root / "tools/export_pvdiag_single_delivery.py"
    source = repo_root / "release/conalog_full_runtime_v1/pvdiag_single.py"

    with tempfile.TemporaryDirectory(prefix="pvdiag_single_delivery_export_") as tmp:
        output_dir = Path(tmp) / "professor_delivery"
        manifest = Path(tmp) / "internal_export_manifest.json"
        export_proc = subprocess.run(
            [
                sys.executable,
                str(exporter),
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(output_dir),
                "--manifest-output",
                str(manifest),
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert_true(export_proc.returncode == 0, export_proc.stderr or export_proc.stdout)
        summary = json.loads(export_proc.stdout)
        assert_true(summary["delivery_ready"] == 1, summary)
        assert_true(summary["professor_deliverable_file_count"] == 1, summary)
        assert_true(summary["professor_deliverable_files"] == ["pvdiag_single.py"], summary)

        entries = sorted(path.name for path in output_dir.iterdir())
        assert_true(entries == ["pvdiag_single.py"], entries)
        exported = output_dir / "pvdiag_single.py"
        assert_true(exported.read_bytes() == source.read_bytes(), exported)
        assert_true(manifest.exists(), manifest)

        self_test = subprocess.run(
            [sys.executable, str(exported), "--single-self-test"],
            cwd=output_dir,
            text=True,
            capture_output=True,
            check=False,
        )
        assert_true(self_test.returncode == 0, self_test.stderr or self_test.stdout)
        assert_true("self-test ok" in self_test.stdout, self_test.stdout)

    print("smoke ok: pvdiag_single_delivery_export_v1")


if __name__ == "__main__":
    main()
