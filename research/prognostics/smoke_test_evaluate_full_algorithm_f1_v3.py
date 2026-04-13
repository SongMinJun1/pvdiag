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


def assert_close(actual: float, expected: float, label: str) -> None:
    if abs(actual - expected) > 1e-6:
        raise SystemExit(f"{label} mismatch: expected {expected}, got {actual}")


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "evaluate_full_algorithm_f1_v3.py"
    smoke_vendor = root / "research" / "prognostics" / "smoke_test_vendor_reply_adjudication.py"
    smoke_v3 = root / "research" / "prognostics" / "smoke_test_critical_actionability_shadow_v3.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        share_dir.mkdir(parents=True, exist_ok=True)

        reaudit_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "manual_override_neg",
                    "strict_trigger_date": "2025-03-10",
                    "candidate_validity": "false_positive",
                    "onset_confidence": "high",
                    "reason_summary": "strict_method=confirmed_fault_flag|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0",
                    "review_priority": "P1",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "manual overrides vendor",
                },
                {
                    "site": "demo",
                    "panel_id": "matched_primary_keeps_precedence",
                    "strict_trigger_date": "2025-03-11",
                    "candidate_validity": "",
                    "onset_confidence": "high",
                    "reason_summary": "strict_method=confirmed_fault_flag|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0",
                    "review_priority": "P1",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "primary beats fallback",
                },
                {
                    "site": "demo",
                    "panel_id": "unmatched_clean_confirmed",
                    "strict_trigger_date": "2025-03-12",
                    "candidate_validity": "",
                    "onset_confidence": "medium",
                    "reason_summary": "strict_method=confirmed_fault_flag|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0",
                    "review_priority": "P2",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "clean confirmed fallback",
                },
                {
                    "site": "demo",
                    "panel_id": "unmatched_confounded_confirmed",
                    "strict_trigger_date": "2025-03-13",
                    "candidate_validity": "",
                    "onset_confidence": "medium",
                    "reason_summary": "strict_method=confirmed_fault_flag|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0",
                    "review_priority": "P2",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "confounded confirmed fallback",
                },
                {
                    "site": "demo",
                    "panel_id": "unmatched_critical",
                    "strict_trigger_date": "2025-03-14",
                    "candidate_validity": "",
                    "onset_confidence": "high",
                    "reason_summary": "strict_method=critical_fault_flag|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0",
                    "review_priority": "P1",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "critical must stay blank",
                },
                {
                    "site": "demo",
                    "panel_id": "matched_maint_tp",
                    "strict_trigger_date": "2025-03-15",
                    "candidate_validity": "",
                    "onset_confidence": "high",
                    "reason_summary": "strict_method=confirmed_fault_flag|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0",
                    "review_priority": "P1",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "matched maintenance tp",
                },
                {
                    "site": "demo",
                    "panel_id": "manual_excluded",
                    "strict_trigger_date": "2025-03-16",
                    "candidate_validity": "needs_more_info",
                    "onset_confidence": "medium",
                    "reason_summary": "strict_method=confirmed_fault_flag|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0",
                    "review_priority": "P3",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "manual exclude",
                },
                {
                    "site": "demo",
                    "panel_id": "no_truth",
                    "strict_trigger_date": "2025-03-17",
                    "candidate_validity": "",
                    "onset_confidence": "medium",
                    "reason_summary": "strict_method=confirmed_fault_flag|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0",
                    "review_priority": "P3",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "no truth available",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_rejected_confounded",
                    "strict_trigger_date": "2025-03-18",
                    "candidate_validity": "",
                    "onset_confidence": "medium",
                    "reason_summary": "strict_method=confirmed_fault_flag|recovery_reset=yes|shadow_frac=0.0|group_off_frac=0.0",
                    "review_priority": "P2",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "rejected confounded confirmed",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_likely_clean",
                    "strict_trigger_date": "2025-03-19",
                    "candidate_validity": "",
                    "onset_confidence": "high",
                    "reason_summary": "strict_method=confirmed_fault_flag|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0",
                    "review_priority": "P2",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "lenient only positive",
                },
            ]
        )
        reaudit_df.to_csv(share_dir / "panel_date_reaudit_working.csv", index=False, encoding="utf-8-sig")

        vendor_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "manual_override_neg",
                    "strict_trigger_date": "2025-03-10",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "electrical_fault_like",
                    "vendor_note": "manual should override",
                },
                {
                    "site": "demo",
                    "panel_id": "matched_primary_keeps_precedence",
                    "strict_trigger_date": "2025-03-11",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "electrical_fault_like",
                    "vendor_note": "primary common cause",
                },
                {
                    "site": "demo",
                    "panel_id": "unmatched_clean_confirmed",
                    "strict_trigger_date": "2025-03-12",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "electrical_fault_like",
                    "vendor_note": "clean confirmed",
                },
                {
                    "site": "demo",
                    "panel_id": "unmatched_confounded_confirmed",
                    "strict_trigger_date": "2025-03-13",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "electrical_fault_like",
                    "vendor_note": "confounded confirmed",
                },
                {
                    "site": "demo",
                    "panel_id": "unmatched_critical",
                    "strict_trigger_date": "2025-03-14",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "electrical_fault_like",
                    "vendor_note": "critical remains blank",
                },
                {
                    "site": "demo",
                    "panel_id": "matched_maint_tp",
                    "strict_trigger_date": "2025-03-15",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "electrical_fault_like",
                    "vendor_note": "matched maintenance",
                },
                {
                    "site": "demo",
                    "panel_id": "manual_excluded",
                    "strict_trigger_date": "2025-03-16",
                    "vendor_reply_class": "vendor_rejected",
                    "vendor_fault_family": "none_visible",
                    "vendor_note": "manual exclude must win",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_rejected_confounded",
                    "strict_trigger_date": "2025-03-18",
                    "vendor_reply_class": "vendor_rejected",
                    "vendor_fault_family": "none_visible",
                    "vendor_note": "negative confounded confirmed",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_likely_clean",
                    "strict_trigger_date": "2025-03-19",
                    "vendor_reply_class": "vendor_likely_positive",
                    "vendor_fault_family": "electrical_fault_like",
                    "vendor_note": "lenient only positive",
                },
            ]
        )
        vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

        v3_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "manual_override_neg",
                    "strict_trigger_date": "2025-03-10",
                    "actionability_v3": "maintenance_candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "matched_primary_keeps_precedence",
                    "strict_trigger_date": "2025-03-11",
                    "actionability_v3": "common_cause_review",
                },
                {
                    "site": "demo",
                    "panel_id": "matched_maint_tp",
                    "strict_trigger_date": "2025-03-15",
                    "actionability_v3": "maintenance_candidate",
                },
            ]
        )
        v3_df.to_csv(share_dir / "critical_actionability_shadow_v3_latest.csv", index=False, encoding="utf-8-sig")

        eval_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(eval_res.returncode == 0, f"full algorithm f1 v3 eval failed:\n{eval_res.stdout}\n{eval_res.stderr}")

        summary = pd.read_csv(share_dir / "full_algorithm_f1_summary_v3.csv", low_memory=False, encoding="utf-8-sig")
        confusion = pd.read_csv(share_dir / "full_algorithm_confusion_v3.csv", low_memory=False, encoding="utf-8-sig")
        errors = pd.read_csv(share_dir / "full_algorithm_case_errors_v3.csv", low_memory=False, encoding="utf-8-sig")

        assert_true(set(summary["truth_mode"]) == {"strict", "lenient"}, "strict and lenient modes must run")
        assert_true(set(summary["prediction_mode"]) == {"maintenance", "operational"}, "both prediction modes must run")
        assert_true(set(summary["source_split"]) == {"overall", "manual_truth", "vendor_truth"}, "source splits must run")

        by_key = summary.set_index(["truth_mode", "prediction_mode", "source_split"])
        strict_maint_overall = by_key.loc[("strict", "maintenance", "overall")]
        strict_oper_overall = by_key.loc[("strict", "operational", "overall")]
        lenient_maint_overall = by_key.loc[("lenient", "maintenance", "overall")]
        lenient_oper_overall = by_key.loc[("lenient", "operational", "overall")]

        assert_true(int(strict_maint_overall["tp"]) == 1, "strict maintenance tp mismatch")
        assert_true(int(strict_maint_overall["fp"]) == 1, "strict maintenance fp mismatch")
        assert_true(int(strict_maint_overall["fn"]) == 4, "strict maintenance fn mismatch")
        assert_true(int(strict_maint_overall["tn"]) == 1, "strict maintenance tn mismatch")
        assert_true(int(strict_maint_overall["excluded_rows"]) == 3, "strict maintenance excluded mismatch")
        assert_true(int(strict_maint_overall["scored_rows"]) == 7, "strict maintenance scored mismatch")
        assert_close(float(strict_maint_overall["primary_coverage"]), round(3 / 7, 6), "strict primary coverage")
        assert_close(float(strict_maint_overall["effective_coverage"]), round(6 / 7, 6), "strict effective coverage")

        assert_true(int(strict_oper_overall["tp"]) == 3, "strict operational tp mismatch")
        assert_true(int(strict_oper_overall["fp"]) == 1, "strict operational fp mismatch")
        assert_true(int(strict_oper_overall["fn"]) == 2, "strict operational fn mismatch")
        assert_true(int(strict_oper_overall["tn"]) == 1, "strict operational tn mismatch")

        assert_true(int(lenient_maint_overall["tp"]) == 1, "lenient maintenance tp mismatch")
        assert_true(int(lenient_maint_overall["fp"]) == 1, "lenient maintenance fp mismatch")
        assert_true(int(lenient_maint_overall["fn"]) == 5, "lenient maintenance fn mismatch")
        assert_true(int(lenient_maint_overall["tn"]) == 1, "lenient maintenance tn mismatch")
        assert_true(int(lenient_maint_overall["excluded_rows"]) == 2, "lenient maintenance excluded mismatch")
        assert_true(int(lenient_maint_overall["scored_rows"]) == 8, "lenient maintenance scored mismatch")
        assert_close(float(lenient_maint_overall["primary_coverage"]), 0.375, "lenient primary coverage")
        assert_close(float(lenient_maint_overall["effective_coverage"]), 0.875, "lenient effective coverage")

        assert_true(int(lenient_oper_overall["tp"]) == 4, "lenient operational tp mismatch")
        assert_true(int(lenient_oper_overall["fp"]) == 1, "lenient operational fp mismatch")
        assert_true(int(lenient_oper_overall["fn"]) == 2, "lenient operational fn mismatch")
        assert_true(int(lenient_oper_overall["tn"]) == 1, "lenient operational tn mismatch")

        manual_override_row = errors.loc[
            (errors["site"] == "demo")
            & (errors["panel_id"] == "manual_override_neg")
            & (errors["truth_mode"] == "strict")
            & (errors["prediction_mode"] == "maintenance")
            & (errors["source_split"] == "overall")
        ]
        assert_true(len(manual_override_row) == 1, "manual override row must appear")
        assert_true(manual_override_row.iloc[0]["truth_source"] == "manual_truth", "manual truth must override vendor")

        clean_row = errors.loc[
            (errors["panel_id"] == "unmatched_clean_confirmed")
            & (errors["truth_mode"] == "strict")
            & (errors["prediction_mode"] == "maintenance")
            & (errors["source_split"] == "overall")
        ]
        assert_true(len(clean_row) == 1, "clean confirmed fallback row must appear")
        assert_true(clean_row.iloc[0]["derived_actionability_v3"] == "singleton_review", "clean confirmed must derive singleton_review")
        assert_true(clean_row.iloc[0]["prediction_source"] == "confirmed_fault_clean", "clean confirmed source mismatch")

        confounded_row = errors.loc[
            (errors["panel_id"] == "unmatched_confounded_confirmed")
            & (errors["truth_mode"] == "strict")
            & (errors["prediction_mode"] == "operational")
            & (errors["source_split"] == "overall")
        ]
        assert_true(len(confounded_row) == 1, "confounded confirmed fallback row must appear")
        assert_true(confounded_row.iloc[0]["derived_actionability_v3"] == "monitor_only", "confounded confirmed must derive monitor_only")
        assert_true(confounded_row.iloc[0]["prediction_source"] == "confirmed_fault_confounded", "confounded source mismatch")

        matched_row = errors.loc[
            (errors["panel_id"] == "matched_primary_keeps_precedence")
            & (errors["truth_mode"] == "strict")
            & (errors["prediction_mode"] == "maintenance")
            & (errors["source_split"] == "overall")
        ]
        assert_true(len(matched_row) == 1, "matched primary row must appear")
        assert_true(matched_row.iloc[0]["actionability_v3"] == "common_cause_review", "matched actionability should be preserved")
        assert_true(pd.isna(matched_row.iloc[0]["derived_actionability_v3"]) or matched_row.iloc[0]["derived_actionability_v3"] == "", "matched row should not use derived actionability")
        assert_true(matched_row.iloc[0]["final_actionability_v3"] == "common_cause_review", "primary actionability must take precedence")
        assert_true(matched_row.iloc[0]["prediction_source"] == "primary_actionability_v3", "matched row should keep primary source")

        critical_row = errors.loc[
            (errors["panel_id"] == "unmatched_critical")
            & (errors["truth_mode"] == "strict")
            & (errors["prediction_mode"] == "operational")
            & (errors["source_split"] == "overall")
        ]
        assert_true(len(critical_row) == 1, "unmatched critical row must appear")
        assert_true(pd.isna(critical_row.iloc[0]["derived_actionability_v3"]) or critical_row.iloc[0]["derived_actionability_v3"] == "", "critical row must stay blank")
        assert_true(pd.isna(critical_row.iloc[0]["final_actionability_v3"]) or critical_row.iloc[0]["final_actionability_v3"] == "", "critical row final actionability must stay blank")
        assert_true(critical_row.iloc[0]["prediction_source"] == "unmatched_critical_missing_v3", "critical row source mismatch")

        for row in confusion.itertuples(index=False):
            subset = reaudit_df.copy()
            if row.source_split == "manual_truth":
                subset = subset.loc[subset["candidate_validity"].fillna("").astype(str).str.strip().ne("")]
            elif row.source_split == "vendor_truth":
                manual_mask = subset["candidate_validity"].fillna("").astype(str).str.strip().ne("")
                vendor_index = vendor_df.set_index(["site", "panel_id", "strict_trigger_date"]).index
                subset_index = pd.MultiIndex.from_frame(subset[["site", "panel_id", "strict_trigger_date"]])
                subset = subset.loc[~manual_mask & subset_index.isin(vendor_index)]
            total = int(row.tp) + int(row.fp) + int(row.fn) + int(row.tn) + int(row.excluded_rows)
            assert_true(total == len(subset), "confusion counts must add up correctly")

        assert_true(summary["f1"].between(0, 1).all(), "F1 must remain within [0,1]")
        assert_true(summary["precision"].between(0, 1).all(), "precision must remain within [0,1]")
        assert_true(summary["recall"].between(0, 1).all(), "recall must remain within [0,1]")
        assert_true(summary["primary_coverage"].between(0, 1).all(), "primary coverage must remain within [0,1]")
        assert_true(summary["effective_coverage"].between(0, 1).all(), "effective coverage must remain within [0,1]")
        assert_true((summary["effective_coverage"] >= summary["primary_coverage"]).all(), "effective coverage must be >= primary coverage")

    smoke_vendor_res = run([sys.executable, str(smoke_vendor)], root)
    assert_true(
        smoke_vendor_res.returncode == 0,
        f"vendor adjudication smoke failed:\n{smoke_vendor_res.stdout}\n{smoke_vendor_res.stderr}",
    )
    smoke_v3_res = run([sys.executable, str(smoke_v3)], root)
    assert_true(
        smoke_v3_res.returncode == 0,
        f"critical actionability v3 smoke failed:\n{smoke_v3_res.stdout}\n{smoke_v3_res.stderr}",
    )

    print("[OK] scripts compile")
    print("[OK] strict and lenient modes both run")
    print("[OK] maintenance and operational modes both run")
    print("[OK] manual truth overrides vendor truth")
    print("[OK] unmatched clean confirmed_fault_flag row becomes singleton_review via fallback")
    print("[OK] unmatched confounded confirmed_fault_flag row becomes monitor_only via fallback")
    print("[OK] matched actionability_v3 row keeps precedence over fallback")
    print("[OK] unmatched critical_fault_flag row remains blank")
    print("[OK] confusion counts add up correctly")
    print("[OK] F1 remains within [0,1]")
    print("[OK] primary_coverage and effective_coverage remain within [0,1]")
    print("[OK] effective_coverage >= primary_coverage")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
