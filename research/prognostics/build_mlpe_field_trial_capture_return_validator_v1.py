#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from mlpe_field_trial_user_input_contract_v1 import require_explicit_user_filled_input
except ImportError:
    from research.prognostics.mlpe_field_trial_user_input_contract_v1 import require_explicit_user_filled_input

try:
    from mlpe_field_trial_chain_manifest_v1 import DEFAULT_CAPTURE_CHAIN_MANIFEST, resolve_capture_chain_dependency
except ImportError:
    from research.prognostics.mlpe_field_trial_chain_manifest_v1 import (
        DEFAULT_CAPTURE_CHAIN_MANIFEST,
        resolve_capture_chain_dependency,
    )


OWNER_BRANCH = "BR-20260425-111"
DEFAULT_WATCHLIST_ARTIFACT = "real_capture_intake_watchlist"
DEFAULT_RETURNED_CAPTURE = "/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_capture_return_validator_br111_check"

VALIDATION_OUTPUT_NAME = "mlpe_field_trial_capture_return_validation_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_capture_return_validation_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_capture_return_validation_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_capture_return_validation_v1.json"

REQUIRED_CAPTURE_FIELDS = [
    "site",
    "panel_id",
    "mlpe_device_id",
    "start_ts",
    "end_ts",
    "injection_case",
    "planned_fault_family",
    "planned_fault_subtype",
    "affected_scope",
    "injection_mode",
    "injection_strength",
    "expected_signature",
    "mlpe_state",
    "timestamp_quality",
    "communication_quality",
]

REQUIRED_EVIDENCE_PATH_FIELDS = ["raw_data_path", "peer_data_path", "waveform_slice_path"]

WATCHLIST_COLUMNS = [
    "trial_event_id",
    "injection_case",
    "planned_fault_family",
    "planned_fault_subtype",
    "real_capture_status",
    "real_capture_required_flag",
]

CAPTURE_COLUMNS = [
    "trial_event_id",
    "site",
    "root_id",
    "panel_id",
    "mlpe_device_id",
    "start_ts",
    "end_ts",
    "capture_status",
    "injection_case",
    "planned_fault_family",
    "planned_fault_subtype",
    "affected_scope",
    "injection_mode",
    "injection_strength",
    "expected_signature",
    "mlpe_state",
    "raw_data_path",
    "peer_data_path",
    "weather_data_path",
    "waveform_slice_path",
    "timestamp_quality",
    "communication_quality",
    "final_fault_family",
    "final_fault_subtype",
    "final_truth_confidence",
    "final_label_attached",
    "label_status",
    "operator_promotion_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "reviewer",
    "review_note",
]

VALIDATION_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "watchlist_row_found_flag",
    "returned_row_found_flag",
    "duplicate_returned_event_id_flag",
    "watchlist_real_capture_status",
    "watchlist_real_capture_required_flag",
    "capture_status",
    "label_status",
    "site",
    "panel_id",
    "mlpe_device_id",
    "injection_case",
    "planned_fault_family",
    "planned_fault_subtype",
    "metadata_ready_flag",
    "required_evidence_paths_filled_flag",
    "required_evidence_paths_exist_flag",
    "weather_path_filled_flag",
    "weather_path_exists_flag",
    "label_attached_flag",
    "returned_ready_for_adjudication_flag",
    "still_waiting_for_real_capture_flag",
    "validation_failed_flag",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "validation_bucket",
    "missing_metadata_fields_csv",
    "missing_evidence_path_fields_csv",
    "missing_evidence_files_csv",
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


