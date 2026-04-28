#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-108"
DEFAULT_CAPTURE_INPUT = "/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_partial_capture_failure_matrix_br108_check"

MATRIX_CAPTURE_OUTPUT_NAME = "mlpe_field_trial_partial_capture_failure_matrix_input_v1.csv"
EXPECTED_OUTPUT_NAME = "mlpe_field_trial_partial_capture_expected_buckets_v1.csv"
EVIDENCE_OUTPUT_NAME = "mlpe_field_trial_partial_capture_evidence_manifest_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_partial_capture_failure_matrix_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_partial_capture_failure_matrix_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_partial_capture_failure_matrix_v1.json"

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

SCENARIOS = [
    ("planned_baseline", "planned_waiting_for_capture", "blocked_planned_capture"),
    ("complete_label_pending", "capture_ready_label_pending", "adjudication_handoff_ready"),
    ("missing_metadata", "capture_metadata_incomplete", "blocked_readiness_incomplete"),
    ("missing_evidence_path", "evidence_paths_missing", "blocked_readiness_incomplete"),
    ("missing_evidence_file", "evidence_files_not_found", "blocked_readiness_incomplete"),
    ("label_attached_truth_gate", "label_attached_truth_gate_required", "truth_gate_required_after_label"),
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_template(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing capture template: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    for col in CAPTURE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    out = df.reindex(columns=CAPTURE_COLUMNS).copy()
    for col in CAPTURE_COLUMNS:
        out[col] = out[col].map(normalize_text)
    return out


def write_evidence(path: Path, event_id: str, kind: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "ts,v,i,p,kind,trial_event_id\n"
        f"2026-01-01T00:00:00Z,40.0,8.0,320.0,{kind},{event_id}\n",
        encoding="utf-8",
    )


def base_filled_row(template_row: pd.Series, idx: int, output_dir: Path) -> tuple[dict[str, str], list[dict[str, object]]]:
    event_id = f"BR108-{idx + 1:03d}"
    evidence_dir = output_dir / "partial_capture_evidence" / event_id
    evidence_rows = []
    paths = {
        "raw_data_path": evidence_dir / "raw.csv",
        "peer_data_path": evidence_dir / "peer.csv",
        "weather_data_path": evidence_dir / "weather.csv",
        "waveform_slice_path": evidence_dir / "waveform.csv",
    }
    for field, path in paths.items():
        kind = field.replace("_data_path", "").replace("_slice_path", "")
        write_evidence(path, event_id, kind)
        evidence_rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": event_id,
                "field_name": field,
                "evidence_path": str(path),
                "exists_flag": int(path.exists()),
            }
        )
    row = template_row.to_dict()
    row.update(
        {
            "owner_branch": OWNER_BRANCH,
            "trial_event_id": event_id,
            "site": "synthetic_site",
            "root_id": "synthetic_root",
            "panel_id": f"synthetic_panel_{idx + 1:03d}",
            "mlpe_device_id": f"synthetic_mlpe_{idx + 1:03d}",
            "start_ts": "2026-01-01T00:00:00Z",
            "end_ts": "2026-01-01T00:10:00Z",
            "capture_status": "captured",
            "injection_strength": "synthetic_failure_matrix",
            "raw_data_path": str(paths["raw_data_path"]),
            "peer_data_path": str(paths["peer_data_path"]),
            "weather_data_path": str(paths["weather_data_path"]),
            "waveform_slice_path": str(paths["waveform_slice_path"]),
            "timestamp_quality": "ok",
            "communication_quality": "ok",
            "final_fault_family": "",
            "final_fault_subtype": "",
            "final_truth_confidence": "",
            "final_label_attached": "0",
            "label_status": "label_pending",
            "operator_promotion_allowed": "0",
            "engine_patch_allowed": "0",
            "threshold_patch_allowed": "0",
            "reviewer": "",
            "review_note": "synthetic failure matrix only",
        }
    )
    return row, evidence_rows


