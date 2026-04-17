#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.prognostics import gpvs_train_supervised as gpvs_supervised
from research.prognostics.build_panel_day_engine_gpvs_detailed_type_inference_audit_v1 import (
    build_real_panel_feature_row,
    ensure_columns,
    load_model_bundle,
    load_panel_core,
    load_training_frame,
    normalize_text,
    positive_training_mask,
    read_csv,
)


FAULT_PANEL_EVENT_AUDIT_NAME = "panel_day_engine_fault_panel_event_audit_v1.csv"
PANEL_MULTIAXIS_VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
DETAILED_TYPE_AUDIT_NAME = "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv"
REBUILD_SUMMARY_NAME = "panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv"
OPTIONAL_FAMILY_EVAL_NAME = "gpvs_fault_family_eval_cases.csv"
RECOVERED_MANIFEST_NAME = "gpvs_bytype_recovered_feature_manifest_v1.json"

OUTPUT_FEATURE_COMPATIBILITY_NAME = "panel_day_engine_gpvs_mlpe_feature_compatibility_v1.csv"
OUTPUT_DISTRIBUTION_SHIFT_NAME = "panel_day_engine_gpvs_mlpe_distribution_shift_v1.csv"
OUTPUT_PANEL_AGREEMENT_NAME = "panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv"
OUTPUT_SUMMARY_NAME = "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv"
OUTPUT_NOTE_NAME = "panel_day_engine_gpvs_mlpe_compatibility_note_v1.md"

FEATURE_COMPATIBILITY_COLS = [
    "feature_name",
    "in_recovered_manifest_flag",
    "in_training_frame_flag",
    "in_realpanel_frame_flag",
    "training_non_null_rate",
    "realpanel_non_null_rate",
    "schema_match_flag",
    "note_ko",
]

DISTRIBUTION_SHIFT_COLS = [
    "site",
    "panel_id",
    "event_reference_date",
    "feature_count",
    "out_of_p01_p99_count",
    "out_of_p05_p95_count",
    "max_abs_zscore",
    "median_percentile",
    "distribution_shift_bucket_ko",
]

PANEL_AGREEMENT_COLS = [
    "site",
    "panel_id",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
    "GPVS_참고유형_ko",
    "GPVS_외부참조시나리오명_ko",
    "family_vs_kernellog_alignment_ko",
    "scenario_vs_kernellog_alignment_ko",
    "feature_shift_bucket_ko",
    "overall_gpvs_reference_usefulness_ko",
    "overall_gpvs_trust_note_ko",
]

SUMMARY_COLS = [
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
]

WARNING_TEXT = "GPVS original scenario space and MLPE official problem-type space are not identical."

VERDICT_REQUIRED_COLS = ["site", "panel_id", "패널고장여부_ko", "커널로그_원인군_ko"]
VERDICT_FAMILY_COL_CANDIDATES = ["GPVS_내부참고유형_ko", "GPVS_참고유형_ko"]
VERDICT_SCENARIO_COL_CANDIDATES = ["GPVS_외부참조시나리오명_ko", "GPVS_시나리오명_ko"]
VERDICT_PATTERN_COL_CANDIDATES = ["GPVS_외부참조패턴_ko"]

GPVS_SCENARIO_NAME_BY_CANONICAL_CODE = {
    "F0": "정상 운전 시나리오",
    "F1": "인버터 전력소자 이상 시나리오",
    "F2": "제어 피드백 센서 이상 시나리오",
    "F3": "계통 전압 이상 시나리오",
    "F4": "PV 어레이 mismatch(부분 음영) 시나리오",
    "F5": "PV 어레이 mismatch(부분 개방회로) 시나리오",
    "F6": "부스트 컨버터 PI gain 이상 시나리오",
    "F7": "부스트 컨버터 PI 시정수 이상 시나리오",
}

GPVS_SCENARIO_NAME_BY_PATTERN = {
    "정상 기준선": "정상 운전 시나리오",
    "인버터/전력변환 이상 패턴": "인버터 전력소자 이상 시나리오",
    "제어·계측 이상 힌트": "제어 피드백 센서 이상 시나리오",
    "계통 교란 플래그": "계통 전압 이상 시나리오",
    "패널·어레이 mismatch 참조": "PV 어레이 mismatch(부분 음영) 시나리오",
    "부분 개방·접속 이상 참조": "PV 어레이 mismatch(부분 개방회로) 시나리오",
    "제어기 gain 이상 패턴": "부스트 컨버터 PI gain 이상 시나리오",
    "제어기 시정수 이상 패턴": "부스트 컨버터 PI 시정수 이상 시나리오",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit GPVS-to-MLPE compatibility and trustworthiness for current real fault panels."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root. Defaults to project root.",
    )
    return parser.parse_args()


def normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in normalized.columns:
        if normalized[column].dtype == object:
            normalized[column] = normalized[column].map(normalize_text)
    return normalized


def read_optional_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return ""


def normalized_column_or_blank(df: pd.DataFrame, column_name: str) -> pd.Series:
    if not column_name:
        return pd.Series([""] * len(df), index=df.index, dtype="object")
    return df[column_name].map(normalize_text)


def canonicalize_gpvs_code(value: object) -> str:
    text = normalize_text(value).upper()
    if len(text) < 2 or not text.startswith("F"):
        return ""
    candidate = text[:2]
    return candidate if candidate in GPVS_SCENARIO_NAME_BY_CANONICAL_CODE else ""


def resolve_scenario_name(
    *,
    legacy_scenario_name: object,
    detailed_fault_type: object,
    front_pattern_name: object,
) -> str:
    scenario_name = normalize_text(legacy_scenario_name)
    if scenario_name:
        return scenario_name

    canonical_code = canonicalize_gpvs_code(detailed_fault_type)
    if canonical_code:
        return GPVS_SCENARIO_NAME_BY_CANONICAL_CODE.get(canonical_code, "")

    return GPVS_SCENARIO_NAME_BY_PATTERN.get(normalize_text(front_pattern_name), "")


def choose_reference_date(row: pd.Series) -> str:
    strict_trigger = normalize_text(row.get("strict_trigger_date", ""))
    if strict_trigger:
        return strict_trigger
    first_final = normalize_text(row.get("first_final_fault_date", ""))
    if first_final:
        return first_final
    return ""


def to_flag(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return int(pd.notna(numeric) and int(numeric) == 1)


def load_manifest(root: Path) -> dict[str, object]:
    path = root / "data" / "gpvs" / "out" / RECOVERED_MANIFEST_NAME
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_context(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None]:
    share_dir = root / "_share"
    fault_df = normalize_frame(read_csv(share_dir / FAULT_PANEL_EVENT_AUDIT_NAME))
    verdict_df = normalize_frame(read_csv(share_dir / PANEL_MULTIAXIS_VERDICT_NAME))
    detailed_df = normalize_frame(read_csv(share_dir / DETAILED_TYPE_AUDIT_NAME))
    rebuild_summary_df = normalize_frame(read_csv(share_dir / REBUILD_SUMMARY_NAME))
    optional_family_eval_df = read_optional_csv(share_dir / OPTIONAL_FAMILY_EVAL_NAME)
    if optional_family_eval_df is not None:
        optional_family_eval_df = normalize_frame(optional_family_eval_df)

    ensure_columns(
        fault_df,
        ["site", "panel_id", "strict_trigger_date", "first_final_fault_date", "사건유형_재판정_ko", "최종고장양상_재판정_ko"],
        FAULT_PANEL_EVENT_AUDIT_NAME,
    )
    ensure_columns(verdict_df, VERDICT_REQUIRED_COLS, PANEL_MULTIAXIS_VERDICT_NAME)
    ensure_columns(
        detailed_df,
        [
            "site",
            "panel_id",
            "event_reference_date",
            "gpvs_family_label",
            "gpvs_detailed_model_source",
            "gpvs_detailed_top1_fault_type",
            "gpvs_detailed_top1_score",
            "gpvs_detailed_top2_fault_type",
            "gpvs_detailed_top2_score",
            "gpvs_detailed_margin",
            "gpvs_detailed_status_ko",
        ],
        DETAILED_TYPE_AUDIT_NAME,
    )
    ensure_columns(
        rebuild_summary_df,
        ["recovered_model_exported_flag", "current_recovered_attachable_flag"],
        REBUILD_SUMMARY_NAME,
    )

    fault_only = fault_df.copy()
    if len(fault_only) != 6:
        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_NAME} must contain exactly 6 current fault panels, found {len(fault_only)}")

    verdict_fault = verdict_df.loc[verdict_df["패널고장여부_ko"].eq("고장")].copy()
    if len(verdict_fault) != 6:
        raise SystemExit(
            f"{PANEL_MULTIAXIS_VERDICT_NAME} must contain exactly 6 fault rows by 패널고장여부_ko==고장, found {len(verdict_fault)}"
        )

    family_col = first_existing_column(verdict_fault, VERDICT_FAMILY_COL_CANDIDATES)
    scenario_col = first_existing_column(verdict_fault, VERDICT_SCENARIO_COL_CANDIDATES)
    pattern_col = first_existing_column(verdict_fault, VERDICT_PATTERN_COL_CANDIDATES)
    verdict_fault = verdict_fault.copy()
    verdict_fault["resolved_gpvs_family_ko"] = normalized_column_or_blank(verdict_fault, family_col)
    verdict_fault["resolved_gpvs_external_scenario_ko"] = normalized_column_or_blank(verdict_fault, scenario_col)
    verdict_fault["resolved_gpvs_external_pattern_ko"] = normalized_column_or_blank(verdict_fault, pattern_col)

    merged = (
        fault_only.merge(
            verdict_fault,
            on=["site", "panel_id"],
            how="left",
            suffixes=("", "_verdict"),
        )
        .merge(
            detailed_df,
            on=["site", "panel_id"],
            how="left",
            suffixes=("", "_detail"),
        )
        .reset_index(drop=True)
    )
    merged["GPVS_참고유형_ko"] = merged["resolved_gpvs_family_ko"].map(normalize_text)
    family_blank = merged["GPVS_참고유형_ko"].eq("")
    merged.loc[family_blank, "GPVS_참고유형_ko"] = merged.loc[family_blank, "gpvs_family_label"].map(normalize_text)
    merged["GPVS_외부참조시나리오명_ko"] = merged.apply(
        lambda row: resolve_scenario_name(
            legacy_scenario_name=row.get("resolved_gpvs_external_scenario_ko", ""),
            detailed_fault_type=row.get("gpvs_detailed_top1_fault_type", ""),
            front_pattern_name=row.get("resolved_gpvs_external_pattern_ko", ""),
        ),
        axis=1,
    )
    return merged, rebuild_summary_df, optional_family_eval_df


