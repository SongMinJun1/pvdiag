#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import py_compile
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


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_fixture(root: Path) -> None:
    share = root / "_share"
    share.mkdir(parents=True, exist_ok=True)

    write_csv(
        share / "panel_day_engine_precursor_onset_truth_v1.csv",
        [
            {
                "site": "siteA",
                "panel_id": "panel_same",
                "fault_start_date": "2025-01-10",
                "selected_episode_end_date": "2025-01-09",
                "preferred_precursor_onset_date": "2025-01-01",
            },
            {
                "site": "siteB",
                "panel_id": "panel_distinct",
                "fault_start_date": "2025-01-10",
                "selected_episode_end_date": "2025-01-09",
                "preferred_precursor_onset_date": "2025-01-01",
            },
        ],
        [
            "site",
            "panel_id",
            "fault_start_date",
            "selected_episode_end_date",
            "preferred_precursor_onset_date",
        ],
    )

    write_csv(
        share / "panel_day_engine_abrupt6_symptom_map_v1.csv",
        [
            {"site": "siteA", "panel_id": "panel_same", "고장시점": "2025-01-10"},
            {"site": "siteB", "panel_id": "panel_distinct", "고장시점": "2025-03-10"},
        ],
        ["site", "panel_id", "고장시점"],
    )

    write_csv(
        share / "panel_day_engine_non_precursor_performance_cases_v1.csv",
        [
            {
                "site": "siteA",
                "panel_id": "panel_same",
                "anchor_date": "2025-01-10",
                "first_confirmed_fault_date": "",
                "first_critical_fault_date": "",
                "first_final_fault_date": "",
            },
            {
                "site": "siteB",
                "panel_id": "panel_distinct",
                "anchor_date": "2025-03-10",
                "first_confirmed_fault_date": "",
                "first_critical_fault_date": "",
                "first_final_fault_date": "",
            },
        ],
        [
            "site",
            "panel_id",
            "anchor_date",
            "first_confirmed_fault_date",
            "first_critical_fault_date",
            "first_final_fault_date",
        ],
    )

    write_csv(
        share / "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        [
            {
                "site": "siteA",
                "panel_id": "panel_same",
                "패널고장여부_ko": "고장",
                "전조형이력_flag": 1,
                "급작고장이력_flag": 1,
            },
            {
                "site": "siteB",
                "panel_id": "panel_distinct",
                "패널고장여부_ko": "고장",
                "전조형이력_flag": 1,
                "급작고장이력_flag": 1,
            },
        ],
        ["site", "panel_id", "패널고장여부_ko", "전조형이력_flag", "급작고장이력_flag"],
    )

    write_csv(
        share / "panel_day_engine_panel_multiaxis_event_supplement_v1.csv",
        [
            {"site": "siteA", "panel_id": "panel_same", "사건유형_ko": "전조형 고장"},
            {"site": "siteA", "panel_id": "panel_same", "사건유형_ko": "급작 고장"},
            {"site": "siteB", "panel_id": "panel_distinct", "사건유형_ko": "전조형 고장"},
            {"site": "siteB", "panel_id": "panel_distinct", "사건유형_ko": "급작 고장"},
        ],
        ["site", "panel_id", "사건유형_ko"],
    )

    write_csv(
        share / "panel_date_reaudit_working.csv",
        [
            {
                "site": "siteA",
                "panel_id": "panel_same",
                "strict_trigger_date": "2025-01-10",
                "first_warning_date": "2025-01-02",
                "retrospective_onset_date": "2025-01-02",
            },
            {
                "site": "siteB",
                "panel_id": "panel_distinct",
                "strict_trigger_date": "2025-03-10",
                "first_warning_date": "2025-01-02",
                "retrospective_onset_date": "2025-01-02",
            },
        ],
        ["site", "panel_id", "strict_trigger_date", "first_warning_date", "retrospective_onset_date"],
    )

    for site, panel_id, hard_dates in [
        ("siteA", "panel_same", {"2025-01-10", "2025-01-11"}),
        ("siteB", "panel_distinct", {"2025-03-10", "2025-03-11"}),
    ]:
        rows = []
        for date in ["2025-01-01", "2025-01-09", "2025-01-10", "2025-03-10", "2025-03-11"]:
            hard = date in hard_dates
            rows.append(
                {
                    "date": date,
                    "panel_id": panel_id,
                    "confirmed_fault": hard,
                    "critical_fault": hard,
                    "final_fault": hard,
                }
            )
        write_csv(
            root / "data" / site / "out" / "panel_day_core.csv",
            rows,
            ["date", "panel_id", "confirmed_fault", "critical_fault", "final_fault"],
        )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research/prognostics/build_panel_day_engine_precursor_abrupt_consistency_audit_v1.py"
    smoke_script = repo_root / "research/prognostics/smoke_test_panel_day_engine_precursor_abrupt_consistency_audit_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        repo_root / "_share/panel_day_engine_precursor_abrupt_consistency_cases_v1.csv",
        repo_root / "_share/panel_day_engine_precursor_abrupt_consistency_summary_v1.csv",
        repo_root / "_share/panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="panel_day_engine_precursor_abrupt_consistency_smoke_") as tmp_dir:
        root = Path(tmp_dir)
        build_fixture(root)

        result = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(result.returncode == 0, f"builder failed: {result.stderr or result.stdout}")

        cases_df = pd.read_csv(root / "_share/panel_day_engine_precursor_abrupt_consistency_cases_v1.csv", low_memory=False, encoding="utf-8-sig")
        summary_df = pd.read_csv(root / "_share/panel_day_engine_precursor_abrupt_consistency_summary_v1.csv", low_memory=False, encoding="utf-8-sig")
        recommendation_df = pd.read_csv(root / "_share/panel_day_engine_precursor_abrupt_consistency_recommendation_v1.csv", low_memory=False, encoding="utf-8-sig")

        assert_true(len(cases_df) == 2, f"expected 2 overlap cases, found {len(cases_df)}")
        same_row = cases_df.loc[cases_df["panel_id"].eq("panel_same")].iloc[0]
        distinct_row = cases_df.loc[cases_df["panel_id"].eq("panel_distinct")].iloc[0]
        assert_true(int(same_row["same_event_flag"]) == 1, "same-event fixture row should be marked same_event")
        assert_true(int(same_row["distinct_event_flag"]) == 0, "same-event fixture row should not be marked distinct_event")
        assert_true(same_row["consistency_judgment_ko"] == "같은 사건", "same-event judgment mismatch")
        assert_true(int(distinct_row["same_event_flag"]) == 0, "distinct-event fixture row should not be marked same_event")
        assert_true(int(distinct_row["distinct_event_flag"]) == 1, "distinct-event fixture row should be marked distinct_event")
        assert_true(distinct_row["consistency_judgment_ko"] == "별도 사건", "distinct-event judgment mismatch")

        summary_row = summary_df.iloc[0]
        assert_true(int(summary_row["overlap_panel_count"]) == 2, "summary overlap count mismatch")
        assert_true(int(summary_row["same_event_count"]) == 1, "summary same-event count mismatch")
        assert_true(int(summary_row["distinct_event_count"]) == 1, "summary distinct-event count mismatch")
        assert_true(int(summary_row["ambiguous_count"]) == 0, "summary ambiguous count mismatch")
        assert_true(int(summary_row["current_unique_fault_panel_count"]) == 2, "summary current fault count mismatch")
        assert_true(int(summary_row["current_precursor_event_count"]) == 2, "summary precursor count mismatch")
        assert_true(int(summary_row["current_abrupt_event_count"]) == 2, "summary abrupt count mismatch")
        assert_true(int(summary_row["corrected_precursor_led_fault_count"]) == 1, "summary corrected precursor-led count mismatch")
        assert_true(int(summary_row["corrected_pure_abrupt_fault_count"]) == 1, "summary corrected pure abrupt count mismatch")

        recommendation_row = recommendation_df.iloc[0]
        assert_true(
            recommendation_row["recommended_next_handling"] == "keep_overlap_as_ambiguous_until_manual_review",
            "mixed synthetic fixture should recommend manual review",
        )

    after = {path: file_digest(path) for path in official_outputs}
    assert_true(before == after, "official outputs changed during smoke test")


if __name__ == "__main__":
    main()
