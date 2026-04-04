#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

FEATURE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "overlap_case_class",
    "fate_class",
    "cohort_hint",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "recurring_run_within_60d",
    "future_fault_linked_flag",
    "future_truth_linked_flag",
]

V0_SCORE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert_true(spec is not None and spec.loader is not None, f"failed to load module: {path.name}")
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def feature_row(
    panel_id: str,
    start: str,
    end: str,
    run_day_count: int,
    run_shape_class: str,
    *,
    overlap_case_class: str = "unmatched_to_review",
    recurring: int = 0,
    future_fault: int = 0,
    future_truth: int = 0,
    max_v_drop: float = 0.5,
    min_mid_v_ratio: float = 0.5,
    min_mid_ratio: float = 0.5,
    mean_signal_count: float = 1.5,
    max_signal_count: float = 2.0,
    p95_recon_error: float = 0.05,
    cond_evt_only_day_ratio: float = 0.5,
    ae_mid_or_hi_early_day_ratio: float = 0.3,
) -> dict[str, object]:
    return {
        "site": "alpha",
        "panel_id": panel_id,
        "run_start_date": start,
        "run_end_date": end,
        "run_day_count": run_day_count,
        "run_shape_class": run_shape_class,
        "overlap_case_class": overlap_case_class,
        "fate_class": "",
        "cohort_hint": "unmatched_other",
        "max_v_drop": max_v_drop,
        "min_mid_v_ratio": min_mid_v_ratio,
        "min_mid_ratio": min_mid_ratio,
        "mean_signal_count": mean_signal_count,
        "max_signal_count": max_signal_count,
        "p95_recon_error": p95_recon_error,
        "cond_evt_only_day_ratio": cond_evt_only_day_ratio,
        "ae_mid_or_hi_early_day_ratio": ae_mid_or_hi_early_day_ratio,
        "recurring_run_within_60d": recurring,
        "future_fault_linked_flag": future_fault,
        "future_truth_linked_flag": future_truth,
    }


def score_row(feature: dict[str, object], raw_score: float) -> dict[str, object]:
    return {
        "site": feature["site"],
        "panel_id": feature["panel_id"],
        "run_start_date": feature["run_start_date"],
        "run_end_date": feature["run_end_date"],
        "electrical_core_score": raw_score + 1.0,
        "electrical_core_minus_broadshape_050": raw_score,
    }


