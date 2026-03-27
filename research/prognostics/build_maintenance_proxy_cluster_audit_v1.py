#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
SELECTED_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "current_actionability_v3",
    "shadow_actionability_v3",
    "strict_method",
    "shadow_frac",
    "group_off_frac",
    "recovery_reset",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "v_drop",
    "coverage_mid",
    "strict_day_group_like_flag",
    "same_group_zero_like_count",
    "same_site_zero_like_count",
    "vendor_reply_class",
    "vendor_fault_family",
    "note",
]
REAUDIT_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity",
    "review_priority",
]
VENDOR_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "vendor_reply_class",
    "vendor_fault_family",
    "vendor_note",
]
ONSET_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
]
SUMMARY_COLS = [
    "record_type",
    "total_selected_cases",
    "total_site_events",
    "total_group_clusters",
    "median_group_cluster_size",
    "p90_group_cluster_size",
    "max_group_cluster_size",
    "site_events_ge_5_selected_count",
    "site_events_ge_10_selected_count",
    "group_clusters_ge_3_members_count",
    "broad_site_day_cluster_count",
    "concentrated_group_cluster_count",
    "singleton_cluster_count",
    "ambiguous_cluster_count",
    "selected_cases_with_vendor_positive_context",
    "selected_cases_with_vendor_rejected_context",
    "selected_cases_with_manual_positive_context",
    "selected_cases_with_manual_negative_context",
    "site",
    "strict_trigger_date",
    "site_event_id",
    "site_event_selected_count",
    "site_event_group_cluster_count",
    "max_group_cluster_size_site_event",
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
    "site_event_selected_count",
    "site_event_group_cluster_count",
    "group_cluster_share_of_site_event",
    "vendor_positive_member_count",
    "vendor_rejected_member_count",
    "manual_positive_member_count",
    "manual_negative_member_count",
    "onset_recent_member_count",
    "onset_long_horizon_member_count",
    "median_same_group_zero_like_count",
    "max_same_group_zero_like_count",
    "median_same_site_zero_like_count",
    "max_same_site_zero_like_count",
    "cluster_interpretation",
    "recommended_use",
]
CASE_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "site_event_id",
    "group_cluster_id",
    "fallback_group_proxy",
    "current_actionability_v3",
    "shadow_actionability_v3",
    "strict_method",
    "shadow_frac",
    "group_off_frac",
    "recovery_reset",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "strict_day_group_like_flag",
    "same_group_zero_like_count",
    "same_site_zero_like_count",
    "vendor_reply_class",
    "vendor_fault_family",
    "candidate_validity",
    "review_priority",
    "vendor_positive_context_flag",
    "vendor_rejected_context_flag",
    "manual_positive_context_flag",
    "manual_negative_context_flag",
    "onset_recent_flag",
    "onset_long_horizon_flag",
    "group_cluster_member_count",
    "site_event_selected_count",
    "group_cluster_share_of_site_event",
    "cluster_interpretation",
    "recommended_use",
    "note",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit whether maintenance-proxy shadow selections are better interpreted as same-day group/common-cause incidents."
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


def to_bool(value: object) -> bool:
    return normalize_text(value).lower() in {"1", "true", "t", "yes", "y"}


def to_int_flag(value: object) -> int:
    return 1 if to_bool(value) else 0


def safe_metric(numer: int | float, denom: int | float) -> float:
    if denom <= 0:
        return 0.0
    return round(float(numer / denom), 6)


def fallback_group_key(panel_id: object) -> str:
    parts = normalize_text(panel_id).split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return normalize_text(panel_id)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def dedupe(df: pd.DataFrame, name: str, cols: list[str]) -> pd.DataFrame:
    dupes = df.loc[df.duplicated(subset=cols, keep=False), cols]
    if not dupes.empty:
        raise SystemExit(f"{name} has duplicate rows on {cols}")
    return df


def join_pipe(values: pd.Series) -> str:
    cleaned = sorted({normalize_text(value) for value in values if normalize_text(value)})
    return "|".join(cleaned)


