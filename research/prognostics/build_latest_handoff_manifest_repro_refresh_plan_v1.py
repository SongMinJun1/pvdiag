#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import shlex
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

try:
    from build_generated_handoff_repro_literal_audit_v1 import (
        build_detail_rows as build_generated_literal_detail_rows,
    )
except ImportError:
    from research.prognostics.build_generated_handoff_repro_literal_audit_v1 import (
        build_detail_rows as build_generated_literal_detail_rows,
    )


OWNER_BRANCH = "BR-20260429-229"

DETAIL_OUTPUT_NAME = "latest_handoff_manifest_repro_refresh_plan_v1.csv"
SUMMARY_OUTPUT_NAME = "latest_handoff_manifest_repro_refresh_plan_summary_v1.csv"
NOTE_OUTPUT_NAME = "latest_handoff_manifest_repro_refresh_plan_note_v1.md"
JSON_OUTPUT_NAME = "latest_handoff_manifest_repro_refresh_plan_v1.json"

LATEST_HANDOFF_PATH = (
    "research/prognostics/build_panel_day_engine_latest_evidence_handoff_manifest_v1.py"
)
OUTPUT_FLAGS = {"--output-dir", "--output-root"}
REPO_ROOT_FLAGS = {"--repo-root"}

DETAIL_COLUMNS = [
    "owner_branch",
    "plan_id",
    "branch_id",
    "branch_title",
    "evidence_layer",
    "handoff_state",
    "primary_artifact_path",
    "artifact_location_type",
    "repro_temp_literal_count",
    "temp_input_literal_count",
    "temp_output_literal_count",
    "temp_repo_root_literal_count",
    "manifest_input_required",
    "output_parameterization_required",
    "repo_root_refresh_required",
    "refresh_bucket",
    "manual_literal_edit_allowed",
    "runtime_semantic_change_allowed_rows",
    "operator_facing_change_allowed_rows",
    "recommended_next_action",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a branch-level refresh plan for the latest evidence handoff manifest "
            "without editing generated repro literals by hand."
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


def load_module(path: Path) -> ModuleType:
    if not path.exists():
        raise SystemExit(f"missing latest handoff builder: {path}")
    spec = importlib.util.spec_from_file_location("latest_handoff_manifest_builder", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load latest handoff builder: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def classify_artifact(path_text: str) -> str:
    return "temp" if path_text.startswith(("/private/tmp/", "/tmp/", "/private/var/")) else "repo"


def temp_pairs(repro_command: str) -> list[tuple[str, str]]:
    tokens = shlex.split(repro_command)
    pairs: list[tuple[str, str]] = []
    for index, token in enumerate(tokens[:-1]):
        value = tokens[index + 1]
        if token.startswith("--") and value.startswith("/private/tmp/"):
            pairs.append((token, value))
    return pairs


def classify_refresh_bucket(
    temp_input_count: int,
    temp_output_count: int,
    temp_repo_root_count: int,
) -> str:
    if temp_input_count == 0 and temp_output_count == 0 and temp_repo_root_count == 0:
        return "repo_doc_no_repro_refresh_needed"
    if temp_repo_root_count:
        return "repo_root_plus_manifest_input_refresh_plan"
    if temp_input_count and temp_output_count:
        return "manifest_inputs_and_parameterized_output_plan"
    if temp_input_count:
        return "manifest_input_only_refresh_plan"
    if temp_output_count:
        return "parameterized_output_only_refresh_plan"
    return "manual_review"


def build_detail_rows(repo_root: Path) -> list[dict[str, object]]:
    module = load_module(repo_root / LATEST_HANDOFF_PATH)
    branch_specs = getattr(module, "BRANCH_SPECS", None)
    if not isinstance(branch_specs, list):
        raise SystemExit("latest handoff builder does not expose BRANCH_SPECS list")

    rows: list[dict[str, object]] = []
    for index, spec in enumerate(branch_specs, start=1):
        if not isinstance(spec, dict):
            raise SystemExit("latest handoff BRANCH_SPECS contains a non-dict row")
        repro_command = str(spec.get("repro_command", ""))
        pairs = temp_pairs(repro_command)
        temp_output_count = sum(1 for flag, _value in pairs if flag in OUTPUT_FLAGS)
        temp_repo_root_count = sum(1 for flag, _value in pairs if flag in REPO_ROOT_FLAGS)
        temp_input_count = len(pairs) - temp_output_count - temp_repo_root_count
        refresh_bucket = classify_refresh_bucket(
            temp_input_count,
            temp_output_count,
            temp_repo_root_count,
        )

        if refresh_bucket == "repo_doc_no_repro_refresh_needed":
            next_action = "preserve repo-doc handoff row; no latest-handoff repro refresh needed"
        elif temp_repo_root_count:
            next_action = (
                "refresh as generated command using current checkout repo-root plus manifestized "
                "inputs and parameterized output root"
            )
        else:
            next_action = (
                "refresh as generated command with manifestized inputs and parameterized output "
                "root; do not edit literals one by one"
            )

        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "plan_id": f"BR229-{index:03d}",
                "branch_id": spec.get("branch_id", ""),
                "branch_title": spec.get("branch_title", ""),
                "evidence_layer": spec.get("evidence_layer", ""),
                "handoff_state": spec.get("handoff_state", ""),
                "primary_artifact_path": spec.get("primary_artifact_path", ""),
                "artifact_location_type": classify_artifact(str(spec.get("primary_artifact_path", ""))),
                "repro_temp_literal_count": len(pairs),
                "temp_input_literal_count": temp_input_count,
                "temp_output_literal_count": temp_output_count,
                "temp_repo_root_literal_count": temp_repo_root_count,
                "manifest_input_required": int(temp_input_count > 0),
                "output_parameterization_required": int(temp_output_count > 0),
                "repo_root_refresh_required": int(temp_repo_root_count > 0),
                "refresh_bucket": refresh_bucket,
                "manual_literal_edit_allowed": 0,
                "runtime_semantic_change_allowed_rows": 0,
                "operator_facing_change_allowed_rows": 0,
                "recommended_next_action": next_action,
            }
        )
    return rows


