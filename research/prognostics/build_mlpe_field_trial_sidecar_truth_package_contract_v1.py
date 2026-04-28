#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from mlpe_field_trial_chain_manifest_v1 import DEFAULT_TRUTH_INTAKE_CHAIN_MANIFEST, resolve_truth_intake_chain_dependency
except ImportError:
    from research.prognostics.mlpe_field_trial_chain_manifest_v1 import (
        DEFAULT_TRUTH_INTAKE_CHAIN_MANIFEST,
        resolve_truth_intake_chain_dependency,
    )


OWNER_BRANCH = "BR-20260425-137"
DEFAULT_MATERIALIZATION_PRECHECK_ARTIFACT = "truth_materialization_precheck"
DEFAULT_COMMON_CAUSE_CLEARANCE_ARTIFACT = "common_cause_clearance"
DEFAULT_ARTIFACT_MLPE_CONTROL_CLEARANCE_ARTIFACT = "artifact_mlpe_control_clearance"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_sidecar_truth_package_contract_br137_check"

CONTRACT_OUTPUT_NAME = "mlpe_field_trial_sidecar_truth_package_contract_v1.csv"
PACKAGE_OUTPUT_NAME = "mlpe_field_trial_sidecar_truth_package_dry_run_v1.csv"
ISSUES_OUTPUT_NAME = "mlpe_field_trial_sidecar_truth_package_contract_issues_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_sidecar_truth_package_contract_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_sidecar_truth_package_contract_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_sidecar_truth_package_contract_v1.json"

