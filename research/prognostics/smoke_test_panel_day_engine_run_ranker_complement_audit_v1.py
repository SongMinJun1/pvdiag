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
LABEL_PACK_V3_COLS = [*KEY_COLS, "label_bucket_v3", "training_label_v3"]
V0_COLS = [*KEY_COLS, "electrical_core_minus_broadshape_050"]


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
    return {
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
        "cond_evt_same_day_early_corroborated_day_ratio": min(cond_evt_day_ratio, 0.7),
        "ae_mid_or_hi_early_day_ratio": ae_mid_or_hi_early_day_ratio,
        "dtw_mid_or_hi_early_day_ratio": ae_mid_or_hi_early_day_ratio * 0.9,
        "hs_mid_or_hi_early_day_ratio": ae_mid_or_hi_early_day_ratio * 0.8,
        "max_recon_error": p95_recon_error + 0.03,
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


def date_for(site_offset: int, run_idx: int) -> tuple[str, str]:
    start_day = 1 + site_offset * 50 + run_idx
    start = pd.Timestamp("2026-01-01") + pd.Timedelta(days=start_day)
    end = start + pd.Timedelta(days=1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def build_fixture_root(tmp_root: Path) -> None:
    share_dir = tmp_root / "_share"
    feature_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    v0_rows: list[dict[str, object]] = []

    sites = ["alpha", "beta"]
    for site_offset, site in enumerate(sites):
        for run_idx in range(40):
            panel_id = f"{site}.run.{run_idx:02d}"
            start, end = date_for(site_offset, run_idx)
            label_bucket_v3 = "unlabeled_other"
            training_label_v3 = "exclude"
            run_shape_class = "medium_alert_run"

            # default unlabeled background
            feature_kwargs = dict(
                run_shape_class=run_shape_class,
                run_day_count=2,
                pre_ews_day_count=0,
                ews_warning_day_count=0,
                pre_alarm_day_count=0,
                max_signal_count=1.0,
                mean_signal_count=1.0,
                cond_evt_day_ratio=0.20,
                cond_evt_only_day_ratio=0.15,
                ae_mid_or_hi_early_day_ratio=0.20,
                p95_recon_error=0.03,
                max_v_drop=0.20,
                min_mid_ratio=0.82,
                min_mid_v_ratio=0.80,
            )
            reference_score = 6.0 - (run_idx * 0.08)

            if run_idx in {0, 1, 2, 3, 4}:
                label_bucket_v3 = "positive_like"
                training_label_v3 = "positive"
                feature_kwargs.update(
                    run_day_count=3,
                    pre_ews_day_count=2,
                    ews_warning_day_count=1,
                    pre_alarm_day_count=1,
                    max_signal_count=3.0,
                    mean_signal_count=2.4,
                    cond_evt_day_ratio=0.88,
                    cond_evt_only_day_ratio=0.80,
                    ae_mid_or_hi_early_day_ratio=0.90,
                    p95_recon_error=0.08,
                    max_v_drop=0.70,
                    min_mid_ratio=0.42,
                    min_mid_v_ratio=0.40,
                )
                reference_score = 9.5 - run_idx * 0.2

            if run_idx in {5, 6, 7, 8, 9}:
                label_bucket_v3 = "negative_like"
                training_label_v3 = "negative"
                feature_kwargs.update(
                    run_day_count=3,
                    pre_ews_day_count=0,
                    ews_warning_day_count=0,
                    pre_alarm_day_count=0,
                    max_signal_count=1.2,
                    mean_signal_count=1.1,
                    cond_evt_day_ratio=0.18,
                    cond_evt_only_day_ratio=0.10,
                    ae_mid_or_hi_early_day_ratio=0.18,
                    p95_recon_error=0.025,
                    max_v_drop=0.18,
                    min_mid_ratio=0.84,
                    min_mid_v_ratio=0.82,
                )
                reference_score = 5.0 - (run_idx - 5) * 0.1

            # positive logistic-only
            if run_idx == 1:
                feature_kwargs.update(
                    run_day_count=4,
                    pre_ews_day_count=3,
                    ews_warning_day_count=2,
                    pre_alarm_day_count=1,
                    max_signal_count=3.2,
                    mean_signal_count=2.6,
                    cond_evt_day_ratio=0.92,
                    cond_evt_only_day_ratio=0.86,
                    ae_mid_or_hi_early_day_ratio=0.94,
                    p95_recon_error=0.09,
                    max_v_drop=0.74,
                    min_mid_ratio=0.39,
                    min_mid_v_ratio=0.37,
                )
                reference_score = 2.2

            # positive reference-only
            if run_idx == 2:
                feature_kwargs.update(
                    run_day_count=2,
                    pre_ews_day_count=0,
                    ews_warning_day_count=0,
                    pre_alarm_day_count=0,
                    max_signal_count=1.1,
                    mean_signal_count=1.0,
                    cond_evt_day_ratio=0.15,
                    cond_evt_only_day_ratio=0.08,
                    ae_mid_or_hi_early_day_ratio=0.18,
                    p95_recon_error=0.02,
                    max_v_drop=0.16,
                    min_mid_ratio=0.83,
                    min_mid_v_ratio=0.82,
                )
                reference_score = 9.4

            # negative logistic-only
            if run_idx == 5:
                feature_kwargs.update(
                    run_day_count=4,
                    pre_ews_day_count=3,
                    ews_warning_day_count=1,
                    pre_alarm_day_count=1,
                    max_signal_count=3.1,
                    mean_signal_count=2.5,
                    cond_evt_day_ratio=0.86,
                    cond_evt_only_day_ratio=0.82,
                    ae_mid_or_hi_early_day_ratio=0.88,
                    p95_recon_error=0.08,
                    max_v_drop=0.69,
                    min_mid_ratio=0.44,
                    min_mid_v_ratio=0.42,
                )
                reference_score = 2.0

            # negative reference-only
            if run_idx == 6:
                feature_kwargs.update(
                    run_day_count=3,
                    pre_ews_day_count=0,
                    ews_warning_day_count=0,
                    pre_alarm_day_count=0,
                    max_signal_count=1.0,
                    mean_signal_count=1.0,
                    cond_evt_day_ratio=0.14,
                    cond_evt_only_day_ratio=0.06,
                    ae_mid_or_hi_early_day_ratio=0.15,
                    p95_recon_error=0.02,
                    max_v_drop=0.15,
                    min_mid_ratio=0.86,
                    min_mid_v_ratio=0.85,
                )
                reference_score = 9.3

            feature_rows.append(make_feature_row(site, panel_id, start, end, **feature_kwargs))
            label_rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "run_start_date": start,
                    "run_end_date": end,
                    "label_bucket_v3": label_bucket_v3,
                    "training_label_v3": training_label_v3,
                }
            )
            v0_rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "run_start_date": start,
                    "run_end_date": end,
                    "electrical_core_minus_broadshape_050": reference_score,
                }
            )

    write_csv(share_dir / "panel_day_engine_run_feature_table_v1.csv", feature_rows, FEATURE_COLS)
    write_csv(share_dir / "panel_day_engine_run_label_pack_v3_intersection.csv", label_rows, LABEL_PACK_V3_COLS)
    write_csv(share_dir / "panel_day_engine_run_ranker_v0_scores.csv", v0_rows, V0_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research" / "prognostics" / "build_panel_day_engine_run_ranker_complement_audit_v1.py"

    py_compile.compile(str(repo_root / "pv_ae" / "panel_day_engine.py"), doraise=True)
    py_compile.compile(str(builder), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="run-ranker-complement-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        result = run([sys.executable, str(builder), "--root", str(tmp_root)], cwd=repo_root)
        if result.returncode != 0:
            raise SystemExit(f"builder failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        fold_summary_path = tmp_root / "_share" / "panel_day_engine_run_ranker_complement_fold_summary_v1.csv"
        cases_path = tmp_root / "_share" / "panel_day_engine_run_ranker_complement_cases_v1.csv"
        recommendation_path = tmp_root / "_share" / "panel_day_engine_run_ranker_complement_recommendation_v1.csv"

        assert_true(fold_summary_path.exists(), "missing fold summary output")
        assert_true(cases_path.exists(), "missing case output")
        assert_true(recommendation_path.exists(), "missing recommendation output")

        fold_summary_df = pd.read_csv(fold_summary_path, encoding="utf-8-sig")
        cases_df = pd.read_csv(cases_path, encoding="utf-8-sig")
        recommendation_df = pd.read_csv(recommendation_path, encoding="utf-8-sig")

        assert_true(set(fold_summary_df["fold_type"].astype(str)) == {"leave_one_site_out", "time_holdout_70_30"}, "unexpected fold types")
        assert_true(len(fold_summary_df) == 3, "expected 3 fold rows")
        disagreement_classes = set(cases_df["disagreement_class"].astype(str))
        assert_true("positive_logistic_only" in disagreement_classes, "missing positive_logistic_only disagreements")
        assert_true("positive_reference_only" in disagreement_classes, "missing positive_reference_only disagreements")

        valid = fold_summary_df.loc[fold_summary_df["skip_reason"].fillna("").astype(str).eq("")]
        expected_increment = (
            valid["positive_logistic_only_count"].astype(float) - valid["negative_logistic_only_count"].astype(float)
        )
        assert_true(
            all(
                round(a, 8) == round(b, 8)
                for a, b in zip(valid["logistic_incremental_positive_minus_negative"].astype(float), expected_increment)
            ),
            "incremental positive-minus-negative should equal logistic-only positive minus logistic-only negative",
        )

        assert_true(len(recommendation_df) == 1, "recommendation output should contain exactly one row")
        direction = str(recommendation_df.iloc[0]["recommended_next_direction"])
        assert_true(
            direction in {"use_logistic_as_secondary_discovery_lane", "stop_learned_scorer_for_now"},
            f"unexpected recommendation: {direction}",
        )

        assert_true(not cases_df.empty, "case output should not be empty")

    print("smoke_test_panel_day_engine_run_ranker_complement_audit_v1.py: PASS")


if __name__ == "__main__":
    main()
