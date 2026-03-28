#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_common_inputs(
    tmp_root: Path,
    audit_summary_rows: list[dict[str, object]],
    forensics_summary_rows: list[dict[str, object]],
    forensics_day_rows: list[dict[str, object]],
    timing_rows: list[dict[str, object]],
) -> None:
    share_dir = tmp_root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(audit_summary_rows).to_csv(
        share_dir / "common_cause_precursor_audit_summary_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame(
        [
            {
                "tier_id": "broad_3g_10p",
                "site": row["site"],
                "date": row["date"],
            }
            for row in forensics_day_rows
        ]
    ).to_csv(
        share_dir / "common_cause_precursor_candidate_days_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame(
        [
            {
                "tier_id": "broad_3g_10p",
                "site": row["site"],
                "matched_episode_id": row.get("matched_episode_id", ""),
                "matched_trigger_mode": row.get("matched_trigger_mode", ""),
                "matched_episode_start_date": row.get("matched_episode_start_date", ""),
                "candidate_day_count_for_episode": 1,
                "earliest_candidate_date": row["date"],
                "latest_candidate_date": row["date"],
                "best_lead_days": row.get("days_to_episode_start", ""),
                "has_exact_same_day_candidate": int(row.get("precursor_timing_type") == "exact_same_day_episode"),
                "has_lead_1_to_3_candidate": int(row.get("precursor_timing_type") == "lead_1_to_3_days"),
                "has_lead_4_to_7_candidate": int(row.get("precursor_timing_type") == "lead_4_to_7_days"),
            }
            for row in forensics_day_rows
        ]
    ).to_csv(
        share_dir / "common_cause_precursor_episode_matches_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame(forensics_summary_rows).to_csv(
        share_dir / "common_cause_precursor_case_forensics_summary_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame(forensics_day_rows).to_csv(
        share_dir / "common_cause_precursor_case_forensics_days_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame(
        [
            {
                "site": row["site"],
                "date": row["date"],
                "fallback_group_proxy": f"{row['site']}.g0",
                "group_panel_count": 3,
                "zero_like_group_panel_count": 3,
                "group_like_zero_like_group_panel_count": 3,
                "group_panel_share_of_site_day": 0.12,
                "rank_by_group_like_zero_like_count": 1,
            }
            for row in forensics_day_rows
        ]
    ).to_csv(
        share_dir / "common_cause_precursor_case_forensics_groups_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame(timing_rows).to_csv(
        share_dir / "maintenance_proxy_event_timing_clusters_v2.csv",
        index=False,
        encoding="utf-8-sig",
    )


def scenario_strong_generalization(tmp_root: Path) -> None:
    audit_rows = [
        {
            "tier_id": "broad_3g_10p",
            "candidate_day_count": 8,
            "lead_1_to_3_precision": 0.60,
            "episode_lead_1_to_3_recall": 0.25,
        },
        {
            "tier_id": "medium_2g_5p",
            "candidate_day_count": 8,
            "lead_1_to_3_precision": 0.60,
            "episode_lead_1_to_3_recall": 0.25,
        },
        {
            "tier_id": "narrow_1g_3p",
            "candidate_day_count": 10,
            "lead_1_to_3_precision": 0.50,
            "episode_lead_1_to_3_recall": 0.25,
        },
    ]
    summary_rows = [
        {
            "record_type": "summary",
            "total_candidate_days": 6,
            "plausible_precursor_day_count": 4,
            "episode_aligned_day_count": 2,
            "likely_persistent_site_pattern_count": 0,
            "likely_sparse_site_pattern_count": 0,
            "ambiguous_case_count": 0,
            "conalog_candidate_day_count": 3,
            "ktc_ess_candidate_day_count": 0,
            "conalog_plausible_precursor_count": 2,
            "ktc_ess_plausible_precursor_count": 0,
            "ktc_ess_persistent_site_pattern_count": 0,
            "site": "",
            "candidate_day_count": "",
        },
        {
            "record_type": "site",
            "site": "conalog",
            "candidate_day_count": 3,
            "plausible_precursor_day_count": 2,
            "episode_aligned_day_count": 1,
            "likely_persistent_site_pattern_count": 0,
            "likely_sparse_site_pattern_count": 0,
            "ambiguous_case_count": 0,
        },
        {
            "record_type": "site",
            "site": "gangui",
            "candidate_day_count": 3,
            "plausible_precursor_day_count": 2,
            "episode_aligned_day_count": 1,
            "likely_persistent_site_pattern_count": 0,
            "likely_sparse_site_pattern_count": 0,
            "ambiguous_case_count": 0,
        },
        {"record_type": "site", "site": "ktc_ess", "candidate_day_count": 0, "plausible_precursor_day_count": 0, "episode_aligned_day_count": 0, "likely_persistent_site_pattern_count": 0, "likely_sparse_site_pattern_count": 0, "ambiguous_case_count": 0},
        {"record_type": "site", "site": "sinhyo", "candidate_day_count": 0, "plausible_precursor_day_count": 0, "episode_aligned_day_count": 0, "likely_persistent_site_pattern_count": 0, "likely_sparse_site_pattern_count": 0, "ambiguous_case_count": 0},
    ]
    day_rows = [
        {"site": "conalog", "date": "2025-01-10", "matched_episode_id": "ep1", "matched_trigger_mode": "medium_or_higher", "matched_episode_start_date": "2025-01-12", "days_to_episode_start": 2, "precursor_timing_type": "lead_1_to_3_days", "forensic_hypothesis": "plausible_precursor_day"},
        {"site": "conalog", "date": "2025-01-11", "matched_episode_id": "ep1", "matched_trigger_mode": "medium_or_higher", "matched_episode_start_date": "2025-01-12", "days_to_episode_start": 1, "precursor_timing_type": "lead_1_to_3_days", "forensic_hypothesis": "plausible_precursor_day"},
        {"site": "conalog", "date": "2025-01-12", "matched_episode_id": "ep1", "matched_trigger_mode": "medium_or_higher", "matched_episode_start_date": "2025-01-12", "days_to_episode_start": 0, "precursor_timing_type": "exact_same_day_episode", "forensic_hypothesis": "episode_aligned_day"},
        {"site": "gangui", "date": "2025-02-10", "matched_episode_id": "ep2", "matched_trigger_mode": "medium_or_higher", "matched_episode_start_date": "2025-02-12", "days_to_episode_start": 2, "precursor_timing_type": "lead_1_to_3_days", "forensic_hypothesis": "plausible_precursor_day"},
        {"site": "gangui", "date": "2025-02-11", "matched_episode_id": "ep2", "matched_trigger_mode": "medium_or_higher", "matched_episode_start_date": "2025-02-12", "days_to_episode_start": 1, "precursor_timing_type": "lead_1_to_3_days", "forensic_hypothesis": "plausible_precursor_day"},
        {"site": "gangui", "date": "2025-02-12", "matched_episode_id": "ep2", "matched_trigger_mode": "medium_or_higher", "matched_episode_start_date": "2025-02-12", "days_to_episode_start": 0, "precursor_timing_type": "exact_same_day_episode", "forensic_hypothesis": "episode_aligned_day"},
    ]
    timing_rows = [
        {"site": "conalog", "timing_overlap_type": "lead_before_episode"},
        {"site": "gangui", "timing_overlap_type": "lead_before_episode"},
    ]
    write_common_inputs(tmp_root, audit_rows, summary_rows, day_rows, timing_rows)


