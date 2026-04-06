#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

import build_panel_day_engine_run_ranker_v2_holdout_audit as holdout_base

KEY_COLS = holdout_base.KEY_COLS
FEATURE_COLS = list(dict.fromkeys([*KEY_COLS, "run_day_count", "run_shape_class", *holdout_base.TRAIN_FEATURES]))
LABEL_PACK_V2_COLS = [
    *KEY_COLS,
    "label_bucket_v2",
    "training_label_v2",
    "label_confidence_v2",
    "label_sources_csv_v2",
    "label_reason_ko_v2",
]
CANDIDATE_COLS = [*KEY_COLS, "candidate_class"]
REVIEW_BATCH_COLS = [*KEY_COLS, "review_track"]
STRATEGY_COLS = ["recommended_strategy", "recommended_reason_ko"]
V0_COLS = [*KEY_COLS, "electrical_core_score", "electrical_core_minus_broadshape_050"]
V2_SUMMARY_COLS = [
    "score_name",
    "fold_type",
    "mean_top10_positive_minus_negative",
    "mean_top20_positive_minus_negative",
]


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
    row = {
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
        "cond_evt_same_day_early_corroborated_day_ratio": min(cond_evt_day_ratio, 0.6),
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
    return row


def build_fixture_root(tmp_root: Path) -> None:
    share_dir = tmp_root / "_share"

    feature_rows = [
        make_feature_row("alpha", "run.pos.a", "2026-01-01", "2026-01-03", run_shape_class="medium_alert_run", run_day_count=3, pre_ews_day_count=2, ews_warning_day_count=1, pre_alarm_day_count=1, max_signal_count=3, mean_signal_count=2.2, cond_evt_day_ratio=0.9, cond_evt_only_day_ratio=0.8, ae_mid_or_hi_early_day_ratio=0.9, p95_recon_error=0.08, max_v_drop=0.70, min_mid_ratio=0.40, min_mid_v_ratio=0.38),
        make_feature_row("alpha", "run.neg.a", "2026-01-04", "2026-01-06", run_shape_class="medium_alert_run", run_day_count=3, pre_ews_day_count=0, ews_warning_day_count=0, pre_alarm_day_count=0, max_signal_count=1, mean_signal_count=1.0, cond_evt_day_ratio=0.2, cond_evt_only_day_ratio=0.1, ae_mid_or_hi_early_day_ratio=0.2, p95_recon_error=0.02, max_v_drop=0.20, min_mid_ratio=0.82, min_mid_v_ratio=0.80),
        make_feature_row("alpha", "run.promote.a", "2026-01-07", "2026-01-08", run_shape_class="medium_alert_run", run_day_count=2, pre_ews_day_count=1, ews_warning_day_count=1, pre_alarm_day_count=0, max_signal_count=3, mean_signal_count=2.0, cond_evt_day_ratio=0.8, cond_evt_only_day_ratio=0.7, ae_mid_or_hi_early_day_ratio=0.8, p95_recon_error=0.07, max_v_drop=0.60, min_mid_ratio=0.45, min_mid_v_ratio=0.44),
        make_feature_row("alpha", "run.exclude.a", "2026-01-09", "2026-01-10", run_shape_class="short_alert_run", run_day_count=2, pre_ews_day_count=0, ews_warning_day_count=0, pre_alarm_day_count=0, max_signal_count=1, mean_signal_count=1.1, cond_evt_day_ratio=0.3, cond_evt_only_day_ratio=0.2, ae_mid_or_hi_early_day_ratio=0.3, p95_recon_error=0.03, max_v_drop=0.25, min_mid_ratio=0.76, min_mid_v_ratio=0.74),
        make_feature_row("beta", "run.pos.b", "2026-01-11", "2026-01-13", run_shape_class="medium_alert_run", run_day_count=3, pre_ews_day_count=2, ews_warning_day_count=1, pre_alarm_day_count=1, max_signal_count=3, mean_signal_count=2.1, cond_evt_day_ratio=0.85, cond_evt_only_day_ratio=0.75, ae_mid_or_hi_early_day_ratio=0.88, p95_recon_error=0.07, max_v_drop=0.68, min_mid_ratio=0.42, min_mid_v_ratio=0.40),
        make_feature_row("beta", "run.neg.b", "2026-01-14", "2026-01-16", run_shape_class="medium_alert_run", run_day_count=3, pre_ews_day_count=0, ews_warning_day_count=0, pre_alarm_day_count=0, max_signal_count=1, mean_signal_count=0.9, cond_evt_day_ratio=0.15, cond_evt_only_day_ratio=0.1, ae_mid_or_hi_early_day_ratio=0.2, p95_recon_error=0.02, max_v_drop=0.18, min_mid_ratio=0.84, min_mid_v_ratio=0.83),
        make_feature_row("beta", "run.candidate.only", "2026-01-17", "2026-01-19", run_shape_class="chronic_alert_run", run_day_count=3, pre_ews_day_count=1, ews_warning_day_count=1, pre_alarm_day_count=0, max_signal_count=3, mean_signal_count=1.9, cond_evt_day_ratio=0.75, cond_evt_only_day_ratio=0.68, ae_mid_or_hi_early_day_ratio=0.76, p95_recon_error=0.06, max_v_drop=0.55, min_mid_ratio=0.50, min_mid_v_ratio=0.49),
        make_feature_row("beta", "run.review.only", "2026-01-20", "2026-01-21", run_shape_class="short_alert_run", run_day_count=2, pre_ews_day_count=1, ews_warning_day_count=0, pre_alarm_day_count=0, max_signal_count=2, mean_signal_count=1.5, cond_evt_day_ratio=0.5, cond_evt_only_day_ratio=0.5, ae_mid_or_hi_early_day_ratio=0.55, p95_recon_error=0.05, max_v_drop=0.40, min_mid_ratio=0.58, min_mid_v_ratio=0.56),
        make_feature_row("gamma", "run.pos.c", "2026-01-22", "2026-01-24", run_shape_class="medium_alert_run", run_day_count=3, pre_ews_day_count=2, ews_warning_day_count=1, pre_alarm_day_count=1, max_signal_count=3, mean_signal_count=2.3, cond_evt_day_ratio=0.88, cond_evt_only_day_ratio=0.77, ae_mid_or_hi_early_day_ratio=0.90, p95_recon_error=0.09, max_v_drop=0.72, min_mid_ratio=0.39, min_mid_v_ratio=0.37),
        make_feature_row("gamma", "run.neg.c", "2026-01-25", "2026-01-27", run_shape_class="medium_alert_run", run_day_count=3, pre_ews_day_count=0, ews_warning_day_count=0, pre_alarm_day_count=0, max_signal_count=1, mean_signal_count=1.0, cond_evt_day_ratio=0.12, cond_evt_only_day_ratio=0.08, ae_mid_or_hi_early_day_ratio=0.18, p95_recon_error=0.02, max_v_drop=0.16, min_mid_ratio=0.85, min_mid_v_ratio=0.84),
        make_feature_row("gamma", "run.promote.c", "2026-01-28", "2026-01-30", run_shape_class="chronic_alert_run", run_day_count=3, pre_ews_day_count=2, ews_warning_day_count=1, pre_alarm_day_count=0, max_signal_count=3, mean_signal_count=2.0, cond_evt_day_ratio=0.78, cond_evt_only_day_ratio=0.69, ae_mid_or_hi_early_day_ratio=0.79, p95_recon_error=0.07, max_v_drop=0.58, min_mid_ratio=0.47, min_mid_v_ratio=0.46),
        make_feature_row("gamma", "run.exclude.c", "2026-01-31", "2026-02-01", run_shape_class="short_alert_run", run_day_count=2, pre_ews_day_count=0, ews_warning_day_count=0, pre_alarm_day_count=0, max_signal_count=1, mean_signal_count=1.1, cond_evt_day_ratio=0.25, cond_evt_only_day_ratio=0.2, ae_mid_or_hi_early_day_ratio=0.25, p95_recon_error=0.03, max_v_drop=0.22, min_mid_ratio=0.78, min_mid_v_ratio=0.76),
    ]
    write_csv(share_dir / "panel_day_engine_run_feature_table_v1.csv", feature_rows, FEATURE_COLS)

    label_rows = [
        {"site": "alpha", "panel_id": "run.pos.a", "run_start_date": "2026-01-01", "run_end_date": "2026-01-03", "label_bucket_v2": "positive_like", "training_label_v2": "positive", "label_confidence_v2": "strong", "label_sources_csv_v2": "eligible_local", "label_reason_ko_v2": "positive"},
        {"site": "alpha", "panel_id": "run.neg.a", "run_start_date": "2026-01-04", "run_end_date": "2026-01-06", "label_bucket_v2": "negative_like", "training_label_v2": "negative", "label_confidence_v2": "medium", "label_sources_csv_v2": "nuisance_alert", "label_reason_ko_v2": "negative"},
        {"site": "alpha", "panel_id": "run.promote.a", "run_start_date": "2026-01-07", "run_end_date": "2026-01-08", "label_bucket_v2": "unlabeled_other", "training_label_v2": "exclude", "label_confidence_v2": "weak", "label_sources_csv_v2": "unmatched_other", "label_reason_ko_v2": "exclude"},
        {"site": "alpha", "panel_id": "run.exclude.a", "run_start_date": "2026-01-09", "run_end_date": "2026-01-10", "label_bucket_v2": "unlabeled_other", "training_label_v2": "exclude", "label_confidence_v2": "weak", "label_sources_csv_v2": "unmatched_other", "label_reason_ko_v2": "exclude"},
        {"site": "beta", "panel_id": "run.pos.b", "run_start_date": "2026-01-11", "run_end_date": "2026-01-13", "label_bucket_v2": "positive_like", "training_label_v2": "positive", "label_confidence_v2": "strong", "label_sources_csv_v2": "future_fault_linked", "label_reason_ko_v2": "positive"},
        {"site": "beta", "panel_id": "run.neg.b", "run_start_date": "2026-01-14", "run_end_date": "2026-01-16", "label_bucket_v2": "negative_like", "training_label_v2": "negative", "label_confidence_v2": "medium", "label_sources_csv_v2": "isolated_unexplained", "label_reason_ko_v2": "negative"},
        {"site": "beta", "panel_id": "run.candidate.only", "run_start_date": "2026-01-17", "run_end_date": "2026-01-19", "label_bucket_v2": "unlabeled_other", "training_label_v2": "exclude", "label_confidence_v2": "weak", "label_sources_csv_v2": "unmatched_other", "label_reason_ko_v2": "exclude"},
        {"site": "beta", "panel_id": "run.review.only", "run_start_date": "2026-01-20", "run_end_date": "2026-01-21", "label_bucket_v2": "unlabeled_other", "training_label_v2": "exclude", "label_confidence_v2": "weak", "label_sources_csv_v2": "unmatched_other", "label_reason_ko_v2": "exclude"},
        {"site": "gamma", "panel_id": "run.pos.c", "run_start_date": "2026-01-22", "run_end_date": "2026-01-24", "label_bucket_v2": "positive_like", "training_label_v2": "positive", "label_confidence_v2": "strong", "label_sources_csv_v2": "future_truth_linked", "label_reason_ko_v2": "positive"},
        {"site": "gamma", "panel_id": "run.neg.c", "run_start_date": "2026-01-25", "run_end_date": "2026-01-27", "label_bucket_v2": "negative_like", "training_label_v2": "negative", "label_confidence_v2": "medium", "label_sources_csv_v2": "nuisance_alert", "label_reason_ko_v2": "negative"},
        {"site": "gamma", "panel_id": "run.promote.c", "run_start_date": "2026-01-28", "run_end_date": "2026-01-30", "label_bucket_v2": "unlabeled_other", "training_label_v2": "exclude", "label_confidence_v2": "weak", "label_sources_csv_v2": "unmatched_other", "label_reason_ko_v2": "exclude"},
        {"site": "gamma", "panel_id": "run.exclude.c", "run_start_date": "2026-01-31", "run_end_date": "2026-02-01", "label_bucket_v2": "unlabeled_other", "training_label_v2": "exclude", "label_confidence_v2": "weak", "label_sources_csv_v2": "unmatched_other", "label_reason_ko_v2": "exclude"},
    ]
    write_csv(share_dir / "panel_day_engine_run_label_pack_v2.csv", label_rows, LABEL_PACK_V2_COLS)

    candidate_rows = [
        {"site": "alpha", "panel_id": "run.promote.a", "run_start_date": "2026-01-07", "run_end_date": "2026-01-08", "candidate_class": "positive_promotion_candidate"},
        {"site": "gamma", "panel_id": "run.promote.c", "run_start_date": "2026-01-28", "run_end_date": "2026-01-30", "candidate_class": "positive_promotion_candidate"},
        {"site": "beta", "panel_id": "run.candidate.only", "run_start_date": "2026-01-17", "run_end_date": "2026-01-19", "candidate_class": "positive_promotion_candidate"},
        {"site": "alpha", "panel_id": "run.exclude.a", "run_start_date": "2026-01-09", "run_end_date": "2026-01-10", "candidate_class": "low_priority_unlabeled"},
    ]
    write_csv(share_dir / "panel_day_engine_run_boundary_label_expansion_candidates_v1.csv", candidate_rows, CANDIDATE_COLS)

    review_rows = [
        {"site": "alpha", "panel_id": "run.promote.a", "run_start_date": "2026-01-07", "run_end_date": "2026-01-08", "review_track": "positive_review_batch"},
        {"site": "gamma", "panel_id": "run.promote.c", "run_start_date": "2026-01-28", "run_end_date": "2026-01-30", "review_track": "positive_review_batch"},
        {"site": "beta", "panel_id": "run.review.only", "run_start_date": "2026-01-20", "run_end_date": "2026-01-21", "review_track": "positive_review_batch"},
    ]
    write_csv(share_dir / "panel_day_engine_run_label_expansion_review_batch_v1.csv", review_rows, REVIEW_BATCH_COLS)

    strategy_rows = [
        {
            "recommended_strategy": "use_boundary_intersection_with_review_batch",
            "recommended_reason_ko": "synthetic recommended strategy",
        }
    ]
    write_csv(share_dir / "panel_day_engine_run_boundary_distance_hygiene_strategy_v1.csv", strategy_rows, STRATEGY_COLS)

    v0_rows = [
        {"site": "alpha", "panel_id": "run.pos.a", "run_start_date": "2026-01-01", "run_end_date": "2026-01-03", "electrical_core_score": 8.0, "electrical_core_minus_broadshape_050": 8.5},
        {"site": "alpha", "panel_id": "run.neg.a", "run_start_date": "2026-01-04", "run_end_date": "2026-01-06", "electrical_core_score": 2.0, "electrical_core_minus_broadshape_050": 2.2},
        {"site": "alpha", "panel_id": "run.promote.a", "run_start_date": "2026-01-07", "run_end_date": "2026-01-08", "electrical_core_score": 7.0, "electrical_core_minus_broadshape_050": 7.3},
        {"site": "alpha", "panel_id": "run.exclude.a", "run_start_date": "2026-01-09", "run_end_date": "2026-01-10", "electrical_core_score": 3.0, "electrical_core_minus_broadshape_050": 3.2},
        {"site": "beta", "panel_id": "run.pos.b", "run_start_date": "2026-01-11", "run_end_date": "2026-01-13", "electrical_core_score": 7.8, "electrical_core_minus_broadshape_050": 8.2},
        {"site": "beta", "panel_id": "run.neg.b", "run_start_date": "2026-01-14", "run_end_date": "2026-01-16", "electrical_core_score": 1.8, "electrical_core_minus_broadshape_050": 2.0},
        {"site": "beta", "panel_id": "run.candidate.only", "run_start_date": "2026-01-17", "run_end_date": "2026-01-19", "electrical_core_score": 6.8, "electrical_core_minus_broadshape_050": 7.1},
        {"site": "beta", "panel_id": "run.review.only", "run_start_date": "2026-01-20", "run_end_date": "2026-01-21", "electrical_core_score": 4.8, "electrical_core_minus_broadshape_050": 5.0},
        {"site": "gamma", "panel_id": "run.pos.c", "run_start_date": "2026-01-22", "run_end_date": "2026-01-24", "electrical_core_score": 8.1, "electrical_core_minus_broadshape_050": 8.6},
        {"site": "gamma", "panel_id": "run.neg.c", "run_start_date": "2026-01-25", "run_end_date": "2026-01-27", "electrical_core_score": 1.7, "electrical_core_minus_broadshape_050": 1.9},
        {"site": "gamma", "panel_id": "run.promote.c", "run_start_date": "2026-01-28", "run_end_date": "2026-01-30", "electrical_core_score": 7.2, "electrical_core_minus_broadshape_050": 7.4},
        {"site": "gamma", "panel_id": "run.exclude.c", "run_start_date": "2026-01-31", "run_end_date": "2026-02-01", "electrical_core_score": 2.8, "electrical_core_minus_broadshape_050": 3.0},
    ]
    write_csv(share_dir / "panel_day_engine_run_ranker_v0_scores.csv", v0_rows, V0_COLS)

    v2_summary_rows = [
        {"score_name": "logistic_v2_holdout", "fold_type": "leave_one_site_out", "mean_top10_positive_minus_negative": 0.10, "mean_top20_positive_minus_negative": 0.05},
        {"score_name": "logistic_v2_holdout", "fold_type": "time_holdout_70_30", "mean_top10_positive_minus_negative": 0.05, "mean_top20_positive_minus_negative": 0.02},
        {"score_name": "electrical_core_minus_broadshape_050", "fold_type": "leave_one_site_out", "mean_top10_positive_minus_negative": 0.15, "mean_top20_positive_minus_negative": 0.10},
        {"score_name": "electrical_core_minus_broadshape_050", "fold_type": "time_holdout_70_30", "mean_top10_positive_minus_negative": 0.08, "mean_top20_positive_minus_negative": 0.04},
        {"score_name": "electrical_core_score", "fold_type": "leave_one_site_out", "mean_top10_positive_minus_negative": 0.12, "mean_top20_positive_minus_negative": 0.08},
        {"score_name": "electrical_core_score", "fold_type": "time_holdout_70_30", "mean_top10_positive_minus_negative": 0.06, "mean_top20_positive_minus_negative": 0.03},
    ]
    write_csv(share_dir / "panel_day_engine_run_ranker_v2_holdout_summary.csv", v2_summary_rows, V2_SUMMARY_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research" / "prognostics" / "build_panel_day_engine_run_ranker_v3_intersection_holdout_audit.py"

    py_compile.compile(str(repo_root / "pv_ae" / "panel_day_engine.py"), doraise=True)
    py_compile.compile(str(builder), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="v3-intersection-holdout-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        result = run([sys.executable, str(builder), "--root", str(tmp_root)], cwd=repo_root)
        if result.returncode != 0:
            raise SystemExit(f"builder failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        label_pack_path = tmp_root / "_share" / "panel_day_engine_run_label_pack_v3_intersection.csv"
        summary_path = tmp_root / "_share" / "panel_day_engine_run_ranker_v3_intersection_holdout_summary.csv"
        topk_path = tmp_root / "_share" / "panel_day_engine_run_ranker_v3_intersection_holdout_topk_yield.csv"
        assert_true(label_pack_path.exists(), "missing v3 label pack output")
        assert_true(summary_path.exists(), "missing holdout summary output")
        assert_true(topk_path.exists(), "missing topk yield output")

        label_pack = pd.read_csv(label_pack_path, encoding="utf-8-sig")
        summary_df = pd.read_csv(summary_path, encoding="utf-8-sig")
        topk_df = pd.read_csv(topk_path, encoding="utf-8-sig")

        promoted = label_pack.loc[label_pack["promoted_intersection_positive_flag"].fillna(0).astype(int).eq(1)].copy()
        assert_true(len(promoted) == 2, "intersection promotion count should be 2")
        assert_true(set(promoted["panel_id"].astype(str)) == {"run.promote.a", "run.promote.c"}, "wrong promoted rows selected")
        assert_true(promoted["training_label_v3"].astype(str).eq("positive").all(), "promoted rows should become positive")
        assert_true(promoted["label_source_v3"].astype(str).eq("boundary_intersection_weak_positive").all(), "promoted source mismatch")

        carried = label_pack.loc[label_pack["panel_id"].astype(str).eq("run.neg.a")].iloc[0]
        assert_true(str(carried["training_label_v3"]) == "negative", "non-promoted row should carry through v2 label")
        assert_true(str(carried["label_bucket_v3"]) == "negative_like", "non-promoted bucket carry-through failed")

        assert_true(set(summary_df["score_name"].astype(str)) == {
            "logistic_v3_intersection_holdout",
            "electrical_core_score",
            "electrical_core_minus_broadshape_050",
        }, "unexpected score names in summary")
        assert_true(set(summary_df["fold_type"].astype(str)) == {"leave_one_site_out", "time_holdout_70_30"}, "unexpected fold types")
        assert_true(len(topk_df) > 0, "topk yield should not be empty")

        loso_logistic = summary_df.loc[
            (summary_df["score_name"].astype(str) == "logistic_v3_intersection_holdout")
            & (summary_df["fold_type"].astype(str) == "leave_one_site_out")
        ].iloc[0]
        expected_delta = float(loso_logistic["mean_top20_positive_minus_negative"]) - 0.05
        assert_true(
            round(float(loso_logistic["delta_mean_top20_vs_v2_logistic"]), 8) == round(expected_delta, 8),
            "delta vs v2 logistic should be computed from v2 summary baseline",
        )

        promoted_sites_csv = str(loso_logistic["promoted_sites_csv"])
        assert_true(promoted_sites_csv == "alpha,gamma", f"unexpected promoted_sites_csv: {promoted_sites_csv}")

        wrong_strategy = pd.DataFrame(
            [{"recommended_strategy": "use_review_batch_only", "recommended_reason_ko": "wrong for test"}]
        )
        wrong_strategy.to_csv(
            tmp_root / "_share" / "panel_day_engine_run_boundary_distance_hygiene_strategy_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )
        bad_result = run([sys.executable, str(builder), "--root", str(tmp_root)], cwd=repo_root)
        assert_true(bad_result.returncode != 0, "builder should fail when strategy is not intersection")
        combined_msg = f"{bad_result.stdout}\n{bad_result.stderr}"
        assert_true(
            "use_boundary_intersection_with_review_batch" in combined_msg,
            "strategy mismatch error should mention required strategy",
        )


if __name__ == "__main__":
    main()
