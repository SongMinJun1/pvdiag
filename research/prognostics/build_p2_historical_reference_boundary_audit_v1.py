#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
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


OWNER_BRANCH = "BR-20260429-227"

DETAIL_OUTPUT_NAME = "p2_historical_reference_boundary_audit_v1.csv"
SUMMARY_OUTPUT_NAME = "p2_historical_reference_boundary_audit_summary_v1.csv"
NOTE_OUTPUT_NAME = "p2_historical_reference_boundary_audit_note_v1.md"
JSON_OUTPUT_NAME = "p2_historical_reference_boundary_audit_v1.json"

TARGET_PRIORITIES = {
    "p2_historical_evidence_reference",
    "p2_historical_repro_reference",
}

DETAIL_COLUMNS = [
    "owner_branch",
    "reference_id",
    "relative_path",
    "line_no",
    "match_kind",
    "file_kind",
    "workflow_lane",
    "match_role",
    "triage_priority",
    "matched_text",
    "boundary_class",
    "rewrite_policy",
    "stable_replacement_required",
    "refresh_only_when_touching_doc",
    "current_handoff_rebuild_candidate",
    "runtime_semantic_change_allowed_rows",
    "bulk_rewrite_allowed_rows",
    "recommended_next_action",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit p2 historical evidence/repro path references so they are not bulk-rewritten "
            "without a stable artifact, refreshed handoff, or current reproduction need."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for audit outputs. Required so this audit creates no temp default.",
    )
    parser.add_argument("--max-file-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def collect_path_rows(repo_root: Path, max_file_bytes: int) -> list[dict[str, object]]:
    files, _skipped = iter_scan_files(repo_root, list(DEFAULT_SCAN_ROOTS), max_file_bytes)
    rows: list[dict[str, object]] = []
    for path in files:
        rows.extend(scan_file(path, repo_root))
    return rows


def classify_boundary(row: dict[str, object]) -> dict[str, object]:
    triage_priority = str(row.get("triage_priority", ""))
    match_role = str(row.get("match_role", ""))
    file_kind = str(row.get("file_kind", ""))
    workflow_lane = str(row.get("workflow_lane", ""))

    if triage_priority == "p2_historical_evidence_reference":
        return {
            "boundary_class": "historical_evidence_provenance_pointer",
            "rewrite_policy": "preserve_until_named_stable_artifact_exists",
            "stable_replacement_required": 1,
            "refresh_only_when_touching_doc": 0,
            "current_handoff_rebuild_candidate": 0,
            "recommended_next_action": (
                "do_not_rewrite_bulk; materialize a stable artifact only when the evidence "
                "is promoted into a current handoff"
            ),
        }

    if match_role == "embedded_repro_command_temp_reference" and file_kind == "research_prognostics":
        return {
            "boundary_class": "generated_handoff_repro_literal",
            "rewrite_policy": "rebuild_handoff_manifest_when_that_handoff_becomes_current",
            "stable_replacement_required": 0,
            "refresh_only_when_touching_doc": 0,
            "current_handoff_rebuild_candidate": 1,
            "recommended_next_action": (
                "keep as historical repro text now; when refreshing the generated handoff, "
                "prefer manifest/explicit inputs instead of fixed temp paths"
            ),
        }

    if file_kind == "repo_doc":
        return {
            "boundary_class": "historical_doc_repro_reference",
            "rewrite_policy": "refresh_to_repo_relative_or_manifest_form_only_when_doc_is_reopened",
            "stable_replacement_required": 0,
            "refresh_only_when_touching_doc": 1,
            "current_handoff_rebuild_candidate": 0,
            "recommended_next_action": (
                "leave historical doc text intact unless the doc is refreshed for a current "
                "handoff or reproducibility packet"
            ),
        }

    return {
        "boundary_class": "p2_historical_reference_manual_review",
        "rewrite_policy": "inspect_before_rewrite",
        "stable_replacement_required": 0,
        "refresh_only_when_touching_doc": 0,
        "current_handoff_rebuild_candidate": int(workflow_lane != "repo_docs"),
        "recommended_next_action": "inspect the reference before changing it",
    }


def build_detail_rows(path_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    target_rows = [
        row for row in path_rows if str(row.get("triage_priority", "")) in TARGET_PRIORITIES
    ]
    detail_rows: list[dict[str, object]] = []
    for index, row in enumerate(target_rows, start=1):
        boundary = classify_boundary(row)
        detail_rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "reference_id": f"BR227-{index:04d}",
                "relative_path": row.get("relative_path", ""),
                "line_no": row.get("line_no", ""),
                "match_kind": row.get("match_kind", ""),
                "file_kind": row.get("file_kind", ""),
                "workflow_lane": row.get("workflow_lane", ""),
                "match_role": row.get("match_role", ""),
                "triage_priority": row.get("triage_priority", ""),
                "matched_text": row.get("matched_text", ""),
                "boundary_class": boundary["boundary_class"],
                "rewrite_policy": boundary["rewrite_policy"],
                "stable_replacement_required": boundary["stable_replacement_required"],
                "refresh_only_when_touching_doc": boundary["refresh_only_when_touching_doc"],
                "current_handoff_rebuild_candidate": boundary["current_handoff_rebuild_candidate"],
                "runtime_semantic_change_allowed_rows": 0,
                "bulk_rewrite_allowed_rows": 0,
                "recommended_next_action": boundary["recommended_next_action"],
            }
        )
    return detail_rows


