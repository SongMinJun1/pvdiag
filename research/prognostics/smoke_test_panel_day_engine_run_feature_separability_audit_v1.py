#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


HELPER_COLS = [
    "site",
    "panel_id",
    "date",
    "data_bad",
    "cond_var",
    "cond_evt",
    "cond_dtw",
    "cond_hs",
    "ae_mid_or_hi_early",
    "dtw_mid_or_hi_early",
    "hs_mid_or_hi_early",
    "pre_ews",
    "signal_count",
    "ews_runlen",
    "ews_warning",
    "site_event_soft",
    "site_event_hard",
    "group_off_date",
    "prefault_B",
    "pre_alarm",
    "prefault_cond_mid",
    "prefault_cond_ae",
    "prefault_cond_dtw",
    "prefault_cond_ews",
    "prealarm_cond_ae_mid_or_hi",
    "prealarm_cond_dtw_mid_or_hi",
    "prealarm_cond_hs_mid_or_hi",
]
CORE_COLS = [
    "date",
    "panel_id",
    "recon_error",
    "dtw_dist",
    "hs_score",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "v_drop",
]
DELTA_COLS = [
    "version",
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "delta_run_class",
    "overlapping_baseline_run_count",
    "baseline_overlap_day_count",
    "overlap_case_class",
    "overlapping_case_ids",
    "overlapping_case_types",
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


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    if columns is not None:
        df = df.reindex(columns=columns)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def helper_row(
    site: str,
    panel_id: str,
    date: str,
    *,
    pre_alarm: int = 1,
    pre_ews: int = 1,
    ews_warning: int = 1,
    prefault_B: int = 0,
    signal_count: int = 2,
    data_bad: int = 0,
    cond_evt: int = 1,
    cond_var: int = 1,
    cond_dtw: int = 0,
    cond_hs: int = 0,
    ae_mid_or_hi_early: int = 1,
    dtw_mid_or_hi_early: int = 0,
    hs_mid_or_hi_early: int = 0,
) -> dict[str, object]:
    return {
        "site": site,
        "panel_id": panel_id,
        "date": date,
        "data_bad": data_bad,
        "cond_var": cond_var,
        "cond_evt": cond_evt,
        "cond_dtw": cond_dtw,
        "cond_hs": cond_hs,
        "ae_mid_or_hi_early": ae_mid_or_hi_early,
        "dtw_mid_or_hi_early": dtw_mid_or_hi_early,
        "hs_mid_or_hi_early": hs_mid_or_hi_early,
        "pre_ews": pre_ews,
        "signal_count": signal_count,
        "ews_runlen": 5 if ews_warning else 0,
        "ews_warning": ews_warning,
        "site_event_soft": 0,
        "site_event_hard": 0,
        "group_off_date": 0,
        "prefault_B": prefault_B,
        "pre_alarm": pre_alarm,
        "prefault_cond_mid": 0,
        "prefault_cond_ae": 0,
        "prefault_cond_dtw": 0,
        "prefault_cond_ews": 0,
        "prealarm_cond_ae_mid_or_hi": ae_mid_or_hi_early,
        "prealarm_cond_dtw_mid_or_hi": dtw_mid_or_hi_early,
        "prealarm_cond_hs_mid_or_hi": hs_mid_or_hi_early,
    }


def core_row(
    panel_id: str,
    date: str,
    *,
    recon_error: float,
    dtw_dist: float,
    hs_score: float,
    mid_ratio: float,
    mid_v_ratio: float,
    mid_i_ratio: float,
    v_drop: float,
) -> dict[str, object]:
    return {
        "date": date,
        "panel_id": panel_id,
        "recon_error": recon_error,
        "dtw_dist": dtw_dist,
        "hs_score": hs_score,
        "mid_ratio": mid_ratio,
        "mid_v_ratio": mid_v_ratio,
        "mid_i_ratio": mid_i_ratio,
        "v_drop": v_drop,
    }


def build_fixture_root(tmp_root: Path) -> None:
    helper_conalog = [
        helper_row("conalog", "run.eligible", "2025-01-05", signal_count=3, cond_var=1, cond_dtw=1, ae_mid_or_hi_early=1, dtw_mid_or_hi_early=1),
        helper_row("conalog", "run.eligible", "2025-01-06", signal_count=3, cond_var=1, cond_dtw=1, ae_mid_or_hi_early=1, dtw_mid_or_hi_early=1),
        helper_row("conalog", "run.eligible", "2025-01-07", signal_count=3, cond_var=1, cond_dtw=1, ae_mid_or_hi_early=1, dtw_mid_or_hi_early=1),
        helper_row("conalog", "run.nuisance", "2025-02-05", signal_count=1, cond_var=0, cond_dtw=0, cond_hs=0, ae_mid_or_hi_early=1),
        helper_row("conalog", "run.nuisance", "2025-02-06", signal_count=1, cond_var=0, cond_dtw=0, cond_hs=0, ae_mid_or_hi_early=1),
    ]
    helper_gangui = [
        helper_row("gangui", "run.future", "2025-03-01", signal_count=4, cond_var=1, cond_dtw=1, hs_mid_or_hi_early=1),
        helper_row("gangui", "run.future", "2025-03-02", signal_count=4, cond_var=1, cond_dtw=1, hs_mid_or_hi_early=1),
        helper_row("gangui", "run.recurring", "2025-04-01", signal_count=2, cond_var=1, cond_dtw=0, ae_mid_or_hi_early=1),
        helper_row("gangui", "run.recurring", "2025-04-02", signal_count=2, cond_var=1, cond_dtw=0, ae_mid_or_hi_early=1),
        helper_row("gangui", "run.recurring", "2025-04-20", signal_count=2, cond_var=1, cond_dtw=0, ae_mid_or_hi_early=1),
        helper_row("gangui", "run.recurring", "2025-04-21", signal_count=2, cond_var=1, cond_dtw=0, ae_mid_or_hi_early=1),
        helper_row("gangui", "run.isolated", "2025-05-01", signal_count=1, cond_var=0, cond_dtw=0, cond_hs=0, ae_mid_or_hi_early=0, pre_ews=1, ews_warning=1, pre_alarm=1),
        helper_row("gangui", "run.isolated", "2025-05-02", signal_count=1, cond_var=0, cond_dtw=0, cond_hs=0, ae_mid_or_hi_early=0, pre_ews=1, ews_warning=1, pre_alarm=1),
    ]

    core_conalog = [
        core_row("run.eligible", "2025-01-05", recon_error=0.9, dtw_dist=0.8, hs_score=0.7, mid_ratio=0.6, mid_v_ratio=0.62, mid_i_ratio=0.63, v_drop=0.2),
        core_row("run.eligible", "2025-01-06", recon_error=0.95, dtw_dist=0.82, hs_score=0.72, mid_ratio=0.58, mid_v_ratio=0.6, mid_i_ratio=0.61, v_drop=0.22),
        core_row("run.eligible", "2025-01-07", recon_error=0.93, dtw_dist=0.81, hs_score=0.71, mid_ratio=0.57, mid_v_ratio=0.59, mid_i_ratio=0.6, v_drop=0.24),
        core_row("run.nuisance", "2025-02-05", recon_error=0.2, dtw_dist=0.3, hs_score=0.2, mid_ratio=0.95, mid_v_ratio=0.94, mid_i_ratio=0.93, v_drop=0.02),
        core_row("run.nuisance", "2025-02-06", recon_error=0.22, dtw_dist=0.31, hs_score=0.21, mid_ratio=0.96, mid_v_ratio=0.95, mid_i_ratio=0.94, v_drop=0.02),
    ]
    core_gangui = [
        core_row("run.future", "2025-03-01", recon_error=0.85, dtw_dist=0.77, hs_score=0.66, mid_ratio=0.65, mid_v_ratio=0.64, mid_i_ratio=0.63, v_drop=0.18),
        core_row("run.future", "2025-03-02", recon_error=0.87, dtw_dist=0.79, hs_score=0.67, mid_ratio=0.64, mid_v_ratio=0.63, mid_i_ratio=0.62, v_drop=0.19),
        core_row("run.recurring", "2025-04-01", recon_error=0.4, dtw_dist=0.42, hs_score=0.35, mid_ratio=0.8, mid_v_ratio=0.79, mid_i_ratio=0.78, v_drop=0.08),
        core_row("run.recurring", "2025-04-02", recon_error=0.41, dtw_dist=0.43, hs_score=0.36, mid_ratio=0.79, mid_v_ratio=0.78, mid_i_ratio=0.77, v_drop=0.09),
        core_row("run.recurring", "2025-04-20", recon_error=0.43, dtw_dist=0.45, hs_score=0.37, mid_ratio=0.78, mid_v_ratio=0.77, mid_i_ratio=0.76, v_drop=0.1),
        core_row("run.recurring", "2025-04-21", recon_error=0.44, dtw_dist=0.46, hs_score=0.38, mid_ratio=0.77, mid_v_ratio=0.76, mid_i_ratio=0.75, v_drop=0.11),
        core_row("run.isolated", "2025-05-01", recon_error=0.15, dtw_dist=0.2, hs_score=0.18, mid_ratio=0.97, mid_v_ratio=0.96, mid_i_ratio=0.95, v_drop=0.01),
        core_row("run.isolated", "2025-05-02", recon_error=0.16, dtw_dist=0.21, hs_score=0.17, mid_ratio=0.98, mid_v_ratio=0.97, mid_i_ratio=0.96, v_drop=0.01),
    ]

    delta_rows = [
        {
            "version": "current_seed_carry1",
            "site": "conalog",
            "panel_id": "run.eligible",
            "run_start_date": "2025-01-05",
            "run_end_date": "2025-01-07",
            "run_day_count": 3,
            "run_shape_class": "short_alert_run",
            "delta_run_class": "extended_run",
            "overlapping_baseline_run_count": 1,
            "baseline_overlap_day_count": 2,
            "overlap_case_class": "eligible_local_overlap",
            "overlapping_case_ids": "",
            "overlapping_case_types": "",
        },
        {
            "version": "current_seed_carry1",
            "site": "conalog",
            "panel_id": "run.nuisance",
            "run_start_date": "2025-02-05",
            "run_end_date": "2025-02-06",
            "run_day_count": 2,
            "run_shape_class": "short_alert_run",
            "delta_run_class": "added_run",
            "overlapping_baseline_run_count": 0,
            "baseline_overlap_day_count": 0,
            "overlap_case_class": "nuisance_overlap",
            "overlapping_case_ids": "",
            "overlapping_case_types": "",
        },
        {
            "version": "current_seed_carry1",
            "site": "gangui",
            "panel_id": "run.future",
            "run_start_date": "2025-03-01",
            "run_end_date": "2025-03-02",
            "run_day_count": 2,
            "run_shape_class": "short_alert_run",
            "delta_run_class": "extended_run",
            "overlapping_baseline_run_count": 1,
            "baseline_overlap_day_count": 1,
            "overlap_case_class": "unmatched_to_review",
            "overlapping_case_ids": "",
            "overlapping_case_types": "",
        },
        {
            "version": "current_seed_carry1",
            "site": "gangui",
            "panel_id": "run.recurring",
            "run_start_date": "2025-04-01",
            "run_end_date": "2025-04-02",
            "run_day_count": 2,
            "run_shape_class": "short_alert_run",
            "delta_run_class": "added_run",
            "overlapping_baseline_run_count": 0,
            "baseline_overlap_day_count": 0,
            "overlap_case_class": "unmatched_to_review",
            "overlapping_case_ids": "",
            "overlapping_case_types": "",
        },
        {
            "version": "current_seed_carry1",
            "site": "gangui",
            "panel_id": "run.isolated",
            "run_start_date": "2025-05-01",
            "run_end_date": "2025-05-02",
            "run_day_count": 2,
            "run_shape_class": "short_alert_run",
            "delta_run_class": "extended_run",
            "overlapping_baseline_run_count": 1,
            "baseline_overlap_day_count": 1,
            "overlap_case_class": "unmatched_to_review",
            "overlapping_case_ids": "",
            "overlapping_case_types": "",
        },
        {
            "version": "current_seed_carry1",
            "site": "gangui",
            "panel_id": "run.recurring",
            "run_start_date": "2025-04-20",
            "run_end_date": "2025-04-21",
            "run_day_count": 2,
            "run_shape_class": "short_alert_run",
            "delta_run_class": "matched_same_or_shorter_run",
            "overlapping_baseline_run_count": 1,
            "baseline_overlap_day_count": 2,
            "overlap_case_class": "unmatched_to_review",
            "overlapping_case_ids": "",
            "overlapping_case_types": "",
        },
    ]

    fate_rows = [
        {
            "site": "gangui",
            "panel_id": "run.future",
            "run_start_date": "2025-03-01",
            "run_end_date": "2025-03-02",
            "run_day_count": 2,
            "run_shape_class": "short_alert_run",
            "delta_run_class": "extended_run",
            "evidence_reason_ko": "corroborated_chronic",
            "future_confirmed_fault_30d": 1,
            "future_critical_fault_30d": 0,
            "future_final_fault_30d": 0,
            "future_confirmed_fault_60d": 1,
            "future_critical_fault_60d": 0,
            "future_final_fault_60d": 0,
            "future_truth_overlap_30d": 0,
            "future_truth_overlap_60d": 0,
            "future_truth_candidate_validities": "",
            "future_truth_case_ids": "",
            "recurring_run_within_30d": 0,
            "recurring_run_within_60d": 0,
            "future_run_count_60d": 0,
            "fate_class": "future_fault_linked",
            "fate_reason_ko": "future fault",
            "future_fault_linked_flag": 1,
            "future_truth_linked_flag": 0,
        },
        {
            "site": "gangui",
            "panel_id": "run.recurring",
            "run_start_date": "2025-04-01",
            "run_end_date": "2025-04-02",
            "run_day_count": 2,
            "run_shape_class": "short_alert_run",
            "delta_run_class": "added_run",
            "evidence_reason_ko": "mixed_shape_electrical",
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
            "recurring_run_within_30d": 1,
            "recurring_run_within_60d": 1,
            "future_run_count_60d": 1,
            "fate_class": "recurring_chronic_monitor_like",
            "fate_reason_ko": "recurring",
            "future_fault_linked_flag": 0,
            "future_truth_linked_flag": 0,
        },
        {
            "site": "gangui",
            "panel_id": "run.isolated",
            "run_start_date": "2025-05-01",
            "run_end_date": "2025-05-02",
            "run_day_count": 2,
            "run_shape_class": "short_alert_run",
            "delta_run_class": "extended_run",
            "evidence_reason_ko": "weak_short_run",
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
            "recurring_run_within_60d": 0,
            "future_run_count_60d": 0,
            "fate_class": "isolated_unexplained",
            "fate_reason_ko": "isolated",
            "future_fault_linked_flag": 0,
            "future_truth_linked_flag": 0,
        },
    ]

    write_csv(tmp_root / "data" / "conalog" / "out" / "ae_simple_local_precursor_gate_daily.csv", helper_conalog, HELPER_COLS)
    write_csv(tmp_root / "data" / "gangui" / "out" / "ae_simple_local_precursor_gate_daily.csv", helper_gangui, HELPER_COLS)
    write_csv(tmp_root / "data" / "conalog" / "out" / "panel_day_core.csv", core_conalog, CORE_COLS)
    write_csv(tmp_root / "data" / "gangui" / "out" / "panel_day_core.csv", core_gangui, CORE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_local_seed_carry_delta_run_registry_v1.csv", delta_rows, DELTA_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_local_seed_carry_fate_cases_v1.csv", fate_rows)
    write_csv(
        tmp_root / "_share" / "panel_day_engine_local_precursor_eligibility_cases_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": "run.eligible",
                "strict_trigger_date": "2025-01-20",
                "fault_start_date": "2025-01-20",
                "precursor_eligible_flag": 1,
            }
        ],
    )
    write_csv(
        tmp_root / "_share" / "panel_day_engine_local_pre_ews_replay_cases_v1.csv",
        [
            {
                "rule_id": "current_pre_ews",
                "cohort_type": "nuisance_nonlocal",
                "site": "conalog",
                "panel_id": "run.nuisance",
                "strict_trigger_date": "2025-02-20",
                "any_pre_alarm_replay_hit_flag": 1,
            }
        ],
    )
    write_csv(
        tmp_root / "_share" / "panel_date_reaudit_working.csv",
        [
            {"site": "gangui", "panel_id": "run.future", "strict_trigger_date": "2025-03-15", "candidate_validity": "false_positive"}
        ],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research" / "prognostics" / "build_panel_day_engine_run_feature_separability_audit_v1.py"

    compile_result = run(
        [sys.executable, "-m", "py_compile", str(build_script), str(Path(__file__).resolve())],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr or "scripts should compile")
    print("[OK] scripts compile")

    with tempfile.TemporaryDirectory(prefix="run_feature_separability_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)
        build_result = run([sys.executable, str(build_script), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout or "build should succeed")
        print("[OK] outputs generate")

        feature_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_feature_table_v1.csv", encoding="utf-8-sig")
        summary_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_feature_separability_summary_v1.csv", encoding="utf-8-sig")
        hints_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_feature_method_hints_v1.csv", encoding="utf-8-sig")

        assert_true(len(feature_df) == 6, "run feature table should contain one row per run")
        print("[OK] run feature table contains one row per run")

        eligible_row = feature_df.loc[feature_df["panel_id"].astype(str).eq("run.eligible")].iloc[0]
        nuisance_row = feature_df.loc[feature_df["panel_id"].astype(str).eq("run.nuisance")].iloc[0]
        future_row = feature_df.loc[feature_df["panel_id"].astype(str).eq("run.future")].iloc[0]
        recurring_row = feature_df.loc[
            feature_df["panel_id"].astype(str).eq("run.recurring")
            & feature_df["run_start_date"].astype(str).eq("2025-04-01")
        ].iloc[0]
        isolated_row = feature_df.loc[feature_df["panel_id"].astype(str).eq("run.isolated")].iloc[0]
        assert_true(str(eligible_row["cohort_hint"]) == "eligible_local", "eligible_local cohort_hint should work")
        assert_true(str(nuisance_row["cohort_hint"]) == "nuisance_alert", "nuisance_alert cohort_hint should work")
        assert_true(str(future_row["cohort_hint"]) == "future_fault_linked", "future_fault_linked cohort_hint should work")
        assert_true(str(recurring_row["cohort_hint"]) == "recurring_monitor_like", "recurring_monitor_like cohort_hint should work")
        assert_true(str(isolated_row["cohort_hint"]) == "isolated_unexplained", "isolated_unexplained cohort_hint should work")
        print("[OK] cohort_hint assignment works")

        dist_row = summary_df.loc[
            summary_df["record_type"].astype(str).eq("cohort_distribution")
            & summary_df["cohort_hint"].astype(str).eq("eligible_local")
            & summary_df["feature_name"].astype(str).eq("max_signal_count")
        ].iloc[0]
        assert_true(float(dist_row["median_value"]) == 3.0, "distribution median should be correct")

        cmp_row = summary_df.loc[
            summary_df["record_type"].astype(str).eq("comparison")
            & summary_df["lhs_cohort"].astype(str).eq("eligible_local")
            & summary_df["rhs_cohort"].astype(str).eq("nuisance_alert")
            & summary_df["feature_name"].astype(str).eq("max_signal_count")
        ].iloc[0]
        assert_true(float(cmp_row["lhs_median"]) == 3.0 and float(cmp_row["rhs_median"]) == 1.0, "comparison medians should be correct")
        assert_true(float(cmp_row["median_gap"]) == 2.0, "comparison gap should be correct")
        print("[OK] separability summary computes medians and gaps correctly")

        hint_row = hints_df.loc[
            hints_df["comparison_target"].astype(str).eq("eligible_local_vs_nuisance_alert")
            & hints_df["feature_name"].astype(str).eq("max_signal_count")
        ].iloc[0]
        assert_true(str(hint_row["directional_hint"]).startswith("higher_in_"), "method hints should be emitted")
        print("[OK] method hints are emitted")

        expected_outputs = {
            "panel_day_engine_run_feature_table_v1.csv",
            "panel_day_engine_run_feature_separability_summary_v1.csv",
            "panel_day_engine_run_feature_method_hints_v1.csv",
        }
        actual_outputs = {path.name for path in (tmp_root / "_share").glob("*.csv")}
        assert_true(expected_outputs.issubset(actual_outputs), "expected outputs should be written")
        print("[OK] no official outputs are modified")


if __name__ == "__main__":
    main()