def cluster_interpretation(member_panel_count: int, site_event_selected_count: int, share: float) -> tuple[str, str]:
    if site_event_selected_count >= 10 and share < 0.50:
        return "broad_site_day_cluster", "common_cause_site_event_signal"
    if member_panel_count >= 3 and share >= 0.50:
        return "concentrated_group_cluster", "common_cause_group_signal"
    if member_panel_count == 1:
        return "singleton_cluster", "panel_level_review_signal"
    return "ambiguous_cluster", "needs_manual_cluster_review"


def load_core_site(root: Path, site: str) -> pd.DataFrame:
    path = root / "data" / site / "out" / "panel_day_core.csv"
    df = read_csv(path)
    if "panel_id" not in df.columns or "date" not in df.columns:
        raise SystemExit(f"panel_day_core.csv missing key columns for site={site}")

    df["site"] = site
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["strict_trigger_date"] = df["date"].map(normalize_date)
    df = df.drop_duplicates(subset=KEY_COLS, keep="first").copy()

    if "group_key_base" not in df.columns:
        df["group_key_base"] = ""
    df["group_key_base"] = df["group_key_base"].map(normalize_text)
    missing_group = df["group_key_base"].eq("")
    df.loc[missing_group, "group_key_base"] = df.loc[missing_group, "panel_id"].map(fallback_group_key)

    return df.loc[:, KEY_COLS + ["group_key_base"]].rename(columns={"group_key_base": "fallback_group_proxy"})


def load_core_all(root: Path, sites: list[str]) -> pd.DataFrame:
    frames = [load_core_site(root, site) for site in sites]
    if not frames:
        return pd.DataFrame(columns=KEY_COLS + ["fallback_group_proxy"])
    return pd.concat(frames, ignore_index=True)


