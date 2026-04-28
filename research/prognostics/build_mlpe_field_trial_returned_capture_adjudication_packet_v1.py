#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from mlpe_field_trial_chain_manifest_v1 import DEFAULT_CAPTURE_CHAIN_MANIFEST, resolve_capture_chain_dependency
except ImportError:
    from research.prognostics.mlpe_field_trial_chain_manifest_v1 import (
        DEFAULT_CAPTURE_CHAIN_MANIFEST,
        resolve_capture_chain_dependency,
    )


OWNER_BRANCH = "BR-20260425-114"
DEFAULT_PREFLIGHT_ARTIFACT = "capture_return_rerun_preflight"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_returned_capture_adjudication_packet_br114_check"

PACKET_OUTPUT_NAME = "mlpe_field_trial_returned_capture_adjudication_packet_v1.csv"
BLOCKED_OUTPUT_NAME = "mlpe_field_trial_returned_capture_adjudication_blocked_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_returned_capture_adjudication_packet_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_returned_capture_adjudication_packet_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_returned_capture_adjudication_packet_v1.json"

PREFLIGHT_COLUMNS = [
    "trial_event_id",
    "validation_bucket",
    "required_evidence_rows",
    "required_evidence_resolved_rows",
    "required_evidence_problem_rows",
    "readiness_handoff_rerun_allowed",
    "post_return_rerun_bucket",
]

PACKET_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "packet_status",
    "source_preflight_bucket",
    "required_evidence_rows",
    "required_evidence_resolved_rows",
    "required_evidence_problem_rows",
    "reviewer_final_fault_family",
    "reviewer_final_fault_subtype",
    "reviewer_truth_confidence",
    "reviewer_common_cause_clearance",
    "reviewer_measurement_artifact_clearance",
    "reviewer_notes",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "next_action",
]

BLOCKED_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "blocked_bucket",
    "source_preflight_bucket",
    "readiness_handoff_rerun_allowed",
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


def int_flag(value: object) -> int:
    return int(normalize_text(value) == "1")


def build_packet(preflight: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    packet_rows = []
    blocked_rows = []
    for _, row in preflight.iterrows():
        event_id = normalize_text(row["trial_event_id"])
        allowed = int_flag(row["readiness_handoff_rerun_allowed"])
        bucket = normalize_text(row["post_return_rerun_bucket"])
        if allowed:
            packet_rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "packet_status": "ready_for_final_adjudication_packet",
                    "source_preflight_bucket": bucket,
                    "required_evidence_rows": normalize_text(row["required_evidence_rows"]),
                    "required_evidence_resolved_rows": normalize_text(row["required_evidence_resolved_rows"]),
                    "required_evidence_problem_rows": normalize_text(row["required_evidence_problem_rows"]),
                    "reviewer_final_fault_family": "",
                    "reviewer_final_fault_subtype": "",
                    "reviewer_truth_confidence": "",
                    "reviewer_common_cause_clearance": "",
                    "reviewer_measurement_artifact_clearance": "",
                    "reviewer_notes": "",
                    "truth_intake_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "engine_patch_allowed": 0,
                    "next_action": "Fill final adjudication fields from external 실증 review only.",
                }
            )
        else:
            blocked_rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "blocked_bucket": bucket or "preflight_not_allowed",
                    "source_preflight_bucket": bucket,
                    "readiness_handoff_rerun_allowed": allowed,
                    "truth_intake_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "engine_patch_allowed": 0,
                    "next_action": "Do not create adjudication packet until BR-113 allows rerun.",
                }
            )
    return (
        pd.DataFrame(packet_rows).reindex(columns=PACKET_COLUMNS),
        pd.DataFrame(blocked_rows).reindex(columns=BLOCKED_COLUMNS),
    )


def build_summary(packet: pd.DataFrame, blocked: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "packet_rows": int(len(packet)),
            "blocked_rows": int(len(blocked)),
            "truth_intake_allowed_sum": int(packet["truth_intake_allowed"].sum()) if len(packet) else 0,
            "threshold_patch_allowed_sum": int(packet["threshold_patch_allowed"].sum()) if len(packet) else 0,
            "engine_patch_allowed_sum": int(packet["engine_patch_allowed"].sum()) if len(packet) else 0,
        }
    ]
    if len(blocked):
        for bucket, sub in blocked.groupby("blocked_bucket", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "blocked_bucket",
                    "summary_key": bucket,
                    "packet_rows": 0,
                    "blocked_rows": int(len(sub)),
                    "truth_intake_allowed_sum": 0,
                    "threshold_patch_allowed_sum": 0,
                    "engine_patch_allowed_sum": 0,
                }
            )
    return pd.DataFrame(rows)


def write_note(output_dir: Path, summary: pd.DataFrame) -> Path:
    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-114 MLPE Field-Trial Returned Capture Adjudication Packet",
        "",
        "## Purpose",
        "- Create final-adjudication packet rows only after BR-113 allows readiness/handoff rerun.",
        "- Keep reviewer label fields blank until external 실증 review supplies them.",
        "",
        "## Real Result",
        f"- packet rows: `{overall['packet_rows']}`",
        f"- blocked rows: `{overall['blocked_rows']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Packet generation is not truth intake.",
        "- Blank reviewer fields are intentional until real final labels arrive.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--capture-chain-manifest", default=DEFAULT_CAPTURE_CHAIN_MANIFEST)
    parser.add_argument("--preflight", default="")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    preflight_path = resolve_capture_chain_dependency(
        repo_root,
        args.preflight,
        DEFAULT_PREFLIGHT_ARTIFACT,
        args.capture_chain_manifest,
    )
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    preflight = read_csv(preflight_path, PREFLIGHT_COLUMNS)
    packet, blocked = build_packet(preflight)
    summary = build_summary(packet, blocked)

    packet_path = output_dir / PACKET_OUTPUT_NAME
    blocked_path = output_dir / BLOCKED_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    packet.to_csv(packet_path, index=False, encoding="utf-8-sig")
    blocked.to_csv(blocked_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    overall = summary[summary["summary_scope"].eq("overall")].iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "packet_rows": int(overall["packet_rows"]),
        "blocked_rows": int(overall["blocked_rows"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "packet": str(packet_path),
            "blocked": str(blocked_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
