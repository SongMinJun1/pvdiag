#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
weaklabel_eval_2sigma.py

Weak-label evaluation for PV prognostics using 2-sigma onset labels.
- pandas/numpy only
- date-block bootstrap CI
- D=2/D=3 and W=7/14/30 sensitivity table
- walk-forward cutoff table
- one-page markdown summary
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_int_list(s: str) -> list[int]:
    vals: list[int] = []
    for tok in str(s).split(","):
        t = tok.strip()
        if not t:
            continue
        vals.append(int(t))
    return vals


def parse_str_list(s: str) -> list[str]:
    vals: list[str] = []
    for tok in str(s).split(","):
        t = tok.strip()
        if t:
            vals.append(t)
    return vals


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, help="site key (data/<site>/out)")
    ap.add_argument("--scores-path", default=None, help="optional explicit scores CSV path")
    ap.add_argument("--out-dir", default=None, help="optional explicit output directory")
    ap.add_argument("--cutoff", required=True, help="test cutoff date (YYYY-MM-DD)")
    ap.add_argument("--K", type=int, default=20, help="top-K per day")
    ap.add_argument("--Ws", default="7,14,30", help="horizons in days, comma-separated")
    ap.add_argument("--B", type=int, default=500, help="bootstrap iterations")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--block-days", type=int, default=14, help="date-block length for bootstrap")
    ap.add_argument("--walk-month-offsets", default="-2,-1,0,1", help="month offsets from cutoff")
    ap.add_argument("--walk-W", type=int, default=14, help="horizon for walk-forward table")
    ap.add_argument(
        "--scores",
        default="risk_vdrop_plus_7d,v_drop,risk_vdrop_or_7d,risk_7d_mean,level_drop,risk_day,risk_ens",
        help="candidate score columns",
    )
    ap.add_argument(
        "--ci-scores",
        default="risk_vdrop_plus_7d,v_drop,risk_7d_mean,level_drop",
        help="score columns used for bootstrap CI",
    )
    return ap.parse_args()


def resolve_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    default_out = (Path("data") / str(args.site).strip() / "out").resolve()
    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else default_out
    scores_path = (
        Path(args.scores_path).expanduser().resolve()
        if args.scores_path
        else (out_dir / "scores_with_risk_ens.csv").resolve()
    )
    return scores_path, out_dir


def load_scores(scores_path: Path) -> pd.DataFrame:
    if not scores_path.is_file():
        raise FileNotFoundError(f"scores file not found: {scores_path}")
    df = pd.read_csv(scores_path, low_memory=False, encoding="utf-8-sig")
    if "date" not in df.columns or "panel_id" not in df.columns:
        raise ValueError("scores CSV must contain date, panel_id")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["panel_id"] = df["panel_id"].astype(str)
    df = df.dropna(subset=["date", "panel_id"]).copy()
    return df.sort_values(["panel_id", "date"]).reset_index(drop=True)


def load_onset_map(out_dir: Path, d_days: int) -> tuple[str, pd.Series]:
    xlsx_name = f"low_panels_2sigma_d{int(d_days)}.xlsx"
    xlsx_path = out_dir / xlsx_name
    if not xlsx_path.is_file():
        raise FileNotFoundError(f"weak-label xlsx not found: {xlsx_path}")

    x = pd.read_excel(xlsx_path, sheet_name="consecutive_alerts")
    if "panel_id" not in x.columns or "date" not in x.columns:
        raise ValueError(f"{xlsx_name} missing required columns: panel_id,date")
    x["panel_id"] = x["panel_id"].astype(str)
    x["date"] = pd.to_datetime(x["date"], errors="coerce").dt.normalize()
    x = x.dropna(subset=["panel_id", "date"])

    onset = x.groupby("panel_id")["date"].min()
    return xlsx_name, onset


def build_eval_df(scores: pd.DataFrame, onset_map: pd.Series, cutoff: pd.Timestamp, w_days: int) -> pd.DataFrame:
    df = scores[scores["date"] >= cutoff].copy()
    onset = df["panel_id"].map(onset_map)
    upper = df["date"] + pd.to_timedelta(int(w_days), unit="D")
    df["y"] = onset.notna() & (onset >= df["date"]) & (onset <= upper)
    return df


