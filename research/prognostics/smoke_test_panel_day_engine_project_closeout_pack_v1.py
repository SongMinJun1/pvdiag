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
                "final_reason_ko": "operator workflow only",
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
                "do_text_ko": "모든 보고/발표/핸드오프에서 현재는 추가 fault case 수집이 불가능하다는 hard constraint 를 먼저 명시한다.",
                "dont_text_ko": "새 truth 없이 exploratory 또는 caution scope를 frozen default 결론으로 승격하지 말 것.",
                "claim_strength": "bounded_current_data_claim",
                "priority_order": 1,
            },
            {
                "row_id": "do_04_step3",
                "scope_or_topic": "step3_precursor_performance",
                "do_text_ko": "step3 precursor 결과는 exploratory result 로만 쓴다.",
                "dont_text_ko": "step3 precursor 결과를 stable detector performance 로 말하지 않는다.",
                "claim_strength": "exploratory_claim_only",
                "priority_order": 4,
            },
        ],
        ["row_id", "scope_or_topic", "do_text_ko", "dont_text_ko", "claim_strength", "priority_order"],
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
        share / "panel_day_engine_project_current_data_freeze_pack_v1.csv",
        [
            {
                "eval_scope": "step1_taxonomy",
                "current_best_target_name": "coverage_only",
                "current_best_metric_kind": "structural_coverage_metric",
                "current_best_f1": "",
                "current_best_positive_support": 3,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "freeze_with_caution",
                "acquisition_blocked_flag": 0,
                "current_data_decision": "freeze_with_caution",
                "allowed_claim_strength": "bounded_current_data_claim",
                "next_allowed_action": "keep_with_caution_note",
                "freeze_reason_ko": "step1 structural only",
            },
            {
                "eval_scope": "step2_onset_truth",
                "current_best_target_name": "coverage_only",
                "current_best_metric_kind": "structural_coverage_metric",
                "current_best_f1": "",
                "current_best_positive_support": 2,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "freeze_with_caution",
                "acquisition_blocked_flag": 0,
                "current_data_decision": "freeze_with_caution",
                "allowed_claim_strength": "bounded_current_data_claim",
                "next_allowed_action": "keep_with_caution_note",
                "freeze_reason_ko": "step2 structural only",
            },
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
                "freeze_reason_ko": "step4 abrupt bounded",
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
                "current_operational_workflow_reason_ko": "workflow choice",
                "freeze_recommendation": "freeze_with_caution",
                "acquisition_blocked_flag": 0,
                "current_data_decision": "workflow_proxy_only",
                "allowed_claim_strength": "workflow_claim_only",
                "next_allowed_action": "operator_workflow_only",
                "freeze_reason_ko": "workflow only",
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
        share / "panel_day_engine_internal_share_clean_summary_v1.csv",
        [
            {"섹션": "최신 성능", "항목": "전조형 고장", "값_ko": "대표기준=first_signalcount2", "비고_ko": "탐색적"},
            {"섹션": "급작 고장 6건", "항목": "건수", "값_ko": "6건", "비고_ko": "stored abrupt positives"},
            {"섹션": "커널로그-프로젝트 매핑", "항목": "요약", "값_ko": "증상축 vs 사건축", "비고_ko": "mapping only"},
            {"섹션": "GPV 7종", "항목": "요약", "값_ko": "stored by-type metric", "비고_ko": "reference axis"},
            {"섹션": "진행률", "항목": "연구/알고리즘 큰 줄기", "값_ko": "85", "비고_ko": "mainline mostly done"},
        ],
        ["섹션", "항목", "값_ko", "비고_ko"],
    )

    abrupt_rows = []
    for idx in range(6):
        abrupt_rows.append(
            {
                "site": "siteA",
                "panel_id": f"panel.{idx}",
                "고장시점": f"2025-01-0{idx+1}",
                "증상명_ko": "다이오드형" if idx < 4 else ("개방/장치이상형" if idx == 4 else "모듈손상형"),
                "세부근거_ko": "stored truth mapping",
                "source_field_ko": "vendor_fault_family",
                "비고_ko": "fixture",
            }
        )
    write_csv(
        share / "panel_day_engine_abrupt6_symptom_map_v1.csv",
        abrupt_rows,
        ["site", "panel_id", "고장시점", "증상명_ko", "세부근거_ko", "source_field_ko", "비고_ko"],
    )

    write_csv(
        share / "panel_day_engine_kernellog_project_mapping_v1.csv",
        [
            {
                "커널로그_증상명": "출력 저하형",
                "주_프로젝트분류": "전조형 고장",
                "보조_프로젝트분류": "급작 고장",
                "설명_ko": "symptom axis",
                "주의_ko": "do not overclaim",
            },
            {
                "커널로그_증상명": "전압 변화형",
                "주_프로젝트분류": "급작 고장",
                "보조_프로젝트분류": "전조형 고장",
                "설명_ko": "symptom axis",
                "주의_ko": "do not overclaim",
            },
            {
                "커널로그_증상명": "패턴 이상형",
                "주_프로젝트분류": "같이 흔들리는 이상",
                "보조_프로젝트분류": "오경보",
                "설명_ko": "symptom axis",
                "주의_ko": "do not overclaim",
            },
            {
                "커널로그_증상명": "불안정형",
                "주_프로젝트분류": "반복 이상",
                "보조_프로젝트분류": "오경보",
                "설명_ko": "symptom axis",
                "주의_ko": "do not overclaim",
            },
            {
                "커널로그_증상명": "복합형",
                "주_프로젝트분류": "급작 고장",
                "보조_프로젝트분류": "같이 흔들리는 이상",
                "설명_ko": "symptom axis",
                "주의_ko": "do not overclaim",
            },
        ],
        ["커널로그_증상명", "주_프로젝트분류", "보조_프로젝트분류", "설명_ko", "주의_ko"],
    )

    gpv_rows = []
    for idx in range(1, 8):
        gpv_rows.append(
            {
                "고장유형_번호": idx,
                "고장유형_설명_ko": f"GPVS Fault{idx}",
                "성능요약_ko": "stored by-type metric",
                "수치_ko": f"auc=0.{idx}000, ap=0.{idx}100, f1_fpr1=0.{idx}200",
                "source_ref_ko": "data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv",
            }
        )
    write_csv(
        share / "panel_day_engine_gpv7_perf_summary_v1.csv",
        gpv_rows,
        ["고장유형_번호", "고장유형_설명_ko", "성능요약_ko", "수치_ko", "source_ref_ko"],
    )

    write_csv(
        share / "panel_day_engine_project_progress_snapshot_v1.csv",
        [
            {"항목": "연구/알고리즘 큰 줄기", "현재_완료율_추정": 85, "현재_상태_ko": "mainline mostly done", "근거_ko": "step3 and common remain exploratory"},
            {"항목": "운영 스택", "현재_완료율_추정": 95, "현재_상태_ko": "operator stack essentially complete", "근거_ko": "release/pipeline pass"},
            {"항목": "내부 공유/정리 문서", "현재_완료율_추정": 70, "현재_상태_ko": "docs improved", "근거_ko": "appendix and clean pack complete"},
        ],
        ["항목", "현재_완료율_추정", "현재_상태_ko", "근거_ko"],
    )

    write_csv(
        share / "panel_day_engine_operator_attention_policy_recommendation_v1.csv",
        [
            {
                "recommended_policy_name": "baseline_plus_discovery_cluster",
                "recommended_policy_reason_ko": "cluster preview keeps linked proxy gain while reducing operator load.",
                "expected_use_ko": "queue/watch baseline에 discovery cluster를 side-by-side로 붙인 기본 operator workflow",
                "caution_ko": "cluster view는 drill-down이 필요할 때 panel preview를 함께 본다.",
            }
        ],
        ["recommended_policy_name", "recommended_policy_reason_ko", "expected_use_ko", "caution_ko"],
    )

    write_csv(
        share / "panel_day_engine_operator_release_gate_manifest_v1.csv",
        [
            {
                "final_release_gate_pass_flag": 1,
                "note_ko": "operator stack release gate 통과",
            }
        ],
        ["final_release_gate_pass_flag", "note_ko"],
    )

    write_csv(
        share / "panel_day_engine_operator_pipeline_manifest_v1.csv",
        [
            {
                "final_pipeline_pass_flag": 1,
                "note_ko": "전체 operator pipeline 정상",
            }
        ],
        ["final_pipeline_pass_flag", "note_ko"],
    )

    (share / "panel_day_engine_project_handoff_pack_v1.md").write_text(
        "## 1. 지금 확정해서 쓸 수 있는 것\n", encoding="utf-8-sig"
    )
    (share / "panel_day_engine_internal_share_clean_pack_v1.md").write_text(
        "## 1. 최신 성능 요약\n", encoding="utf-8-sig"
    )


