#!/usr/bin/env python3
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_VERDICT_SCRIPT = REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_bootstrap_verdict_v1.py"
RUN_SCRIPT = REPO_ROOT / "research" / "prognostics" / "run_runtime_bootstrap_chain_shadow_compare_v1.py"


def main() -> None:
    py_compile.compile(str(REPO_ROOT / "pv_ae" / "panel_day_engine.py"), doraise=True)
    py_compile.compile(str(BOOTSTRAP_VERDICT_SCRIPT), doraise=True)
    py_compile.compile(str(RUN_SCRIPT), doraise=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_root = Path(tmp_dir) / "bootstrap_compare"
        subprocess.run(
            [
                sys.executable,
                str(RUN_SCRIPT),
                "--output-root",
                str(output_root),
                "--reuse-existing-site-outs",
            ],
            cwd=REPO_ROOT,
            check=True,
        )
        report_path = output_root / "runtime_bootstrap_chain_shadow_compare_v1.json"
        if not report_path.exists():
            raise SystemExit("bootstrap compare report was not written")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if "all_targets_match" not in report or "all_decision_targets_match" not in report:
            raise SystemExit("bootstrap compare report missing topline fields")
        if report.get("all_final_chain_targets_match") is not True:
            raise SystemExit("bootstrap chain must preserve final verdict/evidence/heuristic targets exactly on baseline data")
        if report.get("audit_bootstrap_current_field_diff_only") is not True:
            raise SystemExit("bootstrap chain must differ only on expected audit current-table fields")
        if not (output_root / "workspace" / "_share" / "panel_day_engine_bootstrap_verdict_v1.csv").exists():
            raise SystemExit("bootstrap verdict output missing from workspace")
        if not (output_root / "workspace" / "_share" / "panel_day_engine_bootstrap_verdict_summary_v1.csv").exists():
            raise SystemExit("bootstrap verdict summary missing from workspace")
        if "panel_day_engine_panel_multiaxis_verdict_v1.csv" not in report["targets"]:
            raise SystemExit("bootstrap compare report missing verdict target")

    print("[OK] runtime bootstrap chain shadow compare smoke test passed")


if __name__ == "__main__":
    main()
