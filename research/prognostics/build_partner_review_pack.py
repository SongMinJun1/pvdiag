#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd

SITES = ["conalog", "sinhyo", "gangui", "ktc_ess"]
EVENT_PER_SITE = 5
PREALERT_PER_SITE = 3
FINAL_COLS = [
    "site",
    "panel_id",
    "구분",
    "우선순위",
    "주요 날짜",
    "현재 상태 요약",
    "추정 유형",
    "우리 해석",
    "현장 확인 부탁사항",
    "confidence",
    "현장 일치 여부",
    "실제 이슈 유형",
    "발견일",
    "발생 추정일",
    "조치 여부",
    "메모",
    "risk_ens",
    "risk_day",
    "phenotype",
    "dominant_family",
    "top_score",
    "evidence_strength",
    "phenotype_event_date",
]


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def has_value(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    return pd.to_datetime(df[col], errors="coerce").notna()


def as_bool(series: pd.Series) -> pd.Series:
    if getattr(series, "dtype", None) == bool:
        return series.fillna(False)
    return pd.to_numeric(series, errors="coerce").fillna(0).ne(0)


def priority_label(df: pd.DataFrame) -> pd.Series:
    dead = has_value(df, "dead_diag_date")
    critical = has_value(df, "critical_diag_date")
    online = has_value(df, "diagnosis_date_online")
    out = pd.Series("prealert", index=df.index)
    out.loc[online] = "online"
    out.loc[critical] = "critical"
    out.loc[dead] = "dead"
    return out


def estimated_type(row: pd.Series) -> str:
    phenotype = str(row.get("phenotype") or "").strip()
    dominant = str(row.get("dominant_family") or "").strip()
    if phenotype == "compound":
        return "compound"
    if dominant in {"electrical", "shape", "instability"}:
        return dominant
    return "unknown"


def status_summary(row: pd.Series) -> str:
    bucket = str(row.get("bucket") or "").strip()
    inferred = estimated_type(row)
    if bucket == "prealert_candidate":
        if inferred == "electrical":
            return "전기형 우세의 경고 후보"
        if inferred == "shape":
            return "형태형 우세의 경고 후보"
        if inferred == "instability":
            return "불안정형 우세의 경고 후보"
        if inferred == "compound":
            return "복합형 경고 후보"
        return "전조 후보"
    if inferred == "electrical":
        return "전기형 우세의 강한 이상"
    if inferred == "shape":
        return "형태형 우세의 강한 이상"
    if inferred == "instability":
        return "불안정형 우세의 강한 이상"
    if inferred == "compound":
        return "복합형 이상 후보"
    return "이상 후보"


def interpretation(row: pd.Series) -> str:
    phenotype = str(row.get("phenotype") or "").strip()
    inferred = estimated_type(row)
    if not phenotype:
        return "전조 후보이지만 아직 유형 근거는 약함"
    if inferred == "electrical":
        return "출력 저하, 전압 이상, 스트링 또는 모듈 전기 계열 이상 가능성"
    if inferred == "shape":
        return "mismatch, 배열 불균형, 음영, 패턴 변화 가능성"
    if inferred == "instability":
        return "흔들림, 접속 불안정, 간헐 이상 가능성"
    if inferred == "compound":
        return "한 축으로 단정 어렵고 복합 원인 가능성"
    return "전조 후보이지만 아직 유형 근거는 약함"


def what_to_check(row: pd.Series) -> str:
    bucket = str(row.get("bucket") or "").strip()
    inferred = estimated_type(row)
    if bucket == "prealert_candidate":
        return "아직 확진 전이므로 최근 점검 이력과 이상 징후 존재 여부 확인 요청"
    if inferred == "electrical":
        return "실제 출력 저하 여부, 스트링 단선 여부, 모듈 교체 또는 점검 이력 확인 요청"
    if inferred == "shape":
        return "배열 불균형, 음영, 특정 패널 패턴 이상 여부 확인 요청"
    if inferred == "instability":
        return "간헐 이상, 접속 불안정, 측정 흔들림 여부 확인 요청"
    if inferred == "compound":
        return "전기형 원인과 추가 패턴 이상 여부 함께 확인 요청"
    return "최근 점검 이력과 이상 징후 존재 여부 확인 요청"


def confidence(row: pd.Series) -> str:
    strength = str(row.get("evidence_strength") or "").strip().lower()
    if strength == "strong":
        return "strong"
    if strength == "medium":
        return "medium"
    return "weak"


def format_dates(row: pd.Series) -> str:
    parts = []
    for label, col in [
        ("online", "diagnosis_date_online"),
        ("critical", "critical_diag_date"),
        ("dead", "dead_diag_date"),
        ("phenotype", "phenotype_event_date"),
    ]:
        value = row.get(col, pd.NA)
        if pd.notna(value) and str(value) != "":
            parts.append(f"{label} {value}")
    if as_bool(pd.Series([row.get("final_fault", False)])).iloc[0]:
        parts.append("final yes")
    return " | ".join(parts) if parts else "-"


def build_site_rows(root: Path, site: str) -> pd.DataFrame:
    alerts = read_csv_or_empty(root / "data" / site / "out" / "latest_alerts_enriched.csv")
    if alerts.empty:
        return pd.DataFrame(columns=FINAL_COLS)

    alerts = alerts.copy()
    alerts["site"] = site
    alerts["우선순위"] = priority_label(alerts)
    event_mask = alerts["우선순위"].isin(["dead", "critical", "online"]) | as_bool(alerts.get("final_fault", pd.Series(False, index=alerts.index)))

    event_df = alerts.loc[event_mask].copy()
    prealert_df = alerts.loc[~event_mask].copy()

    prio_order = {"dead": 0, "critical": 1, "online": 2, "prealert": 3}
    if not event_df.empty:
        event_df["_prio"] = event_df["우선순위"].map(prio_order).fillna(99)
        event_df = event_df.sort_values(["_prio", "risk_ens"], ascending=[True, False], na_position="last").head(EVENT_PER_SITE).drop(columns=["_prio"])
        event_df["bucket"] = "event_candidate"
    if not prealert_df.empty:
        sort_col = "risk_ens" if "risk_ens" in prealert_df.columns else "risk_day"
        prealert_df = prealert_df.sort_values(sort_col, ascending=False, na_position="last").head(PREALERT_PER_SITE).copy()
        prealert_df["우선순위"] = "prealert"
        prealert_df["bucket"] = "prealert_candidate"

    df = pd.concat([event_df, prealert_df], ignore_index=True)
    if df.empty:
        return pd.DataFrame(columns=FINAL_COLS)

    df["구분"] = df["bucket"].replace({"event_candidate": "event candidate", "prealert_candidate": "prealert candidate"})
    df["주요 날짜"] = df.apply(format_dates, axis=1)
    df["현재 상태 요약"] = df.apply(status_summary, axis=1)
    df["추정 유형"] = df.apply(estimated_type, axis=1)
    df["우리 해석"] = df.apply(interpretation, axis=1)
    df["현장 확인 부탁사항"] = df.apply(what_to_check, axis=1)
    df["confidence"] = df.apply(confidence, axis=1)
    df["현장 일치 여부"] = pd.NA
    df["실제 이슈 유형"] = pd.NA
    df["발견일"] = pd.NA
    df["발생 추정일"] = pd.NA
    df["조치 여부"] = pd.NA
    df["메모"] = pd.NA

    for col in FINAL_COLS:
        if col not in df.columns:
            df[col] = pd.NA
    df["site"] = df["site"].replace({"conalog": "Conalog"})
    return df[FINAL_COLS].copy()


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    out_path = root / "_share" / "partner_crosscheck_review.xlsx"
    panel_rows = pd.concat([build_site_rows(root, site) for site in SITES], ignore_index=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        panel_rows.to_excel(writer, sheet_name="검토요청", index=False)
    print(f"[OK] wrote {out_path}")
    print(f"[COUNT] panel_review_rows={len(panel_rows)}")
    if not panel_rows.empty:
        print(panel_rows.groupby("site").size().to_string())


if __name__ == "__main__":
    main()