def load_input_manifest(repo_root: Path, value: str | Path | None) -> tuple[Path | None, dict[str, Any]]:
    if value is None or str(value).strip() == "":
        return None, {}
    path = resolve_path(repo_root, value)
    if not path.exists():
        raise FileNotFoundError(f"missing input manifest: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"input manifest must be a JSON object: {path}")
    return path, payload


def manifest_path_value(manifest: dict[str, Any], key: str) -> str:
    raw = manifest.get(key)
    if raw is None and isinstance(manifest.get("inputs"), dict):
        raw = manifest["inputs"].get(key)
    if isinstance(raw, dict):
        for field in ["path", "artifact_path", "static_path"]:
            if raw.get(field):
                return str(raw[field])
        return ""
    return "" if raw is None else str(raw)


def cli_flag_provided(flag: str, argv: list[str]) -> bool:
    return any(item == flag or item.startswith(f"{flag}=") for item in argv)


def resolve_returned_capture_input(
    repo_root: Path,
    returned_capture_value: str | Path,
    manifest: dict[str, Any],
    explicit_flags: set[str],
) -> tuple[Path, str]:
    if "--returned-capture" in explicit_flags:
        return resolve_path(repo_root, returned_capture_value), "explicit_cli"
    if manifest:
        manifest_value = manifest_path_value(manifest, "returned_capture")
        if not manifest_value:
            raise KeyError(
                "MLPE field-trial input manifest is missing `returned_capture`; "
                "pass --returned-capture explicitly or add inputs.returned_capture"
            )
        return resolve_path(repo_root, manifest_value), "input_manifest"
    return resolve_path(repo_root, returned_capture_value), "legacy_default"


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


def path_exists(repo_root: Path, path_text: str) -> bool:
    if not path_text:
        return False
    return resolve_path(repo_root, path_text).exists()


def first_group_rows(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if df.empty or "trial_event_id" not in df.columns:
        return {}
    keyed = df[df["trial_event_id"].astype(str).str.len() > 0].copy()
    return {str(key): sub.copy() for key, sub in keyed.groupby("trial_event_id", sort=False, dropna=False)}


def label_attached(row: pd.Series) -> int:
    return int(row.get("final_label_attached", "") == "1" or row.get("label_status", "") == "label_attached")


def build_validation(watchlist: pd.DataFrame, returned: pd.DataFrame, repo_root: Path) -> pd.DataFrame:
    watchlist = watchlist.copy()
    returned = returned.copy()
    for col in WATCHLIST_COLUMNS:
        if col not in watchlist.columns:
            watchlist[col] = ""
    for col in CAPTURE_COLUMNS:
        if col not in returned.columns:
            returned[col] = ""

    returned_groups = first_group_rows(returned)
    watch_ids = [normalize_text(value) for value in watchlist["trial_event_id"].tolist() if normalize_text(value)]
    extra_ids = [event_id for event_id in returned_groups if event_id not in set(watch_ids)]
    ordered_ids = watch_ids + extra_ids

    rows: list[dict[str, object]] = []
    for event_id in ordered_ids:
        watch_matches = watchlist[watchlist["trial_event_id"].astype(str).eq(event_id)]
        watch_found = int(not watch_matches.empty)
        watch_row = watch_matches.iloc[0] if watch_found else pd.Series(dtype=object)

        returned_matches = returned_groups.get(event_id, pd.DataFrame())
        returned_found = int(not returned_matches.empty)
        duplicate_returned = int(len(returned_matches) > 1)
        returned_row = returned_matches.iloc[0] if returned_found else pd.Series(dtype=object)

        capture_status = normalize_text(returned_row.get("capture_status", ""))
        planned_or_empty = capture_status in {"", "planned"}
        missing_metadata = [
            field
            for field in REQUIRED_CAPTURE_FIELDS
            if returned_found and not planned_or_empty and not normalize_text(returned_row.get(field, ""))
        ]
        missing_path_fields = [
            field
            for field in REQUIRED_EVIDENCE_PATH_FIELDS
            if returned_found and not planned_or_empty and not normalize_text(returned_row.get(field, ""))
        ]
        missing_files = [
            field
            for field in REQUIRED_EVIDENCE_PATH_FIELDS
            if returned_found
            and not planned_or_empty
            and normalize_text(returned_row.get(field, ""))
            and not path_exists(repo_root, normalize_text(returned_row.get(field, "")))
        ]
        weather_path = normalize_text(returned_row.get("weather_data_path", ""))
        weather_filled = int(bool(weather_path))
        weather_exists = int(path_exists(repo_root, weather_path)) if weather_filled else 0

        metadata_ready = int(returned_found and not planned_or_empty and not missing_metadata)
        paths_filled = int(returned_found and not planned_or_empty and not missing_path_fields)
        paths_exist = int(paths_filled and not missing_files)
        attached = label_attached(returned_row) if returned_found else 0

        if not watch_found:
            bucket = "returned_row_not_in_watchlist"
            ready = 0
            waiting = 0
            failed = 1
            next_action = "Remove or separately register returned row before adjudication."
        elif duplicate_returned:
            bucket = "duplicate_returned_event_id"
            ready = 0
            waiting = 0
            failed = 1
            next_action = "Resolve duplicate trial_event_id rows before readiness review."
        elif not returned_found:
            bucket = "return_missing"
            ready = 0
            waiting = 1
            failed = 0
            next_action = "Collect and return the real capture row."
        elif planned_or_empty:
            bucket = "still_waiting_for_real_capture"
            ready = 0
            waiting = 1
            failed = 0
            next_action = "Fill real capture metadata/evidence; planned rows are not defects."
        elif capture_status == "discarded":
            bucket = "returned_discarded_review_required"
            ready = 0
            waiting = 0
            failed = 0
            next_action = "Review discard reason; do not use this row for truth intake."
        elif missing_metadata:
            bucket = "returned_metadata_incomplete"
            ready = 0
            waiting = 0
            failed = 1
            next_action = "Complete required capture metadata before adjudication."
        elif missing_path_fields:
            bucket = "returned_evidence_paths_missing"
            ready = 0
            waiting = 0
            failed = 1
            next_action = "Attach raw, peer, and waveform slice evidence paths."
        elif missing_files:
            bucket = "returned_evidence_files_not_found"
            ready = 0
            waiting = 0
            failed = 1
            next_action = "Fix evidence paths or regenerate referenced evidence files."
        elif attached:
            bucket = "returned_label_attached_truth_gate_required"
            ready = 0
            waiting = 0
            failed = 0
            next_action = "Run the separate truth-intake gate; validator alone is not approval."
        else:
            bucket = "returned_capture_ready_label_pending"
            ready = 1
            waiting = 0
            failed = 0
            next_action = "Rerun readiness and handoff gates before final adjudication."

        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": event_id,
                "watchlist_row_found_flag": watch_found,
                "returned_row_found_flag": returned_found,
                "duplicate_returned_event_id_flag": duplicate_returned,
                "watchlist_real_capture_status": normalize_text(watch_row.get("real_capture_status", "")),
                "watchlist_real_capture_required_flag": normalize_text(watch_row.get("real_capture_required_flag", "")),
                "capture_status": capture_status,
                "label_status": normalize_text(returned_row.get("label_status", "")),
                "site": normalize_text(returned_row.get("site", "")),
                "panel_id": normalize_text(returned_row.get("panel_id", "")),
                "mlpe_device_id": normalize_text(returned_row.get("mlpe_device_id", "")),
                "injection_case": normalize_text(returned_row.get("injection_case", watch_row.get("injection_case", ""))),
                "planned_fault_family": normalize_text(returned_row.get("planned_fault_family", watch_row.get("planned_fault_family", ""))),
                "planned_fault_subtype": normalize_text(returned_row.get("planned_fault_subtype", watch_row.get("planned_fault_subtype", ""))),
                "metadata_ready_flag": metadata_ready,
                "required_evidence_paths_filled_flag": paths_filled,
                "required_evidence_paths_exist_flag": paths_exist,
                "weather_path_filled_flag": weather_filled,
                "weather_path_exists_flag": weather_exists,
                "label_attached_flag": attached,
                "returned_ready_for_adjudication_flag": ready,
                "still_waiting_for_real_capture_flag": waiting,
                "validation_failed_flag": failed,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "validation_bucket": bucket,
                "missing_metadata_fields_csv": ",".join(missing_metadata),
                "missing_evidence_path_fields_csv": ",".join(missing_path_fields),
                "missing_evidence_files_csv": ",".join(missing_files),
                "next_action": next_action,
            }
        )
    return pd.DataFrame(rows).reindex(columns=VALIDATION_COLUMNS)


