#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from build_repo_live_temp_reference_review_v1 import build_review as build_live_temp_review


OWNER_BRANCH = "BR-20260429-170"

DETAIL_OUTPUT_NAME = "panel_day_engine_episode_truth_input_manifest_contract_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_episode_truth_input_manifest_contract_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_episode_truth_input_manifest_contract_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_episode_truth_input_manifest_contract_v1.json"

TARGET_WORKFLOW_LANE = "panel_engine_episode_truth"

DETAIL_COLUMNS = [
    "owner_branch",
    "contract_id",
    "source_file",
    "line_no",
    "consumer_script",
    "consumer_input_flag",
    "upstream_stage_key",
    "default_path",
    "reference_shape",
    "live_reference_kind",
    "manifest_required_flag",
    "explicit_input_supported_flag",
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
            "Build a contract table for episode-truth temp input references before "
            "rewriting any builder defaults."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for contract outputs. Required so this contract builder has no temp default.",
    )
    parser.add_argument("--max-file-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def resolve(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def consumer_script(source_file: str) -> str:
    return Path(source_file).name


def upstream_stage_key(path_text: str) -> str:
    path = Path(path_text.rstrip("/"))
    token = path.name if path.name else path.parent.name
    return token.removesuffix("_check")


def consumer_input_flag(source_file: str, path_text: str, line_no: int) -> str:
    name = Path(source_file).name
    if name == "build_panel_day_engine_episode_truth_adjudication_worksheet_v1.py":
        if "source_trace_audit" in path_text:
            return "--trace-input"
        if "evidence_attachment" in path_text:
            return "--index-input"
    if name == "build_panel_day_engine_episode_truth_conservative_adjudication_v1.py":
        return "--worksheet-input"
    if name == "build_panel_day_engine_episode_truth_durable_shape_review_v1.py":
        return "--br088-input"
    if name == "build_panel_day_engine_episode_truth_evidence_attachment_v1.py":
        return "--reviewed-rows-input"
    if name == "build_panel_day_engine_episode_truth_map_v1.py":
        if "local_morphology_family_shape" in path_text:
            return "--shape-input"
        if "subtype_truth_expansion_backlog" in path_text:
            return "--backlog-input"
    if name == "build_panel_day_engine_episode_truth_review_packet_v1.py":
        return "--episode-map-input"
    if name == "build_panel_day_engine_episode_truth_source_trace_audit_v1.py":
        if "evidence_attachment_index" in path_text:
            return "--index-input"
        if "review_input_template" in path_text:
            return "--template-input"
        if "evidence_attachment" in path_text:
            if line_no <= 19:
                return "--index-input"
            return "--template-input"
    if name == "build_panel_day_engine_reviewed_episode_truth_rows_v1.py":
        if "direction_assumption_audit" in path_text:
            return "--guard-json-input"
        if "episode_truth_review_packet" in path_text:
            return "--packet-input"
    return ""


def build_contract(repo_root: Path, max_file_bytes: int) -> list[dict[str, object]]:
    live_rows = build_live_temp_review(repo_root, max_file_bytes)
    episode_rows = [
        row for row in live_rows if str(row.get("workflow_lane", "")) == TARGET_WORKFLOW_LANE
    ]

    rows: list[dict[str, object]] = []
    for idx, row in enumerate(episode_rows, start=1):
        kind = str(row.get("live_reference_kind", ""))
        literal_or_repro = int(row.get("literal_or_repro_only_flag", 0))
        source_file = str(row.get("source_file", ""))
        path_text = str(row.get("matched_text", ""))
        line_no = int(row.get("line_no", 0))
        flag = "" if literal_or_repro else consumer_input_flag(source_file, path_text, line_no)
        manifest_required = int(not literal_or_repro)
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "contract_id": f"BR170-EPTR-{idx:03d}",
                "source_file": source_file,
                "line_no": line_no,
                "consumer_script": consumer_script(source_file),
                "consumer_input_flag": flag,
                "upstream_stage_key": upstream_stage_key(path_text),
                "default_path": path_text,
                "reference_shape": str(row.get("reference_shape", "")),
                "live_reference_kind": kind,
                "manifest_required_flag": manifest_required,
                "explicit_input_supported_flag": int(bool(flag)),
                "literal_or_repro_only_flag": literal_or_repro,
                "runtime_semantic_change_allowed_flag": 0,
                "bulk_rewrite_allowed_flag": 0,
                "recommended_resolution": (
                    "resolve_from_episode_truth_manifest_or_explicit_input"
                    if manifest_required
                    else "refresh_note_repro_only_when_touching_builder"
                ),
                "rationale": (
                    "Episode-truth chain inputs should be resolved from a manifest or explicit CLI input before "
                    "the temp literal is removed."
                    if manifest_required
                    else "This path is embedded in generated note prose and should not drive input-contract changes."
                ),
            }
        )
    return rows


