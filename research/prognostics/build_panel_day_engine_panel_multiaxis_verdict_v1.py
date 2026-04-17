#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

WORKFLOW_DEFAULT_NAME = "panel_day_engine_operator_workflow_default_v1.csv"
ABRUPT6_SYMPTOM_MAP_NAME = "panel_day_engine_abrupt6_symptom_map_v1.csv"
KERNELLOG_PROJECT_MAPPING_NAME = "panel_day_engine_kernellog_project_mapping_v1.csv"
GPV7_PERF_SUMMARY_NAME = "panel_day_engine_gpv7_perf_summary_v1.csv"
FINAL_DECISION_PACK_NAME = "panel_day_engine_project_final_decision_pack_v1.csv"
PRECURSOR_ONSET_TRUTH_NAME = "panel_day_engine_precursor_onset_truth_v1.csv"
NON_PRECURSOR_PERFORMANCE_CASES_NAME = "panel_day_engine_non_precursor_performance_cases_v1.csv"
COMMON_CAUSE_RETROFIT_NAME = "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv"
GPVS_ATTACH_INVENTORY_NAME = "panel_day_engine_gpvs_panel_attach_inventory_v1.csv"
GPVS_ATTACH_FEASIBILITY_NAME = "panel_day_engine_gpvs_panel_attach_feasibility_v1.csv"
GPVS_ATTACH_CANDIDATES_NAME = "panel_day_engine_gpvs_panel_attach_candidates_v1.csv"
PRECURSOR_ABRUPT_CONSISTENCY_CASES_NAME = "panel_day_engine_precursor_abrupt_consistency_cases_v1.csv"
PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME = "panel_day_engine_precursor_abrupt_consistency_summary_v1.csv"
PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME = "panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv"
FORENSIC_SUMMARY_NAME = "panel_day_engine_c42997_1_1_forensic_summary_v1.csv"
FAULT_PANEL_EVENT_AUDIT_NAME = "panel_day_engine_fault_panel_event_audit_v1.csv"
DETAILED_FAULT_BRIDGE_AUDIT_NAME = "panel_day_engine_detailed_fault_bridge_audit_v1.csv"
DETAILED_FAULT_BRIDGE_SUMMARY_NAME = "panel_day_engine_detailed_fault_bridge_summary_v1.csv"
GPVS_BYTYPE_REBUILD_SUMMARY_NAME = "panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv"
GPVS_DETAILED_TYPE_INFERENCE_AUDIT_NAME = "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv"
GPVS_DETAILED_TYPE_REALPANEL_SANITY_NAME = "panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv"
GPVS_MLPE_PANEL_AGREEMENT_NAME = "panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv"
GPVS_CANONICAL_DICTIONARY_NAME = "panel_day_engine_gpvs_canonical_dictionary_v1.csv"
GPVS_MLPE_FAULT_MATCHING_TABLE_NAME = "panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv"
GPVS_MLPE_COMPATIBILITY_SUMMARY_NAME = "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv"

VERDICT_OUTPUT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
EVENT_SUPPLEMENT_OUTPUT_NAME = "panel_day_engine_panel_multiaxis_event_supplement_v1.csv"
CLUSTER_SUPPLEMENT_OUTPUT_NAME = "panel_day_engine_panel_multiaxis_cluster_supplement_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_panel_multiaxis_verdict_summary_v1.csv"

VERDICT_COLS = [
    "site",
    "panel_id",
    "사건유형_ko",
    "사건유형_해석_ko",
    "최종고장양상_ko",
    "대표판정_ko",
    "사건이력_ko",
    "전조흔적_flag",
    "순수급작_flag",
    "전조평가셋편입_flag",
    "급작평가셋편입_flag",
    "해석대평가차이_ko",
    "운영최초전조발견일",
    "운영최초전조마커",
    "사건해석상전조시작일",
    "benchmark전조시작일",
    "전조형이력_flag",
    "급작고장이력_flag",
    "공통원인이력_flag",
    "반복이상이력_flag",
    "패널고장여부_ko",
    "GPVS_적용대상_ko",
    "커널로그_증상명_ko",
    "커널로그_원인군_ko",
    "GPVS_부착상태_ko",
    "GPVS_내부참고유형_ko",
    "GPVS_외부참조패턴_ko",
    "GPVS_참조사용등급_ko",
    "GPVS_참조설명_ko",
    "세부fault_type_code",
    "세부fault_type_label_ko",
    "세부fault_부착상태_ko",
    "세부fault_근거파일_ko",
    "세부fault_기준일",
    "세부fault_보류사유_ko",
    "운영위치_ko",
    "판정주의_ko",
]

EVENT_SUPPLEMENT_COLS = [
    "site",
    "panel_id",
    "사건유형_ko",
    "사건우선순위",
    "대표판정여부_flag",
    "운영위치_ko",
    "비고_ko",
]

CLUSTER_COLS = [
    "site",
    "cluster_id",
    "대표판정_ko",
    "커널로그_증상명_ko",
    "GPVS_참고유형_ko",
    "GPVS_근거_ko",
    "운영위치_ko",
    "판정주의_ko",
]

SUMMARY_COLS = [
    "전체_패널수",
    "고유_고장패널수",
    "사건해석_전조형_패널수",
    "사건해석_급작_패널수",
    "사건해석_전조형_급격종료_패널수",
    "사건해석_전조형_진행성악화_패널수",
    "전조흔적_패널수",
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
    "GPVS_미부착_패널key없음수",
    "GPVS_미부착_key부족수",
    "GPVS_미부착_산출물없음수",
    "GPVS_세부fault_부착수",
    "GPVS_세부fault_판정유보수",
    "GPVS_세부fault_추론불가수",
    "GPVS_세부fault_부착패널수",
    "GPVS_세부fault_판정유보패널수",
    "GPVS_세부fault_비대상패널수",
    "GPVS_세부fault_F2M_패널수",
    "GPVS_세부fault_F4L_패널수",
    "사건보조행수",
    "클러스터_보조행수",
    "note_ko",
]

PANEL_LEVEL_PREVIEW_CLASSES = {"queue_run", "watch_now_panel"}
CLUSTER_PREVIEW_CLASS = "secondary_value_cluster"
GPVS_ABSENCE_REASON = "현재 저장 산출물에는 패널별 GPVS 직접 판정이 없음"
GPVS_NON_TARGET_REASON = "고장 패널이 아니어서 GPVS 적용 대상 아님"
GPVS_SCENARIO_WARNING = "외부 GPVS 실험 시나리오 설명이며 실제 패널의 물리 root cause를 직접 뜻하지 않음"
GPVS_REFERENCE_ONLY_NOTE = "GPVS는 direct root-cause classifier가 아니라 reference layer로만 사용"
GPVS_FRONT_PATTERN_NAME_MAP = {
    "F0": "정상 기준형",
    "F1": "전력변환부 이상형",
    "F2": "장치 응답 이상형",
    "F3": "외부 계통 교란형",
    "F4": "국소 출력 불균형형",
    "F5": "부분 개방·접속 이상형",
    "F6": "제어 응답 이상형",
    "F7": "제어 응답 이상형",
}
GPVS_FRONT_DESCRIPTION_MAP = {
    "F0": "비고장 기준 패턴으로, 다른 패널/구간의 변화량을 비교하는 기준선",
    "F1": "인버터 전력변환부 이상과 유사한 패턴",
    "F2": "센서/피드백 오류로 장치 응답이 어긋나는 패턴으로, 패널 물리 파손보다 장치 응답 이상 힌트로 해석",
    "F3": "외부 계통 변동이나 순간 저전압과 유사한 교란 이벤트 패턴",
    "F4": "일부 패널의 출력 균형이 깨지는 패턴으로, 부분 음영뿐 아니라 오염·열화·다이오드/접속 이상 등과 유사하게 보일 수 있음",
    "F5": "일부 연결부가 끊기거나 약해진 것처럼 보이는 패턴으로, 커넥터 이탈·접점 불량·부분 단선과 더 잘 이어짐",
    "F6": "제어 응답 또는 제어 파라미터 이상과 유사한 패턴",
    "F7": "제어 응답 또는 제어 파라미터 이상과 유사한 패턴",
}
GPVS_REFERENCE_GRADE_MAP = {
    "참고가능": "참고가능",
    "주의참고": "주의참고",
    "비권장": "비권장",
}

GPVS_SCENARIO_FAMILY_MAP = {
    "F0": {
        "family": "정상 기준",
        "name": "정상 운전 시나리오",
        "description": "fault를 넣지 않은 기준 실험 상태",
    },
    "F1": {
        "family": "인버터/전력변환부 이상",
        "name": "인버터 전력소자 이상 시나리오",
        "description": "인버터 내부 IGBT 등 전력소자 고장으로 전력변환 경로 자체가 깨지는 상황",
    },
    "F2": {
        "family": "제어·계측 이상",
        "name": "제어 피드백 센서 이상 시나리오",
        "description": "전류/전압 피드백 센서 이상으로 제어기가 실제 상태를 잘못 읽어 MPPT 또는 인버터 제어가 어긋나는 상황",
    },
    "F3": {
        "family": "계통 이상",
        "name": "계통 전압 이상 시나리오",
        "description": "외부 계통 측 간헐적 전압 sag 등으로 운전 안정성이 흔들리는 상황",
    },
    "F4": {
        "family": "PV 어레이 이상",
        "name": "PV 어레이 mismatch(부분 음영) 시나리오",
        "description": "일부 패널이 부분 음영을 받아 어레이 내 전압·전류 균형이 깨지는 상황",
    },
    "F5": {
        "family": "PV 어레이 이상",
        "name": "PV 어레이 mismatch(부분 개방회로) 시나리오",
        "description": "PV 어레이 일부에 open-circuit 성격 이상이 생겨 어레이 균형이 깨지는 상황",
    },
    "F6": {
        "family": "제어기 이상",
        "name": "부스트 컨버터 PI gain 이상 시나리오",
        "description": "PI 제어기의 gain 설정 이상으로 제어 응답이 비정상화되는 상황",
    },
    "F7": {
        "family": "제어기 이상",
        "name": "부스트 컨버터 PI 시정수 이상 시나리오",
        "description": "PI 제어기의 time constant 이상으로 응답 속도와 안정화 과정이 비정상화되는 상황",
    },
}

GPVS_SCENARIO_MODE_MAP = {
    "L": "제한출력 운전(IPPT)",
    "M": "최대전력점 추종 운전(MPPT)",
}

EVENT_HISTORY_ORDER = [
    "전조형 고장",
    "급작 고장",
    "고장유형 보류",
    "공통원인 이벤트",
    "반복 이상",
]

EVENT_PRIORITY = {
    "급작 고장": 1,
    "전조형 고장": 2,
    "고장유형 보류": 3,
    "공통원인 이벤트": 4,
    "반복 이상": 5,
}

SPECIFIC_TO_BROAD_SYMPTOM = {
    "다이오드형": "전압 변화형",
    "개방/장치이상형": "전압 변화형",
    "모듈손상형": "출력 저하형",
    "출력저하형": "출력 저하형",
    "전압변화형": "전압 변화형",
    "복합형": "복합형",
    "불충분": "불충분",
}

SCOPE_BY_EVENT_TYPE = {
    "전조형 고장": "step3_precursor_performance",
    "급작 고장": "step4_abrupt_no_precursor",
    "공통원인 이벤트": "step4_common_cause_routing",
}

REQUIRED_FORENSIC_SUMMARY_COLS = [
    "site",
    "panel_id",
    "현재_재감사라벨_ko",
    "earliest_warning_date",
    "earliest_onset_date",
    "strong_trigger_date",
    "전조흔적_시작일",
    "강한트리거일",
    "사건유형_결정규칙_ko",
    "최종고장양상_결정규칙_ko",
    "사건유형_결정_ko",
    "최종고장양상_결정_ko",
    "사건시간양상_판정_ko",
    "현재표_보정필요여부_flag",
]

FORENSIC_RULE_SITE = "conalog"
FORENSIC_RULE_PANEL_ID = "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"
FORENSIC_RULE_ONSET_DATE = "2025-01-20"
FORENSIC_RULE_TRIGGER_DATE = "2025-03-21"
FORENSIC_RULE_EVENT_TYPE = "전조형 고장"
FORENSIC_RULE_TERMINAL_PATTERN = "급격 종료"
FORENSIC_RULE_REASON = "stored-field rule 기준 retrospective_onset_date<strict_trigger_date, onset_confidence=high, onset_method=persistent_5of7 이라 전조형 고장으로 읽고 최종고장양상은 급격 종료로 둔다"

