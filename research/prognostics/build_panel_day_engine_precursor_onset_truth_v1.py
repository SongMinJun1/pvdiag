#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

FAULT_TAXONOMY_NAME = "panel_day_engine_fault_taxonomy_v1.csv"
ELIGIBILITY_CASES_NAME = "panel_day_engine_local_precursor_eligibility_cases_v1.csv"
REAUDIT_NAME = "panel_date_reaudit_working.csv"
FAULT_PANEL_EVENT_AUDIT_NAME = "panel_day_engine_fault_panel_event_audit_v1.csv"
FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME = "panel_day_engine_fault_panel_event_audit_summary_v1.csv"
FORENSIC_SUMMARY_NAME = "panel_day_engine_c42997_1_1_forensic_summary_v1.csv"
GATE_DAILY_NAME = "ae_simple_local_precursor_gate_daily.csv"
PANEL_DAY_CORE_NAME = "panel_day_core.csv"

ONSET_TRUTH_OUTPUT_NAME = "panel_day_engine_precursor_onset_truth_v1.csv"
ONSET_LADDER_OUTPUT_NAME = "panel_day_engine_precursor_onset_ladder_v1.csv"
ONSET_SUMMARY_OUTPUT_NAME = "panel_day_engine_precursor_onset_summary_v1.csv"

WINDOW_DAYS = 30
EPISODE_GAP_TOLERANCE_DAYS = 1

CASE_OUTPUT_COLS = [
    "site",
    "panel_id",
    "fault_start_date",
    "vendor_fault_family",
    "temporality_class",
    "bounded_window_start",
    "first_cond_evt_date",
    "first_cond_evt_corroborated_date",
    "first_signalcount2_date",
    "first_pre_ews_date",
    "first_ews_warning_date",
    "first_pre_alarm_date",
    "selected_episode_start_date",
    "selected_episode_end_date",
    "selected_episode_day_count",
    "preferred_precursor_onset_date",
    "preferred_onset_stage",
    "preferred_onset_confidence",
    "lead_days_from_preferred_onset_to_fault_start",
    "onset_reason_ko",
    "operational_first_precursor_detected_date",
    "operational_first_precursor_marker_name",
    "operational_lead_days_to_fault_start",
    "interpretive_precursor_onset_date",
    "interpretive_lead_days_to_fault_start",
    "benchmark_precursor_onset_date",
    "benchmark_lead_days_to_fault_start",
]

LADDER_OUTPUT_COLS = [
    "site",
    "panel_id",
    "fault_start_date",
    "onset_marker",
    "onset_date",
    "lead_days",
    "available_flag",
]

SUMMARY_OUTPUT_COLS = [
    "summary_type",
    "marker_name",
    "distribution_value",
    "case_count",
    "available_case_count",
    "available_rate",
    "median_lead_days",
    "min_lead_days",
    "max_lead_days",
]

MARKER_SPECS = [
    ("first_cond_evt", "first_cond_evt_date"),
    ("first_cond_evt_corroborated", "first_cond_evt_corroborated_date"),
    ("first_signalcount2", "first_signalcount2_date"),
    ("first_pre_ews", "first_pre_ews_date"),
    ("first_ews_warning", "first_ews_warning_date"),
    ("first_pre_alarm", "first_pre_alarm_date"),
    ("preferred_precursor_onset", "preferred_precursor_onset_date"),
]

OPERATIONAL_MARKER_SPECS = MARKER_SPECS[:-1]

GATE_REQUIRED_COLS = [
    "panel_id",
    "date",
    "cond_var",
    "cond_evt",
    "cond_dtw",
    "cond_hs",
    "pre_ews",
    "signal_count",
    "ews_warning",
    "pre_alarm",
]

CORE_REQUIRED_COLS = ["panel_id", "date"]

ELIGIBILITY_REQUIRED_COLS = [
    "site",
    "panel_id",
    "fault_start_date",
    "vendor_fault_family",
    "temporality_class",
    "precursor_eligible_flag",
]

