#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
V3_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "anchor_date",
    "critical_phenotype_v3",
    "actionability_v3",
    "vendor_reply_class",
    "vendor_fault_family",
]
VENDOR_COLS = ["site", "panel_id", "vendor_reply_class", "vendor_fault_family"]
OUTBOUND_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "anchor_date",
    "critical_phenotype_v3",
    "actionability_v3",
    "vendor_reply_class",
    "vendor_fault_family",
]
CLUSTER_COLS = [
    "site",
    "cluster_id",
    "anchor_date",
    "group_proxy",
    "member_panel_count",
    "member_panels",
    "representative_panel_id",
    "critical_phenotype_v3",
    "vendor_reply_class",
    "vendor_fault_family",
    "recommended_action",
]
INTERNAL_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "anchor_date",
    "critical_phenotype_v3",
    "actionability_v3",
    "internal_review_priority",
    "vendor_reply_class",
    "vendor_fault_family",
]
MONITOR_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "anchor_date",
    "critical_phenotype_v3",
    "actionability_v3",
    "vendor_reply_class",
    "vendor_fault_family",
]
SUMMARY_COLS = [
    "site",
    "outbound_count",
    "common_cause_cluster_count",
    "common_cause_panel_count",
    "singleton_review_count",
    "monitor_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Route critical actionability v3 rows into operational routing buckets and cluster review packs.")
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
        help="Sites to process. Defaults to the known stable sites.",
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


def fallback_group_proxy(panel_id: str) -> str:
    parts = normalize_text(panel_id).split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return normalize_text(panel_id)


def ensure_vendor_df(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=VENDOR_COLS)
    df = read_csv(path)
    missing = [col for col in VENDOR_COLS if col not in df.columns]
    if missing:
        raise SystemExit(f"vendor adjudication input missing columns: {missing}")
    for col in VENDOR_COLS:
        df[col] = df[col].map(normalize_text)
    return df.loc[:, VENDOR_COLS].drop_duplicates(subset=["site", "panel_id"]).copy()


