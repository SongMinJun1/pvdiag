#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

CLUSTER_COLS = [
    "site",
    "cluster_id",
    "cluster_start_date",
    "cluster_end_date",
    "panel_count",
    "representative_panel_id",
    "representative_run_start_date",
    "representative_run_end_date",
    "any_future_fault_linked_ref_flag",
    "any_future_truth_linked_ref_flag",
]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def load_builder_module(repo_root: Path):
    module_path = repo_root / "research/prognostics/build_panel_day_engine_operator_secondary_discovery_cluster_delta_v1.py"
    spec = importlib.util.spec_from_file_location("cluster_delta_builder", module_path)
    assert_true(spec is not None and spec.loader is not None, "failed to load cluster delta builder module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=CLUSTER_COLS).to_csv(path, index=False, encoding="utf-8-sig")


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False)


def cluster_row(
    site: str,
    cluster_id: str,
    start_date: str,
    end_date: str,
    *,
    panel_count: int = 1,
    representative_panel_id: str | None = None,
    representative_run_start_date: str | None = None,
    representative_run_end_date: str | None = None,
    fault_flag: int = 0,
    truth_flag: int = 0,
) -> dict[str, object]:
    rep_panel = representative_panel_id or f"{cluster_id}.panel"
    rep_start = representative_run_start_date or start_date
    rep_end = representative_run_end_date or end_date
    return {
        "site": site,
        "cluster_id": cluster_id,
        "cluster_start_date": start_date,
        "cluster_end_date": end_date,
        "panel_count": panel_count,
        "representative_panel_id": rep_panel,
        "representative_run_start_date": rep_start,
        "representative_run_end_date": rep_end,
        "any_future_fault_linked_ref_flag": fault_flag,
        "any_future_truth_linked_ref_flag": truth_flag,
    }


def frame_as_text(df: pd.DataFrame) -> pd.DataFrame:
    return df.fillna("").astype(str).reset_index(drop=True)


