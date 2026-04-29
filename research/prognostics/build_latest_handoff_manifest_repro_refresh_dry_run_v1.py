#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import shlex
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

try:
    from build_latest_handoff_manifest_repro_refresh_plan_v1 import (
        build_detail_rows as build_refresh_plan_rows,
    )
except ImportError:
    from research.prognostics.build_latest_handoff_manifest_repro_refresh_plan_v1 import (
        build_detail_rows as build_refresh_plan_rows,
    )


OWNER_BRANCH = "BR-20260429-230"

DETAIL_OUTPUT_NAME = "latest_handoff_manifest_repro_refresh_dry_run_v1.csv"
SUMMARY_OUTPUT_NAME = "latest_handoff_manifest_repro_refresh_dry_run_summary_v1.csv"
NOTE_OUTPUT_NAME = "latest_handoff_manifest_repro_refresh_dry_run_note_v1.md"
JSON_OUTPUT_NAME = "latest_handoff_manifest_repro_refresh_dry_run_v1.json"
MANIFEST_TEMPLATE_OUTPUT_NAME = (
    "latest_handoff_manifest_repro_refresh_input_manifest_templates_v1.json"
)

LATEST_HANDOFF_PATH = (
    "research/prognostics/build_panel_day_engine_latest_evidence_handoff_manifest_v1.py"
)
OUTPUT_FLAGS = {"--output-dir", "--output-root"}
REPO_ROOT_FLAGS = {"--repo-root"}
TEMP_PREFIXES = ("/private" + "/tmp/", "/tmp/", "/private/var/")
INPUT_MANIFEST_PLACEHOLDER = "${LATEST_HANDOFF_MANIFEST_DIR}"
OUTPUT_ROOT_PLACEHOLDER = "${LATEST_HANDOFF_OUTPUT_ROOT}"
CURRENT_REPO_ROOT_PLACEHOLDER = "$(pwd)"

DETAIL_COLUMNS = [
    "owner_branch",
    "dry_run_id",
    "branch_id",
    "branch_title",
    "evidence_layer",
    "handoff_state",
    "source_script",
    "script_supports_input_manifest",
    "old_repro_command",
    "proposed_repro_command",
    "old_private_tmp_literal_count",
    "proposed_private_tmp_literal_count",
    "temp_input_literal_count",
    "temp_output_literal_count",
    "temp_repo_root_literal_count",
    "input_manifest_added",
    "input_manifest_template_path",
    "input_manifest_keys",
    "removed_input_flags",
    "output_root_parameterized",
    "proposed_output_dir",
    "repo_root_replaced_with_pwd",
    "proposed_primary_artifact_path",
    "command_changed",
    "dry_run_status",
    "runtime_semantic_change_allowed_rows",
    "operator_facing_change_allowed_rows",
    "recommended_next_action",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run replacement repro commands for the latest evidence handoff manifest "
            "using branch-local input manifests and a parameterized output root."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for audit outputs. Required so this dry-run adds no temp default.",
    )
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


def shell_join(tokens: list[str]) -> str:
    return " ".join(shlex.quote(token) for token in tokens)


def safe_id(branch_id: str, branch_title: str) -> str:
    branch_token = branch_id.lower().replace("br-202604", "br")
    text = f"{branch_token}_{branch_title}".lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "latest_handoff_branch"


def flag_to_manifest_key(flag: str) -> str:
    return flag.removeprefix("--").replace("-", "_")


def is_temp_path(value: str) -> bool:
    return value.startswith(TEMP_PREFIXES)


def private_tmp_count(text: str) -> int:
    return text.count("/private" + "/tmp/")


def source_supports_input_manifest(repo_root: Path, command_tokens: list[str]) -> int:
    if len(command_tokens) < 2:
        return 0
    script_path = repo_root / command_tokens[1]
    if not script_path.exists() or not script_path.is_file():
        return 0
    try:
        source = script_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        source = script_path.read_text(encoding="utf-8", errors="replace")
    return int("--input-manifest" in source)


