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
        work[f"delta_{raw_col}"] = (
            sorted_df.groupby("source_id")[raw_col].diff().reindex(sorted_df.index).reindex(work.index)
        )
        work[f"rollmean3_{raw_col}"] = _group_rolling_feature(work, raw_col, order_col, 3, "mean")
        work[f"rollstd3_{raw_col}"] = _group_rolling_feature(work, raw_col, order_col, 3, "std").fillna(0.0)

    deg_cols = []
    deg_norm_cols = []
    span_cols = []
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
                span = np.nan
                med = np.nan
                mad = np.nan
            else:
                n_unique = int(pd.Series(pre_vals).nunique(dropna=True))
                span = float(np.max(pre_vals) - np.min(pre_vals))
                deg = float(n_unique <= 1 or (np.isfinite(span) and span <= SPAN_EPS))
                med = float(np.median(pre_vals))
                mad = float(np.median(np.abs(pre_vals - med)))
            deg_name = f"deg_{raw_col}"
            span_name = f"span_{raw_col}"
            norm_name = f"norm_{raw_col}"
            deg_norm_name = f"deg_norm_{raw_col}"
            work.loc[idx, deg_name] = deg
            work.loc[idx, span_name] = span
            if not np.isfinite(mad) or mad <= 0.0:
                work.loc[idx, norm_name] = np.nan
                work.loc[idx, deg_norm_name] = 1.0
            else:
                work.loc[idx, norm_name] = (pd.to_numeric(g[raw_col], errors="coerce").to_numpy(dtype=float) - med) / (1.4826 * mad)
                work.loc[idx, deg_norm_name] = 0.0
            if deg == 0.0:
                active += 1
            if deg_name not in deg_cols:
                deg_cols.append(deg_name)
            if deg_norm_name not in deg_norm_cols:
                deg_norm_cols.append(deg_norm_name)
            if span_name not in span_cols:
                span_cols.append(span_name)
        active_axis_count.loc[idx] = float(active)
    work["active_axis_count"] = active_axis_count

    norm_cols = [f"norm_{c}" for c in RAW_COLS]
    for norm_col in norm_cols:
        work[norm_col] = pd.to_numeric(work[norm_col], errors="coerce")
        work[f"rollmean3_{norm_col}"] = _group_rolling_feature(work, norm_col, order_col, 3, "mean")
        work[f"rollmax3_{norm_col}"] = _group_rolling_feature(work, norm_col, order_col, 3, "max")
        work[f"rollmean5_{norm_col}"] = _group_rolling_feature(work, norm_col, order_col, 5, "mean")
        work[f"rollmax5_{norm_col}"] = _group_rolling_feature(work, norm_col, order_col, 5, "max")

    base_features = ["mode_L", "mode_M"] + RAW_COLS + norm_cols + LIKE_COLS + ["active_axis_count"] + deg_cols + deg_norm_cols + span_cols
    delta_features = [f"delta_{c}" for c in RAW_COLS]
    rollmean_features = [f"rollmean3_{c}" for c in RAW_COLS]
    rollstd_features = [f"rollstd3_{c}" for c in RAW_COLS]
    norm_roll_features = []
    for norm_col in norm_cols:
        norm_roll_features.extend(
            [
                f"rollmean3_{norm_col}",
                f"rollmax3_{norm_col}",
                f"rollmean5_{norm_col}",
                f"rollmax5_{norm_col}",
            ]
        )
    feature_cols = base_features + delta_features + rollmean_features + rollstd_features + norm_roll_features
    return work, feature_cols


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
                    max_iter=120,
                    random_state=random_state,
                ),
            ),
        ]
    )


