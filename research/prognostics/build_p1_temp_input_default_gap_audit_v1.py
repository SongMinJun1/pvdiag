#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    from build_repo_path_portability_audit_v1 import DEFAULT_SCAN_ROOTS, iter_scan_files, scan_file
except ImportError:
    from research.prognostics.build_repo_path_portability_audit_v1 import (
        DEFAULT_SCAN_ROOTS,
        iter_scan_files,
        scan_file,
    )


OWNER_BRANCH = "BR-20260429-225"

DETAIL_OUTPUT_NAME = "p1_temp_input_default_gap_audit_v1.csv"
SUMMARY_OUTPUT_NAME = "p1_temp_input_default_gap_audit_summary_v1.csv"
NOTE_OUTPUT_NAME = "p1_temp_input_default_gap_audit_note_v1.md"
JSON_OUTPUT_NAME = "p1_temp_input_default_gap_audit_v1.json"

EXPECTED_TOTAL_PATH_MATCHES = 1935
EXPECTED_P1_LIVE_TEMP_ROWS = 68
EXPECTED_P1_TEMP_INPUT_ROWS = 15
EXPECTED_CLOSED_ROWS = 14
EXPECTED_OPEN_GAP_ROWS = 1
EXPECTED_WORKFLOW_COUNTS = {
    "mlpe_field_trial": 7,
    "panel_engine_common_cause": 2,
    "panel_engine_prepatch_scorecard": 1,
    "panel_engine_voltage_preserved": 5,
}

DETAIL_COLUMNS = [
    "owner_branch",
    "gap_id",
    "relative_path",
    "line_no",
    "workflow_lane",
    "dependency_contract",
    "match_role",
    "matched_text",
    "default_constant",
    "explicit_cli_flag",
    "has_explicit_cli_arg",
    "has_input_manifest_arg",
    "has_source_specific_manifest_resolver",
    "has_user_filled_guard",
    "has_fixture_allow_flag",
    "closure_class",
    "closure_status",
    "open_gap_reason",
    "supporting_branch",
    "recommended_next_action",
    "runtime_semantic_change_allowed_rows",
    "bulk_rewrite_allowed_rows",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]