APPROVAL_FIELDS = [
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

MATERIALIZATION_COLUMNS = [
    "trial_event_id",
    "site",
    "root_id",
    "panel_id",
    "event_date",
    "truth_candidate_role",
    "truth_seed_reviewer_decision",
    "materialization_precheck_passed_flag",
    "future_sidecar_truth_package_candidate_flag",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

CLEARANCE_COLUMNS = [
    "trial_event_id",
    "clearance_group",
    "required_flag",
    "clearance_passed_flag",
    "clearance_blocking_flag",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

SIDEcar_PACKAGE_INPUT_COLUMNS = [
    "trial_event_id",
    "site",
    "root_id",
    "panel_id",
    "event_date",
    "sidecar_truth_package_id",
    "sidecar_package_mode",
    "sidecar_truth_label",
    "sidecar_fault_family",
    "sidecar_event_type",
    "sidecar_onset_date",
    "sidecar_fault_date",
    "source_materialization_path",
    "source_common_cause_clearance_path",
    "source_artifact_mlpe_control_clearance_path",
    "reviewer_package_approval_flag",
    "reviewer_package_note",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
]

CONTRACT_GROUPS = [
    {
        "package_group": "materialization_precheck_ready",
        "required_flag": 1,
        "required_fields_csv": "BR-127 materialization_precheck_passed_flag,future_sidecar_truth_package_candidate_flag",
        "pass_condition": "BR-127 row is a future sidecar truth package candidate and has no write flags",
        "blocked_status": "blocked_materialization_precheck_not_ready",
        "next_gate_use": "BR-138 sidecar package row eligibility",
    },
    {
        "package_group": "common_cause_clearance_ready",
        "required_flag": 1,
        "required_fields_csv": "BR-134/BR-133 common-cause clearance rows",
        "pass_condition": "all required common-cause clearance rows for the event are non-blocking",
        "blocked_status": "blocked_common_cause_clearance_not_ready",
        "next_gate_use": "prevent common-cause row from becoming panel-local truth",
    },
    {
        "package_group": "artifact_mlpe_control_clearance_ready",
        "required_flag": 1,
        "required_fields_csv": "BR-136/BR-135 artifact and MLPE-control clearance rows",
        "pass_condition": "all required artifact/MLPE-control clearance rows for the event are non-blocking",
        "blocked_status": "blocked_artifact_mlpe_control_clearance_not_ready",
        "next_gate_use": "prevent artifact/control row from becoming panel physical truth",
    },
    {
        "package_group": "sidecar_payload_identity",
        "required_flag": 1,
        "required_fields_csv": "sidecar_truth_package_id,site,root_id,panel_id,event_date",
        "pass_condition": "sidecar package row is present and has stable event identity fields",
        "blocked_status": "blocked_sidecar_payload_identity_incomplete",
        "next_gate_use": "make package rows traceable without canonical overwrite",
    },
    {
        "package_group": "sidecar_truth_label_payload",
        "required_flag": 1,
        "required_fields_csv": "sidecar_truth_label,sidecar_fault_family,sidecar_event_type,sidecar_onset_date or sidecar_fault_date",
        "pass_condition": "review package carries a non-empty truth label payload and at least one event date",
        "blocked_status": "blocked_sidecar_truth_label_payload_incomplete",
        "next_gate_use": "truth replay input after reviewer approval",
    },
    {
        "package_group": "source_evidence_provenance_attached",
        "required_flag": 1,
        "required_fields_csv": "source_materialization_path,source_common_cause_clearance_path,source_artifact_mlpe_control_clearance_path",
        "pass_condition": "package row points back to materialization and both clearance sources",
        "blocked_status": "blocked_source_evidence_provenance_missing",
        "next_gate_use": "reviewer audit trail",
    },
    {
        "package_group": "write_boundary_locked",
        "required_flag": 1,
        "required_fields_csv": "canonical_truth_write_allowed,truth_intake_allowed,threshold_patch_allowed,engine_patch_allowed",
        "pass_condition": "all write/approval fields remain 0 in source and package rows",
        "blocked_status": "blocked_write_boundary_violation",
        "next_gate_use": "keep canonical truth, threshold, and engine writes closed",
    },
    {
        "package_group": "reviewer_package_approval_note",
        "required_flag": 1,
        "required_fields_csv": "reviewer_package_approval_flag,reviewer_package_note",
        "pass_condition": "reviewer_package_approval_flag=1 and reviewer note is non-empty",
        "blocked_status": "blocked_reviewer_package_approval_missing",
        "next_gate_use": "human review before sidecar package emission",
    },
]

CONTRACT_COLUMNS = [
    "owner_branch",
    "package_group",
    "required_flag",
    "required_fields_csv",
    "pass_condition",
    "blocked_status",
    "next_gate_use",
]

PACKAGE_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "site",
    "root_id",
    "panel_id",
    "event_date",
    "package_group",
    "required_flag",
    "materialization_ready_flag",
    "common_cause_clearance_ready_flag",
    "artifact_mlpe_control_clearance_ready_flag",
    "package_row_present_flag",
    "package_group_passed_flag",
    "package_group_blocking_flag",
    "sidecar_truth_package_status",
    "sidecar_truth_package_id",
    "sidecar_package_mode",
    "sidecar_truth_label",
    "sidecar_fault_family",
    "sidecar_event_type",
    "sidecar_onset_date",
    "sidecar_fault_date",
    "reviewer_package_note",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "package_next_action",
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


def approval_violation(row: pd.Series) -> bool:
    return any(int_value(row.get(field, "0")) != 0 for field in APPROVAL_FIELDS)


def build_contract() -> pd.DataFrame:
    rows = [{"owner_branch": OWNER_BRANCH, **group} for group in CONTRACT_GROUPS]
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


def build_missing_input_rows() -> tuple[pd.DataFrame, pd.DataFrame]:
    package = pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": "",
                "site": "",
                "root_id": "",
                "panel_id": "",
                "event_date": "",
                "package_group": "contract_input",
                "required_flag": 1,
                "materialization_ready_flag": 0,
                "common_cause_clearance_ready_flag": 0,
                "artifact_mlpe_control_clearance_ready_flag": 0,
                "package_row_present_flag": 0,
                "package_group_passed_flag": 0,
                "package_group_blocking_flag": 1,
                "sidecar_truth_package_status": "blocked_missing_materialization_precheck",
                "sidecar_truth_package_id": "",
                "sidecar_package_mode": "",
                "sidecar_truth_label": "",
                "sidecar_fault_family": "",
                "sidecar_event_type": "",
                "sidecar_onset_date": "",
                "sidecar_fault_date": "",
                "reviewer_package_note": "",
                "canonical_truth_write_allowed": 0,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "package_next_action": "Run BR-127 materialization precheck first; do not emit sidecar truth rows.",
            }
        ]
    ).reindex(columns=PACKAGE_COLUMNS)
    issues = pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": "",
                "issue_type": "missing_materialization_precheck",
                "field": "materialization_precheck",
                "observed_value": "",
                "expected_policy": "BR-127 materialization precheck output before sidecar truth package contract run",
            }
        ]
    ).reindex(columns=ISSUE_COLUMNS)
    return package, issues


