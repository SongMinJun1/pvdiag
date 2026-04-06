#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

FEATURE_TABLE_COLS = [
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
LABEL_PACK_V2_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "label_bucket_v2", "training_label_v2"]
REVIEW_BATCH_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "label_bucket_v2",
    "candidate_class",
    "candidate_priority_band",
    "review_track",
    "review_priority_rank",
    "review_priority_reason_ko",
    "suggested_label_action",
    "suggested_label_action_reason_ko",
    "site_positive_gap_flag",
    "site_negative_gap_flag",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
    "global_score_rank",
    "site_score_rank",
    "watch_now_panel_ref_flag",
    "watch_review_run_ref_flag",
    "common_cause_descriptive_ref_flag",
    "expansion_reason_ko",
]
V2_SUMMARY_COLS = ["score_name", "fold_type", "mean_top20_positive_minus_negative"]
V0_SCORE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
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
    site: str,
    panel_id: str,
    date: str,
    *,
    run_day_count: int,
    max_v_drop: float,
    min_mid_v_ratio: float,
    min_mid_ratio: float,
    cond_evt_only_day_ratio: float,
    ae_mid_or_hi_early_day_ratio: float,
    mean_signal_count: float,
    max_signal_count: float,
    p95_recon_error: float,
) -> dict[str, object]:
    return {
        "site": site,
        "panel_id": panel_id,
        "run_start_date": date,
        "run_end_date": date,
        "run_day_count": run_day_count,
        "run_shape_class": "medium_alert_run",
        "overlap_case_class": "unmatched_to_review",
        "delta_run_class": "added_run",
        "fate_class": "",
        "cohort_hint": "synthetic_only",
        "pre_ews_day_count": run_day_count,
        "ews_warning_day_count": run_day_count,
        "pre_alarm_day_count": run_day_count,
        "prefault_B_day_count": 0,
        "pre_ews_run_count": 1,
        "ews_warning_run_count": 1,
        "pre_alarm_run_count": 1,
        "prefault_B_run_count": 0,
        "pre_alarm_max_run": run_day_count,
        "max_signal_count": max_signal_count,
        "mean_signal_count": mean_signal_count,
        "any_data_bad": 0,
        "data_bad_day_ratio": 0.0,
        "cond_evt_day_ratio": 1.0,
        "cond_evt_only_day_ratio": cond_evt_only_day_ratio,
        "cond_evt_same_day_early_corroborated_day_ratio": 1.0 - cond_evt_only_day_ratio,
        "ae_mid_or_hi_early_day_ratio": ae_mid_or_hi_early_day_ratio,
        "dtw_mid_or_hi_early_day_ratio": 0.5,
        "hs_mid_or_hi_early_day_ratio": 0.25,
        "max_recon_error": p95_recon_error,
        "p95_recon_error": p95_recon_error,
        "max_dtw_dist": max_signal_count * 10.0,
        "p95_dtw_dist": max_signal_count * 9.0,
        "max_hs_score": ae_mid_or_hi_early_day_ratio,
        "p95_hs_score": ae_mid_or_hi_early_day_ratio,
        "min_mid_ratio": min_mid_ratio,
        "min_mid_v_ratio": min_mid_v_ratio,
        "min_mid_i_ratio": min_mid_ratio,
        "max_v_drop": max_v_drop,
        "recurring_run_within_60d": 0,
        "future_fault_linked_flag": 0,
        "future_truth_linked_flag": 0,
    }


def label_row(feature: dict[str, object], label_bucket_v2: str, training_label_v2: str) -> dict[str, object]:
    return {
        "site": feature["site"],
        "panel_id": feature["panel_id"],
        "run_start_date": feature["run_start_date"],
        "run_end_date": feature["run_end_date"],
        "label_bucket_v2": label_bucket_v2,
        "training_label_v2": training_label_v2,
    }


def v0_row(feature: dict[str, object], core_score: float, broadshape_score: float) -> dict[str, object]:
    return {
        "site": feature["site"],
        "panel_id": feature["panel_id"],
        "run_start_date": feature["run_start_date"],
        "run_end_date": feature["run_end_date"],
        "electrical_core_score": core_score,
        "electrical_core_minus_broadshape_050": broadshape_score,
    }


