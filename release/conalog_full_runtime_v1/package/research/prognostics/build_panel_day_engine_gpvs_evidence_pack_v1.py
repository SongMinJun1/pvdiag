#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]

VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
FAMILY_EVAL_NAME = "gpvs_fault_family_eval_cases.csv"
ATTACH_CANDIDATES_NAME = "panel_day_engine_gpvs_panel_attach_candidates_v1.csv"
DETAILED_AUDIT_NAME = "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv"
DETAILED_SANITY_NAME = "panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv"
BYTYPE_PROVENANCE_SUMMARY_NAME = "panel_day_engine_gpvs_bytype_provenance_summary_v1.csv"
BYTYPE_REBUILD_SUMMARY_NAME = "panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv"
MLPE_PANEL_AGREEMENT_NAME = "panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv"
MLPE_COMPATIBILITY_SUMMARY_NAME = "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv"
MLPE_MATCHING_TABLE_NAME = "panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv"
MLPE_MATCHING_SUMMARY_NAME = "panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv"
CANONICAL_DICTIONARY_NAME = "panel_day_engine_gpvs_canonical_dictionary_v1.csv"

OUTPUT_PACK_NAME = "panel_day_engine_gpvs_evidence_pack_v1.csv"
OUTPUT_SUMMARY_NAME = "panel_day_engine_gpvs_evidence_summary_v1.csv"
OUTPUT_NOTE_NAME = "panel_day_engine_gpvs_evidence_note_v1.md"

PACK_COLS = [
    "site",
    "panel_id",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
    "GPVS_내부판정_ko",
    "GPVS_내부판정근거_ko",
    "GPVS_외부참조패턴_ko",
    "GPVS_외부참조근거_ko",
    "GPVS_호환성판정_ko",
    "GPVS_호환성근거_ko",
    "GPVS_매칭정책_ko",
    "GPVS_매칭근거_ko",
    "GPVS_최종사용권고_ko",
    "GPVS_권고사유_ko",
]

SUMMARY_COLS = [
    "fault_panel_count",
    "internal_evidence_available_count",
    "external_evidence_available_count",
    "compatibility_reference_only_flag",
    "core_reference_count",
    "core_reference_candidate_count",
    "auxiliary_reference_count",
    "confounder_flag_count",
    "reserved_system_count",
    "not_recommended_count",
    "final_operational_rule_ko",
    "note_ko",
]

VERDICT_REQUIRED_COLS = [
    "site",
    "panel_id",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
    "패널고장여부_ko",
]
DETAILED_REQUIRED_COLS = [
    "site",
    "panel_id",
    "gpvs_detailed_model_source",
    "gpvs_detailed_top1_fault_type",
    "gpvs_detailed_top1_score",
    "gpvs_detailed_top2_fault_type",
    "gpvs_detailed_top2_score",
    "gpvs_detailed_margin",
]
COMPATIBILITY_SUMMARY_REQUIRED_COLS = ["fault_panel_count", "final_recommendation_ko", "note_ko"]
MATCHING_SUMMARY_REQUIRED_COLS = [
    "canonical_code_count",
    "core_reference_count",
    "auxiliary_reference_count",
    "confounder_count",
    "reserved_system_count",
    "final_matching_policy_ko",
    "note_ko",
]

INTERNAL_COL_CANDIDATES = ["GPVS_내부참고유형_ko", "GPVS_참고유형_ko"]
EXTERNAL_PATTERN_COL_CANDIDATES = ["GPVS_외부참조패턴_ko", "GPVS_외부참조시나리오명_ko"]