def average_precision_binary(y_true: np.ndarray, y_score: np.ndarray) -> float:
    y = y_true.astype(int)
    s = y_score.astype(float)
    m = np.isfinite(s)
    y = y[m]
    s = s[m]
    n_pos = int(y.sum())
    if n_pos <= 0:
        return float("nan")
    order = np.argsort(-s, kind="mergesort")
    y_ord = y[order]
    tp = np.cumsum(y_ord)
    fp = np.cumsum(1 - y_ord)
    prec = tp / np.maximum(tp + fp, 1)
    return float((prec * y_ord).sum() / n_pos)


def roc_auc_binary(y_true: np.ndarray, y_score: np.ndarray) -> float:
    y = y_true.astype(int)
    s = y_score.astype(float)
    m = np.isfinite(s)
    y = y[m]
    s = s[m]
    n_pos = int(y.sum())
    n_neg = int((1 - y).sum())
    if n_pos <= 0 or n_neg <= 0:
        return float("nan")
    ranks = pd.Series(s).rank(method="average").to_numpy(dtype=float)
    sum_ranks_pos = float(ranks[y == 1].sum())
    auc = (sum_ranks_pos - (n_pos * (n_pos + 1) / 2.0)) / (n_pos * n_neg)
    return float(auc)


def precision_at_k_by_day(df: pd.DataFrame, score_col: str, k: int) -> float:
    if score_col not in df.columns:
        return float("nan")
    t = df[["date", "y", score_col]].copy()
    t[score_col] = pd.to_numeric(t[score_col], errors="coerce")
    t = t.dropna(subset=[score_col, "date"])
    if t.empty:
        return float("nan")

    n_sel = 0
    n_hit = 0
    for _, g in t.groupby("date", sort=False):
        gg = g.sort_values(score_col, ascending=False).head(int(k))
        n_sel += len(gg)
        n_hit += int(gg["y"].astype(bool).sum())
    if n_sel == 0:
        return float("nan")
    return float(n_hit / n_sel)


def eval_one_score(df: pd.DataFrame, score_col: str, k: int) -> dict[str, float]:
    if score_col not in df.columns:
        return {
            "score": score_col,
            "n_rows": 0,
            "n_pos": 0,
            "base_rate": np.nan,
            "avg_precision": np.nan,
            "roc_auc": np.nan,
            "precision@K(W)": np.nan,
            "lift": np.nan,
        }

    t = df[["y", score_col]].copy()
    t[score_col] = pd.to_numeric(t[score_col], errors="coerce")
    t = t.dropna(subset=[score_col])
    n_rows = int(len(t))
    n_pos = int(t["y"].astype(int).sum())
    base_rate = float(n_pos / n_rows) if n_rows > 0 else np.nan
    ap = average_precision_binary(t["y"].to_numpy(dtype=int), t[score_col].to_numpy(dtype=float))
    auc = roc_auc_binary(t["y"].to_numpy(dtype=int), t[score_col].to_numpy(dtype=float))
    p_at_k = precision_at_k_by_day(df, score_col, k)
    lift = float(p_at_k / base_rate) if np.isfinite(base_rate) and base_rate > 0 and np.isfinite(p_at_k) else np.nan

    return {
        "score": score_col,
        "n_rows": n_rows,
        "n_pos": n_pos,
        "base_rate": base_rate,
        "avg_precision": ap,
        "roc_auc": auc,
        "precision@K(W)": p_at_k,
        "lift": lift,
    }


def eval_table(df: pd.DataFrame, score_cols: list[str], k: int) -> pd.DataFrame:
    rows = [eval_one_score(df, c, k) for c in score_cols if c in df.columns]
    if not rows:
        return pd.DataFrame(columns=["score", "n_rows", "n_pos", "base_rate", "avg_precision", "roc_auc", "precision@K(W)", "lift"])
    return pd.DataFrame(rows)


