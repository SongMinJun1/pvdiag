#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_SITES = ["kernelog1", "sinhyo", "gangui", "ktc_ess"]
EVENT_DATE_PRIORITY = [
    "diagnosis_date_online",
    "critical_diag_date",
    "diag_critical_date",
    "dead_diag_date",
    "diag_dead_date",
]
SCORE_COLS = ["level_drop_like", "v_drop_like", "dtw_like", "hs_like", "ae_like"]


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Build GPVS-informed event phenotypes across latest site outputs")
    ap.add_argument("--sites", default=",".join(DEFAULT_SITES), help="Comma-separated site names")
    ap.add_argument("--share-dir", default="_share", help="Output directory")
    return ap.parse_args()


def _find_input(site: str, name: str) -> pathlib.Path:
    candidates = [
        pathlib.Path(f"data/{site}/out/{name}"),
        pathlib.Path(f"data/{site}/raw/out/{name}"),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"{site}: missing {name} in raw/out or out")


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _rank01(series: pd.Series) -> pd.Series:
    s = _numeric(series)
    out = pd.Series(np.nan, index=s.index, dtype=float)
    mask = np.isfinite(s)
    if bool(mask.any()):
        out.loc[mask] = s.loc[mask].rank(method="average", pct=True)
    return out.clip(0.0, 1.0)


def _clip01(series: pd.Series) -> pd.Series:
    return _numeric(series).clip(0.0, 1.0)


def _ensure_like_columns(core: pd.DataFrame) -> pd.DataFrame:
    out = core.copy()

    if "level_drop_like" in out.columns:
        out["level_drop_like"] = _clip01(out["level_drop_like"])
    elif "fault_like_day" in out.columns:
        out["level_drop_like"] = _clip01(out["fault_like_day"])
    elif "mid_ratio" in out.columns:
        out["level_drop_like"] = (1.0 - _numeric(out["mid_ratio"])).clip(0.0, 1.0)
    else:
        out["level_drop_like"] = np.nan

    if "v_drop_like" in out.columns:
        out["v_drop_like"] = _clip01(out["v_drop_like"])
    elif "v_drop" in out.columns:
        out["v_drop_like"] = _clip01(out["v_drop"])
    else:
        out["v_drop_like"] = np.nan

    if "dtw_like" in out.columns:
        out["dtw_like"] = _clip01(out["dtw_like"])
    elif "dtw_dist" in out.columns:
        out["dtw_like"] = _rank01(out["dtw_dist"])
    else:
        out["dtw_like"] = np.nan

    if "hs_like" in out.columns:
        out["hs_like"] = _clip01(out["hs_like"])
    elif "hs_score" in out.columns:
        out["hs_like"] = _rank01(out["hs_score"])
    else:
        out["hs_like"] = np.nan

    if "ae_like" in out.columns:
        out["ae_like"] = _clip01(out["ae_like"])
    elif "ae_strength" in out.columns:
        out["ae_like"] = _clip01(out["ae_strength"])
    elif "recon_error" in out.columns:
        out["ae_like"] = _rank01(out["recon_error"])
    else:
        out["ae_like"] = np.nan

    return out


def _extract_events(site: str, diag: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in diag.iterrows():
        panel_id = row.get("panel_id")
        date_to_cols: dict[pd.Timestamp, list[str]] = {}
        for col in EVENT_DATE_PRIORITY:
            if col not in diag.columns:
                continue
            dt = pd.to_datetime(row.get(col), errors="coerce")
            if pd.isna(dt):
                continue
            dt = dt.normalize()
            date_to_cols.setdefault(dt, []).append(col)
        for event_date, cols in sorted(date_to_cols.items(), key=lambda x: x[0]):
            rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "event_date": event_date,
                    "event_source_cols": ",".join(cols),
                }
            )
    if not rows:
        return pd.DataFrame(columns=["site", "panel_id", "event_date", "event_source_cols"])
    return pd.DataFrame(rows)


def _summarize_event(
    site: str,
    panel_id: str,
    event_date: pd.Timestamp,
    event_source_cols: str,
    core: pd.DataFrame,
    core_path: pathlib.Path,
    diag_path: pathlib.Path,
) -> dict[str, Any]:
    end = pd.to_datetime(event_date).normalize()
    start = end - pd.Timedelta(days=7)
    panel = core[core["panel_id"].astype(str) == str(panel_id)].copy()
    win = panel[(panel["date"] >= start) & (panel["date"] <= end)].sort_values("date")
    rec: dict[str, Any] = {
        "site": site,
        "panel_id": str(panel_id),
        "event_date": end,
        "event_source_cols": event_source_cols,
        "window_start": start,
        "window_end": end,
        "window_rows": int(len(win)),
        "core_path": str(core_path),
        "diagnosis_path": str(diag_path),
    }
    for score_col in SCORE_COLS:
        s = _numeric(win[score_col]) if score_col in win.columns else pd.Series(dtype=float)
        rec[f"{score_col}_mean"] = float(s.mean()) if len(s) else np.nan
        rec[f"{score_col}_max"] = float(s.max()) if len(s) else np.nan
        rec[f"{score_col}_last_day_value"] = float(s.iloc[-1]) if len(s) else np.nan
    return rec


def _safe_max(*vals: Any) -> float:
    nums = [float(v) for v in vals if pd.notna(v)]
    return float(np.max(nums)) if nums else np.nan