def load_group_proxy(root: Path, site: str) -> pd.DataFrame:
    path = root / "data" / site / "out" / "panel_day_core.csv"
    df = read_csv(path)
    required = ["date", "panel_id"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{path} missing columns: {missing}")
    df = df.copy()
    df["site"] = site
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["anchor_date"] = pd.to_datetime(df["date"], errors="coerce").dt.date.astype("string")
    if "group_key_base" in df.columns:
        df["group_proxy"] = df["group_key_base"].map(normalize_text)
    else:
        df["group_proxy"] = ""
    missing_proxy = df["group_proxy"].eq("")
    df.loc[missing_proxy, "group_proxy"] = df.loc[missing_proxy, "panel_id"].map(fallback_group_proxy)
    return df.loc[:, ["site", "panel_id", "anchor_date", "group_proxy"]].drop_duplicates()


def join_unique(series: pd.Series) -> str:
    values = sorted({normalize_text(v) for v in series if normalize_text(v)})
    return "|".join(values)


def add_vendor_context(v3_df: pd.DataFrame, vendor_df: pd.DataFrame) -> pd.DataFrame:
    if vendor_df.empty:
        return v3_df
    lookup = vendor_df.set_index(["site", "panel_id"], drop=False)
    rows: list[dict[str, object]] = []
    for row in v3_df.itertuples(index=False):
        vendor_row = None
        if (row.site, row.panel_id) in lookup.index:
            vendor_row = lookup.loc[(row.site, row.panel_id)]
            if isinstance(vendor_row, pd.DataFrame):
                vendor_row = vendor_row.iloc[0]
        rows.append(
            {
                **row._asdict(),
                "vendor_reply_class": normalize_text("" if vendor_row is None else vendor_row.get("vendor_reply_class", getattr(row, "vendor_reply_class", ""))) or normalize_text(getattr(row, "vendor_reply_class", "")),
                "vendor_fault_family": normalize_text("" if vendor_row is None else vendor_row.get("vendor_fault_family", getattr(row, "vendor_fault_family", ""))) or normalize_text(getattr(row, "vendor_fault_family", "")),
            }
        )
    return pd.DataFrame(rows)


def route_rows(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    v3_df = read_csv(root / "_share" / "critical_actionability_shadow_v3_latest.csv")
    missing = [col for col in V3_REQUIRED_COLS if col not in v3_df.columns]
    if missing:
        raise SystemExit(f"critical_actionability_shadow_v3_latest.csv missing columns: {missing}")
    vendor_df = ensure_vendor_df(root / "_share" / "vendor_reply_adjudication_latest.csv")

    v3_df = v3_df.copy()
    for col in V3_REQUIRED_COLS:
        v3_df[col] = v3_df[col].map(normalize_text)
    v3_df = v3_df.loc[v3_df["site"].isin(sites)].copy()
    v3_df = add_vendor_context(v3_df, vendor_df)

    group_rows = []
    for site in sites:
        site_df = v3_df.loc[v3_df["site"].eq(site)]
        if site_df.empty:
            continue
        proxy_df = load_group_proxy(root, site)
        group_rows.append(proxy_df)
    if group_rows:
        group_proxy_df = pd.concat(group_rows, ignore_index=True)
    else:
        group_proxy_df = pd.DataFrame(columns=["site", "panel_id", "anchor_date", "group_proxy"])

    merged = v3_df.merge(group_proxy_df, on=["site", "panel_id", "anchor_date"], how="left")
    merged["group_proxy"] = merged["group_proxy"].fillna("").map(normalize_text)
    missing_proxy = merged["group_proxy"].eq("")
    merged.loc[missing_proxy, "group_proxy"] = merged.loc[missing_proxy, "panel_id"].map(fallback_group_proxy)

    outbound = merged.loc[merged["actionability_v3"].eq("maintenance_candidate"), OUTBOUND_COLS].copy()

    common_cause = merged.loc[merged["actionability_v3"].eq("common_cause_review")].copy()
    cluster_records: list[dict[str, object]] = []
    if not common_cause.empty:
        grouped = common_cause.groupby(["site", "anchor_date", "group_proxy"], dropna=False, sort=True)
        for (site, anchor_date, group_proxy), cluster_df in grouped:
            member_panels = sorted(cluster_df["panel_id"].map(normalize_text).tolist())
            representative_panel_id = member_panels[0] if member_panels else ""
            cluster_id = f"{site}:{anchor_date}:{group_proxy}"
            cluster_records.append(
                {
                    "site": site,
                    "cluster_id": cluster_id,
                    "anchor_date": anchor_date,
                    "group_proxy": group_proxy,
                    "member_panel_count": int(len(cluster_df)),
                    "member_panels": "|".join(member_panels),
                    "representative_panel_id": representative_panel_id,
                    "critical_phenotype_v3": join_unique(cluster_df["critical_phenotype_v3"]) or "common_cause_borderline",
                    "vendor_reply_class": join_unique(cluster_df["vendor_reply_class"]),
                    "vendor_fault_family": join_unique(cluster_df["vendor_fault_family"]),
                    "recommended_action": "review_as_common_cause_cluster",
                }
            )
    cluster_df = pd.DataFrame(cluster_records, columns=CLUSTER_COLS)

    internal = merged.loc[merged["actionability_v3"].eq("singleton_review")].copy()
    internal["internal_review_priority"] = internal["vendor_reply_class"].map(
        lambda value: "high" if normalize_text(value) in {"vendor_rejected", "vendor_pattern_positive"} else "medium"
    )
    internal = internal.loc[:, INTERNAL_COLS].copy()

    monitor = merged.loc[merged["actionability_v3"].eq("monitor_only"), MONITOR_COLS].copy()

    summary_records = []
    for site in sites:
        site_rows = merged.loc[merged["site"].eq(site)]
        site_clusters = cluster_df.loc[cluster_df["site"].eq(site)]
        summary_records.append(
            {
                "site": site,
                "outbound_count": int(site_rows["actionability_v3"].eq("maintenance_candidate").sum()),
                "common_cause_cluster_count": int(len(site_clusters)),
                "common_cause_panel_count": int(site_rows["actionability_v3"].eq("common_cause_review").sum()),
                "singleton_review_count": int(site_rows["actionability_v3"].eq("singleton_review").sum()),
                "monitor_count": int(site_rows["actionability_v3"].eq("monitor_only").sum()),
            }
        )
    summary = pd.DataFrame(summary_records, columns=SUMMARY_COLS)

    return outbound, cluster_df, internal, monitor, summary


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"

    outbound, cluster_df, internal, monitor, summary = route_rows(root, list(args.sites))

    outbound.to_csv(share_dir / "critical_outbound_candidates_v4.csv", index=False, encoding="utf-8-sig")
    cluster_df.to_csv(share_dir / "critical_cluster_review_v4.csv", index=False, encoding="utf-8-sig")
    internal.to_csv(share_dir / "critical_internal_review_v4.csv", index=False, encoding="utf-8-sig")
    monitor.to_csv(share_dir / "critical_monitor_archive_v4.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / "critical_case_routing_summary_v4.csv", index=False, encoding="utf-8-sig")

    print(
        "critical_case_router_v4 "
        f"outbound={len(outbound)} "
        f"clusters={len(cluster_df)} "
        f"internal={len(internal)} "
        f"monitor={len(monitor)}"
    )


if __name__ == "__main__":
    main()
