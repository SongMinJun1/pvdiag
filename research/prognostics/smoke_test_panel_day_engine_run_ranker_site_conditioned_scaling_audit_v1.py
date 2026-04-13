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

import research.prognostics.build_panel_day_engine_run_ranker_site_conditioned_scaling_audit_v1 as audit

SITE_METHOD_NAME = audit.SITE_METHOD_NAME
GLOBAL_METHOD_NAME = audit.GLOBAL_METHOD_NAME
REFERENCE_METHOD_NAME = audit.REFERENCE_METHOD_NAME
FIXED_SCENARIO_NAME = audit.FIXED_SCENARIO_NAME


def repo_root() -> Path:
    return REPO_ROOT


def make_feature_row(
    site: str,
    panel_suffix: str,
    run_index: int,
    run_start_date: str,
    run_day_count: int,
    run_shape_class: str,
    cohort_hint: str,
    max_v_drop: float,
    min_mid_v_ratio: float,
    min_mid_ratio: float,
    cond_evt_only_day_ratio: float,
    ae_ratio: float,
    mean_signal_count: float,
    max_signal_count: float,
    p95_recon_error: float,
) -> dict[str, object]:
    pre_ews_day_count = int(round(run_day_count * min(ae_ratio, 1.0) * 0.35))
    ews_warning_day_count = int(round(run_day_count * min(ae_ratio, 1.0) * 0.2))
    pre_alarm_day_count = int(round(run_day_count * min(cond_evt_only_day_ratio, 1.0) * 0.2))
    prefault_b_day_count = int(round(run_day_count * 0.15))
    pre_alarm_max_run = min(pre_alarm_day_count, run_day_count)
    cond_evt_day_ratio = min(1.0, cond_evt_only_day_ratio + 0.1)
    corroborated_ratio = min(1.0, cond_evt_only_day_ratio * 0.6)
    dtw_ratio = min(1.0, ae_ratio * 0.8)
    hs_ratio = min(1.0, ae_ratio * 0.7)
    max_recon_error = p95_recon_error * 1.2
    max_dtw_dist = 1.0 + max_v_drop * 0.25
    p95_dtw_dist = 0.8 + max_v_drop * 0.2
    max_hs_score = 0.2 + ae_ratio * 0.5
    p95_hs_score = 0.15 + ae_ratio * 0.35
    min_mid_i_ratio = min_mid_v_ratio + 0.03
    panel_id = f"{site}-panel-{panel_suffix}"
    return {
        "site": site,
        "panel_id": panel_id,
        "run_start_date": run_start_date,
        "run_end_date": (pd.Timestamp(run_start_date) + pd.Timedelta(days=run_day_count - 1)).strftime("%Y-%m-%d"),
        "run_day_count": run_day_count,
        "run_shape_class": run_shape_class,
        "cohort_hint": cohort_hint,
        "pre_ews_day_count": pre_ews_day_count,
        "ews_warning_day_count": ews_warning_day_count,
        "pre_alarm_day_count": pre_alarm_day_count,
        "prefault_B_day_count": prefault_b_day_count,
        "pre_alarm_max_run": pre_alarm_max_run,
        "max_signal_count": max_signal_count,
        "mean_signal_count": mean_signal_count,
        "any_data_bad": 0,
        "data_bad_day_ratio": 0.0,
        "cond_evt_day_ratio": cond_evt_day_ratio,
        "cond_evt_only_day_ratio": cond_evt_only_day_ratio,
        "cond_evt_same_day_early_corroborated_day_ratio": corroborated_ratio,
        "ae_mid_or_hi_early_day_ratio": ae_ratio,
        "dtw_mid_or_hi_early_day_ratio": dtw_ratio,
        "hs_mid_or_hi_early_day_ratio": hs_ratio,
        "max_recon_error": max_recon_error,
        "p95_recon_error": p95_recon_error,
        "max_dtw_dist": max_dtw_dist,
        "p95_dtw_dist": p95_dtw_dist,
        "max_hs_score": max_hs_score,
        "p95_hs_score": p95_hs_score,
        "min_mid_ratio": min_mid_ratio,
        "min_mid_v_ratio": min_mid_v_ratio,
        "min_mid_i_ratio": min_mid_i_ratio,
        "max_v_drop": max_v_drop,
    }


