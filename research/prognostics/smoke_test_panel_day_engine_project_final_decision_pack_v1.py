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
        share / "panel_day_engine_project_current_data_freeze_pack_v1.csv",
        [
            {
                "eval_scope": "step1_taxonomy",
                "current_data_decision": "freeze_with_caution",
                "allowed_claim_strength": "bounded_current_data_claim",
                "current_best_target_name": "coverage_only",
                "current_best_metric_kind": "structural_coverage_metric",
                "current_best_f1": "",
                "current_best_positive_support": 3,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "freeze_with_caution",
                "acquisition_blocked_flag": 0,
                "next_allowed_action": "keep_with_caution_note",
                "freeze_reason_ko": "step1 structural scope",
            },
            {
                "eval_scope": "step2_onset_truth",
                "current_data_decision": "freeze_with_caution",
                "allowed_claim_strength": "bounded_current_data_claim",
                "current_best_target_name": "coverage_only",
                "current_best_metric_kind": "structural_coverage_metric",
                "current_best_f1": "",
                "current_best_positive_support": 2,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "freeze_with_caution",
                "acquisition_blocked_flag": 0,
                "next_allowed_action": "keep_with_caution_note",
                "freeze_reason_ko": "step2 structural scope",
            },
            {
                "eval_scope": "step3_precursor_performance",
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "current_best_target_name": "first_signalcount2",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 1.0,
                "current_best_positive_support": 3,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "do_not_freeze",
                "acquisition_blocked_flag": 1,
                "next_allowed_action": "do_not_upgrade_without_new_truth",
                "freeze_reason_ko": "benchmark reset precursor support 3 and c429 included",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "current_best_target_name": "final_fault_hit_by_anchor",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 0.83,
                "current_best_positive_support": 3,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "do_not_freeze",
                "acquisition_blocked_flag": 1,
                "next_allowed_action": "do_not_upgrade_without_new_truth",
                "freeze_reason_ko": "benchmark reset pure abrupt support 3 with c429 excluded",
            },
            {
                "eval_scope": "step4_common_cause_routing",
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "current_best_target_name": "breadth_marker_only",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 1.0,
                "current_best_positive_support": 4,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "do_not_freeze",
                "acquisition_blocked_flag": 1,
                "next_allowed_action": "do_not_upgrade_without_new_truth",
                "freeze_reason_ko": "step4 common-cause descriptive only",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "current_data_decision": "workflow_proxy_only",
                "allowed_claim_strength": "workflow_claim_only",
                "current_best_target_name": "baseline_plus_discovery_narrow",
                "current_best_metric_kind": "retrospective_proxy_metric",
                "current_best_f1": 0.55,
                "current_best_positive_support": 11,
                "current_operational_workflow_name": "baseline_plus_discovery_cluster",
                "current_operational_workflow_reason_ko": "recommended for operator workflow",
                "freeze_recommendation": "freeze_with_caution",
                "acquisition_blocked_flag": 0,
                "next_allowed_action": "operator_workflow_only",
                "freeze_reason_ko": "operator workflow proxy only",
            },
        ],
        [
            "eval_scope",
            "current_data_decision",
            "allowed_claim_strength",
            "current_best_target_name",
            "current_best_metric_kind",
            "current_best_f1",
            "current_best_positive_support",
            "current_operational_workflow_name",
            "current_operational_workflow_reason_ko",
            "freeze_recommendation",
            "acquisition_blocked_flag",
            "next_allowed_action",
            "freeze_reason_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_project_current_data_freeze_summary_v1.csv",
        [
            {
                "current_data_decision": "freeze_as_current_default",
                "scope_count": 0,
                "operational_default_claim_count": 0,
                "bounded_current_data_claim_count": 0,
                "exploratory_claim_only_count": 0,
                "workflow_claim_only_count": 0,
                "note_ko": "none",
            },
            {
                "current_data_decision": "freeze_with_caution",
                "scope_count": 2,
                "operational_default_claim_count": 0,
                "bounded_current_data_claim_count": 2,
                "exploratory_claim_only_count": 0,
                "workflow_claim_only_count": 0,
                "note_ko": "caution",
            },
            {
                "current_data_decision": "exploratory_only",
                "scope_count": 3,
                "operational_default_claim_count": 0,
                "bounded_current_data_claim_count": 0,
                "exploratory_claim_only_count": 3,
                "workflow_claim_only_count": 0,
                "note_ko": "exploratory",
            },
            {
                "current_data_decision": "workflow_proxy_only",
                "scope_count": 1,
                "operational_default_claim_count": 0,
                "bounded_current_data_claim_count": 0,
                "exploratory_claim_only_count": 0,
                "workflow_claim_only_count": 1,
                "note_ko": "workflow only",
            },
        ],
        [
            "current_data_decision",
            "scope_count",
            "operational_default_claim_count",
            "bounded_current_data_claim_count",
            "exploratory_claim_only_count",
            "workflow_claim_only_count",
            "note_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_project_current_data_claims_v1.csv",
        [
            {
                "claim_id": "claim_step1_taxonomy",
                "claim_scope": "step1_taxonomy",
                "claim_text_ko": "step1 taxonomy/support 범위는 structural coverage 설명으로만 유지한다.",
                "claim_strength": "bounded_current_data_claim",
                "prohibited_overclaim_ko": "step1 overclaim 금지",
            },
            {
                "claim_id": "claim_step2_onset_truth",
                "claim_scope": "step2_onset_truth",
                "claim_text_ko": "step2 onset rows는 onset coverage/reference 설명으로만 유지한다.",
                "claim_strength": "bounded_current_data_claim",
                "prohibited_overclaim_ko": "step2 overclaim 금지",
            },
            {
                "claim_id": "claim_step3_precursor",
                "claim_scope": "step3_precursor_performance",
                "claim_text_ko": "step3 precursor marker 결과는 exploratory result 로만 사용한다.",
                "claim_strength": "exploratory_claim_only",
                "prohibited_overclaim_ko": "step3 stable detector claim 금지",
            },
            {
                "claim_id": "claim_step4_abrupt",
                "claim_scope": "step4_abrupt_no_precursor",
                "claim_text_ko": "step4 pure abrupt/no-precursor 결과는 benchmark reset 이후 precursor benchmark 3과 분리된 순수 급작 benchmark 3만을 positive 로 두고, positive support=3 이라 exploratory result 로만 유지한다. c42997 row는 precursor benchmark에 포함되고 pure abrupt benchmark에서는 제외된다.",
                "claim_strength": "exploratory_claim_only",
                "prohibited_overclaim_ko": "pure abrupt support 3을 large-support stable benchmark 로 과장하지 말 것.",
            },
            {
                "claim_id": "claim_step4_common_cause",
                "claim_scope": "step4_common_cause_routing",
                "claim_text_ko": "step4 common-cause routing 은 descriptive / exploratory 수준으로만 유지한다.",
                "claim_strength": "exploratory_claim_only",
                "prohibited_overclaim_ko": "common-cause operational classifier claim 금지",
            },
            {
                "claim_id": "claim_operator_workflow",
                "claim_scope": "operator_policy_proxy",
                "claim_text_ko": "operator workflow 는 workflow proxy claim 으로만 사용한다.",
                "claim_strength": "workflow_claim_only",
                "prohibited_overclaim_ko": "workflow validation을 detector generalization claim 으로 바꾸지 말 것.",
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
        share / "panel_day_engine_operator_attention_policy_recommendation_v1.csv",
        [
            {
                "recommended_policy_name": "baseline_plus_discovery_cluster",
                "recommended_policy_reason_ko": "recommended for operator workflow",
                "expected_use_ko": "queue/watch baseline에 discovery cluster를 붙인 기본 workflow",
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
        share / "panel_day_engine_operator_release_gate_manifest_v1.csv",
        [
            {
                "final_release_gate_pass_flag": 1,
                "note_ko": "release gate pass",
            }
        ],
        [
            "final_release_gate_pass_flag",
            "note_ko",
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
                "전조평가셋편입_패널수": 3,
                "급작평가셋편입_패널수": 3,
            }
        ],
        ["사건유형_재판정_전조형수", "전조평가셋편입_패널수", "급작평가셋편입_패널수"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder_path = repo_root / "research/prognostics/build_panel_day_engine_project_final_decision_pack_v1.py"
    smoke_path = Path(__file__).resolve()
    load_module(builder_path, "project_final_decision_pack_builder")

    py_compile.compile(str(builder_path), doraise=True)
    py_compile.compile(str(smoke_path), doraise=True)

    official_outputs = [
        repo_root / "_share/panel_day_engine_project_final_decision_pack_v1.csv",
        repo_root / "_share/panel_day_engine_project_final_decision_summary_v1.csv",
        repo_root / "_share/panel_day_engine_project_final_do_and_dont_v1.csv",
    ]
    before_digests = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="project_final_decision_pack_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture(tmp_root)

        result = run([sys.executable, str(builder_path), "--root", str(tmp_root)], cwd=repo_root)
        assert_true(result.returncode == 0, f"builder failed: {result.stderr or result.stdout}")

        pack_df = pd.read_csv(
            tmp_root / "_share/panel_day_engine_project_final_decision_pack_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )
        summary_df = pd.read_csv(
            tmp_root / "_share/panel_day_engine_project_final_decision_summary_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )
        do_dont_df = pd.read_csv(
            tmp_root / "_share/panel_day_engine_project_final_do_and_dont_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )

        operator_row = pack_df.loc[pack_df["eval_scope"].eq("operator_policy_proxy")].iloc[0]
        step1_row = pack_df.loc[pack_df["eval_scope"].eq("step1_taxonomy")].iloc[0]
        step3_row = pack_df.loc[pack_df["eval_scope"].eq("step3_precursor_performance")].iloc[0]
        step4_row = pack_df.loc[pack_df["eval_scope"].eq("step4_abrupt_no_precursor")].iloc[0]

        assert_true(step1_row["final_usage_decision"] == "bounded_reporting_use", "step1 should map to bounded_reporting_use")
        assert_true(step3_row["final_usage_decision"] == "exploratory_only", "step3 should map to exploratory_only")
        assert_true(step4_row["final_usage_decision"] == "exploratory_only", "step4 abrupt should map to exploratory_only")
        assert_true(float(step3_row["current_best_positive_support"]) == 3.0, "step3 benchmark support should be reset to 3")
        assert_true("precursor benchmark support는 3개" in step3_row["final_reason_ko"], "step3 final reason should mention precursor benchmark support 3")
        assert_true("순수 급작 benchmark support는 3개" in step4_row["final_reason_ko"], "step4 final reason should mention pure abrupt benchmark support 3")
        assert_true("c42997" in step4_row["final_reason_ko"], "step4 final reason should mention c429 eval-set exclusion")
        assert_true(operator_row["final_usage_decision"] == "workflow_only", "operator scope should map to workflow_only")
        assert_true(
            operator_row["chosen_operational_workflow_name"] == "baseline_plus_discovery_cluster",
            "operator scope should carry chosen workflow",
        )
        non_operator_workflows = pack_df.loc[pack_df["eval_scope"].ne("operator_policy_proxy"), "chosen_operational_workflow_name"]
        assert_true(non_operator_workflows.fillna("").eq("").all(), "non-operator scopes should keep chosen workflow blank")
        assert_true(int(operator_row["release_gate_pass_flag"]) == 1, "release_gate_pass_flag should be 1")
        assert_true(int(operator_row["pipeline_pass_flag"]) == 1, "pipeline_pass_flag should be 1")
        assert_true(
            "baseline_plus_discovery_cluster" in operator_row["final_reason_ko"],
            "operator final reason should mention chosen workflow",
        )

        workflow_summary = summary_df.loc[summary_df["final_usage_decision"].eq("workflow_only")].iloc[0]
        assert_true(int(workflow_summary["scope_count"]) == 1, "workflow_only summary count mismatch")
        assert_true(
            workflow_summary["chosen_operational_workflow_name"] == "baseline_plus_discovery_cluster",
            "summary should repeat chosen workflow",
        )

        expected_topics = {
            "project_current_data_limit",
            "step1_taxonomy",
            "step2_onset_truth",
            "step3_precursor_performance",
            "step4_abrupt_no_precursor",
            "step4_common_cause_routing",
            "operator_workflow",
        }
        assert_true(expected_topics.issubset(set(do_dont_df["scope_or_topic"])), "missing do-and-don't rows")
        operator_do = do_dont_df.loc[do_dont_df["scope_or_topic"].eq("operator_workflow")].iloc[0]
        assert_true(
            "baseline_plus_discovery_cluster" in operator_do["do_text_ko"],
            "operator do row should mention chosen workflow",
        )
        step4_do = do_dont_df.loc[do_dont_df["scope_or_topic"].eq("step4_abrupt_no_precursor")].iloc[0]
        assert_true("positive support=3" in step4_do["do_text_ko"], "step4 do row should mention corrected pure abrupt support")
        assert_true("precursor benchmark 3" in step4_do["do_text_ko"], "step4 do row should mention precursor benchmark support 3")
        assert_true("순수 급작 benchmark 3" in step4_do["do_text_ko"], "step4 do row should mention pure abrupt benchmark support 3")

    after_digests = {path: file_digest(path) for path in official_outputs}
    assert_true(before_digests == after_digests, "smoke test modified official outputs")

    print("smoke_test_panel_day_engine_project_final_decision_pack_v1.py: PASS")


if __name__ == "__main__":
    main()
