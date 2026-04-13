#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ATTENTION_COLS = [
    "attention_class",
    "site",
    "panel_id",
    "display_start_date",
    "display_end_date",
    "display_day_count",
    "display_shape_class",
    "display_status_or_tier",
    "priority_band",
    "clipped_operator_score",
    "raw_operator_score",
    "overlap_case_class",
    "action_bucket",
    "watchlist_bucket",
    "score_hygiene_flag",
    "score_hygiene_reason_ko",
    "future_fault_linked_flag_ref",
    "future_truth_linked_flag_ref",
    "panel_has_watch_now_overlap_flag",
    "panel_watch_now_run_count",
    "panel_watch_now_total_day_count",
    "panel_watch_now_earliest_start_date",
    "panel_watch_now_latest_end_date",
    "panel_any_future_fault_linked_ref",
    "panel_any_future_truth_linked_ref",
    "panel_overlap_case_class_set",
    "panel_rollup_reason_ko",
    "attention_any_future_fault_linked_ref_flag",
    "attention_any_future_truth_linked_ref_flag",
    "attention_merge_reason_ko",
    "attention_reason_ko",
]

ATTENTION_SUMMARY_COLS = [
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
]

DELTA_COLS = [
    "site",
    "panel_id",
    "delta_class",
    "previous_attention_class",
    "current_attention_class",
    "previous_status_or_tier",
    "current_status_or_tier",
    "previous_priority_band",
    "current_priority_band",
    "previous_clipped_operator_score",
    "current_clipped_operator_score",
    "clipped_score_delta",
    "previous_action_bucket",
    "current_action_bucket",
    "previous_watchlist_bucket",
    "current_watchlist_bucket",
    "previous_panel_has_watch_now_overlap_flag",
    "current_panel_has_watch_now_overlap_flag",
    "previous_attention_any_future_fault_linked_ref_flag",
    "current_attention_any_future_fault_linked_ref_flag",
    "previous_attention_any_future_truth_linked_ref_flag",
    "current_attention_any_future_truth_linked_ref_flag",
    "delta_reason_ko",
]

BASELINE_MANIFEST_COLS = [
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
]

BASELINE_SUMMARY_COLS = [
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
]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def attention_row(
    panel_id: str,
    *,
    attention_class: str = "queue_run",
    priority_band: str = "P1",
    clipped_operator_score: float = 5.0,
    raw_operator_score: float | None = None,
    display_status_or_tier: str = "ongoing_run",
    display_day_count: int = 3,
    action_bucket: str = "investigate_now",
    watchlist_bucket: str = "none",
    any_future_fault: int = 0,
    any_future_truth: int = 0,
) -> dict[str, object]:
    if raw_operator_score is None:
        raw_operator_score = clipped_operator_score
    is_watch = attention_class == "watch_now_panel"
    return {
        "attention_class": attention_class,
        "site": "alpha",
        "panel_id": panel_id,
        "display_start_date": "2025-01-01",
        "display_end_date": "2025-01-03",
        "display_day_count": display_day_count,
        "display_shape_class": "chronic_alert_run" if is_watch else "medium_alert_run",
        "display_status_or_tier": display_status_or_tier,
        "priority_band": priority_band,
        "clipped_operator_score": clipped_operator_score,
        "raw_operator_score": raw_operator_score,
        "overlap_case_class": "unmatched_to_review",
        "action_bucket": action_bucket,
        "watchlist_bucket": watchlist_bucket,
        "score_hygiene_flag": 0,
        "score_hygiene_reason_ko": "clipping 영향 적음",
        "future_fault_linked_flag_ref": any_future_fault if is_watch else 0,
        "future_truth_linked_flag_ref": any_future_truth if is_watch else 0,
        "panel_has_watch_now_overlap_flag": 1 if is_watch else 0,
        "panel_watch_now_run_count": 2 if is_watch else 0,
        "panel_watch_now_total_day_count": 10 if is_watch else 0,
        "panel_watch_now_earliest_start_date": "2024-12-25" if is_watch else "",
        "panel_watch_now_latest_end_date": "2025-01-03" if is_watch else "",
        "panel_any_future_fault_linked_ref": any_future_fault if is_watch else 0,
        "panel_any_future_truth_linked_ref": any_future_truth if is_watch else 0,
        "panel_overlap_case_class_set": "unmatched_to_review" if is_watch else "",
        "panel_rollup_reason_ko": "future linkage reference 있음" if any_future_fault or any_future_truth else "",
        "attention_any_future_fault_linked_ref_flag": any_future_fault,
        "attention_any_future_truth_linked_ref_flag": any_future_truth,
        "attention_merge_reason_ko": "watch panel 단독" if is_watch else "queue 단독",
        "attention_reason_ko": "반복 chronic 대표 panel 주시" if is_watch else "즉시 대응 queue run",
    }


