#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-105"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_package_manifest_br105_check"
DEFAULT_SCHEMA_DIR = "/private/tmp/mlpe_field_trial_capture_schema_br102_check"
DEFAULT_READINESS_DIR = "/private/tmp/mlpe_field_trial_capture_readiness_br103_check"
DEFAULT_INTAKE_DIR = "/private/tmp/mlpe_field_trial_operator_intake_br104_check"

MANIFEST_OUTPUT_NAME = "mlpe_field_trial_package_manifest_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_package_manifest_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_package_manifest_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_package_manifest_v1.json"


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def artifact_rows(repo_root: Path, schema_dir: Path, readiness_dir: Path, intake_dir: Path) -> list[dict[str, object]]:
    docs = repo_root / "docs"
    rows = [
        {
            "stage": "taxonomy",
            "artifact_role": "decision_doc",
            "artifact_name": "BR-101 fault taxonomy",
            "path": docs / "OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_101_MLPE_FIELD_TRIAL_FAULT_TAXONOMY_V1.md",
            "required_for_field_trial": 1,
            "repro_command": "n/a - docs only",
            "approval_boundary": "truth=0;threshold=0;engine=0",
            "next_use": "Read before changing top-level MLPE/PV fault families.",
        },
        {
            "stage": "capture_schema",
            "artifact_role": "builder",
            "artifact_name": "BR-102 capture schema builder",
            "path": repo_root / "research/prognostics/build_mlpe_field_trial_capture_schema_v1.py",
            "required_for_field_trial": 1,
            "repro_command": "python3 research/prognostics/build_mlpe_field_trial_capture_schema_v1.py --repo-root <repo> --output-dir <schema_dir>",
            "approval_boundary": "truth=0;threshold=0;engine=0",
            "next_use": "Regenerate the blank capture template and schema checks.",
        },
        {
            "stage": "capture_schema",
            "artifact_role": "capture_template",
            "artifact_name": "BR-102 capture template",
            "path": schema_dir / "mlpe_field_trial_capture_template_v1.csv",
            "required_for_field_trial": 1,
            "repro_command": "python3 research/prognostics/build_mlpe_field_trial_capture_schema_v1.py --repo-root <repo> --output-dir <schema_dir>",
            "approval_boundary": "truth=0;threshold=0;engine=0",
            "next_use": "Copy/fill during field-trial planning and capture.",
        },
        {
            "stage": "capture_schema",
            "artifact_role": "schema_dictionary",
            "artifact_name": "BR-102 capture schema dictionary",
            "path": schema_dir / "mlpe_field_trial_capture_schema_v1.csv",
            "required_for_field_trial": 1,
            "repro_command": "python3 research/prognostics/build_mlpe_field_trial_capture_schema_v1.py --repo-root <repo> --output-dir <schema_dir>",
            "approval_boundary": "truth=0;threshold=0;engine=0",
            "next_use": "Check field meaning and controlled-value expectations.",
        },
        {
            "stage": "capture_schema",
            "artifact_role": "allowed_values",
            "artifact_name": "BR-102 allowed values",
            "path": schema_dir / "mlpe_field_trial_capture_allowed_values_v1.csv",
            "required_for_field_trial": 1,
            "repro_command": "python3 research/prognostics/build_mlpe_field_trial_capture_schema_v1.py --repo-root <repo> --output-dir <schema_dir>",
            "approval_boundary": "truth=0;threshold=0;engine=0",
            "next_use": "Keep operator-filled values within known categories.",
        },
        {
            "stage": "readiness",
            "artifact_role": "builder",
            "artifact_name": "BR-103 readiness builder",
            "path": repo_root / "research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py",
            "required_for_field_trial": 1,
            "repro_command": "python3 research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py --repo-root <repo> --capture-input <capture_csv> --output-dir <readiness_dir>",
            "approval_boundary": "truth=0;threshold=0;engine=0",
            "next_use": "Re-run after capture rows are filled.",
        },
        {
            "stage": "readiness",
            "artifact_role": "readiness_packet",
            "artifact_name": "BR-103 readiness packet",
            "path": readiness_dir / "mlpe_field_trial_capture_readiness_packet_v1.csv",
            "required_for_field_trial": 1,
            "repro_command": "python3 research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py --repo-root <repo> --capture-input <capture_csv> --output-dir <readiness_dir>",
            "approval_boundary": "truth=0;threshold=0;engine=0",
            "next_use": "Use buckets to decide whether rows are ready for adjudication.",
        },
        {
            "stage": "readiness",
            "artifact_role": "readiness_missing",
            "artifact_name": "BR-103 missing evidence list",
            "path": readiness_dir / "mlpe_field_trial_capture_readiness_missing_evidence_v1.csv",
            "required_for_field_trial": 1,
            "repro_command": "python3 research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py --repo-root <repo> --capture-input <capture_csv> --output-dir <readiness_dir>",
            "approval_boundary": "truth=0;threshold=0;engine=0",
            "next_use": "Resolve missing metadata/evidence before final adjudication.",
        },
        {
            "stage": "operator_intake",
            "artifact_role": "builder",
            "artifact_name": "BR-104 operator intake builder",
            "path": repo_root / "research/prognostics/build_mlpe_field_trial_operator_intake_guide_v1.py",
            "required_for_field_trial": 1,
            "repro_command": "python3 research/prognostics/build_mlpe_field_trial_operator_intake_guide_v1.py --repo-root <repo> --capture-input <capture_csv> --readiness-input <readiness_csv> --output-dir <intake_dir>",
            "approval_boundary": "truth=0;threshold=0;engine=0",
            "next_use": "Regenerate the operator-facing checklist.",
        },
        {
            "stage": "operator_intake",
            "artifact_role": "operator_checklist",
            "artifact_name": "BR-104 operator intake checklist",
            "path": intake_dir / "mlpe_field_trial_operator_intake_checklist_v1.csv",
            "required_for_field_trial": 1,
            "repro_command": "python3 research/prognostics/build_mlpe_field_trial_operator_intake_guide_v1.py --repo-root <repo> --capture-input <capture_csv> --readiness-input <readiness_csv> --output-dir <intake_dir>",
            "approval_boundary": "truth=0;threshold=0;engine=0",
            "next_use": "Give this to operators as the row-level fill list.",
        },
        {
            "stage": "operator_intake",
            "artifact_role": "field_guide",
            "artifact_name": "BR-104 operator field guide",
            "path": intake_dir / "mlpe_field_trial_operator_intake_field_guide_v1.csv",
            "required_for_field_trial": 1,
            "repro_command": "python3 research/prognostics/build_mlpe_field_trial_operator_intake_guide_v1.py --repo-root <repo> --capture-input <capture_csv> --readiness-input <readiness_csv> --output-dir <intake_dir>",
            "approval_boundary": "truth=0;threshold=0;engine=0",
            "next_use": "Use as a field-by-field explanation sheet.",
        },
        {
            "stage": "operator_intake",
            "artifact_role": "runbook",
            "artifact_name": "BR-104 operator runbook",
            "path": intake_dir / "mlpe_field_trial_operator_intake_runbook_v1.md",
            "required_for_field_trial": 1,
            "repro_command": "python3 research/prognostics/build_mlpe_field_trial_operator_intake_guide_v1.py --repo-root <repo> --capture-input <capture_csv> --readiness-input <readiness_csv> --output-dir <intake_dir>",
            "approval_boundary": "truth=0;threshold=0;engine=0",
            "next_use": "Read before capture to avoid final-label or patch confusion.",
        },
        {
            "stage": "handoff",
            "artifact_role": "active_register",
            "artifact_name": "runtime active branch register",
            "path": docs / "OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md",
            "required_for_field_trial": 1,
            "repro_command": "n/a - maintained by branch commits",
            "approval_boundary": "truth=0;threshold=0;engine=0",
            "next_use": "Use as the current ordered decision log.",
        },
    ]
    for idx, row in enumerate(rows, start=1):
        path = Path(row["path"])
        row["owner_branch"] = OWNER_BRANCH
        row["manifest_id"] = f"BR105-MANIFEST-{idx:03d}"
        row["path"] = str(path)
        row["exists_flag"] = int(path.exists())
        row["truth_intake_allowed"] = 0
        row["threshold_patch_allowed"] = 0
        row["engine_patch_allowed"] = 0
    return rows


