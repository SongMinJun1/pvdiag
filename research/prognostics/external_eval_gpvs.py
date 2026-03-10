#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
from typing import Any

import numpy as np
import pandas as pd


SCORE_COLS = [
    "ae_like",
    "dtw_like",
    "hs_like",
    "level_drop_like",
    "v_drop_like",
]
RAW_SCORE_MAP = {
    "ae_like": "ae_raw",
    "dtw_like": "dtw_raw",
    "hs_like": "hs_raw",
    "level_drop_like": "level_drop_raw",
    "v_drop_like": "v_drop_raw",
}
NOAE_RAW_COLS = [
    "level_drop_raw",
    "v_drop_raw",
    "dtw_raw",
    "hs_raw",
]
FPR1 = 0.01
DEGENERATE_SPAN_EPS = 1e-12


def _derive_positive_label(df: pd.DataFrame) -> np.ndarray:
    # Priority: window-level label -> file-level label -> scenario-id fallback.
    if "is_fault_window" in df.columns:
        y = pd.to_numeric(df["is_fault_window"], errors="coerce").fillna(0).astype(int).to_numpy()
        return (y != 0).astype(int)
    if "is_fault_file" in df.columns:
        y = pd.to_numeric(df["is_fault_file"], errors="coerce").fillna(0).astype(int).to_numpy()
        return (y != 0).astype(int)
    if "fault_sid" in df.columns:
        sid = pd.to_numeric(df["fault_sid"], errors="coerce").fillna(0).to_numpy(dtype=float)
        return (sid > 0).astype(int)
    # Backward compatibility for older ingest outputs.
    y = pd.to_numeric(df.get("label_fault"), errors="coerce").fillna(0).astype(int).to_numpy()
    return (y != 0).astype(int)


def _fmt(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, (float, np.floating)):
        if np.isnan(x):
            return ""
        return f"{x:.6g}"
    return str(x)


def _to_md_table(df: pd.DataFrame) -> str:
    if df.empty:
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
    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return np.nan
    ranks = pd.Series(score).rank(method="average")
    sum_pos = float(ranks[y == 1].sum())
    auc = (sum_pos - (n_pos * (n_pos + 1) / 2.0)) / (n_pos * n_neg)
    return float(auc)


def _average_precision(y: np.ndarray, score: np.ndarray) -> float:
    y = y.astype(int)
    n_pos = int((y == 1).sum())
    if n_pos == 0:
        return np.nan
    order = np.argsort(-score, kind="mergesort")
    y_sorted = y[order]
    tp = np.cumsum(y_sorted)
    k = np.arange(1, len(y_sorted) + 1)
    precision = tp / k
    return float(precision[y_sorted == 1].mean()) if np.any(y_sorted == 1) else np.nan


def _precision_at_k(y: np.ndarray, score: np.ndarray, k: int) -> tuple[float, int]:
    n = len(y)
    if n == 0:
        return np.nan, 0
    k_used = int(min(max(1, k), n))
    order = np.argsort(-score, kind="mergesort")
    topk = y[order[:k_used]]
    return float(np.mean(topk)), k_used


def _threshold_at_fpr(score: np.ndarray, y: np.ndarray, fpr: float = FPR1) -> dict[str, float]:
    finite = np.isfinite(score) & np.isfinite(y)
    if not np.any(finite):
        return {"threshold_fpr1": np.nan, "actual_fpr_fpr1": np.nan}
    score_f = score[finite]
    y_f = y[finite].astype(int)
    healthy = np.sort(score_f[y_f == 0].astype(float))
    if len(healthy) == 0:
        return {"threshold_fpr1": np.nan, "actual_fpr_fpr1": np.nan}

    # Use a strict rule `score > tau` and choose tau from observed healthy values
    # so that actual healthy-side FPR is <= target and as close as possible.
    candidates = np.unique(healthy)
    chosen_tau = float(np.max(healthy))
    chosen_fpr = 0.0
    for tau in candidates:
        actual_fpr = float(np.mean(healthy > tau))
        if actual_fpr <= fpr and actual_fpr >= chosen_fpr:
            chosen_tau = float(tau)
            chosen_fpr = actual_fpr
    return {"threshold_fpr1": chosen_tau, "actual_fpr_fpr1": chosen_fpr}


def _binary_metrics_at_threshold(y: np.ndarray, score: np.ndarray, threshold: float) -> dict[str, float]:
    finite = np.isfinite(score) & np.isfinite(y)
    if not np.any(finite) or not np.isfinite(threshold):
        return {
            "precision_fpr1": np.nan,
            "recall_fpr1": np.nan,
            "f1_fpr1": np.nan,
        }
    score_f = score[finite]
    y_f = y[finite].astype(int)
    pred = score_f > threshold
    tp = int(np.sum(pred & (y_f == 1)))
    fp = int(np.sum(pred & (y_f == 0)))
    fn = int(np.sum((~pred) & (y_f == 1)))
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else np.nan
    if np.isfinite(recall) and (precision + recall) > 0:
        f1 = float((2.0 * precision * recall) / (precision + recall))
    elif np.isfinite(recall):
        f1 = 0.0
    else:
        f1 = np.nan
    return {
        "precision_fpr1": precision,
        "recall_fpr1": recall,
        "f1_fpr1": f1,
    }


def _score_degeneracy(score: np.ndarray, span_eps: float = DEGENERATE_SPAN_EPS) -> dict[str, float]:
    finite = np.isfinite(score)
    if not np.any(finite):
        return {
            "n_unique_score": 0.0,
            "score_span": np.nan,
            "degenerate_score": 1.0,
        }
    score_f = score[finite].astype(float)
    n_unique = int(pd.Series(score_f).nunique(dropna=True))
    span = float(np.max(score_f) - np.min(score_f)) if len(score_f) else np.nan
    deg = int(n_unique <= 1 or (np.isfinite(span) and span <= span_eps))
    return {
        "n_unique_score": float(n_unique),
        "score_span": span,
        "degenerate_score": float(deg),
    }


def _corr_sign(raw: np.ndarray, like: np.ndarray) -> float:
    finite = np.isfinite(raw) & np.isfinite(like)
    if int(np.sum(finite)) < 2:
        return 1.0
    raw_f = raw[finite].astype(float)
    like_f = like[finite].astype(float)
    if float(np.nanstd(raw_f)) <= 0.0 or float(np.nanstd(like_f)) <= 0.0:
        return 1.0
    corr = np.corrcoef(raw_f, like_f)[0, 1]
    if not np.isfinite(corr):
        return 1.0
    return -1.0 if corr < 0 else 1.0


def _mad(x: np.ndarray) -> float:
    xf = x[np.isfinite(x)].astype(float)
    if len(xf) == 0:
        return np.nan
    med = float(np.median(xf))
    return float(np.median(np.abs(xf - med)))


def _build_ensemble_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ensemble_raw"] = np.nan
    out["ensemble_active_axes"] = np.nan
    out["ensemble_degenerate_axes"] = ""
    for raw_col in RAW_SCORE_MAP.values():
        out[f"z_{raw_col}"] = np.nan

    if "source_id" in out.columns:
        group_keys = out["source_id"].fillna("src").astype(str)
    else:
        group_keys = pd.Series(["src"] * len(out), index=out.index, dtype=str)
    y_all = _derive_positive_label(out)

    for sid, idx in group_keys.groupby(group_keys).groups.items():
        g = out.loc[idx].copy()
        y = y_all[g.index]
        active_cols: list[str] = []
        deg_cols: list[str] = []
        z_cols: list[np.ndarray] = []
        pre_mask = (y == 0)

        for like_col in SCORE_COLS:
            raw_col = RAW_SCORE_MAP.get(like_col, "")
            if like_col not in g.columns or raw_col not in g.columns:
                deg_cols.append(raw_col or like_col)
                continue
            raw = pd.to_numeric(g[raw_col], errors="coerce").to_numpy(dtype=float)
            like = pd.to_numeric(g[like_col], errors="coerce").to_numpy(dtype=float)
            sign = _corr_sign(raw, like)
            raw_signed = raw * sign
            pre_vals = raw_signed[pre_mask & np.isfinite(raw_signed)]
            deg = _score_degeneracy(pre_vals)
            mad = _mad(pre_vals)
            if bool(deg["degenerate_score"]) or not np.isfinite(mad) or mad <= 0.0:
                deg_cols.append(raw_col)
                continue
            med = float(np.median(pre_vals))
            z = (raw_signed - med) / (1.4826 * mad)
            z_cols.append(z.astype(float))
            active_cols.append(raw_col)
            out.loc[g.index, f"z_{raw_col}"] = z.astype(float)

        if z_cols:
            z_mat = np.vstack(z_cols)
            ensemble_raw = np.nanmean(z_mat, axis=0)
            active_count = float(len(active_cols))
        else:
            ensemble_raw = np.full(len(g), np.nan, dtype=float)
            active_count = 0.0
        out.loc[g.index, "ensemble_raw"] = ensemble_raw
        out.loc[g.index, "ensemble_active_axes"] = active_count
        out.loc[g.index, "ensemble_degenerate_axes"] = ",".join(deg_cols)

    return out


