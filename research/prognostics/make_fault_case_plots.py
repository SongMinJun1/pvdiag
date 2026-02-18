#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_fault_case_plots.py
- fault_events_auto.csv 기반으로 각 fault panel의 타임라인 CSV + PNG 생성
"""

from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

def _to_dt_norm(s):
    return pd.to_datetime(s, errors="coerce").dt.normalize()

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", required=True, help="scores_with_risk_loss14d.csv (or scores_with_risk.csv)")
    ap.add_argument("--events", required=True, help="fault_events_auto.csv")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--pre", type=int, default=120)
    ap.add_argument("--post", type=int, default=30)
    return ap.parse_args()

def main():
    args = parse_args()
    df = pd.read_csv(args.scores, encoding="utf-8-sig", low_memory=False)
    ev = pd.read_csv(args.events, encoding="utf-8-sig", low_memory=False)

    df["date"] = _to_dt_norm(df["date"])
    df["panel_id"] = df["panel_id"].astype(str)
    ev["panel_id"] = ev["panel_id"].astype(str)
    ev["onset_date"] = _to_dt_norm(ev["onset_date"])

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    import matplotlib.pyplot as plt

    for _, r in ev.iterrows():
        pid = r["panel_id"]
        onset = r["onset_date"]
        if pd.isna(onset):
            continue

        g = df[df["panel_id"] == pid].sort_values("date")
        w = g[(g["date"] >= onset - pd.Timedelta(days=int(args.pre))) &
              (g["date"] <= onset + pd.Timedelta(days=int(args.post)))].copy()

        csv_path = out_dir / f"case_{pid}.csv"
        w.to_csv(csv_path, index=False, encoding="utf-8-sig")

        # Plot: mid_ratio + risk_day + cp_score
        fig = plt.figure(figsize=(12, 5))
        ax = plt.gca()

        if "mid_ratio" in w.columns:
            ax.plot(w["date"], pd.to_numeric(w["mid_ratio"], errors="coerce"), label="mid_ratio")
        if "risk_day" in w.columns:
            ax.plot(w["date"], pd.to_numeric(w["risk_day"], errors="coerce"), label="risk_day")
        ax.axvline(onset, linestyle="--", label="onset")

        ax.set_title(f"{pid} | onset={onset.date()}")
        ax.set_xlabel("date")
        ax.set_ylabel("mid_ratio / risk_day")
        ax.legend(loc="upper left")

        if "cp_score" in w.columns:
            ax2 = ax.twinx()
            ax2.plot(w["date"], pd.to_numeric(w["cp_score"], errors="coerce"), label="cp_score")
            ax2.set_ylabel("cp_score")
            ax2.legend(loc="upper right")

        png_path = out_dir / f"case_{pid}.png"
        plt.tight_layout()
        plt.savefig(png_path, dpi=160)
        plt.close(fig)

        print("[OK] wrote", csv_path)
        print("[OK] wrote", png_path)

if __name__ == "__main__":
    main()
