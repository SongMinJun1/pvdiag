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

PIPELINE_MANIFEST_NAME = "panel_day_engine_operator_pipeline_manifest_v1.csv"
QA_SUMMARY_NAME = "panel_day_engine_operator_refresh_qa_summary_v1.csv"
BASELINE_MANIFEST_NAME = "panel_day_engine_operator_baseline_manifest_v1.csv"

REPORT_OUTPUT_NAME = "panel_day_engine_operator_pipeline_idempotence_report_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_pipeline_idempotence_summary_v1.csv"

REPORT_COLS = [
    "check_name",
    "severity",
    "status",
    "first_run_value",
    "second_run_value",
    "detail_ko",
]

SUMMARY_COLS = [
    "audit_started_at_utc",
    "audit_finished_at_utc",
    "idempotence_pass_flag",
    "fail_count",
    "pass_count",
    "first_run_pipeline_pass_flag",
    "second_run_pipeline_pass_flag",
    "second_run_changed_count",
    "second_run_cluster_delta_changed_count",
    "second_run_unified_digest_changed_count",
    "second_run_workflow_default_changed_count",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the operator pipeline twice and audit steady-state idempotence on the second run."
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


def read_required_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing required output: {path}")
    df = pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
    if df.empty:
        raise SystemExit(f"required output is empty: {path}")
    return df


def numeric_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


def run_pipeline(root: Path, requested_sites: list[str]) -> subprocess.CompletedProcess[str]:
    script_path = root / PIPELINE_SCRIPT
    if not script_path.exists():
        raise SystemExit(f"missing pipeline entrypoint: {script_path}")
    return subprocess.run(
        [sys.executable, str(script_path), "--sites", ",".join(requested_sites), "--root", str(root)],
        cwd=root,
        text=True,
        capture_output=True,
    )


def snapshot_outputs(root: Path) -> dict[str, pd.Series]:
    share_dir = root / "_share"
    pipeline_manifest = read_required_csv(share_dir / PIPELINE_MANIFEST_NAME).iloc[0].copy()
    qa_summary = read_required_csv(share_dir / QA_SUMMARY_NAME).iloc[0].copy()
    baseline_manifest = read_required_csv(share_dir / BASELINE_MANIFEST_NAME).iloc[0].copy()
    return {
        "pipeline_manifest": pipeline_manifest,
        "qa_summary": qa_summary,
        "baseline_manifest": baseline_manifest,
    }


class ReportBuilder:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = []

    def add(
        self,
        *,
        check_name: str,
        severity: str,
        status: str,
        first_run_value: object,
        second_run_value: object,
        detail_ko: str,
    ) -> None:
        self.rows.append(
            {
                "check_name": check_name,
                "severity": severity,
                "status": status,
                "first_run_value": first_run_value,
                "second_run_value": second_run_value,
                "detail_ko": detail_ko,
            }
        )

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows, columns=REPORT_COLS)


def add_equal_check(
    report: ReportBuilder,
    *,
    check_name: str,
    severity: str,
    first_run_value: int,
    second_run_value: int,
    detail_ko: str,
) -> None:
    report.add(
        check_name=check_name,
        severity=severity,
        status="pass" if first_run_value == second_run_value else "fail",
        first_run_value=first_run_value,
        second_run_value=second_run_value,
        detail_ko=detail_ko,
    )


def add_zero_check(
    report: ReportBuilder,
    *,
    check_name: str,
    severity: str,
    first_run_value: int,
    second_run_value: int,
    detail_ko: str,
) -> None:
    report.add(
        check_name=check_name,
        severity=severity,
        status="pass" if second_run_value == 0 else "fail",
        first_run_value=first_run_value,
        second_run_value=second_run_value,
        detail_ko=detail_ko,
    )


