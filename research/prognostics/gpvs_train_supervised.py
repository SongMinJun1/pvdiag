#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
from itertools import product
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


RAW_COLS = [
    "level_drop_raw",
    "v_drop_raw",
    "dtw_raw",
    "hs_raw",
    "ae_raw",
]
LIKE_COLS = [
    "level_drop_like",
    "v_drop_like",
    "dtw_like",
    "hs_like",
    "ae_like",
]
FPR1 = 0.01
SPAN_EPS = 1e-12


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


def _threshold_at_fpr(train_neg_scores: np.ndarray, fpr: float = FPR1) -> float:
    s = np.asarray(train_neg_scores, dtype=float)
    s = s[np.isfinite(s)]
    if len(s) == 0:
        return np.nan
    s = np.sort(s)
    candidates = np.unique(s)
    chosen_tau = float(np.max(s))
    chosen_fpr = 0.0
    for tau in candidates:
        actual_fpr = float(np.mean(s > tau))
        if actual_fpr <= fpr and actual_fpr >= chosen_fpr:
            chosen_tau = float(tau)
            chosen_fpr = actual_fpr
    return chosen_tau


def _precision_recall_f1(y: np.ndarray, pred: np.ndarray) -> tuple[float, float, float]:
    yb = y.astype(int)
    pb = pred.astype(bool)
    tp = int(np.sum(pb & (yb == 1)))
    fp = int(np.sum(pb & (yb == 0)))
    fn = int(np.sum((~pb) & (yb == 1)))
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else np.nan
    if np.isfinite(recall) and (precision + recall) > 0:
        f1 = float((2.0 * precision * recall) / (precision + recall))
    elif np.isfinite(recall):
        f1 = 0.0
    else:
        f1 = np.nan
    return precision, recall, f1


def _best_f1_threshold(train_y: np.ndarray, train_score: np.ndarray) -> float:
    finite = np.isfinite(train_y) & np.isfinite(train_score)
    y = train_y[finite].astype(int)
    s = train_score[finite].astype(float)
    if len(s) == 0:
        return np.nan
    best_tau = float(np.nanmedian(s))
    best_f1 = -1.0
    for tau in np.unique(s):
        _, _, f1 = _precision_recall_f1(y, s > tau)
        if np.isfinite(f1) and f1 > best_f1:
            best_f1 = f1
            best_tau = float(tau)
    return best_tau


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


def _check_required(df: pd.DataFrame) -> None:
    need = ["source_id", "fault_type", "is_fault_window"] + RAW_COLS + LIKE_COLS
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise RuntimeError(f"missing required columns: {missing}")


def _mode_suffix(df: pd.DataFrame) -> pd.Series:
    if "fault_mode" in df.columns:
        m = df["fault_mode"].fillna("").astype(str)
        m = m.where(m.isin(["L", "M"]), "")
        if bool(m.ne("").any()):
            return m
    ft = df["fault_type"].fillna("").astype(str)
    out = pd.Series("", index=df.index, dtype=str)
    out[ft.str.endswith("L")] = "L"
    out[ft.str.endswith("M")] = "M"
    return out


def _group_rolling_feature(
    df: pd.DataFrame,
    value_col: str,
    order_col: str,
    window: int,
    op: str,
) -> pd.Series:
    sorted_df = df.sort_values(["source_id", order_col]).copy()
    gb = sorted_df.groupby("source_id")[value_col]
    if op == "mean":
        rolled = gb.rolling(window, min_periods=1).mean().reset_index(level=0, drop=True)
    elif op == "max":
        rolled = gb.rolling(window, min_periods=1).max().reset_index(level=0, drop=True)
    elif op == "std":
        rolled = gb.rolling(window, min_periods=1).std(ddof=0).reset_index(level=0, drop=True).fillna(0.0)
    else:
        raise ValueError(op)
    return rolled.reindex(sorted_df.index).reindex(df.index)


