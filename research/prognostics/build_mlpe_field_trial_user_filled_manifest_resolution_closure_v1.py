#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


OWNER_BRANCH = "BR-20260429-209"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_user_filled_manifest_resolution_closure_br209_check"

DETAIL_OUTPUT_NAME = "mlpe_field_trial_user_filled_manifest_resolution_closure_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_user_filled_manifest_resolution_closure_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_user_filled_manifest_resolution_closure_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_user_filled_manifest_resolution_closure_v1.json"

ACTIVE_REGISTER = "docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md"

EXPECTED_CONSUMERS = [
    {
        "branch": "BR-20260429-202",
        "consumer": "build_mlpe_field_trial_capture_return_validator_v1.py",
        "smoke": "smoke_test_mlpe_field_trial_capture_return_validator_v1.py",
        "doc": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_202_MLPE_CAPTURE_RETURN_VALIDATOR_MANIFEST_RESOLUTION_V1.md",
        "flag": "--returned-capture",
        "key": "returned_capture",
        "resolver": "resolve_returned_capture_input",
    },
    {
        "branch": "BR-20260429-203",
        "consumer": "build_mlpe_field_trial_capture_return_evidence_resolver_v1.py",
        "smoke": "smoke_test_mlpe_field_trial_capture_return_evidence_resolver_v1.py",
        "doc": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_203_MLPE_CAPTURE_RETURN_EVIDENCE_RESOLVER_MANIFEST_RESOLUTION_V1.md",
        "flag": "--returned-capture",
        "key": "returned_capture",
        "resolver": "resolve_returned_capture_input",
    },
    {
        "branch": "BR-20260429-204",
        "consumer": "build_mlpe_field_trial_final_label_validator_v1.py",
        "smoke": "smoke_test_mlpe_field_trial_final_label_validator_v1.py",
        "doc": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_204_MLPE_FINAL_LABEL_VALIDATOR_MANIFEST_RESOLUTION_V1.md",
        "flag": "--label-input",
        "key": "label_input",
        "resolver": "resolve_label_input",
    },
    {
        "branch": "BR-20260429-205",
        "consumer": "build_mlpe_field_trial_label_to_truth_gate_v1.py",
        "smoke": "smoke_test_mlpe_field_trial_label_to_truth_gate_v1.py",
        "doc": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_205_MLPE_LABEL_TO_TRUTH_GATE_MANIFEST_RESOLUTION_V1.md",
        "flag": "--label-input",
        "key": "label_input",
        "resolver": "resolve_label_input",
    },
    {
        "branch": "BR-20260429-206",
        "consumer": "build_mlpe_field_trial_real_label_intake_runbook_v1.py",
        "smoke": "smoke_test_mlpe_field_trial_real_label_intake_runbook_v1.py",
        "doc": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_206_MLPE_REAL_LABEL_INTAKE_RUNBOOK_MANIFEST_RESOLUTION_V1.md",
        "flag": "--label-input",
        "key": "label_input",
        "resolver": "resolve_label_input",
    },
    {
        "branch": "BR-20260429-207",
        "consumer": "build_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py",
        "smoke": "smoke_test_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py",
        "doc": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_207_MLPE_TRUTH_INTAKE_PREFLIGHT_REVIEW_MANIFEST_RESOLUTION_V1.md",
        "flag": "--reviewed-checklist",
        "key": "reviewed_checklist",
        "resolver": "resolve_reviewed_checklist_input",
    },
    {
        "branch": "BR-20260429-208",
        "consumer": "build_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py",
        "smoke": "smoke_test_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py",
        "doc": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_208_MLPE_TRUTH_SEED_REVIEWER_DECISION_MANIFEST_RESOLUTION_V1.md",
        "flag": "--decision-input",
        "key": "decision_input",
        "resolver": "resolve_decision_input",
    },
]

