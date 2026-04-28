#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-148-precheck"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_commit_scope_dry_run_br148_check"

FILES_OUTPUT_NAME = "mlpe_field_trial_commit_scope_dry_run_files_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_commit_scope_dry_run_summary_v1.csv"
ISSUES_OUTPUT_NAME = "mlpe_field_trial_commit_scope_dry_run_issues_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_commit_scope_dry_run_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_commit_scope_dry_run_v1.json"

FILE_COLUMNS = [
    "owner_branch",
    "status_code",
    "path",
    "tracked_state",
    "role_family",
    "commit_scope_policy",
    "risk_flag",
    "recommended_action",
]

ISSUE_COLUMNS = [
    "owner_branch",
    "issue_type",
    "path",
    "observed_value",
    "expected_policy",
]


def run_git(repo_root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout


def status_rows(repo_root: Path) -> list[tuple[str, str]]:
    out = run_git(repo_root, ["status", "--porcelain=v1", "-uall"])
    rows: list[tuple[str, str]] = []
    for line in out.splitlines():
        if not line:
            continue
        code = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        rows.append((code, path))
    return rows


def is_data_raw_or_out(path: str) -> bool:
    parts = Path(path).parts
    return len(parts) >= 3 and parts[0] == "data" and parts[2] in {"raw", "out"}


def classify_path(path: str) -> tuple[str, str, int, str]:
    if path == "pv_ae/panel_day_engine.py":
        return (
            "panel_engine_source",
            "exclude_from_this_scope",
            1,
            "Do not include in this dry-run scope; engine semantics require BR-144 authorization.",
        )
    if is_data_raw_or_out(path):
        return (
            "large_site_data",
            "exclude_from_commit",
            1,
            "Keep data/<site>/raw and data/<site>/out outside git/package commit scope.",
        )
    if path.startswith("release/conalog_full_runtime_v1/") and path.endswith(".json"):
        return (
            "generated_release_artifact",
            "exclude_unless_release_sync_branch",
            1,
            "Restore or isolate generated release JSON unless a release-sync branch explicitly owns it.",
        )
    if path == "docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md":
        return (
            "runtime_control_doc",
            "include_if_reviewed",
            0,
            "Review with branch docs and include as current-state register update.",
        )
    if path.startswith("docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_"):
        return (
            "runtime_branch_doc_or_matrix",
            "include_if_reviewed",
            0,
            "Include as the documented BR-126..143 continuity and gate record.",
        )
    if path.startswith("research/prognostics/build_mlpe_field_trial_") and path.endswith(".py"):
        return (
            "field_trial_contract_builder",
            "include_if_smoke_passes",
            0,
            "Include with matching smoke and documented output path.",
        )
    if path.startswith("research/prognostics/smoke_test_mlpe_field_trial_") and path.endswith(".py"):
        return (
            "field_trial_contract_smoke",
            "include_if_passes",
            0,
            "Include as validation coverage for the matching builder.",
        )
    return (
        "unclassified_dirty_path",
        "hold_for_manual_review",
        1,
        "Classify before staging; do not sweep into the commit with git add .",
    )


def tracked_state(status_code: str) -> str:
    if status_code == "??":
        return "untracked"
    if "D" in status_code:
        return "deleted"
    if "R" in status_code:
        return "renamed"
    return "tracked_modified"


def issue_type_for(row: dict[str, object]) -> str:
    role = str(row["role_family"])
    state = str(row["tracked_state"])
    if role == "panel_engine_source":
        return "panel_engine_source_dirty"
    if role == "large_site_data":
        return "large_site_data_dirty"
    if role == "generated_release_artifact":
        return "generated_release_artifact_dirty"
    if role == "unclassified_dirty_path":
        return "unclassified_dirty_path"
    if state in {"deleted", "renamed"}:
        return f"{state}_dirty_path"
    return "dirty_path_review_required"


def build_files(repo_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    file_rows: list[dict[str, object]] = []
    issue_rows: list[dict[str, object]] = []
    for code, path in status_rows(repo_root):
        role, policy, risk, action = classify_path(path)
        row = {
            "owner_branch": OWNER_BRANCH,
            "status_code": code,
            "path": path,
            "tracked_state": tracked_state(code),
            "role_family": role,
            "commit_scope_policy": policy,
            "risk_flag": risk,
            "recommended_action": action,
        }
        file_rows.append(row)
        if risk or row["tracked_state"] in {"deleted", "renamed"}:
            issue_rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "issue_type": issue_type_for(row),
                    "path": path,
                    "observed_value": f"{code} {role}",
                    "expected_policy": action,
                }
            )
    return pd.DataFrame(file_rows).reindex(columns=FILE_COLUMNS), pd.DataFrame(issue_rows).reindex(columns=ISSUE_COLUMNS)