def build_fixture_root(root: Path) -> None:
    features = [
        feature_row(
            "watch.panel",
            "2025-01-01",
            "2025-01-04",
            12,
            "chronic_alert_run",
            recurring=1,
            max_v_drop=0.90,
            min_mid_v_ratio=0.20,
            min_mid_ratio=0.20,
            mean_signal_count=1.0,
            max_signal_count=1.8,
            p95_recon_error=0.01,
            cond_evt_only_day_ratio=0.2,
            ae_mid_or_hi_early_day_ratio=0.1,
        ),
        feature_row(
            "queue.panel",
            "2025-01-09",
            "2025-01-10",
            2,
            "medium_alert_run",
            max_v_drop=0.75,
            min_mid_v_ratio=0.35,
            min_mid_ratio=0.35,
            mean_signal_count=1.2,
            max_signal_count=1.6,
            p95_recon_error=0.02,
            cond_evt_only_day_ratio=0.4,
            ae_mid_or_hi_early_day_ratio=0.2,
        ),
        feature_row(
            "recover.panel",
            "2025-01-03",
            "2025-01-04",
            2,
            "short_alert_run",
            max_v_drop=0.45,
            min_mid_v_ratio=0.55,
            min_mid_ratio=0.55,
            mean_signal_count=1.0,
            max_signal_count=1.0,
            p95_recon_error=0.03,
            cond_evt_only_day_ratio=0.3,
            ae_mid_or_hi_early_day_ratio=0.2,
        ),
        feature_row(
            "hist.panel",
            "2024-12-01",
            "2024-12-01",
            1,
            "short_alert_run",
            max_v_drop=0.10,
            min_mid_v_ratio=0.90,
            min_mid_ratio=0.90,
            mean_signal_count=1.0,
            max_signal_count=1.0,
            p95_recon_error=0.01,
            cond_evt_only_day_ratio=0.1,
            ae_mid_or_hi_early_day_ratio=0.1,
        ),
        feature_row(
            "hist2.panel",
            "2024-11-20",
            "2024-11-20",
            1,
            "short_alert_run",
            max_v_drop=0.08,
            min_mid_v_ratio=0.92,
            min_mid_ratio=0.92,
            mean_signal_count=1.0,
            max_signal_count=1.0,
            p95_recon_error=0.01,
            cond_evt_only_day_ratio=0.1,
            ae_mid_or_hi_early_day_ratio=0.1,
        ),
    ]
    scores = [
        score_row(features[0], 10.0),
        score_row(features[1], 9.0),
        score_row(features[2], 6.0),
        score_row(features[3], 1.0),
        score_row(features[4], 0.5),
    ]

    write_csv(root / "_share" / "panel_day_engine_run_feature_table_v1.csv", features, FEATURE_COLS)
    write_csv(root / "_share" / "panel_day_engine_run_ranker_v0_scores.csv", scores, V0_SCORE_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_operator_baseline_v1.py"
    build_module = load_module(build_path, "operator_baseline_build")

    assert_true(
        build_module.BUILDER_SEQUENCE
        == [
            "research/prognostics/build_panel_day_engine_operator_run_consolidation_v1.py",
            "research/prognostics/build_panel_day_engine_operator_attention_delta_v1.py",
        ],
        "orchestrator should keep run consolidation then attention delta order",
    )

    official_paths = [
        repo_root / "_share" / "panel_day_engine_operator_baseline_manifest_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_baseline_summary_v1.csv",
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
            "research/prognostics/build_panel_day_engine_operator_baseline_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_operator_baseline_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="operator_baseline_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_operator_baseline_v1.py",
                "--root",
                str(tmp_root),
            ],
            repo_root,
        )
        assert_true(build_result.returncode == 0, build_result.stderr)

        share_dir = tmp_root / "_share"
        manifest_path = share_dir / "panel_day_engine_operator_baseline_manifest_v1.csv"
        summary_path = share_dir / "panel_day_engine_operator_baseline_summary_v1.csv"
        previous_snapshot_path = share_dir / "panel_day_engine_operator_attention_now_v1_previous.csv"

        assert_true(manifest_path.exists(), "baseline manifest should be generated")
        assert_true(summary_path.exists(), "baseline summary should be generated")
        assert_true(previous_snapshot_path.exists(), "first-run bootstrap should still write previous snapshot")

        manifest = pd.read_csv(manifest_path, encoding="utf-8-sig")
        summary = pd.read_csv(summary_path, encoding="utf-8-sig")
        attention_now = pd.read_csv(share_dir / "panel_day_engine_operator_attention_now_v1.csv", encoding="utf-8-sig")
        attention_delta = pd.read_csv(share_dir / "panel_day_engine_operator_attention_delta_v1.csv", encoding="utf-8-sig")
        delta_summary = pd.read_csv(share_dir / "panel_day_engine_operator_attention_delta_summary_v1.csv", encoding="utf-8-sig")

        assert_true(len(manifest) == 1, "manifest should emit one row")
        manifest_row = manifest.iloc[0]
        overall_summary = summary.loc[summary["record_type"].astype(str).eq("overall")].iloc[0]
        overall_delta = delta_summary.loc[delta_summary["record_type"].astype(str).eq("overall")].iloc[0]

        assert_true(bool(str(manifest_row["generated_at_utc"]).strip()), "manifest should include generated_at_utc")
        assert_true(int(manifest_row["attention_count"]) == 2, "manifest attention_count mismatch")
        assert_true(int(manifest_row["queue_count"]) == 1, "manifest queue_count mismatch")
        assert_true(int(manifest_row["backlog_count"]) == 2, "manifest backlog_count mismatch")
        assert_true(int(manifest_row["watchlist_count"]) == 1, "manifest watchlist_count mismatch")
        assert_true(int(manifest_row["watch_now_count"]) == 1, "manifest watch_now_count mismatch")
        assert_true(int(manifest_row["watch_review_count"]) == 0, "manifest watch_review_count mismatch")
        assert_true(int(manifest_row["attention_delta_count"]) == 2, "manifest attention_delta_count mismatch")
        assert_true(int(manifest_row["new_attention_count"]) == 2, "manifest new_attention_count mismatch")
        assert_true(int(manifest_row["dropped_attention_count"]) == 0, "manifest dropped_attention_count mismatch")
        assert_true(int(manifest_row["total_changed_count"]) == 2, "manifest total_changed_count mismatch")

        assert_true(int(overall_summary["attention_count"]) == 2, "summary attention_count mismatch")
        assert_true(int(overall_summary["queue_count"]) == 1, "summary queue_count mismatch")
        assert_true(int(overall_summary["backlog_count"]) == 2, "summary backlog_count mismatch")
        assert_true(int(overall_summary["watchlist_count"]) == 1, "summary watchlist_count mismatch")
        assert_true(int(overall_summary["watch_now_count"]) == 1, "summary watch_now_count mismatch")
        assert_true(int(overall_summary["watch_review_count"]) == 0, "summary watch_review_count mismatch")
        assert_true(int(overall_summary["new_attention_count"]) == 2, "summary new_attention_count mismatch")
        assert_true(int(overall_summary["dropped_attention_count"]) == 0, "summary dropped_attention_count mismatch")
        assert_true(int(overall_summary["total_changed_count"]) == 2, "summary total_changed_count mismatch")

        assert_true(int(overall_delta["current_attention_count"]) == len(attention_now), "delta summary should reflect current attention count")
        assert_true(len(attention_delta) == 2, "bootstrap delta should treat all current attention rows as new")
        assert_true(attention_delta["delta_class"].eq("new_attention").all(), "bootstrap delta rows should all be new_attention")

        previous_snapshot = pd.read_csv(previous_snapshot_path, encoding="utf-8-sig")
        assert_true(previous_snapshot.equals(attention_now), "previous snapshot should match current attention after bootstrap")

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