def _feature_engineering(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    work = df.copy()
    work["y"] = pd.to_numeric(work["is_fault_window"], errors="coerce").fillna(0).astype(int)
    work["mode"] = _mode_suffix(work)
    work["mode_L"] = work["mode"].eq("L").astype(float)
    work["mode_M"] = work["mode"].eq("M").astype(float)

    order_col = "window_ord" if "window_ord" in work.columns else ("window_idx" if "window_idx" in work.columns else None)
    if order_col is None:
        work["_order"] = np.arange(len(work), dtype=float)
        order_col = "_order"

    for raw_col in RAW_COLS:
        work[raw_col] = pd.to_numeric(work[raw_col], errors="coerce")
        sorted_df = work.sort_values(["source_id", order_col]).copy()
        work[f"delta_{raw_col}"] = sorted_df.groupby("source_id")[raw_col].diff().reindex(sorted_df.index).reindex(work.index)
        work[f"rollmean3_{raw_col}"] = _group_rolling_feature(work, raw_col, order_col, 3, "mean")
        work[f"rollmax3_{raw_col}"] = _group_rolling_feature(work, raw_col, order_col, 3, "max")

    deg_cols = []
    active_axis_count = pd.Series(0.0, index=work.index)
    for sid, idx in work.groupby("source_id").groups.items():
        g = work.loc[idx].copy()
        y = g["y"].to_numpy(dtype=int)
        pre_mask = y == 0
        active = 0
        for raw_col in RAW_COLS:
            vals = pd.to_numeric(g[raw_col], errors="coerce").to_numpy(dtype=float)
            pre_vals = vals[pre_mask & np.isfinite(vals)]
            if len(pre_vals) == 0:
                deg = 1.0
            else:
                n_unique = int(pd.Series(pre_vals).nunique(dropna=True))
                span = float(np.max(pre_vals) - np.min(pre_vals))
                deg = float(n_unique <= 1 or (np.isfinite(span) and span <= SPAN_EPS))
            deg_name = f"deg_{raw_col}"
            work.loc[idx, deg_name] = deg
            if deg == 0.0:
                active += 1
            if deg_name not in deg_cols:
                deg_cols.append(deg_name)
        active_axis_count.loc[idx] = float(active)
    work["active_axis_count"] = active_axis_count

    feature_cols = ["mode_L", "mode_M"] + RAW_COLS + LIKE_COLS + ["active_axis_count"] + deg_cols
    feature_cols += [f"delta_{c}" for c in RAW_COLS]
    feature_cols += [f"rollmean3_{c}" for c in RAW_COLS]
    feature_cols += [f"rollmax3_{c}" for c in RAW_COLS]
    return work, feature_cols


def _candidate_feature_sets() -> dict[str, list[str]]:
    mode_cols = ["mode_L", "mode_M"]
    deg_cols = [f"deg_{c}" for c in RAW_COLS]
    raw_delta = [f"delta_{c}" for c in RAW_COLS]
    raw_rollmean3 = [f"rollmean3_{c}" for c in RAW_COLS]
    raw_rollmax3 = [f"rollmax3_{c}" for c in RAW_COLS]
    return {
        "stable_like_all": [
            "level_drop_like",
            "v_drop_like",
            "dtw_like",
            "hs_like",
            "ae_like",
            *mode_cols,
            "active_axis_count",
            *deg_cols,
        ],
        "stable_like_shape_first": [
            "dtw_like",
            "hs_like",
            "ae_like",
            *mode_cols,
            "active_axis_count",
            *deg_cols,
        ],
        "raw_no_norm_all": [
            *RAW_COLS,
            *mode_cols,
            "active_axis_count",
            *deg_cols,
            *raw_delta,
            *raw_rollmean3,
            *raw_rollmax3,
        ],
        "mixed_no_norm": [
            *LIKE_COLS,
            *RAW_COLS,
            *mode_cols,
            "active_axis_count",
            *deg_cols,
            *raw_delta,
            *raw_rollmean3,
            *raw_rollmax3,
        ],
    }


def _stabilize_feature_frames(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, list[str], dict[str, list[str]]]:
    keep = []
    removed_all_nan = []
    removed_zero_var = []
    for col in feature_cols:
        s = pd.to_numeric(train_df[col], errors="coerce")
        finite = s[np.isfinite(s)]
        if len(finite) == 0:
            removed_all_nan.append(col)
            continue
        if int(pd.Series(finite).nunique(dropna=True)) <= 1:
            removed_zero_var.append(col)
            continue
        keep.append(col)
    meta = {
        "removed_all_nan": removed_all_nan,
        "removed_zero_var": removed_zero_var,
    }
    return train_df[keep].copy(), test_df[keep].copy(), keep, meta


def _baseline_best_single(df: pd.DataFrame) -> tuple[str, float, float]:
    y = pd.to_numeric(df["is_fault_window"], errors="coerce").fillna(0).astype(int).to_numpy()
    rows = []
    for col in LIKE_COLS:
        s = pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float)
        m = np.isfinite(s)
        yy = y[m]
        ss = s[m]
        rows.append({"score": col, "roc_auc": _roc_auc_rank(yy, ss), "ap": _average_precision(yy, ss)})
    res = pd.DataFrame(rows).sort_values(["roc_auc", "ap"], ascending=False, na_position="last").reset_index(drop=True)
    if res.empty:
        return "", np.nan, np.nan
    r = res.iloc[0]
    return str(r["score"]), float(r["roc_auc"]), float(r["ap"])


