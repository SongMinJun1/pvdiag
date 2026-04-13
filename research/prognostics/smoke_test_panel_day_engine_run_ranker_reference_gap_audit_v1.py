#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import research.prognostics.build_panel_day_engine_run_ranker_reference_gap_audit_v1 as audit


def repo_root() -> Path:
    return REPO_ROOT


def make_feature_row(
    site: str,
    panel_id: str,
    run_start_date: str,
    run_end_date: str,
    run_day_count: int,
    run_shape_class: str,
    cohort_hint: str,
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
        "run_start_date": run_start_date,
        "run_end_date": run_end_date,
        "run_day_count": run_day_count,
        "run_shape_class": run_shape_class,
        "cohort_hint": cohort_hint,
        "max_v_drop": max_v_drop,
        "min_mid_v_ratio": min_mid_v_ratio,
        "min_mid_ratio": min_mid_ratio,
        "cond_evt_only_day_ratio": cond_evt_only_day_ratio,
        "ae_mid_or_hi_early_day_ratio": ae_mid_or_hi_early_day_ratio,
        "mean_signal_count": mean_signal_count,
        "max_signal_count": max_signal_count,
        "p95_recon_error": p95_recon_error,
    }


def build_synthetic_root(root: Path) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    feature_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    score_rows: list[dict[str, object]] = []

    for rank in range(1, 61):
        site = "alpha" if rank <= 30 else "beta"
        site_rank = rank if site == "alpha" else rank - 30
        panel_id = f"{site}-panel-{site_rank:02d}"
        run_start_date = f"2025-01-{rank:02d}" if site == "alpha" else f"2025-02-{site_rank:02d}"
        run_end_date = run_start_date
        score = float(101 - rank)
        label_bucket = "unlabeled_other"
        run_shape_class = "short_alert_run"
        cohort_hint = "unmatched_other"
        max_v_drop = 1.0 + rank * 0.05
        min_mid_v_ratio = 0.95 - rank * 0.005
        min_mid_ratio = min_mid_v_ratio + 0.05
        cond_evt_only_day_ratio = 0.1
        ae_ratio = 0.1
        mean_signal_count = 1.0
        max_signal_count = 2.0
        p95_recon_error = 0.05

        if rank == 5:
            label_bucket = "positive_like"
            run_shape_class = "chronic_alert_run"
            cohort_hint = "future_fault_linked"
            max_v_drop = 12.0
            min_mid_v_ratio = 0.32
            min_mid_ratio = 0.40
            cond_evt_only_day_ratio = 0.80
            ae_ratio = 0.90
            mean_signal_count = 4.5
            max_signal_count = 6.0
            p95_recon_error = 0.30
        elif rank == 10:
            label_bucket = "negative_like"
            run_shape_class = "medium_alert_run"
            cohort_hint = "nuisance_alert"
            max_v_drop = 9.0
            min_mid_v_ratio = 0.50
            min_mid_ratio = 0.60
            cond_evt_only_day_ratio = 0.35
            ae_ratio = 0.30
            mean_signal_count = 2.0
            max_signal_count = 3.0
            p95_recon_error = 0.18
        elif rank == 25:
            label_bucket = "positive_like"
            run_shape_class = "medium_alert_run"
            cohort_hint = "future_fault_linked"
            max_v_drop = 8.0
            min_mid_v_ratio = 0.45
            min_mid_ratio = 0.53
            cond_evt_only_day_ratio = 0.55
            ae_ratio = 0.65
            mean_signal_count = 3.5
            max_signal_count = 5.0
            p95_recon_error = 0.20
        elif rank == 30:
            label_bucket = "negative_like"
            run_shape_class = "medium_alert_run"
            cohort_hint = "nuisance_alert"
            max_v_drop = 6.5
            min_mid_v_ratio = 0.62
            min_mid_ratio = 0.70
            cond_evt_only_day_ratio = 0.22
            ae_ratio = 0.20
            mean_signal_count = 1.8
            max_signal_count = 3.0
            p95_recon_error = 0.11
        elif rank == 55:
            label_bucket = "positive_like"
            run_shape_class = "short_alert_run"
            cohort_hint = "future_fault_linked"
            max_v_drop = 2.5
            min_mid_v_ratio = 0.82
            min_mid_ratio = 0.87
            cond_evt_only_day_ratio = 0.18
            ae_ratio = 0.16
            mean_signal_count = 1.2
            max_signal_count = 2.0
            p95_recon_error = 0.06
        elif rank == 56:
            label_bucket = "negative_like"
            run_shape_class = "short_alert_run"
            cohort_hint = "nuisance_alert"
            max_v_drop = 2.0
            min_mid_v_ratio = 0.88
            min_mid_ratio = 0.93
            cond_evt_only_day_ratio = 0.05
            ae_ratio = 0.04
            mean_signal_count = 1.0
            max_signal_count = 1.0
            p95_recon_error = 0.04

        feature_rows.append(
            make_feature_row(
                site=site,
                panel_id=panel_id,
                run_start_date=run_start_date,
                run_end_date=run_end_date,
                run_day_count=1 + (rank % 3),
                run_shape_class=run_shape_class,
                cohort_hint=cohort_hint,
                max_v_drop=max_v_drop,
                min_mid_v_ratio=min_mid_v_ratio,
                min_mid_ratio=min_mid_ratio,
                cond_evt_only_day_ratio=cond_evt_only_day_ratio,
                ae_mid_or_hi_early_day_ratio=ae_ratio,
                mean_signal_count=mean_signal_count,
                max_signal_count=max_signal_count,
                p95_recon_error=p95_recon_error,
            )
        )
        label_rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "run_start_date": run_start_date,
                "run_end_date": run_end_date,
                "label_bucket_v2": label_bucket,
            }
        )
        score_rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "run_start_date": run_start_date,
                "run_end_date": run_end_date,
                audit.FOCUS_SCORE_NAME: score,
            }
        )

    pd.DataFrame(feature_rows).to_csv(share_dir / audit.FEATURE_TABLE_NAME, index=False, encoding="utf-8-sig")
    pd.DataFrame(label_rows).to_csv(share_dir / audit.LABEL_PACK_V2_NAME, index=False, encoding="utf-8-sig")
    pd.DataFrame(score_rows).to_csv(share_dir / audit.V0_SCORES_NAME, index=False, encoding="utf-8-sig")


