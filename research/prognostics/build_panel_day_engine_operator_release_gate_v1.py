#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DEFAULT_SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]

PIPELINE_SCRIPT = "research/prognostics/build_panel_day_engine_operator_pipeline_v1.py"
IDEMPOTENCE_SCRIPT = "research/prognostics/build_panel_day_engine_operator_pipeline_idempotence_audit_v1.py"

PIPELINE_MANIFEST_NAME = "panel_day_engine_operator_pipeline_manifest_v1.csv"
IDEMPOTENCE_SUMMARY_NAME = "panel_day_engine_operator_pipeline_idempotence_summary_v1.csv"
RELEASE_GATE_MANIFEST_NAME = "panel_day_engine_operator_release_gate_manifest_v1.csv"

RELEASE_GATE_MANIFEST_COLS = [
    "release_gate_started_at_utc",
    "release_gate_finished_at_utc",
    "requested_sites_csv",
    "pipeline_executed_flag",
    "pipeline_pass_flag",
    "idempotence_executed_flag",
    "idempotence_pass_flag",
    "final_release_gate_pass_flag",
    "final_recommended_exit_code",
    "overall_attention_count",
    "overall_queue_count",
    "overall_watch_now_count",
    "overall_watch_review_count",
    "overall_backlog_count",
    "overall_cluster_preview_count",
    "overall_discovery_cluster_count",
    "overall_unified_digest_count",
    "overall_workflow_default_count",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the operator pipeline release/stability gate by executing the normal pipeline and, on success, the pipeline idempotence audit."
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


def run_builder(root: Path, script_relative_path: str, requested_sites: list[str]) -> subprocess.CompletedProcess[str]:
    script_path = root / script_relative_path
    cmd = [sys.executable, str(script_path), "--sites", ",".join(requested_sites), "--root", str(root)]
    if not script_path.exists():
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=1,
            stdout="",
            stderr=f"missing builder script: {script_path}",
        )
    return subprocess.run(cmd, cwd=root, text=True, capture_output=True)


def read_first_row_or_none(path: Path) -> pd.Series | None:
    if not path.exists():
        return None
    df = pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
    if df.empty:
        return None
    return df.iloc[0].copy()


def numeric_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


def determine_note(
    *,
    pipeline_pass_flag: int,
    idempotence_executed_flag: int,
    idempotence_pass_flag: int,
) -> str:
    if pipeline_pass_flag != 1 or idempotence_executed_flag == 0:
        return "pipeline 실패로 idempotence 생략"
    if idempotence_pass_flag != 1:
        return "idempotence 미통과로 release 보류"
    return "operator stack release gate 통과"


def build_manifest(
    *,
    release_gate_started_at_utc: str,
    release_gate_finished_at_utc: str,
    requested_sites_csv: str,
    pipeline_executed_flag: int,
    pipeline_row: pd.Series | None,
    idempotence_executed_flag: int,
    idempotence_row: pd.Series | None,
) -> pd.DataFrame:
    pipeline_pass_flag = numeric_int(pipeline_row.get("final_pipeline_pass_flag")) if pipeline_row is not None else 0
    idempotence_pass_flag = (
        numeric_int(idempotence_row.get("idempotence_pass_flag")) if idempotence_row is not None else 0
    )
    final_release_gate_pass_flag = int(
        pipeline_pass_flag == 1 and idempotence_executed_flag == 1 and idempotence_pass_flag == 1
    )
    final_recommended_exit_code = 0 if final_release_gate_pass_flag == 1 else 1

    manifest_row = {
        "release_gate_started_at_utc": release_gate_started_at_utc,
        "release_gate_finished_at_utc": release_gate_finished_at_utc,
        "requested_sites_csv": requested_sites_csv,
        "pipeline_executed_flag": pipeline_executed_flag,
        "pipeline_pass_flag": pipeline_pass_flag,
        "idempotence_executed_flag": idempotence_executed_flag,
        "idempotence_pass_flag": idempotence_pass_flag,
        "final_release_gate_pass_flag": final_release_gate_pass_flag,
        "final_recommended_exit_code": final_recommended_exit_code,
        "overall_attention_count": numeric_int(pipeline_row.get("overall_attention_count")) if pipeline_row is not None else 0,
        "overall_queue_count": numeric_int(pipeline_row.get("overall_queue_count")) if pipeline_row is not None else 0,
        "overall_watch_now_count": numeric_int(pipeline_row.get("overall_watch_now_count")) if pipeline_row is not None else 0,
        "overall_watch_review_count": numeric_int(pipeline_row.get("overall_watch_review_count")) if pipeline_row is not None else 0,
        "overall_backlog_count": numeric_int(pipeline_row.get("overall_backlog_count")) if pipeline_row is not None else 0,
        "overall_cluster_preview_count": numeric_int(pipeline_row.get("overall_cluster_preview_count"))
        if pipeline_row is not None
        else 0,
        "overall_discovery_cluster_count": numeric_int(pipeline_row.get("overall_discovery_cluster_count"))
        if pipeline_row is not None
        else 0,
        "overall_unified_digest_count": numeric_int(pipeline_row.get("overall_unified_digest_count"))
        if pipeline_row is not None
        else 0,
        "overall_workflow_default_count": numeric_int(pipeline_row.get("overall_workflow_default_count"))
        if pipeline_row is not None
        else 0,
        "note_ko": determine_note(
            pipeline_pass_flag=pipeline_pass_flag,
            idempotence_executed_flag=idempotence_executed_flag,
            idempotence_pass_flag=idempotence_pass_flag,
        ),
    }
    return pd.DataFrame([manifest_row], columns=RELEASE_GATE_MANIFEST_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    requested_sites = parse_sites_csv(args.sites)
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    started_at = utc_now_iso()

    pipeline_result = run_builder(root, PIPELINE_SCRIPT, requested_sites)
    pipeline_row = read_first_row_or_none(share_dir / PIPELINE_MANIFEST_NAME)
    pipeline_pass_flag = numeric_int(pipeline_row.get("final_pipeline_pass_flag")) if pipeline_row is not None else 0

    idempotence_executed_flag = 0
    idempotence_row: pd.Series | None = None
    if pipeline_result.returncode == 0 and pipeline_pass_flag == 1:
        idempotence_executed_flag = 1
        run_builder(root, IDEMPOTENCE_SCRIPT, requested_sites)
        idempotence_row = read_first_row_or_none(share_dir / IDEMPOTENCE_SUMMARY_NAME)

    finished_at = utc_now_iso()
    manifest = build_manifest(
        release_gate_started_at_utc=started_at,
        release_gate_finished_at_utc=finished_at,
        requested_sites_csv=",".join(requested_sites),
        pipeline_executed_flag=1,
        pipeline_row=pipeline_row,
        idempotence_executed_flag=idempotence_executed_flag,
        idempotence_row=idempotence_row,
    )
    manifest_path = share_dir / RELEASE_GATE_MANIFEST_NAME
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    exit_code = int(manifest.iloc[0]["final_recommended_exit_code"])
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
