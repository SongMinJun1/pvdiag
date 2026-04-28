#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-109"
DEFAULT_BR107_ROOT = "/private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check"
DEFAULT_BR108_ROOT = "/private/tmp/mlpe_field_trial_partial_capture_failure_matrix_br108_check"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_pre_adjudication_dry_run_gate_br109_check"

GATE_OUTPUT_NAME = "mlpe_field_trial_pre_adjudication_dry_run_gate_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_pre_adjudication_dry_run_gate_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_pre_adjudication_dry_run_gate_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_pre_adjudication_dry_run_gate_v1.json"


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)


def add_check(rows: list[dict[str, object]], check_id: str, check_name: str, passed: bool, observed: object, expected: object) -> None:
    rows.append(
        {
            "owner_branch": OWNER_BRANCH,
            "check_id": check_id,
            "check_name": check_name,
            "passed_flag": int(bool(passed)),
            "observed_value": observed,
            "expected_value": expected,
            "truth_intake_allowed": 0,
            "threshold_patch_allowed": 0,
            "engine_patch_allowed": 0,
        }
    )


def build_gate(br107_root: Path, br108_root: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    br107_fixture = read_csv_or_empty(br107_root / "mlpe_field_trial_filled_capture_fixture_v1.csv")
    br107_readiness = read_csv_or_empty(br107_root / "readiness/mlpe_field_trial_capture_readiness_packet_v1.csv")
    br107_guard = read_csv_or_empty(br107_root / "guard/mlpe_field_trial_adjudication_handoff_guard_v1.csv")
    br108_expected = read_csv_or_empty(br108_root / "mlpe_field_trial_partial_capture_expected_buckets_v1.csv")
    br108_readiness = read_csv_or_empty(br108_root / "readiness/mlpe_field_trial_capture_readiness_packet_v1.csv")
    br108_guard = read_csv_or_empty(br108_root / "guard/mlpe_field_trial_adjudication_handoff_guard_v1.csv")

    add_check(rows, "BR109-001", "br107_fixture_rows", len(br107_fixture) == 14, len(br107_fixture), 14)
    add_check(
        rows,
        "BR109-002",
        "br107_all_capture_ready",
        (not br107_readiness.empty) and set(br107_readiness["readiness_bucket"]) == {"capture_ready_label_pending"},
        sorted(set(br107_readiness["readiness_bucket"])) if not br107_readiness.empty else "missing",
        "capture_ready_label_pending only",
    )
    add_check(
        rows,
        "BR109-003",
        "br107_all_handoff_allowed",
        (not br107_guard.empty) and int(br107_guard["adjudication_handoff_allowed"].sum()) == 14,
        int(br107_guard["adjudication_handoff_allowed"].sum()) if not br107_guard.empty else "missing",
        14,
    )
    add_check(
        rows,
        "BR109-004",
        "br107_truth_still_blocked",
        (not br107_guard.empty) and int(br107_guard["truth_intake_allowed"].sum()) == 0,
        int(br107_guard["truth_intake_allowed"].sum()) if not br107_guard.empty else "missing",
        0,
    )
    if br108_expected.empty or br108_readiness.empty or br108_guard.empty:
        add_check(rows, "BR109-005", "br108_expected_outputs_present", False, "missing", "present")
        add_check(rows, "BR109-006", "br108_expected_buckets_match", False, "missing", "all match")
        add_check(rows, "BR109-007", "br108_handoff_allowed_one", False, "missing", 1)
        add_check(rows, "BR109-008", "br108_truth_still_blocked", False, "missing", 0)
    else:
        guard_cols = br108_guard[["trial_event_id", "guard_bucket", "adjudication_handoff_allowed", "truth_intake_allowed"]].rename(
            columns={"truth_intake_allowed": "guard_truth_intake_allowed"}
        )
        merged = br108_expected.merge(br108_readiness[["trial_event_id", "readiness_bucket"]], on="trial_event_id", how="left")
        merged = merged.merge(guard_cols, on="trial_event_id", how="left")
        readiness_match = bool((merged["expected_readiness_bucket"] == merged["readiness_bucket"]).all())
        guard_match = bool((merged["expected_guard_bucket"] == merged["guard_bucket"]).all())
        add_check(rows, "BR109-005", "br108_expected_outputs_present", True, len(merged), len(br108_expected))
        add_check(rows, "BR109-006", "br108_expected_buckets_match", readiness_match and guard_match, f"readiness={readiness_match};guard={guard_match}", "both true")
        add_check(rows, "BR109-007", "br108_handoff_allowed_one", int(merged["adjudication_handoff_allowed"].sum()) == 1, int(merged["adjudication_handoff_allowed"].sum()), 1)
        add_check(rows, "BR109-008", "br108_truth_still_blocked", int(merged["guard_truth_intake_allowed"].sum()) == 0, int(merged["guard_truth_intake_allowed"].sum()), 0)
    return pd.DataFrame(rows)


def build_summary(gate: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "gate_rows": int(len(gate)),
                "passed_rows": int(gate["passed_flag"].sum()),
                "failed_rows": int((gate["passed_flag"] == 0).sum()),
                "overall_passed_flag": int(gate["passed_flag"].all()),
                "truth_intake_allowed_sum": int(gate["truth_intake_allowed"].sum()),
                "threshold_patch_allowed_sum": int(gate["threshold_patch_allowed"].sum()),
                "engine_patch_allowed_sum": int(gate["engine_patch_allowed"].sum()),
            }
        ]
    )


def write_note(output_dir: Path, summary: pd.DataFrame) -> Path:
    row = summary.iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-109 MLPE Field-Trial Pre-Adjudication Dry-Run Gate",
        "",
        "## Purpose",
        "- Require the BR-107 positive fixture and BR-108 failure matrix to pass before real capture rows are accepted for adjudication review.",
        "- Keep dry-run gate pass separate from truth intake.",
        "",
        "## Real Result",
        f"- gate rows: `{row['gate_rows']}`",
        f"- passed rows: `{row['passed_rows']}`",
        f"- failed rows: `{row['failed_rows']}`",
        f"- overall passed flag: `{row['overall_passed_flag']}`",
        f"- truth intake allowed sum: `{row['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{row['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{row['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Passing this gate means plumbing is healthy.",
        "- Passing this gate does not create labels or approve thresholds/engine edits.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--br107-root", default=DEFAULT_BR107_ROOT)
    parser.add_argument("--br108-root", default=DEFAULT_BR108_ROOT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    br107_root = resolve_path(repo_root, args.br107_root)
    br108_root = resolve_path(repo_root, args.br108_root)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gate = build_gate(br107_root, br108_root)
    summary = build_summary(gate)

    gate_path = output_dir / GATE_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    gate.to_csv(gate_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    overall = summary.iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "gate_rows": int(overall["gate_rows"]),
        "passed_rows": int(overall["passed_rows"]),
        "failed_rows": int(overall["failed_rows"]),
        "overall_passed_flag": int(overall["overall_passed_flag"]),
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
