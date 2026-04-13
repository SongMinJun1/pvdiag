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


def git(tmp_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], tmp_root)


def write_inputs(tmp_root: Path) -> list[Path]:
    share_dir = tmp_root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    (tmp_root / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_root / "research" / "prognostics").mkdir(parents=True, exist_ok=True)

    input_paths: list[Path] = []

    handoff_summary_df = pd.DataFrame(
        [
            {
                "baseline_guard_status": "frozen_baseline_preserved",
                "freeze_recommendation": "baseline_frozen_ready",
                "strict_maintenance_f1": 0.615384,
                "strict_operational_f1": 1.0,
                "lenient_maintenance_f1": 0.615384,
                "lenient_operational_f1": 1.0,
                "official_scored_count": 13,
                "manual_scored_count": 13,
                "vendor_scored_count": 0,
                "deferred_hold_count": 10,
                "active_review_queue_count": 0,
                "precursor_global_recommendation": "keep_under_observation",
                "next_workstream_recommendation": "safe_to_switch_topic",
            }
        ]
    )
    path = share_dir / "workstream_handoff_summary_v1.csv"
    handoff_summary_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    handoff_sites_df = pd.DataFrame(
        [
            {
                "site": "conalog",
                "site_status": "scored_with_site_specific_precursor_note",
                "official_scored_count": 7,
                "manual_scored_count": 7,
                "vendor_scored_count": 0,
                "deferred_hold_count": 0,
                "precursor_site_recommendation": "keep_site_specific_precursor_note",
                "handoff_note_ko": "공식 score는 유지하고 precursor site note만 관찰용으로 넘깁니다.",
            },
            {
                "site": "gangui",
                "site_status": "scored_with_deferred_hold",
                "official_scored_count": 4,
                "manual_scored_count": 4,
                "vendor_scored_count": 0,
                "deferred_hold_count": 10,
                "precursor_site_recommendation": "no_precursor_signal",
                "handoff_note_ko": "공식 score는 유지하고 deferred hold 행은 증거 전까지 보류합니다.",
            },
        ]
    )
    path = share_dir / "workstream_handoff_sites_v1.csv"
    handoff_sites_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    handoff_open_threads_df = pd.DataFrame(
        [
            {
                "thread_key": "gangui_deferred_high_actionability",
                "thread_status": "on_hold",
                "owner_needed": "field_or_OM_review",
                "reactivation_condition": "field_or_OM_evidence_available",
                "note_ko": "deferred hold",
            },
            {
                "thread_key": "conalog_site_specific_precursor_note",
                "thread_status": "observation_only",
                "owner_needed": "analysis_review",
                "reactivation_condition": "repeated_multi_site_evidence",
                "note_ko": "site note only",
            },
            {
                "thread_key": "precursor_global_addon",
                "thread_status": "not_adopted",
                "owner_needed": "future_research",
                "reactivation_condition": "precision_and_recall_thresholds_met",
                "note_ko": "not adopted",
            },
            {
                "thread_key": "baseline_regression_guard",
                "thread_status": "active_guard",
                "owner_needed": "any_future_workstream",
                "reactivation_condition": "run_before_reporting_or_topic_switch",
                "note_ko": "rerun before reporting",
            },
        ]
    )
    path = share_dir / "workstream_handoff_open_threads_v1.csv"
    handoff_open_threads_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    guard_summary_df = pd.DataFrame(
        [
            {
                "guard_status": "frozen_baseline_preserved",
                "overall_diff_count": 0,
                "site_diff_count": 0,
                "decision_diff_count": 0,
                "total_diff_count": 0,
            }
        ]
    )
    path = share_dir / "baseline_regression_guard_summary_v1.csv"
    guard_summary_df.to_csv(path, index=False, encoding="utf-8-sig")
    input_paths.append(path)

    for rel_path in [
        Path("research/prognostics/build_site_event_dataset.py"),
        Path("research/prognostics/smoke_test_site_event_dataset.py"),
    ]:
        abs_path = tmp_root / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text("# placeholder\n", encoding="utf-8")
        input_paths.append(abs_path)

    return input_paths


def init_repo(tmp_root: Path) -> list[Path]:
    input_paths = write_inputs(tmp_root)

    init_res = git(tmp_root, ["init", "-q"])
    assert_true(init_res.returncode == 0, f"git init failed:\n{init_res.stdout}\n{init_res.stderr}")

    branch_res = git(tmp_root, ["checkout", "-b", "smoke-branch"])
    assert_true(branch_res.returncode == 0, f"git checkout failed:\n{branch_res.stdout}\n{branch_res.stderr}")

    email_res = git(tmp_root, ["config", "user.email", "smoke@example.com"])
    name_res = git(tmp_root, ["config", "user.name", "Smoke Test"])
    assert_true(email_res.returncode == 0, f"git config email failed:\n{email_res.stdout}\n{email_res.stderr}")
    assert_true(name_res.returncode == 0, f"git config name failed:\n{name_res.stdout}\n{name_res.stderr}")

    add_res = git(tmp_root, ["add", "."])
    assert_true(add_res.returncode == 0, f"git add failed:\n{add_res.stdout}\n{add_res.stderr}")

    commit_res = git(tmp_root, ["commit", "-m", "init"])
    assert_true(commit_res.returncode == 0, f"git commit failed:\n{commit_res.stdout}\n{commit_res.stderr}")
    return input_paths