def _detection_delay(
    score: np.ndarray,
    y: np.ndarray,
    source: np.ndarray,
    order: np.ndarray,
    k: int,
    thr_q: float = 0.95,
) -> dict[str, float]:
    finite = np.isfinite(score) & np.isfinite(y)
    if not np.any(finite):
        return {
            "thr_q": thr_q,
            "thr_val": np.nan,
            "event_count": 0.0,
            "detect_rate": np.nan,
            "delay_mean": np.nan,
            "delay_median": np.nan,
            "delay_p25": np.nan,
            "delay_p75": np.nan,
        }
    score_f = score[finite]
    y_f = y[finite].astype(int)
    src_f = source[finite].astype(str)
    ord_f = order[finite].astype(float)

    healthy = score_f[y_f == 0]
    if len(healthy):
        thr_val = float(np.quantile(healthy, thr_q))
    else:
        thr_val = float(np.quantile(score_f, thr_q))

    n = len(score_f)
    k_used = int(min(max(1, k), n))
    top_idx = np.argsort(-score_f, kind="mergesort")[:k_used]
    top_flag = np.zeros(n, dtype=bool)
    top_flag[top_idx] = True

    delays: list[float] = []
    event_cnt = 0
    for sid in np.unique(src_f):
        m = src_f == sid
        yy = y_f[m]
        if int(np.sum(yy == 1)) == 0:
            continue
        event_cnt += 1
        ord_sid = ord_f[m]
        sid_idx = np.where(m)[0]
        local_order = np.argsort(ord_sid, kind="mergesort")
        yy_s = yy[local_order]
        ss_s = score_f[m][local_order]
        tt_s = top_flag[sid_idx][local_order]
        onset = int(np.where(yy_s == 1)[0][0])

        cand = []
        hit_thr = np.where(ss_s >= thr_val)[0]
        if len(hit_thr):
            cand.append(int(hit_thr[0]))
        hit_top = np.where(tt_s)[0]
        if len(hit_top):
            cand.append(int(hit_top[0]))
        if cand:
            detect = min(cand)
            delays.append(float(detect - onset))

    d = np.asarray(delays, dtype=float)
    return {
        "thr_q": float(thr_q),
        "thr_val": float(thr_val),
        "event_count": float(event_cnt),
        "detect_rate": float(len(d) / event_cnt) if event_cnt > 0 else np.nan,
        "delay_mean": float(np.mean(d)) if len(d) else np.nan,
        "delay_median": float(np.median(d)) if len(d) else np.nan,
        "delay_p25": float(np.quantile(d, 0.25)) if len(d) else np.nan,
        "delay_p75": float(np.quantile(d, 0.75)) if len(d) else np.nan,
    }


def _post_detection_summary(
    score: np.ndarray,
    y: np.ndarray,
    source: np.ndarray,
    order: np.ndarray,
    threshold: float,
) -> dict[str, float]:
    finite = np.isfinite(score) & np.isfinite(y)
    if not np.any(finite) or not np.isfinite(threshold):
        return {
            "detect_rate_post": np.nan,
            "delay_first_post_windows": np.nan,
            "event_count_post": 0.0,
        }
    score_f = score[finite]
    y_f = y[finite].astype(int)
    src_f = source[finite].astype(str)
    ord_f = order[finite].astype(float)

    delays: list[float] = []
    event_cnt = 0
    detected = 0
    for sid in np.unique(src_f):
        m = src_f == sid
        yy = y_f[m]
        if int(np.sum(yy == 1)) == 0:
            continue
        event_cnt += 1
        ord_sid = ord_f[m]
        local_order = np.argsort(ord_sid, kind="mergesort")
        yy_s = yy[local_order]
        ss_s = score_f[m][local_order]
        onset = int(np.where(yy_s == 1)[0][0])
        post_hit = np.where((np.arange(len(ss_s)) >= onset) & (ss_s > threshold))[0]
        if len(post_hit):
            detected += 1
            delays.append(float(int(post_hit[0]) - onset))
    d = np.asarray(delays, dtype=float)
    return {
        "detect_rate_post": float(detected / event_cnt) if event_cnt > 0 else np.nan,
        "delay_first_post_windows": float(np.mean(d)) if len(d) else np.nan,
        "event_count_post": float(event_cnt),
    }


def _active_axis_stat(active_axes: np.ndarray) -> float:
    finite = np.isfinite(active_axes)
    if not np.any(finite):
        return np.nan
    return float(np.mean(active_axes[finite].astype(float)))


def _combine_topk_rows(mat: np.ndarray, k: int) -> np.ndarray:
    out = np.full(mat.shape[0], np.nan, dtype=float)
    for i in range(mat.shape[0]):
        vals = mat[i, :]
        vals = vals[np.isfinite(vals)]
        if len(vals) == 0:
            continue
        kk = min(max(1, k), len(vals))
        out[i] = float(np.mean(np.sort(vals)[-kk:]))
    return out


def _combine_weighted_rows(mat: np.ndarray, weights: np.ndarray) -> np.ndarray:
    out = np.full(mat.shape[0], np.nan, dtype=float)
    for i in range(mat.shape[0]):
        vals = mat[i, :]
        valid = np.isfinite(vals) & np.isfinite(weights) & (weights > 0)
        if not np.any(valid):
            continue
        out[i] = float(np.average(vals[valid], weights=weights[valid]))
    return out


def _baseline_noae_weights(baseline_metrics: pd.DataFrame) -> dict[str, float]:
    like_to_raw = {k: v for k, v in RAW_SCORE_MAP.items() if v in NOAE_RAW_COLS}
    w = {}
    for like_col, raw_col in like_to_raw.items():
        hit = baseline_metrics[baseline_metrics["score"] == like_col]
        if hit.empty:
            w[raw_col] = 0.0
            continue
        score = float(hit.iloc[0]["roc_auc"]) if np.isfinite(hit.iloc[0]["roc_auc"]) else np.nan
        w[raw_col] = max(score - 0.5, 0.0) if np.isfinite(score) else 0.0
    total = sum(w.values())
    if total <= 0:
        return {raw_col: 1.0 / len(NOAE_RAW_COLS) for raw_col in NOAE_RAW_COLS}
    return {raw_col: w.get(raw_col, 0.0) / total for raw_col in NOAE_RAW_COLS}


