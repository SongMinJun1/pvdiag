#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import re
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


V_PATTERNS = [
    "vpv",
    "v_pv",
    "voltage",
    "vin",
    "v_in",
    "vdc",
]
I_PATTERNS = [
    "ipv",
    "i_pv",
    "current",
    "iout",
    "i_out",
    "idc",
]
P_PATTERNS = [
    "ppv",
    "p_pv",
    "power",
    "pout",
    "p_out",
    "pdc",
]
LABEL_PATTERNS = [
    "label",
    "fault",
    "class",
    "target",
    "status",
    "anomaly",
    "y",
]
TYPE_PATTERNS = [
    "faulttype",
    "fault_type",
    "type",
    "category",
]
TIME_PATTERNS = [
    "timestamp",
    "datetime",
    "date_time",
    "time",
    "date",
    "ts",
    "t",
]
PANEL_PATTERNS = [
    "panel",
    "module",
    "string",
    "id",
]


@dataclass
class StreamData:
    source_id: str
    frame: pd.DataFrame
    fault_sid: int
    fault_mode: str
    fault_type: str
    is_fault_file: bool


_SCENARIO_RE_EXACT = re.compile(r"^F(?P<sid>[0-7])(?P<mode>[LM])$", flags=re.IGNORECASE)
_SCENARIO_RE_SEARCH = re.compile(r"F(?P<sid>[0-7])(?P<mode>[LM])", flags=re.IGNORECASE)


def _parse_scenario_from_filename(path: pathlib.Path) -> tuple[int, str, str, bool]:
    stem = path.stem
    m = _SCENARIO_RE_EXACT.match(stem)
    if m is None:
        m = _SCENARIO_RE_SEARCH.search(stem)
    if m is None:
        raise RuntimeError(
            "GPVS scenario parse failed (expected pattern like F0L/F3M) "
            f"for file: {path}"
        )
    sid = int(m.group("sid"))
    mode = str(m.group("mode")).upper()
    ftype = f"F{sid}{mode}"
    return sid, mode, ftype, bool(sid > 0)


def _norm(s: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())


def _find_col(df: pd.DataFrame, patterns: list[str]) -> str | None:
    best_col = None
    best_score = -1
    for c in df.columns:
        nc = _norm(c)
        score = 0
        for p in patterns:
            if p in nc:
                score = max(score, len(p))
        if score > best_score:
            best_score = score
            best_col = c
    return best_col if best_score > 0 else None


def _parse_fault_binary(series: pd.Series) -> pd.Series:
    num = pd.to_numeric(series, errors="coerce")
    out_num = num.fillna(0.0).ne(0.0)

    txt = series.fillna("").astype(str).str.strip().str.lower()
    healthy_tokens = {
        "",
        "0",
        "healthy",
        "normal",
        "ok",
        "good",
        "none",
        "no",
        "false",
        "nofault",
    }
    fault_tokens = {"fault", "fail", "abnormal", "anomaly", "defect", "error", "true"}
    out_txt = pd.Series(False, index=series.index)
    for tok in fault_tokens:
        out_txt = out_txt | txt.str.contains(tok, regex=False)
    out_txt = out_txt | (~txt.isin(healthy_tokens) & txt.ne(""))
    return (out_num | out_txt).astype(int)


def _align_length(arr: np.ndarray, n: int) -> np.ndarray:
    x = np.asarray(arr).reshape(-1)
    if len(x) >= n:
        return x[:n]
    out = np.empty(n, dtype=float)
    out[:] = np.nan
    out[: len(x)] = pd.to_numeric(pd.Series(x), errors="coerce").to_numpy(dtype=float)
    return out


def _matlab_datenum_to_datetime(num: np.ndarray) -> pd.Series:
    # MATLAB datenum origin offset vs pandas datetime ordinal.
    vals = pd.to_numeric(pd.Series(num), errors="coerce").to_numpy(dtype=float)
    dt = pd.Series(pd.NaT, index=np.arange(len(vals)), dtype="datetime64[ns]")
    m = np.isfinite(vals)
    if not np.any(m):
        return dt
    base = pd.Timestamp("1970-01-01")
    # datenum day 719529 == 1970-01-01
    secs = (vals[m] - 719529.0) * 86400.0
    dt.loc[m] = pd.to_datetime(base.value / 1e9 + secs, unit="s", errors="coerce")
    return dt