def write_inputs(
    root: Path,
    *,
    attention_rows: list[dict[str, object]],
    delta_rows: list[dict[str, object]],
    manifest_generated_at_utc: str,
) -> None:
    share_dir = root / "_share"
    attention_count = len(attention_rows)
    queue_count = sum(1 for row in attention_rows if row["attention_class"] == "queue_run")
    watch_now_panel_count = sum(1 for row in attention_rows if row["attention_class"] == "watch_now_panel")
    changed_attention_count = sum(1 for row in delta_rows if row["delta_class"] != "dropped_attention")
    dropped_attention_count = sum(1 for row in delta_rows if row["delta_class"] == "dropped_attention")

    attention_summary_rows = [
        {
            "record_type": "overall",
            "site": "",
            "attention_count": attention_count,
            "queue_run_attention_count": queue_count,
            "watch_now_panel_attention_count": watch_now_panel_count,
            "deduped_panel_overlap_count": 0,
            "deduped_overlap_future_fault_linked_ref_count": 0,
            "deduped_overlap_future_truth_linked_ref_count": 0,
            "attention_future_fault_linked_ref_count": 0,
            "attention_future_truth_linked_ref_count": 0,
            "attention_any_future_fault_linked_ref_count": 0,
            "attention_any_future_truth_linked_ref_count": 0,
        },
        {
            "record_type": "site",
            "site": "alpha",
            "attention_count": attention_count,
            "queue_run_attention_count": queue_count,
            "watch_now_panel_attention_count": watch_now_panel_count,
            "deduped_panel_overlap_count": 0,
            "deduped_overlap_future_fault_linked_ref_count": 0,
            "deduped_overlap_future_truth_linked_ref_count": 0,
            "attention_future_fault_linked_ref_count": 0,
            "attention_future_truth_linked_ref_count": 0,
            "attention_any_future_fault_linked_ref_count": 0,
            "attention_any_future_truth_linked_ref_count": 0,
        },
    ]

    baseline_summary_rows = [
        {
            "record_type": "overall",
            "site": "",
            "attention_count": attention_count,
            "queue_count": queue_count,
            "backlog_count": 0,
            "watchlist_count": watch_now_panel_count,
            "watch_now_count": watch_now_panel_count,
            "watch_review_count": 0,
            "new_attention_count": sum(1 for row in delta_rows if row["delta_class"] == "new_attention"),
            "dropped_attention_count": dropped_attention_count,
            "total_changed_count": len(delta_rows),
        },
        {
            "record_type": "site",
            "site": "alpha",
            "attention_count": attention_count,
            "queue_count": queue_count,
            "backlog_count": 0,
            "watchlist_count": watch_now_panel_count,
            "watch_now_count": watch_now_panel_count,
            "watch_review_count": 0,
            "new_attention_count": sum(1 for row in delta_rows if row["delta_class"] == "new_attention"),
            "dropped_attention_count": dropped_attention_count,
            "total_changed_count": len(delta_rows),
        },
    ]

    manifest_rows = [
        {
            "generated_at_utc": manifest_generated_at_utc,
            "attention_count": attention_count,
            "queue_count": queue_count,
            "backlog_count": 0,
            "watchlist_count": watch_now_panel_count,
            "watch_now_count": watch_now_panel_count,
            "watch_review_count": 0,
            "attention_delta_count": len(delta_rows),
            "new_attention_count": sum(1 for row in delta_rows if row["delta_class"] == "new_attention"),
            "dropped_attention_count": dropped_attention_count,
            "total_changed_count": len(delta_rows),
        }
    ]

    write_csv(share_dir / "panel_day_engine_operator_attention_now_v1.csv", attention_rows, ATTENTION_COLS)
    write_csv(share_dir / "panel_day_engine_operator_attention_summary_v1.csv", attention_summary_rows, ATTENTION_SUMMARY_COLS)
    write_csv(share_dir / "panel_day_engine_operator_attention_delta_v1.csv", delta_rows, DELTA_COLS)
    write_csv(share_dir / "panel_day_engine_operator_baseline_manifest_v1.csv", manifest_rows, BASELINE_MANIFEST_COLS)
    write_csv(share_dir / "panel_day_engine_operator_baseline_summary_v1.csv", baseline_summary_rows, BASELINE_SUMMARY_COLS)


