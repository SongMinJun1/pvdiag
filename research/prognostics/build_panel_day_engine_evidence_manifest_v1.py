#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd


DETAIL_OUTPUT_NAME = "panel_day_engine_evidence_manifest_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_evidence_manifest_summary_v1.csv"
JSON_OUTPUT_NAME = "panel_day_engine_evidence_pack_manifest_v1.json"
PACK_ROOT_DIRNAME = "evidence_pack_root"

RUNTIME_REPRO_COMMAND = (
    "python3 release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py "
    "--data-root /Users/b9gc/pvdiag/data "
    "--output-root /private/tmp/conalog_mlpe_seed_expand_check "
    "--sites conalog gangui ktc_ess"
)
REPORT_ENTRY_REPRO_COMMAND = (
    "python3 research/prognostics/build_panel_day_engine_report_entry_friction_axis_v1.py "
    "--data-root /Users/b9gc/pvdiag/data "
    "--result-root /private/tmp/conalog_mlpe_seed_expand_check/result "
    "--output-dir /private/tmp/report_entry_friction_axis_sidecar_check "
    "--sites conalog gangui ktc_ess"
)
RECOVERY_REPRO_COMMAND = (
    "python3 research/prognostics/build_panel_day_engine_recovery_recurrence_axis_v1.py "
    "--data-root /Users/b9gc/pvdiag/data "
    "--result-root /private/tmp/conalog_mlpe_seed_expand_check/result "
    "--output-dir /private/tmp/recovery_recurrence_axis_sidecar_check "
    "--sites conalog gangui ktc_ess"
)
GROUP_OFF_REPRO_COMMAND = "manual_oneoff_scan_locked_in_docs: BR-20260424-037"
OPPORTUNITY_REPRO_COMMAND = "manual_oneoff_scan_locked_in_docs: BR-20260424-039"

