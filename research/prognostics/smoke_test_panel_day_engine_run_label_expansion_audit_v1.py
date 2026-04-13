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
LABEL_PACK_V2_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "label_bucket_v2",
    "training_label_v2",
]
V0_SCORE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "cohort_hint",
    "electrical_core_score",
    "electrical_evt_score",
    "electrical_evt_minus_broadshape_score",
    "electrical_core_minus_broadshape_025",
    "electrical_core_minus_broadshape_050",
    "electrical_core_minus_broadshape_075",
    "electrical_core_plus_evtonly_minus_broadshape_025",
    "electrical_core_plus_evtonly_minus_broadshape_050",
]
HOLDOUT_SUMMARY_COLS = [
    "score_name",
    "fold_type",
    "valid_fold_count",
    "mean_labeled_test_auc",
    "mean_labeled_test_average_precision",
    "mean_top10_positive_minus_negative",
    "mean_top20_positive_minus_negative",
    "mean_top10_positive_like_count",
    "mean_top10_negative_like_count",
    "mean_top20_positive_like_count",
    "mean_top20_negative_like_count",
    "delta_mean_top10_positive_minus_negative_vs_v1",
    "delta_mean_top20_positive_minus_negative_vs_v1",
    "note",
]
WATCH_NOW_COLS = ["site", "panel_id"]
WATCHLIST_REVIEW_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
COMMON_CAUSE_COLS = ["eval_bucket_v2", "site", "panel_id", "combined_marker_flag"]


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
    start: str,
    end: str,
    *,
    run_day_count: int,
    run_shape_class: str,
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
        "run_start_date": start,
        "run_end_date": end,
        "run_day_count": run_day_count,
        "run_shape_class": run_shape_class,
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


def score_row(feature: dict[str, object], electrical_core_score: float, electrical_core_minus_broadshape_050: float) -> dict[str, object]:
    return {
        "site": feature["site"],
        "panel_id": feature["panel_id"],
        "run_start_date": feature["run_start_date"],
        "run_end_date": feature["run_end_date"],
        "run_day_count": feature["run_day_count"],
        "run_shape_class": feature["run_shape_class"],
        "cohort_hint": feature["cohort_hint"],
        "electrical_core_score": electrical_core_score,
        "electrical_evt_score": electrical_core_score,
        "electrical_evt_minus_broadshape_score": electrical_core_minus_broadshape_050 + 0.1,
        "electrical_core_minus_broadshape_025": electrical_core_minus_broadshape_050 + 0.1,
        "electrical_core_minus_broadshape_050": electrical_core_minus_broadshape_050,
        "electrical_core_minus_broadshape_075": electrical_core_minus_broadshape_050 - 0.1,
        "electrical_core_plus_evtonly_minus_broadshape_025": electrical_core_minus_broadshape_050 + 0.1,
        "electrical_core_plus_evtonly_minus_broadshape_050": electrical_core_minus_broadshape_050,
    }


