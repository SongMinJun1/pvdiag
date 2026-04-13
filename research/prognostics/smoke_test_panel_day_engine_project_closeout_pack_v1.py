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


def build_fixture(root: Path) -> None:
    share = root / "_share"
    share.mkdir(parents=True, exist_ok=True)

    write_csv(
        share / "panel_day_engine_project_final_decision_pack_v1.csv",
        [
            {
                "eval_scope": "step1_taxonomy",
                "current_data_decision": "freeze_with_caution",
                "allowed_claim_strength": "bounded_current_data_claim",
                "current_best_target_name": "coverage_only",
                "current_best_metric_kind": "structural_coverage_metric",
                "current_best_f1": "",
                "current_best_positive_support": 3,
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "final_usage_decision": "bounded_reporting_use",
                "final_reason_ko": "step1 structural only",
            },
            {
                "eval_scope": "step2_onset_truth",
                "current_data_decision": "freeze_with_caution",
                "allowed_claim_strength": "bounded_current_data_claim",
                "current_best_target_name": "coverage_only",
                "current_best_metric_kind": "structural_coverage_metric",
                "current_best_f1": "",
                "current_best_positive_support": 2,
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "final_usage_decision": "bounded_reporting_use",
                "final_reason_ko": "step2 structural reference",
            },
            {
                "eval_scope": "step3_precursor_performance",
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "current_best_target_name": "first_signalcount2",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 1.0,
                "current_best_positive_support": 3,
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "final_usage_decision": "exploratory_only",
                "final_reason_ko": "benchmark reset precursor benchmark support 3, c429 included, exploratory only",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "current_best_target_name": "final_fault_hit_by_anchor",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 0.6666666666666666,
                "current_best_positive_support": 3,
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "final_usage_decision": "exploratory_only",
                "final_reason_ko": "benchmark reset 이후 precursor benchmark support 3, pure abrupt benchmark support 3이다. c42997 row는 전조형 고장/급격 종료로 해석되며 precursor benchmark에 포함되고 pure abrupt benchmark에서는 제외된다.",
            },
            {
                "eval_scope": "step4_common_cause_routing",
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "current_best_target_name": "breadth_marker_only",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 1.0,
                "current_best_positive_support": 4,
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "final_usage_decision": "exploratory_only",
                "final_reason_ko": "step4 common exploratory only",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "current_data_decision": "workflow_proxy_only",
                "allowed_claim_strength": "workflow_claim_only",
                "current_best_target_name": "baseline_plus_discovery_narrow",
                "current_best_metric_kind": "retrospective_proxy_metric",
                "current_best_f1": 0.55,
                "current_best_positive_support": 11,
                "chosen_operational_workflow_name": "baseline_plus_discovery_cluster",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "final_usage_decision": "workflow_only",
                "final_reason_ko": "operator workflow only",
            },
        ],
        [
            "eval_scope",
            "current_data_decision",
            "allowed_claim_strength",
            "current_best_target_name",
            "current_best_metric_kind",
            "current_best_f1",
            "current_best_positive_support",
            "chosen_operational_workflow_name",
            "release_gate_pass_flag",
            "pipeline_pass_flag",
            "final_usage_decision",
            "final_reason_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_project_final_decision_summary_v1.csv",
        [
            {
                "final_usage_decision": "operational_default",
                "scope_count": 0,
                "operational_default_count": 0,
                "bounded_reporting_use_count": 0,
                "exploratory_only_count": 0,
                "workflow_only_count": 0,
                "release_gate_pass_flag": 1,
                "chosen_operational_workflow_name": "baseline_plus_discovery_cluster",
                "note_ko": "none",
            },
            {
                "final_usage_decision": "bounded_reporting_use",
                "scope_count": 2,
                "operational_default_count": 0,
                "bounded_reporting_use_count": 2,
                "exploratory_only_count": 0,
                "workflow_only_count": 0,
                "release_gate_pass_flag": 1,
                "chosen_operational_workflow_name": "baseline_plus_discovery_cluster",
                "note_ko": "bounded use",
            },
            {
                "final_usage_decision": "exploratory_only",
                "scope_count": 3,
                "operational_default_count": 0,
                "bounded_reporting_use_count": 0,
                "exploratory_only_count": 3,
                "workflow_only_count": 0,
                "release_gate_pass_flag": 1,
                "chosen_operational_workflow_name": "baseline_plus_discovery_cluster",
                "note_ko": "exploratory",
            },
            {
                "final_usage_decision": "workflow_only",
                "scope_count": 1,
                "operational_default_count": 0,
                "bounded_reporting_use_count": 0,
                "exploratory_only_count": 0,
                "workflow_only_count": 1,
                "release_gate_pass_flag": 1,
                "chosen_operational_workflow_name": "baseline_plus_discovery_cluster",
                "note_ko": "workflow only",
            },
        ],
        [
            "final_usage_decision",
            "scope_count",
            "operational_default_count",
            "bounded_reporting_use_count",
            "exploratory_only_count",
            "workflow_only_count",
            "release_gate_pass_flag",
            "chosen_operational_workflow_name",
            "note_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_project_final_do_and_dont_v1.csv",
        [
            {
                "row_id": "do_01_project_limit",
                "scope_or_topic": "project_current_data_limit",
                "do_text_ko": "모든 보고/발표/핸드오프에서 현재는 추가 fault case 수집이 불가능하다는 hard constraint 를 먼저 명시한다.",
                "dont_text_ko": "새 truth 없이 exploratory 또는 caution scope를 frozen default 결론으로 승격하지 말 것.",
                "claim_strength": "bounded_current_data_claim",
                "priority_order": 1,
            },
            {
                "row_id": "do_04_step3",
                "scope_or_topic": "step3_precursor_performance",
                "do_text_ko": "step3 precursor 결과는 exploratory result 로만 쓴다.",
                "dont_text_ko": "step3 precursor 결과를 stable detector performance 로 말하지 않는다.",
                "claim_strength": "exploratory_claim_only",
                "priority_order": 4,
            },
        ],
        ["row_id", "scope_or_topic", "do_text_ko", "dont_text_ko", "claim_strength", "priority_order"],
    )

    write_csv(
        share / "panel_day_engine_project_handoff_summary_v1.csv",
        [
            {
                "eval_scope": "step1_taxonomy",
                "current_data_decision": "freeze_with_caution",
                "final_usage_decision": "bounded_reporting_use",
                "allowed_claim_strength": "bounded_current_data_claim",
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "handoff_status_ko": "주의해서 사용",
            },
            {
                "eval_scope": "step2_onset_truth",
                "current_data_decision": "freeze_with_caution",
                "final_usage_decision": "bounded_reporting_use",
                "allowed_claim_strength": "bounded_current_data_claim",
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "handoff_status_ko": "주의해서 사용",
            },
            {
                "eval_scope": "step3_precursor_performance",
                "current_data_decision": "exploratory_only",
                "final_usage_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "handoff_status_ko": "탐색용으로만 유지",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "current_data_decision": "exploratory_only",
                "final_usage_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "handoff_status_ko": "탐색용으로만 유지",
            },
            {
                "eval_scope": "step4_common_cause_routing",
                "current_data_decision": "exploratory_only",
                "final_usage_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "handoff_status_ko": "탐색용으로만 유지",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "current_data_decision": "workflow_proxy_only",
                "final_usage_decision": "workflow_only",
                "allowed_claim_strength": "workflow_claim_only",
                "chosen_operational_workflow_name": "baseline_plus_discovery_cluster",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "handoff_status_ko": "운영 workflow 용",
            },
        ],
        [
            "eval_scope",
            "current_data_decision",
            "final_usage_decision",
            "allowed_claim_strength",
            "chosen_operational_workflow_name",
            "release_gate_pass_flag",
            "pipeline_pass_flag",
            "handoff_status_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_project_current_data_freeze_pack_v1.csv",
        [
            {
                "eval_scope": "step1_taxonomy",
                "current_best_target_name": "coverage_only",
                "current_best_metric_kind": "structural_coverage_metric",
                "current_best_f1": "",
                "current_best_positive_support": 3,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "freeze_with_caution",
                "acquisition_blocked_flag": 0,
                "current_data_decision": "freeze_with_caution",
                "allowed_claim_strength": "bounded_current_data_claim",
                "next_allowed_action": "keep_with_caution_note",
                "freeze_reason_ko": "step1 structural only",
            },
            {
                "eval_scope": "step2_onset_truth",
                "current_best_target_name": "coverage_only",
                "current_best_metric_kind": "structural_coverage_metric",
                "current_best_f1": "",
                "current_best_positive_support": 2,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "freeze_with_caution",
                "acquisition_blocked_flag": 0,
                "current_data_decision": "freeze_with_caution",
                "allowed_claim_strength": "bounded_current_data_claim",
                "next_allowed_action": "keep_with_caution_note",
                "freeze_reason_ko": "step2 structural only",
            },
            {
                "eval_scope": "step3_precursor_performance",
                "current_best_target_name": "first_signalcount2",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 1.0,
                "current_best_positive_support": 3,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "do_not_freeze",
                "acquisition_blocked_flag": 1,
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "next_allowed_action": "do_not_upgrade_without_new_truth",
                "freeze_reason_ko": "benchmark reset precursor support 3 and c429 included",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "current_best_target_name": "final_fault_hit_by_anchor",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 0.6666666666666666,
                "current_best_positive_support": 3,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "do_not_freeze",
                "acquisition_blocked_flag": 1,
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "next_allowed_action": "do_not_upgrade_without_new_truth",
                "freeze_reason_ko": "benchmark reset 이후 precursor benchmark 3과 분리된 순수 급작 benchmark 3만을 positive로 읽어야 한다. c42997 row는 precursor benchmark에 포함되고 pure abrupt benchmark에서는 제외한다.",
            },
            {
                "eval_scope": "step4_common_cause_routing",
                "current_best_target_name": "breadth_marker_only",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 1.0,
                "current_best_positive_support": 4,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "do_not_freeze",
                "acquisition_blocked_flag": 1,
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "next_allowed_action": "do_not_upgrade_without_new_truth",
                "freeze_reason_ko": "step4 common exploratory",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "current_best_target_name": "baseline_plus_discovery_narrow",
                "current_best_metric_kind": "retrospective_proxy_metric",
                "current_best_f1": 0.55,
                "current_best_positive_support": 11,
                "current_operational_workflow_name": "baseline_plus_discovery_cluster",
                "current_operational_workflow_reason_ko": "workflow choice",
                "freeze_recommendation": "freeze_with_caution",
                "acquisition_blocked_flag": 0,
                "current_data_decision": "workflow_proxy_only",
                "allowed_claim_strength": "workflow_claim_only",
                "next_allowed_action": "operator_workflow_only",
                "freeze_reason_ko": "workflow only",
            },
        ],
        [
            "eval_scope",
            "current_best_target_name",
            "current_best_metric_kind",
            "current_best_f1",
            "current_best_positive_support",
            "current_operational_workflow_name",
            "current_operational_workflow_reason_ko",
            "freeze_recommendation",
            "acquisition_blocked_flag",
            "current_data_decision",
            "allowed_claim_strength",
            "next_allowed_action",
            "freeze_reason_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_internal_share_clean_summary_v1.csv",
        [
            {"섹션": "최신 성능", "항목": "전조형 고장", "값_ko": "대표기준=first_signalcount2", "비고_ko": "탐색적"},
            {"섹션": "급작 고장 6건", "항목": "건수", "값_ko": "6건", "비고_ko": "stored abrupt positives"},
            {"섹션": "커널로그-프로젝트 매핑", "항목": "요약", "값_ko": "증상축 vs 사건축", "비고_ko": "mapping only"},
            {"섹션": "GPV 7종", "항목": "요약", "값_ko": "stored by-type metric", "비고_ko": "reference axis"},
            {"섹션": "진행률", "항목": "연구/알고리즘 큰 줄기", "값_ko": "85", "비고_ko": "mainline mostly done"},
        ],
        ["섹션", "항목", "값_ko", "비고_ko"],
    )

    abrupt_rows = []
    for idx in range(6):
        is_overlap = idx in {4, 5}
        abrupt_rows.append(
            {
                "site": "conalog" if idx == 3 else "siteA",
                "panel_id": FORENSIC_HOLDOUT_PANEL_ID if idx == 3 else f"panel.{idx}",
                "고장시점": "2025-03-21" if idx == 3 else f"2025-01-0{idx+1}",
                "사건유형_ko": "전조형 고장" if idx in {3, 4, 5} else "급작 고장",
                "최종고장양상_ko": "급격 종료" if idx == 3 else ("진행성 악화" if is_overlap else "급작 발생"),
                "순수급작_flag": 0 if idx in {3, 4, 5} else 1,
                "증상명_ko": "개방/장치이상형" if idx in {3, 4} else ("다이오드형" if idx < 3 else "모듈손상형"),
                "세부근거_ko": "stored truth mapping",
                "source_field_ko": "vendor_fault_family",
                "비고_ko": "fixture",
            }
        )
    write_csv(
        share / "panel_day_engine_abrupt6_symptom_map_v1.csv",
        abrupt_rows,
        ["site", "panel_id", "고장시점", "사건유형_ko", "최종고장양상_ko", "순수급작_flag", "증상명_ko", "세부근거_ko", "source_field_ko", "비고_ko"],
    )

    write_csv(
        share / "panel_day_engine_kernellog_project_mapping_v1.csv",
        [
            {
                "커널로그_증상명": "출력 저하형",
                "주_프로젝트분류": "전조형 고장",
                "보조_프로젝트분류": "급작 고장",
                "설명_ko": "symptom axis",
                "주의_ko": "do not overclaim",
            },
            {
                "커널로그_증상명": "전압 변화형",
                "주_프로젝트분류": "급작 고장",
                "보조_프로젝트분류": "전조형 고장",
                "설명_ko": "symptom axis",
                "주의_ko": "do not overclaim",
            },
            {
                "커널로그_증상명": "패턴 이상형",
                "주_프로젝트분류": "같이 흔들리는 이상",
                "보조_프로젝트분류": "오경보",
                "설명_ko": "symptom axis",
                "주의_ko": "do not overclaim",
            },
            {
                "커널로그_증상명": "불안정형",
                "주_프로젝트분류": "반복 이상",
                "보조_프로젝트분류": "오경보",
                "설명_ko": "symptom axis",
                "주의_ko": "do not overclaim",
            },
            {
                "커널로그_증상명": "복합형",
                "주_프로젝트분류": "급작 고장",
                "보조_프로젝트분류": "같이 흔들리는 이상",
                "설명_ko": "symptom axis",
                "주의_ko": "do not overclaim",
            },
        ],
        ["커널로그_증상명", "주_프로젝트분류", "보조_프로젝트분류", "설명_ko", "주의_ko"],
    )

    gpv_rows = []
    for idx in range(1, 8):
        gpv_rows.append(
            {
                "고장유형_번호": idx,
                "고장유형_설명_ko": f"GPVS Fault{idx}",
                "성능요약_ko": "stored by-type metric",
                "수치_ko": f"auc=0.{idx}000, ap=0.{idx}100, f1_fpr1=0.{idx}200",
                "source_ref_ko": "data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv",
            }
        )
    write_csv(
        share / "panel_day_engine_gpv7_perf_summary_v1.csv",
        gpv_rows,
        ["고장유형_번호", "고장유형_설명_ko", "성능요약_ko", "수치_ko", "source_ref_ko"],
    )

    write_csv(
        share / "panel_day_engine_project_progress_snapshot_v1.csv",
        [
            {"항목": "연구/알고리즘 큰 줄기", "현재_완료율_추정": 85, "현재_상태_ko": "mainline mostly done", "근거_ko": "step3 and common remain exploratory"},
            {"항목": "운영 스택", "현재_완료율_추정": 95, "현재_상태_ko": "operator stack essentially complete", "근거_ko": "release/pipeline pass"},
            {"항목": "내부 공유/정리 문서", "현재_완료율_추정": 70, "현재_상태_ko": "docs improved", "근거_ko": "appendix and clean pack complete"},
        ],
        ["항목", "현재_완료율_추정", "현재_상태_ko", "근거_ko"],
    )

    write_csv(
        share / "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": FORENSIC_HOLDOUT_PANEL_ID,
                "대표판정_ko": "전조형 고장",
                "사건이력_ko": "전조형 고장(급격 종료)",
                "운영최초전조발견일": "2025-02-20",
                "운영최초전조마커": "first_cond_evt",
                "사건해석상전조시작일": "2025-01-20",
                "benchmark전조시작일": "2025-03-18",
                "전조형이력_flag": 1,
                "급작고장이력_flag": 0,
                "공통원인이력_flag": 0,
                "반복이상이력_flag": 0,
                "패널고장여부_ko": "고장",
                "커널로그_증상명_ko": "전압 변화형",
                "커널로그_원인군_ko": "개방/장치이상형",
                "GPVS_참고유형_ko": "전기적 고장 계열",
                "GPVS_근거_ko": "_share/gpvs_fault_family_eval_cases.csv | site+panel_id | fixture",
                "운영위치_ko": "현재 workflow 미포함",
                "판정주의_ko": "fixture",
            }
        ],
        [
            "site",
            "panel_id",
            "대표판정_ko",
            "사건이력_ko",
            "운영최초전조발견일",
            "운영최초전조마커",
            "사건해석상전조시작일",
            "benchmark전조시작일",
            "전조형이력_flag",
            "급작고장이력_flag",
            "공통원인이력_flag",
            "반복이상이력_flag",
            "패널고장여부_ko",
            "커널로그_증상명_ko",
            "커널로그_원인군_ko",
            "GPVS_참고유형_ko",
            "GPVS_근거_ko",
            "운영위치_ko",
            "판정주의_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_panel_multiaxis_event_supplement_v1.csv",
        [
            {
                "site": "siteA",
                "panel_id": "panel.0",
                "사건유형_ko": "전조형 고장",
                "사건우선순위": 2,
                "대표판정여부_flag": 1,
                "운영위치_ko": "현재 workflow 미포함",
                "비고_ko": "fixture",
            },
        ],
        ["site", "panel_id", "사건유형_ko", "사건우선순위", "대표판정여부_flag", "운영위치_ko", "비고_ko"],
    )

    write_csv(
        share / "panel_day_engine_panel_multiaxis_cluster_supplement_v1.csv",
        [
            {
                "site": "siteCC",
                "cluster_id": "cluster.1",
                "대표판정_ko": "공통원인 이벤트",
                "커널로그_증상명_ko": "패턴 이상형",
                "GPVS_참고유형_ko": "미부착",
                "GPVS_근거_ko": "현재 저장 산출물에는 패널별 GPVS 직접 판정이 없음",
                "운영위치_ko": "추가 발견 후보",
                "판정주의_ko": "fixture",
            }
        ],
        ["site", "cluster_id", "대표판정_ko", "커널로그_증상명_ko", "GPVS_참고유형_ko", "GPVS_근거_ko", "운영위치_ko", "판정주의_ko"],
    )

    write_csv(
        share / "panel_day_engine_panel_multiaxis_verdict_summary_v1.csv",
        [
            {
                "전체_패널수": 25,
                "고유_고장패널수": 6,
                "사건해석_전조형_패널수": 3,
                "사건해석_급작_패널수": 3,
                "사건해석_전조형_급격종료_패널수": 1,
                "사건해석_전조형_진행성악화_패널수": 2,
                "전조흔적_패널수": 3,
                "순수급작_패널수": 3,
                "엄격전조평가셋_패널수": 2,
                "순수급작평가셋_패널수": 3,
                "해석과평가셋불일치_패널수": 1,
                "공통원인이력_패널수": 4,
                "반복이상이력_패널수": 11,
                "대표판정_급작수": 3,
                "대표판정_전조형수": 3,
                "대표판정_공통원인수": 4,
                "대표판정_반복이상수": 10,
                "대표판정_고장유형보류수": 0,
                "대표판정_불충분수": 5,
                "고장_패널수": 6,
                "비고장_패널수": 4,
                "미확정_패널수": 15,
                "커널로그_증상명_부착수": 20,
                "커널로그_원인군_부착수": 6,
                "GPVS_적용대상_패널수": 6,
                "GPVS_부착수": 6,
                "GPVS_미부착수": 0,
                "GPVS_비대상수": 19,
                "사건보조행수": 23,
                "클러스터_보조행수": 5,
                "note_ko": "fixture multiaxis summary",
            }
        ],
        [
            "전체_패널수",
            "고유_고장패널수",
            "사건해석_전조형_패널수",
            "사건해석_급작_패널수",
            "사건해석_전조형_급격종료_패널수",
            "사건해석_전조형_진행성악화_패널수",
            "전조흔적_패널수",
            "순수급작_패널수",
            "엄격전조평가셋_패널수",
            "순수급작평가셋_패널수",
            "해석과평가셋불일치_패널수",
            "공통원인이력_패널수",
            "반복이상이력_패널수",
            "대표판정_급작수",
            "대표판정_전조형수",
            "대표판정_공통원인수",
            "대표판정_반복이상수",
            "대표판정_고장유형보류수",
            "대표판정_불충분수",
            "고장_패널수",
            "비고장_패널수",
            "미확정_패널수",
            "커널로그_증상명_부착수",
            "커널로그_원인군_부착수",
            "GPVS_적용대상_패널수",
            "GPVS_부착수",
            "GPVS_미부착수",
            "GPVS_비대상수",
            "사건보조행수",
            "클러스터_보조행수",
            "note_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_fault_panel_event_audit_summary_v1.csv",
        [
            {
                "사건유형_재판정_전조형수": 3,
                "전조평가셋편입_패널수": 3,
                "급작평가셋편입_패널수": 3,
            }
        ],
        ["사건유형_재판정_전조형수", "전조평가셋편입_패널수", "급작평가셋편입_패널수"],
    )

    write_csv(
        share / "panel_day_engine_operator_attention_policy_recommendation_v1.csv",
        [
            {
                "recommended_policy_name": "baseline_plus_discovery_cluster",
                "recommended_policy_reason_ko": "cluster preview keeps linked proxy gain while reducing operator load.",
                "expected_use_ko": "queue/watch baseline에 discovery cluster를 side-by-side로 붙인 기본 operator workflow",
                "caution_ko": "cluster view는 drill-down이 필요할 때 panel preview를 함께 본다.",
            }
        ],
        ["recommended_policy_name", "recommended_policy_reason_ko", "expected_use_ko", "caution_ko"],
    )

    write_csv(
        share / "panel_day_engine_operator_release_gate_manifest_v1.csv",
        [
            {
                "final_release_gate_pass_flag": 1,
                "note_ko": "operator stack release gate 통과",
            }
        ],
        ["final_release_gate_pass_flag", "note_ko"],
    )

    write_csv(
        share / "panel_day_engine_operator_pipeline_manifest_v1.csv",
        [
            {
                "final_pipeline_pass_flag": 1,
                "note_ko": "전체 operator pipeline 정상",
            }
        ],
        ["final_pipeline_pass_flag", "note_ko"],
    )

    (share / "panel_day_engine_project_handoff_pack_v1.md").write_text(
        "## 1. 지금 확정해서 쓸 수 있는 것\n", encoding="utf-8-sig"
    )
    (share / "panel_day_engine_internal_share_clean_pack_v1.md").write_text(
        "## 1. 최신 성능 요약\n", encoding="utf-8-sig"
    )


def initialize_git_repo(root: Path) -> None:
    assert_true(run(["git", "init", "-b", "feature/test-closeout"], root).returncode == 0, "git init failed")
    assert_true(run(["git", "config", "user.email", "codex@example.com"], root).returncode == 0, "git email failed")
    assert_true(run(["git", "config", "user.name", "Codex"], root).returncode == 0, "git name failed")
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    assert_true(run(["git", "add", "README.md"], root).returncode == 0, "git add failed")
    assert_true(run(["git", "commit", "-m", "fixture"], root).returncode == 0, "git commit failed")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research/prognostics/build_panel_day_engine_project_closeout_pack_v1.py"
    smoke_script = repo_root / "research/prognostics/smoke_test_panel_day_engine_project_closeout_pack_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        repo_root / "_share/panel_day_engine_project_closeout_pack_v1.md",
        repo_root / "_share/panel_day_engine_project_artifact_index_v1.csv",
        repo_root / "_share/panel_day_engine_project_status_snapshot_v1.csv",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="panel_day_engine_closeout_smoke_") as tmp_dir:
        root = Path(tmp_dir)
        build_fixture(root)
        initialize_git_repo(root)

        result = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(result.returncode == 0, f"builder failed: {result.stderr or result.stdout}")

        closeout_md = root / "_share/panel_day_engine_project_closeout_pack_v1.md"
        artifact_index_csv = root / "_share/panel_day_engine_project_artifact_index_v1.csv"
        status_snapshot_csv = root / "_share/panel_day_engine_project_status_snapshot_v1.csv"

        assert_true(closeout_md.exists(), "missing closeout markdown")
        assert_true(artifact_index_csv.exists(), "missing artifact index")
        assert_true(status_snapshot_csv.exists(), "missing status snapshot")

        markdown = closeout_md.read_text(encoding="utf-8-sig")
        required_sections = [
            "## 1. 지금 확정된 결론",
            "## 2. 운영 기본값",
            "## 3. 조심해서만 말해야 하는 것",
            "## 4. 아직 탐색적으로만 남겨야 하는 것",
            "## 5. 가장 먼저 볼 산출물",
            "## 6. 프로젝트를 다시 열면 어디서 시작할지",
        ]
        for section in required_sections:
            assert_true(section in markdown, f"missing markdown section: {section}")
        assert_true("baseline_plus_discovery_cluster" in markdown, "markdown missing chosen workflow")
        assert_true("release gate 는 통과(1)" in markdown, "markdown missing release gate status")
        assert_true("pipeline 도 통과(1)" in markdown, "markdown missing pipeline status")
        assert_true("추가 fault case 수집이 불가능" in markdown, "markdown missing current data limit")
        assert_true("패널별 대표판정표가 이제 완성돼서" in markdown, "markdown missing panel multiaxis completion note")
        assert_true("우리판정 / 커널로그 판정 / GPVS 참고판정 / 운영위치" in markdown, "markdown missing panel multiaxis one-line explanation")
        assert_true("fault-family reference axis라 고장 panel 6개에만 적용" in markdown, "markdown missing GPVS scope note")
        assert_true("비고장/미확정 panel 19개는 GPVS 비대상" in markdown, "markdown missing GPVS non-target note")
        assert_true("전조형 고장이 급격 종료로 끝난 경우" in markdown, "markdown missing precursor-led abrupt-ending note")
        assert_true("c42997a6-5881-47e7-9035-7de8a2673b54.1.1 은 전조형 고장/급격 종료로 해석되며 precursor benchmark에는 포함되고 pure abrupt benchmark에서는 제외된다." in markdown, "markdown missing c429 benchmark note")
        assert_true("운영상 최초 전조 발견일은 benchmark onset 과 다를 수 있다." in markdown, "markdown missing operational-vs-benchmark onset note")
        assert_true("사건 해석용 onset, 운영 detection onset, benchmark onset 을 분리해서 읽어야 한다." in markdown, "markdown missing 3-onset split note")
        assert_true(
            "c42997a6-5881-47e7-9035-7de8a2673b54.1.1 예시: interpretive onset = 2025-01-20, operational detection = 2025-02-20, benchmark onset = 2025-03-18"
            in markdown,
            "markdown missing c429 3-date split example",
        )
        assert_true("순수 급작 사건은 현재 stored data 기준 3건" in markdown, "markdown missing pure abrupt count note")
        assert_true("benchmark reset 이후 전조형 benchmark support 는 3건이고, 순수 급작 benchmark support 는 3건이다." in markdown, "markdown missing benchmark reset support note")
        assert_true("사건 해석상 전조형 고장 패널은 3건" in markdown, "markdown missing interpreted precursor count note")
        top_read_lines = [
            "- `panel_day_engine_panel_multiaxis_verdict_v1.csv`: panel reader-facing 대표판정을 가장 먼저 본다.",
            "- `panel_day_engine_project_final_decision_pack_v1.csv`: scope별 최종 usage decision 을 바로 이어서 확인한다.",
            "- `panel_day_engine_operator_workflow_default_v1.csv`: 현재 운영 queue/watch 기본 row 를 확인한다.",
            "- `panel_day_engine_project_final_do_and_dont_v1.csv`: 말해도 되는 것과 말하면 안 되는 것을 마지막으로 체크한다.",
        ]
        last_pos = -1
        for line in top_read_lines:
            pos = markdown.find(line)
            assert_true(pos >= 0, f"missing top read line: {line}")
            assert_true(pos > last_pos, "top read order mismatch")
            last_pos = pos

        artifact_index_df = pd.read_csv(artifact_index_csv, low_memory=False, encoding="utf-8-sig")
        required_artifacts = {
            "panel_day_engine_panel_multiaxis_verdict_v1.csv",
            "panel_day_engine_panel_multiaxis_event_supplement_v1.csv",
            "panel_day_engine_panel_multiaxis_cluster_supplement_v1.csv",
            "panel_day_engine_panel_multiaxis_verdict_summary_v1.csv",
            "panel_day_engine_project_final_decision_pack_v1.csv",
            "panel_day_engine_project_final_do_and_dont_v1.csv",
            "panel_day_engine_project_handoff_pack_v1.md",
            "panel_day_engine_internal_share_clean_pack_v1.md",
            "panel_day_engine_abrupt6_symptom_map_v1.csv",
            "panel_day_engine_kernellog_project_mapping_v1.csv",
            "panel_day_engine_gpv7_perf_summary_v1.csv",
            "panel_day_engine_project_progress_snapshot_v1.csv",
            "panel_day_engine_operator_pipeline_manifest_v1.csv",
            "panel_day_engine_operator_release_gate_manifest_v1.csv",
        }
        assert_true(required_artifacts.issubset(set(artifact_index_df["산출물명"])), "artifact index missing rows")

        status_snapshot_df = pd.read_csv(status_snapshot_csv, low_memory=False, encoding="utf-8-sig")
        required_status_items = {
            "현재_브랜치",
            "현재_HEAD_커밋",
            "완료된_로드맵_최대단계",
            "선택된_운영_workflow",
            "release_gate_통과여부",
            "pipeline_통과여부",
            "현재_데이터_한계",
            "최종_권장_사용_범위",
            "패널_3축통합판정_행수",
            "패널_3축통합판정_GPVS부착수",
            "패널_3축통합판정_GPVS미부착수",
            "패널_3축통합판정_커널로그원인군부착수",
        }
        assert_true(required_status_items.issubset(set(status_snapshot_df["항목"])), "status snapshot missing rows")
        branch_value = status_snapshot_df.loc[status_snapshot_df["항목"].eq("현재_브랜치"), "값"].iloc[0]
        assert_true(branch_value == "feature/test-closeout", "unexpected branch value in status snapshot")
        assert_true(
            status_snapshot_df.loc[status_snapshot_df["항목"].eq("패널_3축통합판정_행수"), "값"].iloc[0] == "25",
            "panel multiaxis total count mismatch",
        )
        assert_true(
            status_snapshot_df.loc[status_snapshot_df["항목"].eq("패널_3축통합판정_GPVS부착수"), "값"].iloc[0] == "6",
            "panel multiaxis GPVS attached count mismatch",
        )
        assert_true(
            status_snapshot_df.loc[status_snapshot_df["항목"].eq("패널_3축통합판정_GPVS미부착수"), "값"].iloc[0] == "0",
            "panel multiaxis GPVS unattached count mismatch",
        )
        assert_true(
            status_snapshot_df.loc[status_snapshot_df["항목"].eq("패널_3축통합판정_커널로그원인군부착수"), "값"].iloc[0] == "6",
            "panel multiaxis kernel cause attach count mismatch",
        )

    after = {path: file_digest(path) for path in official_outputs}
    assert_true(before == after, "official outputs changed during smoke test")


if __name__ == "__main__":
    main()
