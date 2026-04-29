#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from build_repo_live_temp_reference_review_v1 import build_review, resolve


OWNER_BRANCH = "BR-20260429-224"

DETAIL_OUTPUT_NAME = "p1_live_temp_lane_closure_audit_v1.csv"
SUMMARY_OUTPUT_NAME = "p1_live_temp_lane_closure_audit_summary_v1.csv"
NOTE_OUTPUT_NAME = "p1_live_temp_lane_closure_audit_note_v1.md"
JSON_OUTPUT_NAME = "p1_live_temp_lane_closure_audit_v1.json"

EXPECTED_TOTAL_ROWS = 68
EXPECTED_REQUIRES_INPUT_ROWS = 62
EXPECTED_LITERAL_OR_REPRO_ROWS = 6
EXPECTED_KIND_COUNTS = {
    "static_upstream_directory_input": 48,
    "static_upstream_artifact_input": 10,
    "runtime_result_bundle_input": 4,
    "embedded_note_repro_command": 4,
    "intentional_temp_detection_literal": 2,
}
EXPECTED_DIRECTORY_WORKFLOW_COUNTS = {
    "panel_engine_episode_truth": 12,
    "panel_engine_common_cause": 8,
    "panel_engine_prepatch_scorecard": 4,
    "panel_engine_voltage_preserved": 4,
    "panel_day_engine_evidence": 20,
}

