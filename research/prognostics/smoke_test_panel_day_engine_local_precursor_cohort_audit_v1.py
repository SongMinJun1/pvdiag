#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


OUTPUT_NAMES = {
    "panel_day_engine_local_precursor_cohort_summary_v1.csv",
    "panel_day_engine_local_precursor_cohort_cases_v1.csv",
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
    write_csv(
        tmp_root / "_share" / "panel_day_engine_local_precursor_shadow_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": "panel.a",
                "date": "2025-01-08",
                "recon_error": 0.9,
                "dtw_dist": 0.8,
                "hs_score": 0.7,
                "mid_ratio": 0.80,
                "mid_v_ratio": 0.90,
                "mid_i_ratio": 0.88,
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
                "first_local_precursor_date_per_panel": "2025-01-08",
                "lead_days_to_final_fault": 4,
                "alert_pattern": "ews_only",
            },
            {
                "site": "conalog",
                "panel_id": "panel.a",
                "date": "2025-01-09",
                "recon_error": 1.0,
                "dtw_dist": 0.9,
                "hs_score": 0.8,
                "mid_ratio": 0.70,
                "mid_v_ratio": 0.85,
                "mid_i_ratio": 0.83,
                "v_drop": 0.14,
                "confirmed_fault": 0,
                "critical_fault": 0,
                "final_fault": 0,
                "group_off_like": 0,
                "shadow_like": 0,
                "ews_warning_flag": 0,
                "prefault_B_flag": 1,
                "pre_alarm_flag": 0,
                "local_precursor_any_flag": 1,
                "first_local_precursor_date_per_panel": "2025-01-08",
                "lead_days_to_final_fault": 3,
                "alert_pattern": "prefault_only",
            },
            {
                "site": "conalog",
                "panel_id": "panel.a",
                "date": "2025-01-11",
                "recon_error": 1.2,
                "dtw_dist": 1.0,
                "hs_score": 0.9,
                "mid_ratio": 0.55,
                "mid_v_ratio": 0.80,
                "mid_i_ratio": 0.75,
                "v_drop": 0.20,
                "confirmed_fault": 0,
                "critical_fault": 0,
                "final_fault": 0,
                "group_off_like": 0,
                "shadow_like": 0,
                "ews_warning_flag": 0,
                "prefault_B_flag": 0,
                "pre_alarm_flag": 1,
                "local_precursor_any_flag": 1,
                "first_local_precursor_date_per_panel": "2025-01-08",
                "lead_days_to_final_fault": 1,
                "alert_pattern": "pre_alarm_only",
            },
            {
                "site": "conalog",
                "panel_id": "panel.a",
                "date": "2025-01-12",
                "recon_error": 1.5,
                "dtw_dist": 1.3,
                "hs_score": 1.0,
                "mid_ratio": 0.20,
                "mid_v_ratio": 0.60,
                "mid_i_ratio": 0.60,
                "v_drop": 0.40,
                "confirmed_fault": 1,
                "critical_fault": 0,
                "final_fault": 1,
                "group_off_like": 0,
                "shadow_like": 0,
                "ews_warning_flag": 0,
                "prefault_B_flag": 0,
                "pre_alarm_flag": 0,
                "local_precursor_any_flag": 0,
                "first_local_precursor_date_per_panel": "2025-01-08",
                "lead_days_to_final_fault": "",
                "alert_pattern": "no_local_precursor",
            },
            {
                "site": "gangui",
                "panel_id": "panel.b",
                "date": "2025-02-03",
                "recon_error": 0.8,
                "dtw_dist": 0.7,
                "hs_score": 0.6,
                "mid_ratio": 0.76,
                "mid_v_ratio": 0.88,
                "mid_i_ratio": 0.85,
                "v_drop": 0.12,
                "confirmed_fault": 0,
                "critical_fault": 0,
                "final_fault": 0,
                "group_off_like": 0,
                "shadow_like": 0,
                "ews_warning_flag": 1,
                "prefault_B_flag": 1,
                "pre_alarm_flag": 0,
                "local_precursor_any_flag": 1,
                "first_local_precursor_date_per_panel": "2025-02-03",
                "lead_days_to_final_fault": "",
                "alert_pattern": "ews_and_prefault",
            },
            {
                "site": "gangui",
                "panel_id": "panel.e",
                "date": "2025-04-10",
                "recon_error": 0.8,
                "dtw_dist": 0.7,
                "hs_score": 0.6,
                "mid_ratio": 0.70,
                "mid_v_ratio": 0.88,
                "mid_i_ratio": 0.85,
                "v_drop": 0.12,
                "confirmed_fault": 0,
                "critical_fault": 0,
                "final_fault": 0,
                "group_off_like": 0,
                "shadow_like": 0,
                "ews_warning_flag": 0,
                "prefault_B_flag": 0,
                "pre_alarm_flag": 1,
                "local_precursor_any_flag": 1,
                "first_local_precursor_date_per_panel": "2025-04-10",
                "lead_days_to_final_fault": "",
                "alert_pattern": "pre_alarm_only",
            },
            {
                "site": "ktc_ess",
                "panel_id": "panel.c",
                "date": "2025-03-10",
                "recon_error": 0.7,
                "dtw_dist": 0.6,
                "hs_score": 0.5,
                "mid_ratio": 0.74,
                "mid_v_ratio": 0.86,
                "mid_i_ratio": 0.84,
                "v_drop": 0.11,
                "confirmed_fault": 0,
                "critical_fault": 0,
                "final_fault": 0,
                "group_off_like": 0,
                "shadow_like": 0,
                "ews_warning_flag": 1,
                "prefault_B_flag": 0,
                "pre_alarm_flag": 0,
                "local_precursor_any_flag": 1,
                "first_local_precursor_date_per_panel": "2025-03-10",
                "lead_days_to_final_fault": "",
                "alert_pattern": "ews_only",
            },
            {
                "site": "ktc_ess",
                "panel_id": "panel.d",
                "date": "2024-12-14",
                "recon_error": 0.8,
                "dtw_dist": 0.7,
                "hs_score": 0.6,
                "mid_ratio": 0.72,
                "mid_v_ratio": 0.86,
                "mid_i_ratio": 0.84,
                "v_drop": 0.12,
                "confirmed_fault": 0,
                "critical_fault": 0,
                "final_fault": 0,
                "group_off_like": 0,
                "shadow_like": 0,
                "ews_warning_flag": 1,
                "prefault_B_flag": 0,
                "pre_alarm_flag": 1,
                "local_precursor_any_flag": 1,
                "first_local_precursor_date_per_panel": "2024-12-14",
                "lead_days_to_final_fault": "",
                "alert_pattern": "ews_and_pre_alarm",
            },
            {
                "site": "ktc_ess",
                "panel_id": "panel.d",
                "date": "2025-08-16",
                "recon_error": 1.4,
                "dtw_dist": 1.2,
                "hs_score": 0.9,
                "mid_ratio": 0.22,
                "mid_v_ratio": 0.58,
                "mid_i_ratio": 0.60,
                "v_drop": 0.40,
                "confirmed_fault": 1,
                "critical_fault": 0,
                "final_fault": 1,
                "group_off_like": 0,
                "shadow_like": 0,
                "ews_warning_flag": 0,
                "prefault_B_flag": 0,
                "pre_alarm_flag": 0,
                "local_precursor_any_flag": 0,
                "first_local_precursor_date_per_panel": "2024-12-14",
                "lead_days_to_final_fault": "",
                "alert_pattern": "no_local_precursor",
            },
        ],
        columns=shadow_columns,
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
                "panel_id": "panel.a",
                "strict_trigger_date": "2025-01-10",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "",
            },
            {
                "site": "gangui",
                "panel_id": "panel.b",
                "strict_trigger_date": "2025-02-05",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "family_from_reaudit",
            },
            {
                "site": "ktc_ess",
                "panel_id": "panel.c",
                "strict_trigger_date": "2025-03-10",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "",
            },
            {
                "site": "ktc_ess",
                "panel_id": "panel.d",
                "strict_trigger_date": "2025-08-16",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "",
            },
            {
                "site": "gangui",
                "panel_id": "panel.e",
                "strict_trigger_date": "2025-04-20",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "",
            },
            {
                "site": "conalog",
                "panel_id": "panel.group",
                "strict_trigger_date": "2025-01-15",
                "candidate_validity": "group_side",
                "vendor_fault_family": "",
            },
            {
                "site": "gangui",
                "panel_id": "panel.fp",
                "strict_trigger_date": "2025-02-06",
                "candidate_validity": "false_positive",
                "vendor_fault_family": "",
            },
        ],
        columns=reaudit_columns,
    )

    write_csv(
        tmp_root / "_share" / "vendor_reply_adjudication_latest.csv",
        [
            {
                "site": "conalog",
                "panel_id": "panel.a",
                "strict_trigger_date": "2025-01-10",
                "vendor_fault_family": "family_from_vendor",
            },
            {
                "site": "ktc_ess",
                "panel_id": "panel.c",
                "strict_trigger_date": "2025-03-10",
                "vendor_fault_family": "family_ktc_vendor",
            },
            {
                "site": "ktc_ess",
                "panel_id": "panel.d",
                "strict_trigger_date": "2025-08-16",
                "vendor_fault_family": "family_panel_d_vendor",
            },
        ],
    )


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_panel_day_engine_local_precursor_cohort_audit_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script), str(Path(__file__))], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        build_fixture_root(tmp_root)

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        share_dir = tmp_root / "_share"
        produced_output_names = {path.name for path in share_dir.iterdir() if path.is_file()}
        assert_true(
            OUTPUT_NAMES.issubset(produced_output_names),
            "builder should emit the two cohort audit outputs",
        )

        cases_df = pd.read_csv(share_dir / "panel_day_engine_local_precursor_cohort_cases_v1.csv", encoding="utf-8-sig")
        summary_df = pd.read_csv(share_dir / "panel_day_engine_local_precursor_cohort_summary_v1.csv", encoding="utf-8-sig")

        assert_true(len(cases_df) == 5, "true_positive cohort filtering should keep only five synthetic cases")
        assert_true(
            set(cases_df["panel_id"]) == {"panel.a", "panel.b", "panel.c", "panel.d", "panel.e"},
            "group_side and false_positive rows should be excluded",
        )

        case_a = cases_df.loc[cases_df["panel_id"].eq("panel.a")].iloc[0]
        assert_true(case_a["fault_start_date"] == "2025-01-12", "fault_start_date should use first final_fault when available")
        assert_true(case_a["fault_start_source"] == "final_fault_first_true", "fault_start_source should record final_fault origin")
        assert_true(case_a["vendor_fault_family"] == "family_from_vendor", "vendor context should fill blank family from vendor adjudication")
        assert_true(case_a["first_ews_warning_date_any_prior"] == "2025-01-08", "any-prior ews date should be earliest prior alert")
        assert_true(case_a["first_prefault_B_date_any_prior"] == "2025-01-09", "any-prior prefault date should be earliest prior alert")
        assert_true(case_a["first_pre_alarm_date_any_prior"] == "2025-01-11", "any-prior pre_alarm date should be earliest prior alert")
        assert_true(case_a["first_ews_warning_date_bounded"] == "2025-01-08", "bounded ews date should stay within the valid window")
        assert_true(case_a["first_prefault_B_date_bounded"] == "2025-01-09", "bounded prefault date should stay within the valid window")
        assert_true(case_a["first_pre_alarm_date_bounded"] == "2025-01-11", "bounded pre_alarm date should stay within the valid window")
        assert_true(int(case_a["any_local_precursor_any_prior_hit_flag"]) == 1, "any-prior hit flag should be set")
        assert_true(int(case_a["any_local_precursor_bounded_hit_flag"]) == 1, "bounded hit flag should be set")
        assert_true(int(case_a["any_local_precursor_hit_flag"]) == 1, "legacy hit flag should now mean bounded hit")
        assert_true(case_a["best_alert_source"] == "ews_warning", "best bounded alert should use bounded alerts only")
        assert_true(int(case_a["best_alert_lead_days"]) == 4, "best bounded lead should be correct")
        assert_true(int(case_a["stale_any_prior_alert_flag"]) == 0, "bounded-hit case should not be stale")

        case_b = cases_df.loc[cases_df["panel_id"].eq("panel.b")].iloc[0]
        assert_true(case_b["fault_start_date"] == "2025-02-05", "strict_trigger fallback should be used when no final_fault exists")
        assert_true(case_b["fault_start_source"] == "strict_trigger_fallback", "fault_start_source should record fallback")
        assert_true(case_b["first_ews_warning_date_bounded"] == "2025-02-03", "bounded ews date should be kept")
        assert_true(case_b["first_prefault_B_date_bounded"] == "2025-02-03", "bounded prefault date should be kept")
        assert_true(case_b["best_alert_source"] == "prefault_B", "tie-break should prefer prefault_B over ews_warning")
        assert_true(int(case_b["best_alert_lead_days"]) == 2, "bounded best lead should be correct")

        case_c = cases_df.loc[cases_df["panel_id"].eq("panel.c")].iloc[0]
        assert_true(pd.isna(case_c["first_ews_warning_date_any_prior"]) or case_c["first_ews_warning_date_any_prior"] == "", "same-day alerts should not count as any-prior hits")
        assert_true(int(case_c["any_local_precursor_any_prior_hit_flag"]) == 0, "same-day-only alert should not count as prior hit")
        assert_true(int(case_c["any_local_precursor_bounded_hit_flag"]) == 0, "same-day-only alert should not count as bounded hit")
        assert_true(case_c["best_alert_source"] == "none", "no bounded hit should produce none")

        case_d = cases_df.loc[cases_df["panel_id"].eq("panel.d")].iloc[0]
        assert_true(case_d["first_ews_warning_date_any_prior"] == "2024-12-14", "stale any-prior ews should be preserved")
        assert_true(case_d["first_pre_alarm_date_any_prior"] == "2024-12-14", "stale any-prior pre_alarm should be preserved")
        assert_true(pd.isna(case_d["first_ews_warning_date_bounded"]) or case_d["first_ews_warning_date_bounded"] == "", "245-day-old alert should not be bounded")
        assert_true(pd.isna(case_d["first_pre_alarm_date_bounded"]) or case_d["first_pre_alarm_date_bounded"] == "", "245-day-old alert should not be bounded")
        assert_true(int(case_d["any_local_precursor_any_prior_hit_flag"]) == 1, "stale case should count as any-prior hit")
        assert_true(int(case_d["any_local_precursor_bounded_hit_flag"]) == 0, "stale case should not count as bounded hit")
        assert_true(int(case_d["stale_any_prior_alert_flag"]) == 1, "stale flag should fire when only stale hits exist")
        assert_true(case_d["best_alert_source"] == "none", "bounded best alert should stay none for stale-only case")
        assert_true(case_d["stale_best_alert_source"] == "pre_alarm", "stale tie-break should prefer pre_alarm over ews_warning")
        assert_true(int(case_d["stale_best_alert_lead_days"]) == 245, "stale best lead should measure the stale gap")

        case_e = cases_df.loc[cases_df["panel_id"].eq("panel.e")].iloc[0]
        assert_true(case_e["first_pre_alarm_date_bounded"] == "2025-04-10", "8-to-30-day bounded alert should be captured")
        assert_true(int(case_e["pre_alarm_bounded_lead_days"]) == 10, "8-to-30 bounded lead should be correct")
        assert_true(case_e["best_alert_source"] == "pre_alarm", "single bounded pre_alarm should become best source")

        overall = summary_df.loc[summary_df["record_type"].eq("overall")].iloc[0]
        assert_true(int(overall["cohort_case_count"]) == 5, "overall summary should count true_positive cases")
        assert_true(int(overall["any_prior_hit_case_count"]) == 4, "overall any-prior hit count should be correct")
        assert_true(int(overall["bounded_hit_case_count"]) == 3, "overall bounded hit count should be correct")
        assert_true(int(overall["bounded_lead_1_to_3_case_count"]) == 1, "1-to-3 bounded lead bucket should be correct")
        assert_true(int(overall["bounded_lead_4_to_7_case_count"]) == 1, "4-to-7 bounded lead bucket should be correct")
        assert_true(int(overall["bounded_lead_8_to_30_case_count"]) == 1, "8-to-30 bounded lead bucket should be correct")
        assert_true(int(overall["stale_alert_case_count"]) == 1, "stale alert case count should be correct")
        assert_true(int(overall["no_bounded_alert_before_fault_count"]) == 2, "no bounded alert count should be correct")
        assert_true(float(overall["median_best_alert_lead_days"]) == 4.0, "median bounded best lead should ignore stale 245-day alerts")

    print("[OK] scripts compile")
    print("[OK] outputs generate")
    print("[OK] true_positive cohort filtering works")
    print("[OK] group_side and false_positive rows are excluded")
    print("[OK] fault_start_date uses final_fault when available")
    print("[OK] strict_trigger fallback works when final_fault is absent")
    print("[OK] a synthetic alert 245 days before fault counts as any-prior hit but not bounded hit")
    print("[OK] best_alert_lead_days uses bounded alerts only")
    print("[OK] stale_any_prior_alert_flag fires correctly")
    print("[OK] bounded lead bucket counts compute correctly")
    print("[OK] no official outputs are modified")


if __name__ == "__main__":
    main()
