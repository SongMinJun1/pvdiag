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
V1_SUMMARY_COLS = [
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
    "note",
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
        "run_shape_class": "short_alert_run",
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


def v0_row(feature: dict[str, object], score: float) -> dict[str, object]:
    return {
        "site": feature["site"],
        "panel_id": feature["panel_id"],
        "run_start_date": feature["run_start_date"],
        "run_end_date": feature["run_end_date"],
        "run_day_count": feature["run_day_count"],
        "run_shape_class": feature["run_shape_class"],
        "cohort_hint": feature["cohort_hint"],
        "electrical_core_score": score,
        "electrical_evt_score": score,
        "electrical_evt_minus_broadshape_score": score - 0.05,
        "electrical_core_minus_broadshape_025": score - 0.05,
        "electrical_core_minus_broadshape_050": score - 0.10,
        "electrical_core_minus_broadshape_075": score - 0.15,
        "electrical_core_plus_evtonly_minus_broadshape_025": score - 0.05,
        "electrical_core_plus_evtonly_minus_broadshape_050": score - 0.10,
    }


def build_fixture_root(tmp_root: Path) -> None:
    features = [
        feature_row("alpha", "alpha.pos.1", "2025-01-01", run_day_count=3, max_v_drop=0.90, min_mid_v_ratio=0.22, min_mid_ratio=0.28, cond_evt_only_day_ratio=0.86, ae_mid_or_hi_early_day_ratio=0.10, mean_signal_count=1.0, max_signal_count=1.1, p95_recon_error=0.12),
        feature_row("alpha", "alpha.other.1", "2025-01-02", run_day_count=2, max_v_drop=0.35, min_mid_v_ratio=0.75, min_mid_ratio=0.78, cond_evt_only_day_ratio=0.42, ae_mid_or_hi_early_day_ratio=0.48, mean_signal_count=2.1, max_signal_count=2.4, p95_recon_error=0.42),
        feature_row("alpha", "alpha.monitor.1", "2025-01-03", run_day_count=2, max_v_drop=0.40, min_mid_v_ratio=0.70, min_mid_ratio=0.74, cond_evt_only_day_ratio=0.50, ae_mid_or_hi_early_day_ratio=0.52, mean_signal_count=2.2, max_signal_count=2.5, p95_recon_error=0.45),
        feature_row("beta", "beta.pos.1", "2025-01-04", run_day_count=3, max_v_drop=0.82, min_mid_v_ratio=0.29, min_mid_ratio=0.34, cond_evt_only_day_ratio=0.80, ae_mid_or_hi_early_day_ratio=0.14, mean_signal_count=1.1, max_signal_count=1.3, p95_recon_error=0.16),
        feature_row("beta", "beta.common.1", "2025-01-05", run_day_count=2, max_v_drop=0.45, min_mid_v_ratio=0.68, min_mid_ratio=0.70, cond_evt_only_day_ratio=0.52, ae_mid_or_hi_early_day_ratio=0.50, mean_signal_count=2.0, max_signal_count=2.2, p95_recon_error=0.40),
        feature_row("beta", "beta.other.1", "2025-01-06", run_day_count=2, max_v_drop=0.33, min_mid_v_ratio=0.76, min_mid_ratio=0.77, cond_evt_only_day_ratio=0.38, ae_mid_or_hi_early_day_ratio=0.55, mean_signal_count=2.3, max_signal_count=2.6, p95_recon_error=0.44),
        feature_row("gamma", "gamma.neg.1", "2025-01-07", run_day_count=3, max_v_drop=0.12, min_mid_v_ratio=0.93, min_mid_ratio=0.91, cond_evt_only_day_ratio=0.08, ae_mid_or_hi_early_day_ratio=0.92, mean_signal_count=3.6, max_signal_count=4.0, p95_recon_error=0.86),
        feature_row("beta", "beta.pos.2", "2025-01-08", run_day_count=3, max_v_drop=0.78, min_mid_v_ratio=0.31, min_mid_ratio=0.36, cond_evt_only_day_ratio=0.81, ae_mid_or_hi_early_day_ratio=0.12, mean_signal_count=1.0, max_signal_count=1.3, p95_recon_error=0.18),
        feature_row("alpha", "alpha.other.2", "2025-01-09", run_day_count=2, max_v_drop=0.34, min_mid_v_ratio=0.74, min_mid_ratio=0.76, cond_evt_only_day_ratio=0.40, ae_mid_or_hi_early_day_ratio=0.49, mean_signal_count=2.2, max_signal_count=2.4, p95_recon_error=0.43),
        feature_row("gamma", "gamma.neg.2", "2025-01-10", run_day_count=3, max_v_drop=0.10, min_mid_v_ratio=0.95, min_mid_ratio=0.93, cond_evt_only_day_ratio=0.06, ae_mid_or_hi_early_day_ratio=0.94, mean_signal_count=3.8, max_signal_count=4.2, p95_recon_error=0.90),
        feature_row("beta", "beta.pos.3", "2025-01-11", run_day_count=3, max_v_drop=0.84, min_mid_v_ratio=0.27, min_mid_ratio=0.31, cond_evt_only_day_ratio=0.84, ae_mid_or_hi_early_day_ratio=0.11, mean_signal_count=1.0, max_signal_count=1.2, p95_recon_error=0.14),
        feature_row("alpha", "alpha.pos.2", "2025-01-12", run_day_count=3, max_v_drop=0.88, min_mid_v_ratio=0.24, min_mid_ratio=0.29, cond_evt_only_day_ratio=0.86, ae_mid_or_hi_early_day_ratio=0.10, mean_signal_count=1.0, max_signal_count=1.1, p95_recon_error=0.11),
    ]
    labels = [
        label_row(features[0], "positive_like", "positive"),
        label_row(features[1], "unlabeled_other", "exclude"),
        label_row(features[2], "monitor_like", "exclude"),
        label_row(features[3], "positive_like", "positive"),
        label_row(features[4], "common_cause_like", "exclude"),
        label_row(features[5], "unlabeled_other", "exclude"),
        label_row(features[6], "negative_like", "negative"),
        label_row(features[7], "positive_like", "positive"),
        label_row(features[8], "unlabeled_other", "exclude"),
        label_row(features[9], "negative_like", "negative"),
        label_row(features[10], "positive_like", "positive"),
        label_row(features[11], "positive_like", "positive"),
    ]
    v0_rows = []
    for row, label in zip(features, labels):
        if label["label_bucket_v2"] == "positive_like":
            score = 0.80
        elif label["label_bucket_v2"] == "negative_like":
            score = 0.20
        elif label["label_bucket_v2"] == "common_cause_like":
            score = 0.42
        else:
            score = 0.50
        v0_rows.append(v0_row(row, score))

    v1_summary_rows = [
        {
            "score_name": "logistic_v1_holdout",
            "fold_type": "leave_one_site_out",
            "valid_fold_count": 2,
            "mean_labeled_test_auc": 0.60,
            "mean_labeled_test_average_precision": 0.62,
            "mean_top10_positive_minus_negative": 0.05,
            "mean_top20_positive_minus_negative": 0.02,
            "mean_top10_positive_like_count": 1.0,
            "mean_top10_negative_like_count": 0.5,
            "mean_top20_positive_like_count": 1.5,
            "mean_top20_negative_like_count": 1.0,
            "note": "baseline",
        },
        {
            "score_name": "logistic_v1_holdout",
            "fold_type": "time_holdout_70_30",
            "valid_fold_count": 1,
            "mean_labeled_test_auc": 0.65,
            "mean_labeled_test_average_precision": 0.66,
            "mean_top10_positive_minus_negative": 0.00,
            "mean_top20_positive_minus_negative": 0.01,
            "mean_top10_positive_like_count": 0.0,
            "mean_top10_negative_like_count": 0.0,
            "mean_top20_positive_like_count": 0.0,
            "mean_top20_negative_like_count": 0.0,
            "note": "baseline",
        },
        {
            "score_name": "electrical_core_score",
            "fold_type": "leave_one_site_out",
            "valid_fold_count": 2,
            "mean_labeled_test_auc": 0.70,
            "mean_labeled_test_average_precision": 0.72,
            "mean_top10_positive_minus_negative": 0.10,
            "mean_top20_positive_minus_negative": 0.05,
            "mean_top10_positive_like_count": 1.0,
            "mean_top10_negative_like_count": 0.0,
            "mean_top20_positive_like_count": 1.5,
            "mean_top20_negative_like_count": 0.5,
            "note": "baseline",
        },
        {
            "score_name": "electrical_core_score",
            "fold_type": "time_holdout_70_30",
            "valid_fold_count": 1,
            "mean_labeled_test_auc": 0.80,
            "mean_labeled_test_average_precision": 0.82,
            "mean_top10_positive_minus_negative": 0.00,
            "mean_top20_positive_minus_negative": 0.05,
            "mean_top10_positive_like_count": 0.0,
            "mean_top10_negative_like_count": 0.0,
            "mean_top20_positive_like_count": 1.0,
            "mean_top20_negative_like_count": 0.0,
            "note": "baseline",
        },
        {
            "score_name": "electrical_core_minus_broadshape_050",
            "fold_type": "leave_one_site_out",
            "valid_fold_count": 2,
            "mean_labeled_test_auc": 0.68,
            "mean_labeled_test_average_precision": 0.70,
            "mean_top10_positive_minus_negative": 0.08,
            "mean_top20_positive_minus_negative": 0.04,
            "mean_top10_positive_like_count": 1.0,
            "mean_top10_negative_like_count": 0.2,
            "mean_top20_positive_like_count": 1.5,
            "mean_top20_negative_like_count": 0.7,
            "note": "baseline",
        },
        {
            "score_name": "electrical_core_minus_broadshape_050",
            "fold_type": "time_holdout_70_30",
            "valid_fold_count": 1,
            "mean_labeled_test_auc": 0.78,
            "mean_labeled_test_average_precision": 0.79,
            "mean_top10_positive_minus_negative": 0.00,
            "mean_top20_positive_minus_negative": 0.03,
            "mean_top10_positive_like_count": 0.0,
            "mean_top10_negative_like_count": 0.0,
            "mean_top20_positive_like_count": 1.0,
            "mean_top20_negative_like_count": 0.0,
            "note": "baseline",
        },
    ]

    write_csv(tmp_root / "_share" / "panel_day_engine_run_feature_table_v1.csv", features, FEATURE_TABLE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_label_pack_v2.csv", labels, LABEL_PACK_V2_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v0_scores.csv", v0_rows, V0_SCORE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v1_holdout_summary.csv", v1_summary_rows, V1_SUMMARY_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_run_ranker_v2_holdout_audit.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_run_ranker_v2_holdout_fold_scores.csv",
        repo_root / "_share" / "panel_day_engine_run_ranker_v2_holdout_summary.csv",
        repo_root / "_share" / "panel_day_engine_run_ranker_v2_holdout_topk_yield.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    with tempfile.TemporaryDirectory(prefix="ranker_v2_holdout_smoke_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        compile_result = run(
            [
                sys.executable,
                "-m",
                "py_compile",
                "pv_ae/panel_day_engine.py",
                "research/prognostics/build_panel_day_engine_run_ranker_v2_holdout_audit.py",
                "research/prognostics/smoke_test_panel_day_engine_run_ranker_v2_holdout_audit.py",
            ],
            repo_root,
        )
        assert_true(compile_result.returncode == 0, compile_result.stderr)

        build_result = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_run_ranker_v2_holdout_audit.py",
                "--root",
                str(tmp_root),
            ],
            repo_root,
        )
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        share_dir = tmp_root / "_share"
        fold_scores = pd.read_csv(share_dir / "panel_day_engine_run_ranker_v2_holdout_fold_scores.csv")
        summary = pd.read_csv(share_dir / "panel_day_engine_run_ranker_v2_holdout_summary.csv")
        topk = pd.read_csv(share_dir / "panel_day_engine_run_ranker_v2_holdout_topk_yield.csv")

        expected_scores = {
            "logistic_v2_holdout",
            "electrical_core_score",
            "electrical_core_minus_broadshape_050",
        }
        assert_true(set(fold_scores["score_name"]) == expected_scores, "fold score names mismatch")
        assert_true(set(summary["score_name"]) == expected_scores, "summary score names mismatch")
        assert_true(set(topk["score_name"]) == expected_scores, "top-k score names mismatch")

        skipped = fold_scores.loc[
            (fold_scores["fold_type"] == "leave_one_site_out")
            & (fold_scores["fold_id"] == "gamma")
        ]
        assert_true(not skipped.empty, "expected skipped gamma fold")
        assert_true(
            skipped["skip_reason"].fillna("").eq("train_labeled_missing_class").all(),
            "gamma fold should be skipped for missing class",
        )

        valid_time = fold_scores.loc[
            (fold_scores["fold_type"] == "time_holdout_70_30")
            & (fold_scores["score_name"] == "logistic_v2_holdout")
        ]
        assert_true(len(valid_time) == 1, "expected one time holdout logistic row")
        time_row = valid_time.iloc[0]
        assert_true(pd.notna(time_row["labeled_test_auc"]), "time holdout AUC should be populated")
        assert_true(pd.notna(time_row["labeled_test_average_precision"]), "time holdout AP should be populated")

        time_topk10 = topk.loc[
            (topk["fold_type"] == "time_holdout_70_30")
            & (topk["fold_id"] == "time_holdout_70_30")
            & (topk["score_name"] == "logistic_v2_holdout")
            & (topk["top_k"] == 10)
        ]
        assert_true(len(time_topk10) == 1, "expected one time holdout top10 row")
        top10_row = time_topk10.iloc[0]
        expected_gap = float(top10_row["topk_positive_like_rate"]) - float(top10_row["topk_negative_like_rate"])
        assert_true(
            abs(float(top10_row["topk_positive_minus_negative"]) - expected_gap) < 1e-9,
            "top10 positive-minus-negative mismatch",
        )

        loso_summary = summary.loc[
            (summary["fold_type"] == "leave_one_site_out")
            & (summary["score_name"] == "logistic_v2_holdout")
        ]
        assert_true(len(loso_summary) == 1, "expected logistic LOSO summary row")
        assert_true(int(loso_summary.iloc[0]["valid_fold_count"]) == 2, "LOSO valid folds should exclude skipped fold")

        baseline_summary = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v1_holdout_summary.csv")
        logistic_loso = loso_summary.iloc[0]
        logistic_baseline = baseline_summary.loc[
            (baseline_summary["score_name"] == "logistic_v1_holdout")
            & (baseline_summary["fold_type"] == "leave_one_site_out")
        ].iloc[0]
        expected_delta_top10 = float(logistic_loso["mean_top10_positive_minus_negative"]) - float(
            logistic_baseline["mean_top10_positive_minus_negative"]
        )
        expected_delta_top20 = float(logistic_loso["mean_top20_positive_minus_negative"]) - float(
            logistic_baseline["mean_top20_positive_minus_negative"]
        )
        assert_true(
            abs(float(logistic_loso["delta_mean_top10_positive_minus_negative_vs_v1"]) - expected_delta_top10) < 1e-9,
            "logistic delta top10 mismatch",
        )
        assert_true(
            abs(float(logistic_loso["delta_mean_top20_positive_minus_negative_vs_v1"]) - expected_delta_top20) < 1e-9,
            "logistic delta top20 mismatch",
        )

        reference_loso = summary.loc[
            (summary["fold_type"] == "leave_one_site_out")
            & (summary["score_name"] == "electrical_core_score")
        ].iloc[0]
        reference_baseline = baseline_summary.loc[
            (baseline_summary["score_name"] == "electrical_core_score")
            & (baseline_summary["fold_type"] == "leave_one_site_out")
        ].iloc[0]
        expected_ref_delta = float(reference_loso["mean_top20_positive_minus_negative"]) - float(
            reference_baseline["mean_top20_positive_minus_negative"]
        )
        assert_true(
            abs(float(reference_loso["delta_mean_top20_positive_minus_negative_vs_v1"]) - expected_ref_delta) < 1e-9,
            "reference delta top20 mismatch",
        )

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
