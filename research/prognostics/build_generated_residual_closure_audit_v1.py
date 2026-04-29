#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    from build_generated_handoff_repro_literal_post_br232_rescan_v1 import (
        build_rows as build_post_br232_rescan_rows,
    )
except ImportError:
    from research.prognostics.build_generated_handoff_repro_literal_post_br232_rescan_v1 import (
        build_rows as build_post_br232_rescan_rows,
    )


OWNER_BRANCH = "BR-20260429-237"

DETAIL_OUTPUT_NAME = "generated_residual_closure_audit_v1.csv"
SUMMARY_OUTPUT_NAME = "generated_residual_closure_audit_summary_v1.csv"
NOTE_OUTPUT_NAME = "generated_residual_closure_audit_note_v1.md"
JSON_OUTPUT_NAME = "generated_residual_closure_audit_v1.json"

DETAIL_COLUMNS = [
    "owner_branch",
    "closure_id",
    "source_rescan_id",
    "relative_path",
    "line_no",
    "literal_role",
    "post_br232_residual_lane",
    "post_br232_status",
    "closure_bucket",
    "closure_decision",
    "current_action_required",
    "safe_to_leave_in_place",
    "reopen_trigger",
    "manual_literal_edit_allowed",
    "runtime_semantic_change_allowed_rows",
    "operator_facing_change_allowed_rows",
    "recommended_next_action",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Close the remaining generated handoff/repro residuals after the latest handoff "
            "and evidence manifest repro refreshes. This is audit-only."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for closure audit outputs. Required to avoid hidden temp defaults.",
    )
    parser.add_argument("--max-file-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def classify_closure(row: dict[str, object]) -> dict[str, object]:
    lane = str(row.get("post_br232_residual_lane", ""))
    if lane == "episode_note_repro_deferred":
        return {
            "closure_bucket": "deferred_note_repro_only",
            "closure_decision": "closed_until_episode_truth_map_touched",
            "current_action_required": 0,
            "safe_to_leave_in_place": 1,
            "reopen_trigger": "touching build_panel_day_engine_episode_truth_map_v1.py",
            "recommended_next_action": (
                "defer; when the episode truth map note is touched, refresh the generated "
                "repo-root repro text to use --repo-root \"$(pwd)\""
            ),
        }
    if lane == "validation_output_destination_preserved":
        return {
            "closure_bucket": "intentional_validation_output_destination",
            "closure_decision": "preserved_not_input_debt",
            "current_action_required": 0,
            "safe_to_leave_in_place": 1,
            "reopen_trigger": "only if validation output destination policy changes",
            "recommended_next_action": (
                "preserve as explicit validation output destination; do not treat as a "
                "handoff input or stale evidence root"
            ),
        }
    return {
        "closure_bucket": "unexpected_generated_residual",
        "closure_decision": "reopen_before_next_cleanup",
        "current_action_required": 1,
        "safe_to_leave_in_place": 0,
        "reopen_trigger": "immediate_manual_review",
        "recommended_next_action": "inspect this residual before claiming generated closure",
    }


def build_detail_rows(repo_root: Path, max_file_bytes: int) -> tuple[list[dict[str, object]], int]:
    rescan_rows, path_portability_total = build_post_br232_rescan_rows(repo_root, max_file_bytes)
    rows: list[dict[str, object]] = []
    for index, row in enumerate(rescan_rows, start=1):
        closure = classify_closure(row)
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "closure_id": f"BR237-{index:03d}",
                "source_rescan_id": row.get("rescan_id", ""),
                "relative_path": row.get("relative_path", ""),
                "line_no": row.get("line_no", ""),
                "literal_role": row.get("literal_role", ""),
                "post_br232_residual_lane": row.get("post_br232_residual_lane", ""),
                "post_br232_status": row.get("post_br232_status", ""),
                "closure_bucket": closure["closure_bucket"],
                "closure_decision": closure["closure_decision"],
                "current_action_required": closure["current_action_required"],
                "safe_to_leave_in_place": closure["safe_to_leave_in_place"],
                "reopen_trigger": closure["reopen_trigger"],
                "manual_literal_edit_allowed": 0,
                "runtime_semantic_change_allowed_rows": 0,
                "operator_facing_change_allowed_rows": 0,
                "recommended_next_action": closure["recommended_next_action"],
            }
        )
    return rows, path_portability_total


