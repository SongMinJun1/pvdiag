# -*- coding: utf-8 -*-
"""
폴더 내 모든 엑셀/CSV를 읽어 패널별 일일 발전량을 계산/정규화한 뒤,
시그마 기준으로 저성과 패널-날짜를 판정하고,
같은 패널이 N일 연속 저성과인 (패널, 날짜) 및 연속구간 요약을 엑셀로 저장.
"""

# ============================================================
# ★★★ 사용자 설정 (여기만 수정하세요) ★★★
# ============================================================
INPUT_DIR = r"data/kernelog1/low_energy_in"                 # 엑셀/CSV 파일들이 들어있는 폴더 경로
OUTPUT_PATH = r"data/kernelog1/out/low_panels_2sigma_d3.xlsx"
# 결과 엑셀 저장 경로(.xlsx)

SIGMA = 2.0                             # 시그마 기준 (예: 2.0 → 평균-2σ)
NORM = "day_mean_ratio"                 # 정규화 방식: "day_mean_ratio" | "day_total_ratio" | panel_zscore"
CONSECUTIVE_DAYS = 3                   # 연속 저성과 판정 최소 일수 (예: 2 → 이틀 연속)

CLAMP_POWER_NONNEG = True               # 전력(W) 적분 시 음수 전력을 0으로 클램프할지 여부
# ============================================================

from pathlib import Path
import re
import numpy as np
import pandas as pd


# ----------------------------
# 컬럼 자동 탐지 유틸
# ----------------------------
DATETIME_CANDIDATES = [
    "date_time", "datetime", "timestamp", "time", "date", "dt", "측정시간", "일시", "시간"
]
PANEL_CANDIDATES = [
    "map_id", "panel_id", "panel", "string_id", "module_id", "device_id", "인버터id", "패널id", "패널_id"
]
MAPTYPE_CANDIDATES = ["map_type", "type", "구분"]

POWER_CANDIDATES = [
    "p (w)", "p(w)", "power(w)", "power", "pac", "p_out", "w"
]
ENERGY_CANDIDATES = [
    "energy(kwh)", "energy (kwh)", "kwh", "yield", "발전량", "발전량(kwh)"
]

VOLTAGE_CANDIDATES = [
    "v_in", "vin", "input_voltage", "voltage", "v", "vdc", "dc_voltage", "입력전압", "전압"
]
CURRENT_CANDIDATES = [
    "i_out", "iout", "current", "i", "idc", "dc_current", "출력전류", "전류"
]


def _norm_colname(c: str) -> str:
    c2 = str(c).strip().lower()
    c2 = re.sub(r"\s+", " ", c2)
    return c2


def detect_column(df: pd.DataFrame, candidates) -> str | None:
    cols = list(df.columns)
    norm_map = {_norm_colname(c): c for c in cols}
    for cand in candidates:
        cand_n = _norm_colname(cand)
        if cand_n in norm_map:
            return norm_map[cand_n]
    for cand in candidates:
        cand_n = _norm_colname(cand)
        # Avoid false positives from very short tokens like "e" matching many columns.
        if len(cand_n) < 3:
            continue
        for ncol, orig in norm_map.items():
            if cand_n in ncol:
                return orig
    return None


def infer_interval_hours(dt_series: pd.Series) -> float:
    s = pd.to_datetime(dt_series, errors="coerce")
    s = s.dropna().sort_values().unique()
    if len(s) < 2:
        return 5 / 60.0
    diffs = np.diff(s).astype("timedelta64[s]").astype(float)
    diffs = diffs[diffs > 0]
    if len(diffs) == 0:
        return 5 / 60.0
    median_sec = float(np.median(diffs))
    median_sec = max(60.0, min(median_sec, 3600.0))
    return median_sec / 3600.0


# ----------------------------
# 파일 로딩
# ----------------------------
def read_one_file(fp: Path) -> pd.DataFrame:
    suffix = fp.suffix.lower()
    if suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(fp)
    elif suffix == ".csv":
        df = pd.read_csv(fp)
    else:
        raise ValueError(f"지원하지 않는 확장자: {fp}")
    df["__source_file__"] = fp.name
    return df


