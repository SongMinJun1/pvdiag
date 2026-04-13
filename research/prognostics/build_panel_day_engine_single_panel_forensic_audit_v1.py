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
FAULT_PANEL_EVENT_AUDIT_NAME = "panel_day_engine_fault_panel_event_audit_v1.csv"


@dataclass(frozen=True)
class OriginalLabelEvidence:
    label_ko: str
    evidence_ko: str
    recovered_flag: bool


@dataclass(frozen=True)
class ContinuityAssessment:
    earliest_warning_date: pd.Timestamp | None
    earliest_onset_date: pd.Timestamp | None
    strong_trigger_date: pd.Timestamp | None
    pretrigger_start_date: pd.Timestamp | None
    pretrigger_end_date: pd.Timestamp | None
    days_between_onset_and_trigger: int | None
    effective_lead_days: int | None
    pretrigger_window_day_count: int
    ae_active_days_pretrigger: int
    dtw_active_days_pretrigger: int
    hs_active_days_pretrigger: int
    cond_evt_days_pretrigger: int
    pre_alarm_days_pretrigger: int
    final_fault_days_pretrigger: int
    longest_consecutive_active_run_days: int
    longest_consecutive_cond_evt_run_days: int
    last_gap_before_trigger_days: int | None
    first_ae_active_date: pd.Timestamp | None
    first_dtw_active_date: pd.Timestamp | None
    first_hs_active_date: pd.Timestamp | None
    first_cond_evt_date: pd.Timestamp | None
    first_pre_alarm_date: pd.Timestamp | None
    last_pretrigger_active_date: pd.Timestamp | None
    continuity_judgment_ko: str
    event_recommendation_ko: str


@dataclass(frozen=True)
class RuleBasedEventDecision:
    event_type_ko: str
    terminal_pattern_ko: str
    event_rule_ko: str
    terminal_rule_ko: str
    abrupt_positive_evidence_flag: int
    first_final_fault_date: pd.Timestamp | None
    first_critical_fault_date: pd.Timestamp | None
    dead_diag_date: pd.Timestamp | None


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


def earliest_non_null_date(df: pd.DataFrame, columns: Iterable[str]) -> pd.Timestamp | None:
    if df.empty:
        return None
    values: list[pd.Timestamp] = []
    for column in columns:
        if column not in df.columns:
            continue
        parsed = pd.to_datetime(df[column], errors="coerce").dropna()
        if not parsed.empty:
            values.append(parsed.min())
    if not values:
        return None
    return min(values)


def earliest_true_date(df: pd.DataFrame, column: str, date_column: str = "date") -> pd.Timestamp | None:
    if df.empty or column not in df.columns or date_column not in df.columns:
        return None
    working = df.loc[df[column].fillna(False).astype(bool), date_column]
    if working.empty:
        return None
    value = pd.to_datetime(working, errors="coerce").min()
    return None if pd.isna(value) else value


def latest_true_date(df: pd.DataFrame, column: str, date_column: str = "date") -> pd.Timestamp | None:
    if df.empty or column not in df.columns or date_column not in df.columns:
        return None
    working = df.loc[df[column].fillna(False).astype(bool), date_column]
    if working.empty:
        return None
    value = pd.to_datetime(working, errors="coerce").max()
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


def bool_or_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=bool)
    result = pd.Series(False, index=df.index)
    for column in columns:
        if column in df.columns:
            result = result | df[column].fillna(False).astype(bool)
    return result


def longest_consecutive_true_run(dates: pd.Series, flags: pd.Series) -> int:
    if dates.empty or flags.empty:
        return 0
    working = pd.DataFrame({"date": pd.to_datetime(dates, errors="coerce"), "flag": flags.fillna(False).astype(bool)})
    working = working.dropna(subset=["date"]).sort_values("date")
    longest = 0
    current = 0
    prev_true_date: pd.Timestamp | None = None
    for row in working.itertuples(index=False):
        if not row.flag:
            current = 0
            prev_true_date = None
            continue
        if prev_true_date is not None and int((row.date - prev_true_date).days) == 1:
            current += 1
        else:
            current = 1
        prev_true_date = row.date
        longest = max(longest, current)
    return longest


