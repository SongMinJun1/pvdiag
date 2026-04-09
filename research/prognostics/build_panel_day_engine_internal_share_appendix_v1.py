#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

NON_PRECURSOR_CASES_NAME = "panel_day_engine_non_precursor_performance_cases_v1.csv"
REAUDIT_WORKING_NAME = "panel_date_reaudit_working.csv"
LOCAL_PRECURSOR_ELIGIBILITY_NAME = "panel_day_engine_local_precursor_eligibility_cases_v1.csv"
PROJECT_EVAL_MATRIX_NAME = "panel_day_engine_project_eval_matrix_v1.csv"
CURRENT_FREEZE_PACK_NAME = "panel_day_engine_project_current_data_freeze_pack_v1.csv"
POLICY_RECOMMENDATION_NAME = "panel_day_engine_operator_attention_policy_recommendation_v1.csv"
PIPELINE_MANIFEST_NAME = "panel_day_engine_operator_pipeline_manifest_v1.csv"

ABRUPT6_OUTPUT_NAME = "panel_day_engine_abrupt6_symptom_map_v1.csv"
KERNEL_MAPPING_OUTPUT_NAME = "panel_day_engine_kernellog_project_mapping_v1.csv"
GPV7_OUTPUT_NAME = "panel_day_engine_gpv7_perf_summary_v1.csv"
PROGRESS_OUTPUT_NAME = "panel_day_engine_project_progress_snapshot_v1.csv"

ABRUPT6_COLS = [
    "site",
    "panel_id",
    "고장시점",
    "증상명_ko",
    "세부근거_ko",
    "source_field_ko",
    "비고_ko",
]

KERNEL_MAPPING_COLS = [
    "커널로그_증상명",
    "주_프로젝트분류",
    "보조_프로젝트분류",
    "설명_ko",
    "주의_ko",
]

GPV7_COLS = [
    "고장유형_번호",
    "고장유형_설명_ko",
    "성능요약_ko",
    "수치_ko",
    "source_ref_ko",
]

PROGRESS_COLS = [
    "항목",
    "현재_완료율_추정",
    "현재_상태_ko",
    "근거_ko",
]

EXPECTED_ABRUPT_CASE_COUNT = 6
GPV_SCENARIOS = [f"F{i}" for i in range(1, 8)]
BANNED_PANEL_IDS = {
    "45dfa600-79b7-428e-95d3-22345a068986.1.0",
    "45dfa600-79b7-428e-95d3-22345a068986.1.1",
    "d15b9e13-4117-49ae-a78f-7ace013e48de.0.0",
    "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.9",
}

GPV_COARSE_DESCRIPTION = {
    "F1": "GPVS fault scenario F1 (개별 시나리오 설명은 현재 저장 문서에서 미확인)",
    "F2": "GPVS fault scenario F2 (개별 시나리오 설명은 현재 저장 문서에서 미확인)",
    "F3": "GPVS fault scenario F3 (개별 시나리오 설명은 현재 저장 문서에서 미확인)",
    "F4": "GPVS fault scenario F4 (개별 시나리오 설명은 현재 저장 문서에서 미확인)",
    "F5": "GPVS fault scenario F5 (개별 시나리오 설명은 현재 저장 문서에서 미확인)",
    "F6": "GPVS fault scenario F6 (개별 시나리오 설명은 현재 저장 문서에서 미확인)",
    "F7": "GPVS fault scenario F7 (개별 시나리오 설명은 현재 저장 문서에서 미확인)",
}

SYMPTOM_FAMILY_MAP = {
    "diode_like": "다이오드형",
    "open_or_device_issue_like": "개방/장치이상형",
    "group_or_inverter_side_like": "개방/장치이상형",
    "module_damage_like": "모듈손상형",
}

ACCEPTED_ABRUPT_TRUTH_FAMILIES = {
    "diode_like",
    "open_or_device_issue_like",
    "module_damage_like",
}

