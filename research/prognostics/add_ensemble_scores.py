#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import numpy as np
import pandas as pd

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cp-alpha", type=float, default=0.20)
    return ap.parse_args()

def to_bool(s):
    return s.astype(str).str.lower().isin(["1","true","t","yes"])

def main():
    args = parse_args()
    df = pd.read_csv(args.inp, low_memory=False, encoding="utf-8-sig")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["panel_id"] = df["panel_id"].astype(str)

    def num(col):
        return pd.to_numeric(df.get(col, np.nan), errors="coerce")

    risk_day = num("risk_day")
    level_drop = num("level_drop")
    ae_rank = num("ae_rank")
    dtw_rank = num("dtw_rank")

    cp_alarm_int = to_bool(df.get("cp_alarm", False)).astype(int)
    cp_score = num("cp_score")

    shape_rank = np.nanmax(np.vstack([ae_rank.to_numpy(), dtw_rank.to_numpy()]), axis=0)
    df["shape_rank"] = shape_rank

    risk_max = np.nanmax(np.vstack([risk_day.to_numpy(), level_drop.to_numpy(), ae_rank.to_numpy(), dtw_rank.to_numpy()]), axis=0)
    df["risk_max4"] = risk_max

    df["risk_ens"] = np.clip(0.5*level_drop + 0.5*shape_rank, 0, 1)

    df["risk_cp"] = np.clip(df["risk_max4"] + float(args.cp_alpha)*cp_alarm_int, 0, 1)

    if ("v_drop" in df.columns) and ("risk_7d_mean" in df.columns):
        v_drop = pd.to_numeric(df["v_drop"], errors="coerce")
        risk_7d_mean = pd.to_numeric(df["risk_7d_mean"], errors="coerce")

        df["risk_vdrop_or_7d"] = pd.concat(
            [v_drop, risk_7d_mean], axis=1
        ).max(axis=1, skipna=True)
        df["risk_vdrop_or_7d"] = df["risk_vdrop_or_7d"].clip(0, 1)

        df["risk_vdrop_plus_7d"] = (0.5 * v_drop) + (0.5 * risk_7d_mean)
        df["risk_vdrop_plus_7d"] = df["risk_vdrop_plus_7d"].clip(0, 1)

    df["cp_pctl_panel"] = df.groupby("panel_id")["cp_score"].rank(pct=True)
    df["cp_rank_day"]   = df.groupby("date")["cp_score"].rank(pct=True)

    df.to_csv(args.out, index=False, encoding="utf-8-sig")
    print("[OK] wrote", args.out)

if __name__ == "__main__":
    main()
