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
DIGEST_SCRIPT = "research/prognostics/build_panel_day_engine_operator_digest_v1.py"
BUILDER_SEQUENCE = [RUN_CONSOLIDATION_SCRIPT, ATTENTION_DELTA_SCRIPT, DIGEST_SCRIPT]

RUN_SUMMARY_NAME = "panel_day_engine_operator_run_summary_v1.csv"
ATTENTION_NOW_NAME = "panel_day_engine_operator_attention_now_v1.csv"
ATTENTION_DELTA_NAME = "panel_day_engine_operator_attention_delta_v1.csv"
ATTENTION_DELTA_SUMMARY_NAME = "panel_day_engine_operator_attention_delta_summary_v1.csv"
DIGEST_SUMMARY_NAME = "panel_day_engine_operator_digest_summary_v1.csv"
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
DIGEST_SUMMARY_REQUIRED_COLS = [
    "record_type",
    "site",
    "attention_count",
    "changed_attention_count",
    "queue_run_count",
    "watch_now_panel_count",
    "new_attention_count",
    "dropped_attention_count",
    "attention_class_changed_count",
    "status_or_tier_changed_count",
    "priority_changed_count",
    "score_shifted_count",
    "metadata_changed_count",
    "generated_at_utc",
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
    "digest_attention_count",
    "digest_changed_attention_count",
    "digest_queue_run_count",
    "digest_watch_now_panel_count",
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
    "digest_changed_attention_count",
    "digest_queue_run_count",
    "digest_watch_now_panel_count",
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


def build_manifest_and_summary(
    root: Path,
    generated_at_utc: str,
    *,
    digest_summary: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
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

    if digest_summary is not None:
        ensure_columns(digest_summary, DIGEST_SUMMARY_REQUIRED_COLS, DIGEST_SUMMARY_NAME)
        digest_summary = digest_summary.copy()
        digest_summary["record_type"] = digest_summary["record_type"].map(normalize_text)
        digest_summary["site"] = digest_summary["site"].map(normalize_text)
        merged = merged.merge(
            digest_summary.loc[
                :,
                [
                    "record_type",
                    "site",
                    "attention_count",
                    "changed_attention_count",
                    "queue_run_count",
                    "watch_now_panel_count",
                ],
            ].rename(columns={"attention_count": "digest_attention_count"}),
            on=["record_type", "site"],
            how="left",
            validate="one_to_one",
        )
    else:
        merged["digest_attention_count"] = pd.NA
        merged["changed_attention_count"] = 0
        merged["queue_run_count"] = 0
        merged["watch_now_panel_count"] = 0

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
        "digest_attention_count",
        "changed_attention_count",
        "queue_run_count",
        "watch_now_panel_count",
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
            "digest_changed_attention_count": merged["changed_attention_count"],
            "digest_queue_run_count": merged["queue_run_count"],
            "digest_watch_now_panel_count": merged["watch_now_panel_count"],
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
                "generated_at_utc": generated_at_utc,
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
                "digest_attention_count": int(overall_row["attention_count"]),
                "digest_changed_attention_count": int(overall_row["digest_changed_attention_count"]),
                "digest_queue_run_count": int(overall_row["digest_queue_run_count"]),
                "digest_watch_now_panel_count": int(overall_row["digest_watch_now_panel_count"]),
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
    generated_at_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    for script_relative_path in BUILDER_SEQUENCE[:2]:
        run_builder(repo_root, root, script_relative_path)

    # Digest builder reads baseline manifest/summary, so write a provisional
    # baseline after run consolidation + attention delta and then overwrite it
    # with the final digest-aware baseline after digest generation.
    manifest, summary = build_manifest_and_summary(root, generated_at_utc)
    manifest.to_csv(share_dir / BASELINE_MANIFEST_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / BASELINE_SUMMARY_NAME, index=False, encoding="utf-8-sig")

    run_builder(repo_root, root, DIGEST_SCRIPT)

    digest_summary = read_csv(share_dir / DIGEST_SUMMARY_NAME)
    manifest, summary = build_manifest_and_summary(root, generated_at_utc, digest_summary=digest_summary)
    manifest.to_csv(share_dir / BASELINE_MANIFEST_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / BASELINE_SUMMARY_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