def build_report(first_snapshot: dict[str, pd.Series], second_snapshot: dict[str, pd.Series]) -> pd.DataFrame:
    report = ReportBuilder()

    first_pipeline = first_snapshot["pipeline_manifest"]
    second_pipeline = second_snapshot["pipeline_manifest"]
    first_qa = first_snapshot["qa_summary"]
    second_qa = second_snapshot["qa_summary"]
    first_baseline = first_snapshot["baseline_manifest"]
    second_baseline = second_snapshot["baseline_manifest"]

    first_run_pipeline_pass_flag = numeric_int(first_pipeline.get("final_pipeline_pass_flag"))
    second_run_pipeline_pass_flag = numeric_int(second_pipeline.get("final_pipeline_pass_flag"))
    first_run_changed_count = numeric_int(first_pipeline.get("overall_changed_count"))
    second_run_changed_count = numeric_int(second_pipeline.get("overall_changed_count"))
    first_run_cluster_delta_changed_count = numeric_int(first_qa.get("overall_cluster_delta_changed_count"))
    second_run_cluster_delta_changed_count = numeric_int(second_qa.get("overall_cluster_delta_changed_count"))
    first_run_unified_digest_changed_count = numeric_int(first_qa.get("overall_unified_digest_changed_count"))
    second_run_unified_digest_changed_count = numeric_int(second_qa.get("overall_unified_digest_changed_count"))
    first_run_workflow_default_changed_count = numeric_int(first_qa.get("overall_workflow_default_changed_count"))
    second_run_workflow_default_changed_count = numeric_int(second_qa.get("overall_workflow_default_changed_count"))

    report.add(
        check_name="first_run_pipeline_pass",
        severity="fail",
        status="pass" if first_run_pipeline_pass_flag == 1 else "fail",
        first_run_value=first_run_pipeline_pass_flag,
        second_run_value=second_run_pipeline_pass_flag,
        detail_ko="1차 run pipeline manifest final_pipeline_pass_flag가 1인지 확인",
    )
    report.add(
        check_name="second_run_pipeline_pass",
        severity="fail",
        status="pass" if second_run_pipeline_pass_flag == 1 else "fail",
        first_run_value=first_run_pipeline_pass_flag,
        second_run_value=second_run_pipeline_pass_flag,
        detail_ko="2차 run pipeline manifest final_pipeline_pass_flag가 1인지 확인",
    )
    add_zero_check(
        report,
        check_name="second_run_changed_count_zero",
        severity="fail",
        first_run_value=first_run_changed_count,
        second_run_value=second_run_changed_count,
        detail_ko="동일 입력 재실행(second run)에서 overall changed count가 0인지 확인",
    )
    add_zero_check(
        report,
        check_name="second_run_cluster_delta_changed_zero",
        severity="fail",
        first_run_value=first_run_cluster_delta_changed_count,
        second_run_value=second_run_cluster_delta_changed_count,
        detail_ko="동일 입력 재실행(second run)에서 QA summary cluster delta changed count가 0인지 확인",
    )
    add_zero_check(
        report,
        check_name="second_run_unified_digest_changed_zero",
        severity="fail",
        first_run_value=first_run_unified_digest_changed_count,
        second_run_value=second_run_unified_digest_changed_count,
        detail_ko="동일 입력 재실행(second run)에서 QA summary unified digest changed count가 0인지 확인",
    )
    add_zero_check(
        report,
        check_name="second_run_workflow_default_changed_zero",
        severity="fail",
        first_run_value=first_run_workflow_default_changed_count,
        second_run_value=second_run_workflow_default_changed_count,
        detail_ko="동일 입력 재실행(second run)에서 QA summary workflow default changed count가 0인지 확인",
    )

    add_equal_check(
        report,
        check_name="first_vs_second_attention_count_equal",
        severity="fail",
        first_run_value=numeric_int(first_pipeline.get("overall_attention_count")),
        second_run_value=numeric_int(second_pipeline.get("overall_attention_count")),
        detail_ko="1차/2차 run overall attention count가 동일한지 확인",
    )
    add_equal_check(
        report,
        check_name="first_vs_second_queue_count_equal",
        severity="fail",
        first_run_value=numeric_int(first_pipeline.get("overall_queue_count")),
        second_run_value=numeric_int(second_pipeline.get("overall_queue_count")),
        detail_ko="1차/2차 run overall queue count가 동일한지 확인",
    )
    add_equal_check(
        report,
        check_name="first_vs_second_cluster_preview_count_equal",
        severity="fail",
        first_run_value=numeric_int(first_pipeline.get("overall_cluster_preview_count")),
        second_run_value=numeric_int(second_pipeline.get("overall_cluster_preview_count")),
        detail_ko="1차/2차 run overall cluster preview count가 동일한지 확인",
    )
    add_equal_check(
        report,
        check_name="first_vs_second_discovery_cluster_count_equal",
        severity="fail",
        first_run_value=numeric_int(first_pipeline.get("overall_discovery_cluster_count")),
        second_run_value=numeric_int(second_pipeline.get("overall_discovery_cluster_count")),
        detail_ko="1차/2차 run overall discovery cluster count가 동일한지 확인",
    )
    add_equal_check(
        report,
        check_name="first_vs_second_workflow_default_count_equal",
        severity="fail",
        first_run_value=numeric_int(first_pipeline.get("overall_workflow_default_count")),
        second_run_value=numeric_int(second_pipeline.get("overall_workflow_default_count")),
        detail_ko="1차/2차 run overall workflow default count가 동일한지 확인",
    )
    add_equal_check(
        report,
        check_name="first_vs_second_qa_pass_equal",
        severity="fail",
        first_run_value=numeric_int(first_qa.get("qa_pass_flag")),
        second_run_value=numeric_int(second_qa.get("qa_pass_flag")),
        detail_ko="1차/2차 run QA pass flag가 동일한지 확인",
    )

    add_equal_check(
        report,
        check_name="first_vs_second_watch_now_count_equal",
        severity="info",
        first_run_value=numeric_int(first_pipeline.get("overall_watch_now_count")),
        second_run_value=numeric_int(second_pipeline.get("overall_watch_now_count")),
        detail_ko="1차/2차 run overall watch_now count가 동일한지 참고용으로 확인",
    )
    add_equal_check(
        report,
        check_name="first_vs_second_watch_review_count_equal",
        severity="info",
        first_run_value=numeric_int(first_pipeline.get("overall_watch_review_count")),
        second_run_value=numeric_int(second_pipeline.get("overall_watch_review_count")),
        detail_ko="1차/2차 run overall watch_review count가 동일한지 참고용으로 확인",
    )
    add_equal_check(
        report,
        check_name="first_vs_second_backlog_count_equal",
        severity="info",
        first_run_value=numeric_int(first_pipeline.get("overall_backlog_count")),
        second_run_value=numeric_int(second_pipeline.get("overall_backlog_count")),
        detail_ko="1차/2차 run overall backlog count가 동일한지 참고용으로 확인",
    )
    add_equal_check(
        report,
        check_name="first_vs_second_cluster_delta_current_count_equal",
        severity="info",
        first_run_value=numeric_int(first_pipeline.get("overall_cluster_delta_current_count")),
        second_run_value=numeric_int(second_pipeline.get("overall_cluster_delta_current_count")),
        detail_ko="1차/2차 run overall cluster delta current count가 동일한지 참고용으로 확인",
    )
    add_equal_check(
        report,
        check_name="first_vs_second_unified_digest_count_equal",
        severity="info",
        first_run_value=numeric_int(first_pipeline.get("overall_unified_digest_count")),
        second_run_value=numeric_int(second_pipeline.get("overall_unified_digest_count")),
        detail_ko="1차/2차 run overall unified digest count가 동일한지 참고용으로 확인",
    )
    add_equal_check(
        report,
        check_name="first_vs_second_qa_fail_count_equal",
        severity="info",
        first_run_value=numeric_int(first_qa.get("fail_count")),
        second_run_value=numeric_int(second_qa.get("fail_count")),
        detail_ko="1차/2차 run QA fail_count가 동일한지 참고용으로 확인",
    )
    add_equal_check(
        report,
        check_name="first_vs_second_qa_warn_count_equal",
        severity="info",
        first_run_value=numeric_int(first_qa.get("warn_count")),
        second_run_value=numeric_int(second_qa.get("warn_count")),
        detail_ko="1차/2차 run QA warn_count가 동일한지 참고용으로 확인",
    )
    add_equal_check(
        report,
        check_name="first_vs_second_baseline_attention_count_equal",
        severity="info",
        first_run_value=numeric_int(first_baseline.get("attention_count")),
        second_run_value=numeric_int(second_baseline.get("attention_count")),
        detail_ko="1차/2차 run baseline manifest attention count가 동일한지 참고용으로 확인",
    )

    return report.to_frame()


