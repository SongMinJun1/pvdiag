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
    build_script = root / "research" / "prognostics" / "build_maintenance_promotion_proxy_audit_v1.py"
    smoke_shadow = root / "research" / "prognostics" / "smoke_test_evaluate_maintenance_shadow_f1_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        share_dir.mkdir(parents=True, exist_ok=True)
        data_dir = tmp_root / "data"
        (data_dir / "demo" / "out").mkdir(parents=True, exist_ok=True)

        promotion_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "strict_candidate.0.0",
                    "strict_trigger_date": "2025-03-10",
                    "gap_bucket": "clean_confirmed_fault_review_gap",
                    "promotion_hypothesis": "candidate_for_maintenance_shadow",
                    "appears_in_strict": 1,
                    "appears_in_lenient": 1,
                    "in_strict_backed_shadow": 1,
                    "in_full_candidate_shadow": 1,
                    "vendor_fault_family": "group_or_inverter_side_like",
                    "note": "strict candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "lenient_candidate.1.0",
                    "strict_trigger_date": "2025-03-11",
                    "gap_bucket": "clean_confirmed_fault_review_gap",
                    "promotion_hypothesis": "candidate_for_maintenance_shadow",
                    "appears_in_strict": 0,
                    "appears_in_lenient": 1,
                    "in_strict_backed_shadow": 0,
                    "in_full_candidate_shadow": 1,
                    "vendor_fault_family": "open_or_device_issue_like",
                    "note": "lenient-only candidate",
                },
            ]
        )
        original_promotion_csv = promotion_df.to_csv(index=False)
        promotion_df.to_csv(share_dir / "maintenance_shadow_promotion_sets_v1.csv", index=False, encoding="utf-8-sig")

        audit_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "strict_candidate.0.0",
                    "strict_trigger_date": "2025-03-10",
                    "gap_bucket": "clean_confirmed_fault_review_gap",
                    "promotion_hypothesis": "candidate_for_maintenance_shadow",
                    "prediction_source": "confirmed_fault_clean",
                    "critical_phenotype_v3": "",
                    "actionability_v3": "",
                    "derived_actionability_v3": "singleton_review",
                    "final_actionability_v3": "singleton_review",
                    "parsed_strict_method": "confirmed_fault_flag",
                    "parsed_shadow_frac": 0.0,
                    "parsed_group_off_frac": 0.0,
                    "parsed_recovery_reset": "no",
                    "days_earlier_than_trigger": 0,
                    "onset_confidence": "medium",
                    "onset_method": "strict_trigger_fallback",
                    "note": "strict candidate",
                },
                {
                    "site": "demo",
                    "panel_id": "lenient_candidate.1.0",
                    "strict_trigger_date": "2025-03-11",
                    "gap_bucket": "clean_confirmed_fault_review_gap",
                    "promotion_hypothesis": "candidate_for_maintenance_shadow",
                    "prediction_source": "confirmed_fault_clean",
                    "critical_phenotype_v3": "",
                    "actionability_v3": "",
                    "derived_actionability_v3": "singleton_review",
                    "final_actionability_v3": "singleton_review",
                    "parsed_strict_method": "confirmed_fault_flag",
                    "parsed_shadow_frac": 0.0,
                    "parsed_group_off_frac": 0.0,
                    "parsed_recovery_reset": "no",
                    "days_earlier_than_trigger": 45,
                    "onset_confidence": "high",
                    "onset_method": "persistent_5of7",
                    "note": "lenient candidate",
                },
            ]
        )
        audit_df.to_csv(share_dir / "maintenance_gap_audit_cases_v1.csv", index=False, encoding="utf-8-sig")

        actionability_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "strict_candidate.0.0",
                    "strict_trigger_date": "2025-03-10",
                    "anchor_date": "2025-03-10",
                    "critical_phenotype_v2": "singleton_borderline_review",
                    "critical_phenotype_v3": "singleton_borderline_review",
                    "cluster_guard_flag": 0,
                    "same_site_borderline_count_anchor_date": 1,
                    "same_group_borderline_count_anchor_date": 1,
                },
                {
                    "site": "demo",
                    "panel_id": "lenient_candidate.1.0",
                    "strict_trigger_date": "2025-03-11",
                    "anchor_date": "2025-03-11",
                    "critical_phenotype_v2": "singleton_borderline_review",
                    "critical_phenotype_v3": "singleton_borderline_review",
                    "cluster_guard_flag": 0,
                    "same_site_borderline_count_anchor_date": 1,
                    "same_group_borderline_count_anchor_date": 1,
                },
            ]
        )
        original_actionability_csv = actionability_df.to_csv(index=False)
        actionability_df.to_csv(share_dir / "critical_actionability_shadow_v3_latest.csv", index=False, encoding="utf-8-sig")

        v2_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "strict_candidate.0.0",
                    "strict_trigger_date": "2025-03-10",
                    "valid_days": 0,
                    "evidence_days": 0,
                    "evidence_ratio": 0.0,
                    "mid_ratio_win_median": 0.0,
                    "mid_v_ratio_win_median": 1.2,
                    "mid_i_ratio_win_median": 0.0,
                    "v_drop_win_median": 0.0,
                    "coverage_mid_win_median": 1.0,
                    "shape_support_flag": 0,
                },
                {
                    "site": "demo",
                    "panel_id": "lenient_candidate.1.0",
                    "strict_trigger_date": "2025-03-11",
                    "valid_days": 0,
                    "evidence_days": 0,
                    "evidence_ratio": 0.0,
                    "mid_ratio_win_median": 0.0,
                    "mid_v_ratio_win_median": 0.0,
                    "mid_i_ratio_win_median": 0.7,
                    "v_drop_win_median": 1.0,
                    "coverage_mid_win_median": 0.75,
                    "shape_support_flag": 0,
                },
            ]
        )
        v2_df.to_csv(share_dir / "critical_phenotype_shadow_v2_latest.csv", index=False, encoding="utf-8-sig")

        panel_onset_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "strict_candidate.0.0",
                    "strict_trigger_date": "2025-03-10",
                    "days_earlier_than_trigger": 0,
                    "onset_confidence": "medium",
                    "onset_method": "strict_trigger_fallback",
                },
                {
                    "site": "demo",
                    "panel_id": "lenient_candidate.1.0",
                    "strict_trigger_date": "2025-03-11",
                    "days_earlier_than_trigger": 45,
                    "onset_confidence": "high",
                    "onset_method": "persistent_5of7",
                },
            ]
        )
        panel_onset_df.to_csv(share_dir / "panel_onset_shadow_latest.csv", index=False, encoding="utf-8-sig")

        core_df = pd.DataFrame(
            [
                {
                    "date": "2025-03-10",
                    "panel_id": "strict_candidate.0.0",
                    "group_key_base": "strict_candidate.0",
                    "mid_ratio": 0.0,
                    "last_ratio": 0.0,
                    "mid_v_ratio": 1.2,
                    "mid_i_ratio": 0.0,
                    "v_drop": 0.0,
                    "v_ref_ok": False,
                    "coverage_mid": 1.0,
                    "shadow_like": False,
                    "group_off_like": False,
                },
                {
                    "date": "2025-03-10",
                    "panel_id": "strict_candidate.0.1",
                    "group_key_base": "strict_candidate.0",
                    "mid_ratio": 0.0,
                    "last_ratio": 0.0,
                    "mid_v_ratio": 1.1,
                    "mid_i_ratio": 0.0,
                    "v_drop": 0.0,
                    "v_ref_ok": False,
                    "coverage_mid": 1.0,
                    "shadow_like": False,
                    "group_off_like": False,
                },
                {
                    "date": "2025-03-11",
                    "panel_id": "lenient_candidate.1.0",
                    "group_key_base": "lenient_candidate.1",
                    "mid_ratio": 0.0,
                    "last_ratio": 0.0,
                    "mid_v_ratio": 0.0,
                    "mid_i_ratio": 0.7,
                    "v_drop": 1.0,
                    "v_ref_ok": True,
                    "coverage_mid": 0.75,
                    "shadow_like": False,
                    "group_off_like": False,
                },
            ]
        )
        core_df.to_csv(data_dir / "demo" / "out" / "panel_day_core.csv", index=False, encoding="utf-8-sig")

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        cases_df = pd.read_csv(share_dir / "maintenance_promotion_proxy_cases_v1.csv", encoding="utf-8-sig")
        summary_df = pd.read_csv(share_dir / "maintenance_promotion_proxy_summary_v1.csv", encoding="utf-8-sig")
        rules_df = pd.read_csv(share_dir / "maintenance_promotion_proxy_rules_v1.csv", encoding="utf-8-sig")

        assert_true(len(cases_df) == 2, f"candidate rows must be preserved exactly, got {len(cases_df)}")

        strict_row = cases_df.loc[cases_df["panel_id"].eq("strict_candidate.0.0")].iloc[0]
        lenient_row = cases_df.loc[cases_df["panel_id"].eq("lenient_candidate.1.0")].iloc[0]
        assert_true(
            strict_row["target_proxy_tier"] == "strict_backed_candidate",
            "strict candidate tier mismatch",
        )
        assert_true(
            lenient_row["target_proxy_tier"] == "lenient_only_candidate",
            "lenient-only candidate tier mismatch",
        )
        assert_true(int(strict_row["strict_day_group_like_flag"]) == 1, "strict candidate should be group-like")
        assert_true(int(strict_row["same_group_zero_like_count"]) == 2, "strict candidate group collapse count mismatch")
        assert_true(int(lenient_row["strict_day_open_like_flag"]) == 1, "lenient-only candidate should be open-like")
        assert_true(int(lenient_row["onset_long_horizon_flag"]) == 1, "lenient-only candidate should be long-horizon")

        group_rule = rules_df.loc[rules_df["proxy_rule_id"].eq("strict_day_group_collapse")].iloc[0]
        assert_true(int(group_rule["selected_case_count"]) == 1, "group collapse selected count mismatch")
        assert_true(int(group_rule["strict_backed_hit_count"]) == 1, "group collapse strict-backed hit mismatch")
        assert_true(float(group_rule["precision_for_strict_backed"]) == 1.0, "group collapse precision mismatch")
        assert_true(float(group_rule["recall_for_strict_backed"]) == 1.0, "group collapse recall mismatch")

        open_rule = rules_df.loc[rules_df["proxy_rule_id"].eq("strict_day_open_like")].iloc[0]
        assert_true(int(open_rule["selected_case_count"]) == 1, "open-like selected count mismatch")
        assert_true(int(open_rule["lenient_only_hit_count"]) == 1, "open-like lenient hit mismatch")

        summary = summary_df.iloc[0]
        assert_true(int(summary["strict_backed_candidate_count"]) == 1, "strict_backed count mismatch")
        assert_true(int(summary["lenient_only_candidate_count"]) == 1, "lenient_only count mismatch")
        assert_true(int(summary["count_group_collapse_strict_backed"]) == 1, "strict_backed group collapse count mismatch")
        assert_true(int(summary["count_open_like_lenient_only"]) == 1, "lenient_only open-like count mismatch")

        actionability_after = pd.read_csv(
            share_dir / "critical_actionability_shadow_v3_latest.csv",
            encoding="utf-8-sig",
        )
        promotion_after = pd.read_csv(
            share_dir / "maintenance_shadow_promotion_sets_v1.csv",
            encoding="utf-8-sig",
        )
        assert_true(
            actionability_after.to_csv(index=False) == original_actionability_csv,
            "proxy audit must not modify official actionability output",
        )
        assert_true(
            promotion_after.to_csv(index=False) == original_promotion_csv,
            "proxy audit must not modify promotion-set input",
        )

    smoke_shadow_res = run([sys.executable, str(smoke_shadow)], root)
    assert_true(
        smoke_shadow_res.returncode == 0,
        f"existing maintenance-shadow smoke failed:\n{smoke_shadow_res.stdout}\n{smoke_shadow_res.stderr}",
    )

    print("[OK] outputs generate")
    print("[OK] candidate rows are preserved exactly")
    print("[OK] synthetic strict_backed and lenient_only candidates are labeled correctly")
    print("[OK] fixed proxy rules produce consistent counts")
    print("[OK] no official prediction outputs are modified")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
