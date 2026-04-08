#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REFRESH_MANIFEST_NAME = "panel_day_engine_operator_refresh_manifest_v1.csv"
REFRESH_SITE_RESULTS_NAME = "panel_day_engine_operator_refresh_site_results_v1.csv"
BASELINE_MANIFEST_NAME = "panel_day_engine_operator_baseline_manifest_v1.csv"
BASELINE_SUMMARY_NAME = "panel_day_engine_operator_baseline_summary_v1.csv"
ATTENTION_SUMMARY_NAME = "panel_day_engine_operator_attention_summary_v1.csv"
DIGEST_SUMMARY_NAME = "panel_day_engine_operator_digest_summary_v1.csv"
RUN_SUMMARY_NAME = "panel_day_engine_operator_run_summary_v1.csv"
WATCHLIST_SUMMARY_NAME = "panel_day_engine_operator_watchlist_summary_v1.csv"
RUN_WATCHLIST_SUMMARY_NAME = "panel_day_engine_operator_run_watchlist_summary_v1.csv"
CLUSTER_PREVIEW_NAME = "panel_day_engine_operator_attention_plus_discovery_cluster_preview_v1.csv"
CLUSTER_PREVIEW_SUMMARY_NAME = "panel_day_engine_operator_attention_plus_discovery_cluster_preview_summary_v1.csv"
CLUSTER_DELTA_NAME = "panel_day_engine_operator_secondary_discovery_cluster_delta_v1.csv"
CLUSTER_DELTA_SUMMARY_NAME = "panel_day_engine_operator_secondary_discovery_cluster_delta_summary_v1.csv"
UNIFIED_DIGEST_NAME = "panel_day_engine_operator_unified_digest_v1.csv"
UNIFIED_DIGEST_SUMMARY_NAME = "panel_day_engine_operator_unified_digest_summary_v1.csv"
WORKFLOW_DEFAULT_NAME = "panel_day_engine_operator_workflow_default_v1.csv"
WORKFLOW_DEFAULT_SUMMARY_NAME = "panel_day_engine_operator_workflow_default_summary_v1.csv"

QA_REPORT_NAME = "panel_day_engine_operator_refresh_qa_report_v1.csv"
QA_SUMMARY_NAME = "panel_day_engine_operator_refresh_qa_summary_v1.csv"

QUEUE_COUNT_WARN_THRESHOLD = 20
ATTENTION_COUNT_WARN_THRESHOLD = 50
WATCH_NOW_COUNT_WARN_THRESHOLD = 40
BACKLOG_QUEUE_RATIO_WARN_THRESHOLD = 500.0
CLUSTER_PREVIEW_COUNT_WARN_THRESHOLD = 35
DISCOVERY_CLUSTER_COUNT_WARN_THRESHOLD = 10
UNIFIED_DIGEST_COUNT_WARN_THRESHOLD = 30
WORKFLOW_DEFAULT_COUNT_WARN_THRESHOLD = 30

QA_REPORT_COLS = [
    "check_name",
    "severity",
    "status",
    "observed_value",
    "expected_value",
    "detail_ko",
]

QA_SUMMARY_COLS = [
    "generated_at_utc",
    "qa_pass_flag",
    "fail_count",
    "warn_count",
    "pass_count",
    "skip_count",
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
    "overall_cluster_delta_current_count",
    "overall_cluster_delta_changed_count",
    "overall_cluster_delta_new_count",
    "overall_cluster_delta_dropped_count",
    "overall_cluster_delta_representative_changed_count",
    "overall_cluster_delta_linked_ref_changed_count",
    "overall_unified_digest_count",
    "overall_unified_digest_queue_run_count",
    "overall_unified_digest_watch_now_panel_count",
    "overall_unified_digest_secondary_value_cluster_count",
    "overall_unified_digest_changed_count",
    "overall_unified_digest_changed_attention_count",
    "overall_unified_digest_changed_cluster_count",
    "overall_workflow_default_count",
    "overall_workflow_default_queue_run_count",
    "overall_workflow_default_watch_now_panel_count",
    "overall_workflow_default_secondary_value_cluster_count",
    "overall_workflow_default_changed_count",
    "overall_workflow_default_primary_attention_count",
    "overall_workflow_default_supplemental_discovery_count",
    "overall_workflow_default_linked_ref_count",
    "overall_workflow_default_truth_ref_count",
]

