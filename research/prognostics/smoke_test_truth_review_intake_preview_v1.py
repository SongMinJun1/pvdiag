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
    build_script = root / "research" / "prognostics" / "build_truth_review_intake_preview_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_truth_review_batch_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        share_dir.mkdir(parents=True, exist_ok=True)

        batch_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "blank_case",
                    "strict_trigger_date": "2025-03-10",
                    "review_priority_bucket": "urgent_official_error_context",
                    "priority_score": 100,
                    "recommended_review_action": "manual_reaudit_first",
                },
                {
                    "site": "demo",
                    "panel_id": "valid_case",
                    "strict_trigger_date": "2025-03-11",
                    "review_priority_bucket": "vendor_backed_unlabeled",
                    "priority_score": 70,
                    "recommended_review_action": "compare_with_vendor_and_field_logs",
                },
                {
                    "site": "demo",
                    "panel_id": "invalid_case",
                    "strict_trigger_date": "2025-03-12",
                    "review_priority_bucket": "high_actionability_unlabeled",
                    "priority_score": 60,
                    "recommended_review_action": "manual_reaudit_first",
                },
                {
                    "site": "demo",
                    "panel_id": "duplicate_case",
                    "strict_trigger_date": "2025-03-13",
                    "review_priority_bucket": "urgent_official_error_context",
                    "priority_score": 95,
                    "recommended_review_action": "manual_reaudit_first",
                },
                {
                    "site": "demo",
                    "panel_id": "incomplete_case",
                    "strict_trigger_date": "2025-03-14",
                    "review_priority_bucket": "vendor_backed_unlabeled",
                    "priority_score": 65,
                    "recommended_review_action": "compare_with_vendor_and_field_logs",
                },
            ]
        )
        batch_df.to_csv(share_dir / "truth_review_batch_v1.csv", index=False, encoding="utf-8-sig")

        template_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "blank_case",
                    "strict_trigger_date": "2025-03-10",
                    "candidate_validity": "",
                    "date_judgement": "",
                    "note": "",
                    "review_owner": "",
                    "review_status": "",
                },
                {
                    "site": "demo",
                    "panel_id": "valid_case",
                    "strict_trigger_date": "2025-03-11",
                    "candidate_validity": "true_positive",
                    "date_judgement": "trigger matched",
                    "note": "valid reviewer note",
                    "review_owner": "kim",
                    "review_status": "done",
                },
                {
                    "site": "demo",
                    "panel_id": "invalid_case",
                    "strict_trigger_date": "2025-03-12",
                    "candidate_validity": "bad_label",
                    "date_judgement": "",
                    "note": "",
                    "review_owner": "lee",
                    "review_status": "done",
                },
                {
                    "site": "demo",
                    "panel_id": "duplicate_case",
                    "strict_trigger_date": "2025-03-13",
                    "candidate_validity": "false_positive",
                    "date_judgement": "",
                    "note": "first duplicate",
                    "review_owner": "park",
                    "review_status": "in_progress",
                },
                {
                    "site": "demo",
                    "panel_id": "duplicate_case",
                    "strict_trigger_date": "2025-03-13",
                    "candidate_validity": "group_side",
                    "date_judgement": "",
                    "note": "second duplicate",
                    "review_owner": "park",
                    "review_status": "done",
                },
                {
                    "site": "demo",
                    "panel_id": "incomplete_case",
                    "strict_trigger_date": "2025-03-14",
                    "candidate_validity": "",
                    "date_judgement": "",
                    "note": "left candidate blank",
                    "review_owner": "choi",
                    "review_status": "started",
                },
                {
                    "site": "demo",
                    "panel_id": "unexpected_case",
                    "strict_trigger_date": "2025-03-15",
                    "candidate_validity": "true_positive",
                    "date_judgement": "",
                    "note": "not in batch",
                    "review_owner": "han",
                    "review_status": "done",
                },
            ]
        )
        template_df.to_csv(share_dir / "truth_review_copyback_template_v1.csv", index=False, encoding="utf-8-sig")

        canonical_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "blank_case",
                    "strict_trigger_date": "2025-03-10",
                    "candidate_validity": "",
                    "date_judgement": "",
                    "note": "",
                },
                {
                    "site": "demo",
                    "panel_id": "valid_case",
                    "strict_trigger_date": "2025-03-11",
                    "candidate_validity": "",
                    "date_judgement": "",
                    "note": "old note",
                },
                {
                    "site": "demo",
                    "panel_id": "invalid_case",
                    "strict_trigger_date": "2025-03-12",
                    "candidate_validity": "",
                    "date_judgement": "",
                    "note": "",
                },
                {
                    "site": "demo",
                    "panel_id": "duplicate_case",
                    "strict_trigger_date": "2025-03-13",
                    "candidate_validity": "",
                    "date_judgement": "",
                    "note": "",
                },
                {
                    "site": "demo",
                    "panel_id": "incomplete_case",
                    "strict_trigger_date": "2025-03-14",
                    "candidate_validity": "",
                    "date_judgement": "",
                    "note": "",
                },
            ]
        )
        original_canonical_csv = canonical_df.to_csv(index=False)
        canonical_df.to_csv(share_dir / "panel_date_reaudit_working.csv", index=False, encoding="utf-8-sig")

        run_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(run_res.returncode == 0, f"script failed:\n{run_res.stdout}\n{run_res.stderr}")

        summary_df = pd.read_csv(share_dir / "truth_review_intake_summary_v1.csv", encoding="utf-8-sig")
        preview_df = pd.read_csv(share_dir / "truth_review_intake_preview_v1.csv", encoding="utf-8-sig")
        issues_df = pd.read_csv(share_dir / "truth_review_intake_issues_v1.csv", encoding="utf-8-sig")

        assert_true(not summary_df.empty, "summary output is empty")
        assert_true(not preview_df.empty, "preview output is empty")
        assert_true(not issues_df.empty, "issues output is empty")
        assert_true(len(preview_df) == len(batch_df), "base round-1 universe should be preserved exactly")

        blank_row = preview_df.loc[preview_df["panel_id"].eq("blank_case")].iloc[0]
        assert_true(blank_row["intake_row_status"] == "untouched_blank", "blank template row should become untouched_blank")

        valid_row = preview_df.loc[preview_df["panel_id"].eq("valid_case")].iloc[0]
        assert_true(
            valid_row["intake_row_status"] == "ready_for_copyback_preview" and int(valid_row["copyback_ready_flag"]) == 1,
            "valid filled row should become ready_for_copyback_preview",
        )

        invalid_row = preview_df.loc[preview_df["panel_id"].eq("invalid_case")].iloc[0]
        assert_true(
            invalid_row["intake_row_status"] == "invalid_candidate_validity",
            "invalid candidate_validity should become invalid_candidate_validity",
        )

        duplicate_row = preview_df.loc[preview_df["panel_id"].eq("duplicate_case")].iloc[0]
        assert_true(
            duplicate_row["intake_row_status"] == "duplicate_submission",
            "duplicate key should become duplicate_submission",
        )

        incomplete_row = preview_df.loc[preview_df["panel_id"].eq("incomplete_case")].iloc[0]
        assert_true(
            incomplete_row["intake_row_status"] == "incomplete_missing_candidate_validity",
            "missing candidate_validity with other fields filled should become incomplete_missing_candidate_validity",
        )

        assert_true(
            (issues_df["issue_type"] == "unexpected_key").any(),
            "unexpected template key should become unexpected_key",
        )

        current_canonical_csv = pd.read_csv(
            share_dir / "panel_date_reaudit_working.csv",
            encoding="utf-8-sig",
        ).to_csv(index=False)
        assert_true(current_canonical_csv == original_canonical_csv, "canonical truth file should remain unchanged")

        print("[OK] outputs generate")
        print("[OK] blank template rows become untouched_blank")
        print("[OK] valid filled row becomes ready_for_copyback_preview")
        print("[OK] invalid candidate_validity becomes invalid_candidate_validity")
        print("[OK] duplicate key becomes duplicate_submission")
        print("[OK] unexpected template key becomes unexpected_key")
        print("[OK] no canonical truth file is modified")

    safe_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(safe_res.returncode == 0, f"existing safe smoke failed:\n{safe_res.stdout}\n{safe_res.stderr}")
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
