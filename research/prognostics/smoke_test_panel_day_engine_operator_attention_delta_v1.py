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


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=ATTENTION_COLS).to_csv(path, index=False, encoding="utf-8-sig")


def attention_row(
    panel_id: str,
    *,
    attention_class: str = "queue_run",
    status_or_tier: str = "ongoing_run",
    priority_band: str = "P1",
    clipped_operator_score: float = 5.0,
    raw_operator_score: float | None = None,
    action_bucket: str = "investigate_now",
    watchlist_bucket: str = "none",
    panel_has_overlap: int = 0,
    any_future_fault: int = 0,
    any_future_truth: int = 0,
    overlap_case_class: str = "unmatched_to_review",
    merge_reason: str = "queue 단독",
    attention_reason: str = "즉시 대응 queue run",
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
        "display_day_count": 3,
        "display_shape_class": "chronic_alert_run" if is_watch else "medium_alert_run",
        "display_status_or_tier": status_or_tier,
        "priority_band": priority_band,
        "clipped_operator_score": clipped_operator_score,
        "raw_operator_score": raw_operator_score,
        "overlap_case_class": overlap_case_class,
        "action_bucket": action_bucket,
        "watchlist_bucket": watchlist_bucket,
        "score_hygiene_flag": 0,
        "score_hygiene_reason_ko": "clipping 영향 적음",
        "future_fault_linked_flag_ref": any_future_fault if is_watch else 0,
        "future_truth_linked_flag_ref": any_future_truth if is_watch else 0,
        "panel_has_watch_now_overlap_flag": panel_has_overlap,
        "panel_watch_now_run_count": 2 if panel_has_overlap else 0,
        "panel_watch_now_total_day_count": 11 if panel_has_overlap else 0,
        "panel_watch_now_earliest_start_date": "2024-12-20" if panel_has_overlap else "",
        "panel_watch_now_latest_end_date": "2025-01-03" if panel_has_overlap else "",
        "panel_any_future_fault_linked_ref": any_future_fault if panel_has_overlap or is_watch else 0,
        "panel_any_future_truth_linked_ref": any_future_truth if panel_has_overlap or is_watch else 0,
        "panel_overlap_case_class_set": overlap_case_class if panel_has_overlap or is_watch else "",
        "panel_rollup_reason_ko": "future linkage reference 있음" if any_future_fault or any_future_truth else "",
        "attention_any_future_fault_linked_ref_flag": any_future_fault,
        "attention_any_future_truth_linked_ref_flag": any_future_truth,
        "attention_merge_reason_ko": merge_reason,
        "attention_reason_ko": attention_reason,
    }