def build_payload(rows: list[dict[str, object]], path_portability_total: int) -> dict[str, object]:
    role_counts = Counter(str(row["literal_role"]) for row in rows)
    lane_counts = Counter(str(row["post_br232_residual_lane"]) for row in rows)
    bucket_counts = Counter(str(row["closure_bucket"]) for row in rows)
    decision_counts = Counter(str(row["closure_decision"]) for row in rows)
    file_counts = Counter(str(row["relative_path"]) for row in rows)

    action_required = sum(int(row["current_action_required"]) for row in rows)
    safe_rows = sum(int(row["safe_to_leave_in_place"]) for row in rows)
    manual_allowed = sum(int(row["manual_literal_edit_allowed"]) for row in rows)
    runtime_allowed = sum(int(row["runtime_semantic_change_allowed_rows"]) for row in rows)
    operator_allowed = sum(int(row["operator_facing_change_allowed_rows"]) for row in rows)
    latest_rows = role_counts.get("latest_evidence_handoff_manifest_repro", 0)
    evidence_rows = role_counts.get("evidence_pack_manifest_repro", 0)
    episode_rows = role_counts.get("generated_note_repo_root_repro", 0)
    validation_rows = role_counts.get("validation_output_dir_literal", 0)

    return {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "path_portability_total_matches": path_portability_total,
        "generated_residual_rows": len(rows),
        "latest_handoff_residual_rows": latest_rows,
        "evidence_manifest_residual_rows": evidence_rows,
        "episode_note_deferred_rows": episode_rows,
        "validation_output_preserved_rows": validation_rows,
        "current_action_required_rows": action_required,
        "safe_to_leave_in_place_rows": safe_rows,
        "deferred_until_touched_rows": bucket_counts.get("deferred_note_repro_only", 0),
        "intentional_output_destination_rows": bucket_counts.get(
            "intentional_validation_output_destination",
            0,
        ),
        "unexpected_generated_residual_rows": bucket_counts.get("unexpected_generated_residual", 0),
        "manual_literal_edit_allowed_rows": manual_allowed,
        "runtime_semantic_change_allowed_rows": runtime_allowed,
        "operator_facing_change_allowed_rows": operator_allowed,
        "generated_residual_closure_complete": int(
            len(rows) == 2
            and latest_rows == 0
            and evidence_rows == 0
            and episode_rows == 1
            and validation_rows == 1
            and action_required == 0
            and safe_rows == 2
            and manual_allowed == 0
            and runtime_allowed == 0
            and operator_allowed == 0
        ),
        "literal_role_counts": dict(sorted(role_counts.items())),
        "post_br232_residual_lane_counts": dict(sorted(lane_counts.items())),
        "closure_bucket_counts": dict(sorted(bucket_counts.items())),
        "closure_decision_counts": dict(sorted(decision_counts.items())),
        "relative_path_counts": dict(sorted(file_counts.items())),
        "recommended_next_branch": "path_portability_final_rescan",
    }


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scalar_keys = [
        "path_portability_total_matches",
        "generated_residual_rows",
        "latest_handoff_residual_rows",
        "evidence_manifest_residual_rows",
        "episode_note_deferred_rows",
        "validation_output_preserved_rows",
        "current_action_required_rows",
        "safe_to_leave_in_place_rows",
        "deferred_until_touched_rows",
        "intentional_output_destination_rows",
        "unexpected_generated_residual_rows",
        "manual_literal_edit_allowed_rows",
        "runtime_semantic_change_allowed_rows",
        "operator_facing_change_allowed_rows",
        "generated_residual_closure_complete",
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
        "literal_role_counts",
        "post_br232_residual_lane_counts",
        "closure_bucket_counts",
        "closure_decision_counts",
        "relative_path_counts",
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


def render_note(payload: dict[str, object]) -> str:
    return "\n".join(
        [
            "# Generated Residual Closure Audit V1",
            "",
            "## Summary",
            "- Closes the remaining generated handoff/repro residuals after BR-236.",
            "- Confirms there are no latest-handoff or evidence-manifest repro residuals left.",
            "- This is audit-only; it does not rewrite note text, validation output destinations, runtime semantics, or operator-facing outputs.",
            "",
            "## Counts",
            f"- generated_residual_rows: `{payload['generated_residual_rows']}`",
            f"- latest_handoff_residual_rows: `{payload['latest_handoff_residual_rows']}`",
            f"- evidence_manifest_residual_rows: `{payload['evidence_manifest_residual_rows']}`",
            f"- episode_note_deferred_rows: `{payload['episode_note_deferred_rows']}`",
            f"- validation_output_preserved_rows: `{payload['validation_output_preserved_rows']}`",
            f"- current_action_required_rows: `{payload['current_action_required_rows']}`",
            f"- safe_to_leave_in_place_rows: `{payload['safe_to_leave_in_place_rows']}`",
            f"- manual_literal_edit_allowed_rows: `{payload['manual_literal_edit_allowed_rows']}`",
            f"- runtime_semantic_change_allowed_rows: `{payload['runtime_semantic_change_allowed_rows']}`",
            f"- operator_facing_change_allowed_rows: `{payload['operator_facing_change_allowed_rows']}`",
            f"- generated_residual_closure_complete: `{payload['generated_residual_closure_complete']}`",
            "",
            "## Boundary",
            "- The episode note repro row is deferred until the episode truth map note is touched.",
            "- The validation output literal is preserved as an explicit output destination.",
            "- Any new latest-handoff or evidence-manifest residual should reopen the portability lane.",
            "",
            "## Next Decision",
            f"- Next safe branch: `{payload['recommended_next_branch']}`.",
            "- Run a broader portability rescan before declaring this cleanup axis closed.",
        ]
    ) + "\n"


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    rows, path_portability_total = build_detail_rows(repo_root, args.max_file_bytes)
    payload = build_payload(rows, path_portability_total)

    write_csv(output_dir / DETAIL_OUTPUT_NAME, rows, DETAIL_COLUMNS)
    write_csv(output_dir / SUMMARY_OUTPUT_NAME, summary_rows(payload), SUMMARY_COLUMNS)
    (output_dir / NOTE_OUTPUT_NAME).write_text(render_note(payload), encoding="utf-8")
    (output_dir / JSON_OUTPUT_NAME).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote generated residual closure audit to {output_dir}")


if __name__ == "__main__":
    main()
