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

try:
    from build_evidence_manifest_repro_refresh_plan_v1 import (
        OUTPUT_ROOT_PLACEHOLDER,
        SOURCE_BUILDER_PATH,
        build_detail_rows as build_plan_rows,
        private_tmp_count,
    )
except ImportError:
    from research.prognostics.build_evidence_manifest_repro_refresh_plan_v1 import (
        OUTPUT_ROOT_PLACEHOLDER,
        SOURCE_BUILDER_PATH,
        build_detail_rows as build_plan_rows,
        private_tmp_count,
    )


OWNER_BRANCH = "BR-20260429-235"

DETAIL_OUTPUT_NAME = "evidence_manifest_repro_refresh_dry_run_v1.csv"
SUMMARY_OUTPUT_NAME = "evidence_manifest_repro_refresh_dry_run_summary_v1.csv"
NOTE_OUTPUT_NAME = "evidence_manifest_repro_refresh_dry_run_note_v1.md"
JSON_OUTPUT_NAME = "evidence_manifest_repro_refresh_dry_run_v1.json"
SOURCE_PATCH_PLAN_OUTPUT_NAME = "evidence_manifest_repro_refresh_source_patch_plan_v1.csv"

DETAIL_COLUMNS = [
    "owner_branch",
    "dry_run_id",
    "evidence_family",
    "judgment_role",
    "artifact_name",
    "artifact_kind",
    "source_root_label",
    "repro_mode",
    "source_constant",
    "old_repro_command",
    "proposed_repro_command",
    "old_private_tmp_literal_count",
    "proposed_private_tmp_literal_count",
    "command_changed",
    "placeholder_root_used",
    "dry_run_status",
    "manual_literal_edit_allowed",
    "runtime_semantic_change_allowed_rows",
    "operator_facing_change_allowed_rows",
    "recommended_next_action",
]

