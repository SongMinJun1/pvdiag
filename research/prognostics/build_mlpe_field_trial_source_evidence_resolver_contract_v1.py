#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-131"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_source_evidence_resolver_contract_br131_check"

CONTRACT_OUTPUT_NAME = "mlpe_field_trial_source_evidence_resolver_contract_v1.csv"
RESOLUTION_OUTPUT_NAME = "mlpe_field_trial_source_evidence_resolution_dry_run_v1.csv"
ISSUES_OUTPUT_NAME = "mlpe_field_trial_source_evidence_resolver_contract_issues_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_source_evidence_resolver_contract_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_source_evidence_resolver_contract_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_source_evidence_resolver_contract_v1.json"

APPROVAL_FIELDS = [
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

VALIDATION_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "row_index",
    "capture_status",
    "intake_validation_status",
    "real_capture_intake_ready_flag",
    "capture_input_path",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

CAPTURE_COLUMNS = [
    "trial_event_id",
    "raw_data_path",
    "peer_data_path",
    "weather_data_path",
    "waveform_slice_path",
]

SOURCE_GROUPS = [
    {
        "evidence_group": "capture_validation_row",
        "evidence_kind": "source_trace",
        "path_field": "capture_validation_path",
        "required_flag": 1,
        "required_policy": "required_for_each_candidate_event",
        "existence_policy": "input file must exist",
        "row_scope": "BR-129 validation row",
        "blocked_status": "blocked_missing_capture_validation",
        "next_gate_use": "BR-132 resolver run input trace",
    },
    {
        "evidence_group": "capture_row",
        "evidence_kind": "source_trace",
        "path_field": "capture_input_path",
        "required_flag": 1,
        "required_policy": "required_for_each_candidate_event",
        "existence_policy": "input file must exist and contain trial_event_id",
        "row_scope": "real capture CSV row",
        "blocked_status": "blocked_missing_capture_row",
        "next_gate_use": "BR-132 resolver run row trace",
    },
    {
        "evidence_group": "raw_data_slice",
        "evidence_kind": "raw_panel_signal",
        "path_field": "raw_data_path",
        "required_flag": 1,
        "required_policy": "required_after_real_capture_intake_ready",
        "existence_policy": "path must exist and be non-empty",
        "row_scope": "exact panel raw slice",
        "blocked_status": "blocked_raw_data_path",
        "next_gate_use": "source trace and waveform audit",
    },
    {
        "evidence_group": "peer_context_slice",
        "evidence_kind": "peer_context",
        "path_field": "peer_data_path",
        "required_flag": 1,
        "required_policy": "required_after_real_capture_intake_ready",
        "existence_policy": "path must exist and be non-empty",
        "row_scope": "peer/common-cause context slice",
        "blocked_status": "blocked_peer_data_path",
        "next_gate_use": "common-cause and artifact clearance",
    },
    {
        "evidence_group": "waveform_slice",
        "evidence_kind": "morphology",
        "path_field": "waveform_slice_path",
        "required_flag": 1,
        "required_policy": "required_after_real_capture_intake_ready",
        "existence_policy": "path must exist and be non-empty",
        "row_scope": "high-resolution or day-level waveform slice",
        "blocked_status": "blocked_waveform_slice_path",
        "next_gate_use": "family morphology and physical-invariant review",
    },
    {
        "evidence_group": "weather_context",
        "evidence_kind": "external_context",
        "path_field": "weather_data_path",
        "required_flag": 0,
        "required_policy": "optional_supporting_context",
        "existence_policy": "if supplied, path should exist and be non-empty",
        "row_scope": "weather or irradiance context",
        "blocked_status": "optional_weather_context_missing",
        "next_gate_use": "supporting common-cause review only",
    },
]

CONTRACT_COLUMNS = [
    "owner_branch",
    "evidence_group",
    "evidence_kind",
    "path_field",
    "required_flag",
    "required_policy",
    "existence_policy",
    "row_scope",
    "pass_condition",
    "blocked_status",
    "next_gate_use",
]

RESOLUTION_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "row_index",
    "capture_status",
    "capture_intake_status",
    "real_capture_intake_ready_flag",
    "evidence_group",
    "evidence_kind",
    "evidence_required_flag",
    "path_field",
    "path_value",
    "path_filled_flag",
    "path_exists_flag",
    "file_size_bytes",
    "source_evidence_resolution_status",
    "source_evidence_resolved_flag",
    "source_evidence_blocking_flag",
    "capture_validation_path",
    "capture_input_path",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "resolver_next_action",
]

