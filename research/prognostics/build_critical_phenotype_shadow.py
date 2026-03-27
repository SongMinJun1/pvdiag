#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
CRITICAL_REASON_TOKEN = "strict_method=critical_fault_flag"
OUTPUT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "anchor_date",
    "vendor_reply_class",
    "vendor_fault_family",
    "mid_ratio",
    "last_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "v_drop",
    "v_ref_ok",
    "coverage_mid",
    "shadow_like",
    "group_off_like",
    "critical_phenotype",
    "phenotype_confidence",
    "phenotype_reason",
]
SUMMARY_COLS = [
    "site",
    "total_critical_cases",
    "count_diode_or_module_damage_like",
    "count_open_or_device_issue_like",
    "count_group_or_inverter_side_like",
    "count_weak_critical_candidate",
]
VENDOR_MATRIX_COLS = [
    "site",
    "critical_phenotype",
    "vendor_reply_class",
    "vendor_fault_family",
    "row_count",
]
VENDOR_INPUT_COLS = [
    "site",
    "panel_id",
    "vendor_reply_class",
    "vendor_fault_family",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split current critical fault flag cases into explicit shadow phenotypes.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    parser.add_argument(
        "--sites",
        nargs="*",
        default=SITES,
        help="Sites to process. Defaults to the known stable sites.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def to_bool(value: object) -> bool:
    text = normalize_text(value).lower()
    return text in {"1", "true", "t", "yes", "y"}


def to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def ensure_vendor_df(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=VENDOR_INPUT_COLS)
    df = read_csv(path)
    missing = [col for col in VENDOR_INPUT_COLS if col not in df.columns]
    if missing:
        raise SystemExit(f"vendor adjudication input missing columns: {missing}")
    for col in VENDOR_INPUT_COLS:
        df[col] = df[col].map(normalize_text)
    return df.loc[:, VENDOR_INPUT_COLS].copy()


def parse_strict_method(reason_summary: str) -> str:
    for part in normalize_text(reason_summary).split("|"):
        if part.startswith("strict_method="):
            return part.split("=", 1)[1]
    return ""


def select_anchor(window_df: pd.DataFrame, strict_trigger_date: pd.Timestamp) -> pd.Series:
    ranked = window_df.copy()
    ranked["v_drop_num"] = to_numeric(ranked["v_drop"]).fillna(float("-inf"))
    ranked["mid_v_ratio_num"] = to_numeric(ranked["mid_v_ratio"]).fillna(float("inf"))
    ranked["distance_days"] = (ranked["date_dt"] - strict_trigger_date).abs().dt.days
    ranked = ranked.sort_values(
        ["v_drop_num", "mid_v_ratio_num", "distance_days", "date_dt"],
        ascending=[False, True, True, True],
        kind="stable",
    )
    return ranked.iloc[0]


def classify(row: pd.Series) -> tuple[str, str, str]:
    mid_ratio = pd.to_numeric(row.get("mid_ratio"), errors="coerce")
    mid_v_ratio = pd.to_numeric(row.get("mid_v_ratio"), errors="coerce")
    mid_i_ratio = pd.to_numeric(row.get("mid_i_ratio"), errors="coerce")
    v_drop = pd.to_numeric(row.get("v_drop"), errors="coerce")
    coverage_mid = pd.to_numeric(row.get("coverage_mid"), errors="coerce")
    v_ref_ok = to_bool(row.get("v_ref_ok"))
    shadow_like = to_bool(row.get("shadow_like"))
    group_off_like = to_bool(row.get("group_off_like"))

    phenotype = "weak_critical_candidate"
    reason = []

    if (
        pd.notna(mid_ratio)
        and pd.notna(mid_v_ratio)
        and pd.notna(v_drop)
        and mid_ratio <= 0.10
        and mid_v_ratio <= 0.10
        and v_drop >= 0.90
    ):
        phenotype = "open_or_device_issue_like"
        reason.append("very_low_mid_ratio")
        reason.append("very_low_mid_v_ratio")
        reason.append("extreme_v_drop")
    elif (
        pd.notna(mid_ratio)
        and pd.notna(mid_i_ratio)
        and pd.notna(mid_v_ratio)
        and mid_ratio <= 0.10
        and mid_i_ratio <= 0.10
        and mid_v_ratio >= 1.05
    ):
        phenotype = "group_or_inverter_side_like"
        reason.append("very_low_mid_ratio")
        reason.append("very_low_mid_i_ratio")
        reason.append("high_mid_v_ratio")
    elif (
        v_ref_ok
        and not shadow_like
        and not group_off_like
        and pd.notna(coverage_mid)
        and pd.notna(mid_i_ratio)
        and pd.notna(mid_v_ratio)
        and pd.notna(mid_ratio)
        and pd.notna(v_drop)
        and coverage_mid >= 0.95
        and mid_i_ratio >= 0.90
        and mid_v_ratio <= 0.75
        and mid_ratio <= 0.78
        and v_drop >= 0.28
    ):
        phenotype = "diode_or_module_damage_like"
        reason.append("high_coverage")
        reason.append("current_preserved")
        reason.append("voltage_depressed")
        reason.append("moderate_to_strong_v_drop")
    else:
        reason.append("rule_not_met")

    if phenotype == "weak_critical_candidate":
        confidence = "low"
    elif shadow_like or group_off_like or (pd.notna(coverage_mid) and coverage_mid < 0.95):
        confidence = "medium"
    else:
        confidence = "high"

    return phenotype, confidence, "|".join(reason)


def build_rows(root: Path, sites: list[str]) -> pd.DataFrame:
    onset_path = root / "_share" / "panel_onset_shadow_latest.csv"
    vendor_path = root / "_share" / "vendor_reply_adjudication_latest.csv"
    onset_df = read_csv(onset_path)
    vendor_df = ensure_vendor_df(vendor_path)

    required_onset = ["site", "panel_id", "strict_trigger_date", "reason_summary"]
    missing = [col for col in required_onset if col not in onset_df.columns]
    if missing:
        raise SystemExit(f"panel_onset_shadow_latest.csv missing columns: {missing}")

    onset_df = onset_df.copy()
    onset_df["site"] = onset_df["site"].map(normalize_text)
    onset_df["panel_id"] = onset_df["panel_id"].map(normalize_text)
    onset_df["strict_method"] = onset_df["reason_summary"].map(parse_strict_method)
    onset_df = onset_df.loc[
        onset_df["site"].isin(sites) & onset_df["strict_method"].eq("critical_fault_flag")
    ].copy()

    vendor_lookup = vendor_df.set_index(["site", "panel_id"], drop=False) if not vendor_df.empty else pd.DataFrame(columns=VENDOR_INPUT_COLS).set_index(["site", "panel_id"], drop=False)

    rows: list[dict[str, object]] = []
    for site in sites:
        site_cases = onset_df.loc[onset_df["site"].eq(site)].copy()
        if site_cases.empty:
            continue
        core_path = root / "data" / site / "out" / "panel_day_core.csv"
        core_df = read_csv(core_path)
        required_core = ["date", "panel_id", "mid_ratio", "last_ratio", "mid_v_ratio", "mid_i_ratio", "v_drop", "v_ref_ok", "coverage_mid", "shadow_like", "group_off_like"]
        missing_core = [col for col in required_core if col not in core_df.columns]
        if missing_core:
            raise SystemExit(f"{core_path} missing columns: {missing_core}")
        core_df = core_df.copy()
        core_df["panel_id"] = core_df["panel_id"].map(normalize_text)
        core_df["date_dt"] = pd.to_datetime(core_df["date"], errors="coerce")

        for case in site_cases.itertuples(index=False):
            strict_trigger_date = pd.to_datetime(case.strict_trigger_date, errors="coerce")
            panel_window = core_df.loc[
                core_df["panel_id"].eq(case.panel_id)
                & core_df["date_dt"].between(strict_trigger_date - pd.Timedelta(days=7), strict_trigger_date + pd.Timedelta(days=7), inclusive="both")
            ].copy()
            if panel_window.empty:
                continue
            anchor = select_anchor(panel_window, strict_trigger_date)
            phenotype, confidence, reason = classify(anchor)
            vendor_row = None
            if (case.site, case.panel_id) in vendor_lookup.index:
                vendor_row = vendor_lookup.loc[(case.site, case.panel_id)]
                if isinstance(vendor_row, pd.DataFrame):
                    vendor_row = vendor_row.iloc[0]

            rows.append(
                {
                    "site": case.site,
                    "panel_id": case.panel_id,
                    "strict_trigger_date": normalize_text(case.strict_trigger_date),
                    "anchor_date": anchor["date_dt"].date().isoformat() if pd.notna(anchor["date_dt"]) else normalize_text(anchor.get("date")),
                    "vendor_reply_class": normalize_text("" if vendor_row is None else vendor_row.get("vendor_reply_class", "")),
                    "vendor_fault_family": normalize_text("" if vendor_row is None else vendor_row.get("vendor_fault_family", "")),
                    "mid_ratio": pd.to_numeric(anchor.get("mid_ratio"), errors="coerce"),
                    "last_ratio": pd.to_numeric(anchor.get("last_ratio"), errors="coerce"),
                    "mid_v_ratio": pd.to_numeric(anchor.get("mid_v_ratio"), errors="coerce"),
                    "mid_i_ratio": pd.to_numeric(anchor.get("mid_i_ratio"), errors="coerce"),
                    "v_drop": pd.to_numeric(anchor.get("v_drop"), errors="coerce"),
                    "v_ref_ok": int(to_bool(anchor.get("v_ref_ok"))),
                    "coverage_mid": pd.to_numeric(anchor.get("coverage_mid"), errors="coerce"),
                    "shadow_like": int(to_bool(anchor.get("shadow_like"))),
                    "group_off_like": int(to_bool(anchor.get("group_off_like"))),
                    "critical_phenotype": phenotype,
                    "phenotype_confidence": confidence,
                    "phenotype_reason": reason,
                }
            )

    return pd.DataFrame(rows, columns=OUTPUT_COLS)


def build_summary(rows_df: pd.DataFrame, sites: list[str]) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for site in sites:
        subset = rows_df.loc[rows_df["site"].eq(site)]
        records.append(
            {
                "site": site,
                "total_critical_cases": int(len(subset)),
                "count_diode_or_module_damage_like": int(subset["critical_phenotype"].eq("diode_or_module_damage_like").sum()),
                "count_open_or_device_issue_like": int(subset["critical_phenotype"].eq("open_or_device_issue_like").sum()),
                "count_group_or_inverter_side_like": int(subset["critical_phenotype"].eq("group_or_inverter_side_like").sum()),
                "count_weak_critical_candidate": int(subset["critical_phenotype"].eq("weak_critical_candidate").sum()),
            }
        )
    return pd.DataFrame(records, columns=SUMMARY_COLS)


def build_vendor_matrix(rows_df: pd.DataFrame) -> pd.DataFrame:
    if rows_df.empty:
        return pd.DataFrame(columns=VENDOR_MATRIX_COLS)
    matrix = (
        rows_df.groupby(
            ["site", "critical_phenotype", "vendor_reply_class", "vendor_fault_family"],
            dropna=False,
        )
        .size()
        .reset_index(name="row_count")
    )
    return matrix.loc[:, VENDOR_MATRIX_COLS]


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    sites = list(args.sites)

    rows_df = build_rows(root, sites)
    summary_df = build_summary(rows_df, sites)
    vendor_matrix_df = build_vendor_matrix(rows_df)

    rows_df.to_csv(share_dir / "critical_phenotype_shadow_latest.csv", index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / "critical_phenotype_shadow_summary.csv", index=False, encoding="utf-8-sig")
    vendor_matrix_df.to_csv(share_dir / "critical_phenotype_vendor_matrix.csv", index=False, encoding="utf-8-sig")

    print(f"critical_shadow_rows={len(rows_df)}")


if __name__ == "__main__":
    main()
