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
PRECURSOR_REPORT_NAME = "fault_panel_result_precursor_report_v1.csv"
RAWONLY_CURRENT_NAME = "fault_panel_result_raw_only_current_v1.csv"
RAWONLY_SIGNAL_NAME = "fault_panel_result_raw_only_fault_signal_report_v1.csv"
DETAIL_OUTPUT_NAME = "panel_day_engine_report_entry_friction_axis_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_report_entry_friction_axis_summary_v1.csv"
DIRECT_FAMILY_NAMES = ["group_off_date", "site_event"]
SIGNAL_MARKER_BOOL_COLS = [
    "pre_ews",
    "prefault_B",
    "fault_like_day",
    "final_fault",
    "critical_fault",
]
SUPPORT_BOOL_COLS = [
    "recovered_any",
    "recovered_sustained",
    "re_drop",
    "subgroup_common_cause_candidate",
]
OUTPUT_COLS = [
    "site",
    "direct_flag_family",
    "panel_id",
    "direct_row_count",
    "direct_dates",
    "group_off_row_count",
    "site_event_soft_row_count",
    "site_event_hard_row_count",
    "has_current",
    "has_precursor",
    "has_rawonly",
    "current_exact_same_day_flag",
    "precursor_exact_same_day_flag",
    "rawonly_signal_exact_same_day_flag",
    "rawonly_start_exact_same_day_flag",
    "best_report_lane",
    "best_report_gap_d",
    "nearest_current_gap_d",
    "nearest_precursor_gap_d",
    "nearest_raw_signal_gap_d",
    "nearest_raw_start_gap_d",
    "any_pre_ews",
    "any_prefault_B",
    "any_fault_like_day",
    "any_final_fault",
    "any_critical_fault",
    "any_recovered_any",
    "any_recovered_sustained",
    "any_re_drop",
    "any_subgroup_common_cause_candidate",
    "blocker_type",
]
SUMMARY_COLS = [
    "direct_flag_family",
    "blocker_type",
    "panels",
    "total_direct_rows",
    "exact_current_panels",
    "exact_precursor_panels",
    "exact_rawonly_panels",
    "min_best_report_gap_d",
    "min_current_gap_d",
    "min_precursor_gap_d",
    "min_raw_signal_gap_d",
    "min_raw_start_gap_d",
]
NEAR_SIGNAL_ANCHOR_DAYS = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an evidence-only sidecar that explains where direct raw common-cause rows "
            "do or do not enter report-layer current/precursor/raw-only artifacts."
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
        help="Folder where the friction-axis sidecar CSVs will be written.",
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


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def add_missing_columns(df: pd.DataFrame, cols: list[str], default: object = 0) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col not in out.columns:
            out[col] = default
    return out


def prepare_raw_candidates(path: Path, site: str) -> pd.DataFrame:
    df = read_csv(path)
    df = add_missing_columns(df, SIGNAL_MARKER_BOOL_COLS + SUPPORT_BOOL_COLS + ["group_off_date", "site_event_soft", "site_event_hard", "critical_source"], default=0)
    ensure_columns(df, ["date", "panel_id"], f"{site}/{RAW_CANDIDATE_NAME}")
    out = df.copy()
    out["site"] = site
    out["panel_id"] = out["panel_id"].map(normalize_text)
    out["date"] = out["date"].map(normalize_date_text)
    for col in SIGNAL_MARKER_BOOL_COLS + SUPPORT_BOOL_COLS + ["group_off_date", "site_event_soft", "site_event_hard"]:
        out[col] = out[col].map(to_flag)
    out["critical_source"] = out["critical_source"].map(normalize_text)
    out["signal_marker_flag"] = (
        out[SIGNAL_MARKER_BOOL_COLS].sum(axis=1).gt(0)
        | (out["critical_source"].ne("") & out["critical_source"].ne("none"))
    ).astype(int)
    return out


def build_panel_dates(df: pd.DataFrame, date_cols: list[str]) -> dict[tuple[str, str], list[str]]:
    if df.empty:
        return {}
    out: dict[tuple[str, str], set[str]] = {}
    site_col = "site" if "site" in df.columns else None
    for row in df.to_dict(orient="records"):
        site = normalize_text(row.get(site_col)) if site_col else ""
        panel_id = normalize_text(row.get("panel_id"))
        if not panel_id:
            continue
        key = (site, panel_id)
        bucket = out.setdefault(key, set())
        for col in date_cols:
            if col not in row:
                continue
            value = normalize_date_text(row.get(col))
            if value:
                bucket.add(value)
    return {key: sorted(values) for key, values in out.items()}


def nearest_gap_days(anchor_dates: list[str], candidate_dates: list[str]) -> int | None:
    if not anchor_dates or not candidate_dates:
        return None
    anchor_ts = pd.to_datetime(pd.Series(anchor_dates), errors="coerce").dropna()
    candidate_ts = pd.to_datetime(pd.Series(candidate_dates), errors="coerce").dropna()
    if anchor_ts.empty or candidate_ts.empty:
        return None
    best: int | None = None
    for anchor in anchor_ts:
        diffs = (candidate_ts - anchor).dt.days.abs()
        local = int(diffs.min())
        best = local if best is None else min(best, local)
    return best


