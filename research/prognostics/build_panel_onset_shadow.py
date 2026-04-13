#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DEFAULT_SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
STRICT_OUTPUT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "first_warning_date",
    "retrospective_onset_date",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "shadow_like_fraction",
    "group_off_like_fraction",
    "reason_summary",
]
SUMMARY_COLS = [
    "site",
    "strict_cases",
    "shadow_rows",
    "median_days_earlier",
    "p90_days_earlier",
    "high_conf_count",
    "medium_conf_count",
    "low_conf_count",
]
SUSPICIOUS_COLS = STRICT_OUTPUT_COLS + ["suspicious_reason"]

LOW_THRESHOLD = 0.45
WARNING_THRESHOLD = 0.35
NORMAL_THRESHOLD = 0.20
RECOVERY_BREAK_DAYS = 10
PERSISTENCE_WINDOW = 7
PERSISTENCE_MIN_DAYS = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build panel-level retrospective onset shadow rows for strict cases.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    parser.add_argument(
        "--sites",
        nargs="*",
        default=DEFAULT_SITES,
        help="Sites to process. Defaults to the known stable sites.",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=60,
        help="Retrospective lookback window in days. Defaults to 60.",
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


def to_bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    text = series.fillna("").astype(str).str.strip().str.lower()
    return text.isin(["1", "true", "t", "yes", "y"])


def to_numeric_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def preferred_status_path(root: Path, site: str) -> Path:
    enriched = root / "data" / site / "out" / "latest_panel_status_enriched.csv"
    if enriched.exists():
        return enriched
    plain = root / "data" / site / "out" / "latest_panel_status.csv"
    if plain.exists():
        return plain
    raise SystemExit(f"missing latest panel status for {site}: expected {enriched} or {plain}")


def strict_case_mask(df: pd.DataFrame) -> pd.Series:
    mask = pd.Series(False, index=df.index)
    for col in ["diagnosis_date_online", "critical_diag_date", "dead_diag_date"]:
        if col in df.columns:
            mask |= df[col].notna()
    if "final_fault" in df.columns:
        mask |= to_bool_series(df["final_fault"])
    return mask


def clamp(series: pd.Series, low: float = 0.0, high: float = 1.0) -> pd.Series:
    return series.clip(lower=low, upper=high)


def median_or_nan(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return float("nan")
    return round(float(numeric.median()), 6)


def quantile_or_nan(series: pd.Series, q: float) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return float("nan")
    return round(float(numeric.quantile(q)), 6)


def last_recovery_break_end(normal_mask: pd.Series) -> int | None:
    run_start: int | None = None
    last_end: int | None = None
    for idx, is_normal in enumerate(normal_mask.tolist()):
        if is_normal:
            if run_start is None:
                run_start = idx
        elif run_start is not None:
            if idx - run_start >= RECOVERY_BREAK_DAYS:
                last_end = idx - 1
            run_start = None
    if run_start is not None and len(normal_mask) - run_start >= RECOVERY_BREAK_DAYS:
        last_end = len(normal_mask) - 1
    return last_end


def earliest_persistent_onset(candidate_mask: pd.Series, start_idx: int, strict_idx: int) -> int | None:
    for idx in range(start_idx, strict_idx + 1):
        if not bool(candidate_mask.iloc[idx]):
            continue
        end_idx = min(idx + PERSISTENCE_WINDOW, strict_idx + 1)
        window = candidate_mask.iloc[idx:end_idx]
        if len(window) == PERSISTENCE_WINDOW and int(window.sum()) >= PERSISTENCE_MIN_DAYS:
            return idx
    return None


def strict_trigger_from_panel_core(panel_df: pd.DataFrame, status_row: pd.Series) -> tuple[pd.Timestamp, str]:
    panel_df = panel_df.copy()
    panel_df["date_dt"] = pd.to_datetime(panel_df["date"], errors="coerce")
    candidates: list[tuple[pd.Timestamp, str]] = []

    def add_if_match(date_col: str, flag_col: str | None, method: str) -> None:
        if flag_col and flag_col in panel_df.columns:
            flag_dates = panel_df.loc[to_bool_series(panel_df[flag_col]), "date_dt"].dropna()
            if not flag_dates.empty:
                candidates.append((flag_dates.min(), method))
        if date_col in panel_df.columns:
            target = pd.to_datetime(status_row.get(date_col), errors="coerce")
            if pd.notna(target):
                matched = panel_df.loc[panel_df["date_dt"].eq(target), "date_dt"].dropna()
                if not matched.empty:
                    candidates.append((matched.min(), method))

    add_if_match("diagnosis_date_online", None, "online_diagnosis_day")
    add_if_match("critical_diag_date", "critical_diag_on_day", "critical_diagnosis_day")
    add_if_match("dead_diag_date", "dead_diag_on_day", "dead_diagnosis_day")

    for flag_col, method in [
        ("confirmed_fault", "confirmed_fault_flag"),
        ("critical_fault", "critical_fault_flag"),
        ("final_fault", "final_fault_flag"),
    ]:
        if flag_col in panel_df.columns:
            flag_dates = panel_df.loc[to_bool_series(panel_df[flag_col]), "date_dt"].dropna()
            if not flag_dates.empty:
                candidates.append((flag_dates.min(), method))

    if not candidates:
        fallback = pd.to_datetime(status_row.get("date"), errors="coerce")
        if pd.isna(fallback):
            raise SystemExit(f"unable to derive strict trigger date for {status_row.get('panel_id')}")
        return fallback, "status_row_fallback"

    candidates.sort(key=lambda item: item[0])
    return candidates[0]


def build_signal_frame(panel_df: pd.DataFrame) -> pd.DataFrame:
    df = panel_df.copy()
    df = df.sort_values("date_dt", kind="stable").reset_index(drop=True)

    for col in ["mid_ratio", "last_ratio", "v_drop", "coverage_mid", "coverage", "recon_error"]:
        if col in df.columns:
            df[col] = to_numeric_series(df[col])

    if "v_ref_ok" in df.columns:
        df["v_ref_ok_bool"] = to_bool_series(df["v_ref_ok"]).astype(float)
    else:
        df["v_ref_ok_bool"] = 1.0
    for flag_col in ["shadow_like", "group_off_like", "data_bad"]:
        if flag_col in df.columns:
            df[f"{flag_col}_bool"] = to_bool_series(df[flag_col]).astype(float)
        else:
            df[f"{flag_col}_bool"] = 0.0

    coverage_source = "coverage_mid" if "coverage_mid" in df.columns else "coverage"
    if coverage_source in df.columns:
        df["coverage_like"] = to_numeric_series(df[coverage_source])
    else:
        df["coverage_like"] = 1.0

    roll = lambda col: df[col].rolling(PERSISTENCE_WINDOW, min_periods=1).mean()

    df["mid_ratio_7d"] = roll("mid_ratio") if "mid_ratio" in df.columns else pd.Series(float("nan"), index=df.index)
    df["last_ratio_7d"] = roll("last_ratio") if "last_ratio" in df.columns else pd.Series(float("nan"), index=df.index)
    df["v_drop_7d"] = roll("v_drop") if "v_drop" in df.columns else pd.Series(float("nan"), index=df.index)
    df["coverage_7d"] = roll("coverage_like")
    df["v_ref_ok_7d"] = roll("v_ref_ok_bool")
    df["shadow_like_7d"] = roll("shadow_like_bool")
    df["group_off_like_7d"] = roll("group_off_like_bool")
    df["data_bad_7d"] = roll("data_bad_bool")

    mid_component = clamp((0.985 - df["mid_ratio_7d"]) / 0.08).fillna(0.0)
    last_component = clamp((0.985 - df["last_ratio_7d"]) / 0.08).fillna(0.0)
    vdrop_component = clamp(df["v_drop_7d"] / 0.12).fillna(0.0)

    if "recon_error" in df.columns:
        df["recon_error_7d"] = roll("recon_error")
        q50 = df["recon_error"].median(skipna=True)
        q75 = df["recon_error"].quantile(0.75)
        scale = max(float(q75 - q50) if pd.notna(q75) and pd.notna(q50) else 0.0, 1e-6)
        ae_component = clamp((df["recon_error_7d"] - float(q75 if pd.notna(q75) else q50 or 0.0)) / (3.0 * scale)).fillna(0.0)
    else:
        ae_component = pd.Series(0.0, index=df.index)

    df["onset_score"] = (
        0.35 * mid_component
        + 0.25 * last_component
        + 0.25 * vdrop_component
        + 0.15 * ae_component
    )
    low_validity_mask = (df["coverage_7d"] < 0.40) | (df["v_ref_ok_7d"] < 0.50)
    df.loc[low_validity_mask, "onset_score"] *= 0.60
    df.loc[df["data_bad_7d"] >= 0.5, "onset_score"] *= 0.50

    df["warning_flag"] = df["onset_score"] >= WARNING_THRESHOLD
    df["confound_primary"] = (df["shadow_like_7d"] >= 0.50) | (df["group_off_like_7d"] >= 0.50)
    df["candidate_flag"] = (
        (df["onset_score"] >= LOW_THRESHOLD)
        & (~df["confound_primary"])
        & (df["coverage_7d"] >= 0.40)
    )
    df["normal_flag"] = df["onset_score"] < NORMAL_THRESHOLD
    return df


def format_fraction(value: float) -> float:
    if pd.isna(value):
        return float("nan")
    return round(float(value), 6)


def analyze_strict_case(site: str, panel_id: str, panel_df: pd.DataFrame, strict_trigger_date: pd.Timestamp, strict_method: str, lookback_days: int) -> dict[str, object]:
    panel_df = panel_df.copy()
    panel_df["date_dt"] = pd.to_datetime(panel_df["date"], errors="coerce")
    panel_df = panel_df.loc[panel_df["date_dt"].notna()].sort_values("date_dt", kind="stable")

    window_start = strict_trigger_date - pd.Timedelta(days=lookback_days)
    analysis = panel_df.loc[
        panel_df["date_dt"].between(window_start, strict_trigger_date, inclusive="both")
    ].copy()
    if analysis.empty:
        return {
            "site": site,
            "panel_id": panel_id,
            "strict_trigger_date": strict_trigger_date.date().isoformat(),
            "first_warning_date": "",
            "retrospective_onset_date": strict_trigger_date.date().isoformat(),
            "days_earlier_than_trigger": 0,
            "onset_confidence": "low",
            "onset_method": "empty_window_fallback",
            "shadow_like_fraction": float("nan"),
            "group_off_like_fraction": float("nan"),
            "reason_summary": f"strict_method={strict_method}|analysis_window=empty",
            "_recovery_break_inconsistency": False,
        }

    analysis = build_signal_frame(analysis)
    strict_idx = int(analysis.index[analysis["date_dt"].eq(strict_trigger_date)][0]) if strict_trigger_date in set(analysis["date_dt"]) else int(analysis.index.max())

    warning_dates = analysis.loc[analysis["warning_flag"], "date_dt"]
    first_warning_date = warning_dates.min() if not warning_dates.empty else pd.NaT

    recovery_end_idx = last_recovery_break_end(analysis.loc[:strict_idx, "normal_flag"])
    search_start_idx = 0 if recovery_end_idx is None else recovery_end_idx + 1
    onset_idx = earliest_persistent_onset(analysis["candidate_flag"], search_start_idx, strict_idx)

    recovery_reset = recovery_end_idx is not None and pd.notna(first_warning_date) and first_warning_date <= analysis.loc[recovery_end_idx, "date_dt"]
    if onset_idx is None:
        onset_date = strict_trigger_date
        if analysis.loc[strict_idx, "confound_primary"]:
            onset_method = "strict_trigger_fallback_confound"
        else:
            onset_method = "strict_trigger_fallback"
    else:
        onset_date = analysis.loc[onset_idx, "date_dt"]
        onset_method = "persistent_5of7_after_recovery_break" if recovery_reset else "persistent_5of7"

    confound_slice = analysis.loc[analysis["date_dt"].between(onset_date, strict_trigger_date, inclusive="both")]
    if confound_slice.empty:
        confound_slice = analysis
    shadow_fraction = format_fraction(confound_slice["shadow_like_bool"].mean())
    group_off_fraction = format_fraction(confound_slice["group_off_like_bool"].mean())

    days_earlier = int((strict_trigger_date - onset_date).days)
    recovery_break_inconsistency = recovery_end_idx is not None and onset_idx is not None and onset_idx <= recovery_end_idx
    high_confound = max(shadow_fraction if pd.notna(shadow_fraction) else 0.0, group_off_fraction if pd.notna(group_off_fraction) else 0.0) >= 0.50

    if onset_method.startswith("persistent_5of7") and not high_confound and days_earlier >= 7 and analysis.loc[search_start_idx:strict_idx, "coverage_7d"].median() >= 0.6:
        onset_confidence = "high"
    elif onset_method.startswith("persistent_5of7") and not high_confound:
        onset_confidence = "medium"
    elif onset_method == "strict_trigger_fallback" and not high_confound:
        onset_confidence = "medium"
    else:
        onset_confidence = "low"

    reason_bits = [
        f"strict_method={strict_method}",
        f"window_start={window_start.date().isoformat()}",
        f"first_warning={first_warning_date.date().isoformat() if pd.notna(first_warning_date) else 'none'}",
        f"recovery_reset={'yes' if recovery_reset else 'no'}",
        f"shadow_frac={shadow_fraction if pd.notna(shadow_fraction) else 'nan'}",
        f"group_off_frac={group_off_fraction if pd.notna(group_off_fraction) else 'nan'}",
    ]

    return {
        "site": site,
        "panel_id": panel_id,
        "strict_trigger_date": strict_trigger_date.date().isoformat(),
        "first_warning_date": first_warning_date.date().isoformat() if pd.notna(first_warning_date) else "",
        "retrospective_onset_date": onset_date.date().isoformat(),
        "days_earlier_than_trigger": days_earlier,
        "onset_confidence": onset_confidence,
        "onset_method": onset_method,
        "shadow_like_fraction": shadow_fraction,
        "group_off_like_fraction": group_off_fraction,
        "reason_summary": "|".join(reason_bits),
        "_recovery_break_inconsistency": recovery_break_inconsistency,
    }


def build_site_rows(root: Path, site: str, lookback_days: int) -> list[dict[str, object]]:
    status_df = read_csv(preferred_status_path(root, site))
    if "panel_id" not in status_df.columns:
        raise SystemExit(f"latest panel status missing panel_id for {site}")
    strict_cases = status_df.loc[strict_case_mask(status_df)].copy()
    strict_cases["panel_id"] = strict_cases["panel_id"].map(normalize_text)
    strict_cases = strict_cases.loc[strict_cases["panel_id"].ne("")]

    core_path = root / "data" / site / "out" / "panel_day_core.csv"
    core_df = read_csv(core_path)
    if "panel_id" not in core_df.columns or "date" not in core_df.columns:
        raise SystemExit(f"panel_day_core.csv missing panel_id/date for {site}")
    core_df["panel_id"] = core_df["panel_id"].map(normalize_text)

    rows: list[dict[str, object]] = []
    for strict_case in strict_cases.itertuples(index=False):
        panel_id = normalize_text(strict_case.panel_id)
        panel_df = core_df.loc[core_df["panel_id"].eq(panel_id)].copy()
        if panel_df.empty:
            continue
        strict_trigger_date, strict_method = strict_trigger_from_panel_core(panel_df, pd.Series(strict_case._asdict()))
        rows.append(
            analyze_strict_case(
                site=site,
                panel_id=panel_id,
                panel_df=panel_df,
                strict_trigger_date=strict_trigger_date,
                strict_method=strict_method,
                lookback_days=lookback_days,
            )
        )
    return rows


def build_summary(rows_df: pd.DataFrame, strict_case_counts: dict[str, int], sites: list[str]) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for site in sites:
        subset = rows_df.loc[rows_df["site"].eq(site)].copy()
        records.append(
            {
                "site": site,
                "strict_cases": int(strict_case_counts.get(site, 0)),
                "shadow_rows": int(len(subset)),
                "median_days_earlier": median_or_nan(subset["days_earlier_than_trigger"]),
                "p90_days_earlier": quantile_or_nan(subset["days_earlier_than_trigger"], 0.9),
                "high_conf_count": int(subset["onset_confidence"].eq("high").sum()),
                "medium_conf_count": int(subset["onset_confidence"].eq("medium").sum()),
                "low_conf_count": int(subset["onset_confidence"].eq("low").sum()),
            }
        )
    return pd.DataFrame(records, columns=SUMMARY_COLS)


def build_suspicious(rows_df: pd.DataFrame, lookback_days: int) -> pd.DataFrame:
    suspicious_rows: list[dict[str, object]] = []
    for row in rows_df.to_dict(orient="records"):
        reasons: list[str] = []
        days_earlier = pd.to_numeric(row.get("days_earlier_than_trigger"), errors="coerce")
        shadow_fraction = pd.to_numeric(row.get("shadow_like_fraction"), errors="coerce")
        group_fraction = pd.to_numeric(row.get("group_off_like_fraction"), errors="coerce")
        if pd.notna(days_earlier) and float(days_earlier) > lookback_days:
            reasons.append("days_earlier_gt_lookback")
        if row.get("onset_confidence") == "low":
            reasons.append("low_confidence")
        if row.get("_recovery_break_inconsistency"):
            reasons.append("recovery_break_inconsistency")
        if (pd.notna(shadow_fraction) and float(shadow_fraction) >= 0.50) or (pd.notna(group_fraction) and float(group_fraction) >= 0.50):
            reasons.append("high_confound_fraction")
        if reasons:
            emitted = {key: row.get(key, "") for key in STRICT_OUTPUT_COLS}
            emitted["suspicious_reason"] = "|".join(reasons)
            suspicious_rows.append(emitted)
    return pd.DataFrame(suspicious_rows, columns=SUSPICIOUS_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    sites = list(args.sites)
    share_dir = root / "_share"

    all_rows: list[dict[str, object]] = []
    strict_case_counts: dict[str, int] = {}
    for site in sites:
        status_df = read_csv(preferred_status_path(root, site))
        strict_case_counts[site] = int(strict_case_mask(status_df).sum())
        all_rows.extend(build_site_rows(root, site, args.lookback_days))

    rows_df = pd.DataFrame(all_rows)
    if rows_df.empty:
        rows_df = pd.DataFrame(columns=STRICT_OUTPUT_COLS + ["_recovery_break_inconsistency"])

    latest_df = rows_df.loc[:, STRICT_OUTPUT_COLS].copy()
    summary_df = build_summary(rows_df, strict_case_counts, sites)
    suspicious_df = build_suspicious(rows_df, args.lookback_days)

    latest_df.to_csv(share_dir / "panel_onset_shadow_latest.csv", index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / "panel_onset_shadow_summary.csv", index=False, encoding="utf-8-sig")
    suspicious_df.to_csv(share_dir / "panel_onset_shadow_suspicious.csv", index=False, encoding="utf-8-sig")

    print(f"shadow_rows={len(latest_df)}")
    print(f"suspicious_rows={len(suspicious_df)}")


if __name__ == "__main__":
    main()