def build_manifest(repo_root: Path, schema_dir: Path, readiness_dir: Path, intake_dir: Path) -> pd.DataFrame:
    columns = [
        "owner_branch",
        "manifest_id",
        "stage",
        "artifact_role",
        "artifact_name",
        "path",
        "exists_flag",
        "required_for_field_trial",
        "repro_command",
        "approval_boundary",
        "next_use",
        "truth_intake_allowed",
        "threshold_patch_allowed",
        "engine_patch_allowed",
    ]
    return pd.DataFrame(artifact_rows(repo_root, schema_dir, readiness_dir, intake_dir)).reindex(columns=columns)


def build_summary(manifest: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "rows": int(len(manifest)),
            "required_rows": int(manifest["required_for_field_trial"].sum()),
            "required_missing_rows": int(((manifest["required_for_field_trial"] == 1) & (manifest["exists_flag"] == 0)).sum()),
            "truth_intake_allowed_sum": int(manifest["truth_intake_allowed"].sum()),
            "threshold_patch_allowed_sum": int(manifest["threshold_patch_allowed"].sum()),
            "engine_patch_allowed_sum": int(manifest["engine_patch_allowed"].sum()),
        }
    ]
    for stage, sub in manifest.groupby("stage", dropna=False):
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "stage",
                "summary_key": stage,
                "rows": int(len(sub)),
                "required_rows": int(sub["required_for_field_trial"].sum()),
                "required_missing_rows": int(((sub["required_for_field_trial"] == 1) & (sub["exists_flag"] == 0)).sum()),
                "truth_intake_allowed_sum": int(sub["truth_intake_allowed"].sum()),
                "threshold_patch_allowed_sum": int(sub["threshold_patch_allowed"].sum()),
                "engine_patch_allowed_sum": int(sub["engine_patch_allowed"].sum()),
            }
        )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, summary: pd.DataFrame) -> Path:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-105 MLPE Field-Trial Package Manifest",
        "",
        "## Purpose",
        "- Keep the BR-101 through BR-104 field-trial artifacts discoverable from one manifest.",
        "- Separate capture/readiness/operator material from final truth labels and engine changes.",
        "",
        "## Real Result",
        f"- manifest rows: `{overall['rows']}`",
        f"- required rows: `{overall['required_rows']}`",
        f"- required missing rows: `{overall['required_missing_rows']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- This manifest is a navigation layer.",
        "- It does not create labels, approve thresholds, or patch runtime semantics.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--schema-dir", default=DEFAULT_SCHEMA_DIR)
    parser.add_argument("--readiness-dir", default=DEFAULT_READINESS_DIR)
    parser.add_argument("--intake-dir", default=DEFAULT_INTAKE_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    schema_dir = resolve_path(repo_root, args.schema_dir)
    readiness_dir = resolve_path(repo_root, args.readiness_dir)
    intake_dir = resolve_path(repo_root, args.intake_dir)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest(repo_root, schema_dir, readiness_dir, intake_dir)
    summary = build_summary(manifest)

    manifest_path = output_dir / MANIFEST_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "rows": int(overall["rows"]),
        "required_rows": int(overall["required_rows"]),
        "required_missing_rows": int(overall["required_missing_rows"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "manifest": str(manifest_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
