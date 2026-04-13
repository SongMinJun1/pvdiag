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
    build_script = root / "research" / "prognostics" / "build_truth_review_copyback_apply_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_truth_review_intake_preview_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        share_dir.mkdir(parents=True, exist_ok=True)

        intake_preview_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "apply_case",
                    "strict_trigger_date": "2025-04-01",
                    "candidate_validity_current": "",
                    "date_judgement_current": "",
                    "note_current": "",
                    "candidate_validity_proposed": "true_positive",
                    "date_judgement_proposed": "strict date ok",
                    "note_proposed": "review note a",
                    "review_owner": "kim",
                    "review_status": "done",
                    "review_priority_bucket": "urgent_official_error_context",
                    "priority_score": 100,
                    "recommended_review_action": "manual_reaudit_first",
                    "intake_row_status": "ready_for_copyback_preview",
                    "copyback_ready_flag": 1,
                },
                {
                    "site": "demo",
                    "panel_id": "candidate_conflict_case",
                    "strict_trigger_date": "2025-04-02",
                    "candidate_validity_current": "group_side",
                    "date_judgement_current": "",
                    "note_current": "canonical note",
                    "candidate_validity_proposed": "false_positive",
                    "date_judgement_proposed": "",
                    "note_proposed": "review note b",
                    "review_owner": "lee",
                    "review_status": "done",
                    "review_priority_bucket": "urgent_official_error_context",
                    "priority_score": 95,
                    "recommended_review_action": "manual_reaudit_first",
                    "intake_row_status": "ready_for_copyback_preview",
                    "copyback_ready_flag": 1,
                },
                {
                    "site": "demo",
                    "panel_id": "date_conflict_case",
                    "strict_trigger_date": "2025-04-03",
                    "candidate_validity_current": "",
                    "date_judgement_current": "old date call",
                    "note_current": "",
                    "candidate_validity_proposed": "group_side",
                    "date_judgement_proposed": "new date call",
                    "note_proposed": "",
                    "review_owner": "park",
                    "review_status": "done",
                    "review_priority_bucket": "vendor_backed_unlabeled",
                    "priority_score": 80,
                    "recommended_review_action": "compare_with_vendor_and_field_logs",
                    "intake_row_status": "ready_for_copyback_preview",
                    "copyback_ready_flag": 1,
                },
                {
                    "site": "demo",
                    "panel_id": "unmatched_case",
                    "strict_trigger_date": "2025-04-04",
                    "candidate_validity_current": "",
                    "date_judgement_current": "",
                    "note_current": "",
                    "candidate_validity_proposed": "true_positive",
                    "date_judgement_proposed": "",
                    "note_proposed": "review note unmatched",
                    "review_owner": "choi",
                    "review_status": "done",
                    "review_priority_bucket": "vendor_backed_unlabeled",
                    "priority_score": 75,
                    "recommended_review_action": "compare_with_vendor_and_field_logs",
                    "intake_row_status": "ready_for_copyback_preview",
                    "copyback_ready_flag": 1,
                },
                {
                    "site": "demo",
                    "panel_id": "note_merge_case",
                    "strict_trigger_date": "2025-04-05",
                    "candidate_validity_current": "",
                    "date_judgement_current": "",
                    "note_current": "canonical note",
                    "candidate_validity_proposed": "group_side",
                    "date_judgement_proposed": "",
                    "note_proposed": "review note extra",
                    "review_owner": "han",
                    "review_status": "done",
                    "review_priority_bucket": "high_actionability_unlabeled",
                    "priority_score": 70,
                    "recommended_review_action": "manual_reaudit_first",
                    "intake_row_status": "ready_for_copyback_preview",
                    "copyback_ready_flag": 1,
                },
                {
                    "site": "demo",
                    "panel_id": "nonready_case",
                    "strict_trigger_date": "2025-04-06",
                    "candidate_validity_current": "",
                    "date_judgement_current": "",
                    "note_current": "",
                    "candidate_validity_proposed": "",
                    "date_judgement_proposed": "",
                    "note_proposed": "",
                    "review_owner": "",
                    "review_status": "",
                    "review_priority_bucket": "vendor_backed_unlabeled",
                    "priority_score": 60,
                    "recommended_review_action": "compare_with_vendor_and_field_logs",
                    "intake_row_status": "untouched_blank",
                    "copyback_ready_flag": 0,
                },
            ]
        )
        intake_preview_df.to_csv(share_dir / "truth_review_intake_preview_v1.csv", index=False, encoding="utf-8-sig")

        canonical_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "apply_case",
                    "strict_trigger_date": "2025-04-01",
                    "candidate_validity": "",
                    "date_judgement": "",
                    "note": "",
                    "review_priority": "P1",
                },
                {
                    "site": "demo",
                    "panel_id": "candidate_conflict_case",
                    "strict_trigger_date": "2025-04-02",
                    "candidate_validity": "group_side",
                    "date_judgement": "",
                    "note": "canonical note",
                    "review_priority": "P1",
                },
                {
                    "site": "demo",
                    "panel_id": "date_conflict_case",
                    "strict_trigger_date": "2025-04-03",
                    "candidate_validity": "",
                    "date_judgement": "old date call",
                    "note": "",
                    "review_priority": "P2",
                },
                {
                    "site": "demo",
                    "panel_id": "note_merge_case",
                    "strict_trigger_date": "2025-04-05",
                    "candidate_validity": "",
                    "date_judgement": "",
                    "note": "canonical note",
                    "review_priority": "P2",
                },
                {
                    "site": "demo",
                    "panel_id": "nonready_case",
                    "strict_trigger_date": "2025-04-06",
                    "candidate_validity": "",
                    "date_judgement": "",
                    "note": "",
                    "review_priority": "P3",
                },
            ]
        )
        original_canonical_csv = canonical_df.to_csv(index=False)
        canonical_df.to_csv(share_dir / "panel_date_reaudit_working.csv", index=False, encoding="utf-8-sig")

        run_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(run_res.returncode == 0, f"script failed:\n{run_res.stdout}\n{run_res.stderr}")

        summary_df = pd.read_csv(share_dir / "truth_review_copyback_apply_summary_v1.csv", encoding="utf-8-sig")
        proposed_df = pd.read_csv(share_dir / "panel_date_reaudit_working_proposed_v1.csv", encoding="utf-8-sig")
        copyback_rows_df = pd.read_csv(share_dir / "truth_review_copyback_rows_v1.csv", encoding="utf-8-sig")
        conflicts_df = pd.read_csv(share_dir / "truth_review_copyback_conflicts_v1.csv", encoding="utf-8-sig")

        assert_true(not summary_df.empty, "summary output is empty")
        assert_true(not proposed_df.empty, "proposed canonical output is empty")
        assert_true(not copyback_rows_df.empty, "copyback rows output is empty")
        assert_true(not conflicts_df.empty, "conflicts output is empty")

        assert_true(len(proposed_df) == len(canonical_df), "proposed canonical row count should match canonical input")
        assert_true(len(copyback_rows_df) == 2, "only non-conflicted ready rows should become copyback rows")

        apply_case = proposed_df.loc[proposed_df["panel_id"].eq("apply_case")].iloc[0]
        assert_true(apply_case["candidate_validity"] == "true_positive", "ready no_conflict row should apply candidate_validity")
        assert_true(apply_case["date_judgement"] == "strict date ok", "ready no_conflict row should apply date_judgement")
        assert_true(apply_case["note"] == "review note a", "ready no_conflict row should apply note")

        note_merge_case = proposed_df.loc[proposed_df["panel_id"].eq("note_merge_case")].iloc[0]
        assert_true(
            note_merge_case["note"] == "canonical note || review_v1: review note extra",
            "note merge semantics should append review_v1 text when notes differ",
        )

        candidate_conflict_case = proposed_df.loc[proposed_df["panel_id"].eq("candidate_conflict_case")].iloc[0]
        assert_true(
            candidate_conflict_case["candidate_validity"] == "group_side",
            "candidate_validity conflict should not be applied",
        )

        date_conflict_case = proposed_df.loc[proposed_df["panel_id"].eq("date_conflict_case")].iloc[0]
        assert_true(
            date_conflict_case["date_judgement"] == "old date call",
            "date_judgement conflict should not be applied",
        )

        assert_true(
            (conflicts_df["conflict_type"] == "candidate_validity_conflict").any(),
            "candidate_validity conflict should be detected",
        )
        assert_true(
            (conflicts_df["conflict_type"] == "date_judgement_conflict").any(),
            "date_judgement conflict should be detected",
        )
        assert_true(
            (conflicts_df["conflict_type"] == "no_matching_canonical_row").any(),
            "unmatched row should become no_matching_canonical_row",
        )

        current_canonical_csv = pd.read_csv(
            share_dir / "panel_date_reaudit_working.csv",
            encoding="utf-8-sig",
        ).to_csv(index=False)
        assert_true(current_canonical_csv == original_canonical_csv, "canonical source file should remain unchanged")

        summary_row = summary_df.iloc[0]
        assert_true(int(summary_row["ready_row_count"]) == 5, "ready row count should reflect only eligible intake rows")
        assert_true(int(summary_row["apply_ready_count"]) == 2, "apply ready count should match non-conflicted rows")
        assert_true(int(summary_row["conflict_count"]) == 3, "conflict count should reflect candidate/date/unmatched rows")
        assert_true(int(summary_row["untouched_or_nonready_count"]) == 1, "non-ready rows should be counted separately")

        print("[OK] outputs generate")
        print("[OK] ready no_conflict row is applied into proposed canonical file")
        print("[OK] candidate_validity conflict is detected and not applied")
        print("[OK] date_judgement conflict is detected and not applied")
        print("[OK] unmatched row becomes no_matching_canonical_row")
        print("[OK] note merge semantics work as specified")
        print("[OK] canonical source file is not modified")

    safe_smoke_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(
        safe_smoke_res.returncode == 0,
        f"existing safe smoke failed:\n{safe_smoke_res.stdout}\n{safe_smoke_res.stderr}",
    )
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
