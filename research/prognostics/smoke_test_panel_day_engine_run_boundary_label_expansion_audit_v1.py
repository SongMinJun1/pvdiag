#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
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
LABEL_COLS = [*KEY_COLS, "label_bucket_v2", "training_label_v2"]
GAP_COLS = [
    *KEY_COLS,
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
REVIEW_BATCH_COLS = [*KEY_COLS, "review_track", "candidate_priority_band"]
V0_COLS = [*KEY_COLS, "electrical_core_minus_broadshape_050"]


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

    feature_rows = [
        feature_row(
            "alpha",
            "proto_pos_a",
            "2026-01-01",
            "2026-01-05",
            run_shape_class="medium_alert_run",
            run_day_count=5,
            max_v_drop=0.60,
            min_mid_v_ratio=0.42,
            min_mid_ratio=0.48,
            cond_evt_only_day_ratio=0.80,
            ae_mid_or_hi_early_day_ratio=0.90,
            mean_signal_count=1.8,
            max_signal_count=3.0,
            p95_recon_error=0.020,
        ),
        feature_row(
            "beta",
            "proto_pos_b",
            "2026-01-10",
            "2026-01-20",
            run_shape_class="chronic_alert_run",
            run_day_count=11,
            max_v_drop=0.50,
            min_mid_v_ratio=0.53,
            min_mid_ratio=0.55,
            cond_evt_only_day_ratio=0.75,
            ae_mid_or_hi_early_day_ratio=0.85,
            mean_signal_count=1.4,
            max_signal_count=2.0,
            p95_recon_error=0.024,
        ),
        feature_row(
            "alpha",
            "proto_neg_a",
            "2026-02-01",
            "2026-02-20",
            run_shape_class="chronic_alert_run",
            run_day_count=20,
            max_v_drop=0.68,
            min_mid_v_ratio=0.31,
            min_mid_ratio=0.34,
            cond_evt_only_day_ratio=0.25,
            ae_mid_or_hi_early_day_ratio=1.00,
            mean_signal_count=2.2,
            max_signal_count=4.0,
            p95_recon_error=0.070,
        ),
        feature_row(
            "gamma",
            "cand_pos",
            "2026-03-01",
            "2026-03-05",
            run_shape_class="medium_alert_run",
            run_day_count=5,
            max_v_drop=0.58,
            min_mid_v_ratio=0.44,
            min_mid_ratio=0.47,
            cond_evt_only_day_ratio=0.82,
            ae_mid_or_hi_early_day_ratio=0.88,
            mean_signal_count=1.7,
            max_signal_count=3.0,
            p95_recon_error=0.021,
        ),
        feature_row(
            "alpha",
            "cand_neg",
            "2026-03-07",
            "2026-03-20",
            run_shape_class="chronic_alert_run",
            run_day_count=14,
            max_v_drop=0.70,
            min_mid_v_ratio=0.32,
            min_mid_ratio=0.35,
            cond_evt_only_day_ratio=0.20,
            ae_mid_or_hi_early_day_ratio=0.98,
            mean_signal_count=2.1,
            max_signal_count=4.0,
            p95_recon_error=0.068,
        ),
        feature_row(
            "beta",
            "cand_monitor",
            "2026-03-12",
            "2026-03-15",
            run_shape_class="chronic_alert_run",
            run_day_count=4,
            max_v_drop=0.40,
            min_mid_v_ratio=0.60,
            min_mid_ratio=0.64,
            cond_evt_only_day_ratio=0.55,
            ae_mid_or_hi_early_day_ratio=0.60,
            mean_signal_count=1.1,
            max_signal_count=2.0,
            p95_recon_error=0.030,
        ),
        feature_row(
            "alpha",
            "cand_low",
            "2026-03-21",
            "2026-03-24",
            run_shape_class="short_alert_run",
            run_day_count=18,
            max_v_drop=0.71,
            min_mid_v_ratio=0.30,
            min_mid_ratio=0.33,
            cond_evt_only_day_ratio=0.16,
            ae_mid_or_hi_early_day_ratio=1.00,
            mean_signal_count=2.3,
            max_signal_count=4.0,
            p95_recon_error=0.072,
        ),
        feature_row(
            "alpha",
            "train_pos_a",
            "2026-01-22",
            "2026-01-25",
            run_shape_class="medium_alert_run",
            run_day_count=4,
            max_v_drop=0.62,
            min_mid_v_ratio=0.41,
            min_mid_ratio=0.46,
            cond_evt_only_day_ratio=0.70,
            ae_mid_or_hi_early_day_ratio=0.92,
            mean_signal_count=1.9,
            max_signal_count=3.0,
            p95_recon_error=0.020,
        ),
        feature_row(
            "alpha",
            "train_neg_a",
            "2026-01-26",
            "2026-01-31",
            run_shape_class="medium_alert_run",
            run_day_count=6,
            max_v_drop=0.28,
            min_mid_v_ratio=0.74,
            min_mid_ratio=0.78,
            cond_evt_only_day_ratio=0.20,
            ae_mid_or_hi_early_day_ratio=0.35,
            mean_signal_count=1.0,
            max_signal_count=2.0,
            p95_recon_error=0.018,
        ),
        feature_row(
            "beta",
            "train_pos_b",
            "2026-01-22",
            "2026-01-30",
            run_shape_class="medium_alert_run",
            run_day_count=9,
            max_v_drop=0.56,
            min_mid_v_ratio=0.48,
            min_mid_ratio=0.50,
            cond_evt_only_day_ratio=0.72,
            ae_mid_or_hi_early_day_ratio=0.82,
            mean_signal_count=1.5,
            max_signal_count=3.0,
            p95_recon_error=0.022,
        ),
        feature_row(
            "beta",
            "train_neg_b",
            "2026-01-31",
            "2026-02-03",
            run_shape_class="medium_alert_run",
            run_day_count=4,
            max_v_drop=0.24,
            min_mid_v_ratio=0.77,
            min_mid_ratio=0.81,
            cond_evt_only_day_ratio=0.12,
            ae_mid_or_hi_early_day_ratio=0.28,
            mean_signal_count=1.0,
            max_signal_count=2.0,
            p95_recon_error=0.015,
        ),
    ]
    write_csv(share_dir / "panel_day_engine_run_feature_table_v1.csv", feature_rows, FEATURE_COLS)

    label_rows = [
        {"site": "alpha", "panel_id": "proto_pos_a", "run_start_date": "2026-01-01", "run_end_date": "2026-01-05", "label_bucket_v2": "positive_like", "training_label_v2": "positive"},
        {"site": "beta", "panel_id": "proto_pos_b", "run_start_date": "2026-01-10", "run_end_date": "2026-01-20", "label_bucket_v2": "positive_like", "training_label_v2": "positive"},
        {"site": "alpha", "panel_id": "proto_neg_a", "run_start_date": "2026-02-01", "run_end_date": "2026-02-20", "label_bucket_v2": "negative_like", "training_label_v2": "negative"},
        {"site": "gamma", "panel_id": "cand_pos", "run_start_date": "2026-03-01", "run_end_date": "2026-03-05", "label_bucket_v2": "unlabeled_other", "training_label_v2": "exclude"},
        {"site": "alpha", "panel_id": "cand_neg", "run_start_date": "2026-03-07", "run_end_date": "2026-03-20", "label_bucket_v2": "unlabeled_other", "training_label_v2": "exclude"},
        {"site": "beta", "panel_id": "cand_monitor", "run_start_date": "2026-03-12", "run_end_date": "2026-03-15", "label_bucket_v2": "monitor_like", "training_label_v2": "exclude"},
        {"site": "alpha", "panel_id": "cand_low", "run_start_date": "2026-03-21", "run_end_date": "2026-03-24", "label_bucket_v2": "unlabeled_other", "training_label_v2": "exclude"},
        {"site": "alpha", "panel_id": "train_pos_a", "run_start_date": "2026-01-22", "run_end_date": "2026-01-25", "label_bucket_v2": "positive_like", "training_label_v2": "positive"},
        {"site": "alpha", "panel_id": "train_neg_a", "run_start_date": "2026-01-26", "run_end_date": "2026-01-31", "label_bucket_v2": "negative_like", "training_label_v2": "negative"},
        {"site": "beta", "panel_id": "train_pos_b", "run_start_date": "2026-01-22", "run_end_date": "2026-01-30", "label_bucket_v2": "positive_like", "training_label_v2": "positive"},
        {"site": "beta", "panel_id": "train_neg_b", "run_start_date": "2026-01-31", "run_end_date": "2026-02-03", "label_bucket_v2": "negative_like", "training_label_v2": "negative"},
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
            score=9.0,
            global_rank=21,
            site_rank=5,
            run_shape_class="medium_alert_run",
            run_day_count=5,
            max_v_drop=0.60,
            min_mid_v_ratio=0.42,
            min_mid_ratio=0.48,
            cond_evt_only_day_ratio=0.80,
            ae_mid_or_hi_early_day_ratio=0.90,
            mean_signal_count=1.8,
            max_signal_count=3.0,
            p95_recon_error=0.020,
        ),
        gap_row(
            "beta",
            "proto_pos_b",
            "2026-01-10",
            "2026-01-20",
            label_bucket_v2="positive_like",
            gap_class="positive_below_top50_global",
            score=8.5,
            global_rank=57,
            site_rank=15,
            run_shape_class="chronic_alert_run",
            run_day_count=11,
            max_v_drop=0.50,
            min_mid_v_ratio=0.53,
            min_mid_ratio=0.55,
            cond_evt_only_day_ratio=0.75,
            ae_mid_or_hi_early_day_ratio=0.85,
            mean_signal_count=1.4,
            max_signal_count=2.0,
            p95_recon_error=0.024,
        ),
        gap_row(
            "alpha",
            "proto_neg_a",
            "2026-02-01",
            "2026-02-20",
            label_bucket_v2="negative_like",
            gap_class="negative_top20_global",
            score=9.8,
            global_rank=16,
            site_rank=3,
            run_shape_class="chronic_alert_run",
            run_day_count=20,
            max_v_drop=0.68,
            min_mid_v_ratio=0.31,
            min_mid_ratio=0.34,
            cond_evt_only_day_ratio=0.25,
            ae_mid_or_hi_early_day_ratio=1.00,
            mean_signal_count=2.2,
            max_signal_count=4.0,
            p95_recon_error=0.070,
        ),
    ]
    write_csv(share_dir / "panel_day_engine_run_ranker_reference_gap_cases_v1.csv", gap_rows, GAP_COLS)

    review_rows = [
        {
            "site": "gamma",
            "panel_id": "cand_pos",
            "run_start_date": "2026-03-01",
            "run_end_date": "2026-03-05",
            "review_track": "positive_review_batch",
            "candidate_priority_band": "P1",
        }
    ]
    write_csv(share_dir / "panel_day_engine_run_label_expansion_review_batch_v1.csv", review_rows, REVIEW_BATCH_COLS)

    score_rows = [
        {"site": "alpha", "panel_id": "proto_neg_a", "run_start_date": "2026-02-01", "run_end_date": "2026-02-20", "electrical_core_minus_broadshape_050": 10.0},
        {"site": "alpha", "panel_id": "cand_neg", "run_start_date": "2026-03-07", "run_end_date": "2026-03-20", "electrical_core_minus_broadshape_050": 9.7},
        {"site": "gamma", "panel_id": "cand_pos", "run_start_date": "2026-03-01", "run_end_date": "2026-03-05", "electrical_core_minus_broadshape_050": 9.4},
        {"site": "alpha", "panel_id": "proto_pos_a", "run_start_date": "2026-01-01", "run_end_date": "2026-01-05", "electrical_core_minus_broadshape_050": 8.8},
        {"site": "beta", "panel_id": "proto_pos_b", "run_start_date": "2026-01-10", "run_end_date": "2026-01-20", "electrical_core_minus_broadshape_050": 8.6},
        {"site": "beta", "panel_id": "cand_monitor", "run_start_date": "2026-03-12", "run_end_date": "2026-03-15", "electrical_core_minus_broadshape_050": 6.5},
        {"site": "alpha", "panel_id": "train_pos_a", "run_start_date": "2026-01-22", "run_end_date": "2026-01-25", "electrical_core_minus_broadshape_050": 6.2},
        {"site": "beta", "panel_id": "train_pos_b", "run_start_date": "2026-01-22", "run_end_date": "2026-01-30", "electrical_core_minus_broadshape_050": 5.8},
        {"site": "alpha", "panel_id": "train_neg_a", "run_start_date": "2026-01-26", "run_end_date": "2026-01-31", "electrical_core_minus_broadshape_050": 3.3},
        {"site": "beta", "panel_id": "train_neg_b", "run_start_date": "2026-01-31", "run_end_date": "2026-02-03", "electrical_core_minus_broadshape_050": 3.1},
        {"site": "alpha", "panel_id": "cand_low", "run_start_date": "2026-03-21", "run_end_date": "2026-03-24", "electrical_core_minus_broadshape_050": 1.0},
    ]
    write_csv(share_dir / "panel_day_engine_run_ranker_v0_scores.csv", score_rows, V0_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research" / "prognostics" / "build_panel_day_engine_run_boundary_label_expansion_audit_v1.py"
    py_compile.compile(str(repo_root / "pv_ae" / "panel_day_engine.py"), doraise=True)
    py_compile.compile(str(builder), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="boundary-label-expansion-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        result = run([sys.executable, str(builder), "--root", str(tmp_root)], cwd=repo_root)
        if result.returncode != 0:
            raise SystemExit(f"builder failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        candidates_path = tmp_root / "_share" / "panel_day_engine_run_boundary_label_expansion_candidates_v1.csv"
        summary_path = tmp_root / "_share" / "panel_day_engine_run_boundary_label_expansion_summary_v1.csv"
        prototypes_path = tmp_root / "_share" / "panel_day_engine_run_boundary_label_expansion_prototypes_v1.csv"

        assert_true(candidates_path.exists(), "missing candidates output")
        assert_true(summary_path.exists(), "missing summary output")
        assert_true(prototypes_path.exists(), "missing prototypes output")

        candidates = pd.read_csv(candidates_path, encoding="utf-8-sig")
        summary_df = pd.read_csv(summary_path, encoding="utf-8-sig")
        prototypes = pd.read_csv(prototypes_path, encoding="utf-8-sig")

        pool_names = set(prototypes["prototype_pool_name"].astype(str))
        assert_true(
            pool_names == {"positive_boundary_prototype_pool", "hard_negative_prototype_pool"},
            f"unexpected prototype pools: {pool_names}",
        )
        assert_true(
            int(prototypes["prototype_pool_name"].eq("positive_boundary_prototype_pool").sum()) == 2,
            "positive prototype pool selection failed",
        )
        assert_true(
            int(prototypes["prototype_pool_name"].eq("hard_negative_prototype_pool").sum()) == 1,
            "hard negative prototype pool selection failed",
        )

        def pick(panel_id: str) -> pd.Series:
            subset = candidates.loc[candidates["panel_id"].astype(str).eq(panel_id)]
            assert_true(len(subset) == 1, f"expected one row for {panel_id}")
            return subset.iloc[0]

        cand_pos = pick("cand_pos")
        cand_neg = pick("cand_neg")
        cand_monitor = pick("cand_monitor")
        cand_low = pick("cand_low")

        assert_true(cand_pos["candidate_class"] == "positive_promotion_candidate", "positive candidate class failed")
        assert_true(cand_pos["candidate_priority_band"] == "P1", "P1 assignment failed")
        assert_true(float(cand_pos["boundary_margin"]) > 0, "positive boundary margin should be positive")

        assert_true(cand_neg["candidate_class"] == "hard_negative_review_candidate", "hard negative candidate class failed")
        assert_true(cand_neg["candidate_priority_band"] == "P3", "P3 assignment failed")
        assert_true(float(cand_neg["boundary_margin"]) <= 0, "hard negative margin should be non-positive")

        assert_true(
            cand_monitor["candidate_class"] == "monitor_or_common_cause_holdout",
            "monitor/common-cause holdout class failed",
        )
        assert_true(cand_monitor["candidate_priority_band"] == "P4", "holdout should stay P4")

        assert_true(cand_low["candidate_class"] == "low_priority_unlabeled", "low priority class failed")
        assert_true(cand_low["candidate_priority_band"] == "P4", "low priority should stay P4")

        overall = summary_df.loc[summary_df["record_type"].astype(str).eq("overall")]
        assert_true(len(overall) == 1, "overall summary row missing")
        overall_row = overall.iloc[0]
        assert_true(int(overall_row["excluded_run_count"]) == 4, "excluded_run_count mismatch")
        assert_true(int(overall_row["positive_promotion_candidate_count"]) == 1, "positive count mismatch")
        assert_true(int(overall_row["hard_negative_review_candidate_count"]) == 1, "hard negative count mismatch")
        assert_true(int(overall_row["monitor_or_common_cause_holdout_count"]) == 1, "holdout count mismatch")
        assert_true(int(overall_row["low_priority_unlabeled_count"]) == 1, "low priority count mismatch")
        assert_true(int(overall_row["p1_count"]) == 1, "P1 count mismatch")
        assert_true(int(overall_row["p3_count"]) == 1, "P3 count mismatch")
        assert_true(int(overall_row["p4_count"]) == 2, "P4 count mismatch")
        assert_true(int(overall_row["site_positive_gap_flag"]) == 1, "site gap summary mismatch")


if __name__ == "__main__":
    main()
