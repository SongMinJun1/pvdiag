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
    "recurring_run_within_60d",
    "future_fault_linked_flag",
    "future_truth_linked_flag",
]

V1_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "overlap_case_class",
    "delta_run_class",
    "cohort_hint",
    "fate_class",
    "recurring_run_within_60d",
    "future_fault_linked_flag",
    "future_truth_linked_flag",
    "eligibility_case_flag",
    "pre_ews_replay_case_flag",
    "seed_carry_fate_case_flag",
    "delta_run_registry_flag",
    "operator_watchlist_flag",
    "watchlist_bucket",
    "watchlist_tier",
    "label_bucket",
    "training_label",
    "label_confidence",
    "label_sources_csv",
    "label_reason_ko",
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
    run_day_count: int = 2,
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
        "recurring_run_within_60d": 1 if fate_class == "recurring_chronic_monitor_like" else 0,
        "future_fault_linked_flag": future_fault_linked_flag,
        "future_truth_linked_flag": future_truth_linked_flag,
    }


def v1_row(feature: dict[str, object], *, label_bucket: str, training_label: str, label_confidence: str, label_sources_csv: str, label_reason_ko: str) -> dict[str, object]:
    row = dict(feature)
    row.update(
        {
            "eligibility_case_flag": 0,
            "pre_ews_replay_case_flag": 0,
            "seed_carry_fate_case_flag": 1 if row.get("fate_class") else 0,
            "delta_run_registry_flag": 1,
            "operator_watchlist_flag": 0,
            "watchlist_bucket": "",
            "watchlist_tier": "",
            "label_bucket": label_bucket,
            "training_label": training_label,
            "label_confidence": label_confidence,
            "label_sources_csv": label_sources_csv,
            "label_reason_ko": label_reason_ko,
        }
    )
    return row


