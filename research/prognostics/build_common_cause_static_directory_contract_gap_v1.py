#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from build_repo_static_directory_reference_inventory_v1 import build_inventory, resolve


OWNER_BRANCH = "BR-20260429-213"
EXPECTED_COMMON_CAUSE_DIRECTORY_ROWS = 8
TARGET_WORKFLOW_LANE = "panel_engine_common_cause"

DETAIL_OUTPUT_NAME = "common_cause_static_directory_contract_gap_v1.csv"
SUMMARY_OUTPUT_NAME = "common_cause_static_directory_contract_gap_summary_v1.csv"
NOTE_OUTPUT_NAME = "common_cause_static_directory_contract_gap_note_v1.md"
JSON_OUTPUT_NAME = "common_cause_static_directory_contract_gap_v1.json"

DETAIL_COLUMNS = [
    "owner_branch",
    "contract_id",
    "source_file",
    "line_no",
    "directory_slug",
    "expected_manifest_key",
    "explicit_cli_flag",
    "has_input_manifest_flag",
    "has_manifest_resolver_flag",
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
        "research/prognostics/build_panel_day_engine_common_cause_exact_seed_search_v1.py",
        14,
    ): ("judgment_input", "--judgment-input"),
    (
        "research/prognostics/build_panel_day_engine_common_cause_exact_seed_search_v1.py",
        18,
    ): ("synchrony_input", "--synchrony-input"),
    (
        "research/prognostics/build_panel_day_engine_common_cause_manual_trace_review_v1.py",
        14,
    ): ("blocker_input", "--blocker-input"),
    (
        "research/prognostics/build_panel_day_engine_common_cause_structural_blocker_review_v1.py",
        11,
    ): ("exact_seed_input", "--exact-seed-input"),
    (
        "research/prognostics/build_panel_day_engine_strong_common_cause_blocker_regression_packet_v1.py",
        11,
    ): ("judgment_input", "--judgment-input"),
    (
        "research/prognostics/check_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py",
        11,
    ): ("strong_blocker_input", "--strong-blocker-input"),
    (
        "research/prognostics/check_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py",
        18,
    ): ("structural_input", "--structural-input"),
    (
        "research/prognostics/check_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py",
        22,
    ): ("trace_input", "--trace-input"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Identify which common-cause static directory references already have "
            "manifest/explicit CLI contracts and which still need code follow-up."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for gap outputs. Required so this audit adds no temp default.",
    )
    parser.add_argument("--max-file-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def read_source(repo_root: Path, source_file: str) -> str:
    path = repo_root / source_file
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def has_manifest_resolver(source_text: str) -> int:
    resolver_names = ["resolve_manifest_input(", "resolve_chain_input("]
    return int(any(name in source_text for name in resolver_names))


def build_gap(repo_root: Path, max_file_bytes: int) -> list[dict[str, object]]:
    inventory = build_inventory(repo_root, max_file_bytes)
    common_rows = [
        row for row in inventory if str(row.get("workflow_lane")) == TARGET_WORKFLOW_LANE
    ]

    out: list[dict[str, object]] = []
    for idx, row in enumerate(common_rows, start=1):
        source_file = str(row["source_file"])
        line_no = int(row["line_no"])
        expected_manifest_key, explicit_cli_flag = EXPECTED_CONTRACTS.get(
            (source_file, line_no),
            ("", ""),
        )
        source_text = read_source(repo_root, source_file)
        checks: list[str] = []
        has_input_manifest = int("--input-manifest" in source_text)
        resolver_flag = has_manifest_resolver(source_text)
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
        if not resolver_flag:
            checks.append("missing_manifest_resolver")
        if not legacy_default_retained:
            checks.append("legacy_default_not_detected")

        out.append(
            {
                "owner_branch": OWNER_BRANCH,
                "contract_id": f"BR213-{idx:03d}",
                "source_file": source_file,
                "line_no": line_no,
                "directory_slug": row.get("directory_slug", ""),
                "expected_manifest_key": expected_manifest_key,
                "explicit_cli_flag": explicit_cli_flag,
                "has_input_manifest_flag": has_input_manifest,
                "has_manifest_resolver_flag": resolver_flag,
                "explicit_cli_arg_present_flag": explicit_cli_arg_present,
                "legacy_default_retained_flag": legacy_default_retained,
                "contract_status": "closed" if not checks else "needs_patch",
                "missing_checks": ";".join(checks),
                "runtime_semantic_change_allowed_flag": 0,
                "bulk_rewrite_allowed_flag": 0,
                "recommended_resolution": (
                    "add_input_manifest_and_manifest_resolver_before_rewriting_legacy_default"
                    if checks
                    else "keep_legacy_default_but_use_manifest_or_explicit_cli_for_reproducible_runs"
                ),
            }
        )
    return out


def summary_payload(gap_rows: list[dict[str, object]]) -> dict[str, object]:
    fail_count = sum(str(row["contract_status"]) != "closed" for row in gap_rows)
    missing_check_count = sum(
        len([part for part in str(row["missing_checks"]).split(";") if part])
        for row in gap_rows
    )
    payload: dict[str, object] = {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_common_cause_directory_rows": EXPECTED_COMMON_CAUSE_DIRECTORY_ROWS,
        "common_cause_directory_rows": len(gap_rows),
        "source_file_count": len({str(row["source_file"]) for row in gap_rows}),
        "contract_closed_rows": len(gap_rows) - fail_count,
        "contract_gap_rows": fail_count,
        "input_manifest_arg_rows": sum(int(row["has_input_manifest_flag"]) for row in gap_rows),
        "manifest_resolver_rows": sum(int(row["has_manifest_resolver_flag"]) for row in gap_rows),
        "explicit_cli_arg_rows": sum(int(row["explicit_cli_arg_present_flag"]) for row in gap_rows),
        "legacy_default_retained_rows": sum(int(row["legacy_default_retained_flag"]) for row in gap_rows),
        "runtime_semantic_change_allowed_rows": sum(
            int(row["runtime_semantic_change_allowed_flag"]) for row in gap_rows
        ),
        "bulk_rewrite_allowed_rows": sum(int(row["bulk_rewrite_allowed_flag"]) for row in gap_rows),
        "missing_check_count": missing_check_count,
        "contract_complete": int(
            len(gap_rows) == EXPECTED_COMMON_CAUSE_DIRECTORY_ROWS
            and fail_count == 0
            and missing_check_count == 0
        ),
        "contract_status_counts": dict(Counter(str(row["contract_status"]) for row in gap_rows)),
        "recommended_next_branch": (
            "patch_common_cause_static_directory_gap_scripts_with_input_manifest_resolver"
        ),
    }
    return payload


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    keys = [
        "expected_common_cause_directory_rows",
        "common_cause_directory_rows",
        "source_file_count",
        "contract_closed_rows",
        "contract_gap_rows",
        "input_manifest_arg_rows",
        "manifest_resolver_rows",
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
        "# Common-Cause Static Directory Contract Gap",
        "",
        "## Boundary",
        "- This branch identifies common-cause input-contract gaps only.",
        "- It does not rewrite legacy temp-directory defaults.",
        "- It does not change `pv_ae/panel_day_engine.py`, runtime semantics, truth, threshold, or operator-facing behavior.",
        "",
        "## Key Counts",
        f"- expected common-cause directory rows: {payload['expected_common_cause_directory_rows']}",
        f"- actual common-cause directory rows: {payload['common_cause_directory_rows']}",
        f"- source files: {payload['source_file_count']}",
        f"- contract closed rows: {payload['contract_closed_rows']}",
        f"- contract gap rows: {payload['contract_gap_rows']}",
        f"- input-manifest arg rows: {payload['input_manifest_arg_rows']}",
        f"- manifest resolver rows: {payload['manifest_resolver_rows']}",
        f"- explicit CLI arg rows: {payload['explicit_cli_arg_rows']}",
        f"- missing check count: {payload['missing_check_count']}",
        f"- contract complete: {payload['contract_complete']}",
        "",
        "## Decision",
        "- Common-cause static directory references are not fully contract-closed yet.",
        "- The next code patch should add input-manifest and manifest resolver handling to the gap scripts before any path rewrite.",
        "- Keep direct runtime semantic and bulk rewrite permission at 0.",
    ]
    path = output_dir / NOTE_OUTPUT_NAME
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = resolve(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gap_rows = build_gap(repo_root, args.max_file_bytes)
    payload = summary_payload(gap_rows)

    detail_path = output_dir / DETAIL_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME
    write_csv(detail_path, gap_rows, DETAIL_COLUMNS)
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
