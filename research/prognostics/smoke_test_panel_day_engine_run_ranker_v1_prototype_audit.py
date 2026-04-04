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
V0_TOPK_COLS = [
    "score_name",
    "top_k",
    "topk_positive_like_count",
    "topk_nuisance_like_count",
    "topk_monitor_like_count",
    "topk_unlabeled_other_count",
    "topk_positive_like_rate",
    "topk_nuisance_like_rate",
    "topk_monitor_like_rate",
    "topk_unlabeled_other_rate",
    "topk_eligible_local_count",
    "topk_future_fault_linked_count",
    "topk_nuisance_alert_count",
    "topk_isolated_unexplained_count",
    "topk_recurring_monitor_like_count",
    "base_positive_like_rate",
    "base_nuisance_like_rate",
    "positive_like_lift",
    "nuisance_like_lift",
    "precision_minus_nuisance",
]
V1_SCORE_NAMES = [
    "logistic_v1_score",
    "hgb_v1_score",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
]
TOP_K_VALUES = [10, 20, 50, 100]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df = df.reindex(columns=columns)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def feature_row(
    site: str,
    panel_id: str,
    start: str,
    end: str,
    *,
    cohort_hint: str,
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
        "run_day_count": run_day_count,
        "run_shape_class": "chronic_alert_run" if run_day_count >= 10 else "short_alert_run",
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
        "cond_evt_same_day_early_corroborated_day_ratio": 1.0 - min(cond_evt_only_day_ratio, 1.0),
        "ae_mid_or_hi_early_day_ratio": ae_mid_or_hi_early_day_ratio,
        "dtw_mid_or_hi_early_day_ratio": 0.5,
        "hs_mid_or_hi_early_day_ratio": 0.3,
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


def v0_score_row(
    site: str,
    panel_id: str,
    start: str,
    end: str,
    *,
    run_day_count: int,
    run_shape_class: str,
    cohort_hint: str,
    electrical_core_score: float,
    electrical_core_minus_broadshape_050: float,
) -> dict[str, object]:
    return {
        "site": site,
        "panel_id": panel_id,
        "run_start_date": start,
        "run_end_date": end,
        "run_day_count": run_day_count,
        "run_shape_class": run_shape_class,
        "cohort_hint": cohort_hint,
        "electrical_core_score": electrical_core_score,
        "electrical_evt_score": electrical_core_score,
        "electrical_evt_minus_broadshape_score": electrical_core_minus_broadshape_050,
        "electrical_core_minus_broadshape_025": electrical_core_minus_broadshape_050,
        "electrical_core_minus_broadshape_050": electrical_core_minus_broadshape_050,
        "electrical_core_minus_broadshape_075": electrical_core_minus_broadshape_050,
        "electrical_core_plus_evtonly_minus_broadshape_025": electrical_core_minus_broadshape_050,
        "electrical_core_plus_evtonly_minus_broadshape_050": electrical_core_minus_broadshape_050,
    }


def build_fixture_root(tmp_root: Path) -> None:
    header_like_feature_row = {col: col for col in FEATURE_TABLE_COLS}
    feature_rows = [
        header_like_feature_row,
        feature_row("conalog", "run.pos.1", "2025-01-01", "2025-01-05", cohort_hint="eligible_local", run_day_count=5, max_v_drop=0.85, min_mid_v_ratio=0.25, min_mid_ratio=0.30, cond_evt_only_day_ratio=0.90, ae_mid_or_hi_early_day_ratio=0.10, mean_signal_count=1.0, max_signal_count=1.0, p95_recon_error=0.10),
        feature_row("conalog", "run.pos.2", "2025-01-10", "2025-01-15", cohort_hint="future_fault_linked", run_day_count=6, max_v_drop=0.80, min_mid_v_ratio=0.32, min_mid_ratio=0.36, cond_evt_only_day_ratio=0.82, ae_mid_or_hi_early_day_ratio=0.12, mean_signal_count=1.1, max_signal_count=1.2, p95_recon_error=0.12),
        feature_row("gangui", "run.neg.1", "2025-02-01", "2025-02-05", cohort_hint="nuisance_alert", run_day_count=5, max_v_drop=0.18, min_mid_v_ratio=0.90, min_mid_ratio=0.88, cond_evt_only_day_ratio=0.08, ae_mid_or_hi_early_day_ratio=0.92, mean_signal_count=3.6, max_signal_count=4.0, p95_recon_error=0.82),
        feature_row("gangui", "run.neg.2", "2025-02-10", "2025-02-14", cohort_hint="isolated_unexplained", run_day_count=5, max_v_drop=0.16, min_mid_v_ratio=0.94, min_mid_ratio=0.92, cond_evt_only_day_ratio=0.05, ae_mid_or_hi_early_day_ratio=0.90, mean_signal_count=3.8, max_signal_count=4.1, p95_recon_error=0.88),
        feature_row("ktc_ess", "run.mon.1", "2025-03-01", "2025-03-06", cohort_hint="recurring_monitor_like", run_day_count=6, max_v_drop=0.42, min_mid_v_ratio=0.72, min_mid_ratio=0.70, cond_evt_only_day_ratio=0.50, ae_mid_or_hi_early_day_ratio=0.55, mean_signal_count=2.2, max_signal_count=2.5, p95_recon_error=0.42),
        feature_row("sinhyo", "run.other.1", "2025-04-01", "2025-04-04", cohort_hint="unmatched_other", run_day_count=4, max_v_drop=0.30, min_mid_v_ratio=0.78, min_mid_ratio=0.76, cond_evt_only_day_ratio=0.38, ae_mid_or_hi_early_day_ratio=0.45, mean_signal_count=2.0, max_signal_count=2.2, p95_recon_error=0.32),
    ]
    feature_rows.extend(
        [
            feature_row(
                "sinhyo",
                f"run.bulk.{idx:03d}",
                f"2025-05-{(idx % 28) + 1:02d}",
                f"2025-05-{(idx % 28) + 1:02d}",
                cohort_hint="unmatched_other",
                run_day_count=1,
                max_v_drop=max(0.01, 0.14 - idx * 0.001),
                min_mid_v_ratio=min(0.995, 0.93 + idx * 0.0004),
                min_mid_ratio=min(0.995, 0.92 + idx * 0.0004),
                cond_evt_only_day_ratio=max(0.0, 0.12 - idx * 0.001),
                ae_mid_or_hi_early_day_ratio=min(0.99, 0.76 + idx * 0.001),
                mean_signal_count=min(5.0, 3.0 + idx * 0.01),
                max_signal_count=min(5.0, 3.2 + idx * 0.01),
                p95_recon_error=min(1.0, 0.60 + idx * 0.003),
            )
            for idx in range(1, 45)
        ]
    )

    header_like_v0_score_row = {col: col for col in V0_SCORE_COLS}
    v0_rows = [header_like_v0_score_row]
    for row in feature_rows[1:]:
        if row["site"] == "site":
            continue
        v0_rows.append(
            v0_score_row(
                row["site"],
                row["panel_id"],
                row["run_start_date"],
                row["run_end_date"],
                run_day_count=row["run_day_count"],
                run_shape_class=row["run_shape_class"],
                cohort_hint=row["cohort_hint"],
                electrical_core_score=float(row["max_v_drop"]) * 10.0,
                electrical_core_minus_broadshape_050=float(row["max_v_drop"]) * 8.0,
            )
        )

    header_like_v0_topk_row = {col: col for col in V0_TOPK_COLS}
    v0_topk_rows = [
        header_like_v0_topk_row,
        {
            "score_name": "electrical_core_score",
            "top_k": 10,
            "topk_positive_like_count": 2,
            "topk_nuisance_like_count": 1,
            "topk_monitor_like_count": 0,
            "topk_unlabeled_other_count": 7,
            "topk_positive_like_rate": 0.2,
            "topk_nuisance_like_rate": 0.1,
            "topk_monitor_like_rate": 0.0,
            "topk_unlabeled_other_rate": 0.7,
            "topk_eligible_local_count": 1,
            "topk_future_fault_linked_count": 1,
            "topk_nuisance_alert_count": 1,
            "topk_isolated_unexplained_count": 0,
            "topk_recurring_monitor_like_count": 0,
            "base_positive_like_rate": 0.5,
            "base_nuisance_like_rate": 0.5,
            "positive_like_lift": 0.4,
            "nuisance_like_lift": 0.2,
            "precision_minus_nuisance": 0.1,
        },
        {
            "score_name": "electrical_core_minus_broadshape_050",
            "top_k": 10,
            "topk_positive_like_count": 1,
            "topk_nuisance_like_count": 1,
            "topk_monitor_like_count": 0,
            "topk_unlabeled_other_count": 8,
            "topk_positive_like_rate": 0.1,
            "topk_nuisance_like_rate": 0.1,
            "topk_monitor_like_rate": 0.0,
            "topk_unlabeled_other_rate": 0.8,
            "topk_eligible_local_count": 1,
            "topk_future_fault_linked_count": 0,
            "topk_nuisance_alert_count": 1,
            "topk_isolated_unexplained_count": 0,
            "topk_recurring_monitor_like_count": 0,
            "base_positive_like_rate": 0.5,
            "base_nuisance_like_rate": 0.5,
            "positive_like_lift": 0.2,
            "nuisance_like_lift": 0.2,
            "precision_minus_nuisance": 0.0,
        },
    ]

    write_csv(tmp_root / "_share" / "panel_day_engine_run_feature_table_v1.csv", feature_rows, FEATURE_TABLE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v0_scores.csv", v0_rows, V0_SCORE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v0_topk_yield_summary.csv", v0_topk_rows, V0_TOPK_COLS)


def main() -> None:
    script_path = Path(__file__).resolve()
    build_script = script_path.with_name("build_panel_day_engine_run_ranker_v1_prototype_audit.py")
    with tempfile.TemporaryDirectory(prefix="run_ranker_v1_prototype_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        compile_result = run(
            [sys.executable, "-m", "py_compile", str(build_script), str(script_path)],
            cwd=tmp_root,
        )
        assert_true(compile_result.returncode == 0, compile_result.stderr)

        build_result = run([sys.executable, str(build_script), "--root", str(tmp_root)], cwd=tmp_root)
        assert_true(build_result.returncode == 0, build_result.stderr)

        scores_path = tmp_root / "_share" / "panel_day_engine_run_ranker_v1_scores.csv"
        summary_path = tmp_root / "_share" / "panel_day_engine_run_ranker_v1_summary.csv"
        topk_path = tmp_root / "_share" / "panel_day_engine_run_ranker_v1_topk_yield_summary.csv"
        topruns_path = tmp_root / "_share" / "panel_day_engine_run_ranker_v1_topruns.csv"
        assert_true(scores_path.exists(), "scores output missing")
        assert_true(summary_path.exists(), "summary output missing")
        assert_true(topk_path.exists(), "topk output missing")
        assert_true(topruns_path.exists(), "topruns output missing")

        scores_df = pd.read_csv(scores_path, low_memory=False, encoding="utf-8-sig")
        summary_df = pd.read_csv(summary_path, low_memory=False, encoding="utf-8-sig")
        topk_df = pd.read_csv(topk_path, low_memory=False, encoding="utf-8-sig")
        topruns_df = pd.read_csv(topruns_path, low_memory=False, encoding="utf-8-sig")

        assert_true(len(scores_df) == 50, f"expected 50 scored runs, found {len(scores_df)}")
        assert_true(scores_df[["logistic_v1_score", "hgb_v1_score"]].notna().all().all(), "learned scores missing")
        assert_true(set(V1_SCORE_NAMES) == set(summary_df["score_name"]), "summary score coverage mismatch")
        assert_true(set(V1_SCORE_NAMES) == set(topk_df["score_name"]), "topk score coverage mismatch")

        best_positive_logistic = scores_df.loc[scores_df["cohort_hint"].isin({"eligible_local", "future_fault_linked"}), "logistic_v1_score"].max()
        best_negative_logistic = scores_df.loc[scores_df["cohort_hint"].isin({"nuisance_alert", "isolated_unexplained"}), "logistic_v1_score"].max()
        best_positive_hgb = scores_df.loc[scores_df["cohort_hint"].isin({"eligible_local", "future_fault_linked"}), "hgb_v1_score"].max()
        best_negative_hgb = scores_df.loc[scores_df["cohort_hint"].isin({"nuisance_alert", "isolated_unexplained"}), "hgb_v1_score"].max()
        assert_true(best_positive_logistic > best_negative_logistic, "logistic score ordering looks wrong")
        assert_true(best_positive_hgb > best_negative_hgb, "hgb score ordering looks wrong")

        expected_topk_rows = len(V1_SCORE_NAMES) * sum(min(k, len(scores_df)) for k in TOP_K_VALUES)
        assert_true(len(topk_df) == len(V1_SCORE_NAMES) * len(TOP_K_VALUES), "topk summary row count mismatch")
        assert_true(len(topruns_df) == len(V1_SCORE_NAMES) * min(30, len(scores_df)), "topruns row count mismatch")

        logistic_top10 = scores_df.sort_values(
            ["logistic_v1_score", "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
            ascending=[False, False, True, True, True, True],
            kind="stable",
        ).head(10)
        logistic_top10_positive = int(logistic_top10["cohort_hint"].isin({"eligible_local", "future_fault_linked"}).sum())
        logistic_top10_negative = int(logistic_top10["cohort_hint"].isin({"nuisance_alert", "isolated_unexplained"}).sum())
        top10_summary = topk_df.loc[(topk_df["score_name"] == "logistic_v1_score") & (topk_df["top_k"] == 10)].iloc[0]
        assert_true(int(top10_summary["topk_positive_like_count"]) == logistic_top10_positive, "top10 positive count mismatch")
        assert_true(int(top10_summary["topk_negative_like_count"]) == logistic_top10_negative, "top10 negative count mismatch")

        base_positive_rate = 2 / 4
        base_negative_rate = 2 / 4
        assert_true(
            abs(float(top10_summary["positive_lift_vs_base"]) - ((logistic_top10_positive / 10.0) / base_positive_rate)) < 1e-9,
            "positive lift mismatch",
        )
        assert_true(
            abs(float(top10_summary["negative_lift_vs_base"]) - ((logistic_top10_negative / 10.0) / base_negative_rate)) < 1e-9,
            "negative lift mismatch",
        )

        expected_scores = {"logistic_v1_score", "hgb_v1_score", "electrical_core_score", "electrical_core_minus_broadshape_050"}
        assert_true(set(topruns_df["score_name"]) == expected_scores, "topruns score coverage mismatch")


if __name__ == "__main__":
    main()
