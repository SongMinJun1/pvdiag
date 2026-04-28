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


OWNER_BRANCH = "BR-20260425-110"
DEFAULT_OPERATOR_CHECKLIST_ARTIFACT = "operator_intake_checklist"
DEFAULT_HANDOFF_GUARD_ARTIFACT = "adjudication_handoff_guard"
DEFAULT_DRY_RUN_GATE_SUMMARY_ARTIFACT = "pre_adjudication_dry_run_gate_summary"
DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_real_capture_intake_watchlist_br110_check"

WATCHLIST_OUTPUT_NAME = "mlpe_field_trial_real_capture_intake_watchlist_v1.csv"
SUMMARY_OUTPUT_NAME = "mlpe_field_trial_real_capture_intake_watchlist_summary_v1.csv"
NOTE_OUTPUT_NAME = "mlpe_field_trial_real_capture_intake_watchlist_note_v1.md"
JSON_OUTPUT_NAME = "mlpe_field_trial_real_capture_intake_watchlist_v1.json"


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing input: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False).astype(object)
    return df.where(pd.notna(df), "")


def dry_run_passed(path: Path) -> int:
    if not path.exists():
        return 0
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    if "overall_passed_flag" not in df.columns:
        return 0
    return int(df.iloc[0]["overall_passed_flag"])


def build_watchlist(operator: pd.DataFrame, guard: pd.DataFrame, dry_run_passed_flag: int) -> pd.DataFrame:
    guard_cols = guard[["trial_event_id", "guard_bucket", "adjudication_handoff_allowed"]].copy()
    rows = operator.merge(guard_cols, on="trial_event_id", how="left")
    rows["owner_branch"] = OWNER_BRANCH
    rows["dry_run_gate_passed_flag"] = dry_run_passed_flag
    rows["real_capture_status"] = rows["guard_bucket"].map(
        lambda bucket: "waiting_for_real_capture" if bucket == "blocked_planned_capture" else "review_current_state"
    )
    rows["real_capture_required_flag"] = (rows["real_capture_status"] == "waiting_for_real_capture").astype(int)
    rows["truth_intake_allowed"] = 0
    rows["threshold_patch_allowed"] = 0
    rows["engine_patch_allowed"] = 0
    rows["next_action"] = rows.apply(
        lambda row: "Collect real capture metadata/evidence using BR-104 checklist."
        if row["real_capture_required_flag"] == 1
        else "Review row state before any adjudication handoff.",
        axis=1,
    )
    columns = [
        "owner_branch",
        "trial_event_id",
        "injection_case",
        "planned_fault_family",
        "planned_fault_subtype",
        "br103_readiness_bucket",
        "operator_phase",
        "guard_bucket",
        "adjudication_handoff_allowed",
        "dry_run_gate_passed_flag",
        "real_capture_status",
        "real_capture_required_flag",
        "capture_metadata_to_fill_csv",
        "evidence_paths_to_attach_csv",
        "optional_context_to_attach_csv",
        "truth_intake_allowed",
        "threshold_patch_allowed",
        "engine_patch_allowed",
        "next_action",
    ]
    return rows.reindex(columns=columns)


def build_summary(watchlist: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "owner_branch": OWNER_BRANCH,
                "rows": int(len(watchlist)),
                "dry_run_gate_passed_flag": int(watchlist["dry_run_gate_passed_flag"].min()) if len(watchlist) else 0,
                "real_capture_required_rows": int(watchlist["real_capture_required_flag"].sum()),
                "handoff_allowed_rows": int(pd.to_numeric(watchlist["adjudication_handoff_allowed"], errors="coerce").fillna(0).sum()),
                "truth_intake_allowed_sum": int(watchlist["truth_intake_allowed"].sum()),
                "threshold_patch_allowed_sum": int(watchlist["threshold_patch_allowed"].sum()),
                "engine_patch_allowed_sum": int(watchlist["engine_patch_allowed"].sum()),
            }
        ]
    )


def write_note(output_dir: Path, summary: pd.DataFrame) -> Path:
    row = summary.iloc[0].to_dict()
    note_path = output_dir / NOTE_OUTPUT_NAME
    lines = [
        "# BR-110 MLPE Field-Trial Real Capture Intake Watchlist",
        "",
        "## Purpose",
        "- Convert operator checklist and handoff guard state into a real-capture waiting list.",
        "- Keep the project pointed at field capture rather than premature truth/threshold/engine work.",
        "",
        "## Real Result",
        f"- rows: `{row['rows']}`",
        f"- dry-run gate passed flag: `{row['dry_run_gate_passed_flag']}`",
        f"- real capture required rows: `{row['real_capture_required_rows']}`",
        f"- handoff allowed rows: `{row['handoff_allowed_rows']}`",
        f"- truth intake allowed sum: `{row['truth_intake_allowed_sum']}`",
        f"- threshold patch allowed sum: `{row['threshold_patch_allowed_sum']}`",
        f"- engine patch allowed sum: `{row['engine_patch_allowed_sum']}`",
        "",
        "## Boundary",
        "- Watchlist rows are collection tasks, not labels.",
        "- Field capture and final labels are still external dependencies.",
    ]
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--capture-chain-manifest", default=DEFAULT_CAPTURE_CHAIN_MANIFEST)
    parser.add_argument("--operator-checklist", default="")
    parser.add_argument("--handoff-guard", default="")
    parser.add_argument("--dry-run-gate-summary", default="")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    operator_path = resolve_capture_chain_dependency(
        repo_root,
        args.operator_checklist,
        DEFAULT_OPERATOR_CHECKLIST_ARTIFACT,
        args.capture_chain_manifest,
    )
    guard_path = resolve_capture_chain_dependency(
        repo_root,
        args.handoff_guard,
        DEFAULT_HANDOFF_GUARD_ARTIFACT,
        args.capture_chain_manifest,
    )
    dry_run_summary_path = resolve_capture_chain_dependency(
        repo_root,
        args.dry_run_gate_summary,
        DEFAULT_DRY_RUN_GATE_SUMMARY_ARTIFACT,
        args.capture_chain_manifest,
    )
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    watchlist = build_watchlist(read_csv(operator_path), read_csv(guard_path), dry_run_passed(dry_run_summary_path))
    summary = build_summary(watchlist)

    watchlist_path = output_dir / WATCHLIST_OUTPUT_NAME
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    json_path = output_dir / JSON_OUTPUT_NAME

    watchlist.to_csv(watchlist_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    note_path = write_note(output_dir, summary)

    overall = summary.iloc[0].to_dict()
    payload = {
        "owner_branch": OWNER_BRANCH,
        "rows": int(overall["rows"]),
        "dry_run_gate_passed_flag": int(overall["dry_run_gate_passed_flag"]),
        "real_capture_required_rows": int(overall["real_capture_required_rows"]),
        "handoff_allowed_rows": int(overall["handoff_allowed_rows"]),
        "truth_intake_allowed_sum": int(overall["truth_intake_allowed_sum"]),
        "threshold_patch_allowed_sum": int(overall["threshold_patch_allowed_sum"]),
        "engine_patch_allowed_sum": int(overall["engine_patch_allowed_sum"]),
        "outputs": {
            "watchlist": str(watchlist_path),
            "summary": str(summary_path),
            "note": str(note_path),
            "json": str(json_path),
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
