#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_ROOT = REPO_ROOT / "release" / "conalog_full_runtime_v1"
SINGLE_FILE = RELEASE_ROOT / "pvdiag_single.py"
MODULAR_RUNNER = RELEASE_ROOT / "package" / "app" / "run_full_algorithm_pack.py"

DEFAULT_SITES = "conalog,gangui,ktc_ess"
DRY_RUN_CSV_OUTPUTS = [
    "result/fault6_fixed_result_table_v1.csv",
    "result/fault6_label_and_algorithm_preview_v1.csv",
]
FULL_REUSE_CSV_OUTPUTS = [
    *DRY_RUN_CSV_OUTPUTS,
    "result/fault_panel_result_current_preview_v1.csv",
    "result/fault_panel_result_current_v1.csv",
    "result/fault_panel_result_precursor_report_v1.csv",
    "result/fault_panel_result_raw_only_fault_signal_report_v1.csv",
    "result/fault_panel_result_raw_only_current_preview_v1.csv",
    "result/fault_panel_result_raw_only_current_v1.csv",
    "result/live_chain/fault_panel_result_live_preview_v1.csv",
    "result/live_chain/fault_panel_result_live_v1.csv",
    "result/raw_only_chain/fault_panel_result_raw_only_preview_v1.csv",
    "result/raw_only_chain/fault_panel_result_raw_only_v1.csv",
]
FULL_REUSE_REQUIRED_NON_CSV = [
    "result/fault_panel_result_master_report_v1.md",
    "result/fault_panel_result_detailed_report_v1.xlsx",
    "result/live_chain/live_chain_summary_v1.json",
    "result/raw_only_chain/raw_only_chain_summary_v1.json",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare generated pvdiag_single.py outputs with the modular packaged runner. "
            "This checks the delivery artifact against the development reference."
        )
    )
    parser.add_argument(
        "--mode",
        choices=["dry-run", "reuse-existing-site-outs"],
        default="dry-run",
        help="dry-run compares fixed exported tables; reuse-existing-site-outs compares full dashboard outputs.",
    )
    parser.add_argument("--sites", default=DEFAULT_SITES, help="Comma-separated site list.")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=REPO_ROOT / "data",
        help="Data root for reuse-existing-site-outs mode. Defaults to repo data/.",
    )
    parser.add_argument(
        "--reuse-existing-site-outs-root",
        type=Path,
        default=None,
        help="Root containing <site>/out trees for reuse-existing-site-outs mode.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path(tempfile.gettempdir()) / "pvdiag_single_vs_modular_check_v1.json",
        help="Path for comparison JSON.",
    )
    parser.add_argument(
        "--keep-workspace",
        action="store_true",
        help="Keep temporary modular/single output workspace for inspection.",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(command: list[str], log_path: Path) -> dict[str, Any]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        log.write(proc.stdout)
    return {
        "command": command,
        "returncode": proc.returncode,
        "log_path": str(log_path),
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-40:]),
    }


def create_dry_run_data(root: Path, sites: list[str]) -> None:
    for site in sites:
        raw_dir = root / site / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        start = datetime(2026, 1, 1)
        for offset in range(20):
            day = (start + timedelta(days=offset)).strftime("%Y-%m-%d")
            (raw_dir / f"{day}_{site}_dryrun.csv").write_text("timestamp,panel_id,power\n", encoding="utf-8")


def read_csv_schema(path: Path) -> tuple[int, list[str]]:
    frame = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    return int(len(frame)), [str(col) for col in frame.columns]


def compare_csv(relative_path: str, modular_root: Path, single_root: Path) -> dict[str, Any]:
    modular_path = modular_root / relative_path
    single_path = single_root / relative_path
    row: dict[str, Any] = {
        "path": relative_path,
        "modular_exists": modular_path.exists(),
        "single_exists": single_path.exists(),
        "row_count_match": False,
        "schema_match": False,
        "sha256_match": False,
    }
    if not modular_path.exists() or not single_path.exists():
        return row
    modular_rows, modular_schema = read_csv_schema(modular_path)
    single_rows, single_schema = read_csv_schema(single_path)
    row.update(
        {
            "modular_rows": modular_rows,
            "single_rows": single_rows,
            "modular_schema": modular_schema,
            "single_schema": single_schema,
            "row_count_match": modular_rows == single_rows,
            "schema_match": modular_schema == single_schema,
            "modular_sha256": sha256_file(modular_path),
            "single_sha256": sha256_file(single_path),
        }
    )
    row["sha256_match"] = row["modular_sha256"] == row["single_sha256"]
    return row


def compare_non_csv(relative_path: str, modular_root: Path, single_root: Path) -> dict[str, Any]:
    modular_path = modular_root / relative_path
    single_path = single_root / relative_path
    return {
        "path": relative_path,
        "modular_exists": modular_path.exists(),
        "single_exists": single_path.exists(),
        "exists_match": modular_path.exists() and single_path.exists(),
        "modular_bytes": modular_path.stat().st_size if modular_path.exists() else None,
        "single_bytes": single_path.stat().st_size if single_path.exists() else None,
    }


