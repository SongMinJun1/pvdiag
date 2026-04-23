#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


RUNTIME_AUDIT_OUTPUT_NAME = "panel_day_engine_runtime_fault_event_audit_v1.csv"
RUNTIME_AUDIT_SUMMARY_NAME = "panel_day_engine_runtime_fault_event_audit_summary_v1.csv"
RUNTIME_VERDICT_OUTPUT_NAME = "panel_day_engine_runtime_final_verdict_v1.csv"
RUNTIME_VERDICT_SUMMARY_NAME = "panel_day_engine_runtime_final_verdict_summary_v1.csv"
RUNTIME_HEURISTIC_OUTPUT_NAME = "panel_day_engine_runtime_cause_candidate_heuristics_v1.csv"
RUNTIME_HEURISTIC_SUMMARY_NAME = "panel_day_engine_runtime_cause_candidate_summary_v1.csv"

RUNTIME_FAULT_OUTPUT_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
    "1순위_의심원인_ko",
    "2순위_의심원인_ko",
    "3순위_의심원인_ko",
]
RUNTIME_PREVIEW_OUTPUT_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
    "1순위_의심원인_ko",
    "2순위_의심원인_ko",
    "3순위_의심원인_ko",
    "커널로그 기존 알고리즘",
]

DISPLAY_HEURISTIC_NAME_MAP = {
    "다이오드·서브스트링형": "다이오드·국소 회로 이상형",
    "접속·부분개방형": "접촉 끊김 형",
    "센서·피드백형": "장치 측정 이상형",
    "제어응답형": "장치 응답 이상형",
    "전력변환부형": "전력변환부 이상형",
    "외부계통교란형": "외부 전원 흔들림형",
}

PRIMARY_WARNING_COLS = [
    "ews_warning",
    "pre_alarm",
]
SECONDARY_WARNING_COLS = [
    "pre_ews",
    "prefault_B",
    "prefault_cond_mid",
    "prefault_cond_ae",
    "prefault_cond_dtw",
    "prefault_cond_ews",
    "prealarm_cond_ae_mid_or_hi",
    "prealarm_cond_dtw_mid_or_hi",
    "prealarm_cond_hs_mid_or_hi",
]
ALL_WARNING_COLS = PRIMARY_WARNING_COLS + SECONDARY_WARNING_COLS
PRIMARY_WARNING_MAX_GAP_DAYS = 120
SECONDARY_WARNING_MIN_GAP_DAYS = 7
SECONDARY_WARNING_MAX_GAP_DAYS = 120
PREFERRED_PREFAULT_B_WARNING_COLS = ["prefault_B_effective", "prefault_B"]
PROXIMAL_COMMON_CAUSE_WINDOW_DAYS = 3
DEGRADATION_ONSET_BACKDATE_GUARD_NAME = "G1_extreme_longgap_one_day"
DEGRADATION_ONSET_BACKDATE_GUARD_MIN_GAP_DAYS = 30
DEGRADATION_ONSET_BACKDATE_GUARD_MAX_DEGRADE_DAYS = 1
PROMOTION_DECISION_ONSET_SIGNAL_COLS = [
    "signal_count",
    "pre_ews",
    "ews_warning",
    "pre_alarm",
]
PROMOTION_DECISION_ONSET_SIGNAL_LOOKAHEAD_DAYS = 10


@dataclass(frozen=True)
class PanelRuntimeMetrics:
    site: str
    panel_id: str
    earliest_warning_date: str
    earliest_warning_marker: str
    retrospective_onset_date: str
    strict_trigger_date: str
    first_final_fault_date: str
    dead_diag_date: str
    onset_confidence: str
    onset_method: str
    패널고장여부_ko: str
    전조흔적_flag: int
    순수급작_flag: int
    전조평가셋편입_flag: int
    급작평가셋편입_flag: int
    사건유형_재판정_ko: str
    최종고장양상_재판정_ko: str
    재판정_근거_ko: str
    현재표_보정필요여부_flag: int
    대표critical_source: str
    대표anom_level: str
    대표anom_subtype: str
    algorithm_family_ko: str
    algorithm_symptom_ko: str
    detailed_fault_code: str
    detailed_fault_label_ko: str
    gap_days: int
    degradation_onset_backdate_guard_flag: bool
    degradation_onset_backdate_guard_name: str
    degradation_onset_backdate_guard_reason: str
    degradation_onset_backdate_guard_degrade_days: int
    g1_suppressed_event_shadow_flag: bool
    g1_suppressed_event_shadow_rule_name: str
    g1_suppressed_event_shadow_current_onset_date: str
    g1_suppressed_event_shadow_strict_trigger_date: str
    g1_suppressed_event_shadow_current_event_type_ko: str
    g1_suppressed_event_shadow_current_final_pattern_ko: str
    g1_suppressed_event_shadow_event_type_if_applied_ko: str
    g1_suppressed_event_shadow_final_pattern_if_applied_ko: str
    g1_suppressed_event_shadow_transition_class: str
    g1_suppressed_event_shadow_reason: str
    g1_suppressed_event_guard_applied_flag: bool
    g1_suppressed_event_guard_apply_reason: str
    secondary_window_candidate_flag: bool
    secondary_window_selected_onset_date: str
    secondary_window_selected_marker: str
    secondary_window_selected_gap_days: int
    secondary_window_qualified_count: int
    secondary_window_too_early_count: int
    secondary_window_change_class: str
    secondary_window_review_tier: str
    secondary_window_reason: str
    promotion_decision_bucket: str
    promotion_decision_reason: str
    common_cause_anchor_date: str
    common_cause_anchor_kind: str
    has_final_fault: bool
    has_critical_fault: bool
    has_fault_like: bool
    has_degradation: bool
    has_shadow: bool
    has_vdrop: bool
    has_site_event: bool
    has_group_off: bool
    has_subgroup_common_cause: bool
    has_common_cause_history: bool
    has_strict_trigger_proximal_common_cause: bool
    has_warning_proximal_common_cause: bool
    has_trigger_proximal_common_cause: bool


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def truthy_mask(series: pd.Series) -> pd.Series:
    lowered = series.astype(str).str.strip().str.lower()
    return lowered.isin({"1", "true", "t", "yes"})


