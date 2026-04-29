#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from build_repo_live_temp_reference_review_v1 import build_review, resolve


OWNER_BRANCH = "BR-20260429-223"
EXPECTED_LITERAL_OR_REPRO_ROWS = 6
EXPECTED_EMBEDDED_REPRO_ROWS = 4
EXPECTED_DETECTOR_LITERAL_ROWS = 2

DETAIL_OUTPUT_NAME = "live_temp_literal_repro_closure_audit_v1.csv"
SUMMARY_OUTPUT_NAME = "live_temp_literal_repro_closure_audit_summary_v1.csv"
NOTE_OUTPUT_NAME = "live_temp_literal_repro_closure_audit_note_v1.md"
JSON_OUTPUT_NAME = "live_temp_literal_repro_closure_audit_v1.json"

DETAIL_COLUMNS = [
    "owner_branch",
    "closure_id",
    "source_file",
    "line_no",
    "workflow_lane",
    "matched_text",
    "live_reference_kind",
    "closure_class",
    "requires_manifest_or_explicit_input_flag",
    "literal_or_repro_only_flag",
    "runtime_semantic_change_allowed_flag",
    "bulk_rewrite_allowed_flag",
    "input_contract_gap_flag",
    "operator_action_required_flag",
    "recommended_resolution",
    "rationale",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Close the literal/repro-only live-temp rows by proving they are not live "
            "input dependencies and should not trigger manifest contracts."
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


def closure_class(kind: str) -> str:
    if kind == "embedded_note_repro_command":
        return "closed_embedded_repro_command"
    if kind == "intentional_temp_detection_literal":
        return "closed_intentional_detector_literal"
    return "unexpected_literal_or_repro_kind"


def build_audit(repo_root: Path, max_file_bytes: int) -> list[dict[str, object]]:
    review = build_review(repo_root, max_file_bytes)
    literal_rows = [row for row in review if int(row.get("literal_or_repro_only_flag", 0)) == 1]
    out: list[dict[str, object]] = []
    for idx, row in enumerate(literal_rows, start=1):
        kind = str(row["live_reference_kind"])
        out.append(
            {
                "owner_branch": OWNER_BRANCH,
                "closure_id": f"BR223-{idx:03d}",
                "source_file": str(row["source_file"]),
                "line_no": int(row["line_no"]),
                "workflow_lane": str(row["workflow_lane"]),
                "matched_text": str(row["matched_text"]),
                "live_reference_kind": kind,
                "closure_class": closure_class(kind),
                "requires_manifest_or_explicit_input_flag": int(
                    row["requires_manifest_or_explicit_input_flag"]
                ),
                "literal_or_repro_only_flag": int(row["literal_or_repro_only_flag"]),
                "runtime_semantic_change_allowed_flag": int(row["runtime_semantic_change_allowed_flag"]),
                "bulk_rewrite_allowed_flag": int(row["bulk_rewrite_allowed_flag"]),
                "input_contract_gap_flag": 0,
                "operator_action_required_flag": 0,
                "recommended_resolution": str(row["recommended_resolution"]),
                "rationale": str(row["rationale"]),
            }
        )
    return out


def summary_payload(audit_rows: list[dict[str, object]]) -> dict[str, object]:
    kind_counts = Counter(str(row["live_reference_kind"]) for row in audit_rows)
    closure_counts = Counter(str(row["closure_class"]) for row in audit_rows)
    input_gap_count = sum(int(row["input_contract_gap_flag"]) for row in audit_rows)
    closure_complete = int(
        len(audit_rows) == EXPECTED_LITERAL_OR_REPRO_ROWS
        and kind_counts.get("embedded_note_repro_command", 0) == EXPECTED_EMBEDDED_REPRO_ROWS
        and kind_counts.get("intentional_temp_detection_literal", 0) == EXPECTED_DETECTOR_LITERAL_ROWS
        and sum(int(row["requires_manifest_or_explicit_input_flag"]) for row in audit_rows) == 0
        and input_gap_count == 0
    )
    payload: dict[str, object] = {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_literal_or_repro_rows": EXPECTED_LITERAL_OR_REPRO_ROWS,
        "literal_or_repro_rows": len(audit_rows),
        "embedded_note_repro_command_rows": kind_counts.get("embedded_note_repro_command", 0),
        "intentional_temp_detection_literal_rows": kind_counts.get(
            "intentional_temp_detection_literal", 0
        ),
        "source_file_count": len({str(row["source_file"]) for row in audit_rows}),
        "requires_manifest_or_explicit_input_rows": sum(
            int(row["requires_manifest_or_explicit_input_flag"]) for row in audit_rows
        ),
        "input_contract_gap_rows": input_gap_count,
        "operator_action_required_rows": sum(
            int(row["operator_action_required_flag"]) for row in audit_rows
        ),
        "runtime_semantic_change_allowed_rows": sum(
            int(row["runtime_semantic_change_allowed_flag"]) for row in audit_rows
        ),
        "bulk_rewrite_allowed_rows": sum(int(row["bulk_rewrite_allowed_flag"]) for row in audit_rows),
        "closure_complete": closure_complete,
        "live_reference_kind_counts": dict(kind_counts),
        "closure_class_counts": dict(closure_counts),
        "workflow_lane_counts": dict(Counter(str(row["workflow_lane"]) for row in audit_rows)),
        "recommended_next_branch": (
            "p1_live_temp_reference_lane_closure_audit"
            if closure_complete
            else "inspect_unexpected_literal_or_repro_rows"
        ),
    }
    return payload


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    keys = [
        "expected_literal_or_repro_rows",
        "literal_or_repro_rows",
        "embedded_note_repro_command_rows",
        "intentional_temp_detection_literal_rows",
        "source_file_count",
        "requires_manifest_or_explicit_input_rows",
        "input_contract_gap_rows",
        "operator_action_required_rows",
        "runtime_semantic_change_allowed_rows",
        "bulk_rewrite_allowed_rows",
        "closure_complete",
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
        ("closure_class", "closure_class_counts"),
        ("workflow_lane", "workflow_lane_counts"),
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
        "# Live Temp Literal/Repro Closure Audit",
        "",
        "## Boundary",
        "- This branch closes literal/repro-only live-temp rows.",
        "- It does not rewrite embedded note repro commands.",
        "- It does not rewrite detector literals.",
        "- It does not change `pv_ae/panel_day_engine.py`, runtime semantics, truth, threshold, or operator-facing behavior.",
        "",
        "## Summary",
        f"- literal or repro rows: `{payload['literal_or_repro_rows']}`",
        f"- embedded note repro command rows: `{payload['embedded_note_repro_command_rows']}`",
        f"- intentional temp detector literal rows: `{payload['intentional_temp_detection_literal_rows']}`",
        f"- source files: `{payload['source_file_count']}`",
        f"- requires manifest or explicit input rows: `{payload['requires_manifest_or_explicit_input_rows']}`",
        f"- input contract gap rows: `{payload['input_contract_gap_rows']}`",
        f"- operator action required rows: `{payload['operator_action_required_rows']}`",
        f"- runtime semantic change allowed rows: `{payload['runtime_semantic_change_allowed_rows']}`",
        f"- bulk rewrite allowed rows: `{payload['bulk_rewrite_allowed_rows']}`",
        f"- closure complete: `{payload['closure_complete']}`",
        "",
        "## Decision",
        "- Treat these rows as closed non-input references when counts remain stable.",
        "- Refresh embedded repro commands only when touching the owning builder notes.",
        "- Preserve detector literals unless they produce new audit self-noise.",
        "- Continue to a full p1 live-temp lane closure audit next.",
    ]
    path = output_dir / NOTE_OUTPUT_NAME
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = resolve(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audit_rows = build_audit(repo_root, args.max_file_bytes)
    payload = summary_payload(audit_rows)

    detail_path = output_dir / DETAIL_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME
    note_path = write_note(output_dir, payload)

    write_csv(detail_path, audit_rows, DETAIL_COLUMNS)
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
