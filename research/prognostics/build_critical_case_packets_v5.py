#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
V3_REQUIRED_COLS = ["site", "panel_id", "anchor_date", "actionability_v3"]
OUTBOUND_REQUIRED_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "anchor_date",
    "critical_phenotype_v3",
    "actionability_v3",
    "vendor_reply_class",
    "vendor_fault_family",
]
CLUSTER_REQUIRED_COLS = [
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
]
INTERNAL_REQUIRED_COLS = [
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
VENDOR_COLS = ["site", "panel_id", "vendor_reply_class", "vendor_fault_family"]
OUTBOUND_PACK_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "anchor_date",
    "critical_phenotype_v3",
    "actionability_v3",
    "vendor_reply_class",
    "vendor_fault_family",
    "recommended_check_items",
    "cluster_leakage_flag",
    "case_priority",
]
CLUSTER_PACK_COLS = [
    "site",
    "cluster_id",
    "anchor_date",
    "group_proxy",
    "member_panel_count",
    "member_panels",
    "representative_panel_id",
    "recommended_check_items",
    "case_priority",
]
INTERNAL_PACK_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "anchor_date",
    "critical_phenotype_v3",
    "actionability_v3",
    "vendor_reply_class",
    "vendor_fault_family",
    "internal_review_priority",
    "vendor_positive_hold_flag",
    "recommended_check_items",
]
SUMMARY_COLS = [
    "site",
    "outbound_count",
    "outbound_cluster_leakage_count",
    "cluster_count",
    "internal_count",
    "internal_vendor_positive_hold_count",
    "monitor_count",
]
VENDOR_POSITIVE = {"vendor_pattern_positive", "vendor_likely_positive", "field_confirmed_positive"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package critical case routing v4 outputs into review/shareable case packets with sanity flags.")
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


def group_proxy_family(value: object) -> str:
    text = normalize_text(value)
    parts = text.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return text


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


def recommended_check_items(phenotype: str) -> str:
    mapping = {
        "electrical_fault_like": "입력전압 저하/전류 유지/모듈·다이오드·커넥터 확인",
        "open_or_device_issue_like": "입력전압 저하/전류 유지/모듈·다이오드·커넥터 확인",
        "group_or_inverter_side_like": "동일 그룹/인버터/커넥터/상위설비 확인",
        "singleton_borderline_review": "라인차트/댓글/현장기록 재확인",
        "common_cause_borderline": "공통원인(동일 날짜·동일 그룹) 우선 확인",
        "shape_only_monitor": "외부 공유 제외, 추세 모니터링",
        "weak_critical_candidate": "외부 공유 제외, 추세 모니터링",
    }
    return mapping.get(normalize_text(phenotype), "")


def add_vendor_context(df: pd.DataFrame, vendor_df: pd.DataFrame) -> pd.DataFrame:
    if vendor_df.empty:
        return df
    lookup = vendor_df.set_index(["site", "panel_id"], drop=False)
    rows: list[dict[str, object]] = []
    for row in df.itertuples(index=False):
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


def load_inputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    v3 = read_csv(root / "_share" / "critical_actionability_shadow_v3_latest.csv")
    outbound = read_csv(root / "_share" / "critical_outbound_candidates_v4.csv")
    cluster = read_csv(root / "_share" / "critical_cluster_review_v4.csv")
    internal = read_csv(root / "_share" / "critical_internal_review_v4.csv")
    vendor = ensure_vendor_df(root / "_share" / "vendor_reply_adjudication_latest.csv")

    for df, required, name in [
        (v3, V3_REQUIRED_COLS, "critical_actionability_shadow_v3_latest.csv"),
        (outbound, OUTBOUND_REQUIRED_COLS, "critical_outbound_candidates_v4.csv"),
        (cluster, CLUSTER_REQUIRED_COLS, "critical_cluster_review_v4.csv"),
        (internal, INTERNAL_REQUIRED_COLS, "critical_internal_review_v4.csv"),
    ]:
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise SystemExit(f"{name} missing columns: {missing}")

    for df in [v3, outbound, cluster, internal]:
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].map(normalize_text)
    v3 = v3.loc[v3["site"].isin(sites)].copy()
    outbound = outbound.loc[outbound["site"].isin(sites)].copy()
    cluster = cluster.loc[cluster["site"].isin(sites)].copy()
    internal = internal.loc[internal["site"].isin(sites)].copy()
    return v3, outbound, cluster, internal, vendor


