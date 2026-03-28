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
    build_script = root / "research" / "prognostics" / "build_baseline_freeze_pack_v1.py"
    safe_smoke_deferred = root / "research" / "prognostics" / "smoke_test_truth_review_deferred_hold_v1.py"
    safe_smoke_precursor = root / "research" / "prognostics" / "smoke_test_common_cause_precursor_decision_pack_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        share_dir.mkdir(parents=True, exist_ok=True)

        f1_df = pd.DataFrame(
            [
                {
                    "truth_mode": "strict",
                    "prediction_mode": "maintenance",
                    "source_split": "overall",
                    "f1": 0.61,
                },
                {
                    "truth_mode": "strict",
                    "prediction_mode": "operational",
                    "source_split": "overall",
                    "f1": 0.91,
                },
                {
                    "truth_mode": "lenient",
                    "prediction_mode": "maintenance",
                    "source_split": "overall",
                    "f1": 0.72,
                },
                {
                    "truth_mode": "lenient",
                    "prediction_mode": "operational",
                    "source_split": "overall",
                    "f1": 0.95,
                },
                {
                    "truth_mode": "strict",
                    "prediction_mode": "maintenance",
                    "source_split": "manual_truth",
                    "f1": 0.61,
                },
            ]
        )
        f1_df.to_csv(share_dir / "full_algorithm_f1_summary_v3.csv", index=False, encoding="utf-8-sig")
        original_f1_bytes = (share_dir / "full_algorithm_f1_summary_v3.csv").read_bytes()

        score_scope_summary_df = pd.DataFrame(
            [
                {
                    "record_type": "summary",
                    "total_strict_cases": 20,
                    "official_scored_count": 7,
                    "manual_scored_count": 6,
                    "vendor_scored_count": 1,
                    "deferred_unlabeled_high_actionability_count": 2,
                    "deferred_unlabeled_other_count": 10,
                    "excluded_labeled_needs_more_info_count": 1,
                    "excluded_vendor_no_info_count": 0,
                    "excluded_other_count": 0,
                    "site": "",
                    "total_cases": 20,
                }
            ]
        )
        score_scope_summary_df.to_csv(
            share_dir / "score_scope_manifest_summary_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )
        original_score_scope_summary_bytes = (share_dir / "score_scope_manifest_summary_v1.csv").read_bytes()

        score_scope_sites_df = pd.DataFrame(
            [
                {
                    "site": "conalog",
                    "total_cases": 10,
                    "official_scored_count": 4,
                    "manual_scored_count": 4,
                    "vendor_scored_count": 0,
                    "deferred_unlabeled_high_actionability_count": 0,
                    "deferred_unlabeled_other_count": 6,
                    "recommended_site_handling": "continue_scoring_normally",
                },
                {
                    "site": "gangui",
                    "total_cases": 8,
                    "official_scored_count": 2,
                    "manual_scored_count": 1,
                    "vendor_scored_count": 1,
                    "deferred_unlabeled_high_actionability_count": 2,
                    "deferred_unlabeled_other_count": 4,
                    "recommended_site_handling": "score_with_deferred_note",
                },
                {
                    "site": "ktc_ess",
                    "total_cases": 2,
                    "official_scored_count": 1,
                    "manual_scored_count": 1,
                    "vendor_scored_count": 0,
                    "deferred_unlabeled_high_actionability_count": 0,
                    "deferred_unlabeled_other_count": 1,
                    "recommended_site_handling": "continue_scoring_normally",
                },
            ]
        )
        score_scope_sites_df.to_csv(
            share_dir / "score_scope_manifest_sites_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )
        original_score_scope_sites_bytes = (share_dir / "score_scope_manifest_sites_v1.csv").read_bytes()

        deferred_summary_df = pd.DataFrame(
            [
                {
                    "record_type": "summary",
                    "original_batch_count": 2,
                    "deferred_hold_count": 2,
                    "active_batch_v2_count": 0,
                    "deferred_site_count": 1,
                    "site": "",
                    "active_batch_v2_count_after_hold": "",
                    "site_handling_recommendation": "",
                },
                {
                    "record_type": "site",
                    "original_batch_count": "",
                    "deferred_hold_count": 0,
                    "active_batch_v2_count": "",
                    "deferred_site_count": "",
                    "site": "conalog",
                    "active_batch_v2_count_after_hold": 0,
                    "site_handling_recommendation": "no_deferred_hold_rows",
                },
                {
                    "record_type": "site",
                    "original_batch_count": "",
                    "deferred_hold_count": 2,
                    "active_batch_v2_count": "",
                    "deferred_site_count": "",
                    "site": "gangui",
                    "active_batch_v2_count_after_hold": 0,
                    "site_handling_recommendation": "keep_on_hold_until_field_evidence",
                },
                {
                    "record_type": "site",
                    "original_batch_count": "",
                    "deferred_hold_count": 0,
                    "active_batch_v2_count": "",
                    "deferred_site_count": "",
                    "site": "ktc_ess",
                    "active_batch_v2_count_after_hold": 0,
                    "site_handling_recommendation": "no_deferred_hold_rows",
                },
            ]
        )
        deferred_summary_df.to_csv(
            share_dir / "truth_review_deferred_summary_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )
        original_deferred_summary_bytes = (share_dir / "truth_review_deferred_summary_v1.csv").read_bytes()

        precursor_summary_df = pd.DataFrame(
            [
                {
                    "global_recommendation": "keep_under_observation",
                    "global_decision_reason": "Promising local slice exists, but global generalization is still too weak.",
                    "primary_tier_used": "broad_3g_10p",
                }
            ]
        )
        precursor_summary_df.to_csv(
            share_dir / "common_cause_precursor_decision_summary_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )
        original_precursor_summary_bytes = (share_dir / "common_cause_precursor_decision_summary_v1.csv").read_bytes()

        precursor_sites_df = pd.DataFrame(
            [
                {
                    "site": "conalog",
                    "candidate_day_count": 4,
                    "plausible_precursor_day_count": 2,
                    "episode_aligned_day_count": 2,
                    "likely_persistent_site_pattern_count": 0,
                    "likely_sparse_site_pattern_count": 0,
                    "ambiguous_case_count": 0,
                    "site_recommendation": "keep_site_specific_precursor_note",
                    "site_decision_reason": "Conalog still has a defensible site-specific precursor note only.",
                },
                {
                    "site": "gangui",
                    "candidate_day_count": 0,
                    "plausible_precursor_day_count": 0,
                    "episode_aligned_day_count": 0,
                    "likely_persistent_site_pattern_count": 0,
                    "likely_sparse_site_pattern_count": 0,
                    "ambiguous_case_count": 0,
                    "site_recommendation": "no_precursor_signal",
                    "site_decision_reason": "No precursor signal is retained for gangui.",
                },
                {
                    "site": "ktc_ess",
                    "candidate_day_count": 2,
                    "plausible_precursor_day_count": 0,
                    "episode_aligned_day_count": 0,
                    "likely_persistent_site_pattern_count": 2,
                    "likely_sparse_site_pattern_count": 1,
                    "ambiguous_case_count": 0,
                    "site_recommendation": "likely_site_pattern_not_generalizable",
                    "site_decision_reason": "ktc_ess still looks like a site-pattern line, not a precursor line.",
                },
            ]
        )
        precursor_sites_df.to_csv(
            share_dir / "common_cause_precursor_decision_sites_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )
        original_precursor_sites_bytes = (share_dir / "common_cause_precursor_decision_sites_v1.csv").read_bytes()

        active_batch_df = pd.DataFrame(
            columns=[
                "round1_review_order",
                "round1_bucket_rank",
                "site",
                "panel_id",
                "strict_trigger_date",
                "review_priority_bucket",
            ]
        )
        active_batch_df.to_csv(share_dir / "truth_review_active_batch_v2.csv", index=False, encoding="utf-8-sig")
        original_active_batch_bytes = (share_dir / "truth_review_active_batch_v2.csv").read_bytes()

        run_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "conalog", "gangui", "ktc_ess"], root)
        assert_true(run_res.returncode == 0, f"script failed:\n{run_res.stdout}\n{run_res.stderr}")

        summary_df = pd.read_csv(share_dir / "baseline_freeze_summary_v1.csv", encoding="utf-8-sig")
        sites_df = pd.read_csv(share_dir / "baseline_freeze_sites_v1.csv", encoding="utf-8-sig")
        decisions_df = pd.read_csv(share_dir / "baseline_freeze_decisions_v1.csv", encoding="utf-8-sig")

        assert_true(len(summary_df) == 1, "baseline freeze summary should contain exactly one overall row")
        assert_true(not sites_df.empty, "baseline freeze sites output is empty")
        assert_true(not decisions_df.empty, "baseline freeze decisions output is empty")

        summary_row = summary_df.iloc[0]
        assert_true(abs(float(summary_row["strict_maintenance_f1"]) - 0.61) < 1e-6, "strict_maintenance_f1 should match synthetic input")
        assert_true(abs(float(summary_row["strict_operational_f1"]) - 0.91) < 1e-6, "strict_operational_f1 should match synthetic input")
        assert_true(abs(float(summary_row["lenient_maintenance_f1"]) - 0.72) < 1e-6, "lenient_maintenance_f1 should match synthetic input")
        assert_true(abs(float(summary_row["lenient_operational_f1"]) - 0.95) < 1e-6, "lenient_operational_f1 should match synthetic input")
        assert_true(int(summary_row["official_scored_count"]) == 7, "official_scored_count should come from score scope summary")
        assert_true(int(summary_row["manual_scored_count"]) == 6, "manual_scored_count should come from score scope summary")
        assert_true(int(summary_row["vendor_scored_count"]) == 1, "vendor_scored_count should come from score scope summary")
        assert_true(int(summary_row["deferred_hold_count"]) == 2, "deferred_hold_count should come from deferred summary")
        assert_true(int(summary_row["active_review_queue_count"]) == 0, "active_review_queue_count should come from active batch row count")
        assert_true(
            summary_row["precursor_global_recommendation"] == "keep_under_observation",
            "precursor_global_recommendation should come from precursor decision summary",
        )
        assert_true(
            summary_row["freeze_recommendation"] == "baseline_frozen_ready",
            "active_review_queue_count == 0 should yield baseline_frozen_ready",
        )

        by_site = sites_df.set_index("site")
        assert_true(
            by_site.loc["gangui", "site_status"] == "scored_with_deferred_hold",
            "deferred-hold site should become scored_with_deferred_hold",
        )
        assert_true(
            by_site.loc["conalog", "site_status"] == "scored_with_site_specific_precursor_note",
            "precursor-note site should become scored_with_site_specific_precursor_note",
        )

        by_decision = decisions_df.set_index("decision_key")
        assert_true(
            by_decision.loc["official_baseline_status", "decision_status"] == "frozen",
            "official_baseline_status should be frozen when the baseline is ready",
        )
        assert_true(
            by_decision.loc["active_truth_review_queue", "decision_status"] == "empty",
            "active_truth_review_queue should be empty in the frozen scenario",
        )
        assert_true(
            by_decision.loc["deferred_high_actionability_rows", "decision_status"] == "on_hold",
            "deferred high-actionability rows should be marked on_hold",
        )
        assert_true(
            by_decision.loc["global_precursor_addon", "decision_status"] == "keep_under_observation",
            "global precursor addon decision should mirror the precursor summary",
        )
        assert_true(
            by_decision.loc["conalog_precursor_note", "decision_status"] == "keep",
            "conalog precursor note should be kept in the synthetic scenario",
        )
        assert_true(
            by_decision.loc["next_workstream_recommendation", "decision_status"] == "safe_to_switch_topic",
            "frozen baseline should allow switching to the next workstream",
        )

        current_f1_bytes = (share_dir / "full_algorithm_f1_summary_v3.csv").read_bytes()
        current_score_scope_summary_bytes = (share_dir / "score_scope_manifest_summary_v1.csv").read_bytes()
        current_score_scope_sites_bytes = (share_dir / "score_scope_manifest_sites_v1.csv").read_bytes()
        current_deferred_summary_bytes = (share_dir / "truth_review_deferred_summary_v1.csv").read_bytes()
        current_precursor_summary_bytes = (share_dir / "common_cause_precursor_decision_summary_v1.csv").read_bytes()
        current_precursor_sites_bytes = (share_dir / "common_cause_precursor_decision_sites_v1.csv").read_bytes()
        current_active_batch_bytes = (share_dir / "truth_review_active_batch_v2.csv").read_bytes()
        assert_true(current_f1_bytes == original_f1_bytes, "full algorithm summary input should remain unchanged")
        assert_true(
            current_score_scope_summary_bytes == original_score_scope_summary_bytes,
            "score scope summary input should remain unchanged",
        )
        assert_true(
            current_score_scope_sites_bytes == original_score_scope_sites_bytes,
            "score scope sites input should remain unchanged",
        )
        assert_true(
            current_deferred_summary_bytes == original_deferred_summary_bytes,
            "deferred summary input should remain unchanged",
        )
        assert_true(
            current_precursor_summary_bytes == original_precursor_summary_bytes,
            "precursor summary input should remain unchanged",
        )
        assert_true(
            current_precursor_sites_bytes == original_precursor_sites_bytes,
            "precursor sites input should remain unchanged",
        )
        assert_true(
            current_active_batch_bytes == original_active_batch_bytes,
            "active review queue input should remain unchanged",
        )

        print("[OK] outputs generate")
        print("[OK] overall summary pulls the correct values from synthetic inputs")
        print("[OK] active_review_queue_count == 0 yields baseline_frozen_ready")
        print("[OK] deferred hold and precursor note sites classify correctly")
        print("[OK] decisions output expected statuses")
        print("[OK] no official outputs are modified")

    safe_deferred_res = run([sys.executable, str(safe_smoke_deferred)], root)
    assert_true(
        safe_deferred_res.returncode == 0,
        f"existing deferred-hold smoke failed:\n{safe_deferred_res.stdout}\n{safe_deferred_res.stderr}",
    )
    safe_precursor_res = run([sys.executable, str(safe_smoke_precursor)], root)
    assert_true(
        safe_precursor_res.returncode == 0,
        f"existing precursor smoke failed:\n{safe_precursor_res.stdout}\n{safe_precursor_res.stderr}",
    )
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
