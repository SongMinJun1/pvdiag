#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    from build_path_portability_cleanup_axis_checkpoint_v1 import (
        build_detail_rows as build_checkpoint_detail_rows,
        build_final_rescan,
        build_payload as build_checkpoint_payload,
    )
except ImportError:
    from research.prognostics.build_path_portability_cleanup_axis_checkpoint_v1 import (
        build_detail_rows as build_checkpoint_detail_rows,
        build_final_rescan,
        build_payload as build_checkpoint_payload,
    )


OWNER_BRANCH = "BR-20260430-240"

DETAIL_OUTPUT_NAME = "path_portability_axis_closeout_decision_v1.csv"
SUMMARY_OUTPUT_NAME = "path_portability_axis_closeout_decision_summary_v1.csv"
NOTE_OUTPUT_NAME = "path_portability_axis_closeout_decision_note_v1.md"
JSON_OUTPUT_NAME = "path_portability_axis_closeout_decision_v1.json"

DETAIL_COLUMNS = [
    "owner_branch",
    "decision_id",
    "decision_group",
    "gate_key",
    "observed_value",
    "required_value",
    "decision_status",
    "decision",
    "reason",
    "runtime_semantic_change_allowed_rows",
    "operator_facing_change_allowed_rows",
    "engine_patch_allowed_rows",
    "bulk_rewrite_allowed_rows",
    "recommended_next_action",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Decide whether the path-portability cleanup axis needs a final cleanup PR "
            "or can be closed as a current blocker. This is audit-only."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for closeout decision outputs. Required to avoid hidden temp defaults.",
    )
    parser.add_argument("--max-file-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def build_checkpoint(repo_root: Path, max_file_bytes: int) -> dict[str, object]:
    final_payload = build_final_rescan(repo_root, max_file_bytes)
    checkpoint_rows = build_checkpoint_detail_rows(final_payload)
    return build_checkpoint_payload(checkpoint_rows, final_payload)


def decision_status(observed: int, required: int, comparator: str) -> str:
    if comparator == "eq":
        return "pass" if observed == required else "fail"
    if comparator == "ge":
        return "pass" if observed >= required else "fail"
    raise ValueError(f"unknown comparator: {comparator}")


def decision_row(
    index: int,
    group: str,
    gate_key: str,
    observed: int,
    required: int,
    comparator: str,
    decision: str,
    reason: str,
    recommended_next_action: str,
) -> dict[str, object]:
    return {
        "owner_branch": OWNER_BRANCH,
        "decision_id": f"BR240-{index:03d}",
        "decision_group": group,
        "gate_key": gate_key,
        "observed_value": observed,
        "required_value": required,
        "decision_status": decision_status(observed, required, comparator),
        "decision": decision,
        "reason": reason,
        "runtime_semantic_change_allowed_rows": 0,
        "operator_facing_change_allowed_rows": 0,
        "engine_patch_allowed_rows": 0,
        "bulk_rewrite_allowed_rows": 0,
        "recommended_next_action": recommended_next_action,
    }


def build_detail_rows(checkpoint_payload: dict[str, object]) -> list[dict[str, object]]:
    specs = [
        (
            "closeout_gate",
            "checkpoint_ready",
            int(checkpoint_payload["checkpoint_ready"]),
            1,
            "eq",
            "close_path_portability_axis_as_current_blocker",
            "BR-239 checkpoint is ready",
            "return to algorithm or field-trial readiness work",
        ),
        (
            "closeout_gate",
            "checkpoint_fail_rows",
            int(checkpoint_payload["checkpoint_fail_rows"]),
            0,
            "eq",
            "no_final_cleanup_pr_needed_for_failures",
            "no checkpoint row fails",
            "do not open a broad cleanup PR",
        ),
        (
            "closeout_gate",
            "path_portability_axis_current_blocker_rows",
            int(checkpoint_payload["path_portability_axis_current_blocker_rows"]),
            0,
            "eq",
            "no_current_blocking_debt_remaining",
            "current blocker rows are zero",
            "treat path portability as closed unless a future checkpoint fails",
        ),
        (
            "cleanup_pr_gate",
            "path_portability_zero_literal_cleanup_claim",
            int(checkpoint_payload["path_portability_zero_literal_cleanup_claim"]),
            0,
            "eq",
            "do_not_run_zero_literal_cleanup_pr",
            "zero-literal cleanup is intentionally not claimed",
            "preserve historical/provenance/context path text unless owner file is touched",
        ),
        (
            "cleanup_pr_gate",
            "path_portability_total_matches",
            int(checkpoint_payload["path_portability_total_matches"]),
            1,
            "ge",
            "remaining_literals_are_context_not_current_blockers",
            "visible historical/provenance/context path text remains",
            "avoid bulk rewrite; refresh only scoped owner lanes",
        ),
        (
            "resume_gate",
            "return_to_algorithm_or_field_trial_readiness_allowed",
            int(checkpoint_payload["return_to_algorithm_or_field_trial_readiness_allowed"]),
            1,
            "eq",
            "resume_algorithm_or_field_trial_readiness",
            "checkpoint explicitly allows returning to roadmap work",
            "move next branch to roadmap readiness rather than portability cleanup",
        ),
        (
            "write_boundary",
            "runtime_semantic_change_allowed_rows",
            int(checkpoint_payload["runtime_semantic_change_allowed_rows"]),
            0,
            "eq",
            "no_runtime_semantic_change",
            "path-portability closeout does not authorize runtime semantics",
            "route future semantic work through prepatch gates",
        ),
        (
            "write_boundary",
            "operator_facing_change_allowed_rows",
            int(checkpoint_payload["operator_facing_change_allowed_rows"]),
            0,
            "eq",
            "no_operator_facing_change",
            "path-portability closeout does not authorize output changes",
            "keep output changes behind explicit operator review",
        ),
        (
            "write_boundary",
            "engine_patch_allowed_rows",
            int(checkpoint_payload["engine_patch_allowed_rows"]),
            0,
            "eq",
            "no_engine_patch",
            "path-portability closeout does not authorize panel-engine edits",
            "do not touch pv_ae/panel_day_engine.py in this axis",
        ),
        (
            "write_boundary",
            "bulk_rewrite_allowed_rows",
            int(checkpoint_payload["bulk_rewrite_allowed_rows"]),
            0,
            "eq",
            "no_bulk_rewrite",
            "broad literal cleanup remains disallowed",
            "open owner-scoped refresh branches only when needed",
        ),
    ]
    return [
        decision_row(index, *spec)
        for index, spec in enumerate(specs, start=1)
    ]


def build_payload(
    detail_rows: list[dict[str, object]],
    checkpoint_payload: dict[str, object],
) -> dict[str, object]:
    status_counts = Counter(str(row["decision_status"]) for row in detail_rows)
    group_counts = Counter(str(row["decision_group"]) for row in detail_rows)
    fail_rows = status_counts.get("fail", 0)
    runtime_allowed = sum(int(row["runtime_semantic_change_allowed_rows"]) for row in detail_rows)
    operator_allowed = sum(int(row["operator_facing_change_allowed_rows"]) for row in detail_rows)
    engine_allowed = sum(int(row["engine_patch_allowed_rows"]) for row in detail_rows)
    bulk_allowed = sum(int(row["bulk_rewrite_allowed_rows"]) for row in detail_rows)
    closeout_ready = int(
        fail_rows == 0
        and runtime_allowed == 0
        and operator_allowed == 0
        and engine_allowed == 0
        and bulk_allowed == 0
    )
    final_cleanup_pr_required = int(
        not (
            closeout_ready
            and int(checkpoint_payload["path_portability_axis_current_blocker_rows"]) == 0
            and int(checkpoint_payload["path_portability_zero_literal_cleanup_claim"]) == 0
        )
    )
    return {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision_rows": len(detail_rows),
        "decision_pass_rows": status_counts.get("pass", 0),
        "decision_fail_rows": fail_rows,
        "path_portability_axis_closeout_ready": closeout_ready,
        "final_cleanup_pr_required": final_cleanup_pr_required,
        "path_portability_axis_status": (
            "closed_as_current_blocker"
            if closeout_ready and final_cleanup_pr_required == 0
            else "reopen_cleanup_axis"
        ),
        "next_workstream_allowed": int(closeout_ready and final_cleanup_pr_required == 0),
        "path_portability_axis_current_blocker_rows": int(
            checkpoint_payload["path_portability_axis_current_blocker_rows"]
        ),
        "path_portability_zero_literal_cleanup_claim": int(
            checkpoint_payload["path_portability_zero_literal_cleanup_claim"]
        ),
        "path_portability_total_matches": int(checkpoint_payload["path_portability_total_matches"]),
        "p1_live_temp_reference_rows": int(checkpoint_payload["p1_live_temp_reference_rows"]),
        "p1_temp_input_default_rows": int(checkpoint_payload["p1_temp_input_default_rows"]),
        "p2_historical_evidence_rows": int(checkpoint_payload["p2_historical_evidence_rows"]),
        "p2_historical_repro_rows": int(checkpoint_payload["p2_historical_repro_rows"]),
        "generated_residual_rows": int(checkpoint_payload["generated_residual_rows"]),
        "runtime_semantic_change_allowed_rows": runtime_allowed,
        "operator_facing_change_allowed_rows": operator_allowed,
        "engine_patch_allowed_rows": engine_allowed,
        "bulk_rewrite_allowed_rows": bulk_allowed,
        "decision_status_counts": dict(sorted(status_counts.items())),
        "decision_group_counts": dict(sorted(group_counts.items())),
        "recommended_next_branch": (
            "return_to_algorithm_or_field_trial_readiness_roadmap"
            if closeout_ready and final_cleanup_pr_required == 0
            else "path_portability_final_cleanup_or_failure_review"
        ),
    }


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    scalar_keys = [
        "decision_rows",
        "decision_pass_rows",
        "decision_fail_rows",
        "path_portability_axis_closeout_ready",
        "final_cleanup_pr_required",
        "next_workstream_allowed",
        "path_portability_axis_current_blocker_rows",
        "path_portability_zero_literal_cleanup_claim",
        "path_portability_total_matches",
        "p1_live_temp_reference_rows",
        "p1_temp_input_default_rows",
        "p2_historical_evidence_rows",
        "p2_historical_repro_rows",
        "generated_residual_rows",
        "runtime_semantic_change_allowed_rows",
        "operator_facing_change_allowed_rows",
        "engine_patch_allowed_rows",
        "bulk_rewrite_allowed_rows",
    ]
    rows: list[dict[str, object]] = []
    for key in scalar_keys:
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "overall",
                "key": key,
                "count": int(payload[key]),
            }
        )
    for scope_key in ["decision_status_counts", "decision_group_counts"]:
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
            "# Path Portability Axis Closeout Decision V1",
            "",
            "## Summary",
            "- Decides whether a final path-portability cleanup PR is needed.",
            "- Reuses the BR-239 checkpoint and keeps the zero-literal boundary explicit.",
            "- This is audit-only; it does not alter runtime semantics, operator-facing outputs, or panel-engine code.",
            "",
            "## Decision",
            f"- path_portability_axis_closeout_ready: `{payload['path_portability_axis_closeout_ready']}`",
            f"- final_cleanup_pr_required: `{payload['final_cleanup_pr_required']}`",
            f"- path_portability_axis_status: `{payload['path_portability_axis_status']}`",
            f"- next_workstream_allowed: `{payload['next_workstream_allowed']}`",
            "",
            "## Evidence",
            f"- decision_fail_rows: `{payload['decision_fail_rows']}`",
            f"- path_portability_axis_current_blocker_rows: `{payload['path_portability_axis_current_blocker_rows']}`",
            f"- path_portability_zero_literal_cleanup_claim: `{payload['path_portability_zero_literal_cleanup_claim']}`",
            f"- path_portability_total_matches: `{payload['path_portability_total_matches']}`",
            f"- generated_residual_rows: `{payload['generated_residual_rows']}`",
            "",
            "## Boundary",
            "- No final bulk cleanup PR is required while current blocker rows are zero and zero-literal cleanup is not claimed.",
            "- Remaining p1/p2/p3 path literals are owner-touch context, not active blockers.",
            "- Reopen this axis only if a checkpoint row fails or an owner-file touch needs a scoped refresh.",
            "",
            "## Next Decision",
            f"- Next safe branch: `{payload['recommended_next_branch']}`.",
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

    checkpoint_payload = build_checkpoint(repo_root, args.max_file_bytes)
    detail_rows = build_detail_rows(checkpoint_payload)
    payload = build_payload(detail_rows, checkpoint_payload)

    write_csv(output_dir / DETAIL_OUTPUT_NAME, detail_rows, DETAIL_COLUMNS)
    write_csv(output_dir / SUMMARY_OUTPUT_NAME, summary_rows(payload), SUMMARY_COLUMNS)
    (output_dir / NOTE_OUTPUT_NAME).write_text(render_note(payload), encoding="utf-8")
    (output_dir / JSON_OUTPUT_NAME).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