def build_training_frames(root: Path) -> tuple[pd.DataFrame, list[str]]:
    training_raw = load_training_frame(root)
    training_eng, training_feature_cols = gpvs_supervised._feature_engineering(training_raw)
    positive_mask = positive_training_mask(training_raw) & training_raw["fault_type"].map(normalize_text).ne("")
    training_pos = training_eng.loc[positive_mask].copy()
    if training_pos.empty:
        raise SystemExit("gpvs_window_scores.csv has no positive fault_type rows for compatibility audit")
    return training_pos, training_feature_cols


def build_realpanel_feature_frame(root: Path, context_df: pd.DataFrame, feature_cols: list[str]) -> tuple[pd.DataFrame, dict[tuple[str, str], str]]:
    rows: list[dict[str, object]] = []
    reasons: dict[tuple[str, str], str] = {}
    panel_core_cache: dict[str, pd.DataFrame] = {}

    for row in context_df.to_dict(orient="records"):
        site = normalize_text(row.get("site", ""))
        panel_id = normalize_text(row.get("panel_id", ""))
        reference_date = normalize_text(row.get("event_reference_date", "")) or choose_reference_date(pd.Series(row))
        if not reference_date:
            reasons[(site, panel_id)] = "reference event date 없음"
            continue
        if site not in panel_core_cache:
            panel_core_cache[site] = load_panel_core(root, site)
        panel_df = panel_core_cache[site]
        panel_df = panel_df.loc[panel_df["panel_id"].map(normalize_text).eq(panel_id)].copy()
        feature_df, reason = build_real_panel_feature_row(panel_df, reference_date, feature_cols)
        if feature_df is None:
            reasons[(site, panel_id)] = reason
            continue
        payload = {column: feature_df.iloc[0][column] for column in feature_df.columns}
        payload.update({"site": site, "panel_id": panel_id, "event_reference_date": reference_date})
        rows.append(payload)

    real_df = pd.DataFrame(rows)
    if real_df.empty:
        real_df = pd.DataFrame(columns=["site", "panel_id", "event_reference_date", *feature_cols])
    return real_df, reasons


