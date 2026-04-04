#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

FEATURE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "overlap_case_class",
    "delta_run_class",
    "fate_class",
    "cohort_hint",
    "pre_ews_day_count",
    "ews_warning_day_count",
    "pre_alarm_day_count",
    "prefault_B_day_count",
    "pre_ews_run_count",
    "ews_warning_run_count",
    "pre_alarm_run_count",
    "prefault_B_run_count",
    "pre_alarm_max_run",
    "max_signal_count",
    "mean_signal_count",
    "any_data_bad",
    "data_bad_day_ratio",
    "cond_evt_day_ratio",
    "cond_evt_only_day_ratio",
    "cond_evt_same_day_early_corroborated_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "dtw_mid_or_hi_early_day_ratio",
    "hs_mid_or_hi_early_day_ratio",
    "max_recon_error",
    "p95_recon_error",
    "max_dtw_dist",
    "p95_dtw_dist",
    "max_hs_score",
    "p95_hs_score",
    "min_mid_ratio",
    "min_mid_v_ratio",
    "min_mid_i_ratio",
    "max_v_drop",
    "recurring_run_within_60d",
    "future_fault_linked_flag",
    "future_truth_linked_flag",
]
V0_SCORE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "cohort_hint",
    "electrical_core_score",
    "electrical_evt_score",
    "electrical_evt_minus_broadshape_score",
    "electrical_core_minus_broadshape_025",
    "electrical_core_minus_broadshape_050",
    "electrical_core_minus_broadshape_075",
    "electrical_core_plus_evtonly_minus_broadshape_025",
    "electrical_core_plus_evtonly_minus_broadshape_050",
]
FATE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "delta_run_class",
    "evidence_reason_ko",
    "future_confirmed_fault_7d",
    "future_critical_fault_7d",
    "future_final_fault_7d",
    "future_confirmed_fault_30d",
    "future_critical_fault_30d",
    "future_final_fault_30d",
    "future_confirmed_fault_60d",
    "future_critical_fault_60d",
    "future_final_fault_60d",
    "future_truth_overlap_30d",
    "future_truth_overlap_60d",
    "future_truth_candidate_validities",
    "future_truth_case_ids",
    "recurring_run_within_30d",
    "recurring_run_within_60d",
    "future_run_count_60d",
    "fate_class",
    "fate_reason_ko",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def feature_row(
    panel_id: str,
    start: str,
    end: str,
    run_day_count: int,
    score_seed: float,
    *,
    recurring: int = 0,
    future_fault: int = 0,
    future_truth: int = 0,
    fate_class: str = "",
) -> dict[str, object]:
    return {
        "site": "alpha",
        "panel_id": panel_id,
        "run_start_date": start,
        "run_end_date": end,
        "run_day_count": run_day_count,
        "run_shape_class": "chronic_alert_run" if run_day_count >= 10 else "short_alert_run",
        "overlap_case_class": "unmatched_to_review",
        "delta_run_class": "added_run",
        "fate_class": fate_class,
        "cohort_hint": "unmatched_other",
        "pre_ews_day_count": run_day_count,
        "ews_warning_day_count": run_day_count,
        "pre_alarm_day_count": run_day_count,
        "prefault_B_day_count": 0,
        "pre_ews_run_count": 1,
        "ews_warning_run_count": 1,
        "pre_alarm_run_count": 1,
        "prefault_B_run_count": 0,
        "pre_alarm_max_run": run_day_count,
        "max_signal_count": 2.0,
        "mean_signal_count": 1.5,
        "any_data_bad": 0,
        "data_bad_day_ratio": 0.0,
        "cond_evt_day_ratio": 1.0,
        "cond_evt_only_day_ratio": max(0.0, 1.0 - score_seed / 20.0),
        "cond_evt_same_day_early_corroborated_day_ratio": min(1.0, score_seed / 20.0),
        "ae_mid_or_hi_early_day_ratio": min(1.0, score_seed / 20.0),
        "dtw_mid_or_hi_early_day_ratio": 0.5,
        "hs_mid_or_hi_early_day_ratio": 0.3,
        "max_recon_error": 0.1,
        "p95_recon_error": 0.1,
        "max_dtw_dist": 10.0,
        "p95_dtw_dist": 9.5,
        "max_hs_score": 0.4,
        "p95_hs_score": 0.35,
        "min_mid_ratio": 0.5,
        "min_mid_v_ratio": 0.5,
        "min_mid_i_ratio": 0.5,
        "max_v_drop": 0.5,
        "recurring_run_within_60d": recurring,
        "future_fault_linked_flag": future_fault,
        "future_truth_linked_flag": future_truth,
    }


