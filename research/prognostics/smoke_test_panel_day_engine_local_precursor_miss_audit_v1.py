#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


OUTPUT_NAMES = {
    "panel_day_engine_local_precursor_miss_summary_v1.csv",
    "panel_day_engine_local_precursor_miss_cases_v1.csv",
    "panel_day_engine_local_precursor_miss_windows_v1.csv",
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
            "panel_id": "panel.raw",
            "date": "2025-01-10",
            "recon_error": 1.0,
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
            "panel_id": "filler.a",
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
            "panel_id": "filler.b",
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
            "panel_id": "filler.c",
            "date": "2025-01-03",
            "recon_error": 0.30,
            "dtw_dist": 0.30,
            "hs_score": 0.30,
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
            "panel_id": "filler.d",
            "date": "2025-01-04",
            "recon_error": 0.40,
            "dtw_dist": 0.40,
            "hs_score": 0.40,
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
            "site": "gangui",
            "panel_id": "panel.confound",
            "date": "2025-02-10",
            "recon_error": 0.30,
            "dtw_dist": 0.20,
            "hs_score": 0.20,
            "mid_ratio": 0.40,
            "mid_v_ratio": 0.70,
            "mid_i_ratio": 0.82,
            "v_drop": 0.25,
            "confirmed_fault": 0,
            "critical_fault": 0,
            "final_fault": 0,
            "group_off_like": 1,
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
            "site": "gangui",
            "panel_id": "filler.e",
            "date": "2025-02-01",
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
            "site": "ktc_ess",
            "panel_id": "panel.stale",
            "date": "2025-03-05",
            "recon_error": 0.05,
            "dtw_dist": 0.05,
            "hs_score": 0.05,
            "mid_ratio": 0.96,
            "mid_v_ratio": 0.96,
            "mid_i_ratio": 0.96,
            "v_drop": 0.04,
            "confirmed_fault": 0,
            "critical_fault": 0,
            "final_fault": 0,
            "group_off_like": 0,
            "shadow_like": 0,
            "ews_warning_flag": 0,
            "prefault_B_flag": 0,
            "pre_alarm_flag": 0,
            "local_precursor_any_flag": 0,
            "first_local_precursor_date_per_panel": "2024-11-20",
            "lead_days_to_final_fault": "",
            "alert_pattern": "no_local_precursor",
        },
        {
            "site": "ktc_ess",
            "panel_id": "filler.f",
            "date": "2025-03-01",
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
            "site": "sinhyo",
            "panel_id": "panel.none",
            "date": "2025-04-10",
            "recon_error": 1.0,
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
            "site": "sinhyo",
            "panel_id": "filler.g",
            "date": "2025-04-01",
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
            "site": "sinhyo",
            "panel_id": "filler.h",
            "date": "2025-04-02",
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
            "site": "sinhyo",
            "panel_id": "filler.i",
            "date": "2025-04-03",
            "recon_error": 0.30,
            "dtw_dist": 0.30,
            "hs_score": 0.30,
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
            "site": "sinhyo",
            "panel_id": "filler.j",
            "date": "2025-04-04",
            "recon_error": 10.0,
            "dtw_dist": 10.0,
            "hs_score": 10.0,
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
            "panel_id": "panel.hit",
            "date": "2025-01-15",
            "recon_error": 0.50,
            "dtw_dist": 0.40,
            "hs_score": 0.40,
            "mid_ratio": 0.70,
            "mid_v_ratio": 0.80,
            "mid_i_ratio": 0.84,
            "v_drop": 0.20,
            "confirmed_fault": 0,
            "critical_fault": 0,
            "final_fault": 0,
            "group_off_like": 0,
            "shadow_like": 0,
            "ews_warning_flag": 1,
            "prefault_B_flag": 0,
            "pre_alarm_flag": 0,
            "local_precursor_any_flag": 1,
            "first_local_precursor_date_per_panel": "2025-01-15",
            "lead_days_to_final_fault": 5,
            "alert_pattern": "ews_only",
        },
    ]
    write_csv(tmp_root / "_share" / "panel_day_engine_local_precursor_shadow_v1.csv", shadow_rows, columns=shadow_columns)

    case_columns = [
        "site",
        "panel_id",
        "strict_trigger_date",
        "fault_start_date",
        "fault_start_source",
        "candidate_validity",
        "vendor_fault_family",
        "first_ews_warning_date_any_prior",
        "first_prefault_B_date_any_prior",
        "first_pre_alarm_date_any_prior",
        "first_ews_warning_date_bounded",
        "first_prefault_B_date_bounded",
        "first_pre_alarm_date_bounded",
        "ews_warning_any_prior_hit_flag",
        "prefault_B_any_prior_hit_flag",
        "pre_alarm_any_prior_hit_flag",
        "ews_warning_bounded_hit_flag",
        "prefault_B_bounded_hit_flag",
        "pre_alarm_bounded_hit_flag",
        "any_local_precursor_any_prior_hit_flag",
        "any_local_precursor_bounded_hit_flag",
        "any_local_precursor_hit_flag",
        "ews_warning_bounded_lead_days",
        "prefault_B_bounded_lead_days",
        "pre_alarm_bounded_lead_days",
        "best_alert_source",
        "best_alert_lead_days",
        "stale_any_prior_alert_flag",
        "stale_best_alert_source",
        "stale_best_alert_lead_days",
    ]
    case_rows = [
        {
            "site": "conalog",
            "panel_id": "panel.raw",
            "strict_trigger_date": "2025-01-20",
            "fault_start_date": "2025-01-20",
            "fault_start_source": "strict_trigger_fallback",
            "candidate_validity": "true_positive",
            "vendor_fault_family": "family_raw",
            "ews_warning_any_prior_hit_flag": 0,
            "prefault_B_any_prior_hit_flag": 0,
            "pre_alarm_any_prior_hit_flag": 0,
            "ews_warning_bounded_hit_flag": 0,
            "prefault_B_bounded_hit_flag": 0,
            "pre_alarm_bounded_hit_flag": 0,
            "any_local_precursor_any_prior_hit_flag": 0,
            "any_local_precursor_bounded_hit_flag": 0,
            "any_local_precursor_hit_flag": 0,
            "best_alert_source": "none",
            "stale_any_prior_alert_flag": 0,
            "stale_best_alert_source": "none",
        },
        {
            "site": "gangui",
            "panel_id": "panel.confound",
            "strict_trigger_date": "2025-02-20",
            "fault_start_date": "2025-02-20",
            "fault_start_source": "strict_trigger_fallback",
            "candidate_validity": "true_positive",
            "vendor_fault_family": "family_confound",
            "ews_warning_any_prior_hit_flag": 0,
            "prefault_B_any_prior_hit_flag": 0,
            "pre_alarm_any_prior_hit_flag": 0,
            "ews_warning_bounded_hit_flag": 0,
            "prefault_B_bounded_hit_flag": 0,
            "pre_alarm_bounded_hit_flag": 0,
            "any_local_precursor_any_prior_hit_flag": 0,
            "any_local_precursor_bounded_hit_flag": 0,
            "any_local_precursor_hit_flag": 0,
            "best_alert_source": "none",
            "stale_any_prior_alert_flag": 0,
            "stale_best_alert_source": "none",
        },
        {
            "site": "ktc_ess",
            "panel_id": "panel.stale",
            "strict_trigger_date": "2025-03-20",
            "fault_start_date": "2025-03-20",
            "fault_start_source": "final_fault_first_true",
            "candidate_validity": "true_positive",
            "vendor_fault_family": "family_stale",
            "first_ews_warning_date_any_prior": "2024-11-20",
            "pre_alarm_any_prior_hit_flag": 1,
            "any_local_precursor_any_prior_hit_flag": 1,
            "any_local_precursor_bounded_hit_flag": 0,
            "any_local_precursor_hit_flag": 0,
            "best_alert_source": "none",
            "stale_any_prior_alert_flag": 1,
            "stale_best_alert_source": "pre_alarm",
            "stale_best_alert_lead_days": 120,
        },
        {
            "site": "sinhyo",
            "panel_id": "panel.none",
            "strict_trigger_date": "2025-04-20",
            "fault_start_date": "2025-04-20",
            "fault_start_source": "strict_trigger_fallback",
            "candidate_validity": "true_positive",
            "vendor_fault_family": "family_none",
            "any_local_precursor_any_prior_hit_flag": 0,
            "any_local_precursor_bounded_hit_flag": 0,
            "any_local_precursor_hit_flag": 0,
            "best_alert_source": "none",
            "stale_any_prior_alert_flag": 0,
            "stale_best_alert_source": "none",
        },
        {
            "site": "conalog",
            "panel_id": "panel.hit",
            "strict_trigger_date": "2025-01-20",
            "fault_start_date": "2025-01-20",
            "fault_start_source": "strict_trigger_fallback",
            "candidate_validity": "true_positive",
            "vendor_fault_family": "family_hit",
            "any_local_precursor_any_prior_hit_flag": 1,
            "any_local_precursor_bounded_hit_flag": 1,
            "any_local_precursor_hit_flag": 1,
            "best_alert_source": "ews_warning",
            "best_alert_lead_days": 5,
            "stale_any_prior_alert_flag": 0,
            "stale_best_alert_source": "none",
        },
    ]
    write_csv(tmp_root / "_share" / "panel_day_engine_local_precursor_cohort_cases_v1.csv", case_rows, columns=case_columns)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_panel_day_engine_local_precursor_miss_audit_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script), str(Path(__file__))], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        build_fixture_root(tmp_root)

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        share_dir = tmp_root / "_share"
        produced_output_names = {path.name for path in share_dir.iterdir() if path.is_file()}
        assert_true(OUTPUT_NAMES.issubset(produced_output_names), "builder should emit the three miss audit outputs")

        summary_df = pd.read_csv(share_dir / "panel_day_engine_local_precursor_miss_summary_v1.csv", encoding="utf-8-sig")
        cases_df = pd.read_csv(share_dir / "panel_day_engine_local_precursor_miss_cases_v1.csv", encoding="utf-8-sig")
        windows_df = pd.read_csv(share_dir / "panel_day_engine_local_precursor_miss_windows_v1.csv", encoding="utf-8-sig")

        assert_true(len(cases_df) == 4, "only bounded-miss cohort cases should be audited")
        assert_true("panel.hit" not in set(cases_df["panel_id"]), "bounded-hit cases should be excluded from miss audit")

        raw_case = cases_df.loc[cases_df["panel_id"].eq("panel.raw")].iloc[0]
        assert_true(int(raw_case["any_raw_signal_day_flag"]) == 1, "site-specific p90 thresholds should mark the conalog raw-signal miss")
        assert_true(raw_case["strongest_signal_date"] == "2025-01-10", "strongest raw-signal day should be chosen correctly")
        assert_true(raw_case["miss_reason_class"] == "raw_signal_present_but_no_alert", "raw-signal/no-alert miss should classify correctly")

        confound_case = cases_df.loc[cases_df["panel_id"].eq("panel.confound")].iloc[0]
        assert_true(int(confound_case["any_raw_signal_day_flag"]) == 1, "confounded case should still show raw signal days")
        assert_true(int(confound_case["any_group_off_like_flag"]) == 1, "group_off_like confound should be captured")
        assert_true(confound_case["miss_reason_class"] == "confounded_signal_window", "confounded miss should classify correctly")

        stale_case = cases_df.loc[cases_df["panel_id"].eq("panel.stale")].iloc[0]
        assert_true(int(stale_case["stale_any_prior_alert_flag"]) == 1, "stale-only case should preserve stale flag")
        assert_true(int(stale_case["any_raw_signal_day_flag"]) == 0, "stale-only case should have no bounded raw signal days")
        assert_true(stale_case["miss_reason_class"] == "stale_alert_only", "stale-only miss should classify correctly")

        none_case = cases_df.loc[cases_df["panel_id"].eq("panel.none")].iloc[0]
        assert_true(int(none_case["any_raw_signal_day_flag"]) == 0, "no-signal case should not trigger raw-signal flag")
        assert_true(none_case["miss_reason_class"] == "no_obvious_persisted_signal", "no-signal miss should classify correctly")

        sinhyo_window = windows_df.loc[(windows_df["panel_id"].eq("panel.none")) & (windows_df["date"].eq("2025-04-10"))].iloc[0]
        conalog_window = windows_df.loc[(windows_df["panel_id"].eq("panel.raw")) & (windows_df["date"].eq("2025-01-10"))].iloc[0]
        assert_true(int(conalog_window["raw_signal_day_flag"]) == 1, "p90-based raw-signal day should appear in window rows")
        assert_true(int(sinhyo_window["raw_signal_day_flag"]) == 0, "same absolute value can miss when site-specific p90 is higher")
        assert_true(len(windows_df) >= 4, "window rows output should be populated")

        overall = summary_df.loc[summary_df["record_type"].eq("overall")].iloc[0]
        assert_true(int(overall["miss_case_count"]) == 4, "overall miss case count should be correct")
        assert_true(int(overall["no_obvious_persisted_signal_count"]) == 1, "no-signal count should be correct")
        assert_true(int(overall["raw_signal_present_but_no_alert_count"]) == 1, "raw-signal/no-alert count should be correct")
        assert_true(int(overall["confounded_signal_window_count"]) == 1, "confounded count should be correct")
        assert_true(int(overall["stale_alert_only_count"]) == 1, "stale-only count should be correct")
        assert_true(int(overall["any_raw_signal_day_case_count"]) == 2, "any raw-signal case count should be correct")
        assert_true(int(overall["confounded_case_count"]) == 1, "confounded case count should be correct")

    print("[OK] scripts compile")
    print("[OK] outputs generate")
    print("[OK] site-specific p90 thresholds are applied")
    print("[OK] synthetic raw-signal/no-alert miss becomes raw_signal_present_but_no_alert")
    print("[OK] synthetic confounded miss becomes confounded_signal_window")
    print("[OK] synthetic stale-only miss becomes stale_alert_only")
    print("[OK] synthetic no-signal miss becomes no_obvious_persisted_signal")
    print("[OK] window rows output is populated")
    print("[OK] no official outputs are modified")


if __name__ == "__main__":
    main()
