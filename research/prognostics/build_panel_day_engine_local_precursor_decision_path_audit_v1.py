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
WINDOW_OUTPUT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "fault_start_date",
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
    "ews_warning_flag",
    "prefault_B_flag",
    "pre_alarm_flag",
    "cond_mid_proxy",
    "cond_ae_proxy",
    "cond_dtw_proxy",
    "cond_hs_proxy",
    "cond_mid_available_flag",
    "cond_ae_available_flag",
    "cond_dtw_available_flag",
    "cond_hs_available_flag",
    "day_path_state",
]
CASE_OUTPUT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "fault_start_date",
    "first_visible_signal_date",
    "first_ews_warning_date",
    "first_prefault_B_date",
    "first_pre_alarm_date",
    "earliest_day_path_state",
    "dominant_miss_reason_class",
    "dominant_miss_reason_ko",
]
SUMMARY_OUTPUT_COLS = [
    "record_type",
    "site",
    "cohort_case_count",
    "helper_alert_hit_case_count",
    "visible_signal_but_no_ews_warning_case_count",
    "ews_warning_without_alert_escalation_case_count",
    "no_visible_signal_before_fault_case_count",
    "unresolved_due_to_unpersisted_inputs_case_count",
    "first_visible_signal_case_count",
    "first_ews_warning_case_count",
    "first_prefault_B_case_count",
    "first_pre_alarm_case_count",
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
    "group_off_like",
    "shadow_like",
    "ews_warning_flag",
    "prefault_B_flag",
    "pre_alarm_flag",
]
REQUIRED_COHORT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "fault_start_date",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconstruct the panel_day_engine local precursor decision path as far as current persisted outputs allow."
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
        help="Audit window in days before fault_start_date. Defaults to 30.",
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


def safe_div(numer: int | float, denom: int | float) -> float:
    if denom <= 0:
        return 0.0
    return round(float(numer / denom), 6)


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
    for col in ["group_off_like", "shadow_like", "ews_warning_flag", "prefault_B_flag", "pre_alarm_flag"]:
        shadow[col] = shadow[col].map(to_int_flag).astype(int)
    return shadow


def load_cohort_cases(root: Path, sites: list[str]) -> pd.DataFrame:
    cohort_cases = read_csv(root / "_share" / "panel_day_engine_local_precursor_cohort_cases_v1.csv")
    ensure_columns(cohort_cases, REQUIRED_COHORT_COLS, "panel_day_engine_local_precursor_cohort_cases_v1.csv")
    cohort_cases = cohort_cases.copy()
    if "candidate_validity" in cohort_cases.columns:
        cohort_cases["candidate_validity"] = cohort_cases["candidate_validity"].map(normalize_text)
        cohort_cases = cohort_cases.loc[cohort_cases["candidate_validity"].eq("true_positive")].copy()
    for col in ["site", "panel_id"]:
        cohort_cases[col] = cohort_cases[col].map(normalize_text)
    for col in ["strict_trigger_date", "fault_start_date"]:
        cohort_cases[col] = cohort_cases[col].map(normalize_date)
    if "vendor_fault_family" not in cohort_cases.columns:
        cohort_cases["vendor_fault_family"] = ""
    cohort_cases["vendor_fault_family"] = cohort_cases["vendor_fault_family"].map(normalize_text)
    cohort_cases = cohort_cases.loc[cohort_cases["site"].isin(sites)].copy()
    cohort_cases = dedupe_by_keys(cohort_cases, "panel_day_engine_local_precursor_cohort_cases_v1.csv", CASE_KEY_COLS)
    return cohort_cases.loc[:, [*CASE_KEY_COLS, "fault_start_date", "vendor_fault_family"]].copy()


