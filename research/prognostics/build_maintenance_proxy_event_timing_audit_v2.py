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
    "cluster_interpretation",
    "recommended_use",
]
CLUSTER_COLS = [
    "site",
    "strict_trigger_date",
    "site_event_id",
    "group_cluster_id",
    "fallback_group_proxy",
    "member_panel_count",
    "cluster_interpretation",
    "recommended_use",
    "exact_same_day_event_flag",
    "exact_event_column_used",
    "within_frame_window_flag",
    "window_event_column_used",
    "episode_overlap_flag",
    "matched_episode_id",
    "matched_trigger_mode",
    "matched_episode_start_date",
    "matched_episode_end_date",
    "days_to_episode_start",
    "days_to_episode_end",
    "timing_overlap_type",
    "recommended_disposition",
]
MATCH_COLS = [
    "site",
    "strict_trigger_date",
    "group_cluster_id",
    "exact_same_day_event_flag",
    "exact_event_column_used",
    "within_frame_window_flag",
    "window_event_column_used",
    "episode_overlap_flag",
    "matched_episode_id",
    "matched_trigger_mode",
    "matched_episode_start_date",
    "matched_episode_end_date",
    "days_to_episode_start",
    "days_to_episode_end",
    "timing_overlap_type",
    "recommended_disposition",
]
SUMMARY_COLS = [
    "total_clusters",
    "exact_same_day_event_overlap_count",
    "within_frame_window_only_count",
    "lead_before_episode_count",
    "episode_window_overlap_count",
    "no_existing_event_overlap_count",
    "redundant_exact_event_signal_count",
    "redundant_episode_signal_count",
    "potential_early_common_cause_signal_count",
    "ambiguous_event_window_signal_count",
    "novel_common_cause_candidate_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refine timing semantics for maintenance-proxy event overlap without changing official outputs."
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


def detect_exact_event_column(columns: list[str]) -> str:
    for col in ["event_day_flag", "site_event_flag", "event_flag", "event_today"]:
        if col in columns:
            return col
    for col in columns:
        lower = col.lower()
        if lower.endswith("_today"):
            return col
    return ""


def detect_window_event_column(columns: list[str]) -> str:
    for col in ["event_within_7d", "event_within_3d", "event_within_1d"]:
        if col in columns:
            return col
    for col in columns:
        lower = col.lower()
        if "within_" in lower and "event" in lower:
            return col
    return ""


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


def classify_timing(exact_flag: int, episode_overlap_flag: int, days_to_episode_start: object, window_flag: int) -> tuple[str, str]:
    days_to_start_int = None if normalize_text(days_to_episode_start) == "" else int(days_to_episode_start)
    if exact_flag == 1:
        return "exact_same_day_event_overlap", "redundant_exact_event_signal"
    if episode_overlap_flag == 1:
        return "episode_window_overlap", "redundant_episode_signal"
    if days_to_start_int is not None and days_to_start_int in {1, 2, 3}:
        return "lead_before_episode", "potential_early_common_cause_signal"
    if window_flag == 1:
        return "within_frame_window_only", "ambiguous_event_window_signal"
    return "no_existing_event_overlap", "novel_common_cause_candidate"


def prepare_clusters(root: Path, sites: list[str]) -> pd.DataFrame:
    clusters = read_csv(root / "_share" / "maintenance_proxy_event_overlap_clusters_v1.csv")
    ensure_columns(clusters, CLUSTER_REQUIRED_COLS, "maintenance_proxy_event_overlap_clusters_v1.csv")

    clusters["site"] = clusters["site"].map(normalize_text)
    clusters["strict_trigger_date"] = clusters["strict_trigger_date"].map(normalize_date)
    clusters = clusters.loc[clusters["site"].isin(sites)].copy()
    clusters = dedupe(clusters, ["group_cluster_id"], "maintenance_proxy_event_overlap_clusters_v1.csv")

    for col in [
        "site_event_id",
        "group_cluster_id",
        "fallback_group_proxy",
        "cluster_interpretation",
        "recommended_use",
    ]:
        clusters[col] = clusters[col].map(normalize_text)
    clusters["member_panel_count"] = pd.to_numeric(clusters["member_panel_count"], errors="coerce").fillna(0).astype(int)
    return clusters


def prepare_event_frame(root: Path, sites: list[str]) -> tuple[pd.DataFrame, str, str]:
    frame = read_csv(root / "_share" / "site_day_event_frame_latest.csv")
    frame["site"] = frame["site"].map(normalize_text)
    frame["date"] = frame["date"].map(normalize_date)
    frame = frame.loc[frame["site"].isin(sites)].copy()

    exact_col = detect_exact_event_column(list(frame.columns))
    window_col = detect_window_event_column(list(frame.columns))
    frame["exact_same_day_event_flag"] = frame[exact_col].map(to_int_flag) if exact_col else 0
    frame["within_frame_window_flag"] = frame[window_col].map(to_int_flag) if window_col else 0

    keep = ["site", "date", "exact_same_day_event_flag", "within_frame_window_flag"]
    frame = frame.loc[:, keep].drop_duplicates(subset=["site", "date"], keep="first").copy()
    return frame, exact_col, window_col


def prepare_episodes(root: Path, sites: list[str]) -> pd.DataFrame:
    episodes = read_csv(root / "_share" / "site_day_alert_episodes_latest.csv")
    episodes["site"] = episodes["site"].map(normalize_text)
    episodes = episodes.loc[episodes["site"].isin(sites)].copy()

    for col in ["trigger_mode", "episode_id"]:
        if col not in episodes.columns:
            episodes[col] = ""
        episodes[col] = episodes[col].map(normalize_text)

    if "episode_start_date" not in episodes.columns:
        fallback_col = ""
        for col in ["start_date", "peak_date", "next_event_date"]:
            if col in episodes.columns:
                fallback_col = col
                break
        if not fallback_col:
            raise SystemExit("site_day_alert_episodes_latest.csv missing episode boundary columns")
        episodes["episode_start_date"] = episodes[fallback_col]
        episodes["episode_end_date"] = episodes[fallback_col]
    elif "episode_end_date" not in episodes.columns:
        episodes["episode_end_date"] = episodes["episode_start_date"]

    episodes["episode_start_date"] = episodes["episode_start_date"].map(normalize_date)
    episodes["episode_end_date"] = episodes["episode_end_date"].map(normalize_date)
    return episodes


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    clusters = prepare_clusters(root, sites)
    frame, exact_col, window_col = prepare_event_frame(root, sites)
    episodes = prepare_episodes(root, sites)

    frame_join = frame.rename(columns={"date": "strict_trigger_date"})
    clusters = clusters.merge(frame_join, on=["site", "strict_trigger_date"], how="left")
    clusters["exact_same_day_event_flag"] = pd.to_numeric(clusters["exact_same_day_event_flag"], errors="coerce").fillna(0).astype(int)
    clusters["within_frame_window_flag"] = pd.to_numeric(clusters["within_frame_window_flag"], errors="coerce").fillna(0).astype(int)
    clusters["exact_event_column_used"] = exact_col
    clusters["window_event_column_used"] = window_col

    output_rows: list[dict[str, object]] = []
    for row in clusters.to_dict("records"):
        episode_match = best_episode_match(episodes, normalize_text(row["site"]), normalize_text(row["strict_trigger_date"]))
        row.update(episode_match)
        timing_type, disposition = classify_timing(
            int(row["exact_same_day_event_flag"]),
            int(row["episode_overlap_flag"]),
            row["days_to_episode_start"],
            int(row["within_frame_window_flag"]),
        )
        row["timing_overlap_type"] = timing_type
        row["recommended_disposition"] = disposition
        output_rows.append(row)

    cluster_output = pd.DataFrame(output_rows, columns=CLUSTER_COLS)
    matches_output = cluster_output.loc[:, MATCH_COLS].copy()
    summary_output = pd.DataFrame(
        [
            {
                "total_clusters": int(len(cluster_output)),
                "exact_same_day_event_overlap_count": int(cluster_output["timing_overlap_type"].eq("exact_same_day_event_overlap").sum()),
                "within_frame_window_only_count": int(cluster_output["timing_overlap_type"].eq("within_frame_window_only").sum()),
                "lead_before_episode_count": int(cluster_output["timing_overlap_type"].eq("lead_before_episode").sum()),
                "episode_window_overlap_count": int(cluster_output["timing_overlap_type"].eq("episode_window_overlap").sum()),
                "no_existing_event_overlap_count": int(cluster_output["timing_overlap_type"].eq("no_existing_event_overlap").sum()),
                "redundant_exact_event_signal_count": int(cluster_output["recommended_disposition"].eq("redundant_exact_event_signal").sum()),
                "redundant_episode_signal_count": int(cluster_output["recommended_disposition"].eq("redundant_episode_signal").sum()),
                "potential_early_common_cause_signal_count": int(cluster_output["recommended_disposition"].eq("potential_early_common_cause_signal").sum()),
                "ambiguous_event_window_signal_count": int(cluster_output["recommended_disposition"].eq("ambiguous_event_window_signal").sum()),
                "novel_common_cause_candidate_count": int(cluster_output["recommended_disposition"].eq("novel_common_cause_candidate").sum()),
            }
        ],
        columns=SUMMARY_COLS,
    )
    return summary_output, cluster_output, matches_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_output, cluster_output, matches_output = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_output.to_csv(out_dir / "maintenance_proxy_event_timing_summary_v2.csv", index=False, encoding="utf-8-sig")
    cluster_output.to_csv(out_dir / "maintenance_proxy_event_timing_clusters_v2.csv", index=False, encoding="utf-8-sig")
    matches_output.to_csv(out_dir / "maintenance_proxy_event_timing_matches_v2.csv", index=False, encoding="utf-8-sig")
    print(f"maintenance_proxy_event_timing_clusters_v2={len(cluster_output)}")


if __name__ == "__main__":
    main()
