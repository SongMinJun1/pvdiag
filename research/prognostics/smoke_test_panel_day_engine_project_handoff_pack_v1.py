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
                "final_reason_ko": "structural only",
            },
            {
                "eval_scope": "step2_onset_truth",
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
                "final_reason_ko": "structural reference",
            },
            {
                "eval_scope": "step3_precursor_performance",
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "current_best_target_name": "first_cond_evt",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 1.0,
                "current_best_positive_support": 3,
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "final_usage_decision": "exploratory_only",
                "final_reason_ko": "step3 exploratory",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "current_best_target_name": "final_fault_hit_by_anchor",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 0.57,
                "current_best_positive_support": 3,
                "chosen_operational_workflow_name": "",
                "release_gate_pass_flag": 1,
                "pipeline_pass_flag": 1,
                "final_usage_decision": "exploratory_only",
                "final_reason_ko": "step4 abrupt exploratory",
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
                "final_reason_ko": "step4 common exploratory",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "current_data_decision": "workflow_proxy_only",
                "allowed_claim_strength": "workflow_claim_only",
                "current_best_target_name": "baseline_plus_discovery_cluster",
                "current_best_metric_kind": "retrospective_proxy_metric",
                "current_best_f1": 0.55,
                "current_best_positive_support": 23,
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
                "eval_scope": "step3_precursor_performance",
                "current_best_target_name": "first_cond_evt",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 1.0,
                "current_best_positive_support": 3,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "do_not_freeze",
                "acquisition_blocked_flag": 1,
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "next_allowed_action": "do_not_upgrade_without_new_truth",
                "freeze_reason_ko": "precursor is exploratory",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "current_best_target_name": "final_fault_hit_by_anchor",
                "current_best_metric_kind": "true_case_metric",
                "current_best_f1": 0.57,
                "current_best_positive_support": 3,
                "current_operational_workflow_name": "",
                "current_operational_workflow_reason_ko": "",
                "freeze_recommendation": "do_not_freeze",
                "acquisition_blocked_flag": 1,
                "current_data_decision": "exploratory_only",
                "allowed_claim_strength": "exploratory_claim_only",
                "next_allowed_action": "do_not_upgrade_without_new_truth",
                "freeze_reason_ko": "abrupt is exploratory",
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
        share / "panel_day_engine_project_eval_matrix_v1.csv",
        [
            {
                "eval_scope": "step3_precursor_performance",
                "eval_part_name": "step3",
                "metric_kind": "true_case_metric",
                "unit_type": "panel",
                "positive_set_name": "precursor",
                "negative_set_name": "other",
                "target_name": "first_cond_evt",
                "support_positive": 3,
                "support_negative": 10,
                "tp": 3,
                "fp": 0,
                "fn": 0,
                "tn": 10,
                "recall": 1.0,
                "precision": 1.0,
                "f1": 1.0,
                "note_ko": "precursor benchmark support 3",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "eval_part_name": "step4_abrupt",
                "metric_kind": "true_case_metric",
                "unit_type": "panel",
                "positive_set_name": "pure_abrupt",
                "negative_set_name": "other",
                "target_name": "final_fault_hit_by_anchor",
                "support_positive": 3,
                "support_negative": 10,
                "tp": 2,
                "fp": 1,
                "fn": 1,
                "tn": 9,
                "recall": 0.6667,
                "precision": 0.6667,
                "f1": 0.5714,
                "note_ko": "pure abrupt benchmark support 3",
            },
            {
                "eval_scope": "step4_common_cause_routing",
                "eval_part_name": "step4_common",
                "metric_kind": "true_case_metric",
                "unit_type": "panel",
                "positive_set_name": "common_cause",
                "negative_set_name": "other",
                "target_name": "breadth_marker_only",
                "support_positive": 4,
                "support_negative": 10,
                "tp": 4,
                "fp": 0,
                "fn": 0,
                "tn": 10,
                "recall": 1.0,
                "precision": 1.0,
                "f1": 1.0,
                "note_ko": "common-cause support 4",
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
        share / "panel_day_engine_project_eval_reliability_v1.csv",
        [
            {
                "eval_scope": "step3_precursor_performance",
                "target_name": "first_cond_evt",
                "metric_kind": "true_case_metric",
                "positive_support": 3,
                "negative_support": 10,
                "predicted_positive_support": 3,
                "recall": 1.0,
                "precision": 1.0,
                "f1": 1.0,
                "recall_ci_low": 0.4,
                "recall_ci_high": 1.0,
                "precision_ci_low": 0.4,
                "precision_ci_high": 1.0,
                "reliability_class": "underpowered",
                "freeze_recommendation": "do_not_freeze",
                "reliability_reason_ko": "step3 underpowered",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "target_name": "final_fault_hit_by_anchor",
                "metric_kind": "true_case_metric",
                "positive_support": 3,
                "negative_support": 10,
                "predicted_positive_support": 3,
                "recall": 0.6667,
                "precision": 0.6667,
                "f1": 0.5714,
                "recall_ci_low": 0.2,
                "recall_ci_high": 0.9,
                "precision_ci_low": 0.2,
                "precision_ci_high": 0.9,
                "reliability_class": "underpowered",
                "freeze_recommendation": "do_not_freeze",
                "reliability_reason_ko": "step4 underpowered",
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
        share / "panel_day_engine_precursor_onset_truth_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0",
                "operational_first_precursor_detected_date": "2024-11-08",
                "operational_first_precursor_marker_name": "first_cond_evt",
                "interpretive_precursor_onset_date": "2024-11-06",
                "benchmark_precursor_onset_date": "2024-11-08",
            },
            {
                "site": "ktc_ess",
                "panel_id": "70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4",
                "operational_first_precursor_detected_date": "2025-01-27",
                "operational_first_precursor_marker_name": "first_cond_evt",
                "interpretive_precursor_onset_date": "2025-01-25",
                "benchmark_precursor_onset_date": "2025-01-27",
            },
            {
                "site": "conalog",
                "panel_id": "c42997a6-5881-47e7-9035-7de8a2673b54.1.1",
                "operational_first_precursor_detected_date": "2025-02-20",
                "operational_first_precursor_marker_name": "first_cond_evt",
                "interpretive_precursor_onset_date": "2025-01-20",
                "benchmark_precursor_onset_date": "2025-03-18",
            },
        ],
        [
            "site",
            "panel_id",
            "operational_first_precursor_detected_date",
            "operational_first_precursor_marker_name",
            "interpretive_precursor_onset_date",
            "benchmark_precursor_onset_date",
        ],
    )

    panel_rows = [
        {
            "site": "conalog",
            "panel_id": "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0",
            "사건유형_ko": "전조형 고장",
            "사건유형_해석_ko": "전조형 고장",
            "최종고장양상_ko": "진행성 악화",
            "운영최초전조발견일": "2024-11-08",
            "운영최초전조마커": "first_cond_evt",
            "사건해석상전조시작일": "2024-11-06",
            "benchmark전조시작일": "2024-11-08",
            "전조평가셋편입_flag": 1,
            "급작평가셋편입_flag": 0,
            "GPVS_적용대상_ko": "적용대상",
            "GPVS_부착상태_ko": "부착",
        },
        {
            "site": "ktc_ess",
            "panel_id": "70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4",
            "사건유형_ko": "전조형 고장",
            "사건유형_해석_ko": "전조형 고장",
            "최종고장양상_ko": "진행성 악화",
            "운영최초전조발견일": "2025-01-27",
            "운영최초전조마커": "first_cond_evt",
            "사건해석상전조시작일": "2025-01-25",
            "benchmark전조시작일": "2025-01-27",
            "전조평가셋편입_flag": 1,
            "급작평가셋편입_flag": 0,
            "GPVS_적용대상_ko": "적용대상",
            "GPVS_부착상태_ko": "부착",
        },
        {
            "site": "conalog",
            "panel_id": "c42997a6-5881-47e7-9035-7de8a2673b54.1.1",
            "사건유형_ko": "전조형 고장",
            "사건유형_해석_ko": "전조형 고장",
            "최종고장양상_ko": "급격 종료",
            "운영최초전조발견일": "2025-02-20",
            "운영최초전조마커": "first_cond_evt",
            "사건해석상전조시작일": "2025-01-20",
            "benchmark전조시작일": "2025-03-18",
            "전조평가셋편입_flag": 1,
            "급작평가셋편입_flag": 0,
            "GPVS_적용대상_ko": "적용대상",
            "GPVS_부착상태_ko": "부착",
        },
    ]
    panel_rows.extend(
        [
            {
                "site": "gangui",
                "panel_id": "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7",
                "사건유형_ko": "급작 고장",
                "사건유형_해석_ko": "급작 고장",
                "최종고장양상_ko": "급작 발생",
                "운영최초전조발견일": "",
                "운영최초전조마커": "",
                "사건해석상전조시작일": "",
                "benchmark전조시작일": "",
                "전조평가셋편입_flag": 0,
                "급작평가셋편입_flag": 1,
                "GPVS_적용대상_ko": "적용대상",
                "GPVS_부착상태_ko": "부착",
            },
            {
                "site": "gangui",
                "panel_id": "bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16",
                "사건유형_ko": "급작 고장",
                "사건유형_해석_ko": "급작 고장",
                "최종고장양상_ko": "급작 발생",
                "운영최초전조발견일": "",
                "운영최초전조마커": "",
                "사건해석상전조시작일": "",
                "benchmark전조시작일": "",
                "전조평가셋편입_flag": 0,
                "급작평가셋편입_flag": 1,
                "GPVS_적용대상_ko": "적용대상",
                "GPVS_부착상태_ko": "부착",
            },
            {
                "site": "ktc_ess",
                "panel_id": "10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12",
                "사건유형_ko": "급작 고장",
                "사건유형_해석_ko": "급작 고장",
                "최종고장양상_ko": "급작 발생",
                "운영최초전조발견일": "",
                "운영최초전조마커": "",
                "사건해석상전조시작일": "",
                "benchmark전조시작일": "",
                "전조평가셋편입_flag": 0,
                "급작평가셋편입_flag": 1,
                "GPVS_적용대상_ko": "적용대상",
                "GPVS_부착상태_ko": "부착",
            },
        ]
    )
    for idx in range(19):
        panel_rows.append(
            {
                "site": "sinhyo",
                "panel_id": f"nontarget.{idx}",
                "사건유형_ko": "반복 이상",
                "사건유형_해석_ko": "반복 이상",
                "최종고장양상_ko": "해당없음",
                "운영최초전조발견일": "",
                "운영최초전조마커": "",
                "사건해석상전조시작일": "",
                "benchmark전조시작일": "",
                "전조평가셋편입_flag": 0,
                "급작평가셋편입_flag": 0,
                "GPVS_적용대상_ko": "비대상",
                "GPVS_부착상태_ko": "비대상",
            }
        )

    write_csv(
        share / "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        panel_rows,
        [
            "site",
            "panel_id",
            "사건유형_ko",
            "사건유형_해석_ko",
            "최종고장양상_ko",
            "운영최초전조발견일",
            "운영최초전조마커",
            "사건해석상전조시작일",
            "benchmark전조시작일",
            "전조평가셋편입_flag",
            "급작평가셋편입_flag",
            "GPVS_적용대상_ko",
            "GPVS_부착상태_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_operator_attention_policy_recommendation_v1.csv",
        [
            {
                "recommended_policy_name": "baseline_plus_discovery_cluster",
                "recommended_policy_reason_ko": "cluster preview가 operator load와 site skew를 더 잘 억제한다.",
                "expected_use_ko": "queue/watch baseline에 discovery cluster를 side-by-side로 붙인 기본 operator workflow",
                "caution_ko": "cluster view는 panel preview drill-down과 함께 봐야 한다.",
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
        ["final_release_gate_pass_flag", "note_ko"],
    )

    write_csv(
        share / "panel_day_engine_operator_pipeline_manifest_v1.csv",
        [
            {
                "final_pipeline_pass_flag": 1,
                "note_ko": "pipeline pass",
            }
        ],
        ["final_pipeline_pass_flag", "note_ko"],
    )


def initialize_git_repo(root: Path) -> None:
    assert_true(run(["git", "init", "-b", "feature/test-handoff"], root).returncode == 0, "git init failed")
    assert_true(run(["git", "config", "user.email", "codex@example.com"], root).returncode == 0, "git email failed")
    assert_true(run(["git", "config", "user.name", "Codex"], root).returncode == 0, "git name failed")
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    assert_true(run(["git", "add", "README.md"], root).returncode == 0, "git add failed")
    assert_true(run(["git", "commit", "-m", "fixture"], root).returncode == 0, "git commit failed")


def write_live_status_snapshot(root: Path) -> tuple[str, str]:
    branch = run(["git", "branch", "--show-current"], root).stdout.strip()
    head = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    assert_true(bool(branch), "live branch must be non-empty")
    assert_true(bool(head), "live head must be non-empty")
    write_csv(
        root / "_share/panel_day_engine_project_status_snapshot_v1.csv",
        [
            {"항목": "현재_브랜치", "값": branch, "설명_ko": "live git branch"},
            {"항목": "현재_HEAD_커밋", "값": head, "설명_ko": "live git HEAD"},
        ],
        ["항목", "값", "설명_ko"],
    )
    return branch, head


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
        initialize_git_repo(tmp_root)
        live_branch, live_head = write_live_status_snapshot(tmp_root)

        result = run([sys.executable, str(builder_path), "--root", str(tmp_root)], cwd=repo_root)
        assert_true(result.returncode == 0, f"builder failed: {result.stderr or result.stdout}")
        assert_true("missing columns" not in (result.stderr or ""), "builder stderr still mentions missing columns")
        assert_true("missing columns" not in (result.stdout or ""), "builder stdout still mentions missing columns")

        summary_df = pd.read_csv(
            tmp_root / "_share/panel_day_engine_project_handoff_summary_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )
        markdown_text = (tmp_root / "_share/panel_day_engine_project_handoff_pack_v1.md").read_text(encoding="utf-8")

        assert_true(list(summary_df.columns) == ["항목", "값", "비고_ko"], "handoff summary must keep compact row-style columns")
        for forbidden_column in [
            "eval_scope",
            "current_data_decision",
            "final_usage_decision",
            "allowed_claim_strength",
            "chosen_operational_workflow_name",
            "release_gate_pass_flag",
            "pipeline_pass_flag",
            "handoff_status_ko",
        ]:
            assert_true(forbidden_column not in summary_df.columns, f"obsolete wide-column leaked into summary: {forbidden_column}")

        summary_lookup = {
            str(row["항목"]): str(row["값"])
            for row in summary_df.to_dict(orient="records")
        }
        for metric_name, expected_value in {
            "사건해석_전조형_패널수": "3",
            "precursor_benchmark_support": "3",
            "순수급작_benchmark_support": "3",
            "common_cause_support": "4",
            "GPVS_적용대상_패널수": "6",
            "GPVS_부착수": "6",
            "GPVS_비대상_패널수": "19",
            "chosen_workflow": "baseline_plus_discovery_cluster",
            "release_gate": "1",
            "pipeline_pass": "1",
        }.items():
            assert_true(summary_lookup.get(metric_name) == expected_value, f"summary row mismatch: {metric_name}")

        for heading in [
            "## 1. 지금 확정된 기준",
            "## 2. 운영 기본값",
            "## 3. 전조/급작 읽는 법",
            "## 4. 조심해서만 말해야 하는 것",
            "## 5. 가장 먼저 볼 파일",
        ]:
            assert_true(heading in markdown_text, f"missing markdown section: {heading}")

        required_snippets = [
            "사건 해석상 전조형 고장 패널 수는 `3` 이다.",
            "전조형 benchmark support 는 `3` 이다.",
            "순수 급작 benchmark support 는 `3` 이다.",
            "공통원인 이벤트 support 는 `4` 이다.",
            "운영 기본 workflow 는 `baseline_plus_discovery_cluster` 다.",
            "release gate 는 `통과` (`1`) 이고 pipeline 도 `통과` (`1`) 다.",
            "GPVS 는 고장 패널 `6` 개에만 적용하고 현재 `6` 개 모두 부착됐다.",
            "비고장/미확정 패널 `19` 개는 GPVS 비대상이다.",
            "사건 해석, 운영 최초 전조 발견일, benchmark onset, 평가셋 편입은 같은 뜻이 아니다.",
            "c429 사건 해석 onset 은 `2025-01-20` 이고 benchmark onset 은 `2025-03-18` 이다.",
            "c429 운영 최초 전조 발견은 `2025-02-20` (`first_cond_evt`) 이다.",
            "c429 panel row의 평가셋 편입 flag 는 전조=`1`, 급작=`0` 로 분리돼 있다.",
            "handoff benchmark 보고에서는 c429를 precursor benchmark 포함, pure abrupt benchmark 제외로 읽는다.",
            "step3 precursor 와 step4 pure abrupt 는 둘 다 `underpowered` / `exploratory_only` 수준으로 유지한다.",
            f"현재 status snapshot 기준 git context 는 branch=`{live_branch}`, HEAD=`{live_head}` 다.",
        ]
        for snippet in required_snippets:
            assert_true(snippet in markdown_text, f"missing markdown snippet: {snippet}")

        forbidden_snippets = [
            "전조 2",
            "급작 6",
            "c42997 보류",
        ]
        for snippet in forbidden_snippets:
            assert_true(snippet not in markdown_text, f"stale wording leaked into markdown: {snippet}")

    after_digests = [(str(path), file_digest(path)) for path in official_outputs]
    assert_true(before_digests == after_digests, "smoke test modified official outputs")

    print("smoke_test_panel_day_engine_project_handoff_pack_v1.py: PASS")


if __name__ == "__main__":
    main()
