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

    plan_rows: list[dict[str, object]] = []
    step3_targets = [
        "first_cond_evt",
        "first_cond_evt_corroborated",
        "first_signalcount2",
        "first_pre_ews",
        "first_ews_warning",
        "first_pre_alarm",
    ]
    for target in step3_targets:
        plan_rows.append(
            {
                "eval_scope": "step3_precursor_performance",
                "target_name": target,
                "reliability_class": "underpowered",
                "freeze_recommendation": "do_not_freeze",
                "current_positive_support": 2,
                "current_negative_support": 10,
                "additional_positive_needed_for_5": 3,
                "additional_positive_needed_for_10": 8,
                "current_artifact_candidate_pool_count": 0,
                "requires_new_truth_or_data_flag": 1,
                "expansion_action_class": "collect_new_precursor_truth_cases",
                "suggested_collection_unit": "fault_case",
                "suggested_collection_source_ko": "새 precursor-bearing fault_case truth 수집",
                "priority_rank": 1,
                "expansion_reason_ko": "need precursor truth",
            }
        )

    for target in [
        "final_fault_hit_by_anchor",
        "final_fault_hit_within_3d_after",
        "final_fault_hit_within_7d_after",
        "critical_fault_hit_within_7d_after",
        "confirmed_fault_hit_within_7d_after",
    ]:
        plan_rows.append(
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "target_name": target,
                "reliability_class": "low_support",
                "freeze_recommendation": "freeze_with_caution",
                "current_positive_support": 6,
                "current_negative_support": 6,
                "additional_positive_needed_for_5": 0,
                "additional_positive_needed_for_10": 4,
                "current_artifact_candidate_pool_count": 0,
                "requires_new_truth_or_data_flag": 1,
                "expansion_action_class": "collect_new_abrupt_truth_cases",
                "suggested_collection_unit": "panel_case",
                "suggested_collection_source_ko": "새 abrupt panel_case truth 수집",
                "priority_rank": 3,
                "expansion_reason_ko": "need abrupt truth",
            }
        )

    for target in ["current_marker_only", "breadth_marker_only", "combined_marker"]:
        plan_rows.append(
            {
                "eval_scope": "step4_common_cause_routing",
                "target_name": target,
                "reliability_class": "underpowered",
                "freeze_recommendation": "do_not_freeze",
                "current_positive_support": 4,
                "current_negative_support": 8,
                "additional_positive_needed_for_5": 1,
                "additional_positive_needed_for_10": 6,
                "current_artifact_candidate_pool_count": 0,
                "requires_new_truth_or_data_flag": 1,
                "expansion_action_class": "collect_new_common_cause_truth_cases",
                "suggested_collection_unit": "site_event",
                "suggested_collection_source_ko": "새 common-cause site_event truth 수집",
                "priority_rank": 2,
                "expansion_reason_ko": "need common-cause truth",
            }
        )

    for target in ["baseline_only", "workflow_default"]:
        plan_rows.append(
            {
                "eval_scope": "operator_policy_proxy",
                "target_name": target,
                "reliability_class": "proxy_only",
                "freeze_recommendation": "freeze_with_caution",
                "current_positive_support": 11,
                "current_negative_support": 19,
                "additional_positive_needed_for_5": 0,
                "additional_positive_needed_for_10": 0,
                "current_artifact_candidate_pool_count": "",
                "requires_new_truth_or_data_flag": 0,
                "expansion_action_class": "workflow_validation_not_truth",
                "suggested_collection_unit": "workflow_observation",
                "suggested_collection_source_ko": "workflow observation 수집",
                "priority_rank": 4,
                "expansion_reason_ko": "validate workflow",
            }
        )

    for scope, targets, support in [
        ("step1_taxonomy", ["bucket_a", "bucket_b"], [2, 1]),
        ("step2_onset_truth", ["onset_a", "onset_b"], [2, 3]),
    ]:
        for target, current_support in zip(targets, support):
            plan_rows.append(
                {
                    "eval_scope": scope,
                    "target_name": target,
                    "reliability_class": "structural_only",
                    "freeze_recommendation": "freeze_with_caution",
                    "current_positive_support": current_support,
                    "current_negative_support": "",
                    "additional_positive_needed_for_5": max(5 - current_support, 0),
                    "additional_positive_needed_for_10": max(10 - current_support, 0),
                    "current_artifact_candidate_pool_count": "",
                    "requires_new_truth_or_data_flag": 0,
                    "expansion_action_class": "no_action_structural",
                    "suggested_collection_unit": "none",
                    "suggested_collection_source_ko": "문서 유지",
                    "priority_rank": 6,
                    "expansion_reason_ko": "structural scope",
                }
            )

    write_csv(
        share / "panel_day_engine_project_truth_expansion_plan_v1.csv",
        plan_rows,
        [
            "eval_scope",
            "target_name",
            "reliability_class",
            "freeze_recommendation",
            "current_positive_support",
            "current_negative_support",
            "additional_positive_needed_for_5",
            "additional_positive_needed_for_10",
            "current_artifact_candidate_pool_count",
            "requires_new_truth_or_data_flag",
            "expansion_action_class",
            "suggested_collection_unit",
            "suggested_collection_source_ko",
            "priority_rank",
            "expansion_reason_ko",
        ],
    )

    gap_rows: list[dict[str, object]] = []
    for row in plan_rows:
        gap_rows.append(
            {
                "eval_scope": row["eval_scope"],
                "target_name": row["target_name"],
                "reliability_class": row["reliability_class"],
                "freeze_recommendation": row["freeze_recommendation"],
                "current_positive_support": row["current_positive_support"],
                "current_negative_support": row["current_negative_support"],
                "additional_positive_needed_for_5": row["additional_positive_needed_for_5"],
                "additional_positive_needed_for_10": row["additional_positive_needed_for_10"],
                "current_artifact_candidate_pool_name": "",
                "current_artifact_candidate_pool_count": row["current_artifact_candidate_pool_count"],
                "can_reach_5_with_current_artifacts_flag": "",
                "can_reach_10_with_current_artifacts_flag": "",
                "support_gap_reason_ko": "synthetic gap",
            }
        )

    write_csv(
        share / "panel_day_engine_project_eval_support_gap_v1.csv",
        gap_rows,
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
        share / "panel_day_engine_project_freeze_plan_v1.csv",
        [
            {
                "eval_scope": "step3_precursor_performance",
                "recommended_target_name": "",
                "recommended_metric_kind": "",
                "recommended_f1": "",
                "recommended_positive_support": "",
                "recommended_reliability_class": "",
                "recommended_freeze_recommendation": "do_not_freeze",
                "current_default_decision": "do_not_freeze",
                "freeze_reason_ko": "need more precursor support",
            },
            {
                "eval_scope": "step4_common_cause_routing",
                "recommended_target_name": "",
                "recommended_metric_kind": "",
                "recommended_f1": "",
                "recommended_positive_support": "",
                "recommended_reliability_class": "",
                "recommended_freeze_recommendation": "do_not_freeze",
                "current_default_decision": "do_not_freeze",
                "freeze_reason_ko": "need more common-cause support",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "recommended_target_name": "final_fault_hit_by_anchor",
                "recommended_metric_kind": "true_case_metric",
                "recommended_f1": 0.83,
                "recommended_positive_support": 6,
                "recommended_reliability_class": "low_support",
                "recommended_freeze_recommendation": "freeze_with_caution",
                "current_default_decision": "freeze_with_caution",
                "freeze_reason_ko": "caution only",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "recommended_target_name": "workflow_default",
                "recommended_metric_kind": "retrospective_proxy_metric",
                "recommended_f1": 0.53,
                "recommended_positive_support": 11,
                "recommended_reliability_class": "proxy_only",
                "recommended_freeze_recommendation": "freeze_with_caution",
                "current_default_decision": "freeze_with_caution",
                "freeze_reason_ko": "proxy caution",
            },
            {
                "eval_scope": "step1_taxonomy",
                "recommended_target_name": "",
                "recommended_metric_kind": "structural_coverage_metric",
                "recommended_f1": "",
                "recommended_positive_support": "",
                "recommended_reliability_class": "structural_only",
                "recommended_freeze_recommendation": "freeze_with_caution",
                "current_default_decision": "freeze_with_caution",
                "freeze_reason_ko": "structural caution",
            },
            {
                "eval_scope": "step2_onset_truth",
                "recommended_target_name": "",
                "recommended_metric_kind": "structural_coverage_metric",
                "recommended_f1": "",
                "recommended_positive_support": "",
                "recommended_reliability_class": "structural_only",
                "recommended_freeze_recommendation": "freeze_with_caution",
                "current_default_decision": "freeze_with_caution",
                "freeze_reason_ko": "structural caution",
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
            "current_default_decision",
            "freeze_reason_ko",
        ],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder_path = repo_root / "research/prognostics/build_panel_day_engine_project_truth_acquisition_backlog_v1.py"
    builder_mod = load_module(builder_path, "project_truth_acquisition_backlog_builder")

    official_paths = [
        repo_root / "_share" / "panel_day_engine_project_truth_acquisition_backlog_v1.csv",
        repo_root / "_share" / "panel_day_engine_project_truth_acquisition_backlog_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_project_truth_acquisition_notes_v1.csv",
    ]
    official_digests_before = {path: file_digest(path) for path in official_paths}

    py_compile.compile(str(builder_path), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="project_truth_acquisition_backlog_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture(tmp_root)
        result = run([sys.executable, str(builder_path), "--root", str(tmp_root)], repo_root)
        assert_true(result.returncode == 0, result.stderr or result.stdout)

        backlog = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_truth_acquisition_backlog_v1.csv",
            encoding="utf-8-sig",
        )
        summary = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_truth_acquisition_backlog_summary_v1.csv",
            encoding="utf-8-sig",
        )
        notes = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_truth_acquisition_notes_v1.csv",
            encoding="utf-8-sig",
        )

        assert_true(backlog.columns.tolist() == builder_mod.BACKLOG_COLS, "backlog schema mismatch")
        assert_true(summary.columns.tolist() == builder_mod.BACKLOG_SUMMARY_COLS, "backlog summary schema mismatch")
        assert_true(notes.columns.tolist() == builder_mod.BACKLOG_NOTES_COLS, "backlog notes schema mismatch")
        assert_true(len(backlog) == 6, "expected one deduplicated row per scope")

        step3_row = backlog.loc[backlog["eval_scope"].eq("step3_precursor_performance")].iloc[0]
        assert_true(step3_row["collection_unit"] == "fault_case", "step3 collection_unit failed")
        assert_true(int(step3_row["current_positive_support_unique"]) == 2, "step3 unique support failed")
        assert_true(int(step3_row["additional_units_needed_for_5"]) == 3, "step3 unique need-for-5 failed")
        assert_true(int(step3_row["additional_units_needed_for_10"]) == 8, "step3 unique need-for-10 failed")
        assert_true(int(step3_row["priority_rank"]) == 1, "step3 priority failed")
        assert_true(step3_row["freeze_status_ko"] == "do_not_freeze", "step3 freeze status failed")

        abrupt_row = backlog.loc[backlog["eval_scope"].eq("step4_abrupt_no_precursor")].iloc[0]
        assert_true(abrupt_row["collection_unit"] == "panel_case", "abrupt collection_unit failed")
        assert_true(int(abrupt_row["current_positive_support_unique"]) == 6, "abrupt unique support failed")
        assert_true(int(abrupt_row["additional_units_needed_for_5"]) == 0, "abrupt unique need-for-5 failed")
        assert_true(int(abrupt_row["additional_units_needed_for_10"]) == 4, "abrupt unique need-for-10 failed")
        assert_true(abrupt_row["freeze_status_ko"] == "freeze_with_caution", "abrupt freeze status failed")

        common_row = backlog.loc[backlog["eval_scope"].eq("step4_common_cause_routing")].iloc[0]
        assert_true(common_row["collection_unit"] == "site_event", "common-cause collection_unit failed")
        assert_true(int(common_row["current_positive_support_unique"]) == 4, "common-cause unique support failed")
        assert_true(int(common_row["additional_units_needed_for_5"]) == 1, "common-cause unique need-for-5 failed")
        assert_true(int(common_row["additional_units_needed_for_10"]) == 6, "common-cause unique need-for-10 failed")
        assert_true(common_row["freeze_status_ko"] == "do_not_freeze", "common-cause freeze status failed")

        proxy_row = backlog.loc[backlog["eval_scope"].eq("operator_policy_proxy")].iloc[0]
        assert_true(proxy_row["collection_unit"] == "workflow_observation", "proxy collection_unit failed")
        assert_true(int(proxy_row["requires_new_truth_or_data_flag"]) == 0, "proxy requires_new flag failed")
        assert_true(proxy_row["freeze_status_ko"] == "freeze_with_caution", "proxy freeze status failed")

        structural_row = backlog.loc[backlog["eval_scope"].eq("step1_taxonomy")].iloc[0]
        assert_true(structural_row["collection_unit"] == "none", "structural collection_unit failed")
        assert_true(int(structural_row["current_positive_support_unique"]) == 1, "structural unique support failed")
        assert_true(int(structural_row["priority_rank"]) == 6, "structural priority failed")
        assert_true(structural_row["freeze_status_ko"] == "freeze_with_caution", "structural freeze status failed")

        fault_summary = summary.loc[
            summary["collection_unit"].eq("fault_case")
            & summary["expansion_action_class"].eq("collect_new_precursor_truth_cases")
        ].iloc[0]
        assert_true(int(fault_summary["scope_count"]) == 1, "fault_case summary scope_count failed")
        assert_true(int(fault_summary["total_current_positive_support_unique"]) == 2, "fault_case summary support failed")
        assert_true(int(fault_summary["total_additional_units_needed_for_5"]) == 3, "fault_case summary need-for-5 failed")

        none_summary = summary.loc[
            summary["collection_unit"].eq("none")
            & summary["expansion_action_class"].eq("no_action_structural")
        ].iloc[0]
        assert_true(int(none_summary["scope_count"]) == 2, "none summary scope_count failed")
        assert_true(int(none_summary["total_current_positive_support_unique"]) == 3, "none summary support sum failed")

        step3_notes = notes.loc[notes["eval_scope"].eq("step3_precursor_performance")].iloc[0]
        assert_true("+3 new precursor-bearing fault_case" in step3_notes["note_ko"], "step3 notes overcount correction failed")
        common_notes = notes.loc[notes["eval_scope"].eq("step4_common_cause_routing")].iloc[0]
        assert_true("+1 common-cause site_event" in common_notes["note_ko"], "common-cause notes overcount correction failed")

    official_digests_after = {path: file_digest(path) for path in official_paths}
    assert_true(official_digests_before == official_digests_after, "official outputs were modified")

    print("smoke_test_panel_day_engine_project_truth_acquisition_backlog_v1.py: PASS")


if __name__ == "__main__":
    main()
