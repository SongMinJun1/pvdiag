#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
DEFAULT_MAX_PRECURSOR_LOOKBACK_DAYS = 30
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
    "candidate_validity",
    "vendor_fault_family",
    "first_ews_warning_date_any_prior",
    "first_prefault_B_date_any_prior",
    "first_pre_alarm_date_any_prior",
    "first_ews_warning_date_bounded",
    "first_prefault_B_date_bounded",
    "first_pre_alarm_date_bounded",
    "ews_warning_any_prior_hit_flag",
    "prefault_B_any_prior_hit_flag",
    "pre_alarm_any_prior_hit_flag",
    "ews_warning_bounded_hit_flag",
    "prefault_B_bounded_hit_flag",
    "pre_alarm_bounded_hit_flag",
    "any_local_precursor_any_prior_hit_flag",
    "any_local_precursor_bounded_hit_flag",
    "any_local_precursor_hit_flag",
    "ews_warning_bounded_lead_days",
    "prefault_B_bounded_lead_days",
    "pre_alarm_bounded_lead_days",
    "best_alert_source",
    "best_alert_lead_days",
    "stale_any_prior_alert_flag",
    "stale_best_alert_source",
    "stale_best_alert_lead_days",
]
SUMMARY_OUTPUT_COLS = [
    "record_type",
    "site",
    "cohort_case_count",
    "any_prior_hit_case_count",
    "any_prior_hit_rate",
    "bounded_hit_case_count",
    "bounded_hit_rate",
    "ews_warning_bounded_hit_case_count",
    "ews_warning_bounded_hit_rate",
    "prefault_B_bounded_hit_case_count",
    "prefault_B_bounded_hit_rate",
    "pre_alarm_bounded_hit_case_count",
    "pre_alarm_bounded_hit_rate",
    "bounded_lead_1_to_3_case_count",
    "bounded_lead_4_to_7_case_count",
    "bounded_lead_8_to_30_case_count",
    "stale_alert_case_count",
    "median_best_alert_lead_days",
    "no_bounded_alert_before_fault_count",
]
REQUIRED_SHADOW_COLS = [
    "site",
    "panel_id",
    "date",
    "final_fault",
    "ews_warning_flag",
    "prefault_B_flag",
    "pre_alarm_flag",
]
REQUIRED_REAUDIT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit panel_day_engine local precursor cohort behavior on truth-confirmed local fault cases."
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
        "--max-precursor-lookback-days",
        type=int,
        default=DEFAULT_MAX_PRECURSOR_LOOKBACK_DAYS,
        help="Maximum bounded precursor lookback window in days. Defaults to 30.",
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


def first_nonblank(left: object, right: object) -> str:
    left_text = normalize_text(left)
    if left_text:
        return left_text
    return normalize_text(right)


def load_shadow(root: Path, sites: list[str]) -> pd.DataFrame:
    shadow = read_csv(root / "_share" / "panel_day_engine_local_precursor_shadow_v1.csv")
    ensure_columns(shadow, REQUIRED_SHADOW_COLS, "panel_day_engine_local_precursor_shadow_v1.csv")

    shadow = shadow.copy()
    shadow["site"] = shadow["site"].map(normalize_text)
    shadow["panel_id"] = shadow["panel_id"].map(normalize_text)
    shadow["date"] = shadow["date"].map(normalize_date)
    shadow = shadow.loc[shadow["site"].isin(sites)].copy()
    shadow = dedupe_by_keys(shadow, "panel_day_engine_local_precursor_shadow_v1.csv", ["site", "panel_id", "date"])
    shadow["date_ts"] = shadow["date"].map(parse_date)
    for col in ["final_fault", "ews_warning_flag", "prefault_B_flag", "pre_alarm_flag"]:
        shadow[col] = shadow[col].map(to_int_flag).astype(int)
    return shadow


def load_reaudit(root: Path, sites: list[str]) -> pd.DataFrame:
    reaudit = read_csv(root / "_share" / "panel_date_reaudit_working.csv")
    ensure_columns(reaudit, REQUIRED_REAUDIT_COLS, "panel_date_reaudit_working.csv")
    reaudit = reaudit.copy()
    for col in ["site", "panel_id", "candidate_validity"]:
        reaudit[col] = reaudit[col].map(normalize_text)
    reaudit["strict_trigger_date"] = reaudit["strict_trigger_date"].map(normalize_date)
    if "vendor_fault_family" not in reaudit.columns:
        reaudit["vendor_fault_family"] = ""
    reaudit["vendor_fault_family"] = reaudit["vendor_fault_family"].map(normalize_text)
    reaudit = reaudit.loc[
        reaudit["site"].isin(sites) & reaudit["candidate_validity"].eq("true_positive")
    ].copy()
    reaudit = dedupe_by_keys(reaudit, "panel_date_reaudit_working.csv", KEY_COLS)
    return reaudit.loc[:, [*KEY_COLS, "candidate_validity", "vendor_fault_family"]].copy()


