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
ALERT_PRIORITY = {
    "prefault_B": 0,
    "pre_alarm": 1,
    "ews_warning": 2,
}
CASE_OUTPUT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "fault_start_date",
    "fault_start_source",
    "vendor_fault_family",
    "bounded_raw_signal_day_count",
    "earliest_bounded_raw_signal_date",
    "earliest_bounded_raw_signal_lead_days",
    "first_ews_warning_date_bounded",
    "first_prefault_B_date_bounded",
    "first_pre_alarm_date_bounded",
    "ews_warning_bounded_hit_flag",
    "prefault_B_bounded_hit_flag",
    "pre_alarm_bounded_hit_flag",
    "any_local_precursor_bounded_hit_flag",
    "best_alert_source",
    "best_alert_lead_days",
    "temporality_class",
    "precursor_eligible_flag",
    "temporality_reason_ko",
]
SUMMARY_OUTPUT_COLS = [
    "record_type",
    "site",
    "cohort_case_count",
    "progressive_local_precursor_expected_count",
    "abrupt_local_precursor_unexpected_count",
    "unknown_local_temporality_count",
    "precursor_eligible_case_count",
    "precursor_eligible_hit_case_count",
    "precursor_eligible_hit_rate",
    "ews_warning_eligible_hit_case_count",
    "ews_warning_eligible_hit_rate",
    "prefault_B_eligible_hit_case_count",
    "prefault_B_eligible_hit_rate",
    "pre_alarm_eligible_hit_case_count",
    "pre_alarm_eligible_hit_rate",
    "median_best_alert_lead_days_on_eligible",
    "noneligible_case_count",
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
    "ews_warning_flag",
    "prefault_B_flag",
    "pre_alarm_flag",
]
REQUIRED_COHORT_CASE_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
]
REQUIRED_REAUDIT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify local-fault cases into precursor-eligible vs abrupt/unknown temporality before evaluating panel_day_engine local precursor hits."
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
        help="Bounded precursor inspection window in days. Defaults to 30.",
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


def safe_div(numer: int | float, denom: int | float) -> float:
    if denom <= 0:
        return 0.0
    return round(float(numer / denom), 6)


def median_or_blank(series: pd.Series) -> object:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return pd.NA
    return round(float(numeric.median()), 6)


def first_nonblank(*values: object) -> str:
    for value in values:
        text = normalize_text(value)
        if text:
            return text
    return ""


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
    for col in ["final_fault", "ews_warning_flag", "prefault_B_flag", "pre_alarm_flag"]:
        shadow[col] = shadow[col].map(to_int_flag).astype(int)
    return shadow


def load_cohort_cases(root: Path, sites: list[str]) -> pd.DataFrame:
    cases = read_csv(root / "_share" / "panel_day_engine_local_precursor_cohort_cases_v1.csv")
    ensure_columns(cases, REQUIRED_COHORT_CASE_COLS, "panel_day_engine_local_precursor_cohort_cases_v1.csv")
    cases = cases.copy()
    for col in ["site", "panel_id", "fault_start_source", "candidate_validity", "vendor_fault_family"]:
        if col not in cases.columns:
            cases[col] = ""
        cases[col] = cases[col].map(normalize_text)
    for col in ["strict_trigger_date", "fault_start_date"]:
        if col not in cases.columns:
            cases[col] = ""
        cases[col] = cases[col].map(normalize_date)
    cases = cases.loc[cases["site"].isin(sites)].copy()
    cases = dedupe_by_keys(cases, "panel_day_engine_local_precursor_cohort_cases_v1.csv", CASE_KEY_COLS)
    return cases


def load_positive_reaudit(root: Path, sites: list[str]) -> pd.DataFrame:
    reaudit = read_csv(root / "_share" / "panel_date_reaudit_working.csv")
    ensure_columns(reaudit, REQUIRED_REAUDIT_COLS, "panel_date_reaudit_working.csv")
    reaudit = reaudit.copy()
    for col in ["site", "panel_id", "candidate_validity", "vendor_fault_family"]:
        if col not in reaudit.columns:
            reaudit[col] = ""
        reaudit[col] = reaudit[col].map(normalize_text)
    reaudit["strict_trigger_date"] = reaudit["strict_trigger_date"].map(normalize_date)
    reaudit = reaudit.loc[
        reaudit["site"].isin(sites) & reaudit["candidate_validity"].eq("true_positive")
    ].copy()
    reaudit = dedupe_by_keys(reaudit, "panel_date_reaudit_working.csv", CASE_KEY_COLS)
    return reaudit.loc[:, [*CASE_KEY_COLS, "candidate_validity", "vendor_fault_family"]].copy()