def initialize_git_repo(root: Path) -> None:
    assert_true(run(["git", "init", "-b", "feature/test-closeout"], root).returncode == 0, "git init failed")
    assert_true(run(["git", "config", "user.email", "codex@example.com"], root).returncode == 0, "git email failed")
    assert_true(run(["git", "config", "user.name", "Codex"], root).returncode == 0, "git name failed")
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    assert_true(run(["git", "add", "README.md"], root).returncode == 0, "git add failed")
    assert_true(run(["git", "commit", "-m", "fixture"], root).returncode == 0, "git commit failed")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research/prognostics/build_panel_day_engine_project_closeout_pack_v1.py"
    smoke_script = repo_root / "research/prognostics/smoke_test_panel_day_engine_project_closeout_pack_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        repo_root / "_share/panel_day_engine_project_closeout_pack_v1.md",
        repo_root / "_share/panel_day_engine_project_artifact_index_v1.csv",
        repo_root / "_share/panel_day_engine_project_status_snapshot_v1.csv",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="panel_day_engine_closeout_smoke_") as tmp_dir:
        root = Path(tmp_dir)
        build_fixture(root)
        initialize_git_repo(root)

        result = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(result.returncode == 0, f"builder failed: {result.stderr or result.stdout}")

        closeout_md = root / "_share/panel_day_engine_project_closeout_pack_v1.md"
        artifact_index_csv = root / "_share/panel_day_engine_project_artifact_index_v1.csv"
        status_snapshot_csv = root / "_share/panel_day_engine_project_status_snapshot_v1.csv"

        assert_true(closeout_md.exists(), "missing closeout markdown")
        assert_true(artifact_index_csv.exists(), "missing artifact index")
        assert_true(status_snapshot_csv.exists(), "missing status snapshot")

        markdown = closeout_md.read_text(encoding="utf-8-sig")
        required_sections = [
            "## 1. 지금 확정된 결론",
            "## 2. 운영 기본값",
            "## 3. 조심해서만 말해야 하는 것",
            "## 4. 아직 탐색적으로만 남겨야 하는 것",
            "## 5. 가장 먼저 볼 산출물",
            "## 6. 프로젝트를 다시 열면 어디서 시작할지",
        ]
        for section in required_sections:
            assert_true(section in markdown, f"missing markdown section: {section}")
        assert_true("baseline_plus_discovery_cluster" in markdown, "markdown missing chosen workflow")
        assert_true("release gate 는 통과(1)" in markdown, "markdown missing release gate status")
        assert_true("pipeline 도 통과(1)" in markdown, "markdown missing pipeline status")
        assert_true("추가 fault case 수집이 불가능" in markdown, "markdown missing current data limit")

        artifact_index_df = pd.read_csv(artifact_index_csv, low_memory=False, encoding="utf-8-sig")
        required_artifacts = {
            "panel_day_engine_project_final_decision_pack_v1.csv",
            "panel_day_engine_project_final_do_and_dont_v1.csv",
            "panel_day_engine_project_handoff_pack_v1.md",
            "panel_day_engine_internal_share_clean_pack_v1.md",
            "panel_day_engine_abrupt6_symptom_map_v1.csv",
            "panel_day_engine_kernellog_project_mapping_v1.csv",
            "panel_day_engine_gpv7_perf_summary_v1.csv",
            "panel_day_engine_project_progress_snapshot_v1.csv",
            "panel_day_engine_operator_pipeline_manifest_v1.csv",
            "panel_day_engine_operator_release_gate_manifest_v1.csv",
        }
        assert_true(required_artifacts.issubset(set(artifact_index_df["산출물명"])), "artifact index missing rows")

        status_snapshot_df = pd.read_csv(status_snapshot_csv, low_memory=False, encoding="utf-8-sig")
        required_status_items = {
            "현재_브랜치",
            "현재_HEAD_커밋",
            "완료된_로드맵_최대단계",
            "선택된_운영_workflow",
            "release_gate_통과여부",
            "pipeline_통과여부",
            "현재_데이터_한계",
            "최종_권장_사용_범위",
        }
        assert_true(required_status_items.issubset(set(status_snapshot_df["항목"])), "status snapshot missing rows")
        branch_value = status_snapshot_df.loc[status_snapshot_df["항목"].eq("현재_브랜치"), "값"].iloc[0]
        assert_true(branch_value == "feature/test-closeout", "unexpected branch value in status snapshot")

    after = {path: file_digest(path) for path in official_outputs}
    assert_true(before == after, "official outputs changed during smoke test")


if __name__ == "__main__":
    main()
