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


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def feature_row(
    site: str,
    panel_id: str,
    start: str,
    end: str,
    *,
    cohort_hint: str,
    fate_class: str = "",
    future_fault_linked_flag: int = 0,
    future_truth_linked_flag: int = 0,
    run_day_count: int = 3,
) -> dict[str, object]:
    return {
        "site": site,
        "panel_id": panel_id,
        "run_start_date": start,
        "run_end_date": end,
        "run_day_count": run_day_count,
        "run_shape_class": "chronic_alert_run" if run_day_count >= 10 else "medium_alert_run",
        "overlap_case_class": "unmatched_to_review",
        "delta_run_class": "added_run",
        "fate_class": fate_class,
        "cohort_hint": cohort_hint,
        "pre_ews_day_count": 1,
        "ews_warning_day_count": 1,
        "pre_alarm_day_count": 1,
        "prefault_B_day_count": 0,
        "pre_ews_run_count": 1,
        "ews_warning_run_count": 1,
        "pre_alarm_run_count": 1,
        "prefault_B_run_count": 0,
        "pre_alarm_max_run": 1,
        "max_signal_count": 2.0,
        "mean_signal_count": 1.5,
        "any_data_bad": 0,
        "data_bad_day_ratio": 0.0,
        "cond_evt_day_ratio": 0.4,
        "cond_evt_only_day_ratio": 0.2,
        "cond_evt_same_day_early_corroborated_day_ratio": 0.1,
        "ae_mid_or_hi_early_day_ratio": 0.2,
        "dtw_mid_or_hi_early_day_ratio": 0.2,
        "hs_mid_or_hi_early_day_ratio": 0.2,
        "max_recon_error": 0.1,
        "p95_recon_error": 0.1,
        "max_dtw_dist": 1.0,
        "p95_dtw_dist": 1.0,
        "max_hs_score": 1.0,
        "p95_hs_score": 1.0,
        "min_mid_ratio": 0.8,
        "min_mid_v_ratio": 0.8,
        "min_mid_i_ratio": 0.8,
        "max_v_drop": 0.2,
        "recurring_run_within_60d": 0,
        "future_fault_linked_flag": future_fault_linked_flag,
        "future_truth_linked_flag": future_truth_linked_flag,
    }


