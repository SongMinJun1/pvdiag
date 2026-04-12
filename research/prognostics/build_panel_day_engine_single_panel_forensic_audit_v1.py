from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
from pandas.errors import EmptyDataError


TARGET_SITE = "conalog"
TARGET_PANEL_ID = "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"

SUMMARY_OUTPUT = "_share/panel_day_engine_c42997_1_1_forensic_summary_v1.csv"
TIMELINE_OUTPUT = "_share/panel_day_engine_c42997_1_1_forensic_timeline_v1.csv"
NOTE_OUTPUT = "_share/panel_day_engine_c42997_1_1_forensic_note_v1.md"


@dataclass(frozen=True)
class OriginalLabelEvidence:
    label_ko: str
    evidence_ko: str
    recovered_flag: bool


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a forensic audit pack for a single panel without changing detector logic."
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
        try:
            return pd.read_csv(path, low_memory=False)
        except EmptyDataError:
            return pd.DataFrame()


def exact_panel_rows(df: pd.DataFrame, panel_id: str, site: str | None = None) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    panel_cols = [col for col in df.columns if col.lower() in {"panel_id", "display_entity_id", "entity_id"}]
    if not panel_cols:
        return df.iloc[0:0].copy()
    mask = False
    for col in panel_cols:
        current = df[col].astype(str).eq(panel_id)
        mask = current if mask is False else (mask | current)
    result = df.loc[mask].copy()
    if site is not None and "site" in result.columns:
        result = result.loc[result["site"].astype(str).eq(site)].copy()
    return result


def to_timestamp(value: object) -> pd.Timestamp | None:
    if pd.isna(value):
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    return ts


def format_date(value: object) -> str:
    ts = to_timestamp(value)
    if ts is None:
        return ""
    return ts.strftime("%Y-%m-%d")


def date_gap_days(start: object, end: object) -> int | None:
    start_ts = to_timestamp(start)
    end_ts = to_timestamp(end)
    if start_ts is None or end_ts is None:
        return None
    return int((end_ts - start_ts).days)


def bool_sum(series: pd.Series) -> int:
    return int(series.fillna(False).astype(bool).sum())


def vendor_fault_family_to_ko(value: object) -> str:
    text = str(value).strip()
    mapping = {
        "open_or_device_issue_like": "개방/장치이상형",
        "diode_like": "다이오드형",
        "module_damage_like": "모듈손상형",
    }
    if not text or text.lower() == "nan":
        return "미확인"
    return mapping.get(text, text)


def recover_original_kernel_label(root: Path) -> OriginalLabelEvidence:
    candidate_specs = [
        (
            root / "_share/partner_review_pack_send/return_sheet_send.csv",
            ["our_phenotype", "our_dominant_family"],
        ),
        (
            root / "_share/partner_review_pack_send/panel_review_for_partner.csv",
            ["phenotype", "dominant_family"],
        ),
        (
            root / "data/conalog/out/latest_panel_status_enriched.csv",
            ["phenotype", "dominant_family"],
        ),
    ]
    for path, columns in candidate_specs:
        df = read_csv(path, required=False)
        row_df = exact_panel_rows(df, TARGET_PANEL_ID)
        if row_df.empty:
            continue
        row = row_df.iloc[0]
        values = []
        for column in columns:
            if column in row.index:
                raw = str(row[column]).strip()
                if raw and raw.lower() != "nan":
                    values.append(raw)
        if values:
            label = " / ".join(values)
            evidence = f"{path.relative_to(root)} ({', '.join(columns)})"
            return OriginalLabelEvidence(
                label_ko=label,
                evidence_ko=evidence,
                recovered_flag=True,
            )
    return OriginalLabelEvidence(
        label_ko="미확인",
        evidence_ko="현재 저장 산출물에서 직접 확인 실패",
        recovered_flag=False,
    )


