#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from mlpe_field_trial_user_input_contract_v1 import require_explicit_user_filled_input
except ImportError:
    from research.prognostics.mlpe_field_trial_user_input_contract_v1 import require_explicit_user_filled_input


OWNER_BRANCH = "BR-20260425-112"
DEFAULT_VALIDATION = "/private/tmp/mlpe_field_trial_capture_return_validator_br111_check/mlpe_field_trial_capture_return_validation_v1.csv"
DEFAULT_RETURNED_CAPTURE = "/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_capture_return_evidence_resolver_br112_check"

RESOLUTION_OUTPUT_NAME = "mlpe_field_trial_capture_return_evidence_resolution_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_capture_return_evidence_resolution_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_capture_return_evidence_resolution_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_capture_return_evidence_resolution_v1.json"

VALIDATION_COLUMNS = [
    "trial_event_id",
    "validation_bucket",
    "returned_ready_for_adjudication_flag",
    "still_waiting_for_real_capture_flag",
]

CAPTURE_COLUMNS = [
    "trial_event_id",
    "raw_data_path",
    "peer_data_path",
    "weather_data_path",
    "waveform_slice_path",
]

EVIDENCE_FIELDS = [
    ("raw", "raw_data_path", 1),
    ("peer", "peer_data_path", 1),
    ("weather", "weather_data_path", 0),
    ("waveform", "waveform_slice_path", 1),
]

RESOLUTION_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "validation_bucket",
    "returned_ready_for_adjudication_flag",
    "still_waiting_for_real_capture_flag",
    "evidence_kind",
    "evidence_required_flag",
    "evidence_path_field",
    "evidence_path",
    "evidence_path_filled_flag",
    "evidence_file_exists_flag",
    "evidence_file_size_bytes",
    "evidence_resolution_bucket",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
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


def bool_int(value: object) -> int:
    return int(normalize_text(value) == "1")


def file_size(repo_root: Path, path_text: str) -> tuple[int, int]:
    if not path_text:
        return 0, 0
    path = resolve_path(repo_root, path_text)
    if not path.exists():
        return 0, 0
    return 1, int(path.stat().st_size)


def build_resolution(validation: pd.DataFrame, returned: pd.DataFrame, repo_root: Path) -> pd.DataFrame:
    capture_by_event = {
        normalize_text(row["trial_event_id"]): row
        for _, row in returned.iterrows()
        if normalize_text(row.get("trial_event_id", ""))
    }
    validation_ids = [
        normalize_text(value)
        for value in validation["trial_event_id"].tolist()
        if normalize_text(value)
    ]
    extra_capture_ids = [event_id for event_id in capture_by_event if event_id not in set(validation_ids)]
    ordered_ids = validation_ids + extra_capture_ids

    rows: list[dict[str, object]] = []
    for event_id in ordered_ids:
        validation_match = validation[validation["trial_event_id"].astype(str).eq(event_id)]
        validation_row = validation_match.iloc[0] if not validation_match.empty else pd.Series(dtype=object)
        capture_row = capture_by_event.get(event_id, pd.Series(dtype=object))
        bucket = normalize_text(validation_row.get("validation_bucket", "capture_not_in_validation"))
        ready_flag = bool_int(validation_row.get("returned_ready_for_adjudication_flag", "0"))
        waiting_flag = bool_int(validation_row.get("still_waiting_for_real_capture_flag", "0"))

        for evidence_kind, field, required in EVIDENCE_FIELDS:
            path_text = normalize_text(capture_row.get(field, ""))
            filled = int(bool(path_text))
            exists, size_bytes = file_size(repo_root, path_text)

            if waiting_flag:
                resolution_bucket = "waiting_for_real_capture"
                next_action = "Collect real capture evidence paths after field capture."
            elif not filled and required:
                resolution_bucket = "required_evidence_path_missing"
                next_action = "Attach required evidence path before readiness rerun."
            elif not filled:
                resolution_bucket = "optional_evidence_path_missing"
                next_action = "Optional evidence is absent; continue only if required evidence is complete."
            elif not exists:
                resolution_bucket = "evidence_file_not_found"
                next_action = "Fix the evidence path or regenerate the referenced file."
            elif size_bytes <= 0:
                resolution_bucket = "evidence_file_empty"
                next_action = "Regenerate the evidence file; empty files are not usable."
            else:
                resolution_bucket = "evidence_file_resolved"
                next_action = "Evidence file is resolved; keep truth/threshold/engine approvals blocked."

            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "validation_bucket": bucket,
                    "returned_ready_for_adjudication_flag": ready_flag,
                    "still_waiting_for_real_capture_flag": waiting_flag,
                    "evidence_kind": evidence_kind,
                    "evidence_required_flag": required,
                    "evidence_path_field": field,
                    "evidence_path": path_text,
                    "evidence_path_filled_flag": filled,
                    "evidence_file_exists_flag": exists,
                    "evidence_file_size_bytes": size_bytes,
                    "evidence_resolution_bucket": resolution_bucket,
                    "truth_intake_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "engine_patch_allowed": 0,
                    "next_action": next_action,
                }
            )
    return pd.DataFrame(rows).reindex(columns=RESOLUTION_COLUMNS)


