#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

WEATHER_COLS = [
    "site",
    "date",
    "score_window_flag",
    "weather_available",
    "weather_tag",
    "sun_hours",
    "rain_flag",
    "cloud_flag",
    "weather_confidence",
    "weather_source",
    "weather_missing_reason",
    "note",
]
EVENT_DATASET_COLS = [
    "site",
    "review_group",
    "representative_date",
    "event_confidence_level",
]
FRAME_COLS = [
    "site",
    "date",
    "score_window_flag",
    "weather_available",
    "weather_tag",
    "rain_flag",
    "cloud_flag",
    "weather_confound_flag_calc",
    "event_today",
    "event_within_1d",
    "event_within_3d",
    "event_within_7d",
    "eligible_1d",
    "eligible_3d",
    "eligible_7d",
    "next_event_date",
    "next_review_group",
    "next_event_confidence_level",
    "future_event_low_confidence_flag",
    "site_alert_count_today",
    "site_online_diag_count_today",
    "site_critical_count_today",
    "site_dead_count_today",
    "site_final_fault_count_today",
    "site_new_alerts_today",
    "site_resolved_alerts_today",
    "days_since_last_event",
    "recent_event_count_30d",
]
RISK_COLS = FRAME_COLS + ["risk_score_heuristic", "risk_band"]


def positive_rate_or_nan(df: pd.DataFrame, label_col: str) -> float:
    if df.empty:
        return float("nan")
    return round(float(df[label_col].mean()), 6)


