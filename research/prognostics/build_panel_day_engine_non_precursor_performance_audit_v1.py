#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

EVAL_BUCKETS_NAME = "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv"
ELIGIBILITY_CASES_NAME = "panel_day_engine_local_precursor_eligibility_cases_v1.csv"
REAUDIT_NAME = "panel_date_reaudit_working.csv"
FAULT_PANEL_EVENT_AUDIT_NAME = "panel_day_engine_fault_panel_event_audit_v1.csv"
FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME = "panel_day_engine_fault_panel_event_audit_summary_v1.csv"
PANEL_DAY_CORE_NAME = "panel_day_core.csv"
GATE_DAILY_NAME = "ae_simple_local_precursor_gate_daily.csv"

CASES_OUTPUT_NAME = "panel_day_engine_non_precursor_performance_cases_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_non_precursor_performance_summary_v1.csv"
COMPARISON_OUTPUT_NAME = "panel_day_engine_non_precursor_bucket_comparison_v1.csv"

ABRUPT_BUCKET = "abrupt_or_no_precursor_now"
NON_PANEL_BUCKET = "non_panel_or_common_cause"
UNKNOWN_BUCKET = "unknown_needs_review"

ABRUPT_LOOKBACK_DAYS = 3
ABRUPT_LOOKAHEAD_DAYS = 7
NON_PANEL_WINDOW_DAYS = 3

REQUIRED_EVAL_BUCKETS_COLS = ["fault_family_id", "eval_bucket_v2"]
REQUIRED_ELIGIBILITY_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "fault_start_date",
    "vendor_fault_family",
    "temporality_class",
    "precursor_eligible_flag",
]
REQUIRED_REAUDIT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "candidate_validity",
    "vendor_fault_family",
    "vendor_reply_class",
]
REQUIRED_FAULT_AUDIT_COLS = ["site", "panel_id", "strict_trigger_date", "사건유형_재판정_ko"]
REQUIRED_FAULT_AUDIT_SUMMARY_COLS = ["사건유형_재판정_급작수", "순수급작_패널수"]
CORE_REQUESTED_COLS = [
    "panel_id",
    "date",
    "confirmed_fault",
    "critical_fault",
    "final_fault",
    "group_off_like",
    "shadow_like",
]

EXPECTED_PURE_ABRUPT_SUPPORT = 3
EXPECTED_COMMON_CAUSE_SUPPORT = 4
GATE_REQUESTED_COLS = [
    "panel_id",
    "date",
    "group_off_date",
    "ews_warning",
    "pre_alarm",
]

CASES_OUTPUT_COLS = [
    "eval_bucket_v2",
    "site",
    "panel_id",
    "anchor_date",
    "anchor_source",
    "vendor_fault_family",
    "truth_case_id",
    "candidate_validity",
    "vendor_reply_class",
    "first_confirmed_fault_date",
    "confirmed_fault_available_flag",
    "confirmed_fault_lead_days_to_fault_start",
    "confirmed_fault_hit_by_anchor_flag",
    "confirmed_fault_hit_within_3d_after_flag",
    "confirmed_fault_hit_within_7d_after_flag",
    "first_critical_fault_date",
    "critical_fault_available_flag",
    "critical_fault_lead_days_to_fault_start",
    "critical_fault_hit_by_anchor_flag",
    "critical_fault_hit_within_3d_after_flag",
    "critical_fault_hit_within_7d_after_flag",
    "first_final_fault_date",
    "final_fault_available_flag",
    "final_fault_lead_days_to_fault_start",
    "final_fault_hit_by_anchor_flag",
    "final_fault_hit_within_3d_after_flag",
    "final_fault_hit_within_7d_after_flag",
    "abrupt_eval_reason_ko",
    "any_group_off_like_flag",
    "any_shadow_like_flag",
    "any_common_cause_like_flag",
    "any_local_precursor_alert_flag",
    "any_final_fault_flag",
    "route_eval_reason_ko",
    "descriptive_only_reason_ko",
]

SUMMARY_OUTPUT_COLS = [
    "eval_bucket_v2",
    "case_count",
    "final_fault_hit_by_anchor_rate",
    "final_fault_hit_within_3d_after_rate",
    "final_fault_hit_within_7d_after_rate",
    "confirmed_fault_hit_within_7d_after_rate",
    "critical_fault_hit_within_7d_after_rate",
    "common_cause_like_rate",
    "group_off_like_rate",
    "shadow_like_rate",
    "local_precursor_alert_contamination_rate",
    "final_fault_rate",
    "note_ko",
]

