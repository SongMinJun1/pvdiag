#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_SITES = ["conalog", "gangui", "ktc_ess"]
RAW_CANDIDATE_NAME = "ae_simple_fault_candidates.csv"
CURRENT_RESULT_NAMES = [
    "fault_panel_result_current_v1.csv",
    "fault_panel_result_current_preview_v1.csv",
]
RAWONLY_CURRENT_NAMES = [
    "fault_panel_result_raw_only_current_v1.csv",
    "fault_panel_result_raw_only_current_preview_v1.csv",
]
PRECURSOR_REPORT_NAME = "fault_panel_result_precursor_report_v1.csv"
RAWONLY_SIGNAL_NAME = "fault_panel_result_raw_only_fault_signal_report_v1.csv"
DETAIL_OUTPUT_NAME = "panel_day_engine_recovery_recurrence_axis_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_recovery_recurrence_axis_summary_v1.csv"
RECOVERY_BOOL_COLS = ["recovered_any", "recovered_sustained", "re_drop"]
SIGNAL_MARKER_BOOL_COLS = [
    "pre_ews",
    "prefault_B",
    "fault_like_day",
    "final_fault",
    "critical_fault",
]
SUPPORT_BOOL_COLS = [
    "group_off_date",
    "site_event_soft",
    "site_event_hard",
    "subgroup_common_cause_candidate",
]
OUTPUT_COLS = [
    "site",
    "panel_id",
    "candidate_row_count",
    "signal_row_count",
    "recovery_row_count",
    "recovered_any_row_count",
    "recovered_sustained_row_count",
    "re_drop_row_count",
    "first_signal_date",
    "first_recovery_date",
    "last_recovery_date",
    "max_sustain_mins",
    "first_drop_time",
    "last_drop_time",
    "has_official_current",
    "has_rawonly_current",
    "has_precursor",
    "has_rawonly_signal",
    "best_report_lane",
    "recovery_bucket",
    "recovery_lane_bucket",
    "any_pre_ews",
    "any_prefault_B",
    "any_fault_like_day",
    "any_final_fault",
    "any_critical_fault",
    "any_group_off_date",
    "any_site_event",
    "any_subgroup_common_cause_candidate",
]
SUMMARY_COLS = [
    "site",
    "best_report_lane",
    "recovery_bucket",
    "panels",
    "total_candidate_rows",
    "total_signal_rows",
    "total_recovery_rows",
    "max_sustain_mins",
    "panels_with_group_off",
    "panels_with_site_event",
    "panels_with_subgroup_common_cause_candidate",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an evidence-only sidecar that explains transient recovery, sustained recovery, "
            "re-drop, and persistent non-recovery across report lanes."
        )
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        required=True,
        help="Folder containing <site>/out/ae_simple_fault_candidates.csv.",
    )
    parser.add_argument(
        "--result-root",
        type=Path,
        required=True,
        help="Folder containing result CSVs from run_full_algorithm_pack.py.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Folder where the recovery/recurrence sidecar CSVs will be written.",
    )
    parser.add_argument(
        "--sites",
        nargs="*",
        default=DEFAULT_SITES,
        help="Sites to include. Defaults to conalog, gangui, ktc_ess.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def normalize_date_text(value: object) -> str:
    text = normalize_text(value)
    return text[:10] if len(text) >= 10 else text


def to_flag(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return 1
    if text in {"0", "false", "f", "no", "n", ""}:
        return 0
    try:
        return 1 if float(text) > 0 else 0
    except ValueError:
        return 0


def read_csv(path: Path, required: bool = True) -> pd.DataFrame:
    if not path.exists():
        if required:
            raise SystemExit(f"missing input: {path}")
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def add_missing_columns(df: pd.DataFrame, cols: list[str], default: object = 0) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col not in out.columns:
            out[col] = default
    return out


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def find_first_existing(root: Path, names: list[str]) -> pd.DataFrame:
    for name in names:
        path = root / name
        if path.exists():
            return read_csv(path, required=True)
    return pd.DataFrame()


def prepare_raw_candidates(path: Path, site: str) -> pd.DataFrame:
    df = read_csv(path)
    df = add_missing_columns(
        df,
        RECOVERY_BOOL_COLS + SIGNAL_MARKER_BOOL_COLS + SUPPORT_BOOL_COLS + ["sustain_mins", "drop_time"],
        default=0,
    )
    ensure_columns(df, ["date", "panel_id"], f"{site}/{RAW_CANDIDATE_NAME}")
    out = df.copy()
    out["site"] = site
    out["panel_id"] = out["panel_id"].map(normalize_text)
    out["date"] = out["date"].map(normalize_date_text)
    for col in RECOVERY_BOOL_COLS + SIGNAL_MARKER_BOOL_COLS + SUPPORT_BOOL_COLS:
        out[col] = out[col].map(to_flag)
    out["signal_marker_flag"] = out[SIGNAL_MARKER_BOOL_COLS].sum(axis=1).gt(0).astype(int)
    out["recovery_marker_flag"] = out[RECOVERY_BOOL_COLS].sum(axis=1).gt(0).astype(int)
    out["candidate_flag"] = (out["signal_marker_flag"].eq(1) | out["recovery_marker_flag"].eq(1)).astype(int)
    out["sustain_mins"] = pd.to_numeric(out["sustain_mins"], errors="coerce")
    out["drop_time"] = out["drop_time"].map(normalize_text)
    return out


def build_panel_keys(df: pd.DataFrame) -> set[tuple[str, str]]:
    if df.empty or "panel_id" not in df.columns:
        return set()
    site_present = "site" in df.columns
    keys = set()
    for row in df.to_dict(orient="records"):
        site = normalize_text(row.get("site")) if site_present else ""
        panel_id = normalize_text(row.get("panel_id"))
        if panel_id:
            keys.add((site, panel_id))
    return keys


def pick_best_lane(
    key: tuple[str, str],
    official_current_keys: set[tuple[str, str]],
    rawonly_current_keys: set[tuple[str, str]],
    precursor_keys: set[tuple[str, str]],
    rawonly_signal_keys: set[tuple[str, str]],
) -> str:
    if key in official_current_keys:
        return "official_current"
    if key in rawonly_current_keys:
        return "rawonly_current"
    if key in precursor_keys:
        return "precursor"
    if key in rawonly_signal_keys:
        return "rawonly_signal"
    return "none"


def classify_recovery_bucket(panel_df: pd.DataFrame) -> str:
    if panel_df["re_drop"].sum() > 0:
        return "re_drop_cycle"
    if panel_df["recovered_sustained"].sum() > 0:
        return "sustained_recovery"
    if panel_df["recovered_any"].sum() > 0:
        return "transient_recovery"
    return "persistent_non_recovery"


def first_nonempty_sorted(values: list[str]) -> str:
    filtered = sorted(value for value in values if value)
    return filtered[0] if filtered else ""


def last_nonempty_sorted(values: list[str]) -> str:
    filtered = sorted(value for value in values if value)
    return filtered[-1] if filtered else ""


def aggregate_panels(
    raw_df: pd.DataFrame,
    official_current_keys: set[tuple[str, str]],
    rawonly_current_keys: set[tuple[str, str]],
    precursor_keys: set[tuple[str, str]],
    rawonly_signal_keys: set[tuple[str, str]],
) -> pd.DataFrame:
    candidate_df = raw_df.loc[raw_df["candidate_flag"].eq(1)].copy()
    rows: list[dict[str, object]] = []
    for (site, panel_id), panel_df in candidate_df.groupby(["site", "panel_id"], sort=True):
        key = (site, panel_id)
        recovery_dates = sorted(panel_df.loc[panel_df["recovery_marker_flag"].eq(1), "date"].map(normalize_date_text).unique().tolist())
        signal_dates = sorted(panel_df.loc[panel_df["signal_marker_flag"].eq(1), "date"].map(normalize_date_text).unique().tolist())
        drop_times = sorted(value for value in panel_df["drop_time"].map(normalize_text).tolist() if value)
        best_lane = pick_best_lane(
            key=key,
            official_current_keys=official_current_keys,
            rawonly_current_keys=rawonly_current_keys,
            precursor_keys=precursor_keys,
            rawonly_signal_keys=rawonly_signal_keys,
        )
        recovery_bucket = classify_recovery_bucket(panel_df)
        rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "candidate_row_count": int(len(panel_df)),
                "signal_row_count": int(panel_df["signal_marker_flag"].sum()),
                "recovery_row_count": int(panel_df["recovery_marker_flag"].sum()),
                "recovered_any_row_count": int(panel_df["recovered_any"].sum()),
                "recovered_sustained_row_count": int(panel_df["recovered_sustained"].sum()),
                "re_drop_row_count": int(panel_df["re_drop"].sum()),
                "first_signal_date": first_nonempty_sorted(signal_dates),
                "first_recovery_date": first_nonempty_sorted(recovery_dates),
                "last_recovery_date": last_nonempty_sorted(recovery_dates),
                "max_sustain_mins": panel_df["sustain_mins"].max(),
                "first_drop_time": first_nonempty_sorted(drop_times),
                "last_drop_time": last_nonempty_sorted(drop_times),
                "has_official_current": int(key in official_current_keys),
                "has_rawonly_current": int(key in rawonly_current_keys),
                "has_precursor": int(key in precursor_keys),
                "has_rawonly_signal": int(key in rawonly_signal_keys),
                "best_report_lane": best_lane,
                "recovery_bucket": recovery_bucket,
                "recovery_lane_bucket": f"{recovery_bucket}__{best_lane}",
                "any_pre_ews": int(panel_df["pre_ews"].sum() > 0),
                "any_prefault_B": int(panel_df["prefault_B"].sum() > 0),
                "any_fault_like_day": int(panel_df["fault_like_day"].sum() > 0),
                "any_final_fault": int(panel_df["final_fault"].sum() > 0),
                "any_critical_fault": int(panel_df["critical_fault"].sum() > 0),
                "any_group_off_date": int(panel_df["group_off_date"].sum() > 0),
                "any_site_event": int((panel_df["site_event_soft"].sum() + panel_df["site_event_hard"].sum()) > 0),
                "any_subgroup_common_cause_candidate": int(panel_df["subgroup_common_cause_candidate"].sum() > 0),
            }
        )
    return pd.DataFrame(rows).reindex(columns=OUTPUT_COLS)