TAXONOMY_REQUIRED_COLS = ["recommended_eval_bucket"]
REAUDIT_REQUIRED_COLS = ["site", "panel_id", "vendor_fault_family", "retrospective_onset_date"]
FAULT_PANEL_EVENT_AUDIT_REQUIRED_COLS = ["site", "panel_id", "strict_trigger_date", "사건유형_재판정_ko"]
FAULT_PANEL_EVENT_AUDIT_SUMMARY_REQUIRED_COLS = ["사건유형_재판정_전조형수"]
FORENSIC_REQUIRED_COLS = ["site", "panel_id", "사건유형_결정_ko", "최종고장양상_결정_ko"]

FORENSIC_HOLDOUT_SITE = "conalog"
FORENSIC_HOLDOUT_PANEL_ID = "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"
EXPECTED_PRECURSOR_BENCHMARK_SUPPORT = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build precursor onset truth and an onset ladder for precursor-bearing local cases only."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the project root.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def normalize_date_text(value: object) -> str:
    text = normalize_text(value)
    return text[:10] if len(text) >= 10 else text


def to_int_flag(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"", "0", "0.0", "false", "f", "no", "n"}:
        return 0
    if text in {"1", "1.0", "true", "t", "yes", "y"}:
        return 1
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return int(bool(numeric)) if not pd.isna(numeric) else 0


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def drop_repeated_header_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    header_mask = pd.Series(True, index=df.index)
    for col in df.columns:
        header_mask &= df[col].map(normalize_text).eq(col)
    return df.loc[~header_mask].reset_index(drop=True)


def parse_timestamp(value: object) -> pd.Timestamp | pd.NaT:
    text = normalize_date_text(value)
    if not text:
        return pd.NaT
    return pd.to_datetime(text, errors="coerce")


def read_site_subset_csv(
    path: Path,
    *,
    requested_cols: list[str],
    panels: set[str],
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
    site: str | None = None,
) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")

    chunks: list[pd.DataFrame] = []
    usecols = lambda col: col in requested_cols or (site is not None and col == "site")
    for chunk in pd.read_csv(
        path,
        usecols=usecols,
        chunksize=100_000,
        low_memory=False,
        encoding="utf-8-sig",
    ):
        chunk = drop_repeated_header_rows(chunk)
        if chunk.empty:
            continue
        if "site" not in chunk.columns and site is not None:
            chunk["site"] = site
        if "panel_id" in chunk.columns:
            chunk["panel_id"] = chunk["panel_id"].map(normalize_text)
            chunk = chunk.loc[chunk["panel_id"].isin(panels)].copy()
        if chunk.empty:
            continue
        if "date" in chunk.columns:
            chunk["date"] = chunk["date"].map(parse_timestamp)
            chunk = chunk.loc[chunk["date"].notna()].copy()
            chunk = chunk.loc[chunk["date"].ge(window_start) & chunk["date"].lt(window_end)].copy()
        if chunk.empty:
            continue
        chunks.append(chunk)

    output_cols = [col for col in requested_cols if col in (chunks[0].columns if chunks else requested_cols)]
    if site is not None and "site" not in output_cols:
        output_cols = ["site", *output_cols]
    if not chunks:
        return pd.DataFrame(columns=output_cols)
    return pd.concat(chunks, ignore_index=True)


def format_date(value: pd.Timestamp | pd.NaT) -> str:
    if pd.isna(value):
        return ""
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def lead_days_between(start_date: pd.Timestamp | pd.NaT, end_date: pd.Timestamp | pd.NaT) -> int | None:
    if pd.isna(start_date) or pd.isna(end_date):
        return None
    return int((pd.Timestamp(end_date) - pd.Timestamp(start_date)).days)


def derive_operational_first_detection(marker_dates: dict[str, pd.Timestamp | pd.NaT]) -> tuple[pd.Timestamp | pd.NaT, str]:
    candidates: list[tuple[pd.Timestamp, int, str]] = []
    for order_idx, (marker_name, _) in enumerate(OPERATIONAL_MARKER_SPECS):
        marker_date = marker_dates.get(marker_name, pd.NaT)
        if pd.isna(marker_date):
            continue
        candidates.append((pd.Timestamp(marker_date), order_idx, marker_name))
    if not candidates:
        return (pd.NaT, "")
    candidates.sort(key=lambda item: (item[0], item[1]))
    chosen_date, _, chosen_marker = candidates[0]
    return (chosen_date, chosen_marker)


