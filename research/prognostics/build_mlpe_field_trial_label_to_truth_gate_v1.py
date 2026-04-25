#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-117"
DEFAULT_LABEL_INPUT = "/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_template_v1.csv"
DEFAULT_LABEL_VALIDATION = "/private/tmp/mlpe_field_trial_final_label_validator_br116_check/mlpe_field_trial_final_label_validation_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_label_to_truth_gate_br117_check"

GATE_OUTPUT_NAME = "mlpe_field_trial_label_to_truth_gate_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_label_to_truth_gate_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_label_to_truth_gate_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_label_to_truth_gate_v1.json"

ELIGIBLE_TRUTH_CONFIDENCE = {"confirmed_injected", "confirmed_observed", "negative_control"}
POSITIVE_TRUTH_CONFIDENCE = {"confirmed_injected", "confirmed_observed"}

LABEL_COLUMNS = [
    "trial_event_id",
    "reviewer_final_fault_family",
    "reviewer_final_fault_subtype",
    "reviewer_truth_confidence",
    "reviewer_common_cause_clearance",
    "reviewer_measurement_artifact_clearance",
    "reviewer_label_source",
    "reviewer",
    "reviewed_at",
    "reviewer_notes",
]

VALIDATION_COLUMNS = [
    "trial_event_id",
    "reviewer_label_complete_flag",
    "label_validation_failed_flag",
    "truth_gate_candidate_flag",
    "label_validation_bucket",
]

GATE_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "label_validation_bucket",
    "reviewer_label_complete_flag",
    "label_validation_failed_flag",
    "truth_gate_candidate_flag",
    "reviewer_final_fault_family",
    "reviewer_final_fault_subtype",
    "reviewer_truth_confidence",
    "reviewer_common_cause_clearance",
    "reviewer_measurement_artifact_clearance",
    "reviewer_label_source",
    "truth_candidate_role",
    "truth_gate_ready_flag",
    "truth_gate_blocked_flag",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "truth_gate_bucket",
    "blocker_reason",
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


def read_csv(path: Path, required_columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing input: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    for col in required_columns:
        if col not in df.columns:
            df[col] = ""
    out = df.copy()
    for col in out.columns:
        out[col] = out[col].map(normalize_text)
    return out


def int_flag(value: object) -> int:
    return int(normalize_text(value) == "1")


def truth_role(confidence: str) -> str:
    if confidence in POSITIVE_TRUTH_CONFIDENCE:
        return "positive_truth_candidate"
    if confidence == "negative_control":
        return "negative_truth_candidate"
    return "not_truth_candidate"


def build_gate(label_input: pd.DataFrame, validation: pd.DataFrame) -> pd.DataFrame:
    validation_by_event = {
        normalize_text(row["trial_event_id"]): row
        for _, row in validation.iterrows()
        if normalize_text(row.get("trial_event_id", ""))
    }
    rows = []
    for _, label in label_input.iterrows():
        event_id = normalize_text(label["trial_event_id"])
        validation_row = validation_by_event.get(event_id, pd.Series(dtype=object))
        validation_found = not validation_row.empty
        complete = int_flag(validation_row.get("reviewer_label_complete_flag", "0"))
        failed = int_flag(validation_row.get("label_validation_failed_flag", "1"))
        candidate = int_flag(validation_row.get("truth_gate_candidate_flag", "0"))
        label_bucket = normalize_text(validation_row.get("label_validation_bucket", "missing_label_validation"))
        confidence = normalize_text(label.get("reviewer_truth_confidence", ""))
        common_clearance = normalize_text(label.get("reviewer_common_cause_clearance", ""))
        artifact_clearance = normalize_text(label.get("reviewer_measurement_artifact_clearance", ""))

        if not validation_found:
            bucket = "blocked_missing_label_validation"
            blocker = "missing_label_validation"
            ready = 0
            next_action = "Run BR-116 label validation before truth gate."
        elif failed or not complete or not candidate:
            bucket = "blocked_label_validation_not_passed"
            blocker = label_bucket or "label_validation_not_passed"
            ready = 0
            next_action = "Fix BR-116 label validation issues before truth gate."
        elif confidence not in ELIGIBLE_TRUTH_CONFIDENCE:
            bucket = "blocked_truth_confidence_not_confirmed"
            blocker = f"reviewer_truth_confidence={confidence or 'blank'}"
            ready = 0
            next_action = "Keep probable/ambiguous labels out of truth intake until confirmed or negative-control."
        elif common_clearance != "cleared_panel_local":
            bucket = "blocked_common_cause_not_cleared"
            blocker = f"reviewer_common_cause_clearance={common_clearance or 'blank'}"
            ready = 0
            next_action = "Resolve common-cause clearance before truth intake."
        elif artifact_clearance != "cleared_physical":
            bucket = "blocked_measurement_artifact_not_cleared"
            blocker = f"reviewer_measurement_artifact_clearance={artifact_clearance or 'blank'}"
            ready = 0
            next_action = "Resolve measurement-artifact clearance before truth intake."
        else:
            bucket = "truth_gate_ready_for_truth_intake_review"
            blocker = ""
            ready = 1
            next_action = "Send to the next truth-intake review gate; do not self-authorize patches."

        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": event_id,
                "label_validation_bucket": label_bucket,
                "reviewer_label_complete_flag": complete,
                "label_validation_failed_flag": failed,
                "truth_gate_candidate_flag": candidate,
                "reviewer_final_fault_family": normalize_text(label.get("reviewer_final_fault_family", "")),
                "reviewer_final_fault_subtype": normalize_text(label.get("reviewer_final_fault_subtype", "")),
                "reviewer_truth_confidence": confidence,
                "reviewer_common_cause_clearance": common_clearance,
                "reviewer_measurement_artifact_clearance": artifact_clearance,
                "reviewer_label_source": normalize_text(label.get("reviewer_label_source", "")),
                "truth_candidate_role": truth_role(confidence) if ready else "not_truth_candidate",
                "truth_gate_ready_flag": ready,
                "truth_gate_blocked_flag": int(not ready),
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "truth_gate_bucket": bucket,
                "blocker_reason": blocker,
                "next_action": next_action,
            }
        )
    return pd.DataFrame(rows).reindex(columns=GATE_COLUMNS)


