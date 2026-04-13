#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DELTA_COLS = [
    "version",
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "delta_run_class",
    "overlapping_baseline_run_count",
    "baseline_overlap_day_count",
    "overlap_case_class",
    "overlapping_case_ids",
    "overlapping_case_types",
]
HELPER_COLS = [
    "site",
    "panel_id",
    "date",
    "data_bad",
    "cond_var",
    "cond_evt",
    "cond_dtw",
    "cond_hs",
    "ae_mid_or_hi_early",
    "dtw_mid_or_hi_early",
    "hs_mid_or_hi_early",
    "pre_ews",
    "signal_count",
    "ews_runlen",
    "ews_warning",
    "site_event_soft",
    "site_event_hard",
    "group_off_date",
    "prefault_B",
    "pre_alarm",
    "prefault_cond_mid",
    "prefault_cond_ae",
    "prefault_cond_dtw",
    "prefault_cond_ews",
    "prealarm_cond_ae_mid_or_hi",
    "prealarm_cond_dtw_mid_or_hi",
    "prealarm_cond_hs_mid_or_hi",
]
CORE_COLS = [
    "date",
    "panel_id",
    "confirmed_fault",
    "critical_fault",
    "final_fault",
    "recon_error",
    "dtw_dist",
    "hs_score",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "v_drop",
]


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


def helper_row(
    site: str,
    panel_id: str,
    date: str,
    *,
    pre_alarm: int = 0,
    cond_evt: int = 1,
    cond_var: int = 1,
    cond_dtw: int = 0,
    cond_hs: int = 0,
    ae_mid_or_hi_early: int = 1,
    dtw_mid_or_hi_early: int = 0,
    hs_mid_or_hi_early: int = 0,
    signal_count: int = 2,
) -> dict[str, object]:
    return {
        "site": site,
        "panel_id": panel_id,
        "date": date,
        "data_bad": 0,
        "cond_var": cond_var,
        "cond_evt": cond_evt,
        "cond_dtw": cond_dtw,
        "cond_hs": cond_hs,
        "ae_mid_or_hi_early": ae_mid_or_hi_early,
        "dtw_mid_or_hi_early": dtw_mid_or_hi_early,
        "hs_mid_or_hi_early": hs_mid_or_hi_early,
        "pre_ews": pre_alarm,
        "signal_count": signal_count,
        "ews_runlen": 5 if pre_alarm else 0,
        "ews_warning": pre_alarm,
        "site_event_soft": 0,
        "site_event_hard": 0,
        "group_off_date": 0,
        "prefault_B": 0,
        "pre_alarm": pre_alarm,
        "prefault_cond_mid": 0,
        "prefault_cond_ae": 0,
        "prefault_cond_dtw": 0,
        "prefault_cond_ews": 0,
        "prealarm_cond_ae_mid_or_hi": ae_mid_or_hi_early,
        "prealarm_cond_dtw_mid_or_hi": dtw_mid_or_hi_early,
        "prealarm_cond_hs_mid_or_hi": hs_mid_or_hi_early,
    }


def core_row(
    panel_id: str,
    date: str,
    *,
    confirmed_fault: int = 0,
    critical_fault: int = 0,
    final_fault: int = 0,
    recon_error: float = 0.4,
    dtw_dist: float = 0.3,
    hs_score: float = 0.2,
    mid_ratio: float = 0.8,
    mid_v_ratio: float = 0.8,
    mid_i_ratio: float = 0.8,
    v_drop: float = 0.1,
) -> dict[str, object]:
    return {
        "date": date,
        "panel_id": panel_id,
        "confirmed_fault": confirmed_fault,
        "critical_fault": critical_fault,
        "final_fault": final_fault,
        "recon_error": recon_error,
        "dtw_dist": dtw_dist,
        "hs_score": hs_score,
        "mid_ratio": mid_ratio,
        "mid_v_ratio": mid_v_ratio,
        "mid_i_ratio": mid_i_ratio,
        "v_drop": v_drop,
    }


