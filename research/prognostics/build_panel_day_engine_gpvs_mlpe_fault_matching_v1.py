#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]

PANEL_MULTIAXIS_VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
GPVS_MLPE_PANEL_AGREEMENT_NAME = "panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv"
GPVS_MLPE_COMPATIBILITY_SUMMARY_NAME = "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv"
GPVS_DETAILED_AUDIT_NAME = "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv"

OUTPUT_CANONICAL_DICTIONARY_NAME = "panel_day_engine_gpvs_canonical_dictionary_v1.csv"
OUTPUT_MATCHING_TABLE_NAME = "panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv"
OUTPUT_SUMMARY_NAME = "panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv"
OUTPUT_NOTE_NAME = "panel_day_engine_gpvs_mlpe_fault_matching_note_v1.md"

CANONICAL_DICTIONARY_COLS = [
    "canonical_gpvs_code",
    "current_usage_tier_ko",
    "mlpe_reference_family_ko",
    "mlpe_reference_name_ko",
    "usage_rule_ko",
    "current_real_fault_support_count",
    "note_ko",
]

MATCHING_TABLE_COLS = [
    "mlpe_official_fault_ko",
    "canonical_gpvs_code",
    "match_strength_ko",
    "match_role_ko",
    "evidence_basis_ko",
    "current_real_fault_support_count",
    "recommendation_ko",
]

SUMMARY_COLS = [
    "canonical_code_count",
    "core_reference_count",
    "auxiliary_reference_count",
    "confounder_count",
    "reserved_system_count",
    "final_matching_policy_ko",
    "note_ko",
]

CANONICAL_CODES = [f"F{idx}" for idx in range(8)]

CANONICAL_POLICY = {
    "F0": {
        "current_usage_tier_ko": "baseline",
        "mlpe_reference_family_ko": "정상 기준",
        "mlpe_reference_name_ko": "정상 기준선",
        "usage_rule_ko": "비고장 기준선과 drift 비교에만 사용",
        "base_note_ko": "front-facing matching에서는 fault명이 아니라 baseline reference로만 노출",
    },
    "F1": {
        "current_usage_tier_ko": "reserved_system_level",
        "mlpe_reference_family_ko": "시스템/전력변환",
        "mlpe_reference_name_ko": "인버터 전력변환부 시스템 시나리오",
        "usage_rule_ko": "MLPE direct fault명이 아니라 통합 결과표 후보축으로만 보류",
        "base_note_ko": "current panel set direct support가 없어 system-level reserve로만 유지",
    },
    "F2": {
        "current_usage_tier_ko": "auxiliary_reference",
        "mlpe_reference_family_ko": "제어·계측 힌트",
        "mlpe_reference_name_ko": "제어/계측 이상 보조 힌트",
        "usage_rule_ko": "direct root-cause가 아니라 제어·계측 이상 힌트로만 사용",
        "base_note_ko": "current panel set에서 direct root-cause matching보다 auxiliary hint 성격이 강함",
    },
    "F3": {
        "current_usage_tier_ko": "confounder_only",
        "mlpe_reference_family_ko": "계통 교란",
        "mlpe_reference_name_ko": "계통 교란 플래그",
        "usage_rule_ko": "fault label이 아니라 confounder flag로만 사용",
        "base_note_ko": "real-panel direct support가 없어 confounder-only로 유지",
    },
    "F4": {
        "current_usage_tier_ko": "core_reference",
        "mlpe_reference_family_ko": "패널·어레이 불균형",
        "mlpe_reference_name_ko": "패널·어레이 mismatch 핵심 참조",
        "usage_rule_ko": "MLPE 패널·어레이 불균형 해석의 핵심 reference로 사용",
        "base_note_ko": "current panel set에서 가장 유용한 panel/array imbalance reference code",
    },
    "F5": {
        "current_usage_tier_ko": "core_reference_candidate",
        "mlpe_reference_family_ko": "패널·어레이 불균형",
        "mlpe_reference_name_ko": "부분 개방회로 계열 핵심 참조 후보",
        "usage_rule_ko": "케이블 접점불량(단선) 가설의 핵심 reference candidate로 유지",
        "base_note_ko": "current panel set direct support는 약하지만 semantics상 살려둘 가치가 큼",
    },
    "F6": {
        "current_usage_tier_ko": "reserved_system_level",
        "mlpe_reference_family_ko": "제어기/시스템",
        "mlpe_reference_name_ko": "제어기 gain 이상 시스템 시나리오",
        "usage_rule_ko": "MLPE direct fault명이 아니라 통합 결과표 후보축으로만 보류",
        "base_note_ko": "system-level reserve code로만 유지",
    },
    "F7": {
        "current_usage_tier_ko": "reserved_system_level",
        "mlpe_reference_family_ko": "제어기/시스템",
        "mlpe_reference_name_ko": "제어기 시정수 이상 시스템 시나리오",
        "usage_rule_ko": "MLPE direct fault명이 아니라 통합 결과표 후보축으로만 보류",
        "base_note_ko": "system-level reserve code로만 유지",
    },
}