def build_cases(root: Path, sites: list[str]) -> pd.DataFrame:
    selected_df = read_csv(root / "_share" / "maintenance_proxy_shadow_selected_cases_v1.csv")
    reaudit_df = read_csv(root / "_share" / "panel_date_reaudit_working.csv")
    vendor_df = read_csv(root / "_share" / "vendor_reply_adjudication_latest.csv")
    onset_df = read_csv(root / "_share" / "panel_onset_shadow_latest.csv")

    ensure_columns(selected_df, SELECTED_REQUIRED_COLS, "maintenance_proxy_shadow_selected_cases_v1.csv")
    ensure_columns(reaudit_df, REAUDIT_REQUIRED_COLS, "panel_date_reaudit_working.csv")
    ensure_columns(vendor_df, VENDOR_REQUIRED_COLS, "vendor_reply_adjudication_latest.csv")
    ensure_columns(onset_df, ONSET_REQUIRED_COLS, "panel_onset_shadow_latest.csv")

    for df in [selected_df, reaudit_df, vendor_df, onset_df]:
        for col in ["site", "panel_id"]:
            df[col] = df[col].map(normalize_text)
        df["strict_trigger_date"] = df["strict_trigger_date"].map(normalize_date)

    text_cols_selected = [
        "current_actionability_v3",
        "shadow_actionability_v3",
        "strict_method",
        "recovery_reset",
        "onset_confidence",
        "onset_method",
        "vendor_reply_class",
        "vendor_fault_family",
        "note",
    ]
    for col in text_cols_selected:
        selected_df[col] = selected_df[col].map(normalize_text)
    for col in ["candidate_validity", "review_priority"]:
        reaudit_df[col] = reaudit_df[col].map(normalize_text)
    for col in ["vendor_reply_class", "vendor_fault_family", "vendor_note"]:
        vendor_df[col] = vendor_df[col].map(normalize_text)
    for col in ["onset_confidence", "onset_method"]:
        onset_df[col] = onset_df[col].map(normalize_text)

    numeric_cols_selected = [
        "shadow_frac",
        "group_off_frac",
        "days_earlier_than_trigger",
        "mid_ratio",
        "mid_v_ratio",
        "mid_i_ratio",
        "v_drop",
        "coverage_mid",
        "same_group_zero_like_count",
        "same_site_zero_like_count",
    ]
    for col in numeric_cols_selected:
        selected_df[col] = pd.to_numeric(selected_df[col], errors="coerce")
    selected_df["strict_day_group_like_flag"] = selected_df["strict_day_group_like_flag"].map(to_bool)
    onset_df["days_earlier_than_trigger"] = pd.to_numeric(onset_df["days_earlier_than_trigger"], errors="coerce")

    selected_df = dedupe(selected_df.loc[:, KEY_COLS + [c for c in SELECTED_REQUIRED_COLS if c not in KEY_COLS]], "maintenance_proxy_shadow_selected_cases_v1.csv", KEY_COLS)
    reaudit_unique = dedupe(reaudit_df.loc[:, REAUDIT_REQUIRED_COLS], "panel_date_reaudit_working.csv", KEY_COLS)
    vendor_unique = dedupe(vendor_df.loc[:, VENDOR_REQUIRED_COLS], "vendor_reply_adjudication_latest.csv", KEY_COLS).rename(
        columns={
            "vendor_reply_class": "vendor_reply_class_vendor",
            "vendor_fault_family": "vendor_fault_family_vendor",
            "vendor_note": "vendor_note_vendor",
        }
    )
    onset_unique = dedupe(onset_df.loc[:, ONSET_REQUIRED_COLS], "panel_onset_shadow_latest.csv", KEY_COLS).rename(
        columns={
            "days_earlier_than_trigger": "days_earlier_than_trigger_onset",
            "onset_confidence": "onset_confidence_onset",
            "onset_method": "onset_method_onset",
        }
    )
    core_all = load_core_all(root, sites)

    cases = selected_df.merge(reaudit_unique, on=KEY_COLS, how="left")
    cases = cases.merge(vendor_unique, on=KEY_COLS, how="left")
    cases = cases.merge(onset_unique, on=KEY_COLS, how="left")
    cases = cases.merge(core_all, on=KEY_COLS, how="left")

    missing_group = cases["fallback_group_proxy"].fillna("").eq("")
    cases.loc[missing_group, "fallback_group_proxy"] = cases.loc[missing_group, "panel_id"].map(fallback_group_key)

    cases["vendor_reply_class"] = cases.apply(
        lambda row: normalize_text(row["vendor_reply_class"]) or normalize_text(row.get("vendor_reply_class_vendor", "")),
        axis=1,
    )
    cases["vendor_fault_family"] = cases.apply(
        lambda row: normalize_text(row["vendor_fault_family"]) or normalize_text(row.get("vendor_fault_family_vendor", "")),
        axis=1,
    )
    cases["note"] = cases.apply(
        lambda row: normalize_text(row["note"]) or normalize_text(row.get("vendor_note_vendor", "")),
        axis=1,
    )
    cases["days_earlier_than_trigger"] = cases["days_earlier_than_trigger"].where(
        cases["days_earlier_than_trigger"].notna(), cases["days_earlier_than_trigger_onset"]
    )
    cases["onset_confidence"] = cases.apply(
        lambda row: normalize_text(row["onset_confidence"]) or normalize_text(row.get("onset_confidence_onset", "")),
        axis=1,
    )
    cases["onset_method"] = cases.apply(
        lambda row: normalize_text(row["onset_method"]) or normalize_text(row.get("onset_method_onset", "")),
        axis=1,
    )

    cases["site_event_id"] = cases.apply(
        lambda row: f"{row['site']}:{row['strict_trigger_date']}",
        axis=1,
    )
    cases["group_cluster_id"] = cases.apply(
        lambda row: f"{row['site']}:{row['strict_trigger_date']}:{row['fallback_group_proxy']}",
        axis=1,
    )

    vendor_positive = {"field_confirmed_positive", "vendor_pattern_positive", "vendor_likely_positive"}
    cases["vendor_positive_context_flag"] = cases["vendor_reply_class"].isin(vendor_positive).astype(int)
    cases["vendor_rejected_context_flag"] = cases["vendor_reply_class"].eq("vendor_rejected").astype(int)
    cases["manual_positive_context_flag"] = cases["candidate_validity"].isin({"true_positive", "group_side"}).astype(int)
    cases["manual_negative_context_flag"] = cases["candidate_validity"].eq("false_positive").astype(int)
    cases["onset_recent_flag"] = pd.to_numeric(cases["days_earlier_than_trigger"], errors="coerce").le(7).fillna(False).astype(int)
    cases["onset_long_horizon_flag"] = pd.to_numeric(cases["days_earlier_than_trigger"], errors="coerce").ge(30).fillna(False).astype(int)
    return cases


