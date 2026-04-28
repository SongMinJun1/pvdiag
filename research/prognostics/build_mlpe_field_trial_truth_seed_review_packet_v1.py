#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OWNER_BRANCH = "BR-20260425-120"
DEFAULT_RUNBOOK_DIR = "/private/tmp/mlpe_field_trial_real_label_intake_runbook_br119_check"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_truth_seed_review_packet_br120_check"

RUNBOOK_SUMMARY_NAME = "mlpe_field_trial_real_label_intake_runbook_summary_v1.csv"
GATE_OUTPUT_NAME = "mlpe_field_trial_label_to_truth_gate_v1.csv"

PACKET_OUTPUT_NAME = "mlpe_field_trial_truth_seed_review_packet_v1.csv"
BLOCKED_OUTPUT_NAME = "mlpe_field_trial_truth_seed_review_blocked_rows_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_truth_seed_review_packet_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_truth_seed_review_packet_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_truth_seed_review_packet_v1.json"

PACKET_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "truth_seed_review_packet_status",
    "truth_candidate_role",
    "reviewer_final_fault_family",
    "reviewer_final_fault_subtype",
    "reviewer_truth_confidence",
    "reviewer_common_cause_clearance",
    "reviewer_measurement_artifact_clearance",
    "reviewer_label_source",
    "label_validation_bucket",
    "truth_gate_bucket",
    "blocker_reason",
    "recommended_review_action",
    "canonical_truth_write_allowed",
    "truth_intake_allowed",
    "threshold_patch_allowed",
    "engine_patch_allowed",
    "source_gate_path",
    "next_action",
]

