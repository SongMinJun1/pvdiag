#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import py_compile
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


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


BANNED_PANEL_IDS = [
    "45dfa600-79b7-428e-95d3-22345a068986.1.0",
    "45dfa600-79b7-428e-95d3-22345a068986.1.1",
    "d15b9e13-4117-49ae-a78f-7ace013e48de.0.0",
    "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.9",
]

FORENSIC_HOLDOUT_PANEL_ID = "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"


def build_fixture(root: Path, omit_reaudit_panel_ids: set[str] | None = None) -> None:
    omit_reaudit_panel_ids = omit_reaudit_panel_ids or set()
    share = root / "_share"
    share.mkdir(parents=True, exist_ok=True)

    write_csv(
        share / "panel_day_engine_non_precursor_performance_cases_v1.csv",
        [
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "site": "sitea",
                "panel_id": "p1",
                "anchor_date": "2025-01-01",
                "anchor_source": "fault_start_date",
                "vendor_fault_family": "diode_like",
                "candidate_validity": "true_positive",
                "vendor_reply_class": "vendor_pattern_positive",
                "confirmed_fault_hit_by_anchor_flag": 0,
                "confirmed_fault_hit_within_3d_after_flag": 0,
                "confirmed_fault_hit_within_7d_after_flag": 0,
                "critical_fault_hit_by_anchor_flag": 1,
                "critical_fault_hit_within_3d_after_flag": 0,
                "critical_fault_hit_within_7d_after_flag": 0,
                "final_fault_hit_by_anchor_flag": 1,
                "final_fault_hit_within_3d_after_flag": 0,
                "final_fault_hit_within_7d_after_flag": 0,
                "abrupt_eval_reason_ko": "급작 anchor hit",
            },
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "site": "sitea",
                "panel_id": "p2",
                "anchor_date": "2025-01-02",
                "anchor_source": "fault_start_date",
                "vendor_fault_family": "diode_like",
                "candidate_validity": "true_positive",
                "vendor_reply_class": "vendor_likely_positive",
                "confirmed_fault_hit_by_anchor_flag": 0,
                "confirmed_fault_hit_within_3d_after_flag": 0,
                "confirmed_fault_hit_within_7d_after_flag": 0,
                "critical_fault_hit_by_anchor_flag": 1,
                "critical_fault_hit_within_3d_after_flag": 0,
                "critical_fault_hit_within_7d_after_flag": 0,
                "final_fault_hit_by_anchor_flag": 0,
                "final_fault_hit_within_3d_after_flag": 1,
                "final_fault_hit_within_7d_after_flag": 1,
                "abrupt_eval_reason_ko": "다이오드형 급작 anchor hit",
            },
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "site": "sitec",
                "panel_id": BANNED_PANEL_IDS[0],
                "anchor_date": "2025-01-07",
                "anchor_source": "strict_trigger_date",
                "vendor_fault_family": "none_visible",
                "candidate_validity": "false_positive",
                "vendor_reply_class": "vendor_rejected",
                "confirmed_fault_hit_by_anchor_flag": 0,
                "confirmed_fault_hit_within_3d_after_flag": 0,
                "confirmed_fault_hit_within_7d_after_flag": 0,
                "critical_fault_hit_by_anchor_flag": 1,
                "critical_fault_hit_within_3d_after_flag": 0,
                "critical_fault_hit_within_7d_after_flag": 0,
                "final_fault_hit_by_anchor_flag": 1,
                "final_fault_hit_within_3d_after_flag": 0,
                "final_fault_hit_within_7d_after_flag": 0,
                "abrupt_eval_reason_ko": "전압 0 수준 급락만 관찰",
            },
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "site": "sitec",
                "panel_id": BANNED_PANEL_IDS[1],
                "anchor_date": "2025-01-08",
                "anchor_source": "strict_trigger_date",
                "vendor_fault_family": "none_visible",
                "candidate_validity": "false_positive",
                "vendor_reply_class": "vendor_rejected",
                "confirmed_fault_hit_by_anchor_flag": 0,
                "confirmed_fault_hit_within_3d_after_flag": 0,
                "confirmed_fault_hit_within_7d_after_flag": 0,
                "critical_fault_hit_by_anchor_flag": 1,
                "critical_fault_hit_within_3d_after_flag": 0,
                "critical_fault_hit_within_7d_after_flag": 0,
                "final_fault_hit_by_anchor_flag": 0,
                "final_fault_hit_within_3d_after_flag": 0,
                "final_fault_hit_within_7d_after_flag": 1,
                "abrupt_eval_reason_ko": "출력 급저하만 관찰",
            },
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "site": "sitec",
                "panel_id": BANNED_PANEL_IDS[2],
                "anchor_date": "2025-01-09",
                "anchor_source": "strict_trigger_date",
                "vendor_fault_family": "none_visible",
                "candidate_validity": "false_positive",
                "vendor_reply_class": "vendor_rejected",
                "confirmed_fault_hit_by_anchor_flag": 0,
                "confirmed_fault_hit_within_3d_after_flag": 0,
                "confirmed_fault_hit_within_7d_after_flag": 0,
                "critical_fault_hit_by_anchor_flag": 1,
                "critical_fault_hit_within_3d_after_flag": 0,
                "critical_fault_hit_within_7d_after_flag": 0,
                "final_fault_hit_by_anchor_flag": 1,
                "final_fault_hit_within_3d_after_flag": 0,
                "final_fault_hit_within_7d_after_flag": 0,
                "abrupt_eval_reason_ko": "strict false positive",
            },
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "site": "sitec",
                "panel_id": BANNED_PANEL_IDS[3],
                "anchor_date": "2025-01-10",
                "anchor_source": "strict_trigger_date",
                "vendor_fault_family": "none_visible",
                "candidate_validity": "false_positive",
                "vendor_reply_class": "vendor_rejected",
                "confirmed_fault_hit_by_anchor_flag": 0,
                "confirmed_fault_hit_within_3d_after_flag": 0,
                "confirmed_fault_hit_within_7d_after_flag": 0,
                "critical_fault_hit_by_anchor_flag": 1,
                "critical_fault_hit_within_3d_after_flag": 0,
                "critical_fault_hit_within_7d_after_flag": 0,
                "final_fault_hit_by_anchor_flag": 0,
                "final_fault_hit_within_3d_after_flag": 1,
                "final_fault_hit_within_7d_after_flag": 1,
                "abrupt_eval_reason_ko": "strict false positive",
            },
        ],
        [
            "eval_bucket_v2",
            "site",
            "panel_id",
            "anchor_date",
            "anchor_source",
            "vendor_fault_family",
            "candidate_validity",
            "vendor_reply_class",
            "confirmed_fault_hit_by_anchor_flag",
            "confirmed_fault_hit_within_3d_after_flag",
            "confirmed_fault_hit_within_7d_after_flag",
            "critical_fault_hit_by_anchor_flag",
            "critical_fault_hit_within_3d_after_flag",
            "critical_fault_hit_within_7d_after_flag",
            "final_fault_hit_by_anchor_flag",
            "final_fault_hit_within_3d_after_flag",
            "final_fault_hit_within_7d_after_flag",
            "abrupt_eval_reason_ko",
        ],
    )

    reaudit_rows = [
        {
            "site": "sitea",
            "panel_id": "p1",
            "strict_trigger_date": "2025-01-01",
            "reason_summary": "다이오드 손상 의심",
            "vendor_reply_class": "vendor_pattern_positive",
            "vendor_fault_family": "diode_like",
            "candidate_validity": "true_positive",
            "vendor_note": "다이오드 쪽 현상",
        },
        {
            "site": "sitea",
            "panel_id": "p2",
            "strict_trigger_date": "2025-01-02",
            "reason_summary": "다이오드 라인 단선형 징후",
            "vendor_reply_class": "vendor_likely_positive",
            "vendor_fault_family": "diode_like",
            "candidate_validity": "true_positive",
            "vendor_note": "다이오드 계열",
        },
        {
            "site": "sitea",
            "panel_id": "p3",
            "strict_trigger_date": "2025-01-03",
            "reason_summary": "다이오드 손상으로 해석",
            "vendor_reply_class": "vendor_pattern_positive",
            "vendor_fault_family": "diode_like",
            "candidate_validity": "true_positive",
            "vendor_note": "다이오드형 accepted truth",
        },
        {
            "site": "siteb",
            "panel_id": "p4",
            "strict_trigger_date": "2025-01-04",
            "reason_summary": "다이오드 계열 급작 사례",
            "vendor_reply_class": "vendor_pattern_positive",
            "vendor_fault_family": "diode_like",
            "candidate_validity": "true_positive",
            "vendor_note": "다이오드형 accepted truth",
        },
        {
            "site": "conalog",
            "panel_id": FORENSIC_HOLDOUT_PANEL_ID,
            "strict_trigger_date": "2025-03-21",
            "reason_summary": "장치 또는 개방 문제로 해석",
            "vendor_reply_class": "needs_more_info",
            "vendor_fault_family": "open_or_device_issue_like",
            "candidate_validity": "true_positive",
            "vendor_note": "장치 이슈 accepted truth",
        },
        {
            "site": "siteb",
            "panel_id": "p6",
            "strict_trigger_date": "2025-01-06",
            "reason_summary": "모듈 손상으로 보임",
            "vendor_reply_class": "vendor_likely_positive",
            "vendor_fault_family": "module_damage_like",
            "candidate_validity": "true_positive",
            "vendor_note": "모듈 손상 accepted truth",
        },
        {
            "site": "sitec",
            "panel_id": BANNED_PANEL_IDS[0],
            "strict_trigger_date": "2025-01-07",
            "reason_summary": "banned false positive",
            "vendor_reply_class": "vendor_rejected",
            "vendor_fault_family": "diode_like",
            "candidate_validity": "false_positive",
            "vendor_note": "",
        },
        {
            "site": "sitec",
            "panel_id": BANNED_PANEL_IDS[1],
            "strict_trigger_date": "2025-01-08",
            "reason_summary": "banned false positive",
            "vendor_reply_class": "vendor_rejected",
            "vendor_fault_family": "open_or_device_issue_like",
            "candidate_validity": "false_positive",
            "vendor_note": "",
        },
    ]
    reaudit_rows = [row for row in reaudit_rows if row["panel_id"] not in omit_reaudit_panel_ids]
    write_csv(
        share / "panel_date_reaudit_working.csv",
        reaudit_rows,
        [
            "site",
            "panel_id",
            "strict_trigger_date",
            "reason_summary",
            "vendor_reply_class",
            "vendor_fault_family",
            "candidate_validity",
            "vendor_note",
        ],
    )

    write_csv(
        share / "panel_day_engine_local_precursor_eligibility_cases_v1.csv",
        [
            {
                "site": "sitea",
                "panel_id": "p1",
                "strict_trigger_date": "2025-01-01",
                "fault_start_date": "2025-01-01",
                "vendor_fault_family": "diode_like",
                "precursor_eligible_flag": 1,
            },
            {
                "site": "sitea",
                "panel_id": "p2",
                "strict_trigger_date": "2025-01-02",
                "fault_start_date": "2025-01-02",
                "vendor_fault_family": "diode_like",
                "precursor_eligible_flag": 1,
            },
            {
                "site": "sitea",
                "panel_id": "p3",
                "strict_trigger_date": "2025-01-03",
                "fault_start_date": "2025-01-03",
                "vendor_fault_family": "diode_like",
                "precursor_eligible_flag": 1,
            },
            {
                "site": "siteb",
                "panel_id": "p4",
                "strict_trigger_date": "2025-01-04",
                "fault_start_date": "2025-01-04",
                "vendor_fault_family": "diode_like",
                "precursor_eligible_flag": 1,
            },
            {
                "site": "siteb",
                "panel_id": "p6",
                "strict_trigger_date": "2025-01-06",
                "fault_start_date": "2025-01-06",
                "vendor_fault_family": "module_damage_like",
                "precursor_eligible_flag": 1,
            },
            {
                "site": "conalog",
                "panel_id": FORENSIC_HOLDOUT_PANEL_ID,
                "strict_trigger_date": "2025-03-21",
                "fault_start_date": "2025-03-21",
                "vendor_fault_family": "open_or_device_issue_like",
                "precursor_eligible_flag": 0,
            },
        ],
        [
            "site",
            "panel_id",
            "strict_trigger_date",
            "fault_start_date",
            "vendor_fault_family",
            "precursor_eligible_flag",
        ],
    )

    write_csv(
        share / "panel_day_engine_project_eval_matrix_v1.csv",
        [
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "target_name": "final_fault_hit_by_anchor",
                "support_positive": 6,
                "recall": 0.8333333333333334,
                "precision": 0.8333333333333334,
                "f1": 0.8333333333333334,
            }
        ],
        ["eval_scope", "target_name", "support_positive", "recall", "precision", "f1"],
    )

    write_csv(
        share / "panel_day_engine_precursor_abrupt_consistency_cases_v1.csv",
        [
            {
                "site": "sitea",
                "panel_id": "p1",
                "same_event_flag": 1,
                "distinct_event_flag": 0,
                "consistency_judgment_ko": "같은 사건",
            },
            {
                "site": "siteb",
                "panel_id": "p6",
                "same_event_flag": 1,
                "distinct_event_flag": 0,
                "consistency_judgment_ko": "같은 사건",
            },
        ],
        ["site", "panel_id", "same_event_flag", "distinct_event_flag", "consistency_judgment_ko"],
    )

    write_csv(
        share / "panel_day_engine_precursor_abrupt_consistency_summary_v1.csv",
        [
            {
                "overlap_panel_count": 2,
                "same_event_count": 2,
                "corrected_pure_abrupt_fault_count": 4,
            }
        ],
        ["overlap_panel_count", "same_event_count", "corrected_pure_abrupt_fault_count"],
    )

    write_csv(
        share / "panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv",
        [
            {
                "recommended_next_handling": "relabel_overlap_as_precursor_led_faults",
                "rationale_ko": "fixture same-event overlap",
            }
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
                "현재_패널표_사건유형_ko": "급작 고장",
                "현재_패널표_커널로그증상명_ko": "전압 변화형",
                "현재_패널표_커널로그원인군_ko": "개방/장치이상형",
                "현재_패널표_GPVS참고유형_ko": "개방/장치이상 계열",
                "전조흔적_시작일": "2025-01-20",
                "강한트리거일": "2025-03-21",
                "선행기간_일": 60,
                "사건시간양상_판정_ko": "전조흔적있음_순수급작보류",
                "확정도_판정_ko": "보류",
                "현재표_보정필요여부_flag": 1,
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
            "전조흔적_시작일",
            "강한트리거일",
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
                "site": "sitea",
                "panel_id": "p1",
                "현재표_사건유형_ko": "전조형 고장",
                "현재표_최종고장양상_ko": "진행성 악화",
                "전조흔적_flag": 1,
                "순수급작_flag": 0,
                "전조평가셋편입_flag": 1,
                "급작평가셋편입_flag": 0,
                "사건유형_재판정_ko": "전조형 고장",
                "최종고장양상_재판정_ko": "진행성 악화",
                "재판정_근거_ko": "fault panel event audit explicit stored-field rule",
            },
            {
                "site": "sitea",
                "panel_id": "p2",
                "현재표_사건유형_ko": "급작 고장",
                "현재표_최종고장양상_ko": "급작 발생",
                "전조흔적_flag": 0,
                "순수급작_flag": 1,
                "전조평가셋편입_flag": 0,
                "급작평가셋편입_flag": 1,
                "사건유형_재판정_ko": "급작 고장",
                "최종고장양상_재판정_ko": "급작 발생",
                "재판정_근거_ko": "fault panel event audit explicit stored-field rule",
            },
            {
                "site": "sitea",
                "panel_id": "p3",
                "현재표_사건유형_ko": "급작 고장",
                "현재표_최종고장양상_ko": "급작 발생",
                "전조흔적_flag": 0,
                "순수급작_flag": 1,
                "전조평가셋편입_flag": 0,
                "급작평가셋편입_flag": 1,
                "사건유형_재판정_ko": "급작 고장",
                "최종고장양상_재판정_ko": "급작 발생",
                "재판정_근거_ko": "fault panel event audit explicit stored-field rule",
                "현재표_보정필요여부_flag": 0,
            },
            {
                "site": "siteb",
                "panel_id": "p4",
                "현재표_사건유형_ko": "급작 고장",
                "현재표_최종고장양상_ko": "급작 발생",
                "전조흔적_flag": 0,
                "순수급작_flag": 1,
                "전조평가셋편입_flag": 0,
                "급작평가셋편입_flag": 1,
                "사건유형_재판정_ko": "급작 고장",
                "최종고장양상_재판정_ko": "급작 발생",
                "재판정_근거_ko": "fault panel event audit explicit stored-field rule",
                "현재표_보정필요여부_flag": 0,
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
                "재판정_근거_ko": "explicit stored-field rule; interpretation precursor-led but both eval sets excluded",
                "현재표_보정필요여부_flag": 0,
            },
            {
                "site": "siteb",
                "panel_id": "p6",
                "현재표_사건유형_ko": "전조형 고장",
                "현재표_최종고장양상_ko": "진행성 악화",
                "전조흔적_flag": 1,
                "순수급작_flag": 0,
                "전조평가셋편입_flag": 1,
                "급작평가셋편입_flag": 0,
                "사건유형_재판정_ko": "전조형 고장",
                "최종고장양상_재판정_ko": "진행성 악화",
                "재판정_근거_ko": "fault panel event audit explicit stored-field rule",
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

    (root / "data" / "gpvs" / "out").mkdir(parents=True, exist_ok=True)
    write_csv(
        root / "data" / "gpvs" / "out" / "EXTERNAL_GPVS_BYTYPE_METRICS.csv",
        [
            {"fault_type": "F1L", "sid": 1, "score": "dtw_like", "auc": 0.61, "ap": 0.59, "precision_fpr1": 0.81, "recall_fpr1": 0.04, "f1_fpr1": 0.08, "detect_rate_post": 1.0},
            {"fault_type": "F1M", "sid": 1, "score": "dtw_like", "auc": 0.91, "ap": 0.94, "precision_fpr1": 0.99, "recall_fpr1": 0.80, "f1_fpr1": 0.88, "detect_rate_post": 1.0},
            {"fault_type": "F2L", "sid": 2, "score": "level_drop_like", "auc": 0.57, "ap": 0.54, "precision_fpr1": 0.69, "recall_fpr1": 0.02, "f1_fpr1": 0.04, "detect_rate_post": 0.8},
            {"fault_type": "F2M", "sid": 2, "score": "ae_like", "auc": 0.51, "ap": 0.51, "precision_fpr1": 0.50, "recall_fpr1": 0.01, "f1_fpr1": 0.02, "detect_rate_post": 0.7},
            {"fault_type": "F3L", "sid": 3, "score": "ae_like", "auc": 0.57, "ap": 0.62, "precision_fpr1": 0.92, "recall_fpr1": 0.11, "f1_fpr1": 0.20, "detect_rate_post": 0.9},
            {"fault_type": "F3M", "sid": 3, "score": "dtw_like", "auc": 0.57, "ap": 0.56, "precision_fpr1": 0.80, "recall_fpr1": 0.03, "f1_fpr1": 0.06, "detect_rate_post": 0.8},
            {"fault_type": "F4L", "sid": 4, "score": "dtw_like", "auc": 0.54, "ap": 0.52, "precision_fpr1": 0.62, "recall_fpr1": 0.01, "f1_fpr1": 0.03, "detect_rate_post": 0.6},
            {"fault_type": "F4M", "sid": 4, "score": "ae_like", "auc": 0.53, "ap": 0.53, "precision_fpr1": 0.62, "recall_fpr1": 0.01, "f1_fpr1": 0.03, "detect_rate_post": 0.6},
            {"fault_type": "F5L", "sid": 5, "score": "dtw_like", "auc": 0.97, "ap": 0.93, "precision_fpr1": 0.95, "recall_fpr1": 0.04, "f1_fpr1": 0.08, "detect_rate_post": 1.0},
            {"fault_type": "F5M", "sid": 5, "score": "hs_like", "auc": 0.52, "ap": 0.51, "precision_fpr1": 0.52, "recall_fpr1": 0.01, "f1_fpr1": 0.02, "detect_rate_post": 0.5},
            {"fault_type": "F6L", "sid": 6, "score": "hs_like", "auc": 0.52, "ap": 0.52, "precision_fpr1": 0.50, "recall_fpr1": 0.01, "f1_fpr1": 0.02, "detect_rate_post": 0.5},
            {"fault_type": "F6M", "sid": 6, "score": "ae_like", "auc": 0.50, "ap": 0.49, "precision_fpr1": 0.45, "recall_fpr1": 0.01, "f1_fpr1": 0.01, "detect_rate_post": 0.4},
            {"fault_type": "F7L", "sid": 7, "score": "dtw_like", "auc": 0.54, "ap": 0.53, "precision_fpr1": 0.55, "recall_fpr1": 0.02, "f1_fpr1": 0.03, "detect_rate_post": 0.7},
            {"fault_type": "F7M", "sid": 7, "score": "ae_like", "auc": 0.55, "ap": 0.55, "precision_fpr1": 0.60, "recall_fpr1": 0.02, "f1_fpr1": 0.03, "detect_rate_post": 0.8},
        ],
        ["fault_type", "sid", "score", "auc", "ap", "precision_fpr1", "recall_fpr1", "f1_fpr1", "detect_rate_post"],
    )

    write_csv(
        share / "panel_day_engine_project_current_data_freeze_pack_v1.csv",
        [
            {
                "eval_scope": "step1_taxonomy",
                "current_data_decision": "freeze_with_caution",
                "freeze_reason_ko": "step1 structural only",
            },
            {
                "eval_scope": "step2_onset_truth",
                "current_data_decision": "freeze_with_caution",
                "freeze_reason_ko": "step2 structural only",
            },
            {
                "eval_scope": "step3_precursor_performance",
                "current_data_decision": "exploratory_only",
                "freeze_reason_ko": "step3 exploratory",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "current_data_decision": "freeze_with_caution",
                "freeze_reason_ko": "step4 abrupt bounded",
            },
            {
                "eval_scope": "step4_common_cause_routing",
                "current_data_decision": "exploratory_only",
                "freeze_reason_ko": "step4 common exploratory",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "current_data_decision": "workflow_proxy_only",
                "freeze_reason_ko": "workflow only",
            },
        ],
        ["eval_scope", "current_data_decision", "freeze_reason_ko"],
    )

    write_csv(
        share / "panel_day_engine_operator_attention_policy_recommendation_v1.csv",
        [
            {
                "recommended_policy_name": "baseline_plus_discovery_cluster",
                "recommended_policy_reason_ko": "cluster workflow chosen",
            }
        ],
        ["recommended_policy_name", "recommended_policy_reason_ko"],
    )

    write_csv(
        share / "panel_day_engine_operator_pipeline_manifest_v1.csv",
        [
            {
                "final_pipeline_pass_flag": 1,
                "note_ko": "pipeline ok",
            }
        ],
        ["final_pipeline_pass_flag", "note_ko"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research" / "prognostics" / "build_panel_day_engine_internal_share_appendix_v1.py"
    smoke_script = repo_root / "research" / "prognostics" / "smoke_test_panel_day_engine_internal_share_appendix_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        repo_root / "_share" / "panel_day_engine_abrupt6_symptom_map_v1.csv",
        repo_root / "_share" / "panel_day_engine_kernellog_project_mapping_v1.csv",
        repo_root / "_share" / "panel_day_engine_gpv7_perf_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_project_progress_snapshot_v1.csv",
    ]
    before_digests = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="tmp_internal_share_appendix_v1_") as tmp_dir:
        temp_root = Path(tmp_dir)
        build_fixture(temp_root)

        for forbidden in [
            temp_root / "_share" / "panel_day_engine_ae_dtw_case_review_v1.csv",
            temp_root / "_share" / "panel_day_engine_ae_dtw_case_episode_review_v1.csv",
            temp_root / "_share" / "panel_day_engine_ae_dtw_output_normal_candidates_v1.csv",
        ]:
            assert_true(not forbidden.exists(), f"fixture unexpectedly includes seed-panel output: {forbidden.name}")

        result = run([sys.executable, str(build_script), "--root", str(temp_root)], repo_root)
        assert_true(result.returncode == 0, f"appendix build failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        abrupt_df = pd.read_csv(
            temp_root / "_share" / "panel_day_engine_abrupt6_symptom_map_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )
        mapping_df = pd.read_csv(
            temp_root / "_share" / "panel_day_engine_kernellog_project_mapping_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )
        gpv_df = pd.read_csv(
            temp_root / "_share" / "panel_day_engine_gpv7_perf_summary_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )
        progress_df = pd.read_csv(
            temp_root / "_share" / "panel_day_engine_project_progress_snapshot_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )

        assert_true(len(abrupt_df) == 6, f"abrupt6 row count mismatch: {len(abrupt_df)}")
        symptom_lookup = dict(zip(abrupt_df["panel_id"], abrupt_df["증상명_ko"]))
        assert_true(symptom_lookup["p1"] == "다이오드형", "p1 should map to 다이오드형")
        assert_true(symptom_lookup["p2"] == "다이오드형", "p2 should map to 다이오드형")
        assert_true(symptom_lookup["p3"] == "다이오드형", "p3 should map to 다이오드형")
        assert_true(symptom_lookup["p4"] == "다이오드형", "p4 should map to 다이오드형")
        assert_true(symptom_lookup[FORENSIC_HOLDOUT_PANEL_ID] == "개방/장치이상형", "holdout panel should map to 개방/장치이상형")
        assert_true(symptom_lookup["p6"] == "모듈손상형", "p6 should map to 모듈손상형")
        event_lookup = dict(zip(abrupt_df["panel_id"], abrupt_df["사건유형_ko"]))
        terminal_lookup = dict(zip(abrupt_df["panel_id"], abrupt_df["최종고장양상_ko"]))
        pure_abrupt_lookup = dict(zip(abrupt_df["panel_id"], abrupt_df["순수급작_flag"]))
        caution_lookup = dict(zip(abrupt_df["panel_id"], abrupt_df["사건유형_판정주의_ko"]))
        assert_true(event_lookup["p1"] == "전조형 고장", "p1 should be reconciled as precursor-led fault")
        assert_true(event_lookup["p6"] == "전조형 고장", "p6 should be reconciled as precursor-led fault")
        assert_true(event_lookup[FORENSIC_HOLDOUT_PANEL_ID] == "전조형 고장", "c429 row should now be interpreted as precursor-led fault")
        assert_true(terminal_lookup["p1"] == "진행성 악화", "p1 terminal pattern should be progressive worsening")
        assert_true(terminal_lookup["p6"] == "진행성 악화", "p6 terminal pattern should be progressive worsening")
        assert_true(terminal_lookup[FORENSIC_HOLDOUT_PANEL_ID] == "급격 종료", "c429 terminal pattern should be abrupt ending")
        assert_true(int(pure_abrupt_lookup["p1"]) == 0, "p1 should not stay pure abrupt")
        assert_true(int(pure_abrupt_lookup["p6"]) == 0, "p6 should not stay pure abrupt")
        assert_true(int(pure_abrupt_lookup[FORENSIC_HOLDOUT_PANEL_ID]) == 0, "c429 should not stay pure abrupt")
        assert_true(
            "전조형 고장" in caution_lookup[FORENSIC_HOLDOUT_PANEL_ID] or "explicit" in caution_lookup[FORENSIC_HOLDOUT_PANEL_ID],
            "c429 caution text should come from fault-event audit reasoning",
        )
        assert_true(int(pd.to_numeric(abrupt_df["순수급작_flag"]).sum()) == 3, "pure abrupt count should be 3")
        assert_true(
            abrupt_df["증상명_ko"].value_counts().to_dict() == {
                "다이오드형": 4,
                "개방/장치이상형": 1,
                "모듈손상형": 1,
            },
            "abrupt6 family composition should be 4/1/1",
        )
        assert_true(
            not abrupt_df["panel_id"].isin(BANNED_PANEL_IDS).any(),
            "banned panel ids should be excluded from abrupt6 output",
        )
        assert_true(
            abrupt_df["비고_ko"].astype(str).str.contains("selection_rule=strict_abrupt_evidence_plus_truth_backfill").all(),
            "synthetic abrupt selection should use strict_abrupt_evidence_plus_truth_backfill",
        )
        assert_true(
            abrupt_df["비고_ko"].astype(str).str.contains("selection_source=reaudit_accepted_truth_backfill").any(),
            "synthetic abrupt selection should backfill accepted truth rows",
        )
        abrupt_note_text = " ".join(abrupt_df["비고_ko"].astype(str).tolist())
        assert_true("candidate_validity=false_positive" not in abrupt_note_text, "false_positive rows should be excluded")
        assert_true("vendor_reply_class=vendor_rejected" not in abrupt_note_text, "vendor_rejected rows should be excluded")
        assert_true(
            abrupt_df["비고_ko"].astype(str).str.contains("family_composition_check=ok").all(),
            "family composition check should be confirmed in synthetic fixture",
        )

        assert_true(
            set(mapping_df["커널로그_증상명"]) == {"출력 저하형", "전압 변화형", "패턴 이상형", "불안정형", "복합형"},
            "kernel mapping rows mismatch",
        )

        number_values = {str(value) for value in gpv_df["고장유형_번호"].tolist()}
        assert_true({"1", "2", "3", "4", "5", "6", "7"} <= number_values, "gpv summary rows missing")
        fallback_rows = gpv_df.loc[gpv_df["고장유형_번호"].astype(str).isin([str(i) for i in range(1, 8)])]
        assert_true(
            fallback_rows["성능요약_ko"].str.contains("representative row").all(),
            "gpv parser should use actual by-type representative rows",
        )
        assert_true(
            fallback_rows["source_ref_ko"].str.contains("EXTERNAL_GPVS_BYTYPE_METRICS.csv").all(),
            "gpv source_ref should mention by-type metrics file",
        )
        assert_true(
            fallback_rows["수치_ko"].str.contains("auc=").all() and fallback_rows["수치_ko"].str.contains("ap=").all(),
            "gpv numeric summary should include actual auc/ap values",
        )

        assert_true(len(progress_df) == 3, f"progress snapshot row count mismatch: {len(progress_df)}")
        assert_true(
            set(progress_df["항목"]) == {"연구/알고리즘 큰 줄기", "운영 스택", "내부 공유/정리 문서"},
            "progress snapshot item mismatch",
        )
        progress_lookup = dict(zip(progress_df["항목"], progress_df["현재_완료율_추정"]))
        assert_true(progress_lookup["연구/알고리즘 큰 줄기"] == 85, "research progress should remain 85")
        assert_true(progress_lookup["운영 스택"] == 95, "operator stack progress should remain 95")
        assert_true(progress_lookup["내부 공유/정리 문서"] == 70, "internal-share progress should now be 70")

        for forbidden in [
            temp_root / "_share" / "panel_day_engine_ae_dtw_case_review_v1.csv",
            temp_root / "_share" / "panel_day_engine_ae_dtw_case_episode_review_v1.csv",
            temp_root / "_share" / "panel_day_engine_ae_dtw_output_normal_candidates_v1.csv",
        ]:
            assert_true(not forbidden.exists(), f"seed-panel output should not be read or created: {forbidden.name}")

    with tempfile.TemporaryDirectory(prefix="tmp_internal_share_appendix_v1_guardrail_") as tmp_dir:
        broken_root = Path(tmp_dir)
        build_fixture(broken_root, omit_reaudit_panel_ids={"p6"})
        abrupt_output_path = broken_root / "_share" / "panel_day_engine_abrupt6_symptom_map_v1.csv"
        abrupt_output_path.write_text("sentinel", encoding="utf-8")
        sentinel_digest = file_digest(abrupt_output_path)

        broken_result = run([sys.executable, str(build_script), "--root", str(broken_root)], repo_root)
        assert_true(broken_result.returncode != 0, "builder should fail when abrupt positive universe cannot recover 6 rows")
        combined_error = f"{broken_result.stdout}\n{broken_result.stderr}"
        assert_true(
            "exactly 6 rows" in combined_error,
            "builder should fail clearly when abrupt positive universe is not 6 rows",
        )
        assert_true(
            file_digest(abrupt_output_path) == sentinel_digest,
            "stale-output protection failed: abrupt output was overwritten on failure",
        )

    after_digests = {path: file_digest(path) for path in official_outputs}
    assert_true(before_digests == after_digests, "smoke test modified official appendix outputs")

    print("[OK] appendix scripts compile")
    print("[OK] abrupt6 symptom map emitted with expected row count")
    print("[OK] false_positive/vendor_rejected abrupt rows and banned panel ids are excluded")
    print("[OK] stale-output protection works when abrupt positive universe cannot recover 6 rows")
    print("[OK] fixed kernel mapping rows emitted")
    print("[OK] GPV by-type parser uses actual stored metrics when present")
    print("[OK] progress snapshot rows emitted")
    print("[OK] seed-panel outputs are not read or required")
    print("[OK] official outputs unchanged")


if __name__ == "__main__":
    main()
