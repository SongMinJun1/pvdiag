#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


TARGET_PANELS = [
    "45dfa600-79b7-428e-95d3-22345a068986.1.1",
    "d15b9e13-4117-49ae-a78f-7ace013e48de.0.0",
    "45dfa600-79b7-428e-95d3-22345a068986.1.0",
    "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.9",
]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert_true(spec is not None and spec.loader is not None, f"failed to load module: {path.name}")
    spec.loader.exec_module(module)
    return module


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
        share / "panel_day_engine_project_eval_matrix_v1.csv",
        [
            {
                "eval_scope": "step3_precursor_performance",
                "eval_part_name": "precursor_bearing_marker_performance",
                "metric_kind": "true_case_metric",
                "unit_type": "case",
                "positive_set_name": "precursor_bearing_detectable_now",
                "negative_set_name": "others",
                "target_name": "first_signalcount2",
                "support_positive": 2,
                "support_negative": 8,
                "tp": 2,
                "fp": 0,
                "fn": 0,
                "tn": 8,
                "recall": 1.0,
                "precision": 1.0,
                "f1": 1.0,
                "note_ko": "step3 synthetic",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "eval_part_name": "abrupt_no_precursor_performance",
                "metric_kind": "true_case_metric",
                "unit_type": "case",
                "positive_set_name": "abrupt",
                "negative_set_name": "others",
                "target_name": "final_fault_hit_by_anchor",
                "support_positive": 6,
                "support_negative": 6,
                "tp": 5,
                "fp": 1,
                "fn": 1,
                "tn": 5,
                "recall": 0.8333333333333334,
                "precision": 0.8333333333333334,
                "f1": 0.8333333333333334,
                "note_ko": "step4 abrupt synthetic",
            },
            {
                "eval_scope": "step4_common_cause_routing",
                "eval_part_name": "common_cause_routing_performance",
                "metric_kind": "true_case_metric",
                "unit_type": "case",
                "positive_set_name": "common_cause",
                "negative_set_name": "others",
                "target_name": "breadth_marker_only",
                "support_positive": 4,
                "support_negative": 8,
                "tp": 4,
                "fp": 0,
                "fn": 0,
                "tn": 8,
                "recall": 1.0,
                "precision": 1.0,
                "f1": 1.0,
                "note_ko": "common-cause synthetic",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "eval_part_name": "operator_workflow_policy_proxy",
                "metric_kind": "retrospective_proxy_metric",
                "unit_type": "panel",
                "positive_set_name": "proxy_positive",
                "negative_set_name": "proxy_negative",
                "target_name": "baseline_plus_discovery_cluster",
                "support_positive": 11,
                "support_negative": 19,
                "tp": 11,
                "fp": 19,
                "fn": 0,
                "tn": 0,
                "recall": 1.0,
                "precision": 0.3666666666666666,
                "f1": 0.5365853658536585,
                "note_ko": "workflow proxy synthetic",
            },
        ],
        [
            "eval_scope",
            "eval_part_name",
            "metric_kind",
            "unit_type",
            "positive_set_name",
            "negative_set_name",
            "target_name",
            "support_positive",
            "support_negative",
            "tp",
            "fp",
            "fn",
            "tn",
            "recall",
            "precision",
            "f1",
            "note_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_project_current_data_freeze_pack_v1.csv",
        [
            {
                "eval_scope": "step3_precursor_performance",
                "current_best_target_name": "first_signalcount2",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 1.0,
                "current_best_positive_support": 2,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "do_not_freeze",
                "acquisition_blocked_flag": 1,
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "next_allowed_action": "do_not_upgrade_without_new_truth",
                "freeze_reason_ko": "step3 exploratory",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "current_best_target_name": "final_fault_hit_by_anchor",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 0.8333333333333334,
                "current_best_positive_support": 6,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "freeze_with_caution",
                "acquisition_blocked_flag": 1,
                "current_data_decision": "freeze_with_caution",
                "allowed_claim_strength": "bounded_current_data_claim",
                "next_allowed_action": "keep_with_caution_note",
                "freeze_reason_ko": "step4 abrupt caution",
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
                "current_operational_workflow_reason_ko": "recommended workflow",
                "freeze_recommendation": "freeze_with_caution",
                "acquisition_blocked_flag": 0,
                "current_data_decision": "workflow_proxy_only",
                "allowed_claim_strength": "workflow_claim_only",
                "next_allowed_action": "operator_workflow_only",
                "freeze_reason_ko": "operator workflow only",
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
        share / "panel_day_engine_project_current_data_claims_v1.csv",
        [
            {
                "claim_id": "claim_step3",
                "claim_scope": "step3_precursor_performance",
                "claim_text_ko": "step3 precursor marker 결과는 exploratory result 로만 사용한다.",
                "claim_strength": "exploratory_claim_only",
                "prohibited_overclaim_ko": "step3 stable detector claim 금지",
            },
            {
                "claim_id": "claim_step4_abrupt",
                "claim_scope": "step4_abrupt_no_precursor",
                "claim_text_ko": "step4 abrupt 결과는 caution 과 함께 bounded current-data conclusion 으로만 유지한다.",
                "claim_strength": "bounded_current_data_claim",
                "prohibited_overclaim_ko": "step4 abrupt overclaim 금지",
            },
            {
                "claim_id": "claim_step4_common",
                "claim_scope": "step4_common_cause_routing",
                "claim_text_ko": "step4 common-cause routing 은 descriptive / exploratory 수준으로만 유지한다.",
                "claim_strength": "exploratory_claim_only",
                "prohibited_overclaim_ko": "common-cause operational classifier claim 금지",
            },
            {
                "claim_id": "claim_operator",
                "claim_scope": "operator_policy_proxy",
                "claim_text_ko": "operator workflow 는 workflow proxy claim 으로만 사용한다.",
                "claim_strength": "workflow_claim_only",
                "prohibited_overclaim_ko": "workflow packaging을 detector generalization 으로 바꾸지 말 것",
            },
        ],
        [
            "claim_id",
            "claim_scope",
            "claim_text_ko",
            "claim_strength",
            "prohibited_overclaim_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_precursor_onset_summary_v1.csv",
        [
            {
                "summary_type": "onset_marker",
                "marker_name": "first_signalcount2",
                "distribution_value": "",
                "case_count": 2,
                "available_case_count": 2,
                "available_rate": 1.0,
                "median_lead_days": 11.5,
                "min_lead_days": 6.0,
                "max_lead_days": 17.0,
            }
        ],
        [
            "summary_type",
            "marker_name",
            "distribution_value",
            "case_count",
            "available_case_count",
            "available_rate",
            "median_lead_days",
            "min_lead_days",
            "max_lead_days",
        ],
    )

    write_csv(
        share / "panel_day_engine_precursor_performance_summary_v1.csv",
        [
            {
                "marker_name": "first_signalcount2",
                "case_count": 2,
                "available_case_count": 2,
                "available_rate": 1.0,
                "median_lead_days": 11.5,
                "min_lead_days": 6.0,
                "max_lead_days": 17.0,
                "median_onset_capture_gap_days": 0.5,
                "exact_or_earlier_count": 1,
                "within_3d_late_count": 1,
                "within_7d_late_count": 0,
                "late_over_7d_count": 0,
                "missing_count": 0,
                "exact_or_earlier_rate": 0.5,
                "exact_or_earlier_plus_within_3d_rate": 1.0,
            }
        ],
        [
            "marker_name",
            "case_count",
            "available_case_count",
            "available_rate",
            "median_lead_days",
            "min_lead_days",
            "max_lead_days",
            "median_onset_capture_gap_days",
            "exact_or_earlier_count",
            "within_3d_late_count",
            "within_7d_late_count",
            "late_over_7d_count",
            "missing_count",
            "exact_or_earlier_rate",
            "exact_or_earlier_plus_within_3d_rate",
        ],
    )

    write_csv(
        share / "panel_day_engine_non_precursor_performance_summary_v1.csv",
        [
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "case_count": 6,
                "final_fault_hit_by_anchor_rate": 0.8333333333333334,
                "final_fault_hit_within_3d_after_rate": 0.0,
                "final_fault_hit_within_7d_after_rate": 0.0,
                "confirmed_fault_hit_within_7d_after_rate": 0.0,
                "critical_fault_hit_within_7d_after_rate": 0.0,
                "common_cause_like_rate": "",
                "group_off_like_rate": "",
                "shadow_like_rate": "",
                "local_precursor_alert_contamination_rate": "",
                "final_fault_rate": "",
                "note_ko": "abrupt summary synthetic",
            }
        ],
        [
            "eval_bucket_v2",
            "case_count",
            "final_fault_hit_by_anchor_rate",
            "final_fault_hit_within_3d_after_rate",
            "final_fault_hit_within_7d_after_rate",
            "confirmed_fault_hit_within_7d_after_rate",
            "critical_fault_hit_within_7d_after_rate",
            "common_cause_like_rate",
            "group_off_like_rate",
            "shadow_like_rate",
            "local_precursor_alert_contamination_rate",
            "final_fault_rate",
            "note_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_operator_attention_policy_recommendation_v1.csv",
        [
            {
                "recommended_policy_name": "baseline_plus_discovery_cluster",
                "recommended_policy_reason_ko": "recommended for operator workflow",
                "expected_use_ko": "queue/watch baseline에 discovery cluster를 붙인 기본 operator workflow",
                "caution_ko": "cluster view는 panel drill-down을 압축한다.",
            }
        ],
        [
            "recommended_policy_name",
            "recommended_policy_reason_ko",
            "expected_use_ko",
            "caution_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_operator_pipeline_manifest_v1.csv",
        [
            {
                "final_pipeline_pass_flag": 1,
                "note_ko": "pipeline pass",
            }
        ],
        [
            "final_pipeline_pass_flag",
            "note_ko",
        ],
    )

    write_csv(
        share / "panel_date_reaudit_working.csv",
        [
            {
                "site": "sitea",
                "panel_id": "45dfa600-79b7-428e-95d3-22345a068986.1.0",
                "strict_trigger_date": "2025-01-12",
                "first_warning_date": "2025-01-01",
                "retrospective_onset_date": "2025-01-10",
                "days_earlier_than_trigger": 2,
                "onset_confidence": "medium",
                "onset_method": "synthetic",
                "reason_summary": "synthetic re-audit",
                "vendor_reply_class": "vendor_rejected",
                "vendor_fault_family": "none_visible",
                "field_confirmed_flag": 0,
                "dispute_type": "ours_positive_vendor_rejected",
                "vendor_note": "none",
                "review_priority": "P1",
                "reaudited_earliest_visible_date": "",
                "reaudited_first_warning_date": "",
                "field_estimated_start_date": "",
                "date_judgement": "",
                "failure_mode_judgement": "",
                "candidate_validity": "false_positive",
                "review_confidence": "",
                "note": "assistant_seed: monitor_only",
            }
        ],
        [
            "site",
            "panel_id",
            "strict_trigger_date",
            "first_warning_date",
            "retrospective_onset_date",
            "days_earlier_than_trigger",
            "onset_confidence",
            "onset_method",
            "reason_summary",
            "vendor_reply_class",
            "vendor_fault_family",
            "field_confirmed_flag",
            "dispute_type",
            "vendor_note",
            "review_priority",
            "reaudited_earliest_visible_date",
            "reaudited_first_warning_date",
            "field_estimated_start_date",
            "date_judgement",
            "failure_mode_judgement",
            "candidate_validity",
            "review_confidence",
            "note",
        ],
    )

    write_csv(
        share / "panel_day_engine_local_seed_carry_fate_cases_v1.csv",
        [
            {
                "site": "sitea",
                "panel_id": "45dfa600-79b7-428e-95d3-22345a068986.1.0",
                "run_start_date": "2025-01-01",
                "run_end_date": "2025-01-20",
                "run_day_count": 20,
                "run_shape_class": "chronic_alert_run",
                "delta_run_class": "extended_run",
                "evidence_reason_ko": "synthetic recurring",
                "future_confirmed_fault_7d": 0,
                "future_critical_fault_7d": 0,
                "future_final_fault_7d": 0,
                "future_confirmed_fault_30d": 0,
                "future_critical_fault_30d": 0,
                "future_final_fault_30d": 0,
                "future_confirmed_fault_60d": 0,
                "future_critical_fault_60d": 0,
                "future_final_fault_60d": 0,
                "future_truth_overlap_30d": 0,
                "future_truth_overlap_60d": 0,
                "future_truth_candidate_validities": "",
                "future_truth_case_ids": "",
                "recurring_run_within_30d": 1,
                "recurring_run_within_60d": 1,
                "future_run_count_60d": 2,
                "fate_class": "recurring_chronic_monitor_like",
                "fate_reason_ko": "synthetic recurring monitor",
            }
        ],
        [
            "site",
            "panel_id",
            "run_start_date",
            "run_end_date",
            "run_day_count",
            "run_shape_class",
            "delta_run_class",
            "evidence_reason_ko",
            "future_confirmed_fault_7d",
            "future_critical_fault_7d",
            "future_final_fault_7d",
            "future_confirmed_fault_30d",
            "future_critical_fault_30d",
            "future_final_fault_30d",
            "future_confirmed_fault_60d",
            "future_critical_fault_60d",
            "future_final_fault_60d",
            "future_truth_overlap_30d",
            "future_truth_overlap_60d",
            "future_truth_candidate_validities",
            "future_truth_case_ids",
            "recurring_run_within_30d",
            "recurring_run_within_60d",
            "future_run_count_60d",
            "fate_class",
            "fate_reason_ko",
        ],
    )

    sitea_out = root / "data/sitea/out"
    sitea_out.mkdir(parents=True, exist_ok=True)

    gate_rows = []
    core_rows = []
    diag_rows = []
    all_dates = pd.date_range("2025-01-01", periods=6, freq="D")

    for date in all_dates:
        date_str = date.strftime("%Y-%m-%d")
        gate_rows.extend(
            [
                {
                    "site": "sitea",
                    "panel_id": "45dfa600-79b7-428e-95d3-22345a068986.1.1",
                    "date": date_str,
                    "data_bad": False,
                    "cond_var": date_str in {"2025-01-02", "2025-01-03"},
                    "cond_evt": False,
                    "cond_dtw": date_str in {"2025-01-02"},
                    "cond_hs": False,
                    "pre_ews": False,
                    "signal_count": 1,
                    "ews_runlen": 0,
                    "ews_warning": False,
                    "site_event_soft": False,
                    "site_event_hard": False,
                    "group_off_date": False,
                    "prefault_B": False,
                    "pre_alarm": False,
                    "prefault_cond_mid": False,
                    "prefault_cond_ae": False,
                    "prefault_cond_dtw": False,
                    "prefault_cond_ews": False,
                    "prealarm_cond_ae_mid_or_hi": False,
                    "prealarm_cond_dtw_mid_or_hi": False,
                    "prealarm_cond_hs_mid_or_hi": False,
                },
                {
                    "site": "sitea",
                    "panel_id": "45dfa600-79b7-428e-95d3-22345a068986.1.0",
                    "date": date_str,
                    "data_bad": False,
                    "cond_var": date_str in {"2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"},
                    "cond_evt": date_str in {"2025-01-02", "2025-01-03"},
                    "cond_dtw": date_str in {"2025-01-01", "2025-01-02", "2025-01-03"},
                    "cond_hs": date_str in {"2025-01-02"},
                    "pre_ews": True,
                    "signal_count": 3,
                    "ews_runlen": 4,
                    "ews_warning": True,
                    "site_event_soft": False,
                    "site_event_hard": False,
                    "group_off_date": False,
                    "prefault_B": False,
                    "pre_alarm": date_str in {"2025-01-02", "2025-01-03", "2025-01-04"},
                    "prefault_cond_mid": True,
                    "prefault_cond_ae": True,
                    "prefault_cond_dtw": True,
                    "prefault_cond_ews": True,
                    "prealarm_cond_ae_mid_or_hi": True,
                    "prealarm_cond_dtw_mid_or_hi": True,
                    "prealarm_cond_hs_mid_or_hi": False,
                },
                {
                    "site": "sitea",
                    "panel_id": "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.9",
                    "date": date_str,
                    "data_bad": False,
                    "cond_var": date_str in {"2025-01-03", "2025-01-04"},
                    "cond_evt": date_str in {"2025-01-03", "2025-01-04"},
                    "cond_dtw": date_str in {"2025-01-03"},
                    "cond_hs": False,
                    "pre_ews": True,
                    "signal_count": 2,
                    "ews_runlen": 2,
                    "ews_warning": True,
                    "site_event_soft": False,
                    "site_event_hard": False,
                    "group_off_date": False,
                    "prefault_B": False,
                    "pre_alarm": date_str in {"2025-01-03", "2025-01-04"},
                    "prefault_cond_mid": True,
                    "prefault_cond_ae": False,
                    "prefault_cond_dtw": False,
                    "prefault_cond_ews": True,
                    "prealarm_cond_ae_mid_or_hi": False,
                    "prealarm_cond_dtw_mid_or_hi": False,
                    "prealarm_cond_hs_mid_or_hi": False,
                },
            ]
        )
        core_rows.extend(
            [
                {
                    "date": date_str,
                    "panel_id": "45dfa600-79b7-428e-95d3-22345a068986.1.1",
                    "recon_error": 0.01,
                    "mid_ratio": 0.95,
                    "mid_v_ratio": 0.96,
                    "v_drop": 0.03,
                    "final_fault": False,
                    "ae_strength": "mid",
                    "anom_subtype": "normal",
                },
                {
                    "date": date_str,
                    "panel_id": "45dfa600-79b7-428e-95d3-22345a068986.1.0",
                    "recon_error": 0.09 if date_str in {"2025-01-03", "2025-01-04"} else 0.04,
                    "mid_ratio": 0.55 if date_str in {"2025-01-03", "2025-01-04"} else 0.9,
                    "mid_v_ratio": 0.45 if date_str in {"2025-01-03", "2025-01-04"} else 0.95,
                    "v_drop": 0.4 if date_str in {"2025-01-03", "2025-01-04"} else 0.05,
                    "final_fault": date_str in {"2025-01-03", "2025-01-04"},
                    "ae_strength": "high",
                    "anom_subtype": "normal",
                },
                {
                    "date": date_str,
                    "panel_id": "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.9",
                    "recon_error": 0.025,
                    "mid_ratio": 0.83,
                    "mid_v_ratio": 0.84,
                    "v_drop": 0.2,
                    "final_fault": False,
                    "ae_strength": "mid",
                    "anom_subtype": "normal",
                },
                {
                    "date": date_str,
                    "panel_id": f"site_context_panel_{date_str}",
                    "recon_error": 0.02,
                    "mid_ratio": 0.9,
                    "mid_v_ratio": 0.9,
                    "v_drop": 0.1,
                    "final_fault": date_str in {"2025-01-03", "2025-01-04"},
                    "ae_strength": "low",
                    "anom_subtype": "normal",
                },
            ]
        )

    for extra_idx in range(1, 10):
        gate_rows.append(
            {
                "site": "sitea",
                "panel_id": f"context_pre_{extra_idx}",
                "date": "2025-01-03",
                "data_bad": False,
                "cond_var": False,
                "cond_evt": False,
                "cond_dtw": False,
                "cond_hs": False,
                "pre_ews": False,
                "signal_count": 0,
                "ews_runlen": 0,
                "ews_warning": False,
                "site_event_soft": False,
                "site_event_hard": False,
                "group_off_date": False,
                "prefault_B": False,
                "pre_alarm": True,
                "prefault_cond_mid": False,
                "prefault_cond_ae": False,
                "prefault_cond_dtw": False,
                "prefault_cond_ews": False,
                "prealarm_cond_ae_mid_or_hi": False,
                "prealarm_cond_dtw_mid_or_hi": False,
                "prealarm_cond_hs_mid_or_hi": False,
            }
        )

    write_csv(
        sitea_out / "ae_simple_local_precursor_gate_daily.csv",
        gate_rows,
        [
            "site",
            "panel_id",
            "date",
            "data_bad",
            "cond_var",
            "cond_evt",
            "cond_dtw",
            "cond_hs",
            "pre_ews",
            "signal_count",
            "ews_runlen",
            "ews_warning",
            "site_event_soft",
            "site_event_hard",
            "group_off_date",
            "prefault_B",
            "pre_alarm",
            "prefault_cond_mid",
            "prefault_cond_ae",
            "prefault_cond_dtw",
            "prefault_cond_ews",
            "prealarm_cond_ae_mid_or_hi",
            "prealarm_cond_dtw_mid_or_hi",
            "prealarm_cond_hs_mid_or_hi",
        ],
    )
    write_csv(
        sitea_out / "panel_day_core.csv",
        core_rows,
        [
            "date",
            "panel_id",
            "recon_error",
            "mid_ratio",
            "mid_v_ratio",
            "v_drop",
            "final_fault",
            "ae_strength",
            "anom_subtype",
        ],
    )
    write_csv(
        sitea_out / "panel_diagnosis_summary.csv",
        [
            {
                "panel_id": "45dfa600-79b7-428e-95d3-22345a068986.1.0",
                "dead_diag_date": "",
                "critical_diag_date": "2025-01-04",
                "diagnosis_date_online": "2025-01-04",
                "final_fault_first_date": "2025-01-03",
                "dead_days": 0,
                "critical_days": 2,
                "tuning_level": "p2",
            }
        ],
        [
            "panel_id",
            "dead_diag_date",
            "critical_diag_date",
            "diagnosis_date_online",
            "final_fault_first_date",
            "dead_days",
            "critical_days",
            "tuning_level",
        ],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder_path = repo_root / "research/prognostics/build_panel_day_engine_internal_share_case_and_metrics_v1.py"
    smoke_path = Path(__file__).resolve()
    load_module(builder_path, "internal_share_case_and_metrics_builder")

    py_compile.compile(str(builder_path), doraise=True)
    py_compile.compile(str(smoke_path), doraise=True)

    official_outputs = [
        repo_root / "_share/panel_day_engine_ae_dtw_case_review_v1.csv",
        repo_root / "_share/panel_day_engine_latest_perf_internal_share_v1.csv",
        repo_root / "_share/panel_day_engine_internal_share_brief_v1.md",
    ]
    before_digests = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="internal_share_case_and_metrics_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture(tmp_root)

        result = run([sys.executable, str(builder_path), "--root", str(tmp_root)], cwd=repo_root)
        assert_true(result.returncode == 0, f"builder failed: {result.stderr or result.stdout}")

        case_review_df = pd.read_csv(
            tmp_root / "_share/panel_day_engine_ae_dtw_case_review_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )
        latest_perf_df = pd.read_csv(
            tmp_root / "_share/panel_day_engine_latest_perf_internal_share_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )
        brief_path = tmp_root / "_share/panel_day_engine_internal_share_brief_v1.md"
        brief_text = brief_path.read_text(encoding="utf-8")

        hidden_row = case_review_df.loc[
            case_review_df["panel_id"].eq("45dfa600-79b7-428e-95d3-22345a068986.1.1")
        ].iloc[0]
        visible_row = case_review_df.loc[
            case_review_df["panel_id"].eq("45dfa600-79b7-428e-95d3-22345a068986.1.0")
        ].iloc[0]
        missing_row = case_review_df.loc[
            case_review_df["panel_id"].eq("d15b9e13-4117-49ae-a78f-7ace013e48de.0.0")
        ].iloc[0]

        assert_true(int(hidden_row["found_flag"]) == 1, "hidden target should be found")
        assert_true(hidden_row["무가시형_판정"] == "무가시형_가능성_높음", "hidden heuristic should assign hidden-high")
        assert_true(int(visible_row["found_flag"]) == 1, "visible target should be found")
        assert_true(visible_row["무가시형_판정"] == "가시형_가능성_있음", "visible heuristic should assign visible-like")
        assert_true(int(missing_row["found_flag"]) == 0, "missing target should keep found_flag=0")
        assert_true(missing_row["무가시형_판정"] == "패널미발견", "missing target should mark panel not found")

        assert_true(set(latest_perf_df["구분"]) == {"전조형 고장", "급작 고장", "common-cause routing", "운영 workflow"}, "latest perf rows mismatch")
        assert_true("## 1. AE/DTW 사례 요약" in brief_text, "brief section 1 missing")
        assert_true("## 2. 최신 성능 한 줄 요약" in brief_text, "brief section 2 missing")
        assert_true("## 3. 지금 당장 말해도 되는 것 / 말하면 안 되는 것" in brief_text, "brief section 3 missing")

    after_digests = {path: file_digest(path) for path in official_outputs}
    assert_true(before_digests == after_digests, "smoke test modified official outputs")

    print("smoke_test_panel_day_engine_internal_share_case_and_metrics_v1.py: PASS")


if __name__ == "__main__":
    main()
