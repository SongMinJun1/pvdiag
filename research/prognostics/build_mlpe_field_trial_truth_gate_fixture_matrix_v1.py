#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-118"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_truth_gate_fixture_matrix_br118_check"

LABEL_INPUT_NAME = "mlpe_field_trial_truth_gate_fixture_labels_v1.csv"
VALIDATION_INPUT_NAME = "mlpe_field_trial_truth_gate_fixture_validation_v1.csv"
MATRIX_OUTPUT_NAME = "mlpe_field_trial_truth_gate_fixture_matrix_v1.csv"
MISMATCH_OUTPUT_NAME = "mlpe_field_trial_truth_gate_fixture_matrix_mismatches_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_truth_gate_fixture_matrix_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_truth_gate_fixture_matrix_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_truth_gate_fixture_matrix_v1.json"

GATE_OUTPUT_NAME = "mlpe_field_trial_label_to_truth_gate_v1.csv"

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

EXPECTATION_COLUMNS = [
    "case_id",
    "scenario_group",
    "trial_event_id",
    "expected_truth_gate_ready_flag",
    "expected_truth_gate_blocked_flag",
    "expected_truth_candidate_role",
    "expected_truth_gate_bucket",
    "expected_blocker_contains",
]


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def make_label(
    case_id: str,
    truth_confidence: str,
    common_clearance: str,
    artifact_clearance: str,
    *,
    family: str = "panel_surface_environment_fault",
    subtype: str = "partial_shading",
    source: str = "manual_expert_review",
) -> dict[str, object]:
    return {
        "trial_event_id": case_id,
        "reviewer_final_fault_family": family,
        "reviewer_final_fault_subtype": subtype,
        "reviewer_truth_confidence": truth_confidence,
        "reviewer_common_cause_clearance": common_clearance,
        "reviewer_measurement_artifact_clearance": artifact_clearance,
        "reviewer_label_source": source,
        "reviewer": "br118_fixture_reviewer",
        "reviewed_at": "2026-04-25T00:00:00Z",
        "reviewer_notes": f"BR-118 synthetic fixture case {case_id}",
    }


def make_validation(
    case_id: str,
    *,
    complete: int = 1,
    failed: int = 0,
    candidate: int = 1,
    bucket: str = "label_valid_truth_gate_required",
) -> dict[str, object]:
    return {
        "trial_event_id": case_id,
        "reviewer_label_complete_flag": complete,
        "label_validation_failed_flag": failed,
        "truth_gate_candidate_flag": candidate,
        "label_validation_bucket": bucket,
    }


def make_expected(
    case_id: str,
    scenario_group: str,
    *,
    ready: int,
    role: str,
    bucket: str,
    blocker_contains: str = "",
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "scenario_group": scenario_group,
        "trial_event_id": case_id,
        "expected_truth_gate_ready_flag": ready,
        "expected_truth_gate_blocked_flag": int(not ready),
        "expected_truth_candidate_role": role,
        "expected_truth_gate_bucket": bucket,
        "expected_blocker_contains": blocker_contains,
    }