ISSUE_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "row_index",
    "issue_type",
    "field",
    "observed_value",
    "expected_policy",
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def int_value(value: object) -> int:
    text = normalize_text(value)
    if not text:
        return 0
    return int(float(text))


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


def path_stats(repo_root: Path, path_text: str) -> tuple[int, int]:
    if not path_text:
        return 0, 0
    path = resolve_path(repo_root, path_text)
    if not path.exists():
        return 0, 0
    return 1, int(path.stat().st_size)


def build_contract() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for group in SOURCE_GROUPS:
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                **group,
                "pass_condition": pass_condition(group),
            }
        )
    return pd.DataFrame(rows).reindex(columns=CONTRACT_COLUMNS)


def pass_condition(group: dict[str, object]) -> str:
    if group["evidence_group"] == "weather_context":
        return "blank is allowed; if non-empty then file exists and size > 0"
    if group["evidence_group"] in {"capture_validation_row", "capture_row"}:
        return "source row is present and upstream approval/write fields are all 0"
    return "path is non-empty, file exists, file size > 0, and upstream intake row is ready"


def add_issue(
    issues: list[dict[str, object]],
    event_id: str,
    row_index: int,
    issue_type: str,
    field: str,
    observed: str,
    expected: str,
) -> None:
    issues.append(
        {
            "owner_branch": OWNER_BRANCH,
            "trial_event_id": event_id,
            "row_index": row_index,
            "issue_type": issue_type,
            "field": field,
            "observed_value": observed,
            "expected_policy": expected,
        }
    )


def approval_violation(row: pd.Series) -> bool:
    return any(int_value(row.get(field, "0")) != 0 for field in APPROVAL_FIELDS)


def source_status_for_group(
    repo_root: Path,
    group: dict[str, object],
    validation_path: Path | None,
    capture_path: Path | None,
    validation_row: pd.Series,
    capture_row: pd.Series | None,
) -> tuple[str, int, int, str, int, int]:
    event_ready = int_value(validation_row.get("real_capture_intake_ready_flag", "0")) == 1
    event_id = normalize_text(validation_row.get("trial_event_id", ""))
    required = int(group["required_flag"])
    path_field = str(group["path_field"])

    if not event_id:
        return "blocked_missing_trial_event_id", 0, 1, "", 0, 0
    if approval_violation(validation_row):
        return "blocked_source_approval_flag_violation", 0, 1, "", 0, 0
    if not event_ready:
        return "blocked_capture_intake_not_ready", 0, required, "", 0, 0

    if path_field == "capture_validation_path":
        path_text = str(validation_path) if validation_path else ""
        exists, size_bytes = path_stats(repo_root, path_text)
        resolved = int(exists == 1 and size_bytes > 0)
        return ("source_evidence_resolved" if resolved else "blocked_missing_capture_validation", resolved, 1 - resolved, path_text, exists, size_bytes)

    if capture_row is None:
        return "blocked_missing_capture_row", 0, required, "", 0, 0

    if path_field == "capture_input_path":
        path_text = str(capture_path) if capture_path else ""
    else:
        path_text = normalize_text(capture_row.get(path_field, ""))

    exists, size_bytes = path_stats(repo_root, path_text)
    filled = int(bool(path_text))

    if not filled and not required:
        return "optional_source_missing", 1, 0, path_text, 0, 0
    if not filled:
        return "blocked_required_path_missing", 0, 1, path_text, 0, 0
    if not exists:
        return "blocked_file_not_found", 0, required, path_text, 0, 0
    if size_bytes <= 0:
        return "blocked_file_empty", 0, required, path_text, 1, size_bytes
    return "source_evidence_resolved", 1, 0, path_text, 1, size_bytes


