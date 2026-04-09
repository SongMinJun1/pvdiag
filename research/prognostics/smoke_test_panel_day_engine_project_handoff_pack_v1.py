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
                "final_reason_ko": "step2 structural reference",
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
                "final_reason_ko": "step4 common descriptive only",
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
        share / "panel_day_engine_project_final_decision_summary_v1.csv",
        [
            {
                "final_usage_decision": "operational_default",
                "scope_count": 0,
                "operational_default_count": 0,
                "bounded_reporting_use_count": 0,
                "exploratory_only_count": 0,
                "workflow_only_count": 0,
                "release_gate_pass_flag": 1,
                "chosen_operational_workflow_name": "baseline_plus_discovery_cluster",
                "note_ko": "none",
            },
            {
                "final_usage_decision": "bounded_reporting_use",
                "scope_count": 3,
                "operational_default_count": 0,
                "bounded_reporting_use_count": 3,
                "exploratory_only_count": 0,
                "workflow_only_count": 0,
                "release_gate_pass_flag": 1,
                "chosen_operational_workflow_name": "baseline_plus_discovery_cluster",
                "note_ko": "bounded use",
            },
            {
                "final_usage_decision": "exploratory_only",
                "scope_count": 2,
                "operational_default_count": 0,
                "bounded_reporting_use_count": 0,
                "exploratory_only_count": 2,
                "workflow_only_count": 0,
                "release_gate_pass_flag": 1,
                "chosen_operational_workflow_name": "baseline_plus_discovery_cluster",
                "note_ko": "exploratory",
            },
            {
                "final_usage_decision": "workflow_only",
                "scope_count": 1,
                "operational_default_count": 0,
                "bounded_reporting_use_count": 0,
                "exploratory_only_count": 0,
                "workflow_only_count": 1,
                "release_gate_pass_flag": 1,
                "chosen_operational_workflow_name": "baseline_plus_discovery_cluster",
                "note_ko": "workflow only",
            },
        ],
        [
            "final_usage_decision",
            "scope_count",
            "operational_default_count",
            "bounded_reporting_use_count",
            "exploratory_only_count",
            "workflow_only_count",
            "release_gate_pass_flag",
            "chosen_operational_workflow_name",
            "note_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_project_final_do_and_dont_v1.csv",
        [
            {
                "row_id": "do_01_project_limit",
                "scope_or_topic": "project_current_data_limit",
                "do_text_ko": "현재는 추가 fault case 수집이 불가능하다는 hard constraint 를 먼저 적는다.",
                "dont_text_ko": "새 truth 없이 caution/exploratory scope를 frozen default 로 승격하지 않는다.",
                "claim_strength": "bounded_current_data_claim",
                "priority_order": 1,
            },
            {
                "row_id": "do_02_step1",
                "scope_or_topic": "step1_taxonomy",
                "do_text_ko": "step1 taxonomy 는 structural coverage/reference 설명으로만 사용한다.",
                "dont_text_ko": "step1 taxonomy 를 detector 일반화 성능으로 과장하지 않는다.",
                "claim_strength": "bounded_current_data_claim",
                "priority_order": 2,
            },
            {
                "row_id": "do_03_step2",
                "scope_or_topic": "step2_onset_truth",
                "do_text_ko": "step2 onset truth 는 onset coverage/reference 설명으로만 사용한다.",
                "dont_text_ko": "step2 onset truth 를 classifier 성능 주장으로 과장하지 않는다.",
                "claim_strength": "bounded_current_data_claim",
                "priority_order": 3,
            },
            {
                "row_id": "do_04_step3",
                "scope_or_topic": "step3_precursor_performance",
                "do_text_ko": "step3 precursor 결과는 exploratory result 로만 쓴다.",
                "dont_text_ko": "step3 precursor 결과를 stable detector performance 로 말하지 않는다.",
                "claim_strength": "exploratory_claim_only",
                "priority_order": 4,
            },
            {
                "row_id": "do_05_step4_abrupt",
                "scope_or_topic": "step4_abrupt_no_precursor",
                "do_text_ko": "step4 abrupt/no-precursor 결과는 caution 과 함께 bounded current-data conclusion 으로만 전달한다.",
                "dont_text_ko": "step4 abrupt 결과를 완결된 detector benchmark 로 말하지 않는다.",
                "claim_strength": "bounded_current_data_claim",
                "priority_order": 5,
            },
            {
                "row_id": "do_06_step4_common",
                "scope_or_topic": "step4_common_cause_routing",
                "do_text_ko": "step4 common-cause routing 은 descriptive / exploratory 범위로만 쓴다.",
                "dont_text_ko": "step4 common-cause routing 을 안정된 classifier 성능으로 말하지 않는다.",
                "claim_strength": "exploratory_claim_only",
                "priority_order": 6,
            },
            {
                "row_id": "do_07_operator",
                "scope_or_topic": "operator_workflow",
                "do_text_ko": "chosen operational workflow 와 release/pipeline 통과 상태를 함께 handoff 한다.",
                "dont_text_ko": "workflow validation 을 detector generalization claim 으로 바꾸지 않는다.",
                "claim_strength": "workflow_claim_only",
                "priority_order": 7,
            },
        ],
        [
            "row_id",
            "scope_or_topic",
            "do_text_ko",
            "dont_text_ko",
            "claim_strength",
            "priority_order",
        ],
    )

    write_csv(
        share / "panel_day_engine_operator_attention_policy_recommendation_v1.csv",
        [
            {
                "recommended_policy_name": "baseline_plus_discovery_cluster",
                "recommended_policy_reason_ko": "cluster preview가 operator load와 site skew를 더 잘 억제한다.",
                "expected_use_ko": "queue/watch baseline에 discovery cluster를 side-by-side로 붙인 기본 operator workflow",
                "caution_ko": "cluster view는 panel drill-down을 압축하므로 panel preview를 함께 봐야 한다.",
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


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder_path = repo_root / "research/prognostics/build_panel_day_engine_project_handoff_pack_v1.py"
    smoke_path = Path(__file__).resolve()
    load_module(builder_path, "project_handoff_pack_builder")

    py_compile.compile(str(builder_path), doraise=True)
    py_compile.compile(str(smoke_path), doraise=True)

    official_outputs = [
        repo_root / "_share/panel_day_engine_project_handoff_pack_v1.md",
        repo_root / "_share/panel_day_engine_project_handoff_summary_v1.csv",
    ]
    before_digests = [(str(path), file_digest(path)) for path in official_outputs]

    with tempfile.TemporaryDirectory(prefix="project_handoff_pack_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture(tmp_root)

        result = run([sys.executable, str(builder_path), "--root", str(tmp_root)], cwd=repo_root)
        assert_true(result.returncode == 0, f"builder failed: {result.stderr or result.stdout}")

        summary_df = pd.read_csv(
            tmp_root / "_share/panel_day_engine_project_handoff_summary_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )
        markdown_text = (tmp_root / "_share/panel_day_engine_project_handoff_pack_v1.md").read_text(encoding="utf-8")

        operator_row = summary_df.loc[summary_df["eval_scope"].eq("operator_policy_proxy")].iloc[0]
        step1_row = summary_df.loc[summary_df["eval_scope"].eq("step1_taxonomy")].iloc[0]
        step3_row = summary_df.loc[summary_df["eval_scope"].eq("step3_precursor_performance")].iloc[0]

        assert_true(
            operator_row["chosen_operational_workflow_name"] == "baseline_plus_discovery_cluster",
            "chosen workflow should be populated for operator_policy_proxy",
        )
        assert_true(
            step1_row["chosen_operational_workflow_name"] != step1_row["chosen_operational_workflow_name"]
            or step1_row["chosen_operational_workflow_name"] == "",
            "non-operator scope should keep chosen workflow blank",
        )
        assert_true(step1_row["handoff_status_ko"] == "주의해서 사용", "bounded_reporting_use should map to caution handoff status")
        assert_true(step3_row["handoff_status_ko"] == "탐색용으로만 유지", "exploratory_only should map correctly")
        assert_true(operator_row["handoff_status_ko"] == "운영 workflow 용", "workflow_only should map correctly")

        for heading in [
            "## 1. 지금 확정해서 쓸 수 있는 것",
            "## 2. 조심해서만 써야 하는 것",
            "## 3. 아직 탐색적으로만 봐야 하는 것",
            "## 4. 운영 기본 workflow",
            "## 5. 말해도 되는 것 / 말하면 안 되는 것",
        ]:
            assert_true(heading in markdown_text, f"missing markdown section: {heading}")

        assert_true("baseline_plus_discovery_cluster" in markdown_text, "markdown should mention chosen workflow")
        assert_true("release gate 상태는 `통과`" in markdown_text, "markdown should mention release gate status")
        assert_true("pipeline 상태는 `통과`" in markdown_text, "markdown should mention pipeline status")
        assert_true("step3_precursor_performance" in markdown_text, "markdown should mention step3 exploratory scope")
        assert_true("step4_abrupt_no_precursor" in markdown_text, "markdown should mention step4 abrupt caution scope")

    after_digests = [(str(path), file_digest(path)) for path in official_outputs]
    assert_true(before_digests == after_digests, "smoke test modified official outputs")

    print("smoke_test_panel_day_engine_project_handoff_pack_v1.py: PASS")


if __name__ == "__main__":
    main()
