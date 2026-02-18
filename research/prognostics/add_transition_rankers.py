#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_transition_rankers.py
- panel별 rolling baseline(과거 30일 median/MAD) 대비 변화량 기반 transition 점수 생성
- NO-LEAKAGE: shift(1) 후 rolling (현재일 정보는 baseline에 포함되지 않음)
- 추가:
  - cp_pulse: cp_alarm이 0->1로 변하는 첫날만 1 (지속 True의 chronic 방지용)
  - risk_cp_pulse: risk_max4 + alpha * cp_pulse (클리핑 안 함, 랭킹용)
"""

import argparse
import numpy as np
import pandas as pd

def to_bool(s):
    return s.astype(str).str.lower().isin(["1","true","t","yes"])

def parse():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--window", type=int, default=30)
    ap.add_argument("--min-history", type=int, default=10)
    ap.add_argument("--cp-alpha", type=float, default=0.5)
    ap.add_argument("--cp-pulse-boost", type=float, default=5.0)
    return ap.parse_args()

def roll_med_mad(arr, window, min_hist):
    s = pd.Series(arr, dtype="float64").shift(1)
    med = s.rolling(window, min_periods=min_hist).median()

    def mad_func(x):
        m = np.nanmedian(x)
        return np.nanmedian(np.abs(x - m))

    mad = s.rolling(window, min_periods=min_hist).apply(mad_func, raw=True)
    return med.to_numpy(), mad.to_numpy()

def main():
    a = parse()
    df = pd.read_csv(a.inp, low_memory=False, encoding="utf-8-sig")
    df.columns = [c.replace("\ufeff","") for c in df.columns]

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["panel_id"] = df["panel_id"].astype(str)
    df = df.dropna(subset=["date","panel_id"])
    df = df.sort_values(["panel_id","date"]).reset_index(drop=True)

    # numeric columns
    def num(col):
        return pd.to_numeric(df[col], errors="coerce") if col in df.columns else pd.Series(np.nan, index=df.index)

    mid_ratio = num("mid_ratio")
    risk_day  = num("risk_day")
    ae_rank   = num("ae_rank")
    dtw_rank  = num("dtw_rank")
    level_drop = num("level_drop")  # 있으면 그대로, 없으면 아래에서 계산
    if level_drop.isna().all():
        # 기본 정의: 1 - mid_ratio (mid_ratio가 0~1 근처라는 가정)
        level_drop = 1.0 - mid_ratio

    cp_score = num("cp_score")
    cp_alarm_int = to_bool(df["cp_alarm"]) if "cp_alarm" in df.columns else pd.Series(False, index=df.index)
    cp_alarm_int = cp_alarm_int.astype(int)
    df["cp_alarm_int"] = cp_alarm_int

    # cp_pulse: 0->1 되는 첫날만
    prev = df.groupby("panel_id")["cp_alarm_int"].shift(1).fillna(0).astype(int)
    df["cp_pulse"] = ((df["cp_alarm_int"] == 1) & (prev == 0)).astype(int)

    # shape rank (strongest of AE/DTW)
    shape_rank = np.nanmax(np.vstack([ae_rank.to_numpy(), dtw_rank.to_numpy()]), axis=0)
    df["shape_rank"] = shape_rank

    # risk_max4 (no clip) : ranking-friendly
    risk_max4 = np.nanmax(np.vstack([
        risk_day.to_numpy(),
        level_drop.to_numpy(),
        ae_rank.to_numpy(),
        dtw_rank.to_numpy(),
    ]), axis=0)
    df["risk_max4"] = risk_max4

    # pulse-based cp booster (no chronic carry)
    df["risk_cp_pulse"] = df["risk_max4"] + float(a.cp_alpha) * df["cp_pulse"]

    # cp_score day-percentile (optional interpretability)
    df["cp_rank_day"] = df.groupby("date")["cp_score"].rank(pct=True)

    # rolling baseline per panel (median/MAD, no-leakage)
    n = len(df)
    med_mid = np.full(n, np.nan); mad_mid = np.full(n, np.nan)
    med_shape = np.full(n, np.nan); mad_shape = np.full(n, np.nan)

    for pid, g in df.groupby("panel_id", sort=False):
        idx = g.index.to_numpy()
        m, s = roll_med_mad(mid_ratio.iloc[idx].to_numpy(), a.window, a.min_history)
        med_mid[idx] = m; mad_mid[idx] = s

        m, s = roll_med_mad(df["shape_rank"].iloc[idx].to_numpy(), a.window, a.min_history)
        med_shape[idx] = m; mad_shape[idx] = s

    eps = 1e-6
    # 변화량 (positive only)
    delta_mid = (med_mid - mid_ratio.to_numpy())  # mid_ratio drop
    z_mid = np.maximum(0.0, delta_mid / (mad_mid + eps))

    delta_shape = (df["shape_rank"].to_numpy() - med_shape)  # shape rise
    z_shape = np.maximum(0.0, delta_shape / (mad_shape + eps))

    df["z_mid_drop"] = z_mid
    df["z_shape_rise"] = z_shape

    # transition raw: change only
    df["transition_raw"] = np.fmax(z_mid, z_shape)

    # transition + cp_pulse boost (transition EWS의 핵심)
    df["transition_cp"] = np.fmax(df["transition_raw"].to_numpy(), float(a.cp_pulse_boost) * df["cp_pulse"].to_numpy())

    # day-percentile ranks (0~1), for easy comparison/report
    df["transition_rank_day"] = df.groupby("date")["transition_raw"].rank(pct=True)
    df["transition_cp_rank_day"] = df.groupby("date")["transition_cp"].rank(pct=True)

    df.to_csv(a.out, index=False, encoding="utf-8-sig")
    print("[OK] wrote", a.out)

if __name__ == "__main__":
    main()