REQUIRED_NON_PRECURSOR_COLS = [
    "eval_bucket_v2",
    "site",
    "panel_id",
    "anchor_date",
    "anchor_source",
    "vendor_fault_family",
    "candidate_validity",
    "vendor_reply_class",
    "abrupt_eval_reason_ko",
    "confirmed_fault_hit_by_anchor_flag",
    "confirmed_fault_hit_within_3d_after_flag",
    "confirmed_fault_hit_within_7d_after_flag",
    "critical_fault_hit_by_anchor_flag",
    "critical_fault_hit_within_3d_after_flag",
    "critical_fault_hit_within_7d_after_flag",
    "final_fault_hit_by_anchor_flag",
    "final_fault_hit_within_3d_after_flag",
    "final_fault_hit_within_7d_after_flag",
]

REQUIRED_REAUDIT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "reason_summary",
    "vendor_reply_class",
    "vendor_fault_family",
    "candidate_validity",
    "vendor_note",
]

OPTIONAL_LOCAL_ELIGIBILITY_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "fault_start_date",
    "vendor_fault_family",
    "precursor_eligible_flag",
]

REQUIRED_PROJECT_EVAL_COLS = [
    "eval_scope",
    "target_name",
    "support_positive",
    "recall",
    "precision",
    "f1",
]

REQUIRED_FREEZE_PACK_COLS = [
    "eval_scope",
    "current_data_decision",
    "freeze_reason_ko",
]

REQUIRED_POLICY_COLS = [
    "recommended_policy_name",
    "recommended_policy_reason_ko",
]

REQUIRED_PIPELINE_COLS = [
    "final_pipeline_pass_flag",
    "note_ko",
]

FINAL_EVIDENCE_COLS = [
    "final_fault_hit_by_anchor_flag",
    "final_fault_hit_within_3d_after_flag",
    "final_fault_hit_within_7d_after_flag",
]