def review_row(
    feature: dict[str, object],
    *,
    candidate_priority_band: str,
    review_track: str,
    suggested_label_action: str,
    score: float,
    watch_now_panel_ref_flag: int,
    site_positive_gap_flag: int,
    review_priority_rank: int,
    label_bucket_v2: str = "unlabeled_other",
    candidate_class: str = "positive_review_candidate",
) -> dict[str, object]:
    return {
        "site": feature["site"],
        "panel_id": feature["panel_id"],
        "run_start_date": feature["run_start_date"],
        "run_end_date": feature["run_end_date"],
        "run_day_count": feature["run_day_count"],
        "run_shape_class": feature["run_shape_class"],
        "label_bucket_v2": label_bucket_v2,
        "candidate_class": candidate_class,
        "candidate_priority_band": candidate_priority_band,
        "review_track": review_track,
        "review_priority_rank": review_priority_rank,
        "review_priority_reason_ko": "synthetic review row",
        "suggested_label_action": suggested_label_action,
        "suggested_label_action_reason_ko": "synthetic action",
        "site_positive_gap_flag": site_positive_gap_flag,
        "site_negative_gap_flag": 0,
        "electrical_core_score": score - 0.2,
        "electrical_core_minus_broadshape_050": score,
        "global_score_rank": review_priority_rank,
        "site_score_rank": review_priority_rank,
        "watch_now_panel_ref_flag": watch_now_panel_ref_flag,
        "watch_review_run_ref_flag": 0,
        "common_cause_descriptive_ref_flag": 1 if review_track == "common_cause_review_batch" else 0,
        "expansion_reason_ko": "synthetic review candidate",
    }