REQUIRED_SUMMARY_FILES = {
    "refresh_manifest_exists": REFRESH_MANIFEST_NAME,
    "site_results_exists": REFRESH_SITE_RESULTS_NAME,
    "baseline_manifest_exists": BASELINE_MANIFEST_NAME,
    "baseline_summary_exists": BASELINE_SUMMARY_NAME,
    "attention_summary_exists": ATTENTION_SUMMARY_NAME,
    "digest_summary_exists": DIGEST_SUMMARY_NAME,
    "cluster_preview_exists": CLUSTER_PREVIEW_NAME,
    "cluster_preview_summary_exists": CLUSTER_PREVIEW_SUMMARY_NAME,
    "cluster_delta_exists": CLUSTER_DELTA_NAME,
    "cluster_delta_summary_exists": CLUSTER_DELTA_SUMMARY_NAME,
    "unified_digest_exists": UNIFIED_DIGEST_NAME,
    "unified_digest_summary_exists": UNIFIED_DIGEST_SUMMARY_NAME,
    "workflow_default_exists": WORKFLOW_DEFAULT_NAME,
    "workflow_default_summary_exists": WORKFLOW_DEFAULT_SUMMARY_NAME,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate that the latest operator refresh produced a coherent refresh/baseline/digest stack."
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


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def parse_iso_datetime(value: object) -> pd.Timestamp:
    if pd.isna(value):
        return pd.NaT
    text = str(value).strip()
    if not text:
        return pd.NaT
    return pd.to_datetime(text, utc=True, errors="coerce")


def numeric_value(value: object, default: float = 0.0) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return float(default if pd.isna(numeric) else numeric)


def read_csv_if_exists(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


class QaReportBuilder:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = []

    def add(
        self,
        check_name: str,
        severity: str,
        status: str,
        observed_value: object,
        expected_value: object,
        detail_ko: str,
    ) -> None:
        self.rows.append(
            {
                "check_name": check_name,
                "severity": severity,
                "status": status,
                "observed_value": observed_value,
                "expected_value": expected_value,
                "detail_ko": detail_ko,
            }
        )

    def fail_exists(self, check_name: str, file_name: str, exists: bool) -> None:
        self.add(
            check_name=check_name,
            severity="fail",
            status="pass" if exists else "fail",
            observed_value="exists" if exists else "missing",
            expected_value="exists",
            detail_ko=f"필수 입력 파일 확인: {file_name}",
        )

    def skip(self, check_name: str, severity: str, detail_ko: str) -> None:
        self.add(
            check_name=check_name,
            severity=severity,
            status="skip",
            observed_value="",
            expected_value="",
            detail_ko=detail_ko,
        )

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows, columns=QA_REPORT_COLS)


def ensure_summary_identity(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    if "record_type" in normalized.columns:
        normalized["record_type"] = normalized["record_type"].map(normalize_text)
    if "site" in normalized.columns:
        normalized["site"] = normalized["site"].map(normalize_text)
    return normalized


def extract_overall_row(df: pd.DataFrame | None) -> pd.Series | None:
    if df is None or "record_type" not in df.columns:
        return None
    normalized = ensure_summary_identity(df)
    overall_rows = normalized.loc[normalized["record_type"].eq("overall")]
    if overall_rows.empty:
        return None
    return overall_rows.iloc[0]


def extract_site_rows(df: pd.DataFrame | None) -> pd.DataFrame | None:
    if df is None or "record_type" not in df.columns:
        return None
    normalized = ensure_summary_identity(df)
    return normalized.loc[normalized["record_type"].eq("site")].reset_index(drop=True)


def run_hard_checks(
    report: QaReportBuilder,
    *,
    refresh_manifest: pd.DataFrame | None,
    site_results: pd.DataFrame | None,
    baseline_manifest: pd.DataFrame | None,
    baseline_summary: pd.DataFrame | None,
    attention_summary: pd.DataFrame | None,
    digest_summary: pd.DataFrame | None,
    run_summary: pd.DataFrame | None,
    cluster_preview_summary: pd.DataFrame | None,
    cluster_delta_summary: pd.DataFrame | None,
    unified_digest_summary: pd.DataFrame | None,
    workflow_default_summary: pd.DataFrame | None,
) -> None:
    refresh_manifest_row = refresh_manifest.iloc[0] if refresh_manifest is not None and not refresh_manifest.empty else None
    baseline_manifest_row = baseline_manifest.iloc[0] if baseline_manifest is not None and not baseline_manifest.empty else None
    baseline_overall = extract_overall_row(baseline_summary)
    baseline_sites = extract_site_rows(baseline_summary)
    digest_overall = extract_overall_row(digest_summary)
    run_overall = extract_overall_row(run_summary)
    cluster_preview_overall = extract_overall_row(cluster_preview_summary)
    cluster_preview_sites = extract_site_rows(cluster_preview_summary)
    cluster_delta_overall = extract_overall_row(cluster_delta_summary)
    cluster_delta_sites = extract_site_rows(cluster_delta_summary)
    unified_digest_overall = extract_overall_row(unified_digest_summary)
    unified_digest_sites = extract_site_rows(unified_digest_summary)
    workflow_default_overall = extract_overall_row(workflow_default_summary)
    workflow_default_sites = extract_site_rows(workflow_default_summary)

    if refresh_manifest_row is None:
        report.skip("all_requested_sites_succeeded", "fail", "refresh manifest 없음으로 site 성공 여부를 판정할 수 없음")
        report.skip("baseline_built", "fail", "refresh manifest 없음으로 baseline build 여부를 판정할 수 없음")
        report.skip("refresh_finish_after_start", "fail", "refresh manifest 없음으로 refresh 시간 순서를 판정할 수 없음")
    else:
        failed_site_count = int(numeric_value(refresh_manifest_row.get("failed_site_count")))
        report.add(
            "all_requested_sites_succeeded",
            "fail",
            "pass" if failed_site_count == 0 else "fail",
            observed_value=failed_site_count,
            expected_value=0,
            detail_ko="refresh manifest 기준 실패 site 수",
        )
        baseline_built_flag = int(numeric_value(refresh_manifest_row.get("baseline_built_flag")))
        report.add(
            "baseline_built",
            "fail",
            "pass" if baseline_built_flag == 1 else "fail",
            observed_value=baseline_built_flag,
            expected_value=1,
            detail_ko="site refresh 완료 후 baseline builder 실행 여부",
        )
        started_at = parse_iso_datetime(refresh_manifest_row.get("refresh_started_at_utc"))
        finished_at = parse_iso_datetime(refresh_manifest_row.get("refresh_finished_at_utc"))
        time_ok = pd.notna(started_at) and pd.notna(finished_at) and finished_at > started_at
        report.add(
            "refresh_finish_after_start",
            "fail",
            "pass" if time_ok else "fail",
            observed_value=str(finished_at) if pd.notna(finished_at) else "",
            expected_value="> refresh_started_at_utc",
            detail_ko="refresh 시작/종료 시각 순서 확인",
        )

    if site_results is None:
        report.skip("refresh_duration_present", "fail", "site results 없음으로 duration 검증을 건너뜀")
    else:
        durations = pd.to_numeric(site_results.get("duration_seconds"), errors="coerce")
        duration_ok = bool(len(site_results) > 0) and durations.notna().all() and (durations > 0).all()
        report.add(
            "refresh_duration_present",
            "fail",
            "pass" if duration_ok else "fail",
            observed_value=int(durations.notna().sum()) if durations is not None else 0,
            expected_value=f"{len(site_results)} positive durations",
            detail_ko="모든 requested site에 대해 양수 duration 기록 여부",
        )

    if baseline_manifest_row is None:
        report.skip("attention_digest_count_match", "fail", "baseline manifest 없음으로 attention/digest count 비교를 건너뜀")
        report.skip("attention_queue_watch_match", "fail", "baseline manifest 없음으로 queue/watch 합 비교를 건너뜀")
    else:
        attention_count = int(numeric_value(baseline_manifest_row.get("attention_count")))
        digest_attention_count = int(numeric_value(baseline_manifest_row.get("digest_attention_count")))
        report.add(
            "attention_digest_count_match",
            "fail",
            "pass" if attention_count == digest_attention_count else "fail",
            observed_value=f"{attention_count} vs {digest_attention_count}",
            expected_value="attention_count == digest_attention_count",
            detail_ko="baseline manifest 기준 attention/digest count 일치 여부",
        )
        digest_queue = int(numeric_value(baseline_manifest_row.get("digest_queue_run_count")))
        digest_watch = int(numeric_value(baseline_manifest_row.get("digest_watch_now_panel_count")))
        report.add(
            "attention_queue_watch_match",
            "fail",
            "pass" if attention_count == (digest_queue + digest_watch) else "fail",
            observed_value=f"{attention_count} vs {digest_queue + digest_watch}",
            expected_value="attention_count == digest_queue_run_count + digest_watch_now_panel_count",
            detail_ko="attention count가 queue + watch_now_panel 합과 맞는지 확인",
        )

    if run_overall is None:
        report.skip("watchlist_partition_match", "fail", "run summary 없음으로 watchlist partition 검증을 건너뜀")
    else:
        watchlist_count = int(numeric_value(run_overall.get("watchlist_count")))
        watch_now_count = int(numeric_value(run_overall.get("watch_now_count")))
        watch_review_count = int(numeric_value(run_overall.get("watch_review_count")))
        report.add(
            "watchlist_partition_match",
            "fail",
            "pass" if watchlist_count == (watch_now_count + watch_review_count) else "fail",
            observed_value=f"{watchlist_count} vs {watch_now_count + watch_review_count}",
            expected_value="watchlist_count == watch_now_count + watch_review_count",
            detail_ko="watchlist가 watch_now / watch_review로 완전히 분할되는지 확인",
        )

    if baseline_overall is None or baseline_sites is None:
        report.skip("site_sum_matches_overall_attention", "fail", "baseline summary 없음으로 site attention 합 검증을 건너뜀")
        report.skip("site_sum_matches_overall_queue", "fail", "baseline summary 없음으로 site queue 합 검증을 건너뜀")
        report.skip("site_sum_matches_overall_watch_now_panel", "fail", "baseline summary 없음으로 site watch_now_panel 합 검증을 건너뜀")
    else:
        overall_attention = int(numeric_value(baseline_overall.get("attention_count")))
        site_attention_sum = int(pd.to_numeric(baseline_sites["attention_count"], errors="coerce").fillna(0).sum())
        report.add(
            "site_sum_matches_overall_attention",
            "fail",
            "pass" if site_attention_sum == overall_attention else "fail",
            observed_value=site_attention_sum,
            expected_value=overall_attention,
            detail_ko="baseline summary per-site attention 합이 overall과 일치하는지 확인",
        )
        overall_queue = int(numeric_value(baseline_overall.get("queue_count")))
        site_queue_sum = int(pd.to_numeric(baseline_sites["queue_count"], errors="coerce").fillna(0).sum())
        report.add(
            "site_sum_matches_overall_queue",
            "fail",
            "pass" if site_queue_sum == overall_queue else "fail",
            observed_value=site_queue_sum,
            expected_value=overall_queue,
            detail_ko="baseline summary per-site queue 합이 overall과 일치하는지 확인",
        )
        overall_watch_panel = int(numeric_value(baseline_overall.get("digest_watch_now_panel_count")))
        site_watch_panel_sum = int(
            pd.to_numeric(baseline_sites["digest_watch_now_panel_count"], errors="coerce").fillna(0).sum()
        )
        report.add(
            "site_sum_matches_overall_watch_now_panel",
            "fail",
            "pass" if site_watch_panel_sum == overall_watch_panel else "fail",
            observed_value=site_watch_panel_sum,
            expected_value=overall_watch_panel,
            detail_ko="baseline summary per-site watch_now_panel 합이 overall과 일치하는지 확인",
        )

    if baseline_manifest_row is None or cluster_preview_overall is None:
        report.skip(
            "cluster_preview_count_match_manifest",
            "fail",
            "baseline manifest 또는 cluster preview summary 없음으로 cluster preview count 검증을 건너뜀",
        )
        report.skip(
            "cluster_preview_secondary_count_match_manifest",
            "fail",
            "baseline manifest 또는 cluster preview summary 없음으로 discovery cluster count 검증을 건너뜀",
        )
        report.skip(
            "cluster_preview_fault_ref_count_match_manifest",
            "fail",
            "baseline manifest 또는 cluster preview summary 없음으로 cluster fault ref count 검증을 건너뜀",
        )
        report.skip(
            "cluster_preview_truth_ref_count_match_manifest",
            "fail",
            "baseline manifest 또는 cluster preview summary 없음으로 cluster truth ref count 검증을 건너뜀",
        )
    else:
        manifest_cluster_preview_count = int(numeric_value(baseline_manifest_row.get("cluster_preview_count")))
        summary_cluster_preview_count = int(numeric_value(cluster_preview_overall.get("cluster_preview_count")))
        report.add(
            "cluster_preview_count_match_manifest",
            "fail",
            "pass" if manifest_cluster_preview_count == summary_cluster_preview_count else "fail",
            observed_value=f"{manifest_cluster_preview_count} vs {summary_cluster_preview_count}",
            expected_value="baseline manifest cluster_preview_count == cluster preview summary overall cluster_preview_count",
            detail_ko="baseline manifest와 cluster preview summary의 overall preview count가 일치하는지 확인",
        )

        manifest_secondary_cluster_count = int(
            numeric_value(baseline_manifest_row.get("cluster_preview_secondary_value_cluster_count"))
        )
        summary_secondary_cluster_count = int(numeric_value(cluster_preview_overall.get("secondary_value_cluster_count")))
        report.add(
            "cluster_preview_secondary_count_match_manifest",
            "fail",
            "pass" if manifest_secondary_cluster_count == summary_secondary_cluster_count else "fail",
            observed_value=f"{manifest_secondary_cluster_count} vs {summary_secondary_cluster_count}",
            expected_value=(
                "baseline manifest cluster_preview_secondary_value_cluster_count == "
                "cluster preview summary overall secondary_value_cluster_count"
            ),
            detail_ko="baseline manifest와 cluster preview summary의 discovery cluster 수가 일치하는지 확인",
        )

        manifest_fault_ref_count = int(numeric_value(baseline_manifest_row.get("cluster_preview_future_fault_linked_ref_count")))
        summary_fault_ref_count = int(
            numeric_value(cluster_preview_overall.get("clusters_with_future_fault_linked_ref_count"))
        )
        report.add(
            "cluster_preview_fault_ref_count_match_manifest",
            "fail",
            "pass" if manifest_fault_ref_count == summary_fault_ref_count else "fail",
            observed_value=f"{manifest_fault_ref_count} vs {summary_fault_ref_count}",
            expected_value=(
                "baseline manifest cluster_preview_future_fault_linked_ref_count == "
                "cluster preview summary overall clusters_with_future_fault_linked_ref_count"
            ),
            detail_ko="baseline manifest와 cluster preview summary의 retrospective future fault linked cluster 수가 일치하는지 확인",
        )

        manifest_truth_ref_count = int(numeric_value(baseline_manifest_row.get("cluster_preview_future_truth_linked_ref_count")))
        summary_truth_ref_count = int(
            numeric_value(cluster_preview_overall.get("clusters_with_future_truth_linked_ref_count"))
        )
        report.add(
            "cluster_preview_truth_ref_count_match_manifest",
            "fail",
            "pass" if manifest_truth_ref_count == summary_truth_ref_count else "fail",
            observed_value=f"{manifest_truth_ref_count} vs {summary_truth_ref_count}",
            expected_value=(
                "baseline manifest cluster_preview_future_truth_linked_ref_count == "
                "cluster preview summary overall clusters_with_future_truth_linked_ref_count"
            ),
            detail_ko="baseline manifest와 cluster preview summary의 retrospective future truth linked cluster 수가 일치하는지 확인",
        )

    if baseline_overall is None or cluster_preview_overall is None:
        report.skip(
            "cluster_preview_count_matches_attention_plus_clusters",
            "fail",
            "baseline summary 또는 cluster preview summary 없음으로 preview total count 검증을 건너뜀",
        )
    else:
        overall_attention = int(numeric_value(baseline_overall.get("attention_count")))
        overall_secondary_clusters = int(numeric_value(cluster_preview_overall.get("secondary_value_cluster_count")))
        overall_cluster_preview_count = int(numeric_value(cluster_preview_overall.get("cluster_preview_count")))
        expected_cluster_preview_count = overall_attention + overall_secondary_clusters
        report.add(
            "cluster_preview_count_matches_attention_plus_clusters",
            "fail",
            "pass" if overall_cluster_preview_count == expected_cluster_preview_count else "fail",
            observed_value=overall_cluster_preview_count,
            expected_value=expected_cluster_preview_count,
            detail_ko="cluster preview overall count가 baseline attention 수와 discovery cluster 수의 합과 일치하는지 확인",
        )

    if cluster_preview_overall is None or cluster_preview_sites is None:
        report.skip(
            "cluster_preview_site_sum_matches_overall",
            "fail",
            "cluster preview summary 없음으로 per-site cluster preview 합 검증을 건너뜀",
        )
    else:
        overall_cluster_preview_count = int(numeric_value(cluster_preview_overall.get("cluster_preview_count")))
        site_cluster_preview_sum = int(
            pd.to_numeric(cluster_preview_sites["cluster_preview_count"], errors="coerce").fillna(0).sum()
        )
        report.add(
            "cluster_preview_site_sum_matches_overall",
            "fail",
            "pass" if site_cluster_preview_sum == overall_cluster_preview_count else "fail",
            observed_value=site_cluster_preview_sum,
            expected_value=overall_cluster_preview_count,
            detail_ko="cluster preview summary per-site preview count 합이 overall과 일치하는지 확인",
        )

    if baseline_manifest_row is None or cluster_delta_overall is None:
        report.skip(
            "cluster_delta_current_count_match_manifest",
            "fail",
            "baseline manifest 또는 cluster delta summary 없음으로 cluster delta current count 검증을 건너뜀",
        )
        report.skip(
            "cluster_delta_changed_count_match_manifest",
            "fail",
            "baseline manifest 또는 cluster delta summary 없음으로 cluster delta changed count 검증을 건너뜀",
        )
        report.skip(
            "cluster_delta_new_count_match_manifest",
            "fail",
            "baseline manifest 또는 cluster delta summary 없음으로 cluster delta new count 검증을 건너뜀",
        )
        report.skip(
            "cluster_delta_dropped_count_match_manifest",
            "fail",
            "baseline manifest 또는 cluster delta summary 없음으로 cluster delta dropped count 검증을 건너뜀",
        )
        report.skip(
            "cluster_delta_representative_changed_count_match_manifest",
            "fail",
            "baseline manifest 또는 cluster delta summary 없음으로 representative changed count 검증을 건너뜀",
        )
        report.skip(
            "cluster_delta_linked_ref_changed_count_match_manifest",
            "fail",
            "baseline manifest 또는 cluster delta summary 없음으로 linked ref changed count 검증을 건너뜀",
        )
    else:
        manifest_current_cluster_count = int(numeric_value(baseline_manifest_row.get("cluster_delta_current_count")))
        summary_current_cluster_count = int(numeric_value(cluster_delta_overall.get("current_cluster_count")))
        report.add(
            "cluster_delta_current_count_match_manifest",
            "fail",
            "pass" if manifest_current_cluster_count == summary_current_cluster_count else "fail",
            observed_value=f"{manifest_current_cluster_count} vs {summary_current_cluster_count}",
            expected_value="baseline manifest cluster_delta_current_count == cluster delta summary overall current_cluster_count",
            detail_ko="baseline manifest와 cluster delta summary의 overall current cluster 수가 일치하는지 확인",
        )
        manifest_changed_cluster_count = int(numeric_value(baseline_manifest_row.get("cluster_delta_changed_count")))
        summary_changed_cluster_count = int(numeric_value(cluster_delta_overall.get("changed_cluster_count")))
        report.add(
            "cluster_delta_changed_count_match_manifest",
            "fail",
            "pass" if manifest_changed_cluster_count == summary_changed_cluster_count else "fail",
            observed_value=f"{manifest_changed_cluster_count} vs {summary_changed_cluster_count}",
            expected_value="baseline manifest cluster_delta_changed_count == cluster delta summary overall changed_cluster_count",
            detail_ko="baseline manifest와 cluster delta summary의 overall changed cluster 수가 일치하는지 확인",
        )
        manifest_new_cluster_count = int(numeric_value(baseline_manifest_row.get("cluster_delta_new_count")))
        summary_new_cluster_count = int(numeric_value(cluster_delta_overall.get("new_cluster_count")))
        report.add(
            "cluster_delta_new_count_match_manifest",
            "fail",
            "pass" if manifest_new_cluster_count == summary_new_cluster_count else "fail",
            observed_value=f"{manifest_new_cluster_count} vs {summary_new_cluster_count}",
            expected_value="baseline manifest cluster_delta_new_count == cluster delta summary overall new_cluster_count",
            detail_ko="baseline manifest와 cluster delta summary의 overall new cluster 수가 일치하는지 확인",
        )
        manifest_dropped_cluster_count = int(numeric_value(baseline_manifest_row.get("cluster_delta_dropped_count")))
        summary_dropped_cluster_count = int(numeric_value(cluster_delta_overall.get("dropped_cluster_count")))
        report.add(
            "cluster_delta_dropped_count_match_manifest",
            "fail",
            "pass" if manifest_dropped_cluster_count == summary_dropped_cluster_count else "fail",
            observed_value=f"{manifest_dropped_cluster_count} vs {summary_dropped_cluster_count}",
            expected_value="baseline manifest cluster_delta_dropped_count == cluster delta summary overall dropped_cluster_count",
            detail_ko="baseline manifest와 cluster delta summary의 overall dropped cluster 수가 일치하는지 확인",
        )
        manifest_representative_changed_count = int(
            numeric_value(baseline_manifest_row.get("cluster_delta_representative_changed_count"))
        )
        summary_representative_changed_count = int(numeric_value(cluster_delta_overall.get("representative_changed_count")))
        report.add(
            "cluster_delta_representative_changed_count_match_manifest",
            "fail",
            "pass" if manifest_representative_changed_count == summary_representative_changed_count else "fail",
            observed_value=f"{manifest_representative_changed_count} vs {summary_representative_changed_count}",
            expected_value=(
                "baseline manifest cluster_delta_representative_changed_count == "
                "cluster delta summary overall representative_changed_count"
            ),
            detail_ko="baseline manifest와 cluster delta summary의 representative changed 수가 일치하는지 확인",
        )
        manifest_linked_ref_changed_count = int(
            numeric_value(baseline_manifest_row.get("cluster_delta_linked_ref_changed_count"))
        )
        summary_linked_ref_changed_count = int(numeric_value(cluster_delta_overall.get("linked_ref_changed_count")))
        report.add(
            "cluster_delta_linked_ref_changed_count_match_manifest",
            "fail",
            "pass" if manifest_linked_ref_changed_count == summary_linked_ref_changed_count else "fail",
            observed_value=f"{manifest_linked_ref_changed_count} vs {summary_linked_ref_changed_count}",
            expected_value=(
                "baseline manifest cluster_delta_linked_ref_changed_count == "
                "cluster delta summary overall linked_ref_changed_count"
            ),
            detail_ko="baseline manifest와 cluster delta summary의 linked ref changed 수가 일치하는지 확인",
        )

    if cluster_delta_overall is None or cluster_delta_sites is None:
        report.skip(
            "cluster_delta_site_sum_matches_overall",
            "fail",
            "cluster delta summary 없음으로 per-site cluster delta 합 검증을 건너뜀",
        )
    else:
        overall_current_cluster_count = int(numeric_value(cluster_delta_overall.get("current_cluster_count")))
        site_current_cluster_sum = int(
            pd.to_numeric(cluster_delta_sites["current_cluster_count"], errors="coerce").fillna(0).sum()
        )
        overall_changed_cluster_count = int(numeric_value(cluster_delta_overall.get("changed_cluster_count")))
        site_changed_cluster_sum = int(
            pd.to_numeric(cluster_delta_sites["changed_cluster_count"], errors="coerce").fillna(0).sum()
        )
        overall_new_cluster_count = int(numeric_value(cluster_delta_overall.get("new_cluster_count")))
        site_new_cluster_sum = int(
            pd.to_numeric(cluster_delta_sites["new_cluster_count"], errors="coerce").fillna(0).sum()
        )
        overall_dropped_cluster_count = int(numeric_value(cluster_delta_overall.get("dropped_cluster_count")))
        site_dropped_cluster_sum = int(
            pd.to_numeric(cluster_delta_sites["dropped_cluster_count"], errors="coerce").fillna(0).sum()
        )
        sums_ok = (
            site_current_cluster_sum == overall_current_cluster_count
            and site_changed_cluster_sum == overall_changed_cluster_count
            and site_new_cluster_sum == overall_new_cluster_count
            and site_dropped_cluster_sum == overall_dropped_cluster_count
        )
        report.add(
            "cluster_delta_site_sum_matches_overall",
            "fail",
            "pass" if sums_ok else "fail",
            observed_value=(
                f"current {site_current_cluster_sum}/{overall_current_cluster_count}, "
                f"changed {site_changed_cluster_sum}/{overall_changed_cluster_count}, "
                f"new {site_new_cluster_sum}/{overall_new_cluster_count}, "
                f"dropped {site_dropped_cluster_sum}/{overall_dropped_cluster_count}"
            ),
            expected_value="per-site current/changed/new/dropped sums == overall",
            detail_ko="cluster delta summary per-site current/changed/new/dropped 합이 overall과 각각 일치하는지 확인",
        )

    if baseline_manifest_row is None or unified_digest_overall is None:
        report.skip(
            "unified_digest_count_match_manifest",
            "fail",
            "baseline manifest 또는 unified digest summary 없음으로 unified digest count 검증을 건너뜀",
        )
        report.skip(
            "unified_digest_queue_count_match_manifest",
            "fail",
            "baseline manifest 또는 unified digest summary 없음으로 unified digest queue count 검증을 건너뜀",
        )
        report.skip(
            "unified_digest_watch_now_count_match_manifest",
            "fail",
            "baseline manifest 또는 unified digest summary 없음으로 unified digest watch_now count 검증을 건너뜀",
        )
        report.skip(
            "unified_digest_secondary_cluster_count_match_manifest",
            "fail",
            "baseline manifest 또는 unified digest summary 없음으로 unified digest secondary cluster count 검증을 건너뜀",
        )
        report.skip(
            "unified_digest_changed_count_match_manifest",
            "fail",
            "baseline manifest 또는 unified digest summary 없음으로 unified digest changed count 검증을 건너뜀",
        )
        report.skip(
            "unified_digest_changed_attention_count_match_manifest",
            "fail",
            "baseline manifest 또는 unified digest summary 없음으로 unified digest changed attention count 검증을 건너뜀",
        )
        report.skip(
            "unified_digest_changed_cluster_count_match_manifest",
            "fail",
            "baseline manifest 또는 unified digest summary 없음으로 unified digest changed cluster count 검증을 건너뜀",
        )
    else:
        unified_manifest_count = int(numeric_value(baseline_manifest_row.get("unified_digest_count")))
        unified_summary_count = int(numeric_value(unified_digest_overall.get("digest_count")))
        report.add(
            "unified_digest_count_match_manifest",
            "fail",
            "pass" if unified_manifest_count == unified_summary_count else "fail",
            observed_value=f"{unified_manifest_count} vs {unified_summary_count}",
            expected_value="baseline manifest unified_digest_count == unified digest summary overall digest_count",
            detail_ko="baseline manifest와 unified digest summary의 overall digest count가 일치하는지 확인",
        )
        unified_manifest_queue = int(numeric_value(baseline_manifest_row.get("unified_digest_queue_run_count")))
        unified_summary_queue = int(numeric_value(unified_digest_overall.get("queue_run_count")))
        report.add(
            "unified_digest_queue_count_match_manifest",
            "fail",
            "pass" if unified_manifest_queue == unified_summary_queue else "fail",
            observed_value=f"{unified_manifest_queue} vs {unified_summary_queue}",
            expected_value="baseline manifest unified_digest_queue_run_count == unified digest summary overall queue_run_count",
            detail_ko="baseline manifest와 unified digest summary의 overall queue_run count가 일치하는지 확인",
        )
        unified_manifest_watch = int(numeric_value(baseline_manifest_row.get("unified_digest_watch_now_panel_count")))
        unified_summary_watch = int(numeric_value(unified_digest_overall.get("watch_now_panel_count")))
        report.add(
            "unified_digest_watch_now_count_match_manifest",
            "fail",
            "pass" if unified_manifest_watch == unified_summary_watch else "fail",
            observed_value=f"{unified_manifest_watch} vs {unified_summary_watch}",
            expected_value=(
                "baseline manifest unified_digest_watch_now_panel_count == unified digest summary overall watch_now_panel_count"
            ),
            detail_ko="baseline manifest와 unified digest summary의 overall watch_now_panel count가 일치하는지 확인",
        )
        unified_manifest_cluster = int(
            numeric_value(baseline_manifest_row.get("unified_digest_secondary_value_cluster_count"))
        )
        unified_summary_cluster = int(numeric_value(unified_digest_overall.get("secondary_value_cluster_count")))
        report.add(
            "unified_digest_secondary_cluster_count_match_manifest",
            "fail",
            "pass" if unified_manifest_cluster == unified_summary_cluster else "fail",
            observed_value=f"{unified_manifest_cluster} vs {unified_summary_cluster}",
            expected_value=(
                "baseline manifest unified_digest_secondary_value_cluster_count == "
                "unified digest summary overall secondary_value_cluster_count"
            ),
            detail_ko="baseline manifest와 unified digest summary의 overall secondary_value_cluster count가 일치하는지 확인",
        )
        unified_manifest_changed = int(numeric_value(baseline_manifest_row.get("unified_digest_changed_count")))
        unified_summary_changed = int(numeric_value(unified_digest_overall.get("changed_count")))
        report.add(
            "unified_digest_changed_count_match_manifest",
            "fail",
            "pass" if unified_manifest_changed == unified_summary_changed else "fail",
            observed_value=f"{unified_manifest_changed} vs {unified_summary_changed}",
            expected_value="baseline manifest unified_digest_changed_count == unified digest summary overall changed_count",
            detail_ko="baseline manifest와 unified digest summary의 overall changed count가 일치하는지 확인",
        )
        unified_manifest_changed_attention = int(
            numeric_value(baseline_manifest_row.get("unified_digest_changed_attention_count"))
        )
        unified_summary_changed_attention = int(numeric_value(unified_digest_overall.get("changed_attention_count")))
        report.add(
            "unified_digest_changed_attention_count_match_manifest",
            "fail",
            "pass" if unified_manifest_changed_attention == unified_summary_changed_attention else "fail",
            observed_value=f"{unified_manifest_changed_attention} vs {unified_summary_changed_attention}",
            expected_value=(
                "baseline manifest unified_digest_changed_attention_count == "
                "unified digest summary overall changed_attention_count"
            ),
            detail_ko="baseline manifest와 unified digest summary의 overall changed_attention count가 일치하는지 확인",
        )
        unified_manifest_changed_cluster = int(
            numeric_value(baseline_manifest_row.get("unified_digest_changed_cluster_count"))
        )
        unified_summary_changed_cluster = int(numeric_value(unified_digest_overall.get("changed_cluster_count")))
        report.add(
            "unified_digest_changed_cluster_count_match_manifest",
            "fail",
            "pass" if unified_manifest_changed_cluster == unified_summary_changed_cluster else "fail",
            observed_value=f"{unified_manifest_changed_cluster} vs {unified_summary_changed_cluster}",
            expected_value=(
                "baseline manifest unified_digest_changed_cluster_count == "
                "unified digest summary overall changed_cluster_count"
            ),
            detail_ko="baseline manifest와 unified digest summary의 overall changed_cluster count가 일치하는지 확인",
        )

    if baseline_overall is None or unified_digest_overall is None:
        report.skip(
            "unified_digest_count_matches_attention_plus_clusters",
            "fail",
            "baseline summary 또는 unified digest summary 없음으로 unified digest total count 검증을 건너뜀",
        )
    else:
        overall_attention = int(numeric_value(baseline_overall.get("attention_count")))
        overall_discovery_clusters = int(numeric_value(baseline_overall.get("discovery_cluster_count")))
        overall_unified_digest_count = int(numeric_value(unified_digest_overall.get("digest_count")))
        expected_unified_digest_count = overall_attention + overall_discovery_clusters
        report.add(
            "unified_digest_count_matches_attention_plus_clusters",
            "fail",
            "pass" if overall_unified_digest_count == expected_unified_digest_count else "fail",
            observed_value=overall_unified_digest_count,
            expected_value=expected_unified_digest_count,
            detail_ko="unified digest overall count가 baseline attention 수와 discovery cluster 수의 합과 일치하는지 확인",
        )

    if unified_digest_overall is None or unified_digest_sites is None:
        report.skip(
            "unified_digest_site_sum_matches_overall",
            "fail",
            "unified digest summary 없음으로 per-site unified digest 합 검증을 건너뜀",
        )
    else:
        overall_digest_count = int(numeric_value(unified_digest_overall.get("digest_count")))
        overall_queue_run_count = int(numeric_value(unified_digest_overall.get("queue_run_count")))
        overall_watch_now_panel_count = int(numeric_value(unified_digest_overall.get("watch_now_panel_count")))
        overall_secondary_value_cluster_count = int(
            numeric_value(unified_digest_overall.get("secondary_value_cluster_count"))
        )
        overall_changed_count = int(numeric_value(unified_digest_overall.get("changed_count")))
        site_digest_count_sum = int(pd.to_numeric(unified_digest_sites["digest_count"], errors="coerce").fillna(0).sum())
        site_queue_run_sum = int(
            pd.to_numeric(unified_digest_sites["queue_run_count"], errors="coerce").fillna(0).sum()
        )
        site_watch_now_sum = int(
            pd.to_numeric(unified_digest_sites["watch_now_panel_count"], errors="coerce").fillna(0).sum()
        )
        site_secondary_cluster_sum = int(
            pd.to_numeric(unified_digest_sites["secondary_value_cluster_count"], errors="coerce").fillna(0).sum()
        )
        site_changed_sum = int(pd.to_numeric(unified_digest_sites["changed_count"], errors="coerce").fillna(0).sum())
        sums_ok = (
            site_digest_count_sum == overall_digest_count
            and site_queue_run_sum == overall_queue_run_count
            and site_watch_now_sum == overall_watch_now_panel_count
            and site_secondary_cluster_sum == overall_secondary_value_cluster_count
            and site_changed_sum == overall_changed_count
        )
        report.add(
            "unified_digest_site_sum_matches_overall",
            "fail",
            "pass" if sums_ok else "fail",
            observed_value=(
                f"digest {site_digest_count_sum}/{overall_digest_count}, "
                f"queue {site_queue_run_sum}/{overall_queue_run_count}, "
                f"watch {site_watch_now_sum}/{overall_watch_now_panel_count}, "
                f"cluster {site_secondary_cluster_sum}/{overall_secondary_value_cluster_count}, "
                f"changed {site_changed_sum}/{overall_changed_count}"
            ),
            expected_value="per-site digest/queue/watch/cluster/changed sums == overall",
            detail_ko="unified digest summary per-site digest/queue/watch/cluster/changed 합이 overall과 각각 일치하는지 확인",
        )

    if baseline_manifest_row is None or workflow_default_overall is None:
        report.skip(
            "workflow_default_count_match_manifest",
            "fail",
            "baseline manifest 또는 workflow default summary 없음으로 workflow default count 검증을 건너뜀",
        )
        report.skip(
            "workflow_default_queue_count_match_manifest",
            "fail",
            "baseline manifest 또는 workflow default summary 없음으로 workflow default queue count 검증을 건너뜀",
        )
        report.skip(
            "workflow_default_watch_now_count_match_manifest",
            "fail",
            "baseline manifest 또는 workflow default summary 없음으로 workflow default watch_now count 검증을 건너뜀",
        )
        report.skip(
            "workflow_default_secondary_cluster_count_match_manifest",
            "fail",
            "baseline manifest 또는 workflow default summary 없음으로 workflow default secondary cluster count 검증을 건너뜀",
        )
        report.skip(
            "workflow_default_changed_count_match_manifest",
            "fail",
            "baseline manifest 또는 workflow default summary 없음으로 workflow default changed count 검증을 건너뜀",
        )
        report.skip(
            "workflow_default_primary_attention_count_match_manifest",
            "fail",
            "baseline manifest 또는 workflow default summary 없음으로 workflow default primary attention count 검증을 건너뜀",
        )
        report.skip(
            "workflow_default_supplemental_discovery_count_match_manifest",
            "fail",
            "baseline manifest 또는 workflow default summary 없음으로 workflow default supplemental discovery count 검증을 건너뜀",
        )
        report.skip(
            "workflow_default_linked_ref_count_match_manifest",
            "fail",
            "baseline manifest 또는 workflow default summary 없음으로 workflow default linked ref count 검증을 건너뜀",
        )
        report.skip(
            "workflow_default_truth_ref_count_match_manifest",
            "fail",
            "baseline manifest 또는 workflow default summary 없음으로 workflow default truth ref count 검증을 건너뜀",
        )
    else:
        workflow_manifest_count = int(numeric_value(baseline_manifest_row.get("workflow_default_item_count")))
        workflow_summary_count = int(numeric_value(workflow_default_overall.get("workflow_item_count")))
        report.add(
            "workflow_default_count_match_manifest",
            "fail",
            "pass" if workflow_manifest_count == workflow_summary_count else "fail",
            observed_value=f"{workflow_manifest_count} vs {workflow_summary_count}",
            expected_value="baseline manifest workflow_default_item_count == workflow default summary overall workflow_item_count",
            detail_ko="baseline manifest와 workflow default summary의 overall workflow item count가 일치하는지 확인",
        )
        workflow_manifest_queue = int(numeric_value(baseline_manifest_row.get("workflow_default_queue_run_count")))
        workflow_summary_queue = int(numeric_value(workflow_default_overall.get("queue_run_count")))
        report.add(
            "workflow_default_queue_count_match_manifest",
            "fail",
            "pass" if workflow_manifest_queue == workflow_summary_queue else "fail",
            observed_value=f"{workflow_manifest_queue} vs {workflow_summary_queue}",
            expected_value="baseline manifest workflow_default_queue_run_count == workflow default summary overall queue_run_count",
            detail_ko="baseline manifest와 workflow default summary의 overall queue_run count가 일치하는지 확인",
        )
        workflow_manifest_watch = int(
            numeric_value(baseline_manifest_row.get("workflow_default_watch_now_panel_count"))
        )
        workflow_summary_watch = int(numeric_value(workflow_default_overall.get("watch_now_panel_count")))
        report.add(
            "workflow_default_watch_now_count_match_manifest",
            "fail",
            "pass" if workflow_manifest_watch == workflow_summary_watch else "fail",
            observed_value=f"{workflow_manifest_watch} vs {workflow_summary_watch}",
            expected_value=(
                "baseline manifest workflow_default_watch_now_panel_count == workflow default summary overall watch_now_panel_count"
            ),
            detail_ko="baseline manifest와 workflow default summary의 overall watch_now_panel count가 일치하는지 확인",
        )
        workflow_manifest_cluster = int(
            numeric_value(baseline_manifest_row.get("workflow_default_secondary_value_cluster_count"))
        )
        workflow_summary_cluster = int(numeric_value(workflow_default_overall.get("secondary_value_cluster_count")))
        report.add(
            "workflow_default_secondary_cluster_count_match_manifest",
            "fail",
            "pass" if workflow_manifest_cluster == workflow_summary_cluster else "fail",
            observed_value=f"{workflow_manifest_cluster} vs {workflow_summary_cluster}",
            expected_value=(
                "baseline manifest workflow_default_secondary_value_cluster_count == "
                "workflow default summary overall secondary_value_cluster_count"
            ),
            detail_ko="baseline manifest와 workflow default summary의 overall secondary_value_cluster count가 일치하는지 확인",
        )
        workflow_manifest_changed = int(numeric_value(baseline_manifest_row.get("workflow_default_changed_count")))
        workflow_summary_changed = int(numeric_value(workflow_default_overall.get("changed_count")))
        report.add(
            "workflow_default_changed_count_match_manifest",
            "fail",
            "pass" if workflow_manifest_changed == workflow_summary_changed else "fail",
            observed_value=f"{workflow_manifest_changed} vs {workflow_summary_changed}",
            expected_value="baseline manifest workflow_default_changed_count == workflow default summary overall changed_count",
            detail_ko="baseline manifest와 workflow default summary의 overall changed count가 일치하는지 확인",
        )
        workflow_manifest_primary = int(
            numeric_value(baseline_manifest_row.get("workflow_default_primary_attention_count"))
        )
        workflow_summary_primary = int(numeric_value(workflow_default_overall.get("primary_attention_count")))
        report.add(
            "workflow_default_primary_attention_count_match_manifest",
            "fail",
            "pass" if workflow_manifest_primary == workflow_summary_primary else "fail",
            observed_value=f"{workflow_manifest_primary} vs {workflow_summary_primary}",
            expected_value=(
                "baseline manifest workflow_default_primary_attention_count == "
                "workflow default summary overall primary_attention_count"
            ),
            detail_ko="baseline manifest와 workflow default summary의 overall primary attention count가 일치하는지 확인",
        )
        workflow_manifest_supplemental = int(
            numeric_value(baseline_manifest_row.get("workflow_default_supplemental_discovery_count"))
        )
        workflow_summary_supplemental = int(
            numeric_value(workflow_default_overall.get("supplemental_discovery_count"))
        )
        report.add(
            "workflow_default_supplemental_discovery_count_match_manifest",
            "fail",
            "pass" if workflow_manifest_supplemental == workflow_summary_supplemental else "fail",
            observed_value=f"{workflow_manifest_supplemental} vs {workflow_summary_supplemental}",
            expected_value=(
                "baseline manifest workflow_default_supplemental_discovery_count == "
                "workflow default summary overall supplemental_discovery_count"
            ),
            detail_ko="baseline manifest와 workflow default summary의 overall supplemental discovery count가 일치하는지 확인",
        )
        workflow_manifest_linked = int(numeric_value(baseline_manifest_row.get("workflow_default_linked_ref_count")))
        workflow_summary_linked = int(numeric_value(workflow_default_overall.get("linked_ref_count")))
        report.add(
            "workflow_default_linked_ref_count_match_manifest",
            "fail",
            "pass" if workflow_manifest_linked == workflow_summary_linked else "fail",
            observed_value=f"{workflow_manifest_linked} vs {workflow_summary_linked}",
            expected_value="baseline manifest workflow_default_linked_ref_count == workflow default summary overall linked_ref_count",
            detail_ko="baseline manifest와 workflow default summary의 overall linked ref count가 일치하는지 확인",
        )
        workflow_manifest_truth = int(numeric_value(baseline_manifest_row.get("workflow_default_truth_ref_count")))
        workflow_summary_truth = int(numeric_value(workflow_default_overall.get("truth_ref_count")))
        report.add(
            "workflow_default_truth_ref_count_match_manifest",
            "fail",
            "pass" if workflow_manifest_truth == workflow_summary_truth else "fail",
            observed_value=f"{workflow_manifest_truth} vs {workflow_summary_truth}",
            expected_value="baseline manifest workflow_default_truth_ref_count == workflow default summary overall truth_ref_count",
            detail_ko="baseline manifest와 workflow default summary의 overall truth ref count가 일치하는지 확인",
        )

    if workflow_default_overall is None or unified_digest_overall is None:
        report.skip(
            "workflow_default_count_matches_unified_digest",
            "fail",
            "workflow default summary 또는 unified digest summary 없음으로 workflow/unified digest total count 검증을 건너뜀",
        )
    else:
        overall_workflow_default_count = int(numeric_value(workflow_default_overall.get("workflow_item_count")))
        overall_unified_digest_count = int(numeric_value(unified_digest_overall.get("digest_count")))
        report.add(
            "workflow_default_count_matches_unified_digest",
            "fail",
            "pass" if overall_workflow_default_count == overall_unified_digest_count else "fail",
            observed_value=overall_workflow_default_count,
            expected_value=overall_unified_digest_count,
            detail_ko="workflow default overall count가 unified digest overall count와 일치하는지 확인",
        )

    if workflow_default_overall is None or workflow_default_sites is None:
        report.skip(
            "workflow_default_site_sum_matches_overall",
            "fail",
            "workflow default summary 없음으로 per-site workflow default 합 검증을 건너뜀",
        )
    else:
        overall_workflow_item_count = int(numeric_value(workflow_default_overall.get("workflow_item_count")))
        overall_queue_run_count = int(numeric_value(workflow_default_overall.get("queue_run_count")))
        overall_watch_now_panel_count = int(numeric_value(workflow_default_overall.get("watch_now_panel_count")))
        overall_secondary_value_cluster_count = int(
            numeric_value(workflow_default_overall.get("secondary_value_cluster_count"))
        )
        overall_changed_count = int(numeric_value(workflow_default_overall.get("changed_count")))
        site_workflow_item_sum = int(
            pd.to_numeric(workflow_default_sites["workflow_item_count"], errors="coerce").fillna(0).sum()
        )
        site_queue_run_sum = int(
            pd.to_numeric(workflow_default_sites["queue_run_count"], errors="coerce").fillna(0).sum()
        )
        site_watch_now_sum = int(
            pd.to_numeric(workflow_default_sites["watch_now_panel_count"], errors="coerce").fillna(0).sum()
        )
        site_secondary_cluster_sum = int(
            pd.to_numeric(workflow_default_sites["secondary_value_cluster_count"], errors="coerce").fillna(0).sum()
        )
        site_changed_sum = int(
            pd.to_numeric(workflow_default_sites["changed_count"], errors="coerce").fillna(0).sum()
        )
        sums_ok = (
            site_workflow_item_sum == overall_workflow_item_count
            and site_queue_run_sum == overall_queue_run_count
            and site_watch_now_sum == overall_watch_now_panel_count
            and site_secondary_cluster_sum == overall_secondary_value_cluster_count
            and site_changed_sum == overall_changed_count
        )
        report.add(
            "workflow_default_site_sum_matches_overall",
            "fail",
            "pass" if sums_ok else "fail",
            observed_value=(
                f"workflow {site_workflow_item_sum}/{overall_workflow_item_count}, "
                f"queue {site_queue_run_sum}/{overall_queue_run_count}, "
                f"watch {site_watch_now_sum}/{overall_watch_now_panel_count}, "
                f"cluster {site_secondary_cluster_sum}/{overall_secondary_value_cluster_count}, "
                f"changed {site_changed_sum}/{overall_changed_count}"
            ),
            expected_value="per-site workflow/queue/watch/cluster/changed sums == overall",
            detail_ko="workflow default summary per-site workflow/queue/watch/cluster/changed 합이 overall과 각각 일치하는지 확인",
        )


def run_soft_checks(
    report: QaReportBuilder,
    *,
    baseline_summary: pd.DataFrame | None,
    run_summary: pd.DataFrame | None,
    cluster_preview_summary: pd.DataFrame | None,
    unified_digest_summary: pd.DataFrame | None,
    workflow_default_summary: pd.DataFrame | None,
) -> None:
    baseline_overall = extract_overall_row(baseline_summary)
    run_overall = extract_overall_row(run_summary)
    cluster_preview_overall = extract_overall_row(cluster_preview_summary)
    unified_digest_overall = extract_overall_row(unified_digest_summary)
    workflow_default_overall = extract_overall_row(workflow_default_summary)

    if run_overall is None:
        report.skip("queue_count_too_large", "warn", "run summary 없음으로 queue 규모 경고 검사를 건너뜀")
        report.skip("watch_now_count_too_large", "warn", "run summary 없음으로 watch_now 규모 경고 검사를 건너뜀")
        report.skip("backlog_queue_ratio_extreme", "warn", "run summary 없음으로 backlog/queue ratio 경고 검사를 건너뜀")
    else:
        queue_count = int(numeric_value(run_overall.get("queue_count")))
        report.add(
            "queue_count_too_large",
            "warn",
            "warn" if queue_count > QUEUE_COUNT_WARN_THRESHOLD else "pass",
            observed_value=queue_count,
            expected_value=f"<= {QUEUE_COUNT_WARN_THRESHOLD}",
            detail_ko="queue 규모가 운영자가 한 번에 보기 어려울 정도로 큰지 확인",
        )
        watch_now_count = int(numeric_value(run_overall.get("watch_now_count")))
        report.add(
            "watch_now_count_too_large",
            "warn",
            "warn" if watch_now_count > WATCH_NOW_COUNT_WARN_THRESHOLD else "pass",
            observed_value=watch_now_count,
            expected_value=f"<= {WATCH_NOW_COUNT_WARN_THRESHOLD}",
            detail_ko="watch_now 규모가 과도한지 확인",
        )
        backlog_count = int(numeric_value(run_overall.get("backlog_count")))
        ratio = backlog_count / max(queue_count, 1)
        report.add(
            "backlog_queue_ratio_extreme",
            "warn",
            "warn" if ratio > BACKLOG_QUEUE_RATIO_WARN_THRESHOLD else "pass",
            observed_value=f"{ratio:.3f}",
            expected_value=f"<= {BACKLOG_QUEUE_RATIO_WARN_THRESHOLD}",
            detail_ko="backlog 대비 active queue 비율이 비정상적으로 큰지 확인",
        )

    if baseline_overall is None:
        report.skip("attention_count_too_large", "warn", "baseline summary 없음으로 attention 규모 경고 검사를 건너뜀")
    else:
        attention_count = int(numeric_value(baseline_overall.get("attention_count")))
        report.add(
            "attention_count_too_large",
            "warn",
            "warn" if attention_count > ATTENTION_COUNT_WARN_THRESHOLD else "pass",
            observed_value=attention_count,
            expected_value=f"<= {ATTENTION_COUNT_WARN_THRESHOLD}",
            detail_ko="attention 전체 건수가 운영 관점에서 과도한지 확인",
        )

    if cluster_preview_overall is None:
        report.skip("cluster_preview_too_large", "warn", "cluster preview summary 없음으로 cluster preview 규모 경고 검사를 건너뜀")
        report.skip(
            "discovery_cluster_count_too_large",
            "warn",
            "cluster preview summary 없음으로 discovery cluster 규모 경고 검사를 건너뜀",
        )
    else:
        cluster_preview_count = int(numeric_value(cluster_preview_overall.get("cluster_preview_count")))
        report.add(
            "cluster_preview_too_large",
            "warn",
            "warn" if cluster_preview_count > CLUSTER_PREVIEW_COUNT_WARN_THRESHOLD else "pass",
            observed_value=cluster_preview_count,
            expected_value=f"<= {CLUSTER_PREVIEW_COUNT_WARN_THRESHOLD}",
            detail_ko="cluster preview 전체 건수가 운영 preview로 보기 과도한지 확인",
        )
        discovery_cluster_count = int(numeric_value(cluster_preview_overall.get("secondary_value_cluster_count")))
        report.add(
            "discovery_cluster_count_too_large",
            "warn",
            "warn" if discovery_cluster_count > DISCOVERY_CLUSTER_COUNT_WARN_THRESHOLD else "pass",
            observed_value=discovery_cluster_count,
            expected_value=f"<= {DISCOVERY_CLUSTER_COUNT_WARN_THRESHOLD}",
            detail_ko="secondary discovery cluster 수가 supplemental preview로 보기 과도한지 확인",
        )

    if unified_digest_overall is None:
        report.skip("unified_digest_too_large", "warn", "unified digest summary 없음으로 unified digest 규모 경고 검사를 건너뜀")
    else:
        unified_digest_count = int(numeric_value(unified_digest_overall.get("digest_count")))
        report.add(
            "unified_digest_too_large",
            "warn",
            "warn" if unified_digest_count > UNIFIED_DIGEST_COUNT_WARN_THRESHOLD else "pass",
            observed_value=unified_digest_count,
            expected_value=f"<= {UNIFIED_DIGEST_COUNT_WARN_THRESHOLD}",
            detail_ko="unified digest 전체 건수가 operator digest로 보기 과도한지 확인",
        )

    if workflow_default_overall is None:
        report.skip("workflow_default_too_large", "warn", "workflow default summary 없음으로 workflow default 규모 경고 검사를 건너뜀")
    else:
        workflow_default_count = int(numeric_value(workflow_default_overall.get("workflow_item_count")))
        report.add(
            "workflow_default_too_large",
            "warn",
            "warn" if workflow_default_count > WORKFLOW_DEFAULT_COUNT_WARN_THRESHOLD else "pass",
            observed_value=workflow_default_count,
            expected_value=f"<= {WORKFLOW_DEFAULT_COUNT_WARN_THRESHOLD}",
            detail_ko="workflow default 전체 건수가 기본 operator workflow로 보기 과도한지 확인",
        )


def build_summary(
    report: pd.DataFrame,
    *,
    baseline_summary: pd.DataFrame | None,
    run_summary: pd.DataFrame | None,
    cluster_preview_summary: pd.DataFrame | None,
    cluster_delta_summary: pd.DataFrame | None,
    unified_digest_summary: pd.DataFrame | None,
    workflow_default_summary: pd.DataFrame | None,
) -> pd.DataFrame:
    baseline_overall = extract_overall_row(baseline_summary)
    run_overall = extract_overall_row(run_summary)
    cluster_preview_overall = extract_overall_row(cluster_preview_summary)
    cluster_delta_overall = extract_overall_row(cluster_delta_summary)
    unified_digest_overall = extract_overall_row(unified_digest_summary)
    workflow_default_overall = extract_overall_row(workflow_default_summary)

    def get_from_row(row: pd.Series | None, key: str) -> int:
        if row is None:
            return 0
        return int(numeric_value(row.get(key)))

    summary_row = {
        "generated_at_utc": utc_now_iso(),
        "qa_pass_flag": int(int(report["status"].eq("fail").sum()) == 0),
        "fail_count": int(report["status"].eq("fail").sum()),
        "warn_count": int(report["status"].eq("warn").sum()),
        "pass_count": int(report["status"].eq("pass").sum()),
        "skip_count": int(report["status"].eq("skip").sum()),
        "overall_attention_count": get_from_row(baseline_overall, "attention_count"),
        "overall_queue_count": get_from_row(run_overall, "queue_count"),
        "overall_watch_now_count": get_from_row(run_overall, "watch_now_count"),
        "overall_watch_review_count": get_from_row(run_overall, "watch_review_count"),
        "overall_backlog_count": get_from_row(run_overall, "backlog_count"),
        "overall_changed_count": get_from_row(baseline_overall, "total_changed_count"),
        "overall_cluster_preview_count": get_from_row(cluster_preview_overall, "cluster_preview_count"),
        "overall_discovery_cluster_count": get_from_row(cluster_preview_overall, "secondary_value_cluster_count"),
        "overall_cluster_preview_future_fault_linked_ref_count": get_from_row(
            cluster_preview_overall, "clusters_with_future_fault_linked_ref_count"
        ),
        "overall_cluster_preview_future_truth_linked_ref_count": get_from_row(
            cluster_preview_overall, "clusters_with_future_truth_linked_ref_count"
        ),
        "overall_cluster_delta_current_count": get_from_row(cluster_delta_overall, "current_cluster_count"),
        "overall_cluster_delta_changed_count": get_from_row(cluster_delta_overall, "changed_cluster_count"),
        "overall_cluster_delta_new_count": get_from_row(cluster_delta_overall, "new_cluster_count"),
        "overall_cluster_delta_dropped_count": get_from_row(cluster_delta_overall, "dropped_cluster_count"),
        "overall_cluster_delta_representative_changed_count": get_from_row(
            cluster_delta_overall, "representative_changed_count"
        ),
        "overall_cluster_delta_linked_ref_changed_count": get_from_row(
            cluster_delta_overall, "linked_ref_changed_count"
        ),
        "overall_unified_digest_count": get_from_row(unified_digest_overall, "digest_count"),
        "overall_unified_digest_queue_run_count": get_from_row(unified_digest_overall, "queue_run_count"),
        "overall_unified_digest_watch_now_panel_count": get_from_row(unified_digest_overall, "watch_now_panel_count"),
        "overall_unified_digest_secondary_value_cluster_count": get_from_row(
            unified_digest_overall, "secondary_value_cluster_count"
        ),
        "overall_unified_digest_changed_count": get_from_row(unified_digest_overall, "changed_count"),
        "overall_unified_digest_changed_attention_count": get_from_row(
            unified_digest_overall, "changed_attention_count"
        ),
        "overall_unified_digest_changed_cluster_count": get_from_row(
            unified_digest_overall, "changed_cluster_count"
        ),
        "overall_workflow_default_count": get_from_row(workflow_default_overall, "workflow_item_count"),
        "overall_workflow_default_queue_run_count": get_from_row(workflow_default_overall, "queue_run_count"),
        "overall_workflow_default_watch_now_panel_count": get_from_row(
            workflow_default_overall, "watch_now_panel_count"
        ),
        "overall_workflow_default_secondary_value_cluster_count": get_from_row(
            workflow_default_overall, "secondary_value_cluster_count"
        ),
        "overall_workflow_default_changed_count": get_from_row(workflow_default_overall, "changed_count"),
        "overall_workflow_default_primary_attention_count": get_from_row(
            workflow_default_overall, "primary_attention_count"
        ),
        "overall_workflow_default_supplemental_discovery_count": get_from_row(
            workflow_default_overall, "supplemental_discovery_count"
        ),
        "overall_workflow_default_linked_ref_count": get_from_row(workflow_default_overall, "linked_ref_count"),
        "overall_workflow_default_truth_ref_count": get_from_row(workflow_default_overall, "truth_ref_count"),
    }
    return pd.DataFrame([summary_row], columns=QA_SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    report_builder = QaReportBuilder()
    data_frames: dict[str, pd.DataFrame | None] = {}

    for check_name, file_name in REQUIRED_SUMMARY_FILES.items():
        df = read_csv_if_exists(share_dir / file_name)
        data_frames[file_name] = df
        report_builder.fail_exists(check_name, file_name, df is not None)

    optional_watchlist = read_csv_if_exists(share_dir / WATCHLIST_SUMMARY_NAME)
    optional_run_watchlist = read_csv_if_exists(share_dir / RUN_WATCHLIST_SUMMARY_NAME)
    _ = optional_watchlist, optional_run_watchlist

    run_summary = read_csv_if_exists(share_dir / RUN_SUMMARY_NAME)

    run_hard_checks(
        report_builder,
        refresh_manifest=data_frames[REFRESH_MANIFEST_NAME],
        site_results=data_frames[REFRESH_SITE_RESULTS_NAME],
        baseline_manifest=data_frames[BASELINE_MANIFEST_NAME],
        baseline_summary=data_frames[BASELINE_SUMMARY_NAME],
        attention_summary=data_frames[ATTENTION_SUMMARY_NAME],
        digest_summary=data_frames[DIGEST_SUMMARY_NAME],
        run_summary=run_summary,
        cluster_preview_summary=data_frames[CLUSTER_PREVIEW_SUMMARY_NAME],
        cluster_delta_summary=data_frames[CLUSTER_DELTA_SUMMARY_NAME],
        unified_digest_summary=data_frames[UNIFIED_DIGEST_SUMMARY_NAME],
        workflow_default_summary=data_frames[WORKFLOW_DEFAULT_SUMMARY_NAME],
    )
    run_soft_checks(
        report_builder,
        baseline_summary=data_frames[BASELINE_SUMMARY_NAME],
        run_summary=run_summary,
        cluster_preview_summary=data_frames[CLUSTER_PREVIEW_SUMMARY_NAME],
        unified_digest_summary=data_frames[UNIFIED_DIGEST_SUMMARY_NAME],
        workflow_default_summary=data_frames[WORKFLOW_DEFAULT_SUMMARY_NAME],
    )

    report = report_builder.to_frame()
    summary = build_summary(
        report,
        baseline_summary=data_frames[BASELINE_SUMMARY_NAME],
        run_summary=run_summary,
        cluster_preview_summary=data_frames[CLUSTER_PREVIEW_SUMMARY_NAME],
        cluster_delta_summary=data_frames[CLUSTER_DELTA_SUMMARY_NAME],
        unified_digest_summary=data_frames[UNIFIED_DIGEST_SUMMARY_NAME],
        workflow_default_summary=data_frames[WORKFLOW_DEFAULT_SUMMARY_NAME],
    )

    report.to_csv(share_dir / QA_REPORT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / QA_SUMMARY_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