ARTIFACT_SPECS = [
    {
        "evidence_family": "report_lane_result_base",
        "judgment_role": "candidate_reservoir",
        "root_key": "result_root",
        "relative_path": "fault_panel_result_current_v1.csv",
        "artifact_kind": "result_csv",
        "latest_decision_log": "DL-20260424-017",
        "repro_mode": "runtime_run",
        "repro_command": RUNTIME_REPRO_COMMAND,
    },
    {
        "evidence_family": "report_lane_result_base",
        "judgment_role": "candidate_reservoir",
        "root_key": "result_root",
        "relative_path": "fault_panel_result_current_preview_v1.csv",
        "artifact_kind": "preview_csv",
        "latest_decision_log": "DL-20260424-017",
        "repro_mode": "runtime_run",
        "repro_command": RUNTIME_REPRO_COMMAND,
    },
    {
        "evidence_family": "report_lane_result_base",
        "judgment_role": "candidate_reservoir",
        "root_key": "result_root",
        "relative_path": "fault_panel_result_precursor_report_v1.csv",
        "artifact_kind": "result_csv",
        "latest_decision_log": "DL-20260424-017",
        "repro_mode": "runtime_run",
        "repro_command": RUNTIME_REPRO_COMMAND,
    },
    {
        "evidence_family": "report_lane_result_base",
        "judgment_role": "candidate_reservoir",
        "root_key": "result_root",
        "relative_path": "fault_panel_result_raw_only_current_v1.csv",
        "artifact_kind": "result_csv",
        "latest_decision_log": "DL-20260424-017",
        "repro_mode": "runtime_run",
        "repro_command": RUNTIME_REPRO_COMMAND,
    },
    {
        "evidence_family": "report_lane_result_base",
        "judgment_role": "candidate_reservoir",
        "root_key": "result_root",
        "relative_path": "fault_panel_result_raw_only_current_preview_v1.csv",
        "artifact_kind": "preview_csv",
        "latest_decision_log": "DL-20260424-017",
        "repro_mode": "runtime_run",
        "repro_command": RUNTIME_REPRO_COMMAND,
    },
    {
        "evidence_family": "report_lane_result_base",
        "judgment_role": "candidate_reservoir",
        "root_key": "result_root",
        "relative_path": "fault_panel_result_raw_only_fault_signal_report_v1.csv",
        "artifact_kind": "result_csv",
        "latest_decision_log": "DL-20260424-017",
        "repro_mode": "runtime_run",
        "repro_command": RUNTIME_REPRO_COMMAND,
    },
    {
        "evidence_family": "runtime_summary_context",
        "judgment_role": "supportive_hint",
        "root_key": "result_root",
        "relative_path": "fault_panel_result_master_report_v1.md",
        "artifact_kind": "report_markdown",
        "latest_decision_log": "DL-20260424-020",
        "repro_mode": "runtime_run",
        "repro_command": RUNTIME_REPRO_COMMAND,
    },
    {
        "evidence_family": "runtime_summary_context",
        "judgment_role": "supportive_hint",
        "root_key": "result_root",
        "relative_path": "fault_panel_result_current_report_v1.md",
        "artifact_kind": "report_markdown",
        "latest_decision_log": "DL-20260424-020",
        "repro_mode": "runtime_run",
        "repro_command": RUNTIME_REPRO_COMMAND,
    },
    {
        "evidence_family": "runtime_summary_context",
        "judgment_role": "supportive_hint",
        "root_key": "result_root",
        "relative_path": "fault_panel_result_raw_only_current_report_v1.md",
        "artifact_kind": "report_markdown",
        "latest_decision_log": "DL-20260424-020",
        "repro_mode": "runtime_run",
        "repro_command": RUNTIME_REPRO_COMMAND,
    },
    {
        "evidence_family": "runtime_summary_context",
        "judgment_role": "supportive_hint",
        "root_key": "result_root",
        "relative_path": "live_chain_summary_v1.json",
        "artifact_kind": "summary_json",
        "latest_decision_log": "DL-20260424-020",
        "repro_mode": "runtime_run",
        "repro_command": RUNTIME_REPRO_COMMAND,
    },
    {
        "evidence_family": "runtime_summary_context",
        "judgment_role": "supportive_hint",
        "root_key": "result_root",
        "relative_path": "raw_only_chain_summary_v1.json",
        "artifact_kind": "summary_json",
        "latest_decision_log": "DL-20260424-020",
        "repro_mode": "runtime_run",
        "repro_command": RUNTIME_REPRO_COMMAND,
    },
    {
        "evidence_family": "operator_surface_preview",
        "judgment_role": "supportive_hint",
        "root_key": "result_root",
        "relative_path": "fault6_fixed_result_table_v1.csv",
        "artifact_kind": "preview_csv",
        "latest_decision_log": "DL-20260424-020",
        "repro_mode": "runtime_run",
        "repro_command": RUNTIME_REPRO_COMMAND,
    },
    {
        "evidence_family": "operator_surface_preview",
        "judgment_role": "supportive_hint",
        "root_key": "result_root",
        "relative_path": "fault6_label_and_algorithm_preview_v1.csv",
        "artifact_kind": "preview_csv",
        "latest_decision_log": "DL-20260424-020",
        "repro_mode": "runtime_run",
        "repro_command": RUNTIME_REPRO_COMMAND,
    },
    {
        "evidence_family": "operator_surface_preview",
        "judgment_role": "supportive_hint",
        "root_key": "result_root",
        "relative_path": "fault_panel_result_detailed_report_v1.xlsx",
        "artifact_kind": "report_xlsx",
        "latest_decision_log": "DL-20260424-020",
        "repro_mode": "runtime_run",
        "repro_command": RUNTIME_REPRO_COMMAND,
    },
    {
        "evidence_family": "group_off_report_lane_blocker",
        "judgment_role": "structural_blocker",
        "root_key": "group_off_root",
        "relative_path": "group_off_report_lane_blocker_table_v1.csv",
        "artifact_kind": "detail_csv",
        "latest_decision_log": "DL-20260424-019",
        "repro_mode": "manual_oneoff",
        "repro_command": GROUP_OFF_REPRO_COMMAND,
    },
    {
        "evidence_family": "group_off_report_lane_blocker",
        "judgment_role": "structural_blocker",
        "root_key": "group_off_root",
        "relative_path": "group_off_report_lane_blocker_summary_v1.csv",
        "artifact_kind": "summary_csv",
        "latest_decision_log": "DL-20260424-019",
        "repro_mode": "manual_oneoff",
        "repro_command": GROUP_OFF_REPRO_COMMAND,
    },
    {
        "evidence_family": "evidence_axis_opportunity_map",
        "judgment_role": "candidate_reservoir",
        "root_key": "opportunity_root",
        "relative_path": "evidence_axis_opportunity_summary_v1.csv",
        "artifact_kind": "summary_csv",
        "latest_decision_log": "DL-20260424-021",
        "repro_mode": "manual_oneoff",
        "repro_command": OPPORTUNITY_REPRO_COMMAND,
    },
    {
        "evidence_family": "report_entry_friction_axis",
        "judgment_role": "structural_blocker",
        "root_key": "report_entry_root",
        "relative_path": "panel_day_engine_report_entry_friction_axis_v1.csv",
        "artifact_kind": "detail_csv",
        "latest_decision_log": "DL-20260424-022",
        "repro_mode": "builder",
        "repro_command": REPORT_ENTRY_REPRO_COMMAND,
    },
    {
        "evidence_family": "report_entry_friction_axis",
        "judgment_role": "structural_blocker",
        "root_key": "report_entry_root",
        "relative_path": "panel_day_engine_report_entry_friction_axis_summary_v1.csv",
        "artifact_kind": "summary_csv",
        "latest_decision_log": "DL-20260424-022",
        "repro_mode": "builder",
        "repro_command": REPORT_ENTRY_REPRO_COMMAND,
    },
    {
        "evidence_family": "recovery_recurrence_axis",
        "judgment_role": "supportive_hint",
        "root_key": "recovery_root",
        "relative_path": "panel_day_engine_recovery_recurrence_axis_v1.csv",
        "artifact_kind": "detail_csv",
        "latest_decision_log": "DL-20260424-023",
        "repro_mode": "builder",
        "repro_command": RECOVERY_REPRO_COMMAND,
    },
    {
        "evidence_family": "recovery_recurrence_axis",
        "judgment_role": "supportive_hint",
        "root_key": "recovery_root",
        "relative_path": "panel_day_engine_recovery_recurrence_axis_summary_v1.csv",
        "artifact_kind": "summary_csv",
        "latest_decision_log": "DL-20260424-023",
        "repro_mode": "builder",
        "repro_command": RECOVERY_REPRO_COMMAND,
    },
]

