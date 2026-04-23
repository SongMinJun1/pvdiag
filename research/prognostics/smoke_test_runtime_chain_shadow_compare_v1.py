#!/usr/bin/env python3
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "research" / "prognostics" / "run_runtime_chain_shadow_compare_v1.py"
WATCH = REPO_ROOT / "_share" / "panel_day_engine_panel_multiaxis_verdict_v1.csv"

EXPECTED_TARGETS = [
    "panel_day_engine_fault_panel_event_audit_v1.csv",
    "panel_day_engine_fault_panel_event_audit_summary_v1.csv",
    "panel_day_engine_panel_multiaxis_verdict_v1.csv",
    "panel_day_engine_panel_multiaxis_verdict_summary_v1.csv",
    "panel_day_engine_gpvs_evidence_pack_v1.csv",
    "panel_day_engine_gpvs_evidence_summary_v1.csv",
    "panel_day_engine_cause_candidate_heuristics_v1.csv",
    "panel_day_engine_cause_candidate_summary_v1.csv",
]


def main() -> None:
    before = WATCH.read_bytes()
    py_compile.compile(str(REPO_ROOT / "pv_ae" / "panel_day_engine.py"), doraise=True)
    py_compile.compile(str(SCRIPT), doraise=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_root = Path(tmp_dir) / "shadow_compare"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--output-root",
                str(output_root),
                "--reuse-existing-site-outs",
            ],
            cwd=REPO_ROOT,
            check=True,
        )
        report_path = output_root / "runtime_chain_shadow_compare_v1.json"
        if not report_path.exists():
            raise SystemExit("shadow compare report missing")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if report.get("all_targets_match") is not True:
            raise SystemExit("shadow compare must be exact-match after frozen synchronization")
        if report.get("all_decision_targets_match") is not True:
            raise SystemExit("shadow compare must preserve decision columns under reuse-existing-site-outs mode")
        if report.get("all_known_nondecision_deltas_accounted_for") is not True:
            raise SystemExit("known non-decision deltas must be fully accounted for in shadow compare report")
        for name in EXPECTED_TARGETS:
            if name not in report.get("targets", {}):
                raise SystemExit(f"missing compare target: {name}")
            target = report["targets"][name]
            if target.get("candidate", {}).get("exists") is not True:
                raise SystemExit(f"candidate output missing for target: {name}")
            if target.get("reference", {}).get("exists") is not True:
                raise SystemExit(f"reference output missing for target: {name}")
        verdict_analysis = report["targets"]["panel_day_engine_panel_multiaxis_verdict_v1.csv"].get("column_analysis", {})
        if verdict_analysis.get("decision_diff_columns"):
            raise SystemExit("verdict decision columns must not differ in shadow compare")
        if verdict_analysis.get("classification") != "exact_match":
            raise SystemExit("verdict must exact-match after frozen synchronization")
        audit_analysis = report["targets"]["panel_day_engine_fault_panel_event_audit_v1.csv"].get("column_analysis", {})
        if audit_analysis.get("classification") != "exact_match":
            raise SystemExit("fault panel event audit must exact-match after frozen synchronization")

    after = WATCH.read_bytes()
    if before != after:
        raise SystemExit("shadow compare must not modify frozen verdict")

    print("[OK] runtime chain shadow compare smoke test passed")


if __name__ == "__main__":
    main()
