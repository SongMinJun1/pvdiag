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


def write_common_live_inputs(tmp_root: Path) -> list[Path]:
    share_dir = tmp_root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    input_paths: list[Path] = []

    f1_df = pd.DataFrame(
        [
            {"truth_mode": "strict", "prediction_mode": "maintenance", "source_split": "overall", "f1": 0.61},
            {"truth_mode": "strict", "prediction_mode": "operational", "source_split": "overall", "f1": 0.91},
            {"truth_mode": "lenient", "prediction_mode": "maintenance", "source_split": "overall", "f1": 0.72},
            {"truth_mode": "lenient", "prediction_mode": "operational", "source_split": "overall", "f1": 0.95},
        ]
    )
    path = share_dir / "full_algorithm_f1_summary_v3.csv"
    f1_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    score_scope_summary_df = pd.DataFrame(
        [
            {
                "record_type": "summary",
                "total_strict_cases": 20,
                "official_scored_count": 7,
                "manual_scored_count": 6,
                "vendor_scored_count": 1,
                "deferred_unlabeled_high_actionability_count": 2,
                "deferred_unlabeled_other_count": 10,
                "excluded_labeled_needs_more_info_count": 1,
                "excluded_vendor_no_info_count": 0,
                "excluded_other_count": 0,
                "site": "",
                "total_cases": 20,
            }
        ]
    )
    path = share_dir / "score_scope_manifest_summary_v1.csv"
    score_scope_summary_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    score_scope_sites_df = pd.DataFrame(
        [
            {
                "site": "conalog",
                "total_cases": 10,
                "official_scored_count": 4,
                "manual_scored_count": 4,
                "vendor_scored_count": 0,
                "deferred_unlabeled_high_actionability_count": 0,
                "deferred_unlabeled_other_count": 6,
                "recommended_site_handling": "continue_scoring_normally",
            },
            {
                "site": "gangui",
                "total_cases": 8,
                "official_scored_count": 2,
                "manual_scored_count": 1,
                "vendor_scored_count": 1,
                "deferred_unlabeled_high_actionability_count": 2,
                "deferred_unlabeled_other_count": 4,
                "recommended_site_handling": "score_with_deferred_note",
            },
            {
                "site": "ktc_ess",
                "total_cases": 2,
                "official_scored_count": 1,
                "manual_scored_count": 1,
                "vendor_scored_count": 0,
                "deferred_unlabeled_high_actionability_count": 0,
                "deferred_unlabeled_other_count": 1,
                "recommended_site_handling": "continue_scoring_normally",
            },
        ]
    )
    path = share_dir / "score_scope_manifest_sites_v1.csv"
    score_scope_sites_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    deferred_summary_df = pd.DataFrame(
        [
            {
                "record_type": "summary",
                "original_batch_count": 2,
                "deferred_hold_count": 2,
                "active_batch_v2_count": 0,
                "deferred_site_count": 1,
                "site": "",
                "active_batch_v2_count_after_hold": "",
                "site_handling_recommendation": "",
            },
            {
                "record_type": "site",
                "original_batch_count": "",
                "deferred_hold_count": 0,
                "active_batch_v2_count": "",
                "deferred_site_count": "",
                "site": "conalog",
                "active_batch_v2_count_after_hold": 0,
                "site_handling_recommendation": "no_deferred_hold_rows",
            },
            {
                "record_type": "site",
                "original_batch_count": "",
                "deferred_hold_count": 2,
                "active_batch_v2_count": "",
                "deferred_site_count": "",
                "site": "gangui",
                "active_batch_v2_count_after_hold": 0,
                "site_handling_recommendation": "keep_on_hold_until_field_evidence",
            },
            {
                "record_type": "site",
                "original_batch_count": "",
                "deferred_hold_count": 0,
                "active_batch_v2_count": "",
                "deferred_site_count": "",
                "site": "ktc_ess",
                "active_batch_v2_count_after_hold": 0,
                "site_handling_recommendation": "no_deferred_hold_rows",
            },
        ]
    )
    path = share_dir / "truth_review_deferred_summary_v1.csv"
    deferred_summary_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    precursor_summary_df = pd.DataFrame(
        [
            {
                "global_recommendation": "keep_under_observation",
                "global_decision_reason": "Promising local slice exists, but global generalization is still too weak.",
                "primary_tier_used": "broad_3g_10p",
            }
        ]
    )
    path = share_dir / "common_cause_precursor_decision_summary_v1.csv"
    precursor_summary_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    precursor_sites_df = pd.DataFrame(
        [
            {
                "site": "conalog",
                "candidate_day_count": 4,
                "plausible_precursor_day_count": 2,
                "episode_aligned_day_count": 2,
                "likely_persistent_site_pattern_count": 0,
                "likely_sparse_site_pattern_count": 0,
                "ambiguous_case_count": 0,
                "site_recommendation": "keep_site_specific_precursor_note",
                "site_decision_reason": "Conalog still has a defensible site-specific precursor note only.",
            },
            {
                "site": "gangui",
                "candidate_day_count": 0,
                "plausible_precursor_day_count": 0,
                "episode_aligned_day_count": 0,
                "likely_persistent_site_pattern_count": 0,
                "likely_sparse_site_pattern_count": 0,
                "ambiguous_case_count": 0,
                "site_recommendation": "no_precursor_signal",
                "site_decision_reason": "No precursor signal is retained for gangui.",
            },
            {
                "site": "ktc_ess",
                "candidate_day_count": 2,
                "plausible_precursor_day_count": 0,
                "episode_aligned_day_count": 0,
                "likely_persistent_site_pattern_count": 2,
                "likely_sparse_site_pattern_count": 1,
                "ambiguous_case_count": 0,
                "site_recommendation": "likely_site_pattern_not_generalizable",
                "site_decision_reason": "ktc_ess still looks like a site-pattern line, not a precursor line.",
            },
        ]
    )
    path = share_dir / "common_cause_precursor_decision_sites_v1.csv"
    precursor_sites_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    active_batch_df = pd.DataFrame(
        columns=[
            "round1_review_order",
            "round1_bucket_rank",
            "site",
            "panel_id",
            "strict_trigger_date",
            "review_priority_bucket",
        ]
    )
    path = share_dir / "truth_review_active_batch_v2.csv"
    active_batch_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    return input_paths


