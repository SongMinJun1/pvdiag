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


def evaluate(scores_csv: pathlib.Path, out_csv: pathlib.Path, out_md: pathlib.Path, k: int, thr_q: float) -> tuple[pd.DataFrame, pathlib.Path, pathlib.Path]:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    metrics_cols = [
        "score",
        "n_valid",
        "n_pos",
        "base_rate",
        "auc",
        "ap",
        "precision_at_k",
        "k_used",
        "thr_q",
        "thr_val",
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
        return metrics, out_csv, out_md

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
        s = pd.to_numeric(df[sc], errors="coerce").to_numpy(dtype=float)
        m = np.isfinite(s) & np.isfinite(y)
        yy = y[m]
        ss = s[m]
        if len(yy) == 0:
            excluded.append(f"{sc}(all_nan)")
            continue
        auc = _roc_auc_rank(yy, ss)
        ap = _average_precision(yy, ss)
        p_at_k, k_used = _precision_at_k(yy, ss, k)
        delay = _detection_delay(ss, yy, source[m], order[m], k=k, thr_q=thr_q)
        rows.append(
            {
                "score": sc,
                "n_valid": int(len(yy)),
                "n_pos": int(np.sum(yy == 1)),
                "base_rate": float(np.mean(yy == 1)) if len(yy) else np.nan,
                "auc": auc,
                "ap": ap,
                "precision_at_k": p_at_k,
                "k_used": int(k_used),
                "thr_q": delay["thr_q"],
                "thr_val": delay["thr_val"],
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
        metrics = metrics.sort_values(["ap", "auc"], ascending=False, na_position="last").reset_index(drop=True)
    metrics.to_csv(out_csv, index=False, encoding="utf-8-sig")

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
    lines.append("## 점수별 AUC/AP/precision@K")
    lines.append(_to_md_table(metrics[["score", "auc", "ap", "precision_at_k", "k_used", "detect_rate", "delay_median_windows"]] if not metrics.empty else metrics))
    lines.append("")
    lines.append("## 축 반응 해석")
    lines.extend(summary_lines)
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
    return metrics, out_csv, out_md


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Evaluate GPVS external benchmark from gpvs_window_scores.csv")
    ap.add_argument("--scores-csv", default="data/gpvs/out/gpvs_window_scores.csv", help="Input window score csv")
    ap.add_argument("--out-csv", default="data/gpvs/out/EXTERNAL_GPVS_METRICS.csv", help="Output metrics csv")
    ap.add_argument("--out-md", default="data/gpvs/out/EXTERNAL_GPVS_ONEPAGE.md", help="Output onepage markdown")
    ap.add_argument("--k", type=int, default=20, help="K for precision@K and topK delay rule")
    ap.add_argument("--thr-q", type=float, default=0.95, help="Healthy quantile for score threshold in delay metric")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    metrics, out_csv, out_md = evaluate(
        scores_csv=pathlib.Path(args.scores_csv),
        out_csv=pathlib.Path(args.out_csv),
        out_md=pathlib.Path(args.out_md),
        k=int(args.k),
        thr_q=float(args.thr_q),
    )
    print(f"[OK] rows(metrics): {len(metrics)}")
    print(f"[OK] wrote metrics: {out_csv}")
    print(f"[OK] wrote onepage: {out_md}")


if __name__ == "__main__":
    main()
