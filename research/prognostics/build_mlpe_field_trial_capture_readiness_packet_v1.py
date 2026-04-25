#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-103"
DEFAULT_CAPTURE_INPUT = "/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_capture_readiness_br103_check"

READINESS_OUTPUT_NAME = "mlpe_field_trial_capture_readiness_packet_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_capture_readiness_summary_v1.csv"
MISSING_OUTPUT_NAME = "mlpe_field_trial_capture_readiness_missing_evidence_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_capture_readiness_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_capture_readiness_packet_v1.json"

CAPTURE_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "site",
    "root_id",
    "panel_id",
    "mlpe_device_id",
    "start_ts",
    "end_ts",
    "capture_status",
    "injection_case",
    "planned_fault_family",
    "planned_fault_subtype",
    "affected_scope",
    "injection_mode",
    "injection_strength",
    "expected_signature",
    "planned_panel_local_flag",
    "planned_common_cause_flag",
    "planned_measurement_artifact_flag",
    "mlpe_state",
    "raw_data_path",
    "peer_data_path",
    "weather_data_path",
    "waveform_slice_path",
    "timestamp_quality",
    "communication_quality",
    "final_fault_family",
    "final_fault_subtype",
    "final_truth_confidence",
    "final_label_attached",
    "label_status",
    "operator_promotion_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "reviewer",
    "review_note",
]

REQUIRED_CAPTURE_FIELDS = [
    "site",
    "panel_id",
    "mlpe_device_id",
    "start_ts",
    "end_ts",
    "injection_case",
    "planned_fault_family",
    "planned_fault_subtype",
    "affected_scope",
    "injection_mode",
    "injection_strength",
    "expected_signature",
    "mlpe_state",
    "timestamp_quality",
    "communication_quality",
]

REQUIRED_EVIDENCE_PATH_FIELDS = ["raw_data_path", "peer_data_path", "waveform_slice_path"]

READINESS_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "site",
    "panel_id",
    "capture_status",
    "label_status",
    "injection_case",
    "planned_fault_family",
    "planned_fault_subtype",
    "metadata_ready_flag",
    "required_evidence_paths_filled_flag",
    "required_evidence_paths_exist_flag",
    "weather_path_filled_flag",
    "weather_path_exists_flag",
    "final_label_attached",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "readiness_bucket",
    "missing_metadata_fields_csv",
    "missing_evidence_path_fields_csv",
    "missing_evidence_files_csv",
    "next_action",
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_capture(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing capture input: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    for col in CAPTURE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    out = df.reindex(columns=CAPTURE_COLUMNS).copy()
    for col in CAPTURE_COLUMNS:
        out[col] = out[col].map(normalize_text)
    return out


def path_exists(repo_root: Path, path_text: str) -> bool:
    if not path_text:
        return False
    return resolve_path(repo_root, path_text).exists()


def build_readiness(capture: pd.DataFrame, repo_root: Path) -> pd.DataFrame:
    rows = []
    for idx, row in capture.iterrows():
        trial_event_id = row["trial_event_id"] or f"row_{idx + 1}"
        planned = row["capture_status"] == "planned"
        missing_metadata = [field for field in REQUIRED_CAPTURE_FIELDS if not row[field]]
        missing_path_fields = [field for field in REQUIRED_EVIDENCE_PATH_FIELDS if not row[field]]
        missing_files = [
            field
            for field in REQUIRED_EVIDENCE_PATH_FIELDS
            if row[field] and not path_exists(repo_root, row[field])
        ]
        weather_filled = int(bool(row["weather_data_path"]))
        weather_exists = int(path_exists(repo_root, row["weather_data_path"])) if weather_filled else 0

        metadata_ready = int(not planned and not missing_metadata)
        paths_filled = int(not planned and not missing_path_fields)
        paths_exist = int(paths_filled and not missing_files)
        final_label_attached = int(row["final_label_attached"] == "1" or row["label_status"] == "label_attached")

        if planned:
            bucket = "planned_waiting_for_capture"
            next_action = "Fill capture metadata during 실증."
        elif missing_metadata:
            bucket = "capture_metadata_incomplete"
            next_action = "Complete required capture metadata before evidence review."
        elif missing_path_fields:
            bucket = "evidence_paths_missing"
            next_action = "Attach raw, peer, and waveform slice paths."
        elif missing_files:
            bucket = "evidence_files_not_found"
            next_action = "Fix evidence paths or regenerate referenced evidence files."
        elif not final_label_attached:
            bucket = "capture_ready_label_pending"
            next_action = "Ready for final adjudication; keep truth intake blocked until labels are attached."
        else:
            bucket = "label_attached_truth_gate_required"
            next_action = "Run separate truth-intake gate; readiness alone is not promotion approval."

        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": trial_event_id,
                "site": row["site"],
                "panel_id": row["panel_id"],
                "capture_status": row["capture_status"],
                "label_status": row["label_status"],
                "injection_case": row["injection_case"],
                "planned_fault_family": row["planned_fault_family"],
                "planned_fault_subtype": row["planned_fault_subtype"],
                "metadata_ready_flag": metadata_ready,
                "required_evidence_paths_filled_flag": paths_filled,
                "required_evidence_paths_exist_flag": paths_exist,
                "weather_path_filled_flag": weather_filled,
                "weather_path_exists_flag": weather_exists,
                "final_label_attached": final_label_attached,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "readiness_bucket": bucket,
                "missing_metadata_fields_csv": ",".join(missing_metadata),
                "missing_evidence_path_fields_csv": ",".join(missing_path_fields),
                "missing_evidence_files_csv": ",".join(missing_files),
                "next_action": next_action,
            }
        )
    return pd.DataFrame(rows).reindex(columns=READINESS_COLUMNS)