def build_payload(
    repo_root: Path,
    branch_rows: list[dict[str, object]],
    max_file_bytes: int,
) -> dict[str, object]:
    _path_rows, generated_literal_rows = build_generated_literal_detail_rows(repo_root, max_file_bytes)
    latest_literal_rows = [
        row
        for row in generated_literal_rows
        if str(row.get("literal_role", "")) == "latest_evidence_handoff_manifest_repro"
    ]

    bucket_counts = Counter(str(row["refresh_bucket"]) for row in branch_rows)
    layer_counts = Counter(str(row["evidence_layer"]) for row in branch_rows)
    handoff_state_counts = Counter(str(row["handoff_state"]) for row in branch_rows)
    temp_input_literals = sum(int(row["temp_input_literal_count"]) for row in branch_rows)
    temp_output_literals = sum(int(row["temp_output_literal_count"]) for row in branch_rows)
    temp_repo_root_literals = sum(int(row["temp_repo_root_literal_count"]) for row in branch_rows)
    repro_temp_literals = sum(int(row["repro_temp_literal_count"]) for row in branch_rows)
    refresh_required_branches = sum(
        1 for row in branch_rows if str(row["refresh_bucket"]) != "repo_doc_no_repro_refresh_needed"
    )

    return {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "branch_spec_rows": len(branch_rows),
        "refresh_required_branch_rows": refresh_required_branches,
        "repo_doc_no_refresh_branch_rows": bucket_counts.get("repo_doc_no_repro_refresh_needed", 0),
        "latest_handoff_repro_literal_rows_from_br228": len(latest_literal_rows),
        "planned_repro_temp_literal_rows": repro_temp_literals,
        "temp_input_literal_rows": temp_input_literals,
        "temp_output_literal_rows": temp_output_literals,
        "temp_repo_root_literal_rows": temp_repo_root_literals,
        "manifest_input_required_branch_rows": sum(
            int(row["manifest_input_required"]) for row in branch_rows
        ),
        "output_parameterization_required_branch_rows": sum(
            int(row["output_parameterization_required"]) for row in branch_rows
        ),
        "repo_root_refresh_required_branch_rows": sum(
            int(row["repo_root_refresh_required"]) for row in branch_rows
        ),
        "manual_literal_edit_allowed_rows": sum(
            int(row["manual_literal_edit_allowed"]) for row in branch_rows
        ),
        "runtime_semantic_change_allowed_rows": 0,
        "operator_facing_change_allowed_rows": 0,
        "latest_literal_count_match": int(len(latest_literal_rows) == repro_temp_literals),
        "refresh_plan_complete": int(
            len(branch_rows) > 0
            and len(latest_literal_rows) == repro_temp_literals
            and sum(int(row["manual_literal_edit_allowed"]) for row in branch_rows) == 0
        ),
        "refresh_bucket_counts": dict(sorted(bucket_counts.items())),
        "evidence_layer_counts": dict(sorted(layer_counts.items())),
        "handoff_state_counts": dict(sorted(handoff_state_counts.items())),
        "recommended_next_branch": "latest_handoff_manifest_repro_refresh_dry_run",
    }


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scalar_keys = [
        "branch_spec_rows",
        "refresh_required_branch_rows",
        "repo_doc_no_refresh_branch_rows",
        "latest_handoff_repro_literal_rows_from_br228",
        "planned_repro_temp_literal_rows",
        "temp_input_literal_rows",
        "temp_output_literal_rows",
        "temp_repo_root_literal_rows",
        "manifest_input_required_branch_rows",
        "output_parameterization_required_branch_rows",
        "repo_root_refresh_required_branch_rows",
        "manual_literal_edit_allowed_rows",
        "runtime_semantic_change_allowed_rows",
        "operator_facing_change_allowed_rows",
        "latest_literal_count_match",
        "refresh_plan_complete",
    ]
    for key in scalar_keys:
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "overall",
                "key": key,
                "count": payload[key],
            }
        )
    for scope_key in ["refresh_bucket_counts", "evidence_layer_counts", "handoff_state_counts"]:
        scope = scope_key.removesuffix("_counts")
        for key, value in payload[scope_key].items():
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": scope,
                    "key": key,
                    "count": value,
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def render_note(payload: dict[str, object]) -> str:
    return "\n".join(
        [
            "# Latest Handoff Manifest Repro Refresh Plan V1",
            "",
            "## Summary",
            "- Builds a branch-level refresh plan for the latest evidence handoff manifest.",
            "- This is a plan/audit patch only; it does not rewrite generated repro literals.",
            "- The plan converts literal cleanup into manifestized inputs, parameterized output roots, and current checkout repo-root handling.",
            "",
            "## Counts",
            f"- branch_spec_rows: `{payload['branch_spec_rows']}`",
            f"- refresh_required_branch_rows: `{payload['refresh_required_branch_rows']}`",
            f"- repo_doc_no_refresh_branch_rows: `{payload['repo_doc_no_refresh_branch_rows']}`",
            f"- latest_handoff_repro_literal_rows_from_br228: `{payload['latest_handoff_repro_literal_rows_from_br228']}`",
            f"- planned_repro_temp_literal_rows: `{payload['planned_repro_temp_literal_rows']}`",
            f"- temp_input_literal_rows: `{payload['temp_input_literal_rows']}`",
            f"- temp_output_literal_rows: `{payload['temp_output_literal_rows']}`",
            f"- temp_repo_root_literal_rows: `{payload['temp_repo_root_literal_rows']}`",
            f"- manual_literal_edit_allowed_rows: `{payload['manual_literal_edit_allowed_rows']}`",
            f"- latest_literal_count_match: `{payload['latest_literal_count_match']}`",
            f"- refresh_plan_complete: `{payload['refresh_plan_complete']}`",
            "",
            "## Boundary",
            "- Do not edit latest handoff repro literals one by one.",
            "- Inputs should become manifestized or explicit CLI inputs in the refreshed generator.",
            "- Output roots should be parameterized output destinations, not evidence dependencies.",
            "- The one stale repo-root literal should become current checkout based repro text.",
            "",
            "## Next Action",
            f"- Recommended next branch: `{payload['recommended_next_branch']}`.",
            "- Keep this separate from runtime semantics and panel-engine code.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    branch_rows = build_detail_rows(repo_root)
    payload = build_payload(repo_root, branch_rows, args.max_file_bytes)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / DETAIL_OUTPUT_NAME, branch_rows, DETAIL_COLUMNS)
    write_csv(args.output_dir / SUMMARY_OUTPUT_NAME, summary_rows(payload), SUMMARY_COLUMNS)
    (args.output_dir / NOTE_OUTPUT_NAME).write_text(render_note(payload), encoding="utf-8")
    (args.output_dir / JSON_OUTPUT_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
