#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_PACKET_INPUT = Path(
    "/private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv"
)
DEFAULT_COMMON_CAUSE_STRONG_BLOCKER_INPUT = Path(
    "/private/tmp/strong_common_cause_blocker_regression_packet_check/"
    "panel_day_engine_strong_common_cause_blocker_regression_packet_v1.csv"
)
DEFAULT_COMMON_CAUSE_EXACT_SEARCH_INPUT = Path(
    "/private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv"
)
DEFAULT_COMMON_CAUSE_STRUCTURAL_INPUT = Path(
    "/private/tmp/common_cause_structural_blocker_review_check/"
    "panel_day_engine_common_cause_structural_blocker_review_v1.csv"
)
DEFAULT_COMMON_CAUSE_TRACE_INPUT = Path(
    "/private/tmp/common_cause_manual_trace_review_check/panel_day_engine_common_cause_manual_trace_review_v1.csv"
)
PANEL_ENGINE_GATE_DETAIL = "panel_day_engine_patch_safety_gate_v1.csv"
PANEL_ENGINE_GATE_SUMMARY = "panel_day_engine_patch_safety_gate_summary_v1.csv"
FAULT_FAMILY_GATE_DETAIL = "panel_day_engine_fault_family_regression_prepatch_gate_v1.csv"
FAULT_FAMILY_GATE_SUMMARY = "panel_day_engine_fault_family_regression_prepatch_gate_summary_v1.csv"
COMMON_CAUSE_GATE_DETAIL = "panel_day_engine_common_cause_semantic_prepatch_gate_v1.csv"
COMMON_CAUSE_GATE_SUMMARY = "panel_day_engine_common_cause_semantic_prepatch_gate_summary_v1.csv"
DETAIL_OUTPUT_NAME = "panel_day_engine_algorithm_prepatch_runbook_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_algorithm_prepatch_runbook_summary_v1.csv"
DETAIL_COLS = [
    "runbook_step",
    "gate_name",
    "overall_status",
    "pass_flag",
    "failed_required_gate_count",
    "output_dir",
    "summary_path",
    "detail_path",
    "command",
]
SUMMARY_COLS = [
    "overall_status",
    "gate_count",
    "passed_gate_count",
    "failed_gate_count",
    "panel_engine_gate_status",
    "fault_family_gate_status",
    "common_cause_gate_status",
    "engine_change_detected",
    "fault_family_packet_rows",
    "fault_family_target_exact_closure_candidate_sum",
    "fault_family_operator_promotion_allowed_sum",
    "fault_family_engine_patch_candidate_sum",
    "common_cause_required_gate_count",
    "common_cause_failed_required_gate_count",
    "common_cause_warn_gate_count",
    "common_cause_exact_family_closure_sum",
    "common_cause_raw_direct_row_sum",
    "common_cause_official_current_bridge_candidate_sum",
    "common_cause_semantic_patch_candidate_sum",
    "common_cause_operator_promotion_allowed_sum",
    "common_cause_engine_patch_candidate_sum",
    "common_cause_threshold_patch_allowed_sum",
    "next_required_action",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the panel-engine algorithm prepatch runbook: panel-engine safety gate plus "
            "BR-059 fault-family regression prepatch gate plus BR-075 common-cause semantic "
            "prepatch gate."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--input-manifest", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--packet-input", type=Path, default=DEFAULT_PACKET_INPUT)
    parser.add_argument(
        "--common-cause-strong-blocker-input",
        type=Path,
        default=DEFAULT_COMMON_CAUSE_STRONG_BLOCKER_INPUT,
    )
    parser.add_argument(
        "--common-cause-exact-search-input",
        type=Path,
        default=DEFAULT_COMMON_CAUSE_EXACT_SEARCH_INPUT,
    )
    parser.add_argument(
        "--common-cause-structural-input",
        type=Path,
        default=DEFAULT_COMMON_CAUSE_STRUCTURAL_INPUT,
    )
    parser.add_argument(
        "--common-cause-trace-input",
        type=Path,
        default=DEFAULT_COMMON_CAUSE_TRACE_INPUT,
    )
    parser.add_argument("--base-ref", default="HEAD")
    parser.add_argument("--changed-paths-file", type=Path, default=None)
    parser.add_argument(
        "--allow-fail",
        action="store_true",
        help="Write runbook outputs but return success even when a sub-gate fails.",
    )
    return parser.parse_args()


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