def read_csv(path: Path, required: bool = True) -> pd.DataFrame:
    if not path.exists():
        if required:
            raise SystemExit(f"missing input: {path}")
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def to_timestamp(value: object) -> pd.Timestamp | None:
    if pd.isna(value):
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    return ts.normalize()


def format_date(value: object) -> str:
    ts = to_timestamp(value)
    return "" if ts is None else ts.strftime("%Y-%m-%d")


def min_ts(values: list[pd.Timestamp | None]) -> pd.Timestamp | None:
    parsed = [value for value in values if value is not None]
    return min(parsed) if parsed else None


def first_true_date(df: pd.DataFrame, column: str) -> pd.Timestamp | None:
    if df.empty or column not in df.columns or "date" not in df.columns:
        return None
    working = df.loc[truthy_mask(df[column]), "date"]
    if working.empty:
        return None
    ts = pd.to_datetime(working, errors="coerce").dropna()
    return None if ts.empty else ts.min().normalize()


def true_date_set(df: pd.DataFrame, columns: list[str]) -> set[pd.Timestamp]:
    if df.empty or "date" not in df.columns:
        return set()
    dates: set[pd.Timestamp] = set()
    for column in columns:
        if column not in df.columns:
            continue
        working = pd.to_datetime(df.loc[truthy_mask(df[column]), "date"], errors="coerce").dropna()
        dates.update(pd.Timestamp(ts).normalize() for ts in working.tolist())
    return dates


def first_true_marker(df: pd.DataFrame, columns: list[str]) -> tuple[pd.Timestamp | None, str]:
    candidates: list[tuple[pd.Timestamp, str]] = []
    for column in columns:
        ts = first_true_date(df, column)
        if ts is not None:
            candidates.append((ts, column))
    if not candidates:
        return None, ""
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0]


def true_marker_candidates(df: pd.DataFrame, columns: list[str]) -> list[tuple[pd.Timestamp, str]]:
    candidates: list[tuple[pd.Timestamp, str]] = []
    if df.empty or "date" not in df.columns:
        return candidates
    for column in dict.fromkeys(columns):
        if column not in df.columns:
            continue
        dates = pd.to_datetime(df.loc[truthy_mask(df[column]), "date"], errors="coerce").dropna()
        candidates.extend((pd.Timestamp(ts).normalize(), column) for ts in dates.tolist())
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates


def first_true_marker_in_gap_window(
    df: pd.DataFrame,
    columns: list[str],
    strict_trigger: pd.Timestamp | None,
    min_gap_days: int,
    max_gap_days: int,
) -> tuple[pd.Timestamp | None, str, int, int, int]:
    if strict_trigger is None:
        return None, "", 0, 0, 0

    qualified: list[tuple[pd.Timestamp, str, int]] = []
    too_early_count = 0
    for ts, marker in true_marker_candidates(df, columns):
        if ts >= strict_trigger:
            continue
        gap_days = int((strict_trigger - ts).days)
        if min_gap_days <= gap_days <= max_gap_days:
            qualified.append((ts, marker, gap_days))
        elif gap_days > max_gap_days:
            too_early_count += 1

    if not qualified:
        return None, "", 0, 0, too_early_count
    qualified.sort(key=lambda item: (item[0], item[1]))
    selected_ts, selected_marker, selected_gap = qualified[0]
    return selected_ts, selected_marker, selected_gap, len(qualified), too_early_count


def resolve_secondary_window_warning_cols(df: pd.DataFrame) -> list[str]:
    prefault_col = next(
        (column for column in PREFERRED_PREFAULT_B_WARNING_COLS if column in df.columns),
        "prefault_B",
    )
    secondary_cols = [column for column in SECONDARY_WARNING_COLS if column != "prefault_B"]
    return list(dict.fromkeys(["pre_ews", prefault_col, *secondary_cols]))


def discover_sites(root: Path) -> list[str]:
    data_root = root / "data"
    if not data_root.exists():
        raise SystemExit(f"missing data root: {data_root}")
    sites = sorted(
        path.name
        for path in data_root.iterdir()
        if path.is_dir() and (path / "out" / "panel_day_core.csv").exists()
    )
    if not sites:
        raise SystemExit(f"no site outputs found under: {data_root}")
    return sites


