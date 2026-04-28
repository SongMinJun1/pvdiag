#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-113"
DEFAULT_VALIDATION = "/private/tmp/mlpe_field_trial_capture_return_validator_br111_check/mlpe_field_trial_capture_return_validation_v1.csv"
DEFAULT_EVIDENCE_RESOLUTION = "/private/tmp/mlpe_field_trial_capture_return_evidence_resolver_br112_check/mlpe_field_trial_capture_return_evidence_resolution_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_capture_return_rerun_preflight_br113_check"

PREFLIGHT_OUTPUT_NAME = "mlpe_field_trial_capture_return_rerun_preflight_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_capture_return_rerun_preflight_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_capture_return_rerun_preflight_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_capture_return_rerun_preflight_v1.json"

VALIDATION_COLUMNS = [
    "trial_event_id",
    "validation_bucket",
    "returned_ready_for_adjudication_flag",
    "still_waiting_for_real_capture_flag",
    "validation_failed_flag",
    "label_attached_flag",
]

EVIDENCE_COLUMNS = [
    "trial_event_id",
    "evidence_required_flag",
    "evidence_file_exists_flag",
    "evidence_resolution_bucket",
]

PREFLIGHT_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "validation_bucket",
    "returned_ready_for_adjudication_flag",
    "still_waiting_for_real_capture_flag",
    "validation_failed_flag",
    "label_attached_flag",
    "required_evidence_rows",
    "required_evidence_resolved_rows",
    "required_evidence_problem_rows",
    "readiness_handoff_rerun_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "post_return_rerun_bucket",
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


def build_evidence_rollup(evidence: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if evidence.empty:
        return pd.DataFrame(
            columns=[
                "trial_event_id",
                "required_evidence_rows",
                "required_evidence_resolved_rows",
                "required_evidence_problem_rows",
            ]
        )
    for event_id, sub in evidence.groupby("trial_event_id", sort=False, dropna=False):
        required = sub[sub["evidence_required_flag"].map(int_flag).eq(1)]
        resolved = required[required["evidence_resolution_bucket"].eq("evidence_file_resolved")]
        waiting = required[required["evidence_resolution_bucket"].eq("waiting_for_real_capture")]
        problem = required[
            ~required["evidence_resolution_bucket"].isin(["evidence_file_resolved", "waiting_for_real_capture"])
        ]
        rows.append(
            {
                "trial_event_id": normalize_text(event_id),
                "required_evidence_rows": int(len(required)),
                "required_evidence_resolved_rows": int(len(resolved)),
                "required_evidence_problem_rows": 0 if len(waiting) == len(required) else int(len(problem)),
            }
        )
    return pd.DataFrame(rows)


def build_preflight(validation: pd.DataFrame, evidence: pd.DataFrame) -> pd.DataFrame:
    rollup = build_evidence_rollup(evidence)
    rows = validation.merge(rollup, on="trial_event_id", how="left")
    for col in ["required_evidence_rows", "required_evidence_resolved_rows", "required_evidence_problem_rows"]:
        rows[col] = pd.to_numeric(rows[col], errors="coerce").fillna(0).astype(int)

    out_rows = []
    for _, row in rows.iterrows():
        waiting = int_flag(row["still_waiting_for_real_capture_flag"])
        returned_ready = int_flag(row["returned_ready_for_adjudication_flag"])
        validation_failed = int_flag(row["validation_failed_flag"])
        label_attached = int_flag(row["label_attached_flag"])
        evidence_problem = int(row["required_evidence_problem_rows"])
        required_rows = int(row["required_evidence_rows"])
        resolved_rows = int(row["required_evidence_resolved_rows"])

        if waiting:
            bucket = "blocked_waiting_for_real_capture"
            allowed = 0
            next_action = "Wait for real capture return before rerunning readiness/handoff gates."
        elif validation_failed:
            bucket = "blocked_return_validation_failed"
            allowed = 0
            next_action = "Resolve BR-111 validation failures before rerun."
        elif evidence_problem:
            bucket = "blocked_required_evidence_problem"
            allowed = 0
            next_action = "Resolve BR-112 required evidence problems before rerun."
        elif label_attached:
            bucket = "truth_gate_required_after_label"
            allowed = 0
            next_action = "Run the separate truth-intake gate; do not use rerun preflight as approval."
        elif returned_ready and required_rows > 0 and resolved_rows == required_rows:
            bucket = "ready_for_readiness_handoff_rerun"
            allowed = 1
            next_action = "Rerun BR-103 readiness and BR-106 handoff guard on returned capture rows."
        else:
            bucket = "blocked_return_not_ready"
            allowed = 0
            next_action = "Inspect validation and evidence state before rerun."

        out_rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": row["trial_event_id"],
                "validation_bucket": row["validation_bucket"],
                "returned_ready_for_adjudication_flag": returned_ready,
                "still_waiting_for_real_capture_flag": waiting,
                "validation_failed_flag": validation_failed,
                "label_attached_flag": label_attached,
                "required_evidence_rows": required_rows,
                "required_evidence_resolved_rows": resolved_rows,
                "required_evidence_problem_rows": evidence_problem,
                "readiness_handoff_rerun_allowed": allowed,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "post_return_rerun_bucket": bucket,
                "next_action": next_action,
            }
        )
    return pd.DataFrame(out_rows).reindex(columns=PREFLIGHT_COLUMNS)


