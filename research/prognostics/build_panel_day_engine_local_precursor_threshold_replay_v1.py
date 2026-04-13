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
REPLAY_RULE_IDS = [
    "current_bounded_alert",
    "raw_signal_any_day",
    "raw_signal_2day_persistence",
    "shape_plus_electrical_combo",
]
SUMMARY_OUTPUT_COLS = [
    "rule_id",
    "positive_case_count",
    "positive_trigger_case_count",
    "positive_trigger_rate",
    "nuisance_case_count",
    "nuisance_trigger_case_count",
    "nuisance_trigger_rate",
    "final_fault_first_true_positive_case_count",
    "final_fault_first_true_positive_trigger_rate",
    "strict_trigger_fallback_positive_case_count",
    "strict_trigger_fallback_positive_trigger_rate",
    "median_positive_rule_lead_days",
    "recovered_positive_cases_vs_current",
]
CASE_OUTPUT_COLS = [
    "rule_id",
    "cohort_type",
    "site",
    "panel_id",
    "strict_trigger_date",
    "anchor_date",
    "anchor_source",
    "vendor_fault_family",
    "rule_trigger_flag",
    "earliest_rule_trigger_date",
    "rule_lead_days",
    "bounded_raw_signal_day_count",
    "any_group_off_like_flag",
    "any_shadow_like_flag",
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
REQUIRED_COHORT_CASE_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "fault_start_date",
    "fault_start_source",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay alternative local precursor alert rules on top of the stable panel_day_engine local precursor shadow."
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
        help="Bounded replay window in days. Defaults to 30.",
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
    for col in ["final_fault", "group_off_like", "shadow_like", "ews_warning_flag", "prefault_B_flag", "pre_alarm_flag"]:
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
        reaudit["site"].isin(sites)
        & reaudit["candidate_validity"].isin(["true_positive", "group_side", "false_positive"])
    ].copy()
    return dedupe_by_keys(reaudit, "panel_date_reaudit_working.csv", CASE_KEY_COLS)


def load_positive_anchor_cases(root: Path, sites: list[str]) -> pd.DataFrame:
    cohort_cases = read_csv(root / "_share" / "panel_day_engine_local_precursor_cohort_cases_v1.csv")
    ensure_columns(cohort_cases, REQUIRED_COHORT_CASE_COLS, "panel_day_engine_local_precursor_cohort_cases_v1.csv")
    cohort_cases = cohort_cases.copy()
    cohort_cases["site"] = cohort_cases["site"].map(normalize_text)
    cohort_cases["panel_id"] = cohort_cases["panel_id"].map(normalize_text)
    cohort_cases["strict_trigger_date"] = cohort_cases["strict_trigger_date"].map(normalize_date)
    cohort_cases["fault_start_date"] = cohort_cases["fault_start_date"].map(normalize_date)
    cohort_cases["fault_start_source"] = cohort_cases["fault_start_source"].map(normalize_text)
    cohort_cases = cohort_cases.loc[cohort_cases["site"].isin(sites)].copy()
    return dedupe_by_keys(cohort_cases, "panel_day_engine_local_precursor_cohort_cases_v1.csv", CASE_KEY_COLS)


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


def build_evaluation_cases(
    reaudit_df: pd.DataFrame,
    positive_anchor_df: pd.DataFrame,
) -> pd.DataFrame:
    positive_df = reaudit_df.loc[reaudit_df["candidate_validity"].eq("true_positive")].copy()
    positive_df = positive_df.merge(
        positive_anchor_df.loc[:, [*CASE_KEY_COLS, "fault_start_date", "fault_start_source"]],
        on=CASE_KEY_COLS,
        how="left",
    )
    missing_positive = positive_df.loc[positive_df["fault_start_date"].eq("") | positive_df["fault_start_date"].isna(), CASE_KEY_COLS]
    if not missing_positive.empty:
        raise SystemExit("true_positive cohort cases missing fault_start_date/fault_start_source from cohort audit")
    positive_df["cohort_type"] = "positive"
    positive_df["anchor_date"] = positive_df["fault_start_date"]
    positive_df["anchor_source"] = positive_df["fault_start_source"]

    nuisance_df = reaudit_df.loc[reaudit_df["candidate_validity"].isin(["group_side", "false_positive"])].copy()
    nuisance_df["cohort_type"] = "nuisance"
    nuisance_df["anchor_date"] = nuisance_df["strict_trigger_date"]
    nuisance_df["anchor_source"] = "strict_trigger_anchor"

    combined = pd.concat([positive_df, nuisance_df], ignore_index=True, sort=False)
    return combined.loc[
        :,
        [
            "cohort_type",
            "site",
            "panel_id",
            "strict_trigger_date",
            "anchor_date",
            "anchor_source",
            "vendor_fault_family",
        ],
    ].copy()