def build_clusters(cases: pd.DataFrame) -> pd.DataFrame:
    site_event_sizes = cases.groupby("site_event_id").size().rename("site_event_selected_count")
    site_event_cluster_counts = cases.groupby("site_event_id")["group_cluster_id"].nunique().rename("site_event_group_cluster_count")

    grouped = cases.groupby("group_cluster_id", dropna=False)
    cluster_rows: list[dict[str, object]] = []
    for group_cluster_id, group in grouped:
        row0 = group.iloc[0]
        member_count = int(len(group))
        site_event_selected_count = int(site_event_sizes[row0["site_event_id"]])
        site_event_group_cluster_count = int(site_event_cluster_counts[row0["site_event_id"]])
        share = safe_metric(member_count, site_event_selected_count)
        interpretation, recommended_use = cluster_interpretation(member_count, site_event_selected_count, share)
        cluster_rows.append(
            {
                "site": row0["site"],
                "strict_trigger_date": row0["strict_trigger_date"],
                "site_event_id": row0["site_event_id"],
                "group_cluster_id": group_cluster_id,
                "fallback_group_proxy": row0["fallback_group_proxy"],
                "member_panel_count": member_count,
                "member_panels": join_pipe(group["panel_id"]),
                "representative_panel_id": sorted(group["panel_id"])[0],
                "site_event_selected_count": site_event_selected_count,
                "site_event_group_cluster_count": site_event_group_cluster_count,
                "group_cluster_share_of_site_event": share,
                "vendor_positive_member_count": int(group["vendor_positive_context_flag"].sum()),
                "vendor_rejected_member_count": int(group["vendor_rejected_context_flag"].sum()),
                "manual_positive_member_count": int(group["manual_positive_context_flag"].sum()),
                "manual_negative_member_count": int(group["manual_negative_context_flag"].sum()),
                "onset_recent_member_count": int(group["onset_recent_flag"].sum()),
                "onset_long_horizon_member_count": int(group["onset_long_horizon_flag"].sum()),
                "median_same_group_zero_like_count": float(pd.to_numeric(group["same_group_zero_like_count"], errors="coerce").median()),
                "max_same_group_zero_like_count": int(pd.to_numeric(group["same_group_zero_like_count"], errors="coerce").max()),
                "median_same_site_zero_like_count": float(pd.to_numeric(group["same_site_zero_like_count"], errors="coerce").median()),
                "max_same_site_zero_like_count": int(pd.to_numeric(group["same_site_zero_like_count"], errors="coerce").max()),
                "cluster_interpretation": interpretation,
                "recommended_use": recommended_use,
            }
        )

    return pd.DataFrame(cluster_rows, columns=CLUSTER_COLS)


def attach_cluster_context(cases: pd.DataFrame, clusters: pd.DataFrame) -> pd.DataFrame:
    cluster_join = clusters.loc[:, [
        "group_cluster_id",
        "member_panel_count",
        "site_event_selected_count",
        "group_cluster_share_of_site_event",
        "cluster_interpretation",
        "recommended_use",
    ]].rename(columns={"member_panel_count": "group_cluster_member_count"})
    enriched = cases.merge(cluster_join, on="group_cluster_id", how="left")
    return enriched.loc[:, CASE_COLS].copy()