def build_summary(preflight: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "rows": int(len(preflight)),
            "waiting_rows": int(preflight["still_waiting_for_real_capture_flag"].sum()),
            "rerun_allowed_rows": int(preflight["readiness_handoff_rerun_allowed"].sum()),
            "validation_failed_rows": int(preflight["validation_failed_flag"].sum()),
            "required_evidence_problem_rows": int(preflight["required_evidence_problem_rows"].sum()),
            "truth_intake_allowed_sum": int(preflight["truth_intake_allowed"].sum()),
            "threshold_patch_allowed_sum": int(preflight["threshold_patch_allowed"].sum()),
            "engine_patch_allowed_sum": int(preflight["engine_patch_allowed"].sum()),
        }
    ]
    for bucket, sub in preflight.groupby("post_return_rerun_bucket", dropna=False):
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "post_return_rerun_bucket",
                "summary_key": bucket,
                "rows": int(len(sub)),
                "waiting_rows": int(sub["still_waiting_for_real_capture_flag"].sum()),
                "rerun_allowed_rows": int(sub["readiness_handoff_rerun_allowed"].sum()),
                "validation_failed_rows": int(sub["validation_failed_flag"].sum()),
                "required_evidence_problem_rows": int(sub["required_evidence_problem_rows"].sum()),
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
        "# BR-113 MLPE Field-Trial Capture Return Rerun Preflight",
        "",
        "## Purpose",
        "- Combine BR-111 validation and BR-112 evidence resolution before BR-103/BR-106 reruns.",
        "- Allow readiness/handoff rerun only when returned capture and required evidence are complete.",
        "",
        "## Real Result",
        f"- rows: `{overall['rows']}`",
        f"- waiting rows: `{overall['waiting_rows']}`",
        f"- rerun-allowed rows: `{overall['rerun_allowed_rows']}`",
        f"- validation-failed rows: `{overall['validation_failed_rows']}`",
        f"- required evidence problem rows: `{overall['required_evidence_problem_rows']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Rerun allowed is not adjudication approval.",
        "- Truth, threshold, and engine approvals remain locked to `0`.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--validation", default=DEFAULT_VALIDATION)
    parser.add_argument("--evidence-resolution", default=DEFAULT_EVIDENCE_RESOLUTION)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    validation_path = resolve_path(repo_root, args.validation)
    evidence_path = resolve_path(repo_root, args.evidence_resolution)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    validation = read_csv(validation_path, VALIDATION_COLUMNS)
    evidence = read_csv(evidence_path, EVIDENCE_COLUMNS)
    preflight = build_preflight(validation, evidence)
    summary = build_summary(preflight)

    preflight_path = output_dir / PREFLIGHT_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    preflight.to_csv(preflight_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "rows": int(overall["rows"]),
        "waiting_rows": int(overall["waiting_rows"]),
        "rerun_allowed_rows": int(overall["rerun_allowed_rows"]),
        "validation_failed_rows": int(overall["validation_failed_rows"]),
        "required_evidence_problem_rows": int(overall["required_evidence_problem_rows"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "preflight": str(preflight_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