EXPECTED_FINAL_SCOPES = {
    "step3_precursor_performance",
    "step4_abrupt_no_precursor",
    "step4_common_cause_routing",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a panel-level representative multi-axis verdict table with separate event-history and cluster supplements."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the project root.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def normalize_frames(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    normalized: dict[str, pd.DataFrame] = {}
    for key, value in frames.items():
        df = value.copy()
        for column in df.columns:
            if df[column].dtype == object:
                df[column] = df[column].map(normalize_text)
        normalized[key] = df
    return normalized


def first_existing_column(df: pd.DataFrame, candidates: list[str], frame_name: str) -> str:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    raise SystemExit(f"{frame_name} missing any of columns: {candidates}")


def to_numeric_flag(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def gpvs_scenario_fields(gpvs_detailed_code: object) -> dict[str, str]:
    code = normalize_text(gpvs_detailed_code)
    blank = {
        "GPVS_시나리오_family_ko": "",
        "GPVS_시나리오명_ko": "",
        "GPVS_시나리오_고장상황설명_ko": "",
        "GPVS_운전모드_ko": "",
        "GPVS_해석주의_ko": "",
    }
    if not code:
        return blank

    prefix = code[:2] if len(code) >= 2 else ""
    suffix = code[-1] if len(code) >= 1 else ""
    scenario_meta = GPVS_SCENARIO_FAMILY_MAP.get(prefix)
    if scenario_meta is None:
        return {
            "GPVS_시나리오_family_ko": "",
            "GPVS_시나리오명_ko": f"외부 GPVS 시나리오 {code}",
            "GPVS_시나리오_고장상황설명_ko": "공식 GPVS 시나리오 map에 직접 등록되지 않은 코드",
            "GPVS_운전모드_ko": GPVS_SCENARIO_MODE_MAP.get(suffix, ""),
            "GPVS_해석주의_ko": GPVS_SCENARIO_WARNING,
        }
    return {
        "GPVS_시나리오_family_ko": scenario_meta["family"],
        "GPVS_시나리오명_ko": scenario_meta["name"],
        "GPVS_시나리오_고장상황설명_ko": scenario_meta["description"],
        "GPVS_운전모드_ko": GPVS_SCENARIO_MODE_MAP.get(suffix, ""),
        "GPVS_해석주의_ko": GPVS_SCENARIO_WARNING,
    }


def canonical_gpvs_code(gpvs_detailed_code: object) -> str:
    code = normalize_text(gpvs_detailed_code).upper()
    if len(code) < 2 or not code.startswith("F"):
        return ""
    canonical = code[:2]
    return canonical if canonical in GPVS_FRONT_PATTERN_NAME_MAP else ""


def gpvs_front_facing_fields(
    *,
    panel_fault_status: str,
    gpvs_type: str,
    gpvs_detailed_code: str,
    panel_agreement_row: dict[str, str] | None,
) -> dict[str, str]:
    blank = {
        "GPVS_내부참고유형_ko": "",
        "GPVS_외부참조패턴_ko": "",
        "GPVS_참조사용등급_ko": "",
        "GPVS_참조설명_ko": "",
    }
    if panel_fault_status != "고장":
        return blank

    canonical_code = canonical_gpvs_code(gpvs_detailed_code)
    internal_type = normalize_text(gpvs_type)
    usefulness = ""
    if panel_agreement_row is not None:
        usefulness = GPVS_REFERENCE_GRADE_MAP.get(
            normalize_text(panel_agreement_row.get("overall_gpvs_reference_usefulness_ko", "")),
            "",
        )

    return {
        "GPVS_내부참고유형_ko": "" if internal_type in {"", "미부착", "비대상"} else internal_type,
        "GPVS_외부참조패턴_ko": GPVS_FRONT_PATTERN_NAME_MAP.get(canonical_code, ""),
        "GPVS_참조사용등급_ko": usefulness,
        "GPVS_참조설명_ko": GPVS_FRONT_DESCRIPTION_MAP.get(canonical_code, ""),
    }


def load_inputs(root: Path) -> dict[str, pd.DataFrame]:
    share_dir = root / "_share"
    frames = {
        "workflow": read_csv(share_dir / WORKFLOW_DEFAULT_NAME),
        "abrupt6": read_csv(share_dir / ABRUPT6_SYMPTOM_MAP_NAME),
        "kernel_map": read_csv(share_dir / KERNELLOG_PROJECT_MAPPING_NAME),
        "gpv7": read_csv(share_dir / GPV7_PERF_SUMMARY_NAME),
        "final_pack": read_csv(share_dir / FINAL_DECISION_PACK_NAME),
        "precursor_truth": read_csv(share_dir / PRECURSOR_ONSET_TRUTH_NAME),
        "non_precursor_perf": read_csv(share_dir / NON_PRECURSOR_PERFORMANCE_CASES_NAME),
        "common_cause": read_csv(share_dir / COMMON_CAUSE_RETROFIT_NAME),
        "gpvs_attach_inventory": read_csv(share_dir / GPVS_ATTACH_INVENTORY_NAME),
        "gpvs_attach_feasibility": read_csv(share_dir / GPVS_ATTACH_FEASIBILITY_NAME),
        "gpvs_attach_candidates": read_csv(share_dir / GPVS_ATTACH_CANDIDATES_NAME),
        "consistency_cases": read_csv(share_dir / PRECURSOR_ABRUPT_CONSISTENCY_CASES_NAME),
        "consistency_summary": read_csv(share_dir / PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME),
        "consistency_recommendation": read_csv(share_dir / PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME),
        "forensic_summary": read_csv(share_dir / FORENSIC_SUMMARY_NAME),
        "fault_event_audit": read_csv(share_dir / FAULT_PANEL_EVENT_AUDIT_NAME),
        "detailed_fault_bridge_audit": read_csv(share_dir / DETAILED_FAULT_BRIDGE_AUDIT_NAME),
        "detailed_fault_bridge_summary": read_csv(share_dir / DETAILED_FAULT_BRIDGE_SUMMARY_NAME),
        "gpvs_bytype_rebuild_summary": read_csv(share_dir / GPVS_BYTYPE_REBUILD_SUMMARY_NAME),
        "gpvs_detailed_type_audit": read_csv(share_dir / GPVS_DETAILED_TYPE_INFERENCE_AUDIT_NAME),
        "gpvs_detailed_type_realpanel_sanity": read_csv(share_dir / GPVS_DETAILED_TYPE_REALPANEL_SANITY_NAME),
        "gpvs_mlpe_panel_agreement": read_csv(share_dir / GPVS_MLPE_PANEL_AGREEMENT_NAME),
        "gpvs_canonical_dictionary": read_csv(share_dir / GPVS_CANONICAL_DICTIONARY_NAME),
        "gpvs_mlpe_fault_matching": read_csv(share_dir / GPVS_MLPE_FAULT_MATCHING_TABLE_NAME),
        "gpvs_mlpe_compatibility_summary": read_csv(share_dir / GPVS_MLPE_COMPATIBILITY_SUMMARY_NAME),
    }

    ensure_columns(
        frames["workflow"],
        [
            "preview_attention_class",
            "site",
            "display_entity_id",
            "display_shape_or_cluster_kind",
            "display_status_or_tier",
            "display_score",
            "workflow_reason_ko",
        ],
        WORKFLOW_DEFAULT_NAME,
    )
    ensure_columns(
        frames["abrupt6"],
        [
            "site",
            "panel_id",
            "고장시점",
            "사건유형_ko",
            "최종고장양상_ko",
            "순수급작_flag",
            "증상명_ko",
            "세부근거_ko",
            "source_field_ko",
            "비고_ko",
        ],
        ABRUPT6_SYMPTOM_MAP_NAME,
    )
    ensure_columns(
        frames["kernel_map"],
        ["커널로그_증상명", "주_프로젝트분류", "보조_프로젝트분류", "설명_ko", "주의_ko"],
        KERNELLOG_PROJECT_MAPPING_NAME,
    )
    ensure_columns(
        frames["gpv7"],
        ["고장유형_번호", "고장유형_설명_ko", "성능요약_ko", "수치_ko", "source_ref_ko"],
        GPV7_PERF_SUMMARY_NAME,
    )
    ensure_columns(
        frames["final_pack"],
        ["eval_scope", "current_data_decision", "final_usage_decision", "final_reason_ko"],
        FINAL_DECISION_PACK_NAME,
    )
    ensure_columns(
        frames["precursor_truth"],
        [
            "site",
            "panel_id",
            "preferred_precursor_onset_date",
            "operational_first_precursor_detected_date",
            "operational_first_precursor_marker_name",
            "interpretive_precursor_onset_date",
            "benchmark_precursor_onset_date",
        ],
        PRECURSOR_ONSET_TRUTH_NAME,
    )
    ensure_columns(
        frames["non_precursor_perf"],
        ["eval_bucket_v2", "site", "panel_id"],
        NON_PRECURSOR_PERFORMANCE_CASES_NAME,
    )
    ensure_columns(
        frames["common_cause"],
        [
            "eval_bucket_v2",
            "site",
            "panel_id",
            "current_marker_only_flag",
            "breadth_marker_only_flag",
            "combined_marker_flag",
        ],
        COMMON_CAUSE_RETROFIT_NAME,
    )
    ensure_columns(
        frames["gpvs_attach_inventory"],
        [
            "경로",
            "존재여부",
            "granularity_ko",
            "panel_id_컬럼존재_flag",
            "site_컬럼존재_flag",
            "panel_attach_candidate_flag",
            "attachability_note_ko",
            "note_ko",
        ],
        GPVS_ATTACH_INVENTORY_NAME,
    )
    ensure_columns(
        frames["gpvs_attach_feasibility"],
        [
            "GPVS_패널별_직접판정_가능여부",
            "근거_ko",
            "최선_후보_파일",
            "overlap_panel_count",
            "overlap_rate",
            "다음권장조치_ko",
        ],
        GPVS_ATTACH_FEASIBILITY_NAME,
    )
    ensure_columns(
        frames["gpvs_attach_candidates"],
        ["site", "panel_id", "GPVS_참고유형_ko", "source_path", "source_key_ko", "비고_ko"],
        GPVS_ATTACH_CANDIDATES_NAME,
    )
    ensure_columns(
        frames["consistency_cases"],
        ["site", "panel_id", "same_event_flag", "distinct_event_flag", "consistency_judgment_ko"],
        PRECURSOR_ABRUPT_CONSISTENCY_CASES_NAME,
    )
    ensure_columns(
        frames["consistency_summary"],
        ["overlap_panel_count", "same_event_count", "corrected_pure_abrupt_fault_count"],
        PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME,
    )
    ensure_columns(
        frames["consistency_recommendation"],
        ["recommended_next_handling", "rationale_ko"],
        PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME,
    )
    ensure_columns(frames["forensic_summary"], REQUIRED_FORENSIC_SUMMARY_COLS, FORENSIC_SUMMARY_NAME)
    ensure_columns(
        frames["fault_event_audit"],
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
        FAULT_PANEL_EVENT_AUDIT_NAME,
    )
    ensure_columns(
        frames["detailed_fault_bridge_audit"],
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
        DETAILED_FAULT_BRIDGE_AUDIT_NAME,
    )
    ensure_columns(
        frames["detailed_fault_bridge_summary"],
        [
            "고장패널수",
            "세부fault_부착수",
            "세부fault_보류수",
            "exact_date_match_패널수",
            "exact_date_conflict_패널수",
            "exact_date_miss_패널수",
            "note_ko",
        ],
        DETAILED_FAULT_BRIDGE_SUMMARY_NAME,
    )
    ensure_columns(
        frames["gpvs_bytype_rebuild_summary"],
        [
            "recovered_model_exported_flag",
            "recovered_feature_manifest_exported_flag",
            "recovered_model_source_ko",
            "parity_overall_status_ko",
            "current_recovered_attachable_flag",
            "note_ko",
        ],
        GPVS_BYTYPE_REBUILD_SUMMARY_NAME,
    )
    ensure_columns(
        frames["gpvs_detailed_type_audit"],
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
        GPVS_DETAILED_TYPE_INFERENCE_AUDIT_NAME,
    )
    ensure_columns(
        frames["gpvs_detailed_type_realpanel_sanity"],
        [
            "site",
            "panel_id",
            "gpvs_family_label",
            "gpvs_detailed_top1_fault_type",
            "single_type_collapse_flag",
            "attach_recommendation_ko",
        ],
        GPVS_DETAILED_TYPE_REALPANEL_SANITY_NAME,
    )
    ensure_columns(
        frames["gpvs_mlpe_panel_agreement"],
        [
            "site",
            "panel_id",
            "overall_gpvs_reference_usefulness_ko",
            "overall_gpvs_trust_note_ko",
        ],
        GPVS_MLPE_PANEL_AGREEMENT_NAME,
    )
    ensure_columns(
        frames["gpvs_canonical_dictionary"],
        [
            "canonical_gpvs_code",
            "current_usage_tier_ko",
            "mlpe_reference_name_ko",
            "usage_rule_ko",
            "note_ko",
        ],
        GPVS_CANONICAL_DICTIONARY_NAME,
    )
    ensure_columns(
        frames["gpvs_mlpe_fault_matching"],
        [
            "mlpe_official_fault_ko",
            "canonical_gpvs_code",
            "match_strength_ko",
            "match_role_ko",
            "recommendation_ko",
        ],
        GPVS_MLPE_FAULT_MATCHING_TABLE_NAME,
    )
    ensure_columns(
        frames["gpvs_mlpe_compatibility_summary"],
        [
            "fault_panel_count",
            "final_recommendation_ko",
            "note_ko",
        ],
        GPVS_MLPE_COMPATIBILITY_SUMMARY_NAME,
    )
    return normalize_frames(frames)


def validate_inputs(root: Path, frames: dict[str, pd.DataFrame]) -> None:
    workflow_df = frames["workflow"]
    kernel_map_df = frames["kernel_map"]
    final_pack_df = frames["final_pack"]

    preview_values = set(workflow_df["preview_attention_class"].tolist())
    if not PANEL_LEVEL_PREVIEW_CLASSES.issubset(preview_values):
        missing = sorted(PANEL_LEVEL_PREVIEW_CLASSES - preview_values)
        raise SystemExit(f"{WORKFLOW_DEFAULT_NAME} missing queue/watch rows: {missing}")

    required_kernel_symptoms = {"출력 저하형", "전압 변화형", "패턴 이상형", "불안정형", "복합형"}
    missing_symptoms = required_kernel_symptoms - set(kernel_map_df["커널로그_증상명"].tolist())
    if missing_symptoms:
        raise SystemExit(f"{KERNELLOG_PROJECT_MAPPING_NAME} missing required symptom rows: {sorted(missing_symptoms)}")

    final_scopes = set(final_pack_df["eval_scope"].tolist())
    missing_scopes = EXPECTED_FINAL_SCOPES - final_scopes
    if missing_scopes:
        raise SystemExit(f"{FINAL_DECISION_PACK_NAME} missing required scopes: {sorted(missing_scopes)}")

    feasibility_df = frames["gpvs_attach_feasibility"]
    if len(feasibility_df) != 1:
        raise SystemExit(f"{GPVS_ATTACH_FEASIBILITY_NAME} must contain exactly one row, found {len(feasibility_df)}")
    feasibility_value = normalize_text(feasibility_df.iloc[0]["GPVS_패널별_직접판정_가능여부"])
    if feasibility_value not in {"가능", "불가"}:
        raise SystemExit(
            f"{GPVS_ATTACH_FEASIBILITY_NAME} has invalid GPVS_패널별_직접판정_가능여부: {feasibility_value}"
        )
    overlap_value = pd.to_numeric(feasibility_df.iloc[0]["overlap_panel_count"], errors="coerce")
    if pd.isna(overlap_value):
        raise SystemExit(f"{GPVS_ATTACH_FEASIBILITY_NAME} overlap_panel_count must be numeric")
    candidates_df = frames["gpvs_attach_candidates"]
    if feasibility_value == "가능" and candidates_df.empty:
        raise SystemExit(f"{GPVS_ATTACH_CANDIDATES_NAME} is empty despite feasibility=가능")
    if feasibility_value == "불가" and not candidates_df.empty:
        raise SystemExit(f"{GPVS_ATTACH_CANDIDATES_NAME} must be empty when feasibility=불가")
    if not candidates_df.empty and candidates_df.duplicated(subset=["site", "panel_id"]).any():
        dup = candidates_df.loc[candidates_df.duplicated(subset=["site", "panel_id"], keep=False), ["site", "panel_id"]]
        raise SystemExit(f"{GPVS_ATTACH_CANDIDATES_NAME} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}")
    if frames["gpvs_attach_inventory"].empty:
        raise SystemExit(f"{GPVS_ATTACH_INVENTORY_NAME} must not be empty")
    if len(frames["detailed_fault_bridge_summary"]) != 1:
        raise SystemExit(
            f"{DETAILED_FAULT_BRIDGE_SUMMARY_NAME} must contain exactly one row, found {len(frames['detailed_fault_bridge_summary'])}"
        )
    if len(frames["gpvs_bytype_rebuild_summary"]) != 1:
        raise SystemExit(
            f"{GPVS_BYTYPE_REBUILD_SUMMARY_NAME} must contain exactly one row, found {len(frames['gpvs_bytype_rebuild_summary'])}"
        )
    if len(frames["gpvs_mlpe_compatibility_summary"]) != 1:
        raise SystemExit(
            f"{GPVS_MLPE_COMPATIBILITY_SUMMARY_NAME} must contain exactly one row, found {len(frames['gpvs_mlpe_compatibility_summary'])}"
        )
    compatibility_recommendation = normalize_text(
        frames["gpvs_mlpe_compatibility_summary"].iloc[0]["final_recommendation_ko"]
    )
    if compatibility_recommendation != "참고축으로만 사용":
        raise SystemExit(
            f"{GPVS_MLPE_COMPATIBILITY_SUMMARY_NAME} final_recommendation_ko must be 참고축으로만 사용, got {compatibility_recommendation or '<blank>'}"
        )
    canonical_codes = {
        normalize_text(value)
        for value in frames["gpvs_canonical_dictionary"]["canonical_gpvs_code"].tolist()
        if normalize_text(value)
    }
    missing_canonical_codes = sorted(set(GPVS_FRONT_PATTERN_NAME_MAP) - canonical_codes)
    if missing_canonical_codes:
        raise SystemExit(
            f"{GPVS_CANONICAL_DICTIONARY_NAME} missing canonical codes required by front-facing GPVS map: {missing_canonical_codes}"
        )


def load_same_event_overlap_keys(frames: dict[str, pd.DataFrame]) -> set[tuple[str, str]]:
    recommendation_df = frames["consistency_recommendation"]
    if len(recommendation_df) != 1:
        raise SystemExit(
            f"{PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME} must contain exactly one row, found {len(recommendation_df)}"
        )
    recommendation = normalize_text(recommendation_df.iloc[0]["recommended_next_handling"])
    if recommendation != "relabel_overlap_as_precursor_led_faults":
        raise SystemExit(
            "precursor/abrupt consistency recommendation must be relabel_overlap_as_precursor_led_faults for panel verdict reconciliation; "
            f"got {recommendation or '<blank>'}"
        )

    cases_df = frames["consistency_cases"]
    same_event_df = cases_df.loc[pd.to_numeric(cases_df["same_event_flag"], errors="coerce").fillna(0).eq(1)].copy()
    overlap_keys = {
        (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        for row in same_event_df.to_dict(orient="records")
        if normalize_text(row["site"]) and normalize_text(row["panel_id"])
    }
    summary_row = frames["consistency_summary"].iloc[0].to_dict()
    expected_overlap = int(pd.to_numeric(summary_row["overlap_panel_count"], errors="raise"))
    expected_same = int(pd.to_numeric(summary_row["same_event_count"], errors="raise"))
    corrected_pure_abrupt = int(pd.to_numeric(summary_row["corrected_pure_abrupt_fault_count"], errors="raise"))
    if expected_overlap != expected_same:
        raise SystemExit(
            f"{PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME} must keep overlap_panel_count == same_event_count for this reconciliation"
        )
    if len(overlap_keys) != expected_same:
        raise SystemExit(
            f"same-event overlap count mismatch between cases and summary: cases={len(overlap_keys)}, summary={expected_same}"
        )
    if len(overlap_keys) != 2:
        raise SystemExit(f"expected current same-event overlap panel count to be 2, found {len(overlap_keys)}")
    if corrected_pure_abrupt != 4:
        raise SystemExit(f"expected corrected pure abrupt fault count to be 4, found {corrected_pure_abrupt}")
    return overlap_keys


def load_forensic_rule_case(frames: dict[str, pd.DataFrame]) -> dict[str, str]:
    forensic_df = frames["forensic_summary"].copy()
    target_df = forensic_df.loc[
        forensic_df["site"].eq(FORENSIC_RULE_SITE)
        & forensic_df["panel_id"].eq(FORENSIC_RULE_PANEL_ID)
    ].copy()
    if len(target_df) != 1:
        raise SystemExit(
            f"{FORENSIC_SUMMARY_NAME} must contain exactly one target row for {FORENSIC_RULE_SITE}/{FORENSIC_RULE_PANEL_ID}, found {len(target_df)}"
        )
    row = {key: normalize_text(value) for key, value in target_df.iloc[0].to_dict().items()}
    onset_date = normalize_text(row.get("earliest_onset_date")) or normalize_text(row.get("전조흔적_시작일"))
    trigger_date = normalize_text(row.get("strong_trigger_date")) or normalize_text(row.get("강한트리거일"))
    if onset_date != FORENSIC_RULE_ONSET_DATE or trigger_date != FORENSIC_RULE_TRIGGER_DATE:
        raise SystemExit(
            f"{FORENSIC_SUMMARY_NAME} guard failed: expected onset/trigger {FORENSIC_RULE_ONSET_DATE}/{FORENSIC_RULE_TRIGGER_DATE}, got {onset_date}/{trigger_date}"
        )
    row["__forensic_onset_date"] = onset_date
    row["__forensic_trigger_date"] = trigger_date
    return row


def fault_event_audit_lookup(frames: dict[str, pd.DataFrame]) -> dict[tuple[str, str], dict[str, str]]:
    audit_df = frames["fault_event_audit"].copy()
    if audit_df.empty:
        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_NAME} must not be empty")
    if audit_df[["site", "panel_id"]].duplicated().any():
        dup = audit_df.loc[audit_df[["site", "panel_id"]].duplicated(keep=False), ["site", "panel_id"]]
        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_NAME} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}")

    lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in audit_df.to_dict(orient="records"):
        site = normalize_text(row["site"])
        panel_id = normalize_text(row["panel_id"])
        if site and panel_id:
            lookup[(site, panel_id)] = {key: normalize_text(value) for key, value in row.items()}
    if len(lookup) != 6:
        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_NAME} must contain current fault panel 6 rows, found {len(lookup)}")
    if (FORENSIC_RULE_SITE, FORENSIC_RULE_PANEL_ID) not in lookup:
        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_NAME} must contain forensic target panel row")
    return lookup


