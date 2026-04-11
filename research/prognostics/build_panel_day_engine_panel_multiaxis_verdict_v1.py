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
GPVS_ATTACH_FEASIBILITY_NAME = "panel_day_engine_gpvs_panel_attach_feasibility_v1.csv"
GPVS_ATTACH_CANDIDATES_NAME = "panel_day_engine_gpvs_panel_attach_candidates_v1.csv"

VERDICT_OUTPUT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
EVENT_SUPPLEMENT_OUTPUT_NAME = "panel_day_engine_panel_multiaxis_event_supplement_v1.csv"
CLUSTER_SUPPLEMENT_OUTPUT_NAME = "panel_day_engine_panel_multiaxis_cluster_supplement_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_panel_multiaxis_verdict_summary_v1.csv"

VERDICT_COLS = [
    "site",
    "panel_id",
    "대표판정_ko",
    "사건이력_ko",
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
    "급작이력_패널수",
    "전조형이력_패널수",
    "공통원인이력_패널수",
    "반복이상이력_패널수",
    "대표판정_급작수",
    "대표판정_전조형수",
    "대표판정_공통원인수",
    "대표판정_반복이상수",
    "대표판정_불충분수",
    "고장_패널수",
    "비고장_패널수",
    "미확정_패널수",
    "커널로그_증상명_부착수",
    "커널로그_원인군_부착수",
    "GPVS_참고유형_부착수",
    "GPVS_미부착수",
    "사건보조행수",
    "클러스터_보조행수",
    "note_ko",
]

PANEL_LEVEL_PREVIEW_CLASSES = {"queue_run", "watch_now_panel"}
CLUSTER_PREVIEW_CLASS = "secondary_value_cluster"
GPVS_ABSENCE_REASON = "현재 저장 산출물에는 패널별 GPVS 직접 판정이 없음"

EVENT_HISTORY_ORDER = [
    "전조형 고장",
    "급작 고장",
    "공통원인 이벤트",
    "반복 이상",
]

REPRESENTATIVE_PRIORITY_ORDER = [
    "급작 고장",
    "전조형 고장",
    "공통원인 이벤트",
    "반복 이상",
    "불충분",
]

EVENT_PRIORITY = {
    "급작 고장": 1,
    "전조형 고장": 2,
    "공통원인 이벤트": 3,
    "반복 이상": 4,
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

SCOPE_BY_REPRESENTATIVE_VERDICT = {
    "전조형 고장": "step3_precursor_performance",
    "급작 고장": "step4_abrupt_no_precursor",
    "공통원인 이벤트": "step4_common_cause_routing",
}

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
        "gpvs_attach_feasibility": read_csv(share_dir / GPVS_ATTACH_FEASIBILITY_NAME),
        "gpvs_attach_candidates": read_csv(share_dir / GPVS_ATTACH_CANDIDATES_NAME),
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
        ["site", "panel_id", "고장시점", "증상명_ko", "세부근거_ko", "source_field_ko", "비고_ko"],
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
    representative_verdict: str,
    final_pack_by_scope: dict[str, dict[str, object]],
) -> str:
    scope = SCOPE_BY_REPRESENTATIVE_VERDICT.get(representative_verdict, "")
    if scope:
        final_row = final_pack_by_scope.get(scope, {})
        final_usage = normalize_text(final_row.get("final_usage_decision", ""))
        if final_usage == "bounded_reporting_use":
            return f"{representative_verdict} 축은 current closeout 기준 bounded current-data 수준으로만 읽는다."
        if final_usage == "exploratory_only":
            return f"{representative_verdict} 축은 current closeout 기준 exploratory 범위로만 읽는다."
    if representative_verdict == "반복 이상":
        return "반복 이상은 chronic monitor/반복 lane 해석이며 stable fault classifier claim이 아니다."
    if representative_verdict == "불충분":
        return "현재 stored positive universe와 직접 연결되지 않아 사건 성격을 보수적으로 유지한다."
    return "현재 저장 산출물만으로는 사건 성격 판정 근거가 제한적이다."


