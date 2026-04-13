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

CLUSTER_ROLLUP_COLS = [
    "site",
    "cluster_id",
    "cluster_start_date",
    "cluster_end_date",
    "cluster_span_days",
    "panel_count",
    "panel_ids_csv",
    "representative_panel_id",
    "representative_run_start_date",
    "representative_run_end_date",
    "representative_run_day_count",
    "representative_electrical_core_minus_broadshape_050",
    "representative_logistic_v3_discovery_score",
    "max_electrical_core_minus_broadshape_050_in_cluster",
    "max_logistic_v3_discovery_score_in_cluster",
    "future_fault_linked_ref_panel_count",
    "future_truth_linked_ref_panel_count",
    "any_future_fault_linked_ref_flag",
    "any_future_truth_linked_ref_flag",
    "cluster_reason_ko",
]

POLICY_RECOMMENDATION_COLS = [
    "recommended_policy_name",
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
    write_csv(
        share_dir / "panel_day_engine_operator_discovery_preview_policy_recommendation_v1.csv",
        [{"recommended_policy_name": "score_threshold|representative_electrical_core_minus_broadshape_050>=9"}],
        POLICY_RECOMMENDATION_COLS,
    )
    write_csv(
        share_dir / "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.csv",
        [
            {
                "site": "alpha",
                "cluster_id": "alpha_cluster_001",
                "cluster_start_date": "2026-01-07",
                "cluster_end_date": "2026-01-10",
                "cluster_span_days": 4,
                "panel_count": 2,
                "panel_ids_csv": "alpha.queue,alpha.hidden",
                "representative_panel_id": "alpha.hidden",
                "representative_run_start_date": "2026-01-08",
                "representative_run_end_date": "2026-01-10",
                "representative_run_day_count": 3,
                "representative_electrical_core_minus_broadshape_050": 11.0,
                "representative_logistic_v3_discovery_score": 0.98,
                "max_electrical_core_minus_broadshape_050_in_cluster": 11.0,
                "max_logistic_v3_discovery_score_in_cluster": 0.98,
                "future_fault_linked_ref_panel_count": 1,
                "future_truth_linked_ref_panel_count": 0,
                "any_future_fault_linked_ref_flag": 1,
                "any_future_truth_linked_ref_flag": 0,
                "cluster_reason_ko": "fixture alpha cluster",
            },
            {
                "site": "beta",
                "cluster_id": "beta_cluster_001",
                "cluster_start_date": "2026-01-08",
                "cluster_end_date": "2026-01-09",
                "cluster_span_days": 2,
                "panel_count": 1,
                "panel_ids_csv": "beta.new",
                "representative_panel_id": "beta.new",
                "representative_run_start_date": "2026-01-08",
                "representative_run_end_date": "2026-01-09",
                "representative_run_day_count": 2,
                "representative_electrical_core_minus_broadshape_050": 9.0,
                "representative_logistic_v3_discovery_score": 0.97,
                "max_electrical_core_minus_broadshape_050_in_cluster": 9.0,
                "max_logistic_v3_discovery_score_in_cluster": 0.97,
                "future_fault_linked_ref_panel_count": 0,
                "future_truth_linked_ref_panel_count": 1,
                "any_future_fault_linked_ref_flag": 0,
                "any_future_truth_linked_ref_flag": 1,
                "cluster_reason_ko": "fixture beta cluster",
            },
        ],
        CLUSTER_ROLLUP_COLS,
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
        narrow_preview_path = tmp_root / "_share" / "panel_day_engine_operator_attention_plus_discovery_preview_narrow_v1.csv"
        narrow_summary_path = tmp_root / "_share" / "panel_day_engine_operator_attention_plus_discovery_preview_narrow_summary_v1.csv"
        cluster_preview_path = tmp_root / "_share" / "panel_day_engine_operator_attention_plus_discovery_cluster_preview_v1.csv"
        cluster_preview_summary_path = tmp_root / "_share" / "panel_day_engine_operator_attention_plus_discovery_cluster_preview_summary_v1.csv"
        assert_true(preview_path.exists(), "missing preview output")
        assert_true(summary_path.exists(), "missing preview summary output")
        assert_true(narrow_preview_path.exists(), "missing narrow preview output")
        assert_true(narrow_summary_path.exists(), "missing narrow preview summary output")
        assert_true(cluster_preview_path.exists(), "missing cluster preview output")
        assert_true(cluster_preview_summary_path.exists(), "missing cluster preview summary output")

        observed_preview = pd.read_csv(preview_path, encoding="utf-8-sig")
        observed_summary = pd.read_csv(summary_path, encoding="utf-8-sig")
        observed_narrow_preview = pd.read_csv(narrow_preview_path, encoding="utf-8-sig")
        observed_narrow_summary = pd.read_csv(narrow_summary_path, encoding="utf-8-sig")
        observed_cluster_preview = pd.read_csv(cluster_preview_path, encoding="utf-8-sig")
        observed_cluster_preview_summary = pd.read_csv(cluster_preview_summary_path, encoding="utf-8-sig")

        baseline_df = builder_mod.load_baseline_attention(tmp_root)
        secondary_source_df = builder_mod.load_secondary_value_panel_source(tmp_root)
        secondary_df = builder_mod.build_secondary_preview_rows(secondary_source_df)
        expected_preview, secondary_enriched_df = builder_mod.build_preview(baseline_df, secondary_df)
        expected_summary = builder_mod.build_summary(expected_preview, baseline_df, secondary_enriched_df)
        policy = builder_mod.load_policy_recommendation(tmp_root)
        narrow_source_df = builder_mod.select_policy_source_rows(secondary_source_df, policy)
        narrow_secondary_df = builder_mod.build_secondary_preview_rows(narrow_source_df)
        expected_narrow_preview, narrow_secondary_enriched_df = builder_mod.build_narrow_preview(
            baseline_df,
            narrow_secondary_df,
            str(policy["policy_name"]),
        )
        expected_narrow_summary = builder_mod.build_narrow_summary(
            expected_narrow_preview,
            baseline_df,
            narrow_secondary_enriched_df,
            str(policy["policy_name"]),
        )
        cluster_source_df = builder_mod.load_cluster_rollup_source(tmp_root)
        expected_cluster_preview, cluster_enriched_df = builder_mod.build_cluster_preview(baseline_df, cluster_source_df)
        expected_cluster_preview_summary = builder_mod.build_cluster_preview_summary(
            expected_cluster_preview,
            cluster_enriched_df,
        )

        assert_true(
            observed_preview.columns.tolist() == builder_mod.PREVIEW_COLS,
            "full preview schema should remain unchanged",
        )
        assert_true(
            observed_summary.columns.tolist() == builder_mod.SUMMARY_COLS,
            "full preview summary schema should remain unchanged",
        )
        assert_true(
            observed_narrow_preview.columns.tolist() == builder_mod.NARROW_PREVIEW_COLS,
            "narrow preview schema mismatch",
        )
        assert_true(
            observed_narrow_summary.columns.tolist() == builder_mod.NARROW_SUMMARY_COLS,
            "narrow preview summary schema mismatch",
        )
        assert_true(
            observed_cluster_preview.columns.tolist() == builder_mod.CLUSTER_PREVIEW_COLS,
            "cluster preview schema mismatch",
        )
        assert_true(
            observed_cluster_preview_summary.columns.tolist() == builder_mod.CLUSTER_PREVIEW_SUMMARY_COLS,
            "cluster preview summary schema mismatch",
        )

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
        assert_true(
            normalize_df_for_compare(observed_narrow_preview.loc[:, builder_mod.NARROW_PREVIEW_COLS]).equals(
                normalize_df_for_compare(expected_narrow_preview.loc[:, builder_mod.NARROW_PREVIEW_COLS])
            ),
            "narrow preview output does not match expected policy-filtered append",
        )
        assert_true(
            normalize_df_for_compare(observed_narrow_summary.loc[:, builder_mod.NARROW_SUMMARY_COLS]).equals(
                normalize_df_for_compare(expected_narrow_summary.loc[:, builder_mod.NARROW_SUMMARY_COLS])
            ),
            "narrow preview summary does not match expected policy-filtered counts",
        )
        assert_true(
            normalize_df_for_compare(observed_cluster_preview.loc[:, builder_mod.CLUSTER_PREVIEW_COLS]).equals(
                normalize_df_for_compare(expected_cluster_preview.loc[:, builder_mod.CLUSTER_PREVIEW_COLS])
            ),
            "cluster preview output does not match expected baseline + cluster append",
        )
        assert_true(
            normalize_df_for_compare(observed_cluster_preview_summary.loc[:, builder_mod.CLUSTER_PREVIEW_SUMMARY_COLS]).equals(
                normalize_df_for_compare(expected_cluster_preview_summary.loc[:, builder_mod.CLUSTER_PREVIEW_SUMMARY_COLS])
            ),
            "cluster preview summary does not match expected counts",
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

        parsed_score_policy = builder_mod.parse_policy_name(
            "score_threshold|representative_electrical_core_minus_broadshape_050>=9"
        )
        parsed_topk_policy = builder_mod.parse_policy_name(
            "topk_per_site|top_2_per_site_by_representative_electrical_core_minus_broadshape_050"
        )
        parsed_combined_policy = builder_mod.parse_policy_name(
            "threshold_plus_topk_per_site|representative_electrical_core_minus_broadshape_050>=10&top_3_per_site_by_representative_electrical_core_minus_broadshape_050"
        )
        assert_true(parsed_score_policy["policy_family"] == "score_threshold", "score_threshold policy parse failed")
        assert_true(int(parsed_topk_policy["top_k"]) == 2, "topk_per_site policy parse failed")
        assert_true(
            parsed_combined_policy["policy_family"] == "threshold_plus_topk_per_site",
            "threshold_plus_topk_per_site policy parse failed",
        )

        narrow_keys = list(
            map(tuple, observed_narrow_preview.loc[:, ["site", "panel_id"]].itertuples(index=False, name=None))
        )
        full_discovery_keys = set(
            map(
                tuple,
                observed_preview.loc[
                    observed_preview["preview_attention_class"].astype(str).eq("secondary_value_panel"),
                    ["site", "panel_id"],
                ].itertuples(index=False, name=None),
            )
        )
        narrow_discovery_keys = set(
            map(
                tuple,
                observed_narrow_preview.loc[
                    observed_narrow_preview["is_narrow_discovery_row_flag"].astype(int).eq(1),
                    ["site", "panel_id"],
                ].itertuples(index=False, name=None),
            )
        )
        assert_true(
            narrow_discovery_keys.issubset(full_discovery_keys),
            "narrowed discovery rows should be a subset of full preview discovery rows",
        )
        for key in baseline_keys:
            assert_true(key in narrow_keys, f"baseline row {key} should still be present in narrow preview")
        assert_true(("beta", "beta.new") in narrow_discovery_keys, "policy-selected discovery panel should be present")
        assert_true(("gamma", "gamma.new") not in narrow_discovery_keys, "below-threshold discovery panel should be excluded")
        assert_true(("beta", "beta.overlap") not in narrow_discovery_keys, "overlapping discovery panel should stay suppressed")

        beta_new_narrow_row = observed_narrow_preview.loc[
            observed_narrow_preview["site"].astype(str).eq("beta")
            & observed_narrow_preview["panel_id"].astype(str).eq("beta.new")
        ].iloc[0]
        assert_true(
            str(beta_new_narrow_row["preview_policy_name"])
            == "score_threshold|representative_electrical_core_minus_broadshape_050>=9",
            "narrow preview policy name mismatch",
        )
        assert_true(
            int(beta_new_narrow_row["is_narrow_discovery_row_flag"]) == 1,
            "narrow discovery row flag mismatch",
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

        narrow_overall_row = observed_narrow_summary.loc[
            observed_narrow_summary["record_type"].astype(str).eq("overall")
        ].iloc[0]
        assert_true(
            str(narrow_overall_row["preview_policy_name"])
            == "score_threshold|representative_electrical_core_minus_broadshape_050>=9",
            "overall narrow preview policy name mismatch",
        )
        assert_true(int(narrow_overall_row["narrow_preview_attention_count"]) == 4, "overall narrow preview count mismatch")
        assert_true(int(narrow_overall_row["queue_run_count"]) == 2, "overall narrow queue_run_count mismatch")
        assert_true(int(narrow_overall_row["watch_now_panel_count"]) == 1, "overall narrow watch_now_panel_count mismatch")
        assert_true(int(narrow_overall_row["secondary_value_panel_count"]) == 1, "overall narrow secondary count mismatch")
        assert_true(int(narrow_overall_row["overlap_panel_count"]) == 1, "overall narrow overlap count mismatch")
        assert_true(
            int(narrow_overall_row["narrow_incremental_fault_or_truth_linked_panel_count"]) == 1,
            "overall narrow incremental linked count mismatch",
        )
        assert_true(int(narrow_overall_row["narrow_selected_site_count"]) == 1, "overall narrow selected site count mismatch")
        assert_true(
            abs(float(narrow_overall_row["narrow_max_single_site_share"]) - 1.0) < 1e-9,
            "overall narrow max single site share mismatch",
        )

        cluster_preview_keys = list(
            map(
                tuple,
                observed_cluster_preview.loc[
                    observed_cluster_preview["preview_attention_class"].astype(str).isin(["queue_run", "watch_now_panel"]),
                    ["site", "display_entity_id"],
                ].itertuples(index=False, name=None),
            )
        )
        for key in baseline_keys:
            assert_true(key in cluster_preview_keys, f"baseline row {key} should be preserved in cluster preview")

        cluster_ids = set(
            observed_cluster_preview.loc[
                observed_cluster_preview["preview_attention_class"].astype(str).eq("secondary_value_cluster"),
                "display_entity_id",
            ].astype(str)
        )
        assert_true(
            cluster_ids == {"alpha_cluster_001", "beta_cluster_001"},
            "cluster preview should append both cluster rows with cluster_id as display_entity_id",
        )
        alpha_cluster_row = observed_cluster_preview.loc[
            observed_cluster_preview["display_entity_id"].astype(str).eq("alpha_cluster_001")
        ].iloc[0]
        assert_true(
            int(alpha_cluster_row["member_overlap_with_attention_count"]) == 1,
            "member_overlap_with_attention_count should detect overlapping attention member panels",
        )
        assert_true(
            str(alpha_cluster_row["display_shape_or_cluster_kind"]) == "discovery_cluster",
            "cluster row should use discovery_cluster shape/kind",
        )
        assert_true(
            str(alpha_cluster_row["display_status_or_tier"]) == "secondary_discovery_cluster",
            "cluster row should use secondary_discovery_cluster status",
        )

        cluster_overall_row = observed_cluster_preview_summary.loc[
            observed_cluster_preview_summary["record_type"].astype(str).eq("overall")
        ].iloc[0]
        assert_true(int(cluster_overall_row["cluster_preview_count"]) == 5, "overall cluster preview count mismatch")
        assert_true(int(cluster_overall_row["queue_run_count"]) == 2, "overall cluster queue count mismatch")
        assert_true(int(cluster_overall_row["watch_now_panel_count"]) == 1, "overall cluster watch count mismatch")
        assert_true(int(cluster_overall_row["secondary_value_cluster_count"]) == 2, "overall cluster row count mismatch")
        assert_true(int(cluster_overall_row["cluster_panel_total_count"]) == 3, "overall cluster panel total mismatch")
        assert_true(
            int(cluster_overall_row["clusters_with_future_fault_linked_ref_count"]) == 1,
            "overall cluster future fault-linked count mismatch",
        )
        assert_true(
            int(cluster_overall_row["clusters_with_future_truth_linked_ref_count"]) == 1,
            "overall cluster future truth-linked count mismatch",
        )
        assert_true(
            int(cluster_overall_row["total_member_overlap_with_attention_count"]) == 1,
            "overall cluster member overlap count mismatch",
        )

    print("smoke_test_panel_day_engine_operator_attention_plus_discovery_preview_v1.py: PASS")


if __name__ == "__main__":
    main()