MATCHING_POLICY = [
    {
        "mlpe_official_fault_ko": "정션박스 손상",
        "canonical_gpvs_code": "F4",
        "match_strength_ko": "강",
        "match_role_ko": "핵심참조",
        "evidence_basis_template_ko": "F4는 PV 어레이 mismatch 계열이며 current real fault panel support={support}건, scenario partial alignment={scenario_partial}건으로 panel/array imbalance 해석에 가장 직접적이다",
        "recommendation_ko": "reference layer에서 우선 확인하되 direct root-cause로 단정하지 않음",
    },
    {
        "mlpe_official_fault_ko": "케이블 접점불량(단선)",
        "canonical_gpvs_code": "F5",
        "match_strength_ko": "강",
        "match_role_ko": "핵심참조",
        "evidence_basis_template_ko": "F5는 부분 개방회로 시나리오라 케이블 접점불량(단선)과 가장 가깝지만 current real fault panel support={support}건이라 아직 candidate 성격이 크다",
        "recommendation_ko": "core reference candidate로 유지하고 현 패널셋 direct evidence가 쌓일 때까지 조건부 사용",
    },
    {
        "mlpe_official_fault_ko": "모듈 경년 열화",
        "canonical_gpvs_code": "F4",
        "match_strength_ko": "중",
        "match_role_ko": "보조참조",
        "evidence_basis_template_ko": "F4는 출력 불균형 방향을 포착하므로 경년 열화의 결과적 mismatch와 겹칠 수 있으나 one-to-one는 아니다; current support={support}건",
        "recommendation_ko": "조건부 reference로만 사용",
    },
    {
        "mlpe_official_fault_ko": "모듈 내 누전 추적",
        "canonical_gpvs_code": "",
        "match_strength_ko": "없음",
        "match_role_ko": "비권장",
        "evidence_basis_template_ko": "current GPVS canonical code space에는 누전 추적을 직접 가리키는 row-level match가 없다",
        "recommendation_ko": "GPVS direct matching 사용 비권장",
    },
    {
        "mlpe_official_fault_ko": "인버터/스트링 동작 불량",
        "canonical_gpvs_code": "F2",
        "match_strength_ko": "약",
        "match_role_ko": "보조참조",
        "evidence_basis_template_ko": "F2 current support={support}건이 있지만 scenario conflict={scenario_conflict}건이라 direct fault명보다 제어·계측 이상 힌트로만 읽어야 한다",
        "recommendation_ko": "제어·계측 이상 힌트로만 사용",
    },
    {
        "mlpe_official_fault_ko": "인버터/스트링 동작 불량",
        "canonical_gpvs_code": "F3",
        "match_strength_ko": "약",
        "match_role_ko": "교란플래그",
        "evidence_basis_template_ko": "F3는 계통 교란 confounder code이며 current support={support}건으로 fault classifier보다 disturbance flag 성격이 강하다",
        "recommendation_ko": "교란 플래그로만 유지",
    },
    {
        "mlpe_official_fault_ko": "인버터/스트링 동작 불량",
        "canonical_gpvs_code": "F1",
        "match_strength_ko": "약",
        "match_role_ko": "시스템보류",
        "evidence_basis_template_ko": "F1는 인버터/전력변환부 system-level scenario이며 current support={support}건이라 MLPE panel verdict direct mapping을 보류한다",
        "recommendation_ko": "통합 결과표 후보축으로만 보류",
    },
    {
        "mlpe_official_fault_ko": "인버터/스트링 동작 불량",
        "canonical_gpvs_code": "F6",
        "match_strength_ko": "약",
        "match_role_ko": "시스템보류",
        "evidence_basis_template_ko": "F6는 제어기 gain 이상 system-level scenario이며 current support={support}건이라 MLPE panel verdict direct mapping을 보류한다",
        "recommendation_ko": "통합 결과표 후보축으로만 보류",
    },
    {
        "mlpe_official_fault_ko": "인버터/스트링 동작 불량",
        "canonical_gpvs_code": "F7",
        "match_strength_ko": "약",
        "match_role_ko": "시스템보류",
        "evidence_basis_template_ko": "F7는 제어기 시정수 이상 system-level scenario이며 current support={support}건이라 MLPE panel verdict direct mapping을 보류한다",
        "recommendation_ko": "통합 결과표 후보축으로만 보류",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Formalize what MLPE fault classes GPVS can currently help detect."
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


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def canonicalize_gpvs_code(value: object) -> str:
    text = normalize_text(value)
    match = re.match(r"^(F[0-7])", text)
    return match.group(1) if match else ""


def normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in normalized.columns:
        if normalized[column].dtype == object:
            normalized[column] = normalized[column].map(normalize_text)
    return normalized


def load_inputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    share_dir = root / "_share"
    verdict_df = normalize_frame(read_csv(share_dir / PANEL_MULTIAXIS_VERDICT_NAME))
    agreement_df = normalize_frame(read_csv(share_dir / GPVS_MLPE_PANEL_AGREEMENT_NAME))
    compatibility_summary_df = normalize_frame(read_csv(share_dir / GPVS_MLPE_COMPATIBILITY_SUMMARY_NAME))
    detailed_audit_df = normalize_frame(read_csv(share_dir / GPVS_DETAILED_AUDIT_NAME))

    ensure_columns(
        verdict_df,
        ["site", "panel_id", "패널고장여부_ko", "GPVS_세부fault_code", "GPVS_참고유형_ko", "GPVS_시나리오명_ko"],
        PANEL_MULTIAXIS_VERDICT_NAME,
    )
    ensure_columns(
        agreement_df,
        [
            "site",
            "panel_id",
            "overall_gpvs_reference_usefulness_ko",
            "scenario_vs_kernellog_alignment_ko",
            "family_vs_kernellog_alignment_ko",
        ],
        GPVS_MLPE_PANEL_AGREEMENT_NAME,
    )
    ensure_columns(
        compatibility_summary_df,
        ["final_recommendation_ko", "note_ko"],
        GPVS_MLPE_COMPATIBILITY_SUMMARY_NAME,
    )
    ensure_columns(
        detailed_audit_df,
        ["site", "panel_id", "gpvs_detailed_top1_fault_type"],
        GPVS_DETAILED_AUDIT_NAME,
    )
    return verdict_df, agreement_df, compatibility_summary_df, detailed_audit_df


def build_fault_panel_context(
    verdict_df: pd.DataFrame,
    agreement_df: pd.DataFrame,
    detailed_audit_df: pd.DataFrame,
) -> pd.DataFrame:
    fault_df = verdict_df.loc[verdict_df["패널고장여부_ko"].eq("고장")].copy()
    if len(fault_df) != 6:
        raise SystemExit(f"{PANEL_MULTIAXIS_VERDICT_NAME} must contain exactly 6 fault rows, found {len(fault_df)}")

    audit_subset = detailed_audit_df[["site", "panel_id", "gpvs_detailed_top1_fault_type"]].copy()
    audit_subset["audit_canonical_gpvs_code"] = audit_subset["gpvs_detailed_top1_fault_type"].map(canonicalize_gpvs_code)

    fault_df["canonical_gpvs_code"] = fault_df["GPVS_세부fault_code"].map(canonicalize_gpvs_code)
    merged = fault_df.merge(
        audit_subset[["site", "panel_id", "audit_canonical_gpvs_code"]],
        on=["site", "panel_id"],
        how="left",
    ).merge(
        agreement_df,
        on=["site", "panel_id"],
        how="left",
    )

    mismatch_df = merged.loc[
        merged["audit_canonical_gpvs_code"].map(normalize_text).ne("")
        & merged["canonical_gpvs_code"].map(normalize_text).ne(merged["audit_canonical_gpvs_code"].map(normalize_text))
    ].copy()
    if not mismatch_df.empty:
        raise SystemExit(
            "current attached GPVS canonical code and detailed audit top1 code disagree: "
            + mismatch_df[["site", "panel_id", "canonical_gpvs_code", "audit_canonical_gpvs_code"]].to_string(index=False)
        )
    return merged


def build_code_stats(fault_context_df: pd.DataFrame) -> dict[str, dict[str, int]]:
    stats: dict[str, dict[str, int]] = {}
    for canonical_code in CANONICAL_CODES:
        code_df = fault_context_df.loc[fault_context_df["canonical_gpvs_code"].eq(canonical_code)].copy()
        stats[canonical_code] = {
            "support": int(len(code_df)),
            "useful": int(code_df["overall_gpvs_reference_usefulness_ko"].eq("참고가능").sum()),
            "caution": int(code_df["overall_gpvs_reference_usefulness_ko"].eq("주의참고").sum()),
            "notrec": int(code_df["overall_gpvs_reference_usefulness_ko"].eq("비권장").sum()),
            "scenario_conflict": int(code_df["scenario_vs_kernellog_alignment_ko"].eq("불일치").sum()),
            "scenario_partial": int(code_df["scenario_vs_kernellog_alignment_ko"].eq("부분일치").sum()),
            "family_align": int(code_df["family_vs_kernellog_alignment_ko"].eq("일치").sum()),
            "family_partial": int(code_df["family_vs_kernellog_alignment_ko"].eq("부분일치").sum()),
        }
    return stats


def build_canonical_dictionary_df(code_stats: dict[str, dict[str, int]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for canonical_code in CANONICAL_CODES:
        policy = CANONICAL_POLICY[canonical_code]
        stats = code_stats[canonical_code]
        note = policy["base_note_ko"]
        support = stats["support"]
        if support > 0:
            note = (
                f"real fault support {support}건; panel agreement useful/caution/notrec="
                f"{stats['useful']}/{stats['caution']}/{stats['notrec']}"
            )
        rows.append(
            {
                "canonical_gpvs_code": canonical_code,
                "current_usage_tier_ko": policy["current_usage_tier_ko"],
                "mlpe_reference_family_ko": policy["mlpe_reference_family_ko"],
                "mlpe_reference_name_ko": policy["mlpe_reference_name_ko"],
                "usage_rule_ko": policy["usage_rule_ko"],
                "current_real_fault_support_count": support,
                "note_ko": note,
            }
        )
    return pd.DataFrame(rows).reindex(columns=CANONICAL_DICTIONARY_COLS)


def build_matching_table_df(code_stats: dict[str, dict[str, int]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for item in MATCHING_POLICY:
        canonical_code = item["canonical_gpvs_code"]
        stats = code_stats.get(canonical_code, {"support": 0, "scenario_partial": 0, "scenario_conflict": 0})
        evidence_basis = item["evidence_basis_template_ko"].format(
            support=stats.get("support", 0),
            scenario_partial=stats.get("scenario_partial", 0),
            scenario_conflict=stats.get("scenario_conflict", 0),
        )
        rows.append(
            {
                "mlpe_official_fault_ko": item["mlpe_official_fault_ko"],
                "canonical_gpvs_code": canonical_code,
                "match_strength_ko": item["match_strength_ko"],
                "match_role_ko": item["match_role_ko"],
                "evidence_basis_ko": evidence_basis,
                "current_real_fault_support_count": stats.get("support", 0),
                "recommendation_ko": item["recommendation_ko"],
            }
        )
    return pd.DataFrame(rows).reindex(columns=MATCHING_TABLE_COLS)


def build_summary_df(
    compatibility_summary_df: pd.DataFrame,
    canonical_dictionary_df: pd.DataFrame,
) -> pd.DataFrame:
    tier_series = canonical_dictionary_df["current_usage_tier_ko"].map(normalize_text)
    compatibility_row = compatibility_summary_df.iloc[0].to_dict() if not compatibility_summary_df.empty else {}
    compatibility_recommendation = normalize_text(compatibility_row.get("final_recommendation_ko", ""))

    core_reference_count = int(tier_series.isin(["baseline", "core_reference", "core_reference_candidate"]).sum())
    auxiliary_reference_count = int(tier_series.eq("auxiliary_reference").sum())
    confounder_count = int(tier_series.eq("confounder_only").sum())
    reserved_system_count = int(tier_series.eq("reserved_system_level").sum())

    final_matching_policy = "F0/F4/F5 core, F2 auxiliary, F3 confounder, F1/F6/F7 reserved"
    note = (
        f"compatibility final recommendation={compatibility_recommendation or '미기재'}. "
        "따라서 이 matching table은 direct root-cause classifier가 아니라 reference-layer 운영 규칙으로만 사용한다."
    )

    return pd.DataFrame(
        [
            {
                "canonical_code_count": len(canonical_dictionary_df),
                "core_reference_count": core_reference_count,
                "auxiliary_reference_count": auxiliary_reference_count,
                "confounder_count": confounder_count,
                "reserved_system_count": reserved_system_count,
                "final_matching_policy_ko": final_matching_policy,
                "note_ko": note,
            }
        ]
    ).reindex(columns=SUMMARY_COLS)


def build_note_md(
    compatibility_summary_df: pd.DataFrame,
    canonical_dictionary_df: pd.DataFrame,
    matching_table_df: pd.DataFrame,
) -> str:
    compatibility_row = compatibility_summary_df.iloc[0].to_dict() if not compatibility_summary_df.empty else {}
    compatibility_recommendation = normalize_text(compatibility_row.get("final_recommendation_ko", ""))

    core_codes = canonical_dictionary_df.loc[
        canonical_dictionary_df["current_usage_tier_ko"].isin(["baseline", "core_reference", "core_reference_candidate"]),
        "canonical_gpvs_code",
    ].tolist()
    auxiliary_codes = canonical_dictionary_df.loc[
        canonical_dictionary_df["current_usage_tier_ko"].eq("auxiliary_reference"),
        "canonical_gpvs_code",
    ].tolist()
    confounder_codes = canonical_dictionary_df.loc[
        canonical_dictionary_df["current_usage_tier_ko"].eq("confounder_only"),
        "canonical_gpvs_code",
    ].tolist()
    reserved_codes = canonical_dictionary_df.loc[
        canonical_dictionary_df["current_usage_tier_ko"].eq("reserved_system_level"),
        "canonical_gpvs_code",
    ].tolist()

    return "\n".join(
        [
            "# panel_day_engine_gpvs_mlpe_fault_matching_note_v1",
            "",
            "## 1. 왜 matching table이 필요한가",
            "- GPVS는 현재 direct root-cause classifier가 아니라 reference layer다.",
            "- 그래서 어떤 code를 front-facing하게 살리고, 어떤 code는 교란/보류로만 둘지를 명시적으로 고정할 필요가 있다.",
            f"- 현재 compatibility audit 최종 권고는 `{compatibility_recommendation}` 이고, 이번 table은 그 제한을 전제로 쓴다.",
            "",
            "## 2. 지금 살리는 코드",
            f"- 현재 살리는 front-facing canonical code는 {', '.join(core_codes)} 이다.",
            "- F4/F5는 MLPE 패널·어레이 불균형 해석에 가장 유용하다.",
            "- F0는 fault명이 아니라 baseline reference로만 남긴다.",
            "",
            "## 3. 지금 보조로만 남기는 코드",
            f"- 보조로만 남기는 code는 {', '.join(auxiliary_codes)} 이다.",
            "- F2는 direct root-cause보다는 제어·계측 이상 힌트로만 쓴다.",
            "- 즉, F2가 나와도 실제 패널 physical fault명으로 번역하지 않는다.",
            "",
            "## 4. 지금 교란/보류로 두는 코드",
            f"- 교란 플래그 code는 {', '.join(confounder_codes)} 이다.",
            f"- 시스템 보류 code는 {', '.join(reserved_codes)} 이다.",
            "- F3는 교란 플래그로만 남긴다.",
            "- F1/F6/F7은 통합 결과표 후보축으로만 보류한다.",
            "",
            "## 5. 현재 운영 원칙",
            "- GPVS는 reference layer이며 MLPE 공식 fault verdict를 직접 대체하지 않는다.",
            "- L/M은 front-facing matching에서는 제거한다.",
            "- front-facing 표현은 `세부시나리오 F4`, `세부시나리오 F5` 같은 canonical code 중심으로 유지한다.",
            "- direct physical root-cause naming은 현재 matching table 바깥에서 금지한다.",
        ]
    ) + "\n"


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    verdict_df, agreement_df, compatibility_summary_df, detailed_audit_df = load_inputs(root)
    fault_context_df = build_fault_panel_context(verdict_df, agreement_df, detailed_audit_df)
    code_stats = build_code_stats(fault_context_df)

    canonical_dictionary_df = build_canonical_dictionary_df(code_stats)
    matching_table_df = build_matching_table_df(code_stats)
    summary_df = build_summary_df(compatibility_summary_df, canonical_dictionary_df)
    note_md = build_note_md(compatibility_summary_df, canonical_dictionary_df, matching_table_df)

    canonical_dictionary_df.to_csv(share_dir / OUTPUT_CANONICAL_DICTIONARY_NAME, index=False, encoding="utf-8-sig")
    matching_table_df.to_csv(share_dir / OUTPUT_MATCHING_TABLE_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / OUTPUT_SUMMARY_NAME, index=False, encoding="utf-8-sig")
    (share_dir / OUTPUT_NOTE_NAME).write_text(note_md, encoding="utf-8")


if __name__ == "__main__":
    main()
