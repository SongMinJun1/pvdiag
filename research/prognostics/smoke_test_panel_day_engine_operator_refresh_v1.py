#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert_true(spec is not None and spec.loader is not None, f"failed to load module: {path.name}")
    spec.loader.exec_module(module)
    return module


def write_stub_script(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_stub_root(root: Path, *, fail_sites: list[str] | None = None) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    if fail_sites:
        (share_dir / "fail_sites.txt").write_text("\n".join(fail_sites), encoding="utf-8")

    site_runner = """#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--site", required=True)
args = ap.parse_args()

root = Path.cwd()
share_dir = root / "_share"
fail_path = share_dir / "fail_sites.txt"
fail_sites = set()
if fail_path.exists():
    fail_sites = {line.strip() for line in fail_path.read_text(encoding="utf-8").splitlines() if line.strip()}

with (share_dir / "run_log.txt").open("a", encoding="utf-8") as fp:
    fp.write(f"SITE:{args.site}\\n")

if args.site in fail_sites:
    print(f"site failed: {args.site}", file=sys.stderr)
    raise SystemExit(7)
"""
    baseline_builder = """#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
args = ap.parse_args()

root = Path(args.root)
share_dir = root / "_share"
share_dir.mkdir(parents=True, exist_ok=True)
with (share_dir / "run_log.txt").open("a", encoding="utf-8") as fp:
    fp.write("BASELINE\\n")
(share_dir / "baseline_called.txt").write_text("called", encoding="utf-8")
"""
    write_stub_script(root / "research/prognostics/run_panel_day_site.py", site_runner)
    write_stub_script(root / "research/prognostics/build_panel_day_engine_operator_baseline_v1.py", baseline_builder)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_operator_refresh_v1.py"
    build_module = load_module(build_path, "operator_refresh_build")

    assert_true(
        build_module.parse_sites_csv(None) == ["conalog", "gangui", "ktc_ess", "sinhyo"],
        "default site parsing mismatch",
    )
    assert_true(
        build_module.parse_sites_csv("conalog, gangui ,ktc_ess") == ["conalog", "gangui", "ktc_ess"],
        "explicit site parsing mismatch",
    )

    official_paths = [
        repo_root / "_share" / "panel_day_engine_operator_refresh_manifest_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_refresh_site_results_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_operator_refresh_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_operator_refresh_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="operator_refresh_success_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_stub_root(tmp_root)
        build_result = run(
            [
                sys.executable,
                str(build_path),
                "--root",
                str(tmp_root),
                "--sites",
                "alpha,beta",
            ],
            repo_root,
        )
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        share_dir = tmp_root / "_share"
        manifest = pd.read_csv(share_dir / "panel_day_engine_operator_refresh_manifest_v1.csv", encoding="utf-8-sig")
        site_results = pd.read_csv(share_dir / "panel_day_engine_operator_refresh_site_results_v1.csv", encoding="utf-8-sig")
        run_log = (share_dir / "run_log.txt").read_text(encoding="utf-8").splitlines()

        assert_true(len(manifest) == 1, "refresh manifest should emit one row")
        assert_true(len(site_results) == 2, "site results should emit one row per requested site")
        manifest_row = manifest.iloc[0]
        assert_true(int(manifest_row["requested_site_count"]) == 2, "requested_site_count mismatch")
        assert_true(int(manifest_row["succeeded_site_count"]) == 2, "succeeded_site_count mismatch")
        assert_true(int(manifest_row["failed_site_count"]) == 0, "failed_site_count mismatch")
        assert_true(int(manifest_row["baseline_built_flag"]) == 1, "baseline_built_flag mismatch")
        assert_true(int(manifest_row["baseline_builder_return_code"]) == 0, "baseline_builder_return_code mismatch")
        assert_true(manifest_row["requested_sites_csv"] == "alpha,beta", "requested_sites_csv mismatch")
        assert_true(manifest_row["succeeded_sites_csv"] == "alpha,beta", "succeeded_sites_csv mismatch")
        assert_true(str(manifest_row["failed_sites_csv"]).strip() in {"", "nan"}, "failed_sites_csv should be blank")
        assert_true(site_results["success_flag"].astype(int).tolist() == [1, 1], "success path flags mismatch")
        assert_true(run_log == ["SITE:alpha", "SITE:beta", "BASELINE"], "refresh should run all sites before baseline")
        assert_true((share_dir / "baseline_called.txt").exists(), "baseline should be called after successful site refresh")

    with tempfile.TemporaryDirectory(prefix="operator_refresh_failure_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_stub_root(tmp_root, fail_sites=["gangui"])
        build_result = run(
            [
                sys.executable,
                str(build_path),
                "--root",
                str(tmp_root),
                "--sites",
                "conalog,gangui,ktc_ess",
            ],
            repo_root,
        )
        assert_true(build_result.returncode != 0, "partial site failure should return nonzero")

        share_dir = tmp_root / "_share"
        manifest = pd.read_csv(share_dir / "panel_day_engine_operator_refresh_manifest_v1.csv", encoding="utf-8-sig")
        site_results = pd.read_csv(share_dir / "panel_day_engine_operator_refresh_site_results_v1.csv", encoding="utf-8-sig")
        run_log = (share_dir / "run_log.txt").read_text(encoding="utf-8").splitlines()

        assert_true(len(site_results) == 3, "partial failure should still record every requested site")
        manifest_row = manifest.iloc[0]
        assert_true(int(manifest_row["requested_site_count"]) == 3, "failure path requested_site_count mismatch")
        assert_true(int(manifest_row["succeeded_site_count"]) == 2, "failure path succeeded_site_count mismatch")
        assert_true(int(manifest_row["failed_site_count"]) == 1, "failure path failed_site_count mismatch")
        assert_true(int(manifest_row["baseline_built_flag"]) == 0, "baseline should be skipped on partial failure")
        assert_true(str(manifest_row["baseline_builder_return_code"]).strip() in {"", "nan"}, "skipped baseline return code should be blank")
        assert_true(manifest_row["failed_sites_csv"] == "gangui", "failed_sites_csv mismatch")
        assert_true(site_results["success_flag"].astype(int).tolist() == [1, 0, 1], "partial failure flags mismatch")
        failed_error = site_results.loc[site_results["site"].eq("gangui"), "error_message"].iloc[0]
        assert_true("site failed: gangui" in failed_error, "failure error message mismatch")
        assert_true(
            run_log == ["SITE:conalog", "SITE:gangui", "SITE:ktc_ess"],
            "baseline should be skipped after partial failure",
        )
        assert_true(
            not (share_dir / "baseline_called.txt").exists(),
            "baseline should not be called when any site fails",
        )

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
