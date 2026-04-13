#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

BASELINE_COLS = [
    "attention_class",
    "site",
    "attention_any_future_fault_linked_ref_flag",
    "attention_any_future_truth_linked_ref_flag",
]

PANEL_PREVIEW_COLS = [
    "preview_attention_class",
    "site",
    "attention_any_future_fault_linked_ref_flag",
    "attention_any_future_truth_linked_ref_flag",
]

CLUSTER_PREVIEW_COLS = [
    "preview_attention_class",
    "site",
    "linked_ref_flag",
    "truth_ref_flag",
]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def load_builder_module(repo_root: Path):
    module_path = repo_root / "research/prognostics/build_panel_day_engine_operator_attention_policy_audit_v1.py"
    spec = importlib.util.spec_from_file_location("operator_attention_policy_audit_build", module_path)
    assert_true(spec is not None and spec.loader is not None, "failed to load attention policy audit builder module")
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


def baseline_row(attention_class: str, site: str, *, fault: int = 0, truth: int = 0) -> dict[str, object]:
    return {
        "attention_class": attention_class,
        "site": site,
        "attention_any_future_fault_linked_ref_flag": fault,
        "attention_any_future_truth_linked_ref_flag": truth,
    }


def panel_preview_row(preview_attention_class: str, site: str, *, fault: int = 0, truth: int = 0) -> dict[str, object]:
    return {
        "preview_attention_class": preview_attention_class,
        "site": site,
        "attention_any_future_fault_linked_ref_flag": fault,
        "attention_any_future_truth_linked_ref_flag": truth,
    }


