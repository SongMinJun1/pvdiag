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

import pandas as pd


OWNER_BRANCH = "BR-20260429-231"

DETAIL_OUTPUT_NAME = "latest_handoff_manifest_repro_refresh_apply_check_v1.csv"
SUMMARY_OUTPUT_NAME = "latest_handoff_manifest_repro_refresh_apply_check_summary_v1.csv"
NOTE_OUTPUT_NAME = "latest_handoff_manifest_repro_refresh_apply_check_note_v1.md"
JSON_OUTPUT_NAME = "latest_handoff_manifest_repro_refresh_apply_check_v1.json"

LATEST_HANDOFF_PATH = (
    "research/prognostics/build_panel_day_engine_latest_evidence_handoff_manifest_v1.py"
)
EXPECTED_BRANCH_ROWS = 14
EXPECTED_REFRESHED_ROWS = 12
EXPECTED_REPO_DOC_ROWS = 2
BR230_OLD_REPRO_TEMP_LITERAL_ROWS = 41

DETAIL_COLUMNS = [
    "owner_branch",
    "check_id",
    "branch_id",
    "branch_title",
    "evidence_layer",
    "handoff_state",
    "artifact_location_type",
    "primary_artifact_path",
    "repro_command",
    "repro_private_tmp_literal_count",
    "artifact_private_tmp_literal_count",
    "has_input_manifest",
    "has_latest_handoff_manifest_dir",
    "has_latest_handoff_output_root",
    "has_current_repo_root_pwd",
    "repo_doc_command_preserved",
    "repro_required_if_missing",
    "operator_promotion_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "runtime_semantic_change_allowed_rows",
    "operator_facing_change_allowed_rows",
    "row_status",
    "recommended_next_action",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check that the latest handoff generator has applied the BR-230 repro refresh "
            "dry-run without changing runtime semantics."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for check outputs. Required so this check adds no temp default.",
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


def private_tmp_count(text: object) -> int:
    return str(text).count("/private" + "/tmp/")


def build_detail_rows(repo_root: Path) -> list[dict[str, object]]:
    module = load_module(repo_root / LATEST_HANDOFF_PATH)
    detail = module.build_manifest(repo_root)
    if not isinstance(detail, pd.DataFrame):
        raise SystemExit("latest handoff build_manifest did not return a DataFrame")

    rows: list[dict[str, object]] = []
    for index, row in enumerate(detail.to_dict(orient="records"), start=1):
        branch_id = str(row.get("branch_id", ""))
        repro_command = str(row.get("repro_command", ""))
        artifact_path = str(row.get("primary_artifact_path", ""))
        artifact_location_type = str(row.get("artifact_location_type", ""))
        is_repo_doc = artifact_location_type == "repo"
        repro_temp_count = private_tmp_count(repro_command)
        artifact_temp_count = private_tmp_count(artifact_path)
        has_input_manifest = int("--input-manifest" in repro_command)
        has_manifest_dir = int("LATEST_HANDOFF_MANIFEST_DIR" in repro_command)
        has_output_root = int("LATEST_HANDOFF_OUTPUT_ROOT" in repro_command)
        has_pwd_root = int('"$(pwd)"' in repro_command or "$(pwd)" in repro_command)
        repo_doc_preserved = int(
            is_repo_doc
            and has_input_manifest == 0
            and has_output_root == 0
            and repro_temp_count == 0
        )

        if repro_temp_count or artifact_temp_count:
            row_status = "failed_temp_literal_remaining"
            next_action = "stop and inspect remaining latest handoff temp literal"
        elif is_repo_doc and repo_doc_preserved:
            row_status = "repo_doc_preserved"
            next_action = "keep repo-doc handoff row unchanged"
        elif (
            artifact_location_type == "parameterized"
            and has_input_manifest
            and has_manifest_dir
            and has_output_root
        ):
            row_status = "applied_manifestized_repro"
            next_action = "use regenerated manifest row as refreshed handoff text"
        else:
            row_status = "manual_review"
            next_action = "inspect row before treating refresh as applied"

        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "check_id": f"BR231-{index:03d}",
                "branch_id": branch_id,
                "branch_title": row.get("branch_title", ""),
                "evidence_layer": row.get("evidence_layer", ""),
                "handoff_state": row.get("handoff_state", ""),
                "artifact_location_type": artifact_location_type,
                "primary_artifact_path": artifact_path,
                "repro_command": repro_command,
                "repro_private_tmp_literal_count": repro_temp_count,
                "artifact_private_tmp_literal_count": artifact_temp_count,
                "has_input_manifest": has_input_manifest,
                "has_latest_handoff_manifest_dir": has_manifest_dir,
                "has_latest_handoff_output_root": has_output_root,
                "has_current_repo_root_pwd": has_pwd_root,
                "repo_doc_command_preserved": repo_doc_preserved,
                "repro_required_if_missing": int(row.get("repro_required_if_missing", 0)),
                "operator_promotion_allowed": int(row.get("operator_promotion_allowed", 0)),
                "engine_patch_allowed": int(row.get("engine_patch_allowed", 0)),
                "threshold_patch_allowed": int(row.get("threshold_patch_allowed", 0)),
                "runtime_semantic_change_allowed_rows": 0,
                "operator_facing_change_allowed_rows": 0,
                "row_status": row_status,
                "recommended_next_action": next_action,
            }
        )
    return rows