def list_input_files(input_dir: Path) -> list[Path]:
    files: list[Path] = []
    for ext in ("*.xlsx", "*.xls", "*.csv"):
        files.extend(sorted(input_dir.rglob(ext)))
    # Keep only real files
    files = [p for p in files if p.is_file()]
    return files


def load_all(input_dir: Path) -> list[pd.DataFrame]:
    files = list_input_files(input_dir)
    if not files:
        raise FileNotFoundError(f"폴더(및 하위 폴더)에 엑셀/CSV 파일이 없습니다: {input_dir}")

    dfs: list[pd.DataFrame] = []
    for fp in files:
        try:
            dfs.append(read_one_file(fp))
        except Exception as e:
            print(f"[WARN] 파일 읽기 실패: {fp} ({e})")

    if not dfs:
        raise RuntimeError("읽을 수 있는 파일이 없습니다(모두 실패).")

    return dfs


# ----------------------------
# 일일 발전량 계산
# ----------------------------
def compute_daily_energy(raw: pd.DataFrame, clamp_power_nonneg: bool = True) -> tuple[pd.DataFrame, dict]:
    meta = {}

    dt_col = detect_column(raw, DATETIME_CANDIDATES)
    panel_col = detect_column(raw, PANEL_CANDIDATES)
    maptype_col = detect_column(raw, MAPTYPE_CANDIDATES)

    if dt_col is None or panel_col is None:
        raise ValueError(f"필수 컬럼 탐지 실패. dt_col={dt_col}, panel_col={panel_col}")

    df = raw.copy()

    if maptype_col is not None:
        vals = df[maptype_col].astype(str).str.lower()
        if (vals == "panel").any():
            df = df[vals == "panel"].copy()
            meta["filtered_map_type"] = "panel"
        else:
            meta["filtered_map_type"] = None

    df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
    df = df.dropna(subset=[dt_col, panel_col])
    df["__date__"] = df[dt_col].dt.date

    energy_col = detect_column(df, ENERGY_CANDIDATES)
    power_col = detect_column(df, POWER_CANDIDATES)
    v_col = detect_column(df, VOLTAGE_CANDIDATES)
    i_col = detect_column(df, CURRENT_CANDIDATES)
    meta["dt_col"] = dt_col
    meta["panel_col"] = panel_col
    meta["energy_col"] = energy_col
    meta["power_col"] = power_col
    meta["v_col"] = v_col
    meta["i_col"] = i_col

    if energy_col is not None:
        df["_energy_kwh_"] = pd.to_numeric(df[energy_col], errors="coerce").fillna(0.0)
        daily = (
            df.groupby([panel_col, "__date__"], as_index=False)["_energy_kwh_"]
            .sum()
            .rename(columns={panel_col: "panel_id", "__date__": "date", "_energy_kwh_": "energy_kwh"})
        )
        meta["energy_calc"] = "sum_energy_column"

    elif power_col is not None:
        df["_power_w_"] = pd.to_numeric(df[power_col], errors="coerce").fillna(0.0)
        if clamp_power_nonneg:
            df["_power_w_"] = df["_power_w_"].clip(lower=0.0)

        interval_h = infer_interval_hours(df[dt_col])
        meta["interval_hours_inferred"] = interval_h

        df["_energy_kwh_"] = df["_power_w_"] * interval_h / 1000.0

        daily = (
            df.groupby([panel_col, "__date__"], as_index=False)["_energy_kwh_"]
            .sum()
            .rename(columns={panel_col: "panel_id", "__date__": "date", "_energy_kwh_": "energy_kwh"})
        )
        meta["energy_calc"] = "integrate_power_W"

    elif v_col is not None and i_col is not None:
        df["_v_"] = pd.to_numeric(df[v_col], errors="coerce").fillna(0.0)
        df["_i_"] = pd.to_numeric(df[i_col], errors="coerce").fillna(0.0)
        df["_power_w_"] = df["_v_"] * df["_i_"]
        if clamp_power_nonneg:
            df["_power_w_"] = df["_power_w_"].clip(lower=0.0)

        interval_h = infer_interval_hours(df[dt_col])
        meta["interval_hours_inferred"] = interval_h

        df["_energy_kwh_"] = df["_power_w_"].astype(float) * interval_h / 1000.0

        daily = (
            df.groupby([panel_col, "__date__"], as_index=False)["_energy_kwh_"]
            .sum()
            .rename(columns={panel_col: "panel_id", "__date__": "date", "_energy_kwh_": "energy_kwh"})
        )
        meta["energy_calc"] = "integrate_v_times_i"

    else:
        raise ValueError(
            "에너지(kWh) 컬럼도 없고 전력(W) 컬럼도 없으며, 전압/전류 컬럼(v_in/i_out)도 탐지되지 않았습니다. "
            f"탐지 결과: energy_col={energy_col}, power_col={power_col}, v_col={v_col}, i_col={i_col}"
        )

    src = (
        df.groupby([panel_col, "__date__"])["__source_file__"]
        .agg(lambda x: ",".join(sorted(set(map(str, x)))))
        .reset_index()
        .rename(columns={panel_col: "panel_id", "__date__": "date", "__source_file__": "source_files"})
    )
    out = daily.merge(src, on=["panel_id", "date"], how="left")
    out["date"] = pd.to_datetime(out["date"])
    return out, meta