def build_feature_compatibility_df(
    manifest_feature_cols: list[str],
    removed_zero_var: set[str],
    training_pos: pd.DataFrame,
    training_feature_cols: list[str],
    realpanel_feature_df: pd.DataFrame,
) -> pd.DataFrame:
    training_set = set(training_feature_cols)
    realpanel_cols = {column for column in realpanel_feature_df.columns if column not in {"site", "panel_id", "event_reference_date"}}
    all_features = sorted(set(manifest_feature_cols) | training_set | realpanel_cols)
    rows: list[dict[str, object]] = []

    for feature_name in all_features:
        in_manifest = int(feature_name in manifest_feature_cols)
        in_training = int(feature_name in training_set)
        in_realpanel = int(feature_name in realpanel_cols)

        training_non_null_rate = ""
        if feature_name in training_pos.columns:
            training_non_null_rate = float(training_pos[feature_name].notna().mean())

        realpanel_non_null_rate = ""
        if feature_name in realpanel_feature_df.columns:
            realpanel_non_null_rate = float(realpanel_feature_df[feature_name].notna().mean())

        schema_match_flag = int(bool(in_manifest and in_training and in_realpanel))
        if feature_name in removed_zero_var:
            note = "training engineering에는 있었지만 zero-variance 제거로 recovered head 입력에서는 빠짐"
        elif schema_match_flag:
            note = "recovered model, training path, real-panel inference path가 모두 공유하는 feature"
        elif in_training and not in_manifest:
            note = "training engineering에는 있으나 recovered head 입력에는 사용되지 않음"
        elif in_manifest and not in_realpanel:
            note = "recovered head 입력에는 있으나 현재 real fault panel 6건에서는 재구성되지 않음"
        elif in_realpanel and not in_manifest:
            note = "real-panel 중간 재구성 frame에는 있으나 recovered head 입력에는 직접 쓰이지 않음"
        else:
            note = "schema 간 직접 대응이 약함"

        rows.append(
            {
                "feature_name": feature_name,
                "in_recovered_manifest_flag": in_manifest,
                "in_training_frame_flag": in_training,
                "in_realpanel_frame_flag": in_realpanel,
                "training_non_null_rate": training_non_null_rate,
                "realpanel_non_null_rate": realpanel_non_null_rate,
                "schema_match_flag": schema_match_flag,
                "note_ko": note,
            }
        )

    return pd.DataFrame(rows).reindex(columns=FEATURE_COMPATIBILITY_COLS)


def classify_distribution_shift(feature_count: int, out_of_p01_p99_count: int, out_of_p05_p95_count: int, max_abs_zscore: float) -> str:
    if feature_count <= 0:
        return "cannot_compare"
    if out_of_p01_p99_count == 0 and (not np.isfinite(max_abs_zscore) or max_abs_zscore < 2.0):
        return "training_range_inside"
    if out_of_p05_p95_count <= max(2, int(round(feature_count * 0.25))) and (not np.isfinite(max_abs_zscore) or max_abs_zscore < 4.0):
        return "mild_shift"
    return "strong_shift"