def require_existing_site_outs(data_root: Path, sites: list[str]) -> None:
    missing = [site for site in sites if not (data_root / site / "out").exists()]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"missing <site>/out for reuse-existing-site-outs mode: {joined}")


def build_commands(args: argparse.Namespace, workspace: Path, sites: list[str]) -> tuple[list[str], list[str], Path, Path]:
    modular_output = workspace / "modular_output"
    single_output = workspace / "single_output"
    site_arg = ",".join(sites)

    if args.mode == "dry-run":
        dry_data = workspace / "dry_data"
        create_dry_run_data(dry_data, sites)
        shared_args = [
            "--data-root",
            str(dry_data),
            "--sites",
            site_arg,
            "--dry-run",
            "--epochs",
            "1",
        ]
    else:
        data_root = args.data_root.expanduser().resolve()
        reuse_root = (
            args.reuse_existing_site_outs_root.expanduser().resolve()
            if args.reuse_existing_site_outs_root is not None
            else data_root
        )
        require_existing_site_outs(reuse_root, sites)
        shared_args = [
            "--data-root",
            str(data_root),
            "--sites",
            site_arg,
            "--reuse-existing-site-outs-root",
            str(reuse_root),
            "--epochs",
            "1",
        ]

    modular_command = [
        sys.executable,
        str(MODULAR_RUNNER),
        *shared_args,
        "--output-root",
        str(modular_output),
    ]
    single_command = [
        sys.executable,
        str(SINGLE_FILE),
        *shared_args,
        "--output-root",
        str(single_output),
    ]
    return modular_command, single_command, modular_output, single_output


def check_payload_files() -> None:
    missing = [path for path in [SINGLE_FILE, MODULAR_RUNNER] if not path.exists()]
    if missing:
        raise SystemExit("missing required file(s): " + ", ".join(str(path) for path in missing))


def main() -> int:
    args = parse_args()
    check_payload_files()
    sites = [site.strip() for site in str(args.sites).split(",") if site.strip()]
    if not sites:
        raise SystemExit("at least one site is required")

    temp_obj = None
    if args.keep_workspace:
        workspace = Path(tempfile.mkdtemp(prefix="pvdiag_single_vs_modular_keep_"))
    else:
        temp_obj = tempfile.TemporaryDirectory(prefix="pvdiag_single_vs_modular_")
        workspace = Path(temp_obj.name)

    try:
        modular_command, single_command, modular_output, single_output = build_commands(args, workspace, sites)
        modular_run = run_command(modular_command, workspace / "logs" / "modular.log")
        single_run = run_command(single_command, workspace / "logs" / "single.log")

        csv_outputs = DRY_RUN_CSV_OUTPUTS if args.mode == "dry-run" else FULL_REUSE_CSV_OUTPUTS
        non_csv_outputs = [] if args.mode == "dry-run" else FULL_REUSE_REQUIRED_NON_CSV
        csv_checks = [compare_csv(path, modular_output, single_output) for path in csv_outputs]
        non_csv_checks = [compare_non_csv(path, modular_output, single_output) for path in non_csv_outputs]

        status = "pass"
        failures: list[str] = []
        if modular_run["returncode"] != 0:
            failures.append("modular runner returned nonzero")
        if single_run["returncode"] != 0:
            failures.append("single-file runner returned nonzero")
        for row in csv_checks:
            if not (row["modular_exists"] and row["single_exists"]):
                failures.append(f"missing csv output: {row['path']}")
                continue
            if not row["row_count_match"]:
                failures.append(f"row count mismatch: {row['path']}")
            if not row["schema_match"]:
                failures.append(f"schema mismatch: {row['path']}")
            if not row["sha256_match"]:
                failures.append(f"sha256 mismatch: {row['path']}")
        for row in non_csv_checks:
            if not row["exists_match"]:
                failures.append(f"missing non-csv output: {row['path']}")
        if failures:
            status = "fail"

        report = {
            "status": status,
            "mode": args.mode,
            "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sites": sites,
            "single_file": str(SINGLE_FILE.relative_to(REPO_ROOT)),
            "modular_runner": str(MODULAR_RUNNER.relative_to(REPO_ROOT)),
            "modular_run": modular_run,
            "single_run": single_run,
            "csv_checks": csv_checks,
            "non_csv_checks": non_csv_checks,
            "failures": failures,
        }
        if args.keep_workspace:
            report["workspace"] = str(workspace)
        args.json_out.expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        args.json_out.expanduser().resolve().write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if status == "pass":
            print(f"[OK] single vs modular check passed: {args.json_out}")
            if args.keep_workspace:
                print(f"[OK] workspace kept: {workspace}")
            return 0
        print(f"[FAIL] single vs modular check failed: {args.json_out}")
        for failure in failures:
            print(f"- {failure}")
        print(f"[INFO] modular log: {modular_run['log_path']}")
        print(f"[INFO] single log: {single_run['log_path']}")
        if args.keep_workspace:
            print(f"[INFO] workspace kept: {workspace}")
        return 1
    finally:
        if temp_obj is not None:
            temp_obj.cleanup()
        elif not args.keep_workspace and workspace.exists():
            shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
