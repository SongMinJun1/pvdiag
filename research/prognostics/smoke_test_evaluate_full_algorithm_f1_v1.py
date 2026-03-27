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
    build_script = root / "research" / "prognostics" / "evaluate_full_algorithm_f1_v1.py"
    smoke_v3 = root / "research" / "prognostics" / "smoke_test_critical_actionability_shadow_v3.py"
    smoke_field = root / "research" / "prognostics" / "smoke_test_field_truth_validation.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        share_dir.mkdir(parents=True, exist_ok=True)

        truth_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "p_tp_maint",
                    "strict_trigger_date": "2025-03-10",
                    "candidate_validity": "true_positive",
                    "review_priority": "P1",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "electrical_fault_like",
                    "note": "tp maintenance",
                },
                {
                    "site": "demo",
                    "panel_id": "p_tp_operational_only",
                    "strict_trigger_date": "2025-03-11",
                    "candidate_validity": "group_side",
                    "review_priority": "P2",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "tp operational only",
                },
                {
                    "site": "demo",
                    "panel_id": "p_fp_maint",
                    "strict_trigger_date": "2025-03-12",
                    "candidate_validity": "false_positive",
                    "review_priority": "P1",
                    "vendor_reply_class": "vendor_rejected",
                    "vendor_fault_family": "none_visible",
                    "note": "fp maintenance",
                },
                {
                    "site": "demo",
                    "panel_id": "p_tn_missing",
                    "strict_trigger_date": "2025-03-13",
                    "candidate_validity": "false_positive",
                    "review_priority": "P3",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "tn missing prediction",
                },
                {
                    "site": "demo",
                    "panel_id": "p_fn_missing",
                    "strict_trigger_date": "2025-03-14",
                    "candidate_validity": "true_positive",
                    "review_priority": "P2",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "fn missing prediction",
                },
                {
                    "site": "demo",
                    "panel_id": "p_excluded",
                    "strict_trigger_date": "2025-03-15",
                    "candidate_validity": "needs_more_info",
                    "review_priority": "P3",
                    "vendor_reply_class": "vendor_no_info",
                    "vendor_fault_family": "",
                    "note": "excluded",
                },
                {
                    "site": "demo",
                    "panel_id": "p_blank",
                    "strict_trigger_date": "2025-03-16",
                    "candidate_validity": "",
                    "review_priority": "P3",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "blank excluded",
                },
            ]
        )
        truth_df.to_csv(share_dir / "panel_date_reaudit_working.csv", index=False, encoding="utf-8-sig")

        v3_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "p_tp_maint",
                    "strict_trigger_date": "2025-03-10",
                    "actionability_v3": "maintenance_candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "p_tp_operational_only",
                    "strict_trigger_date": "2025-03-11",
                    "actionability_v3": "singleton_review",
                },
                {
                    "site": "demo",
                    "panel_id": "p_fp_maint",
                    "strict_trigger_date": "2025-03-12",
                    "actionability_v3": "maintenance_candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "p_excluded",
                    "strict_trigger_date": "2025-03-15",
                    "actionability_v3": "common_cause_review",
                },
            ]
        )
        v3_df.to_csv(share_dir / "critical_actionability_shadow_v3_latest.csv", index=False, encoding="utf-8-sig")

        eval_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(eval_res.returncode == 0, f"full algorithm f1 eval failed:\n{eval_res.stdout}\n{eval_res.stderr}")

        summary = pd.read_csv(share_dir / "full_algorithm_f1_summary.csv", low_memory=False, encoding="utf-8-sig")
        confusion = pd.read_csv(share_dir / "full_algorithm_confusion.csv", low_memory=False, encoding="utf-8-sig")
        errors = pd.read_csv(share_dir / "full_algorithm_case_errors.csv", low_memory=False, encoding="utf-8-sig")

        assert_true(set(summary["prediction_mode"]) == {"maintenance", "operational"}, "both maintenance and operational modes must run")
        assert_true(set(summary["source_split"]) == {"overall", "vendor_reply_present", "vendor_reply_absent"}, "source split rows must be produced")

        by_key = summary.set_index(["prediction_mode", "source_split"])
        maint_overall = by_key.loc[("maintenance", "overall")]
        oper_overall = by_key.loc[("operational", "overall")]

        assert_true(int(maint_overall["tp"]) == 1, "maintenance tp mismatch")
        assert_true(int(maint_overall["fp"]) == 1, "maintenance fp mismatch")
        assert_true(int(maint_overall["fn"]) == 2, "maintenance fn mismatch")
        assert_true(int(maint_overall["tn"]) == 1, "maintenance tn mismatch")
        assert_true(int(maint_overall["excluded_rows"]) == 2, "maintenance excluded_rows mismatch")
        assert_true(int(maint_overall["scored_rows"]) == 5, "maintenance scored_rows mismatch")
        assert_true(float(maint_overall["coverage"]) == 0.6, "maintenance coverage mismatch")

        assert_true(int(oper_overall["tp"]) == 2, "operational tp mismatch")
        assert_true(int(oper_overall["fp"]) == 1, "operational fp mismatch")
        assert_true(int(oper_overall["fn"]) == 1, "operational fn mismatch")
        assert_true(int(oper_overall["tn"]) == 1, "operational tn mismatch")

        for row in confusion.itertuples(index=False):
            subset = truth_df.copy()
            vendor_present = subset["vendor_reply_class"].fillna("").astype(str).str.strip().ne("")
            if row.source_split == "vendor_reply_present":
                subset = subset.loc[vendor_present]
            elif row.source_split == "vendor_reply_absent":
                subset = subset.loc[~vendor_present]
            total = int(row.tp) + int(row.fp) + int(row.fn) + int(row.tn) + int(row.excluded_rows)
            assert_true(total == len(subset), "confusion counts must add up correctly")

        assert_true(summary["f1"].between(0, 1).all(), "F1 must remain within [0,1]")
        assert_true(summary["precision"].between(0, 1).all(), "precision must remain within [0,1]")
        assert_true(summary["recall"].between(0, 1).all(), "recall must remain within [0,1]")
        assert_true(summary["coverage"].between(0, 1).all(), "coverage must remain within [0,1]")
        assert_true(not errors.empty, "case errors file should contain fp/fn rows")
        assert_true(set(errors["error_type"]) <= {"fp", "fn"}, "error types must be fp/fn only")

    smoke_v3_res = run([sys.executable, str(smoke_v3)], root)
    assert_true(smoke_v3_res.returncode == 0, f"critical actionability v3 smoke failed:\n{smoke_v3_res.stdout}\n{smoke_v3_res.stderr}")
    smoke_field_res = run([sys.executable, str(smoke_field)], root)
    assert_true(smoke_field_res.returncode == 0, f"field truth smoke failed:\n{smoke_field_res.stdout}\n{smoke_field_res.stderr}")

    print("[OK] scripts compile")
    print("[OK] both maintenance and operational modes run")
    print("[OK] confusion counts add up correctly")
    print("[OK] F1 remains within [0,1]")
    print("[OK] excluded rows handled correctly")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
