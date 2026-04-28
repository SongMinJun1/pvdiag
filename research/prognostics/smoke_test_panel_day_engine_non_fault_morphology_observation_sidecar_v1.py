#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_non_fault_morphology_observation_sidecar_v1.csv"
SUMMARY_NAME = "panel_day_engine_non_fault_morphology_observation_sidecar_summary_v1.csv"
NOTE_NAME = "panel_day_engine_non_fault_morphology_observation_sidecar_note_v1.md"


def write_gap_review(path: Path) -> None:
    rows = [
        {
            "site": "conalog",
            "panel_id": "eligible_early_warning",
            "source_search_status": "no_report_heuristic_match",
            "recovery_bucket": "persistent_non_recovery",
            "synchrony_bucket": "panel_local_or_weak_synchrony",
            "anchor_dates": "2026-01-04",
            "raw_candidate_dates": "2026-01-01",
            "nearest_raw_candidate_date": "2026-01-01",
            "nearest_anchor_date": "2026-01-04",
            "min_abs_gap_days": 3,
            "gap_direction": "raw_before_anchor",
            "date_alignment_gap_type": "near_anchor_1_3d",
            "raw_candidate_row_count": 1,
            "raw_signal_row_count": 1,
            "raw_recovery_row_count": 0,
            "raw_pre_ews_row_count": 1,
            "raw_prefault_B_effective_row_count": 0,
            "raw_fault_like_row_count": 0,
            "raw_final_fault_row_count": 0,
            "raw_critical_fault_row_count": 0,
            "raw_re_drop_row_count": 0,
            "raw_common_cause_row_count": 0,
            "signal_basis_type": "early_warning_only",
            "raw_audit_status_ko": "미확정",
            "raw_final_status_ko": "미확정",
            "raw_audit_anom_subtype": "normal",
            "raw_audit_critical_source": "none",
            "raw_heuristic_row_present_flag": 0,
            "any_operator_report_row_present_flag": 0,
            "report_attachment_gap_type": "final_verdict_all_rows_only_non_fault",
            "heuristic_attachment_gap_type": "expected_absent_non_fault_status_gate",
            "engine_patch_candidate_flag": 0,
            "report_patch_candidate_flag": 1,
            "review_note": "source note",
        },
        {
            "site": "gangui",
            "panel_id": "eligible_recovery",
            "source_search_status": "no_report_heuristic_match",
            "recovery_bucket": "sustained_recovery",
            "synchrony_bucket": "panel_local_or_weak_synchrony",
            "anchor_dates": "2026-02-04",
            "raw_candidate_dates": "2026-02-01",
            "nearest_raw_candidate_date": "2026-02-01",
            "nearest_anchor_date": "2026-02-04",
            "min_abs_gap_days": 3,
            "gap_direction": "raw_before_anchor",
            "date_alignment_gap_type": "near_anchor_1_3d",
            "raw_candidate_row_count": 1,
            "raw_signal_row_count": 1,
            "raw_recovery_row_count": 1,
            "raw_pre_ews_row_count": 1,
            "raw_prefault_B_effective_row_count": 0,
            "raw_fault_like_row_count": 0,
            "raw_final_fault_row_count": 0,
            "raw_critical_fault_row_count": 0,
            "raw_re_drop_row_count": 0,
            "raw_common_cause_row_count": 0,
            "signal_basis_type": "early_warning_plus_recovery",
            "raw_audit_status_ko": "미확정",
            "raw_final_status_ko": "미확정",
            "raw_audit_anom_subtype": "normal",
            "raw_audit_critical_source": "none",
            "raw_heuristic_row_present_flag": 0,
            "any_operator_report_row_present_flag": 0,
            "report_attachment_gap_type": "final_verdict_all_rows_only_non_fault",
            "heuristic_attachment_gap_type": "expected_absent_non_fault_status_gate",
            "engine_patch_candidate_flag": 0,
            "report_patch_candidate_flag": 1,
            "review_note": "source note",
        },
        {
            "site": "conalog",
            "panel_id": "excluded_date_displaced",
            "source_search_status": "no_report_heuristic_match",
            "recovery_bucket": "re_drop_cycle",
            "synchrony_bucket": "",
            "anchor_dates": "2026-03-01",
            "raw_candidate_dates": "2026-01-01",
            "nearest_raw_candidate_date": "2026-01-01",
            "nearest_anchor_date": "2026-03-01",
            "min_abs_gap_days": 59,
            "gap_direction": "raw_before_anchor",
            "date_alignment_gap_type": "date_displaced_gt14d",
            "raw_candidate_row_count": 1,
            "raw_signal_row_count": 0,
            "raw_recovery_row_count": 1,
            "raw_pre_ews_row_count": 0,
            "raw_prefault_B_effective_row_count": 0,
            "raw_fault_like_row_count": 0,
            "raw_final_fault_row_count": 0,
            "raw_critical_fault_row_count": 0,
            "raw_re_drop_row_count": 1,
            "raw_common_cause_row_count": 0,
            "signal_basis_type": "recovery_only",
            "raw_audit_status_ko": "미확정",
            "raw_final_status_ko": "미확정",
            "raw_audit_anom_subtype": "normal",
            "raw_audit_critical_source": "none",
            "raw_heuristic_row_present_flag": 0,
            "any_operator_report_row_present_flag": 0,
            "report_attachment_gap_type": "final_verdict_all_rows_only_non_fault",
            "heuristic_attachment_gap_type": "expected_absent_non_fault_status_gate",
            "engine_patch_candidate_flag": 0,
            "report_patch_candidate_flag": 0,
            "review_note": "source note",
        },
        {
            "site": "conalog",
            "panel_id": "excluded_fault_signal",
            "source_search_status": "no_report_heuristic_match",
            "recovery_bucket": "persistent_non_recovery",
            "synchrony_bucket": "panel_local_or_weak_synchrony",
            "anchor_dates": "2026-04-01",
            "raw_candidate_dates": "2026-04-01",
            "nearest_raw_candidate_date": "2026-04-01",
            "nearest_anchor_date": "2026-04-01",
            "min_abs_gap_days": 0,
            "gap_direction": "exact",
            "date_alignment_gap_type": "near_anchor_1_3d",
            "raw_candidate_row_count": 1,
            "raw_signal_row_count": 1,
            "raw_recovery_row_count": 0,
            "raw_pre_ews_row_count": 0,
            "raw_prefault_B_effective_row_count": 0,
            "raw_fault_like_row_count": 1,
            "raw_final_fault_row_count": 1,
            "raw_critical_fault_row_count": 0,
            "raw_re_drop_row_count": 0,
            "raw_common_cause_row_count": 0,
            "signal_basis_type": "hard_fault_like",
            "raw_audit_status_ko": "고장",
            "raw_final_status_ko": "고장",
            "raw_audit_anom_subtype": "confirmed_fault",
            "raw_audit_critical_source": "vdrop",
            "raw_heuristic_row_present_flag": 0,
            "any_operator_report_row_present_flag": 0,
            "report_attachment_gap_type": "no_report_rows",
            "heuristic_attachment_gap_type": "unexpected_missing_for_fault_signal",
            "engine_patch_candidate_flag": 1,
            "report_patch_candidate_flag": 0,
            "review_note": "source note",
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = (
        repo_root
        / "research"
        / "prognostics"
        / "build_panel_day_engine_non_fault_morphology_observation_sidecar_v1.py"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        source = root / "gap_review.csv"
        out_root = root / "out"
        write_gap_review(source)

        completed = run(
            [
                sys.executable,
                str(script),
                "--gap-review-input",
                str(source),
                "--output-dir",
                str(out_root),
            ],
            repo_root,
        )
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)
        detail = pd.read_csv(out_root / DETAIL_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(out_root / SUMMARY_NAME, encoding="utf-8-sig")
        note = (out_root / NOTE_NAME).read_text(encoding="utf-8")
        assert_true(len(detail) == 2, detail.to_string())
        assert_true(set(detail["panel_id"]) == {"eligible_early_warning", "eligible_recovery"}, detail.to_string())
        assert_true(int(detail["operator_promotion_allowed_flag"].sum()) == 0, detail.to_string())
        assert_true(int(detail["engine_patch_candidate_flag"].sum()) == 0, detail.to_string())
        assert_true(set(detail["recommended_action"]) == {"keep_sidecar_review_only"}, detail.to_string())
        assert_true(int(summary["panels"].sum()) == 2, summary.to_string())
        assert_true(int(summary["operator_promotion_allowed_sum"].sum()) == 0, summary.to_string())
        assert_true(int(summary["engine_patch_candidate_sum"].sum()) == 0, summary.to_string())
        assert_true("do not justify a `panel_day_engine.py`" in note, note)


if __name__ == "__main__":
    main()
