#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd

CURRENT_CLUSTER_NAME = "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.csv"
PREVIOUS_CLUSTER_NAME = "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1_previous.csv"
DELTA_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_cluster_delta_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_cluster_delta_summary_v1.csv"

KEY_COLS = ["site", "cluster_id"]
REQUIRED_CLUSTER_COLS = [
    "site",
    "cluster_id",
    "cluster_start_date",
    "cluster_end_date",
    "panel_count",
    "representative_panel_id",
    "representative_run_start_date",
    "representative_run_end_date",
    "any_future_fault_linked_ref_flag",
    "any_future_truth_linked_ref_flag",
]
DATE_COLS = [
    "cluster_start_date",
    "cluster_end_date",
    "representative_run_start_date",
    "representative_run_end_date",
]
TEXT_COLS = ["site", "cluster_id", "representative_panel_id"]
FLAG_COLS = ["any_future_fault_linked_ref_flag", "any_future_truth_linked_ref_flag"]
MATCHED_DELTA_PRIORITY = {
    "representative_changed": 0,
    "linked_ref_changed": 1,
    "panel_count_changed": 2,
    "cluster_span_changed": 3,
}
DELTA_SORT_PRIORITY = {
    "new_cluster": 0,
    "dropped_cluster": 1,
    "representative_changed": 2,
    "linked_ref_changed": 3,
    "panel_count_changed": 4,
    "cluster_span_changed": 5,
}

DELTA_OUTPUT_COLS = [
    "site",
    "delta_class",
    "previous_cluster_id",
    "current_cluster_id",
    "previous_cluster_start_date",
    "previous_cluster_end_date",
    "current_cluster_start_date",
    "current_cluster_end_date",
    "previous_panel_count",
    "current_panel_count",
    "previous_representative_panel_id",
    "current_representative_panel_id",
    "previous_fault_linked_ref_flag",
    "current_fault_linked_ref_flag",
    "previous_truth_linked_ref_flag",
    "current_truth_linked_ref_flag",
    "overlap_days",
    "delta_reason_ko",
]