def build_site_p90s(shadow_df: pd.DataFrame) -> dict[str, dict[str, float | pd.NA]]:
    p90s: dict[str, dict[str, float | pd.NA]] = {}
    for site, group in shadow_df.groupby("site", sort=False):
        p90s[site] = {}
        for col in SIGNAL_METRIC_COLS:
            numeric = pd.to_numeric(group[col], errors="coerce").dropna()
            if numeric.empty:
                p90s[site][col] = pd.NA
            else:
                p90s[site][col] = float(numeric.quantile(0.9))
    return p90s


def bool_or_na(value: bool, available: int) -> object:
    if available == 0:
        return pd.NA
    return int(bool(value))


def day_path_state(row: pd.Series) -> str:
    prefault = int(row["prefault_B_flag"]) == 1
    pre_alarm = int(row["pre_alarm_flag"]) == 1
    ews = int(row["ews_warning_flag"]) == 1

    shape_flags = []
    for proxy_col, available_col in [
        ("cond_ae_proxy", "cond_ae_available_flag"),
        ("cond_dtw_proxy", "cond_dtw_available_flag"),
        ("cond_hs_proxy", "cond_hs_available_flag"),
    ]:
        if int(row[available_col]) == 1:
            shape_flags.append(int(row[proxy_col]) == 1)

    cond_mid_available = int(row["cond_mid_available_flag"]) == 1
    cond_mid_true = cond_mid_available and int(row["cond_mid_proxy"]) == 1
    visible_signal = cond_mid_true or any(shape_flags)
    any_key_available = cond_mid_available or any(int(row[col]) == 1 for col in ["cond_ae_available_flag", "cond_dtw_available_flag", "cond_hs_available_flag"])

    if prefault:
        return "prefault_B_day"
    if pre_alarm:
        return "pre_alarm_day"
    if ews and any(shape_flags):
        return "ews_plus_shape_or_distance"
    if ews and not any(shape_flags):
        return "ews_only"
    if visible_signal and not ews:
        return "visible_signal_no_ews"
    if any_key_available:
        return "no_visible_signal"
    return "unresolved_due_to_unpersisted_inputs"


def dominant_miss_reason_ko(reason_class: str) -> str:
    mapping = {
        "no_visible_signal_before_fault": "persisted decision path에서 fault 전 visible precursor signal을 확인하지 못함",
        "visible_signal_but_no_ews_warning": "visible signal proxy는 있었지만 persisted ews_warning은 나타나지 않음",
        "ews_warning_without_alert_escalation": "ews_warning은 있었지만 prefault_B/pre_alarm helper escalation은 일어나지 않음",
        "helper_alert_hit": "bounded window 안에서 helper alert(prefault_B 또는 pre_alarm)가 실제로 나타남",
        "unresolved_due_to_unpersisted_inputs": "핵심 내부 gate 입력이 persistence 되어 있지 않아 decision path를 clean하게 복원할 수 없음",
    }
    return mapping[reason_class]


