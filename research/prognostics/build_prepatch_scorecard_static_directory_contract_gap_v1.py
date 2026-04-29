#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from build_repo_static_directory_reference_inventory_v1 import build_inventory, resolve


OWNER_BRANCH = "BR-20260429-215"
EXPECTED_PREPATCH_DIRECTORY_ROWS = 4
TARGET_WORKFLOW_LANE = "panel_engine_prepatch_scorecard"

DETAIL_OUTPUT_NAME = "prepatch_scorecard_static_directory_contract_gap_v1.csv"
SUMMARY_OUTPUT_NAME = "prepatch_scorecard_static_directory_contract_gap_summary_v1.csv"
NOTE_OUTPUT_NAME = "prepatch_scorecard_static_directory_contract_gap_note_v1.md"
JSON_OUTPUT_NAME = "prepatch_scorecard_static_directory_contract_gap_v1.json"

DETAIL_COLUMNS = [
    "owner_branch",
    "contract_id",
    "source_file",
    "line_no",
    "directory_slug",
    "expected_manifest_keys",
    "explicit_cli_flags",
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
        "research/prognostics/build_panel_day_engine_result_delta_scorecard_v1.py",
        "panel_engine_algorithm_prepatch_runbook_check",
    ): (["prepatch_runbook_summary"], ["--prepatch-runbook-summary"]),
    (
        "research/prognostics/check_panel_day_engine_algorithm_prepatch_runbook_v1.py",
        "strong_common_cause_blocker_regression_packet_check",
    ): (["common_cause_strong_blocker_input"], ["--common-cause-strong-blocker-input"]),
    (
        "research/prognostics/check_panel_day_engine_algorithm_prepatch_runbook_v1.py",
        "common_cause_structural_blocker_review_check",
    ): (["common_cause_structural_input"], ["--common-cause-structural-input"]),
    (
        "research/prognostics/compare_panel_day_engine_result_delta_scorecards_v1.py",
        "panel_engine_result_delta_scorecard_check",
    ): (
        ["baseline_scorecard_summary", "post_scorecard_summary"],
        ["--baseline-scorecard-summary", "--post-scorecard-summary"],
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Identify which prepatch scorecard static directory references already have "
            "manifest/explicit CLI contracts and which still need follow-up."
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
    prepatch_rows = [
        row for row in inventory if str(row.get("workflow_lane")) == TARGET_WORKFLOW_LANE
    ]

    out: list[dict[str, object]] = []
    for idx, row in enumerate(prepatch_rows, start=1):
        source_file = str(row["source_file"])
        line_no = int(row["line_no"])
        directory_slug = str(row.get("directory_slug", ""))
        expected_manifest_keys, explicit_cli_flags = EXPECTED_CONTRACTS.get(
            (source_file, directory_slug),
            ([], []),
        )
        source_text = read_source(repo_root, source_file)
        checks: list[str] = []
        has_input_manifest = int("--input-manifest" in source_text)
        resolver_flag = has_manifest_resolver(source_text)
        explicit_cli_arg_present = int(
            bool(explicit_cli_flags) and all(flag in source_text for flag in explicit_cli_flags)
        )
        legacy_default_retained = int(str(row["matched_text"]) in source_text)

        if not expected_manifest_keys:
            checks.append("missing_expected_manifest_key_mapping")
        else:
            missing_keys = [key for key in expected_manifest_keys if key not in source_text]
            if missing_keys:
                checks.append("manifest_key_not_referenced:" + "|".join(missing_keys))
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
                "contract_id": f"BR215-{idx:03d}",
                "source_file": source_file,
                "line_no": line_no,
                "directory_slug": directory_slug,
                "expected_manifest_keys": "|".join(expected_manifest_keys),
                "explicit_cli_flags": "|".join(explicit_cli_flags),
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
        "expected_prepatch_directory_rows": EXPECTED_PREPATCH_DIRECTORY_ROWS,
        "prepatch_directory_rows": len(gap_rows),
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
            len(gap_rows) == EXPECTED_PREPATCH_DIRECTORY_ROWS
            and fail_count == 0
            and missing_check_count == 0
        ),
        "contract_status_counts": dict(Counter(str(row["contract_status"]) for row in gap_rows)),
        "recommended_next_branch": (
            "patch_prepatch_scorecard_static_directory_gap_scripts_with_input_manifest_resolver"
        ),
    }
    return payload


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    keys = [
        "expected_prepatch_directory_rows",
        "prepatch_directory_rows",
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
        "# Prepatch Scorecard Static Directory Contract Gap",
        "",
        "## Boundary",
        "- This branch identifies prepatch scorecard input-contract gaps only.",
        "- It does not rewrite legacy temp-directory defaults.",
        "- It does not change `pv_ae/panel_day_engine.py`, runtime semantics, truth, threshold, or operator-facing behavior.",
        "",
        "## Key Counts",
        f"- expected prepatch directory rows: {payload['expected_prepatch_directory_rows']}",
        f"- actual prepatch directory rows: {payload['prepatch_directory_rows']}",
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
        "- Prepatch scorecard static directory references are not fully contract-closed yet.",
        "- The next code patch should add input-manifest and manifest resolver handling before any path rewrite.",
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