def representative_verdict_from_flags(flags: dict[str, int]) -> str:
    if flags["has_급작고장"]:
        return "급작 고장"
    if flags["has_전조형고장"]:
        return "전조형 고장"
    if flags["has_공통원인이벤트"]:
        return "공통원인 이벤트"
    if flags["has_반복이상"]:
        return "반복 이상"
    return "불충분"


def panel_fault_status_from_flags(flags: dict[str, int]) -> str:
    if flags["has_급작고장"] or flags["has_전조형고장"]:
        return "고장"
    if flags["has_공통원인이벤트"]:
        return "비고장"
    return "미확정"


def event_history_text(flags: dict[str, int]) -> str:
    members = [
        event_name
        for event_name in EVENT_HISTORY_ORDER
        if (
            (event_name == "전조형 고장" and flags["has_전조형고장"])
            or (event_name == "급작 고장" and flags["has_급작고장"])
            or (event_name == "공통원인 이벤트" and flags["has_공통원인이벤트"])
            or (event_name == "반복 이상" and flags["has_반복이상"])
        )
    ]
    return "+".join(members)


def map_kernel_axis(
    representative_verdict: str,
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

    if representative_verdict == "전조형 고장":
        return "출력 저하형", "불충분", "전조형 representative verdict라 nearest symptom 축으로 출력 저하형만 부착했다."
    if representative_verdict == "공통원인 이벤트":
        return "패턴 이상형", "불충분", "공통원인 representative verdict라 nearest symptom 축으로 패턴 이상형만 부착했다."
    if representative_verdict == "반복 이상":
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
) -> tuple[dict[tuple[str, str], dict[str, str]], str, int]:
    feasibility_row = feasibility_df.iloc[0]
    feasibility_value = normalize_text(feasibility_row["GPVS_패널별_직접판정_가능여부"])
    overlap_expected = int(pd.to_numeric(feasibility_row["overlap_panel_count"], errors="raise"))
    best_source = normalize_text(feasibility_row["최선_후보_파일"])
    feasibility_reason = normalize_text(feasibility_row["근거_ko"])

    if feasibility_value == "불가":
        return {}, f"{GPVS_ABSENCE_REASON} {feasibility_reason}".strip(), 0

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
        }

    source_note = (
        f"panel-level GPVS direct reference partially attached from {best_source} "
        f"(expected overlap={overlap_expected}, matched={len(gpvs_lookup)})"
    )
    if feasibility_reason:
        source_note += f". {feasibility_reason}"
    return gpvs_lookup, source_note, overlap_expected


