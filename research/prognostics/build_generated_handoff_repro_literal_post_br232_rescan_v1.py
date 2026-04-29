#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    from build_generated_handoff_repro_literal_audit_v1 import (
        build_detail_rows as build_generated_literal_rows,
    )
except ImportError:
    from research.prognostics.build_generated_handoff_repro_literal_audit_v1 import (
        build_detail_rows as build_generated_literal_rows,
    )


OWNER_BRANCH = "BR-20260429-233"

DETAIL_OUTPUT_NAME = "generated_handoff_repro_literal_post_br232_rescan_v1.csv"
SUMMARY_OUTPUT_NAME = "generated_handoff_repro_literal_post_br232_rescan_summary_v1.csv"
NOTE_OUTPUT_NAME = "generated_handoff_repro_literal_post_br232_rescan_note_v1.md"
JSON_OUTPUT_NAME = "generated_handoff_repro_literal_post_br232_rescan_v1.json"

BR228_GENERATED_LITERAL_ROWS = 50
BR228_LATEST_HANDOFF_ROWS = 41
BR228_EVIDENCE_MANIFEST_ROWS = 7
BR228_EPISODE_NOTE_ROWS = 1
BR228_VALIDATION_OUTPUT_ROWS = 1
BR228_MANIFESTIZED_REBUILD_CANDIDATE_ROWS = 48

DETAIL_COLUMNS = [
    "owner_branch",
    "rescan_id",
    "source_literal_id",
    "relative_path",
    "line_no",
    "literal_role",
    "current_handoff_relevance",
    "refresh_policy",
    "matched_text",
    "post_br232_residual_lane",
    "post_br232_status",
    "next_branch_hint",
    "manifestized_rebuild_candidate",
    "intentional_validation_output_literal",
    "manual_literal_edit_allowed",
    "runtime_semantic_change_allowed_rows",
    "operator_facing_change_allowed_rows",
    "recommended_next_action",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Re-scan generated handoff/repro literals after BR-231/232 and lock the remaining "
            "residual lanes without changing runtime behavior."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for rescan outputs. Required to avoid hidden temp defaults.",
    )
    parser.add_argument("--max-file-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def classify_residual(row: dict[str, object]) -> tuple[str, str, str, str]:
    literal_role = str(row.get("literal_role", ""))
    if literal_role == "latest_evidence_handoff_manifest_repro":
        return (
            "unexpected_latest_handoff_residual",
            "failed_latest_handoff_regression",
            "stop_and_reopen_latest_handoff_portability",
            "latest handoff should stay closed after BR-232; inspect immediately",
        )
    if literal_role == "evidence_pack_manifest_repro":
        return (
            "evidence_manifest_repro_next_lane",
            "open_supporting_manifest_refresh",
            "evidence_manifest_repro_refresh_plan",
            "plan evidence manifest parameterization before rewriting generated literals",
        )
    if literal_role == "generated_note_repo_root_repro":
        return (
            "episode_note_repro_deferred",
            "deferred_until_episode_truth_map_touch",
            "episode_truth_map_note_repro_refresh_when_touched",
            "defer unless reopening episode truth map note; then use --repo-root \"$(pwd)\"",
        )
    if literal_role == "validation_output_dir_literal":
        return (
            "validation_output_destination_preserved",
            "closed_intentional_output_destination",
            "none_preserve_output_literal",
            "preserve as explicit validation output destination, not handoff input debt",
        )
    return (
        "manual_review_residual",
        "needs_manual_review",
        "manual_review_before_patch",
        "inspect residual literal before changing it",
    )


def build_rows(repo_root: Path, max_file_bytes: int) -> tuple[list[dict[str, object]], int]:
    path_rows, source_rows = build_generated_literal_rows(repo_root, max_file_bytes)
    rows: list[dict[str, object]] = []
    for index, row in enumerate(source_rows, start=1):
        lane, status, next_branch, next_action = classify_residual(row)
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "rescan_id": f"BR233-{index:03d}",
                "source_literal_id": row.get("literal_id", ""),
                "relative_path": row.get("relative_path", ""),
                "line_no": row.get("line_no", ""),
                "literal_role": row.get("literal_role", ""),
                "current_handoff_relevance": row.get("current_handoff_relevance", ""),
                "refresh_policy": row.get("refresh_policy", ""),
                "matched_text": row.get("matched_text", ""),
                "post_br232_residual_lane": lane,
                "post_br232_status": status,
                "next_branch_hint": next_branch,
                "manifestized_rebuild_candidate": int(row.get("manifestized_rebuild_candidate", 0)),
                "intentional_validation_output_literal": int(
                    row.get("intentional_validation_output_literal", 0)
                ),
                "manual_literal_edit_allowed": int(row.get("manual_literal_edit_allowed", 0)),
                "runtime_semantic_change_allowed_rows": 0,
                "operator_facing_change_allowed_rows": 0,
                "recommended_next_action": next_action,
            }
        )
    return rows, len(path_rows)


