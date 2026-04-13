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
                "reliability_reason_ko": "structural",
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
                "reliability_reason_ko": "proxy",
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
            {"site": "alpha", "panel_id": "P1", "fault_start_date": "2026-01-01"},
        ],
        ["site", "panel_id", "fault_start_date"],
    )
    write_csv(
        share / "panel_day_engine_precursor_performance_cases_v1.csv",
        [
            {"site": "alpha", "panel_id": "P1", "fault_start_date": "2026-01-01"},
        ],
        ["site", "panel_id", "fault_start_date"],
    )
    write_csv(
        share / "panel_day_engine_local_precursor_eligibility_cases_v1.csv",
        [
            {"site": "alpha", "panel_id": "P1", "fault_start_date": "2026-01-01", "precursor_eligible_flag": 1},
            {"site": "alpha", "panel_id": "P2", "fault_start_date": "2026-01-02", "precursor_eligible_flag": 1},
            {"site": "alpha", "panel_id": "P3", "fault_start_date": "2026-01-03", "precursor_eligible_flag": 1},
            {"site": "alpha", "panel_id": "P4", "fault_start_date": "2026-01-04", "precursor_eligible_flag": 0},
        ],
        ["site", "panel_id", "fault_start_date", "precursor_eligible_flag"],
    )
    write_csv(
        share / "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv",
        [
            {"fault_family_id": "electrical_fault_like_progressive_local", "eval_bucket_v2": "precursor_bearing_detectable_now"},
            {"fault_family_id": "electrical_fault_like_abrupt_local", "eval_bucket_v2": "abrupt_or_no_precursor_now"},
            {"fault_family_id": "electrical_fault_like_unknown_local_temporality", "eval_bucket_v2": "unknown_needs_review"},
            {"fault_family_id": "group_or_inverter_side_like", "eval_bucket_v2": "non_panel_or_common_cause"},
            {"fault_family_id": "none_visible_or_unconfirmed", "eval_bucket_v2": "abrupt_or_no_precursor_now"},
        ],
        ["fault_family_id", "eval_bucket_v2"],
    )
    write_csv(
        share / "panel_day_engine_non_precursor_performance_cases_v1.csv",
        [
            {"eval_bucket_v2": "abrupt_or_no_precursor_now", "site": "alpha", "panel_id": "A1", "anchor_date": "2026-02-01", "truth_case_id": "reaudit|alpha|A1|2026-02-01"},
            {"eval_bucket_v2": "abrupt_or_no_precursor_now", "site": "alpha", "panel_id": "A2", "anchor_date": "2026-02-02", "truth_case_id": "eligibility|alpha|A2|2026-02-02"},
            {"eval_bucket_v2": "non_panel_or_common_cause", "site": "alpha", "panel_id": "C1", "anchor_date": "2026-03-01", "truth_case_id": "reaudit|alpha|C1|2026-03-01"},
        ],
        ["eval_bucket_v2", "site", "panel_id", "anchor_date", "truth_case_id"],
    )
    write_csv(
        share / "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv",
        [
            {"eval_bucket_v2": "non_panel_or_common_cause", "site": "alpha", "panel_id": "C1", "anchor_date": "2026-03-01", "truth_case_id": "reaudit|alpha|C1|2026-03-01"},
            {"eval_bucket_v2": "abrupt_or_no_precursor_now", "site": "alpha", "panel_id": "A1", "anchor_date": "2026-02-01", "truth_case_id": "reaudit|alpha|A1|2026-02-01"},
        ],
        ["eval_bucket_v2", "site", "panel_id", "anchor_date", "truth_case_id"],
    )
    write_csv(
        share / "panel_date_reaudit_working.csv",
        [
            {"site": "alpha", "panel_id": "A1", "strict_trigger_date": "2026-02-01", "vendor_fault_family": "none_visible", "candidate_validity": "false_positive"},
            {"site": "alpha", "panel_id": "A3", "strict_trigger_date": "2026-02-03", "vendor_fault_family": "none_visible", "candidate_validity": "needs_more_info"},
            {"site": "alpha", "panel_id": "C1", "strict_trigger_date": "2026-03-01", "vendor_fault_family": "group_or_inverter_side_like", "candidate_validity": "group_side"},
            {"site": "alpha", "panel_id": "C2", "strict_trigger_date": "2026-03-02", "vendor_fault_family": "group_or_inverter_side_like", "candidate_validity": "group_side"},
        ],
        ["site", "panel_id", "strict_trigger_date", "vendor_fault_family", "candidate_validity"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder_path = repo_root / "research/prognostics/build_panel_day_engine_project_eval_support_gap_audit_v1.py"
    builder_mod = load_module(builder_path, "project_eval_support_gap_builder")

    official_paths = [
        repo_root / "_share" / "panel_day_engine_project_eval_support_gap_v1.csv",
        repo_root / "_share" / "panel_day_engine_project_eval_support_gap_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_project_eval_support_gap_candidates_v1.csv",
    ]
    official_digests_before = {path: file_digest(path) for path in official_paths}

    py_compile.compile(str(builder_path), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="project_eval_support_gap_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture(tmp_root)
        result = run([sys.executable, str(builder_path), "--root", str(tmp_root)], repo_root)
        assert_true(result.returncode == 0, result.stderr or result.stdout)

        gap = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_eval_support_gap_v1.csv",
            encoding="utf-8-sig",
        )
        summary = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_eval_support_gap_summary_v1.csv",
            encoding="utf-8-sig",
        )
        candidates = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_eval_support_gap_candidates_v1.csv",
            encoding="utf-8-sig",
        )

        assert_true(gap.columns.tolist() == builder_mod.SUPPORT_GAP_COLS, "support gap schema mismatch")
        assert_true(summary.columns.tolist() == builder_mod.SUPPORT_GAP_SUMMARY_COLS, "support gap summary schema mismatch")
        assert_true(candidates.columns.tolist() == builder_mod.CANDIDATE_COLS, "candidate schema mismatch")

        step3_row = gap.loc[gap["eval_scope"].astype(str).eq("step3_precursor_performance")].iloc[0]
        assert_true(int(step3_row["current_positive_support"]) == 2, "step3 current_positive_support mismatch")
        assert_true(int(step3_row["additional_positive_needed_for_5"]) == 3, "step3 support gap to 5 mismatch")
        assert_true(int(step3_row["additional_positive_needed_for_10"]) == 8, "step3 support gap to 10 mismatch")
        assert_true(int(step3_row["current_artifact_candidate_pool_count"]) == 2, "step3 pool count mismatch")
        assert_true(int(step3_row["can_reach_5_with_current_artifacts_flag"]) == 0, "step3 reach 5 mismatch")
        assert_true(int(step3_row["can_reach_10_with_current_artifacts_flag"]) == 0, "step3 reach 10 mismatch")

        step4a_row = gap.loc[gap["eval_scope"].astype(str).eq("step4_abrupt_no_precursor")].iloc[0]
        assert_true(int(step4a_row["current_positive_support"]) == 6, "step4A current_positive_support mismatch")
        assert_true(int(step4a_row["additional_positive_needed_for_5"]) == 0, "step4A support gap to 5 mismatch")
        assert_true(int(step4a_row["additional_positive_needed_for_10"]) == 4, "step4A support gap to 10 mismatch")
        assert_true(int(step4a_row["current_artifact_candidate_pool_count"]) == 1, "step4A pool count mismatch")
        assert_true(int(step4a_row["can_reach_5_with_current_artifacts_flag"]) == 1, "step4A reach 5 mismatch")
        assert_true(int(step4a_row["can_reach_10_with_current_artifacts_flag"]) == 0, "step4A reach 10 mismatch")

        step4b_row = gap.loc[gap["eval_scope"].astype(str).eq("step4_common_cause_routing")].iloc[0]
        assert_true(int(step4b_row["current_positive_support"]) == 4, "step4B current_positive_support mismatch")
        assert_true(int(step4b_row["additional_positive_needed_for_5"]) == 1, "step4B support gap to 5 mismatch")
        assert_true(int(step4b_row["additional_positive_needed_for_10"]) == 6, "step4B support gap to 10 mismatch")
        assert_true(int(step4b_row["current_artifact_candidate_pool_count"]) == 1, "step4B pool count mismatch")
        assert_true(int(step4b_row["can_reach_5_with_current_artifacts_flag"]) == 1, "step4B reach 5 mismatch")
        assert_true(int(step4b_row["can_reach_10_with_current_artifacts_flag"]) == 0, "step4B reach 10 mismatch")

        proxy_row = gap.loc[gap["eval_scope"].astype(str).eq("operator_policy_proxy")].iloc[0]
        assert_true(pd.isna(proxy_row["current_artifact_candidate_pool_count"]), "proxy pool count should be blank")
        assert_true(pd.isna(proxy_row["can_reach_5_with_current_artifacts_flag"]), "proxy reach flag should be blank")

        structural_row = gap.loc[gap["eval_scope"].astype(str).eq("step1_taxonomy")].iloc[0]
        assert_true(pd.isna(structural_row["current_artifact_candidate_pool_count"]), "structural pool count should be blank")

        assert_true(
            int(candidates.loc[candidates["eval_scope"].astype(str).eq("step3_precursor_performance")].shape[0]) == 2,
            "step3 candidate exclusion logic mismatch",
        )
        assert_true(
            "P1" not in set(candidates.loc[candidates["eval_scope"].astype(str).eq("step3_precursor_performance"), "panel_id"].astype(str)),
            "step3 candidate pool should exclude onset truth rows",
        )
        assert_true(
            "A1" not in set(candidates.loc[candidates["eval_scope"].astype(str).eq("step4_abrupt_no_precursor"), "panel_id"].astype(str)),
            "step4A candidate pool should exclude already counted abrupt rows",
        )
        assert_true(
            "C1" not in set(candidates.loc[candidates["eval_scope"].astype(str).eq("step4_common_cause_routing"), "panel_id"].astype(str)),
            "step4B candidate pool should exclude already counted common-cause rows",
        )

        summary_step4b = summary.loc[summary["eval_scope"].astype(str).eq("step4_common_cause_routing")].iloc[0]
        assert_true(int(summary_step4b["focused_target_count"]) == 1, "summary focused_target_count mismatch")
        assert_true(int(summary_step4b["underpowered_target_count"]) == 1, "summary underpowered_target_count mismatch")
        assert_true(int(summary_step4b["total_current_artifact_candidate_pool_count"]) == 1, "summary pool count mismatch")
        assert_true(int(summary_step4b["any_scope_can_reach_5_with_current_artifacts_flag"]) == 1, "summary reach 5 mismatch")
        assert_true(int(summary_step4b["any_scope_can_reach_10_with_current_artifacts_flag"]) == 0, "summary reach 10 mismatch")

    official_digests_after = {path: file_digest(path) for path in official_paths}
    assert_true(
        official_digests_after == official_digests_before,
        "smoke test must not modify official project eval support-gap outputs under repository _share",
    )

    print("smoke_test_panel_day_engine_project_eval_support_gap_audit_v1.py: PASS")


if __name__ == "__main__":
    main()
