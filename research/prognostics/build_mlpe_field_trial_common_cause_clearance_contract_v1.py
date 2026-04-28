#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-133"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_common_cause_clearance_contract_br133_check"

CONTRACT_OUTPUT_NAME = "mlpe_field_trial_common_cause_clearance_contract_v1.csv"
CLEARANCE_OUTPUT_NAME = "mlpe_field_trial_common_cause_clearance_dry_run_v1.csv"
ISSUES_OUTPUT_NAME = "mlpe_field_trial_common_cause_clearance_contract_issues_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_common_cause_clearance_contract_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_common_cause_clearance_contract_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_common_cause_clearance_contract_v1.json"

APPROVAL_FIELDS = [
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

SOURCE_RESOLUTION_COLUMNS = [
    "trial_event_id",
    "real_capture_intake_ready_flag",
    "evidence_required_flag",
    "source_evidence_blocking_flag",
    "source_evidence_resolved_flag",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

CLEARANCE_INPUT_COLUMNS = [
    "trial_event_id",
    "site",
    "root_id",
    "panel_id",
    "event_date",
    "peer_panel_count",
    "peer_context_clearance_flag",
    "site_breadth_clearance_flag",
    "root_group_breadth_clearance_flag",
    "temporal_synchrony_clearance_flag",
    "reviewer_common_cause_clearance_flag",
    "same_day_site_event_flag",
    "same_day_group_off_flag",
    "bulk_screen_flag",
    "common_cause_clearance_note",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

CLEARANCE_GROUPS = [
    {
        "clearance_group": "source_evidence_ready",
        "required_flag": 1,
        "required_fields_csv": "BR-131 event-level source_evidence_ready",
        "pass_condition": "BR-131 required groups have no source_evidence_blocking_flag",
        "blocked_status": "blocked_source_evidence_not_ready",
        "next_gate_use": "BR-134 input eligibility",
    },
    {
        "clearance_group": "peer_context_clearance",
        "required_flag": 1,
        "required_fields_csv": "peer_panel_count,peer_context_clearance_flag",
        "pass_condition": "peer_context_clearance_flag=1 and peer_panel_count > 0",
        "blocked_status": "blocked_peer_context_not_cleared",
        "next_gate_use": "separate panel-local from peer-wide movement",
    },
    {
        "clearance_group": "site_breadth_clearance",
        "required_flag": 1,
        "required_fields_csv": "site_breadth_clearance_flag,bulk_screen_flag",
        "pass_condition": "site_breadth_clearance_flag=1 and bulk_screen_flag=0",
        "blocked_status": "blocked_site_breadth_not_cleared",
        "next_gate_use": "prevent site-wide/root-screen promotion",
    },
    {
        "clearance_group": "root_group_breadth_clearance",
        "required_flag": 1,
        "required_fields_csv": "root_group_breadth_clearance_flag",
        "pass_condition": "root_group_breadth_clearance_flag=1",
        "blocked_status": "blocked_root_group_breadth_not_cleared",
        "next_gate_use": "prevent group-side promotion",
    },
    {
        "clearance_group": "temporal_synchrony_clearance",
        "required_flag": 1,
        "required_fields_csv": "temporal_synchrony_clearance_flag,same_day_site_event_flag,same_day_group_off_flag",
        "pass_condition": "temporal_synchrony_clearance_flag=1 and same_day_site_event_flag=0 and same_day_group_off_flag=0",
        "blocked_status": "blocked_temporal_synchrony_not_cleared",
        "next_gate_use": "prevent same-day common-cause overlap",
    },
    {
        "clearance_group": "reviewer_clearance_note",
        "required_flag": 1,
        "required_fields_csv": "reviewer_common_cause_clearance_flag,common_cause_clearance_note",
        "pass_condition": "reviewer_common_cause_clearance_flag=1 and note is non-empty",
        "blocked_status": "blocked_reviewer_clearance_missing",
        "next_gate_use": "audit trail before sidecar truth package",
    },
]

CONTRACT_COLUMNS = [
    "owner_branch",
    "clearance_group",
    "required_flag",
    "required_fields_csv",
    "pass_condition",
    "blocked_status",
    "next_gate_use",
]

CLEARANCE_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "site",
    "root_id",
    "panel_id",
    "event_date",
    "clearance_group",
    "required_flag",
    "source_evidence_ready_flag",
    "clearance_row_present_flag",
    "clearance_passed_flag",
    "clearance_blocking_flag",
    "common_cause_clearance_status",
    "peer_panel_count",
    "same_day_site_event_flag",
    "same_day_group_off_flag",
    "bulk_screen_flag",
    "common_cause_clearance_note",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "clearance_next_action",
]

ISSUE_COLUMNS = [
    "owner_branch",
    "trial_event_id",
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


def build_contract() -> pd.DataFrame:
    rows = [{"owner_branch": OWNER_BRANCH, **group} for group in CLEARANCE_GROUPS]
    return pd.DataFrame(rows).reindex(columns=CONTRACT_COLUMNS)


def add_issue(issues: list[dict[str, object]], event_id: str, issue_type: str, field: str, observed: str, expected: str) -> None:
    issues.append(
        {
            "owner_branch": OWNER_BRANCH,
            "trial_event_id": event_id,
            "issue_type": issue_type,
            "field": field,
            "observed_value": observed,
            "expected_policy": expected,
        }
    )


def approval_violation(row: pd.Series) -> bool:
    return any(int_value(row.get(field, "0")) != 0 for field in APPROVAL_FIELDS)


def source_ready_by_event(source_resolution: pd.DataFrame) -> dict[str, int]:
    ready: dict[str, int] = {}
    for event_id, sub in source_resolution[source_resolution["trial_event_id"].map(normalize_text).ne("")].groupby("trial_event_id"):
        required = sub[sub["evidence_required_flag"].map(int_value).eq(1)]
        event_ready = int(sub["real_capture_intake_ready_flag"].map(int_value).max()) == 1 if len(sub) else False
        no_blocking = int(required["source_evidence_blocking_flag"].map(int_value).sum()) == 0 if len(required) else False
        no_write = not any(approval_violation(row) for _, row in sub.iterrows())
        ready[event_id] = int(event_ready and no_blocking and no_write)
    return ready


def build_missing_input_rows() -> tuple[pd.DataFrame, pd.DataFrame]:
    clearance = pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": "",
                "site": "",
                "root_id": "",
                "panel_id": "",
                "event_date": "",
                "clearance_group": "contract_input",
                "required_flag": 1,
                "source_evidence_ready_flag": 0,
                "clearance_row_present_flag": 0,
                "clearance_passed_flag": 0,
                "clearance_blocking_flag": 1,
                "common_cause_clearance_status": "blocked_missing_source_evidence_resolution",
                "peer_panel_count": 0,
                "same_day_site_event_flag": 0,
                "same_day_group_off_flag": 0,
                "bulk_screen_flag": 0,
                "common_cause_clearance_note": "",
                "canonical_truth_write_allowed": 0,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "clearance_next_action": "Run BR-131/132 source-evidence resolution before common-cause clearance.",
            }
        ]
    ).reindex(columns=CLEARANCE_COLUMNS)
    issues = pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": "",
                "issue_type": "missing_source_evidence_resolution",
                "field": "source_evidence_resolution",
                "observed_value": "",
                "expected_policy": "BR-131/132 source-evidence resolution rows",
            }
        ]
    ).reindex(columns=ISSUE_COLUMNS)
    return clearance, issues


