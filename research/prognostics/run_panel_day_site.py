#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_panel_day_site.py
- pv_ae/panel_day_engine.py 를 site 기반으로 실행해서 panel_day_core.csv를 만들기 위한 래퍼
- 핵심: --help를 파싱해 "실제로 존재하는 옵션만" 넘겨서 호환 이슈를 줄임
"""

from __future__ import annotations
import argparse
import re
import subprocess
import sys
from pathlib import Path
import pandas as pd


DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def get_help_opts() -> set[str]:
    try:
        out = subprocess.check_output(
            [sys.executable, "pv_ae/panel_day_engine.py", "--help"],
            stderr=subprocess.STDOUT,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print("[ERROR] failed to run --help. Output:")
        print(e.output)
        raise
    # extract tokens like --train_start, --train-start, ...
    return set(re.findall(r"(--[A-Za-z0-9][A-Za-z0-9_-]*)", out))


def pick_flag(opts: set[str], candidates: list[str]) -> str | None:
    for c in candidates:
        if c in opts:
            return c
    return None


def scan_dates(site: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    base = Path("data") / site
    csvs = [p for p in base.rglob("*.csv") if "/out/" not in str(p)]
    dates = []
    for p in csvs:
        m = DATE_RE.search(p.name)
        if m:
            d = pd.to_datetime(m.group(1), errors="coerce")
            if pd.notna(d):
                dates.append(d.normalize())
    if not dates:
        raise SystemExit(
            f"[FATAL] No YYYY-MM-DD found in filenames under data/{site}. "
            "Rename files to include date or change date parsing logic."
        )
    return min(dates), max(dates)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--train-days", type=int, default=60)
    args = ap.parse_args()

    site = args.site
    train_days = int(args.train_days)

    min_d, max_d = scan_dates(site)
    span_days = (max_d - min_d).days

    # choose train_end conservatively: min(train_days-1, max(14, 30% of span))
    proposed = min(train_days - 1, max(14, int(span_days * 0.30)))
    if proposed < 1:
        proposed = 1

    train_start = min_d
    train_end = min_d + pd.Timedelta(days=proposed)

    if train_end >= max_d:
        train_end = max_d - pd.Timedelta(days=1)

    eval_start = train_end + pd.Timedelta(days=1)
    eval_end = max_d

    print(f"[INFO] site={site}")
    print(f"[INFO] date_range: {min_d.date()} .. {max_d.date()}")
    print(f"[INFO] train: {train_start.date()} .. {train_end.date()}")
    print(f"[INFO] eval : {eval_start.date()} .. {eval_end.date()}")

    opts = get_help_opts()

    cmd = [sys.executable, "pv_ae/panel_day_engine.py"]

    # site/data root/dir
    f_site = pick_flag(opts, ["--site"])
    if f_site:
        cmd += [f_site, site]

    f_data_root = pick_flag(opts, ["--data_root", "--data-root"])
    if f_data_root:
        cmd += [f_data_root, "data"]

    f_input_dir = pick_flag(opts, ["--input_dir", "--input-dir", "--data_dir", "--data-dir", "--site_dir", "--site-dir"])
    if f_input_dir:
        cmd += [f_input_dir, str(Path("data") / site)]

    f_out_dir = pick_flag(opts, ["--out_dir", "--out-dir"])
    if f_out_dir:
        cmd += [f_out_dir, str(Path("data") / site / "out")]

    # date args
    f_train_s = pick_flag(opts, ["--train_start", "--train-start"])
    f_train_e = pick_flag(opts, ["--train_end", "--train-end"])
    f_eval_s  = pick_flag(opts, ["--eval_start", "--eval-start"])
    f_eval_e  = pick_flag(opts, ["--eval_end", "--eval-end"])

    if f_train_s: cmd += [f_train_s, str(train_start.date())]
    if f_train_e: cmd += [f_train_e, str(train_end.date())]
    if f_eval_s:  cmd += [f_eval_s,  str(eval_start.date())]
    if f_eval_e:  cmd += [f_eval_e,  str(eval_end.date())]

    print("\n[RUN] " + " ".join(cmd) + "\n")
    p = subprocess.run(cmd)
    if p.returncode != 0:
        raise SystemExit(p.returncode)

    # expected output
    out_scores = Path("data") / site / "out" / "panel_day_core.csv"
    if out_scores.exists():
        print(f"[OK] panel_day_core created: {out_scores}")
    else:
        print(f"[WARN] run finished but {out_scores} not found. Check script output for actual out path.")


if __name__ == "__main__":
    main()
