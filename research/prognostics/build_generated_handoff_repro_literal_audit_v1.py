#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    from build_p2_historical_reference_boundary_audit_v1 import (
        build_detail_rows as build_p2_detail_rows,
        collect_path_rows,
    )
except ImportError:
    from research.prognostics.build_p2_historical_reference_boundary_audit_v1 import (
        build_detail_rows as build_p2_detail_rows,
        collect_path_rows,
    )


OWNER_BRANCH = "BR-20260429-228"

DETAIL_OUTPUT_NAME = "generated_handoff_repro_literal_audit_v1.csv"
SUMMARY_OUTPUT_NAME = "generated_handoff_repro_literal_audit_summary_v1.csv"
NOTE_OUTPUT_NAME = "generated_handoff_repro_literal_audit_note_v1.md"
JSON_OUTPUT_NAME = "generated_handoff_repro_literal_audit_v1.json"

LATEST_HANDOFF = "research/prognostics/build_panel_day_engine_latest_evidence_handoff_manifest_v1.py"
EVIDENCE_MANIFEST = "research/prognostics/build_panel_day_engine_evidence_manifest_v1.py"
EPISODE_TRUTH_MAP = "research/prognostics/build_panel_day_engine_episode_truth_map_v1.py"
PATCH_SAFETY_GATE = "research/prognostics/check_panel_day_engine_patch_safety_gate_v1.py"

DETAIL_COLUMNS = [
    "owner_branch",
    "literal_id",
    "relative_path",
    "line_no",
    "workflow_lane",
    "matched_text",
    "literal_role",
    "current_handoff_relevance",
    "refresh_policy",
    "manifestized_rebuild_candidate",
    "stable_artifact_materialization_required",
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
            "Classify the p2 generated handoff/repro literals so current handoff refresh "
            "candidates are separated from validation output literals and historical notes."
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


def classify_literal(row: dict[str, object]) -> dict[str, object]:
    relative_path = str(row.get("relative_path", ""))
    matched_text = str(row.get("matched_text", ""))

    if relative_path == LATEST_HANDOFF:
        return {
            "literal_role": "latest_evidence_handoff_manifest_repro",
            "current_handoff_relevance": "current_handoff_refresh_candidate",
            "refresh_policy": "rebuild_latest_handoff_with_manifestized_repro_commands",
            "manifestized_rebuild_candidate": 1,
            "stable_artifact_materialization_required": 0,
            "intentional_validation_output_literal": 0,
            "manual_literal_edit_allowed": 0,
            "recommended_next_action": (
                "refresh this generated handoff as one manifest-aware unit; do not edit "
                "individual temp literals by hand"
            ),
        }

    if relative_path == EVIDENCE_MANIFEST:
        return {
            "literal_role": "evidence_pack_manifest_repro",
            "current_handoff_relevance": "supporting_manifest_refresh_candidate",
            "refresh_policy": "refresh_evidence_manifest_when_promoted_into_current_handoff",
            "manifestized_rebuild_candidate": 1,
            "stable_artifact_materialization_required": 0,
            "intentional_validation_output_literal": 0,
            "manual_literal_edit_allowed": 0,
            "recommended_next_action": (
                "keep until the evidence manifest is refreshed; replace fixed temp roots "
                "through generated manifest parameters, not manual string edits"
            ),
        }

    if relative_path == EPISODE_TRUTH_MAP:
        return {
            "literal_role": "generated_note_repo_root_repro",
            "current_handoff_relevance": "single_note_repro_refresh_candidate",
            "refresh_policy": "refresh_generated_note_repro_to_pwd_when_touching_episode_truth_map",
            "manifestized_rebuild_candidate": 0,
            "stable_artifact_materialization_required": 0,
            "intentional_validation_output_literal": 0,
            "manual_literal_edit_allowed": 0,
            "recommended_next_action": (
                "defer unless reopening the episode truth map note; prefer --repo-root "
                "\"$(pwd)\" in generated repro text"
            ),
        }

    if relative_path == PATCH_SAFETY_GATE:
        return {
            "literal_role": "validation_output_dir_literal",
            "current_handoff_relevance": "not_handoff_input",
            "refresh_policy": "preserve_as_validation_output_destination",
            "manifestized_rebuild_candidate": 0,
            "stable_artifact_materialization_required": 0,
            "intentional_validation_output_literal": 1,
            "manual_literal_edit_allowed": 0,
            "recommended_next_action": (
                "keep as explicit validation output destination; it is not a handoff input "
                "or historical evidence dependency"
            ),
        }

    return {
        "literal_role": "generated_repro_literal_manual_review",
        "current_handoff_relevance": "manual_review",
        "refresh_policy": "inspect_before_rewrite",
        "manifestized_rebuild_candidate": 0,
        "stable_artifact_materialization_required": 0,
        "intentional_validation_output_literal": 0,
        "manual_literal_edit_allowed": 0,
        "recommended_next_action": "inspect before changing this generated repro literal",
    }


def build_detail_rows(repo_root: Path, max_file_bytes: int) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    path_rows = collect_path_rows(repo_root, max_file_bytes)
    p2_rows = build_p2_detail_rows(path_rows)
    generated_rows = [
        row for row in p2_rows if str(row.get("boundary_class", "")) == "generated_handoff_repro_literal"
    ]
    detail_rows: list[dict[str, object]] = []
    for index, row in enumerate(generated_rows, start=1):
        classification = classify_literal(row)
        detail_rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "literal_id": f"BR228-{index:03d}",
                "relative_path": row.get("relative_path", ""),
                "line_no": row.get("line_no", ""),
                "workflow_lane": row.get("workflow_lane", ""),
                "matched_text": row.get("matched_text", ""),
                "literal_role": classification["literal_role"],
                "current_handoff_relevance": classification["current_handoff_relevance"],
                "refresh_policy": classification["refresh_policy"],
                "manifestized_rebuild_candidate": classification["manifestized_rebuild_candidate"],
                "stable_artifact_materialization_required": classification[
                    "stable_artifact_materialization_required"
                ],
                "intentional_validation_output_literal": classification[
                    "intentional_validation_output_literal"
                ],
                "manual_literal_edit_allowed": classification["manual_literal_edit_allowed"],
                "runtime_semantic_change_allowed_rows": 0,
                "operator_facing_change_allowed_rows": 0,
                "recommended_next_action": classification["recommended_next_action"],
            }
        )
    return path_rows, detail_rows