def judge_continuity(
    *,
    explicit_precursor_eval_flag: bool,
    effective_lead_days: int | None,
    ae_active_days_pretrigger: int,
    dtw_active_days_pretrigger: int,
    hs_active_days_pretrigger: int,
    cond_evt_days_pretrigger: int,
    pre_alarm_days_pretrigger: int,
    longest_consecutive_active_run_days: int,
    longest_consecutive_cond_evt_run_days: int,
    last_gap_before_trigger_days: int | None,
) -> str:
    has_any_trace = any(
        value > 0
        for value in (
            ae_active_days_pretrigger,
            dtw_active_days_pretrigger,
            hs_active_days_pretrigger,
            cond_evt_days_pretrigger,
            pre_alarm_days_pretrigger,
        )
    )
    if explicit_precursor_eval_flag and effective_lead_days is not None and effective_lead_days >= 7:
        return "동일사건_연속가능성_높음"
    if effective_lead_days is not None and effective_lead_days >= 7:
        sustained_activity = (
            longest_consecutive_active_run_days >= 7
            and ae_active_days_pretrigger >= 7
            and dtw_active_days_pretrigger >= 5
            and last_gap_before_trigger_days is not None
            and last_gap_before_trigger_days <= 3
        )
        event_support = (
            cond_evt_days_pretrigger >= 3
            or pre_alarm_days_pretrigger >= 2
            or longest_consecutive_cond_evt_run_days >= 3
            or hs_active_days_pretrigger >= 3
        )
        if sustained_activity and event_support:
            return "동일사건_연속가능성_높음"
        weak_continuity = (
            longest_consecutive_active_run_days >= 3
            or ae_active_days_pretrigger >= 3
            or dtw_active_days_pretrigger >= 3
            or cond_evt_days_pretrigger >= 2
            or pre_alarm_days_pretrigger >= 1
        )
        if weak_continuity:
            if last_gap_before_trigger_days is not None and last_gap_before_trigger_days >= 14:
                return "초기경고와_후기트리거_별개가능성"
            return "전조흔적은있지만_연속성불충분"
        if has_any_trace:
            return "초기경고와_후기트리거_별개가능성"
    if has_any_trace:
        return "전조흔적은있지만_연속성불충분"
    return "불충분"


def continuity_recommendation_for(continuity_judgment_ko: str) -> str:
    mapping = {
        "동일사건_연속가능성_높음": "전조형고장으로상향",
        "전조흔적은있지만_연속성불충분": "고장유형보류유지",
        "초기경고와_후기트리거_별개가능성": "순수급작으로복귀",
        "불충분": "추가수동검토필요",
    }
    return mapping[continuity_judgment_ko]


def nonempty_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def abrupt_positive_evidence_exists(nonprec_row: pd.Series) -> int:
    text_columns = [
        "anchor_date",
        "first_confirmed_fault_date",
        "first_critical_fault_date",
        "first_final_fault_date",
    ]
    flag_columns = [
        "confirmed_fault_hit_by_anchor_flag",
        "confirmed_fault_hit_within_3d_after_flag",
        "confirmed_fault_hit_within_7d_after_flag",
        "critical_fault_hit_by_anchor_flag",
        "critical_fault_hit_within_3d_after_flag",
        "critical_fault_hit_within_7d_after_flag",
        "final_fault_hit_by_anchor_flag",
        "final_fault_hit_within_3d_after_flag",
        "final_fault_hit_within_7d_after_flag",
    ]
    for column in text_columns:
        if nonempty_text(nonprec_row.get(column)):
            return 1
    for column in flag_columns:
        if pd.to_numeric(pd.Series([nonprec_row.get(column)]), errors="coerce").fillna(0).iloc[0] == 1:
            return 1
    return 0


def first_true_core_date(core_df: pd.DataFrame, column: str) -> pd.Timestamp | None:
    return earliest_true_date(core_df, column)


def repeated_core_date(core_df: pd.DataFrame, column: str) -> pd.Timestamp | None:
    if column not in core_df.columns:
        return None
    values = pd.to_datetime(core_df[column], errors="coerce").dropna()
    if values.empty:
        return None
    return values.iloc[0]


def determine_rule_based_event_decision(
    reaudit_row: pd.Series,
    nonprec_row: pd.Series,
    core_df: pd.DataFrame,
) -> RuleBasedEventDecision:
    retrospective_onset = to_timestamp(reaudit_row.get("retrospective_onset_date"))
    strict_trigger = to_timestamp(reaudit_row.get("strict_trigger_date"))
    onset_confidence = nonempty_text(reaudit_row.get("onset_confidence"))
    onset_method = nonempty_text(reaudit_row.get("onset_method"))
    abrupt_positive_flag = abrupt_positive_evidence_exists(nonprec_row)
    first_final_fault_date = first_true_core_date(core_df, "final_fault")
    first_critical_fault_date = first_true_core_date(core_df, "critical_fault")
    dead_diag_date = repeated_core_date(core_df, "dead_diag_date")

    precursor_rule = (
        retrospective_onset is not None
        and strict_trigger is not None
        and retrospective_onset < strict_trigger
        and onset_confidence == "high"
        and onset_method == "persistent_5of7"
    )
    abrupt_rule = retrospective_onset is None and abrupt_positive_flag == 1

    if precursor_rule:
        event_type = "전조형 고장"
        event_rule = (
            "retrospective_onset_date 비공란, strict_trigger_date 비공란, "
            "retrospective_onset_date < strict_trigger_date, onset_confidence=high, "
            "onset_method=persistent_5of7 이 모두 성립해 전조형 고장으로 결정"
        )
    elif abrupt_rule:
        event_type = "급작 고장"
        event_rule = (
            "retrospective_onset_date 공란이고 anchor/final/critical hit 기반 abrupt positive evidence 가 있어 급작 고장으로 결정"
        )
    else:
        event_type = "고장유형 보류"
        event_rule = (
            "전조형 고장 규칙과 급작 고장 규칙을 모두 만족하지 않아 positive fault panel 이지만 고장유형 보류로 결정"
        )

    abrupt_ending = (
        first_final_fault_date is not None
        and strict_trigger is not None
        and first_final_fault_date == strict_trigger
        and dead_diag_date is not None
        and dead_diag_date <= strict_trigger + pd.Timedelta(days=1)
    )
    if abrupt_ending:
        terminal_pattern = "급격 종료"
        terminal_rule = (
            "first_final_fault_date == strict_trigger_date 이고 dead_diag_date <= strict_trigger_date + 1 day 라 급격 종료로 결정"
        )
    elif abrupt_positive_flag == 1:
        terminal_pattern = "급작 발생"
        terminal_rule = "급격 종료 규칙은 미충족이지만 abrupt positive evidence 가 있어 급작 발생으로 둔다."
    elif event_type == "전조형 고장":
        terminal_pattern = "진행성 악화"
        terminal_rule = "급격 종료 규칙이 없고 전조형 고장 규칙만 성립해 진행성 악화로 둔다."
    else:
        terminal_pattern = "불충분"
        terminal_rule = "stored field 만으로 terminal failure pattern 을 더 좁히기 어렵다."

    return RuleBasedEventDecision(
        event_type_ko=event_type,
        terminal_pattern_ko=terminal_pattern,
        event_rule_ko=event_rule,
        terminal_rule_ko=terminal_rule,
        abrupt_positive_evidence_flag=abrupt_positive_flag,
        first_final_fault_date=first_final_fault_date,
        first_critical_fault_date=first_critical_fault_date,
        dead_diag_date=dead_diag_date,
    )