def bootstrap_sample_dates(unique_dates: np.ndarray, block_days: int, rng: np.random.Generator) -> np.ndarray:
    n = len(unique_dates)
    if n == 0:
        return unique_dates
    starts = np.arange(n)
    out: list[pd.Timestamp] = []
    while len(out) < n:
        st = int(rng.choice(starts))
        ed = min(n, st + int(block_days))
        out.extend(list(unique_dates[st:ed]))
    return np.array(out[:n], dtype="datetime64[ns]")


def bootstrap_ci(
    df: pd.DataFrame,
    score_cols: list[str],
    k: int,
    b_iters: int,
    block_days: int,
    seed: int,
) -> pd.DataFrame:
    point = eval_table(df, score_cols, k).set_index("score")
    dates = np.array(sorted(df["date"].dropna().unique()))
    if len(dates) == 0:
        return pd.DataFrame(columns=["score", "metric", "point", "boot_mean", "ci95_lo", "ci95_hi"])

    by_date = {d: g for d, g in df.groupby("date", sort=False)}
    rng = np.random.default_rng(seed)

    metrics = ["base_rate", "avg_precision", "roc_auc", "precision@K(W)", "lift"]
    boot_store: dict[tuple[str, str], list[float]] = {}
    for s in score_cols:
        for m in metrics:
            boot_store[(s, m)] = []

    for _ in range(int(b_iters)):
        sampled_dates = bootstrap_sample_dates(dates, block_days=block_days, rng=rng)
        parts = [by_date[d] for d in sampled_dates if d in by_date]
        if not parts:
            continue
        bs = pd.concat(parts, ignore_index=True)
        tbl = eval_table(bs, score_cols, k).set_index("score")
        for s in score_cols:
            if s not in tbl.index:
                continue
            for m in metrics:
                v = tbl.at[s, m]
                if np.isfinite(v):
                    boot_store[(s, m)].append(float(v))

    rows = []
    for s in score_cols:
        if s not in point.index:
            continue
        for m in metrics:
            arr = np.array(boot_store[(s, m)], dtype=float)
            if arr.size == 0:
                rows.append(
                    {
                        "score": s,
                        "metric": m,
                        "point": float(point.at[s, m]),
                        "boot_mean": np.nan,
                        "ci95_lo": np.nan,
                        "ci95_hi": np.nan,
                    }
                )
                continue
            rows.append(
                {
                    "score": s,
                    "metric": m,
                    "point": float(point.at[s, m]),
                    "boot_mean": float(np.nanmean(arr)),
                    "ci95_lo": float(np.nanpercentile(arr, 2.5)),
                    "ci95_hi": float(np.nanpercentile(arr, 97.5)),
                }
            )
    return pd.DataFrame(rows)


