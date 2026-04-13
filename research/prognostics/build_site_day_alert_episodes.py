#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

FRAME_COLS = [
    "site",
    "date",
    "score_window_flag",
    "weather_confound_flag_calc",
    "event_within_1d",
    "event_within_3d",
    "event_within_7d",
    "eligible_1d",
    "eligible_3d",
    "eligible_7d",
    "next_event_date",
    "next_review_group",
]
RISK_COLS = [
    "site",
    "date",
    "risk_score_heuristic",
    "risk_band",
]
GROUP_COLS = [
    "site",
    "review_group",
    "representative_date",
]
EPISODE_COLS = [
    "site",
    "trigger_mode",
    "episode_id",
    "episode_start_date",
    "episode_end_date",
    "duration_days",
    "n_alert_days",
    "peak_risk_score",
    "peak_risk_band",
    "peak_date",
    "eligible_1d",
    "eligible_3d",
    "eligible_7d",
    "matched_event_within_1d",
    "matched_event_within_3d",
    "matched_event_within_7d",
    "next_event_date",
    "matched_review_group",
    "lead_days_from_start",
    "lead_days_from_peak",
    "weather_confound_any",
    "weather_confound_all",
]
SUMMARY_COLS = [
    "site",
    "trigger_mode",
    "total_episodes",
    "eligible_episodes_1d",
    "eligible_episodes_3d",
    "eligible_episodes_7d",
    "matched_episodes_1d",
    "matched_episodes_3d",
    "matched_episodes_7d",
    "matched_rate_1d",
    "matched_rate_3d",
    "matched_rate_7d",
    "false_episodes_7d",
    "median_duration_days",
    "median_lead_days_from_start",
    "median_lead_days_from_peak",
    "alert_days",
    "compression_ratio",
]
TRIGGER_MODES = ("high_only", "medium_or_higher")
GAP_TOLERANCE_DAYS = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compress site-day risk outputs into alert episodes.")
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


def safe_rate(numer: int, denom: int) -> float:
    if denom == 0:
        return float("nan")
    return round(float(numer) / float(denom), 6)


