#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
CLUSTER_REQUIRED_COLS = [
    "site",
    "strict_trigger_date",
    "site_event_id",
    "group_cluster_id",
    "fallback_group_proxy",
    "member_panel_count",
    "member_panels",
    "representative_panel_id",
    "site_event_selected_count",
    "site_event_group_cluster_count",
    "cluster_interpretation",
    "recommended_use",
]
CASE_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "site_event_id",
    "group_cluster_id",
]
MATCH_COLS = [
    "site",
    "strict_trigger_date",
    "group_cluster_id",
    "frame_event_overlap_flag",
    "frame_event_column_used",
    "episode_overlap_flag",
    "matched_episode_id",
    "matched_trigger_mode",
    "matched_episode_start_date",
    "matched_episode_end_date",
    "days_to_episode_start",
    "days_to_episode_end",
    "overlap_type",
    "recommended_disposition",
]
CLUSTER_COLS = [
    "site",
    "strict_trigger_date",
    "site_event_id",
    "group_cluster_id",
    "fallback_group_proxy",
    "member_panel_count",
    "member_panels",
    "representative_panel_id",
    "cluster_interpretation",
    "recommended_use",
    "frame_event_overlap_flag",
    "frame_event_column_used",
    "event_confidence_level",
    "weather_confound_flag",
    "episode_overlap_flag",
    "matched_episode_id",
    "matched_trigger_mode",
    "matched_episode_start_date",
    "matched_episode_end_date",
    "days_to_episode_start",
    "days_to_episode_end",
    "overlap_type",
    "recommended_disposition",
]
SUMMARY_COLS = [
    "record_type",
    "total_clusters",
    "total_selected_cases",
    "exact_frame_event_overlap_count",
    "episode_window_overlap_count",
    "lead_before_episode_count",
    "no_existing_event_overlap_count",
    "redundant_with_existing_event_layer_count",
    "redundant_with_existing_episode_layer_count",
    "potential_early_common_cause_signal_count",
    "novel_common_cause_candidate_count",
    "site",
    "strict_trigger_date",
    "site_event_id",
    "site_event_group_cluster_count",
    "site_event_selected_count",
    "overlap_type_mode",
    "recommended_disposition_mode",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit overlap between maintenance-proxy cluster selections and existing site-day event / alert-episode layers."
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


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def dedupe(df: pd.DataFrame, cols: list[str], name: str) -> pd.DataFrame:
    dupes = df.loc[df.duplicated(subset=cols, keep=False), cols]
    if not dupes.empty:
        raise SystemExit(f"{name} has duplicate rows on {cols}")
    return df


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


def mode_or_blank(values: pd.Series) -> str:
    cleaned = [normalize_text(value) for value in values if normalize_text(value)]
    if not cleaned:
        return ""
    counts = pd.Series(cleaned).value_counts()
    return str(counts.index[0])


def join_text(values: pd.Series) -> str:
    cleaned = sorted({normalize_text(value) for value in values if normalize_text(value)})
    return "|".join(cleaned)


def detect_frame_event_column(columns: list[str]) -> str:
    preferred = ["event_day_flag", "site_event_flag", "event_flag"]
    for col in preferred:
        if col in columns:
            return col

    fallback = [
        "event_within_7d",
        "event_within_3d",
        "event_within_1d",
        "event_today",
    ]
    for col in fallback:
        if col in columns:
            return col

    for col in columns:
        lower = col.lower()
        if "event" in lower and lower.endswith("_flag"):
            return col
    return ""


def overlap_type(frame_flag: int, episode_flag: int, days_to_episode_start: int | None) -> tuple[str, str]:
    if frame_flag == 1:
        return "exact_frame_event_overlap", "redundant_with_existing_event_layer"
    if episode_flag == 1:
        return "episode_window_overlap", "redundant_with_existing_episode_layer"
    if days_to_episode_start is not None and 1 <= days_to_episode_start <= 3:
        return "lead_before_episode", "potential_early_common_cause_signal"
    return "no_existing_event_overlap", "novel_common_cause_candidate"


def prepare_clusters(root: Path, sites: list[str]) -> tuple[pd.DataFrame, int]:
    clusters = read_csv(root / "_share" / "maintenance_proxy_cluster_audit_clusters_v1.csv")
    cases = read_csv(root / "_share" / "maintenance_proxy_cluster_audit_cases_v1.csv")
    ensure_columns(clusters, CLUSTER_REQUIRED_COLS, "maintenance_proxy_cluster_audit_clusters_v1.csv")
    ensure_columns(cases, CASE_REQUIRED_COLS, "maintenance_proxy_cluster_audit_cases_v1.csv")

    for df in [clusters, cases]:
        df["site"] = df["site"].map(normalize_text)
        df["strict_trigger_date"] = df["strict_trigger_date"].map(normalize_date)

    clusters = clusters.loc[clusters["site"].isin(sites)].copy()
    cases = cases.loc[cases["site"].isin(sites)].copy()
    clusters = dedupe(clusters, ["group_cluster_id"], "maintenance_proxy_cluster_audit_clusters_v1.csv")
    cases = dedupe(cases, ["site", "panel_id", "strict_trigger_date"], "maintenance_proxy_cluster_audit_cases_v1.csv")

    for col in [
        "site_event_id",
        "group_cluster_id",
        "fallback_group_proxy",
        "member_panels",
        "representative_panel_id",
        "cluster_interpretation",
        "recommended_use",
    ]:
        clusters[col] = clusters[col].map(normalize_text)
    for col in ["member_panel_count", "site_event_selected_count", "site_event_group_cluster_count"]:
        clusters[col] = pd.to_numeric(clusters[col], errors="coerce").fillna(0).astype(int)

    total_selected_cases = int(len(cases))
    return clusters, total_selected_cases


def prepare_event_frame(root: Path, sites: list[str]) -> tuple[pd.DataFrame, str]:
    frame = read_csv(root / "_share" / "site_day_event_frame_latest.csv")
    frame["site"] = frame["site"].map(normalize_text)
    frame["date"] = frame["date"].map(normalize_date)
    frame = frame.loc[frame["site"].isin(sites)].copy()
    event_col = detect_frame_event_column(list(frame.columns))
    if event_col:
        frame["frame_event_overlap_flag"] = frame[event_col].map(to_int_flag)
    else:
        frame["frame_event_overlap_flag"] = 0
    if "weather_confound_flag" not in frame.columns and "weather_confound_flag_calc" in frame.columns:
        frame["weather_confound_flag"] = frame["weather_confound_flag_calc"]
    if "event_confidence_level" not in frame.columns and "next_event_confidence_level" in frame.columns:
        frame["event_confidence_level"] = frame["next_event_confidence_level"]
    keep_cols = ["site", "date", "frame_event_overlap_flag"]
    for col in ["event_confidence_level", "weather_confound_flag"]:
        if col in frame.columns:
            keep_cols.append(col)
    frame = frame.loc[:, keep_cols].drop_duplicates(subset=["site", "date"], keep="first").copy()
    return frame, event_col


def prepare_event_dataset(root: Path, sites: list[str]) -> pd.DataFrame:
    path = root / "_share" / "site_event_dataset_latest.csv"
    if not path.exists():
        return pd.DataFrame(columns=["site", "representative_date", "event_start_date", "event_end_date", "event_confidence_level", "weather_confound_flag"])
    df = read_csv(path)
    if "site" not in df.columns:
        return pd.DataFrame(columns=["site", "representative_date", "event_start_date", "event_end_date", "event_confidence_level", "weather_confound_flag"])
    df["site"] = df["site"].map(normalize_text)
    df = df.loc[df["site"].isin(sites)].copy()
    for col in ["representative_date", "event_start_date", "event_end_date"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].map(normalize_date)
    for col in ["event_confidence_level", "weather_confound_flag"]:
        if col not in df.columns:
            df[col] = ""
    return df.loc[:, ["site", "representative_date", "event_start_date", "event_end_date", "event_confidence_level", "weather_confound_flag"]].copy()


def prepare_episodes(root: Path, sites: list[str]) -> pd.DataFrame:
    episodes = read_csv(root / "_share" / "site_day_alert_episodes_latest.csv")
    episodes["site"] = episodes["site"].map(normalize_text)
    episodes = episodes.loc[episodes["site"].isin(sites)].copy()

    for col in ["trigger_mode", "episode_id"]:
        if col not in episodes.columns:
            episodes[col] = ""
        episodes[col] = episodes[col].map(normalize_text)

    if "episode_start_date" not in episodes.columns:
        start_fallback = ""
        for col in ["start_date", "peak_date", "next_event_date"]:
            if col in episodes.columns:
                start_fallback = col
                break
        if not start_fallback:
            raise SystemExit("site_day_alert_episodes_latest.csv missing episode boundary columns")
        episodes["episode_start_date"] = episodes[start_fallback]
        episodes["episode_end_date"] = episodes.get(start_fallback, episodes["episode_start_date"])
    elif "episode_end_date" not in episodes.columns:
        episodes["episode_end_date"] = episodes["episode_start_date"]

    episodes["episode_start_date"] = episodes["episode_start_date"].map(normalize_date)
    episodes["episode_end_date"] = episodes["episode_end_date"].map(normalize_date)
    return episodes


def event_dataset_context(dataset: pd.DataFrame, site: str, target_date: str) -> tuple[str, str]:
    if dataset.empty:
        return "", ""
    target_ts = parse_date(target_date)
    if pd.isna(target_ts):
        return "", ""
    site_rows = dataset.loc[dataset["site"].eq(site)].copy()
    if site_rows.empty:
        return "", ""
    site_rows["start_ts"] = site_rows["event_start_date"].map(parse_date)
    site_rows["end_ts"] = site_rows["event_end_date"].map(parse_date)
    site_rows["rep_ts"] = site_rows["representative_date"].map(parse_date)

    same_day = site_rows.loc[site_rows["rep_ts"].eq(target_ts)]
    if same_day.empty:
        same_day = site_rows.loc[
            site_rows["start_ts"].notna()
            & site_rows["end_ts"].notna()
            & (site_rows["start_ts"] <= target_ts)
            & (site_rows["end_ts"] >= target_ts)
        ]
    if same_day.empty:
        return "", ""
    row = same_day.sort_values(["rep_ts", "start_ts"], na_position="last").iloc[0]
    return normalize_text(row.get("event_confidence_level", "")), normalize_text(row.get("weather_confound_flag", ""))


def best_episode_match(episodes: pd.DataFrame, site: str, target_date: str) -> dict[str, object]:
    blank = {
        "episode_overlap_flag": 0,
        "matched_episode_id": "",
        "matched_trigger_mode": "",
        "matched_episode_start_date": "",
        "matched_episode_end_date": "",
        "days_to_episode_start": "",
        "days_to_episode_end": "",
    }
    target_ts = parse_date(target_date)
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

    overlap = site_rows.loc[(site_rows["days_to_start"] <= 0) & (site_rows["days_to_end"] >= 0)]
    if not overlap.empty:
        chosen = overlap.sort_values(["days_to_end", "days_to_start", "episode_id"], ascending=[True, False, True]).iloc[0]
        return {
            "episode_overlap_flag": 1,
            "matched_episode_id": normalize_text(chosen["episode_id"]),
            "matched_trigger_mode": normalize_text(chosen["trigger_mode"]),
            "matched_episode_start_date": normalize_text(chosen["episode_start_date"]),
            "matched_episode_end_date": normalize_text(chosen["episode_end_date"]),
            "days_to_episode_start": int(chosen["days_to_start"]),
            "days_to_episode_end": int(chosen["days_to_end"]),
        }

    future = site_rows.loc[site_rows["days_to_start"] > 0].sort_values(["days_to_start", "days_to_end", "episode_id"])
    if not future.empty:
        chosen = future.iloc[0]
        return {
            "episode_overlap_flag": 0,
            "matched_episode_id": normalize_text(chosen["episode_id"]),
            "matched_trigger_mode": normalize_text(chosen["trigger_mode"]),
            "matched_episode_start_date": normalize_text(chosen["episode_start_date"]),
            "matched_episode_end_date": normalize_text(chosen["episode_end_date"]),
            "days_to_episode_start": int(chosen["days_to_start"]),
            "days_to_episode_end": int(chosen["days_to_end"]),
        }

    past = site_rows.assign(abs_days=site_rows["days_to_end"].abs()).sort_values(["abs_days", "episode_id"])
    if past.empty:
        return blank
    chosen = past.iloc[0]
    return {
        "episode_overlap_flag": 0,
        "matched_episode_id": normalize_text(chosen["episode_id"]),
        "matched_trigger_mode": normalize_text(chosen["trigger_mode"]),
        "matched_episode_start_date": normalize_text(chosen["episode_start_date"]),
        "matched_episode_end_date": normalize_text(chosen["episode_end_date"]),
        "days_to_episode_start": int(chosen["days_to_start"]),
        "days_to_episode_end": int(chosen["days_to_end"]),
    }


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    clusters, total_selected_cases = prepare_clusters(root, sites)
    frame, frame_col = prepare_event_frame(root, sites)
    dataset = prepare_event_dataset(root, sites)
    episodes = prepare_episodes(root, sites)

    frame_join = frame.rename(columns={"date": "strict_trigger_date"})
    clusters = clusters.merge(frame_join, on=["site", "strict_trigger_date"], how="left")
    clusters["frame_event_overlap_flag"] = pd.to_numeric(clusters["frame_event_overlap_flag"], errors="coerce").fillna(0).astype(int)
    clusters["frame_event_column_used"] = frame_col
    if "event_confidence_level" not in clusters.columns:
        clusters["event_confidence_level"] = ""
    if "weather_confound_flag" not in clusters.columns:
        clusters["weather_confound_flag"] = ""

    enriched_rows: list[dict[str, object]] = []
    for row in clusters.to_dict("records"):
        event_confidence_level = normalize_text(row.get("event_confidence_level", ""))
        weather_confound_flag = normalize_text(row.get("weather_confound_flag", ""))
        ds_conf, ds_weather = event_dataset_context(dataset, normalize_text(row["site"]), normalize_text(row["strict_trigger_date"]))
        if not event_confidence_level:
            event_confidence_level = ds_conf
        if not weather_confound_flag:
            weather_confound_flag = ds_weather

        episode_match = best_episode_match(episodes, normalize_text(row["site"]), normalize_text(row["strict_trigger_date"]))
        row.update(episode_match)
        row["event_confidence_level"] = event_confidence_level
        row["weather_confound_flag"] = weather_confound_flag

        days_to_start = row["days_to_episode_start"]
        days_to_start_int = None if days_to_start == "" else int(days_to_start)
        row["overlap_type"], row["recommended_disposition"] = overlap_type(
            int(row["frame_event_overlap_flag"]),
            int(row["episode_overlap_flag"]),
            days_to_start_int,
        )
        enriched_rows.append(row)

    cluster_output = pd.DataFrame(enriched_rows)
    cluster_output = cluster_output.loc[:, CLUSTER_COLS].copy()
    matches_output = cluster_output.loc[:, MATCH_COLS].copy()

    summary_rows = [
        {
            "record_type": "summary",
            "total_clusters": int(len(cluster_output)),
            "total_selected_cases": total_selected_cases,
            "exact_frame_event_overlap_count": int(cluster_output["overlap_type"].eq("exact_frame_event_overlap").sum()),
            "episode_window_overlap_count": int(cluster_output["overlap_type"].eq("episode_window_overlap").sum()),
            "lead_before_episode_count": int(cluster_output["overlap_type"].eq("lead_before_episode").sum()),
            "no_existing_event_overlap_count": int(cluster_output["overlap_type"].eq("no_existing_event_overlap").sum()),
            "redundant_with_existing_event_layer_count": int(cluster_output["recommended_disposition"].eq("redundant_with_existing_event_layer").sum()),
            "redundant_with_existing_episode_layer_count": int(cluster_output["recommended_disposition"].eq("redundant_with_existing_episode_layer").sum()),
            "potential_early_common_cause_signal_count": int(cluster_output["recommended_disposition"].eq("potential_early_common_cause_signal").sum()),
            "novel_common_cause_candidate_count": int(cluster_output["recommended_disposition"].eq("novel_common_cause_candidate").sum()),
            "site": "",
            "strict_trigger_date": "",
            "site_event_id": "",
            "site_event_group_cluster_count": "",
            "site_event_selected_count": "",
            "overlap_type_mode": "",
            "recommended_disposition_mode": "",
        }
    ]

    site_event_view = cluster_output.groupby(["site", "strict_trigger_date", "site_event_id"], as_index=False).agg(
        site_event_group_cluster_count=("group_cluster_id", "nunique"),
        site_event_selected_count=("member_panel_count", "sum"),
        overlap_type_mode=("overlap_type", mode_or_blank),
        recommended_disposition_mode=("recommended_disposition", mode_or_blank),
    )
    for row in site_event_view.itertuples(index=False):
        summary_rows.append(
            {
                "record_type": "site_event",
                "total_clusters": "",
                "total_selected_cases": "",
                "exact_frame_event_overlap_count": "",
                "episode_window_overlap_count": "",
                "lead_before_episode_count": "",
                "no_existing_event_overlap_count": "",
                "redundant_with_existing_event_layer_count": "",
                "redundant_with_existing_episode_layer_count": "",
                "potential_early_common_cause_signal_count": "",
                "novel_common_cause_candidate_count": "",
                "site": row.site,
                "strict_trigger_date": row.strict_trigger_date,
                "site_event_id": row.site_event_id,
                "site_event_group_cluster_count": int(row.site_event_group_cluster_count),
                "site_event_selected_count": int(row.site_event_selected_count),
                "overlap_type_mode": row.overlap_type_mode,
                "recommended_disposition_mode": row.recommended_disposition_mode,
            }
        )

    summary_output = pd.DataFrame(summary_rows, columns=SUMMARY_COLS)
    return summary_output, cluster_output, matches_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_output, cluster_output, matches_output = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_output.to_csv(out_dir / "maintenance_proxy_event_overlap_summary_v1.csv", index=False, encoding="utf-8-sig")
    cluster_output.to_csv(out_dir / "maintenance_proxy_event_overlap_clusters_v1.csv", index=False, encoding="utf-8-sig")
    matches_output.to_csv(out_dir / "maintenance_proxy_event_overlap_matches_v1.csv", index=False, encoding="utf-8-sig")
    print(f"maintenance_proxy_event_overlap_clusters_v1={len(cluster_output)}")


if __name__ == "__main__":
    main()