def validate_taxonomy(root: Path) -> None:
    path = root / "_share" / FAULT_TAXONOMY_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, TAXONOMY_REQUIRED_COLS, path.name)
    bucket_values = set(df["recommended_eval_bucket"].map(normalize_text))
    if "precursor_bearing" not in bucket_values:
        raise SystemExit("fault taxonomy does not define a precursor_bearing bucket")


def load_precursor_cases(root: Path) -> pd.DataFrame:
    share_dir = root / "_share"

    fault_audit_df = drop_repeated_header_rows(read_csv(share_dir / FAULT_PANEL_EVENT_AUDIT_NAME))
    ensure_columns(fault_audit_df, FAULT_PANEL_EVENT_AUDIT_REQUIRED_COLS, FAULT_PANEL_EVENT_AUDIT_NAME)
    fault_audit_df["site"] = fault_audit_df["site"].map(normalize_text)
    fault_audit_df["panel_id"] = fault_audit_df["panel_id"].map(normalize_text)
    fault_audit_df["strict_trigger_date"] = fault_audit_df["strict_trigger_date"].map(parse_timestamp)
    fault_audit_df["사건유형_재판정_ko"] = fault_audit_df["사건유형_재판정_ko"].map(normalize_text)
    precursor_df = fault_audit_df.loc[fault_audit_df["사건유형_재판정_ko"].eq("전조형 고장")].copy()
    precursor_df = precursor_df.loc[precursor_df["strict_trigger_date"].notna()].copy()

    summary_df = drop_repeated_header_rows(read_csv(share_dir / FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME))
    ensure_columns(summary_df, FAULT_PANEL_EVENT_AUDIT_SUMMARY_REQUIRED_COLS, FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME)
    if len(summary_df) != 1:
        raise SystemExit(
            f"{FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME} must contain exactly one row, found {len(summary_df)}"
        )
    expected_support = numeric_int(summary_df.iloc[0]["사건유형_재판정_전조형수"])
    if expected_support != EXPECTED_PRECURSOR_BENCHMARK_SUPPORT:
        raise SystemExit(
            f"audited precursor benchmark support must be {EXPECTED_PRECURSOR_BENCHMARK_SUPPORT}, found {expected_support}"
        )
    if len(precursor_df) != expected_support:
        raise SystemExit(
            f"precursor benchmark row count mismatch between fault audit summary and rows: summary={expected_support}, rows={len(precursor_df)}"
        )

    forensic_df = drop_repeated_header_rows(read_csv(share_dir / FORENSIC_SUMMARY_NAME))
    ensure_columns(forensic_df, FORENSIC_REQUIRED_COLS, FORENSIC_SUMMARY_NAME)
    forensic_df["site"] = forensic_df["site"].map(normalize_text)
    forensic_df["panel_id"] = forensic_df["panel_id"].map(normalize_text)
    forensic_match_df = forensic_df.loc[
        forensic_df["site"].eq(FORENSIC_HOLDOUT_SITE) & forensic_df["panel_id"].eq(FORENSIC_HOLDOUT_PANEL_ID)
    ].copy()
    if len(forensic_match_df) != 1:
        raise SystemExit(f"{FORENSIC_SUMMARY_NAME} must contain exactly one c42997 precursor forensic row")
    forensic_row = forensic_match_df.iloc[0]
    if normalize_text(forensic_row["사건유형_결정_ko"]) != "전조형 고장":
        raise SystemExit("c42997 forensic decision must be 전조형 고장 for benchmark reset precursor truth")
    if normalize_text(forensic_row["최종고장양상_결정_ko"]) != "급격 종료":
        raise SystemExit("c42997 forensic terminal pattern must be 급격 종료 for benchmark reset precursor truth")

    precursor_keys = set(zip(precursor_df["site"], precursor_df["panel_id"]))
    if (FORENSIC_HOLDOUT_SITE, FORENSIC_HOLDOUT_PANEL_ID) not in precursor_keys:
        raise SystemExit("c42997 forensic-confirmed precursor panel is missing from audited precursor benchmark truth")

    eligibility_df = drop_repeated_header_rows(read_csv(share_dir / ELIGIBILITY_CASES_NAME))
    ensure_columns(eligibility_df, ELIGIBILITY_REQUIRED_COLS, ELIGIBILITY_CASES_NAME)
    for col in ["site", "panel_id", "vendor_fault_family", "temporality_class"]:
        eligibility_df[col] = eligibility_df[col].map(normalize_text)
    eligibility_df["fault_start_date"] = eligibility_df["fault_start_date"].map(parse_timestamp)
    eligibility_df["precursor_eligible_flag"] = eligibility_df["precursor_eligible_flag"].map(to_int_flag).astype(int)
    eligibility_df = eligibility_df.sort_values(["site", "panel_id", "fault_start_date"]).drop_duplicates(
        subset=["site", "panel_id"], keep="last"
    )

    reaudit_df = drop_repeated_header_rows(read_csv(share_dir / REAUDIT_NAME))
    ensure_columns(reaudit_df, REAUDIT_REQUIRED_COLS, REAUDIT_NAME)
    for col in ["site", "panel_id", "vendor_fault_family"]:
        reaudit_df[col] = reaudit_df[col].map(normalize_text)
    reaudit_df["retrospective_onset_date"] = reaudit_df["retrospective_onset_date"].map(parse_timestamp)
    reaudit_df = reaudit_df.drop_duplicates(subset=["site", "panel_id"], keep="last")

    cases = precursor_df.merge(
        eligibility_df.loc[:, ["site", "panel_id", "vendor_fault_family", "temporality_class"]],
        on=["site", "panel_id"],
        how="left",
    )
    if "retrospective_onset_date" in cases.columns:
        cases = cases.rename(columns={"retrospective_onset_date": "retrospective_onset_date_audit"})
    else:
        cases["retrospective_onset_date_audit"] = pd.NaT
    cases = cases.merge(
        reaudit_df.loc[:, ["site", "panel_id", "vendor_fault_family", "retrospective_onset_date"]].rename(
            columns={
                "vendor_fault_family": "vendor_fault_family_reaudit",
                "retrospective_onset_date": "retrospective_onset_date_reaudit",
            }
        ),
        on=["site", "panel_id"],
        how="left",
    )
    cases["vendor_fault_family"] = cases["vendor_fault_family"].map(normalize_text)
    cases["vendor_fault_family_reaudit"] = cases["vendor_fault_family_reaudit"].map(normalize_text)
    cases["vendor_fault_family"] = cases["vendor_fault_family"].where(
        cases["vendor_fault_family"].ne(""),
        cases["vendor_fault_family_reaudit"],
    )
    if "temporality_class" not in cases.columns:
        cases["temporality_class"] = ""
    cases["temporality_class"] = cases["temporality_class"].map(normalize_text)
    cases["temporality_class"] = cases["temporality_class"].where(
        cases["temporality_class"].ne(""),
        "progressive_local_precursor_expected",
    )
    cases["retrospective_onset_date"] = pd.to_datetime(
        cases.get("retrospective_onset_date_audit", pd.Series(pd.NaT, index=cases.index)),
        errors="coerce",
    ).where(
        pd.to_datetime(cases.get("retrospective_onset_date_audit", pd.Series(pd.NaT, index=cases.index)), errors="coerce").notna(),
        pd.to_datetime(cases.get("retrospective_onset_date_reaudit", pd.Series(pd.NaT, index=cases.index)), errors="coerce"),
    )
    cases["fault_start_date"] = cases["strict_trigger_date"]
    cases["precursor_eligible_flag"] = 1
    cases = cases.loc[:, [*ELIGIBILITY_REQUIRED_COLS, "retrospective_onset_date"]].copy()
    cases = cases.sort_values(["site", "panel_id", "fault_start_date"]).reset_index(drop=True)
    return cases


