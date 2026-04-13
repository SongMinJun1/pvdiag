#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

CANDIDATE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "label_bucket_v2",
    "candidate_class",
    "candidate_priority_band",
    "site_positive_gap_flag",
    "site_negative_gap_flag",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
    "global_score_rank",
    "site_score_rank",
    "watch_now_panel_ref_flag",
    "watch_review_run_ref_flag",
    "common_cause_descriptive_ref_flag",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "expansion_reason_ko",
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
V0_COLS = [
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
WATCH_NOW_COLS = ["site", "panel_id", "any_future_fault_linked_flag_ref", "any_future_truth_linked_flag_ref"]
WATCH_REVIEW_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "future_fault_linked_flag", "future_truth_linked_flag"]
FATE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
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
]
REAUDIT_COLS = ["site", "panel_id", "strict_trigger_date", "candidate_validity", "review_priority"]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def candidate_row(
    site: str,
    panel_id: str,
    start: str,
    end: str,
    *,
    run_day_count: int,
    run_shape_class: str,
    label_bucket_v2: str,
    candidate_class: str,
    candidate_priority_band: str,
    site_positive_gap_flag: int,
    site_negative_gap_flag: int,
    score: float,
    global_rank: int,
    site_rank: int,
    watch_now_flag: int = 0,
    watch_review_flag: int = 0,
    common_flag: int = 0,
) -> dict[str, object]:
    return {
        "site": site,
        "panel_id": panel_id,
        "run_start_date": start,
        "run_end_date": end,
        "run_day_count": run_day_count,
        "run_shape_class": run_shape_class,
        "label_bucket_v2": label_bucket_v2,
        "candidate_class": candidate_class,
        "candidate_priority_band": candidate_priority_band,
        "site_positive_gap_flag": site_positive_gap_flag,
        "site_negative_gap_flag": site_negative_gap_flag,
        "electrical_core_score": score - 0.2,
        "electrical_core_minus_broadshape_050": score,
        "global_score_rank": global_rank,
        "site_score_rank": site_rank,
        "watch_now_panel_ref_flag": watch_now_flag,
        "watch_review_run_ref_flag": watch_review_flag,
        "common_cause_descriptive_ref_flag": common_flag,
        "max_v_drop": score / 10.0,
        "min_mid_v_ratio": 1.0 - score / 20.0,
        "min_mid_ratio": 1.0 - score / 30.0,
        "cond_evt_only_day_ratio": 0.5,
        "ae_mid_or_hi_early_day_ratio": 0.4,
        "mean_signal_count": 2.0,
        "max_signal_count": 3.0,
        "p95_recon_error": 0.2,
        "expansion_reason_ko": "synthetic candidate",
    }


def feature_from_candidate(row: dict[str, object]) -> dict[str, object]:
    return {
        "site": row["site"],
        "panel_id": row["panel_id"],
        "run_start_date": row["run_start_date"],
        "run_end_date": row["run_end_date"],
        "run_day_count": row["run_day_count"],
        "run_shape_class": row["run_shape_class"],
        "overlap_case_class": "unmatched_to_review",
        "delta_run_class": "added_run",
        "fate_class": "",
        "cohort_hint": "synthetic_only",
        "pre_ews_day_count": row["run_day_count"],
        "ews_warning_day_count": row["run_day_count"],
        "pre_alarm_day_count": row["run_day_count"],
        "prefault_B_day_count": 0,
        "pre_ews_run_count": 1,
        "ews_warning_run_count": 1,
        "pre_alarm_run_count": 1,
        "prefault_B_run_count": 0,
        "pre_alarm_max_run": row["run_day_count"],
        "max_signal_count": row["max_signal_count"],
        "mean_signal_count": row["mean_signal_count"],
        "any_data_bad": 0,
        "data_bad_day_ratio": 0.0,
        "cond_evt_day_ratio": 1.0,
        "cond_evt_only_day_ratio": row["cond_evt_only_day_ratio"],
        "cond_evt_same_day_early_corroborated_day_ratio": 0.5,
        "ae_mid_or_hi_early_day_ratio": row["ae_mid_or_hi_early_day_ratio"],
        "dtw_mid_or_hi_early_day_ratio": 0.4,
        "hs_mid_or_hi_early_day_ratio": 0.3,
        "max_recon_error": row["p95_recon_error"],
        "p95_recon_error": row["p95_recon_error"],
        "max_dtw_dist": 10.0,
        "p95_dtw_dist": 9.0,
        "max_hs_score": row["ae_mid_or_hi_early_day_ratio"],
        "p95_hs_score": row["ae_mid_or_hi_early_day_ratio"],
        "min_mid_ratio": row["min_mid_ratio"],
        "min_mid_v_ratio": row["min_mid_v_ratio"],
        "min_mid_i_ratio": row["min_mid_ratio"],
        "max_v_drop": row["max_v_drop"],
        "recurring_run_within_60d": 0,
        "future_fault_linked_flag": 0,
        "future_truth_linked_flag": 0,
    }