def _robust_center_scale(x: np.ndarray) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return 0.0, 1.0
    c = float(np.median(x))
    mad = float(np.median(np.abs(x - c)))
    s = 1.4826 * mad
    if not np.isfinite(s) or s < 1e-9:
        s = float(np.std(x))
    if not np.isfinite(s) or s < 1e-9:
        s = 1.0
    return c, s


def _sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    z = np.clip(z, -20.0, 20.0)
    return 1.0 / (1.0 + np.exp(-z))


def _scale_like(raw: np.ndarray, healthy_mask: np.ndarray) -> np.ndarray:
    raw = np.asarray(raw, dtype=float)
    hm = np.asarray(healthy_mask, dtype=bool)
    base = raw[np.isfinite(raw) & hm]
    if len(base) < 5:
        base = raw[np.isfinite(raw)]
    c, s = _robust_center_scale(base)
    z = (raw - c) / s
    out = _sigmoid(z)
    out[~np.isfinite(raw)] = np.nan
    return out


def _resample_wave(arr: np.ndarray, n: int = 64) -> np.ndarray:
    x = np.asarray(arr, dtype=float).reshape(-1)
    if len(x) == 0:
        return np.zeros(n, dtype=float)
    idx = np.arange(len(x), dtype=float)
    finite = np.isfinite(x)
    if np.sum(finite) < 2:
        x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    else:
        x = np.interp(idx, idx[finite], x[finite])
    xi = np.linspace(0, len(x) - 1, n)
    return np.interp(xi, idx, x).astype(float)


def _dtw_distance(a: np.ndarray, b: np.ndarray, band: int = 8) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    n = min(len(a), len(b))
    if n == 0:
        return np.nan
    a = a[:n]
    b = b[:n]
    band = max(1, int(band))
    d = np.full((n, n), np.inf, dtype=float)
    d[0, 0] = (a[0] - b[0]) ** 2
    for i in range(n):
        j0 = max(0, i - band)
        j1 = min(n - 1, i + band)
        for j in range(j0, j1 + 1):
            cost = (a[i] - b[j]) ** 2
            if i == 0 and j == 0:
                d[i, j] = cost
            else:
                m = min(
                    d[i - 1, j] if i > 0 else np.inf,
                    d[i, j - 1] if j > 0 else np.inf,
                    d[i - 1, j - 1] if (i > 0 and j > 0) else np.inf,
                )
                d[i, j] = cost + m
    return float(np.sqrt(d[n - 1, n - 1]))


def _pca_recon_error(x_train: np.ndarray, x_all: np.ndarray, n_comp: int = 8) -> np.ndarray:
    if x_train.ndim != 2 or x_all.ndim != 2:
        return np.full(len(x_all), np.nan, dtype=float)
    if len(x_train) < max(6, n_comp + 2):
        return np.full(len(x_all), np.nan, dtype=float)
    mu = np.mean(x_train, axis=0, keepdims=True)
    xc = x_train - mu
    try:
        _, _, vt = np.linalg.svd(xc, full_matrices=False)
    except np.linalg.LinAlgError:
        return np.full(len(x_all), np.nan, dtype=float)
    k = min(int(n_comp), vt.shape[0])
    if k < 1:
        return np.full(len(x_all), np.nan, dtype=float)
    basis = vt[:k]
    xa = x_all - mu
    z = xa @ basis.T
    rec = z @ basis + mu
    err = np.mean((x_all - rec) ** 2, axis=1)
    return err.astype(float)


