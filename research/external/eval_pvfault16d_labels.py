#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

SCORE_SPECS = [
    ("mid_ratio", "bad_level=-mid_ratio"),
    ("recon_error", "higher_is_worse"),
    ("dtw_dist", "higher_is_worse"),
    ("hs_score", "higher_is_worse"),
    ("v_drop", "higher_is_worse"),
    ("risk_day", "higher_is_worse"),
    ("risk_ens", "higher_is_worse"),
]


def _fmt(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, (float, np.floating)):
        if np.isnan(x):
            return ""
        return f"{x:.6g}"
    return str(x)


def _to_md_table(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "_(no rows)_"
    cols = list(df.columns)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in df.iterrows():
        vals = [_fmt(row[c]).replace("|", "\\|") for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def _roc_auc_rank(y: np.ndarray, score: np.ndarray) -> float:
    y = y.astype(int)
    s = pd.Series(score)
    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = s.rank(method="average")
    sum_pos = float(ranks[y == 1].sum())
    auc = (sum_pos - (n_pos * (n_pos + 1) / 2.0)) / (n_pos * n_neg)
    return float(auc)


def _average_precision(y: np.ndarray, score: np.ndarray) -> float:
    y = y.astype(int)
    n_pos = int((y == 1).sum())
    if n_pos == 0:
        return float("nan")
    order = np.argsort(-score, kind="mergesort")
    y_sorted = y[order]
    tp = np.cumsum(y_sorted)
    k = np.arange(1, len(y_sorted) + 1)
    precision = tp / k
    ap = float(precision[y_sorted == 1].mean()) if np.any(y_sorted == 1) else float("nan")
    return ap


def _spearman_corr(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 2 or len(y) < 2:
        return float("nan")
    xr = pd.Series(x).rank(method="average").to_numpy(dtype=float)
    yr = pd.Series(y).rank(method="average").to_numpy(dtype=float)
    if np.nanstd(xr) == 0 or np.nanstd(yr) == 0:
        return float("nan")
    return float(np.corrcoef(xr, yr)[0, 1])


def _is_constant(x: np.ndarray) -> bool:
    if len(x) == 0:
        return True
    s = pd.Series(x)
    return int(s.nunique(dropna=True)) < 2


def _bootstrap_ci(
    score: np.ndarray,
    target: np.ndarray,
    metric_fn: Callable[[np.ndarray, np.ndarray], float],
    b: int,
    seed: int,
) -> tuple[float, float, float]:
    n = len(score)
    if n <= 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    vals: list[float] = []
    for _ in range(int(b)):
        idx = rng.integers(0, n, size=n)
        v = metric_fn(score[idx], target[idx])
        if np.isfinite(v):
            vals.append(float(v))
    if not vals:
        return float("nan"), float("nan"), float("nan")
    arr = np.asarray(vals, dtype=float)
    return float(np.mean(arr)), float(np.quantile(arr, 0.025)), float(np.quantile(arr, 0.975))


def _mode_scalar(s: pd.Series) -> float:
    m = pd.to_numeric(s, errors="coerce").mode(dropna=True)
    return float(m.iloc[0]) if len(m) else np.nan


def _safe_ratio(series: pd.Series, value: int) -> float:
    s = pd.to_numeric(series, errors="coerce")
    valid = s.notna()
    n = int(valid.sum())
    if n == 0:
        return float("nan")
    return float(((s == value) & valid).sum() / n)


def _nonzero_mode(series: pd.Series) -> int:
    s = pd.to_numeric(series, errors="coerce")
    s = s[s.notna() & (s != 0)]
    if s.empty:
        return 0
    m = s.mode(dropna=True)
    if m.empty:
        return 0
    return int(m.iloc[0])


def _load_day_labels_from_converted(path: str | Path) -> pd.DataFrame:
    converted = pd.read_csv(path)
    if "date_time" not in converted.columns or "fault_label" not in converted.columns:
        raise RuntimeError("converted.csv must contain `date_time` and `fault_label` columns.")
    converted["date"] = pd.to_datetime(converted["date_time"], errors="coerce").dt.normalize()
    converted["fault_label"] = pd.to_numeric(converted["fault_label"], errors="coerce")
    converted = converted.dropna(subset=["date"]).copy()

    labels_day = (
        converted.groupby("date", sort=True)["fault_label"]
        .agg(
            pos_ratio_day=lambda s: float(((pd.to_numeric(s, errors="coerce") != 0) & pd.to_numeric(s, errors="coerce").notna()).mean()),
            type_ratio_1=lambda s: _safe_ratio(s, 1),
            type_ratio_2=lambda s: _safe_ratio(s, 2),
            type_ratio_3=lambda s: _safe_ratio(s, 3),
            type_ratio_4=lambda s: _safe_ratio(s, 4),
            label_mode_nonzero_day=lambda s: _nonzero_mode(s),
            n_samples=lambda s: int(pd.to_numeric(s, errors="coerce").notna().sum()),
        )
        .reset_index()
    )
    return labels_day


def _load_scores_day(scores_path: str | Path, agg: str) -> tuple[pd.DataFrame, list[str], list[str]]:
    scores = pd.read_csv(scores_path)
    if "date" not in scores.columns:
        raise RuntimeError("scores csv must contain `date` column.")
    scores["date"] = pd.to_datetime(scores["date"], errors="coerce").dt.normalize()

    available: list[str] = []
    excluded: list[str] = []
    oriented = pd.DataFrame({"date": scores["date"]})
    for col, _desc in SCORE_SPECS:
        if col not in scores.columns:
            excluded.append(col)
            continue
        raw = pd.to_numeric(scores[col], errors="coerce")
        if col == "mid_ratio":
            oriented[col] = -raw
        else:
            oriented[col] = raw
        available.append(col)

    if not available:
        raise RuntimeError("No usable score columns found in scores file.")
    agg_fn = "max" if agg == "max" else "mean"
    scores_day = oriented.groupby("date", sort=True)[available].agg(agg_fn).reset_index()
    return scores_day, available, excluded


def evaluate(args: argparse.Namespace) -> tuple[Path, Path]:
    labels_day = _load_day_labels_from_converted(args.converted)
    scores_day, available_scores, excluded = _load_scores_day(args.scores, agg=args.agg)
    merged = labels_day.merge(scores_day, on="date", how="inner")
    if merged.empty:
        raise RuntimeError("No overlapping dates between scores and converted labels.")

    pos_ratio = pd.to_numeric(merged["pos_ratio_day"], errors="coerce")
    q25 = float(pos_ratio.quantile(0.25))
    q75 = float(pos_ratio.quantile(0.75))

    cont_rows: list[dict[str, Any]] = []
    hl_rows: list[dict[str, Any]] = []
    type_rows: list[dict[str, Any]] = []
    na_reasons: list[str] = []

    for col, desc in SCORE_SPECS:
        if col not in merged.columns:
            continue
        score = pd.to_numeric(merged[col], errors="coerce")
        use = pd.DataFrame({"score": score, "target": pos_ratio}).dropna(subset=["score", "target"])
        if use.empty:
            excluded.append(f"{col} (all NaN)")
            continue

        x = use["score"].to_numpy(dtype=float)
        y = use["target"].to_numpy(dtype=float)
        score_const = _is_constant(x)
        target_const = _is_constant(y)
        sp_status = "ok"
        sp_note = ""
        if score_const or target_const:
            sp = float("nan")
            sp_mean, sp_lo, sp_hi = float("nan"), float("nan"), float("nan")
            why = []
            if score_const:
                why.append("score constant")
            if target_const:
                why.append("target constant")
            sp_status = "NA(constant)"
            sp_note = ", ".join(why)
            na_reasons.append(f"{col}: Spearman=NA(constant) because {sp_note}.")
        else:
            sp = _spearman_corr(x, y)
            sp_mean, sp_lo, sp_hi = _bootstrap_ci(
                x,
                y,
                metric_fn=lambda s, t: _spearman_corr(s, t),
                b=int(args.bootstrap),
                seed=int(args.seed),
            )
        cont_rows.append(
            {
                "metric_group": "continuous_pos_ratio",
                "score": col,
                "direction": desc,
                "n_rows": int(len(use)),
                "spearman": sp,
                "spearman_boot_mean": sp_mean,
                "spearman_ci95_lo": sp_lo,
                "spearman_ci95_hi": sp_hi,
                "spearman_status": sp_status,
                "na_reason": sp_note,
            }
        )

        use_hl = use[(use["target"] <= q25) | (use["target"] >= q75)].copy()
        y_hl = (use_hl["target"] >= q75).astype(int).to_numpy(dtype=int)
        s_hl = use_hl["score"].to_numpy(dtype=float)
        hl_score_const = _is_constant(s_hl)
        hl_target_const = _is_constant(y_hl)
        if hl_score_const or hl_target_const:
            auc_hl = float("nan")
            ap_hl = float("nan")
            auc_mean, auc_lo, auc_hi = float("nan"), float("nan"), float("nan")
            ap_mean, ap_lo, ap_hi = float("nan"), float("nan"), float("nan")
        else:
            auc_hl = _roc_auc_rank(y_hl, s_hl)
            ap_hl = _average_precision(y_hl, s_hl)
            auc_mean, auc_lo, auc_hi = _bootstrap_ci(
                s_hl,
                y_hl,
                metric_fn=lambda s, t: _roc_auc_rank(t.astype(int), s),
                b=int(args.bootstrap),
                seed=int(args.seed),
            )
            ap_mean, ap_lo, ap_hi = _bootstrap_ci(
                s_hl,
                y_hl,
                metric_fn=lambda s, t: _average_precision(t.astype(int), s),
                b=int(args.bootstrap),
                seed=int(args.seed),
            )
        hl_rows.append(
            {
                "metric_group": "heavy_vs_light",
                "score": col,
                "direction": desc,
                "q25": q25,
                "q75": q75,
                "n_rows": int(len(use_hl)),
                "n_pos": int((y_hl == 1).sum()),
                "base_rate": float((y_hl == 1).mean()) if len(y_hl) else float("nan"),
                "roc_auc": auc_hl,
                "roc_auc_boot_mean": auc_mean,
                "roc_auc_ci95_lo": auc_lo,
                "roc_auc_ci95_hi": auc_hi,
                "ap": ap_hl,
                "ap_boot_mean": ap_mean,
                "ap_ci95_lo": ap_lo,
                "ap_ci95_hi": ap_hi,
                "hl_status": "NA(constant)" if (hl_score_const or hl_target_const) else "ok",
            }
        )

        use_t = pd.DataFrame(
            {
                "score": pd.to_numeric(merged[col], errors="coerce"),
                "ratio_4": pd.to_numeric(merged["type_ratio_4"], errors="coerce"),
            }
        ).dropna(subset=["score", "ratio_4"])
        if use_t.empty:
            continue
        r4_q25 = float(use_t["ratio_4"].quantile(0.25))
        r4_q75 = float(use_t["ratio_4"].quantile(0.75))
        med_low = float(use_t.loc[use_t["ratio_4"] <= r4_q25, "score"].median())
        med_high = float(use_t.loc[use_t["ratio_4"] >= r4_q75, "score"].median())
        type_rows.append(
            {
                "metric_group": "type_ratio4",
                "score": col,
                "direction": desc,
                "n_rows": int(len(use_t)),
                "spearman_score_vs_ratio4": _spearman_corr(
                    use_t["score"].to_numpy(dtype=float),
                    use_t["ratio_4"].to_numpy(dtype=float),
                ),
                "median_score_ratio4_q25": med_low,
                "median_score_ratio4_q75": med_high,
            }
        )

    cont_df = pd.DataFrame(cont_rows)
    hl_df = pd.DataFrame(hl_rows)
    type_df = pd.DataFrame(type_rows)
    metrics_df = pd.concat([cont_df, hl_df, type_df], ignore_index=True, sort=False)

    cont_md_df = cont_df.copy()
    if not cont_md_df.empty and "spearman_status" in cont_md_df.columns:
        cont_md_df["spearman"] = cont_md_df["spearman"].astype(object)
        const_mask = cont_md_df["spearman_status"] != "ok"
        cont_md_df.loc[const_mask, "spearman"] = "NA(constant)"

    out_md = Path(args.out)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_csv = Path(args.out_metrics) if args.out_metrics else (out_md.parent / "EXTERNAL_PVFAULT_METRICS.csv")
    metrics_df.to_csv(out_csv, index=False)

    lines = []
    lines.append("# EXTERNAL PVFAULT ONEPAGE")
    lines.append("")
    lines.append("## Setup")
    lines.append(f"- scores: `{Path(args.scores)}`")
    lines.append(f"- converted: `{Path(args.converted)}`")
    if args.labels:
        lines.append(f"- labels (ignored): `{Path(args.labels)}`")
    lines.append(f"- score_day_agg: `{args.agg}`")
    lines.append(f"- bootstrap_B: {int(args.bootstrap)}")
    lines.append(f"- n_days_merged: {len(merged)}")
    lines.append(f"- n_days_pos_any(pos_ratio_day>0): {int((pos_ratio > 0).sum())} / {int(pos_ratio.notna().sum())}")
    lines.append(f"- heavy_vs_light thresholds: q25={q25:.6g}, q75={q75:.6g}")
    lines.append("")
    lines.append("본 데이터는 모든 날짜에 fault_label!=0 구간이 일부 존재하여, any>0 이진 라벨은 전부 positive가 된다.")
    lines.append("따라서 외부 검증은 정상/고장 판별이 아니라, fault 비율(pos_ratio)이라는 강도(target intensity)에 대해 점수가 단조적으로 반응하는지로 평가한다.")
    lines.append("string1/string2 라벨이 날짜별 동일하여 날짜 단위로 중복을 제거했다.")
    lines.append("")
    lines.append("## Continuous Target (target=pos_ratio): Spearman + bootstrap CI")
    lines.append(_to_md_table(cont_md_df))
    lines.append("")
    lines.append("## Heavy-vs-Light (q25/q75): ROC-AUC / AP + bootstrap CI")
    lines.append(_to_md_table(hl_df))
    lines.append("")
    lines.append("## Type Summary (ratio_4 vs score_bad correlation)")
    lines.append(_to_md_table(type_df))
    lines.append("")
    lines.append("## Excluded Scores")
    if excluded:
        for c in excluded:
            lines.append(f"- {c}: not present in input scores (or unusable)")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## NA 이유")
    if na_reasons:
        for s in na_reasons:
            lines.append(f"- {s}")
    else:
        lines.append("- 없음")
    lines.append("")
    lines.append("## Notes")
    lines.append("- Sample unit is fixed to date-level (one row per date).")
    lines.append("- mid_ratio uses bad_level=-mid_ratio (no clipping).")
    lines.append("- heavy-vs-light keeps only pos_ratio<=q25 or >=q75 and drops middle range.")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_md, out_csv


def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Evaluate pvfault16d external labels against pvdiag scores.")
    ap.add_argument("--scores", default="data/pvfault16d/out/ae_simple_scores.csv", help="Scores csv path")
    ap.add_argument("--labels", default="", help="Deprecated/optional; ignored (kept for CLI compatibility).")
    ap.add_argument("--converted", default="data/pvfault16d/converted.csv", help="Converted raw csv path")
    ap.add_argument("--out", default="data/pvfault16d/out/EXTERNAL_PVFAULT_ONEPAGE.md", help="Output onepage md path")
    ap.add_argument("--out-metrics", default="data/pvfault16d/out/EXTERNAL_PVFAULT_METRICS.csv", help="Output metrics csv path")
    ap.add_argument("--agg", choices=["max", "mean"], default="max", help="Date-level aggregation across panels")
    ap.add_argument("--bootstrap", type=int, default=500, help="Bootstrap repetitions")
    ap.add_argument("--seed", type=int, default=42, help="Bootstrap random seed")
    return ap


def main() -> None:
    args = build_argparser().parse_args()
    out_md, out_csv = evaluate(args)
    print(f"[OK] wrote onepage: {out_md}")
    print(f"[OK] wrote metrics: {out_csv}")


if __name__ == "__main__":
    main()