def v0_from_candidate(row: dict[str, object]) -> dict[str, object]:
    return {
        "site": row["site"],
        "panel_id": row["panel_id"],
        "run_start_date": row["run_start_date"],
        "run_end_date": row["run_end_date"],
        "run_day_count": row["run_day_count"],
        "run_shape_class": row["run_shape_class"],
        "cohort_hint": "synthetic_only",
        "electrical_core_score": row["electrical_core_score"],
        "electrical_evt_score": row["electrical_core_score"],
        "electrical_evt_minus_broadshape_score": row["electrical_core_minus_broadshape_050"] + 0.1,
        "electrical_core_minus_broadshape_025": row["electrical_core_minus_broadshape_050"] + 0.1,
        "electrical_core_minus_broadshape_050": row["electrical_core_minus_broadshape_050"],
        "electrical_core_minus_broadshape_075": row["electrical_core_minus_broadshape_050"] - 0.1,
        "electrical_core_plus_evtonly_minus_broadshape_025": row["electrical_core_minus_broadshape_050"] + 0.1,
        "electrical_core_plus_evtonly_minus_broadshape_050": row["electrical_core_minus_broadshape_050"],
    }


def build_fixture_root(tmp_root: Path) -> None:
    candidates: list[dict[str, object]] = []
    global_rank = 1

    candidates.append(candidate_row("alpha", "alpha.p1.1", "2025-01-01", "2025-01-03", run_day_count=3, run_shape_class="medium_alert_run", label_bucket_v2="unlabeled_other", candidate_class="positive_review_candidate", candidate_priority_band="P1", site_positive_gap_flag=1, site_negative_gap_flag=0, score=9.9, global_rank=global_rank, site_rank=1, watch_now_flag=1)); global_rank += 1
    candidates.append(candidate_row("beta", "beta.p1.1", "2025-01-02", "2025-01-04", run_day_count=3, run_shape_class="medium_alert_run", label_bucket_v2="unlabeled_other", candidate_class="positive_review_candidate", candidate_priority_band="P1", site_positive_gap_flag=1, site_negative_gap_flag=0, score=9.8, global_rank=global_rank, site_rank=1)); global_rank += 1

    for idx in range(1, 17):
        candidates.append(
            candidate_row(
                "alpha",
                f"alpha.p2.{idx}",
                f"2025-02-{idx:02d}",
                f"2025-02-{idx:02d}",
                run_day_count=4,
                run_shape_class="medium_alert_run",
                label_bucket_v2="unlabeled_other",
                candidate_class="positive_review_candidate",
                candidate_priority_band="P2",
                site_positive_gap_flag=0,
                site_negative_gap_flag=0,
                score=9.0 - idx * 0.1,
                global_rank=global_rank,
                site_rank=idx,
                watch_review_flag=1 if idx == 6 else 0,
            )
        )
        global_rank += 1
    for idx in range(1, 17):
        candidates.append(
            candidate_row(
                "beta",
                f"beta.p2.{idx}",
                f"2025-03-{idx:02d}",
                f"2025-03-{idx:02d}",
                run_day_count=5,
                run_shape_class="chronic_alert_run",
                label_bucket_v2="unlabeled_other",
                candidate_class="positive_review_candidate",
                candidate_priority_band="P2",
                site_positive_gap_flag=0,
                site_negative_gap_flag=0,
                score=7.9 - idx * 0.1,
                global_rank=global_rank,
                site_rank=idx,
            )
        )
        global_rank += 1

    for idx in range(1, 13):
        candidates.append(
            candidate_row(
                "gamma",
                f"gamma.mon.{idx}",
                f"2025-04-{idx:02d}",
                f"2025-04-{idx:02d}",
                run_day_count=6,
                run_shape_class="chronic_alert_run",
                label_bucket_v2="monitor_like",
                candidate_class="monitor_review_candidate",
                candidate_priority_band="P3",
                site_positive_gap_flag=0,
                site_negative_gap_flag=0,
                score=6.0 - idx * 0.1,
                global_rank=global_rank,
                site_rank=idx,
            )
        )
        global_rank += 1

    candidates.append(candidate_row("delta", "delta.cc.1", "2025-05-10", "2025-05-12", run_day_count=3, run_shape_class="medium_alert_run", label_bucket_v2="common_cause_like", candidate_class="common_cause_review_candidate", candidate_priority_band="P3", site_positive_gap_flag=0, site_negative_gap_flag=0, score=5.5, global_rank=global_rank, site_rank=1, common_flag=1)); global_rank += 1
    candidates.append(candidate_row("delta", "delta.cc.2", "2025-05-14", "2025-05-15", run_day_count=2, run_shape_class="medium_alert_run", label_bucket_v2="common_cause_like", candidate_class="common_cause_review_candidate", candidate_priority_band="P3", site_positive_gap_flag=0, site_negative_gap_flag=0, score=5.2, global_rank=global_rank, site_rank=2, common_flag=1)); global_rank += 1

    features = [feature_from_candidate(row) for row in candidates]
    scores = [v0_from_candidate(row) for row in candidates]
    watch_now = [{"site": "alpha", "panel_id": "alpha.p1.1", "any_future_fault_linked_flag_ref": 1, "any_future_truth_linked_flag_ref": 0}]
    watch_review = [{"site": "alpha", "panel_id": "alpha.p2.6", "run_start_date": "2025-02-06", "run_end_date": "2025-02-06", "future_fault_linked_flag": 0, "future_truth_linked_flag": 1}]
    fate = [{
        "site": "beta",
        "panel_id": "beta.p2.1",
        "run_start_date": "2025-03-01",
        "run_end_date": "2025-03-01",
        "future_confirmed_fault_7d": 0,
        "future_critical_fault_7d": 0,
        "future_final_fault_7d": 0,
        "future_confirmed_fault_30d": 0,
        "future_critical_fault_30d": 0,
        "future_final_fault_30d": 0,
        "future_confirmed_fault_60d": 0,
        "future_critical_fault_60d": 0,
        "future_final_fault_60d": 0,
        "future_truth_overlap_30d": 1,
        "future_truth_overlap_60d": 1,
        "future_truth_candidate_validities": "needs_more_info",
        "future_truth_case_ids": "beta|beta.p2.1|2025-03-05",
    }]
    reaudit = [
        {"site": "delta", "panel_id": "delta.cc.1", "strict_trigger_date": "2025-05-08", "candidate_validity": "group_side", "review_priority": "P1"},
        {"site": "delta", "panel_id": "delta.cc.2", "strict_trigger_date": "2025-05-11", "candidate_validity": "group_side", "review_priority": "P1"},
    ]

    write_csv(tmp_root / "_share" / "panel_day_engine_run_label_expansion_candidates_v1.csv", candidates, CANDIDATE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_feature_table_v1.csv", features, FEATURE_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_run_ranker_v0_scores.csv", scores, V0_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_operator_run_watchlist_now_panels_v1.csv", watch_now, WATCH_NOW_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_operator_run_watchlist_review_v1.csv", watch_review, WATCH_REVIEW_COLS)
    write_csv(tmp_root / "_share" / "panel_day_engine_local_seed_carry_fate_cases_v1.csv", fate, FATE_COLS)
    write_csv(tmp_root / "_share" / "panel_date_reaudit_working.csv", reaudit, REAUDIT_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_run_label_expansion_review_batch_v1.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_run_label_expansion_review_batch_v1.csv",
        repo_root / "_share" / "panel_day_engine_run_label_expansion_review_batch_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_run_label_expansion_review_evidence_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "pv_ae/panel_day_engine.py",
            "research/prognostics/build_panel_day_engine_run_label_expansion_review_batch_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_run_label_expansion_review_batch_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="run_label_expansion_batch_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        batch = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_label_expansion_review_batch_v1.csv", encoding="utf-8-sig")
        summary = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_label_expansion_review_batch_summary_v1.csv", encoding="utf-8-sig")
        evidence = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_label_expansion_review_evidence_v1.csv", encoding="utf-8-sig")

        positive_batch = batch.loc[batch["review_track"].eq("positive_review_batch")].copy()
        monitor_batch = batch.loc[batch["review_track"].eq("monitor_review_batch")].copy()
        common_batch = batch.loc[batch["review_track"].eq("common_cause_review_batch")].copy()

        assert_true(len(positive_batch.loc[positive_batch["candidate_priority_band"].eq("P1")]) == 2, "all P1 rows should be included")

        selected_p2 = positive_batch.loc[positive_batch["candidate_priority_band"].eq("P2")].copy()
        alpha_p2 = selected_p2.loc[selected_p2["panel_id"].astype(str).str.startswith("alpha.p2.")]
        beta_p2 = selected_p2.loc[selected_p2["panel_id"].astype(str).str.startswith("beta.p2.")]
        assert_true(len(selected_p2) == 30, "P2 selection should equal site-top5 rows plus global top-20 rows")
        assert_true(set(range(1, 6)).issubset(set(alpha_p2["site_score_rank"].astype(int))), "alpha site top5 should be included")
        assert_true(set(range(1, 6)).issubset(set(beta_p2["site_score_rank"].astype(int))), "beta site top5 should be included")
        assert_true("beta.p2.15" not in set(beta_p2["panel_id"]), "global top-up should still leave out lower beta rows")
        assert_true("beta.p2.16" not in set(beta_p2["panel_id"]), "global top-up should exclude the lowest beta row")
        assert_true(len(alpha_p2) == 16, "higher-scoring alpha P2 rows should survive global top-up in this fixture")
        assert_true(len(beta_p2) == 14, "lower-scoring beta P2 rows should be partially trimmed by global top-up")

        assert_true(len(monitor_batch) == 10, "monitor batch should cap at top 10 rows globally")
        assert_true(len(common_batch) == 2, "all common-cause review candidates should be included")

        first_positive = positive_batch.sort_values("review_priority_rank").iloc[0]
        assert_true(str(first_positive["review_track"]) == "positive_review_batch", "review track mismatch")
        assert_true(str(first_positive["suggested_label_action"]) == "inspect_for_positive_promotion", "positive action mismatch")

        evidence_alpha_p1 = evidence.loc[evidence["panel_id"].eq("alpha.p1.1")].iloc[0]
        assert_true(int(evidence_alpha_p1["future_fault_linked_ref_flag"]) == 1, "watch-now future fault ref should populate evidence")

        evidence_alpha_watch_review = evidence.loc[evidence["panel_id"].eq("alpha.p2.6")].iloc[0]
        assert_true(int(evidence_alpha_watch_review["future_truth_linked_ref_flag"]) == 1, "watch-review future truth ref should populate evidence")

        evidence_beta_fate = evidence.loc[evidence["panel_id"].eq("beta.p2.1")].iloc[0]
        assert_true("beta|beta.p2.1|2025-03-05" in str(evidence_beta_fate["overlapping_truth_case_ids"]), "fate truth case ids should populate evidence")

        evidence_delta_common = evidence.loc[evidence["panel_id"].eq("delta.cc.1")].iloc[0]
        assert_true("reaudit|delta|delta.cc.1|2025-05-08" in str(evidence_delta_common["overlapping_truth_case_ids"]), "reaudit overlap should populate evidence")
        assert_true("group_side" in str(evidence_delta_common["overlapping_truth_candidate_validities"]), "reaudit validity should populate evidence")

        overall = summary.loc[summary["record_type"].eq("overall")].iloc[0]
        assert_true(int(overall["positive_review_batch_count"]) == 32, "positive batch count mismatch")
        assert_true(int(overall["monitor_review_batch_count"]) == 10, "monitor batch count mismatch")
        assert_true(int(overall["common_cause_review_batch_count"]) == 2, "common-cause batch count mismatch")
        assert_true(int(overall["p1_included_count"]) == 2, "P1 included count mismatch")
        assert_true(int(overall["p2_included_count"]) == 30, "P2 included count mismatch")
        assert_true(int(overall["site_positive_gap_flag"]) == 1, "overall site positive gap should reflect included P1 sites")

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