def clearance_status_for_group(group_name: str, source_ready: int, row: pd.Series | None) -> tuple[str, int, int]:
    if source_ready != 1:
        return "blocked_source_evidence_not_ready", 0, 1
    if row is None:
        return "blocked_missing_common_cause_clearance_row", 0, 1
    if approval_violation(row):
        return "blocked_clearance_approval_flag_violation", 0, 1

    if group_name == "source_evidence_ready":
        return "common_cause_clearance_passed", 1, 0
    if group_name == "peer_context_clearance":
        passed = int_value(row.get("peer_context_clearance_flag", "0")) == 1 and int_value(row.get("peer_panel_count", "0")) > 0
        return ("common_cause_clearance_passed", 1, 0) if passed else ("blocked_peer_context_not_cleared", 0, 1)
    if group_name == "site_breadth_clearance":
        passed = int_value(row.get("site_breadth_clearance_flag", "0")) == 1 and int_value(row.get("bulk_screen_flag", "0")) == 0
        return ("common_cause_clearance_passed", 1, 0) if passed else ("blocked_site_breadth_not_cleared", 0, 1)
    if group_name == "root_group_breadth_clearance":
        passed = int_value(row.get("root_group_breadth_clearance_flag", "0")) == 1
        return ("common_cause_clearance_passed", 1, 0) if passed else ("blocked_root_group_breadth_not_cleared", 0, 1)
    if group_name == "temporal_synchrony_clearance":
        passed = (
            int_value(row.get("temporal_synchrony_clearance_flag", "0")) == 1
            and int_value(row.get("same_day_site_event_flag", "0")) == 0
            and int_value(row.get("same_day_group_off_flag", "0")) == 0
        )
        return ("common_cause_clearance_passed", 1, 0) if passed else ("blocked_temporal_synchrony_not_cleared", 0, 1)
    if group_name == "reviewer_clearance_note":
        passed = int_value(row.get("reviewer_common_cause_clearance_flag", "0")) == 1 and bool(normalize_text(row.get("common_cause_clearance_note", "")))
        return ("common_cause_clearance_passed", 1, 0) if passed else ("blocked_reviewer_clearance_missing", 0, 1)
    return "blocked_unknown_clearance_group", 0, 1