DETAIL_COLUMNS = [
    "owner_branch",
    "closure_id",
    "live_reference_kind",
    "workflow_lane",
    "expected_rows",
    "observed_rows",
    "closure_class",
    "closure_status",
    "requires_manifest_or_explicit_input_rows",
    "literal_or_repro_only_rows",
    "open_contract_gap_rows",
    "runtime_semantic_change_allowed_rows",
    "bulk_rewrite_allowed_rows",
    "supporting_branches",
    "recommended_resolution",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize whether the full p1 live-temp reference lane is closed by "
            "contract, not by bulk path rewriting."
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


def row_count(rows: list[dict[str, object]], **filters: str) -> int:
    count = 0
    for row in rows:
        if all(str(row.get(key)) == value for key, value in filters.items()):
            count += 1
    return count


def sum_flag(rows: list[dict[str, object]], flag: str, **filters: str) -> int:
    total = 0
    for row in rows:
        if all(str(row.get(key)) == value for key, value in filters.items()):
            total += int(row.get(flag, 0))
    return total


def closure_status(expected: int, observed: int, gap_rows: int) -> str:
    return "closed" if expected == observed and gap_rows == 0 else "needs_review"


def detail_row(
    closure_id: str,
    rows: list[dict[str, object]],
    live_reference_kind: str,
    workflow_lane: str,
    expected_rows: int,
    closure_class: str,
    supporting_branches: str,
    recommended_resolution: str,
) -> dict[str, object]:
    filters = {"live_reference_kind": live_reference_kind}
    if workflow_lane:
        filters["workflow_lane"] = workflow_lane
    observed_rows = row_count(rows, **filters)
    requires_input = sum_flag(rows, "requires_manifest_or_explicit_input_flag", **filters)
    literal_or_repro = sum_flag(rows, "literal_or_repro_only_flag", **filters)
    semantic_rows = sum_flag(rows, "runtime_semantic_change_allowed_flag", **filters)
    rewrite_rows = sum_flag(rows, "bulk_rewrite_allowed_flag", **filters)
    if live_reference_kind in {
        "static_upstream_directory_input",
        "static_upstream_artifact_input",
        "runtime_result_bundle_input",
    }:
        gap_rows = max(0, observed_rows - expected_rows) + max(0, expected_rows - observed_rows)
    else:
        gap_rows = 0 if observed_rows == expected_rows and requires_input == 0 else observed_rows
    status = closure_status(expected_rows, observed_rows, gap_rows)
    return {
        "owner_branch": OWNER_BRANCH,
        "closure_id": closure_id,
        "live_reference_kind": live_reference_kind,
        "workflow_lane": workflow_lane or "all",
        "expected_rows": expected_rows,
        "observed_rows": observed_rows,
        "closure_class": closure_class,
        "closure_status": status,
        "requires_manifest_or_explicit_input_rows": requires_input,
        "literal_or_repro_only_rows": literal_or_repro,
        "open_contract_gap_rows": gap_rows,
        "runtime_semantic_change_allowed_rows": semantic_rows,
        "bulk_rewrite_allowed_rows": rewrite_rows,
        "supporting_branches": supporting_branches,
        "recommended_resolution": recommended_resolution,
    }


def build_detail(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    detail: list[dict[str, object]] = []
    idx = 1
    for workflow_lane, expected_rows in EXPECTED_DIRECTORY_WORKFLOW_COUNTS.items():
        detail.append(
            detail_row(
                f"BR224-{idx:03d}",
                rows,
                "static_upstream_directory_input",
                workflow_lane,
                expected_rows,
                "closed_static_directory_contract",
                "BR-212|BR-214|BR-216|BR-217|BR-218",
                "keep_manifest_or_explicit_directory_contracts",
            )
        )
        idx += 1
    for kind, expected_rows, closure_class, branches, resolution in [
        (
            "static_upstream_artifact_input",
            10,
            "closed_static_artifact_contract",
            "BR-219|BR-220",
            "keep_manifest_or_explicit_artifact_contracts",
        ),
        (
            "runtime_result_bundle_input",
            4,
            "closed_runtime_result_bundle_contract",
            "BR-222",
            "keep_manifest_or_explicit_result_bundle_contracts",
        ),
        (
            "embedded_note_repro_command",
            4,
            "closed_embedded_repro_command",
            "BR-223",
            "refresh_only_when_touching_owner_note",
        ),
        (
            "intentional_temp_detection_literal",
            2,
            "closed_intentional_detector_literal",
            "BR-221|BR-223",
            "preserve_unless_it_creates_audit_self_noise",
        ),
    ]:
        detail.append(
            detail_row(
                f"BR224-{idx:03d}",
                rows,
                kind,
                "",
                expected_rows,
                closure_class,
                branches,
                resolution,
            )
        )
        idx += 1
    return detail


def summary_payload(review_rows: list[dict[str, object]], detail_rows: list[dict[str, object]]) -> dict[str, object]:
    kind_counts = Counter(str(row["live_reference_kind"]) for row in review_rows)
    workflow_counts = Counter(str(row["workflow_lane"]) for row in review_rows)
    open_contract_gap_rows = sum(int(row["open_contract_gap_rows"]) for row in detail_rows)
    closure_status_counts = Counter(str(row["closure_status"]) for row in detail_rows)
    expected_kind_match = int(all(kind_counts.get(key, 0) == value for key, value in EXPECTED_KIND_COUNTS.items()))
    expected_directory_workflow_match = int(
        all(
            row_count(
                review_rows,
                live_reference_kind="static_upstream_directory_input",
                workflow_lane=workflow_lane,
            )
            == expected_rows
            for workflow_lane, expected_rows in EXPECTED_DIRECTORY_WORKFLOW_COUNTS.items()
        )
    )
    total_rows = len(review_rows)
    requires_input = sum(int(row["requires_manifest_or_explicit_input_flag"]) for row in review_rows)
    literal_or_repro = sum(int(row["literal_or_repro_only_flag"]) for row in review_rows)
    runtime_semantic_rows = sum(int(row["runtime_semantic_change_allowed_flag"]) for row in review_rows)
    bulk_rewrite_rows = sum(int(row["bulk_rewrite_allowed_flag"]) for row in review_rows)
    closure_complete = int(
        total_rows == EXPECTED_TOTAL_ROWS
        and requires_input == EXPECTED_REQUIRES_INPUT_ROWS
        and literal_or_repro == EXPECTED_LITERAL_OR_REPRO_ROWS
        and expected_kind_match == 1
        and expected_directory_workflow_match == 1
        and open_contract_gap_rows == 0
        and runtime_semantic_rows == 0
        and bulk_rewrite_rows == 0
        and closure_status_counts.get("needs_review", 0) == 0
    )
    payload: dict[str, object] = {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_live_temp_reference_rows": EXPECTED_TOTAL_ROWS,
        "live_temp_reference_rows": total_rows,
        "requires_manifest_or_explicit_input_rows": requires_input,
        "literal_or_repro_only_rows": literal_or_repro,
        "open_contract_gap_rows": open_contract_gap_rows,
        "runtime_semantic_change_allowed_rows": runtime_semantic_rows,
        "bulk_rewrite_allowed_rows": bulk_rewrite_rows,
        "expected_kind_match": expected_kind_match,
        "expected_directory_workflow_match": expected_directory_workflow_match,
        "closure_complete": closure_complete,
        "detail_rows": len(detail_rows),
        "live_reference_kind_counts": dict(kind_counts),
        "workflow_lane_counts": dict(workflow_counts),
        "closure_status_counts": dict(closure_status_counts),
        "recommended_next_branch": (
            "p1_live_temp_reference_lane_closed_move_to_next_portability_axis"
            if closure_complete
            else "inspect_p1_live_temp_lane_regression"
        ),
    }
    return payload


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    keys = [
        "expected_live_temp_reference_rows",
        "live_temp_reference_rows",
        "requires_manifest_or_explicit_input_rows",
        "literal_or_repro_only_rows",
        "open_contract_gap_rows",
        "runtime_semantic_change_allowed_rows",
        "bulk_rewrite_allowed_rows",
        "expected_kind_match",
        "expected_directory_workflow_match",
        "closure_complete",
        "detail_rows",
    ]
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": key,
            "count": payload[key],
        }
        for key in keys
    ]
    for scope, payload_key in [
        ("live_reference_kind", "live_reference_kind_counts"),
        ("workflow_lane", "workflow_lane_counts"),
        ("closure_status", "closure_status_counts"),
    ]:
        counts = payload[payload_key]
        assert isinstance(counts, dict)
        for key, count in sorted(counts.items()):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": scope,
                    "key": key,
                    "count": count,
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def write_note(output_dir: Path, payload: dict[str, object]) -> Path:
    lines = [
        "# P1 Live Temp Lane Closure Audit",
        "",
        "## Boundary",
        "- This branch closes the p1 live-temp reference lane at the audit level.",
        "- It does not rewrite any legacy temp defaults.",
        "- It does not change `pv_ae/panel_day_engine.py`, runtime semantics, truth, threshold, or operator-facing behavior.",
        "",
        "## Summary",
        f"- live-temp rows: `{payload['live_temp_reference_rows']}`",
        f"- requires manifest or explicit input rows: `{payload['requires_manifest_or_explicit_input_rows']}`",
        f"- literal or repro only rows: `{payload['literal_or_repro_only_rows']}`",
        f"- open contract gap rows: `{payload['open_contract_gap_rows']}`",
        f"- expected kind match: `{payload['expected_kind_match']}`",
        f"- expected directory workflow match: `{payload['expected_directory_workflow_match']}`",
        f"- runtime semantic change allowed rows: `{payload['runtime_semantic_change_allowed_rows']}`",
        f"- bulk rewrite allowed rows: `{payload['bulk_rewrite_allowed_rows']}`",
        f"- closure complete: `{payload['closure_complete']}`",
        "",
        "## Decision",
        "- Treat the p1 live-temp lane as closed if this audit remains green.",
        "- Future work should move to the next portability/cleanup axis instead of reopening these paths without new evidence.",
        "- Any new live-temp input default must join an explicit contract bucket before being considered closed.",
    ]
    path = output_dir / NOTE_OUTPUT_NAME
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = resolve(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    review_rows = build_review(repo_root, args.max_file_bytes)
    detail_rows = build_detail(review_rows)
    payload = summary_payload(review_rows, detail_rows)

    detail_path = output_dir / DETAIL_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME
    note_path = write_note(output_dir, payload)

    write_csv(detail_path, detail_rows, DETAIL_COLUMNS)
    write_csv(summary_path, summary_rows(payload), SUMMARY_COLUMNS)
    payload["outputs"] = {
        "detail": str(detail_path),
        "summary": str(summary_path),
        "note": str(note_path),
        "json": str(json_path),
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
