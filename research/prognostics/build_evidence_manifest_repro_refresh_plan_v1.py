#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType


OWNER_BRANCH = "BR-20260429-234"

SOURCE_BUILDER_PATH = "research/prognostics/build_panel_day_engine_evidence_manifest_v1.py"

DETAIL_OUTPUT_NAME = "evidence_manifest_repro_refresh_plan_v1.csv"
SUMMARY_OUTPUT_NAME = "evidence_manifest_repro_refresh_plan_summary_v1.csv"
NOTE_OUTPUT_NAME = "evidence_manifest_repro_refresh_plan_note_v1.md"
JSON_OUTPUT_NAME = "evidence_manifest_repro_refresh_plan_v1.json"

OUTPUT_ROOT_PLACEHOLDER = "${EVIDENCE_MANIFEST_OUTPUT_ROOT}"
RUNTIME_OUTPUT_ROOT = f"{OUTPUT_ROOT_PLACEHOLDER}/runtime"
RUNTIME_RESULT_ROOT = f"{OUTPUT_ROOT_PLACEHOLDER}/runtime/result"

COMMAND_SPECS = [
    {
        "source_constant": "RUNTIME_REPRO_COMMAND",
        "command_repro_mode": "runtime_run",
        "literals": [
            {
                "literal_role": "runtime_output_root",
                "old_literal": "/private/tmp/conalog_mlpe_seed_expand_check",
                "placeholder_literal": RUNTIME_OUTPUT_ROOT,
                "replacement_kind": "parameterized_runtime_output_root",
            }
        ],
    },
    {
        "source_constant": "REPORT_ENTRY_REPRO_COMMAND",
        "command_repro_mode": "builder",
        "literals": [
            {
                "literal_role": "sidecar_result_root",
                "old_literal": "/private/tmp/conalog_mlpe_seed_expand_check/result",
                "placeholder_literal": RUNTIME_RESULT_ROOT,
                "replacement_kind": "shared_runtime_result_root",
            },
            {
                "literal_role": "sidecar_output_dir",
                "old_literal": "/private/tmp/report_entry_friction_axis_sidecar_check",
                "placeholder_literal": f"{OUTPUT_ROOT_PLACEHOLDER}/report_entry_friction_axis_sidecar",
                "replacement_kind": "parameterized_sidecar_output_dir",
            },
        ],
    },
    {
        "source_constant": "RECOVERY_REPRO_COMMAND",
        "command_repro_mode": "builder",
        "literals": [
            {
                "literal_role": "sidecar_result_root",
                "old_literal": "/private/tmp/conalog_mlpe_seed_expand_check/result",
                "placeholder_literal": RUNTIME_RESULT_ROOT,
                "replacement_kind": "shared_runtime_result_root",
            },
            {
                "literal_role": "sidecar_output_dir",
                "old_literal": "/private/tmp/recovery_recurrence_axis_sidecar_check",
                "placeholder_literal": f"{OUTPUT_ROOT_PLACEHOLDER}/recovery_recurrence_axis_sidecar",
                "replacement_kind": "parameterized_sidecar_output_dir",
            },
        ],
    },
    {
        "source_constant": "COMMON_CAUSE_REPRO_COMMAND",
        "command_repro_mode": "builder",
        "literals": [
            {
                "literal_role": "sidecar_result_root",
                "old_literal": "/private/tmp/conalog_mlpe_seed_expand_check/result",
                "placeholder_literal": RUNTIME_RESULT_ROOT,
                "replacement_kind": "shared_runtime_result_root",
            },
            {
                "literal_role": "sidecar_output_dir",
                "old_literal": "/private/tmp/common_cause_synchrony_axis_sidecar_check",
                "placeholder_literal": f"{OUTPUT_ROOT_PLACEHOLDER}/common_cause_synchrony_axis_sidecar",
                "replacement_kind": "parameterized_sidecar_output_dir",
            },
        ],
    },
]

DETAIL_COLUMNS = [
    "owner_branch",
    "plan_id",
    "source_constant",
    "command_repro_mode",
    "literal_role",
    "old_literal",
    "placeholder_literal",
    "replacement_kind",
    "refresh_bucket",
    "literal_apply_status",
    "old_repro_command",
    "proposed_repro_command",
    "old_private_tmp_literal_count",
    "proposed_private_tmp_literal_count",
    "artifact_spec_rows_using_command",
    "manual_literal_edit_allowed",
    "runtime_semantic_change_allowed_rows",
    "operator_facing_change_allowed_rows",
    "recommended_next_action",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plan the evidence manifest repro-command refresh by mapping hard-coded "
            "/private/tmp literals to a single operator-provided output root. This does "
            "not edit the manifest builder or run production jobs."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for plan outputs. Required to avoid hidden temp defaults.",
    )
    return parser.parse_args()