def load_vendor_context(root: Path, sites: list[str]) -> pd.DataFrame:
    path = root / "_share" / "vendor_reply_adjudication_latest.csv"
    if not path.exists():
        return pd.DataFrame(columns=[*CASE_KEY_COLS, "vendor_fault_family_vendor"])
    vendor = read_csv(path)
    required = ["site", "panel_id", "strict_trigger_date", "vendor_fault_family"]
    ensure_columns(vendor, required, "vendor_reply_adjudication_latest.csv")
    vendor = vendor.copy()
    vendor["site"] = vendor["site"].map(normalize_text)
    vendor["panel_id"] = vendor["panel_id"].map(normalize_text)
    vendor["strict_trigger_date"] = vendor["strict_trigger_date"].map(normalize_date)
    vendor["vendor_fault_family"] = vendor["vendor_fault_family"].map(normalize_text)
    vendor = vendor.loc[vendor["site"].isin(sites)].copy()
    vendor = dedupe_by_keys(vendor.loc[:, required], "vendor_reply_adjudication_latest.csv", CASE_KEY_COLS)
    return vendor.rename(columns={"vendor_fault_family": "vendor_fault_family_vendor"})


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


def nearest_bounded_date(
    panel_df: pd.DataFrame,
    flag_col: str,
    fault_start_date: pd.Timestamp,
    lookback_days: int,
) -> pd.Timestamp | pd.NaT:
    lower_bound = fault_start_date - pd.Timedelta(days=lookback_days)
    matches = panel_df.loc[
        panel_df[flag_col].eq(1)
        & panel_df["date_ts"].lt(fault_start_date)
        & panel_df["date_ts"].ge(lower_bound),
        "date_ts",
    ].dropna()
    if matches.empty:
        return pd.NaT
    return matches.max()


def earliest_bounded_alert_from_raw(
    panel_df: pd.DataFrame,
    fault_start_date: pd.Timestamp,
    lookback_days: int,
) -> tuple[str, pd.Timestamp | pd.NaT]:
    lower_bound = fault_start_date - pd.Timedelta(days=lookback_days)
    bounded_rows = panel_df.loc[
        panel_df["date_ts"].lt(fault_start_date) & panel_df["date_ts"].ge(lower_bound)
    ].copy()
    choices: list[tuple[pd.Timestamp, int, str]] = []
    for source, col in [
        ("prefault_B", "prefault_B_flag"),
        ("pre_alarm", "pre_alarm_flag"),
        ("ews_warning", "ews_warning_flag"),
    ]:
        matched = bounded_rows.loc[bounded_rows[col].eq(1), "date_ts"].dropna()
        for ts in matched.tolist():
            choices.append((ts, ALERT_PRIORITY[source], source))
    if not choices:
        return "none", pd.NaT
    choices.sort(key=lambda item: (item[0], item[1]))
    return choices[0][2], choices[0][0]


def derive_fault_anchor(
    case: pd.Series,
    panel_shadow: pd.DataFrame,
    window_days: int,
) -> tuple[pd.Timestamp, str]:
    reused_fault_start = parse_date(case.get("fault_start_date", ""))
    reused_fault_source = normalize_text(case.get("fault_start_source", ""))
    if pd.notna(reused_fault_start):
        return reused_fault_start, reused_fault_source or "cohort_audit_reused"

    strict_trigger_ts = parse_date(case["strict_trigger_date"])
    if pd.isna(strict_trigger_ts):
        raise SystemExit(f"invalid strict_trigger_date: {case['site']}|{case['panel_id']}|{case['strict_trigger_date']}")

    final_fault_dates = panel_shadow.loc[
        panel_shadow["final_fault"].eq(1)
        & panel_shadow["date_ts"].ge(strict_trigger_ts - pd.Timedelta(days=window_days))
        & panel_shadow["date_ts"].le(strict_trigger_ts + pd.Timedelta(days=window_days)),
        "date_ts",
    ].dropna()
    if not final_fault_dates.empty:
        return final_fault_dates.min(), "final_fault_first_true_recomputed"
    return strict_trigger_ts, "strict_trigger_fallback_recomputed"


