#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def make_daily_files(in_csv: Path, out_dir: Path, rule: str = "5min") -> list[Path]:
    df = pd.read_csv(in_csv)
    required = ["date_time", "panel_id", "v_in", "i_out", "irr", "pvt", "fault_label"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"Missing columns in input csv: {missing}")

    df["date_time"] = pd.to_datetime(df["date_time"], errors="coerce")
    df = df.dropna(subset=["date_time"])
    df["panel_id"] = df["panel_id"].astype(str)

    num_cols = ["v_in", "i_out", "irr", "pvt", "fault_label"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    chunks = []
    for panel_id, g in df.groupby("panel_id", sort=True):
        g = g.sort_values("date_time").set_index("date_time")
        r = g[num_cols].resample(rule).mean()
        r["panel_id"] = panel_id
        chunks.append(r.reset_index())

    out = pd.concat(chunks, ignore_index=True)
    out = out.sort_values(["date_time", "panel_id"])
    out = out[["date_time", "panel_id", "v_in", "i_out", "irr", "pvt", "fault_label"]]

    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for d, g in out.groupby(out["date_time"].dt.date, sort=True):
        p = raw_dir / f"{d}.csv"
        g.to_csv(p, index=False)
        written.append(p)
    return written


def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Downsample converted.csv to 5-minute panel series and split to daily raw CSV files."
    )
    ap.add_argument(
        "--in",
        "--in-csv",
        dest="in_csv",
        default="data/pvfault16d/converted.csv",
        help="Input converted csv path",
    )
    ap.add_argument(
        "--out",
        "--out-dir",
        dest="out_dir",
        default="data/pvfault16d",
        help="Output directory (daily files written under <out>/raw)",
    )
    ap.add_argument("--rule", default="5min", help="Pandas resample rule (default: 5min)")
    return ap


def main() -> None:
    args = build_argparser().parse_args()
    in_csv = Path(args.in_csv)
    out_dir = Path(args.out_dir)
    written = make_daily_files(in_csv=in_csv, out_dir=out_dir, rule=args.rule)
    print(f"[OK] input: {in_csv}")
    print(f"[OK] output dir: {out_dir / 'raw'}")
    print(f"[OK] wrote {len(written)} daily files")
    for p in written[:5]:
        print(f" - {p}")
    if len(written) > 5:
        print(" - ...")


if __name__ == "__main__":
    main()
