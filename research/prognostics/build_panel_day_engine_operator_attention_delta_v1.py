#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd

CURRENT_ATTENTION_NAME = "panel_day_engine_operator_attention_now_v1.csv"
PREVIOUS_ATTENTION_NAME = "panel_day_engine_operator_attention_now_v1_previous.csv"
DELTA_OUTPUT_NAME = "panel_day_engine_operator_attention_delta_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_attention_delta_summary_v1.csv"

KEY_COLS = ["site", "panel_id"]
TEXT_COMPARE_COLS = [
    "attention_class",
    "display_status_or_tier",
    "priority_band",
    "action_bucket",
    "watchlist_bucket",
]
FLAG_COMPARE_COLS = [
    "panel_has_watch_now_overlap_flag",
    "attention_any_future_fault_linked_ref_flag",
    "attention_any_future_truth_linked_ref_flag",
]
NUMERIC_COMPARE_COLS = ["clipped_operator_score"]
CURRENT_REQUIRED_COLS = [*KEY_COLS, *TEXT_COMPARE_COLS, *FLAG_COMPARE_COLS, *NUMERIC_COMPARE_COLS]
DELTA_CLASS_PRIORITY = {
    "new_attention": 0,
    "dropped_attention": 1,
    "attention_class_changed": 2,
    "status_or_tier_changed": 3,
    "priority_changed": 4,
    "score_shifted": 5,
    "metadata_changed": 6,
}
EPSILON = 1e-9

DELTA_OUTPUT_COLS = [
    "site",
    "panel_id",
    "delta_class",
    "previous_attention_class",
    "current_attention_class",
    "previous_status_or_tier",
    "current_status_or_tier",
    "previous_priority_band",
    "current_priority_band",
    "previous_clipped_operator_score",
    "current_clipped_operator_score",
    "clipped_score_delta",
    "previous_action_bucket",
    "current_action_bucket",
    "previous_watchlist_bucket",
    "current_watchlist_bucket",
    "previous_panel_has_watch_now_overlap_flag",
    "current_panel_has_watch_now_overlap_flag",
    "previous_attention_any_future_fault_linked_ref_flag",
    "current_attention_any_future_fault_linked_ref_flag",
    "previous_attention_any_future_truth_linked_ref_flag",
    "current_attention_any_future_truth_linked_ref_flag",
    "delta_reason_ko",
]

SUMMARY_OUTPUT_COLS = [
    "record_type",
    "site",
    "current_attention_count",
    "previous_attention_count",
    "new_attention_count",
    "dropped_attention_count",
    "attention_class_changed_count",
    "status_or_tier_changed_count",
    "priority_changed_count",
    "score_shifted_count",
    "metadata_changed_count",
    "total_changed_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build operator attention delta feed from current/previous snapshots.")
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


def prepare_attention_snapshot(path: Path, *, required_current: bool) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=CURRENT_REQUIRED_COLS) if not required_current else None  # type: ignore[return-value]

    df = drop_repeated_header_rows(read_csv(path)).copy()
    ensure_columns(df, KEY_COLS, path.name)
    if required_current:
        ensure_columns(df, CURRENT_REQUIRED_COLS, path.name)
    else:
        for col in CURRENT_REQUIRED_COLS:
            if col not in df.columns:
                df[col] = ""

    for col in KEY_COLS + TEXT_COMPARE_COLS:
        df[col] = df[col].map(normalize_text)
    for col in NUMERIC_COMPARE_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in FLAG_COMPARE_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    deduped = df.drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)
    return deduped


def value_changed(previous: pd.Series, current: pd.Series, col: str) -> bool:
    if col in NUMERIC_COMPARE_COLS:
        prev_val = pd.to_numeric(previous.get(col), errors="coerce")
        curr_val = pd.to_numeric(current.get(col), errors="coerce")
        if pd.isna(prev_val) and pd.isna(curr_val):
            return False
        if pd.isna(prev_val) or pd.isna(curr_val):
            return True
        return abs(float(curr_val) - float(prev_val)) > EPSILON
    if col in FLAG_COMPARE_COLS:
        prev_val = int(pd.to_numeric(previous.get(col), errors="coerce") if pd.notna(previous.get(col)) else 0)
        curr_val = int(pd.to_numeric(current.get(col), errors="coerce") if pd.notna(current.get(col)) else 0)
        return prev_val != curr_val
    return normalize_text(previous.get(col)) != normalize_text(current.get(col))