def numeric_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return 0
    return int(numeric)


def load_site_daily(root: Path, site: str, panels: set[str], site_window_start: pd.Timestamp, site_window_end: pd.Timestamp) -> pd.DataFrame:
    out_dir = root / "data" / site / "out"
    gate_path = out_dir / GATE_DAILY_NAME
    core_path = out_dir / PANEL_DAY_CORE_NAME

    gate_df = read_site_subset_csv(
        gate_path,
        requested_cols=GATE_REQUIRED_COLS,
        panels=panels,
        window_start=site_window_start,
        window_end=site_window_end,
        site=site,
    )
    ensure_columns(gate_df, GATE_REQUIRED_COLS, gate_path.name)
    if "site" not in gate_df.columns:
        gate_df["site"] = site
    gate_df["site"] = gate_df["site"].map(normalize_text)
    gate_df["panel_id"] = gate_df["panel_id"].map(normalize_text)
    gate_df["date"] = gate_df["date"].map(parse_timestamp)
    gate_df = gate_df.loc[gate_df["panel_id"].isin(panels)].copy()
    gate_df = gate_df.loc[gate_df["date"].notna()].copy()
    for col in ["cond_var", "cond_evt", "cond_dtw", "cond_hs", "pre_ews", "ews_warning", "pre_alarm"]:
        gate_df[col] = gate_df[col].map(to_int_flag).astype(int)
    gate_df["signal_count"] = pd.to_numeric(gate_df["signal_count"], errors="coerce").fillna(0).astype(int)
    gate_df = gate_df.loc[:, ["site", *GATE_REQUIRED_COLS]].drop_duplicates(subset=["site", "panel_id", "date"], keep="last")

    core_df = read_site_subset_csv(
        core_path,
        requested_cols=CORE_REQUIRED_COLS,
        panels=panels,
        window_start=site_window_start,
        window_end=site_window_end,
        site=site,
    )
    ensure_columns(core_df, CORE_REQUIRED_COLS, core_path.name)
    core_df["site"] = site
    core_df["panel_id"] = core_df["panel_id"].map(normalize_text)
    core_df["date"] = core_df["date"].map(parse_timestamp)
    core_df = core_df.loc[core_df["panel_id"].isin(panels)].copy()
    core_df = core_df.loc[core_df["date"].notna()].copy()
    core_df["core_row_flag"] = 1
    core_df = core_df.loc[:, ["site", *CORE_REQUIRED_COLS, "core_row_flag"]].drop_duplicates(subset=["site", "panel_id", "date"], keep="last")

    daily = core_df.merge(gate_df, on=["site", "panel_id", "date"], how="outer")
    daily["core_row_flag"] = daily.get("core_row_flag", 0).fillna(0).astype(int)
    for col in ["cond_var", "cond_evt", "cond_dtw", "cond_hs", "pre_ews", "ews_warning", "pre_alarm"]:
        daily[col] = daily.get(col, 0).fillna(0).astype(int)
    daily["signal_count"] = daily.get("signal_count", 0).fillna(0).astype(int)
    daily["cond_evt_corroborated_flag"] = (
        daily["cond_evt"].eq(1) & daily[["cond_var", "cond_dtw", "cond_hs"]].max(axis=1).eq(1)
    ).astype(int)
    daily = daily.sort_values(["panel_id", "date"]).reset_index(drop=True)
    return daily


