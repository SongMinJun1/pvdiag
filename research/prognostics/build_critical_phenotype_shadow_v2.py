#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
OUTPUT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "anchor_date",
    "vendor_reply_class",
    "vendor_fault_family",
    "valid_days",
    "evidence_days",
    "evidence_ratio",
    "mid_ratio_win_median",
    "mid_v_ratio_win_median",
    "mid_i_ratio_win_median",
    "v_drop_win_median",
    "coverage_mid_win_median",
    "critical_phenotype_v2",
    "phenotype_confidence_v2",
    "shape_support_flag",
    "cluster_guard_flag",
]
SUMMARY_COLS = [
    "site",
    "total_critical_cases",
    "count_electrical_fault_like",
    "count_open_or_device_issue_like",
    "count_group_or_inverter_side_like",
    "count_borderline_electrical_review",
    "count_shape_only_monitor",
    "count_weak_critical_candidate",
]
VENDOR_MATRIX_COLS = [
    "site",
    "critical_phenotype_v2",
    "vendor_reply_class",
    "vendor_fault_family",
    "row_count",
]
VENDOR_COLS = ["site", "panel_id", "vendor_reply_class", "vendor_fault_family"]
ONSET_COLS = ["site", "panel_id", "strict_trigger_date", "reason_summary"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Critical phenotype shadow v2 with window consensus and actionability separation.")
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
    return normalize_text(value).lower() in {"1", "true", "t", "yes", "y"}


def to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def parse_strict_method(reason_summary: str) -> str:
    for part in normalize_text(reason_summary).split("|"):
        if part.startswith("strict_method="):
            return part.split("=", 1)[1]
    return ""


def ensure_vendor_df(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=VENDOR_COLS)
    df = read_csv(path)
    missing = [col for col in VENDOR_COLS if col not in df.columns]
    if missing:
        raise SystemExit(f"vendor adjudication input missing columns: {missing}")
    for col in VENDOR_COLS:
        df[col] = df[col].map(normalize_text)
    return df.loc[:, VENDOR_COLS].copy()


def add_site_day_percentiles(core_df: pd.DataFrame) -> pd.DataFrame:
    df = core_df.copy()
    if "recon_error" in df.columns:
        df["recon_error_day_pct"] = df.groupby("date_dt", dropna=False)["recon_error"].rank(pct=True, method="average")
    else:
        df["recon_error_day_pct"] = float("nan")
    if "dtw_dist" in df.columns:
        df["dtw_dist_day_pct"] = df.groupby("date_dt", dropna=False)["dtw_dist"].rank(pct=True, method="average")
    else:
        df["dtw_dist_day_pct"] = float("nan")
    return df


def valid_day_mask(window_df: pd.DataFrame) -> pd.Series:
    return (
        window_df["v_ref_ok_bool"]
        & window_df["coverage_mid_num"].ge(0.85)
        & (~window_df["shadow_like_bool"])
        & (~window_df["group_off_like_bool"])
    )


def diode_evidence_mask(window_df: pd.DataFrame) -> pd.Series:
    return (
        window_df["mid_v_ratio_num"].le(0.75)
        & window_df["v_drop_num"].ge(0.28)
        & window_df["mid_i_ratio_num"].ge(0.85)
    )


def representative_anchor(window_df: pd.DataFrame, strict_trigger_date: pd.Timestamp) -> str:
    ranked = window_df.copy()
    ranked["distance_days"] = (ranked["date_dt"] - strict_trigger_date).abs().dt.days
    ranked = ranked.sort_values(
        ["v_drop_num", "mid_v_ratio_num", "distance_days", "date_dt"],
        ascending=[False, True, True, True],
        kind="stable",
    )
    anchor = ranked.iloc[0]
    return anchor["date_dt"].date().isoformat()


def classify_window(window_df: pd.DataFrame) -> tuple[str, str, int, int, float, float, float, float, float, float, int]:
    valid_mask = valid_day_mask(window_df)
    evidence_mask = valid_mask & diode_evidence_mask(window_df)
    valid_days = int(valid_mask.sum())
    evidence_days = int(evidence_mask.sum())
    evidence_ratio = round(float(evidence_days / valid_days), 6) if valid_days > 0 else 0.0

    mid_ratio_med = float(window_df["mid_ratio_num"].median()) if window_df["mid_ratio_num"].notna().any() else float("nan")
    mid_v_ratio_med = float(window_df["mid_v_ratio_num"].median()) if window_df["mid_v_ratio_num"].notna().any() else float("nan")
    mid_i_ratio_med = float(window_df["mid_i_ratio_num"].median()) if window_df["mid_i_ratio_num"].notna().any() else float("nan")
    v_drop_med = float(window_df["v_drop_num"].median()) if window_df["v_drop_num"].notna().any() else float("nan")
    coverage_mid_med = float(window_df["coverage_mid_num"].median()) if window_df["coverage_mid_num"].notna().any() else float("nan")

    shape_support_flag = int(
        (window_df["recon_error_day_pct"].max(skipna=True) >= 0.85)
        or (window_df["dtw_dist_day_pct"].max(skipna=True) >= 0.85)
    )

    phenotype = "weak_critical_candidate"
    confidence = "low"

    if (
        pd.notna(mid_ratio_med)
        and pd.notna(mid_v_ratio_med)
        and pd.notna(v_drop_med)
        and mid_ratio_med <= 0.10
        and mid_v_ratio_med <= 0.10
        and v_drop_med >= 0.90
    ):
        phenotype = "open_or_device_issue_like"
        confidence = "high"
    elif (
        pd.notna(mid_ratio_med)
        and pd.notna(mid_i_ratio_med)
        and pd.notna(mid_v_ratio_med)
        and mid_ratio_med <= 0.10
        and mid_i_ratio_med <= 0.10
        and mid_v_ratio_med >= 1.05
    ):
        phenotype = "group_or_inverter_side_like"
        confidence = "high"
    elif (
        valid_days >= 5
        and evidence_days >= 4
        and evidence_ratio >= 0.60
        and pd.notna(mid_v_ratio_med)
        and pd.notna(v_drop_med)
        and pd.notna(mid_i_ratio_med)
        and pd.notna(coverage_mid_med)
        and mid_v_ratio_med <= 0.72
        and v_drop_med >= 0.30
        and mid_i_ratio_med >= 0.90
        and coverage_mid_med >= 0.85
    ):
        phenotype = "electrical_fault_like"
        confidence = "high"
    elif valid_days >= 5 and evidence_days >= 4:
        phenotype = "borderline_electrical_review"
        confidence = "medium"
    elif shape_support_flag == 1:
        phenotype = "shape_only_monitor"
        confidence = "medium"

    return (
        phenotype,
        confidence,
        valid_days,
        evidence_days,
        evidence_ratio,
        round(mid_ratio_med, 6) if pd.notna(mid_ratio_med) else float("nan"),
        round(mid_v_ratio_med, 6) if pd.notna(mid_v_ratio_med) else float("nan"),
        round(mid_i_ratio_med, 6) if pd.notna(mid_i_ratio_med) else float("nan"),
        round(v_drop_med, 6) if pd.notna(v_drop_med) else float("nan"),
        round(coverage_mid_med, 6) if pd.notna(coverage_mid_med) else float("nan"),
        shape_support_flag,
    )


def build_rows(root: Path, sites: list[str]) -> pd.DataFrame:
    onset_df = read_csv(root / "_share" / "panel_onset_shadow_latest.csv")
    vendor_df = ensure_vendor_df(root / "_share" / "vendor_reply_adjudication_latest.csv")
    onset_df = onset_df.copy()
    missing_onset = [col for col in ONSET_COLS if col not in onset_df.columns]
    if missing_onset:
        raise SystemExit(f"panel_onset_shadow_latest.csv missing columns: {missing_onset}")
    onset_df["site"] = onset_df["site"].map(normalize_text)
    onset_df["panel_id"] = onset_df["panel_id"].map(normalize_text)
    onset_df["strict_method"] = onset_df["reason_summary"].map(parse_strict_method)
    onset_df = onset_df.loc[
        onset_df["site"].isin(sites) & onset_df["strict_method"].eq("critical_fault_flag")
    ].copy()

    vendor_lookup = vendor_df.set_index(["site", "panel_id"], drop=False) if not vendor_df.empty else pd.DataFrame(columns=VENDOR_COLS).set_index(["site", "panel_id"], drop=False)
    rows: list[dict[str, object]] = []

    for site in sites:
        site_cases = onset_df.loc[onset_df["site"].eq(site)]
        if site_cases.empty:
            continue
        core_df = read_csv(root / "data" / site / "out" / "panel_day_core.csv")
        required_core = ["date", "panel_id", "mid_ratio", "mid_v_ratio", "mid_i_ratio", "v_drop", "coverage_mid", "shadow_like", "group_off_like", "v_ref_ok", "recon_error", "dtw_dist"]
        missing_core = [col for col in required_core if col not in core_df.columns]
        if missing_core:
            raise SystemExit(f"data/{site}/out/panel_day_core.csv missing columns: {missing_core}")
        core_df = core_df.copy()
        core_df["site"] = site
        core_df["panel_id"] = core_df["panel_id"].map(normalize_text)
        core_df["date_dt"] = pd.to_datetime(core_df["date"], errors="coerce")
        core_df["mid_ratio_num"] = to_numeric(core_df["mid_ratio"])
        core_df["last_ratio_num"] = to_numeric(core_df["last_ratio"]) if "last_ratio" in core_df.columns else float("nan")
        core_df["mid_v_ratio_num"] = to_numeric(core_df["mid_v_ratio"])
        core_df["mid_i_ratio_num"] = to_numeric(core_df["mid_i_ratio"])
        core_df["v_drop_num"] = to_numeric(core_df["v_drop"])
        core_df["coverage_mid_num"] = to_numeric(core_df["coverage_mid"])
        core_df["recon_error"] = to_numeric(core_df["recon_error"])
        core_df["dtw_dist"] = to_numeric(core_df["dtw_dist"])
        core_df["v_ref_ok_bool"] = core_df["v_ref_ok"].map(to_bool)
        core_df["shadow_like_bool"] = core_df["shadow_like"].map(to_bool)
        core_df["group_off_like_bool"] = core_df["group_off_like"].map(to_bool)
        core_df = add_site_day_percentiles(core_df)
        core_df["valid_day"] = valid_day_mask(core_df)
        core_df["diode_evidence_day"] = core_df["valid_day"] & diode_evidence_mask(core_df)
        daily_prevalence = core_df.groupby("date_dt", dropna=False)["diode_evidence_day"].mean().to_dict()

        for case in site_cases.itertuples(index=False):
            strict_trigger_date = pd.to_datetime(case.strict_trigger_date, errors="coerce")
            window_df = core_df.loc[
                core_df["panel_id"].eq(case.panel_id)
                & core_df["date_dt"].between(strict_trigger_date - pd.Timedelta(days=7), strict_trigger_date + pd.Timedelta(days=7), inclusive="both")
            ].copy()
            if window_df.empty:
                continue

            (
                phenotype,
                confidence,
                valid_days,
                evidence_days,
                evidence_ratio,
                mid_ratio_med,
                mid_v_ratio_med,
                mid_i_ratio_med,
                v_drop_med,
                coverage_mid_med,
                shape_support_flag,
            ) = classify_window(window_df)
            anchor_date = representative_anchor(window_df, strict_trigger_date)
            anchor_dt = pd.to_datetime(anchor_date, errors="coerce")
            cluster_guard_flag = int(float(daily_prevalence.get(anchor_dt, 0.0)) > 0.05) if pd.notna(anchor_dt) else 0

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
                    "anchor_date": anchor_date,
                    "vendor_reply_class": normalize_text("" if vendor_row is None else vendor_row.get("vendor_reply_class", "")),
                    "vendor_fault_family": normalize_text("" if vendor_row is None else vendor_row.get("vendor_fault_family", "")),
                    "valid_days": valid_days,
                    "evidence_days": evidence_days,
                    "evidence_ratio": evidence_ratio,
                    "mid_ratio_win_median": mid_ratio_med,
                    "mid_v_ratio_win_median": mid_v_ratio_med,
                    "mid_i_ratio_win_median": mid_i_ratio_med,
                    "v_drop_win_median": v_drop_med,
                    "coverage_mid_win_median": coverage_mid_med,
                    "critical_phenotype_v2": phenotype,
                    "phenotype_confidence_v2": confidence,
                    "shape_support_flag": shape_support_flag,
                    "cluster_guard_flag": cluster_guard_flag,
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
                "count_electrical_fault_like": int(subset["critical_phenotype_v2"].eq("electrical_fault_like").sum()),
                "count_open_or_device_issue_like": int(subset["critical_phenotype_v2"].eq("open_or_device_issue_like").sum()),
                "count_group_or_inverter_side_like": int(subset["critical_phenotype_v2"].eq("group_or_inverter_side_like").sum()),
                "count_borderline_electrical_review": int(subset["critical_phenotype_v2"].eq("borderline_electrical_review").sum()),
                "count_shape_only_monitor": int(subset["critical_phenotype_v2"].eq("shape_only_monitor").sum()),
                "count_weak_critical_candidate": int(subset["critical_phenotype_v2"].eq("weak_critical_candidate").sum()),
            }
        )
    return pd.DataFrame(records, columns=SUMMARY_COLS)


def build_vendor_matrix(rows_df: pd.DataFrame) -> pd.DataFrame:
    if rows_df.empty:
        return pd.DataFrame(columns=VENDOR_MATRIX_COLS)
    matrix = (
        rows_df.groupby(
            ["site", "critical_phenotype_v2", "vendor_reply_class", "vendor_fault_family"],
            dropna=False,
        )
        .size()
        .reset_index(name="row_count")
        .rename(columns={"critical_phenotype_v2": "critical_phenotype_v2"})
    )
    return matrix.loc[:, VENDOR_MATRIX_COLS]


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    sites = list(args.sites)
    share_dir = root / "_share"

    rows_df = build_rows(root, sites)
    summary_df = build_summary(rows_df, sites)
    vendor_matrix_df = build_vendor_matrix(rows_df)

    rows_df.to_csv(share_dir / "critical_phenotype_shadow_v2_latest.csv", index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / "critical_phenotype_shadow_v2_summary.csv", index=False, encoding="utf-8-sig")
    vendor_matrix_df.to_csv(share_dir / "critical_phenotype_shadow_v2_vendor_matrix.csv", index=False, encoding="utf-8-sig")

    print(f"critical_shadow_v2_rows={len(rows_df)}")


if __name__ == "__main__":
    main()
