#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from build_mlpe_field_trial_output_default_review_v1 import build_review, resolve


OWNER_BRANCH = "BR-20260429-210"
EXPECTED_OUTPUT_DEFAULT_ROWS = 37
EXPECTED_RECOMMENDED_RESOLUTION = (
    "keep_dev_temp_default_but_require_explicit_output_dir_for_reproducible_runs"
)

DETAIL_OUTPUT_NAME = "mlpe_field_trial_output_default_closure_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_output_default_closure_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_output_default_closure_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_output_default_closure_v1.json"

DETAIL_COLUMNS = [
    "owner_branch",
    "output_default_id",
    "source_file",
    "default_variable",
    "default_output_dir",
    "consumer_script",
    "cli_output_dir_override_flag",
    "writes_only_default_flag",
    "input_dependency_flag",
    "generated_dependency_flag",
    "runtime_semantic_change_allowed_flag",
    "mass_rewrite_recommended_flag",
    "recommended_resolution",
    "closure_status",
    "missing_checks",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Close the MLPE field-trial output-default lane by verifying that "
            "current output defaults are write destinations with explicit "
            "reviewer/repro output-dir overrides."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for closure outputs. Required so this closure adds no new temp default.",
    )
    parser.add_argument("--max-file-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def int_flag(row: dict[str, object], key: str) -> int:
    try:
        return int(row.get(key, 0))
    except (TypeError, ValueError):
        return 0


def missing_checks_for(row: dict[str, object]) -> list[str]:
    checks: list[str] = []
    if int_flag(row, "cli_output_dir_override_flag") != 1:
        checks.append("missing_cli_output_dir_override")
    if int_flag(row, "writes_only_default_flag") != 1:
        checks.append("not_writes_only_default")
    if int_flag(row, "input_dependency_flag") != 0:
        checks.append("input_dependency_present")
    if int_flag(row, "generated_dependency_flag") != 0:
        checks.append("generated_dependency_present")
    if int_flag(row, "runtime_semantic_change_allowed_flag") != 0:
        checks.append("runtime_semantic_change_allowed")
    if int_flag(row, "mass_rewrite_recommended_flag") != 0:
        checks.append("mass_rewrite_recommended")
    if str(row.get("recommended_resolution", "")) != EXPECTED_RECOMMENDED_RESOLUTION:
        checks.append("unexpected_recommended_resolution")
    return checks


def build_closure(repo_root: Path, max_file_bytes: int) -> list[dict[str, object]]:
    review = build_review(repo_root, max_file_bytes)
    closure: list[dict[str, object]] = []
    for row in review:
        missing = missing_checks_for(row)
        closure.append(
            {
                "owner_branch": OWNER_BRANCH,
                "output_default_id": row.get("output_default_id", ""),
                "source_file": row.get("source_file", ""),
                "default_variable": row.get("default_variable", ""),
                "default_output_dir": row.get("default_output_dir", ""),
                "consumer_script": row.get("consumer_script", ""),
                "cli_output_dir_override_flag": int_flag(row, "cli_output_dir_override_flag"),
                "writes_only_default_flag": int_flag(row, "writes_only_default_flag"),
                "input_dependency_flag": int_flag(row, "input_dependency_flag"),
                "generated_dependency_flag": int_flag(row, "generated_dependency_flag"),
                "runtime_semantic_change_allowed_flag": int_flag(
                    row, "runtime_semantic_change_allowed_flag"
                ),
                "mass_rewrite_recommended_flag": int_flag(row, "mass_rewrite_recommended_flag"),
                "recommended_resolution": row.get("recommended_resolution", ""),
                "closure_status": "closed" if not missing else "needs_review",
                "missing_checks": ";".join(missing),
            }
        )
    return closure


def summary_payload(closure: list[dict[str, object]]) -> dict[str, object]:
    output_default_rows = len(closure)
    distinct_source_file_count = len({str(row["source_file"]) for row in closure})
    closure_fail_count = sum(str(row["closure_status"]) != "closed" for row in closure)
    missing_check_count = sum(
        len([part for part in str(row["missing_checks"]).split(";") if part])
        for row in closure
    )
    payload: dict[str, object] = {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_output_default_rows": EXPECTED_OUTPUT_DEFAULT_ROWS,
        "output_default_rows": output_default_rows,
        "distinct_source_file_count": distinct_source_file_count,
        "closure_pass_count": output_default_rows - closure_fail_count,
        "closure_fail_count": closure_fail_count,
        "missing_cli_output_dir_override_rows": sum(
            1 - int(row["cli_output_dir_override_flag"]) for row in closure
        ),
        "input_dependency_rows": sum(int(row["input_dependency_flag"]) for row in closure),
        "generated_dependency_rows": sum(int(row["generated_dependency_flag"]) for row in closure),
        "runtime_semantic_change_allowed_rows": sum(
            int(row["runtime_semantic_change_allowed_flag"]) for row in closure
        ),
        "mass_rewrite_recommended_rows": sum(
            int(row["mass_rewrite_recommended_flag"]) for row in closure
        ),
        "missing_check_count": missing_check_count,
        "closure_complete": int(
            output_default_rows == EXPECTED_OUTPUT_DEFAULT_ROWS
            and distinct_source_file_count == EXPECTED_OUTPUT_DEFAULT_ROWS
            and closure_fail_count == 0
            and missing_check_count == 0
        ),
        "recommended_next_branch": (
            "mlpe_output_defaults_closed_continue_static_directory_or_repo_cleanup_lane"
        ),
        "closure_status_counts": dict(Counter(str(row["closure_status"]) for row in closure)),
    }
    return payload


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    keys = [
        "expected_output_default_rows",
        "output_default_rows",
        "distinct_source_file_count",
        "closure_pass_count",
        "closure_fail_count",
        "missing_cli_output_dir_override_rows",
        "input_dependency_rows",
        "generated_dependency_rows",
        "runtime_semantic_change_allowed_rows",
        "mass_rewrite_recommended_rows",
        "missing_check_count",
        "closure_complete",
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
        "# MLPE Field-Trial Output Default Closure",
        "",
        "## Boundary",
        "- This is a static closure audit for output-location defaults only.",
        "- Output defaults are write destinations, not evidence inputs.",
        "- No `pv_ae/panel_day_engine.py`, runtime truth, threshold, engine, or operator-facing behavior changes are allowed here.",
        "- BR-210 itself requires `--output-dir`, so it does not add another local temp output default.",
        "",
        "## Key Counts",
        f"- expected output default rows: {payload['expected_output_default_rows']}",
        f"- actual output default rows: {payload['output_default_rows']}",
        f"- distinct source files: {payload['distinct_source_file_count']}",
        f"- closure pass rows: {payload['closure_pass_count']}",
        f"- closure fail rows: {payload['closure_fail_count']}",
        f"- missing check count: {payload['missing_check_count']}",
        f"- closure complete: {payload['closure_complete']}",
        "",
        "## Count Drift Note",
        "- BR-168 originally reviewed 36 MLPE output defaults.",
        "- BR-209 added one closure builder with its own output default, so the current repository count is 37.",
        "- BR-210 locks that current count and avoids creating a 38th row by requiring explicit `--output-dir`.",
        "",
        "## Recommendation",
        "- Keep these defaults as local developer write destinations for now.",
        "- Reproducible, reviewer-facing, or packaged runs should continue passing explicit `--output-dir`.",
        "- Continue next with static directory references or broader repo organization cleanup; do not reopen input/generated dependency cleanup from these rows.",
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