def build_clearance(
    source_resolution: pd.DataFrame | None,
    clearance_input: pd.DataFrame | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if source_resolution is None:
        return build_missing_input_rows()

    ready_by_event = source_ready_by_event(source_resolution)
    rows: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    clearance_by_event: dict[str, pd.Series] = {}

    if clearance_input is not None:
        duplicate_ids = clearance_input["trial_event_id"][clearance_input["trial_event_id"].duplicated()].map(normalize_text).tolist()
        for event_id in duplicate_ids:
            add_issue(issues, event_id, "duplicate_clearance_row", "trial_event_id", event_id, "one clearance row per trial_event_id")
        for _, row in clearance_input.iterrows():
            event_id = normalize_text(row.get("trial_event_id", ""))
            if event_id and event_id not in clearance_by_event:
                clearance_by_event[event_id] = row

    if not ready_by_event:
        return build_missing_input_rows()

    for event_id, source_ready in ready_by_event.items():
        clearance_row = clearance_by_event.get(event_id)
        if clearance_input is None and source_ready == 1:
            add_issue(issues, event_id, "missing_common_cause_clearance_input", "common_cause_clearance_input", "", "required when source/evidence is ready")
        elif clearance_row is None and source_ready == 1:
            add_issue(issues, event_id, "missing_common_cause_clearance_row", "trial_event_id", event_id, "one clearance row per ready event")
        elif clearance_row is not None and approval_violation(clearance_row):
            add_issue(issues, event_id, "clearance_approval_flag_violation", "approval_fields", "nonzero", "all approval/write fields remain 0")

        for group in CLEARANCE_GROUPS:
            group_name = str(group["clearance_group"])
            status, passed, blocking = clearance_status_for_group(group_name, source_ready, clearance_row)
            if blocking and status not in {"blocked_source_evidence_not_ready", "blocked_missing_common_cause_clearance_row"}:
                add_issue(issues, event_id, status, group_name, "not passed", str(group["pass_condition"]))
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "site": normalize_text(clearance_row.get("site", "")) if clearance_row is not None else "",
                    "root_id": normalize_text(clearance_row.get("root_id", "")) if clearance_row is not None else "",
                    "panel_id": normalize_text(clearance_row.get("panel_id", "")) if clearance_row is not None else "",
                    "event_date": normalize_text(clearance_row.get("event_date", "")) if clearance_row is not None else "",
                    "clearance_group": group_name,
                    "required_flag": int(group["required_flag"]),
                    "source_evidence_ready_flag": source_ready,
                    "clearance_row_present_flag": int(clearance_row is not None),
                    "clearance_passed_flag": passed,
                    "clearance_blocking_flag": blocking,
                    "common_cause_clearance_status": status,
                    "peer_panel_count": int_value(clearance_row.get("peer_panel_count", "0")) if clearance_row is not None else 0,
                    "same_day_site_event_flag": int_value(clearance_row.get("same_day_site_event_flag", "0")) if clearance_row is not None else 0,
                    "same_day_group_off_flag": int_value(clearance_row.get("same_day_group_off_flag", "0")) if clearance_row is not None else 0,
                    "bulk_screen_flag": int_value(clearance_row.get("bulk_screen_flag", "0")) if clearance_row is not None else 0,
                    "common_cause_clearance_note": normalize_text(clearance_row.get("common_cause_clearance_note", "")) if clearance_row is not None else "",
                    "canonical_truth_write_allowed": 0,
                    "truth_intake_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "engine_patch_allowed": 0,
                    "clearance_next_action": next_action(status),
                }
            )

    return pd.DataFrame(rows).reindex(columns=CLEARANCE_COLUMNS), pd.DataFrame(issues).reindex(columns=ISSUE_COLUMNS)


