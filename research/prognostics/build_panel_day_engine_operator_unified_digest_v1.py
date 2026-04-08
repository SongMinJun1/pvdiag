#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

CURRENT_PREVIEW_NAME = "panel_day_engine_operator_attention_plus_discovery_cluster_preview_v1.csv"
ATTENTION_DELTA_NAME = "panel_day_engine_operator_attention_delta_v1.csv"
CLUSTER_DELTA_NAME = "panel_day_engine_operator_secondary_discovery_cluster_delta_v1.csv"
UNIFIED_DIGEST_OUTPUT_NAME = "panel_day_engine_operator_unified_digest_v1.csv"
UNIFIED_DIGEST_SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_unified_digest_summary_v1.csv"

ALLOWED_PREVIEW_CLASSES = {"queue_run", "watch_now_panel", "secondary_value_cluster"}
ATTENTION_PREVIEW_CLASSES = {"queue_run", "watch_now_panel"}
CLASS_PRIORITY = {"queue_run": 0, "watch_now_panel": 1, "secondary_value_cluster": 2}
CURRENT_KEY_COLS = ["preview_attention_class", "site", "display_entity_id"]
ATTENTION_DELTA_KEY_COLS = ["site", "panel_id"]
CLUSTER_DELTA_KEY_COLS = ["site", "current_cluster_id"]

REQUIRED_PREVIEW_COLS = [
    "preview_attention_class",
    "site",
    "display_entity_id",
    "display_start_date",
    "display_end_date",
    "display_span_or_day_count",
    "display_shape_or_cluster_kind",
    "display_status_or_tier",
    "display_score",
    "linked_ref_flag",
    "truth_ref_flag",
    "cluster_panel_count",
    "preview_reason_ko",
]
REQUIRED_ATTENTION_DELTA_COLS = ["site", "panel_id", "delta_class", "delta_reason_ko"]
REQUIRED_CLUSTER_DELTA_COLS = ["site", "current_cluster_id", "delta_class", "delta_reason_ko"]

