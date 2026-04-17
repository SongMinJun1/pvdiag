#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]

OUTPUTS = [
    "panel_day_engine_gpvs_evidence_pack_v1.csv",
    "panel_day_engine_gpvs_evidence_summary_v1.csv",
    "panel_day_engine_gpvs_evidence_note_v1.md",
]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture(root: Path) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    verdict_rows = [
        {
            "site": "conalog",
            "panel_id": "panel_f4_1",
            "사건유형_ko": "전조형 고장",
            "최종고장양상_ko": "진행성 악화",
            "커널로그_원인군_ko": "다이오드/전기적 이상",
            "패널고장여부_ko": "고장",
            "GPVS_내부참고유형_ko": "전기적 고장 계열",
            "GPVS_외부참조패턴_ko": "국소 출력 불균형형",
        },
        {
            "site": "conalog",
            "panel_id": "panel_f2_1",
            "사건유형_ko": "전조형 고장",
            "최종고장양상_ko": "급격 종료",
            "커널로그_원인군_ko": "개방/장치이상",
            "패널고장여부_ko": "고장",
            "GPVS_내부참고유형_ko": "개방/장치이상 계열",
            "GPVS_외부참조패턴_ko": "장치 응답 이상형",
        },
        {
            "site": "gangui",
            "panel_id": "panel_f2_2",
            "사건유형_ko": "급작 고장",
            "최종고장양상_ko": "급작 발생",
            "커널로그_원인군_ko": "전기적 이상",
            "패널고장여부_ko": "고장",
            "GPVS_내부참고유형_ko": "전기적 고장 계열",
            "GPVS_외부참조패턴_ko": "장치 응답 이상형",
        },
        {
            "site": "gangui",
            "panel_id": "panel_f2_3",
            "사건유형_ko": "급작 고장",
            "최종고장양상_ko": "급작 발생",
            "커널로그_원인군_ko": "전기적 이상",
            "패널고장여부_ko": "고장",
            "GPVS_내부참고유형_ko": "전기적 고장 계열",
            "GPVS_외부참조패턴_ko": "장치 응답 이상형",
        },
        {
            "site": "ktc_ess",
            "panel_id": "panel_f4_2",
            "사건유형_ko": "급작 고장",
            "최종고장양상_ko": "급작 발생",
            "커널로그_원인군_ko": "비교곤란",
            "패널고장여부_ko": "고장",
            "GPVS_내부참고유형_ko": "불확실",
            "GPVS_외부참조패턴_ko": "국소 출력 불균형형",
        },
        {
            "site": "ktc_ess",
            "panel_id": "panel_f2_4",
            "사건유형_ko": "전조형 고장",
            "최종고장양상_ko": "진행성 악화",
            "커널로그_원인군_ko": "모듈 손상",
            "패널고장여부_ko": "고장",
            "GPVS_내부참고유형_ko": "전기적 고장 계열",
            "GPVS_외부참조패턴_ko": "장치 응답 이상형",
        },
        {
            "site": "siteX",
            "panel_id": "panel_non_fault",
            "사건유형_ko": "",
            "최종고장양상_ko": "",
            "커널로그_원인군_ko": "",
            "패널고장여부_ko": "미확정",
            "GPVS_내부참고유형_ko": "",
            "GPVS_외부참조패턴_ko": "",
        },
    ]
    write_csv(
        share_dir / "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        verdict_rows,
        [
            "site",
            "panel_id",
            "사건유형_ko",
            "최종고장양상_ko",
            "커널로그_원인군_ko",
            "패널고장여부_ko",
            "GPVS_내부참고유형_ko",
            "GPVS_외부참조패턴_ko",
        ],
    )

    family_eval_rows = [
        {
            "site": "conalog",
            "panel_id": "panel_f4_1",
            "prediction_source": "critical_phenotype_v3",
            "fallback_rule_used": "resolved_by_critical_phenotype_v3",
            "error_type": "correct",
            "pred_fault_family": "electrical_fault_like",
            "vendor_fault_family": "diode_like",
        },
        {
            "site": "conalog",
            "panel_id": "panel_f2_1",
            "prediction_source": "strict_day_core_fallback",
            "fallback_rule_used": "legacy_open_device",
            "error_type": "correct",
            "pred_fault_family": "open_or_device_issue_like",
            "vendor_fault_family": "open_or_device_issue_like",
        },
        {
            "site": "gangui",
            "panel_id": "panel_f2_2",
            "prediction_source": "critical_phenotype_v3",
            "fallback_rule_used": "resolved_by_critical_phenotype_v3",
            "error_type": "correct",
            "pred_fault_family": "electrical_fault_like",
            "vendor_fault_family": "diode_like",
        },
        {
            "site": "gangui",
            "panel_id": "panel_f2_3",
            "prediction_source": "critical_phenotype_v3",
            "fallback_rule_used": "resolved_by_critical_phenotype_v3",
            "error_type": "correct",
            "pred_fault_family": "electrical_fault_like",
            "vendor_fault_family": "diode_like",
        },
        {
            "site": "ktc_ess",
            "panel_id": "panel_f2_4",
            "prediction_source": "critical_phenotype_v3",
            "fallback_rule_used": "resolved_by_critical_phenotype_v3",
            "error_type": "correct",
            "pred_fault_family": "electrical_fault_like",
            "vendor_fault_family": "module_damage_like",
        },
    ]
    write_csv(
        share_dir / "gpvs_fault_family_eval_cases.csv",
        family_eval_rows,
        [
            "site",
            "panel_id",
            "prediction_source",
            "fallback_rule_used",
            "error_type",
            "pred_fault_family",
            "vendor_fault_family",
        ],
    )

    attach_rows = [
        {
            "site": "ktc_ess",
            "panel_id": "panel_f4_2",
            "GPVS_참고유형_ko": "불확실",
            "source_key_ko": "site+panel_id",
            "비고_ko": "prediction_source=critical_phenotype_v3, fallback_rule=resolved_by_critical_phenotype_v3, error_type=abstain_uncertain, vendor_fault_family=diode_like",
        }
    ]
    write_csv(
        share_dir / "panel_day_engine_gpvs_panel_attach_candidates_v1.csv",
        attach_rows,
        ["site", "panel_id", "GPVS_참고유형_ko", "source_key_ko", "비고_ko"],
    )

    detailed_rows = [
        {
            "site": "conalog",
            "panel_id": "panel_f4_1",
            "gpvs_detailed_model_source": "recovered_artifact",
            "gpvs_detailed_top1_fault_type": "F4L",
            "gpvs_detailed_top1_score": 0.766398,
            "gpvs_detailed_top2_fault_type": "F2M",
            "gpvs_detailed_top2_score": 0.231202,
            "gpvs_detailed_margin": 0.535196,
            "gpvs_detailed_status_ko": "추론성공",
            "gpvs_detailed_reason_ko": "fixture",
        },
        {
            "site": "conalog",
            "panel_id": "panel_f2_1",
            "gpvs_detailed_model_source": "recovered_artifact",
            "gpvs_detailed_top1_fault_type": "F2M",
            "gpvs_detailed_top1_score": 0.999968,
            "gpvs_detailed_top2_fault_type": "F4L",
            "gpvs_detailed_top2_score": 0.000030,
            "gpvs_detailed_margin": 0.999938,
            "gpvs_detailed_status_ko": "추론성공",
            "gpvs_detailed_reason_ko": "fixture",
        },
        {
            "site": "gangui",
            "panel_id": "panel_f2_2",
            "gpvs_detailed_model_source": "recovered_artifact",
            "gpvs_detailed_top1_fault_type": "F2M",
            "gpvs_detailed_top1_score": 0.998361,
            "gpvs_detailed_top2_fault_type": "F4L",
            "gpvs_detailed_top2_score": 0.001631,
            "gpvs_detailed_margin": 0.996731,
            "gpvs_detailed_status_ko": "추론성공",
            "gpvs_detailed_reason_ko": "fixture",
        },
        {
            "site": "gangui",
            "panel_id": "panel_f2_3",
            "gpvs_detailed_model_source": "recovered_artifact",
            "gpvs_detailed_top1_fault_type": "F2M",
            "gpvs_detailed_top1_score": 0.990925,
            "gpvs_detailed_top2_fault_type": "F4L",
            "gpvs_detailed_top2_score": 0.009071,
            "gpvs_detailed_margin": 0.981854,
            "gpvs_detailed_status_ko": "추론성공",
            "gpvs_detailed_reason_ko": "fixture",
        },
        {
            "site": "ktc_ess",
            "panel_id": "panel_f4_2",
            "gpvs_detailed_model_source": "recovered_artifact",
            "gpvs_detailed_top1_fault_type": "F4L",
            "gpvs_detailed_top1_score": 0.821737,
            "gpvs_detailed_top2_fault_type": "F2M",
            "gpvs_detailed_top2_score": 0.116780,
            "gpvs_detailed_margin": 0.704957,
            "gpvs_detailed_status_ko": "추론성공",
            "gpvs_detailed_reason_ko": "fixture",
        },
        {
            "site": "ktc_ess",
            "panel_id": "panel_f2_4",
            "gpvs_detailed_model_source": "recovered_artifact",
            "gpvs_detailed_top1_fault_type": "F2M",
            "gpvs_detailed_top1_score": 0.963202,
            "gpvs_detailed_top2_fault_type": "F4L",
            "gpvs_detailed_top2_score": 0.036322,
            "gpvs_detailed_margin": 0.926880,
            "gpvs_detailed_status_ko": "추론성공",
            "gpvs_detailed_reason_ko": "fixture",
        },
    ]
    write_csv(
        share_dir / "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv",
        detailed_rows,
        [
            "site",
            "panel_id",
            "gpvs_detailed_model_source",
            "gpvs_detailed_top1_fault_type",
            "gpvs_detailed_top1_score",
            "gpvs_detailed_top2_fault_type",
            "gpvs_detailed_top2_score",
            "gpvs_detailed_margin",
            "gpvs_detailed_status_ko",
            "gpvs_detailed_reason_ko",
        ],
    )

    sanity_rows = [
        {
            "site": row["site"],
            "panel_id": row["panel_id"],
            "attach_recommendation_ko": "attach_ok",
            "family_vs_detail_consistency_ko": "fixture consistency",
        }
        for row in detailed_rows
    ]
    write_csv(
        share_dir / "panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv",
        sanity_rows,
        ["site", "panel_id", "attach_recommendation_ko", "family_vs_detail_consistency_ko"],
    )

    provenance_summary = [
        {
            "provenance_status": "original_trained_head_recovered",
            "serialized_model_found_flag": 1,
            "feature_manifest_found_flag": 1,
            "training_script_found_flag": 1,
            "evaluation_script_found_flag": 1,
            "current_fallback_lr_attachable_flag": 0,
            "note_ko": "fixture",
        }
    ]
    write_csv(
        share_dir / "panel_day_engine_gpvs_bytype_provenance_summary_v1.csv",
        provenance_summary,
        [
            "provenance_status",
            "serialized_model_found_flag",
            "feature_manifest_found_flag",
            "training_script_found_flag",
            "evaluation_script_found_flag",
            "current_fallback_lr_attachable_flag",
            "note_ko",
        ],
    )

    rebuild_summary = [
        {
            "recovered_model_exported_flag": 1,
            "recovered_feature_manifest_exported_flag": 1,
            "recovered_model_source_ko": "fixture",
            "parity_overall_status_ko": "일치",
            "current_recovered_attachable_flag": 1,
            "note_ko": "fixture",
        }
    ]
    write_csv(
        share_dir / "panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv",
        rebuild_summary,
        [
            "recovered_model_exported_flag",
            "recovered_feature_manifest_exported_flag",
            "recovered_model_source_ko",
            "parity_overall_status_ko",
            "current_recovered_attachable_flag",
            "note_ko",
        ],
    )

    agreement_rows = [
        {
            "site": "conalog",
            "panel_id": "panel_f4_1",
            "overall_gpvs_reference_usefulness_ko": "주의참고",
            "family_vs_kernellog_alignment_ko": "일치",
            "scenario_vs_kernellog_alignment_ko": "부분일치",
            "feature_shift_bucket_ko": "strong_shift",
            "overall_gpvs_trust_note_ko": "fixture caution",
        },
        {
            "site": "conalog",
            "panel_id": "panel_f2_1",
            "overall_gpvs_reference_usefulness_ko": "비권장",
            "family_vs_kernellog_alignment_ko": "일치",
            "scenario_vs_kernellog_alignment_ko": "불일치",
            "feature_shift_bucket_ko": "strong_shift",
            "overall_gpvs_trust_note_ko": "fixture caution",
        },
        {
            "site": "gangui",
            "panel_id": "panel_f2_2",
            "overall_gpvs_reference_usefulness_ko": "비권장",
            "family_vs_kernellog_alignment_ko": "일치",
            "scenario_vs_kernellog_alignment_ko": "불일치",
            "feature_shift_bucket_ko": "strong_shift",
            "overall_gpvs_trust_note_ko": "fixture caution",
        },
        {
            "site": "gangui",
            "panel_id": "panel_f2_3",
            "overall_gpvs_reference_usefulness_ko": "비권장",
            "family_vs_kernellog_alignment_ko": "일치",
            "scenario_vs_kernellog_alignment_ko": "불일치",
            "feature_shift_bucket_ko": "strong_shift",
            "overall_gpvs_trust_note_ko": "fixture caution",
        },
        {
            "site": "ktc_ess",
            "panel_id": "panel_f4_2",
            "overall_gpvs_reference_usefulness_ko": "주의참고",
            "family_vs_kernellog_alignment_ko": "비교곤란",
            "scenario_vs_kernellog_alignment_ko": "부분일치",
            "feature_shift_bucket_ko": "strong_shift",
            "overall_gpvs_trust_note_ko": "fixture caution",
        },
        {
            "site": "ktc_ess",
            "panel_id": "panel_f2_4",
            "overall_gpvs_reference_usefulness_ko": "비권장",
            "family_vs_kernellog_alignment_ko": "부분일치",
            "scenario_vs_kernellog_alignment_ko": "불일치",
            "feature_shift_bucket_ko": "strong_shift",
            "overall_gpvs_trust_note_ko": "fixture caution",
        },
    ]
    write_csv(
        share_dir / "panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv",
        agreement_rows,
        [
            "site",
            "panel_id",
            "overall_gpvs_reference_usefulness_ko",
            "family_vs_kernellog_alignment_ko",
            "scenario_vs_kernellog_alignment_ko",
            "feature_shift_bucket_ko",
            "overall_gpvs_trust_note_ko",
        ],
    )

    compatibility_summary = [
        {
            "fault_panel_count": 6,
            "recovered_model_present_flag": 1,
            "feature_schema_match_ratio": 1.0,
            "strong_shift_panel_count": 6,
            "mild_shift_panel_count": 0,
            "family_alignment_count": 4,
            "family_partial_alignment_count": 1,
            "family_conflict_count": 0,
            "scenario_alignment_count": 0,
            "scenario_partial_alignment_count": 2,
            "scenario_conflict_count": 4,
            "gpvs_reference_useful_count": 0,
            "gpvs_reference_caution_count": 2,
            "gpvs_reference_not_recommended_count": 4,
            "final_recommendation_ko": "참고축으로만 사용",
            "note_ko": "GPVS original scenario space and MLPE official problem-type space are not identical.",
        }
    ]
    write_csv(
        share_dir / "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv",
        compatibility_summary,
        [
            "fault_panel_count",
            "recovered_model_present_flag",
            "feature_schema_match_ratio",
            "strong_shift_panel_count",
            "mild_shift_panel_count",
            "family_alignment_count",
            "family_partial_alignment_count",
            "family_conflict_count",
            "scenario_alignment_count",
            "scenario_partial_alignment_count",
            "scenario_conflict_count",
            "gpvs_reference_useful_count",
            "gpvs_reference_caution_count",
            "gpvs_reference_not_recommended_count",
            "final_recommendation_ko",
            "note_ko",
        ],
    )

    matching_table_rows = [
        {
            "mlpe_official_fault_ko": "정션박스 손상",
            "canonical_gpvs_code": "F4",
            "match_strength_ko": "강",
            "match_role_ko": "핵심참조",
            "evidence_basis_ko": "fixture",
            "current_real_fault_support_count": 2,
            "recommendation_ko": "reference layer에서 우선 확인하되 direct root-cause로 단정하지 않음",
        },
        {
            "mlpe_official_fault_ko": "케이블 접점불량(단선)",
            "canonical_gpvs_code": "F5",
            "match_strength_ko": "강",
            "match_role_ko": "핵심참조",
            "evidence_basis_ko": "fixture",
            "current_real_fault_support_count": 0,
            "recommendation_ko": "조건부 사용",
        },
        {
            "mlpe_official_fault_ko": "모듈 경년 열화",
            "canonical_gpvs_code": "F4",
            "match_strength_ko": "중",
            "match_role_ko": "보조참조",
            "evidence_basis_ko": "fixture",
            "current_real_fault_support_count": 2,
            "recommendation_ko": "조건부 reference로만 사용",
        },
        {
            "mlpe_official_fault_ko": "인버터/스트링 동작 불량",
            "canonical_gpvs_code": "F2",
            "match_strength_ko": "약",
            "match_role_ko": "보조참조",
            "evidence_basis_ko": "fixture",
            "current_real_fault_support_count": 4,
            "recommendation_ko": "제어·계측 이상 힌트로만 사용",
        },
        {
            "mlpe_official_fault_ko": "인버터/스트링 동작 불량",
            "canonical_gpvs_code": "F3",
            "match_strength_ko": "약",
            "match_role_ko": "교란플래그",
            "evidence_basis_ko": "fixture",
            "current_real_fault_support_count": 0,
            "recommendation_ko": "교란 플래그로만 유지",
        },
        {
            "mlpe_official_fault_ko": "인버터/스트링 동작 불량",
            "canonical_gpvs_code": "F1",
            "match_strength_ko": "약",
            "match_role_ko": "시스템보류",
            "evidence_basis_ko": "fixture",
            "current_real_fault_support_count": 0,
            "recommendation_ko": "통합 결과표 후보축으로만 보류",
        },
        {
            "mlpe_official_fault_ko": "인버터/스트링 동작 불량",
            "canonical_gpvs_code": "F6",
            "match_strength_ko": "약",
            "match_role_ko": "시스템보류",
            "evidence_basis_ko": "fixture",
            "current_real_fault_support_count": 0,
            "recommendation_ko": "통합 결과표 후보축으로만 보류",
        },
        {
            "mlpe_official_fault_ko": "인버터/스트링 동작 불량",
            "canonical_gpvs_code": "F7",
            "match_strength_ko": "약",
            "match_role_ko": "시스템보류",
            "evidence_basis_ko": "fixture",
            "current_real_fault_support_count": 0,
            "recommendation_ko": "통합 결과표 후보축으로만 보류",
        },
    ]
    write_csv(
        share_dir / "panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv",
        matching_table_rows,
        [
            "mlpe_official_fault_ko",
            "canonical_gpvs_code",
            "match_strength_ko",
            "match_role_ko",
            "evidence_basis_ko",
            "current_real_fault_support_count",
            "recommendation_ko",
        ],
    )

    matching_summary = [
        {
            "canonical_code_count": 8,
            "core_reference_count": 3,
            "auxiliary_reference_count": 1,
            "confounder_count": 1,
            "reserved_system_count": 3,
            "final_matching_policy_ko": "F0/F4/F5 core, F2 auxiliary, F3 confounder, F1/F6/F7 reserved",
            "note_ko": "fixture",
        }
    ]
    write_csv(
        share_dir / "panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv",
        matching_summary,
        [
            "canonical_code_count",
            "core_reference_count",
            "auxiliary_reference_count",
            "confounder_count",
            "reserved_system_count",
            "final_matching_policy_ko",
            "note_ko",
        ],
    )

    dictionary_rows = [
        {
            "canonical_gpvs_code": "F0",
            "current_usage_tier_ko": "baseline",
            "mlpe_reference_name_ko": "정상 기준선",
            "usage_rule_ko": "비고장 기준선과 drift 비교에만 사용",
            "note_ko": "fixture",
        },
        {
            "canonical_gpvs_code": "F1",
            "current_usage_tier_ko": "reserved_system_level",
            "mlpe_reference_name_ko": "인버터 전력변환부 시스템 시나리오",
            "usage_rule_ko": "MLPE direct fault명이 아니라 통합 결과표 후보축으로만 보류",
            "note_ko": "fixture",
        },
        {
            "canonical_gpvs_code": "F2",
            "current_usage_tier_ko": "auxiliary_reference",
            "mlpe_reference_name_ko": "제어/계측 이상 보조 힌트",
            "usage_rule_ko": "direct root-cause가 아니라 제어·계측 이상 힌트로만 사용",
            "note_ko": "fixture",
        },
        {
            "canonical_gpvs_code": "F3",
            "current_usage_tier_ko": "confounder_only",
            "mlpe_reference_name_ko": "계통 교란 플래그",
            "usage_rule_ko": "fault label이 아니라 confounder flag로만 사용",
            "note_ko": "fixture",
        },
        {
            "canonical_gpvs_code": "F4",
            "current_usage_tier_ko": "core_reference",
            "mlpe_reference_name_ko": "패널·어레이 mismatch 핵심 참조",
            "usage_rule_ko": "MLPE 패널·어레이 불균형 해석의 핵심 reference로 사용",
            "note_ko": "fixture",
        },
        {
            "canonical_gpvs_code": "F5",
            "current_usage_tier_ko": "core_reference_candidate",
            "mlpe_reference_name_ko": "부분 개방회로 계열 핵심 참조 후보",
            "usage_rule_ko": "케이블 접점불량(단선) 가설의 핵심 reference candidate로 유지",
            "note_ko": "fixture",
        },
        {
            "canonical_gpvs_code": "F6",
            "current_usage_tier_ko": "reserved_system_level",
            "mlpe_reference_name_ko": "제어기 gain 이상 시스템 시나리오",
            "usage_rule_ko": "MLPE direct fault명이 아니라 통합 결과표 후보축으로만 보류",
            "note_ko": "fixture",
        },
        {
            "canonical_gpvs_code": "F7",
            "current_usage_tier_ko": "reserved_system_level",
            "mlpe_reference_name_ko": "제어기 시정수 이상 시스템 시나리오",
            "usage_rule_ko": "MLPE direct fault명이 아니라 통합 결과표 후보축으로만 보류",
            "note_ko": "fixture",
        },
    ]
    write_csv(
        share_dir / "panel_day_engine_gpvs_canonical_dictionary_v1.csv",
        dictionary_rows,
        [
            "canonical_gpvs_code",
            "current_usage_tier_ko",
            "mlpe_reference_name_ko",
            "usage_rule_ko",
            "note_ko",
        ],
    )