SUMMARY_OUTPUT_COLS = [
    "record_type",
    "site",
    "current_cluster_count",
    "previous_cluster_count",
    "changed_cluster_count",
    "new_cluster_count",
    "dropped_cluster_count",
    "representative_changed_count",
    "linked_ref_changed_count",
    "panel_count_changed_count",
    "cluster_span_changed_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an operator-facing delta feed for secondary discovery clusters."
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


def date_to_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def prepare_cluster_snapshot(path: Path, *, required_current: bool) -> pd.DataFrame:
    if not path.exists():
        if required_current:
            raise SystemExit(f"missing input: {path}")
        return pd.DataFrame(columns=REQUIRED_CLUSTER_COLS)

    df = drop_repeated_header_rows(read_csv(path)).copy()
    ensure_columns(df, REQUIRED_CLUSTER_COLS, path.name)
    for col in TEXT_COLS:
        df[col] = df[col].map(normalize_text)
    if df.duplicated(subset=KEY_COLS).any():
        dup_df = df.loc[df.duplicated(subset=KEY_COLS, keep=False), KEY_COLS].drop_duplicates()
        raise SystemExit(f"{path.name} must be unique by {KEY_COLS}, got duplicates: {dup_df.to_dict('records')}")
    for col in DATE_COLS:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        if df[col].isna().any():
            raise SystemExit(f"{path.name} contains invalid {col}")
    df["panel_count"] = pd.to_numeric(df["panel_count"], errors="coerce")
    if df["panel_count"].isna().any() or df["panel_count"].lt(1).any():
        raise SystemExit(f"{path.name} contains invalid panel_count")
    for col in FLAG_COLS:
        df[col] = normalize_flag(df[col])
    return df.loc[:, REQUIRED_CLUSTER_COLS].copy()


def overlap_days(
    current_start: pd.Timestamp,
    current_end: pd.Timestamp,
    previous_start: pd.Timestamp,
    previous_end: pd.Timestamp,
) -> int:
    overlap_start = max(current_start, previous_start)
    overlap_end = min(current_end, previous_end)
    if overlap_start > overlap_end:
        return 0
    return int((overlap_end - overlap_start).days + 1)


def build_site_matches(current: pd.DataFrame, previous: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    sites = sorted(set(current["site"].dropna().astype(str)) | set(previous["site"].dropna().astype(str)))
    for site in sites:
        current_scope = current.loc[current["site"].eq(site)].copy()
        previous_scope = previous.loc[previous["site"].eq(site)].copy()
        if current_scope.empty or previous_scope.empty:
            continue
        candidates: list[dict[str, object]] = []
        for _, current_row in current_scope.iterrows():
            for _, previous_row in previous_scope.iterrows():
                overlap = overlap_days(
                    pd.Timestamp(current_row["cluster_start_date"]),
                    pd.Timestamp(current_row["cluster_end_date"]),
                    pd.Timestamp(previous_row["cluster_start_date"]),
                    pd.Timestamp(previous_row["cluster_end_date"]),
                )
                if overlap < 1:
                    continue
                candidates.append(
                    {
                        "site": site,
                        "current_cluster_id": current_row["cluster_id"],
                        "previous_cluster_id": previous_row["cluster_id"],
                        "current_cluster_start_date": pd.Timestamp(current_row["cluster_start_date"]),
                        "current_cluster_end_date": pd.Timestamp(current_row["cluster_end_date"]),
                        "previous_cluster_start_date": pd.Timestamp(previous_row["cluster_start_date"]),
                        "previous_cluster_end_date": pd.Timestamp(previous_row["cluster_end_date"]),
                        "overlap_days": overlap,
                    }
                )
        candidates.sort(
            key=lambda row: (
                -int(row["overlap_days"]),
                pd.Timestamp(row["current_cluster_start_date"]),
                pd.Timestamp(row["current_cluster_end_date"]),
                pd.Timestamp(row["previous_cluster_start_date"]),
                pd.Timestamp(row["previous_cluster_end_date"]),
                str(row["current_cluster_id"]),
                str(row["previous_cluster_id"]),
            )
        )
        matched_current: set[tuple[str, str]] = set()
        matched_previous: set[tuple[str, str]] = set()
        for candidate in candidates:
            current_key = (site, str(candidate["current_cluster_id"]))
            previous_key = (site, str(candidate["previous_cluster_id"]))
            if current_key in matched_current or previous_key in matched_previous:
                continue
            matched_current.add(current_key)
            matched_previous.add(previous_key)
            rows.append(
                {
                    "site": site,
                    "current_cluster_id": candidate["current_cluster_id"],
                    "previous_cluster_id": candidate["previous_cluster_id"],
                    "overlap_days": int(candidate["overlap_days"]),
                }
            )
    match_df = pd.DataFrame(rows, columns=["site", "current_cluster_id", "previous_cluster_id", "overlap_days"])
    if match_df.empty:
        return match_df
    return match_df.sort_values(
        ["site", "overlap_days", "current_cluster_id", "previous_cluster_id"],
        ascending=[True, False, True, True],
        kind="mergesort",
    ).reset_index(drop=True)


def matched_delta_class(previous_row: pd.Series, current_row: pd.Series) -> str:
    representative_changed = any(
        [
            normalize_text(previous_row["representative_panel_id"]) != normalize_text(current_row["representative_panel_id"]),
            pd.Timestamp(previous_row["representative_run_start_date"])
            != pd.Timestamp(current_row["representative_run_start_date"]),
            pd.Timestamp(previous_row["representative_run_end_date"])
            != pd.Timestamp(current_row["representative_run_end_date"]),
        ]
    )
    linked_ref_changed = any(
        [
            int(previous_row["any_future_fault_linked_ref_flag"]) != int(current_row["any_future_fault_linked_ref_flag"]),
            int(previous_row["any_future_truth_linked_ref_flag"]) != int(current_row["any_future_truth_linked_ref_flag"]),
        ]
    )
    panel_count_changed = int(previous_row["panel_count"]) != int(current_row["panel_count"])
    cluster_span_changed = any(
        [
            pd.Timestamp(previous_row["cluster_start_date"]) != pd.Timestamp(current_row["cluster_start_date"]),
            pd.Timestamp(previous_row["cluster_end_date"]) != pd.Timestamp(current_row["cluster_end_date"]),
        ]
    )
    states = {
        "representative_changed": representative_changed,
        "linked_ref_changed": linked_ref_changed,
        "panel_count_changed": panel_count_changed,
        "cluster_span_changed": cluster_span_changed,
    }
    for delta_class, _priority in sorted(MATCHED_DELTA_PRIORITY.items(), key=lambda item: item[1]):
        if states[delta_class]:
            return delta_class
    return "unchanged"


def row_text(row: pd.Series | None, col: str) -> str:
    if row is None:
        return ""
    return normalize_text(row.get(col))


def row_date(row: pd.Series | None, col: str) -> str:
    if row is None:
        return ""
    return date_to_text(row.get(col))


def row_int(row: pd.Series | None, col: str) -> object:
    if row is None:
        return ""
    value = pd.to_numeric(pd.Series([row.get(col)]), errors="coerce").iloc[0]
    return "" if pd.isna(value) else int(value)


def delta_reason_ko(
    delta_class: str,
    previous_row: pd.Series | None,
    current_row: pd.Series | None,
) -> str:
    if delta_class == "new_cluster":
        return "이전 snapshot과 1일 이상 겹치는 cluster가 없어 신규 discovery cluster로 본다"
    if delta_class == "dropped_cluster":
        return "현재 snapshot과 1일 이상 겹치는 cluster가 없어 사라진 discovery cluster로 본다"
    if delta_class == "representative_changed":
        return (
            f"대표 panel/run이 {row_text(previous_row, 'representative_panel_id')}에서 "
            f"{row_text(current_row, 'representative_panel_id')}로 바뀌었다"
        )
    if delta_class == "linked_ref_changed":
        return (
            "retrospective linked reference flag가 "
            f"fault {row_int(previous_row, 'any_future_fault_linked_ref_flag')}->"
            f"{row_int(current_row, 'any_future_fault_linked_ref_flag')}, "
            f"truth {row_int(previous_row, 'any_future_truth_linked_ref_flag')}->"
            f"{row_int(current_row, 'any_future_truth_linked_ref_flag')}로 바뀌었다"
        )
    if delta_class == "panel_count_changed":
        return (
            f"cluster panel 수가 {row_int(previous_row, 'panel_count')}에서 "
            f"{row_int(current_row, 'panel_count')}로 바뀌었다"
        )
    if delta_class == "cluster_span_changed":
        return (
            f"cluster 기간이 {row_date(previous_row, 'cluster_start_date')}~{row_date(previous_row, 'cluster_end_date')}에서 "
            f"{row_date(current_row, 'cluster_start_date')}~{row_date(current_row, 'cluster_end_date')}로 바뀌었다"
        )
    return ""


def build_delta_rows(current: pd.DataFrame, previous: pd.DataFrame) -> pd.DataFrame:
    current_map = {tuple(row[col] for col in KEY_COLS): row for _, row in current.iterrows()}
    previous_map = {tuple(row[col] for col in KEY_COLS): row for _, row in previous.iterrows()}
    matches = build_site_matches(current, previous)

    matched_current_keys: set[tuple[str, str]] = set()
    matched_previous_keys: set[tuple[str, str]] = set()
    rows: list[dict[str, object]] = []

    for _, match in matches.iterrows():
        key_previous = (str(match["site"]), str(match["previous_cluster_id"]))
        key_current = (str(match["site"]), str(match["current_cluster_id"]))
        previous_row = previous_map[key_previous]
        current_row = current_map[key_current]
        matched_previous_keys.add(key_previous)
        matched_current_keys.add(key_current)
        delta_class = matched_delta_class(previous_row, current_row)
        if delta_class == "unchanged":
            continue
        rows.append(
            {
                "site": str(match["site"]),
                "delta_class": delta_class,
                "previous_cluster_id": row_text(previous_row, "cluster_id"),
                "current_cluster_id": row_text(current_row, "cluster_id"),
                "previous_cluster_start_date": row_date(previous_row, "cluster_start_date"),
                "previous_cluster_end_date": row_date(previous_row, "cluster_end_date"),
                "current_cluster_start_date": row_date(current_row, "cluster_start_date"),
                "current_cluster_end_date": row_date(current_row, "cluster_end_date"),
                "previous_panel_count": row_int(previous_row, "panel_count"),
                "current_panel_count": row_int(current_row, "panel_count"),
                "previous_representative_panel_id": row_text(previous_row, "representative_panel_id"),
                "current_representative_panel_id": row_text(current_row, "representative_panel_id"),
                "previous_fault_linked_ref_flag": row_int(previous_row, "any_future_fault_linked_ref_flag"),
                "current_fault_linked_ref_flag": row_int(current_row, "any_future_fault_linked_ref_flag"),
                "previous_truth_linked_ref_flag": row_int(previous_row, "any_future_truth_linked_ref_flag"),
                "current_truth_linked_ref_flag": row_int(current_row, "any_future_truth_linked_ref_flag"),
                "overlap_days": int(match["overlap_days"]),
                "delta_reason_ko": delta_reason_ko(delta_class, previous_row, current_row),
            }
        )

    unmatched_current = sorted(
        set(current_map) - matched_current_keys,
        key=lambda key: (
            key[0],
            pd.Timestamp(current_map[key]["cluster_start_date"]),
            pd.Timestamp(current_map[key]["cluster_end_date"]),
            key[1],
        ),
    )
    for key in unmatched_current:
        current_row = current_map[key]
        rows.append(
            {
                "site": key[0],
                "delta_class": "new_cluster",
                "previous_cluster_id": "",
                "current_cluster_id": row_text(current_row, "cluster_id"),
                "previous_cluster_start_date": "",
                "previous_cluster_end_date": "",
                "current_cluster_start_date": row_date(current_row, "cluster_start_date"),
                "current_cluster_end_date": row_date(current_row, "cluster_end_date"),
                "previous_panel_count": "",
                "current_panel_count": row_int(current_row, "panel_count"),
                "previous_representative_panel_id": "",
                "current_representative_panel_id": row_text(current_row, "representative_panel_id"),
                "previous_fault_linked_ref_flag": "",
                "current_fault_linked_ref_flag": row_int(current_row, "any_future_fault_linked_ref_flag"),
                "previous_truth_linked_ref_flag": "",
                "current_truth_linked_ref_flag": row_int(current_row, "any_future_truth_linked_ref_flag"),
                "overlap_days": 0,
                "delta_reason_ko": delta_reason_ko("new_cluster", None, current_row),
            }
        )

    unmatched_previous = sorted(
        set(previous_map) - matched_previous_keys,
        key=lambda key: (
            key[0],
            pd.Timestamp(previous_map[key]["cluster_start_date"]),
            pd.Timestamp(previous_map[key]["cluster_end_date"]),
            key[1],
        ),
    )
    for key in unmatched_previous:
        previous_row = previous_map[key]
        rows.append(
            {
                "site": key[0],
                "delta_class": "dropped_cluster",
                "previous_cluster_id": row_text(previous_row, "cluster_id"),
                "current_cluster_id": "",
                "previous_cluster_start_date": row_date(previous_row, "cluster_start_date"),
                "previous_cluster_end_date": row_date(previous_row, "cluster_end_date"),
                "current_cluster_start_date": "",
                "current_cluster_end_date": "",
                "previous_panel_count": row_int(previous_row, "panel_count"),
                "current_panel_count": "",
                "previous_representative_panel_id": row_text(previous_row, "representative_panel_id"),
                "current_representative_panel_id": "",
                "previous_fault_linked_ref_flag": row_int(previous_row, "any_future_fault_linked_ref_flag"),
                "current_fault_linked_ref_flag": "",
                "previous_truth_linked_ref_flag": row_int(previous_row, "any_future_truth_linked_ref_flag"),
                "current_truth_linked_ref_flag": "",
                "overlap_days": 0,
                "delta_reason_ko": delta_reason_ko("dropped_cluster", previous_row, None),
            }
        )

    delta = pd.DataFrame(rows, columns=DELTA_OUTPUT_COLS)
    if delta.empty:
        return delta
    delta["_delta_order"] = delta["delta_class"].map(DELTA_SORT_PRIORITY).fillna(99)
    delta = delta.sort_values(
        ["_delta_order", "site", "current_cluster_id", "previous_cluster_id"],
        ascending=[True, True, True, True],
        kind="mergesort",
    ).drop(columns=["_delta_order"])
    return delta.reset_index(drop=True)


def count_by_delta_class(scope_delta: pd.DataFrame, delta_class: str) -> int:
    return int(scope_delta["delta_class"].eq(delta_class).sum()) if not scope_delta.empty else 0


def build_delta_summary(delta: pd.DataFrame, current: pd.DataFrame, previous: pd.DataFrame) -> pd.DataFrame:
    sites = sorted(set(current["site"].dropna().astype(str)) | set(previous["site"].dropna().astype(str)))
    rows: list[dict[str, object]] = []

    def build_row(site: str | None) -> dict[str, object]:
        if site is None:
            current_scope = current
            previous_scope = previous
            delta_scope = delta
            record_type = "overall"
            site_value = ""
        else:
            current_scope = current.loc[current["site"].eq(site)]
            previous_scope = previous.loc[previous["site"].eq(site)]
            delta_scope = delta.loc[delta["site"].eq(site)]
            record_type = "site"
            site_value = site
        return {
            "record_type": record_type,
            "site": site_value,
            "current_cluster_count": int(len(current_scope)),
            "previous_cluster_count": int(len(previous_scope)),
            "changed_cluster_count": int(len(delta_scope)),
            "new_cluster_count": count_by_delta_class(delta_scope, "new_cluster"),
            "dropped_cluster_count": count_by_delta_class(delta_scope, "dropped_cluster"),
            "representative_changed_count": count_by_delta_class(delta_scope, "representative_changed"),
            "linked_ref_changed_count": count_by_delta_class(delta_scope, "linked_ref_changed"),
            "panel_count_changed_count": count_by_delta_class(delta_scope, "panel_count_changed"),
            "cluster_span_changed_count": count_by_delta_class(delta_scope, "cluster_span_changed"),
        }

    rows.append(build_row(None))
    for site in sites:
        rows.append(build_row(site))
    return pd.DataFrame(rows, columns=SUMMARY_OUTPUT_COLS)


def build_outputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    share_dir = root / "_share"
    current = prepare_cluster_snapshot(share_dir / CURRENT_CLUSTER_NAME, required_current=True)
    previous = prepare_cluster_snapshot(share_dir / PREVIOUS_CLUSTER_NAME, required_current=False)
    delta = build_delta_rows(current, previous)
    summary = build_delta_summary(delta, current, previous)
    return delta, summary


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    current_path = share_dir / CURRENT_CLUSTER_NAME
    previous_path = share_dir / PREVIOUS_CLUSTER_NAME

    delta, summary = build_outputs(root)
    delta.to_csv(share_dir / DELTA_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    shutil.copyfile(current_path, previous_path)


if __name__ == "__main__":
    main()