def build_distribution_shift_df(
    context_df: pd.DataFrame,
    training_pos: pd.DataFrame,
    feature_cols: list[str],
    realpanel_feature_df: pd.DataFrame,
    missing_reasons: dict[tuple[str, str], str],
) -> pd.DataFrame:
    real_indexed = realpanel_feature_df.set_index(["site", "panel_id"], drop=False) if not realpanel_feature_df.empty else pd.DataFrame()
    rows: list[dict[str, object]] = []

    for row in context_df.to_dict(orient="records"):
        site = normalize_text(row.get("site", ""))
        panel_id = normalize_text(row.get("panel_id", ""))
        reference_date = normalize_text(row.get("event_reference_date", "")) or choose_reference_date(pd.Series(row))
        key = (site, panel_id)
        if isinstance(real_indexed, pd.DataFrame) and not real_indexed.empty and key in real_indexed.index:
            feature_row = real_indexed.loc[key]
        else:
            _reason = missing_reasons.get(key, "real-panel feature row 없음")
            rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "event_reference_date": reference_date,
                    "feature_count": 0,
                    "out_of_p01_p99_count": 0,
                    "out_of_p05_p95_count": 0,
                    "max_abs_zscore": "",
                    "median_percentile": "",
                    "distribution_shift_bucket_ko": "cannot_compare",
                }
            )
            continue

        compared = 0
        out_p01_p99 = 0
        out_p05_p95 = 0
        zscores: list[float] = []
        percentiles: list[float] = []
        for feature_name in feature_cols:
            if feature_name not in training_pos.columns:
                continue
            train_series = pd.to_numeric(training_pos[feature_name], errors="coerce").dropna()
            feature_value = pd.to_numeric(pd.Series([feature_row.get(feature_name)]), errors="coerce").iloc[0]
            if train_series.empty or pd.isna(feature_value):
                continue
            compared += 1
            p01 = float(np.nanpercentile(train_series, 1))
            p99 = float(np.nanpercentile(train_series, 99))
            p05 = float(np.nanpercentile(train_series, 5))
            p95 = float(np.nanpercentile(train_series, 95))
            median = float(np.nanmedian(train_series))
            std = float(np.nanstd(train_series))
            value = float(feature_value)
            if value < p01 or value > p99:
                out_p01_p99 += 1
            if value < p05 or value > p95:
                out_p05_p95 += 1
            percentiles.append(float((train_series <= value).mean() * 100.0))
            if std > 0 and np.isfinite(std):
                zscores.append(abs((value - median) / std))

        max_abs_zscore = float(max(zscores)) if zscores else np.nan
        median_percentile = float(np.median(percentiles)) if percentiles else np.nan
        bucket = classify_distribution_shift(compared, out_p01_p99, out_p05_p95, max_abs_zscore)
        rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "event_reference_date": reference_date,
                "feature_count": compared,
                "out_of_p01_p99_count": out_p01_p99,
                "out_of_p05_p95_count": out_p05_p95,
                "max_abs_zscore": max_abs_zscore if np.isfinite(max_abs_zscore) else "",
                "median_percentile": median_percentile if np.isfinite(median_percentile) else "",
                "distribution_shift_bucket_ko": bucket,
            }
        )

    return pd.DataFrame(rows).reindex(columns=DISTRIBUTION_SHIFT_COLS)


def classify_family_alignment(kernel_cause: str, gpvs_family_label: str) -> str:
    kernel = normalize_text(kernel_cause)
    family = normalize_text(gpvs_family_label)
    if not kernel or not family:
        return "비교곤란"
    if family == "불확실":
        return "비교곤란"
    if kernel == "개방/장치이상형" and "개방/장치이상" in family:
        return "일치"
    if kernel == "다이오드형" and family == "전기적 고장 계열":
        return "일치"
    if kernel == "모듈손상형" and family == "전기적 고장 계열":
        return "부분일치"
    return "비교곤란"


def classify_scenario_alignment(kernel_cause: str, scenario_name: str) -> str:
    kernel = normalize_text(kernel_cause)
    scenario = normalize_text(scenario_name)
    if not kernel or not scenario:
        return "비교곤란"
    if "제어 피드백 센서 이상" in scenario and kernel in {"다이오드형", "모듈손상형", "개방/장치이상형"}:
        return "불일치"
    if "PV 어레이 mismatch" in scenario and kernel in {"다이오드형", "모듈손상형"}:
        return "부분일치"
    return "비교곤란"


def build_reference_usefulness(family_alignment: str, scenario_alignment: str, shift_bucket: str) -> tuple[str, str]:
    if shift_bucket == "cannot_compare":
        return (
            "비권장",
            "real-panel feature vector를 비교하지 못해 GPVS를 reference layer로도 신뢰하기 어려움",
        )
    if scenario_alignment == "불일치" or family_alignment == "불일치":
        return (
            "비권장",
            "외부 GPVS scenario/family 방향성이 current kernel-log 원인군과 직접 충돌해 direct trust를 주기 어려움",
        )
    if shift_bucket == "strong_shift":
        return (
            "주의참고",
            "feature schema는 맞지만 training 대비 분포 이동이 커서 GPVS는 reference-only로만 읽는 편이 안전함",
        )
    if family_alignment in {"일치", "부분일치"} or scenario_alignment == "부분일치":
        return (
            "참고가능",
            "directional reference로는 읽을 수 있으나 external GPVS scenario를 물리 root cause로 번역하면 안 됨",
        )
    return (
        "주의참고",
        "의미 축이 직접 대응하지 않아 GPVS는 decision axis가 아니라 보조 reference로만 읽어야 함",
    )


