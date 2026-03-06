#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
risk_score.py
- Input: panel_day_core.csv (panel×day)
- Output: adds risk_day + rolling risk + change-point score(cp_score)
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class RiskWeights:
    level_drop: float = 0.35
    ae_rank: float = 0.15
    dtw_rank: float = 0.15
    hs_rank: float = 0.05
    sustain_rank: float = 0.10
    low_area_rank: float = 0.10
    vdrop_comp: float = 0.10

    @staticmethod
    def from_json(s: str) -> "RiskWeights":
        d = json.loads(s)
        rw = RiskWeights()
        for k, v in d.items():
            if hasattr(rw, k):
                setattr(rw, k, float(v))
        return rw

    def as_dict(self) -> Dict[str, float]:
        return {
            "level_drop": float(self.level_drop),
            "ae_rank": float(self.ae_rank),
            "dtw_rank": float(self.dtw_rank),
            "hs_rank": float(self.hs_rank),
            "sustain_rank": float(self.sustain_rank),
            "low_area_rank": float(self.low_area_rank),
            "vdrop_comp": float(self.vdrop_comp),
        }


def _to_dt_norm(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce").dt.normalize()


def _pct_rank(s: pd.Series, ascending: bool = True) -> pd.Series:
    """Percentile rank in [0,1]. Returns NaN when too few finite values."""
    x = pd.to_numeric(s, errors="coerce")
    if x.notna().sum() < 2:
        return pd.Series(np.nan, index=s.index)
    return x.rank(pct=True, ascending=ascending)


def _clip01(x: pd.Series) -> pd.Series:
    x = pd.to_numeric(x, errors="coerce")
    return x.clip(lower=0.0, upper=1.0)


def compute_risk_components(df: pd.DataFrame) -> pd.DataFrame:
    """Create component columns used for risk."""
    out = df.copy()

    # Guard: required cols
    if "date" not in out.columns or "panel_id" not in out.columns:
        raise ValueError("Input must contain 'date' and 'panel_id' columns.")

    out["date"] = _to_dt_norm(out["date"])
    out["panel_id"] = out["panel_id"].astype(str)

    # Level drop: 1 - mid_ratio (bounded to [0,1])
    if "mid_ratio" in out.columns:
        out["level_drop"] = _clip01(1.0 - pd.to_numeric(out["mid_ratio"], errors="coerce"))
    else:
        out["level_drop"] = np.nan

    # Within-day ranks (higher = worse risk)
    if "recon_error" in out.columns:
        out["ae_rank"] = out.groupby("date")["recon_error"].transform(lambda s: _pct_rank(s, ascending=True))
    else:
        out["ae_rank"] = np.nan

    if "dtw_dist" in out.columns:
        out["dtw_rank"] = out.groupby("date")["dtw_dist"].transform(lambda s: _pct_rank(s, ascending=True))
    else:
        out["dtw_rank"] = np.nan

    if "hs_score" in out.columns:
        out["hs_rank"] = out.groupby("date")["hs_score"].transform(lambda s: _pct_rank(s, ascending=True))
    else:
        out["hs_rank"] = np.nan

    # Event intensity proxies
    if "sustain_mins" in out.columns:
        out["sustain_rank"] = out.groupby("date")["sustain_mins"].transform(lambda s: _pct_rank(s, ascending=True))
    else:
        out["sustain_rank"] = np.nan

    if "low_area" in out.columns:
        out["low_area_rank"] = out.groupby("date")["low_area"].transform(lambda s: _pct_rank(s, ascending=True))
    else:
        out["low_area_rank"] = np.nan

    # V-drop component (only when v_ref_ok and v_drop exists)
    if "v_drop" in out.columns:
        vdrop = pd.to_numeric(out["v_drop"], errors="coerce")
        vref_ok = out.get("v_ref_ok", False)
        vref_ok = pd.to_numeric(vref_ok, errors="coerce").fillna(0).astype(int).astype(bool)
        out["vdrop_comp"] = np.where(vref_ok & np.isfinite(vdrop), np.clip(vdrop, 0.0, 1.0), np.nan)
    else:
        out["vdrop_comp"] = np.nan

    return out


def combine_weighted_risk(df: pd.DataFrame, w: RiskWeights) -> pd.DataFrame:
    """risk_day = weighted mean of available components (per-row availability-aware)."""
    out = df.copy()

    comp_w = w.as_dict()
    comps = list(comp_w.keys())

    num = pd.Series(0.0, index=out.index)
    den = pd.Series(0.0, index=out.index)

    for c in comps:
        if c not in out.columns:
            continue
        x = pd.to_numeric(out[c], errors="coerce")
        ww = float(comp_w[c])
        m = x.notna()
        num = num + ww * x.fillna(0.0)
        den = den + ww * m.astype(float)

    out["risk_day"] = np.where(den > 0.0, num / den, np.nan)
    out["risk_day"] = pd.to_numeric(out["risk_day"], errors="coerce").clip(0.0, 1.0)

    # Gate out bad data
    if "data_bad" in out.columns:
        bad = out["data_bad"].astype(bool)
        out.loc[bad, "risk_day"] = np.nan

    return out


def add_rolling(df: pd.DataFrame) -> pd.DataFrame:
    out = df.sort_values(["panel_id", "date"]).copy()

    def _roll_mean(s: pd.Series, w: int, mp: int) -> pd.Series:
        return s.rolling(window=w, min_periods=mp).mean()

    def _roll_max(s: pd.Series, w: int, mp: int) -> pd.Series:
        return s.rolling(window=w, min_periods=mp).max()

    out["risk_7d_mean"] = out.groupby("panel_id")["risk_day"].transform(lambda s: _roll_mean(s, 7, 3))
    out["risk_7d_max"]  = out.groupby("panel_id")["risk_day"].transform(lambda s: _roll_max(s, 7, 3))
    out["risk_30d_mean"] = out.groupby("panel_id")["risk_day"].transform(lambda s: _roll_mean(s, 30, 10))
    out["risk_30d_max"]  = out.groupby("panel_id")["risk_day"].transform(lambda s: _roll_max(s, 30, 10))
    return out


def cusum_cp_scores(
    df: pd.DataFrame,
    input_col: str = "risk_7d_mean",
    baseline_n: int = 14,
    k: float = 0.5,
    h: float = 5.0,
    eps: float = 1e-6,
) -> pd.DataFrame:
    """
    Simple one-sided CUSUM on z-scored input.
    - baseline mean/std from first `baseline_n` finite points per panel
    - cp_score accumulates positive mean shift
    """
    out = df.sort_values(["panel_id", "date"]).copy()
    out["cp_score"] = np.nan
    out["cp_alarm"] = False

    for pid, g in out.groupby("panel_id", sort=False):
        x = pd.to_numeric(g[input_col], errors="coerce").to_numpy(dtype=float)
        idx = g.index.to_numpy()

        finite_idx = np.where(np.isfinite(x))[0]
        if finite_idx.size < baseline_n:
            # Not enough history; keep NaN/False
            continue

        base_pos = finite_idx[:baseline_n]
        mu = float(np.mean(x[base_pos]))
        sd = float(np.std(x[base_pos]))
        sd = max(sd, eps)

        S = 0.0
        scores = np.full_like(x, np.nan, dtype=float)
        alarms = np.zeros_like(x, dtype=bool)

        for t in range(len(x)):
            if not np.isfinite(x[t]):
                scores[t] = S
                alarms[t] = False
                continue
            z = (x[t] - mu) / sd
            S = max(0.0, S + (z - float(k)))
            scores[t] = S
            alarms[t] = bool(S >= float(h))

        out.loc[idx, "cp_score"] = scores
        out.loc[idx, "cp_alarm"] = alarms

    return out


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Input scores CSV (panel_day_core.csv)")
    ap.add_argument("--out", dest="out", required=True, help="Output CSV with risk/cp columns")
    ap.add_argument("--weights-json", default=None,
                    help='Override risk weights JSON, e.g. \'{"level_drop":0.4,"ae_rank":0.1}\'')
    ap.add_argument("--cp-input", default="risk_7d_mean", choices=["risk_day", "risk_7d_mean", "risk_7d_max"],
                    help="Column to feed into change-point detector")
    ap.add_argument("--cp-baseline-n", type=int, default=14)
    ap.add_argument("--cp-k", type=float, default=0.5)
    ap.add_argument("--cp-h", type=float, default=5.0)
    return ap.parse_args()


def main():
    args = parse_args()
    df = pd.read_csv(args.inp, encoding="utf-8-sig")
    df = compute_risk_components(df)

    w = RiskWeights()
    if args.weights_json:
        w = RiskWeights.from_json(args.weights_json)

    df = combine_weighted_risk(df, w)
    df = add_rolling(df)

    # Change-point
    df = cusum_cp_scores(
        df,
        input_col=str(args.cp_input),
        baseline_n=int(args.cp_baseline_n),
        k=float(args.cp_k),
        h=float(args.cp_h),
    )

    df.to_csv(args.out, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote: {args.out}")
    print("[INFO] risk weights:", w.as_dict())


if __name__ == "__main__":
    main()