DEFAULT_CANONICAL_DICTIONARY = {
    "F0": {
        "current_usage_tier_ko": "baseline",
        "mlpe_reference_name_ko": "정상 기준선",
        "usage_rule_ko": "비고장 기준선과 drift 비교에만 사용",
        "note_ko": "fault명이 아니라 baseline reference로만 노출",
    },
    "F1": {
        "current_usage_tier_ko": "reserved_system_level",
        "mlpe_reference_name_ko": "인버터 전력변환부 시스템 시나리오",
        "usage_rule_ko": "MLPE direct fault명이 아니라 통합 결과표 후보축으로만 보류",
        "note_ko": "system-level reserve code",
    },
    "F2": {
        "current_usage_tier_ko": "auxiliary_reference",
        "mlpe_reference_name_ko": "제어/계측 이상 보조 힌트",
        "usage_rule_ko": "direct root-cause가 아니라 제어·계측 이상 힌트로만 사용",
        "note_ko": "control/measurement hint only",
    },
    "F3": {
        "current_usage_tier_ko": "confounder_only",
        "mlpe_reference_name_ko": "계통 교란 플래그",
        "usage_rule_ko": "fault label이 아니라 confounder flag로만 사용",
        "note_ko": "disturbance flag only",
    },
    "F4": {
        "current_usage_tier_ko": "core_reference",
        "mlpe_reference_name_ko": "패널·어레이 mismatch 핵심 참조",
        "usage_rule_ko": "MLPE 패널·어레이 불균형 해석의 핵심 reference로 사용",
        "note_ko": "panel/array imbalance reference",
    },
    "F5": {
        "current_usage_tier_ko": "core_reference_candidate",
        "mlpe_reference_name_ko": "부분 개방회로 계열 핵심 참조 후보",
        "usage_rule_ko": "케이블 접점불량(단선) 가설의 핵심 reference candidate로 유지",
        "note_ko": "candidate until real-panel evidence grows",
    },
    "F6": {
        "current_usage_tier_ko": "reserved_system_level",
        "mlpe_reference_name_ko": "제어기 gain 이상 시스템 시나리오",
        "usage_rule_ko": "MLPE direct fault명이 아니라 통합 결과표 후보축으로만 보류",
        "note_ko": "system-level reserve code",
    },
    "F7": {
        "current_usage_tier_ko": "reserved_system_level",
        "mlpe_reference_name_ko": "제어기 시정수 이상 시스템 시나리오",
        "usage_rule_ko": "MLPE direct fault명이 아니라 통합 결과표 후보축으로만 보류",
        "note_ko": "system-level reserve code",
    },
}

DEFAULT_EXTERNAL_PATTERN_BY_CODE = {
    "F0": "정상 기준선",
    "F1": "전력변환 이상형",
    "F2": "장치 응답 이상형",
    "F3": "계통 교란형",
    "F4": "국소 출력 불균형형",
    "F5": "부분 개방·접속 이상형",
    "F6": "제어기 gain 이상형",
    "F7": "제어기 시정수 이상형",
}

TIER_TO_POLICY = {
    "baseline": "기준선",
    "core_reference": "핵심참조",
    "core_reference_candidate": "핵심참조후보",
    "auxiliary_reference": "보조참조",
    "confounder_only": "교란플래그",
    "reserved_system_level": "시스템보류",
}

