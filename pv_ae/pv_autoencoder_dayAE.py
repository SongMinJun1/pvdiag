# ====== pv_autoencoder_dayAE.py: AE + 최소 룰 기반 버전 ======
import argparse
import json
import pathlib
import re
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm


# ========= 유틸 =========

# ======== Filename date helper (SSOT) ========
_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")

def extract_date_from_filename(fname: str) -> pd.Timestamp:
    """Extract first YYYY-MM-DD from filename and return normalized Timestamp.
    Returns pd.NaT when not found / parse fails.
    """
    m = _DATE_RE.search(str(fname))
    if not m:
        return pd.NaT
    return pd.to_datetime(m.group(1), errors="coerce").normalize()


def find_col(df: pd.DataFrame, *names: str) -> str:
    """CSV 컬럼 이름이 조금씩 달라도 비슷한 걸 찾아주는 헬퍼."""
    low = {c.lower(): c for c in df.columns}
    for n in names:
        if n.lower() in low:
            return low[n.lower()]
    base = names[0].lower().replace(" ", "").replace("_", "")
    for c in df.columns:
        if base in c.lower().replace(" ", "").replace("_", ""):
            return c
    raise KeyError(f"column not found: {names}")


def to_fixed_length(ts: pd.Series, target_len: int = 96) -> np.ndarray:
    """1일 시계열을 0~1 구간에서 선형보간 → 길이 target_len 벡터."""
    if len(ts) == 0:
        return np.zeros(target_len, dtype=float)
    x = np.linspace(0, 1, num=len(ts))
    y = ts.values.astype(float)
    xi = np.linspace(0, 1, num=target_len)
    yi = np.interp(xi, x, y)
    yi = np.nan_to_num(yi, nan=0.0, posinf=0.0, neginf=0.0)
    return yi


def estimate_interval_minutes(dt_index: pd.DatetimeIndex) -> float:
    """Robustly estimate sampling interval (minutes) from timestamp diffs.

    - Uses median of positive diffs (seconds) to avoid outliers.
    - Fallback to 5.0 when estimation fails.
    """
    try:
        if dt_index is None or len(dt_index) < 3:
            return 5.0
        diffs = dt_index.to_series().diff().dt.total_seconds().to_numpy()
        diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
        if len(diffs) == 0:
            return 5.0
        med_sec = float(np.median(diffs))
        if not np.isfinite(med_sec) or med_sec <= 0:
            return 5.0
        return med_sec / 60.0
    except Exception:
        return 5.0


# ==== nanmean_or: np.nanmean with empty-slice guard ====
def nanmean_or(arr: np.ndarray | list, default: float = np.nan) -> float:
    """np.nanmean with an explicit empty-slice guard.

    Returns `default` when there are no finite values.
    """
    a = np.asarray(arr, dtype=float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return float(default)
    return float(np.mean(a))


# ======== Panel group key helper ========
def panel_group_key(pid: str) -> str:
    """Best-effort grouping key from panel_id.

    Many of our panel_id values look like:
      <uuid>.<string>.<panel>
    For peer baselines, we should compare within the same <uuid>.<string> group to
    avoid false V-drop signals caused by different string designs/MPPT voltages.

    If the format is not like that, fall back to the first token.
    """
    s = str(pid)
    parts = s.split(".")
    if len(parts) >= 3:
        return parts[0] + "." + parts[1]
    if len(parts) == 2:
        return parts[0]
    return s

# ======== 1D k-means (k=2) and train-only vbin builder ========

def kmeans_1d_2(x: np.ndarray, iters: int = 20) -> tuple[float, float, float]:
    """Simple 1D k-means for k=2 without sklearn.

    Returns (c0, c1, split) where split is midpoint between centroids.
    Assumes x is finite and len(x) >= 2.
    """
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        m = float(np.nanmedian(x)) if len(x) else 0.0
        return m, m, m

    # init: 25th and 75th percentiles
    c0 = float(np.quantile(x, 0.25))
    c1 = float(np.quantile(x, 0.75))
    if not np.isfinite(c0):
        c0 = float(np.nanmin(x))
    if not np.isfinite(c1):
        c1 = float(np.nanmax(x))
    if c0 == c1:
        c1 = c0 + 1e-6

    for _ in range(int(iters)):
        d0 = np.abs(x - c0)
        d1 = np.abs(x - c1)
        m0 = x[d0 <= d1]
        m1 = x[d0 > d1]
        if len(m0) > 0:
            c0_new = float(np.mean(m0))
        else:
            c0_new = c0
        if len(m1) > 0:
            c1_new = float(np.mean(m1))
        else:
            c1_new = c1
        # convergence
        if abs(c0_new - c0) < 1e-6 and abs(c1_new - c1) < 1e-6:
            c0, c1 = c0_new, c1_new
            break
        c0, c1 = c0_new, c1_new

    # order centroids
    if c0 > c1:
        c0, c1 = c1, c0
    split = 0.5 * (c0 + c1)
    return float(c0), float(c1), float(split)


def build_vbin_map_from_train(
    train_files: list[pathlib.Path],
    critical_peer_min: float,
    mid_peer_alive_thr: float,
    mid_ratio_dead_thr: float,
    coverage_min: float,
) -> tuple[dict[str, int], dict[str, any]]:
    """Build a stable per-panel voltage-bin map from TRAIN period only.

    Purpose:
    - Some group_key contain mixed string designs / MPPT voltages.
    - v_ref_span becomes large and v_ref_ok blocks v_drop.
    - We split group_key into sub-groups (vbin=0/1) based on panel-level typical mid_v_ratio.

    Rules:
    - Use TRAIN files only (no leakage).
    - Exclude data_bad and dead-like rows when estimating panel typical mid_v_ratio.
    - Assign vbin per base group_key using 1D k-means (k=2) on panel medians.
    - If group is unimodal (small separation), do not split.

    Returns:
      vbin_map: panel_id(str) -> 0 or 1
      diag: diagnostics dict for logging
    """
    # Collect mid_v_ratio observations for each panel across train days
    # NOTE (Gangui finding): `mid_peer` can be consistently around ~0.4 on clear days
    # depending on daylight/mid-window definition. If we gate too hard (e.g., 0.5),
    # vbin training observations become empty and vbin_map degenerates to n=0.
    # We therefore use a slightly more permissive peer gate ONLY for building vbin_map.
    vbin_peer_min = min(float(mid_peer_alive_thr), 0.35)
    obs: dict[str, list[float]] = {}
    obs_gk: dict[str, str] = {}

    for p in train_files:
        try:
            ev_map = compute_event_features(p)
        except Exception:
            continue
        for pid, ev in ev_map.items():
            pid_s = str(pid)
            mv = ev.get("mid_v_ratio", np.nan)
            mp = ev.get("mid_peer", np.nan)
            mr = ev.get("mid_ratio", np.nan)
            cov = ev.get("coverage_mid", ev.get("coverage", np.nan))

            # train-time quality gates
            if not np.isfinite(mv) or not np.isfinite(mp) or not np.isfinite(mr):
                continue
            if float(mp) < float(vbin_peer_min):
                continue
            if float(cov) < float(coverage_min):
                continue
            # exclude dead-like
            if float(mr) <= float(mid_ratio_dead_thr):
                continue

            gk = panel_group_key(pid_s)
            obs.setdefault(pid_s, []).append(float(mv))
            obs_gk[pid_s] = gk

    # Panel-level typical mid_v_ratio (median)
    panel_med: dict[str, float] = {}
    for pid_s, lst in obs.items():
        arr = np.asarray(lst, dtype=float)
        arr = arr[np.isfinite(arr)]
        if len(arr) == 0:
            continue
        panel_med[pid_s] = float(np.median(arr))

    # Group panels by base group_key
    by_gk: dict[str, list[tuple[str, float]]] = {}
    for pid_s, mv_med in panel_med.items():
        gk = obs_gk.get(pid_s) or panel_group_key(pid_s)
        by_gk.setdefault(gk, []).append((pid_s, float(mv_med)))

    vbin_map: dict[str, int] = {}
    diag: dict[str, any] = {
        "groups_total": int(len(by_gk)),
        "groups_split": 0,
        "groups_unsplit": 0,
        "panels_assigned": 0,
        "rule": "train-only panel_median mid_v_ratio; kmeans1d k=2; split only if separation is meaningful",
        "groups": {},
    }

    # Heuristic thresholds
    # - We normally require >=2 panels per bin to avoid unstable references.
    # - However, for small groups (n=3~5) with *very* strong separation, we allow 1 panel in the smaller bin.
    #   This is specifically to avoid permanent legacy fallback when a group_key has only 3~5 panels.
    min_panels_to_split = 4
    min_sep = 0.18        # typical separation threshold
    min_sep_strong = 0.30 # strong separation threshold (allow split even when group is small)
    min_bin_size = 2      # normal requirement
    min_bin_size_small = 1  # allowed only when sep is strong and group is small

    for gk, pairs in by_gk.items():
        pairs = [(pid_s, mv) for (pid_s, mv) in pairs if np.isfinite(mv)]
        if len(pairs) < 2:
            for pid_s, _mv in pairs:
                vbin_map[pid_s] = 0
            diag["groups"][gk] = {"n": len(pairs), "split": False, "reason": "too_few_panels"}
            diag["groups_unsplit"] += 1
            continue

        xs = np.asarray([mv for (_pid_s, mv) in pairs], dtype=float)
        xs = xs[np.isfinite(xs)]
        if len(xs) < 2:
            for pid_s, _mv in pairs:
                vbin_map[pid_s] = 0
            diag["groups"][gk] = {"n": len(pairs), "split": False, "reason": "no_finite"}
            diag["groups_unsplit"] += 1
            continue

        c0, c1, split = kmeans_1d_2(xs)
        sep = float(abs(c1 - c0))

        # Split decision:
        # - Normal case: enough panels AND meaningful separation
        # - Strong-sep case: even if group is small, split when sep is very large
        do_split = (
            ((len(pairs) >= int(min_panels_to_split)) and (sep >= float(min_sep)))
            or ((sep >= float(min_sep_strong)) and (len(pairs) >= 3))
        )

        if not do_split:
            for pid_s, _mv in pairs:
                vbin_map[pid_s] = 0
            diag["groups"][gk] = {
                "n": len(pairs),
                "split": False,
                "reason": "unimodal_or_small",
                "c0": c0,
                "c1": c1,
                "sep": sep,
                "split_at": split,
            }
            diag["groups_unsplit"] += 1
            continue

        # Bin-size safety:
        # - default: require >=2 panels per bin
        # - small group + strong separation: allow 1 panel in the smaller bin
        b0 = int(sum(1 for (_pid_s, mv) in pairs if float(mv) <= float(split)))
        b1 = int(sum(1 for (_pid_s, mv) in pairs if float(mv) > float(split)))

        eff_min_bin = int(min_bin_size)
        if (len(pairs) <= 5) and (sep >= float(min_sep_strong)):
            eff_min_bin = int(min_bin_size_small)

        if (b0 < eff_min_bin) or (b1 < eff_min_bin):
            for pid_s, _mv in pairs:
                vbin_map[pid_s] = 0
            diag["groups"][gk] = {
                "n": len(pairs),
                "split": False,
                "reason": "tiny_bin",
                "c0": c0,
                "c1": c1,
                "sep": sep,
                "split_at": split,
                "bin0": b0,
                "bin1": b1,
                "eff_min_bin": eff_min_bin,
            }
            diag["groups_unsplit"] += 1
            continue

        # Assign bins by split point
        for pid_s, mv in pairs:
            vbin_map[pid_s] = 0 if float(mv) <= float(split) else 1

        diag["groups"][gk] = {
            "n": len(pairs),
            "split": True,
            "c0": c0,
            "c1": c1,
            "sep": sep,
            "split_at": split,
            "bin0": int(sum(1 for (_pid_s, mv) in pairs if float(mv) <= float(split))),
            "bin1": int(sum(1 for (_pid_s, mv) in pairs if float(mv) > float(split))),
        }
        diag["groups_split"] += 1

    diag["panels_assigned"] = int(len(vbin_map))
    return vbin_map, diag


def mark_run_segments(
    df: pd.DataFrame,
    key_col: str,
    date_col: str,
    cond_col: str,
    min_len: int,
    out_col: str,
) -> pd.DataFrame:
    """Mark whole consecutive-true segments when run length >= min_len."""
    df[out_col] = False
    if min_len <= 1:
        df[out_col] = df[cond_col].fillna(False).astype(bool)
        return df

    df = df.sort_values([key_col, date_col]).copy()
    for pid, g in df.groupby(key_col, sort=False):
        idxs = g.index.to_list()
        flags = g[cond_col].fillna(False).astype(bool).to_list()

        start = None
        run_len = 0
        for k, flag in enumerate(flags + [False]):  # sentinel
            if flag:
                if start is None:
                    start = k
                    run_len = 1
                else:
                    run_len += 1
            else:
                if start is not None and run_len >= int(min_len):
                    seg_idxs = idxs[start : start + run_len]
                    df.loc[seg_idxs, out_col] = True
                start = None
                run_len = 0
    return df


def compute_vdrop_labels(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    """Single SSOT for critical-like labels.

    Output columns (defined exactly once here):
      - critical_like_raw / critical_like_suspect_raw
      - critical_like_eff / critical_like / critical_like_suspect / critical_like_suspect_eff
      - critical_like_legacy / critical_source / vdrop_trust
    """
    out = df.copy()
    args = params["args"]
    tuning_level = str(params.get("tuning_level", "p2")).lower().strip()

    def _bool_col(name: str) -> pd.Series:
        if name not in out.columns:
            return pd.Series(False, index=out.index)
        s = pd.to_numeric(out[name], errors="coerce").fillna(0.0)
        return s.ne(0)

    def _num_col(name: str) -> pd.Series:
        if name in out.columns:
            return pd.to_numeric(out[name], errors="coerce")
        return pd.Series(np.nan, index=out.index, dtype=float)

    v_ref_ok = _bool_col("v_ref_ok")
    data_bad = _bool_col("data_bad")
    group_off_like = _bool_col("group_off_like")
    mid_peer_ok = _num_col("mid_peer") >= float(args.mid_peer_alive_thr)

    # V-drop hit evidence (trust-agnostic): preserve legacy guard set used in existing vdrop_condition_post.
    v_drop = _num_col("v_drop")
    mid_i = _num_col("mid_i_ratio")
    mid_r = _num_col("mid_ratio")
    vdrop_hit_any = (
        v_drop.notna()
        & np.isfinite(v_drop.to_numpy(dtype=float))
        & (v_drop >= float(args.v_drop_thr))
        & mid_i.notna()
        & (mid_i >= float(args.mid_i_ratio_healthy_thr))
        & mid_r.notna()
        & (mid_r >= float(args.critical_mid_ratio_min))
        & (mid_r <= float(args.critical_mid_ratio_max))
    )

    out["critical_like_raw"] = (vdrop_hit_any & v_ref_ok).astype(int)
    out["critical_like_suspect_raw"] = (vdrop_hit_any & (~v_ref_ok)).astype(int)

    # Legacy fallback semantics are preserved for p2 only.
    legacy_hit = pd.Series(False, index=out.index)
    if tuning_level == "p2":
        use_vdrop = v_ref_ok & np.isfinite(v_drop.to_numpy(dtype=float))
        cov_mid = _num_col("coverage_mid").fillna(0.0)
        mid_v = _num_col("mid_v_ratio")
        legacy_hit = (
            (~data_bad)
            & mid_peer_ok
            & (~use_vdrop)
            & (cov_mid >= float(args.coverage_min))
            & mid_v.notna()
            & (mid_v <= float(args.mid_v_ratio_critical_thr))
            & (mid_i >= float(args.mid_i_ratio_healthy_thr))
            & (mid_r >= float(args.critical_mid_ratio_min))
            & (mid_r <= float(args.critical_mid_ratio_max))
        )
    out["critical_like_legacy"] = legacy_hit.astype(int)

    # Effective labels (after quality + group-off gates) are defined once here.
    eff_vdrop = (
        (out["critical_like_raw"].astype(int) == 1)
        & (~data_bad)
        & mid_peer_ok
        & (~group_off_like)
    )
    eff_legacy = (
        legacy_hit.astype(bool)
        & (~group_off_like)
    )
    out["critical_like_eff"] = (eff_vdrop | eff_legacy).astype(bool)
    out["critical_like"] = out["critical_like_eff"].astype(bool)

    out["critical_like_suspect"] = (
        (out["critical_like_suspect_raw"].astype(int) == 1)
        & (~data_bad)
        & mid_peer_ok
        & (~group_off_like)
        & (~out["critical_like_eff"].astype(bool))
    ).astype(bool)
    out["critical_like_suspect_eff"] = out["critical_like_suspect"].astype(bool)

    out["vdrop_trust"] = v_ref_ok.astype(int)

    # Source is set once: legacy > vdrop > vdrop_suspect precedence.
    out["critical_source"] = "none"
    out.loc[out["critical_like_suspect"].astype(bool), "critical_source"] = "vdrop_suspect"
    out.loc[out["critical_like_eff"].astype(bool) & (~legacy_hit.astype(bool)), "critical_source"] = "vdrop"
    out.loc[legacy_hit.astype(bool) & out["critical_like_eff"].astype(bool), "critical_source"] = "legacy"

    return out


def _max_run_by_panel(df: pd.DataFrame, flag_col: str) -> pd.DataFrame:
    """Compute max consecutive-day run length per panel for a boolean/int flag."""
    tmp = df[["panel_id", "date", flag_col]].copy()
    tmp[flag_col] = pd.to_numeric(tmp[flag_col], errors="coerce").fillna(0).astype(int)
    tmp = tmp.sort_values(["panel_id", "date"])

    runs = []
    for pid, g in tmp.groupby("panel_id", sort=False):
        vals = g[flag_col].to_numpy(dtype=int)
        best = 0
        cur = 0
        for v in vals:
            if v == 1:
                cur += 1
                if cur > best:
                    best = cur
            else:
                cur = 0
        runs.append((pid, int(best)))
    return pd.DataFrame(runs, columns=["panel_id", f"{flag_col}_max_run"]).sort_values(
        f"{flag_col}_max_run", ascending=False
    )

# ======== DTW & Hampel Score Helpers =========

def dtw_distance(curve: np.ndarray, ref: np.ndarray, band: int | None = None) -> float:
    """
    Compute Dynamic Time Warping (DTW) distance between two 1D arrays.
    - Truncate to min(len(curve), len(ref))
    - Use squared difference as cost
    - NaNs treated as 0.0
    - O(N^2) baseline; if `band` is provided, apply Sakoe–Chiba constraint to speed up.

    Parameters
    ----------
    curve, ref : np.ndarray
        1D arrays.
    band : int | None
        If not None, only compute cells where |i-j| <= band.
        Use a small band (e.g., 8~16 for length 96) to reduce compute.
    """
    a = np.nan_to_num(curve, nan=0.0, posinf=0.0, neginf=0.0)
    b = np.nan_to_num(ref, nan=0.0, posinf=0.0, neginf=0.0)
    n = min(len(a), len(b))
    a = a[:n]
    b = b[:n]

    # If band is None, default to full DTW.
    if band is None:
        band = n  # effectively unconstrained
    else:
        band = int(max(0, band))

    INF = 1e30
    D = np.full((n, n), INF, dtype=float)

    # Initialize start
    D[0, 0] = (a[0] - b[0]) ** 2

    # Initialize first column/row within band
    for i in range(1, n):
        if i <= band:
            D[i, 0] = D[i - 1, 0] + (a[i] - b[0]) ** 2
    for j in range(1, n):
        if j <= band:
            D[0, j] = D[0, j - 1] + (a[0] - b[j]) ** 2

    # Main DP with band constraint
    for i in range(1, n):
        j_start = max(1, i - band)
        j_end = min(n - 1, i + band)
        for j in range(j_start, j_end + 1):
            cost = (a[i] - b[j]) ** 2
            D[i, j] = cost + min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])

    return float(D[n - 1, n - 1])