def run_build(repo_root: Path, root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    result = run(
        [
            sys.executable,
            "research/prognostics/build_panel_day_engine_operator_digest_v1.py",
            "--root",
            str(root),
        ],
        repo_root,
    )
    assert_true(result.returncode == 0, result.stderr)
    share_dir = root / "_share"
    digest = pd.read_csv(share_dir / "panel_day_engine_operator_digest_v1.csv", encoding="utf-8-sig")
    summary = pd.read_csv(share_dir / "panel_day_engine_operator_digest_summary_v1.csv", encoding="utf-8-sig")
    return digest, summary


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    official_paths = [
        repo_root / "_share" / "panel_day_engine_operator_attention_now_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_delta_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_baseline_manifest_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_baseline_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_digest_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_digest_summary_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_operator_digest_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_operator_digest_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="operator_digest_empty_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        write_inputs(
            tmp_root,
            attention_rows=[
                attention_row("queue.one", attention_class="queue_run", priority_band="P1", clipped_operator_score=9.0),
                attention_row(
                    "watch.one",
                    attention_class="watch_now_panel",
                    display_status_or_tier="watch_now",
                    priority_band="P1",
                    clipped_operator_score=7.0,
                    action_bucket="recurring_backlog",
                    watchlist_bucket="recurring_watch_p1",
                ),
            ],
            delta_rows=[],
            manifest_generated_at_utc="2026-04-05T00:00:00Z",
        )
        digest, summary = run_build(repo_root, tmp_root)
        overall = summary.loc[summary["record_type"].astype(str).eq("overall")].iloc[0]
        assert_true(len(digest) == 2, "digest should keep one row per current attention item when delta is empty")
        assert_true(digest["changed_since_previous_flag"].eq(0).all(), "delta-empty digest should mark all rows unchanged")
        assert_true(digest["latest_delta_class"].fillna("").eq("").all(), "delta-empty digest should keep latest_delta_class blank")
        assert_true(digest["latest_delta_reason_ko"].fillna("").eq("").all(), "delta-empty digest should keep latest_delta_reason_ko blank")
        assert_true(digest["baseline_generated_at_utc"].eq("2026-04-05T00:00:00Z").all(), "digest should propagate baseline timestamp")
        assert_true(int(overall["attention_count"]) == 2, "delta-empty summary attention_count mismatch")
        assert_true(int(overall["changed_attention_count"]) == 0, "delta-empty changed count mismatch")
        assert_true(int(overall["unchanged_attention_count"]) == 2, "delta-empty unchanged count mismatch")
        assert_true(int(overall["queue_run_count"]) == 1, "delta-empty queue_run_count mismatch")
        assert_true(int(overall["watch_now_panel_count"]) == 1, "delta-empty watch count mismatch")

    with tempfile.TemporaryDirectory(prefix="operator_digest_changed_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        write_inputs(
            tmp_root,
            attention_rows=[
                attention_row("queue.changed", attention_class="queue_run", priority_band="P1", clipped_operator_score=9.0),
                attention_row("queue.same", attention_class="queue_run", priority_band="P2", clipped_operator_score=8.0),
                attention_row(
                    "watch.score",
                    attention_class="watch_now_panel",
                    display_status_or_tier="watch_now",
                    priority_band="P1",
                    clipped_operator_score=7.5,
                    action_bucket="recurring_backlog",
                    watchlist_bucket="recurring_watch_p1",
                ),
            ],
            delta_rows=[
                {
                    "site": "alpha",
                    "panel_id": "queue.changed",
                    "delta_class": "new_attention",
                    "previous_attention_class": "",
                    "current_attention_class": "queue_run",
                    "previous_status_or_tier": "",
                    "current_status_or_tier": "ongoing_run",
                    "previous_priority_band": "",
                    "current_priority_band": "P1",
                    "previous_clipped_operator_score": "",
                    "current_clipped_operator_score": 9.0,
                    "clipped_score_delta": "",
                    "previous_action_bucket": "",
                    "current_action_bucket": "investigate_now",
                    "previous_watchlist_bucket": "",
                    "current_watchlist_bucket": "none",
                    "previous_panel_has_watch_now_overlap_flag": "",
                    "current_panel_has_watch_now_overlap_flag": 0,
                    "previous_attention_any_future_fault_linked_ref_flag": "",
                    "current_attention_any_future_fault_linked_ref_flag": 0,
                    "previous_attention_any_future_truth_linked_ref_flag": "",
                    "current_attention_any_future_truth_linked_ref_flag": 0,
                    "delta_reason_ko": "신규 attention panel",
                },
                {
                    "site": "alpha",
                    "panel_id": "watch.score",
                    "delta_class": "score_shifted",
                    "previous_attention_class": "watch_now_panel",
                    "current_attention_class": "watch_now_panel",
                    "previous_status_or_tier": "watch_now",
                    "current_status_or_tier": "watch_now",
                    "previous_priority_band": "P1",
                    "current_priority_band": "P1",
                    "previous_clipped_operator_score": 6.0,
                    "current_clipped_operator_score": 7.5,
                    "clipped_score_delta": 1.5,
                    "previous_action_bucket": "recurring_backlog",
                    "current_action_bucket": "recurring_backlog",
                    "previous_watchlist_bucket": "recurring_watch_p1",
                    "current_watchlist_bucket": "recurring_watch_p1",
                    "previous_panel_has_watch_now_overlap_flag": 1,
                    "current_panel_has_watch_now_overlap_flag": 1,
                    "previous_attention_any_future_fault_linked_ref_flag": 0,
                    "current_attention_any_future_fault_linked_ref_flag": 0,
                    "previous_attention_any_future_truth_linked_ref_flag": 0,
                    "current_attention_any_future_truth_linked_ref_flag": 0,
                    "delta_reason_ko": "score 큰 변동",
                },
                {
                    "site": "alpha",
                    "panel_id": "dropped.only",
                    "delta_class": "dropped_attention",
                    "previous_attention_class": "queue_run",
                    "current_attention_class": "",
                    "previous_status_or_tier": "ongoing_run",
                    "current_status_or_tier": "",
                    "previous_priority_band": "P2",
                    "current_priority_band": "",
                    "previous_clipped_operator_score": 4.0,
                    "current_clipped_operator_score": "",
                    "clipped_score_delta": "",
                    "previous_action_bucket": "investigate_now",
                    "current_action_bucket": "",
                    "previous_watchlist_bucket": "none",
                    "current_watchlist_bucket": "",
                    "previous_panel_has_watch_now_overlap_flag": 0,
                    "current_panel_has_watch_now_overlap_flag": "",
                    "previous_attention_any_future_fault_linked_ref_flag": 0,
                    "current_attention_any_future_fault_linked_ref_flag": "",
                    "previous_attention_any_future_truth_linked_ref_flag": 0,
                    "current_attention_any_future_truth_linked_ref_flag": "",
                    "delta_reason_ko": "attention에서 제거됨",
                },
            ],
            manifest_generated_at_utc="2026-04-05T01:23:45Z",
        )
        digest, summary = run_build(repo_root, tmp_root)
        overall = summary.loc[summary["record_type"].astype(str).eq("overall")].iloc[0]

        assert_true(digest["panel_id"].tolist() == ["queue.changed", "queue.same", "watch.score"], "digest sorting should keep queue before watch and changed queue before unchanged queue")
        assert_true(
            dict(zip(digest["panel_id"], digest["changed_since_previous_flag"])) == {
                "queue.changed": 1,
                "queue.same": 0,
                "watch.score": 1,
            },
            "changed flag should be set only for current attention rows present in delta",
        )
        watch_score = digest.loc[digest["panel_id"].eq("watch.score")].iloc[0]
        queue_changed = digest.loc[digest["panel_id"].eq("queue.changed")].iloc[0]
        assert_true(queue_changed["latest_delta_class"] == "new_attention", "new attention row should carry latest delta class")
        assert_true(queue_changed["latest_delta_reason_ko"] == "신규 attention panel", "new attention row should carry latest delta reason")
        assert_true(
            pd.isna(queue_changed["previous_attention_class"]) or str(queue_changed["previous_attention_class"]) == "",
            "new attention row should keep previous class blank",
        )
        assert_true(float(watch_score["previous_clipped_operator_score"]) == 6.0, "previous clipped score should join from delta")
        assert_true(abs(float(watch_score["clipped_score_delta"]) - 1.5) < 1e-9, "clipped_score_delta should join from delta")
        assert_true(watch_score["baseline_generated_at_utc"] == "2026-04-05T01:23:45Z", "digest should propagate baseline timestamp")

        assert_true(int(overall["attention_count"]) == 3, "digest summary attention_count mismatch")
        assert_true(int(overall["changed_attention_count"]) == 2, "digest summary changed_attention_count should exclude dropped rows")
        assert_true(int(overall["unchanged_attention_count"]) == 1, "digest summary unchanged_attention_count mismatch")
        assert_true(int(overall["queue_run_count"]) == 2, "digest summary queue_run_count mismatch")
        assert_true(int(overall["watch_now_panel_count"]) == 1, "digest summary watch count mismatch")
        assert_true(int(overall["new_attention_count"]) == 1, "digest summary new_attention_count mismatch")
        assert_true(int(overall["dropped_attention_count"]) == 1, "digest summary dropped_attention_count mismatch")
        assert_true(int(overall["score_shifted_count"]) == 1, "digest summary score_shifted_count mismatch")
        assert_true(int(overall["generated_at_utc"] == "2026-04-05T01:23:45Z"), "digest summary generated_at_utc mismatch")

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