def build_continuity_assessment(
    reaudit_row: pd.Series,
    precursor_truth_df: pd.DataFrame,
    core_df: pd.DataFrame,
    gate_df: pd.DataFrame,
) -> ContinuityAssessment:
    first_warning = to_timestamp(reaudit_row.get("first_warning_date"))
    earliest_local_warning = earliest_true_date(gate_df, "ews_warning")
    earliest_warning = window_range(first_warning, earliest_local_warning)[0]
    retrospective_onset = to_timestamp(reaudit_row.get("retrospective_onset_date"))
    precursor_truth_onset = earliest_non_null_date(
        precursor_truth_df,
        (
            "preferred_precursor_onset_date",
            "preferred_onset_date",
            "precursor_onset_date",
            "onset_date",
        ),
    )
    earliest_onset = window_range(retrospective_onset, precursor_truth_onset)[0]
    strong_trigger = to_timestamp(reaudit_row.get("strict_trigger_date"))
    pretrigger_start = window_range(earliest_warning, earliest_onset)[0]
    pretrigger_end = strong_trigger - pd.Timedelta(days=1) if strong_trigger is not None else None

    if (
        pretrigger_start is None
        or pretrigger_end is None
        or pretrigger_end < pretrigger_start
    ):
        empty_judgment = judge_continuity(
            explicit_precursor_eval_flag=not precursor_truth_df.empty,
            effective_lead_days=date_gap_days(pretrigger_start, strong_trigger),
            ae_active_days_pretrigger=0,
            dtw_active_days_pretrigger=0,
            hs_active_days_pretrigger=0,
            cond_evt_days_pretrigger=0,
            pre_alarm_days_pretrigger=0,
            longest_consecutive_active_run_days=0,
            longest_consecutive_cond_evt_run_days=0,
            last_gap_before_trigger_days=None,
        )
        return ContinuityAssessment(
            earliest_warning_date=earliest_warning,
            earliest_onset_date=earliest_onset,
            strong_trigger_date=strong_trigger,
            pretrigger_start_date=pretrigger_start,
            pretrigger_end_date=pretrigger_end,
            days_between_onset_and_trigger=date_gap_days(earliest_onset, strong_trigger),
            effective_lead_days=date_gap_days(pretrigger_start, strong_trigger),
            pretrigger_window_day_count=0,
            ae_active_days_pretrigger=0,
            dtw_active_days_pretrigger=0,
            hs_active_days_pretrigger=0,
            cond_evt_days_pretrigger=0,
            pre_alarm_days_pretrigger=0,
            final_fault_days_pretrigger=0,
            longest_consecutive_active_run_days=0,
            longest_consecutive_cond_evt_run_days=0,
            last_gap_before_trigger_days=None,
            first_ae_active_date=None,
            first_dtw_active_date=None,
            first_hs_active_date=None,
            first_cond_evt_date=None,
            first_pre_alarm_date=None,
            last_pretrigger_active_date=None,
            continuity_judgment_ko=empty_judgment,
            event_recommendation_ko=continuity_recommendation_for(empty_judgment),
        )

    pretrigger_gate = gate_df.loc[(gate_df["date"] >= pretrigger_start) & (gate_df["date"] <= pretrigger_end)].copy()
    pretrigger_core = core_df.loc[(core_df["date"] >= pretrigger_start) & (core_df["date"] <= pretrigger_end)].copy()
    active_any = bool_or_columns(
        pretrigger_gate,
        ("prefault_cond_ae", "prefault_cond_dtw", "cond_hs", "cond_evt", "pre_alarm", "prefault_B"),
    )
    last_active_date = None
    if not pretrigger_gate.empty and not active_any.empty and active_any.any():
        last_active_date = pd.to_datetime(pretrigger_gate.loc[active_any, "date"], errors="coerce").max()
        if pd.isna(last_active_date):
            last_active_date = None

    last_gap_before_trigger_days = None
    if strong_trigger is not None and last_active_date is not None:
        last_gap_before_trigger_days = max(0, int((strong_trigger - last_active_date).days - 1))

    ae_active_days = bool_sum(pretrigger_gate["prefault_cond_ae"]) if "prefault_cond_ae" in pretrigger_gate.columns else 0
    dtw_active_days = bool_sum(pretrigger_gate["prefault_cond_dtw"]) if "prefault_cond_dtw" in pretrigger_gate.columns else 0
    hs_active_days = bool_sum(pretrigger_gate["cond_hs"]) if "cond_hs" in pretrigger_gate.columns else 0
    cond_evt_days = bool_sum(pretrigger_gate["cond_evt"]) if "cond_evt" in pretrigger_gate.columns else 0
    pre_alarm_days = bool_sum(pretrigger_gate["pre_alarm"]) if "pre_alarm" in pretrigger_gate.columns else 0
    final_fault_days = bool_sum(pretrigger_core["final_fault"]) if "final_fault" in pretrigger_core.columns else 0

    continuity_judgment = judge_continuity(
        explicit_precursor_eval_flag=not precursor_truth_df.empty,
        effective_lead_days=date_gap_days(pretrigger_start, strong_trigger),
        ae_active_days_pretrigger=ae_active_days,
        dtw_active_days_pretrigger=dtw_active_days,
        hs_active_days_pretrigger=hs_active_days,
        cond_evt_days_pretrigger=cond_evt_days,
        pre_alarm_days_pretrigger=pre_alarm_days,
        longest_consecutive_active_run_days=longest_consecutive_true_run(pretrigger_gate["date"], active_any),
        longest_consecutive_cond_evt_run_days=(
            longest_consecutive_true_run(pretrigger_gate["date"], pretrigger_gate["cond_evt"])
            if "cond_evt" in pretrigger_gate.columns
            else 0
        ),
        last_gap_before_trigger_days=last_gap_before_trigger_days,
    )

    return ContinuityAssessment(
        earliest_warning_date=earliest_warning,
        earliest_onset_date=earliest_onset,
        strong_trigger_date=strong_trigger,
        pretrigger_start_date=pretrigger_start,
        pretrigger_end_date=pretrigger_end,
        days_between_onset_and_trigger=date_gap_days(earliest_onset, strong_trigger),
        effective_lead_days=date_gap_days(pretrigger_start, strong_trigger),
        pretrigger_window_day_count=int((pretrigger_end - pretrigger_start).days) + 1,
        ae_active_days_pretrigger=ae_active_days,
        dtw_active_days_pretrigger=dtw_active_days,
        hs_active_days_pretrigger=hs_active_days,
        cond_evt_days_pretrigger=cond_evt_days,
        pre_alarm_days_pretrigger=pre_alarm_days,
        final_fault_days_pretrigger=final_fault_days,
        longest_consecutive_active_run_days=longest_consecutive_true_run(pretrigger_gate["date"], active_any),
        longest_consecutive_cond_evt_run_days=(
            longest_consecutive_true_run(pretrigger_gate["date"], pretrigger_gate["cond_evt"])
            if "cond_evt" in pretrigger_gate.columns
            else 0
        ),
        last_gap_before_trigger_days=last_gap_before_trigger_days,
        first_ae_active_date=earliest_true_date(pretrigger_gate, "prefault_cond_ae"),
        first_dtw_active_date=earliest_true_date(pretrigger_gate, "prefault_cond_dtw"),
        first_hs_active_date=earliest_true_date(pretrigger_gate, "cond_hs"),
        first_cond_evt_date=earliest_true_date(pretrigger_gate, "cond_evt"),
        first_pre_alarm_date=earliest_true_date(pretrigger_gate, "pre_alarm"),
        last_pretrigger_active_date=last_active_date,
        continuity_judgment_ko=continuity_judgment,
        event_recommendation_ko=continuity_recommendation_for(continuity_judgment),
    )