DETAIL_COLUMNS = [
    "owner_branch",
    "branch",
    "consumer",
    "input_flag",
    "manifest_key",
    "consumer_exists",
    "smoke_exists",
    "doc_exists",
    "active_register_mentions_branch",
    "has_guard_call",
    "has_input_manifest_arg",
    "has_manifest_loader",
    "has_manifest_path_reader",
    "has_explicit_cli_precedence",
    "has_manifest_key_resolution",
    "has_legacy_default_path",
    "records_resolution_sources",
    "smoke_covers_explicit_cli",
    "smoke_covers_manifest_path",
    "smoke_covers_explicit_override",
    "smoke_covers_fail_closed",
    "doc_records_non_semantic_boundary",
    "operator_facing_change_allowed",
    "truth_write_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "closure_status",
    "missing_checks",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "expected_consumer_count",
    "manifest_binding_count",
    "distinct_manifest_key_count",
    "closure_pass_count",
    "closure_fail_count",
    "unresolved_manifest_consumer_count",
    "missing_check_count",
    "operator_facing_change_allowed_sum",
    "truth_write_allowed_sum",
    "threshold_patch_allowed_sum",
    "engine_patch_allowed_sum",
    "closure_complete",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def as_int(value: bool) -> int:
    return 1 if value else 0


def build_detail(repo_root: Path) -> list[dict[str, object]]:
    active_register_text = read_text(resolve_path(repo_root, ACTIVE_REGISTER))
    rows: list[dict[str, object]] = []

    for spec in EXPECTED_CONSUMERS:
        consumer_path = repo_root / "research/prognostics" / spec["consumer"]
        smoke_path = repo_root / "research/prognostics" / spec["smoke"]
        doc_path = resolve_path(repo_root, spec["doc"])
        consumer_text = read_text(consumer_path)
        smoke_text = read_text(smoke_path)
        doc_text = read_text(doc_path)
        key = spec["key"]
        flag = spec["flag"]

        checks = {
            "consumer_exists": consumer_path.exists(),
            "smoke_exists": smoke_path.exists(),
            "doc_exists": doc_path.exists(),
            "active_register_mentions_branch": spec["branch"] in active_register_text,
            "has_guard_call": "require_explicit_user_filled_input" in consumer_text,
            "has_input_manifest_arg": "--input-manifest" in consumer_text,
            "has_manifest_loader": "load_input_manifest" in consumer_text,
            "has_manifest_path_reader": "manifest_path_value" in consumer_text,
            "has_explicit_cli_precedence": flag in consumer_text and "explicit_cli" in consumer_text,
            "has_manifest_key_resolution": key in consumer_text and "input_manifest" in consumer_text,
            "has_legacy_default_path": "legacy_default" in consumer_text,
            "records_resolution_sources": "input_resolution_sources" in consumer_text,
            "smoke_covers_explicit_cli": "explicit_cli" in smoke_text,
            "smoke_covers_manifest_path": "--input-manifest" in smoke_text and "input_manifest" in smoke_text,
            "smoke_covers_explicit_override": "bad_" in smoke_text and "explicit_cli" in smoke_text,
            "smoke_covers_fail_closed": f"missing `{key}`" in smoke_text,
            "doc_records_non_semantic_boundary": (
                "operator-facing behavior" in doc_text
                and "pv_ae/panel_day_engine.py" in doc_text
                and "threshold" in doc_text
                and "engine" in doc_text
            ),
        }
        missing = [name for name, passed in checks.items() if not passed]
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "branch": spec["branch"],
                "consumer": spec["consumer"],
                "input_flag": flag,
                "manifest_key": key,
                **{name: as_int(value) for name, value in checks.items()},
                "operator_facing_change_allowed": 0,
                "truth_write_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "closure_status": "closed" if not missing else "needs_followup",
                "missing_checks": "; ".join(missing),
            }
        )
    return rows