def load_daily_windows(root: Path, cases: pd.DataFrame) -> pd.DataFrame:
    if cases.empty:
        return pd.DataFrame(
            columns=[
                "site",
                "panel_id",
                "date",
                "core_row_flag",
                "cond_var",
                "cond_evt",
                "cond_dtw",
                "cond_hs",
                "pre_ews",
                "signal_count",
                "ews_warning",
                "pre_alarm",
                "cond_evt_corroborated_flag",
            ]
        )

    site_frames: list[pd.DataFrame] = []
    for site, site_cases in cases.groupby("site"):
        panels = set(site_cases["panel_id"].astype(str))
        site_window_start = site_cases["fault_start_date"].map(parse_timestamp).min() - pd.Timedelta(days=WINDOW_DAYS)
        site_window_end = site_cases["fault_start_date"].map(parse_timestamp).max()
        site_frames.append(load_site_daily(root, site, panels, site_window_start, site_window_end))
    return pd.concat(site_frames, ignore_index=True) if site_frames else pd.DataFrame()


def first_date_for_mask(df: pd.DataFrame, mask: pd.Series) -> pd.Timestamp | pd.NaT:
    matched = df.loc[mask].sort_values("date")
    if matched.empty:
        return pd.NaT
    return pd.Timestamp(matched.iloc[0]["date"])


