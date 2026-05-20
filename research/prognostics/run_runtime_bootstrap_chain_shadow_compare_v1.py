#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.prognostics import run_runtime_chain_shadow_compare_v1 as shadow_mod

FINAL_CHAIN_TARGETS = [
    "panel_day_engine_panel_multiaxis_verdict_v1.csv",
    "panel_day_engine_gpvs_evidence_pack_v1.csv",
    "panel_day_engine_cause_candidate_heuristics_v1.csv",
]
EXPECTED_BOOTSTRAP_AUDIT_DIFF_COLUMNS = {
    "현재표_최종고장양상_ko",
    "현재표_보정필요여부_flag",
}
BOOTSTRAP_VERDICT_SCRIPT = REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_bootstrap_verdict_v1.py"
FAULT_EVENT_AUDIT_SCRIPT = REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_fault_panel_event_audit_v1.py"
VERDICT_SCRIPT = REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_panel_multiaxis_verdict_v1.py"
GPVS_EVIDENCE_SCRIPT = REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_gpvs_evidence_pack_v1.py"
HEURISTIC_SCRIPT = REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_cause_candidate_heuristics_v1.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a workspace-only bootstrap verdict -> fault_event_audit -> final verdict -> GPVS evidence -> "
            "heuristic chain and compare it against the current frozen reference outputs."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root. Defaults to the current project root.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="Folder where workspace, optional live-engine refresh, and compare report will be written.",
    )
    parser.add_argument(
        "--sites",
        default=",".join(shadow_mod.BASELINE_SITES),
        help="Sites to refresh with live engine before the bootstrap chain. Defaults to baseline sites.",
    )
    parser.add_argument(
        "--reuse-existing-site-outs",
        action="store_true",
        help="Skip live engine refresh and seed all baseline sites from the repo's current data/<site>/out.",
    )
    parser.add_argument("--epochs", type=int, default=1, help="Epochs to pass to the packaged runtime engine when refreshing sites.")
    parser.add_argument("--device", default="cpu", help="Torch device to pass to the packaged runtime engine.")
    return parser.parse_args()


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def run_bootstrap_chain(root: Path, workspace_root: Path) -> None:
    run(
        [
            sys.executable,
            str(BOOTSTRAP_VERDICT_SCRIPT),
            "--root",
            str(workspace_root),
            "--write-panel-verdict-alias",
        ],
        cwd=root,
    )
    for script in [
        FAULT_EVENT_AUDIT_SCRIPT,
        VERDICT_SCRIPT,
        GPVS_EVIDENCE_SCRIPT,
        HEURISTIC_SCRIPT,
    ]:
        run([sys.executable, str(script), "--root", str(workspace_root)], cwd=root)


def build_report(
    root: Path,
    output_root: Path,
    workspace_root: Path,
    live_output_root: Path | None,
    live_sites: list[str],
    site_seed_mode: dict[str, str],
) -> dict[str, object]:
    report = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": str(root),
        "workspace_root": str(workspace_root),
        "live_output_root": str(live_output_root) if live_output_root is not None else "",
        "live_sites": live_sites,
        "site_seed_mode": site_seed_mode,
        "bootstrap_verdict_path": str(workspace_root / "_share" / "panel_day_engine_bootstrap_verdict_v1.csv"),
        "bootstrap_verdict_summary_path": str(workspace_root / "_share" / "panel_day_engine_bootstrap_verdict_summary_v1.csv"),
        "all_targets_match": True,
        "all_decision_targets_match": True,
        "all_nonexact_deltas_explainable": True,
        "all_final_chain_targets_match": True,
        "audit_bootstrap_current_field_diff_only": True,
        "targets": {},
        "note_ko": (
            "이 report는 frozen verdict seed를 쓰지 않고, runtime용 bootstrap verdict를 먼저 만든 뒤 "
            "fault_event_audit -> final verdict -> gpvs evidence -> heuristic를 workspace에서 다시 계산해 "
            "frozen reference와 비교한 결과다."
        ),
    }

    for name in shadow_mod.COMPARE_TARGETS:
        target_result = shadow_mod.compare_target(root, workspace_root, name)
        target_result["column_analysis"] = shadow_mod.csv_column_diff_summary(
            root / "_share" / name,
            workspace_root / "_share" / name,
            name,
        )
        report["targets"][name] = target_result
        if not target_result["match"]:
            report["all_targets_match"] = False
        if name in FINAL_CHAIN_TARGETS and not target_result["match"]:
            report["all_final_chain_targets_match"] = False
        column_analysis = target_result.get("column_analysis", {})
        if column_analysis:
            if column_analysis.get("decision_diff_columns"):
                report["all_decision_targets_match"] = False
            if column_analysis.get("classification") != "exact_match" and not column_analysis.get("explainable_flag", False):
                report["all_nonexact_deltas_explainable"] = False
        if name == "panel_day_engine_fault_panel_event_audit_v1.csv":
            differing = set((column_analysis or {}).get("differing_columns", {}).keys())
            if differing and differing != EXPECTED_BOOTSTRAP_AUDIT_DIFF_COLUMNS:
                report["audit_bootstrap_current_field_diff_only"] = False

    if report["all_final_chain_targets_match"] and report["audit_bootstrap_current_field_diff_only"]:
        report["topline_ko"] = (
            "final verdict/evidence/heuristic targets match exactly; only bootstrap audit current-table fields differ"
        )
    elif report["all_decision_targets_match"]:
        report["topline_ko"] = "decision columns are preserved"
    else:
        report["topline_ko"] = "decision columns changed"
    report_path = output_root / "runtime_bootstrap_chain_shadow_compare_v1.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    workspace_root = output_root / "workspace"

    live_sites = shadow_mod.normalize_sites(args.sites)
    if workspace_root.exists():
        shutil.rmtree(workspace_root)

    live_output_root: Path | None = None
    if not args.reuse_existing_site_outs:
        live_output_root = shadow_mod.prepare_live_engine_outputs(root, output_root, live_sites, args.epochs, args.device)

    site_seed_mode = shadow_mod.seed_workspace(root, workspace_root, live_output_root, live_sites if live_output_root else [])
    run_bootstrap_chain(root, workspace_root)
    report = build_report(root, output_root, workspace_root, live_output_root, live_sites, site_seed_mode)
    report_path = output_root / "runtime_bootstrap_chain_shadow_compare_v1.json"
    print(f"[OK] bootstrap chain shadow compare report: {report_path}")
    print(f"[OK] all_targets_match={report['all_targets_match']}")
    print(f"[OK] all_decision_targets_match={report['all_decision_targets_match']}")


if __name__ == "__main__":
    main()