def _build_logreg() -> Any:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", solver="lbfgs")),
        ]
    )


def _make_hgb(params: dict[str, Any], random_state: int) -> Any:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "clf",
                HistGradientBoostingClassifier(
                    learning_rate=float(params["learning_rate"]),
                    max_leaf_nodes=None if params["max_leaf_nodes"] is None else int(params["max_leaf_nodes"]),
                    min_samples_leaf=int(params["min_samples_leaf"]),
                    max_depth=params["max_depth"],
                    l2_regularization=float(params["l2_regularization"]),
                    max_iter=60,
                    random_state=random_state,
                ),
            ),
        ]
    )

def _predict_score(model: Any, X_eval: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X_eval)[:, 1]
    if hasattr(model, "decision_function"):
        s = model.decision_function(X_eval)
        return 1.0 / (1.0 + np.exp(-np.asarray(s, dtype=float)))
    raise RuntimeError("model does not expose predict_proba or decision_function")


def _serialize_list(vals: list[str], limit: int = 12) -> str:
    if not vals:
        return ""
    if len(vals) <= limit:
        return ",".join(vals)
    head = ",".join(vals[:limit])
    return f"{head},...(+{len(vals) - limit})"


def _hgb_param_grid() -> list[dict[str, Any]]:
    grid = []
    for lr, leaf, min_leaf, depth, l2 in product(
        [0.03, 0.05, 0.1],
        [15, 31, 63],
        [10, 20, 50],
        [3, 5, None],
        [0.0, 0.1, 1.0],
    ):
        grid.append(
            {
                "learning_rate": lr,
                "max_leaf_nodes": leaf,
                "min_samples_leaf": min_leaf,
                "max_depth": depth,
                "l2_regularization": l2,
            }
        )
    return grid


def _fit_predict_with_feature_set(
    model: Any,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    train_y: np.ndarray,
    feature_cols: list[str],
) -> tuple[np.ndarray, np.ndarray, list[str], dict[str, list[str]]]:
    X_train, X_test, kept, meta = _stabilize_feature_frames(train_df, test_df, feature_cols)
    if not kept or len(np.unique(train_y)) < 2:
        return np.full(len(train_df), np.nan), np.full(len(test_df), np.nan), kept, meta
    model.fit(X_train, train_y)
    train_score = _predict_score(model, X_train)
    test_score = _predict_score(model, X_test)
    return train_score, test_score, kept, meta