def resolve_manifest_input(
    repo_root: Path,
    key: str,
    flag: str,
    arg_value: str | Path,
    manifest: dict[str, Any],
    explicit_flags: set[str],
) -> tuple[Path, str]:
    if flag in explicit_flags:
        return resolve_path(repo_root, arg_value), "explicit_cli"
    if manifest:
        manifest_value = manifest_path_value(manifest, key)
        if not manifest_value:
            raise KeyError(
                f"prepatch runbook input manifest is missing `{key}`; "
                f"pass {flag} explicitly or add inputs.{key}"
            )
        return resolve_path(repo_root, manifest_value), "input_manifest"
    return resolve_path(repo_root, arg_value), "legacy_default"


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def to_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing gate output: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def command_text(command: list[str]) -> str:
    return " ".join(command)


def run_panel_engine_gate(args: argparse.Namespace, gate_dir: Path) -> dict[str, object]:
    script = args.repo_root / "research" / "prognostics" / "check_panel_day_engine_patch_safety_gate_v1.py"
    command = [
        sys.executable,
        str(script),
        "--repo-root",
        str(args.repo_root),
        "--base-ref",
        args.base_ref,
        "--output-dir",
        str(gate_dir),
    ]
    if args.changed_paths_file is not None:
        command.extend(["--changed-paths-file", str(args.changed_paths_file)])
    completed = run_command(command, args.repo_root)
    if completed.returncode != 0:
        raise SystemExit(completed.stderr or completed.stdout)
    summary_path = gate_dir / PANEL_ENGINE_GATE_SUMMARY
    detail_path = gate_dir / PANEL_ENGINE_GATE_DETAIL
    summary = read_csv(summary_path).iloc[0]
    status = normalize_text(summary.get("overall_status"))
    return {
        "runbook_step": "1",
        "gate_name": "panel_engine_patch_safety_gate",
        "overall_status": status,
        "pass_flag": int(status == "pass"),
        "failed_required_gate_count": to_int(summary.get("fail_gate_count")),
        "output_dir": str(gate_dir),
        "summary_path": str(summary_path),
        "detail_path": str(detail_path),
        "command": command_text(command),
        "engine_change_detected": to_int(summary.get("engine_change_detected")),
    }


def run_fault_family_gate(args: argparse.Namespace, gate_dir: Path) -> dict[str, object]:
    script = (
        args.repo_root
        / "research"
        / "prognostics"
        / "check_panel_day_engine_fault_family_regression_prepatch_gate_v1.py"
    )
    command = [
        sys.executable,
        str(script),
        "--packet-input",
        str(args.packet_input),
        "--output-dir",
        str(gate_dir),
        "--allow-fail",
    ]
    completed = run_command(command, args.repo_root)
    if completed.returncode != 0:
        raise SystemExit(completed.stderr or completed.stdout)
    summary_path = gate_dir / FAULT_FAMILY_GATE_SUMMARY
    detail_path = gate_dir / FAULT_FAMILY_GATE_DETAIL
    summary = read_csv(summary_path).iloc[0]
    status = normalize_text(summary.get("overall_status"))
    return {
        "runbook_step": "2",
        "gate_name": "fault_family_regression_prepatch_gate",
        "overall_status": status,
        "pass_flag": int(status == "pass"),
        "failed_required_gate_count": to_int(summary.get("failed_required_gate_count")),
        "output_dir": str(gate_dir),
        "summary_path": str(summary_path),
        "detail_path": str(detail_path),
        "command": command_text(command),
        "packet_rows": to_int(summary.get("packet_rows")),
        "target_exact_closure_candidate_sum": to_int(summary.get("target_exact_closure_candidate_sum")),
        "operator_promotion_allowed_sum": to_int(summary.get("operator_promotion_allowed_sum")),
        "engine_patch_candidate_sum": to_int(summary.get("engine_patch_candidate_sum")),
    }


