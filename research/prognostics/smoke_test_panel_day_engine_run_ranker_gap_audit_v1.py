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
LABEL_PACK_V2_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "label_bucket_v2", "training_label_v2"]
PROMOTION_SCENARIO_COLS = [
    "scenario_name",
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "candidate_priority_band",
    "electrical_core_minus_broadshape_050",
    "watch_now_panel_ref_flag",
    "site_positive_gap_flag",
    "scenario_label_source",
    "promotion_reason_ko",
]
V0_SCORE_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "electrical_core_score", "electrical_core_minus_broadshape_050"]
V2_SUMMARY_COLS = ["score_name", "fold_type", "mean_top20_positive_minus_negative"]
V3_SUMMARY_COLS = ["scenario_name", "loso_mean_top20_positive_minus_negative", "time_mean_top20_positive_minus_negative"]


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
    positive_like_features: bool,
    cohort_hint: str,
) -> dict[str, object]:
    if positive_like_features:
        max_v_drop = 0.92
        min_mid_v_ratio = 0.22
        min_mid_ratio = 0.28
        cond_evt_only_day_ratio = 0.86
        ae_ratio = 0.14
        mean_signal = 1.2
        max_signal = 1.5
        p95_recon = 0.16
    else:
        max_v_drop = 0.15
        min_mid_v_ratio = 0.93
        min_mid_ratio = 0.91
        cond_evt_only_day_ratio = 0.10
        ae_ratio = 0.90
        mean_signal = 3.5
        max_signal = 4.0
        p95_recon = 0.84
    return {
        "site": site,
        "panel_id": panel_id,
        "run_start_date": date,
        "run_end_date": date,
        "run_day_count": 3,
        "run_shape_class": "medium_alert_run",
        "overlap_case_class": "unmatched_to_review",
        "delta_run_class": "added_run",
        "fate_class": "",
        "cohort_hint": cohort_hint,
        "pre_ews_day_count": 3,
        "ews_warning_day_count": 2,
        "pre_alarm_day_count": 1,
        "prefault_B_day_count": 0,
        "pre_ews_run_count": 1,
        "ews_warning_run_count": 1,
        "pre_alarm_run_count": 1,
        "prefault_B_run_count": 0,
        "pre_alarm_max_run": 2,
        "max_signal_count": max_signal,
        "mean_signal_count": mean_signal,
        "any_data_bad": 0,
        "data_bad_day_ratio": 0.0,
        "cond_evt_day_ratio": 1.0,
        "cond_evt_only_day_ratio": cond_evt_only_day_ratio,
        "cond_evt_same_day_early_corroborated_day_ratio": 1.0 - cond_evt_only_day_ratio,
        "ae_mid_or_hi_early_day_ratio": ae_ratio,
        "dtw_mid_or_hi_early_day_ratio": 0.5,
        "hs_mid_or_hi_early_day_ratio": 0.25,
        "max_recon_error": p95_recon,
        "p95_recon_error": p95_recon,
        "max_dtw_dist": max_signal * 10.0,
        "p95_dtw_dist": max_signal * 9.0,
        "max_hs_score": ae_ratio,
        "p95_hs_score": ae_ratio,
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


def v0_row(feature: dict[str, object], electrical_core_score: float, electrical_core_minus_broadshape_050: float) -> dict[str, object]:
    return {
        "site": feature["site"],
        "panel_id": feature["panel_id"],
        "run_start_date": feature["run_start_date"],
        "run_end_date": feature["run_end_date"],
        "electrical_core_score": electrical_core_score,
        "electrical_core_minus_broadshape_050": electrical_core_minus_broadshape_050,
    }


def scenario_row(
    scenario_name: str,
    feature: dict[str, object],
    *,
    candidate_priority_band: str,
    score: float,
) -> dict[str, object]:
    return {
        "scenario_name": scenario_name,
        "site": feature["site"],
        "panel_id": feature["panel_id"],
        "run_start_date": feature["run_start_date"],
        "run_end_date": feature["run_end_date"],
        "candidate_priority_band": candidate_priority_band,
        "electrical_core_minus_broadshape_050": score,
        "watch_now_panel_ref_flag": 0,
        "site_positive_gap_flag": 0,
        "scenario_label_source": "weak_positive_promotion",
        "promotion_reason_ko": "synthetic promotion",
    }


def build_fixture_root(tmp_root: Path) -> None:
    features: list[dict[str, object]] = []
    labels: list[dict[str, object]] = []
    scores: list[dict[str, object]] = []
    promotions: list[dict[str, object]] = []

    def add_run(site: str, panel_id: str, date: str, positive_features: bool, bucket: str, train: str, core: float, ref: float) -> dict[str, object]:
        feature = feature_row(site, panel_id, date, positive_like_features=positive_features, cohort_hint=bucket)
        features.append(feature)
        labels.append(label_row(feature, bucket, train))
        scores.append(v0_row(feature, core, ref))
        return feature

    # alpha test site: create all four disagreement classes
    add_run("alpha", "alpha.pos.base1", "2025-01-01", True, "positive_like", "positive", 0.82, 0.84)
    add_run("alpha", "alpha.pos.base2", "2025-01-02", True, "positive_like", "positive", 0.80, 0.82)
    add_run("alpha", "alpha.pos.base3", "2025-01-03", True, "positive_like", "positive", 0.78, 0.80)
    add_run("alpha", "alpha.neg.base1", "2025-01-04", False, "negative_like", "negative", 0.18, 0.20)
    add_run("alpha", "alpha.neg.base2", "2025-01-05", False, "negative_like", "negative", 0.20, 0.22)
    add_run("alpha", "alpha.neg.base3", "2025-01-06", False, "negative_like", "negative", 0.22, 0.24)
    add_run("alpha", "alpha.pos.refmiss", "2025-01-07", False, "positive_like", "positive", 0.25, 0.98)
    add_run("alpha", "alpha.pos.loggain", "2025-01-08", True, "positive_like", "positive", 0.28, 0.12)
    add_run("alpha", "alpha.neg.logfalse", "2025-01-09", True, "negative_like", "negative", 0.30, 0.14)
    add_run("alpha", "alpha.neg.reffalse", "2025-01-10", False, "negative_like", "negative", 0.24, 0.97)
    for idx in range(11, 26):
        positive_features = idx % 3 == 0
        core = 0.45 + (idx % 4) * 0.03
        ref = 0.45 + (idx % 5) * 0.05
        add_run("alpha", f"alpha.excl.{idx}", f"2025-01-{idx:02d}", positive_features, "unlabeled_other", "exclude", core, ref)

    # beta, gamma train support
    beta_fixed = add_run("beta", "beta.prom.fixed", "2025-02-01", True, "unlabeled_other", "exclude", 0.62, 0.58)
    beta_other = add_run("beta", "beta.prom.other", "2025-02-02", True, "unlabeled_other", "exclude", 0.63, 0.59)
    gamma_fixed = add_run("gamma", "gamma.prom.fixed", "2025-03-01", True, "unlabeled_other", "exclude", 0.61, 0.57)

    for site, month in [("beta", "02"), ("gamma", "03")]:
        add_run(site, f"{site}.pos.1", f"2025-{month}-03", True, "positive_like", "positive", 0.82, 0.84)
        add_run(site, f"{site}.pos.2", f"2025-{month}-04", True, "positive_like", "positive", 0.80, 0.82)
        add_run(site, f"{site}.pos.3", f"2025-{month}-05", True, "positive_like", "positive", 0.78, 0.80)
        add_run(site, f"{site}.neg.1", f"2025-{month}-06", False, "negative_like", "negative", 0.18, 0.20)
        add_run(site, f"{site}.neg.2", f"2025-{month}-07", False, "negative_like", "negative", 0.20, 0.22)
        add_run(site, f"{site}.neg.3", f"2025-{month}-08", False, "negative_like", "negative", 0.22, 0.24)
        add_run(site, f"{site}.excl.1", f"2025-{month}-09", True, "unlabeled_other", "exclude", 0.58, 0.54)
        add_run(site, f"{site}.excl.2", f"2025-{month}-10", False, "unlabeled_other", "exclude", 0.40, 0.44)

    promotions.extend(
        [
            scenario_row("p1_plus_site_balanced_p2", beta_fixed, candidate_priority_band="P2", score=8.5),
            scenario_row("p1_plus_site_balanced_p2", gamma_fixed, candidate_priority_band="P2", score=8.4),
            scenario_row("p1_only", beta_other, candidate_priority_band="P1", score=8.9),
        ]
    )

    v2_summary_rows = [
        {"score_name": "electrical_core_minus_broadshape_050", "fold_type": "leave_one_site_out", "mean_top20_positive_minus_negative": 0.20},
        {"score_name": "electrical_core_minus_broadshape_050", "fold_type": "time_holdout_70_30", "mean_top20_positive_minus_negative": 0.10},
        {"score_name": "logistic_v2_holdout", "fold_type": "leave_one_site_out", "mean_top20_positive_minus_negative": 0.12},
        {"score_name": "logistic_v2_holdout", "fold_type": "time_holdout_70_30", "mean_top20_positive_minus_negative": 0.08},
    ]
    v3_summary_rows = [
        {"scenario_name": "p1_only", "loso_mean_top20_positive_minus_negative": 0.11, "time_mean_top20_positive_minus_negative": 0.08},
        {"scenario_name": "p1_plus_site_balanced_p2", "loso_mean_top20_positive_minus_negative": 0.15, "time_mean_top20_positive_minus_negative": 0.08},
    ]

    write_csv(tmp_root / "_share" / "panel_day_engine_run_feature_table_v1.csv", features, FEATURE_TABLE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_label_pack_v2.csv", labels, LABEL_PACK_V2_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_label_promotion_scenarios_v1.csv", promotions, PROMOTION_SCENARIO_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v0_scores.csv", scores, V0_SCORE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v2_holdout_summary.csv", v2_summary_rows, V2_SUMMARY_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v3_scenario_holdout_summary_v1.csv", v3_summary_rows, V3_SUMMARY_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_run_ranker_gap_audit_v1.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_run_ranker_gap_audit_folds_v1.csv",
        repo_root / "_share" / "panel_day_engine_run_ranker_gap_audit_cases_v1.csv",
        repo_root / "_share" / "panel_day_engine_run_ranker_gap_audit_summary_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    with tempfile.TemporaryDirectory(prefix="ranker_gap_audit_smoke_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        compile_result = run(
            [
                sys.executable,
                "-m",
                "py_compile",
                "pv_ae/panel_day_engine.py",
                "research/prognostics/build_panel_day_engine_run_ranker_gap_audit_v1.py",
                "research/prognostics/smoke_test_panel_day_engine_run_ranker_gap_audit_v1.py",
            ],
            repo_root,
        )
        assert_true(compile_result.returncode == 0, compile_result.stderr)

        build_result = run(
            [sys.executable, str(build_path), "--root", str(tmp_root)],
            repo_root,
        )
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        folds = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_gap_audit_folds_v1.csv", encoding="utf-8-sig")
        cases = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_gap_audit_cases_v1.csv", encoding="utf-8-sig")
        summary = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_gap_audit_summary_v1.csv", encoding="utf-8-sig")

        alpha_logistic = folds.loc[
            (folds["fold_type"].eq("leave_one_site_out"))
            & (folds["fold_id"].eq("alpha"))
            & (folds["method_name"].eq("logistic_v3_candidate"))
        ].iloc[0]
        assert_true(int(alpha_logistic["train_positive_count"]) == 8, "scenario selection should only use p1_plus_site_balanced_p2 promotions")

        alpha_cases = cases.loc[cases["fold_id"].eq("alpha")].copy()
        observed_classes = set(alpha_cases["disagreement_class"])
        expected_classes = {
            "positive_captured_by_reference_not_logistic",
            "positive_captured_by_logistic_not_reference",
            "negative_promoted_by_logistic_not_reference",
            "negative_promoted_by_reference_not_logistic",
        }
        assert_true(expected_classes.issubset(observed_classes), f"missing disagreement classes: {expected_classes - observed_classes}")

        pos_ref = alpha_cases.loc[alpha_cases["disagreement_class"].eq("positive_captured_by_reference_not_logistic")]
        assert_true("alpha.pos.refmiss" in set(pos_ref["panel_id"]), "reference-only positive should be detected")
        neg_log = alpha_cases.loc[alpha_cases["disagreement_class"].eq("negative_promoted_by_logistic_not_reference")]
        assert_true("alpha.neg.logfalse" in set(neg_log["panel_id"]), "logistic-only negative should be detected")

        loso_pos_ref_summary = summary.loc[
            (summary["summary_type"].eq("disagreement_summary"))
            & (summary["fold_type"].eq("leave_one_site_out"))
            & (summary["disagreement_class"].eq("positive_captured_by_reference_not_logistic"))
        ].iloc[0]
        assert_true(int(loso_pos_ref_summary["run_count"]) == 1, "LOSO positive reference-only summary count mismatch")

        recommendation = summary.loc[summary["summary_type"].eq("overall_recommendation")].iloc[0]
        assert_true(
            str(recommendation["recommended_next_direction"]) == "try_deterministic_plus_learned_hybrid",
            "recommendation heuristic mismatch",
        )

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