def load_module(path: Path) -> ModuleType:
    if not path.exists():
        raise SystemExit(f"missing evidence manifest builder: {path}")
    spec = importlib.util.spec_from_file_location("panel_day_engine_evidence_manifest", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load evidence manifest builder: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def private_tmp_count(text: str) -> int:
    return text.count("/private/tmp/")


def build_command_replacement(command: str, literal_specs: list[dict[str, str]]) -> str:
    proposed = command
    for literal_spec in sorted(literal_specs, key=lambda item: len(item["old_literal"]), reverse=True):
        proposed = proposed.replace(
            literal_spec["old_literal"],
            literal_spec["placeholder_literal"],
        )
    return proposed


def artifact_spec_count_for_command(module: ModuleType, command: str) -> int:
    artifact_specs = getattr(module, "ARTIFACT_SPECS", [])
    if not isinstance(artifact_specs, list):
        raise SystemExit("evidence manifest builder does not expose ARTIFACT_SPECS list")
    return sum(
        1
        for spec in artifact_specs
        if isinstance(spec, dict) and str(spec.get("repro_command", "")) == command
    )


def build_detail_rows(repo_root: Path) -> list[dict[str, object]]:
    module = load_module(repo_root / SOURCE_BUILDER_PATH)
    rows: list[dict[str, object]] = []
    plan_index = 1
    for command_spec in COMMAND_SPECS:
        source_constant = str(command_spec["source_constant"])
        command = str(getattr(module, source_constant, ""))
        if not command:
            raise SystemExit(f"missing source command constant: {source_constant}")
        literal_specs = command_spec["literals"]
        proposed_command = build_command_replacement(command, literal_specs)
        old_private_count = private_tmp_count(command)
        proposed_private_count = private_tmp_count(proposed_command)
        artifact_count = artifact_spec_count_for_command(module, command)
        for literal_spec in literal_specs:
            old_literal = literal_spec["old_literal"]
            placeholder_literal = literal_spec["placeholder_literal"]
            old_literal_occurrences = command.count(old_literal)
            placeholder_occurrences = command.count(placeholder_literal)
            if old_literal_occurrences == 1:
                literal_apply_status = "pending_replacement"
            elif old_literal_occurrences == 0 and placeholder_occurrences == 1:
                proposed_command = command
                proposed_private_count = old_private_count
                literal_apply_status = "already_applied"
            else:
                raise SystemExit(
                    f"{source_constant} expected one occurrence of either {old_literal} or "
                    f"{placeholder_literal}; found old={old_literal_occurrences}, "
                    f"placeholder={placeholder_occurrences}"
                )
            refresh_bucket = (
                "runtime_output_root_parameterization_plan"
                if literal_spec["literal_role"] == "runtime_output_root"
                else "sidecar_repro_root_parameterization_plan"
            )
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "plan_id": f"BR234-{plan_index:03d}",
                    "source_constant": source_constant,
                    "command_repro_mode": command_spec["command_repro_mode"],
                    "literal_role": literal_spec["literal_role"],
                    "old_literal": old_literal,
                    "placeholder_literal": literal_spec["placeholder_literal"],
                    "replacement_kind": literal_spec["replacement_kind"],
                    "refresh_bucket": refresh_bucket,
                    "literal_apply_status": literal_apply_status,
                    "old_repro_command": command,
                    "proposed_repro_command": proposed_command,
                    "old_private_tmp_literal_count": old_private_count,
                    "proposed_private_tmp_literal_count": proposed_private_count,
                    "artifact_spec_rows_using_command": artifact_count,
                    "manual_literal_edit_allowed": 0,
                    "runtime_semantic_change_allowed_rows": 0,
                    "operator_facing_change_allowed_rows": 0,
                    "recommended_next_action": (
                        "generate a dry-run patch for build_panel_day_engine_evidence_manifest_v1.py; "
                        "preserve manual_oneoff repro rows and do not hand-edit generated literals"
                    ),
                }
            )
            plan_index += 1
    return rows


def manual_oneoff_command_count(module: ModuleType) -> int:
    commands = {
        str(getattr(module, "GROUP_OFF_REPRO_COMMAND", "")),
        str(getattr(module, "OPPORTUNITY_REPRO_COMMAND", "")),
    }
    return sum(1 for command in commands if command.startswith("manual_oneoff"))


