#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from build_repo_static_directory_reference_inventory_v1 import build_inventory, resolve


OWNER_BRANCH = "BR-20260429-212"
EXPECTED_EPISODE_TRUTH_DIRECTORY_ROWS = 12
TARGET_WORKFLOW_LANE = "panel_engine_episode_truth"

DETAIL_OUTPUT_NAME = "episode_truth_static_directory_contract_closure_v1.csv"
SUMMARY_OUTPUT_NAME = "episode_truth_static_directory_contract_closure_summary_v1.csv"
NOTE_OUTPUT_NAME = "episode_truth_static_directory_contract_closure_note_v1.md"
JSON_OUTPUT_NAME = "episode_truth_static_directory_contract_closure_v1.json"

DETAIL_COLUMNS = [
    "owner_branch",
    "contract_id",
    "source_file",
    "line_no",
    "directory_slug",
    "source_branch_hint",
    "expected_manifest_key",
    "explicit_cli_flag",
    "has_input_manifest_flag",
    "has_resolve_chain_input_flag",
    "explicit_cli_arg_present_flag",
    "legacy_default_retained_flag",
    "contract_status",
    "missing_checks",
    "runtime_semantic_change_allowed_flag",
    "bulk_rewrite_allowed_flag",
    "recommended_resolution",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]