def score_row(feature: dict[str, object], score: float) -> dict[str, object]:
    return {
        "site": feature["site"],
        "panel_id": feature["panel_id"],
        "run_start_date": feature["run_start_date"],
        "run_end_date": feature["run_end_date"],
        "run_day_count": feature["run_day_count"],
        "run_shape_class": feature["run_shape_class"],
        "cohort_hint": feature["cohort_hint"],
        "electrical_core_score": score + 1.0,
        "electrical_evt_score": score + 0.5,
        "electrical_evt_minus_broadshape_score": score,
        "electrical_core_minus_broadshape_025": score,
        "electrical_core_minus_broadshape_050": score,
        "electrical_core_minus_broadshape_075": score - 0.5,
        "electrical_core_plus_evtonly_minus_broadshape_025": score,
        "electrical_core_plus_evtonly_minus_broadshape_050": score - 0.2,
    }


def fate_row(feature: dict[str, object], fate_class: str) -> dict[str, object]:
    return {
        "site": feature["site"],
        "panel_id": feature["panel_id"],
        "run_start_date": feature["run_start_date"],
        "run_end_date": feature["run_end_date"],
        "run_day_count": feature["run_day_count"],
        "run_shape_class": feature["run_shape_class"],
        "delta_run_class": feature["delta_run_class"],
        "evidence_reason_ko": "",
        "future_confirmed_fault_7d": 0,
        "future_critical_fault_7d": 0,
        "future_final_fault_7d": 0,
        "future_confirmed_fault_30d": 0,
        "future_critical_fault_30d": 0,
        "future_final_fault_30d": 0,
        "future_confirmed_fault_60d": 0,
        "future_critical_fault_60d": 0,
        "future_final_fault_60d": 0,
        "future_truth_overlap_30d": 0,
        "future_truth_overlap_60d": 0,
        "future_truth_candidate_validities": "",
        "future_truth_case_ids": "",
        "recurring_run_within_30d": 0,
        "recurring_run_within_60d": feature["recurring_run_within_60d"],
        "future_run_count_60d": 0,
        "fate_class": fate_class,
        "fate_reason_ko": "",
    }


