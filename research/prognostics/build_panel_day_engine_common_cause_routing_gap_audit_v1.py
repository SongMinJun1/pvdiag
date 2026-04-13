#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

EVAL_BUCKETS_NAME = "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv"
REAUDIT_NAME = "panel_date_reaudit_working.csv"
PANEL_DAY_CORE_NAME = "panel_day_core.csv"
GATE_DAILY_NAME = "ae_simple_local_precursor_gate_daily.csv"

CASES_OUTPUT_NAME = "panel_day_engine_common_cause_routing_gap_cases_v1.csv"
DAYS_OUTPUT_NAME = "panel_day_engine_common_cause_routing_gap_days_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_common_cause_routing_gap_summary_v1.csv"

NON_PANEL_BUCKET = "non_panel_or_common_cause"
WINDOW_DAYS = 7
NEAR_ANCHOR_DAYS = 3
BREADTH_FRACTION_THRESHOLD = 0.10
VERY_LOW_FRACTION_THRESHOLD = 0.05

REQUIRED_EVAL_COLS = ["fault_family_id", "eval_bucket_v2"]
REQUIRED_REAUDIT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "first_warning_date",
    "retrospective_onset_date",
    "candidate_validity",
    "vendor_fault_family",
    "vendor_reply_class",
]
CORE_REQUESTED_COLS = [
    "panel_id",
    "date",
    "final_fault",
    "group_off_like",
    "shadow_like",
]
GATE_REQUESTED_COLS = [
    "panel_id",
    "date",
    "group_off_date",
    "ews_warning",
    "pre_alarm",
]

CASES_OUTPUT_COLS = [
    "site",
    "panel_id",
    "anchor_date",
    "truth_case_id",
    "vendor_fault_family",
    "candidate_validity",
    "vendor_reply_class",
    "any_group_off_like_flag",
    "any_shadow_like_flag",
    "any_common_cause_like_flag",
    "any_local_precursor_alert_flag",
    "any_final_fault_flag",
    "max_final_fault_panel_count",
    "max_pre_alarm_panel_count",
    "max_ews_warning_panel_count",
    "max_group_off_like_panel_count",
    "max_shadow_like_panel_count",
    "max_final_fault_panel_fraction",
    "max_pre_alarm_panel_fraction",
    "max_ews_warning_panel_fraction",
    "max_group_off_like_panel_fraction",
    "max_shadow_like_panel_fraction",
    "first_date_max_final_fault_breadth",
    "first_date_max_pre_alarm_breadth",
    "routing_gap_class",
    "routing_gap_reason_ko",
]

DAYS_OUTPUT_COLS = [
    "site",
    "panel_id",
    "anchor_date",
    "truth_case_id",
    "date",
    "site_panel_count_on_date",
    "group_off_like_panel_count_on_date",
    "shadow_like_panel_count_on_date",
    "pre_alarm_panel_count_on_date",
    "ews_warning_panel_count_on_date",
    "final_fault_panel_count_on_date",
    "group_off_like_panel_fraction_on_date",
    "shadow_like_panel_fraction_on_date",
    "pre_alarm_panel_fraction_on_date",
    "ews_warning_panel_fraction_on_date",
    "final_fault_panel_fraction_on_date",
    "date_role_ko",
]