def abrupt_lookup(abrupt_df: pd.DataFrame) -> dict[tuple[str, str], dict[str, object]]:
    return {
        (normalize_text(row["site"]), normalize_text(row["panel_id"])): row
        for row in abrupt_df.to_dict(orient="records")
    }


def final_pack_lookup(final_pack_df: pd.DataFrame) -> dict[str, dict[str, object]]:
    return {
        normalize_text(row["eval_scope"]): row
        for row in final_pack_df.to_dict(orient="records")
    }


def build_workflow_panel_df(workflow_df: pd.DataFrame) -> pd.DataFrame:
    panel_df = workflow_df.loc[workflow_df["preview_attention_class"].isin(PANEL_LEVEL_PREVIEW_CLASSES)].copy()
    panel_df = panel_df.sort_values(["site", "display_entity_id", "display_score"], ascending=[True, True, False])
    return panel_df.drop_duplicates(subset=["site", "display_entity_id"], keep="first")


def build_cluster_df(workflow_df: pd.DataFrame) -> pd.DataFrame:
    cluster_df = workflow_df.loc[workflow_df["preview_attention_class"].eq(CLUSTER_PREVIEW_CLASS)].copy()
    if cluster_df.empty:
        return cluster_df
    cluster_df = cluster_df.sort_values(["site", "display_entity_id", "display_score"], ascending=[True, True, False])
    return cluster_df.drop_duplicates(subset=["site", "display_entity_id"], keep="first")


def panel_key_set(df: pd.DataFrame, site_col: str, panel_col: str) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for row in df.to_dict(orient="records"):
        site = normalize_text(row[site_col])
        panel_id = normalize_text(row[panel_col])
        if site and panel_id:
            keys.add((site, panel_id))
    return keys


def build_precursor_positive_keys(precursor_df: pd.DataFrame) -> set[tuple[str, str]]:
    panel_col = first_existing_column(
        precursor_df,
        ["panel_id", "display_entity_id", "entity_id", "panel_entity_id"],
        PRECURSOR_ONSET_TRUTH_NAME,
    )
    positive_df = precursor_df.loc[precursor_df["preferred_precursor_onset_date"].ne("")].copy()
    keys = panel_key_set(positive_df, "site", panel_col)
    if not keys:
        raise SystemExit(f"{PRECURSOR_ONSET_TRUTH_NAME} has no precursor-positive rows with preferred_precursor_onset_date")
    return keys


def precursor_truth_lookup(precursor_df: pd.DataFrame) -> dict[tuple[str, str], dict[str, str]]:
    panel_col = first_existing_column(
        precursor_df,
        ["panel_id", "display_entity_id", "entity_id", "panel_entity_id"],
        PRECURSOR_ONSET_TRUTH_NAME,
    )
    positive_df = precursor_df.loc[precursor_df["preferred_precursor_onset_date"].ne("")].copy()
    if positive_df[["site", panel_col]].duplicated().any():
        dup = positive_df.loc[positive_df[["site", panel_col]].duplicated(keep=False), ["site", panel_col]]
        raise SystemExit(f"{PRECURSOR_ONSET_TRUTH_NAME} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}")
    lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in positive_df.to_dict(orient="records"):
        key = (normalize_text(row["site"]), normalize_text(row[panel_col]))
        lookup[key] = {column: normalize_text(value) for column, value in row.items()}
    return lookup


def build_abrupt_eval_keys(non_precursor_df: pd.DataFrame) -> set[tuple[str, str]]:
    positive_df = non_precursor_df.loc[
        non_precursor_df["eval_bucket_v2"].eq("abrupt_or_no_precursor_now")
    ].copy()
    keys = panel_key_set(positive_df, "site", "panel_id")
    if not keys:
        raise SystemExit(
            f"{NON_PRECURSOR_PERFORMANCE_CASES_NAME} has no abrupt_or_no_precursor_now rows"
        )
    return keys


def build_common_cause_positive_keys(common_df: pd.DataFrame) -> set[tuple[str, str]]:
    marker_mask = (
        to_numeric_flag(common_df["current_marker_only_flag"]).eq(1)
        | to_numeric_flag(common_df["breadth_marker_only_flag"]).eq(1)
        | to_numeric_flag(common_df["combined_marker_flag"]).eq(1)
    )
    positive_df = common_df.loc[common_df["eval_bucket_v2"].eq("non_panel_or_common_cause") & marker_mask].copy()
    keys = panel_key_set(positive_df, "site", "panel_id")
    if not keys:
        raise SystemExit(
            f"{COMMON_CAUSE_RETROFIT_NAME} has no non_panel_or_common_cause positive rows with current/breadth/combined marker evidence"
        )
    return keys


def workflow_lookup(workflow_panel_df: pd.DataFrame) -> dict[tuple[str, str], dict[str, object]]:
    return {
        (normalize_text(row["site"]), normalize_text(row["display_entity_id"])): row
        for row in workflow_panel_df.to_dict(orient="records")
    }


def current_data_scope_note(
    event_type: str,
    terminal_pattern: str,
    final_pack_by_scope: dict[str, dict[str, object]],
) -> str:
    if event_type == "전조형 고장" and terminal_pattern == "급격 종료":
        return "이 panel은 전조형 사건 한 건이 마지막에 급격 종료로 끝난 것으로 읽는다. event type과 terminal failure pattern은 분리해서 해석해야 한다."
    scope = SCOPE_BY_EVENT_TYPE.get(event_type, "")
    if scope:
        final_row = final_pack_by_scope.get(scope, {})
        final_usage = normalize_text(final_row.get("final_usage_decision", ""))
        if final_usage == "bounded_reporting_use":
            return f"{event_type} 축은 current closeout 기준 bounded current-data 수준으로만 읽는다."
        if final_usage == "exploratory_only":
            return f"{event_type} 축은 current closeout 기준 exploratory 범위로만 읽는다."
    if event_type == "반복 이상":
        return "반복 이상은 chronic monitor/반복 lane 해석이며 stable fault classifier claim이 아니다."
    if event_type == "불충분":
        return "현재 stored positive universe와 직접 연결되지 않아 사건 성격을 보수적으로 유지한다."
    return "현재 저장 산출물만으로는 사건 성격 판정 근거가 제한적이다."


def event_type_and_terminal_pattern(
    flags: dict[str, int],
    *,
    is_same_event_overlap: bool,
    forensic_rule_case: dict[str, str] | None,
    fault_audit_row: dict[str, str] | None,
) -> tuple[str, str]:
    if fault_audit_row is not None:
        return (
            normalize_text(fault_audit_row["사건유형_재판정_ko"]) or "불충분",
            normalize_text(fault_audit_row["최종고장양상_재판정_ko"]) or "불충분",
        )
    if forensic_rule_case is not None:
        return (
            normalize_text(forensic_rule_case["사건유형_결정_ko"]) or "불충분",
            normalize_text(forensic_rule_case["최종고장양상_결정_ko"]) or "불충분",
        )
    if is_same_event_overlap:
        return ("전조형 고장", "급격 종료")
    if flags["has_급작고장"]:
        return ("급작 고장", "급작 발생")
    if flags["has_전조형고장"]:
        return ("전조형 고장", "진행성 악화")
    if flags["has_공통원인이벤트"]:
        return ("공통원인 이벤트", "해당없음")
    if flags["has_반복이상"]:
        return ("반복 이상", "해당없음")
    return ("불충분", "불충분")


def panel_fault_status_from_event_type(event_type: str) -> str:
    if event_type in {"전조형 고장", "급작 고장", "고장유형 보류"}:
        return "고장"
    if event_type == "공통원인 이벤트":
        return "비고장"
    return "미확정"


def gpvs_applicability_from_fault_status(panel_fault_status: str) -> str:
    return "적용대상" if panel_fault_status == "고장" else "비대상"


def event_history_text(
    flags: dict[str, int],
    *,
    is_same_event_overlap: bool,
    forensic_rule_case: dict[str, str] | None,
    fault_audit_row: dict[str, str] | None,
) -> str:
    if fault_audit_row is not None:
        event_type = normalize_text(fault_audit_row["사건유형_재판정_ko"])
        terminal_pattern = normalize_text(fault_audit_row["최종고장양상_재판정_ko"])
        if event_type == "급작 고장" and terminal_pattern == "급작 발생":
            return event_type
        if event_type == "전조형 고장" and terminal_pattern == "진행성 악화":
            return event_type
        if event_type and terminal_pattern and terminal_pattern not in {"불충분", "해당없음"}:
            return f"{event_type}({terminal_pattern})"
        return event_type
    if forensic_rule_case is not None:
        event_type = normalize_text(forensic_rule_case["사건유형_결정_ko"])
        terminal_pattern = normalize_text(forensic_rule_case["최종고장양상_결정_ko"])
        if event_type and terminal_pattern and terminal_pattern != "불충분":
            return f"{event_type}({terminal_pattern})"
        return event_type
    members: list[str] = []
    if flags["has_전조형고장"]:
        if is_same_event_overlap:
            members.append("전조형 고장(급격 종료)")
        else:
            members.append("전조형 고장")
    if flags["has_급작고장"]:
        members.append("급작 고장")
    if flags["has_공통원인이벤트"]:
        members.append("공통원인 이벤트")
    if flags["has_반복이상"]:
        members.append("반복 이상")
    return "+".join(members)


