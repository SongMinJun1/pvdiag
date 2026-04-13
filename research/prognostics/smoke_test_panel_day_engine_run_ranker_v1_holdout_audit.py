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
V1_SCORE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "cohort_hint",
    "logistic_v1_score",
    "hgb_v1_score",
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
    cohort_hint: str,
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
        "cohort_hint": cohort_hint,
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
        "future_fault_linked_flag": 1 if cohort_hint == "future_fault_linked" else 0,
        "future_truth_linked_flag": 0,
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
        "electrical_evt_minus_broadshape_score": score - 0.1,
        "electrical_core_minus_broadshape_025": score - 0.1,
        "electrical_core_minus_broadshape_050": score - 0.2,
        "electrical_core_minus_broadshape_075": score - 0.3,
        "electrical_core_plus_evtonly_minus_broadshape_025": score - 0.1,
        "electrical_core_plus_evtonly_minus_broadshape_050": score - 0.2,
    }


def v1_row(feature: dict[str, object], score: float) -> dict[str, object]:
    return {
        "site": feature["site"],
        "panel_id": feature["panel_id"],
        "run_start_date": feature["run_start_date"],
        "run_end_date": feature["run_end_date"],
        "run_day_count": feature["run_day_count"],
        "run_shape_class": feature["run_shape_class"],
        "cohort_hint": feature["cohort_hint"],
        "logistic_v1_score": score,
        "hgb_v1_score": score,
        "electrical_core_score": score,
        "electrical_core_minus_broadshape_050": score - 0.2,
    }