def compute_hs(curve: np.ndarray) -> float:
    """
    Compute a Hampel-like turbulence score for a 1D array.
    - NaNs/infs replaced with 0.0
    - Uses median/MAD, fallback to std if MAD too small, else 0.0
    - Returns fraction of |z| >= 2.5
    """
    x = np.nan_to_num(curve, nan=0.0, posinf=0.0, neginf=0.0)
    med = np.median(x)
    mad = np.median(np.abs(x - med))
    scale = mad if mad >= 1e-6 else np.std(x)
    if scale < 1e-6:
        return 0.0
    z = (x - med) / scale
    return float(np.mean(np.abs(z) >= 2.5))


# ========= 하루 power ratio 곡선 (AE용) =========

def load_day_curves(csv_path: pathlib.Path, daylight_frac: float = 0.10, peer_eps: float = 1e-6, use_log_ratio: bool = False) -> Dict[str, np.ndarray]:
    """
    - P = V * I
    - peer median P 기준으로 P_ratio = P / peerP
    - peerP가 max의 daylight_frac 이상인 구간만 사용
    - 각 패널 곡선을 길이 96으로 보간
    """
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(csv_path)

    c_dt = find_col(df, "date_time", "datetime", "timestamp", "time")
    c_id = find_col(df, "map_id", "panel_id", "id")
    c_v = find_col(df, "v_in (v)", "v_in", "vin", "input_voltage")
    c_i = find_col(df, "i_out (a)", "i_out", "i", "current")

    df["_dt"] = pd.to_datetime(df[c_dt], errors="coerce")
    df = df.dropna(subset=["_dt"]).sort_values("_dt")

    v = pd.to_numeric(df[c_v], errors="coerce")
    i = pd.to_numeric(df[c_i], errors="coerce")
    df["p_calc"] = (v * i).astype(float).clip(lower=0)

    P = df.pivot_table(index="_dt", columns=c_id, values="p_calc")

    # Site-level peer (for daylight detection)
    peerP_site = P.median(axis=1)
    if len(peerP_site) == 0 or np.nanmax(peerP_site.values) <= 0:
        return {}

    # Daylight mask based on site-level peer
    mask = peerP_site >= float(np.nanmax(peerP_site.values)) * daylight_frac
    P_use = P.loc[mask]

    # Build per-group peer medians to avoid false anomalies from heterogeneous strings
    # IMPORTANT: keep original column labels for safe DataFrame indexing (do not index by str(...) blindly).
    group_cols: Dict[str, List[Any]] = {}
    for pid in P_use.columns:
        pid_s = str(pid)
        group_cols.setdefault(panel_group_key(pid_s), []).append(pid)
    peerP_group: Dict[str, pd.Series] = {}
    for gk, gcols in group_cols.items():
        peerP_group[gk] = P_use[gcols].median(axis=1)

    curves: Dict[str, np.ndarray] = {}
    for pid in P_use.columns:
        pid_s = str(pid)
        s = P_use[pid].astype(float)
        if s.notna().sum() < 10:
            continue
        gk = panel_group_key(pid_s)
        peer_use = peerP_group.get(gk)
        if peer_use is None or len(peer_use) == 0:
            continue
        peer_aligned = peer_use.reindex(s.index, method="nearest")

        # Robust ratio: avoid division blow-up when peer baseline is tiny.
        # Optionally use log-stabilized ratio for heavy-tailed / low-irradiance robustness.
        peer_aligned_v = pd.to_numeric(peer_aligned, errors="coerce").astype(float)
        s_v = pd.to_numeric(s, errors="coerce").astype(float)

        if use_log_ratio:
            # log1p ratio proxy: log(P+1) - log(peer+1)
            ratio_vals = (np.log1p(s_v.clip(lower=0.0)) - np.log1p(peer_aligned_v.clip(lower=0.0)))
        else:
            safe_peer = peer_aligned_v.where(peer_aligned_v >= float(peer_eps), np.nan)
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio_vals = s_v / safe_peer

        ratio = pd.Series(
            np.nan_to_num(ratio_vals.to_numpy(), nan=0.0, posinf=0.0, neginf=0.0),
            index=s.index,
        )
        curves[pid_s] = to_fixed_length(ratio, 96)
    return curves


# ========= 하루 이벤트 feature (룰용) =========

