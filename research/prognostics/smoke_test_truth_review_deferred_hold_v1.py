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
    build_script = root / "research" / "prognostics" / "build_truth_review_deferred_hold_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_score_scope_manifest_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        share_dir.mkdir(parents=True, exist_ok=True)

        cases_df = pd.DataFrame(
            [
                {
                    "site": "alpha",
                    "panel_id": "alpha_hold_1",
                    "strict_trigger_date": "2025-03-10",
                    "scope_class": "deferred_unlabeled_high_actionability",
                    "review_priority_bucket": "high_actionability_unlabeled",
                    "priority_score": 62,
                    "critical_phenotype_v3": "electrical_fault_like",
                    "actionability_v3": "maintenance_candidate",
                },
                {
                    "site": "alpha",
                    "panel_id": "alpha_hold_2",
                    "strict_trigger_date": "2025-03-11",
                    "scope_class": "deferred_unlabeled_high_actionability",
                    "review_priority_bucket": "high_actionability_unlabeled",
                    "priority_score": 61,
                    "critical_phenotype_v3": "singleton_borderline_review",
                    "actionability_v3": "singleton_review",
                },
                {
                    "site": "gangui",
                    "panel_id": "gangui_same_scope_but_not_hold",
                    "strict_trigger_date": "2025-03-12",
                    "scope_class": "deferred_unlabeled_high_actionability",
                    "review_priority_bucket": "high_actionability_unlabeled",
                    "priority_score": 61,
                    "critical_phenotype_v3": "common_cause_borderline",
                    "actionability_v3": "common_cause_review",
                },
                {
                    "site": "beta",
                    "panel_id": "beta_manual_scored",
                    "strict_trigger_date": "2025-03-13",
                    "scope_class": "manual_scored",
                    "review_priority_bucket": "already_labeled",
                    "priority_score": 0,
                    "critical_phenotype_v3": "electrical_fault_like",
                    "actionability_v3": "maintenance_candidate",
                },
                {
                    "site": "alpha",
                    "panel_id": "alpha_deferred_other",
                    "strict_trigger_date": "2025-03-14",
                    "scope_class": "deferred_unlabeled_other",
                    "review_priority_bucket": "monitor_only_backlog",
                    "priority_score": 30,
                    "critical_phenotype_v3": "shape_only_monitor",
                    "actionability_v3": "monitor_only",
                },
            ]
        )
        original_cases_csv = cases_df.to_csv(index=False)
        cases_df.to_csv(share_dir / "score_scope_manifest_cases_v1.csv", index=False, encoding="utf-8-sig")

        sites_df = pd.DataFrame(
            [
                {
                    "site": "alpha",
                    "total_cases": 3,
                    "official_scored_count": 1,
                    "manual_scored_count": 1,
                    "vendor_scored_count": 0,
                    "deferred_unlabeled_high_actionability_count": 2,
                    "deferred_unlabeled_other_count": 1,
                    "recommended_site_handling": "score_with_deferred_note",
                },
                {
                    "site": "gangui",
                    "total_cases": 1,
                    "official_scored_count": 1,
                    "manual_scored_count": 1,
                    "vendor_scored_count": 0,
                    "deferred_unlabeled_high_actionability_count": 1,
                    "deferred_unlabeled_other_count": 0,
                    "recommended_site_handling": "continue_scoring_normally",
                },
                {
                    "site": "beta",
                    "total_cases": 1,
                    "official_scored_count": 1,
                    "manual_scored_count": 1,
                    "vendor_scored_count": 0,
                    "deferred_unlabeled_high_actionability_count": 0,
                    "deferred_unlabeled_other_count": 0,
                    "recommended_site_handling": "continue_scoring_normally",
                },
            ]
        )
        original_sites_csv = sites_df.to_csv(index=False)
        sites_df.to_csv(share_dir / "score_scope_manifest_sites_v1.csv", index=False, encoding="utf-8-sig")

        batch_df = pd.DataFrame(
            [
                {
                    "round1_review_order": 1,
                    "round1_bucket_rank": 1,
                    "site": "beta",
                    "panel_id": "urgent_case",
                    "strict_trigger_date": "2025-03-09",
                    "review_priority_bucket": "urgent_official_error_context",
                    "priority_score": 100,
                    "review_focus": "official_error_reaudit",
                    "review_checklist": "urgent checklist",
                    "recommended_review_action": "manual_reaudit_first",
                },
                {
                    "round1_review_order": 2,
                    "round1_bucket_rank": 3,
                    "site": "alpha",
                    "panel_id": "alpha_hold_1",
                    "strict_trigger_date": "2025-03-10",
                    "review_priority_bucket": "high_actionability_unlabeled",
                    "priority_score": 62,
                    "review_focus": "actionability_sanity_check",
                    "review_checklist": "high checklist",
                    "recommended_review_action": "manual_reaudit_first",
                },
                {
                    "round1_review_order": 3,
                    "round1_bucket_rank": 2,
                    "site": "beta",
                    "panel_id": "vendor_case",
                    "strict_trigger_date": "2025-03-10",
                    "review_priority_bucket": "vendor_backed_unlabeled",
                    "priority_score": 70,
                    "review_focus": "vendor_field_log_compare",
                    "review_checklist": "vendor checklist",
                    "recommended_review_action": "compare_with_vendor_and_field_logs",
                },
                {
                    "round1_review_order": 4,
                    "round1_bucket_rank": 3,
                    "site": "alpha",
                    "panel_id": "alpha_hold_2",
                    "strict_trigger_date": "2025-03-11",
                    "review_priority_bucket": "high_actionability_unlabeled",
                    "priority_score": 61,
                    "review_focus": "actionability_sanity_check",
                    "review_checklist": "high checklist",
                    "recommended_review_action": "manual_reaudit_first",
                },
                {
                    "round1_review_order": 5,
                    "round1_bucket_rank": 3,
                    "site": "gangui",
                    "panel_id": "gangui_same_scope_but_not_hold",
                    "strict_trigger_date": "2025-03-12",
                    "review_priority_bucket": "high_actionability_unlabeled",
                    "priority_score": 61,
                    "review_focus": "actionability_sanity_check",
                    "review_checklist": "high checklist",
                    "recommended_review_action": "manual_reaudit_first",
                },
            ]
        )
        original_batch_csv = batch_df.to_csv(index=False)
        batch_df.to_csv(share_dir / "truth_review_batch_v1.csv", index=False, encoding="utf-8-sig")

        run_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "alpha", "gangui", "beta"], root)
        assert_true(run_res.returncode == 0, f"script failed:\n{run_res.stdout}\n{run_res.stderr}")

        hold_df = pd.read_csv(share_dir / "truth_review_deferred_hold_v1.csv", encoding="utf-8-sig")
        active_df = pd.read_csv(share_dir / "truth_review_active_batch_v2.csv", encoding="utf-8-sig")
        summary_df = pd.read_csv(share_dir / "truth_review_deferred_summary_v1.csv", encoding="utf-8-sig")

        assert_true(not hold_df.empty, "deferred hold output is empty")
        assert_true(not active_df.empty, "active batch output is empty")
        assert_true(not summary_df.empty, "summary output is empty")

        hold_ids = hold_df["panel_id"].astype(str).tolist()
        active_ids = active_df["panel_id"].astype(str).tolist()
        assert_true(
            hold_ids == ["alpha_hold_1", "alpha_hold_2"],
            "deferred universe should come from scope + site recommendation, not a hard-coded site name",
        )
        assert_true(
            "gangui_same_scope_but_not_hold" not in hold_ids and "gangui_same_scope_but_not_hold" in active_ids,
            "same scope_class should stay active when the site recommendation is not score_with_deferred_note",
        )
        assert_true(
            active_ids == ["urgent_case", "vendor_case", "gangui_same_scope_but_not_hold"],
            "active batch v2 should exclude only deferred-hold rows and preserve original order",
        )
        assert_true(
            len(batch_df) - len(hold_df) == len(active_df),
            "original batch minus deferred count should equal active_batch_v2_count",
        )
        assert_true(
            hold_df["hold_reason"].eq("deferred_high_actionability_without_field_evidence").all()
            and hold_df["hold_status"].eq("on_hold").all()
            and hold_df["reactivation_condition"].eq("field_or_OM_evidence_available").all(),
            "hold registry should emit the fixed governance fields",
        )

        summary_row = summary_df.loc[summary_df["record_type"].eq("summary")].iloc[0]
        alpha_row = summary_df.loc[summary_df["site"].eq("alpha")].iloc[0]
        gangui_row = summary_df.loc[summary_df["site"].eq("gangui")].iloc[0]
        assert_true(int(summary_row["original_batch_count"]) == 5, "summary should capture the original batch count")
        assert_true(int(summary_row["deferred_hold_count"]) == 2, "summary should capture the deferred hold count")
        assert_true(int(summary_row["active_batch_v2_count"]) == 3, "summary should capture the active batch count")
        assert_true(int(summary_row["deferred_site_count"]) == 1, "summary should capture the deferred site count")
        assert_true(
            alpha_row["site_handling_recommendation"] == "keep_on_hold_until_field_evidence"
            and int(alpha_row["active_batch_v2_count_after_hold"]) == 0,
            "alpha should be marked as on hold with zero remaining active rows",
        )
        assert_true(
            gangui_row["site_handling_recommendation"] == "no_deferred_hold_rows"
            and int(gangui_row["active_batch_v2_count_after_hold"]) == 1,
            "gangui should keep its active row because the site recommendation is normal scoring",
        )

        current_cases_csv = pd.read_csv(
            share_dir / "score_scope_manifest_cases_v1.csv", encoding="utf-8-sig"
        ).to_csv(index=False)
        current_sites_csv = pd.read_csv(
            share_dir / "score_scope_manifest_sites_v1.csv", encoding="utf-8-sig"
        ).to_csv(index=False)
        current_batch_csv = pd.read_csv(
            share_dir / "truth_review_batch_v1.csv", encoding="utf-8-sig"
        ).to_csv(index=False)
        assert_true(current_cases_csv == original_cases_csv, "score scope cases input should remain unchanged")
        assert_true(current_sites_csv == original_sites_csv, "score scope sites input should remain unchanged")
        assert_true(current_batch_csv == original_batch_csv, "truth review batch input should remain unchanged")

        print("[OK] outputs generate")
        print("[OK] deferred universe is selected from score scope + site recommendation")
        print("[OK] active batch v2 excludes deferred rows exactly while preserving original order")
        print("[OK] original batch minus deferred count equals active_batch_v2_count")
        print("[OK] no official scoring inputs are modified")

    safe_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(safe_res.returncode == 0, f"existing safe smoke failed:\n{safe_res.stdout}\n{safe_res.stderr}")
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
