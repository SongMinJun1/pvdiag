#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-119"
DEFAULT_LABEL_INPUT = "/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_template_v1.csv"
DEFAULT_SCHEMA = "/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_schema_v1.csv"
DEFAULT_ALLOWED_VALUES = "/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_allowed_values_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_real_label_intake_runbook_br119_check"

RUNBOOK_OUTPUT_NAME = "mlpe_field_trial_real_label_intake_runbook_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_real_label_intake_runbook_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_real_label_intake_runbook_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_real_label_intake_runbook_v1.json"

BR116_VALIDATION_OUTPUT_NAME = "mlpe_field_trial_final_label_validation_v1.csv"

RUNBOOK_COLUMNS = [
    "owner_branch",
    "stage_order",
    "stage_id",
    "stage_status",
    "hard_stop_flag",
    "label_rows",
    "ready_rows",
    "blocked_rows",
    "mismatch_rows",
    "truth_seed_review_candidate_rows",
    "truth_intake_allowed_sum",
    "threshold_patch_allowed_sum",
    "engine_patch_allowed_sum",
    "input_path",
    "output_path",
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


def run_json(repo_root: Path, script_rel: str, args: list[str]) -> dict[str, object]:
    script = repo_root / script_rel
    if not script.exists():
        raise FileNotFoundError(f"missing script: {script}")
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    return json.loads(proc.stdout)


def int_payload(payload: dict[str, object], key: str) -> int:
    return int(payload.get(key, 0) or 0)


def stage_row(
    *,
    stage_order: int,
    stage_id: str,
    stage_status: str,
    hard_stop: int,
    label_rows: int = 0,
    ready_rows: int = 0,
    blocked_rows: int = 0,
    mismatch_rows: int = 0,
    review_candidates: int = 0,
    truth_allowed: int = 0,
    threshold_allowed: int = 0,
    engine_allowed: int = 0,
    input_path: str = "",
    output_path: str = "",
    next_action: str = "",
) -> dict[str, object]:
    return {
        "owner_branch": OWNER_BRANCH,
        "stage_order": stage_order,
        "stage_id": stage_id,
        "stage_status": stage_status,
        "hard_stop_flag": hard_stop,
        "label_rows": label_rows,
        "ready_rows": ready_rows,
        "blocked_rows": blocked_rows,
        "mismatch_rows": mismatch_rows,
        "truth_seed_review_candidate_rows": review_candidates,
        "truth_intake_allowed_sum": truth_allowed,
        "threshold_patch_allowed_sum": threshold_allowed,
        "engine_patch_allowed_sum": engine_allowed,
        "input_path": input_path,
        "output_path": output_path,
        "next_action": next_action,
    }


def build_runbook(
    label_path: Path,
    schema_path: Path,
    allowed_values_path: Path,
    fixture_payload: dict[str, object],
    validation_payload: dict[str, object],
    gate_payload: dict[str, object],
) -> pd.DataFrame:
    fixture_mismatches = int_payload(fixture_payload, "mismatch_rows")
    fixture_ready = int_payload(fixture_payload, "actual_ready_rows")
    fixture_blocked = int_payload(fixture_payload, "actual_blocked_rows")
    label_rows = int_payload(validation_payload, "label_rows")
    valid_rows = int_payload(validation_payload, "valid_label_rows")
    validation_failed = int_payload(validation_payload, "validation_failed_rows")
    issue_rows = int_payload(validation_payload, "issue_rows")
    gate_ready = int_payload(gate_payload, "truth_gate_ready_rows")
    gate_blocked = int_payload(gate_payload, "truth_gate_blocked_rows")
    truth_review_candidates = gate_ready if fixture_mismatches == 0 else 0

    if fixture_mismatches:
        fixture_status = "failed_fixture_contract_mismatch"
        fixture_next = "Fix BR-117/BR-118 gate contract before reading real labels."
    else:
        fixture_status = "passed_fixture_contract"
        fixture_next = "Proceed to real label validation."

    if label_rows == 0:
        validation_status = "waiting_for_real_label_csv"
        validation_next = "Fill BR-115 label template from KTC ESS field-trial evidence, then rerun BR-119."
    elif validation_failed:
        validation_status = "completed_with_blocked_label_rows"
        validation_next = "Send valid rows to BR-117 gate; fix invalid rows before reuse."
    else:
        validation_status = "passed_label_validation"
        validation_next = "Send valid rows to BR-117 label-to-truth gate."

    if label_rows == 0:
        gate_status = "waiting_for_real_label_csv"
        gate_next = "No truth-gate rows exist until real labels are supplied."
    elif gate_ready:
        gate_status = "truth_gate_ready_review_candidates_present"
        gate_next = "Review ready rows as sidecar truth-seed candidates; do not write canonical truth."
    else:
        gate_status = "truth_gate_all_rows_blocked"
        gate_next = "Resolve gate blockers before truth-seed review."

    return pd.DataFrame(
        [
            stage_row(
                stage_order=1,
                stage_id="br118_fixture_contract",
                stage_status=fixture_status,
                hard_stop=int(bool(fixture_mismatches)),
                ready_rows=fixture_ready,
                blocked_rows=fixture_blocked,
                mismatch_rows=fixture_mismatches,
                input_path="synthetic_fixture",
                output_path=str(fixture_payload["outputs"]["matrix"]),
                next_action=fixture_next,
            ),
            stage_row(
                stage_order=2,
                stage_id="br116_real_label_validation",
                stage_status=validation_status,
                hard_stop=int(bool(fixture_mismatches)),
                label_rows=label_rows,
                ready_rows=valid_rows,
                blocked_rows=validation_failed,
                truth_allowed=int_payload(validation_payload, "truth_intake_allowed_sum"),
                threshold_allowed=int_payload(validation_payload, "threshold_patch_allowed_sum"),
                engine_allowed=int_payload(validation_payload, "engine_patch_allowed_sum"),
                input_path=f"{label_path};{schema_path};{allowed_values_path}",
                output_path=str(validation_payload["outputs"]["validation"]),
                next_action=f"{validation_next} issue_rows={issue_rows}",
            ),
            stage_row(
                stage_order=3,
                stage_id="br117_label_to_truth_gate",
                stage_status=gate_status,
                hard_stop=int(bool(fixture_mismatches)),
                label_rows=label_rows,
                ready_rows=gate_ready,
                blocked_rows=gate_blocked,
                review_candidates=truth_review_candidates,
                truth_allowed=int_payload(gate_payload, "truth_intake_allowed_sum"),
                threshold_allowed=int_payload(gate_payload, "threshold_patch_allowed_sum"),
                engine_allowed=int_payload(gate_payload, "engine_patch_allowed_sum"),
                input_path=f"{label_path};{validation_payload['outputs']['validation']}",
                output_path=str(gate_payload["outputs"]["gate"]),
                next_action=gate_next,
            ),
            stage_row(
                stage_order=4,
                stage_id="truth_seed_write_boundary",
                stage_status="locked_sidecar_review_only",
                hard_stop=0,
                label_rows=label_rows,
                ready_rows=truth_review_candidates,
                blocked_rows=gate_blocked,
                review_candidates=truth_review_candidates,
                truth_allowed=0,
                threshold_allowed=0,
                engine_allowed=0,
                input_path=str(gate_payload["outputs"]["gate"]),
                output_path="none",
                next_action="Keep canonical truth, threshold replay, and engine patches blocked until a later explicit review branch.",
            ),
        ]
    ).reindex(columns=RUNBOOK_COLUMNS)


def build_summary(runbook: pd.DataFrame) -> pd.DataFrame:
    fixture = runbook[runbook["stage_id"].eq("br118_fixture_contract")].iloc[0]
    validation = runbook[runbook["stage_id"].eq("br116_real_label_validation")].iloc[0]
    gate = runbook[runbook["stage_id"].eq("br117_label_to_truth_gate")].iloc[0]
    return pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "overall",
                "summary_key": "all",
                "fixture_mismatch_rows": int(fixture["mismatch_rows"]),
                "label_rows": int(validation["label_rows"]),
                "valid_label_rows": int(validation["ready_rows"]),
                "validation_blocked_rows": int(validation["blocked_rows"]),
                "truth_gate_ready_rows": int(gate["ready_rows"]),
                "truth_gate_blocked_rows": int(gate["blocked_rows"]),
                "truth_seed_review_candidate_rows": int(gate["truth_seed_review_candidate_rows"]),
                "hard_stop_rows": int(runbook["hard_stop_flag"].sum()),
                "truth_intake_allowed_sum": int(runbook["truth_intake_allowed_sum"].sum()),
                "threshold_patch_allowed_sum": int(runbook["threshold_patch_allowed_sum"].sum()),
                "engine_patch_allowed_sum": int(runbook["engine_patch_allowed_sum"].sum()),
            }
        ]
    )


