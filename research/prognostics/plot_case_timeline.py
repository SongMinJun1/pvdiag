#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, help="site key, e.g. conalog")
    ap.add_argument("--panel", required=True, help="panel_id")
    ap.add_argument("--onset", required=True, help="manual onset date (YYYY-MM-DD)")
    ap.add_argument("--window", type=int, default=30, help="days before/after onset")
    ap.add_argument("--out", default=None, help="optional output png path")
    return ap.parse_args()


def to_bool(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().isin(["1", "true", "t", "yes"])


def load_data(site: str) -> tuple[pd.DataFrame, Path]:
    out_dir = (Path("data") / str(site).strip() / "out").resolve()
    ae_path = out_dir / "panel_day_core.csv"
    if not ae_path.is_file():
        raise FileNotFoundError(f"missing: {ae_path}")

    df = pd.read_csv(ae_path, low_memory=False, encoding="utf-8-sig")
    df["date"] = pd.to_datetime(df.get("date"), errors="coerce").dt.normalize()
    df["panel_id"] = df.get("panel_id").astype(str)
    df = df.dropna(subset=["date", "panel_id"]).copy()

    risk_path = out_dir / "panel_day_risk_ensemble.csv"
    if risk_path.is_file():
        rk = pd.read_csv(risk_path, low_memory=False, encoding="utf-8-sig")
        rk["date"] = pd.to_datetime(rk.get("date"), errors="coerce").dt.normalize()
        rk["panel_id"] = rk.get("panel_id").astype(str)
        rk = rk.dropna(subset=["date", "panel_id"]).copy()
        keep = [c for c in ["date", "panel_id", "risk_day", "risk_ens"] if c in rk.columns]
        if keep:
            df = df.merge(rk[keep], on=["date", "panel_id"], how="left", suffixes=("", "_risk"))

    return df.sort_values(["panel_id", "date"]).reset_index(drop=True), out_dir


def first_true_date(g: pd.DataFrame, col: str) -> pd.Timestamp | pd.NaT:
    if col not in g.columns:
        return pd.NaT
    m = to_bool(g[col])
    hit = g.loc[m, "date"]
    if hit.empty:
        return pd.NaT
    return pd.to_datetime(hit.min(), errors="coerce").normalize()


def first_nonnull_date(g: pd.DataFrame, col: str) -> pd.Timestamp | pd.NaT:
    if col not in g.columns:
        return pd.NaT
    s = pd.to_datetime(g[col], errors="coerce").dropna()
    if s.empty:
        return pd.NaT
    return pd.to_datetime(s.min(), errors="coerce").normalize()


def add_vline_all(axes, d: pd.Timestamp | pd.NaT, label: str, color: str, ls: str = "--") -> None:
    if pd.isna(d):
        return
    for i, ax in enumerate(axes):
        ax.axvline(d, color=color, linestyle=ls, linewidth=1.2, label=(label if i == 0 else None))


def main() -> None:
    args = parse_args()
    onset = pd.to_datetime(args.onset, errors="coerce").normalize()
    if pd.isna(onset):
        raise ValueError(f"invalid --onset: {args.onset}")

    df, out_dir = load_data(args.site)
    g = df[df["panel_id"].astype(str) == str(args.panel)].copy().sort_values("date")
    if g.empty:
        raise ValueError(f"panel not found in panel_day_core.csv: {args.panel}")

    dead_start_date = first_true_date(g, "state_dead_eff")

    # Prefer explicit dead_diag_on_day; fallback to diagnosis_date_online first non-null.
    if "dead_diag_on_day" in g.columns:
        diagnosis_date_online = first_true_date(g, "dead_diag_on_day")
    else:
        diagnosis_date_online = pd.NaT
    diag_col_date = first_nonnull_date(g, "diagnosis_date_online")
    if pd.isna(diagnosis_date_online):
        diagnosis_date_online = diag_col_date

    left = onset - pd.Timedelta(days=int(args.window))
    right = onset + pd.Timedelta(days=int(args.window))
    w = g[(g["date"] >= left) & (g["date"] <= right)].copy().sort_values("date")
    if w.empty:
        raise ValueError("no rows in onset±window range for this panel")

    # Numeric conversions for plotting.
    for c in ["mid_ratio", "v_drop", "recon_error", "dtw_dist", "hs_score", "risk_day", "risk_ens"]:
        if c not in w.columns:
            w[c] = np.nan
        else:
            w[c] = pd.to_numeric(w[c], errors="coerce")
    if "state_dead_eff" in w.columns:
        w["state_dead_eff_int"] = to_bool(w["state_dead_eff"]).astype(int)
    else:
        w["state_dead_eff_int"] = 0
    if "dead_diag_on_day" in w.columns:
        w["dead_diag_on_day_int"] = to_bool(w["dead_diag_on_day"]).astype(int)
    else:
        w["dead_diag_on_day_int"] = 0

    fig, axes = plt.subplots(3, 1, figsize=(13, 9), sharex=True)

    # (A) mid_ratio
    axes[0].plot(w["date"], w["mid_ratio"], color="#1f77b4", linewidth=1.5, label="mid_ratio")
    axes[0].set_ylabel("mid_ratio")
    axes[0].grid(alpha=0.25)
    axes[0].legend(loc="upper right")

    # (B) v_drop
    axes[1].plot(w["date"], w["v_drop"], color="#d62728", linewidth=1.5, label="v_drop")
    axes[1].set_ylabel("v_drop")
    axes[1].grid(alpha=0.25)
    axes[1].legend(loc="upper right")

    # (C) state_dead_eff / dead_diag_on_day + optional risk_ens
    axes[2].step(w["date"], w["state_dead_eff_int"], where="post", color="#2ca02c", linewidth=1.6, label="state_dead_eff")
    axes[2].step(w["date"], w["dead_diag_on_day_int"], where="post", color="#9467bd", linewidth=1.4, label="dead_diag_on_day")
    if "risk_ens" in w.columns and np.isfinite(w["risk_ens"]).any():
        axes[2].plot(w["date"], w["risk_ens"], color="#ff7f0e", linewidth=1.0, alpha=0.8, label="risk_ens")
    axes[2].set_ylabel("state/diag (0/1)")
    axes[2].set_ylim(-0.05, 1.05)
    axes[2].grid(alpha=0.25)
    axes[2].legend(loc="upper right")

    # Vertical markers
    add_vline_all(axes, onset, "onset_manual", "#111111", ls="--")
    add_vline_all(axes, dead_start_date, "dead_start_date", "#2ca02c", ls="-.")
    add_vline_all(axes, diagnosis_date_online, "diagnosis_date_online", "#9467bd", ls=":")
    if pd.notna(diag_col_date) and pd.notna(diagnosis_date_online) and diag_col_date != diagnosis_date_online:
        add_vline_all(axes, diag_col_date, "diagnosis_date_online(col)", "#8c564b", ls=":")

    axes[0].set_title(f"Case Timeline | panel={args.panel} | onset={onset.date()} | window=±{int(args.window)}d")
    axes[2].set_xlabel("date")

    fig.autofmt_xdate()
    fig.tight_layout()

    if args.out:
        out_path = Path(args.out).expanduser().resolve()
    else:
        out_path = (out_dir / f"FIG_case_{args.panel}.png").resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    size_bytes = out_path.stat().st_size if out_path.is_file() else -1
    print(f"{out_path}\t{size_bytes}")


if __name__ == "__main__":
    main()