def build_panel_agreement_df(context_df: pd.DataFrame, distribution_df: pd.DataFrame) -> pd.DataFrame:
    shift_map = {
        (normalize_text(row.get("site", "")), normalize_text(row.get("panel_id", ""))): normalize_text(
            row.get("distribution_shift_bucket_ko", "")
        )
        for row in distribution_df.to_dict(orient="records")
    }
    rows: list[dict[str, object]] = []

    for row in context_df.to_dict(orient="records"):
        site = normalize_text(row.get("site", ""))
        panel_id = normalize_text(row.get("panel_id", ""))
        kernel_cause = normalize_text(row.get("커널로그_원인군_ko", ""))
        gpvs_family = normalize_text(row.get("GPVS_참고유형_ko", ""))
        scenario_name = normalize_text(row.get("GPVS_외부참조시나리오명_ko", "")) or normalize_text(row.get("GPVS_시나리오명_ko", ""))
        family_alignment = classify_family_alignment(kernel_cause, gpvs_family)
        scenario_alignment = classify_scenario_alignment(kernel_cause, scenario_name)
        shift_bucket = shift_map.get((site, panel_id), "cannot_compare")
        usefulness, trust_note = build_reference_usefulness(family_alignment, scenario_alignment, shift_bucket)
        rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "사건유형_ko": normalize_text(row.get("사건유형_재판정_ko", "")) or normalize_text(row.get("사건유형_ko", "")),
                "최종고장양상_ko": normalize_text(row.get("최종고장양상_재판정_ko", "")) or normalize_text(row.get("최종고장양상_ko", "")),
                "커널로그_원인군_ko": kernel_cause,
                "GPVS_참고유형_ko": gpvs_family,
                "GPVS_외부참조시나리오명_ko": scenario_name,
                "family_vs_kernellog_alignment_ko": family_alignment,
                "scenario_vs_kernellog_alignment_ko": scenario_alignment,
                "feature_shift_bucket_ko": shift_bucket,
                "overall_gpvs_reference_usefulness_ko": usefulness,
                "overall_gpvs_trust_note_ko": trust_note,
            }
        )

    return pd.DataFrame(rows).reindex(columns=PANEL_AGREEMENT_COLS)


def build_summary_df(
    feature_compatibility_df: pd.DataFrame,
    distribution_df: pd.DataFrame,
    agreement_df: pd.DataFrame,
    rebuild_summary_df: pd.DataFrame,
    model_source: str,
) -> pd.DataFrame:
    manifest_rows = feature_compatibility_df.loc[
        feature_compatibility_df["in_recovered_manifest_flag"].eq(1)
    ].copy()
    feature_schema_match_ratio = (
        float(pd.to_numeric(manifest_rows["schema_match_flag"], errors="coerce").mean()) if not manifest_rows.empty else 0.0
    )

    fault_panel_count = int(len(agreement_df))
    recovered_model_present_flag = int(
        model_source == "recovered_artifact"
        and not rebuild_summary_df.empty
        and to_flag(rebuild_summary_df.iloc[0].get("recovered_model_exported_flag", 0)) == 1
    )
    strong_shift_panel_count = int(distribution_df["distribution_shift_bucket_ko"].eq("strong_shift").sum())
    mild_shift_panel_count = int(distribution_df["distribution_shift_bucket_ko"].eq("mild_shift").sum())

    family_alignment_count = int(agreement_df["family_vs_kernellog_alignment_ko"].eq("일치").sum())
    family_partial_alignment_count = int(agreement_df["family_vs_kernellog_alignment_ko"].eq("부분일치").sum())
    family_conflict_count = int(agreement_df["family_vs_kernellog_alignment_ko"].eq("불일치").sum())

    scenario_alignment_count = int(agreement_df["scenario_vs_kernellog_alignment_ko"].eq("일치").sum())
    scenario_partial_alignment_count = int(agreement_df["scenario_vs_kernellog_alignment_ko"].eq("부분일치").sum())
    scenario_conflict_count = int(agreement_df["scenario_vs_kernellog_alignment_ko"].eq("불일치").sum())

    useful_count = int(agreement_df["overall_gpvs_reference_usefulness_ko"].eq("참고가능").sum())
    caution_count = int(agreement_df["overall_gpvs_reference_usefulness_ko"].eq("주의참고").sum())
    not_recommended_count = int(agreement_df["overall_gpvs_reference_usefulness_ko"].eq("비권장").sum())

    if fault_panel_count <= 0:
        final_recommendation = "증거 부족"
    elif not recovered_model_present_flag:
        final_recommendation = "직접 판정축 사용 비권장"
    elif strong_shift_panel_count > 0 or scenario_conflict_count > 0 or family_conflict_count > 0:
        final_recommendation = "참고축으로만 사용"
    elif mild_shift_panel_count > 0 or scenario_partial_alignment_count > 0 or family_partial_alignment_count > 0:
        final_recommendation = "조건부 참고 가능"
    else:
        final_recommendation = "조건부 참고 가능"

    note = (
        f"schema_match_ratio={feature_schema_match_ratio:.3f}, strong_shift_panel_count={strong_shift_panel_count}, "
        f"scenario_conflict_count={scenario_conflict_count}. {WARNING_TEXT} "
        "따라서 GPVS는 direct root-cause classifier가 아니라 reference layer로만 읽는 것이 안전하다."
    )

    return pd.DataFrame(
        [
            {
                "fault_panel_count": fault_panel_count,
                "recovered_model_present_flag": recovered_model_present_flag,
                "feature_schema_match_ratio": feature_schema_match_ratio,
                "strong_shift_panel_count": strong_shift_panel_count,
                "mild_shift_panel_count": mild_shift_panel_count,
                "family_alignment_count": family_alignment_count,
                "family_partial_alignment_count": family_partial_alignment_count,
                "family_conflict_count": family_conflict_count,
                "scenario_alignment_count": scenario_alignment_count,
                "scenario_partial_alignment_count": scenario_partial_alignment_count,
                "scenario_conflict_count": scenario_conflict_count,
                "gpvs_reference_useful_count": useful_count,
                "gpvs_reference_caution_count": caution_count,
                "gpvs_reference_not_recommended_count": not_recommended_count,
                "final_recommendation_ko": final_recommendation,
                "note_ko": note,
            }
        ]
    ).reindex(columns=SUMMARY_COLS)