def classify_delta(previous: pd.Series | None, current: pd.Series | None) -> str | None:
    if previous is None and current is not None:
        return "new_attention"
    if current is None and previous is not None:
        return "dropped_attention"
    if previous is None or current is None:
        return None

    class_changed = value_changed(previous, current, "attention_class")
    status_or_bucket_changed = any(
        value_changed(previous, current, col)
        for col in ["display_status_or_tier", "action_bucket", "watchlist_bucket"]
    )
    priority_changed = value_changed(previous, current, "priority_band")

    prev_score = pd.to_numeric(previous.get("clipped_operator_score"), errors="coerce")
    curr_score = pd.to_numeric(current.get("clipped_operator_score"), errors="coerce")
    score_shifted = False
    if pd.notna(prev_score) and pd.notna(curr_score):
        score_shifted = abs(float(curr_score) - float(prev_score)) >= 1.0
    elif pd.notna(prev_score) or pd.notna(curr_score):
        score_shifted = True

    metadata_changed = (
        not class_changed
        and not status_or_bucket_changed
        and not priority_changed
        and not score_shifted
        and any(value_changed(previous, current, col) for col in FLAG_COMPARE_COLS)
    )

    if class_changed:
        return "attention_class_changed"
    if status_or_bucket_changed:
        return "status_or_tier_changed"
    if priority_changed:
        return "priority_changed"
    if score_shifted:
        return "score_shifted"
    if metadata_changed:
        return "metadata_changed"
    return None


def delta_reason_ko(delta_class: str) -> str:
    mapping = {
        "new_attention": "신규 attention panel",
        "dropped_attention": "attention에서 제거됨",
        "attention_class_changed": "queue/watch class 변경",
        "status_or_tier_changed": "status 또는 tier 변경",
        "priority_changed": "priority 변경",
        "score_shifted": "score 큰 변동",
        "metadata_changed": "reference metadata 변경",
    }
    return mapping[delta_class]


def row_value(row: pd.Series | None, col: str, *, numeric: bool = False, flag: bool = False) -> object:
    if row is None:
        return ""
    if numeric:
        value = pd.to_numeric(row.get(col), errors="coerce")
        return None if pd.isna(value) else float(value)
    if flag:
        value = pd.to_numeric(row.get(col), errors="coerce")
        return "" if pd.isna(value) else int(value)
    return normalize_text(row.get(col))


def build_delta_rows(current: pd.DataFrame, previous: pd.DataFrame) -> pd.DataFrame:
    previous_map = {tuple(row[col] for col in KEY_COLS): row for _, row in previous.iterrows()}
    current_map = {tuple(row[col] for col in KEY_COLS): row for _, row in current.iterrows()}
    all_keys = sorted(set(previous_map) | set(current_map))

    rows: list[dict[str, object]] = []
    for key in all_keys:
        previous_row = previous_map.get(key)
        current_row = current_map.get(key)
        delta_class = classify_delta(previous_row, current_row)
        if delta_class is None:
            continue

        previous_score = row_value(previous_row, "clipped_operator_score", numeric=True)
        current_score = row_value(current_row, "clipped_operator_score", numeric=True)
        score_delta = None
        if previous_score != "" and current_score != "":
            score_delta = float(current_score) - float(previous_score)

        rows.append(
            {
                "site": key[0],
                "panel_id": key[1],
                "delta_class": delta_class,
                "previous_attention_class": row_value(previous_row, "attention_class"),
                "current_attention_class": row_value(current_row, "attention_class"),
                "previous_status_or_tier": row_value(previous_row, "display_status_or_tier"),
                "current_status_or_tier": row_value(current_row, "display_status_or_tier"),
                "previous_priority_band": row_value(previous_row, "priority_band"),
                "current_priority_band": row_value(current_row, "priority_band"),
                "previous_clipped_operator_score": previous_score,
                "current_clipped_operator_score": current_score,
                "clipped_score_delta": score_delta,
                "previous_action_bucket": row_value(previous_row, "action_bucket"),
                "current_action_bucket": row_value(current_row, "action_bucket"),
                "previous_watchlist_bucket": row_value(previous_row, "watchlist_bucket"),
                "current_watchlist_bucket": row_value(current_row, "watchlist_bucket"),
                "previous_panel_has_watch_now_overlap_flag": row_value(
                    previous_row, "panel_has_watch_now_overlap_flag", flag=True
                ),
                "current_panel_has_watch_now_overlap_flag": row_value(
                    current_row, "panel_has_watch_now_overlap_flag", flag=True
                ),
                "previous_attention_any_future_fault_linked_ref_flag": row_value(
                    previous_row, "attention_any_future_fault_linked_ref_flag", flag=True
                ),
                "current_attention_any_future_fault_linked_ref_flag": row_value(
                    current_row, "attention_any_future_fault_linked_ref_flag", flag=True
                ),
                "previous_attention_any_future_truth_linked_ref_flag": row_value(
                    previous_row, "attention_any_future_truth_linked_ref_flag", flag=True
                ),
                "current_attention_any_future_truth_linked_ref_flag": row_value(
                    current_row, "attention_any_future_truth_linked_ref_flag", flag=True
                ),
                "delta_reason_ko": delta_reason_ko(delta_class),
            }
        )

    delta = pd.DataFrame(rows, columns=DELTA_OUTPUT_COLS)
    if delta.empty:
        return delta

    delta["_delta_order"] = delta["delta_class"].map(DELTA_CLASS_PRIORITY).fillna(99)
    delta = delta.sort_values(
        ["_delta_order", "site", "panel_id"],
        ascending=[True, True, True],
        kind="mergesort",
    ).drop(columns=["_delta_order"])
    return delta.reset_index(drop=True)


