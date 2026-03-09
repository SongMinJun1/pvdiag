#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_scores_pipeline.py

Reproducible post-processing orchestrator:
  1) risk_score.py
  2) add_transition_scores.py
  3) add_ensemble_scores.py

Single source input:
  - data/<site>/out/panel_day_core.csv (via --site)
  - or explicit --scores-path + --out-dir
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd


RISK_REQUIRED_COLS = ["risk_day", "risk_7d_mean", "cp_score", "cp_alarm"]
TRANS_REQUIRED_COLS = [
    "transition_raw",
    "transition_cp",
    "transition_rank_day",
    "transition_cp_rank_day",
]
ENS_REQUIRED_COLS = ["risk_ens", "risk_cp", "shape_rank", "risk_max4"]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Run risk -> transition -> ensemble post-processing with fixed output names."
    )

    ap.add_argument("--site", default=None, help="Site key (uses data/<site>/out/panel_day_core.csv)")
    ap.add_argument("--scores-path", default=None, help="Explicit panel_day_core.csv path")
    ap.add_argument("--out-dir", default=None, help="Output directory (required with --scores-path)")

    # risk_score.py options
    ap.add_argument("--risk-weights-json", default=None)
    ap.add_argument(
        "--risk-cp-input",
        default="risk_7d_mean",
        choices=["risk_day", "risk_7d_mean", "risk_7d_max"],
    )
    ap.add_argument("--risk-cp-baseline-n", type=int, default=14)
    ap.add_argument("--risk-cp-k", type=float, default=0.5)
    ap.add_argument("--risk-cp-h", type=float, default=5.0)

    # add_transition_scores.py options
    ap.add_argument("--trans-window", type=int, default=30)
    ap.add_argument("--trans-min-history", type=int, default=10)
    ap.add_argument("--trans-cp-alpha", type=float, default=0.5)
    ap.add_argument("--trans-cp-pulse-boost", type=float, default=5.0)

    # add_ensemble_scores.py options
    ap.add_argument("--ens-cp-alpha", type=float, default=0.20)
    ap.add_argument(
        "--ens-cp-grid",
        default="",
        help='Optional comma-separated cp-alpha grid (e.g., "0.0,0.1,0.2"). Default OFF.',
    )

    args = ap.parse_args()

    use_site = args.site is not None
    use_path = args.scores_path is not None
    if use_site == use_path:
        ap.error("Use exactly one input mode: --site OR --scores-path.")
    if use_path and args.out_dir is None:
        ap.error("--out-dir is required when using --scores-path.")
    if use_site and args.out_dir is not None:
        ap.error("--out-dir must not be set with --site mode (auto path mode).")

    return args


def _resolve_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    if args.site is not None:
        out_dir = (Path("data") / str(args.site).strip() / "out").resolve()
        scores_path = (out_dir / "panel_day_core.csv").resolve()
        return scores_path, out_dir

    scores_path = Path(args.scores_path).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    return scores_path, out_dir


def _check_file_nonempty(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Expected output file not found: {path}")
    if path.stat().st_size <= 0:
        raise RuntimeError(f"Output file is empty: {path}")


def _check_header(path: Path, required_cols: list[str]) -> None:
    header = pd.read_csv(path, nrows=0, encoding="utf-8-sig")
    missing = [c for c in required_cols if c not in header.columns]
    if missing:
        raise RuntimeError(f"Missing required columns in {path.name}: {missing}")


def _run_step(cmd: list[str], out_path: Path, required_cols: list[str]) -> None:
    print("[RUN]", " ".join(cmd))
    subprocess.run(cmd, check=True)
    _check_file_nonempty(out_path)
    _check_header(out_path, required_cols)
    print(f"[OK] wrote and validated: {out_path}")


def _parse_alpha_grid(grid_s: str) -> list[str]:
    if not grid_s:
        return []
    vals = []
    for tok in grid_s.split(","):
        t = tok.strip()
        if not t:
            continue
        float(t)  # validate
        vals.append(t)
    return vals


def _alpha_tag(alpha_s: str) -> str:
    return alpha_s.replace(".", "p")


def main() -> None:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent

    scores_path, out_dir = _resolve_paths(args)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not scores_path.is_file():
        raise FileNotFoundError(f"Input scores file not found: {scores_path}")

    risk_out = out_dir / "panel_day_risk.csv"
    trans_out = out_dir / "panel_day_risk_transition.csv"
    ens_out = out_dir / "panel_day_risk_ensemble.csv"

    print(f"[INFO] input scores: {scores_path}")
    print(f"[INFO] output dir: {out_dir}")

    risk_cmd = [
        sys.executable,
        str(script_dir / "risk_score.py"),
        "--in",
        str(scores_path),
        "--out",
        str(risk_out),
        "--cp-input",
        str(args.risk_cp_input),
        "--cp-baseline-n",
        str(int(args.risk_cp_baseline_n)),
        "--cp-k",
        str(float(args.risk_cp_k)),
        "--cp-h",
        str(float(args.risk_cp_h)),
    ]
    if args.risk_weights_json:
        risk_cmd += ["--weights-json", str(args.risk_weights_json)]
    _run_step(risk_cmd, risk_out, RISK_REQUIRED_COLS)

    trans_cmd = [
        sys.executable,
        str(script_dir / "add_transition_scores.py"),
        "--in",
        str(risk_out),
        "--out",
        str(trans_out),
        "--window",
        str(int(args.trans_window)),
        "--min-history",
        str(int(args.trans_min_history)),
        "--cp-alpha",
        str(float(args.trans_cp_alpha)),
        "--cp-pulse-boost",
        str(float(args.trans_cp_pulse_boost)),
    ]
    _run_step(trans_cmd, trans_out, TRANS_REQUIRED_COLS)

    ens_cmd = [
        sys.executable,
        str(script_dir / "add_ensemble_scores.py"),
        "--in",
        str(trans_out),
        "--out",
        str(ens_out),
        "--cp-alpha",
        str(float(args.ens_cp_alpha)),
    ]
    _run_step(ens_cmd, ens_out, ENS_REQUIRED_COLS)

    for alpha_s in _parse_alpha_grid(args.ens_cp_grid):
        ens_grid_out = out_dir / f"panel_day_risk_ensemble_a{_alpha_tag(alpha_s)}.csv"
        ens_grid_cmd = [
            sys.executable,
            str(script_dir / "add_ensemble_scores.py"),
            "--in",
            str(trans_out),
            "--out",
            str(ens_grid_out),
            "--cp-alpha",
            alpha_s,
        ]
        _run_step(ens_grid_cmd, ens_grid_out, ENS_REQUIRED_COLS)

    print("[DONE] pipeline complete")
    print(f"[OUT] risk: {risk_out}")
    print(f"[OUT] transition: {trans_out}")
    print(f"[OUT] ensemble: {ens_out}")


if __name__ == "__main__":
    main()
