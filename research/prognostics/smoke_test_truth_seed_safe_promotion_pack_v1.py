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
                "panel_id": "safe_a",
                "strict_trigger_date": "2025-07-01",
                "candidate_validity": "",
                "date_judgement": "",
                "note": "",
                "review_priority": "P1",
            },
            {
                "site": "demo",
                "panel_id": "safe_b",
                "strict_trigger_date": "2025-07-02",
                "candidate_validity": "",
                "date_judgement": "current date",
                "note": "current note",
                "review_priority": "P1",
            },
            {
                "site": "demo",
                "panel_id": "gate_c",
                "strict_trigger_date": "2025-07-03",
                "candidate_validity": "",
                "date_judgement": "",
                "note": "",
                "review_priority": "P2",
            },
        ]
    )
    canonical_df.to_csv(share_dir / "panel_date_reaudit_working.csv", index=False, encoding="utf-8-sig")

    safe_df = pd.DataFrame(
        [
            {
                "site": "demo",
                "panel_id": "safe_a",
                "strict_trigger_date": "2025-07-01",
                "candidate_validity_proposed": "true_positive",
                "date_judgement_proposed": "",
                "note_proposed": "safe note a",
                "review_owner": "kim",
                "review_status": "done",
                "vendor_reply_class": "vendor_pattern_positive",
                "vendor_fault_family": "diode_like",
                "actionability_v3": "maintenance_candidate",
                "change_class": "safe_same_label_copyback",
            },
            {
                "site": "demo",
                "panel_id": "safe_b",
                "strict_trigger_date": "2025-07-02",
                "candidate_validity_proposed": "group_side",
                "date_judgement_proposed": "",
                "note_proposed": "safe note b",
                "review_owner": "lee",
                "review_status": "done",
                "vendor_reply_class": "field_confirmed_positive",
                "vendor_fault_family": "group_or_inverter_side_like",
                "actionability_v3": "",
                "change_class": "safe_same_label_copyback",
            },
        ]
    )
    safe_df.to_csv(share_dir / "truth_seed_safe_apply_rows_v1.csv", index=False, encoding="utf-8-sig")

    gate_df = pd.DataFrame(
        [
            {
                "site": "demo",
                "panel_id": "gate_c",
                "strict_trigger_date": "2025-07-03",
                "candidate_validity_proposed": "true_positive",
                "date_judgement_proposed": "",
                "note_proposed": "gate note",
                "review_owner": "park",
                "review_status": "done",
                "vendor_reply_class": "vendor_likely_positive",
                "vendor_fault_family": "module_damage_like",
                "actionability_v3": "maintenance_candidate",
                "current_strict_truth_label": "exclude",
                "proposed_strict_truth_label": "positive",
                "gate_reason": "strict 기준에서 exclude -> positive로 바뀌므로 manual evidence 재확인이 필요",
            }
        ]
    )
    gate_df.to_csv(share_dir / "truth_seed_gate_review_rows_v1.csv", index=False, encoding="utf-8-sig")

    evidence_df = pd.DataFrame(
        [
            {
                "site": "demo",
                "panel_id": "gate_c",
                "strict_trigger_date": "2025-07-03",
                "evidence_summary_ko": "gate evidence summary",
                "review_question_ko": "gate review question",
                "recommended_sources_ko": "gate sources",
            }
        ]
    )
    evidence_df.to_csv(share_dir / "truth_review_evidence_pack_v1.csv", index=False, encoding="utf-8-sig")

    scenario_df = pd.DataFrame(
        [
            {
                "scenario": "current_canonical",
                "truth_mode": "strict",
                "prediction_mode": "maintenance",
                "source_split": "overall",
                "f1": 0.6,
            },
            {
                "scenario": "safe_same_label_only",
                "truth_mode": "strict",
                "prediction_mode": "maintenance",
                "source_split": "overall",
                "f1": 0.6,
            },
            {
                "scenario": "current_canonical",
                "truth_mode": "strict",
                "prediction_mode": "operational",
                "source_split": "overall",
                "f1": 1.0,
            },
            {
                "scenario": "safe_same_label_only",
                "truth_mode": "strict",
                "prediction_mode": "operational",
                "source_split": "overall",
                "f1": 1.0,
            },
            {
                "scenario": "current_canonical",
                "truth_mode": "lenient",
                "prediction_mode": "maintenance",
                "source_split": "overall",
                "f1": 0.571429,
            },
            {
                "scenario": "safe_same_label_only",
                "truth_mode": "lenient",
                "prediction_mode": "maintenance",
                "source_split": "overall",
                "f1": 0.571429,
            },
            {
                "scenario": "current_canonical",
                "truth_mode": "lenient",
                "prediction_mode": "operational",
                "source_split": "overall",
                "f1": 1.0,
            },
            {
                "scenario": "safe_same_label_only",
                "truth_mode": "lenient",
                "prediction_mode": "operational",
                "source_split": "overall",
                "f1": 1.0,
            },
        ]
    )
    scenario_df.to_csv(share_dir / "truth_seed_promotion_scenarios_summary_v1.csv", index=False, encoding="utf-8-sig")
    return canonical_df


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_truth_seed_safe_promotion_pack_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_evaluate_truth_seed_promotion_scenarios_v1.py"

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

        proposed_df = pd.read_csv(share_dir / "panel_date_reaudit_working_safe7_proposed_v1.csv", encoding="utf-8-sig")
        safe_copyback_df = pd.read_csv(share_dir / "truth_seed_safe7_copyback_rows_v1.csv", encoding="utf-8-sig")
        gate_packet_df = pd.read_csv(share_dir / "truth_seed_gate3_review_packet_v1.csv", encoding="utf-8-sig")
        summary_df = pd.read_csv(share_dir / "truth_seed_safe_promotion_summary_v1.csv", encoding="utf-8-sig")

        assert_true(not proposed_df.empty, "safe7 proposed canonical should not be empty")
        assert_true(not safe_copyback_df.empty, "safe copyback rows should not be empty")
        assert_true(not gate_packet_df.empty, "gate review packet should not be empty")
        assert_true(not summary_df.empty, "summary should not be empty")

        safe_keys = set(safe_copyback_df.loc[:, ["site", "panel_id", "strict_trigger_date"]].itertuples(index=False, name=None))
        gate_keys = set(gate_packet_df.loc[:, ["site", "panel_id", "strict_trigger_date"]].itertuples(index=False, name=None))
        assert_true(
            safe_keys == {("demo", "safe_a", "2025-07-01"), ("demo", "safe_b", "2025-07-02")},
            "safe universe should be preserved exactly",
        )
        assert_true(
            gate_keys == {("demo", "gate_c", "2025-07-03")},
            "gate universe should be preserved exactly",
        )

        assert_true(
            len(proposed_df) == len(canonical_df),
            "proposed canonical sidecar should have the same row count as canonical source",
        )

        safe_a_row = proposed_df.loc[proposed_df["panel_id"].eq("safe_a")].iloc[0]
        safe_b_row = proposed_df.loc[proposed_df["panel_id"].eq("safe_b")].iloc[0]
        gate_c_row = proposed_df.loc[proposed_df["panel_id"].eq("gate_c")].iloc[0]
        assert_true(safe_a_row["candidate_validity"] == "true_positive", "safe row should apply into safe7 proposed canonical")
        assert_true(safe_b_row["candidate_validity"] == "group_side", "second safe row should apply into safe7 proposed canonical")
        assert_true(
            gate_c_row["candidate_validity"] == "" or pd.isna(gate_c_row["candidate_validity"]),
            "gate-review rows should not be applied into the safe7 proposed canonical",
        )
        assert_true(
            safe_b_row["note"] == "current note || review_v1: safe note b",
            "note merge semantics should match copyback apply for safe rows",
        )

        summary_row = summary_df.iloc[0]
        assert_true(
            summary_row["summary_recommendation"] == "promote_safe7_now_and_review_gate3",
            "summary recommendation should promote safe7 when metrics are unchanged or improved",
        )

        assert_true(
            gate_packet_df.iloc[0]["evidence_summary_ko"] == "gate evidence summary",
            "gate review packet should carry evidence pack context when available",
        )

        current_canonical_csv = pd.read_csv(
            share_dir / "panel_date_reaudit_working.csv",
            encoding="utf-8-sig",
        ).to_csv(index=False)
        assert_true(current_canonical_csv == original_canonical_csv, "canonical source file should remain unchanged")

        print("[OK] outputs generate")
        print("[OK] safe universe is preserved exactly")
        print("[OK] gate universe is preserved exactly")
        print("[OK] proposed canonical sidecar has same row count as canonical source")
        print("[OK] no gate-review rows are applied into the safe7 proposed canonical")
        print("[OK] summary_recommendation is promote_safe7_now_and_review_gate3 on a synthetic unchanged/improved metric fixture")
        print("[OK] no canonical source file is modified")

    safe_smoke_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(
        safe_smoke_res.returncode == 0,
        f"existing safe smoke failed:\n{safe_smoke_res.stdout}\n{safe_smoke_res.stderr}",
    )
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