def exact_overlap(anchor_dates: list[str], candidate_dates: list[str]) -> int:
    if not anchor_dates or not candidate_dates:
        return 0
    return int(bool(set(anchor_dates) & set(candidate_dates)))


def pick_best_lane(
    current_gap: int | None,
    precursor_gap: int | None,
    raw_signal_gap: int | None,
    raw_start_gap: int | None,
) -> tuple[str, int | None]:
    candidates: list[tuple[str, int]] = []
    if current_gap is not None:
        candidates.append(("current", current_gap))
    if precursor_gap is not None:
        candidates.append(("precursor", precursor_gap))
    if raw_signal_gap is not None:
        candidates.append(("raw_signal", raw_signal_gap))
    if raw_start_gap is not None:
        candidates.append(("raw_start", raw_start_gap))
    if not candidates:
        return "none", None
    lane, gap = min(candidates, key=lambda item: (item[1], item[0]))
    return lane, gap


def classify_blocker(
    current_exact: int,
    precursor_exact: int,
    raw_signal_exact: int,
    raw_start_exact: int,
    best_lane: str,
    best_gap: int | None,
) -> str:
    if current_exact:
        return "current_exact_overlap"
    if precursor_exact:
        return "precursor_exact_overlap"
    if raw_signal_exact or raw_start_exact:
        return "rawonly_exact_overlap"
    if best_lane == "none":
        return "no_report_lane_entry"
    if best_lane == "current":
        return "current_date_displaced"
    if best_lane == "precursor":
        return "precursor_carryover_without_exact_overlap"
    if best_lane in {"raw_signal", "raw_start"}:
        if best_gap is not None and best_gap <= NEAR_SIGNAL_ANCHOR_DAYS:
            return "rawonly_near_signal_anchor"
        return "rawonly_date_displaced"
    return "no_report_lane_entry"


def filter_direct_family(df: pd.DataFrame, family: str) -> pd.DataFrame:
    if family == "group_off_date":
        mask = df["group_off_date"].eq(1)
    elif family == "site_event":
        mask = df["site_event_soft"].eq(1) | df["site_event_hard"].eq(1)
    else:
        raise SystemExit(f"unknown family: {family}")
    return df.loc[mask & df["signal_marker_flag"].eq(1)].copy()


def aggregate_family_rows(
    family_df: pd.DataFrame,
    family: str,
    current_dates: dict[tuple[str, str], list[str]],
    precursor_dates: dict[tuple[str, str], list[str]],
    raw_start_dates: dict[tuple[str, str], list[str]],
    raw_signal_dates: dict[tuple[str, str], list[str]],
) -> list[dict[str, object]]:
    if family_df.empty:
        return []

    rows: list[dict[str, object]] = []
    for (site, panel_id), panel_df in family_df.groupby(["site", "panel_id"], sort=True):
        direct_dates = sorted(panel_df["date"].map(normalize_date_text).unique().tolist())
        key = (site, panel_id)
        current_panel_dates = current_dates.get(key, [])
        precursor_panel_dates = precursor_dates.get(key, [])
        raw_start_panel_dates = raw_start_dates.get(key, [])
        raw_signal_panel_dates = raw_signal_dates.get(key, [])
        current_exact = exact_overlap(direct_dates, current_panel_dates)
        precursor_exact = exact_overlap(direct_dates, precursor_panel_dates)
        raw_signal_exact = exact_overlap(direct_dates, raw_signal_panel_dates)
        raw_start_exact = exact_overlap(direct_dates, raw_start_panel_dates)
        current_gap = nearest_gap_days(direct_dates, current_panel_dates)
        precursor_gap = nearest_gap_days(direct_dates, precursor_panel_dates)
        raw_signal_gap = nearest_gap_days(direct_dates, raw_signal_panel_dates)
        raw_start_gap = nearest_gap_days(direct_dates, raw_start_panel_dates)
        best_lane, best_gap = pick_best_lane(current_gap, precursor_gap, raw_signal_gap, raw_start_gap)
        rows.append(
            {
                "site": site,
                "direct_flag_family": family,
                "panel_id": panel_id,
                "direct_row_count": int(len(panel_df)),
                "direct_dates": "|".join(direct_dates),
                "group_off_row_count": int(panel_df["group_off_date"].sum()),
                "site_event_soft_row_count": int(panel_df["site_event_soft"].sum()),
                "site_event_hard_row_count": int(panel_df["site_event_hard"].sum()),
                "has_current": int(bool(current_panel_dates)),
                "has_precursor": int(bool(precursor_panel_dates)),
                "has_rawonly": int(bool(raw_signal_panel_dates or raw_start_panel_dates)),
                "current_exact_same_day_flag": current_exact,
                "precursor_exact_same_day_flag": precursor_exact,
                "rawonly_signal_exact_same_day_flag": raw_signal_exact,
                "rawonly_start_exact_same_day_flag": raw_start_exact,
                "best_report_lane": best_lane,
                "best_report_gap_d": best_gap,
                "nearest_current_gap_d": current_gap,
                "nearest_precursor_gap_d": precursor_gap,
                "nearest_raw_signal_gap_d": raw_signal_gap,
                "nearest_raw_start_gap_d": raw_start_gap,
                "any_pre_ews": int(panel_df["pre_ews"].sum() > 0),
                "any_prefault_B": int(panel_df["prefault_B"].sum() > 0),
                "any_fault_like_day": int(panel_df["fault_like_day"].sum() > 0),
                "any_final_fault": int(panel_df["final_fault"].sum() > 0),
                "any_critical_fault": int(panel_df["critical_fault"].sum() > 0),
                "any_recovered_any": int(panel_df["recovered_any"].sum() > 0),
                "any_recovered_sustained": int(panel_df["recovered_sustained"].sum() > 0),
                "any_re_drop": int(panel_df["re_drop"].sum() > 0),
                "any_subgroup_common_cause_candidate": int(panel_df["subgroup_common_cause_candidate"].sum() > 0),
                "blocker_type": classify_blocker(
                    current_exact=current_exact,
                    precursor_exact=precursor_exact,
                    raw_signal_exact=raw_signal_exact,
                    raw_start_exact=raw_start_exact,
                    best_lane=best_lane,
                    best_gap=best_gap,
                ),
            }
        )
    return rows