def build_fixture_root(tmp_root: Path) -> None:
    features = [
        feature_row("alpha", "run.priority", "2025-01-08", "2025-01-12", cohort_hint="nuisance_alert"),
        feature_row("alpha", "run.abrupt3", "2025-01-23", "2025-01-24", cohort_hint="unmatched_other"),
        feature_row("beta", "run.neg", "2025-02-01", "2025-02-02", cohort_hint="unmatched_other", fate_class="isolated_unexplained"),
        feature_row("beta", "run.monitor", "2025-02-03", "2025-02-12", cohort_hint="unmatched_other", fate_class="recurring_chronic_monitor_like", run_day_count=10),
        feature_row("gamma", "run.common", "2025-02-05", "2025-02-06", cohort_hint="unmatched_other"),
        feature_row("delta", "run.future", "2025-03-01", "2025-03-03", cohort_hint="unmatched_other", future_truth_linked_flag=1),
        feature_row("delta", "run.other", "2025-03-10", "2025-03-11", cohort_hint="unmatched_other"),
    ]
    write_csv(tmp_root / "_share" / "panel_day_engine_run_feature_table_v1.csv", features, FEATURE_TABLE_COLS)

    v1_rows = [
        v1_row(features[0], label_bucket="nuisance_like", training_label="negative", label_confidence="medium", label_sources_csv="nuisance_alert", label_reason_ko="nuisance 또는 isolated burden"),
        v1_row(features[1], label_bucket="unlabeled_other", training_label="excluded", label_confidence="weak", label_sources_csv="unmatched_other", label_reason_ko="아직 라벨 부족"),
        v1_row(features[2], label_bucket="nuisance_like", training_label="negative", label_confidence="medium", label_sources_csv="isolated_unexplained", label_reason_ko="nuisance 또는 isolated burden"),
        v1_row(features[3], label_bucket="monitor_like", training_label="excluded", label_confidence="medium", label_sources_csv="recurring_monitor_like", label_reason_ko="반복 chronic monitor형"),
        v1_row(features[4], label_bucket="unlabeled_other", training_label="excluded", label_confidence="weak", label_sources_csv="unmatched_other", label_reason_ko="아직 라벨 부족"),
        v1_row(features[5], label_bucket="positive_like", training_label="positive", label_confidence="strong", label_sources_csv="future_truth_linked", label_reason_ko="전조 eligible 또는 후행 fault linkage"),
        v1_row(features[6], label_bucket="unlabeled_other", training_label="excluded", label_confidence="weak", label_sources_csv="unmatched_other", label_reason_ko="아직 라벨 부족"),
    ]
    write_csv(tmp_root / "_share" / "panel_day_engine_run_label_pack_v1.csv", v1_rows, V1_COLS)

    write_csv(
        tmp_root / "_share" / "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv",
        [
            {"fault_family_id": "precursor", "eval_bucket_v2": "precursor_bearing_detectable_now"},
            {"fault_family_id": "abrupt", "eval_bucket_v2": "abrupt_or_no_precursor_now"},
            {"fault_family_id": "common", "eval_bucket_v2": "non_panel_or_common_cause"},
            {"fault_family_id": "unknown", "eval_bucket_v2": "unknown_needs_review"},
        ],
        ["fault_family_id", "eval_bucket_v2"],
    )

    write_csv(
        tmp_root / "_share" / "panel_day_engine_precursor_onset_truth_v1.csv",
        [
            {
                "site": "delta",
                "panel_id": "run.future",
                "fault_start_date": "2025-03-03",
                "preferred_precursor_onset_date": "2025-03-01",
            }
        ],
        ["site", "panel_id", "fault_start_date", "preferred_precursor_onset_date"],
    )
    write_csv(
        tmp_root / "_share" / "panel_day_engine_precursor_performance_cases_v1.csv",
        [
            {
                "site": "delta",
                "panel_id": "run.future",
                "fault_start_date": "2025-03-03",
                "preferred_precursor_onset_date": "2025-03-01",
            }
        ],
        ["site", "panel_id", "fault_start_date", "preferred_precursor_onset_date"],
    )
    write_csv(
        tmp_root / "_share" / "panel_day_engine_non_precursor_performance_cases_v1.csv",
        [
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "site": "alpha",
                "panel_id": "run.priority",
                "anchor_date": "2025-01-10",
                "final_fault_hit_by_anchor_flag": 1,
                "final_fault_hit_within_3d_after_flag": 0,
            },
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "site": "alpha",
                "panel_id": "run.abrupt3",
                "anchor_date": "2025-01-20",
                "final_fault_hit_by_anchor_flag": 0,
                "final_fault_hit_within_3d_after_flag": 1,
            },
        ],
        [
            "eval_bucket_v2",
            "site",
            "panel_id",
            "anchor_date",
            "final_fault_hit_by_anchor_flag",
            "final_fault_hit_within_3d_after_flag",
        ],
    )
    write_csv(
        tmp_root / "_share" / "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv",
        [
            {
                "eval_bucket_v2": "non_panel_or_common_cause",
                "site": "gamma",
                "panel_id": "run.common",
                "anchor_date": "2025-02-01",
                "combined_marker_flag": 1,
            }
        ],
        ["eval_bucket_v2", "site", "panel_id", "anchor_date", "combined_marker_flag"],
    )
    write_csv(
        tmp_root / "_share" / "panel_day_engine_local_seed_carry_fate_cases_v1.csv",
        [
            {
                "site": "beta",
                "panel_id": "run.neg",
                "run_start_date": "2025-02-01",
                "run_end_date": "2025-02-02",
                "fate_class": "isolated_unexplained",
            },
            {
                "site": "beta",
                "panel_id": "run.monitor",
                "run_start_date": "2025-02-03",
                "run_end_date": "2025-02-12",
                "fate_class": "recurring_chronic_monitor_like",
            },
        ],
        ["site", "panel_id", "run_start_date", "run_end_date", "fate_class"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_run_label_pack_v2.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_run_label_pack_v2.csv",
        repo_root / "_share" / "panel_day_engine_run_label_pack_summary_v2.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "pv_ae/panel_day_engine.py",
            "research/prognostics/build_panel_day_engine_run_label_pack_v2.py",
            "research/prognostics/smoke_test_panel_day_engine_run_label_pack_v2.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="run_label_pack_v2_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        label_pack = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_label_pack_v2.csv", encoding="utf-8-sig")
        summary = pd.read_csv(tmp_root / "_share" / "panel_day_engine_run_label_pack_summary_v2.csv", encoding="utf-8-sig")

        assert_true(len(label_pack) == 7, "label pack v2 should preserve one row per run")

        priority = label_pack.loc[label_pack["panel_id"].eq("run.priority")].iloc[0]
        assert_true(str(priority["label_bucket_v2"]) == "positive_like", "abrupt by-anchor should outrank nuisance label")
        assert_true(str(priority["training_label_v2"]) == "positive", "priority run training label mismatch")
        assert_true(str(priority["label_confidence_v2"]) == "strong", "abrupt by-anchor should be strong")
        assert_true(int(priority["abrupt_hit_by_anchor_flag"]) == 1, "abrupt by-anchor flag missing")
        assert_true("abrupt_hit_by_anchor" in str(priority["label_sources_csv_v2"]), "abrupt by-anchor source missing")

        abrupt3 = label_pack.loc[label_pack["panel_id"].eq("run.abrupt3")].iloc[0]
        assert_true(str(abrupt3["label_bucket_v2"]) == "positive_like", "within_3d abrupt hit should map to positive_like")
        assert_true(str(abrupt3["label_confidence_v2"]) == "medium", "within_3d abrupt hit should be medium confidence")
        assert_true(int(abrupt3["abrupt_hit_within_3d_flag"]) == 1, "within_3d abrupt flag missing")

        negative = label_pack.loc[label_pack["panel_id"].eq("run.neg")].iloc[0]
        assert_true(str(negative["label_bucket_v2"]) == "negative_like", "isolated fate should map to negative_like")
        assert_true(str(negative["training_label_v2"]) == "negative", "negative_like training label mismatch")

        monitor = label_pack.loc[label_pack["panel_id"].eq("run.monitor")].iloc[0]
        assert_true(str(monitor["label_bucket_v2"]) == "monitor_like", "monitor fate should map to monitor_like")
        assert_true(str(monitor["training_label_v2"]) == "exclude", "monitor_like rows should be excluded")

        common = label_pack.loc[label_pack["panel_id"].eq("run.common")].iloc[0]
        assert_true(str(common["label_bucket_v2"]) == "common_cause_like", "combined marker common cause should map to common_cause_like")
        assert_true(str(common["training_label_v2"]) == "exclude", "common cause rows should be excluded")
        assert_true(int(common["common_cause_descriptive_case_flag"]) == 1, "common cause descriptive flag missing")

        future = label_pack.loc[label_pack["panel_id"].eq("run.future")].iloc[0]
        assert_true(str(future["label_bucket_v2"]) == "positive_like", "future linkage should remain positive_like")
        assert_true(int(future["precursor_onset_support_flag"]) == 1, "precursor onset support flag should join")
        assert_true(int(future["precursor_performance_support_flag"]) == 1, "precursor performance support flag should join")

        unlabeled = label_pack.loc[label_pack["panel_id"].eq("run.other")].iloc[0]
        assert_true(str(unlabeled["label_bucket_v2"]) == "unlabeled_other", "unmatched row should stay unlabeled_other")
        assert_true(str(unlabeled["training_label_v2"]) == "exclude", "unmatched row should be excluded")
        assert_true(str(unlabeled["label_sources_csv_v2"]) == "unmatched_other", "unmatched source tag mismatch")

        overall = summary.loc[summary["record_type"].astype(str).eq("overall")].iloc[0]
        assert_true(int(overall["total_run_count"]) == 7, "summary total_run_count mismatch")
        assert_true(int(overall["positive_like_count"]) == 3, "summary positive_like_count mismatch")
        assert_true(int(overall["negative_like_count"]) == 1, "summary negative_like_count mismatch")
        assert_true(int(overall["monitor_like_count"]) == 1, "summary monitor_like_count mismatch")
        assert_true(int(overall["common_cause_like_count"]) == 1, "summary common_cause_like_count mismatch")
        assert_true(int(overall["unlabeled_other_count"]) == 1, "summary unlabeled_other_count mismatch")
        assert_true(int(overall["positive_training_count"]) == 3, "summary positive_training_count mismatch")
        assert_true(int(overall["negative_training_count"]) == 1, "summary negative_training_count mismatch")
        assert_true(int(overall["excluded_training_count"]) == 3, "summary excluded_training_count mismatch")
        assert_true(int(overall["strong_label_count"]) == 2, "summary strong_label_count mismatch")
        assert_true(int(overall["medium_label_count"]) == 4, "summary medium_label_count mismatch")
        assert_true(int(overall["weak_label_count"]) == 1, "summary weak_label_count mismatch")
        assert_true(int(overall["positive_training_increment_vs_v1"]) == 2, "positive increment vs v1 mismatch")
        assert_true(int(overall["negative_training_increment_vs_v1"]) == -1, "negative increment vs v1 mismatch")

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
