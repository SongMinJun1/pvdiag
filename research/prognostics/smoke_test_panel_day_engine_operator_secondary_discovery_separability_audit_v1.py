#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DISCOVERY_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "logistic_v3_discovery_score",
    "electrical_core_minus_broadshape_050",
    "global_discovery_rank",
    "site_discovery_rank",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "discovery_reason_ko",
]
FATE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "discovery_fate_class",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture_root(tmp_root: Path) -> None:
    share_dir = tmp_root / "_share"
    discovery_rows = [
        {
            "site": "alpha",
            "panel_id": "fault.a",
            "run_start_date": "2025-01-01",
            "run_end_date": "2025-01-02",
            "run_day_count": 2,
            "run_shape_class": "short_alert_run",
            "logistic_v3_discovery_score": 0.95,
            "electrical_core_minus_broadshape_050": 12.0,
            "global_discovery_rank": 1,
            "site_discovery_rank": 1,
            "max_v_drop": 0.80,
            "min_mid_v_ratio": 0.20,
            "min_mid_ratio": 0.25,
            "cond_evt_only_day_ratio": 0.20,
            "ae_mid_or_hi_early_day_ratio": 0.90,
            "mean_signal_count": 2.0,
            "max_signal_count": 3.0,
            "p95_recon_error": 0.08,
            "discovery_reason_ko": "fault",
        },
        {
            "site": "alpha",
            "panel_id": "fault.b",
            "run_start_date": "2025-01-05",
            "run_end_date": "2025-01-08",
            "run_day_count": 4,
            "run_shape_class": "medium_alert_run",
            "logistic_v3_discovery_score": 0.92,
            "electrical_core_minus_broadshape_050": 10.0,
            "global_discovery_rank": 2,
            "site_discovery_rank": 2,
            "max_v_drop": 0.70,
            "min_mid_v_ratio": 0.25,
            "min_mid_ratio": 0.30,
            "cond_evt_only_day_ratio": 0.30,
            "ae_mid_or_hi_early_day_ratio": 0.80,
            "mean_signal_count": 2.0,
            "max_signal_count": 2.0,
            "p95_recon_error": 0.07,
            "discovery_reason_ko": "fault",
        },
        {
            "site": "alpha",
            "panel_id": "iso.a",
            "run_start_date": "2025-01-10",
            "run_end_date": "2025-01-10",
            "run_day_count": 1,
            "run_shape_class": "short_alert_run",
            "logistic_v3_discovery_score": 0.50,
            "electrical_core_minus_broadshape_050": 3.0,
            "global_discovery_rank": 3,
            "site_discovery_rank": 3,
            "max_v_drop": 0.15,
            "min_mid_v_ratio": 0.82,
            "min_mid_ratio": 0.84,
            "cond_evt_only_day_ratio": 0.70,
            "ae_mid_or_hi_early_day_ratio": 0.20,
            "mean_signal_count": 1.0,
            "max_signal_count": 1.0,
            "p95_recon_error": 0.03,
            "discovery_reason_ko": "isolated",
        },
        {
            "site": "beta",
            "panel_id": "recur.a",
            "run_start_date": "2025-02-01",
            "run_end_date": "2025-02-02",
            "run_day_count": 2,
            "run_shape_class": "short_alert_run",
            "logistic_v3_discovery_score": 0.70,
            "electrical_core_minus_broadshape_050": 4.0,
            "global_discovery_rank": 4,
            "site_discovery_rank": 1,
            "max_v_drop": 0.30,
            "min_mid_v_ratio": 0.60,
            "min_mid_ratio": 0.62,
            "cond_evt_only_day_ratio": 0.80,
            "ae_mid_or_hi_early_day_ratio": 0.40,
            "mean_signal_count": 1.0,
            "max_signal_count": 1.0,
            "p95_recon_error": 0.04,
            "discovery_reason_ko": "recur",
        },
        {
            "site": "beta",
            "panel_id": "recur.b",
            "run_start_date": "2025-02-06",
            "run_end_date": "2025-02-10",
            "run_day_count": 5,
            "run_shape_class": "medium_alert_run",
            "logistic_v3_discovery_score": 0.72,
            "electrical_core_minus_broadshape_050": 6.0,
            "global_discovery_rank": 5,
            "site_discovery_rank": 2,
            "max_v_drop": 0.35,
            "min_mid_v_ratio": 0.65,
            "min_mid_ratio": 0.66,
            "cond_evt_only_day_ratio": 0.75,
            "ae_mid_or_hi_early_day_ratio": 0.45,
            "mean_signal_count": 1.0,
            "max_signal_count": 2.0,
            "p95_recon_error": 0.05,
            "discovery_reason_ko": "recur",
        },
        {
            "site": "gamma",
            "panel_id": "iso.b",
            "run_start_date": "2025-03-01",
            "run_end_date": "2025-03-01",
            "run_day_count": 1,
            "run_shape_class": "short_alert_run",
            "logistic_v3_discovery_score": 0.40,
            "electrical_core_minus_broadshape_050": 2.0,
            "global_discovery_rank": 6,
            "site_discovery_rank": 1,
            "max_v_drop": 0.10,
            "min_mid_v_ratio": 0.90,
            "min_mid_ratio": 0.92,
            "cond_evt_only_day_ratio": 0.90,
            "ae_mid_or_hi_early_day_ratio": 0.10,
            "mean_signal_count": 1.0,
            "max_signal_count": 1.0,
            "p95_recon_error": 0.02,
            "discovery_reason_ko": "isolated",
        },
    ]
    fate_rows = [
        {"site": "alpha", "panel_id": "fault.a", "run_start_date": "2025-01-01", "run_end_date": "2025-01-02", "discovery_fate_class": "future_fault_linked"},
        {"site": "alpha", "panel_id": "fault.b", "run_start_date": "2025-01-05", "run_end_date": "2025-01-08", "discovery_fate_class": "future_fault_linked"},
        {"site": "alpha", "panel_id": "iso.a", "run_start_date": "2025-01-10", "run_end_date": "2025-01-10", "discovery_fate_class": "isolated_unexplained"},
        {"site": "beta", "panel_id": "recur.a", "run_start_date": "2025-02-01", "run_end_date": "2025-02-02", "discovery_fate_class": "recurring_monitor_like"},
        {"site": "beta", "panel_id": "recur.b", "run_start_date": "2025-02-06", "run_end_date": "2025-02-10", "discovery_fate_class": "recurring_monitor_like"},
        {"site": "gamma", "panel_id": "iso.b", "run_start_date": "2025-03-01", "run_end_date": "2025-03-01", "discovery_fate_class": "isolated_unexplained"},
    ]

    write_csv(share_dir / "panel_day_engine_operator_secondary_discovery_v1.csv", discovery_rows, DISCOVERY_COLS)
    write_csv(share_dir / "panel_day_engine_operator_secondary_discovery_fate_cases_v1.csv", fate_rows, FATE_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research" / "prognostics" / "build_panel_day_engine_operator_secondary_discovery_separability_audit_v1.py"

    py_compile.compile(str(repo_root / "pv_ae" / "panel_day_engine.py"), doraise=True)
    py_compile.compile(str(builder), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="secondary-discovery-separability-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        result = run([sys.executable, str(builder), "--root", str(tmp_root)], cwd=repo_root)
        if result.returncode != 0:
            raise SystemExit(f"builder failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        summary_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_separability_summary_v1.csv"
        cases_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_separability_cases_v1.csv"
        recommendation_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_separability_recommendation_v1.csv"
        assert_true(summary_path.exists(), "missing separability summary output")
        assert_true(cases_path.exists(), "missing separability cases output")
        assert_true(recommendation_path.exists(), "missing separability recommendation output")

        summary_df = pd.read_csv(summary_path, encoding="utf-8-sig")
        cases_df = pd.read_csv(cases_path, encoding="utf-8-sig")
        recommendation_df = pd.read_csv(recommendation_path, encoding="utf-8-sig")

        assert_true(len(cases_df) == 6, "should emit one case row per discovery run")

        fault_score_row = summary_df.loc[
            summary_df["record_type"].astype(str).eq("group_feature_summary")
            & summary_df["fate_group"].astype(str).eq("future_fault_linked")
            & summary_df["feature_name"].astype(str).eq("electrical_core_minus_broadshape_050")
        ].iloc[0]
        assert_true(float(fault_score_row["median_value"]) == 11.0, "fault median electrical score should match synthetic truth")
        assert_true(float(fault_score_row["p25_value"]) == 10.5, "fault p25 electrical score should be correct")
        assert_true(float(fault_score_row["p75_value"]) == 11.5, "fault p75 electrical score should be correct")

        cmp_row = summary_df.loc[
            summary_df["record_type"].astype(str).eq("comparison_summary")
            & summary_df["lhs_group"].astype(str).eq("future_fault_linked")
            & summary_df["rhs_group"].astype(str).eq("recurring_monitor_like")
            & summary_df["feature_name"].astype(str).eq("electrical_core_minus_broadshape_050")
        ].iloc[0]
        assert_true(float(cmp_row["median_gap"]) == 6.0, "median gap should be correct")
        assert_true(round(float(cmp_row["normalized_gap"]), 6) == 6.0, "normalized gap should be correct")

        alpha_row = summary_df.loc[
            summary_df["record_type"].astype(str).eq("site_effect_summary")
            & summary_df["site"].astype(str).eq("alpha")
        ].iloc[0]
        assert_true(int(alpha_row["selected_discovery_count"]) == 3, "site effect selected count should be correct")
        assert_true(int(alpha_row["future_fault_linked_count"]) == 2, "site effect future fault count should be correct")
        assert_true(int(alpha_row["isolated_unexplained_count"]) == 1, "site effect isolated count should be correct")
        assert_true(round(float(alpha_row["future_fault_or_truth_linked_rate"]), 6) == round(2 / 3, 6), "site linked rate should be correct")

        assert_true(
            recommendation_df.iloc[0]["recommended_next_direction"] == "try_feature_threshold_split",
            "strong current-state gap should recommend feature-threshold split",
        )

    print("smoke_test_panel_day_engine_operator_secondary_discovery_separability_audit_v1.py: PASS")


if __name__ == "__main__":
    main()