def build_summary(validation: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "rows": int(len(validation)),
            "returned_row_found_rows": int(validation["returned_row_found_flag"].sum()),
            "still_waiting_rows": int(validation["still_waiting_for_real_capture_flag"].sum()),
            "returned_ready_rows": int(validation["returned_ready_for_adjudication_flag"].sum()),
            "validation_failed_rows": int(validation["validation_failed_flag"].sum()),
            "label_attached_rows": int(validation["label_attached_flag"].sum()),
            "truth_intake_allowed_sum": int(validation["truth_intake_allowed"].sum()),
            "threshold_patch_allowed_sum": int(validation["threshold_patch_allowed"].sum()),
            "engine_patch_allowed_sum": int(validation["engine_patch_allowed"].sum()),
        }
    ]
    for bucket, sub in validation.groupby("validation_bucket", dropna=False):
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "validation_bucket",
                "summary_key": bucket,
                "rows": int(len(sub)),
                "returned_row_found_rows": int(sub["returned_row_found_flag"].sum()),
                "still_waiting_rows": int(sub["still_waiting_for_real_capture_flag"].sum()),
                "returned_ready_rows": int(sub["returned_ready_for_adjudication_flag"].sum()),
                "validation_failed_rows": int(sub["validation_failed_flag"].sum()),
                "label_attached_rows": int(sub["label_attached_flag"].sum()),
                "truth_intake_allowed_sum": int(sub["truth_intake_allowed"].sum()),
                "threshold_patch_allowed_sum": int(sub["threshold_patch_allowed"].sum()),
                "engine_patch_allowed_sum": int(sub["engine_patch_allowed"].sum()),
            }
        )
    return pd.DataFrame(rows)