def _grouped_cv_score_hgb(
    feat_df: pd.DataFrame,
    train_idx: np.ndarray,
    feature_cols: list[str],
    params: dict[str, Any],
    random_state: int,
) -> tuple[float, pd.DataFrame]:
    train_df = feat_df.iloc[train_idx].copy()
    groups = train_df["source_id"].fillna("src").astype(str).to_numpy()
    y = train_df["y"].to_numpy(dtype=int)
    n_groups = int(pd.Series(groups).nunique(dropna=True))
    if n_groups < 2:
        return np.nan, pd.DataFrame()

    scores = []
    fold_rows = []
    gss = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=random_state)
    for fold_id, (tr_rel, te_rel) in enumerate(gss.split(train_df, y, groups=groups), start=1):
        fold_train = train_df.iloc[tr_rel]
        fold_test = train_df.iloc[te_rel]
        y_train = y[tr_rel]
        y_test = y[te_rel]
        X_train, X_test, kept, meta = _stabilize_feature_frames(fold_train, fold_test, feature_cols)
        row = {
            "fold_id": fold_id,
            "kept_feature_count": int(len(kept)),
            "removed_all_nan_count": int(len(meta["removed_all_nan"])),
            "removed_zero_var_count": int(len(meta["removed_zero_var"])),
            "removed_all_nan": _serialize_list(meta["removed_all_nan"]),
            "removed_zero_var": _serialize_list(meta["removed_zero_var"]),
        }
        if not kept or len(np.unique(y_train)) < 2 or len(np.unique(y_test)) < 2:
            row["roc_auc"] = np.nan
            fold_rows.append(row)
            continue
        model = _make_hgb(params, random_state=random_state)
        model.fit(X_train, y_train)
        pred = _predict_score(model, X_test)
        auc = _roc_auc_rank(y_test, pred)
        row["roc_auc"] = auc
        fold_rows.append(row)
        if np.isfinite(auc):
            scores.append(float(auc))
    return (float(np.mean(scores)) if scores else np.nan), pd.DataFrame(fold_rows)


