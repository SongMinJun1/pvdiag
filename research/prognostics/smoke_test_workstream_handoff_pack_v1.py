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


def write_inputs(tmp_root: Path) -> list[Path]:
    share_dir = tmp_root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    input_paths: list[Path] = []

    freeze_summary_df = pd.DataFrame(
        [
            {
                "strict_maintenance_f1": 0.615384,
                "strict_operational_f1": 1.0,
                "lenient_maintenance_f1": 0.615384,
                "lenient_operational_f1": 1.0,
                "official_scored_count": 13,
                "manual_scored_count": 13,
                "vendor_scored_count": 0,
                "deferred_hold_count": 10,
                "active_review_queue_count": 0,
                "precursor_global_recommendation": "keep_under_observation",
                "freeze_recommendation": "baseline_frozen_ready",
            }
        ]
    )
    path = share_dir / "baseline_freeze_summary_v1.csv"
    freeze_summary_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    freeze_sites_df = pd.DataFrame(
        [
            {
                "site": "conalog",
                "official_scored_count": 7,
                "manual_scored_count": 7,
                "vendor_scored_count": 0,
                "deferred_hold_count": 0,
                "precursor_site_recommendation": "keep_site_specific_precursor_note",
                "site_status": "scored_with_site_specific_precursor_note",
            },
            {
                "site": "gangui",
                "official_scored_count": 4,
                "manual_scored_count": 4,
                "vendor_scored_count": 0,
                "deferred_hold_count": 10,
                "precursor_site_recommendation": "no_precursor_signal",
                "site_status": "scored_with_deferred_hold",
            },
            {
                "site": "ktc_ess",
                "official_scored_count": 2,
                "manual_scored_count": 2,
                "vendor_scored_count": 0,
                "deferred_hold_count": 0,
                "precursor_site_recommendation": "likely_site_pattern_not_generalizable",
                "site_status": "stable_scored_site",
            },
            {
                "site": "sinhyo",
                "official_scored_count": 0,
                "manual_scored_count": 0,
                "vendor_scored_count": 0,
                "deferred_hold_count": 0,
                "precursor_site_recommendation": "no_precursor_signal",
                "site_status": "stable_scored_site",
            },
        ]
    )
    path = share_dir / "baseline_freeze_sites_v1.csv"
    freeze_sites_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    freeze_decisions_df = pd.DataFrame(
        [
            {
                "decision_key": "official_baseline_status",
                "decision_status": "frozen",
                "decision_reason": "Baseline is frozen.",
                "supporting_value": "baseline_frozen_ready",
            },
            {
                "decision_key": "active_truth_review_queue",
                "decision_status": "empty",
                "decision_reason": "No active review rows remain.",
                "supporting_value": "0",
            },
            {
                "decision_key": "deferred_high_actionability_rows",
                "decision_status": "on_hold",
                "decision_reason": "Deferred rows remain on hold.",
                "supporting_value": "10",
            },
            {
                "decision_key": "global_precursor_addon",
                "decision_status": "keep_under_observation",
                "decision_reason": "Global addon is not adopted.",
                "supporting_value": "broad_3g_10p",
            },
            {
                "decision_key": "conalog_precursor_note",
                "decision_status": "keep",
                "decision_reason": "Conalog keeps a site note.",
                "supporting_value": "keep_site_specific_precursor_note",
            },
            {
                "decision_key": "next_workstream_recommendation",
                "decision_status": "safe_to_switch_topic",
                "decision_reason": "Baseline is frozen and review queue is empty.",
                "supporting_value": "baseline_frozen_ready",
            },
        ]
    )
    path = share_dir / "baseline_freeze_decisions_v1.csv"
    freeze_decisions_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    guard_summary_df = pd.DataFrame(
        [
            {
                "guard_status": "frozen_baseline_preserved",
                "overall_diff_count": 0,
                "site_diff_count": 0,
                "decision_diff_count": 0,
                "total_diff_count": 0,
                "frozen_strict_maintenance_f1": "0.615384",
                "current_strict_maintenance_f1": "0.615384",
                "frozen_strict_operational_f1": "1.000000",
                "current_strict_operational_f1": "1.000000",
                "frozen_lenient_maintenance_f1": "0.615384",
                "current_lenient_maintenance_f1": "0.615384",
                "frozen_lenient_operational_f1": "1.000000",
                "current_lenient_operational_f1": "1.000000",
                "frozen_official_scored_count": "13",
                "current_official_scored_count": "13",
                "frozen_manual_scored_count": "13",
                "current_manual_scored_count": "13",
                "frozen_vendor_scored_count": "0",
                "current_vendor_scored_count": "0",
                "frozen_deferred_hold_count": "10",
                "current_deferred_hold_count": "10",
                "frozen_active_review_queue_count": "0",
                "current_active_review_queue_count": "0",
                "frozen_precursor_global_recommendation": "keep_under_observation",
                "current_precursor_global_recommendation": "keep_under_observation",
                "frozen_freeze_recommendation": "baseline_frozen_ready",
                "current_freeze_recommendation": "baseline_frozen_ready",
            }
        ]
    )
    path = share_dir / "baseline_regression_guard_summary_v1.csv"
    guard_summary_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    guard_sites_df = pd.DataFrame(
        [
            {
                "site": "conalog",
                "frozen_site_status": "scored_with_site_specific_precursor_note",
                "current_site_status": "scored_with_site_specific_precursor_note",
                "site_diff_count": 0,
                "site_guard_status": "preserved",
            },
            {
                "site": "gangui",
                "frozen_site_status": "scored_with_deferred_hold",
                "current_site_status": "scored_with_deferred_hold",
                "site_diff_count": 0,
                "site_guard_status": "preserved",
            },
            {
                "site": "ktc_ess",
                "frozen_site_status": "stable_scored_site",
                "current_site_status": "stable_scored_site",
                "site_diff_count": 0,
                "site_guard_status": "preserved",
            },
            {
                "site": "sinhyo",
                "frozen_site_status": "stable_scored_site",
                "current_site_status": "stable_scored_site",
                "site_diff_count": 0,
                "site_guard_status": "preserved",
            },
        ]
    )
    path = share_dir / "baseline_regression_guard_sites_v1.csv"
    guard_sites_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    deferred_hold_df = pd.DataFrame(
        [
            {
                "site": "gangui",
                "panel_id": "gangui.0.1",
                "strict_trigger_date": "2025-11-11",
                "review_priority_bucket": "high_actionability_unlabeled",
                "priority_score": 61,
                "critical_phenotype_v3": "common_cause_borderline",
                "actionability_v3": "common_cause_review",
                "hold_reason": "deferred_high_actionability_without_field_evidence",
                "hold_status": "on_hold",
                "reactivation_condition": "field_or_OM_evidence_available",
            },
            {
                "site": "gangui",
                "panel_id": "gangui.0.2",
                "strict_trigger_date": "2025-11-12",
                "review_priority_bucket": "high_actionability_unlabeled",
                "priority_score": 62,
                "critical_phenotype_v3": "electrical_fault_like",
                "actionability_v3": "maintenance_candidate",
                "hold_reason": "deferred_high_actionability_without_field_evidence",
                "hold_status": "on_hold",
                "reactivation_condition": "field_or_OM_evidence_available",
            },
        ]
    )
    path = share_dir / "truth_review_deferred_hold_v1.csv"
    deferred_hold_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

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
                "site_decision_reason": "Conalog note only.",
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
                "site_decision_reason": "No precursor signal.",
            },
            {
                "site": "ktc_ess",
                "candidate_day_count": 4,
                "plausible_precursor_day_count": 0,
                "episode_aligned_day_count": 0,
                "likely_persistent_site_pattern_count": 2,
                "likely_sparse_site_pattern_count": 2,
                "ambiguous_case_count": 0,
                "site_recommendation": "likely_site_pattern_not_generalizable",
                "site_decision_reason": "Site pattern only.",
            },
            {
                "site": "sinhyo",
                "candidate_day_count": 0,
                "plausible_precursor_day_count": 0,
                "episode_aligned_day_count": 0,
                "likely_persistent_site_pattern_count": 0,
                "likely_sparse_site_pattern_count": 0,
                "ambiguous_case_count": 0,
                "site_recommendation": "no_precursor_signal",
                "site_decision_reason": "No precursor signal.",
            },
        ]
    )
    path = share_dir / "common_cause_precursor_decision_sites_v1.csv"
    precursor_sites_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    optional_scope_summary_df = pd.DataFrame(
        [
            {
                "record_type": "summary",
                "total_strict_cases": 114,
                "official_scored_count": 13,
                "manual_scored_count": 13,
                "vendor_scored_count": 0,
            }
        ]
    )
    path = share_dir / "score_scope_manifest_summary_v1.csv"
    optional_scope_summary_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    return input_paths