EXPECTED_CONTRACTS = {
    (
        "research/prognostics/build_panel_day_engine_episode_truth_map_v1.py",
        22,
    ): ("shape_input", "--shape-input"),
    (
        "research/prognostics/build_panel_day_engine_episode_truth_map_v1.py",
        26,
    ): ("backlog_input", "--backlog-input"),
    (
        "research/prognostics/build_panel_day_engine_episode_truth_review_packet_v1.py",
        19,
    ): ("episode_map_input", "--episode-map-input"),
    (
        "research/prognostics/build_panel_day_engine_reviewed_episode_truth_rows_v1.py",
        19,
    ): ("packet_input", "--packet-input"),
    (
        "research/prognostics/build_panel_day_engine_reviewed_episode_truth_rows_v1.py",
        23,
    ): ("guard_json_input", "--guard-json-input"),
    (
        "research/prognostics/build_panel_day_engine_episode_truth_evidence_attachment_v1.py",
        23,
    ): ("reviewed_rows_input", "--reviewed-rows-input"),
    (
        "research/prognostics/build_panel_day_engine_episode_truth_source_trace_audit_v1.py",
        19,
    ): ("index_input", "--index-input"),
    (
        "research/prognostics/build_panel_day_engine_episode_truth_source_trace_audit_v1.py",
        23,
    ): ("template_input", "--template-input"),
    (
        "research/prognostics/build_panel_day_engine_episode_truth_adjudication_worksheet_v1.py",
        20,
    ): ("trace_input", "--trace-input"),
    (
        "research/prognostics/build_panel_day_engine_episode_truth_adjudication_worksheet_v1.py",
        24,
    ): ("index_input", "--index-input"),
    (
        "research/prognostics/build_panel_day_engine_episode_truth_conservative_adjudication_v1.py",
        20,
    ): ("worksheet_input", "--worksheet-input"),
    (
        "research/prognostics/build_panel_day_engine_episode_truth_durable_shape_review_v1.py",
        20,
    ): ("br088_input", "--br088-input"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that episode-truth static directory references already have "
            "manifest or explicit CLI input contracts before any path rewrite."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for closure outputs. Required so this audit adds no temp default.",
    )
    parser.add_argument("--max-file-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def read_source(repo_root: Path, source_file: str) -> str:
    path = repo_root / source_file
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def build_closure(repo_root: Path, max_file_bytes: int) -> list[dict[str, object]]:
    inventory = build_inventory(repo_root, max_file_bytes)
    episode_rows = [
        row for row in inventory if str(row.get("workflow_lane")) == TARGET_WORKFLOW_LANE
    ]

    out: list[dict[str, object]] = []
    for idx, row in enumerate(episode_rows, start=1):
        source_file = str(row["source_file"])
        line_no = int(row["line_no"])
        expected_manifest_key, explicit_cli_flag = EXPECTED_CONTRACTS.get(
            (source_file, line_no),
            ("", ""),
        )
        source_text = read_source(repo_root, source_file)
        checks: list[str] = []
        has_input_manifest = int("--input-manifest" in source_text)
        has_resolve_chain_input = int("resolve_chain_input(" in source_text)
        explicit_cli_arg_present = int(bool(explicit_cli_flag) and explicit_cli_flag in source_text)
        legacy_default_retained = int(str(row["matched_text"]) in source_text)

        if not expected_manifest_key:
            checks.append("missing_expected_manifest_key_mapping")
        elif expected_manifest_key not in source_text:
            checks.append("manifest_key_not_referenced")
        if not explicit_cli_arg_present:
            checks.append("missing_explicit_cli_arg")
        if not has_input_manifest:
            checks.append("missing_input_manifest_arg")
        if not has_resolve_chain_input:
            checks.append("missing_resolve_chain_input")
        if not legacy_default_retained:
            checks.append("legacy_default_not_detected")

        out.append(
            {
                "owner_branch": OWNER_BRANCH,
                "contract_id": f"BR212-{idx:03d}",
                "source_file": source_file,
                "line_no": line_no,
                "directory_slug": row.get("directory_slug", ""),
                "source_branch_hint": row.get("source_branch_hint", ""),
                "expected_manifest_key": expected_manifest_key,
                "explicit_cli_flag": explicit_cli_flag,
                "has_input_manifest_flag": has_input_manifest,
                "has_resolve_chain_input_flag": has_resolve_chain_input,
                "explicit_cli_arg_present_flag": explicit_cli_arg_present,
                "legacy_default_retained_flag": legacy_default_retained,
                "contract_status": "closed" if not checks else "needs_review",
                "missing_checks": ";".join(checks),
                "runtime_semantic_change_allowed_flag": 0,
                "bulk_rewrite_allowed_flag": 0,
                "recommended_resolution": (
                    "keep_legacy_default_but_use_input_manifest_or_explicit_cli_for_reproducible_runs"
                ),
            }
        )
    return out


def summary_payload(closure: list[dict[str, object]]) -> dict[str, object]:
    contract_fail_count = sum(str(row["contract_status"]) != "closed" for row in closure)
    missing_check_count = sum(
        len([part for part in str(row["missing_checks"]).split(";") if part])
        for row in closure
    )
    payload: dict[str, object] = {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_episode_truth_directory_rows": EXPECTED_EPISODE_TRUTH_DIRECTORY_ROWS,
        "episode_truth_directory_rows": len(closure),
        "source_file_count": len({str(row["source_file"]) for row in closure}),
        "contract_closed_rows": len(closure) - contract_fail_count,
        "contract_fail_rows": contract_fail_count,
        "input_manifest_arg_rows": sum(int(row["has_input_manifest_flag"]) for row in closure),
        "resolve_chain_input_rows": sum(int(row["has_resolve_chain_input_flag"]) for row in closure),
        "explicit_cli_arg_rows": sum(int(row["explicit_cli_arg_present_flag"]) for row in closure),
        "legacy_default_retained_rows": sum(int(row["legacy_default_retained_flag"]) for row in closure),
        "runtime_semantic_change_allowed_rows": sum(
            int(row["runtime_semantic_change_allowed_flag"]) for row in closure
        ),
        "bulk_rewrite_allowed_rows": sum(int(row["bulk_rewrite_allowed_flag"]) for row in closure),
        "missing_check_count": missing_check_count,
        "contract_complete": int(
            len(closure) == EXPECTED_EPISODE_TRUTH_DIRECTORY_ROWS
            and contract_fail_count == 0
            and missing_check_count == 0
        ),
        "contract_status_counts": dict(Counter(str(row["contract_status"]) for row in closure)),
        "recommended_next_branch": (
            "episode_truth_directory_contract_closed_choose_next_static_directory_lane"
        ),
    }
    return payload


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    keys = [
        "expected_episode_truth_directory_rows",
        "episode_truth_directory_rows",
        "source_file_count",
        "contract_closed_rows",
        "contract_fail_rows",
        "input_manifest_arg_rows",
        "resolve_chain_input_rows",
        "explicit_cli_arg_rows",
        "legacy_default_retained_rows",
        "runtime_semantic_change_allowed_rows",
        "bulk_rewrite_allowed_rows",
        "missing_check_count",
        "contract_complete",
    ]
    return [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": key,
            "count": payload[key],
        }
        for key in keys
    ]


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def write_note(output_dir: Path, payload: dict[str, object]) -> Path:
    lines = [
        "# Episode Truth Static Directory Contract Closure",
        "",
        "## Boundary",
        "- This branch verifies input contracts only.",
        "- It does not rewrite legacy temp-directory defaults.",
        "- It does not change `pv_ae/panel_day_engine.py`, runtime semantics, truth, threshold, or operator-facing behavior.",
        "- Reproducible runs should use `--input-manifest` or explicit per-input CLI arguments.",
        "",
        "## Key Counts",
        f"- expected episode-truth directory rows: {payload['expected_episode_truth_directory_rows']}",
        f"- actual episode-truth directory rows: {payload['episode_truth_directory_rows']}",
        f"- source files: {payload['source_file_count']}",
        f"- contract closed rows: {payload['contract_closed_rows']}",
        f"- contract fail rows: {payload['contract_fail_rows']}",
        f"- input-manifest arg rows: {payload['input_manifest_arg_rows']}",
        f"- resolve-chain-input rows: {payload['resolve_chain_input_rows']}",
        f"- explicit CLI arg rows: {payload['explicit_cli_arg_rows']}",
        f"- missing check count: {payload['missing_check_count']}",
        f"- contract complete: {payload['contract_complete']}",
        "",
        "## Decision",
        "- Episode-truth static directory references can stay as legacy defaults for local continuity.",
        "- They are no longer the best next path-rewrite target because the manifest/explicit-input contract is already present.",
        "- Continue with another static directory lane, likely common-cause or panel-day evidence, before considering any bulk rewrite.",
    ]
    path = output_dir / NOTE_OUTPUT_NAME
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = resolve(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    closure = build_closure(repo_root, args.max_file_bytes)
    payload = summary_payload(closure)

    detail_path = output_dir / DETAIL_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME
    write_csv(detail_path, closure, DETAIL_COLUMNS)
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
