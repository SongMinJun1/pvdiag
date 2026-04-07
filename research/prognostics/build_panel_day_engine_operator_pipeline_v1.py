#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DEFAULT_SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
REFRESH_SCRIPT = "research/prognostics/build_panel_day_engine_operator_refresh_v1.py"
QA_SCRIPT = "research/prognostics/build_panel_day_engine_operator_refresh_qa_v1.py"

REFRESH_MANIFEST_NAME = "panel_day_engine_operator_refresh_manifest_v1.csv"
QA_SUMMARY_NAME = "panel_day_engine_operator_refresh_qa_summary_v1.csv"
PIPELINE_MANIFEST_NAME = "panel_day_engine_operator_pipeline_manifest_v1.csv"
REQUIRED_QA_SUMMARY_COLS = [
    "qa_pass_flag",
    "overall_attention_count",
    "overall_queue_count",
    "overall_watch_now_count",
    "overall_watch_review_count",
    "overall_backlog_count",
    "overall_changed_count",
    "overall_cluster_preview_count",
    "overall_discovery_cluster_count",
    "overall_cluster_preview_future_fault_linked_ref_count",
    "overall_cluster_preview_future_truth_linked_ref_count",
]

PIPELINE_MANIFEST_COLS = [
    "pipeline_started_at_utc",
    "pipeline_finished_at_utc",
    "requested_sites_csv",
    "refresh_succeeded_site_count",
    "refresh_failed_site_count",
    "refresh_baseline_built_flag",
    "qa_executed_flag",
    "qa_skip_reason",
    "qa_pass_flag",
    "final_pipeline_pass_flag",
    "final_recommended_exit_code",
    "overall_attention_count",
    "overall_queue_count",
    "overall_watch_now_count",
    "overall_watch_review_count",
    "overall_backlog_count",
    "overall_changed_count",
    "overall_cluster_preview_count",
    "overall_discovery_cluster_count",
    "overall_cluster_preview_future_fault_linked_ref_count",
    "overall_cluster_preview_future_truth_linked_ref_count",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the operator refresh pipeline end-to-end and expose refresh-QA-validated discovery preview counts in the final pipeline manifest."
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


def run_builder(root: Path, script_relative_path: str, extra_args: list[str]) -> subprocess.CompletedProcess[str]:
    script_path = root / script_relative_path
    return subprocess.run(
        [sys.executable, str(script_path), *extra_args, "--root", str(root)],
        cwd=root,
        text=True,
        capture_output=True,
    )


def read_required_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing required output: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def numeric_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


def determine_note(
    *,
    refresh_failed_site_count: int,
    refresh_baseline_built_flag: int,
    qa_executed_flag: int,
    qa_pass_flag: int,
) -> tuple[int, str]:
    final_pass = int(
        refresh_failed_site_count == 0
        and refresh_baseline_built_flag == 1
        and qa_executed_flag == 1
        and qa_pass_flag == 1
    )
    if final_pass == 1:
        return final_pass, "전체 operator pipeline 정상"
    if refresh_failed_site_count > 0 or refresh_baseline_built_flag == 0:
        return final_pass, "site refresh 실패로 baseline/QA 미완료"
    if qa_executed_flag == 0:
        return final_pass, "baseline 미완료로 QA 건너뜀"
    return final_pass, "QA 미통과로 운영 배포 보류"


def build_manifest(
    *,
    pipeline_started_at_utc: str,
    pipeline_finished_at_utc: str,
    requested_sites_csv: str,
    refresh_manifest_row: pd.Series,
    qa_executed_flag: int,
    qa_pass_flag: int,
    qa_summary_row: pd.Series | None,
) -> pd.DataFrame:
    refresh_succeeded_site_count = numeric_int(refresh_manifest_row.get("succeeded_site_count"))
    refresh_failed_site_count = numeric_int(refresh_manifest_row.get("failed_site_count"))
    refresh_baseline_built_flag = numeric_int(refresh_manifest_row.get("baseline_built_flag"))
    qa_skip_reason = "" if qa_executed_flag == 1 else "baseline 미완료로 QA 건너뜀"

    overall_attention_count = numeric_int(qa_summary_row.get("overall_attention_count")) if qa_summary_row is not None else 0
    overall_queue_count = numeric_int(qa_summary_row.get("overall_queue_count")) if qa_summary_row is not None else 0
    overall_watch_now_count = numeric_int(qa_summary_row.get("overall_watch_now_count")) if qa_summary_row is not None else 0
    overall_watch_review_count = numeric_int(qa_summary_row.get("overall_watch_review_count")) if qa_summary_row is not None else 0
    overall_backlog_count = numeric_int(qa_summary_row.get("overall_backlog_count")) if qa_summary_row is not None else 0
    overall_changed_count = numeric_int(qa_summary_row.get("overall_changed_count")) if qa_summary_row is not None else 0
    overall_cluster_preview_count = (
        numeric_int(qa_summary_row.get("overall_cluster_preview_count")) if qa_summary_row is not None else 0
    )
    overall_discovery_cluster_count = (
        numeric_int(qa_summary_row.get("overall_discovery_cluster_count")) if qa_summary_row is not None else 0
    )
    overall_cluster_preview_future_fault_linked_ref_count = (
        numeric_int(qa_summary_row.get("overall_cluster_preview_future_fault_linked_ref_count"))
        if qa_summary_row is not None
        else 0
    )
    overall_cluster_preview_future_truth_linked_ref_count = (
        numeric_int(qa_summary_row.get("overall_cluster_preview_future_truth_linked_ref_count"))
        if qa_summary_row is not None
        else 0
    )

    final_pipeline_pass_flag, note_ko = determine_note(
        refresh_failed_site_count=refresh_failed_site_count,
        refresh_baseline_built_flag=refresh_baseline_built_flag,
        qa_executed_flag=qa_executed_flag,
        qa_pass_flag=qa_pass_flag,
    )
    final_recommended_exit_code = 0 if final_pipeline_pass_flag == 1 else 1

    row = {
        "pipeline_started_at_utc": pipeline_started_at_utc,
        "pipeline_finished_at_utc": pipeline_finished_at_utc,
        "requested_sites_csv": requested_sites_csv,
        "refresh_succeeded_site_count": refresh_succeeded_site_count,
        "refresh_failed_site_count": refresh_failed_site_count,
        "refresh_baseline_built_flag": refresh_baseline_built_flag,
        "qa_executed_flag": int(qa_executed_flag),
        "qa_skip_reason": qa_skip_reason,
        "qa_pass_flag": int(qa_pass_flag),
        "final_pipeline_pass_flag": int(final_pipeline_pass_flag),
        "final_recommended_exit_code": int(final_recommended_exit_code),
        "overall_attention_count": overall_attention_count,
        "overall_queue_count": overall_queue_count,
        "overall_watch_now_count": overall_watch_now_count,
        "overall_watch_review_count": overall_watch_review_count,
        "overall_backlog_count": overall_backlog_count,
        "overall_changed_count": overall_changed_count,
        "overall_cluster_preview_count": overall_cluster_preview_count,
        "overall_discovery_cluster_count": overall_discovery_cluster_count,
        "overall_cluster_preview_future_fault_linked_ref_count": (
            overall_cluster_preview_future_fault_linked_ref_count
        ),
        "overall_cluster_preview_future_truth_linked_ref_count": (
            overall_cluster_preview_future_truth_linked_ref_count
        ),
        "note_ko": note_ko,
    }
    return pd.DataFrame([row], columns=PIPELINE_MANIFEST_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    requested_sites = parse_sites_csv(args.sites)

    pipeline_started_at_utc = utc_now_iso()

    refresh_result = run_builder(root, REFRESH_SCRIPT, ["--sites", ",".join(requested_sites)])
    refresh_manifest = read_required_csv(share_dir / REFRESH_MANIFEST_NAME)
    if refresh_manifest.empty:
        raise SystemExit("refresh manifest is empty")
    refresh_manifest_row = refresh_manifest.iloc[0]

    qa_executed_flag = 0
    qa_pass_flag = 0
    qa_summary_row: pd.Series | None = None

    if numeric_int(refresh_manifest_row.get("baseline_built_flag")) == 1:
        qa_executed_flag = 1
        run_builder(root, QA_SCRIPT, [])
        qa_summary = read_required_csv(share_dir / QA_SUMMARY_NAME)
        if qa_summary.empty:
            raise SystemExit("qa summary is empty")
        ensure_columns(qa_summary, REQUIRED_QA_SUMMARY_COLS, QA_SUMMARY_NAME)
        qa_summary_row = qa_summary.iloc[0]
        qa_pass_flag = numeric_int(qa_summary_row.get("qa_pass_flag"))

    pipeline_finished_at_utc = utc_now_iso()
    manifest = build_manifest(
        pipeline_started_at_utc=pipeline_started_at_utc,
        pipeline_finished_at_utc=pipeline_finished_at_utc,
        requested_sites_csv=",".join(requested_sites),
        refresh_manifest_row=refresh_manifest_row,
        qa_executed_flag=qa_executed_flag,
        qa_pass_flag=qa_pass_flag,
        qa_summary_row=qa_summary_row,
    )
    manifest.to_csv(share_dir / PIPELINE_MANIFEST_NAME, index=False, encoding="utf-8-sig")

    final_exit_code = int(manifest.iloc[0]["final_recommended_exit_code"])
    if refresh_result.returncode != 0 and final_exit_code == 0:
        raise SystemExit(1)
    raise SystemExit(final_exit_code)


if __name__ == "__main__":
    main()