def build_payload(path_rows: list[dict[str, object]], detail_rows: list[dict[str, object]]) -> dict[str, object]:
    all_priority_counts = Counter(str(row.get("triage_priority", "")) for row in path_rows)
    priority_counts = Counter(str(row["triage_priority"]) for row in detail_rows)
    boundary_counts = Counter(str(row["boundary_class"]) for row in detail_rows)
    file_kind_counts = Counter(str(row["file_kind"]) for row in detail_rows)
    workflow_counts = Counter(str(row["workflow_lane"]) for row in detail_rows)
    rewrite_policy_counts = Counter(str(row["rewrite_policy"]) for row in detail_rows)

    stable_required = sum(int(row["stable_replacement_required"]) for row in detail_rows)
    refresh_when_touching = sum(int(row["refresh_only_when_touching_doc"]) for row in detail_rows)
    handoff_rebuild = sum(int(row["current_handoff_rebuild_candidate"]) for row in detail_rows)

    return {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "path_portability_total_matches": len(path_rows),
        "p0_stale_worktree_rows": all_priority_counts.get("p0_stale_worktree", 0),
        "p1_live_temp_reference_rows": all_priority_counts.get("p1_live_temp_reference", 0),
        "p1_temp_input_default_rows": all_priority_counts.get("p1_temp_input_default_reference", 0),
        "p2_historical_total_rows": len(detail_rows),
        "p2_historical_evidence_rows": priority_counts.get("p2_historical_evidence_reference", 0),
        "p2_historical_repro_rows": priority_counts.get("p2_historical_repro_reference", 0),
        "stable_replacement_required_rows": stable_required,
        "refresh_only_when_touching_doc_rows": refresh_when_touching,
        "current_handoff_rebuild_candidate_rows": handoff_rebuild,
        "immediate_bulk_rewrite_allowed_rows": 0,
        "runtime_semantic_change_allowed_rows": 0,
        "operator_facing_change_allowed_rows": 0,
        "historical_boundary_complete": int(
            len(detail_rows) > 0
            and stable_required + refresh_when_touching + handoff_rebuild == len(detail_rows)
        ),
        "triage_priority_counts": dict(sorted(priority_counts.items())),
        "boundary_class_counts": dict(sorted(boundary_counts.items())),
        "file_kind_counts": dict(sorted(file_kind_counts.items())),
        "workflow_lane_counts": dict(sorted(workflow_counts.items())),
        "rewrite_policy_counts": dict(sorted(rewrite_policy_counts.items())),
        "recommended_next_branch": "p2_historical_reference_refresh_only_for_current_handoff",
    }


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scalar_keys = [
        "path_portability_total_matches",
        "p0_stale_worktree_rows",
        "p1_live_temp_reference_rows",
        "p1_temp_input_default_rows",
        "p2_historical_total_rows",
        "p2_historical_evidence_rows",
        "p2_historical_repro_rows",
        "stable_replacement_required_rows",
        "refresh_only_when_touching_doc_rows",
        "current_handoff_rebuild_candidate_rows",
        "immediate_bulk_rewrite_allowed_rows",
        "runtime_semantic_change_allowed_rows",
        "operator_facing_change_allowed_rows",
        "historical_boundary_complete",
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
    for scope_key in [
        "triage_priority_counts",
        "boundary_class_counts",
        "file_kind_counts",
        "workflow_lane_counts",
        "rewrite_policy_counts",
    ]:
        scope = scope_key.removesuffix("_counts")
        for key, value in payload[scope_key].items():
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": scope,
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


def render_note(payload: dict[str, object]) -> str:
    return "\n".join(
        [
            "# P2 Historical Reference Boundary Audit V1",
            "",
            "## Summary",
            "- Audits p2 historical evidence/repro path references after p1 path-input lanes are closed.",
            "- This is a boundary audit, not a rewrite patch.",
            "- It blocks bulk historical path cleanup unless a stable replacement artifact, current handoff refresh, or reopened doc scope exists.",
            "",
            "## Counts",
            f"- path_portability_total_matches: `{payload['path_portability_total_matches']}`",
            f"- p2_historical_total_rows: `{payload['p2_historical_total_rows']}`",
            f"- p2_historical_evidence_rows: `{payload['p2_historical_evidence_rows']}`",
            f"- p2_historical_repro_rows: `{payload['p2_historical_repro_rows']}`",
            f"- stable_replacement_required_rows: `{payload['stable_replacement_required_rows']}`",
            f"- refresh_only_when_touching_doc_rows: `{payload['refresh_only_when_touching_doc_rows']}`",
            f"- current_handoff_rebuild_candidate_rows: `{payload['current_handoff_rebuild_candidate_rows']}`",
            f"- immediate_bulk_rewrite_allowed_rows: `{payload['immediate_bulk_rewrite_allowed_rows']}`",
            f"- runtime_semantic_change_allowed_rows: `{payload['runtime_semantic_change_allowed_rows']}`",
            f"- historical_boundary_complete: `{payload['historical_boundary_complete']}`",
            "",
            "## Boundary",
            "- Historical evidence references are preserved as provenance until a named stable artifact is materialized.",
            "- Historical doc repro references are refreshed only when the doc is reopened for current handoff use.",
            "- Generated handoff repro literals should be rebuilt through a refreshed manifest instead of edited one by one.",
            "",
            "## Next Action",
            f"- Recommended next branch: `{payload['recommended_next_branch']}`.",
            "- Keep this separate from runtime semantics and panel-engine code.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    path_rows = collect_path_rows(repo_root, args.max_file_bytes)
    detail_rows = build_detail_rows(path_rows)
    payload = build_payload(path_rows, detail_rows)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / DETAIL_OUTPUT_NAME, detail_rows, DETAIL_COLUMNS)
    write_csv(args.output_dir / SUMMARY_OUTPUT_NAME, summary_rows(payload), SUMMARY_COLUMNS)
    (args.output_dir / NOTE_OUTPUT_NAME).write_text(render_note(payload), encoding="utf-8")
    (args.output_dir / JSON_OUTPUT_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