def build_packs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    v3, outbound, cluster, internal, vendor = load_inputs(root, sites)

    group_rows = []
    for site in sites:
        if v3["site"].eq(site).any():
            group_rows.append(load_group_proxy(root, site))
    group_df = pd.concat(group_rows, ignore_index=True) if group_rows else pd.DataFrame(columns=["site", "panel_id", "anchor_date", "group_proxy"])

    outbound = add_vendor_context(outbound, vendor)
    outbound = outbound.merge(group_df, on=["site", "panel_id", "anchor_date"], how="left")
    outbound["group_proxy"] = outbound["group_proxy"].fillna("").map(normalize_text)
    missing_proxy = outbound["group_proxy"].eq("")
    outbound.loc[missing_proxy, "group_proxy"] = outbound.loc[missing_proxy, "panel_id"].map(fallback_group_proxy)
    outbound["group_proxy_family"] = outbound["group_proxy"].map(group_proxy_family)

    cluster = cluster.copy()
    cluster["group_proxy_family"] = cluster["group_proxy"].map(group_proxy_family)
    cluster_family_keys = {
        (row.site, row.anchor_date, row.group_proxy_family)
        for row in cluster.itertuples(index=False)
        if normalize_text(row.group_proxy_family)
    }

    outbound["recommended_check_items"] = outbound["critical_phenotype_v3"].map(recommended_check_items)
    outbound["cluster_leakage_flag"] = outbound.apply(
        lambda row: 1
        if (row.site, row.anchor_date, row.group_proxy_family) in cluster_family_keys
        else 0,
        axis=1,
    )
    outbound["case_priority"] = outbound["vendor_reply_class"].map(
        lambda value: "high" if normalize_text(value) in {"field_confirmed_positive", "vendor_pattern_positive"} else "medium"
    )
    outbound_pack = outbound.loc[:, OUTBOUND_PACK_COLS].copy()

    cluster_pack = cluster.copy()
    cluster_pack["recommended_check_items"] = cluster_pack["critical_phenotype_v3"].map(recommended_check_items)
    cluster_pack["case_priority"] = cluster_pack["member_panel_count"].map(lambda n: "high" if pd.to_numeric(n, errors="coerce") >= 3 else "medium")
    cluster_pack = cluster_pack.loc[:, CLUSTER_PACK_COLS].copy()

    outbound_keys = {(row.site, row.panel_id) for row in outbound.itertuples(index=False)}
    internal = add_vendor_context(internal, vendor)
    internal["vendor_positive_hold_flag"] = internal.apply(
        lambda row: 1
        if normalize_text(row.vendor_reply_class) in VENDOR_POSITIVE and (row.site, row.panel_id) not in outbound_keys
        else 0,
        axis=1,
    )
    internal["recommended_check_items"] = internal["critical_phenotype_v3"].map(recommended_check_items)
    internal_pack = internal.loc[:, INTERNAL_PACK_COLS].copy()

    summary_rows = []
    for site in sites:
        site_v3 = v3.loc[v3["site"].eq(site)]
        site_outbound = outbound_pack.loc[outbound_pack["site"].eq(site)]
        site_cluster = cluster_pack.loc[cluster_pack["site"].eq(site)]
        site_internal = internal_pack.loc[internal_pack["site"].eq(site)]
        summary_rows.append(
            {
                "site": site,
                "outbound_count": int(len(site_outbound)),
                "outbound_cluster_leakage_count": int(site_outbound["cluster_leakage_flag"].fillna(0).astype(int).sum()) if not site_outbound.empty else 0,
                "cluster_count": int(len(site_cluster)),
                "internal_count": int(len(site_internal)),
                "internal_vendor_positive_hold_count": int(site_internal["vendor_positive_hold_flag"].fillna(0).astype(int).sum()) if not site_internal.empty else 0,
                "monitor_count": int(site_v3["actionability_v3"].eq("monitor_only").sum()),
            }
        )
    summary = pd.DataFrame(summary_rows, columns=SUMMARY_COLS)

    return outbound_pack, cluster_pack, internal_pack, summary


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"

    outbound_pack, cluster_pack, internal_pack, summary = build_packs(root, list(args.sites))

    outbound_pack.to_csv(share_dir / "critical_outbound_pack_v5.csv", index=False, encoding="utf-8-sig")
    cluster_pack.to_csv(share_dir / "critical_cluster_pack_v5.csv", index=False, encoding="utf-8-sig")
    internal_pack.to_csv(share_dir / "critical_internal_review_pack_v5.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(share_dir / "critical_case_packets_summary_v5.csv", index=False, encoding="utf-8-sig")

    print(
        "critical_case_packets_v5 "
        f"outbound={len(outbound_pack)} "
        f"clusters={len(cluster_pack)} "
        f"internal={len(internal_pack)}"
    )


if __name__ == "__main__":
    main()