def build_summary(
    report: pd.DataFrame,
    *,
    first_snapshot: dict[str, pd.Series],
    second_snapshot: dict[str, pd.Series],
    audit_started_at_utc: str,
    audit_finished_at_utc: str,
) -> pd.DataFrame:
    hard_rows = report.loc[report["severity"].astype(str).eq("fail")].copy()
    hard_fail_count = int(hard_rows["status"].astype(str).eq("fail").sum())
    hard_pass_count = int(hard_rows["status"].astype(str).eq("pass").sum())
    idempotence_pass_flag = int(hard_fail_count == 0)

    first_pipeline = first_snapshot["pipeline_manifest"]
    second_pipeline = second_snapshot["pipeline_manifest"]
    second_qa = second_snapshot["qa_summary"]

    note_ko = (
        "동일 입력 back-to-back second run에서 spurious change 없이 steady-state가 확인됨"
        if idempotence_pass_flag == 1
        else "2차 run zero-change 또는 1/2차 핵심 count 일치 조건이 깨져 steady-state 보장에 실패함"
    )

    row = {
        "audit_started_at_utc": audit_started_at_utc,
        "audit_finished_at_utc": audit_finished_at_utc,
        "idempotence_pass_flag": idempotence_pass_flag,
        "fail_count": hard_fail_count,
        "pass_count": hard_pass_count,
        "first_run_pipeline_pass_flag": numeric_int(first_pipeline.get("final_pipeline_pass_flag")),
        "second_run_pipeline_pass_flag": numeric_int(second_pipeline.get("final_pipeline_pass_flag")),
        "second_run_changed_count": numeric_int(second_pipeline.get("overall_changed_count")),
        "second_run_cluster_delta_changed_count": numeric_int(second_qa.get("overall_cluster_delta_changed_count")),
        "second_run_unified_digest_changed_count": numeric_int(second_qa.get("overall_unified_digest_changed_count")),
        "second_run_workflow_default_changed_count": numeric_int(
            second_qa.get("overall_workflow_default_changed_count")
        ),
        "note_ko": note_ko,
    }
    return pd.DataFrame([row], columns=SUMMARY_COLS)


def save_outputs(root: Path, report: pd.DataFrame, summary: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    report.to_csv(share_dir / REPORT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    requested_sites = parse_sites_csv(args.sites)

    audit_started_at_utc = utc_now_iso()
    _ = run_pipeline(root, requested_sites)
    first_snapshot = snapshot_outputs(root)

    _ = run_pipeline(root, requested_sites)
    second_snapshot = snapshot_outputs(root)

    report = build_report(first_snapshot, second_snapshot)
    audit_finished_at_utc = utc_now_iso()
    summary = build_summary(
        report,
        first_snapshot=first_snapshot,
        second_snapshot=second_snapshot,
        audit_started_at_utc=audit_started_at_utc,
        audit_finished_at_utc=audit_finished_at_utc,
    )
    save_outputs(root, report, summary)


if __name__ == "__main__":
    main()
