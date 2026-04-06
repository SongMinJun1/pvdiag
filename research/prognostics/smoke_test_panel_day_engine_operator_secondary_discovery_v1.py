#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

import build_panel_day_engine_run_ranker_v2_holdout_audit as holdout_base
import build_panel_day_engine_operator_secondary_discovery_v1 as builder_mod

KEY_COLS = holdout_base.KEY_COLS
FEATURE_COLS = list(dict.fromkeys([*KEY_COLS, "run_day_count", "run_shape_class", *holdout_base.TRAIN_FEATURES]))
LABEL_PACK_V3_COLS = [*KEY_COLS, "label_bucket_v3", "training_label_v3"]
RECOMMENDATION_COLS = ["recommended_next_direction", "rationale_ko"]
SPLIT_RECOMMENDATION_COLS = ["recommended_split_rule", "recommended_next_direction", "rationale_ko"]
ATTENTION_COLS = ["site", "panel_id"]
V0_COLS = [*KEY_COLS, "electrical_core_minus_broadshape_050"]
FATE_REF_COLS = [*KEY_COLS, "discovery_fate_class"]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def make_feature_row(
    site: str,
    panel_id: str,
    start: str,
    end: str,
    *,
    run_shape_class: str,
    run_day_count: int,
    pre_ews_day_count: int,
    ews_warning_day_count: int,
    pre_alarm_day_count: int,
    max_signal_count: float,
    mean_signal_count: float,
    cond_evt_day_ratio: float,
    cond_evt_only_day_ratio: float,
    ae_mid_or_hi_early_day_ratio: float,
    p95_recon_error: float,
    max_v_drop: float,
    min_mid_ratio: float,
    min_mid_v_ratio: float,
) -> dict[str, object]:
    return {
        "site": site,
        "panel_id": panel_id,
        "run_start_date": start,
        "run_end_date": end,
        "run_day_count": run_day_count,
        "run_shape_class": run_shape_class,
        "pre_ews_day_count": pre_ews_day_count,
        "ews_warning_day_count": ews_warning_day_count,
        "pre_alarm_day_count": pre_alarm_day_count,
        "prefault_B_day_count": 0,
        "pre_alarm_max_run": pre_alarm_day_count,
        "max_signal_count": max_signal_count,
        "mean_signal_count": mean_signal_count,
        "any_data_bad": 0,
        "data_bad_day_ratio": 0.0,
        "cond_evt_day_ratio": cond_evt_day_ratio,
        "cond_evt_only_day_ratio": cond_evt_only_day_ratio,
        "cond_evt_same_day_early_corroborated_day_ratio": min(cond_evt_day_ratio, 0.7),
        "ae_mid_or_hi_early_day_ratio": ae_mid_or_hi_early_day_ratio,
        "dtw_mid_or_hi_early_day_ratio": ae_mid_or_hi_early_day_ratio * 0.9,
        "hs_mid_or_hi_early_day_ratio": ae_mid_or_hi_early_day_ratio * 0.8,
        "max_recon_error": p95_recon_error + 0.02,
        "p95_recon_error": p95_recon_error,
        "max_dtw_dist": 1.0 - min_mid_ratio,
        "p95_dtw_dist": max(0.0, 1.0 - min_mid_ratio - 0.05),
        "max_hs_score": ae_mid_or_hi_early_day_ratio,
        "p95_hs_score": max(0.0, ae_mid_or_hi_early_day_ratio - 0.05),
        "min_mid_ratio": min_mid_ratio,
        "min_mid_v_ratio": min_mid_v_ratio,
        "min_mid_i_ratio": min_mid_ratio + 0.02,
        "max_v_drop": max_v_drop,
    }