def median_or_nan(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return float("nan")
    return round(float(numeric.median()), 6)


def trigger_mask(risk: pd.DataFrame, trigger_mode: str) -> pd.Series:
    if trigger_mode == "high_only":
        return risk["risk_band"].eq("high")
    if trigger_mode == "medium_or_higher":
        return risk["risk_band"].isin(["high", "medium"])
    raise ValueError(f"unsupported trigger_mode: {trigger_mode}")


def build_group_lookup(groups: pd.DataFrame) -> dict[tuple[str, str], str]:
    lookup: dict[tuple[str, str], str] = {}
    for row in groups.itertuples(index=False):
        lookup[(str(row.site).strip(), str(row.review_group).strip())] = str(row.representative_date).strip()
    return lookup


def match_group(site: str, review_group: str, start_row: pd.Series, group_lookup: dict[tuple[str, str], str]) -> tuple[str, str]:
    canonical_group = review_group.strip()
    if not canonical_group:
        return "", ""
    canonical_date = group_lookup.get((site, canonical_group), "")
    if canonical_date:
        return canonical_date, canonical_group
    fallback_date = str(start_row.get("next_event_date", "") or "").strip()
    return fallback_date, canonical_group


def lead_days(next_event_date: str, anchor_date: pd.Timestamp) -> float:
    next_date = pd.to_datetime(next_event_date, errors="coerce")
    if pd.isna(next_date) or pd.isna(anchor_date):
        return float("nan")
    return float((next_date - anchor_date).days)


def weather_confound_flags(episode: pd.DataFrame) -> tuple[object, object]:
    flags = episode["weather_confound_flag_calc"].map(normalize_optional_flag)
    valid = flags[flags.isin(["0", "1"])]
    if valid.empty:
        return "", ""
    any_flag = 1 if valid.eq("1").any() else 0
    all_flag = 1 if valid.eq("1").all() else 0
    return any_flag, all_flag


def episode_record(site: str, trigger_mode: str, episode_no: int, episode: pd.DataFrame, group_lookup: dict[tuple[str, str], str]) -> dict[str, object]:
    ordered = episode.sort_values("date_dt", kind="stable").copy()
    start_row = ordered.iloc[0]
    end_row = ordered.iloc[-1]
    peak_row = (
        ordered.sort_values(["risk_score_heuristic", "date_dt"], ascending=[False, True], kind="stable")
        .iloc[0]
    )

    matched_date, matched_group = match_group(
        site=str(start_row["site"]),
        review_group=str(start_row["next_review_group"] or ""),
        start_row=start_row,
        group_lookup=group_lookup,
    )
    start_dt = pd.to_datetime(start_row["date"], errors="coerce")
    end_dt = pd.to_datetime(end_row["date"], errors="coerce")
    peak_dt = pd.to_datetime(peak_row["date"], errors="coerce")
    weather_any, weather_all = weather_confound_flags(ordered)

    return {
        "site": site,
        "trigger_mode": trigger_mode,
        "episode_id": f"{episode_no:04d}",
        "episode_start_date": str(start_row["date"]),
        "episode_end_date": str(end_row["date"]),
        "duration_days": int((end_dt - start_dt).days + 1),
        "n_alert_days": int(len(ordered)),
        "peak_risk_score": round(float(peak_row["risk_score_heuristic"]), 6),
        "peak_risk_band": str(peak_row["risk_band"]),
        "peak_date": str(peak_row["date"]),
        "eligible_1d": int(start_row["eligible_1d"]),
        "eligible_3d": int(start_row["eligible_3d"]),
        "eligible_7d": int(start_row["eligible_7d"]),
        "matched_event_within_1d": int(start_row["event_within_1d"]),
        "matched_event_within_3d": int(start_row["event_within_3d"]),
        "matched_event_within_7d": int(start_row["event_within_7d"]),
        "next_event_date": matched_date,
        "matched_review_group": matched_group,
        "lead_days_from_start": lead_days(matched_date, start_dt),
        "lead_days_from_peak": lead_days(matched_date, peak_dt),
        "weather_confound_any": weather_any,
        "weather_confound_all": weather_all,
    }


def build_episodes(day_df: pd.DataFrame, groups: pd.DataFrame) -> pd.DataFrame:
    group_lookup = build_group_lookup(groups)
    rows: list[dict[str, object]] = []

    for site, site_days in day_df.groupby("site", sort=True):
        site_days = site_days.sort_values("date_dt", kind="stable").copy()
        for trigger_mode in TRIGGER_MODES:
            triggered = site_days.loc[trigger_mask(site_days, trigger_mode)].copy()
            if triggered.empty:
                continue

            episode_no = 0
            current_indices: list[int] = []
            previous_date: pd.Timestamp | None = None

            for idx, row in triggered.iterrows():
                current_date = row["date_dt"]
                start_new = previous_date is None or (current_date - previous_date).days > (GAP_TOLERANCE_DAYS + 1)
                if start_new and current_indices:
                    episode_no += 1
                    rows.append(episode_record(site, trigger_mode, episode_no, triggered.loc[current_indices], group_lookup))
                    current_indices = []
                current_indices.append(idx)
                previous_date = current_date

            if current_indices:
                episode_no += 1
                rows.append(episode_record(site, trigger_mode, episode_no, triggered.loc[current_indices], group_lookup))

    if not rows:
        return pd.DataFrame(columns=EPISODE_COLS)
    episodes = pd.DataFrame(rows)
    return episodes[EPISODE_COLS].copy()


def build_summary(day_df: pd.DataFrame, episodes: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    sites = sorted(day_df["site"].dropna().astype(str).unique().tolist())

    for site in sites:
        site_days = day_df.loc[day_df["site"].eq(site)].copy()
        for trigger_mode in TRIGGER_MODES:
            alert_days = int(trigger_mask(site_days, trigger_mode).sum())
            site_episodes = episodes.loc[
                episodes["site"].eq(site) & episodes["trigger_mode"].eq(trigger_mode)
            ].copy()

            summary_row: dict[str, object] = {
                "site": site,
                "trigger_mode": trigger_mode,
                "total_episodes": int(len(site_episodes)),
                "alert_days": alert_days,
                "compression_ratio": safe_rate(alert_days, int(len(site_episodes))),
                "median_duration_days": median_or_nan(site_episodes.get("duration_days", pd.Series(dtype=float))),
                "median_lead_days_from_start": median_or_nan(site_episodes.get("lead_days_from_start", pd.Series(dtype=float))),
                "median_lead_days_from_peak": median_or_nan(site_episodes.get("lead_days_from_peak", pd.Series(dtype=float))),
            }

            for horizon in ["1d", "3d", "7d"]:
                eligible_col = f"eligible_{horizon}"
                matched_col = f"matched_event_within_{horizon}"
                eligible_mask = pd.to_numeric(site_episodes.get(eligible_col, pd.Series(dtype=float)), errors="coerce").fillna(0).eq(1)
                eligible_count = int(eligible_mask.sum())
                matched_count = int(pd.to_numeric(site_episodes.loc[eligible_mask, matched_col], errors="coerce").fillna(0).sum()) if not site_episodes.empty else 0
                summary_row[f"eligible_episodes_{horizon}"] = eligible_count
                summary_row[f"matched_episodes_{horizon}"] = matched_count
                summary_row[f"matched_rate_{horizon}"] = safe_rate(matched_count, eligible_count)

            summary_row["false_episodes_7d"] = (
                int(summary_row["eligible_episodes_7d"]) - int(summary_row["matched_episodes_7d"])
            )
            rows.append(summary_row)

    if not rows:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary = pd.DataFrame(rows)
    return summary[SUMMARY_COLS].copy()


def build_outputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    share_dir = root / "_share"
    frame_path = share_dir / "site_day_event_frame_latest.csv"
    risk_path = share_dir / "site_day_event_risk_latest.csv"
    groups_path = share_dir / "site_event_groups_latest.csv"

    frame = ensure_columns(read_csv(frame_path), FRAME_COLS, str(frame_path))[FRAME_COLS].copy()
    risk = ensure_columns(read_csv(risk_path), RISK_COLS, str(risk_path))[RISK_COLS].copy()
    groups = ensure_columns(read_csv(groups_path), GROUP_COLS, str(groups_path))[GROUP_COLS].copy()

    frame["site"] = normalized_text(frame["site"])
    frame["date"] = normalized_text(frame["date"])
    risk["site"] = normalized_text(risk["site"])
    risk["date"] = normalized_text(risk["date"])
    groups["site"] = normalized_text(groups["site"])
    groups["review_group"] = normalized_text(groups["review_group"])
    groups["representative_date"] = normalized_text(groups["representative_date"])

    day_df = frame.merge(risk, on=["site", "date"], how="inner", validate="one_to_one")
    day_df["date_dt"] = pd.to_datetime(day_df["date"], errors="coerce")
    for col in [
        "event_within_1d",
        "event_within_3d",
        "event_within_7d",
        "eligible_1d",
        "eligible_3d",
        "eligible_7d",
    ]:
        day_df[col] = pd.to_numeric(day_df[col], errors="coerce").fillna(0).astype(int)
    day_df["risk_score_heuristic"] = pd.to_numeric(day_df["risk_score_heuristic"], errors="coerce")
    day_df["risk_band"] = normalized_text(day_df["risk_band"])
    day_df["next_review_group"] = normalized_text(day_df["next_review_group"])
    day_df["next_event_date"] = normalized_text(day_df["next_event_date"])
    day_df["weather_confound_flag_calc"] = day_df["weather_confound_flag_calc"].map(normalize_optional_flag)
    day_df = day_df.sort_values(["site", "date_dt"], kind="stable").reset_index(drop=True)

    episodes = build_episodes(day_df, groups)
    summary = build_summary(day_df, episodes)
    return episodes, summary


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    episodes, summary = build_outputs(root)
    episodes.to_csv(share_dir / "site_day_alert_episodes_latest.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / "site_day_alert_episode_summary.csv", index=False, encoding="utf-8-sig")

    if episodes.empty:
        print("episode_rows=0")
    else:
        counts = episodes["trigger_mode"].value_counts().sort_index()
        print(f"episode_rows={len(episodes)}")
        print(counts.to_string())


if __name__ == "__main__":
    main()