def interpretation_layer_fields(
    flags: dict[str, int],
    event_type: str,
    *,
    precursor_eval_flag: int,
    abrupt_eval_flag: int,
    is_same_event_overlap: bool,
    forensic_rule_case: dict[str, str] | None,
    fault_audit_row: dict[str, str] | None,
) -> dict[str, object]:
    def mismatch_text_for(event_type_ko: str, precursor_flag: int, abrupt_flag: int) -> str:
        if event_type_ko == "전조형 고장" and precursor_flag == 0:
            return "explicit rule상 전조형 고장이지만 현재 strict precursor evaluation set에는 아직 미편입"
        if event_type_ko == "급작 고장" and abrupt_flag == 0:
            return "explicit rule상 급작 고장이지만 현재 pure abrupt evaluation set에는 아직 미편입"
        return ""

    if fault_audit_row is not None:
        event_type_ko = normalize_text(fault_audit_row["사건유형_재판정_ko"]) or event_type
        return {
            "사건유형_해석_ko": event_type_ko,
            "전조흔적_flag": int(pd.to_numeric(pd.Series([fault_audit_row["전조흔적_flag"]]), errors="coerce").fillna(0).iloc[0]),
            "순수급작_flag": int(pd.to_numeric(pd.Series([fault_audit_row["순수급작_flag"]]), errors="coerce").fillna(0).iloc[0]),
            "전조평가셋편입_flag": precursor_eval_flag,
            "급작평가셋편입_flag": abrupt_eval_flag,
            "해석대평가차이_ko": mismatch_text_for(event_type_ko, precursor_eval_flag, abrupt_eval_flag),
        }
    if is_same_event_overlap:
        return {
            "사건유형_해석_ko": "전조형 고장",
            "전조흔적_flag": 1,
            "순수급작_flag": 0,
            "전조평가셋편입_flag": precursor_eval_flag,
            "급작평가셋편입_flag": abrupt_eval_flag,
            "해석대평가차이_ko": mismatch_text_for("전조형 고장", precursor_eval_flag, abrupt_eval_flag),
        }
    if forensic_rule_case is not None:
        event_type_ko = normalize_text(forensic_rule_case["사건유형_결정_ko"]) or event_type
        return {
            "사건유형_해석_ko": event_type_ko,
            "전조흔적_flag": 1,
            "순수급작_flag": 0,
            "전조평가셋편입_flag": precursor_eval_flag,
            "급작평가셋편입_flag": abrupt_eval_flag,
            "해석대평가차이_ko": mismatch_text_for(event_type_ko, precursor_eval_flag, abrupt_eval_flag),
        }
    if flags["has_급작고장"]:
        return {
            "사건유형_해석_ko": "급작 고장",
            "전조흔적_flag": 0,
            "순수급작_flag": 1,
            "전조평가셋편입_flag": precursor_eval_flag,
            "급작평가셋편입_flag": abrupt_eval_flag,
            "해석대평가차이_ko": mismatch_text_for("급작 고장", precursor_eval_flag, abrupt_eval_flag),
        }
    if flags["has_전조형고장"]:
        return {
            "사건유형_해석_ko": "전조형 고장",
            "전조흔적_flag": 1,
            "순수급작_flag": 0,
            "전조평가셋편입_flag": precursor_eval_flag,
            "급작평가셋편입_flag": abrupt_eval_flag,
            "해석대평가차이_ko": mismatch_text_for("전조형 고장", precursor_eval_flag, abrupt_eval_flag),
        }
    return {
        "사건유형_해석_ko": event_type,
        "전조흔적_flag": 0,
        "순수급작_flag": 0,
        "전조평가셋편입_flag": precursor_eval_flag,
        "급작평가셋편입_flag": abrupt_eval_flag,
        "해석대평가차이_ko": mismatch_text_for(event_type, precursor_eval_flag, abrupt_eval_flag),
    }


def map_kernel_axis(
    event_type: str,
    abrupt_row: dict[str, object] | None,
) -> tuple[str, str, str]:
    if abrupt_row is not None:
        specific = normalize_text(abrupt_row["증상명_ko"]) or "불충분"
        broad = SPECIFIC_TO_BROAD_SYMPTOM.get(specific, "불충분")
        note = (
            f"커널로그 원인군은 abrupt6 symptom map의 `{specific}` 를 연결했다."
            if specific != "불충분"
            else "abrupt6 direct map가 있지만 stored symptom name이 불충분하다."
        )
        return broad, specific, note

    if event_type == "전조형 고장":
        return "출력 저하형", "불충분", "전조형 representative verdict라 nearest symptom 축으로 출력 저하형만 부착했다."
    if event_type == "공통원인 이벤트":
        return "패턴 이상형", "불충분", "공통원인 representative verdict라 nearest symptom 축으로 패턴 이상형만 부착했다."
    if event_type == "반복 이상":
        return "불안정형", "불충분", "watch_now_panel 반복 lane이라 nearest symptom 축으로 불안정형만 부착했다."
    return "불충분", "불충분", "현재 stored field로 커널로그 증상축을 더 붙이기 어렵다."


def map_operating_location(workflow_row: dict[str, object] | None) -> str:
    if workflow_row is None:
        return "현재 workflow 미포함"
    preview_class = normalize_text(workflow_row["preview_attention_class"])
    if preview_class == "queue_run":
        return "바로 확인"
    if preview_class == "watch_now_panel":
        return "경과 관찰"
    return "현재 workflow 미포함"


def recover_gpvs_panel_level_reference_from_audit(
    feasibility_df: pd.DataFrame,
    candidates_df: pd.DataFrame,
    panel_keys: set[tuple[str, str]],
) -> tuple[dict[tuple[str, str], dict[str, str]], dict[str, str], int]:
    feasibility_row = feasibility_df.iloc[0]
    feasibility_value = normalize_text(feasibility_row["GPVS_패널별_직접판정_가능여부"])
    overlap_expected = int(pd.to_numeric(feasibility_row["overlap_panel_count"], errors="raise"))
    best_source = normalize_text(feasibility_row["최선_후보_파일"])
    feasibility_reason = normalize_text(feasibility_row["근거_ko"])

    if feasibility_value == "불가":
        return (
            {},
            {
                "feasibility": feasibility_value,
                "best_source": best_source,
                "feasibility_reason": feasibility_reason,
            },
            0,
        )

    gpvs_lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in candidates_df.to_dict(orient="records"):
        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        if key not in panel_keys:
            continue
        source_path = normalize_text(row["source_path"])
        source_key = normalize_text(row["source_key_ko"])
        note = normalize_text(row["비고_ko"])
        reason_parts = [part for part in [source_path, source_key, note] if part]
        gpvs_lookup[key] = {
            "GPVS_참고유형_ko": normalize_text(row["GPVS_참고유형_ko"]) or "미부착",
            "GPVS_근거_ko": " | ".join(reason_parts) if reason_parts else GPVS_ABSENCE_REASON,
            "GPVS_후보파일_ko": source_path,
        }

    return (
        gpvs_lookup,
        {
            "feasibility": feasibility_value,
            "best_source": best_source,
            "feasibility_reason": feasibility_reason,
        },
        overlap_expected,
    )


def gpvs_unattached_reason(
    inventory_df: pd.DataFrame,
    feasibility_meta: dict[str, str],
) -> str:
    feasibility_value = normalize_text(feasibility_meta.get("feasibility", ""))
    best_source = normalize_text(feasibility_meta.get("best_source", ""))
    inventory = inventory_df.copy()
    inventory["panel_attach_candidate_flag"] = to_numeric_flag(inventory["panel_attach_candidate_flag"])

    if feasibility_value == "가능" and (
        best_source
        or inventory["panel_attach_candidate_flag"].eq(1).any()
    ):
        return "GPVS 패널수준 후보 파일은 있으나 이 패널 key가 없음"

    key_poor_mask = inventory["panel_attach_candidate_flag"].eq(0) & inventory["granularity_ko"].isin(["유형수준", "집계수준"])
    if key_poor_mask.any():
        return "GPVS 결과는 있으나 패널수준 key가 없음"

    return "패널수준 GPVS 산출물 없음"


def detailed_fault_type_label(code: str) -> str:
    normalized = normalize_text(code)
    if len(normalized) >= 2 and normalized[0] == "F" and normalized[1].isdigit():
        family_idx = normalized[1]
        if family_idx in {"1", "2", "3", "4", "5", "6", "7"}:
            return f"GPVS Fault{family_idx}"
    return normalized