MATCHING_REASON_BY_CODE = {
    "F0": "F0는 비고장 기준선과 drift 비교 기준으로만 사용한다",
    "F1": "F1은 현재 패널 단독표보다 시스템/통합 결과표 후보축으로만 보류한다",
    "F2": "F2는 장치 응답 이상 힌트로만 사용하고 direct root-cause로 읽지 않는다",
    "F3": "F3는 외부 계통 교란 플래그로만 남긴다",
    "F4": "F4는 패널·어레이 불균형 해석에 가장 유용한 핵심 reference code다",
    "F5": "F5는 부분 개방·접속 약화 계열과 가장 가까운 핵심참조후보다",
    "F6": "F6은 현재 패널 단독표보다 시스템/통합 결과표 후보축으로만 보류한다",
    "F7": "F7은 현재 패널 단독표보다 시스템/통합 결과표 후보축으로만 보류한다",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate current GPVS evidence layers for the real fault panels."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root. Defaults to project root.",
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


def read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def canonicalize_gpvs_code(value: object) -> str:
    text = normalize_text(value)
    match = re.match(r"^(F[0-7])", text)
    return match.group(1) if match else ""


def as_key(site: object, panel_id: object) -> tuple[str, str]:
    return normalize_text(site), normalize_text(panel_id)


def lookup_map(df: pd.DataFrame) -> dict[tuple[str, str], dict[str, object]]:
    if df.empty or "site" not in df.columns or "panel_id" not in df.columns:
        return {}
    records: dict[tuple[str, str], dict[str, object]] = {}
    for row in df.to_dict(orient="records"):
        records[as_key(row.get("site"), row.get("panel_id"))] = row
    return records


def first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return ""


def first_row_text(row: dict[str, object], candidates: list[str]) -> str:
    for candidate in candidates:
        text = normalize_text(row.get(candidate))
        if text:
            return text
    return ""


def fmt_score(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    try:
        return f"{float(text):.3f}"
    except ValueError:
        return text


def build_canonical_dictionary_map(df: pd.DataFrame) -> dict[str, dict[str, str]]:
    canonical_map = {
        code: payload.copy()
        for code, payload in DEFAULT_CANONICAL_DICTIONARY.items()
    }
    if df.empty or "canonical_gpvs_code" not in df.columns:
        return canonical_map
    for row in df.to_dict(orient="records"):
        code = normalize_text(row.get("canonical_gpvs_code"))
        if not code:
            continue
        payload = canonical_map.setdefault(code, {})
        for field in ["current_usage_tier_ko", "mlpe_reference_name_ko", "usage_rule_ko", "note_ko"]:
            text = normalize_text(row.get(field))
            if text:
                payload[field] = text
    return canonical_map


def build_matching_table_map(df: pd.DataFrame) -> dict[str, list[dict[str, object]]]:
    table_map: dict[str, list[dict[str, object]]] = {}
    if df.empty or "canonical_gpvs_code" not in df.columns:
        return table_map
    for row in df.to_dict(orient="records"):
        code = normalize_text(row.get("canonical_gpvs_code"))
        if not code:
            continue
        table_map.setdefault(code, []).append(row)
    return table_map


def build_internal_evidence(
    family_row: dict[str, object] | None,
    attach_row: dict[str, object] | None,
) -> str:
    if family_row:
        parts = []
        source = normalize_text(family_row.get("prediction_source"))
        fallback = normalize_text(family_row.get("fallback_rule_used"))
        error_type = normalize_text(family_row.get("error_type"))
        pred_family = normalize_text(family_row.get("pred_fault_family"))
        vendor_family = normalize_text(family_row.get("vendor_fault_family"))
        if source:
            parts.append(f"family evaluator source={source}")
        if fallback:
            parts.append(f"fallback={fallback}")
        if error_type:
            parts.append(f"error={error_type}")
        if pred_family:
            parts.append(f"pred={pred_family}")
        if vendor_family:
            parts.append(f"vendor={vendor_family}")
        return ", ".join(parts) if parts else "family evaluator row 확인됨"
    if attach_row:
        source_key = normalize_text(attach_row.get("source_key_ko"))
        note = normalize_text(attach_row.get("비고_ko"))
        parts = []
        if source_key:
            parts.append(f"attach candidate key={source_key}")
        if note:
            parts.append(note)
        return ", ".join(parts) if parts else "attach candidate row 확인됨"
    return "근거 파일 미확인"


def build_external_pattern(
    verdict_row: dict[str, object],
    canonical_code: str,
    canonical_map: dict[str, dict[str, str]],
) -> str:
    pattern = first_row_text(verdict_row, EXTERNAL_PATTERN_COL_CANDIDATES)
    if pattern:
        return pattern
    if canonical_code in DEFAULT_EXTERNAL_PATTERN_BY_CODE:
        return DEFAULT_EXTERNAL_PATTERN_BY_CODE[canonical_code]
    return normalize_text(canonical_map.get(canonical_code, {}).get("mlpe_reference_name_ko"))


def build_external_evidence(
    detailed_row: dict[str, object] | None,
    sanity_row: dict[str, object] | None,
) -> str:
    if not detailed_row:
        return "근거 파일 미확인"
    parts = []
    model_source = normalize_text(detailed_row.get("gpvs_detailed_model_source"))
    top1 = normalize_text(detailed_row.get("gpvs_detailed_top1_fault_type"))
    top1_score = fmt_score(detailed_row.get("gpvs_detailed_top1_score"))
    top2 = normalize_text(detailed_row.get("gpvs_detailed_top2_fault_type"))
    top2_score = fmt_score(detailed_row.get("gpvs_detailed_top2_score"))
    margin = fmt_score(detailed_row.get("gpvs_detailed_margin"))
    status = normalize_text(detailed_row.get("gpvs_detailed_status_ko"))
    reason = normalize_text(detailed_row.get("gpvs_detailed_reason_ko"))
    if model_source:
        parts.append(f"by-type source={model_source}")
    if top1:
        parts.append(f"top1={top1}({top1_score})")
    if top2:
        parts.append(f"top2={top2}({top2_score})")
    if margin:
        parts.append(f"margin={margin}")
    if status:
        parts.append(f"status={status}")
    if reason:
        parts.append(f"reason={reason}")
    if sanity_row:
        attach_recommendation = normalize_text(sanity_row.get("attach_recommendation_ko"))
        consistency = normalize_text(sanity_row.get("family_vs_detail_consistency_ko"))
        if attach_recommendation:
            parts.append(f"sanity={attach_recommendation}")
        if consistency:
            parts.append(f"consistency={consistency}")
    return ", ".join(parts) if parts else "근거 파일 미확인"


def map_usefulness_to_compatibility(
    usefulness: str,
    summary_final_recommendation: str,
) -> str:
    if usefulness == "비권장":
        return "직접 판정축 사용 비권장"
    if usefulness in {"참고가능", "주의참고"}:
        return "조건부 참고 가능"
    if summary_final_recommendation in {
        "참고축으로만 사용",
        "조건부 참고 가능",
        "직접 판정축 사용 비권장",
        "비교곤란",
    }:
        return summary_final_recommendation
    return "비교곤란"


def build_compatibility_evidence(
    agreement_row: dict[str, object] | None,
    compatibility_summary_row: dict[str, object],
) -> str:
    parts = []
    if agreement_row:
        family_alignment = normalize_text(agreement_row.get("family_vs_kernellog_alignment_ko"))
        scenario_alignment = normalize_text(agreement_row.get("scenario_vs_kernellog_alignment_ko"))
        shift = normalize_text(agreement_row.get("feature_shift_bucket_ko"))
        usefulness = normalize_text(agreement_row.get("overall_gpvs_reference_usefulness_ko"))
        trust_note = normalize_text(agreement_row.get("overall_gpvs_trust_note_ko"))
        if family_alignment:
            parts.append(f"family_alignment={family_alignment}")
        if scenario_alignment:
            parts.append(f"scenario_alignment={scenario_alignment}")
        if shift:
            parts.append(f"feature_shift={shift}")
        if usefulness:
            parts.append(f"panel_usefulness={usefulness}")
        if trust_note:
            parts.append(trust_note)
    summary_final = normalize_text(compatibility_summary_row.get("final_recommendation_ko"))
    summary_note = normalize_text(compatibility_summary_row.get("note_ko"))
    strong_shift_count = normalize_text(compatibility_summary_row.get("strong_shift_panel_count"))
    scenario_conflict_count = normalize_text(compatibility_summary_row.get("scenario_conflict_count"))
    if summary_final:
        parts.append(f"summary={summary_final}")
    if strong_shift_count:
        parts.append(f"strong_shift_panel_count={strong_shift_count}")
    if scenario_conflict_count:
        parts.append(f"scenario_conflict_count={scenario_conflict_count}")
    if summary_note:
        parts.append(summary_note)
    return "; ".join(part for part in parts if part) or "호환성 근거 미확인"


def build_matching_policy(canonical_code: str, canonical_map: dict[str, dict[str, str]]) -> str:
    if not canonical_code:
        return "비권장"
    usage_tier = normalize_text(canonical_map.get(canonical_code, {}).get("current_usage_tier_ko"))
    return TIER_TO_POLICY.get(usage_tier, "비권장")


def build_matching_evidence(
    canonical_code: str,
    canonical_map: dict[str, dict[str, str]],
    matching_table_map: dict[str, list[dict[str, object]]],
) -> str:
    if not canonical_code:
        return "canonical GPVS code 미확인"
    rule = normalize_text(canonical_map.get(canonical_code, {}).get("usage_rule_ko"))
    note = normalize_text(canonical_map.get(canonical_code, {}).get("note_ko"))
    parts = [MATCHING_REASON_BY_CODE.get(canonical_code, "canonical matching rule 미정의")]
    if rule:
        parts.append(rule)
    if note:
        parts.append(note)
    rows = matching_table_map.get(canonical_code, [])
    if rows:
        compact = []
        for row in rows:
            official_fault = normalize_text(row.get("mlpe_official_fault_ko"))
            role = normalize_text(row.get("match_role_ko"))
            if official_fault and role:
                compact.append(f"{official_fault}:{role}")
        if compact:
            parts.append("matching=" + " / ".join(compact))
    return "; ".join(part for part in parts if part)


def combine_final_recommendation(
    matching_policy: str,
    compatibility_judgment: str,
    has_internal_evidence: bool,
    has_external_evidence: bool,
) -> str:
    if not has_internal_evidence or not has_external_evidence:
        return "비권장"
    if matching_policy == "비권장":
        return "비권장"
    if matching_policy in {
        "핵심참조",
        "핵심참조후보",
        "보조참조",
        "교란플래그",
        "시스템보류",
        "기준선",
    }:
        return matching_policy
    return "비권장"


def build_recommendation_reason(
    final_recommendation: str,
    compatibility_judgment: str,
    matching_policy: str,
    external_pattern: str,
    canonical_code: str,
) -> str:
    pattern_or_code = external_pattern or canonical_code or "GPVS reference"
    if final_recommendation == "핵심참조":
        return f"{pattern_or_code}는 direct root-cause가 아니라 reference-only 핵심참조로만 사용한다."
    if final_recommendation == "핵심참조후보":
        return f"{pattern_or_code}는 direct root-cause가 아니라 reference-only 핵심참조후보로만 사용한다."
    if final_recommendation == "보조참조":
        return f"{pattern_or_code}는 직접 root-cause 판정에는 쓰지 말고 보조참조로만 사용한다."
    if final_recommendation == "교란플래그":
        return f"{pattern_or_code}는 고장명보다 교란 신호를 표시하는 용도로만 쓰는 것이 안전하다."
    if final_recommendation == "시스템보류":
        return f"{pattern_or_code}는 현재 패널 단독표보다 시스템/통합 결과표 후보축으로만 보류한다."
    if final_recommendation == "기준선":
        return f"{pattern_or_code}는 fault명이 아니라 비교 기준선으로만 사용한다."
    if matching_policy == "비권장":
        return f"{pattern_or_code}는 matching policy 자체가 비권장이라 direct root-cause로도 reference로도 쓰지 않는다."
    return f"{pattern_or_code}는 required evidence가 부족하거나 unusable 상태라 비권장으로 둔다."


def main() -> None:
    args = parse_args()
    share_dir = args.root / "_share"

    verdict_df = read_csv(share_dir / VERDICT_NAME)
    ensure_columns(verdict_df, VERDICT_REQUIRED_COLS, VERDICT_NAME)
    detailed_df = read_csv(share_dir / DETAILED_AUDIT_NAME)
    ensure_columns(detailed_df, DETAILED_REQUIRED_COLS, DETAILED_AUDIT_NAME)
    compatibility_summary_df = read_csv(share_dir / MLPE_COMPATIBILITY_SUMMARY_NAME)
    ensure_columns(
        compatibility_summary_df,
        COMPATIBILITY_SUMMARY_REQUIRED_COLS,
        MLPE_COMPATIBILITY_SUMMARY_NAME,
    )
    matching_table_df = read_csv(share_dir / MLPE_MATCHING_TABLE_NAME)
    matching_summary_df = read_csv(share_dir / MLPE_MATCHING_SUMMARY_NAME)
    ensure_columns(
        matching_summary_df,
        MATCHING_SUMMARY_REQUIRED_COLS,
        MLPE_MATCHING_SUMMARY_NAME,
    )

    family_eval_df = read_optional_csv(share_dir / FAMILY_EVAL_NAME)
    attach_candidates_df = read_optional_csv(share_dir / ATTACH_CANDIDATES_NAME)
    detailed_sanity_df = read_optional_csv(share_dir / DETAILED_SANITY_NAME)
    provenance_summary_df = read_optional_csv(share_dir / BYTYPE_PROVENANCE_SUMMARY_NAME)
    rebuild_summary_df = read_optional_csv(share_dir / BYTYPE_REBUILD_SUMMARY_NAME)
    panel_agreement_df = read_optional_csv(share_dir / MLPE_PANEL_AGREEMENT_NAME)
    canonical_dictionary_df = read_optional_csv(share_dir / CANONICAL_DICTIONARY_NAME)

    internal_col = first_existing_column(verdict_df, INTERNAL_COL_CANDIDATES)
    external_col = first_existing_column(verdict_df, EXTERNAL_PATTERN_COL_CANDIDATES)

    fault_df = verdict_df[verdict_df["패널고장여부_ko"].map(normalize_text) == "고장"].copy()
    if fault_df.empty:
        raise SystemExit("no current fault panels found in verdict table")

    family_eval_map = lookup_map(family_eval_df)
    attach_candidates_map = lookup_map(attach_candidates_df)
    detailed_map = lookup_map(detailed_df)
    detailed_sanity_map = lookup_map(detailed_sanity_df)
    panel_agreement_map = lookup_map(panel_agreement_df)

    compatibility_summary_row = compatibility_summary_df.iloc[0].to_dict()
    matching_summary_row = matching_summary_df.iloc[0].to_dict()
    provenance_summary_row = provenance_summary_df.iloc[0].to_dict() if not provenance_summary_df.empty else {}
    rebuild_summary_row = rebuild_summary_df.iloc[0].to_dict() if not rebuild_summary_df.empty else {}

    canonical_map = build_canonical_dictionary_map(canonical_dictionary_df)
    matching_table_map = build_matching_table_map(matching_table_df)

    pack_rows: list[dict[str, object]] = []
    for row in fault_df.to_dict(orient="records"):
        key = as_key(row.get("site"), row.get("panel_id"))
        detailed_row = detailed_map.get(key)
        family_row = family_eval_map.get(key)
        attach_row = attach_candidates_map.get(key)
        agreement_row = panel_agreement_map.get(key)
        sanity_row = detailed_sanity_map.get(key)

        canonical_code = canonicalize_gpvs_code(
            (detailed_row or {}).get("gpvs_detailed_top1_fault_type")
        )
        internal_verdict = normalize_text(row.get(internal_col)) if internal_col else ""
        external_pattern = normalize_text(row.get(external_col)) if external_col else ""
        external_pattern = external_pattern or build_external_pattern(row, canonical_code, canonical_map)

        usefulness = normalize_text((agreement_row or {}).get("overall_gpvs_reference_usefulness_ko"))
        compatibility_judgment = map_usefulness_to_compatibility(
            usefulness,
            normalize_text(compatibility_summary_row.get("final_recommendation_ko")),
        )
        matching_policy = build_matching_policy(canonical_code, canonical_map)
        internal_evidence = build_internal_evidence(family_row, attach_row)
        external_evidence = build_external_evidence(detailed_row, sanity_row)
        final_recommendation = combine_final_recommendation(
            matching_policy,
            compatibility_judgment,
            internal_evidence != "근거 파일 미확인",
            external_evidence != "근거 파일 미확인",
        )

        pack_rows.append(
            {
                "site": normalize_text(row.get("site")),
                "panel_id": normalize_text(row.get("panel_id")),
                "사건유형_ko": normalize_text(row.get("사건유형_ko")),
                "최종고장양상_ko": normalize_text(row.get("최종고장양상_ko")),
                "커널로그_원인군_ko": normalize_text(row.get("커널로그_원인군_ko")),
                "GPVS_내부판정_ko": internal_verdict,
                "GPVS_내부판정근거_ko": internal_evidence,
                "GPVS_외부참조패턴_ko": external_pattern,
                "GPVS_외부참조근거_ko": external_evidence,
                "GPVS_호환성판정_ko": compatibility_judgment,
                "GPVS_호환성근거_ko": build_compatibility_evidence(
                    agreement_row,
                    compatibility_summary_row,
                ),
                "GPVS_매칭정책_ko": matching_policy,
                "GPVS_매칭근거_ko": build_matching_evidence(
                    canonical_code,
                    canonical_map,
                    matching_table_map,
                ),
                "GPVS_최종사용권고_ko": final_recommendation,
                "GPVS_권고사유_ko": build_recommendation_reason(
                    final_recommendation,
                    compatibility_judgment,
                    matching_policy,
                    external_pattern,
                    canonical_code,
                ),
            }
        )

    pack_df = pd.DataFrame(pack_rows).reindex(columns=PACK_COLS)

    summary_row = {
        "fault_panel_count": len(pack_df),
        "internal_evidence_available_count": int(
            (pack_df["GPVS_내부판정근거_ko"] != "근거 파일 미확인").sum()
        ),
        "external_evidence_available_count": int(
            (pack_df["GPVS_외부참조근거_ko"] != "근거 파일 미확인").sum()
        ),
        "compatibility_reference_only_flag": int(
            normalize_text(compatibility_summary_row.get("final_recommendation_ko")) == "참고축으로만 사용"
        ),
        "core_reference_count": int((pack_df["GPVS_최종사용권고_ko"] == "핵심참조").sum()),
        "core_reference_candidate_count": int(
            (pack_df["GPVS_최종사용권고_ko"] == "핵심참조후보").sum()
        ),
        "auxiliary_reference_count": int((pack_df["GPVS_최종사용권고_ko"] == "보조참조").sum()),
        "confounder_flag_count": int((pack_df["GPVS_최종사용권고_ko"] == "교란플래그").sum()),
        "reserved_system_count": int((pack_df["GPVS_최종사용권고_ko"] == "시스템보류").sum()),
        "not_recommended_count": int((pack_df["GPVS_최종사용권고_ko"] == "비권장").sum()),
        "final_operational_rule_ko": "GPVS는 direct root-cause classifier가 아니라 reference layer로만 사용",
        "note_ko": (
            f"compatibility={normalize_text(compatibility_summary_row.get('final_recommendation_ko'))}, "
            f"matching_policy={normalize_text(matching_summary_row.get('final_matching_policy_ko'))}, "
            f"provenance={normalize_text(provenance_summary_row.get('provenance_status')) or '미기록'}, "
            f"rebuild_attachable={normalize_text(rebuild_summary_row.get('current_recovered_attachable_flag')) or '미기록'}"
        ),
    }
    summary_df = pd.DataFrame([summary_row]).reindex(columns=SUMMARY_COLS)

    current_code_counts = {
        code: int(
            (
                detailed_df["gpvs_detailed_top1_fault_type"]
                .map(canonicalize_gpvs_code)
                == code
            ).sum()
        )
        for code in sorted(canonical_map)
    }
    note_lines = [
        "# 1. GPVS 내부판정 근거",
        f"- 현재 fault panel {len(pack_df)}건 중 내부판정 근거가 확인된 패널은 {summary_row['internal_evidence_available_count']}건입니다.",
        "- 내부판정은 family evaluator row가 있으면 prediction_source / fallback_rule / pred_fault_family / vendor_fault_family를 우선 근거로 쓰고, 없으면 attach candidate trace를 보조 근거로 씁니다.",
        "- GPVS 내부판정과 외부참조는 서로 다른 레이어입니다.",
        "",
        "# 2. GPVS 외부참조 근거",
        f"- 외부참조 근거가 확인된 패널은 {summary_row['external_evidence_available_count']}건입니다.",
        f"- by-type provenance={normalize_text(provenance_summary_row.get('provenance_status')) or '미기록'}, rebuild_attachable={normalize_text(rebuild_summary_row.get('current_recovered_attachable_flag')) or '미기록'} 입니다.",
        "- 외부참조는 recovered by-type inference의 top1/top2 score와 margin을 요약한 근거 사례이며 direct root-cause 판정값이 아닙니다.",
        "",
        "# 3. GPVS↔MLPE 호환성 근거",
        f"- compatibility summary는 `{normalize_text(compatibility_summary_row.get('final_recommendation_ko'))}` 입니다.",
        f"- summary note: {normalize_text(compatibility_summary_row.get('note_ko'))}",
        "- reference-only 는 unusable 을 뜻하지 않습니다.",
        "- auxiliary-reference row 는 direct root-cause 사용을 금지한 채 보조참조로는 계속 사용할 수 있습니다.",
        "- 호환성 audit 결과에 따라 GPVS는 reference layer로만 사용합니다.",
        "",
        "# 4. GPVS↔MLPE matching 근거",
        f"- matching summary는 `{normalize_text(matching_summary_row.get('final_matching_policy_ko'))}` 입니다.",
        "- matching 정책에 따라 F0/F4/F5/F2/F3/F1/F6/F7의 사용 등급이 갈립니다.",
        "- 현재 real fault panel support는 "
        + ", ".join(
            f"{code}={count}"
            for code, count in current_code_counts.items()
            if count > 0
        )
        + " 입니다.",
        "",
        "# 5. 현재 운영 원칙",
        "- GPVS 내부판정과 외부참조는 서로 다른 레이어다.",
        "- 외부참조는 근거 사례이지 direct root-cause 판정값이 아니다.",
        "- 호환성 audit 결과에 따라 GPVS는 reference layer로만 사용한다.",
        "- matching 정책에 따라 F0/F4/F5/F2/F3/F1/F6/F7의 사용 등급이 갈린다.",
        "- GPVS는 direct root-cause classifier가 아니라 reference layer로만 사용한다.",
    ]

    output_pack_path = share_dir / OUTPUT_PACK_NAME
    output_summary_path = share_dir / OUTPUT_SUMMARY_NAME
    output_note_path = share_dir / OUTPUT_NOTE_NAME
    output_pack_path.parent.mkdir(parents=True, exist_ok=True)

    pack_df.to_csv(output_pack_path, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_summary_path, index=False, encoding="utf-8-sig")
    output_note_path.write_text("\n".join(note_lines).strip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