def classify_temporality(
    bounded_raw_signal_day_count: int,
    earliest_bounded_raw_signal_lead_days: object,
    final_zone_df: pd.DataFrame,
) -> tuple[str, int, str]:
    final_zone_min_mid_ratio = pd.to_numeric(final_zone_df["mid_ratio"], errors="coerce").min() if not final_zone_df.empty else pd.NA
    final_zone_min_mid_v_ratio = pd.to_numeric(final_zone_df["mid_v_ratio"], errors="coerce").min() if not final_zone_df.empty else pd.NA
    final_zone_max_v_drop = pd.to_numeric(final_zone_df["v_drop"], errors="coerce").max() if not final_zone_df.empty else pd.NA
    abrupt_collapse = (
        pd.notna(final_zone_min_mid_ratio)
        and pd.notna(final_zone_min_mid_v_ratio)
        and pd.notna(final_zone_max_v_drop)
        and float(final_zone_min_mid_ratio) <= 0.10
        and float(final_zone_min_mid_v_ratio) <= 0.10
        and float(final_zone_max_v_drop) >= 0.90
    )

    if (
        bounded_raw_signal_day_count >= 2
        and pd.notna(earliest_bounded_raw_signal_lead_days)
        and float(earliest_bounded_raw_signal_lead_days) >= 2
    ):
        reason = (
            f"bounded raw-signal day가 {bounded_raw_signal_day_count}일이고 earliest lead가 "
            f"{int(earliest_bounded_raw_signal_lead_days)}일이라 progressive local precursor 기대 패턴"
        )
        return "progressive_local_precursor_expected", 1, reason

    if bounded_raw_signal_day_count <= 1:
        near_fault_strong_day = (
            pd.notna(earliest_bounded_raw_signal_lead_days)
            and float(earliest_bounded_raw_signal_lead_days) <= 1
        )
        if near_fault_strong_day or abrupt_collapse:
            if abrupt_collapse:
                reason = "fault 직전 1일 zone에서 output·voltage 급락과 큰 v_drop이 함께 보여 abrupt local 패턴"
            else:
                reason = "raw-signal day가 1일 이하이고 첫 strong day가 fault 1일 이내라 abrupt local 패턴"
            return "abrupt_local_precursor_unexpected", 0, reason

    if bounded_raw_signal_day_count == 0:
        reason = "bounded window에서 raw-signal day가 없어 progressive/abrupt를 확정하기 어려움"
    else:
        lead_text = (
            ""
            if pd.isna(earliest_bounded_raw_signal_lead_days)
            else f", earliest lead {int(earliest_bounded_raw_signal_lead_days)}일"
        )
        reason = (
            f"bounded raw-signal day {bounded_raw_signal_day_count}일{lead_text}로 "
            "progressive 요건도 abrupt 요건도 충족하지 않음"
        )
    return "unknown_local_temporality", 0, reason