def build_cond_evt_episodes(cond_evt_dates: list[pd.Timestamp]) -> list[dict[str, object]]:
    if not cond_evt_dates:
        return []
    sorted_dates = sorted(pd.Timestamp(value) for value in cond_evt_dates)
    episodes: list[dict[str, object]] = []
    current_start = sorted_dates[0]
    current_end = sorted_dates[0]
    current_dates = [sorted_dates[0]]
    max_gap_days = EPISODE_GAP_TOLERANCE_DAYS + 1
    for current_date in sorted_dates[1:]:
        gap_days = int((current_date - current_end).days)
        if gap_days <= max_gap_days:
            current_end = current_date
            current_dates.append(current_date)
            continue
        episodes.append(
            {
                "start_date": current_start,
                "end_date": current_end,
                "cond_evt_day_count": len(current_dates),
            }
        )
        current_start = current_date
        current_end = current_date
        current_dates = [current_date]
    episodes.append(
        {
            "start_date": current_start,
            "end_date": current_end,
            "cond_evt_day_count": len(current_dates),
        }
    )
    return episodes


def choose_latest_episode(episodes: list[dict[str, object]]) -> dict[str, object] | None:
    if not episodes:
        return None
    return sorted(
        episodes,
        key=lambda item: (pd.Timestamp(item["end_date"]), pd.Timestamp(item["start_date"]), int(item["cond_evt_day_count"])),
    )[-1]


def derive_preferred_onset(selected_episode: dict[str, object] | None, episode_df: pd.DataFrame) -> tuple[str, str, str, int | None, str]:
    if selected_episode is None:
        return (
            "",
            "no_detectable_precursor_episode",
            "weak",
            None,
            "bounded window 안에 cond_evt episode가 없어 precursor onset truth를 확정하지 못함",
        )

    onset_date = format_date(pd.Timestamp(selected_episode["start_date"]))
    if episode_df["pre_alarm"].eq(1).any() or episode_df["ews_warning"].eq(1).any():
        return (
            onset_date,
            "episode_start_before_alarm",
            "strong",
            int(selected_episode["cond_evt_day_count"]),
            "선택된 cond_evt episode 내부에 pre_alarm 또는 ews_warning가 있어 episode 시작을 강한 onset truth로 채택",
        )
    if episode_df["signal_count"].ge(2).any() or episode_df["cond_evt_corroborated_flag"].eq(1).any():
        return (
            onset_date,
            "episode_start_before_corroborated_signal",
            "medium",
            int(selected_episode["cond_evt_day_count"]),
            "선택된 cond_evt episode 내부에 corroborated cond_evt 또는 signal_count>=2가 있어 episode 시작을 중간 신뢰 onset으로 채택",
        )
    return (
        onset_date,
        "episode_start_evt_only",
        "weak",
        int(selected_episode["cond_evt_day_count"]),
        "선택된 cond_evt episode가 evt-only 패턴이라 episode 시작을 약한 onset으로 기록",
    )