# ----------------------------
# 정규화 + 2σ 판정 + 이틀 연속 탐지
# ----------------------------
def normalize_daily(daily: pd.DataFrame, norm: str = "day_mean_ratio") -> pd.DataFrame:
    df = daily.copy()

    if norm == "day_mean_ratio":
        day_mean = df.groupby("date")["energy_kwh"].transform("mean")
        df["normalized"] = np.where(day_mean > 0, df["energy_kwh"] / day_mean, np.nan)
    elif norm == "day_total_ratio":
        day_sum = df.groupby("date")["energy_kwh"].transform("sum")
        df["normalized"] = np.where(day_sum > 0, df["energy_kwh"] / day_sum, np.nan)
    elif norm == "panel_zscore":
        mu = df.groupby("panel_id")["energy_kwh"].transform("mean")
        sd = df.groupby("panel_id")["energy_kwh"].transform("std")
        df["normalized"] = np.where(sd > 0, (df["energy_kwh"] - mu) / sd, np.nan)
    else:
        raise ValueError(f"알 수 없는 norm: {norm}")

    return df


def flag_low_2sigma(df_norm: pd.DataFrame, sigma: float = 2.0) -> pd.DataFrame:
    df = df_norm.copy()
    m = df.groupby("date")["normalized"].transform("mean")
    sd = df.groupby("date")["normalized"].transform("std")
    df["cutoff_2sigma"] = m - sigma * sd
    df["is_low"] = df["normalized"] <= df["cutoff_2sigma"]
    return df


