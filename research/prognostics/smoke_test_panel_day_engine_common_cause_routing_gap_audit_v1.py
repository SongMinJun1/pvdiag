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
                "fault_family_id": "group_or_inverter_side_like",
                "fault_family_name_ko": "group",
                "family_group_ko": "common",
                "literature_precursor_capable_flag": 1,
                "current_pipeline_detectable_flag": 0,
                "preferred_sensor_modality": "inverter_or_system_level",
                "eval_bucket_v2": "non_panel_or_common_cause",
                "eval_bucket_reason_ko": "synthetic",
            }
        ],
        [
            "fault_family_id",
            "fault_family_name_ko",
            "family_group_ko",
            "literature_precursor_capable_flag",
            "current_pipeline_detectable_flag",
            "preferred_sensor_modality",
            "eval_bucket_v2",
            "eval_bucket_reason_ko",
        ],
    )

    write_csv(
        share / "panel_date_reaudit_working.csv",
        [
            {
                "site": "alpha",
                "panel_id": "breadth_case",
                "strict_trigger_date": "2025-01-10",
                "first_warning_date": "",
                "retrospective_onset_date": "",
                "candidate_validity": "group_side",
                "vendor_fault_family": "group_or_inverter_side_like",
                "vendor_reply_class": "field_confirmed_positive",
            },
            {
                "site": "alpha",
                "panel_id": "misaligned_case",
                "strict_trigger_date": "2025-02-10",
                "first_warning_date": "",
                "retrospective_onset_date": "",
                "candidate_validity": "group_side",
                "vendor_fault_family": "group_or_inverter_side_like",
                "vendor_reply_class": "field_confirmed_positive",
            },
            {
                "site": "alpha",
                "panel_id": "local_case",
                "strict_trigger_date": "2025-03-10",
                "first_warning_date": "",
                "retrospective_onset_date": "",
                "candidate_validity": "group_side",
                "vendor_fault_family": "group_or_inverter_side_like",
                "vendor_reply_class": "field_confirmed_positive",
            },
            {
                "site": "alpha",
                "panel_id": "weak_case",
                "strict_trigger_date": "2025-04-10",
                "first_warning_date": "",
                "retrospective_onset_date": "",
                "candidate_validity": "group_side",
                "vendor_fault_family": "group_or_inverter_side_like",
                "vendor_reply_class": "field_confirmed_positive",
            },
        ],
        [
            "site",
            "panel_id",
            "strict_trigger_date",
            "first_warning_date",
            "retrospective_onset_date",
            "candidate_validity",
            "vendor_fault_family",
            "vendor_reply_class",
        ],
    )

    core_rows: list[dict[str, object]] = []
    gate_rows: list[dict[str, object]] = []

    for panel_idx in range(10):
        panel = f"breadth_extra_{panel_idx}"
        core_rows.append(
            {"panel_id": panel, "date": "2025-01-10", "final_fault": 1 if panel_idx < 2 else 0, "group_off_like": 0, "shadow_like": 0}
        )
        gate_rows.append(
            {"site": "alpha", "panel_id": panel, "date": "2025-01-10", "group_off_date": 0, "ews_warning": 0, "pre_alarm": 1 if panel_idx < 2 else 0}
        )
    core_rows.append({"panel_id": "breadth_case", "date": "2025-01-10", "final_fault": 1, "group_off_like": 0, "shadow_like": 0})
    gate_rows.append({"site": "alpha", "panel_id": "breadth_case", "date": "2025-01-10", "group_off_date": 0, "ews_warning": 0, "pre_alarm": 1})

    for panel_idx in range(8):
        panel = f"misaligned_extra_{panel_idx}"
        core_rows.append({"panel_id": panel, "date": "2025-02-10", "final_fault": 0, "group_off_like": 0, "shadow_like": 0})
        gate_rows.append({"site": "alpha", "panel_id": panel, "date": "2025-02-10", "group_off_date": 0, "ews_warning": 0, "pre_alarm": 0})
    core_rows.append({"panel_id": "misaligned_case", "date": "2025-02-15", "final_fault": 0, "group_off_like": 1, "shadow_like": 0})
    gate_rows.append({"site": "alpha", "panel_id": "misaligned_case", "date": "2025-02-15", "group_off_date": 0, "ews_warning": 0, "pre_alarm": 0})

    for panel_idx in range(20):
        panel = f"local_extra_{panel_idx}"
        core_rows.append({"panel_id": panel, "date": "2025-03-10", "final_fault": 0, "group_off_like": 0, "shadow_like": 0})
        gate_rows.append({"site": "alpha", "panel_id": panel, "date": "2025-03-10", "group_off_date": 0, "ews_warning": 0, "pre_alarm": 0})
    core_rows.append({"panel_id": "local_case", "date": "2025-03-10", "final_fault": 1, "group_off_like": 0, "shadow_like": 0})
    gate_rows.append({"site": "alpha", "panel_id": "local_case", "date": "2025-03-10", "group_off_date": 0, "ews_warning": 0, "pre_alarm": 0})

    for panel_idx in range(12):
        panel = f"weak_extra_{panel_idx}"
        core_rows.append({"panel_id": panel, "date": "2025-04-10", "final_fault": 0, "group_off_like": 0, "shadow_like": 0})
        gate_rows.append({"site": "alpha", "panel_id": panel, "date": "2025-04-10", "group_off_date": 0, "ews_warning": 0, "pre_alarm": 0})
    core_rows.append({"panel_id": "weak_case", "date": "2025-04-10", "final_fault": 0, "group_off_like": 0, "shadow_like": 0})
    gate_rows.append({"site": "alpha", "panel_id": "weak_case", "date": "2025-04-10", "group_off_date": 0, "ews_warning": 0, "pre_alarm": 0})

    write_csv(
        tmp_root / "data" / "alpha" / "out" / "panel_day_core.csv",
        core_rows,
        ["panel_id", "date", "final_fault", "group_off_like", "shadow_like"],
    )
    write_csv(
        tmp_root / "data" / "alpha" / "out" / "ae_simple_local_precursor_gate_daily.csv",
        gate_rows,
        ["site", "panel_id", "date", "group_off_date", "ews_warning", "pre_alarm"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_common_cause_routing_gap_audit_v1.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_common_cause_routing_gap_cases_v1.csv",
        repo_root / "_share" / "panel_day_engine_common_cause_routing_gap_days_v1.csv",
        repo_root / "_share" / "panel_day_engine_common_cause_routing_gap_summary_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_common_cause_routing_gap_audit_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_common_cause_routing_gap_audit_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="common_cause_routing_gap_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        cases_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_common_cause_routing_gap_cases_v1.csv", encoding="utf-8-sig")
        days_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_common_cause_routing_gap_days_v1.csv", encoding="utf-8-sig")
        summary_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_common_cause_routing_gap_summary_v1.csv", encoding="utf-8-sig")

        case_class = dict(zip(cases_df["panel_id"], cases_df["routing_gap_class"]))
        assert_true(case_class["breadth_case"] == "breadth_without_current_marker", "breadth case should classify as breadth_without_current_marker")
        assert_true(case_class["misaligned_case"] == "current_marker_present_but_misaligned_window", "misaligned case should classify as misaligned window")
        assert_true(case_class["local_case"] == "local_fault_like_not_common_cause_like", "local case should classify as local_fault_like_not_common_cause_like")
        assert_true(case_class["weak_case"] == "weak_or_sparse_signal", "weak case should classify as weak_or_sparse_signal")

        breadth_case = cases_df.loc[cases_df["panel_id"].eq("breadth_case")].iloc[0]
        assert_true(float(breadth_case["max_final_fault_panel_fraction"]) > 0.1, "breadth case should show broad final_fault fraction")

        day_row = days_df.loc[(days_df["panel_id"].eq("breadth_case")) & (days_df["date"].eq("2025-01-10"))].iloc[0]
        assert_true(int(day_row["site_panel_count_on_date"]) == 11, "site_panel_count_on_date should reflect all site panels in scope")
        assert_true(int(day_row["final_fault_panel_count_on_date"]) == 3, "final_fault_panel_count_on_date should count breadth panels correctly")
        assert_true(float(day_row["pre_alarm_panel_fraction_on_date"]) > 0.1, "pre_alarm fraction should compute correctly")

        overall_summary = summary_df.loc[summary_df["record_type"].eq("overall")].iloc[0]
        assert_true(int(overall_summary["case_count"]) == 4, "summary case count should match synthetic cases")
        assert_true(int(overall_summary["breadth_without_current_marker_count"]) == 1, "summary breadth class count should be correct")
        assert_true(int(overall_summary["weak_or_sparse_signal_count"]) == 1, "summary weak class count should be correct")

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