def run_build(repo_root: Path, root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    result = run(
        [
            sys.executable,
            "research/prognostics/build_panel_day_engine_operator_secondary_discovery_cluster_delta_v1.py",
            "--root",
            str(root),
        ],
        repo_root,
    )
    assert_true(result.returncode == 0, result.stderr)
    share_dir = root / "_share"
    delta = read_csv(share_dir / "panel_day_engine_operator_secondary_discovery_cluster_delta_v1.csv")
    summary = read_csv(share_dir / "panel_day_engine_operator_secondary_discovery_cluster_delta_summary_v1.csv")
    return delta, summary


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder_mod = load_builder_module(repo_root)

    official_paths = [
        repo_root / "_share" / "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1_previous.csv",
        repo_root / "_share" / "panel_day_engine_operator_secondary_discovery_cluster_delta_v1.csv",
        repo_root / "_share" / "panel_day_engine_operator_secondary_discovery_cluster_delta_summary_v1.csv",
    ]
    official_state = {
        path: (
            path.exists(),
            hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "",
        )
        for path in official_paths
    }

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_operator_secondary_discovery_cluster_delta_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_operator_secondary_discovery_cluster_delta_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="cluster_delta_bootstrap_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        share_dir = tmp_root / "_share"
        current_path = share_dir / "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.csv"
        previous_path = share_dir / "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1_previous.csv"

        current_rows = [
            cluster_row("alpha", "alpha_cluster_001", "2025-01-01", "2025-01-03", panel_count=2, fault_flag=1),
            cluster_row("beta", "beta_cluster_001", "2025-02-10", "2025-02-10", panel_count=1, truth_flag=1),
        ]
        write_csv(current_path, current_rows)

        expected_delta, expected_summary = builder_mod.build_outputs(tmp_root)
        delta, summary = run_build(repo_root, tmp_root)

        assert_true(not previous_path.exists() or previous_path.read_bytes() == current_path.read_bytes(), "bootstrap should write current snapshot as previous after comparison")
        assert_true(len(delta) == 2, "bootstrap run should emit all current clusters as delta rows")
        assert_true(set(delta["delta_class"]) == {"new_cluster"}, "bootstrap delta rows should all be new_cluster")

        overall = summary.loc[summary["record_type"].eq("overall")].iloc[0]
        assert_true(int(overall["current_cluster_count"]) == 2, "bootstrap current cluster count mismatch")
        assert_true(int(overall["previous_cluster_count"]) == 0, "bootstrap previous cluster count mismatch")
        assert_true(int(overall["changed_cluster_count"]) == 2, "bootstrap changed cluster count mismatch")
        assert_true(int(overall["new_cluster_count"]) == 2, "bootstrap new cluster count mismatch")
        assert_true(int(overall["dropped_cluster_count"]) == 0, "bootstrap dropped cluster count mismatch")
        assert_true(previous_path.exists(), "bootstrap should still write previous snapshot")
        assert_true(previous_path.read_bytes() == current_path.read_bytes(), "bootstrap previous snapshot should copy current")
        assert_true(
            frame_as_text(delta).equals(frame_as_text(expected_delta)),
            "bootstrap delta output should match build_outputs before snapshot overwrite",
        )
        assert_true(
            frame_as_text(summary).equals(frame_as_text(expected_summary)),
            "bootstrap summary output should match build_outputs before snapshot overwrite",
        )

    with tempfile.TemporaryDirectory(prefix="cluster_delta_compare_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        share_dir = tmp_root / "_share"
        current_path = share_dir / "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.csv"
        previous_path = share_dir / "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1_previous.csv"

        previous_rows = [
            cluster_row("alpha", "alpha_prev_rep", "2025-01-01", "2025-01-05", panel_count=2, representative_panel_id="alpha.prev.rep"),
            cluster_row("alpha", "alpha_prev_same", "2025-01-10", "2025-01-12", panel_count=1, representative_panel_id="alpha.same"),
            cluster_row("alpha", "alpha_prev_drop", "2025-01-20", "2025-01-22", panel_count=1, representative_panel_id="alpha.drop"),
            cluster_row("beta", "beta_prev_link", "2025-03-01", "2025-03-03", panel_count=1, representative_panel_id="beta.link"),
            cluster_row("beta", "beta_prev_count", "2025-04-01", "2025-04-03", panel_count=2, representative_panel_id="beta.count"),
            cluster_row("beta", "beta_prev_span", "2025-05-01", "2025-05-03", panel_count=1, representative_panel_id="beta.span"),
            cluster_row("gamma", "gamma_prev_a", "2025-06-01", "2025-06-05", panel_count=1, representative_panel_id="gamma.a"),
            cluster_row("gamma", "gamma_prev_b", "2025-06-05", "2025-06-10", panel_count=1, representative_panel_id="gamma.b"),
        ]
        current_rows = [
            cluster_row("alpha", "alpha_cur_rep", "2025-01-02", "2025-01-05", panel_count=2, representative_panel_id="alpha.cur.rep"),
            cluster_row("alpha", "alpha_cur_same", "2025-01-10", "2025-01-12", panel_count=1, representative_panel_id="alpha.same"),
            cluster_row("alpha", "alpha_cur_new", "2025-02-05", "2025-02-06", panel_count=1, representative_panel_id="alpha.new"),
            cluster_row(
                "beta",
                "beta_cur_link",
                "2025-03-02",
                "2025-03-04",
                panel_count=1,
                representative_panel_id="beta.link",
                representative_run_start_date="2025-03-01",
                representative_run_end_date="2025-03-03",
                fault_flag=1,
            ),
            cluster_row("beta", "beta_cur_count", "2025-04-01", "2025-04-03", panel_count=3, representative_panel_id="beta.count"),
            cluster_row(
                "beta",
                "beta_cur_span",
                "2025-05-02",
                "2025-05-04",
                panel_count=1,
                representative_panel_id="beta.span",
                representative_run_start_date="2025-05-01",
                representative_run_end_date="2025-05-03",
            ),
            cluster_row(
                "gamma",
                "gamma_cur_main",
                "2025-06-05",
                "2025-06-10",
                panel_count=1,
                representative_panel_id="gamma.b",
                representative_run_start_date="2025-06-05",
                representative_run_end_date="2025-06-10",
            ),
        ]
        write_csv(previous_path, previous_rows)
        write_csv(current_path, current_rows)

        current_snapshot = builder_mod.prepare_cluster_snapshot(current_path, required_current=True)
        previous_snapshot = builder_mod.prepare_cluster_snapshot(previous_path, required_current=False)
        matches = builder_mod.build_site_matches(current_snapshot, previous_snapshot)
        gamma_match = matches.loc[matches["current_cluster_id"].eq("gamma_cur_main")].iloc[0]
        assert_true(str(gamma_match["previous_cluster_id"]) == "gamma_prev_b", "overlap matching should greedily pair gamma_cur_main with gamma_prev_b")
        assert_true(int(gamma_match["overlap_days"]) == 6, "gamma overlap should be 6 days")

        expected_delta, expected_summary = builder_mod.build_outputs(tmp_root)
        delta, summary = run_build(repo_root, tmp_root)
        updated_previous = read_csv(previous_path)
        current_loaded = read_csv(current_path)

        expected_classes = {
            "alpha_cur_rep": "representative_changed",
            "alpha_cur_new": "new_cluster",
            "alpha_prev_drop": "dropped_cluster",
            "beta_cur_link": "linked_ref_changed",
            "beta_cur_count": "panel_count_changed",
            "beta_cur_span": "cluster_span_changed",
            "gamma_prev_a": "dropped_cluster",
        }
        actual_classes: dict[str, str] = {}
        for _, row in delta.iterrows():
            entity_id = row["current_cluster_id"] or row["previous_cluster_id"]
            actual_classes[str(entity_id)] = str(row["delta_class"])
        assert_true(actual_classes == expected_classes, "delta classification should cover new/dropped/representative/linked/panel_count/span changes")
        assert_true("alpha_cur_same" not in actual_classes, "unchanged matched cluster should not be emitted")
        assert_true("gamma_cur_main" not in actual_classes, "greedily matched unchanged cluster should not be emitted")

        overall = summary.loc[summary["record_type"].eq("overall")].iloc[0]
        assert_true(int(overall["current_cluster_count"]) == 7, "comparison current cluster count mismatch")
        assert_true(int(overall["previous_cluster_count"]) == 8, "comparison previous cluster count mismatch")
        assert_true(int(overall["changed_cluster_count"]) == 7, "comparison changed cluster count mismatch")
        assert_true(int(overall["new_cluster_count"]) == 1, "comparison new cluster count mismatch")
        assert_true(int(overall["dropped_cluster_count"]) == 2, "comparison dropped cluster count mismatch")
        assert_true(int(overall["representative_changed_count"]) == 1, "comparison representative_changed count mismatch")
        assert_true(int(overall["linked_ref_changed_count"]) == 1, "comparison linked_ref_changed count mismatch")
        assert_true(int(overall["panel_count_changed_count"]) == 1, "comparison panel_count_changed count mismatch")
        assert_true(int(overall["cluster_span_changed_count"]) == 1, "comparison cluster_span_changed count mismatch")

        gamma_site = summary.loc[(summary["record_type"].eq("site")) & (summary["site"].eq("gamma"))].iloc[0]
        assert_true(int(gamma_site["changed_cluster_count"]) == 1, "gamma site changed cluster count mismatch")
        assert_true(int(gamma_site["dropped_cluster_count"]) == 1, "gamma site dropped cluster count mismatch")

        linked_row = delta.loc[delta["current_cluster_id"].eq("beta_cur_link")].iloc[0]
        assert_true(int(linked_row["overlap_days"]) == 2, "linked_ref_changed row should preserve overlap days")
        assert_true(
            "retrospective linked reference flag" in str(linked_row["delta_reason_ko"]),
            "linked_ref_changed reason should mention retrospective linked reference",
        )

        assert_true(
            frame_as_text(delta).equals(frame_as_text(expected_delta)),
            "comparison delta output should match build_outputs before snapshot overwrite",
        )
        assert_true(
            frame_as_text(summary).equals(frame_as_text(expected_summary)),
            "comparison summary output should match build_outputs before snapshot overwrite",
        )
        assert_true(
            "alpha_prev_drop" in set(delta["previous_cluster_id"]),
            "dropped cluster should appear in delta before snapshot overwrite",
        )
        assert_true(
            updated_previous.equals(current_loaded),
            "previous snapshot should be overwritten with current only after comparison",
        )

    for path, (existed_before, digest_before) in official_state.items():
        assert_true(path.exists() == existed_before, f"official file existence changed during smoke: {path.name}")
        if existed_before:
            digest_after = hashlib.sha256(path.read_bytes()).hexdigest()
            assert_true(digest_after == digest_before, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
