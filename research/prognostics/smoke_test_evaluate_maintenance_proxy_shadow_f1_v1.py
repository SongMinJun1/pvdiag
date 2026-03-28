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
    build_script = root / "research" / "prognostics" / "evaluate_maintenance_proxy_shadow_f1_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_evaluate_maintenance_shadow_f1_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        data_dir = tmp_root / "data" / "demo" / "out"
        share_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        reaudit_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "proxy_group_tp.1.0",
                    "strict_trigger_date": "2025-03-10",
                    "candidate_validity": "",
                    "onset_confidence": "medium",
                    "reason_summary": "",
                    "review_priority": "P1",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "group_or_inverter_side_like",
                    "note": "proxy group tp",
                },
                {
                    "site": "demo",
                    "panel_id": "site_only_should_not_trigger.2.0",
                    "strict_trigger_date": "2025-03-11",
                    "candidate_validity": "",
                    "onset_confidence": "medium",
                    "reason_summary": "",
                    "review_priority": "P1",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "group_or_inverter_side_like",
                    "note": "site only positive",
                },
                {
                    "site": "demo",
                    "panel_id": "existing_maint.3.0",
                    "strict_trigger_date": "2025-03-12",
                    "candidate_validity": "",
                    "onset_confidence": "high",
                    "reason_summary": "",
                    "review_priority": "P1",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "diode_like",
                    "note": "already maintenance",
                },
                {
                    "site": "demo",
                    "panel_id": "manual_negative_fp.4.0",
                    "strict_trigger_date": "2025-03-13",
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
                    "panel_id": "no_truth_excluded.5.0",
                    "strict_trigger_date": "2025-03-14",
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
                    "panel_id": "proxy_group_tp.1.0",
                    "strict_trigger_date": "2025-03-10",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "group_or_inverter_side_like",
                    "vendor_note": "proxy group tp",
                },
                {
                    "site": "demo",
                    "panel_id": "site_only_should_not_trigger.2.0",
                    "strict_trigger_date": "2025-03-11",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "group_or_inverter_side_like",
                    "vendor_note": "site only positive",
                },
                {
                    "site": "demo",
                    "panel_id": "existing_maint.3.0",
                    "strict_trigger_date": "2025-03-12",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "diode_like",
                    "vendor_note": "existing maintenance",
                },
            ]
        )
        vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

        actionability_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "proxy_group_tp.1.0",
                    "strict_trigger_date": "2025-03-10",
                    "actionability_v3": "",
                },
                {
                    "site": "demo",
                    "panel_id": "site_only_should_not_trigger.2.0",
                    "strict_trigger_date": "2025-03-11",
                    "actionability_v3": "",
                },
                {
                    "site": "demo",
                    "panel_id": "existing_maint.3.0",
                    "strict_trigger_date": "2025-03-12",
                    "actionability_v3": "maintenance_candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "manual_negative_fp.4.0",
                    "strict_trigger_date": "2025-03-13",
                    "actionability_v3": "maintenance_candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "no_truth_excluded.5.0",
                    "strict_trigger_date": "2025-03-14",
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
                    "panel_id": "proxy_group_tp.1.0",
                    "strict_trigger_date": "2025-03-10",
                    "days_earlier_than_trigger": 0,
                    "onset_confidence": "medium",
                    "onset_method": "strict_trigger_fallback",
                    "reason_summary": "strict_method=confirmed_fault_flag|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0",
                },
                {
                    "site": "demo",
                    "panel_id": "site_only_should_not_trigger.2.0",
                    "strict_trigger_date": "2025-03-11",
                    "days_earlier_than_trigger": 0,
                    "onset_confidence": "medium",
                    "onset_method": "strict_trigger_fallback",
                    "reason_summary": "strict_method=confirmed_fault_flag|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0",
                },
                {
                    "site": "demo",
                    "panel_id": "existing_maint.3.0",
                    "strict_trigger_date": "2025-03-12",
                    "days_earlier_than_trigger": 0,
                    "onset_confidence": "medium",
                    "onset_method": "strict_trigger_fallback",
                    "reason_summary": "strict_method=confirmed_fault_flag|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0",
                },
                {
                    "site": "demo",
                    "panel_id": "manual_negative_fp.4.0",
                    "strict_trigger_date": "2025-03-13",
                    "days_earlier_than_trigger": 0,
                    "onset_confidence": "medium",
                    "onset_method": "strict_trigger_fallback",
                    "reason_summary": "strict_method=confirmed_fault_flag|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0",
                },
                {
                    "site": "demo",
                    "panel_id": "no_truth_excluded.5.0",
                    "strict_trigger_date": "2025-03-14",
                    "days_earlier_than_trigger": 0,
                    "onset_confidence": "medium",
                    "onset_method": "strict_trigger_fallback",
                    "reason_summary": "strict_method=confirmed_fault_flag|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0",
                },
            ]
        )
        onset_df.to_csv(share_dir / "panel_onset_shadow_latest.csv", index=False, encoding="utf-8-sig")

        core_df = pd.DataFrame(
            [
                {
                    "panel_id": "proxy_group_tp.1.0",
                    "date": "2025-03-10",
                    "mid_ratio": 0.0,
                    "last_ratio": 0.0,
                    "mid_v_ratio": 1.10,
                    "mid_i_ratio": 0.0,
                    "v_drop": -0.10,
                    "v_ref_ok": False,
                    "coverage_mid": 1.0,
                    "shadow_like": False,
                    "group_off_like": False,
                    "group_key_base": "proxy_group_tp.1",
                },
                {
                    "panel_id": "proxy_group_tp.1.1",
                    "date": "2025-03-10",
                    "mid_ratio": 0.0,
                    "last_ratio": 0.0,
                    "mid_v_ratio": 1.08,
                    "mid_i_ratio": 0.0,
                    "v_drop": -0.08,
                    "v_ref_ok": False,
                    "coverage_mid": 1.0,
                    "shadow_like": False,
                    "group_off_like": False,
                    "group_key_base": "proxy_group_tp.1",
                },
                {
                    "panel_id": "site_only_should_not_trigger.2.0",
                    "date": "2025-03-11",
                    "mid_ratio": 0.0,
                    "last_ratio": 0.0,
                    "mid_v_ratio": 1.12,
                    "mid_i_ratio": 0.0,
                    "v_drop": -0.12,
                    "v_ref_ok": False,
                    "coverage_mid": 1.0,
                    "shadow_like": False,
                    "group_off_like": False,
                    "group_key_base": "site_only_should_not_trigger.2",
                },
                {
                    "panel_id": "other_group_a.9.0",
                    "date": "2025-03-11",
                    "mid_ratio": 0.0,
                    "last_ratio": 0.0,
                    "mid_v_ratio": 1.10,
                    "mid_i_ratio": 0.0,
                    "v_drop": -0.10,
                    "v_ref_ok": False,
                    "coverage_mid": 1.0,
                    "shadow_like": False,
                    "group_off_like": False,
                    "group_key_base": "other_group_a.9",
                },
                {
                    "panel_id": "other_group_b.9.0",
                    "date": "2025-03-11",
                    "mid_ratio": 0.0,
                    "last_ratio": 0.0,
                    "mid_v_ratio": 1.14,
                    "mid_i_ratio": 0.0,
                    "v_drop": -0.14,
                    "v_ref_ok": False,
                    "coverage_mid": 1.0,
                    "shadow_like": False,
                    "group_off_like": False,
                    "group_key_base": "other_group_b.9",
                },
                {
                    "panel_id": "existing_maint.3.0",
                    "date": "2025-03-12",
                    "mid_ratio": 0.0,
                    "last_ratio": 0.0,
                    "mid_v_ratio": 1.11,
                    "mid_i_ratio": 0.0,
                    "v_drop": -0.11,
                    "v_ref_ok": False,
                    "coverage_mid": 1.0,
                    "shadow_like": False,
                    "group_off_like": False,
                    "group_key_base": "existing_maint.3",
                },
                {
                    "panel_id": "existing_maint.3.1",
                    "date": "2025-03-12",
                    "mid_ratio": 0.0,
                    "last_ratio": 0.0,
                    "mid_v_ratio": 1.07,
                    "mid_i_ratio": 0.0,
                    "v_drop": -0.07,
                    "v_ref_ok": False,
                    "coverage_mid": 1.0,
                    "shadow_like": False,
                    "group_off_like": False,
                    "group_key_base": "existing_maint.3",
                },
                {
                    "panel_id": "manual_negative_fp.4.0",
                    "date": "2025-03-13",
                    "mid_ratio": 0.4,
                    "last_ratio": 0.4,
                    "mid_v_ratio": 0.9,
                    "mid_i_ratio": 0.8,
                    "v_drop": 0.2,
                    "v_ref_ok": True,
                    "coverage_mid": 1.0,
                    "shadow_like": False,
                    "group_off_like": False,
                    "group_key_base": "manual_negative_fp.4",
                },
                {
                    "panel_id": "no_truth_excluded.5.0",
                    "date": "2025-03-14",
                    "mid_ratio": 0.3,
                    "last_ratio": 0.3,
                    "mid_v_ratio": 0.8,
                    "mid_i_ratio": 0.7,
                    "v_drop": 0.2,
                    "v_ref_ok": True,
                    "coverage_mid": 1.0,
                    "shadow_like": False,
                    "group_off_like": False,
                    "group_key_base": "no_truth_excluded.5",
                },
            ]
        )
        core_df.to_csv(data_dir / "panel_day_core.csv", index=False, encoding="utf-8-sig")

        run_res = run(
            [
                sys.executable,
                str(build_script),
                "--root",
                str(tmp_root),
                "--sites",
                "demo",
            ],
            root,
        )
        assert_true(run_res.returncode == 0, f"script failed:\n{run_res.stdout}\n{run_res.stderr}")

        summary_df = pd.read_csv(share_dir / "maintenance_proxy_shadow_f1_summary_v1.csv", encoding="utf-8-sig")
        selected_df = pd.read_csv(share_dir / "maintenance_proxy_shadow_selected_cases_v1.csv", encoding="utf-8-sig")
        errors_df = pd.read_csv(share_dir / "maintenance_proxy_shadow_case_errors_v1.csv", encoding="utf-8-sig")

        assert_true(not summary_df.empty, "summary output is empty")
        assert_true(not errors_df.empty, "case errors output is empty")
        assert_true(len(selected_df) == 1, f"expected exactly one selected proxy case, got {len(selected_df)}")
        assert_true(
            selected_df.iloc[0]["panel_id"] == "proxy_group_tp.1.0",
            "proxy rule should select only clean confirmed same-group collapse case",
        )
        assert_true(
            "site_only_should_not_trigger.2.0" not in set(selected_df["panel_id"]),
            "site-level collapse alone should not trigger promotion",
        )
        assert_true(
            "existing_maint.3.0" not in set(selected_df["panel_id"]),
            "existing maintenance_candidate row must not be double-promoted",
        )

        baseline_row = summary_df.loc[
            (summary_df["scenario"] == "baseline_v3")
            & (summary_df["truth_mode"] == "strict")
            & (summary_df["source_split"] == "overall")
        ].iloc[0]
        shadow_row = summary_df.loc[
            (summary_df["scenario"] == "same_group_group_like_shadow")
            & (summary_df["truth_mode"] == "strict")
            & (summary_df["source_split"] == "overall")
        ].iloc[0]
        assert_close(float(baseline_row["tp"]), 1.0, "baseline tp")
        assert_close(float(baseline_row["fp"]), 1.0, "baseline fp")
        assert_close(float(baseline_row["fn"]), 2.0, "baseline fn")
        assert_close(float(baseline_row["f1"]), 0.4, "baseline f1")
        assert_close(float(shadow_row["tp"]), 2.0, "shadow tp")
        assert_close(float(shadow_row["fp"]), 1.0, "shadow fp")
        assert_close(float(shadow_row["fn"]), 1.0, "shadow fn")
        assert_close(float(shadow_row["f1"]), 0.666667, "shadow f1")
        assert_true(float(shadow_row["promoted_case_count"]) == 1.0, "shadow promoted_case_count should be 1")

        for col in ["precision", "recall", "f1"]:
            assert_true(summary_df[col].between(0, 1).all(), f"{col} must remain within [0,1]")

        current_actionability_after = (share_dir / "critical_actionability_shadow_v3_latest.csv").read_text(encoding="utf-8-sig")
        assert_true(
            current_actionability_after == original_actionability_csv,
            "official actionability output must not be modified",
        )

        print("[OK] outputs generate")
        print("[OK] baseline_v3 reproduces current maintenance baseline on synthetic fixture")
        print("[OK] proxy rule promotes only clean confirmed group-like same-group collapse cases")
        print("[OK] site-level collapse alone does not trigger promotion")
        print("[OK] rows already maintenance_candidate are not double-promoted")
        print("[OK] no official prediction outputs are modified")

    safe_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(safe_res.returncode == 0, f"existing safe smoke failed:\n{safe_res.stdout}\n{safe_res.stderr}")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
