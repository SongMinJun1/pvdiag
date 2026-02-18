#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compare_rankers.py
- 목적: 동일한 future_loss_Hd 라벨에서, 어떤 ranking 컬럼이 Top-K에서 더 잘 잡는지 비교
- 입력: scores_with_risk_loss14d.csv (risk_day, level_drop, ae_rank, dtw_rank, hs_rank, cp_score 등 포함)
- 출력: ranker_compare.csv (ranker별 평균 capture_rate / precision@K / lift / workload)
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="scores_with_risk_lossXd.csv")
    ap.add_argument("--out", dest="out", required=True, help="output csv path")
    ap.add_argument("--horizon", type=int, default=None, help="optional; infer from file if not given")
    ap.add_argument("--ks", default="50", help="comma-separated K list, e.g. 10,20,50")
    ap.add_argument("--cols", nargs="+", required=True, help="ranking columns to compare")
    ap.add_argument("--loss-col", default=None, help="loss col override; default uses future_loss_{H}d")
    ap.add_argument("--require-highloss", action="store_true",
                    help="If set, requires highloss_q exists; otherwise precision/lift may be NaN.")
    return ap.parse_args()


def _to_dt_norm(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce").dt.normalize()


def eval_one(df: pd.DataFrame, loss_col: str, rank_col: str, k: int) -> Dict[str, Any]:
    # valid rows
    valid = df["date"].notna() & df["panel_id"].notna()
    valid = valid & np.isfinite(pd.to_numeric(df[rank_col], errors="coerce"))
    valid = valid & np.isfinite(pd.to_numeric(df[loss_col], errors="coerce"))
    if "data_bad" in df.columns:
        valid = valid & (~df["data_bad"].astype(bool))

    dfx = df.loc[valid].copy()
    if len(dfx) == 0:
        return {"n_days": 0}

    # base positive rate (if label exists)
    base_rate = np.nan
    if "highloss_q" in dfx.columns:
        base_rate = float(np.mean(dfx["highloss_q"].astype(bool).to_numpy()))

    daily_rows = []
    selected_counts: Dict[str, int] = {}

    for d, g in dfx.groupby("date", sort=True):
        if len(g) < k:
            continue
        g = g.sort_values(rank_col, ascending=False)
        top = g.head(k)

        all_loss = float(np.nansum(pd.to_numeric(g[loss_col], errors="coerce").to_numpy(dtype=float)))
        top_loss = float(np.nansum(pd.to_numeric(top[loss_col], errors="coerce").to_numpy(dtype=float)))
        capture = (top_loss / all_loss) if all_loss > 1e-12 else np.nan

        prec = np.nan
        if "highloss_q" in g.columns:
            prec = float(np.mean(top["highloss_q"].astype(bool).to_numpy()))

        daily_rows.append((capture, prec))

        for pid in top["panel_id"].astype(str).to_list():
            selected_counts[pid] = selected_counts.get(pid, 0) + 1

    if not daily_rows:
        return {"n_days": 0}

    captures = np.array([r[0] for r in daily_rows], dtype=float)
    precs = np.array([r[1] for r in daily_rows], dtype=float)

    mean_capture = float(np.nanmean(captures))
    mean_prec = float(np.nanmean(precs)) if np.isfinite(precs).any() else np.nan
    lift = (mean_prec / base_rate) if (np.isfinite(mean_prec) and np.isfinite(base_rate) and base_rate > 1e-12) else np.nan

    top10_work = sorted(selected_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]

    return {
        "rank_col": rank_col,
        "k": int(k),
        "n_days": int(len(daily_rows)),
        "mean_capture_rate": mean_capture,
        "mean_precision_at_k": mean_prec,
        "base_pos_rate": base_rate,
        "lift_vs_base": lift,
        "n_panels_selected_at_least_once": int(len(selected_counts)),
        "top10_panels_by_selection_days": json.dumps(top10_work, ensure_ascii=False),
    }


def main():
    args = parse_args()
    df = pd.read_csv(args.inp, encoding="utf-8-sig", low_memory=False)
    if "date" not in df.columns or "panel_id" not in df.columns:
        raise ValueError("Input must contain date and panel_id.")
    df["date"] = _to_dt_norm(df["date"])
    df["panel_id"] = df["panel_id"].astype(str)

    ks: List[int] = [int(x.strip()) for x in args.ks.split(",") if x.strip()]
    cols: List[str] = args.cols

    H = args.horizon
    if H is None:
        # try to infer from loss columns
        cand = [c for c in df.columns if c.startswith("future_loss_") and c.endswith("d")]
        if cand:
            # pick first one
            H = int(cand[0].replace("future_loss_", "").replace("d", ""))
        else:
            H = 14

    loss_col = args.loss_col or f"future_loss_{H}d"
    if loss_col not in df.columns:
        raise ValueError(f"loss_col not found: {loss_col}")

    if args.require_highloss and "highloss_q" not in df.columns:
        raise ValueError("require-highloss set but highloss_q is missing. Re-run make_loss_labels.py first.")

    rows = []
    for c in cols:
        if c not in df.columns:
            print(f"[WARN] missing rank col: {c} (skip)")
            continue
        for k in ks:
            rows.append(eval_one(df, loss_col, c, k))

    out = pd.DataFrame(rows)
    out = out.sort_values(["k", "mean_capture_rate"], ascending=[True, False])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote: {args.out}")
    print(out[["rank_col","k","n_days","mean_capture_rate","mean_precision_at_k","base_pos_rate","lift_vs_base"]].to_string(index=False))


if __name__ == "__main__":
    main()