def build_payload(path_rows: list[dict[str, object]], detail_rows: list[dict[str, object]]) -> dict[str, object]:
    role_counts = Counter(str(row["literal_role"]) for row in detail_rows)
    relevance_counts = Counter(str(row["current_handoff_relevance"]) for row in detail_rows)
    file_counts = Counter(str(row["relative_path"]) for row in detail_rows)
    refresh_counts = Counter(str(row["refresh_policy"]) for row in detail_rows)

    manifestized = sum(int(row["manifestized_rebuild_candidate"]) for row in detail_rows)
    stable_required = sum(int(row["stable_artifact_materialization_required"]) for row in detail_rows)
    validation_literals = sum(int(row["intentional_validation_output_literal"]) for row in detail_rows)
    manual_allowed = sum(int(row["manual_literal_edit_allowed"]) for row in detail_rows)

    return {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "path_portability_total_matches": len(path_rows),
        "generated_handoff_repro_literal_rows": len(detail_rows),
        "latest_handoff_manifest_repro_rows": role_counts.get("latest_evidence_handoff_manifest_repro", 0),
        "evidence_manifest_repro_rows": role_counts.get("evidence_pack_manifest_repro", 0),
        "episode_note_repro_rows": role_counts.get("generated_note_repo_root_repro", 0),
        "validation_output_literal_rows": role_counts.get("validation_output_dir_literal", 0),
        "manifestized_rebuild_candidate_rows": manifestized,
        "stable_artifact_materialization_required_rows": stable_required,
        "intentional_validation_output_literal_rows": validation_literals,
        "manual_literal_edit_allowed_rows": manual_allowed,
        "runtime_semantic_change_allowed_rows": 0,
        "operator_facing_change_allowed_rows": 0,
        "audit_complete": int(
            len(detail_rows) > 0
            and sum(role_counts.values()) == len(detail_rows)
            and manual_allowed == 0
        ),
        "literal_role_counts": dict(sorted(role_counts.items())),
        "current_handoff_relevance_counts": dict(sorted(relevance_counts.items())),
        "relative_path_counts": dict(sorted(file_counts.items())),
        "refresh_policy_counts": dict(sorted(refresh_counts.items())),
        "recommended_next_branch": "latest_handoff_manifest_repro_refresh_plan",
    }


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scalar_keys = [
        "path_portability_total_matches",
        "generated_handoff_repro_literal_rows",
        "latest_handoff_manifest_repro_rows",
        "evidence_manifest_repro_rows",
        "episode_note_repro_rows",
        "validation_output_literal_rows",
        "manifestized_rebuild_candidate_rows",
        "stable_artifact_materialization_required_rows",
        "intentional_validation_output_literal_rows",
        "manual_literal_edit_allowed_rows",
        "runtime_semantic_change_allowed_rows",
        "operator_facing_change_allowed_rows",
        "audit_complete",
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
        "current_handoff_relevance_counts",
        "relative_path_counts",
        "refresh_policy_counts",
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
            "# Generated Handoff Repro Literal Audit V1",
            "",
            "## Summary",
            "- Re-audits the 50 generated handoff/repro literals from BR-227.",
            "- Separates current handoff refresh candidates from validation output literals and generated note repro text.",
            "- This is an audit-only patch; it does not rewrite the literals.",
            "",
            "## Counts",
            f"- path_portability_total_matches: `{payload['path_portability_total_matches']}`",
            f"- generated_handoff_repro_literal_rows: `{payload['generated_handoff_repro_literal_rows']}`",
            f"- latest_handoff_manifest_repro_rows: `{payload['latest_handoff_manifest_repro_rows']}`",
            f"- evidence_manifest_repro_rows: `{payload['evidence_manifest_repro_rows']}`",
            f"- episode_note_repro_rows: `{payload['episode_note_repro_rows']}`",
            f"- validation_output_literal_rows: `{payload['validation_output_literal_rows']}`",
            f"- manifestized_rebuild_candidate_rows: `{payload['manifestized_rebuild_candidate_rows']}`",
            f"- manual_literal_edit_allowed_rows: `{payload['manual_literal_edit_allowed_rows']}`",
            f"- runtime_semantic_change_allowed_rows: `{payload['runtime_semantic_change_allowed_rows']}`",
            f"- operator_facing_change_allowed_rows: `{payload['operator_facing_change_allowed_rows']}`",
            f"- audit_complete: `{payload['audit_complete']}`",
            "",
            "## Boundary",
            "- Do not edit individual generated temp literals by hand.",
            "- Refresh the latest handoff manifest as one manifest-aware unit.",
            "- Keep validation output temp paths as output destinations, not handoff inputs.",
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
    path_rows, detail_rows = build_detail_rows(repo_root, args.max_file_bytes)
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