COMPARISON_OUTPUT_COLS = [
    "bucket_name",
    "primary_metric_name",
    "primary_metric_value",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit non-precursor buckets separately after precursor-bearing performance."
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
    if text in {"", "0", "0.0", "false", "f", "n", "no"}:
        return 0
    if text in {"1", "1.0", "true", "t", "y", "yes"}:
        return 1
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return int(bool(numeric)) if not pd.isna(numeric) else 0


def numeric_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


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


def derive_fault_family_id(vendor_fault_family: str, temporality_class: str) -> str:
    family = normalize_text(vendor_fault_family)
    temporality = normalize_text(temporality_class)
    if family in {"diode_like", "module_damage_like"}:
        if temporality == "progressive_local_precursor_expected":
            return "electrical_fault_like_progressive_local"
        if temporality == "abrupt_local_precursor_unexpected":
            return "electrical_fault_like_abrupt_local"
        return "electrical_fault_like_unknown_local_temporality"
    if family == "group_or_inverter_side_like":
        return "group_or_inverter_side_like"
    if family in {"none_visible", "none_visible_or_unconfirmed"}:
        return "none_visible_or_unconfirmed"
    return ""


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
        chunk["panel_id"] = chunk["panel_id"].map(normalize_text)
        chunk = chunk.loc[chunk["panel_id"].isin(panels)].copy()
        if chunk.empty:
            continue
        chunk["date"] = chunk["date"].map(parse_timestamp)
        chunk = chunk.loc[chunk["date"].notna()].copy()
        chunk = chunk.loc[chunk["date"].ge(window_start) & chunk["date"].le(window_end)].copy()
        if chunk.empty:
            continue
        chunks.append(chunk)

    if not chunks:
        columns = list(requested_cols)
        if site is not None and "site" not in columns:
            columns = ["site", *columns]
        return pd.DataFrame(columns=columns)
    return pd.concat(chunks, ignore_index=True)


def load_eval_bucket_map(root: Path) -> dict[str, str]:
    path = root / "_share" / EVAL_BUCKETS_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_EVAL_BUCKETS_COLS, path.name)
    df["fault_family_id"] = df["fault_family_id"].map(normalize_text)
    df["eval_bucket_v2"] = df["eval_bucket_v2"].map(normalize_text)
    return dict(zip(df["fault_family_id"], df["eval_bucket_v2"]))


def load_eligibility_cases(root: Path, eval_bucket_map: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    path = root / "_share" / ELIGIBILITY_CASES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_ELIGIBILITY_COLS, path.name)
    for col in ["site", "panel_id", "vendor_fault_family", "temporality_class"]:
        df[col] = df[col].map(normalize_text)
    for col in ["strict_trigger_date", "fault_start_date"]:
        df[col] = df[col].map(normalize_date_text)
    df["precursor_eligible_flag"] = df["precursor_eligible_flag"].map(to_int_flag).astype(int)
    df["fault_family_id"] = df.apply(
        lambda row: derive_fault_family_id(
            normalize_text(row["vendor_fault_family"]),
            normalize_text(row["temporality_class"]),
        ),
        axis=1,
    )
    df["eval_bucket_v2"] = df["fault_family_id"].map(lambda value: normalize_text(eval_bucket_map.get(value, UNKNOWN_BUCKET)))
    df["truth_case_id"] = (
        "eligibility|"
        + df["site"].astype(str)
        + "|"
        + df["panel_id"].astype(str)
        + "|"
        + df["fault_start_date"].astype(str)
    )
    df["anchor_date"] = df["fault_start_date"].where(df["fault_start_date"].ne(""), df["strict_trigger_date"])
    df["anchor_source"] = df["fault_start_date"].map(normalize_text).ne("").map(lambda flag: "fault_start_date" if flag else "strict_trigger_date")
    abrupt_df = df.loc[df["eval_bucket_v2"].eq(ABRUPT_BUCKET)].copy()
    unknown_df = df.loc[df["eval_bucket_v2"].eq(UNKNOWN_BUCKET)].copy()
    return abrupt_df, unknown_df


def load_reaudit_cases(root: Path, eval_bucket_map: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    path = root / "_share" / REAUDIT_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_REAUDIT_COLS, path.name)
    for col in ["site", "panel_id", "strict_trigger_date", "candidate_validity", "vendor_fault_family", "vendor_reply_class"]:
        df[col] = df[col].map(normalize_text)
    df["fault_family_id"] = df.apply(
        lambda row: derive_fault_family_id(
            normalize_text(row["vendor_fault_family"]),
            "",
        ),
        axis=1,
    )
    df["mapped_eval_bucket_v2"] = df["fault_family_id"].map(lambda value: normalize_text(eval_bucket_map.get(value, "")))
    df["truth_case_id"] = (
        "reaudit|"
        + df["site"].astype(str)
        + "|"
        + df["panel_id"].astype(str)
        + "|"
        + df["strict_trigger_date"].astype(str)
    )
    df["anchor_date"] = df["strict_trigger_date"]
    df["anchor_source"] = "strict_trigger_date"

    abrupt_df = df.loc[df["mapped_eval_bucket_v2"].eq(ABRUPT_BUCKET)].copy()
    non_panel_df = df.loc[
        df["mapped_eval_bucket_v2"].eq(NON_PANEL_BUCKET)
        | df["candidate_validity"].eq("group_side")
        | df["vendor_fault_family"].eq("group_or_inverter_side_like")
    ].copy()
    unknown_df = df.loc[
        (df["mapped_eval_bucket_v2"].eq(UNKNOWN_BUCKET))
        | (df["vendor_fault_family"].eq("open_or_device_issue_like"))
        | (df["candidate_validity"].eq("needs_more_info"))
    ].copy()
    return abrupt_df, non_panel_df, unknown_df


