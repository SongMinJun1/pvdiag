#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

import build_panel_day_engine_operator_discovery_preview_policy_audit_v1 as builder_mod

VALUE_PANEL_COLS = [
    "site",
    "panel_id",
    "representative_electrical_core_minus_broadshape_050",
    "any_future_fault_linked_ref_flag",
    "any_future_truth_linked_ref_flag",
]

PREVIEW_SUMMARY_COLS = [
    "record_type",
    "secondary_value_panel_count",
    "secondary_incremental_fault_or_truth_linked_panel_count",
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
    value_rows = [
        {
            "site": "alpha",
            "panel_id": "a1",
            "representative_electrical_core_minus_broadshape_050": 14.0,
            "any_future_fault_linked_ref_flag": 1,
            "any_future_truth_linked_ref_flag": 0,
        },
        {
            "site": "alpha",
            "panel_id": "a2",
            "representative_electrical_core_minus_broadshape_050": 11.0,
            "any_future_fault_linked_ref_flag": 1,
            "any_future_truth_linked_ref_flag": 0,
        },
        {
            "site": "alpha",
            "panel_id": "a3",
            "representative_electrical_core_minus_broadshape_050": 8.0,
            "any_future_fault_linked_ref_flag": 0,
            "any_future_truth_linked_ref_flag": 0,
        },
        {
            "site": "beta",
            "panel_id": "b1",
            "representative_electrical_core_minus_broadshape_050": 13.0,
            "any_future_fault_linked_ref_flag": 1,
            "any_future_truth_linked_ref_flag": 0,
        },
        {
            "site": "beta",
            "panel_id": "b2",
            "representative_electrical_core_minus_broadshape_050": 9.0,
            "any_future_fault_linked_ref_flag": 0,
            "any_future_truth_linked_ref_flag": 0,
        },
        {
            "site": "gamma",
            "panel_id": "c1",
            "representative_electrical_core_minus_broadshape_050": 9.0,
            "any_future_fault_linked_ref_flag": 1,
            "any_future_truth_linked_ref_flag": 0,
        },
    ]
    preview_rows = [
        {
            "record_type": "overall",
            "secondary_value_panel_count": 6,
            "secondary_incremental_fault_or_truth_linked_panel_count": 4,
        }
    ]
    write_csv(share_dir / "panel_day_engine_operator_secondary_discovery_value_panels_v1.csv", value_rows, VALUE_PANEL_COLS)
    write_csv(
        share_dir / "panel_day_engine_operator_attention_plus_discovery_preview_summary_v1.csv",
        preview_rows,
        PREVIEW_SUMMARY_COLS,
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
    builder = repo_root / "research" / "prognostics" / "build_panel_day_engine_operator_discovery_preview_policy_audit_v1.py"

    py_compile.compile(str(repo_root / "pv_ae" / "panel_day_engine.py"), doraise=True)
    py_compile.compile(str(builder), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="operator-discovery-preview-policy-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        result = run([sys.executable, str(builder), "--root", str(tmp_root)], cwd=repo_root)
        if result.returncode != 0:
            raise SystemExit(f"builder failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        sweep_path = tmp_root / "_share" / "panel_day_engine_operator_discovery_preview_policy_sweep_v1.csv"
        summary_path = tmp_root / "_share" / "panel_day_engine_operator_discovery_preview_policy_summary_v1.csv"
        recommendation_path = tmp_root / "_share" / "panel_day_engine_operator_discovery_preview_policy_recommendation_v1.csv"
        assert_true(sweep_path.exists(), "missing policy sweep output")
        assert_true(summary_path.exists(), "missing policy summary output")
        assert_true(recommendation_path.exists(), "missing policy recommendation output")

        observed_sweep = pd.read_csv(sweep_path, encoding="utf-8-sig")
        observed_summary = pd.read_csv(summary_path, encoding="utf-8-sig")
        observed_recommendation = pd.read_csv(recommendation_path, encoding="utf-8-sig")

        value_df = builder_mod.load_value_panels(tmp_root)
        preview_context = builder_mod.load_preview_context(tmp_root)
        expected_sweep, expected_summary, expected_recommendation = builder_mod.build_outputs(value_df, preview_context)

        assert_true(
            normalize_df_for_compare(observed_sweep.loc[:, builder_mod.SWEEP_COLS]).equals(
                normalize_df_for_compare(expected_sweep.loc[:, builder_mod.SWEEP_COLS])
            ),
            "policy sweep output does not match expected policy evaluation",
        )
        assert_true(
            normalize_df_for_compare(observed_summary.loc[:, builder_mod.SUMMARY_COLS]).equals(
                normalize_df_for_compare(expected_summary.loc[:, builder_mod.SUMMARY_COLS])
            ),
            "policy summary output does not match expected recommended flagging",
        )
        assert_true(
            normalize_df_for_compare(observed_recommendation.loc[:, builder_mod.RECOMMENDATION_COLS]).equals(
                normalize_df_for_compare(expected_recommendation.loc[:, builder_mod.RECOMMENDATION_COLS])
            ),
            "policy recommendation output does not match expected heuristic choice",
        )

        threshold_10 = observed_sweep.loc[
            observed_sweep["policy_family"].astype(str).eq("score_threshold")
            & observed_sweep["policy_spec"].astype(str).eq(f"{builder_mod.SCORE_COL}>=10")
        ].iloc[0]
        assert_true(int(threshold_10["selected_panel_count"]) == 3, "score_threshold>=10 selected count mismatch")
        assert_true(int(threshold_10["selected_fault_or_truth_linked_panel_count"]) == 3, "score_threshold>=10 linked count mismatch")

        top1 = observed_sweep.loc[
            observed_sweep["policy_family"].astype(str).eq("topk_per_site")
            & observed_sweep["policy_spec"].astype(str).eq(f"top_1_per_site_by_{builder_mod.SCORE_COL}")
        ].iloc[0]
        assert_true(int(top1["selected_panel_count"]) == 3, "topk_per_site K=1 selected count mismatch")
        assert_true(abs(float(top1["capture_rate_over_all_secondary_linked_panels"]) - 0.75) < 1e-9, "topk_per_site K=1 capture mismatch")

        combined = observed_sweep.loc[
            observed_sweep["policy_family"].astype(str).eq("threshold_plus_topk_per_site")
            & observed_sweep["policy_spec"].astype(str).eq(f"{builder_mod.SCORE_COL}>=10&top_1_per_site_by_{builder_mod.SCORE_COL}")
        ].iloc[0]
        assert_true(int(combined["selected_panel_count"]) == 2, "combined policy selected count mismatch")
        assert_true(int(combined["selected_fault_or_truth_linked_panel_count"]) == 2, "combined policy linked count mismatch")

        assert_true(int(observed_summary["recommended_policy_flag"].sum()) == 1, "exactly one policy should be recommended")
        recommendation_row = observed_recommendation.iloc[0]
        assert_true(
            str(recommendation_row["recommended_policy_name"]) == f"topk_per_site|top_1_per_site_by_{builder_mod.SCORE_COL}",
            "recommendation heuristic should choose topk_per_site K=1 for synthetic data",
        )

    print("smoke_test_panel_day_engine_operator_discovery_preview_policy_audit_v1.py: PASS")


if __name__ == "__main__":
    main()