def _phenotype_row(row: pd.Series) -> dict[str, Any]:
    electrical = _safe_max(row.get("level_drop_like_max"), row.get("v_drop_like_max"))
    shape = _safe_max(row.get("dtw_like_max"), row.get("ae_like_max"))
    instability = float(row.get("hs_like_max")) if pd.notna(row.get("hs_like_max")) else np.nan

    family_scores = {
        "electrical": electrical,
        "shape": shape,
        "instability": instability,
    }
    finite = {k: v for k, v in family_scores.items() if pd.notna(v)}
    if not finite:
        return {
            "dominant_family": "unclear",
            "top_score": np.nan,
            "second_score": np.nan,
            "margin_top2": np.nan,
            "active_family_count": 0,
            "phenotype": "unclear",
            "evidence_strength": "weak",
            "electrical_score": electrical,
            "shape_score": shape,
            "instability_score": instability,
        }

    ranked = sorted(finite.items(), key=lambda x: x[1], reverse=True)
    dominant_family, top_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else np.nan
    margin = float(top_score - second_score) if pd.notna(second_score) else np.nan
    near_top = []
    for fam, val in finite.items():
        if top_score > 0 and val >= (0.9 * top_score) and val >= 0.55:
            near_top.append(fam)
    active_family_count = len(near_top)

    if not np.isfinite(top_score) or top_score < 0.55:
        phenotype = "unclear"
        strength = "weak"
    elif active_family_count >= 2:
        phenotype = "compound"
        strength = "strong" if top_score >= 0.75 else "medium"
    else:
        phenotype = dominant_family
        if top_score >= 0.8 and (pd.isna(margin) or margin >= 0.15):
            strength = "strong"
        elif top_score >= 0.65:
            strength = "medium"
        else:
            strength = "weak"

    return {
        "dominant_family": dominant_family,
        "top_score": top_score,
        "second_score": second_score,
        "margin_top2": margin,
        "active_family_count": active_family_count,
        "phenotype": phenotype,
        "evidence_strength": strength,
        "electrical_score": electrical,
        "shape_score": shape,
        "instability_score": instability,
    }


def build(site: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    core_path = _find_input(site, "panel_day_core.csv")
    diag_path = _find_input(site, "panel_diagnosis_summary.csv")

    core = pd.read_csv(core_path, low_memory=False)
    diag = pd.read_csv(diag_path)
    core["date"] = pd.to_datetime(core["date"], errors="coerce").dt.normalize()
    core["panel_id"] = core["panel_id"].astype(str)
    diag["panel_id"] = diag["panel_id"].astype(str)
    core = _ensure_like_columns(core)

    events = _extract_events(site, diag)
    if events.empty:
        empty = pd.DataFrame(columns=["site", "panel_id", "event_date"])
        return empty, empty

    summary_rows = [
        _summarize_event(
            site=site,
            panel_id=str(ev["panel_id"]),
            event_date=pd.to_datetime(ev["event_date"]),
            event_source_cols=str(ev["event_source_cols"]),
            core=core,
            core_path=core_path,
            diag_path=diag_path,
        )
        for _, ev in events.iterrows()
    ]
    summary = pd.DataFrame(summary_rows).sort_values(["site", "event_date", "panel_id"]).reset_index(drop=True)
    phenotype_cols = summary.apply(_phenotype_row, axis=1, result_type="expand")
    phenotypes = pd.concat([summary, phenotype_cols], axis=1)
    return summary, phenotypes


def main() -> None:
    args = _parse_args()
    sites = [s.strip() for s in str(args.sites).split(",") if s.strip()]
    share_dir = pathlib.Path(args.share_dir)
    share_dir.mkdir(parents=True, exist_ok=True)

    all_summary = []
    all_pheno = []
    for site in sites:
        summary, phenotypes = build(site)
        all_summary.append(summary)
        all_pheno.append(phenotypes)

    nonempty_summary = [df for df in all_summary if not df.empty]
    nonempty_pheno = [df for df in all_pheno if not df.empty]
    summary_df = pd.concat(nonempty_summary, ignore_index=True) if nonempty_summary else pd.DataFrame()
    pheno_df = pd.concat(nonempty_pheno, ignore_index=True) if nonempty_pheno else pd.DataFrame()

    counts_df = (
        pheno_df.pivot_table(index="site", columns="phenotype", values="panel_id", aggfunc="count", fill_value=0)
        .reset_index()
        if not pheno_df.empty
        else pd.DataFrame(columns=["site"])
    )
    if not counts_df.empty:
        counts_df.columns.name = None

    dom_counts_df = pd.DataFrame(columns=["site"])
    if not pheno_df.empty:
        dom = pheno_df.copy()
        if "dominant_family" not in dom.columns:
            dom["dominant_family"] = "missing"
        dom["dominant_family"] = dom["dominant_family"].fillna("missing").astype(str)
        dom_counts_df = (
            dom.pivot_table(index="site", columns="dominant_family", values="panel_id", aggfunc="count", fill_value=0)
            .reset_index()
        )
        dom_counts_df.columns.name = None

    summary_path = share_dir / "site_event_summary_latest.csv"
    pheno_path = share_dir / "site_event_phenotypes_latest.csv"
    counts_path = share_dir / "site_event_phenotype_counts_latest.csv"
    dom_counts_path = share_dir / "site_event_dominant_family_counts_latest.csv"

    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    pheno_df.to_csv(pheno_path, index=False, encoding="utf-8-sig")
    counts_df.to_csv(counts_path, index=False, encoding="utf-8-sig")
    dom_counts_df.to_csv(dom_counts_path, index=False, encoding="utf-8-sig")

    print(f"[OK] wrote summary: {summary_path}")
    print(f"[OK] wrote phenotypes: {pheno_path}")
    print(f"[OK] wrote counts: {counts_path}")
    print(f"[OK] wrote dominant-family counts: {dom_counts_path}")


if __name__ == "__main__":
    main()