def run_common_cause_gate(args: argparse.Namespace, gate_dir: Path) -> dict[str, object]:
    script = (
        args.repo_root
        / "research"
        / "prognostics"
        / "check_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py"
    )
    command = [
        sys.executable,
        str(script),
        "--strong-blocker-input",
        str(args.common_cause_strong_blocker_input),
        "--exact-search-input",
        str(args.common_cause_exact_search_input),
        "--structural-input",
        str(args.common_cause_structural_input),
        "--trace-input",
        str(args.common_cause_trace_input),
        "--output-dir",
        str(gate_dir),
        "--allow-fail",
    ]
    completed = run_command(command, args.repo_root)
    if completed.returncode != 0:
        raise SystemExit(completed.stderr or completed.stdout)
    summary_path = gate_dir / COMMON_CAUSE_GATE_SUMMARY
    detail_path = gate_dir / COMMON_CAUSE_GATE_DETAIL
    summary = read_csv(summary_path).iloc[0]
    status = normalize_text(summary.get("overall_status"))
    return {
        "runbook_step": "3",
        "gate_name": "common_cause_semantic_prepatch_gate",
        "overall_status": status,
        "pass_flag": int(status == "pass"),
        "failed_required_gate_count": to_int(summary.get("failed_required_gate_count")),
        "output_dir": str(gate_dir),
        "summary_path": str(summary_path),
        "detail_path": str(detail_path),
        "command": command_text(command),
        "required_gate_count": to_int(summary.get("required_gate_count")),
        "warn_gate_count": to_int(summary.get("warn_gate_count")),
        "exact_family_closure_sum": to_int(summary.get("exact_family_closure_sum")),
        "raw_direct_common_cause_row_sum": to_int(summary.get("raw_direct_common_cause_row_sum")),
        "official_current_bridge_candidate_sum": to_int(
            summary.get("official_current_bridge_candidate_sum")
        ),
        "semantic_patch_candidate_sum": to_int(summary.get("semantic_patch_candidate_sum")),
        "operator_promotion_allowed_sum": to_int(summary.get("operator_promotion_allowed_sum")),
        "engine_patch_candidate_sum": to_int(summary.get("engine_patch_candidate_sum")),
        "threshold_patch_allowed_sum": to_int(summary.get("threshold_patch_allowed_sum")),
    }