def summary_rows(contract: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = [
        {"owner_branch": OWNER_BRANCH, "summary_scope": "overall", "key": "episode_truth_reference_rows", "count": len(contract)},
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": "manifest_required_rows",
            "count": sum(int(row["manifest_required_flag"]) for row in contract),
        },
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": "explicit_input_supported_rows",
            "count": sum(int(row["explicit_input_supported_flag"]) for row in contract),
        },
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": "literal_or_repro_only_rows",
            "count": sum(int(row["literal_or_repro_only_flag"]) for row in contract),
        },
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": "runtime_semantic_change_allowed_rows",
            "count": sum(int(row["runtime_semantic_change_allowed_flag"]) for row in contract),
        },
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": "bulk_rewrite_allowed_rows",
            "count": sum(int(row["bulk_rewrite_allowed_flag"]) for row in contract),
        },
    ]
    for scope, field in [
        ("live_reference_kind", "live_reference_kind"),
        ("consumer_script", "consumer_script"),
        ("consumer_input_flag", "consumer_input_flag"),
        ("recommended_resolution", "recommended_resolution"),
    ]:
        for key, count in sorted(Counter(str(row[field]) for row in contract).items()):
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
        "# Panel-Day Engine Episode Truth Input Manifest Contract",
        "",
        "## Boundary",
        "- This is a contract table only.",
        "- Existing episode-truth builders are not rewritten in this branch.",
        "- Direct `pv_ae/panel_day_engine.py` edits remain out of scope.",
        "",
        "## Key Counts",
        f"- episode-truth reference rows: {lookup.get(('overall', 'episode_truth_reference_rows'), 0)}",
        f"- manifest-required rows: {lookup.get(('overall', 'manifest_required_rows'), 0)}",
        f"- explicit-input-supported rows: {lookup.get(('overall', 'explicit_input_supported_rows'), 0)}",
        f"- literal/repro-only rows: {lookup.get(('overall', 'literal_or_repro_only_rows'), 0)}",
        f"- runtime semantic change allowed rows: {lookup.get(('overall', 'runtime_semantic_change_allowed_rows'), 0)}",
        f"- bulk rewrite allowed rows: {lookup.get(('overall', 'bulk_rewrite_allowed_rows'), 0)}",
        "",
        "## Recommendation",
        "- Next branch should add a small episode-truth manifest resolver or require explicit inputs for selected chain scripts.",
        "- Do not delete the temp defaults until those consumers have a manifest or explicit input path in reproducible commands.",
    ]
    path = output_dir / NOTE_OUTPUT_NAME
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = resolve(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    contract = build_contract(repo_root, args.max_file_bytes)
    summary = summary_rows(contract)

    detail_path = output_dir / DETAIL_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME
    write_csv(detail_path, contract, DETAIL_COLUMNS)
    write_csv(summary_path, summary, SUMMARY_COLUMNS)
    note_path = write_note(output_dir, summary)

    payload = {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "episode_truth_reference_rows": len(contract),
        "manifest_required_rows": sum(int(row["manifest_required_flag"]) for row in contract),
        "explicit_input_supported_rows": sum(int(row["explicit_input_supported_flag"]) for row in contract),
        "literal_or_repro_only_rows": sum(int(row["literal_or_repro_only_flag"]) for row in contract),
        "runtime_semantic_change_allowed_rows": sum(
            int(row["runtime_semantic_change_allowed_flag"]) for row in contract
        ),
        "bulk_rewrite_allowed_rows": sum(int(row["bulk_rewrite_allowed_flag"]) for row in contract),
        "live_reference_kind_counts": dict(Counter(str(row["live_reference_kind"]) for row in contract)),
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