def build_fixture_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    labels: list[dict[str, object]] = []
    validations: list[dict[str, object]] = []
    expected: list[dict[str, object]] = []

    pass_cases = [
        (
            "PASS_CONFIRMED_INJECTED",
            "confirmed_injected",
            "positive_truth_candidate",
            "panel_surface_environment_fault",
            "partial_shading",
        ),
        (
            "PASS_CONFIRMED_OBSERVED",
            "confirmed_observed",
            "positive_truth_candidate",
            "panel_surface_environment_fault",
            "partial_shading",
        ),
        (
            "PASS_NEGATIVE_CONTROL",
            "negative_control",
            "negative_truth_candidate",
            "normal",
            "normal_clear_day_baseline",
        ),
    ]
    for case_id, confidence, role, family, subtype in pass_cases:
        labels.append(
            make_label(
                case_id,
                confidence,
                "cleared_panel_local",
                "cleared_physical",
                family=family,
                subtype=subtype,
                source="field_trial_injection_log",
            )
        )
        validations.append(make_validation(case_id))
        expected.append(
            make_expected(
                case_id,
                "pass_ready_candidate",
                ready=1,
                role=role,
                bucket="truth_gate_ready_for_truth_intake_review",
            )
        )

    for case_id, confidence in [
        ("BLOCK_CONFIDENCE_PROBABLE", "probable"),
        ("BLOCK_CONFIDENCE_AMBIGUOUS", "ambiguous"),
        ("BLOCK_CONFIDENCE_BLANK", ""),
    ]:
        labels.append(make_label(case_id, confidence, "cleared_panel_local", "cleared_physical"))
        validations.append(make_validation(case_id))
        expected.append(
            make_expected(
                case_id,
                "block_truth_confidence",
                ready=0,
                role="not_truth_candidate",
                bucket="blocked_truth_confidence_not_confirmed",
                blocker_contains="reviewer_truth_confidence=",
            )
        )

    for case_id, common_clearance in [
        ("BLOCK_COMMON_CAUSE_SUSPECTED", "common_cause_suspected"),
        ("BLOCK_COMMON_CAUSE_CONFIRMED", "common_cause_confirmed"),
        ("BLOCK_COMMON_CAUSE_UNKNOWN", "unknown"),
    ]:
        labels.append(make_label(case_id, "confirmed_injected", common_clearance, "cleared_physical"))
        validations.append(make_validation(case_id))
        expected.append(
            make_expected(
                case_id,
                "block_common_cause_clearance",
                ready=0,
                role="not_truth_candidate",
                bucket="blocked_common_cause_not_cleared",
                blocker_contains="reviewer_common_cause_clearance=",
            )
        )

    for case_id, artifact_clearance in [
        ("BLOCK_ARTIFACT_SUSPECTED", "measurement_artifact_suspected"),
        ("BLOCK_ARTIFACT_CONFIRMED", "measurement_artifact_confirmed"),
        ("BLOCK_ARTIFACT_UNKNOWN", "unknown"),
    ]:
        labels.append(make_label(case_id, "confirmed_injected", "cleared_panel_local", artifact_clearance))
        validations.append(make_validation(case_id))
        expected.append(
            make_expected(
                case_id,
                "block_measurement_artifact_clearance",
                ready=0,
                role="not_truth_candidate",
                bucket="blocked_measurement_artifact_not_cleared",
                blocker_contains="reviewer_measurement_artifact_clearance=",
            )
        )

    validation_failures = [
        (
            "BLOCK_VALIDATION_FAILED",
            {"complete": 1, "failed": 1, "candidate": 0, "bucket": "blocked_required_fields_missing"},
        ),
        (
            "BLOCK_VALIDATION_INCOMPLETE",
            {"complete": 0, "failed": 1, "candidate": 0, "bucket": "blocked_required_fields_missing"},
        ),
        (
            "BLOCK_VALIDATION_CANDIDATE_ZERO",
            {"complete": 1, "failed": 0, "candidate": 0, "bucket": "blocked_not_truth_gate_candidate"},
        ),
    ]
    for case_id, validation_kwargs in validation_failures:
        labels.append(make_label(case_id, "confirmed_injected", "cleared_panel_local", "cleared_physical"))
        validations.append(make_validation(case_id, **validation_kwargs))
        expected.append(
            make_expected(
                case_id,
                "block_label_validation",
                ready=0,
                role="not_truth_candidate",
                bucket="blocked_label_validation_not_passed",
                blocker_contains=str(validation_kwargs["bucket"]),
            )
        )

    missing_validation_case = "BLOCK_MISSING_VALIDATION"
    labels.append(make_label(missing_validation_case, "confirmed_injected", "cleared_panel_local", "cleared_physical"))
    expected.append(
        make_expected(
            missing_validation_case,
            "block_missing_validation",
            ready=0,
            role="not_truth_candidate",
            bucket="blocked_missing_label_validation",
            blocker_contains="missing_label_validation",
        )
    )

    return (
        pd.DataFrame(labels).reindex(columns=LABEL_COLUMNS),
        pd.DataFrame(validations).reindex(columns=VALIDATION_COLUMNS),
        pd.DataFrame(expected).reindex(columns=EXPECTATION_COLUMNS),
    )