UNIFIED_DIGEST_COLS = [
    "preview_attention_class",
    "site",
    "display_entity_id",
    "display_start_date",
    "display_end_date",
    "display_span_or_day_count",
    "display_shape_or_cluster_kind",
    "display_status_or_tier",
    "display_score",
    "linked_ref_flag",
    "truth_ref_flag",
    "cluster_panel_count",
    "changed_since_previous_flag",
    "latest_delta_source",
    "latest_delta_class",
    "latest_delta_reason_ko",
    "digest_reason_ko",
]
UNIFIED_DIGEST_SUMMARY_COLS = [
    "record_type",
    "site",
    "digest_count",
    "queue_run_count",
    "watch_now_panel_count",
    "secondary_value_cluster_count",
    "changed_count",
    "changed_attention_count",
    "changed_cluster_count",
    "changed_queue_run_count",
    "changed_watch_now_panel_count",
    "changed_secondary_value_cluster_count",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a unified current-state operator digest by combining baseline attention + discovery cluster preview with attention_delta + cluster_delta."
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


def normalize_flag(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).gt(0).astype(int)


def ensure_unique(df: pd.DataFrame, key_cols: list[str], name: str) -> None:
    if df.duplicated(subset=key_cols).any():
        dup_df = df.loc[df.duplicated(subset=key_cols, keep=False), key_cols].drop_duplicates()
        raise SystemExit(f"{name} must be unique by {key_cols}, got duplicates: {dup_df.to_dict('records')}")


def prepare_preview(path: Path) -> pd.DataFrame:
    df = drop_repeated_header_rows(read_csv(path)).copy()
    ensure_columns(df, REQUIRED_PREVIEW_COLS, path.name)
    for col in [
        "preview_attention_class",
        "site",
        "display_entity_id",
        "display_start_date",
        "display_end_date",
        "display_shape_or_cluster_kind",
        "display_status_or_tier",
        "preview_reason_ko",
    ]:
        df[col] = df[col].map(normalize_text)
    bad_classes = sorted(set(df["preview_attention_class"]) - ALLOWED_PREVIEW_CLASSES)
    if bad_classes:
        raise SystemExit(f"{path.name} contains unsupported preview_attention_class values: {bad_classes}")
    for col in ["display_span_or_day_count", "display_score", "cluster_panel_count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["linked_ref_flag", "truth_ref_flag"]:
        df[col] = normalize_flag(df[col])
    if df["display_entity_id"].eq("").any():
        raise SystemExit(f"{path.name} contains blank display_entity_id")
    ensure_unique(df, CURRENT_KEY_COLS, path.name)
    return df.loc[:, REQUIRED_PREVIEW_COLS].copy()


def prepare_attention_delta(path: Path) -> pd.DataFrame:
    df = drop_repeated_header_rows(read_csv(path)).copy()
    if df.empty:
        return pd.DataFrame(columns=REQUIRED_ATTENTION_DELTA_COLS)
    ensure_columns(df, REQUIRED_ATTENTION_DELTA_COLS, path.name)
    for col in ["site", "panel_id", "delta_class", "delta_reason_ko"]:
        df[col] = df[col].map(normalize_text)
    ensure_unique(df, ATTENTION_DELTA_KEY_COLS, path.name)
    return df.loc[:, REQUIRED_ATTENTION_DELTA_COLS].copy()


def prepare_cluster_delta(path: Path) -> pd.DataFrame:
    df = drop_repeated_header_rows(read_csv(path)).copy()
    if df.empty:
        return pd.DataFrame(columns=REQUIRED_CLUSTER_DELTA_COLS)
    ensure_columns(df, REQUIRED_CLUSTER_DELTA_COLS, path.name)
    for col in ["site", "current_cluster_id", "delta_class", "delta_reason_ko"]:
        df[col] = df[col].map(normalize_text)
    current_delta = df.loc[df["current_cluster_id"].ne("")].copy()
    if current_delta.empty:
        return pd.DataFrame(columns=REQUIRED_CLUSTER_DELTA_COLS)
    ensure_unique(current_delta, CLUSTER_DELTA_KEY_COLS, path.name)
    return current_delta.loc[:, REQUIRED_CLUSTER_DELTA_COLS].copy()


def digest_reason_ko(
    preview_attention_class: str,
    changed_since_previous_flag: int,
    latest_delta_source: str,
    latest_delta_class: str,
) -> str:
    if preview_attention_class == "queue_run":
        base = "current queue_run item"
    elif preview_attention_class == "watch_now_panel":
        base = "current watch_now_panel item"
    else:
        base = "current secondary_value_cluster item"

    if changed_since_previous_flag == 0:
        return f"{base}이며 직전 snapshot 대비 변화 없음"
    if latest_delta_source == "attention_delta":
        return f"{base}이며 attention_delta={latest_delta_class} 변화가 반영됨"
    if latest_delta_source == "cluster_delta":
        return f"{base}이며 cluster_delta={latest_delta_class} 변화가 반영됨"
    return f"{base}이며 직전 snapshot 대비 변화가 반영됨"


def build_digest(
    preview: pd.DataFrame,
    attention_delta: pd.DataFrame,
    cluster_delta: pd.DataFrame,
) -> pd.DataFrame:
    digest = preview.copy()

    attention_join = attention_delta.rename(
        columns={
            "panel_id": "display_entity_id",
            "delta_class": "attention_latest_delta_class",
            "delta_reason_ko": "attention_latest_delta_reason_ko",
        }
    )
    cluster_join = cluster_delta.rename(
        columns={
            "current_cluster_id": "display_entity_id",
            "delta_class": "cluster_latest_delta_class",
            "delta_reason_ko": "cluster_latest_delta_reason_ko",
        }
    )

    digest = digest.merge(
        attention_join,
        on=["site", "display_entity_id"],
        how="left",
        validate="many_to_one",
    )
    digest = digest.merge(
        cluster_join,
        on=["site", "display_entity_id"],
        how="left",
        validate="many_to_one",
    )

    is_attention = digest["preview_attention_class"].isin(ATTENTION_PREVIEW_CLASSES)
    is_cluster = digest["preview_attention_class"].eq("secondary_value_cluster")
    matched_attention = is_attention & digest["attention_latest_delta_class"].map(normalize_text).ne("")
    matched_cluster = is_cluster & digest["cluster_latest_delta_class"].map(normalize_text).ne("")

    digest["changed_since_previous_flag"] = (matched_attention | matched_cluster).astype(int)
    digest["latest_delta_source"] = "none"
    digest.loc[matched_attention, "latest_delta_source"] = "attention_delta"
    digest.loc[matched_cluster, "latest_delta_source"] = "cluster_delta"

    digest["latest_delta_class"] = ""
    digest.loc[matched_attention, "latest_delta_class"] = (
        digest.loc[matched_attention, "attention_latest_delta_class"].map(normalize_text)
    )
    digest.loc[matched_cluster, "latest_delta_class"] = (
        digest.loc[matched_cluster, "cluster_latest_delta_class"].map(normalize_text)
    )

    digest["latest_delta_reason_ko"] = ""
    digest.loc[matched_attention, "latest_delta_reason_ko"] = (
        digest.loc[matched_attention, "attention_latest_delta_reason_ko"].map(normalize_text)
    )
    digest.loc[matched_cluster, "latest_delta_reason_ko"] = (
        digest.loc[matched_cluster, "cluster_latest_delta_reason_ko"].map(normalize_text)
    )

    digest["digest_reason_ko"] = digest.apply(
        lambda row: digest_reason_ko(
            preview_attention_class=normalize_text(row["preview_attention_class"]),
            changed_since_previous_flag=int(row["changed_since_previous_flag"]),
            latest_delta_source=normalize_text(row["latest_delta_source"]),
            latest_delta_class=normalize_text(row["latest_delta_class"]),
        ),
        axis=1,
    )

    digest["_class_order"] = digest["preview_attention_class"].map(CLASS_PRIORITY).fillna(99)
    digest = digest.sort_values(
        [
            "_class_order",
            "changed_since_previous_flag",
            "display_score",
            "cluster_panel_count",
            "display_span_or_day_count",
            "site",
            "display_entity_id",
        ],
        ascending=[True, False, False, False, False, True, True],
        kind="mergesort",
    ).drop(columns=["_class_order", "attention_latest_delta_class", "attention_latest_delta_reason_ko", "cluster_latest_delta_class", "cluster_latest_delta_reason_ko"])
    return digest.reindex(columns=UNIFIED_DIGEST_COLS).reset_index(drop=True)


def build_summary(digest: pd.DataFrame) -> pd.DataFrame:
    sites = sorted(digest["site"].dropna().map(normalize_text).unique())
    rows: list[dict[str, object]] = []

    def build_row(site: str | None) -> dict[str, object]:
        if site is None:
            scope = digest
            record_type = "overall"
            site_value = ""
        else:
            scope = digest.loc[digest["site"].eq(site)]
            record_type = "site"
            site_value = site

        queue_run_count = int(scope["preview_attention_class"].eq("queue_run").sum())
        watch_now_panel_count = int(scope["preview_attention_class"].eq("watch_now_panel").sum())
        secondary_value_cluster_count = int(scope["preview_attention_class"].eq("secondary_value_cluster").sum())
        changed_queue_run_count = int(
            (scope["preview_attention_class"].eq("queue_run") & scope["changed_since_previous_flag"].eq(1)).sum()
        )
        changed_watch_now_panel_count = int(
            (scope["preview_attention_class"].eq("watch_now_panel") & scope["changed_since_previous_flag"].eq(1)).sum()
        )
        changed_secondary_value_cluster_count = int(
            (scope["preview_attention_class"].eq("secondary_value_cluster") & scope["changed_since_previous_flag"].eq(1)).sum()
        )
        changed_attention_count = changed_queue_run_count + changed_watch_now_panel_count
        changed_cluster_count = changed_secondary_value_cluster_count
        return {
            "record_type": record_type,
            "site": site_value,
            "digest_count": int(len(scope)),
            "queue_run_count": queue_run_count,
            "watch_now_panel_count": watch_now_panel_count,
            "secondary_value_cluster_count": secondary_value_cluster_count,
            "changed_count": int(scope["changed_since_previous_flag"].sum()),
            "changed_attention_count": changed_attention_count,
            "changed_cluster_count": changed_cluster_count,
            "changed_queue_run_count": changed_queue_run_count,
            "changed_watch_now_panel_count": changed_watch_now_panel_count,
            "changed_secondary_value_cluster_count": changed_secondary_value_cluster_count,
            "note_ko": "current baseline attention과 secondary discovery cluster preview를 delta context와 함께 unified digest로 노출",
        }

    rows.append(build_row(None))
    for site in sites:
        rows.append(build_row(site))
    return pd.DataFrame(rows, columns=UNIFIED_DIGEST_SUMMARY_COLS)


def build_outputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    share_dir = root / "_share"
    preview = prepare_preview(share_dir / CURRENT_PREVIEW_NAME)
    attention_delta = prepare_attention_delta(share_dir / ATTENTION_DELTA_NAME)
    cluster_delta = prepare_cluster_delta(share_dir / CLUSTER_DELTA_NAME)
    digest = build_digest(preview, attention_delta, cluster_delta)
    summary = build_summary(digest)
    return digest, summary


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    digest, summary = build_outputs(root)
    digest.to_csv(share_dir / UNIFIED_DIGEST_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / UNIFIED_DIGEST_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
