#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

import build_panel_day_engine_operator_attention_plus_discovery_preview_v1 as builder_mod

ATTENTION_COLS = [
    "attention_class",
    "site",
    "panel_id",
    "display_start_date",
    "display_end_date",
    "display_day_count",
    "display_shape_class",
    "display_status_or_tier",
    "clipped_operator_score",
    "raw_operator_score",
    "overlap_case_class",
    "attention_any_future_fault_linked_ref_flag",
    "attention_any_future_truth_linked_ref_flag",
    "attention_reason_ko",
]

SECONDARY_COLS = [
    "site",
    "panel_id",
    "representative_run_start_date",
    "representative_run_end_date",
    "representative_run_day_count",
    "representative_run_shape_class",
    "representative_electrical_core_minus_broadshape_050",
    "representative_logistic_v3_discovery_score",
    "value_run_count_for_panel",
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


def build_fixture_root(tmp_root: Path) -> None:
    share_dir = tmp_root / "_share"
    attention_rows = [
        {
            "attention_class": "queue_run",
            "site": "alpha",
            "panel_id": "alpha.queue",
            "display_start_date": "2026-01-01",
            "display_end_date": "2026-01-02",
            "display_day_count": 2,
            "display_shape_class": "medium_alert_run",
            "display_status_or_tier": "ongoing_run",
            "clipped_operator_score": 8.5,
            "raw_operator_score": 8.5,
            "overlap_case_class": "unmatched_to_review",
            "attention_any_future_fault_linked_ref_flag": 1,
            "attention_any_future_truth_linked_ref_flag": 0,
            "attention_reason_ko": "baseline queue row",
        },
        {
            "attention_class": "watch_now_panel",
            "site": "alpha",
            "panel_id": "alpha.watch",
            "display_start_date": "2026-01-03",
            "display_end_date": "2026-01-04",
            "display_day_count": 2,
            "display_shape_class": "short_alert_run",
            "display_status_or_tier": "watch_now",
            "clipped_operator_score": 6.0,
            "raw_operator_score": 6.0,
            "overlap_case_class": "watch_now_overlap",
            "attention_any_future_fault_linked_ref_flag": 0,
            "attention_any_future_truth_linked_ref_flag": 1,
            "attention_reason_ko": "baseline watch row",
        },
        {
            "attention_class": "queue_run",
            "site": "beta",
            "panel_id": "beta.overlap",
            "display_start_date": "2026-01-05",
            "display_end_date": "2026-01-06",
            "display_day_count": 2,
            "display_shape_class": "short_alert_run",
            "display_status_or_tier": "ongoing_run",
            "clipped_operator_score": 7.0,
            "raw_operator_score": 7.0,
            "overlap_case_class": "unmatched_to_review",
            "attention_any_future_fault_linked_ref_flag": 0,
            "attention_any_future_truth_linked_ref_flag": 0,
            "attention_reason_ko": "baseline overlap row",
        },
    ]
    secondary_rows = [
        {
            "site": "beta",
            "panel_id": "beta.overlap",
            "representative_run_start_date": "2026-01-07",
            "representative_run_end_date": "2026-01-07",
            "representative_run_day_count": 1,
            "representative_run_shape_class": "short_alert_run",
            "representative_electrical_core_minus_broadshape_050": 9.5,
            "representative_logistic_v3_discovery_score": 0.99,
            "value_run_count_for_panel": 2,
            "any_future_fault_linked_ref_flag": 1,
            "any_future_truth_linked_ref_flag": 0,
            "value_panel_reason_ko": "overlap should be suppressed",
        },
        {
            "site": "beta",
            "panel_id": "beta.new",
            "representative_run_start_date": "2026-01-08",
            "representative_run_end_date": "2026-01-09",
            "representative_run_day_count": 2,
            "representative_run_shape_class": "medium_alert_run",
            "representative_electrical_core_minus_broadshape_050": 9.0,
            "representative_logistic_v3_discovery_score": 0.97,
            "value_run_count_for_panel": 1,
            "any_future_fault_linked_ref_flag": 1,
            "any_future_truth_linked_ref_flag": 0,
            "value_panel_reason_ko": "incremental hidden value",
        },
        {
            "site": "gamma",
            "panel_id": "gamma.new",
            "representative_run_start_date": "2026-01-10",
            "representative_run_end_date": "2026-01-12",
            "representative_run_day_count": 3,
            "representative_run_shape_class": "chronic_alert_run",
            "representative_electrical_core_minus_broadshape_050": 4.0,
            "representative_logistic_v3_discovery_score": 0.80,
            "value_run_count_for_panel": 1,
            "any_future_fault_linked_ref_flag": 0,
            "any_future_truth_linked_ref_flag": 0,
            "value_panel_reason_ko": "non-overlap low retrospective value",
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
    builder = repo_root / "research" / "prognostics" / "build_panel_day_engine_operator_attention_plus_discovery_preview_v1.py"

    py_compile.compile(str(repo_root / "pv_ae" / "panel_day_engine.py"), doraise=True)
    py_compile.compile(str(builder), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="attention-plus-discovery-preview-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        result = run([sys.executable, str(builder), "--root", str(tmp_root)], cwd=repo_root)
        if result.returncode != 0:
            raise SystemExit(f"builder failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        preview_path = tmp_root / "_share" / "panel_day_engine_operator_attention_plus_discovery_preview_v1.csv"
        summary_path = tmp_root / "_share" / "panel_day_engine_operator_attention_plus_discovery_preview_summary_v1.csv"
        assert_true(preview_path.exists(), "missing preview output")
        assert_true(summary_path.exists(), "missing preview summary output")

        observed_preview = pd.read_csv(preview_path, encoding="utf-8-sig")
        observed_summary = pd.read_csv(summary_path, encoding="utf-8-sig")

        baseline_df = builder_mod.load_baseline_attention(tmp_root)
        secondary_df = builder_mod.load_secondary_value_panels(tmp_root)
        expected_preview, secondary_enriched_df = builder_mod.build_preview(baseline_df, secondary_df)
        expected_summary = builder_mod.build_summary(expected_preview, baseline_df, secondary_enriched_df)

        assert_true(
            normalize_df_for_compare(observed_preview.loc[:, builder_mod.PREVIEW_COLS]).equals(
                normalize_df_for_compare(expected_preview.loc[:, builder_mod.PREVIEW_COLS])
            ),
            "preview output does not match expected baseline + non-overlap discovery append",
        )
        assert_true(
            normalize_df_for_compare(observed_summary.loc[:, builder_mod.SUMMARY_COLS]).equals(
                normalize_df_for_compare(expected_summary.loc[:, builder_mod.SUMMARY_COLS])
            ),
            "preview summary does not match expected counts",
        )

        baseline_keys = set(map(tuple, baseline_df.loc[:, ["site", "panel_id"]].itertuples(index=False, name=None)))
        observed_keys = list(map(tuple, observed_preview.loc[:, ["site", "panel_id"]].itertuples(index=False, name=None)))
        for key in baseline_keys:
            assert_true(key in observed_keys, f"baseline row {key} should be preserved")

        assert_true(observed_keys.count(("beta", "beta.overlap")) == 1, "overlapping panel should not be duplicated")
        assert_true(("beta", "beta.new") in observed_keys, "non-overlapping secondary panel should be appended")
        assert_true(("gamma", "gamma.new") in observed_keys, "second non-overlapping secondary panel should be appended")

        beta_new_row = observed_preview.loc[
            observed_preview["site"].astype(str).eq("beta") & observed_preview["panel_id"].astype(str).eq("beta.new")
        ].iloc[0]
        assert_true(
            str(beta_new_row["preview_attention_class"]) == "secondary_value_panel",
            "appended secondary row should use secondary_value_panel class",
        )

        overall_row = observed_summary.loc[observed_summary["record_type"].astype(str).eq("overall")].iloc[0]
        assert_true(int(overall_row["preview_attention_count"]) == 5, "overall preview count mismatch")
        assert_true(int(overall_row["queue_run_count"]) == 2, "overall queue_run_count mismatch")
        assert_true(int(overall_row["watch_now_panel_count"]) == 1, "overall watch_now_panel_count mismatch")
        assert_true(int(overall_row["secondary_value_panel_count"]) == 2, "overall secondary_value_panel_count mismatch")
        assert_true(int(overall_row["overlap_panel_count"]) == 1, "overall overlap_panel_count mismatch")
        assert_true(
            int(overall_row["secondary_incremental_fault_or_truth_linked_panel_count"]) == 1,
            "overall secondary incremental linked panel count mismatch",
        )

    print("smoke_test_panel_day_engine_operator_attention_plus_discovery_preview_v1.py: PASS")


if __name__ == "__main__":
    main()
