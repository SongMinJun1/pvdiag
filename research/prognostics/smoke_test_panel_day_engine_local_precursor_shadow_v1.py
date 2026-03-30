#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


OUTPUT_NAMES = {
    "panel_day_engine_local_precursor_shadow_v1.csv",
    "panel_day_engine_local_precursor_shadow_summary_v1.csv",
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
    core_columns = [
        "date",
        "panel_id",
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
    ]

    write_csv(
        tmp_root / "data" / "conalog" / "out" / "panel_day_core.csv",
        [
            {
                "date": "2025-01-01",
                "panel_id": "panel.a",
                "recon_error": 0.8,
                "dtw_dist": 0.7,
                "hs_score": 0.4,
                "mid_ratio": 0.85,
                "mid_v_ratio": 0.92,
                "mid_i_ratio": 0.88,
                "v_drop": 0.05,
                "confirmed_fault": 0,
                "critical_fault": 0,
                "final_fault": 0,
                "group_off_like": 0,
                "shadow_like": 0,
            },
            {
                "date": "2025-01-02",
                "panel_id": "panel.a",
                "recon_error": 0.9,
                "dtw_dist": 0.8,
                "hs_score": 0.5,
                "mid_ratio": 0.70,
                "mid_v_ratio": 0.85,
                "mid_i_ratio": 0.78,
                "v_drop": 0.15,
                "confirmed_fault": 0,
                "critical_fault": 0,
                "final_fault": 0,
                "group_off_like": 0,
                "shadow_like": 0,
            },
            {
                "date": "2025-01-03",
                "panel_id": "panel.a",
                "recon_error": 1.1,
                "dtw_dist": 1.0,
                "hs_score": 0.7,
                "mid_ratio": 0.55,
                "mid_v_ratio": 0.80,
                "mid_i_ratio": 0.75,
                "v_drop": 0.20,
                "confirmed_fault": 0,
                "critical_fault": 0,
                "final_fault": 0,
                "group_off_like": 0,
                "shadow_like": 0,
            },
            {
                "date": "2025-01-05",
                "panel_id": "panel.a",
                "recon_error": 1.5,
                "dtw_dist": 1.2,
                "hs_score": 0.9,
                "mid_ratio": 0.20,
                "mid_v_ratio": 0.55,
                "mid_i_ratio": 0.60,
                "v_drop": 0.40,
                "confirmed_fault": 1,
                "critical_fault": 0,
                "final_fault": 1,
                "group_off_like": 0,
                "shadow_like": 0,
            },
            {
                "date": "2025-01-01",
                "panel_id": "panel.b",
                "recon_error": 0.3,
                "dtw_dist": 0.2,
                "hs_score": 0.1,
                "mid_ratio": 0.95,
                "mid_v_ratio": 0.98,
                "mid_i_ratio": 0.97,
                "v_drop": 0.01,
                "confirmed_fault": 0,
                "critical_fault": 0,
                "final_fault": 0,
                "group_off_like": 1,
                "shadow_like": 1,
            },
        ],
        columns=core_columns,
    )

    write_csv(
        tmp_root / "data" / "conalog" / "out" / "ae_simple_ews_warnings.csv",
        [
            {"date": "2025-01-01", "panel_id": "panel.a"},
            {"date": "2025-01-01", "panel_id": "panel.a"},
        ],
    )
    write_csv(
        tmp_root / "data" / "conalog" / "out" / "ae_simple_prefault_B_daily.csv",
        [
            {"date": "2025-01-02", "panel_id": "panel.a"},
        ],
    )
    write_csv(
        tmp_root / "data" / "conalog" / "out" / "ae_simple_panel_alarms.csv",
        [
            {
                "panel_id": "panel.a",
                "first_date": "2025-01-01",
                "last_date": "2025-01-05",
                "has_fault": 1,
                "n_fault_days": 1,
                "any_ews": 1,
                "n_ews_days": 1,
                "any_pre_alarm": 1,
                "n_pre_alarm_days": 2,
                "fault_start_date": "2025-01-05",
                "pre_alarm_start": "2025-01-03",
                "lead_days": 2,
                "alarm_pattern": "pre_fault_candidate",
            },
            {
                "panel_id": "panel.b",
                "first_date": "2025-01-01",
                "last_date": "2025-01-01",
                "has_fault": 0,
                "n_fault_days": 0,
                "any_ews": 0,
                "n_ews_days": 0,
                "any_pre_alarm": 0,
                "n_pre_alarm_days": 0,
                "fault_start_date": "",
                "pre_alarm_start": "",
                "lead_days": "",
                "alarm_pattern": "no_pre_alarm",
            },
        ],
    )

    for site in ["gangui", "ktc_ess", "sinhyo"]:
        write_csv(
            tmp_root / "data" / site / "out" / "panel_day_core.csv",
            [
                {
                    "date": "2025-02-01",
                    "panel_id": f"{site}.panel.1",
                    "recon_error": 0.2,
                    "dtw_dist": 0.2,
                    "hs_score": 0.2,
                    "mid_ratio": 0.98,
                    "mid_v_ratio": 0.99,
                    "mid_i_ratio": 0.97,
                    "v_drop": 0.01,
                    "confirmed_fault": 0,
                    "critical_fault": 0,
                    "final_fault": 0,
                    "group_off_like": 0,
                    "shadow_like": 0,
                }
            ],
            columns=core_columns,
        )


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_panel_day_engine_local_precursor_shadow_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script), str(Path(__file__))], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        build_fixture_root(tmp_root)

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        share_dir = tmp_root / "_share"
        produced_output_names = {path.name for path in share_dir.iterdir() if path.is_file()}
        assert_true(produced_output_names == OUTPUT_NAMES, "builder should only emit the two local-precursor shadow outputs")

        shadow_df = pd.read_csv(share_dir / "panel_day_engine_local_precursor_shadow_v1.csv", encoding="utf-8-sig")
        summary_df = pd.read_csv(share_dir / "panel_day_engine_local_precursor_shadow_summary_v1.csv", encoding="utf-8-sig")

        assert_true(len(shadow_df) == 8, "row count should match synthetic panel_day_core rows across all sites")
        assert_true(shadow_df[["site", "panel_id", "date"]].duplicated().sum() == 0, "base unit should stay unique")

        panel_a = shadow_df.loc[
            shadow_df["site"].eq("conalog") & shadow_df["panel_id"].eq("panel.a")
        ].sort_values("date")
        jan1 = panel_a.loc[panel_a["date"].eq("2025-01-01")].iloc[0]
        jan2 = panel_a.loc[panel_a["date"].eq("2025-01-02")].iloc[0]
        jan3 = panel_a.loc[panel_a["date"].eq("2025-01-03")].iloc[0]
        jan5 = panel_a.loc[panel_a["date"].eq("2025-01-05")].iloc[0]

        assert_true(int(jan1["ews_warning_flag"]) == 1, "ews helper should join at the day level")
        assert_true(int(jan2["prefault_B_flag"]) == 1, "prefault helper should join at the day level")
        assert_true(int(jan3["pre_alarm_flag"]) == 1, "pre_alarm helper should anchor to pre_alarm_start date")
        assert_true(int(jan1["local_precursor_any_flag"]) == 1, "local_precursor_any_flag should be max of helper flags")
        assert_true(jan1["first_local_precursor_date_per_panel"] == "2025-01-01", "first_local_precursor_date_per_panel should be earliest local precursor date")
        assert_true(int(float(jan1["lead_days_to_final_fault"])) == 4, "lead_days should count from precursor row to first later final fault")
        assert_true(int(float(jan2["lead_days_to_final_fault"])) == 3, "lead_days should update per precursor row")
        assert_true(int(float(jan3["lead_days_to_final_fault"])) == 2, "pre_alarm lead_days should be correct")
        assert_true(pd.isna(jan5["lead_days_to_final_fault"]), "non-precursor rows should keep blank lead days")

        assert_true(jan1["alert_pattern"] == "ews_only", "single ews row should classify as ews_only")
        assert_true(jan2["alert_pattern"] == "prefault_only", "single prefault row should classify as prefault_only")
        assert_true(jan3["alert_pattern"] == "pre_alarm_only", "single pre_alarm row should classify as pre_alarm_only")
        assert_true(jan5["alert_pattern"] == "no_local_precursor", "no helper flags should classify as no_local_precursor")

        gangui_row = shadow_df.loc[shadow_df["site"].eq("gangui")].iloc[0]
        assert_true(int(gangui_row["local_precursor_any_flag"]) == 0, "missing helper files should default to zero flags")
        assert_true(
            pd.isna(gangui_row["first_local_precursor_date_per_panel"])
            or gangui_row["first_local_precursor_date_per_panel"] == "",
            "missing helper files should keep blank first precursor date",
        )
        assert_true(gangui_row["alert_pattern"] == "no_local_precursor", "missing helper files should classify as no_local_precursor")

        conalog_summary = summary_df.loc[summary_df["site"].eq("conalog")].iloc[0]
        assert_true(int(conalog_summary["ews_warning_day_count"]) == 1, "summary should count ews days")
        assert_true(int(conalog_summary["prefault_B_day_count"]) == 1, "summary should count prefault days")
        assert_true(int(conalog_summary["pre_alarm_day_count"]) == 1, "summary should count pre_alarm days")
        assert_true(int(conalog_summary["local_precursor_any_day_count"]) == 3, "summary should count any precursor days")
        assert_true(int(conalog_summary["panels_with_any_local_precursor_count"]) == 1, "summary should count panels with any precursor")
        assert_true(int(conalog_summary["final_fault_panel_count"]) == 1, "summary should count final fault panels")
        assert_true(
            int(conalog_summary["final_fault_panels_with_prior_local_precursor_count"]) == 1,
            "summary should count final-fault panels with prior local precursor",
        )

    print("[OK] scripts compile")
    print("[OK] outputs generate")
    print("[OK] helper outputs join correctly")
    print("[OK] local_precursor_any_flag works")
    print("[OK] first_local_precursor_date_per_panel is correct")
    print("[OK] lead_days_to_final_fault is correct on synthetic data")
    print("[OK] missing helper files are tolerated and produce false/blank flags")
    print("[OK] no official outputs are modified")


if __name__ == "__main__":
    main()
