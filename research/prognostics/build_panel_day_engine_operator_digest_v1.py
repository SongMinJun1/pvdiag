#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ATTENTION_NOW_NAME = "panel_day_engine_operator_attention_now_v1.csv"
ATTENTION_SUMMARY_NAME = "panel_day_engine_operator_attention_summary_v1.csv"
ATTENTION_DELTA_NAME = "panel_day_engine_operator_attention_delta_v1.csv"
ATTENTION_DELTA_SUMMARY_NAME = "panel_day_engine_operator_attention_delta_summary_v1.csv"
BASELINE_MANIFEST_NAME = "panel_day_engine_operator_baseline_manifest_v1.csv"
BASELINE_SUMMARY_NAME = "panel_day_engine_operator_baseline_summary_v1.csv"
DIGEST_OUTPUT_NAME = "panel_day_engine_operator_digest_v1.csv"
DIGEST_SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_digest_summary_v1.csv"

KEY_COLS = ["site", "panel_id"]
ATTENTION_REQUIRED_COLS = [
    "attention_class",
    "site",
    "panel_id",
    "display_status_or_tier",
    "priority_band",
    "clipped_operator_score",
    "display_day_count",
]
DELTA_REQUIRED_COLS = [
    "site",
    "panel_id",
    "delta_class",
    "delta_reason_ko",
    "previous_attention_class",
    "previous_status_or_tier",
    "previous_priority_band",
    "previous_clipped_operator_score",
    "clipped_score_delta",
]
ATTENTION_SUMMARY_REQUIRED_COLS = [
    "record_type",
    "site",
    "attention_count",
    "queue_run_attention_count",
    "watch_now_panel_attention_count",
]
DELTA_SUMMARY_REQUIRED_COLS = [
    "record_type",
    "site",
    "current_attention_count",
    "new_attention_count",
    "dropped_attention_count",
    "attention_class_changed_count",
    "status_or_tier_changed_count",
    "priority_changed_count",
    "score_shifted_count",
    "metadata_changed_count",
    "total_changed_count",
]
BASELINE_MANIFEST_REQUIRED_COLS = ["generated_at_utc"]
BASELINE_SUMMARY_REQUIRED_COLS = ["record_type", "site", "attention_count"]

ATTENTION_CLASS_PRIORITY = {"queue_run": 0, "watch_now_panel": 1}
PRIORITY_BAND_PRIORITY = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}

DIGEST_ADDED_COLS = [
    "changed_since_previous_flag",
    "latest_delta_class",
    "latest_delta_reason_ko",
    "previous_attention_class",
    "previous_status_or_tier",
    "previous_priority_band",
    "previous_clipped_operator_score",
    "clipped_score_delta",
    "baseline_generated_at_utc",
]

