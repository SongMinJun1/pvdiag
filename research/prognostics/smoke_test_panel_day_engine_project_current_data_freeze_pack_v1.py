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

    reliability_rows = [
        {
            "eval_scope": "step1_taxonomy",
            "target_name": "unknown_needs_review",
            "metric_kind": "structural_coverage_metric",
            "positive_support": 3,
            "negative_support": "",
            "predicted_positive_support": "",
            "recall": "",
            "precision": "",
            "f1": "",
            "recall_ci_low": "",
            "recall_ci_high": "",
            "precision_ci_low": "",
            "precision_ci_high": "",
            "reliability_class": "structural_only",
            "freeze_recommendation": "freeze_with_caution",
            "reliability_reason_ko": "structural step1",
        },
        {
            "eval_scope": "step1_taxonomy",
            "target_name": "abrupt_or_no_precursor_now",
            "metric_kind": "structural_coverage_metric",
            "positive_support": 2,
            "negative_support": "",
            "predicted_positive_support": "",
            "recall": "",
            "precision": "",
            "f1": "",
            "recall_ci_low": "",
            "recall_ci_high": "",
            "precision_ci_low": "",
            "precision_ci_high": "",
            "reliability_class": "structural_only",
            "freeze_recommendation": "freeze_with_caution",
            "reliability_reason_ko": "structural step1",
        },
        {
            "eval_scope": "step2_onset_truth",
            "target_name": "first_cond_evt",
            "metric_kind": "structural_coverage_metric",
            "positive_support": 2,
            "negative_support": "",
            "predicted_positive_support": "",
            "recall": "",
            "precision": "",
            "f1": "",
            "recall_ci_low": "",
            "recall_ci_high": "",
            "precision_ci_low": "",
            "precision_ci_high": "",
            "reliability_class": "structural_only",
            "freeze_recommendation": "freeze_with_caution",
            "reliability_reason_ko": "structural step2",
        },
        {
            "eval_scope": "step3_precursor_performance",
            "target_name": "first_signalcount2",
            "metric_kind": "true_case_metric",
            "positive_support": 2,
            "negative_support": 10,
            "predicted_positive_support": 2,
            "recall": 1.0,
            "precision": 1.0,
            "f1": 1.0,
            "recall_ci_low": 0.34,
            "recall_ci_high": 1.0,
            "precision_ci_low": 0.34,
            "precision_ci_high": 1.0,
            "reliability_class": "underpowered",
            "freeze_recommendation": "do_not_freeze",
            "reliability_reason_ko": "underpowered precursor",
        },
        {
            "eval_scope": "step3_precursor_performance",
            "target_name": "first_pre_alarm",
            "metric_kind": "true_case_metric",
            "positive_support": 2,
            "negative_support": 10,
            "predicted_positive_support": 3,
            "recall": 0.5,
            "precision": 0.33,
            "f1": 0.4,
            "recall_ci_low": 0.09,
            "recall_ci_high": 0.9,
            "precision_ci_low": 0.06,
            "precision_ci_high": 0.79,
            "reliability_class": "underpowered",
            "freeze_recommendation": "do_not_freeze",
            "reliability_reason_ko": "underpowered precursor",
        },
        {
            "eval_scope": "step4_abrupt_no_precursor",
            "target_name": "final_fault_hit_by_anchor",
            "metric_kind": "true_case_metric",
            "positive_support": 3,
            "negative_support": 6,
            "predicted_positive_support": 4,
            "recall": 0.83,
            "precision": 0.83,
            "f1": 0.83,
            "recall_ci_low": 0.30,
            "recall_ci_high": 0.95,
            "precision_ci_low": 0.30,
            "precision_ci_high": 0.95,
            "reliability_class": "underpowered",
            "freeze_recommendation": "do_not_freeze",
            "reliability_reason_ko": "interpretation precursor 3 / strict precursor eval 2 / pure abrupt eval 3",
        },
        {
            "eval_scope": "step4_common_cause_routing",
            "target_name": "breadth_marker_only",
            "metric_kind": "true_case_metric",
            "positive_support": 4,
            "negative_support": 8,
            "predicted_positive_support": 4,
            "recall": 1.0,
            "precision": 1.0,
            "f1": 1.0,
            "recall_ci_low": 0.51,
            "recall_ci_high": 1.0,
            "precision_ci_low": 0.51,
            "precision_ci_high": 1.0,
            "reliability_class": "underpowered",
            "freeze_recommendation": "do_not_freeze",
            "reliability_reason_ko": "common cause underpowered",
        },
        {
            "eval_scope": "step4_common_cause_routing",
            "target_name": "combined_marker",
            "metric_kind": "true_case_metric",
            "positive_support": 4,
            "negative_support": 8,
            "predicted_positive_support": 4,
            "recall": 1.0,
            "precision": 1.0,
            "f1": 1.0,
            "recall_ci_low": 0.51,
            "recall_ci_high": 1.0,
            "precision_ci_low": 0.51,
            "precision_ci_high": 1.0,
            "reliability_class": "underpowered",
            "freeze_recommendation": "do_not_freeze",
            "reliability_reason_ko": "common cause underpowered",
        },
        {
            "eval_scope": "operator_policy_proxy",
            "target_name": "baseline_plus_discovery_cluster",
            "metric_kind": "retrospective_proxy_metric",
            "positive_support": 11,
            "negative_support": 19,
            "predicted_positive_support": 30,
            "recall": 1.0,
            "precision": 0.37,
            "f1": 0.54,
            "recall_ci_low": 0.74,
            "recall_ci_high": 1.0,
            "precision_ci_low": 0.21,
            "precision_ci_high": 0.55,
            "reliability_class": "proxy_only",
            "freeze_recommendation": "freeze_with_caution",
            "reliability_reason_ko": "proxy only",
        },
        {
            "eval_scope": "operator_policy_proxy",
            "target_name": "baseline_plus_discovery_narrow",
            "metric_kind": "retrospective_proxy_metric",
            "positive_support": 11,
            "negative_support": 19,
            "predicted_positive_support": 29,
            "recall": 1.0,
            "precision": 0.38,
            "f1": 0.55,
            "recall_ci_low": 0.74,
            "recall_ci_high": 1.0,
            "precision_ci_low": 0.22,
            "precision_ci_high": 0.56,
            "reliability_class": "proxy_only",
            "freeze_recommendation": "freeze_with_caution",
            "reliability_reason_ko": "proxy only",
        },
    ]
    write_csv(
        share / "panel_day_engine_project_eval_reliability_v1.csv",
        reliability_rows,
        [
            "eval_scope",
            "target_name",
            "metric_kind",
            "positive_support",
            "negative_support",
            "predicted_positive_support",
            "recall",
            "precision",
            "f1",
            "recall_ci_low",
            "recall_ci_high",
            "precision_ci_low",
            "precision_ci_high",
            "reliability_class",
            "freeze_recommendation",
            "reliability_reason_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_project_eval_freeze_candidates_v1.csv",
        [
            {
                "eval_scope": "step1_taxonomy",
                "recommended_target_name": "",
                "recommended_metric_kind": "structural_coverage_metric",
                "recommended_f1": "",
                "recommended_positive_support": "",
                "recommended_reliability_class": "structural_only",
                "recommended_freeze_recommendation": "freeze_with_caution",
                "rationale_ko": "step1 structural caution",
            },
            {
                "eval_scope": "step2_onset_truth",
                "recommended_target_name": "",
                "recommended_metric_kind": "structural_coverage_metric",
                "recommended_f1": "",
                "recommended_positive_support": "",
                "recommended_reliability_class": "structural_only",
                "recommended_freeze_recommendation": "freeze_with_caution",
                "rationale_ko": "step2 structural caution",
            },
            {
                "eval_scope": "step3_precursor_performance",
                "recommended_target_name": "",
                "recommended_metric_kind": "",
                "recommended_f1": "",
                "recommended_positive_support": "",
                "recommended_reliability_class": "",
                "recommended_freeze_recommendation": "do_not_freeze",
                "rationale_ko": "step3 underpowered",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "recommended_target_name": "",
                "recommended_metric_kind": "",
                "recommended_f1": "",
                "recommended_positive_support": "",
                "recommended_reliability_class": "",
                "recommended_freeze_recommendation": "do_not_freeze",
                "rationale_ko": "interpretation precursor 3 / strict precursor eval 2 / pure abrupt eval 3",
            },
            {
                "eval_scope": "step4_common_cause_routing",
                "recommended_target_name": "",
                "recommended_metric_kind": "",
                "recommended_f1": "",
                "recommended_positive_support": "",
                "recommended_reliability_class": "",
                "recommended_freeze_recommendation": "do_not_freeze",
                "rationale_ko": "common cause descriptive only",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "recommended_target_name": "baseline_plus_discovery_narrow",
                "recommended_metric_kind": "retrospective_proxy_metric",
                "recommended_f1": 0.55,
                "recommended_positive_support": 11,
                "recommended_reliability_class": "proxy_only",
                "recommended_freeze_recommendation": "freeze_with_caution",
                "rationale_ko": "workflow proxy caution",
            },
        ],
        [
            "eval_scope",
            "recommended_target_name",
            "recommended_metric_kind",
            "recommended_f1",
            "recommended_positive_support",
            "recommended_reliability_class",
            "recommended_freeze_recommendation",
            "rationale_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_project_truth_acquisition_backlog_v1.csv",
        [
            {
                "eval_scope": "step1_taxonomy",
                "collection_unit": "none",
                "expansion_action_class": "no_action_structural",
                "current_positive_support_unique": 1,
                "additional_units_needed_for_5": 4,
                "additional_units_needed_for_10": 9,
                "requires_new_truth_or_data_flag": 0,
                "suggested_collection_source_ko": "문서 유지",
                "priority_rank": 6,
                "freeze_status_ko": "freeze_with_caution",
                "backlog_reason_ko": "structural only",
            },
            {
                "eval_scope": "step2_onset_truth",
                "collection_unit": "none",
                "expansion_action_class": "no_action_structural",
                "current_positive_support_unique": 2,
                "additional_units_needed_for_5": 3,
                "additional_units_needed_for_10": 8,
                "requires_new_truth_or_data_flag": 0,
                "suggested_collection_source_ko": "문서 유지",
                "priority_rank": 6,
                "freeze_status_ko": "freeze_with_caution",
                "backlog_reason_ko": "structural only",
            },
            {
                "eval_scope": "step3_precursor_performance",
                "collection_unit": "fault_case",
                "expansion_action_class": "collect_new_precursor_truth_cases",
                "current_positive_support_unique": 2,
                "additional_units_needed_for_5": 3,
                "additional_units_needed_for_10": 8,
                "requires_new_truth_or_data_flag": 1,
                "suggested_collection_source_ko": "새 precursor fault_case truth 수집",
                "priority_rank": 1,
                "freeze_status_ko": "do_not_freeze",
                "backlog_reason_ko": "precursor backlog blocked",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "collection_unit": "panel_case",
                "expansion_action_class": "collect_new_abrupt_truth_cases",
                "current_positive_support_unique": 3,
                "additional_units_needed_for_5": 2,
                "additional_units_needed_for_10": 7,
                "requires_new_truth_or_data_flag": 1,
                "suggested_collection_source_ko": "새 abrupt panel_case truth 수집",
                "priority_rank": 3,
                "freeze_status_ko": "do_not_freeze",
                "backlog_reason_ko": "pure abrupt gap remains while interpretation precursor 3 / strict precursor eval 2 / pure abrupt eval 3 stay intentionally different",
            },
            {
                "eval_scope": "step4_common_cause_routing",
                "collection_unit": "site_event",
                "expansion_action_class": "collect_new_common_cause_truth_cases",
                "current_positive_support_unique": 4,
                "additional_units_needed_for_5": 1,
                "additional_units_needed_for_10": 6,
                "requires_new_truth_or_data_flag": 1,
                "suggested_collection_source_ko": "새 common-cause site_event truth 수집",
                "priority_rank": 2,
                "freeze_status_ko": "do_not_freeze",
                "backlog_reason_ko": "common-cause backlog blocked",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "collection_unit": "workflow_observation",
                "expansion_action_class": "workflow_validation_not_truth",
                "current_positive_support_unique": 11,
                "additional_units_needed_for_5": 0,
                "additional_units_needed_for_10": 0,
                "requires_new_truth_or_data_flag": 0,
                "suggested_collection_source_ko": "workflow observation 수집",
                "priority_rank": 4,
                "freeze_status_ko": "freeze_with_caution",
                "backlog_reason_ko": "workflow validation only",
            },
        ],
        [
            "eval_scope",
            "collection_unit",
            "expansion_action_class",
            "current_positive_support_unique",
            "additional_units_needed_for_5",
            "additional_units_needed_for_10",
            "requires_new_truth_or_data_flag",
            "suggested_collection_source_ko",
            "priority_rank",
            "freeze_status_ko",
            "backlog_reason_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_project_truth_expansion_plan_summary_v1.csv",
        [
            {
                "expansion_action_class": "collect_new_precursor_truth_cases",
                "target_count": 6,
                "total_additional_positive_needed_for_5": 18,
                "total_additional_positive_needed_for_10": 48,
                "requires_new_truth_or_data_count": 6,
                "highest_priority_rank": 1,
                "note_ko": "precursor-bearing scope needs new fault_case truth",
            },
            {
                "expansion_action_class": "collect_new_common_cause_truth_cases",
                "target_count": 3,
                "total_additional_positive_needed_for_5": 3,
                "total_additional_positive_needed_for_10": 18,
                "requires_new_truth_or_data_count": 3,
                "highest_priority_rank": 2,
                "note_ko": "common-cause scope needs new site_event truth",
            },
            {
                "expansion_action_class": "collect_new_abrupt_truth_cases",
                "target_count": 5,
                "total_additional_positive_needed_for_5": 2,
                "total_additional_positive_needed_for_10": 31,
                "requires_new_truth_or_data_count": 5,
                "highest_priority_rank": 3,
                "note_ko": "pure abrupt scope needs more panel_case truth while interpretation precursor 3 / strict precursor eval 2 / pure abrupt eval 3 stay intentionally different",
            },
            {
                "expansion_action_class": "workflow_validation_not_truth",
                "target_count": 5,
                "total_additional_positive_needed_for_5": 0,
                "total_additional_positive_needed_for_10": 0,
                "requires_new_truth_or_data_count": 0,
                "highest_priority_rank": 4,
                "note_ko": "workflow validation, not more truth labels",
            },
            {
                "expansion_action_class": "no_action_structural",
                "target_count": 4,
                "total_additional_positive_needed_for_5": 0,
                "total_additional_positive_needed_for_10": 0,
                "requires_new_truth_or_data_count": 0,
                "highest_priority_rank": 6,
                "note_ko": "structural coverage only",
            },
        ],
        [
            "expansion_action_class",
            "target_count",
            "total_additional_positive_needed_for_5",
            "total_additional_positive_needed_for_10",
            "requires_new_truth_or_data_count",
            "highest_priority_rank",
            "note_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_operator_attention_policy_recommendation_v1.csv",
        [
            {
                "recommended_policy_name": "baseline_plus_discovery_cluster",
                "recommended_policy_reason_ko": "recommended for operator workflow",
                "expected_use_ko": "queue/watch baseline에 discovery cluster를 side-by-side로 붙인 기본 operator workflow",
                "caution_ko": "panel-level drill-down은 별도 panel preview가 필요하다.",
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
        share / "panel_day_engine_fault_panel_event_audit_summary_v1.csv",
        [
            {
                "사건유형_재판정_전조형수": 3,
                "사건유형_재판정_급작수": 3,
                "전조평가셋편입_패널수": 2,
                "급작평가셋편입_패널수": 3,
                "해석과평가셋불일치_패널수": 1,
            }
        ],
        [
            "사건유형_재판정_전조형수",
            "사건유형_재판정_급작수",
            "전조평가셋편입_패널수",
            "급작평가셋편입_패널수",
            "해석과평가셋불일치_패널수",
        ],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder_path = repo_root / "research/prognostics/build_panel_day_engine_project_current_data_freeze_pack_v1.py"
    builder_mod = load_module(builder_path, "project_current_data_freeze_pack_builder")

    official_paths = [
        repo_root / "_share" / "panel_day_engine_project_current_data_freeze_pack_v1.csv",
        repo_root / "_share" / "panel_day_engine_project_current_data_freeze_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_project_current_data_claims_v1.csv",
    ]
    official_digests_before = {path: file_digest(path) for path in official_paths}

    py_compile.compile(str(builder_path), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="project_current_data_freeze_pack_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture(tmp_root)
        result = run([sys.executable, str(builder_path), "--root", str(tmp_root)], repo_root)
        assert_true(result.returncode == 0, result.stderr or result.stdout)

        pack = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_current_data_freeze_pack_v1.csv",
            encoding="utf-8-sig",
        )
        summary = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_current_data_freeze_summary_v1.csv",
            encoding="utf-8-sig",
        )
        claims = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_current_data_claims_v1.csv",
            encoding="utf-8-sig",
        )

        assert_true(pack.columns.tolist() == builder_mod.FREEZE_PACK_COLS, "freeze pack schema mismatch")
        assert_true(summary.columns.tolist() == builder_mod.FREEZE_SUMMARY_COLS, "freeze summary schema mismatch")
        assert_true(claims.columns.tolist() == builder_mod.CLAIMS_COLS, "claims schema mismatch")
        assert_true(len(pack) == 6, "expected one row per eval scope")

        step3_row = pack.loc[pack["eval_scope"].eq("step3_precursor_performance")].iloc[0]
        assert_true(step3_row["current_best_target_name"] == "first_signalcount2", "step3 best target fallback failed")
        assert_true(step3_row["current_data_decision"] == "exploratory_only", "step3 decision mapping failed")
        assert_true(step3_row["allowed_claim_strength"] == "exploratory_claim_only", "step3 claim strength failed")
        assert_true(step3_row["next_allowed_action"] == "do_not_upgrade_without_new_truth", "step3 next action failed")
        assert_true(int(step3_row["acquisition_blocked_flag"]) == 1, "step3 acquisition blocked flag failed")

        abrupt_row = pack.loc[pack["eval_scope"].eq("step4_abrupt_no_precursor")].iloc[0]
        assert_true(abrupt_row["current_best_target_name"] == "final_fault_hit_by_anchor", "abrupt best target failed")
        assert_true(abrupt_row["current_data_decision"] == "exploratory_only", "abrupt decision mapping failed")
        assert_true(abrupt_row["allowed_claim_strength"] == "exploratory_claim_only", "abrupt claim strength failed")
        assert_true(abrupt_row["next_allowed_action"] == "do_not_upgrade_without_new_truth", "abrupt next action failed")
        assert_true(int(abrupt_row["acquisition_blocked_flag"]) == 1, "abrupt acquisition blocked flag failed")
        assert_true(
            "사건 해석상 전조형 고장 패널은 3개" in abrupt_row["freeze_reason_ko"]
            and "엄격 전조 평가셋 편입은 2개" in abrupt_row["freeze_reason_ko"]
            and "순수 급작 평가셋 편입은 3개" in abrupt_row["freeze_reason_ko"]
            and "c42997" in abrupt_row["freeze_reason_ko"],
            "abrupt freeze reason should mention the 3/2/3 interpretation-vs-eval split",
        )

        common_row = pack.loc[pack["eval_scope"].eq("step4_common_cause_routing")].iloc[0]
        assert_true(common_row["current_best_target_name"] == "breadth_marker_only", "common-cause best target fallback failed")
        assert_true(common_row["current_data_decision"] == "exploratory_only", "common-cause decision failed")
        assert_true(common_row["allowed_claim_strength"] == "exploratory_claim_only", "common-cause claim strength failed")

        operator_row = pack.loc[pack["eval_scope"].eq("operator_policy_proxy")].iloc[0]
        assert_true(operator_row["current_best_target_name"] == "baseline_plus_discovery_narrow", "operator retrospective best target failed")
        assert_true(operator_row["current_operational_workflow_name"] == "baseline_plus_discovery_cluster", "operator operational workflow mapping failed")
        assert_true(operator_row["current_operational_workflow_reason_ko"] == "recommended for operator workflow", "operator workflow reason mapping failed")
        assert_true(operator_row["current_data_decision"] == "workflow_proxy_only", "operator decision mapping failed")
        assert_true(operator_row["allowed_claim_strength"] == "workflow_claim_only", "operator claim strength failed")
        assert_true(operator_row["next_allowed_action"] == "operator_workflow_only", "operator next action failed")
        assert_true(int(operator_row["acquisition_blocked_flag"]) == 0, "operator acquisition blocked flag failed")
        assert_true("retrospective proxy best target은 baseline_plus_discovery_narrow" in operator_row["freeze_reason_ko"], "operator freeze reason missing retrospective distinction")
        assert_true("operational workflow 는 baseline_plus_discovery_cluster" in operator_row["freeze_reason_ko"], "operator freeze reason missing workflow distinction")
        assert_true("pipeline pass=1" in operator_row["freeze_reason_ko"], "operator freeze reason missing pipeline status")

        step1_row = pack.loc[pack["eval_scope"].eq("step1_taxonomy")].iloc[0]
        assert_true(step1_row["current_best_target_name"] == "coverage_only", "step1 structural target label failed")
        assert_true(pd.isna(step1_row["current_best_f1"]) or step1_row["current_best_f1"] == "", "step1 structural f1 should be blank")
        assert_true(step1_row["current_data_decision"] == "freeze_with_caution", "step1 decision failed")
        assert_true(step1_row["allowed_claim_strength"] == "bounded_current_data_claim", "step1 claim strength failed")
        assert_true(int(step1_row["acquisition_blocked_flag"]) == 0, "step1 acquisition blocked flag failed")

        step2_row = pack.loc[pack["eval_scope"].eq("step2_onset_truth")].iloc[0]
        assert_true(step2_row["current_best_target_name"] == "coverage_only", "step2 structural target label failed")
        assert_true(pd.isna(step2_row["current_best_f1"]) or step2_row["current_best_f1"] == "", "step2 structural f1 should be blank")

        summary_lookup = {row["current_data_decision"]: row for _, row in summary.iterrows()}
        assert_true(int(summary_lookup["freeze_as_current_default"]["scope_count"]) == 0, "summary default scope_count failed")
        assert_true(int(summary_lookup["freeze_with_caution"]["scope_count"]) == 2, "summary caution scope_count failed")
        assert_true(int(summary_lookup["exploratory_only"]["scope_count"]) == 3, "summary exploratory scope_count failed")
        assert_true(int(summary_lookup["workflow_proxy_only"]["scope_count"]) == 1, "summary workflow scope_count failed")

        assert_true(len(claims) == 6, "expected one claim row per scope")
        step3_claim = claims.loc[claims["claim_scope"].eq("step3_precursor_performance")].iloc[0]
        assert_true("underpowered" in step3_claim["claim_text_ko"], "step3 claim text missing underpowered")
        step4_claim = claims.loc[claims["claim_scope"].eq("step4_abrupt_no_precursor")].iloc[0]
        assert_true("positive support=3" in step4_claim["claim_text_ko"], "step4 claim should mention corrected pure abrupt support")
        assert_true(
            "사건 해석상 전조형 고장 패널은 3개" in step4_claim["claim_text_ko"]
            and "엄격 전조 평가셋 편입은 2개" in step4_claim["claim_text_ko"]
            and "순수 급작 평가셋 편입은 3개" in step4_claim["claim_text_ko"]
            and "c42997" in step4_claim["claim_text_ko"],
            "step4 claim should mention the 3/2/3 interpretation-vs-eval split",
        )
        step1_claim = claims.loc[claims["claim_scope"].eq("step1_taxonomy")].iloc[0]
        assert_true("best target" not in step1_claim["claim_text_ko"], "step1 claim should avoid classifier-style best target wording")
        operator_claim = claims.loc[claims["claim_scope"].eq("operator_policy_proxy")].iloc[0]
        assert_true("baseline_plus_discovery_cluster" in operator_claim["claim_text_ko"], "operator claim missing policy")
        assert_true("baseline_plus_discovery_narrow" in operator_claim["claim_text_ko"], "operator claim missing retrospective best target")
        assert_true("pipeline pass=1" in operator_claim["claim_text_ko"], "operator claim missing pipeline status")

    official_digests_after = {path: file_digest(path) for path in official_paths}
    assert_true(official_digests_before == official_digests_after, "official outputs were modified")

    print("smoke_test_panel_day_engine_project_current_data_freeze_pack_v1.py: PASS")


if __name__ == "__main__":
    main()