def bootstrap_delta_ci(
    df: pd.DataFrame,
    plus_col: str,
    base_col: str,
    k: int,
    b_iters: int,
    block_days: int,
    seed: int,
) -> pd.DataFrame:
    dates = np.array(sorted(df["date"].dropna().unique()))
    cols_need = {"y", "date", plus_col, base_col}
    if len(dates) == 0 or not cols_need.issubset(set(df.columns)):
        return pd.DataFrame(columns=["delta", "metric", "boot_mean", "ci95_lo", "ci95_hi"])

    by_date = {d: g for d, g in df.groupby("date", sort=False)}
    rng = np.random.default_rng(seed)

    d_ap: list[float] = []
    d_prec: list[float] = []
    d_lift: list[float] = []

    for _ in range(int(b_iters)):
        sampled_dates = bootstrap_sample_dates(dates, block_days=block_days, rng=rng)
        parts = [by_date[d] for d in sampled_dates if d in by_date]
        if not parts:
            continue
        bs = pd.concat(parts, ignore_index=True)

        m_plus = eval_one_score(bs, plus_col, k)
        m_base = eval_one_score(bs, base_col, k)

        ap_plus = m_plus["avg_precision"]
        ap_base = m_base["avg_precision"]
        pr_plus = m_plus["precision@K(W)"]
        pr_base = m_base["precision@K(W)"]
        lf_plus = m_plus["lift"]
        lf_base = m_base["lift"]

        if np.isfinite(ap_plus) and np.isfinite(ap_base):
            d_ap.append(float(ap_plus - ap_base))
        if np.isfinite(pr_plus) and np.isfinite(pr_base):
            d_prec.append(float(pr_plus - pr_base))
        if np.isfinite(lf_plus) and np.isfinite(lf_base):
            d_lift.append(float(lf_plus - lf_base))

    def _row(metric: str, arr: list[float]) -> dict[str, float]:
        a = np.array(arr, dtype=float)
        if a.size == 0:
            return {"delta": f"{plus_col} - {base_col}", "metric": metric, "boot_mean": np.nan, "ci95_lo": np.nan, "ci95_hi": np.nan}
        return {
            "delta": f"{plus_col} - {base_col}",
            "metric": metric,
            "boot_mean": float(np.nanmean(a)),
            "ci95_lo": float(np.nanpercentile(a, 2.5)),
            "ci95_hi": float(np.nanpercentile(a, 97.5)),
        }

    return pd.DataFrame(
        [
            _row("dAP", d_ap),
            _row("dPrec", d_prec),
            _row("dLift", d_lift),
        ]
    )


def make_walk_cutoffs(base_cutoff: pd.Timestamp, month_offsets: list[int]) -> list[pd.Timestamp]:
    cuts = []
    for m in month_offsets:
        c = (base_cutoff + pd.DateOffset(months=int(m))).normalize()
        cuts.append(c)
    cuts = sorted(set(cuts))
    return cuts


def fmt_float(x: float) -> str:
    if x is None or not np.isfinite(x):
        return "nan"
    return f"{float(x):.6f}"


