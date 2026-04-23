#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]

VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
EVIDENCE_SUMMARY_NAME = "panel_day_engine_gpvs_evidence_summary_v1.csv"
CAUSE_SUMMARY_NAME = "panel_day_engine_cause_candidate_summary_v1.csv"
FINAL_DECISION_PACK_NAME = "panel_day_engine_project_final_decision_pack_v1.csv"

FULL_ALGORITHM_F1_NAME = "full_algorithm_f1_summary_v3.csv"
CRITICAL_ACTIONABILITY_F1_NAME = "critical_actionability_f1_summary.csv"
GPVS_FAMILY_F1_NAME = "gpvs_fault_family_f1_summary.csv"
FIELD_VALIDATION_SUMMARY_NAME = "field_validation_summary.csv"

VALIDATION_DOC_PATH = REPO_ROOT / "docs/OPS_FAULT_VALIDATION_MATRIX_V1.md"
VALIDATION_REPORT_PATH = REPO_ROOT / "outputs/validation/fault_validation_report_v1.csv"
VALIDATION_RUNNER_PATH = REPO_ROOT / "research/prognostics/run_fault_validation_v1.py"

OUTPUT_COVERAGE_NAME = "panel_day_engine_fault_coverage_matrix_v1.csv"
OUTPUT_METRICS_NAME = "panel_day_engine_model_metrics_v1.csv"

COVERAGE_COLS = [
    "target_fault_or_anomaly_ko",
    "detection_signal_or_pattern_ko",
    "primary_layer_ko",
    "supporting_layers_csv",
    "key_features_or_patterns_ko",
    "final_output_field_ko",
    "coverage_level_ko",
    "note_ko",
]

METRIC_COLS = [
    "layer_ko",
    "metric_family_ko",
    "metric_name",
    "metric_value",
    "dataset_scope_ko",
    "official_flag",
    "note_ko",
]

VERDICT_REQUIRED_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
]