def build_case_level_truth(cases: pd.DataFrame, daily_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for case in cases.to_dict(orient="records"):
        site = normalize_text(case["site"])
        panel_id = normalize_text(case["panel_id"])
        fault_start = parse_timestamp(case["fault_start_date"])
        bounded_window_start = pd.Timestamp(fault_start) - pd.Timedelta(days=WINDOW_DAYS)

        case_daily = daily_df.loc[
            daily_df["site"].eq(site)
            & daily_df["panel_id"].eq(panel_id)
            & daily_df["date"].ge(bounded_window_start)
            & daily_df["date"].lt(fault_start)
        ].copy()
        case_daily = case_daily.sort_values("date").reset_index(drop=True)

        first_cond_evt = first_date_for_mask(case_daily, case_daily["cond_evt"].eq(1))
        first_cond_evt_corroborated = first_date_for_mask(case_daily, case_daily["cond_evt_corroborated_flag"].eq(1))
        first_signalcount2 = first_date_for_mask(case_daily, case_daily["signal_count"].ge(2))
        first_pre_ews = first_date_for_mask(case_daily, case_daily["pre_ews"].eq(1))
        first_ews_warning = first_date_for_mask(case_daily, case_daily["ews_warning"].eq(1))
        first_pre_alarm = first_date_for_mask(case_daily, case_daily["pre_alarm"].eq(1))
        marker_dates = {
            "first_cond_evt": first_cond_evt,
            "first_cond_evt_corroborated": first_cond_evt_corroborated,
            "first_signalcount2": first_signalcount2,
            "first_pre_ews": first_pre_ews,
            "first_ews_warning": first_ews_warning,
            "first_pre_alarm": first_pre_alarm,
        }
        operational_first_detected_ts, operational_first_marker = derive_operational_first_detection(marker_dates)

        cond_evt_dates = [pd.Timestamp(value) for value in case_daily.loc[case_daily["cond_evt"].eq(1), "date"].tolist()]
        episodes = build_cond_evt_episodes(cond_evt_dates)
        selected_episode = choose_latest_episode(episodes)
        if selected_episode is None:
            episode_df = case_daily.iloc[0:0].copy()
            selected_start = ""
            selected_end = ""
            selected_count = None
        else:
            selected_start_ts = pd.Timestamp(selected_episode["start_date"])
            selected_end_ts = pd.Timestamp(selected_episode["end_date"])
            episode_df = case_daily.loc[case_daily["date"].between(selected_start_ts, selected_end_ts)].copy()
            selected_start = format_date(selected_start_ts)
            selected_end = format_date(selected_end_ts)
            selected_count = int(selected_episode["cond_evt_day_count"])

        preferred_onset, preferred_stage, preferred_confidence, _, onset_reason_ko = derive_preferred_onset(
            selected_episode,
            episode_df,
        )
        lead_days = lead_days_between(parse_timestamp(preferred_onset), fault_start)
        interpretive_onset_ts = parse_timestamp(case.get("retrospective_onset_date"))
        benchmark_onset_ts = parse_timestamp(preferred_onset)

        rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "fault_start_date": format_date(fault_start),
                "vendor_fault_family": normalize_text(case["vendor_fault_family"]),
                "temporality_class": normalize_text(case["temporality_class"]),
                "bounded_window_start": format_date(bounded_window_start),
                "first_cond_evt_date": format_date(first_cond_evt),
                "first_cond_evt_corroborated_date": format_date(first_cond_evt_corroborated),
                "first_signalcount2_date": format_date(first_signalcount2),
                "first_pre_ews_date": format_date(first_pre_ews),
                "first_ews_warning_date": format_date(first_ews_warning),
                "first_pre_alarm_date": format_date(first_pre_alarm),
                "selected_episode_start_date": selected_start,
                "selected_episode_end_date": selected_end,
                "selected_episode_day_count": selected_count,
                "preferred_precursor_onset_date": preferred_onset,
                "preferred_onset_stage": preferred_stage,
                "preferred_onset_confidence": preferred_confidence,
                "lead_days_from_preferred_onset_to_fault_start": lead_days,
                "onset_reason_ko": onset_reason_ko,
                "operational_first_precursor_detected_date": format_date(operational_first_detected_ts),
                "operational_first_precursor_marker_name": operational_first_marker,
                "operational_lead_days_to_fault_start": lead_days_between(operational_first_detected_ts, fault_start),
                "interpretive_precursor_onset_date": format_date(interpretive_onset_ts),
                "interpretive_lead_days_to_fault_start": lead_days_between(interpretive_onset_ts, fault_start),
                "benchmark_precursor_onset_date": format_date(benchmark_onset_ts),
                "benchmark_lead_days_to_fault_start": lead_days,
            }
        )
    return pd.DataFrame(rows).reindex(columns=CASE_OUTPUT_COLS)