def summarize(detail_df: pd.DataFrame) -> pd.DataFrame:
    if detail_df.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    working = detail_df.copy()
    working["rawonly_exact_any_flag"] = (
        working["rawonly_signal_exact_same_day_flag"].fillna(0).astype(int)
        | working["rawonly_start_exact_same_day_flag"].fillna(0).astype(int)
    )
    grouped = (
        working.groupby(["direct_flag_family", "blocker_type"], dropna=False)
        .agg(
            panels=("panel_id", "nunique"),
            total_direct_rows=("direct_row_count", "sum"),
            exact_current_panels=("current_exact_same_day_flag", "sum"),
            exact_precursor_panels=("precursor_exact_same_day_flag", "sum"),
            exact_rawonly_panels=("rawonly_exact_any_flag", "sum"),
            min_best_report_gap_d=("best_report_gap_d", "min"),
            min_current_gap_d=("nearest_current_gap_d", "min"),
            min_precursor_gap_d=("nearest_precursor_gap_d", "min"),
            min_raw_signal_gap_d=("nearest_raw_signal_gap_d", "min"),
            min_raw_start_gap_d=("nearest_raw_start_gap_d", "min"),
        )
        .reset_index()
    )
    return grouped.reindex(columns=SUMMARY_COLS)


def find_first_existing(root: Path, names: list[str]) -> pd.DataFrame:
    for name in names:
        path = root / name
        if path.exists():
            return read_csv(path, required=True)
    return pd.DataFrame()


def main() -> None:
    args = parse_args()
    data_root = args.data_root
    result_root = args.result_root
    output_dir = args.output_dir
    sites = [normalize_text(site) for site in args.sites if normalize_text(site)]
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_frames: list[pd.DataFrame] = []
    for site in sites:
        raw_frames.append(prepare_raw_candidates(data_root / site / "out" / RAW_CANDIDATE_NAME, site))
    raw_df = pd.concat(raw_frames, ignore_index=True) if raw_frames else pd.DataFrame()

    current_df = find_first_existing(result_root, CURRENT_RESULT_NAMES)
    precursor_df = read_csv(result_root / PRECURSOR_REPORT_NAME, required=False)
    rawonly_current_df = read_csv(result_root / RAWONLY_CURRENT_NAME, required=False)
    rawonly_signal_df = read_csv(result_root / RAWONLY_SIGNAL_NAME, required=False)

    current_dates = build_panel_dates(current_df, ["고장날짜", "고장 기준일", "신호 기준일"])
    precursor_dates = build_panel_dates(precursor_df, ["전조날짜"])
    raw_start_dates = build_panel_dates(rawonly_current_df, ["전조날짜"])
    raw_signal_dates = build_panel_dates(rawonly_signal_df, ["신호 기준일", "전조 시작일"])

    detail_rows: list[dict[str, object]] = []
    for family in DIRECT_FAMILY_NAMES:
        family_df = filter_direct_family(raw_df, family)
        detail_rows.extend(
            aggregate_family_rows(
                family_df=family_df,
                family=family,
                current_dates=current_dates,
                precursor_dates=precursor_dates,
                raw_start_dates=raw_start_dates,
                raw_signal_dates=raw_signal_dates,
            )
        )

    detail_df = pd.DataFrame(detail_rows).reindex(columns=OUTPUT_COLS)
    summary_df = summarize(detail_df)
    detail_df.to_csv(output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
