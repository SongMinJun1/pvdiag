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
    write_text(tmp_root / "pv_ae" / "panel_day_engine.py", "# synthetic core\n")
    share_dir = tmp_root / "_share"

    write_csv(
        share_dir / "panel_day_engine_fault_taxonomy_v1.csv",
        [
            {
                "fault_family_id": "electrical_fault_like_progressive_local",
                "fault_family_name_ko": "점진 전조형",
                "family_group_ko": "전기 fault",
                "precursor_capable_flag": 1,
                "onset_labelable_flag": 1,
                "recommended_eval_bucket": "precursor_bearing",
                "evidence_source_files": "eligibility",
                "rationale_ko": "synthetic",
            },
            {
                "fault_family_id": "none_visible_or_unconfirmed",
                "fault_family_name_ko": "none visible",
                "family_group_ko": "other",
                "precursor_capable_flag": 0,
                "onset_labelable_flag": 0,
                "recommended_eval_bucket": "abrupt_or_no_precursor",
                "evidence_source_files": "eligibility",
                "rationale_ko": "synthetic",
            },
        ],
        [
            "fault_family_id",
            "fault_family_name_ko",
            "family_group_ko",
            "precursor_capable_flag",
            "onset_labelable_flag",
            "recommended_eval_bucket",
            "evidence_source_files",
            "rationale_ko",
        ],
    )

    write_csv(
        share_dir / "panel_day_engine_local_precursor_eligibility_cases_v1.csv",
        [
            {
                "site": "alpha",
                "panel_id": "p_strong",
                "fault_start_date": "2025-01-10",
                "vendor_fault_family": "diode_like",
                "temporality_class": "progressive_local_precursor_expected",
                "precursor_eligible_flag": 1,
            },
            {
                "site": "alpha",
                "panel_id": "p_medium",
                "fault_start_date": "2025-02-10",
                "vendor_fault_family": "module_damage_like",
                "temporality_class": "progressive_local_precursor_expected",
                "precursor_eligible_flag": 1,
            },
            {
                "site": "beta",
                "panel_id": "p_weak",
                "fault_start_date": "2025-03-10",
                "vendor_fault_family": "diode_like",
                "temporality_class": "progressive_local_precursor_expected",
                "precursor_eligible_flag": 1,
            },
            {
                "site": "beta",
                "panel_id": "p_none",
                "fault_start_date": "2025-04-10",
                "vendor_fault_family": "diode_like",
                "temporality_class": "progressive_local_precursor_expected",
                "precursor_eligible_flag": 1,
            },
            {
                "site": "alpha",
                "panel_id": "p_skip",
                "fault_start_date": "2025-05-10",
                "vendor_fault_family": "diode_like",
                "temporality_class": "abrupt_local_precursor_unexpected",
                "precursor_eligible_flag": 0,
            },
        ],
        [
            "site",
            "panel_id",
            "fault_start_date",
            "vendor_fault_family",
            "temporality_class",
            "precursor_eligible_flag",
        ],
    )

    write_csv(
        tmp_root / "data" / "alpha" / "out" / "ae_simple_local_precursor_gate_daily.csv",
        [
            {"site": "alpha", "panel_id": "p_strong", "date": "2025-01-03", "cond_var": 0, "cond_evt": 1, "cond_dtw": 0, "cond_hs": 0, "pre_ews": 0, "signal_count": 1, "ews_warning": 0, "pre_alarm": 0},
            {"site": "alpha", "panel_id": "p_strong", "date": "2025-01-04", "cond_var": 0, "cond_evt": 1, "cond_dtw": 0, "cond_hs": 0, "pre_ews": 0, "signal_count": 1, "ews_warning": 0, "pre_alarm": 0},
            {"site": "alpha", "panel_id": "p_strong", "date": "2025-01-06", "cond_var": 1, "cond_evt": 1, "cond_dtw": 0, "cond_hs": 0, "pre_ews": 1, "signal_count": 2, "ews_warning": 0, "pre_alarm": 0},
            {"site": "alpha", "panel_id": "p_strong", "date": "2025-01-08", "cond_var": 1, "cond_evt": 1, "cond_dtw": 0, "cond_hs": 0, "pre_ews": 1, "signal_count": 2, "ews_warning": 1, "pre_alarm": 1},
            {"site": "alpha", "panel_id": "p_medium", "date": "2025-01-31", "cond_var": 0, "cond_evt": 1, "cond_dtw": 0, "cond_hs": 0, "pre_ews": 0, "signal_count": 1, "ews_warning": 0, "pre_alarm": 0},
            {"site": "alpha", "panel_id": "p_medium", "date": "2025-02-01", "cond_var": 0, "cond_evt": 1, "cond_dtw": 0, "cond_hs": 1, "pre_ews": 0, "signal_count": 2, "ews_warning": 0, "pre_alarm": 0},
        ],
        ["site", "panel_id", "date", "cond_var", "cond_evt", "cond_dtw", "cond_hs", "pre_ews", "signal_count", "ews_warning", "pre_alarm"],
    )

    write_csv(
        tmp_root / "data" / "beta" / "out" / "ae_simple_local_precursor_gate_daily.csv",
        [
            {"site": "beta", "panel_id": "p_weak", "date": "2025-03-05", "cond_var": 0, "cond_evt": 1, "cond_dtw": 0, "cond_hs": 0, "pre_ews": 0, "signal_count": 1, "ews_warning": 0, "pre_alarm": 0},
            {"site": "beta", "panel_id": "p_none", "date": "2025-04-05", "cond_var": 0, "cond_evt": 0, "cond_dtw": 0, "cond_hs": 0, "pre_ews": 1, "signal_count": 0, "ews_warning": 0, "pre_alarm": 0},
        ],
        ["site", "panel_id", "date", "cond_var", "cond_evt", "cond_dtw", "cond_hs", "pre_ews", "signal_count", "ews_warning", "pre_alarm"],
    )

    write_csv(
        tmp_root / "data" / "alpha" / "out" / "panel_day_core.csv",
        [
            {"panel_id": "p_strong", "date": "2025-01-03"},
            {"panel_id": "p_strong", "date": "2025-01-04"},
            {"panel_id": "p_strong", "date": "2025-01-06"},
            {"panel_id": "p_strong", "date": "2025-01-08"},
            {"panel_id": "p_medium", "date": "2025-01-31"},
            {"panel_id": "p_medium", "date": "2025-02-01"},
        ],
        ["panel_id", "date"],
    )
    write_csv(
        tmp_root / "data" / "beta" / "out" / "panel_day_core.csv",
        [
            {"panel_id": "p_weak", "date": "2025-03-05"},
            {"panel_id": "p_none", "date": "2025-04-05"},
        ],
        ["panel_id", "date"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_precursor_onset_truth_v1.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_precursor_onset_truth_v1.csv",
        repo_root / "_share" / "panel_day_engine_precursor_onset_ladder_v1.csv",
        repo_root / "_share" / "panel_day_engine_precursor_onset_summary_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_precursor_onset_truth_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_precursor_onset_truth_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="precursor_onset_truth_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        truth_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_precursor_onset_truth_v1.csv", encoding="utf-8-sig")
        ladder_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_precursor_onset_ladder_v1.csv", encoding="utf-8-sig")
        summary_df = pd.read_csv(tmp_root / "_share" / "panel_day_engine_precursor_onset_summary_v1.csv", encoding="utf-8-sig")

        assert_true(len(truth_df) == 4, "only precursor-bearing eligible cases should be emitted")

        strong = truth_df.loc[truth_df["panel_id"].eq("p_strong")].iloc[0]
        assert_true(strong["selected_episode_start_date"] == "2025-01-03", "1-day gap episode chaining should preserve early episode start")
        assert_true(strong["selected_episode_end_date"] == "2025-01-08", "selected episode end should follow chained latest cond_evt day")
        assert_true(strong["preferred_onset_stage"] == "episode_start_before_alarm", "strong case should pick alarm-backed stage")
        assert_true(int(strong["lead_days_from_preferred_onset_to_fault_start"]) == 7, "strong lead days should be computed from preferred onset")

        medium = truth_df.loc[truth_df["panel_id"].eq("p_medium")].iloc[0]
        assert_true(
            medium["preferred_onset_stage"] == "episode_start_before_corroborated_signal",
            "medium case should pick corroborated stage",
        )
        assert_true(int(medium["lead_days_from_preferred_onset_to_fault_start"]) == 10, "medium lead days should be correct")

        weak = truth_df.loc[truth_df["panel_id"].eq("p_weak")].iloc[0]
        assert_true(weak["preferred_onset_stage"] == "episode_start_evt_only", "weak case should pick evt-only stage")
        assert_true(int(weak["lead_days_from_preferred_onset_to_fault_start"]) == 5, "weak lead days should be correct")

        none_case = truth_df.loc[truth_df["panel_id"].eq("p_none")].iloc[0]
        assert_true(
            none_case["preferred_onset_stage"] == "no_detectable_precursor_episode",
            "case without cond_evt episode should have no-detectable stage",
        )
        assert_true(pd.isna(none_case["lead_days_from_preferred_onset_to_fault_start"]), "no-episode case should not have lead days")

        preferred_rows = ladder_df.loc[ladder_df["onset_marker"].eq("preferred_precursor_onset")].copy()
        assert_true(len(preferred_rows) == 4, "ladder should emit one preferred onset row per case")
        assert_true(
            int(preferred_rows.loc[preferred_rows["panel_id"].eq("p_none"), "available_flag"].iloc[0]) == 0,
            "no-episode case should have unavailable preferred onset",
        )

        summary_marker_names = set(summary_df["marker_name"].astype(str))
        assert_true("first_cond_evt" in summary_marker_names, "summary should include onset marker rows")
        assert_true("preferred_onset_confidence" in summary_marker_names, "summary should include confidence distribution")
        assert_true("preferred_onset_stage" in summary_marker_names, "summary should include stage distribution")

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()
