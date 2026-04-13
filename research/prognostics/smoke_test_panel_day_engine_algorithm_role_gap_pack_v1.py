#!/usr/bin/env python3
from __future__ import annotations

import hashlib
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


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig")


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_fixture(root: Path) -> None:
    share = root / "_share"
    share.mkdir(parents=True, exist_ok=True)

    write_csv(
        share / "panel_day_engine_project_final_decision_pack_v1.csv",
        [
            {
                "eval_scope": "step1_taxonomy",
                "current_data_decision": "freeze_with_caution",
                "allowed_claim_strength": "bounded_current_data_claim",
                "current_best_target_name": "coverage_only",
                "current_best_metric_kind": "structural_coverage_metric",
                "current_best_f1": "",
                "current_best_positive_support": 3,
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "final_usage_decision": "bounded_reporting_use",
                "final_reason_ko": "step1 structural only",
            },
            {
                "eval_scope": "step2_onset_truth",
                "current_data_decision": "freeze_with_caution",
                "allowed_claim_strength": "bounded_current_data_claim",
                "current_best_target_name": "coverage_only",
                "current_best_metric_kind": "structural_coverage_metric",
                "current_best_f1": "",
                "current_best_positive_support": 2,
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "final_usage_decision": "bounded_reporting_use",
                "final_reason_ko": "step2 structural only",
            },
            {
                "eval_scope": "step3_precursor_performance",
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "current_best_target_name": "first_signalcount2",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 1.0,
                "current_best_positive_support": 2,
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "final_usage_decision": "exploratory_only",
                "final_reason_ko": "step3 exploratory only",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "current_data_decision": "freeze_with_caution",
                "allowed_claim_strength": "bounded_current_data_claim",
                "current_best_target_name": "final_fault_hit_by_anchor",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 0.8333333333333334,
                "current_best_positive_support": 6,
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "final_usage_decision": "bounded_reporting_use",
                "final_reason_ko": "step4 abrupt bounded use",
            },
            {
                "eval_scope": "step4_common_cause_routing",
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "current_best_target_name": "breadth_marker_only",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 1.0,
                "current_best_positive_support": 4,
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "final_usage_decision": "exploratory_only",
                "final_reason_ko": "step4 common exploratory only",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "current_data_decision": "workflow_proxy_only",
                "allowed_claim_strength": "workflow_claim_only",
                "current_best_target_name": "baseline_plus_discovery_narrow",
                "current_best_metric_kind": "retrospective_proxy_metric",
                "current_best_f1": 0.55,
                "current_best_positive_support": 11,
                "chosen_operational_workflow_name": "baseline_plus_discovery_cluster",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "final_usage_decision": "workflow_only",
                "final_reason_ko": "workflow only",
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
            "chosen_operational_workflow_name",
            "release_gate_pass_flag",
            "pipeline_pass_flag",
            "final_usage_decision",
            "final_reason_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_project_current_data_freeze_pack_v1.csv",
        [
            {
                "eval_scope": "step1_taxonomy",
                "current_data_decision": "freeze_with_caution",
                "freeze_reason_ko": "step1 structural only",
            },
            {
                "eval_scope": "step2_onset_truth",
                "current_data_decision": "freeze_with_caution",
                "freeze_reason_ko": "step2 structural only",
            },
            {
                "eval_scope": "step3_precursor_performance",
                "current_data_decision": "exploratory_only",
                "freeze_reason_ko": "step3 exploratory only",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "current_data_decision": "freeze_with_caution",
                "freeze_reason_ko": "step4 abrupt bounded",
            },
            {
                "eval_scope": "step4_common_cause_routing",
                "current_data_decision": "exploratory_only",
                "freeze_reason_ko": "step4 common exploratory",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "current_data_decision": "workflow_proxy_only",
                "freeze_reason_ko": "workflow only",
            },
        ],
        ["eval_scope", "current_data_decision", "freeze_reason_ko"],
    )

    write_csv(
        share / "panel_day_engine_project_handoff_summary_v1.csv",
        [
            {
                "eval_scope": "step1_taxonomy",
                "current_data_decision": "freeze_with_caution",
                "final_usage_decision": "bounded_reporting_use",
                "allowed_claim_strength": "bounded_current_data_claim",
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "handoff_status_ko": "주의해서 사용",
            },
            {
                "eval_scope": "step2_onset_truth",
                "current_data_decision": "freeze_with_caution",
                "final_usage_decision": "bounded_reporting_use",
                "allowed_claim_strength": "bounded_current_data_claim",
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "handoff_status_ko": "주의해서 사용",
            },
            {
                "eval_scope": "step3_precursor_performance",
                "current_data_decision": "exploratory_only",
                "final_usage_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "handoff_status_ko": "탐색용으로만 유지",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "current_data_decision": "freeze_with_caution",
                "final_usage_decision": "bounded_reporting_use",
                "allowed_claim_strength": "bounded_current_data_claim",
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "handoff_status_ko": "주의해서 사용",
            },
            {
                "eval_scope": "step4_common_cause_routing",
                "current_data_decision": "exploratory_only",
                "final_usage_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "handoff_status_ko": "탐색용으로만 유지",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "current_data_decision": "workflow_proxy_only",
                "final_usage_decision": "workflow_only",
                "allowed_claim_strength": "workflow_claim_only",
                "chosen_operational_workflow_name": "baseline_plus_discovery_cluster",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "handoff_status_ko": "운영 workflow 용",
            },
        ],
        [
            "eval_scope",
            "current_data_decision",
            "final_usage_decision",
            "allowed_claim_strength",
            "chosen_operational_workflow_name",
            "release_gate_pass_flag",
            "pipeline_pass_flag",
            "handoff_status_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_project_eval_matrix_v1.csv",
        [
            {
                "eval_scope": "step3_precursor_performance",
                "metric_kind": "true_case_metric",
                "target_name": "first_signalcount2",
                "support_positive": 2,
                "f1": 1.0,
                "note_ko": "exploratory precursor metric",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "metric_kind": "true_case_metric",
                "target_name": "final_fault_hit_by_anchor",
                "support_positive": 6,
                "f1": 0.8333333333333334,
                "note_ko": "bounded abrupt metric",
            },
            {
                "eval_scope": "step4_common_cause_routing",
                "metric_kind": "true_case_metric",
                "target_name": "breadth_marker_only",
                "support_positive": 4,
                "f1": 1.0,
                "note_ko": "common-cause exploratory metric",
            },
        ],
        ["eval_scope", "metric_kind", "target_name", "support_positive", "f1", "note_ko"],
    )

    write_csv(
        share / "panel_day_engine_non_precursor_performance_cases_v1.csv",
        [
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "vendor_fault_family": "diode_like",
                "candidate_validity": "true_positive",
                "vendor_reply_class": "vendor_pattern_positive",
            },
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "vendor_fault_family": "diode_like",
                "candidate_validity": "true_positive",
                "vendor_reply_class": "vendor_pattern_positive",
            },
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "vendor_fault_family": "open_or_device_issue_like",
                "candidate_validity": "true_positive",
                "vendor_reply_class": "vendor_likely_positive",
            },
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "vendor_fault_family": "module_damage_like",
                "candidate_validity": "true_positive",
                "vendor_reply_class": "vendor_likely_positive",
            },
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "vendor_fault_family": "none_visible",
                "candidate_validity": "false_positive",
                "vendor_reply_class": "vendor_rejected",
            },
        ],
        ["eval_bucket_v2", "vendor_fault_family", "candidate_validity", "vendor_reply_class"],
    )

    write_csv(
        share / "panel_day_engine_operator_attention_policy_recommendation_v1.csv",
        [
            {
                "recommended_policy_name": "baseline_plus_discovery_cluster",
                "recommended_policy_reason_ko": "cluster workflow chosen",
                "expected_use_ko": "operator workflow default",
                "caution_ko": "not a detector generalization claim",
            }
        ],
        ["recommended_policy_name", "recommended_policy_reason_ko", "expected_use_ko", "caution_ko"],
    )

    write_csv(
        share / "panel_day_engine_operator_pipeline_manifest_v1.csv",
        [
            {
                "final_pipeline_pass_flag": 1,
                "note_ko": "pipeline ok",
            }
        ],
        ["final_pipeline_pass_flag", "note_ko"],
    )

    write_csv(
        share / "panel_day_engine_kernellog_project_mapping_v1.csv",
        [
            {"커널로그_증상명": "출력 저하형"},
            {"커널로그_증상명": "전압 변화형"},
        ],
        ["커널로그_증상명"],
    )

    write_text(root / "docs" / "OPS_GPVS_FAULT_FAMILY_F1.md", "# GPVS fault family\n")
    write_text(root / "docs" / "internal" / "PROGRAM_INVENTORY.md", "# Program inventory\n")
    write_text(root / "_share" / "kernelog1_case" / "CASE_STUDY_KERNELOG1.md", "# kernel study\n")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research" / "prognostics" / "build_panel_day_engine_algorithm_role_gap_pack_v1.py"
    smoke_script = repo_root / "research" / "prognostics" / "smoke_test_panel_day_engine_algorithm_role_gap_pack_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        repo_root / "_share" / "panel_day_engine_algorithm_role_map_v1.csv",
        repo_root / "_share" / "panel_day_engine_algorithm_gap_map_v1.csv",
        repo_root / "_share" / "panel_day_engine_algorithm_decision_flow_v1.md",
    ]
    before_digests = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="tmp_algorithm_role_gap_pack_v1_") as tmp_dir:
        temp_root = Path(tmp_dir)
        build_fixture(temp_root)

        result = run([sys.executable, str(build_script), "--root", str(temp_root)], repo_root)
        assert_true(result.returncode == 0, f"build failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        role_df = pd.read_csv(
            temp_root / "_share" / "panel_day_engine_algorithm_role_map_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )
        gap_df = pd.read_csv(
            temp_root / "_share" / "panel_day_engine_algorithm_gap_map_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )
        decision_flow = (
            temp_root / "_share" / "panel_day_engine_algorithm_decision_flow_v1.md"
        ).read_text(encoding="utf-8-sig")

        assert_true(
            set(role_df["알고리즘명"]) == {"메인 알고리즘", "커널로그 알고리즘", "GPV 기반 알고리즘"},
            "algorithm role rows mismatch",
        )
        required_topics = {
            "세 알고리즘 역할 고정",
            "세 알고리즘 우선순위 고정",
            "커널로그 증상축 ↔ 프로젝트 사건축 매핑",
            "GPV 외부참고축 위치 고정",
            "물리 원인명 확정 한계",
        }
        assert_true(required_topics <= set(gap_df["gap_topic"]), "required gap topics missing")
        for heading in [
            "## 1. 지금 쓰는 3개 알고리즘의 역할",
            "## 2. 실제 판정 순서",
            "## 3. 지금 가능한 판정 / 아직 못 하는 판정",
            "## 4. 과장하면 안 되는 것",
        ]:
            assert_true(heading in decision_flow, f"markdown heading missing: {heading}")
        assert_true(
            "1. 메인 알고리즘이 사건 성격을 먼저 판정한다." in decision_flow,
            "decision order step 1 missing",
        )
        assert_true(
            "2. 커널로그 알고리즘이 증상명/원인군 이름을 붙인다." in decision_flow,
            "decision order step 2 missing",
        )
        assert_true(
            "3. GPV 기반 알고리즘은 외부 참고 축으로 사용한다." in decision_flow,
            "decision order step 3 missing",
        )

    after_digests = {path: file_digest(path) for path in official_outputs}
    assert_true(before_digests == after_digests, "smoke test modified official outputs")

    print("[OK] algorithm role gap scripts compile")
    print("[OK] the three required algorithm rows are emitted")
    print("[OK] the required gap topics are emitted")
    print("[OK] decision flow markdown sections are emitted")
    print("[OK] official outputs unchanged")


if __name__ == "__main__":
    main()