def write_note(
    output_dir: Path,
    summary: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> Path:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    source_map = input_resolution_sources or {}
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-111 MLPE Field-Trial Capture Return Validator",
        "",
        "## Purpose",
        "- Validate returned real-capture rows against the BR-110 watchlist before adjudication.",
        "- Treat planned rows as waiting state, not validation defects.",
        "- Keep truth, threshold, and engine approvals locked to `0`.",
        "",
        "## Inputs",
        f"- evidence input manifest: `{input_manifest_path if input_manifest_path is not None else 'not provided'}`",
        "",
        "## Input Resolution Sources",
        f"- `returned_capture`: `{source_map.get('returned_capture', 'legacy_default')}`",
        "",
        "## Real Result",
        f"- rows: `{overall['rows']}`",
        f"- returned-row-found rows: `{overall['returned_row_found_rows']}`",
        f"- still-waiting rows: `{overall['still_waiting_rows']}`",
        f"- returned-ready rows: `{overall['returned_ready_rows']}`",
        f"- validation-failed rows: `{overall['validation_failed_rows']}`",
        f"- label-attached rows: `{overall['label_attached_rows']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Return validation is not truth intake.",
        "- A returned-ready row still needs BR-103/BR-106 rerun and final adjudication.",
        "- Labels must come from the external 실증/final-review process.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--capture-chain-manifest", default=DEFAULT_CAPTURE_CHAIN_MANIFEST)
    parser.add_argument("--input-manifest", default=None)
    parser.add_argument("--watchlist", default="")
    parser.add_argument("--returned-capture", default=DEFAULT_RETURNED_CAPTURE)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--allow-user-filled-default", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    input_manifest_path, input_manifest = load_input_manifest(repo_root, args.input_manifest)
    watchlist_path = resolve_capture_chain_dependency(
        repo_root,
        args.watchlist,
        DEFAULT_WATCHLIST_ARTIFACT,
        args.capture_chain_manifest,
    )
    explicit_flags = {
        flag
        for flag in ["--returned-capture"]
        if cli_flag_provided(flag, sys.argv[1:])
    }
    returned_capture_path, returned_capture_source = resolve_returned_capture_input(
        repo_root,
        args.returned_capture,
        input_manifest,
        explicit_flags,
    )
    input_resolution_sources = {"returned_capture": returned_capture_source}
    output_dir = resolve_path(repo_root, args.output_dir)
    require_explicit_user_filled_input(
        input_name="returned capture",
        input_path=returned_capture_path,
        default_path=DEFAULT_RETURNED_CAPTURE,
        allow_user_filled_default=args.allow_user_filled_default,
        explicit_flag="--returned-capture",
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    watchlist = read_csv(watchlist_path, WATCHLIST_COLUMNS)
    returned = read_csv(returned_capture_path, CAPTURE_COLUMNS)
    validation = build_validation(watchlist, returned, repo_root)
    summary = build_summary(validation)

    validation_path = output_dir / VALIDATION_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    validation.to_csv(validation_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary, input_manifest_path, input_resolution_sources)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "rows": int(overall["rows"]),
        "returned_row_found_rows": int(overall["returned_row_found_rows"]),
        "still_waiting_rows": int(overall["still_waiting_rows"]),
        "returned_ready_rows": int(overall["returned_ready_rows"]),
        "validation_failed_rows": int(overall["validation_failed_rows"]),
        "label_attached_rows": int(overall["label_attached_rows"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "input_manifest": str(input_manifest_path) if input_manifest_path is not None else "",
        "input_resolution_sources": input_resolution_sources,
        "outputs": {
            "validation": str(validation_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