PATCH_PLAN_COLUMNS = [
    "owner_branch",
    "patch_plan_id",
    "source_constant",
    "old_repro_command",
    "proposed_repro_command",
    "old_private_tmp_literal_count",
    "proposed_private_tmp_literal_count",
    "artifact_spec_rows_using_command",
    "source_patch_required",
    "manual_literal_edit_allowed",
    "runtime_semantic_change_allowed_rows",
    "operator_facing_change_allowed_rows",
    "recommended_next_action",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run the evidence manifest repro-command refresh planned in BR-234. "
            "This compares artifact-spec repro rows before applying any source builder patch."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for dry-run outputs. Required so this dry-run adds no temp default.",
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


def command_lookup_from_plan(plan_rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    lookup: dict[str, dict[str, object]] = {}
    for row in plan_rows:
        source_constant = str(row["source_constant"])
        if source_constant not in lookup:
            lookup[source_constant] = row
            continue
        if str(lookup[source_constant]["proposed_repro_command"]) != str(row["proposed_repro_command"]):
            raise SystemExit(f"inconsistent proposed command for {source_constant}")
    return lookup


def old_command_to_source_constant(command_rows: dict[str, dict[str, object]]) -> dict[str, str]:
    return {
        str(row["old_repro_command"]): source_constant
        for source_constant, row in command_rows.items()
    }


def source_patch_plan_rows(command_rows: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, (source_constant, row) in enumerate(sorted(command_rows.items()), start=1):
        old_command = str(row["old_repro_command"])
        proposed_command = str(row["proposed_repro_command"])
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "patch_plan_id": f"BR235-PATCH-{index:03d}",
                "source_constant": source_constant,
                "old_repro_command": old_command,
                "proposed_repro_command": proposed_command,
                "old_private_tmp_literal_count": private_tmp_count(old_command),
                "proposed_private_tmp_literal_count": private_tmp_count(proposed_command),
                "artifact_spec_rows_using_command": row["artifact_spec_rows_using_command"],
                "source_patch_required": int(old_command != proposed_command),
                "manual_literal_edit_allowed": 0,
                "runtime_semantic_change_allowed_rows": 0,
                "operator_facing_change_allowed_rows": 0,
                "recommended_next_action": (
                    "apply this source-constant replacement in the next branch, then regenerate "
                    "the evidence manifest and re-scan generated handoff literals"
                ),
            }
        )
    return rows


def build_detail_rows(repo_root: Path) -> list[dict[str, object]]:
    module = load_module(repo_root / SOURCE_BUILDER_PATH)
    artifact_specs = getattr(module, "ARTIFACT_SPECS", [])
    if not isinstance(artifact_specs, list):
        raise SystemExit("evidence manifest builder does not expose ARTIFACT_SPECS list")

    command_rows = command_lookup_from_plan(build_plan_rows(repo_root))
    old_to_constant = old_command_to_source_constant(command_rows)
    rows: list[dict[str, object]] = []
    for index, spec in enumerate(artifact_specs, start=1):
        if not isinstance(spec, dict):
            raise SystemExit("evidence manifest ARTIFACT_SPECS contains a non-dict row")
        old_command = str(spec.get("repro_command", ""))
        source_constant = old_to_constant.get(old_command, "")
        proposed_command = (
            str(command_rows[source_constant]["proposed_repro_command"])
            if source_constant
            else old_command
        )
        command_changed = int(old_command != proposed_command)
        proposed_private = private_tmp_count(proposed_command)
        if command_changed and proposed_private == 0:
            status = "dry_run_replacement_ready"
            next_action = "apply source command replacement in the next branch"
        elif command_changed:
            status = "manual_review_temp_literal_remaining"
            next_action = "stop and inspect proposed command before applying source patch"
        elif OUTPUT_ROOT_PLACEHOLDER in proposed_command:
            status = "applied_parameterized_repro"
            next_action = "regenerate the evidence manifest and re-run generated handoff literal rescan"
        else:
            status = "preserved_manual_or_repo_repro"
            next_action = "preserve command"
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "dry_run_id": f"BR235-{index:03d}",
                "evidence_family": spec.get("evidence_family", ""),
                "judgment_role": spec.get("judgment_role", ""),
                "artifact_name": Path(str(spec.get("relative_path", ""))).name,
                "artifact_kind": spec.get("artifact_kind", ""),
                "source_root_label": spec.get("root_key", ""),
                "repro_mode": spec.get("repro_mode", ""),
                "source_constant": source_constant,
                "old_repro_command": old_command,
                "proposed_repro_command": proposed_command,
                "old_private_tmp_literal_count": private_tmp_count(old_command),
                "proposed_private_tmp_literal_count": proposed_private,
                "command_changed": command_changed,
                "placeholder_root_used": int(OUTPUT_ROOT_PLACEHOLDER in proposed_command),
                "dry_run_status": status,
                "manual_literal_edit_allowed": 0,
                "runtime_semantic_change_allowed_rows": 0,
                "operator_facing_change_allowed_rows": 0,
                "recommended_next_action": next_action,
            }
        )
    return rows


