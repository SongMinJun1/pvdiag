#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["kernelog1", "sinhyo", "gangui", "ktc_ess"]
RETURN_COLS = [
    "site",
    "panel_id",
    "our_bucket",
    "our_dominant_family",
    "our_phenotype",
    "our_comment",
    "field_match",
    "actual_issue_type",
    "issue_detected_date",
    "issue_started_estimated_date",
    "action_taken",
    "note",
]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Build partner review pack for cross-check")
    ap.add_argument("--prealert-topn", type=int, default=10, help="Top-N prealert candidates per site")
    return ap.parse_args()


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def first_value(df: pd.DataFrame, col: str):
    if df.empty or col not in df.columns:
        return pd.NA
    value = df.iloc[0][col]
    return value if pd.notna(value) else pd.NA


def has_value(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    return pd.to_datetime(df[col], errors="coerce").notna()


def as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    return pd.to_numeric(series, errors="coerce").fillna(0).ne(0)


def review_priority(df: pd.DataFrame) -> pd.Series:
    dead = has_value(df, "dead_diag_date")
    critical = has_value(df, "critical_diag_date")
    online = has_value(df, "diagnosis_date_online")
    final_fault = as_bool(df.get("final_fault", pd.Series(False, index=df.index)))
    out = pd.Series("final", index=df.index)
    out.loc[online] = "online"
    out.loc[critical] = "critical"
    out.loc[dead] = "dead"
    out.loc[~(dead | critical | online | final_fault)] = pd.NA
    return out


def site_note_map(manual_df: pd.DataFrame) -> dict[str, str]:
    if manual_df.empty or "site" not in manual_df.columns:
        return {}
    notes = {}
    for site, _ in manual_df.groupby(manual_df["site"].astype(str)):
        notes[site] = "gangui field notes were used as qualitative reference only, not exact validation" if site == "gangui" else ""
    return notes


def empty_return_sheet() -> pd.DataFrame:
    return pd.DataFrame(columns=RETURN_COLS)


def build_site_frames(root: Path, site: str, topn: int, note_map: dict[str, str]):
    out_dir = root / "data" / site / "out"
    summary = read_csv_or_empty(out_dir / "latest_site_summary.csv")
    alerts = read_csv_or_empty(out_dir / "latest_alerts_enriched.csv")
    pheno_summary = read_csv_or_empty(out_dir / "latest_site_phenotype_summary.csv")

    latest_date = first_value(summary, "latest_date")
    site_summary_df = pd.DataFrame(
        [
            {
                "site": site,
                "latest_date": latest_date,
                "panel_count": first_value(summary, "panel_count"),
                "alert_count": first_value(summary, "alert_count"),
                "online_diag_count": first_value(summary, "online_diag_count"),
                "critical_count": first_value(summary, "critical_count"),
                "dead_count": first_value(summary, "dead_count"),
                "final_fault_count": first_value(summary, "final_fault_count"),
                "dominant_electrical_count": first_value(pheno_summary, "dominant_electrical_count"),
                "dominant_shape_count": first_value(pheno_summary, "dominant_shape_count"),
                "dominant_instability_count": first_value(pheno_summary, "dominant_instability_count"),
                "compound_count": first_value(pheno_summary, "compound_count"),
            }
        ]
    )

    if alerts.empty:
        return site_summary_df, pd.DataFrame(), pd.DataFrame(), empty_return_sheet()

    alerts = alerts.copy()
    alerts["site"] = site
    alerts["latest_date"] = latest_date

    event_mask = (
        has_value(alerts, "diagnosis_date_online")
        | has_value(alerts, "critical_diag_date")
        | has_value(alerts, "dead_diag_date")
        | as_bool(alerts.get("final_fault", pd.Series(False, index=alerts.index)))
    )
    event_df = alerts.loc[event_mask].copy()
    event_df["review_priority"] = review_priority(event_df)
    prio_order = {"dead": 0, "critical": 1, "online": 2, "final": 3}
    if not event_df.empty:
        event_df["_prio"] = event_df["review_priority"].map(prio_order).fillna(99)
        event_df = event_df.sort_values(["site", "_prio", "risk_ens"], ascending=[True, True, False]).drop(columns=["_prio"])
    event_cols = [
        "site",
        "panel_id",
        "latest_date",
        "diagnosis_date_online",
        "critical_diag_date",
        "dead_diag_date",
        "final_fault",
        "risk_ens",
        "risk_day",
        "phenotype",
        "dominant_family",
        "top_score",
        "evidence_strength",
        "phenotype_event_date",
        "review_priority",
    ]
    event_df = event_df[[c for c in event_cols if c in event_df.columns]].copy()

    prealert_df = alerts.loc[~event_mask].copy()
    if not prealert_df.empty:
        sort_col = "risk_ens" if "risk_ens" in prealert_df.columns else "risk_day"
        prealert_df = prealert_df.sort_values(sort_col, ascending=False, na_position="last").head(topn).copy()
        prealert_df["review_priority"] = range(1, len(prealert_df) + 1)
    prealert_cols = [
        "site",
        "panel_id",
        "latest_date",
        "risk_ens",
        "risk_day",
        "phenotype",
        "dominant_family",
        "top_score",
        "second_score",
        "margin_top2",
        "evidence_strength",
        "phenotype_event_date",
        "review_priority",
    ]
    prealert_df = prealert_df[[c for c in prealert_cols if c in prealert_df.columns]].copy()

    our_comment = note_map.get(site, "")
    return_sheet = pd.concat(
        [
            pd.DataFrame(
                {
                    "site": event_df.get("site", pd.Series(dtype=object)),
                    "panel_id": event_df.get("panel_id", pd.Series(dtype=object)),
                    "our_bucket": "event_candidate",
                    "our_dominant_family": event_df.get("dominant_family", pd.Series(dtype=object)),
                    "our_phenotype": event_df.get("phenotype", pd.Series(dtype=object)),
                    "our_comment": our_comment,
                }
            ),
            pd.DataFrame(
                {
                    "site": prealert_df.get("site", pd.Series(dtype=object)),
                    "panel_id": prealert_df.get("panel_id", pd.Series(dtype=object)),
                    "our_bucket": "prealert_candidate",
                    "our_dominant_family": prealert_df.get("dominant_family", pd.Series(dtype=object)),
                    "our_phenotype": prealert_df.get("phenotype", pd.Series(dtype=object)),
                    "our_comment": our_comment,
                }
            ),
        ],
        ignore_index=True,
    )
    for col in RETURN_COLS:
        if col not in return_sheet.columns:
            return_sheet[col] = pd.NA
    return_sheet = return_sheet[RETURN_COLS].copy()

    return site_summary_df, event_df, prealert_df, return_sheet


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    out_dir = root / "_share" / "partner_review_pack_latest"
    out_dir.mkdir(parents=True, exist_ok=True)

    manual_df = read_csv_or_empty(root / "docs" / "internal" / "manual_field_evidence_latest.csv")
    note_map = site_note_map(manual_df)

    summary_frames = []
    event_frames = []
    prealert_frames = []
    return_frames = []
    for site in SITES:
        site_summary_df, event_df, prealert_df, return_sheet = build_site_frames(root, site, args.prealert_topn, note_map)
        summary_frames.append(site_summary_df)
        event_frames.append(event_df)
        prealert_frames.append(prealert_df)
        return_frames.append(return_sheet)

    site_summary = pd.concat(summary_frames, ignore_index=True)
    event_candidates = pd.concat(event_frames, ignore_index=True)
    prealert_candidates = pd.concat(prealert_frames, ignore_index=True)
    return_sheet = pd.concat(return_frames, ignore_index=True)

    site_summary.to_csv(out_dir / "site_summary.csv", index=False, encoding="utf-8-sig")
    event_candidates.to_csv(out_dir / "event_candidates.csv", index=False, encoding="utf-8-sig")
    prealert_candidates.to_csv(out_dir / "prealert_candidates.csv", index=False, encoding="utf-8-sig")
    return_sheet.to_csv(out_dir / "return_sheet.csv", index=False, encoding="utf-8-sig")

    xlsx_path = out_dir / "partner_review_pack.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        site_summary.to_excel(writer, sheet_name="site_summary", index=False)
        event_candidates.to_excel(writer, sheet_name="event_candidates", index=False)
        prealert_candidates.to_excel(writer, sheet_name="prealert_candidates", index=False)
        return_sheet.to_excel(writer, sheet_name="return_sheet", index=False)

    print(f"[OK] wrote {out_dir / 'site_summary.csv'}")
    print(f"[OK] wrote {out_dir / 'event_candidates.csv'}")
    print(f"[OK] wrote {out_dir / 'prealert_candidates.csv'}")
    print(f"[OK] wrote {out_dir / 'return_sheet.csv'}")
    print(f"[OK] wrote {xlsx_path}")
    print(f"[COUNT] event_candidates={len(event_candidates)}")
    print(f"[COUNT] prealert_candidates={len(prealert_candidates)}")


if __name__ == "__main__":
    main()