def _hgb_param_grid() -> list[dict[str, Any]]:
    grid = []
    for lr, leaf, min_leaf, depth, l2 in product(
        [0.05, 0.1],
        [31, 63],
        [20],
        [None],
        [0.0],
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


def _predict_score(model: Any, X_eval: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X_eval)[:, 1]
    if hasattr(model, "decision_function"):
        s = model.decision_function(X_eval)
        return 1.0 / (1.0 + np.exp(-np.asarray(s, dtype=float)))
    raise RuntimeError("model does not expose predict_proba or decision_function")


def _fit_predict_mode_aware_hgb(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    mode_train: pd.Series,
    X_eval: pd.DataFrame,
    mode_eval: pd.Series,
    params: dict[str, Any],
    random_state: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    fallback = _make_hgb(params, random_state=random_state)
    fallback.fit(X_train, y_train)
    preds = _predict_score(fallback, X_eval)
    models: dict[str, Any] = {"fallback": fallback}

    for mode in ["L", "M"]:
        mask = mode_train.eq(mode).to_numpy()
        if int(np.sum(mask)) == 0:
            continue
        y_sub = y_train[mask]
        if len(np.unique(y_sub)) < 2:
            continue
        model = _make_hgb(params, random_state=random_state)
        model.fit(X_train.iloc[mask], y_sub)
        models[mode] = model
        eval_mask = mode_eval.eq(mode).to_numpy()
        if int(np.sum(eval_mask)) > 0:
            preds[eval_mask] = _predict_score(model, X_eval.iloc[eval_mask])
    return preds, models


def _grouped_cv_score_hgb(
    X: pd.DataFrame,
    y: np.ndarray,
    groups: np.ndarray,
    modes: pd.Series,
    params: dict[str, Any],
    random_state: int,
    mode_aware: bool,
) -> float:
    n_groups = int(pd.Series(groups).nunique(dropna=True))
    n_splits = min(2, n_groups)
    if n_splits < 2:
        return np.nan
    gkf = GroupKFold(n_splits=n_splits)
    scores = []
    for tr_idx, te_idx in gkf.split(X, y, groups):
        X_train = X.iloc[tr_idx]
        X_test = X.iloc[te_idx]
        y_train = y[tr_idx]
        y_test = y[te_idx]
        if len(np.unique(y_train)) < 2 or len(np.unique(y_test)) < 2:
            continue
        if mode_aware:
            pred, _ = _fit_predict_mode_aware_hgb(
                X_train=X_train,
                y_train=y_train,
                mode_train=modes.iloc[tr_idx],
                X_eval=X_test,
                mode_eval=modes.iloc[te_idx],
                params=params,
                random_state=random_state,
            )
        else:
            model = _make_hgb(params, random_state=random_state)
            model.fit(X_train, y_train)
            pred = _predict_score(model, X_test)
        if len(np.unique(y_test)) < 2:
            continue
        scores.append(float(roc_auc_score(y_test, pred)))
    return float(np.mean(scores)) if scores else np.nan


def _search_best_hgb_params(
    X: pd.DataFrame,
    y: np.ndarray,
    groups: np.ndarray,
    modes: pd.Series,
    random_state: int,
    mode_aware: bool,
) -> tuple[dict[str, Any], pd.DataFrame]:
    rows = []
    for params in _hgb_param_grid():
        cv_auc = _grouped_cv_score_hgb(
            X=X,
            y=y,
            groups=groups,
            modes=modes,
            params=params,
            random_state=random_state,
            mode_aware=mode_aware,
        )
        row = dict(params)
        row["mode_aware"] = int(mode_aware)
        row["grouped_cv_roc_auc"] = cv_auc
        rows.append(row)
    res = pd.DataFrame(rows).sort_values(["grouped_cv_roc_auc"], ascending=False, na_position="last").reset_index(drop=True)
    if res.empty:
        raise RuntimeError("hyperparameter search returned no rows")
    best = res.iloc[0]
    return {
        "learning_rate": float(best["learning_rate"]),
        "max_leaf_nodes": int(best["max_leaf_nodes"]),
        "min_samples_leaf": int(best["min_samples_leaf"]),
        "max_depth": None if pd.isna(best["max_depth"]) else int(best["max_depth"]),
        "l2_regularization": float(best["l2_regularization"]),
    }, res


def _evaluate_scores(
    model_name: str,
    split_name: str,
    split_kind: str,
    train_y: np.ndarray,
    test_y: np.ndarray,
    train_score: np.ndarray,
    test_score: np.ndarray,
    feature_count: int,
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
        "feature_count": int(feature_count),
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
        "note": note,
    }


def run_supervised(
    scores_csv: pathlib.Path,
    out_csv: pathlib.Path,
    out_md: pathlib.Path,
    baseline_csv: pathlib.Path | None,
    test_size: float,
    random_state: int,
) -> tuple[pd.DataFrame, pathlib.Path, pathlib.Path]:
    if not scores_csv.exists():
        raise FileNotFoundError(scores_csv)
    df = pd.read_csv(scores_csv)
    _check_required(df)
    feat_df, feature_cols = _feature_engineering(df)
    X = feat_df[feature_cols].copy()
    y = feat_df["y"].to_numpy(dtype=int)
    groups = feat_df["source_id"].fillna("src").astype(str).to_numpy()
    modes = feat_df["mode"].copy()

    baseline_score, baseline_auc, baseline_ap = _baseline_best_single(feat_df)
    baseline_series = pd.to_numeric(feat_df[baseline_score], errors="coerce") if baseline_score else pd.Series(np.nan, index=feat_df.index)

    best_hgb_params, hgb_search = _search_best_hgb_params(
        X=X,
        y=y,
        groups=groups,
        modes=modes,
        random_state=random_state,
        mode_aware=False,
    )
    best_mode_params, mode_hgb_search = _search_best_hgb_params(
        X=X,
        y=y,
        groups=groups,
        modes=modes,
        random_state=random_state,
        mode_aware=True,
    )

    split_defs: list[tuple[str, str, np.ndarray, np.ndarray]] = []
    tr_idx, te_idx = train_test_split(np.arange(len(feat_df)), test_size=test_size, random_state=random_state, stratify=y)
    split_defs.append(("pooled_random", "optimistic_window_split", np.asarray(tr_idx), np.asarray(te_idx)))
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    tr_g, te_g = next(gss.split(X, y, groups=groups))
    split_defs.append(("grouped_source", "stricter_file_split", np.asarray(tr_g), np.asarray(te_g)))

    rows: list[dict[str, Any]] = []
    for split_name, split_kind, train_idx, test_idx in split_defs:
        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]
        y_train = y[train_idx]
        y_test = y[test_idx]
        mode_train = modes.iloc[train_idx]
        mode_test = modes.iloc[test_idx]

        base_train = pd.to_numeric(baseline_series.iloc[train_idx], errors="coerce").to_numpy(dtype=float)
        base_test = pd.to_numeric(baseline_series.iloc[test_idx], errors="coerce").to_numpy(dtype=float)
        rows.append(
            _evaluate_scores(
                model_name=f"baseline_best_single::{baseline_score}",
                split_name=split_name,
                split_kind=split_kind,
                train_y=y_train,
                test_y=y_test,
                train_score=base_train,
                test_score=base_test,
                feature_count=1,
                note="unsupervised comparator",
            )
        )

        logreg = _build_logreg()
        logreg.fit(X_train, y_train)
        rows.append(
            _evaluate_scores(
                model_name="LogisticRegression",
                split_name=split_name,
                split_kind=split_kind,
                train_y=y_train,
                test_y=y_test,
                train_score=_predict_score(logreg, X_train),
                test_score=_predict_score(logreg, X_test),
                feature_count=len(feature_cols),
                note="baseline supervised",
            )
        )

        hgb = _make_hgb(best_hgb_params, random_state=random_state)
        hgb.fit(X_train, y_train)
        rows.append(
            _evaluate_scores(
                model_name="HistGradientBoostingClassifier_tuned",
                split_name=split_name,
                split_kind=split_kind,
                train_y=y_train,
                test_y=y_test,
                train_score=_predict_score(hgb, X_train),
                test_score=_predict_score(hgb, X_test),
                feature_count=len(feature_cols),
                note=f"best_grouped_params={best_hgb_params}",
            )
        )

        mode_train_score, _ = _fit_predict_mode_aware_hgb(
            X_train=X_train,
            y_train=y_train,
            mode_train=mode_train,
            X_eval=X_train,
            mode_eval=mode_train,
            params=best_mode_params,
            random_state=random_state,
        )
        mode_test_score, _ = _fit_predict_mode_aware_hgb(
            X_train=X_train,
            y_train=y_train,
            mode_train=mode_train,
            X_eval=X_test,
            mode_eval=mode_test,
            params=best_mode_params,
            random_state=random_state,
        )
        rows.append(
            _evaluate_scores(
                model_name="HistGradientBoostingClassifier_mode_aware",
                split_name=split_name,
                split_kind=split_kind,
                train_y=y_train,
                test_y=y_test,
                train_score=mode_train_score,
                test_score=mode_test_score,
                feature_count=len(feature_cols),
                note=f"best_grouped_mode_params={best_mode_params}",
            )
        )

    metrics = pd.DataFrame(rows)
    metrics.to_csv(out_csv, index=False, encoding="utf-8-sig")

    cmp = metrics[["split_name", "split_kind", "model", "roc_auc", "ap", "f1_best", "f1_fpr1"]].copy()
    best_by_split = (
        metrics[metrics["model"].isin(["LogisticRegression", "HistGradientBoostingClassifier_tuned", "HistGradientBoostingClassifier_mode_aware"])]
        .sort_values(["split_name", "roc_auc", "ap"], ascending=[True, False, False], na_position="last")
        .groupby("split_name", as_index=False)
        .first()[["split_name", "model", "roc_auc", "ap", "f1_best", "f1_fpr1"]]
    )

    sup1_hgb = pd.DataFrame()
    if baseline_csv is not None and baseline_csv.exists():
        prev = pd.read_csv(baseline_csv)
        sup1_hgb = prev[prev["model"] == "HistGradientBoostingClassifier"].copy()

    lines = []
    lines.append("# EXTERNAL GPVS SUPERVISED2 ONEPAGE")
    lines.append("")
    lines.append("## 목적")
    lines.append("- 전반부 normal / 후반부 fault 라벨을 이용한 supervised 2차 benchmark입니다.")
    lines.append("- 목표는 `grouped_source` 일반화 성능 향상입니다.")
    lines.append("")
    lines.append("## feature family 요약")
    lines.append(f"- total feature count: {len(feature_cols)}")
    lines.append("- 기존 feature 유지: raw/like/mode/active_axis/degenerate/span/delta/rolling std/mean")
    lines.append("- 추가: `norm_*` (file-wise pre-half robust normalization)")
    lines.append("- 추가: `rollmean3_norm_*`, `rollmax3_norm_*`, `rollmean5_norm_*`, `rollmax5_norm_*`")
    lines.append("")
    lines.append("## baseline")
    lines.append(f"- baseline_best_single: `{baseline_score}`")
    lines.append(f"- full-data baseline roc_auc: {_fmt(baseline_auc)}")
    lines.append(f"- full-data baseline ap: {_fmt(baseline_ap)}")
    lines.append("")
    lines.append("## best hyperparameters")
    lines.append(f"- HGB pooled tuned: `{best_hgb_params}`")
    lines.append(f"- HGB mode-aware tuned: `{best_mode_params}`")
    lines.append("")
    lines.append("## model별 결과")
    lines.append(_to_md_table(cmp))
    lines.append("")
    lines.append("## split 해석")
    lines.append("- `pooled_random`: 윈도우 단위 랜덤 분할로 같은 file의 상관 구조가 train/test에 함께 들어갈 수 있어 optimistic합니다.")
    lines.append("- `grouped_source`: `source_id` 기준 전체 file holdout이라 더 정직한 일반화 참고용입니다.")
    lines.append("")
    if not sup1_hgb.empty:
        lines.append("## supervised1 HGB vs supervised2 HGB")
        prev_cmp = sup1_hgb[["split_name", "roc_auc", "ap", "f1_best", "f1_fpr1"]].rename(
            columns={
                "roc_auc": "sup1_hgb_roc_auc",
                "ap": "sup1_hgb_ap",
                "f1_best": "sup1_hgb_f1_best",
                "f1_fpr1": "sup1_hgb_f1_fpr1",
            }
        )
        new_cmp = metrics[metrics["model"] == "HistGradientBoostingClassifier_mode_aware"][["split_name", "roc_auc", "ap", "f1_best", "f1_fpr1"]].rename(
            columns={
                "roc_auc": "sup2_mode_hgb_roc_auc",
                "ap": "sup2_mode_hgb_ap",
                "f1_best": "sup2_mode_hgb_f1_best",
                "f1_fpr1": "sup2_mode_hgb_f1_fpr1",
            }
        )
        delta = prev_cmp.merge(new_cmp, on="split_name", how="outer")
        if not delta.empty:
            delta["roc_auc_delta"] = delta["sup2_mode_hgb_roc_auc"] - delta["sup1_hgb_roc_auc"]
            delta["ap_delta"] = delta["sup2_mode_hgb_ap"] - delta["sup1_hgb_ap"]
            delta["f1_fpr1_delta"] = delta["sup2_mode_hgb_f1_fpr1"] - delta["sup1_hgb_f1_fpr1"]
        lines.append(_to_md_table(delta))
        lines.append("")
    lines.append("## best supervised by split")
    lines.append(_to_md_table(best_by_split))
    lines.append("")
    lines.append("## optimistic vs grouped gap")
    gap_rows = []
    for model_name in ["LogisticRegression", "HistGradientBoostingClassifier_tuned", "HistGradientBoostingClassifier_mode_aware"]:
        sub = metrics[metrics["model"] == model_name].set_index("split_name")
        if "pooled_random" in sub.index and "grouped_source" in sub.index:
            gap_rows.append(
                {
                    "model": model_name,
                    "roc_auc_gap": float(sub.loc["pooled_random", "roc_auc"] - sub.loc["grouped_source", "roc_auc"]),
                    "ap_gap": float(sub.loc["pooled_random", "ap"] - sub.loc["grouped_source", "ap"]),
                    "f1_fpr1_gap": float(sub.loc["pooled_random", "f1_fpr1"] - sub.loc["grouped_source", "f1_fpr1"]),
                }
            )
    lines.append(_to_md_table(pd.DataFrame(gap_rows)))
    lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return metrics, out_csv, out_md


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Train supervised GPVS benchmark models from gpvs_window_scores.csv")
    ap.add_argument("--scores-csv", default="data/gpvs/out/gpvs_window_scores.csv", help="Input GPVS window score CSV")
    ap.add_argument("--out-csv", default="data/gpvs/out/EXTERNAL_GPVS_SUPERVISED2_METRICS.csv", help="Output supervised2 metrics CSV")
    ap.add_argument("--out-md", default="data/gpvs/out/EXTERNAL_GPVS_SUPERVISED2_ONEPAGE.md", help="Output supervised2 onepage markdown")
    ap.add_argument("--baseline-csv", default="data/gpvs/out/EXTERNAL_GPVS_SUPERVISED_METRICS.csv", help="Existing supervised1 metrics CSV for comparison")
    ap.add_argument("--test-size", type=float, default=0.3, help="Test size for both split settings")
    ap.add_argument("--random-state", type=int, default=42, help="Random seed")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    metrics, out_csv, out_md = run_supervised(
        scores_csv=pathlib.Path(args.scores_csv),
        out_csv=pathlib.Path(args.out_csv),
        out_md=pathlib.Path(args.out_md),
        baseline_csv=pathlib.Path(args.baseline_csv) if args.baseline_csv else None,
        test_size=float(args.test_size),
        random_state=int(args.random_state),
    )
    print(f"[OK] rows(metrics): {len(metrics)}")
    print(f"[OK] wrote metrics: {out_csv}")
    print(f"[OK] wrote onepage: {out_md}")


if __name__ == "__main__":
    main()