SUPPORTING_BRANCH_BY_FILE = {
    "research/prognostics/build_mlpe_field_trial_capture_return_evidence_resolver_v1.py": "BR-20260429-203|BR-20260429-209",
    "research/prognostics/build_mlpe_field_trial_capture_return_validator_v1.py": "BR-20260429-202|BR-20260429-209",
    "research/prognostics/build_mlpe_field_trial_final_label_validator_v1.py": "BR-20260429-204|BR-20260429-209",
    "research/prognostics/build_mlpe_field_trial_label_to_truth_gate_v1.py": "BR-20260429-205|BR-20260429-209",
    "research/prognostics/build_mlpe_field_trial_real_label_intake_runbook_v1.py": "BR-20260429-206|BR-20260429-209",
    "research/prognostics/build_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py": "BR-20260429-207|BR-20260429-209",
    "research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py": "BR-20260429-208|BR-20260429-209",
    "research/prognostics/build_panel_day_engine_common_cause_exact_seed_search_v1.py": "BR-20260429-200",
    "research/prognostics/build_panel_day_engine_common_cause_manual_trace_review_v1.py": "BR-20260429-201",
    "research/prognostics/build_panel_day_engine_result_delta_scorecard_v1.py": "BR-20260429-216",
    "research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py": "BR-20260429-197",
    "research/prognostics/build_panel_day_engine_voltage_preserved_evidence_request_packet_v1.py": "BR-20260429-195",
    "research/prognostics/build_panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.py": "BR-20260429-198",
    "research/prognostics/build_panel_day_engine_voltage_preserved_raw_source_attachment_v1.py": "BR-20260429-196",
    "research/prognostics/build_panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.py": "BR-20260429-199",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Re-audit p1 temp input defaults after the p1 live-temp lane closure. "
            "This identifies which remaining defaults are contract-closed and which "
            "still need a small follow-up patch."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for audit outputs. Required so this audit adds no temp default.",
    )
    parser.add_argument("--max-file-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def read_source_lines(repo_root: Path, relative_path: str) -> list[str]:
    try:
        return (repo_root / relative_path).read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return (repo_root / relative_path).read_text(encoding="utf-8", errors="replace").splitlines()


def find_default_constant(lines: list[str], line_no: int) -> str:
    index = max(0, line_no - 1)
    for cursor in range(index, max(-1, index - 8), -1):
        match = re.search(r"\b(DEFAULT_[A-Z0-9_]+)\b\s*=", lines[cursor])
        if match:
            return match.group(1)
    return ""


def find_cli_flag_for_default(source_lines: list[str], default_constant: str) -> str:
    if not default_constant:
        return ""
    default_pattern = re.compile(rf"default\s*=\s*{re.escape(default_constant)}\b")
    for index, line in enumerate(source_lines):
        if not default_pattern.search(line):
            continue
        block_start = index
        while block_start >= 0 and "parser.add_argument" not in source_lines[block_start]:
            block_start -= 1
        if block_start < 0:
            continue
        block = "\n".join(source_lines[block_start : index + 1])
        flag_match = re.search(r"[\"'](--[A-Za-z0-9][A-Za-z0-9_-]*)[\"']", block)
        if flag_match:
            return flag_match.group(1)
    return ""


def has_source_specific_manifest_resolver(source_text: str, cli_flag: str, dependency_contract: str) -> bool:
    if dependency_contract == "mlpe_user_filled_input":
        return "input_manifest" in source_text and "require_explicit_user_filled_input" in source_text
    if not cli_flag:
        return False
    return source_text.count(cli_flag) > 1 and "input_manifest" in source_text


def collect_path_rows(repo_root: Path, max_file_bytes: int) -> list[dict[str, object]]:
    files, _skipped = iter_scan_files(repo_root, list(DEFAULT_SCAN_ROOTS), max_file_bytes)
    rows: list[dict[str, object]] = []
    for path in files:
        rows.extend(scan_file(path, repo_root))
    return rows


def classify_detail_row(
    repo_root: Path,
    row: dict[str, object],
    index: int,
) -> dict[str, object]:
    relative_path = str(row["relative_path"])
    line_no = int(row["line_no"])
    source_lines = read_source_lines(repo_root, relative_path)
    source_text = "\n".join(source_lines)
    default_constant = find_default_constant(source_lines, line_no)
    cli_flag = find_cli_flag_for_default(source_lines, default_constant)
    dependency_contract = str(row.get("dependency_contract", ""))
    has_explicit_cli_arg = bool(cli_flag)
    has_input_manifest_arg = "--input-manifest" in source_text
    has_manifest_resolver = has_source_specific_manifest_resolver(
        source_text,
        cli_flag,
        dependency_contract,
    )
    has_user_guard = "require_explicit_user_filled_input" in source_text
    has_fixture_allow = "--allow-user-filled-default" in source_text

    if dependency_contract == "mlpe_user_filled_input":
        closed = has_explicit_cli_arg and has_input_manifest_arg and has_user_guard and has_fixture_allow
        closure_class = "closed_guarded_user_filled_default"
        open_gap_reason = "" if closed else "missing_user_filled_guard_or_manifest_support"
        next_action = "keep_fail_closed_user_filled_guard"
    else:
        closed = has_explicit_cli_arg and has_input_manifest_arg and has_manifest_resolver
        closure_class = "closed_manifest_or_explicit_input_default" if closed else "open_explicit_cli_only_default"
        open_gap_reason = "" if closed else "legacy_default_has_explicit_cli_but_no_source_specific_manifest_resolution"
        next_action = (
            "keep_manifest_or_explicit_input_contract"
            if closed
            else "add_source_specific_manifest_resolution_or_require_explicit_input"
        )

    return {
        "owner_branch": OWNER_BRANCH,
        "gap_id": f"BR225-{index:03d}",
        "relative_path": relative_path,
        "line_no": line_no,
        "workflow_lane": str(row.get("workflow_lane", "")),
        "dependency_contract": dependency_contract,
        "match_role": str(row.get("match_role", "")),
        "matched_text": str(row.get("matched_text", "")),
        "default_constant": default_constant,
        "explicit_cli_flag": cli_flag,
        "has_explicit_cli_arg": int(has_explicit_cli_arg),
        "has_input_manifest_arg": int(has_input_manifest_arg),
        "has_source_specific_manifest_resolver": int(has_manifest_resolver),
        "has_user_filled_guard": int(has_user_guard),
        "has_fixture_allow_flag": int(has_fixture_allow),
        "closure_class": closure_class,
        "closure_status": "closed" if closed else "needs_patch",
        "open_gap_reason": open_gap_reason,
        "supporting_branch": SUPPORTING_BRANCH_BY_FILE.get(relative_path, ""),
        "recommended_next_action": next_action,
        "runtime_semantic_change_allowed_rows": 0,
        "bulk_rewrite_allowed_rows": 0,
    }


def summary_payload(
    path_rows: list[dict[str, object]],
    detail_rows: list[dict[str, object]],
) -> dict[str, object]:
    priority_counts = Counter(str(row["triage_priority"]) for row in path_rows)
    workflow_counts = Counter(str(row["workflow_lane"]) for row in detail_rows)
    closure_counts = Counter(str(row["closure_status"]) for row in detail_rows)
    class_counts = Counter(str(row["closure_class"]) for row in detail_rows)
    open_rows = [row for row in detail_rows if row["closure_status"] != "closed"]
    expected_workflow_match = int(
        all(workflow_counts.get(key, 0) == value for key, value in EXPECTED_WORKFLOW_COUNTS.items())
    )
    expected_counts_match = int(
        len(path_rows) == EXPECTED_TOTAL_PATH_MATCHES
        and priority_counts.get("p1_live_temp_reference", 0) == EXPECTED_P1_LIVE_TEMP_ROWS
        and len(detail_rows) == EXPECTED_P1_TEMP_INPUT_ROWS
        and closure_counts.get("closed", 0) == EXPECTED_CLOSED_ROWS
        and len(open_rows) == EXPECTED_OPEN_GAP_ROWS
    )
    closure_complete = int(expected_counts_match == 1 and expected_workflow_match == 1)
    return {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "path_portability_total_matches": len(path_rows),
        "p0_stale_worktree_rows": priority_counts.get("p0_stale_worktree", 0),
        "p1_live_temp_reference_rows": priority_counts.get("p1_live_temp_reference", 0),
        "p1_temp_input_default_rows": len(detail_rows),
        "closed_rows": closure_counts.get("closed", 0),
        "open_gap_rows": len(open_rows),
        "mlpe_guarded_user_filled_rows": class_counts.get("closed_guarded_user_filled_default", 0),
        "non_mlpe_manifest_or_explicit_closed_rows": class_counts.get(
            "closed_manifest_or_explicit_input_default",
            0,
        ),
        "explicit_cli_only_open_rows": class_counts.get("open_explicit_cli_only_default", 0),
        "runtime_semantic_change_allowed_rows": 0,
        "bulk_rewrite_allowed_rows": 0,
        "expected_counts_match": expected_counts_match,
        "expected_workflow_match": expected_workflow_match,
        "closure_complete": closure_complete,
        "workflow_lane_counts": dict(sorted(workflow_counts.items())),
        "closure_class_counts": dict(sorted(class_counts.items())),
        "open_gap_files": [str(row["relative_path"]) for row in open_rows],
        "recommended_next_branch": "patch_result_delta_runtime_root_manifest_or_required_cli",
    }


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scalar_keys = [
        "path_portability_total_matches",
        "p0_stale_worktree_rows",
        "p1_live_temp_reference_rows",
        "p1_temp_input_default_rows",
        "closed_rows",
        "open_gap_rows",
        "mlpe_guarded_user_filled_rows",
        "non_mlpe_manifest_or_explicit_closed_rows",
        "explicit_cli_only_open_rows",
        "runtime_semantic_change_allowed_rows",
        "bulk_rewrite_allowed_rows",
        "expected_counts_match",
        "expected_workflow_match",
        "closure_complete",
    ]
    for key in scalar_keys:
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "overall",
                "key": key,
                "count": payload[key],
            }
        )
    for key, value in payload["workflow_lane_counts"].items():
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "workflow_lane",
                "key": key,
                "count": value,
            }
        )
    for key, value in payload["closure_class_counts"].items():
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "closure_class",
                "key": key,
                "count": value,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def render_note(payload: dict[str, object], detail_rows: list[dict[str, object]]) -> str:
    open_rows = [row for row in detail_rows if row["closure_status"] != "closed"]
    lines = [
        "# P1 Temp Input Default Gap Audit V1",
        "",
        "## Summary",
        "- Re-audits p1 temp input defaults after the BR-224 p1 live-temp lane closure.",
        "- This is an audit-only patch. It does not rewrite defaults or change runtime behavior.",
        "",
        "## Counts",
        f"- path_portability_total_matches: `{payload['path_portability_total_matches']}`",
        f"- p0_stale_worktree_rows: `{payload['p0_stale_worktree_rows']}`",
        f"- p1_live_temp_reference_rows: `{payload['p1_live_temp_reference_rows']}`",
        f"- p1_temp_input_default_rows: `{payload['p1_temp_input_default_rows']}`",
        f"- closed_rows: `{payload['closed_rows']}`",
        f"- open_gap_rows: `{payload['open_gap_rows']}`",
        f"- closure_complete: `{payload['closure_complete']}`",
        "",
        "## Interpretation",
        "- BR-224 keeps the 68 live-temp rows closed at contract/audit level.",
        "- The remaining p1 temp input-default lane is mostly closed by existing guards or manifest/explicit-input support.",
        "- One row remains an explicit-CLI-only legacy default and should be patched separately.",
        "",
        "## Open Gap",
    ]
    if open_rows:
        for row in open_rows:
            lines.append(
                "- "
                f"`{row['relative_path']}:{row['line_no']}` "
                f"`{row['default_constant']}` -> `{row['open_gap_reason']}`"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Next Action",
            "- Patch the open prepatch scorecard runtime-root default by adding source-specific manifest resolution or a required explicit input boundary.",
            "- Keep this separate from runtime semantics and panel-engine code.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    path_rows = collect_path_rows(repo_root, args.max_file_bytes)
    p1_temp_rows = [
        row
        for row in path_rows
        if str(row.get("triage_priority")) == "p1_temp_input_default_reference"
    ]
    detail_rows = [
        classify_detail_row(repo_root, row, index)
        for index, row in enumerate(p1_temp_rows, start=1)
    ]
    payload = summary_payload(path_rows, detail_rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / DETAIL_OUTPUT_NAME, detail_rows, DETAIL_COLUMNS)
    write_csv(args.output_dir / SUMMARY_OUTPUT_NAME, summary_rows(payload), SUMMARY_COLUMNS)
    (args.output_dir / NOTE_OUTPUT_NAME).write_text(render_note(payload, detail_rows), encoding="utf-8")
    (args.output_dir / JSON_OUTPUT_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