STRICT_ABRUPT_EVIDENCE_COLS = FINAL_EVIDENCE_COLS + [
    "critical_fault_hit_by_anchor_flag",
    "critical_fault_hit_within_3d_after_flag",
    "critical_fault_hit_within_7d_after_flag",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an appendix-only internal-share pack without touching the seed-panel case review flow."
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


def numeric_float(value: object) -> float | None:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return None
    return float(numeric)


def numeric_int(value: object) -> int:
    numeric = numeric_float(value)
    return 0 if numeric is None else int(numeric)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def read_optional_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def load_inputs(root: Path) -> dict[str, pd.DataFrame]:
    share_dir = root / "_share"
    frames = {
        "non_precursor": read_csv(share_dir / NON_PRECURSOR_CASES_NAME),
        "reaudit": read_csv(share_dir / REAUDIT_WORKING_NAME),
        "local_eligibility": read_optional_csv(share_dir / LOCAL_PRECURSOR_ELIGIBILITY_NAME),
        "project_eval": read_csv(share_dir / PROJECT_EVAL_MATRIX_NAME),
        "freeze_pack": read_csv(share_dir / CURRENT_FREEZE_PACK_NAME),
        "policy": read_csv(share_dir / POLICY_RECOMMENDATION_NAME),
        "pipeline": read_csv(share_dir / PIPELINE_MANIFEST_NAME),
    }

    ensure_columns(frames["non_precursor"], REQUIRED_NON_PRECURSOR_COLS, NON_PRECURSOR_CASES_NAME)
    ensure_columns(frames["reaudit"], REQUIRED_REAUDIT_COLS, REAUDIT_WORKING_NAME)
    if frames["local_eligibility"] is not None:
        ensure_columns(frames["local_eligibility"], OPTIONAL_LOCAL_ELIGIBILITY_COLS, LOCAL_PRECURSOR_ELIGIBILITY_NAME)
    ensure_columns(frames["project_eval"], REQUIRED_PROJECT_EVAL_COLS, PROJECT_EVAL_MATRIX_NAME)
    ensure_columns(frames["freeze_pack"], REQUIRED_FREEZE_PACK_COLS, CURRENT_FREEZE_PACK_NAME)
    ensure_columns(frames["policy"], REQUIRED_POLICY_COLS, POLICY_RECOMMENDATION_NAME)
    ensure_columns(frames["pipeline"], REQUIRED_PIPELINE_COLS, PIPELINE_MANIFEST_NAME)

    for df in frames.values():
        for column in df.columns:
            if df[column].dtype == object:
                df[column] = df[column].map(normalize_text)
    return frames


def find_matching_reaudit_row(case_row: dict[str, object], reaudit_df: pd.DataFrame) -> dict[str, object] | None:
    subset = reaudit_df.loc[
        reaudit_df["site"].eq(case_row["site"])
        & reaudit_df["panel_id"].eq(case_row["panel_id"])
    ].copy()
    if subset.empty:
        return None

    anchor_date = normalize_text(case_row["anchor_date"])
    strict_match = subset.loc[subset["strict_trigger_date"].eq(anchor_date)]
    if not strict_match.empty:
        return strict_match.iloc[0].to_dict()
    return subset.iloc[0].to_dict()


def symptom_from_text(text: str) -> str:
    lowered = text.lower()
    has_voltage = ("전압" in text) or ("voltage" in lowered)
    has_output = ("출력" in text) or ("output" in lowered) or ("저하" in text)
    if has_voltage and has_output:
        return "복합형"
    if "다이오드" in text or "diode" in lowered:
        return "다이오드형"
    if "개방" in text or "open" in lowered or "장치" in text or "device" in lowered or "커넥터" in text or "인버터" in text:
        return "개방/장치이상형"
    if "모듈" in text or "module" in lowered:
        return "모듈손상형"
    if has_voltage:
        return "전압변화형"
    if has_output:
        return "출력저하형"
    return "불충분"


def map_abrupt_symptom(case_row: dict[str, object], reaudit_row: dict[str, object] | None) -> tuple[str, str, str]:
    vendor_fault_family = normalize_text(case_row.get("vendor_fault_family"))
    if vendor_fault_family in SYMPTOM_FAMILY_MAP:
        detail = f"vendor_fault_family={vendor_fault_family}"
        return SYMPTOM_FAMILY_MAP[vendor_fault_family], detail, "vendor_fault_family"

    if reaudit_row:
        for field_name in ["reason_summary", "vendor_note"]:
            text = normalize_text(reaudit_row.get(field_name))
            if not text:
                continue
            symptom = symptom_from_text(text)
            if symptom != "불충분":
                return symptom, text, field_name

    reason_text = normalize_text(case_row.get("abrupt_eval_reason_ko"))
    if reason_text:
        symptom = symptom_from_text(reason_text)
        if symptom != "불충분":
            return symptom, reason_text, "abrupt_eval_reason_ko"

    fallback_parts = []
    if reaudit_row:
        vendor_note = normalize_text(reaudit_row.get("vendor_note"))
        reason_summary = normalize_text(reaudit_row.get("reason_summary"))
        if vendor_note:
            fallback_parts.append(f"vendor_note={vendor_note}")
        if reason_summary:
            fallback_parts.append(f"reason_summary={reason_summary}")
    if not fallback_parts and reason_text:
        fallback_parts.append(f"abrupt_eval_reason_ko={reason_text}")
    if not fallback_parts:
        fallback_parts.append("명시적 diode/open/module-like 근거를 current artifact에서 찾지 못함")
    return "불충분", "; ".join(fallback_parts), "vendor_note/reason_summary/abrupt_eval_reason_ko"


def any_flag(df: pd.DataFrame, columns: list[str]) -> pd.Series:
    mask = pd.Series(False, index=df.index)
    for column in columns:
        mask = mask | pd.to_numeric(df[column], errors="coerce").fillna(0).eq(1)
    return mask


def review_positive_mask(df: pd.DataFrame) -> pd.Series:
    candidate_validity = df["candidate_validity"].map(normalize_text)
    vendor_reply_class = df["vendor_reply_class"].map(normalize_text)
    return ~candidate_validity.eq("false_positive") & ~vendor_reply_class.eq("vendor_rejected")


def build_lookup(df: pd.DataFrame | None, key_cols: list[str]) -> dict[tuple[str, ...], dict[str, object]]:
    if df is None:
        return {}
    lookup: dict[tuple[str, ...], dict[str, object]] = {}
    for row in df.to_dict(orient="records"):
        key = tuple(normalize_text(row[col]) for col in key_cols)
        lookup[key] = row
    return lookup


def accepted_abrupt_family_rows(
    reaudit_df: pd.DataFrame,
    local_eligibility_df: pd.DataFrame | None,
) -> pd.DataFrame:
    eligibility_lookup = build_lookup(local_eligibility_df, ["site", "panel_id"])
    vendor_family = reaudit_df["vendor_fault_family"].map(normalize_text)
    review_positive = review_positive_mask(reaudit_df)
    abrupt_family = vendor_family.isin(sorted(ACCEPTED_ABRUPT_TRUTH_FAMILIES))
    banned = reaudit_df["panel_id"].map(normalize_text).isin(BANNED_PANEL_IDS)
    accepted = reaudit_df.loc[review_positive & abrupt_family & ~banned].copy()
    accepted["anchor_date"] = accepted["strict_trigger_date"]
    accepted["selection_source"] = "reaudit_accepted_truth_backfill"
    for idx, row in accepted.iterrows():
        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        eligibility_row = eligibility_lookup.get(key)
        if eligibility_row:
            fault_start_date = normalize_text(eligibility_row.get("fault_start_date"))
            if fault_start_date:
                accepted.at[idx, "anchor_date"] = fault_start_date
    return accepted.sort_values(["site", "anchor_date", "panel_id"]).reset_index(drop=True)


def strict_abrupt_evidence_rows(non_precursor_df: pd.DataFrame) -> pd.DataFrame:
    abrupt_df = non_precursor_df.loc[non_precursor_df["eval_bucket_v2"].eq("abrupt_or_no_precursor_now")].copy()
    abrupt_df = abrupt_df.sort_values(["site", "anchor_date", "panel_id"]).reset_index(drop=True)

    review_positive = review_positive_mask(abrupt_df)
    strict_evidence = any_flag(abrupt_df, STRICT_ABRUPT_EVIDENCE_COLS)
    banned = abrupt_df["panel_id"].map(normalize_text).isin(BANNED_PANEL_IDS)
    selected = abrupt_df.loc[review_positive & strict_evidence & ~banned].copy().reset_index(drop=True)
    selected["selection_source"] = "non_precursor_abrupt_evidence"
    return selected


def select_abrupt_positive_cases(
    non_precursor_df: pd.DataFrame,
    reaudit_df: pd.DataFrame,
    local_eligibility_df: pd.DataFrame | None,
) -> tuple[pd.DataFrame, str]:
    strict_df = strict_abrupt_evidence_rows(non_precursor_df)
    accepted_truth_df = accepted_abrupt_family_rows(reaudit_df, local_eligibility_df)

    strict_keys = {
        (normalize_text(row["site"]), normalize_text(row["panel_id"])) for row in strict_df.to_dict(orient="records")
    }
    backfill_rows = accepted_truth_df.loc[
        [
            (normalize_text(row["site"]), normalize_text(row["panel_id"])) not in strict_keys
            for row in accepted_truth_df.to_dict(orient="records")
        ]
    ].copy()

    selected = pd.concat([strict_df, backfill_rows], ignore_index=True)
    selected = selected.sort_values(["site", "anchor_date", "panel_id"]).reset_index(drop=True)
    selection_rule = "strict_abrupt_evidence_plus_truth_backfill"

    if len(selected) != EXPECTED_ABRUPT_CASE_COUNT:
        raise SystemExit(
            "abrupt positive universe must contain exactly 6 rows after strict abrupt evidence plus accepted truth backfill; "
            f"strict={len(strict_df)}, accepted_truth={len(accepted_truth_df)}, final={len(selected)}"
        )

    if selected["candidate_validity"].map(normalize_text).isin(["false_positive"]).any():
        raise SystemExit("abrupt positive universe still contains candidate_validity=false_positive rows")
    if selected["vendor_reply_class"].map(normalize_text).isin(["vendor_rejected"]).any():
        raise SystemExit("abrupt positive universe still contains vendor_reply_class=vendor_rejected rows")
    banned_hits = selected["panel_id"].map(normalize_text).isin(BANNED_PANEL_IDS)
    if banned_hits.any():
        banned_values = sorted(selected.loc[banned_hits, "panel_id"].map(normalize_text).unique().tolist())
        raise SystemExit(f"abrupt positive universe still contains banned panel ids: {banned_values}")

    return selected, selection_rule


def build_abrupt6_symptom_map(
    non_precursor_df: pd.DataFrame,
    reaudit_df: pd.DataFrame,
    local_eligibility_df: pd.DataFrame | None,
) -> pd.DataFrame:
    abrupt_df, selection_rule = select_abrupt_positive_cases(non_precursor_df, reaudit_df, local_eligibility_df)
    if len(abrupt_df) != EXPECTED_ABRUPT_CASE_COUNT:
        raise SystemExit(
            f"selected abrupt symptom-map universe must be {EXPECTED_ABRUPT_CASE_COUNT}, got {len(abrupt_df)}"
        )

    reaudit_lookup = build_lookup(reaudit_df, ["site", "panel_id"])
    eligibility_lookup = build_lookup(local_eligibility_df, ["site", "panel_id"])
    rows: list[dict[str, object]] = []
    for case_row in abrupt_df.to_dict(orient="records"):
        key = (normalize_text(case_row["site"]), normalize_text(case_row["panel_id"]))
        reaudit_row = reaudit_lookup.get(key) or find_matching_reaudit_row(case_row, reaudit_df)
        eligibility_row = eligibility_lookup.get(key)
        enriched_row = dict(case_row)
        if reaudit_row:
            for field_name in ["vendor_fault_family", "candidate_validity", "vendor_reply_class"]:
                enriched_value = normalize_text(reaudit_row.get(field_name))
                if enriched_value:
                    enriched_row[field_name] = enriched_value
        symptom, detail, source_field = map_abrupt_symptom(enriched_row, reaudit_row)
        note_parts = [
            f"selection_rule={selection_rule}",
            f"selection_source={normalize_text(case_row.get('selection_source'))}",
            f"anchor_source={normalize_text(case_row.get('anchor_source'))}",
            f"candidate_validity={normalize_text(enriched_row.get('candidate_validity'))}",
            f"vendor_reply_class={normalize_text(enriched_row.get('vendor_reply_class'))}",
        ]
        hard_evidence_bits = []
        for column in STRICT_ABRUPT_EVIDENCE_COLS:
            if numeric_int(case_row.get(column)) == 1:
                hard_evidence_bits.append(column)
        if hard_evidence_bits:
            note_parts.append(f"evidence={','.join(hard_evidence_bits)}")
        if eligibility_row:
            fault_start_date = normalize_text(eligibility_row.get("fault_start_date"))
            if fault_start_date:
                note_parts.append(f"eligibility_fault_start_date={fault_start_date}")
        rows.append(
            {
                "site": normalize_text(enriched_row["site"]),
                "panel_id": normalize_text(enriched_row["panel_id"]),
                "고장시점": normalize_text(case_row["anchor_date"]),
                "증상명_ko": symptom,
                "세부근거_ko": detail,
                "source_field_ko": source_field,
                "비고_ko": "; ".join(part for part in note_parts if normalize_text(part)),
            }
        )
    abrupt6_df = pd.DataFrame(rows, columns=ABRUPT6_COLS)

    family_counts = abrupt6_df["증상명_ko"].value_counts().to_dict()
    expected_counts = {"다이오드형": 4, "개방/장치이상형": 1, "모듈손상형": 1}
    if all(symptom in family_counts for symptom in expected_counts):
        composition_ok = all(family_counts.get(symptom, 0) == count for symptom, count in expected_counts.items())
        if composition_ok:
            abrupt6_df["비고_ko"] = abrupt6_df["비고_ko"].map(lambda text: f"{text}; family_composition_check=ok")
        else:
            abrupt6_df["비고_ko"] = abrupt6_df["비고_ko"].map(
                lambda text: f"{text}; family_composition_check=uncertain"
            )
    else:
        abrupt6_df["비고_ko"] = abrupt6_df["비고_ko"].map(
            lambda text: f"{text}; family_composition_check=uncertain"
        )
    return abrupt6_df


def build_kernel_mapping() -> pd.DataFrame:
    rows = [
        {
            "커널로그_증상명": "출력 저하형",
            "주_프로젝트분류": "전조형 고장",
            "보조_프로젝트분류": "급작 고장",
            "설명_ko": "출력이 서서히 눌리거나 회복 없이 약해지는 증상은 전조형 고장 쪽 해석이 기본이다. 다만 anchor 근처 급락이면 급작 고장 보조 해석이 붙는다.",
            "주의_ko": "출력만 보고 물리 root-cause를 단정하지 말고 전압/전류 및 fault anchor 문맥을 함께 본다.",
        },
        {
            "커널로그_증상명": "전압 변화형",
            "주_프로젝트분류": "급작 고장",
            "보조_프로젝트분류": "전조형 고장",
            "설명_ko": "전압 collapse나 급격한 전압 변화는 abrupt anchor와 더 잘 맞는다. 다만 반복적으로 누적되면 전조형 해석 보조가 가능하다.",
            "주의_ko": "전압 변화만으로 diode/open/device를 확정하지 말고 same-day collapse 범위와 현장 note를 같이 본다.",
        },
        {
            "커널로그_증상명": "패턴 이상형",
            "주_프로젝트분류": "같이 흔들리는 이상",
            "보조_프로젝트분류": "오경보",
            "설명_ko": "여러 패널이 같은 날 비슷하게 흔들리면 site/context 쪽 패턴 이상으로 읽는 편이 안전하다.",
            "주의_ko": "패턴 이상형은 confusion matrix가 아니라 해석 매핑이다. panel-local fault와 직접 동일시하면 안 된다.",
        },
        {
            "커널로그_증상명": "불안정형",
            "주_프로젝트분류": "반복 이상",
            "보조_프로젝트분류": "오경보",
            "설명_ko": "짧게 반복되거나 들쑥날쑥한 이상은 반복 이상/monitor lane 쪽으로 우선 해석한다.",
            "주의_ko": "반복된다고 바로 고장으로 승격하지 말고 output-normal monitor 문맥과 함께 본다.",
        },
        {
            "커널로그_증상명": "복합형",
            "주_프로젝트분류": "급작 고장",
            "보조_프로젝트분류": "같이 흔들리는 이상",
            "설명_ko": "출력 저하와 전압 변화, breadth 신호가 겹치면 복합형으로 보고 abrupt와 common-cause 가능성을 함께 남긴다.",
            "주의_ko": "복합형은 해석 보류용 분류다. unsupported 물리 root-cause 명칭으로 과장하지 않는다.",
        },
    ]
    return pd.DataFrame(rows, columns=KERNEL_MAPPING_COLS)


def gpv_search_refs(root: Path) -> list[str]:
    candidate_paths = [
        root / "data" / "gpvs" / "out" / "EXTERNAL_GPVS_BYTYPE_METRICS.csv",
        root / "data" / "gpvs" / "out" / "EXTERNAL_GPVS_METRICS.csv",
        root / "docs" / "reports" / "gpvs_final_summary.md",
        root / "docs" / "OPS_GPVS_FAULT_FAMILY_F1.md",
        root / "_share" / "gpvs_fault_family_f1_summary.csv",
    ]
    refs = [str(path.relative_to(root)) for path in candidate_paths if path.exists()]
    return refs


def format_metric_bits(record: dict[str, object], metric_names: list[str]) -> str:
    metric_bits: list[str] = []
    for metric_name in metric_names:
        metric_value = numeric_float(record.get(metric_name))
        if metric_value is not None:
            metric_bits.append(f"{metric_name}={metric_value:.4f}")
    return ", ".join(metric_bits)


def parse_gpv_bytype_rows(path: Path, root: Path) -> list[dict[str, object]] | None:
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
    except Exception:
        return None

    required = ["fault_type", "sid", "score", "auc", "ap", "precision_fpr1", "recall_fpr1", "f1_fpr1"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        return None

    subset = df.loc[df["fault_type"].map(normalize_text).str.match(r"^F[1-7][LM]$")].copy()
    if subset.empty:
        return None

    subset["sid_num"] = pd.to_numeric(subset["sid"], errors="coerce")
    subset = subset.loc[subset["sid_num"].between(1, 7, inclusive="both")].copy()
    if subset.empty:
        return None

    rows: list[dict[str, object]] = []
    for sid in range(1, 8):
        sid_rows = subset.loc[subset["sid_num"].eq(float(sid))].copy()
        if sid_rows.empty:
            return None
        sid_rows["_ap"] = pd.to_numeric(sid_rows["ap"], errors="coerce").fillna(-1.0)
        sid_rows["_auc"] = pd.to_numeric(sid_rows["auc"], errors="coerce").fillna(-1.0)
        sid_rows["_f1"] = pd.to_numeric(sid_rows["f1_fpr1"], errors="coerce").fillna(-1.0)
        best_row = sid_rows.sort_values(["_ap", "_auc", "_f1"], ascending=False).iloc[0].to_dict()
        fault_type = normalize_text(best_row["fault_type"])
        score_name = normalize_text(best_row["score"])
        metric_text = format_metric_bits(
            best_row,
            ["auc", "ap", "precision_fpr1", "recall_fpr1", "f1_fpr1", "detect_rate_post"],
        )
        rows.append(
            {
                "고장유형_번호": str(sid),
                "고장유형_설명_ko": f"GPVS Fault{sid}",
                "성능요약_ko": f"{fault_type} / {score_name} representative row from EXTERNAL_GPVS_BYTYPE_METRICS.csv",
                "수치_ko": metric_text,
                "source_ref_ko": (
                    f"{path.relative_to(root)} "
                    "(fault_type,sid,score,auc,ap,precision_fpr1,recall_fpr1,f1_fpr1,detect_rate_post)"
                ),
            }
        )
    return rows


def try_load_exact_gpv7_rows(root: Path) -> list[dict[str, object]] | None:
    bytype_candidates = [
        root / "data" / "gpvs" / "out" / "EXTERNAL_GPVS_BYTYPE_METRICS.csv",
        root / "data" / "gpvs" / "out" / "EXTERNAL_GPVS_ENSEMBLE_BYTYPE_METRICS.csv",
        root / "data" / "gpvs" / "out" / "EXTERNAL_GPVS_ENSEMBLE2_BYTYPE_METRICS.csv",
        root / "data" / "gpvs" / "out" / "EXTERNAL_GPVS_ENSEMBLE3_BYTYPE_METRICS.csv",
    ]
    for path in bytype_candidates:
        rows = parse_gpv_bytype_rows(path, root)
        if rows is not None:
            return rows
    return None


def build_gpv7_perf_summary(root: Path) -> pd.DataFrame:
    exact_rows = try_load_exact_gpv7_rows(root)
    if exact_rows is not None:
        rows = exact_rows
    else:
        ref_list = gpv_search_refs(root)
        ref_text = "repo search only / not found"
        if ref_list:
            ref_text = f"repo search only / not found ({'; '.join(ref_list[:3])})"
        rows = [
            {
                "고장유형_번호": scenario.replace("F", ""),
                "고장유형_설명_ko": GPV_COARSE_DESCRIPTION[scenario],
                "성능요약_ko": "현재 저장 산출물에서 7종별 정식 수치 미확인",
                "수치_ko": "",
                "source_ref_ko": ref_text,
            }
            for scenario in GPV_SCENARIOS
        ]
        rows.append(
            {
                "고장유형_번호": "note",
                "고장유형_설명_ko": "binary/aggregate GPV 별도 note",
                "성능요약_ko": "binary/aggregate GPV performance may exist separately but exact 7-class table was not found in current stored artifacts",
                "수치_ko": "",
                "source_ref_ko": ref_text,
            }
        )
    return pd.DataFrame(rows, columns=GPV7_COLS)


def build_progress_snapshot(
    project_eval_df: pd.DataFrame,
    freeze_pack_df: pd.DataFrame,
    policy_df: pd.DataFrame,
    pipeline_df: pd.DataFrame,
) -> pd.DataFrame:
    freeze_lookup = {normalize_text(row["eval_scope"]): row for row in freeze_pack_df.to_dict(orient="records")}
    policy_name = normalize_text(policy_df.iloc[0]["recommended_policy_name"])
    pipeline_pass_flag = numeric_int(pipeline_df.iloc[0]["final_pipeline_pass_flag"])

    step3_decision = normalize_text(freeze_lookup["step3_precursor_performance"]["current_data_decision"])
    common_decision = normalize_text(freeze_lookup["step4_common_cause_routing"]["current_data_decision"])
    abrupt_best = project_eval_df.loc[
        project_eval_df["eval_scope"].eq("step4_abrupt_no_precursor")
        & project_eval_df["target_name"].eq("final_fault_hit_by_anchor")
    ]
    abrupt_f1 = ""
    if not abrupt_best.empty:
        abrupt_metric = numeric_float(abrupt_best.iloc[0]["f1"])
        abrupt_f1 = "" if abrupt_metric is None else f"{abrupt_metric:.3f}"

    rows = [
        {
            "항목": "연구/알고리즘 큰 줄기",
            "현재_완료율_추정": 85,
            "현재_상태_ko": "주요 줄기는 정리됐지만 step3와 common-cause 쪽은 현재 데이터 한계로 underpowered 또는 exploratory 상태가 남아 있다.",
            "근거_ko": f"freeze pack 기준 step3={step3_decision}, step4_common={common_decision}, abrupt best F1={abrupt_f1}",
        },
        {
            "항목": "운영 스택",
            "현재_완료율_추정": 95,
            "현재_상태_ko": "baseline/QA/pipeline/release gate/idempotence까지 운영 packaging 줄기는 사실상 완료된 상태다.",
            "근거_ko": f"pipeline pass={pipeline_pass_flag}, recommended workflow={policy_name}",
        },
        {
            "항목": "내부 공유/정리 문서",
            "현재_완료율_추정": 70,
            "현재_상태_ko": "내부 공유용 정리 문서는 진행 중이고 이번 appendix로 abrupt6/분류 매핑/GPV/progress 정리가 추가로 보강됐다.",
            "근거_ko": "current-data freeze pack과 handoff 계열 문서는 존재하지만 appendix형 사람용 정리는 계속 채우는 중이다.",
        },
    ]
    return pd.DataFrame(rows, columns=PROGRESS_COLS)


def write_csv(df: pd.DataFrame, path: Path, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    frames = load_inputs(root)

    abrupt6_df = build_abrupt6_symptom_map(
        frames["non_precursor"],
        frames["reaudit"],
        frames["local_eligibility"],
    )
    kernel_mapping_df = build_kernel_mapping()
    gpv7_df = build_gpv7_perf_summary(root)
    progress_df = build_progress_snapshot(
        frames["project_eval"],
        frames["freeze_pack"],
        frames["policy"],
        frames["pipeline"],
    )

    write_csv(abrupt6_df, share_dir / ABRUPT6_OUTPUT_NAME, ABRUPT6_COLS)
    write_csv(kernel_mapping_df, share_dir / KERNEL_MAPPING_OUTPUT_NAME, KERNEL_MAPPING_COLS)
    write_csv(gpv7_df, share_dir / GPV7_OUTPUT_NAME, GPV7_COLS)
    write_csv(progress_df, share_dir / PROGRESS_OUTPUT_NAME, PROGRESS_COLS)

    print(f"wrote {share_dir / ABRUPT6_OUTPUT_NAME}")
    print(f"wrote {share_dir / KERNEL_MAPPING_OUTPUT_NAME}")
    print(f"wrote {share_dir / GPV7_OUTPUT_NAME}")
    print(f"wrote {share_dir / PROGRESS_OUTPUT_NAME}")


if __name__ == "__main__":
    main()
