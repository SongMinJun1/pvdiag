#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RUN_CONSOLIDATION_SCRIPT = "research/prognostics/build_panel_day_engine_operator_run_consolidation_v1.py"
ATTENTION_DELTA_SCRIPT = "research/prognostics/build_panel_day_engine_operator_attention_delta_v1.py"
BUILDER_SEQUENCE = [RUN_CONSOLIDATION_SCRIPT, ATTENTION_DELTA_SCRIPT]

RUN_SUMMARY_NAME = "panel_day_engine_operator_run_summary_v1.csv"
ATTENTION_NOW_NAME = "panel_day_engine_operator_attention_now_v1.csv"
ATTENTION_DELTA_NAME = "panel_day_engine_operator_attention_delta_v1.csv"
ATTENTION_DELTA_SUMMARY_NAME = "panel_day_engine_operator_attention_delta_summary_v1.csv"
BASELINE_MANIFEST_NAME = "panel_day_engine_operator_baseline_manifest_v1.csv"
BASELINE_SUMMARY_NAME = "panel_day_engine_operator_baseline_summary_v1.csv"

RUN_SUMMARY_REQUIRED_COLS = [
    "record_type",
    "site",
    "queue_count",
    "backlog_count",
    "watchlist_count",
    "watch_now_count",
    "watch_review_count",
]
DELTA_SUMMARY_REQUIRED_COLS = [
    "record_type",
    "site",
    "current_attention_count",
    "new_attention_count",
    "dropped_attention_count",
    "total_changed_count",
]

MANIFEST_OUTPUT_COLS = [
    "generated_at_utc",
    "attention_count",
    "queue_count",
    "backlog_count",
    "watchlist_count",
    "watch_now_count",
    "watch_review_count",
    "attention_delta_count",
    "new_attention_count",
    "dropped_attention_count",
    "total_changed_count",
]

SUMMARY_OUTPUT_COLS = [
    "record_type",
    "site",
    "attention_count",
    "queue_count",
    "backlog_count",
    "watchlist_count",
    "watch_now_count",
    "watch_review_count",
    "new_attention_count",
    "dropped_attention_count",
    "total_changed_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the stable operator baseline build sequence for run consolidation + attention delta."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the project root.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing required output: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def run_builder(repo_root: Path, root: Path, script_relative_path: str) -> None:
    script_path = repo_root / script_relative_path
    result = subprocess.run(
        [sys.executable, str(script_path), "--root", str(root)],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or f"{script_relative_path} failed"
        raise SystemExit(details)


def build_manifest_and_summary(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    share_dir = root / "_share"
    run_summary = read_csv(share_dir / RUN_SUMMARY_NAME)
    delta_summary = read_csv(share_dir / ATTENTION_DELTA_SUMMARY_NAME)
    attention_now = read_csv(share_dir / ATTENTION_NOW_NAME)
    attention_delta = read_csv(share_dir / ATTENTION_DELTA_NAME)

    ensure_columns(run_summary, RUN_SUMMARY_REQUIRED_COLS, RUN_SUMMARY_NAME)
    ensure_columns(delta_summary, DELTA_SUMMARY_REQUIRED_COLS, ATTENTION_DELTA_SUMMARY_NAME)
    ensure_columns(attention_now, ["site", "panel_id"], ATTENTION_NOW_NAME)
    ensure_columns(attention_delta, ["site", "panel_id", "delta_class"], ATTENTION_DELTA_NAME)

    for df in (run_summary, delta_summary):
        df["record_type"] = df["record_type"].map(normalize_text)
        df["site"] = df["site"].map(normalize_text)

    merged = run_summary.loc[:, RUN_SUMMARY_REQUIRED_COLS].merge(
        delta_summary.loc[:, DELTA_SUMMARY_REQUIRED_COLS],
        on=["record_type", "site"],
        how="outer",
        validate="one_to_one",
    )

    for col in [
        "queue_count",
        "backlog_count",
        "watchlist_count",
        "watch_now_count",
        "watch_review_count",
        "current_attention_count",
        "new_attention_count",
        "dropped_attention_count",
        "total_changed_count",
    ]:
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0).astype(int)

    summary = pd.DataFrame(
        {
            "record_type": merged["record_type"],
            "site": merged["site"],
            "attention_count": merged["current_attention_count"],
            "queue_count": merged["queue_count"],
            "backlog_count": merged["backlog_count"],
            "watchlist_count": merged["watchlist_count"],
            "watch_now_count": merged["watch_now_count"],
            "watch_review_count": merged["watch_review_count"],
            "new_attention_count": merged["new_attention_count"],
            "dropped_attention_count": merged["dropped_attention_count"],
            "total_changed_count": merged["total_changed_count"],
        },
        columns=SUMMARY_OUTPUT_COLS,
    )

    summary["_record_order"] = summary["record_type"].map({"overall": 0, "site": 1}).fillna(99)
    summary = summary.sort_values(["_record_order", "site"], ascending=[True, True], kind="mergesort").drop(
        columns=["_record_order"]
    )

    overall_summary = summary.loc[summary["record_type"].eq("overall")]
    if overall_summary.empty:
        raise SystemExit("baseline summary missing overall row")
    overall_row = overall_summary.iloc[0]
    manifest = pd.DataFrame(
        [
            {
                "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "attention_count": int(overall_row["attention_count"]),
                "queue_count": int(overall_row["queue_count"]),
                "backlog_count": int(overall_row["backlog_count"]),
                "watchlist_count": int(overall_row["watchlist_count"]),
                "watch_now_count": int(overall_row["watch_now_count"]),
                "watch_review_count": int(overall_row["watch_review_count"]),
                "attention_delta_count": int(len(attention_delta)),
                "new_attention_count": int(overall_row["new_attention_count"]),
                "dropped_attention_count": int(overall_row["dropped_attention_count"]),
                "total_changed_count": int(overall_row["total_changed_count"]),
            }
        ],
        columns=MANIFEST_OUTPUT_COLS,
    )
    return manifest, summary.reset_index(drop=True)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    repo_root = Path(__file__).resolve().parents[2]
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    for script_relative_path in BUILDER_SEQUENCE:
        run_builder(repo_root, root, script_relative_path)

    manifest, summary = build_manifest_and_summary(root)
    manifest.to_csv(share_dir / BASELINE_MANIFEST_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / BASELINE_SUMMARY_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
