#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

FORENSIC_HOLDOUT_PANEL_ID = "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"
SPECIAL_10305_SITE = "ktc_ess"
SPECIAL_10305_PANEL_ID = "10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_fixture(root: Path) -> None:
    share = root / "_share"
    gpvs_out = root / "data" / "gpvs" / "out"
    share.mkdir(parents=True, exist_ok=True)
    gpvs_out.mkdir(parents=True, exist_ok=True)

    write_csv(
        share / "panel_day_engine_operator_workflow_default_v1.csv",
        [
            {
                "preview_attention_class": "queue_run",
                "site": SPECIAL_10305_SITE,
                "display_entity_id": SPECIAL_10305_PANEL_ID,
                "display_start_date": "2026-02-01",
                "display_end_date": "2026-02-02",
                "display_span_or_day_count": 2,
                "display_shape_or_cluster_kind": "short_alert_run",
                "display_status_or_tier": "ongoing_run",
                "display_score": 9.0,
                "linked_ref_flag": 1,
                "truth_ref_flag": 0,
                "cluster_panel_count": 1,
                "changed_since_previous_flag": 0,
                "latest_delta_source": "none",
                "latest_delta_class": "",
                "latest_delta_reason_ko": "",
                "digest_reason_ko": "queue item",
                "workflow_policy_name": "baseline_plus_discovery_cluster",
                "workflow_role": "primary_attention",
                "workflow_priority_class": "queue_priority",
                "workflow_reason_ko": "기본 queue attention",
            },
            {
                "preview_attention_class": "watch_now_panel",
                "site": "siteB",
                "display_entity_id": "panel_repeat",
                "display_start_date": "2026-01-10",
                "display_end_date": "2026-02-10",
                "display_span_or_day_count": 32,
                "display_shape_or_cluster_kind": "chronic_alert_run",
                "display_status_or_tier": "watch_now",
                "display_score": 5.5,
                "linked_ref_flag": 0,
                "truth_ref_flag": 0,
                "cluster_panel_count": 1,
                "changed_since_previous_flag": 0,
                "latest_delta_source": "none",
                "latest_delta_class": "",
                "latest_delta_reason_ko": "",
                "digest_reason_ko": "watch item",
                "workflow_policy_name": "baseline_plus_discovery_cluster",
                "workflow_role": "primary_attention",
                "workflow_priority_class": "watch_priority",
                "workflow_reason_ko": "기본 watch attention",
            },
            {
                "preview_attention_class": "queue_run",
                "site": "siteQ",
                "display_entity_id": "panel_queue_only",
                "display_start_date": "2026-02-03",
                "display_end_date": "2026-02-05",
                "display_span_or_day_count": 3,
                "display_shape_or_cluster_kind": "medium_alert_run",
                "display_status_or_tier": "ongoing_run",
                "display_score": 6.5,
                "linked_ref_flag": 0,
                "truth_ref_flag": 0,
                "cluster_panel_count": 1,
                "changed_since_previous_flag": 0,
                "latest_delta_source": "none",
                "latest_delta_class": "",
                "latest_delta_reason_ko": "",
                "digest_reason_ko": "queue item",
                "workflow_policy_name": "baseline_plus_discovery_cluster",
                "workflow_role": "primary_attention",
                "workflow_priority_class": "queue_priority",
                "workflow_reason_ko": "기본 queue attention",
            },
            {
                "preview_attention_class": "secondary_value_cluster",
                "site": "siteC",
                "display_entity_id": "cluster_001",
                "display_start_date": "2026-02-02",
                "display_end_date": "2026-02-03",
                "display_span_or_day_count": 2,
                "display_shape_or_cluster_kind": "discovery_cluster",
                "display_status_or_tier": "secondary_discovery_cluster",
                "display_score": 6.2,
                "linked_ref_flag": 1,
                "truth_ref_flag": 0,
                "cluster_panel_count": 3,
                "changed_since_previous_flag": 0,
                "latest_delta_source": "none",
                "latest_delta_class": "",
                "latest_delta_reason_ko": "",
                "digest_reason_ko": "cluster item",
                "workflow_policy_name": "baseline_plus_discovery_cluster",
                "workflow_role": "supplemental_discovery",
                "workflow_priority_class": "discovery_priority",
                "workflow_reason_ko": "기본 workflow에 포함된 discovery cluster",
            },
        ],
        [
            "preview_attention_class",
            "site",
            "display_entity_id",
            "display_start_date",
            "display_end_date",
            "display_span_or_day_count",
            "display_shape_or_cluster_kind",
            "display_status_or_tier",
            "display_score",
            "linked_ref_flag",
            "truth_ref_flag",
            "cluster_panel_count",
            "changed_since_previous_flag",
            "latest_delta_source",
            "latest_delta_class",
            "latest_delta_reason_ko",
            "digest_reason_ko",
            "workflow_policy_name",
            "workflow_role",
            "workflow_priority_class",
            "workflow_reason_ko",
        ],
    )

    abrupt_rows = [
        {"site": SPECIAL_10305_SITE, "panel_id": SPECIAL_10305_PANEL_ID, "고장시점": "2025-01-01", "사건유형_ko": "급작 고장", "최종고장양상_ko": "급작 발생", "순수급작_flag": 1, "증상명_ko": "다이오드형", "세부근거_ko": "fixture", "source_field_ko": "vendor_fault_family", "비고_ko": "fixture"},
        {"site": "siteA", "panel_id": "abrupt_2", "고장시점": "2025-01-02", "사건유형_ko": "급작 고장", "최종고장양상_ko": "급작 발생", "순수급작_flag": 1, "증상명_ko": "다이오드형", "세부근거_ko": "fixture", "source_field_ko": "vendor_fault_family", "비고_ko": "fixture"},
        {"site": "siteA", "panel_id": "abrupt_3", "고장시점": "2025-01-03", "사건유형_ko": "급작 고장", "최종고장양상_ko": "급작 발생", "순수급작_flag": 1, "증상명_ko": "다이오드형", "세부근거_ko": "fixture", "source_field_ko": "vendor_fault_family", "비고_ko": "fixture"},
        {"site": "conalog", "panel_id": FORENSIC_HOLDOUT_PANEL_ID, "고장시점": "2025-03-21", "사건유형_ko": "전조형 고장", "최종고장양상_ko": "급격 종료", "순수급작_flag": 0, "증상명_ko": "개방/장치이상형", "세부근거_ko": "fixture", "source_field_ko": "vendor_fault_family", "비고_ko": "fixture"},
        {"site": "siteA", "panel_id": "abrupt_5", "고장시점": "2025-01-05", "사건유형_ko": "전조형 고장", "최종고장양상_ko": "진행성 악화", "순수급작_flag": 0, "증상명_ko": "개방/장치이상형", "세부근거_ko": "fixture", "source_field_ko": "vendor_fault_family", "비고_ko": "fixture"},
        {"site": "siteA", "panel_id": "abrupt_6", "고장시점": "2025-01-06", "사건유형_ko": "전조형 고장", "최종고장양상_ko": "진행성 악화", "순수급작_flag": 0, "증상명_ko": "모듈손상형", "세부근거_ko": "fixture", "source_field_ko": "vendor_fault_family", "비고_ko": "fixture"},
    ]
    write_csv(
        share / "panel_day_engine_abrupt6_symptom_map_v1.csv",
        abrupt_rows,
        ["site", "panel_id", "고장시점", "사건유형_ko", "최종고장양상_ko", "순수급작_flag", "증상명_ko", "세부근거_ko", "source_field_ko", "비고_ko"],
    )

    # overlap two precursor events with abrupt panels so the fixture mirrors the current real-data event semantics.
    write_csv(
        share / "panel_day_engine_precursor_onset_truth_v1.csv",
        [
            {
                "site": "siteA",
                "panel_id": "abrupt_5",
                "preferred_precursor_onset_date": "2025-01-02",
                "operational_first_precursor_detected_date": "2025-01-02",
                "operational_first_precursor_marker_name": "first_cond_evt",
                "interpretive_precursor_onset_date": "2025-01-02",
                "benchmark_precursor_onset_date": "2025-01-02",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_6",
                "preferred_precursor_onset_date": "2025-01-01",
                "operational_first_precursor_detected_date": "2025-01-01",
                "operational_first_precursor_marker_name": "first_cond_evt",
                "interpretive_precursor_onset_date": "2025-01-01",
                "benchmark_precursor_onset_date": "2025-01-01",
            },
            {
                "site": "conalog",
                "panel_id": FORENSIC_HOLDOUT_PANEL_ID,
                "preferred_precursor_onset_date": "2025-03-18",
                "operational_first_precursor_detected_date": "2025-02-20",
                "operational_first_precursor_marker_name": "first_cond_evt",
                "interpretive_precursor_onset_date": "2025-01-20",
                "benchmark_precursor_onset_date": "2025-03-18",
            },
        ],
        [
            "site",
            "panel_id",
            "preferred_precursor_onset_date",
            "operational_first_precursor_detected_date",
            "operational_first_precursor_marker_name",
            "interpretive_precursor_onset_date",
            "benchmark_precursor_onset_date",
        ],
    )

    write_csv(
        share / "panel_day_engine_non_precursor_performance_cases_v1.csv",
        [
            {"eval_bucket_v2": "abrupt_or_no_precursor_now", "site": SPECIAL_10305_SITE, "panel_id": SPECIAL_10305_PANEL_ID},
            {"eval_bucket_v2": "abrupt_or_no_precursor_now", "site": "siteA", "panel_id": "abrupt_2"},
            {"eval_bucket_v2": "abrupt_or_no_precursor_now", "site": "siteA", "panel_id": "abrupt_3"},
        ],
        ["eval_bucket_v2", "site", "panel_id"],
    )

    write_csv(
        share / "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv",
        [
            {"eval_bucket_v2": "non_panel_or_common_cause", "site": "siteCC", "panel_id": "common_1", "current_marker_only_flag": 0, "breadth_marker_only_flag": 1, "combined_marker_flag": 1},
            {"eval_bucket_v2": "non_panel_or_common_cause", "site": "siteCC", "panel_id": "common_2", "current_marker_only_flag": 0, "breadth_marker_only_flag": 1, "combined_marker_flag": 1},
            {"eval_bucket_v2": "non_panel_or_common_cause", "site": "siteCC", "panel_id": "common_3", "current_marker_only_flag": 0, "breadth_marker_only_flag": 1, "combined_marker_flag": 1},
            {"eval_bucket_v2": "non_panel_or_common_cause", "site": "siteCC", "panel_id": "common_4", "current_marker_only_flag": 0, "breadth_marker_only_flag": 1, "combined_marker_flag": 1},
        ],
        ["eval_bucket_v2", "site", "panel_id", "current_marker_only_flag", "breadth_marker_only_flag", "combined_marker_flag"],
    )

    write_csv(
        share / "panel_day_engine_precursor_abrupt_consistency_cases_v1.csv",
        [
            {"site": "siteA", "panel_id": "abrupt_5", "same_event_flag": 1, "distinct_event_flag": 0, "consistency_judgment_ko": "같은 사건"},
            {"site": "siteA", "panel_id": "abrupt_6", "same_event_flag": 1, "distinct_event_flag": 0, "consistency_judgment_ko": "같은 사건"},
        ],
        ["site", "panel_id", "same_event_flag", "distinct_event_flag", "consistency_judgment_ko"],
    )
    write_csv(
        share / "panel_day_engine_precursor_abrupt_consistency_summary_v1.csv",
        [
            {"overlap_panel_count": 2, "same_event_count": 2, "corrected_pure_abrupt_fault_count": 4}
        ],
        ["overlap_panel_count", "same_event_count", "corrected_pure_abrupt_fault_count"],
    )
    write_csv(
        share / "panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv",
        [
            {"recommended_next_handling": "relabel_overlap_as_precursor_led_faults", "rationale_ko": "fixture same-event overlap"}
        ],
        ["recommended_next_handling", "rationale_ko"],
    )

    write_csv(
        share / "panel_day_engine_c42997_1_1_forensic_summary_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": FORENSIC_HOLDOUT_PANEL_ID,
                "원래_커널로그라벨_ko": "compound / electrical",
                "원래라벨_근거파일_ko": "fixture",
                "현재_재감사라벨_ko": "개방/장치이상형 (open_or_device_issue_like)",
                "현재_재감사_근거파일_ko": "fixture",
                "현재_패널표_사건유형_ko": "전조형 고장",
                "현재_패널표_커널로그증상명_ko": "전압 변화형",
                "현재_패널표_커널로그원인군_ko": "개방/장치이상형",
                "현재_패널표_GPVS참고유형_ko": "개방/장치이상 계열",
                "earliest_warning_date": "2025-01-16",
                "earliest_onset_date": "2025-01-20",
                "strong_trigger_date": "2025-03-21",
                "전조흔적_시작일": "2025-01-16",
                "강한트리거일": "2025-03-21",
                "사건유형_결정규칙_ko": "retrospective_onset_date < strict_trigger_date and onset_confidence=high and onset_method=persistent_5of7",
                "최종고장양상_결정규칙_ko": "first_final_fault_date == strict_trigger_date and dead_diag_date <= strict_trigger_date + 1 day",
                "사건유형_결정_ko": "전조형 고장",
                "최종고장양상_결정_ko": "급격 종료",
                "선행기간_일": 60,
                "사건시간양상_판정_ko": "전조흔적있음_순수급작보류",
                "확정도_판정_ko": "보류",
                "현재표_보정필요여부_flag": 0,
                "핵심판정_한줄요약_ko": "fixture",
                "다음보정권고_ko": "fixture",
            }
        ],
        [
            "site",
            "panel_id",
            "원래_커널로그라벨_ko",
            "원래라벨_근거파일_ko",
            "현재_재감사라벨_ko",
            "현재_재감사_근거파일_ko",
            "현재_패널표_사건유형_ko",
            "현재_패널표_커널로그증상명_ko",
            "현재_패널표_커널로그원인군_ko",
            "현재_패널표_GPVS참고유형_ko",
            "earliest_warning_date",
            "earliest_onset_date",
            "strong_trigger_date",
            "전조흔적_시작일",
            "강한트리거일",
            "사건유형_결정규칙_ko",
            "최종고장양상_결정규칙_ko",
            "사건유형_결정_ko",
            "최종고장양상_결정_ko",
            "선행기간_일",
            "사건시간양상_판정_ko",
            "확정도_판정_ko",
            "현재표_보정필요여부_flag",
            "핵심판정_한줄요약_ko",
            "다음보정권고_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_fault_panel_event_audit_v1.csv",
        [
            {
                "site": SPECIAL_10305_SITE,
                "panel_id": SPECIAL_10305_PANEL_ID,
                "현재표_사건유형_ko": "급작 고장",
                "현재표_최종고장양상_ko": "급작 발생",
                "전조흔적_flag": 0,
                "순수급작_flag": 1,
                "전조평가셋편입_flag": 0,
                "급작평가셋편입_flag": 1,
                "사건유형_재판정_ko": "급작 고장",
                "최종고장양상_재판정_ko": "급작 발생",
                "재판정_근거_ko": "same-day fallback onset은 pure abrupt 허용",
                "현재표_보정필요여부_flag": 0,
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_2",
                "현재표_사건유형_ko": "급작 고장",
                "현재표_최종고장양상_ko": "급작 발생",
                "전조흔적_flag": 0,
                "순수급작_flag": 1,
                "전조평가셋편입_flag": 0,
                "급작평가셋편입_flag": 1,
                "사건유형_재판정_ko": "급작 고장",
                "최종고장양상_재판정_ko": "급작 발생",
                "재판정_근거_ko": "same-day fallback onset은 pure abrupt 허용",
                "현재표_보정필요여부_flag": 0,
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_3",
                "현재표_사건유형_ko": "급작 고장",
                "현재표_최종고장양상_ko": "급작 발생",
                "전조흔적_flag": 0,
                "순수급작_flag": 1,
                "전조평가셋편입_flag": 0,
                "급작평가셋편입_flag": 1,
                "사건유형_재판정_ko": "급작 고장",
                "최종고장양상_재판정_ko": "급작 발생",
                "재판정_근거_ko": "same-day fallback onset은 pure abrupt 허용",
                "현재표_보정필요여부_flag": 0,
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_5",
                "현재표_사건유형_ko": "전조형 고장",
                "현재표_최종고장양상_ko": "진행성 악화",
                "전조흔적_flag": 1,
                "순수급작_flag": 0,
                "전조평가셋편입_flag": 1,
                "급작평가셋편입_flag": 0,
                "사건유형_재판정_ko": "전조형 고장",
                "최종고장양상_재판정_ko": "진행성 악화",
                "재판정_근거_ko": "precursor explicit rule hit",
                "현재표_보정필요여부_flag": 1,
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_6",
                "현재표_사건유형_ko": "전조형 고장",
                "현재표_최종고장양상_ko": "진행성 악화",
                "전조흔적_flag": 1,
                "순수급작_flag": 0,
                "전조평가셋편입_flag": 1,
                "급작평가셋편입_flag": 0,
                "사건유형_재판정_ko": "전조형 고장",
                "최종고장양상_재판정_ko": "진행성 악화",
                "재판정_근거_ko": "precursor explicit rule hit",
                "현재표_보정필요여부_flag": 1,
            },
            {
                "site": "conalog",
                "panel_id": FORENSIC_HOLDOUT_PANEL_ID,
                "현재표_사건유형_ko": "전조형 고장",
                "현재표_최종고장양상_ko": "급격 종료",
                "전조흔적_flag": 1,
                "순수급작_flag": 0,
                "전조평가셋편입_flag": 0,
                "급작평가셋편입_flag": 0,
                "사건유형_재판정_ko": "전조형 고장",
                "최종고장양상_재판정_ko": "급격 종료",
                "재판정_근거_ko": "explicit stored-field rule",
                "현재표_보정필요여부_flag": 0,
            },
        ],
        [
            "site",
            "panel_id",
            "현재표_사건유형_ko",
            "현재표_최종고장양상_ko",
            "전조흔적_flag",
            "순수급작_flag",
            "전조평가셋편입_flag",
            "급작평가셋편입_flag",
            "사건유형_재판정_ko",
            "최종고장양상_재판정_ko",
            "재판정_근거_ko",
            "현재표_보정필요여부_flag",
        ],
    )

    write_csv(
        share / "panel_day_engine_detailed_fault_bridge_audit_v1.csv",
        [
            {
                "site": SPECIAL_10305_SITE,
                "panel_id": SPECIAL_10305_PANEL_ID,
                "reference_date": "2025-01-01",
                "exact_match_file_count": 2,
                "matched_files_csv": "data/pvfault/out/PVFAULT_labels_day.csv|_share/external_pvfault_20260304/PVFAULT_labels_day.csv",
                "matched_fault_type_values_csv": "F101",
                "consensus_fault_type_code": "F101",
                "attachable_flag": 1,
                "attach_reason_ko": "exact_date_consensus",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_2",
                "reference_date": "2025-01-02",
                "exact_match_file_count": 2,
                "matched_files_csv": "data/pvfault/out/PVFAULT_labels_day.csv|_share/external_pvfault_20260304/PVFAULT_labels_day.csv",
                "matched_fault_type_values_csv": "F201|F202",
                "consensus_fault_type_code": "",
                "attachable_flag": 0,
                "attach_reason_ko": "exact_date_conflict",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_3",
                "reference_date": "2025-01-03",
                "exact_match_file_count": 0,
                "matched_files_csv": "",
                "matched_fault_type_values_csv": "",
                "consensus_fault_type_code": "",
                "attachable_flag": 0,
                "attach_reason_ko": "no_exact_date_match",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_5",
                "reference_date": "2025-01-05",
                "exact_match_file_count": 1,
                "matched_files_csv": "_share/external_pvfault_20260304_215400/PVFAULT_labels_day.csv",
                "matched_fault_type_values_csv": "F501",
                "consensus_fault_type_code": "F501",
                "attachable_flag": 1,
                "attach_reason_ko": "exact_date_consensus",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_6",
                "reference_date": "2025-01-06",
                "exact_match_file_count": 1,
                "matched_files_csv": "_share/external_pvfault_fixlabel_20260304_174840/PVFAULT_labels_day.csv",
                "matched_fault_type_values_csv": "F601",
                "consensus_fault_type_code": "F601",
                "attachable_flag": 1,
                "attach_reason_ko": "exact_date_consensus",
            },
            {
                "site": "conalog",
                "panel_id": FORENSIC_HOLDOUT_PANEL_ID,
                "reference_date": "2025-03-21",
                "exact_match_file_count": 0,
                "matched_files_csv": "",
                "matched_fault_type_values_csv": "",
                "consensus_fault_type_code": "",
                "attachable_flag": 0,
                "attach_reason_ko": "no_exact_date_match",
            },
        ],
        [
            "site",
            "panel_id",
            "reference_date",
            "exact_match_file_count",
            "matched_files_csv",
            "matched_fault_type_values_csv",
            "consensus_fault_type_code",
            "attachable_flag",
            "attach_reason_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_detailed_fault_bridge_summary_v1.csv",
        [
            {
                "고장패널수": 6,
                "세부fault_부착수": 3,
                "세부fault_보류수": 3,
                "exact_date_match_패널수": 4,
                "exact_date_conflict_패널수": 1,
                "exact_date_miss_패널수": 2,
                "note_ko": "exact-date consensus only; detailed fault type stays separate from GPVS family",
            }
        ],
        [
            "고장패널수",
            "세부fault_부착수",
            "세부fault_보류수",
            "exact_date_match_패널수",
            "exact_date_conflict_패널수",
            "exact_date_miss_패널수",
            "note_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_kernellog_project_mapping_v1.csv",
        [
            {"커널로그_증상명": "출력 저하형", "주_프로젝트분류": "전조형 고장", "보조_프로젝트분류": "급작 고장", "설명_ko": "fixture", "주의_ko": "fixture"},
            {"커널로그_증상명": "전압 변화형", "주_프로젝트분류": "급작 고장", "보조_프로젝트분류": "전조형 고장", "설명_ko": "fixture", "주의_ko": "fixture"},
            {"커널로그_증상명": "패턴 이상형", "주_프로젝트분류": "공통원인 이벤트", "보조_프로젝트분류": "오경보", "설명_ko": "fixture", "주의_ko": "fixture"},
            {"커널로그_증상명": "불안정형", "주_프로젝트분류": "반복 이상", "보조_프로젝트분류": "오경보", "설명_ko": "fixture", "주의_ko": "fixture"},
            {"커널로그_증상명": "복합형", "주_프로젝트분류": "급작 고장", "보조_프로젝트분류": "공통원인 이벤트", "설명_ko": "fixture", "주의_ko": "fixture"},
        ],
        ["커널로그_증상명", "주_프로젝트분류", "보조_프로젝트분류", "설명_ko", "주의_ko"],
    )

    write_csv(
        share / "panel_day_engine_gpv7_perf_summary_v1.csv",
        [
            {
                "고장유형_번호": idx,
                "고장유형_설명_ko": f"GPVS Fault{idx}",
                "성능요약_ko": "stored by-type metric",
                "수치_ko": f"auc=0.{idx}000",
                "source_ref_ko": "data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv",
            }
            for idx in range(1, 8)
        ],
        ["고장유형_번호", "고장유형_설명_ko", "성능요약_ko", "수치_ko", "source_ref_ko"],
    )

    write_csv(
        share / "panel_day_engine_project_final_decision_pack_v1.csv",
        [
            {"eval_scope": "step1_taxonomy", "current_data_decision": "freeze_with_caution", "final_usage_decision": "bounded_reporting_use", "final_reason_ko": "fixture"},
            {"eval_scope": "step2_onset_truth", "current_data_decision": "freeze_with_caution", "final_usage_decision": "bounded_reporting_use", "final_reason_ko": "fixture"},
            {"eval_scope": "step3_precursor_performance", "current_data_decision": "exploratory_only", "final_usage_decision": "exploratory_only", "final_reason_ko": "fixture"},
            {"eval_scope": "step4_abrupt_no_precursor", "current_data_decision": "exploratory_only", "final_usage_decision": "exploratory_only", "final_reason_ko": "fixture"},
            {"eval_scope": "step4_common_cause_routing", "current_data_decision": "exploratory_only", "final_usage_decision": "exploratory_only", "final_reason_ko": "fixture"},
            {"eval_scope": "operator_policy_proxy", "current_data_decision": "workflow_proxy_only", "final_usage_decision": "workflow_only", "final_reason_ko": "fixture"},
        ],
        ["eval_scope", "current_data_decision", "final_usage_decision", "final_reason_ko"],
    )

    write_csv(
        share / "panel_day_engine_gpvs_panel_attach_inventory_v1.csv",
        [
            {
                "경로": "_share/gpvs_fault_family_eval_cases.csv",
                "존재여부": 1,
                "파일종류_ko": "테이블",
                "granularity_ko": "패널수준",
                "panel_id_컬럼존재_flag": 1,
                "site_컬럼존재_flag": 1,
                "유형_컬럼존재_flag": 1,
                "점수_컬럼존재_flag": 0,
                "panel_attach_candidate_flag": 1,
                "current_panel_count": 12,
                "candidate_panel_count": 3,
                "overlap_panel_count": 2,
                "overlap_rate": 2 / 12,
                "attachability_note_ko": "site+panel_id direct match 가능",
                "note_ko": "fixture panel attach candidate",
            },
            {
                "경로": "data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv",
                "존재여부": 1,
                "파일종류_ko": "테이블",
                "granularity_ko": "유형수준",
                "panel_id_컬럼존재_flag": 0,
                "site_컬럼존재_flag": 0,
                "유형_컬럼존재_flag": 1,
                "점수_컬럼존재_flag": 1,
                "panel_attach_candidate_flag": 0,
                "current_panel_count": "",
                "candidate_panel_count": "",
                "overlap_panel_count": "",
                "overlap_rate": "",
                "attachability_note_ko": "panel key 없음",
                "note_ko": "fixture type-level only",
            },
        ],
        [
            "경로",
            "존재여부",
            "파일종류_ko",
            "granularity_ko",
            "panel_id_컬럼존재_flag",
            "site_컬럼존재_flag",
            "유형_컬럼존재_flag",
            "점수_컬럼존재_flag",
            "panel_attach_candidate_flag",
            "current_panel_count",
            "candidate_panel_count",
            "overlap_panel_count",
            "overlap_rate",
            "attachability_note_ko",
            "note_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_gpvs_panel_attach_feasibility_v1.csv",
        [
            {
                "GPVS_패널별_직접판정_가능여부": "가능",
                "근거_ko": "fixture gpvs eval cases can be joined by site+panel_id",
                "최선_후보_파일": "_share/gpvs_fault_family_eval_cases.csv",
                "overlap_panel_count": 2,
                "overlap_rate": 2 / 12,
                "다음권장조치_ko": "fixture attach",
            }
        ],
        ["GPVS_패널별_직접판정_가능여부", "근거_ko", "최선_후보_파일", "overlap_panel_count", "overlap_rate", "다음권장조치_ko"],
    )

    write_csv(
        share / "panel_day_engine_gpvs_panel_attach_candidates_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": FORENSIC_HOLDOUT_PANEL_ID,
                "GPVS_참고유형_ko": "개방/장치이상 계열",
                "source_path": "_share/gpvs_fault_family_eval_cases.csv",
                "source_key_ko": "site+panel_id",
                "비고_ko": "prediction_source=critical_phenotype_v3",
            },
            {
                "site": SPECIAL_10305_SITE,
                "panel_id": SPECIAL_10305_PANEL_ID,
                "GPVS_참고유형_ko": "불확실",
                "source_path": "_share/gpvs_fault_family_eval_cases.csv",
                "source_key_ko": "site+panel_id",
                "비고_ko": "prediction_source=critical_phenotype_v3",
            },
            {
                "site": "siteCC",
                "panel_id": "common_1",
                "GPVS_참고유형_ko": "공통원인/인버터측 계열",
                "source_path": "_share/gpvs_fault_family_eval_cases.csv",
                "source_key_ko": "site+panel_id",
                "비고_ko": "prediction_source=strict_day_core_fallback",
            },
            {
                "site": "siteZ",
                "panel_id": "panel_extra",
                "GPVS_참고유형_ko": "무가시형 계열",
                "source_path": "_share/gpvs_fault_family_eval_cases.csv",
                "source_key_ko": "site+panel_id",
                "비고_ko": "not in panel table",
            },
        ],
        ["site", "panel_id", "GPVS_참고유형_ko", "source_path", "source_key_ko", "비고_ko"],
    )

    write_csv(
        share / "panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv",
        [
            {
                "recovered_model_exported_flag": 1,
                "recovered_feature_manifest_exported_flag": 1,
                "recovered_model_source_ko": "gpvs_train_supervised selected primary path reuse",
                "parity_overall_status_ko": "일치",
                "current_recovered_attachable_flag": 1,
                "note_ko": "fixture recovered by-type artifact parity ok",
            }
        ],
        [
            "recovered_model_exported_flag",
            "recovered_feature_manifest_exported_flag",
            "recovered_model_source_ko",
            "parity_overall_status_ko",
            "current_recovered_attachable_flag",
            "note_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv",
        [
            {
                "site": SPECIAL_10305_SITE,
                "panel_id": SPECIAL_10305_PANEL_ID,
                "event_reference_date": "2025-01-01",
                "gpvs_detailed_model_source": "recovered_artifact",
                "gpvs_family_label": "불확실",
                "gpvs_detailed_top1_fault_type": "F4L",
                "gpvs_detailed_top1_score": 0.82,
                "gpvs_detailed_top2_fault_type": "F2M",
                "gpvs_detailed_top2_score": 0.12,
                "gpvs_detailed_margin": 0.70,
                "gpvs_detailed_status_ko": "추론성공",
                "gpvs_detailed_reason_ko": "model_source=recovered_artifact; top1=F4L:0.82; top2=F2M:0.12",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_2",
                "event_reference_date": "2025-01-02",
                "gpvs_detailed_model_source": "recovered_artifact",
                "gpvs_family_label": "전기적 고장 계열",
                "gpvs_detailed_top1_fault_type": "F2M",
                "gpvs_detailed_top1_score": 0.99,
                "gpvs_detailed_top2_fault_type": "F4L",
                "gpvs_detailed_top2_score": 0.01,
                "gpvs_detailed_margin": 0.98,
                "gpvs_detailed_status_ko": "추론성공",
                "gpvs_detailed_reason_ko": "model_source=recovered_artifact; top1=F2M:0.99; top2=F4L:0.01",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_3",
                "event_reference_date": "2025-01-03",
                "gpvs_detailed_model_source": "recovered_artifact",
                "gpvs_family_label": "전기적 고장 계열",
                "gpvs_detailed_top1_fault_type": "F2M",
                "gpvs_detailed_top1_score": 0.98,
                "gpvs_detailed_top2_fault_type": "F4L",
                "gpvs_detailed_top2_score": 0.02,
                "gpvs_detailed_margin": 0.96,
                "gpvs_detailed_status_ko": "추론성공",
                "gpvs_detailed_reason_ko": "model_source=recovered_artifact; top1=F2M:0.98; top2=F4L:0.02",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_5",
                "event_reference_date": "2025-01-05",
                "gpvs_detailed_model_source": "recovered_artifact",
                "gpvs_family_label": "전기적 고장 계열",
                "gpvs_detailed_top1_fault_type": "F4L",
                "gpvs_detailed_top1_score": 0.76,
                "gpvs_detailed_top2_fault_type": "F2M",
                "gpvs_detailed_top2_score": 0.22,
                "gpvs_detailed_margin": 0.54,
                "gpvs_detailed_status_ko": "추론성공",
                "gpvs_detailed_reason_ko": "model_source=recovered_artifact; top1=F4L:0.76; top2=F2M:0.22",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_6",
                "event_reference_date": "2025-01-06",
                "gpvs_detailed_model_source": "recovered_artifact",
                "gpvs_family_label": "전기적 고장 계열",
                "gpvs_detailed_top1_fault_type": "F2M",
                "gpvs_detailed_top1_score": 0.97,
                "gpvs_detailed_top2_fault_type": "F4L",
                "gpvs_detailed_top2_score": 0.02,
                "gpvs_detailed_margin": 0.95,
                "gpvs_detailed_status_ko": "추론성공",
                "gpvs_detailed_reason_ko": "model_source=recovered_artifact; top1=F2M:0.97; top2=F4L:0.02",
            },
            {
                "site": "conalog",
                "panel_id": FORENSIC_HOLDOUT_PANEL_ID,
                "event_reference_date": "2025-03-21",
                "gpvs_detailed_model_source": "recovered_artifact",
                "gpvs_family_label": "전기적 고장 계열",
                "gpvs_detailed_top1_fault_type": "F2M",
                "gpvs_detailed_top1_score": 0.99,
                "gpvs_detailed_top2_fault_type": "F4L",
                "gpvs_detailed_top2_score": 0.01,
                "gpvs_detailed_margin": 0.98,
                "gpvs_detailed_status_ko": "추론성공",
                "gpvs_detailed_reason_ko": "model_source=recovered_artifact; top1=F2M:0.99; top2=F4L:0.01",
            },
        ],
        [
            "site",
            "panel_id",
            "event_reference_date",
            "gpvs_detailed_model_source",
            "gpvs_family_label",
            "gpvs_detailed_top1_fault_type",
            "gpvs_detailed_top1_score",
            "gpvs_detailed_top2_fault_type",
            "gpvs_detailed_top2_score",
            "gpvs_detailed_margin",
            "gpvs_detailed_status_ko",
            "gpvs_detailed_reason_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv",
        [
            {
                "site": SPECIAL_10305_SITE,
                "panel_id": SPECIAL_10305_PANEL_ID,
                "gpvs_family_label": "불확실",
                "gpvs_detailed_top1_fault_type": "F4L",
                "single_type_collapse_flag": 0,
                "attach_recommendation_ko": "attach_ok",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_2",
                "gpvs_family_label": "전기적 고장 계열",
                "gpvs_detailed_top1_fault_type": "F2M",
                "single_type_collapse_flag": 0,
                "attach_recommendation_ko": "attach_ok",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_3",
                "gpvs_family_label": "전기적 고장 계열",
                "gpvs_detailed_top1_fault_type": "F2M",
                "single_type_collapse_flag": 0,
                "attach_recommendation_ko": "attach_ok",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_5",
                "gpvs_family_label": "전기적 고장 계열",
                "gpvs_detailed_top1_fault_type": "F4L",
                "single_type_collapse_flag": 0,
                "attach_recommendation_ko": "attach_ok",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_6",
                "gpvs_family_label": "전기적 고장 계열",
                "gpvs_detailed_top1_fault_type": "F2M",
                "single_type_collapse_flag": 0,
                "attach_recommendation_ko": "attach_ok",
            },
            {
                "site": "conalog",
                "panel_id": FORENSIC_HOLDOUT_PANEL_ID,
                "gpvs_family_label": "전기적 고장 계열",
                "gpvs_detailed_top1_fault_type": "F2M",
                "single_type_collapse_flag": 0,
                "attach_recommendation_ko": "attach_ok",
            }
        ],
        [
            "site",
            "panel_id",
            "gpvs_family_label",
            "gpvs_detailed_top1_fault_type",
            "single_type_collapse_flag",
            "attach_recommendation_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv",
        [
            {
                "site": SPECIAL_10305_SITE,
                "panel_id": SPECIAL_10305_PANEL_ID,
                "gpvs_family_label": "불확실",
                "gpvs_detailed_top1_fault_type": "F4L",
                "overall_gpvs_reference_usefulness_ko": "주의참고",
                "overall_gpvs_trust_note_ko": "feature shift가 커서 reference-only로 읽어야 함",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_2",
                "gpvs_family_label": "전기적 고장 계열",
                "gpvs_detailed_top1_fault_type": "F2M",
                "overall_gpvs_reference_usefulness_ko": "비권장",
                "overall_gpvs_trust_note_ko": "scenario conflict가 커 direct trust를 주기 어려움",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_3",
                "gpvs_family_label": "전기적 고장 계열",
                "gpvs_detailed_top1_fault_type": "F2M",
                "overall_gpvs_reference_usefulness_ko": "비권장",
                "overall_gpvs_trust_note_ko": "scenario conflict가 커 direct trust를 주기 어려움",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_5",
                "gpvs_family_label": "전기적 고장 계열",
                "gpvs_detailed_top1_fault_type": "F4L",
                "overall_gpvs_reference_usefulness_ko": "주의참고",
                "overall_gpvs_trust_note_ko": "reference-only로 읽는 편이 안전함",
            },
            {
                "site": "siteA",
                "panel_id": "abrupt_6",
                "gpvs_family_label": "전기적 고장 계열",
                "gpvs_detailed_top1_fault_type": "F2M",
                "overall_gpvs_reference_usefulness_ko": "비권장",
                "overall_gpvs_trust_note_ko": "scenario conflict가 커 direct trust를 주기 어려움",
            },
            {
                "site": "conalog",
                "panel_id": FORENSIC_HOLDOUT_PANEL_ID,
                "gpvs_family_label": "개방/장치이상 계열",
                "gpvs_detailed_top1_fault_type": "F2M",
                "overall_gpvs_reference_usefulness_ko": "비권장",
                "overall_gpvs_trust_note_ko": "외부 scenario/family 방향성이 현재 kernel-log 원인군과 직접 충돌",
            },
        ],
        [
            "site",
            "panel_id",
            "gpvs_family_label",
            "gpvs_detailed_top1_fault_type",
            "overall_gpvs_reference_usefulness_ko",
            "overall_gpvs_trust_note_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_gpvs_canonical_dictionary_v1.csv",
        [
            {"canonical_gpvs_code": "F0", "current_usage_tier_ko": "baseline", "mlpe_reference_name_ko": "정상 기준선", "usage_rule_ko": "baseline only", "note_ko": "fixture"},
            {"canonical_gpvs_code": "F1", "current_usage_tier_ko": "reserved_system_level", "mlpe_reference_name_ko": "인버터 전력변환부 시스템 시나리오", "usage_rule_ko": "reserved", "note_ko": "fixture"},
            {"canonical_gpvs_code": "F2", "current_usage_tier_ko": "auxiliary_reference", "mlpe_reference_name_ko": "제어/계측 이상 보조 힌트", "usage_rule_ko": "auxiliary", "note_ko": "fixture"},
            {"canonical_gpvs_code": "F3", "current_usage_tier_ko": "confounder_only", "mlpe_reference_name_ko": "계통 교란 플래그", "usage_rule_ko": "confounder", "note_ko": "fixture"},
            {"canonical_gpvs_code": "F4", "current_usage_tier_ko": "core_reference", "mlpe_reference_name_ko": "패널·어레이 mismatch 핵심 참조", "usage_rule_ko": "core", "note_ko": "fixture"},
            {"canonical_gpvs_code": "F5", "current_usage_tier_ko": "core_reference_candidate", "mlpe_reference_name_ko": "부분 개방회로 계열 핵심 참조 후보", "usage_rule_ko": "candidate", "note_ko": "fixture"},
            {"canonical_gpvs_code": "F6", "current_usage_tier_ko": "reserved_system_level", "mlpe_reference_name_ko": "제어기 gain 이상 시스템 시나리오", "usage_rule_ko": "reserved", "note_ko": "fixture"},
            {"canonical_gpvs_code": "F7", "current_usage_tier_ko": "reserved_system_level", "mlpe_reference_name_ko": "제어기 시정수 이상 시스템 시나리오", "usage_rule_ko": "reserved", "note_ko": "fixture"},
        ],
        [
            "canonical_gpvs_code",
            "current_usage_tier_ko",
            "mlpe_reference_name_ko",
            "usage_rule_ko",
            "note_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv",
        [
            {"mlpe_official_fault_ko": "정션박스 손상", "canonical_gpvs_code": "F4", "match_strength_ko": "강", "match_role_ko": "핵심참조", "recommendation_ko": "reference only"},
            {"mlpe_official_fault_ko": "케이블 접점불량(단선)", "canonical_gpvs_code": "F5", "match_strength_ko": "강", "match_role_ko": "핵심참조", "recommendation_ko": "candidate"},
            {"mlpe_official_fault_ko": "인버터/스트링 동작 불량", "canonical_gpvs_code": "F2", "match_strength_ko": "약", "match_role_ko": "보조참조", "recommendation_ko": "hint only"},
        ],
        [
            "mlpe_official_fault_ko",
            "canonical_gpvs_code",
            "match_strength_ko",
            "match_role_ko",
            "recommendation_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv",
        [
            {
                "fault_panel_count": 6,
                "final_recommendation_ko": "참고축으로만 사용",
                "note_ko": "fixture summary",
            }
        ],
        [
            "fault_panel_count",
            "final_recommendation_ko",
            "note_ko",
        ],
    )

    write_csv(
        gpvs_out / "gpvs_window_scores.csv",
        [
            {
                "sample_id": "F1::w0",
                "source_id": "F1",
                "window_idx": 0,
                "fault_type": "F1",
                "level_drop_like": 0.9,
            }
        ],
        ["sample_id", "source_id", "window_idx", "fault_type", "level_drop_like"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research/prognostics/build_panel_day_engine_panel_multiaxis_verdict_v1.py"
    smoke_script = repo_root / "research/prognostics/smoke_test_panel_day_engine_panel_multiaxis_verdict_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        repo_root / "_share/panel_day_engine_panel_multiaxis_verdict_v1.csv",
        repo_root / "_share/panel_day_engine_panel_multiaxis_event_supplement_v1.csv",
        repo_root / "_share/panel_day_engine_panel_multiaxis_cluster_supplement_v1.csv",
        repo_root / "_share/panel_day_engine_panel_multiaxis_verdict_summary_v1.csv",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="panel_day_engine_multiaxis_verdict_smoke_") as tmp_dir:
        root = Path(tmp_dir)
        build_fixture(root)

        result = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(result.returncode == 0, f"builder failed: {result.stderr or result.stdout}")

        verdict_path = root / "_share/panel_day_engine_panel_multiaxis_verdict_v1.csv"
        event_path = root / "_share/panel_day_engine_panel_multiaxis_event_supplement_v1.csv"
        cluster_path = root / "_share/panel_day_engine_panel_multiaxis_cluster_supplement_v1.csv"
        summary_path = root / "_share/panel_day_engine_panel_multiaxis_verdict_summary_v1.csv"
        assert_true(verdict_path.exists(), "missing verdict csv")
        assert_true(event_path.exists(), "missing event supplement csv")
        assert_true(cluster_path.exists(), "missing cluster supplement csv")
        assert_true(summary_path.exists(), "missing summary csv")

        verdict_df = pd.read_csv(verdict_path, low_memory=False, encoding="utf-8-sig")
        event_df = pd.read_csv(event_path, low_memory=False, encoding="utf-8-sig")
        cluster_df = pd.read_csv(cluster_path, low_memory=False, encoding="utf-8-sig")
        summary_df = pd.read_csv(summary_path, low_memory=False, encoding="utf-8-sig")

        assert_true(not verdict_df.duplicated(subset=["site", "panel_id"]).any(), "main table must be unique by panel")
        assert_true(len(verdict_df) == 12, f"expected 12 unique panels, found {len(verdict_df)}")
        required_new_columns = {
            "사건유형_해석_ko",
            "전조흔적_flag",
            "순수급작_flag",
            "전조평가셋편입_flag",
            "급작평가셋편입_flag",
            "해석대평가차이_ko",
            "운영최초전조발견일",
            "운영최초전조마커",
            "사건해석상전조시작일",
            "benchmark전조시작일",
            "세부fault_type_code",
            "세부fault_type_label_ko",
            "세부fault_부착상태_ko",
            "세부fault_근거파일_ko",
            "세부fault_기준일",
            "세부fault_보류사유_ko",
            "GPVS_내부참고유형_ko",
            "GPVS_외부참조패턴_ko",
            "GPVS_참조사용등급_ko",
            "GPVS_참조설명_ko",
        }
        assert_true(required_new_columns.issubset(set(verdict_df.columns)), "front-facing interpretation/GPVS columns missing")
        forbidden_low_level_gpvs_columns = {
            "GPVS_참고유형_ko",
            "GPVS_근거_ko",
            "GPVS_미부착사유_ko",
            "GPVS_후보파일_ko",
            "GPVS_세부fault_code",
            "GPVS_세부fault_score",
            "GPVS_세부fault_rank2_code",
            "GPVS_세부fault_rank2_score",
            "GPVS_세부fault_margin",
            "GPVS_세부fault_status_ko",
            "GPVS_세부fault_부착상태_ko",
            "GPVS_세부fault_근거_ko",
            "GPVS_세부fault_판정주의_ko",
            "GPVS_시나리오_family_ko",
            "GPVS_시나리오명_ko",
            "GPVS_시나리오_고장상황설명_ko",
            "GPVS_운전모드_ko",
            "GPVS_해석주의_ko",
        }
        assert_true(
            not forbidden_low_level_gpvs_columns.intersection(set(verdict_df.columns)),
            "low-level GPVS columns should not leak into front-facing main verdict output",
        )

        overlap_row = verdict_df.loc[(verdict_df["site"].eq("siteA")) & (verdict_df["panel_id"].eq("abrupt_6"))].iloc[0]
        overlap_row_2 = verdict_df.loc[(verdict_df["site"].eq("siteA")) & (verdict_df["panel_id"].eq("abrupt_5"))].iloc[0]
        abrupt_only_row = verdict_df.loc[
            (verdict_df["site"].eq(SPECIAL_10305_SITE)) & (verdict_df["panel_id"].eq(SPECIAL_10305_PANEL_ID))
        ].iloc[0]
        forensic_row = verdict_df.loc[(verdict_df["site"].eq("conalog")) & (verdict_df["panel_id"].eq(FORENSIC_HOLDOUT_PANEL_ID))].iloc[0]
        common_row = verdict_df.loc[(verdict_df["site"].eq("siteCC")) & (verdict_df["panel_id"].eq("common_1"))].iloc[0]
        repeat_row = verdict_df.loc[(verdict_df["site"].eq("siteB")) & (verdict_df["panel_id"].eq("panel_repeat"))].iloc[0]
        unknown_row = verdict_df.loc[(verdict_df["site"].eq("siteQ")) & (verdict_df["panel_id"].eq("panel_queue_only"))].iloc[0]

        assert_true(overlap_row["사건유형_ko"] == "전조형 고장", "overlap row should be relabeled as precursor-led fault")
        assert_true(overlap_row["사건유형_해석_ko"] == "전조형 고장", "overlap interpretation layer mismatch")
        assert_true(overlap_row["최종고장양상_ko"] == "진행성 악화", "overlap row should follow corrected audit terminal pattern")
        assert_true(overlap_row["대표판정_ko"] == "전조형 고장", "representative verdict should match corrected event type")
        assert_true(overlap_row["사건이력_ko"] == "전조형 고장", "event history should preserve one precursor event after corrected audit sync")
        assert_true(int(overlap_row["전조흔적_flag"]) == 1, "overlap precursor-trace flag missing")
        assert_true(int(overlap_row["순수급작_flag"]) == 0, "overlap should not stay pure abrupt")
        assert_true(int(overlap_row["전조평가셋편입_flag"]) == 1, "overlap should stay in precursor eval set")
        assert_true(int(overlap_row["급작평가셋편입_flag"]) == 0, "overlap should be removed from abrupt eval set")
        assert_true(normalize_text(overlap_row["해석대평가차이_ko"]) == "", "overlap should not expose interpretation/eval mismatch")
        assert_true(int(overlap_row["전조형이력_flag"]) == 1, "overlap precursor flag missing")
        assert_true(int(overlap_row["급작고장이력_flag"]) == 0, "same-event overlap should not stay as abrupt event")
        assert_true(overlap_row["패널고장여부_ko"] == "고장", "panel fault status should mark overlap as fault")
        assert_true(overlap_row["GPVS_적용대상_ko"] == "적용대상", "fault row should be marked GPVS applicable")
        assert_true(overlap_row["커널로그_원인군_ko"] == "모듈손상형", "abrupt symptom map should stay highest priority")

        assert_true(overlap_row_2["사건유형_ko"] == "전조형 고장", "second overlap row should also be precursor-led")
        assert_true(overlap_row_2["최종고장양상_ko"] == "진행성 악화", "second overlap terminal pattern mapping failed")
        assert_true(overlap_row_2["사건이력_ko"] == "전조형 고장", "second overlap history mapping failed")
        assert_true(abrupt_only_row["사건유형_ko"] == "급작 고장", "pure abrupt representative mapping failed")
        assert_true(abrupt_only_row["사건유형_해석_ko"] == "급작 고장", "pure abrupt interpretation layer mismatch")
        assert_true(abrupt_only_row["최종고장양상_ko"] == "급작 발생", "pure abrupt terminal pattern mapping failed")
        assert_true(abrupt_only_row["패널고장여부_ko"] == "고장", "pure abrupt fault status mapping failed")
        assert_true(int(abrupt_only_row["전조흔적_flag"]) == 0, "pure abrupt row should not carry precursor trace")
        assert_true(int(abrupt_only_row["순수급작_flag"]) == 1, "pure abrupt row should keep 순수급작_flag=1")
        assert_true(int(abrupt_only_row["전조평가셋편입_flag"]) == 0, "pure abrupt row should not be in precursor eval set")
        assert_true(int(abrupt_only_row["급작평가셋편입_flag"]) == 1, "pure abrupt row should be in abrupt eval set")
        assert_true(abrupt_only_row["GPVS_적용대상_ko"] == "적용대상", "pure abrupt row should remain GPVS applicable")
        assert_true(forensic_row["사건유형_ko"] == "전조형 고장", "forensic target row should now be 전조형 고장")
        assert_true(forensic_row["사건유형_해석_ko"] == "전조형 고장", "forensic target interpretation layer mismatch")
        assert_true(forensic_row["대표판정_ko"] == "전조형 고장", "forensic target representative verdict mismatch")
        assert_true(forensic_row["최종고장양상_ko"] == "급격 종료", "forensic target terminal pattern mismatch")
        assert_true(forensic_row["사건이력_ko"] == "전조형 고장(급격 종료)", "forensic target history mismatch")
        assert_true(forensic_row["패널고장여부_ko"] == "고장", "forensic target should stay a fault panel")
        assert_true(int(forensic_row["전조흔적_flag"]) == 1, "forensic target should keep precursor-trace flag")
        assert_true(int(forensic_row["순수급작_flag"]) == 0, "forensic target should not stay pure abrupt")
        assert_true(int(forensic_row["전조평가셋편입_flag"]) == 1, "forensic target should now be in precursor eval set")
        assert_true(int(forensic_row["급작평가셋편입_flag"]) == 0, "forensic target should stay outside abrupt eval set")
        assert_true(str(forensic_row["운영최초전조발견일"]) == "2025-02-20", "forensic target operational first detection date mismatch")
        assert_true(str(forensic_row["운영최초전조마커"]) == "first_cond_evt", "forensic target operational first marker mismatch")
        assert_true(str(forensic_row["사건해석상전조시작일"]) == "2025-01-20", "forensic target interpretive onset mismatch")
        assert_true(str(forensic_row["benchmark전조시작일"]) == "2025-03-18", "forensic target benchmark onset mismatch")
        assert_true(normalize_text(forensic_row["해석대평가차이_ko"]) == "", "forensic target mismatch explanation should be cleared")
        assert_true(forensic_row["GPVS_적용대상_ko"] == "적용대상", "forensic target should stay GPVS applicable")
        assert_true("2025-01-20" in str(forensic_row["판정주의_ko"]), "forensic target note should mention precursor-like start date")
        assert_true("2025-03-21" in str(forensic_row["판정주의_ko"]), "forensic target note should mention strong trigger date")
        assert_true("persistent_5of7" in str(forensic_row["판정주의_ko"]), "forensic target note should mention explicit stored-field rule")

        assert_true(common_row["사건유형_ko"] == "공통원인 이벤트", "common-cause representative mapping failed")
        assert_true(common_row["사건유형_해석_ko"] == "공통원인 이벤트", "common-cause interpretation should match visible label")
        assert_true(common_row["최종고장양상_ko"] == "해당없음", "common-cause terminal pattern should be n/a")
        assert_true(common_row["패널고장여부_ko"] == "비고장", "common-cause fault status mapping failed")
        assert_true(int(common_row["전조흔적_flag"]) == 0, "common-cause row should keep precursor trace off")
        assert_true(int(common_row["순수급작_flag"]) == 0, "common-cause row should keep pure-abrupt off")
        assert_true(common_row["GPVS_적용대상_ko"] == "비대상", "common-cause row should be GPVS non-target")
        assert_true(common_row["커널로그_증상명_ko"] == "패턴 이상형", "common-cause symptom mapping failed")

        assert_true(repeat_row["사건유형_ko"] == "반복 이상", "repeat representative mapping failed")
        assert_true(repeat_row["사건유형_해석_ko"] == "반복 이상", "repeat interpretation should match visible label")
        assert_true(repeat_row["최종고장양상_ko"] == "해당없음", "repeat terminal pattern should be n/a")
        assert_true(repeat_row["패널고장여부_ko"] == "미확정", "repeat fault status mapping failed")
        assert_true(int(repeat_row["전조흔적_flag"]) == 0, "repeat row should keep precursor trace off")
        assert_true(int(repeat_row["순수급작_flag"]) == 0, "repeat row should keep pure-abrupt off")
        assert_true(repeat_row["GPVS_적용대상_ko"] == "비대상", "repeat row should be GPVS non-target")
        assert_true(repeat_row["사건이력_ko"] == "반복 이상", "repeat history mapping failed")

        assert_true(unknown_row["사건유형_ko"] == "불충분", "queue-only row should stay insufficient")
        assert_true(unknown_row["사건유형_해석_ko"] == "불충분", "unknown interpretation should match visible label")
        assert_true(unknown_row["최종고장양상_ko"] == "불충분", "queue-only terminal pattern should stay insufficient")
        assert_true(unknown_row["패널고장여부_ko"] == "미확정", "queue-only fault status mapping failed")
        assert_true(int(unknown_row["전조흔적_flag"]) == 0, "unknown row should keep precursor trace off")
        assert_true(int(unknown_row["순수급작_flag"]) == 0, "unknown row should keep pure-abrupt off")
        assert_true(unknown_row["GPVS_적용대상_ko"] == "비대상", "non-fault unresolved row should be GPVS non-target")
        assert_true(normalize_text(unknown_row["사건이력_ko"]) == "", "queue-only history should stay blank")

        assert_true(len(event_df) == 11, f"expected 11 event supplement rows, found {len(event_df)}")
        overlap_event_rows = event_df.loc[(event_df["site"].eq("siteA")) & (event_df["panel_id"].eq("abrupt_6"))]
        assert_true(len(overlap_event_rows) == 1, "same-event overlap should keep one precursor-led event row")
        assert_true(
            set(overlap_event_rows["사건유형_ko"]) == {"전조형 고장"},
            "overlap event supplement type mismatch",
        )
        precursor_rep_flag = overlap_event_rows.loc[overlap_event_rows["사건유형_ko"].eq("전조형 고장"), "대표판정여부_flag"].iloc[0]
        assert_true(int(precursor_rep_flag) == 1, "precursor-led overlap row should keep precursor as representative")
        assert_true(
            overlap_event_rows["비고_ko"].astype(str).str.contains("fault panel event audit explicit stored-field rule").all(),
            "overlap event supplement should mention fault audit explicit rule",
        )
        holdout_event_rows = event_df.loc[(event_df["site"].eq("conalog")) & (event_df["panel_id"].eq(FORENSIC_HOLDOUT_PANEL_ID))]
        assert_true(len(holdout_event_rows) == 1, "forensic target should keep one event-history row")
        assert_true(
            holdout_event_rows.iloc[0]["사건유형_ko"] == "전조형 고장",
            "forensic target event supplement type mismatch",
        )

        assert_true(len(cluster_df) == 1, f"expected 1 cluster supplement row, found {len(cluster_df)}")
        cluster_row = cluster_df.iloc[0]
        assert_true(cluster_row["대표판정_ko"] == "공통원인 이벤트", "cluster representative mapping failed")
        assert_true(cluster_row["운영위치_ko"] == "추가 발견 후보", "cluster operating location mapping failed")

        assert_true(forensic_row["GPVS_부착상태_ko"] == "부착", "matched forensic row should mark GPVS attached")
        assert_true(common_row["GPVS_부착상태_ko"] == "비대상", "common-cause row should not be a GPVS target")
        assert_true(repeat_row["GPVS_부착상태_ko"] == "비대상", "repeat row should not be a GPVS target")
        assert_true(unknown_row["GPVS_부착상태_ko"] == "비대상", "unknown row should not be a GPVS target")
        assert_true(abrupt_only_row["GPVS_부착상태_ko"] == "부착", "10305 row should keep GPVS family attach status after front-facing sync")
        assert_true(
            int((verdict_df["GPVS_부착상태_ko"] == "부착").sum()) == 2,
            "GPVS attach count must equal feasibility overlap count",
        )
        assert_true(forensic_row["GPVS_내부참고유형_ko"] == "개방/장치이상 계열", "c429 front-facing internal GPVS label mismatch")
        assert_true(forensic_row["GPVS_외부참조패턴_ko"] == "제어·계측 이상 힌트", "c429 front-facing external GPVS pattern mismatch")
        assert_true(forensic_row["GPVS_참조사용등급_ko"] == "비권장", "c429 front-facing GPVS usage grade mismatch")
        assert_true(
            "제어 피드백 센서 이상과 유사한 패턴" in str(forensic_row["GPVS_참조설명_ko"]),
            "c429 front-facing GPVS description mismatch",
        )
        assert_true(abrupt_only_row["GPVS_내부참고유형_ko"] == "불확실", "10305 front-facing internal GPVS label mismatch")
        assert_true(abrupt_only_row["GPVS_외부참조패턴_ko"] == "패널·어레이 mismatch 참조", "10305-like front-facing external GPVS pattern mismatch")
        assert_true(abrupt_only_row["GPVS_참조사용등급_ko"] == "주의참고", "10305-like front-facing GPVS usage grade mismatch")
        assert_true(
            "일부 패널 불균형이 나타나는 패턴" in str(abrupt_only_row["GPVS_참조설명_ko"]),
            "10305-like front-facing GPVS description mismatch",
        )
        for row in [common_row, repeat_row, unknown_row]:
            for column in [
                "GPVS_내부참고유형_ko",
                "GPVS_외부참조패턴_ko",
                "GPVS_참조사용등급_ko",
                "GPVS_참조설명_ko",
            ]:
                assert_true(normalize_text(row[column]) == "", f"non-fault rows must keep {column} blank")

        assert_true(abrupt_only_row["세부fault_부착상태_ko"] == "부착", "exact-date consensus row should attach detailed fault")
        assert_true(abrupt_only_row["세부fault_type_code"] == "F101", "attached detailed fault code mismatch")
        assert_true(abrupt_only_row["세부fault_type_label_ko"] == "GPVS Fault1", "attached detailed fault label mapping failed")
        assert_true("PVFAULT_labels_day.csv" in str(abrupt_only_row["세부fault_근거파일_ko"]), "attached detailed fault should expose source file")
        assert_true(abrupt_only_row["세부fault_기준일"] == "2025-01-01", "attached detailed fault reference date mismatch")
        assert_true(normalize_text(abrupt_only_row["세부fault_보류사유_ko"]) == "", "attached detailed fault should keep hold reason blank")

        conflict_row = verdict_df.loc[(verdict_df["site"].eq("siteA")) & (verdict_df["panel_id"].eq("abrupt_2"))].iloc[0]
        miss_row = verdict_df.loc[(verdict_df["site"].eq("siteA")) & (verdict_df["panel_id"].eq("abrupt_3"))].iloc[0]
        precursor_attach_row = verdict_df.loc[(verdict_df["site"].eq("siteA")) & (verdict_df["panel_id"].eq("abrupt_5"))].iloc[0]
        precursor_attach_row_2 = verdict_df.loc[(verdict_df["site"].eq("siteA")) & (verdict_df["panel_id"].eq("abrupt_6"))].iloc[0]

        assert_true(conflict_row["GPVS_외부참조패턴_ko"] == "제어·계측 이상 힌트", "first abrupt front-facing GPVS pattern mismatch")
        assert_true(conflict_row["GPVS_참조사용등급_ko"] == "비권장", "first abrupt GPVS usage grade mismatch")
        assert_true(miss_row["GPVS_외부참조패턴_ko"] == "제어·계측 이상 힌트", "second abrupt front-facing GPVS pattern mismatch")
        assert_true(miss_row["GPVS_참조사용등급_ko"] == "비권장", "second abrupt GPVS usage grade mismatch")
        assert_true(precursor_attach_row["GPVS_외부참조패턴_ko"] == "패널·어레이 mismatch 참조", "precursor F4 front-facing GPVS pattern mismatch")
        assert_true(precursor_attach_row["GPVS_참조사용등급_ko"] == "주의참고", "precursor F4 GPVS usage grade mismatch")
        assert_true(precursor_attach_row_2["GPVS_외부참조패턴_ko"] == "제어·계측 이상 힌트", "second precursor F2 front-facing GPVS pattern mismatch")
        assert_true(precursor_attach_row_2["GPVS_참조사용등급_ko"] == "비권장", "second precursor F2 GPVS usage grade mismatch")

        assert_true(conflict_row["세부fault_부착상태_ko"] == "보류", "conflict path should hold detailed fault attach")
        assert_true(normalize_text(conflict_row["세부fault_type_code"]) == "", "conflict row must not keep detailed fault code")
        assert_true(conflict_row["세부fault_보류사유_ko"] == "exact_date_conflict", "conflict row hold reason mismatch")
        assert_true(conflict_row["세부fault_기준일"] == "2025-01-02", "conflict row reference date mismatch")

        assert_true(miss_row["세부fault_부착상태_ko"] == "보류", "no-exact-match path should hold detailed fault attach")
        assert_true(miss_row["세부fault_보류사유_ko"] == "no_exact_date_match", "miss row hold reason mismatch")
        assert_true(normalize_text(miss_row["세부fault_근거파일_ko"]) == "", "miss row should keep detailed-fault source blank")

        assert_true(precursor_attach_row["세부fault_부착상태_ko"] == "부착", "precursor row should still attach detailed fault when consensus exists")
        assert_true(precursor_attach_row["세부fault_type_label_ko"] == "GPVS Fault5", "precursor detailed fault label mapping failed")
        assert_true(precursor_attach_row_2["세부fault_type_label_ko"] == "GPVS Fault6", "second precursor detailed fault label mapping failed")

        assert_true(forensic_row["세부fault_부착상태_ko"] == "보류", "c429 fixture should stay detailed-fault hold in no-match path")
        assert_true(forensic_row["세부fault_보류사유_ko"] == "no_exact_date_match", "c429 detailed-fault hold reason mismatch")
        assert_true(common_row["세부fault_부착상태_ko"] == "비대상", "common-cause row should stay detailed-fault non-target")
        assert_true(repeat_row["세부fault_부착상태_ko"] == "비대상", "repeat row should stay detailed-fault non-target")
        assert_true(unknown_row["세부fault_부착상태_ko"] == "비대상", "unknown row should stay detailed-fault non-target")

        summary_row = summary_df.iloc[0]
        rep_counts = verdict_df["사건유형_ko"].value_counts().to_dict()
        fault_counts = verdict_df["패널고장여부_ko"].value_counts().to_dict()
        precursor_event_count = int(pd.to_numeric(verdict_df["전조형이력_flag"]).sum())
        pure_abrupt_event_count = int(pd.to_numeric(verdict_df["급작고장이력_flag"]).sum())
        common_event_count = int(pd.to_numeric(verdict_df["공통원인이력_flag"]).sum())
        repeat_event_count = int(pd.to_numeric(verdict_df["반복이상이력_flag"]).sum())
        abrupt_ending_panel_count = int(
            (
                verdict_df["사건유형_ko"].eq("전조형 고장")
                & verdict_df["최종고장양상_ko"].eq("급격 종료")
            ).sum()
        )
        progressive_precursor_panel_count = int(
            (
                verdict_df["사건유형_ko"].eq("전조형 고장")
                & verdict_df["최종고장양상_ko"].eq("진행성 악화")
            ).sum()
        )
        pure_abrupt_panel_count = int(verdict_df["사건유형_ko"].eq("급작 고장").sum())
        precursor_trace_panel_count = int(pd.to_numeric(verdict_df["전조흔적_flag"]).sum())
        pure_abrupt_flag_panel_count = int(pd.to_numeric(verdict_df["순수급작_flag"]).sum())
        precursor_eval_included_count = int(pd.to_numeric(verdict_df["전조평가셋편입_flag"]).sum())
        abrupt_eval_included_count = int(pd.to_numeric(verdict_df["급작평가셋편입_flag"]).sum())
        interpretation_eval_mismatch_count = int(verdict_df["해석대평가차이_ko"].map(normalize_text).ne("").sum())
        gpvs_front_pattern_attached_count = int(verdict_df["GPVS_외부참조패턴_ko"].map(normalize_text).ne("").sum())
        gpvs_front_pattern_blank_fault_count = int(
            verdict_df.loc[verdict_df["패널고장여부_ko"].eq("고장"), "GPVS_외부참조패턴_ko"].map(normalize_text).eq("").sum()
        )
        gpvs_front_pattern_nontarget_count = int(
            verdict_df.loc[verdict_df["패널고장여부_ko"].ne("고장"), "GPVS_외부참조패턴_ko"].map(normalize_text).eq("").sum()
        )
        gpvs_pattern_f2_count = int(verdict_df["GPVS_외부참조패턴_ko"].eq("제어·계측 이상 힌트").sum())
        gpvs_pattern_f4_count = int(verdict_df["GPVS_외부참조패턴_ko"].eq("패널·어레이 mismatch 참조").sum())
        assert_true(int(summary_row["전체_패널수"]) == 12, "summary total panel count mismatch")
        assert_true(int(verdict_df["패널고장여부_ko"].eq("고장").sum()) == 6, "fixture fault-panel count should be 6")
        assert_true(precursor_event_count == 3, "fixture precursor event count should be 3")
        assert_true(pure_abrupt_event_count == 3, "fixture pure abrupt event count should be 3")
        assert_true(abrupt_ending_panel_count == 1, "fixture abrupt-ending precursor count should be 1")
        assert_true(progressive_precursor_panel_count == 2, "fixture progressive precursor panel count should be 2")
        assert_true(pure_abrupt_panel_count == 3, "fixture pure abrupt panel count should be 3")
        assert_true(precursor_trace_panel_count == 3, "fixture precursor-trace panel count should be 3")
        assert_true(pure_abrupt_flag_panel_count == 3, "fixture pure-abrupt flag count should be 3")
        assert_true(precursor_eval_included_count == 3, "fixture precursor-eval inclusion count should be 3")
        assert_true(abrupt_eval_included_count == 3, "fixture abrupt-eval inclusion count should be 3")
        assert_true(interpretation_eval_mismatch_count == 0, "fixture interpretation/eval mismatch count should be 0")
        assert_true(int(summary_row["고유_고장패널수"]) == int(verdict_df["패널고장여부_ko"].eq("고장").sum()), "unique fault-panel summary must come from final rows")
        assert_true(int(summary_row["사건해석_전조형_패널수"]) == int(rep_counts.get("전조형 고장", 0)), "interpreted precursor summary must come from final rows")
        assert_true(int(summary_row["사건해석_급작_패널수"]) == pure_abrupt_panel_count, "interpreted abrupt summary must come from final rows")
        assert_true(int(summary_row["사건해석_전조형_급격종료_패널수"]) == abrupt_ending_panel_count, "precursor abrupt-ending summary must come from final rows")
        assert_true(int(summary_row["사건해석_전조형_진행성악화_패널수"]) == progressive_precursor_panel_count, "progressive precursor summary must come from final rows")
        assert_true(int(summary_row["전조흔적_패널수"]) == precursor_trace_panel_count, "precursor-trace summary must come from final rows")
        assert_true(pure_abrupt_flag_panel_count == pure_abrupt_panel_count, "pure-abrupt flag count should align with interpreted abrupt count in this fixture")
        assert_true(int(summary_row["엄격전조평가셋_패널수"]) == precursor_eval_included_count, "strict precursor-eval inclusion summary must come from final rows")
        assert_true(int(summary_row["순수급작평가셋_패널수"]) == abrupt_eval_included_count, "pure abrupt-eval inclusion summary must come from final rows")
        assert_true(int(summary_row["해석과평가셋불일치_패널수"]) == interpretation_eval_mismatch_count, "interpretation/eval mismatch summary must come from final rows")
        assert_true(int(summary_row["공통원인이력_패널수"]) == common_event_count, "common membership summary must come from final rows")
        assert_true(int(summary_row["반복이상이력_패널수"]) == repeat_event_count, "repeat membership summary must come from final rows")
        assert_true(int(summary_row["대표판정_급작수"]) == int(rep_counts.get("급작 고장", 0)), "representative abrupt summary mismatch")
        assert_true(int(summary_row["대표판정_전조형수"]) == int(rep_counts.get("전조형 고장", 0)), "representative precursor summary mismatch")
        assert_true(int(summary_row["대표판정_공통원인수"]) == int(rep_counts.get("공통원인 이벤트", 0)), "representative common summary mismatch")
        assert_true(int(summary_row["대표판정_반복이상수"]) == int(rep_counts.get("반복 이상", 0)), "representative repeat summary mismatch")
        assert_true(int(summary_row["대표판정_고장유형보류수"]) == int(rep_counts.get("고장유형 보류", 0)), "representative holdout summary mismatch")
        assert_true(int(summary_row["대표판정_불충분수"]) == int(rep_counts.get("불충분", 0)), "representative insufficient summary mismatch")
        assert_true(int(summary_row["고장_패널수"]) == int(fault_counts.get("고장", 0)), "fault-status summary mismatch")
        assert_true(int(summary_row["비고장_패널수"]) == int(fault_counts.get("비고장", 0)), "non-fault summary mismatch")
        assert_true(int(summary_row["미확정_패널수"]) == int(fault_counts.get("미확정", 0)), "unknown-status summary mismatch")
        assert_true(int(summary_row["GPVS_적용대상_패널수"]) == 6, "GPVS applicable summary mismatch")
        assert_true(int(summary_row["GPVS_부착수"]) == 2, "GPVS attached summary mismatch")
        assert_true(int(summary_row["GPVS_미부착수"]) == 4, "GPVS unattached summary mismatch")
        assert_true(int(summary_row["GPVS_비대상수"]) == 6, "GPVS non-target summary mismatch")
        assert_true(int(summary_row["GPVS_미부착_패널key없음수"]) == 4, "GPVS unattached missing-panel-key summary mismatch")
        assert_true(int(summary_row["GPVS_미부착_key부족수"]) == 0, "GPVS key-poor summary mismatch")
        assert_true(int(summary_row["GPVS_미부착_산출물없음수"]) == 0, "GPVS no-artifact summary mismatch")
        assert_true(int(summary_row["GPVS_세부fault_부착수"]) == gpvs_front_pattern_attached_count, "GPVS learned by-type attached summary mismatch")
        assert_true(int(summary_row["GPVS_세부fault_판정유보수"]) == gpvs_front_pattern_blank_fault_count, "GPVS learned by-type deferred summary mismatch")
        assert_true(int(summary_row["GPVS_세부fault_추론불가수"]) == 0, "GPVS learned by-type impossible summary mismatch")
        assert_true(gpvs_front_pattern_attached_count == 6, "fixture should attach GPVS front-facing reference pattern to all 6 fault panels")
        assert_true(gpvs_front_pattern_blank_fault_count == 0, "fixture should keep GPVS front-facing blank fault count at 0")
        assert_true(int(summary_row["GPVS_세부fault_부착패널수"]) == gpvs_front_pattern_attached_count, "GPVS detailed attached panel summary mismatch")
        assert_true(int(summary_row["GPVS_세부fault_판정유보패널수"]) == gpvs_front_pattern_blank_fault_count, "GPVS detailed deferred panel summary mismatch")
        assert_true(int(summary_row["GPVS_세부fault_비대상패널수"]) == gpvs_front_pattern_nontarget_count, "GPVS detailed non-target panel summary mismatch")
        assert_true(int(summary_row["GPVS_세부fault_F2M_패널수"]) == gpvs_pattern_f2_count, "GPVS detailed F2M summary mismatch")
        assert_true(int(summary_row["GPVS_세부fault_F4L_패널수"]) == gpvs_pattern_f4_count, "GPVS detailed F4L summary mismatch")
        assert_true(gpvs_pattern_f2_count == 4, "fixture should keep GPVS front-facing F2 count at 4")
        assert_true(gpvs_pattern_f4_count == 2, "fixture should keep GPVS front-facing F4 count at 2")
        stale_summary_columns = {
            "세부fault_부착수",
            "세부fault_보류수",
            "세부fault_비대상수",
            "세부fault_exact_date_match_패널수",
            "세부fault_exact_date_conflict_패널수",
            "세부fault_exact_date_miss_패널수",
        }
        assert_true(not stale_summary_columns.intersection(set(summary_df.columns)), "summary should not keep stale exact-date bridge columns")
        assert_true(int(summary_row["사건보조행수"]) == len(event_df), "event supplement summary mismatch")
        assert_true(int(summary_row["클러스터_보조행수"]) == len(cluster_df), "cluster supplement summary mismatch")
        assert_true("event type과 terminal failure pattern" in str(summary_row["note_ko"]), "summary note should mention event-type vs terminal-pattern split")
        assert_true("해석" in str(summary_row["note_ko"]), "summary note should mention interpretation layer")
        assert_true("fault panel event audit" in str(summary_row["note_ko"]), "summary note should mention fault-panel audit sync")
        assert_true("same-day fallback onset" in str(summary_row["note_ko"]), "summary note should mention same-day fallback abrupt correction")
        assert_true("모두 부착" in str(summary_row["note_ko"]) or "부분" in str(summary_row["note_ko"]), "summary note should mention GPVS attach scope")
        assert_true("GPVS 세부 fault는 learned GPVS by-type inference 결과" in str(summary_row["note_ko"]), "summary note should mention learned GPVS by-type inference")
        assert_true("외부 GPVS 실험 시나리오 참조축" in str(summary_row["note_ko"]), "summary note should mention external GPVS scenario axis")
        assert_true("PVFAULT exact-date bridge" in str(summary_row["note_ko"]), "summary note should explain retired PVFAULT exact-date bridge path")
        assert_true("retired path" in str(summary_row["note_ko"]) or "retire" in str(summary_row["note_ko"]), "summary note should mark exact-date bridge path as retired")
        assert_true("현재 부착 0건 / 보류 6건 / 비대상 19건" not in str(summary_row["note_ko"]), "summary note should not keep stale 0/6/19 bridge wording")

        assert_true(cluster_row["GPVS_참고유형_ko"] == "미부착", "cluster row must stay GPVS unattached")
        assert_true(cluster_row["GPVS_근거_ko"] == "현재 저장 산출물에는 패널별 GPVS 직접 판정이 없음", "cluster row must keep GPVS absence reason")

    after = {path: file_digest(path) for path in official_outputs}
    assert_true(before == after, "official outputs changed during smoke test")


if __name__ == "__main__":
    main()