def build_fixture_root(tmp_root: Path) -> None:
    feature_rows = [
        feature_row("alpha", "run.pos.priority", "2025-01-01", "2025-01-03", cohort_hint="eligible_local", fate_class="isolated_unexplained"),
        feature_row("alpha", "run.pos.future", "2025-01-04", "2025-01-06", cohort_hint="unmatched_other", future_truth_linked_flag=1),
        feature_row("alpha", "run.neg.cohort", "2025-01-07", "2025-01-09", cohort_hint="nuisance_alert"),
        feature_row("beta", "run.neg.fate", "2025-02-01", "2025-02-03", cohort_hint="unmatched_other", fate_class="isolated_unexplained"),
        feature_row("beta", "run.mon.cohort", "2025-02-04", "2025-02-06", cohort_hint="recurring_monitor_like"),
        feature_row("beta", "run.mon.fate", "2025-02-07", "2025-02-09", cohort_hint="unmatched_other", fate_class="recurring_chronic_monitor_like", run_day_count=12),
        feature_row("beta", "run.other", "2025-02-10", "2025-02-12", cohort_hint="unmatched_other"),
    ]
    write_csv(tmp_root / "_share" / "panel_day_engine_run_feature_table_v1.csv", feature_rows, FEATURE_TABLE_COLS)

    write_csv(
        tmp_root / "_share" / "panel_day_engine_local_precursor_eligibility_cases_v1.csv",
        [
            {
                "site": "alpha",
                "panel_id": "run.pos.priority",
                "strict_trigger_date": "2025-01-10",
                "fault_start_date": "2025-01-20",
                "precursor_eligible_flag": 1,
                "temporality_reason_ko": "eligible",
            }
        ],
        ["site", "panel_id", "strict_trigger_date", "fault_start_date", "precursor_eligible_flag", "temporality_reason_ko"],
    )
    write_csv(
        tmp_root / "_share" / "panel_day_engine_local_pre_ews_replay_cases_v1.csv",
        [
            {
                "rule_id": "current_pre_ews",
                "cohort_type": "nuisance_nonlocal",
                "site": "alpha",
                "panel_id": "run.neg.cohort",
                "strict_trigger_date": "2025-01-08",
                "any_pre_ews_replay_hit_flag": 1,
                "any_ews_warning_replay_hit_flag": 0,
                "any_pre_alarm_replay_hit_flag": 1,
            }
        ],
        [
            "rule_id",
            "cohort_type",
            "site",
            "panel_id",
            "strict_trigger_date",
            "any_pre_ews_replay_hit_flag",
            "any_ews_warning_replay_hit_flag",
            "any_pre_alarm_replay_hit_flag",
        ],
    )
    write_csv(
        tmp_root / "_share" / "panel_day_engine_local_seed_carry_fate_cases_v1.csv",
        [
            {
                "site": "alpha",
                "panel_id": "run.pos.future",
                "run_start_date": "2025-01-04",
                "run_end_date": "2025-01-06",
                "fate_class": "",
                "recurring_run_within_60d": 0,
                "future_truth_overlap_30d": 1,
                "future_truth_overlap_60d": 1,
            },
            {
                "site": "beta",
                "panel_id": "run.neg.fate",
                "run_start_date": "2025-02-01",
                "run_end_date": "2025-02-03",
                "fate_class": "isolated_unexplained",
                "recurring_run_within_60d": 0,
                "future_truth_overlap_30d": 0,
                "future_truth_overlap_60d": 0,
            },
            {
                "site": "beta",
                "panel_id": "run.mon.fate",
                "run_start_date": "2025-02-07",
                "run_end_date": "2025-02-09",
                "fate_class": "recurring_chronic_monitor_like",
                "recurring_run_within_60d": 1,
                "future_truth_overlap_30d": 0,
                "future_truth_overlap_60d": 0,
            },
        ],
        [
            "site",
            "panel_id",
            "run_start_date",
            "run_end_date",
            "fate_class",
            "recurring_run_within_60d",
            "future_truth_overlap_30d",
            "future_truth_overlap_60d",
        ],
    )
    write_csv(
        tmp_root / "_share" / "panel_day_engine_local_seed_carry_delta_run_registry_v1.csv",
        [
            {
                "version": "current_seed_carry1",
                "site": row["site"],
                "panel_id": row["panel_id"],
                "run_start_date": row["run_start_date"],
                "run_end_date": row["run_end_date"],
                "run_day_count": row["run_day_count"],
                "run_shape_class": row["run_shape_class"],
                "delta_run_class": row["delta_run_class"],
                "overlap_case_class": row["overlap_case_class"],
                "overlapping_case_ids": "",
                "overlapping_case_types": "",
            }
            for row in feature_rows
        ],
        [
            "version",
            "site",
            "panel_id",
            "run_start_date",
            "run_end_date",
            "run_day_count",
            "run_shape_class",
            "delta_run_class",
            "overlap_case_class",
            "overlapping_case_ids",
            "overlapping_case_types",
        ],
    )
    write_csv(
        tmp_root / "_share" / "panel_day_engine_operator_run_watchlist_v1.csv",
        [
            {
                "site": "beta",
                "panel_id": "run.mon.fate",
                "run_start_date": "2025-02-07",
                "run_end_date": "2025-02-09",
                "run_day_count": 12,
                "run_shape_class": "chronic_alert_run",
                "status": "recurring_run",
                "priority_band": "P1",
                "action_bucket": "recurring_backlog",
                "overlap_case_class": "unmatched_to_review",
                "raw_operator_score": 9.0,
                "clipped_operator_score": 8.5,
                "raw_rank_within_site": 1,
                "clipped_rank_within_site": 1,
                "score_hygiene_flag": 0,
                "score_hygiene_reason_ko": "clipping 영향 적음",
                "future_fault_linked_flag": 0,
                "future_truth_linked_flag": 0,
                "watchlist_bucket": "recurring_watch_p1",
                "watchlist_tier": "watch_now",
                "watchlist_reason_ko": "반복 chronic 상위 우선순위",
                "watchlist_tier_reason_ko": "즉시 주시할 상위 반복 chronic",
            }
        ],
        [
            "site",
            "panel_id",
            "run_start_date",
            "run_end_date",
            "run_day_count",
            "run_shape_class",
            "status",
            "priority_band",
            "action_bucket",
            "overlap_case_class",
            "raw_operator_score",
            "clipped_operator_score",
            "raw_rank_within_site",
            "clipped_rank_within_site",
            "score_hygiene_flag",
            "score_hygiene_reason_ko",
            "future_fault_linked_flag",
            "future_truth_linked_flag",
            "watchlist_bucket",
            "watchlist_tier",
            "watchlist_reason_ko",
            "watchlist_tier_reason_ko",
        ],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_run_label_pack_v1.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_run_label_pack_v1.csv",
        repo_root / "_share" / "panel_day_engine_run_label_pack_summary_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_run_label_pack_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_run_label_pack_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="run_label_pack_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        label_pack = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_label_pack_v1.csv", encoding="utf-8-sig")
        summary = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_label_pack_summary_v1.csv", encoding="utf-8-sig")

        assert_true(len(label_pack) == 7, "label pack should preserve one row per run")

        positive_priority = label_pack.loc[label_pack["panel_id"].eq("run.pos.priority")].iloc[0]
        assert_true(str(positive_priority["label_bucket"]) == "positive_like", "positive priority should outrank nuisance/isolated fate")
        assert_true(str(positive_priority["training_label"]) == "positive", "positive priority training label mismatch")
        assert_true(str(positive_priority["label_confidence"]) == "strong", "positive priority confidence mismatch")
        assert_true("eligible_local" in str(positive_priority["label_sources_csv"]), "positive priority sources should include eligible_local")

        positive_future = label_pack.loc[label_pack["panel_id"].eq("run.pos.future")].iloc[0]
        assert_true(str(positive_future["label_bucket"]) == "positive_like", "future truth linkage should map to positive_like")
        assert_true(str(positive_future["training_label"]) == "positive", "future truth linkage should map to positive training")
        assert_true("future_truth_linked" in str(positive_future["label_sources_csv"]), "future truth linkage source missing")
        assert_true(int(positive_future["seed_carry_fate_case_flag"]) == 1, "seed carry fate enrichment should be carried")

        negative_fate = label_pack.loc[label_pack["panel_id"].eq("run.neg.fate")].iloc[0]
        assert_true(str(negative_fate["label_bucket"]) == "nuisance_like", "isolated fate should map to nuisance_like")
        assert_true(str(negative_fate["training_label"]) == "negative", "isolated fate should map to negative training")

        monitor_fate = label_pack.loc[label_pack["panel_id"].eq("run.mon.fate")].iloc[0]
        assert_true(str(monitor_fate["label_bucket"]) == "monitor_like", "recurring monitor fate should map to monitor_like")
        assert_true(str(monitor_fate["training_label"]) == "excluded", "monitor_like rows should be excluded from training")
        assert_true(int(monitor_fate["operator_watchlist_flag"]) == 1, "optional watchlist enrichment should join")
        assert_true(str(monitor_fate["watchlist_tier"]) == "watch_now", "watchlist tier enrichment mismatch")

        unlabeled = label_pack.loc[label_pack["panel_id"].eq("run.other")].iloc[0]
        assert_true(str(unlabeled["label_bucket"]) == "unlabeled_other", "unmatched row should stay unlabeled_other")
        assert_true(str(unlabeled["training_label"]) == "excluded", "unlabeled rows should be excluded")
        assert_true(str(unlabeled["label_confidence"]) == "weak", "unlabeled rows should be weak confidence")
        assert_true(str(unlabeled["label_sources_csv"]) == "unmatched_other", "unlabeled source tag mismatch")

        overall = summary.loc[summary["record_type"].astype(str).eq("overall")].iloc[0]
        assert_true(int(overall["total_run_count"]) == 7, "summary total_run_count mismatch")
        assert_true(int(overall["positive_like_count"]) == 2, "summary positive_like_count mismatch")
        assert_true(int(overall["nuisance_like_count"]) == 2, "summary nuisance_like_count mismatch")
        assert_true(int(overall["monitor_like_count"]) == 2, "summary monitor_like_count mismatch")
        assert_true(int(overall["unlabeled_other_count"]) == 1, "summary unlabeled_other_count mismatch")
        assert_true(int(overall["positive_training_count"]) == 2, "summary positive_training_count mismatch")
        assert_true(int(overall["negative_training_count"]) == 2, "summary negative_training_count mismatch")
        assert_true(int(overall["excluded_training_count"]) == 3, "summary excluded_training_count mismatch")
        assert_true(int(overall["strong_label_count"]) == 2, "summary strong_label_count mismatch")
        assert_true(int(overall["medium_label_count"]) == 4, "summary medium_label_count mismatch")
        assert_true(int(overall["weak_label_count"]) == 1, "summary weak_label_count mismatch")

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