def materialization_ready(row: pd.Series) -> int:
    if approval_violation(row):
        return 0
    return int(
        int_value(row.get("materialization_precheck_passed_flag", "0")) == 1
        and int_value(row.get("future_sidecar_truth_package_candidate_flag", "0")) == 1
    )


def clearance_ready_by_event(clearance: pd.DataFrame | None) -> dict[str, int]:
    if clearance is None or clearance.empty or "trial_event_id" not in clearance.columns:
        return {}
    ready: dict[str, int] = {}
    for event_id, sub in clearance[clearance["trial_event_id"].map(normalize_text).ne("")].groupby("trial_event_id"):
        required = sub[sub["required_flag"].map(int_value).eq(1)]
        no_required_rows = len(required) == 0
        no_blocking = int(required["clearance_blocking_flag"].map(int_value).sum()) == 0 if len(required) else False
        no_write = not any(approval_violation(row) for _, row in sub.iterrows())
        ready[event_id] = int((not no_required_rows) and no_blocking and no_write)
    return ready


def package_rows_by_event(package_input: pd.DataFrame | None) -> dict[str, pd.Series]:
    if package_input is None or package_input.empty or "trial_event_id" not in package_input.columns:
        return {}
    rows: dict[str, pd.Series] = {}
    for _, row in package_input.iterrows():
        event_id = normalize_text(row.get("trial_event_id", ""))
        if event_id and event_id not in rows:
            rows[event_id] = row
    return rows


def row_text(row: pd.Series | None, field: str) -> str:
    if row is None:
        return ""
    return normalize_text(row.get(field, ""))


def row_int(row: pd.Series | None, field: str) -> int:
    if row is None:
        return 0
    return int_value(row.get(field, "0"))


def identity_complete(row: pd.Series | None) -> bool:
    return row is not None and all(row_text(row, field) for field in ["sidecar_truth_package_id", "site", "root_id", "panel_id", "event_date"])


def label_payload_complete(row: pd.Series | None) -> bool:
    if row is None:
        return False
    required = ["sidecar_truth_label", "sidecar_fault_family", "sidecar_event_type"]
    has_label = all(row_text(row, field) for field in required)
    has_date = bool(row_text(row, "sidecar_onset_date") or row_text(row, "sidecar_fault_date"))
    return bool(has_label and has_date)


def provenance_attached(row: pd.Series | None) -> bool:
    required = [
        "source_materialization_path",
        "source_common_cause_clearance_path",
        "source_artifact_mlpe_control_clearance_path",
    ]
    return row is not None and all(row_text(row, field) for field in required)


def reviewer_approved(row: pd.Series | None) -> bool:
    return row is not None and row_int(row, "reviewer_package_approval_flag") == 1 and bool(row_text(row, "reviewer_package_note"))


def package_write_boundary_locked(source_row: pd.Series, package_row: pd.Series | None) -> bool:
    if approval_violation(source_row):
        return False
    if package_row is not None and approval_violation(package_row):
        return False
    return True