def detailed_fault_bridge_lookup(
    audit_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> tuple[dict[tuple[str, str], dict[str, str]], dict[str, int | str]]:
    if audit_df[["site", "panel_id"]].duplicated().any():
        dup = audit_df.loc[audit_df[["site", "panel_id"]].duplicated(keep=False), ["site", "panel_id"]]
        raise SystemExit(
            f"{DETAILED_FAULT_BRIDGE_AUDIT_NAME} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}"
        )
    lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in audit_df.to_dict(orient="records"):
        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        lookup[key] = {column: normalize_text(value) for column, value in row.items()}
    if len(lookup) != 6:
        raise SystemExit(f"{DETAILED_FAULT_BRIDGE_AUDIT_NAME} must contain current fault panel 6 rows, found {len(lookup)}")

    summary_row = summary_df.iloc[0]
    meta = {
        "fault_panel_count": int(pd.to_numeric(summary_row["고장패널수"], errors="raise")),
        "attached_count": int(pd.to_numeric(summary_row["세부fault_부착수"], errors="raise")),
        "held_count": int(pd.to_numeric(summary_row["세부fault_보류수"], errors="raise")),
        "exact_match_count": int(pd.to_numeric(summary_row["exact_date_match_패널수"], errors="raise")),
        "conflict_count": int(pd.to_numeric(summary_row["exact_date_conflict_패널수"], errors="raise")),
        "miss_count": int(pd.to_numeric(summary_row["exact_date_miss_패널수"], errors="raise")),
        "note_ko": normalize_text(summary_row["note_ko"]),
    }
    if meta["fault_panel_count"] != 6:
        raise SystemExit(f"{DETAILED_FAULT_BRIDGE_SUMMARY_NAME} 고장패널수 must be 6, found {meta['fault_panel_count']}")
    return lookup, meta


def gpvs_detailed_type_attachment_lookup(
    audit_df: pd.DataFrame,
    sanity_df: pd.DataFrame,
    rebuild_summary_df: pd.DataFrame,
) -> tuple[dict[tuple[str, str], dict[str, str]], dict[str, int | str]]:
    if audit_df[["site", "panel_id"]].duplicated().any():
        dup = audit_df.loc[audit_df[["site", "panel_id"]].duplicated(keep=False), ["site", "panel_id"]]
        raise SystemExit(
            f"{GPVS_DETAILED_TYPE_INFERENCE_AUDIT_NAME} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}"
        )
    if sanity_df[["site", "panel_id"]].duplicated().any():
        dup = sanity_df.loc[sanity_df[["site", "panel_id"]].duplicated(keep=False), ["site", "panel_id"]]
        raise SystemExit(
            f"{GPVS_DETAILED_TYPE_REALPANEL_SANITY_NAME} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}"
        )

    audit_lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in audit_df.to_dict(orient="records"):
        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        audit_lookup[key] = {column: normalize_text(value) for column, value in row.items()}
    sanity_lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in sanity_df.to_dict(orient="records"):
        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        sanity_lookup[key] = {column: normalize_text(value) for column, value in row.items()}

    if len(audit_lookup) != 6:
        raise SystemExit(f"{GPVS_DETAILED_TYPE_INFERENCE_AUDIT_NAME} must contain current fault panel 6 rows, found {len(audit_lookup)}")
    if len(sanity_lookup) != 6:
        raise SystemExit(f"{GPVS_DETAILED_TYPE_REALPANEL_SANITY_NAME} must contain current fault panel 6 rows, found {len(sanity_lookup)}")

    summary_row = rebuild_summary_df.iloc[0]
    attachable_flag = int(pd.to_numeric(summary_row["current_recovered_attachable_flag"], errors="raise"))
    recovered_exported_flag = int(pd.to_numeric(summary_row["recovered_model_exported_flag"], errors="raise"))
    parity_status = normalize_text(summary_row["parity_overall_status_ko"])
    note_ko = normalize_text(summary_row["note_ko"])

    lookup: dict[tuple[str, str], dict[str, str]] = {}
    attached_expected = 0
    deferred_expected = 0
    for key, audit_row in audit_lookup.items():
        sanity_row = sanity_lookup.get(key)
        attach_recommendation = normalize_text((sanity_row or {}).get("attach_recommendation_ko", ""))
        model_source = normalize_text(audit_row.get("gpvs_detailed_model_source", ""))
        guard_ok = (
            attachable_flag == 1
            and model_source == "recovered_artifact"
            and attach_recommendation == "attach_ok"
        )
        merged = dict(audit_row)
        merged["attach_recommendation_ko"] = attach_recommendation
        merged["__guard_ok"] = "1" if guard_ok else "0"
        lookup[key] = merged
        if guard_ok:
            attached_expected += 1
        else:
            deferred_expected += 1

    return lookup, {
        "fault_panel_count": 6,
        "attached_count": attached_expected,
        "deferred_count": deferred_expected,
        "recovered_exported_flag": recovered_exported_flag,
        "attachable_flag": attachable_flag,
        "parity_status_ko": parity_status,
        "note_ko": note_ko,
    }


def gpvs_reference_front_lookup(
    panel_agreement_df: pd.DataFrame,
) -> dict[tuple[str, str], dict[str, str]]:
    if panel_agreement_df[["site", "panel_id"]].duplicated().any():
        dup = panel_agreement_df.loc[
            panel_agreement_df[["site", "panel_id"]].duplicated(keep=False),
            ["site", "panel_id"],
        ]
        raise SystemExit(
            f"{GPVS_MLPE_PANEL_AGREEMENT_NAME} must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}"
        )
    lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in panel_agreement_df.to_dict(orient="records"):
        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        lookup[key] = {column: normalize_text(value) for column, value in row.items()}
    return lookup


def build_outputs(
    root: Path,
    frames: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, int | str], dict[str, str]]:
    workflow_panel_df = build_workflow_panel_df(frames["workflow"])
    cluster_df = build_cluster_df(frames["workflow"])
    workflow_by_key = workflow_lookup(workflow_panel_df)
    abrupt_by_key = abrupt_lookup(frames["abrupt6"])
    final_pack_by_scope = final_pack_lookup(frames["final_pack"])
    same_event_overlap_keys = load_same_event_overlap_keys(frames)
    forensic_rule_case = load_forensic_rule_case(frames)
    fault_audit_by_key = fault_event_audit_lookup(frames)
    detailed_fault_by_key, detailed_fault_meta = detailed_fault_bridge_lookup(
        frames["detailed_fault_bridge_audit"],
        frames["detailed_fault_bridge_summary"],
    )
    gpvs_detailed_type_by_key, gpvs_detailed_type_meta = gpvs_detailed_type_attachment_lookup(
        frames["gpvs_detailed_type_audit"],
        frames["gpvs_detailed_type_realpanel_sanity"],
        frames["gpvs_bytype_rebuild_summary"],
    )
    gpvs_reference_front_by_key = gpvs_reference_front_lookup(frames["gpvs_mlpe_panel_agreement"])
    precursor_truth_by_key = precursor_truth_lookup(frames["precursor_truth"])
    forensic_rule_key = (FORENSIC_RULE_SITE, FORENSIC_RULE_PANEL_ID)

    workflow_keys = set(workflow_by_key.keys())
    abrupt_keys = set(abrupt_by_key.keys())
    pure_abrupt_keys = abrupt_keys - same_event_overlap_keys - {forensic_rule_key}
    precursor_keys = build_precursor_positive_keys(frames["precursor_truth"])
    precursor_eval_keys = precursor_keys
    abrupt_eval_keys = build_abrupt_eval_keys(frames["non_precursor_perf"])
    common_keys = build_common_cause_positive_keys(frames["common_cause"])
    workflow_watch_keys = {
        (normalize_text(row["site"]), normalize_text(row["display_entity_id"]))
        for row in workflow_panel_df.loc[workflow_panel_df["preview_attention_class"].eq("watch_now_panel")].to_dict(orient="records")
    }
    panel_keys = set().union(workflow_keys, abrupt_keys, precursor_keys, common_keys)
    if not same_event_overlap_keys.issubset(abrupt_keys):
        raise SystemExit("same-event overlap panels must be included in abrupt symptom map universe")
    if not same_event_overlap_keys.issubset(precursor_keys):
        raise SystemExit("same-event overlap panels must be included in precursor-positive universe")
    if forensic_rule_key not in abrupt_keys:
        raise SystemExit("forensic target panel must remain in abrupt symptom map universe")

    gpvs_by_key, gpvs_feasibility_meta, gpvs_expected_attach_count = recover_gpvs_panel_level_reference_from_audit(
        frames["gpvs_attach_feasibility"],
        frames["gpvs_attach_candidates"],
        panel_keys,
    )
    gpvs_default_unattached_reason = gpvs_unattached_reason(
        frames["gpvs_attach_inventory"],
        gpvs_feasibility_meta,
    )
    gpvs_best_source = normalize_text(gpvs_feasibility_meta.get("best_source", ""))
    gpvs_expected_attach_count_applicable = 0

    panel_rows: list[dict[str, object]] = []
    event_rows: list[dict[str, object]] = []

    for site, panel_id in sorted(panel_keys):
        key = (site, panel_id)
        workflow_row = workflow_by_key.get(key)
        abrupt_row = abrupt_by_key.get(key)
        precursor_truth_row = precursor_truth_by_key.get(key)
        is_same_event_overlap = key in same_event_overlap_keys
        active_forensic_rule_case = forensic_rule_case if key == forensic_rule_key else None
        active_fault_audit_row = fault_audit_by_key.get(key)
        precursor_eval_flag = int(key in precursor_eval_keys)
        abrupt_eval_flag = int(key in abrupt_eval_keys)
        flags = {
            "has_전조형고장": int(key in precursor_keys),
            "has_급작고장": int(key in pure_abrupt_keys),
            "has_공통원인이벤트": int(key in common_keys),
            "has_반복이상": int(key in workflow_watch_keys),
        }

        event_type, terminal_pattern = event_type_and_terminal_pattern(
            flags,
            is_same_event_overlap=is_same_event_overlap,
            forensic_rule_case=active_forensic_rule_case,
            fault_audit_row=active_fault_audit_row,
        )
        representative_verdict = event_type
        history = event_history_text(
            flags,
            is_same_event_overlap=is_same_event_overlap,
            forensic_rule_case=active_forensic_rule_case,
            fault_audit_row=active_fault_audit_row,
        )
        interpretation = interpretation_layer_fields(
            flags,
            event_type,
            precursor_eval_flag=precursor_eval_flag,
            abrupt_eval_flag=abrupt_eval_flag,
            is_same_event_overlap=is_same_event_overlap,
            forensic_rule_case=active_forensic_rule_case,
            fault_audit_row=active_fault_audit_row,
        )
        operational_first_precursor_detected_date = ""
        operational_first_precursor_marker_name = ""
        interpretive_precursor_onset_date = ""
        benchmark_precursor_onset_date = ""
        if precursor_truth_row is not None and panel_fault_status_from_event_type(event_type) == "고장":
            operational_first_precursor_detected_date = normalize_text(
                precursor_truth_row.get("operational_first_precursor_detected_date", "")
            )
            operational_first_precursor_marker_name = normalize_text(
                precursor_truth_row.get("operational_first_precursor_marker_name", "")
            )
            interpretive_precursor_onset_date = normalize_text(
                precursor_truth_row.get("interpretive_precursor_onset_date", "")
            )
            benchmark_precursor_onset_date = (
                normalize_text(precursor_truth_row.get("benchmark_precursor_onset_date", ""))
                or normalize_text(precursor_truth_row.get("preferred_precursor_onset_date", ""))
            )
        panel_fault_status = panel_fault_status_from_event_type(event_type)
        gpvs_applicability = gpvs_applicability_from_fault_status(panel_fault_status)
        kernel_symptom, kernel_cause_group, kernel_note = map_kernel_axis(event_type, abrupt_row)

        gpvs_row = gpvs_by_key.get(key)
        if gpvs_applicability == "비대상":
            gpvs_attach_status = "비대상"
            gpvs_type = "비대상"
            gpvs_reason = ""
            gpvs_unattached_note = GPVS_NON_TARGET_REASON
            gpvs_candidate_file = ""
        else:
            if gpvs_row is None:
                gpvs_attach_status = "미부착"
                gpvs_type = "미부착"
                gpvs_reason = GPVS_ABSENCE_REASON
                gpvs_unattached_note = gpvs_default_unattached_reason
                gpvs_candidate_file = gpvs_best_source
            else:
                gpvs_attach_status = "부착"
                gpvs_type = normalize_text(gpvs_row["GPVS_참고유형_ko"]) or "미부착"
                gpvs_reason = normalize_text(gpvs_row["GPVS_근거_ko"]) or GPVS_ABSENCE_REASON
                gpvs_unattached_note = ""
                gpvs_candidate_file = normalize_text(gpvs_row.get("GPVS_후보파일_ko", "")) or gpvs_best_source
                gpvs_expected_attach_count_applicable += 1

        detailed_fault_row = detailed_fault_by_key.get(key)
        if panel_fault_status == "고장":
            if detailed_fault_row is None:
                raise SystemExit(f"{DETAILED_FAULT_BRIDGE_AUDIT_NAME} missing fault panel row for {site}/{panel_id}")
            detailed_attachable = int(
                pd.to_numeric(pd.Series([detailed_fault_row["attachable_flag"]]), errors="coerce").fillna(0).iloc[0]
            )
            detailed_reference_date = normalize_text(detailed_fault_row["reference_date"])
            detailed_files = normalize_text(detailed_fault_row["matched_files_csv"])
            detailed_code = normalize_text(detailed_fault_row["consensus_fault_type_code"])
            detailed_reason = normalize_text(detailed_fault_row["attach_reason_ko"])
            if detailed_attachable == 1 and detailed_code:
                detailed_status = "부착"
                detailed_label = detailed_fault_type_label(detailed_code)
                detailed_hold_reason = ""
            else:
                detailed_status = "보류"
                detailed_code = ""
                detailed_label = ""
                detailed_hold_reason = detailed_reason
        else:
            detailed_status = "비대상"
            detailed_code = ""
            detailed_label = ""
            detailed_files = ""
            detailed_reference_date = ""
            detailed_hold_reason = ""

        gpvs_detailed_row = gpvs_detailed_type_by_key.get(key)
        if panel_fault_status == "고장":
            attach_guard_ok = gpvs_detailed_row is not None and normalize_text(gpvs_detailed_row.get("__guard_ok")) == "1"
            if attach_guard_ok:
                gpvs_detailed_code = normalize_text(gpvs_detailed_row["gpvs_detailed_top1_fault_type"])
                gpvs_detailed_score = normalize_text(gpvs_detailed_row["gpvs_detailed_top1_score"])
                gpvs_detailed_rank2 = normalize_text(gpvs_detailed_row["gpvs_detailed_top2_fault_type"])
                gpvs_detailed_rank2_score = normalize_text(gpvs_detailed_row["gpvs_detailed_top2_score"])
                gpvs_detailed_margin = normalize_text(gpvs_detailed_row["gpvs_detailed_margin"])
                gpvs_detailed_attach_status = "부착"
                gpvs_detailed_reason = "recovered_artifact by-type inference"
                gpvs_detailed_caution = "family와 detailed type은 별도 축"
            else:
                gpvs_detailed_code = ""
                gpvs_detailed_score = ""
                gpvs_detailed_rank2 = ""
                gpvs_detailed_rank2_score = ""
                gpvs_detailed_margin = ""
                gpvs_detailed_attach_status = "판정유보"
                gpvs_detailed_reason = "attach guard 미충족"
                gpvs_detailed_caution = ""
            gpvs_detailed_status = gpvs_detailed_attach_status
        else:
            gpvs_detailed_code = ""
            gpvs_detailed_score = ""
            gpvs_detailed_rank2 = ""
            gpvs_detailed_rank2_score = ""
            gpvs_detailed_margin = ""
            gpvs_detailed_status = "비대상"
            gpvs_detailed_attach_status = "비대상"
            gpvs_detailed_reason = ""
            gpvs_detailed_caution = ""

        universe_parts: list[str] = []
        if flags["has_전조형고장"]:
            universe_parts.append("precursor onset truth positive universe 포함")
        if flags["has_급작고장"]:
            universe_parts.append("abrupt6 positive universe 포함")
        if flags["has_공통원인이벤트"]:
            universe_parts.append("common-cause descriptive positive universe 포함")
        if flags["has_반복이상"]:
            universe_parts.append("workflow watch_now_panel 포함")
        if active_forensic_rule_case is not None:
            universe_parts.append("single-panel forensic explicit rule 적용")
        if active_fault_audit_row is not None:
            universe_parts.append("fault panel event audit explicit rule 적용")
        if workflow_row is None:
            universe_parts.append("현재 workflow default row에는 아직 없음")
        if not universe_parts:
            universe_parts.append("workflow current row 기반 fallback verdict")

        caution_parts = [
            current_data_scope_note(event_type, terminal_pattern, final_pack_by_scope),
            kernel_note,
            f"사건유형={event_type}, 최종고장양상={terminal_pattern}",
            f"사건이력={history}" if history else "사건이력 없음",
            "; ".join(universe_parts),
        ]
        if gpvs_attach_status == "미부착":
            caution_parts.append(gpvs_unattached_note or GPVS_ABSENCE_REASON)
        if gpvs_attach_status == "비대상":
            caution_parts.append(GPVS_NON_TARGET_REASON)
        if detailed_status == "부착":
            caution_parts.append(f"세부fault_type={detailed_label} ({detailed_code}) exact-date consensus 부착")
        elif detailed_status == "보류":
            caution_parts.append(f"세부fault_type 보류={detailed_hold_reason or 'unknown'}")
        if gpvs_detailed_attach_status == "부착":
            gpvs_detailed_score_part = f", score={gpvs_detailed_score}" if gpvs_detailed_score else ""
            gpvs_detailed_margin_part = f", margin={gpvs_detailed_margin}" if gpvs_detailed_margin else ""
            caution_parts.append(
                f"GPVS learned by-type 세부fault={gpvs_detailed_code}{gpvs_detailed_score_part}{gpvs_detailed_margin_part}"
            )
        elif gpvs_detailed_attach_status == "판정유보":
            caution_parts.append(f"GPVS learned by-type 세부fault 판정유보={gpvs_detailed_reason or 'unknown'}")
        if active_fault_audit_row is not None:
            caution_parts.append(
                f"fault panel event audit 재판정={normalize_text(active_fault_audit_row['사건유형_재판정_ko'])}/{normalize_text(active_fault_audit_row['최종고장양상_재판정_ko'])}"
            )
            caution_parts.append(normalize_text(active_fault_audit_row["재판정_근거_ko"]))
        if active_forensic_rule_case is not None:
            caution_parts.append(
                f"explicit stored-field rule onset={normalize_text(active_forensic_rule_case.get('__forensic_onset_date')) or FORENSIC_RULE_ONSET_DATE}, "
                f"trigger={normalize_text(active_forensic_rule_case.get('__forensic_trigger_date')) or FORENSIC_RULE_TRIGGER_DATE}"
            )
            caution_parts.append(FORENSIC_RULE_REASON)
            caution_parts.append(
                f"현재 재감사 family hint={forensic_rule_case['현재_재감사라벨_ko']}"
            )
        onset_split_parts = []
        if operational_first_precursor_detected_date:
            onset_split_parts.append(
                f"운영상 최초 전조 발견={operational_first_precursor_detected_date}"
                + (f" ({operational_first_precursor_marker_name})" if operational_first_precursor_marker_name else "")
            )
        if interpretive_precursor_onset_date:
            onset_split_parts.append(f"사건 해석상 전조 시작={interpretive_precursor_onset_date}")
        if benchmark_precursor_onset_date:
            onset_split_parts.append(f"benchmark 전조 시작={benchmark_precursor_onset_date}")
        if onset_split_parts:
            caution_parts.append(" / ".join(onset_split_parts))
        if normalize_text(interpretation["해석대평가차이_ko"]):
            caution_parts.append(normalize_text(interpretation["해석대평가차이_ko"]))
        gpvs_scenario_info = gpvs_scenario_fields(gpvs_detailed_code)
        gpvs_reference_front_row = gpvs_reference_front_by_key.get(key)
        if panel_fault_status == "고장" and gpvs_reference_front_row is None:
            raise SystemExit(f"{GPVS_MLPE_PANEL_AGREEMENT_NAME} missing fault panel row for {site}/{panel_id}")
        gpvs_front_fields = gpvs_front_facing_fields(
            panel_fault_status=panel_fault_status,
            gpvs_type=gpvs_type,
            gpvs_detailed_code=gpvs_detailed_code,
            panel_agreement_row=gpvs_reference_front_row,
        )

        panel_rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "사건유형_ko": event_type,
                "사건유형_해석_ko": interpretation["사건유형_해석_ko"],
                "최종고장양상_ko": terminal_pattern,
                "대표판정_ko": representative_verdict,
                "사건이력_ko": history,
                "전조흔적_flag": interpretation["전조흔적_flag"],
                "순수급작_flag": interpretation["순수급작_flag"],
                "전조평가셋편입_flag": interpretation["전조평가셋편입_flag"],
                "급작평가셋편입_flag": interpretation["급작평가셋편입_flag"],
                "해석대평가차이_ko": interpretation["해석대평가차이_ko"],
                "운영최초전조발견일": operational_first_precursor_detected_date,
                "운영최초전조마커": operational_first_precursor_marker_name,
                "사건해석상전조시작일": interpretive_precursor_onset_date,
                "benchmark전조시작일": benchmark_precursor_onset_date,
                "전조형이력_flag": flags["has_전조형고장"],
                "급작고장이력_flag": flags["has_급작고장"],
                "공통원인이력_flag": flags["has_공통원인이벤트"],
                "반복이상이력_flag": flags["has_반복이상"],
                "패널고장여부_ko": panel_fault_status,
                "GPVS_적용대상_ko": gpvs_applicability,
                "커널로그_증상명_ko": kernel_symptom,
                "커널로그_원인군_ko": kernel_cause_group,
                "GPVS_부착상태_ko": gpvs_attach_status,
                "GPVS_내부참고유형_ko": gpvs_front_fields["GPVS_내부참고유형_ko"],
                "GPVS_외부참조패턴_ko": gpvs_front_fields["GPVS_외부참조패턴_ko"],
                "GPVS_참조사용등급_ko": gpvs_front_fields["GPVS_참조사용등급_ko"],
                "GPVS_참조설명_ko": gpvs_front_fields["GPVS_참조설명_ko"],
                "GPVS_참고유형_ko": gpvs_type,
                "GPVS_근거_ko": gpvs_reason,
                "GPVS_미부착사유_ko": gpvs_unattached_note,
                "GPVS_후보파일_ko": gpvs_candidate_file,
                "GPVS_세부fault_code": gpvs_detailed_code,
                "GPVS_세부fault_score": gpvs_detailed_score,
                "GPVS_세부fault_rank2_code": gpvs_detailed_rank2,
                "GPVS_세부fault_rank2_score": gpvs_detailed_rank2_score,
                "GPVS_세부fault_margin": gpvs_detailed_margin,
                "GPVS_세부fault_status_ko": gpvs_detailed_status,
                "GPVS_세부fault_부착상태_ko": gpvs_detailed_attach_status,
                "GPVS_세부fault_근거_ko": gpvs_detailed_reason,
                "GPVS_세부fault_판정주의_ko": gpvs_detailed_caution,
                "GPVS_시나리오_family_ko": gpvs_scenario_info["GPVS_시나리오_family_ko"],
                "GPVS_시나리오명_ko": gpvs_scenario_info["GPVS_시나리오명_ko"],
                "GPVS_시나리오_고장상황설명_ko": gpvs_scenario_info["GPVS_시나리오_고장상황설명_ko"],
                "GPVS_운전모드_ko": gpvs_scenario_info["GPVS_운전모드_ko"],
                "GPVS_해석주의_ko": gpvs_scenario_info["GPVS_해석주의_ko"],
                "세부fault_type_code": detailed_code,
                "세부fault_type_label_ko": detailed_label,
                "세부fault_부착상태_ko": detailed_status,
                "세부fault_근거파일_ko": detailed_files,
                "세부fault_기준일": detailed_reference_date,
                "세부fault_보류사유_ko": detailed_hold_reason,
                "운영위치_ko": map_operating_location(workflow_row),
                "판정주의_ko": " ".join(part for part in caution_parts if part),
            }
        )

        event_members: list[tuple[str, str]] = []
        if active_fault_audit_row is not None:
            event_members.append(
                (
                    normalize_text(active_fault_audit_row["사건유형_재판정_ko"]) or event_type,
                    "fault panel event audit explicit stored-field rule 기준 대표사건",
                )
            )
        elif active_forensic_rule_case is not None:
            event_members.append(
                (
                    normalize_text(active_forensic_rule_case["사건유형_결정_ko"]) or event_type,
                    "single-panel forensic explicit stored-field rule 기준 대표사건",
                )
            )
        elif flags["has_전조형고장"]:
            if is_same_event_overlap:
                event_members.append(("전조형 고장", "같은 사건 audit 기준 최종고장양상=급격 종료"))
            else:
                event_members.append(("전조형 고장", "stored precursor positive universe 포함"))
        if flags["has_급작고장"]:
            event_members.append(("급작 고장", "stored pure abrupt positive universe 포함"))
        if flags["has_공통원인이벤트"]:
            event_members.append(("공통원인 이벤트", "stored common-cause positive universe 포함"))
        if flags["has_반복이상"]:
            event_members.append(("반복 이상", "workflow watch_now_panel 포함"))

        deduped_event_members: list[tuple[str, str]] = []
        seen_event_names: set[str] = set()
        for event_name, event_note in event_members:
            if event_name in seen_event_names:
                continue
            seen_event_names.add(event_name)
            deduped_event_members.append((event_name, event_note))

        for event_name, event_note in deduped_event_members:
            if not history:
                break
            event_rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "사건유형_ko": event_name,
                    "사건우선순위": EVENT_PRIORITY[event_name],
                    "대표판정여부_flag": int(event_name == representative_verdict),
                    "운영위치_ko": map_operating_location(workflow_row),
                    "비고_ko": (
                        "대표판정과 동일"
                        if event_name == representative_verdict
                        else f"대표판정은 `{representative_verdict}` 이고 이 row는 사건이력 보존용"
                    ),
                }
            )
            if event_note:
                event_rows[-1]["비고_ko"] = (
                    f"{event_rows[-1]['비고_ko']}; {event_note}"
                    if normalize_text(event_rows[-1]["비고_ko"])
                    else event_note
                )

    cluster_rows: list[dict[str, str]] = []
    for row in cluster_df.to_dict(orient="records"):
        cluster_rows.append(
            {
                "site": normalize_text(row["site"]),
                "cluster_id": normalize_text(row["display_entity_id"]),
                "대표판정_ko": "공통원인 이벤트",
                "커널로그_증상명_ko": "패턴 이상형",
                "GPVS_참고유형_ko": "미부착",
                "GPVS_근거_ko": GPVS_ABSENCE_REASON,
                "운영위치_ko": "추가 발견 후보",
                "판정주의_ko": "secondary discovery cluster 보조 row이며 panel-level 개별 verdict로 확장하지 않는다. "
                + GPVS_ABSENCE_REASON,
            }
        )

    verdict_internal_df = pd.DataFrame(panel_rows)
    verdict_df = verdict_internal_df.reindex(columns=VERDICT_COLS)
    event_supplement_df = pd.DataFrame(event_rows).reindex(columns=EVENT_SUPPLEMENT_COLS)
    cluster_supplement_df = pd.DataFrame(cluster_rows).reindex(columns=CLUSTER_COLS)

    if verdict_df.empty:
        raise SystemExit("panel-level representative verdict table is empty")

    metrics = {
        "workflow_panel_count": len(workflow_keys),
        "workflow_cluster_count": len(cluster_df),
        "abrupt_fault6_total": len(abrupt_keys),
        "pure_abrupt_expected": len(pure_abrupt_keys),
        "same_event_overlap_expected": len(same_event_overlap_keys),
        "forensic_rule_expected": 1,
        "fault_audit_expected": len(fault_audit_by_key),
        "precursor_expected": len(precursor_keys),
        "precursor_eval_expected": len(precursor_eval_keys),
        "abrupt_eval_expected": len(abrupt_eval_keys),
        "common_expected": len(common_keys),
        "gpvs_expected_attach_count": gpvs_expected_attach_count_applicable,
        "gpvs_detailed_attached_expected": int(gpvs_detailed_type_meta["attached_count"]),
        "gpvs_detailed_deferred_expected": int(gpvs_detailed_type_meta["deferred_count"]),
        "gpvs_detailed_impossible_expected": 0,
        "gpvs_detailed_note": str(gpvs_detailed_type_meta["note_ko"]),
        "detailed_fault_attached_expected": int(detailed_fault_meta["attached_count"]),
        "detailed_fault_held_expected": int(detailed_fault_meta["held_count"]),
        "detailed_fault_exact_match_expected": int(detailed_fault_meta["exact_match_count"]),
        "detailed_fault_conflict_expected": int(detailed_fault_meta["conflict_count"]),
        "detailed_fault_miss_expected": int(detailed_fault_meta["miss_count"]),
        "detailed_fault_note": str(detailed_fault_meta["note_ko"]),
    }
    return verdict_df, verdict_internal_df, event_supplement_df, cluster_supplement_df, metrics, gpvs_feasibility_meta


