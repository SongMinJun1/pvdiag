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
    build_script = root / "research" / "prognostics" / "build_truth_coverage_priority_audit_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_common_cause_precursor_decision_pack_v1.py"

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
                    "panel_id": "official_error_case",
                    "strict_trigger_date": "2025-03-10",
                    "candidate_validity": "",
                    "review_priority": "P1",
                    "note": "official error row",
                },
                {
                    "site": "demo",
                    "panel_id": "maintenance_gap_case",
                    "strict_trigger_date": "2025-03-11",
                    "candidate_validity": "",
                    "review_priority": "P1",
                    "note": "maintenance gap row",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_backed_case",
                    "strict_trigger_date": "2025-03-12",
                    "candidate_validity": "",
                    "review_priority": "P2",
                    "note": "vendor-backed row",
                },
                {
                    "site": "demo",
                    "panel_id": "already_labeled_case",
                    "strict_trigger_date": "2025-03-13",
                    "candidate_validity": "true_positive",
                    "review_priority": "P2",
                    "note": "already labeled row",
                },
            ]
        )
        base_df.to_csv(share_dir / "panel_date_reaudit_working.csv", index=False, encoding="utf-8-sig")

        vendor_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "vendor_backed_case",
                    "strict_trigger_date": "2025-03-12",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "group_or_inverter_side_like",
                    "vendor_note": "vendor backed",
                },
                {
                    "site": "demo",
                    "panel_id": "already_labeled_case",
                    "strict_trigger_date": "2025-03-13",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "diode_like",
                    "vendor_note": "already labeled vendor note",
                },
            ]
        )
        vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

        actionability_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "official_error_case",
                    "strict_trigger_date": "2025-03-10",
                    "critical_phenotype_v3": "singleton_borderline_review",
                    "actionability_v3": "singleton_review",
                },
                {
                    "site": "demo",
                    "panel_id": "maintenance_gap_case",
                    "strict_trigger_date": "2025-03-11",
                    "critical_phenotype_v3": "singleton_borderline_review",
                    "actionability_v3": "singleton_review",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_backed_case",
                    "strict_trigger_date": "2025-03-12",
                    "critical_phenotype_v3": "group_common_cause",
                    "actionability_v3": "",
                },
                {
                    "site": "demo",
                    "panel_id": "already_labeled_case",
                    "strict_trigger_date": "2025-03-13",
                    "critical_phenotype_v3": "electrical_fault_like",
                    "actionability_v3": "maintenance_candidate",
                },
            ]
        )
        original_actionability_csv = actionability_df.to_csv(index=False)
        actionability_df.to_csv(
            share_dir / "critical_actionability_shadow_v3_latest.csv",
            index=False,
            encoding="utf-8-sig",
        )

        errors_df = pd.DataFrame(
            [
                {
                    "truth_mode": "strict",
                    "prediction_mode": "maintenance",
                    "source_split": "overall",
                    "site": "demo",
                    "panel_id": "official_error_case",
                    "strict_trigger_date": "2025-03-10",
                    "error_type": "fn",
                    "prediction_source": "confirmed_fault_clean",
                },
                {
                    "truth_mode": "lenient",
                    "prediction_mode": "maintenance",
                    "source_split": "overall",
                    "site": "demo",
                    "panel_id": "official_error_case",
                    "strict_trigger_date": "2025-03-10",
                    "error_type": "fn",
                    "prediction_source": "confirmed_fault_clean",
                },
            ]
        )
        errors_df.to_csv(share_dir / "full_algorithm_case_errors_v3.csv", index=False, encoding="utf-8-sig")

        maintenance_gap_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "maintenance_gap_case",
                    "strict_trigger_date": "2025-03-11",
                    "gap_bucket": "clean_confirmed_fault_review_gap",
                    "promotion_hypothesis": "candidate_for_maintenance_shadow",
                }
            ]
        )
        maintenance_gap_df.to_csv(share_dir / "maintenance_gap_audit_cases_v1.csv", index=False, encoding="utf-8-sig")

        precursor_cases_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "date": "2025-03-12",
                    "matched_episode_id": "ep1",
                    "matched_trigger_mode": "medium_or_higher",
                    "matched_episode_start_date": "2025-03-14",
                    "days_to_episode_start": 2,
                    "precursor_timing_type": "lead_1_to_3_days",
                    "forensic_hypothesis": "plausible_precursor_day",
                    "site_recommendation": "keep_site_specific_precursor_note",
                    "include_in_site_specific_note_flag": 1,
                }
            ]
        )
        precursor_cases_df.to_csv(
            share_dir / "common_cause_precursor_decision_cases_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )

        precursor_sites_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "candidate_day_count": 1,
                    "plausible_precursor_day_count": 1,
                    "episode_aligned_day_count": 0,
                    "likely_persistent_site_pattern_count": 0,
                    "likely_sparse_site_pattern_count": 0,
                    "ambiguous_case_count": 0,
                    "site_recommendation": "keep_site_specific_precursor_note",
                    "site_decision_reason": "context only",
                }
            ]
        )
        precursor_sites_df.to_csv(
            share_dir / "common_cause_precursor_decision_sites_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )

        run_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(run_res.returncode == 0, f"script failed:\n{run_res.stdout}\n{run_res.stderr}")

        summary_df = pd.read_csv(share_dir / "truth_coverage_priority_summary_v1.csv", encoding="utf-8-sig")
        cases_df = pd.read_csv(share_dir / "truth_coverage_priority_cases_v1.csv", encoding="utf-8-sig")
        queue_df = pd.read_csv(share_dir / "truth_coverage_site_review_queue_v1.csv", encoding="utf-8-sig")

        assert_true(not summary_df.empty, "summary output is empty")
        assert_true(not cases_df.empty, "case output is empty")
        assert_true(not queue_df.empty, "site queue output is empty")
        assert_true(len(cases_df) == len(base_df), "base strict-case universe should be preserved exactly")

        official_row = cases_df.loc[cases_df["panel_id"].eq("official_error_case")].iloc[0]
        assert_true(
            official_row["review_priority_bucket"] == "urgent_official_error_context",
            "synthetic official-error unlabeled row should become urgent_official_error_context",
        )

        maintenance_row = cases_df.loc[cases_df["panel_id"].eq("maintenance_gap_case")].iloc[0]
        assert_true(
            maintenance_row["review_priority_bucket"] == "maintenance_definition_gap",
            "synthetic maintenance-gap row should become maintenance_definition_gap",
        )

        vendor_row = cases_df.loc[cases_df["panel_id"].eq("vendor_backed_case")].iloc[0]
        assert_true(
            vendor_row["review_priority_bucket"] == "vendor_backed_unlabeled",
            "synthetic vendor-backed unlabeled row should become vendor_backed_unlabeled",
        )

        labeled_row = cases_df.loc[cases_df["panel_id"].eq("already_labeled_case")].iloc[0]
        assert_true(
            labeled_row["review_priority_bucket"] == "already_labeled",
            "synthetic already-labeled row should become already_labeled",
        )

        current_actionability_csv = pd.read_csv(
            share_dir / "critical_actionability_shadow_v3_latest.csv",
            encoding="utf-8-sig",
        ).to_csv(index=False)
        assert_true(
            current_actionability_csv == original_actionability_csv,
            "official actionability output should remain unchanged",
        )

        print("[OK] outputs generate")
        print("[OK] base strict-case universe is preserved exactly")
        print("[OK] synthetic official-error unlabeled row becomes urgent_official_error_context")
        print("[OK] synthetic maintenance-gap row becomes maintenance_definition_gap")
        print("[OK] synthetic vendor-backed unlabeled row becomes vendor_backed_unlabeled")
        print("[OK] synthetic already-labeled row becomes already_labeled")
        print("[OK] no official outputs are modified")

    safe_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(safe_res.returncode == 0, f"existing safe smoke failed:\n{safe_res.stdout}\n{safe_res.stderr}")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
