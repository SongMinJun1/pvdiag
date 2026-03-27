#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

EPISODE_REQUIRED_COLS = [
    "site",
    "trigger_mode",
    "episode_id",
    "episode_start_date",
    "episode_end_date",
    "duration_days",
    "peak_risk_band",
    "peak_risk_score",
    "matched_review_group",
    "next_event_date",
    "lead_days_from_start",
    "eligible_1d",
    "eligible_3d",
    "eligible_7d",
    "weather_confound_any",
]
EVENT_REQUIRED_COLS = [
    "site",
    "review_group",
    "likely_common_issue",
    "event_confidence_level",
    "weather_tag",
]
TRUTH_REQUIRED_COLS = [
    "site",
    "review_group",
    "our_interpretation",
]
META_REQUIRED_COLS = [
    "site",
    "review_group",
]
PACK_COLS = [
    "site",
    "trigger_mode",
    "episode_id",
    "episode_start_date",
    "episode_end_date",
    "duration_days",
    "peak_risk_band",
    "peak_risk_score",
    "matched_review_group",
    "next_event_date",
    "lead_days_from_start",
    "likely_common_issue",
    "event_confidence_level",
    "weather_tag",
    "weather_confound_any",
    "review_priority",
]
TRUTH_TEMPLATE_COLS = [
    "site",
    "episode_id",
    "episode_start_date",
    "episode_end_date",
    "matched_review_group",
    "our_interpretation",
    "field_issue_detected_date",
    "field_issue_started_estimated_date",
    "actual_issue_type",
    "actual_primary_view",
    "action_taken",
    "episode_match_manual",
    "note",
]
SUMMARY_COLS = [
    "total_selected_episodes",
    "count_by_trigger_mode",
    "count_by_review_priority",
    "count_by_site",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an episode review pack and truth template.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, expected: list[str], name: str) -> pd.DataFrame:
    missing = [col for col in expected if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")
    return df.copy()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def build_interpretation_lookup(truth_df: pd.DataFrame, meta_df: pd.DataFrame) -> dict[tuple[str, str], str]:
    truth_df = truth_df.copy()
    truth_df["site"] = truth_df["site"].map(normalize_text)
    truth_df["review_group"] = truth_df["review_group"].map(normalize_text)
    truth_df["our_interpretation"] = truth_df["our_interpretation"].map(normalize_text)

    meta_groups = {
        (normalize_text(row.site), normalize_text(row.review_group))
        for row in meta_df.itertuples(index=False)
    }

    lookup: dict[tuple[str, str], str] = {}
    for (site, review_group), group in truth_df.groupby(["site", "review_group"], dropna=False):
        if (site, review_group) not in meta_groups:
            continue
        interpretations = [value for value in group["our_interpretation"] if value]
        lookup[(site, review_group)] = interpretations[0] if interpretations else ""
    return lookup


def build_event_lookup(event_df: pd.DataFrame) -> dict[tuple[str, str], dict[str, str]]:
    event_df = event_df.copy()
    for col in ["site", "review_group", "likely_common_issue", "event_confidence_level", "weather_tag"]:
        event_df[col] = event_df[col].map(normalize_text)

    lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in event_df.itertuples(index=False):
        lookup[(row.site, row.review_group)] = {
            "likely_common_issue": row.likely_common_issue,
            "event_confidence_level": row.event_confidence_level,
            "weather_tag": row.weather_tag,
        }
    return lookup


def overlaps_any(site: str, start: pd.Timestamp, end: pd.Timestamp, high_df: pd.DataFrame) -> bool:
    subset = high_df.loc[high_df["site"].eq(site)]
    if subset.empty:
        return False
    return bool(((subset["episode_start_dt"] <= end) & (subset["episode_end_dt"] >= start)).any())


def eligible_any(row: pd.Series) -> bool:
    return any(int(row.get(col, 0)) == 1 for col in ["eligible_1d", "eligible_3d", "eligible_7d"])


def review_priority(row: pd.Series) -> str:
    confidence = normalize_text(row.get("event_confidence_level", ""))
    if row["trigger_mode"] == "high_only" and eligible_any(row):
        return "P1"
    if row["trigger_mode"] == "medium_or_higher" and not bool(row["overlaps_high"]) and confidence != "low":
        return "P2"
    return "P3"


def format_counts(series: pd.Series) -> str:
    if series.empty:
        return ""
    counts = series.value_counts(dropna=False, sort=False)
    parts: list[str] = []
    for key, value in counts.items():
        key_text = normalize_text(key) or "blank"
        parts.append(f"{key_text}:{int(value)}")
    return "|".join(parts)


def build_review_pack(
    episodes: pd.DataFrame,
    event_lookup: dict[tuple[str, str], dict[str, str]],
    interpretation_lookup: dict[tuple[str, str], str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    episodes = episodes.copy()
    episodes["site"] = episodes["site"].map(normalize_text)
    episodes["trigger_mode"] = episodes["trigger_mode"].map(normalize_text)
    episodes["episode_id"] = episodes["episode_id"].map(lambda value: normalize_text(value).zfill(4))
    episodes["matched_review_group"] = episodes["matched_review_group"].map(normalize_text)
    episodes["next_event_date"] = episodes["next_event_date"].map(normalize_text)
    episodes["episode_start_date"] = episodes["episode_start_date"].map(normalize_text)
    episodes["episode_end_date"] = episodes["episode_end_date"].map(normalize_text)
    episodes["episode_start_dt"] = pd.to_datetime(episodes["episode_start_date"], errors="coerce")
    episodes["episode_end_dt"] = pd.to_datetime(episodes["episode_end_date"], errors="coerce")

    high_df = episodes.loc[episodes["trigger_mode"].eq("high_only")].copy()
    medium_df = episodes.loc[episodes["trigger_mode"].eq("medium_or_higher")].copy()
    medium_df["overlaps_high"] = medium_df.apply(
        lambda row: overlaps_any(row["site"], row["episode_start_dt"], row["episode_end_dt"], high_df),
        axis=1,
    )
    high_df["overlaps_high"] = False

    selected = pd.concat(
        [high_df, medium_df.loc[~medium_df["overlaps_high"]]],
        ignore_index=True,
        sort=False,
    )
    selected = selected.sort_values(
        ["site", "episode_start_dt", "trigger_mode", "episode_id"],
        kind="stable",
    ).reset_index(drop=True)

    selected["likely_common_issue"] = selected.apply(
        lambda row: event_lookup.get((row["site"], row["matched_review_group"]), {}).get("likely_common_issue", ""),
        axis=1,
    )
    selected["event_confidence_level"] = selected.apply(
        lambda row: event_lookup.get((row["site"], row["matched_review_group"]), {}).get("event_confidence_level", ""),
        axis=1,
    )
    selected["weather_tag"] = selected.apply(
        lambda row: event_lookup.get((row["site"], row["matched_review_group"]), {}).get("weather_tag", ""),
        axis=1,
    )
    selected["review_priority"] = selected.apply(review_priority, axis=1)
    selected["truth_episode_id"] = selected.apply(
        lambda row: f"{row['trigger_mode']}:{row['episode_id']}",
        axis=1,
    )

    pack = selected.loc[:, PACK_COLS].copy()

    truth_template = pd.DataFrame(
        {
            "site": selected["site"],
            "episode_id": selected["truth_episode_id"],
            "episode_start_date": selected["episode_start_date"],
            "episode_end_date": selected["episode_end_date"],
            "matched_review_group": selected["matched_review_group"],
            "our_interpretation": selected.apply(
                lambda row: interpretation_lookup.get((row["site"], row["matched_review_group"]), ""),
                axis=1,
            ),
            "field_issue_detected_date": "",
            "field_issue_started_estimated_date": "",
            "actual_issue_type": "",
            "actual_primary_view": "",
            "action_taken": "",
            "episode_match_manual": "",
            "note": "",
        }
    ).loc[:, TRUTH_TEMPLATE_COLS]

    summary = pd.DataFrame(
        [
            {
                "total_selected_episodes": int(len(selected)),
                "count_by_trigger_mode": format_counts(selected["trigger_mode"]),
                "count_by_review_priority": format_counts(selected["review_priority"]),
                "count_by_site": format_counts(selected["site"]),
            }
        ],
        columns=SUMMARY_COLS,
    )

    return pack, truth_template, summary


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"

    episodes = ensure_columns(
        read_csv(share_dir / "site_day_alert_episodes_latest.csv"),
        EPISODE_REQUIRED_COLS,
        "site_day_alert_episodes_latest.csv",
    )
    event_dataset = ensure_columns(
        read_csv(share_dir / "site_event_dataset_latest.csv"),
        EVENT_REQUIRED_COLS,
        "site_event_dataset_latest.csv",
    )
    truth_template = ensure_columns(
        read_csv(share_dir / "field_truth_template.csv"),
        TRUTH_REQUIRED_COLS,
        "field_truth_template.csv",
    )
    truth_meta = ensure_columns(
        read_csv(share_dir / "field_truth_template_meta.csv"),
        META_REQUIRED_COLS,
        "field_truth_template_meta.csv",
    )

    event_lookup = build_event_lookup(event_dataset)
    interpretation_lookup = build_interpretation_lookup(truth_template, truth_meta)
    pack, truth_out, summary = build_review_pack(episodes, event_lookup, interpretation_lookup)

    pack.to_csv(share_dir / "episode_review_pack_latest.csv", index=False, encoding="utf-8-sig")
    truth_out.to_csv(share_dir / "episode_truth_template.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / "episode_review_summary.csv", index=False, encoding="utf-8-sig")

    print(f"selected_episodes={len(pack)}")
    print(f"count_by_trigger_mode={format_counts(pack['trigger_mode'])}")
    print(f"count_by_review_priority={format_counts(pack['review_priority'])}")
    print(f"count_by_site={format_counts(pack['site'])}")


if __name__ == "__main__":
    main()
