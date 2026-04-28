#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-115"
DEFAULT_PACKET = "/private/tmp/mlpe_field_trial_returned_capture_adjudication_packet_br114_check/mlpe_field_trial_returned_capture_adjudication_packet_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check"

TEMPLATE_OUTPUT_NAME = "mlpe_field_trial_final_label_intake_template_v1.csv"
SCHEMA_OUTPUT_NAME = "mlpe_field_trial_final_label_intake_schema_v1.csv"
ALLOWED_VALUES_OUTPUT_NAME = "mlpe_field_trial_final_label_allowed_values_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_final_label_intake_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_final_label_intake_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_final_label_intake_schema_v1.json"

PACKET_COLUMNS = [
    "trial_event_id",
    "packet_status",
    "source_preflight_bucket",
]

LABEL_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "packet_status",
    "source_preflight_bucket",
    "reviewer_final_fault_family",
    "reviewer_final_fault_subtype",
    "reviewer_truth_confidence",
    "reviewer_common_cause_clearance",
    "reviewer_measurement_artifact_clearance",
    "reviewer_label_source",
    "reviewer",
    "reviewed_at",
    "reviewer_notes",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

ALLOWED_VALUES = {
    "reviewer_truth_confidence": ["confirmed_injected", "confirmed_observed", "probable", "ambiguous", "negative_control"],
    "reviewer_common_cause_clearance": ["cleared_panel_local", "common_cause_suspected", "common_cause_confirmed", "unknown"],
    "reviewer_measurement_artifact_clearance": ["cleared_physical", "measurement_artifact_suspected", "measurement_artifact_confirmed", "unknown"],
    "reviewer_label_source": ["field_trial_injection_log", "field_inspection", "maintenance_record", "manual_expert_review"],
    "truth_intake_allowed": ["0"],
    "threshold_patch_allowed": ["0"],
    "engine_patch_allowed": ["0"],
}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_packet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing packet input: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    for col in PACKET_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    out = df.copy()
    for col in out.columns:
        out[col] = out[col].map(normalize_text)
    return out


def build_template(packet: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in packet.iterrows():
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": row["trial_event_id"],
                "packet_status": row["packet_status"],
                "source_preflight_bucket": row["source_preflight_bucket"],
                "reviewer_final_fault_family": "",
                "reviewer_final_fault_subtype": "",
                "reviewer_truth_confidence": "",
                "reviewer_common_cause_clearance": "",
                "reviewer_measurement_artifact_clearance": "",
                "reviewer_label_source": "",
                "reviewer": "",
                "reviewed_at": "",
                "reviewer_notes": "",
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
            }
        )
    return pd.DataFrame(rows).reindex(columns=LABEL_COLUMNS)


def build_schema() -> pd.DataFrame:
    rows = []
    required = {
        "trial_event_id",
        "reviewer_final_fault_family",
        "reviewer_final_fault_subtype",
        "reviewer_truth_confidence",
        "reviewer_common_cause_clearance",
        "reviewer_measurement_artifact_clearance",
        "reviewer_label_source",
        "reviewer",
        "reviewed_at",
    }
    for col in LABEL_COLUMNS:
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "column": col,
                "required_when_packet_row_exists": int(col in required),
                "edit_policy": "external_reviewer_fill" if col in required or col == "reviewer_notes" else "system_locked",
            }
        )
    return pd.DataFrame(rows)


def build_allowed_values() -> pd.DataFrame:
    rows = []
    for field, values in ALLOWED_VALUES.items():
        for value in values:
            rows.append({"owner_branch": OWNER_BRANCH, "field": field, "allowed_value": value})
    return pd.DataFrame(rows)


def build_summary(template: pd.DataFrame, schema: pd.DataFrame, allowed: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "template_rows": int(len(template)),
                "schema_rows": int(len(schema)),
                "allowed_value_rows": int(len(allowed)),
                "reviewer_label_attached_rows": 0,
                "truth_intake_allowed_sum": int(template["truth_intake_allowed"].sum()) if len(template) else 0,
                "threshold_patch_allowed_sum": int(template["threshold_patch_allowed"].sum()) if len(template) else 0,
                "engine_patch_allowed_sum": int(template["engine_patch_allowed"].sum()) if len(template) else 0,
            }
        ]
    )


def write_note(output_dir: Path, summary: pd.DataFrame) -> Path:
    row = summary.iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-115 MLPE Field-Trial Final Label Intake Schema",
        "",
        "## Purpose",
        "- Define how external reviewer labels will be captured after BR-114 packet rows exist.",
        "- Keep label intake separate from truth intake and algorithm patch approval.",
        "",
        "## Real Result",
        f"- template rows: `{row['template_rows']}`",
        f"- schema rows: `{row['schema_rows']}`",
        f"- allowed-value rows: `{row['allowed_value_rows']}`",
        f"- reviewer-label-attached rows: `{row['reviewer_label_attached_rows']}`",
        f"- truth intake allowed sum: `{row['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{row['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{row['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- A filled reviewer label is still not automatic truth promotion.",
        "- Separate validation and truth-intake gates must run after labels arrive.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--packet", default=DEFAULT_PACKET)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    packet_path = resolve_path(repo_root, args.packet)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    packet = read_packet(packet_path)
    template = build_template(packet)
    schema = build_schema()
    allowed = build_allowed_values()
    summary = build_summary(template, schema, allowed)

    template_path = output_dir / TEMPLATE_OUTPUT_NAME
    schema_path = output_dir / SCHEMA_OUTPUT_NAME
    allowed_path = output_dir / ALLOWED_VALUES_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    template.to_csv(template_path, index=False, encoding="utf-8-sig")
    schema.to_csv(schema_path, index=False, encoding="utf-8-sig")
    allowed.to_csv(allowed_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    row = summary.iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "template_rows": int(row["template_rows"]),
        "schema_rows": int(row["schema_rows"]),
        "allowed_value_rows": int(row["allowed_value_rows"]),
        "reviewer_label_attached_rows": int(row["reviewer_label_attached_rows"]),
        "truth_intake_allowed_sum": int(row["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(row["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(row["engine_patch_allowed_sum"]),
        "outputs": {
            "template": str(template_path),
            "schema": str(schema_path),
            "allowed_values": str(allowed_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