def mark_consecutive_days(df_flagged: pd.DataFrame, min_consec: int = 2) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df_flagged.copy().sort_values(["panel_id", "date"]).reset_index(drop=True)

    def _per_panel(g: pd.DataFrame) -> pd.DataFrame:
        g = g.sort_values("date").copy()
        is_low = g["is_low"].values
        dates = g["date"].values

        streak_len = np.ones(len(g), dtype=int)
        for i in range(1, len(g)):
            if is_low[i] and is_low[i - 1] and (dates[i] - dates[i - 1]) == pd.Timedelta(days=1):
                streak_len[i] = streak_len[i - 1] + 1

        in_streak = np.zeros(len(g), dtype=bool)
        for i in range(len(g) - 1, -1, -1):
            if streak_len[i] >= min_consec:
                for j in range(i, i - streak_len[i], -1):
                    in_streak[j] = True

        g["in_streak"] = in_streak
        return g

    df2 = df.groupby("panel_id", group_keys=False).apply(_per_panel)
    alerts = df2[df2["in_streak"]].copy()

    streak_rows = []
    for pid, g in alerts.groupby("panel_id"):
        g = g.sort_values("date")
        split = (g["date"].diff().dt.days != 1).cumsum()
        for _, gg in g.groupby(split):
            if len(gg) >= min_consec:
                sf = ",".join(gg["source_files"].fillna("").astype(str).tolist())
                sf = ",".join(sorted(set([x for x in sf.split(",") if x])))

                streak_rows.append({
                    "panel_id": pid,
                    "start_date": gg["date"].min(),
                    "end_date": gg["date"].max(),
                    "length_days": int(len(gg)),
                    "min_normalized": float(np.nanmin(gg["normalized"].values)),
                    "min_energy_kwh": float(np.nanmin(gg["energy_kwh"].values)),
                    "source_files": sf
                })

    streaks = pd.DataFrame(streak_rows)
    if not streaks.empty:
        streaks = streaks.sort_values(["length_days", "panel_id"], ascending=[False, True]).reset_index(drop=True)

    return alerts.reset_index(drop=True), streaks


# ----------------------------
# 메인
# ----------------------------
def main():
    input_dir = Path(INPUT_DIR)
    if not input_dir.exists():
        raise FileNotFoundError(f"input_dir이 존재하지 않습니다: {input_dir}")

    print(f"[설정] 폴더={INPUT_DIR}, 시그마={SIGMA}, 정규화={NORM}, 연속일수={CONSECUTIVE_DAYS}")

    dfs = load_all(input_dir)
    daily_parts = []
    metas = []
    for one in dfs:
        daily_one, meta_one = compute_daily_energy(one, clamp_power_nonneg=CLAMP_POWER_NONNEG)
        daily_parts.append(daily_one)
        metas.append(meta_one)

    daily = pd.concat(daily_parts, ignore_index=True)
    # In case multiple files contribute to the same (panel_id, date), sum energy and merge source_files.
    def _merge_sources(s: pd.Series) -> str:
        toks = []
        for v in s.fillna("").astype(str):
            toks.extend([x for x in v.split(",") if x])
        return ",".join(sorted(set(toks)))

    daily = (
        daily.groupby(["panel_id", "date"], as_index=False)
        .agg({"energy_kwh": "sum", "source_files": _merge_sources})
    )
    meta = {"n_files": len(dfs)}
    if metas:
        # keep a small sample of detected columns for debugging
        meta["meta_sample_0"] = metas[0]

    daily_norm = normalize_daily(daily, norm=NORM)
    flagged = flag_low_2sigma(daily_norm, sigma=SIGMA)
    alerts, streaks = mark_consecutive_days(flagged, min_consec=CONSECUTIVE_DAYS)

    output_cols = ["source_files", "panel_id", "date"]
    low_only = flagged[flagged["is_low"]].sort_values(["date", "panel_id"]).reset_index(drop=True)[output_cols]
    alerts_out = alerts.sort_values(["panel_id", "date"]).reset_index(drop=True)[output_cols]
    streaks_cols = ["panel_id", "start_date", "end_date", "length_days", "source_files"]

    out_path = Path(OUTPUT_PATH)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        low_only.to_excel(writer, index=False, sheet_name="low_panels")
        alerts_out.to_excel(writer, index=False, sheet_name="consecutive_alerts")
        if streaks is None or streaks.empty:
            pd.DataFrame(columns=streaks_cols).to_excel(writer, index=False, sheet_name="streaks_summary")
        else:
            streaks[streaks_cols].to_excel(writer, index=False, sheet_name="streaks_summary")

    print(f"[OK] 저장 완료: {out_path}")
    print(f"[INFO] 저성과 패널 rows={len(low_only)}, 연속저성과 rows={len(alerts_out)}, 연속구간={len(streaks) if streaks is not None else 0}")


if __name__ == "__main__":
    main()