def build_onset_ladder(case_truth_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for case in case_truth_df.to_dict(orient="records"):
        fault_start = parse_timestamp(case["fault_start_date"])
        for marker_name, column_name in MARKER_SPECS:
            onset_date = parse_timestamp(case[column_name])
            available_flag = int(not pd.isna(onset_date))
            rows.append(
                {
                    "site": normalize_text(case["site"]),
                    "panel_id": normalize_text(case["panel_id"]),
                    "fault_start_date": normalize_text(case["fault_start_date"]),
                    "onset_marker": marker_name,
                    "onset_date": format_date(onset_date),
                    "lead_days": lead_days_between(onset_date, fault_start),
                    "available_flag": available_flag,
                }
            )
    return pd.DataFrame(rows).reindex(columns=LADDER_OUTPUT_COLS)


def summarize_leads(lead_series: pd.Series) -> tuple[float | None, float | None, float | None]:
    valid = pd.to_numeric(lead_series, errors="coerce").dropna()
    if valid.empty:
        return (None, None, None)
    return (float(valid.median()), float(valid.min()), float(valid.max()))


def build_summary(case_truth_df: pd.DataFrame, ladder_df: pd.DataFrame) -> pd.DataFrame:
    total_case_count = int(len(case_truth_df))
    rows: list[dict[str, object]] = []

    for marker_name, _ in MARKER_SPECS:
        marker_df = ladder_df.loc[ladder_df["onset_marker"].eq(marker_name)].copy()
        available_df = marker_df.loc[marker_df["available_flag"].eq(1)].copy()
        median_lead, min_lead, max_lead = summarize_leads(available_df["lead_days"])
        rows.append(
            {
                "summary_type": "onset_marker",
                "marker_name": marker_name,
                "distribution_value": "",
                "case_count": total_case_count,
                "available_case_count": int(len(available_df)),
                "available_rate": (len(available_df) / total_case_count) if total_case_count else 0.0,
                "median_lead_days": median_lead,
                "min_lead_days": min_lead,
                "max_lead_days": max_lead,
            }
        )

    for confidence in ["strong", "medium", "weak"]:
        count = int(case_truth_df["preferred_onset_confidence"].eq(confidence).sum())
        rows.append(
            {
                "summary_type": "preferred_onset_confidence_distribution",
                "marker_name": "preferred_onset_confidence",
                "distribution_value": confidence,
                "case_count": count,
                "available_case_count": count,
                "available_rate": (count / total_case_count) if total_case_count else 0.0,
                "median_lead_days": None,
                "min_lead_days": None,
                "max_lead_days": None,
            }
        )

    for stage in [
        "episode_start_before_alarm",
        "episode_start_before_corroborated_signal",
        "episode_start_evt_only",
        "no_detectable_precursor_episode",
    ]:
        count = int(case_truth_df["preferred_onset_stage"].eq(stage).sum())
        rows.append(
            {
                "summary_type": "preferred_onset_stage_distribution",
                "marker_name": "preferred_onset_stage",
                "distribution_value": stage,
                "case_count": count,
                "available_case_count": count,
                "available_rate": (count / total_case_count) if total_case_count else 0.0,
                "median_lead_days": None,
                "min_lead_days": None,
                "max_lead_days": None,
            }
        )

    return pd.DataFrame(rows).reindex(columns=SUMMARY_OUTPUT_COLS)


def write_outputs(root: Path, case_truth_df: pd.DataFrame, ladder_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    case_truth_df.to_csv(share_dir / ONSET_TRUTH_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    ladder_df.to_csv(share_dir / ONSET_LADDER_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / ONSET_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    validate_taxonomy(root)
    cases = load_precursor_cases(root)
    daily_df = load_daily_windows(root, cases)
    case_truth_df = build_case_level_truth(cases, daily_df)
    ladder_df = build_onset_ladder(case_truth_df)
    summary_df = build_summary(case_truth_df, ladder_df)
    write_outputs(root, case_truth_df, ladder_df, summary_df)


if __name__ == "__main__":
    main()