def build_fixture_root(tmp_root: Path) -> None:
    features = [
        feature_row("alpha.r01", "2025-01-09", "2025-01-10", 12, 20.0, future_fault=1),
        feature_row("alpha.r02", "2025-01-08", "2025-01-08", 12, 19.0),
        feature_row("alpha.r03", "2025-01-07", "2025-01-09", 10, 18.0),
        feature_row("alpha.r04", "2025-01-01", "2025-01-02", 11, 17.0, recurring=1, future_truth=1),
        feature_row("alpha.r05", "2025-01-03", "2025-01-05", 5, 16.0),
    ]
    for idx in range(6, 21):
        start = f"2024-12-{idx:02d}" if idx <= 9 else f"2024-11-{idx:02d}"
        end = start
        features.append(feature_row(f"alpha.r{idx:02d}", start, end, 2, 21.0 - idx))

    explicit_scores = {
        "alpha.r01": 20.0,
        "alpha.r02": 19.0,
        "alpha.r03": 15.0,
        "alpha.r04": 17.0,
        "alpha.r05": 16.0,
    }
    scores = [score_row(row, explicit_scores.get(row["panel_id"], 21.0 - idx)) for idx, row in enumerate(features, start=1)]
    fates = [fate_row(features[2], "future_fault_linked")]

    write_csv(tmp_root / "_share" / "panel_day_engine_run_feature_table_v1.csv", features, FEATURE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v0_scores.csv", scores, V0_SCORE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_local_seed_carry_fate_cases_v1.csv", fates, FATE_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="operator_run_consolidation_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        compile_result = run(
            [
                sys.executable,
                "-m",
                "py_compile",
                "research/prognostics/build_panel_day_engine_operator_run_consolidation_v1.py",
                "research/prognostics/smoke_test_panel_day_engine_operator_run_consolidation_v1.py",
            ],
            repo_root,
        )
        assert_true(compile_result.returncode == 0, compile_result.stderr)

        build_result = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_operator_run_consolidation_v1.py",
                "--root",
                str(tmp_root),
            ],
            repo_root,
        )
        assert_true(build_result.returncode == 0, build_result.stderr)

        share_dir = tmp_root / "_share"
        registry = pd.read_csv(share_dir / "panel_day_engine_operator_run_registry_v1.csv")
        queue = pd.read_csv(share_dir / "panel_day_engine_operator_run_queue_v1.csv")
        backlog = pd.read_csv(share_dir / "panel_day_engine_operator_run_backlog_v1.csv")
        summary = pd.read_csv(share_dir / "panel_day_engine_operator_run_summary_v1.csv")

        assert_true(len(registry) == 20, "registry should contain one row per run")
        assert_true(len(queue) == 3, "queue should include only investigate_now/monitor_active runs")
        assert_true(len(backlog) == 2, "backlog should include recurring/recovered runs only")

        status_by_panel = dict(zip(registry["panel_id"], registry["status"]))
        assert_true(status_by_panel["alpha.r01"] == "ongoing_run", "alpha.r01 should be ongoing")
        assert_true(status_by_panel["alpha.r02"] == "new_run", "alpha.r02 should be new")
        assert_true(status_by_panel["alpha.r04"] == "recurring_run", "alpha.r04 should be recurring")
        assert_true(status_by_panel["alpha.r05"] == "recovered_run", "alpha.r05 should be recovered")
        assert_true(status_by_panel["alpha.r20"] == "historical_run", "alpha.r20 should be historical")

        band_by_panel = dict(zip(registry["panel_id"], registry["priority_band"]))
        assert_true(band_by_panel["alpha.r01"] == "P1", "top run should be P1")
        assert_true(band_by_panel["alpha.r02"] == "P2", "rank 2 should be P2")
        assert_true(band_by_panel["alpha.r10"] == "P3", "mid-ranked run should be P3")
        assert_true(band_by_panel["alpha.r20"] == "P4", "lowest run should be P4")

        action_by_panel = dict(zip(registry["panel_id"], registry["action_bucket"]))
        assert_true(action_by_panel["alpha.r01"] == "investigate_now", "ongoing P1 should investigate_now")
        assert_true(action_by_panel["alpha.r02"] == "investigate_now", "new P2 should investigate_now")
        assert_true(action_by_panel["alpha.r03"] == "monitor_active", "new P3 medium should monitor_active")
        assert_true(action_by_panel["alpha.r04"] == "recurring_backlog", "recurring run should go to recurring_backlog")
        assert_true(action_by_panel["alpha.r05"] == "recovered_backlog", "recovered run should go to recovered_backlog")
        assert_true(action_by_panel["alpha.r20"] == "historical_archive", "historical P4 should archive")

        queued_panels = set(queue["panel_id"])
        backlog_panels = set(backlog["panel_id"])
        assert_true("alpha.r01" in queued_panels, "ongoing P1 should be queued")
        assert_true("alpha.r02" in queued_panels, "new P2 should be queued")
        assert_true("alpha.r03" in queued_panels, "new P3 medium should be queued")
        assert_true("alpha.r04" not in queued_panels, "recurring backlog should not remain in queue")
        assert_true("alpha.r04" in backlog_panels, "P4 recurring run should move to backlog")
        assert_true("alpha.r05" not in queued_panels, "recovered run should not remain in queue")
        assert_true("alpha.r05" in backlog_panels, "recovered run should go to backlog")
        assert_true("alpha.r20" not in queued_panels, "historical P4 run should be excluded from queue")
        assert_true("alpha.r20" not in backlog_panels, "historical archive should be excluded from backlog")

        registry_panels = set(registry["panel_id"])
        assert_true(queued_panels.issubset(registry_panels), "queue must be subset of registry")
        assert_true(backlog_panels.issubset(registry_panels), "backlog must be subset of registry")

        fate_by_panel = dict(zip(registry["panel_id"], registry["fate_class"]))
        assert_true(fate_by_panel["alpha.r03"] == "future_fault_linked", "optional fate enrichment should fill fate_class")

        overall = summary.loc[summary["record_type"] == "overall"].iloc[0]
        assert_true(int(overall["investigate_now_count"]) == 2, "investigate_now count mismatch")
        assert_true(int(overall["monitor_active_count"]) == 1, "monitor_active count mismatch")
        assert_true(int(overall["recurring_backlog_count"]) == 1, "recurring_backlog count mismatch")
        assert_true(int(overall["recovered_backlog_count"]) == 1, "recovered_backlog count mismatch")
        assert_true(int(overall["historical_archive_count"]) == 15, "historical_archive count mismatch")
        assert_true(int(overall["queue_count"]) == 3, "overall queue count mismatch")
        assert_true(int(overall["backlog_count"]) == 2, "overall backlog count mismatch")
        assert_true(int(overall["p1_run_count"]) == 1, "overall P1 count mismatch")
        assert_true(int(overall["p2_run_count"]) == 3, "overall P2 count mismatch")
        assert_true(int(overall["queue_chronic_count"]) == 3, "queue chronic count mismatch")
        assert_true(int(overall["backlog_chronic_count"]) == 1, "backlog chronic count mismatch")


if __name__ == "__main__":
    main()