def run_gate_builder(repo_root: Path, label_path: Path, validation_path: Path, gate_dir: Path) -> dict[str, object]:
    builder = repo_root / "research/prognostics/build_mlpe_field_trial_label_to_truth_gate_v1.py"
    if not builder.exists():
        raise FileNotFoundError(f"missing BR-117 gate builder: {builder}")
    proc = subprocess.run(
        [
            sys.executable,
            str(builder),
            "--repo-root",
            str(repo_root),
            "--label-input",
            str(label_path),
            "--label-validation",
            str(validation_path),
            "--output-dir",
            str(gate_dir),
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    return json.loads(proc.stdout)


def as_int(value: object) -> int:
    if pd.isna(value):
        return 0
    return int(float(str(value).strip() or "0"))


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def compare_matrix(expectation: pd.DataFrame, gate: pd.DataFrame) -> pd.DataFrame:
    merged = expectation.merge(gate, on="trial_event_id", how="left", suffixes=("", "_actual"))
    rows = []
    for _, row in merged.iterrows():
        actual_ready = as_int(row.get("truth_gate_ready_flag", 0))
        actual_blocked = as_int(row.get("truth_gate_blocked_flag", 0))
        actual_role = normalize_text(row.get("truth_candidate_role", ""))
        actual_bucket = normalize_text(row.get("truth_gate_bucket", ""))
        actual_blocker = normalize_text(row.get("blocker_reason", ""))
        expected_blocker_contains = normalize_text(row.get("expected_blocker_contains", ""))

        ready_match = actual_ready == as_int(row["expected_truth_gate_ready_flag"])
        blocked_match = actual_blocked == as_int(row["expected_truth_gate_blocked_flag"])
        role_match = actual_role == normalize_text(row["expected_truth_candidate_role"])
        bucket_match = actual_bucket == normalize_text(row["expected_truth_gate_bucket"])
        if expected_blocker_contains:
            blocker_match = expected_blocker_contains in actual_blocker
        else:
            blocker_match = actual_blocker == ""
        case_pass = int(ready_match and blocked_match and role_match and bucket_match and blocker_match)

        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "case_id": row["case_id"],
                "scenario_group": row["scenario_group"],
                "trial_event_id": row["trial_event_id"],
                "expected_truth_gate_ready_flag": as_int(row["expected_truth_gate_ready_flag"]),
                "actual_truth_gate_ready_flag": actual_ready,
                "expected_truth_gate_blocked_flag": as_int(row["expected_truth_gate_blocked_flag"]),
                "actual_truth_gate_blocked_flag": actual_blocked,
                "expected_truth_candidate_role": normalize_text(row["expected_truth_candidate_role"]),
                "actual_truth_candidate_role": actual_role,
                "expected_truth_gate_bucket": normalize_text(row["expected_truth_gate_bucket"]),
                "actual_truth_gate_bucket": actual_bucket,
                "expected_blocker_contains": expected_blocker_contains,
                "actual_blocker_reason": actual_blocker,
                "ready_match_flag": int(ready_match),
                "blocked_match_flag": int(blocked_match),
                "role_match_flag": int(role_match),
                "bucket_match_flag": int(bucket_match),
                "blocker_match_flag": int(blocker_match),
                "case_pass_flag": case_pass,
                "truth_intake_allowed": as_int(row.get("truth_intake_allowed", 0)),
                "threshold_patch_allowed": as_int(row.get("threshold_patch_allowed", 0)),
                "engine_patch_allowed": as_int(row.get("engine_patch_allowed", 0)),
            }
        )
    return pd.DataFrame(rows)


