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
        share / "panel_day_engine_common_cause_routing_gap_cases_v1.csv",
        [
            {
                "site": "alpha",
                "panel_id": "common_pos_1",
                "anchor_date": "2025-01-10",
                "truth_case_id": "gap|alpha|common_pos_1|2025-01-10",
                "vendor_fault_family": "group_or_inverter_side_like",
                "candidate_validity": "group_side",
                "vendor_reply_class": "field_confirmed_positive",
                "any_group_off_like_flag": 0,
                "any_shadow_like_flag": 0,
                "any_common_cause_like_flag": 0,
                "any_local_precursor_alert_flag": 1,
                "any_final_fault_flag": 1,
            },
            {
                "site": "alpha",
                "panel_id": "common_pos_2",
                "anchor_date": "2025-01-20",
                "truth_case_id": "gap|alpha|common_pos_2|2025-01-20",
                "vendor_fault_family": "group_or_inverter_side_like",
                "candidate_validity": "group_side",
                "vendor_reply_class": "field_confirmed_positive",
                "any_group_off_like_flag": 0,
                "any_shadow_like_flag": 0,
                "any_common_cause_like_flag": 0,
                "any_local_precursor_alert_flag": 1,
                "any_final_fault_flag": 0,
            },
        ],
        [
            "site",
            "panel_id",
            "anchor_date",
            "truth_case_id",
            "vendor_fault_family",
            "candidate_validity",
            "vendor_reply_class",
            "any_group_off_like_flag",
            "any_shadow_like_flag",
            "any_common_cause_like_flag",
            "any_local_precursor_alert_flag",
            "any_final_fault_flag",
        ],
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

    core_rows: list[dict[str, object]] = []
    gate_rows: list[dict[str, object]] = []

    for panel_idx in range(20):
        panel = f"p{panel_idx:02d}"
        core_rows.append({"panel_id": panel, "date": "2025-01-10", "final_fault": 1 if panel_idx < 2 else 0})
        gate_rows.append({"panel_id": panel, "date": "2025-01-10", "ews_warning": 0, "pre_alarm": 0})

        core_rows.append({"panel_id": panel, "date": "2025-01-20", "final_fault": 0})
        gate_rows.append({"panel_id": panel, "date": "2025-01-20", "ews_warning": 0, "pre_alarm": 0})

        core_rows.append({"panel_id": panel, "date": "2025-01-21", "final_fault": 0})
        gate_rows.append({"panel_id": panel, "date": "2025-01-21", "ews_warning": 0, "pre_alarm": 1 if panel_idx < 2 else 0})

        core_rows.append({"panel_id": panel, "date": "2025-02-10", "final_fault": 0})
        gate_rows.append({"panel_id": panel, "date": "2025-02-10", "ews_warning": 1 if panel_idx == 0 else 0, "pre_alarm": 0})

        core_rows.append({"panel_id": panel, "date": "2025-03-10", "final_fault": 1 if panel_idx == 0 else 0})
        gate_rows.append({"panel_id": panel, "date": "2025-03-10", "ews_warning": 0, "pre_alarm": 0})

    write_csv(
        tmp_root / "data" / "alpha" / "out" / "panel_day_core.csv",
        core_rows,
        ["panel_id", "date", "final_fault"],
    )
    write_csv(
        tmp_root / "data" / "alpha" / "out" / "ae_simple_local_precursor_gate_daily.csv",
        [{"site": "alpha", **row} for row in gate_rows],
        ["site", "panel_id", "date", "ews_warning", "pre_alarm"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_common_cause_breadth_marker_audit_v1.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_common_cause_breadth_marker_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_common_cause_breadth_marker_cases_v1.csv",
        repo_root / "_share" / "panel_day_engine_common_cause_breadth_marker_threshold_sweep_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_common_cause_breadth_marker_audit_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_common_cause_breadth_marker_audit_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="common_cause_breadth_marker_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        summary_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_common_cause_breadth_marker_summary_v1.csv", encoding="utf-8-sig")
        cases_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_common_cause_breadth_marker_cases_v1.csv", encoding="utf-8-sig")
        sweep_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_common_cause_breadth_marker_threshold_sweep_v1.csv", encoding="utf-8-sig")

        target_row = sweep_df.loc[
            sweep_df["rule_name"].eq("any_breadth_threshold|plusminus_3d|0.10")
        ].iloc[0]
        assert_true(float(target_row["positive_capture_rate"]) == 1.0, "plusminus_3d any>=0.10 should capture both positives")
        assert_true(float(target_row["precursor_negative_trigger_rate"]) == 0.0, "precursor negative contamination should stay zero at threshold 0.10")
        assert_true(float(target_row["abrupt_negative_trigger_rate"]) == 0.0, "abrupt negative contamination should stay zero at threshold 0.10")

        contaminated_row = sweep_df.loc[
            sweep_df["rule_name"].eq("any_breadth_threshold|same_day|0.05")
        ].iloc[0]
        assert_true(float(contaminated_row["precursor_negative_trigger_rate"]) == 1.0, "same_day any>=0.05 should contaminate precursor negative")
        assert_true(float(contaminated_row["abrupt_negative_trigger_rate"]) == 1.0, "same_day any>=0.05 should contaminate abrupt negative")

        recommended_rows = summary_df.loc[summary_df["recommended_rule_flag"].eq(1) & summary_df["summary_type"].eq("candidate_rule")]
        assert_true(len(recommended_rows) == 1, "exactly one candidate rule should be recommended")
        assert_true(
            recommended_rows.iloc[0]["rule_name"] == "any_breadth_threshold|plusminus_3d|0.10",
            "recommended rule should match best capture/contamination tradeoff",
        )

        positive_case = cases_df.loc[cases_df["panel_id"].eq("common_pos_2")].iloc[0]
        assert_true(float(positive_case["max_pre_alarm_panel_fraction_same_day"]) == 0.0, "same-day pre_alarm fraction should be zero for delayed positive")
        assert_true(float(positive_case["max_pre_alarm_panel_fraction_3d"]) == 0.1, "3d pre_alarm fraction should capture delayed breadth")
        assert_true(int(positive_case["best_breadth_rule_hit_flag"]) == 1, "recommended rule should hit delayed positive case")

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