def build_summary(resolution: pd.DataFrame) -> pd.DataFrame:
    event_count = int(resolution["trial_event_id"].nunique()) if len(resolution) else 0
    waiting_events = int(
        resolution[resolution["still_waiting_for_real_capture_flag"].eq(1)]["trial_event_id"].nunique()
    ) if len(resolution) else 0
    ready_events = int(
        resolution[resolution["returned_ready_for_adjudication_flag"].eq(1)]["trial_event_id"].nunique()
    ) if len(resolution) else 0
    missing_required = resolution[
        resolution["evidence_required_flag"].eq(1)
        & ~resolution["evidence_resolution_bucket"].isin(["evidence_file_resolved", "waiting_for_real_capture"])
    ]
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "events": event_count,
            "waiting_events": waiting_events,
            "returned_ready_events": ready_events,
            "evidence_rows": int(len(resolution)),
            "required_evidence_rows": int(resolution["evidence_required_flag"].sum()),
            "evidence_path_filled_rows": int(resolution["evidence_path_filled_flag"].sum()),
            "evidence_file_exists_rows": int(resolution["evidence_file_exists_flag"].sum()),
            "required_evidence_problem_rows": int(len(missing_required)),
            "evidence_file_size_total_bytes": int(resolution["evidence_file_size_bytes"].sum()),
            "truth_intake_allowed_sum": int(resolution["truth_intake_allowed"].sum()),
            "threshold_patch_allowed_sum": int(resolution["threshold_patch_allowed"].sum()),
            "engine_patch_allowed_sum": int(resolution["engine_patch_allowed"].sum()),
        }
    ]
    for bucket, sub in resolution.groupby("evidence_resolution_bucket", dropna=False):
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "evidence_resolution_bucket",
                "summary_key": bucket,
                "events": int(sub["trial_event_id"].nunique()),
                "waiting_events": int(sub[sub["still_waiting_for_real_capture_flag"].eq(1)]["trial_event_id"].nunique()),
                "returned_ready_events": int(sub[sub["returned_ready_for_adjudication_flag"].eq(1)]["trial_event_id"].nunique()),
                "evidence_rows": int(len(sub)),
                "required_evidence_rows": int(sub["evidence_required_flag"].sum()),
                "evidence_path_filled_rows": int(sub["evidence_path_filled_flag"].sum()),
                "evidence_file_exists_rows": int(sub["evidence_file_exists_flag"].sum()),
                "required_evidence_problem_rows": int(
                    len(
                        sub[
                            sub["evidence_required_flag"].eq(1)
                            & ~sub["evidence_resolution_bucket"].isin(["evidence_file_resolved", "waiting_for_real_capture"])
                        ]
                    )
                ),
                "evidence_file_size_total_bytes": int(sub["evidence_file_size_bytes"].sum()),
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
        "# BR-112 MLPE Field-Trial Capture Return Evidence Resolver",
        "",
        "## Purpose",
        "- Resolve returned-capture evidence paths after BR-111 validation.",
        "- Track file existence and byte size without changing validation, truth, threshold, or engine state.",
        "",
        "## Real Result",
        f"- events: `{overall['events']}`",
        f"- waiting events: `{overall['waiting_events']}`",
        f"- returned-ready events: `{overall['returned_ready_events']}`",
        f"- evidence rows: `{overall['evidence_rows']}`",
        f"- required evidence rows: `{overall['required_evidence_rows']}`",
        f"- evidence-path-filled rows: `{overall['evidence_path_filled_rows']}`",
        f"- evidence-file-exists rows: `{overall['evidence_file_exists_rows']}`",
        f"- required evidence problem rows: `{overall['required_evidence_problem_rows']}`",
        f"- evidence file size total bytes: `{overall['evidence_file_size_total_bytes']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Waiting rows are not evidence failures.",
        "- Resolved files are still attachments, not truth labels.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--validation", default=DEFAULT_VALIDATION)
    parser.add_argument("--returned-capture", default=DEFAULT_RETURNED_CAPTURE)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--allow-user-filled-default", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    validation_path = resolve_path(repo_root, args.validation)
    returned_capture_path = resolve_path(repo_root, args.returned_capture)
    output_dir = resolve_path(repo_root, args.output_dir)
    require_explicit_user_filled_input(
        input_name="returned capture",
        input_path=returned_capture_path,
        default_path=DEFAULT_RETURNED_CAPTURE,
        allow_user_filled_default=args.allow_user_filled_default,
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    validation = read_csv(validation_path, VALIDATION_COLUMNS)
    returned = read_csv(returned_capture_path, CAPTURE_COLUMNS)
    resolution = build_resolution(validation, returned, repo_root)
    summary = build_summary(resolution)

    resolution_path = output_dir / RESOLUTION_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    resolution.to_csv(resolution_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "events": int(overall["events"]),
        "waiting_events": int(overall["waiting_events"]),
        "returned_ready_events": int(overall["returned_ready_events"]),
        "evidence_rows": int(overall["evidence_rows"]),
        "required_evidence_rows": int(overall["required_evidence_rows"]),
        "evidence_path_filled_rows": int(overall["evidence_path_filled_rows"]),
        "evidence_file_exists_rows": int(overall["evidence_file_exists_rows"]),
        "required_evidence_problem_rows": int(overall["required_evidence_problem_rows"]),
        "evidence_file_size_total_bytes": int(overall["evidence_file_size_total_bytes"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "resolution": str(resolution_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
