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
COMMON_CAUSE_RETROFIT_NAME = "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv"
GPVS_ATTACH_INVENTORY_NAME = "panel_day_engine_gpvs_panel_attach_inventory_v1.csv"
GPVS_ATTACH_FEASIBILITY_NAME = "panel_day_engine_gpvs_panel_attach_feasibility_v1.csv"
GPVS_ATTACH_CANDIDATES_NAME = "panel_day_engine_gpvs_panel_attach_candidates_v1.csv"
PRECURSOR_ABRUPT_CONSISTENCY_CASES_NAME = "panel_day_engine_precursor_abrupt_consistency_cases_v1.csv"
PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME = "panel_day_engine_precursor_abrupt_consistency_summary_v1.csv"
PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME = "panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv"
FORENSIC_SUMMARY_NAME = "panel_day_engine_c42997_1_1_forensic_summary_v1.csv"

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
    "전조형이력_flag",
    "급작고장이력_flag",
    "공통원인이력_flag",
    "반복이상이력_flag",
    "패널고장여부_ko",
    "GPVS_적용대상_ko",
    "커널로그_증상명_ko",
    "커널로그_원인군_ko",
    "GPVS_부착상태_ko",
    "GPVS_참고유형_ko",
    "GPVS_근거_ko",
    "GPVS_미부착사유_ko",
    "GPVS_후보파일_ko",
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
    "전조사건수",
    "순수급작사건수",
    "전조후급격종료_패널수",
    "고장유형보류_패널수",
    "순수전조_패널수",
    "전조흔적_패널수",
    "순수급작_패널수",
    "전조평가셋편입_패널수",
    "급작평가셋편입_패널수",
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
    "사건보조행수",
    "클러스터_보조행수",
    "note_ko",
]

PANEL_LEVEL_PREVIEW_CLASSES = {"queue_run", "watch_now_panel"}
CLUSTER_PREVIEW_CLASS = "secondary_value_cluster"
GPVS_ABSENCE_REASON = "현재 저장 산출물에는 패널별 GPVS 직접 판정이 없음"
GPVS_NON_TARGET_REASON = "고장 패널이 아니어서 GPVS 적용 대상 아님"

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
    "전조흔적_시작일",
    "강한트리거일",
    "사건시간양상_판정_ko",
    "현재표_보정필요여부_flag",
]

FORENSIC_HOLDOUT_SITE = "conalog"
FORENSIC_HOLDOUT_PANEL_ID = "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"
FORENSIC_HOLDOUT_WARNING_DATE = "2025-01-20"
FORENSIC_HOLDOUT_TRIGGER_DATE = "2025-03-21"
FORENSIC_HOLDOUT_REASON = "전조흔적 시작일 2025-01-20, 강한트리거일 2025-03-21 이라 순수 급작 보류"

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