def paired_options(tokens: list[str]) -> list[tuple[int, str, str]]:
    pairs: list[tuple[int, str, str]] = []
    index = 0
    while index < len(tokens) - 1:
        flag = tokens[index]
        value = tokens[index + 1]
        if flag.startswith("--") and not value.startswith("--"):
            pairs.append((index, flag, value))
            index += 2
        else:
            index += 1
    return pairs


def rewrite_command(
    repo_root: Path,
    spec: dict[str, object],
) -> dict[str, object]:
    branch_id = str(spec.get("branch_id", ""))
    branch_title = str(spec.get("branch_title", ""))
    old_command = str(spec.get("repro_command", ""))
    tokens = shlex.split(old_command)
    temp_pairs = [(flag, value) for _index, flag, value in paired_options(tokens) if is_temp_path(value)]
    temp_input_pairs = [
        (flag, value)
        for flag, value in temp_pairs
        if flag not in OUTPUT_FLAGS and flag not in REPO_ROOT_FLAGS
    ]
    temp_output_pairs = [(flag, value) for flag, value in temp_pairs if flag in OUTPUT_FLAGS]
    temp_repo_root_pairs = [(flag, value) for flag, value in temp_pairs if flag in REPO_ROOT_FLAGS]
    script_support = source_supports_input_manifest(repo_root, tokens)
    if not temp_pairs:
        return {
            "owner_branch": OWNER_BRANCH,
            "branch_id": branch_id,
            "branch_title": branch_title,
            "evidence_layer": spec.get("evidence_layer", ""),
            "handoff_state": spec.get("handoff_state", ""),
            "source_script": tokens[1] if len(tokens) > 1 else "",
            "script_supports_input_manifest": script_support,
            "old_repro_command": old_command,
            "proposed_repro_command": old_command,
            "old_private_tmp_literal_count": 0,
            "proposed_private_tmp_literal_count": 0,
            "temp_input_literal_count": 0,
            "temp_output_literal_count": 0,
            "temp_repo_root_literal_count": 0,
            "input_manifest_added": 0,
            "input_manifest_template_path": "",
            "input_manifest_keys": "",
            "input_manifest_inputs": {},
            "removed_input_flags": "",
            "output_root_parameterized": 0,
            "proposed_output_dir": "",
            "repo_root_replaced_with_pwd": 0,
            "proposed_primary_artifact_path": spec.get("primary_artifact_path", ""),
            "command_changed": 0,
            "dry_run_status": "unchanged_repo_doc",
            "runtime_semantic_change_allowed_rows": 0,
            "operator_facing_change_allowed_rows": 0,
            "recommended_next_action": "preserve command; no latest handoff temp literal refresh needed",
        }
    branch_safe_id = safe_id(branch_id, branch_title)
    manifest_path = f"{INPUT_MANIFEST_PLACEHOLDER}/{branch_safe_id}_input_manifest.json"
    proposed_output_dir = f"{OUTPUT_ROOT_PLACEHOLDER}/{branch_safe_id}"
    old_artifact_name = Path(str(spec.get("primary_artifact_path", ""))).name
    proposed_primary_artifact = (
        f"{proposed_output_dir}/{old_artifact_name}" if old_artifact_name else proposed_output_dir
    )

    new_tokens: list[str] = []
    index = 0
    input_manifest_added = 0
    output_replacements = 0
    repo_root_replacements = 0
    removed_input_flags: list[str] = []
    manifest_inputs: dict[str, dict[str, str]] = {}

    while index < len(tokens):
        token = tokens[index]
        next_value = tokens[index + 1] if index + 1 < len(tokens) else ""
        if token.startswith("--") and next_value and not next_value.startswith("--"):
            if is_temp_path(next_value) and token in OUTPUT_FLAGS:
                new_tokens.extend([token, proposed_output_dir])
                output_replacements += 1
                index += 2
                continue
            if is_temp_path(next_value) and token in REPO_ROOT_FLAGS:
                new_tokens.extend([token, CURRENT_REPO_ROOT_PLACEHOLDER])
                repo_root_replacements += 1
                index += 2
                continue
            if is_temp_path(next_value):
                manifest_key = flag_to_manifest_key(token)
                manifest_inputs[manifest_key] = {
                    "path": next_value,
                    "source_flag": token,
                    "source_branch": branch_id,
                }
                removed_input_flags.append(token)
                index += 2
                continue
        new_tokens.append(token)
        index += 1

    if manifest_inputs:
        new_tokens.extend(["--input-manifest", manifest_path])
        input_manifest_added = 1

    proposed_command = shell_join(new_tokens)
    if not old_command:
        status = "manual_review_missing_repro_command"
    elif manifest_inputs and not script_support:
        status = "manual_review_script_lacks_input_manifest"
    elif private_tmp_count(proposed_command) == 0:
        status = "dry_run_replacement_ready"
    else:
        status = "manual_review_temp_literal_remaining"

    if status == "unchanged_repo_doc":
        next_action = "preserve command; no latest handoff temp literal refresh needed"
    elif status == "dry_run_replacement_ready":
        next_action = "compare old/new command text, then patch latest handoff generator in a separate branch"
    else:
        next_action = "inspect before patching latest handoff generator"

    return {
        "owner_branch": OWNER_BRANCH,
        "branch_id": branch_id,
        "branch_title": branch_title,
        "evidence_layer": spec.get("evidence_layer", ""),
        "handoff_state": spec.get("handoff_state", ""),
        "source_script": tokens[1] if len(tokens) > 1 else "",
        "script_supports_input_manifest": script_support,
        "old_repro_command": old_command,
        "proposed_repro_command": proposed_command,
        "old_private_tmp_literal_count": private_tmp_count(old_command),
        "proposed_private_tmp_literal_count": private_tmp_count(proposed_command),
        "temp_input_literal_count": len(temp_input_pairs),
        "temp_output_literal_count": len(temp_output_pairs),
        "temp_repo_root_literal_count": len(temp_repo_root_pairs),
        "input_manifest_added": input_manifest_added,
        "input_manifest_template_path": manifest_path if manifest_inputs else "",
        "input_manifest_keys": "|".join(sorted(manifest_inputs)),
        "input_manifest_inputs": manifest_inputs,
        "removed_input_flags": "|".join(removed_input_flags),
        "output_root_parameterized": int(output_replacements > 0),
        "proposed_output_dir": proposed_output_dir if output_replacements else "",
        "repo_root_replaced_with_pwd": int(repo_root_replacements > 0),
        "proposed_primary_artifact_path": proposed_primary_artifact
        if output_replacements
        else spec.get("primary_artifact_path", ""),
        "command_changed": int(old_command != proposed_command),
        "dry_run_status": status,
        "runtime_semantic_change_allowed_rows": 0,
        "operator_facing_change_allowed_rows": 0,
        "recommended_next_action": next_action,
    }


