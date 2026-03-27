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
    build_script = root / "research" / "prognostics" / "evaluate_maintenance_shadow_f1_v1.py"
    smoke_gap = root / "research" / "prognostics" / "smoke_test_maintenance_gap_audit_v1.py"

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
                    "panel_id": "strict_backed_candidate",
                    "strict_trigger_date": "2025-03-10",
                    "candidate_validity": "",
                    "onset_confidence": "high",
                    "reason_summary": "",
                    "review_priority": "P1",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "strict-backed candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "lenient_only_candidate",
                    "strict_trigger_date": "2025-03-11",
                    "candidate_validity": "",
                    "onset_confidence": "medium",
                    "reason_summary": "",
                    "review_priority": "P1",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "lenient-only candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "keep_review_case",
                    "strict_trigger_date": "2025-03-12",
                    "candidate_validity": "",
                    "onset_confidence": "medium",
                    "reason_summary": "",
                    "review_priority": "P1",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "keep review case",
                },
                {
                    "site": "demo",
                    "panel_id": "baseline_maint_tp",
                    "strict_trigger_date": "2025-03-13",
                    "candidate_validity": "",
                    "onset_confidence": "high",
                    "reason_summary": "",
                    "review_priority": "P1",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "baseline maintenance tp",
                },
                {
                    "site": "demo",
                    "panel_id": "manual_negative_fp",
                    "strict_trigger_date": "2025-03-14",
                    "candidate_validity": "false_positive",
                    "onset_confidence": "medium",
                    "reason_summary": "",
                    "review_priority": "P2",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "manual negative fp",
                },
                {
                    "site": "demo",
                    "panel_id": "no_truth_excluded",
                    "strict_trigger_date": "2025-03-15",
                    "candidate_validity": "",
                    "onset_confidence": "medium",
                    "reason_summary": "",
                    "review_priority": "P3",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "note": "excluded no truth",
                },
            ]
        )
        reaudit_df.to_csv(share_dir / "panel_date_reaudit_working.csv", index=False, encoding="utf-8-sig")

        vendor_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "strict_backed_candidate",
                    "strict_trigger_date": "2025-03-10",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "group_or_inverter_side_like",
                    "vendor_note": "strict-backed truth",
                },
                {
                    "site": "demo",
                    "panel_id": "lenient_only_candidate",
                    "strict_trigger_date": "2025-03-11",
                    "vendor_reply_class": "vendor_likely_positive",
                    "vendor_fault_family": "open_or_device_issue_like",
                    "vendor_note": "lenient-only truth",
                },
                {
                    "site": "demo",
                    "panel_id": "keep_review_case",
                    "strict_trigger_date": "2025-03-12",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "diode_like",
                    "vendor_note": "keep review truth",
                },
                {
                    "site": "demo",
                    "panel_id": "baseline_maint_tp",
                    "strict_trigger_date": "2025-03-13",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "diode_like",
                    "vendor_note": "baseline tp",
                },
                {
                    "site": "demo",
                    "panel_id": "no_truth_excluded",
                    "strict_trigger_date": "2025-03-15",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "vendor_note": "",
                },
            ]
        )
        vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

        actionability_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "strict_backed_candidate",
                    "strict_trigger_date": "2025-03-10",
                    "actionability_v3": "",
                },
                {
                    "site": "demo",
                    "panel_id": "lenient_only_candidate",
                    "strict_trigger_date": "2025-03-11",
                    "actionability_v3": "",
                },
                {
                    "site": "demo",
                    "panel_id": "keep_review_case",
                    "strict_trigger_date": "2025-03-12",
                    "actionability_v3": "singleton_review",
                },
                {
                    "site": "demo",
                    "panel_id": "baseline_maint_tp",
                    "strict_trigger_date": "2025-03-13",
                    "actionability_v3": "maintenance_candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "manual_negative_fp",
                    "strict_trigger_date": "2025-03-14",
                    "actionability_v3": "maintenance_candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "no_truth_excluded",
                    "strict_trigger_date": "2025-03-15",
                    "actionability_v3": "",
                },
            ]
        )
        original_actionability_csv = actionability_df.to_csv(index=False)
        actionability_df.to_csv(
            share_dir / "critical_actionability_shadow_v3_latest.csv",
            index=False,
            encoding="utf-8-sig",
        )

        audit_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "strict_backed_candidate",
                    "strict_trigger_date": "2025-03-10",
                    "gap_bucket": "clean_confirmed_fault_review_gap",
                    "promotion_hypothesis": "candidate_for_maintenance_shadow",
                    "appears_in_strict": 1,
                    "appears_in_lenient": 1,
                    "vendor_fault_family": "group_or_inverter_side_like",
                    "note": "strict-backed candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "lenient_only_candidate",
                    "strict_trigger_date": "2025-03-11",
                    "gap_bucket": "clean_confirmed_fault_review_gap",
                    "promotion_hypothesis": "candidate_for_maintenance_shadow",
                    "appears_in_strict": 0,
                    "appears_in_lenient": 1,
                    "vendor_fault_family": "open_or_device_issue_like",
                    "note": "lenient-only candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "keep_review_case",
                    "strict_trigger_date": "2025-03-12",
                    "gap_bucket": "primary_singleton_review_gap",
                    "promotion_hypothesis": "keep_as_review",
                    "appears_in_strict": 1,
                    "appears_in_lenient": 1,
                    "vendor_fault_family": "diode_like",
                    "note": "keep review case",
                },
            ]
        )
        audit_df.to_csv(share_dir / "maintenance_gap_audit_cases_v1.csv", index=False, encoding="utf-8-sig")

        baseline_diag = pd.DataFrame(
            [
                {
                    "truth_mode": "strict",
                    "prediction_mode": "maintenance",
                    "source_split": "overall",
                    "f1": 0.4,
                },
                {
                    "truth_mode": "lenient",
                    "prediction_mode": "maintenance",
                    "source_split": "overall",
                    "f1": 0.333333,
                },
            ]
        )
        baseline_diag.to_csv(share_dir / "full_algorithm_f1_summary_v3.csv", index=False, encoding="utf-8-sig")

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        summary_df = pd.read_csv(share_dir / "maintenance_shadow_f1_summary_v1.csv", encoding="utf-8-sig")
        changes_df = pd.read_csv(share_dir / "maintenance_shadow_case_changes_v1.csv", encoding="utf-8-sig")
        sets_df = pd.read_csv(share_dir / "maintenance_shadow_promotion_sets_v1.csv", encoding="utf-8-sig")

        strict_baseline = summary_df.loc[
            (summary_df["scenario"] == "baseline_v3")
            & (summary_df["truth_mode"] == "strict")
            & (summary_df["source_split"] == "overall")
        ].iloc[0]
        assert_true(int(strict_baseline["tp"]) == 1, "baseline strict tp mismatch")
        assert_true(int(strict_baseline["fp"]) == 1, "baseline strict fp mismatch")
        assert_true(int(strict_baseline["fn"]) == 2, "baseline strict fn mismatch")
        assert_true(int(strict_baseline["tn"]) == 0, "baseline strict tn mismatch")
        assert_close(float(strict_baseline["f1"]), 0.4, "baseline strict f1")

        strict_shadow = summary_df.loc[
            (summary_df["scenario"] == "strict_backed_shadow")
            & (summary_df["truth_mode"] == "strict")
            & (summary_df["source_split"] == "overall")
        ].iloc[0]
        assert_true(int(strict_shadow["tp"]) == 2, "strict-backed strict tp mismatch")
        assert_true(int(strict_shadow["promoted_case_count"]) == 1, "strict-backed promoted count mismatch")
        assert_true(
            int(strict_shadow["promoted_lenient_only_count"]) == 0,
            "strict-backed should not include lenient-only promotions",
        )

        lenient_full = summary_df.loc[
            (summary_df["scenario"] == "full_candidate_shadow")
            & (summary_df["truth_mode"] == "lenient")
            & (summary_df["source_split"] == "overall")
        ].iloc[0]
        assert_true(int(lenient_full["tp"]) == 3, "full shadow lenient tp mismatch")
        assert_true(int(lenient_full["promoted_case_count"]) == 2, "full shadow promoted count mismatch")
        assert_true(
            int(lenient_full["promoted_lenient_only_count"]) == 1,
            "full shadow should include one lenient-only promotion",
        )

        assert_true(
            not changes_df["panel_id"].eq("keep_review_case").any(),
            "keep_as_review rows must never be promoted",
        )
        strict_change = changes_df.loc[
            (changes_df["scenario"] == "strict_backed_shadow")
            & (changes_df["panel_id"] == "strict_backed_candidate")
        ].iloc[0]
        assert_true(
            strict_change["promotion_tier"] == "strict_backed",
            "strict-backed scenario should keep strict_backed tier",
        )
        lenient_change = changes_df.loc[
            (changes_df["scenario"] == "full_candidate_shadow")
            & (changes_df["panel_id"] == "lenient_only_candidate")
        ].iloc[0]
        assert_true(
            lenient_change["promotion_tier"] == "lenient_only",
            "full shadow should include lenient-only promotion tier",
        )

        sets_row = sets_df.loc[sets_df["panel_id"].eq("lenient_only_candidate")].iloc[0]
        assert_true(int(sets_row["in_strict_backed_shadow"]) == 0, "lenient-only case must stay out of strict-backed set")
        assert_true(int(sets_row["in_full_candidate_shadow"]) == 1, "lenient-only case must be in full shadow set")

        actionability_after = pd.read_csv(
            share_dir / "critical_actionability_shadow_v3_latest.csv",
            encoding="utf-8-sig",
        )
        assert_true(
            actionability_after.to_csv(index=False) == original_actionability_csv,
            "shadow evaluator must not modify official actionability output",
        )

        for col in ["f1", "precision", "recall"]:
            valid = summary_df[col].dropna().between(0.0, 1.0, inclusive="both").all()
            assert_true(bool(valid), f"{col} must remain within [0,1]")

    smoke_gap_res = run([sys.executable, str(smoke_gap)], root)
    assert_true(
        smoke_gap_res.returncode == 0,
        f"existing maintenance gap audit smoke failed:\n{smoke_gap_res.stdout}\n{smoke_gap_res.stderr}",
    )

    print("[OK] outputs generate")
    print("[OK] baseline_v3 reproduces current maintenance baseline on synthetic fixture")
    print("[OK] strict_backed_shadow promotes only appears_in_strict == 1 candidates")
    print("[OK] full_candidate_shadow promotes both strict-backed and lenient-only candidates")
    print("[OK] keep_as_review rows are never promoted")
    print("[OK] no official prediction outputs are modified")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