BLOCKED_COLUMNS = [
    "owner_branch",
    "trial_event_id",
    "truth_seed_review_packet_status",
    "truth_candidate_role",
    "reviewer_final_fault_family",
    "reviewer_final_fault_subtype",
    "reviewer_truth_confidence",
    "truth_gate_bucket",
    "blocker_reason",
    "blocked_review_action",
    "source_gate_path",
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing input: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    out = df.copy()
    for col in out.columns:
        out[col] = out[col].map(normalize_text)
    return out


def int_value(value: object) -> int:
    text = normalize_text(value)
    if not text:
        return 0
    return int(float(text))


def first_summary_value(summary: pd.DataFrame, key: str) -> int:
    if summary.empty or key not in summary.columns:
        return 0
    return int_value(summary.iloc[0][key])


def recommended_action(role: str) -> str:
    if role == "positive_truth_candidate":
        return "Review as positive sidecar truth-seed candidate; require explicit reviewer sign-off before any future write."
    if role == "negative_truth_candidate":
        return "Review as negative-control sidecar truth-seed candidate; require explicit reviewer sign-off before any future write."
    return "Do not include in truth-seed packet."


def build_packet(runbook_summary: pd.DataFrame, gate: pd.DataFrame, source_gate_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    fixture_mismatches = first_summary_value(runbook_summary, "fixture_mismatch_rows")
    gate = gate.copy()
    for col in [
        "truth_gate_ready_flag",
        "truth_gate_blocked_flag",
        "truth_candidate_role",
        "reviewer_final_fault_family",
        "reviewer_final_fault_subtype",
        "reviewer_truth_confidence",
        "reviewer_common_cause_clearance",
        "reviewer_measurement_artifact_clearance",
        "reviewer_label_source",
        "label_validation_bucket",
        "truth_gate_bucket",
        "blocker_reason",
    ]:
        if col not in gate.columns:
            gate[col] = ""

    packet_rows = []
    blocked_rows = []
    for _, row in gate.iterrows():
        event_id = normalize_text(row.get("trial_event_id", ""))
        role = normalize_text(row.get("truth_candidate_role", ""))
        ready = int_value(row.get("truth_gate_ready_flag", "0"))
        blocked = int_value(row.get("truth_gate_blocked_flag", "0"))
        status = "blocked_fixture_contract_mismatch" if fixture_mismatches else "ready_for_sidecar_truth_seed_review"
        if ready and not fixture_mismatches:
            packet_rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "truth_seed_review_packet_status": status,
                    "truth_candidate_role": role,
                    "reviewer_final_fault_family": normalize_text(row.get("reviewer_final_fault_family", "")),
                    "reviewer_final_fault_subtype": normalize_text(row.get("reviewer_final_fault_subtype", "")),
                    "reviewer_truth_confidence": normalize_text(row.get("reviewer_truth_confidence", "")),
                    "reviewer_common_cause_clearance": normalize_text(row.get("reviewer_common_cause_clearance", "")),
                    "reviewer_measurement_artifact_clearance": normalize_text(row.get("reviewer_measurement_artifact_clearance", "")),
                    "reviewer_label_source": normalize_text(row.get("reviewer_label_source", "")),
                    "label_validation_bucket": normalize_text(row.get("label_validation_bucket", "")),
                    "truth_gate_bucket": normalize_text(row.get("truth_gate_bucket", "")),
                    "blocker_reason": normalize_text(row.get("blocker_reason", "")),
                    "recommended_review_action": recommended_action(role),
                    "canonical_truth_write_allowed": 0,
                    "truth_intake_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "engine_patch_allowed": 0,
                    "source_gate_path": str(source_gate_path),
                    "next_action": "Human review must decide whether this sidecar candidate can enter a later explicit truth-intake branch.",
                }
            )
        elif blocked or fixture_mismatches:
            blocked_rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "trial_event_id": event_id,
                    "truth_seed_review_packet_status": "blocked_before_truth_seed_review",
                    "truth_candidate_role": role or "not_truth_candidate",
                    "reviewer_final_fault_family": normalize_text(row.get("reviewer_final_fault_family", "")),
                    "reviewer_final_fault_subtype": normalize_text(row.get("reviewer_final_fault_subtype", "")),
                    "reviewer_truth_confidence": normalize_text(row.get("reviewer_truth_confidence", "")),
                    "truth_gate_bucket": "blocked_fixture_contract_mismatch" if fixture_mismatches else normalize_text(row.get("truth_gate_bucket", "")),
                    "blocker_reason": "fixture_contract_mismatch" if fixture_mismatches else normalize_text(row.get("blocker_reason", "")),
                    "blocked_review_action": "Resolve BR-118 fixture mismatch first." if fixture_mismatches else "Resolve BR-117 truth-gate blocker before truth-seed review.",
                    "source_gate_path": str(source_gate_path),
                }
            )

    return (
        pd.DataFrame(packet_rows).reindex(columns=PACKET_COLUMNS),
        pd.DataFrame(blocked_rows).reindex(columns=BLOCKED_COLUMNS),
    )


