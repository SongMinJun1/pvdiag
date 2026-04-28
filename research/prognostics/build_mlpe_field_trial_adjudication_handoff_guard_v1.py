#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-106"
DEFAULT_READINESS_INPUT = "/private/tmp/mlpe_field_trial_capture_readiness_br103_check/mlpe_field_trial_capture_readiness_packet_v1.csv"
DEFAULT_MANIFEST_SUMMARY_INPUT = "/private/tmp/mlpe_field_trial_package_manifest_br105_check/mlpe_field_trial_package_manifest_summary_v1.csv"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_adjudication_handoff_guard_br106_check"

GUARD_OUTPUT_NAME = "mlpe_field_trial_adjudication_handoff_guard_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_adjudication_handoff_guard_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_adjudication_handoff_guard_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_adjudication_handoff_guard_v1.json"

READINESS_COLUMNS = [
    "trial_event_id",
    "capture_status",
    "label_status",
    "readiness_bucket",
    "metadata_ready_flag",
    "required_evidence_paths_filled_flag",
    "required_evidence_paths_exist_flag",
    "final_label_attached",
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_readiness(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing readiness input: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    for col in READINESS_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    out = df.reindex(columns=READINESS_COLUMNS).copy()
    for col in READINESS_COLUMNS:
        out[col] = out[col].map(normalize_text)
    return out


def read_manifest_summary(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(
            [
                {
                    "summary_scope": "overall",
                    "summary_key": "manifest_missing",
                    "required_missing_rows": 1,
                }
            ]
        )
    return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)


def manifest_missing_count(summary: pd.DataFrame) -> int:
    if "summary_scope" not in summary.columns or "required_missing_rows" not in summary.columns:
        return 1
    overall = summary[summary["summary_scope"].astype(str).eq("overall")]
    if overall.empty:
        return 1
    return int(overall.iloc[0]["required_missing_rows"])


def build_guard(readiness: pd.DataFrame, manifest_missing_rows: int) -> pd.DataFrame:
    rows = []
    for _, row in readiness.iterrows():
        bucket = row["readiness_bucket"]
        final_label_attached = int(row["final_label_attached"] == "1")
        capture_ready = bucket == "capture_ready_label_pending"
        label_gate_ready = bucket == "label_attached_truth_gate_required"
        if manifest_missing_rows > 0:
            guard_bucket = "blocked_manifest_missing"
            blocker = "manifest_required_artifact_missing"
            next_action = "Regenerate or restore missing field-trial artifacts before handoff."
        elif row["capture_status"] == "planned":
            guard_bucket = "blocked_planned_capture"
            blocker = "capture_not_filled"
            next_action = "Fill field-trial capture metadata and evidence paths, then rerun readiness."
        elif capture_ready:
            guard_bucket = "adjudication_handoff_ready"
            blocker = ""
            next_action = "Send to final adjudication; keep truth intake blocked until labels are attached."
        elif label_gate_ready or final_label_attached:
            guard_bucket = "truth_gate_required_after_label"
            blocker = "separate_truth_gate_required"
            next_action = "Run a separate truth-intake gate; handoff guard alone is not approval."
        else:
            guard_bucket = "blocked_readiness_incomplete"
            blocker = bucket or "readiness_incomplete"
            next_action = "Resolve readiness blockers before adjudication handoff."
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "trial_event_id": row["trial_event_id"],
                "capture_status": row["capture_status"],
                "label_status": row["label_status"],
                "readiness_bucket": bucket,
                "manifest_required_missing_rows": manifest_missing_rows,
                "adjudication_handoff_allowed": int(guard_bucket == "adjudication_handoff_ready"),
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
                "guard_bucket": guard_bucket,
                "blocker_reason": blocker,
                "next_action": next_action,
            }
        )
    return pd.DataFrame(rows)


def build_summary(guard: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "rows": int(len(guard)),
            "adjudication_handoff_allowed_rows": int(guard["adjudication_handoff_allowed"].sum()),
            "truth_intake_allowed_sum": int(guard["truth_intake_allowed"].sum()),
            "threshold_patch_allowed_sum": int(guard["threshold_patch_allowed"].sum()),
            "engine_patch_allowed_sum": int(guard["engine_patch_allowed"].sum()),
        }
    ]
    for bucket, sub in guard.groupby("guard_bucket", dropna=False):
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "guard_bucket",
                "summary_key": bucket,
                "rows": int(len(sub)),
                "adjudication_handoff_allowed_rows": int(sub["adjudication_handoff_allowed"].sum()),
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
        "# BR-106 MLPE Field-Trial Adjudication Handoff Guard",
        "",
        "## Purpose",
        "- Decide whether filled field-trial rows may be handed to final adjudication.",
        "- Keep truth intake, threshold tuning, and engine patches blocked.",
        "",
        "## Real Result",
        f"- rows: `{overall['rows']}`",
        f"- adjudication handoff allowed rows: `{overall['adjudication_handoff_allowed_rows']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Handoff readiness is not truth readiness.",
        "- Label-attached rows still require a separate truth-intake gate.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--readiness-input", default=DEFAULT_READINESS_INPUT)
    parser.add_argument("--manifest-summary-input", default=DEFAULT_MANIFEST_SUMMARY_INPUT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    readiness_input = resolve_path(repo_root, args.readiness_input)
    manifest_summary_input = resolve_path(repo_root, args.manifest_summary_input)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    readiness = read_readiness(readiness_input)
    manifest_summary = read_manifest_summary(manifest_summary_input)
    guard = build_guard(readiness, manifest_missing_count(manifest_summary))
    summary = build_summary(guard)

    guard_path = output_dir / GUARD_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    guard.to_csv(guard_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "rows": int(overall["rows"]),
        "adjudication_handoff_allowed_rows": int(overall["adjudication_handoff_allowed_rows"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "guard": str(guard_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