def compute_final_row_counts(verdict_df: pd.DataFrame) -> dict[str, int]:
    abrupt_flags = to_numeric_flag(verdict_df["급작고장이력_flag"]).astype(int)
    precursor_flags = to_numeric_flag(verdict_df["전조형이력_flag"]).astype(int)
    common_flags = to_numeric_flag(verdict_df["공통원인이력_flag"]).astype(int)
    repeat_flags = to_numeric_flag(verdict_df["반복이상이력_flag"]).astype(int)
    precursor_trace_flags = to_numeric_flag(verdict_df["전조흔적_flag"]).astype(int)
    pure_abrupt_flags = to_numeric_flag(verdict_df["순수급작_flag"]).astype(int)
    precursor_eval_flags = to_numeric_flag(verdict_df["전조평가셋편입_flag"]).astype(int)
    abrupt_eval_flags = to_numeric_flag(verdict_df["급작평가셋편입_flag"]).astype(int)
    event_type_counts = verdict_df["사건유형_ko"].value_counts().to_dict()
    panel_fault_counts = verdict_df["패널고장여부_ko"].value_counts().to_dict()
    interpretation_eval_mismatch_count = int(verdict_df["해석대평가차이_ko"].map(normalize_text).ne("").sum())

    abrupt_ending_mask = verdict_df["최종고장양상_ko"].eq("급격 종료") & verdict_df["사건유형_ko"].eq("전조형 고장")
    progressive_precursor_mask = verdict_df["사건유형_ko"].eq("전조형 고장") & verdict_df["최종고장양상_ko"].eq("진행성 악화")
    interpreted_precursor_mask = verdict_df["사건유형_ko"].eq("전조형 고장")
    interpreted_abrupt_mask = verdict_df["사건유형_ko"].eq("급작 고장")

    return {
        "전체_패널수": int(len(verdict_df)),
        "고유_고장패널수": int(verdict_df["패널고장여부_ko"].eq("고장").sum()),
        "사건해석_전조형_패널수": int(interpreted_precursor_mask.sum()),
        "사건해석_급작_패널수": int(interpreted_abrupt_mask.sum()),
        "사건해석_전조형_급격종료_패널수": int(abrupt_ending_mask.sum()),
        "사건해석_전조형_진행성악화_패널수": int(progressive_precursor_mask.sum()),
        "전조흔적_패널수": int(precursor_trace_flags.sum()),
        "엄격전조평가셋_패널수": int(precursor_eval_flags.sum()),
        "순수급작평가셋_패널수": int(abrupt_eval_flags.sum()),
        "해석과평가셋불일치_패널수": interpretation_eval_mismatch_count,
        "공통원인이력_패널수": int(common_flags.sum()),
        "반복이상이력_패널수": int(repeat_flags.sum()),
        "대표판정_급작수": int(event_type_counts.get("급작 고장", 0)),
        "대표판정_전조형수": int(event_type_counts.get("전조형 고장", 0)),
        "대표판정_공통원인수": int(event_type_counts.get("공통원인 이벤트", 0)),
        "대표판정_반복이상수": int(event_type_counts.get("반복 이상", 0)),
        "대표판정_고장유형보류수": int(event_type_counts.get("고장유형 보류", 0)),
        "대표판정_불충분수": int(event_type_counts.get("불충분", 0)),
        "고장_패널수": int(panel_fault_counts.get("고장", 0)),
        "비고장_패널수": int(panel_fault_counts.get("비고장", 0)),
        "미확정_패널수": int(panel_fault_counts.get("미확정", 0)),
    }


