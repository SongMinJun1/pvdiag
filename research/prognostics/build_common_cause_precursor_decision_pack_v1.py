#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
PRIMARY_TIER = "broad_3g_10p"
SUMMARY_COLS = [
    "global_recommendation",
    "global_decision_reason",
    "primary_tier_used",
    "broad_3g_10p_candidate_day_count",
    "broad_3g_10p_lead_1_to_3_precision",
    "broad_3g_10p_episode_lead_1_to_3_recall",
    "total_plausible_precursor_day_count",
    "plausible_precursor_site_count",
    "total_episode_aligned_day_count",
    "total_likely_persistent_site_pattern_count",
    "total_likely_sparse_site_pattern_count",
]
SITE_COLS = [
    "site",
    "candidate_day_count",
    "plausible_precursor_day_count",
    "episode_aligned_day_count",
    "likely_persistent_site_pattern_count",
    "likely_sparse_site_pattern_count",
    "ambiguous_case_count",
    "site_recommendation",
    "site_decision_reason",
]
CASE_COLS = [
    "site",
    "date",
    "matched_episode_id",
    "matched_trigger_mode",
    "matched_episode_start_date",
    "days_to_episode_start",
    "precursor_timing_type",
    "forensic_hypothesis",
    "site_recommendation",
    "include_in_site_specific_note_flag",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consolidate common-cause precursor audits into a final decision artifact."
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
        help="Sites to include. Defaults to stable known sites.",
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


def fmt_float(value: object) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return "NA"
    return f"{float(numeric):.3f}"


def num_or_zero(value: object) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return 0.0
    return float(numeric)


def load_inputs(root: Path, sites: list[str]) -> dict[str, pd.DataFrame]:
    audit_summary = read_csv(root / "_share" / "common_cause_precursor_audit_summary_v1.csv")
    candidate_days = read_csv(root / "_share" / "common_cause_precursor_candidate_days_v1.csv")
    episode_matches = read_csv(root / "_share" / "common_cause_precursor_episode_matches_v1.csv")
    forensics_summary = read_csv(root / "_share" / "common_cause_precursor_case_forensics_summary_v1.csv")
    forensics_days = read_csv(root / "_share" / "common_cause_precursor_case_forensics_days_v1.csv")
    forensics_groups = read_csv(root / "_share" / "common_cause_precursor_case_forensics_groups_v1.csv")
    timing_clusters = read_csv(root / "_share" / "maintenance_proxy_event_timing_clusters_v2.csv")

    for df, date_cols in [
        (candidate_days, ["date", "matched_episode_start_date", "matched_episode_end_date"]),
        (episode_matches, ["matched_episode_start_date", "earliest_candidate_date", "latest_candidate_date"]),
        (forensics_days, ["date", "matched_episode_start_date", "matched_episode_end_date"]),
        (forensics_groups, ["date"]),
        (timing_clusters, ["strict_trigger_date", "matched_episode_start_date", "matched_episode_end_date"]),
    ]:
        for col in date_cols:
            if col in df.columns:
                df[col] = df[col].map(normalize_date)

    for df in [candidate_days, episode_matches, forensics_days, forensics_groups, timing_clusters]:
        if "site" in df.columns:
            df["site"] = df["site"].map(normalize_text)

    candidate_days = candidate_days.loc[candidate_days["site"].isin(sites)].copy()
    episode_matches = episode_matches.loc[episode_matches["site"].isin(sites)].copy()
    forensics_days = forensics_days.loc[forensics_days["site"].isin(sites)].copy()
    forensics_groups = forensics_groups.loc[forensics_groups["site"].isin(sites)].copy()
    timing_clusters = timing_clusters.loc[timing_clusters["site"].isin(sites)].copy()

    for col in [
        "lead_1_to_3_precision",
        "episode_lead_1_to_3_recall",
        "candidate_day_count",
        "plausible_precursor_day_count",
        "episode_aligned_day_count",
        "likely_persistent_site_pattern_count",
        "likely_sparse_site_pattern_count",
        "ambiguous_case_count",
    ]:
        if col in audit_summary.columns:
            audit_summary[col] = pd.to_numeric(audit_summary[col], errors="coerce")
        if col in forensics_summary.columns:
            forensics_summary[col] = pd.to_numeric(forensics_summary[col], errors="coerce")

    if "days_to_episode_start" in forensics_days.columns:
        forensics_days["days_to_episode_start"] = pd.to_numeric(forensics_days["days_to_episode_start"], errors="coerce")

    return {
        "audit_summary": audit_summary,
        "candidate_days": candidate_days,
        "episode_matches": episode_matches,
        "forensics_summary": forensics_summary,
        "forensics_days": forensics_days,
        "forensics_groups": forensics_groups,
        "timing_clusters": timing_clusters,
    }


def build_site_counts(forensics_summary: pd.DataFrame, forensics_days: pd.DataFrame, sites: list[str]) -> pd.DataFrame:
    summary_sites = forensics_summary.loc[forensics_summary.get("record_type", "").eq("site")].copy()
    if summary_sites.empty:
        summary_sites = pd.DataFrame({"site": sites})
    else:
        summary_sites["site"] = summary_sites["site"].map(normalize_text)
        summary_sites = summary_sites.loc[summary_sites["site"].isin(sites)].copy()

    actual_counts = (
        forensics_days.groupby("site", as_index=False)
        .agg(
            candidate_day_count=("date", "size"),
            plausible_precursor_day_count=("forensic_hypothesis", lambda s: int(s.eq("plausible_precursor_day").sum())),
            episode_aligned_day_count=("forensic_hypothesis", lambda s: int(s.eq("episode_aligned_day").sum())),
            likely_persistent_site_pattern_count=("forensic_hypothesis", lambda s: int(s.eq("likely_persistent_site_pattern").sum())),
            likely_sparse_site_pattern_count=("forensic_hypothesis", lambda s: int(s.eq("likely_sparse_site_pattern").sum())),
            ambiguous_case_count=("forensic_hypothesis", lambda s: int(s.eq("ambiguous_case").sum())),
        )
    )

    base = pd.DataFrame({"site": sites})
    merged = base.merge(summary_sites, on="site", how="left").merge(actual_counts, on="site", how="left", suffixes=("_summary", ""))

    count_cols = [
        "candidate_day_count",
        "plausible_precursor_day_count",
        "episode_aligned_day_count",
        "likely_persistent_site_pattern_count",
        "likely_sparse_site_pattern_count",
        "ambiguous_case_count",
    ]
    for col in count_cols:
        summary_col = f"{col}_summary"
        if summary_col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(pd.to_numeric(merged[summary_col], errors="coerce"))
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0).astype(int)

    return merged.loc[:, ["site", *count_cols]].copy()