def build_matrix(template: pd.DataFrame, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    expected_rows = []
    evidence_rows = []
    for idx, (scenario, readiness_bucket, guard_bucket) in enumerate(SCENARIOS):
        row, evidence = base_filled_row(template.iloc[idx % len(template)], idx, output_dir)
        event_id = row["trial_event_id"]
        if scenario == "planned_baseline":
            row["capture_status"] = "planned"
        elif scenario == "missing_metadata":
            row["panel_id"] = ""
        elif scenario == "missing_evidence_path":
            row["raw_data_path"] = ""
        elif scenario == "missing_evidence_file":
            missing_path = output_dir / "partial_capture_evidence" / event_id / "missing_raw.csv"
            row["raw_data_path"] = str(missing_path)
            evidence.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "field_name": "raw_data_path",
                    "evidence_path": str(missing_path),
                    "exists_flag": 0,
                }
            )
        elif scenario == "label_attached_truth_gate":
            row["final_fault_family"] = row["planned_fault_family"]
            row["final_fault_subtype"] = row["planned_fault_subtype"]
            row["final_truth_confidence"] = "confirmed_injected"
            row["final_label_attached"] = "1"
            row["label_status"] = "label_attached"
        row["review_note"] = f"synthetic failure matrix scenario={scenario}; not field truth"
        rows.append(row)
        evidence_rows.extend(evidence)
        expected_rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": event_id,
                "scenario": scenario,
                "expected_readiness_bucket": readiness_bucket,
                "expected_guard_bucket": guard_bucket,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
            }
        )
    return (
        pd.DataFrame(rows).reindex(columns=CAPTURE_COLUMNS),
        pd.DataFrame(expected_rows),
        pd.DataFrame(evidence_rows),
    )


def build_summary(matrix: pd.DataFrame, expected: pd.DataFrame, evidence: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "scenario_rows": int(len(matrix)),
                "expected_rows": int(len(expected)),
                "evidence_rows": int(len(evidence)),
                "evidence_missing_rows": int(evidence["exists_flag"].eq(0).sum()),
                "label_attached_rows": int(matrix["final_label_attached"].astype(str).eq("1").sum()),
                "truth_intake_allowed_sum": 0,
                "threshold_patch_allowed_sum": 0,
                "engine_patch_allowed_sum": 0,
            }
        ]
    )


def write_note(output_dir: Path, summary: pd.DataFrame) -> Path:
    row = summary.iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-108 MLPE Field-Trial Partial Capture Failure Matrix",
        "",
        "## Purpose",
        "- Create synthetic partial-capture scenarios to test readiness and handoff failure modes.",
        "- Confirm incomplete capture rows block adjudication while complete label-pending rows can hand off.",
        "",
        "## Real Result",
        f"- scenario rows: `{row['scenario_rows']}`",
        f"- expected rows: `{row['expected_rows']}`",
        f"- evidence rows: `{row['evidence_rows']}`",
        f"- evidence missing rows: `{row['evidence_missing_rows']}`",
        f"- label-attached rows: `{row['label_attached_rows']}`",
        f"- truth intake allowed sum: `{row['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{row['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{row['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- These rows are synthetic negative/positive plumbing cases only.",
        "- They must not be used as field truth labels.",
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

    template = read_template(capture_input)
    matrix, expected, evidence = build_matrix(template, output_dir)
    summary = build_summary(matrix, expected, evidence)

    matrix_path = output_dir / MATRIX_CAPTURE_OUTPUT_NAME
    expected_path = output_dir / EXPECTED_OUTPUT_NAME
    evidence_path = output_dir / EVIDENCE_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    matrix.to_csv(matrix_path, index=False, encoding="utf-8-sig")
    expected.to_csv(expected_path, index=False, encoding="utf-8-sig")
    evidence.to_csv(evidence_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    overall = summary.iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "scenario_rows": int(overall["scenario_rows"]),
        "expected_rows": int(overall["expected_rows"]),
        "evidence_rows": int(overall["evidence_rows"]),
        "evidence_missing_rows": int(overall["evidence_missing_rows"]),
        "label_attached_rows": int(overall["label_attached_rows"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "matrix": str(matrix_path),
            "expected": str(expected_path),
            "evidence": str(evidence_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