def build_summary(detail_rows: list[dict[str, object]]) -> dict[str, object]:
    missing_check_count = sum(
        0 if not str(row["missing_checks"]) else len(str(row["missing_checks"]).split("; "))
        for row in detail_rows
    )
    closure_fail_count = sum(1 for row in detail_rows if row["closure_status"] != "closed")
    return {
        "owner_branch": OWNER_BRANCH,
        "expected_consumer_count": len(detail_rows),
        "manifest_binding_count": len(detail_rows),
        "distinct_manifest_key_count": len({str(row["manifest_key"]) for row in detail_rows}),
        "closure_pass_count": sum(1 for row in detail_rows if row["closure_status"] == "closed"),
        "closure_fail_count": closure_fail_count,
        "unresolved_manifest_consumer_count": closure_fail_count,
        "missing_check_count": missing_check_count,
        "operator_facing_change_allowed_sum": sum(int(row["operator_facing_change_allowed"]) for row in detail_rows),
        "truth_write_allowed_sum": sum(int(row["truth_write_allowed"]) for row in detail_rows),
        "threshold_patch_allowed_sum": sum(int(row["threshold_patch_allowed"]) for row in detail_rows),
        "engine_patch_allowed_sum": sum(int(row["engine_patch_allowed"]) for row in detail_rows),
        "closure_complete": as_int(closure_fail_count == 0 and missing_check_count == 0),
    }


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def write_note(output_dir: Path, summary: dict[str, object]) -> Path:
    lines = [
        "# BR-209 MLPE User-Filled Manifest Resolution Closure",
        "",
        "## Purpose",
        "- Close the MLPE field-trial user-filled input manifest-resolution lane with a reproducible static audit.",
        "- Verify that all seven guarded user-filled consumers support explicit CLI input, optional manifest input, source recording, override precedence, and fail-closed smoke coverage.",
        "- Keep this closure audit non-semantic: no runtime, truth, threshold, engine, or operator-facing behavior change.",
        "",
        "## Outputs",
        f"- `{output_dir / DETAIL_OUTPUT_NAME}`",
        f"- `{output_dir / SUMMARY_OUTPUT_NAME}`",
        f"- `{output_dir / JSON_OUTPUT_NAME}`",
        "",
        "## Result",
        f"- owner_branch: `{summary['owner_branch']}`",
        f"- expected consumers: `{summary['expected_consumer_count']}`",
        f"- manifest bindings: `{summary['manifest_binding_count']}`",
        f"- distinct manifest keys: `{summary['distinct_manifest_key_count']}`",
        f"- closed consumers: `{summary['closure_pass_count']}`",
        f"- failed consumers: `{summary['closure_fail_count']}`",
        f"- unresolved manifest consumers: `{summary['unresolved_manifest_consumer_count']}`",
        f"- missing checks: `{summary['missing_check_count']}`",
        f"- operator-facing change allowed sum: `{summary['operator_facing_change_allowed_sum']}`",
        f"- truth write allowed sum: `{summary['truth_write_allowed_sum']}`",
        f"- threshold patch allowed sum: `{summary['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{summary['engine_patch_allowed_sum']}`",
        f"- closure complete: `{summary['closure_complete']}`",
        "",
        "## Reading",
        "- `closure_complete=1` means the BR-202..BR-208 guarded user-filled consumer list is manifest-aware and smoke-covered.",
        "- This audit does not regenerate reviewer artifacts and does not approve canonical truth, thresholds, engine patches, or operator-facing semantics.",
        "- New user-filled MLPE inputs should be added to this audit before relying on temp defaults.",
    ]
    path = output_dir / NOTE_OUTPUT_NAME
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    detail_rows = build_detail(repo_root)
    summary = build_summary(detail_rows)

    detail_path = output_dir / DETAIL_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    note_path = output_dir / NOTE_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    write_csv(detail_path, detail_rows, DETAIL_COLUMNS)
    write_csv(summary_path, [summary], SUMMARY_COLUMNS)
    note_path = write_note(output_dir, summary)
    payload = {
        **summary,
        "outputs": {
            "detail": str(detail_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
        "recommended_next_branch": "mlpe_user_filled_manifest_resolution_closed_continue_next_cleanup_lane",
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
