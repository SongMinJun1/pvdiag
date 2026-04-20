#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPARE_SCRIPT = REPO_ROOT / "research" / "prognostics" / "run_runtime_rawonly_chain_compare_v1.py"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_root = Path(tmp_dir) / "rawonly_compare"
        subprocess.run(
            [
                sys.executable,
                str(COMPARE_SCRIPT),
                "--output-root",
                str(output_root),
                "--reuse-existing-site-outs-root",
                str(REPO_ROOT / "data"),
            ],
            cwd=REPO_ROOT,
            check=True,
        )

        summary_path = output_root / "runtime_rawonly_chain_compare_v1.json"
        fault_path = output_root / "result" / "fault_panel_result_raw_only_v1.csv"
        preview_path = output_root / "result" / "fault_panel_result_raw_only_preview_v1.csv"
        for path in [summary_path, fault_path, preview_path]:
            if not path.exists():
                raise SystemExit(f"missing raw-only chain output: {path}")

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        compare = summary.get("reference_compare", {})
        if compare.get("reference_available") is not True:
            raise SystemExit("raw-only chain compare must detect the packaged fixed reference")
        if compare.get("candidate_row_count", 0) < compare.get("reference_row_count", 0):
            raise SystemExit("raw-only chain should not produce fewer fault rows than the fixed reference on baseline reuse run")
        if compare.get("matched_row_key_count", 0) <= 0:
            raise SystemExit("raw-only chain compare must overlap at least one fixed reference key on baseline reuse run")
        if compare.get("overlap_decision_columns_match") is not True:
            raise SystemExit("raw-only chain must preserve status/event/terminal on the overlapping fixed reference keys")

        fault_df = pd.read_csv(fault_path, encoding="utf-8-sig", low_memory=False)
        preview_df = pd.read_csv(preview_path, encoding="utf-8-sig", low_memory=False)
        expected_fault_cols = [
            "site",
            "panel_id",
            "패널고장여부_ko",
            "사건유형_ko",
            "최종고장양상_ko",
            "커널로그_원인군_ko",
            "1순위_의심원인_ko",
            "2순위_의심원인_ko",
            "3순위_의심원인_ko",
        ]
        expected_preview_cols = expected_fault_cols + ["커널로그 기존 알고리즘"]
        if fault_df.columns.tolist() != expected_fault_cols:
            raise SystemExit(f"unexpected raw-only fault table columns: {fault_df.columns.tolist()}")
        if preview_df.columns.tolist() != expected_preview_cols:
            raise SystemExit(f"unexpected raw-only preview columns: {preview_df.columns.tolist()}")
        if len(fault_df) <= 0:
            raise SystemExit("raw-only fault table must not be empty")

    print("[OK] runtime raw-only chain smoke passed")


if __name__ == "__main__":
    main()