def validate_real_coverage(
    verdict_df: pd.DataFrame,
    event_supplement_df: pd.DataFrame,
    cluster_supplement_df: pd.DataFrame,
    metrics: dict[str, int],
) -> None:
    if verdict_df["panel_id"].eq("").any():
        raise SystemExit("main panel verdict table must not contain blank panel_id rows")
    if verdict_df.duplicated(subset=["site", "panel_id"]).any():
        dup = verdict_df.loc[verdict_df.duplicated(subset=["site", "panel_id"], keep=False), ["site", "panel_id"]]
        raise SystemExit(f"main panel verdict table must be unique by (site, panel_id): {dup.to_dict(orient='records')[:5]}")

    counts = compute_final_row_counts(verdict_df)
    interpreted_abrupt_membership = counts["사건해석_급작_패널수"]
    interpreted_precursor_membership = counts["사건해석_전조형_패널수"]
    common_membership = counts["공통원인이력_패널수"]
    gpvs_attached = int(verdict_df["GPVS_부착상태_ko"].eq("부착").sum())
    gpvs_detailed_attached = int(verdict_df["GPVS_세부fault_부착상태_ko"].eq("부착").sum())
    gpvs_detailed_deferred = int(verdict_df["GPVS_세부fault_부착상태_ko"].eq("판정유보").sum())
    gpvs_detailed_nontarget = int(verdict_df["GPVS_세부fault_부착상태_ko"].eq("비대상").sum())
    detailed_fault_attached = int(verdict_df["세부fault_부착상태_ko"].eq("부착").sum())
    detailed_fault_held = int(verdict_df["세부fault_부착상태_ko"].eq("보류").sum())
    detailed_fault_nontarget = int(verdict_df["세부fault_부착상태_ko"].eq("비대상").sum())

    if counts["고유_고장패널수"] != 6:
        raise SystemExit(f"고유_고장패널수 must be 6, found {counts['고유_고장패널수']}")
    if interpreted_precursor_membership != 3:
        raise SystemExit(f"사건해석_전조형_패널수 must be 3, found {interpreted_precursor_membership}")
    if interpreted_abrupt_membership != 3:
        raise SystemExit(f"사건해석_급작_패널수 must be 3, found {interpreted_abrupt_membership}")
    if counts["사건해석_전조형_급격종료_패널수"] != 1:
        raise SystemExit(f"사건해석_전조형_급격종료_패널수 must be 1, found {counts['사건해석_전조형_급격종료_패널수']}")
    if counts["사건해석_전조형_진행성악화_패널수"] != 2:
        raise SystemExit(f"사건해석_전조형_진행성악화_패널수 must be 2, found {counts['사건해석_전조형_진행성악화_패널수']}")
    if counts["전조흔적_패널수"] != 3:
        raise SystemExit(f"전조흔적_패널수 must be 3, found {counts['전조흔적_패널수']}")
    if counts["엄격전조평가셋_패널수"] != 3:
        raise SystemExit(f"엄격전조평가셋_패널수 must be 3, found {counts['엄격전조평가셋_패널수']}")
    if counts["순수급작평가셋_패널수"] != 3:
        raise SystemExit(f"순수급작평가셋_패널수 must be 3, found {counts['순수급작평가셋_패널수']}")
    if counts["해석과평가셋불일치_패널수"] != 0:
        raise SystemExit(f"해석과평가셋불일치_패널수 must be 0, found {counts['해석과평가셋불일치_패널수']}")
    if common_membership != 4:
        raise SystemExit(f"panels with 공통원인이력_flag must be 4, found {common_membership}")
    if gpvs_attached != int(metrics["gpvs_expected_attach_count"]):
        raise SystemExit(
            f"GPVS attached row count must equal applicable direct-match count {metrics['gpvs_expected_attach_count']}, found {gpvs_attached}"
        )
    if gpvs_detailed_attached != int(metrics["gpvs_detailed_attached_expected"]):
        raise SystemExit(
            f"GPVS detailed attached row count must equal inference summary {metrics['gpvs_detailed_attached_expected']}, found {gpvs_detailed_attached}"
        )
    if gpvs_detailed_deferred != int(metrics["gpvs_detailed_deferred_expected"]):
        raise SystemExit(
            f"GPVS detailed deferred row count must equal inference summary {metrics['gpvs_detailed_deferred_expected']}, found {gpvs_detailed_deferred}"
        )
    if gpvs_detailed_nontarget != int(len(verdict_df) - counts["고유_고장패널수"]):
        raise SystemExit("GPVS detailed non-target row count must equal non-fault/non-uncertain panel count")
    if detailed_fault_attached != int(metrics["detailed_fault_attached_expected"]):
        raise SystemExit(
            f"세부fault attached row count must equal audit summary {metrics['detailed_fault_attached_expected']}, found {detailed_fault_attached}"
        )
    if detailed_fault_held != int(metrics["detailed_fault_held_expected"]):
        raise SystemExit(
            f"세부fault held row count must equal audit summary {metrics['detailed_fault_held_expected']}, found {detailed_fault_held}"
        )
    if detailed_fault_nontarget != int(len(verdict_df) - counts["고유_고장패널수"]):
        raise SystemExit("세부fault non-target row count must equal non-fault/non-uncertain panel count")
    if verdict_df.loc[verdict_df["GPVS_적용대상_ko"].eq("적용대상"), "패널고장여부_ko"].ne("고장").any():
        raise SystemExit("GPVS applicable rows must be fault panels only")
    if verdict_df.loc[verdict_df["패널고장여부_ko"].eq("고장"), "GPVS_적용대상_ko"].ne("적용대상").any():
        raise SystemExit("fault panels must be marked GPVS_적용대상_ko=적용대상")
    if verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("부착"), "GPVS_적용대상_ko"].ne("적용대상").any():
        raise SystemExit("GPVS attached rows must be GPVS_적용대상_ko=적용대상")
    if verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("미부착"), "GPVS_적용대상_ko"].ne("적용대상").any():
        raise SystemExit("GPVS unattached rows must be GPVS_적용대상_ko=적용대상")
    if verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("부착"), "GPVS_참고유형_ko"].eq("미부착").any():
        raise SystemExit("GPVS attached rows must not keep GPVS_참고유형_ko=미부착")
    if verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("미부착"), "GPVS_참고유형_ko"].ne("미부착").any():
        raise SystemExit("GPVS unattached rows must keep GPVS_참고유형_ko=미부착")
    if verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("비대상"), "GPVS_참고유형_ko"].ne("비대상").any():
        raise SystemExit("GPVS non-target rows must keep GPVS_참고유형_ko=비대상")
    if verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("비대상"), "GPVS_후보파일_ko"].map(normalize_text).ne("").any():
        raise SystemExit("GPVS non-target rows must keep GPVS_후보파일_ko blank")
    if verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("비대상"), "GPVS_미부착사유_ko"].ne(GPVS_NON_TARGET_REASON).any():
        raise SystemExit(f"GPVS non-target rows must keep GPVS_미부착사유_ko={GPVS_NON_TARGET_REASON}")
    fault_gpvs_detailed = verdict_df.loc[verdict_df["패널고장여부_ko"].eq("고장")].copy()
    if fault_gpvs_detailed["GPVS_세부fault_부착상태_ko"].isin(["부착", "판정유보"]).ne(True).any():
        raise SystemExit("fault rows must keep GPVS_세부fault_부착상태_ko in {부착, 판정유보}")
    if verdict_df.loc[verdict_df["패널고장여부_ko"].ne("고장"), "GPVS_세부fault_부착상태_ko"].map(normalize_text).ne("비대상").any():
        raise SystemExit("non-fault rows must keep GPVS_세부fault_부착상태_ko=비대상")
    if verdict_df["GPVS_세부fault_status_ko"].map(normalize_text).ne(verdict_df["GPVS_세부fault_부착상태_ko"].map(normalize_text)).any():
        raise SystemExit("GPVS_세부fault_status_ko and GPVS_세부fault_부착상태_ko must stay synchronized")
    if verdict_df.loc[verdict_df["GPVS_세부fault_부착상태_ko"].eq("부착"), "GPVS_세부fault_code"].map(normalize_text).eq("").any():
        raise SystemExit("GPVS detailed attached rows must keep non-empty GPVS_세부fault_code")
    if verdict_df.loc[verdict_df["GPVS_세부fault_부착상태_ko"].eq("판정유보"), "GPVS_세부fault_code"].map(normalize_text).ne("").any():
        raise SystemExit("GPVS detailed deferred rows must keep empty GPVS_세부fault_code")
    if verdict_df.loc[verdict_df["GPVS_세부fault_부착상태_ko"].eq("부착"), "GPVS_세부fault_rank2_score"].map(normalize_text).eq("").any():
        raise SystemExit("GPVS detailed attached rows must keep non-empty GPVS_세부fault_rank2_score")
    if verdict_df.loc[verdict_df["GPVS_세부fault_부착상태_ko"].eq("부착"), "GPVS_세부fault_판정주의_ko"].map(normalize_text).ne("family와 detailed type은 별도 축").any():
        raise SystemExit("GPVS detailed attached rows must keep the separation caution note")
    if verdict_df.loc[verdict_df["GPVS_세부fault_부착상태_ko"].isin(["부착", "판정유보"]), "GPVS_세부fault_근거_ko"].map(normalize_text).eq("").any():
        raise SystemExit("fault rows with GPVS detailed inference status must keep non-empty GPVS_세부fault_근거_ko")
    gpvs_detailed_nontarget_subset = verdict_df.loc[
        verdict_df["패널고장여부_ko"].ne("고장"),
        [
            "GPVS_세부fault_code",
            "GPVS_세부fault_score",
            "GPVS_세부fault_rank2_code",
            "GPVS_세부fault_rank2_score",
            "GPVS_세부fault_margin",
            "GPVS_세부fault_근거_ko",
            "GPVS_세부fault_판정주의_ko",
        ],
    ].copy()
    if not gpvs_detailed_nontarget_subset.empty:
        gpvs_detailed_nontarget_subset = gpvs_detailed_nontarget_subset.apply(lambda column: column.map(normalize_text))
    if gpvs_detailed_nontarget_subset.ne("").any().any():
        raise SystemExit("non-fault rows must keep GPVS detailed inference columns blank")
    if verdict_df.loc[verdict_df["GPVS_세부fault_code"].map(normalize_text).ne(""), "GPVS_해석주의_ko"].map(normalize_text).ne(GPVS_SCENARIO_WARNING).any():
        raise SystemExit("rows with GPVS_세부fault_code must keep GPVS_해석주의_ko warning text")
    attached_scenario_subset = verdict_df.loc[
        verdict_df["GPVS_세부fault_code"].map(normalize_text).ne(""),
        [
            "GPVS_시나리오_family_ko",
            "GPVS_시나리오명_ko",
            "GPVS_시나리오_고장상황설명_ko",
            "GPVS_운전모드_ko",
            "GPVS_해석주의_ko",
        ],
    ].copy()
    if attached_scenario_subset.apply(lambda column: column.map(normalize_text)).eq("").any().any():
        raise SystemExit("rows with GPVS_세부fault_code must keep non-empty GPVS scenario semantics columns")
    gpvs_scenario_nontarget_subset = verdict_df.loc[
        verdict_df["GPVS_세부fault_code"].map(normalize_text).eq(""),
        [
            "GPVS_시나리오_family_ko",
            "GPVS_시나리오명_ko",
            "GPVS_시나리오_고장상황설명_ko",
            "GPVS_운전모드_ko",
            "GPVS_해석주의_ko",
        ],
    ].copy()
    if not gpvs_scenario_nontarget_subset.empty:
        gpvs_scenario_nontarget_subset = gpvs_scenario_nontarget_subset.apply(lambda column: column.map(normalize_text))
    if gpvs_scenario_nontarget_subset.ne("").any().any():
        raise SystemExit("rows without GPVS_세부fault_code must keep GPVS scenario semantics columns blank")
    front_facing_columns = [
        "GPVS_내부참고유형_ko",
        "GPVS_외부참조패턴_ko",
        "GPVS_참조사용등급_ko",
        "GPVS_참조설명_ko",
    ]
    front_non_fault_subset = verdict_df.loc[
        verdict_df["패널고장여부_ko"].ne("고장"),
        front_facing_columns,
    ].copy()
    if not front_non_fault_subset.empty:
        front_non_fault_subset = front_non_fault_subset.apply(lambda column: column.map(normalize_text))
    if front_non_fault_subset.ne("").any().any():
        raise SystemExit("non-fault/unresolved rows must keep front-facing GPVS columns blank")
    front_facing_series = verdict_df[front_facing_columns].fillna("").astype(str).stack()
    front_facing_text = "\n".join(front_facing_series.tolist())
    for forbidden_token in ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "IPPT", "MPPT", "제한출력 운전", "최대전력점 추종"]:
        if forbidden_token in front_facing_text:
            raise SystemExit(f"front-facing GPVS columns must not expose raw code/mode token: {forbidden_token}")
    if verdict_df.loc[verdict_df["패널고장여부_ko"].eq("고장"), "세부fault_부착상태_ko"].isin(["부착", "보류"]).ne(True).any():
        raise SystemExit("fault rows must keep 세부fault_부착상태_ko in {부착, 보류}")
    if verdict_df.loc[verdict_df["패널고장여부_ko"].ne("고장"), "세부fault_부착상태_ko"].ne("비대상").any():
        raise SystemExit("non-fault rows must keep 세부fault_부착상태_ko=비대상")
    if verdict_df.loc[verdict_df["세부fault_부착상태_ko"].eq("부착"), "세부fault_type_code"].map(normalize_text).eq("").any():
        raise SystemExit("세부fault attached rows must keep non-empty 세부fault_type_code")
    if verdict_df.loc[verdict_df["세부fault_부착상태_ko"].eq("부착"), "세부fault_type_label_ko"].map(normalize_text).eq("").any():
        raise SystemExit("세부fault attached rows must keep non-empty 세부fault_type_label_ko")
    if verdict_df.loc[verdict_df["세부fault_부착상태_ko"].eq("보류"), "세부fault_보류사유_ko"].map(normalize_text).eq("").any():
        raise SystemExit("세부fault held rows must keep non-empty 세부fault_보류사유_ko")
    detailed_nontarget_subset = verdict_df.loc[
        verdict_df["세부fault_부착상태_ko"].eq("비대상"),
        ["세부fault_type_code", "세부fault_type_label_ko", "세부fault_근거파일_ko", "세부fault_기준일", "세부fault_보류사유_ko"],
    ].copy()
    if not detailed_nontarget_subset.empty:
        detailed_nontarget_subset = detailed_nontarget_subset.apply(lambda column: column.map(normalize_text))
    if detailed_nontarget_subset.ne("").any().any():
        raise SystemExit("세부fault non-target rows must keep detailed-fault columns blank")

    forensic_df = verdict_df.loc[
        verdict_df["site"].eq(FORENSIC_RULE_SITE) & verdict_df["panel_id"].eq(FORENSIC_RULE_PANEL_ID)
    ].copy()
    if len(forensic_df) != 1:
        raise SystemExit("forensic target panel must appear exactly once in main panel verdict table")
    forensic_row = forensic_df.iloc[0]
    if normalize_text(forensic_row["사건유형_ko"]) != FORENSIC_RULE_EVENT_TYPE:
        raise SystemExit(f"forensic target panel must be marked 사건유형_ko={FORENSIC_RULE_EVENT_TYPE}")
    if normalize_text(forensic_row["사건유형_해석_ko"]) != FORENSIC_RULE_EVENT_TYPE:
        raise SystemExit(f"forensic target panel must be marked 사건유형_해석_ko={FORENSIC_RULE_EVENT_TYPE}")
    if normalize_text(forensic_row["패널고장여부_ko"]) != "고장":
        raise SystemExit("forensic target panel must stay 패널고장여부_ko=고장")
    if normalize_text(forensic_row["최종고장양상_ko"]) != FORENSIC_RULE_TERMINAL_PATTERN:
        raise SystemExit(f"forensic target panel must keep 최종고장양상_ko={FORENSIC_RULE_TERMINAL_PATTERN}")
    if normalize_text(forensic_row["GPVS_적용대상_ko"]) != "적용대상":
        raise SystemExit("forensic target panel must remain GPVS applicable")
    if int(pd.to_numeric(forensic_row["전조흔적_flag"], errors="coerce")) != 1:
        raise SystemExit("forensic target panel must keep 전조흔적_flag=1")
    if int(pd.to_numeric(forensic_row["순수급작_flag"], errors="coerce")) != 0:
        raise SystemExit("forensic target panel must keep 순수급작_flag=0")
    if int(pd.to_numeric(forensic_row["전조평가셋편입_flag"], errors="coerce")) != 1:
        raise SystemExit("forensic target panel must keep 전조평가셋편입_flag=1")
    if int(pd.to_numeric(forensic_row["급작평가셋편입_flag"], errors="coerce")) != 0:
        raise SystemExit("forensic target panel must keep 급작평가셋편입_flag=0")
    if normalize_text(forensic_row["해석대평가차이_ko"]) != "":
        raise SystemExit("forensic target panel should not expose interpretation/evaluation mismatch text after benchmark sync")
    if FORENSIC_RULE_ONSET_DATE not in normalize_text(forensic_row["판정주의_ko"]) or FORENSIC_RULE_TRIGGER_DATE not in normalize_text(forensic_row["판정주의_ko"]):
        raise SystemExit("forensic target panel note must mention onset/trigger dates")
    if normalize_text(forensic_row["GPVS_세부fault_code"]) != "F2M":
        raise SystemExit("forensic target panel must keep GPVS_세부fault_code=F2M after recovered-artifact attachment")
    if normalize_text(forensic_row["GPVS_세부fault_부착상태_ko"]) != "부착":
        raise SystemExit("forensic target panel must keep GPVS_세부fault_부착상태_ko=부착")
    if normalize_text(forensic_row["GPVS_시나리오_family_ko"]) != "제어·계측 이상":
        raise SystemExit("forensic target panel must expose GPVS_시나리오_family_ko=제어·계측 이상")
    if normalize_text(forensic_row["GPVS_시나리오명_ko"]) != "제어 피드백 센서 이상 시나리오":
        raise SystemExit("forensic target panel must expose F2M scenario name")
    if normalize_text(forensic_row["GPVS_운전모드_ko"]) != "최대전력점 추종 운전(MPPT)":
        raise SystemExit("forensic target panel must expose F2M mode=MPPT")
    if normalize_text(forensic_row["GPVS_해석주의_ko"]) != GPVS_SCENARIO_WARNING:
        raise SystemExit("forensic target panel must keep GPVS scenario warning text")
    if normalize_text(forensic_row["GPVS_내부참고유형_ko"]) != normalize_text(forensic_row["GPVS_참고유형_ko"]):
        raise SystemExit("forensic target panel must surface internal GPVS interpretation in GPVS_내부참고유형_ko")
    if normalize_text(forensic_row["GPVS_외부참조패턴_ko"]) != "장치 응답 이상형":
        raise SystemExit("forensic target panel must expose GPVS_외부참조패턴_ko=장치 응답 이상형")
    if normalize_text(forensic_row["GPVS_참조사용등급_ko"]) != "비권장":
        raise SystemExit("forensic target panel must expose GPVS_참조사용등급_ko=비권장")
    if "센서/피드백 오류로 장치 응답이 어긋나는 패턴" not in normalize_text(forensic_row["GPVS_참조설명_ko"]):
        raise SystemExit("forensic target panel must expose human-readable GPVS reference description for F2")

    special_10305_df = verdict_df.loc[
        verdict_df["site"].eq("ktc_ess") & verdict_df["panel_id"].eq("10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12")
    ].copy()
    if len(special_10305_df) > 1:
        raise SystemExit("10305 real fault panel must appear at most once in main panel verdict table")
    if len(special_10305_df) == 1:
        special_10305_row = special_10305_df.iloc[0]
        if normalize_text(special_10305_row["GPVS_참고유형_ko"]) != "불확실":
            raise SystemExit("10305 row must keep GPVS_참고유형_ko=불확실")
        if normalize_text(special_10305_row["GPVS_세부fault_code"]) != "F4L":
            raise SystemExit("10305 row must keep GPVS_세부fault_code=F4L")
        if normalize_text(special_10305_row["GPVS_시나리오_family_ko"]) != "PV 어레이 이상":
            raise SystemExit("10305 row must expose GPVS_시나리오_family_ko=PV 어레이 이상")
        if normalize_text(special_10305_row["GPVS_시나리오명_ko"]) != "PV 어레이 mismatch(부분 음영) 시나리오":
            raise SystemExit("10305 row must expose F4L scenario name")
        if normalize_text(special_10305_row["GPVS_운전모드_ko"]) != "제한출력 운전(IPPT)":
            raise SystemExit("10305 row must expose F4L mode=IPPT")
        if normalize_text(special_10305_row["GPVS_내부참고유형_ko"]) != "불확실":
            raise SystemExit("10305 row must surface GPVS_내부참고유형_ko=불확실")
        if normalize_text(special_10305_row["GPVS_외부참조패턴_ko"]) != "국소 출력 불균형형":
            raise SystemExit("10305 row must expose GPVS_외부참조패턴_ko=국소 출력 불균형형")
        if normalize_text(special_10305_row["GPVS_참조사용등급_ko"]) != "주의참고":
            raise SystemExit("10305 row must expose GPVS_참조사용등급_ko=주의참고")
        if "일부 패널의 출력 균형이 깨지는 패턴" not in normalize_text(special_10305_row["GPVS_참조설명_ko"]):
            raise SystemExit("10305 row must expose human-readable GPVS reference description for F4")

    overlap_rows = verdict_df.loc[
        verdict_df["전조평가셋편입_flag"].pipe(to_numeric_flag).eq(1)
        & verdict_df["사건유형_ko"].eq("전조형 고장")
        & verdict_df["최종고장양상_ko"].eq("진행성 악화")
    ].copy()
    if len(overlap_rows) != metrics["same_event_overlap_expected"]:
        raise SystemExit(
            f"same-event overlap rows must stay {metrics['same_event_overlap_expected']}, found {len(overlap_rows)}"
        )
    if overlap_rows["사건유형_ko"].map(normalize_text).ne("전조형 고장").any():
        raise SystemExit("same-event overlap rows must keep 사건유형_ko=전조형 고장")
    if overlap_rows["사건유형_해석_ko"].map(normalize_text).ne("전조형 고장").any():
        raise SystemExit("same-event overlap rows must keep 사건유형_해석_ko=전조형 고장")
    if overlap_rows["최종고장양상_ko"].map(normalize_text).ne("진행성 악화").any():
        raise SystemExit("same-event overlap rows must keep 최종고장양상_ko=진행성 악화 after corrected rule sync")
    if to_numeric_flag(overlap_rows["전조흔적_flag"]).ne(1).any():
        raise SystemExit("same-event overlap rows must keep 전조흔적_flag=1")
    if to_numeric_flag(overlap_rows["순수급작_flag"]).ne(0).any():
        raise SystemExit("same-event overlap rows must keep 순수급작_flag=0")
    if to_numeric_flag(overlap_rows["전조평가셋편입_flag"]).ne(1).any():
        raise SystemExit("same-event overlap rows must keep 전조평가셋편입_flag=1")
    if to_numeric_flag(overlap_rows["급작평가셋편입_flag"]).ne(0).any():
        raise SystemExit("same-event overlap rows must keep 급작평가셋편입_flag=0")

    if metrics["workflow_cluster_count"] > 0 and len(cluster_supplement_df) <= 0:
        raise SystemExit("cluster supplement check failed: workflow has discovery clusters but supplement is empty")
    if cluster_supplement_df["GPVS_참고유형_ko"].ne("미부착").any():
        raise SystemExit("cluster supplement must stay GPVS_참고유형_ko=미부착")
    if cluster_supplement_df["GPVS_근거_ko"].ne(GPVS_ABSENCE_REASON).any():
        raise SystemExit(f"cluster supplement must stay GPVS_근거_ko={GPVS_ABSENCE_REASON}")

    insufficient_rows = verdict_df.loc[
        verdict_df["사건유형_ko"].eq("불충분"),
        ["site", "panel_id", "전조형이력_flag", "급작고장이력_flag", "공통원인이력_flag", "반복이상이력_flag"],
    ]
    for row in insufficient_rows.to_dict(orient="records"):
        if any(int(row[column]) == 1 for column in ["전조형이력_flag", "급작고장이력_flag", "공통원인이력_flag", "반복이상이력_flag"]):
            raise SystemExit(f"insufficient representative row violates membership guardrail: {row}")

    if event_supplement_df.empty and (interpreted_abrupt_membership + interpreted_precursor_membership + common_membership) > 0:
        raise SystemExit("event supplement is empty despite event memberships in the main panel table")


