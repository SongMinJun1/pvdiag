#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import pandas as pd


KEY_CSVS = [
    "result/fault6_fixed_result_table_v1.csv",
    "result/fault6_label_and_algorithm_preview_v1.csv",
    "result/fault_panel_result_precursor_report_v1.csv",
    "result/fault_panel_result_raw_only_current_v1.csv",
    "result/fault_panel_result_raw_only_current_preview_v1.csv",
    "result/fault_panel_result_raw_only_fault_signal_report_v1.csv",
]

KEY_FILES = [
    "result/fault_panel_result_master_report_v1.md",
    "result/fault_panel_result_detailed_report_v1.xlsx",
]

DETAIL_COLUMNS = [
    "artifact",
    "check_type",
    "modular_exists",
    "single_exists",
    "modular_rows",
    "single_rows",
    "modular_columns",
    "single_columns",
    "status",
    "note",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare modular pvdiag results with pvdiag_single.py results.")
    parser.add_argument("--modular-output-root", type=Path, required=True)
    parser.add_argument("--single-output-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--json-output", type=Path, default=None)
    return parser.parse_args()


def normalize_columns(df: pd.DataFrame) -> list[str]:
    return [str(col) for col in df.columns.tolist()]


def compare_csv(modular_root: Path, single_root: Path, rel: str) -> dict[str, object]:
    modular_path = modular_root / rel
    single_path = single_root / rel
    row: dict[str, object] = {
        "artifact": rel,
        "check_type": "csv_schema_row_count",
        "modular_exists": int(modular_path.exists()),
        "single_exists": int(single_path.exists()),
        "modular_rows": "",
        "single_rows": "",
        "modular_columns": "",
        "single_columns": "",
        "status": "pass",
        "note": "",
    }
    if not modular_path.exists() or not single_path.exists():
        row["status"] = "fail"
        row["note"] = "missing csv artifact"
        return row
    modular_df = pd.read_csv(modular_path, encoding="utf-8-sig", low_memory=False)
    single_df = pd.read_csv(single_path, encoding="utf-8-sig", low_memory=False)
    modular_cols = normalize_columns(modular_df)
    single_cols = normalize_columns(single_df)
    row["modular_rows"] = len(modular_df)
    row["single_rows"] = len(single_df)
    row["modular_columns"] = "|".join(modular_cols)
    row["single_columns"] = "|".join(single_cols)
    notes = []
    if len(modular_df) != len(single_df):
        notes.append("row count differs")
    if modular_cols != single_cols:
        notes.append("schema differs")
    if notes:
        row["status"] = "fail"
        row["note"] = "; ".join(notes)
    return row


def compare_file(modular_root: Path, single_root: Path, rel: str) -> dict[str, object]:
    modular_path = modular_root / rel
    single_path = single_root / rel
    status = "pass" if modular_path.exists() and single_path.exists() else "fail"
    return {
        "artifact": rel,
        "check_type": "file_exists",
        "modular_exists": int(modular_path.exists()),
        "single_exists": int(single_path.exists()),
        "modular_rows": "",
        "single_rows": "",
        "modular_columns": "",
        "single_columns": "",
        "status": status,
        "note": "" if status == "pass" else "missing required file",
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DETAIL_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in DETAIL_COLUMNS})


def main() -> None:
    args = parse_args()
    modular_root = args.modular_output_root.resolve()
    single_root = args.single_output_root.resolve()
    rows = [compare_csv(modular_root, single_root, rel) for rel in KEY_CSVS]
    rows.extend(compare_file(modular_root, single_root, rel) for rel in KEY_FILES)
    fail_rows = [row for row in rows if row["status"] != "pass"]
    payload = {
        "modular_output_root": str(modular_root),
        "single_output_root": str(single_root),
        "checked_artifacts": len(rows),
        "passed_artifacts": len(rows) - len(fail_rows),
        "failed_artifacts": len(fail_rows),
        "overall_status": "pass" if not fail_rows else "fail",
    }
    if args.output:
        write_csv(args.output.resolve(), rows)
    if args.json_output:
        args.json_output.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.json_output.resolve().write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if fail_rows:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
