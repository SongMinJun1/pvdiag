#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def build_happy_fixture(root: Path, *, queue_count: int = 4, attention_count: int = 10, watch_now_count: int = 3) -> None:
    share = root / "_share"
    share.mkdir(parents=True, exist_ok=True)
    watch_review_count = 2
    watchlist_count = watch_now_count + watch_review_count
    backlog_count = 120
    digest_watch_now = attention_count - queue_count

    write_csv(
        share / "panel_day_engine_operator_refresh_manifest_v1.csv",
        [
            {
                "refresh_started_at_utc": "2026-04-05T00:00:00Z",
                "refresh_finished_at_utc": "2026-04-05T00:05:00Z",
                "requested_site_count": 2,
                "succeeded_site_count": 2,
                "failed_site_count": 0,
                "baseline_built_flag": 1,
                "baseline_builder_return_code": 0,
                "requested_sites_csv": "alpha,beta",
                "succeeded_sites_csv": "alpha,beta",
                "failed_sites_csv": "",
            }
        ],
        [
            "refresh_started_at_utc",
            "refresh_finished_at_utc",
            "requested_site_count",
            "succeeded_site_count",
            "failed_site_count",
            "baseline_built_flag",
            "baseline_builder_return_code",
            "requested_sites_csv",
            "succeeded_sites_csv",
            "failed_sites_csv",
        ],
    )
    write_csv(
        share / "panel_day_engine_operator_refresh_site_results_v1.csv",
        [
            {
                "site": "alpha",
                "started_at_utc": "2026-04-05T00:00:00Z",
                "finished_at_utc": "2026-04-05T00:02:00Z",
                "duration_seconds": 120.0,
                "success_flag": 1,
                "return_code": 0,
                "error_message": "",
            },
            {
                "site": "beta",
                "started_at_utc": "2026-04-05T00:02:00Z",
                "finished_at_utc": "2026-04-05T00:05:00Z",
                "duration_seconds": 180.0,
                "success_flag": 1,
                "return_code": 0,
                "error_message": "",
            },
        ],
        ["site", "started_at_utc", "finished_at_utc", "duration_seconds", "success_flag", "return_code", "error_message"],
    )
    write_csv(
        share / "panel_day_engine_operator_baseline_manifest_v1.csv",
        [
            {
                "generated_at_utc": "2026-04-05T00:06:00Z",
                "attention_count": attention_count,
                "queue_count": queue_count,
                "backlog_count": backlog_count,
                "watchlist_count": watchlist_count,
                "watch_now_count": watch_now_count,
                "watch_review_count": watch_review_count,
                "attention_delta_count": 3,
                "new_attention_count": 2,
                "dropped_attention_count": 1,
                "total_changed_count": 3,
                "digest_attention_count": attention_count,
                "digest_changed_attention_count": 3,
                "digest_queue_run_count": queue_count,
                "digest_watch_now_panel_count": digest_watch_now,
            }
        ],
        [
            "generated_at_utc",
            "attention_count",
            "queue_count",
            "backlog_count",
            "watchlist_count",
            "watch_now_count",
            "watch_review_count",
            "attention_delta_count",
            "new_attention_count",
            "dropped_attention_count",
            "total_changed_count",
            "digest_attention_count",
            "digest_changed_attention_count",
            "digest_queue_run_count",
            "digest_watch_now_panel_count",
        ],
    )
    write_csv(
        share / "panel_day_engine_operator_baseline_summary_v1.csv",
        [
            {
                "record_type": "overall",
                "site": "",
                "attention_count": attention_count,
                "queue_count": queue_count,
                "backlog_count": backlog_count,
                "watchlist_count": watchlist_count,
                "watch_now_count": watch_now_count,
                "watch_review_count": watch_review_count,
                "new_attention_count": 2,
                "dropped_attention_count": 1,
                "total_changed_count": 3,
                "digest_changed_attention_count": 3,
                "digest_queue_run_count": queue_count,
                "digest_watch_now_panel_count": digest_watch_now,
            },
            {
                "record_type": "site",
                "site": "alpha",
                "attention_count": attention_count // 2,
                "queue_count": queue_count // 2,
                "backlog_count": 70,
                "watchlist_count": watchlist_count // 2,
                "watch_now_count": 1,
                "watch_review_count": 1,
                "new_attention_count": 1,
                "dropped_attention_count": 0,
                "total_changed_count": 1,
                "digest_changed_attention_count": 1,
                "digest_queue_run_count": queue_count // 2,
                "digest_watch_now_panel_count": attention_count // 2 - queue_count // 2,
            },
            {
                "record_type": "site",
                "site": "beta",
                "attention_count": attention_count - attention_count // 2,
                "queue_count": queue_count - queue_count // 2,
                "backlog_count": 50,
                "watchlist_count": watchlist_count - watchlist_count // 2,
                "watch_now_count": watch_now_count - 1,
                "watch_review_count": 1,
                "new_attention_count": 1,
                "dropped_attention_count": 1,
                "total_changed_count": 2,
                "digest_changed_attention_count": 2,
                "digest_queue_run_count": queue_count - queue_count // 2,
                "digest_watch_now_panel_count": digest_watch_now - (attention_count // 2 - queue_count // 2),
            },
        ],
        [
            "record_type",
            "site",
            "attention_count",
            "queue_count",
            "backlog_count",
            "watchlist_count",
            "watch_now_count",
            "watch_review_count",
            "new_attention_count",
            "dropped_attention_count",
            "total_changed_count",
            "digest_changed_attention_count",
            "digest_queue_run_count",
            "digest_watch_now_panel_count",
        ],
    )
    write_csv(
        share / "panel_day_engine_operator_attention_summary_v1.csv",
        [
            {
                "record_type": "overall",
                "site": "",
                "attention_count": attention_count,
                "queue_run_attention_count": queue_count,
                "watch_now_panel_attention_count": digest_watch_now,
                "deduped_panel_overlap_count": 1,
                "deduped_overlap_future_fault_linked_ref_count": 0,
                "deduped_overlap_future_truth_linked_ref_count": 0,
                "attention_future_fault_linked_ref_count": 1,
                "attention_future_truth_linked_ref_count": 0,
                "attention_any_future_fault_linked_ref_count": 1,
                "attention_any_future_truth_linked_ref_count": 0,
            }
        ],
        [
            "record_type",
            "site",
            "attention_count",
            "queue_run_attention_count",
            "watch_now_panel_attention_count",
            "deduped_panel_overlap_count",
            "deduped_overlap_future_fault_linked_ref_count",
            "deduped_overlap_future_truth_linked_ref_count",
            "attention_future_fault_linked_ref_count",
            "attention_future_truth_linked_ref_count",
            "attention_any_future_fault_linked_ref_count",
            "attention_any_future_truth_linked_ref_count",
        ],
    )
    write_csv(
        share / "panel_day_engine_operator_digest_summary_v1.csv",
        [
            {
                "record_type": "overall",
                "site": "",
                "attention_count": attention_count,
                "changed_attention_count": 3,
                "unchanged_attention_count": attention_count - 3,
                "queue_run_count": queue_count,
                "watch_now_panel_count": digest_watch_now,
                "new_attention_count": 2,
                "dropped_attention_count": 1,
                "attention_class_changed_count": 0,
                "status_or_tier_changed_count": 1,
                "priority_changed_count": 0,
                "score_shifted_count": 1,
                "metadata_changed_count": 1,
                "generated_at_utc": "2026-04-05T00:06:00Z",
            }
        ],
        [
            "record_type",
            "site",
            "attention_count",
            "changed_attention_count",
            "unchanged_attention_count",
            "queue_run_count",
            "watch_now_panel_count",
            "new_attention_count",
            "dropped_attention_count",
            "attention_class_changed_count",
            "status_or_tier_changed_count",
            "priority_changed_count",
            "score_shifted_count",
            "metadata_changed_count",
            "generated_at_utc",
        ],
    )
    write_csv(
        share / "panel_day_engine_operator_run_summary_v1.csv",
        [
            {
                "record_type": "overall",
                "site": "",
                "total_runs": 100,
                "ongoing_run_count": 4,
                "new_run_count": 2,
                "recurring_run_count": 20,
                "recovered_run_count": 3,
                "chronic_run_count": 9,
                "p1_run_count": 5,
                "p2_run_count": 12,
                "investigate_now_count": 3,
                "monitor_active_count": 1,
                "recurring_backlog_count": 20,
                "recovered_backlog_count": 3,
                "historical_archive_count": 73,
                "queue_count": queue_count,
                "backlog_count": backlog_count,
                "queue_chronic_count": 1,
                "backlog_chronic_count": 8,
                "queue_future_fault_linked_count": 0,
                "queue_future_truth_linked_count": 0,
                "clipped_top20_overlap_vs_raw": 0.9,
                "clipped_top50_overlap_vs_raw": 0.95,
                "clipped_top100_overlap_vs_raw": 1.0,
                "score_hygiene_flag_count": 7,
                "score_hygiene_queue_count": 1,
                "score_hygiene_backlog_count": 5,
                "watchlist_count": watchlist_count,
                "watchlist_p1_count": watch_now_count,
                "watchlist_p2_count": watch_review_count,
                "watchlist_chronic_count": watchlist_count,
                "watch_now_count": watch_now_count,
                "watch_review_count": watch_review_count,
            }
        ],
        [
            "record_type",
            "site",
            "total_runs",
            "ongoing_run_count",
            "new_run_count",
            "recurring_run_count",
            "recovered_run_count",
            "chronic_run_count",
            "p1_run_count",
            "p2_run_count",
            "investigate_now_count",
            "monitor_active_count",
            "recurring_backlog_count",
            "recovered_backlog_count",
            "historical_archive_count",
            "queue_count",
            "backlog_count",
            "queue_chronic_count",
            "backlog_chronic_count",
            "queue_future_fault_linked_count",
            "queue_future_truth_linked_count",
            "clipped_top20_overlap_vs_raw",
            "clipped_top50_overlap_vs_raw",
            "clipped_top100_overlap_vs_raw",
            "score_hygiene_flag_count",
            "score_hygiene_queue_count",
            "score_hygiene_backlog_count",
            "watchlist_count",
            "watchlist_p1_count",
            "watchlist_p2_count",
            "watchlist_chronic_count",
            "watch_now_count",
            "watch_review_count",
        ],
    )
    write_csv(
        share / "panel_day_engine_operator_run_watchlist_summary_v1.csv",
        [
            {
                "record_type": "overall",
                "site": "",
                "watchlist_count": watchlist_count,
                "watchlist_p1_count": watch_now_count,
                "watchlist_p2_count": watch_review_count,
                "watch_now_count": watch_now_count,
                "watch_review_count": watch_review_count,
                "watch_now_panel_count": digest_watch_now,
                "panels_with_multiple_watch_now_runs": 1,
                "median_watch_now_runs_per_panel": 1.0,
                "watchlist_chronic_count": watchlist_count,
                "watchlist_unmatched_to_review_count": watchlist_count,
                "watchlist_eligible_local_overlap_count": 0,
                "watchlist_nuisance_overlap_count": 0,
                "watchlist_future_fault_linked_count": 1,
                "watchlist_future_truth_linked_count": 0,
                "watch_now_future_fault_linked_count": 1,
                "watch_now_future_truth_linked_count": 0,
                "watch_review_future_fault_linked_count": 0,
                "watch_review_future_truth_linked_count": 0,
            }
        ],
        [
            "record_type",
            "site",
            "watchlist_count",
            "watchlist_p1_count",
            "watchlist_p2_count",
            "watch_now_count",
            "watch_review_count",
            "watch_now_panel_count",
            "panels_with_multiple_watch_now_runs",
            "median_watch_now_runs_per_panel",
            "watchlist_chronic_count",
            "watchlist_unmatched_to_review_count",
            "watchlist_eligible_local_overlap_count",
            "watchlist_nuisance_overlap_count",
            "watchlist_future_fault_linked_count",
            "watchlist_future_truth_linked_count",
            "watch_now_future_fault_linked_count",
            "watch_now_future_truth_linked_count",
            "watch_review_future_fault_linked_count",
            "watch_review_future_truth_linked_count",
        ],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_operator_refresh_qa_v1.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_operator_refresh_qa_report_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_refresh_qa_summary_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_operator_refresh_qa_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_operator_refresh_qa_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="operator_refresh_qa_missing_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        write_csv(
            tmp_root / "_share" / "panel_day_engine_operator_refresh_manifest_v1.csv",
            [
                {
                    "refresh_started_at_utc": "2026-04-05T00:00:00Z",
                    "refresh_finished_at_utc": "2026-04-05T00:05:00Z",
                    "requested_site_count": 1,
                    "succeeded_site_count": 1,
                    "failed_site_count": 0,
                    "baseline_built_flag": 1,
                    "baseline_builder_return_code": 0,
                    "requested_sites_csv": "alpha",
                    "succeeded_sites_csv": "alpha",
                    "failed_sites_csv": "",
                }
            ],
            [
                "refresh_started_at_utc",
                "refresh_finished_at_utc",
                "requested_site_count",
                "succeeded_site_count",
                "failed_site_count",
                "baseline_built_flag",
                "baseline_builder_return_code",
                "requested_sites_csv",
                "succeeded_sites_csv",
                "failed_sites_csv",
            ],
        )
        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        report = pd.read_csv(tmp_root / "_share" / "panel_day_engine_operator_refresh_qa_report_v1.csv", encoding="utf-8-sig")
        summary = pd.read_csv(tmp_root / "_share" / "panel_day_engine_operator_refresh_qa_summary_v1.csv", encoding="utf-8-sig")
        assert_true(
            report.loc[report["check_name"].eq("site_results_exists"), "status"].iloc[0] == "fail",
            "missing file path should fail required existence check",
        )
        assert_true(
            report.loc[report["check_name"].eq("attention_digest_count_match"), "status"].iloc[0] == "skip",
            "downstream checks should skip when dependencies are missing",
        )
        assert_true(int(summary.iloc[0]["qa_pass_flag"]) == 0, "missing-file path should not pass QA")

    with tempfile.TemporaryDirectory(prefix="operator_refresh_qa_happy_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_happy_fixture(tmp_root)
        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        report = pd.read_csv(tmp_root / "_share" / "panel_day_engine_operator_refresh_qa_report_v1.csv", encoding="utf-8-sig")
        summary = pd.read_csv(tmp_root / "_share" / "panel_day_engine_operator_refresh_qa_summary_v1.csv", encoding="utf-8-sig")
        failed_rows = report.loc[report["status"].eq("fail")]
        warned_rows = report.loc[report["status"].eq("warn")]
        assert_true(failed_rows.empty, f"happy path should not fail hard checks: {failed_rows.to_dict('records')}")
        assert_true(warned_rows.empty, f"happy path should not trigger warn thresholds: {warned_rows.to_dict('records')}")
        assert_true(int(summary.iloc[0]["qa_pass_flag"]) == 1, "happy path should pass QA")
        assert_true(int(summary.iloc[0]["overall_attention_count"]) == 10, "happy path overall_attention_count mismatch")
        assert_true(int(summary.iloc[0]["overall_queue_count"]) == 4, "happy path overall_queue_count mismatch")
        assert_true(int(summary.iloc[0]["overall_watch_now_count"]) == 3, "happy path overall_watch_now_count mismatch")
        assert_true(int(summary.iloc[0]["overall_watch_review_count"]) == 2, "happy path overall_watch_review_count mismatch")
        assert_true(int(summary.iloc[0]["overall_backlog_count"]) == 120, "happy path overall_backlog_count mismatch")
        assert_true(int(summary.iloc[0]["overall_changed_count"]) == 3, "happy path overall_changed_count mismatch")

    with tempfile.TemporaryDirectory(prefix="operator_refresh_qa_warn_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_happy_fixture(tmp_root, queue_count=21, attention_count=25, watch_now_count=5)
        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        report = pd.read_csv(tmp_root / "_share" / "panel_day_engine_operator_refresh_qa_report_v1.csv", encoding="utf-8-sig")
        summary = pd.read_csv(tmp_root / "_share" / "panel_day_engine_operator_refresh_qa_summary_v1.csv", encoding="utf-8-sig")
        queue_warn = report.loc[report["check_name"].eq("queue_count_too_large")].iloc[0]
        assert_true(queue_warn["status"] == "warn", "queue_count_too_large should warn above threshold")
        assert_true(int(summary.iloc[0]["warn_count"]) >= 1, "warn path should increment warn_count")
        assert_true(int(summary.iloc[0]["qa_pass_flag"]) == 1, "warn-only path should still pass QA")

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
