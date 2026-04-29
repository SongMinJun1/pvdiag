#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from build_repo_live_temp_reference_review_v1 import build_review as build_live_temp_review


OWNER_BRANCH = "BR-20260429-180"

DETAIL_OUTPUT_NAME = "panel_day_engine_evidence_input_manifest_contract_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_evidence_input_manifest_contract_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_evidence_input_manifest_contract_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_evidence_input_manifest_contract_v1.json"

TARGET_WORKFLOW_LANE = "panel_day_engine_evidence"

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
            "Build a contract table for panel-day evidence temp input references before "
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
    text = path_text.lower()
    if name == "build_panel_day_engine_direction_assumption_audit_v1.py":
        if "algorithm_evolution_map" in text:
            return "--br079-root"
        if "subtype_truth_expansion_backlog" in text:
            return "--br080-root"
        if "episode_truth_map" in text:
            return "--br081-root"
        if "episode_truth_review_packet" in text:
            return "--br082-root"
    if name == "build_panel_day_engine_durable_hold_raw_shape_review_v1.py":
        return "--shape-input"
    if name == "build_panel_day_engine_exact_family_closure_readiness_review_v1.py":
        if "local_morphology_exact_seed_search" in text:
            return "--local-morphology-input"
        if "no_report_heuristic_gap_review" in text:
            return "--gap-review-input"
        if "non_fault_morphology_observation_sidecar" in text:
            return "--observation-sidecar-input"
    if name == "build_panel_day_engine_fault_family_judgment_candidate_packet_v1.py":
        if "cross_axis_manifest_sync_review" in text:
            return "--cross-axis-input"
        if "fault_family_regression_pressure_packet" in text:
            return "--pressure-input"
    if name == "build_panel_day_engine_fault_family_regression_pressure_packet_v1.py":
        return "--readiness-input"
    if name == "build_panel_day_engine_local_morphology_family_shape_review_v1.py":
        return "--packet-input"
    if name == "build_panel_day_engine_non_fault_morphology_observation_sidecar_v1.py":
        return "--gap-review-input"
    if name == "build_panel_day_engine_physical_confirmation_requirements_review_v1.py":
        return "--raw-review-input"
    if name == "build_panel_day_engine_physical_evidence_request_packet_v1.py":
        return "--confirmation-input" if line_no <= 12 else "--checklist-input"
    if name == "build_panel_day_engine_raw_waveform_physical_support_review_v1.py":
        return "--review-input"
    if name == "build_panel_day_engine_subtype_threshold_replay_pilot_v1.py":
        if "durable_shape_review" in text:
            return "--shape-input"
        if "reviewed_episode_truth_rows" in text:
            return "--reviewed-truth-input"
    if name == "build_panel_day_engine_subtype_truth_expansion_backlog_v1.py":
        if "algorithm_evolution_map" in text:
            return "--br079-gap-input"
        if "fault_family_judgment_candidate_packet" in text:
            return "--candidate-packet-input"
        if "local_morphology_family_shape_review" in text:
            return "--shape-review-input"
        if "physical_confirmation_requirements_review" in text:
            return "--physical-confirmation-input"
        if "common_cause_exact_seed_search" in text:
            return "--common-cause-search-input"
    if name == "build_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py":
        return "--shape-input"
    if name == "check_panel_day_engine_fault_family_regression_prepatch_gate_v1.py":
        return "--packet-input"
    return ""


def build_contract(repo_root: Path, max_file_bytes: int) -> list[dict[str, object]]:
    live_rows = build_live_temp_review(repo_root, max_file_bytes)
    evidence_rows = [
        row for row in live_rows if str(row.get("workflow_lane", "")) == TARGET_WORKFLOW_LANE
    ]

    rows: list[dict[str, object]] = []
    for idx, row in enumerate(evidence_rows, start=1):
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
                "contract_id": f"BR180-EVTR-{idx:03d}",
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
                    "resolve_from_panel_day_evidence_manifest_or_explicit_input"
                    if manifest_required
                    else "refresh_note_or_scanner_literal_only_when_touching_builder"
                ),
                "rationale": (
                    "Panel-day evidence inputs should be resolved from a manifest or explicit CLI input before "
                    "the temp literal is removed."
                    if manifest_required
                    else "This path is note prose or scanner logic and should not drive input-contract changes."
                ),
            }
        )
    return rows


def summary_rows(contract: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = [
        {"owner_branch": OWNER_BRANCH, "summary_scope": "overall", "key": "evidence_reference_rows", "count": len(contract)},
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
            "key": "unmapped_required_rows",
            "count": sum(
                int(row["manifest_required_flag"]) and not int(row["explicit_input_supported_flag"])
                for row in contract
            ),
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
        "# Panel-Day Engine Evidence Input Manifest Contract",
        "",
        "## Boundary",
        "- This is a contract table only.",
        "- Existing panel-day evidence builders are not rewritten in this branch.",
        "- Direct `pv_ae/panel_day_engine.py` edits remain out of scope.",
        "- Runtime diagnosis, truth labels, threshold tuning, and operator-facing outputs are unchanged.",
        "",
        "## Key Counts",
        f"- evidence reference rows: {lookup.get(('overall', 'evidence_reference_rows'), 0)}",
        f"- manifest-required rows: {lookup.get(('overall', 'manifest_required_rows'), 0)}",
        f"- explicit-input-supported rows: {lookup.get(('overall', 'explicit_input_supported_rows'), 0)}",
        f"- literal/repro-only rows: {lookup.get(('overall', 'literal_or_repro_only_rows'), 0)}",
        f"- unmapped required rows: {lookup.get(('overall', 'unmapped_required_rows'), 0)}",
        f"- runtime semantic change allowed rows: {lookup.get(('overall', 'runtime_semantic_change_allowed_rows'), 0)}",
        f"- bulk rewrite allowed rows: {lookup.get(('overall', 'bulk_rewrite_allowed_rows'), 0)}",
        "",
        "## Recommendation",
        "- Next branch should pick one high-impact evidence consumer and add a manifest resolver or fail-closed explicit-input path.",
        "- Do not delete the temp defaults until each consumer has a manifest or explicit input path in reproducible commands.",
        "- Note/repro and scanner-literal rows should stay out of input-contract execution patches.",
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

    lookup = {(row["summary_scope"], row["key"]): int(row["count"]) for row in summary}
    payload = {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workflow_lane": TARGET_WORKFLOW_LANE,
        "evidence_reference_rows": lookup.get(("overall", "evidence_reference_rows"), 0),
        "manifest_required_rows": lookup.get(("overall", "manifest_required_rows"), 0),
        "explicit_input_supported_rows": lookup.get(("overall", "explicit_input_supported_rows"), 0),
        "literal_or_repro_only_rows": lookup.get(("overall", "literal_or_repro_only_rows"), 0),
        "unmapped_required_rows": lookup.get(("overall", "unmapped_required_rows"), 0),
        "runtime_semantic_change_allowed_rows": lookup.get(("overall", "runtime_semantic_change_allowed_rows"), 0),
        "bulk_rewrite_allowed_rows": lookup.get(("overall", "bulk_rewrite_allowed_rows"), 0),
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