def _search_best_hgb_params(
    feat_df: pd.DataFrame,
    train_idx: np.ndarray,
    feature_cols: list[str],
    random_state: int,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    rows = []
    fold_frames = []
    for params in _hgb_param_grid():
        cv_auc, fold_df = _grouped_cv_score_hgb(
            feat_df=feat_df,
            train_idx=train_idx,
            feature_cols=feature_cols,
            params=params,
            random_state=random_state,
        )
        row = dict(params)
        row["grouped_cv_roc_auc"] = cv_auc
        rows.append(row)
        if not fold_df.empty:
            tmp = fold_df.copy()
            tmp["params"] = str(params)
            fold_frames.append(tmp)
    res = pd.DataFrame(rows).sort_values(
        ["grouped_cv_roc_auc", "learning_rate", "max_leaf_nodes"],
        ascending=[False, True, True],
        na_position="last",
    ).reset_index(drop=True)
    if res.empty:
        raise RuntimeError("hyperparameter search returned no rows")
    best = res.iloc[0]
    best_params = {
        "learning_rate": float(best["learning_rate"]),
        "max_leaf_nodes": int(best["max_leaf_nodes"]),
        "min_samples_leaf": int(best["min_samples_leaf"]),
        "max_depth": None if pd.isna(best["max_depth"]) else int(best["max_depth"]),
        "l2_regularization": float(best["l2_regularization"]),
    }
    best_fold_df = pd.DataFrame()
    if fold_frames:
        all_folds = pd.concat(fold_frames, ignore_index=True)
        best_fold_df = all_folds[all_folds["params"] == str(best_params)].copy()
    return best_params, res, best_fold_df


def _evaluate_scores(
    model_name: str,
    feature_set: str,
    split_name: str,
    split_kind: str,
    train_y: np.ndarray,
    test_y: np.ndarray,
    train_score: np.ndarray,
    test_score: np.ndarray,
    candidate_feature_count: int,
    kept_features: list[str],
    meta: dict[str, list[str]] | None = None,
    best_params: dict[str, Any] | None = None,
    note: str = "",
) -> dict[str, Any]:
    roc_auc = roc_auc_score(test_y, test_score) if len(np.unique(test_y)) > 1 else np.nan
    ap = average_precision_score(test_y, test_score) if int(np.sum(test_y == 1)) > 0 else np.nan

    thr_best = _best_f1_threshold(train_y, train_score)
    pred_best = test_score > thr_best if np.isfinite(thr_best) else np.zeros(len(test_score), dtype=bool)
    p_best, r_best, f1_best = _precision_recall_f1(test_y, pred_best)

    tau_fpr1 = _threshold_at_fpr(train_score[train_y == 0], fpr=FPR1)
    pred_fpr1 = test_score > tau_fpr1 if np.isfinite(tau_fpr1) else np.zeros(len(test_score), dtype=bool)
    p_fpr1, r_fpr1, f1_fpr1 = _precision_recall_f1(test_y, pred_fpr1)
    actual_fpr = float(np.mean(pred_fpr1[test_y == 0])) if int(np.sum(test_y == 0)) > 0 else np.nan

    return {
        "model": model_name,
        "split_name": split_name,
        "split_kind": split_kind,
        "n_train": int(len(train_y)),
        "n_test": int(len(test_y)),
        "n_pos_train": int(np.sum(train_y == 1)),
        "n_pos_test": int(np.sum(test_y == 1)),
        "feature_set": feature_set,
        "candidate_feature_count": int(candidate_feature_count),
        "kept_feature_count": int(len(kept_features)),
        "kept_features": _serialize_list(kept_features),
        "removed_all_nan_count": int(len((meta or {}).get("removed_all_nan", []))),
        "removed_zero_var_count": int(len((meta or {}).get("removed_zero_var", []))),
        "removed_all_nan": _serialize_list((meta or {}).get("removed_all_nan", [])),
        "removed_zero_var": _serialize_list((meta or {}).get("removed_zero_var", [])),
        "roc_auc": float(roc_auc) if np.isfinite(roc_auc) else np.nan,
        "ap": float(ap) if np.isfinite(ap) else np.nan,
        "threshold_best": float(thr_best) if np.isfinite(thr_best) else np.nan,
        "precision_best": p_best,
        "recall_best": r_best,
        "f1_best": f1_best,
        "threshold_fpr1": float(tau_fpr1) if np.isfinite(tau_fpr1) else np.nan,
        "actual_fpr_fpr1": actual_fpr,
        "precision_fpr1": p_fpr1,
        "recall_fpr1": r_fpr1,
        "f1_fpr1": f1_fpr1,
        "best_params": "" if best_params is None else str(best_params),
        "note": note,
    }


def run_supervised(
    scores_csv: pathlib.Path,
    out_csv: pathlib.Path,
    out_md: pathlib.Path,
    test_size: float,
    random_state: int,
) -> tuple[pd.DataFrame, pathlib.Path, pathlib.Path]:
    if not scores_csv.exists():
        raise FileNotFoundError(scores_csv)
    df = pd.read_csv(scores_csv)
    _check_required(df)
    feat_df, feature_cols = _feature_engineering(df)
    y = feat_df["y"].to_numpy(dtype=int)
    groups = feat_df["source_id"].fillna("src").astype(str).to_numpy()
    feature_sets = _candidate_feature_sets()

    baseline_score, baseline_auc, baseline_ap = _baseline_best_single(feat_df)
    baseline_series = pd.to_numeric(feat_df[baseline_score], errors="coerce") if baseline_score else pd.Series(np.nan, index=feat_df.index)

    split_defs: list[tuple[str, str, np.ndarray, np.ndarray]] = []
    tr_idx, te_idx = train_test_split(np.arange(len(feat_df)), test_size=test_size, random_state=random_state, stratify=y)
    split_defs.append(("pooled_random", "optimistic_window_split", np.asarray(tr_idx), np.asarray(te_idx)))
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    tr_g, te_g = next(gss.split(feat_df, y, groups=groups))
    split_defs.append(("grouped_source", "stricter_file_split", np.asarray(tr_g), np.asarray(te_g)))

    rows: list[dict[str, Any]] = []
    removal_rows: list[dict[str, Any]] = []
    split_index = {name: (kind, train_idx, test_idx) for name, kind, train_idx, test_idx in split_defs}

    for split_name, split_kind, train_idx, test_idx in split_defs:
        y_train = y[train_idx]
        y_test = y[test_idx]
        base_train = pd.to_numeric(baseline_series.iloc[train_idx], errors="coerce").to_numpy(dtype=float)
        base_test = pd.to_numeric(baseline_series.iloc[test_idx], errors="coerce").to_numpy(dtype=float)
        rows.append(
            _evaluate_scores(
                model_name=f"baseline_best_single::{baseline_score}",
                feature_set="baseline_best_single",
                split_name=split_name,
                split_kind=split_kind,
                train_y=y_train,
                test_y=y_test,
                train_score=base_train,
                test_score=base_test,
                candidate_feature_count=1,
                kept_features=[baseline_score] if baseline_score else [],
                meta={"removed_all_nan": [], "removed_zero_var": []},
                note="unsupervised comparator",
            )
        )

    grouped_kind, grouped_train_idx, grouped_test_idx = split_index["grouped_source"]

    for feature_set_name, feature_set_cols in feature_sets.items():
        best_hgb_params, search_df, best_fold_df = _search_best_hgb_params(
            feat_df=feat_df,
            train_idx=grouped_train_idx,
            feature_cols=feature_set_cols,
            random_state=random_state,
        )
        if not best_fold_df.empty:
            tmp = best_fold_df.copy()
            tmp["feature_set"] = feature_set_name
            tmp["stage"] = "grouped_cv"
            removal_rows.extend(tmp.to_dict(orient="records"))

        for split_name, split_kind, train_idx, test_idx in split_defs:
            train_df = feat_df.iloc[train_idx]
            test_df = feat_df.iloc[test_idx]
            y_train = y[train_idx]
            y_test = y[test_idx]

            logreg = _build_logreg()
            log_train, log_test, kept_log, meta_log = _fit_predict_with_feature_set(
                model=logreg,
                train_df=train_df,
                test_df=test_df,
                train_y=y_train,
                feature_cols=feature_set_cols,
            )
            removal_rows.append(
                {
                    "feature_set": feature_set_name,
                    "stage": f"{split_name}__LogisticRegression",
                    "fold_id": np.nan,
                    "kept_feature_count": int(len(kept_log)),
                    "removed_all_nan_count": int(len(meta_log["removed_all_nan"])),
                    "removed_zero_var_count": int(len(meta_log["removed_zero_var"])),
                    "removed_all_nan": _serialize_list(meta_log["removed_all_nan"]),
                    "removed_zero_var": _serialize_list(meta_log["removed_zero_var"]),
                    "roc_auc": np.nan,
                }
            )
            rows.append(
                _evaluate_scores(
                    model_name="LogisticRegression",
                    feature_set=feature_set_name,
                    split_name=split_name,
                    split_kind=split_kind,
                    train_y=y_train,
                    test_y=y_test,
                    train_score=log_train,
                    test_score=log_test,
                    candidate_feature_count=len(feature_set_cols),
                    kept_features=kept_log,
                    meta=meta_log,
                    note="fold-wise stabilized features",
                )
            )

            hgb = _make_hgb(best_hgb_params, random_state=random_state)
            hgb_train, hgb_test, kept_hgb, meta_hgb = _fit_predict_with_feature_set(
                model=hgb,
                train_df=train_df,
                test_df=test_df,
                train_y=y_train,
                feature_cols=feature_set_cols,
            )
            removal_rows.append(
                {
                    "feature_set": feature_set_name,
                    "stage": f"{split_name}__HistGradientBoostingClassifier_tuned",
                    "fold_id": np.nan,
                    "kept_feature_count": int(len(kept_hgb)),
                    "removed_all_nan_count": int(len(meta_hgb["removed_all_nan"])),
                    "removed_zero_var_count": int(len(meta_hgb["removed_zero_var"])),
                    "removed_all_nan": _serialize_list(meta_hgb["removed_all_nan"]),
                    "removed_zero_var": _serialize_list(meta_hgb["removed_zero_var"]),
                    "roc_auc": np.nan,
                }
            )
            rows.append(
                _evaluate_scores(
                    model_name="HistGradientBoostingClassifier_tuned",
                    feature_set=feature_set_name,
                    split_name=split_name,
                    split_kind=split_kind,
                    train_y=y_train,
                    test_y=y_test,
                    train_score=hgb_train,
                    test_score=hgb_test,
                    candidate_feature_count=len(feature_set_cols),
                    kept_features=kept_hgb,
                    meta=meta_hgb,
                    best_params=best_hgb_params,
                    note="best params selected on grouped_source train only",
                )
            )

    metrics = pd.DataFrame(rows)
    metrics.to_csv(out_csv, index=False, encoding="utf-8-sig")
    removal_df = pd.DataFrame(removal_rows)

    grouped_rows = metrics[metrics["split_name"] == "grouped_source"].copy()
    pooled_rows = metrics[metrics["split_name"] == "pooled_random"].copy()
    grouped_table = grouped_rows[
        ["feature_set", "model", "roc_auc", "ap", "f1_best", "f1_fpr1", "kept_feature_count", "removed_all_nan_count", "removed_zero_var_count"]
    ].sort_values(["roc_auc", "ap"], ascending=False, na_position="last")
    pooled_table = pooled_rows[
        ["feature_set", "model", "roc_auc", "ap", "f1_best", "f1_fpr1", "kept_feature_count", "removed_all_nan_count", "removed_zero_var_count"]
    ].sort_values(["roc_auc", "ap"], ascending=False, na_position="last")

    grouped_candidates = grouped_rows[grouped_rows["model"].isin(["LogisticRegression", "HistGradientBoostingClassifier_tuned"])].copy()
    best_grouped = grouped_candidates.sort_values(["roc_auc", "ap"], ascending=False, na_position="last").head(1)
    grouped_baseline = grouped_rows[grouped_rows["feature_set"] == "baseline_best_single"].head(1)
    delta_df = pd.DataFrame()
    if not best_grouped.empty and not grouped_baseline.empty:
        bg = best_grouped.iloc[0]
        bl = grouped_baseline.iloc[0]
        delta_df = pd.DataFrame(
            [
                {
                    "baseline_model": bl["model"],
                    "best_grouped_model": bg["model"],
                    "best_grouped_feature_set": bg["feature_set"],
                    "roc_auc_delta": bg["roc_auc"] - bl["roc_auc"],
                    "ap_delta": bg["ap"] - bl["ap"],
                    "f1_best_delta": bg["f1_best"] - bl["f1_best"],
                    "f1_fpr1_delta": bg["f1_fpr1"] - bl["f1_fpr1"],
                }
            ]
        )

    grouped_feature_family = (
        grouped_candidates.groupby("feature_set", as_index=False)
        .agg(
            best_roc_auc=("roc_auc", "max"),
            best_ap=("ap", "max"),
            mean_kept_feature_count=("kept_feature_count", "mean"),
            mean_removed_all_nan=("removed_all_nan_count", "mean"),
            mean_removed_zero_var=("removed_zero_var_count", "mean"),
        )
        .sort_values(["best_roc_auc", "best_ap"], ascending=False, na_position="last")
    )

    lines = []
    lines.append("# EXTERNAL GPVS SUPERVISED3 ONEPAGE")
    lines.append("")
    lines.append("## 목적")
    lines.append("- 전반부 normal / 후반부 fault 라벨을 이용한 supervised 3차 benchmark입니다.")
    lines.append("- 이번 패스의 최적화 기준은 optimistic split이 아니라 `grouped_source` 일반화 성능입니다.")
    lines.append("")
    lines.append("## feature set 요약")
    lines.append("- `stable_like_all`: like 5종 + mode + active_axis_count + degenerate flags")
    lines.append("- `stable_like_shape_first`: dtw/hs/ae like + mode + active_axis_count + degenerate flags")
    lines.append("- `raw_no_norm_all`: raw 5종 + mode + active_axis_count + degenerate flags + raw delta + raw rollmean3 + raw rollmax3")
    lines.append("- `mixed_no_norm`: like 5종 + raw 5종 + mode + active_axis_count + degenerate flags + raw delta + raw rollmean3 + raw rollmax3")
    lines.append("- `norm_level_drop_raw`, `norm_v_drop_raw` 및 norm rolling 파생은 이번 패스에서 의도적으로 제외했습니다.")
    lines.append("")
    lines.append("## baseline")
    lines.append(f"- baseline_best_single: `{baseline_score}`")
    lines.append(f"- full-data baseline roc_auc: {_fmt(baseline_auc)}")
    lines.append(f"- full-data baseline ap: {_fmt(baseline_ap)}")
    lines.append("")
    lines.append("## grouped_source 기준 feature set별 결과")
    lines.append(_to_md_table(grouped_table))
    lines.append("")
    lines.append("## pooled_random 참고표")
    lines.append(_to_md_table(pooled_table))
    lines.append("")
    lines.append("## best grouped_source model")
    lines.append(_to_md_table(best_grouped[["feature_set", "model", "roc_auc", "ap", "f1_best", "f1_fpr1", "best_params", "kept_feature_count"]]))
    lines.append("")
    lines.append("## baseline_best_single 대비 개선폭")
    lines.append(_to_md_table(delta_df))
    lines.append("")
    lines.append("## grouped에서 살아남은 feature family")
    lines.append(_to_md_table(grouped_feature_family))
    lines.append("")
    lines.append("## fold별 제거 feature 요약")
    if removal_df.empty:
        lines.append("_(no removal summary rows)_")
    else:
        removal_show = removal_df[
            ["feature_set", "stage", "fold_id", "kept_feature_count", "removed_all_nan_count", "removed_zero_var_count", "removed_all_nan", "removed_zero_var"]
        ].copy()
        lines.append(_to_md_table(removal_show))
    lines.append("")
    lines.append("## split 해석")
    lines.append("- `pooled_random`: 윈도우 단위 랜덤 분할이라 optimistic 참고용입니다.")
    lines.append("- `grouped_source`: `source_id` 기준 holdout이며, 이번 패스의 하이퍼파라미터 선택 기준입니다.")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return metrics, out_csv, out_md


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Train supervised GPVS benchmark models from gpvs_window_scores.csv")
    ap.add_argument("--scores-csv", default="data/gpvs/out/gpvs_window_scores.csv", help="Input GPVS window score CSV")
    ap.add_argument("--out-csv", default="data/gpvs/out/EXTERNAL_GPVS_SUPERVISED3_METRICS.csv", help="Output supervised3 metrics CSV")
    ap.add_argument("--out-md", default="data/gpvs/out/EXTERNAL_GPVS_SUPERVISED3_ONEPAGE.md", help="Output supervised3 onepage markdown")
    ap.add_argument("--test-size", type=float, default=0.3, help="Test size for both split settings")
    ap.add_argument("--random-state", type=int, default=42, help="Random seed")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    metrics, out_csv, out_md = run_supervised(
        scores_csv=pathlib.Path(args.scores_csv),
        out_csv=pathlib.Path(args.out_csv),
        out_md=pathlib.Path(args.out_md),
        test_size=float(args.test_size),
        random_state=int(args.random_state),
    )
    print(f"[OK] rows(metrics): {len(metrics)}")
    print(f"[OK] wrote metrics: {out_csv}")
    print(f"[OK] wrote onepage: {out_md}")


if __name__ == "__main__":
    main()