def base_feature_profile(site: str, kind: str, idx: int) -> tuple[float, float, float, float, float, float]:
    site_base = {
        "alpha": {"drop": 10.0, "ratio": 0.48, "signal": 3.8, "recon": 0.28},
        "beta": {"drop": 3.2, "ratio": 0.84, "signal": 1.3, "recon": 0.07},
        "gamma": {"drop": 2.2, "ratio": 0.90, "signal": 1.0, "recon": 0.05},
    }[site]
    kind_offset = {
        "positive": (1.6, -0.12, 1.4, 0.10, 0.75, 0.95),
        "positive_soft": (0.8, -0.05, 0.8, 0.04, 0.55, 0.7),
        "negative": (0.4, -0.03, 0.3, 0.015, 0.25, 0.35),
        "negative_extreme_rel": (1.1, -0.09, 1.0, 0.055, 0.65, 0.85),
        "unlabeled_high": (0.9, -0.05, 0.8, 0.045, 0.5, 0.65),
        "unlabeled": (0.1, -0.01, 0.1, 0.005, 0.1, 0.2),
        "monitor": (0.6, -0.04, 0.4, 0.03, 0.4, 0.55),
        "common_cause": (0.2, -0.02, 0.2, 0.01, 0.2, 0.25),
    }[kind]
    jitter = (idx % 3) * 0.03
    max_v_drop = site_base["drop"] + kind_offset[0] + jitter
    min_mid_v_ratio = max(0.1, site_base["ratio"] + kind_offset[1] - jitter * 0.2)
    mean_signal_count = site_base["signal"] + kind_offset[2] + jitter
    p95_recon_error = site_base["recon"] + kind_offset[3] + jitter * 0.01
    cond_evt_only_day_ratio = min(1.0, kind_offset[4] + jitter)
    ae_ratio = min(1.0, kind_offset[5] + jitter)
    min_mid_ratio = max(0.1, min_mid_v_ratio + 0.05)
    max_signal_count = mean_signal_count + 1.0
    return (
        max_v_drop,
        min_mid_v_ratio,
        min_mid_ratio,
        cond_evt_only_day_ratio,
        ae_ratio,
        mean_signal_count,
        max_signal_count,
        p95_recon_error,
    )