def summarize(detail_df: pd.DataFrame) -> pd.DataFrame:
    if detail_df.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary_df = (
        detail_df.groupby(["site", "best_report_lane", "recovery_bucket"], dropna=False)
        .agg(
            panels=("panel_id", "nunique"),
            total_candidate_rows=("candidate_row_count", "sum"),
            total_signal_rows=("signal_row_count", "sum"),
            total_recovery_rows=("recovery_row_count", "sum"),
            max_sustain_mins=("max_sustain_mins", "max"),
            panels_with_group_off=("any_group_off_date", "sum"),
            panels_with_site_event=("any_site_event", "sum"),
            panels_with_subgroup_common_cause_candidate=("any_subgroup_common_cause_candidate", "sum"),
        )
        .reset_index()
    )
    return summary_df.reindex(columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    sites = [normalize_text(site) for site in args.sites if normalize_text(site)]

    raw_frames = [
        prepare_raw_candidates(args.data_root / site / "out" / RAW_CANDIDATE_NAME, site)
        for site in sites
    ]
    raw_df = pd.concat(raw_frames, ignore_index=True) if raw_frames else pd.DataFrame()

    official_current_df = find_first_existing(args.result_root, CURRENT_RESULT_NAMES)
    rawonly_current_df = find_first_existing(args.result_root, RAWONLY_CURRENT_NAMES)
    precursor_df = read_csv(args.result_root / PRECURSOR_REPORT_NAME, required=False)
    rawonly_signal_df = read_csv(args.result_root / RAWONLY_SIGNAL_NAME, required=False)

    official_current_keys = build_panel_keys(official_current_df)
    rawonly_current_keys = build_panel_keys(rawonly_current_df)
    precursor_keys = build_panel_keys(precursor_df)
    rawonly_signal_keys = build_panel_keys(rawonly_signal_df)

    detail_df = aggregate_panels(
        raw_df=raw_df,
        official_current_keys=official_current_keys,
        rawonly_current_keys=rawonly_current_keys,
        precursor_keys=precursor_keys,
        rawonly_signal_keys=rawonly_signal_keys,
    )
    summary_df = summarize(detail_df)

    detail_df.to_csv(output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
