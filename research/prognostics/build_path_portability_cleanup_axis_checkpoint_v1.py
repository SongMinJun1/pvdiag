#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    from build_generated_residual_closure_audit_v1 import (
        build_detail_rows as build_generated_detail_rows,
        build_payload as build_generated_payload,
    )
    from build_path_portability_final_rescan_v1 import (
        build_detail_rows as build_final_rescan_detail_rows,
        build_payload as build_final_rescan_payload,
        collect_path_rows,
    )
except ImportError:
    from research.prognostics.build_generated_residual_closure_audit_v1 import (
        build_detail_rows as build_generated_detail_rows,
        build_payload as build_generated_payload,
    )
    from research.prognostics.build_path_portability_final_rescan_v1 import (
        build_detail_rows as build_final_rescan_detail_rows,
        build_payload as build_final_rescan_payload,
        collect_path_rows,
    )


OWNER_BRANCH = "BR-20260430-239"

DETAIL_OUTPUT_NAME = "path_portability_cleanup_axis_checkpoint_v1.csv"
SUMMARY_OUTPUT_NAME = "path_portability_cleanup_axis_checkpoint_summary_v1.csv"
NOTE_OUTPUT_NAME = "path_portability_cleanup_axis_checkpoint_note_v1.md"
JSON_OUTPUT_NAME = "path_portability_cleanup_axis_checkpoint_v1.json"

