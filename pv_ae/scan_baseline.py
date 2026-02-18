import argparse
import pathlib
from typing import List, Dict, Any

import numpy as np
import pandas as pd

from pv_autoencoder_dayAE import compute_event_features


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--pattern", default="202*-*.csv")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    return ap.parse_args()


def in_range(p: pathlib.Path, s: str, e: str) -> bool:
    name = p.name
    if len(name) < 10:
        return False
    d = name[:10]
    return (d >= s) and (d <= e)


def main():
    args = parse_args()
    data_dir = pathlib.Path(args.dir).expanduser()

    files: List[pathlib.Path] = sorted(
        p for p in data_dir.glob(args.pattern)
        if p.is_file() and in_range(p, args.start, args.end)
    )

    if not files:
        print("[ERR] no files matched for range/pattern")
        return

    rows: List[Dict[str, Any]] = []

    for p in files:
        try:
            ev_map = compute_event_features(p)
        except Exception as e:
            print(f"[WARN] failed to compute features for {p.name}: {e}")
            continue

        if not ev_map:
            continue

        df = pd.DataFrame.from_dict(ev_map, orient="index")
        df = df.replace([np.inf, -np.inf], np.nan)

        n_panels = len(df)
        if n_panels == 0:
            continue

        mid_ratio_mean = float(df["mid_ratio"].mean())
        mid_ratio_std = float(df["mid_ratio"].std())
        coverage_mean = float(df["coverage"].mean())

        ok_mask = (
            df["coverage"] >= 0.7
        ) & (df["mid_ratio"] >= 0.9) & (df["mid_ratio"] <= 1.1)

        dead_mask = (
            df["coverage"] >= 0.7
        ) & (df["mid_peer"] >= 0.5) & (df["mid_ratio"] <= 0.3)

        shadow_mask = (
            df["coverage"] >= 0.7
        ) & (df["sustain_mins"] >= 15) & (df["recovered"].astype(bool))

        ok_frac = float(ok_mask.sum() / n_panels)
        dead_frac = float(dead_mask.sum() / n_panels)
        shadow_frac = float(shadow_mask.sum() / n_panels)

        baseline_score = ok_frac - 2.0 * dead_frac - 1.0 * shadow_frac

        rows.append(
            {
                "date": p.name[:10],
                "n_panels": n_panels,
                "mid_ratio_mean": mid_ratio_mean,
                "mid_ratio_std": mid_ratio_std,
                "coverage_mean": coverage_mean,
                "ok_frac": ok_frac,
                "dead_frac": dead_frac,
                "shadow_frac": shadow_frac,
                "baseline_score": baseline_score,
            }
        )

    if not rows:
        print("[ERR] no daily stats computed")
        return

    out = pd.DataFrame(rows)
    out["date"] = pd.to_datetime(out["date"])
    out = out.sort_values("date")

    out_path = data_dir / "baseline_scan_daily.csv"
    out.to_csv(out_path, index=False, encoding="utf-8-sig")

    print("[OK] wrote", out_path)
    print(out.tail(10))


if __name__ == "__main__":
    main()