def safe_rate(numer: int, denom: int) -> float:
    if denom == 0:
        return float("nan")
    return round(float(numer) / float(denom), 6)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build site-day event frame and weak heuristic event-risk baseline.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, expected: list[str], name: str) -> pd.DataFrame:
    missing = [col for col in expected if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")
    return df.copy()


def normalized_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def normalize_optional_flag(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    try:
        as_float = float(text)
    except ValueError:
        return text
    if as_float.is_integer():
        return str(int(as_float))
    return text


def calc_weather_confound(row: pd.Series) -> str:
    if int(row["weather_available"]) == 0:
        return ""
    rain_flag = normalize_optional_flag(row["rain_flag"])
    cloud_flag = normalize_optional_flag(row["cloud_flag"])
    weather_tag = str(row["weather_tag"] or "").strip().lower()
    if rain_flag == "1":
        return "1"
    if weather_tag in {"cloudy", "mixed"} and cloud_flag == "1":
        return "1"
    return "0"


def load_site_rollups(root: Path, sites: list[str]) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    column_map = {
        "alert_count": "site_alert_count_today",
        "online_diag_count": "site_online_diag_count_today",
        "critical_count": "site_critical_count_today",
        "dead_count": "site_dead_count_today",
        "final_fault_count": "site_final_fault_count_today",
        "new_alert_count": "site_new_alerts_today",
        "resolved_alert_count": "site_resolved_alerts_today",
    }
    target_cols = ["site", "date"] + list(column_map.values())

    for site in sites:
        path = root / "data" / site / "out" / "site_daily_rollup.csv"
        if not path.exists():
            continue
        rollup = read_csv(path)
        if "snapshot_date" not in rollup.columns:
            continue
        if "site" in rollup.columns:
            rollup["site"] = normalized_text(rollup["site"])
            rollup = rollup.loc[rollup["site"].eq(site)].copy()
        else:
            rollup["site"] = site
        if rollup.empty:
            continue
        rollup["date"] = normalized_text(rollup["snapshot_date"])
        keep = rollup[["site", "date"]].copy()
        for source_col, target_col in column_map.items():
            if source_col in rollup.columns:
                keep[target_col] = pd.to_numeric(rollup[source_col], errors="coerce").fillna(0).astype(int)
            else:
                keep[target_col] = 0
        keep = keep.groupby(["site", "date"], dropna=False, as_index=False).sum(numeric_only=True)
        rows.append(keep[target_cols])

    if not rows:
        return pd.DataFrame(columns=target_cols)
    combined = pd.concat(rows, ignore_index=True)
    for col in target_cols[2:]:
        combined[col] = pd.to_numeric(combined[col], errors="coerce").fillna(0).astype(int)
    return combined[target_cols]


def attach_event_labels(frame: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    results: list[pd.DataFrame] = []

    for site, site_frame in frame.groupby("site", sort=False):
        site_frame = site_frame.sort_values("date", kind="stable").copy()
        site_events = events.loc[
            events["site"].eq(site),
            ["review_group", "representative_date", "event_confidence_level"],
        ].copy()
        site_events = site_events.sort_values("representative_date", kind="stable").reset_index(drop=True)
        event_dates = pd.to_datetime(site_events["representative_date"], errors="coerce")

        event_today: list[int] = []
        event_within_1d: list[int] = []
        event_within_3d: list[int] = []
        event_within_7d: list[int] = []
        eligible_1d: list[int] = []
        eligible_3d: list[int] = []
        eligible_7d: list[int] = []
        next_event_date: list[str] = []
        next_review_group: list[str] = []
        next_event_confidence_level: list[str] = []
        future_event_low_confidence_flag: list[object] = []
        days_since_last_event: list[float] = []
        recent_event_count_30d: list[int] = []

        for current_str in site_frame["date"].tolist():
            current_date = pd.to_datetime(current_str, errors="coerce")
            if pd.isna(current_date):
                event_today.append(0)
                event_within_1d.append(0)
                event_within_3d.append(0)
                event_within_7d.append(0)
                eligible_1d.append(0)
                eligible_3d.append(0)
                eligible_7d.append(0)
                next_event_date.append("")
                next_review_group.append("")
                next_event_confidence_level.append("")
                future_event_low_confidence_flag.append("")
                days_since_last_event.append(float("nan"))
                recent_event_count_30d.append(0)
                continue

            deltas = (event_dates - current_date).dt.days
            past_mask = deltas < 0
            future_mask = deltas > 0
            site_latest_raw_date = pd.to_datetime(site_frame["date"].iloc[-1], errors="coerce")

            event_today.append(int((deltas == 0).any()))
            event_within_1d.append(int(((deltas > 0) & (deltas <= 1)).any()))
            event_within_3d.append(int(((deltas > 0) & (deltas <= 3)).any()))
            event_within_7d.append(int(((deltas > 0) & (deltas <= 7)).any()))
            eligible_1d.append(int(current_date + pd.Timedelta(days=1) <= site_latest_raw_date))
            eligible_3d.append(int(current_date + pd.Timedelta(days=3) <= site_latest_raw_date))
            eligible_7d.append(int(current_date + pd.Timedelta(days=7) <= site_latest_raw_date))

            next_idx = future_mask.idxmax() if future_mask.any() else None
            if next_idx is not None and future_mask.any():
                next_event_date.append(site_events.loc[next_idx, "representative_date"])
                next_review_group.append(site_events.loc[next_idx, "review_group"])
                confidence = str(site_events.loc[next_idx, "event_confidence_level"] or "").strip()
                next_event_confidence_level.append(confidence)
                future_event_low_confidence_flag.append(1 if confidence == "low" else 0)
            else:
                next_event_date.append("")
                next_review_group.append("")
                next_event_confidence_level.append("")
                future_event_low_confidence_flag.append("")

            if past_mask.any():
                last_event_date = event_dates.loc[past_mask].max()
                days_since_last_event.append(float((current_date - last_event_date).days))
                recent_event_count_30d.append(int(((deltas < 0) & (deltas >= -30)).sum()))
            else:
                days_since_last_event.append(float("nan"))
                recent_event_count_30d.append(0)

        site_frame["event_today"] = event_today
        site_frame["event_within_1d"] = event_within_1d
        site_frame["event_within_3d"] = event_within_3d
        site_frame["event_within_7d"] = event_within_7d
        site_frame["eligible_1d"] = eligible_1d
        site_frame["eligible_3d"] = eligible_3d
        site_frame["eligible_7d"] = eligible_7d
        site_frame["next_event_date"] = next_event_date
        site_frame["next_review_group"] = next_review_group
        site_frame["next_event_confidence_level"] = next_event_confidence_level
        site_frame["future_event_low_confidence_flag"] = future_event_low_confidence_flag
        site_frame["days_since_last_event"] = days_since_last_event
        site_frame["recent_event_count_30d"] = recent_event_count_30d
        results.append(site_frame)

    combined = pd.concat(results, ignore_index=True)
    for col in [
        "event_today",
        "event_within_1d",
        "event_within_3d",
        "event_within_7d",
        "eligible_1d",
        "eligible_3d",
        "eligible_7d",
        "recent_event_count_30d",
    ]:
        combined[col] = pd.to_numeric(combined[col], errors="coerce").fillna(0).astype(int)
    return combined


def heuristic_score(row: pd.Series) -> float:
    score = 0.02
    score += min(int(row["site_alert_count_today"]), 50) * 0.003
    score += min(int(row["site_online_diag_count_today"]), 20) * 0.010
    score += min(int(row["site_critical_count_today"]), 20) * 0.012
    score += min(int(row["site_dead_count_today"]), 20) * 0.012
    score += min(int(row["site_final_fault_count_today"]), 10) * 0.010
    score += min(int(row["site_new_alerts_today"]), 30) * 0.005
    score -= min(int(row["site_resolved_alerts_today"]), 30) * 0.003

    days_since = row["days_since_last_event"]
    if pd.notna(days_since):
        if days_since <= 3:
            score += 0.20
        elif days_since <= 7:
            score += 0.12
        elif days_since <= 30:
            score += 0.06

    score += min(int(row["recent_event_count_30d"]), 5) * 0.03
    if str(row["weather_confound_flag_calc"]).strip() == "1":
        score += 0.03
    return round(max(0.0, min(score, 1.0)), 6)


def heuristic_band(score: float, q90: float, q98: float) -> str:
    if score >= q98:
        return "high"
    if score >= q90:
        return "medium"
    return "low"


def compute_band_thresholds(risk: pd.DataFrame) -> tuple[float, float]:
    eligible_any = risk[["eligible_1d", "eligible_3d", "eligible_7d"]].eq(1).any(axis=1)
    eligible_scores = risk.loc[eligible_any, "risk_score_heuristic"]
    if eligible_scores.empty:
        eligible_scores = risk["risk_score_heuristic"]
    q90 = round(float(eligible_scores.quantile(0.90)), 6)
    q98 = round(float(eligible_scores.quantile(0.98)), 6)
    return q90, q98


def summarize_band_rate(risk: pd.DataFrame, mask: pd.Series, eligible_col: str, label_col: str) -> tuple[int, float]:
    eligible_mask = mask & risk[eligible_col].eq(1)
    denom = int(eligible_mask.sum())
    numer = int(risk.loc[eligible_mask, label_col].sum())
    return denom, safe_rate(numer, denom)


def build_outputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    share_dir = root / "_share"
    weather_path = share_dir / "site_weather_history_latest.csv"
    events_path = share_dir / "site_event_dataset_latest.csv"

    weather = ensure_columns(read_csv(weather_path), WEATHER_COLS, str(weather_path))[WEATHER_COLS].copy()
    events = ensure_columns(read_csv(events_path), EVENT_DATASET_COLS, str(events_path))[EVENT_DATASET_COLS].copy()

    weather["site"] = normalized_text(weather["site"])
    weather["date"] = normalized_text(weather["date"])
    weather["weather_available"] = pd.to_numeric(weather["weather_available"], errors="coerce").fillna(0).astype(int)
    weather["weather_tag"] = normalized_text(weather["weather_tag"])
    weather["rain_flag"] = weather["rain_flag"].fillna("")
    weather["cloud_flag"] = weather["cloud_flag"].fillna("")
    weather["weather_confound_flag_calc"] = weather.apply(calc_weather_confound, axis=1)

    frame = weather[
        [
            "site",
            "date",
            "score_window_flag",
            "weather_available",
            "weather_tag",
            "rain_flag",
            "cloud_flag",
            "weather_confound_flag_calc",
        ]
    ].copy()

    sites = sorted(frame["site"].dropna().astype(str).unique().tolist())
    rollups = load_site_rollups(root, sites)
    frame = frame.merge(rollups, on=["site", "date"], how="left")
    for col in [
        "site_alert_count_today",
        "site_online_diag_count_today",
        "site_critical_count_today",
        "site_dead_count_today",
        "site_final_fault_count_today",
        "site_new_alerts_today",
        "site_resolved_alerts_today",
    ]:
        if col not in frame.columns:
            frame[col] = 0
        frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0).astype(int)

    events["site"] = normalized_text(events["site"])
    events["review_group"] = normalized_text(events["review_group"])
    events["representative_date"] = normalized_text(events["representative_date"])
    events["event_confidence_level"] = normalized_text(events["event_confidence_level"])
    frame = attach_event_labels(frame, events)
    frame = frame.sort_values(["site", "date"], kind="stable").reset_index(drop=True)
    frame = frame[FRAME_COLS].copy()

    risk = frame.copy()
    risk["risk_score_heuristic"] = risk.apply(heuristic_score, axis=1)
    q90, q98 = compute_band_thresholds(risk)
    risk["risk_band"] = risk["risk_score_heuristic"].apply(lambda score: heuristic_band(float(score), q90, q98))
    risk = risk[RISK_COLS].copy()

    summary = {
        "risk_band_q90": q90,
        "risk_band_q98": q98,
        "total_days": int(len(risk)),
        "eligible_days_1d": int(risk["eligible_1d"].sum()),
        "eligible_days_3d": int(risk["eligible_3d"].sum()),
        "eligible_days_7d": int(risk["eligible_7d"].sum()),
        "positive_days_1d": int(risk["event_within_1d"].sum()),
        "positive_days_3d": int(risk["event_within_3d"].sum()),
        "positive_days_7d": int(risk["event_within_7d"].sum()),
    }
    for band in ["high", "medium", "low"]:
        mask = risk["risk_band"].eq(band)
        days = int(mask.sum())
        summary[f"{band}_days"] = days
        eligible_days_1d, rate_1d = summarize_band_rate(risk, mask, "eligible_1d", "event_within_1d")
        eligible_days_3d, rate_3d = summarize_band_rate(risk, mask, "eligible_3d", "event_within_3d")
        eligible_days_7d, rate_7d = summarize_band_rate(risk, mask, "eligible_7d", "event_within_7d")
        summary[f"{band}_eligible_days_1d"] = eligible_days_1d
        summary[f"{band}_eligible_days_3d"] = eligible_days_3d
        summary[f"{band}_eligible_days_7d"] = eligible_days_7d
        summary[f"{band}_positive_rate_1d"] = rate_1d
        summary[f"{band}_positive_rate_3d"] = rate_3d
        summary[f"{band}_positive_rate_7d"] = rate_7d
    summary_df = pd.DataFrame([summary])

    return frame, risk, summary_df


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    frame, risk, summary = build_outputs(root)
    frame.to_csv(share_dir / "site_day_event_frame_latest.csv", index=False, encoding="utf-8-sig")
    risk.to_csv(share_dir / "site_day_event_risk_latest.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / "site_day_event_risk_summary.csv", index=False, encoding="utf-8-sig")

    q90 = float(summary.loc[0, "risk_band_q90"])
    q98 = float(summary.loc[0, "risk_band_q98"])
    print(f"site_day_event_frame_rows={len(frame)}")
    print(f"risk_band_q90={q90}")
    print(f"risk_band_q98={q98}")
    print(f"positive_days_1d={int(frame['event_within_1d'].sum())}")
    print(f"positive_days_3d={int(frame['event_within_3d'].sum())}")
    print(f"positive_days_7d={int(frame['event_within_7d'].sum())}")
    print(risk["risk_band"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
