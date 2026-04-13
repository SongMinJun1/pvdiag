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

    write_csv(
        share / "panel_day_engine_project_eval_reliability_v1.csv",
        [
            {
                "eval_scope": "step1_taxonomy",
                "target_name": "coverage_bucket",
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
                "reliability_reason_ko": "structural only",
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
                "reliability_reason_ko": "tiny support",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "target_name": "final_fault_hit_by_anchor",
                "metric_kind": "true_case_metric",
                "positive_support": 6,
                "negative_support": 6,
                "predicted_positive_support": 6,
                "recall": 0.83,
                "precision": 0.83,
                "f1": 0.83,
                "recall_ci_low": 0.43,
                "recall_ci_high": 0.97,
                "precision_ci_low": 0.43,
                "precision_ci_high": 0.97,
                "reliability_class": "low_support",
                "freeze_recommendation": "freeze_with_caution",
                "reliability_reason_ko": "low support",
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
                "reliability_reason_ko": "tiny support",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "target_name": "workflow_default",
                "metric_kind": "retrospective_proxy_metric",
                "positive_support": 11,
                "negative_support": 19,
                "predicted_positive_support": 30,
                "recall": 1.0,
                "precision": 0.36,
                "f1": 0.53,
                "recall_ci_low": 0.74,
                "recall_ci_high": 1.0,
                "precision_ci_low": 0.21,
                "precision_ci_high": 0.54,
                "reliability_class": "proxy_only",
                "freeze_recommendation": "freeze_with_caution",
                "reliability_reason_ko": "proxy metric",
            },
        ],
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
        share / "panel_day_engine_project_eval_support_gap_v1.csv",
        [
            {
                "eval_scope": "step1_taxonomy",
                "target_name": "coverage_bucket",
                "reliability_class": "structural_only",
                "freeze_recommendation": "freeze_with_caution",
                "current_positive_support": 2,
                "current_negative_support": "",
                "additional_positive_needed_for_5": 3,
                "additional_positive_needed_for_10": 8,
                "current_artifact_candidate_pool_name": "",
                "current_artifact_candidate_pool_count": "",
                "can_reach_5_with_current_artifacts_flag": "",
                "can_reach_10_with_current_artifacts_flag": "",
                "support_gap_reason_ko": "structural scope",
            },
            {
                "eval_scope": "step3_precursor_performance",
                "target_name": "first_signalcount2",
                "reliability_class": "underpowered",
                "freeze_recommendation": "do_not_freeze",
                "current_positive_support": 2,
                "current_negative_support": 10,
                "additional_positive_needed_for_5": 3,
                "additional_positive_needed_for_10": 8,
                "current_artifact_candidate_pool_name": "precursor_pool",
                "current_artifact_candidate_pool_count": 0,
                "can_reach_5_with_current_artifacts_flag": 0,
                "can_reach_10_with_current_artifacts_flag": 0,
                "support_gap_reason_ko": "need new precursor truth",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "target_name": "final_fault_hit_by_anchor",
                "reliability_class": "low_support",
                "freeze_recommendation": "freeze_with_caution",
                "current_positive_support": 6,
                "current_negative_support": 6,
                "additional_positive_needed_for_5": 0,
                "additional_positive_needed_for_10": 4,
                "current_artifact_candidate_pool_name": "abrupt_pool",
                "current_artifact_candidate_pool_count": 2,
                "can_reach_5_with_current_artifacts_flag": 1,
                "can_reach_10_with_current_artifacts_flag": 0,
                "support_gap_reason_ko": "support 5 yes but 10 no",
            },
            {
                "eval_scope": "step4_common_cause_routing",
                "target_name": "combined_marker",
                "reliability_class": "underpowered",
                "freeze_recommendation": "do_not_freeze",
                "current_positive_support": 4,
                "current_negative_support": 8,
                "additional_positive_needed_for_5": 1,
                "additional_positive_needed_for_10": 6,
                "current_artifact_candidate_pool_name": "common_pool",
                "current_artifact_candidate_pool_count": 0,
                "can_reach_5_with_current_artifacts_flag": 0,
                "can_reach_10_with_current_artifacts_flag": 0,
                "support_gap_reason_ko": "need new common-cause truth",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "target_name": "workflow_default",
                "reliability_class": "proxy_only",
                "freeze_recommendation": "freeze_with_caution",
                "current_positive_support": 11,
                "current_negative_support": 19,
                "additional_positive_needed_for_5": 0,
                "additional_positive_needed_for_10": 0,
                "current_artifact_candidate_pool_name": "",
                "current_artifact_candidate_pool_count": "",
                "can_reach_5_with_current_artifacts_flag": "",
                "can_reach_10_with_current_artifacts_flag": "",
                "support_gap_reason_ko": "workflow validation matters",
            },
        ],
        [
            "eval_scope",
            "target_name",
            "reliability_class",
            "freeze_recommendation",
            "current_positive_support",
            "current_negative_support",
            "additional_positive_needed_for_5",
            "additional_positive_needed_for_10",
            "current_artifact_candidate_pool_name",
            "current_artifact_candidate_pool_count",
            "can_reach_5_with_current_artifacts_flag",
            "can_reach_10_with_current_artifacts_flag",
            "support_gap_reason_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_project_eval_support_gap_summary_v1.csv",
        [
            {"eval_scope": "step1_taxonomy", "note_ko": "structural support summary"},
            {"eval_scope": "step3_precursor_performance", "note_ko": "need new truth expansion"},
            {"eval_scope": "step4_abrupt_no_precursor", "note_ko": "some artifact support exists"},
            {"eval_scope": "step4_common_cause_routing", "note_ko": "common-cause support gap remains"},
            {"eval_scope": "operator_policy_proxy", "note_ko": "workflow validation over truth expansion"},
        ],
        [
            "eval_scope",
            "note_ko",
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
                "rationale_ko": "coverage row only",
            },
            {
                "eval_scope": "step3_precursor_performance",
                "recommended_target_name": "",
                "recommended_metric_kind": "true_case_metric",
                "recommended_f1": "",
                "recommended_positive_support": "",
                "recommended_reliability_class": "underpowered",
                "recommended_freeze_recommendation": "do_not_freeze",
                "rationale_ko": "support too small",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "recommended_target_name": "final_fault_hit_by_anchor",
                "recommended_metric_kind": "true_case_metric",
                "recommended_f1": 0.83,
                "recommended_positive_support": 6,
                "recommended_reliability_class": "provisional",
                "recommended_freeze_recommendation": "freeze_as_current_default",
                "rationale_ko": "synthetic provisional winner",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "recommended_target_name": "workflow_default",
                "recommended_metric_kind": "retrospective_proxy_metric",
                "recommended_f1": 0.53,
                "recommended_positive_support": 11,
                "recommended_reliability_class": "proxy_only",
                "recommended_freeze_recommendation": "freeze_with_caution",
                "rationale_ko": "proxy metric only",
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
        share / "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv",
        [
            {"fault_family_id": "fam1", "eval_bucket_v2": "precursor_bearing_detectable_now"},
            {"fault_family_id": "fam2", "eval_bucket_v2": "abrupt_or_no_precursor_now"},
            {"fault_family_id": "fam3", "eval_bucket_v2": "non_panel_or_common_cause"},
            {"fault_family_id": "fam4", "eval_bucket_v2": "non_panel_or_common_cause"},
        ],
        ["fault_family_id", "eval_bucket_v2"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder_path = repo_root / "research/prognostics/build_panel_day_engine_project_truth_expansion_plan_v1.py"
    builder_mod = load_module(builder_path, "project_truth_expansion_builder")

    official_paths = [
        repo_root / "_share" / "panel_day_engine_project_truth_expansion_plan_v1.csv",
        repo_root / "_share" / "panel_day_engine_project_truth_expansion_plan_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_project_freeze_plan_v1.csv",
    ]
    official_digests_before = {path: file_digest(path) for path in official_paths}

    py_compile.compile(str(builder_path), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="project_truth_expansion_plan_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture(tmp_root)
        result = run([sys.executable, str(builder_path), "--root", str(tmp_root)], repo_root)
        assert_true(result.returncode == 0, result.stderr or result.stdout)

        plan = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_truth_expansion_plan_v1.csv",
            encoding="utf-8-sig",
        )
        summary = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_truth_expansion_plan_summary_v1.csv",
            encoding="utf-8-sig",
        )
        freeze = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_freeze_plan_v1.csv",
            encoding="utf-8-sig",
        )

        assert_true(plan.columns.tolist() == builder_mod.PLAN_COLS, "plan schema mismatch")
        assert_true(summary.columns.tolist() == builder_mod.PLAN_SUMMARY_COLS, "plan summary schema mismatch")
        assert_true(freeze.columns.tolist() == builder_mod.FREEZE_PLAN_COLS, "freeze plan schema mismatch")

        precursor_row = plan.loc[plan["eval_scope"].eq("step3_precursor_performance")].iloc[0]
        assert_true(precursor_row["expansion_action_class"] == "collect_new_precursor_truth_cases", "precursor action mapping failed")
        assert_true(int(precursor_row["priority_rank"]) == 1, "precursor priority rank failed")
        assert_true(int(precursor_row["requires_new_truth_or_data_flag"]) == 1, "precursor requires_new flag failed")
        assert_true(precursor_row["suggested_collection_unit"] == "fault_case", "precursor unit failed")

        abrupt_row = plan.loc[plan["eval_scope"].eq("step4_abrupt_no_precursor")].iloc[0]
        assert_true(abrupt_row["expansion_action_class"] == "collect_new_abrupt_truth_cases", "abrupt action mapping failed")
        assert_true(int(abrupt_row["priority_rank"]) == 3, "abrupt priority rank failed")
        assert_true(int(abrupt_row["requires_new_truth_or_data_flag"]) == 0, "abrupt requires_new flag failed")

        common_row = plan.loc[plan["eval_scope"].eq("step4_common_cause_routing")].iloc[0]
        assert_true(common_row["expansion_action_class"] == "collect_new_common_cause_truth_cases", "common-cause action mapping failed")
        assert_true(int(common_row["priority_rank"]) == 2, "common-cause priority rank failed")
        assert_true(int(common_row["requires_new_truth_or_data_flag"]) == 1, "common-cause requires_new flag failed")

        structural_row = plan.loc[plan["eval_scope"].eq("step1_taxonomy")].iloc[0]
        assert_true(structural_row["expansion_action_class"] == "no_action_structural", "structural action mapping failed")
        assert_true(int(structural_row["priority_rank"]) == 6, "structural priority rank failed")
        assert_true(int(structural_row["requires_new_truth_or_data_flag"]) == 0, "structural requires_new flag failed")

        proxy_row = plan.loc[plan["eval_scope"].eq("operator_policy_proxy")].iloc[0]
        assert_true(proxy_row["expansion_action_class"] == "workflow_validation_not_truth", "proxy action mapping failed")
        assert_true(int(proxy_row["priority_rank"]) == 4, "proxy priority rank failed")
        assert_true(int(proxy_row["requires_new_truth_or_data_flag"]) == 0, "proxy requires_new flag failed")

        precursor_summary = summary.loc[summary["expansion_action_class"].eq("collect_new_precursor_truth_cases")].iloc[0]
        assert_true(int(precursor_summary["target_count"]) == 1, "precursor summary target_count failed")
        assert_true(int(precursor_summary["requires_new_truth_or_data_count"]) == 1, "precursor summary requires_new count failed")
        assert_true(int(precursor_summary["highest_priority_rank"]) == 1, "precursor summary priority failed")

        abrupt_freeze = freeze.loc[freeze["eval_scope"].eq("step4_abrupt_no_precursor")].iloc[0]
        assert_true(abrupt_freeze["current_default_decision"] == "freeze_as_current_default", "freeze_as_current_default mapping failed")
        precursor_freeze = freeze.loc[freeze["eval_scope"].eq("step3_precursor_performance")].iloc[0]
        assert_true(precursor_freeze["current_default_decision"] == "do_not_freeze", "do_not_freeze mapping failed")
        structural_freeze = freeze.loc[freeze["eval_scope"].eq("step1_taxonomy")].iloc[0]
        assert_true(structural_freeze["current_default_decision"] == "freeze_with_caution", "freeze_with_caution mapping failed")

    official_digests_after = {path: file_digest(path) for path in official_paths}
    assert_true(official_digests_before == official_digests_after, "official outputs were modified")

    print("smoke_test_panel_day_engine_project_truth_expansion_plan_v1.py: PASS")


if __name__ == "__main__":
    main()
