#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


FATE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "logistic_v3_discovery_score",
    "electrical_core_minus_broadshape_050",
    "future_confirmed_fault_30d",
    "future_critical_fault_30d",
    "future_final_fault_30d",
    "future_confirmed_fault_60d",
    "future_critical_fault_60d",
    "future_final_fault_60d",
    "future_truth_overlap_30d",
    "future_truth_overlap_60d",
    "future_truth_case_ids",
    "future_truth_candidate_validities",
    "recurring_run_within_30d",
    "recurring_run_within_60d",
    "future_run_count_60d",
    "discovery_fate_class",
    "discovery_fate_reason_ko",
    "ae_mid_or_hi_early_day_ratio",
    "p95_recon_error",
    "max_v_drop",
    "min_mid_ratio",
]
SEPARABILITY_COLS = [
    "record_type",
    "fate_group",
    "feature_name",
    "run_count",
    "median_value",
    "p25_value",
    "p75_value",
    "lhs_group",
    "rhs_group",
    "lhs_median",
    "rhs_median",
    "median_gap",
    "normalized_gap",
    "site",
    "selected_discovery_count",
    "future_fault_linked_count",
    "future_truth_linked_count",
    "recurring_monitor_like_count",
    "isolated_unexplained_count",
    "future_fault_or_truth_linked_rate",
    "recurring_monitor_like_rate",
    "isolated_unexplained_rate",
    "note_ko",
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

    fate_rows = [
        {
            "site": "alpha",
            "panel_id": "pos.a",
            "run_start_date": "2025-01-01",
            "run_end_date": "2025-01-02",
            "run_day_count": 2,
            "run_shape_class": "short_alert_run",
            "logistic_v3_discovery_score": 0.995,
            "electrical_core_minus_broadshape_050": 12.0,
            "future_confirmed_fault_30d": 1,
            "future_critical_fault_30d": 0,
            "future_final_fault_30d": 1,
            "future_confirmed_fault_60d": 1,
            "future_critical_fault_60d": 0,
            "future_final_fault_60d": 1,
            "future_truth_overlap_30d": 0,
            "future_truth_overlap_60d": 0,
            "future_truth_case_ids": "",
            "future_truth_candidate_validities": "",
            "recurring_run_within_30d": 0,
            "recurring_run_within_60d": 0,
            "future_run_count_60d": 0,
            "discovery_fate_class": "future_fault_linked",
            "discovery_fate_reason_ko": "pos",
            "ae_mid_or_hi_early_day_ratio": 0.0,
            "p95_recon_error": 0.003,
            "max_v_drop": 0.80,
            "min_mid_ratio": 0.20,
        },
        {
            "site": "alpha",
            "panel_id": "pos.b",
            "run_start_date": "2025-01-05",
            "run_end_date": "2025-01-08",
            "run_day_count": 4,
            "run_shape_class": "medium_alert_run",
            "logistic_v3_discovery_score": 0.985,
            "electrical_core_minus_broadshape_050": 10.0,
            "future_confirmed_fault_30d": 1,
            "future_critical_fault_30d": 0,
            "future_final_fault_30d": 1,
            "future_confirmed_fault_60d": 1,
            "future_critical_fault_60d": 0,
            "future_final_fault_60d": 1,
            "future_truth_overlap_30d": 0,
            "future_truth_overlap_60d": 0,
            "future_truth_case_ids": "",
            "future_truth_candidate_validities": "",
            "recurring_run_within_30d": 0,
            "recurring_run_within_60d": 0,
            "future_run_count_60d": 0,
            "discovery_fate_class": "future_fault_linked",
            "discovery_fate_reason_ko": "pos",
            "ae_mid_or_hi_early_day_ratio": 0.0,
            "p95_recon_error": 0.008,
            "max_v_drop": 0.70,
            "min_mid_ratio": 0.30,
        },
        {
            "site": "beta",
            "panel_id": "pos.c",
            "run_start_date": "2025-02-01",
            "run_end_date": "2025-02-03",
            "run_day_count": 3,
            "run_shape_class": "medium_alert_run",
            "logistic_v3_discovery_score": 0.960,
            "electrical_core_minus_broadshape_050": 8.0,
            "future_confirmed_fault_30d": 1,
            "future_critical_fault_30d": 0,
            "future_final_fault_30d": 1,
            "future_confirmed_fault_60d": 1,
            "future_critical_fault_60d": 0,
            "future_final_fault_60d": 1,
            "future_truth_overlap_30d": 0,
            "future_truth_overlap_60d": 0,
            "future_truth_case_ids": "",
            "future_truth_candidate_validities": "",
            "recurring_run_within_30d": 0,
            "recurring_run_within_60d": 0,
            "future_run_count_60d": 0,
            "discovery_fate_class": "future_fault_linked",
            "discovery_fate_reason_ko": "pos",
            "ae_mid_or_hi_early_day_ratio": 0.25,
            "p95_recon_error": 0.015,
            "max_v_drop": 0.60,
            "min_mid_ratio": 0.35,
        },
        {
            "site": "beta",
            "panel_id": "rec.a",
            "run_start_date": "2025-02-10",
            "run_end_date": "2025-02-11",
            "run_day_count": 2,
            "run_shape_class": "short_alert_run",
            "logistic_v3_discovery_score": 0.980,
            "electrical_core_minus_broadshape_050": 9.0,
            "future_confirmed_fault_30d": 0,
            "future_critical_fault_30d": 0,
            "future_final_fault_30d": 0,
            "future_confirmed_fault_60d": 0,
            "future_critical_fault_60d": 0,
            "future_final_fault_60d": 0,
            "future_truth_overlap_30d": 0,
            "future_truth_overlap_60d": 0,
            "future_truth_case_ids": "",
            "future_truth_candidate_validities": "",
            "recurring_run_within_30d": 1,
            "recurring_run_within_60d": 1,
            "future_run_count_60d": 2,
            "discovery_fate_class": "recurring_monitor_like",
            "discovery_fate_reason_ko": "rec",
            "ae_mid_or_hi_early_day_ratio": 0.75,
            "p95_recon_error": 0.040,
            "max_v_drop": 0.35,
            "min_mid_ratio": 0.75,
        },
        {
            "site": "gamma",
            "panel_id": "rec.b",
            "run_start_date": "2025-03-01",
            "run_end_date": "2025-03-05",
            "run_day_count": 5,
            "run_shape_class": "medium_alert_run",
            "logistic_v3_discovery_score": 0.940,
            "electrical_core_minus_broadshape_050": 7.0,
            "future_confirmed_fault_30d": 0,
            "future_critical_fault_30d": 0,
            "future_final_fault_30d": 0,
            "future_confirmed_fault_60d": 0,
            "future_critical_fault_60d": 0,
            "future_final_fault_60d": 0,
            "future_truth_overlap_30d": 0,
            "future_truth_overlap_60d": 0,
            "future_truth_case_ids": "",
            "future_truth_candidate_validities": "",
            "recurring_run_within_30d": 1,
            "recurring_run_within_60d": 1,
            "future_run_count_60d": 3,
            "discovery_fate_class": "recurring_monitor_like",
            "discovery_fate_reason_ko": "rec",
            "ae_mid_or_hi_early_day_ratio": 0.50,
            "p95_recon_error": 0.020,
            "max_v_drop": 0.30,
            "min_mid_ratio": 0.70,
        },
        {
            "site": "gamma",
            "panel_id": "iso.a",
            "run_start_date": "2025-03-10",
            "run_end_date": "2025-03-10",
            "run_day_count": 1,
            "run_shape_class": "short_alert_run",
            "logistic_v3_discovery_score": 0.920,
            "electrical_core_minus_broadshape_050": 5.0,
            "future_confirmed_fault_30d": 0,
            "future_critical_fault_30d": 0,
            "future_final_fault_30d": 0,
            "future_confirmed_fault_60d": 0,
            "future_critical_fault_60d": 0,
            "future_final_fault_60d": 0,
            "future_truth_overlap_30d": 0,
            "future_truth_overlap_60d": 0,
            "future_truth_case_ids": "",
            "future_truth_candidate_validities": "",
            "recurring_run_within_30d": 0,
            "recurring_run_within_60d": 0,
            "future_run_count_60d": 0,
            "discovery_fate_class": "isolated_unexplained",
            "discovery_fate_reason_ko": "iso",
            "ae_mid_or_hi_early_day_ratio": 0.50,
            "p95_recon_error": 0.070,
            "max_v_drop": 0.20,
            "min_mid_ratio": 0.80,
        },
    ]
    separability_rows = [
        {
            "record_type": "comparison_summary",
            "feature_name": "electrical_core_minus_broadshape_050",
            "lhs_group": "future_fault_linked",
            "rhs_group": "recurring_monitor_like",
            "normalized_gap": 1.4,
        },
        {
            "record_type": "comparison_summary",
            "feature_name": "logistic_v3_discovery_score",
            "lhs_group": "future_fault_linked",
            "rhs_group": "recurring_monitor_like",
            "normalized_gap": 1.1,
        },
    ]

    write_csv(share_dir / "panel_day_engine_operator_secondary_discovery_fate_cases_v1.csv", fate_rows, FATE_COLS)
    write_csv(share_dir / "panel_day_engine_operator_secondary_discovery_separability_summary_v1.csv", separability_rows, SEPARABILITY_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research" / "prognostics" / "build_panel_day_engine_operator_secondary_discovery_threshold_split_audit_v1.py"

    py_compile.compile(str(repo_root / "pv_ae" / "panel_day_engine.py"), doraise=True)
    py_compile.compile(str(builder), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="secondary-discovery-threshold-split-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        result = run([sys.executable, str(builder), "--root", str(tmp_root)], cwd=repo_root)
        if result.returncode != 0:
            raise SystemExit(f"builder failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        summary_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_threshold_split_summary_v1.csv"
        cases_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_threshold_split_cases_v1.csv"
        recommendation_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_threshold_split_recommendation_v1.csv"
        assert_true(summary_path.exists(), "missing threshold split summary output")
        assert_true(cases_path.exists(), "missing threshold split case output")
        assert_true(recommendation_path.exists(), "missing threshold split recommendation output")

        summary_df = pd.read_csv(summary_path, encoding="utf-8-sig")
        cases_df = pd.read_csv(cases_path, encoding="utf-8-sig")
        recommendation_df = pd.read_csv(recommendation_path, encoding="utf-8-sig")

        target_row = summary_df.loc[
            summary_df["rule_family"].astype(str).eq("electrical_and_low_ae")
            & summary_df["threshold_spec"].astype(str).eq("electrical_core_minus_broadshape_050>=8|ae_mid_or_hi_early_day_ratio<=0.25")
        ].iloc[0]
        assert_true(int(target_row["selected_count"]) == 3, "target rule should select three runs")
        assert_true(int(target_row["positive_count"]) == 3, "target rule should capture all positives")
        assert_true(int(target_row["recurring_count"]) == 0, "target rule should avoid recurring contamination")
        assert_true(int(target_row["isolated_count"]) == 0, "target rule should avoid isolated contamination")
        assert_true(float(target_row["positive_capture_rate"]) == 1.0, "positive capture rate should be correct")
        assert_true(float(target_row["precision_minus_all_negative"]) == 1.0, "precision-minus-all-negative should be correct")

        selected_target_cases = cases_df.loc[
            cases_df["rule_family"].astype(str).eq("electrical_and_low_ae")
            & cases_df["threshold_spec"].astype(str).eq("electrical_core_minus_broadshape_050>=8|ae_mid_or_hi_early_day_ratio<=0.25")
        ]
        assert_true(len(selected_target_cases) == 3, "case output should include selected rows for the target rule")

        recommendation = recommendation_df.iloc[0]
        assert_true(
            str(recommendation["recommended_next_direction"]) == "split_secondary_discovery_into_value_vs_monitor",
            "recommendation should promote a split when the best rule is strong enough",
        )
        assert_true(
            "electrical_and_low_ae" in str(recommendation["recommended_split_rule"]),
            "recommended rule should name the winning threshold split",
        )

    print("smoke_test_panel_day_engine_operator_secondary_discovery_threshold_split_audit_v1.py: PASS")


if __name__ == "__main__":
    main()
