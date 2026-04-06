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

import research.prognostics.build_panel_day_engine_run_ranker_hybrid_audit_v1 as audit


def repo_root() -> Path:
    return REPO_ROOT


def make_feature_row(
    site: str,
    panel_idx: int,
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
    panel_id = f"{site}-panel-{panel_idx:03d}"
    pre_ews_day_count = int(round(run_day_count * min(ae_ratio, 1.0) * 0.35))
    ews_warning_day_count = int(round(run_day_count * min(ae_ratio, 1.0) * 0.2))
    pre_alarm_day_count = int(round(run_day_count * min(cond_evt_only_day_ratio, 1.0) * 0.25))
    prefault_b_day_count = int(round(run_day_count * 0.15))
    pre_alarm_max_run = min(run_day_count, pre_alarm_day_count)
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
        "cond_evt_day_ratio": min(1.0, cond_evt_only_day_ratio + 0.1),
        "cond_evt_only_day_ratio": cond_evt_only_day_ratio,
        "cond_evt_same_day_early_corroborated_day_ratio": min(1.0, cond_evt_only_day_ratio * 0.6),
        "ae_mid_or_hi_early_day_ratio": ae_ratio,
        "dtw_mid_or_hi_early_day_ratio": min(1.0, ae_ratio * 0.8),
        "hs_mid_or_hi_early_day_ratio": min(1.0, ae_ratio * 0.7),
        "max_recon_error": p95_recon_error * 1.2,
        "p95_recon_error": p95_recon_error,
        "max_dtw_dist": 1.0 + max_v_drop * 0.2,
        "p95_dtw_dist": 0.8 + max_v_drop * 0.18,
        "max_hs_score": 0.2 + ae_ratio * 0.5,
        "p95_hs_score": 0.15 + ae_ratio * 0.35,
        "min_mid_ratio": min_mid_ratio,
        "min_mid_v_ratio": min_mid_v_ratio,
        "min_mid_i_ratio": min_mid_v_ratio + 0.03,
        "max_v_drop": max_v_drop,
    }