def build_summary(
    verdict_df: pd.DataFrame,
    event_supplement_df: pd.DataFrame,
    cluster_supplement_df: pd.DataFrame,
    metrics: dict[str, int],
    gpvs_feasibility_meta: dict[str, str],
) -> pd.DataFrame:
    counts = compute_final_row_counts(verdict_df)
    symptom_attached = int(verdict_df["커널로그_증상명_ko"].ne("불충분").sum())
    cause_group_attached = int(verdict_df["커널로그_원인군_ko"].ne("불충분").sum())
    gpvs_applicable = int(verdict_df["GPVS_적용대상_ko"].eq("적용대상").sum())
    gpvs_attached = int(verdict_df["GPVS_부착상태_ko"].eq("부착").sum())
    gpvs_unattached = int(verdict_df["GPVS_부착상태_ko"].eq("미부착").sum())
    gpvs_non_target = int(verdict_df["GPVS_부착상태_ko"].eq("비대상").sum())
    gpvs_detailed_attached = int(verdict_df["GPVS_세부fault_부착상태_ko"].eq("부착").sum())
    gpvs_detailed_deferred = int(verdict_df["GPVS_세부fault_부착상태_ko"].eq("판정유보").sum())
    gpvs_detailed_nontarget = int(verdict_df["GPVS_세부fault_부착상태_ko"].eq("비대상").sum())
    gpvs_detailed_f2m = int(verdict_df["GPVS_세부fault_code"].eq("F2M").sum())
    gpvs_detailed_f4l = int(verdict_df["GPVS_세부fault_code"].eq("F4L").sum())
    detailed_fault_attached = int(verdict_df["세부fault_부착상태_ko"].eq("부착").sum())
    detailed_fault_held = int(verdict_df["세부fault_부착상태_ko"].eq("보류").sum())
    detailed_fault_non_target = int(verdict_df["세부fault_부착상태_ko"].eq("비대상").sum())
    gpvs_reason_counts = (
        verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("미부착"), "GPVS_미부착사유_ko"].value_counts().to_dict()
    )
    best_source = normalize_text(gpvs_feasibility_meta.get("best_source", ""))
    if gpvs_unattached > 0:
        gpvs_note = (
            f"GPVS는 reference axis로만 붙이고, 현재 final row 기준 적용대상 fault panel {gpvs_applicable}개 중 {gpvs_attached}개에만 부분 부착했다."
        )
    else:
        gpvs_note = (
            f"GPVS는 reference axis로만 붙이고, 현재 final row 기준 적용대상 fault panel {gpvs_applicable}개에는 모두 부착했다."
        )
    if best_source:
        gpvs_note += f" 최선 후보 파일은 {best_source} 다."
    gpvs_note += " 다만 GPVS는 현재 fault-family reference axis 이므로 고장 패널에만 적용하고, 비고장/반복/불충분 panel은 비대상으로 둔다."

    row = {
        **counts,
        "커널로그_증상명_부착수": symptom_attached,
        "커널로그_원인군_부착수": cause_group_attached,
        "GPVS_적용대상_패널수": gpvs_applicable,
        "GPVS_부착수": gpvs_attached,
        "GPVS_미부착수": gpvs_unattached,
        "GPVS_비대상수": gpvs_non_target,
        "GPVS_미부착_패널key없음수": int(gpvs_reason_counts.get("GPVS 패널수준 후보 파일은 있으나 이 패널 key가 없음", 0)),
        "GPVS_미부착_key부족수": int(gpvs_reason_counts.get("GPVS 결과는 있으나 패널수준 key가 없음", 0)),
        "GPVS_미부착_산출물없음수": int(gpvs_reason_counts.get("패널수준 GPVS 산출물 없음", 0)),
        "GPVS_세부fault_부착수": gpvs_detailed_attached,
        "GPVS_세부fault_판정유보수": gpvs_detailed_deferred,
        "GPVS_세부fault_추론불가수": 0,
        "GPVS_세부fault_부착패널수": gpvs_detailed_attached,
        "GPVS_세부fault_판정유보패널수": gpvs_detailed_deferred,
        "GPVS_세부fault_비대상패널수": gpvs_detailed_nontarget,
        "GPVS_세부fault_F2M_패널수": gpvs_detailed_f2m,
        "GPVS_세부fault_F4L_패널수": gpvs_detailed_f4l,
        "사건보조행수": int(len(event_supplement_df)),
        "클러스터_보조행수": int(len(cluster_supplement_df)),
        "note_ko": (
            f"main panel table은 unique panel 대표 verdict 표이고 workflow panel {metrics['workflow_panel_count']}건을 기준으로 fault6 rows {metrics['abrupt_fault6_total']}건, 사건 해석상 전조형 3건, 사건 해석상 급작 3건, 엄격 전조 평가셋 3건, 순수 급작 평가셋 3건을 분리해서 적는다. "
            f"fault panel event audit {metrics['fault_audit_expected']}건을 authoritative fault-event source로 읽어 사건유형/최종고장양상/순수급작 flag를 동기화했다. "
            f"same-event overlap {metrics['same_event_overlap_expected']}건은 전조형 고장으로 읽고, c42997 row 는 전조형 고장/급격 종료로 읽으며 엄격 전조 평가셋에는 포함하고 순수 급작 평가셋에서는 제외한다. "
            f"single-panel forensic explicit rule {metrics['forensic_rule_expected']}건은 c42997 row 설명 근거로 유지하고, same-day fallback onset abrupt row 는 급작 고장으로 다시 허용한다. "
            "이제 전조평가셋편입_flag 는 precursor onset truth membership으로, 급작평가셋편입_flag 는 non-precursor abrupt performance case membership으로 다시 계산한다. "
            "사건유형_해석_ko 와 평가셋 편입 flag를 분리해, 사건 해석과 evaluation-set inclusion을 같은 뜻으로 읽지 않게 한다. "
            "또한 운영상 최초 전조 발견일, 사건 해석상 전조 시작일, benchmark 전조 시작일을 분리해 onset date 의미를 섞지 않게 한다. "
            "event type과 terminal failure pattern은 분리해서 읽는다. "
            f"GPVS 세부 fault는 learned GPVS by-type inference 결과를 recovered GPVS by-type artifact parity 일치 이후 real panel event date에 다시 적용해 현재 부착 {gpvs_detailed_attached}건 / 판정유보 {gpvs_detailed_deferred}건 / 비대상 {gpvs_detailed_nontarget}건이다. "
            f"현재 code 분포는 F2M {gpvs_detailed_f2m}건, F4L {gpvs_detailed_f4l}건이다. "
            "GPVS family label 과 GPVS detailed fault code 는 별도 축이며, family 불확실이더라도 recovered by-type inference attach guard를 통과하면 detailed type은 부착할 수 있다. "
            "GPVS detailed fault code는 외부 GPVS 실험 시나리오 참조축이므로 F2M/F4L을 실제 패널 물리 root cause 이름으로 직접 번역하면 안 된다. "
            "공식 detailed-fault attachment source 는 recovered GPVS by-type inference 이고, 과거 PVFAULT exact-date bridge 경로는 audit-only 실패 경로로 retire 했다. "
            "이 세부 fault 축은 GPVS family reference 와 별개로 읽는다. "
            f"사건이력 보조표는 panel이 여러 사건군에 속하거나 전조형 고장이 급격 종료로 끝난 경우를 함께 남긴다. {gpvs_note} unmatched panel은 row-by-row 미부착 사유를 함께 남긴다."
        ),
    }
    return pd.DataFrame([row]).reindex(columns=SUMMARY_COLS)


def write_outputs(
    root: Path,
    verdict_df: pd.DataFrame,
    event_supplement_df: pd.DataFrame,
    cluster_supplement_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    verdict_df.to_csv(share_dir / VERDICT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    event_supplement_df.to_csv(share_dir / EVENT_SUPPLEMENT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    cluster_supplement_df.to_csv(share_dir / CLUSTER_SUPPLEMENT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    frames = load_inputs(root)
    validate_inputs(root, frames)
    verdict_df, verdict_internal_df, event_supplement_df, cluster_supplement_df, metrics, gpvs_feasibility_meta = build_outputs(root, frames)
    validate_real_coverage(verdict_internal_df, event_supplement_df, cluster_supplement_df, metrics)
    summary_df = build_summary(verdict_internal_df, event_supplement_df, cluster_supplement_df, metrics, gpvs_feasibility_meta)
    write_outputs(root, verdict_df, event_supplement_df, cluster_supplement_df, summary_df)


if __name__ == "__main__":
    main()