def build_summary(matrix: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "fixture_rows": int(len(matrix)),
            "case_pass_rows": int(matrix["case_pass_flag"].sum()) if len(matrix) else 0,
            "mismatch_rows": int((matrix["case_pass_flag"] == 0).sum()) if len(matrix) else 0,
            "expected_ready_rows": int(matrix["expected_truth_gate_ready_flag"].sum()) if len(matrix) else 0,
            "actual_ready_rows": int(matrix["actual_truth_gate_ready_flag"].sum()) if len(matrix) else 0,
            "expected_blocked_rows": int(matrix["expected_truth_gate_blocked_flag"].sum()) if len(matrix) else 0,
            "actual_blocked_rows": int(matrix["actual_truth_gate_blocked_flag"].sum()) if len(matrix) else 0,
            "truth_intake_allowed_sum": int(matrix["truth_intake_allowed"].sum()) if len(matrix) else 0,
            "threshold_patch_allowed_sum": int(matrix["threshold_patch_allowed"].sum()) if len(matrix) else 0,
            "engine_patch_allowed_sum": int(matrix["engine_patch_allowed"].sum()) if len(matrix) else 0,
        }
    ]
    if len(matrix):
        for group, sub in matrix.groupby("scenario_group", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "scenario_group",
                    "summary_key": group,
                    "fixture_rows": int(len(sub)),
                    "case_pass_rows": int(sub["case_pass_flag"].sum()),
                    "mismatch_rows": int((sub["case_pass_flag"] == 0).sum()),
                    "expected_ready_rows": int(sub["expected_truth_gate_ready_flag"].sum()),
                    "actual_ready_rows": int(sub["actual_truth_gate_ready_flag"].sum()),
                    "expected_blocked_rows": int(sub["expected_truth_gate_blocked_flag"].sum()),
                    "actual_blocked_rows": int(sub["actual_truth_gate_blocked_flag"].sum()),
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
        "# BR-118 MLPE Field-Trial Truth-Gate Fixture Matrix",
        "",
        "## Purpose",
        "- Lock a synthetic pass/fail matrix around the BR-117 label-to-truth gate.",
        "- Verify that only confirmed positive and negative-control labels with clearances become truth-intake review candidates.",
        "- Keep all truth, threshold, and engine approvals locked at `0`.",
        "",
        "## Result",
        f"- fixture rows: `{overall['fixture_rows']}`",
        f"- case-pass rows: `{overall['case_pass_rows']}`",
        f"- mismatch rows: `{overall['mismatch_rows']}`",
        f"- expected/actual ready rows: `{overall['expected_ready_rows']}` / `{overall['actual_ready_rows']}`",
        f"- expected/actual blocked rows: `{overall['expected_blocked_rows']}` / `{overall['actual_blocked_rows']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- This is a synthetic fixture gate, not field truth.",
        "- Passing fixture rows prove the gate contract is stable, not that any real panel has been labeled.",
        "- `panel_day_engine.py` remains untouched.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    labels, validations, expectation = build_fixture_inputs()
    label_path = output_dir / LABEL_INPUT_NAME
    validation_path = output_dir / VALIDATION_INPUT_NAME
    gate_dir = output_dir / "br117_gate_outputs"
    labels.to_csv(label_path, index=False, encoding="utf-8-sig")
    validations.to_csv(validation_path, index=False, encoding="utf-8-sig")

    gate_payload = run_gate_builder(repo_root, label_path, validation_path, gate_dir)
    gate = pd.read_csv(gate_dir / GATE_OUTPUT_NAME, encoding="utf-8-sig", low_memory=False)
    matrix = compare_matrix(expectation, gate)
    mismatches = matrix[matrix["case_pass_flag"] == 0].copy()
    summary = build_summary(matrix)

    matrix_path = output_dir / MATRIX_OUTPUT_NAME
    mismatch_path = output_dir / MISMATCH_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    matrix.to_csv(matrix_path, index=False, encoding="utf-8-sig")
    mismatches.to_csv(mismatch_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "fixture_rows": int(overall["fixture_rows"]),
        "case_pass_rows": int(overall["case_pass_rows"]),
        "mismatch_rows": int(overall["mismatch_rows"]),
        "expected_ready_rows": int(overall["expected_ready_rows"]),
        "actual_ready_rows": int(overall["actual_ready_rows"]),
        "expected_blocked_rows": int(overall["expected_blocked_rows"]),
        "actual_blocked_rows": int(overall["actual_blocked_rows"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "br117_gate_payload": gate_payload,
        "outputs": {
            "fixture_labels": str(label_path),
            "fixture_validation": str(validation_path),
            "matrix": str(matrix_path),
            "mismatches": str(mismatch_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