def build_summary(
    detail: pd.DataFrame,
    panel_row: dict[str, object],
    fault_row: dict[str, object],
    common_row: dict[str, object],
) -> pd.DataFrame:
    failed_count = int((detail["overall_status"] != "pass").sum())
    overall_status = "pass" if failed_count == 0 else "fail"
    next_action = (
        "prepatch_gates_passed_review_evidence_before_code"
        if overall_status == "pass"
        else "stop_algorithm_patch_until_failed_gate_is_resolved"
    )
    row = {
        "overall_status": overall_status,
        "gate_count": len(detail),
        "passed_gate_count": int(detail["pass_flag"].sum()),
        "failed_gate_count": failed_count,
        "panel_engine_gate_status": panel_row["overall_status"],
        "fault_family_gate_status": fault_row["overall_status"],
        "common_cause_gate_status": common_row["overall_status"],
        "engine_change_detected": panel_row.get("engine_change_detected", 0),
        "fault_family_packet_rows": fault_row.get("packet_rows", 0),
        "fault_family_target_exact_closure_candidate_sum": fault_row.get("target_exact_closure_candidate_sum", 0),
        "fault_family_operator_promotion_allowed_sum": fault_row.get("operator_promotion_allowed_sum", 0),
        "fault_family_engine_patch_candidate_sum": fault_row.get("engine_patch_candidate_sum", 0),
        "common_cause_required_gate_count": common_row.get("required_gate_count", 0),
        "common_cause_failed_required_gate_count": common_row.get("failed_required_gate_count", 0),
        "common_cause_warn_gate_count": common_row.get("warn_gate_count", 0),
        "common_cause_exact_family_closure_sum": common_row.get("exact_family_closure_sum", 0),
        "common_cause_raw_direct_row_sum": common_row.get("raw_direct_common_cause_row_sum", 0),
        "common_cause_official_current_bridge_candidate_sum": common_row.get(
            "official_current_bridge_candidate_sum", 0
        ),
        "common_cause_semantic_patch_candidate_sum": common_row.get("semantic_patch_candidate_sum", 0),
        "common_cause_operator_promotion_allowed_sum": common_row.get(
            "operator_promotion_allowed_sum", 0
        ),
        "common_cause_engine_patch_candidate_sum": common_row.get("engine_patch_candidate_sum", 0),
        "common_cause_threshold_patch_allowed_sum": common_row.get("threshold_patch_allowed_sum", 0),
        "next_required_action": next_action,
    }
    return pd.DataFrame([row], columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    _, input_manifest = load_input_manifest(repo_root, args.input_manifest)
    argv = sys.argv[1:]
    explicit_flags = {
        flag
        for flag in [
            "--packet-input",
            "--common-cause-strong-blocker-input",
            "--common-cause-exact-search-input",
            "--common-cause-structural-input",
            "--common-cause-trace-input",
        ]
        if cli_flag_provided(flag, argv)
    }
    args.packet_input, _ = resolve_manifest_input(
        repo_root,
        "packet_input",
        "--packet-input",
        args.packet_input,
        input_manifest,
        explicit_flags,
    )
    args.common_cause_strong_blocker_input, _ = resolve_manifest_input(
        repo_root,
        "common_cause_strong_blocker_input",
        "--common-cause-strong-blocker-input",
        args.common_cause_strong_blocker_input,
        input_manifest,
        explicit_flags,
    )
    args.common_cause_exact_search_input, _ = resolve_manifest_input(
        repo_root,
        "common_cause_exact_search_input",
        "--common-cause-exact-search-input",
        args.common_cause_exact_search_input,
        input_manifest,
        explicit_flags,
    )
    args.common_cause_structural_input, _ = resolve_manifest_input(
        repo_root,
        "common_cause_structural_input",
        "--common-cause-structural-input",
        args.common_cause_structural_input,
        input_manifest,
        explicit_flags,
    )
    args.common_cause_trace_input, _ = resolve_manifest_input(
        repo_root,
        "common_cause_trace_input",
        "--common-cause-trace-input",
        args.common_cause_trace_input,
        input_manifest,
        explicit_flags,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    panel_dir = args.output_dir / "panel_engine_patch_safety_gate"
    fault_dir = args.output_dir / "fault_family_regression_prepatch_gate"
    common_dir = args.output_dir / "common_cause_semantic_prepatch_gate"
    panel_dir.mkdir(parents=True, exist_ok=True)
    fault_dir.mkdir(parents=True, exist_ok=True)
    common_dir.mkdir(parents=True, exist_ok=True)

    panel_row = run_panel_engine_gate(args, panel_dir)
    fault_row = run_fault_family_gate(args, fault_dir)
    common_row = run_common_cause_gate(args, common_dir)
    detail = pd.DataFrame(
        [
            {col: panel_row.get(col, "") for col in DETAIL_COLS},
            {col: fault_row.get(col, "") for col in DETAIL_COLS},
            {col: common_row.get(col, "") for col in DETAIL_COLS},
        ],
        columns=DETAIL_COLS,
    )
    summary = build_summary(detail, panel_row, fault_row, common_row)
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    if summary.iloc[0]["overall_status"] != "pass" and not args.allow_fail:
        raise SystemExit("panel-day-engine algorithm prepatch runbook failed")


if __name__ == "__main__":
    main()