def build_timing_context(timing_clusters: pd.DataFrame) -> pd.DataFrame:
    if timing_clusters.empty:
        return pd.DataFrame(columns=["site", "lead_before_episode_cluster_count"])
    if "timing_overlap_type" not in timing_clusters.columns:
        timing_clusters["timing_overlap_type"] = ""
    timing_clusters["timing_overlap_type"] = timing_clusters["timing_overlap_type"].map(normalize_text)
    return (
        timing_clusters.groupby("site", as_index=False)
        .agg(
            lead_before_episode_cluster_count=(
                "timing_overlap_type",
                lambda s: int(s.eq("lead_before_episode").sum()),
            )
        )
    )


def decide_site(site_row: pd.Series, lead_cluster_count: int) -> tuple[str, str]:
    plausible = int(site_row["plausible_precursor_day_count"])
    aligned = int(site_row["episode_aligned_day_count"])
    persistent = int(site_row["likely_persistent_site_pattern_count"])
    sparse = int(site_row["likely_sparse_site_pattern_count"])
    candidate_days = int(site_row["candidate_day_count"])

    if plausible >= 2 and aligned >= 1 and persistent == 0:
        if lead_cluster_count > 0:
            reason = (
                f"{plausible} plausible precursor days and {aligned} episode-aligned days with no persistent-pattern days; "
                f"timing audit also showed {lead_cluster_count} lead-before-episode cluster matches."
            )
        else:
            reason = (
                f"{plausible} plausible precursor days and {aligned} episode-aligned days with no persistent-pattern days."
            )
        return "keep_site_specific_precursor_note", reason

    if (persistent >= 1 or sparse >= 1) and plausible == 0:
        reason = (
            f"Plausible precursor days are absent while persistent={persistent} and sparse={sparse}, "
            "which fits a site-pattern or coverage-artifact interpretation better than a precursor interpretation."
        )
        return "likely_site_pattern_not_generalizable", reason

    if candidate_days == 0:
        return "no_precursor_signal", "No candidate days were selected by the precursor audits for this site."

    reason = (
        f"Mixed evidence remains: plausible={plausible}, episode_aligned={aligned}, "
        f"persistent={persistent}, sparse={sparse}."
    )
    return "ambiguous_site_signal", reason


