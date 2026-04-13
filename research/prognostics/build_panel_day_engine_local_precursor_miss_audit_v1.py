#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
CASE_KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
SHADOW_KEY_COLS = ["site", "panel_id", "date"]
DEFAULT_WINDOW_DAYS = 30
SIGNAL_METRIC_COLS = ["recon_error", "dtw_dist", "hs_score"]
SUMMARY_OUTPUT_COLS = [
    "record_type",
    "site",
    "miss_case_count",
    "no_obvious_persisted_signal_count",
    "raw_signal_present_but_no_alert_count",
    "confounded_signal_window_count",
    "stale_alert_only_count",
    "any_raw_signal_day_case_count",
    "confounded_case_count",
]
CASE_OUTPUT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "fault_start_date",
    "window_day_count",
    "max_recon_error",
    "max_dtw_dist",
    "max_hs_score",
    "min_mid_ratio",
    "min_mid_v_ratio",
    "min_mid_i_ratio",
    "max_v_drop",
    "any_group_off_like_flag",
    "any_shadow_like_flag",
    "stale_any_prior_alert_flag",
    "stale_best_alert_source",
    "stale_best_alert_lead_days",
    "any_raw_signal_day_flag",
    "strongest_signal_date",
    "strongest_signal_reason_ko",
    "miss_reason_class",
    "miss_reason_ko",
]
WINDOW_OUTPUT_COLS = [
    "site",
    "panel_id",
    "date",
    "recon_error",
    "dtw_dist",
    "hs_score",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "v_drop",
    "group_off_like",
    "shadow_like",
    "raw_signal_day_flag",
]
REQUIRED_SHADOW_COLS = [
    "site",
    "panel_id",
    "date",
    "recon_error",
    "dtw_dist",
    "hs_score",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "v_drop",
    "final_fault",
    "group_off_like",
    "shadow_like",
]
REQUIRED_CASE_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "fault_start_date",
    "any_local_precursor_bounded_hit_flag",
    "stale_any_prior_alert_flag",
    "stale_best_alert_source",
    "stale_best_alert_lead_days",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit why panel_day_engine bounded local precursor misses occur in the true-positive local fault cohort."
    )
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
        help="Sites to include. Defaults to the stable known sites.",
    )
    parser.add_argument(
        "--window-days",
        type=int,
        default=DEFAULT_WINDOW_DAYS,
        help="Bounded precursor miss audit window in days. Defaults to 30.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def normalize_date(value: object) -> str:
    text = normalize_text(value)
    return text[:10] if len(text) >= 10 else text


def parse_date(value: object) -> pd.Timestamp | pd.NaT:
    text = normalize_date(value)
    if not text:
        return pd.NaT
    return pd.to_datetime(text, errors="coerce")


def to_int_flag(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return 1
    if text in {"0", "false", "f", "no", "n", ""}:
        return 0
    try:
        return 1 if float(text) > 0 else 0
    except ValueError:
        return 0


def to_float(value: object) -> float | pd.NA:
    numeric = pd.to_numeric([value], errors="coerce")[0]
    if pd.isna(numeric):
        return pd.NA
    return float(numeric)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def dedupe_by_keys(df: pd.DataFrame, name: str, cols: list[str]) -> pd.DataFrame:
    dupes = df.loc[df.duplicated(subset=cols, keep=False), cols]
    if not dupes.empty:
        raise SystemExit(f"{name} has duplicate rows on {cols}")
    return df


def max_or_blank(series: pd.Series) -> object:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return pd.NA
    return float(numeric.max())


def min_or_blank(series: pd.Series) -> object:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return pd.NA
    return float(numeric.min())


def load_shadow(root: Path, sites: list[str]) -> pd.DataFrame:
    shadow = read_csv(root / "_share" / "panel_day_engine_local_precursor_shadow_v1.csv")
    ensure_columns(shadow, REQUIRED_SHADOW_COLS, "panel_day_engine_local_precursor_shadow_v1.csv")
    shadow = shadow.copy()
    shadow["site"] = shadow["site"].map(normalize_text)
    shadow["panel_id"] = shadow["panel_id"].map(normalize_text)
    shadow["date"] = shadow["date"].map(normalize_date)
    shadow = shadow.loc[shadow["site"].isin(sites)].copy()
    shadow = dedupe_by_keys(shadow, "panel_day_engine_local_precursor_shadow_v1.csv", SHADOW_KEY_COLS)
    shadow["date_ts"] = shadow["date"].map(parse_date)
    for col in SIGNAL_METRIC_COLS + ["mid_ratio", "mid_v_ratio", "mid_i_ratio", "v_drop"]:
        shadow[col] = pd.to_numeric(shadow[col], errors="coerce")
    for col in ["final_fault", "group_off_like", "shadow_like"]:
        shadow[col] = shadow[col].map(to_int_flag).astype(int)
    return shadow


def load_miss_cases(root: Path, sites: list[str]) -> pd.DataFrame:
    cases = read_csv(root / "_share" / "panel_day_engine_local_precursor_cohort_cases_v1.csv")
    ensure_columns(cases, REQUIRED_CASE_COLS, "panel_day_engine_local_precursor_cohort_cases_v1.csv")
    cases = cases.copy()
    for col in ["site", "panel_id", "stale_best_alert_source"]:
        cases[col] = cases[col].map(normalize_text)
    for col in ["strict_trigger_date", "fault_start_date"]:
        cases[col] = cases[col].map(normalize_date)
    for col in [
        "any_local_precursor_bounded_hit_flag",
        "stale_any_prior_alert_flag",
    ]:
        cases[col] = cases[col].map(to_int_flag).astype(int)
    cases["stale_best_alert_lead_days"] = pd.to_numeric(cases["stale_best_alert_lead_days"], errors="coerce")
    cases = cases.loc[
        cases["site"].isin(sites) & cases["any_local_precursor_bounded_hit_flag"].eq(0)
    ].copy()
    cases = dedupe_by_keys(cases, "panel_day_engine_local_precursor_cohort_cases_v1.csv", CASE_KEY_COLS)
    return cases


def build_site_p90s(shadow_df: pd.DataFrame) -> dict[str, dict[str, float | pd.NA]]:
    p90s: dict[str, dict[str, float | pd.NA]] = {}
    non_final = shadow_df.loc[shadow_df["final_fault"].eq(0)].copy()
    for site, group in non_final.groupby("site", sort=False):
        p90s[site] = {}
        for col in SIGNAL_METRIC_COLS:
            numeric = pd.to_numeric(group[col], errors="coerce").dropna()
            if numeric.empty:
                p90s[site][col] = pd.NA
            else:
                p90s[site][col] = float(numeric.quantile(0.9))
    return p90s


def compute_signal_flags(row: pd.Series, thresholds: dict[str, float | pd.NA]) -> dict[str, bool]:
    recon_high = pd.notna(row["recon_error"]) and pd.notna(thresholds["recon_error"]) and row["recon_error"] >= thresholds["recon_error"]
    dtw_high = pd.notna(row["dtw_dist"]) and pd.notna(thresholds["dtw_dist"]) and row["dtw_dist"] >= thresholds["dtw_dist"]
    hs_high = pd.notna(row["hs_score"]) and pd.notna(thresholds["hs_score"]) and row["hs_score"] >= thresholds["hs_score"]
    mid_v_low = pd.notna(row["mid_v_ratio"]) and row["mid_v_ratio"] <= 0.85
    mid_i_low = pd.notna(row["mid_i_ratio"]) and row["mid_i_ratio"] <= 0.85
    v_drop_high = pd.notna(row["v_drop"]) and row["v_drop"] >= 0.20
    return {
        "recon_high": bool(recon_high),
        "dtw_high": bool(dtw_high),
        "hs_high": bool(hs_high),
        "mid_v_low": bool(mid_v_low),
        "mid_i_low": bool(mid_i_low),
        "v_drop_high": bool(v_drop_high),
    }


def signal_reason_ko(row: pd.Series) -> str:
    if int(row.get("raw_signal_day_flag", 0)) == 0:
        return "가시 persisted 신호 없음"
    shape_like = int(row["recon_high"]) + int(row["dtw_high"]) + int(row["hs_high"])
    electrical_like = int(row["mid_v_low"]) + int(row["mid_i_low"]) + int(row["v_drop_high"])
    confounded = int(row.get("group_off_like", 0)) == 1 or int(row.get("shadow_like", 0)) == 1
    if confounded:
        return "confound 동반 신호"
    if shape_like > 0 and electrical_like > 0:
        return "형상·거리계+전기 신호"
    if electrical_like > 0:
        return "전기적 드리프트"
    return "형상·거리계 이상 우세"


def miss_reason_ko(reason_class: str) -> str:
    mapping = {
        "no_obvious_persisted_signal": "30일 bounded window에서 persisted raw precursor-like signal이 뚜렷하지 않음",
        "raw_signal_present_but_no_alert": "persisted raw precursor-like signal은 보이나 bounded alert는 생성되지 않음",
        "confounded_signal_window": "persisted raw signal은 있으나 group_off/shadow confound가 함께 나타남",
        "stale_alert_only": "bounded window에는 가시 신호가 없고 오래된 historical alert만 남아 있음",
    }
    return mapping[reason_class]


def classify_miss_reason(
    stale_any_prior_alert_flag: int,
    any_raw_signal_day_flag: int,
    any_group_off_like_flag: int,
    any_shadow_like_flag: int,
) -> str:
    if stale_any_prior_alert_flag == 1 and any_raw_signal_day_flag == 0:
        return "stale_alert_only"
    if any_raw_signal_day_flag == 1 and (any_group_off_like_flag == 1 or any_shadow_like_flag == 1):
        return "confounded_signal_window"
    if any_raw_signal_day_flag == 1:
        return "raw_signal_present_but_no_alert"
    return "no_obvious_persisted_signal"


def build_case_and_window_outputs(
    miss_cases_df: pd.DataFrame,
    shadow_df: pd.DataFrame,
    site_p90s: dict[str, dict[str, float | pd.NA]],
    window_days: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    case_rows: list[dict[str, object]] = []
    window_rows: list[dict[str, object]] = []
    shadow_lookup = {
        (site, panel_id): group.sort_values("date_ts").copy()
        for (site, panel_id), group in shadow_df.groupby(["site", "panel_id"], sort=False)
    }
    default_thresholds = {col: pd.NA for col in SIGNAL_METRIC_COLS}

    for case in miss_cases_df.itertuples(index=False):
        fault_start_ts = parse_date(case.fault_start_date)
        if pd.isna(fault_start_ts):
            raise SystemExit(f"invalid fault_start_date for case: {case.site}|{case.panel_id}|{case.fault_start_date}")
        panel_shadow = shadow_lookup.get((case.site, case.panel_id), pd.DataFrame(columns=shadow_df.columns)).copy()
        window_start_ts = fault_start_ts - pd.Timedelta(days=window_days)
        window_df = panel_shadow.loc[
            panel_shadow["date_ts"].ge(window_start_ts) & panel_shadow["date_ts"].lt(fault_start_ts)
        ].copy()
        thresholds = site_p90s.get(case.site, default_thresholds)

        if not window_df.empty:
            signal_flag_df = window_df.apply(lambda row: pd.Series(compute_signal_flags(row, thresholds)), axis=1)
            window_df = pd.concat([window_df.reset_index(drop=True), signal_flag_df.reset_index(drop=True)], axis=1)
            signal_cols = [
                "recon_high",
                "dtw_high",
                "hs_high",
                "mid_v_low",
                "mid_i_low",
                "v_drop_high",
            ]
            window_df["signal_condition_count"] = window_df.loc[:, signal_cols].sum(axis=1).astype(int)
            window_df["raw_signal_day_flag"] = window_df["signal_condition_count"].gt(0).astype(int)
            window_df["strongest_signal_reason_ko"] = window_df.apply(signal_reason_ko, axis=1)
        else:
            window_df = window_df.copy()
            for col in [
                "recon_high",
                "dtw_high",
                "hs_high",
                "mid_v_low",
                "mid_i_low",
                "v_drop_high",
                "signal_condition_count",
                "raw_signal_day_flag",
                "strongest_signal_reason_ko",
            ]:
                window_df[col] = pd.Series(dtype="object")

        any_raw_signal_day_flag = int(window_df["raw_signal_day_flag"].max()) if not window_df.empty else 0
        any_group_off_like_flag = int(window_df["group_off_like"].max()) if not window_df.empty else 0
        any_shadow_like_flag = int(window_df["shadow_like"].max()) if not window_df.empty else 0

        raw_signal_days = window_df.loc[window_df["raw_signal_day_flag"].eq(1)].copy()
        if not raw_signal_days.empty:
            strongest_row = raw_signal_days.sort_values(
                by=["signal_condition_count", "date_ts"],
                ascending=[False, True],
            ).iloc[0]
            strongest_signal_date = strongest_row["date"]
            strongest_signal_reason = strongest_row["strongest_signal_reason_ko"]
        else:
            strongest_signal_date = ""
            strongest_signal_reason = "가시 persisted 신호 없음"

        reason_class = classify_miss_reason(
            int(case.stale_any_prior_alert_flag),
            any_raw_signal_day_flag,
            any_group_off_like_flag,
            any_shadow_like_flag,
        )

        case_rows.append(
            {
                "site": case.site,
                "panel_id": case.panel_id,
                "strict_trigger_date": case.strict_trigger_date,
                "fault_start_date": case.fault_start_date,
                "window_day_count": int(len(window_df)),
                "max_recon_error": max_or_blank(window_df["recon_error"]),
                "max_dtw_dist": max_or_blank(window_df["dtw_dist"]),
                "max_hs_score": max_or_blank(window_df["hs_score"]),
                "min_mid_ratio": min_or_blank(window_df["mid_ratio"]),
                "min_mid_v_ratio": min_or_blank(window_df["mid_v_ratio"]),
                "min_mid_i_ratio": min_or_blank(window_df["mid_i_ratio"]),
                "max_v_drop": max_or_blank(window_df["v_drop"]),
                "any_group_off_like_flag": any_group_off_like_flag,
                "any_shadow_like_flag": any_shadow_like_flag,
                "stale_any_prior_alert_flag": int(case.stale_any_prior_alert_flag),
                "stale_best_alert_source": case.stale_best_alert_source,
                "stale_best_alert_lead_days": case.stale_best_alert_lead_days,
                "any_raw_signal_day_flag": any_raw_signal_day_flag,
                "strongest_signal_date": strongest_signal_date,
                "strongest_signal_reason_ko": strongest_signal_reason,
                "miss_reason_class": reason_class,
                "miss_reason_ko": miss_reason_ko(reason_class),
            }
        )

        for row in window_df.itertuples(index=False):
            window_rows.append(
                {
                    "site": row.site,
                    "panel_id": row.panel_id,
                    "date": row.date,
                    "recon_error": row.recon_error,
                    "dtw_dist": row.dtw_dist,
                    "hs_score": row.hs_score,
                    "mid_ratio": row.mid_ratio,
                    "mid_v_ratio": row.mid_v_ratio,
                    "mid_i_ratio": row.mid_i_ratio,
                    "v_drop": row.v_drop,
                    "group_off_like": int(row.group_off_like),
                    "shadow_like": int(row.shadow_like),
                    "raw_signal_day_flag": int(row.raw_signal_day_flag),
                }
            )

    cases_df = pd.DataFrame(case_rows, columns=CASE_OUTPUT_COLS)
    windows_df = pd.DataFrame(window_rows, columns=WINDOW_OUTPUT_COLS)
    return cases_df, windows_df


def build_summary(cases_df: pd.DataFrame, sites: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    groups = [("overall", "", cases_df)] + [
        ("site", site, cases_df.loc[cases_df["site"].eq(site)].copy()) for site in sites
    ]
    for record_type, site, group in groups:
        rows.append(
            {
                "record_type": record_type,
                "site": site,
                "miss_case_count": int(len(group)),
                "no_obvious_persisted_signal_count": int(group["miss_reason_class"].eq("no_obvious_persisted_signal").sum()) if not group.empty else 0,
                "raw_signal_present_but_no_alert_count": int(group["miss_reason_class"].eq("raw_signal_present_but_no_alert").sum()) if not group.empty else 0,
                "confounded_signal_window_count": int(group["miss_reason_class"].eq("confounded_signal_window").sum()) if not group.empty else 0,
                "stale_alert_only_count": int(group["miss_reason_class"].eq("stale_alert_only").sum()) if not group.empty else 0,
                "any_raw_signal_day_case_count": int(group["any_raw_signal_day_flag"].sum()) if not group.empty else 0,
                "confounded_case_count": int(
                    ((group["any_group_off_like_flag"] == 1) | (group["any_shadow_like_flag"] == 1)).sum()
                ) if not group.empty else 0,
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_OUTPUT_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    shadow_df = load_shadow(root, args.sites)
    miss_cases_df = load_miss_cases(root, args.sites)
    site_p90s = build_site_p90s(shadow_df)
    cases_df, windows_df = build_case_and_window_outputs(
        miss_cases_df,
        shadow_df,
        site_p90s,
        args.window_days,
    )
    summary_df = build_summary(cases_df, args.sites)

    summary_df.to_csv(
        share_dir / "panel_day_engine_local_precursor_miss_summary_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    cases_df.to_csv(
        share_dir / "panel_day_engine_local_precursor_miss_cases_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    windows_df.to_csv(
        share_dir / "panel_day_engine_local_precursor_miss_windows_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    main()
