#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import py_compile
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


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert_true(spec is not None and spec.loader is not None, f"failed to load module: {path.name}")
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_fixture(root: Path) -> None:
    share = root / "_share"
    share.mkdir(parents=True, exist_ok=True)

    write_csv(
        share / "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv",
        [
            {"fault_family_id": "fam_precursor", "eval_bucket_v2": "precursor_bearing_detectable_now"},
            {"fault_family_id": "fam_abrupt", "eval_bucket_v2": "abrupt_or_no_precursor_now"},
            {"fault_family_id": "fam_nonpanel", "eval_bucket_v2": "non_panel_or_common_cause"},
            {"fault_family_id": "fam_unknown", "eval_bucket_v2": "unknown_needs_review"},
        ],
        ["fault_family_id", "eval_bucket_v2"],
    )
    write_csv(
        share / "panel_day_engine_precursor_onset_truth_v1.csv",
        [
            {"site": "alpha", "panel_id": "P1", "fault_start_date": "2026-01-31", "preferred_precursor_onset_date": "2026-01-10"},
            {"site": "alpha", "panel_id": "P2", "fault_start_date": "2026-02-10", "preferred_precursor_onset_date": "2026-02-01"},
        ],
        ["site", "panel_id", "fault_start_date", "preferred_precursor_onset_date"],
    )
    write_csv(
        share / "panel_day_engine_precursor_onset_summary_v1.csv",
        [
            {"summary_type": "onset_marker", "marker_name": "first_cond_evt", "case_count": 2, "available_case_count": 2},
            {"summary_type": "onset_marker", "marker_name": "first_cond_evt_corroborated", "case_count": 2, "available_case_count": 1},
            {"summary_type": "onset_marker", "marker_name": "first_signalcount2", "case_count": 2, "available_case_count": 1},
            {"summary_type": "onset_marker", "marker_name": "first_pre_ews", "case_count": 2, "available_case_count": 1},
            {"summary_type": "onset_marker", "marker_name": "first_ews_warning", "case_count": 2, "available_case_count": 1},
            {"summary_type": "onset_marker", "marker_name": "first_pre_alarm", "case_count": 2, "available_case_count": 0},
        ],
        ["summary_type", "marker_name", "case_count", "available_case_count"],
    )
    write_csv(
        share / "panel_day_engine_precursor_performance_cases_v1.csv",
        [
            {
                "site": "alpha",
                "panel_id": "P1",
                "fault_start_date": "2026-01-31",
                "first_cond_evt_available_flag": 1,
                "first_cond_evt_corroborated_available_flag": 1,
                "first_signalcount2_available_flag": 1,
                "first_pre_ews_available_flag": 0,
                "first_ews_warning_available_flag": 0,
                "first_pre_alarm_available_flag": 0,
            },
            {
                "site": "alpha",
                "panel_id": "P2",
                "fault_start_date": "2026-02-10",
                "first_cond_evt_available_flag": 0,
                "first_cond_evt_corroborated_available_flag": 0,
                "first_signalcount2_available_flag": 0,
                "first_pre_ews_available_flag": 1,
                "first_ews_warning_available_flag": 1,
                "first_pre_alarm_available_flag": 0,
            },
        ],
        [
            "site",
            "panel_id",
            "fault_start_date",
            "first_cond_evt_available_flag",
            "first_cond_evt_corroborated_available_flag",
            "first_signalcount2_available_flag",
            "first_pre_ews_available_flag",
            "first_ews_warning_available_flag",
            "first_pre_alarm_available_flag",
        ],
    )
    write_csv(
        share / "panel_day_engine_non_precursor_performance_cases_v1.csv",
        [
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "site": "alpha",
                "panel_id": "A1",
                "anchor_date": "2026-03-10",
                "truth_case_id": "A1",
                "final_fault_hit_by_anchor_flag": 1,
                "final_fault_hit_within_3d_after_flag": 0,
                "final_fault_hit_within_7d_after_flag": 0,
                "critical_fault_hit_within_7d_after_flag": 1,
                "confirmed_fault_hit_within_7d_after_flag": 0,
            },
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "site": "alpha",
                "panel_id": "A2",
                "anchor_date": "2026-03-20",
                "truth_case_id": "A2",
                "final_fault_hit_by_anchor_flag": 0,
                "final_fault_hit_within_3d_after_flag": 0,
                "final_fault_hit_within_7d_after_flag": 1,
                "critical_fault_hit_within_7d_after_flag": 0,
                "confirmed_fault_hit_within_7d_after_flag": 0,
            },
            {
                "eval_bucket_v2": "non_panel_or_common_cause",
                "site": "alpha",
                "panel_id": "N1",
                "anchor_date": "2026-03-05",
                "truth_case_id": "N1",
                "final_fault_hit_by_anchor_flag": 0,
                "final_fault_hit_within_3d_after_flag": 0,
                "final_fault_hit_within_7d_after_flag": 0,
                "critical_fault_hit_within_7d_after_flag": 0,
                "confirmed_fault_hit_within_7d_after_flag": 0,
            },
            {
                "eval_bucket_v2": "non_panel_or_common_cause",
                "site": "alpha",
                "panel_id": "N2",
                "anchor_date": "2026-03-08",
                "truth_case_id": "N2",
                "final_fault_hit_by_anchor_flag": 0,
                "final_fault_hit_within_3d_after_flag": 0,
                "final_fault_hit_within_7d_after_flag": 0,
                "critical_fault_hit_within_7d_after_flag": 0,
                "confirmed_fault_hit_within_7d_after_flag": 0,
            },
        ],
        [
            "eval_bucket_v2",
            "site",
            "panel_id",
            "anchor_date",
            "truth_case_id",
            "final_fault_hit_by_anchor_flag",
            "final_fault_hit_within_3d_after_flag",
            "final_fault_hit_within_7d_after_flag",
            "critical_fault_hit_within_7d_after_flag",
            "confirmed_fault_hit_within_7d_after_flag",
        ],
    )
    write_csv(
        share / "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv",
        [
            {"eval_bucket_v2": "non_panel_or_common_cause", "site": "alpha", "panel_id": "N1", "current_marker_only_flag": 1, "breadth_marker_only_flag": 0, "combined_marker_flag": 1},
            {"eval_bucket_v2": "non_panel_or_common_cause", "site": "alpha", "panel_id": "N2", "current_marker_only_flag": 0, "breadth_marker_only_flag": 1, "combined_marker_flag": 1},
            {"eval_bucket_v2": "abrupt_or_no_precursor_now", "site": "alpha", "panel_id": "A1", "current_marker_only_flag": 0, "breadth_marker_only_flag": 0, "combined_marker_flag": 1},
            {"eval_bucket_v2": "abrupt_or_no_precursor_now", "site": "alpha", "panel_id": "A2", "current_marker_only_flag": 0, "breadth_marker_only_flag": 0, "combined_marker_flag": 0},
            {"eval_bucket_v2": "precursor_bearing_detectable_now", "site": "alpha", "panel_id": "P1", "current_marker_only_flag": 0, "breadth_marker_only_flag": 0, "combined_marker_flag": 0},
            {"eval_bucket_v2": "precursor_bearing_detectable_now", "site": "alpha", "panel_id": "P2", "current_marker_only_flag": 1, "breadth_marker_only_flag": 0, "combined_marker_flag": 1},
        ],
        [
            "eval_bucket_v2",
            "site",
            "panel_id",
            "current_marker_only_flag",
            "breadth_marker_only_flag",
            "combined_marker_flag",
        ],
    )
    write_csv(
        share / "panel_day_engine_operator_attention_now_v1.csv",
        [
            {"attention_class": "queue_run", "site": "alpha", "panel_id": "B1", "attention_any_future_fault_linked_ref_flag": 1, "attention_any_future_truth_linked_ref_flag": 0},
            {"attention_class": "watch_now_panel", "site": "alpha", "panel_id": "B2", "attention_any_future_fault_linked_ref_flag": 0, "attention_any_future_truth_linked_ref_flag": 0},
        ],
        ["attention_class", "site", "panel_id", "attention_any_future_fault_linked_ref_flag", "attention_any_future_truth_linked_ref_flag"],
    )
    write_csv(
        share / "panel_day_engine_operator_attention_plus_discovery_preview_v1.csv",
        [
            {"preview_attention_class": "queue_run", "site": "alpha", "panel_id": "B1", "attention_any_future_fault_linked_ref_flag": 1, "attention_any_future_truth_linked_ref_flag": 0},
            {"preview_attention_class": "watch_now_panel", "site": "alpha", "panel_id": "B2", "attention_any_future_fault_linked_ref_flag": 0, "attention_any_future_truth_linked_ref_flag": 0},
            {"preview_attention_class": "secondary_value_panel", "site": "alpha", "panel_id": "D1", "attention_any_future_fault_linked_ref_flag": 1, "attention_any_future_truth_linked_ref_flag": 0},
            {"preview_attention_class": "secondary_value_panel", "site": "alpha", "panel_id": "D2", "attention_any_future_fault_linked_ref_flag": 0, "attention_any_future_truth_linked_ref_flag": 0},
        ],
        ["preview_attention_class", "site", "panel_id", "attention_any_future_fault_linked_ref_flag", "attention_any_future_truth_linked_ref_flag"],
    )
    write_csv(
        share / "panel_day_engine_operator_attention_plus_discovery_preview_narrow_v1.csv",
        [
            {"preview_attention_class": "queue_run", "site": "alpha", "panel_id": "B1", "attention_any_future_fault_linked_ref_flag": 1, "attention_any_future_truth_linked_ref_flag": 0},
            {"preview_attention_class": "watch_now_panel", "site": "alpha", "panel_id": "B2", "attention_any_future_fault_linked_ref_flag": 0, "attention_any_future_truth_linked_ref_flag": 0},
            {"preview_attention_class": "secondary_value_panel", "site": "alpha", "panel_id": "D1", "attention_any_future_fault_linked_ref_flag": 1, "attention_any_future_truth_linked_ref_flag": 0},
        ],
        ["preview_attention_class", "site", "panel_id", "attention_any_future_fault_linked_ref_flag", "attention_any_future_truth_linked_ref_flag"],
    )
    write_csv(
        share / "panel_day_engine_operator_attention_plus_discovery_cluster_preview_v1.csv",
        [
            {"preview_attention_class": "queue_run", "site": "alpha", "display_entity_id": "B1", "linked_ref_flag": 1, "truth_ref_flag": 0},
            {"preview_attention_class": "watch_now_panel", "site": "alpha", "display_entity_id": "B2", "linked_ref_flag": 0, "truth_ref_flag": 0},
            {"preview_attention_class": "secondary_value_cluster", "site": "alpha", "display_entity_id": "alpha_cluster_001", "linked_ref_flag": 1, "truth_ref_flag": 0},
        ],
        ["preview_attention_class", "site", "display_entity_id", "linked_ref_flag", "truth_ref_flag"],
    )
    write_csv(
        share / "panel_day_engine_operator_workflow_default_v1.csv",
        [
            {"preview_attention_class": "queue_run", "site": "alpha", "display_entity_id": "B1", "linked_ref_flag": 1, "truth_ref_flag": 0},
            {"preview_attention_class": "watch_now_panel", "site": "alpha", "display_entity_id": "B2", "linked_ref_flag": 0, "truth_ref_flag": 0},
            {"preview_attention_class": "secondary_value_cluster", "site": "alpha", "display_entity_id": "alpha_cluster_001", "linked_ref_flag": 1, "truth_ref_flag": 0},
        ],
        ["preview_attention_class", "site", "display_entity_id", "linked_ref_flag", "truth_ref_flag"],
    )
    write_csv(
        share / "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.csv",
        [
            {"site": "alpha", "cluster_id": "alpha_cluster_001", "panel_ids_csv": "D1,D2"},
        ],
        ["site", "cluster_id", "panel_ids_csv"],
    )
    write_csv(
        share / "panel_date_reaudit_working.csv",
        [{"site": "alpha", "panel_id": "N1", "strict_trigger_date": "2026-03-05"}],
        ["site", "panel_id", "strict_trigger_date"],
    )
    write_csv(
        share / "panel_day_engine_local_precursor_eligibility_cases_v1.csv",
        [
            {"site": "alpha", "panel_id": "P1", "fault_start_date": "2026-01-31"},
            {"site": "alpha", "panel_id": "P2", "fault_start_date": "2026-02-10"},
        ],
        ["site", "panel_id", "fault_start_date"],
    )

    out_dir = root / "data" / "alpha" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        out_dir / "ae_simple_local_precursor_gate_daily.csv",
        [
            {"panel_id": "A1", "date": "2026-03-01", "cond_var": 1, "cond_evt": 1, "cond_dtw": 0, "cond_hs": 0, "pre_ews": 0, "signal_count": 1, "ews_warning": 0, "pre_alarm": 0, "group_off_date": 0},
            {"panel_id": "N1", "date": "2026-02-20", "cond_var": 0, "cond_evt": 0, "cond_dtw": 0, "cond_hs": 0, "pre_ews": 0, "signal_count": 0, "ews_warning": 0, "pre_alarm": 0, "group_off_date": 0},
            {"panel_id": "N2", "date": "2026-03-01", "cond_var": 0, "cond_evt": 0, "cond_dtw": 0, "cond_hs": 0, "pre_ews": 0, "signal_count": 0, "ews_warning": 0, "pre_alarm": 0, "group_off_date": 0},
            {"panel_id": "P1", "date": "2026-01-31", "cond_var": 0, "cond_evt": 0, "cond_dtw": 0, "cond_hs": 0, "pre_ews": 0, "signal_count": 0, "ews_warning": 0, "pre_alarm": 0, "group_off_date": 0},
            {"panel_id": "P2", "date": "2026-02-11", "cond_var": 0, "cond_evt": 0, "cond_dtw": 0, "cond_hs": 0, "pre_ews": 0, "signal_count": 0, "ews_warning": 0, "pre_alarm": 0, "group_off_date": 0},
        ],
        ["panel_id", "date", "cond_var", "cond_evt", "cond_dtw", "cond_hs", "pre_ews", "signal_count", "ews_warning", "pre_alarm", "group_off_date"],
    )
    write_csv(
        out_dir / "panel_day_core.csv",
        [
            {"panel_id": "A1", "date": "2026-03-10", "confirmed_fault": 0, "critical_fault": 1, "final_fault": 1, "group_off_like": 0, "shadow_like": 0},
            {"panel_id": "A2", "date": "2026-03-25", "confirmed_fault": 0, "critical_fault": 0, "final_fault": 1, "group_off_like": 0, "shadow_like": 0},
            {"panel_id": "N1", "date": "2026-03-05", "confirmed_fault": 0, "critical_fault": 0, "final_fault": 0, "group_off_like": 1, "shadow_like": 0},
            {"panel_id": "N2", "date": "2026-03-08", "confirmed_fault": 0, "critical_fault": 0, "final_fault": 0, "group_off_like": 0, "shadow_like": 1},
            {"panel_id": "P1", "date": "2026-01-31", "confirmed_fault": 0, "critical_fault": 0, "final_fault": 0, "group_off_like": 0, "shadow_like": 0},
            {"panel_id": "P2", "date": "2026-02-11", "confirmed_fault": 0, "critical_fault": 0, "final_fault": 1, "group_off_like": 0, "shadow_like": 0},
        ],
        ["panel_id", "date", "confirmed_fault", "critical_fault", "final_fault", "group_off_like", "shadow_like"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder_path = repo_root / "research/prognostics/build_panel_day_engine_project_eval_matrix_v1.py"
    builder_mod = load_module(builder_path, "project_eval_matrix_builder")

    official_paths = [
        repo_root / "_share" / "panel_day_engine_project_eval_matrix_v1.csv",
        repo_root / "_share" / "panel_day_engine_project_eval_matrix_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_project_eval_notes_v1.csv",
    ]
    official_digests_before = {path: file_digest(path) for path in official_paths}

    py_compile.compile(str(builder_path), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="project_eval_matrix_smoke_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture(tmp_root)
        result = run([sys.executable, str(builder_path), "--root", str(tmp_root)], repo_root)
        assert_true(result.returncode == 0, result.stderr or result.stdout)

        matrix = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_eval_matrix_v1.csv",
            encoding="utf-8-sig",
        )
        summary = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_eval_matrix_summary_v1.csv",
            encoding="utf-8-sig",
        )
        notes = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_eval_notes_v1.csv",
            encoding="utf-8-sig",
        )

        assert_true(matrix.columns.tolist() == builder_mod.MATRIX_COLS, "matrix schema mismatch")
        assert_true(summary.columns.tolist() == builder_mod.SUMMARY_COLS, "summary schema mismatch")
        assert_true(notes.columns.tolist() == builder_mod.NOTES_COLS, "notes schema mismatch")

        step1_row = matrix.loc[matrix["eval_scope"].astype(str).eq("step1_taxonomy")].iloc[0]
        assert_true(step1_row["metric_kind"] == "structural_coverage_metric", "step1 metric kind mismatch")
        assert_true(pd.isna(step1_row["precision"]), "step1 precision should be blank")
        assert_true(pd.isna(step1_row["recall"]), "step1 recall should be blank")
        assert_true(pd.isna(step1_row["f1"]), "step1 f1 should be blank")

        step2_row = matrix.loc[
            matrix["eval_scope"].astype(str).eq("step2_onset_truth")
            & matrix["target_name"].astype(str).eq("first_cond_evt")
        ].iloc[0]
        assert_true(step2_row["metric_kind"] == "structural_coverage_metric", "step2 metric kind mismatch")
        assert_true(pd.isna(step2_row["precision"]), "step2 precision should be blank")
        assert_true(int(step2_row["tp"]) == 2, "step2 tp mismatch")
        assert_true(int(step2_row["fn"]) == 0, "step2 fn mismatch")

        step3_row = matrix.loc[
            matrix["eval_scope"].astype(str).eq("step3_precursor_performance")
            & matrix["target_name"].astype(str).eq("first_cond_evt")
        ].iloc[0]
        assert_true(int(step3_row["tp"]) == 1, "step3 tp mismatch")
        assert_true(int(step3_row["fp"]) == 1, "step3 fp mismatch")
        assert_true(int(step3_row["fn"]) == 1, "step3 fn mismatch")
        assert_true(int(step3_row["tn"]) == 3, "step3 tn mismatch")

        step4a_row = matrix.loc[
            matrix["eval_scope"].astype(str).eq("step4_abrupt_no_precursor")
            & matrix["target_name"].astype(str).eq("final_fault_hit_by_anchor")
        ].iloc[0]
        assert_true(int(step4a_row["tp"]) == 1, "step4A tp mismatch")
        assert_true(int(step4a_row["fp"]) == 0, "step4A fp mismatch")
        assert_true(int(step4a_row["fn"]) == 1, "step4A fn mismatch")
        assert_true(int(step4a_row["tn"]) == 4, "step4A tn mismatch")

        step4b_row = matrix.loc[
            matrix["eval_scope"].astype(str).eq("step4_common_cause_routing")
            & matrix["target_name"].astype(str).eq("combined_marker")
        ].iloc[0]
        assert_true(int(step4b_row["tp"]) == 2, "step4B tp mismatch")
        assert_true(int(step4b_row["fp"]) == 2, "step4B fp mismatch")
        assert_true(int(step4b_row["fn"]) == 0, "step4B fn mismatch")
        assert_true(int(step4b_row["tn"]) == 2, "step4B tn mismatch")

        operator_row = matrix.loc[
            matrix["eval_scope"].astype(str).eq("operator_policy_proxy")
            & matrix["target_name"].astype(str).eq("baseline_plus_discovery_narrow")
        ].iloc[0]
        assert_true(int(operator_row["tp"]) == 2, "operator tp mismatch")
        assert_true(int(operator_row["fp"]) == 1, "operator fp mismatch")
        assert_true(int(operator_row["fn"]) == 0, "operator fn mismatch")
        assert_true(int(operator_row["tn"]) == 1, "operator tn mismatch")

        assert_true(not summary.empty, "summary output should not be empty")
        assert_true(len(notes) >= 5, "notes output should contain explanatory rows")

    official_digests_after = {path: file_digest(path) for path in official_paths}
    assert_true(
        official_digests_after == official_digests_before,
        "smoke test must not modify official project eval outputs under repository _share",
    )

    print("smoke_test_panel_day_engine_project_eval_matrix_v1.py: PASS")


if __name__ == "__main__":
    main()