def cluster_preview_row(preview_attention_class: str, site: str, *, fault: int = 0, truth: int = 0) -> dict[str, object]:
    return {
        "preview_attention_class": preview_attention_class,
        "site": site,
        "linked_ref_flag": fault,
        "truth_ref_flag": truth,
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder_mod = load_builder_module(repo_root)

    official_paths = [
        repo_root / "_share" / "panel_day_engine_operator_attention_now_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_plus_discovery_preview_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_plus_discovery_preview_narrow_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_plus_discovery_cluster_preview_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_policy_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_attention_policy_recommendation_v1.csv",
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
            "research/prognostics/build_panel_day_engine_operator_attention_policy_audit_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_operator_attention_policy_audit_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="operator_attention_policy_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        share_dir = tmp_root / "_share"

        baseline_rows = [
            baseline_row("queue_run", "alpha"),
            baseline_row("watch_now_panel", "alpha", fault=1),
            baseline_row("queue_run", "beta"),
            baseline_row("watch_now_panel", "beta"),
        ]
        panel_rows = [
            panel_preview_row("queue_run", "alpha"),
            panel_preview_row("watch_now_panel", "alpha", fault=1),
            panel_preview_row("queue_run", "beta"),
            panel_preview_row("watch_now_panel", "beta"),
            panel_preview_row("secondary_value_panel", "alpha", fault=1),
            panel_preview_row("secondary_value_panel", "alpha", fault=1),
            panel_preview_row("secondary_value_panel", "beta", fault=1),
            panel_preview_row("secondary_value_panel", "alpha"),
        ]
        narrow_rows = [
            panel_preview_row("queue_run", "alpha"),
            panel_preview_row("watch_now_panel", "alpha", fault=1),
            panel_preview_row("queue_run", "beta"),
            panel_preview_row("watch_now_panel", "beta"),
            panel_preview_row("secondary_value_panel", "alpha", fault=1),
            panel_preview_row("secondary_value_panel", "beta", fault=1),
            panel_preview_row("secondary_value_panel", "alpha"),
        ]
        cluster_rows = [
            cluster_preview_row("queue_run", "alpha"),
            cluster_preview_row("watch_now_panel", "alpha", fault=1),
            cluster_preview_row("queue_run", "beta"),
            cluster_preview_row("watch_now_panel", "beta"),
            cluster_preview_row("secondary_value_cluster", "alpha", fault=1),
            cluster_preview_row("secondary_value_cluster", "beta", fault=1),
        ]

        write_csv(share_dir / builder_mod.BASELINE_ONLY_NAME, baseline_rows, BASELINE_COLS)
        write_csv(share_dir / builder_mod.DISCOVERY_PANEL_NAME, panel_rows, PANEL_PREVIEW_COLS)
        write_csv(share_dir / builder_mod.DISCOVERY_NARROW_NAME, narrow_rows, PANEL_PREVIEW_COLS)
        write_csv(share_dir / builder_mod.DISCOVERY_CLUSTER_NAME, cluster_rows, CLUSTER_PREVIEW_COLS)

        expected_summary, expected_recommendation = builder_mod.build_outputs(tmp_root)

        build_result = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_operator_attention_policy_audit_v1.py",
                "--root",
                str(tmp_root),
            ],
            repo_root,
        )
        assert_true(build_result.returncode == 0, build_result.stderr)

        summary = read_csv(share_dir / builder_mod.SUMMARY_OUTPUT_NAME)
        recommendation = read_csv(share_dir / builder_mod.RECOMMENDATION_OUTPUT_NAME)

        assert_true(
            frame_as_text(summary).equals(frame_as_text(expected_summary)),
            "summary output should match build_outputs",
        )
        assert_true(
            frame_as_text(recommendation).equals(frame_as_text(expected_recommendation)),
            "recommendation output should match build_outputs",
        )

        assert_true(summary["policy_name"].tolist() == builder_mod.POLICY_ORDER, "policy summary order mismatch")

        baseline = summary.loc[summary["policy_name"].eq("baseline_only")].iloc[0]
        panel = summary.loc[summary["policy_name"].eq("baseline_plus_discovery_panel")].iloc[0]
        narrow = summary.loc[summary["policy_name"].eq("baseline_plus_discovery_narrow")].iloc[0]
        cluster = summary.loc[summary["policy_name"].eq("baseline_plus_discovery_cluster")].iloc[0]

        assert_true(int(baseline["total_item_count"]) == 4, "baseline total_item_count mismatch")
        assert_true(int(baseline["fault_or_truth_linked_ref_count"]) == 1, "baseline linked count mismatch")
        assert_true(
            int(panel["incremental_fault_or_truth_linked_ref_count_vs_baseline"]) == 3,
            "panel incremental linked count mismatch",
        )
        assert_true(
            abs(float(panel["incremental_fault_or_truth_linked_ref_rate_vs_baseline"]) - 0.75) < 1e-9,
            "panel incremental linked rate mismatch",
        )
        assert_true(int(narrow["total_item_count"]) == 7, "narrow total_item_count mismatch")
        assert_true(int(narrow["discovery_panel_count"]) == 3, "narrow discovery_panel_count mismatch")
        assert_true(int(cluster["total_item_count"]) == 6, "cluster total_item_count mismatch")
        assert_true(int(cluster["discovery_cluster_count"]) == 2, "cluster discovery_cluster_count mismatch")
        assert_true(
            int(cluster["incremental_fault_or_truth_linked_ref_count_vs_baseline"]) == 2,
            "cluster incremental linked count mismatch",
        )
        assert_true(
            abs(float(cluster["incremental_fault_or_truth_linked_ref_rate_vs_baseline"]) - 1.0) < 1e-9,
            "cluster incremental linked rate mismatch",
        )
        assert_true(
            abs(float(cluster["max_single_site_share"]) - 0.5) < 1e-9,
            "cluster max_single_site_share mismatch",
        )

        assert_true(len(recommendation) == 1, "recommendation should emit exactly one row")
        recommendation_row = recommendation.iloc[0]
        assert_true(
            str(recommendation_row["recommended_policy_name"]) == "baseline_plus_discovery_cluster",
            "synthetic fixture should recommend cluster preview as default workflow",
        )
        assert_true(
            str(recommendation_row["recommended_policy_reason_ko"]).strip() != "",
            "recommendation reason should not be blank",
        )

    for path, (existed_before, digest_before) in official_state.items():
        exists_after = path.exists()
        digest_after = hashlib.sha256(path.read_bytes()).hexdigest() if exists_after else ""
        assert_true(exists_after == existed_before, f"official file existence changed during smoke: {path.name}")
        assert_true(digest_after == digest_before, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
