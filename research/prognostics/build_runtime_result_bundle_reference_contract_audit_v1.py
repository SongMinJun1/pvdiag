#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from build_repo_live_temp_reference_review_v1 import build_review, resolve


OWNER_BRANCH = "BR-20260429-222"
EXPECTED_RUNTIME_RESULT_BUNDLE_ROWS = 4
TARGET_LIVE_REFERENCE_KIND = "runtime_result_bundle_input"

DETAIL_OUTPUT_NAME = "runtime_result_bundle_reference_contract_audit_v1.csv"
SUMMARY_OUTPUT_NAME = "runtime_result_bundle_reference_contract_audit_summary_v1.csv"
NOTE_OUTPUT_NAME = "runtime_result_bundle_reference_contract_audit_note_v1.md"
JSON_OUTPUT_NAME = "runtime_result_bundle_reference_contract_audit_v1.json"

DETAIL_COLUMNS = [
    "owner_branch",
    "contract_id",
    "source_file",
    "line_no",
    "matched_text",
    "workflow_lane",
    "expected_manifest_keys",
    "explicit_cli_flags",
    "has_input_manifest_flag",
    "has_manifest_resolver_flag",
    "explicit_cli_arg_present_flag",
    "legacy_default_retained_flag",
    "contract_status",
    "missing_checks",
    "runtime_semantic_change_allowed_flag",
    "bulk_rewrite_allowed_flag",
    "recommended_resolution",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]

