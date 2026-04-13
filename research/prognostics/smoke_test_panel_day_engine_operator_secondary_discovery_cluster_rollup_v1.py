#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

import build_panel_day_engine_operator_secondary_discovery_cluster_rollup_v1 as builder_mod

VALUE_PANEL_COLS = [
    "site",
    "panel_id",
    "representative_run_start_date",
    "representative_run_end_date",
    "representative_run_day_count",
    "representative_run_shape_class",
    "representative_electrical_core_minus_broadshape_050",
    "representative_logistic_v3_discovery_score",
    "value_run_count_for_panel",
    "value_total_day_count_for_panel",
    "earliest_value_run_start_date",
    "latest_value_run_end_date",
    "max_electrical_core_minus_broadshape_050_for_panel",
    "max_logistic_v3_discovery_score_for_panel",
    "any_future_fault_linked_ref_flag",
    "any_future_truth_linked_ref_flag",
    "value_panel_reason_ko",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def normalize_df_for_compare(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            out[col] = pd.to_numeric(out[col], errors="coerce").round(10)
        else:
            out[col] = out[col].fillna("").astype(str)
    return out


def build_fixture_root(tmp_root: Path) -> None:
    rows = [
        {
            "site": "alpha",
            "panel_id": "alpha.p1",
            "representative_run_start_date": "2026-01-01",
            "representative_run_end_date": "2026-01-02",
            "representative_run_day_count": 2,
            "representative_run_shape_class": "medium_alert_run",
            "representative_electrical_core_minus_broadshape_050": 12.0,
            "representative_logistic_v3_discovery_score": 0.70,
            "value_run_count_for_panel": 1,
            "value_total_day_count_for_panel": 2,
            "earliest_value_run_start_date": "2026-01-01",
            "latest_value_run_end_date": "2026-01-02",
            "max_electrical_core_minus_broadshape_050_for_panel": 12.0,
            "max_logistic_v3_discovery_score_for_panel": 0.70,
            "any_future_fault_linked_ref_flag": 0,
            "any_future_truth_linked_ref_flag": 0,
            "value_panel_reason_ko": "fixture alpha p1",
        },
        {
            "site": "alpha",
            "panel_id": "alpha.p2",
            "representative_run_start_date": "2026-01-04",
            "representative_run_end_date": "2026-01-05",
            "representative_run_day_count": 2,
            "representative_run_shape_class": "medium_alert_run",
            "representative_electrical_core_minus_broadshape_050": 12.0,
            "representative_logistic_v3_discovery_score": 0.90,
            "value_run_count_for_panel": 1,
            "value_total_day_count_for_panel": 2,
            "earliest_value_run_start_date": "2026-01-04",
            "latest_value_run_end_date": "2026-01-05",
            "max_electrical_core_minus_broadshape_050_for_panel": 12.0,
            "max_logistic_v3_discovery_score_for_panel": 0.90,
            "any_future_fault_linked_ref_flag": 1,
            "any_future_truth_linked_ref_flag": 0,
            "value_panel_reason_ko": "fixture alpha p2",
        },
        {
            "site": "alpha",
            "panel_id": "alpha.p3",
            "representative_run_start_date": "2026-01-09",
            "representative_run_end_date": "2026-01-09",
            "representative_run_day_count": 1,
            "representative_run_shape_class": "short_alert_run",
            "representative_electrical_core_minus_broadshape_050": 12.0,
            "representative_logistic_v3_discovery_score": 0.80,
            "value_run_count_for_panel": 1,
            "value_total_day_count_for_panel": 1,
            "earliest_value_run_start_date": "2026-01-09",
            "latest_value_run_end_date": "2026-01-09",
            "max_electrical_core_minus_broadshape_050_for_panel": 12.0,
            "max_logistic_v3_discovery_score_for_panel": 0.80,
            "any_future_fault_linked_ref_flag": 0,
            "any_future_truth_linked_ref_flag": 1,
            "value_panel_reason_ko": "fixture alpha p3",
        },
        {
            "site": "beta",
            "panel_id": "beta.p1",
            "representative_run_start_date": "2026-02-10",
            "representative_run_end_date": "2026-02-11",
            "representative_run_day_count": 2,
            "representative_run_shape_class": "medium_alert_run",
            "representative_electrical_core_minus_broadshape_050": 14.0,
            "representative_logistic_v3_discovery_score": 0.50,
            "value_run_count_for_panel": 1,
            "value_total_day_count_for_panel": 2,
            "earliest_value_run_start_date": "2026-02-10",
            "latest_value_run_end_date": "2026-02-11",
            "max_electrical_core_minus_broadshape_050_for_panel": 14.0,
            "max_logistic_v3_discovery_score_for_panel": 0.50,
            "any_future_fault_linked_ref_flag": 0,
            "any_future_truth_linked_ref_flag": 0,
            "value_panel_reason_ko": "fixture beta p1",
        },
        {
            "site": "beta",
            "panel_id": "beta.p2",
            "representative_run_start_date": "2026-02-14",
            "representative_run_end_date": "2026-02-14",
            "representative_run_day_count": 1,
            "representative_run_shape_class": "short_alert_run",
            "representative_electrical_core_minus_broadshape_050": 14.0,
            "representative_logistic_v3_discovery_score": 0.50,
            "value_run_count_for_panel": 1,
            "value_total_day_count_for_panel": 1,
            "earliest_value_run_start_date": "2026-02-14",
            "latest_value_run_end_date": "2026-02-14",
            "max_electrical_core_minus_broadshape_050_for_panel": 14.0,
            "max_logistic_v3_discovery_score_for_panel": 0.50,
            "any_future_fault_linked_ref_flag": 1,
            "any_future_truth_linked_ref_flag": 1,
            "value_panel_reason_ko": "fixture beta p2",
        },
    ]
    write_csv(
        tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_value_panels_v1.csv",
        rows,
        VALUE_PANEL_COLS,
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research" / "prognostics" / "build_panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.py"

    py_compile.compile(str(repo_root / "pv_ae" / "panel_day_engine.py"), doraise=True)
    py_compile.compile(str(builder), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="secondary-discovery-cluster-rollup-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        result = run([sys.executable, str(builder), "--root", str(tmp_root)], cwd=repo_root)
        if result.returncode != 0:
            raise SystemExit(f"builder failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        rollup_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.csv"
        summary_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_cluster_rollup_summary_v1.csv"
        assert_true(rollup_path.exists(), "missing cluster rollup output")
        assert_true(summary_path.exists(), "missing cluster rollup summary output")

        observed_rollup = pd.read_csv(rollup_path, encoding="utf-8-sig")
        observed_summary = pd.read_csv(summary_path, encoding="utf-8-sig")

        value_panels_df = builder_mod.load_value_panels(tmp_root)
        expected_rollup = builder_mod.build_cluster_rollup(value_panels_df)
        expected_summary = builder_mod.build_summary(value_panels_df, expected_rollup)

        assert_true(
            normalize_df_for_compare(observed_rollup.loc[:, builder_mod.CLUSTER_COLS]).equals(
                normalize_df_for_compare(expected_rollup.loc[:, builder_mod.CLUSTER_COLS])
            ),
            "cluster rollup output does not match expected clustering",
        )
        assert_true(
            normalize_df_for_compare(observed_summary.loc[:, builder_mod.SUMMARY_COLS]).equals(
                normalize_df_for_compare(expected_summary.loc[:, builder_mod.SUMMARY_COLS])
            ),
            "cluster rollup summary does not match expected metrics",
        )

        assert_true(len(observed_rollup) == 3, "expected three site-time clusters")

        beta_cluster = observed_rollup.loc[observed_rollup["site"].astype(str).eq("beta")].iloc[0]
        assert_true(int(beta_cluster["panel_count"]) == 2, "beta rows within 3 days should cluster together")
        assert_true(str(beta_cluster["representative_panel_id"]) == "beta.p2", "beta representative selection priority failed")
        assert_true(int(beta_cluster["future_fault_linked_ref_panel_count"]) == 1, "beta fault-linked count mismatch")
        assert_true(int(beta_cluster["future_truth_linked_ref_panel_count"]) == 1, "beta truth-linked count mismatch")

        alpha_clusters = observed_rollup.loc[observed_rollup["site"].astype(str).eq("alpha")].copy()
        assert_true(len(alpha_clusters) == 2, "alpha rows farther than 3 days apart should not be merged")
        alpha_multi = alpha_clusters.loc[alpha_clusters["panel_count"].astype(int).eq(2)].iloc[0]
        assert_true(
            str(alpha_multi["representative_panel_id"]) == "alpha.p2",
            "alpha representative should prefer higher logistic score when electrical score ties",
        )
        assert_true(
            str(alpha_multi["panel_ids_csv"]) == "alpha.p1,alpha.p2",
            "alpha clustered panel ids mismatch",
        )

        overall_row = observed_summary.loc[observed_summary["record_type"].astype(str).eq("overall")].iloc[0]
        assert_true(int(overall_row["value_panel_count"]) == 5, "overall value panel count mismatch")
        assert_true(int(overall_row["cluster_count"]) == 3, "overall cluster count mismatch")
        assert_true(int(overall_row["panel_reduction_count"]) == 2, "overall panel reduction count mismatch")
        assert_true(abs(float(overall_row["panel_reduction_rate"]) - 0.4) < 1e-9, "overall panel reduction rate mismatch")
        assert_true(
            int(overall_row["clusters_with_future_fault_linked_ref_count"]) == 2,
            "overall future fault-linked cluster count mismatch",
        )
        assert_true(
            int(overall_row["clusters_with_future_truth_linked_ref_count"]) == 2,
            "overall future truth-linked cluster count mismatch",
        )
        assert_true(int(overall_row["max_panels_in_one_cluster"]) == 2, "overall max panels per cluster mismatch")
        assert_true(abs(float(overall_row["median_panels_per_cluster"]) - 2.0) < 1e-9, "overall median panels per cluster mismatch")

    print("smoke_test_panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.py: PASS")


if __name__ == "__main__":
    main()