def build_summary(readiness: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "rows": int(len(readiness)),
            "metadata_ready_rows": int(readiness["metadata_ready_flag"].sum()),
            "evidence_paths_filled_rows": int(readiness["required_evidence_paths_filled_flag"].sum()),
            "evidence_paths_exist_rows": int(readiness["required_evidence_paths_exist_flag"].sum()),
            "capture_ready_label_pending_rows": int(readiness["readiness_bucket"].eq("capture_ready_label_pending").sum()),
            "label_attached_rows": int(readiness["final_label_attached"].sum()),
            "truth_intake_allowed_sum": int(readiness["truth_intake_allowed"].sum()),
            "engine_patch_allowed_sum": int(readiness["engine_patch_allowed"].sum()),
        }
    ]
    for bucket, sub in readiness.groupby("readiness_bucket", dropna=False):
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "bucket",
                "summary_key": bucket,
                "rows": int(len(sub)),
                "metadata_ready_rows": int(sub["metadata_ready_flag"].sum()),
                "evidence_paths_filled_rows": int(sub["required_evidence_paths_filled_flag"].sum()),
                "evidence_paths_exist_rows": int(sub["required_evidence_paths_exist_flag"].sum()),
                "capture_ready_label_pending_rows": int(sub["readiness_bucket"].eq("capture_ready_label_pending").sum()),
                "label_attached_rows": int(sub["final_label_attached"].sum()),
                "truth_intake_allowed_sum": int(sub["truth_intake_allowed"].sum()),
                "engine_patch_allowed_sum": int(sub["engine_patch_allowed"].sum()),
            }
        )
    return pd.DataFrame(rows)


def build_missing(readiness: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in readiness.iterrows():
        planned = normalize_text(row["readiness_bucket"]) == "planned_waiting_for_capture"
        metadata_type = "planned_required_later_metadata" if planned else "metadata_field"
        path_type = "planned_required_later_evidence_path" if planned else "evidence_path_field"
        for field in normalize_text(row["missing_metadata_fields_csv"]).split(","):
            if field:
                rows.append({"owner_branch": OWNER_BRANCH, "trial_event_id": row["trial_event_id"], "missing_type": metadata_type, "missing_item": field})
        for field in normalize_text(row["missing_evidence_path_fields_csv"]).split(","):
            if field:
                rows.append({"owner_branch": OWNER_BRANCH, "trial_event_id": row["trial_event_id"], "missing_type": path_type, "missing_item": field})
        for field in normalize_text(row["missing_evidence_files_csv"]).split(","):
            if field:
                rows.append({"owner_branch": OWNER_BRANCH, "trial_event_id": row["trial_event_id"], "missing_type": "evidence_file", "missing_item": field})
    return pd.DataFrame(rows, columns=["owner_branch", "trial_event_id", "missing_type", "missing_item"])


def write_note(output_dir: Path, readiness: pd.DataFrame, summary: pd.DataFrame) -> Path:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-103 MLPE Field-Trial Capture Readiness",
        "",
        "## Purpose",
        "- Read filled or planned BR-102 capture rows and classify readiness before truth intake.",
        "- Separate capture metadata readiness, evidence path readiness, and final label attachment.",
        "- Keep truth, threshold, and engine approvals locked to `0`.",
        "",
        "## Real Result",
        f"- rows: `{overall['rows']}`",
        f"- metadata-ready rows: `{overall['metadata_ready_rows']}`",
        f"- evidence-paths-filled rows: `{overall['evidence_paths_filled_rows']}`",
        f"- evidence-files-exist rows: `{overall['evidence_paths_exist_rows']}`",
        f"- capture-ready label-pending rows: `{overall['capture_ready_label_pending_rows']}`",
        f"- label-attached rows: `{overall['label_attached_rows']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Readiness is not a final label.",
        "- Label-attached rows still require a separate truth-intake gate.",
        "- Missing raw/peer/waveform evidence must be resolved before adjudication.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--capture-input", default=DEFAULT_CAPTURE_INPUT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    capture_input = resolve_path(repo_root, args.capture_input)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    capture = read_capture(capture_input)
    readiness = build_readiness(capture, repo_root)
    summary = build_summary(readiness)
    missing = build_missing(readiness)

    readiness_path = output_dir / READINESS_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    missing_path = output_dir / MISSING_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    readiness.to_csv(readiness_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    missing.to_csv(missing_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, readiness, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "rows": int(overall["rows"]),
        "metadata_ready_rows": int(overall["metadata_ready_rows"]),
        "evidence_paths_filled_rows": int(overall["evidence_paths_filled_rows"]),
        "evidence_paths_exist_rows": int(overall["evidence_paths_exist_rows"]),
        "capture_ready_label_pending_rows": int(overall["capture_ready_label_pending_rows"]),
        "label_attached_rows": int(overall["label_attached_rows"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "readiness": str(readiness_path),
            "summary": str(summary_path),
            "missing": str(missing_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