def build_payload(repo_root: Path, detail_rows: list[dict[str, object]]) -> dict[str, object]:
    command_rows = command_lookup_from_plan(build_plan_rows(repo_root))
    patch_rows = source_patch_plan_rows(command_rows)
    family_counts = Counter(str(row["evidence_family"]) for row in detail_rows)
    mode_counts = Counter(str(row["repro_mode"]) for row in detail_rows)
    status_counts = Counter(str(row["dry_run_status"]) for row in detail_rows)
    source_counts = Counter(str(row["source_constant"]) for row in detail_rows if row["source_constant"])

    artifact_row_old_literals = sum(int(row["old_private_tmp_literal_count"]) for row in detail_rows)
    artifact_row_proposed_literals = sum(
        int(row["proposed_private_tmp_literal_count"]) for row in detail_rows
    )
    unique_old_literals = sum(int(row["old_private_tmp_literal_count"]) for row in patch_rows)
    unique_proposed_literals = sum(
        int(row["proposed_private_tmp_literal_count"]) for row in patch_rows
    )
    changed_rows = sum(int(row["command_changed"]) for row in detail_rows)
    placeholder_rows = sum(int(row["placeholder_root_used"]) for row in detail_rows)
    manual_allowed = sum(int(row["manual_literal_edit_allowed"]) for row in detail_rows)
    runtime_allowed = sum(int(row["runtime_semantic_change_allowed_rows"]) for row in detail_rows)
    operator_allowed = sum(int(row["operator_facing_change_allowed_rows"]) for row in detail_rows)
    source_patch_required_rows = sum(int(row["source_patch_required"]) for row in patch_rows)
    applied_parameterized_rows = status_counts.get("applied_parameterized_repro", 0)
    source_patch_already_applied_rows = sum(
        1
        for row in patch_rows
        if int(row["source_patch_required"]) == 0
        and OUTPUT_ROOT_PLACEHOLDER in str(row["proposed_repro_command"])
    )

    return {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_builder_path": SOURCE_BUILDER_PATH,
        "artifact_spec_rows": len(detail_rows),
        "changed_artifact_spec_rows": changed_rows,
        "unchanged_artifact_spec_rows": len(detail_rows) - changed_rows,
        "runtime_artifact_spec_rows": mode_counts.get("runtime_run", 0),
        "builder_artifact_spec_rows": mode_counts.get("builder", 0),
        "manual_oneoff_artifact_spec_rows": mode_counts.get("manual_oneoff", 0),
        "placeholder_root_used_artifact_rows": placeholder_rows,
        "applied_parameterized_artifact_rows": applied_parameterized_rows,
        "unique_source_command_rows": len(patch_rows),
        "source_patch_required_command_rows": source_patch_required_rows,
        "source_patch_already_applied_command_rows": source_patch_already_applied_rows,
        "artifact_row_old_private_tmp_literal_rows": artifact_row_old_literals,
        "artifact_row_proposed_private_tmp_literal_rows": artifact_row_proposed_literals,
        "unique_command_old_private_tmp_literal_rows": unique_old_literals,
        "unique_command_proposed_private_tmp_literal_rows": unique_proposed_literals,
        "manual_literal_edit_allowed_rows": manual_allowed,
        "runtime_semantic_change_allowed_rows": runtime_allowed,
        "operator_facing_change_allowed_rows": operator_allowed,
        "dry_run_complete": int(
            len(detail_rows) == 23
            and mode_counts.get("runtime_run", 0) == 14
            and mode_counts.get("builder", 0) == 6
            and mode_counts.get("manual_oneoff", 0) == 3
            and placeholder_rows == 20
            and len(patch_rows) == 4
            and source_patch_required_rows in {0, 4}
            and artifact_row_old_literals in {0, 26}
            and artifact_row_proposed_literals == 0
            and unique_old_literals in {0, 7}
            and unique_proposed_literals == 0
            and manual_allowed == 0
            and runtime_allowed == 0
            and operator_allowed == 0
        ),
        "closure_complete": int(
            len(detail_rows) == 23
            and changed_rows == 0
            and applied_parameterized_rows == 20
            and mode_counts.get("manual_oneoff", 0) == 3
            and len(patch_rows) == 4
            and source_patch_required_rows == 0
            and source_patch_already_applied_rows == 4
            and artifact_row_old_literals == 0
            and artifact_row_proposed_literals == 0
            and unique_old_literals == 0
            and unique_proposed_literals == 0
            and manual_allowed == 0
            and runtime_allowed == 0
            and operator_allowed == 0
        ),
        "evidence_family_counts": dict(sorted(family_counts.items())),
        "repro_mode_counts": dict(sorted(mode_counts.items())),
        "dry_run_status_counts": dict(sorted(status_counts.items())),
        "source_constant_counts": dict(sorted(source_counts.items())),
        "recommended_next_branch": "evidence_manifest_repro_refresh_apply_builder",
    }


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scalar_keys = [
        "artifact_spec_rows",
        "changed_artifact_spec_rows",
        "unchanged_artifact_spec_rows",
        "runtime_artifact_spec_rows",
        "builder_artifact_spec_rows",
        "manual_oneoff_artifact_spec_rows",
        "placeholder_root_used_artifact_rows",
        "applied_parameterized_artifact_rows",
        "unique_source_command_rows",
        "source_patch_required_command_rows",
        "source_patch_already_applied_command_rows",
        "artifact_row_old_private_tmp_literal_rows",
        "artifact_row_proposed_private_tmp_literal_rows",
        "unique_command_old_private_tmp_literal_rows",
        "unique_command_proposed_private_tmp_literal_rows",
        "manual_literal_edit_allowed_rows",
        "runtime_semantic_change_allowed_rows",
        "operator_facing_change_allowed_rows",
        "dry_run_complete",
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
        "evidence_family_counts",
        "repro_mode_counts",
        "dry_run_status_counts",
        "source_constant_counts",
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
            "# Evidence Manifest Repro Refresh Dry-Run V1",
            "",
            "## Summary",
            "- Dry-runs the BR-234 evidence manifest repro-command replacement plan.",
            "- Compares artifact-spec repro rows before applying a source builder patch.",
            "- This is dry-run only: it does not edit the source builder, run production jobs, or change runtime semantics.",
            "",
            "## Counts",
            f"- artifact_spec_rows: `{payload['artifact_spec_rows']}`",
            f"- changed_artifact_spec_rows: `{payload['changed_artifact_spec_rows']}`",
            f"- unchanged_artifact_spec_rows: `{payload['unchanged_artifact_spec_rows']}`",
            f"- runtime_artifact_spec_rows: `{payload['runtime_artifact_spec_rows']}`",
            f"- builder_artifact_spec_rows: `{payload['builder_artifact_spec_rows']}`",
            f"- manual_oneoff_artifact_spec_rows: `{payload['manual_oneoff_artifact_spec_rows']}`",
            f"- placeholder_root_used_artifact_rows: `{payload['placeholder_root_used_artifact_rows']}`",
            f"- applied_parameterized_artifact_rows: `{payload['applied_parameterized_artifact_rows']}`",
            f"- artifact_row_old_private_tmp_literal_rows: `{payload['artifact_row_old_private_tmp_literal_rows']}`",
            f"- artifact_row_proposed_private_tmp_literal_rows: `{payload['artifact_row_proposed_private_tmp_literal_rows']}`",
            f"- unique_command_old_private_tmp_literal_rows: `{payload['unique_command_old_private_tmp_literal_rows']}`",
            f"- unique_command_proposed_private_tmp_literal_rows: `{payload['unique_command_proposed_private_tmp_literal_rows']}`",
            f"- source_patch_required_command_rows: `{payload['source_patch_required_command_rows']}`",
            f"- source_patch_already_applied_command_rows: `{payload['source_patch_already_applied_command_rows']}`",
            f"- manual_literal_edit_allowed_rows: `{payload['manual_literal_edit_allowed_rows']}`",
            f"- runtime_semantic_change_allowed_rows: `{payload['runtime_semantic_change_allowed_rows']}`",
            f"- operator_facing_change_allowed_rows: `{payload['operator_facing_change_allowed_rows']}`",
            f"- dry_run_complete: `{payload['dry_run_complete']}`",
            f"- closure_complete: `{payload['closure_complete']}`",
            "",
            "## Boundary",
            "- The source patch should replace only the four repro command constants when pending.",
            "- `ARTIFACT_SPECS` rows should inherit the updated constants automatically.",
            "- Manual one-off repro commands remain preserved.",
            "",
            "## Next Decision",
            "- Next safe branch: `evidence_manifest_repro_refresh_apply_builder`.",
            "- After applying the builder patch, regenerate the manifest and re-run the generated handoff literal rescan.",
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

    detail_rows = build_detail_rows(repo_root)
    command_rows = command_lookup_from_plan(build_plan_rows(repo_root))
    patch_rows = source_patch_plan_rows(command_rows)
    payload = build_payload(repo_root, detail_rows)

    write_csv(output_dir / DETAIL_OUTPUT_NAME, detail_rows, DETAIL_COLUMNS)
    write_csv(output_dir / SOURCE_PATCH_PLAN_OUTPUT_NAME, patch_rows, PATCH_PLAN_COLUMNS)
    write_csv(output_dir / SUMMARY_OUTPUT_NAME, summary_rows(payload), SUMMARY_COLUMNS)
    (output_dir / NOTE_OUTPUT_NAME).write_text(render_note(payload), encoding="utf-8")
    (output_dir / JSON_OUTPUT_NAME).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote evidence manifest repro refresh dry-run to {output_dir}")


if __name__ == "__main__":
    main()