def earliest_true_date(df: pd.DataFrame, column: str, date_column: str = "date") -> pd.Timestamp | None:
    if df.empty or column not in df.columns or date_column not in df.columns:
        return None
    working = df.loc[df[column].fillna(False).astype(bool), date_column]
    if working.empty:
        return None
    value = pd.to_datetime(working, errors="coerce").min()
    return None if pd.isna(value) else value


def window_range(*dates: object) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    parsed = [to_timestamp(value) for value in dates]
    parsed = [value for value in parsed if value is not None]
    if not parsed:
        return None, None
    return min(parsed), max(parsed)


def range_text(start: object, end: object) -> str:
    start_text = format_date(start)
    end_text = format_date(end)
    if not start_text and not end_text:
        return ""
    if start_text == end_text:
        return start_text
    return f"{start_text}~{end_text}"


def build_timeline_rows(
    reaudit_row: pd.Series,
    vendor_row: pd.Series | None,
    nonprec_row: pd.Series,
    core_df: pd.DataFrame,
    gate_df: pd.DataFrame,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    def add(stage: str, date_value: object, source_file: str, source_field: str, value: str, interpretation: str) -> None:
        rows.append(
            {
                "단계": stage,
                "날짜": format_date(date_value) if stage.endswith("date") else (range_text(date_value[0], date_value[1]) if isinstance(date_value, tuple) else format_date(date_value)),
                "source_file": source_file,
                "source_field": source_field,
                "값_ko": value,
                "해석_ko": interpretation,
            }
        )

    first_warning = to_timestamp(reaudit_row.get("first_warning_date"))
    retrospective_onset = to_timestamp(reaudit_row.get("retrospective_onset_date"))
    strict_trigger = to_timestamp(reaudit_row.get("strict_trigger_date"))
    earliest_local_ews = earliest_true_date(gate_df, "ews_warning")
    earliest_prefault_b = earliest_true_date(gate_df, "prefault_B")
    abrupt_anchor = to_timestamp(nonprec_row.get("anchor_date"))
    first_final_fault = earliest_true_date(core_df, "final_fault")
    first_critical_fault = earliest_true_date(core_df, "critical_fault")
    dead_diag = to_timestamp(core_df["dead_diag_date"].dropna().iloc[0]) if "dead_diag_date" in core_df.columns and not core_df["dead_diag_date"].dropna().empty else None
    diagnosis_online = to_timestamp(core_df["diagnosis_date_online"].dropna().iloc[0]) if "diagnosis_date_online" in core_df.columns and not core_df["diagnosis_date_online"].dropna().empty else None

    if earliest_local_ews is not None:
        add(
            "first_local_warning_date",
            earliest_local_ews,
            "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
            "ews_warning",
            format_date(earliest_local_ews),
            "일별 helper 기준 earliest local warning 이다.",
        )
    if first_warning is not None:
        add(
            "first_warning_date",
            first_warning,
            "_share/panel_date_reaudit_working.csv",
            "first_warning_date",
            format_date(first_warning),
            "재감사 기준 처음으로 의미 있는 warning 으로 본 날짜다.",
        )
    if retrospective_onset is not None:
        add(
            "retrospective_onset_date",
            retrospective_onset,
            "_share/panel_date_reaudit_working.csv",
            "retrospective_onset_date",
            format_date(retrospective_onset),
            "재감사에서 되짚어 잡은 onset 날짜다.",
        )
    if earliest_prefault_b is not None:
        add(
            "first_prefault_B_date",
            earliest_prefault_b,
            "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
            "prefault_B",
            format_date(earliest_prefault_b),
            "prefault_B 조건이 처음 켜진 날짜다.",
        )
    if strict_trigger is not None:
        add(
            "strict_trigger_date",
            strict_trigger,
            "_share/panel_date_reaudit_working.csv",
            "strict_trigger_date",
            format_date(strict_trigger),
            "현재 재감사에서 강한 trigger 로 쓰는 기준일이다.",
        )
    if abrupt_anchor is not None:
        add(
            "abrupt_anchor_date",
            abrupt_anchor,
            "_share/panel_day_engine_non_precursor_performance_cases_v1.csv",
            "anchor_date",
            format_date(abrupt_anchor),
            "non-precursor performance case에서 사용한 anchor 날짜다.",
        )
    if first_final_fault is not None:
        add(
            "first_final_fault_date",
            first_final_fault,
            "data/conalog/out/panel_day_core.csv",
            "final_fault",
            format_date(first_final_fault),
            "panel_day_core 상 final_fault 가 처음 True가 된 날이다.",
        )
    if first_critical_fault is not None:
        add(
            "first_critical_fault_date",
            first_critical_fault,
            "data/conalog/out/panel_day_core.csv",
            "critical_fault",
            format_date(first_critical_fault),
            "panel_day_core 상 critical_fault 가 처음 True가 된 날이다.",
        )
    if dead_diag is not None:
        add(
            "abrupt_fault_date",
            dead_diag,
            "data/conalog/out/panel_day_core.csv",
            "dead_diag_date",
            format_date(dead_diag),
            "dead diagnostic 날짜다. strong trigger 다음 날로 기록돼 있다.",
        )
    if diagnosis_online is not None:
        add(
            "diagnosis_date_online",
            diagnosis_online,
            "data/conalog/out/panel_day_core.csv",
            "diagnosis_date_online",
            format_date(diagnosis_online),
            "online diagnosis 날짜다.",
        )

    window_start, _ = window_range(first_warning, retrospective_onset, earliest_local_ews, earliest_prefault_b)
    if window_start is None or strict_trigger is None:
        return rows

    window_gate = gate_df.loc[(gate_df["date"] >= window_start) & (gate_df["date"] <= strict_trigger)].copy()
    window_core = core_df.loc[(core_df["date"] >= window_start) & (core_df["date"] <= strict_trigger)].copy()
    window_label = range_text(window_start, strict_trigger)

    def add_window_metric(stage: str, source_field: str, value: object, interpretation: str, source_file: str) -> None:
        rows.append(
            {
                "단계": stage,
                "날짜": window_label,
                "source_file": source_file,
                "source_field": source_field,
                "값_ko": value,
                "해석_ko": interpretation,
            }
        )

    add_window_metric(
        "window_ae_active_days",
        "prefault_cond_ae",
        int(window_gate["prefault_cond_ae"].fillna(False).astype(bool).sum()),
        "earliest warning/onset 부터 강한 trigger 전까지 AE 조건이 켜진 일수다.",
        "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
    )
    add_window_metric(
        "window_dtw_active_days",
        "prefault_cond_dtw",
        int(window_gate["prefault_cond_dtw"].fillna(False).astype(bool).sum()),
        "같은 구간에서 DTW 조건이 켜진 일수다.",
        "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
    )
    add_window_metric(
        "window_hs_active_days",
        "cond_hs",
        int(window_gate["cond_hs"].fillna(False).astype(bool).sum()),
        "같은 구간에서 HS 조건이 켜진 일수다.",
        "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
    )
    add_window_metric(
        "window_cond_evt_days",
        "cond_evt",
        int(window_gate["cond_evt"].fillna(False).astype(bool).sum()),
        "같은 구간에서 cond_evt 가 켜진 일수다.",
        "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
    )
    add_window_metric(
        "window_pre_alarm_days",
        "pre_alarm",
        int(window_gate["pre_alarm"].fillna(False).astype(bool).sum()),
        "같은 구간에서 pre_alarm 이 켜진 일수다.",
        "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
    )
    add_window_metric(
        "window_final_fault_days",
        "final_fault",
        int(window_core["final_fault"].fillna(False).astype(bool).sum()),
        "같은 구간에서 final_fault 가 켜진 일수다.",
        "data/conalog/out/panel_day_core.csv",
    )
    add_window_metric(
        "window_max_v_drop",
        "v_drop",
        float(pd.to_numeric(window_core["v_drop"], errors="coerce").max()),
        "강한 trigger 전 window에서 본 최대 v_drop 이다.",
        "data/conalog/out/panel_day_core.csv",
    )
    add_window_metric(
        "window_min_mid_ratio",
        "mid_ratio",
        float(pd.to_numeric(window_core["mid_ratio"], errors="coerce").min()),
        "강한 trigger 전 window에서 본 최소 mid_ratio 다.",
        "data/conalog/out/panel_day_core.csv",
    )
    add_window_metric(
        "window_min_mid_v_ratio",
        "mid_v_ratio",
        float(pd.to_numeric(window_core["mid_v_ratio"], errors="coerce").min()),
        "강한 trigger 전 window에서 본 최소 mid_v_ratio 다.",
        "data/conalog/out/panel_day_core.csv",
    )
    return rows


def judge_event_timing(
    precursor_truth_df: pd.DataFrame,
    reaudited_start: pd.Timestamp | None,
    strict_trigger: pd.Timestamp | None,
    earliest_local_warning: pd.Timestamp | None,
) -> str:
    if not precursor_truth_df.empty:
        return "전조형고장의심"
    if reaudited_start is not None and strict_trigger is not None and (strict_trigger - reaudited_start).days >= 7:
        return "전조흔적있음_순수급작보류"
    if earliest_local_warning is None and strict_trigger is not None:
        return "순수급작의심"
    return "불충분"


def judge_certainty(
    vendor_reply_class: str,
    vendor_note: str,
    candidate_validity: str,
    original_label_recovered: bool,
    panel_table_event_type: str,
) -> str:
    note = (vendor_note or "").strip()
    validity = (candidate_validity or "").strip()
    if "현장확인 안됨" in note or validity == "needs_more_info":
        return "보류"
    if vendor_reply_class == "vendor_likely_positive" and original_label_recovered and panel_table_event_type:
        return "중간"
    return "보류"


def build_note(summary_row: dict[str, object]) -> str:
    original_recovered = "회수됨" if summary_row["원래_커널로그라벨_ko"] != "미확인" else "직접 회수 실패"
    correction_need = "필요" if int(summary_row["현재표_보정필요여부_flag"]) == 1 else "불필요"
    lines = [
        "## 1. 현재 파일에서 확인된 사실",
        f"- 원래 커널로그 라벨은 {original_recovered} 상태다. 현재 저장 산출물에서 읽힌 값은 `{summary_row['원래_커널로그라벨_ko']}` 이다.",
        f"- 현재 재감사 라벨은 `{summary_row['현재_재감사라벨_ko']}` 이고, 현재 패널표 사건유형은 `{summary_row['현재_패널표_사건유형_ko']}` 이다.",
        f"- strong trigger 이전 전조흔적 시작일은 `{summary_row['전조흔적_시작일']}` 이고, 강한 trigger 일은 `{summary_row['강한트리거일']}` 이다.",
        "",
        "## 2. 서로 충돌하는 지점",
        f"- historical kernel wording은 `{summary_row['원래_커널로그라벨_ko']}` 쪽인데, 현재 패널표는 `{summary_row['현재_패널표_사건유형_ko']}` / `{summary_row['현재_패널표_커널로그원인군_ko']}` 로 더 단단하게 읽히게 만든다.",
        "- 재감사 쪽에는 `현장확인 안됨` 과 `needs_more_info`가 남아 있어서, stored evidence만으로 즉시 강한 확정판정을 주기 어렵다.",
        "",
        "## 3. 지금 가장 안전한 판정",
        f"- 이 패널은 `{summary_row['사건시간양상_판정_ko']}` 으로 보는 것이 가장 안전하다.",
        "- 즉, 현재로서는 순수 급작으로 고정하기보다 holdout/needs-review 로 두는 쪽이 안전하다.",
        "",
        "## 4. 왜 보정이 필요한지",
        f"- 현재 표 보정 필요 여부는 `{correction_need}` 이다.",
        "- strong trigger 훨씬 이전부터 precursor-like evidence 가 있었는데, 현재 패널표 한 줄만 보면 pure abrupt 처럼 읽힐 수 있다.",
        "- 그래서 이 패널은 event type 과 terminal pattern 을 분리해 읽는 주석이 필요하다.",
    ]
    return "\n".join(lines) + "\n"


def build_forensic_pack(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    share_dir = root / "_share"
    reaudited_df = read_csv(share_dir / "panel_date_reaudit_working.csv")
    vendor_df = read_csv(share_dir / "vendor_reply_adjudication_latest.csv", required=False)
    read_csv(share_dir / "full_algorithm_case_errors_v2.csv", required=False)
    nonprec_df = read_csv(share_dir / "panel_day_engine_non_precursor_performance_cases_v1.csv")
    precursor_truth_df = read_csv(share_dir / "panel_day_engine_precursor_onset_truth_v1.csv")
    panel_table_df = read_csv(share_dir / "panel_day_engine_panel_multiaxis_verdict_v1.csv")
    core_df = read_csv(root / "data/conalog/out/panel_day_core.csv")
    gate_df = read_csv(root / "data/conalog/out/ae_simple_local_precursor_gate_daily.csv")

    reaudit_row_df = exact_panel_rows(reaudited_df, TARGET_PANEL_ID, TARGET_SITE)
    if reaudit_row_df.empty:
        raise RuntimeError(f"Target panel is missing from panel_date_reaudit_working.csv: {TARGET_PANEL_ID}")
    nonprec_row_df = exact_panel_rows(nonprec_df, TARGET_PANEL_ID, TARGET_SITE)
    if nonprec_row_df.empty:
        raise RuntimeError(f"Target panel is missing from panel_day_engine_non_precursor_performance_cases_v1.csv: {TARGET_PANEL_ID}")
    panel_table_row_df = exact_panel_rows(panel_table_df, TARGET_PANEL_ID, TARGET_SITE)
    if panel_table_row_df.empty:
        raise RuntimeError(f"Target panel is missing from panel_day_engine_panel_multiaxis_verdict_v1.csv: {TARGET_PANEL_ID}")

    vendor_row_df = exact_panel_rows(vendor_df, TARGET_PANEL_ID, TARGET_SITE) if not vendor_df.empty else pd.DataFrame()
    precursor_row_df = exact_panel_rows(precursor_truth_df, TARGET_PANEL_ID, TARGET_SITE) if not precursor_truth_df.empty else pd.DataFrame()

    reaudit_row = reaudit_row_df.iloc[0]
    nonprec_row = nonprec_row_df.iloc[0]
    panel_table_row = panel_table_row_df.iloc[0]
    vendor_row = vendor_row_df.iloc[0] if not vendor_row_df.empty else None
    evidence_row = vendor_row if vendor_row is not None else reaudit_row

    core_panel = core_df.loc[core_df["panel_id"].astype(str).eq(TARGET_PANEL_ID)].copy()
    gate_panel = gate_df.loc[gate_df["panel_id"].astype(str).eq(TARGET_PANEL_ID)].copy()
    if core_panel.empty or gate_panel.empty:
        raise RuntimeError("Target panel is missing from daily core/helper outputs.")
    core_panel["date"] = pd.to_datetime(core_panel["date"], errors="coerce")
    gate_panel["date"] = pd.to_datetime(gate_panel["date"], errors="coerce")

    original_label = recover_original_kernel_label(root)

    first_warning = to_timestamp(reaudit_row.get("first_warning_date"))
    retrospective_onset = to_timestamp(reaudit_row.get("retrospective_onset_date"))
    strong_trigger = to_timestamp(reaudit_row.get("strict_trigger_date"))
    earliest_local_warning = earliest_true_date(gate_panel, "ews_warning")
    official_start, _ = window_range(first_warning, retrospective_onset)
    start_for_lead = official_start or earliest_local_warning
    lead_days = date_gap_days(start_for_lead, strong_trigger)

    event_timing = judge_event_timing(precursor_row_df, start_for_lead, strong_trigger, earliest_local_warning)
    vendor_reply_class = str(evidence_row.get("vendor_reply_class", "")).strip()
    vendor_note = str(evidence_row.get("vendor_note", "")).strip()
    candidate_validity = str(nonprec_row.get("candidate_validity", "")).strip()
    certainty = judge_certainty(
        vendor_reply_class=vendor_reply_class,
        vendor_note=vendor_note,
        candidate_validity=candidate_validity,
        original_label_recovered=original_label.recovered_flag,
        panel_table_event_type=str(panel_table_row.get("사건유형_ko", "")).strip(),
    )

    current_reaudit_label = (
        f"{vendor_fault_family_to_ko(evidence_row.get('vendor_fault_family'))} "
        f"({evidence_row.get('vendor_fault_family', '')})"
    )
    correction_needed = int(event_timing != "순수급작의심" and str(panel_table_row.get("사건유형_ko", "")).strip() == "급작 고장")
    one_line = (
        f"원래 stored kernel wording은 `{original_label.label_ko}` 이고 현재 재감사는 `{current_reaudit_label}` 이다. "
        f"{format_date(start_for_lead)}부터 전조흔적이 보여 현재 패널표의 순수 급작 해석은 보류가 더 안전하다."
    )
    next_step = (
        "현재 패널표를 pure abrupt 확정으로 읽지 말고, 전조흔적 있음/needs-review 주석을 함께 붙여 manual holdout 으로 유지"
    )

    summary_row = {
        "site": TARGET_SITE,
        "panel_id": TARGET_PANEL_ID,
        "원래_커널로그라벨_ko": original_label.label_ko,
        "원래라벨_근거파일_ko": original_label.evidence_ko,
        "현재_재감사라벨_ko": current_reaudit_label,
        "현재_재감사_근거파일_ko": "_share/panel_date_reaudit_working.csv / _share/vendor_reply_adjudication_latest.csv",
        "현재_패널표_사건유형_ko": panel_table_row.get("사건유형_ko", ""),
        "현재_패널표_커널로그증상명_ko": panel_table_row.get("커널로그_증상명_ko", ""),
        "현재_패널표_커널로그원인군_ko": panel_table_row.get("커널로그_원인군_ko", ""),
        "현재_패널표_GPVS참고유형_ko": panel_table_row.get("GPVS_참고유형_ko", ""),
        "전조흔적_시작일": format_date(start_for_lead),
        "강한트리거일": format_date(strong_trigger),
        "선행기간_일": lead_days if lead_days is not None else "",
        "사건시간양상_판정_ko": event_timing,
        "확정도_판정_ko": certainty,
        "현재표_보정필요여부_flag": correction_needed,
        "핵심판정_한줄요약_ko": one_line,
        "다음보정권고_ko": next_step,
    }

    timeline_rows = build_timeline_rows(
        reaudit_row=reaudit_row,
        vendor_row=vendor_row,
        nonprec_row=nonprec_row,
        core_df=core_panel,
        gate_df=gate_panel,
    )
    summary_df = pd.DataFrame([summary_row])
    timeline_df = pd.DataFrame(timeline_rows)
    note_text = build_note(summary_row)
    return summary_df, timeline_df, note_text


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_df, timeline_df, note_text = build_forensic_pack(root)
    write_csv(summary_df, root / SUMMARY_OUTPUT)
    write_csv(timeline_df, root / TIMELINE_OUTPUT)
    write_text(note_text, root / NOTE_OUTPUT)
    print(f"Wrote {SUMMARY_OUTPUT}")
    print(f"Wrote {TIMELINE_OUTPUT}")
    print(f"Wrote {NOTE_OUTPUT}")


if __name__ == "__main__":
    main()