def build_missing_input_rows() -> tuple[pd.DataFrame, pd.DataFrame]:
    resolution = pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": "",
                "row_index": 0,
                "capture_status": "missing_capture_validation",
                "capture_intake_status": "blocked_missing_capture_validation_or_input",
                "real_capture_intake_ready_flag": 0,
                "evidence_group": "contract_input",
                "evidence_kind": "source_trace",
                "evidence_required_flag": 1,
                "path_field": "capture_validation",
                "path_value": "",
                "path_filled_flag": 0,
                "path_exists_flag": 0,
                "file_size_bytes": 0,
                "source_evidence_resolution_status": "blocked_missing_capture_validation_or_input",
                "source_evidence_resolved_flag": 0,
                "source_evidence_blocking_flag": 1,
                "capture_validation_path": "",
                "capture_input_path": "",
                "canonical_truth_write_allowed": 0,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "resolver_next_action": "Run BR-129 with real capture rows, then rerun this BR-131 resolver contract.",
            }
        ]
    ).reindex(columns=RESOLUTION_COLUMNS)
    issues = pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": "",
                "row_index": 0,
                "issue_type": "missing_capture_validation_or_input",
                "field": "capture_validation",
                "observed_value": "",
                "expected_policy": "BR-129 validation rows and capture input before BR-132",
            }
        ]
    ).reindex(columns=ISSUE_COLUMNS)
    return resolution, issues


def build_resolution(
    repo_root: Path,
    validation: pd.DataFrame | None,
    capture: pd.DataFrame | None,
    validation_path: Path | None,
    capture_path: Path | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if validation is None or capture is None:
        return build_missing_input_rows()

    capture_by_event = {
        normalize_text(row.get("trial_event_id", "")): row
        for _, row in capture.iterrows()
        if normalize_text(row.get("trial_event_id", ""))
    }
    rows: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []

    for idx, validation_row in validation.iterrows():
        event_id = normalize_text(validation_row.get("trial_event_id", ""))
        row_index = int_value(validation_row.get("row_index", idx + 1)) or idx + 1
        capture_row = capture_by_event.get(event_id)
        if not event_id:
            add_issue(issues, event_id, row_index, "missing_trial_event_id", "trial_event_id", "", "non-empty event id")
        if approval_violation(validation_row):
            add_issue(issues, event_id, row_index, "source_approval_flag_violation", "approval_fields", "nonzero", "all approval/write fields remain 0")
        if event_id and capture_row is None and int_value(validation_row.get("real_capture_intake_ready_flag", "0")) == 1:
            add_issue(issues, event_id, row_index, "missing_capture_row", "trial_event_id", event_id, "capture input row with same trial_event_id")

        for group in SOURCE_GROUPS:
            status, resolved, blocking, path_text, exists, size_bytes = source_status_for_group(
                repo_root,
                group,
                validation_path,
                capture_path,
                validation_row,
                capture_row,
            )
            path_filled = int(bool(path_text))
            required = int(group["required_flag"])
            path_field = str(group["path_field"])

            if status in {"blocked_required_path_missing", "blocked_file_not_found", "blocked_file_empty"}:
                add_issue(
                    issues,
                    event_id,
                    row_index,
                    status,
                    path_field,
                    path_text,
                    str(group["existence_policy"]),
                )

            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "row_index": row_index,
                    "capture_status": normalize_text(validation_row.get("capture_status", "")),
                    "capture_intake_status": normalize_text(validation_row.get("intake_validation_status", "")),
                    "real_capture_intake_ready_flag": int_value(validation_row.get("real_capture_intake_ready_flag", "0")),
                    "evidence_group": group["evidence_group"],
                    "evidence_kind": group["evidence_kind"],
                    "evidence_required_flag": required,
                    "path_field": path_field,
                    "path_value": path_text,
                    "path_filled_flag": path_filled,
                    "path_exists_flag": exists,
                    "file_size_bytes": size_bytes,
                    "source_evidence_resolution_status": status,
                    "source_evidence_resolved_flag": resolved,
                    "source_evidence_blocking_flag": blocking,
                    "capture_validation_path": str(validation_path) if validation_path else "",
                    "capture_input_path": str(capture_path) if capture_path else "",
                    "canonical_truth_write_allowed": 0,
                    "truth_intake_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "engine_patch_allowed": 0,
                    "resolver_next_action": next_action(status),
                }
            )

    return pd.DataFrame(rows).reindex(columns=RESOLUTION_COLUMNS), pd.DataFrame(issues).reindex(columns=ISSUE_COLUMNS)