def date_for(site_offset: int, run_idx: int) -> tuple[str, str]:
    start = pd.Timestamp("2026-01-01") + pd.Timedelta(days=site_offset * 40 + run_idx)
    end = start + pd.Timedelta(days=1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def build_fixture_root(tmp_root: Path) -> None:
    share_dir = tmp_root / "_share"
    feature_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    v0_rows: list[dict[str, object]] = []
    attention_rows: list[dict[str, object]] = []
    fate_rows: list[dict[str, object]] = []

    sites = ["alpha", "beta", "gamma", "delta"]
    for site_offset, site in enumerate(sites):
        pos_start, pos_end = date_for(site_offset, 100)
        neg_start, neg_end = date_for(site_offset, 101)
        feature_rows.append(
            make_feature_row(
                site,
                f"{site}.train.pos",
                pos_start,
                pos_end,
                run_shape_class="medium_alert_run",
                run_day_count=3,
                pre_ews_day_count=2,
                ews_warning_day_count=1,
                pre_alarm_day_count=1,
                max_signal_count=3.0,
                mean_signal_count=2.4,
                cond_evt_day_ratio=0.90,
                cond_evt_only_day_ratio=0.82,
                ae_mid_or_hi_early_day_ratio=0.91,
                p95_recon_error=0.09,
                max_v_drop=0.72,
                min_mid_ratio=0.42,
                min_mid_v_ratio=0.40,
            )
        )
        label_rows.append(
            {
                "site": site,
                "panel_id": f"{site}.train.pos",
                "run_start_date": pos_start,
                "run_end_date": pos_end,
                "label_bucket_v3": "positive_like",
                "training_label_v3": "positive",
            }
        )
        v0_rows.append(
            {
                "site": site,
                "panel_id": f"{site}.train.pos",
                "run_start_date": pos_start,
                "run_end_date": pos_end,
                "electrical_core_minus_broadshape_050": 9.0,
            }
        )

        feature_rows.append(
            make_feature_row(
                site,
                f"{site}.train.neg",
                neg_start,
                neg_end,
                run_shape_class="short_alert_run",
                run_day_count=2,
                pre_ews_day_count=0,
                ews_warning_day_count=0,
                pre_alarm_day_count=0,
                max_signal_count=1.0,
                mean_signal_count=1.0,
                cond_evt_day_ratio=0.15,
                cond_evt_only_day_ratio=0.08,
                ae_mid_or_hi_early_day_ratio=0.18,
                p95_recon_error=0.02,
                max_v_drop=0.18,
                min_mid_ratio=0.84,
                min_mid_v_ratio=0.82,
            )
        )
        label_rows.append(
            {
                "site": site,
                "panel_id": f"{site}.train.neg",
                "run_start_date": neg_start,
                "run_end_date": neg_end,
                "label_bucket_v3": "negative_like",
                "training_label_v3": "negative",
            }
        )
        v0_rows.append(
            {
                "site": site,
                "panel_id": f"{site}.train.neg",
                "run_start_date": neg_start,
                "run_end_date": neg_end,
                "electrical_core_minus_broadshape_050": 1.0,
            }
        )

        for run_idx in range(8):
            start, end = date_for(site_offset, run_idx)
            panel_id = f"{site}.cand.{run_idx}"
            base = 0.88 - run_idx * 0.04
            if site == "delta":
                base -= 0.22
            run_shape_class = ["chronic_alert_run", "medium_alert_run", "short_alert_run"][run_idx % 3]
            feature_rows.append(
                make_feature_row(
                    site,
                    panel_id,
                    start,
                    end,
                    run_shape_class=run_shape_class,
                    run_day_count=4 - (run_idx % 2),
                    pre_ews_day_count=2 if base > 0.45 else 1,
                    ews_warning_day_count=1 if base > 0.40 else 0,
                    pre_alarm_day_count=1 if base > 0.55 else 0,
                    max_signal_count=1.5 + base * 2.0,
                    mean_signal_count=1.0 + base * 1.5,
                    cond_evt_day_ratio=max(0.10, base),
                    cond_evt_only_day_ratio=max(0.05, base - 0.05),
                    ae_mid_or_hi_early_day_ratio=max(0.10, base),
                    p95_recon_error=0.02 + base * 0.05,
                    max_v_drop=0.15 + base * 0.5,
                    min_mid_ratio=max(0.25, 0.95 - base * 0.6),
                    min_mid_v_ratio=max(0.20, 0.93 - base * 0.6),
                )
            )
            label_rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "run_start_date": start,
                    "run_end_date": end,
                    "label_bucket_v3": "unlabeled_other",
                    "training_label_v3": "exclude",
                }
            )
            reference_score = 2.0 + base * 3.0
            v0_rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "run_start_date": start,
                    "run_end_date": end,
                    "electrical_core_minus_broadshape_050": reference_score,
                }
            )
            if site in {"alpha", "beta"} and run_idx <= 2:
                fate_class = "future_fault_linked"
            elif site == "gamma" and run_idx == 4:
                fate_class = "future_truth_linked"
            elif run_idx % 2 == 0:
                fate_class = "recurring_monitor_like"
            else:
                fate_class = "isolated_unexplained"
            fate_rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "run_start_date": start,
                    "run_end_date": end,
                    "discovery_fate_class": fate_class,
                }
            )

    # Exclude one high-score panel already in attention lane.
    attention_rows.append({"site": "alpha", "panel_id": "alpha.cand.0"})
    attention_rows.append({"site": "delta", "panel_id": "delta.cand.0"})

    recommendation_rows = [
        {
            "recommended_next_direction": "use_logistic_as_secondary_discovery_lane",
            "rationale_ko": "synthetic complement approval",
        }
    ]
    split_recommendation_rows = [
        {
            "recommended_split_rule": "electrical_only|electrical_core_minus_broadshape_050>=4",
            "recommended_next_direction": "split_secondary_discovery_into_value_vs_monitor",
            "rationale_ko": "synthetic split approval",
        }
    ]

    write_csv(share_dir / "panel_day_engine_run_feature_table_v1.csv", feature_rows, FEATURE_COLS)
    write_csv(share_dir / "panel_day_engine_run_label_pack_v3_intersection.csv", label_rows, LABEL_PACK_V3_COLS)
    write_csv(share_dir / "panel_day_engine_run_ranker_v0_scores.csv", v0_rows, V0_COLS)
    write_csv(share_dir / "panel_day_engine_operator_attention_now_v1.csv", attention_rows, ATTENTION_COLS)
    write_csv(share_dir / "panel_day_engine_operator_secondary_discovery_fate_cases_v1.csv", fate_rows, FATE_REF_COLS)
    write_csv(
        share_dir / "panel_day_engine_run_ranker_complement_recommendation_v1.csv",
        recommendation_rows,
        RECOMMENDATION_COLS,
    )
    write_csv(
        share_dir / "panel_day_engine_operator_secondary_discovery_threshold_split_recommendation_v1.csv",
        split_recommendation_rows,
        SPLIT_RECOMMENDATION_COLS,
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
    builder = repo_root / "research" / "prognostics" / "build_panel_day_engine_operator_secondary_discovery_v1.py"

    py_compile.compile(str(repo_root / "pv_ae" / "panel_day_engine.py"), doraise=True)
    py_compile.compile(str(builder), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="secondary-discovery-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        result = run([sys.executable, str(builder), "--root", str(tmp_root)], cwd=repo_root)
        if result.returncode != 0:
            raise SystemExit(f"builder failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        discovery_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_v1.csv"
        summary_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_summary_v1.csv"
        value_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_value_v1.csv"
        monitor_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_monitor_v1.csv"
        assert_true(discovery_path.exists(), "missing discovery output")
        assert_true(summary_path.exists(), "missing summary output")
        assert_true(value_path.exists(), "missing value lane output")
        assert_true(monitor_path.exists(), "missing monitor lane output")

        discovery_df = pd.read_csv(discovery_path, encoding="utf-8-sig")
        summary_df = pd.read_csv(summary_path, encoding="utf-8-sig")
        value_df = pd.read_csv(value_path, encoding="utf-8-sig")
        monitor_df = pd.read_csv(monitor_path, encoding="utf-8-sig")
        assert_true(not discovery_df.empty, "discovery output should not be empty")
        assert_true(not summary_df.empty, "summary output should not be empty")

        # Attention panels should be removed entirely.
        selected_panels = set(map(tuple, discovery_df.loc[:, ["site", "panel_id"]].itertuples(index=False, name=None)))
        assert_true(("alpha", "alpha.cand.0") not in selected_panels, "attention panel alpha.cand.0 should be excluded")
        assert_true(("delta", "delta.cand.0") not in selected_panels, "attention panel delta.cand.0 should be excluded")

        # Recompute expected selection from helper functions and compare exactly.
        builder_mod.load_guardrail(tmp_root)
        split_rule = builder_mod.load_split_guardrail(tmp_root)
        scored_universe = builder_mod.prepare_scored_universe(tmp_root)
        attention_panels = builder_mod.load_attention_panels(tmp_root)
        candidate_df = builder_mod.build_candidate_universe(scored_universe, attention_panels)
        expected_df = builder_mod.apply_discovery_split(builder_mod.select_discovery_lane(candidate_df), split_rule)
        expected_value_df, expected_monitor_df = builder_mod.build_lane_outputs(expected_df)
        fate_ref_df = builder_mod.load_fate_references(tmp_root)
        expected_summary_df = builder_mod.build_summary(candidate_df, expected_df, fate_ref_df, str(split_rule["rule_name"]))

        observed_cmp = normalize_df_for_compare(discovery_df.loc[:, builder_mod.DISCOVERY_COLS].copy())
        expected_cmp = normalize_df_for_compare(expected_df.loc[:, builder_mod.DISCOVERY_COLS].copy())
        assert_true(
            observed_cmp.equals(expected_cmp),
            "selected discovery lane does not match top5/site + top20 overall policy",
        )
        assert_true(
            normalize_df_for_compare(value_df.loc[:, builder_mod.DISCOVERY_COLS].copy()).equals(
                normalize_df_for_compare(expected_value_df.loc[:, builder_mod.DISCOVERY_COLS].copy())
            ),
            "value lane file does not match expected split subset",
        )
        assert_true(
            normalize_df_for_compare(monitor_df.loc[:, builder_mod.DISCOVERY_COLS].copy()).equals(
                normalize_df_for_compare(expected_monitor_df.loc[:, builder_mod.DISCOVERY_COLS].copy())
            ),
            "monitor lane file does not match expected split subset",
        )
        assert_true(
            normalize_df_for_compare(summary_df.loc[:, builder_mod.SUMMARY_COLS].copy()).equals(
                normalize_df_for_compare(expected_summary_df.loc[:, builder_mod.SUMMARY_COLS].copy())
            ),
            "summary output does not match expected lane counts and retrospective reference counts",
        )

        assert_true(
            int(discovery_df["value_lane_flag"].sum()) == len(value_df),
            "value lane count should match rows in value output",
        )
        assert_true(
            int(discovery_df["monitor_lane_flag"].sum()) == len(monitor_df),
            "monitor lane count should match rows in monitor output",
        )
        assert_true(
            int((discovery_df["value_lane_flag"] + discovery_df["monitor_lane_flag"]).sum()) == len(discovery_df),
            "rows should partition cleanly into value or monitor",
        )
        assert_true(
            discovery_df["discovery_split_class"].isin(["value_candidate_lane", "monitor_candidate_lane"]).all(),
            "split class should use only allowed values",
        )

        overall_row = summary_df.loc[summary_df["record_type"].astype(str).eq("overall")].iloc[0]
        assert_true(
            int(overall_row["candidate_universe_count"]) == int(len(candidate_df)),
            "overall candidate_universe_count mismatch",
        )
        assert_true(
            int(overall_row["selected_discovery_count"]) == int(len(discovery_df)),
            "overall selected_discovery_count mismatch",
        )
        assert_true(
            int(overall_row["value_lane_count"]) == int(len(value_df)),
            "overall value_lane_count mismatch",
        )
        assert_true(
            int(overall_row["monitor_lane_count"]) == int(len(monitor_df)),
            "overall monitor_lane_count mismatch",
        )
        assert_true(
            int(overall_row["value_lane_future_fault_linked_ref_count"]) > 0,
            "retrospective future fault reference counts should be populated",
        )
        assert_true(
            str(overall_row["split_rule_name"]) == "electrical_only|electrical_core_minus_broadshape_050>=4",
            "summary should carry split_rule_name",
        )

        sample_df = pd.DataFrame(
            [
                {
                    "electrical_core_minus_broadshape_050": 9.0,
                    "logistic_v3_discovery_score": 0.98,
                    "ae_mid_or_hi_early_day_ratio": 0.10,
                    "p95_recon_error": 0.008,
                },
                {
                    "electrical_core_minus_broadshape_050": 7.5,
                    "logistic_v3_discovery_score": 0.96,
                    "ae_mid_or_hi_early_day_ratio": 0.50,
                    "p95_recon_error": 0.040,
                },
            ]
        )
        parser_expectations = {
            "electrical_only|electrical_core_minus_broadshape_050>=8": [True, False],
            "logistic_only|logistic_v3_discovery_score>=0.97": [True, False],
            "electrical_and_low_ae|electrical_core_minus_broadshape_050>=8|ae_mid_or_hi_early_day_ratio<=0.25": [True, False],
            "electrical_and_low_recon|electrical_core_minus_broadshape_050>=8|p95_recon_error<=0.01": [True, False],
            "logistic_and_low_ae|logistic_v3_discovery_score>=0.97|ae_mid_or_hi_early_day_ratio<=0.25": [True, False],
            "logistic_and_low_recon|logistic_v3_discovery_score>=0.97|p95_recon_error<=0.01": [True, False],
        }
        for rule_name, expected_mask in parser_expectations.items():
            parsed = builder_mod.parse_split_rule(rule_name)
            observed_mask = builder_mod.apply_split_rule(sample_df, parsed).tolist()
            assert_true(observed_mask == expected_mask, f"rule parsing/apply failed for {rule_name}")

        bad_guardrail = pd.DataFrame(
            [{"recommended_next_direction": "stop_learned_scorer_for_now", "rationale_ko": "blocked"}]
        )
        bad_guardrail.to_csv(
            tmp_root / "_share" / "panel_day_engine_run_ranker_complement_recommendation_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )
        bad_result = run([sys.executable, str(builder), "--root", str(tmp_root)], cwd=repo_root)
        assert_true(bad_result.returncode != 0, "builder should fail when complement guardrail blocks secondary discovery")
        combined_msg = f"{bad_result.stdout}\n{bad_result.stderr}"
        assert_true("use_logistic_as_secondary_discovery_lane" in combined_msg, "guardrail failure message should mention expected recommendation")

        write_csv(
            tmp_root / "_share" / "panel_day_engine_run_ranker_complement_recommendation_v1.csv",
            [{"recommended_next_direction": "use_logistic_as_secondary_discovery_lane", "rationale_ko": "restored"}],
            RECOMMENDATION_COLS,
        )
        write_csv(
            tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_threshold_split_recommendation_v1.csv",
            [{
                "recommended_split_rule": "electrical_only|electrical_core_minus_broadshape_050>=4",
                "recommended_next_direction": "keep_secondary_discovery_as_analyst_only",
                "rationale_ko": "blocked",
            }],
            SPLIT_RECOMMENDATION_COLS,
        )
        bad_split_result = run([sys.executable, str(builder), "--root", str(tmp_root)], cwd=repo_root)
        assert_true(bad_split_result.returncode != 0, "builder should fail when split guardrail blocks value/monitor partition")
        split_msg = f"{bad_split_result.stdout}\n{bad_split_result.stderr}"
        assert_true(
            "split_secondary_discovery_into_value_vs_monitor" in split_msg,
            "split guardrail failure message should mention expected recommendation",
        )

    print("smoke_test_panel_day_engine_operator_secondary_discovery_v1.py: PASS")


if __name__ == "__main__":
    main()