DETAIL_COLS = [
    "evidence_family",
    "judgment_role",
    "artifact_name",
    "artifact_kind",
    "artifact_path",
    "source_root_label",
    "canonical_or_temp",
    "owner_branch",
    "latest_decision_log",
    "repro_mode",
    "repro_command",
    "artifact_exists",
    "pack_path",
    "pack_materialization",
]
SUMMARY_COLS = [
    "evidence_family",
    "judgment_role",
    "canonical_or_temp",
    "repro_mode",
    "artifacts",
    "existing_artifacts",
    "packed_artifacts",
    "artifact_kinds",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a single evidence manifest and consolidated pack root that index current "
            "runtime result artifacts, temp scans, and implemented evidence-sidecar outputs."
        )
    )
    parser.add_argument("--result-root", type=Path, required=True, help="Folder containing base result artifacts.")
    parser.add_argument("--group-off-root", type=Path, required=True, help="Folder containing group_off blocker scan CSVs.")
    parser.add_argument("--opportunity-root", type=Path, required=True, help="Folder containing evidence-axis opportunity scan CSVs.")
    parser.add_argument("--report-entry-root", type=Path, required=True, help="Folder containing report-entry friction sidecar CSVs.")
    parser.add_argument("--recovery-root", type=Path, required=True, help="Folder containing recovery/recurrence sidecar CSVs.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Folder where the manifest and consolidated pack root will be written.")
    parser.add_argument(
        "--owner-branch",
        default="",
        help="Owner branch string to stamp into manifest rows. Defaults to the current git branch.",
    )
    args = parser.parse_args()
    if not args.owner_branch:
        args.owner_branch = detect_owner_branch()
    return args


def detect_owner_branch() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if completed.returncode == 0:
        return completed.stdout.strip() or "unknown"
    return "unknown"


