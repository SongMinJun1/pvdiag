
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

def _read_csv(p: Path) -> pd.DataFrame:
    df = pd.read_csv(p, low_memory=False, encoding="utf-8-sig")
    df.columns = [c.replace("\ufeff","") for c in df.columns]
    return df

def _first_present(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="kernelog1")
    ap.add_argument("--scores", default=None, help="Path to scores CSV (optional). If omitted, auto-detect in data/<site>/out/")
    ap.add_argument("--out-dir", default=None, help="Output directory (optional). Default: research/reports/<site>/paper_pack")
    args = ap.parse_args()

    site = args.site
    out_dir = Path(args.out_dir) if args.out_dir else Path(f"research/reports/{site}/paper_pack")
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Auto-detect scores file ---
    if args.scores:
        scores_path = Path(args.scores)
    else:
        cand = [
            Path(f"data/{site}/out/panel_day_risk_transition.csv"),
            Path(f"data/{site}/out/panel_day_risk.csv"),
            Path(f"data/{site}/out/panel_day_core.csv"),
        ]
        scores_path = next((p for p in cand if p.exists()), None)
        if scores_path is None:
            raise FileNotFoundError(f"No scores file found. Tried: {cand}")

    df = _read_csv(scores_path)

    # =========================
    # Paper-friendly canonical schema
    # =========================
    # role: used only for ordering + dictionary
    SCHEMA = [
        # ---------- ID ----------
        ("ID", "date", ["date"], "Date", "날짜", "t", "Evaluation date (day)", ""),
        ("ID", "panel_id", ["panel_id", "map_id", "id"], "Panel ID", "패널 ID", "i", "Panel identifier", ""),
        ("ID", "source_csv", ["source_csv"], "Source file", "원본 파일", "", "Source CSV filename", ""),
        ("ID", "group_key", ["group_key"], "Group key", "그룹 키", "", "Peer comparison group key (e.g., uuid.string)", ""),
        ("ID", "group_key_base", ["group_key_base"], "Base group key", "기본 그룹 키", "", "Base group key (pre vbin split)", ""),
        ("ID", "vbin", ["vbin"], "Voltage bin", "전압 bin", "", "Subgroup bin within group_key (train-only)", ""),

        # ---------- Quality / gates ----------
        ("GATE", "peer_midday_frac", ["mid_peer"], "Peer midday fraction", "정오 peer 발전 수준", r"\pi_{mid}", "Site/peer generation level in 11-15h (0..1)", ""),
        ("GATE", "peer_last_frac", ["last_peer"], "Peer last fraction", "마지막 peer 발전 수준", r"\pi_{last}", "Site/peer generation level in last window (0..1)", ""),
        ("GATE", "coverage_daylight", ["coverage"], "Coverage (daylight)", "daylight 커버리지", "cov", "Fraction of valid samples in daylight window (0..1)", ""),
        ("GATE", "coverage_midday", ["coverage_mid"], "Coverage (midday)", "정오 커버리지", r"cov_{mid}", "Fraction of valid samples in 11-15h (0..1)", ""),
        ("GATE", "data_bad", ["data_bad"], "Data bad", "데이터 불량", "", "True if coverage is below threshold", ""),
        ("GATE", "n_ref", ["n_ref"], "Ref panels (n_ref)", "레퍼런스 패널 수", "", "Number of reference panels used for v_ref", ""),
        ("GATE", "n_total", ["n_total"], "Total panels (n_total)", "전체 패널 수", "", "Number of panels in (date, group_key)", ""),

        # ---------- Severity (level) ----------
        ("SEV", "midday_ratio", ["mid_ratio"], "Midday ratio", "정오 출력비", r"r_{mid}", "Mean power ratio in 11-15h (panel/peer)", r"r(t)=P_i(t)/peerP(t),\;\; r_{mid}=mean(r(t) \text{ in 11-15h})"),
        ("SEV", "level_drop", ["level_drop"], "Level drop", "레벨 저하량", r"d_{level}", "Drop magnitude from midday ratio", r"d_{level}=1-r_{mid}"),
        ("SEV", "risk_day", ["risk_day"], "Daily risk score", "일일 위험점수", r"s_{day}", "Daily risk score (rule/level based)", ""),
        ("SEV", "last_ratio", ["last_ratio"], "Last ratio", "마지막 출력비", "", "Mean ratio in the last window", ""),
        ("SEV", "min_ratio", ["min_ratio"], "Min ratio", "최소 출력비", "", "Minimum ratio in daylight", ""),
        ("SEV", "p10_ratio", ["p10_ratio"], "P10 ratio", "10% 출력비", "", "10th percentile ratio in daylight", ""),
        ("SEV", "p50_ratio", ["p50_ratio"], "Median ratio", "중앙값 출력비", "", "Median ratio in daylight", ""),

        # ---------- Event / segments ----------
        ("EVT", "drop_time", ["drop_time"], "Drop start time", "저하 시작", "", "Start time of the longest low segment", ""),
        ("EVT", "sustain_mins", ["sustain_mins"], "Sustain (mins)", "저하 지속(분)", "", "Duration of the longest low segment (minutes)", ""),
        ("EVT", "recovered", ["recovered"], "Recovered", "회복(지속)", "", "Recovered after the low segment (sustained)", ""),
        ("EVT", "recovered_any", ["recovered_any"], "Recovered any", "회복(1회라도)", "", "Recovered at least once after the segment", ""),
        ("EVT", "recovered_sustained", ["recovered_sustained"], "Recovered sustained", "회복 지속", "", "Recovery sustained for a minimum duration", ""),
        ("EVT", "redrop", ["re_drop"], "Re-drop", "재저하", "", "Drops again after sustained recovery", ""),
        ("EVT", "segment_count", ["seg_count"], "Low segment count", "저하 세그먼트 수", "", "Number of low segments", ""),
        ("EVT", "total_low_mins", ["total_low_mins"], "Total low mins", "저하 총시간", "", "Total minutes below sustain threshold", ""),
        ("EVT", "low_area", ["low_area"], "Low area", "저하 면적", "", "Accumulated deficit area below threshold", ""),
        ("EVT", "co_drop_frac", ["co_drop_frac"], "Co-drop fraction", "동시저하 비율", "", "Fraction of peers also low (environment hint)", ""),
        ("EVT", "event_A", ["event_A"], "Event A", "이벤트 A", "", "Rule-based meaningful drop event flag", ""),

        # ---------- V/I helpers ----------
        ("VI", "midday_v_ratio", ["mid_v_ratio"], "Midday V ratio", "정오 전압비", "", "V_panel / peerV in 11-15h", ""),
        ("VI", "midday_i_ratio", ["mid_i_ratio"], "Midday I ratio", "정오 전류비", "", "I_panel / peerI in 11-15h", ""),
        ("VI", "v_ref", ["v_ref"], "V reference", "전압 기준", "", "Group reference voltage ratio", ""),
        ("VI", "v_ref_span", ["v_ref_span"], "V ref span", "전압 분산", "", "Span (p90-p10) used for v_ref trust", ""),
        ("VI", "v_ref_ok", ["v_ref_ok"], "V ref ok", "전압 기준 신뢰", "", "Whether v_ref is trustworthy", ""),
        ("VI", "no_ref", ["no_ref"], "No ref", "레퍼런스 없음", "", "True if reference is unavailable", ""),
        ("VI", "v_drop", ["v_drop"], "V-drop", "전압 드롭", "", "Relative voltage drop vs v_ref", ""),

        # ---------- Shape / anomaly scores ----------
        ("SHAPE", "ae_recon_mse", ["recon_error"], "AE recon MSE", "AE 재구성오차", r"e_{AE}", "AE reconstruction MSE", ""),
        ("SHAPE", "ae_threshold", ["ae_thr_used"], "AE threshold", "AE 임계값", "", "AE threshold used for is_ae_strong", ""),
        ("SHAPE", "ae_rank", ["ae_rank", "recon_rank_day"], "AE rank (day)", "AE 순위(일내)", r"q_{AE}", "AE anomaly percentile/rank within a day", ""),
        ("SHAPE", "ae_strength", ["ae_strength"], "AE strength", "AE 등급", "", "AE strength category (low/mid/high)", ""),
        ("SHAPE", "ae_abnormal", ["is_ae_abn"], "AE abnormal", "AE 이상", "", "AE abnormal flag", ""),
        ("SHAPE", "ae_strong", ["is_ae_strong"], "AE strong", "AE 강이상", "", "AE strong anomaly flag", ""),
        ("SHAPE", "dtw_dist", ["dtw_dist"], "DTW distance", "DTW 거리", "", "DTW distance to reference curve", ""),
        ("SHAPE", "hs_score", ["hs_score"], "HS score", "HS 점수", "", "Hampel-like turbulence score", ""),

        # ---------- Transition / change ----------
        ("TRANS", "transition_rank", ["transition_rank_day"], "Transition rank", "전이 순위", r"q_{trans}", "Rank/percentile of change-vs-history score", ""),
        ("TRANS", "transition_cp_rank", ["transition_cp_rank_day"], "Transition+CP rank", "전이+CP 순위", r"q_{trans+cp}", "Transition rank boosted by change-point signal", ""),
        ("TRANS", "cp_alarm", ["cp_alarm"], "Change-point alarm", "변화점 알람", "", "Change-point detected flag", ""),

        # ---------- Diagnosis / fault decisions ----------
        ("DIAG", "state_dead", ["state_dead"], "State dead", "dead 상태", "", "Dead condition satisfied (today)", ""),
        ("DIAG", "dead_streak", ["dead_streak"], "Dead streak", "dead 연속일수", "", "Consecutive dead days", ""),
        ("DIAG", "confirmed_fault", ["confirmed_fault"], "Confirmed fault (dead)", "확정고장(dead)", r"y_{dead}", "Confirmed fault by dead_streak rule", ""),
        ("DIAG", "critical_like", ["critical_like"], "Critical-like", "critical-like", "", "V-drop-like critical pattern flag", ""),
        ("DIAG", "critical_fault", ["critical_fault"], "Critical fault", "critical fault", "", "Critical fault decision", ""),
        ("DIAG", "final_fault", ["final_fault"], "Final fault", "최종 확정고장", r"y_{fault}", "Final fault flag used as 'fault period' label", ""),

        # ---------- Tags / interpretability ----------
        ("TAG", "anom_level", ["anom_level"], "Anomaly level", "이상 레벨", "", "Human-readable anomaly level label", ""),
        ("TAG", "anom_subtype", ["anom_subtype"], "Anomaly subtype", "이상 서브타입", "", "Subtype label from multi-signals", ""),
        ("TAG", "fault_like_day", ["fault_like_day"], "Fault-like day", "하루고장형", "", "Fault-like daily pattern flag", ""),
        ("TAG", "degraded_candidate", ["degraded_candidate"], "Degraded candidate", "열화후보", "", "Degradation candidate flag", ""),
        ("TAG", "shadow_like", ["shadow_like"], "Shadow-like", "음영유사", "", "Shadow/environment-like flag", ""),

        # ---------- EWS (optional) ----------
        ("EWS", "ews_mid_var_7d", ["ews_mid_var_7d"], "EWS: mid var (7d)", "EWS mid 변동(7d)", "", "Rolling variability of midday_ratio", ""),
        ("EWS", "ews_eventA_freq_7d", ["ews_eventA_freq_7d"], "EWS: eventA freq (7d)", "EWS eventA 빈도(7d)", "", "Rolling frequency of event_A", ""),
        ("EWS", "ews_dtw_mean_7d", ["ews_dtw_mean_7d"], "EWS: dtw mean (7d)", "EWS dtw 평균(7d)", "", "Rolling mean of DTW", ""),
        ("EWS", "ews_hs_mean_7d", ["ews_hs_mean_7d"], "EWS: hs mean (7d)", "EWS hs 평균(7d)", "", "Rolling mean of HS", ""),
    ]

    # --- Build rename map (raw -> canonical) ---
    rename_map = {}
    raw_used = set()
    canonical_used = set()
    rows = []

    for role, canonical, raw_cands, label_en, label_ko, sym, desc, formula in SCHEMA:
        raw = _first_present(df, raw_cands)
        if raw is None:
            continue

        # collision guard
        new = canonical
        if new in canonical_used:
            k = 2
            while f"{canonical}__dup{k}" in canonical_used:
                k += 1
            new = f"{canonical}__dup{k}"
        canonical_used.add(new)

        rename_map[raw] = new
        raw_used.add(raw)

        rows.append({
            "role": role,
            "raw_column": raw,
            "canonical_column": new,
            "paper_label_en": label_en,
            "paper_label_ko": label_ko,
            "symbol": sym,
            "desc": desc,
            "formula": formula
        })

    view = df.rename(columns=rename_map).copy()

    # --- Derived columns (safe) ---
    if "level_drop" not in view.columns and "midday_ratio" in view.columns:
        try:
            view["level_drop"] = 1.0 - pd.to_numeric(view["midday_ratio"], errors="coerce")
            rows.append({
                "role": "SEV",
                "raw_column": "(derived)",
                "canonical_column": "level_drop",
                "paper_label_en": "Level drop",
                "paper_label_ko": "레벨 저하량",
                "symbol": r"d_{level}",
                "desc": "Derived drop magnitude from midday_ratio",
                "formula": r"d_{level}=1-r_{mid}"
            })
        except Exception:
            pass

    # --- Column ordering by role ---
    role_order = ["ID","GATE","SEV","EVT","VI","SHAPE","TRANS","DIAG","TAG","EWS"]
    # canonical columns in schema order:
    schema_cols = [r["canonical_column"] for r in rows if r["canonical_column"] in view.columns]
    # enforce role order grouping
    # (we rebuild desired order by iterating role_order and schema list)
    role_to_cols = {r: [] for r in role_order}
    for r in rows:
        if r["canonical_column"] in view.columns:
            role_to_cols.get(r["role"], []).append(r["canonical_column"])
    ordered = []
    for r in role_order:
        for c in role_to_cols.get(r, []):
            if c in view.columns and c not in ordered:
                ordered.append(c)
    # append the rest (unmapped columns) at the end
    ordered += [c for c in view.columns if c not in ordered]
    view = view[ordered]

    # --- Write files ---
    full_path = out_dir / "scores_view_full.csv"
    view.to_csv(full_path, index=False, encoding="utf-8-sig")

    # Core view: only columns you actually explain in paper/meeting
    core_candidates = [
        "date","panel_id",
        "peer_midday_frac","coverage_midday",
        "midday_ratio","level_drop","risk_day",
        "ae_rank","ae_recon_mse",
        "transition_rank","transition_cp_rank",
        "dead_streak","final_fault"
    ]
    core_cols = [c for c in core_candidates if c in view.columns]
    core_path = out_dir / "scores_view_core.csv"
    view[core_cols].to_csv(core_path, index=False, encoding="utf-8-sig")

    dd = pd.DataFrame(rows)
    dd = dd.sort_values(["role","canonical_column","raw_column"])
    dd_csv = out_dir / "data_dictionary_paper.csv"
    dd.to_csv(dd_csv, index=False, encoding="utf-8-sig")

    # Markdown dictionary (human readable)
    dd_md = out_dir / "data_dictionary_paper.md"
    try:
        md = dd[["role","canonical_column","paper_label_en","paper_label_ko","symbol","desc","formula","raw_column"]].to_markdown(index=False)
    except Exception:
        md = dd.to_string(index=False)
    dd_md.write_text(md, encoding="utf-8")

    print("[OK] scores:", scores_path)
    print("[OK] wrote:", full_path)
    print("[OK] wrote:", core_path)
    print("[OK] wrote:", dd_csv)
    print("[OK] wrote:", dd_md)

if __name__ == "__main__":
    main()