def load_site_outputs(root: Path, site: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    out_dir = root / "data" / site / "out"
    core_path = out_dir / "panel_day_core.csv"
    gate_path = out_dir / "ae_simple_local_precursor_gate_daily.csv"
    core_df = read_csv(core_path)
    ensure_columns(
        core_df,
        [
            "date",
            "panel_id",
            "critical_source",
            "final_fault",
            "critical_fault",
            "fault_like_day",
            "anom_level",
            "anom_subtype",
        ],
        core_path.name,
    )
    core_df["date"] = pd.to_datetime(core_df["date"], errors="coerce")
    core_df["panel_id"] = core_df["panel_id"].astype(str)
    gate_df = read_csv(gate_path, required=False)
    if not gate_df.empty:
        ensure_columns(gate_df, ["date", "panel_id"], gate_path.name)
        gate_df["date"] = pd.to_datetime(gate_df["date"], errors="coerce")
        gate_df["panel_id"] = gate_df["panel_id"].astype(str)
    return core_df, gate_df


def panel_keys(core_df: pd.DataFrame, gate_df: pd.DataFrame) -> list[str]:
    keys = set(core_df["panel_id"].astype(str).tolist())
    if not gate_df.empty and "panel_id" in gate_df.columns:
        keys.update(gate_df["panel_id"].astype(str).tolist())
    return sorted(key for key in keys if normalize_text(key))


def representative_row(panel_core: pd.DataFrame) -> pd.Series:
    final_rows = panel_core.loc[truthy_mask(panel_core["final_fault"])]
    critical_rows = panel_core.loc[truthy_mask(panel_core["critical_fault"])]
    fault_like_rows = panel_core.loc[truthy_mask(panel_core["fault_like_day"])]
    if not final_rows.empty:
        return final_rows.sort_values("date").iloc[0]
    if not critical_rows.empty:
        return critical_rows.sort_values("date").iloc[0]
    if not fault_like_rows.empty:
        return fault_like_rows.sort_values("date").iloc[0]
    return panel_core.sort_values("date").iloc[-1]


def subgroup_common_cause_date_set(panel_core: pd.DataFrame, panel_gate: pd.DataFrame) -> set[pd.Timestamp]:
    return true_date_set(panel_core, ["subgroup_common_cause_candidate"]) | true_date_set(
        panel_gate,
        ["subgroup_common_cause_candidate"],
    )


def panel_abnormal_date_set(panel_core: pd.DataFrame, panel_gate: pd.DataFrame) -> set[pd.Timestamp]:
    core_dates = true_date_set(
        panel_core,
        [
            "degraded_candidate",
            "fault_like_day",
            "critical_fault",
            "final_fault",
            "shadow_like",
            "group_off_like",
        ],
    )
    gate_dates = true_date_set(
        panel_gate,
        [
            "ews_warning",
            "pre_alarm",
            "pre_ews",
            "prefault_B",
            "prefault_B_effective",
            "prefault_B_common_cause_overlap",
        ],
    )
    return core_dates | gate_dates


def count_degradation_days_between(
    panel_core: pd.DataFrame,
    onset: pd.Timestamp | None,
    strict_trigger: pd.Timestamp | None,
) -> int:
    if onset is None or strict_trigger is None or panel_core.empty or "date" not in panel_core.columns:
        return 0

    dates = pd.to_datetime(panel_core["date"], errors="coerce")
    window_mask = dates.notna() & dates.ge(onset) & dates.le(strict_trigger)
    if not window_mask.any():
        return 0

    degrade_mask = pd.Series(False, index=panel_core.index)
    if "degraded_candidate" in panel_core.columns:
        degrade_mask = truthy_mask(panel_core["degraded_candidate"])
    subtype_mask = pd.Series(False, index=panel_core.index)
    if "anom_subtype" in panel_core.columns:
        subtype_mask = panel_core["anom_subtype"].astype(str).str.contains("degradation", case=False, na=False)

    matched_dates = dates.loc[window_mask & (degrade_mask | subtype_mask)].dt.normalize().dropna()
    return int(matched_dates.nunique())


def count_onset_window_signal_days(
    panel_gate: pd.DataFrame,
    onset: pd.Timestamp | None,
    strict_trigger: pd.Timestamp | None,
) -> int:
    if onset is None or strict_trigger is None or panel_gate.empty or "date" not in panel_gate.columns:
        return 0

    dates = pd.to_datetime(panel_gate["date"], errors="coerce")
    window_end = min(strict_trigger, onset + pd.Timedelta(days=PROMOTION_DECISION_ONSET_SIGNAL_LOOKAHEAD_DAYS))
    window_mask = dates.notna() & dates.ge(onset) & dates.le(window_end)
    if not window_mask.any():
        return 0

    matched_dates: set[pd.Timestamp] = set()
    for column in PROMOTION_DECISION_ONSET_SIGNAL_COLS:
        if column not in panel_gate.columns:
            continue
        if column == "signal_count":
            signal_mask = pd.to_numeric(panel_gate[column], errors="coerce").fillna(0).gt(0)
        else:
            signal_mask = truthy_mask(panel_gate[column])
        signal_dates = dates.loc[window_mask & signal_mask].dt.normalize().dropna()
        matched_dates.update(pd.Timestamp(ts).normalize() for ts in signal_dates.tolist())
    return len(matched_dates)


def classify_promotion_decision_bucket(
    *,
    degradation_guard_flag: bool,
    secondary_window_change_class: str,
    secondary_window_review_tier: str,
    secondary_window_selected_marker: str,
    onset_window_signal_days: int,
) -> tuple[str, str]:
    if degradation_guard_flag:
        return (
            "backdate_suppression_candidate",
            "BR008: G1 degradation backdate guard candidate; shadow suppression review only",
        )

    if secondary_window_review_tier in {"audit_provenance_only", "audit_no_event_flip"}:
        return (
            "audit_provenance_only",
            f"BR008: {secondary_window_review_tier}; audit/provenance only and no event flip",
        )

    if secondary_window_change_class != "trigger_only_to_precursor":
        return "", ""

    if secondary_window_review_tier == "review_persistent_secondary_only":
        return (
            "blocked_cluster_risk",
            "BR008: persistent secondary-only candidate; blocked from promotion by cluster false-positive risk",
        )

    if secondary_window_review_tier == "review_supported_context":
        if secondary_window_selected_marker == "prealarm_cond_dtw_mid_or_hi" and onset_window_signal_days == 0:
            return (
                "hold_shadow_only",
                "BR008: supported context exists, but selected onset is DTW prealarm with zero independent onset-window signal",
            )
        return (
            "manual_review",
            "BR008: supported context requires raw/audit review before any operator-facing promotion",
        )

    if secondary_window_review_tier.startswith("review_"):
        return (
            "manual_review",
            "BR008: trigger-only precursor candidate lacks hard promotion support",
        )

    return "", ""


def first_available_anchor(
    strict_trigger: pd.Timestamp | None,
    earliest_warning: pd.Timestamp | None,
    retrospective_onset: pd.Timestamp | None,
) -> tuple[pd.Timestamp | None, str]:
    if strict_trigger is not None:
        return strict_trigger, "strict_trigger"
    if earliest_warning is not None:
        return earliest_warning, "earliest_warning"
    if retrospective_onset is not None:
        return retrospective_onset, "retrospective_onset"
    return None, ""


def choose_algorithm_family(
    representative_source: str,
    representative_subtype: str,
    event_type_ko: str,
    has_final_fault: bool,
    has_critical_fault: bool,
    has_degradation: bool,
    has_shadow: bool,
) -> tuple[str, str, str, str]:
    if event_type_ko != "전조형 고장" and event_type_ko != "급작 고장":
        return "", "", "", ""

    if has_degradation and event_type_ko == "전조형 고장" and not has_final_fault:
        return ("모듈손상형", "출력 저하형", "RAW_MODULE_PROGRESSIVE", "알고리즘상 진행성 열화 계열")
    if representative_source == "legacy":
        return ("개방/장치이상형", "전압 변화형", "RAW_OPEN_LEGACY", "알고리즘상 legacy/open 계열")
    if representative_source == "none" and has_final_fault and not has_critical_fault:
        return ("개방/장치이상형", "전압 변화형", "RAW_OPEN_NOCRIT", "확정고장이지만 vdrop/critical 증거가 약한 계열")
    if representative_source in {"vdrop", "vdrop_suspect"} or "vdrop" in representative_subtype:
        return ("다이오드형", "전압 변화형", "RAW_DIODE_VDROP", "알고리즘상 vdrop 계열")
    if has_shadow and event_type_ko == "전조형 고장":
        return ("모듈손상형", "출력 저하형", "RAW_MODULE_SHADOW", "그림자/열화 진행 계열")
    return ("불충분", "불충분", "RAW_UNCERTAIN", "raw-only family 신뢰도가 충분치 않음")


def compute_panel_metrics(
    site: str,
    panel_id: str,
    core_df: pd.DataFrame,
    gate_df: pd.DataFrame,
) -> PanelRuntimeMetrics:
    panel_core = core_df.loc[core_df["panel_id"].eq(panel_id)].copy().sort_values("date")
    if panel_core.empty:
        raise SystemExit(f"panel core rows must not be empty: {(site, panel_id)}")
    panel_gate = gate_df.loc[gate_df["panel_id"].eq(panel_id)].copy().sort_values("date") if not gate_df.empty else pd.DataFrame()

    first_final_fault = first_true_date(panel_core, "final_fault")
    first_critical_fault = first_true_date(panel_core, "critical_fault")
    first_fault_like = first_true_date(panel_core, "fault_like_day")
    strict_trigger = min_ts([first_critical_fault, first_final_fault, first_fault_like])
    first_primary_warning, first_primary_marker = first_true_marker(panel_gate, PRIMARY_WARNING_COLS)
    first_secondary_warning, first_secondary_marker = first_true_marker(panel_gate, SECONDARY_WARNING_COLS)
    (
        secondary_window_onset,
        secondary_window_marker,
        secondary_window_gap_days,
        secondary_window_qualified_count,
        secondary_window_too_early_count,
    ) = first_true_marker_in_gap_window(
        panel_gate,
        resolve_secondary_window_warning_cols(panel_gate),
        strict_trigger,
        SECONDARY_WARNING_MIN_GAP_DAYS,
        SECONDARY_WARNING_MAX_GAP_DAYS,
    )

    has_degradation = panel_core["anom_subtype"].astype(str).str.contains("degradation", case=False, na=False).any()
    has_shadow = panel_core["anom_subtype"].astype(str).str.contains("shadow", case=False, na=False).any()
    representative = representative_row(panel_core)
    representative_source = normalize_text(representative.get("critical_source"))
    representative_level = normalize_text(representative.get("anom_level"))
    representative_subtype = normalize_text(representative.get("anom_subtype"))
    has_vdrop = representative_source in {"vdrop", "vdrop_suspect"} or "vdrop" in representative_subtype
    abnormal_dates = panel_abnormal_date_set(panel_core, panel_gate)
    site_event_dates = true_date_set(panel_gate, ["site_event_soft", "site_event_hard"])
    site_event_overlap_dates = abnormal_dates & site_event_dates
    group_off_overlap_dates = abnormal_dates & (
        true_date_set(panel_core, ["group_off_date", "group_off_like"])
        | true_date_set(panel_gate, ["group_off_date", "group_off_like"])
    )
    has_group_off = (
        (not panel_gate.empty and first_true_date(panel_gate, "group_off_date") is not None)
        or panel_core["anom_level"].astype(str).str.contains("group_off", case=False, na=False).any()
    )
    subgroup_common_cause_dates = subgroup_common_cause_date_set(panel_core, panel_gate)
    has_site_event = bool(site_event_overlap_dates)
    has_subgroup_common_cause = bool(subgroup_common_cause_dates)
    common_cause_dates = site_event_overlap_dates | group_off_overlap_dates | subgroup_common_cause_dates
    has_common_cause_history = bool(common_cause_dates)

    earliest_warning = first_primary_warning
    earliest_marker = first_primary_marker
    if earliest_warning is None:
        earliest_warning = first_secondary_warning
        earliest_marker = first_secondary_marker

    retrospective_onset = None
    primary_gap_days = (
        (strict_trigger - first_primary_warning).days
        if strict_trigger is not None and first_primary_warning is not None
        else None
    )
    secondary_gap_days = (
        (strict_trigger - first_secondary_warning).days
        if strict_trigger is not None and first_secondary_warning is not None
        else None
    )
    primary_warning_accepted = (
        first_primary_warning is not None
        and strict_trigger is not None
        and first_primary_warning < strict_trigger
        and primary_gap_days is not None
        and primary_gap_days <= PRIMARY_WARNING_MAX_GAP_DAYS
    )
    if strict_trigger is not None:
        if primary_warning_accepted:
            retrospective_onset = first_primary_warning
        elif (
            first_secondary_warning is not None
            and first_secondary_warning < strict_trigger
            and secondary_gap_days is not None
            and SECONDARY_WARNING_MIN_GAP_DAYS <= secondary_gap_days <= SECONDARY_WARNING_MAX_GAP_DAYS
        ):
            retrospective_onset = first_secondary_warning
        elif has_degradation:
            degradation_rows = panel_core.loc[
                panel_core["anom_subtype"].astype(str).str.contains("degradation", case=False, na=False)
            ]
            if not degradation_rows.empty:
                degradation_ts = to_timestamp(degradation_rows.iloc[0]["date"])
                if degradation_ts is not None and degradation_ts <= strict_trigger:
                    retrospective_onset = degradation_ts
                    earliest_marker = "anom_subtype:degradation"

    has_final = first_final_fault is not None
    has_critical = first_critical_fault is not None
    has_fault_like = first_fault_like is not None

    if has_final or has_critical or has_fault_like:
        fault_status = "고장"
    elif earliest_warning is not None:
        fault_status = "미확정"
    else:
        fault_status = "비고장"

    gap_days = 0
    if retrospective_onset is not None and strict_trigger is not None:
        gap_days = max(int((strict_trigger - retrospective_onset).days), 0)

    degradation_guard_degrade_days = count_degradation_days_between(
        panel_core,
        retrospective_onset,
        strict_trigger,
    )
    degradation_guard_flag = (
        earliest_marker == "anom_subtype:degradation"
        and gap_days >= DEGRADATION_ONSET_BACKDATE_GUARD_MIN_GAP_DAYS
        and degradation_guard_degrade_days <= DEGRADATION_ONSET_BACKDATE_GUARD_MAX_DEGRADE_DAYS
    )
    degradation_guard_reason = ""
    if degradation_guard_flag:
        degradation_guard_reason = (
            f"{DEGRADATION_ONSET_BACKDATE_GUARD_NAME}: "
            f"onset_method=anom_subtype:degradation, gap_days>="
            f"{DEGRADATION_ONSET_BACKDATE_GUARD_MIN_GAP_DAYS}, "
            f"degrade_days_between_onset_and_strict<="
            f"{DEGRADATION_ONSET_BACKDATE_GUARD_MAX_DEGRADE_DAYS}"
        )

    common_cause_anchor_ts, common_cause_anchor_kind = first_available_anchor(
        strict_trigger,
        earliest_warning,
        retrospective_onset,
    )
    has_strict_trigger_proximal_common_cause = False
    has_warning_proximal_common_cause = False
    has_trigger_proximal_common_cause = False
    if common_cause_dates:
        if strict_trigger is not None:
            has_strict_trigger_proximal_common_cause = any(
                abs(int((date - strict_trigger).days)) <= PROXIMAL_COMMON_CAUSE_WINDOW_DAYS
                for date in common_cause_dates
            )
        if earliest_warning is not None:
            has_warning_proximal_common_cause = any(
                abs(int((date - earliest_warning).days)) <= PROXIMAL_COMMON_CAUSE_WINDOW_DAYS
                for date in common_cause_dates
            )
        if common_cause_anchor_ts is not None:
            has_trigger_proximal_common_cause = any(
                abs(int((date - common_cause_anchor_ts).days)) <= PROXIMAL_COMMON_CAUSE_WINDOW_DAYS
                for date in common_cause_dates
            )
    has_trigger_proximal_common_cause = (
        has_trigger_proximal_common_cause
        or has_strict_trigger_proximal_common_cause
        or has_warning_proximal_common_cause
    )

    precursor_flag = int(fault_status == "고장" and retrospective_onset is not None)
    abrupt_flag = int(fault_status == "고장" and not precursor_flag)
    precursor_eval_flag = precursor_flag
    abrupt_eval_flag = abrupt_flag

    if fault_status != "고장":
        event_type = ""
        terminal_pattern = ""
        onset_confidence = ""
        onset_method = ""
        current_needs_correction = 0
    elif precursor_flag:
        event_type = "전조형 고장"
        if has_degradation or not has_final or (has_vdrop and gap_days >= 7):
            terminal_pattern = "진행성 악화"
        else:
            terminal_pattern = "급격 종료"
        if gap_days >= 14:
            onset_confidence = "high"
        elif gap_days >= 3:
            onset_confidence = "medium"
        else:
            onset_confidence = "low"
        onset_method = earliest_marker or "runtime_precursor_gate"
        current_needs_correction = 1
    else:
        event_type = "급작 고장"
        terminal_pattern = "급작 발생"
        onset_confidence = "low"
        onset_method = "runtime_trigger_only"
        current_needs_correction = 0

    g1_shadow_flag = degradation_guard_flag and fault_status == "고장" and strict_trigger is not None
    g1_shadow_event_type = "급작 고장" if g1_shadow_flag else ""
    g1_shadow_final_pattern = "급작 발생" if g1_shadow_flag else ""
    g1_shadow_current_onset_date = format_date(retrospective_onset) if g1_shadow_flag else ""
    g1_shadow_current_event_type = event_type if g1_shadow_flag else ""
    g1_shadow_current_final_pattern = terminal_pattern if g1_shadow_flag else ""
    g1_shadow_transition_class = ""
    g1_shadow_reason = ""
    if g1_shadow_flag:
        g1_shadow_transition_class = f"{g1_shadow_current_event_type} -> {g1_shadow_event_type}"
        g1_shadow_reason = (
            "BR013: audit-only G1 suppressed-event shadow; suppress extreme long-gap "
            "one-day degradation onset while keeping strict trigger as event anchor"
        )

    secondary_window_candidate_flag = (
        strict_trigger is not None
        and not primary_warning_accepted
        and secondary_window_onset is not None
        and (
            format_date(secondary_window_onset) != format_date(retrospective_onset)
            or secondary_window_marker != onset_method
            or onset_method == "runtime_trigger_only"
        )
    )
    secondary_window_change_class = ""
    if secondary_window_candidate_flag:
        selected_onset_date = format_date(secondary_window_onset)
        current_onset_date = format_date(retrospective_onset)
        if (
            event_type == "전조형 고장"
            and selected_onset_date == current_onset_date
            and secondary_window_marker != onset_method
        ):
            secondary_window_change_class = "method_provenance_only_primary_marker_mismatch"
        elif onset_method == "anom_subtype:degradation":
            secondary_window_change_class = (
                "g1_degradation_fallback_replaced_by_secondary"
                if degradation_guard_flag
                else "degradation_fallback_replaced_by_secondary"
            )
        elif onset_method == "runtime_trigger_only" and fault_status == "고장":
            secondary_window_change_class = "trigger_only_to_precursor"
        elif event_type == "전조형 고장" and selected_onset_date != current_onset_date:
            secondary_window_change_class = "onset_date_shift_without_event_flip"
        else:
            secondary_window_change_class = "secondary_window_candidate"

    secondary_window_review_tier = ""
    if secondary_window_change_class == "trigger_only_to_precursor":
        if has_strict_trigger_proximal_common_cause or has_site_event or has_subgroup_common_cause:
            secondary_window_review_tier = "review_supported_context"
        elif secondary_window_qualified_count >= 30:
            secondary_window_review_tier = "review_persistent_secondary_only"
        else:
            secondary_window_review_tier = "review_sparse_secondary_only"
    elif secondary_window_change_class == "method_provenance_only_primary_marker_mismatch":
        secondary_window_review_tier = "audit_provenance_only"
    elif secondary_window_change_class:
        secondary_window_review_tier = "audit_no_event_flip"

    secondary_window_reason = ""
    if secondary_window_candidate_flag:
        secondary_window_reason = (
            "BR004_secondary_warning_window_shadow: "
            f"first_secondary_gap_days={secondary_gap_days if secondary_gap_days is not None else ''}, "
            f"selected_gap_days={secondary_window_gap_days}, "
            f"qualified_secondary_count={secondary_window_qualified_count}, "
            f"too_early_secondary_count={secondary_window_too_early_count}, "
            f"change_class={secondary_window_change_class}, "
            f"review_tier={secondary_window_review_tier}"
        )

    onset_window_signal_days = count_onset_window_signal_days(
        panel_gate,
        secondary_window_onset,
        strict_trigger,
    )
    promotion_decision_bucket, promotion_decision_reason = classify_promotion_decision_bucket(
        degradation_guard_flag=degradation_guard_flag,
        secondary_window_change_class=secondary_window_change_class,
        secondary_window_review_tier=secondary_window_review_tier,
        secondary_window_selected_marker=secondary_window_marker,
        onset_window_signal_days=onset_window_signal_days,
    )

    algorithm_family, algorithm_symptom, detailed_code, detailed_label = choose_algorithm_family(
        representative_source=representative_source,
        representative_subtype=representative_subtype,
        event_type_ko=event_type,
        has_final_fault=has_final,
        has_critical_fault=has_critical,
        has_degradation=has_degradation,
        has_shadow=has_shadow,
    )

    g1_guard_applied_flag = g1_shadow_flag and has_strict_trigger_proximal_common_cause
    g1_guard_apply_reason = ""
    if g1_guard_applied_flag:
        event_type = g1_shadow_event_type
        terminal_pattern = g1_shadow_final_pattern
        precursor_flag = 0
        abrupt_flag = 1
        precursor_eval_flag = 0
        abrupt_eval_flag = 1
        retrospective_onset = None
        earliest_warning = None
        earliest_marker = ""
        onset_method = "runtime_trigger_only"
        onset_confidence = "low"
        current_needs_correction = 0
        g1_guard_apply_reason = (
            "BR016: applied strict-proximal-supported G1 guard; "
            "one-day long-gap degradation onset suppressed from operator-facing event semantics"
        )

    evidence_bits: list[str] = []
    if earliest_marker:
        evidence_bits.append(f"warning={earliest_marker}")
    if representative_source:
        evidence_bits.append(f"critical_source={representative_source}")
    if representative_subtype:
        evidence_bits.append(f"anom_subtype={representative_subtype}")
    if g1_guard_applied_flag:
        evidence_bits.append(f"g1_suppressed_backdate_gap_days={gap_days}")
    elif gap_days:
        evidence_bits.append(f"precursor_gap_days={gap_days}")
    if has_group_off:
        evidence_bits.append("group_off_signal=1")
    if g1_guard_applied_flag:
        evidence_bits.append("g1_guard_applied=1")

    return PanelRuntimeMetrics(
        site=site,
        panel_id=panel_id,
        earliest_warning_date=format_date(earliest_warning),
        earliest_warning_marker=earliest_marker,
        retrospective_onset_date=format_date(retrospective_onset),
        strict_trigger_date=format_date(strict_trigger),
        first_final_fault_date=format_date(first_final_fault),
        dead_diag_date=format_date(first_true_date(panel_gate, "group_off_date")),
        onset_confidence=onset_confidence,
        onset_method=onset_method,
        패널고장여부_ko=fault_status,
        전조흔적_flag=precursor_flag,
        순수급작_flag=abrupt_flag,
        전조평가셋편입_flag=precursor_eval_flag,
        급작평가셋편입_flag=abrupt_eval_flag,
        사건유형_재판정_ko=event_type,
        최종고장양상_재판정_ko=terminal_pattern,
        재판정_근거_ko="; ".join(evidence_bits),
        현재표_보정필요여부_flag=current_needs_correction,
        대표critical_source=representative_source,
        대표anom_level=representative_level,
        대표anom_subtype=representative_subtype,
        algorithm_family_ko=algorithm_family,
        algorithm_symptom_ko=algorithm_symptom,
        detailed_fault_code=detailed_code,
        detailed_fault_label_ko=detailed_label,
        gap_days=gap_days,
        degradation_onset_backdate_guard_flag=degradation_guard_flag,
        degradation_onset_backdate_guard_name=(
            DEGRADATION_ONSET_BACKDATE_GUARD_NAME if degradation_guard_flag else ""
        ),
        degradation_onset_backdate_guard_reason=degradation_guard_reason,
        degradation_onset_backdate_guard_degrade_days=degradation_guard_degrade_days,
        g1_suppressed_event_shadow_flag=g1_shadow_flag,
        g1_suppressed_event_shadow_rule_name=(
            DEGRADATION_ONSET_BACKDATE_GUARD_NAME if g1_shadow_flag else ""
        ),
        g1_suppressed_event_shadow_current_onset_date=(
            g1_shadow_current_onset_date
        ),
        g1_suppressed_event_shadow_strict_trigger_date=(
            format_date(strict_trigger) if g1_shadow_flag else ""
        ),
        g1_suppressed_event_shadow_current_event_type_ko=g1_shadow_current_event_type,
        g1_suppressed_event_shadow_current_final_pattern_ko=(
            g1_shadow_current_final_pattern
        ),
        g1_suppressed_event_shadow_event_type_if_applied_ko=g1_shadow_event_type,
        g1_suppressed_event_shadow_final_pattern_if_applied_ko=g1_shadow_final_pattern,
        g1_suppressed_event_shadow_transition_class=g1_shadow_transition_class,
        g1_suppressed_event_shadow_reason=g1_shadow_reason,
        g1_suppressed_event_guard_applied_flag=g1_guard_applied_flag,
        g1_suppressed_event_guard_apply_reason=g1_guard_apply_reason,
        secondary_window_candidate_flag=secondary_window_candidate_flag,
        secondary_window_selected_onset_date=(
            format_date(secondary_window_onset) if secondary_window_candidate_flag else ""
        ),
        secondary_window_selected_marker=secondary_window_marker if secondary_window_candidate_flag else "",
        secondary_window_selected_gap_days=(
            secondary_window_gap_days if secondary_window_candidate_flag else 0
        ),
        secondary_window_qualified_count=secondary_window_qualified_count,
        secondary_window_too_early_count=secondary_window_too_early_count,
        secondary_window_change_class=secondary_window_change_class,
        secondary_window_review_tier=secondary_window_review_tier,
        secondary_window_reason=secondary_window_reason,
        promotion_decision_bucket=promotion_decision_bucket,
        promotion_decision_reason=promotion_decision_reason,
        common_cause_anchor_date=format_date(common_cause_anchor_ts),
        common_cause_anchor_kind=common_cause_anchor_kind,
        has_final_fault=has_final,
        has_critical_fault=has_critical,
        has_fault_like=has_fault_like,
        has_degradation=has_degradation,
        has_shadow=has_shadow,
        has_vdrop=has_vdrop,
        has_site_event=has_site_event,
        has_group_off=has_group_off,
        has_subgroup_common_cause=has_subgroup_common_cause,
        has_common_cause_history=has_common_cause_history,
        has_strict_trigger_proximal_common_cause=has_strict_trigger_proximal_common_cause,
        has_warning_proximal_common_cause=has_warning_proximal_common_cause,
        has_trigger_proximal_common_cause=has_trigger_proximal_common_cause,
    )


def display_heuristic_name(value: object) -> str:
    text = normalize_text(value)
    return DISPLAY_HEURISTIC_NAME_MAP.get(text, text)


def load_runtime_core_from_workspace(workspace_root: Path, site: str) -> pd.DataFrame:
    core_path = workspace_root / "data" / site / "out" / "panel_day_core.csv"
    core_df = read_csv(core_path)
    ensure_columns(
        core_df,
        ["panel_id", "date", "final_fault", "critical_fault", "fault_like_day", "critical_source"],
        core_path.name,
    )
    core_df["panel_id"] = core_df["panel_id"].astype(str)
    core_df["date"] = pd.to_datetime(core_df["date"], errors="coerce")
    return core_df


def representative_algorithm_fields(core_df: pd.DataFrame, panel_id: str) -> dict[str, str]:
    panel_df = core_df.loc[core_df["panel_id"].eq(str(panel_id))].copy().sort_values("date")
    if panel_df.empty:
        return {"커널로그 기존 알고리즘": ""}
    representative = representative_row(panel_df)
    return {"커널로그 기존 알고리즘": normalize_text(representative.get("critical_source"))}


def build_fault_table_from_outputs(
    workspace_root: Path,
    verdict_name: str,
    heuristic_name: str,
) -> pd.DataFrame:
    verdict_path = workspace_root / "_share" / verdict_name
    heuristic_path = workspace_root / "_share" / heuristic_name
    verdict_df = read_csv(verdict_path)
    heuristic_df = read_csv(heuristic_path)
    ensure_columns(
        verdict_df,
        ["site", "panel_id", "패널고장여부_ko", "사건유형_ko", "최종고장양상_ko", "커널로그_원인군_ko"],
        verdict_path.name,
    )
    ensure_columns(
        heuristic_df,
        ["site", "panel_id", "원인후보_top1_ko", "원인후보_top2_ko", "원인후보_top3_ko"],
        heuristic_path.name,
    )
    heuristic_lookup = {
        (normalize_text(row["site"]), normalize_text(row["panel_id"])): row
        for row in heuristic_df.to_dict(orient="records")
    }
    rows: list[dict[str, str]] = []
    fault_rows = verdict_df.loc[verdict_df["패널고장여부_ko"].map(normalize_text).eq("고장")].copy()
    for row in fault_rows.to_dict(orient="records"):
        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        heuristic_row = heuristic_lookup.get(key)
        if heuristic_row is None:
            raise SystemExit(f"missing heuristic row for runtime fault panel: {key}")
        rows.append(
            {
                "site": key[0],
                "panel_id": key[1],
                "패널고장여부_ko": normalize_text(row["패널고장여부_ko"]),
                "사건유형_ko": normalize_text(row["사건유형_ko"]),
                "최종고장양상_ko": normalize_text(row["최종고장양상_ko"]),
                "커널로그_원인군_ko": normalize_text(row["커널로그_원인군_ko"]),
                "1순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top1_ko"]),
                "2순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top2_ko"]),
                "3순위_의심원인_ko": display_heuristic_name(heuristic_row["원인후보_top3_ko"]),
            }
        )
    return pd.DataFrame(rows).reindex(columns=RUNTIME_FAULT_OUTPUT_COLS).sort_values(["site", "panel_id"]).reset_index(drop=True)