def build_fixture_root(tmp_root: Path) -> None:
    features = [
        feature_row("alpha", "alpha.poscand", "2025-01-01", "2025-01-03", run_day_count=3, run_shape_class="medium_alert_run", max_v_drop=0.75, min_mid_v_ratio=0.30, min_mid_ratio=0.35, cond_evt_only_day_ratio=0.8, ae_mid_or_hi_early_day_ratio=0.2, mean_signal_count=1.3, max_signal_count=1.6, p95_recon_error=0.22),
        feature_row("alpha", "alpha.low", "2025-01-04", "2025-01-04", run_day_count=1, run_shape_class="short_alert_run", max_v_drop=0.10, min_mid_v_ratio=0.90, min_mid_ratio=0.92, cond_evt_only_day_ratio=0.1, ae_mid_or_hi_early_day_ratio=0.7, mean_signal_count=2.5, max_signal_count=2.6, p95_recon_error=0.60),
        feature_row("alpha", "alpha.neglabel", "2025-01-05", "2025-01-05", run_day_count=1, run_shape_class="short_alert_run", max_v_drop=0.08, min_mid_v_ratio=0.95, min_mid_ratio=0.96, cond_evt_only_day_ratio=0.05, ae_mid_or_hi_early_day_ratio=0.9, mean_signal_count=3.0, max_signal_count=3.2, p95_recon_error=0.80),
        feature_row("beta", "beta.poslabel", "2025-01-06", "2025-01-06", run_day_count=2, run_shape_class="medium_alert_run", max_v_drop=0.85, min_mid_v_ratio=0.25, min_mid_ratio=0.30, cond_evt_only_day_ratio=0.85, ae_mid_or_hi_early_day_ratio=0.1, mean_signal_count=1.0, max_signal_count=1.2, p95_recon_error=0.15),
        feature_row("beta", "beta.monitor", "2025-01-07", "2025-01-10", run_day_count=4, run_shape_class="chronic_alert_run", max_v_drop=0.40, min_mid_v_ratio=0.68, min_mid_ratio=0.70, cond_evt_only_day_ratio=0.5, ae_mid_or_hi_early_day_ratio=0.45, mean_signal_count=2.0, max_signal_count=2.3, p95_recon_error=0.35),
        feature_row("beta", "beta.common", "2025-01-08", "2025-01-09", run_day_count=2, run_shape_class="medium_alert_run", max_v_drop=0.50, min_mid_v_ratio=0.60, min_mid_ratio=0.62, cond_evt_only_day_ratio=0.4, ae_mid_or_hi_early_day_ratio=0.40, mean_signal_count=1.8, max_signal_count=2.0, p95_recon_error=0.30),
        feature_row("beta", "beta.poscand", "2025-01-11", "2025-01-15", run_day_count=5, run_shape_class="chronic_alert_run", max_v_drop=0.70, min_mid_v_ratio=0.35, min_mid_ratio=0.38, cond_evt_only_day_ratio=0.72, ae_mid_or_hi_early_day_ratio=0.25, mean_signal_count=1.4, max_signal_count=1.8, p95_recon_error=0.28),
    ]
    labels = [
        label_row(features[0], "unlabeled_other", "exclude"),
        label_row(features[1], "unlabeled_other", "exclude"),
        label_row(features[2], "negative_like", "negative"),
        label_row(features[3], "positive_like", "positive"),
        label_row(features[4], "monitor_like", "exclude"),
        label_row(features[5], "common_cause_like", "exclude"),
        label_row(features[6], "unlabeled_other", "exclude"),
    ]
    scores = [
        score_row(features[0], 2.0, 2.5),
        score_row(features[1], 0.4, 0.3),
        score_row(features[2], 0.2, 0.1),
        score_row(features[3], 2.3, 2.8),
        score_row(features[4], 1.2, 1.4),
        score_row(features[5], 1.4, 1.6),
        score_row(features[6], 1.9, 2.2),
    ]
    holdout_summary = [
        {
            "score_name": "logistic_v2_holdout",
            "fold_type": "leave_one_site_out",
            "valid_fold_count": 2,
            "mean_labeled_test_auc": 0.72,
            "mean_labeled_test_average_precision": 0.75,
            "mean_top10_positive_minus_negative": 0.08,
            "mean_top20_positive_minus_negative": 0.03,
            "mean_top10_positive_like_count": 1.0,
            "mean_top10_negative_like_count": 0.2,
            "mean_top20_positive_like_count": 1.5,
            "mean_top20_negative_like_count": 0.8,
            "delta_mean_top10_positive_minus_negative_vs_v1": 0.02,
            "delta_mean_top20_positive_minus_negative_vs_v1": 0.01,
            "note": "baseline",
        },
        {
            "score_name": "logistic_v2_holdout",
            "fold_type": "time_holdout_70_30",
            "valid_fold_count": 1,
            "mean_labeled_test_auc": 0.70,
            "mean_labeled_test_average_precision": 0.71,
            "mean_top10_positive_minus_negative": 0.00,
            "mean_top20_positive_minus_negative": 0.00,
            "mean_top10_positive_like_count": 0.0,
            "mean_top10_negative_like_count": 0.0,
            "mean_top20_positive_like_count": 0.0,
            "mean_top20_negative_like_count": 0.0,
            "delta_mean_top10_positive_minus_negative_vs_v1": 0.00,
            "delta_mean_top20_positive_minus_negative_vs_v1": 0.00,
            "note": "baseline",
        },
    ]
    watch_now_panels = [{"site": "alpha", "panel_id": "alpha.poscand"}]
    watchlist_review = [{"site": "beta", "panel_id": "beta.poscand", "run_start_date": "2025-01-11", "run_end_date": "2025-01-15"}]
    common_cause = [{"eval_bucket_v2": "non_panel_or_common_cause", "site": "beta", "panel_id": "beta.common", "combined_marker_flag": 1}]

    write_csv(tmp_root / "_share" / "panel_day_engine_run_feature_table_v1.csv", features, FEATURE_TABLE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_label_pack_v2.csv", labels, LABEL_PACK_V2_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v0_scores.csv", scores, V0_SCORE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v2_holdout_summary.csv", holdout_summary, HOLDOUT_SUMMARY_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_operator_run_watchlist_now_panels_v1.csv", watch_now_panels, WATCH_NOW_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_operator_run_watchlist_review_v1.csv", watchlist_review, WATCHLIST_REVIEW_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv", common_cause, COMMON_CAUSE_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_run_label_expansion_audit_v1.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_run_label_expansion_candidates_v1.csv",
        repo_root / "_share" / "panel_day_engine_run_label_expansion_summary_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "pv_ae/panel_day_engine.py",
            "research/prognostics/build_panel_day_engine_run_label_expansion_audit_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_run_label_expansion_audit_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="run_label_expansion_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        candidates = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_label_expansion_candidates_v1.csv", encoding="utf-8-sig")
        summary = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_label_expansion_summary_v1.csv", encoding="utf-8-sig")

        assert_true(len(candidates) == 5, "expected one row per excluded run")

        alpha_pos = candidates.loc[candidates["panel_id"].eq("alpha.poscand")].iloc[0]
        assert_true(int(alpha_pos["site_positive_gap_flag"]) == 1, "alpha should have positive gap")
        assert_true(str(alpha_pos["candidate_class"]) == "positive_review_candidate", "alpha.poscand should be positive review")
        assert_true(str(alpha_pos["candidate_priority_band"]) == "P1", "alpha.poscand should be P1")
        assert_true(int(alpha_pos["watch_now_panel_ref_flag"]) == 1, "alpha.poscand should inherit watch-now panel ref")

        beta_pos = candidates.loc[candidates["panel_id"].eq("beta.poscand")].iloc[0]
        assert_true(int(beta_pos["site_positive_gap_flag"]) == 0, "beta should not have positive gap")
        assert_true(str(beta_pos["candidate_class"]) == "positive_review_candidate", "beta.poscand should be positive review")
        assert_true(str(beta_pos["candidate_priority_band"]) == "P2", "beta.poscand should be P2")
        assert_true(int(beta_pos["watch_review_run_ref_flag"]) == 1, "beta.poscand should inherit watch-review ref")

        beta_monitor = candidates.loc[candidates["panel_id"].eq("beta.monitor")].iloc[0]
        assert_true(str(beta_monitor["candidate_class"]) == "monitor_review_candidate", "monitor row should map to monitor review")
        assert_true(str(beta_monitor["candidate_priority_band"]) == "P3", "monitor row should map to P3")

        beta_common = candidates.loc[candidates["panel_id"].eq("beta.common")].iloc[0]
        assert_true(str(beta_common["candidate_class"]) == "common_cause_review_candidate", "common cause row should map to common cause review")
        assert_true(str(beta_common["candidate_priority_band"]) == "P3", "common cause row should map to P3")
        assert_true(int(beta_common["common_cause_descriptive_ref_flag"]) == 1, "common cause descriptive ref missing")

        alpha_low = candidates.loc[candidates["panel_id"].eq("alpha.low")].iloc[0]
        assert_true(str(alpha_low["candidate_class"]) == "low_priority_unlabeled", "short unlabeled row should be low priority")
        assert_true(str(alpha_low["candidate_priority_band"]) == "P4", "short unlabeled row should be P4")

        overall = summary.loc[summary["record_type"].astype(str).eq("overall")].iloc[0]
        assert_true(int(overall["excluded_run_count"]) == 5, "overall excluded count mismatch")
        assert_true(int(overall["positive_review_candidate_count"]) == 2, "positive review count mismatch")
        assert_true(int(overall["monitor_review_candidate_count"]) == 1, "monitor review count mismatch")
        assert_true(int(overall["common_cause_review_candidate_count"]) == 1, "common cause review count mismatch")
        assert_true(int(overall["low_priority_unlabeled_count"]) == 1, "low priority count mismatch")
        assert_true(int(overall["p1_count"]) == 1, "P1 count mismatch")
        assert_true(int(overall["p2_count"]) == 1, "P2 count mismatch")
        assert_true(int(overall["p3_count"]) == 2, "P3 count mismatch")
        assert_true(int(overall["p4_count"]) == 1, "P4 count mismatch")
        assert_true(int(overall["site_positive_gap_flag"]) == 1, "overall positive gap flag should reflect any site gap")
        assert_true(int(overall["site_negative_gap_flag"]) == 1, "overall negative gap flag should reflect any site gap")
        assert_true(abs(float(overall["logistic_v2_loso_delta_top20_vs_v1"]) - 0.01) < 1e-9, "LOSO delta context mismatch")

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