def _build_ensemble2_variants(df: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    out = df.copy()
    top2_cols = [f"z_{c}" for c in NOAE_RAW_COLS]
    out["ensemble_top2_raw"] = np.nan
    out["ensemble_top2_active_axes"] = np.nan
    out["ensemble_weighted_noae_raw"] = np.nan
    out["ensemble_weighted_noae_active_axes"] = np.nan

    if "source_id" in out.columns:
        group_keys = out["source_id"].fillna("src").astype(str)
    else:
        group_keys = pd.Series(["src"] * len(out), index=out.index, dtype=str)

    for _, idx in group_keys.groupby(group_keys).groups.items():
        g = out.loc[idx].copy()
        z_mat = np.column_stack([pd.to_numeric(g.get(c, pd.Series(np.nan, index=g.index)), errors="coerce").to_numpy(dtype=float) for c in top2_cols])
        active_count = np.sum(np.isfinite(z_mat), axis=1).astype(float)
        out.loc[g.index, "ensemble_top2_active_axes"] = active_count
        out.loc[g.index, "ensemble_weighted_noae_active_axes"] = active_count
        out.loc[g.index, "ensemble_top2_raw"] = _combine_topk_rows(z_mat, k=2)
        w_vec = np.asarray([weights.get(c, 0.0) for c in NOAE_RAW_COLS], dtype=float)
        out.loc[g.index, "ensemble_weighted_noae_raw"] = _combine_weighted_rows(z_mat, w_vec)
    return out


def _mode_suffix(series: pd.Series) -> pd.Series:
    s = series.fillna("").astype(str)
    out = pd.Series("", index=series.index, dtype=str)
    out[s.str.endswith("L")] = "L"
    out[s.str.endswith("M")] = "M"
    return out


def _mode_specific_noae_weights(df: pd.DataFrame, metric: str = "roc_auc") -> dict[str, dict[str, float]]:
    y_all = _derive_positive_label(df)
    modes = _mode_suffix(df.get("fault_type", pd.Series("", index=df.index)))
    out: dict[str, dict[str, float]] = {}
    for mode in ["L", "M"]:
        mode_mask = modes.eq(mode).to_numpy()
        raw_weights: dict[str, float] = {}
        eligible: list[str] = []
        for raw_col in NOAE_RAW_COLS:
            z_col = f"z_{raw_col}"
            s = pd.to_numeric(df.get(z_col, pd.Series(np.nan, index=df.index)), errors="coerce").to_numpy(dtype=float)
            mask = mode_mask & np.isfinite(s) & np.isfinite(y_all)
            yy = y_all[mask]
            ss = s[mask]
            deg = _score_degeneracy(ss)
            if len(ss) == 0 or bool(deg["degenerate_score"]):
                raw_weights[raw_col] = 0.0
                continue
            eligible.append(raw_col)
            stat = _roc_auc_rank(yy, ss) if metric == "roc_auc" else _average_precision(yy, ss)
            raw_weights[raw_col] = max(float(stat) - 0.5, 0.0) if np.isfinite(stat) else 0.0
        total = sum(raw_weights.values())
        if total > 0:
            out[mode] = {k: raw_weights.get(k, 0.0) / total for k in NOAE_RAW_COLS}
        elif eligible:
            out[mode] = {k: (1.0 / len(eligible) if k in eligible else 0.0) for k in NOAE_RAW_COLS}
        else:
            out[mode] = {k: 0.0 for k in NOAE_RAW_COLS}
    return out


def _build_ensemble3_variants(df: pd.DataFrame, mode_weights: dict[str, dict[str, float]]) -> pd.DataFrame:
    out = df.copy()
    mode = _mode_suffix(out.get("fault_type", pd.Series("", index=out.index)))
    out["ensemble_mode_hybrid_raw"] = np.nan
    out["ensemble_mode_hybrid_active_axes"] = np.nan
    out["ensemble_mode_weighted_raw"] = np.nan
    out["ensemble_mode_weighted_active_axes"] = np.nan

    top2 = pd.to_numeric(out.get("ensemble_top2_raw", pd.Series(np.nan, index=out.index)), errors="coerce")
    top2_active = pd.to_numeric(out.get("ensemble_top2_active_axes", pd.Series(np.nan, index=out.index)), errors="coerce")
    weighted = pd.to_numeric(out.get("ensemble_weighted_noae_raw", pd.Series(np.nan, index=out.index)), errors="coerce")
    weighted_active = pd.to_numeric(out.get("ensemble_weighted_noae_active_axes", pd.Series(np.nan, index=out.index)), errors="coerce")

    l_mask = mode.eq("L")
    m_mask = mode.eq("M")
    out.loc[l_mask, "ensemble_mode_hybrid_raw"] = weighted[l_mask]
    out.loc[m_mask, "ensemble_mode_hybrid_raw"] = top2[m_mask]
    out.loc[l_mask, "ensemble_mode_hybrid_active_axes"] = weighted_active[l_mask]
    out.loc[m_mask, "ensemble_mode_hybrid_active_axes"] = top2_active[m_mask]

    z_cols = [f"z_{c}" for c in NOAE_RAW_COLS]
    z_mat = np.column_stack([pd.to_numeric(out.get(c, pd.Series(np.nan, index=out.index)), errors="coerce").to_numpy(dtype=float) for c in z_cols])
    active = np.zeros(len(out), dtype=float)
    ens = np.full(len(out), np.nan, dtype=float)
    for mode_name in ["L", "M"]:
        mask = mode.eq(mode_name).to_numpy()
        if not np.any(mask):
            continue
        w_vec = np.asarray([mode_weights.get(mode_name, {}).get(raw_col, 0.0) for raw_col in NOAE_RAW_COLS], dtype=float)
        sub = z_mat[mask, :]
        active_sub = np.sum(np.isfinite(sub) & (w_vec[None, :] > 0), axis=1).astype(float)
        ens_sub = _combine_weighted_rows(sub, w_vec)
        active[mask] = active_sub
        ens[mask] = ens_sub
    out["ensemble_mode_weighted_raw"] = ens
    out["ensemble_mode_weighted_active_axes"] = active
    return out


def _evaluate_named_ensemble_overall(df: pd.DataFrame, score_col: str, active_col: str) -> pd.DataFrame:
    y = _derive_positive_label(df)
    score = pd.to_numeric(df.get(score_col, pd.Series(np.nan, index=df.index)), errors="coerce").to_numpy(dtype=float)
    active_axes = pd.to_numeric(df.get(active_col, pd.Series(np.nan, index=df.index)), errors="coerce").to_numpy(dtype=float)
    finite = np.isfinite(score) & np.isfinite(y)
    yy = y[finite]
    ss = score[finite]
    deg = _score_degeneracy(ss)
    if len(ss) == 0:
        return pd.DataFrame(
            [
                {
                    "score": score_col,
                    "n_valid": 0,
                    "n_pos": 0,
                    "base_rate": np.nan,
                    "active_axis_count": np.nan,
                    "n_unique_score": deg["n_unique_score"],
                    "score_span": deg["score_span"],
                    "degenerate_score": 1.0,
                    "roc_auc": np.nan,
                    "ap": np.nan,
                    "threshold_fpr1": np.nan,
                    "actual_fpr_fpr1": np.nan,
                    "precision_fpr1": np.nan,
                    "recall_fpr1": np.nan,
                    "f1_fpr1": np.nan,
                }
            ]
        )
    if bool(deg["degenerate_score"]):
        threshold_fpr1 = np.nan
        actual_fpr_fpr1 = np.nan
        binary = {"precision_fpr1": np.nan, "recall_fpr1": np.nan, "f1_fpr1": np.nan}
    else:
        fpr_rule = _threshold_at_fpr(ss, yy, fpr=FPR1)
        threshold_fpr1 = fpr_rule["threshold_fpr1"]
        actual_fpr_fpr1 = fpr_rule["actual_fpr_fpr1"]
        binary = _binary_metrics_at_threshold(yy, ss, threshold_fpr1)
    return pd.DataFrame(
        [
            {
                "score": score_col,
                "n_valid": int(len(yy)),
                "n_pos": int(np.sum(yy == 1)),
                "base_rate": float(np.mean(yy == 1)) if len(yy) else np.nan,
                "active_axis_count": _active_axis_stat(active_axes),
                "n_unique_score": deg["n_unique_score"],
                "score_span": deg["score_span"],
                "degenerate_score": deg["degenerate_score"],
                "roc_auc": _roc_auc_rank(yy, ss),
                "ap": _average_precision(yy, ss),
                "threshold_fpr1": threshold_fpr1,
                "actual_fpr_fpr1": actual_fpr_fpr1,
                "precision_fpr1": binary["precision_fpr1"],
                "recall_fpr1": binary["recall_fpr1"],
                "f1_fpr1": binary["f1_fpr1"],
            }
        ]
    )


def _evaluate_named_ensemble_by_type(df: pd.DataFrame, score_col: str, active_col: str) -> pd.DataFrame:
    if "fault_type" not in df.columns:
        return pd.DataFrame(columns=["fault_type", "sid", "score", "n_windows", "active_axis_count", "n_unique_score", "score_span", "degenerate_score", "roc_auc", "ap", "threshold_fpr1", "actual_fpr_fpr1", "precision_fpr1", "recall_fpr1", "f1_fpr1"])
    rows: list[dict[str, Any]] = []
    for fault_type, grp in df.groupby("fault_type", dropna=False):
        g = grp.copy()
        sid_val = pd.to_numeric(g.get("fault_sid"), errors="coerce").dropna()
        sid_num = int(sid_val.iloc[0]) if not sid_val.empty else np.nan
        y = _derive_positive_label(g)
        score = pd.to_numeric(g.get(score_col, pd.Series(np.nan, index=g.index)), errors="coerce").to_numpy(dtype=float)
        active_axes = pd.to_numeric(g.get(active_col, pd.Series(np.nan, index=g.index)), errors="coerce").to_numpy(dtype=float)
        finite = np.isfinite(score) & np.isfinite(y)
        yy = y[finite]
        ss = score[finite]
        deg = _score_degeneracy(ss)
        if len(ss) == 0 or bool(deg["degenerate_score"]):
            threshold_fpr1 = np.nan
            actual_fpr_fpr1 = np.nan
            binary = {"precision_fpr1": np.nan, "recall_fpr1": np.nan, "f1_fpr1": np.nan}
            roc_auc = np.nan
            ap = np.nan
        else:
            fpr_rule = _threshold_at_fpr(ss, yy, fpr=FPR1)
            threshold_fpr1 = fpr_rule["threshold_fpr1"]
            actual_fpr_fpr1 = fpr_rule["actual_fpr_fpr1"]
            binary = _binary_metrics_at_threshold(yy, ss, threshold_fpr1)
            roc_auc = _roc_auc_rank(yy, ss)
            ap = _average_precision(yy, ss)
        rows.append(
            {
                "fault_type": "unknown" if pd.isna(fault_type) or str(fault_type) == "" else str(fault_type),
                "sid": sid_num,
                "score": score_col,
                "n_windows": int(len(yy)),
                "active_axis_count": _active_axis_stat(active_axes),
                "n_unique_score": deg["n_unique_score"],
                "score_span": deg["score_span"],
                "degenerate_score": deg["degenerate_score"],
                "roc_auc": roc_auc,
                "ap": ap,
                "threshold_fpr1": threshold_fpr1,
                "actual_fpr_fpr1": actual_fpr_fpr1,
                "precision_fpr1": binary["precision_fpr1"],
                "recall_fpr1": binary["recall_fpr1"],
                "f1_fpr1": binary["f1_fpr1"],
            }
        )
    return pd.DataFrame(rows).sort_values(["fault_type"], ascending=True, na_position="last").reset_index(drop=True)


def _evaluate_ensemble_overall(df: pd.DataFrame) -> pd.DataFrame:
    return _evaluate_named_ensemble_overall(df, "ensemble_raw", "ensemble_active_axes")


def _evaluate_ensemble_by_type(df: pd.DataFrame) -> pd.DataFrame:
    return _evaluate_named_ensemble_by_type(df, "ensemble_raw", "ensemble_active_axes")


def _write_empty_bytype(out_csv: pathlib.Path, out_md: pathlib.Path) -> pd.DataFrame:
    cols = [
        "fault_type",
        "sid",
        "score",
        "n_windows",
        "split",
        "n_unique_score",
        "score_span",
        "degenerate_score",
        "auc",
        "roc_auc",
        "ap",
        "precision@K",
        "k_used",
        "threshold_fpr1",
        "actual_fpr_fpr1",
        "precision_fpr1",
        "recall_fpr1",
        "f1_fpr1",
        "detect_rate_post",
        "delay_first_post_windows",
    ]
    empty = pd.DataFrame(columns=cols)
    empty.to_csv(out_csv, index=False, encoding="utf-8-sig")
    lines = [
        "# EXTERNAL GPVS fault_type별 축 반응 요약",
        "",
        "- input: `data/gpvs/out/gpvs_window_scores.csv`",
        f"- output(csv): `{out_csv}`",
        "- threshold rule: pre-fault healthy windows 기준 FPR 1% threshold",
        "",
        "_(no rows)_",
        "",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return empty


def _evaluate_by_type(
    df: pd.DataFrame,
    source: np.ndarray,
    order: np.ndarray,
    out_csv: pathlib.Path,
    out_md: pathlib.Path,
    k: int,
) -> pd.DataFrame:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    if "fault_type" not in df.columns:
        return _write_empty_bytype(out_csv, out_md)

    rows: list[dict[str, Any]] = []
    for fault_type, grp in df.groupby("fault_type", dropna=False):
        g = grp.copy()
        g_fault_type = "unknown" if pd.isna(fault_type) or str(fault_type) == "" else str(fault_type)
        sid_val = pd.to_numeric(g.get("fault_sid"), errors="coerce").dropna()
        sid_num = int(sid_val.iloc[0]) if not sid_val.empty else np.nan

        gy = _derive_positive_label(g)
        gsource = g.get("source_id", pd.Series([g_fault_type] * len(g), index=g.index)).astype(str).to_numpy()
        gwi = pd.to_numeric(g.get("window_idx"), errors="coerce")
        gfallback = pd.Series(np.arange(len(g), dtype=float), index=g.index)
        gorder = gwi.fillna(gfallback).to_numpy(dtype=float)

        if int(np.sum(gy == 1)) == 0:
            for sc in SCORE_COLS:
                if sc not in g.columns:
                    continue
                rows.append(
                    {
                        "fault_type": g_fault_type,
                        "sid": sid_num,
                        "score": sc,
                        "n_windows": int(len(g)),
                        "split": np.nan,
                        "n_unique_score": 0.0,
                        "score_span": np.nan,
                        "degenerate_score": 1.0,
                        "auc": np.nan,
                        "roc_auc": np.nan,
                        "ap": np.nan,
                        "precision@K": 0.0,
                        "k_used": int(min(max(1, k), len(g))) if len(g) else 0,
                        "threshold_fpr1": np.nan,
                        "actual_fpr_fpr1": np.nan,
                        "precision_fpr1": np.nan,
                        "recall_fpr1": np.nan,
                        "f1_fpr1": np.nan,
                        "detect_rate_post": np.nan,
                        "delay_first_post_windows": np.nan,
                    }
                )
            continue

        for sc in SCORE_COLS:
            if sc not in g.columns:
                continue
            rank_s = pd.to_numeric(g[sc], errors="coerce").to_numpy(dtype=float)
            raw_col = RAW_SCORE_MAP.get(sc, "")
            raw_s = pd.to_numeric(g.get(raw_col), errors="coerce").to_numpy(dtype=float) if raw_col in g.columns else np.full(len(g), np.nan)

            m_rank = np.isfinite(rank_s) & np.isfinite(gy)
            yy = gy[m_rank]
            ss = rank_s[m_rank]
            if len(yy) == 0:
                continue
            roc_auc = _roc_auc_rank(yy, ss)
            ap = _average_precision(yy, ss)
            p_at_k, k_used = _precision_at_k(yy, ss, k)

            m_raw = np.isfinite(raw_s) & np.isfinite(gy)
            yy_raw = gy[m_raw]
            ss_raw = raw_s[m_raw]
            deg = _score_degeneracy(ss_raw)
            if len(yy_raw) == 0 or bool(deg["degenerate_score"]):
                threshold_fpr1 = np.nan
                actual_fpr_fpr1 = np.nan
                binary = {"precision_fpr1": np.nan, "recall_fpr1": np.nan, "f1_fpr1": np.nan}
                detect = {"detect_rate_post": np.nan, "delay_first_post_windows": np.nan}
            else:
                fpr_rule = _threshold_at_fpr(ss_raw, yy_raw, fpr=FPR1)
                threshold_fpr1 = fpr_rule["threshold_fpr1"]
                actual_fpr_fpr1 = fpr_rule["actual_fpr_fpr1"]
                binary = _binary_metrics_at_threshold(yy_raw, ss_raw, threshold_fpr1)
                detect = _post_detection_summary(ss_raw, yy_raw, gsource[m_raw], gorder[m_raw], threshold_fpr1)
            rows.append(
                {
                    "fault_type": g_fault_type,
                    "sid": sid_num,
                    "score": sc,
                    "n_windows": int(len(yy)),
                    "split": "pre_vs_post" if int(np.sum(yy == 1)) > 0 else np.nan,
                    "n_unique_score": deg["n_unique_score"],
                    "score_span": deg["score_span"],
                    "degenerate_score": deg["degenerate_score"],
                    "auc": roc_auc,
                    "roc_auc": roc_auc,
                    "ap": ap,
                    "precision@K": p_at_k,
                    "k_used": int(k_used),
                    "threshold_fpr1": threshold_fpr1,
                    "actual_fpr_fpr1": actual_fpr_fpr1,
                    "precision_fpr1": binary["precision_fpr1"],
                    "recall_fpr1": binary["recall_fpr1"],
                    "f1_fpr1": binary["f1_fpr1"],
                    "detect_rate_post": detect["detect_rate_post"],
                    "delay_first_post_windows": detect["delay_first_post_windows"],
                }
            )

    metrics = pd.DataFrame(rows)
    if metrics.empty:
        metrics = _write_empty_bytype(out_csv, out_md)
        return metrics

    metrics = metrics.sort_values(["fault_type", "ap", "roc_auc"], ascending=[True, False, False], na_position="last").reset_index(drop=True)
    metrics.to_csv(out_csv, index=False, encoding="utf-8-sig")

    top_rows = []
    for fault_type, grp in metrics[metrics["sid"] != 0].groupby("fault_type", dropna=False):
        g = grp.sort_values(["ap", "roc_auc"], ascending=False, na_position="last").reset_index(drop=True)
        top1 = g.iloc[0] if len(g) >= 1 else None
        top2 = g.iloc[1] if len(g) >= 2 else None
        top_rows.append(
            {
                "fault_type": fault_type,
                "top1(AP)": f"{top1['score']} ({top1['ap']:.3f})" if top1 is not None and np.isfinite(top1["ap"]) else "",
                "top2(AP)": f"{top2['score']} ({top2['ap']:.3f})" if top2 is not None and np.isfinite(top2["ap"]) else "",
                "n_windows": int(top1["n_windows"]) if top1 is not None else np.nan,
                "detect_rate_post(top1)": float(top1["detect_rate_post"]) if top1 is not None else np.nan,
                "delay_first_post(top1)": float(top1["delay_first_post_windows"]) if top1 is not None else np.nan,
            }
        )
    top_df = pd.DataFrame(top_rows)
    deg_df = metrics[metrics["degenerate_score"] == 1.0][["fault_type", "score", "n_unique_score", "score_span"]].copy()
    sat_df = metrics[(metrics["degenerate_score"] == 0.0) & metrics["actual_fpr_fpr1"].fillna(0.0).lt(FPR1 * 0.5)][["fault_type", "score", "actual_fpr_fpr1"]].copy()

    lines = []
    lines.append("# EXTERNAL GPVS fault_type별 축 반응 요약")
    lines.append("")
    lines.append("- input: `data/gpvs/out/gpvs_window_scores.csv`")
    lines.append(f"- output(csv): `{out_csv}`")
    lines.append("- threshold rule: 각 fault_type의 pre-fault healthy windows에서 `score > tau`가 되도록 잡은 FPR 1% threshold")
    lines.append("")
    lines.append("## fault_type별 AP Top-2 (F0 제외)")
    lines.append("")
    lines.append(_to_md_table(top_df))
    lines.append("")
    lines.append("## 해석(회의용)")
    lines.append("")
    lines.append("- 각 fault_type(파일) 안에서 `전반부=pre-fault`, `후반부=post-fault`로 라벨을 재구성해 AP/ROC-AUC/F1@FPR1를 계산했습니다.")
    lines.append("- AP와 ROC-AUC는 기존 `*_like` 점수로 계산하고, F1 계열은 raw score(`*_raw`) 기준으로 다시 계산했습니다.")
    lines.append("- `threshold_fpr1`은 해당 fault_type의 pre-fault healthy windows에서 `score > tau` 규칙으로 actual FPR이 1% 이하가 되도록 잡은 임계값입니다.")
    lines.append("- `detect_rate_post`는 post-fault 구간에서 threshold를 한 번이라도 넘긴 파일 비율입니다.")
    lines.append("- `delay_first_post_windows`는 post-fault 시작 이후 첫 threshold 초과까지의 평균 지연(윈도우)입니다.")
    lines.append("- `degenerate_score=1`이면 raw score collapse로 보고 F1 계열은 해석 제외합니다.")
    lines.append("- `actual_fpr_fpr1`이 매우 낮은 비퇴화 row는 threshold saturation 가능성이 있으므로 F1보다 AP/ROC-AUC를 우선 해석합니다.")
    if not deg_df.empty:
        lines.append("")
        lines.append("## degenerate score rows")
        lines.append(_to_md_table(deg_df))
    if not sat_df.empty:
        lines.append("")
        lines.append("## saturation-prone rows")
        lines.append(_to_md_table(sat_df))
    lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return metrics


def evaluate(
    scores_csv: pathlib.Path,
    out_csv: pathlib.Path,
    out_md: pathlib.Path,
    out_bytype_csv: pathlib.Path,
    out_bytype_md: pathlib.Path,
    k: int,
    thr_q: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pathlib.Path, pathlib.Path, pathlib.Path, pathlib.Path]:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_bytype_csv.parent.mkdir(parents=True, exist_ok=True)
    out_bytype_md.parent.mkdir(parents=True, exist_ok=True)

    metrics_cols = [
        "score",
        "n_valid",
        "n_pos",
        "base_rate",
        "n_unique_score",
        "score_span",
        "degenerate_score",
        "auc",
        "roc_auc",
        "ap",
        "precision_at_k",
        "k_used",
        "thr_q",
        "thr_val",
        "threshold_fpr1",
        "actual_fpr_fpr1",
        "precision_fpr1",
        "recall_fpr1",
        "f1_fpr1",
        "event_count",
        "detect_rate",
        "delay_mean_windows",
        "delay_median_windows",
        "delay_p25_windows",
        "delay_p75_windows",
    ]

    missing_note = ""
    if not scores_csv.exists():
        df = pd.DataFrame(
            columns=[
                "sample_id",
                "source_id",
                "window_idx",
                "t0",
                "t1",
                "label_fault",
                "fault_type",
                "v_pv_mean",
                "i_pv_mean",
                "p_pv_mean",
                "level_drop_raw",
                "v_drop_raw",
                "hs_raw",
                "dtw_raw",
                "ae_raw",
                "level_drop_like",
                "v_drop_like",
                "hs_like",
                "dtw_like",
                "ae_like",
            ]
        )
        missing_note = f"input file not found: `{scores_csv}`"
    else:
        df = pd.read_csv(scores_csv)

    if df.empty:
        metrics = pd.DataFrame(columns=metrics_cols)
        metrics.to_csv(out_csv, index=False, encoding="utf-8-sig")
        bytype_metrics = _write_empty_bytype(out_bytype_csv, out_bytype_md)
        lines = []
        lines.append("# EXTERNAL GPVS ONEPAGE")
        lines.append("")
        lines.append("## 데이터 요약")
        lines.append("- n_samples: 0")
        lines.append("- n_positive: 0")
        lines.append("- base_rate: ")
        if missing_note:
            lines.append(f"- note: {missing_note}")
        lines.append("- note: input is empty or raw GPVS files are not ingested yet.")
        lines.append("")
        lines.append("### fault_type 분포")
        lines.append("_(no rows)_")
        lines.append("")
        lines.append("## 점수별 AUC/AP/precision@K")
        lines.append("_(no rows)_")
        lines.append("")
        lines.append("## 축 반응 해석")
        lines.append("- 전기/형상/변동성 축 비교를 위해서는 GPVS raw 파일 ingest 후 재실행이 필요하다.")
        lines.append("- 현재는 샘플이 없어 지표를 산출하지 못했다.")
        lines.append("- ingest 완료 후 동일 스크립트로 AUC/AP/prec@K/delay가 자동 계산된다.")
        lines.append("- AE/DTW/HS/level/vdrop 축 분리 평가는 비어 있는 상태다.")
        lines.append("- raw 파일 위치 확인: `data/gpvs/_download/GPVS_Faults`")
        lines.append("")
        lines.append("## 한계")
        lines.append("- GPVS 벤치마크는 윈도우 단위 라벨 기준이며, 일 단위 운영 파이프라인의 시간 스케일과 다르다.")
        lines.append("- fault 타입/라벨 정의가 현장 운영 라벨과 다를 수 있으므로 도메인 맵핑 검증이 추가로 필요하다.")
        lines.append("")
        lines.append("## 실행 커맨드")
        lines.append("- `python research/prognostics/ingest_gpvs_faults.py`")
        lines.append("- `python research/prognostics/external_eval_gpvs.py`")
        lines.append("")
        out_md.write_text("\n".join(lines), encoding="utf-8")
        return metrics, bytype_metrics, out_csv, out_md, out_bytype_csv, out_bytype_md

    y = _derive_positive_label(df)
    if int(np.sum(y == 1)) == 0:
        msg = (
            "라벨이 0개라 평가 불가: positive windows/files not found "
            "(checked priority: is_fault_window -> is_fault_file -> fault_sid>0)"
        )
        raise RuntimeError(msg)
    source = df.get("source_id", pd.Series(["src"] * len(df))).astype(str).to_numpy()
    wi = pd.to_numeric(df.get("window_idx"), errors="coerce")
    fallback = pd.Series(np.arange(len(df), dtype=float), index=df.index)
    order = wi.fillna(fallback).to_numpy(dtype=float)
    base_rate = float(np.mean(y == 1)) if len(y) else np.nan

    rows = []
    excluded = []
    for sc in SCORE_COLS:
        if sc not in df.columns:
            excluded.append(sc)
            continue
        rank_s = pd.to_numeric(df[sc], errors="coerce").to_numpy(dtype=float)
        raw_col = RAW_SCORE_MAP.get(sc, "")
        raw_s = pd.to_numeric(df.get(raw_col), errors="coerce").to_numpy(dtype=float) if raw_col in df.columns else np.full(len(df), np.nan)

        m = np.isfinite(rank_s) & np.isfinite(y)
        yy = y[m]
        ss = rank_s[m]
        if len(yy) == 0:
            excluded.append(f"{sc}(all_nan)")
            continue
        auc = _roc_auc_rank(yy, ss)
        ap = _average_precision(yy, ss)
        p_at_k, k_used = _precision_at_k(yy, ss, k)

        m_raw = np.isfinite(raw_s) & np.isfinite(y)
        yy_raw = y[m_raw]
        ss_raw = raw_s[m_raw]
        deg = _score_degeneracy(ss_raw)
        if len(yy_raw) == 0 or bool(deg["degenerate_score"]):
            threshold_fpr1 = np.nan
            actual_fpr_fpr1 = np.nan
            binary = {"precision_fpr1": np.nan, "recall_fpr1": np.nan, "f1_fpr1": np.nan}
        else:
            fpr_rule = _threshold_at_fpr(ss_raw, yy_raw, fpr=FPR1)
            threshold_fpr1 = fpr_rule["threshold_fpr1"]
            actual_fpr_fpr1 = fpr_rule["actual_fpr_fpr1"]
            binary = _binary_metrics_at_threshold(yy_raw, ss_raw, threshold_fpr1)
        delay = _detection_delay(ss, yy, source[m], order[m], k=k, thr_q=thr_q)
        rows.append(
            {
                "score": sc,
                "n_valid": int(len(yy)),
                "n_pos": int(np.sum(yy == 1)),
                "base_rate": float(np.mean(yy == 1)) if len(yy) else np.nan,
                "n_unique_score": deg["n_unique_score"],
                "score_span": deg["score_span"],
                "degenerate_score": deg["degenerate_score"],
                "auc": auc,
                "roc_auc": auc,
                "ap": ap,
                "precision_at_k": p_at_k,
                "k_used": int(k_used),
                "thr_q": delay["thr_q"],
                "thr_val": delay["thr_val"],
                "threshold_fpr1": threshold_fpr1,
                "actual_fpr_fpr1": actual_fpr_fpr1,
                "precision_fpr1": binary["precision_fpr1"],
                "recall_fpr1": binary["recall_fpr1"],
                "f1_fpr1": binary["f1_fpr1"],
                "event_count": delay["event_count"],
                "detect_rate": delay["detect_rate"],
                "delay_mean_windows": delay["delay_mean"],
                "delay_median_windows": delay["delay_median"],
                "delay_p25_windows": delay["delay_p25"],
                "delay_p75_windows": delay["delay_p75"],
            }
        )

    metrics = pd.DataFrame(rows)
    if metrics.empty:
        metrics = pd.DataFrame(columns=metrics_cols)
    else:
        metrics = metrics.sort_values(["ap", "roc_auc"], ascending=False, na_position="last").reset_index(drop=True)
    metrics.to_csv(out_csv, index=False, encoding="utf-8-sig")
    bytype_metrics = _evaluate_by_type(df, source, order, out_bytype_csv, out_bytype_md, k)

    fault_dist = (
        df["fault_type"]
        .fillna("")
        .astype(str)
        .replace("", "unknown")
        .value_counts()
        .reset_index(name="count")
        .rename(columns={"index": "fault_type"})
        if "fault_type" in df.columns
        else pd.DataFrame(columns=["fault_type", "count"])
    )

    summary_lines = [
        "- 전기축(level_drop_like, v_drop_like)은 평균 전력/전압 저하를 반영해 fault 라벨과 직접적으로 연결된다.",
        "- 형상축(dtw_like, ae_like)은 정상 baseline 파형 대비 형태 이탈을 계량화해 고장 신호를 포착한다.",
        "- 변동성축(hs_like)은 난류/불안정 고장에서 민감하게 반응하도록 설계되었다.",
        "- 외부 벤치마크에서 축별 AUC/AP를 함께 비교하면 어떤 fault 타입에 어떤 축이 강한지 확인할 수 있다.",
        "- 단일 점수 대신 축 분리 비교를 제공해 블랙박스 리스크를 낮추고 해석 가능성을 높인다.",
    ]

    lines = []
    lines.append("# EXTERNAL GPVS ONEPAGE")
    lines.append("")
    lines.append("## 데이터 요약")
    lines.append(f"- n_samples: {len(df)}")
    lines.append(f"- n_positive: {int(np.sum(y == 1))}")
    lines.append(f"- base_rate: {base_rate:.6f}" if np.isfinite(base_rate) else "- base_rate: ")
    lines.append("")
    lines.append("### fault_type 분포")
    lines.append(_to_md_table(fault_dist))
    lines.append("")
    lines.append("## 점수별 AUC/AP/F1@FPR1/precision@K")
    lines.append("- AP와 ROC-AUC는 `*_like` 점수, F1 계열은 raw score(`*_raw`) 기준입니다.")
    lines.append("- `threshold_fpr1`은 전체 healthy windows에서 `score > tau` 규칙으로 actual FPR이 1% 이하가 되도록 잡은 threshold입니다.")
    lines.append(_to_md_table(metrics[["score", "roc_auc", "ap", "n_unique_score", "score_span", "degenerate_score", "f1_fpr1", "precision_fpr1", "recall_fpr1", "threshold_fpr1", "actual_fpr_fpr1", "precision_at_k", "k_used", "detect_rate", "delay_median_windows"]] if not metrics.empty else metrics))
    lines.append("")
    lines.append("## 축 반응 해석")
    lines.extend(summary_lines)
    if not metrics.empty and bool((metrics["degenerate_score"] == 1.0).any()):
        lines.append("- `degenerate_score=1`인 row는 raw score collapse로 보고 F1 계열 해석에서 제외해야 한다.")
    if not metrics.empty and bool(((metrics["degenerate_score"] == 0.0) & metrics["actual_fpr_fpr1"].fillna(0.0).lt(FPR1 * 0.5)).any()):
        lines.append("- `actual_fpr_fpr1`이 매우 낮으면 threshold saturation 가능성이 있으므로 F1보다 AP/ROC-AUC를 우선 해석한다.")
    lines.append("")
    lines.append("## 한계")
    lines.append("- GPVS 벤치마크는 윈도우 단위 라벨 기준이며, 일 단위 운영 파이프라인의 시간 스케일과 다르다.")
    lines.append("- 따라서 절대 임계값 이식보다 축별 상대 반응성(AUC/AP/delay) 해석에 초점을 둬야 한다.")
    lines.append("- fault 타입/라벨 정의가 현장 운영 라벨과 다를 수 있으므로 도메인 맵핑 검증이 추가로 필요하다.")
    lines.append("")
    lines.append("## 실행 커맨드")
    lines.append("- `python research/prognostics/ingest_gpvs_faults.py`")
    lines.append("- `python research/prognostics/external_eval_gpvs.py`")
    lines.append("")
    if excluded:
        lines.append("## 제외된 점수")
        for sc in excluded:
            lines.append(f"- {sc}")
        lines.append("")

    out_md.write_text("\n".join(lines), encoding="utf-8")
    return metrics, bytype_metrics, out_csv, out_md, out_bytype_csv, out_bytype_md


def evaluate_ensemble(
    scores_csv: pathlib.Path,
    out_csv: pathlib.Path,
    out_bytype_csv: pathlib.Path,
    out_md: pathlib.Path,
    baseline_metrics: pd.DataFrame,
    baseline_bytype_metrics: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pathlib.Path, pathlib.Path, pd.DataFrame]:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_bytype_csv.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    if not scores_csv.exists():
        empty_overall = _evaluate_ensemble_overall(pd.DataFrame())
        empty_bytype = _evaluate_ensemble_by_type(pd.DataFrame())
        empty_overall.to_csv(out_csv, index=False, encoding="utf-8-sig")
        empty_bytype.to_csv(out_bytype_csv, index=False, encoding="utf-8-sig")
        out_md.write_text("# EXTERNAL GPVS ENSEMBLE ONEPAGE\n\n_(input missing)_\n", encoding="utf-8")
        return empty_overall, empty_bytype, out_csv, out_md, pd.DataFrame()

    df = pd.read_csv(scores_csv)
    ens_df = _build_ensemble_frame(df)
    overall = _evaluate_ensemble_overall(ens_df)
    bytype = _evaluate_ensemble_by_type(ens_df)
    overall.to_csv(out_csv, index=False, encoding="utf-8-sig")
    bytype.to_csv(out_bytype_csv, index=False, encoding="utf-8-sig")

    best_single = baseline_metrics.sort_values(["ap", "roc_auc"], ascending=False, na_position="last").head(1).copy()
    ens_row = overall.iloc[0] if not overall.empty else None

    base_nonf0 = baseline_bytype_metrics[baseline_bytype_metrics.get("sid", pd.Series(dtype=float)).fillna(0).astype(float) > 0].copy()
    if not base_nonf0.empty:
        base_top = (
            base_nonf0.sort_values(["fault_type", "ap", "roc_auc"], ascending=[True, False, False], na_position="last")
            .groupby("fault_type", as_index=False)
            .first()[["fault_type", "ap"]]
            .rename(columns={"ap": "baseline_top_ap"})
        )
    else:
        base_top = pd.DataFrame(columns=["fault_type", "baseline_top_ap"])
    ens_nonf0 = bytype[bytype["sid"].fillna(0).astype(float) > 0][["fault_type", "ap"]].rename(columns={"ap": "ensemble_ap"})
    cmp = ens_nonf0.merge(base_top, on="fault_type", how="left")
    improved = cmp[(cmp["ensemble_ap"] > cmp["baseline_top_ap"]) & np.isfinite(cmp["ensemble_ap"]) & np.isfinite(cmp["baseline_top_ap"])].copy()

    deg_df = bytype[bytype["degenerate_score"] == 1.0][["fault_type", "active_axis_count", "n_unique_score", "score_span"]].copy()
    sat_df = bytype[(bytype["degenerate_score"] == 0.0) & bytype["actual_fpr_fpr1"].fillna(0.0).lt(FPR1 * 0.5)][["fault_type", "actual_fpr_fpr1", "ap", "roc_auc", "f1_fpr1"]].copy()

    lines = []
    lines.append("# EXTERNAL GPVS ENSEMBLE ONEPAGE")
    lines.append("")
    lines.append("## ensemble 생성 규칙")
    lines.append("- source/file 단위 pre-half normal 구간에서 각 raw 축의 median, MAD를 계산해 robust z-score를 만들었습니다.")
    lines.append("- MAD=0 또는 pre-half `n_unique<=1`인 축은 degenerate로 보고 ensemble에서 제외했습니다.")
    lines.append("- raw 방향은 같은 축의 `*_like`와의 상관 부호로 맞춰 `higher = more faulty`로 통일했습니다.")
    lines.append("- `ensemble_raw`는 살아남은 축 z-score 평균이고, `ensemble_active_axes`는 사용된 축 개수입니다.")
    lines.append("")
    lines.append("## overall 비교")
    if not best_single.empty and ens_row is not None:
        lines.append("| model | score | roc_auc | ap | f1_fpr1 | active_axis_count |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        b = best_single.iloc[0]
        lines.append(f"| baseline_best_single | {b['score']} | {_fmt(b['roc_auc'])} | {_fmt(b['ap'])} | {_fmt(b['f1_fpr1'])} | 1 |")
        lines.append(f"| ensemble | ensemble_raw | {_fmt(ens_row['roc_auc'])} | {_fmt(ens_row['ap'])} | {_fmt(ens_row['f1_fpr1'])} | {_fmt(ens_row['active_axis_count'])} |")
        if np.isfinite(b["ap"]) and np.isfinite(ens_row["ap"]):
            lines.append(f"- overall AP delta (ensemble - best single): {ens_row['ap'] - b['ap']:.6f}")
        if np.isfinite(b["roc_auc"]) and np.isfinite(ens_row["roc_auc"]):
            lines.append(f"- overall ROC-AUC delta (ensemble - best single): {ens_row['roc_auc'] - b['roc_auc']:.6f}")
    else:
        lines.append("_(comparison unavailable)_")
    lines.append("")
    lines.append("## by-type 비교")
    lines.append(f"- ensemble AP가 baseline top1보다 좋아진 fault_type 수: {len(improved)}")
    if not improved.empty:
        lines.append(_to_md_table(improved.sort_values("fault_type")))
    else:
        lines.append("_(no improvements)_")
    lines.append("")
    lines.append("## ensemble by-type metrics")
    lines.append(_to_md_table(bytype[["fault_type", "active_axis_count", "roc_auc", "ap", "threshold_fpr1", "actual_fpr_fpr1", "f1_fpr1"]]))
    lines.append("")
    lines.append("## 해석 메모")
    lines.append("- degenerate row는 score collapse로 보고 F1 해석에서 제외합니다.")
    lines.append("- `actual_fpr_fpr1`이 매우 낮은 row는 threshold saturation 가능성이 있어 F1보다 AP/ROC-AUC를 우선 해석합니다.")
    if not deg_df.empty:
        lines.append("")
        lines.append("### degenerate rows")
        lines.append(_to_md_table(deg_df))
    if not sat_df.empty:
        lines.append("")
        lines.append("### saturation-prone rows")
        lines.append(_to_md_table(sat_df))
    lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return overall, bytype, out_csv, out_md, cmp


def evaluate_ensemble2(
    scores_csv: pathlib.Path,
    out_csv: pathlib.Path,
    out_bytype_csv: pathlib.Path,
    out_md: pathlib.Path,
    baseline_metrics: pd.DataFrame,
    baseline_bytype_metrics: pd.DataFrame,
    ensemble_raw_metrics: pd.DataFrame,
    ensemble_raw_bytype: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pathlib.Path, pathlib.Path]:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_bytype_csv.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    if not scores_csv.exists():
        empty = pd.DataFrame(columns=["score", "n_valid", "n_pos", "base_rate", "active_axis_count", "n_unique_score", "score_span", "degenerate_score", "roc_auc", "ap", "threshold_fpr1", "actual_fpr_fpr1", "precision_fpr1", "recall_fpr1", "f1_fpr1"])
        empty.to_csv(out_csv, index=False, encoding="utf-8-sig")
        pd.DataFrame(columns=["fault_type", "sid", "score", "n_windows", "active_axis_count", "n_unique_score", "score_span", "degenerate_score", "roc_auc", "ap", "threshold_fpr1", "actual_fpr_fpr1", "precision_fpr1", "recall_fpr1", "f1_fpr1"]).to_csv(out_bytype_csv, index=False, encoding="utf-8-sig")
        out_md.write_text("# EXTERNAL GPVS ENSEMBLE2 ONEPAGE\n\n_(input missing)_\n", encoding="utf-8")
        return empty, pd.DataFrame(), out_csv, out_md

    df = pd.read_csv(scores_csv)
    ens_df = _build_ensemble_frame(df)
    weights = _baseline_noae_weights(baseline_metrics)
    ens_df = _build_ensemble2_variants(ens_df, weights)

    overall_rows = [
        _evaluate_named_ensemble_overall(ens_df, "ensemble_raw", "ensemble_active_axes"),
        _evaluate_named_ensemble_overall(ens_df, "ensemble_top2_raw", "ensemble_top2_active_axes"),
        _evaluate_named_ensemble_overall(ens_df, "ensemble_weighted_noae_raw", "ensemble_weighted_noae_active_axes"),
    ]
    overall = pd.concat(overall_rows, ignore_index=True)
    overall.to_csv(out_csv, index=False, encoding="utf-8-sig")

    bytype_rows = [
        _evaluate_named_ensemble_by_type(ens_df, "ensemble_raw", "ensemble_active_axes"),
        _evaluate_named_ensemble_by_type(ens_df, "ensemble_top2_raw", "ensemble_top2_active_axes"),
        _evaluate_named_ensemble_by_type(ens_df, "ensemble_weighted_noae_raw", "ensemble_weighted_noae_active_axes"),
    ]
    bytype = pd.concat(bytype_rows, ignore_index=True)
    bytype.to_csv(out_bytype_csv, index=False, encoding="utf-8-sig")

    baseline_best = baseline_metrics.sort_values(["ap", "roc_auc"], ascending=False, na_position="last").head(1).copy()
    compare_models = [
        ("baseline_best_single", baseline_best.iloc[0]["score"] if not baseline_best.empty else "", float(baseline_best.iloc[0]["roc_auc"]) if not baseline_best.empty else np.nan, float(baseline_best.iloc[0]["ap"]) if not baseline_best.empty else np.nan, float(baseline_best.iloc[0]["f1_fpr1"]) if not baseline_best.empty else np.nan, 1.0 if not baseline_best.empty else np.nan),
    ]
    for score_name in ["ensemble_raw", "ensemble_top2_raw", "ensemble_weighted_noae_raw"]:
        hit = overall[overall["score"] == score_name]
        if hit.empty:
            compare_models.append((score_name, score_name, np.nan, np.nan, np.nan, np.nan))
        else:
            r = hit.iloc[0]
            compare_models.append((score_name, score_name, float(r["roc_auc"]), float(r["ap"]), float(r["f1_fpr1"]), float(r["active_axis_count"])))
    compare_df = pd.DataFrame(compare_models, columns=["model", "score", "roc_auc", "ap", "f1_fpr1", "active_axis_count"])

    base_nonf0 = baseline_bytype_metrics[baseline_bytype_metrics.get("sid", pd.Series(dtype=float)).fillna(0).astype(float) > 0].copy()
    base_top = (
        base_nonf0.sort_values(["fault_type", "ap", "roc_auc"], ascending=[True, False, False], na_position="last")
        .groupby("fault_type", as_index=False)
        .first()[["fault_type", "ap"]]
        .rename(columns={"ap": "baseline_top_ap"})
        if not base_nonf0.empty
        else pd.DataFrame(columns=["fault_type", "baseline_top_ap"])
    )
    improve_rows = []
    for score_name in ["ensemble_raw", "ensemble_top2_raw", "ensemble_weighted_noae_raw"]:
        ens_nonf0 = bytype[(bytype["score"] == score_name) & (bytype["sid"].fillna(0).astype(float) > 0)][["fault_type", "ap"]].rename(columns={"ap": "ensemble_ap"})
        cmp = ens_nonf0.merge(base_top, on="fault_type", how="left")
        improved = cmp[(cmp["ensemble_ap"] > cmp["baseline_top_ap"]) & np.isfinite(cmp["ensemble_ap"]) & np.isfinite(cmp["baseline_top_ap"])].copy()
        improve_rows.append({"model": score_name, "improved_fault_type_count": int(len(improved)), "fault_types": ", ".join(improved.sort_values("fault_type")["fault_type"].astype(str).tolist())})
    improve_df = pd.DataFrame(improve_rows)

    lines = []
    lines.append("# EXTERNAL GPVS ENSEMBLE2 ONEPAGE")
    lines.append("")
    lines.append("## 추가 ensemble 정의")
    lines.append("- `ensemble_top2_raw`: non-degenerate no-AE 축(level, vdrop, dtw, hs) 중 row-wise 상위 2개 z-score 평균")
    lines.append("- `ensemble_weighted_noae_raw`: no-AE 축(level, vdrop, dtw, hs)을 baseline overall ROC-AUC 기반 고정 가중치로 가중 평균")
    lines.append(f"- weights(no-AE, roc_auc-0.5 normalized): {weights}")
    lines.append("")
    lines.append("## overall 비교")
    lines.append(_to_md_table(compare_df))
    lines.append("")
    lines.append("## by-type 개선 수")
    lines.append(_to_md_table(improve_df))
    lines.append("")
    lines.append("## by-type 상세")
    lines.append(_to_md_table(bytype[["fault_type", "score", "active_axis_count", "roc_auc", "ap", "f1_fpr1"]]))
    lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return overall, bytype, out_csv, out_md


def evaluate_ensemble3(
    scores_csv: pathlib.Path,
    out_csv: pathlib.Path,
    out_bytype_csv: pathlib.Path,
    out_md: pathlib.Path,
    baseline_metrics: pd.DataFrame,
    baseline_bytype_metrics: pd.DataFrame,
    ensemble_raw_metrics: pd.DataFrame,
    ensemble_raw_bytype: pd.DataFrame,
    ensemble2_metrics: pd.DataFrame,
    ensemble2_bytype_metrics: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pathlib.Path, pathlib.Path]:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_bytype_csv.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    if not scores_csv.exists():
        empty = pd.DataFrame(columns=["score", "n_valid", "n_pos", "base_rate", "active_axis_count", "n_unique_score", "score_span", "degenerate_score", "roc_auc", "ap", "threshold_fpr1", "actual_fpr_fpr1", "precision_fpr1", "recall_fpr1", "f1_fpr1"])
        empty.to_csv(out_csv, index=False, encoding="utf-8-sig")
        pd.DataFrame(columns=["fault_type", "sid", "score", "n_windows", "active_axis_count", "n_unique_score", "score_span", "degenerate_score", "roc_auc", "ap", "threshold_fpr1", "actual_fpr_fpr1", "precision_fpr1", "recall_fpr1", "f1_fpr1"]).to_csv(out_bytype_csv, index=False, encoding="utf-8-sig")
        out_md.write_text("# EXTERNAL GPVS ENSEMBLE3 ONEPAGE\n\n_(input missing)_\n", encoding="utf-8")
        return empty, pd.DataFrame(), out_csv, out_md

    df = pd.read_csv(scores_csv)
    ens_df = _build_ensemble_frame(df)
    base_weights = _baseline_noae_weights(baseline_metrics)
    ens_df = _build_ensemble2_variants(ens_df, base_weights)
    mode_weights = _mode_specific_noae_weights(ens_df, metric="roc_auc")
    ens_df = _build_ensemble3_variants(ens_df, mode_weights)

    overall = pd.concat(
        [
            _evaluate_named_ensemble_overall(ens_df, "ensemble_mode_hybrid_raw", "ensemble_mode_hybrid_active_axes"),
            _evaluate_named_ensemble_overall(ens_df, "ensemble_mode_weighted_raw", "ensemble_mode_weighted_active_axes"),
        ],
        ignore_index=True,
    )
    overall.to_csv(out_csv, index=False, encoding="utf-8-sig")

    bytype = pd.concat(
        [
            _evaluate_named_ensemble_by_type(ens_df, "ensemble_mode_hybrid_raw", "ensemble_mode_hybrid_active_axes"),
            _evaluate_named_ensemble_by_type(ens_df, "ensemble_mode_weighted_raw", "ensemble_mode_weighted_active_axes"),
        ],
        ignore_index=True,
    )
    bytype.to_csv(out_bytype_csv, index=False, encoding="utf-8-sig")

    baseline_best = baseline_metrics.sort_values(["ap", "roc_auc"], ascending=False, na_position="last").head(1).copy()
    compare_rows = []
    if not baseline_best.empty:
        b = baseline_best.iloc[0]
        compare_rows.append(
            {
                "model": "baseline_best_single",
                "score": b["score"],
                "roc_auc": b["roc_auc"],
                "ap": b["ap"],
                "f1_fpr1": b["f1_fpr1"],
                "active_axis_count": 1.0,
                "degenerate_note": "",
            }
        )
    for score_name, src_df in [
        ("ensemble_raw", ensemble_raw_metrics),
        ("ensemble_top2_raw", ensemble2_metrics),
        ("ensemble_weighted_noae_raw", ensemble2_metrics),
        ("ensemble_mode_hybrid_raw", overall),
        ("ensemble_mode_weighted_raw", overall),
    ]:
        hit = src_df[src_df["score"] == score_name]
        if hit.empty:
            continue
        r = hit.iloc[0]
        compare_rows.append(
            {
                "model": score_name,
                "score": score_name,
                "roc_auc": r["roc_auc"],
                "ap": r["ap"],
                "f1_fpr1": r["f1_fpr1"],
                "active_axis_count": r["active_axis_count"],
                "degenerate_note": "exclude" if bool(r.get("degenerate_score", 0.0)) else "",
            }
        )
    compare_df = pd.DataFrame(compare_rows)

    base_nonf0 = baseline_bytype_metrics[baseline_bytype_metrics.get("sid", pd.Series(dtype=float)).fillna(0).astype(float) > 0].copy()
    base_top = (
        base_nonf0.sort_values(["fault_type", "ap", "roc_auc"], ascending=[True, False, False], na_position="last")
        .groupby("fault_type", as_index=False)
        .first()[["fault_type", "ap"]]
        .rename(columns={"ap": "baseline_top_ap"})
        if not base_nonf0.empty
        else pd.DataFrame(columns=["fault_type", "baseline_top_ap"])
    )

    bytype_sources = {
        "ensemble_raw": ensemble_raw_bytype,
        "ensemble_top2_raw": ensemble2_bytype_metrics,
        "ensemble_weighted_noae_raw": ensemble2_bytype_metrics,
        "ensemble_mode_hybrid_raw": bytype,
        "ensemble_mode_weighted_raw": bytype,
    }
    improve_rows = []
    improve_lists: dict[str, list[str]] = {}
    for score_name, src_df in bytype_sources.items():
        ens_nonf0 = src_df[(src_df["score"] == score_name) & (src_df["sid"].fillna(0).astype(float) > 0)][["fault_type", "ap"]].rename(columns={"ap": "ensemble_ap"})
        cmp = ens_nonf0.merge(base_top, on="fault_type", how="left")
        improved = cmp[(cmp["ensemble_ap"] > cmp["baseline_top_ap"]) & np.isfinite(cmp["ensemble_ap"]) & np.isfinite(cmp["baseline_top_ap"])].sort_values("fault_type")
        improve_lists[score_name] = improved["fault_type"].astype(str).tolist()
        improve_rows.append(
            {
                "model": score_name,
                "improved_fault_type_count": int(len(improved)),
                "fault_types": ", ".join(improve_lists[score_name]),
            }
        )
    improve_df = pd.DataFrame(improve_rows)

    lines = []
    lines.append("# EXTERNAL GPVS ENSEMBLE3 ONEPAGE")
    lines.append("")
    lines.append("## 추가 ensemble 정의")
    lines.append("- `ensemble_mode_hybrid_raw`: L 모드에는 `ensemble_weighted_noae_raw`, M 모드에는 `ensemble_top2_raw`를 사용합니다.")
    lines.append("- `ensemble_mode_weighted_raw`: no-AE raw 축(level, vdrop, dtw, hs)에 대해 mode(L/M)별 ROC-AUC 기반 가중치를 따로 계산해 weighted average를 만듭니다.")
    lines.append(f"- mode weights L: {mode_weights.get('L', {})}")
    lines.append(f"- mode weights M: {mode_weights.get('M', {})}")
    lines.append("")
    lines.append("## overall 비교")
    lines.append(_to_md_table(compare_df))
    lines.append("")
    lines.append("## by-type 개선 수")
    lines.append(_to_md_table(improve_df))
    lines.append("")
    lines.append("## 해석 메모")
    lines.append("- `degenerate_score=1`인 row는 해석 제외입니다.")
    lines.append("- `actual_fpr_fpr1`은 기존과 동일한 fixed-FPR 규칙으로 계산했습니다.")
    lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return overall, bytype, out_csv, out_md


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Evaluate GPVS external benchmark from gpvs_window_scores.csv")
    ap.add_argument("--scores-csv", default="data/gpvs/out/gpvs_window_scores.csv", help="Input window score csv")
    ap.add_argument("--out-csv", default="data/gpvs/out/EXTERNAL_GPVS_METRICS.csv", help="Output metrics csv")
    ap.add_argument("--out-md", default="data/gpvs/out/EXTERNAL_GPVS_ONEPAGE.md", help="Output onepage markdown")
    ap.add_argument("--out-bytype-csv", default="data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv", help="Output by-type metrics csv")
    ap.add_argument("--out-bytype-md", default="data/gpvs/out/EXTERNAL_GPVS_BYTYPE_ONEPAGE.md", help="Output by-type markdown")
    ap.add_argument("--out-ensemble-csv", default="data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE_METRICS.csv", help="Output ensemble overall metrics csv")
    ap.add_argument("--out-ensemble-bytype-csv", default="data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE_BYTYPE_METRICS.csv", help="Output ensemble by-type metrics csv")
    ap.add_argument("--out-ensemble-md", default="data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE_ONEPAGE.md", help="Output ensemble onepage markdown")
    ap.add_argument("--out-ensemble2-csv", default="data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE2_METRICS.csv", help="Output ensemble2 overall metrics csv")
    ap.add_argument("--out-ensemble2-bytype-csv", default="data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE2_BYTYPE_METRICS.csv", help="Output ensemble2 by-type metrics csv")
    ap.add_argument("--out-ensemble2-md", default="data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE2_ONEPAGE.md", help="Output ensemble2 onepage markdown")
    ap.add_argument("--out-ensemble3-csv", default="data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE3_METRICS.csv", help="Output ensemble3 overall metrics csv")
    ap.add_argument("--out-ensemble3-bytype-csv", default="data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE3_BYTYPE_METRICS.csv", help="Output ensemble3 by-type metrics csv")
    ap.add_argument("--out-ensemble3-md", default="data/gpvs/out/EXTERNAL_GPVS_ENSEMBLE3_ONEPAGE.md", help="Output ensemble3 onepage markdown")
    ap.add_argument("--k", type=int, default=20, help="K for precision@K and topK delay rule")
    ap.add_argument("--thr-q", type=float, default=0.95, help="Healthy quantile for score threshold in delay metric")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    metrics, bytype_metrics, out_csv, out_md, out_bytype_csv, out_bytype_md = evaluate(
        scores_csv=pathlib.Path(args.scores_csv),
        out_csv=pathlib.Path(args.out_csv),
        out_md=pathlib.Path(args.out_md),
        out_bytype_csv=pathlib.Path(args.out_bytype_csv),
        out_bytype_md=pathlib.Path(args.out_bytype_md),
        k=int(args.k),
        thr_q=float(args.thr_q),
    )
    ensemble_metrics, ensemble_bytype_metrics, out_ensemble_csv, out_ensemble_md, _ = evaluate_ensemble(
        scores_csv=pathlib.Path(args.scores_csv),
        out_csv=pathlib.Path(args.out_ensemble_csv),
        out_bytype_csv=pathlib.Path(args.out_ensemble_bytype_csv),
        out_md=pathlib.Path(args.out_ensemble_md),
        baseline_metrics=metrics,
        baseline_bytype_metrics=bytype_metrics,
    )
    ensemble2_metrics, ensemble2_bytype_metrics, out_ensemble2_csv, out_ensemble2_md = evaluate_ensemble2(
        scores_csv=pathlib.Path(args.scores_csv),
        out_csv=pathlib.Path(args.out_ensemble2_csv),
        out_bytype_csv=pathlib.Path(args.out_ensemble2_bytype_csv),
        out_md=pathlib.Path(args.out_ensemble2_md),
        baseline_metrics=metrics,
        baseline_bytype_metrics=bytype_metrics,
        ensemble_raw_metrics=ensemble_metrics,
        ensemble_raw_bytype=ensemble_bytype_metrics,
    )
    ensemble3_metrics, ensemble3_bytype_metrics, out_ensemble3_csv, out_ensemble3_md = evaluate_ensemble3(
        scores_csv=pathlib.Path(args.scores_csv),
        out_csv=pathlib.Path(args.out_ensemble3_csv),
        out_bytype_csv=pathlib.Path(args.out_ensemble3_bytype_csv),
        out_md=pathlib.Path(args.out_ensemble3_md),
        baseline_metrics=metrics,
        baseline_bytype_metrics=bytype_metrics,
        ensemble_raw_metrics=ensemble_metrics,
        ensemble_raw_bytype=ensemble_bytype_metrics,
        ensemble2_metrics=ensemble2_metrics,
        ensemble2_bytype_metrics=ensemble2_bytype_metrics,
    )
    print(f"[OK] rows(metrics): {len(metrics)}")
    print(f"[OK] rows(bytype): {len(bytype_metrics)}")
    print(f"[OK] rows(ensemble_metrics): {len(ensemble_metrics)}")
    print(f"[OK] rows(ensemble_bytype): {len(ensemble_bytype_metrics)}")
    print(f"[OK] rows(ensemble2_metrics): {len(ensemble2_metrics)}")
    print(f"[OK] rows(ensemble2_bytype): {len(ensemble2_bytype_metrics)}")
    print(f"[OK] rows(ensemble3_metrics): {len(ensemble3_metrics)}")
    print(f"[OK] rows(ensemble3_bytype): {len(ensemble3_bytype_metrics)}")
    print(f"[OK] wrote metrics: {out_csv}")
    print(f"[OK] wrote onepage: {out_md}")
    print(f"[OK] wrote bytype metrics: {out_bytype_csv}")
    print(f"[OK] wrote bytype onepage: {out_bytype_md}")
    print(f"[OK] wrote ensemble metrics: {out_ensemble_csv}")
    print(f"[OK] wrote ensemble bytype metrics: {args.out_ensemble_bytype_csv}")
    print(f"[OK] wrote ensemble onepage: {out_ensemble_md}")
    print(f"[OK] wrote ensemble2 metrics: {out_ensemble2_csv}")
    print(f"[OK] wrote ensemble2 bytype metrics: {args.out_ensemble2_bytype_csv}")
    print(f"[OK] wrote ensemble2 onepage: {out_ensemble2_md}")
    print(f"[OK] wrote ensemble3 metrics: {out_ensemble3_csv}")
    print(f"[OK] wrote ensemble3 bytype metrics: {args.out_ensemble3_bytype_csv}")
    print(f"[OK] wrote ensemble3 onepage: {out_ensemble3_md}")


if __name__ == "__main__":
    main()