def evaluate_window_rules(window_df: pd.DataFrame) -> dict[str, tuple[int, pd.Timestamp | pd.NaT]]:
    alert_rows = window_df.loc[
        window_df[["ews_warning_flag", "prefault_B_flag", "pre_alarm_flag"]].max(axis=1).eq(1)
    ].copy()
    raw_signal_rows = window_df.loc[window_df["raw_signal_day_flag"].eq(1)].copy()
    combo_rows = window_df.loc[
        (
            window_df[["recon_high", "dtw_high", "hs_high"]].max(axis=1).eq(1)
            & window_df[["mid_v_low", "mid_i_low", "v_drop_high"]].max(axis=1).eq(1)
        )
    ].copy()

    results: dict[str, tuple[int, pd.Timestamp | pd.NaT]] = {}
    current_ts = alert_rows["date_ts"].min() if not alert_rows.empty else pd.NaT
    any_signal_ts = raw_signal_rows["date_ts"].min() if not raw_signal_rows.empty else pd.NaT
    if len(raw_signal_rows) >= 2:
        persistence_ts = raw_signal_rows.sort_values("date_ts").iloc[1]["date_ts"]
    else:
        persistence_ts = pd.NaT
    combo_ts = combo_rows["date_ts"].min() if not combo_rows.empty else pd.NaT

    results["current_bounded_alert"] = (0 if pd.isna(current_ts) else 1, current_ts)
    results["raw_signal_any_day"] = (0 if pd.isna(any_signal_ts) else 1, any_signal_ts)
    results["raw_signal_2day_persistence"] = (0 if pd.isna(persistence_ts) else 1, persistence_ts)
    results["shape_plus_electrical_combo"] = (0 if pd.isna(combo_ts) else 1, combo_ts)
    return results


