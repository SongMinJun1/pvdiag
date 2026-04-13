#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DEFAULT_SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
SITE_RUNNER_SCRIPT = "research/prognostics/run_panel_day_site.py"
BASELINE_BUILDER_SCRIPT = "research/prognostics/build_panel_day_engine_operator_baseline_v1.py"

REFRESH_MANIFEST_NAME = "panel_day_engine_operator_refresh_manifest_v1.csv"
REFRESH_SITE_RESULTS_NAME = "panel_day_engine_operator_refresh_site_results_v1.csv"

SITE_RESULTS_OUTPUT_COLS = [
    "site",
    "started_at_utc",
    "finished_at_utc",
    "duration_seconds",
    "success_flag",
    "return_code",
    "error_message",
]

MANIFEST_OUTPUT_COLS = [
    "refresh_started_at_utc",
    "refresh_finished_at_utc",
    "requested_site_count",
    "succeeded_site_count",
    "failed_site_count",
    "baseline_built_flag",
    "baseline_builder_return_code",
    "requested_sites_csv",
    "succeeded_sites_csv",
    "failed_sites_csv",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh selected sites and rebuild the operator baseline when every requested site succeeds."
    )
    parser.add_argument(
        "--sites",
        default=",".join(DEFAULT_SITES),
        help="Comma-separated site list. Defaults to conalog,gangui,ktc_ess,sinhyo.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the project root.",
    )
    return parser.parse_args()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_sites_csv(raw_sites: str | None) -> list[str]:
    if raw_sites is None:
        return list(DEFAULT_SITES)
    sites = [site.strip() for site in str(raw_sites).split(",") if site.strip()]
    if not sites:
        raise SystemExit("no sites requested")
    return sites


def summarize_error(result: subprocess.CompletedProcess[str]) -> str:
    if result.returncode == 0:
        return ""
    text = (result.stderr or "").strip() or (result.stdout or "").strip()
    return " | ".join(line.strip() for line in text.splitlines() if line.strip())


def run_site(root: Path, site: str) -> dict[str, object]:
    script_path = root / SITE_RUNNER_SCRIPT
    started_at = utc_now_iso()
    started_perf = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(script_path), "--site", site],
        cwd=root,
        text=True,
        capture_output=True,
    )
    finished_at = utc_now_iso()
    duration_seconds = round(time.perf_counter() - started_perf, 3)
    return {
        "site": site,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "duration_seconds": duration_seconds,
        "success_flag": int(result.returncode == 0),
        "return_code": int(result.returncode),
        "error_message": summarize_error(result),
    }


def run_baseline(root: Path) -> subprocess.CompletedProcess[str]:
    script_path = root / BASELINE_BUILDER_SCRIPT
    return subprocess.run(
        [sys.executable, str(script_path), "--root", str(root)],
        cwd=root,
        text=True,
        capture_output=True,
    )


def build_manifest(
    requested_sites: list[str],
    site_results: list[dict[str, object]],
    refresh_started_at_utc: str,
    refresh_finished_at_utc: str,
    baseline_built_flag: int,
    baseline_builder_return_code: int | str,
) -> pd.DataFrame:
    succeeded_sites = [row["site"] for row in site_results if int(row["success_flag"]) == 1]
    failed_sites = [row["site"] for row in site_results if int(row["success_flag"]) == 0]
    row = {
        "refresh_started_at_utc": refresh_started_at_utc,
        "refresh_finished_at_utc": refresh_finished_at_utc,
        "requested_site_count": len(requested_sites),
        "succeeded_site_count": len(succeeded_sites),
        "failed_site_count": len(failed_sites),
        "baseline_built_flag": int(baseline_built_flag),
        "baseline_builder_return_code": baseline_builder_return_code,
        "requested_sites_csv": ",".join(requested_sites),
        "succeeded_sites_csv": ",".join(succeeded_sites),
        "failed_sites_csv": ",".join(failed_sites),
    }
    return pd.DataFrame([row], columns=MANIFEST_OUTPUT_COLS)


def write_outputs(root: Path, site_results: list[dict[str, object]], manifest: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(site_results, columns=SITE_RESULTS_OUTPUT_COLS).to_csv(
        share_dir / REFRESH_SITE_RESULTS_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    manifest.to_csv(share_dir / REFRESH_MANIFEST_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    requested_sites = parse_sites_csv(args.sites)

    refresh_started_at_utc = utc_now_iso()
    site_results = [run_site(root, site) for site in requested_sites]

    baseline_built_flag = int(all(int(row["success_flag"]) == 1 for row in site_results))
    baseline_builder_return_code: int | str = ""
    baseline_result: subprocess.CompletedProcess[str] | None = None

    if baseline_built_flag == 1:
        baseline_result = run_baseline(root)
        baseline_builder_return_code = int(baseline_result.returncode)

    refresh_finished_at_utc = utc_now_iso()
    manifest = build_manifest(
        requested_sites,
        site_results,
        refresh_started_at_utc,
        refresh_finished_at_utc,
        baseline_built_flag,
        baseline_builder_return_code,
    )
    write_outputs(root, site_results, manifest)

    failed_site_count = sum(int(row["success_flag"]) == 0 for row in site_results)
    if failed_site_count:
        raise SystemExit(1)
    if baseline_result is not None and baseline_result.returncode != 0:
        details = summarize_error(baseline_result) or "operator baseline build failed"
        raise SystemExit(details)


if __name__ == "__main__":
    main()
