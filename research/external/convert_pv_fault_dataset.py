#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _flat_num(x: Any) -> np.ndarray:
    arr = np.asarray(x)
    arr = np.squeeze(arr)
    return pd.to_numeric(pd.Series(arr.reshape(-1)), errors="coerce").to_numpy()


def _find_var(mat: dict[str, Any], names: list[str]) -> Any:
    norm = {k.lower().replace("_", ""): k for k in mat.keys() if not k.startswith("__")}
    for n in names:
        key = norm.get(n.lower().replace("_", ""))
        if key is not None:
            return mat[key]
    raise KeyError(f"Missing variable. candidates={names}, available={list(mat.keys())}")


def _try_datetime(
    mat_elec: dict[str, Any],
    mat_amb: dict[str, Any],
    n: int,
    total_days: int,
) -> tuple[pd.DatetimeIndex, str]:
    candidates = ["date_time", "datetime", "timestamp", "time", "t", "datenum", "date"]

    for src_name, src in [("dataset_elec", mat_elec), ("dataset_amb", mat_amb)]:
        for name in candidates:
            try:
                raw = _find_var(src, [name])
            except KeyError:
                continue
            vals = np.asarray(raw).squeeze().reshape(-1)
            if vals.size == 0:
                continue
            if np.issubdtype(vals.dtype, np.number):
                s = pd.to_numeric(pd.Series(vals), errors="coerce")
                # MATLAB datenum heuristic
                if s.notna().sum() > 0 and float(s.dropna().median()) > 10000:
                    dt = pd.to_datetime(s - 719529, unit="D", errors="coerce")
                else:
                    dt = pd.to_datetime(s, errors="coerce")
            else:
                dt = pd.to_datetime(pd.Series(vals), errors="coerce")
            dt = dt.dropna()
            if len(dt) >= n:
                return pd.DatetimeIndex(dt.iloc[:n]), f"datetime source: {src_name}.{name}"

    # Assumption (explicit): when no timestamp variable exists in .mat
    # infer dt_seconds so that N samples span about `total_days` days.
    start = pd.Timestamp("2000-01-01 00:00:00")
    if n <= 1:
        dt_seconds = 1
    else:
        dt_seconds = int(round((int(total_days) * 86400) / (n - 1)))
    dt_seconds = max(1, dt_seconds)
    idx = pd.date_range(start=start, periods=n, freq=f"{dt_seconds}s")
    assumption = (
        f"timestamp absent -> inferred dt_seconds={dt_seconds} to match ~{int(total_days)} days "
        f"(start={start})"
    )
    return idx, assumption