def load_inputs(root: Path) -> dict[str, pd.DataFrame]:
    share_dir = root / "_share"
    frames = {
        "workflow": read_csv(share_dir / WORKFLOW_DEFAULT_NAME),
        "abrupt6": read_csv(share_dir / ABRUPT6_SYMPTOM_MAP_NAME),
        "kernel_map": read_csv(share_dir / KERNELLOG_PROJECT_MAPPING_NAME),
        "gpv7": read_csv(share_dir / GPV7_PERF_SUMMARY_NAME),
        "final_pack": read_csv(share_dir / FINAL_DECISION_PACK_NAME),
        "precursor_truth": read_csv(share_dir / PRECURSOR_ONSET_TRUTH_NAME),
        "common_cause": read_csv(share_dir / COMMON_CAUSE_RETROFIT_NAME),
        "gpvs_attach_inventory": read_csv(share_dir / GPVS_ATTACH_INVENTORY_NAME),
        "gpvs_attach_feasibility": read_csv(share_dir / GPVS_ATTACH_FEASIBILITY_NAME),
        "gpvs_attach_candidates": read_csv(share_dir / GPVS_ATTACH_CANDIDATES_NAME),
        "consistency_cases": read_csv(share_dir / PRECURSOR_ABRUPT_CONSISTENCY_CASES_NAME),
        "consistency_summary": read_csv(share_dir / PRECURSOR_ABRUPT_CONSISTENCY_SUMMARY_NAME),
        "consistency_recommendation": read_csv(share_dir / PRECURSOR_ABRUPT_CONSISTENCY_RECOMMENDATION_NAME),
        "forensic_summary": read_csv(share_dir / FORENSIC_SUMMARY_NAME),
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
        ["site", "preferred_precursor_onset_date"],
        PRECURSOR_ONSET_TRUTH_NAME,
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


def load_forensic_holdout_case(frames: dict[str, pd.DataFrame]) -> dict[str, str]:
    forensic_df = frames["forensic_summary"].copy()
    target_df = forensic_df.loc[
        forensic_df["site"].eq(FORENSIC_HOLDOUT_SITE)
        & forensic_df["panel_id"].eq(FORENSIC_HOLDOUT_PANEL_ID)
    ].copy()
    if len(target_df) != 1:
        raise SystemExit(
            f"{FORENSIC_SUMMARY_NAME} must contain exactly one target row for {FORENSIC_HOLDOUT_SITE}/{FORENSIC_HOLDOUT_PANEL_ID}, found {len(target_df)}"
        )
    row = {key: normalize_text(value) for key, value in target_df.iloc[0].to_dict().items()}
    if row["사건시간양상_판정_ko"] != "전조흔적있음_순수급작보류":
        raise SystemExit(
            f"{FORENSIC_SUMMARY_NAME} guard failed: 사건시간양상_판정_ko must be 전조흔적있음_순수급작보류, got {row['사건시간양상_판정_ko'] or '<blank>'}"
        )
    if to_numeric_flag(pd.Series([row["현재표_보정필요여부_flag"]])).iloc[0] != 1:
        raise SystemExit(
            f"{FORENSIC_SUMMARY_NAME} guard failed: 현재표_보정필요여부_flag must be 1, got {row['현재표_보정필요여부_flag'] or '<blank>'}"
        )
    if row["전조흔적_시작일"] != FORENSIC_HOLDOUT_WARNING_DATE or row["강한트리거일"] != FORENSIC_HOLDOUT_TRIGGER_DATE:
        raise SystemExit(
            f"{FORENSIC_SUMMARY_NAME} guard failed: expected warning/trigger {FORENSIC_HOLDOUT_WARNING_DATE}/{FORENSIC_HOLDOUT_TRIGGER_DATE}, got {row['전조흔적_시작일']}/{row['강한트리거일']}"
        )
    return row


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
    if event_type == "고장유형 보류":
        return "single-panel forensic audit 기준 고장 패널이지만 event type은 holdout으로 둔다. terminal failure pattern만 급작 발생으로 남기고 pure abrupt count에는 넣지 않는다."
    if event_type == "전조형 고장" and terminal_pattern == "급격 종료":
        return "이 panel은 precursor-abrupt consistency audit 기준 전조형 고장 한 건이 급격 종료로 끝난 것으로 읽는다. event type과 terminal failure pattern은 분리해서 해석해야 한다."
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
    is_forensic_holdout: bool,
) -> tuple[str, str]:
    if is_forensic_holdout:
        return ("고장유형 보류", "급작 발생")
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
    is_forensic_holdout: bool,
) -> str:
    if is_forensic_holdout:
        return "고장유형 보류(급작 발생)"
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
    is_same_event_overlap: bool,
    is_forensic_holdout: bool,
) -> dict[str, object]:
    if is_same_event_overlap:
        return {
            "사건유형_해석_ko": "전조형 고장",
            "전조흔적_flag": 1,
            "순수급작_flag": 0,
            "전조평가셋편입_flag": 1,
            "급작평가셋편입_flag": 0,
            "해석대평가차이_ko": "",
        }
    if is_forensic_holdout:
        return {
            "사건유형_해석_ko": "전조흔적 있음",
            "전조흔적_flag": 1,
            "순수급작_flag": 0,
            "전조평가셋편입_flag": 0,
            "급작평가셋편입_flag": 0,
            "해석대평가차이_ko": "전조흔적은 있으나 현재 전조평가셋/순수급작평가셋 모두 미편입",
        }
    if flags["has_급작고장"]:
        return {
            "사건유형_해석_ko": "급작 고장",
            "전조흔적_flag": 0,
            "순수급작_flag": 1,
            "전조평가셋편입_flag": 0,
            "급작평가셋편입_flag": 1,
            "해석대평가차이_ko": "",
        }
    if flags["has_전조형고장"]:
        return {
            "사건유형_해석_ko": "전조형 고장",
            "전조흔적_flag": 1,
            "순수급작_flag": 0,
            "전조평가셋편입_flag": 1,
            "급작평가셋편입_flag": 0,
            "해석대평가차이_ko": "",
        }
    return {
        "사건유형_해석_ko": event_type,
        "전조흔적_flag": 0,
        "순수급작_flag": 0,
        "전조평가셋편입_flag": 0,
        "급작평가셋편입_flag": 0,
        "해석대평가차이_ko": "",
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


def build_outputs(
    root: Path,
    frames: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, int], str]:
    workflow_panel_df = build_workflow_panel_df(frames["workflow"])
    cluster_df = build_cluster_df(frames["workflow"])
    workflow_by_key = workflow_lookup(workflow_panel_df)
    abrupt_by_key = abrupt_lookup(frames["abrupt6"])
    final_pack_by_scope = final_pack_lookup(frames["final_pack"])
    same_event_overlap_keys = load_same_event_overlap_keys(frames)
    forensic_holdout_case = load_forensic_holdout_case(frames)
    forensic_holdout_key = (FORENSIC_HOLDOUT_SITE, FORENSIC_HOLDOUT_PANEL_ID)

    workflow_keys = set(workflow_by_key.keys())
    abrupt_keys = set(abrupt_by_key.keys())
    pure_abrupt_keys = abrupt_keys - same_event_overlap_keys - {forensic_holdout_key}
    precursor_keys = build_precursor_positive_keys(frames["precursor_truth"])
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
    if forensic_holdout_key not in abrupt_keys:
        raise SystemExit("forensic holdout panel must remain in abrupt symptom map universe")
    if forensic_holdout_key in precursor_keys:
        raise SystemExit("forensic holdout panel must not be auto-promoted into precursor-positive universe")

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
        is_same_event_overlap = key in same_event_overlap_keys
        is_forensic_holdout = key == forensic_holdout_key
        flags = {
            "has_전조형고장": int(key in precursor_keys),
            "has_급작고장": int(key in pure_abrupt_keys),
            "has_공통원인이벤트": int(key in common_keys),
            "has_반복이상": int(key in workflow_watch_keys),
        }

        event_type, terminal_pattern = event_type_and_terminal_pattern(
            flags,
            is_same_event_overlap=is_same_event_overlap,
            is_forensic_holdout=is_forensic_holdout,
        )
        representative_verdict = event_type
        history = event_history_text(
            flags,
            is_same_event_overlap=is_same_event_overlap,
            is_forensic_holdout=is_forensic_holdout,
        )
        interpretation = interpretation_layer_fields(
            flags,
            event_type,
            is_same_event_overlap=is_same_event_overlap,
            is_forensic_holdout=is_forensic_holdout,
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

        universe_parts: list[str] = []
        if flags["has_전조형고장"]:
            universe_parts.append("precursor onset truth positive universe 포함")
        if flags["has_급작고장"]:
            universe_parts.append("abrupt6 positive universe 포함")
        if flags["has_공통원인이벤트"]:
            universe_parts.append("common-cause descriptive positive universe 포함")
        if flags["has_반복이상"]:
            universe_parts.append("workflow watch_now_panel 포함")
        if is_forensic_holdout:
            universe_parts.append("single-panel forensic holdout 적용")
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
        if is_forensic_holdout:
            caution_parts.append(FORENSIC_HOLDOUT_REASON)
            caution_parts.append(
                f"현재 재감사 family hint={forensic_holdout_case['현재_재감사라벨_ko']}"
            )
        if normalize_text(interpretation["해석대평가차이_ko"]):
            caution_parts.append(normalize_text(interpretation["해석대평가차이_ko"]))

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
                "전조형이력_flag": flags["has_전조형고장"],
                "급작고장이력_flag": flags["has_급작고장"],
                "공통원인이력_flag": flags["has_공통원인이벤트"],
                "반복이상이력_flag": flags["has_반복이상"],
                "패널고장여부_ko": panel_fault_status,
                "GPVS_적용대상_ko": gpvs_applicability,
                "커널로그_증상명_ko": kernel_symptom,
                "커널로그_원인군_ko": kernel_cause_group,
                "GPVS_부착상태_ko": gpvs_attach_status,
                "GPVS_참고유형_ko": gpvs_type,
                "GPVS_근거_ko": gpvs_reason,
                "GPVS_미부착사유_ko": gpvs_unattached_note,
                "GPVS_후보파일_ko": gpvs_candidate_file,
                "운영위치_ko": map_operating_location(workflow_row),
                "판정주의_ko": " ".join(part for part in caution_parts if part),
            }
        )

        event_members: list[tuple[str, str]] = []
        if is_forensic_holdout:
            event_members.append(("고장유형 보류", "single-panel forensic audit 기준 pure abrupt typing holdout"))
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

        for event_name, event_note in event_members:
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

    verdict_df = pd.DataFrame(panel_rows).reindex(columns=VERDICT_COLS)
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
        "forensic_holdout_expected": 1,
        "precursor_expected": len(precursor_keys),
        "common_expected": len(common_keys),
        "gpvs_expected_attach_count": gpvs_expected_attach_count_applicable,
    }
    return verdict_df, event_supplement_df, cluster_supplement_df, metrics, gpvs_feasibility_meta


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
    pure_precursor_mask = verdict_df["사건유형_ko"].eq("전조형 고장") & verdict_df["최종고장양상_ko"].eq("진행성 악화")
    pure_abrupt_mask = verdict_df["사건유형_ko"].eq("급작 고장")
    holdout_fault_mask = verdict_df["사건유형_ko"].eq("고장유형 보류")

    return {
        "전체_패널수": int(len(verdict_df)),
        "고유_고장패널수": int(verdict_df["패널고장여부_ko"].eq("고장").sum()),
        "전조사건수": int(precursor_flags.sum()),
        "순수급작사건수": int(pure_abrupt_mask.sum()),
        "전조후급격종료_패널수": int(abrupt_ending_mask.sum()),
        "고장유형보류_패널수": int(holdout_fault_mask.sum()),
        "순수전조_패널수": int(pure_precursor_mask.sum()),
        "전조흔적_패널수": int(precursor_trace_flags.sum()),
        "순수급작_패널수": int(pure_abrupt_flags.sum()),
        "전조평가셋편입_패널수": int(precursor_eval_flags.sum()),
        "급작평가셋편입_패널수": int(abrupt_eval_flags.sum()),
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
    pure_abrupt_membership = counts["순수급작사건수"]
    precursor_membership = counts["전조사건수"]
    common_membership = counts["공통원인이력_패널수"]
    gpvs_attached = int(verdict_df["GPVS_부착상태_ko"].eq("부착").sum())

    if counts["고유_고장패널수"] != 6:
        raise SystemExit(f"고유_고장패널수 must be 6, found {counts['고유_고장패널수']}")
    if precursor_membership != 2:
        raise SystemExit(f"전조사건수 must be 2, found {precursor_membership}")
    if pure_abrupt_membership != 3:
        raise SystemExit(f"순수급작사건수 must be 3, found {pure_abrupt_membership}")
    if counts["전조후급격종료_패널수"] != 2:
        raise SystemExit(f"전조후급격종료_패널수 must be 2, found {counts['전조후급격종료_패널수']}")
    if counts["고장유형보류_패널수"] != 1:
        raise SystemExit(f"고장유형보류_패널수 must be 1, found {counts['고장유형보류_패널수']}")
    if counts["순수전조_패널수"] != 0:
        raise SystemExit(f"순수전조_패널수 must be 0, found {counts['순수전조_패널수']}")
    if common_membership != 4:
        raise SystemExit(f"panels with 공통원인이력_flag must be 4, found {common_membership}")
    if gpvs_attached != int(metrics["gpvs_expected_attach_count"]):
        raise SystemExit(
            f"GPVS attached row count must equal applicable direct-match count {metrics['gpvs_expected_attach_count']}, found {gpvs_attached}"
        )
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

    holdout_df = verdict_df.loc[
        verdict_df["site"].eq(FORENSIC_HOLDOUT_SITE) & verdict_df["panel_id"].eq(FORENSIC_HOLDOUT_PANEL_ID)
    ].copy()
    if len(holdout_df) != 1:
        raise SystemExit("forensic holdout panel must appear exactly once in main panel verdict table")
    holdout_row = holdout_df.iloc[0]
    if normalize_text(holdout_row["사건유형_ko"]) != "고장유형 보류":
        raise SystemExit("forensic holdout panel must be marked 사건유형_ko=고장유형 보류")
    if normalize_text(holdout_row["사건유형_해석_ko"]) != "전조흔적 있음":
        raise SystemExit("forensic holdout panel must be marked 사건유형_해석_ko=전조흔적 있음")
    if normalize_text(holdout_row["패널고장여부_ko"]) != "고장":
        raise SystemExit("forensic holdout panel must stay 패널고장여부_ko=고장")
    if normalize_text(holdout_row["최종고장양상_ko"]) != "급작 발생":
        raise SystemExit("forensic holdout panel must keep 최종고장양상_ko=급작 발생")
    if normalize_text(holdout_row["GPVS_적용대상_ko"]) != "적용대상":
        raise SystemExit("forensic holdout panel must remain GPVS applicable")
    if int(pd.to_numeric(holdout_row["전조흔적_flag"], errors="coerce")) != 1:
        raise SystemExit("forensic holdout panel must keep 전조흔적_flag=1")
    if int(pd.to_numeric(holdout_row["순수급작_flag"], errors="coerce")) != 0:
        raise SystemExit("forensic holdout panel must keep 순수급작_flag=0")
    if int(pd.to_numeric(holdout_row["전조평가셋편입_flag"], errors="coerce")) != 0:
        raise SystemExit("forensic holdout panel must keep 전조평가셋편입_flag=0")
    if int(pd.to_numeric(holdout_row["급작평가셋편입_flag"], errors="coerce")) != 0:
        raise SystemExit("forensic holdout panel must keep 급작평가셋편입_flag=0")
    if normalize_text(holdout_row["해석대평가차이_ko"]) != "전조흔적은 있으나 현재 전조평가셋/순수급작평가셋 모두 미편입":
        raise SystemExit("forensic holdout panel must expose interpretation/evaluation mismatch text")
    if FORENSIC_HOLDOUT_WARNING_DATE not in normalize_text(holdout_row["판정주의_ko"]) or FORENSIC_HOLDOUT_TRIGGER_DATE not in normalize_text(holdout_row["판정주의_ko"]):
        raise SystemExit("forensic holdout panel note must mention warning/trigger dates")

    overlap_rows = verdict_df.loc[
        verdict_df["사건유형_ko"].eq("전조형 고장") & verdict_df["최종고장양상_ko"].eq("급격 종료")
    ].copy()
    if len(overlap_rows) != metrics["same_event_overlap_expected"]:
        raise SystemExit(
            f"same-event overlap rows must stay {metrics['same_event_overlap_expected']}, found {len(overlap_rows)}"
        )
    if overlap_rows["사건유형_해석_ko"].map(normalize_text).ne("전조형 고장").any():
        raise SystemExit("same-event overlap rows must keep 사건유형_해석_ko=전조형 고장")
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

    if event_supplement_df.empty and (abrupt_membership + precursor_membership + common_membership) > 0:
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
    gpvs_reason_counts = (
        verdict_df.loc[verdict_df["GPVS_부착상태_ko"].eq("미부착"), "GPVS_미부착사유_ko"].value_counts().to_dict()
    )
    best_source = normalize_text(gpvs_feasibility_meta.get("best_source", ""))
    feasibility_reason = normalize_text(gpvs_feasibility_meta.get("feasibility_reason", ""))
    gpvs_note = "GPVS는 reference axis로만 붙이고, matched panel에만 부분 부착했다."
    if best_source:
        gpvs_note += f" 최선 후보 파일은 {best_source} 다."
    if feasibility_reason:
        gpvs_note += f" {feasibility_reason}"
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
        "사건보조행수": int(len(event_supplement_df)),
        "클러스터_보조행수": int(len(cluster_supplement_df)),
        "note_ko": (
            f"main panel table은 unique panel 대표 verdict 표이고 workflow panel {metrics['workflow_panel_count']}건을 기준으로 fault6 rows {metrics['abrupt_fault6_total']}건, pure abrupt {metrics['pure_abrupt_expected']}건, precursor {metrics['precursor_expected']}건, common-cause {metrics['common_expected']}건 membership을 함께 접었다. "
            f"same-event overlap {metrics['same_event_overlap_expected']}건은 전조형 고장(급격 종료)으로 재해석했고 pure abrupt event로는 세지지 않는다. "
            f"single-panel forensic holdout {metrics['forensic_holdout_expected']}건은 고장 패널이지만 pure abrupt typing을 보류해 사건유형=`고장유형 보류` 로 남겼다. "
            "이제 사건유형_해석_ko 와 전조/급작 평가셋 편입 flag를 분리해, 해석층과 evaluation-set inclusion을 같은 뜻으로 읽지 않게 한다. "
            "event type과 terminal failure pattern은 분리해서 읽는다. "
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
    verdict_df, event_supplement_df, cluster_supplement_df, metrics, gpvs_feasibility_meta = build_outputs(root, frames)
    validate_real_coverage(verdict_df, event_supplement_df, cluster_supplement_df, metrics)
    summary_df = build_summary(verdict_df, event_supplement_df, cluster_supplement_df, metrics, gpvs_feasibility_meta)
    write_outputs(root, verdict_df, event_supplement_df, cluster_supplement_df, summary_df)


if __name__ == "__main__":
    main()
