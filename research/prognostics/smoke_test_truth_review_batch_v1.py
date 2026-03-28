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
    build_script = root / "research" / "prognostics" / "build_truth_review_batch_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_truth_coverage_priority_audit_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        share_dir.mkdir(parents=True, exist_ok=True)

        cases_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "urgent_case",
                    "strict_trigger_date": "2025-03-10",
                    "review_priority_bucket": "urgent_official_error_context",
                    "priority_score": 105,
                    "recommended_review_action": "manual_reaudit_first",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "group_or_inverter_side_like",
                    "critical_phenotype_v3": "",
                    "actionability_v3": "",
                    "official_error_modes": "strict:maintenance",
                    "official_error_types": "fn",
                    "prediction_source": "confirmed_fault_clean",
                    "gap_bucket": "clean_confirmed_fault_review_gap",
                    "promotion_hypothesis": "candidate_for_maintenance_shadow",
                    "review_priority": "P1",
                    "note": "urgent note",
                    "vendor_note": "urgent vendor note",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_case",
                    "strict_trigger_date": "2025-03-11",
                    "review_priority_bucket": "vendor_backed_unlabeled",
                    "priority_score": 73,
                    "recommended_review_action": "compare_with_vendor_and_field_logs",
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
                    "note": "vendor note",
                    "vendor_note": "vendor context",
                },
                {
                    "site": "demo",
                    "panel_id": "high_case",
                    "strict_trigger_date": "2025-03-12",
                    "review_priority_bucket": "high_actionability_unlabeled",
                    "priority_score": 61,
                    "recommended_review_action": "manual_reaudit_first",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "critical_phenotype_v3": "singleton_borderline_review",
                    "actionability_v3": "singleton_review",
                    "official_error_modes": "",
                    "official_error_types": "",
                    "prediction_source": "",
                    "gap_bucket": "",
                    "promotion_hypothesis": "",
                    "review_priority": "P2",
                    "note": "high actionability note",
                    "vendor_note": "",
                },
                {
                    "site": "demo",
                    "panel_id": "precursor_case",
                    "strict_trigger_date": "2025-03-13",
                    "review_priority_bucket": "precursor_note_context",
                    "priority_score": 50,
                    "recommended_review_action": "compare_with_vendor_and_field_logs",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "critical_phenotype_v3": "",
                    "actionability_v3": "",
                    "official_error_modes": "",
                    "official_error_types": "",
                    "prediction_source": "",
                    "gap_bucket": "",
                    "promotion_hypothesis": "",
                    "review_priority": "P3",
                    "note": "precursor note",
                    "vendor_note": "",
                },
                {
                    "site": "demo",
                    "panel_id": "backlog_case",
                    "strict_trigger_date": "2025-03-14",
                    "review_priority_bucket": "monitor_only_backlog",
                    "priority_score": 30,
                    "recommended_review_action": "defer_until_backlog_review",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "critical_phenotype_v3": "shape_only_monitor",
                    "actionability_v3": "monitor_only",
                    "official_error_modes": "",
                    "official_error_types": "",
                    "prediction_source": "",
                    "gap_bucket": "",
                    "promotion_hypothesis": "",
                    "review_priority": "P3",
                    "note": "backlog note",
                    "vendor_note": "",
                },
                {
                    "site": "demo",
                    "panel_id": "labeled_case",
                    "strict_trigger_date": "2025-03-15",
                    "review_priority_bucket": "already_labeled",
                    "priority_score": 0,
                    "recommended_review_action": "no_action_needed",
                    "vendor_reply_class": "vendor_rejected",
                    "vendor_fault_family": "none_visible",
                    "critical_phenotype_v3": "shape_only_monitor",
                    "actionability_v3": "monitor_only",
                    "official_error_modes": "",
                    "official_error_types": "",
                    "prediction_source": "",
                    "gap_bucket": "",
                    "promotion_hypothesis": "",
                    "review_priority": "P3",
                    "note": "already labeled note",
                    "vendor_note": "",
                },
            ]
        )
        original_cases_csv = cases_df.to_csv(index=False)
        cases_df.to_csv(share_dir / "truth_coverage_priority_cases_v1.csv", index=False, encoding="utf-8-sig")

        summary_df = pd.DataFrame(
            [
                {
                    "record_type": "summary",
                    "total_strict_cases": 6,
                    "manual_truth_present_count": 1,
                    "manual_truth_missing_count": 5,
                    "urgent_official_error_context_count": 1,
                    "maintenance_definition_gap_count": 0,
                    "vendor_backed_unlabeled_count": 1,
                    "high_actionability_unlabeled_count": 1,
                    "precursor_note_context_count": 1,
                    "monitor_only_backlog_count": 1,
                    "site": "",
                    "total_cases": "",
                    "highest_priority_bucket": "",
                    "highest_priority_bucket_count": "",
                }
            ]
        )
        summary_df.to_csv(share_dir / "truth_coverage_priority_summary_v1.csv", index=False, encoding="utf-8-sig")

        run_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(run_res.returncode == 0, f"script failed:\n{run_res.stdout}\n{run_res.stderr}")

        batch_df = pd.read_csv(share_dir / "truth_review_batch_v1.csv", encoding="utf-8-sig")
        packets_df = pd.read_csv(share_dir / "truth_review_site_packets_v1.csv", encoding="utf-8-sig")
        copyback_df = pd.read_csv(share_dir / "truth_review_copyback_template_v1.csv", encoding="utf-8-sig")

        assert_true(not batch_df.empty, "round-1 batch output is empty")
        assert_true(not packets_df.empty, "site packet output is empty")
        assert_true(not copyback_df.empty, "copyback template output is empty")

        selected_buckets = set(batch_df["review_priority_bucket"].astype(str))
        assert_true(
            selected_buckets <= {
                "urgent_official_error_context",
                "vendor_backed_unlabeled",
                "high_actionability_unlabeled",
            },
            "round-1 universe should include only the 3 intended buckets",
        )

        expected_count = 3
        assert_true(
            len(batch_df) == expected_count,
            "round-1 batch count should equal urgent + vendor_backed + high_actionability counts",
        )
        assert_true(
            len(copyback_df) == len(batch_df),
            "copyback template row count should match round-1 batch row count",
        )

        assert_true(
            batch_df.iloc[0]["panel_id"] == "urgent_case"
            and batch_df.iloc[0]["round1_bucket_rank"] == 1
            and batch_df.iloc[0]["review_focus"] == "official_error_reaudit",
            "urgent case should sort first and map to official_error_reaudit",
        )
        assert_true(
            batch_df.loc[batch_df["panel_id"].eq("vendor_case"), "review_focus"].iloc[0] == "vendor_field_log_compare",
            "vendor-backed row should map to vendor_field_log_compare",
        )
        assert_true(
            batch_df.loc[batch_df["panel_id"].eq("high_case"), "review_focus"].iloc[0] == "actionability_sanity_check",
            "high-actionability row should map to actionability_sanity_check",
        )

        copyback_row = copyback_df.loc[copyback_df["panel_id"].eq("urgent_case")].iloc[0]
        assert_true(
            all(str(copyback_row[col]).strip().lower() in {"", "nan"} for col in ["candidate_validity", "date_judgement", "note", "review_owner", "review_status"]),
            "copyback template fields should be blank by default",
        )

        current_cases_csv = pd.read_csv(
            share_dir / "truth_coverage_priority_cases_v1.csv",
            encoding="utf-8-sig",
        ).to_csv(index=False)
        assert_true(
            current_cases_csv == original_cases_csv,
            "priority audit input should remain unchanged",
        )

        print("[OK] outputs generate")
        print("[OK] selected round-1 universe includes only the 3 intended buckets")
        print("[OK] round-1 batch count equals urgent + vendor_backed + high_actionability counts from synthetic fixture")
        print("[OK] copyback template row count matches round-1 batch row count")
        print("[OK] no official outputs are modified")

    safe_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(safe_res.returncode == 0, f"existing safe smoke failed:\n{safe_res.stdout}\n{safe_res.stderr}")
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