def convert(args: argparse.Namespace) -> tuple[Path, Path, Path, Path]:
    try:
        from scipy.io import loadmat
    except Exception as e:
        raise RuntimeError("scipy is required. install with: pip install scipy") from e

    in_root = Path(args.in_dir) if args.in_dir else Path("external_data/pv_fault_dataset")
    in_elec = Path(args.in_elec) if args.in_elec else (in_root / "dataset_elec.mat")
    in_amb = Path(args.in_amb) if args.in_amb else (in_root / "dataset_amb.mat")
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    out_csv = Path(args.out_csv) if args.out_csv else (out_root / "converted.csv")
    out_summary = Path(args.out_summary) if args.out_summary else (out_root / "daily_label_summary.csv")
    out_report = Path(args.out_report) if args.out_report else (out_root / "conversion_report.txt")

    mat_elec = loadmat(in_elec)
    mat_amb = loadmat(in_amb)

    vdc1 = _flat_num(_find_var(mat_elec, ["vdc1"]))
    vdc2 = _flat_num(_find_var(mat_elec, ["vdc2"]))
    idc1 = _flat_num(_find_var(mat_elec, ["idc1"]))
    idc2 = _flat_num(_find_var(mat_elec, ["idc2"]))
    irr = _flat_num(_find_var(mat_amb, ["irr"]))
    pvt = _flat_num(_find_var(mat_amb, ["pvt"]))
    f_nv = _flat_num(_find_var(mat_amb, ["f_nv", "fnv"]))

    n = min(len(vdc1), len(vdc2), len(idc1), len(idc2), len(irr), len(pvt), len(f_nv))
    if n <= 0:
        raise RuntimeError("No usable rows found after loading .mat variables.")

    total_days = int(getattr(args, "total_days", 16))
    dt_idx, dt_note = _try_datetime(mat_elec, mat_amb, n, total_days=total_days)
    dt_idx = pd.DatetimeIndex(dt_idx[:n])

    base = pd.DataFrame(
        {
            "date_time": dt_idx,
            "irr": irr[:n],
            "pvt": pvt[:n],
            "fault_label": f_nv[:n],
        }
    )

    s1 = base.copy()
    s1["panel_id"] = "string1"
    s1["v_in"] = vdc1[:n]
    s1["i_out"] = idc1[:n]

    s2 = base.copy()
    s2["panel_id"] = "string2"
    s2["v_in"] = vdc2[:n]
    s2["i_out"] = idc2[:n]

    out_df = pd.concat([s1, s2], ignore_index=True)
    out_df = out_df[["date_time", "panel_id", "v_in", "i_out", "irr", "pvt", "fault_label"]]
    out_df.to_csv(out_csv, index=False)

    tmp = out_df.copy()
    tmp["date"] = pd.to_datetime(tmp["date_time"], errors="coerce").dt.date
    tmp["fault_label"] = pd.to_numeric(tmp["fault_label"], errors="coerce")

    def _mode(s: pd.Series) -> float:
        m = s.mode(dropna=True)
        return float(m.iloc[0]) if len(m) else np.nan

    summary = (
        tmp.groupby(["date", "panel_id"], sort=True)
        .agg(
            pos_ratio=("fault_label", lambda s: float((s.fillna(0) != 0).mean())),
            label_mode=("fault_label", _mode),
        )
        .reset_index()
    )
    summary.to_csv(out_summary, index=False)

    report_lines = [
        "[pv_fault_dataset conversion report]",
        f"in_elec={in_elec}",
        f"in_amb={in_amb}",
        f"rows_per_string={n}",
        f"total_rows={len(out_df)}",
        f"datetime_policy={dt_note}",
        "note: fault_label is copied from f_nv and duplicated to both string rows at same timestamp.",
    ]
    out_report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    out_md_report = out_root / "CONVERT_PVFAULT_REPORT.md"
    out_md_report.write_text(
        "\n".join(
            [
                "# CONVERT PVFAULT REPORT",
                f"- input elec: {in_elec}",
                f"- input amb: {in_amb}",
                f"- rows per string: {n}",
                f"- total rows: {len(out_df)}",
                f"- datetime policy: {dt_note}",
                f'- timestamp absent -> inferred dt_seconds={"N/A" if "timestamp absent" not in dt_note else dt_note.split("dt_seconds=")[1].split()[0]} to match ~{total_days} days',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return out_csv, out_summary, out_report, out_md_report


def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Convert pv_fault_dataset .mat files to pvdiag-style long CSV and daily label summary."
    )
    ap.add_argument(
        "--in",
        dest="in_dir",
        default="external_data/pv_fault_dataset",
        help="Input directory containing dataset_elec.mat and dataset_amb.mat",
    )
    ap.add_argument("--in-elec", default=None, help="Path to dataset_elec.mat (overrides --in)")
    ap.add_argument("--in-amb", default=None, help="Path to dataset_amb.mat (overrides --in)")
    ap.add_argument(
        "--out",
        default="data/pvfault16d",
        help="Output root directory",
    )
    ap.add_argument(
        "--total-days",
        type=int,
        default=16,
        help="Fallback total days when timestamp is absent (default: 16).",
    )
    ap.add_argument("--out-csv", default=None, help="Optional override for converted.csv path")
    ap.add_argument("--out-summary", default=None, help="Optional override for daily_label_summary.csv path")
    ap.add_argument("--out-report", default=None, help="Optional override for conversion_report.txt path")
    return ap


def main() -> None:
    ap = build_argparser()
    args = ap.parse_args()
    out_csv, out_summary, out_report, out_md_report = convert(args)
    print(f"[OK] wrote converted csv: {out_csv}")
    print(f"[OK] wrote daily summary: {out_summary}")
    print(f"[OK] wrote report: {out_report}")
    print(f"[OK] wrote report(md): {out_md_report}")


if __name__ == "__main__":
    main()
