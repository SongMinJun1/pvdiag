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
    from build_repo_path_portability_audit_v1 import (
        DEFAULT_SCAN_ROOTS,
        iter_scan_files,
        scan_file,
    )
except ImportError:
    from research.prognostics.build_generated_residual_closure_audit_v1 import (
        build_detail_rows as build_generated_detail_rows,
        build_payload as build_generated_payload,
    )
    from research.prognostics.build_repo_path_portability_audit_v1 import (
        DEFAULT_SCAN_ROOTS,
        iter_scan_files,
        scan_file,
    )


OWNER_BRANCH = "BR-20260430-238"

DETAIL_OUTPUT_NAME = "path_portability_final_rescan_v1.csv"
SUMMARY_OUTPUT_NAME = "path_portability_final_rescan_summary_v1.csv"
NOTE_OUTPUT_NAME = "path_portability_final_rescan_note_v1.md"
JSON_OUTPUT_NAME = "path_portability_final_rescan_v1.json"

DETAIL_COLUMNS = [
    "owner_branch",
    "rescan_id",
    "lane",
    "source",
    "observed_rows",
    "blocking_open_rows",
    "gate_class",
    "gate_status",
    "reopen_trigger",
    "runtime_semantic_change_allowed_rows",
    "operator_facing_change_allowed_rows",
    "bulk_rewrite_allowed_rows",
    "recommended_next_action",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the final path-portability rescan after the generated handoff/evidence "
            "manifest residual lanes are closed. This is audit-only and separates "
            "current blocking debt from historical/provenance path text."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for final-rescan outputs. Required to avoid hidden temp defaults.",
    )
    parser.add_argument("--max-file-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def collect_path_rows(repo_root: Path, max_file_bytes: int) -> list[dict[str, object]]:
    files, _skipped = iter_scan_files(repo_root, list(DEFAULT_SCAN_ROOTS), max_file_bytes)
    rows: list[dict[str, object]] = []
    for path in files:
        rows.extend(scan_file(path, repo_root))
    return rows


def gate_row(
    index: int,
    lane: str,
    source: str,
    observed_rows: int,
    blocking_open_rows: int,
    gate_class: str,
    gate_status: str,
    reopen_trigger: str,
    recommended_next_action: str,
    runtime_semantic_change_allowed_rows: int = 0,
    operator_facing_change_allowed_rows: int = 0,
    bulk_rewrite_allowed_rows: int = 0,
) -> dict[str, object]:
    return {
        "owner_branch": OWNER_BRANCH,
        "rescan_id": f"BR238-{index:03d}",
        "lane": lane,
        "source": source,
        "observed_rows": observed_rows,
        "blocking_open_rows": blocking_open_rows,
        "gate_class": gate_class,
        "gate_status": gate_status,
        "reopen_trigger": reopen_trigger,
        "runtime_semantic_change_allowed_rows": runtime_semantic_change_allowed_rows,
        "operator_facing_change_allowed_rows": operator_facing_change_allowed_rows,
        "bulk_rewrite_allowed_rows": bulk_rewrite_allowed_rows,
        "recommended_next_action": recommended_next_action,
    }


def build_detail_rows(
    path_rows: list[dict[str, object]],
    generated_payload: dict[str, object],
) -> list[dict[str, object]]:
    priority_counts = Counter(str(row.get("triage_priority", "")) for row in path_rows)
    rows: list[dict[str, object]] = []
    idx = 1

    blocking_specs = [
        (
            "p0_stale_worktree",
            "repo_path_portability_audit",
            priority_counts.get("p0_stale_worktree", 0),
            "current_path_blocker",
            "closed" if priority_counts.get("p0_stale_worktree", 0) == 0 else "reopen_required",
            "any stale worktree absolute path appears in repo-facing surfaces",
            "remove or regenerate stale worktree references before claiming portability closure",
        ),
        (
            "latest_handoff_generated_repro_residual",
            "generated_residual_closure_audit",
            int(generated_payload["latest_handoff_residual_rows"]),
            "current_generated_handoff_blocker",
            "closed" if int(generated_payload["latest_handoff_residual_rows"]) == 0 else "reopen_required",
            "latest handoff manifest regains generated temp-path repro residuals",
            "refresh latest handoff generator output through manifestized repro commands",
        ),
        (
            "evidence_manifest_generated_repro_residual",
            "generated_residual_closure_audit",
            int(generated_payload["evidence_manifest_residual_rows"]),
            "current_generated_handoff_blocker",
            "closed" if int(generated_payload["evidence_manifest_residual_rows"]) == 0 else "reopen_required",
            "evidence manifest regains generated temp-path repro residuals",
            "refresh evidence manifest builder constants instead of editing generated CSV rows",
        ),
        (
            "generated_residual_action_required",
            "generated_residual_closure_audit",
            int(generated_payload["current_action_required_rows"]),
            "current_generated_handoff_blocker",
            "closed" if int(generated_payload["current_action_required_rows"]) == 0 else "reopen_required",
            "generated residual closure marks any row as action-required",
            "inspect generated residual owner before closing the portability cleanup axis",
        ),
        (
            "unexpected_generated_residual",
            "generated_residual_closure_audit",
            int(generated_payload["unexpected_generated_residual_rows"]),
            "current_generated_handoff_blocker",
            "closed" if int(generated_payload["unexpected_generated_residual_rows"]) == 0 else "reopen_required",
            "a generated residual falls outside the deferred/preserved buckets",
            "classify the new residual before continuing cleanup",
        ),
    ]
    for lane, source, observed, gate_class, status, reopen_trigger, action in blocking_specs:
        rows.append(
            gate_row(
                idx,
                lane,
                source,
                observed,
                observed,
                gate_class,
                status,
                reopen_trigger,
                action,
            )
        )
        idx += 1

    nonblocking_specs = [
        (
            "episode_note_repro_deferred",
            "generated_residual_closure_audit",
            int(generated_payload["episode_note_deferred_rows"]),
            "deferred_owner-note_repro",
            "deferred_until_owner_touched",
            "episode truth map note is edited",
            "refresh the generated note repro text only when the owner note is touched",
        ),
        (
            "validation_output_destination_preserved",
            "generated_residual_closure_audit",
            int(generated_payload["validation_output_preserved_rows"]),
            "intentional_output_destination_literal",
            "preserved",
            "validation output destination policy changes",
            "preserve this explicit validation output destination",
        ),
        (
            "p1_live_temp_reference_broad_scan",
            "repo_path_portability_audit",
            priority_counts.get("p1_live_temp_reference", 0),
            "previously_scoped_contract_or_literal_lane",
            "nonblocking_current_context",
            "dedicated p1 closure audit is reopened",
            "do not bulk rewrite; use owner-specific manifest/explicit-input contracts",
        ),
        (
            "p1_temp_input_default_broad_scan",
            "repo_path_portability_audit",
            priority_counts.get("p1_temp_input_default_reference", 0),
            "previously_scoped_input_default_lane",
            "nonblocking_current_context",
            "dedicated p1 input-default closure audit is reopened",
            "keep fail-closed guards and manifest/explicit input support",
        ),
        (
            "p2_historical_evidence_reference",
            "repo_path_portability_audit",
            priority_counts.get("p2_historical_evidence_reference", 0),
            "historical_or_provenance_reference",
            "bounded_not_bulk_rewritten",
            "historical evidence is promoted into a current handoff",
            "materialize a stable artifact only when the evidence becomes current",
        ),
        (
            "p2_historical_repro_reference",
            "repo_path_portability_audit",
            priority_counts.get("p2_historical_repro_reference", 0),
            "historical_or_generated_repro_reference",
            "bounded_not_bulk_rewritten",
            "historical repro text is reopened for current handoff use",
            "refresh through owner generator or doc touch, not one-off literal edits",
        ),
        (
            "p2_temp_output_default_reference",
            "repo_path_portability_audit",
            priority_counts.get("p2_temp_output_default_reference", 0),
            "output_destination_default_context",
            "nonblocking_output_context",
            "output default starts being used as input dependency",
            "prefer required --output-dir for reusable builders when touched",
        ),
        (
            "p2_temp_cli_default_reference",
            "repo_path_portability_audit",
            priority_counts.get("p2_temp_cli_default_reference", 0),
            "cli_default_context",
            "nonblocking_cli_context",
            "CLI default is promoted to current dependency input",
            "inspect owner script before changing a fixture or compatibility default",
        ),
        (
            "p3_doc_reference",
            "repo_path_portability_audit",
            priority_counts.get("p3_doc_reference", 0),
            "documentation_reference",
            "nonblocking_doc_context",
            "doc is reopened for current reproducibility handoff",
            "prefer repo-relative docs when touching the document",
        ),
        (
            "p3_test_fixture_reference",
            "repo_path_portability_audit",
            priority_counts.get("p3_test_fixture_reference", 0),
            "test_fixture_reference",
            "nonblocking_fixture_context",
            "fixture literal masks a live default",
            "preserve unless it hides a production/input default",
        ),
        (
            "p3_intentional_detection_literal",
            "repo_path_portability_audit",
            priority_counts.get("p3_intentional_detection_literal", 0),
            "intentional_detector_literal",
            "nonblocking_detector_context",
            "detector literal is counted as real path debt",
            "preserve or mark scanner self-noise when appropriate",
        ),
    ]
    for lane, source, observed, gate_class, status, reopen_trigger, action in nonblocking_specs:
        rows.append(
            gate_row(
                idx,
                lane,
                source,
                observed,
                0,
                gate_class,
                status,
                reopen_trigger,
                action,
            )
        )
        idx += 1

    return rows


def build_payload(path_rows: list[dict[str, object]], detail_rows: list[dict[str, object]], generated_payload: dict[str, object]) -> dict[str, object]:
    priority_counts = Counter(str(row.get("triage_priority", "")) for row in path_rows)
    gate_status_counts = Counter(str(row["gate_status"]) for row in detail_rows)
    gate_class_counts = Counter(str(row["gate_class"]) for row in detail_rows)
    source_counts = Counter(str(row["source"]) for row in detail_rows)
    blocking_open_rows = sum(int(row["blocking_open_rows"]) for row in detail_rows)
    runtime_allowed = sum(int(row["runtime_semantic_change_allowed_rows"]) for row in detail_rows)
    operator_allowed = sum(int(row["operator_facing_change_allowed_rows"]) for row in detail_rows)
    bulk_allowed = sum(int(row["bulk_rewrite_allowed_rows"]) for row in detail_rows)
    zero_literal_cleanup_complete = int(len(path_rows) == 0)
    final_rescan_complete = int(
        blocking_open_rows == 0
        and int(generated_payload["generated_residual_closure_complete"]) == 1
        and runtime_allowed == 0
        and operator_allowed == 0
        and bulk_allowed == 0
    )
    return {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "path_portability_total_matches": len(path_rows),
        "path_portability_zero_literal_cleanup_complete": zero_literal_cleanup_complete,
        "p0_stale_worktree_rows": priority_counts.get("p0_stale_worktree", 0),
        "p1_live_temp_reference_rows": priority_counts.get("p1_live_temp_reference", 0),
        "p1_temp_input_default_rows": priority_counts.get("p1_temp_input_default_reference", 0),
        "p2_historical_evidence_rows": priority_counts.get("p2_historical_evidence_reference", 0),
        "p2_historical_repro_rows": priority_counts.get("p2_historical_repro_reference", 0),
        "p2_temp_output_default_rows": priority_counts.get("p2_temp_output_default_reference", 0),
        "p2_temp_cli_default_rows": priority_counts.get("p2_temp_cli_default_reference", 0),
        "p3_doc_reference_rows": priority_counts.get("p3_doc_reference", 0),
        "p3_test_fixture_rows": priority_counts.get("p3_test_fixture_reference", 0),
        "p3_intentional_detection_rows": priority_counts.get("p3_intentional_detection_literal", 0),
        "generated_residual_rows": int(generated_payload["generated_residual_rows"]),
        "latest_handoff_residual_rows": int(generated_payload["latest_handoff_residual_rows"]),
        "evidence_manifest_residual_rows": int(generated_payload["evidence_manifest_residual_rows"]),
        "episode_note_deferred_rows": int(generated_payload["episode_note_deferred_rows"]),
        "validation_output_preserved_rows": int(generated_payload["validation_output_preserved_rows"]),
        "current_action_required_rows": int(generated_payload["current_action_required_rows"]),
        "unexpected_generated_residual_rows": int(generated_payload["unexpected_generated_residual_rows"]),
        "generated_residual_closure_complete": int(generated_payload["generated_residual_closure_complete"]),
        "blocking_open_rows": blocking_open_rows,
        "runtime_semantic_change_allowed_rows": runtime_allowed,
        "operator_facing_change_allowed_rows": operator_allowed,
        "bulk_rewrite_allowed_rows": bulk_allowed,
        "final_rescan_complete": final_rescan_complete,
        "detail_rows": len(detail_rows),
        "triage_priority_counts": dict(sorted(priority_counts.items())),
        "gate_status_counts": dict(sorted(gate_status_counts.items())),
        "gate_class_counts": dict(sorted(gate_class_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "closure_claim": (
            "current_blocking_gate_clear_not_zero_literal_cleanup"
            if final_rescan_complete
            else "blocking_path_portability_debt_reopened"
        ),
        "recommended_next_branch": (
            "path_portability_cleanup_axis_checkpoint"
            if final_rescan_complete
            else "inspect_path_portability_final_rescan_gaps"
        ),
    }


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scalar_keys = [
        "path_portability_total_matches",
        "path_portability_zero_literal_cleanup_complete",
        "p0_stale_worktree_rows",
        "p1_live_temp_reference_rows",
        "p1_temp_input_default_rows",
        "p2_historical_evidence_rows",
        "p2_historical_repro_rows",
        "p2_temp_output_default_rows",
        "p2_temp_cli_default_rows",
        "p3_doc_reference_rows",
        "p3_test_fixture_rows",
        "p3_intentional_detection_rows",
        "generated_residual_rows",
        "latest_handoff_residual_rows",
        "evidence_manifest_residual_rows",
        "episode_note_deferred_rows",
        "validation_output_preserved_rows",
        "current_action_required_rows",
        "unexpected_generated_residual_rows",
        "generated_residual_closure_complete",
        "blocking_open_rows",
        "runtime_semantic_change_allowed_rows",
        "operator_facing_change_allowed_rows",
        "bulk_rewrite_allowed_rows",
        "final_rescan_complete",
        "detail_rows",
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
        "gate_status_counts",
        "gate_class_counts",
        "source_counts",
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
            "# Path Portability Final Rescan V1",
            "",
            "## Summary",
            "- Runs a fresh repo-wide path-portability scan after BR-236/237.",
            "- Separates current blocking path debt from historical/provenance text and fixture/output context.",
            "- This is audit-only; it does not rewrite historical docs, runtime semantics, operator-facing outputs, or panel-engine code.",
            "",
            "## Final Gate",
            f"- final_rescan_complete: `{payload['final_rescan_complete']}`",
            f"- blocking_open_rows: `{payload['blocking_open_rows']}`",
            f"- generated_residual_closure_complete: `{payload['generated_residual_closure_complete']}`",
            f"- path_portability_zero_literal_cleanup_complete: `{payload['path_portability_zero_literal_cleanup_complete']}`",
            f"- closure_claim: `{payload['closure_claim']}`",
            "",
            "## Key Counts",
            f"- path_portability_total_matches: `{payload['path_portability_total_matches']}`",
            f"- p0_stale_worktree_rows: `{payload['p0_stale_worktree_rows']}`",
            f"- p1_live_temp_reference_rows: `{payload['p1_live_temp_reference_rows']}`",
            f"- p1_temp_input_default_rows: `{payload['p1_temp_input_default_rows']}`",
            f"- p2_historical_evidence_rows: `{payload['p2_historical_evidence_rows']}`",
            f"- p2_historical_repro_rows: `{payload['p2_historical_repro_rows']}`",
            f"- latest_handoff_residual_rows: `{payload['latest_handoff_residual_rows']}`",
            f"- evidence_manifest_residual_rows: `{payload['evidence_manifest_residual_rows']}`",
            f"- episode_note_deferred_rows: `{payload['episode_note_deferred_rows']}`",
            f"- validation_output_preserved_rows: `{payload['validation_output_preserved_rows']}`",
            "",
            "## Boundary",
            "- This does not claim that every historical path literal is gone.",
            "- It claims only that the currently blocking stale-worktree and generated handoff/evidence residual lanes are clear.",
            "- Broad p1/p2/p3 findings remain visible so future owner-file touches can refresh them deliberately.",
            "",
            "## Next Decision",
            f"- Next safe branch: `{payload['recommended_next_branch']}`.",
            "- Use this output as the closeout checkpoint before returning to algorithm or 실증-readiness work.",
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

    path_rows = collect_path_rows(repo_root, args.max_file_bytes)
    generated_rows, _path_portability_total = build_generated_detail_rows(
        repo_root,
        args.max_file_bytes,
    )
    generated_payload = build_generated_payload(generated_rows, len(path_rows))
    detail_rows = build_detail_rows(path_rows, generated_payload)
    payload = build_payload(path_rows, detail_rows, generated_payload)

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