def build_case_rows(
    cohort_df: pd.DataFrame,
    shadow_df: pd.DataFrame,
    site_p90s: dict[str, dict[str, float | pd.NA]],
    window_days: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    shadow_lookup = {
        (site, panel_id): group.sort_values("date_ts").copy()
        for (site, panel_id), group in shadow_df.groupby(["site", "panel_id"], sort=False)
    }
    default_thresholds = {col: pd.NA for col in SIGNAL_METRIC_COLS}

    for case in cohort_df.to_dict(orient="records"):
        panel_shadow = shadow_lookup.get((case["site"], case["panel_id"]), pd.DataFrame(columns=shadow_df.columns)).copy()
        fault_start_ts, fault_start_source = derive_fault_anchor(case, panel_shadow, window_days)

        window_start_ts = fault_start_ts - pd.Timedelta(days=window_days)
        window_df = panel_shadow.loc[
            panel_shadow["date_ts"].ge(window_start_ts) & panel_shadow["date_ts"].lt(fault_start_ts)
        ].copy()

        thresholds = site_p90s.get(case["site"], default_thresholds)
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
            window_df["raw_signal_day_flag"] = window_df.loc[:, signal_cols].sum(axis=1).gt(0).astype(int)
        else:
            window_df = window_df.copy()
            window_df["raw_signal_day_flag"] = pd.Series(dtype="int64")

        raw_signal_df = window_df.loc[window_df["raw_signal_day_flag"].eq(1)].copy()
        bounded_raw_signal_day_count = int(len(raw_signal_df))
        earliest_raw_signal_ts = raw_signal_df["date_ts"].min() if not raw_signal_df.empty else pd.NaT
        earliest_raw_signal_date = "" if pd.isna(earliest_raw_signal_ts) else earliest_raw_signal_ts.date().isoformat()
        earliest_raw_signal_lead_days = (
            pd.NA if pd.isna(earliest_raw_signal_ts) else int((fault_start_ts - earliest_raw_signal_ts).days)
        )

        final_zone_df = window_df.loc[
            window_df["date_ts"].ge(fault_start_ts - pd.Timedelta(days=1))
        ].copy()
        temporality_class, precursor_eligible_flag, temporality_reason = classify_temporality(
            bounded_raw_signal_day_count,
            earliest_raw_signal_lead_days,
            final_zone_df,
        )

        bounded_dates = {
            "ews_warning": nearest_bounded_date(panel_shadow, "ews_warning_flag", fault_start_ts, window_days),
            "prefault_B": nearest_bounded_date(panel_shadow, "prefault_B_flag", fault_start_ts, window_days),
            "pre_alarm": nearest_bounded_date(panel_shadow, "pre_alarm_flag", fault_start_ts, window_days),
        }
        best_alert_source, best_alert_date = earliest_bounded_alert_from_raw(panel_shadow, fault_start_ts, window_days)

        rows.append(
            {
                "site": case["site"],
                "panel_id": case["panel_id"],
                "strict_trigger_date": case["strict_trigger_date"],
                "fault_start_date": fault_start_ts.date().isoformat(),
                "fault_start_source": fault_start_source,
                "vendor_fault_family": first_nonblank(
                    case.get("vendor_fault_family"),
                    case.get("vendor_fault_family_vendor"),
                    case.get("vendor_fault_family_reaudit"),
                ),
                "bounded_raw_signal_day_count": bounded_raw_signal_day_count,
                "earliest_bounded_raw_signal_date": earliest_raw_signal_date,
                "earliest_bounded_raw_signal_lead_days": earliest_raw_signal_lead_days,
                "first_ews_warning_date_bounded": "" if pd.isna(bounded_dates["ews_warning"]) else bounded_dates["ews_warning"].date().isoformat(),
                "first_prefault_B_date_bounded": "" if pd.isna(bounded_dates["prefault_B"]) else bounded_dates["prefault_B"].date().isoformat(),
                "first_pre_alarm_date_bounded": "" if pd.isna(bounded_dates["pre_alarm"]) else bounded_dates["pre_alarm"].date().isoformat(),
                "ews_warning_bounded_hit_flag": 0 if pd.isna(bounded_dates["ews_warning"]) else 1,
                "prefault_B_bounded_hit_flag": 0 if pd.isna(bounded_dates["prefault_B"]) else 1,
                "pre_alarm_bounded_hit_flag": 0 if pd.isna(bounded_dates["pre_alarm"]) else 1,
                "any_local_precursor_bounded_hit_flag": int(any(pd.notna(ts) for ts in bounded_dates.values())),
                "best_alert_source": best_alert_source,
                "best_alert_lead_days": pd.NA if pd.isna(best_alert_date) else int((fault_start_ts - best_alert_date).days),
                "temporality_class": temporality_class,
                "precursor_eligible_flag": precursor_eligible_flag,
                "temporality_reason_ko": temporality_reason,
            }
        )

    cases_df = pd.DataFrame(rows, columns=CASE_OUTPUT_COLS)
    if cases_df.empty:
        return cases_df

    int_cols = [
        "bounded_raw_signal_day_count",
        "ews_warning_bounded_hit_flag",
        "prefault_B_bounded_hit_flag",
        "pre_alarm_bounded_hit_flag",
        "any_local_precursor_bounded_hit_flag",
        "precursor_eligible_flag",
    ]
    for col in int_cols:
        cases_df[col] = pd.to_numeric(cases_df[col], errors="coerce").fillna(0).astype(int)
    return cases_df


def build_summary(cases_df: pd.DataFrame, sites: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    groups = [("overall", "", cases_df)] + [
        ("site", site, cases_df.loc[cases_df["site"].eq(site)].copy()) for site in sites
    ]

    for record_type, site, group in groups:
        cohort_case_count = int(len(group))
        eligible_df = group.loc[group["precursor_eligible_flag"].eq(1)].copy()
        eligible_case_count = int(len(eligible_df))
        any_hit_case_count = int(eligible_df["any_local_precursor_bounded_hit_flag"].sum()) if eligible_case_count else 0
        ews_hit_case_count = int(eligible_df["ews_warning_bounded_hit_flag"].sum()) if eligible_case_count else 0
        prefault_hit_case_count = int(eligible_df["prefault_B_bounded_hit_flag"].sum()) if eligible_case_count else 0
        pre_alarm_hit_case_count = int(eligible_df["pre_alarm_bounded_hit_flag"].sum()) if eligible_case_count else 0
        rows.append(
            {
                "record_type": record_type,
                "site": site,
                "cohort_case_count": cohort_case_count,
                "progressive_local_precursor_expected_count": int(group["temporality_class"].eq("progressive_local_precursor_expected").sum()) if cohort_case_count else 0,
                "abrupt_local_precursor_unexpected_count": int(group["temporality_class"].eq("abrupt_local_precursor_unexpected").sum()) if cohort_case_count else 0,
                "unknown_local_temporality_count": int(group["temporality_class"].eq("unknown_local_temporality").sum()) if cohort_case_count else 0,
                "precursor_eligible_case_count": eligible_case_count,
                "precursor_eligible_hit_case_count": any_hit_case_count,
                "precursor_eligible_hit_rate": safe_div(any_hit_case_count, eligible_case_count),
                "ews_warning_eligible_hit_case_count": ews_hit_case_count,
                "ews_warning_eligible_hit_rate": safe_div(ews_hit_case_count, eligible_case_count),
                "prefault_B_eligible_hit_case_count": prefault_hit_case_count,
                "prefault_B_eligible_hit_rate": safe_div(prefault_hit_case_count, eligible_case_count),
                "pre_alarm_eligible_hit_case_count": pre_alarm_hit_case_count,
                "pre_alarm_eligible_hit_rate": safe_div(pre_alarm_hit_case_count, eligible_case_count),
                "median_best_alert_lead_days_on_eligible": median_or_blank(eligible_df["best_alert_lead_days"]),
                "noneligible_case_count": int(cohort_case_count - eligible_case_count),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_OUTPUT_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    shadow_df = load_shadow(root, args.sites)
    cohort_cases_df = load_cohort_cases(root, args.sites)
    positive_reaudit_df = load_positive_reaudit(root, args.sites)
    cohort_df = cohort_cases_df.merge(
        positive_reaudit_df.rename(columns={"vendor_fault_family": "vendor_fault_family_reaudit"}),
        on=CASE_KEY_COLS,
        how="inner",
    )
    vendor_df = load_vendor_context(root, args.sites)
    if not vendor_df.empty:
        cohort_df = cohort_df.merge(vendor_df, on=CASE_KEY_COLS, how="left")

    site_p90s = build_site_p90s(shadow_df)
    cases_df = build_case_rows(cohort_df, shadow_df, site_p90s, args.window_days)
    summary_df = build_summary(cases_df, args.sites)

    summary_df.to_csv(
        share_dir / "panel_day_engine_local_precursor_eligibility_summary_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    cases_df.to_csv(
        share_dir / "panel_day_engine_local_precursor_eligibility_cases_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    main()
