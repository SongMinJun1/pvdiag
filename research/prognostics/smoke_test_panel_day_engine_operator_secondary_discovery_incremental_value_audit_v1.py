#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

import build_panel_day_engine_operator_secondary_discovery_incremental_value_audit_v1 as builder_mod

ATTENTION_COLS = [
    "site",
    "panel_id",
    "attention_any_future_fault_linked_ref_flag",
    "attention_any_future_truth_linked_ref_flag",
]
SECONDARY_COLS = [
    "site",
    "panel_id",
    "any_future_fault_linked_ref_flag",
    "any_future_truth_linked_ref_flag",
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
    attention_rows = [
        {
            "site": "alpha",
            "panel_id": "a1",
            "attention_any_future_fault_linked_ref_flag": 1,
            "attention_any_future_truth_linked_ref_flag": 0,
        },
        {
            "site": "alpha",
            "panel_id": "a1",
            "attention_any_future_fault_linked_ref_flag": 0,
            "attention_any_future_truth_linked_ref_flag": 0,
        },
        {
            "site": "alpha",
            "panel_id": "shared",
            "attention_any_future_fault_linked_ref_flag": 0,
            "attention_any_future_truth_linked_ref_flag": 1,
        },
        {
            "site": "beta",
            "panel_id": "b1",
            "attention_any_future_fault_linked_ref_flag": 0,
            "attention_any_future_truth_linked_ref_flag": 0,
        },
    ]
    secondary_rows = [
        {
            "site": "alpha",
            "panel_id": "shared",
            "any_future_fault_linked_ref_flag": 0,
            "any_future_truth_linked_ref_flag": 0,
        },
        {
            "site": "alpha",
            "panel_id": "sec_fault",
            "any_future_fault_linked_ref_flag": 1,
            "any_future_truth_linked_ref_flag": 0,
        },
        {
            "site": "beta",
            "panel_id": "b1",
            "any_future_fault_linked_ref_flag": 1,
            "any_future_truth_linked_ref_flag": 0,
        },
        {
            "site": "beta",
            "panel_id": "b1",
            "any_future_fault_linked_ref_flag": 0,
            "any_future_truth_linked_ref_flag": 0,
        },
        {
            "site": "beta",
            "panel_id": "sec_truth",
            "any_future_fault_linked_ref_flag": 0,
            "any_future_truth_linked_ref_flag": 1,
        },
        {
            "site": "beta",
            "panel_id": "sec_noise",
            "any_future_fault_linked_ref_flag": 0,
            "any_future_truth_linked_ref_flag": 0,
        },
    ]
    write_csv(share_dir / "panel_day_engine_operator_attention_now_v1.csv", attention_rows, ATTENTION_COLS)
    write_csv(
        share_dir / "panel_day_engine_operator_secondary_discovery_value_panels_v1.csv",
        secondary_rows,
        SECONDARY_COLS,
    )


def normalize_df_for_compare(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            out[col] = pd.to_numeric(out[col], errors="coerce").round(10)
        else:
            out[col] = out[col].fillna("").astype(str)
    return out


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research" / "prognostics" / "build_panel_day_engine_operator_secondary_discovery_incremental_value_audit_v1.py"

    py_compile.compile(str(repo_root / "pv_ae" / "panel_day_engine.py"), doraise=True)
    py_compile.compile(str(builder), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="secondary-discovery-incremental-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        result = run([sys.executable, str(builder), "--root", str(tmp_root)], cwd=repo_root)
        if result.returncode != 0:
            raise SystemExit(f"builder failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        cases_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_incremental_value_cases_v1.csv"
        summary_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_incremental_value_summary_v1.csv"
        assert_true(cases_path.exists(), "missing incremental value cases output")
        assert_true(summary_path.exists(), "missing incremental value summary output")

        observed_cases = pd.read_csv(cases_path, encoding="utf-8-sig")
        observed_summary = pd.read_csv(summary_path, encoding="utf-8-sig")

        baseline_df = builder_mod.load_baseline_attention(tmp_root)
        secondary_df = builder_mod.load_secondary_value_panels(tmp_root)
        expected_case_df = builder_mod.build_case_table(baseline_df, secondary_df)
        expected_summary_df = builder_mod.build_summary(expected_case_df)

        assert_true(
            normalize_df_for_compare(observed_cases.loc[:, builder_mod.CASE_OUTPUT_COLS]).equals(
                normalize_df_for_compare(expected_case_df.loc[:, builder_mod.CASE_OUTPUT_COLS])
            ),
            "case output does not match expected panel union classification",
        )
        assert_true(
            normalize_df_for_compare(observed_summary.loc[:, builder_mod.SUMMARY_COLS]).equals(
                normalize_df_for_compare(expected_summary_df.loc[:, builder_mod.SUMMARY_COLS])
            ),
            "summary output does not match expected incremental value counts",
        )

        assert_true(
            set(observed_cases["panel_set_class"]) == {"baseline_only", "secondary_only", "in_both"},
            "panel_set_class should cover the three required classes in synthetic data",
        )

        alpha_a1 = observed_cases.loc[
            observed_cases["site"].astype(str).eq("alpha") & observed_cases["panel_id"].astype(str).eq("a1")
        ].iloc[0]
        assert_true(str(alpha_a1["panel_set_class"]) == "baseline_only", "alpha/a1 should be baseline_only")
        assert_true(int(alpha_a1["incremental_value_flag"]) == 0, "baseline_only panel cannot be incremental")

        alpha_shared = observed_cases.loc[
            observed_cases["site"].astype(str).eq("alpha") & observed_cases["panel_id"].astype(str).eq("shared")
        ].iloc[0]
        assert_true(str(alpha_shared["panel_set_class"]) == "in_both", "alpha/shared should be in_both")
        assert_true(int(alpha_shared["future_truth_linked_ref_flag"]) == 1, "alpha/shared should inherit truth ref from baseline")
        assert_true(int(alpha_shared["incremental_value_flag"]) == 0, "in_both panel cannot be incremental")

        beta_b1 = observed_cases.loc[
            observed_cases["site"].astype(str).eq("beta") & observed_cases["panel_id"].astype(str).eq("b1")
        ].iloc[0]
        assert_true(str(beta_b1["panel_set_class"]) == "in_both", "beta/b1 should be in_both")
        assert_true(int(beta_b1["future_fault_linked_ref_flag"]) == 1, "beta/b1 should inherit fault ref from secondary lane")
        assert_true(int(beta_b1["incremental_value_flag"]) == 0, "in_both panel cannot be incremental even if future-linked")

        beta_sec_truth = observed_cases.loc[
            observed_cases["site"].astype(str).eq("beta") & observed_cases["panel_id"].astype(str).eq("sec_truth")
        ].iloc[0]
        assert_true(str(beta_sec_truth["panel_set_class"]) == "secondary_only", "beta/sec_truth should be secondary_only")
        assert_true(int(beta_sec_truth["incremental_value_flag"]) == 1, "secondary_only future-linked panel should be incremental")

        overall_row = observed_summary.loc[observed_summary["record_type"].astype(str).eq("overall")].iloc[0]
        assert_true(int(overall_row["baseline_panel_count"]) == 3, "overall baseline_panel_count mismatch")
        assert_true(int(overall_row["secondary_value_panel_count"]) == 5, "overall secondary_value_panel_count mismatch")
        assert_true(int(overall_row["union_panel_count"]) == 6, "overall union_panel_count mismatch")
        assert_true(int(overall_row["overlap_panel_count"]) == 2, "overall overlap_panel_count mismatch")
        assert_true(
            int(overall_row["incremental_fault_or_truth_linked_panel_count"]) == 2,
            "overall incremental linked panel count mismatch",
        )
        assert_true(
            abs(float(overall_row["incremental_fault_or_truth_linked_panel_rate_over_secondary"]) - 0.4) < 1e-9,
            "overall incremental rate over secondary mismatch",
        )
        assert_true(
            abs(float(overall_row["incremental_fault_or_truth_linked_panel_rate_over_union"]) - (2.0 / 6.0)) < 1e-9,
            "overall incremental rate over union mismatch",
        )

    print("smoke_test_panel_day_engine_operator_secondary_discovery_incremental_value_audit_v1.py: PASS")


if __name__ == "__main__":
    main()