def group_status(
    group_name: str,
    source_row: pd.Series,
    package_row: pd.Series | None,
    common_ready: int,
    artifact_ready: int,
) -> tuple[str, int, int]:
    material_ready = materialization_ready(source_row)
    if group_name == "materialization_precheck_ready":
        passed = material_ready == 1
    elif group_name == "common_cause_clearance_ready":
        passed = common_ready == 1
    elif group_name == "artifact_mlpe_control_clearance_ready":
        passed = artifact_ready == 1
    elif group_name == "sidecar_payload_identity":
        passed = identity_complete(package_row)
    elif group_name == "sidecar_truth_label_payload":
        passed = label_payload_complete(package_row)
    elif group_name == "source_evidence_provenance_attached":
        passed = provenance_attached(package_row)
    elif group_name == "write_boundary_locked":
        passed = package_write_boundary_locked(source_row, package_row)
    elif group_name == "reviewer_package_approval_note":
        passed = reviewer_approved(package_row)
    else:
        passed = False

    if passed:
        return "sidecar_truth_package_group_passed", 1, 0
    for group in CONTRACT_GROUPS:
        if group["package_group"] == group_name:
            return str(group["blocked_status"]), 0, 1
    return "blocked_unknown_package_group", 0, 1


def next_action(status: str) -> str:
    if status == "sidecar_truth_package_group_passed":
        return "Keep as sidecar package evidence only; do not write canonical truth."
    if status == "blocked_materialization_precheck_not_ready":
        return "Resolve BR-127 materialization precheck before package discussion."
    if status == "blocked_common_cause_clearance_not_ready":
        return "Resolve BR-134 common-cause clearance before sidecar package emission."
    if status == "blocked_artifact_mlpe_control_clearance_not_ready":
        return "Resolve BR-136 artifact/MLPE-control clearance before sidecar package emission."
    if status == "blocked_write_boundary_violation":
        return "Clear all source/package write flags; this contract never authorizes writes."
    return "Complete sidecar package payload and reviewer approval before package emission."


def build_package(
    materialization: pd.DataFrame,
    common_clearance: pd.DataFrame | None,
    artifact_clearance: pd.DataFrame | None,
    package_input: pd.DataFrame | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    common_ready = clearance_ready_by_event(common_clearance)
    artifact_ready = clearance_ready_by_event(artifact_clearance)
    package_by_event = package_rows_by_event(package_input)

    for _, source_row in materialization.iterrows():
        event_id = normalize_text(source_row.get("trial_event_id", ""))
        package_row = package_by_event.get(event_id)
        event_common_ready = int(common_ready.get(event_id, 0))
        event_artifact_ready = int(artifact_ready.get(event_id, 0))

        if not event_id:
            add_issue(issues, event_id, "missing_trial_event_id", "trial_event_id", "", "non-empty trial_event_id")
        if package_row is None and materialization_ready(source_row):
            add_issue(issues, event_id, "missing_sidecar_package_input", "trial_event_id", event_id, "one sidecar package review row per materialized candidate")
        if package_row is not None and approval_violation(package_row):
            add_issue(issues, event_id, "package_write_flag_violation", "approval_fields", "nonzero", "all package write/approval fields remain 0")

        for group in CONTRACT_GROUPS:
            group_name = str(group["package_group"])
            status, passed, blocking = group_status(group_name, source_row, package_row, event_common_ready, event_artifact_ready)
            if blocking and event_id:
                add_issue(issues, event_id, status, group_name, "not passed", str(group["pass_condition"]))
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "site": row_text(package_row, "site") or normalize_text(source_row.get("site", "")),
                    "root_id": row_text(package_row, "root_id") or normalize_text(source_row.get("root_id", "")),
                    "panel_id": row_text(package_row, "panel_id") or normalize_text(source_row.get("panel_id", "")),
                    "event_date": row_text(package_row, "event_date") or normalize_text(source_row.get("event_date", "")),
                    "package_group": group_name,
                    "required_flag": int(group["required_flag"]),
                    "materialization_ready_flag": materialization_ready(source_row),
                    "common_cause_clearance_ready_flag": event_common_ready,
                    "artifact_mlpe_control_clearance_ready_flag": event_artifact_ready,
                    "package_row_present_flag": int(package_row is not None),
                    "package_group_passed_flag": passed,
                    "package_group_blocking_flag": blocking,
                    "sidecar_truth_package_status": status,
                    "sidecar_truth_package_id": row_text(package_row, "sidecar_truth_package_id"),
                    "sidecar_package_mode": row_text(package_row, "sidecar_package_mode"),
                    "sidecar_truth_label": row_text(package_row, "sidecar_truth_label"),
                    "sidecar_fault_family": row_text(package_row, "sidecar_fault_family"),
                    "sidecar_event_type": row_text(package_row, "sidecar_event_type"),
                    "sidecar_onset_date": row_text(package_row, "sidecar_onset_date"),
                    "sidecar_fault_date": row_text(package_row, "sidecar_fault_date"),
                    "reviewer_package_note": row_text(package_row, "reviewer_package_note"),
                    "canonical_truth_write_allowed": 0,
                    "truth_intake_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "engine_patch_allowed": 0,
                    "package_next_action": next_action(status),
                }
            )

    return pd.DataFrame(rows).reindex(columns=PACKAGE_COLUMNS), pd.DataFrame(issues).reindex(columns=ISSUE_COLUMNS)


