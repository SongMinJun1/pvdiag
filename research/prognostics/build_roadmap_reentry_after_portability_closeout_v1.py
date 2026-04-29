#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

try:
    from build_path_portability_axis_closeout_decision_v1 import (
        build_checkpoint as build_path_closeout_checkpoint,
        build_detail_rows as build_path_closeout_detail_rows,
        build_payload as build_path_closeout_payload,
    )
except ImportError:
    from research.prognostics.build_path_portability_axis_closeout_decision_v1 import (
        build_checkpoint as build_path_closeout_checkpoint,
        build_detail_rows as build_path_closeout_detail_rows,
        build_payload as build_path_closeout_payload,
    )


OWNER_BRANCH = "BR-20260430-241"

DETAIL_OUTPUT_NAME = "roadmap_reentry_after_portability_closeout_v1.csv"
SUMMARY_OUTPUT_NAME = "roadmap_reentry_after_portability_closeout_summary_v1.csv"
NEXT_OUTPUT_NAME = "roadmap_reentry_after_portability_closeout_next_actions_v1.csv"
NOTE_OUTPUT_NAME = "roadmap_reentry_after_portability_closeout_note_v1.md"
JSON_OUTPUT_NAME = "roadmap_reentry_after_portability_closeout_v1.json"

DEFAULT_QUEUE = "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_128_TO_150_EXECUTION_QUEUE_V1.csv"

DETAIL_COLUMNS = [
    "owner_branch",
    "checkpoint_id",
    "checkpoint_group",
    "gate_key",
    "observed_value",
    "required_value",
    "checkpoint_status",
    "roadmap_claim",
    "blocked_by",
    "truth_intake_allowed_rows",
    "threshold_patch_allowed_rows",
    "engine_patch_allowed_rows",
    "operator_facing_change_allowed_rows",
    "recommended_next_action",
]

NEXT_COLUMNS = [
    "owner_branch",
    "next_action_order",
    "action_id",
    "action_type",
    "requires_real_capture_or_label_flag",
    "safe_without_real_data_flag",
    "status",
    "action_detail",
]