def build_payload(rows: list[dict[str, object]]) -> dict[str, object]:
    status_counts = Counter(str(row["row_status"]) for row in rows)
    location_counts = Counter(str(row["artifact_location_type"]) for row in rows)
    repro_temp = sum(int(row["repro_private_tmp_literal_count"]) for row in rows)
    artifact_temp = sum(int(row["artifact_private_tmp_literal_count"]) for row in rows)
    refreshed_rows = status_counts.get("applied_manifestized_repro", 0)
    repo_doc_rows = status_counts.get("repo_doc_preserved", 0)
    manual_rows = status_counts.get("manual_review", 0) + status_counts.get(
        "failed_temp_literal_remaining", 0
    )
    operator_allowed = sum(int(row["operator_promotion_allowed"]) for row in rows)
    engine_allowed = sum(int(row["engine_patch_allowed"]) for row in rows)
    threshold_allowed = sum(int(row["threshold_patch_allowed"]) for row in rows)

    return {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "branch_spec_rows": len(rows),
        "applied_manifestized_repro_rows": refreshed_rows,
        "repo_doc_preserved_rows": repo_doc_rows,
        "manual_review_rows": manual_rows,
        "repro_private_tmp_literal_rows": repro_temp,
        "artifact_private_tmp_literal_rows": artifact_temp,
        "br230_old_repro_temp_literal_rows": BR230_OLD_REPRO_TEMP_LITERAL_ROWS,
        "applied_repro_temp_literal_drop_rows": BR230_OLD_REPRO_TEMP_LITERAL_ROWS - repro_temp,
        "input_manifest_command_rows": sum(int(row["has_input_manifest"]) for row in rows),
        "manifest_dir_placeholder_rows": sum(
            int(row["has_latest_handoff_manifest_dir"]) for row in rows
        ),
        "output_root_placeholder_rows": sum(
            int(row["has_latest_handoff_output_root"]) for row in rows
        ),
        "repo_root_pwd_rows": sum(int(row["has_current_repo_root_pwd"]) for row in rows),
        "parameterized_artifact_rows": location_counts.get("parameterized", 0),
        "repo_artifact_rows": location_counts.get("repo", 0),
        "repro_required_if_missing_rows": sum(int(row["repro_required_if_missing"]) for row in rows),
        "operator_promotion_allowed_sum": operator_allowed,
        "engine_patch_allowed_sum": engine_allowed,
        "threshold_patch_allowed_sum": threshold_allowed,
        "runtime_semantic_change_allowed_rows": 0,
        "operator_facing_change_allowed_rows": 0,
        "br230_expectation_match": int(
            len(rows) == EXPECTED_BRANCH_ROWS
            and refreshed_rows == EXPECTED_REFRESHED_ROWS
            and repo_doc_rows == EXPECTED_REPO_DOC_ROWS
            and repro_temp == 0
            and artifact_temp == 0
        ),
        "apply_check_complete": int(
            len(rows) == EXPECTED_BRANCH_ROWS
            and refreshed_rows == EXPECTED_REFRESHED_ROWS
            and repo_doc_rows == EXPECTED_REPO_DOC_ROWS
            and manual_rows == 0
            and repro_temp == 0
            and artifact_temp == 0
            and operator_allowed == 0
            and engine_allowed == 0
            and threshold_allowed == 0
        ),
        "row_status_counts": dict(sorted(status_counts.items())),
        "artifact_location_type_counts": dict(sorted(location_counts.items())),
        "recommended_next_branch": "latest_handoff_manifest_portability_closure_audit",
    }


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scalar_keys = [
        "branch_spec_rows",
        "applied_manifestized_repro_rows",
        "repo_doc_preserved_rows",
        "manual_review_rows",
        "repro_private_tmp_literal_rows",
        "artifact_private_tmp_literal_rows",
        "br230_old_repro_temp_literal_rows",
        "applied_repro_temp_literal_drop_rows",
        "input_manifest_command_rows",
        "manifest_dir_placeholder_rows",
        "output_root_placeholder_rows",
        "repo_root_pwd_rows",
        "parameterized_artifact_rows",
        "repo_artifact_rows",
        "repro_required_if_missing_rows",
        "operator_promotion_allowed_sum",
        "engine_patch_allowed_sum",
        "threshold_patch_allowed_sum",
        "runtime_semantic_change_allowed_rows",
        "operator_facing_change_allowed_rows",
        "br230_expectation_match",
        "apply_check_complete",
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
    for scope_key in ["row_status_counts", "artifact_location_type_counts"]:
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
            "# Latest Handoff Manifest Repro Refresh Apply Check V1",
            "",
            "## Summary",
            "- Checks that the latest handoff generator now emits portable repro text.",
            "- Confirms BR-230 dry-run expectations against regenerated manifest rows.",
            "- This check does not execute evidence builders and does not change runtime semantics.",
            "",
            "## Counts",
            f"- branch_spec_rows: `{payload['branch_spec_rows']}`",
            f"- applied_manifestized_repro_rows: `{payload['applied_manifestized_repro_rows']}`",
            f"- repo_doc_preserved_rows: `{payload['repo_doc_preserved_rows']}`",
            f"- repro_private_tmp_literal_rows: `{payload['repro_private_tmp_literal_rows']}`",
            f"- artifact_private_tmp_literal_rows: `{payload['artifact_private_tmp_literal_rows']}`",
            f"- applied_repro_temp_literal_drop_rows: `{payload['applied_repro_temp_literal_drop_rows']}`",
            f"- input_manifest_command_rows: `{payload['input_manifest_command_rows']}`",
            f"- output_root_placeholder_rows: `{payload['output_root_placeholder_rows']}`",
            f"- repo_root_pwd_rows: `{payload['repo_root_pwd_rows']}`",
            f"- br230_expectation_match: `{payload['br230_expectation_match']}`",
            f"- apply_check_complete: `{payload['apply_check_complete']}`",
            "",
            "## Boundary",
            "- This is a handoff-generator portability check only.",
            "- Runtime semantics, threshold semantics, and operator-facing verdicts remain unchanged.",
            "- The next branch should run a broader portability closure audit on generated latest handoff outputs.",
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
    payload = build_payload(rows)

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / DETAIL_OUTPUT_NAME, rows, DETAIL_COLUMNS)
    write_csv(output_dir / SUMMARY_OUTPUT_NAME, summary_rows(payload), SUMMARY_COLUMNS)
    (output_dir / NOTE_OUTPUT_NAME).write_text(render_note(payload), encoding="utf-8")
    (output_dir / JSON_OUTPUT_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
