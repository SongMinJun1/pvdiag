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
    build_script = root / "research" / "prognostics" / "evaluate_full_algorithm_f1_v2.py"
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
                    "review_priority": "P1",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "manual overrides vendor",
                },
                {
                    "site": "demo",
                    "panel_id": "manual_tp",
                    "strict_trigger_date": "2025-03-11",
                    "candidate_validity": "true_positive",
                    "review_priority": "P1",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "manual tp",
                },
                {
                    "site": "demo",
                    "panel_id": "manual_excluded",
                    "strict_trigger_date": "2025-03-12",
                    "candidate_validity": "needs_more_info",
                    "review_priority": "P3",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "manual exclude",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_tp_maint",
                    "strict_trigger_date": "2025-03-13",
                    "candidate_validity": "",
                    "review_priority": "P1",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "vendor positive maintenance",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_tp_oper",
                    "strict_trigger_date": "2025-03-14",
                    "candidate_validity": "",
                    "review_priority": "P2",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "vendor positive operational",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_likely",
                    "strict_trigger_date": "2025-03-15",
                    "candidate_validity": "",
                    "review_priority": "P2",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "vendor likely positive",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_rejected",
                    "strict_trigger_date": "2025-03-16",
                    "candidate_validity": "",
                    "review_priority": "P3",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "vendor rejected",
                },
                {
                    "site": "demo",
                    "panel_id": "no_truth",
                    "strict_trigger_date": "2025-03-17",
                    "candidate_validity": "",
                    "review_priority": "P3",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "no truth available",
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
                    "vendor_note": "vendor positive but manual should override",
                },
                {
                    "site": "demo",
                    "panel_id": "manual_excluded",
                    "strict_trigger_date": "2025-03-12",
                    "vendor_reply_class": "vendor_rejected",
                    "vendor_fault_family": "none_visible",
                    "vendor_note": "manual exclude should still win",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_tp_maint",
                    "strict_trigger_date": "2025-03-13",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "electrical_fault_like",
                    "vendor_note": "vendor positive maintenance",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_tp_oper",
                    "strict_trigger_date": "2025-03-14",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "electrical_fault_like",
                    "vendor_note": "vendor positive operational",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_likely",
                    "strict_trigger_date": "2025-03-15",
                    "vendor_reply_class": "vendor_likely_positive",
                    "vendor_fault_family": "electrical_fault_like",
                    "vendor_note": "vendor likely positive",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_rejected",
                    "strict_trigger_date": "2025-03-16",
                    "vendor_reply_class": "vendor_rejected",
                    "vendor_fault_family": "none_visible",
                    "vendor_note": "vendor rejected",
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
                    "panel_id": "manual_tp",
                    "strict_trigger_date": "2025-03-11",
                    "actionability_v3": "maintenance_candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "manual_excluded",
                    "strict_trigger_date": "2025-03-12",
                    "actionability_v3": "common_cause_review",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_tp_maint",
                    "strict_trigger_date": "2025-03-13",
                    "actionability_v3": "maintenance_candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_tp_oper",
                    "strict_trigger_date": "2025-03-14",
                    "actionability_v3": "singleton_review",
                },
                {
                    "site": "demo",
                    "panel_id": "vendor_likely",
                    "strict_trigger_date": "2025-03-15",
                    "actionability_v3": "monitor_only",
                },
                {
                    "site": "demo",
                    "panel_id": "no_truth",
                    "strict_trigger_date": "2025-03-17",
                    "actionability_v3": "maintenance_candidate",
                },
            ]
        )
        v3_df.to_csv(share_dir / "critical_actionability_shadow_v3_latest.csv", index=False, encoding="utf-8-sig")

        eval_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(eval_res.returncode == 0, f"full algorithm f1 v2 eval failed:\n{eval_res.stdout}\n{eval_res.stderr}")

        summary = pd.read_csv(share_dir / "full_algorithm_f1_summary_v2.csv", low_memory=False, encoding="utf-8-sig")
        confusion = pd.read_csv(share_dir / "full_algorithm_confusion_v2.csv", low_memory=False, encoding="utf-8-sig")
        errors = pd.read_csv(share_dir / "full_algorithm_case_errors_v2.csv", low_memory=False, encoding="utf-8-sig")

        assert_true(set(summary["truth_mode"]) == {"strict", "lenient"}, "strict and lenient modes must run")
        assert_true(set(summary["prediction_mode"]) == {"maintenance", "operational"}, "both prediction modes must run")
        assert_true(set(summary["source_split"]) == {"overall", "manual_truth", "vendor_truth"}, "source splits must run")

        by_key = summary.set_index(["truth_mode", "prediction_mode", "source_split"])

        strict_maint_overall = by_key.loc[("strict", "maintenance", "overall")]
        strict_oper_overall = by_key.loc[("strict", "operational", "overall")]
        lenient_maint_overall = by_key.loc[("lenient", "maintenance", "overall")]
        lenient_oper_overall = by_key.loc[("lenient", "operational", "overall")]
        strict_maint_manual = by_key.loc[("strict", "maintenance", "manual_truth")]
        strict_maint_vendor = by_key.loc[("strict", "maintenance", "vendor_truth")]
        lenient_maint_vendor = by_key.loc[("lenient", "maintenance", "vendor_truth")]

        assert_true(int(strict_maint_overall["tp"]) == 2, "strict maintenance tp mismatch")
        assert_true(int(strict_maint_overall["fp"]) == 1, "strict maintenance fp mismatch")
        assert_true(int(strict_maint_overall["fn"]) == 1, "strict maintenance fn mismatch")
        assert_true(int(strict_maint_overall["tn"]) == 1, "strict maintenance tn mismatch")
        assert_true(int(strict_maint_overall["excluded_rows"]) == 3, "strict maintenance excluded mismatch")
        assert_true(int(strict_maint_overall["scored_rows"]) == 5, "strict maintenance scored_rows mismatch")
        assert_close(float(strict_maint_overall["coverage"]), 0.8, "strict maintenance coverage")

        assert_true(int(strict_oper_overall["tp"]) == 3, "strict operational tp mismatch")
        assert_true(int(strict_oper_overall["fp"]) == 1, "strict operational fp mismatch")
        assert_true(int(strict_oper_overall["fn"]) == 0, "strict operational fn mismatch")
        assert_true(int(strict_oper_overall["tn"]) == 1, "strict operational tn mismatch")

        assert_true(int(lenient_maint_overall["tp"]) == 2, "lenient maintenance tp mismatch")
        assert_true(int(lenient_maint_overall["fp"]) == 1, "lenient maintenance fp mismatch")
        assert_true(int(lenient_maint_overall["fn"]) == 2, "lenient maintenance fn mismatch")
        assert_true(int(lenient_maint_overall["tn"]) == 1, "lenient maintenance tn mismatch")
        assert_true(int(lenient_maint_overall["excluded_rows"]) == 2, "lenient maintenance excluded mismatch")
        assert_true(int(lenient_maint_overall["scored_rows"]) == 6, "lenient maintenance scored_rows mismatch")
        assert_close(float(lenient_maint_overall["coverage"]), round(5 / 6, 6), "lenient maintenance coverage")

        assert_true(int(lenient_oper_overall["tp"]) == 3, "lenient operational tp mismatch")
        assert_true(int(lenient_oper_overall["fp"]) == 1, "lenient operational fp mismatch")
        assert_true(int(lenient_oper_overall["fn"]) == 1, "lenient operational fn mismatch")
        assert_true(int(lenient_oper_overall["tn"]) == 1, "lenient operational tn mismatch")

        assert_true(int(strict_maint_manual["tp"]) == 1, "manual split tp mismatch")
        assert_true(int(strict_maint_manual["fp"]) == 1, "manual split fp mismatch")
        assert_true(int(strict_maint_manual["excluded_rows"]) == 1, "manual split excluded mismatch")
        assert_true(int(strict_maint_vendor["tp"]) == 1, "strict vendor split tp mismatch")
        assert_true(int(strict_maint_vendor["fn"]) == 1, "strict vendor split fn mismatch")
        assert_true(int(strict_maint_vendor["tn"]) == 1, "strict vendor split tn mismatch")
        assert_true(int(strict_maint_vendor["excluded_rows"]) == 1, "strict vendor split excluded mismatch")
        assert_true(int(lenient_maint_vendor["tp"]) == 1, "lenient vendor split tp mismatch")
        assert_true(int(lenient_maint_vendor["fn"]) == 2, "lenient vendor split fn mismatch")
        assert_true(int(lenient_maint_vendor["tn"]) == 1, "lenient vendor split tn mismatch")

        manual_override_row = errors.loc[
            (errors["site"] == "demo")
            & (errors["panel_id"] == "manual_override_neg")
            & (errors["truth_mode"] == "strict")
            & (errors["prediction_mode"] == "maintenance")
            & (errors["source_split"] == "overall")
        ]
        assert_true(len(manual_override_row) == 1, "manual override row must appear as one error")
        assert_true(
            manual_override_row.iloc[0]["truth_source"] == "manual_truth",
            "manual truth must override vendor truth",
        )
        assert_true(
            manual_override_row.iloc[0]["truth_label"] == "negative",
            "manual override row must stay negative",
        )

        for row in confusion.itertuples(index=False):
            subset = reaudit_df.copy()
            if row.source_split == "manual_truth":
                mask = subset["candidate_validity"].fillna("").astype(str).str.strip().ne("")
                subset = subset.loc[mask]
            elif row.source_split == "vendor_truth":
                manual_mask = subset["candidate_validity"].fillna("").astype(str).str.strip().ne("")
                vendor_mask = vendor_df.set_index(["site", "panel_id", "strict_trigger_date"]).index
                subset_idx = pd.MultiIndex.from_frame(subset[["site", "panel_id", "strict_trigger_date"]])
                subset = subset.loc[~manual_mask & subset_idx.isin(vendor_mask)]
            total = int(row.tp) + int(row.fp) + int(row.fn) + int(row.tn) + int(row.excluded_rows)
            assert_true(total == len(subset), "confusion counts must add up correctly")

        assert_true(summary["f1"].between(0, 1).all(), "F1 must remain within [0,1]")
        assert_true(summary["precision"].between(0, 1).all(), "precision must remain within [0,1]")
        assert_true(summary["recall"].between(0, 1).all(), "recall must remain within [0,1]")
        assert_true(summary["coverage"].between(0, 1).all(), "coverage must remain within [0,1]")
        assert_true(not errors.empty, "case errors should be populated")
        assert_true(set(errors["error_type"]) <= {"fp", "fn"}, "error types must be fp/fn only")

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
    print("[OK] confusion counts add up correctly")
    print("[OK] coverage remains within [0,1]")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