def write_onepage(
    path: Path,
    out_dir: Path,
    site: str,
    cutoff: pd.Timestamp,
    k: int,
    ws: list[int],
    sens_tbl: pd.DataFrame,
    walk_tbl: pd.DataFrame,
) -> None:
    lines: list[str] = []
    lines.append(f"# {site} 2σ weak-label 평가 ONEPAGE")
    lines.append("")
    lines.append(f"- cutoff: `{cutoff.date()}`")
    lines.append(f"- K: `{k}`")
    lines.append(f"- W set: `{','.join(map(str, ws))}`")
    lines.append("")
    lines.append("## 민감도 핵심 (D=2/D=3, W별 AP 상위 2개)")
    lines.append("")
    lines.append("| D | W | score | AP | precision@K(W) | lift |")
    lines.append("|---|---:|---|---:|---:|---:|")

    for w in ws:
        for d in (2, 3):
            part = sens_tbl[(sens_tbl["W_days"] == w) & (sens_tbl["xlsx"].str.contains(f"_d{d}"))].copy()
            if part.empty:
                continue
            part = part.sort_values("avg_precision", ascending=False).head(2)
            for _, r in part.iterrows():
                lines.append(
                    f"| {d} | {w} | {r['score']} | {fmt_float(r['avg_precision'])} | "
                    f"{fmt_float(r['precision@K(W)'])} | {fmt_float(r['lift'])} |"
                )
    lines.append("")
    lines.append("## Walk-forward 핵심 (W=14)")
    lines.append("")
    lines.append("| cutoff | score | AP | precision@K | lift |")
    lines.append("|---|---|---:|---:|---:|")
    if not walk_tbl.empty:
        for c in sorted(walk_tbl["cutoff"].dropna().unique()):
            part = walk_tbl[walk_tbl["cutoff"] == c].sort_values("AP", ascending=False).head(2)
            for _, r in part.iterrows():
                lines.append(
                    f"| {pd.to_datetime(c).date()} | {r['score']} | {fmt_float(r['AP'])} | "
                    f"{fmt_float(r['precision@K'])} | {fmt_float(r['lift'])} |"
                )
    lines.append("")
    lines.append("## Delta 요약 (plus − v_drop)")
    lines.append("")
    lines.append("| W | metric | boot_mean | ci95_lo | ci95_hi |")
    lines.append("|---:|---|---:|---:|---:|")

    d_ap_judge: dict[int, str] = {}
    for w in ws:
        p = out_dir / f"CI_BOOTSTRAP_delta_test_W{int(w)}_K{int(k)}.csv"
        if not p.is_file():
            continue
        ddf = pd.read_csv(p, encoding="utf-8-sig")
        for metric in ["dAP", "dPrec", "dLift"]:
            r = ddf[ddf["metric"] == metric]
            if r.empty:
                continue
            rr = r.iloc[0]
            lines.append(
                f"| {int(w)} | {metric} | {fmt_float(rr.get('boot_mean', np.nan))} | "
                f"{fmt_float(rr.get('ci95_lo', np.nan))} | {fmt_float(rr.get('ci95_hi', np.nan))} |"
            )
            if metric == "dAP":
                lo = pd.to_numeric(pd.Series([rr.get("ci95_lo", np.nan)]), errors="coerce").iloc[0]
                hi = pd.to_numeric(pd.Series([rr.get("ci95_hi", np.nan)]), errors="coerce").iloc[0]
                if np.isfinite(lo) and lo > 0:
                    d_ap_judge[int(w)] = "better"
                elif np.isfinite(hi) and hi < 0:
                    d_ap_judge[int(w)] = "worse"
                else:
                    d_ap_judge[int(w)] = "inconclusive"

    lines.append("")
    if d_ap_judge:
        for w in sorted(d_ap_judge.keys()):
            j = d_ap_judge[w]
            if j == "better":
                msg = "유의하게 plus가 더 좋음"
            elif j == "worse":
                msg = "유의하게 plus가 더 나쁨"
            else:
                msg = "유의성 단정 불가"
            lines.append(f"- 판정(W={w}): {msg}")

        lines.append("")
        judgments = [d_ap_judge[w] for w in sorted(d_ap_judge.keys())]
        if all(j == "worse" for j in judgments):
            lines.append("- 요약 결론: W=7/14/30 모두에서 plus가 유의하게 더 나빠, AP 기준 유의한 악화로 판단된다.")
        elif all(j == "better" for j in judgments):
            lines.append("- 요약 결론: W=7/14/30 모두에서 plus가 유의하게 더 좋아, AP 기준 유의한 개선으로 판단된다.")
        elif any(j == "better" for j in judgments) and any(j == "worse" for j in judgments):
            lines.append("- 요약 결론: W별 판정이 개선/악화로 혼재되어 단일 방향 결론을 내리기 어렵다.")
        else:
            lines.append("- 요약 결론: 일부 W에서만 유의하며 나머지는 유의성 단정 불가다.")
    else:
        lines.append("- 결론: delta 부트스트랩 파일이 없어 dAP 유의성 판정 불가.")
    lines.append("")
    lines.append("## 생성 파일")
    lines.append("- `SENSITIVITY_D2D3_test_metrics.csv`")
    lines.append("- `WALKFORWARD_cutoffs_W14_K20.csv` (W/K는 실행 인자에 따라 달라짐)")
    lines.append("- `CI_BOOTSTRAP_test_W{W}_K{K}.csv`")
    lines.append("- `CI_BOOTSTRAP_delta_test_W{W}_K{K}.csv`")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    ws = parse_int_list(args.Ws)
    score_cols = parse_str_list(args.scores)
    ci_scores = parse_str_list(args.ci_scores)
    cutoff = pd.to_datetime(args.cutoff, errors="coerce").normalize()
    if pd.isna(cutoff):
        raise ValueError(f"invalid cutoff: {args.cutoff}")

    scores_path, out_dir = resolve_paths(args)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] scores={scores_path}")
    print(f"[INFO] out_dir={out_dir}")
    print(f"[INFO] cutoff={cutoff.date()} K={args.K} Ws={ws} B={args.B}")

    scores = load_scores(scores_path)
    existing_scores = [c for c in score_cols if c in scores.columns]
    existing_ci_scores = [c for c in ci_scores if c in scores.columns]
    print(f"[INFO] using score cols: {existing_scores}")
    print(f"[INFO] using CI score cols: {existing_ci_scores}")

    sensitivity_rows: list[dict] = []
    for d in (2, 3):
        xlsx_name, onset_map = load_onset_map(out_dir, d_days=d)
        for w in ws:
            ev = build_eval_df(scores, onset_map, cutoff=cutoff, w_days=w)
            tbl = eval_table(ev, existing_scores, k=int(args.K))
            if tbl.empty:
                continue
            tbl.insert(0, "xlsx", xlsx_name)
            tbl.insert(1, "W_days", int(w))
            sensitivity_rows.extend(tbl.to_dict(orient="records"))

            if d == 3:
                ci = bootstrap_ci(
                    ev,
                    score_cols=existing_ci_scores,
                    k=int(args.K),
                    b_iters=int(args.B),
                    block_days=int(args.block_days),
                    seed=int(args.seed) + int(w),
                )
                ci_path = out_dir / f"CI_BOOTSTRAP_test_W{int(w)}_K{int(args.K)}.csv"
                ci.to_csv(ci_path, index=False, encoding="utf-8-sig")
                print(f"[OK] wrote {ci_path}")

                if ("risk_vdrop_plus_7d" in ev.columns) and ("v_drop" in ev.columns):
                    delta = bootstrap_delta_ci(
                        ev,
                        plus_col="risk_vdrop_plus_7d",
                        base_col="v_drop",
                        k=int(args.K),
                        b_iters=int(args.B),
                        block_days=int(args.block_days),
                        seed=int(args.seed) + 1000 + int(w),
                    )
                    d_path = out_dir / f"CI_BOOTSTRAP_delta_test_W{int(w)}_K{int(args.K)}.csv"
                    delta.to_csv(d_path, index=False, encoding="utf-8-sig")
                    print(f"[OK] wrote {d_path}")

    sens = pd.DataFrame(sensitivity_rows)
    sens_path = out_dir / "SENSITIVITY_D2D3_test_metrics.csv"
    sens.to_csv(sens_path, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote {sens_path}")

    walk_offsets = parse_int_list(args.walk_month_offsets)
    walk_cutoffs = make_walk_cutoffs(cutoff, walk_offsets)
    _, onset_d3 = load_onset_map(out_dir, d_days=3)
    walk_scores = [c for c in ["risk_vdrop_plus_7d", "v_drop", "risk_7d_mean", "level_drop"] if c in scores.columns]
    walk_rows: list[dict] = []
    for c in walk_cutoffs:
        ev = build_eval_df(scores, onset_d3, cutoff=c, w_days=int(args.walk_W))
        tbl = eval_table(ev, walk_scores, k=int(args.K))
        for _, r in tbl.iterrows():
            walk_rows.append(
                {
                    "cutoff": pd.to_datetime(c).date().isoformat(),
                    "W": int(args.walk_W),
                    "K": int(args.K),
                    "score": r["score"],
                    "n_rows": int(r["n_rows"]),
                    "n_pos": int(r["n_pos"]),
                    "base_rate": r["base_rate"],
                    "AP": r["avg_precision"],
                    "precision@K": r["precision@K(W)"],
                    "lift": r["lift"],
                }
            )
    walk = pd.DataFrame(walk_rows)
    walk_path = out_dir / f"WALKFORWARD_cutoffs_W{int(args.walk_W)}_K{int(args.K)}.csv"
    walk.to_csv(walk_path, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote {walk_path}")

    onepage_path = out_dir / f"RESULTS_2SIGMA_{str(args.site).upper()}_ONEPAGE.md"
    write_onepage(
        onepage_path,
        out_dir=out_dir,
        site=str(args.site),
        cutoff=cutoff,
        k=int(args.K),
        ws=ws,
        sens_tbl=sens,
        walk_tbl=walk,
    )
    print(f"[OK] wrote {onepage_path}")


if __name__ == "__main__":
    main()