def build_synthetic_root(root: Path) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    feature_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    score_rows: list[dict[str, object]] = []
    promotion_rows: list[dict[str, object]] = []

    site_specs = {
        "alpha": {"count": 120, "start": pd.Timestamp("2025-01-01"), "site_shift": 9.0},
        "beta": {"count": 60, "start": pd.Timestamp("2025-04-01"), "site_shift": 3.0},
        "gamma": {"count": 60, "start": pd.Timestamp("2025-07-01"), "site_shift": 2.2},
    }

    for site, spec in site_specs.items():
        for idx in range(spec["count"]):
            label_bucket = "unlabeled_other"
            training_label = "exclude"
            run_shape_class = "short_alert_run"
            cohort_hint = "unmatched_other"

            if idx < 8:
                label_bucket = "positive_like"
                training_label = "positive"
                run_shape_class = "chronic_alert_run"
                cohort_hint = "future_fault_linked"
            elif 8 <= idx < 16:
                label_bucket = "negative_like"
                training_label = "negative"
                run_shape_class = "medium_alert_run"
                cohort_hint = "nuisance_alert"
            elif 16 <= idx < 22:
                label_bucket = "monitor_like"
                training_label = "exclude"
                run_shape_class = "chronic_alert_run"
                cohort_hint = "recurring_monitor_like"
            elif 22 <= idx < 26:
                label_bucket = "common_cause_like"
                training_label = "exclude"
                run_shape_class = "short_alert_run"
                cohort_hint = "unmatched_other"
            elif 26 <= idx < 40:
                label_bucket = "unlabeled_other"
                training_label = "exclude"
                run_shape_class = "medium_alert_run"
                cohort_hint = "unmatched_other"

            max_v_drop = spec["site_shift"] + 0.06 * idx
            min_mid_v_ratio = max(0.1, 0.92 - 0.004 * idx)
            mean_signal_count = 0.8 + 0.03 * idx
            p95_recon_error = 0.03 + 0.002 * idx
            cond_evt_only_day_ratio = min(1.0, 0.08 + 0.01 * (idx % 12))
            ae_ratio = min(1.0, 0.12 + 0.01 * (idx % 14))
            min_mid_ratio = min_mid_v_ratio + 0.04
            max_signal_count = mean_signal_count + 0.8

            if label_bucket == "positive_like":
                max_v_drop += 1.0
                min_mid_v_ratio -= 0.12
                mean_signal_count += 1.1
                p95_recon_error += 0.08
                cond_evt_only_day_ratio = 0.65 + 0.02 * (idx % 3)
                ae_ratio = 0.8 + 0.03 * (idx % 3)
            elif label_bucket == "negative_like":
                max_v_drop += 0.4
                min_mid_v_ratio -= 0.05
                mean_signal_count += 0.3
                p95_recon_error += 0.02
                cond_evt_only_day_ratio = 0.2 + 0.02 * (idx % 3)
                ae_ratio = 0.25 + 0.02 * (idx % 3)
            elif run_shape_class == "medium_alert_run":
                max_v_drop += 0.5
                min_mid_v_ratio -= 0.03
                mean_signal_count += 0.5
                p95_recon_error += 0.03
                cond_evt_only_day_ratio = 0.45 + 0.01 * (idx % 4)
                ae_ratio = 0.55 + 0.01 * (idx % 4)

            # Force one alpha positive into the reference top50 but just outside reference top20.
            if site == "alpha" and idx == 7:
                max_v_drop = 9.6
                min_mid_v_ratio = 0.39
                min_mid_ratio = 0.43
                cond_evt_only_day_ratio = 0.98
                ae_ratio = 0.98
                mean_signal_count = 4.8
                max_signal_count = 5.8
                p95_recon_error = 0.34

            # Force one alpha negative into reference top50 so hybrid can over-promote it.
            if site == "alpha" and idx == 12:
                max_v_drop = 9.7
                min_mid_v_ratio = 0.36
                min_mid_ratio = 0.4
                cond_evt_only_day_ratio = 0.95
                ae_ratio = 0.96
                mean_signal_count = 4.4
                max_signal_count = 5.2
                p95_recon_error = 0.3

            # Force one alpha positive the reference ranks above hybrid.
            if site == "alpha" and idx == 6:
                max_v_drop = 10.8
                min_mid_v_ratio = 0.58
                min_mid_ratio = 0.62
                cond_evt_only_day_ratio = 0.3
                ae_ratio = 0.35
                mean_signal_count = 1.5
                max_signal_count = 2.2
                p95_recon_error = 0.08

            run_day_count = 4 + (idx % 6)
            run_start_date = (spec["start"] + pd.Timedelta(days=idx * 3)).strftime("%Y-%m-%d")
            feature_row = make_feature_row(
                site=site,
                panel_idx=idx,
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

            reference_score = max_v_drop * 1.4 + (1.0 - min_mid_v_ratio) * 5.5 + mean_signal_count * 0.4
            if site == "alpha" and idx == 7:
                reference_score = 10.8
            if site == "alpha" and idx == 12:
                reference_score = 10.7
            if site == "alpha" and idx == 6:
                reference_score = 11.6

            score_rows.append(
                {
                    "site": feature_row["site"],
                    "panel_id": feature_row["panel_id"],
                    "run_start_date": feature_row["run_start_date"],
                    "run_end_date": feature_row["run_end_date"],
                    "electrical_core_minus_broadshape_050": reference_score,
                }
            )

            if (site, idx) in {("alpha", 26), ("beta", 26), ("gamma", 26), ("gamma", 27)}:
                promotion_rows.append(
                    {
                        "scenario_name": audit.FIXED_SCENARIO_NAME,
                        "site": feature_row["site"],
                        "panel_id": feature_row["panel_id"],
                        "run_start_date": feature_row["run_start_date"],
                        "run_end_date": feature_row["run_end_date"],
                    }
                )
            if (site, idx) in {("alpha", 27), ("beta", 27)}:
                promotion_rows.append(
                    {
                        "scenario_name": "other_scenario_should_be_ignored",
                        "site": feature_row["site"],
                        "panel_id": feature_row["panel_id"],
                        "run_start_date": feature_row["run_start_date"],
                        "run_end_date": feature_row["run_end_date"],
                    }
                )

    pd.DataFrame(feature_rows).to_csv(share_dir / audit.FEATURE_TABLE_NAME, index=False, encoding="utf-8-sig")
    pd.DataFrame(label_rows).to_csv(share_dir / audit.LABEL_PACK_V2_NAME, index=False, encoding="utf-8-sig")
    pd.DataFrame(promotion_rows).to_csv(share_dir / audit.PROMOTION_SCENARIOS_NAME, index=False, encoding="utf-8-sig")
    pd.DataFrame(score_rows).to_csv(share_dir / audit.V0_SCORES_NAME, index=False, encoding="utf-8-sig")
    pd.DataFrame(
        [
            {
                "method_name": "logistic_v3_global_scaling",
                "fold_type": "leave_one_site_out",
                "mean_top20_positive_minus_negative": 0.04,
            },
            {
                "method_name": "logistic_v3_global_scaling",
                "fold_type": "time_holdout_70_30",
                "mean_top20_positive_minus_negative": 0.02,
            },
            {
                "method_name": "logistic_v3_site_conditioned_scaling",
                "fold_type": "leave_one_site_out",
                "mean_top20_positive_minus_negative": 0.03,
            },
            {
                "method_name": "logistic_v3_site_conditioned_scaling",
                "fold_type": "time_holdout_70_30",
                "mean_top20_positive_minus_negative": 0.025,
            },
        ]
    ).to_csv(share_dir / audit.SITE_SCALING_SUMMARY_NAME, index=False, encoding="utf-8-sig")


def assert_summary_deltas(summary_df: pd.DataFrame) -> None:
    loso = summary_df.loc[summary_df["fold_type"].eq("leave_one_site_out")].copy()
    reference_row = loso.loc[loso["method_name"].eq(audit.REFERENCE_METHOD_NAME)].iloc[0]
    hybrid_row = loso.loc[loso["method_name"].eq("hybrid_ref50_global")].iloc[0]
    expected_delta = float(hybrid_row["mean_top20_positive_minus_negative"]) - float(
        reference_row["mean_top20_positive_minus_negative"]
    )
    assert abs(float(hybrid_row["delta_mean_top20_vs_reference"]) - expected_delta) < 1e-9


def assert_shortlist_behavior(temp_root: Path) -> None:
    universe = audit.apply_promotions(audit.prepare_universe(temp_root), audit.load_promotions(temp_root))
    promotions = audit.load_promotions(temp_root)
    assert len(promotions) == 4

    alpha_spec = next(spec for spec in audit.fold_specs(universe) if spec["fold_id"] == "alpha")
    train_df = universe.loc[list(alpha_spec["train_index"])].copy()
    test_df = universe.loc[list(alpha_spec["test_index"])].copy()
    train_labeled = train_df.loc[train_df["scenario_training_label"].isin(audit.TRAIN_LABELS)].copy()
    scored_test = audit.score_test_universe(train_df, test_df, train_labeled)

    reference_ranked = audit.rank_runs(scored_test, audit.REFERENCE_SCORE_COL)
    hybrid50 = audit.build_hybrid_ranking(scored_test, audit.GLOBAL_LEARNED_SCORE_COL, 50)
    hybrid100 = audit.build_hybrid_ranking(scored_test, audit.SITE_LEARNED_SCORE_COL, 100)

    reference_top50 = set(map(tuple, reference_ranked.head(50)[audit.KEY_COLS].itertuples(index=False, name=None)))
    hybrid_top50 = set(map(tuple, hybrid50.head(50)[audit.KEY_COLS].itertuples(index=False, name=None)))
    assert hybrid_top50 == reference_top50

    reference_top100 = set(map(tuple, reference_ranked.head(100)[audit.KEY_COLS].itertuples(index=False, name=None)))
    hybrid100_top = set(map(tuple, hybrid100.head(100)[audit.KEY_COLS].itertuples(index=False, name=None)))
    hybrid100_tail = set(map(tuple, hybrid100.iloc[100:][audit.KEY_COLS].itertuples(index=False, name=None)))
    assert hybrid100_top == reference_top100
    assert hybrid100_tail.isdisjoint(reference_top100)

    reference_top10_list = list(map(tuple, reference_ranked.head(10)[audit.KEY_COLS].itertuples(index=False, name=None)))
    hybrid50_top10_list = list(map(tuple, hybrid50.head(10)[audit.KEY_COLS].itertuples(index=False, name=None)))
    assert reference_top10_list != hybrid50_top10_list


def main() -> None:
    root = repo_root()
    py_compile.compile(str(root / "pv_ae/panel_day_engine.py"), doraise=True)
    py_compile.compile(str(root / "research/prognostics/build_panel_day_engine_run_ranker_hybrid_audit_v1.py"), doraise=True)
    py_compile.compile(str(root / "research/prognostics/smoke_test_panel_day_engine_run_ranker_hybrid_audit_v1.py"), doraise=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_root = Path(tmpdir)
        build_synthetic_root(temp_root)

        subprocess.run(
            [sys.executable, str(root / "research/prognostics/build_panel_day_engine_run_ranker_hybrid_audit_v1.py"), "--root", str(temp_root)],
            check=True,
            cwd=root,
        )

        share_dir = temp_root / "_share"
        summary = pd.read_csv(share_dir / audit.SUMMARY_OUTPUT_NAME, encoding="utf-8-sig")
        topk_yield = pd.read_csv(share_dir / audit.TOPK_OUTPUT_NAME, encoding="utf-8-sig")
        cases = pd.read_csv(share_dir / audit.CASES_OUTPUT_NAME, encoding="utf-8-sig")

        assert set(summary["method_name"]) == set(audit.VISIBLE_METHOD_NAMES)
        assert set(topk_yield["method_name"]) == set(audit.VISIBLE_METHOD_NAMES)
        assert summary["valid_fold_count"].min() >= 1
        assert not cases.empty
        assert set(cases["disagreement_class"]).issubset(set(audit.DISAGREEMENT_CLASSES))

        assert_shortlist_behavior(temp_root)
        assert_summary_deltas(summary)


if __name__ == "__main__":
    main()