def build_case_outputs(
    eval_cases_df: pd.DataFrame,
    shadow_df: pd.DataFrame,
    site_p90s: dict[str, dict[str, float | pd.NA]],
    window_days: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    default_thresholds = {col: pd.NA for col in SIGNAL_METRIC_COLS}
    shadow_lookup = {
        (site, panel_id): group.sort_values("date_ts").copy()
        for (site, panel_id), group in shadow_df.groupby(["site", "panel_id"], sort=False)
    }

    for case in eval_cases_df.itertuples(index=False):
        anchor_ts = parse_date(case.anchor_date)
        if pd.isna(anchor_ts):
            raise SystemExit(f"invalid anchor_date for case: {case.site}|{case.panel_id}|{case.strict_trigger_date}")
        panel_shadow = shadow_lookup.get((case.site, case.panel_id), pd.DataFrame(columns=shadow_df.columns)).copy()
        window_start_ts = anchor_ts - pd.Timedelta(days=window_days)
        window_df = panel_shadow.loc[
            panel_shadow["date_ts"].ge(window_start_ts) & panel_shadow["date_ts"].lt(anchor_ts)
        ].copy()

        thresholds = site_p90s.get(case.site, default_thresholds)
        if not window_df.empty:
            signal_flag_df = window_df.apply(lambda row: pd.Series(compute_signal_flags(row, thresholds)), axis=1)
            window_df = pd.concat([window_df.reset_index(drop=True), signal_flag_df.reset_index(drop=True)], axis=1)
            signal_cols = ["recon_high", "dtw_high", "hs_high", "mid_v_low", "mid_i_low", "v_drop_high"]
            window_df["raw_signal_day_flag"] = window_df.loc[:, signal_cols].sum(axis=1).gt(0).astype(int)
        else:
            for col in ["recon_high", "dtw_high", "hs_high", "mid_v_low", "mid_i_low", "v_drop_high", "raw_signal_day_flag"]:
                window_df[col] = pd.Series(dtype="object")

        rule_results = evaluate_window_rules(window_df)
        bounded_raw_signal_day_count = int(window_df["raw_signal_day_flag"].sum()) if not window_df.empty else 0
        any_group_off_like_flag = int(window_df["group_off_like"].max()) if not window_df.empty else 0
        any_shadow_like_flag = int(window_df["shadow_like"].max()) if not window_df.empty else 0

        for rule_id in REPLAY_RULE_IDS:
            rule_trigger_flag, trigger_ts = rule_results[rule_id]
            rows.append(
                {
                    "rule_id": rule_id,
                    "cohort_type": case.cohort_type,
                    "site": case.site,
                    "panel_id": case.panel_id,
                    "strict_trigger_date": case.strict_trigger_date,
                    "anchor_date": case.anchor_date,
                    "anchor_source": case.anchor_source,
                    "vendor_fault_family": case.vendor_fault_family,
                    "rule_trigger_flag": int(rule_trigger_flag),
                    "earliest_rule_trigger_date": "" if pd.isna(trigger_ts) else trigger_ts.date().isoformat(),
                    "rule_lead_days": (
                        pd.NA
                        if case.cohort_type != "positive" or pd.isna(trigger_ts)
                        else int((anchor_ts - trigger_ts).days)
                    ),
                    "bounded_raw_signal_day_count": bounded_raw_signal_day_count,
                    "any_group_off_like_flag": any_group_off_like_flag,
                    "any_shadow_like_flag": any_shadow_like_flag,
                }
            )

    cases_df = pd.DataFrame(rows, columns=CASE_OUTPUT_COLS)
    if not cases_df.empty:
        int_cols = [
            "rule_trigger_flag",
            "bounded_raw_signal_day_count",
            "any_group_off_like_flag",
            "any_shadow_like_flag",
        ]
        for col in int_cols:
            cases_df[col] = pd.to_numeric(cases_df[col], errors="coerce").fillna(0).astype(int)
    return cases_df


def build_summary(cases_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    current_positive_trigger_count = int(
        cases_df.loc[
            cases_df["rule_id"].eq("current_bounded_alert") & cases_df["cohort_type"].eq("positive"),
            "rule_trigger_flag",
        ].sum()
    )

    for rule_id in REPLAY_RULE_IDS:
        rule_cases = cases_df.loc[cases_df["rule_id"].eq(rule_id)].copy()
        positive = rule_cases.loc[rule_cases["cohort_type"].eq("positive")].copy()
        nuisance = rule_cases.loc[rule_cases["cohort_type"].eq("nuisance")].copy()
        final_fault_positive = positive.loc[positive["anchor_source"].eq("final_fault_first_true")].copy()
        strict_fallback_positive = positive.loc[positive["anchor_source"].eq("strict_trigger_fallback")].copy()

        positive_trigger_case_count = int(positive["rule_trigger_flag"].sum()) if not positive.empty else 0
        nuisance_trigger_case_count = int(nuisance["rule_trigger_flag"].sum()) if not nuisance.empty else 0

        rows.append(
            {
                "rule_id": rule_id,
                "positive_case_count": int(len(positive)),
                "positive_trigger_case_count": positive_trigger_case_count,
                "positive_trigger_rate": safe_div(positive_trigger_case_count, len(positive)),
                "nuisance_case_count": int(len(nuisance)),
                "nuisance_trigger_case_count": nuisance_trigger_case_count,
                "nuisance_trigger_rate": safe_div(nuisance_trigger_case_count, len(nuisance)),
                "final_fault_first_true_positive_case_count": int(len(final_fault_positive)),
                "final_fault_first_true_positive_trigger_rate": safe_div(
                    int(final_fault_positive["rule_trigger_flag"].sum()) if not final_fault_positive.empty else 0,
                    len(final_fault_positive),
                ),
                "strict_trigger_fallback_positive_case_count": int(len(strict_fallback_positive)),
                "strict_trigger_fallback_positive_trigger_rate": safe_div(
                    int(strict_fallback_positive["rule_trigger_flag"].sum()) if not strict_fallback_positive.empty else 0,
                    len(strict_fallback_positive),
                ),
                "median_positive_rule_lead_days": median_or_blank(
                    positive.loc[positive["rule_trigger_flag"].eq(1), "rule_lead_days"]
                ),
                "recovered_positive_cases_vs_current": positive_trigger_case_count - current_positive_trigger_count,
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_OUTPUT_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    shadow_df = load_shadow(root, args.sites)
    reaudit_df = load_reaudit(root, args.sites)
    positive_anchor_df = load_positive_anchor_cases(root, args.sites)
    eval_cases_df = build_evaluation_cases(reaudit_df, positive_anchor_df)
    site_p90s = build_site_p90s(shadow_df)
    cases_df = build_case_outputs(eval_cases_df, shadow_df, site_p90s, args.window_days)
    summary_df = build_summary(cases_df)

    cases_df.to_csv(
        share_dir / "panel_day_engine_local_precursor_threshold_replay_cases_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    summary_df.to_csv(
        share_dir / "panel_day_engine_local_precursor_threshold_replay_summary_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    main()
