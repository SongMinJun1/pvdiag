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
            {
                "fault_family_id": "electrical_fault_like_progressive_local",
                "eval_bucket_v2": "precursor_bearing_detectable_now",
            },
            {
                "fault_family_id": "electrical_fault_like_abrupt_local",
                "eval_bucket_v2": "abrupt_or_no_precursor_now",
            },
            {
                "fault_family_id": "electrical_fault_like_unknown_local_temporality",
                "eval_bucket_v2": "unknown_needs_review",
            },
        ],
        ["fault_family_id", "eval_bucket_v2"],
    )

    write_csv(
        share / "panel_day_engine_precursor_onset_truth_v1.csv",
        [
            {
                "site": "alpha",
                "panel_id": "p1",
                "fault_start_date": "2025-01-20",
                "vendor_fault_family": "diode_like",
                "temporality_class": "progressive_local_precursor_expected",
                "operational_first_precursor_detected_date": "2025-01-10",
                "operational_first_precursor_marker_name": "first_cond_evt",
                "operational_lead_days_to_fault_start": 10,
                "interpretive_precursor_onset_date": "2025-01-10",
                "interpretive_lead_days_to_fault_start": 10,
                "benchmark_precursor_onset_date": "2025-01-10",
                "benchmark_lead_days_to_fault_start": 10,
                "preferred_precursor_onset_date": "2025-01-10",
                "preferred_onset_stage": "episode_start_before_alarm",
                "preferred_onset_confidence": "strong",
            },
            {
                "site": "beta",
                "panel_id": "p2",
                "fault_start_date": "2025-02-20",
                "vendor_fault_family": "module_damage_like",
                "temporality_class": "progressive_local_precursor_expected",
                "operational_first_precursor_detected_date": "2025-02-08",
                "operational_first_precursor_marker_name": "first_cond_evt",
                "operational_lead_days_to_fault_start": 12,
                "interpretive_precursor_onset_date": "2025-02-10",
                "interpretive_lead_days_to_fault_start": 10,
                "benchmark_precursor_onset_date": "2025-02-10",
                "benchmark_lead_days_to_fault_start": 10,
                "preferred_precursor_onset_date": "2025-02-10",
                "preferred_onset_stage": "episode_start_before_corroborated_signal",
                "preferred_onset_confidence": "medium",
            },
            {
                "site": "conalog",
                "panel_id": "c42997a6-5881-47e7-9035-7de8a2673b54.1.1",
                "fault_start_date": "2025-03-21",
                "vendor_fault_family": "open_or_device_issue_like",
                "temporality_class": "progressive_local_precursor_expected",
                "operational_first_precursor_detected_date": "2025-02-20",
                "operational_first_precursor_marker_name": "first_cond_evt",
                "operational_lead_days_to_fault_start": 29,
                "interpretive_precursor_onset_date": "2025-01-20",
                "interpretive_lead_days_to_fault_start": 60,
                "benchmark_precursor_onset_date": "2025-03-18",
                "benchmark_lead_days_to_fault_start": 3,
                "preferred_precursor_onset_date": "2025-03-18",
                "preferred_onset_stage": "episode_start_before_corroborated_signal",
                "preferred_onset_confidence": "medium",
            },
        ],
        [
            "site",
            "panel_id",
            "fault_start_date",
            "vendor_fault_family",
            "temporality_class",
            "operational_first_precursor_detected_date",
            "operational_first_precursor_marker_name",
            "operational_lead_days_to_fault_start",
            "interpretive_precursor_onset_date",
            "interpretive_lead_days_to_fault_start",
            "benchmark_precursor_onset_date",
            "benchmark_lead_days_to_fault_start",
            "preferred_precursor_onset_date",
            "preferred_onset_stage",
            "preferred_onset_confidence",
        ],
    )

    ladder_rows: list[dict[str, object]] = []
    def add_case_rows(site: str, panel_id: str, fault_start_date: str, marker_values: dict[str, tuple[str, int]]):
        for marker in [
            "first_cond_evt",
            "first_cond_evt_corroborated",
            "first_signalcount2",
            "first_pre_ews",
            "first_ews_warning",
            "first_pre_alarm",
        ]:
            if marker in marker_values:
                onset_date, available_flag = marker_values[marker]
                lead_days = (pd.Timestamp(fault_start_date) - pd.Timestamp(onset_date)).days
                ladder_rows.append(
                    {
                        "site": site,
                        "panel_id": panel_id,
                        "fault_start_date": fault_start_date,
                        "onset_marker": marker,
                        "onset_date": onset_date,
                        "lead_days": lead_days,
                        "available_flag": available_flag,
                    }
                )
            else:
                ladder_rows.append(
                    {
                        "site": site,
                        "panel_id": panel_id,
                        "fault_start_date": fault_start_date,
                        "onset_marker": marker,
                        "onset_date": "",
                        "lead_days": "",
                        "available_flag": 0,
                    }
                )

    add_case_rows(
        "alpha",
        "p1",
        "2025-01-20",
        {
            "first_cond_evt": ("2025-01-10", 1),
            "first_cond_evt_corroborated": ("2025-01-11", 1),
            "first_signalcount2": ("2025-01-14", 1),
            "first_ews_warning": ("2025-01-20", 1),
        },
    )
    add_case_rows(
        "beta",
        "p2",
        "2025-02-20",
        {
            "first_cond_evt": ("2025-02-08", 1),
            "first_cond_evt_corroborated": ("2025-02-10", 1),
            "first_signalcount2": ("2025-02-12", 1),
            "first_pre_ews": ("2025-02-09", 1),
        },
    )
    add_case_rows(
        "conalog",
        "c42997a6-5881-47e7-9035-7de8a2673b54.1.1",
        "2025-03-21",
        {
            "first_cond_evt": ("2025-03-18", 1),
            "first_cond_evt_corroborated": ("2025-03-19", 1),
            "first_signalcount2": ("2025-03-19", 1),
        },
    )

    write_csv(
        share / "panel_day_engine_precursor_onset_ladder_v1.csv",
        ladder_rows,
        ["site", "panel_id", "fault_start_date", "onset_marker", "onset_date", "lead_days", "available_flag"],
    )

    write_csv(
        share / "panel_day_engine_local_precursor_eligibility_cases_v1.csv",
        [
            {
                "site": "alpha",
                "panel_id": "p1",
                "fault_start_date": "2025-01-20",
                "vendor_fault_family": "diode_like",
                "temporality_class": "progressive_local_precursor_expected",
                "precursor_eligible_flag": 1,
            },
            {
                "site": "beta",
                "panel_id": "p2",
                "fault_start_date": "2025-02-20",
                "vendor_fault_family": "module_damage_like",
                "temporality_class": "progressive_local_precursor_expected",
                "precursor_eligible_flag": 1,
            },
            {
                "site": "conalog",
                "panel_id": "c42997a6-5881-47e7-9035-7de8a2673b54.1.1",
                "fault_start_date": "2025-03-21",
                "vendor_fault_family": "open_or_device_issue_like",
                "temporality_class": "progressive_local_precursor_expected",
                "precursor_eligible_flag": 1,
            },
        ],
        ["site", "panel_id", "fault_start_date", "vendor_fault_family", "temporality_class", "precursor_eligible_flag"],
    )

    write_csv(
        share / "panel_day_engine_fault_panel_event_audit_summary_v1.csv",
        [{"사건유형_재판정_전조형수": 3}],
        ["사건유형_재판정_전조형수"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_precursor_performance_audit_v1.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_precursor_performance_cases_v1.csv",
        repo_root / "_share" / "panel_day_engine_precursor_performance_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_precursor_performance_marker_comparison_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_precursor_performance_audit_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_precursor_performance_audit_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="precursor_performance_audit_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        cases_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_precursor_performance_cases_v1.csv", encoding="utf-8-sig")
        summary_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_precursor_performance_summary_v1.csv", encoding="utf-8-sig")
        comparison_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_precursor_performance_marker_comparison_v1.csv", encoding="utf-8-sig")

        assert_true(len(cases_df) == 3, "rebuilt precursor benchmark evaluation universe should contain 3 cases")

        p1 = cases_df.loc[cases_df["panel_id"].eq("p1")].iloc[0]
        assert_true(p1["first_cond_evt_onset_capture_class"] == "exact_or_earlier", "exact gap should map to exact_or_earlier")
        assert_true(int(float(p1["first_cond_evt_onset_capture_gap_days"])) == 0, "exact gap should be zero")
        assert_true(p1["first_cond_evt_corroborated_onset_capture_class"] == "within_3d_late", "1-day late should map to within_3d_late")
        assert_true(p1["first_signalcount2_onset_capture_class"] == "within_7d_late", "4-day late should map to within_7d_late")
        assert_true(p1["first_ews_warning_onset_capture_class"] == "late_over_7d", "10-day late should map to late_over_7d")
        assert_true(p1["first_pre_alarm_onset_capture_class"] == "missing", "missing marker should map to missing")

        p2 = cases_df.loc[cases_df["panel_id"].eq("p2")].iloc[0]
        assert_true(p2["first_cond_evt_onset_capture_class"] == "exact_or_earlier", "earlier marker should still map to exact_or_earlier")
        assert_true(int(float(p2["first_cond_evt_onset_capture_gap_days"])) == -2, "earlier marker should have negative gap")
        assert_true(p2["first_signalcount2_onset_capture_class"] == "within_3d_late", "2-day late should map to within_3d_late")

        c429 = cases_df.loc[
            cases_df["panel_id"].eq("c42997a6-5881-47e7-9035-7de8a2673b54.1.1")
        ].iloc[0]
        assert_true(c429["site"] == "conalog", "c429 should be included in rebuilt precursor benchmark cases")
        assert_true(str(c429["operational_first_precursor_detected_date"]) == "2025-02-20", "c429 operational first detection date should be carried through")
        assert_true(str(c429["operational_first_precursor_marker_name"]) == "first_cond_evt", "c429 operational first marker should be carried through")
        assert_true(int(float(c429["operational_lead_days_to_fault_start"])) == 29, "c429 operational lead days should be carried through")
        assert_true(str(c429["interpretive_precursor_onset_date"]) == "2025-01-20", "c429 interpretive onset should be carried through")
        assert_true(int(float(c429["interpretive_lead_days_to_fault_start"])) == 60, "c429 interpretive lead days should be carried through")
        assert_true(str(c429["benchmark_precursor_onset_date"]) == "2025-03-18", "c429 benchmark onset should be carried through")
        assert_true(int(float(c429["benchmark_lead_days_to_fault_start"])) == 3, "c429 benchmark lead days should be carried through")
        assert_true(
            c429["first_cond_evt_corroborated_onset_capture_class"] == "within_3d_late",
            "c429 corroborated marker should remain near the rebuilt preferred onset",
        )

        summary_map = {row["marker_name"]: row for row in summary_df.to_dict(orient="records")}
        first_cond_evt = summary_map["first_cond_evt"]
        assert_true(int(first_cond_evt["case_count"]) == 3, "summary case_count should match rebuilt benchmark universe")
        assert_true(int(first_cond_evt["available_case_count"]) == 3, "first_cond_evt should be available for all rebuilt precursor benchmark cases")
        assert_true(float(first_cond_evt["exact_or_earlier_rate"]) == 1.0, "first_cond_evt should be exact-or-earlier for all rebuilt benchmark cases")

        first_pre_alarm = summary_map["first_pre_alarm"]
        assert_true(int(first_pre_alarm["missing_count"]) == 3, "first_pre_alarm should be missing in all rebuilt synthetic cases")
        assert_true(float(first_pre_alarm["available_rate"]) == 0.0, "first_pre_alarm available_rate should be zero")

        corroborated = summary_map["first_cond_evt_corroborated"]
        assert_true(float(corroborated["exact_or_earlier_plus_within_3d_rate"]) == 1.0, "corroborated marker should be exact-or-earlier plus within_3d for both cases")

        assert_true(not comparison_df.empty, "marker comparison output should not be empty")
        assert_true(
            {"available_rate_rank", "median_lead_days_rank", "exact_or_earlier_rate_rank", "exact_or_earlier_plus_within_3d_rate_rank"}.issubset(comparison_df.columns),
            "comparison output should include ranking columns",
        )

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