def write_note(output_dir: Path, summary: pd.DataFrame) -> Path:
    row = summary.iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-119 MLPE Field-Trial Real Label Intake Runbook",
        "",
        "## Purpose",
        "- Chain BR-118 fixture contract, BR-116 label validation, and BR-117 truth gate for real KTC ESS label CSV intake.",
        "- Keep the flow executable and repeatable before any sidecar truth-seed review.",
        "- Keep canonical truth, threshold replay, and engine patches locked.",
        "",
        "## Result",
        f"- fixture mismatch rows: `{row['fixture_mismatch_rows']}`",
        f"- label rows: `{row['label_rows']}`",
        f"- valid label rows: `{row['valid_label_rows']}`",
        f"- validation-blocked rows: `{row['validation_blocked_rows']}`",
        f"- truth-gate-ready rows: `{row['truth_gate_ready_rows']}`",
        f"- truth-gate-blocked rows: `{row['truth_gate_blocked_rows']}`",
        f"- truth-seed review candidate rows: `{row['truth_seed_review_candidate_rows']}`",
        f"- hard-stop rows: `{row['hard_stop_rows']}`",
        f"- truth intake allowed sum: `{row['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{row['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{row['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Truth-seed review candidates are sidecar review candidates only.",
        "- This runbook does not write canonical truth and does not approve thresholds or engine patches.",
        "- `panel_day_engine.py` remains untouched.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--label-input", default=DEFAULT_LABEL_INPUT)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA)
    parser.add_argument("--allowed-values", default=DEFAULT_ALLOWED_VALUES)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    label_path = resolve_path(repo_root, args.label_input)
    schema_path = resolve_path(repo_root, args.schema)
    allowed_values_path = resolve_path(repo_root, args.allowed_values)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fixture_dir = output_dir / "br118_fixture_contract"
    validation_dir = output_dir / "br116_real_label_validation"
    gate_dir = output_dir / "br117_label_to_truth_gate"

    fixture_payload = run_json(
        repo_root,
        "research/prognostics/build_mlpe_field_trial_truth_gate_fixture_matrix_v1.py",
        ["--repo-root", str(repo_root), "--output-dir", str(fixture_dir)],
    )
    validation_payload = run_json(
        repo_root,
        "research/prognostics/build_mlpe_field_trial_final_label_validator_v1.py",
        [
            "--repo-root",
            str(repo_root),
            "--label-input",
            str(label_path),
            "--schema",
            str(schema_path),
            "--allowed-values",
            str(allowed_values_path),
            "--output-dir",
            str(validation_dir),
        ],
    )
    gate_payload = run_json(
        repo_root,
        "research/prognostics/build_mlpe_field_trial_label_to_truth_gate_v1.py",
        [
            "--repo-root",
            str(repo_root),
            "--label-input",
            str(label_path),
            "--label-validation",
            str(validation_dir / BR116_VALIDATION_OUTPUT_NAME),
            "--output-dir",
            str(gate_dir),
        ],
    )

    runbook = build_runbook(label_path, schema_path, allowed_values_path, fixture_payload, validation_payload, gate_payload)
    summary = build_summary(runbook)

    runbook_path = output_dir / RUNBOOK_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    runbook.to_csv(runbook_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    row = summary.iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "fixture_mismatch_rows": int(row["fixture_mismatch_rows"]),
        "label_rows": int(row["label_rows"]),
        "valid_label_rows": int(row["valid_label_rows"]),
        "validation_blocked_rows": int(row["validation_blocked_rows"]),
        "truth_gate_ready_rows": int(row["truth_gate_ready_rows"]),
        "truth_gate_blocked_rows": int(row["truth_gate_blocked_rows"]),
        "truth_seed_review_candidate_rows": int(row["truth_seed_review_candidate_rows"]),
        "hard_stop_rows": int(row["hard_stop_rows"]),
        "truth_intake_allowed_sum": int(row["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(row["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(row["engine_patch_allowed_sum"]),
        "outputs": {
            "runbook": str(runbook_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
            "fixture_contract_dir": str(fixture_dir),
            "label_validation_dir": str(validation_dir),
            "truth_gate_dir": str(gate_dir),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
