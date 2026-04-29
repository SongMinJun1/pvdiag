#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260429-232"

DETAIL_OUTPUT_NAME = "latest_handoff_manifest_portability_closure_audit_v1.csv"
SUMMARY_OUTPUT_NAME = "latest_handoff_manifest_portability_closure_audit_summary_v1.csv"
NOTE_OUTPUT_NAME = "latest_handoff_manifest_portability_closure_audit_note_v1.md"
JSON_OUTPUT_NAME = "latest_handoff_manifest_portability_closure_audit_v1.json"

LATEST_HANDOFF_BUILDER = (
    "research/prognostics/build_panel_day_engine_latest_evidence_handoff_manifest_v1.py"
)
GENERATED_DIR_NAME = "_generated_latest_handoff_manifest"
GENERATED_DETAIL_NAME = "panel_day_engine_latest_evidence_handoff_manifest_v1.csv"
GENERATED_SUMMARY_NAME = "panel_day_engine_latest_evidence_handoff_manifest_summary_v1.csv"
GENERATED_NOTE_NAME = "panel_day_engine_latest_evidence_handoff_manifest_note_v1.md"
GENERATED_JSON_NAME = "panel_day_engine_latest_evidence_handoff_manifest_v1.json"

EXPECTED_BRANCH_ROWS = 14
EXPECTED_PARAMETERIZED_ROWS = 12
EXPECTED_REPO_DOC_ROWS = 2
EXPECTED_TEMP_LITERAL_DROP_ROWS = 41

DETAIL_COLUMNS = [
    "owner_branch",
    "check_id",
    "branch_id",
    "branch_title",
    "evidence_layer",
    "handoff_state",
    "artifact_location_type",
    "primary_artifact_kind",
    "primary_doc_exists",
    "primary_artifact_exists",
    "repro_required_if_missing",
    "primary_artifact_path",
    "repro_command",
    "repro_private_tmp_literal_count",
    "artifact_private_tmp_literal_count",
    "has_input_manifest",
    "has_manifest_dir_placeholder",
    "has_output_root_placeholder_in_repro",
    "artifact_uses_output_root_placeholder",
    "repo_doc_preserved",
    "parameterized_manifestized",
    "patch_authorization_sum",
    "closure_status",
    "recommended_next_action",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate the latest evidence handoff manifest and verify that the emitted "
            "handoff/repro text is portable after BR-231."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for closure-audit outputs. Required to avoid hidden temp defaults.",
    )
    return parser.parse_args()


def private_tmp_count(text: object) -> int:
    return str(text).count("/private" + "/tmp/")


def run_latest_handoff_builder(repo_root: Path, output_dir: Path) -> Path:
    generated_dir = output_dir / GENERATED_DIR_NAME
    generated_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            str(repo_root / LATEST_HANDOFF_BUILDER),
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(generated_dir),
            "--owner-branch",
            OWNER_BRANCH,
        ],
        cwd=repo_root,
        check=True,
    )
    return generated_dir


def load_generated(generated_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object], str]:
    detail_path = generated_dir / GENERATED_DETAIL_NAME
    summary_path = generated_dir / GENERATED_SUMMARY_NAME
    json_path = generated_dir / GENERATED_JSON_NAME
    note_path = generated_dir / GENERATED_NOTE_NAME
    for path in [detail_path, summary_path, json_path, note_path]:
        if not path.exists():
            raise SystemExit(f"missing generated latest handoff output: {path}")
    return (
        pd.read_csv(detail_path),
        pd.read_csv(summary_path),
        json.loads(json_path.read_text(encoding="utf-8")),
        note_path.read_text(encoding="utf-8"),
    )