def load_branch_specs(repo_root: Path) -> list[dict[str, object]]:
    module = load_module(repo_root / LATEST_HANDOFF_PATH)
    branch_specs = getattr(module, "BRANCH_SPECS", None)
    if not isinstance(branch_specs, list):
        raise SystemExit("latest handoff builder does not expose BRANCH_SPECS list")
    for spec in branch_specs:
        if not isinstance(spec, dict):
            raise SystemExit("latest handoff BRANCH_SPECS contains a non-dict row")
    return branch_specs


def build_detail_rows(repo_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, spec in enumerate(load_branch_specs(repo_root), start=1):
        row = rewrite_command(repo_root, spec)
        row["dry_run_id"] = f"BR230-{index:03d}"
        rows.append(row)
    return rows


def build_manifest_templates(rows: list[dict[str, object]]) -> dict[str, object]:
    templates: dict[str, object] = {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "template_policy": "one_input_manifest_per_latest_handoff_branch",
        "branches": {},
    }
    for row in rows:
        inputs = row.get("input_manifest_inputs", {})
        if not isinstance(inputs, dict) or not inputs:
            continue
        templates["branches"][str(row["branch_id"])] = {
            "template_path": row["input_manifest_template_path"],
            "inputs": inputs,
        }
    return templates


def build_payload(rows: list[dict[str, object]], plan_rows: list[dict[str, object]]) -> dict[str, object]:
    status_counts = Counter(str(row["dry_run_status"]) for row in rows)
    layer_counts = Counter(str(row["evidence_layer"]) for row in rows)
    key_to_paths: dict[str, set[str]] = defaultdict(set)
    branch_key_collisions = 0
    for row in rows:
        inputs = row.get("input_manifest_inputs", {})
        if not isinstance(inputs, dict):
            continue
        for key, item in inputs.items():
            if isinstance(item, dict):
                key_to_paths[key].add(str(item.get("path", "")))
    global_manifest_key_conflicts = sum(1 for paths in key_to_paths.values() if len(paths) > 1)
    branch_key_collisions = sum(
        1
        for row in rows
        if isinstance(row.get("input_manifest_inputs"), dict)
        and len(row["input_manifest_inputs"]) != len(str(row.get("input_manifest_keys", "")).split("|"))
        and str(row.get("input_manifest_keys", ""))
    )

    old_temp = sum(int(row["old_private_tmp_literal_count"]) for row in rows)
    new_temp = sum(int(row["proposed_private_tmp_literal_count"]) for row in rows)
    removed_inputs = sum(int(row["temp_input_literal_count"]) for row in rows)
    replaced_outputs = sum(int(row["temp_output_literal_count"]) for row in rows)
    replaced_repo_roots = sum(int(row["temp_repo_root_literal_count"]) for row in rows)
    ready_rows = status_counts.get("dry_run_replacement_ready", 0)
    unchanged_rows = status_counts.get("unchanged_repo_doc", 0)
    manual_review_rows = len(rows) - ready_rows - unchanged_rows
    plan_temp = sum(int(row["repro_temp_literal_count"]) for row in plan_rows)
    plan_refresh_required = sum(
        1 for row in plan_rows if str(row["refresh_bucket"]) != "repo_doc_no_repro_refresh_needed"
    )

    return {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "branch_spec_rows": len(rows),
        "refresh_required_branch_rows": ready_rows,
        "repo_doc_unchanged_branch_rows": unchanged_rows,
        "manual_review_branch_rows": manual_review_rows,
        "old_private_tmp_literal_rows": old_temp,
        "proposed_private_tmp_literal_rows": new_temp,
        "input_manifest_added_rows": sum(int(row["input_manifest_added"]) for row in rows),
        "input_flags_removed_rows": removed_inputs,
        "output_root_parameterized_rows": sum(int(row["output_root_parameterized"]) for row in rows),
        "output_literals_replaced_rows": replaced_outputs,
        "repo_root_replaced_with_pwd_rows": sum(int(row["repo_root_replaced_with_pwd"]) for row in rows),
        "repo_root_literals_replaced_rows": replaced_repo_roots,
        "script_supports_input_manifest_rows": sum(
            int(row["script_supports_input_manifest"]) for row in rows
        ),
        "global_manifest_key_conflict_rows": global_manifest_key_conflicts,
        "branch_manifest_key_collision_rows": branch_key_collisions,
        "plan_repro_temp_literal_rows_from_br229": plan_temp,
        "plan_refresh_required_branch_rows_from_br229": plan_refresh_required,
        "plan_count_match": int(plan_temp == old_temp and plan_refresh_required == ready_rows),
        "dry_run_complete": int(
            len(rows) > 0
            and new_temp == 0
            and manual_review_rows == 0
            and plan_temp == old_temp
            and plan_refresh_required == ready_rows
        ),
        "runtime_semantic_change_allowed_rows": 0,
        "operator_facing_change_allowed_rows": 0,
        "dry_run_status_counts": dict(sorted(status_counts.items())),
        "evidence_layer_counts": dict(sorted(layer_counts.items())),
        "recommended_next_branch": "latest_handoff_manifest_repro_refresh_apply_generator",
    }


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scalar_keys = [
        "branch_spec_rows",
        "refresh_required_branch_rows",
        "repo_doc_unchanged_branch_rows",
        "manual_review_branch_rows",
        "old_private_tmp_literal_rows",
        "proposed_private_tmp_literal_rows",
        "input_manifest_added_rows",
        "input_flags_removed_rows",
        "output_root_parameterized_rows",
        "output_literals_replaced_rows",
        "repo_root_replaced_with_pwd_rows",
        "repo_root_literals_replaced_rows",
        "script_supports_input_manifest_rows",
        "global_manifest_key_conflict_rows",
        "branch_manifest_key_collision_rows",
        "plan_repro_temp_literal_rows_from_br229",
        "plan_refresh_required_branch_rows_from_br229",
        "plan_count_match",
        "dry_run_complete",
        "runtime_semantic_change_allowed_rows",
        "operator_facing_change_allowed_rows",
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
    for scope_key in ["dry_run_status_counts", "evidence_layer_counts"]:
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
            "# Latest Handoff Manifest Repro Refresh Dry Run V1",
            "",
            "## Summary",
            "- Generates old/new repro command comparisons for the latest handoff manifest.",
            "- Uses one branch-local input manifest per refreshed handoff row, not one global manifest.",
            "- Uses one parameterized output root placeholder for all refreshed output destinations.",
            "- This is a dry-run/audit patch only; it does not edit the latest handoff generator.",
            "",
            "## Counts",
            f"- branch_spec_rows: `{payload['branch_spec_rows']}`",
            f"- refresh_required_branch_rows: `{payload['refresh_required_branch_rows']}`",
            f"- repo_doc_unchanged_branch_rows: `{payload['repo_doc_unchanged_branch_rows']}`",
            f"- old_private_tmp_literal_rows: `{payload['old_private_tmp_literal_rows']}`",
            f"- proposed_private_tmp_literal_rows: `{payload['proposed_private_tmp_literal_rows']}`",
            f"- input_manifest_added_rows: `{payload['input_manifest_added_rows']}`",
            f"- input_flags_removed_rows: `{payload['input_flags_removed_rows']}`",
            f"- output_literals_replaced_rows: `{payload['output_literals_replaced_rows']}`",
            f"- repo_root_literals_replaced_rows: `{payload['repo_root_literals_replaced_rows']}`",
            f"- global_manifest_key_conflict_rows: `{payload['global_manifest_key_conflict_rows']}`",
            f"- plan_count_match: `{payload['plan_count_match']}`",
            f"- dry_run_complete: `{payload['dry_run_complete']}`",
            "",
            "## Boundary",
            "- Do not apply these command replacements directly in this branch.",
            "- The next branch should patch the latest handoff generator and compare regenerated manifest rows.",
            "- Keep the branch-local input manifest design because shared keys such as `packet_input` can mean different artifacts across scripts.",
            "- Keep runtime semantics, operator-facing output, and `pv_ae/panel_day_engine.py` unchanged.",
            "",
            "## Next Action",
            f"- Recommended next branch: `{payload['recommended_next_branch']}`.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    rows = build_detail_rows(repo_root)
    plan_rows = build_refresh_plan_rows(repo_root)
    payload = build_payload(rows, plan_rows)
    templates = build_manifest_templates(rows)

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / DETAIL_OUTPUT_NAME, rows, DETAIL_COLUMNS)
    write_csv(output_dir / SUMMARY_OUTPUT_NAME, summary_rows(payload), SUMMARY_COLUMNS)
    (output_dir / NOTE_OUTPUT_NAME).write_text(render_note(payload), encoding="utf-8")
    (output_dir / JSON_OUTPUT_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / MANIFEST_TEMPLATE_OUTPUT_NAME).write_text(
        json.dumps(templates, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