def build_timeline_rows(
    reaudit_row: pd.Series,
    vendor_row: pd.Series | None,
    nonprec_row: pd.Series,
    core_df: pd.DataFrame,
    gate_df: pd.DataFrame,
    continuity: ContinuityAssessment,
    rule_decision: RuleBasedEventDecision,
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
    current_vendor_note = str(vendor_row.get("vendor_note", "")).strip() if vendor_row is not None else str(reaudit_row.get("vendor_note", "")).strip()

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
    if continuity.earliest_warning_date is not None:
        add(
            "earliest_warning_date",
            continuity.earliest_warning_date,
            "_share/panel_date_reaudit_working.csv + data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
            "first_warning_date + ews_warning",
            format_date(continuity.earliest_warning_date),
            "stored artifact 기준 earliest warning 날짜다.",
        )
    if continuity.earliest_onset_date is not None:
        add(
            "earliest_onset_date",
            continuity.earliest_onset_date,
            "_share/panel_date_reaudit_working.csv + _share/panel_day_engine_precursor_onset_truth_v1.csv",
            "retrospective_onset_date + preferred_precursor_onset_date",
            format_date(continuity.earliest_onset_date),
            "재감사 onset 과 strict precursor onset truth 중 더 이른 onset 후보다.",
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
    if continuity.pretrigger_start_date is not None and continuity.pretrigger_end_date is not None:
        add(
            "pretrigger_window_range",
            (continuity.pretrigger_start_date, continuity.pretrigger_end_date),
            "_share/panel_date_reaudit_working.csv + data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
            "earliest warning/onset .. trigger-1",
            range_text(continuity.pretrigger_start_date, continuity.pretrigger_end_date),
            "연속성 판단에 쓴 pretrigger window 다.",
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
    if window_start is not None and strict_trigger is not None:
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
            "earliest warning/onset 부터 강한 trigger 까지 AE 조건이 켜진 일수다.",
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
            "강한 trigger 전후 전체 window에서 본 최대 v_drop 이다.",
            "data/conalog/out/panel_day_core.csv",
        )
        add_window_metric(
            "window_min_mid_ratio",
            "mid_ratio",
            float(pd.to_numeric(window_core["mid_ratio"], errors="coerce").min()),
            "강한 trigger 전후 전체 window에서 본 최소 mid_ratio 다.",
            "data/conalog/out/panel_day_core.csv",
        )
        add_window_metric(
            "window_min_mid_v_ratio",
            "mid_v_ratio",
            float(pd.to_numeric(window_core["mid_v_ratio"], errors="coerce").min()),
            "강한 trigger 전후 전체 window에서 본 최소 mid_v_ratio 다.",
            "data/conalog/out/panel_day_core.csv",
        )

    pretrigger_label = range_text(continuity.pretrigger_start_date, continuity.pretrigger_end_date)

    def add_pretrigger_metric(stage: str, source_field: str, value: object, interpretation: str, source_file: str) -> None:
        rows.append(
            {
                "단계": stage,
                "날짜": pretrigger_label,
                "source_file": source_file,
                "source_field": source_field,
                "값_ko": value,
                "해석_ko": interpretation,
            }
        )

    if continuity.first_ae_active_date is not None:
        add(
            "first_ae_active_date",
            continuity.first_ae_active_date,
            "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
            "prefault_cond_ae",
            format_date(continuity.first_ae_active_date),
            "pretrigger window 안에서 AE가 처음 활성화된 날짜다.",
        )
    if continuity.first_dtw_active_date is not None:
        add(
            "first_dtw_active_date",
            continuity.first_dtw_active_date,
            "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
            "prefault_cond_dtw",
            format_date(continuity.first_dtw_active_date),
            "pretrigger window 안에서 DTW가 처음 활성화된 날짜다.",
        )
    if continuity.first_hs_active_date is not None:
        add(
            "first_hs_active_date",
            continuity.first_hs_active_date,
            "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
            "cond_hs",
            format_date(continuity.first_hs_active_date),
            "pretrigger window 안에서 HS가 처음 활성화된 날짜다.",
        )
    if continuity.first_cond_evt_date is not None:
        add(
            "first_cond_evt_date",
            continuity.first_cond_evt_date,
            "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
            "cond_evt",
            format_date(continuity.first_cond_evt_date),
            "pretrigger window 안에서 cond_evt가 처음 활성화된 날짜다.",
        )
    if continuity.first_pre_alarm_date is not None:
        add(
            "first_pre_alarm_date",
            continuity.first_pre_alarm_date,
            "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
            "pre_alarm",
            format_date(continuity.first_pre_alarm_date),
            "pretrigger window 안에서 pre_alarm이 처음 켜진 날짜다.",
        )
    if continuity.last_pretrigger_active_date is not None:
        add(
            "last_pretrigger_active_date",
            continuity.last_pretrigger_active_date,
            "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
            "prefault_cond_* / cond_evt / pre_alarm",
            format_date(continuity.last_pretrigger_active_date),
            "trigger 직전 마지막으로 precursor-like activity가 보인 날짜다.",
        )

    add_pretrigger_metric(
        "pretrigger_window_day_count",
        "date",
        continuity.pretrigger_window_day_count,
        "earliest warning/onset 부터 trigger 전날까지의 총 일수다.",
        "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
    )
    add_pretrigger_metric(
        "ae_active_days_pretrigger",
        "prefault_cond_ae",
        continuity.ae_active_days_pretrigger,
        "pretrigger window 안에서 AE 조건이 켜진 일수다.",
        "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
    )
    add_pretrigger_metric(
        "dtw_active_days_pretrigger",
        "prefault_cond_dtw",
        continuity.dtw_active_days_pretrigger,
        "pretrigger window 안에서 DTW 조건이 켜진 일수다.",
        "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
    )
    add_pretrigger_metric(
        "hs_active_days_pretrigger",
        "cond_hs",
        continuity.hs_active_days_pretrigger,
        "pretrigger window 안에서 HS 조건이 켜진 일수다.",
        "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
    )
    add_pretrigger_metric(
        "cond_evt_days_pretrigger",
        "cond_evt",
        continuity.cond_evt_days_pretrigger,
        "pretrigger window 안에서 cond_evt가 켜진 일수다.",
        "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
    )
    add_pretrigger_metric(
        "pre_alarm_days_pretrigger",
        "pre_alarm",
        continuity.pre_alarm_days_pretrigger,
        "pretrigger window 안에서 pre_alarm이 켜진 일수다.",
        "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
    )
    add_pretrigger_metric(
        "final_fault_days_pretrigger",
        "final_fault",
        continuity.final_fault_days_pretrigger,
        "pretrigger window 안에서는 final_fault가 거의 없거나 0이어야 정상이다.",
        "data/conalog/out/panel_day_core.csv",
    )
    add_pretrigger_metric(
        "longest_consecutive_active_run_days",
        "prefault_cond_* / cond_evt / pre_alarm",
        continuity.longest_consecutive_active_run_days,
        "전조 활성 계열이 끊기지 않고 이어진 가장 긴 연속 일수다.",
        "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
    )
    add_pretrigger_metric(
        "longest_consecutive_cond_evt_run_days",
        "cond_evt",
        continuity.longest_consecutive_cond_evt_run_days,
        "cond_evt가 연속으로 이어진 가장 긴 구간 길이다.",
        "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
    )
    add_pretrigger_metric(
        "last_gap_before_trigger_days",
        "prefault_cond_* / cond_evt / pre_alarm",
        continuity.last_gap_before_trigger_days if continuity.last_gap_before_trigger_days is not None else "",
        "마지막 precursor-like activity 뒤 trigger까지 비어 있는 일수다.",
        "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
    )
    add_pretrigger_metric(
        "continuity_judgment_ko",
        "pretrigger continuity",
        continuity.continuity_judgment_ko,
        "전조흔적이 strong trigger와 같은 사건으로 이어졌는지에 대한 continuity 판정이다.",
        "forensic continuity logic",
    )
    add_pretrigger_metric(
        "event_recommendation_ko",
        "continuity_judgment_ko",
        continuity.event_recommendation_ko,
        "연속성 판정을 바탕으로 지금 가장 안전한 사건 권고를 적는다.",
        "forensic continuity logic",
    )
    add_pretrigger_metric(
        "사건유형_결정_ko",
        "retrospective_onset_date / strict_trigger_date / onset_confidence / onset_method / abrupt positive evidence",
        rule_decision.event_type_ko,
        "최종 사건유형은 heuristic 문장이 아니라 stored-field explicit rule로 결정한다.",
        "forensic explicit event rule",
    )
    add_pretrigger_metric(
        "최종고장양상_결정_ko",
        "first_final_fault_date / dead_diag_date / strict_trigger_date",
        rule_decision.terminal_pattern_ko,
        "최종고장양상도 stored-field explicit rule로 결정한다.",
        "forensic explicit terminal rule",
    )
    if current_vendor_note:
        add_pretrigger_metric(
            "vendor_note_context",
            "vendor_note",
            current_vendor_note,
            "현장확인 여부와 보류 사유를 읽기 위한 vendor note다.",
            "_share/panel_date_reaudit_working.csv / _share/vendor_reply_adjudication_latest.csv",
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
    precursor_trace_sentence = (
        f"전조흔적은 실제로 있었다. earliest warning은 `{summary_row['earliest_warning_date']}` 이고 "
        f"earliest onset은 `{summary_row['earliest_onset_date']}` 이다."
        if summary_row["earliest_warning_date"] or summary_row["earliest_onset_date"]
        else "현재 저장 산출물만으로는 strong trigger 이전 전조흔적을 직접 확인하기 어렵다."
    )
    continuity_sentence = {
        "동일사건_연속가능성_높음": "이 흔적은 2025-03-21과 같은 사건으로 이어졌다고 볼 가능성이 높다.",
        "전조흔적은있지만_연속성불충분": "전조흔적은 보이지만 2025-03-21과 같은 사건으로 단정할 연속성은 아직 약하다.",
        "초기경고와_후기트리거_별개가능성": "초기 경고와 2025-03-21 strong trigger는 서로 다른 사건일 가능성을 열어 둬야 한다.",
        "불충분": "현재 저장 산출물만으로는 전조흔적과 2025-03-21의 연결성을 판정하기에 불충분하다.",
    }[summary_row["continuity_judgment_ko"]]
    lines = [
        "## 1. 현재 파일에서 확인된 사실",
        f"- 원래 커널로그 라벨은 {original_recovered} 상태다. 현재 저장 산출물에서 읽힌 값은 `{summary_row['원래_커널로그라벨_ko']}` 이다.",
        f"- 현재 재감사 라벨은 `{summary_row['현재_재감사라벨_ko']}` 이고, 현재 패널표 사건유형은 `{summary_row['현재_패널표_사건유형_ko']}` 이다.",
        f"- {precursor_trace_sentence}",
        f"- strong trigger 일은 `{summary_row['strong_trigger_date']}` 이고, 사건유형 최종 결정은 explicit stored-field rule 기준 `{summary_row['사건유형_결정_ko']}` / `{summary_row['최종고장양상_결정_ko']}` 이다.",
        "",
        "## 2. 서로 충돌하는 지점",
        f"- historical kernel wording은 `{summary_row['원래_커널로그라벨_ko']}` 쪽인데, 현재 패널표는 `{summary_row['현재_패널표_사건유형_ko']}` / `{summary_row['현재_패널표_커널로그원인군_ko']}` 로 더 단단하게 읽히게 만든다.",
        f"- continuity 지표는 `AE {summary_row['ae_active_days_pretrigger']}일 / DTW {summary_row['dtw_active_days_pretrigger']}일 / cond_evt {summary_row['cond_evt_days_pretrigger']}일 / 마지막 gap {summary_row['last_gap_before_trigger_days']}일` 이다.",
        "- 재감사 쪽에는 `현장확인 안됨` 과 `needs_more_info`가 남아 있어서, stored evidence만으로 즉시 강한 확정판정을 주기 어렵다.",
        f"- 다만 이번 사건유형 결정은 heuristic recommendation 문장이 아니라 `{summary_row['사건유형_결정규칙_ko']}` 와 `{summary_row['최종고장양상_결정규칙_ko']}` 를 그대로 적용한 결과이고, downstream fault-panel event audit row 설명 근거로 쓴다.",
        "",
        "## 3. 지금 가장 안전한 판정",
        f"- {continuity_sentence}",
        f"- 하지만 현재 사건유형 결정은 heuristic continuity wording 이 아니라 stored-field rule 기준으로 `{summary_row['사건유형_결정_ko']}` 이다.",
        f"- 최종고장양상도 stored-field rule 기준 `{summary_row['최종고장양상_결정_ko']}` 으로 둔다.",
        f"- coarse timing 판정은 `{summary_row['사건시간양상_판정_ko']}` 이고, 확정도는 `{summary_row['확정도_판정_ko']}` 이다.",
        "",
        "## 4. 왜 보정이 필요한지",
        f"- 현재 표 보정 필요 여부는 `{correction_need}` 이다.",
        f"- pretrigger window `{range_text(summary_row['earliest_warning_date'] or summary_row['earliest_onset_date'], summary_row['strong_trigger_date'])}` 주변에서 precursor-like activity 가 누적되었는지, 아니면 고립된 warning 인지 분리해서 읽어야 한다.",
        "- 이 파일은 이제 pending-fix detector가 아니라, 현재 panel row와 fault-panel event audit row가 왜 그렇게 읽히는지 설명하는 forensic/explanatory note다.",
        "- 그래서 이 패널은 event type, terminal pattern, evaluation-set inclusion 을 분리해 읽는 주석이 계속 필요하다.",
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
    fault_audit_df = read_csv(share_dir / FAULT_PANEL_EVENT_AUDIT_NAME, required=False)
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
    fault_audit_row_df = exact_panel_rows(fault_audit_df, TARGET_PANEL_ID, TARGET_SITE) if not fault_audit_df.empty else pd.DataFrame()

    vendor_row_df = exact_panel_rows(vendor_df, TARGET_PANEL_ID, TARGET_SITE) if not vendor_df.empty else pd.DataFrame()
    precursor_row_df = exact_panel_rows(precursor_truth_df, TARGET_PANEL_ID, TARGET_SITE) if not precursor_truth_df.empty else pd.DataFrame()

    reaudit_row = reaudit_row_df.iloc[0]
    nonprec_row = nonprec_row_df.iloc[0]
    panel_table_row = panel_table_row_df.iloc[0]
    fault_audit_row = fault_audit_row_df.iloc[0] if not fault_audit_row_df.empty else None
    vendor_row = vendor_row_df.iloc[0] if not vendor_row_df.empty else None
    evidence_row = vendor_row if vendor_row is not None else reaudit_row

    core_panel = core_df.loc[core_df["panel_id"].astype(str).eq(TARGET_PANEL_ID)].copy()
    gate_panel = gate_df.loc[gate_df["panel_id"].astype(str).eq(TARGET_PANEL_ID)].copy()
    if core_panel.empty or gate_panel.empty:
        raise RuntimeError("Target panel is missing from daily core/helper outputs.")
    core_panel["date"] = pd.to_datetime(core_panel["date"], errors="coerce")
    gate_panel["date"] = pd.to_datetime(gate_panel["date"], errors="coerce")

    original_label = recover_original_kernel_label(root)
    rule_decision = determine_rule_based_event_decision(
        reaudit_row=reaudit_row,
        nonprec_row=nonprec_row,
        core_df=core_panel,
    )

    first_warning = to_timestamp(reaudit_row.get("first_warning_date"))
    retrospective_onset = to_timestamp(reaudit_row.get("retrospective_onset_date"))
    continuity = build_continuity_assessment(
        reaudit_row=reaudit_row,
        precursor_truth_df=precursor_row_df,
        core_df=core_panel,
        gate_df=gate_panel,
    )
    strong_trigger = continuity.strong_trigger_date
    earliest_local_warning = earliest_true_date(gate_panel, "ews_warning")
    official_start, _ = window_range(first_warning, retrospective_onset)
    start_for_lead = continuity.pretrigger_start_date or official_start or earliest_local_warning
    lead_days = continuity.effective_lead_days

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
    current_panel_type = str(panel_table_row.get("사건유형_ko", "")).strip()
    current_panel_terminal = str(panel_table_row.get("최종고장양상_ko", "")).strip()
    authoritative_event_type = str(fault_audit_row.get("사건유형_재판정_ko", rule_decision.event_type_ko)).strip() if fault_audit_row is not None else rule_decision.event_type_ko
    authoritative_terminal = str(fault_audit_row.get("최종고장양상_재판정_ko", rule_decision.terminal_pattern_ko)).strip() if fault_audit_row is not None else rule_decision.terminal_pattern_ko
    correction_needed = int(
        authoritative_event_type != current_panel_type
        or authoritative_terminal != current_panel_terminal
    )
    continuity_reason = (
        f"pretrigger {continuity.pretrigger_window_day_count}일 동안 "
        f"AE {continuity.ae_active_days_pretrigger}일, DTW {continuity.dtw_active_days_pretrigger}일, "
        f"cond_evt {continuity.cond_evt_days_pretrigger}일, 마지막 gap {continuity.last_gap_before_trigger_days}일"
    )
    one_line = (
        f"원래 stored kernel wording은 `{original_label.label_ko}` 이고 현재 재감사는 `{current_reaudit_label}` 이다. "
        f"explicit stored-field rule 기준 사건유형은 `{rule_decision.event_type_ko}` 이고 최종고장양상은 `{rule_decision.terminal_pattern_ko}` 이다. "
        f"현재 downstream authoritative row는 `{authoritative_event_type}` / `{authoritative_terminal}` 이다."
    )
    next_step = (
        f"사건유형은 `{authoritative_event_type}`, 최종고장양상은 `{authoritative_terminal}` 으로 읽고, "
        "evaluation-set 편입 여부와는 별도로 관리한다. 이 forensic pack은 그 설명 근거를 남긴다."
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
        "earliest_warning_date": format_date(continuity.earliest_warning_date),
        "earliest_onset_date": format_date(continuity.earliest_onset_date),
        "strong_trigger_date": format_date(continuity.strong_trigger_date),
        "days_between_onset_and_trigger": continuity.days_between_onset_and_trigger if continuity.days_between_onset_and_trigger is not None else "",
        "pretrigger_window_day_count": continuity.pretrigger_window_day_count,
        "ae_active_days_pretrigger": continuity.ae_active_days_pretrigger,
        "dtw_active_days_pretrigger": continuity.dtw_active_days_pretrigger,
        "hs_active_days_pretrigger": continuity.hs_active_days_pretrigger,
        "cond_evt_days_pretrigger": continuity.cond_evt_days_pretrigger,
        "pre_alarm_days_pretrigger": continuity.pre_alarm_days_pretrigger,
        "final_fault_days_pretrigger": continuity.final_fault_days_pretrigger,
        "longest_consecutive_active_run_days": continuity.longest_consecutive_active_run_days,
        "longest_consecutive_cond_evt_run_days": continuity.longest_consecutive_cond_evt_run_days,
        "last_gap_before_trigger_days": continuity.last_gap_before_trigger_days if continuity.last_gap_before_trigger_days is not None else "",
        "continuity_judgment_ko": continuity.continuity_judgment_ko,
        "event_recommendation_ko": continuity.event_recommendation_ko,
        "사건유형_결정규칙_ko": rule_decision.event_rule_ko,
        "최종고장양상_결정규칙_ko": rule_decision.terminal_rule_ko,
        "사건유형_결정_ko": rule_decision.event_type_ko,
        "최종고장양상_결정_ko": rule_decision.terminal_pattern_ko,
        "사건시간양상_판정_ko": event_timing,
        "확정도_판정_ko": certainty,
        "현재표_보정필요여부_flag": correction_needed,
        "핵심판정_한줄요약_ko": one_line,
        "다음보정권고_ko": f"{next_step} ({continuity_reason})",
    }

    timeline_rows = build_timeline_rows(
        reaudit_row=reaudit_row,
        vendor_row=vendor_row,
        nonprec_row=nonprec_row,
        core_df=core_panel,
        gate_df=gate_panel,
        continuity=continuity,
        rule_decision=rule_decision,
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
