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
        share / "panel_day_engine_common_cause_breadth_marker_threshold_sweep_v1.csv",
        [
            {
                "rule_name": "final_fault_breadth_threshold|same_day|0.05",
                "rule_family": "final_fault_breadth_threshold",
                "window_name": "same_day",
                "threshold": 0.05,
                "positive_capture_rate": 1.0,
                "contamination_score": 0.0,
            },
            {
                "rule_name": "final_fault_breadth_threshold|plusminus_3d|0.10",
                "rule_family": "final_fault_breadth_threshold",
                "window_name": "plusminus_3d",
                "threshold": 0.10,
                "positive_capture_rate": 1.0,
                "contamination_score": 0.0,
            },
            {
                "rule_name": "any_breadth_threshold|same_day|0.05",
                "rule_family": "any_breadth_threshold",
                "window_name": "same_day",
                "threshold": 0.05,
                "positive_capture_rate": 1.0,
                "contamination_score": 0.0,
            },
            {
                "rule_name": "any_breadth_threshold|plusminus_3d|0.10",
                "rule_family": "any_breadth_threshold",
                "window_name": "plusminus_3d",
                "threshold": 0.10,
                "positive_capture_rate": 1.0,
                "contamination_score": 0.0,
            },
            {
                "rule_name": "any_breadth_threshold|plusminus_7d|0.05",
                "rule_family": "any_breadth_threshold",
                "window_name": "plusminus_7d",
                "threshold": 0.05,
                "positive_capture_rate": 1.0,
                "contamination_score": 0.0,
            },
            {
                "rule_name": "pre_alarm_breadth_threshold|same_day|0.05",
                "rule_family": "pre_alarm_breadth_threshold",
                "window_name": "same_day",
                "threshold": 0.05,
                "positive_capture_rate": 0.5,
                "contamination_score": 0.0,
            },
        ],
        [
            "rule_name",
            "rule_family",
            "window_name",
            "threshold",
            "positive_capture_rate",
            "contamination_score",
        ],
    )

    write_csv(
        share / "panel_day_engine_common_cause_breadth_marker_cases_v1.csv",
        [
            {
                "site": "alpha",
                "panel_id": "common_pos_1",
                "anchor_date": "2025-01-10",
                "truth_case_id": "positive|alpha|common_pos_1|2025-01-10",
            },
            {
                "site": "alpha",
                "panel_id": "common_pos_2",
                "anchor_date": "2025-01-20",
                "truth_case_id": "positive|alpha|common_pos_2|2025-01-20",
            },
        ],
        ["site", "panel_id", "anchor_date", "truth_case_id"],
    )

    write_csv(
        share / "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv",
        [
            {"fault_family_id": "electrical_fault_like_progressive_local", "eval_bucket_v2": "precursor_bearing_detectable_now"},
            {"fault_family_id": "electrical_fault_like_abrupt_local", "eval_bucket_v2": "abrupt_or_no_precursor_now"},
            {"fault_family_id": "group_or_inverter_side_like", "eval_bucket_v2": "non_panel_or_common_cause"},
            {"fault_family_id": "none_visible_or_unconfirmed", "eval_bucket_v2": "abrupt_or_no_precursor_now"},
        ],
        ["fault_family_id", "eval_bucket_v2"],
    )

    write_csv(
        share / "panel_day_engine_precursor_onset_truth_v1.csv",
        [
            {
                "site": "alpha",
                "panel_id": "precursor_neg",
                "fault_start_date": "2025-02-10",
                "vendor_fault_family": "diode_like",
                "temporality_class": "progressive_local_precursor_expected",
            }
        ],
        ["site", "panel_id", "fault_start_date", "vendor_fault_family", "temporality_class"],
    )

    write_csv(
        share / "panel_day_engine_local_precursor_eligibility_cases_v1.csv",
        [
            {
                "site": "alpha",
                "panel_id": "abrupt_neg",
                "strict_trigger_date": "2025-03-10",
                "fault_start_date": "2025-03-10",
                "vendor_fault_family": "diode_like",
                "temporality_class": "abrupt_local_precursor_unexpected",
            }
        ],
        ["site", "panel_id", "strict_trigger_date", "fault_start_date", "vendor_fault_family", "temporality_class"],
    )

    write_csv(
        share / "panel_date_reaudit_working.csv",
        [],
        ["site", "panel_id", "strict_trigger_date", "vendor_fault_family"],
    )

    dates = pd.date_range("2025-01-05", "2025-03-12", freq="D")
    core_rows: list[dict[str, object]] = []
    gate_rows: list[dict[str, object]] = []

    for day in dates:
        date_text = day.strftime("%Y-%m-%d")
        for panel_idx in range(25):
            panel_id = f"p{panel_idx:02d}"
            final_fault = 0
            pre_alarm = 0
            ews_warning = 0

            if date_text in {"2025-01-10", "2025-01-20"} and panel_idx < 3:
                final_fault = 1
            if date_text == "2025-01-05" and panel_idx < 2:
                pre_alarm = 1
            if date_text == "2025-02-10" and panel_idx == 0:
                ews_warning = 1
            if date_text == "2025-03-10" and panel_idx == 0:
                final_fault = 1

            core_rows.append({"panel_id": panel_id, "date": date_text, "final_fault": final_fault})
            gate_rows.append({"site": "alpha", "panel_id": panel_id, "date": date_text, "ews_warning": ews_warning, "pre_alarm": pre_alarm})

    write_csv(
        tmp_root / "data" / "alpha" / "out" / "panel_day_core.csv",
        core_rows,
        ["panel_id", "date", "final_fault"],
    )
    write_csv(
        tmp_root / "data" / "alpha" / "out" / "ae_simple_local_precursor_gate_daily.csv",
        gate_rows,
        ["site", "panel_id", "date", "ews_warning", "pre_alarm"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_common_cause_breadth_retrofit_audit_v1.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_common_cause_breadth_retrofit_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_common_cause_breadth_retrofit_prevalence_v1.csv",
        repo_root / "_share" / "panel_day_engine_common_cause_breadth_retrofit_recommendation_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_common_cause_breadth_retrofit_audit_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_common_cause_breadth_retrofit_audit_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="common_cause_breadth_retrofit_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        summary_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_common_cause_breadth_retrofit_summary_v1.csv", encoding="utf-8-sig")
        prevalence_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_common_cause_breadth_retrofit_prevalence_v1.csv", encoding="utf-8-sig")
        recommendation_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_common_cause_breadth_retrofit_recommendation_v1.csv", encoding="utf-8-sig")

        assert_true("pre_alarm_breadth_threshold|same_day|0.05" not in set(summary_df["rule_name"]), "candidate filtering should drop non-tied rows")

        final_same_day = summary_df.loc[summary_df["rule_name"].eq("final_fault_breadth_threshold|same_day|0.05")].iloc[0]
        final_pm3 = summary_df.loc[summary_df["rule_name"].eq("final_fault_breadth_threshold|plusminus_3d|0.10")].iloc[0]
        any_same_day = summary_df.loc[summary_df["rule_name"].eq("any_breadth_threshold|same_day|0.05")].iloc[0]

        assert_true(float(final_same_day["positive_capture_rate"]) == 1.0, "final same-day candidate should keep perfect positive capture")
        assert_true(float(final_same_day["contamination_score"]) == 0.0, "final same-day candidate should keep zero contamination")
        assert_true(float(any_same_day["triggered_site_day_rate"]) > float(final_same_day["triggered_site_day_rate"]), "any-breadth same-day should be more prevalent than final-fault same-day")
        assert_true(float(final_pm3["triggered_site_day_rate"]) > float(final_same_day["triggered_site_day_rate"]), "plusminus_3d candidate should be broader than same-day candidate")

        recommended_rows = summary_df.loc[summary_df["recommended_rule_flag"].eq(1)]
        assert_true(len(recommended_rows) == 1, "exactly one candidate should be recommended")
        assert_true(
            recommended_rows.iloc[0]["rule_name"] == "final_fault_breadth_threshold|same_day|0.05",
            "recommendation heuristic should prefer the least-broad viable candidate",
        )

        prevalence_row = prevalence_df.loc[
            (prevalence_df["rule_name"].eq("final_fault_breadth_threshold|same_day|0.05"))
            & (prevalence_df["site"].eq("alpha"))
        ].iloc[0]
        assert_true(int(prevalence_row["triggered_site_day_count"]) == 2, "same-day final-fault prevalence should count only the two positive anchor days")

        recommendation_row = recommendation_df.iloc[0]
        assert_true(
            recommendation_row["recommended_rule_name"] == "final_fault_breadth_threshold|same_day|0.05",
            "recommendation output should match summary recommendation",
        )

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