def run_build(repo_root: Path, root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    result = run(
        [
            sys.executable,
            "research/prognostics/build_panel_day_engine_operator_attention_delta_v1.py",
            "--root",
            str(root),
        ],
        repo_root,
    )
    assert_true(result.returncode == 0, result.stderr)
    share_dir = root / "_share"
    delta = pd.read_csv(share_dir / "panel_day_engine_operator_attention_delta_v1.csv", encoding="utf-8-sig")
    summary = pd.read_csv(share_dir / "panel_day_engine_operator_attention_delta_summary_v1.csv", encoding="utf-8-sig")
    return delta, summary


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    official_paths = [
        repo_root / "_share" / "panel_day_engine_operator_attention_now_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_now_v1_previous.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_delta_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_delta_summary_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_operator_attention_delta_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_operator_attention_delta_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="attention_delta_bootstrap_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        share_dir = tmp_root / "_share"
        current_path = share_dir / "panel_day_engine_operator_attention_now_v1.csv"
        current_rows = [
            attention_row("bootstrap.queue", clipped_operator_score=6.0),
            attention_row(
                "bootstrap.watch",
                attention_class="watch_now_panel",
                status_or_tier="watch_now",
                priority_band="P1",
                clipped_operator_score=4.0,
                action_bucket="recurring_backlog",
                watchlist_bucket="recurring_watch_p1",
                panel_has_overlap=1,
                any_future_fault=1,
                merge_reason="watch panel 단독",
                attention_reason="반복 chronic 대표 panel 주시",
            ),
        ]
        write_csv(current_path, current_rows)
        delta, summary = run_build(repo_root, tmp_root)
        previous_path = share_dir / "panel_day_engine_operator_attention_now_v1_previous.csv"

        assert_true(len(delta) == 2, "bootstrap run should mark all current rows as delta rows")
        assert_true(delta["delta_class"].eq("new_attention").all(), "bootstrap delta rows should all be new_attention")
        overall = summary.loc[summary["record_type"].eq("overall")].iloc[0]
        assert_true(int(overall["current_attention_count"]) == 2, "bootstrap current attention count mismatch")
        assert_true(int(overall["previous_attention_count"]) == 0, "bootstrap previous attention count should be zero")
        assert_true(int(overall["new_attention_count"]) == 2, "bootstrap new attention count mismatch")
        assert_true(int(overall["total_changed_count"]) == 2, "bootstrap changed count mismatch")
        assert_true(previous_path.exists(), "bootstrap run should still write previous snapshot")
        assert_true(previous_path.read_bytes() == current_path.read_bytes(), "previous snapshot should copy current after bootstrap")

    with tempfile.TemporaryDirectory(prefix="attention_delta_compare_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        share_dir = tmp_root / "_share"
        current_path = share_dir / "panel_day_engine_operator_attention_now_v1.csv"
        previous_path = share_dir / "panel_day_engine_operator_attention_now_v1_previous.csv"

        previous_rows = [
            attention_row("dropped.panel", clipped_operator_score=9.0),
            attention_row(
                "class.panel",
                attention_class="watch_now_panel",
                status_or_tier="watch_now",
                priority_band="P1",
                clipped_operator_score=8.0,
                action_bucket="recurring_backlog",
                watchlist_bucket="recurring_watch_p1",
                panel_has_overlap=1,
                merge_reason="watch panel 단독",
                attention_reason="반복 chronic 대표 panel 주시",
            ),
            attention_row("status.panel", status_or_tier="ongoing_run", priority_band="P2", clipped_operator_score=7.0),
            attention_row("priority.panel", status_or_tier="ongoing_run", priority_band="P2", clipped_operator_score=6.0),
            attention_row("score.panel", status_or_tier="ongoing_run", priority_band="P1", clipped_operator_score=7.0),
            attention_row("metadata.panel", status_or_tier="ongoing_run", priority_band="P2", clipped_operator_score=5.0),
            attention_row(
                "unchanged.panel",
                attention_class="watch_now_panel",
                status_or_tier="watch_now",
                priority_band="P1",
                clipped_operator_score=4.0,
                action_bucket="recurring_backlog",
                watchlist_bucket="recurring_watch_p1",
                panel_has_overlap=1,
                any_future_truth=1,
                merge_reason="watch panel 단독",
                attention_reason="반복 chronic 대표 panel 주시",
            ),
        ]
        current_rows = [
            attention_row("new.panel", clipped_operator_score=9.5),
            attention_row("class.panel", attention_class="queue_run", status_or_tier="ongoing_run", priority_band="P1", clipped_operator_score=8.0),
            attention_row("status.panel", status_or_tier="new_run", priority_band="P2", clipped_operator_score=7.0),
            attention_row("priority.panel", status_or_tier="ongoing_run", priority_band="P1", clipped_operator_score=6.0),
            attention_row("score.panel", status_or_tier="ongoing_run", priority_band="P1", clipped_operator_score=8.4),
            attention_row(
                "metadata.panel",
                status_or_tier="ongoing_run",
                priority_band="P2",
                clipped_operator_score=5.5,
                panel_has_overlap=1,
                any_future_fault=1,
                merge_reason="queue 우선, panel reference 병합",
            ),
            attention_row(
                "unchanged.panel",
                attention_class="watch_now_panel",
                status_or_tier="watch_now",
                priority_band="P1",
                clipped_operator_score=4.0,
                action_bucket="recurring_backlog",
                watchlist_bucket="recurring_watch_p1",
                panel_has_overlap=1,
                any_future_truth=1,
                merge_reason="watch panel 단독",
                attention_reason="반복 chronic 대표 panel 주시",
            ),
        ]
        write_csv(previous_path, previous_rows)
        write_csv(current_path, current_rows)

        delta, summary = run_build(repo_root, tmp_root)
        updated_previous = pd.read_csv(previous_path, encoding="utf-8-sig")
        current_loaded = pd.read_csv(current_path, encoding="utf-8-sig")

        expected_classes = {
            "new.panel": "new_attention",
            "dropped.panel": "dropped_attention",
            "class.panel": "attention_class_changed",
            "status.panel": "status_or_tier_changed",
            "priority.panel": "priority_changed",
            "score.panel": "score_shifted",
            "metadata.panel": "metadata_changed",
        }
        actual_classes = dict(zip(delta["panel_id"], delta["delta_class"]))
        assert_true(actual_classes == expected_classes, "delta classification should cover new/dropped/class/status/priority/score/metadata changes")

        overall = summary.loc[summary["record_type"].eq("overall")].iloc[0]
        assert_true(int(overall["current_attention_count"]) == 7, "comparison current attention count mismatch")
        assert_true(int(overall["previous_attention_count"]) == 7, "comparison previous attention count mismatch")
        assert_true(int(overall["new_attention_count"]) == 1, "new_attention summary count mismatch")
        assert_true(int(overall["dropped_attention_count"]) == 1, "dropped_attention summary count mismatch")
        assert_true(int(overall["attention_class_changed_count"]) == 1, "attention_class_changed summary count mismatch")
        assert_true(int(overall["status_or_tier_changed_count"]) == 1, "status_or_tier_changed summary count mismatch")
        assert_true(int(overall["priority_changed_count"]) == 1, "priority_changed summary count mismatch")
        assert_true(int(overall["score_shifted_count"]) == 1, "score_shifted summary count mismatch")
        assert_true(int(overall["metadata_changed_count"]) == 1, "metadata_changed summary count mismatch")
        assert_true(int(overall["total_changed_count"]) == 7, "total_changed_count mismatch")

        metadata_row = delta.loc[delta["panel_id"].eq("metadata.panel")].iloc[0]
        assert_true(
            int(metadata_row["current_panel_has_watch_now_overlap_flag"]) == 1,
            "metadata delta should expose current panel overlap flag",
        )
        assert_true(
            int(metadata_row["current_attention_any_future_fault_linked_ref_flag"]) == 1,
            "metadata delta should expose current combined future fault flag",
        )
        score_row = delta.loc[delta["panel_id"].eq("score.panel")].iloc[0]
        assert_true(
            abs(float(score_row["clipped_score_delta"]) - 1.4) < 1e-9,
            "score delta should reflect clipped score change",
        )

        assert_true(
            "dropped.panel" in set(delta["panel_id"]),
            "dropped panel should appear in delta before snapshot overwrite",
        )
        assert_true(
            "dropped.panel" not in set(updated_previous["panel_id"]),
            "updated previous snapshot should match current after comparison",
        )
        assert_true(
            updated_previous.equals(current_loaded),
            "previous snapshot should be overwritten with current only after comparison",
        )

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
