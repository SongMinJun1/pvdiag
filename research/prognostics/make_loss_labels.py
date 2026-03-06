#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_loss_labels.py
- Input: panel_day_risk.csv (panel×day)
- Output: adds future_loss_H (continuous) and highloss_q (binary optional)
"""

from __future__ import annotations
import argparse
import numpy as np
import pandas as pd


def future_sum_strict(loss: np.ndarray, H: int) -> np.ndarray:
    """
    y[t] = sum_{k=1..H} loss[t+k]  (strict: requires all H future days finite)
    """
    n = len(loss)
    y = np.full(n, np.nan, dtype=float)
    loss = np.asarray(loss, dtype=float)

    finite = np.isfinite(loss).astype(int)
    loss0 = np.where(np.isfinite(loss), loss, 0.0)

    pref_loss = np.concatenate([[0.0], np.cumsum(loss0)])
    pref_cnt  = np.concatenate([[0], np.cumsum(finite)])

    for t in range(n):
        a = t + 1
        b = t + H + 1
        if b > n:
            continue
        cnt = int(pref_cnt[b] - pref_cnt[a])
        if cnt == H:
            y[t] = float(pref_loss[b] - pref_loss[a])
    return y


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--horizon", type=int, default=14)
    ap.add_argument("--perf-col", default=None,
                    help="Performance column to use (prefer day_energy_ratio if exists; else mid_ratio).")
    ap.add_argument("--pos-quantile", type=float, default=0.95,
                    help="Quantile threshold for highloss_q label (default 0.95).")
    return ap.parse_args()


def main():
    args = parse_args()
    df = pd.read_csv(args.inp, encoding="utf-8-sig")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["panel_id"] = df["panel_id"].astype(str)
    df = df.sort_values(["panel_id", "date"]).copy()

    # choose perf column
    perf_col = args.perf_col
    if perf_col is None:
        perf_col = "day_energy_ratio" if "day_energy_ratio" in df.columns else "mid_ratio"
    if perf_col not in df.columns:
        raise ValueError(f"perf-col '{perf_col}' not found in input.")

    perf = pd.to_numeric(df[perf_col], errors="coerce")
    perf = perf.clip(lower=0.0, upper=1.2)  # allow slight >1 due to ratio noise
    df["perf_used_col"] = perf_col

    # daily loss proxy
    df["daily_loss"] = np.maximum(0.0, 1.0 - perf)

    # future loss
    H = int(args.horizon)
    fut = np.full(len(df), np.nan, dtype=float)
    for pid, g in df.groupby("panel_id", sort=False):
        idx = g.index.to_numpy()
        loss_arr = pd.to_numeric(g["daily_loss"], errors="coerce").to_numpy(dtype=float)
        fut[idx] = future_sum_strict(loss_arr, H)

    df[f"future_loss_{H}d"] = fut

    # optional binary label (for precision@K etc.)
    q = float(args.pos_quantile)
    valid = np.isfinite(df[f"future_loss_{H}d"].to_numpy())
    if "data_bad" in df.columns:
        valid = valid & (~df["data_bad"].astype(bool).to_numpy())
    thr = float(np.nanquantile(df.loc[valid, f"future_loss_{H}d"], q)) if np.any(valid) else np.nan
    df["highloss_thr"] = thr
    df["highloss_q"] = False
    if np.isfinite(thr):
        df.loc[valid & (df[f"future_loss_{H}d"] >= thr), "highloss_q"] = True

    df.to_csv(args.out, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote: {args.out}")
    print(f"[INFO] perf_col={perf_col} horizon={H} pos_q={q} thr={thr}")


if __name__ == "__main__":
    main()
