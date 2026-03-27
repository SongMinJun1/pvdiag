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
    build_script = root / "research" / "prognostics" / "build_truth_review_evidence_pack_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_truth_review_intake_preview_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        share_dir.mkdir(parents=True, exist_ok=True)

        batch_df = pd.DataFrame(
            [
                {
                    "round1_review_order": 1,
                    "round1_bucket_rank": 1,
                    "site": "demo",
                    "panel_id": "official_case",
                    "strict_trigger_date": "2025-03-10",
                    "review_priority_bucket": "urgent_official_error_context",
                    "priority_score": 105,
                    "review_focus": "official_error_reaudit",
                    "recommended_review_action": "manual_reaudit_first",
                    "review_checklist": "official checklist",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "group_or_inverter_side_like",
                    "critical_phenotype_v3": "singleton_borderline_review",
                    "actionability_v3": "singleton_review",
                    "official_error_modes": "strict:maintenance",
                    "official_error_types": "fn",
                    "prediction_source": "confirmed_fault_clean",
                    "gap_bucket": "clean_confirmed_fault_review_gap",
                    "promotion_hypothesis": "candidate_for_maintenance_shadow",
                    "review_priority": "P1",
                    "note": "official note",
                    "vendor_note": "field confirmation",
                },
                {
                    "round1_review_order": 2,
                    "round1_bucket_rank": 2,
                    "site": "demo",
                    "panel_id": "vendor_case",
                    "strict_trigger_date": "2025-03-11",
                    "review_priority_bucket": "vendor_backed_unlabeled",
                    "priority_score": 75,
                    "review_focus": "vendor_field_log_compare",
                    "recommended_review_action": "compare_with_vendor_and_field_logs",
                    "review_checklist": "vendor checklist",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "diode_like",
                    "critical_phenotype_v3": "electrical_fault_like",
                    "actionability_v3": "maintenance_candidate",
                    "official_error_modes": "",
                    "official_error_types": "",
                    "prediction_source": "",
                    "gap_bucket": "",
                    "promotion_hypothesis": "",
                    "review_priority": "P1",
                    "note": "vendor compare note",
                    "vendor_note": "vendor pattern",
                },
                {
                    "round1_review_order": 3,
                    "round1_bucket_rank": 3,
                    "site": "demo",
                    "panel_id": "action_case",
                    "strict_trigger_date": "2025-03-12",
                    "review_priority_bucket": "high_actionability_unlabeled",
                    "priority_score": 61,
                    "review_focus": "actionability_sanity_check",
                    "recommended_review_action": "manual_reaudit_first",
                    "review_checklist": "actionability checklist",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "critical_phenotype_v3": "common_cause_borderline",
                    "actionability_v3": "common_cause_review",
                    "official_error_modes": "",
                    "official_error_types": "",
                    "prediction_source": "",
                    "gap_bucket": "",
                    "promotion_hypothesis": "",
                    "review_priority": "P2",
                    "note": "action note",
                    "vendor_note": "",
                },
            ]
        )
        original_batch_csv = batch_df.to_csv(index=False)
        batch_df.to_csv(share_dir / "truth_review_batch_v1.csv", index=False, encoding="utf-8-sig")

        priority_cases_df = batch_df.loc[:, [
            "site",
            "panel_id",
            "strict_trigger_date",
            "vendor_reply_class",
            "vendor_fault_family",
            "critical_phenotype_v3",
            "actionability_v3",
            "note",
            "vendor_note",
        ]].copy()
        priority_cases_df.to_csv(share_dir / "truth_coverage_priority_cases_v1.csv", index=False, encoding="utf-8-sig")

        actionability_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "official_case",
                    "strict_trigger_date": "2025-03-10",
                    "anchor_date": "2025-03-09",
                    "critical_phenotype_v2": "borderline_electrical_review",
                    "critical_phenotype_v3": "singleton_borderline_review",
                    "cluster_guard_flag": 0,
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_case",
                    "strict_trigger_date": "2025-03-11",
                    "anchor_date": "2025-03-11",
                    "critical_phenotype_v2": "electrical_fault_like",
                    "critical_phenotype_v3": "electrical_fault_like",
                    "cluster_guard_flag": 0,
                },
                {
                    "site": "demo",
                    "panel_id": "action_case",
                    "strict_trigger_date": "2025-03-12",
                    "anchor_date": "2025-03-12",
                    "critical_phenotype_v2": "common_cause_borderline",
                    "critical_phenotype_v3": "common_cause_borderline",
                    "cluster_guard_flag": 1,
                },
            ]
        )
        actionability_df.to_csv(share_dir / "critical_actionability_shadow_v3_latest.csv", index=False, encoding="utf-8-sig")

        onset_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "official_case",
                    "strict_trigger_date": "2025-03-10",
                    "first_warning_date": "2025-03-07",
                    "retrospective_onset_date": "2025-03-05",
                    "days_earlier_than_trigger": 5,
                    "onset_confidence": "high",
                    "onset_method": "persistent_5of7",
                    "reason_summary": "confirmed fault onset",
                },
                {
                    "site": "demo",
                    "panel_id": "action_case",
                    "strict_trigger_date": "2025-03-12",
                    "first_warning_date": "2025-03-11",
                    "retrospective_onset_date": "2025-03-10",
                    "days_earlier_than_trigger": 2,
                    "onset_confidence": "medium",
                    "onset_method": "strict_trigger_fallback",
                    "reason_summary": "borderline cluster onset",
                },
            ]
        )
        onset_df.to_csv(share_dir / "panel_onset_shadow_latest.csv", index=False, encoding="utf-8-sig")

        errors_df = pd.DataFrame(
            [
                {
                    "truth_mode": "strict",
                    "prediction_mode": "maintenance",
                    "source_split": "overall",
                    "site": "demo",
                    "panel_id": "official_case",
                    "strict_trigger_date": "2025-03-10",
                    "error_type": "fn",
                    "prediction_source": "confirmed_fault_clean",
                }
            ]
        )
        errors_df.to_csv(share_dir / "full_algorithm_case_errors_v3.csv", index=False, encoding="utf-8-sig")

        vendor_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "vendor_case",
                    "strict_trigger_date": "2025-03-11",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "diode_like",
                    "vendor_note": "vendor says diode-like",
                }
            ]
        )
        vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

        precursor_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "date": "2025-03-12",
                    "site_recommendation": "keep_site_specific_precursor_note",
                    "forensic_hypothesis": "plausible_precursor_day",
                    "include_in_site_specific_note_flag": 1,
                }
            ]
        )
        precursor_df.to_csv(
            share_dir / "common_cause_precursor_decision_cases_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )

        run_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(run_res.returncode == 0, f"script failed:\n{run_res.stdout}\n{run_res.stderr}")

        evidence_df = pd.read_csv(share_dir / "truth_review_evidence_pack_v1.csv", encoding="utf-8-sig")
        packets_df = pd.read_csv(share_dir / "truth_review_site_packets_detailed_v1.csv", encoding="utf-8-sig")
        prompts_df = pd.read_csv(share_dir / "truth_review_case_prompts_v1.csv", encoding="utf-8-sig")

        assert_true(not evidence_df.empty, "evidence pack output is empty")
        assert_true(not packets_df.empty, "site packets output is empty")
        assert_true(not prompts_df.empty, "case prompts output is empty")
        assert_true(len(evidence_df) == len(batch_df), "round-1 universe should be preserved exactly")
        assert_true(len(prompts_df) == len(batch_df), "case prompts should preserve the round-1 universe exactly")

        official_row = evidence_df.loc[evidence_df["panel_id"].eq("official_case")].iloc[0]
        assert_true(
            official_row["candidate_validity_review_axis"] == "panel_issue_vs_group_side_vs_false_positive"
            and official_row["date_judgement_review_axis"] == "strict_trigger_vs_onset_context",
            "official_error_reaudit rows should get the expected review axes",
        )

        vendor_row = evidence_df.loc[evidence_df["panel_id"].eq("vendor_case")].iloc[0]
        assert_true(
            vendor_row["candidate_validity_review_axis"] == "vendor_log_reconcile"
            and vendor_row["date_judgement_review_axis"] == "strict_trigger_only",
            "vendor_field_log_compare rows should get the expected review axes",
        )

        action_row = evidence_df.loc[evidence_df["panel_id"].eq("action_case")].iloc[0]
        assert_true(
            action_row["candidate_validity_review_axis"] == "actionability_consistency"
            and action_row["date_judgement_review_axis"] == "strict_trigger_vs_onset_context",
            "actionability_sanity_check rows should get the expected review axes",
        )

        assert_true(
            evidence_df["evidence_summary_ko"].fillna("").str.strip().ne("").all()
            and evidence_df["review_question_ko"].fillna("").str.strip().ne("").all(),
            "evidence_summary_ko and review_question_ko should be nonblank for populated rows",
        )

        current_batch_csv = pd.read_csv(
            share_dir / "truth_review_batch_v1.csv",
            encoding="utf-8-sig",
        ).to_csv(index=False)
        assert_true(current_batch_csv == original_batch_csv, "official batch input should remain unchanged")

        print("[OK] outputs generate")
        print("[OK] round-1 universe is preserved exactly")
        print("[OK] official_error_reaudit rows get the expected review axes")
        print("[OK] vendor_field_log_compare rows get the expected review axes")
        print("[OK] actionability_sanity_check rows get the expected review axes")
        print("[OK] evidence_summary_ko and review_question_ko are nonblank for populated rows")
        print("[OK] no official outputs are modified")

    safe_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(safe_res.returncode == 0, f"existing safe smoke failed:\n{safe_res.stdout}\n{safe_res.stderr}")
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