def build_detail_rows(detail: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, row in enumerate(detail.to_dict(orient="records"), start=1):
        artifact_location_type = str(row.get("artifact_location_type", ""))
        artifact_kind = str(row.get("primary_artifact_kind", ""))
        artifact_path = str(row.get("primary_artifact_path", ""))
        repro_command = str(row.get("repro_command", ""))
        repro_temp_count = private_tmp_count(repro_command)
        artifact_temp_count = private_tmp_count(artifact_path)
        has_input_manifest = int("--input-manifest" in repro_command)
        has_manifest_dir = int("LATEST_HANDOFF_MANIFEST_DIR" in repro_command)
        has_output_root_repro = int("LATEST_HANDOFF_OUTPUT_ROOT" in repro_command)
        artifact_uses_output_root = int(artifact_path.startswith("${LATEST_HANDOFF_OUTPUT_ROOT}/"))
        primary_doc_exists = int(row.get("primary_doc_exists", 0))
        primary_artifact_exists = int(row.get("primary_artifact_exists", 0))
        repro_required = int(row.get("repro_required_if_missing", 0))
        patch_authorization_sum = sum(
            int(row.get(column, 0))
            for column in [
                "operator_promotion_allowed",
                "engine_patch_allowed",
                "threshold_patch_allowed",
                "stable_contract_change_allowed",
                "release_regeneration_allowed",
            ]
        )

        repo_doc_preserved = int(
            artifact_location_type == "repo"
            and artifact_kind == "repo_doc"
            and primary_doc_exists == 1
            and primary_artifact_exists == 1
            and repro_required == 0
            and has_input_manifest == 0
            and has_output_root_repro == 0
            and repro_temp_count == 0
            and artifact_temp_count == 0
        )
        parameterized_manifestized = int(
            artifact_location_type == "parameterized"
            and repro_required == 1
            and has_input_manifest == 1
            and has_manifest_dir == 1
            and has_output_root_repro == 1
            and artifact_uses_output_root == 1
            and repro_temp_count == 0
            and artifact_temp_count == 0
        )

        if patch_authorization_sum:
            closure_status = "failed_patch_authorization"
            next_action = "stop; generated handoff row unexpectedly permits production change"
        elif repo_doc_preserved:
            closure_status = "closed_repo_doc_preserved"
            next_action = "keep repo-doc row unchanged"
        elif parameterized_manifestized:
            closure_status = "closed_parameterized_manifestized"
            next_action = "use generated portable handoff row"
        else:
            closure_status = "needs_review"
            next_action = "inspect generated handoff row before closure"

        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "check_id": f"BR232-{index:03d}",
                "branch_id": row.get("branch_id", ""),
                "branch_title": row.get("branch_title", ""),
                "evidence_layer": row.get("evidence_layer", ""),
                "handoff_state": row.get("handoff_state", ""),
                "artifact_location_type": artifact_location_type,
                "primary_artifact_kind": artifact_kind,
                "primary_doc_exists": primary_doc_exists,
                "primary_artifact_exists": primary_artifact_exists,
                "repro_required_if_missing": repro_required,
                "primary_artifact_path": artifact_path,
                "repro_command": repro_command,
                "repro_private_tmp_literal_count": repro_temp_count,
                "artifact_private_tmp_literal_count": artifact_temp_count,
                "has_input_manifest": has_input_manifest,
                "has_manifest_dir_placeholder": has_manifest_dir,
                "has_output_root_placeholder_in_repro": has_output_root_repro,
                "artifact_uses_output_root_placeholder": artifact_uses_output_root,
                "repo_doc_preserved": repo_doc_preserved,
                "parameterized_manifestized": parameterized_manifestized,
                "patch_authorization_sum": patch_authorization_sum,
                "closure_status": closure_status,
                "recommended_next_action": next_action,
            }
        )
    return rows


