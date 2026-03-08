#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_topk.py
- Input: scores_with_risk_and_loss.csv
- Output: topK daily report + summary json
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--horizon", type=int, default=14)
    ap.add_argument("--k", type=int, default=50)
    ap.add_argument("--risk-col", default="risk_day")
    ap.add_argument("--events", default=None,
                    help="Optional fault_events.csv (panel_id,onset_date,...) for lead-time case study.")
    ap.add_argument("--cp-alarm-col", default="cp_alarm")
    return ap.parse_args()


def main():
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.inp, encoding="utf-8-sig")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["panel_id"] = df["panel_id"].astype(str)

    H = int(args.horizon)
    loss_col = f"future_loss_{H}d"
    if loss_col not in df.columns:
        raise ValueError(f"Missing column: {loss_col}")

    risk_col = str(args.risk_col)
    if risk_col not in df.columns:
        raise ValueError(f"Missing risk column: {risk_col}")

    # filter valid rows
    valid = df["date"].notna() & df["panel_id"].notna()
    valid = valid & np.isfinite(pd.to_numeric(df[risk_col], errors="coerce"))
    valid = valid & np.isfinite(pd.to_numeric(df[loss_col], errors="coerce"))
    if "data_bad" in df.columns:
        valid = valid & (~df["data_bad"].astype(bool))
    dfx = df.loc[valid].copy()

    K = int(args.k)

    daily_rows = []
    selected_counts = {}

    for d, g in dfx.groupby("date", sort=True):
        if len(g) < K:
            continue
        g = g.sort_values(risk_col, ascending=False)

        top = g.head(K)
        all_loss = float(np.nansum(pd.to_numeric(g[loss_col], errors="coerce").to_numpy(dtype=float)))
        top_loss = float(np.nansum(pd.to_numeric(top[loss_col], errors="coerce").to_numpy(dtype=float)))

        # capture rate of future loss (how much of total future loss is covered by top-K)
        capture = (top_loss / all_loss) if all_loss > 1e-12 else np.nan

        # precision@K if highloss_q exists
        prec = np.nan
        if "highloss_q" in g.columns:
            prec = float(np.mean(top["highloss_q"].astype(bool).to_numpy()))

        daily_rows.append({
            "date": d,
            "n": int(len(g)),
            "k": int(K),
            "mean_loss_all": float(np.nanmean(pd.to_numeric(g[loss_col], errors="coerce"))),
            "mean_loss_topk": float(np.nanmean(pd.to_numeric(top[loss_col], errors="coerce"))),
            "sum_loss_all": float(all_loss),
            "sum_loss_topk": float(top_loss),
            "capture_rate": float(capture),
            "precision_at_k": float(prec),
        })

        # workload
        for pid in top["panel_id"].astype(str).to_list():
            selected_counts[pid] = selected_counts.get(pid, 0) + 1

    daily = pd.DataFrame(daily_rows)
    daily_path = out_dir / f"topk_daily_h{H}_k{K}.csv"
    daily.to_csv(daily_path, index=False, encoding="utf-8-sig")

    # summary
    summary: Dict[str, Any] = {
        "horizon_days": H,
        "k": K,
        "risk_col": risk_col,
        "n_days_evaluated": int(len(daily)),
        "mean_capture_rate": float(np.nanmean(daily["capture_rate"])) if len(daily) else np.nan,
        "mean_precision_at_k": float(np.nanmean(daily["precision_at_k"])) if ("precision_at_k" in daily.columns and len(daily)) else np.nan,
        "mean_loss_topk": float(np.nanmean(daily["mean_loss_topk"])) if len(daily) else np.nan,
        "mean_loss_all": float(np.nanmean(daily["mean_loss_all"])) if len(daily) else np.nan,
        "workload": {
            "n_panels_selected_at_least_once": int(len(selected_counts)),
            "top10_panels_by_selection_days": sorted(selected_counts.items(), key=lambda kv: kv[1], reverse=True)[:10],
        },
    }

    # optional lead-time on provided fault events
    if args.events:
        ev = pd.read_csv(args.events, encoding="utf-8-sig")
        if "panel_id" in ev.columns and "onset_date" in ev.columns:
            ev["panel_id"] = ev["panel_id"].astype(str)
            ev["onset_date"] = pd.to_datetime(ev["onset_date"], errors="coerce").dt.normalize()

            cp_col = str(args.cp_alarm_col)
            if cp_col in df.columns:
                df_cp = df.copy()
                df_cp["cp_alarm"] = df_cp[cp_col].astype(bool)
                df_cp["risk_val"] = pd.to_numeric(df_cp[risk_col], errors="coerce")

                lead_rows = []
                for _, r in ev.iterrows():
                    pid = r["panel_id"]
                    onset = r["onset_date"]
                    if pd.isna(onset):
                        continue
                    hist = df_cp[(df_cp["panel_id"] == pid) & (df_cp["date"] <= onset)].sort_values("date")
                    if len(hist) == 0:
                        continue
                    # first cp_alarm before onset
                    alarm_days = hist[hist["cp_alarm"].astype(bool)]
                    first_alarm = alarm_days["date"].min() if len(alarm_days) else pd.NaT
                    lead_cp = (onset - first_alarm).days if pd.notna(first_alarm) else None

                    # risk threshold: top 95% of that panel's history as a simple marker (not claiming universality)
                    rv = hist["risk_val"].to_numpy(dtype=float)
                    rv = rv[np.isfinite(rv)]
                    thr = float(np.nanquantile(rv, 0.95)) if rv.size else np.nan
                    first_risk = hist[hist["risk_val"] >= thr]["date"].min() if np.isfinite(thr) else pd.NaT
                    lead_risk = (onset - first_risk).days if pd.notna(first_risk) else None

                    lead_rows.append({
                        "panel_id": pid,
                        "onset_date": str(onset.date()),
                        "first_cp_alarm": str(first_alarm.date()) if pd.notna(first_alarm) else "",
                        "lead_days_cp_alarm": lead_cp if lead_cp is not None else "",
                        "risk_p95_thr": thr if np.isfinite(thr) else "",
                        "first_risk_p95": str(first_risk.date()) if pd.notna(first_risk) else "",
                        "lead_days_risk_p95": lead_risk if lead_risk is not None else "",
                    })

                lead_df = pd.DataFrame(lead_rows)
                lead_path = out_dir / "leadtime_case_study.csv"
                lead_df.to_csv(lead_path, index=False, encoding="utf-8-sig")
                summary["leadtime_case_study_path"] = str(lead_path)

    summary_path = out_dir / f"topk_report_h{H}_k{K}.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote: {daily_path}")
    print(f"[OK] wrote: {summary_path}")


if __name__ == "__main__":
    main()