def ready_event_count(package: pd.DataFrame) -> int:
    ready = 0
    for _, sub in package[package["trial_event_id"].map(normalize_text).ne("")].groupby("trial_event_id"):
        required = sub[sub["required_flag"].map(int_value).eq(1)]
        if len(required) and int(required["package_group_blocking_flag"].map(int_value).sum()) == 0:
            ready += 1
    return ready


def build_summary(package: pd.DataFrame, issues: pd.DataFrame, contract: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "contract_rows": int(len(contract)),
            "events": int(package["trial_event_id"].map(normalize_text).replace("", pd.NA).dropna().nunique()) if len(package) else 0,
            "sidecar_truth_package_ready_events": ready_event_count(package),
            "package_rows": int(len(package)),
            "package_passed_rows": int(package["package_group_passed_flag"].map(int_value).sum()) if len(package) else 0,
            "package_blocked_rows": int(package["package_group_blocking_flag"].map(int_value).sum()) if len(package) else 0,
            "issue_rows": int(len(issues)),
            "canonical_truth_write_allowed_sum": int(package["canonical_truth_write_allowed"].map(int_value).sum()) if len(package) else 0,
            "truth_intake_allowed_sum": int(package["truth_intake_allowed"].map(int_value).sum()) if len(package) else 0,
            "threshold_patch_allowed_sum": int(package["threshold_patch_allowed"].map(int_value).sum()) if len(package) else 0,
            "engine_patch_allowed_sum": int(package["engine_patch_allowed"].map(int_value).sum()) if len(package) else 0,
        }
    ]
    if len(package):
        for status, sub in package.groupby("sidecar_truth_package_status", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "sidecar_truth_package_status",
                    "summary_key": status,
                    "contract_rows": int(len(contract)),
                    "events": int(sub["trial_event_id"].map(normalize_text).replace("", pd.NA).dropna().nunique()),
                    "sidecar_truth_package_ready_events": 0,
                    "package_rows": int(len(sub)),
                    "package_passed_rows": int(sub["package_group_passed_flag"].map(int_value).sum()),
                    "package_blocked_rows": int(sub["package_group_blocking_flag"].map(int_value).sum()),
                    "issue_rows": int(len(issues)),
                    "canonical_truth_write_allowed_sum": int(sub["canonical_truth_write_allowed"].map(int_value).sum()),
                    "truth_intake_allowed_sum": int(sub["truth_intake_allowed"].map(int_value).sum()),
                    "threshold_patch_allowed_sum": int(sub["threshold_patch_allowed"].map(int_value).sum()),
                    "engine_patch_allowed_sum": int(sub["engine_patch_allowed"].map(int_value).sum()),
                }
            )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, summary: pd.DataFrame) -> None:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    text = "\n".join(
        [
            "# BR-20260425-137 sidecar truth package contract",
            "",
            f"- contract rows: `{overall['contract_rows']}`",
            f"- events: `{overall['events']}`",
            f"- sidecar-truth-package-ready events: `{overall['sidecar_truth_package_ready_events']}`",
            f"- package rows: `{overall['package_rows']}`",
            f"- package passed rows: `{overall['package_passed_rows']}`",
            f"- package blocked rows: `{overall['package_blocked_rows']}`",
            f"- issue rows: `{overall['issue_rows']}`",
            f"- canonical truth write allowed sum: `{overall['canonical_truth_write_allowed_sum']}`",
            f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
            f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
            f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
            "",
            "This contract only defines whether a row may enter a sidecar truth package dry-run.",
            "It does not write canonical truth, enable threshold replay, or patch the panel engine.",
            "",
        ]
    )
    (output_dir / NOTE_OUTPUT_NAME).write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the BR-137 sidecar truth package contract and fail-closed dry run.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--truth-intake-chain-manifest", default=DEFAULT_TRUTH_INTAKE_CHAIN_MANIFEST)
    parser.add_argument("--materialization-precheck", type=Path, default=None)
    parser.add_argument("--common-cause-clearance", type=Path, default=None)
    parser.add_argument("--artifact-mlpe-control-clearance", type=Path, default=None)
    parser.add_argument("--sidecar-package-input", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    materialization_path = resolve_truth_intake_chain_dependency(
        repo_root,
        args.materialization_precheck,
        DEFAULT_MATERIALIZATION_PRECHECK_ARTIFACT,
        args.truth_intake_chain_manifest,
    )
    common_path = resolve_truth_intake_chain_dependency(
        repo_root,
        args.common_cause_clearance,
        DEFAULT_COMMON_CAUSE_CLEARANCE_ARTIFACT,
        args.truth_intake_chain_manifest,
    )
    artifact_path = resolve_truth_intake_chain_dependency(
        repo_root,
        args.artifact_mlpe_control_clearance,
        DEFAULT_ARTIFACT_MLPE_CONTROL_CLEARANCE_ARTIFACT,
        args.truth_intake_chain_manifest,
    )
    package_input_path = resolve_path(repo_root, args.sidecar_package_input) if args.sidecar_package_input else None
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    contract = build_contract()
    if not materialization_path.exists():
        package, issues = build_missing_input_rows()
    else:
        materialization = read_csv(materialization_path, MATERIALIZATION_COLUMNS)
        common_clearance = read_csv(common_path, CLEARANCE_COLUMNS) if common_path.exists() else None
        artifact_clearance = read_csv(artifact_path, CLEARANCE_COLUMNS) if artifact_path.exists() else None
        package_input = read_csv(package_input_path, SIDEcar_PACKAGE_INPUT_COLUMNS) if package_input_path and package_input_path.exists() else None
        package, issues = build_package(materialization, common_clearance, artifact_clearance, package_input)

    summary = build_summary(package, issues, contract)

    contract.to_csv(output_dir / CONTRACT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    package.to_csv(output_dir / PACKAGE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    issues.to_csv(output_dir / ISSUES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "contract_rows": int(overall["contract_rows"]),
        "events": int(overall["events"]),
        "sidecar_truth_package_ready_events": int(overall["sidecar_truth_package_ready_events"]),
        "package_rows": int(overall["package_rows"]),
        "package_passed_rows": int(overall["package_passed_rows"]),
        "package_blocked_rows": int(overall["package_blocked_rows"]),
        "issue_rows": int(overall["issue_rows"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "contract": str(output_dir / CONTRACT_OUTPUT_NAME),
            "package": str(output_dir / PACKAGE_OUTPUT_NAME),
            "issues": str(output_dir / ISSUES_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
            "json": str(output_dir / JSON_OUTPUT_NAME),
        },
    }
    (output_dir / JSON_OUTPUT_NAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