def build_outputs(
    root: Path,
    frames: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, int], str]:
    workflow_panel_df = build_workflow_panel_df(frames["workflow"])
    cluster_df = build_cluster_df(frames["workflow"])
    workflow_by_key = workflow_lookup(workflow_panel_df)
    abrupt_by_key = abrupt_lookup(frames["abrupt6"])
    final_pack_by_scope = final_pack_lookup(frames["final_pack"])

    workflow_keys = set(workflow_by_key.keys())
    abrupt_keys = set(abrupt_by_key.keys())
    precursor_keys = build_precursor_positive_keys(frames["precursor_truth"])
    common_keys = build_common_cause_positive_keys(frames["common_cause"])
    workflow_watch_keys = {
        (normalize_text(row["site"]), normalize_text(row["display_entity_id"]))
        for row in workflow_panel_df.loc[workflow_panel_df["preview_attention_class"].eq("watch_now_panel")].to_dict(orient="records")
    }
    panel_keys = set().union(workflow_keys, abrupt_keys, precursor_keys, common_keys)

    gpvs_by_key, gpvs_source_note, gpvs_expected_attach_count = recover_gpvs_panel_level_reference_from_audit(
        frames["gpvs_attach_feasibility"],
        frames["gpvs_attach_candidates"],
        panel_keys,
    )

    panel_rows: list[dict[str, object]] = []
    event_rows: list[dict[str, object]] = []

    for site, panel_id in sorted(panel_keys):
        key = (site, panel_id)
        workflow_row = workflow_by_key.get(key)
        abrupt_row = abrupt_by_key.get(key)
        flags = {
            "has_전조형고장": int(key in precursor_keys),
            "has_급작고장": int(key in abrupt_keys),
            "has_공통원인이벤트": int(key in common_keys),
            "has_반복이상": int(key in workflow_watch_keys),
        }

        representative_verdict = representative_verdict_from_flags(flags)
        history = event_history_text(flags)
        kernel_symptom, kernel_cause_group, kernel_note = map_kernel_axis(representative_verdict, abrupt_row)

        gpvs_row = gpvs_by_key.get(key)
        if gpvs_row is None:
            gpvs_type = "미부착"
            gpvs_reason = GPVS_ABSENCE_REASON
        else:
            gpvs_type = normalize_text(gpvs_row["GPVS_참고유형_ko"]) or "미부착"
            gpvs_reason = normalize_text(gpvs_row["GPVS_근거_ko"]) or GPVS_ABSENCE_REASON

        universe_parts: list[str] = []
        if flags["has_전조형고장"]:
            universe_parts.append("precursor onset truth positive universe 포함")
        if flags["has_급작고장"]:
            universe_parts.append("abrupt6 positive universe 포함")
        if flags["has_공통원인이벤트"]:
            universe_parts.append("common-cause descriptive positive universe 포함")
        if flags["has_반복이상"]:
            universe_parts.append("workflow watch_now_panel 포함")
        if workflow_row is None:
            universe_parts.append("현재 workflow default row에는 아직 없음")
        if not universe_parts:
            universe_parts.append("workflow current row 기반 fallback verdict")

        caution_parts = [
            current_data_scope_note(representative_verdict, final_pack_by_scope),
            kernel_note,
            f"사건이력={history}" if history else "사건이력 없음",
            "; ".join(universe_parts),
        ]
        if gpvs_type == "미부착":
            caution_parts.append(GPVS_ABSENCE_REASON)

        panel_rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "대표판정_ko": representative_verdict,
                "사건이력_ko": history,
                "전조형이력_flag": flags["has_전조형고장"],
                "급작고장이력_flag": flags["has_급작고장"],
                "공통원인이력_flag": flags["has_공통원인이벤트"],
                "반복이상이력_flag": flags["has_반복이상"],
                "패널고장여부_ko": panel_fault_status_from_flags(flags),
                "커널로그_증상명_ko": kernel_symptom,
                "커널로그_원인군_ko": kernel_cause_group,
                "GPVS_참고유형_ko": gpvs_type,
                "GPVS_근거_ko": gpvs_reason,
                "운영위치_ko": map_operating_location(workflow_row),
                "판정주의_ko": " ".join(part for part in caution_parts if part),
            }
        )

        for event_name in EVENT_HISTORY_ORDER:
            if not history:
                break
            event_flag = (
                flags["has_전조형고장"] if event_name == "전조형 고장" else
                flags["has_급작고장"] if event_name == "급작 고장" else
                flags["has_공통원인이벤트"] if event_name == "공통원인 이벤트" else
                flags["has_반복이상"]
            )
            if not event_flag:
                continue
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
        "abrupt_expected": len(abrupt_keys),
        "precursor_expected": len(precursor_keys),
        "common_expected": len(common_keys),
        "gpvs_expected_attach_count": gpvs_expected_attach_count,
    }
    return verdict_df, event_supplement_df, cluster_supplement_df, metrics, gpvs_source_note


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

    abrupt_membership = int(to_numeric_flag(verdict_df["급작고장이력_flag"]).sum())
    precursor_membership = int(to_numeric_flag(verdict_df["전조형이력_flag"]).sum())
    common_membership = int(to_numeric_flag(verdict_df["공통원인이력_flag"]).sum())
    gpvs_attached = int(verdict_df["GPVS_참고유형_ko"].ne("미부착").sum())

    if abrupt_membership != 6:
        raise SystemExit(f"panels with 급작고장이력_flag must be 6, found {abrupt_membership}")
    if precursor_membership != 2:
        raise SystemExit(f"panels with 전조형이력_flag must be 2, found {precursor_membership}")
    if common_membership != 4:
        raise SystemExit(f"panels with 공통원인이력_flag must be 4, found {common_membership}")
    if gpvs_attached != int(metrics["gpvs_expected_attach_count"]):
        raise SystemExit(
            f"GPVS attached row count must equal feasibility overlap_panel_count {metrics['gpvs_expected_attach_count']}, found {gpvs_attached}"
        )

    if metrics["workflow_cluster_count"] > 0 and len(cluster_supplement_df) <= 0:
        raise SystemExit("cluster supplement check failed: workflow has discovery clusters but supplement is empty")
    if cluster_supplement_df["GPVS_참고유형_ko"].ne("미부착").any():
        raise SystemExit("cluster supplement must stay GPVS_참고유형_ko=미부착")
    if cluster_supplement_df["GPVS_근거_ko"].ne(GPVS_ABSENCE_REASON).any():
        raise SystemExit(f"cluster supplement must stay GPVS_근거_ko={GPVS_ABSENCE_REASON}")

    insufficient_rows = verdict_df.loc[
        verdict_df["대표판정_ko"].eq("불충분"),
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
    gpvs_source_note: str,
) -> pd.DataFrame:
    representative_counts = verdict_df["대표판정_ko"].value_counts().to_dict()
    panel_fault_counts = verdict_df["패널고장여부_ko"].value_counts().to_dict()
    symptom_attached = int(verdict_df["커널로그_증상명_ko"].ne("불충분").sum())
    cause_group_attached = int(verdict_df["커널로그_원인군_ko"].ne("불충분").sum())
    gpvs_attached = int(verdict_df["GPVS_참고유형_ko"].ne("미부착").sum())
    total_panels = int(len(verdict_df))

    row = {
        "전체_패널수": total_panels,
        "급작이력_패널수": int(to_numeric_flag(verdict_df["급작고장이력_flag"]).sum()),
        "전조형이력_패널수": int(to_numeric_flag(verdict_df["전조형이력_flag"]).sum()),
        "공통원인이력_패널수": int(to_numeric_flag(verdict_df["공통원인이력_flag"]).sum()),
        "반복이상이력_패널수": int(to_numeric_flag(verdict_df["반복이상이력_flag"]).sum()),
        "대표판정_급작수": int(representative_counts.get("급작 고장", 0)),
        "대표판정_전조형수": int(representative_counts.get("전조형 고장", 0)),
        "대표판정_공통원인수": int(representative_counts.get("공통원인 이벤트", 0)),
        "대표판정_반복이상수": int(representative_counts.get("반복 이상", 0)),
        "대표판정_불충분수": int(representative_counts.get("불충분", 0)),
        "고장_패널수": int(panel_fault_counts.get("고장", 0)),
        "비고장_패널수": int(panel_fault_counts.get("비고장", 0)),
        "미확정_패널수": int(panel_fault_counts.get("미확정", 0)),
        "커널로그_증상명_부착수": symptom_attached,
        "커널로그_원인군_부착수": cause_group_attached,
        "GPVS_참고유형_부착수": gpvs_attached,
        "GPVS_미부착수": total_panels - gpvs_attached,
        "사건보조행수": int(len(event_supplement_df)),
        "클러스터_보조행수": int(len(cluster_supplement_df)),
        "note_ko": (
            f"main panel table은 unique panel 대표 verdict 표이고 workflow panel {metrics['workflow_panel_count']}건을 기준으로 abrupt6 {metrics['abrupt_expected']}건, precursor {metrics['precursor_expected']}건, common-cause {metrics['common_expected']}건 membership을 함께 접었다. "
            "대표판정은 급작 > 전조형 > 공통원인 이벤트 > 반복 이상 > 불충분 우선순위를 쓴다. "
            "summary count는 final panel row와 membership flag에서 다시 계산했다. "
            f"사건이력 multi-membership은 event supplement로 분리했다. {gpvs_source_note} unmatched panel은 계속 `{GPVS_ABSENCE_REASON}` 으로 둔다."
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
    verdict_df, event_supplement_df, cluster_supplement_df, metrics, gpvs_source_note = build_outputs(root, frames)
    validate_real_coverage(verdict_df, event_supplement_df, cluster_supplement_df, metrics)
    summary_df = build_summary(verdict_df, event_supplement_df, cluster_supplement_df, metrics, gpvs_source_note)
    write_outputs(root, verdict_df, event_supplement_df, cluster_supplement_df, summary_df)


if __name__ == "__main__":
    main()
