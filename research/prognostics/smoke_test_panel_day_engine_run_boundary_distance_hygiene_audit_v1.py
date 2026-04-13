#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

FEATURE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_shape_class",
    "run_day_count",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
]
LABEL_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "label_bucket_v2", "training_label_v2"]
GAP_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "label_bucket_v2",
    "gap_class",
    "electrical_core_minus_broadshape_050",
    "global_score_rank",
    "site_score_rank",
    "run_day_count",
    "run_shape_class",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
]
REVIEW_BATCH_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "review_track", "candidate_priority_band"]
V0_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "electrical_core_minus_broadshape_050"]


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
    run_shape_class: str,
    run_day_count: float,
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
        "run_shape_class": run_shape_class,
        "run_day_count": run_day_count,
        "max_v_drop": max_v_drop,
        "min_mid_v_ratio": min_mid_v_ratio,
        "min_mid_ratio": min_mid_ratio,
        "cond_evt_only_day_ratio": cond_evt_only_day_ratio,
        "ae_mid_or_hi_early_day_ratio": ae_mid_or_hi_early_day_ratio,
        "mean_signal_count": mean_signal_count,
        "max_signal_count": max_signal_count,
        "p95_recon_error": p95_recon_error,
    }


def gap_row(
    site: str,
    panel_id: str,
    start: str,
    end: str,
    *,
    label_bucket_v2: str,
    gap_class: str,
    score: float,
    global_rank: int,
    site_rank: int,
    run_shape_class: str,
    run_day_count: float,
    max_v_drop: float,
    min_mid_v_ratio: float,
    min_mid_ratio: float,
    cond_evt_only_day_ratio: float,
    ae_mid_or_hi_early_day_ratio: float,
    mean_signal_count: float,
    max_signal_count: float,
    p95_recon_error: float,
) -> dict[str, object]:
    row = feature_row(
        site,
        panel_id,
        start,
        end,
        run_shape_class=run_shape_class,
        run_day_count=run_day_count,
        max_v_drop=max_v_drop,
        min_mid_v_ratio=min_mid_v_ratio,
        min_mid_ratio=min_mid_ratio,
        cond_evt_only_day_ratio=cond_evt_only_day_ratio,
        ae_mid_or_hi_early_day_ratio=ae_mid_or_hi_early_day_ratio,
        mean_signal_count=mean_signal_count,
        max_signal_count=max_signal_count,
        p95_recon_error=p95_recon_error,
    )
    row.update(
        {
            "label_bucket_v2": label_bucket_v2,
            "gap_class": gap_class,
            "electrical_core_minus_broadshape_050": score,
            "global_score_rank": global_rank,
            "site_score_rank": site_rank,
        }
    )
    return row