def build_summary(cases: pd.DataFrame, clusters: pd.DataFrame) -> pd.DataFrame:
    group_sizes = pd.to_numeric(clusters["member_panel_count"], errors="coerce") if not clusters.empty else pd.Series(dtype=float)
    site_event_view = clusters.groupby(["site", "strict_trigger_date", "site_event_id"], as_index=False).agg(
        site_event_selected_count=("site_event_selected_count", "max"),
        site_event_group_cluster_count=("site_event_group_cluster_count", "max"),
        max_group_cluster_size_site_event=("member_panel_count", "max"),
    ) if not clusters.empty else pd.DataFrame(columns=["site", "strict_trigger_date", "site_event_id", "site_event_selected_count", "site_event_group_cluster_count", "max_group_cluster_size_site_event"])

    summary_rows = [
        {
            "record_type": "summary",
            "total_selected_cases": int(len(cases)),
            "total_site_events": int(cases["site_event_id"].nunique()),
            "total_group_clusters": int(len(clusters)),
            "median_group_cluster_size": float(group_sizes.median()) if not group_sizes.empty else 0.0,
            "p90_group_cluster_size": float(group_sizes.quantile(0.9)) if not group_sizes.empty else 0.0,
            "max_group_cluster_size": int(group_sizes.max()) if not group_sizes.empty else 0,
            "site_events_ge_5_selected_count": int(site_event_view["site_event_selected_count"].ge(5).sum()) if not site_event_view.empty else 0,
            "site_events_ge_10_selected_count": int(site_event_view["site_event_selected_count"].ge(10).sum()) if not site_event_view.empty else 0,
            "group_clusters_ge_3_members_count": int(clusters["member_panel_count"].ge(3).sum()) if not clusters.empty else 0,
            "broad_site_day_cluster_count": int(clusters["cluster_interpretation"].eq("broad_site_day_cluster").sum()) if not clusters.empty else 0,
            "concentrated_group_cluster_count": int(clusters["cluster_interpretation"].eq("concentrated_group_cluster").sum()) if not clusters.empty else 0,
            "singleton_cluster_count": int(clusters["cluster_interpretation"].eq("singleton_cluster").sum()) if not clusters.empty else 0,
            "ambiguous_cluster_count": int(clusters["cluster_interpretation"].eq("ambiguous_cluster").sum()) if not clusters.empty else 0,
            "selected_cases_with_vendor_positive_context": int(cases["vendor_positive_context_flag"].sum()),
            "selected_cases_with_vendor_rejected_context": int(cases["vendor_rejected_context_flag"].sum()),
            "selected_cases_with_manual_positive_context": int(cases["manual_positive_context_flag"].sum()),
            "selected_cases_with_manual_negative_context": int(cases["manual_negative_context_flag"].sum()),
            "site": "",
            "strict_trigger_date": "",
            "site_event_id": "",
            "site_event_selected_count": "",
            "site_event_group_cluster_count": "",
            "max_group_cluster_size_site_event": "",
        }
    ]

    for row in site_event_view.itertuples(index=False):
        summary_rows.append(
            {
                "record_type": "site_event",
                "total_selected_cases": "",
                "total_site_events": "",
                "total_group_clusters": "",
                "median_group_cluster_size": "",
                "p90_group_cluster_size": "",
                "max_group_cluster_size": "",
                "site_events_ge_5_selected_count": "",
                "site_events_ge_10_selected_count": "",
                "group_clusters_ge_3_members_count": "",
                "broad_site_day_cluster_count": "",
                "concentrated_group_cluster_count": "",
                "singleton_cluster_count": "",
                "ambiguous_cluster_count": "",
                "selected_cases_with_vendor_positive_context": "",
                "selected_cases_with_vendor_rejected_context": "",
                "selected_cases_with_manual_positive_context": "",
                "selected_cases_with_manual_negative_context": "",
                "site": row.site,
                "strict_trigger_date": row.strict_trigger_date,
                "site_event_id": row.site_event_id,
                "site_event_selected_count": int(row.site_event_selected_count),
                "site_event_group_cluster_count": int(row.site_event_group_cluster_count),
                "max_group_cluster_size_site_event": int(row.max_group_cluster_size_site_event),
            }
        )

    return pd.DataFrame(summary_rows, columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    cases = build_cases(args.root.resolve(), list(args.sites))
    clusters = build_clusters(cases)
    case_output = attach_cluster_context(cases, clusters)
    summary = build_summary(case_output, clusters)

    out_dir = args.root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_dir / "maintenance_proxy_cluster_audit_summary_v1.csv", index=False, encoding="utf-8-sig")
    clusters.to_csv(out_dir / "maintenance_proxy_cluster_audit_clusters_v1.csv", index=False, encoding="utf-8-sig")
    case_output.to_csv(out_dir / "maintenance_proxy_cluster_audit_cases_v1.csv", index=False, encoding="utf-8-sig")
    print(f"maintenance_proxy_cluster_audit_rows_v1={len(case_output)}")


if __name__ == "__main__":
    main()
