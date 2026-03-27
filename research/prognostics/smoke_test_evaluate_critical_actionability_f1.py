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
    build_script = root / "research" / "prognostics" / "evaluate_critical_actionability_f1.py"
    smoke_v3 = root / "research" / "prognostics" / "smoke_test_critical_actionability_shadow_v3.py"
    smoke_vendor = root / "research" / "prognostics" / "smoke_test_vendor_reply_adjudication.py"
    smoke_field = root / "research" / "prognostics" / "smoke_test_field_truth_validation.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        share_dir.mkdir(parents=True, exist_ok=True)

        v3_df = pd.DataFrame(
            [
                {"site": "demo", "panel_id": "p_tp", "actionability_v3": "maintenance_candidate"},
                {"site": "demo", "panel_id": "p_fp", "actionability_v3": "maintenance_candidate"},
                {"site": "demo", "panel_id": "p_review", "actionability_v3": "singleton_review"},
                {"site": "demo", "panel_id": "p_tn", "actionability_v3": "monitor_only"},
                {"site": "demo", "panel_id": "p_likely", "actionability_v3": "singleton_review"},
                {"site": "demo", "panel_id": "p_excluded", "actionability_v3": "monitor_only"},
            ]
        )
        v3_df.to_csv(share_dir / "critical_actionability_shadow_v3_latest.csv", index=False, encoding="utf-8-sig")

        vendor_df = pd.DataFrame(
            [
                {"site": "demo", "panel_id": "p_tp", "vendor_reply_class": "vendor_pattern_positive", "vendor_fault_family": "electrical", "vendor_note": "tp"},
                {"site": "demo", "panel_id": "p_fp", "vendor_reply_class": "vendor_rejected", "vendor_fault_family": "none", "vendor_note": "fp"},
                {"site": "demo", "panel_id": "p_review", "vendor_reply_class": "vendor_pattern_positive", "vendor_fault_family": "electrical", "vendor_note": "review positive"},
                {"site": "demo", "panel_id": "p_tn", "vendor_reply_class": "vendor_rejected", "vendor_fault_family": "none", "vendor_note": "tn"},
                {"site": "demo", "panel_id": "p_likely", "vendor_reply_class": "vendor_likely_positive", "vendor_fault_family": "electrical", "vendor_note": "likely"},
                {"site": "demo", "panel_id": "p_missing", "vendor_reply_class": "vendor_pattern_positive", "vendor_fault_family": "electrical", "vendor_note": "missing fn"},
                {"site": "demo", "panel_id": "p_excluded", "vendor_reply_class": "vendor_no_info", "vendor_fault_family": "unknown", "vendor_note": "exclude"},
            ]
        )
        vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

        eval_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(eval_res.returncode == 0, f"critical actionability f1 eval failed:\n{eval_res.stdout}\n{eval_res.stderr}")

        summary = pd.read_csv(share_dir / "critical_actionability_f1_summary.csv", low_memory=False, encoding="utf-8-sig")
        confusion = pd.read_csv(share_dir / "critical_actionability_confusion.csv", low_memory=False, encoding="utf-8-sig")
        errors = pd.read_csv(share_dir / "critical_actionability_case_errors.csv", low_memory=False, encoding="utf-8-sig")

        assert_true(set(summary["truth_mode"]) == {"strict", "lenient"}, "strict and lenient truth modes must both run")
        assert_true(set(summary["prediction_mode"]) == {"maintenance", "operational_review"}, "maintenance and operational_review prediction modes must both run")

        strict_maint = summary.set_index(["truth_mode", "prediction_mode"]).loc[("strict", "maintenance")]
        assert_true(int(strict_maint["tp"]) == 1, "strict maintenance tp mismatch")
        assert_true(int(strict_maint["fp"]) == 1, "strict maintenance fp mismatch")
        assert_true(int(strict_maint["fn"]) == 2, "strict maintenance fn mismatch")
        assert_true(int(strict_maint["tn"]) == 1, "strict maintenance tn mismatch")
        assert_true(int(strict_maint["excluded_rows"]) == 2, "strict maintenance excluded count mismatch")

        for row in confusion.itertuples(index=False):
            total = int(row.tp) + int(row.fp) + int(row.fn) + int(row.tn) + int(row.excluded_rows)
            assert_true(total == len(vendor_df), "confusion counts must add up to the vendor-evaluated row count")

        assert_true(summary["f1"].between(0, 1).all(), "F1 must remain within [0,1]")
        assert_true(summary["precision"].between(0, 1).all(), "precision must remain within [0,1]")
        assert_true(summary["recall"].between(0, 1).all(), "recall must remain within [0,1]")
        assert_true(not errors.empty, "case errors file should contain fp/fn rows for the synthetic fixture")

    smoke_v3_res = run([sys.executable, str(smoke_v3)], root)
    assert_true(smoke_v3_res.returncode == 0, f"critical actionability v3 smoke failed:\n{smoke_v3_res.stdout}\n{smoke_v3_res.stderr}")
    smoke_vendor_res = run([sys.executable, str(smoke_vendor)], root)
    assert_true(smoke_vendor_res.returncode == 0, f"vendor smoke failed:\n{smoke_vendor_res.stdout}\n{smoke_vendor_res.stderr}")
    smoke_field_res = run([sys.executable, str(smoke_field)], root)
    assert_true(smoke_field_res.returncode == 0, f"field truth smoke failed:\n{smoke_field_res.stdout}\n{smoke_field_res.stderr}")

    print("[OK] scripts compile")
    print("[OK] strict and lenient modes both run")
    print("[OK] maintenance and operational_review modes both run")
    print("[OK] confusion counts add up correctly")
    print("[OK] F1 remains within [0,1]")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