def build_synthetic_root(root: Path) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    feature_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    score_rows: list[dict[str, object]] = []
    promotion_rows: list[dict[str, object]] = []

    site_dates = {"alpha": "2025-01-01", "beta": "2025-03-01", "gamma": "2025-05-01"}

    for site in ["alpha", "beta", "gamma"]:
        start = pd.Timestamp(site_dates[site])
        for idx in range(30):
            label_bucket = "unlabeled_other"
            training_label = "exclude"
            kind = "unlabeled"
            run_shape_class = "short_alert_run"
            cohort_hint = "unmatched_other"

            if idx < 3:
                label_bucket = "positive_like"
                training_label = "positive"
                kind = "positive"
                run_shape_class = "chronic_alert_run"
                cohort_hint = "future_fault_linked"
            elif idx == 3 and site == "alpha":
                label_bucket = "positive_like"
                training_label = "positive"
                kind = "positive_soft"
                run_shape_class = "medium_alert_run"
                cohort_hint = "future_fault_linked"
            elif 3 <= idx < 6 and site != "alpha":
                label_bucket = "negative_like"
                training_label = "negative"
                kind = "negative"
                run_shape_class = "medium_alert_run"
                cohort_hint = "nuisance_alert"
            elif 4 <= idx < 7 and site == "alpha":
                label_bucket = "negative_like"
                training_label = "negative"
                kind = "negative"
                run_shape_class = "medium_alert_run"
                cohort_hint = "nuisance_alert"
            elif idx == 6 and site == "beta":
                label_bucket = "negative_like"
                training_label = "negative"
                kind = "negative_extreme_rel"
                run_shape_class = "medium_alert_run"
                cohort_hint = "nuisance_alert"
            elif idx in {7, 8}:
                label_bucket = "monitor_like"
                training_label = "exclude"
                kind = "monitor"
                run_shape_class = "chronic_alert_run"
                cohort_hint = "recurring_monitor_like"
            elif idx in {9, 10}:
                label_bucket = "common_cause_like"
                training_label = "exclude"
                kind = "common_cause"
                run_shape_class = "short_alert_run"
                cohort_hint = "unmatched_other"
            elif (site == "alpha" and 11 <= idx <= 24) or (site != "alpha" and idx in {11, 12, 13, 14, 15}):
                label_bucket = "unlabeled_other"
                training_label = "exclude"
                kind = "unlabeled_high"
                run_shape_class = "medium_alert_run"
                cohort_hint = "unmatched_other"

            (
                max_v_drop,
                min_mid_v_ratio,
                min_mid_ratio,
                cond_evt_only_day_ratio,
                ae_ratio,
                mean_signal_count,
                max_signal_count,
                p95_recon_error,
            ) = base_feature_profile(site, kind, idx)

            if site == "gamma" and idx == 2:
                # Positive the deterministic reference should still rank high.
                max_v_drop = 2.25
                min_mid_v_ratio = 0.91
                min_mid_ratio = 0.95
                cond_evt_only_day_ratio = 0.08
                ae_ratio = 0.12
                mean_signal_count = 1.0
                max_signal_count = 1.4
                p95_recon_error = 0.04

            if site == "alpha" and idx == 3:
                max_v_drop = 10.25
                min_mid_v_ratio = 0.31
                min_mid_ratio = 0.36
                cond_evt_only_day_ratio = 0.92
                ae_ratio = 0.96
                mean_signal_count = 4.6
                max_signal_count = 5.4
                p95_recon_error = 0.31

            run_day_count = 4 + (idx % 4)
            run_start_date = (start + pd.Timedelta(days=idx * 5)).strftime("%Y-%m-%d")
            panel_suffix = f"{idx:02d}"
            feature_row = make_feature_row(
                site=site,
                panel_suffix=panel_suffix,
                run_index=idx,
                run_start_date=run_start_date,
                run_day_count=run_day_count,
                run_shape_class=run_shape_class,
                cohort_hint=cohort_hint,
                max_v_drop=max_v_drop,
                min_mid_v_ratio=min_mid_v_ratio,
                min_mid_ratio=min_mid_ratio,
                cond_evt_only_day_ratio=cond_evt_only_day_ratio,
                ae_ratio=ae_ratio,
                mean_signal_count=mean_signal_count,
                max_signal_count=max_signal_count,
                p95_recon_error=p95_recon_error,
            )
            feature_rows.append(feature_row)
            label_rows.append(
                {
                    "site": feature_row["site"],
                    "panel_id": feature_row["panel_id"],
                    "run_start_date": feature_row["run_start_date"],
                    "run_end_date": feature_row["run_end_date"],
                    "label_bucket_v2": label_bucket,
                    "training_label_v2": training_label,
                }
            )

            reference_score = max_v_drop * 0.9 + (1.0 - min_mid_v_ratio) * 5.0 + mean_signal_count * 0.7
            if site == "gamma" and idx == 2:
                reference_score = 15.0
            if site == "alpha" and idx == 3:
                reference_score = 6.0
            if site == "beta" and idx == 6:
                reference_score = 5.0

            score_rows.append(
                {
                    "site": feature_row["site"],
                    "panel_id": feature_row["panel_id"],
                    "run_start_date": feature_row["run_start_date"],
                    "run_end_date": feature_row["run_end_date"],
                    "electrical_core_minus_broadshape_050": reference_score,
                }
            )

            if (site, idx) in {("beta", 11), ("gamma", 11), ("alpha", 11)}:
                promotion_rows.append(
                    {
                        "scenario_name": FIXED_SCENARIO_NAME,
                        "site": feature_row["site"],
                        "panel_id": feature_row["panel_id"],
                        "run_start_date": feature_row["run_start_date"],
                        "run_end_date": feature_row["run_end_date"],
                    }
                )
            if (site, idx) in {("beta", 12), ("gamma", 12)}:
                promotion_rows.append(
                    {
                        "scenario_name": "other_scenario_should_be_ignored",
                        "site": feature_row["site"],
                        "panel_id": feature_row["panel_id"],
                        "run_start_date": feature_row["run_start_date"],
                        "run_end_date": feature_row["run_end_date"],
                    }
                )

    feature_df = pd.DataFrame(feature_rows)
    label_df = pd.DataFrame(label_rows)
    score_df = pd.DataFrame(score_rows)
    promotion_df = pd.DataFrame(promotion_rows)
    v3_summary_df = pd.DataFrame(
        [
            {
                "scenario_name": FIXED_SCENARIO_NAME,
                "loso_mean_top20_positive_minus_negative": 0.05,
                "time_mean_top20_positive_minus_negative": 0.01,
            }
        ]
    )

    feature_df.to_csv(share_dir / audit.FEATURE_TABLE_NAME, index=False, encoding="utf-8-sig")
    label_df.to_csv(share_dir / audit.LABEL_PACK_V2_NAME, index=False, encoding="utf-8-sig")
    promotion_df.to_csv(share_dir / audit.PROMOTION_SCENARIOS_NAME, index=False, encoding="utf-8-sig")
    score_df.to_csv(share_dir / audit.V0_SCORES_NAME, index=False, encoding="utf-8-sig")
    v3_summary_df.to_csv(share_dir / audit.V3_SCENARIO_SUMMARY_NAME, index=False, encoding="utf-8-sig")


