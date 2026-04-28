#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-121"
DEFAULT_PACKET = "/private/tmp/mlpe_field_trial_truth_seed_review_packet_br120_check/mlpe_field_trial_truth_seed_review_packet_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_schema_br121_check"

TEMPLATE_OUTPUT_NAME = "mlpe_field_trial_truth_seed_reviewer_decision_template_v1.csv"
SCHEMA_OUTPUT_NAME = "mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.csv"
ALLOWED_VALUES_OUTPUT_NAME = "mlpe_field_trial_truth_seed_reviewer_decision_allowed_values_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_truth_seed_reviewer_decision_schema_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_truth_seed_reviewer_decision_schema_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.json"

PACKET_COLUMNS = [
    "trial_event_id",
    "truth_seed_review_packet_status",
    "truth_candidate_role",
    "reviewer_final_fault_family",
    "reviewer_final_fault_subtype",
    "reviewer_truth_confidence",
    "reviewer_common_cause_clearance",
    "reviewer_measurement_artifact_clearance",
    "reviewer_label_source",
    "truth_gate_bucket",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

TEMPLATE_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "truth_seed_review_packet_status",
    "truth_candidate_role",
    "reviewer_final_fault_family",
    "reviewer_final_fault_subtype",
    "reviewer_truth_confidence",
    "reviewer_common_cause_clearance",
    "reviewer_measurement_artifact_clearance",
    "reviewer_label_source",
    "truth_gate_bucket",
    "truth_seed_reviewer_decision",
    "truth_seed_reviewer_confidence",
    "truth_seed_independent_evidence_status",
    "truth_seed_common_cause_final_clearance",
    "truth_seed_measurement_artifact_final_clearance",
    "truth_seed_counterexample_check_status",
    "truth_seed_reviewer_decision_source",
    "truth_seed_reviewer",
    "truth_seed_reviewed_at",
    "truth_seed_reviewer_notes",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

ALLOWED_VALUES = {
    "truth_seed_reviewer_decision": [
        "approve_for_future_truth_intake",
        "reject_not_truth_seed",
        "defer_needs_more_evidence",
    ],
    "truth_seed_reviewer_confidence": [
        "confirmed",
        "probable",
        "ambiguous",
    ],
    "truth_seed_independent_evidence_status": [
        "independent_evidence_confirmed",
        "single_source_only",
        "not_confirmed",
        "unknown",
    ],
    "truth_seed_common_cause_final_clearance": [
        "final_cleared_panel_local",
        "final_common_cause_risk",
        "unknown",
    ],
    "truth_seed_measurement_artifact_final_clearance": [
        "final_cleared_physical",
        "final_measurement_artifact_risk",
        "unknown",
    ],
    "truth_seed_counterexample_check_status": [
        "checked_no_counterexample",
        "counterexample_risk",
        "unknown",
    ],
    "truth_seed_reviewer_decision_source": [
        "field_trial_packet_review",
        "field_inspection_record",
        "maintenance_record",
        "expert_panel_review",
    ],
    "canonical_truth_write_allowed": ["0"],
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


def int_value(value: object) -> int:
    text = normalize_text(value)
    if not text:
        return 0
    return int(float(text))


def build_template(packet: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in packet.iterrows():
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": normalize_text(row.get("trial_event_id", "")),
                "truth_seed_review_packet_status": normalize_text(row.get("truth_seed_review_packet_status", "")),
                "truth_candidate_role": normalize_text(row.get("truth_candidate_role", "")),
                "reviewer_final_fault_family": normalize_text(row.get("reviewer_final_fault_family", "")),
                "reviewer_final_fault_subtype": normalize_text(row.get("reviewer_final_fault_subtype", "")),
                "reviewer_truth_confidence": normalize_text(row.get("reviewer_truth_confidence", "")),
                "reviewer_common_cause_clearance": normalize_text(row.get("reviewer_common_cause_clearance", "")),
                "reviewer_measurement_artifact_clearance": normalize_text(row.get("reviewer_measurement_artifact_clearance", "")),
                "reviewer_label_source": normalize_text(row.get("reviewer_label_source", "")),
                "truth_gate_bucket": normalize_text(row.get("truth_gate_bucket", "")),
                "truth_seed_reviewer_decision": "",
                "truth_seed_reviewer_confidence": "",
                "truth_seed_independent_evidence_status": "",
                "truth_seed_common_cause_final_clearance": "",
                "truth_seed_measurement_artifact_final_clearance": "",
                "truth_seed_counterexample_check_status": "",
                "truth_seed_reviewer_decision_source": "",
                "truth_seed_reviewer": "",
                "truth_seed_reviewed_at": "",
                "truth_seed_reviewer_notes": "",
                "canonical_truth_write_allowed": 0,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
            }
        )
    return pd.DataFrame(rows).reindex(columns=TEMPLATE_COLUMNS)


def build_schema() -> pd.DataFrame:
    required = {
        "trial_event_id",
        "truth_seed_review_packet_status",
        "truth_candidate_role",
        "truth_seed_reviewer_decision",
        "truth_seed_reviewer_confidence",
        "truth_seed_independent_evidence_status",
        "truth_seed_common_cause_final_clearance",
        "truth_seed_measurement_artifact_final_clearance",
        "truth_seed_counterexample_check_status",
        "truth_seed_reviewer_decision_source",
        "truth_seed_reviewer",
        "truth_seed_reviewed_at",
    }
    system_locked = {
        "owner_branch",
        "trial_event_id",
        "truth_seed_review_packet_status",
        "truth_candidate_role",
        "reviewer_final_fault_family",
        "reviewer_final_fault_subtype",
        "reviewer_truth_confidence",
        "reviewer_common_cause_clearance",
        "reviewer_measurement_artifact_clearance",
        "reviewer_label_source",
        "truth_gate_bucket",
        "canonical_truth_write_allowed",
        "truth_intake_allowed",
        "threshold_patch_allowed",
        "engine_patch_allowed",
    }
    rows = []
    for col in TEMPLATE_COLUMNS:
        if col in system_locked:
            edit_policy = "system_locked"
        elif col == "truth_seed_reviewer_notes":
            edit_policy = "external_reviewer_optional"
        else:
            edit_policy = "external_reviewer_fill"
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "column": col,
                "required_when_packet_row_exists": int(col in required),
                "edit_policy": edit_policy,
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
                "reviewer_decision_attached_rows": int(template["truth_seed_reviewer_decision"].map(normalize_text).ne("").sum()) if len(template) else 0,
                "canonical_truth_write_allowed_sum": int(template["canonical_truth_write_allowed"].map(int_value).sum()) if len(template) else 0,
                "truth_intake_allowed_sum": int(template["truth_intake_allowed"].map(int_value).sum()) if len(template) else 0,
                "threshold_patch_allowed_sum": int(template["threshold_patch_allowed"].map(int_value).sum()) if len(template) else 0,
                "engine_patch_allowed_sum": int(template["engine_patch_allowed"].map(int_value).sum()) if len(template) else 0,
            }
        ]
    )


def write_note(output_dir: Path, summary: pd.DataFrame) -> Path:
    row = summary.iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-121 MLPE Field-Trial Truth-Seed Reviewer Decision Schema",
        "",
        "## Purpose",
        "- Define the reviewer decision schema for BR-120 sidecar truth-seed review packet rows.",
        "- Keep reviewer decisions separate from canonical truth writes and algorithm patches.",
        "",
        "## Result",
        f"- template rows: `{row['template_rows']}`",
        f"- schema rows: `{row['schema_rows']}`",
        f"- allowed-value rows: `{row['allowed_value_rows']}`",
        f"- reviewer decision attached rows: `{row['reviewer_decision_attached_rows']}`",
        f"- canonical truth write allowed sum: `{row['canonical_truth_write_allowed_sum']}`",
        f"- truth intake allowed sum: `{row['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{row['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{row['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- A filled reviewer decision is still not a canonical truth write.",
        "- Canonical truth, threshold, and engine approval fields remain locked to `0`.",
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
        "reviewer_decision_attached_rows": int(row["reviewer_decision_attached_rows"]),
        "canonical_truth_write_allowed_sum": int(row["canonical_truth_write_allowed_sum"]),
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