def count_by_delta_class(scope_delta: pd.DataFrame, delta_class: str) -> int:
    return int(scope_delta["delta_class"].eq(delta_class).sum()) if not scope_delta.empty else 0


def build_delta_summary(delta: pd.DataFrame, current: pd.DataFrame, previous: pd.DataFrame) -> pd.DataFrame:
    sites = sorted(set(current["site"].dropna().astype(str)) | set(previous["site"].dropna().astype(str)))
    rows: list[dict[str, object]] = []

    def build_row(scope_site: str | None) -> dict[str, object]:
        if scope_site is None:
            current_scope = current
            previous_scope = previous
            delta_scope = delta
            record_type = "overall"
            site_value = ""
        else:
            current_scope = current.loc[current["site"].eq(scope_site)]
            previous_scope = previous.loc[previous["site"].eq(scope_site)]
            delta_scope = delta.loc[delta["site"].eq(scope_site)]
            record_type = "site"
            site_value = scope_site
        return {
            "record_type": record_type,
            "site": site_value,
            "current_attention_count": int(len(current_scope)),
            "previous_attention_count": int(len(previous_scope)),
            "new_attention_count": count_by_delta_class(delta_scope, "new_attention"),
            "dropped_attention_count": count_by_delta_class(delta_scope, "dropped_attention"),
            "attention_class_changed_count": count_by_delta_class(delta_scope, "attention_class_changed"),
            "status_or_tier_changed_count": count_by_delta_class(delta_scope, "status_or_tier_changed"),
            "priority_changed_count": count_by_delta_class(delta_scope, "priority_changed"),
            "score_shifted_count": count_by_delta_class(delta_scope, "score_shifted"),
            "metadata_changed_count": count_by_delta_class(delta_scope, "metadata_changed"),
            "total_changed_count": int(len(delta_scope)),
        }

    rows.append(build_row(None))
    for site in sites:
        rows.append(build_row(site))
    return pd.DataFrame(rows, columns=SUMMARY_OUTPUT_COLS)


def build_outputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    share_dir = root / "_share"
    current_path = share_dir / CURRENT_ATTENTION_NAME
    previous_path = share_dir / PREVIOUS_ATTENTION_NAME

    if not current_path.exists():
        raise SystemExit(f"missing input: {current_path}")

    current = prepare_attention_snapshot(current_path, required_current=True)
    previous = prepare_attention_snapshot(previous_path, required_current=False)
    delta = build_delta_rows(current, previous)
    summary = build_delta_summary(delta, current, previous)
    return delta, summary


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    current_path = share_dir / CURRENT_ATTENTION_NAME
    previous_path = share_dir / PREVIOUS_ATTENTION_NAME
    delta, summary = build_outputs(root)

    delta.to_csv(share_dir / DELTA_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    shutil.copyfile(current_path, previous_path)


if __name__ == "__main__":
    main()