def snapshot_bytes(paths: list[Path]) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in paths}


def assert_bytes_unchanged(before: dict[Path, bytes]) -> None:
    for path, expected in before.items():
        current = path.read_bytes()
        if current != expected:
            raise SystemExit(f"input file changed unexpectedly: {path.name}")


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_workstream_handoff_pack_v1.py"
    safe_smoke_guard = root / "research" / "prognostics" / "smoke_test_baseline_regression_guard_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script), str(Path(__file__))], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        input_paths = write_inputs(tmp_root)
        before = snapshot_bytes(input_paths)

        build_res = run(
            [sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "conalog", "gangui", "ktc_ess", "sinhyo"],
            root,
        )
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        share_dir = tmp_root / "_share"
        summary_path = share_dir / "workstream_handoff_summary_v1.csv"
        sites_path = share_dir / "workstream_handoff_sites_v1.csv"
        threads_path = share_dir / "workstream_handoff_open_threads_v1.csv"
        assert_true(summary_path.exists(), "summary output was not generated")
        assert_true(sites_path.exists(), "site output was not generated")
        assert_true(threads_path.exists(), "open thread output was not generated")

        summary_df = pd.read_csv(summary_path, encoding="utf-8-sig")
        sites_df = pd.read_csv(sites_path, encoding="utf-8-sig")
        threads_df = pd.read_csv(threads_path, encoding="utf-8-sig")

        assert_true(len(summary_df) == 1, "handoff summary should have exactly one row")
        summary_row = summary_df.iloc[0]
        assert_true(
            str(summary_row["next_workstream_recommendation"]).strip() == "safe_to_switch_topic",
            "synthetic frozen+guarded input should yield safe_to_switch_topic",
        )
        assert_true(
            str(summary_row["baseline_guard_status"]).strip() == "frozen_baseline_preserved",
            "baseline_guard_status should come from the guard summary",
        )

        assert_true(len(sites_df) == 4, "handoff site output should include all four sites")
        note_map = dict(zip(sites_df["site"].astype(str), sites_df["handoff_note_ko"].astype(str)))
        assert_true(
            "precursor site note" in note_map.get("conalog", ""),
            "conalog should carry a site-specific precursor note handoff",
        )
        assert_true(
            "deferred hold" in note_map.get("gangui", ""),
            "gangui should carry a deferred-hold handoff note",
        )
        assert_true(
            "안정 사이트" in note_map.get("ktc_ess", ""),
            "ktc_ess should be described as a stable scored site",
        )
        assert_true(
            "scored row는 없고" in note_map.get("sinhyo", ""),
            "sinhyo should be described as no scored rows / stable",
        )

        required_keys = {
            "gangui_deferred_high_actionability",
            "conalog_site_specific_precursor_note",
            "precursor_global_addon",
            "baseline_regression_guard",
        }
        assert_true(
            set(threads_df["thread_key"].astype(str)) == required_keys,
            "open thread output should contain the required thread keys exactly once",
        )
        assert_true(
            threads_df["thread_key"].astype(str).is_unique,
            "required open thread keys should appear exactly once",
        )

        assert_bytes_unchanged(before)

    print("[OK] outputs generate")
    print("[OK] synthetic frozen+guarded input yields safe_to_switch_topic")
    print("[OK] site handoff notes populate")
    print("[OK] required open thread keys appear exactly once")
    print("[OK] no official outputs are modified")

    safe_smoke_res = run([sys.executable, str(safe_smoke_guard)], root)
    assert_true(
        safe_smoke_res.returncode == 0,
        f"existing safe smoke failed:\n{safe_smoke_res.stdout}\n{safe_smoke_res.stderr}",
    )
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
