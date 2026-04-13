#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_score_scope_manifest_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_truth_coverage_priority_audit_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        share_dir.mkdir(parents=True, exist_ok=True)

        base_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "manual_scored_case",
                    "strict_trigger_date": "2025-03-10",
                    "candidate_validity": "true_positive",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_scored_case",
                    "strict_trigger_date": "2025-03-11",
                    "candidate_validity": "",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                },
                {
                    "site": "demo",
                    "panel_id": "deferred_high_case",
                    "strict_trigger_date": "2025-03-12",
                    "candidate_validity": "",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                },
                {
                    "site": "demo",
                    "panel_id": "deferred_other_case",
                    "strict_trigger_date": "2025-03-13",
                    "candidate_validity": "",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                },
                {
                    "site": "demo",
                    "panel_id": "needs_more_info_case",
                    "strict_trigger_date": "2025-03-14",
                    "candidate_validity": "needs_more_info",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_no_info_case",
                    "strict_trigger_date": "2025-03-15",
                    "candidate_validity": "",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                },
                {
                    "site": "demo",
                    "panel_id": "excluded_other_case",
                    "strict_trigger_date": "2025-03-16",
                    "candidate_validity": "",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                },
            ]
        )
        base_df.to_csv(share_dir / "panel_date_reaudit_working.csv", index=False, encoding="utf-8-sig")

        vendor_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "vendor_scored_case",
                    "strict_trigger_date": "2025-03-11",
                    "vendor_reply_class": "vendor_likely_positive",
                    "vendor_fault_family": "diode_like",
                },
                {
                    "site": "demo",
                    "panel_id": "needs_more_info_case",
                    "strict_trigger_date": "2025-03-14",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "electrical_fault_like",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_no_info_case",
                    "strict_trigger_date": "2025-03-15",
                    "vendor_reply_class": "vendor_no_info",
                    "vendor_fault_family": "unknown",
                },
                {
                    "site": "demo",
                    "panel_id": "excluded_other_case",
                    "strict_trigger_date": "2025-03-16",
                    "vendor_reply_class": "vendor_pending_followup",
                    "vendor_fault_family": "unknown",
                },
            ]
        )
        vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

        summary_input_df = pd.DataFrame(
            [
                {
                    "truth_mode": "strict",
                    "prediction_mode": "maintenance",
                    "source_split": "overall",
                    "scored_rows": 1,
                    "excluded_rows": 6,
                },
                {
                    "truth_mode": "strict",
                    "prediction_mode": "operational",
                    "source_split": "overall",
                    "scored_rows": 1,
                    "excluded_rows": 6,
                },
                {
                    "truth_mode": "lenient",
                    "prediction_mode": "maintenance",
                    "source_split": "overall",
                    "scored_rows": 2,
                    "excluded_rows": 5,
                },
                {
                    "truth_mode": "lenient",
                    "prediction_mode": "operational",
                    "source_split": "overall",
                    "scored_rows": 2,
                    "excluded_rows": 5,
                },
            ]
        )
        original_summary_csv = summary_input_df.to_csv(index=False)
        summary_input_df.to_csv(share_dir / "full_algorithm_f1_summary_v3.csv", index=False, encoding="utf-8-sig")

        priority_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "manual_scored_case",
                    "strict_trigger_date": "2025-03-10",
                    "review_priority_bucket": "already_labeled",
                    "priority_score": 0,
                    "recommended_review_action": "no_action_needed",
                    "critical_phenotype_v3": "electrical_fault_like",
                    "actionability_v3": "maintenance_candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_scored_case",
                    "strict_trigger_date": "2025-03-11",
                    "review_priority_bucket": "vendor_backed_unlabeled",
                    "priority_score": 70,
                    "recommended_review_action": "compare_with_vendor_and_field_logs",
                    "critical_phenotype_v3": "electrical_fault_like",
                    "actionability_v3": "maintenance_candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "deferred_high_case",
                    "strict_trigger_date": "2025-03-12",
                    "review_priority_bucket": "high_actionability_unlabeled",
                    "priority_score": 61,
                    "recommended_review_action": "manual_reaudit_first",
                    "critical_phenotype_v3": "singleton_borderline_review",
                    "actionability_v3": "singleton_review",
                },
                {
                    "site": "demo",
                    "panel_id": "deferred_other_case",
                    "strict_trigger_date": "2025-03-13",
                    "review_priority_bucket": "monitor_only_backlog",
                    "priority_score": 30,
                    "recommended_review_action": "defer_until_backlog_review",
                    "critical_phenotype_v3": "shape_only_monitor",
                    "actionability_v3": "monitor_only",
                },
                {
                    "site": "demo",
                    "panel_id": "needs_more_info_case",
                    "strict_trigger_date": "2025-03-14",
                    "review_priority_bucket": "already_labeled",
                    "priority_score": 0,
                    "recommended_review_action": "no_action_needed",
                    "critical_phenotype_v3": "electrical_fault_like",
                    "actionability_v3": "maintenance_candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_no_info_case",
                    "strict_trigger_date": "2025-03-15",
                    "review_priority_bucket": "vendor_backed_unlabeled",
                    "priority_score": 70,
                    "recommended_review_action": "compare_with_vendor_and_field_logs",
                    "critical_phenotype_v3": "common_cause_borderline",
                    "actionability_v3": "common_cause_review",
                },
                {
                    "site": "demo",
                    "panel_id": "excluded_other_case",
                    "strict_trigger_date": "2025-03-16",
                    "review_priority_bucket": "vendor_backed_unlabeled",
                    "priority_score": 70,
                    "recommended_review_action": "compare_with_vendor_and_field_logs",
                    "critical_phenotype_v3": "common_cause_borderline",
                    "actionability_v3": "common_cause_review",
                },
            ]
        )
        original_priority_csv = priority_df.to_csv(index=False)
        priority_df.to_csv(share_dir / "truth_coverage_priority_cases_v1.csv", index=False, encoding="utf-8-sig")

        batch_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "deferred_high_case",
                    "strict_trigger_date": "2025-03-12",
                    "review_priority_bucket": "high_actionability_unlabeled",
                }
            ]
        )
        batch_df.to_csv(share_dir / "truth_review_batch_v1.csv", index=False, encoding="utf-8-sig")

        run_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(run_res.returncode == 0, f"script failed:\n{run_res.stdout}\n{run_res.stderr}")

        summary_df = pd.read_csv(share_dir / "score_scope_manifest_summary_v1.csv", encoding="utf-8-sig")
        sites_df = pd.read_csv(share_dir / "score_scope_manifest_sites_v1.csv", encoding="utf-8-sig")
        cases_df = pd.read_csv(share_dir / "score_scope_manifest_cases_v1.csv", encoding="utf-8-sig")

        assert_true(not summary_df.empty, "summary output is empty")
        assert_true(not sites_df.empty, "site output is empty")
        assert_true(not cases_df.empty, "case output is empty")
        assert_true(len(cases_df) == len(base_df), "strict-case universe should be preserved exactly")

        manual_row = cases_df.loc[cases_df["panel_id"].eq("manual_scored_case")].iloc[0]
        vendor_row = cases_df.loc[cases_df["panel_id"].eq("vendor_scored_case")].iloc[0]
        deferred_row = cases_df.loc[cases_df["panel_id"].eq("deferred_high_case")].iloc[0]
        needs_more_info_row = cases_df.loc[cases_df["panel_id"].eq("needs_more_info_case")].iloc[0]
        vendor_no_info_row = cases_df.loc[cases_df["panel_id"].eq("vendor_no_info_case")].iloc[0]
        excluded_other_row = cases_df.loc[cases_df["panel_id"].eq("excluded_other_case")].iloc[0]

        assert_true(
            manual_row["scope_class"] == "manual_scored" and int(manual_row["official_scored_flag"]) == 1,
            "synthetic manual truth row should become manual_scored and stay officially scored",
        )
        assert_true(
            vendor_row["scope_class"] == "vendor_scored" and int(vendor_row["official_scored_flag"]) == 1,
            "synthetic vendor truth row should become vendor_scored and stay officially scored",
        )
        assert_true(
            deferred_row["scope_class"] == "deferred_unlabeled_high_actionability"
            and int(deferred_row["official_scored_flag"]) == 0,
            "synthetic high-actionability unlabeled row should remain deferred_unlabeled_high_actionability",
        )
        assert_true(
            needs_more_info_row["scope_class"] == "excluded_labeled_needs_more_info"
            and int(needs_more_info_row["official_scored_flag"]) == 0,
            "needs_more_info row should stay excluded despite vendor context",
        )
        assert_true(
            vendor_no_info_row["scope_class"] == "excluded_vendor_no_info"
            and int(vendor_no_info_row["official_scored_flag"]) == 0,
            "vendor_no_info row should stay excluded from official scoring",
        )
        assert_true(
            excluded_other_row["scope_class"] == "excluded_other"
            and int(excluded_other_row["official_scored_flag"]) == 0,
            "unknown vendor label row should fall into excluded_other",
        )
        assert_true(
            int(deferred_row["in_truth_review_batch_v1_flag"]) == 1,
            "deferred high-actionability row should be tagged as present in truth_review_batch_v1",
        )

        expected_scored = cases_df["scope_class"].isin({"manual_scored", "vendor_scored"}).astype(int)
        assert_true(
            cases_df["official_scored_flag"].astype(int).eq(expected_scored).all(),
            "official_scored_flag should match the scope classification logic",
        )

        summary_row = summary_df.loc[summary_df["record_type"].eq("summary")].iloc[0]
        site_row = sites_df.loc[sites_df["site"].eq("demo")].iloc[0]
        assert_true(int(summary_row["official_scored_count"]) == 2, "summary should count 2 officially scored rows")
        assert_true(int(summary_row["manual_scored_count"]) == 1, "summary should count 1 manual_scored row")
        assert_true(int(summary_row["vendor_scored_count"]) == 1, "summary should count 1 vendor_scored row")
        assert_true(
            int(summary_row["deferred_unlabeled_high_actionability_count"]) == 1,
            "summary should count 1 deferred high-actionability row",
        )
        assert_true(
            site_row["recommended_site_handling"] == "score_with_deferred_note",
            "site handling should keep scoring while explicitly noting deferred rows",
        )

        current_summary_csv = pd.read_csv(share_dir / "full_algorithm_f1_summary_v3.csv", encoding="utf-8-sig").to_csv(
            index=False
        )
        current_priority_csv = pd.read_csv(
            share_dir / "truth_coverage_priority_cases_v1.csv", encoding="utf-8-sig"
        ).to_csv(index=False)
        assert_true(
            current_summary_csv == original_summary_csv,
            "official evaluation summary input should remain unchanged",
        )
        assert_true(
            current_priority_csv == original_priority_csv,
            "truth coverage priority input should remain unchanged",
        )

        print("[OK] outputs generate")
        print("[OK] strict-case universe is preserved exactly")
        print("[OK] synthetic manual_scored / vendor_scored / deferred_unlabeled_high_actionability cases classify correctly")
        print("[OK] official_scored_flag matches scope logic")
        print("[OK] no official evaluation inputs are modified")

    safe_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(safe_res.returncode == 0, f"existing safe smoke failed:\n{safe_res.stdout}\n{safe_res.stderr}")
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
