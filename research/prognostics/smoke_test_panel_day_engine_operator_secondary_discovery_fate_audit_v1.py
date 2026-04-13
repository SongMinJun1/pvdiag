#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DISCOVERY_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "logistic_v3_discovery_score",
    "electrical_core_minus_broadshape_050",
    "global_discovery_rank",
    "site_discovery_rank",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "mean_signal_count",
    "max_signal_count",
    "p95_recon_error",
    "discovery_reason_ko",
]
TRUTH_COLS = ["site", "panel_id", "strict_trigger_date", "candidate_validity"]
HELPER_COLS = ["panel_id", "date", "pre_ews", "ews_warning", "pre_alarm"]
CORE_COLS = ["panel_id", "date", "confirmed_fault", "critical_fault", "final_fault"]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture_root(tmp_root: Path) -> None:
    share_dir = tmp_root / "_share"
    data_dir = tmp_root / "data" / "alpha" / "out"
    data_dir.mkdir(parents=True, exist_ok=True)

    discovery_rows = [
        {
            "site": "alpha",
            "panel_id": "fault.panel",
            "run_start_date": "2025-01-01",
            "run_end_date": "2025-01-02",
            "run_day_count": 2,
            "run_shape_class": "short_alert_run",
            "logistic_v3_discovery_score": 0.95,
            "electrical_core_minus_broadshape_050": 4.2,
            "global_discovery_rank": 1,
            "site_discovery_rank": 1,
            "max_v_drop": 0.70,
            "min_mid_v_ratio": 0.40,
            "min_mid_ratio": 0.42,
            "cond_evt_only_day_ratio": 0.80,
            "ae_mid_or_hi_early_day_ratio": 0.75,
            "mean_signal_count": 2.0,
            "max_signal_count": 3.0,
            "p95_recon_error": 0.08,
            "discovery_reason_ko": "fault candidate",
        },
        {
            "site": "alpha",
            "panel_id": "truth.panel",
            "run_start_date": "2025-02-01",
            "run_end_date": "2025-02-02",
            "run_day_count": 2,
            "run_shape_class": "short_alert_run",
            "logistic_v3_discovery_score": 0.90,
            "electrical_core_minus_broadshape_050": 3.8,
            "global_discovery_rank": 2,
            "site_discovery_rank": 2,
            "max_v_drop": 0.60,
            "min_mid_v_ratio": 0.45,
            "min_mid_ratio": 0.47,
            "cond_evt_only_day_ratio": 0.70,
            "ae_mid_or_hi_early_day_ratio": 0.60,
            "mean_signal_count": 1.8,
            "max_signal_count": 2.0,
            "p95_recon_error": 0.07,
            "discovery_reason_ko": "truth candidate",
        },
        {
            "site": "alpha",
            "panel_id": "recur.panel",
            "run_start_date": "2025-03-01",
            "run_end_date": "2025-03-03",
            "run_day_count": 3,
            "run_shape_class": "chronic_alert_run",
            "logistic_v3_discovery_score": 0.85,
            "electrical_core_minus_broadshape_050": 3.0,
            "global_discovery_rank": 3,
            "site_discovery_rank": 3,
            "max_v_drop": 0.50,
            "min_mid_v_ratio": 0.55,
            "min_mid_ratio": 0.58,
            "cond_evt_only_day_ratio": 0.55,
            "ae_mid_or_hi_early_day_ratio": 0.50,
            "mean_signal_count": 2.5,
            "max_signal_count": 3.0,
            "p95_recon_error": 0.06,
            "discovery_reason_ko": "recurrence candidate",
        },
        {
            "site": "alpha",
            "panel_id": "iso.panel",
            "run_start_date": "2025-04-01",
            "run_end_date": "2025-04-05",
            "run_day_count": 5,
            "run_shape_class": "medium_alert_run",
            "logistic_v3_discovery_score": 0.80,
            "electrical_core_minus_broadshape_050": 2.6,
            "global_discovery_rank": 4,
            "site_discovery_rank": 4,
            "max_v_drop": 0.40,
            "min_mid_v_ratio": 0.65,
            "min_mid_ratio": 0.68,
            "cond_evt_only_day_ratio": 0.40,
            "ae_mid_or_hi_early_day_ratio": 0.35,
            "mean_signal_count": 1.5,
            "max_signal_count": 2.0,
            "p95_recon_error": 0.05,
            "discovery_reason_ko": "isolated candidate",
        },
    ]

    truth_rows = [
        {
            "site": "alpha",
            "panel_id": "truth.panel",
            "strict_trigger_date": "2025-02-15",
            "candidate_validity": "true_positive",
        },
    ]

    helper_rows = [
        {"panel_id": "fault.panel", "date": "2025-01-01", "pre_ews": 1, "ews_warning": 0, "pre_alarm": 0},
        {"panel_id": "fault.panel", "date": "2025-01-02", "pre_ews": 1, "ews_warning": 1, "pre_alarm": 0},
        {"panel_id": "truth.panel", "date": "2025-02-01", "pre_ews": 1, "ews_warning": 0, "pre_alarm": 0},
        {"panel_id": "truth.panel", "date": "2025-02-02", "pre_ews": 1, "ews_warning": 0, "pre_alarm": 0},
        {"panel_id": "recur.panel", "date": "2025-03-01", "pre_ews": 1, "ews_warning": 0, "pre_alarm": 0},
        {"panel_id": "recur.panel", "date": "2025-03-02", "pre_ews": 1, "ews_warning": 1, "pre_alarm": 0},
        {"panel_id": "recur.panel", "date": "2025-03-03", "pre_ews": 1, "ews_warning": 0, "pre_alarm": 0},
        {"panel_id": "recur.panel", "date": "2025-03-15", "pre_ews": 1, "ews_warning": 1, "pre_alarm": 0},
        {"panel_id": "recur.panel", "date": "2025-03-16", "pre_ews": 1, "ews_warning": 0, "pre_alarm": 0},
        {"panel_id": "iso.panel", "date": "2025-04-01", "pre_ews": 1, "ews_warning": 0, "pre_alarm": 0},
        {"panel_id": "iso.panel", "date": "2025-04-02", "pre_ews": 1, "ews_warning": 0, "pre_alarm": 0},
    ]

    core_rows = [
        {"panel_id": "fault.panel", "date": "2025-01-20", "confirmed_fault": 1, "critical_fault": 0, "final_fault": 1},
        {"panel_id": "truth.panel", "date": "2025-02-20", "confirmed_fault": 0, "critical_fault": 0, "final_fault": 0},
        {"panel_id": "recur.panel", "date": "2025-03-20", "confirmed_fault": 0, "critical_fault": 0, "final_fault": 0},
        {"panel_id": "iso.panel", "date": "2025-04-20", "confirmed_fault": 0, "critical_fault": 0, "final_fault": 0},
    ]

    write_csv(share_dir / "panel_day_engine_operator_secondary_discovery_v1.csv", discovery_rows, DISCOVERY_COLS)
    write_csv(share_dir / "panel_date_reaudit_working.csv", truth_rows, TRUTH_COLS)
    write_csv(data_dir / "ae_simple_local_precursor_gate_daily.csv", helper_rows, HELPER_COLS)
    write_csv(data_dir / "panel_day_core.csv", core_rows, CORE_COLS)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research" / "prognostics" / "build_panel_day_engine_operator_secondary_discovery_fate_audit_v1.py"

    py_compile.compile(str(repo_root / "pv_ae" / "panel_day_engine.py"), doraise=True)
    py_compile.compile(str(builder), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="secondary-discovery-fate-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        result = run([sys.executable, str(builder), "--root", str(tmp_root)], cwd=repo_root)
        if result.returncode != 0:
            raise SystemExit(f"builder failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        cases_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_fate_cases_v1.csv"
        summary_path = tmp_root / "_share" / "panel_day_engine_operator_secondary_discovery_fate_summary_v1.csv"
        assert_true(cases_path.exists(), "missing fate case output")
        assert_true(summary_path.exists(), "missing fate summary output")

        cases_df = pd.read_csv(cases_path, encoding="utf-8-sig")
        summary_df = pd.read_csv(summary_path, encoding="utf-8-sig")
        assert_true(len(cases_df) == 4, "should emit one row per discovery run")

        by_panel = {row["panel_id"]: row for row in cases_df.to_dict("records")}
        assert_true(str(by_panel["fault.panel"]["discovery_fate_class"]) == "future_fault_linked", "future fault linkage classification should work")
        assert_true(int(by_panel["fault.panel"]["future_final_fault_30d"]) == 1, "future final fault 30d should be set")

        assert_true(str(by_panel["truth.panel"]["discovery_fate_class"]) == "future_truth_linked", "future truth linkage classification should work")
        assert_true(int(by_panel["truth.panel"]["future_truth_overlap_30d"]) == 1, "future truth overlap 30d should be set")
        assert_true("true_positive" in str(by_panel["truth.panel"]["future_truth_candidate_validities"]), "truth validity should be carried")

        assert_true(str(by_panel["recur.panel"]["discovery_fate_class"]) == "recurring_monitor_like", "recurrence classification should work")
        assert_true(int(by_panel["recur.panel"]["recurring_run_within_30d"]) == 1, "recurrence within 30d should be set")
        assert_true(int(by_panel["recur.panel"]["future_run_count_60d"]) == 1, "future run count 60d should count helper-derived later runs")

        assert_true(str(by_panel["iso.panel"]["discovery_fate_class"]) == "isolated_unexplained", "isolated classification should work")

        overall = summary_df.loc[summary_df["record_type"].astype(str).eq("overall")].iloc[0]
        assert_true(int(overall["future_fault_linked_count"]) == 1, "future fault summary count should be correct")
        assert_true(int(overall["future_truth_linked_count"]) == 1, "future truth summary count should be correct")
        assert_true(int(overall["recurring_monitor_like_count"]) == 1, "recurring summary count should be correct")
        assert_true(int(overall["isolated_unexplained_count"]) == 1, "isolated summary count should be correct")
        assert_true(round(float(overall["short_run_isolated_rate"]), 6) == 0.0, "short run isolated rate should be correct")
        assert_true(round(float(overall["short_run_fault_or_truth_linked_rate"]), 6) == 1.0, "short run fault/truth linked rate should be correct")

    print("smoke_test_panel_day_engine_operator_secondary_discovery_fate_audit_v1.py: PASS")


if __name__ == "__main__":
    main()