def build_summary(gate: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "label_rows": int(len(gate)),
            "truth_gate_ready_rows": int(gate["truth_gate_ready_flag"].sum()) if len(gate) else 0,
            "truth_gate_blocked_rows": int(gate["truth_gate_blocked_flag"].sum()) if len(gate) else 0,
            "positive_truth_candidate_rows": int(gate["truth_candidate_role"].eq("positive_truth_candidate").sum()) if len(gate) else 0,
            "negative_truth_candidate_rows": int(gate["truth_candidate_role"].eq("negative_truth_candidate").sum()) if len(gate) else 0,
            "truth_intake_allowed_sum": int(gate["truth_intake_allowed"].sum()) if len(gate) else 0,
            "threshold_patch_allowed_sum": int(gate["threshold_patch_allowed"].sum()) if len(gate) else 0,
            "engine_patch_allowed_sum": int(gate["engine_patch_allowed"].sum()) if len(gate) else 0,
        }
    ]
    if len(gate):
        for bucket, sub in gate.groupby("truth_gate_bucket", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "truth_gate_bucket",
                    "summary_key": bucket,
                    "label_rows": int(len(sub)),
                    "truth_gate_ready_rows": int(sub["truth_gate_ready_flag"].sum()),
                    "truth_gate_blocked_rows": int(sub["truth_gate_blocked_flag"].sum()),
                    "positive_truth_candidate_rows": int(sub["truth_candidate_role"].eq("positive_truth_candidate").sum()),
                    "negative_truth_candidate_rows": int(sub["truth_candidate_role"].eq("negative_truth_candidate").sum()),
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
        "# BR-117 MLPE Field-Trial Label-to-Truth Gate",
        "",
        "## Purpose",
        "- Gate BR-116-valid reviewer labels before truth intake.",
        "- Require confirmed/negative-control confidence plus common-cause and measurement-artifact clearance.",
        "",
        "## Real Result",
        f"- label rows: `{overall['label_rows']}`",
        f"- truth-gate-ready rows: `{overall['truth_gate_ready_rows']}`",
        f"- truth-gate-blocked rows: `{overall['truth_gate_blocked_rows']}`",
        f"- positive truth candidate rows: `{overall['positive_truth_candidate_rows']}`",
        f"- negative truth candidate rows: `{overall['negative_truth_candidate_rows']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Truth-gate-ready rows are candidates for the next truth-intake review, not automatic truth seeds.",
        "- Threshold and engine patch approvals remain locked to `0`.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--label-input", default=DEFAULT_LABEL_INPUT)
    parser.add_argument("--label-validation", default=DEFAULT_LABEL_VALIDATION)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    label_path = resolve_path(repo_root, args.label_input)
    validation_path = resolve_path(repo_root, args.label_validation)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    label_input = read_csv(label_path, LABEL_COLUMNS)
    validation = read_csv(validation_path, VALIDATION_COLUMNS)
    gate = build_gate(label_input, validation)
    summary = build_summary(gate)

    gate_path = output_dir / GATE_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    gate.to_csv(gate_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "label_rows": int(overall["label_rows"]),
        "truth_gate_ready_rows": int(overall["truth_gate_ready_rows"]),
        "truth_gate_blocked_rows": int(overall["truth_gate_blocked_rows"]),
        "positive_truth_candidate_rows": int(overall["positive_truth_candidate_rows"]),
        "negative_truth_candidate_rows": int(overall["negative_truth_candidate_rows"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "gate": str(gate_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
