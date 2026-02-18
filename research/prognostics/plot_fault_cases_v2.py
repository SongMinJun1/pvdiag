#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def parse():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--pre", type=int, default=120)
    ap.add_argument("--post", type=int, default=30)
    return ap.parse_args()

def main():
    a = parse()
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(a.scores, low_memory=False, encoding="utf-8-sig")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["panel_id"] = df["panel_id"].astype(str)
    df = df.dropna(subset=["date","panel_id"]).sort_values(["panel_id","date"])

    ev = pd.read_csv(a.events, encoding="utf-8-sig")
    ev["panel_id"] = ev["panel_id"].astype(str)
    # accept either onset_date or fault_segment_start as fallback
    if "onset_date" in ev.columns:
        ev["onset_date"] = pd.to_datetime(ev["onset_date"], errors="coerce").dt.normalize()
    else:
        ev["onset_date"] = pd.to_datetime(ev.get("fault_segment_start", pd.NaT), errors="coerce").dt.normalize()

    if "diagnosis_date" in ev.columns:
        ev["diagnosis_date"] = pd.to_datetime(ev["diagnosis_date"], errors="coerce").dt.normalize()
    else:
        ev["diagnosis_date"] = pd.NaT

    cols_pref = [
        "level_drop", "risk_day", "ae_rank",
        "transition_rank_day", "transition_cp_rank_day"
    ]

    for _, r in ev.iterrows():
        pid = r["panel_id"]
        onset = r["onset_date"]
        diag  = r["diagnosis_date"]

        if pd.isna(onset):
            continue

        start = onset - pd.Timedelta(days=int(a.pre))
        end   = onset + pd.Timedelta(days=int(a.post))

        g = df[(df["panel_id"]==pid) & (df["date"]>=start) & (df["date"]<=end)].copy()
        if len(g) == 0:
            continue

        # if level_drop missing, derive from mid_ratio if present
        if ("level_drop" not in g.columns) and ("mid_ratio" in g.columns):
            g["level_drop"] = 1.0 - pd.to_numeric(g["mid_ratio"], errors="coerce")

        # save window CSV
        safe_pid = pid.replace("/", "_")
        g.to_csv(out_dir / f"case_{safe_pid}.csv", index=False, encoding="utf-8-sig")

        # plot
        plt.figure(figsize=(12, 4))
        plotted = 0
        for c in cols_pref:
            if c in g.columns:
                y = pd.to_numeric(g[c], errors="coerce")
                if y.notna().any():
                    plt.plot(g["date"], y, label=c)
                    plotted += 1

        if plotted == 0:
            plt.close()
            continue

        plt.axvline(onset, linestyle="--", label="onset")
        if pd.notna(diag):
            plt.axvline(diag, linestyle="-", label="diagnosis")

        title = f"{pid} | onset={onset.date()}"
        if pd.notna(diag):
            title += f" | diagnosis={diag.date()}"

        plt.title(title)
        plt.ylim(-0.05, 1.05)
        plt.legend(loc="best", fontsize=8)
        plt.tight_layout()
        plt.savefig(out_dir / f"case_{safe_pid}.png", dpi=150)
        plt.close()

    print("[OK] wrote case plots to", out_dir)

if __name__ == "__main__":
    main()