def next_action(status: str) -> str:
    if status == "source_evidence_resolved":
        return "Keep as resolved source/evidence attachment; no truth, threshold, or engine approval."
    if status == "optional_source_missing":
        return "Optional context is absent; continue only if required groups are resolved."
    if status == "blocked_capture_intake_not_ready":
        return "Resolve BR-129 capture intake blockers before BR-132."
    if status == "blocked_source_approval_flag_violation":
        return "Reset upstream approval/write flags to 0 before resolver use."
    if status == "blocked_missing_capture_row":
        return "Attach the matching capture input row before BR-132."
    return "Fix the source/evidence path or source trace before BR-132."


def event_ready_count(resolution: pd.DataFrame) -> int:
    if resolution.empty or "trial_event_id" not in resolution.columns:
        return 0
    ready_events = 0
    for event_id, sub in resolution[resolution["trial_event_id"].map(normalize_text).ne("")].groupby("trial_event_id"):
        required = sub[sub["evidence_required_flag"].map(int_value).eq(1)]
        if required.empty:
            continue
        if int(sub["real_capture_intake_ready_flag"].max()) == 1 and int(required["source_evidence_blocking_flag"].sum()) == 0:
            ready_events += 1
    return ready_events


def build_summary(resolution: pd.DataFrame, issues: pd.DataFrame, contract: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "contract_rows": int(len(contract)),
            "events": int(resolution["trial_event_id"].map(normalize_text).replace("", pd.NA).dropna().nunique()) if len(resolution) else 0,
            "source_evidence_ready_events": event_ready_count(resolution),
            "resolution_rows": int(len(resolution)),
            "required_resolution_rows": int(resolution["evidence_required_flag"].map(int_value).sum()) if len(resolution) else 0,
            "source_evidence_resolved_rows": int(resolution["source_evidence_resolved_flag"].map(int_value).sum()) if len(resolution) else 0,
            "source_evidence_blocked_rows": int(resolution["source_evidence_blocking_flag"].map(int_value).sum()) if len(resolution) else 0,
            "path_exists_rows": int(resolution["path_exists_flag"].map(int_value).sum()) if len(resolution) else 0,
            "file_size_total_bytes": int(resolution["file_size_bytes"].map(int_value).sum()) if len(resolution) else 0,
            "issue_rows": int(len(issues)),
            "canonical_truth_write_allowed_sum": int(resolution["canonical_truth_write_allowed"].map(int_value).sum()) if len(resolution) else 0,
            "truth_intake_allowed_sum": int(resolution["truth_intake_allowed"].map(int_value).sum()) if len(resolution) else 0,
            "threshold_patch_allowed_sum": int(resolution["threshold_patch_allowed"].map(int_value).sum()) if len(resolution) else 0,
            "engine_patch_allowed_sum": int(resolution["engine_patch_allowed"].map(int_value).sum()) if len(resolution) else 0,
        }
    ]
    if len(resolution):
        for status, sub in resolution.groupby("source_evidence_resolution_status", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "source_evidence_resolution_status",
                    "summary_key": status,
                    "contract_rows": int(len(contract)),
                    "events": int(sub["trial_event_id"].map(normalize_text).replace("", pd.NA).dropna().nunique()),
                    "source_evidence_ready_events": 0,
                    "resolution_rows": int(len(sub)),
                    "required_resolution_rows": int(sub["evidence_required_flag"].map(int_value).sum()),
                    "source_evidence_resolved_rows": int(sub["source_evidence_resolved_flag"].map(int_value).sum()),
                    "source_evidence_blocked_rows": int(sub["source_evidence_blocking_flag"].map(int_value).sum()),
                    "path_exists_rows": int(sub["path_exists_flag"].map(int_value).sum()),
                    "file_size_total_bytes": int(sub["file_size_bytes"].map(int_value).sum()),
                    "issue_rows": int(len(issues[issues["trial_event_id"].isin(sub["trial_event_id"])])) if len(issues) else 0,
                    "canonical_truth_write_allowed_sum": int(sub["canonical_truth_write_allowed"].map(int_value).sum()),
                    "truth_intake_allowed_sum": int(sub["truth_intake_allowed"].map(int_value).sum()),
                    "threshold_patch_allowed_sum": int(sub["threshold_patch_allowed"].map(int_value).sum()),
                    "engine_patch_allowed_sum": int(sub["engine_patch_allowed"].map(int_value).sum()),
                }
            )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, summary: pd.DataFrame, validation_path: Path | None, capture_path: Path | None) -> Path:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-131 MLPE Field-Trial Source/Evidence Resolver Contract",
        "",
        "## Purpose",
        "- Define the source/evidence resolver contract before BR-132 real-row execution.",
        "- Expand each BR-129 intake-ready row into source trace, raw, peer, waveform, and optional weather checks.",
        "- Fail closed when capture validation/input rows or required paths are absent.",
        "",
        "## Result",
        f"- capture validation input: `{str(validation_path) if validation_path else ''}`",
        f"- capture CSV input: `{str(capture_path) if capture_path else ''}`",
        f"- contract rows: `{overall['contract_rows']}`",
        f"- events: `{overall['events']}`",
        f"- source/evidence-ready events: `{overall['source_evidence_ready_events']}`",
        f"- resolution rows: `{overall['resolution_rows']}`",
        f"- required resolution rows: `{overall['required_resolution_rows']}`",
        f"- source/evidence resolved rows: `{overall['source_evidence_resolved_rows']}`",
        f"- source/evidence blocked rows: `{overall['source_evidence_blocked_rows']}`",
        f"- path-exists rows: `{overall['path_exists_rows']}`",
        f"- file size total bytes: `{overall['file_size_total_bytes']}`",
        f"- issue rows: `{overall['issue_rows']}`",
        f"- canonical truth write allowed sum: `{overall['canonical_truth_write_allowed_sum']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- BR-131 is a contract/dry-run resolver, not truth intake.",
        "- Resolved source files are attachments, not labels and not independent physical confirmation.",
        "- BR-132 remains blocked until real intake rows exist.",
        "- All write/approval fields remain `0`.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--capture-validation", default="")
    parser.add_argument("--capture-input", default="")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    validation_arg = normalize_text(args.capture_validation)
    capture_arg = normalize_text(args.capture_input)
    validation_path = resolve_path(repo_root, validation_arg) if validation_arg else None
    capture_path = resolve_path(repo_root, capture_arg) if capture_arg else None
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    contract = build_contract()
    validation = read_csv(validation_path, VALIDATION_COLUMNS) if validation_path else None
    capture = read_csv(capture_path, CAPTURE_COLUMNS) if capture_path else None
    resolution, issues = build_resolution(repo_root, validation, capture, validation_path, capture_path)
    summary = build_summary(resolution, issues, contract)

    contract_path = output_dir / CONTRACT_OUTPUT_NAME
    resolution_path = output_dir / RESOLUTION_OUTPUT_NAME
    issues_path = output_dir / ISSUES_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    contract.to_csv(contract_path, index=False, encoding="utf-8-sig")
    resolution.to_csv(resolution_path, index=False, encoding="utf-8-sig")
    issues.to_csv(issues_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary, validation_path, capture_path)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "contract_rows": int(overall["contract_rows"]),
        "events": int(overall["events"]),
        "source_evidence_ready_events": int(overall["source_evidence_ready_events"]),
        "resolution_rows": int(overall["resolution_rows"]),
        "required_resolution_rows": int(overall["required_resolution_rows"]),
        "source_evidence_resolved_rows": int(overall["source_evidence_resolved_rows"]),
        "source_evidence_blocked_rows": int(overall["source_evidence_blocked_rows"]),
        "path_exists_rows": int(overall["path_exists_rows"]),
        "file_size_total_bytes": int(overall["file_size_total_bytes"]),
        "issue_rows": int(overall["issue_rows"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "contract": str(contract_path),
            "resolution": str(resolution_path),
            "issues": str(issues_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