def main() -> None:
    build_script = REPO_ROOT / "research/prognostics/build_panel_day_engine_gpvs_evidence_pack_v1.py"
    smoke_script = REPO_ROOT / "research/prognostics/smoke_test_panel_day_engine_gpvs_evidence_pack_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        REPO_ROOT / "_share/panel_day_engine_panel_multiaxis_verdict_v1.csv",
        REPO_ROOT / "_share/panel_day_engine_project_handoff_pack_v1.md",
        REPO_ROOT / "_share/panel_day_engine_project_closeout_pack_v1.md",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="gpvs_evidence_pack_smoke_") as tmp_dir:
        root = Path(tmp_dir)
        build_fixture(root)
        result = run([sys.executable, str(build_script), "--root", str(root)], REPO_ROOT)
        if result.returncode != 0:
            raise SystemExit(f"build failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        for output_name in OUTPUTS:
            output_path = root / "_share" / output_name
            assert_true(output_path.exists(), f"missing output: {output_name}")

        pack_df = pd.read_csv(root / "_share" / OUTPUTS[0], low_memory=False, encoding="utf-8-sig")
        summary_df = pd.read_csv(root / "_share" / OUTPUTS[1], low_memory=False, encoding="utf-8-sig")
        note_text = (root / "_share" / OUTPUTS[2]).read_text(encoding="utf-8")

        assert_true(len(pack_df) == 6, "fault panel count must stay 6")
        assert_true(pack_df["GPVS_최종사용권고_ko"].fillna("").str.strip().ne("").all(), "every fault panel row must have final recommendation")
        assert_true(int(summary_df.iloc[0]["fault_panel_count"]) == 6, "summary fault_panel_count must equal 6")
        assert_true(
            summary_df.iloc[0]["final_operational_rule_ko"] == "GPVS는 direct root-cause classifier가 아니라 reference layer로만 사용",
            "final_operational_rule_ko must be populated with reference-layer rule",
        )

        rec_map = {
            f"{row['site']}::{row['panel_id']}": row["GPVS_최종사용권고_ko"]
            for row in pack_df.to_dict(orient="records")
        }
        assert_true(rec_map["conalog::panel_f4_1"] == "핵심참조", "F4 caution panel should remain core reference")
        assert_true(rec_map["conalog::panel_f2_1"] == "비권장", "F2 low-compatibility panel should degrade to 비권장")
        assert_true("GPVS 내부판정과 외부참조는 서로 다른 레이어" in note_text, "note must separate internal and external GPVS layers")
        assert_true("reference layer" in note_text, "note must preserve reference-layer rule")

    after = {path: file_digest(path) for path in official_outputs}
    for path in official_outputs:
        assert_true(before[path] == after[path], f"official output changed unexpectedly: {path}")


if __name__ == "__main__":
    main()