def assert_summary_deltas(summary_df: pd.DataFrame) -> None:
    loso = summary_df.loc[summary_df["fold_type"].eq("leave_one_site_out")].copy()
    global_row = loso.loc[loso["method_name"].eq(GLOBAL_METHOD_NAME)].iloc[0]
    site_row = loso.loc[loso["method_name"].eq(SITE_METHOD_NAME)].iloc[0]
    reference_row = loso.loc[loso["method_name"].eq(REFERENCE_METHOD_NAME)].iloc[0]

    expected_site_delta_global = float(site_row["mean_top20_positive_minus_negative"]) - float(
        global_row["mean_top20_positive_minus_negative"]
    )
    assert abs(float(site_row["delta_mean_top20_vs_global_logistic"]) - expected_site_delta_global) < 1e-9

    expected_global_delta_reference = float(global_row["mean_top20_positive_minus_negative"]) - float(
        reference_row["mean_top20_positive_minus_negative"]
    )
    assert abs(float(global_row["delta_mean_top20_vs_reference"]) - expected_global_delta_reference) < 1e-9


def main() -> None:
    root = repo_root()
    py_compile.compile(str(root / "pv_ae/panel_day_engine.py"), doraise=True)
    py_compile.compile(str(root / "research/prognostics/build_panel_day_engine_run_ranker_site_conditioned_scaling_audit_v1.py"), doraise=True)
    py_compile.compile(
        str(root / "research/prognostics/smoke_test_panel_day_engine_run_ranker_site_conditioned_scaling_audit_v1.py"),
        doraise=True,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_root = Path(tmpdir)
        build_synthetic_root(temp_root)

        subprocess.run(
            [
                sys.executable,
                str(root / "research/prognostics/build_panel_day_engine_run_ranker_site_conditioned_scaling_audit_v1.py"),
                "--root",
                str(temp_root),
            ],
            check=True,
            cwd=root,
        )

        share_dir = temp_root / "_share"
        fold_scores = pd.read_csv(share_dir / audit.FOLD_SCORES_OUTPUT_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(share_dir / audit.SUMMARY_OUTPUT_NAME, encoding="utf-8-sig")
        cases = pd.read_csv(share_dir / audit.CASES_OUTPUT_NAME, encoding="utf-8-sig")

        assert set(summary["method_name"]) == {
            GLOBAL_METHOD_NAME,
            SITE_METHOD_NAME,
            REFERENCE_METHOD_NAME,
        }
        assert summary["valid_fold_count"].min() >= 1

        alpha_fold = fold_scores.loc[
            (fold_scores["fold_type"] == "leave_one_site_out")
            & (fold_scores["fold_id"] == "alpha")
            & (fold_scores["method_name"] == GLOBAL_METHOD_NAME)
        ].iloc[0]
        assert int(alpha_fold["train_positive_count"]) == 8
        assert int(alpha_fold["train_negative_count"]) == 7

        assert summary.loc[summary["method_name"].eq(SITE_METHOD_NAME), "note_ko"].str.contains("exploratory").any()
        assert_summary_deltas(summary)

        disagreement_classes = set(cases["disagreement_class"].dropna().astype(str))
        assert not cases.empty
        assert disagreement_classes.issubset(
            {
                "positive_captured_by_site_scaled_not_global",
                "positive_captured_by_reference_not_site_scaled",
                "negative_promoted_by_site_scaled_not_global",
            }
        )

        assert cases["logistic_v3_global_scaling_score"].notna().all()
        assert cases["logistic_v3_site_conditioned_scaling_score"].notna().all()


if __name__ == "__main__":
    main()
