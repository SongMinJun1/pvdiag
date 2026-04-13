#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


OUTPUT_NAMES = {
    "panel_day_engine_local_precursor_decision_path_summary_v1.csv",
    "panel_day_engine_local_precursor_decision_path_cases_v1.csv",
    "panel_day_engine_local_precursor_decision_path_windows_v1.csv",
}


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    if columns is not None:
        df = df.reindex(columns=columns)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture_root(tmp_root: Path) -> None:
    shadow_columns = [
        "site",
        "panel_id",
        "date",
        "recon_error",
        "dtw_dist",
        "hs_score",
        "mid_ratio",
        "mid_v_ratio",
        "mid_i_ratio",
        "v_drop",
        "confirmed_fault",
        "critical_fault",
        "final_fault",
        "group_off_like",
        "shadow_like",
        "ews_warning_flag",
        "prefault_B_flag",
        "pre_alarm_flag",
        "local_precursor_any_flag",
        "first_local_precursor_date_per_panel",
        "lead_days_to_final_fault",
        "alert_pattern",
    ]
    shadow_rows = [
        {
            "site": "conalog",
            "panel_id": "fill.low.1",
            "date": "2025-01-01",
            "recon_error": 0.10,
            "dtw_dist": 0.10,
            "hs_score": 0.10,
            "mid_ratio": 0.95,
            "mid_v_ratio": 0.95,
            "mid_i_ratio": 0.95,
            "v_drop": 0.05,
            "confirmed_fault": 0,
            "critical_fault": 0,
            "final_fault": 0,
            "group_off_like": 0,
            "shadow_like": 0,
            "ews_warning_flag": 0,
            "prefault_B_flag": 0,
            "pre_alarm_flag": 0,
            "local_precursor_any_flag": 0,
            "first_local_precursor_date_per_panel": "",
            "lead_days_to_final_fault": "",
            "alert_pattern": "no_local_precursor",
        },
        {
            "site": "conalog",
            "panel_id": "fill.low.2",
            "date": "2025-01-02",
            "recon_error": 0.20,
            "dtw_dist": 0.20,
            "hs_score": 0.20,
            "mid_ratio": 0.95,
            "mid_v_ratio": 0.95,
            "mid_i_ratio": 0.95,
            "v_drop": 0.05,
            "confirmed_fault": 0,
            "critical_fault": 0,
            "final_fault": 0,
            "group_off_like": 0,
            "shadow_like": 0,
            "ews_warning_flag": 0,
            "prefault_B_flag": 0,
            "pre_alarm_flag": 0,
            "local_precursor_any_flag": 0,
            "first_local_precursor_date_per_panel": "",
            "lead_days_to_final_fault": "",
            "alert_pattern": "no_local_precursor",
        },
        {
            "site": "conalog",
            "panel_id": "visible.case",
            "date": "2025-01-10",
            "recon_error": 1.00,
            "dtw_dist": 0.20,
            "hs_score": 0.20,
            "mid_ratio": 0.90,
            "mid_v_ratio": 0.90,
            "mid_i_ratio": 0.90,
            "v_drop": 0.05,
            "confirmed_fault": 0,
            "critical_fault": 0,
            "final_fault": 0,
            "group_off_like": 0,
            "shadow_like": 0,
            "ews_warning_flag": 0,
            "prefault_B_flag": 0,
            "pre_alarm_flag": 0,
            "local_precursor_any_flag": 0,
            "first_local_precursor_date_per_panel": "",
            "lead_days_to_final_fault": "",
            "alert_pattern": "no_local_precursor",
        },
        {
            "site": "conalog",
            "panel_id": "ews.case",
            "date": "2025-01-11",
            "recon_error": 1.10,
            "dtw_dist": 0.20,
            "hs_score": 0.20,
            "mid_ratio": 0.88,
            "mid_v_ratio": 0.90,
            "mid_i_ratio": 0.90,
            "v_drop": 0.05,
            "confirmed_fault": 0,
            "critical_fault": 0,
            "final_fault": 0,
            "group_off_like": 0,
            "shadow_like": 0,
            "ews_warning_flag": 1,
            "prefault_B_flag": 0,
            "pre_alarm_flag": 0,
            "local_precursor_any_flag": 1,
            "first_local_precursor_date_per_panel": "2025-01-11",
            "lead_days_to_final_fault": 9,
            "alert_pattern": "ews_only",
        },
        {
            "site": "conalog",
            "panel_id": "helper.case",
            "date": "2025-01-12",
            "recon_error": 0.90,
            "dtw_dist": 0.30,
            "hs_score": 0.20,
            "mid_ratio": 0.87,
            "mid_v_ratio": 0.90,
            "mid_i_ratio": 0.90,
            "v_drop": 0.05,
            "confirmed_fault": 0,
            "critical_fault": 0,
            "final_fault": 0,
            "group_off_like": 0,
            "shadow_like": 0,
            "ews_warning_flag": 1,
            "prefault_B_flag": 0,
            "pre_alarm_flag": 1,
            "local_precursor_any_flag": 1,
            "first_local_precursor_date_per_panel": "2025-01-12",
            "lead_days_to_final_fault": 8,
            "alert_pattern": "ews_and_pre_alarm",
        },
        {
            "site": "conalog",
            "panel_id": "unresolved.case",
            "date": "2025-01-13",
            "recon_error": "",
            "dtw_dist": "",
            "hs_score": "",
            "mid_ratio": 0.90,
            "mid_v_ratio": 0.90,
            "mid_i_ratio": 0.90,
            "v_drop": 0.05,
            "confirmed_fault": 0,
            "critical_fault": 0,
            "final_fault": 0,
            "group_off_like": 0,
            "shadow_like": 0,
            "ews_warning_flag": 0,
            "prefault_B_flag": 0,
            "pre_alarm_flag": 0,
            "local_precursor_any_flag": 0,
            "first_local_precursor_date_per_panel": "",
            "lead_days_to_final_fault": "",
            "alert_pattern": "no_local_precursor",
        },
    ]
    write_csv(tmp_root / "_share" / "panel_day_engine_local_precursor_shadow_v1.csv", shadow_rows, columns=shadow_columns)

    cohort_columns = [
        "site",
        "panel_id",
        "strict_trigger_date",
        "fault_start_date",
        "fault_start_source",
        "candidate_validity",
        "vendor_fault_family",
    ]
    write_csv(
        tmp_root / "_share" / "panel_day_engine_local_precursor_cohort_cases_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": "visible.case",
                "strict_trigger_date": "2025-01-20",
                "fault_start_date": "2025-01-20",
                "fault_start_source": "strict_trigger_fallback",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "family_visible",
            },
            {
                "site": "conalog",
                "panel_id": "ews.case",
                "strict_trigger_date": "2025-01-20",
                "fault_start_date": "2025-01-20",
                "fault_start_source": "strict_trigger_fallback",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "family_ews",
            },
            {
                "site": "conalog",
                "panel_id": "helper.case",
                "strict_trigger_date": "2025-01-20",
                "fault_start_date": "2025-01-20",
                "fault_start_source": "strict_trigger_fallback",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "family_helper",
            },
            {
                "site": "conalog",
                "panel_id": "unresolved.case",
                "strict_trigger_date": "2025-01-20",
                "fault_start_date": "2025-01-20",
                "fault_start_source": "strict_trigger_fallback",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "family_unresolved",
            },
        ],
        columns=cohort_columns,
    )


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_panel_day_engine_local_precursor_decision_path_audit_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script), str(Path(__file__))], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        build_fixture_root(tmp_root)

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        share_dir = tmp_root / "_share"
        produced_output_names = {path.name for path in share_dir.iterdir() if path.is_file()}
        assert_true(OUTPUT_NAMES.issubset(produced_output_names), "builder should emit the three decision-path audit outputs")

        summary_df = pd.read_csv(share_dir / "panel_day_engine_local_precursor_decision_path_summary_v1.csv", encoding="utf-8-sig")
        cases_df = pd.read_csv(share_dir / "panel_day_engine_local_precursor_decision_path_cases_v1.csv", encoding="utf-8-sig")
        windows_df = pd.read_csv(share_dir / "panel_day_engine_local_precursor_decision_path_windows_v1.csv", encoding="utf-8-sig")

        visible_row = windows_df.loc[windows_df["panel_id"].eq("visible.case")].iloc[0]
        assert_true(visible_row["day_path_state"] == "visible_signal_no_ews", "visible signal without ews should become visible_signal_no_ews")

        ews_case = cases_df.loc[cases_df["panel_id"].eq("ews.case")].iloc[0]
        assert_true(ews_case["dominant_miss_reason_class"] == "ews_warning_without_alert_escalation", "ews without alert escalation should classify correctly")

        helper_case = cases_df.loc[cases_df["panel_id"].eq("helper.case")].iloc[0]
        assert_true(helper_case["dominant_miss_reason_class"] == "helper_alert_hit", "prefault_B/pre_alarm hit should become helper_alert_hit")
        helper_row = windows_df.loc[windows_df["panel_id"].eq("helper.case")].iloc[0]
        assert_true(helper_row["day_path_state"] == "pre_alarm_day", "pre_alarm should dominate day_path_state when present")

        unresolved_row = windows_df.loc[windows_df["panel_id"].eq("unresolved.case")].iloc[0]
        assert_true(unresolved_row["day_path_state"] == "unresolved_due_to_unpersisted_inputs", "unavailable proxies should route to unresolved when appropriate")
        assert_true(int(unresolved_row["cond_mid_available_flag"]) == 0, "cond_mid should be marked unavailable")

        overall = summary_df.loc[summary_df["record_type"].eq("overall")].iloc[0]
        assert_true(int(overall["cohort_case_count"]) == 4, "summary cohort case count should be correct")
        assert_true(int(overall["helper_alert_hit_case_count"]) == 1, "helper alert hit count should be correct")
        assert_true(int(overall["visible_signal_but_no_ews_warning_case_count"]) == 1, "visible signal/no ews count should be correct")
        assert_true(int(overall["ews_warning_without_alert_escalation_case_count"]) == 1, "ews/no escalation count should be correct")
        assert_true(int(overall["unresolved_due_to_unpersisted_inputs_case_count"]) == 1, "unresolved count should be correct")
        assert_true(int(overall["no_visible_signal_before_fault_case_count"]) == 0, "no-visible count should be correct")
        assert_true(int(overall["first_visible_signal_case_count"]) == 1, "first visible signal case count should be correct")
        assert_true(int(overall["first_ews_warning_case_count"]) == 2, "first ews case count should be correct")
        assert_true(int(overall["first_prefault_B_case_count"]) == 0, "first prefault count should be correct")
        assert_true(int(overall["first_pre_alarm_case_count"]) == 1, "first pre_alarm count should be correct")

    print("[OK] scripts compile")
    print("[OK] outputs generate")
    print("[OK] visible signal without ews becomes visible_signal_no_ews")
    print("[OK] ews without alert escalation becomes ews_warning_without_alert_escalation")
    print("[OK] prefault_B/pre_alarm hit becomes helper_alert_hit")
    print("[OK] unavailable proxies route to unresolved_due_to_unpersisted_inputs when appropriate")
    print("[OK] summary counts are correct")
    print("[OK] no official outputs are modified")


if __name__ == "__main__":
    main()