def load_vendor_context(root: Path, sites: list[str]) -> pd.DataFrame:
    path = root / "_share" / "vendor_reply_adjudication_latest.csv"
    if not path.exists():
        return pd.DataFrame(columns=[*KEY_COLS, "vendor_fault_family_vendor"])
    vendor = read_csv(path)
    required = ["site", "panel_id", "strict_trigger_date", "vendor_fault_family"]
    ensure_columns(vendor, required, "vendor_reply_adjudication_latest.csv")
    vendor = vendor.copy()
    vendor["site"] = vendor["site"].map(normalize_text)
    vendor["panel_id"] = vendor["panel_id"].map(normalize_text)
    vendor["strict_trigger_date"] = vendor["strict_trigger_date"].map(normalize_date)
    vendor["vendor_fault_family"] = vendor["vendor_fault_family"].map(normalize_text)
    vendor = vendor.loc[vendor["site"].isin(sites)].copy()
    vendor = dedupe_by_keys(vendor.loc[:, required], "vendor_reply_adjudication_latest.csv", KEY_COLS)
    return vendor.rename(columns={"vendor_fault_family": "vendor_fault_family_vendor"})


def earliest_any_prior_date(panel_df: pd.DataFrame, flag_col: str, fault_start_date: pd.Timestamp) -> pd.Timestamp | pd.NaT:
    if panel_df.empty:
        return pd.NaT
    matches = panel_df.loc[
        panel_df[flag_col].eq(1) & panel_df["date_ts"].lt(fault_start_date),
        "date_ts",
    ].dropna()
    if matches.empty:
        return pd.NaT
    return matches.min()


def nearest_bounded_date(
    panel_df: pd.DataFrame,
    flag_col: str,
    fault_start_date: pd.Timestamp,
    lookback_days: int,
) -> pd.Timestamp | pd.NaT:
    if panel_df.empty:
        return pd.NaT
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


def best_source_from_dates(
    date_map: dict[str, pd.Timestamp | pd.NaT],
    prefer_earliest: bool,
) -> tuple[str, pd.Timestamp | pd.NaT]:
    choices = [
        (source, ts, ALERT_PRIORITY[source])
        for source, ts in date_map.items()
        if pd.notna(ts)
    ]
    if not choices:
        return "none", pd.NaT
    if prefer_earliest:
        choices.sort(key=lambda item: (item[1], item[2]))
    else:
        choices.sort(key=lambda item: (-item[1].value, item[2]))
    return choices[0][0], choices[0][1]


