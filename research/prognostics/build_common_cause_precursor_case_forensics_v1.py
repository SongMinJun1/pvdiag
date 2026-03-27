#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
TIER_FLAG_MAP = {
    "broad_3g_10p": "selected_by_broad_3g_10p",
    "medium_2g_5p": "selected_by_medium_2g_5p",
    "narrow_1g_3p": "selected_by_narrow_1g_3p",
}
DAY_COLS = [
    "site",
    "date",
    "selected_by_broad_3g_10p",
    "selected_by_medium_2g_5p",
    "selected_by_narrow_1g_3p",
    "matched_episode_id",
    "matched_trigger_mode",
    "matched_episode_start_date",
    "matched_episode_end_date",
    "days_to_episode_start",
    "days_to_episode_end",
    "precursor_timing_type",
    "total_panel_rows",
    "zero_like_panel_count",
    "group_like_zero_like_panel_count",
    "qualifying_group_cluster_count",
    "max_group_cluster_size",
    "total_panels_in_qualifying_groups",
    "qualifying_group_panel_share",
    "local_window_day_count",
    "local_median_total_panel_rows",
    "local_median_zero_like_panel_count",
    "local_median_group_like_zero_like_panel_count",
    "local_median_qualifying_group_cluster_count",
    "total_panel_rows_ratio_vs_local_median",
    "zero_like_count_ratio_vs_local_median",
    "group_like_count_ratio_vs_local_median",
    "qualifying_group_cluster_ratio_vs_local_median",
    "candidate_run_length",
    "candidate_run_start_date",
    "candidate_run_end_date",
    "candidate_run_position",
    "forensic_hypothesis",
]
GROUP_COLS = [
    "site",
    "date",
    "fallback_group_proxy",
    "group_panel_count",
    "zero_like_group_panel_count",
    "group_like_zero_like_group_panel_count",
    "group_panel_share_of_site_day",
    "rank_by_group_like_zero_like_count",
]
SUMMARY_COLS = [
    "record_type",
    "total_candidate_days",
    "plausible_precursor_day_count",
    "episode_aligned_day_count",
    "likely_persistent_site_pattern_count",
    "likely_sparse_site_pattern_count",
    "ambiguous_case_count",
    "conalog_candidate_day_count",
    "ktc_ess_candidate_day_count",
    "conalog_plausible_precursor_count",
    "ktc_ess_plausible_precursor_count",
    "ktc_ess_persistent_site_pattern_count",
    "site",
    "candidate_day_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Perform case-by-case forensics on common-cause precursor candidate days."
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


def fallback_group_key(panel_id: object) -> str:
    parts = normalize_text(panel_id).split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return normalize_text(panel_id)


def first_nonblank(series: pd.Series) -> str:
    for value in series.tolist():
        text = normalize_text(value)
        if text:
            return text
    return ""


def safe_div(numer: int | float, denom: int | float) -> float:
    if denom <= 0:
        return 0.0
    return round(float(numer / denom), 6)


def safe_ratio_or_blank(numer: object, denom: object) -> float | pd.NA:
    numer_value = pd.to_numeric(pd.Series([numer]), errors="coerce").iloc[0]
    denom_value = pd.to_numeric(pd.Series([denom]), errors="coerce").iloc[0]
    if pd.isna(numer_value) or pd.isna(denom_value) or denom_value == 0:
        return pd.NA
    return round(float(numer_value / denom_value), 6)


def load_candidate_days(root: Path, sites: list[str]) -> pd.DataFrame:
    candidate_days = read_csv(root / "_share" / "common_cause_precursor_candidate_days_v1.csv")
    _ = read_csv(root / "_share" / "common_cause_precursor_episode_matches_v1.csv")

    required = [
        "tier_id",
        "site",
        "date",
        "matched_episode_id",
        "matched_trigger_mode",
        "matched_episode_start_date",
        "matched_episode_end_date",
        "days_to_episode_start",
        "days_to_episode_end",
        "precursor_timing_type",
    ]
    missing = [col for col in required if col not in candidate_days.columns]
    if missing:
        raise SystemExit(f"common_cause_precursor_candidate_days_v1.csv missing columns: {missing}")

    candidate_days["site"] = candidate_days["site"].map(normalize_text)
    candidate_days["date"] = candidate_days["date"].map(normalize_date)
    candidate_days["tier_id"] = candidate_days["tier_id"].map(normalize_text)
    candidate_days = candidate_days.loc[candidate_days["site"].isin(sites)].copy()
    if candidate_days.empty:
        return pd.DataFrame(columns=DAY_COLS)

    for col in [
        "matched_episode_id",
        "matched_trigger_mode",
        "matched_episode_start_date",
        "matched_episode_end_date",
        "precursor_timing_type",
    ]:
        candidate_days[col] = candidate_days[col].map(
            normalize_date if "date" in col else normalize_text
        )
    for col in ["days_to_episode_start", "days_to_episode_end"]:
        candidate_days[col] = pd.to_numeric(candidate_days[col], errors="coerce")

    tier_flags = (
        candidate_days.assign(flag=1)
        .pivot_table(index=["site", "date"], columns="tier_id", values="flag", aggfunc="max", fill_value=0)
        .reset_index()
    )
    for tier_id, flag_col in TIER_FLAG_MAP.items():
        if tier_id not in tier_flags.columns:
            tier_flags[tier_id] = 0
        tier_flags[flag_col] = pd.to_numeric(tier_flags[tier_id], errors="coerce").fillna(0).astype(int)
    keep_flag_cols = ["site", "date", *TIER_FLAG_MAP.values()]
    tier_flags = tier_flags.loc[:, keep_flag_cols].copy()

    carry = (
        candidate_days.groupby(["site", "date"], as_index=False)
        .agg(
            matched_episode_id=("matched_episode_id", first_nonblank),
            matched_trigger_mode=("matched_trigger_mode", first_nonblank),
            matched_episode_start_date=("matched_episode_start_date", first_nonblank),
            matched_episode_end_date=("matched_episode_end_date", first_nonblank),
            days_to_episode_start=("days_to_episode_start", "first"),
            days_to_episode_end=("days_to_episode_end", "first"),
            precursor_timing_type=("precursor_timing_type", first_nonblank),
        )
    )
    carry = carry.merge(tier_flags, on=["site", "date"], how="left")
    for flag_col in TIER_FLAG_MAP.values():
        carry[flag_col] = pd.to_numeric(carry[flag_col], errors="coerce").fillna(0).astype(int)
    carry["date_ts"] = carry["date"].map(parse_date)
    return carry.sort_values(["site", "date"]).reset_index(drop=True)


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
        df["date_ts"] = df["date"].map(parse_date)

        frames.append(
            df.loc[
                :,
                [
                    "site",
                    "date",
                    "date_ts",
                    "panel_id",
                    "group_key_base",
                    "zero_like_flag",
                    "group_like_zero_like_flag",
                ],
            ].rename(columns={"group_key_base": "fallback_group_proxy"})
        )

    if not frames:
        return pd.DataFrame(
            columns=[
                "site",
                "date",
                "date_ts",
                "panel_id",
                "fallback_group_proxy",
                "zero_like_flag",
                "group_like_zero_like_flag",
            ]
        )
    return pd.concat(frames, ignore_index=True)


def aggregate_site_days(panel_days: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    group_day = panel_days.groupby(["site", "date", "fallback_group_proxy"], as_index=False).agg(
        group_panel_count=("panel_id", "size"),
        zero_like_group_panel_count=("zero_like_flag", "sum"),
        group_like_zero_like_group_panel_count=("group_like_zero_like_flag", "sum"),
    )

    site_day = panel_days.groupby(["site", "date"], as_index=False).agg(
        total_panel_rows=("panel_id", "size"),
        zero_like_panel_count=("zero_like_flag", "sum"),
        group_like_zero_like_panel_count=("group_like_zero_like_flag", "sum"),
    )
    site_day["date_ts"] = site_day["date"].map(parse_date)

    qualifying_groups = group_day.loc[group_day["group_like_zero_like_group_panel_count"].ge(2)].copy()
    qualifying_day = qualifying_groups.groupby(["site", "date"], as_index=False).agg(
        qualifying_group_cluster_count=("fallback_group_proxy", "size"),
        max_group_cluster_size=("group_like_zero_like_group_panel_count", "max"),
        total_panels_in_qualifying_groups=("group_like_zero_like_group_panel_count", "sum"),
    )

    site_day = site_day.merge(qualifying_day, on=["site", "date"], how="left")
    for col in ["qualifying_group_cluster_count", "max_group_cluster_size", "total_panels_in_qualifying_groups"]:
        site_day[col] = pd.to_numeric(site_day[col], errors="coerce").fillna(0).astype(int)
    site_day["qualifying_group_panel_share"] = site_day.apply(
        lambda row: safe_div(row["total_panels_in_qualifying_groups"], row["total_panel_rows"]),
        axis=1,
    )

    group_day = group_day.merge(site_day.loc[:, ["site", "date", "total_panel_rows"]], on=["site", "date"], how="left")
    group_day["group_panel_share_of_site_day"] = group_day.apply(
        lambda row: safe_div(row["group_panel_count"], row["total_panel_rows"]),
        axis=1,
    )
    return site_day, group_day


def build_local_baselines(candidate_days: pd.DataFrame, site_day: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in candidate_days.to_dict("records"):
        date_ts = row["date_ts"]
        window_rows = site_day.loc[site_day["site"].eq(row["site"])].copy()
        if pd.notna(date_ts):
            window_rows = window_rows.loc[
                window_rows["date_ts"].notna()
                & (window_rows["date_ts"] >= date_ts - pd.Timedelta(days=7))
                & (window_rows["date_ts"] <= date_ts + pd.Timedelta(days=7))
                & window_rows["date"].ne(row["date"])
            ].copy()
        else:
            window_rows = window_rows.iloc[0:0].copy()

        local_median_total_panel_rows = window_rows["total_panel_rows"].median() if not window_rows.empty else pd.NA
        local_median_zero_like_panel_count = window_rows["zero_like_panel_count"].median() if not window_rows.empty else pd.NA
        local_median_group_like_zero_like_panel_count = (
            window_rows["group_like_zero_like_panel_count"].median() if not window_rows.empty else pd.NA
        )
        local_median_qualifying_group_cluster_count = (
            window_rows["qualifying_group_cluster_count"].median() if not window_rows.empty else pd.NA
        )

        rows.append(
            {
                "site": row["site"],
                "date": row["date"],
                "local_window_day_count": int(len(window_rows)),
                "local_median_total_panel_rows": local_median_total_panel_rows,
                "local_median_zero_like_panel_count": local_median_zero_like_panel_count,
                "local_median_group_like_zero_like_panel_count": local_median_group_like_zero_like_panel_count,
                "local_median_qualifying_group_cluster_count": local_median_qualifying_group_cluster_count,
                "total_panel_rows_ratio_vs_local_median": safe_ratio_or_blank(
                    row.get("total_panel_rows"), local_median_total_panel_rows
                ),
                "zero_like_count_ratio_vs_local_median": safe_ratio_or_blank(
                    row.get("zero_like_panel_count"), local_median_zero_like_panel_count
                ),
                "group_like_count_ratio_vs_local_median": safe_ratio_or_blank(
                    row.get("group_like_zero_like_panel_count"), local_median_group_like_zero_like_panel_count
                ),
                "qualifying_group_cluster_ratio_vs_local_median": safe_ratio_or_blank(
                    row.get("qualifying_group_cluster_count"), local_median_qualifying_group_cluster_count
                ),
            }
        )
    return pd.DataFrame(rows)


def build_candidate_runs(candidate_days: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for site, site_df in candidate_days.groupby("site", dropna=False):
        site_df = site_df.sort_values(["date_ts", "date"]).reset_index(drop=True)
        if site_df.empty:
            continue

        run: list[dict[str, object]] = []
        previous_ts: pd.Timestamp | pd.NaT = pd.NaT
        for row in site_df.to_dict("records"):
            date_ts = row["date_ts"]
            contiguous = pd.notna(previous_ts) and pd.notna(date_ts) and (date_ts - previous_ts).days == 1
            if run and not contiguous:
                rows.extend(finalize_run(run))
                run = []
            run.append(row)
            previous_ts = date_ts

        if run:
            rows.extend(finalize_run(run))

    return pd.DataFrame(rows)


def finalize_run(run: list[dict[str, object]]) -> list[dict[str, object]]:
    start_date = normalize_date(run[0]["date"])
    end_date = normalize_date(run[-1]["date"])
    run_length = len(run)
    rows = []
    for idx, row in enumerate(run, start=1):
        rows.append(
            {
                "site": row["site"],
                "date": row["date"],
                "candidate_run_length": run_length,
                "candidate_run_start_date": start_date,
                "candidate_run_end_date": end_date,
                "candidate_run_position": idx,
            }
        )
    return rows


def classify_days(day_output: pd.DataFrame) -> pd.DataFrame:
    def classify(row: pd.Series) -> str:
        total_ratio = row["total_panel_rows_ratio_vs_local_median"]
        ratio_ok = pd.isna(total_ratio) or (0.80 <= float(total_ratio) <= 1.25)

        if (
            row["precursor_timing_type"] == "lead_1_to_3_days"
            and float(row["qualifying_group_panel_share"]) >= 0.10
            and int(row["candidate_run_length"]) <= 4
            and ratio_ok
        ):
            return "plausible_precursor_day"
        if row["precursor_timing_type"] in {"exact_same_day_episode", "in_episode_window"}:
            return "episode_aligned_day"
        if row["precursor_timing_type"] == "no_episode_within_7d" and int(row["candidate_run_length"]) >= 2:
            return "likely_persistent_site_pattern"
        if float(row["qualifying_group_panel_share"]) < 0.05 or int(row["max_group_cluster_size"]) < 3:
            return "likely_sparse_site_pattern"
        return "ambiguous_case"

    day_output["forensic_hypothesis"] = day_output.apply(classify, axis=1)
    return day_output


def build_group_output(candidate_days: pd.DataFrame, group_day: pd.DataFrame) -> pd.DataFrame:
    group_output = group_day.merge(candidate_days.loc[:, ["site", "date"]], on=["site", "date"], how="inner")
    if group_output.empty:
        return pd.DataFrame(columns=GROUP_COLS)

    rows: list[pd.DataFrame] = []
    for (site, date), day_df in group_output.groupby(["site", "date"], dropna=False):
        ranked = day_df.sort_values(
            [
                "group_like_zero_like_group_panel_count",
                "zero_like_group_panel_count",
                "group_panel_count",
                "fallback_group_proxy",
            ],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)
        ranked["rank_by_group_like_zero_like_count"] = range(1, len(ranked) + 1)
        rows.append(ranked)

    group_output = pd.concat(rows, ignore_index=True)
    return group_output.loc[:, GROUP_COLS].copy()


def build_summary(day_output: pd.DataFrame, sites: list[str]) -> pd.DataFrame:
    def count_hypothesis(df: pd.DataFrame, label: str) -> int:
        return int(df["forensic_hypothesis"].eq(label).sum())

    summary_row = {
        "record_type": "summary",
        "total_candidate_days": int(len(day_output)),
        "plausible_precursor_day_count": count_hypothesis(day_output, "plausible_precursor_day"),
        "episode_aligned_day_count": count_hypothesis(day_output, "episode_aligned_day"),
        "likely_persistent_site_pattern_count": count_hypothesis(day_output, "likely_persistent_site_pattern"),
        "likely_sparse_site_pattern_count": count_hypothesis(day_output, "likely_sparse_site_pattern"),
        "ambiguous_case_count": count_hypothesis(day_output, "ambiguous_case"),
        "conalog_candidate_day_count": int(day_output["site"].eq("conalog").sum()),
        "ktc_ess_candidate_day_count": int(day_output["site"].eq("ktc_ess").sum()),
        "conalog_plausible_precursor_count": int(
            day_output.loc[day_output["site"].eq("conalog"), "forensic_hypothesis"].eq("plausible_precursor_day").sum()
        ),
        "ktc_ess_plausible_precursor_count": int(
            day_output.loc[day_output["site"].eq("ktc_ess"), "forensic_hypothesis"].eq("plausible_precursor_day").sum()
        ),
        "ktc_ess_persistent_site_pattern_count": int(
            day_output.loc[day_output["site"].eq("ktc_ess"), "forensic_hypothesis"].eq("likely_persistent_site_pattern").sum()
        ),
        "site": "",
        "candidate_day_count": pd.NA,
    }

    rows = [summary_row]
    for site in sites:
        site_df = day_output.loc[day_output["site"].eq(site)].copy()
        rows.append(
            {
                "record_type": "site",
                "total_candidate_days": pd.NA,
                "plausible_precursor_day_count": count_hypothesis(site_df, "plausible_precursor_day"),
                "episode_aligned_day_count": count_hypothesis(site_df, "episode_aligned_day"),
                "likely_persistent_site_pattern_count": count_hypothesis(site_df, "likely_persistent_site_pattern"),
                "likely_sparse_site_pattern_count": count_hypothesis(site_df, "likely_sparse_site_pattern"),
                "ambiguous_case_count": count_hypothesis(site_df, "ambiguous_case"),
                "conalog_candidate_day_count": pd.NA,
                "ktc_ess_candidate_day_count": pd.NA,
                "conalog_plausible_precursor_count": pd.NA,
                "ktc_ess_plausible_precursor_count": pd.NA,
                "ktc_ess_persistent_site_pattern_count": pd.NA,
                "site": site,
                "candidate_day_count": int(len(site_df)),
            }
        )

    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    candidate_days = load_candidate_days(root, sites)
    panel_days = build_panel_day_rows(root, sites)
    site_day, group_day = aggregate_site_days(panel_days)

    if candidate_days.empty:
        return (
            build_summary(pd.DataFrame(columns=DAY_COLS), sites),
            pd.DataFrame(columns=DAY_COLS),
            pd.DataFrame(columns=GROUP_COLS),
        )

    day_output = candidate_days.merge(site_day.drop(columns=["date_ts"]), on=["site", "date"], how="left")
    local_baselines = build_local_baselines(day_output, site_day)
    day_output = day_output.merge(local_baselines, on=["site", "date"], how="left")
    candidate_runs = build_candidate_runs(candidate_days.loc[:, ["site", "date", "date_ts"]].copy())
    day_output = day_output.merge(candidate_runs, on=["site", "date"], how="left")
    day_output = classify_days(day_output)

    for col in TIER_FLAG_MAP.values():
        day_output[col] = pd.to_numeric(day_output[col], errors="coerce").fillna(0).astype(int)

    day_output = day_output.sort_values(["site", "date"]).reset_index(drop=True)
    day_output = day_output.loc[:, DAY_COLS].copy()
    group_output = build_group_output(candidate_days, group_day)
    summary_output = build_summary(day_output, sites)
    return summary_output, day_output, group_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_output, day_output, group_output = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_output.to_csv(
        out_dir / "common_cause_precursor_case_forensics_summary_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    day_output.to_csv(
        out_dir / "common_cause_precursor_case_forensics_days_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    group_output.to_csv(
        out_dir / "common_cause_precursor_case_forensics_groups_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    print(f"common_cause_precursor_case_forensics_days_v1={len(day_output)}")


if __name__ == "__main__":
    main()