def compute_event_features(
    csv_path: pathlib.Path,
    drop_thr: float = 0.90,
    sustain_thr: float = 0.80,
    last_minutes: int = 60,
    recovered_consec: int = 3,
    recovered_sustain_mins: int = 15,
    co_drop_thr: float = 0.15,
    daylight_event_thr: float = 0.2,
    peer_eps: float = 1e-6,
) -> Dict[str, Dict[str, Any]]:
    """
    패널별로:
      - drop_time: P_ratio가 sustain_thr 이하로 가장 길게 유지된 구간의 시작 시각 (daylight 안에서)
      - sustain_mins: drop 이후 P_ratio <= sustain_thr 인 연속 구간 최장 길이 (분)
      - recovered: drop 이후 P_ratio >= drop_thr 가 연속 recovered_consec 샘플 이상 유지되면 True
      - last_ratio: 마지막 last_minutes 동안 P_ratio 평균
      - last_peer: 마지막 last_minutes 동안 peerP_frac 평균
      - mid_ratio: 11시~15시 사이 daylight 구간에서 P_ratio 평균
      - mid_peer: 11시~15시 사이 daylight 구간에서 peerP_frac 평균
      - co_drop_frac: 최장 저하구간 동안 sustain_thr 이하에 들어간 패널 비율의 평균 (공간 동시성 지표)
      - NOTE: event daylight threshold is `daylight_event_thr` (default 0.2) and ratio uses `peer_eps` guard.
    """
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(csv_path)

    c_dt = find_col(df, "date_time", "datetime", "timestamp", "time")
    c_id = find_col(df, "map_id", "panel_id", "id")
    c_v = find_col(df, "v_in (v)", "v_in", "vin", "input_voltage")
    c_i = find_col(df, "i_out (a)", "i_out", "i", "current")

    df["_dt"] = pd.to_datetime(df[c_dt], errors="coerce")
    df = df.dropna(subset=["_dt"]).sort_values("_dt")

    V = df.pivot_table(index="_dt", columns=c_id, values=c_v)
    I = df.pivot_table(index="_dt", columns=c_id, values=c_i)
    V = V.apply(pd.to_numeric, errors="coerce").clip(lower=0)
    I = I.apply(pd.to_numeric, errors="coerce").clip(lower=0)
    P = (V * I).clip(lower=0)

    # Site-level peer (for daylight/midday gating)
    peerP_site = P.median(axis=1)
    peerV_site = V.median(axis=1)
    peerI_site = I.median(axis=1)
    if len(peerP_site) == 0 or np.nanmax(peerP_site.values) <= 0:
        return {}

    # Build per-group peer baselines (uuid.string) for ratio features
    # IMPORTANT: keep original column labels for safe DataFrame indexing.
    group_cols: Dict[str, List[Any]] = {}
    for pid in P.columns:
        pid_s = str(pid)
        group_cols.setdefault(panel_group_key(pid_s), []).append(pid)
    peerP_by_group: Dict[str, pd.Series] = {}
    peerV_by_group: Dict[str, pd.Series] = {}
    peerI_by_group: Dict[str, pd.Series] = {}

    for gk, gcols in group_cols.items():
        peerP_by_group[gk] = P[gcols].median(axis=1)
        peerV_by_group[gk] = V[gcols].median(axis=1)
        peerI_by_group[gk] = I[gcols].median(axis=1)

    # Fallbacks (degenerate guards)
    for gk in list(peerP_by_group.keys()):
        if len(peerP_by_group[gk]) == 0 or np.nanmax(peerP_by_group[gk].values) <= 0:
            peerP_by_group[gk] = peerP_site.copy()
        if len(peerV_by_group[gk]) == 0 or np.nanmax(peerV_by_group[gk].values) <= 0:
            # DO NOT fallback to power baseline (unit mismatch). Use site-level V median if available.
            if len(peerV_site) > 0 and np.nanmax(peerV_site.values) > 0:
                peerV_by_group[gk] = peerV_site.copy()
            else:
                peerV_by_group[gk] = pd.Series(np.nan, index=peerP_site.index)
        if len(peerI_by_group[gk]) == 0 or np.nanmax(peerI_by_group[gk].values) <= 0:
            # Prefer site-level I median; fallback to 1.0 only when everything is missing.
            if len(peerI_site) > 0 and np.nanmax(peerI_site.values) > 0:
                peerI_by_group[gk] = peerI_site.copy()
            else:
                peerI_by_group[gk] = pd.Series(1.0, index=peerP_site.index)

    # Robust interval estimation (minutes)
    interval_min = estimate_interval_minutes(P.index)
    if not np.isfinite(interval_min) or interval_min <= 0:
        interval_min = 5.0

    # Normalize site-level peer power to [0,1] for daylight and mid-window gating.
    # NOTE: peerP_site can have NaNs at timestamps where all panels are missing.
    # If we later take a mean over a slice that is all-NaN, np.nanmean returns NaN,
    # which then propagates to mid_peer/last_peer and breaks gates downstream.
    peerP_frac = peerP_site / float(np.nanmax(peerP_site.values))
    peerP_frac = peerP_frac.astype(float)
    peerP_frac_arr = np.nan_to_num(peerP_frac.to_numpy(), nan=0.0, posinf=0.0, neginf=0.0)
    # daylight (event): peerP_frac >= daylight_event_thr
    daylight_thr = float(daylight_event_thr)
    daylight_mask = peerP_frac_arr >= daylight_thr

    daylight_mask_np = np.asarray(daylight_mask, dtype=bool)

    times = P.index.to_numpy()
    times_idx = P.index

    # midday mask: daylight and hour in [11,15)
    mid_mask = np.array([
        (pf >= daylight_thr) and (11 <= ts.hour < 15)
        for pf, ts in zip(peerP_frac_arr, times_idx)
    ])

    # Site-level ratio table only for spatial concurrence (co-drop) diagnostics
    with np.errstate(divide="ignore", invalid="ignore"):
        R_tbl_site = P.div(peerP_site, axis=0)

    out: Dict[str, Dict[str, Any]] = {}

    for pid in P.columns:
        pid_s = str(pid)
        gk = panel_group_key(pid_s)
        peerP = peerP_by_group.get(gk, peerP_site)
        peerV = peerV_by_group.get(gk, peerV_site)
        peerI = peerI_by_group.get(gk, peerI_site)
        p = P[pid].astype(float).to_numpy()
        if np.sum(np.isfinite(p)) < 5:
            continue

        # coverage: daylight 구간 중 실제 측정이 있는 비율
        valid_day = np.isfinite(p) & daylight_mask_np
        daylight_count = int(daylight_mask_np.sum())
        if daylight_count > 0:
            coverage = float(valid_day.sum() / daylight_count)
        else:
            coverage = 0.0

        # coverage within mid-window (11~15) to avoid "noon holes" masking issues
        if int(np.sum(mid_mask)) > 0:
            valid_mid = np.isfinite(p) & mid_mask
            coverage_mid = float(np.sum(valid_mid) / int(np.sum(mid_mask)))
        else:
            coverage_mid = float(coverage)

        # EVENT ratio with peer-eps gating (SSOT): peer < eps -> NaN (avoid 0/0, x/0 blow-ups)
        peer_arr = pd.to_numeric(peerP, errors="coerce").astype(float).to_numpy()
        safe_peer = np.where(peer_arr >= float(peer_eps), peer_arr, np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            r = p / safe_peer
        # Keep NaNs here; downstream masks/np.isfinite() will exclude invalid points deterministically.

        # V/I ratio arrays (panel vs *group* peer)
        v_arr = V[pid].astype(float).to_numpy()
        i_arr = I[pid].astype(float).to_numpy()
        with np.errstate(divide="ignore", invalid="ignore"):
            vr = v_arr / peerV.to_numpy()
            ir = i_arr / peerI.to_numpy()
        vr = np.nan_to_num(vr, nan=0.0, posinf=0.0, neginf=0.0)
        ir = np.nan_to_num(ir, nan=0.0, posinf=0.0, neginf=0.0)

        # daylight-masked versions
        vr_day = vr.copy()
        ir_day = ir.copy()
        vr_day[~daylight_mask_np] = np.nan
        ir_day[~daylight_mask_np] = np.nan

        # Spatial concurrence helper series for this panel/day
        # Fraction of panels that are also <= sustain_thr at each timestamp (within daylight)
        # NOTE: Uses median peer baseline; if a large fraction drops together, it's more likely environmental.
        with np.errstate(invalid="ignore"):
            co_series = (R_tbl_site <= sustain_thr).mean(axis=1).to_numpy(dtype=float)
            co_series = np.nan_to_num(co_series, nan=0.0, posinf=0.0, neginf=0.0)
        co_series_day = co_series.copy()
        co_series_day[~daylight_mask_np] = np.nan

        # daylight 부분만 고려
        r_day = r.copy()
        r_day[~daylight_mask_np] = np.nan

        # longest low segment: P_ratio <= sustain_thr within daylight
        cond = np.isfinite(r_day) & (r_day <= sustain_thr)

        # Feature expansion: segment counts / total low minutes / quantiles / low-area
        r_day_f = r_day.copy()
        valid_mask = np.isfinite(r_day_f)

        if np.any(valid_mask):
            min_ratio = float(np.nanmin(r_day_f))
            p10_ratio = float(np.nanpercentile(r_day_f[valid_mask], 10))
            p50_ratio = float(np.nanpercentile(r_day_f[valid_mask], 50))
        else:
            min_ratio = 0.0
            p10_ratio = 0.0
            p50_ratio = 0.0

        # total low minutes
        total_low_pts = int(np.sum(cond))
        total_low_mins = int(round(total_low_pts * float(interval_min)))

        # low area: sum(thr - ratio) where ratio < thr
        low_area = float(np.nansum(np.maximum(0.0, float(sustain_thr) - np.nan_to_num(r_day_f, nan=np.nan))))

        # segment count: number of low segments
        seg_count = 0
        prev = False
        for flag in cond:
            if flag and (not prev):
                seg_count += 1
            prev = bool(flag)

        # compute mid_ratio and mid_peer_val (+ NEW: mid_v_ratio, mid_i_ratio)
        if np.any(mid_mask):
            mid_ratio = nanmean_or(r[mid_mask], default=np.nan)
            mid_peer_val = float(np.mean(peerP_frac_arr[mid_mask])) if np.any(mid_mask) else float(np.mean(peerP_frac_arr))
            mid_v_ratio = nanmean_or(vr[mid_mask], default=np.nan)
            mid_i_ratio = nanmean_or(ir[mid_mask], default=np.nan)
        else:
            mid_ratio = nanmean_or(r_day, default=np.nan)
            mid_peer_val = float(np.mean(peerP_frac_arr))
            mid_v_ratio = nanmean_or(vr_day, default=np.nan)
            mid_i_ratio = nanmean_or(ir_day, default=np.nan)

        if not np.any(cond):
            # no meaningful low segment
            out[pid_s] = {
                "drop_time": "",
                "sustain_mins": 0,
                "recovered": False,
                "last_ratio": nanmean_or(r_day, default=np.nan),
                "last_peer": float(np.mean(peerP_frac_arr)),
                "mid_ratio": float(mid_ratio),
                "mid_peer": float(mid_peer_val),
                "mid_v_ratio": float(mid_v_ratio) if 'mid_v_ratio' in locals() else nanmean_or(vr_day, default=np.nan),
                "mid_i_ratio": float(mid_i_ratio) if 'mid_i_ratio' in locals() else nanmean_or(ir_day, default=np.nan),
                "coverage": float(coverage),
                "co_drop_frac": 0.0,
                "recovered_any": False,
                "recovered_sustained": False,
                "re_drop": False,
                "coverage_mid": float(coverage_mid),
                "seg_count": int(seg_count),
                "total_low_mins": int(total_low_mins),
                "min_ratio": float(min_ratio),
                "p10_ratio": float(p10_ratio),
                "p50_ratio": float(p50_ratio),
                "low_area": float(low_area),
            }
            continue

        # find longest consecutive True segment in cond
        max_len = 0
        best_start = None
        best_end = None
        current_start = None
        current_len = 0

        for idx, flag in enumerate(cond):
            if flag:
                if current_start is None:
                    current_start = idx
                    current_len = 1
                else:
                    current_len += 1
                if current_len > max_len:
                    max_len = current_len
                    best_start = current_start
                    best_end = idx
            else:
                current_start = None
                current_len = 0

        drop_idx = best_start
        if drop_idx is None:
            # fallback: treat as no drop
            out[pid_s] = {
                "drop_time": "",
                "sustain_mins": 0,
                "recovered": False,
                "last_ratio": nanmean_or(r_day, default=np.nan),
                "last_peer": float(np.mean(peerP_frac_arr)),
                "mid_ratio": float(mid_ratio),
                "mid_peer": float(mid_peer_val),
                "mid_v_ratio": float(mid_v_ratio) if 'mid_v_ratio' in locals() else nanmean_or(vr_day, default=np.nan),
                "mid_i_ratio": float(mid_i_ratio) if 'mid_i_ratio' in locals() else nanmean_or(ir_day, default=np.nan),
                "coverage": float(coverage),
                "co_drop_frac": 0.0,
                "recovered_any": False,
                "recovered_sustained": False,
                "re_drop": False,
                "coverage_mid": float(coverage_mid),
                "seg_count": int(seg_count),
                "total_low_mins": int(total_low_mins),
                "min_ratio": float(min_ratio),
                "p10_ratio": float(p10_ratio),
                "p50_ratio": float(p50_ratio),
                "low_area": float(low_area),
            }
            continue

        # Spatial concurrence score for the chosen (longest) low segment
        # Average fraction of panels that are also low during this segment
        if best_end is not None and best_start is not None:
            seg = co_series_day[best_start : best_end + 1]
            co_drop_frac = nanmean_or(seg, default=0.0)
        else:
            co_drop_frac = 0.0

        drop_time = pd.Timestamp(times[drop_idx]).isoformat()
        sustain_mins = int(round(max_len * float(interval_min)))

        # recovered definitions
        # recovered_any: any post-segment ratio >= drop_thr
        # recovered_sustained: post-segment ratio >= drop_thr sustained for recovered_sustain_mins
        # re_drop: after sustained recovery, drops again to sustain_thr or below
        recovered_any = False
        recovered_sustained = False
        re_drop = False

        if best_end is not None and best_end + 1 < len(r):
            tail = r[best_end + 1 :]
            tail_ok = np.isfinite(tail) & (tail >= float(drop_thr))
            recovered_any = bool(np.any(tail_ok))

            # sustain requirement in points (time-based)
            sustain_pts = int(max(1, np.ceil(float(recovered_sustain_mins) / float(interval_min))))

            # longest consecutive True run
            run = 0
            best_run = 0
            for flag in tail_ok:
                if flag:
                    run += 1
                    best_run = max(best_run, run)
                else:
                    run = 0

            recovered_sustained = bool(best_run >= sustain_pts)

            # re_drop: only meaningful after sustained recovery
            if recovered_sustained:
                # find first index where sustained recovery starts
                run = 0
                start_idx = None
                for k, flag in enumerate(tail_ok):
                    if flag:
                        run += 1
                        if run >= sustain_pts:
                            start_idx = k - sustain_pts + 1
                            break
                    else:
                        run = 0

                if start_idx is not None:
                    after_rec = tail[start_idx + sustain_pts :]
                    after_low = np.isfinite(after_rec) & (after_rec <= float(sustain_thr))
                    re_drop = bool(np.any(after_low))

        # backward-compatible alias (old field)
        recovered = bool(recovered_sustained)

        # 마지막 last_minutes 동안 평균
        if len(times) > 0:
            last_dt = pd.Timestamp(times[-1])
            start_last = last_dt - pd.Timedelta(minutes=last_minutes)
            last_mask = (times >= np.datetime64(start_last)) & (times <= np.datetime64(last_dt))
        else:
            last_mask = np.zeros_like(r, dtype=bool)

        if np.any(last_mask):
            last_ratio = nanmean_or(r[last_mask], default=np.nan)
            last_peer = float(np.mean(peerP_frac_arr[last_mask])) if np.any(last_mask) else float(np.mean(peerP_frac_arr))
        else:
            last_ratio = nanmean_or(r_day, default=np.nan)
            last_peer = float(np.mean(peerP_frac_arr))

        out[pid_s] = {
            "drop_time": drop_time,
            "sustain_mins": sustain_mins,
            "recovered": bool(recovered),
            "last_ratio": last_ratio,
            "last_peer": last_peer,
            "mid_ratio": float(mid_ratio),
            "mid_peer": float(mid_peer_val),
            "mid_v_ratio": float(mid_v_ratio),
            "mid_i_ratio": float(mid_i_ratio),
            "coverage": float(coverage),
            "co_drop_frac": float(co_drop_frac),
            "recovered_any": bool(recovered_any),
            "recovered_sustained": bool(recovered_sustained),
            "re_drop": bool(re_drop),
            "coverage_mid": float(coverage_mid),
            "seg_count": int(seg_count),
            "total_low_mins": int(total_low_mins),
            "min_ratio": float(min_ratio),
            "p10_ratio": float(p10_ratio),
            "p50_ratio": float(p50_ratio),
            "low_area": float(low_area),
        }

    return out


# ========= Autoencoder =========

class AE(nn.Module):
    def __init__(self, dim: int = 96, latent: int = 16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(dim, 64),
            nn.ReLU(),
            nn.Linear(64, latent),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent, 64),
            nn.ReLU(),
            nn.Linear(64, dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        out = self.decoder(z)
        return out


def train_ae(train_mat: np.ndarray, latent: int, epochs: int, device: str) -> Tuple[AE, np.ndarray]:
    x = torch.tensor(train_mat, dtype=torch.float32)
    model = AE(dim=train_mat.shape[1], latent=latent).to(device)
    opt = optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()

    ds = torch.utils.data.TensorDataset(x)
    loader = torch.utils.data.DataLoader(ds, batch_size=64, shuffle=True)

    model.train()
    for _ in range(epochs):
        for (batch,) in loader:
            batch = batch.to(device)
            opt.zero_grad()
            rec = model(batch)
            loss = loss_fn(rec, batch)
            loss.backward()
            opt.step()

    model.eval()
    with torch.no_grad():
        rec = model(x.to(device)).cpu().numpy()
    train_err = ((train_mat - rec) ** 2).mean(axis=1)
    return model, train_err


# ========= CLI =========

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=False,
                    help="Input directory containing daily CSVs. Prefer --site for portable runs.")
    ap.add_argument("--site", default=None,
                    help="Site key to use data/<site>/raw as input (portable, recommended).")
    ap.add_argument("--data-root", default=None,
                    help="Project data root. Defaults to <project_root>/data if omitted.")
    ap.add_argument("--out-dir", default=None,
                    help="Output directory. Defaults to data/<site>/out (or <dir>/out).")
    ap.add_argument("--log-dir", default=None,
                    help="Log directory. Defaults to data/<site>/log (or <dir>/log).")
    ap.add_argument("--pattern", default="*.csv")
    ap.add_argument("--train-start", required=True)
    ap.add_argument("--train-end", required=True)
    ap.add_argument("--eval-start", required=True)
    ap.add_argument("--eval-end", required=True)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--latent", type=int, default=16)
    ap.add_argument("--contam", type=float, default=0.10)
    ap.add_argument("--recon-mult", type=float, default=1.0)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--seed", type=int, default=42,
                    help="Random seed for reproducible training/eval (default 42).")
    # 튜닝 단계 스위치 (엄격 진행)
    ap.add_argument(
        "--tuning-level",
        choices=["p0", "p1", "p2"],
        default="p2",
        help=(
            "Tuning stage switch. p0=baseline(dead/confirmed only), p1=+group_off_like gate, p2=full (critical/shadow/EWS/etc)."
        ),
    )

    # 룰 파라미터
    ap.add_argument("--sustain-mins", type=int, default=40)
    ap.add_argument("--drop-thr", type=float, default=0.90)
    ap.add_argument("--sustain-thr", type=float, default=0.80)
    ap.add_argument("--last-ratio-thr", type=float, default=0.80)
    ap.add_argument("--last-peer-thr", type=float, default=0.40)

    # 추가 룰 파라미터
    ap.add_argument("--event-sustain-mins", type=int, default=15)
    ap.add_argument("--mid-peer-alive-thr", type=float, default=0.5)
    ap.add_argument("--mid-ratio-dead-thr", type=float, default=0.2)

    # critical-like (V-drop) parameters (for bypass-diode-short-like patterns)
    # NOTE: In real systems, V-drop levels are not always exactly ~33%.
    # We therefore prefer a *relative* drop vs per-(date, group_key) peer V reference.
    ap.add_argument(
        "--v-drop-thr",
        type=float,
        default=0.20,
        help="Critical-like V-drop threshold expressed as v_drop = 1 - mid_v_ratio/v_ref (default 0.20).",
    )
    ap.add_argument(
        "--v-ref-min",
        type=float,
        default=0.30,
        help="Minimum v_ref (group median mid_v_ratio) required to evaluate v_drop (default 0.30).",
    )
    ap.add_argument(
        "--v-ref-vspan-max",
        type=float,
        default=0.12,
        help="Maximum allowed v_ref span (p90-p10 of mid_v_ratio within (date,group_key)) to trust v_ref/v_drop (default 0.12).",
    )
    ap.add_argument(
        "--v-ref-min-n",
        type=int,
        default=6,
        help="Minimum number of reference panels within (date, group_key) required to trust v_ref/v_drop (default 6).",
    )

    # Backward-compat (legacy): keep old absolute threshold; not used when v_drop is available.
    ap.add_argument(
        "--mid-v-ratio-critical-thr",
        type=float,
        default=0.75,
        help="(Legacy) Absolute critical-like threshold for mid_v_ratio. Prefer --v-drop-thr.",
    )
    ap.add_argument(
        "--mid-i-ratio-healthy-thr",
        type=float,
        default=0.85,
        help="Healthy-ish current threshold for mid_i_ratio when labeling V-drop critical-like (default 0.85).",
    )
    ap.add_argument(
        "--critical_mid_ratio_min",
        type=float,
        default=0.40,
        help="Minimum mid_ratio required to treat V-drop as critical-like (exclude near-dead/off cases). Default 0.40.",
    )
    ap.add_argument(
        "--critical_mid_ratio_max",
        type=float,
        default=0.95,
        help="Maximum mid_ratio allowed for critical-like (exclude fully-normal days). Default 0.95.",
    )
    ap.add_argument(
        "--critical-days",
        type=int,
        default=5,
        help="Number of consecutive critical-like days to confirm critical_fault (default 5).",
    )

    # critical 2-stage split (confirmed vs suspect)
    ap.add_argument("--critical-peer-min", type=float, default=0.6,
                    help="Only evaluate critical stability on days with mid_peer >= this value (default 0.6).")
    ap.add_argument("--critical-vspan-max", type=float, default=0.12,
                    help="Max allowed v_span (p90-p10 of mid_v_ratio) for confirmed critical panels (default 0.12).")
    ap.add_argument("--critical-min-days", type=int, default=5,
                    help="Minimum number of critical-like days for confirmed critical panels (default 5).")

    # shadow-like refinement parameters
    ap.add_argument("--shadow-seg-min", type=int, default=2,
                    help="Minimum number of low segments (seg_count) for shadow_like refinement (default 2).")
    ap.add_argument("--shadow-min-ratio-floor", type=float, default=0.30,
                    help="Minimum min_ratio floor to keep shadow_like from capturing near-dead patterns (default 0.30).")
    ap.add_argument("--dead-days", type=int, default=2)
    ap.add_argument("--coverage-min", type=float, default=0.5)

    ap.add_argument("--ews-quantile", type=float, default=0.9,
                    help="전체 사이트 분포에서 EWS 롤링 지표 상위 분위수 (기본 0.9)")
    ap.add_argument("--ews-k-sigma", type=float, default=1.0,
                    help="월별 베이스라인(mean + k*sigma) 보정 시 사용할 k 값 (기본 1.0)")
    ap.add_argument("--dtw-band", type=int, default=12,
                    help="DTW Sakoe–Chiba band width (None/<=0 means unconstrained). Default 12 for length-96 curves.")
    ap.add_argument("--recovered-consec", type=int, default=3,
                    help="Recovered 판단 시 drop_thr 이상을 연속으로 만족해야 하는 최소 샘플 수 (기본 3).")
    ap.add_argument("--shadow-co-drop-thr", type=float, default=0.15,
                    help="shadow_like 정제 시 co_drop_frac(공간 동시성) 최소 임계값 (기본 0.15).")
    ap.add_argument("--recovered-sustain-mins", type=int, default=15,
                    help="Recovered_sustained 판단을 위한 최소 유지 시간(분). interval 기반으로 points로 변환.")
    ap.add_argument("--peer-eps", type=float, default=1e-6,
                    help="ratio 계산 시 peer baseline이 이 값보다 작으면 제외(division blow-up 방지).")
    ap.add_argument("--daylight-event-thr", type=float, default=0.2,
                    help="Event/daylight gate threshold on peerP_frac for compute_event_features (default 0.2; site override allowed).")
    ap.add_argument("--use-log-ratio", action="store_true",
                    help="AE 입력 ratio를 log1p(P)-log1p(peer)로 안정화하여 사용.")

    # group/string-level OFF-like detection (protect against mislabeling string events as panel faults)
    ap.add_argument("--group-off-min-panels", type=int, default=10,
                    help="(Group-level) If >= this many panels in the SAME group_key are simultaneously dead-like (state_dead) on a day, consider group-off candidate.")
    ap.add_argument("--group-off-min-frac", type=float, default=0.50,
                    help="(Group-level) Minimum dead-like fraction within group_key to consider group-off candidate.")
    ap.add_argument("--group-off-max-frac", type=float, default=1.00,
                    help="(Group-level) Maximum dead-like fraction within group_key (set high; site-wide protection is handled elsewhere).")
    ap.add_argument("--group-off-jaccard", type=float, default=0.80,
                    help="Jaccard similarity threshold between consecutive days' dead-like panel sets to confirm a persistent group-off event.")
    ap.add_argument("--group-off-allow-single-day", action="store_true",
                    help="If set, allow single-day group-off labeling even without consecutive-day set stability.")
    return ap.parse_args()