def load_panel_metadata(root: Path) -> pd.DataFrame:
    eligibility_path = root / "_share" / ELIGIBILITY_CASES_NAME
    eligibility_df = drop_repeated_header_rows(read_csv(eligibility_path))
    ensure_columns(eligibility_df, REQUIRED_ELIGIBILITY_COLS, eligibility_path.name)
    for col in ["site", "panel_id", "strict_trigger_date", "fault_start_date", "vendor_fault_family", "temporality_class"]:
        eligibility_df[col] = eligibility_df[col].map(normalize_text)
    eligibility_df = eligibility_df.sort_values(["site", "panel_id", "fault_start_date", "strict_trigger_date"]).drop_duplicates(
        subset=["site", "panel_id"], keep="last"
    )

    reaudit_path = root / "_share" / REAUDIT_NAME
    reaudit_df = drop_repeated_header_rows(read_csv(reaudit_path))
    ensure_columns(reaudit_df, REQUIRED_REAUDIT_COLS, reaudit_path.name)
    for col in REQUIRED_REAUDIT_COLS:
        reaudit_df[col] = reaudit_df[col].map(normalize_text)
    reaudit_df = reaudit_df.sort_values(["site", "panel_id", "strict_trigger_date"]).drop_duplicates(
        subset=["site", "panel_id"], keep="last"
    )

    metadata_df = reaudit_df.merge(
        eligibility_df.loc[:, ["site", "panel_id", "fault_start_date", "strict_trigger_date", "vendor_fault_family"]],
        on=["site", "panel_id"],
        how="outer",
        suffixes=("_reaudit", "_eligibility"),
    )
    metadata_df["vendor_fault_family"] = metadata_df["vendor_fault_family_reaudit"].map(normalize_text)
    metadata_df["vendor_fault_family"] = metadata_df["vendor_fault_family"].where(
        metadata_df["vendor_fault_family"].ne(""),
        metadata_df["vendor_fault_family_eligibility"].map(normalize_text),
    )
    metadata_df["anchor_date"] = metadata_df["fault_start_date"].map(normalize_text)
    metadata_df["anchor_date"] = metadata_df["anchor_date"].where(
        metadata_df["anchor_date"].ne(""),
        metadata_df["strict_trigger_date_reaudit"].map(normalize_text),
    )
    metadata_df["anchor_date"] = metadata_df["anchor_date"].where(
        metadata_df["anchor_date"].ne(""),
        metadata_df["strict_trigger_date_eligibility"].map(normalize_text),
    )
    metadata_df["candidate_validity"] = metadata_df.get("candidate_validity", "").map(normalize_text)
    metadata_df["vendor_reply_class"] = metadata_df.get("vendor_reply_class", "").map(normalize_text)
    return metadata_df.loc[:, ["site", "panel_id", "anchor_date", "vendor_fault_family", "candidate_validity", "vendor_reply_class"]]


