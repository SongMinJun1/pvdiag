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


OWNER_BRANCH = "BR-20260429-169"

DETAIL_OUTPUT_NAME = "repo_live_temp_reference_review_v1.csv"
SUMMARY_OUTPUT_NAME = "repo_live_temp_reference_review_summary_v1.csv"
NOTE_OUTPUT_NAME = "repo_live_temp_reference_review_note_v1.md"
JSON_OUTPUT_NAME = "repo_live_temp_reference_review_v1.json"

TARGET_TRIAGE_PRIORITY = "p1_live_temp_reference"

DETAIL_COLUMNS = [
    "owner_branch",
    "review_id",
    "source_file",
    "line_no",
    "workflow_lane",
    "matched_text",
    "context_excerpt",
    "default_variable",
    "reference_shape",
    "live_reference_kind",
    "requires_manifest_or_explicit_input_flag",
    "literal_or_repro_only_flag",
    "runtime_semantic_change_allowed_flag",
    "bulk_rewrite_allowed_flag",
    "recommended_resolution",
    "rationale",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Review unresolved live temp references after input/default cleanup, "
            "without rewriting historical or evidence paths in bulk."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for review outputs. Required so this reviewer does not add a temp default.",
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
    match = re.search(r"\b([A-Z0-9_]+_DEFAULT|DEFAULT_[A-Z0-9_]+)\s*=", context_excerpt)
    return match.group(1) if match else ""


def reference_shape(path_text: str) -> str:
    path = Path(path_text)
    if path_text.endswith("/") or not path.suffix:
        return "directory"
    return "file"


def classify_live_reference(path_text: str, context_excerpt: str) -> tuple[str, str, str]:
    context = context_excerpt.lower()
    if "--repo-root" in context or "--output-dir {output_dir}" in context or "python3 research/prognostics" in context:
        return (
            "embedded_note_repro_command",
            "refresh_embedded_repro_command_when_touching_builder_note",
            "The reference is embedded in generated note/runbook prose, not used as a live input read.",
        )
    if "temp_prefixes" in context or "re.compile" in context or "/[^" in context:
        return (
            "intentional_temp_detection_literal",
            "preserve_or_mark_scanner_literal_if_it_creates_audit_noise",
            "The reference is part of a detector/classifier literal and should not be rewritten as an input path.",
        )
    if "conalog_mlpe_seed_expand_check" in path_text:
        return (
            "runtime_result_bundle_input",
            "materialize_or_pass_explicit_result_bundle_inputs",
            "The reference points to runtime result artifacts that should be supplied from a stable result bundle.",
        )
    if reference_shape(path_text) == "directory":
        return (
            "static_upstream_directory_input",
            "resolve_from_manifest_or_explicit_directory_input",
            "The reference points to an upstream evidence directory and should move as a bundle, not as a static literal.",
        )
    return (
        "static_upstream_artifact_input",
        "resolve_from_manifest_or_explicit_artifact_input",
        "The reference points to an upstream evidence artifact and should be supplied explicitly or through a manifest.",
    )


def build_review(repo_root: Path, max_file_bytes: int) -> list[dict[str, object]]:
    files, _ = iter_scan_files(repo_root, DEFAULT_SCAN_ROOTS, max_file_bytes)
    audit_rows: list[dict[str, object]] = []
    for path in files:
        audit_rows.extend(scan_file(path, repo_root))

    target_rows = [
        row for row in audit_rows if normalize_text(row.get("triage_priority")) == TARGET_TRIAGE_PRIORITY
    ]

    out: list[dict[str, object]] = []
    for idx, row in enumerate(target_rows, start=1):
        matched_text = normalize_text(row.get("matched_text"))
        context_excerpt = normalize_text(row.get("context_excerpt"))
        kind, resolution, rationale = classify_live_reference(matched_text, context_excerpt)
        literal_or_repro = int(kind in {"embedded_note_repro_command", "intentional_temp_detection_literal"})
        requires_manifest = int(not literal_or_repro)
        out.append(
            {
                "owner_branch": OWNER_BRANCH,
                "review_id": f"BR169-{idx:03d}",
                "source_file": normalize_text(row.get("relative_path")),
                "line_no": int(row.get("line_no", 0)),
                "workflow_lane": normalize_text(row.get("workflow_lane")),
                "matched_text": matched_text,
                "context_excerpt": context_excerpt,
                "default_variable": parse_default_variable(context_excerpt),
                "reference_shape": reference_shape(matched_text),
                "live_reference_kind": kind,
                "requires_manifest_or_explicit_input_flag": requires_manifest,
                "literal_or_repro_only_flag": literal_or_repro,
                "runtime_semantic_change_allowed_flag": 0,
                "bulk_rewrite_allowed_flag": 0,
                "recommended_resolution": resolution,
                "rationale": rationale,
            }
        )
    return out


def summary_rows(review: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = [
        {"owner_branch": OWNER_BRANCH, "summary_scope": "overall", "key": "live_temp_reference_rows", "count": len(review)},
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": "requires_manifest_or_explicit_input_rows",
            "count": sum(int(row["requires_manifest_or_explicit_input_flag"]) for row in review),
        },
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": "literal_or_repro_only_rows",
            "count": sum(int(row["literal_or_repro_only_flag"]) for row in review),
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
            "key": "bulk_rewrite_allowed_rows",
            "count": sum(int(row["bulk_rewrite_allowed_flag"]) for row in review),
        },
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": "source_files",
            "count": len({str(row["source_file"]) for row in review}),
        },
    ]
    for scope, field in [
        ("live_reference_kind", "live_reference_kind"),
        ("workflow_lane", "workflow_lane"),
        ("reference_shape", "reference_shape"),
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
        "# Repo Live Temp Reference Review",
        "",
        "## Boundary",
        "- This is a review/classification artifact only.",
        "- Do not bulk-rewrite evidence paths from this output.",
        "- Do not change runtime diagnosis semantics or `pv_ae/panel_day_engine.py`.",
        "",
        "## Key Counts",
        f"- live temp reference rows: {lookup.get(('overall', 'live_temp_reference_rows'), 0)}",
        f"- requires manifest or explicit input rows: {lookup.get(('overall', 'requires_manifest_or_explicit_input_rows'), 0)}",
        f"- literal or repro only rows: {lookup.get(('overall', 'literal_or_repro_only_rows'), 0)}",
        f"- runtime semantic change allowed rows: {lookup.get(('overall', 'runtime_semantic_change_allowed_rows'), 0)}",
        f"- bulk rewrite allowed rows: {lookup.get(('overall', 'bulk_rewrite_allowed_rows'), 0)}",
        "",
        "## Recommendation",
        "- Treat static upstream artifact/directory rows as the real follow-up lane.",
        "- Treat embedded note repro commands and detector literals as cleanup/noise only.",
        "- Build manifest or explicit-input contracts before deleting or replacing any live path literals.",
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
        "live_temp_reference_rows": len(review),
        "live_reference_kind_counts": dict(Counter(str(row["live_reference_kind"]) for row in review)),
        "workflow_lane_counts": dict(Counter(str(row["workflow_lane"]) for row in review)),
        "requires_manifest_or_explicit_input_rows": sum(
            int(row["requires_manifest_or_explicit_input_flag"]) for row in review
        ),
        "literal_or_repro_only_rows": sum(int(row["literal_or_repro_only_flag"]) for row in review),
        "runtime_semantic_change_allowed_rows": sum(
            int(row["runtime_semantic_change_allowed_flag"]) for row in review
        ),
        "bulk_rewrite_allowed_rows": sum(int(row["bulk_rewrite_allowed_flag"]) for row in review),
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