def build_summary(runbook_summary: pd.DataFrame, gate: pd.DataFrame, packet: pd.DataFrame, blocked: pd.DataFrame) -> pd.DataFrame:
    fixture_mismatches = first_summary_value(runbook_summary, "fixture_mismatch_rows")
    truth_ready = int(gate["truth_gate_ready_flag"].map(int_value).sum()) if "truth_gate_ready_flag" in gate.columns and len(gate) else 0
    truth_blocked = int(gate["truth_gate_blocked_flag"].map(int_value).sum()) if "truth_gate_blocked_flag" in gate.columns and len(gate) else 0
    positive = int(packet["truth_candidate_role"].eq("positive_truth_candidate").sum()) if len(packet) else 0
    negative = int(packet["truth_candidate_role"].eq("negative_truth_candidate").sum()) if len(packet) else 0
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "summary_scope": "overall",
            "summary_key": "all",
            "fixture_mismatch_rows": fixture_mismatches,
            "source_gate_rows": int(len(gate)),
            "source_truth_gate_ready_rows": truth_ready,
            "source_truth_gate_blocked_rows": truth_blocked,
            "truth_seed_review_packet_rows": int(len(packet)),
            "positive_truth_seed_review_rows": positive,
            "negative_truth_seed_review_rows": negative,
            "blocked_before_truth_seed_review_rows": int(len(blocked)),
            "canonical_truth_write_allowed_sum": int(packet["canonical_truth_write_allowed"].sum()) if len(packet) else 0,
            "truth_intake_allowed_sum": int(packet["truth_intake_allowed"].sum()) if len(packet) else 0,
            "threshold_patch_allowed_sum": int(packet["threshold_patch_allowed"].sum()) if len(packet) else 0,
            "engine_patch_allowed_sum": int(packet["engine_patch_allowed"].sum()) if len(packet) else 0,
        }
    ]
    if len(packet):
        for role, sub in packet.groupby("truth_candidate_role", dropna=False):
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": "truth_candidate_role",
                    "summary_key": role,
                    "fixture_mismatch_rows": fixture_mismatches,
                    "source_gate_rows": int(len(gate)),
                    "source_truth_gate_ready_rows": truth_ready,
                    "source_truth_gate_blocked_rows": truth_blocked,
                    "truth_seed_review_packet_rows": int(len(sub)),
                    "positive_truth_seed_review_rows": int(sub["truth_candidate_role"].eq("positive_truth_candidate").sum()),
                    "negative_truth_seed_review_rows": int(sub["truth_candidate_role"].eq("negative_truth_candidate").sum()),
                    "blocked_before_truth_seed_review_rows": 0,
                    "canonical_truth_write_allowed_sum": int(sub["canonical_truth_write_allowed"].sum()),
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
        "# BR-120 MLPE Field-Trial Truth-Seed Review Packet",
        "",
        "## Purpose",
        "- Convert BR-119/BR-117 gate-ready rows into a sidecar truth-seed review packet.",
        "- Keep blocked gate rows separate from review candidates.",
        "- Keep canonical truth, threshold replay, and engine patches locked.",
        "",
        "## Result",
        f"- fixture mismatch rows: `{overall['fixture_mismatch_rows']}`",
        f"- source gate rows: `{overall['source_gate_rows']}`",
        f"- source truth-gate-ready rows: `{overall['source_truth_gate_ready_rows']}`",
        f"- source truth-gate-blocked rows: `{overall['source_truth_gate_blocked_rows']}`",
        f"- truth-seed review packet rows: `{overall['truth_seed_review_packet_rows']}`",
        f"- positive truth-seed review rows: `{overall['positive_truth_seed_review_rows']}`",
        f"- negative truth-seed review rows: `{overall['negative_truth_seed_review_rows']}`",
        f"- blocked before truth-seed review rows: `{overall['blocked_before_truth_seed_review_rows']}`",
        f"- canonical truth write allowed sum: `{overall['canonical_truth_write_allowed_sum']}`",
        f"- truth intake allowed sum: `{overall['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{overall['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{overall['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Packet rows are review candidates only, not canonical truth rows.",
        "- Canonical truth writes stay locked to `0`.",
        "- `panel_day_engine.py` remains untouched.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--runbook-dir", default=DEFAULT_RUNBOOK_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    runbook_dir = resolve_path(repo_root, args.runbook_dir)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    runbook_summary_path = runbook_dir / RUNBOOK_SUMMARY_NAME
    source_gate_path = runbook_dir / "br117_label_to_truth_gate" / GATE_OUTPUT_NAME
    runbook_summary = read_csv(runbook_summary_path)
    gate = read_csv(source_gate_path)
    packet, blocked = build_packet(runbook_summary, gate, source_gate_path)
    summary = build_summary(runbook_summary, gate, packet, blocked)

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
        "fixture_mismatch_rows": int(overall["fixture_mismatch_rows"]),
        "source_gate_rows": int(overall["source_gate_rows"]),
        "source_truth_gate_ready_rows": int(overall["source_truth_gate_ready_rows"]),
        "source_truth_gate_blocked_rows": int(overall["source_truth_gate_blocked_rows"]),
        "truth_seed_review_packet_rows": int(overall["truth_seed_review_packet_rows"]),
        "positive_truth_seed_review_rows": int(overall["positive_truth_seed_review_rows"]),
        "negative_truth_seed_review_rows": int(overall["negative_truth_seed_review_rows"]),
        "blocked_before_truth_seed_review_rows": int(overall["blocked_before_truth_seed_review_rows"]),
        "canonical_truth_write_allowed_sum": int(overall["canonical_truth_write_allowed_sum"]),
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
