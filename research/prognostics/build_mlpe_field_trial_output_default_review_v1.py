#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from build_repo_path_portability_audit_v1 import DEFAULT_SCAN_ROOTS, iter_scan_files, scan_file


OWNER_BRANCH = "BR-20260429-168"

DETAIL_OUTPUT_NAME = "mlpe_field_trial_output_default_review_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_output_default_review_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_output_default_review_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_output_default_review_v1.json"

TARGET_WORKFLOW_LANE = "mlpe_field_trial"
TARGET_MATCH_ROLE = "research_temp_output_default_reference"

DETAIL_COLUMNS = [
    "owner_branch",
    "output_default_id",
    "source_file",
    "line_no",
    "default_variable",
    "default_output_dir",
    "consumer_script",
    "consumer_stage_slug",
    "cli_output_dir_override_flag",
    "writes_only_default_flag",
    "input_dependency_flag",
    "generated_dependency_flag",
    "runtime_semantic_change_allowed_flag",
    "mass_rewrite_recommended_flag",
    "recommended_resolution",
    "rationale",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Review MLPE field-trial /private/tmp output defaults separately from "
            "input dependencies before changing any builder defaults."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for review outputs. Required so this review does not add a new temp default.",
    )
    parser.add_argument("--max-file-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def normalize_text(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.lower() == "nan" else text


def resolve(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def parse_default_variable(context_excerpt: str) -> str:
    match = re.search(r"\b(DEFAULT_[A-Z0-9_]+)\s*=", context_excerpt)
    return match.group(1) if match else ""


def consumer_stage_slug(source_file: str) -> str:
    name = Path(source_file).name.removesuffix(".py")
    for prefix in ("build_mlpe_field_trial_", "check_mlpe_field_trial_"):
        if name.startswith(prefix):
            return name.removeprefix(prefix).removesuffix("_v1")
    return name


def has_cli_output_dir_override(repo_root: Path, source_file: str) -> int:
    try:
        text = (repo_root / source_file).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = (repo_root / source_file).read_text(encoding="utf-8", errors="replace")
    return int("--output-dir" in text)


def build_review(repo_root: Path, max_file_bytes: int) -> list[dict[str, object]]:
    files, _ = iter_scan_files(repo_root, DEFAULT_SCAN_ROOTS, max_file_bytes)
    audit_rows: list[dict[str, object]] = []
    for path in files:
        audit_rows.extend(scan_file(path, repo_root))

    target_rows = [
        row
        for row in audit_rows
        if normalize_text(row.get("workflow_lane")) == TARGET_WORKFLOW_LANE
        and normalize_text(row.get("match_role")) == TARGET_MATCH_ROLE
    ]

    out: list[dict[str, object]] = []
    for idx, row in enumerate(target_rows, start=1):
        source_file = normalize_text(row.get("relative_path"))
        cli_override = has_cli_output_dir_override(repo_root, source_file)
        recommended_resolution = (
            "keep_dev_temp_default_but_require_explicit_output_dir_for_reproducible_runs"
            if cli_override
            else "add_explicit_output_dir_cli_before_reusable_or_packaged_runs"
        )
        rationale = (
            "The path is a write destination, not an input dependency; reproducible runs "
            "should supply --output-dir rather than relying on a volatile local default."
        )
        out.append(
            {
                "owner_branch": OWNER_BRANCH,
                "output_default_id": f"BR168-{idx:03d}",
                "source_file": source_file,
                "line_no": int(row.get("line_no", 0)),
                "default_variable": parse_default_variable(normalize_text(row.get("context_excerpt"))),
                "default_output_dir": normalize_text(row.get("matched_text")),
                "consumer_script": Path(source_file).name,
                "consumer_stage_slug": consumer_stage_slug(source_file),
                "cli_output_dir_override_flag": cli_override,
                "writes_only_default_flag": 1,
                "input_dependency_flag": 0,
                "generated_dependency_flag": 0,
                "runtime_semantic_change_allowed_flag": 0,
                "mass_rewrite_recommended_flag": 0,
                "recommended_resolution": recommended_resolution,
                "rationale": rationale,
            }
        )
    return out


def summary_rows(review: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = [
        {"owner_branch": OWNER_BRANCH, "summary_scope": "overall", "key": "output_default_rows", "count": len(review)},
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": "cli_output_dir_override_rows",
            "count": sum(int(row["cli_output_dir_override_flag"]) for row in review),
        },
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": "missing_cli_output_dir_override_rows",
            "count": sum(1 - int(row["cli_output_dir_override_flag"]) for row in review),
        },
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": "input_dependency_rows",
            "count": sum(int(row["input_dependency_flag"]) for row in review),
        },
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": "generated_dependency_rows",
            "count": sum(int(row["generated_dependency_flag"]) for row in review),
        },
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": "runtime_semantic_change_allowed_rows",
            "count": sum(int(row["runtime_semantic_change_allowed_flag"]) for row in review),
        },
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": "mass_rewrite_recommended_rows",
            "count": sum(int(row["mass_rewrite_recommended_flag"]) for row in review),
        },
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": "source_files",
            "count": len({str(row["source_file"]) for row in review}),
        },
    ]
    for scope, field in [
        ("recommended_resolution", "recommended_resolution"),
        ("source_file", "source_file"),
    ]:
        for key, count in sorted(Counter(str(row[field]) for row in review).items()):
            rows.append({"owner_branch": OWNER_BRANCH, "summary_scope": scope, "key": key, "count": count})
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def write_note(output_dir: Path, summary: list[dict[str, object]]) -> Path:
    lookup = {(row["summary_scope"], row["key"]): row["count"] for row in summary}
    lines = [
        "# MLPE Field-Trial Output Default Review",
        "",
        "## Boundary",
        "- This is an output-location review only.",
        "- Output defaults are write destinations, not evidence inputs.",
        "- Do not treat these rows as generated dependency or user-filled input blockers.",
        "- Do not change runtime diagnosis semantics or `pv_ae/panel_day_engine.py`.",
        "",
        "## Key Counts",
        f"- output default rows: {lookup.get(('overall', 'output_default_rows'), 0)}",
        f"- CLI `--output-dir` override rows: {lookup.get(('overall', 'cli_output_dir_override_rows'), 0)}",
        f"- missing CLI override rows: {lookup.get(('overall', 'missing_cli_output_dir_override_rows'), 0)}",
        f"- input dependency rows: {lookup.get(('overall', 'input_dependency_rows'), 0)}",
        f"- generated dependency rows: {lookup.get(('overall', 'generated_dependency_rows'), 0)}",
        f"- runtime semantic change allowed rows: {lookup.get(('overall', 'runtime_semantic_change_allowed_rows'), 0)}",
        f"- mass rewrite recommended rows: {lookup.get(('overall', 'mass_rewrite_recommended_rows'), 0)}",
        "",
        "## Recommendation",
        "- Keep existing MLPE temp output defaults as local developer convenience for now.",
        "- Reproducible, reviewer-facing, or packaged runs must pass an explicit `--output-dir`.",
        "- Do not bulk-rewrite the 36 paths until a shared output-root policy is chosen.",
    ]
    path = output_dir / NOTE_OUTPUT_NAME
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = resolve(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    review = build_review(repo_root, args.max_file_bytes)
    summary = summary_rows(review)

    detail_path = output_dir / DETAIL_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME
    write_csv(detail_path, review, DETAIL_COLUMNS)
    write_csv(summary_path, summary, SUMMARY_COLUMNS)
    note_path = write_note(output_dir, summary)

    payload = {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_default_rows": len(review),
        "recommended_resolution_counts": dict(Counter(str(row["recommended_resolution"]) for row in review)),
        "cli_output_dir_override_rows": sum(int(row["cli_output_dir_override_flag"]) for row in review),
        "missing_cli_output_dir_override_rows": sum(1 - int(row["cli_output_dir_override_flag"]) for row in review),
        "input_dependency_rows": sum(int(row["input_dependency_flag"]) for row in review),
        "generated_dependency_rows": sum(int(row["generated_dependency_flag"]) for row in review),
        "runtime_semantic_change_allowed_rows": sum(
            int(row["runtime_semantic_change_allowed_flag"]) for row in review
        ),
        "mass_rewrite_recommended_rows": sum(int(row["mass_rewrite_recommended_flag"]) for row in review),
        "outputs": {
            "detail": str(detail_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