SUMMARY_COLUMNS = ["owner_branch", "summary_scope", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Re-enter the algorithm/field-trial roadmap after path-portability closeout. "
            "This is audit-only and does not authorize truth, threshold, or engine writes."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--queue-input",
        type=Path,
        default=Path(DEFAULT_QUEUE),
        help="BR-128..150 execution queue CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for roadmap reentry outputs. Required to avoid hidden temp defaults.",
    )
    parser.add_argument("--max-file-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def read_queue(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    for col in ["branch", "sequence_no", "runway_stage", "status", "blocked_by", "next_action"]:
        if col not in df.columns:
            df[col] = ""
    out = df.copy()
    for col in out.columns:
        out[col] = out[col].map(normalize_text)
    return out


def int_value(value: object) -> int:
    text = normalize_text(value)
    return int(float(text)) if text else 0


def queue_metrics(queue: pd.DataFrame) -> dict[str, int]:
    try:
        sequence_ok = int([int_value(x) for x in queue["sequence_no"].tolist()] == list(range(1, 24)))
    except Exception:
        sequence_ok = 0
    status = queue["status"].map(normalize_text)
    br130 = queue[queue["branch"].eq("BR-20260425-130")]
    br144 = queue[queue["branch"].eq("BR-20260425-144")]
    br150 = queue[queue["branch"].eq("BR-20260425-150")]
    return {
        "queue_rows": int(len(queue)),
        "queue_sequence_ok": sequence_ok,
        "complete_rows": int(status.eq("complete_this_branch").sum()),
        "blocked_rows": int(status.str.startswith("blocked_").sum()),
        "open_rows": int(status.eq("open_now").sum()),
        "br130_waiting_real_data": int(
            not br130.empty and normalize_text(br130.iloc[0].get("status", "")) == "blocked_waiting_real_data"
        ),
        "br144_waiting_prepatch": int(
            not br144.empty and normalize_text(br144.iloc[0].get("status", "")) == "blocked_waiting_prepatch"
        ),
        "br150_waiting_readiness_audit": int(
            not br150.empty
            and normalize_text(br150.iloc[0].get("status", "")) == "blocked_waiting_readiness_audit"
        ),
    }


def status_for(observed: int, required: int, comparator: str) -> str:
    if comparator == "eq":
        return "pass" if observed == required else "fail"
    if comparator == "ge":
        return "pass" if observed >= required else "fail"
    raise ValueError(f"unknown comparator: {comparator}")


def checkpoint_row(
    index: int,
    group: str,
    gate_key: str,
    observed: int,
    required: int,
    comparator: str,
    roadmap_claim: str,
    blocked_by: str,
    recommended_next_action: str,
) -> dict[str, object]:
    return {
        "owner_branch": OWNER_BRANCH,
        "checkpoint_id": f"BR241-{index:03d}",
        "checkpoint_group": group,
        "gate_key": gate_key,
        "observed_value": observed,
        "required_value": required,
        "checkpoint_status": status_for(observed, required, comparator),
        "roadmap_claim": roadmap_claim,
        "blocked_by": blocked_by,
        "truth_intake_allowed_rows": 0,
        "threshold_patch_allowed_rows": 0,
        "engine_patch_allowed_rows": 0,
        "operator_facing_change_allowed_rows": 0,
        "recommended_next_action": recommended_next_action,
    }


def build_path_closeout(repo_root: Path, max_file_bytes: int) -> dict[str, object]:
    checkpoint_payload = build_path_closeout_checkpoint(repo_root, max_file_bytes)
    detail_rows = build_path_closeout_detail_rows(checkpoint_payload)
    return build_path_closeout_payload(detail_rows, checkpoint_payload)


def build_detail_rows(path_payload: dict[str, object], queue: pd.DataFrame) -> list[dict[str, object]]:
    q = queue_metrics(queue)
    specs = [
        (
            "path_portability_closeout",
            "path_portability_axis_closeout_ready",
            int(path_payload["path_portability_axis_closeout_ready"]),
            1,
            "eq",
            "path portability is no longer the active blocker",
            "none",
            "keep path-portability closed unless a checkpoint row fails",
        ),
        (
            "path_portability_closeout",
            "final_cleanup_pr_required",
            int(path_payload["final_cleanup_pr_required"]),
            0,
            "eq",
            "no final bulk cleanup PR is required",
            "none",
            "do not open a broad literal cleanup branch",
        ),
        (
            "roadmap_queue",
            "queue_rows",
            q["queue_rows"],
            23,
            "eq",
            "BR-128..150 queue is present",
            "queue mismatch",
            "repair queue before choosing next branch",
        ),
        (
            "roadmap_queue",
            "queue_sequence_ok",
            q["queue_sequence_ok"],
            1,
            "eq",
            "BR-128..150 queue sequence is contiguous",
            "queue sequence mismatch",
            "repair queue sequence before choosing next branch",
        ),
        (
            "roadmap_queue",
            "open_rows",
            q["open_rows"],
            0,
            "eq",
            "no runway branch is accidentally open",
            "open branch in queue",
            "resolve open queue rows before continuing",
        ),
        (
            "field_trial_boundary",
            "br130_waiting_real_data",
            q["br130_waiting_real_data"],
            1,
            "eq",
            "real capture intake is the next data-dependent gate",
            "real KTC ESS capture CSV absent",
            "wait for or explicitly ingest real capture CSV before BR-130",
        ),
        (
            "algorithm_boundary",
            "br144_waiting_prepatch",
            q["br144_waiting_prepatch"],
            1,
            "eq",
            "panel-engine semantic patch remains blocked",
            "truth replay / selected rule / shadow / prepatch evidence absent",
            "do not edit pv_ae/panel_day_engine.py",
        ),
        (
            "completion_boundary",
            "br150_waiting_readiness_audit",
            q["br150_waiting_readiness_audit"],
            1,
            "eq",
            "BR-150 is still a prelabel checkpoint, not final completion",
            "official downstream readiness not rerun with real labels",
            "do not claim algorithm completion or performance improvement",
        ),
    ]
    return [checkpoint_row(index, *spec) for index, spec in enumerate(specs, start=1)]


def build_next_actions() -> list[dict[str, object]]:
    rows = [
        {
            "owner_branch": OWNER_BRANCH,
            "next_action_order": 1,
            "action_id": "real_capture_csv_arrival",
            "action_type": "field_trial_input",
            "requires_real_capture_or_label_flag": 1,
            "safe_without_real_data_flag": 0,
            "status": "blocked_waiting_real_data",
            "action_detail": "When KTC ESS capture CSV arrives, run BR-130 real capture intake through the existing fail-closed contract.",
        },
        {
            "owner_branch": OWNER_BRANCH,
            "next_action_order": 2,
            "action_id": "source_evidence_and_clearance_runs",
            "action_type": "field_trial_evidence_resolution",
            "requires_real_capture_or_label_flag": 1,
            "safe_without_real_data_flag": 0,
            "status": "blocked_waiting_real_data",
            "action_detail": "After BR-130, run source/evidence resolver and common-cause/artifact/MLPE-control clearance lanes before truth packaging.",
        },
        {
            "owner_branch": OWNER_BRANCH,
            "next_action_order": 3,
            "action_id": "truth_replay_and_rule_candidate",
            "action_type": "algorithm_evidence",
            "requires_real_capture_or_label_flag": 1,
            "safe_without_real_data_flag": 0,
            "status": "blocked_waiting_truth_replay",
            "action_detail": "Only after sidecar truth package and replay scorecard exist, select at most one candidate rule for shadow application.",
        },
        {
            "owner_branch": OWNER_BRANCH,
            "next_action_order": 4,
            "action_id": "owner_scoped_doc_or_manifest_refresh",
            "action_type": "repo_bookkeeping",
            "requires_real_capture_or_label_flag": 0,
            "safe_without_real_data_flag": 1,
            "status": "allowed_if_needed",
            "action_detail": "If a future owner file is touched, refresh only that scoped manifest/path literal; do not reopen broad portability cleanup.",
        },
    ]
    return rows


def build_payload(
    detail_rows: list[dict[str, object]],
    next_rows: list[dict[str, object]],
    path_payload: dict[str, object],
    queue: pd.DataFrame,
) -> dict[str, object]:
    status_counts = Counter(str(row["checkpoint_status"]) for row in detail_rows)
    group_counts = Counter(str(row["checkpoint_group"]) for row in detail_rows)
    q = queue_metrics(queue)
    fail_rows = status_counts.get("fail", 0)
    truth_allowed = sum(int(row["truth_intake_allowed_rows"]) for row in detail_rows)
    threshold_allowed = sum(int(row["threshold_patch_allowed_rows"]) for row in detail_rows)
    engine_allowed = sum(int(row["engine_patch_allowed_rows"]) for row in detail_rows)
    operator_allowed = sum(int(row["operator_facing_change_allowed_rows"]) for row in detail_rows)
    roadmap_reentry_ready = int(
        fail_rows == 0
        and truth_allowed == 0
        and threshold_allowed == 0
        and engine_allowed == 0
        and operator_allowed == 0
    )
    return {
        "owner_branch": OWNER_BRANCH,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "roadmap_reentry_ready": roadmap_reentry_ready,
        "checkpoint_rows": len(detail_rows),
        "checkpoint_pass_rows": status_counts.get("pass", 0),
        "checkpoint_fail_rows": fail_rows,
        "path_portability_axis_closeout_ready": int(path_payload["path_portability_axis_closeout_ready"]),
        "final_cleanup_pr_required": int(path_payload["final_cleanup_pr_required"]),
        "path_portability_axis_status": str(path_payload["path_portability_axis_status"]),
        "queue_rows": q["queue_rows"],
        "queue_sequence_ok": q["queue_sequence_ok"],
        "queue_complete_rows": q["complete_rows"],
        "queue_blocked_rows": q["blocked_rows"],
        "queue_open_rows": q["open_rows"],
        "br130_waiting_real_data": q["br130_waiting_real_data"],
        "br144_waiting_prepatch": q["br144_waiting_prepatch"],
        "br150_waiting_readiness_audit": q["br150_waiting_readiness_audit"],
        "real_capture_required_to_continue": 1,
        "truth_intake_allowed_rows": truth_allowed,
        "threshold_patch_allowed_rows": threshold_allowed,
        "engine_patch_allowed_rows": engine_allowed,
        "operator_facing_change_allowed_rows": operator_allowed,
        "next_actions": len(next_rows),
        "safe_without_real_data_next_actions": sum(int(row["safe_without_real_data_flag"]) for row in next_rows),
        "real_data_required_next_actions": sum(int(row["requires_real_capture_or_label_flag"]) for row in next_rows),
        "checkpoint_status_counts": dict(sorted(status_counts.items())),
        "checkpoint_group_counts": dict(sorted(group_counts.items())),
        "recommended_next_branch": (
            "ktc_ess_real_capture_intake_when_csv_arrives"
            if roadmap_reentry_ready
            else "inspect_roadmap_reentry_failures"
        ),
    }


def summary_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    keys = [
        "roadmap_reentry_ready",
        "checkpoint_rows",
        "checkpoint_pass_rows",
        "checkpoint_fail_rows",
        "path_portability_axis_closeout_ready",
        "final_cleanup_pr_required",
        "queue_rows",
        "queue_sequence_ok",
        "queue_complete_rows",
        "queue_blocked_rows",
        "queue_open_rows",
        "br130_waiting_real_data",
        "br144_waiting_prepatch",
        "br150_waiting_readiness_audit",
        "real_capture_required_to_continue",
        "truth_intake_allowed_rows",
        "threshold_patch_allowed_rows",
        "engine_patch_allowed_rows",
        "operator_facing_change_allowed_rows",
        "next_actions",
        "safe_without_real_data_next_actions",
        "real_data_required_next_actions",
    ]
    rows: list[dict[str, object]] = []
    for key in keys:
        rows.append(
            {
                "owner_branch": OWNER_BRANCH,
                "summary_scope": "overall",
                "key": key,
                "count": int(payload[key]),
            }
        )
    for scope_key in ["checkpoint_status_counts", "checkpoint_group_counts"]:
        scope = scope_key.removesuffix("_counts")
        for key, value in payload[scope_key].items():
            rows.append(
                {
                    "owner_branch": OWNER_BRANCH,
                    "summary_scope": scope,
                    "key": key,
                    "count": value,
                }
            )
    return rows


def render_note(payload: dict[str, object]) -> str:
    return "\n".join(
        [
            "# Roadmap Reentry After Portability Closeout V1",
            "",
            "## Summary",
            "- Re-enters the algorithm/field-trial roadmap after BR-240 path-portability closeout.",
            "- Confirms path portability is no longer the active blocker.",
            "- Confirms semantic progress still waits for real KTC ESS capture/label evidence.",
            "",
            "## Position",
            f"- roadmap_reentry_ready: `{payload['roadmap_reentry_ready']}`",
            f"- path_portability_axis_status: `{payload['path_portability_axis_status']}`",
            f"- queue_rows: `{payload['queue_rows']}`",
            f"- queue_complete_rows: `{payload['queue_complete_rows']}`",
            f"- queue_blocked_rows: `{payload['queue_blocked_rows']}`",
            f"- queue_open_rows: `{payload['queue_open_rows']}`",
            f"- real_capture_required_to_continue: `{payload['real_capture_required_to_continue']}`",
            "",
            "## Boundary",
            f"- truth_intake_allowed_rows: `{payload['truth_intake_allowed_rows']}`",
            f"- threshold_patch_allowed_rows: `{payload['threshold_patch_allowed_rows']}`",
            f"- engine_patch_allowed_rows: `{payload['engine_patch_allowed_rows']}`",
            f"- operator_facing_change_allowed_rows: `{payload['operator_facing_change_allowed_rows']}`",
            "- This branch does not claim algorithm completion or performance improvement.",
            "",
            "## Next Decision",
            f"- Next safe branch: `{payload['recommended_next_branch']}`.",
            "- If no real CSV/labels are available yet, only owner-scoped bookkeeping is safe.",
        ]
    ) + "\n"


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    queue_path = args.queue_input if args.queue_input.is_absolute() else repo_root / args.queue_input

    path_payload = build_path_closeout(repo_root, args.max_file_bytes)
    queue = read_queue(queue_path)
    detail_rows = build_detail_rows(path_payload, queue)
    next_rows = build_next_actions()
    payload = build_payload(detail_rows, next_rows, path_payload, queue)

    write_csv(output_dir / DETAIL_OUTPUT_NAME, detail_rows, DETAIL_COLUMNS)
    write_csv(output_dir / NEXT_OUTPUT_NAME, next_rows, NEXT_COLUMNS)
    write_csv(output_dir / SUMMARY_OUTPUT_NAME, summary_rows(payload), SUMMARY_COLUMNS)
    (output_dir / NOTE_OUTPUT_NAME).write_text(render_note(payload), encoding="utf-8")
    (output_dir / JSON_OUTPUT_NAME).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