def build_payload(repo_root: Path, rows: list[dict[str, object]]) -> dict[str, object]:
    module = load_module(repo_root / SOURCE_BUILDER_PATH)
    artifact_specs = getattr(module, "ARTIFACT_SPECS", [])
    if not isinstance(artifact_specs, list):
        raise SystemExit("evidence manifest builder does not expose ARTIFACT_SPECS list")
    literal_role_counts = Counter(str(row["literal_role"]) for row in rows)
    source_counts = Counter(str(row["source_constant"]) for row in rows)
    mode_counts = Counter(str(row["command_repro_mode"]) for row in rows)
    refresh_bucket_counts = Counter(str(row["refresh_bucket"]) for row in rows)
    replacement_kind_counts = Counter(str(row["replacement_kind"]) for row in rows)
    apply_status_counts = Counter(str(row["literal_apply_status"]) for row in rows)

    unique_old_commands = {str(row["source_constant"]): str(row["old_repro_command"]) for row in rows}
    unique_proposed_commands = {
        str(row["source_constant"]): str(row["proposed_repro_command"]) for row in rows
    }
    old_private_literals = sum(private_tmp_count(command) for command in unique_old_commands.values())
    proposed_private_literals = sum(
        private_tmp_count(command) for command in unique_proposed_commands.values()
    )
    runtime_specs = sum(1 for spec in artifact_specs if spec.get("repro_mode") == "runtime_run")
    builder_specs = sum(1 for spec in artifact_specs if spec.get("repro_mode") == "builder")
    manual_specs = sum(1 for spec in artifact_specs if spec.get("repro_mode") == "manual_oneoff")

    manual_allowed = sum(int(row["manual_literal_edit_allowed"]) for row in rows)
    runtime_allowed = sum(int(row["runtime_semantic_change_allowed_rows"]) for row in rows)
    operator_allowed = sum(int(row["operator_facing_change_allowed_rows"]) for row in rows)

    return {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_builder_path": SOURCE_BUILDER_PATH,
        "plan_literal_rows": len(rows),
        "command_group_rows": len(unique_old_commands),
        "artifact_specs_rows": len(artifact_specs),
        "runtime_artifact_specs_rows": runtime_specs,
        "builder_artifact_specs_rows": builder_specs,
        "manual_oneoff_artifact_specs_rows": manual_specs,
        "manual_oneoff_command_rows_preserved": manual_oneoff_command_count(module),
        "old_private_tmp_literal_rows": old_private_literals,
        "proposed_private_tmp_literal_rows": proposed_private_literals,
        "runtime_output_root_literal_rows": literal_role_counts.get("runtime_output_root", 0),
        "sidecar_result_root_literal_rows": literal_role_counts.get("sidecar_result_root", 0),
        "sidecar_output_dir_literal_rows": literal_role_counts.get("sidecar_output_dir", 0),
        "pending_replacement_literal_rows": apply_status_counts.get("pending_replacement", 0),
        "already_applied_literal_rows": apply_status_counts.get("already_applied", 0),
        "manual_literal_edit_allowed_rows": manual_allowed,
        "runtime_semantic_change_allowed_rows": runtime_allowed,
        "operator_facing_change_allowed_rows": operator_allowed,
        "plan_complete": int(
            len(rows) == 7
            and len(unique_old_commands) == 4
            and old_private_literals in {0, 7}
            and proposed_private_literals == 0
            and runtime_specs == 14
            and builder_specs == 6
            and manual_specs == 3
            and apply_status_counts.get("pending_replacement", 0)
            + apply_status_counts.get("already_applied", 0)
            == 7
            and manual_allowed == 0
            and runtime_allowed == 0
            and operator_allowed == 0
        ),
        "closure_complete": int(
            len(rows) == 7
            and len(unique_old_commands) == 4
            and old_private_literals == 0
            and proposed_private_literals == 0
            and apply_status_counts.get("already_applied", 0) == 7
            and manual_allowed == 0
            and runtime_allowed == 0
            and operator_allowed == 0
        ),
        "literal_role_counts": dict(sorted(literal_role_counts.items())),
        "source_constant_counts": dict(sorted(source_counts.items())),
        "command_repro_mode_counts": dict(sorted(mode_counts.items())),
        "refresh_bucket_counts": dict(sorted(refresh_bucket_counts.items())),
        "replacement_kind_counts": dict(sorted(replacement_kind_counts.items())),
        "literal_apply_status_counts": dict(sorted(apply_status_counts.items())),
        "recommended_next_branch": "evidence_manifest_repro_refresh_dry_run",
    }


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scalar_keys = [
        "plan_literal_rows",
        "command_group_rows",
        "artifact_specs_rows",
        "runtime_artifact_specs_rows",
        "builder_artifact_specs_rows",
        "manual_oneoff_artifact_specs_rows",
        "manual_oneoff_command_rows_preserved",
        "old_private_tmp_literal_rows",
        "proposed_private_tmp_literal_rows",
        "runtime_output_root_literal_rows",
        "sidecar_result_root_literal_rows",
        "sidecar_output_dir_literal_rows",
        "pending_replacement_literal_rows",
        "already_applied_literal_rows",
        "manual_literal_edit_allowed_rows",
        "runtime_semantic_change_allowed_rows",
        "operator_facing_change_allowed_rows",
        "plan_complete",
        "closure_complete",
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
    for scope_key in [
        "literal_role_counts",
        "source_constant_counts",
        "command_repro_mode_counts",
        "refresh_bucket_counts",
        "replacement_kind_counts",
        "literal_apply_status_counts",
    ]:
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


def render_note(payload: dict[str, object]) -> str:
    return "\n".join(
        [
            "# Evidence Manifest Repro Refresh Plan V1",
            "",
            "## Summary",
            "- Plans the evidence manifest repro-command refresh for the remaining generated handoff lane.",
            "- Maps hard-coded `/private/tmp` repro literals to `${EVIDENCE_MANIFEST_OUTPUT_ROOT}`.",
            "- This is plan-only: it does not edit the source manifest builder, run production jobs, or change runtime semantics.",
            "",
            "## Counts",
            f"- plan_literal_rows: `{payload['plan_literal_rows']}`",
            f"- command_group_rows: `{payload['command_group_rows']}`",
            f"- artifact_specs_rows: `{payload['artifact_specs_rows']}`",
            f"- runtime_artifact_specs_rows: `{payload['runtime_artifact_specs_rows']}`",
            f"- builder_artifact_specs_rows: `{payload['builder_artifact_specs_rows']}`",
            f"- manual_oneoff_artifact_specs_rows: `{payload['manual_oneoff_artifact_specs_rows']}`",
            f"- old_private_tmp_literal_rows: `{payload['old_private_tmp_literal_rows']}`",
            f"- proposed_private_tmp_literal_rows: `{payload['proposed_private_tmp_literal_rows']}`",
            f"- pending_replacement_literal_rows: `{payload['pending_replacement_literal_rows']}`",
            f"- already_applied_literal_rows: `{payload['already_applied_literal_rows']}`",
            f"- manual_literal_edit_allowed_rows: `{payload['manual_literal_edit_allowed_rows']}`",
            f"- runtime_semantic_change_allowed_rows: `{payload['runtime_semantic_change_allowed_rows']}`",
            f"- operator_facing_change_allowed_rows: `{payload['operator_facing_change_allowed_rows']}`",
            f"- plan_complete: `{payload['plan_complete']}`",
            f"- closure_complete: `{payload['closure_complete']}`",
            "",
            "## Replacement Shape",
            f"- Runtime output root: `{RUNTIME_OUTPUT_ROOT}`",
            f"- Shared sidecar result root: `{RUNTIME_RESULT_ROOT}`",
            f"- Sidecar output dirs: `{OUTPUT_ROOT_PLACEHOLDER}/<axis_sidecar>`",
            "- Manual one-off repro rows stay as documented manual scans.",
            "",
            "## Next Decision",
            "- Next safe branch: `evidence_manifest_repro_refresh_dry_run`.",
            "- Generate a dry-run source patch from this plan before applying it to the manifest builder.",
        ]
    ) + "\n"


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = build_detail_rows(repo_root)
    payload = build_payload(repo_root, rows)
    write_csv(output_dir / DETAIL_OUTPUT_NAME, rows, DETAIL_COLUMNS)
    write_csv(output_dir / SUMMARY_OUTPUT_NAME, summary_rows(payload), SUMMARY_COLUMNS)
    (output_dir / NOTE_OUTPUT_NAME).write_text(render_note(payload), encoding="utf-8")
    (output_dir / JSON_OUTPUT_NAME).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote evidence manifest repro refresh plan to {output_dir}")


if __name__ == "__main__":
    main()
