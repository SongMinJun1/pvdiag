#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from build_repo_live_temp_reference_review_v1 import build_review, resolve


OWNER_BRANCH = "BR-20260429-211"
EXPECTED_STATIC_DIRECTORY_ROWS = 48
TARGET_LIVE_REFERENCE_KIND = "static_upstream_directory_input"

DETAIL_OUTPUT_NAME = "repo_static_directory_reference_inventory_v1.csv"
SUMMARY_OUTPUT_NAME = "repo_static_directory_reference_inventory_summary_v1.csv"
NOTE_OUTPUT_NAME = "repo_static_directory_reference_inventory_note_v1.md"
JSON_OUTPUT_NAME = "repo_static_directory_reference_inventory_v1.json"

DETAIL_COLUMNS = [
    "owner_branch",
    "directory_reference_id",
    "source_file",
    "line_no",
    "workflow_lane",
    "default_variable",
    "matched_text",
    "directory_slug",
    "source_branch_hint",
    "directory_reference_kind",
    "requires_manifest_or_explicit_directory_flag",
    "immediate_patch_allowed_flag",
    "bulk_rewrite_allowed_flag",
    "runtime_semantic_change_allowed_flag",
    "recommended_resolution",
    "rationale",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inventory unresolved static /private/tmp directory references after "
            "MLPE input/output-default lanes are closed."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for inventory outputs. Required so this inventory adds no temp default.",
    )
    parser.add_argument("--max-file-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def normalize_text(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.lower() == "nan" else text


def directory_slug(path_text: str) -> str:
    return Path(path_text.rstrip("/")).name


def source_branch_hint(path_text: str) -> str:
    match = re.search(r"_br(\d{3})_", path_text)
    if match:
        return f"BR-{match.group(1)}"
    match = re.search(r"br(\d{3})", path_text)
    if match:
        return f"BR-{match.group(1)}"
    return ""


def directory_reference_kind(workflow_lane: str) -> str:
    if workflow_lane == "panel_engine_episode_truth":
        return "episode_truth_chain_directory"
    if workflow_lane == "panel_engine_common_cause":
        return "common_cause_chain_directory"
    if workflow_lane == "panel_engine_prepatch_scorecard":
        return "prepatch_scorecard_chain_directory"
    if workflow_lane == "panel_engine_voltage_preserved":
        return "voltage_preserved_chain_directory"
    if workflow_lane == "panel_day_engine_evidence":
        return "panel_day_engine_evidence_chain_directory"
    return "other_static_directory_reference"


def build_inventory(repo_root: Path, max_file_bytes: int) -> list[dict[str, object]]:
    review = build_review(repo_root, max_file_bytes)
    static_rows = [
        row
        for row in review
        if normalize_text(row.get("live_reference_kind")) == TARGET_LIVE_REFERENCE_KIND
    ]

    out: list[dict[str, object]] = []
    for idx, row in enumerate(static_rows, start=1):
        matched_text = normalize_text(row.get("matched_text"))
        workflow_lane = normalize_text(row.get("workflow_lane"))
        ref_kind = directory_reference_kind(workflow_lane)
        out.append(
            {
                "owner_branch": OWNER_BRANCH,
                "directory_reference_id": f"BR211-{idx:03d}",
                "source_file": normalize_text(row.get("source_file")),
                "line_no": int(row.get("line_no", 0)),
                "workflow_lane": workflow_lane,
                "default_variable": normalize_text(row.get("default_variable")),
                "matched_text": matched_text,
                "directory_slug": directory_slug(matched_text),
                "source_branch_hint": source_branch_hint(matched_text),
                "directory_reference_kind": ref_kind,
                "requires_manifest_or_explicit_directory_flag": 1,
                "immediate_patch_allowed_flag": 0,
                "bulk_rewrite_allowed_flag": 0,
                "runtime_semantic_change_allowed_flag": 0,
                "recommended_resolution": "resolve_from_manifest_or_explicit_directory_input",
                "rationale": (
                    "The literal points to an upstream directory bundle. It should be "
                    "replaced only by a lane-specific manifest or explicit directory "
                    "input contract, not by a bulk path rewrite."
                ),
            }
        )
    return out


def summary_payload(inventory: list[dict[str, object]]) -> dict[str, object]:
    static_directory_rows = len(inventory)
    source_file_count = len({str(row["source_file"]) for row in inventory})
    payload: dict[str, object] = {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_static_directory_rows": EXPECTED_STATIC_DIRECTORY_ROWS,
        "static_directory_rows": static_directory_rows,
        "source_file_count": source_file_count,
        "requires_manifest_or_explicit_directory_rows": sum(
            int(row["requires_manifest_or_explicit_directory_flag"]) for row in inventory
        ),
        "immediate_patch_allowed_rows": sum(
            int(row["immediate_patch_allowed_flag"]) for row in inventory
        ),
        "bulk_rewrite_allowed_rows": sum(int(row["bulk_rewrite_allowed_flag"]) for row in inventory),
        "runtime_semantic_change_allowed_rows": sum(
            int(row["runtime_semantic_change_allowed_flag"]) for row in inventory
        ),
        "inventory_complete": int(static_directory_rows == EXPECTED_STATIC_DIRECTORY_ROWS),
        "workflow_lane_counts": dict(Counter(str(row["workflow_lane"]) for row in inventory)),
        "directory_reference_kind_counts": dict(
            Counter(str(row["directory_reference_kind"]) for row in inventory)
        ),
        "recommended_next_branch": (
            "choose_one_static_directory_lane_for_manifest_or_explicit_directory_contract"
        ),
    }
    return payload


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": key,
            "count": payload[key],
        }
        for key in [
            "expected_static_directory_rows",
            "static_directory_rows",
            "source_file_count",
            "requires_manifest_or_explicit_directory_rows",
            "immediate_patch_allowed_rows",
            "bulk_rewrite_allowed_rows",
            "runtime_semantic_change_allowed_rows",
            "inventory_complete",
        ]
    ]
    for scope, counts_key in [
        ("workflow_lane", "workflow_lane_counts"),
        ("directory_reference_kind", "directory_reference_kind_counts"),
    ]:
        counts = payload[counts_key]
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
        "# Repo Static Directory Reference Inventory",
        "",
        "## Boundary",
        "- This is an inventory-only branch for unresolved static directory references.",
        "- Do not bulk-rewrite `/private/tmp` directory literals from this artifact.",
        "- Do not change `pv_ae/panel_day_engine.py`, runtime semantics, truth, threshold, or operator-facing behavior.",
        "- Future cleanup must choose one workflow lane and add a manifest or explicit directory input contract.",
        "",
        "## Key Counts",
        f"- expected static directory rows: {payload['expected_static_directory_rows']}",
        f"- actual static directory rows: {payload['static_directory_rows']}",
        f"- source files: {payload['source_file_count']}",
        f"- manifest or explicit directory rows: {payload['requires_manifest_or_explicit_directory_rows']}",
        f"- immediate patch allowed rows: {payload['immediate_patch_allowed_rows']}",
        f"- bulk rewrite allowed rows: {payload['bulk_rewrite_allowed_rows']}",
        f"- runtime semantic change allowed rows: {payload['runtime_semantic_change_allowed_rows']}",
        f"- inventory complete: {payload['inventory_complete']}",
        "",
        "## Workflow Lane Counts",
    ]
    workflow_counts = payload["workflow_lane_counts"]
    assert isinstance(workflow_counts, dict)
    for key, count in sorted(workflow_counts.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(
        [
            "",
            "## Decision",
            "- Static directory references are upstream bundle inputs, not output defaults.",
            "- The safe next branch should select one lane, starting with the largest `panel_day_engine_evidence` bucket or the more cohesive `panel_engine_episode_truth` chain.",
            "- Keep direct rewrite permission at 0 until the chosen lane has a manifest/explicit-directory contract and smoke coverage.",
        ]
    )
    path = output_dir / NOTE_OUTPUT_NAME
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = resolve(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory = build_inventory(repo_root, args.max_file_bytes)
    payload = summary_payload(inventory)

    detail_path = output_dir / DETAIL_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME
    write_csv(detail_path, inventory, DETAIL_COLUMNS)
    write_csv(summary_path, summary_rows(payload), SUMMARY_COLUMNS)
    note_path = write_note(output_dir, payload)

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