def build_payload(rows: list[dict[str, object]], path_portability_total: int) -> dict[str, object]:
    role_counts = Counter(str(row["literal_role"]) for row in rows)
    lane_counts = Counter(str(row["post_br232_residual_lane"]) for row in rows)
    status_counts = Counter(str(row["post_br232_status"]) for row in rows)
    file_counts = Counter(str(row["relative_path"]) for row in rows)

    latest_rows = role_counts.get("latest_evidence_handoff_manifest_repro", 0)
    evidence_rows = role_counts.get("evidence_pack_manifest_repro", 0)
    episode_rows = role_counts.get("generated_note_repo_root_repro", 0)
    validation_rows = role_counts.get("validation_output_dir_literal", 0)
    manual_allowed = sum(int(row["manual_literal_edit_allowed"]) for row in rows)
    manifestized = sum(int(row["manifestized_rebuild_candidate"]) for row in rows)
    validation_intentional = sum(int(row["intentional_validation_output_literal"]) for row in rows)
    runtime_allowed = sum(int(row["runtime_semantic_change_allowed_rows"]) for row in rows)
    operator_allowed = sum(int(row["operator_facing_change_allowed_rows"]) for row in rows)

    return {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "path_portability_total_matches": path_portability_total,
        "post_br232_generated_handoff_repro_literal_rows": len(rows),
        "latest_handoff_manifest_repro_rows": latest_rows,
        "evidence_manifest_repro_rows": evidence_rows,
        "episode_note_repro_rows": episode_rows,
        "validation_output_literal_rows": validation_rows,
        "manifestized_rebuild_candidate_rows": manifestized,
        "intentional_validation_output_literal_rows": validation_intentional,
        "manual_literal_edit_allowed_rows": manual_allowed,
        "runtime_semantic_change_allowed_rows": runtime_allowed,
        "operator_facing_change_allowed_rows": operator_allowed,
        "br228_generated_literal_rows": BR228_GENERATED_LITERAL_ROWS,
        "br228_latest_handoff_rows": BR228_LATEST_HANDOFF_ROWS,
        "br228_evidence_manifest_rows": BR228_EVIDENCE_MANIFEST_ROWS,
        "br228_episode_note_rows": BR228_EPISODE_NOTE_ROWS,
        "br228_validation_output_rows": BR228_VALIDATION_OUTPUT_ROWS,
        "br228_manifestized_rebuild_candidate_rows": BR228_MANIFESTIZED_REBUILD_CANDIDATE_ROWS,
        "generated_literal_drop_since_br228": BR228_GENERATED_LITERAL_ROWS - len(rows),
        "latest_handoff_drop_since_br228": BR228_LATEST_HANDOFF_ROWS - latest_rows,
        "manifestized_rebuild_drop_since_br228": BR228_MANIFESTIZED_REBUILD_CANDIDATE_ROWS
        - manifestized,
        "latest_handoff_closed_after_br232": int(latest_rows == 0),
        "evidence_manifest_closed_after_br236": int(evidence_rows == 0),
        "residual_rescan_complete": int(
            len(rows) in {2, 9}
            and latest_rows == 0
            and evidence_rows in {0, 7}
            and episode_rows == 1
            and validation_rows == 1
            and manifestized in {0, 7}
            and validation_intentional == 1
            and manual_allowed == 0
            and runtime_allowed == 0
            and operator_allowed == 0
        ),
        "literal_role_counts": dict(sorted(role_counts.items())),
        "post_br232_residual_lane_counts": dict(sorted(lane_counts.items())),
        "post_br232_status_counts": dict(sorted(status_counts.items())),
        "relative_path_counts": dict(sorted(file_counts.items())),
        "recommended_next_branch": (
            "evidence_manifest_repro_refresh_plan"
            if evidence_rows
            else "episode_truth_map_note_repro_refresh_when_touched"
        ),
    }


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scalar_keys = [
        "path_portability_total_matches",
        "post_br232_generated_handoff_repro_literal_rows",
        "latest_handoff_manifest_repro_rows",
        "evidence_manifest_repro_rows",
        "episode_note_repro_rows",
        "validation_output_literal_rows",
        "manifestized_rebuild_candidate_rows",
        "intentional_validation_output_literal_rows",
        "manual_literal_edit_allowed_rows",
        "runtime_semantic_change_allowed_rows",
        "operator_facing_change_allowed_rows",
        "br228_generated_literal_rows",
        "br228_latest_handoff_rows",
        "br228_evidence_manifest_rows",
        "br228_episode_note_rows",
        "br228_validation_output_rows",
        "br228_manifestized_rebuild_candidate_rows",
        "generated_literal_drop_since_br228",
        "latest_handoff_drop_since_br228",
        "manifestized_rebuild_drop_since_br228",
        "latest_handoff_closed_after_br232",
        "evidence_manifest_closed_after_br236",
        "residual_rescan_complete",
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
        "post_br232_status_counts",
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
            "# Generated Handoff Repro Literal Post-BR232 Rescan V1",
            "",
            "## Summary",
            "- Re-scans generated handoff/repro literals after BR-231 and BR-232 were merged.",
            "- Confirms the latest handoff lane is closed and separates the remaining residual lanes.",
            "- This is audit-only; it does not rewrite literals, run evidence builders, or change runtime semantics.",
            "",
            "## Counts",
            f"- post_br232_generated_handoff_repro_literal_rows: `{payload['post_br232_generated_handoff_repro_literal_rows']}`",
            f"- latest_handoff_manifest_repro_rows: `{payload['latest_handoff_manifest_repro_rows']}`",
            f"- evidence_manifest_repro_rows: `{payload['evidence_manifest_repro_rows']}`",
            f"- episode_note_repro_rows: `{payload['episode_note_repro_rows']}`",
            f"- validation_output_literal_rows: `{payload['validation_output_literal_rows']}`",
            f"- generated_literal_drop_since_br228: `{payload['generated_literal_drop_since_br228']}`",
            f"- latest_handoff_drop_since_br228: `{payload['latest_handoff_drop_since_br228']}`",
            f"- manifestized_rebuild_candidate_rows: `{payload['manifestized_rebuild_candidate_rows']}`",
            f"- manual_literal_edit_allowed_rows: `{payload['manual_literal_edit_allowed_rows']}`",
            f"- latest_handoff_closed_after_br232: `{payload['latest_handoff_closed_after_br232']}`",
            f"- evidence_manifest_closed_after_br236: `{payload['evidence_manifest_closed_after_br236']}`",
            f"- residual_rescan_complete: `{payload['residual_rescan_complete']}`",
            "",
            "## Boundary",
            "- The latest handoff generator/output lane is considered closed by this rescan.",
            "- The evidence manifest residuals are closed when `evidence_manifest_closed_after_br236=1`.",
            "- The episode note row is deferred until that note is touched.",
            "- The validation output row remains an intentional output destination, not input debt.",
            "",
            "## Next Action",
            f"- Recommended next branch: `{payload['recommended_next_branch']}`.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    rows, path_portability_total = build_rows(repo_root, args.max_file_bytes)
    payload = build_payload(rows, path_portability_total)

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / DETAIL_OUTPUT_NAME, rows, DETAIL_COLUMNS)
    write_csv(output_dir / SUMMARY_OUTPUT_NAME, summary_rows(payload), SUMMARY_COLUMNS)
    (output_dir / NOTE_OUTPUT_NAME).write_text(render_note(payload), encoding="utf-8")
    (output_dir / JSON_OUTPUT_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
