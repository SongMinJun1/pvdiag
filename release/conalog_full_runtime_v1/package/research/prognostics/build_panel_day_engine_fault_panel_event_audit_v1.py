#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError


PANEL_VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
ABRUPT6_NAME = "panel_day_engine_abrupt6_symptom_map_v1.csv"
PRECURSOR_TRUTH_NAME = "panel_day_engine_precursor_onset_truth_v1.csv"
REAUDIT_NAME = "panel_date_reaudit_working.csv"
VENDOR_ADJUDICATION_NAME = "vendor_reply_adjudication_latest.csv"

AUDIT_OUTPUT = "_share/panel_day_engine_fault_panel_event_audit_v1.csv"
SUMMARY_OUTPUT = "_share/panel_day_engine_fault_panel_event_audit_summary_v1.csv"
NOTE_OUTPUT = "_share/panel_day_engine_fault_panel_event_audit_note_v1.md"

TARGET_SITE = "conalog"
TARGET_PANEL_ID = "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"

AUDIT_COLS = [
    "site",
    "panel_id",
    "현재표_사건유형_ko",
    "현재표_최종고장양상_ko",
    "earliest_warning_date",
    "retrospective_onset_date",
    "strict_trigger_date",
    "first_final_fault_date",
    "dead_diag_date",
    "onset_confidence",
    "onset_method",
    "전조흔적_flag",
    "순수급작_flag",
    "전조평가셋편입_flag",
    "급작평가셋편입_flag",
    "사건유형_재판정_ko",
    "최종고장양상_재판정_ko",
    "재판정_근거_ko",
    "현재표_보정필요여부_flag",
]

SUMMARY_COLS = [
    "고유_고장패널수",
    "사건유형_재판정_전조형수",
    "사건유형_재판정_급작수",
    "사건유형_재판정_보류수",
    "최종고장양상_급격종료수",
    "전조흔적_패널수",
    "순수급작_패널수",
    "전조평가셋편입_패널수",
    "급작평가셋편입_패널수",
    "해석과평가셋불일치_패널수",
    "현재표_보정필요_패널수",
    "note_ko",
]


@dataclass(frozen=True)
class EventRedecision:
    event_type_ko: str
    terminal_pattern_ko: str
    event_rule_ko: str
    terminal_rule_ko: str
    abrupt_positive_flag: int


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit all current fault panels with explicit stored-field event rules."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=repo_root(),
        help="Repository root. Defaults to the current repo root.",
    )
    return parser.parse_args()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    ensure_parent(path)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def write_text(text: str, path: Path) -> None:
    ensure_parent(path)
    path.write_text(text, encoding="utf-8-sig")


def read_csv(path: Path, required: bool = True) -> pd.DataFrame:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Required input is missing: {path}")
        return pd.DataFrame()
    try:
        return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
    except EmptyDataError:
        return pd.DataFrame()
    except UnicodeError:
        return pd.read_csv(path, low_memory=False)


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def to_timestamp(value: object) -> pd.Timestamp | None:
    if pd.isna(value):
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    return ts


def format_date(value: object) -> str:
    ts = to_timestamp(value)
    return "" if ts is None else ts.strftime("%Y-%m-%d")


def exact_panel_rows(df: pd.DataFrame, panel_id: str, site: str | None = None) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    panel_cols = [col for col in df.columns if col.lower() in {"panel_id", "display_entity_id", "entity_id"}]
    if not panel_cols:
        return df.iloc[0:0].copy()
    mask = pd.Series(False, index=df.index)
    for col in panel_cols:
        mask = mask | df[col].astype(str).eq(panel_id)
    result = df.loc[mask].copy()
    if site is not None and "site" in result.columns:
        result = result.loc[result["site"].astype(str).eq(site)].copy()
    return result


def earliest_true_date(df: pd.DataFrame, column: str, date_column: str = "date") -> pd.Timestamp | None:
    if df.empty or column not in df.columns or date_column not in df.columns:
        return None
    working = df.loc[df[column].fillna(False).astype(bool), date_column]
    if working.empty:
        return None
    value = pd.to_datetime(working, errors="coerce").min()
    return None if pd.isna(value) else value


