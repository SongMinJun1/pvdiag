#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
TIER_ORDER = ["broad_3g_10p", "medium_2g_5p", "narrow_1g_3p"]
TIER_RULES = {
    "broad_3g_10p": {
        "qualifying_group_cluster_count": 3,
        "total_panels_in_qualifying_groups": 10,
    },
    "medium_2g_5p": {
        "qualifying_group_cluster_count": 2,
        "total_panels_in_qualifying_groups": 5,
    },
    "narrow_1g_3p": {
        "qualifying_group_cluster_count": 1,
        "max_group_cluster_size": 3,
    },
}
SUMMARY_COLS = [
    "tier_id",
    "candidate_day_count",
    "exact_same_day_episode_count",
    "in_episode_window_count",
    "lead_1_to_3_days_count",
    "lead_4_to_7_days_count",
    "no_episode_within_7d_count",
    "exact_same_day_event_count",
    "lead_1_to_3_precision",
    "lead_1_to_7_precision",
    "exact_or_lead_1_to_3_precision",
    "matched_episode_count",
    "episodes_with_lead_1_to_3_count",
    "episode_lead_1_to_3_recall",
    "total_target_episode_count",
    "episode_filter_used",
]
CANDIDATE_COLS = [
    "tier_id",
    "site",
    "date",
    "total_panel_rows",
    "zero_like_panel_count",
    "group_like_zero_like_panel_count",
    "qualifying_group_cluster_count",
    "max_group_cluster_size",
    "total_panels_in_qualifying_groups",
    "qualifying_group_panel_share",
    "exact_same_day_event_flag",
    "exact_event_column_used",
    "matched_episode_id",
    "matched_trigger_mode",
    "matched_episode_start_date",
    "matched_episode_end_date",
    "days_to_episode_start",
    "days_to_episode_end",
    "precursor_timing_type",
]
EPISODE_MATCH_COLS = [
    "tier_id",
    "site",
    "matched_episode_id",
    "matched_trigger_mode",
    "matched_episode_start_date",
    "candidate_day_count_for_episode",
    "earliest_candidate_date",
    "latest_candidate_date",
    "best_lead_days",
    "has_exact_same_day_candidate",
    "has_lead_1_to_3_candidate",
    "has_lead_4_to_7_candidate",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit whether same-group common-cause precursor days generalize across full site-day history."
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
        help="Sites to inspect. Defaults to the stable known sites.",
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


def safe_div(numer: int | float, denom: int | float) -> float:
    if denom <= 0:
        return 0.0
    return round(float(numer / denom), 6)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def fallback_group_key(panel_id: object) -> str:
    parts = normalize_text(panel_id).split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return normalize_text(panel_id)


def detect_exact_event_column(columns: list[str]) -> str:
    for col in ["event_day_flag", "site_event_flag", "event_flag"]:
        if col in columns:
            return col
    return ""


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


def build_panel_day_rows(root: Path, sites: list[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    required = ["date", "panel_id", "mid_ratio", "mid_i_ratio", "mid_v_ratio", "coverage_mid"]
    for site in sites:
        path = root / "data" / site / "out" / "panel_day_core.csv"
        df = read_csv(path)
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise SystemExit(f"panel_day_core.csv missing columns for site={site}: {missing}")

        df["site"] = site
        df["date"] = df["date"].map(normalize_date)
        df["panel_id"] = df["panel_id"].map(normalize_text)
        if "group_key_base" not in df.columns:
            df["group_key_base"] = ""
        df["group_key_base"] = df["group_key_base"].map(normalize_text)
        missing_group = df["group_key_base"].eq("")
        df.loc[missing_group, "group_key_base"] = df.loc[missing_group, "panel_id"].map(fallback_group_key)

        for col in ["mid_ratio", "mid_i_ratio", "mid_v_ratio", "coverage_mid"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["zero_like_flag"] = (
            df["mid_ratio"].le(0.10)
            & df["mid_i_ratio"].le(0.10)
            & df["coverage_mid"].ge(0.50)
        ).fillna(False).astype(int)
        df["group_like_zero_like_flag"] = (
            df["zero_like_flag"].eq(1) & df["mid_v_ratio"].ge(1.05)
        ).fillna(False).astype(int)

        frames.append(
            df.loc[
                :,
                [
                    "site",
                    "date",
                    "panel_id",
                    "group_key_base",
                    "zero_like_flag",
                    "group_like_zero_like_flag",
                ],
            ].rename(columns={"group_key_base": "fallback_group_proxy"})
        )

    if not frames:
        return pd.DataFrame(
            columns=["site", "date", "panel_id", "fallback_group_proxy", "zero_like_flag", "group_like_zero_like_flag"]
        )
    return pd.concat(frames, ignore_index=True)


def aggregate_site_days(panel_days: pd.DataFrame) -> pd.DataFrame:
    site_day = panel_days.groupby(["site", "date"], as_index=False).agg(
        total_panel_rows=("panel_id", "size"),
        zero_like_panel_count=("zero_like_flag", "sum"),
        group_like_zero_like_panel_count=("group_like_zero_like_flag", "sum"),
    )

    qualifying_groups = (
        panel_days.loc[panel_days["group_like_zero_like_flag"].eq(1)]
        .groupby(["site", "date", "fallback_group_proxy"], as_index=False)
        .agg(group_cluster_size=("panel_id", "size"))
    )
    qualifying_groups = qualifying_groups.loc[qualifying_groups["group_cluster_size"].ge(2)].copy()

    qualifying_day = qualifying_groups.groupby(["site", "date"], as_index=False).agg(
        qualifying_group_cluster_count=("fallback_group_proxy", "size"),
        max_group_cluster_size=("group_cluster_size", "max"),
        total_panels_in_qualifying_groups=("group_cluster_size", "sum"),
    )

    aggregated = site_day.merge(qualifying_day, on=["site", "date"], how="left")
    for col in ["qualifying_group_cluster_count", "max_group_cluster_size", "total_panels_in_qualifying_groups"]:
        aggregated[col] = pd.to_numeric(aggregated[col], errors="coerce").fillna(0).astype(int)
    aggregated["qualifying_group_panel_share"] = aggregated.apply(
        lambda row: safe_div(row["total_panels_in_qualifying_groups"], row["total_panel_rows"]),
        axis=1,
    )
    return aggregated


def select_tier_candidates(aggregated: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for tier_id in TIER_ORDER:
        rule = TIER_RULES[tier_id]
        mask = aggregated["qualifying_group_cluster_count"].ge(rule["qualifying_group_cluster_count"])
        if "total_panels_in_qualifying_groups" in rule:
            mask &= aggregated["total_panels_in_qualifying_groups"].ge(rule["total_panels_in_qualifying_groups"])
        if "max_group_cluster_size" in rule:
            mask &= aggregated["max_group_cluster_size"].ge(rule["max_group_cluster_size"])
        tier_df = aggregated.loc[mask].copy()
        tier_df["tier_id"] = tier_id
        rows.append(tier_df)

    if not rows:
        return pd.DataFrame(columns=CANDIDATE_COLS)
    return pd.concat(rows, ignore_index=True)


def prepare_episodes(root: Path, sites: list[str]) -> tuple[pd.DataFrame, str, int]:
    episodes = read_csv(root / "_share" / "site_day_alert_episodes_latest.csv")
    episodes["site"] = episodes["site"].map(normalize_text)
    episodes = episodes.loc[episodes["site"].isin(sites)].copy()
    for col in ["trigger_mode", "episode_id"]:
        if col not in episodes.columns:
            episodes[col] = ""
        episodes[col] = episodes[col].map(normalize_text)
    for col in ["episode_start_date", "episode_end_date"]:
        if col not in episodes.columns:
            raise SystemExit("site_day_alert_episodes_latest.csv missing episode boundary columns")
        episodes[col] = episodes[col].map(normalize_date)

    if episodes["trigger_mode"].eq("medium_or_higher").any():
        filtered = episodes.loc[episodes["trigger_mode"].eq("medium_or_higher")].copy()
        episode_filter_used = "medium_or_higher_only"
    else:
        filtered = episodes.copy()
        episode_filter_used = "all_episodes"

    total_target_episode_count = int(filtered["episode_id"].nunique())
    return filtered, episode_filter_used, total_target_episode_count


def prepare_exact_event_context(root: Path, sites: list[str]) -> tuple[pd.DataFrame, str]:
    path = root / "_share" / "site_day_event_frame_latest.csv"
    if not path.exists():
        return pd.DataFrame(columns=["site", "date", "exact_same_day_event_flag"]), ""

    frame = read_csv(path)
    frame["site"] = frame["site"].map(normalize_text)
    frame["date"] = frame["date"].map(normalize_date)
    frame = frame.loc[frame["site"].isin(sites)].copy()
    exact_col = detect_exact_event_column(list(frame.columns))
    if not exact_col:
        return pd.DataFrame(columns=["site", "date", "exact_same_day_event_flag"]), ""
    frame["exact_same_day_event_flag"] = frame[exact_col].map(to_int_flag)
    frame = frame.loc[:, ["site", "date", "exact_same_day_event_flag"]].drop_duplicates(subset=["site", "date"], keep="first").copy()
    return frame, exact_col


def best_episode_match(episodes: pd.DataFrame, site: str, date: str) -> dict[str, object]:
    blank = {
        "matched_episode_id": "",
        "matched_trigger_mode": "",
        "matched_episode_start_date": "",
        "matched_episode_end_date": "",
        "days_to_episode_start": "",
        "days_to_episode_end": "",
        "precursor_timing_type": "no_episode_within_7d",
    }
    target_ts = parse_date(date)
    if pd.isna(target_ts):
        return blank

    site_rows = episodes.loc[episodes["site"].eq(site)].copy()
    if site_rows.empty:
        return blank

    site_rows["start_ts"] = site_rows["episode_start_date"].map(parse_date)
    site_rows["end_ts"] = site_rows["episode_end_date"].map(parse_date)
    site_rows = site_rows.loc[site_rows["start_ts"].notna() & site_rows["end_ts"].notna()].copy()
    if site_rows.empty:
        return blank

    site_rows["days_to_start"] = (site_rows["start_ts"] - target_ts).dt.days
    site_rows["days_to_end"] = (site_rows["end_ts"] - target_ts).dt.days

    exact_start = site_rows.loc[site_rows["days_to_start"].eq(0)].sort_values(["episode_id"])
    if not exact_start.empty:
        chosen = exact_start.iloc[0]
        return {
            "matched_episode_id": normalize_text(chosen["episode_id"]),
            "matched_trigger_mode": normalize_text(chosen["trigger_mode"]),
            "matched_episode_start_date": normalize_text(chosen["episode_start_date"]),
            "matched_episode_end_date": normalize_text(chosen["episode_end_date"]),
            "days_to_episode_start": 0,
            "days_to_episode_end": int(chosen["days_to_end"]),
            "precursor_timing_type": "exact_same_day_episode",
        }

    in_window = site_rows.loc[(site_rows["days_to_start"] < 0) & (site_rows["days_to_end"] >= 0)].sort_values(
        ["days_to_end", "episode_id"]
    )
    if not in_window.empty:
        chosen = in_window.iloc[0]
        return {
            "matched_episode_id": normalize_text(chosen["episode_id"]),
            "matched_trigger_mode": normalize_text(chosen["trigger_mode"]),
            "matched_episode_start_date": normalize_text(chosen["episode_start_date"]),
            "matched_episode_end_date": normalize_text(chosen["episode_end_date"]),
            "days_to_episode_start": int(chosen["days_to_start"]),
            "days_to_episode_end": int(chosen["days_to_end"]),
            "precursor_timing_type": "in_episode_window",
        }

    future = site_rows.loc[site_rows["days_to_start"] > 0].sort_values(["days_to_start", "episode_id"])
    if not future.empty:
        chosen = future.iloc[0]
        lead_days = int(chosen["days_to_start"])
        timing = "no_episode_within_7d"
        if lead_days in {1, 2, 3}:
            timing = "lead_1_to_3_days"
        elif lead_days in {4, 5, 6, 7}:
            timing = "lead_4_to_7_days"
        return {
            "matched_episode_id": normalize_text(chosen["episode_id"]),
            "matched_trigger_mode": normalize_text(chosen["trigger_mode"]),
            "matched_episode_start_date": normalize_text(chosen["episode_start_date"]),
            "matched_episode_end_date": normalize_text(chosen["episode_end_date"]),
            "days_to_episode_start": lead_days,
            "days_to_episode_end": int(chosen["days_to_end"]),
            "precursor_timing_type": timing,
        }

    past = site_rows.assign(abs_days=site_rows["days_to_end"].abs()).sort_values(["abs_days", "episode_id"])
    if past.empty:
        return blank
    chosen = past.iloc[0]
    return {
        "matched_episode_id": normalize_text(chosen["episode_id"]),
        "matched_trigger_mode": normalize_text(chosen["trigger_mode"]),
        "matched_episode_start_date": normalize_text(chosen["episode_start_date"]),
        "matched_episode_end_date": normalize_text(chosen["episode_end_date"]),
        "days_to_episode_start": int(chosen["days_to_start"]),
        "days_to_episode_end": int(chosen["days_to_end"]),
        "precursor_timing_type": "no_episode_within_7d",
    }


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    panel_days = build_panel_day_rows(root, sites)
    aggregated = aggregate_site_days(panel_days)
    candidate_days = select_tier_candidates(aggregated)
    episodes, episode_filter_used, total_target_episode_count = prepare_episodes(root, sites)
    event_frame, exact_event_column_used = prepare_exact_event_context(root, sites)

    if candidate_days.empty:
        summary_rows = []
        for tier_id in TIER_ORDER:
            summary_rows.append(
                {
                    "tier_id": tier_id,
                    "candidate_day_count": 0,
                    "exact_same_day_episode_count": 0,
                    "in_episode_window_count": 0,
                    "lead_1_to_3_days_count": 0,
                    "lead_4_to_7_days_count": 0,
                    "no_episode_within_7d_count": 0,
                    "exact_same_day_event_count": 0,
                    "lead_1_to_3_precision": 0.0,
                    "lead_1_to_7_precision": 0.0,
                    "exact_or_lead_1_to_3_precision": 0.0,
                    "matched_episode_count": 0,
                    "episodes_with_lead_1_to_3_count": 0,
                    "episode_lead_1_to_3_recall": 0.0,
                    "total_target_episode_count": total_target_episode_count,
                    "episode_filter_used": episode_filter_used,
                }
            )
        return (
            pd.DataFrame(summary_rows, columns=SUMMARY_COLS),
            pd.DataFrame(columns=CANDIDATE_COLS),
            pd.DataFrame(columns=EPISODE_MATCH_COLS),
        )

    candidate_days = candidate_days.merge(event_frame, on=["site", "date"], how="left")
    if exact_event_column_used:
        candidate_days["exact_same_day_event_flag"] = pd.to_numeric(
            candidate_days["exact_same_day_event_flag"], errors="coerce"
        ).fillna(0).astype(int)
    else:
        candidate_days["exact_same_day_event_flag"] = ""
    candidate_days["exact_event_column_used"] = exact_event_column_used

    match_rows: list[dict[str, object]] = []
    for row in candidate_days.to_dict("records"):
        episode_match = best_episode_match(episodes, normalize_text(row["site"]), normalize_text(row["date"]))
        row.update(episode_match)
        match_rows.append(row)

    candidate_output = pd.DataFrame(match_rows)
    candidate_output = candidate_output.loc[:, CANDIDATE_COLS].copy()

    episode_match_rows: list[dict[str, object]] = []
    for tier_id, tier_df in candidate_output.groupby("tier_id"):
        matched = tier_df.loc[tier_df["matched_episode_id"].map(normalize_text).ne("")].copy()
        if matched.empty:
            continue
        for (site, matched_episode_id, matched_trigger_mode, matched_episode_start_date), group in matched.groupby(
            ["site", "matched_episode_id", "matched_trigger_mode", "matched_episode_start_date"],
            dropna=False,
        ):
            positive_leads = pd.to_numeric(group["days_to_episode_start"], errors="coerce")
            positive_leads = positive_leads.loc[positive_leads.ge(0)]
            best_lead_days = ""
            if not positive_leads.empty:
                best_lead_days = int(positive_leads.min())
            episode_match_rows.append(
                {
                    "tier_id": tier_id,
                    "site": normalize_text(site),
                    "matched_episode_id": normalize_text(matched_episode_id),
                    "matched_trigger_mode": normalize_text(matched_trigger_mode),
                    "matched_episode_start_date": normalize_text(matched_episode_start_date),
                    "candidate_day_count_for_episode": int(len(group)),
                    "earliest_candidate_date": normalize_text(group["date"].min()),
                    "latest_candidate_date": normalize_text(group["date"].max()),
                    "best_lead_days": best_lead_days,
                    "has_exact_same_day_candidate": int(group["precursor_timing_type"].eq("exact_same_day_episode").any()),
                    "has_lead_1_to_3_candidate": int(group["precursor_timing_type"].eq("lead_1_to_3_days").any()),
                    "has_lead_4_to_7_candidate": int(group["precursor_timing_type"].eq("lead_4_to_7_days").any()),
                }
            )

    episode_matches_output = pd.DataFrame(episode_match_rows, columns=EPISODE_MATCH_COLS)

    summary_rows = []
    for tier_id in TIER_ORDER:
        tier_df = candidate_output.loc[candidate_output["tier_id"].eq(tier_id)].copy()
        candidate_day_count = int(len(tier_df))
        exact_same_day_episode_count = int(tier_df["precursor_timing_type"].eq("exact_same_day_episode").sum())
        in_episode_window_count = int(tier_df["precursor_timing_type"].eq("in_episode_window").sum())
        lead_1_to_3_days_count = int(tier_df["precursor_timing_type"].eq("lead_1_to_3_days").sum())
        lead_4_to_7_days_count = int(tier_df["precursor_timing_type"].eq("lead_4_to_7_days").sum())
        no_episode_within_7d_count = int(tier_df["precursor_timing_type"].eq("no_episode_within_7d").sum())
        exact_same_day_event_count = int(pd.to_numeric(tier_df["exact_same_day_event_flag"], errors="coerce").fillna(0).eq(1).sum())
        matched_episode_count = int(tier_df["matched_episode_id"].map(normalize_text).loc[lambda s: s.ne("")].nunique())
        episodes_with_lead_1_to_3_count = int(
            tier_df.loc[tier_df["precursor_timing_type"].eq("lead_1_to_3_days"), "matched_episode_id"]
            .map(normalize_text)
            .loc[lambda s: s.ne("")]
            .nunique()
        )

        summary_rows.append(
            {
                "tier_id": tier_id,
                "candidate_day_count": candidate_day_count,
                "exact_same_day_episode_count": exact_same_day_episode_count,
                "in_episode_window_count": in_episode_window_count,
                "lead_1_to_3_days_count": lead_1_to_3_days_count,
                "lead_4_to_7_days_count": lead_4_to_7_days_count,
                "no_episode_within_7d_count": no_episode_within_7d_count,
                "exact_same_day_event_count": exact_same_day_event_count,
                "lead_1_to_3_precision": safe_div(lead_1_to_3_days_count, candidate_day_count),
                "lead_1_to_7_precision": safe_div(lead_1_to_3_days_count + lead_4_to_7_days_count, candidate_day_count),
                "exact_or_lead_1_to_3_precision": safe_div(exact_same_day_episode_count + lead_1_to_3_days_count, candidate_day_count),
                "matched_episode_count": matched_episode_count,
                "episodes_with_lead_1_to_3_count": episodes_with_lead_1_to_3_count,
                "episode_lead_1_to_3_recall": safe_div(episodes_with_lead_1_to_3_count, total_target_episode_count),
                "total_target_episode_count": total_target_episode_count,
                "episode_filter_used": episode_filter_used,
            }
        )

    summary_output = pd.DataFrame(summary_rows, columns=SUMMARY_COLS)
    return summary_output, candidate_output, episode_matches_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_output, candidate_output, episode_matches_output = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_output.to_csv(out_dir / "common_cause_precursor_audit_summary_v1.csv", index=False, encoding="utf-8-sig")
    candidate_output.to_csv(out_dir / "common_cause_precursor_candidate_days_v1.csv", index=False, encoding="utf-8-sig")
    episode_matches_output.to_csv(out_dir / "common_cause_precursor_episode_matches_v1.csv", index=False, encoding="utf-8-sig")
    print(f"common_cause_precursor_candidate_days_v1={len(candidate_output)}")


if __name__ == "__main__":
    main()