def build_note_md(
    summary_df: pd.DataFrame,
    optional_family_eval_df: pd.DataFrame | None,
) -> str:
    summary_row = summary_df.iloc[0].to_dict() if not summary_df.empty else {}
    schema_ratio = pd.to_numeric(pd.Series([summary_row.get("feature_schema_match_ratio", np.nan)]), errors="coerce").iloc[0]
    strong_shift_count = int(pd.to_numeric(pd.Series([summary_row.get("strong_shift_panel_count", 0)]), errors="coerce").fillna(0).iloc[0])
    family_align = int(pd.to_numeric(pd.Series([summary_row.get("family_alignment_count", 0)]), errors="coerce").fillna(0).iloc[0])
    family_partial = int(pd.to_numeric(pd.Series([summary_row.get("family_partial_alignment_count", 0)]), errors="coerce").fillna(0).iloc[0])
    scenario_partial = int(pd.to_numeric(pd.Series([summary_row.get("scenario_partial_alignment_count", 0)]), errors="coerce").fillna(0).iloc[0])
    scenario_conflict = int(pd.to_numeric(pd.Series([summary_row.get("scenario_conflict_count", 0)]), errors="coerce").fillna(0).iloc[0])
    final_recommendation = normalize_text(summary_row.get("final_recommendation_ko", ""))

    training_eval_line = "family-only eval asset는 있으나 row-level fault_type↔family one-to-one asset는 현재 직접 확인되지 않음"
    if optional_family_eval_df is not None and not optional_family_eval_df.empty:
        training_eval_line = (
            f"_share/{OPTIONAL_FAMILY_EVAL_NAME}는 family-level eval 행 {len(optional_family_eval_df)}건을 주지만, "
            "fault_type과 family_label을 같은 row에서 직접 연결하는 자산은 아님"
        )

    return "\n".join(
        [
            "# panel_day_engine_gpvs_mlpe_compatibility_note_v1",
            "",
            "## 1. 왜 호환성 점검이 필요한가",
            "- GPVS original scenario space and MLPE official problem-type space are not identical.",
            "- 그래서 GPVS detailed output을 실제 패널의 direct root-cause classifier처럼 자동 해석하면 안 된다.",
            "- 이번 audit은 recovered GPVS by-type head가 MLPE real fault panel 6건에서 reference layer로는 어느 정도 믿을 수 있는지, 그리고 decision axis로 확장할 수 있는지를 분리해서 본다.",
            "",
            "## 2. feature/schema 호환성",
            f"- recovered model manifest 기준 schema_match_ratio는 {schema_ratio:.3f} 이다.",
            f"- recovered head 실제 사용 feature와 real-panel 재구성 feature는 현재 크게 맞춰지지만, real fault panel 6건 중 strong_shift 판정은 {strong_shift_count}건이다.",
            "- 즉 schema availability와 distribution compatibility는 같은 질문이 아니다.",
            "",
            "## 3. 의미/라벨 호환성",
            f"- GPVS family vs kernel-log 원인군은 일치 {family_align}건, 부분일치 {family_partial}건이다.",
            f"- GPVS external scenario vs kernel-log 원인군은 부분일치 {scenario_partial}건, 불일치 {scenario_conflict}건이다.",
            f"- {training_eval_line}",
            "- therefore GPVS should not automatically be treated as a direct root-cause classifier.",
            "",
            "## 4. 실제 고장 패널 6건에서의 신뢰도",
            f"- 현재 summary recommendation은 `{final_recommendation}` 이다.",
            "- recovered by-type artifact가 존재해도, real-panel feature distribution이 training과 많이 다르면 confidence를 그대로 가져오면 안 된다.",
            "- 특히 external scenario name은 MLPE kernel-log 원인군과 직접 같은 label space가 아니므로, scenario-level 일치는 매우 보수적으로 읽어야 한다.",
            "",
            "## 5. 지금 허용되는 사용 방식",
            "- GPVS는 reference layer로는 읽을 수 있지만, 현재 audit 기준으로는 MLPE official verdict를 대체하는 direct decision axis로 쓰면 안 된다.",
            "- 허용되는 표현은 'GPVS 참조 family/scenario가 이런 방향을 가리킨다' 수준까지다.",
            "- 허용되지 않는 표현은 'GPVS code가 곧 실제 panel physical root cause다' 같은 단정이다.",
        ]
    ) + "\n"


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    context_df, rebuild_summary_df, optional_family_eval_df = build_context(root)
    training_pos, training_feature_cols = build_training_frames(root)
    _model, feature_cols, model_source = load_model_bundle(root)
    manifest = load_manifest(root)
    manifest_feature_cols = [normalize_text(value) for value in manifest.get("kept_features", []) if normalize_text(value)]
    if not manifest_feature_cols:
        manifest_feature_cols = list(feature_cols)
    removed_zero_var = {normalize_text(value) for value in manifest.get("removed_zero_var", []) if normalize_text(value)}

    realpanel_feature_df, missing_reasons = build_realpanel_feature_frame(root, context_df, feature_cols)
    feature_compatibility_df = build_feature_compatibility_df(
        manifest_feature_cols=manifest_feature_cols,
        removed_zero_var=removed_zero_var,
        training_pos=training_pos,
        training_feature_cols=training_feature_cols,
        realpanel_feature_df=realpanel_feature_df,
    )
    distribution_df = build_distribution_shift_df(
        context_df=context_df,
        training_pos=training_pos,
        feature_cols=feature_cols,
        realpanel_feature_df=realpanel_feature_df,
        missing_reasons=missing_reasons,
    )
    agreement_df = build_panel_agreement_df(context_df, distribution_df)
    summary_df = build_summary_df(
        feature_compatibility_df=feature_compatibility_df,
        distribution_df=distribution_df,
        agreement_df=agreement_df,
        rebuild_summary_df=rebuild_summary_df,
        model_source=model_source,
    )
    note_md = build_note_md(summary_df, optional_family_eval_df)

    feature_compatibility_df.to_csv(share_dir / OUTPUT_FEATURE_COMPATIBILITY_NAME, index=False, encoding="utf-8-sig")
    distribution_df.to_csv(share_dir / OUTPUT_DISTRIBUTION_SHIFT_NAME, index=False, encoding="utf-8-sig")
    agreement_df.to_csv(share_dir / OUTPUT_PANEL_AGREEMENT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / OUTPUT_SUMMARY_NAME, index=False, encoding="utf-8-sig")
    (share_dir / OUTPUT_NOTE_NAME).write_text(note_md, encoding="utf-8")


if __name__ == "__main__":
    main()