DIGEST_SUMMARY_OUTPUT_COLS = [
    "record_type",
    "site",
    "attention_count",
    "changed_attention_count",
    "unchanged_attention_count",
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a current-state operator digest by combining attention_now with latest delta context."
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
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def drop_repeated_header_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    header_mask = pd.Series(True, index=df.index)
    for col in df.columns:
        header_mask &= df[col].map(normalize_text).eq(col)
    return df.loc[~header_mask].reset_index(drop=True)


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def prepare_attention(path: Path) -> pd.DataFrame:
    df = drop_repeated_header_rows(read_csv(path)).copy()
    ensure_columns(df, ATTENTION_REQUIRED_COLS, path.name)
    for col in ["attention_class", "site", "panel_id", "display_status_or_tier", "priority_band"]:
        df[col] = df[col].map(normalize_text)
    for col in ["clipped_operator_score", "raw_operator_score", "display_day_count"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def prepare_delta(path: Path) -> pd.DataFrame:
    df = drop_repeated_header_rows(read_csv(path)).copy()
    if df.empty:
        return pd.DataFrame(columns=DELTA_REQUIRED_COLS)
    ensure_columns(df, DELTA_REQUIRED_COLS, path.name)
    for col in [
        "site",
        "panel_id",
        "delta_class",
        "delta_reason_ko",
        "previous_attention_class",
        "previous_status_or_tier",
        "previous_priority_band",
    ]:
        df[col] = df[col].map(normalize_text)
    for col in ["previous_clipped_operator_score", "clipped_score_delta"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def prepare_summary(path: Path, required: list[str]) -> pd.DataFrame:
    df = drop_repeated_header_rows(read_csv(path)).copy()
    ensure_columns(df, required, path.name)
    for col in ["record_type", "site"]:
        if col in df.columns:
            df[col] = df[col].map(normalize_text)
    for col in df.columns:
        if col in {"record_type", "site", "generated_at_utc"}:
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def derive_delta_summary(delta: pd.DataFrame, attention_summary: pd.DataFrame) -> pd.DataFrame:
    attention_scopes = attention_summary.loc[:, ["record_type", "site", "attention_count"]].copy()
    rows: list[dict[str, object]] = []
    for row in attention_scopes.itertuples(index=False):
        if normalize_text(row.record_type) == "overall":
            scope_delta = delta
            site_value = ""
        else:
            scope_delta = delta.loc[delta["site"].eq(normalize_text(row.site))]
            site_value = normalize_text(row.site)
        counts = scope_delta["delta_class"].value_counts()
        rows.append(
            {
                "record_type": normalize_text(row.record_type),
                "site": site_value,
                "current_attention_count": int(row.attention_count),
                "new_attention_count": int(counts.get("new_attention", 0)),
                "dropped_attention_count": int(counts.get("dropped_attention", 0)),
                "attention_class_changed_count": int(counts.get("attention_class_changed", 0)),
                "status_or_tier_changed_count": int(counts.get("status_or_tier_changed", 0)),
                "priority_changed_count": int(counts.get("priority_changed", 0)),
                "score_shifted_count": int(counts.get("score_shifted", 0)),
                "metadata_changed_count": int(counts.get("metadata_changed", 0)),
                "total_changed_count": int(len(scope_delta)),
            }
        )
    return pd.DataFrame(rows, columns=DELTA_SUMMARY_REQUIRED_COLS)


def load_delta_summary(root: Path, attention_summary: pd.DataFrame) -> pd.DataFrame:
    path = root / "_share" / ATTENTION_DELTA_SUMMARY_NAME
    if path.exists():
        return prepare_summary(path, DELTA_SUMMARY_REQUIRED_COLS)
    delta = prepare_delta(root / "_share" / ATTENTION_DELTA_NAME)
    return derive_delta_summary(delta, attention_summary)


def build_digest(attention: pd.DataFrame, delta: pd.DataFrame, baseline_generated_at_utc: str) -> pd.DataFrame:
    digest = attention.merge(delta, on=KEY_COLS, how="left", validate="one_to_one")
    digest["changed_since_previous_flag"] = digest["delta_class"].notna().astype(int)
    digest["latest_delta_class"] = digest["delta_class"].map(normalize_text)
    digest["latest_delta_reason_ko"] = digest["delta_reason_ko"].map(normalize_text)
    digest["baseline_generated_at_utc"] = baseline_generated_at_utc

    digest = digest.rename(
        columns={
            "delta_class": "latest_delta_class_tmp",
            "delta_reason_ko": "latest_delta_reason_ko_tmp",
        }
    )
    digest["latest_delta_class"] = digest.pop("latest_delta_class_tmp").map(normalize_text)
    digest["latest_delta_reason_ko"] = digest.pop("latest_delta_reason_ko_tmp").map(normalize_text)

    digest["_class_order"] = digest["attention_class"].map(ATTENTION_CLASS_PRIORITY).fillna(99)
    digest["_priority_order"] = digest["priority_band"].map(PRIORITY_BAND_PRIORITY).fillna(99)
    digest = digest.sort_values(
        [
            "_class_order",
            "changed_since_previous_flag",
            "_priority_order",
            "clipped_operator_score",
            "display_day_count",
            "site",
            "panel_id",
        ],
        ascending=[True, False, True, False, False, True, True],
        kind="mergesort",
    ).drop(columns=["_class_order", "_priority_order"])

    output_cols = [*attention.columns.tolist(), *DIGEST_ADDED_COLS]
    return digest.reindex(columns=output_cols).reset_index(drop=True)


def build_digest_summary(
    attention_summary: pd.DataFrame,
    delta_summary: pd.DataFrame,
    baseline_summary: pd.DataFrame,
    generated_at_utc: str,
) -> pd.DataFrame:
    merged = attention_summary.loc[:, ATTENTION_SUMMARY_REQUIRED_COLS].merge(
        delta_summary.loc[:, DELTA_SUMMARY_REQUIRED_COLS],
        on=["record_type", "site"],
        how="outer",
    )
    merged = merged.merge(
        baseline_summary.loc[:, BASELINE_SUMMARY_REQUIRED_COLS].rename(columns={"attention_count": "baseline_attention_count"}),
        on=["record_type", "site"],
        how="outer",
    )

    merged["record_type"] = merged["record_type"].map(normalize_text)
    merged["site"] = merged["site"].map(normalize_text)
    for col in [
        "attention_count",
        "queue_run_attention_count",
        "watch_now_panel_attention_count",
        "current_attention_count",
        "new_attention_count",
        "dropped_attention_count",
        "attention_class_changed_count",
        "status_or_tier_changed_count",
        "priority_changed_count",
        "score_shifted_count",
        "metadata_changed_count",
        "total_changed_count",
        "baseline_attention_count",
    ]:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")

    merged["attention_count"] = merged["attention_count"].fillna(merged["current_attention_count"]).fillna(
        merged["baseline_attention_count"]
    )
    merged["changed_attention_count"] = (
        merged["new_attention_count"].fillna(0)
        + merged["attention_class_changed_count"].fillna(0)
        + merged["status_or_tier_changed_count"].fillna(0)
        + merged["priority_changed_count"].fillna(0)
        + merged["score_shifted_count"].fillna(0)
        + merged["metadata_changed_count"].fillna(0)
    )
    merged["unchanged_attention_count"] = (
        merged["attention_count"].fillna(0) - merged["changed_attention_count"].fillna(0)
    ).clip(lower=0)

    summary = pd.DataFrame(
        {
            "record_type": merged["record_type"],
            "site": merged["site"],
            "attention_count": merged["attention_count"].fillna(0).astype(int),
            "changed_attention_count": merged["changed_attention_count"].fillna(0).astype(int),
            "unchanged_attention_count": merged["unchanged_attention_count"].fillna(0).astype(int),
            "queue_run_count": merged["queue_run_attention_count"].fillna(0).astype(int),
            "watch_now_panel_count": merged["watch_now_panel_attention_count"].fillna(0).astype(int),
            "new_attention_count": merged["new_attention_count"].fillna(0).astype(int),
            "dropped_attention_count": merged["dropped_attention_count"].fillna(0).astype(int),
            "attention_class_changed_count": merged["attention_class_changed_count"].fillna(0).astype(int),
            "status_or_tier_changed_count": merged["status_or_tier_changed_count"].fillna(0).astype(int),
            "priority_changed_count": merged["priority_changed_count"].fillna(0).astype(int),
            "score_shifted_count": merged["score_shifted_count"].fillna(0).astype(int),
            "metadata_changed_count": merged["metadata_changed_count"].fillna(0).astype(int),
            "generated_at_utc": generated_at_utc,
        },
        columns=DIGEST_SUMMARY_OUTPUT_COLS,
    )
    summary["_record_order"] = summary["record_type"].map({"overall": 0, "site": 1}).fillna(99)
    summary = summary.sort_values(["_record_order", "site"], ascending=[True, True], kind="mergesort").drop(
        columns=["_record_order"]
    )
    return summary.reset_index(drop=True)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"

    attention = prepare_attention(share_dir / ATTENTION_NOW_NAME)
    attention_summary = prepare_summary(share_dir / ATTENTION_SUMMARY_NAME, ATTENTION_SUMMARY_REQUIRED_COLS)
    delta = prepare_delta(share_dir / ATTENTION_DELTA_NAME)
    baseline_manifest = prepare_summary(share_dir / BASELINE_MANIFEST_NAME, BASELINE_MANIFEST_REQUIRED_COLS)
    baseline_summary = prepare_summary(share_dir / BASELINE_SUMMARY_NAME, BASELINE_SUMMARY_REQUIRED_COLS)
    delta_summary = load_delta_summary(root, attention_summary)

    if baseline_manifest.empty:
        raise SystemExit(f"{BASELINE_MANIFEST_NAME} missing manifest row")
    baseline_generated_at_utc = normalize_text(baseline_manifest.iloc[0]["generated_at_utc"])

    digest = build_digest(attention, delta, baseline_generated_at_utc)
    digest_summary = build_digest_summary(attention_summary, delta_summary, baseline_summary, baseline_generated_at_utc)

    digest.to_csv(share_dir / DIGEST_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    digest_summary.to_csv(share_dir / DIGEST_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
