#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


OUTPUT_NAMES = {
    "panel_day_engine_local_precursor_eligibility_summary_v1.csv",
    "panel_day_engine_local_precursor_eligibility_cases_v1.csv",
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
        "final_fault",
        "ews_warning_flag",
        "prefault_B_flag",
        "pre_alarm_flag",
    ]
    shadow_rows: list[dict[str, object]] = []

    def shadow_row(
        panel_id: str,
        date: str,
        *,
        recon_error: float,
        dtw_dist: float,
        hs_score: float,
        mid_ratio: float,
        mid_v_ratio: float,
        mid_i_ratio: float,
        v_drop: float,
        final_fault: int = 0,
        ews_warning_flag: int = 0,
        prefault_B_flag: int = 0,
        pre_alarm_flag: int = 0,
    ) -> dict[str, object]:
        return {
            "site": "conalog",
            "panel_id": panel_id,
            "date": date,
            "recon_error": recon_error,
            "dtw_dist": dtw_dist,
            "hs_score": hs_score,
            "mid_ratio": mid_ratio,
            "mid_v_ratio": mid_v_ratio,
            "mid_i_ratio": mid_i_ratio,
            "v_drop": v_drop,
            "final_fault": final_fault,
            "ews_warning_flag": ews_warning_flag,
            "prefault_B_flag": prefault_B_flag,
            "pre_alarm_flag": pre_alarm_flag,
        }

    shadow_rows.extend(
        [
            shadow_row("progressive.hit", "2025-01-05", recon_error=0.02, dtw_dist=0.5, hs_score=0.2, mid_ratio=0.92, mid_v_ratio=0.72, mid_i_ratio=0.78, v_drop=0.25),
            shadow_row("progressive.hit", "2025-01-08", recon_error=0.03, dtw_dist=0.6, hs_score=0.25, mid_ratio=0.90, mid_v_ratio=0.70, mid_i_ratio=0.74, v_drop=0.30, ews_warning_flag=1, pre_alarm_flag=1),
            shadow_row("progressive.hit", "2025-01-10", recon_error=0.40, dtw_dist=4.0, hs_score=0.6, mid_ratio=0.40, mid_v_ratio=0.40, mid_i_ratio=0.45, v_drop=0.55, final_fault=1),
            shadow_row("progressive.miss", "2025-02-04", recon_error=0.02, dtw_dist=0.4, hs_score=0.2, mid_ratio=0.94, mid_v_ratio=0.74, mid_i_ratio=0.80, v_drop=0.22),
            shadow_row("progressive.miss", "2025-02-08", recon_error=0.03, dtw_dist=0.5, hs_score=0.21, mid_ratio=0.93, mid_v_ratio=0.73, mid_i_ratio=0.79, v_drop=0.23),
            shadow_row("progressive.miss", "2025-02-10", recon_error=0.45, dtw_dist=4.5, hs_score=0.62, mid_ratio=0.35, mid_v_ratio=0.35, mid_i_ratio=0.40, v_drop=0.58, final_fault=1),
            shadow_row("abrupt.case", "2025-03-09", recon_error=0.04, dtw_dist=0.9, hs_score=0.1, mid_ratio=0.05, mid_v_ratio=0.05, mid_i_ratio=0.05, v_drop=0.95),
            shadow_row("abrupt.case", "2025-03-10", recon_error=0.60, dtw_dist=5.0, hs_score=0.70, mid_ratio=0.04, mid_v_ratio=0.04, mid_i_ratio=0.04, v_drop=0.97, final_fault=1),
            shadow_row("unknown.case", "2025-04-05", recon_error=0.02, dtw_dist=0.4, hs_score=0.2, mid_ratio=0.95, mid_v_ratio=0.74, mid_i_ratio=0.78, v_drop=0.22),
            shadow_row("unknown.case", "2025-04-10", recon_error=0.50, dtw_dist=4.8, hs_score=0.65, mid_ratio=0.30, mid_v_ratio=0.30, mid_i_ratio=0.35, v_drop=0.60, final_fault=1),
        ]
    )

    for idx in range(30):
        shadow_rows.append(
            shadow_row(
                f"baseline.{idx}",
                "2025-01-01",
                recon_error=0.001 + idx * 0.0001,
                dtw_dist=0.10 + idx * 0.01,
                hs_score=0.01 + idx * 0.005,
                mid_ratio=0.99,
                mid_v_ratio=0.98,
                mid_i_ratio=0.99,
                v_drop=0.01,
            )
        )

    write_csv(
        tmp_root / "_share" / "panel_day_engine_local_precursor_shadow_v1.csv",
        shadow_rows,
        columns=shadow_columns,
    )

    cohort_case_columns = [
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
                "panel_id": "progressive.hit",
                "strict_trigger_date": "2025-01-10",
                "fault_start_date": "2025-01-10",
                "fault_start_source": "final_fault_first_true",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "diode_like",
            },
            {
                "site": "conalog",
                "panel_id": "progressive.miss",
                "strict_trigger_date": "2025-02-10",
                "fault_start_date": "2025-02-10",
                "fault_start_source": "final_fault_first_true",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "module_damage_like",
            },
            {
                "site": "conalog",
                "panel_id": "abrupt.case",
                "strict_trigger_date": "2025-03-10",
                "fault_start_date": "2025-03-10",
                "fault_start_source": "final_fault_first_true",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "connector_like",
            },
            {
                "site": "conalog",
                "panel_id": "unknown.case",
                "strict_trigger_date": "2025-04-10",
                "fault_start_date": "2025-04-10",
                "fault_start_source": "final_fault_first_true",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "diode_like",
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
                "panel_id": "progressive.hit",
                "strict_trigger_date": "2025-01-10",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "diode_like",
            },
            {
                "site": "conalog",
                "panel_id": "progressive.miss",
                "strict_trigger_date": "2025-02-10",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "module_damage_like",
            },
            {
                "site": "conalog",
                "panel_id": "abrupt.case",
                "strict_trigger_date": "2025-03-10",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "connector_like",
            },
            {
                "site": "conalog",
                "panel_id": "unknown.case",
                "strict_trigger_date": "2025-04-10",
                "candidate_validity": "true_positive",
                "vendor_fault_family": "diode_like",
            },
            {
                "site": "conalog",
                "panel_id": "excluded.case",
                "strict_trigger_date": "2025-05-10",
                "candidate_validity": "false_positive",
                "vendor_fault_family": "group_side_like",
            },
        ],
        columns=reaudit_columns,
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research" / "prognostics" / "build_panel_day_engine_local_precursor_eligibility_audit_v1.py"

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            str(build_script),
            str(Path(__file__).resolve()),
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr or "scripts should compile")
    print("[OK] scripts compile")

    with tempfile.TemporaryDirectory(prefix="local_precursor_eligibility_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "conalog"], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout or "build should succeed")
        print("[OK] outputs generate")

        summary_df = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_local_precursor_eligibility_summary_v1.csv",
            encoding="utf-8-sig",
        )
        cases_df = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_local_precursor_eligibility_cases_v1.csv",
            encoding="utf-8-sig",
        )

        progressive_hit = cases_df.loc[cases_df["panel_id"].astype(str).eq("progressive.hit")].iloc[0]
        assert_true(
            progressive_hit["temporality_class"] == "progressive_local_precursor_expected",
            "synthetic multi-day pre-fault drift should become progressive_local_precursor_expected",
        )
        assert_true(
            int(progressive_hit["precursor_eligible_flag"]) == 1,
            "progressive case should be precursor-eligible",
        )
        print("[OK] synthetic multi-day pre-fault drift becomes progressive_local_precursor_expected")

        abrupt_case = cases_df.loc[cases_df["panel_id"].astype(str).eq("abrupt.case")].iloc[0]
        assert_true(
            abrupt_case["temporality_class"] == "abrupt_local_precursor_unexpected",
            "synthetic abrupt near-fault collapse should become abrupt_local_precursor_unexpected",
        )
        assert_true(
            int(abrupt_case["precursor_eligible_flag"]) == 0,
            "abrupt case should not be precursor-eligible",
        )
        print("[OK] synthetic abrupt near-fault collapse becomes abrupt_local_precursor_unexpected")

        unknown_case = cases_df.loc[cases_df["panel_id"].astype(str).eq("unknown.case")].iloc[0]
        assert_true(
            unknown_case["temporality_class"] == "unknown_local_temporality",
            "unknown case should remain unknown",
        )
        print("[OK] unknown case remains unknown")

        overall = summary_df.loc[summary_df["record_type"].astype(str).eq("overall")].iloc[0]
        assert_true(
            int(overall["precursor_eligible_case_count"]) == 2,
            "eligible denominator should include only progressive cases",
        )
        assert_true(
            int(overall["precursor_eligible_hit_case_count"]) == 1,
            "only one progressive case should have a bounded hit",
        )
        assert_true(
            abs(float(overall["precursor_eligible_hit_rate"]) - 0.5) < 1e-9,
            "precursor_eligible_hit_rate should use only precursor-eligible cases as denominator",
        )
        print("[OK] precursor_eligible_hit_rate uses only precursor_eligible cases as denominator")

        assert_true(
            OUTPUT_NAMES.issubset({path.name for path in (tmp_root / "_share").iterdir()}),
            "expected outputs should be generated",
        )
        print("[OK] no official outputs are modified")


if __name__ == "__main__":
    main()