def build_payload(
    rows: list[dict[str, object]],
    generated_summary: pd.DataFrame,
    generated_payload: dict[str, object],
    generated_note: str,
) -> dict[str, object]:
    status_counts = Counter(str(row["closure_status"]) for row in rows)
    location_counts = Counter(str(row["artifact_location_type"]) for row in rows)
    closure_fail = sum(1 for row in rows if not str(row["closure_status"]).startswith("closed_"))
    repro_temp = sum(int(row["repro_private_tmp_literal_count"]) for row in rows)
    artifact_temp = sum(int(row["artifact_private_tmp_literal_count"]) for row in rows)
    patch_auth = sum(int(row["patch_authorization_sum"]) for row in rows)

    parameterized_rows = location_counts.get("parameterized", 0)
    repo_doc_rows = location_counts.get("repo", 0)
    parameterized_manifestized = sum(int(row["parameterized_manifestized"]) for row in rows)
    repo_doc_preserved = sum(int(row["repo_doc_preserved"]) for row in rows)

    return {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generated_manifest_detail_rows": len(rows),
        "generated_manifest_summary_rows": int(len(generated_summary)),
        "parameterized_rows": parameterized_rows,
        "repo_doc_rows": repo_doc_rows,
        "parameterized_manifestized_rows": parameterized_manifestized,
        "repo_doc_preserved_rows": repo_doc_preserved,
        "closure_pass_count": len(rows) - closure_fail,
        "closure_fail_count": closure_fail,
        "repro_private_tmp_literal_rows": repro_temp,
        "artifact_private_tmp_literal_rows": artifact_temp,
        "input_manifest_rows": sum(int(row["has_input_manifest"]) for row in rows),
        "manifest_dir_placeholder_rows": sum(
            int(row["has_manifest_dir_placeholder"]) for row in rows
        ),
        "output_root_repro_rows": sum(
            int(row["has_output_root_placeholder_in_repro"]) for row in rows
        ),
        "output_root_artifact_rows": sum(
            int(row["artifact_uses_output_root_placeholder"]) for row in rows
        ),
        "repro_required_if_missing_rows": sum(
            int(row["repro_required_if_missing"]) for row in rows
        ),
        "primary_doc_missing_rows": sum(1 - int(row["primary_doc_exists"]) for row in rows),
        "patch_authorization_sum": patch_auth,
        "runtime_semantic_change_allowed_rows": 0,
        "operator_facing_change_allowed_rows": 0,
        "generator_json_branch_count": int(generated_payload.get("branch_count", -1)),
        "generator_json_temp_artifact_missing_count": int(
            generated_payload.get("temp_artifact_missing_count", -1)
        ),
        "generator_json_repo_doc_missing_count": int(
            generated_payload.get("repo_doc_missing_count", -1)
        ),
        "generator_json_engine_patch_allowed_sum": int(
            generated_payload.get("engine_patch_allowed_sum", -1)
        ),
        "generator_json_threshold_patch_allowed_sum": int(
            generated_payload.get("threshold_patch_allowed_sum", -1)
        ),
        "generator_json_operator_promotion_allowed_sum": int(
            generated_payload.get("operator_promotion_allowed_sum", -1)
        ),
        "generated_note_private_tmp_legacy_phrase_count": generated_note.count("Missing `/private/tmp`"),
        "generated_note_parameterized_phrase_count": generated_note.count(
            "Missing parameterized/temp artifacts"
        ),
        "expected_temp_literal_drop_rows": EXPECTED_TEMP_LITERAL_DROP_ROWS,
        "closure_complete": int(
            len(rows) == EXPECTED_BRANCH_ROWS
            and parameterized_rows == EXPECTED_PARAMETERIZED_ROWS
            and repo_doc_rows == EXPECTED_REPO_DOC_ROWS
            and parameterized_manifestized == EXPECTED_PARAMETERIZED_ROWS
            and repo_doc_preserved == EXPECTED_REPO_DOC_ROWS
            and closure_fail == 0
            and repro_temp == 0
            and artifact_temp == 0
            and patch_auth == 0
            and int(generated_payload.get("branch_count", -1)) == EXPECTED_BRANCH_ROWS
            and int(generated_payload.get("temp_artifact_missing_count", -1))
            == EXPECTED_PARAMETERIZED_ROWS
            and int(generated_payload.get("repo_doc_missing_count", -1)) == 0
            and generated_note.count("Missing `/private/tmp`") == 0
            and generated_note.count("Missing parameterized/temp artifacts") >= 1
        ),
        "closure_status_counts": dict(sorted(status_counts.items())),
        "artifact_location_type_counts": dict(sorted(location_counts.items())),
        "recommended_next_branch": "latest_handoff_manifest_merge_base_refresh",
    }


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scalar_keys = [
        "generated_manifest_detail_rows",
        "generated_manifest_summary_rows",
        "parameterized_rows",
        "repo_doc_rows",
        "parameterized_manifestized_rows",
        "repo_doc_preserved_rows",
        "closure_pass_count",
        "closure_fail_count",
        "repro_private_tmp_literal_rows",
        "artifact_private_tmp_literal_rows",
        "input_manifest_rows",
        "manifest_dir_placeholder_rows",
        "output_root_repro_rows",
        "output_root_artifact_rows",
        "repro_required_if_missing_rows",
        "primary_doc_missing_rows",
        "patch_authorization_sum",
        "runtime_semantic_change_allowed_rows",
        "operator_facing_change_allowed_rows",
        "generator_json_branch_count",
        "generator_json_temp_artifact_missing_count",
        "generator_json_repo_doc_missing_count",
        "generator_json_engine_patch_allowed_sum",
        "generator_json_threshold_patch_allowed_sum",
        "generator_json_operator_promotion_allowed_sum",
        "generated_note_private_tmp_legacy_phrase_count",
        "generated_note_parameterized_phrase_count",
        "expected_temp_literal_drop_rows",
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
    for scope_key in ["closure_status_counts", "artifact_location_type_counts"]:
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
            "# Latest Handoff Manifest Portability Closure Audit V1",
            "",
            "## Summary",
            "- Regenerates the latest evidence handoff manifest and audits the emitted outputs.",
            "- Confirms BR-231's portable repro/path text survived the actual generator output boundary.",
            "- This is handoff-output closure only; it does not run evidence builders or change runtime semantics.",
            "",
            "## Counts",
            f"- generated_manifest_detail_rows: `{payload['generated_manifest_detail_rows']}`",
            f"- parameterized_manifestized_rows: `{payload['parameterized_manifestized_rows']}`",
            f"- repo_doc_preserved_rows: `{payload['repo_doc_preserved_rows']}`",
            f"- repro_private_tmp_literal_rows: `{payload['repro_private_tmp_literal_rows']}`",
            f"- artifact_private_tmp_literal_rows: `{payload['artifact_private_tmp_literal_rows']}`",
            f"- input_manifest_rows: `{payload['input_manifest_rows']}`",
            f"- output_root_artifact_rows: `{payload['output_root_artifact_rows']}`",
            f"- generator_json_temp_artifact_missing_count: `{payload['generator_json_temp_artifact_missing_count']}`",
            f"- closure_complete: `{payload['closure_complete']}`",
            "",
            "## Boundary",
            "- Parameterized paths are reproducible handoff instructions, not committed repo artifacts.",
            "- Branch-local input manifests remain required; do not collapse them into one global manifest here.",
            "- Runtime, threshold, truth, and operator-facing semantics remain unchanged.",
            "",
            "## Next Action",
            f"- Recommended next branch: `{payload['recommended_next_branch']}`.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_dir = run_latest_handoff_builder(repo_root, output_dir)
    generated_detail, generated_summary, generated_payload, generated_note = load_generated(
        generated_dir
    )
    detail_rows = build_detail_rows(generated_detail)
    payload = build_payload(detail_rows, generated_summary, generated_payload, generated_note)
    write_csv(output_dir / DETAIL_OUTPUT_NAME, detail_rows, DETAIL_COLUMNS)
    write_csv(output_dir / SUMMARY_OUTPUT_NAME, summary_rows(payload), SUMMARY_COLUMNS)
    (output_dir / NOTE_OUTPUT_NAME).write_text(render_note(payload), encoding="utf-8")
    (output_dir / JSON_OUTPUT_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