SUMMARY_OUTPUT_COLS = [
    "record_type",
    "site",
    "case_count",
    "breadth_without_current_marker_count",
    "local_fault_like_not_common_cause_like_count",
    "current_marker_present_but_misaligned_window_count",
    "weak_or_sparse_signal_count",
    "unclear_count",
    "any_common_cause_like_rate",
    "max_final_fault_panel_fraction_median",
    "max_pre_alarm_panel_fraction_median",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit why non-panel/common-cause cases are not explained by current routing markers."
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


def parse_timestamp(value: object) -> pd.Timestamp | pd.NaT:
    text = normalize_date_text(value)
    if not text:
        return pd.NaT
    return pd.to_datetime(text, errors="coerce")


def format_date(value: pd.Timestamp | pd.NaT) -> str:
    if pd.isna(value):
        return ""
    return pd.Timestamp(value).strftime("%Y-%m-%d")


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


def drop_repeated_header_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    header_mask = pd.Series(True, index=df.index)
    for col in df.columns:
        header_mask &= df[col].map(normalize_text).eq(col)
    return df.loc[~header_mask].reset_index(drop=True)


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def derive_fault_family_id(vendor_fault_family: str) -> str:
    family = normalize_text(vendor_fault_family)
    if family == "group_or_inverter_side_like":
        return "group_or_inverter_side_like"
    if family in {"none_visible", "none_visible_or_unconfirmed"}:
        return "none_visible_or_unconfirmed"
    if family in {"diode_like", "module_damage_like"}:
        return "electrical_fault_like_unknown_local_temporality"
    return ""


def read_site_date_subset_csv(
    path: Path,
    *,
    requested_cols: list[str],
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
    site: str,
) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")

    chunks: list[pd.DataFrame] = []
    usecols = lambda col: col in requested_cols
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
        chunk["date"] = chunk["date"].map(parse_timestamp)
        chunk = chunk.loc[chunk["date"].notna()].copy()
        chunk = chunk.loc[chunk["date"].ge(window_start) & chunk["date"].le(window_end)].copy()
        if chunk.empty:
            continue
        chunk["site"] = site
        chunk["panel_id"] = chunk["panel_id"].map(normalize_text)
        chunks.append(chunk)

    if not chunks:
        return pd.DataFrame(columns=["site", *requested_cols])
    return pd.concat(chunks, ignore_index=True)


def load_eval_bucket_map(root: Path) -> dict[str, str]:
    path = root / "_share" / EVAL_BUCKETS_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_EVAL_COLS, path.name)
    df["fault_family_id"] = df["fault_family_id"].map(normalize_text)
    df["eval_bucket_v2"] = df["eval_bucket_v2"].map(normalize_text)
    return dict(zip(df["fault_family_id"], df["eval_bucket_v2"]))


def load_case_universe(root: Path, eval_bucket_map: dict[str, str]) -> pd.DataFrame:
    path = root / "_share" / REAUDIT_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_REAUDIT_COLS, path.name)
    for col in REQUIRED_REAUDIT_COLS:
        df[col] = df[col].map(normalize_text)

    df["fault_family_id"] = df["vendor_fault_family"].map(derive_fault_family_id)
    df["mapped_eval_bucket_v2"] = df["fault_family_id"].map(lambda value: normalize_text(eval_bucket_map.get(value, "")))

    non_panel_mask = (
        df["mapped_eval_bucket_v2"].eq(NON_PANEL_BUCKET)
        | df["candidate_validity"].eq("group_side")
        | df["vendor_fault_family"].eq("group_or_inverter_side_like")
    )
    df = df.loc[non_panel_mask].copy()

    df["anchor_date"] = df["strict_trigger_date"]
    missing_anchor = df["anchor_date"].eq("")
    df.loc[missing_anchor, "anchor_date"] = df.loc[missing_anchor, "retrospective_onset_date"]
    missing_anchor = df["anchor_date"].eq("")
    df.loc[missing_anchor, "anchor_date"] = df.loc[missing_anchor, "first_warning_date"]
    df = df.loc[df["anchor_date"].ne("")].copy()

    df["truth_case_id"] = (
        "reaudit|"
        + df["site"].astype(str)
        + "|"
        + df["panel_id"].astype(str)
        + "|"
        + df["anchor_date"].astype(str)
    )
    return df.loc[
        :,
        [
            "site",
            "panel_id",
            "anchor_date",
            "truth_case_id",
            "vendor_fault_family",
            "candidate_validity",
            "vendor_reply_class",
        ],
    ].drop_duplicates(subset=["truth_case_id"], keep="first")


