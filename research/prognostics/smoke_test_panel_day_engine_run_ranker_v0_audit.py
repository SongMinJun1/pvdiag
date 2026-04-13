#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

TOP_K_VALUES = [10, 20, 50, 100]
SCORE_NAMES = [
    "electrical_core_score",
    "electrical_evt_score",
    "electrical_evt_minus_broadshape_score",
    "electrical_core_minus_broadshape_025",
    "electrical_core_minus_broadshape_050",
    "electrical_core_minus_broadshape_075",
    "electrical_core_plus_evtonly_minus_broadshape_025",
    "electrical_core_plus_evtonly_minus_broadshape_050",
]
TOPK_CANDIDATE_NAMES = [
    *SCORE_NAMES,
    "two_stage_core50_penalty050",
    "two_stage_core100_penalty050",
]

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
METHOD_HINT_COLS = [
    "feature_name",
    "comparison_target",
    "normalized_gap",
    "directional_hint",
    "method_relevance_class",
]
REQUIRED_HINT_FEATURES = [
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
]


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


def robust_scale(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.dropna().empty:
        return pd.Series(0.0, index=series.index)
    median = float(numeric.median())
    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    iqr = q3 - q1
    denom = iqr if abs(iqr) > 1e-9 else 1.0
    scaled = (numeric.fillna(median) - median) / denom
    return scaled.clip(-5.0, 5.0)


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


def build_fixture_root(tmp_root: Path) -> None:
    header_like_feature_row = {col: col for col in FEATURE_TABLE_COLS}
    feature_rows = [
        header_like_feature_row,
        feature_row(
            "conalog",
            "run.pos.1",
            "2025-01-01",
            "2025-01-05",
            cohort_hint="eligible_local",
            run_day_count=5,
            max_v_drop=0.80,
            min_mid_v_ratio=0.30,
            min_mid_ratio=0.35,
            cond_evt_only_day_ratio=0.90,
            ae_mid_or_hi_early_day_ratio=0.10,
            mean_signal_count=1.0,
            max_signal_count=1.0,
            p95_recon_error=0.10,
        ),
        feature_row(
            "conalog",
            "run.pos.2",
            "2025-01-10",
            "2025-01-14",
            cohort_hint="future_fault_linked",
            run_day_count=5,
            max_v_drop=0.72,
            min_mid_v_ratio=0.40,
            min_mid_ratio=0.45,
            cond_evt_only_day_ratio=0.80,
            ae_mid_or_hi_early_day_ratio=0.15,
            mean_signal_count=1.2,
            max_signal_count=1.2,
            p95_recon_error=0.12,
        ),
        feature_row(
            "gangui",
            "run.nuis.1",
            "2025-02-01",
            "2025-02-05",
            cohort_hint="nuisance_alert",
            run_day_count=5,
            max_v_drop=0.20,
            min_mid_v_ratio=0.92,
            min_mid_ratio=0.90,
            cond_evt_only_day_ratio=0.10,
            ae_mid_or_hi_early_day_ratio=0.95,
            mean_signal_count=3.5,
            max_signal_count=4.0,
            p95_recon_error=0.82,
        ),
        feature_row(
            "gangui",
            "run.iso.1",
            "2025-02-10",
            "2025-02-14",
            cohort_hint="isolated_unexplained",
            run_day_count=5,
            max_v_drop=0.15,
            min_mid_v_ratio=0.96,
            min_mid_ratio=0.94,
            cond_evt_only_day_ratio=0.05,
            ae_mid_or_hi_early_day_ratio=0.90,
            mean_signal_count=3.8,
            max_signal_count=4.2,
            p95_recon_error=0.88,
        ),
        feature_row(
            "ktc_ess",
            "run.mon.1",
            "2025-03-01",
            "2025-03-06",
            cohort_hint="recurring_monitor_like",
            run_day_count=6,
            max_v_drop=0.42,
            min_mid_v_ratio=0.72,
            min_mid_ratio=0.70,
            cond_evt_only_day_ratio=0.50,
            ae_mid_or_hi_early_day_ratio=0.55,
            mean_signal_count=2.2,
            max_signal_count=2.5,
            p95_recon_error=0.42,
        ),
        feature_row(
            "sinhyo",
            "run.other.1",
            "2025-04-01",
            "2025-04-05",
            cohort_hint="unmatched_other",
            run_day_count=5,
            max_v_drop=0.35,
            min_mid_v_ratio=0.80,
            min_mid_ratio=0.78,
            cond_evt_only_day_ratio=0.40,
            ae_mid_or_hi_early_day_ratio=0.50,
            mean_signal_count=2.0,
            max_signal_count=2.2,
            p95_recon_error=0.35,
        ),
        feature_row(
            "sinhyo",
            "run.other.2",
            "2025-04-10",
            "2025-04-14",
            cohort_hint="unmatched_other",
            run_day_count=5,
            max_v_drop=0.30,
            min_mid_v_ratio=0.82,
            min_mid_ratio=0.80,
            cond_evt_only_day_ratio=0.35,
            ae_mid_or_hi_early_day_ratio=0.55,
            mean_signal_count=2.1,
            max_signal_count=2.3,
            p95_recon_error=0.40,
        ),
        feature_row(
            "sinhyo",
            "run.other.3",
            "2025-04-20",
            "2025-04-24",
            cohort_hint="unmatched_other",
            run_day_count=5,
            max_v_drop=0.26,
            min_mid_v_ratio=0.84,
            min_mid_ratio=0.83,
            cond_evt_only_day_ratio=0.32,
            ae_mid_or_hi_early_day_ratio=0.60,
            mean_signal_count=2.4,
            max_signal_count=2.6,
            p95_recon_error=0.44,
        ),
        feature_row(
            "sinhyo",
            "run.other.4",
            "2025-04-30",
            "2025-05-04",
            cohort_hint="unmatched_other",
            run_day_count=5,
            max_v_drop=0.24,
            min_mid_v_ratio=0.86,
            min_mid_ratio=0.85,
            cond_evt_only_day_ratio=0.28,
            ae_mid_or_hi_early_day_ratio=0.62,
            mean_signal_count=2.5,
            max_signal_count=2.7,
            p95_recon_error=0.47,
        ),
        feature_row(
            "sinhyo",
            "run.other.5",
            "2025-05-10",
            "2025-05-14",
            cohort_hint="unmatched_other",
            run_day_count=5,
            max_v_drop=0.22,
            min_mid_v_ratio=0.88,
            min_mid_ratio=0.87,
            cond_evt_only_day_ratio=0.24,
            ae_mid_or_hi_early_day_ratio=0.68,
            mean_signal_count=2.7,
            max_signal_count=2.9,
            p95_recon_error=0.50,
        ),
        feature_row(
            "sinhyo",
            "run.other.6",
            "2025-05-20",
            "2025-05-24",
            cohort_hint="unmatched_other",
            run_day_count=5,
            max_v_drop=0.18,
            min_mid_v_ratio=0.90,
            min_mid_ratio=0.89,
            cond_evt_only_day_ratio=0.20,
            ae_mid_or_hi_early_day_ratio=0.72,
            mean_signal_count=2.9,
            max_signal_count=3.1,
            p95_recon_error=0.55,
        ),
        feature_row(
            "sinhyo",
            "run.other.7",
            "2025-05-30",
            "2025-06-03",
            cohort_hint="unmatched_other",
            run_day_count=5,
            max_v_drop=0.16,
            min_mid_v_ratio=0.92,
            min_mid_ratio=0.91,
            cond_evt_only_day_ratio=0.18,
            ae_mid_or_hi_early_day_ratio=0.75,
            mean_signal_count=3.0,
            max_signal_count=3.2,
            p95_recon_error=0.60,
        ),
    ]
    feature_rows.extend(
        [
            feature_row(
                "sinhyo",
                f"run.bulk.{idx:03d}",
                f"2025-06-{(idx % 28) + 1:02d}",
                f"2025-06-{(idx % 28) + 1:02d}",
                cohort_hint="unmatched_other",
                run_day_count=1,
                max_v_drop=max(0.01, 0.14 - idx * 0.001),
                min_mid_v_ratio=min(0.995, 0.93 + idx * 0.0004),
                min_mid_ratio=min(0.995, 0.92 + idx * 0.0004),
                cond_evt_only_day_ratio=max(0.0, 0.15 - idx * 0.001),
                ae_mid_or_hi_early_day_ratio=min(0.99, 0.76 + idx * 0.001),
                mean_signal_count=min(5.0, 3.1 + idx * 0.01),
                max_signal_count=min(5.0, 3.3 + idx * 0.01),
                p95_recon_error=min(1.0, 0.61 + idx * 0.003),
            )
            for idx in range(1, 101)
        ]
    )
    header_like_hint_row = {col: col for col in METHOD_HINT_COLS}
    hint_rows = [header_like_hint_row]
    for idx, feature_name in enumerate(REQUIRED_HINT_FEATURES, start=1):
        hint_rows.append(
            {
                "feature_name": feature_name,
                "comparison_target": "eligible_local_vs_nuisance_alert",
                "normalized_gap": float(idx),
                "directional_hint": "synthetic",
                "method_relevance_class": "strong_run_ranker_candidate",
            }
        )

    write_csv(tmp_root / "_share" / "panel_day_engine_run_feature_table_v1.csv", feature_rows, FEATURE_TABLE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_feature_method_hints_v1.csv", hint_rows, METHOD_HINT_COLS)


def main() -> None:
    script_path = Path(__file__).resolve()
    build_script = script_path.with_name("build_panel_day_engine_run_ranker_v0_audit.py")
    with tempfile.TemporaryDirectory(prefix="run_ranker_v0_audit_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        compile_result = run(
            [sys.executable, "-m", "py_compile", str(build_script), str(script_path)],
            cwd=tmp_root,
        )
        assert_true(compile_result.returncode == 0, compile_result.stderr)

        build_result = run([sys.executable, str(build_script), "--root", str(tmp_root)], cwd=tmp_root)
        assert_true(build_result.returncode == 0, build_result.stderr)

        scores_path = tmp_root / "_share" / "panel_day_engine_run_ranker_v0_scores.csv"
        summary_path = tmp_root / "_share" / "panel_day_engine_run_ranker_v0_summary.csv"
        topruns_path = tmp_root / "_share" / "panel_day_engine_run_ranker_v0_topruns.csv"
        topk_summary_path = tmp_root / "_share" / "panel_day_engine_run_ranker_v0_topk_yield_summary.csv"
        topk_rows_path = tmp_root / "_share" / "panel_day_engine_run_ranker_v0_topk_yield_rows.csv"
        assert_true(scores_path.exists(), "scores output missing")
        assert_true(summary_path.exists(), "summary output missing")
        assert_true(topruns_path.exists(), "topruns output missing")
        assert_true(topk_summary_path.exists(), "topk summary output missing")
        assert_true(topk_rows_path.exists(), "topk rows output missing")

        scores_df = pd.read_csv(scores_path, low_memory=False, encoding="utf-8-sig")
        summary_df = pd.read_csv(summary_path, low_memory=False, encoding="utf-8-sig")
        topruns_df = pd.read_csv(topruns_path, low_memory=False, encoding="utf-8-sig")
        topk_summary_df = pd.read_csv(topk_summary_path, low_memory=False, encoding="utf-8-sig")
        topk_rows_df = pd.read_csv(topk_rows_path, low_memory=False, encoding="utf-8-sig")

        assert_true(len(scores_df) == 112, f"expected 112 scored runs, found {len(scores_df)}")
        assert_true(scores_df[SCORE_NAMES].notna().all().all(), "score columns contain NaN")
        assert_true(set(SCORE_NAMES).issubset(scores_df.columns), "new score variants missing from scores output")
        assert_true(set(SCORE_NAMES) == set(summary_df["score_name"]), "summary score_name coverage mismatch")
        assert_true(set(TOPK_CANDIDATE_NAMES) == set(topk_summary_df["score_name"]), "topk summary score_name coverage mismatch")

        raw_feature_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_feature_table_v1.csv", low_memory=False, encoding="utf-8-sig")
        raw_feature_df = raw_feature_df.loc[raw_feature_df["site"].ne("site")].copy().reset_index(drop=True)
        for col in [
            "max_v_drop",
            "min_mid_v_ratio",
            "min_mid_ratio",
            "cond_evt_only_day_ratio",
            "ae_mid_or_hi_early_day_ratio",
            "mean_signal_count",
            "max_signal_count",
            "p95_recon_error",
        ]:
            raw_feature_df[col] = pd.to_numeric(raw_feature_df[col], errors="coerce")
        expected_df = raw_feature_df.loc[:, ["site", "panel_id", "run_start_date", "run_end_date"]].copy()
        expected_df["core"] = (
            robust_scale(raw_feature_df["max_v_drop"])
            + robust_scale(1.0 - raw_feature_df["min_mid_v_ratio"])
            + robust_scale(1.0 - raw_feature_df["min_mid_ratio"])
        )
        expected_df["broadshape_penalty"] = (
            robust_scale(raw_feature_df["ae_mid_or_hi_early_day_ratio"])
            + robust_scale(raw_feature_df["mean_signal_count"])
            + robust_scale(raw_feature_df["max_signal_count"])
            + robust_scale(raw_feature_df["p95_recon_error"])
        )
        expected_df["evtonly_bonus"] = robust_scale(raw_feature_df["cond_evt_only_day_ratio"])
        expected_df["electrical_core_minus_broadshape_025"] = expected_df["core"] - 0.25 * expected_df["broadshape_penalty"]
        expected_df["electrical_core_minus_broadshape_050"] = expected_df["core"] - 0.50 * expected_df["broadshape_penalty"]
        expected_df["electrical_core_minus_broadshape_075"] = expected_df["core"] - 0.75 * expected_df["broadshape_penalty"]
        expected_df["electrical_core_plus_evtonly_minus_broadshape_025"] = (
            expected_df["core"] + 0.25 * expected_df["evtonly_bonus"] - 0.25 * expected_df["broadshape_penalty"]
        )
        expected_df["electrical_core_plus_evtonly_minus_broadshape_050"] = (
            expected_df["core"] + 0.25 * expected_df["evtonly_bonus"] - 0.50 * expected_df["broadshape_penalty"]
        )
        merged_expected = scores_df.merge(
            expected_df,
            on=["site", "panel_id", "run_start_date", "run_end_date"],
            how="left",
            suffixes=("_actual", "_expected"),
        )
        for score_name in [
            "electrical_core_minus_broadshape_025",
            "electrical_core_minus_broadshape_050",
            "electrical_core_minus_broadshape_075",
            "electrical_core_plus_evtonly_minus_broadshape_025",
            "electrical_core_plus_evtonly_minus_broadshape_050",
        ]:
            diff = (merged_expected[f"{score_name}_actual"] - merged_expected[f"{score_name}_expected"]).abs().max()
            assert_true(diff < 1e-9, f"{score_name} formula mismatch")

        ranked_minus = scores_df.sort_values("electrical_evt_minus_broadshape_score", ascending=False, kind="stable").reset_index(drop=True)
        best_positive_rank = ranked_minus.index[ranked_minus["cohort_hint"].isin({"eligible_local", "future_fault_linked"})][0]
        best_nuisance_rank = ranked_minus.index[ranked_minus["cohort_hint"].isin({"nuisance_alert", "isolated_unexplained"})][0]
        assert_true(best_positive_rank < best_nuisance_rank, "positive-like run should outrank nuisance-like run for electrical_evt_minus_broadshape_score")

        evt_summary = summary_df.loc[summary_df["score_name"].eq("electrical_evt_minus_broadshape_score")].iloc[0]
        assert_true(int(evt_summary["positive_like_count"]) == 2, "positive_like_count mismatch")
        assert_true(int(evt_summary["nuisance_like_count"]) == 2, "nuisance_like_count mismatch")
        assert_true(int(evt_summary["monitor_like_count"]) == 1, "monitor_like_count mismatch")
        assert_true(int(evt_summary["unlabeled_other_count"]) == 107, "unlabeled_other_count mismatch")
        ranked_evt_minus_for_summary = scores_df.sort_values(
            ["electrical_evt_minus_broadshape_score", "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
            ascending=[False, False, True, True, True, True],
            kind="stable",
        ).reset_index(drop=True)
        top10_summary_rows = ranked_evt_minus_for_summary.head(10)
        top20_summary_rows = ranked_evt_minus_for_summary.head(20)
        assert_true(int(evt_summary["top10_positive_like_count"]) == int(top10_summary_rows["cohort_hint"].isin({"eligible_local", "future_fault_linked"}).sum()), "top10 positive count mismatch")
        assert_true(int(evt_summary["top10_nuisance_like_count"]) == int(top10_summary_rows["cohort_hint"].isin({"nuisance_alert", "isolated_unexplained"}).sum()), "top10 nuisance count mismatch")
        assert_true(int(evt_summary["top10_monitor_like_count"]) == int(top10_summary_rows["cohort_hint"].eq("recurring_monitor_like").sum()), "top10 monitor count mismatch")
        assert_true(int(evt_summary["top20_positive_like_count"]) == int(top20_summary_rows["cohort_hint"].isin({"eligible_local", "future_fault_linked"}).sum()), "top20 positive count mismatch")
        assert_true(float(evt_summary["positive_vs_nuisance_gap"]) > 0, "positive_vs_nuisance_gap should be positive")

        expected_topruns_rows = min(30, len(scores_df)) * len(SCORE_NAMES)
        assert_true(len(topruns_df) == expected_topruns_rows, f"expected {expected_topruns_rows} top rows, found {len(topruns_df)}")
        for score_name in SCORE_NAMES:
            score_top = topruns_df.loc[topruns_df["score_name"].eq(score_name)].copy()
            assert_true(len(score_top) == 30, f"expected 30 top rows for {score_name}")
            assert_true(score_top["rank"].tolist() == list(range(1, 31)), f"rank assignment broken for {score_name}")

        expected_topk_summary_rows = len(TOPK_CANDIDATE_NAMES) * len(TOP_K_VALUES)
        assert_true(len(topk_summary_df) == expected_topk_summary_rows, f"expected {expected_topk_summary_rows} topk summary rows, found {len(topk_summary_df)}")
        expected_topk_rows = sum(min(k, len(scores_df)) for k in TOP_K_VALUES) * len(TOPK_CANDIDATE_NAMES)
        assert_true(len(topk_rows_df) == expected_topk_rows, f"topk rows length mismatch: {len(topk_rows_df)} vs {expected_topk_rows}")

        ranked_evt_minus = scores_df.sort_values(
            ["electrical_evt_minus_broadshape_score", "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
            ascending=[False, False, True, True, True, True],
            kind="stable",
        ).reset_index(drop=True)
        top10 = ranked_evt_minus.head(10).copy()
        selected_n = len(top10)
        total_labeled_count = int(scores_df["cohort_hint"].isin({"eligible_local", "future_fault_linked", "nuisance_alert", "isolated_unexplained", "recurring_monitor_like"}).sum())
        expected_positive = int(top10["cohort_hint"].isin({"eligible_local", "future_fault_linked"}).sum())
        expected_nuisance = int(top10["cohort_hint"].isin({"nuisance_alert", "isolated_unexplained"}).sum())
        expected_monitor = int(top10["cohort_hint"].eq("recurring_monitor_like").sum())
        expected_unlabeled = int(top10["cohort_hint"].eq("unmatched_other").sum())
        base_positive_rate = int(scores_df["cohort_hint"].isin({"eligible_local", "future_fault_linked"}).sum()) / total_labeled_count
        base_nuisance_rate = int(scores_df["cohort_hint"].isin({"nuisance_alert", "isolated_unexplained"}).sum()) / total_labeled_count

        top10_summary = topk_summary_df.loc[
            topk_summary_df["score_name"].eq("electrical_evt_minus_broadshape_score")
            & topk_summary_df["top_k"].eq(10)
        ].iloc[0]
        assert_true(int(top10_summary["topk_positive_like_count"]) == expected_positive, "top10 positive_like count mismatch")
        assert_true(int(top10_summary["topk_nuisance_like_count"]) == expected_nuisance, "top10 nuisance_like count mismatch")
        assert_true(int(top10_summary["topk_monitor_like_count"]) == expected_monitor, "top10 monitor_like count mismatch")
        assert_true(int(top10_summary["topk_unlabeled_other_count"]) == expected_unlabeled, "top10 unlabeled count mismatch")
        assert_true(abs(float(top10_summary["topk_positive_like_rate"]) - (expected_positive / selected_n)) < 1e-9, "top10 positive rate mismatch")
        assert_true(abs(float(top10_summary["topk_nuisance_like_rate"]) - (expected_nuisance / selected_n)) < 1e-9, "top10 nuisance rate mismatch")
        assert_true(abs(float(top10_summary["base_positive_like_rate"]) - base_positive_rate) < 1e-9, "base positive rate mismatch")
        assert_true(abs(float(top10_summary["base_nuisance_like_rate"]) - base_nuisance_rate) < 1e-9, "base nuisance rate mismatch")
        assert_true(
            abs(float(top10_summary["positive_like_lift"]) - ((expected_positive / selected_n) / (base_positive_rate + 1e-9))) < 1e-6,
            "positive_like_lift mismatch",
        )
        assert_true(
            abs(float(top10_summary["nuisance_like_lift"]) - ((expected_nuisance / selected_n) / (base_nuisance_rate + 1e-9))) < 1e-6,
            "nuisance_like_lift mismatch",
        )
        assert_true(
            abs(float(top10_summary["precision_minus_nuisance"]) - ((expected_positive / selected_n) - (expected_nuisance / selected_n))) < 1e-9,
            "precision_minus_nuisance mismatch",
        )

        top10_rows = topk_rows_df.loc[
            topk_rows_df["score_name"].eq("electrical_evt_minus_broadshape_score")
            & topk_rows_df["top_k"].eq(10)
        ].copy()
        assert_true(len(top10_rows) == 10, "top10 rows selection mismatch")
        assert_true(top10_rows["rank"].tolist() == list(range(1, 11)), "top10 rank assignment mismatch")
        assert_true(top10_rows.iloc[0]["panel_id"] == ranked_evt_minus.iloc[0]["panel_id"], "top10 first run mismatch")

        top20_rows = topk_rows_df.loc[
            topk_rows_df["score_name"].eq("electrical_evt_minus_broadshape_score")
            & topk_rows_df["top_k"].eq(20)
        ].copy()
        assert_true(len(top20_rows) == 20, "top20 rows should include top 20 runs")

        two_stage_50_rows = topk_rows_df.loc[
            topk_rows_df["score_name"].eq("two_stage_core50_penalty050")
            & topk_rows_df["top_k"].eq(100)
        ].copy().sort_values("rank", kind="stable")
        assert_true(len(two_stage_50_rows) == 100, "two-stage core50 top100 rows mismatch")
        assert_true(two_stage_50_rows["stage1_core_rank"].notna().all(), "stage1_core_rank missing for two-stage rows")
        assert_true(two_stage_50_rows["stage2_rerank_score"].notna().all(), "stage2_rerank_score missing for two-stage rows")
        assert_true(two_stage_50_rows.head(50)["stage1_core_rank"].astype(int).le(50).all(), "non-shortlist run leaked into top 50 of two-stage core50")
        assert_true(two_stage_50_rows.iloc[50:]["stage1_core_rank"].astype(int).gt(50).all(), "outside-shortlist ordering broken for two-stage core50")

        two_stage_100_rows = topk_rows_df.loc[
            topk_rows_df["score_name"].eq("two_stage_core100_penalty050")
            & topk_rows_df["top_k"].eq(100)
        ].copy().sort_values("rank", kind="stable")
        assert_true(len(two_stage_100_rows) == 100, "two-stage core100 top100 rows mismatch")
        assert_true(two_stage_100_rows["stage1_core_rank"].astype(int).le(100).all(), "two-stage core100 should contain only shortlisted runs in top100")

        stage1_core = scores_df.sort_values(
            ["electrical_core_score", "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
            ascending=[False, False, True, True, True, True],
            kind="stable",
        ).reset_index(drop=True)
        stage1_core["stage1_core_rank"] = range(1, len(stage1_core) + 1)
        shortlist50 = stage1_core.head(50).copy()
        shortlist50 = shortlist50.sort_values(
            ["electrical_core_minus_broadshape_050", "stage1_core_rank"],
            ascending=[False, True],
            kind="stable",
        ).reset_index(drop=True)
        expected_top10_two_stage = shortlist50.head(10).loc[:, ["panel_id", "stage1_core_rank"]].reset_index(drop=True)
        actual_top10_two_stage = two_stage_50_rows.head(10).loc[:, ["panel_id", "stage1_core_rank"]].copy()
        actual_top10_two_stage["stage1_core_rank"] = actual_top10_two_stage["stage1_core_rank"].astype(int)
        actual_top10_two_stage = actual_top10_two_stage.reset_index(drop=True)
        assert_true(actual_top10_two_stage.equals(expected_top10_two_stage), "two-stage shortlist rerank ordering mismatch")


if __name__ == "__main__":
    main()