def build_fixture_root(tmp_root: Path) -> None:
    delta_rows = [
        {
            "version": "current_seed_carry1",
            "site": "conalog",
            "panel_id": "panel.fault",
            "run_start_date": "2025-01-01",
            "run_end_date": "2025-01-03",
            "run_day_count": 3,
            "run_shape_class": "short_alert_run",
            "delta_run_class": "added_run",
            "overlapping_baseline_run_count": 0,
            "baseline_overlap_day_count": 0,
            "overlap_case_class": "unmatched_to_review",
            "overlapping_case_ids": "",
            "overlapping_case_types": "",
        },
        {
            "version": "current_seed_carry1",
            "site": "conalog",
            "panel_id": "panel.truth",
            "run_start_date": "2025-02-01",
            "run_end_date": "2025-02-03",
            "run_day_count": 3,
            "run_shape_class": "short_alert_run",
            "delta_run_class": "extended_run",
            "overlapping_baseline_run_count": 1,
            "baseline_overlap_day_count": 2,
            "overlap_case_class": "unmatched_to_review",
            "overlapping_case_ids": "",
            "overlapping_case_types": "",
        },
        {
            "version": "current_seed_carry1",
            "site": "gangui",
            "panel_id": "panel.recur",
            "run_start_date": "2025-03-01",
            "run_end_date": "2025-03-03",
            "run_day_count": 3,
            "run_shape_class": "short_alert_run",
            "delta_run_class": "added_run",
            "overlapping_baseline_run_count": 0,
            "baseline_overlap_day_count": 0,
            "overlap_case_class": "unmatched_to_review",
            "overlapping_case_ids": "",
            "overlapping_case_types": "",
        },
        {
            "version": "current_seed_carry1",
            "site": "gangui",
            "panel_id": "panel.iso",
            "run_start_date": "2025-04-01",
            "run_end_date": "2025-04-02",
            "run_day_count": 2,
            "run_shape_class": "short_alert_run",
            "delta_run_class": "extended_run",
            "overlapping_baseline_run_count": 1,
            "baseline_overlap_day_count": 1,
            "overlap_case_class": "unmatched_to_review",
            "overlapping_case_ids": "",
            "overlapping_case_types": "",
        },
    ]

    helper_conalog = [
        helper_row("conalog", "panel.fault", "2025-01-01", pre_alarm=1),
        helper_row("conalog", "panel.fault", "2025-01-02", pre_alarm=1),
        helper_row("conalog", "panel.fault", "2025-01-03", pre_alarm=1),
        helper_row("conalog", "panel.truth", "2025-02-01", pre_alarm=1),
        helper_row("conalog", "panel.truth", "2025-02-02", pre_alarm=1),
        helper_row("conalog", "panel.truth", "2025-02-03", pre_alarm=1),
        helper_row("conalog", "panel.truth", "2025-02-03", pre_alarm=1),  # exact duplicate
        helper_row("conalog", "panel.truth", "2025-05-01", pre_alarm=1),
        helper_row("conalog", "panel.truth", "2025-05-01", pre_alarm=0),  # conflicting duplicate outside relevant future
    ]
    helper_gangui = [
        helper_row("gangui", "panel.recur", "2025-03-01", pre_alarm=1),
        helper_row("gangui", "panel.recur", "2025-03-02", pre_alarm=1),
        helper_row("gangui", "panel.recur", "2025-03-03", pre_alarm=1),
        helper_row("gangui", "panel.recur", "2025-03-20", pre_alarm=1),
        helper_row("gangui", "panel.recur", "2025-03-21", pre_alarm=1),
        helper_row("gangui", "panel.iso", "2025-04-01", pre_alarm=1, cond_var=0, cond_dtw=0, ae_mid_or_hi_early=0),
        helper_row("gangui", "panel.iso", "2025-04-02", pre_alarm=1, cond_var=0, cond_dtw=0, ae_mid_or_hi_early=0),
    ]

    core_conalog = [
        core_row("panel.fault", "2025-01-10", final_fault=1, confirmed_fault=1),
        core_row("panel.truth", "2025-02-10"),
        core_row("panel.truth", "2025-02-20"),
    ]
    core_gangui = [
        core_row("panel.recur", "2025-03-10"),
        core_row("panel.iso", "2025-04-10"),
    ]

    write_csv(tmp_root / "_share" / "panel_day_engine_local_seed_carry_delta_run_registry_v1.csv", delta_rows, DELTA_COLS)
    write_csv(tmp_root / "data" / "conalog" / "out" / "ae_simple_local_precursor_gate_daily.csv", helper_conalog, HELPER_COLS)
    write_csv(tmp_root / "data" / "gangui" / "out" / "ae_simple_local_precursor_gate_daily.csv", helper_gangui, HELPER_COLS)
    write_csv(tmp_root / "data" / "conalog" / "out" / "panel_day_core.csv", core_conalog, CORE_COLS)
    write_csv(tmp_root / "data" / "gangui" / "out" / "panel_day_core.csv", core_gangui, CORE_COLS)
    write_csv(
        tmp_root / "_share" / "panel_date_reaudit_working.csv",
        [
            {
                "site": "conalog",
                "panel_id": "panel.truth",
                "strict_trigger_date": "2025-02-20",
                "candidate_validity": "false_positive",
            },
        ],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research" / "prognostics" / "build_panel_day_engine_local_seed_carry_fate_audit_v1.py"

    compile_result = run(
        [sys.executable, "-m", "py_compile", str(build_script), str(Path(__file__).resolve())],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr or "scripts should compile")
    print("[OK] scripts compile")

    with tempfile.TemporaryDirectory(prefix="seed_carry_fate_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)
        build_result = run([sys.executable, str(build_script), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout or "build should succeed")
        print("[OK] outputs generate")

        summary_df = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_local_seed_carry_fate_summary_v1.csv",
            encoding="utf-8-sig",
        )
        cases_df = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_local_seed_carry_fate_cases_v1.csv",
            encoding="utf-8-sig",
        )

        fault_row = cases_df.loc[cases_df["panel_id"].astype(str).eq("panel.fault")].iloc[0]
        assert_true(str(fault_row["fate_class"]) == "future_fault_linked", "future fault linkage classification should work")

        truth_row = cases_df.loc[cases_df["panel_id"].astype(str).eq("panel.truth")].iloc[0]
        assert_true(str(truth_row["fate_class"]) == "future_truth_linked", "future truth linkage classification should work")

        recur_row = cases_df.loc[cases_df["panel_id"].astype(str).eq("panel.recur")].iloc[0]
        assert_true(str(recur_row["fate_class"]) == "recurring_chronic_monitor_like", "recurrence classification should work")
        assert_true(int(recur_row["future_run_count_60d"]) == 1, "future run count should reflect later recurrence")

        iso_row = cases_df.loc[cases_df["panel_id"].astype(str).eq("panel.iso")].iloc[0]
        assert_true(str(iso_row["fate_class"]) == "isolated_unexplained", "isolated case classification should work")
        print("[OK] future fault / truth / recurrence / isolated classifications work")

        overall = summary_df.loc[summary_df["record_type"].astype(str).eq("overall")].iloc[0]
        assert_true(int(overall["selected_run_count"]) == 4, "summary selected count should be correct")
        assert_true(int(overall["future_fault_linked_count"]) == 1, "fault-linked summary count should be correct")
        assert_true(int(overall["future_truth_linked_count"]) == 1, "truth-linked summary count should be correct")
        assert_true(int(overall["recurring_chronic_monitor_like_count"]) == 1, "recurring summary count should be correct")
        assert_true(int(overall["isolated_unexplained_count"]) == 1, "isolated summary count should be correct")
        print("[OK] summary counts are correct")

        expected_outputs = {
            "panel_day_engine_local_seed_carry_fate_summary_v1.csv",
            "panel_day_engine_local_seed_carry_fate_cases_v1.csv",
        }
        actual_outputs = {path.name for path in (tmp_root / "_share").glob("*.csv")}
        assert_true(expected_outputs.issubset(actual_outputs), "expected outputs should be written")
        print("[OK] no official outputs are modified")


if __name__ == "__main__":
    main()