def load_site_windows(root: Path, cases_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    core_frames: list[pd.DataFrame] = []
    gate_frames: list[pd.DataFrame] = []
    for site, site_cases in cases_df.groupby("site"):
        anchor_dates = site_cases["anchor_date"].map(parse_timestamp)
        site_window_start = anchor_dates.min() - pd.Timedelta(days=WINDOW_DAYS)
        site_window_end = anchor_dates.max() + pd.Timedelta(days=WINDOW_DAYS)
        out_dir = root / "data" / site / "out"

        core_df = read_site_date_subset_csv(
            out_dir / PANEL_DAY_CORE_NAME,
            requested_cols=CORE_REQUESTED_COLS,
            window_start=site_window_start,
            window_end=site_window_end,
            site=site,
        )
        gate_df = read_site_date_subset_csv(
            out_dir / GATE_DAILY_NAME,
            requested_cols=GATE_REQUESTED_COLS,
            window_start=site_window_start,
            window_end=site_window_end,
            site=site,
        )

        if not core_df.empty:
            ensure_columns(core_df, ["site", "panel_id", "date"], f"{site}/{PANEL_DAY_CORE_NAME}")
            for col in ["final_fault", "group_off_like", "shadow_like"]:
                if col not in core_df.columns:
                    core_df[col] = 0
                core_df[col] = core_df[col].map(to_int_flag).astype(int)
            core_frames.append(core_df.loc[:, ["site", "panel_id", "date", "final_fault", "group_off_like", "shadow_like"]])

        if not gate_df.empty:
            ensure_columns(gate_df, ["site", "panel_id", "date"], f"{site}/{GATE_DAILY_NAME}")
            for col in ["group_off_date", "ews_warning", "pre_alarm"]:
                if col not in gate_df.columns:
                    gate_df[col] = 0
                gate_df[col] = gate_df[col].map(to_int_flag).astype(int)
            gate_frames.append(gate_df.loc[:, ["site", "panel_id", "date", "group_off_date", "ews_warning", "pre_alarm"]])

    core_all = pd.concat(core_frames, ignore_index=True) if core_frames else pd.DataFrame(
        columns=["site", "panel_id", "date", "final_fault", "group_off_like", "shadow_like"]
    )
    gate_all = pd.concat(gate_frames, ignore_index=True) if gate_frames else pd.DataFrame(
        columns=["site", "panel_id", "date", "group_off_date", "ews_warning", "pre_alarm"]
    )
    return core_all, gate_all


def aggregate_panel_daily(core_df: pd.DataFrame, gate_df: pd.DataFrame) -> pd.DataFrame:
    core_panel = (
        core_df.groupby(["site", "panel_id", "date"], as_index=False)[["final_fault", "group_off_like", "shadow_like"]]
        .max()
        if not core_df.empty
        else pd.DataFrame(columns=["site", "panel_id", "date", "final_fault", "group_off_like", "shadow_like"])
    )
    gate_panel = (
        gate_df.groupby(["site", "panel_id", "date"], as_index=False)[["group_off_date", "ews_warning", "pre_alarm"]]
        .max()
        if not gate_df.empty
        else pd.DataFrame(columns=["site", "panel_id", "date", "group_off_date", "ews_warning", "pre_alarm"])
    )

    panel_daily = core_panel.merge(gate_panel, how="outer", on=["site", "panel_id", "date"])
    for col in ["final_fault", "group_off_like", "shadow_like", "group_off_date", "ews_warning", "pre_alarm"]:
        if col not in panel_daily.columns:
            panel_daily[col] = 0
        panel_daily[col] = panel_daily[col].fillna(0).map(to_int_flag).astype(int)
    panel_daily["group_off_like_effective"] = panel_daily[["group_off_like", "group_off_date"]].max(axis=1)
    return panel_daily


def aggregate_site_daily(panel_daily_df: pd.DataFrame) -> pd.DataFrame:
    if panel_daily_df.empty:
        return pd.DataFrame(
            columns=[
                "site",
                "date",
                "site_panel_count_on_date",
                "final_fault_panel_count_on_date",
                "pre_alarm_panel_count_on_date",
                "ews_warning_panel_count_on_date",
                "group_off_like_panel_count_on_date",
                "shadow_like_panel_count_on_date",
                "final_fault_panel_fraction_on_date",
                "pre_alarm_panel_fraction_on_date",
                "ews_warning_panel_fraction_on_date",
                "group_off_like_panel_fraction_on_date",
                "shadow_like_panel_fraction_on_date",
            ]
        )

    site_daily = (
        panel_daily_df.groupby(["site", "date"], as_index=False)
        .agg(
            site_panel_count_on_date=("panel_id", "nunique"),
            final_fault_panel_count_on_date=("final_fault", "sum"),
            pre_alarm_panel_count_on_date=("pre_alarm", "sum"),
            ews_warning_panel_count_on_date=("ews_warning", "sum"),
            group_off_like_panel_count_on_date=("group_off_like_effective", "sum"),
            shadow_like_panel_count_on_date=("shadow_like", "sum"),
        )
    )
    denominator = site_daily["site_panel_count_on_date"].clip(lower=1)
    for prefix in ["final_fault", "pre_alarm", "ews_warning", "group_off_like", "shadow_like"]:
        site_daily[f"{prefix}_panel_fraction_on_date"] = (
            site_daily[f"{prefix}_panel_count_on_date"] / denominator
        ).astype(float)
    return site_daily


def safe_fraction(numerator: object, denominator: object) -> float:
    denom = max(int(denominator), 1)
    return float(numerator) / float(denom)


def build_case_day_rows(cases_df: pd.DataFrame, panel_daily_df: pd.DataFrame, site_daily_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    case_rows: list[dict[str, object]] = []
    day_rows: list[dict[str, object]] = []

    for case in cases_df.to_dict(orient="records"):
        site = normalize_text(case["site"])
        panel_id = normalize_text(case["panel_id"])
        anchor_text = normalize_text(case["anchor_date"])
        anchor_ts = parse_timestamp(anchor_text)
        truth_case_id = normalize_text(case["truth_case_id"])

        panel_window = panel_daily_df.loc[
            panel_daily_df["site"].eq(site)
            & panel_daily_df["panel_id"].eq(panel_id)
            & panel_daily_df["date"].ge(anchor_ts - pd.Timedelta(days=WINDOW_DAYS))
            & panel_daily_df["date"].le(anchor_ts + pd.Timedelta(days=WINDOW_DAYS))
        ].copy()
        site_window = site_daily_df.loc[
            site_daily_df["site"].eq(site)
            & site_daily_df["date"].ge(anchor_ts - pd.Timedelta(days=WINDOW_DAYS))
            & site_daily_df["date"].le(anchor_ts + pd.Timedelta(days=WINDOW_DAYS))
        ].copy()

        all_dates = pd.date_range(anchor_ts - pd.Timedelta(days=WINDOW_DAYS), anchor_ts + pd.Timedelta(days=WINDOW_DAYS), freq="D")
        site_window = pd.DataFrame({"date": all_dates}).merge(site_window, how="left", on="date")
        site_window["site"] = site
        for col in [
            "site_panel_count_on_date",
            "final_fault_panel_count_on_date",
            "pre_alarm_panel_count_on_date",
            "ews_warning_panel_count_on_date",
            "group_off_like_panel_count_on_date",
            "shadow_like_panel_count_on_date",
            "final_fault_panel_fraction_on_date",
            "pre_alarm_panel_fraction_on_date",
            "ews_warning_panel_fraction_on_date",
            "group_off_like_panel_fraction_on_date",
            "shadow_like_panel_fraction_on_date",
        ]:
            if col not in site_window.columns:
                site_window[col] = 0
            site_window[col] = site_window[col].fillna(0)

        near_window = panel_window.loc[
            panel_window["date"].ge(anchor_ts - pd.Timedelta(days=NEAR_ANCHOR_DAYS))
            & panel_window["date"].le(anchor_ts + pd.Timedelta(days=NEAR_ANCHOR_DAYS))
        ].copy()

        any_group_off_like_flag = int(panel_window["group_off_like_effective"].sum() > 0)
        any_shadow_like_flag = int(panel_window["shadow_like"].sum() > 0)
        any_common_cause_like_flag = int(any_group_off_like_flag == 1 or any_shadow_like_flag == 1)
        any_local_precursor_alert_flag = int((panel_window["ews_warning"].sum() + panel_window["pre_alarm"].sum()) > 0)
        any_final_fault_flag = int(panel_window["final_fault"].sum() > 0)

        near_common_cause_flag = int(
            near_window["group_off_like_effective"].sum() > 0 or near_window["shadow_like"].sum() > 0
        )
        marker_exists_outside_near = int(any_common_cause_like_flag == 1 and near_common_cause_flag == 0)

        max_final_fault_panel_count = int(site_window["final_fault_panel_count_on_date"].max())
        max_pre_alarm_panel_count = int(site_window["pre_alarm_panel_count_on_date"].max())
        max_ews_warning_panel_count = int(site_window["ews_warning_panel_count_on_date"].max())
        max_group_off_like_panel_count = int(site_window["group_off_like_panel_count_on_date"].max())
        max_shadow_like_panel_count = int(site_window["shadow_like_panel_count_on_date"].max())

        max_final_fault_panel_fraction = float(site_window["final_fault_panel_fraction_on_date"].max())
        max_pre_alarm_panel_fraction = float(site_window["pre_alarm_panel_fraction_on_date"].max())
        max_ews_warning_panel_fraction = float(site_window["ews_warning_panel_fraction_on_date"].max())
        max_group_off_like_panel_fraction = float(site_window["group_off_like_panel_fraction_on_date"].max())
        max_shadow_like_panel_fraction = float(site_window["shadow_like_panel_fraction_on_date"].max())

        final_max_dates = site_window.loc[
            site_window["final_fault_panel_fraction_on_date"].eq(max_final_fault_panel_fraction) & site_window["date"].notna(),
            "date",
        ]
        pre_alarm_max_dates = site_window.loc[
            site_window["pre_alarm_panel_fraction_on_date"].eq(max_pre_alarm_panel_fraction) & site_window["date"].notna(),
            "date",
        ]
        first_date_max_final_fault_breadth = format_date(final_max_dates.min() if not final_max_dates.empty else pd.NaT)
        first_date_max_pre_alarm_breadth = format_date(pre_alarm_max_dates.min() if not pre_alarm_max_dates.empty else pd.NaT)

        has_breadth = (
            max_final_fault_panel_fraction >= BREADTH_FRACTION_THRESHOLD
            or max_pre_alarm_panel_fraction >= BREADTH_FRACTION_THRESHOLD
        )
        sparse_signal = (
            max_final_fault_panel_fraction < VERY_LOW_FRACTION_THRESHOLD
            and max_pre_alarm_panel_fraction < VERY_LOW_FRACTION_THRESHOLD
            and max_ews_warning_panel_fraction < VERY_LOW_FRACTION_THRESHOLD
            and max_group_off_like_panel_fraction < VERY_LOW_FRACTION_THRESHOLD
            and max_shadow_like_panel_fraction < VERY_LOW_FRACTION_THRESHOLD
        )

        if marker_exists_outside_near == 1:
            routing_gap_class = "current_marker_present_but_misaligned_window"
            routing_gap_reason_ko = "group_off/shadow marker가 ±7일 안에는 있지만 anchor ±3일에는 없어 timing misalignment 가능성이 큼"
        elif any_common_cause_like_flag == 0 and has_breadth:
            routing_gap_class = "breadth_without_current_marker"
            routing_gap_reason_ko = "current routing marker는 없지만 site breadth가 넓어 breadth 기반 common-cause 징후가 더 강함"
        elif (
            any_common_cause_like_flag == 0
            and max_final_fault_panel_count <= 1
            and max_pre_alarm_panel_count <= 1
            and (max_final_fault_panel_count > 0 or max_pre_alarm_panel_count > 0 or max_ews_warning_panel_count > 0)
        ):
            routing_gap_class = "local_fault_like_not_common_cause_like"
            routing_gap_reason_ko = "marker도 없고 breadth도 국소적이라 common-cause보다 local fault-like에 가까워 보임"
        elif any_common_cause_like_flag == 0 and sparse_signal:
            routing_gap_class = "weak_or_sparse_signal"
            routing_gap_reason_ko = "marker와 breadth가 모두 약해 routing 근거가 희박함"
        else:
            routing_gap_class = "unclear"
            routing_gap_reason_ko = "현재 breadth/marker 패턴만으로는 공통원인 gap 원인을 단정하기 어려움"

        case_rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "anchor_date": anchor_text,
                "truth_case_id": truth_case_id,
                "vendor_fault_family": normalize_text(case["vendor_fault_family"]),
                "candidate_validity": normalize_text(case["candidate_validity"]),
                "vendor_reply_class": normalize_text(case["vendor_reply_class"]),
                "any_group_off_like_flag": any_group_off_like_flag,
                "any_shadow_like_flag": any_shadow_like_flag,
                "any_common_cause_like_flag": any_common_cause_like_flag,
                "any_local_precursor_alert_flag": any_local_precursor_alert_flag,
                "any_final_fault_flag": any_final_fault_flag,
                "max_final_fault_panel_count": max_final_fault_panel_count,
                "max_pre_alarm_panel_count": max_pre_alarm_panel_count,
                "max_ews_warning_panel_count": max_ews_warning_panel_count,
                "max_group_off_like_panel_count": max_group_off_like_panel_count,
                "max_shadow_like_panel_count": max_shadow_like_panel_count,
                "max_final_fault_panel_fraction": max_final_fault_panel_fraction,
                "max_pre_alarm_panel_fraction": max_pre_alarm_panel_fraction,
                "max_ews_warning_panel_fraction": max_ews_warning_panel_fraction,
                "max_group_off_like_panel_fraction": max_group_off_like_panel_fraction,
                "max_shadow_like_panel_fraction": max_shadow_like_panel_fraction,
                "first_date_max_final_fault_breadth": first_date_max_final_fault_breadth,
                "first_date_max_pre_alarm_breadth": first_date_max_pre_alarm_breadth,
                "routing_gap_class": routing_gap_class,
                "routing_gap_reason_ko": routing_gap_reason_ko,
            }
        )

        for day in site_window.to_dict(orient="records"):
            date_ts = pd.Timestamp(day["date"])
            if date_ts < anchor_ts:
                date_role = "pre"
            elif date_ts > anchor_ts:
                date_role = "post"
            else:
                date_role = "anchor"
            day_rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "anchor_date": anchor_text,
                    "truth_case_id": truth_case_id,
                    "date": format_date(date_ts),
                    "site_panel_count_on_date": int(day["site_panel_count_on_date"]),
                    "group_off_like_panel_count_on_date": int(day["group_off_like_panel_count_on_date"]),
                    "shadow_like_panel_count_on_date": int(day["shadow_like_panel_count_on_date"]),
                    "pre_alarm_panel_count_on_date": int(day["pre_alarm_panel_count_on_date"]),
                    "ews_warning_panel_count_on_date": int(day["ews_warning_panel_count_on_date"]),
                    "final_fault_panel_count_on_date": int(day["final_fault_panel_count_on_date"]),
                    "group_off_like_panel_fraction_on_date": float(day["group_off_like_panel_fraction_on_date"]),
                    "shadow_like_panel_fraction_on_date": float(day["shadow_like_panel_fraction_on_date"]),
                    "pre_alarm_panel_fraction_on_date": float(day["pre_alarm_panel_fraction_on_date"]),
                    "ews_warning_panel_fraction_on_date": float(day["ews_warning_panel_fraction_on_date"]),
                    "final_fault_panel_fraction_on_date": float(day["final_fault_panel_fraction_on_date"]),
                    "date_role_ko": date_role,
                }
            )

    cases_output = pd.DataFrame(case_rows).reindex(columns=CASES_OUTPUT_COLS)
    days_output = pd.DataFrame(day_rows).reindex(columns=DAYS_OUTPUT_COLS)
    return cases_output, days_output