EXPECTED_CONTRACTS_BY_FILE_TEXT = {
    (
        "research/prognostics/build_panel_day_engine_common_cause_exact_seed_search_v1.py",
        "/private/tmp/conalog_mlpe_seed_expand_check/result/"  # pp-self
        "fault_panel_result_precursor_report_v1.csv",
    ): (["precursor_input"], ["--precursor-input"]),
    (
        "research/prognostics/build_panel_day_engine_common_cause_exact_seed_search_v1.py",
        "/private/tmp/conalog_mlpe_seed_expand_check/result/"  # pp-self
        "fault_panel_result_raw_only_fault_signal_report_v1.csv",
    ): (["rawonly_signal_input"], ["--rawonly-signal-input"]),
    (
        "research/prognostics/build_panel_day_engine_common_cause_manual_trace_review_v1.py",
        "/private/tmp/conalog_mlpe_seed_expand_check/result/"  # pp-self
        "fault_panel_result_precursor_report_v1.csv",
    ): (["precursor_input"], ["--precursor-input"]),
    (
        "research/prognostics/build_panel_day_engine_common_cause_manual_trace_review_v1.py",
        "/private/tmp/conalog_mlpe_seed_expand_check/result/"  # pp-self
        "fault_panel_result_raw_only_fault_signal_report_v1.csv",
    ): (["rawonly_signal_input"], ["--rawonly-signal-input"]),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit runtime result bundle input references without rewriting legacy defaults "
            "or changing common-cause evidence semantics."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for audit outputs. Required so this audit adds no temp default.",
    )
    parser.add_argument("--max-file-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def read_source(repo_root: Path, source_file: str) -> str:
    path = repo_root / source_file
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def has_manifest_resolver(source_text: str) -> int:
    resolver_names = ["resolve_manifest_input(", "resolve_chain_input(", "resolve_request_input("]
    return int(any(name in source_text for name in resolver_names))


def build_audit(repo_root: Path, max_file_bytes: int) -> list[dict[str, object]]:
    review = build_review(repo_root, max_file_bytes)
    bundle_rows = [
        row for row in review if str(row.get("live_reference_kind")) == TARGET_LIVE_REFERENCE_KIND
    ]

    out: list[dict[str, object]] = []
    for idx, row in enumerate(bundle_rows, start=1):
        source_file = str(row["source_file"])
        line_no = int(row["line_no"])
        matched_text = str(row["matched_text"])
        expected_manifest_keys, explicit_cli_flags = EXPECTED_CONTRACTS_BY_FILE_TEXT.get(
            (source_file, matched_text),
            ([], []),
        )
        source_text = read_source(repo_root, source_file)
        checks: list[str] = []
        has_input_manifest = int("--input-manifest" in source_text)
        resolver_flag = has_manifest_resolver(source_text)
        explicit_cli_arg_present = int(
            bool(explicit_cli_flags) and all(flag in source_text for flag in explicit_cli_flags)
        )
        legacy_default_retained = int(matched_text in source_text)

        if not expected_manifest_keys:
            checks.append("missing_expected_manifest_key_mapping")
        else:
            missing_keys = [key for key in expected_manifest_keys if key not in source_text]
            if missing_keys:
                checks.append("manifest_key_not_referenced:" + "|".join(missing_keys))
        if not explicit_cli_arg_present:
            checks.append("missing_explicit_cli_arg")
        if not has_input_manifest:
            checks.append("missing_input_manifest_arg")
        if not resolver_flag:
            checks.append("missing_manifest_resolver")
        if not legacy_default_retained:
            checks.append("legacy_default_not_detected")

        out.append(
            {
                "owner_branch": OWNER_BRANCH,
                "contract_id": f"BR222-{idx:03d}",
                "source_file": source_file,
                "line_no": line_no,
                "matched_text": matched_text,
                "workflow_lane": str(row["workflow_lane"]),
                "expected_manifest_keys": "|".join(expected_manifest_keys),
                "explicit_cli_flags": "|".join(explicit_cli_flags),
                "has_input_manifest_flag": has_input_manifest,
                "has_manifest_resolver_flag": resolver_flag,
                "explicit_cli_arg_present_flag": explicit_cli_arg_present,
                "legacy_default_retained_flag": legacy_default_retained,
                "contract_status": "closed" if not checks else "needs_patch",
                "missing_checks": ";".join(checks),
                "runtime_semantic_change_allowed_flag": 0,
                "bulk_rewrite_allowed_flag": 0,
                "recommended_resolution": (
                    "materialize_or_pass_explicit_result_bundle_inputs"
                    if checks
                    else "keep_legacy_default_but_use_manifest_or_explicit_cli_for_reproducible_runs"
                ),
            }
        )
    return out


def summary_payload(audit_rows: list[dict[str, object]]) -> dict[str, object]:
    fail_count = sum(str(row["contract_status"]) != "closed" for row in audit_rows)
    missing_check_count = sum(
        len([part for part in str(row["missing_checks"]).split(";") if part])
        for row in audit_rows
    )
    contract_complete = int(
        len(audit_rows) == EXPECTED_RUNTIME_RESULT_BUNDLE_ROWS
        and fail_count == 0
        and missing_check_count == 0
    )
    payload: dict[str, object] = {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_runtime_result_bundle_rows": EXPECTED_RUNTIME_RESULT_BUNDLE_ROWS,
        "runtime_result_bundle_rows": len(audit_rows),
        "source_file_count": len({str(row["source_file"]) for row in audit_rows}),
        "contract_closed_rows": len(audit_rows) - fail_count,
        "contract_gap_rows": fail_count,
        "input_manifest_arg_rows": sum(int(row["has_input_manifest_flag"]) for row in audit_rows),
        "manifest_resolver_rows": sum(int(row["has_manifest_resolver_flag"]) for row in audit_rows),
        "explicit_cli_arg_rows": sum(int(row["explicit_cli_arg_present_flag"]) for row in audit_rows),
        "legacy_default_retained_rows": sum(int(row["legacy_default_retained_flag"]) for row in audit_rows),
        "runtime_semantic_change_allowed_rows": sum(
            int(row["runtime_semantic_change_allowed_flag"]) for row in audit_rows
        ),
        "bulk_rewrite_allowed_rows": sum(int(row["bulk_rewrite_allowed_flag"]) for row in audit_rows),
        "missing_check_count": missing_check_count,
        "contract_complete": contract_complete,
        "contract_status_counts": dict(Counter(str(row["contract_status"]) for row in audit_rows)),
        "workflow_lane_counts": dict(Counter(str(row["workflow_lane"]) for row in audit_rows)),
        "recommended_next_branch": (
            "runtime_result_bundle_reference_contract_closed_no_rewrite"
            if contract_complete
            else "patch_runtime_result_bundle_consumers_with_input_manifest_resolver"
        ),
    }
    return payload


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    keys = [
        "expected_runtime_result_bundle_rows",
        "runtime_result_bundle_rows",
        "source_file_count",
        "contract_closed_rows",
        "contract_gap_rows",
        "input_manifest_arg_rows",
        "manifest_resolver_rows",
        "explicit_cli_arg_rows",
        "legacy_default_retained_rows",
        "runtime_semantic_change_allowed_rows",
        "bulk_rewrite_allowed_rows",
        "missing_check_count",
        "contract_complete",
    ]
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "key": key,
            "count": payload[key],
        }
        for key in keys
    ]
    workflow_counts = payload["workflow_lane_counts"]
    assert isinstance(workflow_counts, dict)
    for key, count in sorted(workflow_counts.items()):
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "workflow_lane",
                "key": key,
                "count": count,
            }
        )
    status_counts = payload["contract_status_counts"]
    assert isinstance(status_counts, dict)
    for key, count in sorted(status_counts.items()):
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "contract_status",
                "key": key,
                "count": count,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def write_note(output_dir: Path, payload: dict[str, object]) -> Path:
    contract_complete = int(payload["contract_complete"]) == 1
    decision_lines = (
        [
            "- Runtime result bundle references are fully contract-closed.",
            "- No default rewrite is authorized by this audit.",
            "- Keep direct runtime semantic and bulk rewrite permission at 0.",
        ]
        if contract_complete
        else [
            "- Runtime result bundle references are not fully contract-closed yet.",
            "- Patch manifest/resolver support before any path rewrite.",
            "- Keep direct runtime semantic and bulk rewrite permission at 0.",
        ]
    )
    lines = [
        "# Runtime Result Bundle Reference Contract Audit",
        "",
        "## Boundary",
        "- This branch audits result-bundle input contracts only.",
        "- It does not rewrite legacy result-bundle defaults.",
        "- It does not change `pv_ae/panel_day_engine.py`, runtime semantics, truth, threshold, or operator-facing behavior.",
        "",
        "## Summary",
        f"- expected runtime result bundle rows: `{payload['expected_runtime_result_bundle_rows']}`",
        f"- observed runtime result bundle rows: `{payload['runtime_result_bundle_rows']}`",
        f"- source files: `{payload['source_file_count']}`",
        f"- contract closed rows: `{payload['contract_closed_rows']}`",
        f"- contract gap rows: `{payload['contract_gap_rows']}`",
        f"- input-manifest argument rows: `{payload['input_manifest_arg_rows']}`",
        f"- manifest resolver rows: `{payload['manifest_resolver_rows']}`",
        f"- explicit CLI argument rows: `{payload['explicit_cli_arg_rows']}`",
        f"- legacy default retained rows: `{payload['legacy_default_retained_rows']}`",
        f"- missing check count: `{payload['missing_check_count']}`",
        f"- contract complete: `{payload['contract_complete']}`",
        "",
        "## Workflow Lane Counts",
    ]
    workflow_counts = payload["workflow_lane_counts"]
    assert isinstance(workflow_counts, dict)
    for key, count in sorted(workflow_counts.items()):
        lines.append(f"- `{key}`: `{count}`")
    lines.extend(["", "## Decision", *decision_lines])
    path = output_dir / NOTE_OUTPUT_NAME
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = resolve(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audit_rows = build_audit(repo_root, args.max_file_bytes)
    payload = summary_payload(audit_rows)

    detail_path = output_dir / DETAIL_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME
    note_path = write_note(output_dir, payload)

    write_csv(detail_path, audit_rows, DETAIL_COLUMNS)
    write_csv(summary_path, summary_rows(payload), SUMMARY_COLUMNS)
    payload["outputs"] = {
        "detail": str(detail_path),
        "summary": str(summary_path),
        "note": str(note_path),
        "json": str(json_path),
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