def snapshot_bytes(paths: list[Path]) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in paths}


def assert_bytes_unchanged(before: dict[Path, bytes]) -> None:
    for path, expected in before.items():
        current = path.read_bytes()
        if current != expected:
            raise SystemExit(f"input file changed unexpectedly: {path}")


def run_builder(tmp_root: Path, build_script: Path, root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    build_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
    assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

    share_dir = tmp_root / "_share"
    summary_df = pd.read_csv(share_dir / "merge_readiness_summary_v1.csv", encoding="utf-8-sig")
    worktree_df = pd.read_csv(share_dir / "merge_readiness_worktree_v1.csv", encoding="utf-8-sig")
    actions_df = pd.read_csv(share_dir / "merge_readiness_actions_v1.csv", encoding="utf-8-sig")
    return summary_df, worktree_df, actions_df


def scenario_clean(root: Path, build_script: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        input_paths = init_repo(tmp_root)
        before = snapshot_bytes(input_paths)

        summary_df, worktree_df, actions_df = run_builder(tmp_root, build_script, root)
        summary_row = summary_df.iloc[0]
        assert_true(
            str(summary_row["merge_readiness_status"]).strip() == "ready_for_merge_or_archive",
            "clean synthetic status should yield ready_for_merge_or_archive",
        )
        assert_true(worktree_df.empty, "clean synthetic repo should produce no worktree rows")
        assert_true(len(actions_df) == 5, "actions output should always contain five rows")
        assert_true(str(summary_row["current_branch"]).strip() == "smoke-branch", "branch metadata should be captured")
        assert_true(str(summary_row["head_commit_short"]).strip() != "", "head commit short should be captured")
        assert_bytes_unchanged(before)


def scenario_generated_share_only(root: Path, build_script: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        init_repo(tmp_root)
        generated_path = tmp_root / "_share" / "scratch_output.csv"
        generated_path.write_text("x\n1\n", encoding="utf-8")

        summary_df, worktree_df, _actions_df = run_builder(tmp_root, build_script, root)
        summary_row = summary_df.iloc[0]
        assert_true(
            str(summary_row["merge_readiness_status"]).strip()
            == "ready_after_ignoring_generated_and_known_unrelated",
            "generated _share only should yield ready_after_ignoring_generated_and_known_unrelated",
        )
        assert_true(
            worktree_df["worktree_class"].astype(str).eq("generated_share_artifact").all(),
            "generated _share only scenario should classify every row as generated_share_artifact",
        )


def scenario_current_workstream_dirty(root: Path, build_script: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        init_repo(tmp_root)
        dirty_path = tmp_root / "docs" / "current_workstream_note.md"
        dirty_path.write_text("dirty\n", encoding="utf-8")

        summary_df, worktree_df, _actions_df = run_builder(tmp_root, build_script, root)
        summary_row = summary_df.iloc[0]
        assert_true(
            str(summary_row["merge_readiness_status"]).strip() == "hold_due_to_current_workstream_uncommitted",
            "current workstream dirty should yield hold_due_to_current_workstream_uncommitted",
        )
        assert_true(
            worktree_df["worktree_class"].astype(str).eq("current_workstream_uncommitted").any(),
            "current workstream dirty scenario should emit current_workstream_uncommitted rows",
        )


def scenario_other_dirty(root: Path, build_script: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        init_repo(tmp_root)
        dirty_path = tmp_root / "notes.txt"
        dirty_path.write_text("other\n", encoding="utf-8")

        summary_df, worktree_df, _actions_df = run_builder(tmp_root, build_script, root)
        summary_row = summary_df.iloc[0]
        assert_true(
            str(summary_row["merge_readiness_status"]).strip() == "hold_due_to_other_worktree_change",
            "other arbitrary dirty should yield hold_due_to_other_worktree_change",
        )
        assert_true(
            worktree_df["worktree_class"].astype(str).eq("other_worktree_change").any(),
            "other arbitrary dirty scenario should emit other_worktree_change rows",
        )


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_merge_readiness_pack_v1.py"
    safe_smoke_handoff = root / "research" / "prognostics" / "smoke_test_workstream_handoff_pack_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script), str(Path(__file__))], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    scenario_clean(root, build_script)
    scenario_generated_share_only(root, build_script)
    scenario_current_workstream_dirty(root, build_script)
    scenario_other_dirty(root, build_script)

    print("[OK] outputs generate")
    print("[OK] clean synthetic status yields ready_for_merge_or_archive")
    print("[OK] generated _share only yields ready_after_ignoring_generated_and_known_unrelated")
    print("[OK] current workstream dirty yields hold_due_to_current_workstream_uncommitted")
    print("[OK] other arbitrary dirty yields hold_due_to_other_worktree_change")
    print("[OK] no official outputs are modified")

    safe_smoke_res = run([sys.executable, str(safe_smoke_handoff)], root)
    assert_true(
        safe_smoke_res.returncode == 0,
        f"existing safe smoke failed:\n{safe_smoke_res.stdout}\n{safe_smoke_res.stderr}",
    )
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