EVIDENCE_SUMMARY_REQUIRED_COLS = [
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

CAUSE_SUMMARY_REQUIRED_COLS = [
    "fault_panel_count",
    "unique_top1_candidate_count",
    "top1_열화형_count",
    "top1_다이오드·서브스트링형_count",
    "top1_센서·피드백형_count",
    "단일우세_count",
    "two_way_competition_count",
    "multi_way_competition_count",
    "note_ko",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a concise coverage/performance report for the frozen panel day engine stack."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root. Defaults to the project root.",
    )
    return parser.parse_args(argv)


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


def ensure_validation_report(root: Path) -> pd.DataFrame:
    report_path = root / "outputs/validation/fault_validation_report_v1.csv"
    if not report_path.exists():
        result = subprocess.run(
            [sys.executable, str(root / "research/prognostics/run_fault_validation_v1.py")],
            cwd=root,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            raise SystemExit(
                "failed to regenerate outputs/validation/fault_validation_report_v1.csv: "
                f"{result.stderr or result.stdout}"
            )
    return read_csv(report_path)


def first_row(df: pd.DataFrame, name: str) -> pd.Series:
    if len(df) != 1:
        raise SystemExit(f"{name} must contain exactly one row, found {len(df)}")
    return df.iloc[0]


def build_stack_summary_row(verdict_df: pd.DataFrame, evidence_summary_row: pd.Series) -> pd.Series:
    total_panels = int(len(verdict_df))
    fault_panels = int(verdict_df["패널고장여부_ko"].map(normalize_text).eq("고장").sum())
    non_fault_or_unresolved = total_panels - fault_panels
    core_reference = int(pd.to_numeric(evidence_summary_row["core_reference_count"], errors="coerce"))
    auxiliary_reference = int(pd.to_numeric(evidence_summary_row["auxiliary_reference_count"], errors="coerce"))
    not_used = int(pd.to_numeric(evidence_summary_row["not_recommended_count"], errors="coerce"))
    return pd.Series(
        {
            "total_panel_count": total_panels,
            "fault_panel_count": fault_panels,
            "non_fault_or_unresolved_count": non_fault_or_unresolved,
            "gpvs_core_reference_count": core_reference,
            "gpvs_auxiliary_reference_count": auxiliary_reference,
            "gpvs_not_used_count": not_used,
            "note_ko": "panel multiaxis verdict row count와 GPVS evidence summary count를 결합한 derived stack summary 임",
        }
    )


def find_metric_row(
    df: pd.DataFrame,
    *,
    filters: dict[str, str],
) -> dict[str, str]:
    if df.empty:
        return {}
    candidate = df.copy()
    for column, value in filters.items():
        candidate = candidate.loc[candidate[column].map(normalize_text).eq(value)].copy()
    if candidate.empty:
        return {}
    return {key: normalize_text(val) for key, val in candidate.iloc[0].to_dict().items()}


def coverage_rows(
    integrated_summary_row: pd.Series,
    evidence_summary_row: pd.Series,
    cause_summary_row: pd.Series,
) -> list[dict[str, str]]:
    total_panels = int(pd.to_numeric(integrated_summary_row["total_panel_count"], errors="coerce"))
    fault_panels = int(pd.to_numeric(integrated_summary_row["fault_panel_count"], errors="coerce"))
    gpvs_core = int(pd.to_numeric(integrated_summary_row["gpvs_core_reference_count"], errors="coerce"))
    gpvs_aux = int(pd.to_numeric(integrated_summary_row["gpvs_auxiliary_reference_count"], errors="coerce"))
    heuristic_support = int(pd.to_numeric(cause_summary_row["fault_panel_count"], errors="coerce"))
    rows = [
        {
            "target_fault_or_anomaly_ko": "패널고장여부",
            "detection_signal_or_pattern_ko": "대표 panel verdict fault gating",
            "primary_layer_ko": "panel multiaxis verdict",
            "supporting_layers_csv": "conalog 해석층",
            "key_features_or_patterns_ko": "사건유형, 사건이력, 전조흔적, 순수급작, 운영 evidence",
            "final_output_field_ko": "패널고장여부_ko",
            "coverage_level_ko": "직접커버",
            "note_ko": f"현재 frozen integrated summary 기준 total_panel_count={total_panels}, fault_panel_count={fault_panels} 이며 primary status field를 직접 생성함",
        },
        {
            "target_fault_or_anomaly_ko": "전조형 고장",
            "detection_signal_or_pattern_ko": "precursor-bearing event pattern",
            "primary_layer_ko": "사건유형/고장양상 판단",
            "supporting_layers_csv": "panel multiaxis verdict,conalog 해석층",
            "key_features_or_patterns_ko": "retrospective onset, strict trigger, precursor truth membership",
            "final_output_field_ko": "사건유형_ko",
            "coverage_level_ko": "직접커버",
            "note_ko": "사건유형_ko 축에서 직접 표기되는 current frozen event family 중 하나임",
        },
        {
            "target_fault_or_anomaly_ko": "급작 고장",
            "detection_signal_or_pattern_ko": "abrupt no-precursor event pattern",
            "primary_layer_ko": "사건유형/고장양상 판단",
            "supporting_layers_csv": "panel multiaxis verdict,conalog 해석층",
            "key_features_or_patterns_ko": "pure abrupt membership, abrupt event map, event audit rule",
            "final_output_field_ko": "사건유형_ko",
            "coverage_level_ko": "직접커버",
            "note_ko": "사건유형_ko 축에서 직접 표기되는 current frozen event family 중 하나임",
        },
        {
            "target_fault_or_anomaly_ko": "진행성 악화",
            "detection_signal_or_pattern_ko": "progressive terminal deterioration pattern",
            "primary_layer_ko": "사건유형/고장양상 판단",
            "supporting_layers_csv": "panel multiaxis verdict",
            "key_features_or_patterns_ko": "전조형 사건의 terminal pattern split",
            "final_output_field_ko": "최종고장양상_ko",
            "coverage_level_ko": "직접커버",
            "note_ko": "최종고장양상_ko 축에서 직접 표기되는 terminal pattern 임",
        },
        {
            "target_fault_or_anomaly_ko": "급격 종료",
            "detection_signal_or_pattern_ko": "abrupt terminal stop after precursor-bearing event",
            "primary_layer_ko": "사건유형/고장양상 판단",
            "supporting_layers_csv": "panel multiaxis verdict",
            "key_features_or_patterns_ko": "전조형 사건 후 급격 종료 규칙",
            "final_output_field_ko": "최종고장양상_ko",
            "coverage_level_ko": "직접커버",
            "note_ko": "최종고장양상_ko 축에서 직접 표기되는 terminal pattern 임",
        },
        {
            "target_fault_or_anomaly_ko": "급작 발생",
            "detection_signal_or_pattern_ko": "pure abrupt terminal onset",
            "primary_layer_ko": "사건유형/고장양상 판단",
            "supporting_layers_csv": "panel multiaxis verdict",
            "key_features_or_patterns_ko": "급작 고장 lane의 terminal pattern",
            "final_output_field_ko": "최종고장양상_ko",
            "coverage_level_ko": "직접커버",
            "note_ko": "최종고장양상_ko 축에서 직접 표기되는 terminal pattern 임",
        },
        {
            "target_fault_or_anomaly_ko": "conalog 다이오드형",
            "detection_signal_or_pattern_ko": "conalog direct operational interpretation for diode-like pattern",
            "primary_layer_ko": "conalog 해석층",
            "supporting_layers_csv": "panel multiaxis verdict",
            "key_features_or_patterns_ko": "전압 변화형 안의 diode-like interpretation",
            "final_output_field_ko": "커널로그_원인군_ko",
            "coverage_level_ko": "직접커버",
            "note_ko": "conalog는 direct operational interpretation layer 이므로 current frozen output에 직접 부착됨",
        },
        {
            "target_fault_or_anomaly_ko": "conalog 개방/장치이상형",
            "detection_signal_or_pattern_ko": "conalog direct operational interpretation for open or device issue",
            "primary_layer_ko": "conalog 해석층",
            "supporting_layers_csv": "panel multiaxis verdict",
            "key_features_or_patterns_ko": "개방/장치이상 signature",
            "final_output_field_ko": "커널로그_원인군_ko",
            "coverage_level_ko": "직접커버",
            "note_ko": "conalog는 direct operational interpretation layer 이므로 current frozen output에 직접 부착됨",
        },
        {
            "target_fault_or_anomaly_ko": "conalog 모듈손상형",
            "detection_signal_or_pattern_ko": "conalog direct operational interpretation for module-damage-like pattern",
            "primary_layer_ko": "conalog 해석층",
            "supporting_layers_csv": "panel multiaxis verdict",
            "key_features_or_patterns_ko": "모듈손상 signature",
            "final_output_field_ko": "커널로그_원인군_ko",
            "coverage_level_ko": "직접커버",
            "note_ko": "conalog는 direct operational interpretation layer 이므로 current frozen output에 직접 부착됨",
        },
        {
            "target_fault_or_anomaly_ko": "GPVS reference attach",
            "detection_signal_or_pattern_ko": "external GPVS reference pattern attach and usage recommendation",
            "primary_layer_ko": "GPVS reference layer",
            "supporting_layers_csv": "panel multiaxis verdict,conalog 해석층",
            "key_features_or_patterns_ko": "reference-only attach, core/auxiliary recommendation, compatibility guard",
            "final_output_field_ko": "GPVS_최종사용권고_ko",
            "coverage_level_ko": "보조커버",
            "note_ko": f"GPVS evidence summary 기준 core_reference_count={gpvs_core}, auxiliary_reference_count={gpvs_aux} 이며 reference-only attach layer로만 사용함",
        },
        {
            "target_fault_or_anomaly_ko": "heuristic suspected-cause ranking",
            "detection_signal_or_pattern_ko": "triage-only suspected cause ranking and competition note",
            "primary_layer_ko": "cause candidate heuristic",
            "supporting_layers_csv": "panel multiaxis verdict,conalog 해석층,GPVS reference layer",
            "key_features_or_patterns_ko": "top1/top2/top3 ranking, competition state, field-trial action note",
            "final_output_field_ko": "1순위_의심원인_ko|2순위_의심원인_ko|3순위_의심원인_ko",
            "coverage_level_ko": "보조커버",
            "note_ko": f"cause candidate summary 기준 fault_panel_count={heuristic_support} 이며 triage-only suspected-cause narrowing layer로만 사용함",
        },
    ]
    return rows


def metric_rows(
    *,
    integrated_summary_row: pd.Series,
    evidence_summary_row: pd.Series,
    cause_summary_row: pd.Series,
    validation_report_df: pd.DataFrame,
    full_algorithm_f1_df: pd.DataFrame,
    critical_actionability_df: pd.DataFrame,
    gpvs_family_f1_df: pd.DataFrame,
    field_validation_df: pd.DataFrame,
    final_decision_pack_df: pd.DataFrame,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    full_operational = find_metric_row(
        full_algorithm_f1_df,
        filters={"truth_mode": "strict", "prediction_mode": "operational", "source_split": "overall"},
    )
    for metric_name, metric_col in [("precision", "precision"), ("recall", "recall"), ("f1", "f1")]:
        rows.append(
            {
                "layer_ko": "panel multiaxis verdict",
                "metric_family_ko": "공식 frozen classification",
                "metric_name": f"strict_operational_overall_{metric_name}",
                "metric_value": normalize_text(full_operational.get(metric_col, "")),
                "dataset_scope_ko": "full_algorithm_f1_summary_v3 / strict / operational / overall",
                "official_flag": 1 if full_operational else 0,
                "note_ko": (
                    f"current frozen artifact에서 직접 읽은 {metric_name} 이며 broader frozen algorithm scope 수치임. "
                    "25 panel / 6 fault explanatory sample로 일반화하면 안 됨"
                    if full_operational
                    else "panel multiaxis verdict의 공식 frozen classification artifact를 현재 builder 입력에서 특정하지 못해 metric_value를 비워 둠"
                ),
            }
        )

    final_pack_lookup = {
        normalize_text(row["eval_scope"]): {key: normalize_text(value) for key, value in row.items()}
        for row in final_decision_pack_df.to_dict(orient="records")
    }
    for scope, metric_name in [
        ("step3_precursor_performance", "precursor_current_best_f1"),
        ("step4_abrupt_no_precursor", "abrupt_current_best_f1"),
    ]:
        row = final_pack_lookup.get(scope, {})
        rows.append(
            {
                "layer_ko": "사건유형/고장양상 판단",
                "metric_family_ko": "공식 frozen scope-specific metric",
                "metric_name": metric_name,
                "metric_value": normalize_text(row.get("current_best_f1", "")),
                "dataset_scope_ko": f"panel_day_engine_project_final_decision_pack_v1 / {scope}",
                "official_flag": 1 if row else 0,
                "note_ko": (
                    f"current_best_target_name={normalize_text(row.get('current_best_target_name', ''))}, "
                    f"positive_support={normalize_text(row.get('current_best_positive_support', ''))}, "
                    f"final_usage_decision={normalize_text(row.get('final_usage_decision', ''))}"
                    if row
                    else "사건유형/고장양상 판단용 current_best_f1 scope row를 찾지 못해 metric_value를 비워 둠"
                ),
            }
        )

    critical_operational = find_metric_row(
        critical_actionability_df,
        filters={"truth_mode": "strict", "prediction_mode": "operational_review"},
    )
    validation_conalog = validation_report_df.loc[
        validation_report_df["case_type"].map(normalize_text).eq("core_conalog_family")
    ].copy()
    rows.append(
        {
            "layer_ko": "conalog 해석층",
            "metric_family_ko": "coverage/agreement",
            "metric_name": "core_conalog_family_validation_pass_count",
            "metric_value": str(int(validation_conalog["pass_flag"].astype(int).sum())) if not validation_conalog.empty else "",
            "dataset_scope_ko": "outputs/validation/fault_validation_report_v1.csv / core 6 fault snapshot",
            "official_flag": 0,
            "note_ko": "framework validation count 이며 measured field performance 전체셋으로 읽으면 안 됨",
        }
    )
    rows.append(
        {
            "layer_ko": "conalog 해석층",
            "metric_family_ko": "coverage/agreement",
            "metric_name": "field_reviewed_row_count",
            "metric_value": (
                normalize_text(
                    find_metric_row(field_validation_df, filters={"site": "overall"}).get("reviewed_row_count", "")
                )
                if not field_validation_df.empty
                else ""
            ),
            "dataset_scope_ko": "field_validation_summary.csv / overall",
            "official_flag": 1 if not field_validation_df.empty else 0,
            "note_ko": (
                "current field validation summary 기준 reviewed_row_count 이며 아직 reviewed truth가 없으면 0 으로 남음"
                if not field_validation_df.empty
                else "conalog field validation summary artifact가 없어 metric_value를 비워 둠"
            ),
        }
    )
    rows.append(
        {
            "layer_ko": "conalog 해석층",
            "metric_family_ko": "coverage/agreement",
            "metric_name": "strict_operational_review_f1_proxy",
            "metric_value": normalize_text(critical_operational.get("f1", "")),
            "dataset_scope_ko": "critical_actionability_f1_summary.csv / strict / operational_review",
            "official_flag": 1 if critical_operational else 0,
            "note_ko": (
                "current frozen critical actionability artifact 수치이며 conalog-centered operational review proxy로만 읽어야 함"
                if critical_operational
                else "conalog operational review proxy artifact를 현재 builder 입력에서 특정하지 못해 metric_value를 비워 둠"
            ),
        }
    )

    gpvs_overall = find_metric_row(
        gpvs_family_f1_df,
        filters={"evaluation_mode": "closed_world", "row_type": "overall"},
    )
    rows.append(
        {
            "layer_ko": "GPVS reference layer",
            "metric_family_ko": "attach coverage",
            "metric_name": "external_evidence_available_count",
            "metric_value": normalize_text(evidence_summary_row["external_evidence_available_count"]),
            "dataset_scope_ko": "panel_day_engine_gpvs_evidence_summary_v1.csv / current 6 fault sample",
            "official_flag": 1,
            "note_ko": "reference-only attach support count 임",
        }
    )
    rows.append(
        {
            "layer_ko": "GPVS reference layer",
            "metric_family_ko": "attach coverage",
            "metric_name": "core_reference_count",
            "metric_value": normalize_text(evidence_summary_row["core_reference_count"]),
            "dataset_scope_ko": "panel_day_engine_gpvs_evidence_summary_v1.csv / current 6 fault sample",
            "official_flag": 1,
            "note_ko": "reference-only core attach count 임",
        }
    )
    rows.append(
        {
            "layer_ko": "GPVS reference layer",
            "metric_family_ko": "attach coverage",
            "metric_name": "auxiliary_reference_count",
            "metric_value": normalize_text(evidence_summary_row["auxiliary_reference_count"]),
            "dataset_scope_ko": "panel_day_engine_gpvs_evidence_summary_v1.csv / current 6 fault sample",
            "official_flag": 1,
            "note_ko": "reference-only auxiliary attach count 임",
        }
    )
    rows.append(
        {
            "layer_ko": "GPVS reference layer",
            "metric_family_ko": "family-eval artifact",
            "metric_name": "closed_world_macro_f1",
            "metric_value": normalize_text(gpvs_overall.get("macro_f1", "")),
            "dataset_scope_ko": "gpvs_fault_family_f1_summary.csv / closed_world / overall",
            "official_flag": 1 if gpvs_overall else 0,
            "note_ko": (
                "GPVS original family-eval artifact 수치이며 current panel multiaxis verdict의 direct root-cause metric으로 읽으면 안 됨"
                if gpvs_overall
                else "GPVS family evaluation artifact row를 찾지 못해 metric_value를 비워 둠"
            ),
        }
    )

    heuristic_action = validation_report_df.loc[
        validation_report_df["case_type"].map(normalize_text).eq("core_heuristic_action_note")
    ].copy()
    rows.append(
        {
            "layer_ko": "cause candidate heuristic",
            "metric_family_ko": "triage support",
            "metric_name": "fault_panel_support_count",
            "metric_value": normalize_text(cause_summary_row["fault_panel_count"]),
            "dataset_scope_ko": "panel_day_engine_cause_candidate_summary_v1.csv / current 6 fault sample",
            "official_flag": 1,
            "note_ko": "triage-only candidate ranking support count 임",
        }
    )
    rows.append(
        {
            "layer_ko": "cause candidate heuristic",
            "metric_family_ko": "triage support",
            "metric_name": "core_heuristic_action_note_pass_count",
            "metric_value": str(int(heuristic_action["pass_flag"].astype(int).sum())) if not heuristic_action.empty else "",
            "dataset_scope_ko": "outputs/validation/fault_validation_report_v1.csv / core 6 fault snapshot",
            "official_flag": 0,
            "note_ko": "framework validation support count 이며 ranking ground-truth metric은 아님",
        }
    )
    rows.append(
        {
            "layer_ko": "cause candidate heuristic",
            "metric_family_ko": "ranking metric",
            "metric_name": "official_ranking_metric_unavailable",
            "metric_value": "",
            "dataset_scope_ko": "current frozen artifacts",
            "official_flag": 0,
            "note_ko": "heuristic은 triage-only layer라 current frozen artifacts에는 official ranking metric이 없음. validation support count와 competition count로만 해석해야 함",
        }
    )
    return rows


def build_doc_text(
    *,
    integrated_summary_row: pd.Series,
    evidence_summary_row: pd.Series,
    cause_summary_row: pd.Series,
    metrics_df: pd.DataFrame,
) -> str:
    total_panels = normalize_text(integrated_summary_row["total_panel_count"])
    fault_panels = normalize_text(integrated_summary_row["fault_panel_count"])
    gpvs_core = normalize_text(integrated_summary_row["gpvs_core_reference_count"])
    gpvs_aux = normalize_text(integrated_summary_row["gpvs_auxiliary_reference_count"])
    heuristic_unique = normalize_text(cause_summary_row["unique_top1_candidate_count"])
    lines = [
        "# OPS Fault Coverage And Model Performance V1",
        "",
        "## 1. 보고 목적",
        "- 본 문서는 current frozen panel day engine stack이 어떤 fault/anomaly target을 직접 다루고 어떤 target을 보조적으로만 다루는지 concise하게 정리한 coverage/performance 보고서임.",
        "- panel multiaxis verdict가 primary 임. conalog는 direct operational interpretation layer 임. GPVS는 reference-only 임. cause candidate heuristic은 triage-only 임.",
        "- 25 panel / 6 fault sample은 설명용 current frozen sample이며 전체 공식 대표셋으로 일반화하면 안 됨.",
        "",
        "## 2. 현재 알고리즘 스택",
        "- panel multiaxis verdict가 최종 primary 판정층임.",
        "- 사건유형/고장양상 판단은 event type과 terminal pattern을 분리하여 frozen output에 직접 반영함.",
        "- conalog 해석층은 direct operational interpretation layer로서 conalog 원인군을 직접 부착함.",
        f"- GPVS reference layer는 current frozen sample 기준 core_reference_count={gpvs_core}, auxiliary_reference_count={gpvs_aux} 로만 사용하며 direct root-cause classifier가 아님.",
        f"- cause candidate heuristic은 current frozen 6 fault sample 기준 unique_top1_candidate_count={heuristic_unique} 의 triage-only suspected-cause ranking 층임.",
        "",
        "## 3. 입력 데이터와 학습/참조 자산",
        "- panel multiaxis verdict, GPVS evidence pack, cause candidate heuristic summary를 현재 frozen front-facing stack의 직접 입력 자산으로 사용하였음.",
        "- recovered GPVS by-type artifact와 GPVS evidence pack은 reference attach provenance와 usage rule 설명에 사용하였음.",
        "- outputs/validation/fault_validation_report_v1.csv 는 current framework validation support count를 보조적으로 인용하였음.",
        "- full_algorithm_f1_summary_v3.csv, critical_actionability_f1_summary.csv, gpvs_fault_family_f1_summary.csv, panel_day_engine_project_final_decision_pack_v1.csv 를 current frozen metric artifact로 사용하였음.",
        "",
        "## 4. fault/anomaly 커버리지 1대1 매핑",
        "- 패널고장여부, 사건유형, 최종고장양상, conalog 원인군은 직접커버 target 임.",
        "- GPVS reference attach와 heuristic suspected-cause ranking은 보조커버 target 임.",
        "- GPVS는 reference-only layer이므로 physical root-cause 1대1 classifier로 읽으면 안 됨.",
        "",
        "## 5. 레이어별 성능지표 원칙",
        "- panel multiaxis verdict와 사건유형/고장양상 판단은 공식 frozen artifact가 있을 때에만 F1/Precision/Recall을 사용함.",
        "- conalog 해석층은 coverage/agreement 스타일 지표를 우선 사용함.",
        "- GPVS reference layer는 attach coverage, support count, reference-only policy 지표를 사용함.",
        "- cause candidate heuristic은 triage-only layer이므로 ranking ground truth가 없으면 support count와 validation support count만 사용하고 과장된 ranking metric을 만들지 않음.",
        "",
        "## 6. 현재 확보된 지표와 해석",
        f"- current frozen verdict/evidence derived summary 기준 total_panel_count={total_panels}, fault_panel_count={fault_panels} 임.",
        "- full_algorithm_f1_summary_v3 에는 strict/operational overall precision, recall, f1 이 존재하였음. 다만 broader frozen algorithm scope 수치이므로 25 panel / 6 fault 설명용 sample과 동일시하면 안 됨.",
        "- panel_day_engine_project_final_decision_pack_v1 에는 step3 precursor performance 와 step4 abrupt no-precursor scope의 current_best_f1 이 존재하였음. 다만 support가 작고 final_usage_decision이 exploratory_only 로 표시된 scope임.",
        "- GPVS evidence summary 에는 external evidence available count, core reference count, auxiliary reference count가 존재하였음. 이는 reference-only support metric 임.",
        "- cause candidate summary 와 validation framework 는 triage-only heuristic의 support count와 action-note alignment support count만 제공하며 official ranking metric은 제공하지 않음.",
        "",
        "## 7. 현재 한계와 주의사항",
        "- current frozen sample 25 panel / 6 fault는 설명용 current snapshot 이며 전체 성능 대표셋으로 일반화하면 안 됨.",
        "- GPVS는 reference-only layer 이므로 attach count나 family-eval artifact를 direct root-cause classifier 성능처럼 읽으면 안 됨.",
        "- cause candidate heuristic은 triage-only layer 이므로 suspected-cause narrowing 과 competition guidance 용도로만 읽어야 하며 final diagnosis로 사용하면 안 됨.",
        "- 본 문서는 report/build layer only 단계이며 detector logic이나 frozen front-facing output meaning을 다시 정의하지 않았음.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    share_dir = root / "_share"

    verdict_df = read_csv(share_dir / VERDICT_NAME)
    evidence_summary_df = read_csv(share_dir / EVIDENCE_SUMMARY_NAME)
    cause_summary_df = read_csv(share_dir / CAUSE_SUMMARY_NAME)
    final_decision_pack_df = read_optional_csv(share_dir / FINAL_DECISION_PACK_NAME)
    full_algorithm_f1_df = read_optional_csv(share_dir / FULL_ALGORITHM_F1_NAME)
    critical_actionability_df = read_optional_csv(share_dir / CRITICAL_ACTIONABILITY_F1_NAME)
    gpvs_family_f1_df = read_optional_csv(share_dir / GPVS_FAMILY_F1_NAME)
    field_validation_df = read_optional_csv(share_dir / FIELD_VALIDATION_SUMMARY_NAME)
    validation_report_df = ensure_validation_report(root)

    ensure_columns(verdict_df, VERDICT_REQUIRED_COLS, VERDICT_NAME)
    ensure_columns(evidence_summary_df, EVIDENCE_SUMMARY_REQUIRED_COLS, EVIDENCE_SUMMARY_NAME)
    ensure_columns(cause_summary_df, CAUSE_SUMMARY_REQUIRED_COLS, CAUSE_SUMMARY_NAME)
    if not final_decision_pack_df.empty:
        ensure_columns(
            final_decision_pack_df,
            [
                "eval_scope",
                "current_best_target_name",
                "current_best_f1",
                "current_best_positive_support",
                "final_usage_decision",
            ],
            FINAL_DECISION_PACK_NAME,
        )

    evidence_summary_row = first_row(evidence_summary_df, EVIDENCE_SUMMARY_NAME)
    cause_summary_row = first_row(cause_summary_df, CAUSE_SUMMARY_NAME)
    integrated_summary_row = build_stack_summary_row(verdict_df, evidence_summary_row)

    coverage_df = pd.DataFrame(
        coverage_rows(integrated_summary_row, evidence_summary_row, cause_summary_row)
    ).reindex(columns=COVERAGE_COLS)
    metrics_df = pd.DataFrame(
        metric_rows(
            integrated_summary_row=integrated_summary_row,
            evidence_summary_row=evidence_summary_row,
            cause_summary_row=cause_summary_row,
            validation_report_df=validation_report_df,
            full_algorithm_f1_df=full_algorithm_f1_df,
            critical_actionability_df=critical_actionability_df,
            gpvs_family_f1_df=gpvs_family_f1_df,
            field_validation_df=field_validation_df,
            final_decision_pack_df=final_decision_pack_df,
        )
    ).reindex(columns=METRIC_COLS)

    coverage_path = share_dir / OUTPUT_COVERAGE_NAME
    metrics_path = share_dir / OUTPUT_METRICS_NAME
    coverage_df.to_csv(coverage_path, index=False, encoding="utf-8-sig")
    metrics_df.to_csv(metrics_path, index=False, encoding="utf-8-sig")

    doc_path = root / "docs/OPS_FAULT_COVERAGE_AND_MODEL_PERFORMANCE_V1.md"
    doc_path.write_text(
        build_doc_text(
            integrated_summary_row=integrated_summary_row,
            evidence_summary_row=evidence_summary_row,
            cause_summary_row=cause_summary_row,
            metrics_df=metrics_df,
        ),
        encoding="utf-8",
    )

    print(f"[OK] wrote {coverage_path}")
    print(f"[OK] wrote {metrics_path}")
    print(f"[OK] wrote {doc_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