def scenario_observation_and_persistent(tmp_root: Path) -> None:
    audit_rows = [
        {
            "tier_id": "broad_3g_10p",
            "candidate_day_count": 6,
            "lead_1_to_3_precision": 0.30,
            "episode_lead_1_to_3_recall": 0.10,
        },
        {
            "tier_id": "medium_2g_5p",
            "candidate_day_count": 6,
            "lead_1_to_3_precision": 0.30,
            "episode_lead_1_to_3_recall": 0.10,
        },
        {
            "tier_id": "narrow_1g_3p",
            "candidate_day_count": 8,
            "lead_1_to_3_precision": 0.25,
            "episode_lead_1_to_3_recall": 0.10,
        },
    ]
    summary_rows = [
        {
            "record_type": "summary",
            "total_candidate_days": 6,
            "plausible_precursor_day_count": 2,
            "episode_aligned_day_count": 2,
            "likely_persistent_site_pattern_count": 2,
            "likely_sparse_site_pattern_count": 1,
            "ambiguous_case_count": 0,
            "conalog_candidate_day_count": 4,
            "ktc_ess_candidate_day_count": 2,
            "conalog_plausible_precursor_count": 2,
            "ktc_ess_plausible_precursor_count": 0,
            "ktc_ess_persistent_site_pattern_count": 2,
            "site": "",
            "candidate_day_count": "",
        },
        {
            "record_type": "site",
            "site": "conalog",
            "candidate_day_count": 4,
            "plausible_precursor_day_count": 2,
            "episode_aligned_day_count": 2,
            "likely_persistent_site_pattern_count": 0,
            "likely_sparse_site_pattern_count": 0,
            "ambiguous_case_count": 0,
        },
        {
            "record_type": "site",
            "site": "gangui",
            "candidate_day_count": 0,
            "plausible_precursor_day_count": 0,
            "episode_aligned_day_count": 0,
            "likely_persistent_site_pattern_count": 0,
            "likely_sparse_site_pattern_count": 0,
            "ambiguous_case_count": 0,
        },
        {
            "record_type": "site",
            "site": "ktc_ess",
            "candidate_day_count": 2,
            "plausible_precursor_day_count": 0,
            "episode_aligned_day_count": 0,
            "likely_persistent_site_pattern_count": 2,
            "likely_sparse_site_pattern_count": 1,
            "ambiguous_case_count": 0,
        },
        {
            "record_type": "site",
            "site": "sinhyo",
            "candidate_day_count": 0,
            "plausible_precursor_day_count": 0,
            "episode_aligned_day_count": 0,
            "likely_persistent_site_pattern_count": 0,
            "likely_sparse_site_pattern_count": 0,
            "ambiguous_case_count": 0,
        },
    ]
    day_rows = [
        {"site": "conalog", "date": "2025-01-10", "matched_episode_id": "ep1", "matched_trigger_mode": "medium_or_higher", "matched_episode_start_date": "2025-01-12", "days_to_episode_start": 2, "precursor_timing_type": "lead_1_to_3_days", "forensic_hypothesis": "plausible_precursor_day"},
        {"site": "conalog", "date": "2025-01-11", "matched_episode_id": "ep1", "matched_trigger_mode": "medium_or_higher", "matched_episode_start_date": "2025-01-12", "days_to_episode_start": 1, "precursor_timing_type": "lead_1_to_3_days", "forensic_hypothesis": "plausible_precursor_day"},
        {"site": "conalog", "date": "2025-01-12", "matched_episode_id": "ep1", "matched_trigger_mode": "medium_or_higher", "matched_episode_start_date": "2025-01-12", "days_to_episode_start": 0, "precursor_timing_type": "exact_same_day_episode", "forensic_hypothesis": "episode_aligned_day"},
        {"site": "conalog", "date": "2025-01-13", "matched_episode_id": "ep1", "matched_trigger_mode": "medium_or_higher", "matched_episode_start_date": "2025-01-12", "days_to_episode_start": -1, "precursor_timing_type": "in_episode_window", "forensic_hypothesis": "episode_aligned_day"},
        {"site": "ktc_ess", "date": "2025-02-20", "matched_episode_id": "epx", "matched_trigger_mode": "medium_or_higher", "matched_episode_start_date": "2025-01-01", "days_to_episode_start": -50, "precursor_timing_type": "no_episode_within_7d", "forensic_hypothesis": "likely_persistent_site_pattern"},
        {"site": "ktc_ess", "date": "2025-02-21", "matched_episode_id": "epx", "matched_trigger_mode": "medium_or_higher", "matched_episode_start_date": "2025-01-01", "days_to_episode_start": -51, "precursor_timing_type": "no_episode_within_7d", "forensic_hypothesis": "likely_persistent_site_pattern"},
    ]
    timing_rows = [{"site": "conalog", "timing_overlap_type": "lead_before_episode"}]
    write_common_inputs(tmp_root, audit_rows, summary_rows, day_rows, timing_rows)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_common_cause_precursor_decision_pack_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_common_cause_precursor_case_forensics_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        scenario_strong_generalization(tmp_root)
        res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(res.returncode == 0, f"strong scenario failed:\n{res.stdout}\n{res.stderr}")

        summary_df = pd.read_csv(tmp_root / "_share" / "common_cause_precursor_decision_summary_v1.csv", encoding="utf-8-sig")
        assert_true(
            summary_df.iloc[0]["global_recommendation"] == "consider_shadow_addon_next",
            "synthetic multi-site strong generalization should become consider_shadow_addon_next",
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        scenario_observation_and_persistent(tmp_root)
        res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(res.returncode == 0, f"observation scenario failed:\n{res.stdout}\n{res.stderr}")

        summary_df = pd.read_csv(tmp_root / "_share" / "common_cause_precursor_decision_summary_v1.csv", encoding="utf-8-sig")
        sites_df = pd.read_csv(tmp_root / "_share" / "common_cause_precursor_decision_sites_v1.csv", encoding="utf-8-sig")
        cases_df = pd.read_csv(tmp_root / "_share" / "common_cause_precursor_decision_cases_v1.csv", encoding="utf-8-sig")

        assert_true(not summary_df.empty, "summary output is empty")
        assert_true(not sites_df.empty, "site output is empty")
        assert_true(not cases_df.empty, "case output is empty")

        assert_true(
            summary_df.iloc[0]["global_recommendation"] == "keep_under_observation",
            "synthetic one-site plausible precursor should become keep_under_observation",
        )

        ktc_row = sites_df.loc[sites_df["site"].eq("ktc_ess")].iloc[0]
        assert_true(
            ktc_row["site_recommendation"] == "likely_site_pattern_not_generalizable",
            "synthetic persistent-only site should become likely_site_pattern_not_generalizable",
        )

        conalog_cases = cases_df.loc[cases_df["site"].eq("conalog")]
        assert_true(
            conalog_cases["include_in_site_specific_note_flag"].eq(1).all(),
            "site-specific note cases should be included for the plausible one-site signal",
        )
        ktc_cases = cases_df.loc[cases_df["site"].eq("ktc_ess")]
        assert_true(
            ktc_cases["include_in_site_specific_note_flag"].eq(0).all(),
            "persistent site-pattern cases should not be included in the site-specific note",
        )

        print("[OK] outputs generate")
        print("[OK] synthetic multi-site strong generalization becomes consider_shadow_addon_next")
        print("[OK] synthetic one-site plausible precursor becomes keep_under_observation")
        print("[OK] synthetic persistent-only site becomes likely_site_pattern_not_generalizable")
        print("[OK] no official outputs are modified")

    safe_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(safe_res.returncode == 0, f"existing safe smoke failed:\n{safe_res.stdout}\n{safe_res.stderr}")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
