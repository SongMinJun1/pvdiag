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
    build_script = root / "research" / "prognostics" / "evaluate_gpvs_fault_family_f1.py"
    smoke_v3 = root / "research" / "prognostics" / "smoke_test_critical_actionability_shadow_v3.py"
    smoke_vendor = root / "research" / "prognostics" / "smoke_test_vendor_reply_adjudication.py"
    smoke_onset = root / "research" / "prognostics" / "smoke_test_panel_onset_shadow.py"
    smoke_field = root / "research" / "prognostics" / "smoke_test_field_truth_validation.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        out_dir = tmp_root / "data" / "demo" / "out"
        share_dir.mkdir(parents=True, exist_ok=True)
        out_dir.mkdir(parents=True, exist_ok=True)

        vendor_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "p_electrical",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "diode_like",
                    "vendor_note": "electrical",
                    "strict_trigger_date": "2025-03-10",
                },
                {
                    "site": "demo",
                    "panel_id": "p_group_from_v3",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "group_or_inverter_side_like",
                    "vendor_note": "group v3",
                    "strict_trigger_date": "2025-03-11",
                },
                {
                    "site": "demo",
                    "panel_id": "p_none_visible",
                    "vendor_reply_class": "vendor_rejected",
                    "vendor_fault_family": "none_visible",
                    "vendor_note": "none",
                    "strict_trigger_date": "2025-03-12",
                },
                {
                    "site": "demo",
                    "panel_id": "p_open_fallback",
                    "vendor_reply_class": "vendor_likely_positive",
                    "vendor_fault_family": "open_or_device_issue_like",
                    "vendor_note": "open fallback",
                    "strict_trigger_date": "2025-03-13",
                },
                {
                    "site": "demo",
                    "panel_id": "p_group_cluster",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "group_or_inverter_side_like",
                    "vendor_note": "group cluster",
                    "strict_trigger_date": "2025-03-14",
                },
                {
                    "site": "demo",
                    "panel_id": "p_group_collapse_override",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "group_or_inverter_side_like",
                    "vendor_note": "group collapse override",
                    "strict_trigger_date": "2025-03-17",
                },
                {
                    "site": "demo",
                    "panel_id": "p_uncertain",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "module_damage_like",
                    "vendor_note": "uncertain",
                    "strict_trigger_date": "2025-03-15",
                },
                {
                    "site": "demo",
                    "panel_id": "p_excluded",
                    "vendor_reply_class": "vendor_no_info",
                    "vendor_fault_family": "unknown",
                    "vendor_note": "excluded",
                    "strict_trigger_date": "2025-03-16",
                },
            ]
        )
        vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

        v3_df = pd.DataFrame(
            [
                {"site": "demo", "panel_id": "p_electrical", "critical_phenotype_v3": "electrical_fault_like"},
                {"site": "demo", "panel_id": "p_group_from_v3", "critical_phenotype_v3": "common_cause_borderline"},
                {"site": "demo", "panel_id": "p_none_visible", "critical_phenotype_v3": "shape_only_monitor"},
            ]
        )
        v3_df.to_csv(share_dir / "critical_actionability_shadow_v3_latest.csv", index=False, encoding="utf-8-sig")

        onset_df = pd.DataFrame(
            [
                {"site": "demo", "panel_id": "p_open_fallback", "strict_trigger_date": "2025-03-13", "retrospective_onset_date": "2025-03-11"},
                {"site": "demo", "panel_id": "p_group_cluster", "strict_trigger_date": "2025-03-14", "retrospective_onset_date": "2025-03-12"},
                {"site": "demo", "panel_id": "p_group_collapse_override", "strict_trigger_date": "2025-03-17", "retrospective_onset_date": "2025-03-16"},
                {"site": "demo", "panel_id": "p_uncertain", "strict_trigger_date": "2025-03-15", "retrospective_onset_date": "2025-03-13"},
            ]
        )
        onset_df.to_csv(share_dir / "panel_onset_shadow_latest.csv", index=False, encoding="utf-8-sig")

        core_df = pd.DataFrame(
            [
                {
                    "date": "2025-03-13",
                    "panel_id": "p_open_fallback",
                    "group_key_base": "g.open",
                    "mid_ratio": 0.05,
                    "mid_v_ratio": 0.05,
                    "mid_i_ratio": 0.05,
                    "v_drop": 0.95,
                    "coverage_mid": 0.80,
                },
                {
                    "date": "2025-03-14",
                    "panel_id": "p_group_cluster",
                    "group_key_base": "g.cluster",
                    "mid_ratio": 0.04,
                    "mid_v_ratio": 0.08,
                    "mid_i_ratio": 0.05,
                    "v_drop": 0.96,
                    "coverage_mid": 0.85,
                },
                {
                    "date": "2025-03-14",
                    "panel_id": "p_group_cluster_sibling",
                    "group_key_base": "g.cluster",
                    "mid_ratio": 0.05,
                    "mid_v_ratio": 0.09,
                    "mid_i_ratio": 0.05,
                    "v_drop": 0.92,
                    "coverage_mid": 0.90,
                },
                {
                    "date": "2025-03-15",
                    "panel_id": "p_uncertain",
                    "group_key_base": "g.uncertain",
                    "mid_ratio": 0.40,
                    "mid_v_ratio": 0.90,
                    "mid_i_ratio": 0.90,
                    "v_drop": 0.10,
                    "coverage_mid": 0.90,
                },
                {
                    "date": "2025-03-17",
                    "panel_id": "p_group_collapse_override",
                    "group_key_base": "g.override",
                    "mid_ratio": 0.02,
                    "mid_v_ratio": 0.03,
                    "mid_i_ratio": 0.95,
                    "v_drop": 0.97,
                    "coverage_mid": 0.90,
                },
                {
                    "date": "2025-03-17",
                    "panel_id": "p_group_collapse_override_s1",
                    "group_key_base": "g.override",
                    "mid_ratio": 0.04,
                    "mid_v_ratio": 0.08,
                    "mid_i_ratio": 0.05,
                    "v_drop": 0.93,
                    "coverage_mid": 0.80,
                },
                {
                    "date": "2025-03-17",
                    "panel_id": "p_group_collapse_override_s2",
                    "group_key_base": "g.override",
                    "mid_ratio": 0.03,
                    "mid_v_ratio": 0.09,
                    "mid_i_ratio": 0.04,
                    "v_drop": 0.91,
                    "coverage_mid": 0.85,
                },
            ]
        )
        core_df.to_csv(out_dir / "panel_day_core.csv", index=False, encoding="utf-8-sig")

        eval_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(eval_res.returncode == 0, f"gpvs fault family eval failed:\n{eval_res.stdout}\n{eval_res.stderr}")

        cases = pd.read_csv(share_dir / "gpvs_fault_family_eval_cases.csv", low_memory=False, encoding="utf-8-sig")
        summary = pd.read_csv(share_dir / "gpvs_fault_family_f1_summary.csv", low_memory=False, encoding="utf-8-sig")
        confusion = pd.read_csv(share_dir / "gpvs_fault_family_confusion.csv", low_memory=False, encoding="utf-8-sig")

        by_panel = cases.set_index("panel_id")
        assert_true(by_panel.loc["p_electrical", "truth_fault_family"] == "electrical_fault_like", "truth mapping failed for diode_like")
        assert_true(by_panel.loc["p_group_from_v3", "pred_fault_family"] == "group_or_inverter_side_like", "v3 mapping failed for common_cause_borderline")
        assert_true(by_panel.loc["p_open_fallback", "pred_fault_family"] == "open_or_device_issue_like", "fallback inference failed for open/device case")
        assert_true(by_panel.loc["p_group_cluster", "pred_fault_family"] == "group_or_inverter_side_like", "same-day cluster should prefer group/inverter classification")
        assert_true(by_panel.loc["p_group_collapse_override", "pred_fault_family"] == "group_or_inverter_side_like", "collapse evidence should override open/device fallback")
        assert_true(by_panel.loc["p_uncertain", "pred_fault_family"] == "uncertain", "uncertain fallback should remain uncertain")
        assert_true(by_panel.loc["p_group_cluster", "fallback_rule_used"] == "same_day_group_collapse", "group cluster fallback rule mismatch")
        assert_true(by_panel.loc["p_open_fallback", "fallback_rule_used"] == "isolated_zero_like_open_device", "isolated zero-like fallback rule mismatch")
        assert_true(by_panel.loc["p_group_collapse_override", "fallback_rule_used"] == "collapse_overrides_open_device", "collapse override rule mismatch")
        assert_true(int(by_panel.loc["p_group_cluster", "same_group_zero_like_count"]) == 2, "same-group zero-like count mismatch")
        assert_true(int(by_panel.loc["p_open_fallback", "same_site_zero_like_count"]) == 1, "isolated site-level zero-like count mismatch")
        assert_true(by_panel.loc["p_excluded", "truth_fault_family"] != by_panel.loc["p_excluded", "truth_fault_family"], "excluded truth should round-trip as blank/NaN")

        assert_true(set(summary["evaluation_mode"]) == {"closed_world", "abstaining"}, "both evaluation modes must be produced")
        overall = summary.loc[summary["row_type"] == "overall"].copy()
        assert_true(overall["macro_f1"].between(0, 1).all(), "macro_f1 must remain within [0,1]")
        assert_true(overall["weighted_f1"].between(0, 1).all(), "weighted_f1 must remain within [0,1]")
        assert_true(overall["accuracy"].between(0, 1).all(), "accuracy must remain within [0,1]")
        assert_true(overall.loc[overall["evaluation_mode"] == "abstaining", "coverage"].between(0, 1).all(), "abstaining coverage must remain within [0,1]")
        assert_true("uncertain" in set(confusion.loc[confusion["evaluation_mode"] == "closed_world", "pred_fault_family"]), "closed_world confusion must include uncertain")
        assert_true("uncertain" not in set(confusion.loc[confusion["evaluation_mode"] == "abstaining", "pred_fault_family"]), "abstaining confusion must exclude uncertain")

    smoke_v3_res = run([sys.executable, str(smoke_v3)], root)
    assert_true(smoke_v3_res.returncode == 0, f"critical actionability v3 smoke failed:\n{smoke_v3_res.stdout}\n{smoke_v3_res.stderr}")
    smoke_vendor_res = run([sys.executable, str(smoke_vendor)], root)
    assert_true(smoke_vendor_res.returncode == 0, f"vendor adjudication smoke failed:\n{smoke_vendor_res.stdout}\n{smoke_vendor_res.stderr}")
    smoke_onset_res = run([sys.executable, str(smoke_onset)], root)
    assert_true(smoke_onset_res.returncode == 0, f"panel onset shadow smoke failed:\n{smoke_onset_res.stdout}\n{smoke_onset_res.stderr}")
    smoke_field_res = run([sys.executable, str(smoke_field)], root)
    assert_true(smoke_field_res.returncode == 0, f"field truth smoke failed:\n{smoke_field_res.stdout}\n{smoke_field_res.stderr}")

    print("[OK] scripts compile")
    print("[OK] synthetic vendor-adjudicated set runs end-to-end")
    print("[OK] truth mapping works")
    print("[OK] fallback inference works")
    print("[OK] same-day multi-panel zero-like cluster prefers group_or_inverter_side_like")
    print("[OK] isolated zero-like panel remains open_or_device_issue_like")
    print("[OK] closed_world and abstaining summaries are both produced")
    print("[OK] F1 remains within [0,1]")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
