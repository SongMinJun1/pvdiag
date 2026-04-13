#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pandas as pd

SUMMARY_COLS = [
    "current_branch",
    "head_commit_short",
    "baseline_guard_status",
    "freeze_recommendation",
    "next_workstream_recommendation",
    "total_worktree_change_count",
    "generated_share_artifact_count",
    "known_unrelated_dirty_count",
    "current_workstream_uncommitted_count",
    "other_worktree_change_count",
    "merge_readiness_status",
]
WORKTREE_COLS = ["git_status_code", "path", "worktree_class"]
ACTIONS_COLS = ["action_order", "action_key", "action_text_ko"]
KNOWN_UNRELATED_DIRTY = {
    "research/prognostics/build_site_event_dataset.py",
    "research/prognostics/smoke_test_site_event_dataset.py",
}
REQUIRED_OPEN_THREAD_KEYS = {
    "gangui_deferred_high_actionability",
    "conalog_site_specific_precursor_note",
    "precursor_global_addon",
    "baseline_regression_guard",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a merge-readiness pack for the current frozen workstream branch."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def to_int(value: object) -> int:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return 0
    return int(numeric)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def drop_embedded_header_rows(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    if any(col not in df.columns for col in cols):
        return df
    header_mask = pd.Series(True, index=df.index)
    for col in cols:
        header_mask &= df[col].map(normalize_text).eq(col)
    if not bool(header_mask.any()):
        return df
    return df.loc[~header_mask].copy()


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def get_single_row(df: pd.DataFrame, name: str) -> pd.Series:
    if df.empty:
        raise SystemExit(f"{name} is empty")
    return df.iloc[0]


def run_git(root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"git {' '.join(args)} failed with code {result.returncode}: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout


def normalize_git_path(raw_path: str) -> str:
    path = raw_path.strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    if path.startswith('"') and path.endswith('"') and len(path) >= 2:
        path = path[1:-1]
    return path


def classify_worktree_path(path: str) -> str:
    if path.startswith("_share/"):
        return "generated_share_artifact"
    if path in KNOWN_UNRELATED_DIRTY:
        return "known_unrelated_dirty"
    if (path.startswith("docs/") or path.startswith("research/prognostics/")) and path not in KNOWN_UNRELATED_DIRTY:
        return "current_workstream_uncommitted"
    return "other_worktree_change"


def build_worktree_output(root: Path) -> tuple[str, str, pd.DataFrame]:
    current_branch = normalize_text(run_git(root, ["branch", "--show-current"]))
    head_commit_short = normalize_text(run_git(root, ["rev-parse", "--short", "HEAD"]))
    status_stdout = run_git(root, ["status", "--porcelain"])

    rows: list[dict[str, str]] = []
    for raw_line in status_stdout.splitlines():
        if not raw_line:
            continue
        git_status_code = raw_line[:2]
        raw_path = raw_line[3:] if len(raw_line) > 3 else ""
        path = normalize_git_path(raw_path)
        rows.append(
            {
                "git_status_code": git_status_code,
                "path": path,
                "worktree_class": classify_worktree_path(path),
            }
        )

    return current_branch, head_commit_short, pd.DataFrame(rows, columns=WORKTREE_COLS)


def build_summary_output(
    handoff_summary_row: pd.Series,
    guard_summary_row: pd.Series,
    worktree_df: pd.DataFrame,
    current_branch: str,
    head_commit_short: str,
) -> pd.DataFrame:
    baseline_guard_status = normalize_text(
        guard_summary_row.get("guard_status", handoff_summary_row.get("baseline_guard_status", ""))
    )
    freeze_recommendation = normalize_text(handoff_summary_row.get("freeze_recommendation", ""))
    next_workstream_recommendation = normalize_text(handoff_summary_row.get("next_workstream_recommendation", ""))

    class_counts = worktree_df["worktree_class"].value_counts().to_dict() if not worktree_df.empty else {}
    total_worktree_change_count = int(len(worktree_df))
    generated_share_artifact_count = int(class_counts.get("generated_share_artifact", 0))
    known_unrelated_dirty_count = int(class_counts.get("known_unrelated_dirty", 0))
    current_workstream_uncommitted_count = int(class_counts.get("current_workstream_uncommitted", 0))
    other_worktree_change_count = int(class_counts.get("other_worktree_change", 0))

    if (
        baseline_guard_status == "frozen_baseline_preserved"
        and next_workstream_recommendation == "safe_to_switch_topic"
        and total_worktree_change_count == 0
    ):
        merge_readiness_status = "ready_for_merge_or_archive"
    elif (
        baseline_guard_status == "frozen_baseline_preserved"
        and next_workstream_recommendation == "safe_to_switch_topic"
        and current_workstream_uncommitted_count == 0
        and other_worktree_change_count == 0
        and total_worktree_change_count > 0
    ):
        merge_readiness_status = "ready_after_ignoring_generated_and_known_unrelated"
    elif current_workstream_uncommitted_count > 0:
        merge_readiness_status = "hold_due_to_current_workstream_uncommitted"
    else:
        merge_readiness_status = "hold_due_to_other_worktree_change"

    row = {
        "current_branch": current_branch,
        "head_commit_short": head_commit_short,
        "baseline_guard_status": baseline_guard_status,
        "freeze_recommendation": freeze_recommendation,
        "next_workstream_recommendation": next_workstream_recommendation,
        "total_worktree_change_count": total_worktree_change_count,
        "generated_share_artifact_count": generated_share_artifact_count,
        "known_unrelated_dirty_count": known_unrelated_dirty_count,
        "current_workstream_uncommitted_count": current_workstream_uncommitted_count,
        "other_worktree_change_count": other_worktree_change_count,
        "merge_readiness_status": merge_readiness_status,
    }
    return pd.DataFrame([row], columns=SUMMARY_COLS)


def build_actions_output(summary_row: pd.Series, open_threads_df: pd.DataFrame) -> pd.DataFrame:
    current_branch = normalize_text(summary_row["current_branch"])
    head_commit_short = normalize_text(summary_row["head_commit_short"])
    merge_readiness_status = normalize_text(summary_row["merge_readiness_status"])
    generated_share_artifact_count = to_int(summary_row["generated_share_artifact_count"])
    known_unrelated_dirty_count = to_int(summary_row["known_unrelated_dirty_count"])
    current_workstream_uncommitted_count = to_int(summary_row["current_workstream_uncommitted_count"])
    open_thread_count = int(len(open_threads_df))

    if merge_readiness_status in {
        "ready_for_merge_or_archive",
        "ready_after_ignoring_generated_and_known_unrelated",
    }:
        verify_branch_text = (
            f"현재 브랜치 `{current_branch}`와 HEAD `{head_commit_short}`가 의도한 대상인지 마지막으로만 확인하면 됩니다."
        )
    else:
        verify_branch_text = (
            f"현재 브랜치 `{current_branch}`와 HEAD `{head_commit_short}`를 먼저 확인하고 hold 원인을 정리하세요."
        )

    if generated_share_artifact_count > 0:
        generated_share_text = (
            f"`_share/` generated artifact {generated_share_artifact_count}건은 기본 blocker가 아니므로 merge/archive 판단에서는 분리해 다루세요."
        )
    else:
        generated_share_text = "`_share/` generated artifact dirty는 현재 없습니다."

    if known_unrelated_dirty_count > 0:
        known_unrelated_text = (
            f"known unrelated dirty {known_unrelated_dirty_count}건은 이번 workstream merge 판단에서 제외하고 별도로 추적하세요."
        )
    else:
        known_unrelated_text = "제외 대상으로 지정된 known unrelated dirty는 현재 없습니다."

    if current_workstream_uncommitted_count > 0:
        current_workstream_text = (
            f"현재 workstream 변경 {current_workstream_uncommitted_count}건은 커밋하거나 정리하기 전까지 merge/archive를 멈추세요."
        )
    else:
        current_workstream_text = "현재 workstream 미커밋 변경은 없어 이 항목이 blocker는 아닙니다."

    if merge_readiness_status == "ready_for_merge_or_archive":
        safe_to_switch_text = (
            f"frozen baseline, guard, handoff, worktree가 모두 정리돼 open thread {open_thread_count}개를 유지한 채 바로 merge 또는 archive가 가능합니다."
        )
    elif merge_readiness_status == "ready_after_ignoring_generated_and_known_unrelated":
        safe_to_switch_text = (
            f"generated `_share/` 또는 known unrelated dirty만 정리 기준에서 제외하면 open thread {open_thread_count}개를 유지한 채 topic switch용 merge/archive가 가능합니다."
        )
    elif merge_readiness_status == "hold_due_to_current_workstream_uncommitted":
        safe_to_switch_text = "현재 workstream 미커밋 변경을 먼저 정리한 뒤 merge readiness를 다시 확인하세요."
    else:
        safe_to_switch_text = "기타 worktree change가 남아 있어 지금은 merge/archive를 보류하고 변경 출처를 먼저 분류하세요."

    rows = [
        {
            "action_order": 1,
            "action_key": "verify_branch_target",
            "action_text_ko": verify_branch_text,
        },
        {
            "action_order": 2,
            "action_key": "handle_generated_share_files",
            "action_text_ko": generated_share_text,
        },
        {
            "action_order": 3,
            "action_key": "exclude_known_unrelated_dirty",
            "action_text_ko": known_unrelated_text,
        },
        {
            "action_order": 4,
            "action_key": "commit_current_workstream_or_stop",
            "action_text_ko": current_workstream_text,
        },
        {
            "action_order": 5,
            "action_key": "safe_to_switch_or_merge",
            "action_text_ko": safe_to_switch_text,
        },
    ]
    return pd.DataFrame(rows, columns=ACTIONS_COLS)


def build_outputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    handoff_summary_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "workstream_handoff_summary_v1.csv"),
        ["baseline_guard_status"],
    )
    handoff_sites_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "workstream_handoff_sites_v1.csv"),
        ["site"],
    )
    handoff_open_threads_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "workstream_handoff_open_threads_v1.csv"),
        ["thread_key"],
    )
    guard_summary_df = drop_embedded_header_rows(
        read_csv(root / "_share" / "baseline_regression_guard_summary_v1.csv"),
        ["guard_status"],
    )

    ensure_columns(
        handoff_summary_df,
        ["baseline_guard_status", "freeze_recommendation", "next_workstream_recommendation"],
        "workstream_handoff_summary_v1.csv",
    )
    ensure_columns(
        handoff_sites_df,
        ["site", "site_status"],
        "workstream_handoff_sites_v1.csv",
    )
    ensure_columns(
        handoff_open_threads_df,
        ["thread_key", "thread_status", "owner_needed", "reactivation_condition", "note_ko"],
        "workstream_handoff_open_threads_v1.csv",
    )
    ensure_columns(
        guard_summary_df,
        ["guard_status"],
        "baseline_regression_guard_summary_v1.csv",
    )

    open_thread_keys = set(handoff_open_threads_df["thread_key"].map(normalize_text))
    missing_thread_keys = sorted(REQUIRED_OPEN_THREAD_KEYS - open_thread_keys)
    if missing_thread_keys:
        raise SystemExit(f"workstream_handoff_open_threads_v1.csv missing thread keys: {missing_thread_keys}")

    current_branch, head_commit_short, worktree_output = build_worktree_output(root)
    handoff_summary_row = get_single_row(handoff_summary_df, "workstream_handoff_summary_v1.csv")
    guard_summary_row = get_single_row(guard_summary_df, "baseline_regression_guard_summary_v1.csv")

    summary_output = build_summary_output(
        handoff_summary_row,
        guard_summary_row,
        worktree_output,
        current_branch,
        head_commit_short,
    )
    actions_output = build_actions_output(summary_output.iloc[0], handoff_open_threads_df)
    return summary_output, worktree_output, actions_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_output, worktree_output, actions_output = build_outputs(root)

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_output.to_csv(out_dir / "merge_readiness_summary_v1.csv", index=False, encoding="utf-8-sig")
    worktree_output.to_csv(out_dir / "merge_readiness_worktree_v1.csv", index=False, encoding="utf-8-sig")
    actions_output.to_csv(out_dir / "merge_readiness_actions_v1.csv", index=False, encoding="utf-8-sig")
    print(
        "merge_readiness_summary_v1="
        f"{len(summary_output)} merge_readiness_worktree_v1={len(worktree_output)} "
        f"merge_readiness_actions_v1={len(actions_output)}"
    )


if __name__ == "__main__":
    main()