def main():
    args = parse_args()

    # ---- Reproducibility ----
    seed = int(getattr(args, "seed", 42))
    np.random.seed(seed)
    try:
        import random
        random.seed(seed)
    except Exception:
        pass
    try:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        # Best-effort determinism (may have perf impact)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except Exception:
        pass

    # ---- Portable path resolution (project-root relative) ----
    script_path = pathlib.Path(__file__).resolve()
    project_root = script_path.parents[1]  # pvdiag/

    # Determine data root
    if args.data_root is not None:
        data_root = pathlib.Path(args.data_root).expanduser().resolve()
    else:
        data_root = (project_root / "data").resolve()

    # Determine input directory
    if args.site:
        site = str(args.site).strip()
        data_dir = (data_root / site / "raw").resolve()
    elif args.dir:
        data_dir = pathlib.Path(args.dir).expanduser().resolve()
        site = None
    else:
        raise RuntimeError("Must provide either --site <name> or --dir <path>.")

    # Determine output/log directories
    if args.out_dir is not None:
        out_dir = pathlib.Path(args.out_dir).expanduser().resolve()
    else:
        out_dir = ((data_root / site / "out") if site else (data_dir / "out")).resolve()

    if args.log_dir is not None:
        log_dir = pathlib.Path(args.log_dir).expanduser().resolve()
    else:
        log_dir = ((data_root / site / "log") if site else (data_dir / "log")).resolve()

    out_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Record run configuration for reproducibility
    import sys
    from datetime import datetime
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_info_path = log_dir / f"run_{run_ts}.json"
    try:
        run_info = {
            "timestamp": run_ts,
            "cwd": str(pathlib.Path.cwd()),
            "script": str(script_path),
            "project_root": str(project_root),
            "data_root": str(data_root),
            "site": site,
            "data_dir": str(data_dir),
            "out_dir": str(out_dir),
            "log_dir": str(log_dir),
            "argv": sys.argv,
            "python": sys.version,
            "seed": seed,
        }
        run_info_path.write_text(json.dumps(run_info, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] wrote run config: {run_info_path}")
    except Exception as e:
        print(f"[WARN] failed to write run config: {e}")

    if not data_dir.exists():
        raise RuntimeError(f"input directory not found: {data_dir}")

    def in_range(p: pathlib.Path, s: str, e: str) -> bool:
        """Filename date filter.
        - Extracts first occurrence of YYYY-MM-DD anywhere in the filename.
        - Compares as dates to avoid lexicographic corner cases.
        """
        d = extract_date_from_filename(p.name)
        if pd.isna(d):
            return False
        sdt = pd.to_datetime(s, errors="coerce").normalize()
        edt = pd.to_datetime(e, errors="coerce").normalize()
        if pd.isna(sdt) or pd.isna(edt):
            return False
        return (d >= sdt) and (d <= edt)

    files = sorted(
        p for p in data_dir.glob(args.pattern)
        if p.is_file() and p.suffix.lower() == ".csv"
    )

    print(f"[INFO] input_dir = {data_dir}")
    print(f"[INFO] out_dir   = {out_dir}")
    print(f"[INFO] log_dir   = {log_dir}")

    train_files = [p for p in files if in_range(p, args.train_start, args.train_end)]
    eval_files = [p for p in files if in_range(p, args.eval_start, args.eval_end)]

    # Diagnostics: show detected date range in filenames
    try:
        import re
        ds = []
        for p in files:
            m = re.search(r"(\d{4}-\d{2}-\d{2})", p.name)
            if m:
                d = pd.to_datetime(m.group(1), errors="coerce")
                if pd.notna(d):
                    ds.append(d)
        if ds:
            print(f"[INFO] detected file date range: {min(ds).date()} ~ {max(ds).date()} (n={len(ds)})")
    except Exception:
        pass

    if not train_files:
        raise RuntimeError(
            f"no training files in range: {args.train_start} ~ {args.train_end} (pattern={args.pattern})"
        )
    if not eval_files:
        raise RuntimeError(
            f"no eval files in range: {args.eval_start} ~ {args.eval_end} (pattern={args.pattern})"
        )

    # ===== Build train-only voltage-bin map (vbin) for stable group references =====
    # This prevents mixed-string designs from inflating v_ref_span and forcing legacy critical.
    vbin_map: dict[str, int] = {}
    vbin_diag: dict[str, any] = {}
    try:
        vbin_map, vbin_diag = build_vbin_map_from_train(
            train_files=train_files,
            critical_peer_min=float(args.critical_peer_min),
            mid_peer_alive_thr=float(args.mid_peer_alive_thr),
            mid_ratio_dead_thr=float(args.mid_ratio_dead_thr),
            coverage_min=float(args.coverage_min),
        )
        # Persist for reproducibility
        (log_dir / "vbin_map.json").write_text(
            json.dumps(vbin_map, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (log_dir / "vbin_diag.json").write_text(
            json.dumps(vbin_diag, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[OK] wrote vbin_map.json (n={len(vbin_map)}) and vbin_diag.json")
    except Exception as e:
        print(f"[WARN] failed to build vbin_map (will run without vbin split): {e}")
        vbin_map = {}

    # ===== AE 학습 (정상 기간) =====
    X_train: List[np.ndarray] = []
    train_index: List[Tuple[str, str]] = []
    train_curves_by_pid: Dict[str, List[np.ndarray]] = {}

    for p in tqdm(train_files, desc="train-curves"):
        curves = load_day_curves(p, peer_eps=float(args.peer_eps), use_log_ratio=bool(args.use_log_ratio))
        fname = p.name
        for pid, curve in curves.items():
            X_train.append(curve)
            train_index.append((fname, pid))
            train_curves_by_pid.setdefault(pid, []).append(curve)

    if not X_train:
        raise RuntimeError("no training curves")

    X_train_mat = np.vstack(X_train)
    # Compute global and per-panel reference curves
    global_ref_curve = np.median(X_train_mat, axis=0)
    panel_ref: Dict[str, np.ndarray] = {}
    for pid, lst in train_curves_by_pid.items():
        panel_ref[pid] = np.median(np.vstack(lst), axis=0)

    device = args.device

    model, train_err = train_ae(X_train_mat, args.latent, args.epochs, device)
    ae_thr_ae = float(np.quantile(train_err, 1.0 - args.contam))

    # ===== 평가 (고장 후보 기간) =====
    rows = []
    with torch.no_grad():
        for p in tqdm(eval_files, desc="eval"):
            csv_path = p
            fname = p.name

            # 이벤트 feature 계산
            ev_map = compute_event_features(
                csv_path,
                drop_thr=args.drop_thr,
                sustain_thr=args.sustain_thr,
                recovered_consec=int(args.recovered_consec),
                recovered_sustain_mins=int(args.recovered_sustain_mins),
                co_drop_thr=float(args.shadow_co_drop_thr),
                daylight_event_thr=float(getattr(args, "daylight_event_thr", 0.2)),
                peer_eps=float(args.peer_eps),
            )

            curves = load_day_curves(csv_path, peer_eps=float(args.peer_eps), use_log_ratio=bool(args.use_log_ratio))
            for pid, curve in curves.items():
                x = torch.tensor(curve[None, :], dtype=torch.float32).to(device)
                rec = model(x).cpu().numpy()[0]
                recon_err = float(np.mean((curve - rec) ** 2))

                ev = ev_map.get(str(pid), {})
                drop_time = ev.get("drop_time", "")
                sustain_mins = int(ev.get("sustain_mins", 0))
                recovered = bool(ev.get("recovered", False))
                last_ratio = float(ev.get("last_ratio", np.nan))
                last_peer = float(ev.get("last_peer", np.nan))
                mid_ratio = float(ev.get("mid_ratio", np.nan))
                mid_peer = float(ev.get("mid_peer", np.nan))
                mid_v_ratio = float(ev.get("mid_v_ratio", np.nan))
                mid_i_ratio = float(ev.get("mid_i_ratio", np.nan))
                coverage = float(ev.get("coverage", np.nan))
                co_drop_frac = float(ev.get("co_drop_frac", np.nan))
                recovered_any = bool(ev.get("recovered_any", False))
                recovered_sustained = bool(ev.get("recovered_sustained", False))
                re_drop = bool(ev.get("re_drop", False))
                coverage_mid = float(ev.get("coverage_mid", np.nan))
                seg_count = int(ev.get("seg_count", 0))
                total_low_mins = int(ev.get("total_low_mins", 0))
                min_ratio = float(ev.get("min_ratio", np.nan))
                p10_ratio = float(ev.get("p10_ratio", np.nan))
                p50_ratio = float(ev.get("p50_ratio", np.nan))
                low_area = float(ev.get("low_area", np.nan))

                is_ae_abn = recon_err >= ae_thr_ae
                is_ae_strong = recon_err >= (args.recon_mult * ae_thr_ae)

                # --- DTW & HS ---
                ref_curve = panel_ref.get(pid, global_ref_curve)
                band = int(args.dtw_band)
                dtw = float(dtw_distance(curve, ref_curve, band=None if band <= 0 else band))
                hs = float(compute_hs(curve))

                # --- V-drop reference & labels are computed AFTER dataframe-level v_ref merge ---

                # (Remove per-row cache to avoid duplicate computation / label overwrite.)

                group_key = panel_group_key(pid)

                vbin = vbin_map.get(pid, 0)

                group_key_ref = f"{group_key}.v{vbin}"


                # Placeholders (computed post-merge)
                v_ref = np.nan
                v_ref_span = np.nan
                n_ref = np.nan
                n_total = np.nan
                v_ref_ok = False
                v_drop = np.nan


                # Assemble output row with required fields
                rows.append(
                    {
                        "date": extract_date_from_filename(fname),
                        "panel_id": str(pid),
                        "v_ref_ok": v_ref_ok,
                        "v_drop": v_drop,
                        "v_ref": v_ref,
                        "v_ref_span": v_ref_span,
                        "n_ref": n_ref,
                        "n_total": n_total,
                        "group_key_ref": group_key_ref,
                        "recon_error": recon_err,
                        "ae_thr_used": ae_thr_ae,
                        "drop_time": drop_time,
                        "sustain_mins": sustain_mins,
                        "recovered": recovered,
                        "last_ratio": last_ratio,
                        "last_peer": last_peer,
                        "mid_ratio": mid_ratio,
                        "mid_peer": mid_peer,
                        "mid_v_ratio": mid_v_ratio,
                        "mid_i_ratio": mid_i_ratio,
                        "coverage": coverage,
                        "co_drop_frac": co_drop_frac,
                        "is_ae_abn": bool(is_ae_abn),
                        "is_ae_strong": bool(is_ae_strong),
                        "source_csv": fname,
                        "dtw_dist": dtw,
                        "hs_score": hs,
                        "recovered_any": recovered_any,
                        "recovered_sustained": recovered_sustained,
                        "re_drop": re_drop,
                        "coverage_mid": coverage_mid,
                        "seg_count": seg_count,
                        "total_low_mins": total_low_mins,
                        "min_ratio": min_ratio,
                        "p10_ratio": p10_ratio,
                        "p50_ratio": p50_ratio,
                        "low_area": low_area,
                    }
                )

    out = pd.DataFrame(rows)
    # Normalize date to midnight to avoid merge key mismatches
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
    out["drop_time"] = pd.to_datetime(out["drop_time"], errors="coerce")

    cov_min = float(args.coverage_min)
    tuning_level = str(getattr(args, "tuning_level", "p2")).lower().strip()
    if tuning_level not in {"p0", "p1", "p2"}:
        tuning_level = "p2"
    print(f"[INFO] tuning_level = {tuning_level}")
    print(f"[INFO] daylight_event_thr = {float(getattr(args, 'daylight_event_thr', 0.2))}")
    print("[INFO] segment-labeling: confirmed_fault/critical_fault now mark whole sustained segments (not only tail days)")

    # rule-based flags
    out["event_A"] = out["drop_time"].notna() & (out["sustain_mins"] >= int(args.event_sustain_mins))
    out["data_bad"] = (out["coverage"] < cov_min) | (out["coverage_mid"].fillna(0.0) < cov_min)

    # ---- Group-aware V reference and relative V-drop (for critical_like) ----
    # Goal: derive a per-(date, group_key) voltage reference from good rows, then compute
    #       v_drop = 1 - (mid_v_ratio / v_ref).
    # Key requirement: NEVER crash when v_ref is unavailable. Always keep `v_ref` column.

    # Base group_key (string-like) from panel_id
    out["group_key_base"] = out["panel_id"].astype(str).map(panel_group_key)

    # vbin-aware group_key: split base group when train-only medians show mixed voltage levels.
    # IMPORTANT: vbin is fixed from TRAIN only to avoid leakage and day-to-day instability.
    if isinstance(vbin_map, dict) and len(vbin_map) > 0:
        vb = out["panel_id"].astype(str).map(lambda s: vbin_map.get(str(s), 0)).astype(int)
        out["vbin"] = vb
        out["group_key"] = out["group_key_base"].astype(str) + ".v" + vb.astype(str)
    else:
        out["vbin"] = 0
        out["group_key"] = out["group_key_base"].astype(str)

    # A안 적용: v_ref(전압 참조)는 vbin까지 포함한 group_key 단위로 계산한다.
    # 이유: base group_key_ref(=uuid.string) 안에 서로 다른 설계/MPPT 전압 스트링이 섞이면
    #       v_ref_span이 폭발하고 v_ref_ok가 막혀 v_drop 판정이 불안정해진다.
    # 따라서 v_ref를 (date, group_key=vbin 포함) 기준으로 산출/적용하여 혼선을 제거한다.
    out["group_key_ref"] = out["group_key"].astype(str)

    # Ensure n_total is always available for downstream v_ref_ok logic and for CSV outputs.
    # n_total = number of unique panels per (date, group_key). Always recompute from the raw rows
    # so it is never missing even when v_ref is unavailable.
    out["n_total"] = out.groupby(["date", "group_key"])["panel_id"].transform("nunique").astype(float)

    # If this script is re-run in an interactive environment, or if the dataframe is
    # processed twice by accident, prior merge artifacts can remain and cause pandas
    # suffixes (_x/_y), which then breaks downstream v_ref_span selection and can leave
    # v_drop as all-NaN. Clean them up before recomputing.
    _merge_artifact_cols = [
        c for c in out.columns
        if (
            c.startswith("v_ref_tmp")
            or c.startswith("v_p10_grp")
            or c.startswith("v_p90_grp")
            or c.startswith("v_ref_span_grp")
        )
    ]
    if _merge_artifact_cols:
        out = out.drop(columns=_merge_artifact_cols)

    # Always materialize columns up-front to avoid KeyError in any branch.
    # IMPORTANT: v_ref/v_drop must preserve NaN when unusable.
    # Setting v_drop=0.0 on missing v_ref hides data-quality issues and can cause unintended fallback behaviour.
    out["v_ref"] = pd.to_numeric(out.get("v_ref", np.nan), errors="coerce")
    out["v_drop"] = np.nan
    out["v_ref_span"] = np.nan  # group-level span only (avoid merge collisions)
    out["n_ref"] = np.nan
    out["no_ref"] = False

    # Convenience flag: whether v_ref is usable for v_drop evaluation.
    # NOTE: v_ref_ok MUST be recomputed after v_ref is derived (merge step below).
    out["v_ref_ok"] = out["v_ref"].notna() & (out["v_ref"] >= float(args.v_ref_min))

    if tuning_level == "p2":
        # For building v_ref only, we must not over-gate by mid_peer.
        # Gangui finding: clear-day mid_peer can sit around ~0.4 depending on daylight/mid-window definition.
        # Use a slightly more permissive peer threshold ONLY for v_ref computation (no leakage; still uses eval-day rows).
        vref_peer_min = min(float(args.mid_peer_alive_thr), 0.35)
        # Exclude near-dead/off panels from V reference computation.
        # Otherwise a panel/string OFF event can leak into v_ref and distort v_drop.
        dead_like_tmp = (
            (~out["data_bad"].astype(bool))
            & (out["mid_peer"] >= float(vref_peer_min))
            & (out["mid_ratio"] <= float(args.mid_ratio_dead_thr))
        )

        base_mask = (
            (~out["data_bad"].astype(bool))
            & (out["mid_peer"] >= float(vref_peer_min))
            & (np.isfinite(out["mid_v_ratio"]))
            & (~dead_like_tmp)
        )

        if base_mask.any():
            # Robust healthy-cluster v_ref: use upper cluster to avoid low-V contamination
            def _vref_robust_stats(x: pd.Series) -> pd.Series:
                xx = pd.to_numeric(x, errors="coerce").astype(float)
                xx = xx[np.isfinite(xx)]
                if len(xx) == 0:
                    return pd.Series({"v_ref_tmp": np.nan, "v_p10_grp": np.nan, "v_p90_grp": np.nan, "n_ref": 0})

                # Use the upper cluster as the reference (protect against low-V fault contamination)
                # Keep it simple and deterministic: filter by an upper quantile then take median.
                q = float(np.nanquantile(xx, 0.60))
                xh = xx[xx >= q]
                if len(xh) < 2:
                    xh = xx  # fallback when too few remain

                return pd.Series({
                    "v_ref_tmp": float(np.nanmedian(xh)),
                    "v_p10_grp": float(np.nanquantile(xh, 0.10)) if len(xh) > 0 else np.nan,
                    "v_p90_grp": float(np.nanquantile(xh, 0.90)) if len(xh) > 0 else np.nan,
                    "n_ref": int(len(xh)),
                })

            # NOTE: pandas groupby.apply with `as_index=False` can produce length/index
            # mismatches when the applied function returns a Series. Use groupby.apply
            # (without as_index=False) and reset_index safely.
            v_ref_tbl = (
                out.loc[base_mask]
                .groupby(["date", "group_key_ref"])
                .apply(lambda g: _vref_robust_stats(g["mid_v_ratio"]))
                .reset_index()
            )
            v_ref_tbl["v_ref_span_grp"] = v_ref_tbl["v_p90_grp"] - v_ref_tbl["v_p10_grp"]
            # dtype guards (avoid object columns after apply)
            for c in ["v_ref_tmp", "v_p10_grp", "v_p90_grp", "v_ref_span_grp", "n_ref"]:
                if c in v_ref_tbl.columns:
                    v_ref_tbl[c] = pd.to_numeric(v_ref_tbl[c], errors="coerce")

            # Normalize date for safe merge (guard against time components)
            v_ref_tbl["date"] = pd.to_datetime(v_ref_tbl["date"], errors="coerce").dt.normalize()

            # Persist v_ref table for debugging/ops visibility
            try:
                v_ref_tbl.to_csv(log_dir / "v_ref_tbl.csv", index=False)
                print(f"[OK] wrote v_ref_tbl.csv (n={len(v_ref_tbl)})")
                print("[DBG] v_ref_tbl rows by date (top 10):")
                print(v_ref_tbl.groupby(v_ref_tbl["date"].dt.date).size().sort_values(ascending=False).head(10).to_string())
            except Exception as e:
                print(f"[WARN] failed to write v_ref_tbl.csv: {e}")

            # Merge with a TEMP column name to avoid pandas suffix traps.
            if len(v_ref_tbl) > 0:
                # Extra guard: normalize out["date"] before merge (in case other code paths modified it)
                out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
                out = out.merge(v_ref_tbl, on=["date", "group_key_ref"], how="left")

                # Recover v_ref_tmp even if pandas added suffixes.
                if "v_ref_tmp" not in out.columns:
                    for cand in ["v_ref_tmp_y", "v_ref_tmp_x"]:
                        if cand in out.columns:
                            out["v_ref_tmp"] = out[cand]
                            break

                # Choose the best available span column by non-null count.
                span_candidates = [c for c in out.columns if c.startswith("v_ref_span_grp")]
                span_col = None
                if span_candidates:
                    nn = {c: int(pd.to_numeric(out[c], errors="coerce").notna().sum()) for c in span_candidates}
                    span_col = max(nn, key=nn.get)

                # Capture n_ref column name (may be suffixed after merges)
                nref_col = None
                for cand in ["n_ref", "n_ref_y", "n_ref_x"]:
                    if cand in out.columns:
                        nref_col = cand
                        break

                if "v_ref_tmp" in out.columns:
                    # Stable, non-suffixed outputs
                    out["v_ref"] = pd.to_numeric(out["v_ref_tmp"], errors="coerce")
                    out["n_ref"] = pd.to_numeric(out[nref_col], errors="coerce") if nref_col is not None else np.nan
                    # Keep n_total stable: recompute from rows (do not trust merge artifacts).
                    out["n_total"] = out.groupby(["date", "group_key"])["panel_id"].transform("nunique").astype(float)

                    if span_col is not None:
                        out["v_ref_span"] = pd.to_numeric(out[span_col], errors="coerce")
                    else:
                        out["v_ref_span"] = np.nan

                    # v_ref_ok: usable v_ref AND stable group span AND enough reference panels
                    v_ref_min_n = int(getattr(args, "v_ref_min_n", 6))
                    span_ok = out["v_ref_span"].notna() & (out["v_ref_span"] <= float(args.v_ref_vspan_max))

                    # Adaptive min-N based on reference-bin availability within (date, group_key_ref)
                    # (i.e., how many v1 panels exist to form a stable voltage reference).
                    v_ref_min_n = int(getattr(args, "v_ref_min_n", 6))
                    required_n = out["n_total"].apply(lambda x: max(2, min(v_ref_min_n, int(x))) if pd.notna(x) else v_ref_min_n)
                    n_ok = out["n_ref"].notna() & (out["n_ref"] >= required_n)
                    out["v_ref_ok"] = out["v_ref"].notna() & (out["v_ref"] >= float(args.v_ref_min)) & span_ok & n_ok

                    # no_ref: reference not available or too small (ops visibility)
                    out["no_ref"] = out["v_ref"].isna() | (~n_ok)

                    # Drop merge helper columns (including any suffixed variants)
                    drop_cols = []
                    for c in [
                        "v_ref_tmp", "v_ref_tmp_x", "v_ref_tmp_y",
                        "v_p10_grp", "v_p10_grp_x", "v_p10_grp_y",
                        "v_p90_grp", "v_p90_grp_x", "v_p90_grp_y",
                        "n_ref_x", "n_ref_y",
                        "v_ref_span_grp", "v_ref_span_grp_x", "v_ref_span_grp_y",
                    ]:
                        # Keep stable output columns `n_ref` and `n_total`; drop only temporary/suffixed merge helpers.
                        if c in out.columns and c not in {"n_ref", "n_total"}:
                            drop_cols.append(c)
                    if drop_cols:
                        out = out.drop(columns=drop_cols)

                    # Compute relative V-drop using group reference.
                    # Keep NaN when v_ref is missing/unusable; do NOT default to 0.0.
                    out["v_drop"] = np.nan

                    # Ensure numeric dtypes (avoid silent all-False masks when objects sneak in)
                    out["mid_v_ratio"] = pd.to_numeric(out["mid_v_ratio"], errors="coerce")
                    out["v_ref"] = pd.to_numeric(out["v_ref"], errors="coerce")

                    drop_mask = (
                        out["v_ref"].notna()
                        & out["mid_v_ratio"].notna()
                        & np.isfinite(out["mid_v_ratio"].to_numpy(dtype=float))
                        & np.isfinite(out["v_ref"].to_numpy(dtype=float))
                        & (out["v_ref"] > 0)
                    )
                    out.loc[drop_mask, "v_drop"] = 1.0 - (
                        out.loc[drop_mask, "mid_v_ratio"].astype(float)
                        / out.loc[drop_mask, "v_ref"].astype(float)
                    )
                    # Safety: n_total must never be missing.
                    out["n_total"] = out.groupby(["date", "group_key"])["panel_id"].transform("nunique").astype(float)

    out["state_dead"] = (
        (~out["data_bad"])
        & (out["mid_peer"] >= float(args.mid_peer_alive_thr))
        & (out["mid_ratio"] <= float(args.mid_ratio_dead_thr))
    )

    # ---- Stage gating (p0/p1/p2) ----
    # p0: dead/confirmed only (no group_off gate, no critical/shadow/EWS)
    # p1: +group_off_like gate (still no critical/shadow/EWS)
    # p2: full (critical_like + group_off_like + downstream refinement)

    # ---- Ops visibility: why a row is low-trust (suspect) ----
    # Derived from FINAL (post-merge) trust-gate components.
    if "vdrop_trust_reason" not in out.columns:
        out["vdrop_trust_reason"] = ""

    try:
        v_ref_min_n = int(getattr(args, "v_ref_min_n", 6))
        v_ref_min = float(getattr(args, "v_ref_min", 0.30))
        v_ref_vspan_max = float(getattr(args, "v_ref_vspan_max", 0.12))

        n_ref_s = pd.to_numeric(out.get("n_ref", np.nan), errors="coerce")
        v_ref_s = pd.to_numeric(out.get("v_ref", np.nan), errors="coerce")
        vspan_s = pd.to_numeric(out.get("v_ref_span", np.nan), errors="coerce")

        # Match the adaptive required_n logic used in v_ref_ok computation.
        required_n = n_ref_s.apply(
            lambda x: (max(2, min(v_ref_min_n, int(x))) if pd.notna(x) else v_ref_min_n)
        )

        low_vref = v_ref_s.isna() | (~np.isfinite(v_ref_s.to_numpy(dtype=float))) | (v_ref_s < v_ref_min)
        high_vspan = vspan_s.isna() | (~np.isfinite(vspan_s.to_numpy(dtype=float))) | (vspan_s > v_ref_vspan_max)
        low_nref = n_ref_s.isna() | (~np.isfinite(n_ref_s.to_numpy(dtype=float))) | (n_ref_s < required_n)

        # Build reason strings (order-stable)
        r = np.where(low_vref, "low_v_ref", "")
        r = np.where(high_vspan, np.where(r != "", r + "+high_vspan", "high_vspan"), r)
        r = np.where(low_nref, np.where(r != "", r + "+low_n_ref", "low_n_ref"), r)

        # Only keep reason when FINAL trust is low (suspect); else keep blank.
        out["vdrop_trust_reason"] = np.where(out["v_ref_ok"].fillna(False).astype(bool), "", r)
    except Exception as _e:
        # Never fail the pipeline due to a diagnostics column.
        out["vdrop_trust_reason"] = ""

    # critical labels are finalized after group_off_like is known.

    out["group_off_date"] = False
    out["group_off_like"] = False
    out["group_off_group"] = False

    if tuning_level in {"p1", "p2"}:
        # ---- Group-off / string-off like event detection (group_key-level) ----
        # What we observed in Gangui:
        # - Only ~10~15% of site panels are dead-like on those days,
        # - but within specific group_key (string-like groups), dead_frac can be 50~80%.
        # Site-level detection is too coarse; it can over-gate unrelated panels.
        #
        # New behavior:
        # - Detect OFF-like events per (date, group_key)
        # - Mark only those panels in the affected group_key as group_off_like
        # - Keep group_off_date as a convenience (any group-off group on that date)

        out["group_off_group"] = False  # row-level: panel belongs to a group_key flagged as OFF-like on that date

        flagged_pairs: set[tuple[pd.Timestamp, str]] = set()

        # For each group_key, track previous day's dead-set to compute Jaccard stability
        prev_dead_set_by_gk: Dict[str, set] = {}
        prev_date_by_gk: Dict[str, pd.Timestamp] = {}
        prev_candidate_by_gk: Dict[str, bool] = {}

        # Iterate by date then by group_key
        for d in sorted(out["date"].dropna().unique()):
            gd = out[out["date"] == d]
            for gk, gg in gd.groupby("group_key"):
                # dead-like set within good data only (within this group)
                dead_set = set(
                    gg.loc[(~gg["data_bad"].astype(bool)) & (gg["state_dead"].astype(bool)), "panel_id"].astype(str).tolist()
                )
                n_dead = len(dead_set)
                n_total = int(gg["panel_id"].nunique())
                frac = (n_dead / n_total) if n_total > 0 else 0.0

                # Candidate definition is applied per-group now.
                candidate = (
                    (n_dead >= int(args.group_off_min_panels))
                    & (frac >= float(args.group_off_min_frac))
                    & (frac <= float(args.group_off_max_frac))
                )

                confirmed_today = False

                # Allow single-day labeling when explicitly enabled
                if candidate and bool(args.group_off_allow_single_day):
                    confirmed_today = True

                # Consecutive-day stability check (Jaccard)
                if candidate and prev_candidate_by_gk.get(gk, False):
                    prev_dead = prev_dead_set_by_gk.get(gk)
                    if prev_dead is not None:
                        inter = len(dead_set & prev_dead)
                        union = len(dead_set | prev_dead)
                        jacc = (inter / union) if union > 0 else 0.0
                        if jacc >= float(args.group_off_jaccard):
                            confirmed_today = True
                            # also mark previous day as group-off for this group_key
                            prev_d = prev_date_by_gk.get(gk)
                            if prev_d is not None:
                                flagged_pairs.add((prev_d, gk))

                if confirmed_today:
                    flagged_pairs.add((d, gk))

                # update trackers
                prev_dead_set_by_gk[gk] = dead_set
                prev_date_by_gk[gk] = d
                prev_candidate_by_gk[gk] = bool(candidate)

        if flagged_pairs:
            # row-level membership in flagged (date, group_key)
            pair_series = list(zip(out["date"], out["group_key"]))
            out["group_off_group"] = [((dd, ggk) in flagged_pairs) for (dd, ggk) in pair_series]

        # convenience flag: any group-off group exists on that date
        group_dates = {dd for (dd, _gk) in flagged_pairs}
        out["group_off_date"] = out["date"].isin(group_dates)

        # group_off_like is now precise: only dead-like panels in the flagged group_key
        out["group_off_like"] = (
            out["group_off_group"].astype(bool)
            & (~out["data_bad"].astype(bool))
            & out["state_dead"].astype(bool)
        )
        # --- P1/P2 safety: group_off_like must never contribute to V-drop/critical signals ---
        # Rationale: group/string OFF events can produce apparent V-drop rows and confuse downstream checks.
        # We keep group_off_like as its own category and mask V-drop-related fields on those rows.
        go_mask = out["group_off_like"].fillna(False).astype(bool)
        if go_mask.any():
            out.loc[go_mask, "v_drop"] = np.nan
            out.loc[go_mask, "v_ref_ok"] = False
            # keep ops visibility: treat as no usable reference for these rows
            if "no_ref" in out.columns:
                out.loc[go_mask, "no_ref"] = True

    # Effective dead for panel-fault confirmation
    # p0: no group_off gating
    # p1/p2: exclude group_off_like days
    if tuning_level == "p0":
        out["state_dead_eff"] = out["state_dead"].astype(bool)
    else:
        out["state_dead_eff"] = out["state_dead"].astype(bool) & (~out["group_off_like"].astype(bool))

    # Final critical labels (SSOT): define once after group_off_like is known.
    out = compute_vdrop_labels(
        out,
        {
            "args": args,
            "tuning_level": tuning_level,
        },
    )

    # dead streak and confirmed fault (always computed)
    out = out.sort_values(["panel_id", "date"])
    dead_streak = []
    current_panel = None
    cnt = 0
    for pid, is_dead in zip(out["panel_id"], out["state_dead_eff"]):
        if pid != current_panel:
            current_panel = pid
            cnt = 0
        if is_dead:
            cnt += 1
        else:
            cnt = 0
        dead_streak.append(cnt)
    out["dead_streak"] = dead_streak
    # Mark whole dead-like segments when they reach the minimum length (ops-friendly)
    out = mark_run_segments(out, key_col="panel_id", date_col="date", cond_col="state_dead_eff", min_len=int(args.dead_days), out_col="confirmed_fault")

    # ---- Critical-like (V-drop sustained run) ----
    out["crit_streak"] = 0
    out["critical_fault"] = False

    if tuning_level == "p2":
        # ---- Critical-like streak ----
        crit_streak = []
        current_panel = None
        cnt = 0
        for pid, is_crit in zip(out["panel_id"], out["critical_like_eff"]):
            if pid != current_panel:
                current_panel = pid
                cnt = 0
            if bool(is_crit):
                cnt += 1
            else:
                cnt = 0
            crit_streak.append(cnt)
        out["crit_streak"] = crit_streak
        # Mark whole critical-like segments when they reach the minimum length (ops-friendly)
        out = mark_run_segments(out, key_col="panel_id", date_col="date", cond_col="critical_like_eff", min_len=int(args.critical_days), out_col="critical_fault")

    # ===== critical 2-stage split (confirmed vs suspect) =====
    # Compute after `critical_fault` is available.
    out["critical_confirmed"] = False
    out["critical_suspect"] = False
    # Ops-friendly stage label (none/like/suspect/confirmed)
    out["critical_stage"] = "none"

    if tuning_level == "p2":
        crit_rows = out[(out["critical_fault"] == True) & (out["mid_peer"] >= float(args.critical_peer_min))].copy()
        if len(crit_rows) > 0:
            g = (crit_rows.groupby("panel_id")
                         .agg(days=("date", "nunique"),
                              v_p10=("mid_v_ratio", lambda x: x.quantile(0.10)),
                              v_p90=("mid_v_ratio", lambda x: x.quantile(0.90)))
                         .reset_index())
            g["v_span"] = g["v_p90"] - g["v_p10"]

            confirmed_panels = set(
                g[(g["days"] >= int(args.critical_min_days)) & (g["v_span"] <= float(args.critical_vspan_max))]["panel_id"].astype(str).tolist()
            )
            suspect_panels = set(
                g[(g["days"] >= int(args.critical_min_days)) & (g["v_span"] > float(args.critical_vspan_max))]["panel_id"].astype(str).tolist()
            )

            out.loc[out["panel_id"].astype(str).isin(confirmed_panels) & (out["critical_fault"] == True), "critical_confirmed"] = True
            out.loc[out["panel_id"].astype(str).isin(suspect_panels) & (out["critical_fault"] == True), "critical_suspect"] = True
            # Stage labeling priority: confirmed > suspect > like
            out.loc[out["critical_like_eff"].astype(bool), "critical_stage"] = "like"
            out.loc[out["critical_suspect"].astype(bool), "critical_stage"] = "suspect"
            out.loc[out["critical_confirmed"].astype(bool), "critical_stage"] = "confirmed"

    # final_fault
    if tuning_level == "p2":
        # Final fault should only use CONFIRMED critical (V/I-decomposed and stability-checked).
        # Anything else stays as critical_like / critical_suspect for downstream review.
        out["final_fault"] = out["confirmed_fault"] | out["critical_confirmed"]
    else:
        out["final_fault"] = out["confirmed_fault"]

    # ---- Online diagnosis dates (panel-wise first confirmed day) ----
    # Keep date normalization explicit before first-true day extraction.
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()

    dead_days_thr = int(args.dead_days)
    critical_days_thr = int(args.critical_days)

    out["dead_diag_on_day"] = (
        out["state_dead_eff"].fillna(False).astype(bool)
        & (pd.to_numeric(out["dead_streak"], errors="coerce").fillna(0) >= dead_days_thr)
    )
    dead_diag_first = (
        out.loc[out["dead_diag_on_day"], ["panel_id", "date"]]
        .groupby("panel_id", sort=False)["date"]
        .min()
    )
    out["dead_diag_date"] = out["panel_id"].map(dead_diag_first)

    if tuning_level == "p2":
        out["critical_diag_on_day"] = (
            out["critical_like_eff"].fillna(False).astype(bool)
            & (pd.to_numeric(out["crit_streak"], errors="coerce").fillna(0) >= critical_days_thr)
        )
        critical_diag_first = (
            out.loc[out["critical_diag_on_day"], ["panel_id", "date"]]
            .groupby("panel_id", sort=False)["date"]
            .min()
        )
        out["critical_diag_date"] = out["panel_id"].map(critical_diag_first)
    else:
        out["critical_diag_on_day"] = False
        out["critical_diag_date"] = pd.NaT
        critical_diag_first = pd.Series(dtype="datetime64[ns]")

    out["diagnosis_date_online"] = pd.concat(
        [
            pd.to_datetime(out["dead_diag_date"], errors="coerce"),
            pd.to_datetime(out["critical_diag_date"], errors="coerce"),
        ],
        axis=1,
    ).min(axis=1)

    final_fault_first = (
        out.loc[out["final_fault"].fillna(False).astype(bool), ["panel_id", "date"]]
        .groupby("panel_id", sort=False)["date"]
        .min()
    )
    panel_diag = pd.DataFrame({"panel_id": out["panel_id"].astype(str).drop_duplicates()})
    panel_diag["dead_diag_date"] = panel_diag["panel_id"].map(dead_diag_first)
    panel_diag["critical_diag_date"] = panel_diag["panel_id"].map(critical_diag_first)
    panel_diag["diagnosis_date_online"] = pd.concat(
        [
            pd.to_datetime(panel_diag["dead_diag_date"], errors="coerce"),
            pd.to_datetime(panel_diag["critical_diag_date"], errors="coerce"),
        ],
        axis=1,
    ).min(axis=1)
    panel_diag["final_fault_first_date"] = panel_diag["panel_id"].map(final_fault_first)
    panel_diag["dead_days"] = dead_days_thr
    panel_diag["critical_days"] = critical_days_thr
    panel_diag["tuning_level"] = tuning_level
    panel_diag_path = out_dir / "ae_simple_panel_diagnosis.csv"
    panel_diag.to_csv(panel_diag_path, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote output: {panel_diag_path} (n={len(panel_diag)})")

    # Sanity checks for critical label consistency after single-pass SSOT assignment.
    try:
        bad_overlap = int(
            (
                out["critical_like_raw"].astype(bool)
                & out["critical_like_suspect_raw"].astype(bool)
            ).sum()
        )
        if bad_overlap > 0:
            raise AssertionError(
                f"critical raw overlap detected (n={bad_overlap}); raw and suspect_raw must be exclusive"
            )

        # Legacy path may legitimately bypass v_ref_ok; trust check applies to non-legacy rows only.
        leak_nonlegacy = int(
            (
                out["critical_like_eff"].astype(bool)
                & (~out["v_ref_ok"].fillna(False).astype(bool))
                & (~out["critical_like_legacy"].astype(bool))
            ).sum()
        )
        if leak_nonlegacy > 0:
            raise AssertionError(
                f"non-legacy critical leak detected with v_ref_ok==0 (n={leak_nonlegacy})"
            )
        print(f"[CHK] critical_raw_overlap = {bad_overlap}, nonlegacy_vref_leak = {leak_nonlegacy}")
    except Exception as _e:
        raise

    # ---- Reports: confirmed vs suspect (after final critical labels are fixed) ----
    try:
        if tuning_level == "p2":
            rep_confirm = _max_run_by_panel(out, "critical_like")
            rep_suspect = _max_run_by_panel(out, "critical_like_suspect")

            def _attach_ctx(df_run: pd.DataFrame, flag_col: str) -> pd.DataFrame:
                top_pids = df_run.loc[df_run[f"{flag_col}_max_run"] > 0, "panel_id"].astype(str).tolist()
                if not top_pids:
                    return df_run
                sub = out[out["panel_id"].astype(str).isin(top_pids)].copy()
                sub = sub.sort_values(["panel_id", "date"])
                ctx = (
                    sub.groupby("panel_id")
                    .tail(1)[
                        [
                            "panel_id",
                            "group_key_ref",
                            "n_ref",
                            "n_total",
                            "v_ref_span",
                            "mid_peer",
                            "mid_ratio",
                            "mid_v_ratio",
                            "v_drop",
                        ]
                    ]
                    .copy()
                )
                return df_run.merge(ctx, on="panel_id", how="left")

            rep_confirm_ctx = _attach_ctx(rep_confirm, "critical_like")
            rep_suspect_ctx = _attach_ctx(rep_suspect, "critical_like_suspect")

            try:
                rep_confirm_ctx.to_csv(log_dir / "report_critical_confirmed_runs.csv", index=False)
                rep_suspect_ctx.to_csv(log_dir / "report_critical_suspect_runs.csv", index=False)
                rep_confirm_ctx.to_csv(out_dir / "report_critical_confirmed_runs.csv", index=False)
                rep_suspect_ctx.to_csv(out_dir / "report_critical_suspect_runs.csv", index=False)
                print("[OK] wrote reports: report_critical_confirmed_runs.csv / report_critical_suspect_runs.csv")
            except Exception as _e:
                print(f"[WARN] failed to write critical reports: {_e}")

            print("\n[TOP] critical_like confirmed max_run (TOP40)")
            print(rep_confirm.head(40).to_string(index=False))
            print("\n[TOP] critical_like SUSPECT max_run (TOP40)")
            print(rep_suspect.head(40).to_string(index=False))
    except Exception as _e:
        print(f"[WARN] critical report generation failed: {_e}")

    # helper flags for daily fault-like events and degraded candidates
    fault_sustain = 90            # minutes of sustained low ratio to consider the day fault-like
    fault_last_ratio_thr = 0.10   # if last_ratio <= 0.1, treated as nearly dead at end of day
    degraded_upper = 0.60         # upper bound for degraded mid_ratio (0.2 ~ 0.6)

    out["fault_like_day"] = (
        (~out["data_bad"])
        & out["event_A"]
        & (out["sustain_mins"] >= fault_sustain)
        & (out["last_ratio"] <= fault_last_ratio_thr)
        & (out["mid_peer"] >= float(args.mid_peer_alive_thr))
    )

    out["degraded_candidate"] = (
        (~out["data_bad"])
        & (~out["state_dead"])
        & (out["mid_peer"] >= float(args.mid_peer_alive_thr))
        & (out["mid_ratio"] > float(args.mid_ratio_dead_thr))
        & (out["mid_ratio"] <= degraded_upper)
    )

    # shadow-like events (basic): degraded days that recovered at least once
    # NOTE: refined later using HS/DTW strengths to better match transient cloud/shading behaviour.
    out["shadow_like_basic"] = (
        (~out["data_bad"])
        & out["degraded_candidate"]
        & out["recovered_sustained"]
    )

    # Refined shadow-like: require spatial concurrence OR segmented behaviour, and avoid near-dead patterns
    out["shadow_like"] = (
        out["shadow_like_basic"]
        & (
            (out["co_drop_frac"].fillna(0.0) >= float(args.shadow_co_drop_thr))
            | (out["seg_count"].fillna(0).astype(int) >= int(args.shadow_seg_min))
        )
        & (out["min_ratio"].fillna(1.0) >= float(args.shadow_min_ratio_floor))
    )

    # Guard: group/string OFF events should not contaminate other event categories
    if "group_off_like" in out.columns:
        mask_go = out["group_off_like"].fillna(False).astype(bool)
        if mask_go.any():
            for col in ["fault_like_day", "degraded_candidate", "shadow_like_basic", "shadow_like"]:
                if col in out.columns:
                    out.loc[mask_go, col] = False

    # textual anomaly level for easier downstream use
    out["anom_level"] = "normal"
    out.loc[out["degraded_candidate"], "anom_level"] = "degraded_or_shadow"
    out.loc[out["shadow_like"], "anom_level"] = "shadow_like"
    out.loc[out["fault_like_day"], "anom_level"] = "fault_like"
    out.loc[out["group_off_like"], "anom_level"] = "group_off_like"
    out.loc[out["final_fault"], "anom_level"] = "confirmed_fault"

    # Layer 2: AE 기반 강도 / 서브타입 태깅
    # 날짜별 AE 재구성오차 분위수 (0~1)
    out["recon_rank_day"] = out.groupby("date")["recon_error"].rank(pct=True)

    # AE 강도 수준
    out["ae_strength"] = "low"
    out.loc[out["recon_rank_day"] >= 0.7, "ae_strength"] = "mid"
    out.loc[out["recon_rank_day"] >= 0.9, "ae_strength"] = "high"
    # is_ae_strong=True인 경우는 무조건 high로 승격
    out.loc[out["is_ae_strong"], "ae_strength"] = "high"

    # 이상 서브타입 태그
    out["anom_subtype"] = "normal"
    out.loc[out["group_off_like"], "anom_subtype"] = "group_off_event"

    # shadow-like: 음영/날씨성 이벤트를 AE 강도 기준으로 세분화
    out.loc[out["shadow_like"] & (~out["is_ae_strong"]), "anom_subtype"] = "shadow_like_mild"
    out.loc[out["shadow_like"] & out["is_ae_strong"], "anom_subtype"] = "shadow_like_strong"

    # 열화 후보: shadow_like로 이미 태깅된 패널은 제외하고, AE 강도로 구분
    out.loc[
        out["degraded_candidate"] & (~out["shadow_like"]) & (~out["is_ae_strong"]),
        "anom_subtype",
    ] = "degradation_mild"
    out.loc[
        out["degraded_candidate"] & (~out["shadow_like"]) & out["is_ae_strong"],
        "anom_subtype",
    ] = "degradation_strong"

    # 하루 고장 패턴: fault-like day
    out.loc[
        out["fault_like_day"] & (~out["is_ae_strong"]),
        "anom_subtype",
    ] = "fault_like_weak"
    out.loc[
        out["fault_like_day"] & out["is_ae_strong"],
        "anom_subtype",
    ] = "fault_like_strong"

    # 최종 confirmed fault는 항상 confirmed_fault로 override
    out.loc[out["confirmed_fault"], "anom_subtype"] = "confirmed_fault"
    out.loc[(out["critical_fault"]) & (~out["confirmed_fault"]), "anom_subtype"] = "critical_fault_vdrop"

    # Layer 3: EWS(전조) 지표 – 4종 (mid_var, eventA_freq, dtw_mean, hs_mean)
    # 패널별 날짜 순으로 정렬 후 롤링 통계 계산
    out = out.sort_values(["panel_id", "date"])
    grp = out.groupby("panel_id", group_keys=False)

    # 1) 기본 롤링 지표 4개
    out["ews_mid_var_7d"] = grp["mid_ratio"].transform(
        lambda s: s.rolling(window=7, min_periods=3).var()
    )
    out["ews_eventA_freq_7d"] = grp["event_A"].transform(
        lambda s: s.rolling(window=7, min_periods=3).mean()
    )
    out["ews_dtw_mean_7d"] = grp["dtw_dist"].transform(
        lambda s: s.rolling(window=7, min_periods=3).mean()
    )
    out["ews_hs_mean_7d"] = grp["hs_score"].transform(
        lambda s: s.rolling(window=7, min_periods=3).mean()
    )

    # 2) 운영(인과성) 관점: 전역 임계값과 월별 베이스라인은 "과거 데이터"로만 산정
    #    - 날짜 d에서의 판단은 date < d 구간의 분포/베이스라인만 사용 (미래 데이터 누수 방지)

    # ==== EXPORT: Save main output CSV with n_total defensively included ====
    # Ensure n_total is exported for ops/debug (number of panels per (date, group_key))
    if "n_total" not in out.columns:
        out["n_total"] = out.groupby(["date", "group_key"])["panel_id"].transform("nunique").astype(float)

    # Define output columns (OUT_COLS): insert n_total after n_ref if present, else near v_ref-related cols
    OUT_COLS = [
        "date", "panel_id",
        "recon_error", "ae_thr_used",
        "drop_time", "sustain_mins", "recovered",
        "last_ratio", "last_peer",
        "mid_ratio", "mid_peer", "mid_v_ratio", "mid_i_ratio",
        "coverage", "co_drop_frac",
        "is_ae_abn", "is_ae_strong", "source_csv",
        "dtw_dist", "hs_score", "recovered_any", "recovered_sustained", "re_drop",
        "coverage_mid", "seg_count", "total_low_mins", "min_ratio", "p10_ratio", "p50_ratio", "low_area",
        "event_A", "data_bad",
        "group_key_base", "vbin", "group_key",
        "v_ref", "v_ref_span", "v_ref_ok", "n_ref",  # v_ref-related section
        # n_total will be inserted after n_ref or after v_ref-related cols below
        "no_ref", "v_drop",
        "state_dead", "state_dead_eff", "dead_streak", "confirmed_fault",
        "dead_diag_on_day", "dead_diag_date",
        "critical_like", "critical_like_eff", "crit_streak", "critical_fault", "critical_source",
        "critical_diag_on_day", "critical_diag_date", "diagnosis_date_online",
        "critical_confirmed", "critical_suspect", "final_fault",
        "group_off_date", "group_off_like", "group_off_group",
        "fault_like_day", "degraded_candidate", "shadow_like_basic", "shadow_like",
        "anom_level", "recon_rank_day", "ae_strength", "anom_subtype",
        "ews_mid_var_7d", "ews_eventA_freq_7d", "ews_dtw_mean_7d", "ews_hs_mean_7d"
    ]
    # Insert n_total after n_ref if present, else after v_ref_ok, v_ref_span, or v_ref
    if "n_total" not in OUT_COLS:
        try:
            idx = OUT_COLS.index("n_ref") + 1
        except ValueError:
            # Try after v_ref_ok or v_ref_span or v_ref
            for key in ["v_ref_ok", "v_ref_span", "v_ref"]:
                if key in OUT_COLS:
                    idx = OUT_COLS.index(key) + 1
                    break
            else:
                idx = len(OUT_COLS)
        OUT_COLS.insert(idx, "n_total")

    # Final save is performed once at the end of main().

    q = float(args.ews_quantile)
    k_sigma = float(args.ews_k_sigma)

    out["ews_month"] = out["date"].dt.month

    # Pre-allocate causal baseline columns (for transparency/debugging)
    out["mid_base_mean"] = np.nan
    out["mid_base_std"] = np.nan
    out["dtw_base_mean"] = np.nan
    out["dtw_base_std"] = np.nan
    out["hs_base_mean"] = np.nan
    out["hs_base_std"] = np.nan

    # Causal conditions (filled date-by-date)
    cond_var = pd.Series(False, index=out.index)
    cond_dtw = pd.Series(False, index=out.index)
    cond_hs = pd.Series(False, index=out.index)

    # eventA 빈도: 최근 7일 중 절반 이상 event_A 발생 (행 단위로 바로 계산 가능)
    cond_evt = out["ews_eventA_freq_7d"] >= 0.5

    # Date-by-date causal thresholds/baselines
    for d in sorted(out["date"].dropna().unique()):
        mask_d = out["date"] == d
        past = out.loc[out["date"] < d]

        # If no past, leave conditions as False for this date
        if past.empty:
            continue

        # Global (site-wide) thresholds from past only
        def _past_thr(series: pd.Series, qq: float) -> float:
            vals = series.to_numpy()
            if np.isfinite(vals).any():
                return float(np.nanquantile(vals, qq))
            return np.nan

        var_thr = _past_thr(past["ews_mid_var_7d"], q)
        dtw_thr = _past_thr(past["ews_dtw_mean_7d"], q)
        hs_thr = _past_thr(past["ews_hs_mean_7d"], q)

        # Panel×Month baseline from past only
        base = (
            past.groupby(["panel_id", "ews_month"])[
                ["ews_mid_var_7d", "ews_dtw_mean_7d", "ews_hs_mean_7d"]
            ]
            .agg(["mean", "std"])
        )

        # Helper to fetch baseline stats for current rows
        def _get_base(metric: str, stat: str) -> pd.Series:
            s = base[(metric, stat)]
            # align by (panel_id, ews_month)
            key = list(zip(out.loc[mask_d, "panel_id"], out.loc[mask_d, "ews_month"]))
            return pd.Series([s.get(k, np.nan) for k in key], index=out.index[mask_d])

        # Fill baseline columns for this date (debug visibility)
        out.loc[mask_d, "mid_base_mean"] = _get_base("ews_mid_var_7d", "mean")
        out.loc[mask_d, "mid_base_std"] = _get_base("ews_mid_var_7d", "std")
        out.loc[mask_d, "dtw_base_mean"] = _get_base("ews_dtw_mean_7d", "mean")
        out.loc[mask_d, "dtw_base_std"] = _get_base("ews_dtw_mean_7d", "std")
        out.loc[mask_d, "hs_base_mean"] = _get_base("ews_hs_mean_7d", "mean")
        out.loc[mask_d, "hs_base_std"] = _get_base("ews_hs_mean_7d", "std")

        # Apply both gates (global quantile + seasonal baseline) using past-only statistics
        if np.isfinite(var_thr) and var_thr > 0:
            cv = out.loc[mask_d, "ews_mid_var_7d"] >= var_thr
        else:
            cv = pd.Series(False, index=out.index[mask_d])
        mid_thr_base = out.loc[mask_d, "mid_base_mean"] + k_sigma * out.loc[mask_d, "mid_base_std"].fillna(0.0)
        cv = cv & out.loc[mask_d, "mid_base_mean"].notna() & (out.loc[mask_d, "ews_mid_var_7d"] >= mid_thr_base)
        cond_var.loc[mask_d] = cv.fillna(False)

        if np.isfinite(dtw_thr) and dtw_thr > 0:
            cd = out.loc[mask_d, "ews_dtw_mean_7d"] >= dtw_thr
        else:
            cd = pd.Series(False, index=out.index[mask_d])
        dtw_thr_base = out.loc[mask_d, "dtw_base_mean"] + k_sigma * out.loc[mask_d, "dtw_base_std"].fillna(0.0)
        cd = cd & out.loc[mask_d, "dtw_base_mean"].notna() & (out.loc[mask_d, "ews_dtw_mean_7d"] >= dtw_thr_base)
        cond_dtw.loc[mask_d] = cd.fillna(False)

        if np.isfinite(hs_thr) and hs_thr > 0:
            ch = out.loc[mask_d, "ews_hs_mean_7d"] >= hs_thr
        else:
            ch = pd.Series(False, index=out.index[mask_d])
        hs_thr_base = out.loc[mask_d, "hs_base_mean"] + k_sigma * out.loc[mask_d, "hs_base_std"].fillna(0.0)
        ch = ch & out.loc[mask_d, "hs_base_mean"].notna() & (out.loc[mask_d, "ews_hs_mean_7d"] >= hs_thr_base)
        cond_hs.loc[mask_d] = ch.fillna(False)

    # 패널-날짜별로 high 신호 개수 계산 (4개 중 2개 이상)
    signal_count = (
        cond_var.astype(int)
        + cond_evt.astype(int)
        + cond_dtw.astype(int)
        + cond_hs.astype(int)
    )

    # data_bad가 아니고, high 신호가 2개 이상인 날을 "잠정 전조 신호"로 본다.
    pre_ews = (~out["data_bad"]) & (signal_count >= 2)

    # 4) 연속성 조건: 같은 패널에서 5일 이상 연속 pre_ews가 유지되면 EWS 경고로 확정 (방안 C)
    ews_runlen: List[int] = []
    current_panel = None
    streak = 0
    for pid, flag in zip(out["panel_id"], pre_ews):
        if pid != current_panel:
            current_panel = pid
            streak = 0
        if flag:
            streak += 1
        else:
            streak = 0
        ews_runlen.append(streak)

    out["ews_runlen"] = ews_runlen

    out["ews_warning"] = False
    out.loc[pre_ews & (out["ews_runlen"] >= 5), "ews_warning"] = True

    # 이미 고장 확정(final_fault)인 날은 EWS 경고는 별도로 끈다
    out.loc[out["final_fault"], "ews_warning"] = False

    # ===== Site event day (soft/hard) + reason =====
    # Goal: protect ops from site-wide irradiance/weather/comm events.
    # Uses only per-day aggregates available in `out`.

    def _site_event_reason_for_day(g: pd.DataFrame) -> tuple[bool, bool, str]:
        reasons = []

        # 1) peer energy collapse proxy (mid_peer very low)
        mid_peer_med = float(np.nanmedian(g["mid_peer"].to_numpy())) if len(g) else np.nan
        if np.isfinite(mid_peer_med) and mid_peer_med < 0.35:
            reasons.append("peer_peak_low")

        # 2) widespread low concurrence proxy
        co_med = float(np.nanmedian(g["co_drop_frac"].fillna(0.0).to_numpy())) if len(g) else 0.0
        if np.isfinite(co_med) and co_med >= 0.45:
            reasons.append("co_drop_surge")

        # 3) degraded surge
        deg_frac = float(np.mean(g["degraded_candidate"].fillna(False).to_numpy(dtype=bool))) if len(g) else 0.0
        if deg_frac >= 0.35:
            reasons.append("degraded_ratio_surge")

        # 4) shadow-like surge
        sh_frac = float(np.mean(g["shadow_like"].fillna(False).to_numpy(dtype=bool))) if len(g) else 0.0
        if sh_frac >= 0.35:
            reasons.append("shadow_like_surge")

        soft = len(reasons) > 0

        # hard condition: peer collapse OR extreme concurrence OR extreme surge
        hard = False
        if ("peer_peak_low" in reasons) or (co_med >= 0.60) or (deg_frac >= 0.60):
            hard = True

        return soft, hard, ";".join(reasons)

    # compute day-wise flags (pandas groupby.apply FutureWarning-safe)
    def _day_flags_apply(df: pd.DataFrame) -> pd.DataFrame:
        try:
            # pandas newer versions
            return df.groupby("date", group_keys=False).apply(
                lambda g: pd.Series(
                    _site_event_reason_for_day(g),
                    index=["site_event_soft", "site_event_hard", "site_event_reason"],
                ),
                include_groups=False,
            )
        except TypeError:
            # pandas older versions (no include_groups)
            return df.groupby("date", group_keys=False).apply(
                lambda g: pd.Series(
                    _site_event_reason_for_day(g),
                    index=["site_event_soft", "site_event_hard", "site_event_reason"],
                )
            )

    day_flags = _day_flags_apply(out)
    out = out.merge(day_flags, left_on="date", right_index=True, how="left")
    out["site_event_soft"] = out["site_event_soft"].fillna(False).astype(bool)
    out["site_event_hard"] = out["site_event_hard"].fillna(False).astype(bool)
    out["site_event_reason"] = out["site_event_reason"].fillna("").astype(str)

    # Gate: site event day should not produce EWS/prefault escalation.
    out.loc[out["site_event_soft"], "ews_warning"] = False
    out.loc[out["site_event_hard"], "ews_warning"] = False
    # Gate: group/string-level OFF events should not escalate into EWS/prefault
    out.loc[out["group_off_date"].astype(bool), "ews_warning"] = False

    # ---- DTW/HS ranking and subtype refinement ----
    # 1) Add daily DTW and HS ranks
    out["dtw_rank_day"] = out.groupby("date")["dtw_dist"].rank(pct=True)
    out["hs_rank_day"] = out.groupby("date")["hs_score"].rank(pct=True)

    # 2) Add categorical strengths
    out["dtw_strength"] = "low"
    out.loc[out["dtw_rank_day"] >= 0.7, "dtw_strength"] = "mid"
    out.loc[out["dtw_rank_day"] >= 0.9, "dtw_strength"] = "high"
    out["hs_strength"] = "low"
    out.loc[out["hs_rank_day"] >= 0.7, "hs_strength"] = "mid"
    out.loc[out["hs_rank_day"] >= 0.9, "hs_strength"] = "high"

    # Refine shadow-like using HS/DTW strengths to better capture transient cloud/shading
    # - require turbulence (HS mid/high)
    # - avoid cases where the panel is strongly off its own reference (DTW high)
    # - require spatial concurrence (co_drop_frac >= co_drop_thr)
    out["shadow_like"] = (
        out["shadow_like_basic"].astype(bool)
        & out["hs_strength"].isin(["mid", "high"])
        & (~out["dtw_strength"].isin(["high"]))
        & (out["co_drop_frac"].fillna(0.0) >= float(args.shadow_co_drop_thr))
    )

    # Update anom_level after refining shadow_like
    # (keep confirmed_fault highest priority)
    out.loc[out["shadow_like"], "anom_level"] = "shadow_like"
    out.loc[out["shadow_like_basic"] & (~out["shadow_like"]), "anom_level"] = "degraded_or_shadow"
    out.loc[out["final_fault"], "anom_level"] = "confirmed_fault"

    # 3) Refine anom_subtype using DTW/HS
    # For shadow-like days
    out.loc[out["shadow_like"] & (out["hs_strength"] != "high"), "anom_subtype"] = "shadow_like_mild"
    out.loc[
        out["shadow_like"] & (out["hs_strength"] == "high") & (out["dtw_strength"].isin(["mid", "high"])),
        "anom_subtype"
    ] = "shadow_like_strong"

    # For degraded candidates (excluding shadow_like and confirmed faults)
    mask_deg = out["degraded_candidate"] & (~out["shadow_like"]) & (~out["final_fault"])
    out.loc[
        mask_deg & (out["hs_strength"] == "low") & (out["dtw_strength"].isin(["low", "mid"])),
        "anom_subtype"
    ] = "degradation_steady"
    out.loc[
        mask_deg & (out["dtw_strength"] == "high"),
        "anom_subtype"
    ] = "degradation_strong"

    # For fault-like days not yet final_fault
    mask_fault_like = out["fault_like_day"] & (~out["final_fault"])

    # 기본값은 fault_like_weak으로 태깅
    out.loc[mask_fault_like, "anom_subtype"] = "fault_like_weak"

    # DTW가 강하게 틀어지고, HS 난류가 너무 높지 않은 경우를 strong으로 승격
    out.loc[
        mask_fault_like
        & (out["dtw_strength"] == "high")
        & (out["hs_strength"].isin(["low", "mid"])),
        "anom_subtype"
    ] = "fault_like_strong"

    # 4) Confirmed faults always override
    out.loc[out["final_fault"], "anom_subtype"] = "confirmed_fault"

    # 최종 저장 전에는 다시 날짜+패널 기준 정렬
    out = out.sort_values(["date", "panel_id"])

    # ===== Layer 4: 1.1-style pre-fault template engine (Option B, 엔진 1.0) =====
    # 최근 40일 기준으로 패널별 요약 지표를 만들고,
    # 1.1 패널에서 관찰된 패턴과 비슷한 경우를 "전조 후보"로 본다.

    # 패널-날짜 순으로 한 번 더 정렬하고 그룹 생성
    out = out.sort_values(["panel_id", "date"])
    grp_pf = out.groupby("panel_id", group_keys=False)

    # AE/DTW/HS mid 이상 여부를 0/1 플래그로 변환
    out["ae_mid_flag"] = out["ae_strength"].isin(["mid", "high"]).astype(float)
    out["dtw_mid_flag"] = out["dtw_strength"].isin(["mid", "high"]).astype(float)

    # 최근 40일 롤링 윈도우 (일 데이터 기준), 최소 20일 이상 관측이 있을 때만 유효
    window = 40
    min_periods = 20

    out["pf40_mid_mean"] = grp_pf["mid_ratio"].transform(
        lambda s: s.rolling(window=window, min_periods=min_periods).mean()
    )
    out["pf40_ae_ratio"] = grp_pf["ae_mid_flag"].transform(
        lambda s: s.rolling(window=window, min_periods=min_periods).mean()
    )
    out["pf40_dtw_ratio"] = grp_pf["dtw_mid_flag"].transform(
        lambda s: s.rolling(window=window, min_periods=min_periods).mean()
    )
    out["pf40_ews_ratio"] = grp_pf["ews_warning"].transform(
        lambda s: s.rolling(window=window, min_periods=min_periods).mean()
    )

    # Option B 템플릿 임계값 (1.1 pre-fault 윈도우를 기준으로 잡은 보수적 구간)
    mid_low = 0.5      # 평균 mid_ratio가 너무 낮지도(완전 dead) 너무 높지도(완전 정상) 않은 구간
    mid_high = 0.9
    pf_ae_ratio_thr = 0.7    # 최근 40일 중 AE mid/high 비율
    pf_dtw_ratio_thr = 0.7   # 최근 40일 중 DTW mid/high 비율
    pf_ews_ratio_thr = 0.05  # 최근 40일 중 EWS_warning 비율 (대략 40일 중 2일 이상)

    cond_mid = (out["pf40_mid_mean"] >= mid_low) & (out["pf40_mid_mean"] <= mid_high)
    cond_ae = out["pf40_ae_ratio"] >= pf_ae_ratio_thr
    cond_dtw = out["pf40_dtw_ratio"] >= pf_dtw_ratio_thr
    cond_ews = out["pf40_ews_ratio"] >= pf_ews_ratio_thr

    # 실제 전조 엔진 플래그 (b안):
    # - 데이터 품질이 나쁘지 않고(data_bad=False)
    # - 아직 최종 고장(final_fault)이 아닌 상태에서
    # - 위 네 조건을 동시에 만족하면 해당 날짜-패널을 "전조 후보"로 표시
    out["prefault_B"] = (
        (~out["data_bad"]) & (~out["final_fault"]) &
        cond_mid & cond_ae & cond_dtw & cond_ews
    )

    # ===== Helper reports: daily summaries & candidate lists =====
    # 1) 날짜별 anom_level 요약 테이블
    try:
        daily_level = (
            out.pivot_table(
                index="date",
                columns="anom_level",
                values="panel_id",
                aggfunc="count",
                fill_value=0,
            )
            .reset_index()
        )
        daily_level_path = out_dir / "ae_simple_daily_anom_level.csv"
        daily_level.to_csv(daily_level_path, index=False, encoding="utf-8-sig")
    except Exception as e:
        print("[WARN] failed to write daily anom_level summary:", e)

    # 2) 날짜별 anom_subtype 요약 테이블
    try:
        daily_subtype = (
            out.pivot_table(
                index="date",
                columns="anom_subtype",
                values="panel_id",
                aggfunc="count",
                fill_value=0,
            )
            .reset_index()
        )
        daily_subtype_path = out_dir / "ae_simple_daily_anom_subtype.csv"
        daily_subtype.to_csv(daily_subtype_path, index=False, encoding="utf-8-sig")
    except Exception as e:
        print("[WARN] failed to write daily anom_subtype summary:", e)

    # 3) 고장/후보 패널 리스트 (final_fault / fault_like_day / degraded_candidate)
    try:
        mask_candidates = (
            out["final_fault"].astype(bool)
            | out["fault_like_day"].astype(bool)
            | out["degraded_candidate"].astype(bool)
        )
        fault_candidates = out.loc[mask_candidates].copy()
        candidates_path = out_dir / "ae_simple_fault_candidates.csv"
        fault_candidates.to_csv(candidates_path, index=False, encoding="utf-8-sig")
    except Exception as e:
        print("[WARN] failed to write fault candidate list:", e)

    # 4) EWS 경고 패널 리스트
    try:
        ews_list = out[out["ews_warning"].astype(bool)].copy()
        ews_path = out_dir / "ae_simple_ews_warnings.csv"
        ews_list.to_csv(ews_path, index=False, encoding="utf-8-sig")
    except Exception as e:
        print("[WARN] failed to write EWS warning list:", e)

    # 5) 전조 엔진(Option B) 알람 리스트 – 날짜·패널 단위
    try:
        prefault_list = out[out["prefault_B"].astype(bool)].copy()
        pf_path = out_dir / "ae_simple_prefault_B_daily.csv"
        prefault_list.to_csv(pf_path, index=False, encoding="utf-8-sig")
    except Exception as e:
        print("[WARN] failed to write pre-fault template-B list:", e)

    # 5) 패널별 전조/만성 이상 요약 (전조 엔진 1.0, B안 로직)
    try:
        # B안 pre-alarm 플래그: 이미 고장 확정된 날은 제외하고,
        # EWS 경고 + (AE/DTW/HS 중 하나 이상 mid 이상) 인 날만 전조 후보로 간주
        out["pre_alarm"] = (
            (~out["final_fault"].astype(bool))
            & out["ews_warning"].astype(bool)
            & (
                out["ae_strength"].isin(["mid", "high"]) \
                | out["dtw_strength"].isin(["mid", "high"]) \
                | out["hs_strength"].isin(["mid", "high"])
            )
        )

        # 패널별 집계: 기간, 고장 여부, EWS/전조 일수 등
        grp_panel = out.groupby("panel_id")
        panel_summary = grp_panel.agg(
            first_date=("date", "min"),
            last_date=("date", "max"),
            has_fault=("final_fault", "any"),
            n_fault_days=("final_fault", "sum"),
            any_ews=("ews_warning", "any"),
            n_ews_days=("ews_warning", "sum"),
            any_pre_alarm=("pre_alarm", "any"),
            n_pre_alarm_days=("pre_alarm", "sum"),
        )

        # 패널별 최초 고장일과 최초 전조일
        fault_start = (
            out[out["final_fault"].astype(bool)]
            .groupby("panel_id")["date"]
            .min()
            .rename("fault_start_date")
        )
        pre_alarm_start = (
            out[out["pre_alarm"].astype(bool)]
            .groupby("panel_id")["date"]
            .min()
            .rename("pre_alarm_start")
        )

        panel_summary = panel_summary.join(fault_start, how="left").join(pre_alarm_start, how="left")

        # 전조 알람 리드타임 (일 단위)
        panel_summary["lead_days"] = (
            panel_summary["fault_start_date"] - panel_summary["pre_alarm_start"]
        ).dt.days

        # 패턴 분류 함수: 전조 vs 만성 vs 기타
        def _classify_alarm_pattern(row):
            # 전조 후보 자체가 없는 패널
            if not row["any_pre_alarm"]:
                return "no_pre_alarm"

            # 실제 고장 패널: 전조 리드타임이 3일 이상이면 전조 후보로 간주
            if row["has_fault"]:
                if pd.notna(row["lead_days"]) and row["lead_days"] >= 3:
                    return "pre_fault_candidate"  # 고장 전에 전조가 선행
                else:
                    return "near_or_post_fault"  # 고장 직전/직후만 튄 케이스

            # 아직 고장은 아니지만, 전조 알람이 장기간 누적된 만성 이상 패널
            span_days = (row["last_date"] - row["first_date"]).days
            if (row["n_pre_alarm_days"] >= 20) and (span_days >= 60):
                return "chronic_abnormal"  # 장기간 만성 이상 패턴

            # 나머지: 단기 이상 / 일시적 이상
            return "short_abnormal"

        panel_summary["alarm_pattern"] = panel_summary.apply(_classify_alarm_pattern, axis=1)

        # 패널 요약 리포트 저장
        panel_alarm_path = out_dir / "ae_simple_panel_alarms.csv"
        panel_summary.to_csv(panel_alarm_path, index=True, encoding="utf-8-sig")
    except Exception as e:
        print("[WARN] failed to write panel alarm summary:", e)

    out_path = out_dir / "ae_simple_scores.csv"
    out.to_csv(
        out_path,
        index=False,
        encoding="utf-8-sig",
        columns=[c for c in OUT_COLS if c in out.columns],
    )

    meta = {
        "args": vars(args),
        "ae_threshold_global": ae_thr_ae,
        "train_files": [p.name for p in train_files],
        "eval_files": [p.name for p in eval_files],
    }
    meta["tuning_level"] = tuning_level
    suffix = "" if tuning_level == "p2" else f"_{tuning_level}"
    meta_path = out_dir / f"ae_simple_meta{suffix}.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[OK] wrote", out_path)
    print("[OK] tuning_level =", tuning_level)
    print("[OK] ae_threshold_global =", ae_thr_ae)


if __name__ == "__main__":
    main()
# __write_probe__

# __write_probe__