def freeze_current_baseline(tmp_root: Path, root: Path, freeze_script: Path) -> None:
    freeze_res = run(
        [sys.executable, str(freeze_script), "--root", str(tmp_root), "--sites", "conalog", "gangui", "ktc_ess"],
        root,
    )
    assert_true(freeze_res.returncode == 0, f"freeze build failed:\n{freeze_res.stdout}\n{freeze_res.stderr}")


def snapshot_bytes(paths: list[Path]) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in paths}


def assert_bytes_unchanged(before: dict[Path, bytes]) -> None:
    for path, expected in before.items():
        current = path.read_bytes()
        if current != expected:
            raise SystemExit(f"input file changed unexpectedly: {path.name}")


def run_guard(tmp_root: Path, root: Path, guard_script: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    guard_res = run(
        [sys.executable, str(guard_script), "--root", str(tmp_root), "--sites", "conalog", "gangui", "ktc_ess"],
        root,
    )
    assert_true(guard_res.returncode == 0, f"guard build failed:\n{guard_res.stdout}\n{guard_res.stderr}")
    share_dir = tmp_root / "_share"
    summary_df = pd.read_csv(share_dir / "baseline_regression_guard_summary_v1.csv", encoding="utf-8-sig")
    sites_df = pd.read_csv(share_dir / "baseline_regression_guard_sites_v1.csv", encoding="utf-8-sig")
    diffs_df = pd.read_csv(share_dir / "baseline_regression_guard_diffs_v1.csv", encoding="utf-8-sig")
    return summary_df, sites_df, diffs_df


def scenario_preserved(root: Path, freeze_script: Path, guard_script: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        input_paths = write_common_live_inputs(tmp_root)
        freeze_current_baseline(tmp_root, root, freeze_script)
        before = snapshot_bytes(input_paths)

        summary_df, sites_df, diffs_df = run_guard(tmp_root, root, guard_script)
        assert_true(len(summary_df) == 1, "guard summary should have exactly one row")
        summary_row = summary_df.iloc[0]
        assert_true(
            summary_row["guard_status"] == "frozen_baseline_preserved",
            "identical synthetic frozen/current inputs should preserve the frozen baseline",
        )
        assert_true(int(summary_row["total_diff_count"]) == 0, "identical inputs should produce zero diffs")
        assert_true(diffs_df.empty, "identical inputs should not emit diff rows")
        assert_true(
            sites_df["site_guard_status"].eq("preserved").all(),
            "all site rows should be preserved when synthetic inputs are identical",
        )
        assert_bytes_unchanged(before)


def scenario_metric_drift(root: Path, freeze_script: Path, guard_script: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        write_common_live_inputs(tmp_root)
        freeze_current_baseline(tmp_root, root, freeze_script)

        f1_path = tmp_root / "_share" / "full_algorithm_f1_summary_v3.csv"
        f1_df = pd.read_csv(f1_path, encoding="utf-8-sig")
        mask = (
            f1_df["truth_mode"].astype(str).str.strip().eq("strict")
            & f1_df["prediction_mode"].astype(str).str.strip().eq("maintenance")
            & f1_df["source_split"].astype(str).str.strip().eq("overall")
        )
        f1_df.loc[mask, "f1"] = 0.5
        f1_df.to_csv(f1_path, index=False, encoding="utf-8-sig")

        summary_df, _sites_df, diffs_df = run_guard(tmp_root, root, guard_script)
        summary_row = summary_df.iloc[0]
        assert_true(
            summary_row["guard_status"] == "drift_detected",
            "synthetic metric drift should produce drift_detected",
        )
        overall_diffs = diffs_df.loc[diffs_df["diff_scope"].eq("overall")].copy()
        assert_true(not overall_diffs.empty, "synthetic metric drift should emit overall diff rows")
        assert_true(
            overall_diffs["diff_key"].astype(str).eq("strict_maintenance_f1").any(),
            "synthetic metric drift should flag strict_maintenance_f1",
        )


def scenario_site_status_drift(root: Path, freeze_script: Path, guard_script: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        write_common_live_inputs(tmp_root)
        freeze_current_baseline(tmp_root, root, freeze_script)

        precursor_sites_path = tmp_root / "_share" / "common_cause_precursor_decision_sites_v1.csv"
        precursor_sites_df = pd.read_csv(precursor_sites_path, encoding="utf-8-sig")
        precursor_sites_df.loc[
            precursor_sites_df["site"].astype(str).str.strip().eq("conalog"),
            "site_recommendation",
        ] = "no_precursor_signal"
        precursor_sites_df.to_csv(precursor_sites_path, index=False, encoding="utf-8-sig")

        _summary_df, sites_df, diffs_df = run_guard(tmp_root, root, guard_script)
        site_diffs = diffs_df.loc[diffs_df["diff_scope"].eq("site")].copy()
        assert_true(not site_diffs.empty, "synthetic site-status drift should emit site diff rows")
        assert_true(
            site_diffs["site"].astype(str).eq("conalog").any(),
            "synthetic site-status drift should flag conalog",
        )
        conalog_row = sites_df.loc[sites_df["site"].astype(str).eq("conalog")].iloc[0]
        assert_true(
            conalog_row["site_guard_status"] == "drift_detected",
            "conalog should be marked drift_detected when the site status changes",
        )


def scenario_decision_drift(root: Path, freeze_script: Path, guard_script: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        write_common_live_inputs(tmp_root)
        freeze_current_baseline(tmp_root, root, freeze_script)

        precursor_sites_path = tmp_root / "_share" / "common_cause_precursor_decision_sites_v1.csv"
        precursor_sites_df = pd.read_csv(precursor_sites_path, encoding="utf-8-sig")
        precursor_sites_df.loc[
            precursor_sites_df["site"].astype(str).str.strip().eq("conalog"),
            "site_decision_reason",
        ] = "Updated wording only for the conalog note."
        precursor_sites_df.to_csv(precursor_sites_path, index=False, encoding="utf-8-sig")

        _summary_df, _sites_df, diffs_df = run_guard(tmp_root, root, guard_script)
        decision_diffs = diffs_df.loc[diffs_df["diff_scope"].eq("decision")].copy()
        assert_true(not decision_diffs.empty, "synthetic decision drift should emit decision diff rows")
        assert_true(
            decision_diffs["diff_key"].astype(str).eq("conalog_precursor_note.decision_reason").any(),
            "synthetic decision drift should flag conalog_precursor_note.decision_reason",
        )


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    freeze_script = root / "research" / "prognostics" / "build_baseline_freeze_pack_v1.py"
    guard_script = root / "research" / "prognostics" / "build_baseline_regression_guard_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_baseline_freeze_pack_v1.py"

    compile_res = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            str(guard_script),
            str(Path(__file__).resolve()),
        ],
        root,
    )
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    scenario_preserved(root, freeze_script, guard_script)
    scenario_metric_drift(root, freeze_script, guard_script)
    scenario_site_status_drift(root, freeze_script, guard_script)
    scenario_decision_drift(root, freeze_script, guard_script)

    print("[OK] outputs generate")
    print("[OK] identical synthetic frozen/current inputs produce frozen_baseline_preserved and zero diffs")
    print("[OK] synthetic metric drift produces drift_detected with overall diff rows")
    print("[OK] synthetic site-status drift produces site diff rows")
    print("[OK] synthetic decision drift produces decision diff rows")
    print("[OK] no official outputs are modified")

    safe_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(safe_res.returncode == 0, f"existing safe smoke failed:\n{safe_res.stdout}\n{safe_res.stderr}")
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