def load_fault_audit_cases(root: Path) -> tuple[pd.DataFrame, set[tuple[str, str]]]:
    share_dir = root / "_share"
    fault_audit_df = drop_repeated_header_rows(read_csv(share_dir / FAULT_PANEL_EVENT_AUDIT_NAME))
    ensure_columns(fault_audit_df, REQUIRED_FAULT_AUDIT_COLS, FAULT_PANEL_EVENT_AUDIT_NAME)
    for col in ["site", "panel_id", "strict_trigger_date", "사건유형_재판정_ko"]:
        fault_audit_df[col] = fault_audit_df[col].map(normalize_text)

    summary_df = drop_repeated_header_rows(read_csv(share_dir / FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME))
    ensure_columns(summary_df, REQUIRED_FAULT_AUDIT_SUMMARY_COLS, FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME)
    if len(summary_df) != 1:
        raise SystemExit(
            f"{FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME} must contain exactly one row, found {len(summary_df)}"
        )
    summary_row = summary_df.iloc[0]
    audited_abrupt_count = numeric_int(summary_row["사건유형_재판정_급작수"])
    pure_abrupt_count = numeric_int(summary_row["순수급작_패널수"])
    if audited_abrupt_count != EXPECTED_PURE_ABRUPT_SUPPORT or pure_abrupt_count != EXPECTED_PURE_ABRUPT_SUPPORT:
        raise SystemExit(
            f"audited pure abrupt benchmark support must stay {EXPECTED_PURE_ABRUPT_SUPPORT}, found abrupt={audited_abrupt_count}, pure={pure_abrupt_count}"
        )

    abrupt_df = fault_audit_df.loc[fault_audit_df["사건유형_재판정_ko"].eq("급작 고장"), ["site", "panel_id", "strict_trigger_date"]].copy()
    abrupt_df = abrupt_df.drop_duplicates(subset=["site", "panel_id"], keep="first")
    if len(abrupt_df) != EXPECTED_PURE_ABRUPT_SUPPORT:
        raise SystemExit(
            f"fault-panel event audit abrupt benchmark row count must be {EXPECTED_PURE_ABRUPT_SUPPORT}, found {len(abrupt_df)}"
        )

    benchmark_fault_keys = {
        (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        for row in fault_audit_df.loc[:, ["site", "panel_id"]].drop_duplicates().to_dict(orient="records")
    }
    return abrupt_df, benchmark_fault_keys


def build_case_frames(root: Path, eval_bucket_map: dict[str, str]) -> pd.DataFrame:
    metadata_df = load_panel_metadata(root)
    _, eligibility_unknown_df = load_eligibility_cases(root, eval_bucket_map)
    reaudit_abrupt_df, reaudit_non_panel_df, reaudit_unknown_df = load_reaudit_cases(root, eval_bucket_map)
    fault_abrupt_df, benchmark_fault_keys = load_fault_audit_cases(root)

    eligibility_unknown_df["candidate_validity"] = "eligibility_local_case"
    eligibility_unknown_df["vendor_reply_class"] = ""
    eligibility_unknown_df["eval_bucket_v2"] = UNKNOWN_BUCKET

    reaudit_non_panel_df["eval_bucket_v2"] = NON_PANEL_BUCKET
    reaudit_unknown_df["eval_bucket_v2"] = UNKNOWN_BUCKET

    abrupt_df = fault_abrupt_df.merge(metadata_df, on=["site", "panel_id"], how="left")
    abrupt_df["eval_bucket_v2"] = ABRUPT_BUCKET
    abrupt_df["anchor_date"] = abrupt_df["strict_trigger_date"].where(
        abrupt_df["strict_trigger_date"].map(normalize_text).ne(""),
        abrupt_df["anchor_date"].map(normalize_text),
    )
    abrupt_df["anchor_source"] = "fault_panel_event_audit.strict_trigger_date"
    abrupt_df["truth_case_id"] = (
        "fault_event_audit|"
        + abrupt_df["site"].astype(str)
        + "|"
        + abrupt_df["panel_id"].astype(str)
        + "|"
        + abrupt_df["anchor_date"].astype(str)
    )
    abrupt_df["candidate_validity"] = abrupt_df["candidate_validity"].map(normalize_text).where(
        abrupt_df["candidate_validity"].map(normalize_text).ne(""),
        "true_positive",
    )
    abrupt_df["vendor_reply_class"] = abrupt_df["vendor_reply_class"].map(normalize_text)
    abrupt_df["vendor_fault_family"] = abrupt_df["vendor_fault_family"].map(normalize_text)
    abrupt_df = abrupt_df.loc[
        :,
        ["eval_bucket_v2", "site", "panel_id", "anchor_date", "anchor_source", "vendor_fault_family", "truth_case_id", "candidate_validity", "vendor_reply_class"],
    ].drop_duplicates(subset=["truth_case_id"], keep="first")

    non_panel_df = reaudit_non_panel_df.loc[
        :,
        ["eval_bucket_v2", "site", "panel_id", "anchor_date", "anchor_source", "vendor_fault_family", "truth_case_id", "candidate_validity", "vendor_reply_class"],
    ].drop_duplicates(subset=["truth_case_id"], keep="first")
    if len(non_panel_df) != EXPECTED_COMMON_CAUSE_SUPPORT:
        raise SystemExit(
            f"common-cause benchmark support must stay {EXPECTED_COMMON_CAUSE_SUPPORT}, found {len(non_panel_df)}"
        )

    unknown_df = pd.concat(
        [
            eligibility_unknown_df.loc[:, ["eval_bucket_v2", "site", "panel_id", "anchor_date", "anchor_source", "vendor_fault_family", "truth_case_id", "candidate_validity", "vendor_reply_class"]],
            reaudit_unknown_df.loc[:, ["eval_bucket_v2", "site", "panel_id", "anchor_date", "anchor_source", "vendor_fault_family", "truth_case_id", "candidate_validity", "vendor_reply_class"]],
        ],
        ignore_index=True,
    ).drop_duplicates(subset=["truth_case_id"], keep="first")
    unknown_df["site"] = unknown_df["site"].map(normalize_text)
    unknown_df["panel_id"] = unknown_df["panel_id"].map(normalize_text)
    unknown_df = unknown_df.loc[
        ~unknown_df.apply(
            lambda row: (normalize_text(row["site"]), normalize_text(row["panel_id"])) in benchmark_fault_keys,
            axis=1,
        )
    ].copy()

    for df in [abrupt_df, non_panel_df, unknown_df]:
        for col in ["site", "panel_id", "anchor_date", "anchor_source", "vendor_fault_family", "truth_case_id", "candidate_validity", "vendor_reply_class", "eval_bucket_v2"]:
            df[col] = df[col].map(normalize_text)
    return pd.concat([abrupt_df, non_panel_df, unknown_df], ignore_index=True)


def load_site_windows(root: Path, cases_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    core_frames: list[pd.DataFrame] = []
    gate_frames: list[pd.DataFrame] = []
    for site, site_cases in cases_df.groupby("site"):
        panels = set(site_cases["panel_id"].astype(str))
        anchor_dates = site_cases["anchor_date"].map(parse_timestamp)
        site_window_start = anchor_dates.min() - pd.Timedelta(days=max(ABRUPT_LOOKBACK_DAYS, NON_PANEL_WINDOW_DAYS))
        site_window_end = anchor_dates.max() + pd.Timedelta(days=max(ABRUPT_LOOKAHEAD_DAYS, NON_PANEL_WINDOW_DAYS))
        out_dir = root / "data" / site / "out"
        core_df = read_site_subset_csv(
            out_dir / PANEL_DAY_CORE_NAME,
            requested_cols=CORE_REQUESTED_COLS,
            panels=panels,
            window_start=site_window_start,
            window_end=site_window_end,
            site=site,
        )
        gate_df = read_site_subset_csv(
            out_dir / GATE_DAILY_NAME,
            requested_cols=GATE_REQUESTED_COLS,
            panels=panels,
            window_start=site_window_start,
            window_end=site_window_end,
            site=site,
        )
        if not core_df.empty:
            ensure_columns(core_df, ["panel_id", "date"], f"{site}/{PANEL_DAY_CORE_NAME}")
            core_df["site"] = site
            core_df["panel_id"] = core_df["panel_id"].map(normalize_text)
            core_df["date"] = core_df["date"].map(parse_timestamp)
            for col in ["confirmed_fault", "critical_fault", "final_fault", "group_off_like", "shadow_like"]:
                if col not in core_df.columns:
                    core_df[col] = 0
                core_df[col] = core_df[col].map(to_int_flag).astype(int)
            core_frames.append(
                core_df.loc[:, ["site", "panel_id", "date", "confirmed_fault", "critical_fault", "final_fault", "group_off_like", "shadow_like"]]
            )
        if not gate_df.empty:
            ensure_columns(gate_df, ["panel_id", "date"], f"{site}/{GATE_DAILY_NAME}")
            gate_df["site"] = site
            gate_df["panel_id"] = gate_df["panel_id"].map(normalize_text)
            gate_df["date"] = gate_df["date"].map(parse_timestamp)
            for col in ["group_off_date", "ews_warning", "pre_alarm"]:
                if col not in gate_df.columns:
                    gate_df[col] = 0
                gate_df[col] = gate_df[col].map(to_int_flag).astype(int)
            gate_frames.append(
                gate_df.loc[:, ["site", "panel_id", "date", "group_off_date", "ews_warning", "pre_alarm"]]
            )
    core_all = pd.concat(core_frames, ignore_index=True) if core_frames else pd.DataFrame(
        columns=["site", "panel_id", "date", "confirmed_fault", "critical_fault", "final_fault", "group_off_like", "shadow_like"]
    )
    gate_all = pd.concat(gate_frames, ignore_index=True) if gate_frames else pd.DataFrame(
        columns=["site", "panel_id", "date", "group_off_date", "ews_warning", "pre_alarm"]
    )
    return core_all, gate_all


def first_flag_date(df: pd.DataFrame, flag_col: str) -> pd.Timestamp | pd.NaT:
    matched = df.loc[df[flag_col].eq(1)].sort_values("date")
    if matched.empty:
        return pd.NaT
    return pd.Timestamp(matched.iloc[0]["date"])


def lead_days_to_anchor(marker_date: pd.Timestamp | pd.NaT, anchor_date: pd.Timestamp | pd.NaT) -> int | None:
    if pd.isna(marker_date) or pd.isna(anchor_date):
        return None
    return int((pd.Timestamp(anchor_date) - pd.Timestamp(marker_date)).days)


def evaluate_marker_window(marker_date: pd.Timestamp | pd.NaT, anchor_date: pd.Timestamp | pd.NaT) -> tuple[int, int, int]:
    if pd.isna(marker_date) or pd.isna(anchor_date):
        return (0, 0, 0)
    delta_days = int((pd.Timestamp(marker_date) - pd.Timestamp(anchor_date)).days)
    hit_by_anchor = int(delta_days <= 0)
    hit_within_3_after = int(1 <= delta_days <= 3)
    hit_within_7_after = int(1 <= delta_days <= 7)
    return (hit_by_anchor, hit_within_3_after, hit_within_7_after)


def abrupt_reason(row: dict[str, object]) -> str:
    if to_int_flag(row["final_fault_hit_by_anchor_flag"]) == 1:
        return "anchor 시점까지 final_fault가 이미 확인되어 abrupt detection by-anchor hit로 해석"
    if to_int_flag(row["final_fault_hit_within_3d_after_flag"]) == 1:
        return "anchor 직후 3일 안에 final_fault가 확인되어 short-delay abrupt detection으로 해석"
    if to_int_flag(row["final_fault_hit_within_7d_after_flag"]) == 1:
        return "anchor 이후 7일 안에 final_fault가 확인되어 delayed abrupt detection으로 해석"
    if to_int_flag(row["critical_fault_hit_within_7d_after_flag"]) == 1 or to_int_flag(row["confirmed_fault_hit_within_7d_after_flag"]) == 1:
        return "final_fault는 늦지만 critical/confirmed fault 신호가 7일 안에 나타남"
    return "anchor 전후 7일 내 hard fault marker가 약해 abrupt bucket에서도 late/miss 성격이 큼"


def route_reason(row: dict[str, object]) -> str:
    common_cause_like = to_int_flag(row["any_common_cause_like_flag"])
    local_alert = to_int_flag(row["any_local_precursor_alert_flag"])
    if common_cause_like == 1 and local_alert == 0:
        return "group_off/shadow evidence가 있어 common-cause routing 신호로 해석"
    if common_cause_like == 1 and local_alert == 1:
        return "common-cause 신호는 있으나 local precursor alert contamination이 함께 있어 주의가 필요"
    if local_alert == 1:
        return "group-side review row지만 현재 window에서는 local precursor alert 성분이 더 강함"
    return "review truth는 group/inverter 쪽이지만 현재 panel-day routing evidence는 약함"


def descriptive_reason(row: dict[str, object]) -> str:
    if normalize_text(row["vendor_fault_family"]) == "open_or_device_issue_like":
        return "현재 taxonomy row에 직접 안착하지 않은 open/device-like review row라 descriptive only"
    if normalize_text(row["candidate_validity"]) == "needs_more_info":
        return "review truth가 아직 불완전해 unknown_needs_review descriptive only로 유지"
    return "temporality 또는 fault family 정렬이 아직 불안정해 descriptive only로 유지"


def build_case_output(cases_df: pd.DataFrame, core_df: pd.DataFrame, gate_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for case in cases_df.to_dict(orient="records"):
        site = normalize_text(case["site"])
        panel_id = normalize_text(case["panel_id"])
        eval_bucket = normalize_text(case["eval_bucket_v2"])
        anchor_ts = parse_timestamp(case["anchor_date"])
        core_panel = core_df.loc[core_df["site"].eq(site) & core_df["panel_id"].eq(panel_id)].copy()
        gate_panel = gate_df.loc[gate_df["site"].eq(site) & gate_df["panel_id"].eq(panel_id)].copy()

        row = {
            "eval_bucket_v2": eval_bucket,
            "site": site,
            "panel_id": panel_id,
            "anchor_date": normalize_text(case["anchor_date"]),
            "anchor_source": normalize_text(case["anchor_source"]),
            "vendor_fault_family": normalize_text(case["vendor_fault_family"]),
            "truth_case_id": normalize_text(case["truth_case_id"]),
            "candidate_validity": normalize_text(case["candidate_validity"]),
            "vendor_reply_class": normalize_text(case["vendor_reply_class"]),
            "first_confirmed_fault_date": "",
            "confirmed_fault_available_flag": 0,
            "confirmed_fault_lead_days_to_fault_start": None,
            "confirmed_fault_hit_by_anchor_flag": 0,
            "confirmed_fault_hit_within_3d_after_flag": 0,
            "confirmed_fault_hit_within_7d_after_flag": 0,
            "first_critical_fault_date": "",
            "critical_fault_available_flag": 0,
            "critical_fault_lead_days_to_fault_start": None,
            "critical_fault_hit_by_anchor_flag": 0,
            "critical_fault_hit_within_3d_after_flag": 0,
            "critical_fault_hit_within_7d_after_flag": 0,
            "first_final_fault_date": "",
            "final_fault_available_flag": 0,
            "final_fault_lead_days_to_fault_start": None,
            "final_fault_hit_by_anchor_flag": 0,
            "final_fault_hit_within_3d_after_flag": 0,
            "final_fault_hit_within_7d_after_flag": 0,
            "abrupt_eval_reason_ko": "",
            "any_group_off_like_flag": 0,
            "any_shadow_like_flag": 0,
            "any_common_cause_like_flag": 0,
            "any_local_precursor_alert_flag": 0,
            "any_final_fault_flag": 0,
            "route_eval_reason_ko": "",
            "descriptive_only_reason_ko": "",
        }

        if eval_bucket == ABRUPT_BUCKET:
            abrupt_window = core_panel.loc[
                core_panel["date"].ge(anchor_ts - pd.Timedelta(days=ABRUPT_LOOKBACK_DAYS))
                & core_panel["date"].le(anchor_ts + pd.Timedelta(days=ABRUPT_LOOKAHEAD_DAYS))
            ].copy()
            for marker_name, flag_col, prefix in [
                ("confirmed_fault", "confirmed_fault", "confirmed_fault"),
                ("critical_fault", "critical_fault", "critical_fault"),
                ("final_fault", "final_fault", "final_fault"),
            ]:
                marker_ts = first_flag_date(abrupt_window, flag_col)
                available_flag = int(not pd.isna(marker_ts))
                hit_by_anchor, hit_within_3_after, hit_within_7_after = evaluate_marker_window(marker_ts, anchor_ts)
                row[f"first_{marker_name}_date"] = format_date(marker_ts)
                row[f"{prefix}_available_flag"] = available_flag
                row[f"{prefix}_lead_days_to_fault_start"] = lead_days_to_anchor(marker_ts, anchor_ts)
                row[f"{prefix}_hit_by_anchor_flag"] = hit_by_anchor
                row[f"{prefix}_hit_within_3d_after_flag"] = hit_within_3_after
                row[f"{prefix}_hit_within_7d_after_flag"] = hit_within_7_after
            row["abrupt_eval_reason_ko"] = abrupt_reason(row)

        elif eval_bucket == NON_PANEL_BUCKET:
            non_panel_window = core_panel.loc[
                core_panel["date"].ge(anchor_ts - pd.Timedelta(days=NON_PANEL_WINDOW_DAYS))
                & core_panel["date"].le(anchor_ts + pd.Timedelta(days=NON_PANEL_WINDOW_DAYS))
            ].copy()
            gate_window = gate_panel.loc[
                gate_panel["date"].ge(anchor_ts - pd.Timedelta(days=NON_PANEL_WINDOW_DAYS))
                & gate_panel["date"].le(anchor_ts + pd.Timedelta(days=NON_PANEL_WINDOW_DAYS))
            ].copy()
            any_group_off_like_flag = int(
                non_panel_window.get("group_off_like", pd.Series(dtype=int)).map(to_int_flag).sum() > 0
                or gate_window.get("group_off_date", pd.Series(dtype=int)).map(to_int_flag).sum() > 0
            )
            any_shadow_like_flag = int(non_panel_window.get("shadow_like", pd.Series(dtype=int)).map(to_int_flag).sum() > 0)
            any_common_cause_like_flag = int(any_group_off_like_flag == 1 or any_shadow_like_flag == 1)
            any_local_precursor_alert_flag = int(
                gate_window.get("ews_warning", pd.Series(dtype=int)).map(to_int_flag).sum() > 0
                or gate_window.get("pre_alarm", pd.Series(dtype=int)).map(to_int_flag).sum() > 0
            )
            any_final_fault_flag = int(non_panel_window.get("final_fault", pd.Series(dtype=int)).map(to_int_flag).sum() > 0)

            row["any_group_off_like_flag"] = any_group_off_like_flag
            row["any_shadow_like_flag"] = any_shadow_like_flag
            row["any_common_cause_like_flag"] = any_common_cause_like_flag
            row["any_local_precursor_alert_flag"] = any_local_precursor_alert_flag
            row["any_final_fault_flag"] = any_final_fault_flag
            row["route_eval_reason_ko"] = route_reason(row)

        else:
            row["descriptive_only_reason_ko"] = descriptive_reason(case)

        rows.append(row)

    return pd.DataFrame(rows).reindex(columns=CASES_OUTPUT_COLS)


def safe_rate(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    return float(series.map(to_int_flag).mean())


def build_summary(cases_output_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    abrupt_df = cases_output_df.loc[cases_output_df["eval_bucket_v2"].eq(ABRUPT_BUCKET)].copy()
    rows.append(
        {
            "eval_bucket_v2": ABRUPT_BUCKET,
            "case_count": int(len(abrupt_df)),
            "final_fault_hit_by_anchor_rate": safe_rate(abrupt_df["final_fault_hit_by_anchor_flag"]),
            "final_fault_hit_within_3d_after_rate": safe_rate(abrupt_df["final_fault_hit_within_3d_after_flag"]),
            "final_fault_hit_within_7d_after_rate": safe_rate(abrupt_df["final_fault_hit_within_7d_after_flag"]),
            "confirmed_fault_hit_within_7d_after_rate": safe_rate(abrupt_df["confirmed_fault_hit_within_7d_after_flag"]),
            "critical_fault_hit_within_7d_after_rate": safe_rate(abrupt_df["critical_fault_hit_within_7d_after_flag"]),
            "common_cause_like_rate": None,
            "group_off_like_rate": None,
            "shadow_like_rate": None,
            "local_precursor_alert_contamination_rate": None,
            "final_fault_rate": None,
            "note_ko": "abrupt/no-precursor bucket은 detection timing 관점으로 해석",
        }
    )

    non_panel_df = cases_output_df.loc[cases_output_df["eval_bucket_v2"].eq(NON_PANEL_BUCKET)].copy()
    rows.append(
        {
            "eval_bucket_v2": NON_PANEL_BUCKET,
            "case_count": int(len(non_panel_df)),
            "final_fault_hit_by_anchor_rate": None,
            "final_fault_hit_within_3d_after_rate": None,
            "final_fault_hit_within_7d_after_rate": None,
            "confirmed_fault_hit_within_7d_after_rate": None,
            "critical_fault_hit_within_7d_after_rate": None,
            "common_cause_like_rate": safe_rate(non_panel_df["any_common_cause_like_flag"]),
            "group_off_like_rate": safe_rate(non_panel_df["any_group_off_like_flag"]),
            "shadow_like_rate": safe_rate(non_panel_df["any_shadow_like_flag"]),
            "local_precursor_alert_contamination_rate": safe_rate(non_panel_df["any_local_precursor_alert_flag"]),
            "final_fault_rate": safe_rate(non_panel_df["any_final_fault_flag"]),
            "note_ko": "non-panel/common-cause bucket은 routing/classification 관점으로 해석",
        }
    )

    unknown_df = cases_output_df.loc[cases_output_df["eval_bucket_v2"].eq(UNKNOWN_BUCKET)].copy()
    rows.append(
        {
            "eval_bucket_v2": UNKNOWN_BUCKET,
            "case_count": int(len(unknown_df)),
            "final_fault_hit_by_anchor_rate": None,
            "final_fault_hit_within_3d_after_rate": None,
            "final_fault_hit_within_7d_after_rate": None,
            "confirmed_fault_hit_within_7d_after_rate": None,
            "critical_fault_hit_within_7d_after_rate": None,
            "common_cause_like_rate": None,
            "group_off_like_rate": None,
            "shadow_like_rate": None,
            "local_precursor_alert_contamination_rate": None,
            "final_fault_rate": None,
            "note_ko": "descriptive_only",
        }
    )

    return pd.DataFrame(rows).reindex(columns=SUMMARY_OUTPUT_COLS)


def build_bucket_comparison(summary_df: pd.DataFrame) -> pd.DataFrame:
    summary_map = {normalize_text(row["eval_bucket_v2"]): row for row in summary_df.to_dict(orient="records")}
    rows = [
        {
            "bucket_name": ABRUPT_BUCKET,
            "primary_metric_name": "final_fault_hit_within_7d_after_rate",
            "primary_metric_value": summary_map.get(ABRUPT_BUCKET, {}).get("final_fault_hit_within_7d_after_rate"),
            "note_ko": "abrupt/no-precursor bucket의 핵심은 anchor 직후 며칠 안에 final/confirmed fault로 도달하는가이다.",
        },
        {
            "bucket_name": NON_PANEL_BUCKET,
            "primary_metric_name": "common_cause_like_rate",
            "primary_metric_value": summary_map.get(NON_PANEL_BUCKET, {}).get("common_cause_like_rate"),
            "note_ko": "non-panel/common-cause bucket의 핵심은 group_off/shadow 기반 routing 신호가 충분한가이다.",
        },
        {
            "bucket_name": UNKNOWN_BUCKET,
            "primary_metric_name": "descriptive_only",
            "primary_metric_value": None,
            "note_ko": "unknown bucket은 공식 denominator가 아니라 descriptive review 대상으로만 유지한다.",
        },
    ]
    return pd.DataFrame(rows).reindex(columns=COMPARISON_OUTPUT_COLS)


def write_outputs(root: Path, cases_output_df: pd.DataFrame, summary_df: pd.DataFrame, comparison_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    cases_output_df.to_csv(share_dir / CASES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    comparison_df.to_csv(share_dir / COMPARISON_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    eval_bucket_map = load_eval_bucket_map(root)
    cases_df = build_case_frames(root, eval_bucket_map)
    core_df, gate_df = load_site_windows(root, cases_df)
    cases_output_df = build_case_output(cases_df, core_df, gate_df)
    summary_df = build_summary(cases_output_df)
    comparison_df = build_bucket_comparison(summary_df)
    write_outputs(root, cases_output_df, summary_df, comparison_df)


if __name__ == "__main__":
    main()
