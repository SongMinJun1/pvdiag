#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


OUTPUT_NAMES = {
    "panel_day_engine_local_precursor_threshold_replay_summary_v1.csv",
    "panel_day_engine_local_precursor_threshold_replay_cases_v1.csv",
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
            "panel_id": "fill.1",
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
            "panel_id": "fill.2",
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
            "panel_id": "fill.3",
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
            "panel_id": "pos.hit",
            "date": "2025-01-18",
            "recon_error": 0.20,
            "dtw_dist": 0.20,
            "hs_score": 0.20,
            "mid_ratio": 0.85,
            "mid_v_ratio": 0.80,
            "mid_i_ratio": 0.90,
            "v_drop": 0.10,
            "confirmed_fault": 0,
            "critical_fault": 0,
            "final_fault": 0,
            "group_off_like": 0,
            "shadow_like": 0,
            "ews_warning_flag": 1,
            "prefault_B_flag": 0,
            "pre_alarm_flag": 0,
            "local_precursor_any_flag": 1,
            "first_local_precursor_date_per_panel": "2025-01-18",
            "lead_days_to_final_fault": 2,
            "alert_pattern": "ews_only",
        },
        {
            "site": "conalog",
            "panel_id": "pos.recover_combo",
            "date": "2025-02-18",
            "recon_error": 1.00,
            "dtw_dist": 0.20,
            "hs_score": 0.20,
            "mid_ratio": 0.75,
            "mid_v_ratio": 0.80,
            "mid_i_ratio": 0.90,
            "v_drop": 0.10,
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
            "panel_id": "pos.persist",
            "date": "2025-03-15",
            "recon_error": 0.10,
            "dtw_dist": 0.10,
            "hs_score": 0.10,
            "mid_ratio": 0.80,
            "mid_v_ratio": 0.82,
            "mid_i_ratio": 0.88,
            "v_drop": 0.12,
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
            "panel_id": "pos.persist",
            "date": "2025-03-17",
            "recon_error": 0.10,
            "dtw_dist": 0.10,
            "hs_score": 0.10,
            "mid_ratio": 0.78,
            "mid_v_ratio": 0.83,
            "mid_i_ratio": 0.84,
            "v_drop": 0.22,
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
            "panel_id": "nuisance.group",
            "date": "2025-04-18",
            "recon_error": 0.10,
            "dtw_dist": 0.10,
            "hs_score": 0.10,
            "mid_ratio": 0.85,
            "mid_v_ratio": 0.82,
            "mid_i_ratio": 0.88,
            "v_drop": 0.10,
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
            "panel_id": "nuisance.fp",
            "date": "2025-05-18",
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
    ]
    write_csv(tmp_root / "_share" / "panel_day_engine_local_precursor_shadow_v1.csv", shadow_rows, columns=shadow_columns)

    cohort_case_columns = [
        "site",
        "panel_id",
        "strict_trigger_date",
        "fault_start_date",
        "fault_start_source",
    ]
    write_csv(
        tmp_root / "_share" / "panel_day_engine_local_precursor_cohort_cases_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": "pos.hit",
                "strict_trigger_date": "2025-01-20",
                "fault_start_date": "2025-01-20",
                "fault_start_source": "strict_trigger_fallback",
            },
            {
                "site": "conalog",
                "panel_id": "pos.recover_combo",
                "strict_trigger_date": "2025-02-20",
                "fault_start_date": "2025-02-20",
                "fault_start_source": "final_fault_first_true",
            },
            {
                "site": "conalog",
                "panel_id": "pos.persist",
                "strict_trigger_date": "2025-03-20",
                "fault_start_date": "2025-03-20",
                "fault_start_source": "strict_trigger_fallback",
            },
        ],
        columns=cohort_case_columns,
    )

    reaudit_columns = [
        "site",
        "panel_id",
        "strict_trigger_date",
        "candidate_validity",
        "vendor_fault_family",
    ]
    write_csv(
        tmp_root / "_share" / "panel_date_reaudit_working.csv",
        [
            {
                "site": "conalog",
                "panel_id": "pos.hit",
                "strict_trigger_date": "2025-01-20",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "family_hit",
            },
            {
                "site": "conalog",
                "panel_id": "pos.recover_combo",
                "strict_trigger_date": "2025-02-20",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "family_combo",
            },
            {
                "site": "conalog",
                "panel_id": "pos.persist",
                "strict_trigger_date": "2025-03-20",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "family_persist",
            },
            {
                "site": "conalog",
                "panel_id": "nuisance.group",
                "strict_trigger_date": "2025-04-20",
                "candidate_validity": "group_side",
                "vendor_fault_family": "family_group",
            },
            {
                "site": "conalog",
                "panel_id": "nuisance.fp",
                "strict_trigger_date": "2025-05-20",
                "candidate_validity": "false_positive",
                "vendor_fault_family": "family_fp",
            },
            {
                "site": "conalog",
                "panel_id": "excluded.nmi",
                "strict_trigger_date": "2025-06-20",
                "candidate_validity": "needs_more_info",
                "vendor_fault_family": "family_nmi",
            },
        ],
        columns=reaudit_columns,
    )


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_panel_day_engine_local_precursor_threshold_replay_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script), str(Path(__file__))], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        build_fixture_root(tmp_root)

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        share_dir = tmp_root / "_share"
        produced_output_names = {path.name for path in share_dir.iterdir() if path.is_file()}
        assert_true(OUTPUT_NAMES.issubset(produced_output_names), "builder should emit the two threshold replay outputs")

        cases_df = pd.read_csv(share_dir / "panel_day_engine_local_precursor_threshold_replay_cases_v1.csv", encoding="utf-8-sig")
        summary_df = pd.read_csv(share_dir / "panel_day_engine_local_precursor_threshold_replay_summary_v1.csv", encoding="utf-8-sig")

        assert_true(len(cases_df) == 20, "expected one row per case per rule")
        assert_true(set(cases_df["cohort_type"]) == {"positive", "nuisance"}, "both positive and nuisance cohorts should be included")

        raw_any_combo = cases_df.loc[
            cases_df["rule_id"].eq("raw_signal_any_day") & cases_df["panel_id"].eq("pos.recover_combo")
        ].iloc[0]
        assert_true(int(raw_any_combo["rule_trigger_flag"]) == 1, "raw_signal_any_day should recover a synthetic miss")
        assert_true(raw_any_combo["earliest_rule_trigger_date"] == "2025-02-18", "raw_signal_any_day should use earliest raw-signal day")

        raw_persist_combo = cases_df.loc[
            cases_df["rule_id"].eq("raw_signal_2day_persistence") & cases_df["panel_id"].eq("pos.recover_combo")
        ].iloc[0]
        assert_true(int(raw_persist_combo["rule_trigger_flag"]) == 0, "raw_signal_2day_persistence should be stricter than raw_signal_any_day")

        raw_persist_case = cases_df.loc[
            cases_df["rule_id"].eq("raw_signal_2day_persistence") & cases_df["panel_id"].eq("pos.persist")
        ].iloc[0]
        assert_true(int(raw_persist_case["rule_trigger_flag"]) == 1, "two raw-signal days should trigger persistence rule")
        assert_true(raw_persist_case["earliest_rule_trigger_date"] == "2025-03-17", "persistence rule should trigger on the second raw-signal day")

        combo_case = cases_df.loc[
            cases_df["rule_id"].eq("shape_plus_electrical_combo") & cases_df["panel_id"].eq("pos.recover_combo")
        ].iloc[0]
        assert_true(int(combo_case["rule_trigger_flag"]) == 1, "shape_plus_electrical_combo should require both evidence families and trigger here")
        combo_fail_case = cases_df.loc[
            cases_df["rule_id"].eq("shape_plus_electrical_combo") & cases_df["panel_id"].eq("pos.persist")
        ].iloc[0]
        assert_true(int(combo_fail_case["rule_trigger_flag"]) == 0, "shape_plus_electrical_combo should not trigger on electrical-only evidence")

        nuisance_case = cases_df.loc[
            cases_df["rule_id"].eq("raw_signal_any_day") & cases_df["panel_id"].eq("nuisance.group")
        ].iloc[0]
        assert_true(int(nuisance_case["rule_trigger_flag"]) == 1, "nuisance cohort rows should be evaluated")
        assert_true(pd.isna(nuisance_case["rule_lead_days"]) or nuisance_case["rule_lead_days"] == "", "nuisance rule lead days may be blank")

        summary_current = summary_df.loc[summary_df["rule_id"].eq("current_bounded_alert")].iloc[0]
        summary_any = summary_df.loc[summary_df["rule_id"].eq("raw_signal_any_day")].iloc[0]
        summary_persist = summary_df.loc[summary_df["rule_id"].eq("raw_signal_2day_persistence")].iloc[0]
        summary_combo = summary_df.loc[summary_df["rule_id"].eq("shape_plus_electrical_combo")].iloc[0]

        assert_true(int(summary_current["positive_trigger_case_count"]) == 1, "current_bounded_alert should keep the existing bounded hit only")
        assert_true(int(summary_any["positive_trigger_case_count"]) == 3, "raw_signal_any_day should recover both synthetic misses")
        assert_true(int(summary_any["recovered_positive_cases_vs_current"]) == 2, "recovered_positive_cases_vs_current should be computed correctly")
        assert_true(float(summary_any["nuisance_trigger_rate"]) == 0.5, "nuisance_trigger_rate should be computed correctly")
        assert_true(int(summary_persist["positive_trigger_case_count"]) == 1, "persistence rule should remain stricter than any-day replay")
        assert_true(int(summary_combo["positive_trigger_case_count"]) == 1, "combo rule should require both shape and electrical evidence")

    print("[OK] scripts compile")
    print("[OK] outputs generate")
    print("[OK] raw_signal_any_day recovers a synthetic miss")
    print("[OK] raw_signal_2day_persistence is stricter than raw_signal_any_day on synthetic data")
    print("[OK] shape_plus_electrical_combo requires both shape and electrical evidence")
    print("[OK] nuisance cohort rows are included and nuisance_trigger_rate is computed")
    print("[OK] recovered_positive_cases_vs_current is computed correctly")
    print("[OK] no official outputs are modified")


if __name__ == "__main__":
    main()
