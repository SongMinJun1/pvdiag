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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture_root(tmp_root: Path) -> None:
    write_text(tmp_root / "pv_ae" / "panel_day_engine.py", "# synthetic panel_day_engine core\n")
    share = tmp_root / "_share"

    write_csv(
        share / "panel_day_engine_non_precursor_performance_cases_v1.csv",
        [
            {
                "eval_bucket_v2": "non_panel_or_common_cause",
                "site": "alpha",
                "panel_id": "current_only_case",
                "anchor_date": "2025-01-10",
                "truth_case_id": "np|alpha|current_only_case|2025-01-10",
            },
            {
                "eval_bucket_v2": "non_panel_or_common_cause",
                "site": "alpha",
                "panel_id": "breadth_only_case",
                "anchor_date": "2025-01-20",
                "truth_case_id": "np|alpha|breadth_only_case|2025-01-20",
            },
            {
                "eval_bucket_v2": "non_panel_or_common_cause",
                "site": "alpha",
                "panel_id": "both_case",
                "anchor_date": "2025-01-30",
                "truth_case_id": "np|alpha|both_case|2025-01-30",
            },
            {
                "eval_bucket_v2": "non_panel_or_common_cause",
                "site": "alpha",
                "panel_id": "neither_case",
                "anchor_date": "2025-02-10",
                "truth_case_id": "np|alpha|neither_case|2025-02-10",
            },
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "site": "alpha",
                "panel_id": "abrupt_neg_case",
                "anchor_date": "2025-03-10",
                "truth_case_id": "np|alpha|abrupt_neg_case|2025-03-10",
            },
        ],
        ["eval_bucket_v2", "site", "panel_id", "anchor_date", "truth_case_id"],
    )

    write_csv(
        share / "panel_day_engine_non_precursor_performance_summary_v1.csv",
        [
            {
                "eval_bucket_v2": "non_panel_or_common_cause",
                "case_count": 4,
                "common_cause_like_rate": 0.5,
            },
            {
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
                "case_count": 1,
                "common_cause_like_rate": 0.0,
            },
        ],
        ["eval_bucket_v2", "case_count", "common_cause_like_rate"],
    )

    write_csv(
        share / "panel_day_engine_common_cause_breadth_retrofit_recommendation_v1.csv",
        [
            {
                "recommended_rule_name": "final_fault_breadth_threshold|same_day|0.05",
                "recommended_rule_reason_ko": "synthetic",
                "expected_use_ko": "synthetic",
                "caution_ko": "synthetic",
            }
        ],
        ["recommended_rule_name", "recommended_rule_reason_ko", "expected_use_ko", "caution_ko"],
    )

    write_csv(
        share / "panel_day_engine_common_cause_breadth_retrofit_summary_v1.csv",
        [
            {
                "rule_name": "final_fault_breadth_threshold|same_day|0.05",
                "positive_capture_rate": 1.0,
                "contamination_score": 0.0,
                "triggered_site_day_rate": 0.02,
            }
        ],
        ["rule_name", "positive_capture_rate", "contamination_score", "triggered_site_day_rate"],
    )

    write_csv(
        share / "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv",
        [
            {"fault_family_id": "electrical_fault_like_progressive_local", "eval_bucket_v2": "precursor_bearing_detectable_now"},
            {"fault_family_id": "electrical_fault_like_abrupt_local", "eval_bucket_v2": "abrupt_or_no_precursor_now"},
            {"fault_family_id": "group_or_inverter_side_like", "eval_bucket_v2": "non_panel_or_common_cause"},
        ],
        ["fault_family_id", "eval_bucket_v2"],
    )

    write_csv(
        share / "panel_day_engine_precursor_onset_truth_v1.csv",
        [
            {
                "site": "alpha",
                "panel_id": "precursor_neg_case",
                "fault_start_date": "2025-04-10",
                "vendor_fault_family": "diode_like",
                "temporality_class": "progressive_local_precursor_expected",
            }
        ],
        ["site", "panel_id", "fault_start_date", "vendor_fault_family", "temporality_class"],
    )

    panels = ["current_only_case", "breadth_only_case", "both_case", "neither_case", "abrupt_neg_case", "precursor_neg_case"] + [f"extra_{idx}" for idx in range(14)]
    dates = ["2025-01-10", "2025-01-20", "2025-01-30", "2025-02-10", "2025-03-10", "2025-04-10"]
    core_rows: list[dict[str, object]] = []
    gate_rows: list[dict[str, object]] = []
    for date_text in dates:
        for panel in panels:
            group_off_like = 0
            shadow_like = 0
            final_fault = 0
            group_off_date = 0
            ews_warning = 0
            pre_alarm = 0

            if date_text == "2025-01-10" and panel == "current_only_case":
                group_off_like = 1
            if date_text == "2025-01-20" and panel == "extra_0":
                final_fault = 1
            if date_text == "2025-01-30":
                if panel == "both_case":
                    shadow_like = 1
                if panel == "extra_1":
                    final_fault = 1

            core_rows.append(
                {
                    "panel_id": panel,
                    "date": date_text,
                    "final_fault": final_fault,
                    "group_off_like": group_off_like,
                    "shadow_like": shadow_like,
                }
            )
            gate_rows.append(
                {
                    "site": "alpha",
                    "panel_id": panel,
                    "date": date_text,
                    "group_off_date": group_off_date,
                    "ews_warning": ews_warning,
                    "pre_alarm": pre_alarm,
                }
            )

    write_csv(
        tmp_root / "data" / "alpha" / "out" / "panel_day_core.csv",
        core_rows,
        ["panel_id", "date", "final_fault", "group_off_like", "shadow_like"],
    )
    write_csv(
        tmp_root / "data" / "alpha" / "out" / "ae_simple_local_precursor_gate_daily.csv",
        gate_rows,
        ["site", "panel_id", "date", "group_off_date", "ews_warning", "pre_alarm"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_common_cause_descriptive_retrofit_v1.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv",
        repo_root / "_share" / "panel_day_engine_common_cause_descriptive_retrofit_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_common_cause_descriptive_retrofit_comparison_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_common_cause_descriptive_retrofit_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_common_cause_descriptive_retrofit_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="common_cause_descriptive_retrofit_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        cases_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv", encoding="utf-8-sig")
        summary_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_common_cause_descriptive_retrofit_summary_v1.csv", encoding="utf-8-sig")
        comparison_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_common_cause_descriptive_retrofit_comparison_v1.csv", encoding="utf-8-sig")

        mode_map = dict(zip(cases_df["panel_id"], cases_df["explanation_mode_class"]))
        assert_true(mode_map["current_only_case"] == "current_only", "current-only case should map correctly")
        assert_true(mode_map["breadth_only_case"] == "breadth_only", "breadth-only case should map correctly")
        assert_true(mode_map["both_case"] == "both", "both case should map correctly")
        assert_true(mode_map["neither_case"] == "neither", "neither case should map correctly")

        non_panel_row = summary_df.loc[summary_df["eval_bucket_v2"].eq("non_panel_or_common_cause")].iloc[0]
        assert_true(float(non_panel_row["current_marker_explained_rate"]) == 0.5, "current explained rate should be 2/4")
        assert_true(float(non_panel_row["breadth_marker_explained_rate"]) == 0.5, "breadth explained rate should be 2/4")
        assert_true(float(non_panel_row["combined_marker_explained_rate"]) == 0.75, "combined explained rate should be 3/4")
        assert_true(float(non_panel_row["combined_increment_vs_current"]) == 0.25, "combined increment should be computed correctly")

        abrupt_row = summary_df.loc[summary_df["eval_bucket_v2"].eq("abrupt_or_no_precursor_now")].iloc[0]
        precursor_row = summary_df.loc[summary_df["eval_bucket_v2"].eq("precursor_bearing_detectable_now")].iloc[0]
        assert_true(float(abrupt_row["combined_marker_explained_rate"]) == 0.0, "abrupt contamination should remain zero")
        assert_true(float(precursor_row["combined_marker_explained_rate"]) == 0.0, "precursor contamination should remain zero")

        comparison_row = comparison_df.loc[comparison_df["bucket_name"].eq("non_panel_or_common_cause")].iloc[0]
        assert_true(float(comparison_row["combined_increment_vs_current"]) == 0.25, "comparison increment should match summary")

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