def build_fixture_root(tmp_root: Path) -> None:
    share_dir = tmp_root / "_share"

    feature_rows: list[dict[str, object]] = [
        feature_row(
            "alpha",
            "proto_pos_a",
            "2026-01-01",
            "2026-01-05",
            run_shape_class="medium_alert_run",
            run_day_count=5,
            max_v_drop=0.58,
            min_mid_v_ratio=0.46,
            min_mid_ratio=0.49,
            cond_evt_only_day_ratio=0.82,
            ae_mid_or_hi_early_day_ratio=0.90,
            mean_signal_count=1.6,
            max_signal_count=3.0,
            p95_recon_error=0.020,
        ),
        feature_row(
            "beta",
            "proto_pos_b",
            "2026-01-06",
            "2026-01-14",
            run_shape_class="chronic_alert_run",
            run_day_count=9,
            max_v_drop=0.50,
            min_mid_v_ratio=0.53,
            min_mid_ratio=0.56,
            cond_evt_only_day_ratio=0.70,
            ae_mid_or_hi_early_day_ratio=0.82,
            mean_signal_count=1.4,
            max_signal_count=2.0,
            p95_recon_error=0.025,
        ),
        feature_row(
            "alpha",
            "proto_neg",
            "2026-01-15",
            "2026-01-30",
            run_shape_class="chronic_alert_run",
            run_day_count=16,
            max_v_drop=0.69,
            min_mid_v_ratio=0.32,
            min_mid_ratio=0.35,
            cond_evt_only_day_ratio=0.28,
            ae_mid_or_hi_early_day_ratio=1.00,
            mean_signal_count=2.2,
            max_signal_count=4.0,
            p95_recon_error=0.071,
        ),
        feature_row(
            "gamma",
            "cand_review",
            "2026-02-01",
            "2026-02-05",
            run_shape_class="medium_alert_run",
            run_day_count=5,
            max_v_drop=0.60,
            min_mid_v_ratio=0.44,
            min_mid_ratio=0.47,
            cond_evt_only_day_ratio=0.85,
            ae_mid_or_hi_early_day_ratio=0.92,
            mean_signal_count=1.8,
            max_signal_count=3.0,
            p95_recon_error=0.021,
        ),
        feature_row(
            "gamma",
            "cand_loose",
            "2026-02-07",
            "2026-02-12",
            run_shape_class="medium_alert_run",
            run_day_count=6,
            max_v_drop=0.56,
            min_mid_v_ratio=0.49,
            min_mid_ratio=0.52,
            cond_evt_only_day_ratio=0.68,
            ae_mid_or_hi_early_day_ratio=0.75,
            mean_signal_count=1.5,
            max_signal_count=3.0,
            p95_recon_error=0.028,
        ),
        feature_row(
            "alpha",
            "cand_outlier",
            "2026-02-15",
            "2026-02-19",
            run_shape_class="chronic_alert_run",
            run_day_count=250,
            max_v_drop=6.50,
            min_mid_v_ratio=0.20,
            min_mid_ratio=0.22,
            cond_evt_only_day_ratio=1.00,
            ae_mid_or_hi_early_day_ratio=1.00,
            mean_signal_count=20.0,
            max_signal_count=50.0,
            p95_recon_error=2.50,
        ),
        feature_row(
            "beta",
            "cand_monitor",
            "2026-02-20",
            "2026-02-24",
            run_shape_class="chronic_alert_run",
            run_day_count=5,
            max_v_drop=0.42,
            min_mid_v_ratio=0.62,
            min_mid_ratio=0.66,
            cond_evt_only_day_ratio=0.50,
            ae_mid_or_hi_early_day_ratio=0.60,
            mean_signal_count=1.1,
            max_signal_count=2.0,
            p95_recon_error=0.030,
        ),
        feature_row(
            "alpha",
            "cand_low",
            "2026-02-25",
            "2026-02-28",
            run_shape_class="short_alert_run",
            run_day_count=4,
            max_v_drop=0.18,
            min_mid_v_ratio=0.84,
            min_mid_ratio=0.86,
            cond_evt_only_day_ratio=0.08,
            ae_mid_or_hi_early_day_ratio=0.15,
            mean_signal_count=0.8,
            max_signal_count=1.0,
            p95_recon_error=0.011,
        ),
        feature_row(
            "alpha",
            "train_pos_a",
            "2026-01-31",
            "2026-02-03",
            run_shape_class="medium_alert_run",
            run_day_count=4,
            max_v_drop=0.60,
            min_mid_v_ratio=0.45,
            min_mid_ratio=0.48,
            cond_evt_only_day_ratio=0.76,
            ae_mid_or_hi_early_day_ratio=0.88,
            mean_signal_count=1.7,
            max_signal_count=3.0,
            p95_recon_error=0.021,
        ),
        feature_row(
            "alpha",
            "train_neg_a",
            "2026-02-04",
            "2026-02-08",
            run_shape_class="medium_alert_run",
            run_day_count=5,
            max_v_drop=0.25,
            min_mid_v_ratio=0.75,
            min_mid_ratio=0.79,
            cond_evt_only_day_ratio=0.16,
            ae_mid_or_hi_early_day_ratio=0.30,
            mean_signal_count=1.0,
            max_signal_count=2.0,
            p95_recon_error=0.016,
        ),
        feature_row(
            "beta",
            "train_pos_b",
            "2026-02-01",
            "2026-02-06",
            run_shape_class="medium_alert_run",
            run_day_count=6,
            max_v_drop=0.55,
            min_mid_v_ratio=0.50,
            min_mid_ratio=0.53,
            cond_evt_only_day_ratio=0.72,
            ae_mid_or_hi_early_day_ratio=0.82,
            mean_signal_count=1.4,
            max_signal_count=3.0,
            p95_recon_error=0.023,
        ),
        feature_row(
            "beta",
            "train_neg_b",
            "2026-02-08",
            "2026-02-12",
            run_shape_class="medium_alert_run",
            run_day_count=5,
            max_v_drop=0.24,
            min_mid_v_ratio=0.77,
            min_mid_ratio=0.80,
            cond_evt_only_day_ratio=0.12,
            ae_mid_or_hi_early_day_ratio=0.26,
            mean_signal_count=0.9,
            max_signal_count=2.0,
            p95_recon_error=0.015,
        ),
    ]
    write_csv(share_dir / "panel_day_engine_run_feature_table_v1.csv", feature_rows, FEATURE_COLS)

    label_rows = [
        {"site": "alpha", "panel_id": "proto_pos_a", "run_start_date": "2026-01-01", "run_end_date": "2026-01-05", "label_bucket_v2": "positive_like", "training_label_v2": "positive"},
        {"site": "beta", "panel_id": "proto_pos_b", "run_start_date": "2026-01-06", "run_end_date": "2026-01-14", "label_bucket_v2": "positive_like", "training_label_v2": "positive"},
        {"site": "alpha", "panel_id": "proto_neg", "run_start_date": "2026-01-15", "run_end_date": "2026-01-30", "label_bucket_v2": "negative_like", "training_label_v2": "negative"},
        {"site": "gamma", "panel_id": "cand_review", "run_start_date": "2026-02-01", "run_end_date": "2026-02-05", "label_bucket_v2": "unlabeled_other", "training_label_v2": "exclude"},
        {"site": "gamma", "panel_id": "cand_loose", "run_start_date": "2026-02-07", "run_end_date": "2026-02-12", "label_bucket_v2": "unlabeled_other", "training_label_v2": "exclude"},
        {"site": "alpha", "panel_id": "cand_outlier", "run_start_date": "2026-02-15", "run_end_date": "2026-02-19", "label_bucket_v2": "unlabeled_other", "training_label_v2": "exclude"},
        {"site": "beta", "panel_id": "cand_monitor", "run_start_date": "2026-02-20", "run_end_date": "2026-02-24", "label_bucket_v2": "monitor_like", "training_label_v2": "exclude"},
        {"site": "alpha", "panel_id": "cand_low", "run_start_date": "2026-02-25", "run_end_date": "2026-02-28", "label_bucket_v2": "unlabeled_other", "training_label_v2": "exclude"},
        {"site": "alpha", "panel_id": "train_pos_a", "run_start_date": "2026-01-31", "run_end_date": "2026-02-03", "label_bucket_v2": "positive_like", "training_label_v2": "positive"},
        {"site": "alpha", "panel_id": "train_neg_a", "run_start_date": "2026-02-04", "run_end_date": "2026-02-08", "label_bucket_v2": "negative_like", "training_label_v2": "negative"},
        {"site": "beta", "panel_id": "train_pos_b", "run_start_date": "2026-02-01", "run_end_date": "2026-02-06", "label_bucket_v2": "positive_like", "training_label_v2": "positive"},
        {"site": "beta", "panel_id": "train_neg_b", "run_start_date": "2026-02-08", "run_end_date": "2026-02-12", "label_bucket_v2": "negative_like", "training_label_v2": "negative"},
    ]
    write_csv(share_dir / "panel_day_engine_run_label_pack_v2.csv", label_rows, LABEL_COLS)

    gap_rows = [
        gap_row(
            "alpha",
            "proto_pos_a",
            "2026-01-01",
            "2026-01-05",
            label_bucket_v2="positive_like",
            gap_class="positive_top50_global_not_top20",
            score=10.0,
            global_rank=21,
            site_rank=5,
            run_shape_class="medium_alert_run",
            run_day_count=5,
            max_v_drop=0.58,
            min_mid_v_ratio=0.46,
            min_mid_ratio=0.49,
            cond_evt_only_day_ratio=0.82,
            ae_mid_or_hi_early_day_ratio=0.90,
            mean_signal_count=1.6,
            max_signal_count=3.0,
            p95_recon_error=0.020,
        ),
        gap_row(
            "beta",
            "proto_pos_b",
            "2026-01-06",
            "2026-01-14",
            label_bucket_v2="positive_like",
            gap_class="positive_below_top50_global",
            score=8.8,
            global_rank=58,
            site_rank=13,
            run_shape_class="chronic_alert_run",
            run_day_count=9,
            max_v_drop=0.50,
            min_mid_v_ratio=0.53,
            min_mid_ratio=0.56,
            cond_evt_only_day_ratio=0.70,
            ae_mid_or_hi_early_day_ratio=0.82,
            mean_signal_count=1.4,
            max_signal_count=2.0,
            p95_recon_error=0.025,
        ),
        gap_row(
            "alpha",
            "proto_neg",
            "2026-01-15",
            "2026-01-30",
            label_bucket_v2="negative_like",
            gap_class="negative_top20_global",
            score=12.5,
            global_rank=16,
            site_rank=3,
            run_shape_class="chronic_alert_run",
            run_day_count=16,
            max_v_drop=0.69,
            min_mid_v_ratio=0.32,
            min_mid_ratio=0.35,
            cond_evt_only_day_ratio=0.28,
            ae_mid_or_hi_early_day_ratio=1.00,
            mean_signal_count=2.2,
            max_signal_count=4.0,
            p95_recon_error=0.071,
        ),
    ]
    write_csv(share_dir / "panel_day_engine_run_ranker_reference_gap_cases_v1.csv", gap_rows, GAP_COLS)

    review_rows = [
        {
            "site": "gamma",
            "panel_id": "cand_review",
            "run_start_date": "2026-02-01",
            "run_end_date": "2026-02-05",
            "review_track": "positive_review_batch",
            "candidate_priority_band": "P1",
        }
    ]
    write_csv(share_dir / "panel_day_engine_run_label_expansion_review_batch_v1.csv", review_rows, REVIEW_BATCH_COLS)

    v0_rows = [
        {"site": "alpha", "panel_id": "proto_neg", "run_start_date": "2026-01-15", "run_end_date": "2026-01-30", "electrical_core_minus_broadshape_050": 12.5},
        {"site": "alpha", "panel_id": "cand_outlier", "run_start_date": "2026-02-15", "run_end_date": "2026-02-19", "electrical_core_minus_broadshape_050": 11.8},
        {"site": "gamma", "panel_id": "cand_review", "run_start_date": "2026-02-01", "run_end_date": "2026-02-05", "electrical_core_minus_broadshape_050": 10.6},
        {"site": "gamma", "panel_id": "cand_loose", "run_start_date": "2026-02-07", "run_end_date": "2026-02-12", "electrical_core_minus_broadshape_050": 10.1},
        {"site": "alpha", "panel_id": "proto_pos_a", "run_start_date": "2026-01-01", "run_end_date": "2026-01-05", "electrical_core_minus_broadshape_050": 9.5},
        {"site": "beta", "panel_id": "proto_pos_b", "run_start_date": "2026-01-06", "run_end_date": "2026-01-14", "electrical_core_minus_broadshape_050": 8.8},
        {"site": "beta", "panel_id": "cand_monitor", "run_start_date": "2026-02-20", "run_end_date": "2026-02-24", "electrical_core_minus_broadshape_050": 6.2},
        {"site": "alpha", "panel_id": "train_pos_a", "run_start_date": "2026-01-31", "run_end_date": "2026-02-03", "electrical_core_minus_broadshape_050": 6.0},
        {"site": "beta", "panel_id": "train_pos_b", "run_start_date": "2026-02-01", "run_end_date": "2026-02-06", "electrical_core_minus_broadshape_050": 5.7},
        {"site": "alpha", "panel_id": "train_neg_a", "run_start_date": "2026-02-04", "run_end_date": "2026-02-08", "electrical_core_minus_broadshape_050": 3.0},
        {"site": "beta", "panel_id": "train_neg_b", "run_start_date": "2026-02-08", "run_end_date": "2026-02-12", "electrical_core_minus_broadshape_050": 2.9},
        {"site": "alpha", "panel_id": "cand_low", "run_start_date": "2026-02-25", "run_end_date": "2026-02-28", "electrical_core_minus_broadshape_050": 1.1},
    ]
    write_csv(share_dir / "panel_day_engine_run_ranker_v0_scores.csv", v0_rows, V0_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    raw_builder = repo_root / "research" / "prognostics" / "build_panel_day_engine_run_boundary_label_expansion_audit_v1.py"
    hygiene_builder = repo_root / "research" / "prognostics" / "build_panel_day_engine_run_boundary_distance_hygiene_audit_v1.py"

    py_compile.compile(str(repo_root / "pv_ae" / "panel_day_engine.py"), doraise=True)
    py_compile.compile(str(raw_builder), doraise=True)
    py_compile.compile(str(hygiene_builder), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="boundary-distance-hygiene-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        raw_result = run([sys.executable, str(raw_builder), "--root", str(tmp_root)], cwd=repo_root)
        if raw_result.returncode != 0:
            raise SystemExit(f"raw builder failed\nSTDOUT:\n{raw_result.stdout}\nSTDERR:\n{raw_result.stderr}")

        hygiene_result = run([sys.executable, str(hygiene_builder), "--root", str(tmp_root)], cwd=repo_root)
        if hygiene_result.returncode != 0:
            raise SystemExit(f"hygiene builder failed\nSTDOUT:\n{hygiene_result.stdout}\nSTDERR:\n{hygiene_result.stderr}")

        summary_path = tmp_root / "_share" / "panel_day_engine_run_boundary_distance_hygiene_summary_v1.csv"
        outliers_path = tmp_root / "_share" / "panel_day_engine_run_boundary_distance_hygiene_outliers_v1.csv"
        strategy_path = tmp_root / "_share" / "panel_day_engine_run_boundary_distance_hygiene_strategy_v1.csv"
        assert_true(summary_path.exists(), "missing summary output")
        assert_true(outliers_path.exists(), "missing outliers output")
        assert_true(strategy_path.exists(), "missing strategy output")

        summary_df = pd.read_csv(summary_path, encoding="utf-8-sig")
        outliers_df = pd.read_csv(outliers_path, encoding="utf-8-sig")
        strategy_df = pd.read_csv(strategy_path, encoding="utf-8-sig")

        assert_true(set(summary_df["mode_name"].astype(str)) == {
            "raw_boundary",
            "clipped_global_boundary",
            "clipped_site_boundary",
            "boundary_intersection_with_review_batch",
        }, "mode rows missing")

        raw_row = summary_df.loc[summary_df["mode_name"].astype(str).eq("raw_boundary")].iloc[0]
        intersection_row = summary_df.loc[summary_df["mode_name"].astype(str).eq("boundary_intersection_with_review_batch")].iloc[0]
        clipped_global_row = summary_df.loc[summary_df["mode_name"].astype(str).eq("clipped_global_boundary")].iloc[0]

        assert_true(int(raw_row["raw_positive_promotion_candidate_count"]) >= 1, "raw positive count missing")
        assert_true(int(raw_row["candidate_universe_count"]) == 5, "candidate universe count mismatch")
        assert_true(int(intersection_row["positive_promotion_candidate_count"]) == 1, "review-batch intersection should keep one positive")
        assert_true(int(intersection_row["top50_overlap_with_review_batch"]) == 1, "intersection should overlap review batch")
        assert_true(int(clipped_global_row["candidate_count_reduction_vs_raw"]) >= 0, "reduction field should compute")

        outlier_panels = set(outliers_df["panel_id"].astype(str))
        assert_true("cand_outlier" in outlier_panels, "outlier detection should flag synthetic extreme run")

        assert_true(len(strategy_df) == 1, "strategy row missing")
        strategy = str(strategy_df.iloc[0]["recommended_strategy"])
        assert_true(strategy in {
            "use_clipped_global_boundary",
            "use_clipped_site_boundary",
            "use_boundary_intersection_with_review_batch",
            "use_review_batch_only",
        }, f"unexpected strategy: {strategy}")
        assert_true(
            strategy == "use_boundary_intersection_with_review_batch",
            f"synthetic fixture should recommend intersection fallback, got {strategy}",
        )


if __name__ == "__main__":
    main()