def next_action(status: str) -> str:
    if status == "common_cause_clearance_passed":
        return "Keep as common-cause-cleared attachment; no truth, threshold, or engine approval."
    if status == "blocked_source_evidence_not_ready":
        return "Resolve BR-132 source/evidence first."
    if status == "blocked_missing_common_cause_clearance_row":
        return "Attach one common-cause clearance row for this event."
    return "Resolve common-cause blocker before panel-local eligibility or sidecar truth discussion."


def event_ready_count(clearance: pd.DataFrame) -> int:
    ready = 0
    for _, sub in clearance[clearance["trial_event_id"].map(normalize_text).ne("")].groupby("trial_event_id"):
        required = sub[sub["required_flag"].map(int_value).eq(1)]
        if len(required) and int(required["clearance_blocking_flag"].map(int_value).sum()) == 0:
            ready += 1
    return ready


def build_summary(clearance: pd.DataFrame, issues: pd.DataFrame, contract: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "contract_rows": int(len(contract)),
            "events": int(clearance["trial_event_id"].map(normalize_text).replace("", pd.NA).dropna().nunique()) if len(clearance) else 0,
            "common_cause_clearance_ready_events": event_ready_count(clearance),
            "clearance_rows": int(len(clearance)),
            "clearance_passed_rows": int(clearance["clearance_passed_flag"].map(int_value).sum()) if len(clearance) else 0,
            "clearance_blocked_rows": int(clearance["clearance_blocking_flag"].map(int_value).sum()) if len(clearance) else 0,
            "issue_rows": int(len(issues)),
            "canonical_truth_write_allowed_sum": int(clearance["canonical_truth_write_allowed"].map(int_value).sum()) if len(clearance) else 0,
            "truth_intake_allowed_sum": int(clearance["truth_intake_allowed"].map(int_value).sum()) if len(clearance) else 0,
            "threshold_patch_allowed_sum": int(clearance["threshold_patch_allowed"].map(int_value).sum()) if len(clearance) else 0,
            "engine_patch_allowed_sum": int(clearance["engine_patch_allowed"].map(int_value).sum()) if len(clearance) else 0,
        }
    ]
    if len(clearance):
        for status, sub in clearance.groupby("common_cause_clearance_status", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "common_cause_clearance_status",
                    "summary_key": status,
                    "contract_rows": int(len(contract)),
                    "events": int(sub["trial_event_id"].map(normalize_text).replace("", pd.NA).dropna().nunique()),
                    "common_cause_clearance_ready_events": 0,
                    "clearance_rows": int(len(sub)),
                    "clearance_passed_rows": int(sub["clearance_passed_flag"].map(int_value).sum()),
                    "clearance_blocked_rows": int(sub["clearance_blocking_flag"].map(int_value).sum()),
                    "issue_rows": int(len(issues[issues["trial_event_id"].isin(sub["trial_event_id"])])) if len(issues) else 0,
                    "canonical_truth_write_allowed_sum": int(sub["canonical_truth_write_allowed"].map(int_value).sum()),
                    "truth_intake_allowed_sum": int(sub["truth_intake_allowed"].map(int_value).sum()),
                    "threshold_patch_allowed_sum": int(sub["threshold_patch_allowed"].map(int_value).sum()),
                    "engine_patch_allowed_sum": int(sub["engine_patch_allowed"].map(int_value).sum()),
                }
            )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, summary: pd.DataFrame, source_path: Path | None, clearance_path: Path | None) -> Path:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-133 MLPE Field-Trial Common-Cause Clearance Contract",
        "",
        "## Purpose",
        "- Define common-cause clearance before BR-134 real-row execution.",
        "- Require source/evidence readiness plus peer, site breadth, root/group breadth, temporal synchrony, and reviewer clearance.",
        "- Fail closed when source/evidence rows or common-cause clearance rows are absent.",
        "",
        "## Result",
        f"- source/evidence resolution input: `{str(source_path) if source_path else ''}`",
        f"- common-cause clearance input: `{str(clearance_path) if clearance_path else ''}`",
        f"- contract rows: `{overall['contract_rows']}`",
        f"- events: `{overall['events']}`",
        f"- common-cause-clearance-ready events: `{overall['common_cause_clearance_ready_events']}`",
        f"- clearance rows: `{overall['clearance_rows']}`",
        f"- clearance passed rows: `{overall['clearance_passed_rows']}`",
        f"- clearance blocked rows: `{overall['clearance_blocked_rows']}`",
        f"- issue rows: `{overall['issue_rows']}`",
        f"- canonical truth write allowed sum: `{overall['canonical_truth_write_allowed_sum']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Passing this contract only clears the common-cause blocker for a later sidecar flow.",
        "- It does not create truth labels, threshold approval, or panel-local promotion.",
        "- Common-cause rows remain blocker/regression material unless explicitly cleared.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--source-evidence-resolution", default="")
    parser.add_argument("--common-cause-clearance-input", default="")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    source_arg = normalize_text(args.source_evidence_resolution)
    clearance_arg = normalize_text(args.common_cause_clearance_input)
    source_path = resolve_path(repo_root, source_arg) if source_arg else None
    clearance_path = resolve_path(repo_root, clearance_arg) if clearance_arg else None
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    contract = build_contract()
    source_resolution = read_csv(source_path, SOURCE_RESOLUTION_COLUMNS) if source_path else None
    clearance_input = read_csv(clearance_path, CLEARANCE_INPUT_COLUMNS) if clearance_path else None
    clearance, issues = build_clearance(source_resolution, clearance_input)
    summary = build_summary(clearance, issues, contract)

    contract_path = output_dir / CONTRACT_OUTPUT_NAME
    clearance_output_path = output_dir / CLEARANCE_OUTPUT_NAME
    issues_path = output_dir / ISSUES_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    contract.to_csv(contract_path, index=False, encoding="utf-8-sig")
    clearance.to_csv(clearance_output_path, index=False, encoding="utf-8-sig")
    issues.to_csv(issues_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary, source_path, clearance_path)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "contract_rows": int(overall["contract_rows"]),
        "events": int(overall["events"]),
        "common_cause_clearance_ready_events": int(overall["common_cause_clearance_ready_events"]),
        "clearance_rows": int(overall["clearance_rows"]),
        "clearance_passed_rows": int(overall["clearance_passed_rows"]),
        "clearance_blocked_rows": int(overall["clearance_blocked_rows"]),
        "issue_rows": int(overall["issue_rows"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "contract": str(contract_path),
            "clearance": str(clearance_output_path),
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