def earliest_bounded_alert_from_raw(
    panel_df: pd.DataFrame,
    fault_start_date: pd.Timestamp,
    lookback_days: int,
) -> tuple[str, pd.Timestamp | pd.NaT]:
    if panel_df.empty:
        return "none", pd.NaT
    lower_bound = fault_start_date - pd.Timedelta(days=lookback_days)
    bounded_rows = panel_df.loc[
        panel_df["date_ts"].lt(fault_start_date)
        & panel_df["date_ts"].ge(lower_bound)
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


def build_case_rows(
    cohort_df: pd.DataFrame,
    shadow_df: pd.DataFrame,
    max_precursor_lookback_days: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    shadow_lookup = {
        (site, panel_id): group.copy()
        for (site, panel_id), group in shadow_df.groupby(["site", "panel_id"], sort=False)
    }

    for case in cohort_df.itertuples(index=False):
        strict_trigger_ts = parse_date(case.strict_trigger_date)
        if pd.isna(strict_trigger_ts):
            raise SystemExit(f"invalid strict_trigger_date for case: {case.site}|{case.panel_id}|{case.strict_trigger_date}")
        panel_shadow = shadow_lookup.get((case.site, case.panel_id), pd.DataFrame(columns=shadow_df.columns)).copy()

        final_fault_dates = panel_shadow.loc[
            panel_shadow["final_fault"].eq(1)
            & panel_shadow["date_ts"].ge(strict_trigger_ts - pd.Timedelta(days=30)),
            "date_ts",
        ].dropna()
        if not final_fault_dates.empty:
            fault_start_ts = final_fault_dates.min()
            fault_start_source = "final_fault_first_true"
        else:
            fault_start_ts = strict_trigger_ts
            fault_start_source = "strict_trigger_fallback"

        any_prior_dates = {
            "ews_warning": earliest_any_prior_date(panel_shadow, "ews_warning_flag", fault_start_ts),
            "prefault_B": earliest_any_prior_date(panel_shadow, "prefault_B_flag", fault_start_ts),
            "pre_alarm": earliest_any_prior_date(panel_shadow, "pre_alarm_flag", fault_start_ts),
        }
        bounded_dates = {
            "ews_warning": nearest_bounded_date(
                panel_shadow, "ews_warning_flag", fault_start_ts, max_precursor_lookback_days
            ),
            "prefault_B": nearest_bounded_date(
                panel_shadow, "prefault_B_flag", fault_start_ts, max_precursor_lookback_days
            ),
            "pre_alarm": nearest_bounded_date(
                panel_shadow, "pre_alarm_flag", fault_start_ts, max_precursor_lookback_days
            ),
        }

        any_prior_best_source, any_prior_best_date = best_source_from_dates(any_prior_dates, prefer_earliest=True)
        bounded_best_source, bounded_best_date = earliest_bounded_alert_from_raw(
            panel_shadow,
            fault_start_ts,
            max_precursor_lookback_days,
        )

        any_prior_hit_flag = int(any(pd.notna(ts) for ts in any_prior_dates.values()))
        bounded_hit_flag = int(any(pd.notna(ts) for ts in bounded_dates.values()))
        stale_flag = int(any_prior_hit_flag == 1 and bounded_hit_flag == 0)

        rows.append(
            {
                "site": case.site,
                "panel_id": case.panel_id,
                "strict_trigger_date": case.strict_trigger_date,
                "fault_start_date": fault_start_ts.date().isoformat(),
                "fault_start_source": fault_start_source,
                "candidate_validity": case.candidate_validity,
                "vendor_fault_family": case.vendor_fault_family,
                "first_ews_warning_date_any_prior": "" if pd.isna(any_prior_dates["ews_warning"]) else any_prior_dates["ews_warning"].date().isoformat(),
                "first_prefault_B_date_any_prior": "" if pd.isna(any_prior_dates["prefault_B"]) else any_prior_dates["prefault_B"].date().isoformat(),
                "first_pre_alarm_date_any_prior": "" if pd.isna(any_prior_dates["pre_alarm"]) else any_prior_dates["pre_alarm"].date().isoformat(),
                "first_ews_warning_date_bounded": "" if pd.isna(bounded_dates["ews_warning"]) else bounded_dates["ews_warning"].date().isoformat(),
                "first_prefault_B_date_bounded": "" if pd.isna(bounded_dates["prefault_B"]) else bounded_dates["prefault_B"].date().isoformat(),
                "first_pre_alarm_date_bounded": "" if pd.isna(bounded_dates["pre_alarm"]) else bounded_dates["pre_alarm"].date().isoformat(),
                "ews_warning_any_prior_hit_flag": 0 if pd.isna(any_prior_dates["ews_warning"]) else 1,
                "prefault_B_any_prior_hit_flag": 0 if pd.isna(any_prior_dates["prefault_B"]) else 1,
                "pre_alarm_any_prior_hit_flag": 0 if pd.isna(any_prior_dates["pre_alarm"]) else 1,
                "ews_warning_bounded_hit_flag": 0 if pd.isna(bounded_dates["ews_warning"]) else 1,
                "prefault_B_bounded_hit_flag": 0 if pd.isna(bounded_dates["prefault_B"]) else 1,
                "pre_alarm_bounded_hit_flag": 0 if pd.isna(bounded_dates["pre_alarm"]) else 1,
                "any_local_precursor_any_prior_hit_flag": any_prior_hit_flag,
                "any_local_precursor_bounded_hit_flag": bounded_hit_flag,
                "any_local_precursor_hit_flag": bounded_hit_flag,
                "ews_warning_bounded_lead_days": pd.NA if pd.isna(bounded_dates["ews_warning"]) else int((fault_start_ts - bounded_dates["ews_warning"]).days),
                "prefault_B_bounded_lead_days": pd.NA if pd.isna(bounded_dates["prefault_B"]) else int((fault_start_ts - bounded_dates["prefault_B"]).days),
                "pre_alarm_bounded_lead_days": pd.NA if pd.isna(bounded_dates["pre_alarm"]) else int((fault_start_ts - bounded_dates["pre_alarm"]).days),
                "best_alert_source": bounded_best_source,
                "best_alert_lead_days": pd.NA if pd.isna(bounded_best_date) else int((fault_start_ts - bounded_best_date).days),
                "stale_any_prior_alert_flag": stale_flag,
                "stale_best_alert_source": any_prior_best_source if stale_flag == 1 else "none",
                "stale_best_alert_lead_days": (
                    pd.NA
                    if stale_flag == 0 or pd.isna(any_prior_best_date)
                    else int((fault_start_ts - any_prior_best_date).days)
                ),
            }
        )

    cases_df = pd.DataFrame(rows, columns=CASE_OUTPUT_COLS)
    if cases_df.empty:
        return cases_df
    int_cols = [
        "ews_warning_any_prior_hit_flag",
        "prefault_B_any_prior_hit_flag",
        "pre_alarm_any_prior_hit_flag",
        "ews_warning_bounded_hit_flag",
        "prefault_B_bounded_hit_flag",
        "pre_alarm_bounded_hit_flag",
        "any_local_precursor_any_prior_hit_flag",
        "any_local_precursor_bounded_hit_flag",
        "any_local_precursor_hit_flag",
        "stale_any_prior_alert_flag",
    ]
    for col in int_cols:
        cases_df[col] = pd.to_numeric(cases_df[col], errors="coerce").fillna(0).astype(int)
    return cases_df


def median_or_blank(series: pd.Series) -> object:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return pd.NA
    return round(float(numeric.median()), 6)


def build_summary(cases_df: pd.DataFrame, sites: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    groups = [("overall", "", cases_df)] + [
        ("site", site, cases_df.loc[cases_df["site"].eq(site)].copy()) for site in sites
    ]
    for record_type, site, group in groups:
        cohort_case_count = int(len(group))
        any_prior_hit_count = int(group["any_local_precursor_any_prior_hit_flag"].sum()) if cohort_case_count else 0
        bounded_hit_count = int(group["any_local_precursor_bounded_hit_flag"].sum()) if cohort_case_count else 0
        ews_bounded_hit_count = int(group["ews_warning_bounded_hit_flag"].sum()) if cohort_case_count else 0
        prefault_bounded_hit_count = int(group["prefault_B_bounded_hit_flag"].sum()) if cohort_case_count else 0
        pre_alarm_bounded_hit_count = int(group["pre_alarm_bounded_hit_flag"].sum()) if cohort_case_count else 0
        best_leads = pd.to_numeric(group["best_alert_lead_days"], errors="coerce")
        rows.append(
            {
                "record_type": record_type,
                "site": site,
                "cohort_case_count": cohort_case_count,
                "any_prior_hit_case_count": any_prior_hit_count,
                "any_prior_hit_rate": safe_div(any_prior_hit_count, cohort_case_count),
                "bounded_hit_case_count": bounded_hit_count,
                "bounded_hit_rate": safe_div(bounded_hit_count, cohort_case_count),
                "ews_warning_bounded_hit_case_count": ews_bounded_hit_count,
                "ews_warning_bounded_hit_rate": safe_div(ews_bounded_hit_count, cohort_case_count),
                "prefault_B_bounded_hit_case_count": prefault_bounded_hit_count,
                "prefault_B_bounded_hit_rate": safe_div(prefault_bounded_hit_count, cohort_case_count),
                "pre_alarm_bounded_hit_case_count": pre_alarm_bounded_hit_count,
                "pre_alarm_bounded_hit_rate": safe_div(pre_alarm_bounded_hit_count, cohort_case_count),
                "bounded_lead_1_to_3_case_count": int(best_leads.between(1, 3, inclusive="both").sum()),
                "bounded_lead_4_to_7_case_count": int(best_leads.between(4, 7, inclusive="both").sum()),
                "bounded_lead_8_to_30_case_count": int(best_leads.between(8, 30, inclusive="both").sum()),
                "stale_alert_case_count": int(group["stale_any_prior_alert_flag"].sum()) if cohort_case_count else 0,
                "median_best_alert_lead_days": median_or_blank(group["best_alert_lead_days"]),
                "no_bounded_alert_before_fault_count": int(cohort_case_count - bounded_hit_count),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_OUTPUT_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    shadow_df = load_shadow(root, args.sites)
    cohort_df = load_reaudit(root, args.sites)
    vendor_df = load_vendor_context(root, args.sites)
    if not vendor_df.empty:
        cohort_df = cohort_df.merge(vendor_df, on=KEY_COLS, how="left")
        cohort_df["vendor_fault_family"] = cohort_df.apply(
            lambda row: first_nonblank(row["vendor_fault_family"], row.get("vendor_fault_family_vendor", "")),
            axis=1,
        )
        cohort_df = cohort_df.drop(columns=["vendor_fault_family_vendor"])

    cases_df = build_case_rows(cohort_df, shadow_df, args.max_precursor_lookback_days)
    summary_df = build_summary(cases_df, args.sites)

    cases_df.to_csv(
        share_dir / "panel_day_engine_local_precursor_cohort_cases_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    summary_df.to_csv(
        share_dir / "panel_day_engine_local_precursor_cohort_summary_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    main()