def build_outputs(
    cohort_df: pd.DataFrame,
    shadow_df: pd.DataFrame,
    site_p90s: dict[str, dict[str, float | pd.NA]],
    window_days: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    window_rows: list[dict[str, object]] = []
    case_rows: list[dict[str, object]] = []
    shadow_lookup = {
        (site, panel_id): group.sort_values("date_ts").copy()
        for (site, panel_id), group in shadow_df.groupby(["site", "panel_id"], sort=False)
    }

    for case in cohort_df.itertuples(index=False):
        fault_start_ts = parse_date(case.fault_start_date)
        if pd.isna(fault_start_ts):
            raise SystemExit(f"invalid fault_start_date for case: {case.site}|{case.panel_id}|{case.strict_trigger_date}")
        window_start_ts = fault_start_ts - pd.Timedelta(days=window_days)
        panel_shadow = shadow_lookup.get((case.site, case.panel_id), pd.DataFrame(columns=shadow_df.columns)).copy()
        window_df = panel_shadow.loc[
            panel_shadow["date_ts"].ge(window_start_ts) & panel_shadow["date_ts"].lt(fault_start_ts)
        ].copy()

        thresholds = site_p90s.get(case.site, {})
        if not window_df.empty:
            cond_ae_available = window_df["recon_error"].notna() & pd.notna(thresholds.get("recon_error", pd.NA))
            cond_dtw_available = window_df["dtw_dist"].notna() & pd.notna(thresholds.get("dtw_dist", pd.NA))
            cond_hs_available = window_df["hs_score"].notna() & pd.notna(thresholds.get("hs_score", pd.NA))
            window_df["cond_mid_available_flag"] = 0
            window_df["cond_mid_proxy"] = pd.NA
            window_df["cond_ae_available_flag"] = cond_ae_available.astype(int)
            window_df["cond_dtw_available_flag"] = cond_dtw_available.astype(int)
            window_df["cond_hs_available_flag"] = cond_hs_available.astype(int)
            window_df["cond_ae_proxy"] = [
                bool_or_na(val, avail)
                for val, avail in zip(window_df["recon_error"] >= thresholds.get("recon_error", pd.NA), window_df["cond_ae_available_flag"])
            ]
            window_df["cond_dtw_proxy"] = [
                bool_or_na(val, avail)
                for val, avail in zip(window_df["dtw_dist"] >= thresholds.get("dtw_dist", pd.NA), window_df["cond_dtw_available_flag"])
            ]
            window_df["cond_hs_proxy"] = [
                bool_or_na(val, avail)
                for val, avail in zip(window_df["hs_score"] >= thresholds.get("hs_score", pd.NA), window_df["cond_hs_available_flag"])
            ]
            window_df["day_path_state"] = window_df.apply(day_path_state, axis=1)
        else:
            window_df = pd.DataFrame(columns=[*shadow_df.columns, *WINDOW_OUTPUT_COLS])

        for row in window_df.itertuples(index=False):
            window_rows.append(
                {
                    "site": case.site,
                    "panel_id": case.panel_id,
                    "strict_trigger_date": case.strict_trigger_date,
                    "fault_start_date": case.fault_start_date,
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
                    "ews_warning_flag": int(row.ews_warning_flag),
                    "prefault_B_flag": int(row.prefault_B_flag),
                    "pre_alarm_flag": int(row.pre_alarm_flag),
                    "cond_mid_proxy": row.cond_mid_proxy,
                    "cond_ae_proxy": row.cond_ae_proxy,
                    "cond_dtw_proxy": row.cond_dtw_proxy,
                    "cond_hs_proxy": row.cond_hs_proxy,
                    "cond_mid_available_flag": int(row.cond_mid_available_flag),
                    "cond_ae_available_flag": int(row.cond_ae_available_flag),
                    "cond_dtw_available_flag": int(row.cond_dtw_available_flag),
                    "cond_hs_available_flag": int(row.cond_hs_available_flag),
                    "day_path_state": row.day_path_state,
                }
            )

        if not window_df.empty:
            first_visible = window_df.loc[window_df["day_path_state"].eq("visible_signal_no_ews"), "date"]
            first_ews = window_df.loc[window_df["ews_warning_flag"].eq(1), "date"]
            first_prefault = window_df.loc[window_df["prefault_B_flag"].eq(1), "date"]
            first_pre_alarm = window_df.loc[window_df["pre_alarm_flag"].eq(1), "date"]
            informative_states = window_df.loc[
                ~window_df["day_path_state"].eq("no_visible_signal")
            ].sort_values("date_ts")
            earliest_state = informative_states.iloc[0]["day_path_state"] if not informative_states.empty else "no_visible_signal"
        else:
            first_visible = pd.Series(dtype="object")
            first_ews = pd.Series(dtype="object")
            first_prefault = pd.Series(dtype="object")
            first_pre_alarm = pd.Series(dtype="object")
            earliest_state = "unresolved_due_to_unpersisted_inputs"

        if not first_prefault.empty or not first_pre_alarm.empty:
            dominant_class = "helper_alert_hit"
        elif not first_visible.empty and first_ews.empty:
            dominant_class = "visible_signal_but_no_ews_warning"
        elif first_ews.size > 0 and not first_ews.empty and first_prefault.empty and first_pre_alarm.empty:
            dominant_class = "ews_warning_without_alert_escalation"
        elif window_df.empty:
            dominant_class = "unresolved_due_to_unpersisted_inputs"
        elif (window_df["day_path_state"] == "no_visible_signal").all():
            dominant_class = "no_visible_signal_before_fault"
        elif (window_df["day_path_state"] == "unresolved_due_to_unpersisted_inputs").any():
            dominant_class = "unresolved_due_to_unpersisted_inputs"
        else:
            dominant_class = "no_visible_signal_before_fault"

        case_rows.append(
            {
                "site": case.site,
                "panel_id": case.panel_id,
                "strict_trigger_date": case.strict_trigger_date,
                "fault_start_date": case.fault_start_date,
                "first_visible_signal_date": "" if first_visible.empty else str(first_visible.iloc[0]),
                "first_ews_warning_date": "" if first_ews.empty else str(first_ews.iloc[0]),
                "first_prefault_B_date": "" if first_prefault.empty else str(first_prefault.iloc[0]),
                "first_pre_alarm_date": "" if first_pre_alarm.empty else str(first_pre_alarm.iloc[0]),
                "earliest_day_path_state": earliest_state,
                "dominant_miss_reason_class": dominant_class,
                "dominant_miss_reason_ko": dominant_miss_reason_ko(dominant_class),
            }
        )

    windows_df = pd.DataFrame(window_rows, columns=WINDOW_OUTPUT_COLS)
    cases_df = pd.DataFrame(case_rows, columns=CASE_OUTPUT_COLS)
    return windows_df, cases_df


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
                "cohort_case_count": int(len(group)),
                "helper_alert_hit_case_count": int(group["dominant_miss_reason_class"].eq("helper_alert_hit").sum()) if not group.empty else 0,
                "visible_signal_but_no_ews_warning_case_count": int(group["dominant_miss_reason_class"].eq("visible_signal_but_no_ews_warning").sum()) if not group.empty else 0,
                "ews_warning_without_alert_escalation_case_count": int(group["dominant_miss_reason_class"].eq("ews_warning_without_alert_escalation").sum()) if not group.empty else 0,
                "no_visible_signal_before_fault_case_count": int(group["dominant_miss_reason_class"].eq("no_visible_signal_before_fault").sum()) if not group.empty else 0,
                "unresolved_due_to_unpersisted_inputs_case_count": int(group["dominant_miss_reason_class"].eq("unresolved_due_to_unpersisted_inputs").sum()) if not group.empty else 0,
                "first_visible_signal_case_count": int(group["first_visible_signal_date"].fillna("").ne("").sum()) if not group.empty else 0,
                "first_ews_warning_case_count": int(group["first_ews_warning_date"].fillna("").ne("").sum()) if not group.empty else 0,
                "first_prefault_B_case_count": int(group["first_prefault_B_date"].fillna("").ne("").sum()) if not group.empty else 0,
                "first_pre_alarm_case_count": int(group["first_pre_alarm_date"].fillna("").ne("").sum()) if not group.empty else 0,
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_OUTPUT_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    shadow_df = load_shadow(root, args.sites)
    cohort_df = load_cohort_cases(root, args.sites)
    site_p90s = build_site_p90s(shadow_df)
    windows_df, cases_df = build_outputs(cohort_df, shadow_df, site_p90s, args.window_days)
    summary_df = build_summary(cases_df, args.sites)

    summary_df.to_csv(
        share_dir / "panel_day_engine_local_precursor_decision_path_summary_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    cases_df.to_csv(
        share_dir / "panel_day_engine_local_precursor_decision_path_cases_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    windows_df.to_csv(
        share_dir / "panel_day_engine_local_precursor_decision_path_windows_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    main()
