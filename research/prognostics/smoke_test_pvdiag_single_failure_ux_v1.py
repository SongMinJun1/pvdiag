#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def run(command: list[str], cwd: Path, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        **kwargs,
    )


def run_with_missing_torch(single: Path, args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    code = r"""
import importlib.util
import runpy
import sys

single = sys.argv[1]
single_args = sys.argv[2:]
original_find_spec = importlib.util.find_spec

def fake_find_spec(name, *args, **kwargs):
    if name == "torch":
        return None
    return original_find_spec(name, *args, **kwargs)

importlib.util.find_spec = fake_find_spec
sys.argv = [single, *single_args]
try:
    runpy.run_path(single, run_name="__main__")
except SystemExit as exc:
    raise SystemExit(exc.code)
"""
    return run([sys.executable, "-c", code, str(single), *args], cwd=cwd)


def combined(proc: subprocess.CompletedProcess[str]) -> str:
    return proc.stdout + proc.stderr


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "tools/build_pvdiag_single_py.py"
    single = repo_root / "release/conalog_full_runtime_v1/pvdiag_single.py"

    build = run([sys.executable, str(builder), "--repo-root", str(repo_root)], repo_root)
    assert_true(build.returncode == 0, build.stderr or build.stdout)

    self_test_missing_dep = run_with_missing_torch(single, ["--single-self-test"], repo_root)
    self_text = combined(self_test_missing_dep)
    assert_true(self_test_missing_dep.returncode == 0, self_text)
    assert_true("self-test ok" in self_text, self_text)
    assert_true("missing required Python packages" not in self_text, self_text)

    missing_dep = run_with_missing_torch(
        single,
        ["--data-root", str(repo_root / "data"), "--output-root", "/private/tmp/pvdiag_missing_dep_smoke"],
        repo_root,
    )
    missing_text = combined(missing_dep)
    assert_true(missing_dep.returncode == 2, missing_text)
    assert_true("missing required Python packages" in missing_text, missing_text)
    assert_true("torch" in missing_text, missing_text)
    assert_true("pip install pandas numpy torch openpyxl tqdm" in missing_text, missing_text)
    assert_true("run the same command again" in missing_text, missing_text)

    with tempfile.TemporaryDirectory(prefix="pvdiag_single_failure_ux_") as tmp:
        tmp_root = Path(tmp)
        output_root = tmp_root / "bad_data_output"
        bad_data = run(
            [
                sys.executable,
                str(single),
                "--data-root",
                str(tmp_root / "missing_data"),
                "--output-root",
                str(output_root),
            ],
            repo_root,
        )
        bad_text = combined(bad_data)
        assert_true(bad_data.returncode == 3, bad_text)
        assert_true("data-root does not exist" in bad_text, bad_text)
        assert_true("run with --data-root /path/to/data" in bad_text, bad_text)
        assert_true("place a data/ folder next to pvdiag_single.py" in bad_text, bad_text)
        assert_true(str(output_root) in bad_text, bad_text)

        no_data_dir = tmp_root / "no_sibling_data"
        no_data_dir.mkdir()
        no_data = run(
            [sys.executable, str(single), "--output-root", str(tmp_root / "no_data_output")],
            no_data_dir,
            input="",
        )
        no_data_text = combined(no_data)
        assert_true(no_data.returncode == 3, no_data_text)
        assert_true("data-root was not provided" in no_data_text, no_data_text)
        assert_true("sibling data/ was not found" in no_data_text, no_data_text)
        assert_true("run with --data-root /path/to/data" in no_data_text, no_data_text)

    print("smoke ok: pvdiag_single_failure_ux_v1")


if __name__ == "__main__":
    main()