def build_fixture_root(tmp_root: Path) -> None:
    features = [
        feature_row("alpha", "alpha.pos.1", "2025-01-01", run_day_count=3, max_v_drop=0.92, min_mid_v_ratio=0.20, min_mid_ratio=0.25, cond_evt_only_day_ratio=0.88, ae_mid_or_hi_early_day_ratio=0.12, mean_signal_count=1.0, max_signal_count=1.2, p95_recon_error=0.11),
        feature_row("alpha", "alpha.neg.1", "2025-01-02", run_day_count=3, max_v_drop=0.12, min_mid_v_ratio=0.92, min_mid_ratio=0.90, cond_evt_only_day_ratio=0.10, ae_mid_or_hi_early_day_ratio=0.92, mean_signal_count=3.6, max_signal_count=4.0, p95_recon_error=0.82),
        feature_row("alpha", "alpha.p1", "2025-01-03", run_day_count=4, max_v_drop=0.86, min_mid_v_ratio=0.28, min_mid_ratio=0.32, cond_evt_only_day_ratio=0.84, ae_mid_or_hi_early_day_ratio=0.15, mean_signal_count=1.2, max_signal_count=1.5, p95_recon_error=0.18),
        feature_row("alpha", "alpha.p2a", "2025-01-04", run_day_count=4, max_v_drop=0.81, min_mid_v_ratio=0.31, min_mid_ratio=0.36, cond_evt_only_day_ratio=0.80, ae_mid_or_hi_early_day_ratio=0.18, mean_signal_count=1.3, max_signal_count=1.6, p95_recon_error=0.20),
        feature_row("alpha", "alpha.p2b", "2025-01-05", run_day_count=4, max_v_drop=0.74, min_mid_v_ratio=0.38, min_mid_ratio=0.42, cond_evt_only_day_ratio=0.72, ae_mid_or_hi_early_day_ratio=0.22, mean_signal_count=1.5, max_signal_count=1.8, p95_recon_error=0.26),
        feature_row("alpha", "alpha.mon.1", "2025-01-06", run_day_count=4, max_v_drop=0.44, min_mid_v_ratio=0.66, min_mid_ratio=0.70, cond_evt_only_day_ratio=0.50, ae_mid_or_hi_early_day_ratio=0.52, mean_signal_count=2.3, max_signal_count=2.6, p95_recon_error=0.45),
        feature_row("beta", "beta.pos.1", "2025-01-07", run_day_count=3, max_v_drop=0.88, min_mid_v_ratio=0.24, min_mid_ratio=0.28, cond_evt_only_day_ratio=0.86, ae_mid_or_hi_early_day_ratio=0.13, mean_signal_count=1.0, max_signal_count=1.2, p95_recon_error=0.12),
        feature_row("beta", "beta.neg.1", "2025-01-08", run_day_count=3, max_v_drop=0.10, min_mid_v_ratio=0.94, min_mid_ratio=0.93, cond_evt_only_day_ratio=0.08, ae_mid_or_hi_early_day_ratio=0.94, mean_signal_count=3.8, max_signal_count=4.2, p95_recon_error=0.90),
        feature_row("beta", "beta.p1", "2025-01-09", run_day_count=4, max_v_drop=0.82, min_mid_v_ratio=0.30, min_mid_ratio=0.34, cond_evt_only_day_ratio=0.79, ae_mid_or_hi_early_day_ratio=0.16, mean_signal_count=1.3, max_signal_count=1.6, p95_recon_error=0.19),
        feature_row("beta", "beta.p2a", "2025-01-10", run_day_count=4, max_v_drop=0.79, min_mid_v_ratio=0.32, min_mid_ratio=0.37, cond_evt_only_day_ratio=0.78, ae_mid_or_hi_early_day_ratio=0.18, mean_signal_count=1.4, max_signal_count=1.7, p95_recon_error=0.21),
        feature_row("beta", "beta.p2b", "2025-01-11", run_day_count=4, max_v_drop=0.70, min_mid_v_ratio=0.40, min_mid_ratio=0.45, cond_evt_only_day_ratio=0.70, ae_mid_or_hi_early_day_ratio=0.24, mean_signal_count=1.6, max_signal_count=1.9, p95_recon_error=0.27),
        feature_row("beta", "beta.cc.1", "2025-01-12", run_day_count=3, max_v_drop=0.40, min_mid_v_ratio=0.68, min_mid_ratio=0.72, cond_evt_only_day_ratio=0.48, ae_mid_or_hi_early_day_ratio=0.55, mean_signal_count=2.2, max_signal_count=2.6, p95_recon_error=0.44),
        feature_row("gamma", "gamma.pos.1", "2025-01-13", run_day_count=3, max_v_drop=0.91, min_mid_v_ratio=0.22, min_mid_ratio=0.27, cond_evt_only_day_ratio=0.87, ae_mid_or_hi_early_day_ratio=0.12, mean_signal_count=1.1, max_signal_count=1.3, p95_recon_error=0.13),
        feature_row("gamma", "gamma.neg.1", "2025-01-14", run_day_count=3, max_v_drop=0.11, min_mid_v_ratio=0.93, min_mid_ratio=0.92, cond_evt_only_day_ratio=0.07, ae_mid_or_hi_early_day_ratio=0.93, mean_signal_count=3.7, max_signal_count=4.1, p95_recon_error=0.88),
        feature_row("gamma", "gamma.p2a", "2025-01-15", run_day_count=4, max_v_drop=0.76, min_mid_v_ratio=0.35, min_mid_ratio=0.40, cond_evt_only_day_ratio=0.74, ae_mid_or_hi_early_day_ratio=0.20, mean_signal_count=1.5, max_signal_count=1.8, p95_recon_error=0.24),
        feature_row("gamma", "gamma.p2b", "2025-01-16", run_day_count=4, max_v_drop=0.68, min_mid_v_ratio=0.44, min_mid_ratio=0.48, cond_evt_only_day_ratio=0.66, ae_mid_or_hi_early_day_ratio=0.26, mean_signal_count=1.8, max_signal_count=2.0, p95_recon_error=0.30),
    ]

    labels = [
        label_row(features[0], "positive_like", "positive"),
        label_row(features[1], "negative_like", "negative"),
        label_row(features[2], "unlabeled_other", "exclude"),
        label_row(features[3], "unlabeled_other", "exclude"),
        label_row(features[4], "unlabeled_other", "exclude"),
        label_row(features[5], "monitor_like", "exclude"),
        label_row(features[6], "positive_like", "positive"),
        label_row(features[7], "negative_like", "negative"),
        label_row(features[8], "unlabeled_other", "exclude"),
        label_row(features[9], "unlabeled_other", "exclude"),
        label_row(features[10], "unlabeled_other", "exclude"),
        label_row(features[11], "common_cause_like", "exclude"),
        label_row(features[12], "positive_like", "positive"),
        label_row(features[13], "negative_like", "negative"),
        label_row(features[14], "unlabeled_other", "exclude"),
        label_row(features[15], "unlabeled_other", "exclude"),
    ]

    v0_scores = []
    for feature, label in zip(features, labels):
        bucket = label["label_bucket_v2"]
        if bucket == "positive_like":
            core_score, broadshape_score = 0.82, 0.88
        elif bucket == "negative_like":
            core_score, broadshape_score = 0.22, 0.18
        elif bucket == "monitor_like":
            core_score, broadshape_score = 0.45, 0.48
        elif bucket == "common_cause_like":
            core_score, broadshape_score = 0.42, 0.46
        else:
            core_score = 0.55 + feature["max_v_drop"] * 0.15
            broadshape_score = 0.58 + feature["max_v_drop"] * 0.18
        v0_scores.append(v0_row(feature, core_score, broadshape_score))

    review_rows = [
        review_row(features[2], candidate_priority_band="P1", review_track="positive_review_batch", suggested_label_action="inspect_for_positive_promotion", score=9.8, watch_now_panel_ref_flag=1, site_positive_gap_flag=1, review_priority_rank=1),
        review_row(features[8], candidate_priority_band="P1", review_track="positive_review_batch", suggested_label_action="inspect_for_positive_promotion", score=9.7, watch_now_panel_ref_flag=0, site_positive_gap_flag=0, review_priority_rank=2),
        review_row(features[3], candidate_priority_band="P2", review_track="positive_review_batch", suggested_label_action="inspect_for_positive_promotion", score=9.5, watch_now_panel_ref_flag=1, site_positive_gap_flag=0, review_priority_rank=3),
        review_row(features[4], candidate_priority_band="P2", review_track="positive_review_batch", suggested_label_action="inspect_for_positive_promotion", score=9.2, watch_now_panel_ref_flag=0, site_positive_gap_flag=0, review_priority_rank=4),
        review_row(features[9], candidate_priority_band="P2", review_track="positive_review_batch", suggested_label_action="inspect_for_positive_promotion", score=9.4, watch_now_panel_ref_flag=1, site_positive_gap_flag=0, review_priority_rank=5),
        review_row(features[10], candidate_priority_band="P2", review_track="positive_review_batch", suggested_label_action="inspect_for_positive_promotion", score=9.1, watch_now_panel_ref_flag=0, site_positive_gap_flag=0, review_priority_rank=6),
        review_row(features[14], candidate_priority_band="P2", review_track="positive_review_batch", suggested_label_action="inspect_for_positive_promotion", score=8.9, watch_now_panel_ref_flag=0, site_positive_gap_flag=0, review_priority_rank=7),
        review_row(features[15], candidate_priority_band="P2", review_track="positive_review_batch", suggested_label_action="inspect_for_positive_promotion", score=8.5, watch_now_panel_ref_flag=0, site_positive_gap_flag=0, review_priority_rank=8),
        review_row(features[5], candidate_priority_band="P3", review_track="monitor_review_batch", suggested_label_action="inspect_for_monitor_confirmation", score=6.0, watch_now_panel_ref_flag=0, site_positive_gap_flag=0, review_priority_rank=9, label_bucket_v2="monitor_like", candidate_class="monitor_review_candidate"),
        review_row(features[11], candidate_priority_band="P3", review_track="common_cause_review_batch", suggested_label_action="inspect_for_common_cause_confirmation", score=5.5, watch_now_panel_ref_flag=0, site_positive_gap_flag=0, review_priority_rank=10, label_bucket_v2="common_cause_like", candidate_class="common_cause_review_candidate"),
    ]

    v2_summary_rows = [
        {"score_name": "logistic_v2_holdout", "fold_type": "leave_one_site_out", "mean_top20_positive_minus_negative": 0.02},
        {"score_name": "logistic_v2_holdout", "fold_type": "time_holdout_70_30", "mean_top20_positive_minus_negative": 0.01},
        {"score_name": "electrical_core_score", "fold_type": "leave_one_site_out", "mean_top20_positive_minus_negative": 0.04},
        {"score_name": "electrical_core_score", "fold_type": "time_holdout_70_30", "mean_top20_positive_minus_negative": 0.03},
        {"score_name": "electrical_core_minus_broadshape_050", "fold_type": "leave_one_site_out", "mean_top20_positive_minus_negative": 0.05},
        {"score_name": "electrical_core_minus_broadshape_050", "fold_type": "time_holdout_70_30", "mean_top20_positive_minus_negative": 0.04},
    ]

    write_csv(tmp_root / "_share" / "panel_day_engine_run_feature_table_v1.csv", features, FEATURE_TABLE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_label_pack_v2.csv", labels, LABEL_PACK_V2_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_label_expansion_review_batch_v1.csv", review_rows, REVIEW_BATCH_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v2_holdout_summary.csv", v2_summary_rows, V2_SUMMARY_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v0_scores.csv", v0_scores, V0_SCORE_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_run_label_promotion_scenarios_v1.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_run_label_promotion_scenarios_v1.csv",
        repo_root / "_share" / "panel_day_engine_run_ranker_v3_scenario_holdout_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_run_ranker_v3_scenario_topk_yield_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    with tempfile.TemporaryDirectory(prefix="run_label_promotion_scenarios_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        compile_result = run(
            [
                sys.executable,
                "-m",
                "py_compile",
                "pv_ae/panel_day_engine.py",
                "research/prognostics/build_panel_day_engine_run_label_promotion_scenarios_v1.py",
                "research/prognostics/smoke_test_panel_day_engine_run_label_promotion_scenarios_v1.py",
            ],
            repo_root,
        )
        assert_true(compile_result.returncode == 0, compile_result.stderr)

        build_result = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_run_label_promotion_scenarios_v1.py",
                "--root",
                str(tmp_root),
            ],
            repo_root,
        )
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        scenario_listing = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_label_promotion_scenarios_v1.csv", encoding="utf-8-sig")
        summary = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v3_scenario_holdout_summary_v1.csv", encoding="utf-8-sig")
        topk = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v3_scenario_topk_yield_v1.csv", encoding="utf-8-sig")

        expected_counts = {
            "p1_only": 2,
            "p1_plus_watchnow_ref": 4,
            "p1_plus_site_balanced_p2": 8,
            "p1_plus_watchnow_ref_plus_site_balanced": 7,
        }
        actual_counts = scenario_listing.groupby("scenario_name").size().to_dict()
        assert_true(actual_counts == expected_counts, f"scenario selection counts mismatch: {actual_counts}")

        p1_rows = scenario_listing.loc[scenario_listing["scenario_name"].eq("p1_only")]
        assert_true(set(p1_rows["candidate_priority_band"]) == {"P1"}, "p1_only should include only P1 rows")

        balanced_rows = scenario_listing.loc[scenario_listing["scenario_name"].eq("p1_plus_site_balanced_p2")]
        gamma_balanced = balanced_rows.loc[balanced_rows["site"].eq("gamma")]
        assert_true(len(gamma_balanced) == 2, "site-balanced scenario should include top2 gamma P2 rows")

        hybrid_rows = scenario_listing.loc[scenario_listing["scenario_name"].eq("p1_plus_watchnow_ref_plus_site_balanced")]
        assert_true("gamma.p2a" in set(hybrid_rows["panel_id"]), "hybrid scenario should top-up gamma with one remaining P2 row")
        assert_true("gamma.p2b" not in set(hybrid_rows["panel_id"]), "hybrid scenario should only add one remaining gamma P2 row")

        assert_true(set(summary["scenario_name"]) == set(expected_counts), "summary scenario names mismatch")
        assert_true(set(topk["scenario_name"]) == set(expected_counts), "top-k scenario names mismatch")

        loso_counts = summary.set_index("scenario_name")["loso_valid_fold_count"].to_dict()
        time_counts = summary.set_index("scenario_name")["time_valid_fold_count"].to_dict()
        assert_true(all(int(value) == 3 for value in loso_counts.values()), f"unexpected LOSO valid fold counts: {loso_counts}")
        assert_true(all(int(value) == 1 for value in time_counts.values()), f"unexpected time valid fold counts: {time_counts}")

        summary_row = summary.loc[summary["scenario_name"].eq("p1_only")].iloc[0]
        expected_delta = float(summary_row["loso_mean_top20_positive_minus_negative"]) - 0.02
        assert_true(
            abs(float(summary_row["delta_loso_top20_vs_v2_logistic"]) - expected_delta) < 1e-9,
            "delta_loso_top20_vs_v2_logistic mismatch",
        )
        expected_time_delta = float(summary_row["time_mean_top20_positive_minus_negative"]) - 0.01
        assert_true(
            abs(float(summary_row["delta_time_top20_vs_v2_logistic"]) - expected_time_delta) < 1e-9,
            "delta_time_top20_vs_v2_logistic mismatch",
        )

        topk_counts = topk.groupby(["scenario_name", "top_k"]).size().to_dict()
        for scenario_name in expected_counts:
            assert_true(
                topk_counts.get((scenario_name, 10), 0) == 4 and topk_counts.get((scenario_name, 20), 0) == 4,
                f"expected one top-k row per fold for {scenario_name}",
            )

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