def assert_gap_classes(case_df: pd.DataFrame) -> None:
    expected = {
        ("positive_like", 5): "positive_top20_global",
        ("negative_like", 10): "negative_top20_global",
        ("positive_like", 25): "positive_top50_global_not_top20",
        ("negative_like", 30): "negative_top50_global_not_top20",
        ("positive_like", 55): "positive_below_top50_global",
        ("negative_like", 56): "negative_below_top50_global",
    }
    for (label_bucket, global_rank), gap_class in expected.items():
        subset = case_df.loc[
            (case_df["label_bucket_v2"] == label_bucket) & (case_df["global_score_rank"] == global_rank),
            :,
        ]
        assert len(subset) == 1
        assert subset.iloc[0]["gap_class"] == gap_class


def assert_summary_medians(summary_df: pd.DataFrame) -> None:
    gap_rows = summary_df.loc[summary_df["summary_type"] == "gap_class_summary"].copy()
    positive_top20 = gap_rows.loc[gap_rows["gap_class"] == "positive_top20_global"].iloc[0]
    assert int(positive_top20["run_count"]) == 1
    assert float(positive_top20["median_score"]) == 96.0
    assert float(positive_top20["median_global_score_rank"]) == 5.0
    assert float(positive_top20["median_site_score_rank"]) == 5.0
    assert float(positive_top20["median_max_v_drop"]) == 12.0

    recommendation = summary_df.loc[summary_df["summary_type"] == "overall_recommendation"].iloc[0]
    assert recommendation["recommended_next_direction"] == "keep_reference_as_best_current"


def main() -> None:
    root = repo_root()
    py_compile.compile(str(root / "pv_ae/panel_day_engine.py"), doraise=True)
    py_compile.compile(str(root / "research/prognostics/build_panel_day_engine_run_ranker_reference_gap_audit_v1.py"), doraise=True)
    py_compile.compile(str(root / "research/prognostics/smoke_test_panel_day_engine_run_ranker_reference_gap_audit_v1.py"), doraise=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_root = Path(tmpdir)
        build_synthetic_root(temp_root)
        subprocess.run(
            [sys.executable, str(root / "research/prognostics/build_panel_day_engine_run_ranker_reference_gap_audit_v1.py"), "--root", str(temp_root)],
            check=True,
            cwd=root,
        )

        share_dir = temp_root / "_share"
        case_df = pd.read_csv(share_dir / audit.CASES_OUTPUT_NAME, encoding="utf-8-sig")
        summary_df = pd.read_csv(share_dir / audit.SUMMARY_OUTPUT_NAME, encoding="utf-8-sig")

        assert len(case_df) == 6
        assert set(case_df["gap_class"]) == set(audit.GAP_CLASS_ORDER)
        assert_gap_classes(case_df)
        assert_summary_medians(summary_df)


if __name__ == "__main__":
    main()
