#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument(
        "--case",
        required=True,
        help='comma-separated "panel_id:onset_date", e.g. "pid1:2025-03-20,pid2:2025-12-18"',
    )
    ap.add_argument("--K", type=int, default=20)
    return ap.parse_args()


def parse_cases(case_s: str) -> list[tuple[str, pd.Timestamp]]:
    out: list[tuple[str, pd.Timestamp]] = []
    for tok in str(case_s).split(","):
        t = tok.strip()
        if not t:
            continue
        if ":" not in t:
            raise ValueError(f"invalid --case token (missing ':'): {t}")
        pid, ds = t.rsplit(":", 1)
        pid = pid.strip()
        d = pd.to_datetime(ds.strip(), errors="coerce")
        if not pid or pd.isna(d):
            raise ValueError(f"invalid --case token: {t}")
        out.append((pid, d.normalize()))
    if not out:
        raise ValueError("no valid cases parsed from --case")
    return out


def to_bool(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().isin(["1", "true", "t", "yes"])


def load_scores(out_dir: Path) -> pd.DataFrame:
    ae_path = out_dir / "ae_simple_scores.csv"
    if not ae_path.is_file():
        raise FileNotFoundError(f"missing: {ae_path}")
    ae = pd.read_csv(ae_path, low_memory=False, encoding="utf-8-sig")
    ae["date"] = pd.to_datetime(ae.get("date"), errors="coerce").dt.normalize()
    ae["panel_id"] = ae.get("panel_id").astype(str)
    ae = ae.dropna(subset=["date", "panel_id"]).copy()

    risk_path = out_dir / "scores_with_risk_ens.csv"
    if risk_path.is_file():
        rk = pd.read_csv(risk_path, low_memory=False, encoding="utf-8-sig")
        rk["date"] = pd.to_datetime(rk.get("date"), errors="coerce").dt.normalize()
        rk["panel_id"] = rk.get("panel_id").astype(str)
        rk = rk.dropna(subset=["date", "panel_id"]).copy()
        keep = [c for c in ["date", "panel_id", "risk_day", "risk_ens"] if c in rk.columns]
        ae = ae.merge(rk[keep], on=["date", "panel_id"], how="left", suffixes=("", "_risk"))
    return ae.sort_values(["panel_id", "date"]).reset_index(drop=True)


def panel_first_date(series: pd.Series) -> pd.Timestamp | pd.NaT:
    s = pd.to_datetime(series, errors="coerce").dropna()
    if s.empty:
        return pd.NaT
    return s.min()


def get_panel_summary(df: pd.DataFrame, panel_id: str, onset_manual: pd.Timestamp) -> dict[str, object]:
    g = df[df["panel_id"].astype(str) == str(panel_id)].copy().sort_values("date")

    first_obs_date = panel_first_date(g["date"]) if "date" in g.columns else pd.NaT
    dead_start_date = pd.NaT
    if "state_dead_eff" in g.columns:
        dd = g[to_bool(g["state_dead_eff"])]
        if not dd.empty:
            dead_start_date = dd["date"].min()

    if "diagnosis_date_online" in g.columns:
        diagnosis_date_online = panel_first_date(g["diagnosis_date_online"])
    else:
        dead_diag_date = panel_first_date(g["dead_diag_date"]) if "dead_diag_date" in g.columns else pd.NaT
        critical_diag_date = panel_first_date(g["critical_diag_date"]) if "critical_diag_date" in g.columns else pd.NaT
        diagnosis_date_online = pd.concat(
            [pd.Series([dead_diag_date]), pd.Series([critical_diag_date])], axis=1
        ).min(axis=1).iloc[0]

    final_fault_first_date = pd.NaT
    if "final_fault" in g.columns:
        ff = g[to_bool(g["final_fault"])]
        if not ff.empty:
            final_fault_first_date = ff["date"].min()

    onset_outside_window = bool(pd.notna(first_obs_date) and pd.notna(onset_manual) and (onset_manual < first_obs_date))

    confirm_delay_days = np.nan
    if pd.notna(diagnosis_date_online) and pd.notna(dead_start_date):
        confirm_delay_days = int((pd.to_datetime(diagnosis_date_online) - pd.to_datetime(dead_start_date)).days)

    delay_days = np.nan
    if (not onset_outside_window) and pd.notna(diagnosis_date_online) and pd.notna(onset_manual):
        delay_days = int((pd.to_datetime(diagnosis_date_online) - pd.to_datetime(onset_manual)).days)

    return {
        "panel_id": panel_id,
        "onset_manual": onset_manual,
        "first_obs_date": first_obs_date,
        "dead_start_date": dead_start_date,
        "diagnosis_date_online": diagnosis_date_online,
        "final_fault_first_date": final_fault_first_date,
        "confirm_delay_days": confirm_delay_days,
        "onset_outside_window": onset_outside_window,
        "delay_days": delay_days,
    }


def fmt_date(x: object) -> str:
    d = pd.to_datetime(x, errors="coerce")
    if pd.isna(d):
        return "NaT"
    return d.date().isoformat()


def fmt_num(x: object) -> str:
    v = pd.to_numeric(pd.Series([x]), errors="coerce").iloc[0]
    if pd.isna(v):
        return "NaN"
    return f"{float(v):.6f}"


def render_summary_table(one: dict[str, object]) -> str:
    if bool(one.get("onset_outside_window", False)):
        delay_display = "NA(관측 이전)"
    else:
        delay_display = str(one["delay_days"]) if pd.notna(one["delay_days"]) else "NaN"

    rows = [
        ("onset_manual", fmt_date(one["onset_manual"])),
        ("first_obs_date", fmt_date(one["first_obs_date"])),
        ("dead_start_date", fmt_date(one["dead_start_date"])),
        ("diagnosis_date_online", fmt_date(one["diagnosis_date_online"])),
        ("final_fault_first_date", fmt_date(one["final_fault_first_date"])),
        ("confirm_delay_days", str(one["confirm_delay_days"]) if pd.notna(one["confirm_delay_days"]) else "NaN"),
        ("onset_outside_window", "True" if bool(one["onset_outside_window"]) else "False"),
        ("delay_days", delay_display),
    ]
    lines = ["| field | value |", "|---|---|"]
    lines.extend([f"| {k} | {v} |" for k, v in rows])
    return "\n".join(lines)


def render_snapshot_table(df: pd.DataFrame, panel_id: str, onset_manual: pd.Timestamp) -> str:
    g = df[df["panel_id"].astype(str) == str(panel_id)].copy()
    g["date"] = pd.to_datetime(g["date"], errors="coerce").dt.normalize()
    d0 = pd.to_datetime(onset_manual, errors="coerce").normalize()
    win = g[(g["date"] >= d0 - pd.Timedelta(days=30)) & (g["date"] <= d0 + pd.Timedelta(days=30))].copy()
    win = win.sort_values("date")

    cols = ["date", "mid_ratio", "v_drop", "recon_error", "dtw_dist", "hs_score", "ews_warning", "risk_day", "risk_ens"]
    for c in cols:
        if c not in win.columns:
            win[c] = np.nan
    win = win[cols]

    lines = [
        "| date | mid_ratio | v_drop | recon_error | dtw_dist | hs_score | ews_warning | risk_day | risk_ens |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in win.iterrows():
        ews = r["ews_warning"]
        if pd.isna(ews):
            ews_s = "NaN"
        else:
            ews_s = "1" if str(ews).lower() in ["1", "true", "t", "yes"] else "0"
        lines.append(
            "| "
            + " | ".join(
                [
                    fmt_date(r["date"]),
                    fmt_num(r["mid_ratio"]),
                    fmt_num(r["v_drop"]),
                    fmt_num(r["recon_error"]),
                    fmt_num(r["dtw_dist"]),
                    fmt_num(r["hs_score"]),
                    ews_s,
                    fmt_num(r["risk_day"]),
                    fmt_num(r["risk_ens"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def add_rank_columns(df: pd.DataFrame, score_cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in score_cols:
        if c not in out.columns:
            continue
        out[c] = pd.to_numeric(out[c], errors="coerce")
        out[f"{c}_rank_day"] = out.groupby("date")[c].rank(method="min", ascending=False)
    return out


def render_topk_leadtime(df: pd.DataFrame, panel_id: str, onset_manual: pd.Timestamp, k: int) -> str:
    score_cols = [c for c in ["risk_ens", "risk_day", "v_drop", "level_drop", "recon_error", "dtw_dist", "hs_score"] if c in df.columns]
    if not score_cols:
        return "_사용 가능한 score 컬럼이 없어 rank 리드타임 계산 불가_"
    x = add_rank_columns(df, score_cols)
    g_all = x[(x["panel_id"].astype(str) == str(panel_id))].copy().sort_values("date")
    onset = pd.to_datetime(onset_manual).normalize()
    g_before = g_all[g_all["date"] < onset].copy()
    g_on_or_before = g_all[g_all["date"] <= onset].copy()

    lines = [
        f"_순위 기반 조기경보 평가(top-{int(k)})_",
        "",
        "| score | first_date_rank<=K_before_onset | lead_days_before_onset | first_date_rank<=K_on_or_before_onset | lead_days_on_or_before |",
        "|---|---|---:|---|---:|",
    ]
    for s in score_cols:
        rc = f"{s}_rank_day"
        if rc not in g_all.columns:
            continue

        hit_before = g_before[g_before[rc] <= float(k)]
        if hit_before.empty:
            d_before = pd.NaT
            lead_before = np.nan
        else:
            d_before = pd.to_datetime(hit_before["date"].min()).normalize()
            lead_before = int((onset - d_before).days)

        hit_on_or_before = g_on_or_before[g_on_or_before[rc] <= float(k)]
        if hit_on_or_before.empty:
            d_oob = pd.NaT
            lead_oob = np.nan
        else:
            d_oob = pd.to_datetime(hit_on_or_before["date"].min()).normalize()
            lead_oob = int((onset - d_oob).days)

        lines.append(
            f"| {s} | {fmt_date(d_before)} | "
            f"{('NaN' if pd.isna(lead_before) else str(int(lead_before)))} | "
            f"{fmt_date(d_oob)} | {('NaN' if pd.isna(lead_oob) else str(int(lead_oob)))} |"
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    cases = parse_cases(args.case)
    out_dir = (Path("data") / str(args.site).strip() / "out").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_scores(out_dir)
    out_md = out_dir / f"CASE_STUDY_{str(args.site).upper()}.md"

    lines: list[str] = []
    lines.append(f"# Fault Case Study ({args.site})")
    lines.append("")
    lines.append("## 용어 정의")
    lines.append("")
    lines.append("| term | meaning |")
    lines.append("|---|---|")
    lines.append("| first_obs_date | `ae_simple_scores`에서 해당 panel의 첫 관측 날짜 |")
    lines.append("| dead_start_date | `state_dead_eff`가 처음 True가 된 날짜 |")
    lines.append("| diagnosis_date_online | 온라인 진단 컬럼(dead/critical 누적 기준)으로 계산된 최초 진단일 |")
    lines.append("| final_fault_first_date | `final_fault` 세그먼트 라벨의 시작일(백필 시작) |")
    lines.append("")

    for panel_id, onset_manual in cases:
        one = get_panel_summary(df, panel_id=panel_id, onset_manual=onset_manual)
        lines.append(f"## Case: `{panel_id}`")
        lines.append("")
        lines.append("### 날짜 요약")
        lines.append("")
        lines.append(render_summary_table(one))
        if bool(one.get("onset_outside_window", False)):
            lines.append("")
            lines.append("> onset_manual이 관측 시작보다 앞이라, onset 기준 지연/리드타임은 산출 불가")
        lines.append("")
        lines.append("### 전조 신호 스냅샷 (onset ±30일)")
        lines.append("")
        lines.append(render_snapshot_table(df, panel_id=panel_id, onset_manual=onset_manual))
        lines.append("")
        lines.append(f"### Top-{int(args.K)} 진입 리드타임 (순위 기반 조기경보 평가)")
        lines.append("")
        lines.append(render_topk_leadtime(df, panel_id=panel_id, onset_manual=onset_manual, k=int(args.K)))
        lines.append("")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] wrote {out_md}")
    print(f"[INFO] n_cases={len(cases)}")


if __name__ == "__main__":
    main()