def decide_global(
    broad_row: pd.Series,
    site_output: pd.DataFrame,
    total_plausible_precursor_day_count: int,
    plausible_precursor_site_count: int,
) -> tuple[str, str]:
    precision = num_or_zero(broad_row.get("lead_1_to_3_precision"))
    recall = num_or_zero(broad_row.get("episode_lead_1_to_3_recall"))
    sites_with_two_plausible = int(site_output["plausible_precursor_day_count"].ge(2).sum())

    if precision >= 0.50 and recall >= 0.20 and plausible_precursor_site_count >= 2:
        reason = (
            f"Primary tier {PRIMARY_TIER} clears the shadow-addon thresholds: precision={precision:.3f}, "
            f"recall={recall:.3f}, plausible precursor evidence across {plausible_precursor_site_count} sites."
        )
        return "consider_shadow_addon_next", reason

    if precision >= 0.25 and sites_with_two_plausible >= 1:
        plausible_sites = site_output.loc[site_output["plausible_precursor_day_count"].ge(2), "site"].tolist()
        reason = (
            f"Primary tier {PRIMARY_TIER} is encouraging but not general enough: precision={precision:.3f}, "
            f"recall={recall:.3f}, and plausible precursor days are concentrated in {', '.join(plausible_sites)}."
        )
        return "keep_under_observation", reason

    reason = (
        f"Primary tier {PRIMARY_TIER} does not justify adoption: precision={precision:.3f}, recall={recall:.3f}, "
        f"and plausible precursor evidence spans {plausible_precursor_site_count} sites ({total_plausible_precursor_day_count} days total)."
    )
    return "do_not_adopt_global_addon_yet", reason


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    inputs = load_inputs(root, sites)
    audit_summary = inputs["audit_summary"]
    forensics_summary = inputs["forensics_summary"]
    forensics_days = inputs["forensics_days"].copy()
    timing_context = build_timing_context(inputs["timing_clusters"])

    broad_candidates = audit_summary.loc[audit_summary["tier_id"].map(normalize_text).eq(PRIMARY_TIER)].copy()
    if broad_candidates.empty:
        raise SystemExit(f"missing {PRIMARY_TIER} row in common_cause_precursor_audit_summary_v1.csv")
    broad_row = broad_candidates.iloc[0]

    site_output = build_site_counts(forensics_summary, forensics_days, sites)
    site_output = site_output.merge(timing_context, on="site", how="left")
    site_output["lead_before_episode_cluster_count"] = pd.to_numeric(
        site_output["lead_before_episode_cluster_count"], errors="coerce"
    ).fillna(0).astype(int)

    site_recs = site_output.apply(
        lambda row: decide_site(row, int(row["lead_before_episode_cluster_count"])), axis=1
    )
    site_output["site_recommendation"] = [item[0] for item in site_recs]
    site_output["site_decision_reason"] = [item[1] for item in site_recs]

    total_plausible_precursor_day_count = int(site_output["plausible_precursor_day_count"].sum())
    plausible_precursor_site_count = int(site_output["plausible_precursor_day_count"].gt(0).sum())
    total_episode_aligned_day_count = int(site_output["episode_aligned_day_count"].sum())
    total_likely_persistent_site_pattern_count = int(site_output["likely_persistent_site_pattern_count"].sum())
    total_likely_sparse_site_pattern_count = int(site_output["likely_sparse_site_pattern_count"].sum())

    global_recommendation, global_decision_reason = decide_global(
        broad_row,
        site_output,
        total_plausible_precursor_day_count,
        plausible_precursor_site_count,
    )
    summary_output = pd.DataFrame(
        [
            {
                "global_recommendation": global_recommendation,
                "global_decision_reason": global_decision_reason,
                "primary_tier_used": PRIMARY_TIER,
                "broad_3g_10p_candidate_day_count": int(num_or_zero(broad_row["candidate_day_count"])),
                "broad_3g_10p_lead_1_to_3_precision": num_or_zero(broad_row["lead_1_to_3_precision"]),
                "broad_3g_10p_episode_lead_1_to_3_recall": num_or_zero(broad_row["episode_lead_1_to_3_recall"]),
                "total_plausible_precursor_day_count": total_plausible_precursor_day_count,
                "plausible_precursor_site_count": plausible_precursor_site_count,
                "total_episode_aligned_day_count": total_episode_aligned_day_count,
                "total_likely_persistent_site_pattern_count": total_likely_persistent_site_pattern_count,
                "total_likely_sparse_site_pattern_count": total_likely_sparse_site_pattern_count,
            }
        ],
        columns=SUMMARY_COLS,
    )

    site_output = site_output.loc[:, SITE_COLS].sort_values("site").reset_index(drop=True)

    case_output = forensics_days.merge(
        site_output.loc[:, ["site", "site_recommendation"]],
        on="site",
        how="left",
    )
    case_output["matched_episode_id"] = case_output["matched_episode_id"].map(normalize_text)
    case_output["matched_trigger_mode"] = case_output["matched_trigger_mode"].map(normalize_text)
    case_output["matched_episode_start_date"] = case_output["matched_episode_start_date"].map(normalize_date)
    case_output["precursor_timing_type"] = case_output["precursor_timing_type"].map(normalize_text)
    case_output["forensic_hypothesis"] = case_output["forensic_hypothesis"].map(normalize_text)
    case_output["include_in_site_specific_note_flag"] = (
        case_output["site_recommendation"].eq("keep_site_specific_precursor_note")
        & case_output["forensic_hypothesis"].isin({"plausible_precursor_day", "episode_aligned_day"})
    ).astype(int)
    case_output = case_output.loc[:, CASE_COLS].sort_values(["site", "date"]).reset_index(drop=True)

    return summary_output, site_output, case_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_output, site_output, case_output = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_output.to_csv(
        out_dir / "common_cause_precursor_decision_summary_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    site_output.to_csv(
        out_dir / "common_cause_precursor_decision_sites_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    case_output.to_csv(
        out_dir / "common_cause_precursor_decision_cases_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    print(f"common_cause_precursor_decision_cases_v1={len(case_output)}")


if __name__ == "__main__":
    main()