def repeated_core_date(core_df: pd.DataFrame, column: str) -> pd.Timestamp | None:
    if core_df.empty or column not in core_df.columns:
        return None
    value = pd.to_datetime(core_df[column], errors="coerce").dropna()
    if value.empty:
        return None
    return value.iloc[0]


def build_precursor_eval_keys(precursor_truth_df: pd.DataFrame) -> set[tuple[str, str]]:
    panel_cols = [col for col in ("panel_id", "display_entity_id", "entity_id") if col in precursor_truth_df.columns]
    if not panel_cols:
        raise SystemExit(f"{PRECURSOR_TRUTH_NAME} missing panel id column")
    positive_df = precursor_truth_df.loc[
        precursor_truth_df["preferred_precursor_onset_date"].map(normalize_text).ne("")
    ].copy()
    keys: set[tuple[str, str]] = set()
    for row in positive_df.to_dict(orient="records"):
        site = normalize_text(row.get("site"))
        for panel_col in panel_cols:
            panel_id = normalize_text(row.get(panel_col))
            if site and panel_id:
                keys.add((site, panel_id))
                break
    return keys


def build_abrupt_keys(abrupt_df: pd.DataFrame) -> set[tuple[str, str]]:
    return {
        (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        for row in abrupt_df.to_dict(orient="records")
        if normalize_text(row["site"]) and normalize_text(row["panel_id"])
    }


def earliest_warning_date(reaudit_row: pd.Series, gate_df: pd.DataFrame) -> pd.Timestamp | None:
    candidates = [
        to_timestamp(reaudit_row.get("first_warning_date")),
        earliest_true_date(gate_df, "ews_warning"),
    ]
    parsed = [value for value in candidates if value is not None]
    if not parsed:
        return None
    return min(parsed)


def abrupt_positive_evidence_exists(
    key: tuple[str, str],
    abrupt_keys: set[tuple[str, str]],
    core_df: pd.DataFrame,
) -> int:
    if key in abrupt_keys:
        return 1
    if earliest_true_date(core_df, "final_fault") is not None:
        return 1
    if earliest_true_date(core_df, "critical_fault") is not None:
        return 1
    return 0


def determine_event_redecision(
    reaudit_row: pd.Series,
    abrupt_positive_flag: int,
    first_final_fault_date: pd.Timestamp | None,
    dead_diag_date: pd.Timestamp | None,
) -> EventRedecision:
    retrospective_onset = to_timestamp(reaudit_row.get("retrospective_onset_date"))
    strict_trigger = to_timestamp(reaudit_row.get("strict_trigger_date"))
    onset_confidence = normalize_text(reaudit_row.get("onset_confidence"))
    onset_method = normalize_text(reaudit_row.get("onset_method"))

    precursor_rule = (
        retrospective_onset is not None
        and strict_trigger is not None
        and retrospective_onset < strict_trigger
        and onset_confidence == "high"
        and onset_method == "persistent_5of7"
    )
    abrupt_rule = abrupt_positive_flag == 1 and (
        retrospective_onset is None
        or (
            retrospective_onset is not None
            and strict_trigger is not None
            and retrospective_onset == strict_trigger
            and onset_method == "strict_trigger_fallback"
            and onset_confidence != "high"
        )
    )

    if precursor_rule:
        event_type = "전조형 고장"
        event_rule = (
            "retrospective_onset_date 비공란, strict_trigger_date 비공란, "
            "retrospective_onset_date < strict_trigger_date, onset_confidence=high, "
            "onset_method=persistent_5of7 이 모두 성립"
        )
    elif abrupt_rule:
        event_type = "급작 고장"
        event_rule = (
            "abrupt positive evidence 가 있고, retrospective_onset_date 가 공란이거나 "
            "retrospective_onset_date == strict_trigger_date 이면서 onset_method=strict_trigger_fallback, "
            "onset_confidence != high 인 same-day fallback onset 이라 급작 고장으로 둠"
        )
    else:
        event_type = "고장유형 보류"
        event_rule = "전조형 고장 규칙과 급작 고장 규칙을 모두 만족하지 않음"

    abrupt_ending = (
        first_final_fault_date is not None
        and strict_trigger is not None
        and first_final_fault_date == strict_trigger
        and dead_diag_date is not None
        and dead_diag_date <= strict_trigger + pd.Timedelta(days=1)
    )
    if abrupt_ending:
        terminal_pattern = "급격 종료"
        terminal_rule = "first_final_fault_date == strict_trigger_date 이고 dead_diag_date <= strict_trigger_date + 1 day"
    elif event_type == "급작 고장":
        terminal_pattern = "급작 발생"
        terminal_rule = "급격 종료 규칙은 아니지만 사건유형_재판정_ko == 급작 고장 이라 급작 발생으로 둠"
    elif event_type == "전조형 고장":
        terminal_pattern = "진행성 악화"
        terminal_rule = "사건유형_재판정_ko == 전조형 고장 이고 급격 종료 규칙은 아니므로 진행성 악화로 둠"
    else:
        terminal_pattern = "불충분"
        terminal_rule = "stored field 만으로 terminal failure pattern 을 더 좁히기 어려워 불충분으로 둠"

    return EventRedecision(
        event_type_ko=event_type,
        terminal_pattern_ko=terminal_pattern,
        event_rule_ko=event_rule,
        terminal_rule_ko=terminal_rule,
        abrupt_positive_flag=abrupt_positive_flag,
    )


def load_site_frame(root: Path, site: str, filename: str) -> pd.DataFrame:
    return read_csv(root / "data" / site / "out" / filename, required=True)


def load_optional_vendor_row(vendor_df: pd.DataFrame, site: str, panel_id: str) -> pd.Series | None:
    if vendor_df.empty:
        return None
    row_df = exact_panel_rows(vendor_df, panel_id, site=site)
    if row_df.empty:
        return None
    return row_df.iloc[0]


def build_audit(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    share_dir = root / "_share"
    verdict_df = read_csv(share_dir / PANEL_VERDICT_NAME)
    abrupt_df = read_csv(share_dir / ABRUPT6_NAME)
    precursor_truth_df = read_csv(share_dir / PRECURSOR_TRUTH_NAME)
    reaudit_df = read_csv(share_dir / REAUDIT_NAME)
    vendor_df = read_csv(share_dir / VENDOR_ADJUDICATION_NAME, required=False)

    ensure_columns(
        verdict_df,
        [
            "site",
            "panel_id",
            "패널고장여부_ko",
            "사건유형_ko",
            "최종고장양상_ko",
            "전조흔적_flag",
            "순수급작_flag",
            "전조평가셋편입_flag",
            "급작평가셋편입_flag",
        ],
        PANEL_VERDICT_NAME,
    )
    ensure_columns(abrupt_df, ["site", "panel_id"], ABRUPT6_NAME)
    ensure_columns(
        precursor_truth_df,
        ["site", "preferred_precursor_onset_date"],
        PRECURSOR_TRUTH_NAME,
    )
    ensure_columns(
        reaudit_df,
        ["site", "panel_id", "retrospective_onset_date", "strict_trigger_date", "onset_confidence", "onset_method"],
        REAUDIT_NAME,
    )

    fault_df = verdict_df.loc[verdict_df["패널고장여부_ko"].eq("고장")].copy()
    fault_df = fault_df.sort_values(["site", "panel_id"]).drop_duplicates(subset=["site", "panel_id"], keep="first")
    if len(fault_df) != 6:
        raise SystemExit(f"expected current fault panel count to be 6, found {len(fault_df)}")

    abrupt_keys = build_abrupt_keys(abrupt_df)
    precursor_eval_keys = build_precursor_eval_keys(precursor_truth_df)

    site_cache: dict[tuple[str, str], pd.DataFrame] = {}
    audit_rows: list[dict[str, object]] = []
    explicit_precursor_rule_hits = 0

    for row in fault_df.to_dict(orient="records"):
        site = normalize_text(row["site"])
        panel_id = normalize_text(row["panel_id"])
        key = (site, panel_id)

        core_df = site_cache.setdefault((site, "core"), load_site_frame(root, site, "panel_day_core.csv"))
        gate_df = site_cache.setdefault((site, "gate"), load_site_frame(root, site, "ae_simple_local_precursor_gate_daily.csv"))

        core_panel_df = exact_panel_rows(core_df, panel_id, site=site)
        gate_panel_df = exact_panel_rows(gate_df, panel_id, site=site)
        reaudit_panel_df = exact_panel_rows(reaudit_df, panel_id, site=site)
        if reaudit_panel_df.empty:
            raise SystemExit(f"missing reaudit row for fault panel {site}/{panel_id}")
        reaudit_row = reaudit_panel_df.iloc[0]

        earliest_warning = earliest_warning_date(reaudit_row, gate_panel_df)
        retrospective_onset = to_timestamp(reaudit_row.get("retrospective_onset_date"))
        strict_trigger = to_timestamp(reaudit_row.get("strict_trigger_date"))
        first_final_fault_date = earliest_true_date(core_panel_df, "final_fault")
        dead_diag_date = repeated_core_date(core_panel_df, "dead_diag_date")
        abrupt_positive_flag = abrupt_positive_evidence_exists(key, abrupt_keys, core_panel_df)
        redecision = determine_event_redecision(
            reaudit_row=reaudit_row,
            abrupt_positive_flag=abrupt_positive_flag,
            first_final_fault_date=first_final_fault_date,
            dead_diag_date=dead_diag_date,
        )

        current_event = normalize_text(row["사건유형_ko"])
        current_terminal = normalize_text(row["최종고장양상_ko"])
        needs_correction = int(
            current_event != redecision.event_type_ko
            or current_terminal != redecision.terminal_pattern_ko
        )

        vendor_row = load_optional_vendor_row(vendor_df, site, panel_id)
        vendor_hint_parts: list[str] = []
        if vendor_row is not None:
            for column in ("vendor_fault_family", "vendor_reply_class"):
                value = normalize_text(vendor_row.get(column))
                if value:
                    vendor_hint_parts.append(f"{column}={value}")

        reason_parts = [
            redecision.event_rule_ko,
            redecision.terminal_rule_ko,
            f"abrupt_positive_evidence_flag={abrupt_positive_flag}",
        ]
        if key in precursor_eval_keys:
            reason_parts.append("strict precursor truth positive 포함")
        if vendor_hint_parts:
            reason_parts.append(", ".join(vendor_hint_parts))

        precursor_rule_hit = int(redecision.event_type_ko == "전조형 고장")
        explicit_precursor_rule_hits += precursor_rule_hit

        audit_rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "현재표_사건유형_ko": current_event,
                "현재표_최종고장양상_ko": current_terminal,
                "earliest_warning_date": format_date(earliest_warning),
                "retrospective_onset_date": format_date(retrospective_onset),
                "strict_trigger_date": format_date(strict_trigger),
                "first_final_fault_date": format_date(first_final_fault_date),
                "dead_diag_date": format_date(dead_diag_date),
                "onset_confidence": normalize_text(reaudit_row.get("onset_confidence")),
                "onset_method": normalize_text(reaudit_row.get("onset_method")),
                "전조흔적_flag": int(pd.to_numeric(pd.Series([row["전조흔적_flag"]]), errors="coerce").fillna(0).iloc[0]),
                "순수급작_flag": int(pd.to_numeric(pd.Series([row["순수급작_flag"]]), errors="coerce").fillna(0).iloc[0]),
                "전조평가셋편입_flag": int(pd.to_numeric(pd.Series([row["전조평가셋편입_flag"]]), errors="coerce").fillna(0).iloc[0]),
                "급작평가셋편입_flag": int(pd.to_numeric(pd.Series([row["급작평가셋편입_flag"]]), errors="coerce").fillna(0).iloc[0]),
                "사건유형_재판정_ko": redecision.event_type_ko,
                "최종고장양상_재판정_ko": redecision.terminal_pattern_ko,
                "재판정_근거_ko": "; ".join(part for part in reason_parts if part),
                "현재표_보정필요여부_flag": needs_correction,
            }
        )

    audit_df = pd.DataFrame(audit_rows).reindex(columns=AUDIT_COLS)
    if audit_df[["site", "panel_id"]].duplicated().any():
        raise SystemExit("fault panel audit output must be unique by (site, panel_id)")
    if len(audit_df) != 6:
        raise SystemExit(f"fault panel audit output must contain exactly 6 rows, found {len(audit_df)}")

    c429_df = audit_df.loc[audit_df["site"].eq(TARGET_SITE) & audit_df["panel_id"].eq(TARGET_PANEL_ID)].copy()
    if len(c429_df) != 1:
        raise SystemExit("c42997...1.1 must appear exactly once in fault panel event audit")
    if normalize_text(c429_df.iloc[0]["사건유형_재판정_ko"]) != "전조형 고장":
        raise SystemExit("c42997...1.1 must re-evaluate to 전조형 고장 under explicit rule")

    precursor_rule_mask = (
        audit_df["retrospective_onset_date"].map(normalize_text).ne("")
        & audit_df["strict_trigger_date"].map(normalize_text).ne("")
        & (
            pd.to_datetime(audit_df["retrospective_onset_date"], errors="coerce")
            < pd.to_datetime(audit_df["strict_trigger_date"], errors="coerce")
        )
        & audit_df["onset_confidence"].eq("high")
        & audit_df["onset_method"].eq("persistent_5of7")
    )
    if audit_df.loc[precursor_rule_mask, "사건유형_재판정_ko"].ne("전조형 고장").any():
        raise SystemExit("any fault panel meeting the explicit precursor rule must re-evaluate to 전조형 고장")
    if explicit_precursor_rule_hits != int(precursor_rule_mask.sum()):
        raise SystemExit("explicit precursor rule hit count mismatch")

    mismatch_mask = (
        (audit_df["사건유형_재판정_ko"].eq("전조형 고장") & audit_df["전조평가셋편입_flag"].eq(0))
        | (audit_df["사건유형_재판정_ko"].eq("급작 고장") & audit_df["급작평가셋편입_flag"].eq(0))
    )

    summary_row = {
        "고유_고장패널수": int(len(audit_df)),
        "사건유형_재판정_전조형수": int(audit_df["사건유형_재판정_ko"].eq("전조형 고장").sum()),
        "사건유형_재판정_급작수": int(audit_df["사건유형_재판정_ko"].eq("급작 고장").sum()),
        "사건유형_재판정_보류수": int(audit_df["사건유형_재판정_ko"].eq("고장유형 보류").sum()),
        "최종고장양상_급격종료수": int(audit_df["최종고장양상_재판정_ko"].eq("급격 종료").sum()),
        "전조흔적_패널수": int(pd.to_numeric(audit_df["전조흔적_flag"], errors="coerce").fillna(0).sum()),
        "순수급작_패널수": int(pd.to_numeric(audit_df["순수급작_flag"], errors="coerce").fillna(0).sum()),
        "전조평가셋편입_패널수": int(pd.to_numeric(audit_df["전조평가셋편입_flag"], errors="coerce").fillna(0).sum()),
        "급작평가셋편입_패널수": int(pd.to_numeric(audit_df["급작평가셋편입_flag"], errors="coerce").fillna(0).sum()),
        "해석과평가셋불일치_패널수": int(mismatch_mask.sum()),
        "현재표_보정필요_패널수": int(pd.to_numeric(audit_df["현재표_보정필요여부_flag"], errors="coerce").fillna(0).sum()),
        "note_ko": (
            f"current fault panel {len(audit_df)}건에 explicit stored-field rule 을 적용했다. "
            f"재판정 결과 전조형 {int(audit_df['사건유형_재판정_ko'].eq('전조형 고장').sum())}건, "
            f"급작 {int(audit_df['사건유형_재판정_ko'].eq('급작 고장').sum())}건, "
            f"보류 {int(audit_df['사건유형_재판정_ko'].eq('고장유형 보류').sum())}건이다. "
            f"사건 해석상 전조형 패널은 {int(audit_df['사건유형_재판정_ko'].eq('전조형 고장').sum())}건이지만, "
            f"strict precursor eval set 편입은 {int(pd.to_numeric(audit_df['전조평가셋편입_flag'], errors='coerce').fillna(0).sum())}건이다. "
            f"재판정과 evaluation-set inclusion 이 어긋나는 fault panel 은 {int(mismatch_mask.sum())}건이고, 이 표를 downstream event-semantics authoritative source 로 쓴다."
        ),
    }
    summary_df = pd.DataFrame([summary_row]).reindex(columns=SUMMARY_COLS)

    mismatch_df = audit_df.loc[mismatch_mask, ["site", "panel_id", "사건유형_재판정_ko"]].copy()
    correction_df = audit_df.loc[audit_df["현재표_보정필요여부_flag"].eq(1), ["site", "panel_id", "현재표_사건유형_ko", "사건유형_재판정_ko", "현재표_최종고장양상_ko", "최종고장양상_재판정_ko"]].copy()
    pure_abrupt_df = audit_df.loc[audit_df["사건유형_재판정_ko"].eq("급작 고장"), ["site", "panel_id"]].copy()

    mismatch_lines = [
        f"- {row.site} / {row.panel_id} / 재판정={row.사건유형_재판정_ko}"
        for row in mismatch_df.itertuples(index=False)
    ] or ["- 없음"]
    correction_lines = [
        f"- {row.site} / {row.panel_id} / 현재표={row.현재표_사건유형_ko}·{row.현재표_최종고장양상_ko} -> 재판정={row.사건유형_재판정_ko}·{row.최종고장양상_재판정_ko}"
        for row in correction_df.itertuples(index=False)
    ] or ["- 없음"]
    pure_abrupt_lines = [
        f"- {row.site} / {row.panel_id}"
        for row in pure_abrupt_df.itertuples(index=False)
    ] or ["- 없음"]

    note = "\n".join(
        [
            "## 1. 전체 고장 패널 전수 결과",
            f"- 현재 고장 패널 {len(audit_df)}건을 explicit stored-field rule 로 다시 봤다.",
            f"- 재판정 결과는 전조형 고장 {summary_row['사건유형_재판정_전조형수']}건, 급작 고장 {summary_row['사건유형_재판정_급작수']}건, 고장유형 보류 {summary_row['사건유형_재판정_보류수']}건이다.",
            "- 이 audit 표는 downstream 사건유형/최종고장양상 reconciliation 에서 authoritative source 로 쓴다.",
            f"- 현재표 보정 필요 패널은 {summary_row['현재표_보정필요_패널수']}건이다.",
            "",
            "## 2. 순수 급작 패널 수",
            f"- strict rule 재판정 기준 순수 급작 패널 수는 {summary_row['사건유형_재판정_급작수']}건이다.",
            *pure_abrupt_lines,
            "",
            "## 3. 전조흔적은 있지만 평가셋에 안 들어간 패널",
            f"- 사건 해석상 전조형 패널은 {summary_row['사건유형_재판정_전조형수']}건이지만, strict precursor eval set 편입은 {summary_row['전조평가셋편입_패널수']}건이다.",
            f"- 따라서 해석과 evaluation-set inclusion 이 어긋나는 고장 패널은 {summary_row['해석과평가셋불일치_패널수']}건이다.",
            *mismatch_lines,
            "",
            "## 4. 지금 바로 고쳐야 하는 패널",
            *correction_lines,
            "",
        ]
    )
    return audit_df, summary_df, note


def write_outputs(root: Path, audit_df: pd.DataFrame, summary_df: pd.DataFrame, note: str) -> None:
    write_csv(audit_df, root / AUDIT_OUTPUT)
    write_csv(summary_df, root / SUMMARY_OUTPUT)
    write_text(note, root / NOTE_OUTPUT)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    audit_df, summary_df, note = build_audit(root)
    write_outputs(root, audit_df, summary_df, note)
    print(f"Wrote {AUDIT_OUTPUT}")
    print(f"Wrote {SUMMARY_OUTPUT}")
    print(f"Wrote {NOTE_OUTPUT}")


if __name__ == "__main__":
    main()