def build_summary(files: pd.DataFrame, issues: pd.DataFrame) -> pd.DataFrame:
    dirty_files = int(len(files))
    risk_files = int(files["risk_flag"].sum()) if dirty_files else 0
    engine_source_dirty = int(files["role_family"].eq("panel_engine_source").sum()) if dirty_files else 0
    large_data_dirty = int(files["role_family"].eq("large_site_data").sum()) if dirty_files else 0
    release_generated_dirty = int(files["role_family"].eq("generated_release_artifact").sum()) if dirty_files else 0
    unclassified_dirty = int(files["role_family"].eq("unclassified_dirty_path").sum()) if dirty_files else 0
    deleted_or_renamed = int(files["tracked_state"].isin(["deleted", "renamed"]).sum()) if dirty_files else 0
    include_candidate_files = int(dirty_files - risk_files - deleted_or_renamed)
    commit_scope_ready = int(dirty_files > 0 and risk_files == 0 and deleted_or_renamed == 0 and len(issues) == 0)
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "dirty_files": dirty_files,
            "include_candidate_files": include_candidate_files,
            "tracked_modified_files": int(files["tracked_state"].eq("tracked_modified").sum()) if dirty_files else 0,
            "untracked_files": int(files["tracked_state"].eq("untracked").sum()) if dirty_files else 0,
            "runtime_doc_files": int(files["role_family"].str.contains("runtime_").sum()) if dirty_files else 0,
            "builder_files": int(files["role_family"].eq("field_trial_contract_builder").sum()) if dirty_files else 0,
            "smoke_files": int(files["role_family"].eq("field_trial_contract_smoke").sum()) if dirty_files else 0,
            "risk_files": risk_files,
            "issue_rows": int(len(issues)),
            "engine_source_dirty": engine_source_dirty,
            "large_data_dirty": large_data_dirty,
            "release_generated_dirty": release_generated_dirty,
            "unclassified_dirty": unclassified_dirty,
            "deleted_or_renamed_dirty": deleted_or_renamed,
            "commit_scope_ready_flag": commit_scope_ready,
            "canonical_truth_write_allowed_sum": 0,
            "truth_intake_allowed_sum": 0,
            "threshold_patch_allowed_sum": 0,
            "engine_patch_allowed_sum": 0,
        }
    ]
    if dirty_files:
        for role, sub in files.groupby("role_family"):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "role_family",
                    "summary_key": role,
                    "dirty_files": int(len(sub)),
                    "include_candidate_files": int((sub["risk_flag"].eq(0) & ~sub["tracked_state"].isin(["deleted", "renamed"])).sum()),
                    "tracked_modified_files": int(sub["tracked_state"].eq("tracked_modified").sum()),
                    "untracked_files": int(sub["tracked_state"].eq("untracked").sum()),
                    "runtime_doc_files": int(sub["role_family"].str.contains("runtime_").sum()),
                    "builder_files": int(sub["role_family"].eq("field_trial_contract_builder").sum()),
                    "smoke_files": int(sub["role_family"].eq("field_trial_contract_smoke").sum()),
                    "risk_files": int(sub["risk_flag"].sum()),
                    "issue_rows": int(len(issues[issues["path"].isin(set(sub["path"]))])),
                    "engine_source_dirty": int(sub["role_family"].eq("panel_engine_source").sum()),
                    "large_data_dirty": int(sub["role_family"].eq("large_site_data").sum()),
                    "release_generated_dirty": int(sub["role_family"].eq("generated_release_artifact").sum()),
                    "unclassified_dirty": int(sub["role_family"].eq("unclassified_dirty_path").sum()),
                    "deleted_or_renamed_dirty": int(sub["tracked_state"].isin(["deleted", "renamed"]).sum()),
                    "commit_scope_ready_flag": 0,
                    "canonical_truth_write_allowed_sum": 0,
                    "truth_intake_allowed_sum": 0,
                    "threshold_patch_allowed_sum": 0,
                    "engine_patch_allowed_sum": 0,
                }
            )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, summary: pd.DataFrame) -> None:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    text = "\n".join(
        [
            "# BR-20260425-148 precheck commit-scope dry-run audit",
            "",
            f"- dirty files: `{overall['dirty_files']}`",
            f"- include-candidate files: `{overall['include_candidate_files']}`",
            f"- risk files: `{overall['risk_files']}`",
            f"- issue rows: `{overall['issue_rows']}`",
            f"- engine source dirty: `{overall['engine_source_dirty']}`",
            f"- large data dirty: `{overall['large_data_dirty']}`",
            f"- release generated dirty: `{overall['release_generated_dirty']}`",
            f"- unclassified dirty: `{overall['unclassified_dirty']}`",
            f"- commit-scope ready flag: `{overall['commit_scope_ready_flag']}`",
            "",
            "This is a dry-run scope audit only.",
            "It does not stage, commit, push, write truth, tune thresholds, or authorize a panel-engine patch.",
            "",
        ]
    )
    (output_dir / NOTE_OUTPUT_NAME).write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a fail-closed commit-scope dry-run audit for the MLPE runway.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else repo_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    files, issues = build_files(repo_root)
    summary = build_summary(files, issues)

    files.to_csv(output_dir / FILES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    issues.to_csv(output_dir / ISSUES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "dirty_files": int(overall["dirty_files"]),
        "include_candidate_files": int(overall["include_candidate_files"]),
        "risk_files": int(overall["risk_files"]),
        "issue_rows": int(overall["issue_rows"]),
        "engine_source_dirty": int(overall["engine_source_dirty"]),
        "large_data_dirty": int(overall["large_data_dirty"]),
        "release_generated_dirty": int(overall["release_generated_dirty"]),
        "unclassified_dirty": int(overall["unclassified_dirty"]),
        "commit_scope_ready_flag": int(overall["commit_scope_ready_flag"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "files": str(output_dir / FILES_OUTPUT_NAME),
            "issues": str(output_dir / ISSUES_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
            "json": str(output_dir / JSON_OUTPUT_NAME),
        },
    }
    (output_dir / JSON_OUTPUT_NAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
