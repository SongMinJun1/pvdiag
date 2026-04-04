#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
CLIP_INPUT_COLS = [
    "core_vdrop_input",
    "core_midv_input",
    "core_mid_input",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
]

FEATURE_COLS = [
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
FATE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "delta_run_class",
    "evidence_reason_ko",
    "future_confirmed_fault_7d",
    "future_critical_fault_7d",
    "future_final_fault_7d",
    "future_confirmed_fault_30d",
    "future_critical_fault_30d",
    "future_final_fault_30d",
    "future_confirmed_fault_60d",
    "future_critical_fault_60d",
    "future_final_fault_60d",
    "future_truth_overlap_30d",
    "future_truth_overlap_60d",
    "future_truth_candidate_validities",
    "future_truth_case_ids",
    "recurring_run_within_30d",
    "recurring_run_within_60d",
    "future_run_count_60d",
    "fate_class",
    "fate_reason_ko",
]


def robust_scale(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    median = float(numeric.median())
    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    iqr = q3 - q1
    denom = iqr if abs(iqr) > 1e-9 else 1.0
    return ((numeric.fillna(median) - median) / denom).clip(-5.0, 5.0)


def compute_expected_clipped_scores(features: list[dict[str, object]]) -> pd.DataFrame:
    df = pd.DataFrame(features).copy()
    df["core_vdrop_input"] = df["max_v_drop"]
    df["core_midv_input"] = 1.0 - df["min_mid_v_ratio"]
    df["core_mid_input"] = 1.0 - df["min_mid_ratio"]
    for site, site_df in df.groupby("site", sort=True, dropna=False):
        for col in CLIP_INPUT_COLS:
            threshold = float(site_df[col].quantile(0.99))
            df.loc[df["site"].eq(site), f"{col}_clipped"] = df.loc[df["site"].eq(site), col].clip(upper=threshold)
    df["clipped_operator_score"] = (
        robust_scale(df["core_vdrop_input_clipped"])
        + robust_scale(df["core_midv_input_clipped"])
        + robust_scale(df["core_mid_input_clipped"])
        - 0.50
        * (
            robust_scale(df["ae_mid_or_hi_early_day_ratio_clipped"])
            + robust_scale(df["mean_signal_count_clipped"])
            + robust_scale(df["max_signal_count_clipped"])
            + robust_scale(df["p95_recon_error_clipped"])
        )
    )
    return df


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def load_build_module(repo_root: Path):
    module_path = repo_root / "research/prognostics/build_panel_day_engine_operator_run_consolidation_v1.py"
    spec = importlib.util.spec_from_file_location("operator_run_consolidation_build", module_path)
    module = importlib.util.module_from_spec(spec)
    assert_true(spec is not None and spec.loader is not None, "failed to load build module")
    spec.loader.exec_module(module)
    return module


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def feature_row(
    panel_id: str,
    start: str,
    end: str,
    run_day_count: int,
    score_seed: float,
    *,
    recurring: int = 0,
    future_fault: int = 0,
    future_truth: int = 0,
    fate_class: str = "",
    max_v_drop: float = 0.5,
    min_mid_v_ratio: float = 0.5,
    min_mid_ratio: float = 0.5,
    mean_signal_count: float = 1.5,
    max_signal_count: float = 2.0,
    p95_recon_error: float = 0.1,
    overlap_case_class: str = "unmatched_to_review",
) -> dict[str, object]:
    return {
        "site": "alpha",
        "panel_id": panel_id,
        "run_start_date": start,
        "run_end_date": end,
        "run_day_count": run_day_count,
        "run_shape_class": "chronic_alert_run" if run_day_count >= 10 else "short_alert_run",
        "overlap_case_class": overlap_case_class,
        "delta_run_class": "added_run",
        "fate_class": fate_class,
        "cohort_hint": "unmatched_other",
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
        "cond_evt_only_day_ratio": max(0.0, 1.0 - score_seed / 20.0),
        "cond_evt_same_day_early_corroborated_day_ratio": min(1.0, score_seed / 20.0),
        "ae_mid_or_hi_early_day_ratio": min(1.0, score_seed / 20.0),
        "dtw_mid_or_hi_early_day_ratio": 0.5,
        "hs_mid_or_hi_early_day_ratio": 0.3,
        "max_recon_error": 0.1,
        "p95_recon_error": p95_recon_error,
        "max_dtw_dist": 10.0,
        "p95_dtw_dist": 9.5,
        "max_hs_score": 0.4,
        "p95_hs_score": 0.35,
        "min_mid_ratio": min_mid_ratio,
        "min_mid_v_ratio": min_mid_v_ratio,
        "min_mid_i_ratio": 0.5,
        "max_v_drop": max_v_drop,
        "recurring_run_within_60d": recurring,
        "future_fault_linked_flag": future_fault,
        "future_truth_linked_flag": future_truth,
    }


def score_row(feature: dict[str, object], score: float) -> dict[str, object]:
    return {
        "site": feature["site"],
        "panel_id": feature["panel_id"],
        "run_start_date": feature["run_start_date"],
        "run_end_date": feature["run_end_date"],
        "run_day_count": feature["run_day_count"],
        "run_shape_class": feature["run_shape_class"],
        "cohort_hint": feature["cohort_hint"],
        "electrical_core_score": score + 1.0,
        "electrical_evt_score": score + 0.5,
        "electrical_evt_minus_broadshape_score": score,
        "electrical_core_minus_broadshape_025": score,
        "electrical_core_minus_broadshape_050": score,
        "electrical_core_minus_broadshape_075": score - 0.5,
        "electrical_core_plus_evtonly_minus_broadshape_025": score,
        "electrical_core_plus_evtonly_minus_broadshape_050": score - 0.2,
    }


def fate_row(feature: dict[str, object], fate_class: str) -> dict[str, object]:
    return {
        "site": feature["site"],
        "panel_id": feature["panel_id"],
        "run_start_date": feature["run_start_date"],
        "run_end_date": feature["run_end_date"],
        "run_day_count": feature["run_day_count"],
        "run_shape_class": feature["run_shape_class"],
        "delta_run_class": feature["delta_run_class"],
        "evidence_reason_ko": "",
        "future_confirmed_fault_7d": 0,
        "future_critical_fault_7d": 0,
        "future_final_fault_7d": 0,
        "future_confirmed_fault_30d": 0,
        "future_critical_fault_30d": 0,
        "future_final_fault_30d": 0,
        "future_confirmed_fault_60d": 0,
        "future_critical_fault_60d": 0,
        "future_final_fault_60d": 0,
        "future_truth_overlap_30d": 0,
        "future_truth_overlap_60d": 0,
        "future_truth_candidate_validities": "",
        "future_truth_case_ids": "",
        "recurring_run_within_30d": 0,
        "recurring_run_within_60d": feature["recurring_run_within_60d"],
        "future_run_count_60d": 0,
        "fate_class": fate_class,
        "fate_reason_ko": "",
    }


def build_fixture_root(tmp_root: Path) -> None:
    features = [
        feature_row("alpha.r01", "2025-01-09", "2025-01-10", 12, 20.0, future_fault=1, max_v_drop=0.70),
        feature_row("alpha.r02", "2025-01-08", "2025-01-08", 12, 19.0, max_v_drop=0.65),
        feature_row("alpha.r03", "2025-01-07", "2025-01-09", 10, 18.0, max_v_drop=0.60),
        feature_row(
            "alpha.r04",
            "2025-01-01",
            "2025-01-02",
            11,
            17.0,
            recurring=1,
            future_truth=1,
            min_mid_ratio=-25.0,
            min_mid_v_ratio=0.40,
            max_v_drop=0.45,
        ),
        feature_row("alpha.r05", "2025-01-03", "2025-01-05", 5, 16.0),
        feature_row(
            "alpha.r06",
            "2024-12-28",
            "2024-12-29",
            11,
            18.2,
            recurring=1,
            min_mid_ratio=0.20,
            min_mid_v_ratio=0.25,
            max_v_drop=0.62,
            mean_signal_count=1.1,
            max_signal_count=1.4,
            p95_recon_error=0.02,
            overlap_case_class="nuisance_overlap",
        ),
        feature_row(
            "alpha.r21",
            "2024-12-24",
            "2024-12-27",
            12,
            19.5,
            recurring=1,
            future_fault=1,
            max_v_drop=0.68,
            min_mid_v_ratio=0.32,
            min_mid_ratio=0.28,
            mean_signal_count=1.2,
            max_signal_count=1.6,
            p95_recon_error=0.03,
        ),
    ]
    for idx in range(7, 21):
        start = f"2024-12-{idx:02d}" if idx <= 9 else f"2024-11-{idx:02d}"
        end = start
        features.append(feature_row(f"alpha.r{idx:02d}", start, end, 2, 21.0 - idx))

    explicit_scores = {
        "alpha.r01": 20.0,
        "alpha.r02": 19.0,
        "alpha.r03": 15.0,
        "alpha.r04": 17.0,
        "alpha.r05": 16.0,
        "alpha.r06": 18.2,
        "alpha.r21": 19.5,
    }
    scores = [score_row(row, explicit_scores.get(row["panel_id"], 21.0 - idx)) for idx, row in enumerate(features, start=1)]
    fates = [fate_row(features[2], "future_fault_linked")]

    write_csv(tmp_root / "_share" / "panel_day_engine_run_feature_table_v1.csv", features, FEATURE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v0_scores.csv", scores, V0_SCORE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_local_seed_carry_fate_cases_v1.csv", fates, FATE_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="operator_run_consolidation_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        compile_result = run(
            [
                sys.executable,
                "-m",
                "py_compile",
                "research/prognostics/build_panel_day_engine_operator_run_consolidation_v1.py",
                "research/prognostics/smoke_test_panel_day_engine_operator_run_consolidation_v1.py",
            ],
            repo_root,
        )
        assert_true(compile_result.returncode == 0, compile_result.stderr)

        build_result = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_operator_run_consolidation_v1.py",
                "--root",
                str(tmp_root),
            ],
            repo_root,
        )
        assert_true(build_result.returncode == 0, build_result.stderr)

        share_dir = tmp_root / "_share"
        registry = pd.read_csv(share_dir / "panel_day_engine_operator_run_registry_v1.csv")
        queue = pd.read_csv(share_dir / "panel_day_engine_operator_run_queue_v1.csv")
        backlog = pd.read_csv(share_dir / "panel_day_engine_operator_run_backlog_v1.csv")
        watchlist = pd.read_csv(share_dir / "panel_day_engine_operator_run_watchlist_v1.csv")
        watchlist_now = pd.read_csv(share_dir / "panel_day_engine_operator_run_watchlist_now_v1.csv")
        watchlist_review = pd.read_csv(share_dir / "panel_day_engine_operator_run_watchlist_review_v1.csv")
        watchlist_now_panels = pd.read_csv(share_dir / "panel_day_engine_operator_run_watchlist_now_panels_v1.csv")
        watchlist_now_panels_summary = pd.read_csv(share_dir / "panel_day_engine_operator_run_watchlist_now_panels_summary_v1.csv")
        attention_now = pd.read_csv(share_dir / "panel_day_engine_operator_attention_now_v1.csv")
        attention_summary = pd.read_csv(share_dir / "panel_day_engine_operator_attention_summary_v1.csv")
        summary = pd.read_csv(share_dir / "panel_day_engine_operator_run_summary_v1.csv")
        watchlist_summary = pd.read_csv(share_dir / "panel_day_engine_operator_run_watchlist_summary_v1.csv")
        feature_input = pd.read_csv(share_dir / "panel_day_engine_run_feature_table_v1.csv")
        expected_clipped = compute_expected_clipped_scores(feature_input.to_dict("records"))
        build_module = load_build_module(repo_root)

        assert_true(len(registry) == 21, "registry should contain one row per run")
        assert_true(len(queue) == 3, "queue should include only investigate_now/monitor_active runs")
        assert_true(len(backlog) == 4, "backlog should include recurring/recovered runs only")
        assert_true(len(watchlist) == 2, "watchlist should contain only recurring chronic P1/P2 backlog runs")
        assert_true(len(watchlist_now) == 1, "watch_now should contain only P1 watchlist runs")
        assert_true(len(watchlist_review) == 1, "watch_review should contain only P2 watchlist runs")
        assert_true(len(watchlist_now_panels) == 1, "single watch_now panel should pass through unchanged")
        assert_true(len(attention_now) == 4, "attention_now should combine queue and watch_now_panel rows")

        required_registry_cols = {
            "raw_operator_score",
            "clipped_operator_score",
            "raw_rank_within_site",
            "clipped_rank_within_site",
            "rank_shift_abs",
            "score_hygiene_flag",
            "score_hygiene_reason_ko",
            "watchlist_flag",
            "watchlist_bucket",
            "watchlist_reason_ko",
            "watchlist_tier",
            "watch_now_flag",
            "watch_review_flag",
            "watchlist_tier_reason_ko",
        }
        assert_true(required_registry_cols.issubset(set(registry.columns)), "new registry fields should be present")
        assert_true(
            registry["raw_operator_score"].equals(registry["electrical_core_minus_broadshape_050"]),
            "raw operator score should preserve electrical_core_minus_broadshape_050",
        )

        merged_expected = registry.merge(
            expected_clipped.loc[:, [*KEY_COLS, "clipped_operator_score"]],
            on=KEY_COLS,
            how="left",
            suffixes=("", "_expected"),
            validate="one_to_one",
        )
        max_diff = (
            pd.to_numeric(merged_expected["clipped_operator_score"], errors="coerce")
            - pd.to_numeric(merged_expected["clipped_operator_score_expected"], errors="coerce")
        ).abs().max()
        assert_true(float(max_diff) < 1e-9, "transformed-input clipping should define clipped operator score")

        status_by_panel = dict(zip(registry["panel_id"], registry["status"]))
        assert_true(status_by_panel["alpha.r01"] == "ongoing_run", "alpha.r01 should be ongoing")
        assert_true(status_by_panel["alpha.r21"] == "recurring_run", "alpha.r21 should be recurring")
        assert_true(status_by_panel["alpha.r02"] == "new_run", "alpha.r02 should be new")
        assert_true(status_by_panel["alpha.r04"] == "recurring_run", "alpha.r04 should be recurring")
        assert_true(status_by_panel["alpha.r06"] == "recurring_run", "alpha.r06 should be recurring")
        assert_true(status_by_panel["alpha.r05"] == "recovered_run", "alpha.r05 should be recovered")
        assert_true(status_by_panel["alpha.r20"] == "historical_run", "alpha.r20 should be historical")

        band_by_panel = dict(zip(registry["panel_id"], registry["priority_band"]))
        assert_true(band_by_panel["alpha.r01"] == "P1", "top run should be P1")
        assert_true(band_by_panel["alpha.r21"] == "P1", "second-highest run should also be P1")
        assert_true(band_by_panel["alpha.r02"] == "P2", "alpha.r02 should be P2")
        assert_true(band_by_panel["alpha.r04"] == "P2", "recurring chronic watch run should be P2")
        assert_true(band_by_panel["alpha.r10"] == "P3", "mid-ranked run should be P3")
        assert_true(band_by_panel["alpha.r20"] == "P4", "lowest run should be P4")

        action_by_panel = dict(zip(registry["panel_id"], registry["action_bucket"]))
        assert_true(action_by_panel["alpha.r01"] == "investigate_now", "ongoing P1 should investigate_now")
        assert_true(action_by_panel["alpha.r21"] == "recurring_backlog", "recurring P1 should remain backlog")
        assert_true(action_by_panel["alpha.r02"] == "investigate_now", "new P2 should investigate_now")
        assert_true(action_by_panel["alpha.r03"] == "monitor_active", "new P3 medium should monitor_active")
        assert_true(action_by_panel["alpha.r04"] == "recurring_backlog", "recurring run should go to recurring_backlog")
        assert_true(action_by_panel["alpha.r06"] == "recurring_backlog", "nuisance recurring run should stay backlog")
        assert_true(action_by_panel["alpha.r05"] == "recovered_backlog", "recovered run should go to recovered_backlog")
        assert_true(action_by_panel["alpha.r20"] == "historical_archive", "historical P4 should archive")

        queued_panels = set(queue["panel_id"])
        backlog_panels = set(backlog["panel_id"])
        watchlist_panels = set(watchlist["panel_id"])
        assert_true("alpha.r01" in queued_panels, "ongoing P1 should be queued")
        assert_true("alpha.r02" in queued_panels, "new P2 should be queued")
        assert_true("alpha.r03" in queued_panels, "new P3 medium should be queued")
        assert_true("alpha.r21" not in queued_panels, "watchlist backlog run should not enter queue")
        assert_true("alpha.r04" not in queued_panels, "recurring backlog should not remain in queue")
        assert_true("alpha.r04" in backlog_panels, "P4 recurring run should move to backlog")
        assert_true("alpha.r21" in backlog_panels, "recurring P1 backlog run should remain in backlog")
        assert_true("alpha.r06" in backlog_panels, "second recurring run should remain in backlog")
        assert_true("alpha.r05" not in queued_panels, "recovered run should not remain in queue")
        assert_true("alpha.r05" in backlog_panels, "recovered run should go to backlog")
        assert_true("alpha.r20" not in queued_panels, "historical P4 run should be excluded from queue")
        assert_true("alpha.r20" not in backlog_panels, "historical archive should be excluded from backlog")
        assert_true("alpha.r21" in watchlist_panels, "recurring chronic P1 backlog run should go to watchlist")
        assert_true("alpha.r04" in watchlist_panels, "recurring chronic P2 backlog run should go to watchlist")
        assert_true("alpha.r06" not in watchlist_panels, "nuisance-overlap recurring chronic run should not go to watchlist")
        assert_true("alpha.r01" not in watchlist_panels, "queue run should not go to watchlist")

        registry_panels = set(registry["panel_id"])
        assert_true(queued_panels.issubset(registry_panels), "queue must be subset of registry")
        assert_true(backlog_panels.issubset(registry_panels), "backlog must be subset of registry")
        assert_true(watchlist_panels.issubset(backlog_panels), "watchlist must be subset of backlog")
        assert_true(watchlist_panels.isdisjoint(queued_panels), "watchlist must not overlap queue")

        fate_by_panel = dict(zip(registry["panel_id"], registry["fate_class"]))
        assert_true(fate_by_panel["alpha.r03"] == "future_fault_linked", "optional fate enrichment should fill fate_class")

        registry_shift = registry.set_index("panel_id")
        assert_true(
            int(registry_shift.loc["alpha.r04", "score_hygiene_flag"]) == 1,
            "extreme transformed-input run should be hygiene-flagged",
        )
        assert_true(
            int(registry["rank_shift_abs"].max()) >= 1,
            "at least one run should move under clipped ranking",
        )

        recurring_backlog_registry = registry.loc[registry["action_bucket"].eq("recurring_backlog")].copy()
        recurring_backlog_expected = recurring_backlog_registry.sort_values(
            ["clipped_operator_score", "run_day_count", "site", "panel_id", "run_start_date"],
            ascending=[False, False, True, True, True],
            kind="mergesort",
        )
        recurring_backlog_actual = backlog.loc[backlog["action_bucket"].eq("recurring_backlog")].copy()
        assert_true(
            recurring_backlog_actual["panel_id"].tolist() == recurring_backlog_expected["panel_id"].tolist(),
            "backlog ordering should use clipped operator score",
        )
        assert_true(
            recurring_backlog_actual["raw_operator_score"].ne(recurring_backlog_actual["clipped_operator_score"]).any(),
            "raw operator score should remain preserved beside clipped score",
        )

        watchlist_bucket_by_panel = dict(zip(registry["panel_id"], registry["watchlist_bucket"]))
        assert_true(watchlist_bucket_by_panel["alpha.r21"] == "recurring_watch_p1", "recurring chronic P1 should map to watchlist p1")
        assert_true(watchlist_bucket_by_panel["alpha.r04"] == "recurring_watch_p2", "recurring chronic P2 should map to watchlist p2")
        assert_true(watchlist_bucket_by_panel["alpha.r06"] == "none", "nuisance-overlap recurring chronic should be excluded from watchlist")

        watchlist_tier_by_panel = dict(zip(registry["panel_id"], registry["watchlist_tier"]))
        assert_true(watchlist_tier_by_panel["alpha.r21"] == "watch_now", "P1 watchlist run should go to watch_now")
        assert_true(watchlist_tier_by_panel["alpha.r04"] == "watch_review", "P2 watchlist run should go to watch_review")
        assert_true(watchlist_tier_by_panel["alpha.r06"] == "none", "non-watchlist run should stay out of tiers")

        watch_now_run_panels = set(watchlist_now["panel_id"])
        watch_review_panels = set(watchlist_review["panel_id"])
        assert_true(watch_now_run_panels == {"alpha.r21"}, "watch_now should contain only the P1 watchlist run")
        assert_true(watch_review_panels == {"alpha.r04"}, "watch_review should contain only the P2 watchlist run")
        assert_true(watch_now_run_panels.isdisjoint(watch_review_panels), "watch_now and watch_review should not overlap")
        assert_true(watch_now_run_panels | watch_review_panels == watchlist_panels, "watch_now/review should partition watchlist")
        assert_true(watch_now_run_panels.issubset(backlog_panels), "watch_now should stay inside backlog")
        assert_true(watch_review_panels.issubset(backlog_panels), "watch_review should stay inside backlog")
        assert_true(watch_now_run_panels.isdisjoint(queued_panels), "watch_now should not overlap queue")
        assert_true(watch_review_panels.isdisjoint(queued_panels), "watch_review should not overlap queue")

        watchlist_expected = registry.loc[registry["watchlist_flag"].eq(1)].copy().sort_values(
            ["watchlist_bucket", "clipped_operator_score", "run_day_count", "site", "panel_id", "run_start_date"],
            ascending=[True, False, False, True, True, True],
            kind="mergesort",
        )
        assert_true(
            watchlist["panel_id"].tolist() == watchlist_expected["panel_id"].tolist(),
            "watchlist ordering should follow clipped operator score inside bucket",
        )
        watchlist_now_expected = registry.loc[registry["watch_now_flag"].eq(1)].copy().sort_values(
            ["clipped_operator_score", "run_day_count", "site", "panel_id", "run_start_date"],
            ascending=[False, False, True, True, True],
            kind="mergesort",
        )
        watchlist_review_expected = registry.loc[registry["watch_review_flag"].eq(1)].copy().sort_values(
            ["clipped_operator_score", "run_day_count", "site", "panel_id", "run_start_date"],
            ascending=[False, False, True, True, True],
            kind="mergesort",
        )
        assert_true(
            watchlist_now["panel_id"].tolist() == watchlist_now_expected["panel_id"].tolist(),
            "watch_now ordering should follow clipped operator score",
        )
        assert_true(
            watchlist_review["panel_id"].tolist() == watchlist_review_expected["panel_id"].tolist(),
            "watch_review ordering should follow clipped operator score",
        )
        assert_true(
            watchlist_now_panels.iloc[0]["panel_id"] == "alpha.r21",
            "single watch_now panel should preserve the original panel",
        )
        assert_true(
            int(watchlist_now_panels.iloc[0]["watch_now_run_count_for_panel"]) == 1,
            "single watch_now panel should keep run count 1",
        )

        rollup_input = pd.DataFrame(
            [
                {
                    "site": "alpha",
                    "panel_id": "multi.panel",
                    "run_start_date": "2025-01-01",
                    "run_end_date": "2025-01-03",
                    "run_day_count": 3,
                    "run_shape_class": "chronic_alert_run",
                    "status": "recurring_run",
                    "priority_band": "P1",
                    "action_bucket": "recurring_backlog",
                    "overlap_case_class": "unmatched_to_review",
                    "raw_operator_score": 10.0,
                    "clipped_operator_score": 9.0,
                    "raw_rank_within_site": 10,
                    "clipped_rank_within_site": 9,
                    "score_hygiene_flag": 0,
                    "score_hygiene_reason_ko": "clipping 영향 적음",
                    "future_fault_linked_flag": 0,
                    "future_truth_linked_flag": 0,
                    "watchlist_bucket": "recurring_watch_p1",
                    "watchlist_tier": "watch_now",
                    "watchlist_reason_ko": "반복 chronic 상위 우선순위",
                    "watchlist_tier_reason_ko": "즉시 주시할 상위 반복 chronic",
                },
                {
                    "site": "alpha",
                    "panel_id": "multi.panel",
                    "run_start_date": "2025-01-02",
                    "run_end_date": "2025-01-05",
                    "run_day_count": 3,
                    "run_shape_class": "chronic_alert_run",
                    "status": "recurring_run",
                    "priority_band": "P1",
                    "action_bucket": "recurring_backlog",
                    "overlap_case_class": "eligible_local_overlap",
                    "raw_operator_score": 10.0,
                    "clipped_operator_score": 9.0,
                    "raw_rank_within_site": 11,
                    "clipped_rank_within_site": 10,
                    "score_hygiene_flag": 1,
                    "score_hygiene_reason_ko": "min_mid_ratio 영향 큼",
                    "future_fault_linked_flag": 0,
                    "future_truth_linked_flag": 1,
                    "watchlist_bucket": "recurring_watch_p1",
                    "watchlist_tier": "watch_now",
                    "watchlist_reason_ko": "반복 chronic 상위 우선순위",
                    "watchlist_tier_reason_ko": "즉시 주시할 상위 반복 chronic",
                },
                {
                    "site": "alpha",
                    "panel_id": "single.panel",
                    "run_start_date": "2025-01-07",
                    "run_end_date": "2025-01-08",
                    "run_day_count": 2,
                    "run_shape_class": "chronic_alert_run",
                    "status": "recurring_run",
                    "priority_band": "P1",
                    "action_bucket": "recurring_backlog",
                    "overlap_case_class": "unmatched_to_review",
                    "raw_operator_score": 8.0,
                    "clipped_operator_score": 8.0,
                    "raw_rank_within_site": 15,
                    "clipped_rank_within_site": 14,
                    "score_hygiene_flag": 0,
                    "score_hygiene_reason_ko": "clipping 영향 적음",
                    "future_fault_linked_flag": 1,
                    "future_truth_linked_flag": 0,
                    "watchlist_bucket": "recurring_watch_p1",
                    "watchlist_tier": "watch_now",
                    "watchlist_reason_ko": "반복 chronic 상위 우선순위",
                    "watchlist_tier_reason_ko": "즉시 주시할 상위 반복 chronic",
                },
            ]
        )
        rollup = build_module.build_watch_now_panel_rollup(rollup_input)
        rollup_summary = build_module.build_watch_now_panels_summary(rollup, rollup_input)
        assert_true(len(rollup) == 2, "multiple watch_now runs from one panel should collapse to one panel row")
        multi_panel = rollup.loc[rollup["panel_id"].eq("multi.panel")].iloc[0]
        single_panel = rollup.loc[rollup["panel_id"].eq("single.panel")].iloc[0]
        assert_true(
            multi_panel["representative_run_end_date"] == "2025-01-05",
            "representative selection should prefer later run_end_date after score tie",
        )
        assert_true(
            int(multi_panel["watch_now_run_count_for_panel"]) == 2,
            "collapsed panel should report the number of watch_now runs",
        )
        assert_true(
            multi_panel["overlap_case_class_set"] == "eligible_local_overlap|unmatched_to_review",
            "rollup should retain overlap case class set",
        )
        assert_true(
            multi_panel["panel_rollup_reason_ko"] == "future linkage reference 있음",
            "future linkage should be surfaced as rollup reason when present",
        )
        assert_true(
            single_panel["representative_run_start_date"] == "2025-01-07",
            "single-run panel should pass through unchanged",
        )
        assert_true(
            int(single_panel["watch_now_run_count_for_panel"]) == 1,
            "single-run panel should keep run count 1",
        )
        rollup_overall = rollup_summary.loc[rollup_summary["record_type"].eq("overall")].iloc[0]
        assert_true(int(rollup_overall["watch_now_panel_count"]) == 2, "panel summary should count collapsed panels")
        assert_true(int(rollup_overall["watch_now_run_count"]) == 3, "panel summary should preserve source run count")
        assert_true(
            int(rollup_overall["panels_with_multiple_watch_now_runs"]) == 1,
            "panel summary should count multi-run watch_now panels",
        )
        assert_true(
            float(rollup_overall["median_watch_now_runs_per_panel"]) == 1.5,
            "panel summary should compute median runs per panel",
        )

        attention_overall = attention_summary.loc[attention_summary["record_type"].eq("overall")].iloc[0]
        assert_true(int(attention_overall["attention_count"]) == 4, "attention summary count mismatch")
        assert_true(int(attention_overall["queue_run_attention_count"]) == 3, "attention summary queue count mismatch")
        assert_true(
            int(attention_overall["watch_now_panel_attention_count"]) == 1,
            "attention summary watch_now panel count mismatch",
        )
        assert_true(int(attention_overall["deduped_panel_overlap_count"]) == 0, "attention overlap should be zero in fixture")
        assert_true(
            int(attention_overall["deduped_overlap_future_fault_linked_ref_count"]) == 0,
            "fixture should have no deduped fault reference overlaps",
        )
        assert_true(
            int(attention_overall["deduped_overlap_future_truth_linked_ref_count"]) == 0,
            "fixture should have no deduped truth reference overlaps",
        )
        assert_true(
            int(attention_overall["attention_future_fault_linked_ref_count"]) == 2,
            "attention future fault reference count mismatch",
        )
        assert_true(
            int(attention_overall["attention_future_truth_linked_ref_count"]) == 0,
            "attention future truth reference count mismatch",
        )
        assert_true(
            int(attention_overall["attention_any_future_fault_linked_ref_count"]) == 2,
            "attention combined future fault reference count mismatch",
        )
        assert_true(
            int(attention_overall["attention_any_future_truth_linked_ref_count"]) == 0,
            "attention combined future truth reference count mismatch",
        )

        assert_true(
            attention_now["attention_class"].tolist() == ["queue_run", "queue_run", "queue_run", "watch_now_panel"],
            "attention classes should be assigned and queue should sort ahead of watch panels",
        )
        assert_true(
            attention_now["panel_id"].tolist() == ["alpha.r01", "alpha.r02", "alpha.r03", "alpha.r21"],
            "attention ordering should combine queue first, then watch_now panel",
        )
        assert_true(
            attention_now.iloc[0]["display_status_or_tier"] == "ongoing_run",
            "queue attention rows should use status as display_status_or_tier",
        )
        assert_true(
            attention_now.iloc[-1]["display_status_or_tier"] == "watch_now",
            "watch_now panel rows should use watchlist tier as display_status_or_tier",
        )
        assert_true(
            attention_now.iloc[-1]["attention_reason_ko"] == "반복 chronic 대표 panel 주시",
            "watch_now panel rows should carry watch attention reason",
        )
        assert_true(
            attention_now.loc[attention_now["attention_class"].eq("queue_run"), "panel_has_watch_now_overlap_flag"].eq(0).all(),
            "queue rows without watch overlap should keep panel overlap flag at 0",
        )
        assert_true(
            attention_now.loc[attention_now["attention_class"].eq("queue_run"), "attention_merge_reason_ko"].eq("queue 단독").all(),
            "queue-only rows should carry queue-only merge reason",
        )
        assert_true(
            attention_now.loc[attention_now["attention_class"].eq("watch_now_panel"), "panel_has_watch_now_overlap_flag"].eq(1).all(),
            "watch_now panel rows should carry panel overlap flag",
        )
        assert_true(
            attention_now.loc[attention_now["attention_class"].eq("watch_now_panel"), "attention_merge_reason_ko"].eq("watch panel 단독").all(),
            "watch_now panel rows should carry watch-only merge reason",
        )
        assert_true(
            int(
                attention_now.loc[attention_now["panel_id"].eq("alpha.r21"), "attention_any_future_fault_linked_ref_flag"].iloc[0]
            )
            == 1,
            "watch_now panel with direct future fault reference should set combined future fault flag",
        )
        assert_true(
            int(
                attention_now.loc[attention_now["panel_id"].eq("alpha.r21"), "attention_any_future_truth_linked_ref_flag"].iloc[0]
            )
            == 0,
            "watch_now panel without truth reference should keep combined future truth flag at 0",
        )

        attention_queue_input = pd.DataFrame(
            [
                {
                    "site": "alpha",
                    "panel_id": "queue.p1",
                    "run_start_date": "2025-01-10",
                    "run_end_date": "2025-01-12",
                    "run_day_count": 3,
                    "run_shape_class": "medium_alert_run",
                    "status": "ongoing_run",
                    "priority_band": "P1",
                    "clipped_operator_score": 7.0,
                    "raw_operator_score": 7.0,
                    "overlap_case_class": "unmatched_to_review",
                    "action_bucket": "investigate_now",
                    "watchlist_bucket": "none",
                    "score_hygiene_flag": 0,
                    "score_hygiene_reason_ko": "clipping 영향 적음",
                    "future_fault_linked_flag": 0,
                    "future_truth_linked_flag": 0,
                },
                {
                    "site": "alpha",
                    "panel_id": "shared.panel",
                    "run_start_date": "2025-01-08",
                    "run_end_date": "2025-01-09",
                    "run_day_count": 2,
                    "run_shape_class": "short_alert_run",
                    "status": "new_run",
                    "priority_band": "P2",
                    "clipped_operator_score": 5.0,
                    "raw_operator_score": 5.0,
                    "overlap_case_class": "unmatched_to_review",
                    "action_bucket": "investigate_now",
                    "watchlist_bucket": "none",
                    "score_hygiene_flag": 0,
                    "score_hygiene_reason_ko": "clipping 영향 적음",
                    "future_fault_linked_flag": 1,
                    "future_truth_linked_flag": 0,
                },
            ]
        )
        attention_watch_input = pd.DataFrame(
            [
                {
                    "site": "alpha",
                    "panel_id": "shared.panel",
                    "representative_run_start_date": "2025-01-01",
                    "representative_run_end_date": "2025-01-05",
                    "representative_run_day_count": 5,
                    "representative_run_shape_class": "chronic_alert_run",
                    "representative_status": "recurring_run",
                    "representative_priority_band": "P1",
                    "representative_action_bucket": "recurring_backlog",
                    "representative_overlap_case_class": "eligible_local_overlap",
                    "representative_raw_operator_score": 9.0,
                    "representative_clipped_operator_score": 9.0,
                    "representative_raw_rank_within_site": 1,
                    "representative_clipped_rank_within_site": 1,
                    "representative_score_hygiene_flag": 1,
                    "representative_score_hygiene_reason_ko": "max_v_drop 영향 큼",
                    "watch_now_run_count_for_panel": 3,
                    "watch_now_total_day_count_for_panel": 15,
                    "earliest_watch_now_run_start_date": "2025-01-01",
                    "latest_watch_now_run_end_date": "2025-01-05",
                    "max_clipped_operator_score_for_panel": 9.0,
                    "any_future_fault_linked_flag_ref": 1,
                    "any_future_truth_linked_flag_ref": 1,
                    "overlap_case_class_set": "eligible_local_overlap",
                    "panel_rollup_reason_ko": "future linkage reference 있음",
                },
                {
                    "site": "alpha",
                    "panel_id": "watch.only",
                    "representative_run_start_date": "2025-01-03",
                    "representative_run_end_date": "2025-01-07",
                    "representative_run_day_count": 5,
                    "representative_run_shape_class": "chronic_alert_run",
                    "representative_status": "recurring_run",
                    "representative_priority_band": "P1",
                    "representative_action_bucket": "recurring_backlog",
                    "representative_overlap_case_class": "unmatched_to_review",
                    "representative_raw_operator_score": 8.0,
                    "representative_clipped_operator_score": 8.0,
                    "representative_raw_rank_within_site": 2,
                    "representative_clipped_rank_within_site": 2,
                    "representative_score_hygiene_flag": 0,
                    "representative_score_hygiene_reason_ko": "clipping 영향 적음",
                    "watch_now_run_count_for_panel": 2,
                    "watch_now_total_day_count_for_panel": 9,
                    "earliest_watch_now_run_start_date": "2025-01-03",
                    "latest_watch_now_run_end_date": "2025-01-07",
                    "max_clipped_operator_score_for_panel": 8.0,
                    "any_future_fault_linked_flag_ref": 0,
                    "any_future_truth_linked_flag_ref": 1,
                    "overlap_case_class_set": "unmatched_to_review",
                    "panel_rollup_reason_ko": "반복 run 다수, 대표 run만 표시",
                },
            ]
        )
        attention_test = build_module.build_attention_now(attention_queue_input, attention_watch_input)
        attention_test_summary = build_module.build_attention_summary(
            attention_test,
            attention_queue_input,
            attention_watch_input,
        )
        assert_true(len(attention_test) == 3, "deduped attention should keep queue row over overlapping watch panel")
        assert_true(
            attention_test["panel_id"].tolist() == ["queue.p1", "shared.panel", "watch.only"],
            "attention ordering should be queue rows first, then remaining watch panel rows",
        )
        assert_true(
            attention_test["attention_class"].tolist() == ["queue_run", "queue_run", "watch_now_panel"],
            "attention_class should identify queue vs watch panel rows",
        )
        assert_true(
            attention_test.loc[attention_test["panel_id"].eq("shared.panel"), "display_status_or_tier"].iloc[0] == "new_run",
            "overlapping panel should keep the queue row in attention output",
        )
        shared_panel_row = attention_test.loc[attention_test["panel_id"].eq("shared.panel")].iloc[0]
        queue_only_row = attention_test.loc[attention_test["panel_id"].eq("queue.p1")].iloc[0]
        assert_true(
            int(shared_panel_row["panel_has_watch_now_overlap_flag"]) == 1,
            "queue row should inherit watch_now panel overlap flag when deduped",
        )
        assert_true(
            int(shared_panel_row["panel_watch_now_run_count"]) == 3,
            "queue row should inherit watch_now run count from panel rollup",
        )
        assert_true(
            int(shared_panel_row["panel_watch_now_total_day_count"]) == 15,
            "queue row should inherit watch_now total day count from panel rollup",
        )
        assert_true(
            shared_panel_row["panel_watch_now_earliest_start_date"] == "2025-01-01",
            "queue row should inherit panel earliest start date",
        )
        assert_true(
            shared_panel_row["panel_watch_now_latest_end_date"] == "2025-01-05",
            "queue row should inherit panel latest end date",
        )
        assert_true(
            int(shared_panel_row["panel_any_future_fault_linked_ref"]) == 1,
            "queue row should inherit panel future fault reference",
        )
        assert_true(
            int(shared_panel_row["panel_any_future_truth_linked_ref"]) == 1,
            "queue row should inherit panel future truth reference",
        )
        assert_true(
            shared_panel_row["panel_overlap_case_class_set"] == "eligible_local_overlap",
            "queue row should inherit panel overlap case class set",
        )
        assert_true(
            shared_panel_row["panel_rollup_reason_ko"] == "future linkage reference 있음",
            "queue row should inherit panel rollup reason",
        )
        assert_true(
            shared_panel_row["attention_merge_reason_ko"] == "queue 우선, panel reference 병합",
            "deduped queue row should record panel metadata merge reason",
        )
        assert_true(
            int(shared_panel_row["attention_any_future_fault_linked_ref_flag"]) == 1,
            "queue row inheriting panel future fault reference should set combined future fault flag",
        )
        assert_true(
            int(shared_panel_row["attention_any_future_truth_linked_ref_flag"]) == 1,
            "queue row inheriting panel future truth reference should set combined future truth flag",
        )
        assert_true(
            int(queue_only_row["panel_has_watch_now_overlap_flag"]) == 0,
            "queue row without overlap should keep panel overlap flag at 0",
        )
        assert_true(
            queue_only_row["attention_merge_reason_ko"] == "queue 단독",
            "queue row without overlap should remain queue-only",
        )
        assert_true(
            int(queue_only_row["attention_any_future_fault_linked_ref_flag"]) == 0,
            "queue-only row without direct or panel fault reference should keep combined future fault flag at 0",
        )
        attention_test_overall = attention_test_summary.loc[attention_test_summary["record_type"].eq("overall")].iloc[0]
        assert_true(
            int(attention_test_overall["deduped_panel_overlap_count"]) == 1,
            "attention summary should count deduped queue/watch overlap",
        )
        assert_true(
            int(attention_test_overall["watch_now_panel_attention_count"]) == 1,
            "only non-overlapping watch panel should remain after dedup",
        )
        assert_true(
            int(attention_test_overall["deduped_overlap_future_fault_linked_ref_count"]) == 1,
            "attention summary should count deduped fault reference overlaps",
        )
        assert_true(
            int(attention_test_overall["deduped_overlap_future_truth_linked_ref_count"]) == 1,
            "attention summary should count deduped truth reference overlaps",
        )
        assert_true(
            int(attention_test_overall["attention_any_future_fault_linked_ref_count"]) == 1,
            "attention summary should count combined future fault references",
        )
        assert_true(
            int(attention_test_overall["attention_any_future_truth_linked_ref_count"]) == 2,
            "attention summary should count combined future truth references",
        )

        overall = summary.loc[summary["record_type"] == "overall"].iloc[0]
        assert_true(int(overall["investigate_now_count"]) == 2, "investigate_now count mismatch")
        assert_true(int(overall["monitor_active_count"]) == 1, "monitor_active count mismatch")
        assert_true(int(overall["recurring_backlog_count"]) == 3, "recurring_backlog count mismatch")
        assert_true(int(overall["recovered_backlog_count"]) == 1, "recovered_backlog count mismatch")
        assert_true(int(overall["historical_archive_count"]) == 14, "historical_archive count mismatch")
        assert_true(int(overall["queue_count"]) == 3, "overall queue count mismatch")
        assert_true(int(overall["backlog_count"]) == 4, "overall backlog count mismatch")
        assert_true(int(overall["p1_run_count"]) == 2, "overall P1 count mismatch")
        assert_true(int(overall["p2_run_count"]) == 3, "overall P2 count mismatch")
        assert_true(int(overall["queue_chronic_count"]) == 3, "queue chronic count mismatch")
        assert_true(int(overall["backlog_chronic_count"]) == 3, "backlog chronic count mismatch")
        assert_true(pd.notna(overall["clipped_top20_overlap_vs_raw"]), "summary should include overlap metrics")
        assert_true(int(overall["score_hygiene_flag_count"]) >= 1, "summary should include hygiene counts")
        assert_true(int(overall["watchlist_count"]) == 2, "summary should include overall watchlist count")
        assert_true(int(overall["watchlist_p1_count"]) == 1, "summary should include watchlist p1 count")
        assert_true(int(overall["watchlist_p2_count"]) == 1, "summary should include watchlist p2 count")
        assert_true(int(overall["watchlist_chronic_count"]) == 2, "summary should include watchlist chronic count")
        assert_true(int(overall["watch_now_count"]) == 1, "summary should include watch_now count")
        assert_true(int(overall["watch_review_count"]) == 1, "summary should include watch_review count")

        overall_watchlist = watchlist_summary.loc[watchlist_summary["record_type"] == "overall"].iloc[0]
        assert_true(int(overall_watchlist["watchlist_count"]) == 2, "watchlist summary count mismatch")
        assert_true(int(overall_watchlist["watchlist_p1_count"]) == 1, "watchlist summary p1 mismatch")
        assert_true(int(overall_watchlist["watchlist_p2_count"]) == 1, "watchlist summary p2 mismatch")
        assert_true(int(overall_watchlist["watch_now_count"]) == 1, "watchlist summary watch_now mismatch")
        assert_true(int(overall_watchlist["watch_review_count"]) == 1, "watchlist summary watch_review mismatch")
        assert_true(int(overall_watchlist["watch_now_panel_count"]) == 1, "watchlist summary watch_now_panel_count mismatch")
        assert_true(
            int(overall_watchlist["panels_with_multiple_watch_now_runs"]) == 0,
            "watchlist summary multi-panel count mismatch",
        )
        assert_true(
            float(overall_watchlist["median_watch_now_runs_per_panel"]) == 1.0,
            "watchlist summary median watch_now runs mismatch",
        )
        assert_true(int(overall_watchlist["watchlist_chronic_count"]) == 2, "watchlist summary chronic mismatch")
        assert_true(
            int(overall_watchlist["watchlist_unmatched_to_review_count"]) == 2,
            "watchlist unmatched_to_review count mismatch",
        )
        assert_true(
            int(overall_watchlist["watchlist_nuisance_overlap_count"]) == 0,
            "nuisance-overlap run should be excluded from watchlist",
        )
        assert_true(
            int(overall_watchlist["watchlist_future_fault_linked_count"]) == 1,
            "future fault reference count mismatch",
        )
        assert_true(
            int(overall_watchlist["watchlist_future_truth_linked_count"]) == 1,
            "future truth reference count mismatch",
        )
        assert_true(
            int(overall_watchlist["watch_now_future_fault_linked_count"]) == 1,
            "watch_now future fault reference count mismatch",
        )
        assert_true(
            int(overall_watchlist["watch_now_future_truth_linked_count"]) == 0,
            "watch_now future truth reference count mismatch",
        )
        assert_true(
            int(overall_watchlist["watch_review_future_fault_linked_count"]) == 0,
            "watch_review future fault reference count mismatch",
        )
        assert_true(
            int(overall_watchlist["watch_review_future_truth_linked_count"]) == 1,
            "watch_review future truth reference count mismatch",
        )

        overall_watch_now_panels = watchlist_now_panels_summary.loc[
            watchlist_now_panels_summary["record_type"] == "overall"
        ].iloc[0]
        assert_true(int(overall_watch_now_panels["watch_now_panel_count"]) == 1, "watch_now panel summary count mismatch")
        assert_true(int(overall_watch_now_panels["watch_now_run_count"]) == 1, "watch_now panel summary run count mismatch")
        assert_true(
            int(overall_watch_now_panels["panels_with_multiple_watch_now_runs"]) == 0,
            "watch_now panel summary multi-run count mismatch",
        )
        assert_true(
            float(overall_watch_now_panels["median_watch_now_runs_per_panel"]) == 1.0,
            "watch_now panel summary median mismatch",
        )


if __name__ == "__main__":
    main()