def safe_rate(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    return float(series.map(to_int_flag).mean())


def safe_median(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return 0.0
    return float(numeric.median())


def build_summary(cases_output_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for record_type, site, scoped_df in [("overall", "", cases_output_df), *[("site", site, df) for site, df in cases_output_df.groupby("site")]]:
        class_counts = scoped_df["routing_gap_class"].value_counts().to_dict()
        rows.append(
            {
                "record_type": record_type,
                "site": site,
                "case_count": int(len(scoped_df)),
                "breadth_without_current_marker_count": int(class_counts.get("breadth_without_current_marker", 0)),
                "local_fault_like_not_common_cause_like_count": int(class_counts.get("local_fault_like_not_common_cause_like", 0)),
                "current_marker_present_but_misaligned_window_count": int(class_counts.get("current_marker_present_but_misaligned_window", 0)),
                "weak_or_sparse_signal_count": int(class_counts.get("weak_or_sparse_signal", 0)),
                "unclear_count": int(class_counts.get("unclear", 0)),
                "any_common_cause_like_rate": safe_rate(scoped_df["any_common_cause_like_flag"]),
                "max_final_fault_panel_fraction_median": safe_median(scoped_df["max_final_fault_panel_fraction"]),
                "max_pre_alarm_panel_fraction_median": safe_median(scoped_df["max_pre_alarm_panel_fraction"]),
            }
        )
    return pd.DataFrame(rows).reindex(columns=SUMMARY_OUTPUT_COLS)


def write_outputs(root: Path, cases_output_df: pd.DataFrame, days_output_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    cases_output_df.to_csv(share_dir / CASES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    days_output_df.to_csv(share_dir / DAYS_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    eval_bucket_map = load_eval_bucket_map(root)
    cases_df = load_case_universe(root, eval_bucket_map)
    core_df, gate_df = load_site_windows(root, cases_df)
    panel_daily_df = aggregate_panel_daily(core_df, gate_df)
    site_daily_df = aggregate_site_daily(panel_daily_df)
    cases_output_df, days_output_df = build_case_day_rows(cases_df, panel_daily_df, site_daily_df)
    summary_df = build_summary(cases_output_df)
    write_outputs(root, cases_output_df, days_output_df, summary_df)


if __name__ == "__main__":
    main()
