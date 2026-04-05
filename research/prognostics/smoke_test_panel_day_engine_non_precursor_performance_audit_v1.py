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
        share / "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv",
        [
            {"fault_family_id": "electrical_fault_like_progressive_local", "eval_bucket_v2": "precursor_bearing_detectable_now"},
            {"fault_family_id": "electrical_fault_like_abrupt_local", "eval_bucket_v2": "abrupt_or_no_precursor_now"},
            {"fault_family_id": "electrical_fault_like_unknown_local_temporality", "eval_bucket_v2": "unknown_needs_review"},
            {"fault_family_id": "group_or_inverter_side_like", "eval_bucket_v2": "non_panel_or_common_cause"},
            {"fault_family_id": "none_visible_or_unconfirmed", "eval_bucket_v2": "abrupt_or_no_precursor_now"},
        ],
        ["fault_family_id", "eval_bucket_v2"],
    )

    write_csv(
        share / "panel_day_engine_local_precursor_eligibility_cases_v1.csv",
        [
            {
                "site": "alpha",
                "panel_id": "abrupt_local",
                "strict_trigger_date": "2025-01-10",
                "fault_start_date": "2025-01-10",
                "vendor_fault_family": "diode_like",
                "temporality_class": "abrupt_local_precursor_unexpected",
                "precursor_eligible_flag": 0,
            },
            {
                "site": "alpha",
                "panel_id": "unknown_local",
                "strict_trigger_date": "2025-01-15",
                "fault_start_date": "2025-01-15",
                "vendor_fault_family": "diode_like",
                "temporality_class": "unknown_local_temporality",
                "precursor_eligible_flag": 0,
            },
        ],
        ["site", "panel_id", "strict_trigger_date", "fault_start_date", "vendor_fault_family", "temporality_class", "precursor_eligible_flag"],
    )

    write_csv(
        share / "panel_date_reaudit_working.csv",
        [
            {
                "site": "beta",
                "panel_id": "group_case",
                "strict_trigger_date": "2025-02-10",
                "candidate_validity": "group_side",
                "vendor_fault_family": "group_or_inverter_side_like",
                "vendor_reply_class": "field_confirmed_positive",
            },
            {
                "site": "alpha",
                "panel_id": "none_visible_case",
                "strict_trigger_date": "2025-01-20",
                "candidate_validity": "false_positive",
                "vendor_fault_family": "none_visible",
                "vendor_reply_class": "vendor_rejected",
            },
            {
                "site": "beta",
                "panel_id": "unknown_review",
                "strict_trigger_date": "2025-02-15",
                "candidate_validity": "needs_more_info",
                "vendor_fault_family": "open_or_device_issue_like",
                "vendor_reply_class": "vendor_likely_positive",
            },
        ],
        ["site", "panel_id", "strict_trigger_date", "candidate_validity", "vendor_fault_family", "vendor_reply_class"],
    )

    write_csv(
        tmp_root / "data" / "alpha" / "out" / "panel_day_core.csv",
        [
            {"panel_id": "abrupt_local", "date": "2025-01-09", "confirmed_fault": 1, "critical_fault": 0, "final_fault": 0, "group_off_like": 0, "shadow_like": 0},
            {"panel_id": "abrupt_local", "date": "2025-01-12", "confirmed_fault": 1, "critical_fault": 1, "final_fault": 0, "group_off_like": 0, "shadow_like": 0},
            {"panel_id": "abrupt_local", "date": "2025-01-15", "confirmed_fault": 1, "critical_fault": 1, "final_fault": 1, "group_off_like": 0, "shadow_like": 0},
            {"panel_id": "none_visible_case", "date": "2025-01-21", "confirmed_fault": 0, "critical_fault": 0, "final_fault": 0, "group_off_like": 0, "shadow_like": 0},
            {"panel_id": "unknown_local", "date": "2025-01-15", "confirmed_fault": 0, "critical_fault": 0, "final_fault": 0, "group_off_like": 0, "shadow_like": 0},
        ],
        ["panel_id", "date", "confirmed_fault", "critical_fault", "final_fault", "group_off_like", "shadow_like"],
    )
    write_csv(
        tmp_root / "data" / "alpha" / "out" / "ae_simple_local_precursor_gate_daily.csv",
        [
            {"site": "alpha", "panel_id": "abrupt_local", "date": "2025-01-10", "group_off_date": 0, "ews_warning": 0, "pre_alarm": 0},
            {"site": "alpha", "panel_id": "none_visible_case", "date": "2025-01-20", "group_off_date": 0, "ews_warning": 0, "pre_alarm": 0},
            {"site": "alpha", "panel_id": "unknown_local", "date": "2025-01-15", "group_off_date": 0, "ews_warning": 0, "pre_alarm": 0},
        ],
        ["site", "panel_id", "date", "group_off_date", "ews_warning", "pre_alarm"],
    )

    write_csv(
        tmp_root / "data" / "beta" / "out" / "panel_day_core.csv",
        [
            {"panel_id": "group_case", "date": "2025-02-09", "confirmed_fault": 0, "critical_fault": 0, "final_fault": 0, "group_off_like": 1, "shadow_like": 0},
            {"panel_id": "group_case", "date": "2025-02-10", "confirmed_fault": 0, "critical_fault": 0, "final_fault": 1, "group_off_like": 0, "shadow_like": 1},
            {"panel_id": "unknown_review", "date": "2025-02-15", "confirmed_fault": 0, "critical_fault": 0, "final_fault": 0, "group_off_like": 0, "shadow_like": 0},
        ],
        ["panel_id", "date", "confirmed_fault", "critical_fault", "final_fault", "group_off_like", "shadow_like"],
    )
    write_csv(
        tmp_root / "data" / "beta" / "out" / "ae_simple_local_precursor_gate_daily.csv",
        [
            {"site": "beta", "panel_id": "group_case", "date": "2025-02-10", "group_off_date": 1, "ews_warning": 1, "pre_alarm": 0},
            {"site": "beta", "panel_id": "unknown_review", "date": "2025-02-15", "group_off_date": 0, "ews_warning": 0, "pre_alarm": 0},
        ],
        ["site", "panel_id", "date", "group_off_date", "ews_warning", "pre_alarm"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_non_precursor_performance_audit_v1.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_non_precursor_performance_cases_v1.csv",
        repo_root / "_share" / "panel_day_engine_non_precursor_performance_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_non_precursor_bucket_comparison_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_non_precursor_performance_audit_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_non_precursor_performance_audit_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="non_precursor_performance_audit_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        cases_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_non_precursor_performance_cases_v1.csv", encoding="utf-8-sig")
        summary_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_non_precursor_performance_summary_v1.csv", encoding="utf-8-sig")
        comparison_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_non_precursor_bucket_comparison_v1.csv", encoding="utf-8-sig")

        abrupt_case = cases_df.loc[cases_df["panel_id"].eq("abrupt_local")].iloc[0]
        assert_true(int(abrupt_case["confirmed_fault_hit_by_anchor_flag"]) == 1, "confirmed fault before anchor should count as by-anchor hit")
        assert_true(int(abrupt_case["critical_fault_hit_within_3d_after_flag"]) == 1, "critical fault at +2d should count within 3d after")
        assert_true(int(abrupt_case["final_fault_hit_within_7d_after_flag"]) == 1, "final fault at +5d should count within 7d after")
        assert_true(int(abrupt_case["final_fault_hit_within_3d_after_flag"]) == 0, "final fault at +5d should not count within 3d after")
        assert_true(int(float(abrupt_case["final_fault_lead_days_to_fault_start"])) == -5, "late final fault should yield negative lead days")

        group_case = cases_df.loc[cases_df["panel_id"].eq("group_case")].iloc[0]
        assert_true(int(group_case["any_group_off_like_flag"]) == 1, "group case should set group_off_like flag")
        assert_true(int(group_case["any_shadow_like_flag"]) == 1, "group case should set shadow_like flag")
        assert_true(int(group_case["any_common_cause_like_flag"]) == 1, "group case should set common_cause_like flag")
        assert_true(int(group_case["any_local_precursor_alert_flag"]) == 1, "group case should capture local precursor alert contamination")
        assert_true(int(group_case["any_final_fault_flag"]) == 1, "group case should capture final_fault in window")

        unknown_row = cases_df.loc[cases_df["eval_bucket_v2"].eq("unknown_needs_review")].iloc[0]
        assert_true(
            isinstance(unknown_row["descriptive_only_reason_ko"], str) and unknown_row["descriptive_only_reason_ko"] != "",
            "unknown bucket should stay descriptive only",
        )

        summary_map = {row["eval_bucket_v2"]: row for row in summary_df.to_dict(orient="records")}
        abrupt_summary = summary_map["abrupt_or_no_precursor_now"]
        assert_true(int(abrupt_summary["case_count"]) == 2, "abrupt bucket should include abrupt local + none_visible synthetic cases")
        assert_true(float(abrupt_summary["final_fault_hit_within_7d_after_rate"]) == 0.5, "abrupt summary 7d-after rate should be correct")

        non_panel_summary = summary_map["non_panel_or_common_cause"]
        assert_true(float(non_panel_summary["common_cause_like_rate"]) == 1.0, "non-panel common_cause_like_rate should be correct")
        assert_true(float(non_panel_summary["local_precursor_alert_contamination_rate"]) == 1.0, "contamination rate should be correct")

        unknown_summary = summary_map["unknown_needs_review"]
        assert_true(unknown_summary["note_ko"] == "descriptive_only", "unknown summary should stay descriptive only")

        assert_true(len(comparison_df) == 3, "comparison output should include three bucket rows")

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