def classify_location(path: Path) -> str:
    text = str(path)
    temp_prefixes = ("/private/tmp/", "/tmp/", "/private/var/folders/")
    return "temp" if text.startswith(temp_prefixes) else "canonical"


def materialize_artifact(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    try:
        dst.symlink_to(src)
        return "symlink"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


def build_manifest(args: argparse.Namespace) -> pd.DataFrame:
    output_dir = args.output_dir.resolve()
    pack_root = output_dir / PACK_ROOT_DIRNAME
    roots = {
        "result_root": args.result_root.resolve(),
        "group_off_root": args.group_off_root.resolve(),
        "opportunity_root": args.opportunity_root.resolve(),
        "report_entry_root": args.report_entry_root.resolve(),
        "recovery_root": args.recovery_root.resolve(),
    }
    rows: list[dict[str, object]] = []
    for spec in ARTIFACT_SPECS:
        source_root = roots[spec["root_key"]]
        artifact_path = source_root / spec["relative_path"]
        exists = artifact_path.exists()
        pack_path = ""
        pack_materialization = ""
        if exists:
            target_path = pack_root / spec["evidence_family"] / Path(spec["relative_path"]).name
            pack_materialization = materialize_artifact(artifact_path, target_path)
            pack_path = str(target_path)
        rows.append(
            {
                "evidence_family": spec["evidence_family"],
                "judgment_role": spec["judgment_role"],
                "artifact_name": Path(spec["relative_path"]).name,
                "artifact_kind": spec["artifact_kind"],
                "artifact_path": str(artifact_path),
                "source_root_label": spec["root_key"],
                "canonical_or_temp": classify_location(artifact_path),
                "owner_branch": args.owner_branch,
                "latest_decision_log": spec["latest_decision_log"],
                "repro_mode": spec["repro_mode"],
                "repro_command": spec["repro_command"],
                "artifact_exists": int(exists),
                "pack_path": pack_path,
                "pack_materialization": pack_materialization,
            }
        )
    return pd.DataFrame(rows, columns=DETAIL_COLS)


def build_summary(detail_df: pd.DataFrame) -> pd.DataFrame:
    if detail_df.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)

    def join_unique(values: pd.Series) -> str:
        uniques = sorted({str(value) for value in values if str(value).strip()})
        return "|".join(uniques)

    summary = (
        detail_df.groupby(
            ["evidence_family", "judgment_role", "canonical_or_temp", "repro_mode"],
            dropna=False,
            as_index=False,
        )
        .agg(
            artifacts=("artifact_name", "count"),
            existing_artifacts=("artifact_exists", "sum"),
            packed_artifacts=("pack_materialization", lambda s: int(sum(1 for value in s if str(value).strip()))),
            artifact_kinds=("artifact_kind", join_unique),
        )
    )
    return summary.loc[:, SUMMARY_COLS].sort_values(
        ["judgment_role", "evidence_family", "repro_mode"],
        kind="stable",
    )


def write_json_manifest(args: argparse.Namespace, detail_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    output_dir = args.output_dir.resolve()
    payload = {
        "owner_branch": args.owner_branch,
        "output_dir": str(output_dir),
        "pack_root": str(output_dir / PACK_ROOT_DIRNAME),
        "roots": {
            "result_root": str(args.result_root.resolve()),
            "group_off_root": str(args.group_off_root.resolve()),
            "opportunity_root": str(args.opportunity_root.resolve()),
            "report_entry_root": str(args.report_entry_root.resolve()),
            "recovery_root": str(args.recovery_root.resolve()),
        },
        "artifact_count": int(len(detail_df)),
        "existing_artifact_count": int(detail_df["artifact_exists"].sum()) if not detail_df.empty else 0,
        "packed_artifact_count": int(summary_df["packed_artifacts"].sum()) if not summary_df.empty else 0,
        "families": sorted(detail_df["evidence_family"].unique().tolist()) if not detail_df.empty else [],
        "required_fields": DETAIL_COLS,
    }
    (output_dir / JSON_OUTPUT_NAME).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    detail_df = build_manifest(args)
    summary_df = build_summary(detail_df)
    detail_df.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_json_manifest(args, detail_df, summary_df)


if __name__ == "__main__":
    main()