def build_fault_preview(workspace_root: Path, fault_df: pd.DataFrame) -> pd.DataFrame:
    per_site_core = {
        site: load_runtime_core_from_workspace(workspace_root, site)
        for site in sorted(fault_df["site"].astype(str).unique())
    }
    rows: list[dict[str, str]] = []
    for _, row in fault_df.iterrows():
        site = normalize_text(row["site"])
        panel_id = normalize_text(row["panel_id"])
        rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "패널고장여부_ko": normalize_text(row["패널고장여부_ko"]),
                "사건유형_ko": normalize_text(row["사건유형_ko"]),
                "최종고장양상_ko": normalize_text(row["최종고장양상_ko"]),
                "커널로그_원인군_ko": normalize_text(row["커널로그_원인군_ko"]),
                "1순위_의심원인_ko": normalize_text(row["1순위_의심원인_ko"]),
                "2순위_의심원인_ko": normalize_text(row["2순위_의심원인_ko"]),
                "3순위_의심원인_ko": normalize_text(row["3순위_의심원인_ko"]),
                **representative_algorithm_fields(per_site_core[site], panel_id),
            }
        )
    return pd.DataFrame(rows).reindex(columns=RUNTIME_PREVIEW_OUTPUT_COLS)


def compare_fault_table_to_reference(fault_df: pd.DataFrame, reference_path: Path) -> dict[str, object]:
    payload = {
        "reference_path": str(reference_path),
        "reference_available": reference_path.exists(),
        "exact_match": False,
        "row_key_match": False,
        "decision_columns_match": False,
        "overlap_decision_columns_match": False,
        "overlap_exact_match": False,
        "reference_row_count": 0,
        "candidate_row_count": int(len(fault_df)),
        "matched_row_key_count": 0,
        "diff_columns": [],
        "overlap_diff_columns": [],
    }
    if not reference_path.exists():
        return payload
    reference_df = read_csv(reference_path).sort_values(["site", "panel_id"]).reset_index(drop=True)
    candidate_df = fault_df.sort_values(["site", "panel_id"]).reset_index(drop=True)
    reference_keys = list(zip(reference_df["site"].astype(str), reference_df["panel_id"].astype(str)))
    candidate_keys = list(zip(candidate_df["site"].astype(str), candidate_df["panel_id"].astype(str)))
    payload["reference_row_count"] = int(len(reference_df))
    payload["candidate_row_count"] = int(len(candidate_df))
    payload["row_key_match"] = reference_keys == candidate_keys
    payload["matched_row_key_count"] = int(len(set(reference_keys) & set(candidate_keys)))
    diff_columns: list[str] = []
    if len(reference_df) != len(candidate_df):
        diff_columns.append("__row_count__")
    else:
        for column in RUNTIME_FAULT_OUTPUT_COLS:
            if column not in reference_df.columns:
                diff_columns.append(f"missing_reference:{column}")
                continue
            left = reference_df[column].fillna("").astype(str)
            right = candidate_df[column].fillna("").astype(str)
            if not left.equals(right):
                diff_columns.append(column)
    payload["diff_columns"] = diff_columns
    payload["exact_match"] = not diff_columns and payload["row_key_match"]
    decision_columns = ["패널고장여부_ko", "사건유형_ko", "최종고장양상_ko"]
    payload["decision_columns_match"] = payload["row_key_match"] and not any(
        column in diff_columns for column in decision_columns
    )
    overlap = reference_df.merge(candidate_df, on=["site", "panel_id"], how="inner", suffixes=("_reference", "_candidate"))
    overlap_diff_columns: list[str] = []
    if not overlap.empty:
        for column in RUNTIME_FAULT_OUTPUT_COLS[2:]:
            left = overlap[f"{column}_reference"].fillna("").astype(str)
            right = overlap[f"{column}_candidate"].fillna("").astype(str)
            if not left.equals(right):
                overlap_diff_columns.append(column)
    payload["overlap_diff_columns"] = overlap_diff_columns
    payload["overlap_exact_match"] = payload["matched_row_key_count"] == payload["reference_row_count"] and not overlap_diff_columns
    payload["overlap_decision_columns_match"] = payload["matched_row_key_count"] == payload["reference_row_count"] and not any(
        column in overlap_diff_columns for column in decision_columns
    )
    if payload["exact_match"]:
        payload["status_ko"] = "fixed fault reference exact match"
    elif payload["overlap_decision_columns_match"]:
        payload["status_ko"] = "overlap decision columns preserved and raw-only candidate universe expanded by design"
    elif payload["matched_row_key_count"] > 0:
        payload["status_ko"] = "overlap exists but decision drift detected"
    else:
        payload["status_ko"] = "no overlapping fixed reference keys"
    return payload