def _collect_numeric_series(name: str, obj: Any, out: dict[str, np.ndarray]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            _collect_numeric_series(f"{name}_{k}", v, out)
        return
    if hasattr(obj, "__dict__") and not isinstance(obj, (str, bytes, np.ndarray)):
        for k in dir(obj):
            if k.startswith("_"):
                continue
            try:
                v = getattr(obj, k)
            except Exception:
                continue
            _collect_numeric_series(f"{name}_{k}", v, out)
        return
    if not isinstance(obj, np.ndarray):
        return
    arr = np.asarray(obj)
    if arr.size < 10:
        return
    if arr.dtype == object:
        return
    if arr.ndim == 1:
        out[name] = pd.to_numeric(pd.Series(arr), errors="coerce").to_numpy(dtype=float)
        return
    if arr.ndim == 2:
        r, c = arr.shape
        if r >= c and c <= 16:
            for j in range(c):
                out[f"{name}_{j}"] = pd.to_numeric(pd.Series(arr[:, j]), errors="coerce").to_numpy(dtype=float)
        elif c > r and r <= 16:
            for j in range(r):
                out[f"{name}_{j}"] = pd.to_numeric(pd.Series(arr[j, :]), errors="coerce").to_numpy(dtype=float)
        else:
            one = arr[:, 0] if r >= c else arr[0, :]
            out[name] = pd.to_numeric(pd.Series(one), errors="coerce").to_numpy(dtype=float)


def _pick_series_key(series: dict[str, np.ndarray], patterns: list[str]) -> str | None:
    best_key = None
    best_score = -1
    best_len = -1
    for k, arr in series.items():
        nk = _norm(k)
        score = 0
        for p in patterns:
            if p in nk:
                score = max(score, len(p))
        if score <= 0:
            continue
        arr_len = int(len(arr))
        if score > best_score or (score == best_score and arr_len > best_len):
            best_score = score
            best_len = arr_len
            best_key = k
    return best_key


def _load_mat_streams(path: pathlib.Path) -> list[StreamData]:
    fault_sid, fault_mode, fault_type, is_fault_file = _parse_scenario_from_filename(path)
    try:
        from scipy.io import loadmat
    except Exception as e:
        raise RuntimeError("scipy is required to read .mat files") from e

    mat = loadmat(path, squeeze_me=True, struct_as_record=False)
    series: dict[str, np.ndarray] = {}
    for k, v in mat.items():
        if str(k).startswith("__"):
            continue
        _collect_numeric_series(str(k), v, series)
    if not series:
        return []

    key_v = _pick_series_key(series, V_PATTERNS)
    key_i = _pick_series_key(series, I_PATTERNS)
    key_p = _pick_series_key(series, P_PATTERNS)
    key_l = _pick_series_key(series, LABEL_PATTERNS)
    key_t = _pick_series_key(series, TIME_PATTERNS)

    keys = [k for k in [key_v, key_i, key_p, key_l, key_t] if k is not None]
    if not keys:
        return []
    n = max(len(series[k]) for k in keys)
    frame = pd.DataFrame(index=np.arange(n))
    if key_v:
        frame["v_pv"] = _align_length(series[key_v], n)
    if key_i:
        frame["i_pv"] = _align_length(series[key_i], n)
    if key_p:
        frame["p_pv"] = _align_length(series[key_p], n)
    if "p_pv" not in frame.columns and "v_pv" in frame.columns and "i_pv" in frame.columns:
        frame["p_pv"] = pd.to_numeric(frame["v_pv"], errors="coerce") * pd.to_numeric(frame["i_pv"], errors="coerce")

    if key_l:
        lbl = _align_length(series[key_l], n)
        frame["label_fault"] = _parse_fault_binary(pd.Series(lbl)).to_numpy(dtype=int)
        frame["fault_type"] = pd.Series(lbl).fillna(0).astype(str)
    else:
        frame["label_fault"] = 0
        frame["fault_type"] = ""

    if key_t:
        raw_t = _align_length(series[key_t], n)
        if np.nanmedian(raw_t) > 100000:
            frame["time"] = _matlab_datenum_to_datetime(raw_t)
        else:
            frame["time"] = pd.Series(raw_t)
    else:
        frame["time"] = np.arange(n)

    if "p_pv" not in frame.columns:
        return []
    source_id = f"{path.stem}"
    return [
        StreamData(
            source_id=source_id,
            frame=frame,
            fault_sid=fault_sid,
            fault_mode=fault_mode,
            fault_type=fault_type,
            is_fault_file=is_fault_file,
        )
    ]


def _load_csv_streams(path: pathlib.Path) -> list[StreamData]:
    fault_sid, fault_mode, fault_type_file, is_fault_file = _parse_scenario_from_filename(path)
    try:
        df = pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")
    except Exception:
        try:
            df = pd.read_csv(path, encoding="utf-8-sig")
        except Exception:
            df = pd.read_csv(path)
    if df.empty:
        return []

    c_time = _find_col(df, TIME_PATTERNS)
    c_label = _find_col(df, LABEL_PATTERNS)
    c_type = _find_col(df, TYPE_PATTERNS)
    c_v = _find_col(df, V_PATTERNS)
    c_i = _find_col(df, I_PATTERNS)
    c_p = _find_col(df, P_PATTERNS)
    c_panel = _find_col(df, PANEL_PATTERNS)

    if c_p is None and not (c_v and c_i):
        return []

    if c_panel and c_panel in df.columns:
        groups = list(df.groupby(c_panel, sort=False))
    else:
        groups = [("all", df)]

    out: list[StreamData] = []
    for gid, g in groups:
        work = pd.DataFrame(index=g.index)
        if c_time:
            work["time"] = pd.to_datetime(g[c_time], errors="coerce")
            if work["time"].isna().all():
                work["time"] = pd.to_numeric(g[c_time], errors="coerce")
        else:
            work["time"] = np.arange(len(g))
        if c_v:
            work["v_pv"] = pd.to_numeric(g[c_v], errors="coerce")
        if c_i:
            work["i_pv"] = pd.to_numeric(g[c_i], errors="coerce")
        if c_p:
            work["p_pv"] = pd.to_numeric(g[c_p], errors="coerce")
        if "p_pv" not in work.columns and "v_pv" in work.columns and "i_pv" in work.columns:
            work["p_pv"] = work["v_pv"] * work["i_pv"]
        if "p_pv" not in work.columns:
            continue
        if c_label:
            work["label_fault"] = _parse_fault_binary(g[c_label])
        else:
            work["label_fault"] = 0
        # File-name scenario label is SSOT for GPVS-Faults.
        work["fault_type"] = fault_type_file
        sid = f"{path.stem}:{gid}"
        out.append(
            StreamData(
                source_id=sid,
                frame=work.reset_index(drop=True),
                fault_sid=fault_sid,
                fault_mode=fault_mode,
                fault_type=fault_type_file,
                is_fault_file=is_fault_file,
            )
        )
    return out


def _iter_raw_files(root: pathlib.Path) -> list[pathlib.Path]:
    files = []
    for ext in ("*.csv", "*.CSV", "*.mat", "*.MAT"):
        files.extend(root.rglob(ext))
    files = [p for p in files if p.is_file()]
    files.sort()
    return files


def _windowize_stream(stream: StreamData, window: int, stride: int) -> list[dict[str, Any]]:
    df = stream.frame.copy()
    if "time" in df.columns and np.issubdtype(df["time"].dtype, np.datetime64):
        df = df.sort_values("time")
    n = len(df)
    if n < window:
        return []
    starts = list(range(0, n - window + 1, stride))
    n_windows = len(starts)
    if n_windows == 0:
        return []
    rows: list[dict[str, Any]] = []
    for w_idx, start in enumerate(starts):
        end = start + window
        w = df.iloc[start:end]
        p = pd.to_numeric(w.get("p_pv"), errors="coerce").to_numpy(dtype=float)
        v = pd.to_numeric(w.get("v_pv"), errors="coerce").to_numpy(dtype=float) if "v_pv" in w.columns else np.full(window, np.nan)
        i = pd.to_numeric(w.get("i_pv"), errors="coerce").to_numpy(dtype=float) if "i_pv" in w.columns else np.full(window, np.nan)
        if not np.isfinite(p).any() and not np.isfinite(v).any() and not np.isfinite(i).any():
            continue

        # GPVS rule: F0*=healthy file, F{1..7}*=fault file with middle injection.
        is_fault_window = int(stream.is_fault_file and (w_idx >= (n_windows / 2.0)))
        label_fault = int(is_fault_window)

        tcol = w.get("time", pd.Series(np.arange(start, end)))
        t0 = tcol.iloc[0]
        t1 = tcol.iloc[-1]

        p_mean = float(np.nanmean(p)) if np.isfinite(p).any() else np.nan
        v_mean = float(np.nanmean(v)) if np.isfinite(v).any() else np.nan
        i_mean = float(np.nanmean(i)) if np.isfinite(i).any() else np.nan
        p_cv = float(np.nanstd(p) / (abs(np.nanmean(p)) + 1e-6)) if np.isfinite(p).any() else np.nan

        rows.append(
            {
                "sample_id": f"{stream.source_id}::w{start:06d}",
                "source_id": stream.source_id,
                "window_idx": int(start),
                "window_ord": int(w_idx),
                "n_windows": int(n_windows),
                "t0": t0,
                "t1": t1,
                "label_fault": int(label_fault),
                "is_fault_window": int(is_fault_window),
                "fault_sid": int(stream.fault_sid),
                "fault_mode": str(stream.fault_mode),
                "fault_type": str(stream.fault_type),
                "is_fault_file": int(stream.is_fault_file),
                "v_pv_mean": v_mean,
                "i_pv_mean": i_mean,
                "p_pv_mean": p_mean,
                "_p_wave": p,
                "_p_cv_raw": p_cv,
            }
        )
    return rows


def build_window_scores(
    input_root: pathlib.Path,
    out_csv: pathlib.Path,
    window_size: int,
    stride: int,
    dtw_len: int = 64,
) -> pd.DataFrame:
    files = _iter_raw_files(input_root)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    if not files:
        cols = [
            "sample_id",
            "source_id",
            "window_idx",
            "window_ord",
            "n_windows",
            "t0",
            "t1",
            "label_fault",
            "is_fault_window",
            "fault_sid",
            "fault_mode",
            "fault_type",
            "is_fault_file",
            "v_pv_mean",
            "i_pv_mean",
            "p_pv_mean",
            "level_drop_like",
            "v_drop_like",
            "hs_like",
            "dtw_like",
            "ae_like",
        ]
        empty = pd.DataFrame(columns=cols)
        empty.to_csv(out_csv, index=False, encoding="utf-8-sig")
        print(f"[WARN] no input files found under: {input_root}")
        print(f"[OK] wrote empty score file: {out_csv}")
        return empty

    all_rows: list[dict[str, Any]] = []
    for p in files:
        # FAIL FAST on scenario parse mismatch.
        _parse_scenario_from_filename(p)
        try:
            if p.suffix.lower() == ".csv":
                streams = _load_csv_streams(p)
            elif p.suffix.lower() == ".mat":
                streams = _load_mat_streams(p)
            else:
                streams = []
        except Exception as e:
            print(f"[WARN] failed to parse {p}: {e}")
            streams = []
        for s in streams:
            all_rows.extend(_windowize_stream(s, window=window_size, stride=stride))

    if not all_rows:
        cols = [
            "sample_id",
            "source_id",
            "window_idx",
            "window_ord",
            "n_windows",
            "t0",
            "t1",
            "label_fault",
            "is_fault_window",
            "fault_sid",
            "fault_mode",
            "fault_type",
            "is_fault_file",
            "v_pv_mean",
            "i_pv_mean",
            "p_pv_mean",
            "level_drop_like",
            "v_drop_like",
            "hs_like",
            "dtw_like",
            "ae_like",
        ]
        empty = pd.DataFrame(columns=cols)
        empty.to_csv(out_csv, index=False, encoding="utf-8-sig")
        print(f"[WARN] no usable streams/windows from input: {input_root}")
        print(f"[OK] wrote empty score file: {out_csv}")
        return empty

    df = pd.DataFrame(all_rows)
    df["t0"] = pd.to_datetime(df["t0"], errors="coerce")
    df["t1"] = pd.to_datetime(df["t1"], errors="coerce")
    df["label_fault"] = pd.to_numeric(df["label_fault"], errors="coerce").fillna(0).astype(int)

    healthy = df["label_fault"].eq(0).to_numpy(dtype=bool)
    p_mean = pd.to_numeric(df["p_pv_mean"], errors="coerce").to_numpy(dtype=float)
    v_mean = pd.to_numeric(df["v_pv_mean"], errors="coerce").to_numpy(dtype=float)
    cv_raw = pd.to_numeric(df["_p_cv_raw"], errors="coerce").to_numpy(dtype=float)

    base_p_pool = p_mean[healthy & np.isfinite(p_mean)]
    base_v_pool = v_mean[healthy & np.isfinite(v_mean)]
    base_p = float(np.median(base_p_pool)) if len(base_p_pool) else float(np.nanmedian(p_mean))
    base_v = float(np.median(base_v_pool)) if len(base_v_pool) else float(np.nanmedian(v_mean))
    if not np.isfinite(base_p):
        base_p = 1.0
    if not np.isfinite(base_v):
        base_v = 1.0

    level_drop_raw = np.clip((base_p - p_mean) / (abs(base_p) + 1e-9), 0.0, None)
    v_drop_raw = np.clip((base_v - v_mean) / (abs(base_v) + 1e-9), 0.0, None)

    waves = np.vstack([_resample_wave(w, n=dtw_len) for w in df["_p_wave"]])
    h_idx = healthy & np.isfinite(waves).all(axis=1)
    if np.any(h_idx):
        baseline_wave = np.nanmedian(waves[h_idx], axis=0)
    else:
        baseline_wave = np.nanmedian(waves, axis=0)
    if not np.isfinite(baseline_wave).all():
        baseline_wave = np.nan_to_num(baseline_wave, nan=0.0, posinf=0.0, neginf=0.0)

    dtw_raw = np.array([_dtw_distance(w, baseline_wave, band=max(2, dtw_len // 8)) for w in waves], dtype=float)
    ae_raw = _pca_recon_error(waves[h_idx], waves, n_comp=min(8, max(2, dtw_len // 8))) if np.any(h_idx) else np.full(len(df), np.nan)

    df["level_drop_raw"] = level_drop_raw
    df["v_drop_raw"] = v_drop_raw
    df["hs_raw"] = cv_raw
    df["dtw_raw"] = dtw_raw
    df["ae_raw"] = ae_raw
    df["level_drop_like"] = _scale_like(level_drop_raw, healthy)
    df["v_drop_like"] = _scale_like(v_drop_raw, healthy)
    df["hs_like"] = _scale_like(cv_raw, healthy)
    df["dtw_like"] = _scale_like(dtw_raw, healthy)
    df["ae_like"] = _scale_like(ae_raw, healthy)

    out_cols = [
        "sample_id",
        "source_id",
        "window_idx",
        "window_ord",
        "n_windows",
        "t0",
        "t1",
        "label_fault",
        "is_fault_window",
        "fault_sid",
        "fault_mode",
        "fault_type",
        "is_fault_file",
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
    out = df[out_cols].copy()
    out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] files parsed: {len(files)}")
    print(f"[OK] window samples: {len(out)}")
    print(f"[OK] wrote: {out_csv}")
    return out


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Ingest GPVS-Faults raw files (csv/mat) and build window-level scores.")
    ap.add_argument("--input-root", default="data/gpvs/_download/GPVS_Faults", help="Root directory of GPVS raw files.")
    ap.add_argument("--out-csv", default="data/gpvs/out/gpvs_window_scores.csv", help="Output window-score CSV path.")
    ap.add_argument("--window-size", type=int, default=256, help="Sliding window size in samples.")
    ap.add_argument("--stride", type=int, default=128, help="Sliding window stride in samples.")
    ap.add_argument("--dtw-len", type=int, default=64, help="Resampled length for DTW/AE-like calculations.")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    build_window_scores(
        input_root=pathlib.Path(args.input_root),
        out_csv=pathlib.Path(args.out_csv),
        window_size=int(args.window_size),
        stride=int(args.stride),
        dtw_len=int(args.dtw_len),
    )


if __name__ == "__main__":
    main()