def build_fixture_root(tmp_root: Path) -> None:
    features = [
        feature_row("alpha", "alpha.pos.1", "2025-01-01", "eligible_local", run_day_count=3, max_v_drop=0.85, min_mid_v_ratio=0.25, min_mid_ratio=0.30, cond_evt_only_day_ratio=0.85, ae_mid_or_hi_early_day_ratio=0.10, mean_signal_count=1.0, max_signal_count=1.2, p95_recon_error=0.12),
        feature_row("alpha", "alpha.other.1", "2025-01-02", "unmatched_other", run_day_count=2, max_v_drop=0.35, min_mid_v_ratio=0.75, min_mid_ratio=0.78, cond_evt_only_day_ratio=0.40, ae_mid_or_hi_early_day_ratio=0.45, mean_signal_count=2.0, max_signal_count=2.1, p95_recon_error=0.40),
        feature_row("alpha", "alpha.mon.1", "2025-01-03", "recurring_monitor_like", run_day_count=2, max_v_drop=0.38, min_mid_v_ratio=0.70, min_mid_ratio=0.74, cond_evt_only_day_ratio=0.48, ae_mid_or_hi_early_day_ratio=0.50, mean_signal_count=2.1, max_signal_count=2.3, p95_recon_error=0.42),
        feature_row("beta", "beta.pos.1", "2025-01-04", "future_fault_linked", run_day_count=3, max_v_drop=0.80, min_mid_v_ratio=0.28, min_mid_ratio=0.33, cond_evt_only_day_ratio=0.82, ae_mid_or_hi_early_day_ratio=0.12, mean_signal_count=1.1, max_signal_count=1.3, p95_recon_error=0.15),
        feature_row("beta", "beta.other.1", "2025-01-05", "unmatched_other", run_day_count=2, max_v_drop=0.32, min_mid_v_ratio=0.76, min_mid_ratio=0.77, cond_evt_only_day_ratio=0.35, ae_mid_or_hi_early_day_ratio=0.55, mean_signal_count=2.3, max_signal_count=2.5, p95_recon_error=0.45),
        feature_row("alpha", "alpha.mon.2", "2025-01-06", "recurring_monitor_like", run_day_count=2, max_v_drop=0.40, min_mid_v_ratio=0.69, min_mid_ratio=0.72, cond_evt_only_day_ratio=0.50, ae_mid_or_hi_early_day_ratio=0.52, mean_signal_count=2.0, max_signal_count=2.2, p95_recon_error=0.44),
        feature_row("gamma", "gamma.neg.1", "2025-01-07", "nuisance_alert", run_day_count=3, max_v_drop=0.12, min_mid_v_ratio=0.93, min_mid_ratio=0.91, cond_evt_only_day_ratio=0.08, ae_mid_or_hi_early_day_ratio=0.92, mean_signal_count=3.7, max_signal_count=4.0, p95_recon_error=0.86),
        feature_row("beta", "beta.pos.2", "2025-01-08", "eligible_local", run_day_count=3, max_v_drop=0.78, min_mid_v_ratio=0.30, min_mid_ratio=0.35, cond_evt_only_day_ratio=0.80, ae_mid_or_hi_early_day_ratio=0.14, mean_signal_count=1.2, max_signal_count=1.4, p95_recon_error=0.18),
        feature_row("alpha", "alpha.other.2", "2025-01-09", "unmatched_other", run_day_count=2, max_v_drop=0.34, min_mid_v_ratio=0.74, min_mid_ratio=0.75, cond_evt_only_day_ratio=0.42, ae_mid_or_hi_early_day_ratio=0.48, mean_signal_count=2.2, max_signal_count=2.4, p95_recon_error=0.43),
        feature_row("gamma", "gamma.neg.2", "2025-01-10", "isolated_unexplained", run_day_count=3, max_v_drop=0.10, min_mid_v_ratio=0.95, min_mid_ratio=0.93, cond_evt_only_day_ratio=0.06, ae_mid_or_hi_early_day_ratio=0.94, mean_signal_count=3.8, max_signal_count=4.2, p95_recon_error=0.90),
        feature_row("beta", "beta.pos.3", "2025-01-11", "future_fault_linked", run_day_count=3, max_v_drop=0.82, min_mid_v_ratio=0.27, min_mid_ratio=0.31, cond_evt_only_day_ratio=0.84, ae_mid_or_hi_early_day_ratio=0.11, mean_signal_count=1.0, max_signal_count=1.2, p95_recon_error=0.14),
        feature_row("alpha", "alpha.pos.2", "2025-01-12", "eligible_local", run_day_count=3, max_v_drop=0.88, min_mid_v_ratio=0.24, min_mid_ratio=0.29, cond_evt_only_day_ratio=0.86, ae_mid_or_hi_early_day_ratio=0.10, mean_signal_count=1.0, max_signal_count=1.1, p95_recon_error=0.11),
    ]

    v0_rows = []
    v1_rows = []
    for row in features:
        is_positive = row["cohort_hint"] in {"eligible_local", "future_fault_linked"}
        is_negative = row["cohort_hint"] in {"nuisance_alert", "isolated_unexplained"}
        v0_score = 0.9 if is_positive else (0.2 if is_negative else 0.5)
        v1_score = 0.92 if is_positive else (0.12 if is_negative else 0.55)
        v0_rows.append(v0_row(row, v0_score))
        v1_rows.append(v1_row(row, v1_score))

    write_csv(tmp_root / "_share" / "panel_day_engine_run_feature_table_v1.csv", features, FEATURE_TABLE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v0_scores.csv", v0_rows, V0_SCORE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v1_scores.csv", v1_rows, V1_SCORE_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="ranker_v1_holdout_smoke_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        compile_result = run(
            [
                sys.executable,
                "-m",
                "py_compile",
                "research/prognostics/build_panel_day_engine_run_ranker_v1_holdout_audit.py",
                "research/prognostics/smoke_test_panel_day_engine_run_ranker_v1_holdout_audit.py",
            ],
            repo_root,
        )
        assert_true(compile_result.returncode == 0, compile_result.stderr)

        build_result = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_run_ranker_v1_holdout_audit.py",
                "--root",
                str(tmp_root),
            ],
            repo_root,
        )
        assert_true(build_result.returncode == 0, build_result.stderr)

        share_dir = tmp_root / "_share"
        fold_scores_path = share_dir / "panel_day_engine_run_ranker_v1_holdout_fold_scores.csv"
        summary_path = share_dir / "panel_day_engine_run_ranker_v1_holdout_summary.csv"
        topk_path = share_dir / "panel_day_engine_run_ranker_v1_holdout_topk_yield.csv"
        assert_true(fold_scores_path.exists(), "missing fold score output")
        assert_true(summary_path.exists(), "missing summary output")
        assert_true(topk_path.exists(), "missing top-k output")

        fold_scores = pd.read_csv(fold_scores_path)
        summary = pd.read_csv(summary_path)
        topk = pd.read_csv(topk_path)

        expected_scores = {
            "logistic_v1_holdout",
            "electrical_core_score",
            "electrical_core_minus_broadshape_050",
        }
        assert_true(set(fold_scores["score_name"]) == expected_scores, "score names mismatch in fold scores")
        assert_true(set(summary["score_name"]) == expected_scores, "score names mismatch in summary")
        assert_true(set(topk["score_name"]) == expected_scores, "score names mismatch in top-k output")

        skipped = fold_scores.loc[
            (fold_scores["fold_type"] == "leave_one_site_out")
            & (fold_scores["fold_id"] == "gamma")
        ]
        assert_true(not skipped.empty, "expected skipped gamma fold")
        assert_true(
            skipped["skip_reason"].fillna("").eq("train_labeled_missing_class").all(),
            "skip reason should record insufficient labels",
        )

        valid_time = fold_scores.loc[
            (fold_scores["fold_type"] == "time_holdout_70_30")
            & (fold_scores["score_name"] == "logistic_v1_holdout")
        ]
        assert_true(len(valid_time) == 1, "expected one time holdout logistic row")
        time_row = valid_time.iloc[0]
        assert_true(pd.notna(time_row["labeled_test_auc"]), "time holdout AUC should be populated")
        assert_true(pd.notna(time_row["labeled_test_average_precision"]), "time holdout AP should be populated")

        time_topk10 = topk.loc[
            (topk["fold_type"] == "time_holdout_70_30")
            & (topk["fold_id"] == "time_holdout_70_30")
            & (topk["score_name"] == "logistic_v1_holdout")
            & (topk["top_k"] == 10)
        ]
        assert_true(len(time_topk10) == 1, "expected one time holdout top10 row")
        top10_row = time_topk10.iloc[0]
        assert_true(
            int(top10_row["topk_positive_like_count"]) == int(time_row["top10_positive_like_count"]),
            "top10 positive count mismatch",
        )
        assert_true(
            int(top10_row["topk_negative_like_count"]) == int(time_row["top10_negative_like_count"]),
            "top10 negative count mismatch",
        )
        expected_gap = float(top10_row["topk_positive_like_rate"]) - float(top10_row["topk_negative_like_rate"])
        assert_true(
            abs(float(top10_row["top10_or_20_positive_minus_negative"]) - expected_gap) < 1e-9,
            "top10 positive-minus-negative mismatch",
        )

        loso_summary = summary.loc[
            (summary["fold_type"] == "leave_one_site_out")
            & (summary["score_name"] == "logistic_v1_holdout")
        ]
        assert_true(len(loso_summary) == 1, "expected logistic LOSO summary row")
        assert_true(int(loso_summary.iloc[0]["valid_fold_count"]) == 2, "LOSO valid fold count should exclude skipped fold")


if __name__ == "__main__":
    main()
