#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

PREVIEW_COLS = [
    "preview_attention_class",
    "site",
    "display_entity_id",
    "display_start_date",
    "display_end_date",
    "display_span_or_day_count",
    "display_shape_or_cluster_kind",
    "display_status_or_tier",
    "display_score",
    "linked_ref_flag",
    "truth_ref_flag",
    "cluster_panel_count",
    "member_overlap_with_attention_count",
    "preview_reason_ko",
]
ATTENTION_DELTA_COLS = [
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
CLUSTER_DELTA_COLS = [
    "site",
    "delta_class",
    "previous_cluster_id",
    "current_cluster_id",
    "previous_cluster_start_date",
    "previous_cluster_end_date",
    "current_cluster_start_date",
    "current_cluster_end_date",
    "previous_panel_count",
    "current_panel_count",
    "previous_representative_panel_id",
    "current_representative_panel_id",
    "previous_fault_linked_ref_flag",
    "current_fault_linked_ref_flag",
    "previous_truth_linked_ref_flag",
    "current_truth_linked_ref_flag",
    "overlap_days",
    "delta_reason_ko",
]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def load_builder_module(repo_root: Path):
    module_path = repo_root / "research/prognostics/build_panel_day_engine_operator_unified_digest_v1.py"
    spec = importlib.util.spec_from_file_location("operator_unified_digest_build", module_path)
    assert_true(spec is not None and spec.loader is not None, "failed to load unified digest builder module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False)


def frame_as_text(df: pd.DataFrame) -> pd.DataFrame:
    return df.fillna("").astype(str).reset_index(drop=True)


def preview_row(
    preview_attention_class: str,
    site: str,
    display_entity_id: str,
    *,
    display_start_date: str = "2026-04-01",
    display_end_date: str = "2026-04-02",
    span: int = 2,
    shape_or_kind: str = "medium_alert_run",
    status_or_tier: str = "ongoing_run",
    score: float = 5.0,
    linked_ref_flag: int = 0,
    truth_ref_flag: int = 0,
    cluster_panel_count: int = 1,
    preview_reason_ko: str = "fixture preview row",
) -> dict[str, object]:
    return {
        "preview_attention_class": preview_attention_class,
        "site": site,
        "display_entity_id": display_entity_id,
        "display_start_date": display_start_date,
        "display_end_date": display_end_date,
        "display_span_or_day_count": span,
        "display_shape_or_cluster_kind": shape_or_kind,
        "display_status_or_tier": status_or_tier,
        "display_score": score,
        "linked_ref_flag": linked_ref_flag,
        "truth_ref_flag": truth_ref_flag,
        "cluster_panel_count": cluster_panel_count,
        "member_overlap_with_attention_count": 0,
        "preview_reason_ko": preview_reason_ko,
    }


def attention_delta_row(site: str, panel_id: str, delta_class: str, delta_reason_ko: str) -> dict[str, object]:
    return {
        "site": site,
        "panel_id": panel_id,
        "delta_class": delta_class,
        "previous_attention_class": "queue_run",
        "current_attention_class": "queue_run",
        "previous_status_or_tier": "ongoing_run",
        "current_status_or_tier": "ongoing_run",
        "previous_priority_band": "P1",
        "current_priority_band": "P1",
        "previous_clipped_operator_score": 5.0,
        "current_clipped_operator_score": 6.0,
        "clipped_score_delta": 1.0,
        "previous_action_bucket": "investigate_now",
        "current_action_bucket": "investigate_now",
        "previous_watchlist_bucket": "none",
        "current_watchlist_bucket": "none",
        "previous_panel_has_watch_now_overlap_flag": 0,
        "current_panel_has_watch_now_overlap_flag": 0,
        "previous_attention_any_future_fault_linked_ref_flag": 0,
        "current_attention_any_future_fault_linked_ref_flag": 0,
        "previous_attention_any_future_truth_linked_ref_flag": 0,
        "current_attention_any_future_truth_linked_ref_flag": 0,
        "delta_reason_ko": delta_reason_ko,
    }


def cluster_delta_row(site: str, current_cluster_id: str, delta_class: str, delta_reason_ko: str) -> dict[str, object]:
    return {
        "site": site,
        "delta_class": delta_class,
        "previous_cluster_id": f"prev.{current_cluster_id}",
        "current_cluster_id": current_cluster_id,
        "previous_cluster_start_date": "2026-03-30",
        "previous_cluster_end_date": "2026-04-01",
        "current_cluster_start_date": "2026-04-01",
        "current_cluster_end_date": "2026-04-02",
        "previous_panel_count": 2,
        "current_panel_count": 3,
        "previous_representative_panel_id": "prev.rep",
        "current_representative_panel_id": "cur.rep",
        "previous_fault_linked_ref_flag": 0,
        "current_fault_linked_ref_flag": 1,
        "previous_truth_linked_ref_flag": 0,
        "current_truth_linked_ref_flag": 0,
        "overlap_days": 2,
        "delta_reason_ko": delta_reason_ko,
    }


def run_build(repo_root: Path, root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    result = run(
        [
            sys.executable,
            "research/prognostics/build_panel_day_engine_operator_unified_digest_v1.py",
            "--root",
            str(root),
        ],
        repo_root,
    )
    assert_true(result.returncode == 0, result.stderr)
    share_dir = root / "_share"
    digest = read_csv(share_dir / "panel_day_engine_operator_unified_digest_v1.csv")
    summary = read_csv(share_dir / "panel_day_engine_operator_unified_digest_summary_v1.csv")
    return digest, summary


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder_mod = load_builder_module(repo_root)

    official_paths = [
        repo_root / "_share" / "panel_day_engine_operator_attention_plus_discovery_cluster_preview_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_delta_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_secondary_discovery_cluster_delta_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_unified_digest_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_unified_digest_summary_v1.csv",
    ]
    official_state = {
        path: (path.exists(), hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "")
        for path in official_paths
    }

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_operator_unified_digest_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_operator_unified_digest_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="operator_unified_digest_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        share_dir = tmp_root / "_share"
        preview_rows = [
            preview_row("queue_run", "alpha", "alpha.queue.changed", score=9.0, preview_reason_ko="queue changed row"),
            preview_row("queue_run", "alpha", "alpha.queue.same", score=8.0, preview_reason_ko="queue same row"),
            preview_row("queue_run", "beta", "beta.queue.same", score=4.0, preview_reason_ko="beta queue same row"),
            preview_row(
                "watch_now_panel",
                "alpha",
                "alpha.watch.changed",
                status_or_tier="watch_now",
                shape_or_kind="chronic_alert_run",
                score=7.0,
                preview_reason_ko="watch changed row",
            ),
            preview_row(
                "watch_now_panel",
                "beta",
                "beta.watch.same",
                status_or_tier="watch_now",
                shape_or_kind="chronic_alert_run",
                score=5.0,
                preview_reason_ko="watch same row",
            ),
            preview_row(
                "secondary_value_cluster",
                "alpha",
                "alpha.cluster.changed",
                shape_or_kind="discovery_cluster",
                status_or_tier="secondary_discovery_cluster",
                score=10.0,
                linked_ref_flag=1,
                cluster_panel_count=3,
                preview_reason_ko="cluster changed row",
            ),
            preview_row(
                "secondary_value_cluster",
                "beta",
                "beta.cluster.same",
                shape_or_kind="discovery_cluster",
                status_or_tier="secondary_discovery_cluster",
                score=6.0,
                cluster_panel_count=2,
                preview_reason_ko="cluster same row",
            ),
        ]
        attention_delta_rows = [
            attention_delta_row("alpha", "alpha.queue.changed", "new_attention", "신규 attention panel"),
            attention_delta_row("alpha", "alpha.watch.changed", "status_or_tier_changed", "status 또는 tier 변경"),
            attention_delta_row("alpha", "alpha.dropped", "dropped_attention", "attention에서 제거됨"),
        ]
        cluster_delta_rows = [
            cluster_delta_row("alpha", "alpha.cluster.changed", "representative_changed", "대표 panel/run 변경"),
            {
                **cluster_delta_row("alpha", "", "dropped_cluster", "사라진 cluster"),
                "previous_cluster_id": "alpha.cluster.dropped",
            },
        ]

        write_csv(share_dir / "panel_day_engine_operator_attention_plus_discovery_cluster_preview_v1.csv", preview_rows, PREVIEW_COLS)
        write_csv(share_dir / "panel_day_engine_operator_attention_delta_v1.csv", attention_delta_rows, ATTENTION_DELTA_COLS)
        write_csv(share_dir / "panel_day_engine_operator_secondary_discovery_cluster_delta_v1.csv", cluster_delta_rows, CLUSTER_DELTA_COLS)

        expected_digest, expected_summary = builder_mod.build_outputs(tmp_root)
        digest, summary = run_build(repo_root, tmp_root)

        assert_true(frame_as_text(digest).equals(frame_as_text(expected_digest)), "unified digest output mismatch against build_outputs")
        assert_true(frame_as_text(summary).equals(frame_as_text(expected_summary)), "unified digest summary mismatch against build_outputs")

        queue_changed = digest.loc[
            (digest["preview_attention_class"].eq("queue_run")) & (digest["display_entity_id"].eq("alpha.queue.changed"))
        ].iloc[0]
        assert_true(int(queue_changed["changed_since_previous_flag"]) == 1, "changed attention queue row should get changed flag")
        assert_true(queue_changed["latest_delta_source"] == "attention_delta", "changed attention queue row should use attention_delta source")
        assert_true(queue_changed["latest_delta_class"] == "new_attention", "changed attention queue row delta class mismatch")
        assert_true(queue_changed["latest_delta_reason_ko"] == "신규 attention panel", "changed attention queue row delta reason mismatch")

        watch_same = digest.loc[
            (digest["preview_attention_class"].eq("watch_now_panel")) & (digest["display_entity_id"].eq("beta.watch.same"))
        ].iloc[0]
        assert_true(int(watch_same["changed_since_previous_flag"]) == 0, "unchanged current watch row should get changed flag 0")
        assert_true(watch_same["latest_delta_source"] == "none", "unchanged current watch row should have delta source none")
        assert_true(watch_same["latest_delta_class"] == "", "unchanged current watch row should keep latest_delta_class blank")

        cluster_changed = digest.loc[
            (digest["preview_attention_class"].eq("secondary_value_cluster"))
            & (digest["display_entity_id"].eq("alpha.cluster.changed"))
        ].iloc[0]
        assert_true(int(cluster_changed["changed_since_previous_flag"]) == 1, "changed cluster row should get changed flag")
        assert_true(cluster_changed["latest_delta_source"] == "cluster_delta", "changed cluster row should use cluster_delta source")
        assert_true(
            cluster_changed["latest_delta_class"] == "representative_changed",
            "changed cluster row delta class mismatch",
        )
        assert_true(
            cluster_changed["latest_delta_reason_ko"] == "대표 panel/run 변경",
            "changed cluster row delta reason mismatch",
        )

        expected_order = [
            "alpha.queue.changed",
            "alpha.queue.same",
            "beta.queue.same",
            "alpha.watch.changed",
            "beta.watch.same",
            "alpha.cluster.changed",
            "beta.cluster.same",
        ]
        assert_true(
            digest["display_entity_id"].tolist() == expected_order,
            "digest should sort by class, changed flag, score, cluster size, and span",
        )

        overall = summary.loc[summary["record_type"].eq("overall")].iloc[0]
        alpha_site = summary.loc[(summary["record_type"].eq("site")) & (summary["site"].eq("alpha"))].iloc[0]
        beta_site = summary.loc[(summary["record_type"].eq("site")) & (summary["site"].eq("beta"))].iloc[0]
        assert_true(int(overall["digest_count"]) == 7, "overall digest_count mismatch")
        assert_true(int(overall["queue_run_count"]) == 3, "overall queue_run_count mismatch")
        assert_true(int(overall["watch_now_panel_count"]) == 2, "overall watch_now_panel_count mismatch")
        assert_true(int(overall["secondary_value_cluster_count"]) == 2, "overall secondary_value_cluster_count mismatch")
        assert_true(int(overall["changed_count"]) == 3, "overall changed_count mismatch")
        assert_true(int(overall["changed_attention_count"]) == 2, "overall changed_attention_count mismatch")
        assert_true(int(overall["changed_cluster_count"]) == 1, "overall changed_cluster_count mismatch")
        assert_true(int(overall["changed_queue_run_count"]) == 1, "overall changed_queue_run_count mismatch")
        assert_true(int(overall["changed_watch_now_panel_count"]) == 1, "overall changed_watch_now_panel_count mismatch")
        assert_true(
            int(overall["changed_secondary_value_cluster_count"]) == 1,
            "overall changed_secondary_value_cluster_count mismatch",
        )
        assert_true(int(alpha_site["changed_count"]) == 3, "alpha changed_count mismatch")
        assert_true(int(beta_site["changed_count"]) == 0, "beta changed_count mismatch")

    for path, (existed_before, digest_before) in official_state.items():
        assert_true(path.exists() == existed_before, f"official file existence changed during smoke: {path.name}")
        if existed_before:
            digest_after = hashlib.sha256(path.read_bytes()).hexdigest()
            assert_true(digest_after == digest_before, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