DETAIL_COLUMNS = [
    "owner_branch",
    "checkpoint_id",
    "checkpoint_group",
    "gate_key",
    "observed_value",
    "required_value",
    "checkpoint_status",
    "axis_claim",
    "reopen_trigger",
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
            "Record the closeout checkpoint for the path-portability cleanup axis. "
            "This reuses the BR-238 final rescan and does not alter runtime logic."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for checkpoint outputs. Required to avoid hidden temp defaults.",
    )
    parser.add_argument("--max-file-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def build_final_rescan(repo_root: Path, max_file_bytes: int) -> dict[str, object]:
    path_rows = collect_path_rows(repo_root, max_file_bytes)
    generated_rows, _path_portability_total = build_generated_detail_rows(
        repo_root,
        max_file_bytes,
    )
    generated_payload = build_generated_payload(generated_rows, len(path_rows))
    detail_rows = build_final_rescan_detail_rows(path_rows, generated_payload)
    return build_final_rescan_payload(path_rows, detail_rows, generated_payload)


def status_for(observed: int, required: int, comparator: str) -> str:
    if comparator == "eq":
        return "pass" if observed == required else "fail"
    if comparator == "ge":
        return "pass" if observed >= required else "fail"
    raise ValueError(f"unknown comparator: {comparator}")


def checkpoint_row(
    index: int,
    group: str,
    gate_key: str,
    observed: int,
    required: int,
    comparator: str,
    axis_claim: str,
    reopen_trigger: str,
    recommended_next_action: str,
) -> dict[str, object]:
    return {
        "owner_branch": OWNER_BRANCH,
        "checkpoint_id": f"BR239-{index:03d}",
        "checkpoint_group": group,
        "gate_key": gate_key,
        "observed_value": observed,
        "required_value": required,
        "checkpoint_status": status_for(observed, required, comparator),
        "axis_claim": axis_claim,
        "reopen_trigger": reopen_trigger,
        "runtime_semantic_change_allowed_rows": 0,
        "operator_facing_change_allowed_rows": 0,
        "engine_patch_allowed_rows": 0,
        "bulk_rewrite_allowed_rows": 0,
        "recommended_next_action": recommended_next_action,
    }


def build_detail_rows(final_payload: dict[str, object]) -> list[dict[str, object]]:
    specs = [
        (
            "current_blocking_gate",
            "blocking_open_rows",
            int(final_payload["blocking_open_rows"]),
            0,
            "eq",
            "path portability is not a current blocker",
            "blocking_open_rows becomes nonzero in final rescan",
            "reopen the owning path-portability lane before algorithm work",
        ),
        (
            "current_blocking_gate",
            "final_rescan_complete",
            int(final_payload["final_rescan_complete"]),
            1,
            "eq",
            "BR-238 final rescan is passing",
            "final_rescan_complete becomes 0",
            "rerun BR-238 and inspect failed gate rows",
        ),
        (
            "generated_residual_gate",
            "generated_residual_closure_complete",
            int(final_payload["generated_residual_closure_complete"]),
            1,
            "eq",
            "generated residual lane is closed for current blockers",
            "generated_residual_closure_complete becomes 0",
            "inspect generated residual closure before continuing",
        ),
        (
            "generated_residual_gate",
            "latest_handoff_residual_rows",
            int(final_payload["latest_handoff_residual_rows"]),
            0,
            "eq",
            "latest handoff generated residuals are clear",
            "latest handoff residual rows reappear",
            "refresh latest handoff generator output via manifestized commands",
        ),
        (
            "generated_residual_gate",
            "evidence_manifest_residual_rows",
            int(final_payload["evidence_manifest_residual_rows"]),
            0,
            "eq",
            "evidence manifest generated residuals are clear",
            "evidence manifest residual rows reappear",
            "refresh evidence manifest builder constants",
        ),
        (
            "historical_literal_boundary",
            "path_portability_zero_literal_cleanup_complete",
            int(final_payload["path_portability_zero_literal_cleanup_complete"]),
            0,
            "eq",
            "zero-literal cleanup is explicitly not claimed",
            "zero-literal flag changes without a dedicated cleanup branch",
            "do not conflate visible historical literals with current blockers",
        ),
        (
            "historical_literal_boundary",
            "path_portability_total_matches",
            int(final_payload["path_portability_total_matches"]),
            1,
            "ge",
            "historical/provenance/context path text remains visible",
            "total path matches unexpectedly drop to zero",
            "verify no broad rewrite erased historical reproducibility context",
        ),
        (
            "write_boundary",
            "runtime_semantic_change_allowed_rows",
            int(final_payload["runtime_semantic_change_allowed_rows"]),
            0,
            "eq",
            "runtime semantics stay untouched",
            "runtime semantic allowance becomes nonzero",
            "stop and route through the algorithm prepatch gate",
        ),
        (
            "write_boundary",
            "operator_facing_change_allowed_rows",
            int(final_payload["operator_facing_change_allowed_rows"]),
            0,
            "eq",
            "operator-facing outputs stay untouched",
            "operator-facing allowance becomes nonzero",
            "stop and require explicit operator-output review",
        ),
        (
            "write_boundary",
            "bulk_rewrite_allowed_rows",
            int(final_payload["bulk_rewrite_allowed_rows"]),
            0,
            "eq",
            "bulk path rewrite remains disallowed",
            "bulk rewrite allowance becomes nonzero",
            "split owner-file refreshes instead of broad literal editing",
        ),
    ]
    return [
        checkpoint_row(index, *spec)
        for index, spec in enumerate(specs, start=1)
    ]


def build_payload(
    detail_rows: list[dict[str, object]],
    final_payload: dict[str, object],
) -> dict[str, object]:
    status_counts = Counter(str(row["checkpoint_status"]) for row in detail_rows)
    group_counts = Counter(str(row["checkpoint_group"]) for row in detail_rows)
    failed_rows = status_counts.get("fail", 0)
    runtime_allowed = sum(int(row["runtime_semantic_change_allowed_rows"]) for row in detail_rows)
    operator_allowed = sum(int(row["operator_facing_change_allowed_rows"]) for row in detail_rows)
    engine_allowed = sum(int(row["engine_patch_allowed_rows"]) for row in detail_rows)
    bulk_allowed = sum(int(row["bulk_rewrite_allowed_rows"]) for row in detail_rows)
    checkpoint_ready = int(
        failed_rows == 0
        and runtime_allowed == 0
        and operator_allowed == 0
        and engine_allowed == 0
        and bulk_allowed == 0
    )
    return {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "checkpoint_rows": len(detail_rows),
        "checkpoint_pass_rows": status_counts.get("pass", 0),
        "checkpoint_fail_rows": failed_rows,
        "checkpoint_ready": checkpoint_ready,
        "path_portability_axis_current_blocker_rows": int(final_payload["blocking_open_rows"]),
        "path_portability_axis_currently_blocking": int(
            int(final_payload["blocking_open_rows"]) > 0
        ),
        "path_portability_axis_closed_as_current_blocker": checkpoint_ready,
        "path_portability_zero_literal_cleanup_claim": int(
            final_payload["path_portability_zero_literal_cleanup_complete"]
        ),
        "path_portability_total_matches": int(final_payload["path_portability_total_matches"]),
        "p1_live_temp_reference_rows": int(final_payload["p1_live_temp_reference_rows"]),
        "p1_temp_input_default_rows": int(final_payload["p1_temp_input_default_rows"]),
        "p2_historical_evidence_rows": int(final_payload["p2_historical_evidence_rows"]),
        "p2_historical_repro_rows": int(final_payload["p2_historical_repro_rows"]),
        "generated_residual_rows": int(final_payload["generated_residual_rows"]),
        "episode_note_deferred_rows": int(final_payload["episode_note_deferred_rows"]),
        "validation_output_preserved_rows": int(final_payload["validation_output_preserved_rows"]),
        "runtime_semantic_change_allowed_rows": runtime_allowed,
        "operator_facing_change_allowed_rows": operator_allowed,
        "engine_patch_allowed_rows": engine_allowed,
        "bulk_rewrite_allowed_rows": bulk_allowed,
        "return_to_algorithm_or_field_trial_readiness_allowed": checkpoint_ready,
        "checkpoint_status_counts": dict(sorted(status_counts.items())),
        "checkpoint_group_counts": dict(sorted(group_counts.items())),
        "upstream_final_rescan_closure_claim": str(final_payload["closure_claim"]),
        "recommended_next_branch": (
            "return_to_algorithm_or_field_trial_readiness_roadmap"
            if checkpoint_ready
            else "inspect_path_portability_cleanup_axis_checkpoint_failures"
        ),
    }


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    scalar_keys = [
        "checkpoint_rows",
        "checkpoint_pass_rows",
        "checkpoint_fail_rows",
        "checkpoint_ready",
        "path_portability_axis_current_blocker_rows",
        "path_portability_axis_currently_blocking",
        "path_portability_axis_closed_as_current_blocker",
        "path_portability_zero_literal_cleanup_claim",
        "path_portability_total_matches",
        "p1_live_temp_reference_rows",
        "p1_temp_input_default_rows",
        "p2_historical_evidence_rows",
        "p2_historical_repro_rows",
        "generated_residual_rows",
        "episode_note_deferred_rows",
        "validation_output_preserved_rows",
        "runtime_semantic_change_allowed_rows",
        "operator_facing_change_allowed_rows",
        "engine_patch_allowed_rows",
        "bulk_rewrite_allowed_rows",
        "return_to_algorithm_or_field_trial_readiness_allowed",
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
    for scope_key in ["checkpoint_status_counts", "checkpoint_group_counts"]:
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
            "# Path Portability Cleanup Axis Checkpoint V1",
            "",
            "## Summary",
            "- Records the closeout checkpoint for the path-portability cleanup axis.",
            "- Reuses the BR-238 final rescan instead of making a manual judgment.",
            "- This is audit-only; it does not change runtime semantics, operator-facing outputs, or panel-engine code.",
            "",
            "## Checkpoint Result",
            f"- checkpoint_ready: `{payload['checkpoint_ready']}`",
            f"- checkpoint_fail_rows: `{payload['checkpoint_fail_rows']}`",
            f"- path_portability_axis_current_blocker_rows: `{payload['path_portability_axis_current_blocker_rows']}`",
            f"- path_portability_axis_closed_as_current_blocker: `{payload['path_portability_axis_closed_as_current_blocker']}`",
            f"- path_portability_zero_literal_cleanup_claim: `{payload['path_portability_zero_literal_cleanup_claim']}`",
            f"- return_to_algorithm_or_field_trial_readiness_allowed: `{payload['return_to_algorithm_or_field_trial_readiness_allowed']}`",
            "",
            "## Important Boundary",
            "- This checkpoint does not claim every path literal has been removed.",
            f"- `path_portability_total_matches` remains `{payload['path_portability_total_matches']}`.",
            "- Remaining broad p1/p2/p3 rows are visible context for future owner-file touches, not current blocking debt.",
            "- If any checkpoint row fails later, reopen the specific path-portability owner lane before algorithm work.",
            "",
            "## Next Decision",
            f"- Next safe branch: `{payload['recommended_next_branch']}`.",
            "- Resume algorithm or field-trial readiness work with this cleanup axis no longer treated as the active blocker.",
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

    final_payload = build_final_rescan(repo_root, args.max_file_bytes)
    detail_rows = build_detail_rows(final_payload)
    payload = build_payload(detail_rows, final_payload)

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
