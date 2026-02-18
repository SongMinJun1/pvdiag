#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_fault_topk_leadtime.py
- 실제 fault event(onset_date)을 기준으로:
  - onset 이전 pre_window 기간 동안
  - 각 날짜에서 fault panel이 ranker 기준 Top-K에 언제 처음 들어오는지(리드타임)를 계산
- Output:
  - research/reports/<site>/fault_topk_leadtime.csv
"""

from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def _to_dt_norm(s):
    return pd.to_datetime(s, errors="coerce").dt.normalize()


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", required=True, help="scores_with_risk.csv or scores_with_risk_loss14d.csv")
    ap.add_argument("--events", required=True, help="fault_events_auto.csv")
    ap.add_argument("--out", required=True, help="output csv")
    ap.add_argument("--pre-window", type=int, default=120, help="days before onset to scan")
    ap.add_argument("--ks", default="10,20,50", help="comma-separated K list")
    ap.add_argument("--rankers", default="risk_day,cp_score,level_drop,dtw_rank,ae_rank",
                    help="comma-separated ranker columns (descending order)")
    ap.add_argument("--require-finite", default="risk_day",
                    help="only evaluate days where this column is finite for all panels")
    return ap.parse_args()


def main():
    args = parse_args()
    df = pd.read_csv(args.scores, encoding="utf-8-sig", low_memory=False)
    ev = pd.read_csv(args.events, encoding="utf-8-sig", low_memory=False)

    df["date"] = _to_dt_norm(df["date"])
    df["panel_id"] = df["panel_id"].astype(str)

    ev["panel_id"] = ev["panel_id"].astype(str)
    ev["onset_date"] = _to_dt_norm(ev["onset_date"])

    ks = [int(x.strip()) for x in args.ks.split(",") if x.strip()]
    rankers = [x.strip() for x in args.rankers.split(",") if x.strip()]
    req = args.require_finite

    out_rows = []
    for _, r in ev.iterrows():
        pid = r["panel_id"]
        onset = r["onset_date"]
        if pd.isna(onset):
            continue

        start = onset - pd.Timedelta(days=int(args.pre_window))
        end = onset - pd.Timedelta(days=1)

        # date subset
        sub = df[(df["date"]>=start) & (df["date"]<=end)].copy()
        if "data_bad" in sub.columns:
            sub = sub[~sub["data_bad"].astype(bool)]

        # per day ranking
        for rk in rankers:
            if rk not in sub.columns:
                continue

            # compute earliest date where fault panel rank <= K
            first_dates = {k: pd.NaT for k in ks}
            best_rank = np.inf
            n_days = 0

            for d, g in sub.groupby("date", sort=True):
                # require finite
                if req in g.columns:
                    if not np.isfinite(pd.to_numeric(g[req], errors="coerce")).any():
                        continue

                vals = pd.to_numeric(g[rk], errors="coerce")
                if vals.notna().sum() < 3:
                    continue

                g2 = g.copy()
                g2["_v"] = vals
                g2 = g2[g2["_v"].notna()]
                if len(g2) < 3:
                    continue

                g2 = g2.sort_values("_v", ascending=False)
                n_days += 1

                # rank of pid
                pos = np.where(g2["panel_id"].to_numpy() == pid)[0]
                if pos.size == 0:
                    continue
                rank = int(pos[0]) + 1
                best_rank = min(best_rank, rank)

                for k in ks:
                    if pd.isna(first_dates[k]) and rank <= k:
                        first_dates[k] = d

            for k in ks:
                fd = first_dates[k]
                lead = (onset - fd).days if pd.notna(fd) else np.nan
                out_rows.append({
                    "panel_id": pid,
                    "onset_date": str(onset.date()),
                    "ranker": rk,
                    "k": k,
                    "first_topk_date": str(fd.date()) if pd.notna(fd) else "",
                    "lead_days_topk": lead,
                    "best_rank_in_window": int(best_rank) if np.isfinite(best_rank) else "",
                    "n_days_evaluated": n_days,
                })

    out = pd.DataFrame(out_rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False, encoding="utf-8-sig")
    print("[OK] wrote", args.out)
    print(out.sort_values(["panel_id","ranker","k"]).to_string(index=False))


if __name__ == "__main__":
    main()
