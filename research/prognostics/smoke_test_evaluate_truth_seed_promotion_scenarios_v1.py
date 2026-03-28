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


def build_fixture(share_dir: Path) -> pd.DataFrame:
    canonical_df = pd.DataFrame(
        [
            {
                "site": "demo",
                "panel_id": "safe_case_1",
                "strict_trigger_date": "2025-06-01",
                "candidate_validity": "",
                "onset_confidence": "medium",
                "reason_summary": "strict_method=critical_fault_flag|shadow_frac=0.0|group_off_frac=0.0|recovery_reset=no",
                "review_priority": "P1",
                "vendor_reply_class": "",
                "vendor_fault_family": "",
                "note": "",
            },
            {
                "site": "demo",
                "panel_id": "safe_case_2",
                "strict_trigger_date": "2025-06-02",
                "candidate_validity": "",
                "onset_confidence": "medium",
                "reason_summary": "strict_method=confirmed_fault_flag|shadow_frac=0.0|group_off_frac=0.0|recovery_reset=no",
                "review_priority": "P1",
                "vendor_reply_class": "",
                "vendor_fault_family": "",
                "note": "",
            },
            {
                "site": "demo",
                "panel_id": "gate_case",
                "strict_trigger_date": "2025-06-03",
                "candidate_validity": "",
                "onset_confidence": "medium",
                "reason_summary": "strict_method=critical_fault_flag|shadow_frac=0.0|group_off_frac=0.0|recovery_reset=no",
                "review_priority": "P2",
                "vendor_reply_class": "",
                "vendor_fault_family": "",
                "note": "",
            },
        ]
    )
    canonical_df.to_csv(share_dir / "panel_date_reaudit_working.csv", index=False, encoding="utf-8-sig")

    copyback_df = pd.DataFrame(
        [
            {
                "site": "demo",
                "panel_id": "safe_case_1",
                "strict_trigger_date": "2025-06-01",
                "candidate_validity_current": "",
                "candidate_validity_proposed": "true_positive",
                "candidate_validity_merged": "true_positive",
                "date_judgement_current": "",
                "date_judgement_proposed": "same day ok",
                "date_judgement_merged": "same day ok",
                "note_current": "",
                "note_proposed": "safe vendor-pattern seed",
                "note_merged": "safe vendor-pattern seed",
                "review_owner": "kim",
                "review_status": "done",
                "conflict_type": "no_conflict",
                "apply_ready_flag": 1,
            },
            {
                "site": "demo",
                "panel_id": "safe_case_2",
                "strict_trigger_date": "2025-06-02",
                "candidate_validity_current": "",
                "candidate_validity_proposed": "group_side",
                "candidate_validity_merged": "group_side",
                "date_judgement_current": "",
                "date_judgement_proposed": "",
                "date_judgement_merged": "",
                "note_current": "",
                "note_proposed": "safe confirmed-fault seed",
                "note_merged": "safe confirmed-fault seed",
                "review_owner": "lee",
                "review_status": "done",
                "conflict_type": "no_conflict",
                "apply_ready_flag": 1,
            },
            {
                "site": "demo",
                "panel_id": "gate_case",
                "strict_trigger_date": "2025-06-03",
                "candidate_validity_current": "",
                "candidate_validity_proposed": "true_positive",
                "candidate_validity_merged": "true_positive",
                "date_judgement_current": "",
                "date_judgement_proposed": "",
                "date_judgement_merged": "",
                "note_current": "",
                "note_proposed": "gate seed",
                "note_merged": "gate seed",
                "review_owner": "park",
                "review_status": "done",
                "conflict_type": "no_conflict",
                "apply_ready_flag": 1,
            },
        ]
    )
    copyback_df.to_csv(share_dir / "truth_review_copyback_rows_v1.csv", index=False, encoding="utf-8-sig")

    changed_df = pd.DataFrame(
        [
            {
                "site": "demo",
                "panel_id": "safe_case_1",
                "strict_trigger_date": "2025-06-01",
                "truth_mode": "lenient",
                "current_truth_source": "vendor_truth",
                "current_truth_label": "positive",
                "proposed_truth_source": "manual_truth",
                "proposed_truth_label": "positive",
                "candidate_validity_current": "",
                "candidate_validity_proposed": "true_positive",
                "vendor_reply_class": "vendor_pattern_positive",
                "vendor_fault_family": "diode_like",
                "actionability_v3": "maintenance_candidate",
                "change_type": "vendor_to_manual_same_label",
            },
            {
                "site": "demo",
                "panel_id": "safe_case_1",
                "strict_trigger_date": "2025-06-01",
                "truth_mode": "strict",
                "current_truth_source": "vendor_truth",
                "current_truth_label": "positive",
                "proposed_truth_source": "manual_truth",
                "proposed_truth_label": "positive",
                "candidate_validity_current": "",
                "candidate_validity_proposed": "true_positive",
                "vendor_reply_class": "vendor_pattern_positive",
                "vendor_fault_family": "diode_like",
                "actionability_v3": "maintenance_candidate",
                "change_type": "vendor_to_manual_same_label",
            },
            {
                "site": "demo",
                "panel_id": "safe_case_2",
                "strict_trigger_date": "2025-06-02",
                "truth_mode": "lenient",
                "current_truth_source": "vendor_truth",
                "current_truth_label": "positive",
                "proposed_truth_source": "manual_truth",
                "proposed_truth_label": "positive",
                "candidate_validity_current": "",
                "candidate_validity_proposed": "group_side",
                "vendor_reply_class": "field_confirmed_positive",
                "vendor_fault_family": "group_or_inverter_side_like",
                "actionability_v3": "",
                "change_type": "vendor_to_manual_same_label",
            },
            {
                "site": "demo",
                "panel_id": "safe_case_2",
                "strict_trigger_date": "2025-06-02",
                "truth_mode": "strict",
                "current_truth_source": "vendor_truth",
                "current_truth_label": "positive",
                "proposed_truth_source": "manual_truth",
                "proposed_truth_label": "positive",
                "candidate_validity_current": "",
                "candidate_validity_proposed": "group_side",
                "vendor_reply_class": "field_confirmed_positive",
                "vendor_fault_family": "group_or_inverter_side_like",
                "actionability_v3": "",
                "change_type": "vendor_to_manual_same_label",
            },
            {
                "site": "demo",
                "panel_id": "gate_case",
                "strict_trigger_date": "2025-06-03",
                "truth_mode": "lenient",
                "current_truth_source": "vendor_truth",
                "current_truth_label": "positive",
                "proposed_truth_source": "manual_truth",
                "proposed_truth_label": "positive",
                "candidate_validity_current": "",
                "candidate_validity_proposed": "true_positive",
                "vendor_reply_class": "vendor_likely_positive",
                "vendor_fault_family": "module_damage_like",
                "actionability_v3": "maintenance_candidate",
                "change_type": "vendor_to_manual_same_label",
            },
            {
                "site": "demo",
                "panel_id": "gate_case",
                "strict_trigger_date": "2025-06-03",
                "truth_mode": "strict",
                "current_truth_source": "vendor_truth",
                "current_truth_label": "exclude",
                "proposed_truth_source": "manual_truth",
                "proposed_truth_label": "positive",
                "candidate_validity_current": "",
                "candidate_validity_proposed": "true_positive",
                "vendor_reply_class": "vendor_likely_positive",
                "vendor_fault_family": "module_damage_like",
                "actionability_v3": "maintenance_candidate",
                "change_type": "vendor_to_manual_label_changed",
            },
        ]
    )
    changed_df.to_csv(share_dir / "truth_seed_impact_changed_cases_v1.csv", index=False, encoding="utf-8-sig")

    vendor_df = pd.DataFrame(
        [
            {
                "site": "demo",
                "panel_id": "safe_case_1",
                "strict_trigger_date": "2025-06-01",
                "vendor_reply_class": "vendor_pattern_positive",
                "vendor_fault_family": "diode_like",
                "vendor_note": "vendor positive",
            },
            {
                "site": "demo",
                "panel_id": "safe_case_2",
                "strict_trigger_date": "2025-06-02",
                "vendor_reply_class": "field_confirmed_positive",
                "vendor_fault_family": "group_or_inverter_side_like",
                "vendor_note": "field confirmed",
            },
            {
                "site": "demo",
                "panel_id": "gate_case",
                "strict_trigger_date": "2025-06-03",
                "vendor_reply_class": "vendor_likely_positive",
                "vendor_fault_family": "module_damage_like",
                "vendor_note": "likely positive only",
            },
        ]
    )
    vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

    action_df = pd.DataFrame(
        [
            {
                "site": "demo",
                "panel_id": "safe_case_1",
                "strict_trigger_date": "2025-06-01",
                "actionability_v3": "maintenance_candidate",
            },
            {
                "site": "demo",
                "panel_id": "safe_case_2",
                "strict_trigger_date": "2025-06-02",
                "actionability_v3": "monitor_only",
            },
            {
                "site": "demo",
                "panel_id": "gate_case",
                "strict_trigger_date": "2025-06-03",
                "actionability_v3": "maintenance_candidate",
            },
        ]
    )
    action_df.to_csv(share_dir / "critical_actionability_shadow_v3_latest.csv", index=False, encoding="utf-8-sig")
    return canonical_df


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "evaluate_truth_seed_promotion_scenarios_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_evaluate_truth_seed_impact_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        share_dir.mkdir(parents=True, exist_ok=True)
        canonical_df = build_fixture(share_dir)
        original_canonical_csv = canonical_df.to_csv(index=False)

        run_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(run_res.returncode == 0, f"script failed:\n{run_res.stdout}\n{run_res.stderr}")

        summary_df = pd.read_csv(share_dir / "truth_seed_promotion_scenarios_summary_v1.csv", encoding="utf-8-sig")
        safe_df = pd.read_csv(share_dir / "truth_seed_safe_apply_rows_v1.csv", encoding="utf-8-sig")
        gate_df = pd.read_csv(share_dir / "truth_seed_gate_review_rows_v1.csv", encoding="utf-8-sig")
        changed_df = pd.read_csv(share_dir / "truth_seed_promotion_changed_cases_v1.csv", encoding="utf-8-sig")

        assert_true(not summary_df.empty, "summary output is empty")
        assert_true(not safe_df.empty, "safe rows output is empty")
        assert_true(not gate_df.empty, "gate rows output is empty")
        assert_true(not changed_df.empty, "changed cases output is empty")

        ready_keys = {
            ("demo", "safe_case_1", "2025-06-01"),
            ("demo", "safe_case_2", "2025-06-02"),
            ("demo", "gate_case", "2025-06-03"),
        }
        split_keys = set(safe_df.loc[:, ["site", "panel_id", "strict_trigger_date"]].itertuples(index=False, name=None))
        split_keys |= set(gate_df.loc[:, ["site", "panel_id", "strict_trigger_date"]].itertuples(index=False, name=None))
        assert_true(split_keys == ready_keys, "unique ready universe should be preserved exactly across safe/gate split")

        assert_true(
            safe_df["change_class"].eq("safe_same_label_copyback").all(),
            "synthetic same-label rows should go to safe_same_label_copyback",
        )
        assert_true(
            len(gate_df) == 1 and gate_df.iloc[0]["panel_id"] == "gate_case",
            "synthetic strict-changing row should go to gate_review_required",
        )

        safe_changed = changed_df.loc[changed_df["scenario"].eq("safe_same_label_only")]
        assert_true(
            safe_changed["scenario_change_type"].eq("no_label_change_manualized").all(),
            "safe_same_label_only should leave strict polarity unchanged on synthetic fixture",
        )

        full_gate_changed = changed_df.loc[
            changed_df["scenario"].eq("full_ready_rows")
            & changed_df["panel_id"].eq("gate_case")
            & changed_df["truth_mode"].eq("strict")
        ]
        assert_true(
            not full_gate_changed.empty
            and full_gate_changed["scenario_change_type"].eq("strict_label_changed_requires_gate").all(),
            "full_ready_rows should be able to change strict truth when gate rows exist",
        )

        summary_counts = summary_df.iloc[0]
        assert_true(int(summary_counts["ready_unique_case_count"]) == 3, "ready_unique_case_count should match synthetic ready universe")
        assert_true(int(summary_counts["safe_same_label_case_count"]) == 2, "safe_same_label_case_count should match synthetic same-label rows")
        assert_true(int(summary_counts["gate_review_case_count"]) == 1, "gate_review_case_count should match synthetic gate rows")

        current_canonical_csv = pd.read_csv(
            share_dir / "panel_date_reaudit_working.csv",
            encoding="utf-8-sig",
        ).to_csv(index=False)
        assert_true(current_canonical_csv == original_canonical_csv, "canonical source file should remain unchanged")

        print("[OK] outputs generate")
        print("[OK] unique ready universe is preserved exactly")
        print("[OK] synthetic same-label rows go to safe_same_label_copyback")
        print("[OK] synthetic strict-changing rows go to gate_review_required")
        print("[OK] safe_same_label_only leaves strict polarity unchanged on synthetic fixture")
        print("[OK] full_ready_rows can change strict truth when synthetic gate rows exist")
        print("[OK] no canonical source file is modified")

    safe_smoke_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(
        safe_smoke_res.returncode == 0,
        f"existing safe smoke failed:\n{safe_smoke_res.stdout}\n{safe_smoke_res.stderr}",
    )
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
