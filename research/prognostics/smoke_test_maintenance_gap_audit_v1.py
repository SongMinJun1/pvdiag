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


def has_truth_filled_template(root: Path) -> bool:
    template_path = root / "_share" / "field_truth_template.csv"
    if not template_path.exists():
        return False
    df = pd.read_csv(template_path, encoding="utf-8-sig")
    if df.empty:
        return False
    truth_cols = [
        col
        for col in [
            "fault_confirmed",
            "true_fault_type",
            "fault_start_date",
            "fault_end_date",
            "maintenance_action",
            "note",
        ]
        if col in df.columns
    ]
    if not truth_cols:
        return False
    filled = df[truth_cols].apply(
        lambda col: col.map(lambda value: bool(str(value).strip()) if not pd.isna(value) else False)
    )
    return bool(filled.any(axis=1).any())


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_maintenance_gap_audit_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        share_dir.mkdir(parents=True, exist_ok=True)

        errors_df = pd.DataFrame(
            [
                {
                    "truth_mode": "strict",
                    "prediction_mode": "maintenance",
                    "source_split": "overall",
                    "site": "demo",
                    "panel_id": "clean_confirmed",
                    "strict_trigger_date": "2025-03-10",
                    "truth_source": "vendor_truth",
                    "truth_label": "positive",
                    "actionability_v3": "",
                    "derived_actionability_v3": "singleton_review",
                    "final_actionability_v3": "singleton_review",
                    "prediction_label": "negative",
                    "error_type": "fn",
                    "prediction_source": "confirmed_fault_clean",
                    "parsed_strict_method": "confirmed_fault_flag",
                    "parsed_shadow_frac": 0.0,
                    "parsed_group_off_frac": 0.0,
                    "parsed_recovery_reset": "no",
                    "candidate_validity": "",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "group_or_inverter_side_like",
                    "review_priority": "P1",
                    "note": "clean confirmed row",
                },
                {
                    "truth_mode": "lenient",
                    "prediction_mode": "maintenance",
                    "source_split": "overall",
                    "site": "demo",
                    "panel_id": "clean_confirmed",
                    "strict_trigger_date": "2025-03-10",
                    "truth_source": "vendor_truth",
                    "truth_label": "positive",
                    "actionability_v3": "",
                    "derived_actionability_v3": "singleton_review",
                    "final_actionability_v3": "singleton_review",
                    "prediction_label": "negative",
                    "error_type": "fn",
                    "prediction_source": "confirmed_fault_clean",
                    "parsed_strict_method": "confirmed_fault_flag",
                    "parsed_shadow_frac": 0.0,
                    "parsed_group_off_frac": 0.0,
                    "parsed_recovery_reset": "no",
                    "candidate_validity": "",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "group_or_inverter_side_like",
                    "review_priority": "P1",
                    "note": "clean confirmed row",
                },
                {
                    "truth_mode": "strict",
                    "prediction_mode": "maintenance",
                    "source_split": "overall",
                    "site": "demo",
                    "panel_id": "primary_singleton",
                    "strict_trigger_date": "2025-03-11",
                    "truth_source": "vendor_truth",
                    "truth_label": "positive",
                    "actionability_v3": "singleton_review",
                    "derived_actionability_v3": "",
                    "final_actionability_v3": "singleton_review",
                    "prediction_label": "negative",
                    "error_type": "fn",
                    "prediction_source": "primary_actionability_v3",
                    "parsed_strict_method": "critical_fault_flag",
                    "parsed_shadow_frac": 0.0,
                    "parsed_group_off_frac": 0.0,
                    "parsed_recovery_reset": "no",
                    "candidate_validity": "",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "diode_like",
                    "review_priority": "P1",
                    "note": "primary singleton row",
                },
                {
                    "truth_mode": "strict",
                    "prediction_mode": "maintenance",
                    "source_split": "overall",
                    "site": "demo",
                    "panel_id": "confounded_review",
                    "strict_trigger_date": "2025-03-12",
                    "truth_source": "vendor_truth",
                    "truth_label": "positive",
                    "actionability_v3": "",
                    "derived_actionability_v3": "monitor_only",
                    "final_actionability_v3": "monitor_only",
                    "prediction_label": "negative",
                    "error_type": "fn",
                    "prediction_source": "confirmed_fault_confounded",
                    "parsed_strict_method": "confirmed_fault_flag",
                    "parsed_shadow_frac": 0.3,
                    "parsed_group_off_frac": 0.0,
                    "parsed_recovery_reset": "yes",
                    "candidate_validity": "",
                    "vendor_reply_class": "vendor_rejected",
                    "vendor_fault_family": "none_visible",
                    "review_priority": "P2",
                    "note": "confounded row",
                },
            ]
        )
        errors_df.to_csv(share_dir / "full_algorithm_case_errors_v3.csv", index=False, encoding="utf-8-sig")

        summary_df = pd.DataFrame(
            [
                {
                    "truth_mode": "strict",
                    "prediction_mode": "operational",
                    "source_split": "overall",
                    "f1": 1.0,
                    "scored_rows": 3,
                    "primary_coverage": 0.666667,
                    "effective_coverage": 1.0,
                },
                {
                    "truth_mode": "lenient",
                    "prediction_mode": "operational",
                    "source_split": "overall",
                    "f1": 1.0,
                    "scored_rows": 3,
                    "primary_coverage": 0.666667,
                    "effective_coverage": 1.0,
                },
            ]
        )
        summary_df.to_csv(share_dir / "full_algorithm_f1_summary_v3.csv", index=False, encoding="utf-8-sig")

        actionability_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "primary_singleton",
                    "strict_trigger_date": "2025-03-11",
                    "critical_phenotype_v3": "singleton_borderline_review",
                    "actionability_v3": "singleton_review",
                },
                {
                    "site": "demo",
                    "panel_id": "clean_confirmed",
                    "strict_trigger_date": "2025-03-10",
                    "critical_phenotype_v3": "",
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

        onset_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "clean_confirmed",
                    "strict_trigger_date": "2025-03-10",
                    "days_earlier_than_trigger": 12,
                    "onset_confidence": "high",
                    "onset_method": "persistent_5of7",
                },
                {
                    "site": "demo",
                    "panel_id": "primary_singleton",
                    "strict_trigger_date": "2025-03-11",
                    "days_earlier_than_trigger": 0,
                    "onset_confidence": "medium",
                    "onset_method": "strict_trigger_fallback",
                },
                {
                    "site": "demo",
                    "panel_id": "confounded_review",
                    "strict_trigger_date": "2025-03-12",
                    "days_earlier_than_trigger": 0,
                    "onset_confidence": "medium",
                    "onset_method": "strict_trigger_fallback",
                },
            ]
        )
        onset_df.to_csv(share_dir / "panel_onset_shadow_latest.csv", index=False, encoding="utf-8-sig")

        vendor_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "clean_confirmed",
                    "strict_trigger_date": "2025-03-10",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "group_or_inverter_side_like",
                },
                {
                    "site": "demo",
                    "panel_id": "primary_singleton",
                    "strict_trigger_date": "2025-03-11",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "diode_like",
                },
                {
                    "site": "demo",
                    "panel_id": "confounded_review",
                    "strict_trigger_date": "2025-03-12",
                    "vendor_reply_class": "vendor_rejected",
                    "vendor_fault_family": "none_visible",
                },
            ]
        )
        vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        cases_df = pd.read_csv(share_dir / "maintenance_gap_audit_cases_v1.csv", encoding="utf-8-sig")
        summary_out = pd.read_csv(share_dir / "maintenance_gap_audit_summary_v1.csv", encoding="utf-8-sig")
        promotion_df = pd.read_csv(
            share_dir / "maintenance_gap_promotion_candidates_v1.csv",
            encoding="utf-8-sig",
        )

        assert_true(len(cases_df) == 3, f"expected 3 unique strict cases, got {len(cases_df)}")

        clean_row = cases_df.loc[cases_df["panel_id"].eq("clean_confirmed")].iloc[0]
        assert_true(int(clean_row["appears_in_strict"]) == 1, "clean row must appear in strict")
        assert_true(int(clean_row["appears_in_lenient"]) == 1, "clean row must appear in lenient")
        assert_true(
            clean_row["gap_bucket"] == "clean_confirmed_fault_review_gap",
            "clean confirmed row should map to clean_confirmed_fault_review_gap",
        )
        assert_true(
            clean_row["promotion_hypothesis"] == "candidate_for_maintenance_shadow",
            "clean confirmed row should become candidate_for_maintenance_shadow",
        )

        primary_row = cases_df.loc[cases_df["panel_id"].eq("primary_singleton")].iloc[0]
        assert_true(
            primary_row["gap_bucket"] == "primary_singleton_review_gap",
            "primary singleton row should map to primary_singleton_review_gap",
        )
        assert_true(
            primary_row["promotion_hypothesis"] == "keep_as_review",
            "primary singleton row should stay keep_as_review",
        )

        confounded_row = cases_df.loc[cases_df["panel_id"].eq("confounded_review")].iloc[0]
        assert_true(
            confounded_row["gap_bucket"] == "confounded_review_gap",
            "confounded row should map to confounded_review_gap",
        )
        assert_true(
            confounded_row["promotion_hypothesis"] == "keep_as_review",
            "confounded row should stay keep_as_review",
        )

        assert_true(len(promotion_df) == 1, f"expected 1 promotion candidate, got {len(promotion_df)}")
        assert_true(
            promotion_df.iloc[0]["panel_id"] == "clean_confirmed",
            "promotion candidates should only include clean confirmed row",
        )

        summary_top = summary_out.loc[summary_out["record_type"].eq("summary")].iloc[0]
        assert_true(int(summary_top["total_unique_gap_cases"]) == 3, "summary unique gap case count mismatch")
        assert_true(
            int(summary_top["count_candidate_for_maintenance_shadow"]) == 1,
            "summary promotion candidate count mismatch",
        )
        assert_true(
            int(summary_top["count_keep_as_review"]) == 2,
            "summary keep_as_review count mismatch",
        )

        actionability_after = pd.read_csv(
            share_dir / "critical_actionability_shadow_v3_latest.csv",
            encoding="utf-8-sig",
        )
        assert_true(
            actionability_after.to_csv(index=False) == original_actionability_csv,
            "audit must not modify current actionability output",
        )

    print("[OK] audit outputs generate")
    print("[OK] strict/lenient duplicate maintenance FN rows collapse into one unique strict-case row")
    print("[OK] synthetic clean confirmed_fault_clean row becomes candidate_for_maintenance_shadow")
    print("[OK] synthetic primary_actionability_v3 singleton row becomes keep_as_review")
    print("[OK] synthetic confounded row becomes keep_as_review")
    print("[OK] no current prediction/routing outputs are modified")
    if has_truth_filled_template(root):
        print("[SKIP] existing repo smoke-path check skipped because field_truth_template contains user-entered truth rows")
    else:
        print("[OK] existing repo smoke-path check is eligible")


if __name__ == "__main__":
    main()
