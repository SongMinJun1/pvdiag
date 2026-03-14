#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd

SITES = ["conalog", "sinhyo", "gangui", "ktc_ess"]
PHENO_COLS = [
    "phenotype",
    "dominant_family",
    "top_score",
    "second_score",
    "margin_top2",
    "evidence_strength",
    "phenotype_event_date",
]


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def site_event_tables(root: Path, site: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    events_path = root / "_share" / "site_event_phenotypes_latest.csv"
    events = read_csv_or_empty(events_path)
    if events.empty or "site" not in events.columns:
        site_events = pd.DataFrame(columns=["site", "panel_id", "event_date"])
    else:
        site_events = events[events["site"].astype(str) == site].copy()
    if "event_date" in site_events.columns:
        site_events["event_date"] = pd.to_datetime(site_events["event_date"], errors="coerce")
    else:
        site_events["event_date"] = pd.NaT

    latest = site_events.sort_values(["panel_id", "event_date"], na_position="last").drop_duplicates("panel_id", keep="last").copy()
    latest = latest.rename(columns={"event_date": "phenotype_event_date"})
    keep = [c for c in ["panel_id", "phenotype", "dominant_family", "top_score", "second_score", "margin_top2", "evidence_strength", "phenotype_event_date"] if c in latest.columns]
    latest = latest[keep].copy() if keep else pd.DataFrame(columns=["panel_id"] + PHENO_COLS)
    return site_events, latest


def attach_latest_pheno(df: pd.DataFrame, latest: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    drop_cols = [c for c in PHENO_COLS if c in out.columns]
    if drop_cols:
        out = out.drop(columns=drop_cols)
    if latest.empty:
        for col in PHENO_COLS:
            if col not in out.columns:
                out[col] = pd.NA
        return out
    merged = out.merge(latest, on="panel_id", how="left")
    for col in PHENO_COLS:
        if col not in merged.columns:
            merged[col] = pd.NA
    return merged


def scalar_count(df: pd.DataFrame, site: str, col: str) -> int:
    if df.empty or "site" not in df.columns or col not in df.columns:
        return 0
    sub = df[df["site"].astype(str) == site]
    if sub.empty:
        return 0
    value = pd.to_numeric(sub.iloc[0][col], errors="coerce")
    return int(value) if pd.notna(value) else 0


def write_site_outputs(root: Path, site: str) -> None:
    out_dir = root / "data" / site / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    site_events, latest = site_event_tables(root, site)
    phenotype_counts = read_csv_or_empty(root / "_share" / "site_event_phenotype_counts_latest.csv")
    dominant_counts = read_csv_or_empty(root / "_share" / "site_event_dominant_family_counts_latest.csv")

    latest_events_path = out_dir / "latest_event_phenotypes.csv"
    alerts_path = out_dir / "latest_alerts.csv"
    status_path = out_dir / "latest_panel_status.csv"
    alerts_enriched_path = out_dir / "latest_alerts_enriched.csv"
    status_enriched_path = out_dir / "latest_panel_status_enriched.csv"
    summary_path = out_dir / "latest_site_phenotype_summary.csv"

    event_out = site_events.copy()
    if not event_out.empty and "event_date" in event_out.columns:
        event_out["event_date"] = event_out["event_date"].dt.strftime("%Y-%m-%d")
    event_out.to_csv(latest_events_path, index=False, encoding="utf-8-sig")

    alerts = read_csv_or_empty(alerts_path)
    status = read_csv_or_empty(status_path)
    attach_latest_pheno(alerts, latest).to_csv(alerts_enriched_path, index=False, encoding="utf-8-sig")
    attach_latest_pheno(status, latest).to_csv(status_enriched_path, index=False, encoding="utf-8-sig")

    summary = pd.DataFrame(
        [
            {
                "site": site,
                "event_count": int(len(site_events)),
                "compound_count": scalar_count(phenotype_counts, site, "compound"),
                "shape_count": scalar_count(phenotype_counts, site, "shape"),
                "instability_count": scalar_count(phenotype_counts, site, "instability"),
                "unclear_count": scalar_count(phenotype_counts, site, "unclear"),
                "dominant_electrical_count": scalar_count(dominant_counts, site, "electrical"),
                "dominant_shape_count": scalar_count(dominant_counts, site, "shape"),
                "dominant_instability_count": scalar_count(dominant_counts, site, "instability"),
            }
        ]
    )
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")

    print(f"[OK] {site}: wrote {latest_events_path.name}, {alerts_enriched_path.name}, {status_enriched_path.name}, {summary_path.name}")


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    for site in SITES:
        write_site_outputs(root, site)


if __name__ == "__main__":
    main()
