#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROUTING_GAP_CASES_NAME = "panel_day_engine_common_cause_routing_gap_cases_v1.csv"
EVAL_BUCKETS_NAME = "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv"
PRECURSOR_ONSET_TRUTH_NAME = "panel_day_engine_precursor_onset_truth_v1.csv"
ELIGIBILITY_CASES_NAME = "panel_day_engine_local_precursor_eligibility_cases_v1.csv"
REAUDIT_NAME = "panel_date_reaudit_working.csv"
PANEL_DAY_CORE_NAME = "panel_day_core.csv"
GATE_DAILY_NAME = "ae_simple_local_precursor_gate_daily.csv"

SUMMARY_OUTPUT_NAME = "panel_day_engine_common_cause_breadth_marker_summary_v1.csv"
CASES_OUTPUT_NAME = "panel_day_engine_common_cause_breadth_marker_cases_v1.csv"
SWEEP_OUTPUT_NAME = "panel_day_engine_common_cause_breadth_marker_threshold_sweep_v1.csv"

NON_PANEL_BUCKET = "non_panel_or_common_cause"
PRECURSOR_BUCKET = "precursor_bearing_detectable_now"
ABRUPT_BUCKET = "abrupt_or_no_precursor_now"

WINDOW_DEFS = {
    "same_day": 0,
    "plusminus_3d": 3,
    "plusminus_7d": 7,
}
THRESHOLDS = [0.05, 0.10, 0.15, 0.20]
RULE_FAMILIES = {
    "final_fault_breadth_threshold": ["final_fault"],
    "pre_alarm_breadth_threshold": ["pre_alarm"],
    "ews_warning_breadth_threshold": ["ews_warning"],
    "any_breadth_threshold": ["final_fault", "pre_alarm", "ews_warning"],
}

REQUIRED_ROUTING_GAP_COLS = [
    "site",
    "panel_id",
    "anchor_date",
    "truth_case_id",
    "vendor_fault_family",
    "any_common_cause_like_flag",
]
REQUIRED_EVAL_COLS = ["fault_family_id", "eval_bucket_v2"]
REQUIRED_ONSET_TRUTH_COLS = [
    "site",
    "panel_id",
    "fault_start_date",
    "vendor_fault_family",
    "temporality_class",
]
REQUIRED_ELIGIBILITY_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "fault_start_date",
    "vendor_fault_family",
    "temporality_class",
]
REQUIRED_REAUDIT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "vendor_fault_family",
]
CORE_REQUESTED_COLS = ["panel_id", "date", "final_fault"]
GATE_REQUESTED_COLS = ["panel_id", "date", "ews_warning", "pre_alarm"]

SWEEP_OUTPUT_COLS = [
    "rule_name",
    "rule_family",
    "window_name",
    "threshold",
    "positive_case_count",
    "positive_capture_count",
    "positive_capture_rate",
    "precursor_negative_case_count",
    "precursor_negative_trigger_count",
    "precursor_negative_trigger_rate",
    "abrupt_negative_case_count",
    "abrupt_negative_trigger_count",
    "abrupt_negative_trigger_rate",
    "contamination_score",
    "note_ko",
]

CASES_OUTPUT_COLS = [
    "site",
    "panel_id",
    "anchor_date",
    "truth_case_id",
    "max_final_fault_panel_fraction_same_day",
    "max_final_fault_panel_fraction_3d",
    "max_final_fault_panel_fraction_7d",
    "max_pre_alarm_panel_fraction_same_day",
    "max_pre_alarm_panel_fraction_3d",
    "max_pre_alarm_panel_fraction_7d",
    "max_ews_warning_panel_fraction_same_day",
    "max_ews_warning_panel_fraction_3d",
    "max_ews_warning_panel_fraction_7d",
    "current_marker_any_flag",
    "best_breadth_rule_name",
    "best_breadth_rule_hit_flag",
    "breadth_reason_ko",
]

SUMMARY_OUTPUT_COLS = [
    "summary_type",
    "rule_name",
    "rule_family",
    "window_name",
    "threshold",
    "positive_capture_rate",
    "contamination_score",
    "precursor_negative_trigger_rate",
    "abrupt_negative_trigger_rate",
    "recommended_rule_flag",
    "why_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit breadth-based common-cause routing markers against positive capture and contamination."
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


def load_positive_cases(root: Path) -> pd.DataFrame:
    path = root / "_share" / ROUTING_GAP_CASES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_ROUTING_GAP_COLS, path.name)
    for col in REQUIRED_ROUTING_GAP_COLS:
        df[col] = df[col].map(normalize_text)
    df["case_group"] = "positive"
    df["current_marker_any_flag"] = df["any_common_cause_like_flag"].map(to_int_flag).astype(int)
    return df.loc[:, ["case_group", "site", "panel_id", "anchor_date", "truth_case_id", "vendor_fault_family", "current_marker_any_flag"]]


def load_precursor_negative_cases(root: Path, eval_bucket_map: dict[str, str]) -> pd.DataFrame:
    path = root / "_share" / PRECURSOR_ONSET_TRUTH_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_ONSET_TRUTH_COLS, path.name)
    for col in REQUIRED_ONSET_TRUTH_COLS:
        df[col] = df[col].map(normalize_text)
    df["fault_family_id"] = df.apply(
        lambda row: derive_fault_family_id(row["vendor_fault_family"], row["temporality_class"]),
        axis=1,
    )
    df["eval_bucket_v2"] = df["fault_family_id"].map(lambda value: normalize_text(eval_bucket_map.get(value, "")))
    df = df.loc[df["eval_bucket_v2"].eq(PRECURSOR_BUCKET)].copy()
    df["case_group"] = "precursor_negative"
    df["anchor_date"] = df["fault_start_date"]
    df["truth_case_id"] = (
        "onset|"
        + df["site"].astype(str)
        + "|"
        + df["panel_id"].astype(str)
        + "|"
        + df["fault_start_date"].astype(str)
    )
    df["current_marker_any_flag"] = 0
    return df.loc[:, ["case_group", "site", "panel_id", "anchor_date", "truth_case_id", "vendor_fault_family", "current_marker_any_flag"]]


def load_abrupt_negative_cases(root: Path, eval_bucket_map: dict[str, str]) -> pd.DataFrame:
    eligibility_path = root / "_share" / ELIGIBILITY_CASES_NAME
    eligibility_df = drop_repeated_header_rows(read_csv(eligibility_path))
    ensure_columns(eligibility_df, REQUIRED_ELIGIBILITY_COLS, eligibility_path.name)
    for col in REQUIRED_ELIGIBILITY_COLS:
        eligibility_df[col] = eligibility_df[col].map(normalize_text)
    eligibility_df["fault_family_id"] = eligibility_df.apply(
        lambda row: derive_fault_family_id(row["vendor_fault_family"], row["temporality_class"]),
        axis=1,
    )
    eligibility_df["eval_bucket_v2"] = eligibility_df["fault_family_id"].map(lambda value: normalize_text(eval_bucket_map.get(value, "")))
    eligibility_df = eligibility_df.loc[eligibility_df["eval_bucket_v2"].eq(ABRUPT_BUCKET)].copy()
    eligibility_df["anchor_date"] = eligibility_df["fault_start_date"].where(
        eligibility_df["fault_start_date"].ne(""),
        eligibility_df["strict_trigger_date"],
    )
    eligibility_df["truth_case_id"] = (
        "eligibility|"
        + eligibility_df["site"].astype(str)
        + "|"
        + eligibility_df["panel_id"].astype(str)
        + "|"
        + eligibility_df["anchor_date"].astype(str)
    )
    eligibility_df["case_group"] = "abrupt_negative"
    eligibility_df["current_marker_any_flag"] = 0

    reaudit_path = root / "_share" / REAUDIT_NAME
    reaudit_df = drop_repeated_header_rows(read_csv(reaudit_path))
    ensure_columns(reaudit_df, REQUIRED_REAUDIT_COLS, reaudit_path.name)
    for col in REQUIRED_REAUDIT_COLS:
        reaudit_df[col] = reaudit_df[col].map(normalize_text)
    reaudit_df["fault_family_id"] = reaudit_df["vendor_fault_family"].map(lambda value: derive_fault_family_id(value, ""))
    reaudit_df["eval_bucket_v2"] = reaudit_df["fault_family_id"].map(lambda value: normalize_text(eval_bucket_map.get(value, "")))
    reaudit_df = reaudit_df.loc[reaudit_df["eval_bucket_v2"].eq(ABRUPT_BUCKET)].copy()
    reaudit_df["anchor_date"] = reaudit_df["strict_trigger_date"]
    reaudit_df["truth_case_id"] = (
        "reaudit|"
        + reaudit_df["site"].astype(str)
        + "|"
        + reaudit_df["panel_id"].astype(str)
        + "|"
        + reaudit_df["anchor_date"].astype(str)
    )
    reaudit_df["case_group"] = "abrupt_negative"
    reaudit_df["current_marker_any_flag"] = 0

    combined = pd.concat(
        [
            eligibility_df.loc[:, ["case_group", "site", "panel_id", "anchor_date", "truth_case_id", "vendor_fault_family", "current_marker_any_flag"]],
            reaudit_df.loc[:, ["case_group", "site", "panel_id", "anchor_date", "truth_case_id", "vendor_fault_family", "current_marker_any_flag"]],
        ],
        ignore_index=True,
    )
    combined = combined.loc[combined["anchor_date"].ne("")].drop_duplicates(subset=["truth_case_id"], keep="first")
    return combined


def load_case_universe(root: Path) -> pd.DataFrame:
    eval_bucket_map = load_eval_bucket_map(root)
    positive_df = load_positive_cases(root)
    precursor_df = load_precursor_negative_cases(root, eval_bucket_map)
    abrupt_df = load_abrupt_negative_cases(root, eval_bucket_map)
    combined = pd.concat([positive_df, precursor_df, abrupt_df], ignore_index=True)
    combined["site"] = combined["site"].map(normalize_text)
    combined["panel_id"] = combined["panel_id"].map(normalize_text)
    combined["anchor_date"] = combined["anchor_date"].map(normalize_date_text)
    combined["truth_case_id"] = combined["truth_case_id"].map(normalize_text)
    combined["vendor_fault_family"] = combined["vendor_fault_family"].map(normalize_text)
    combined["current_marker_any_flag"] = combined["current_marker_any_flag"].map(to_int_flag).astype(int)
    return combined


def load_site_windows(root: Path, cases_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    core_frames: list[pd.DataFrame] = []
    gate_frames: list[pd.DataFrame] = []
    max_window = max(WINDOW_DEFS.values())
    for site, site_cases in cases_df.groupby("site"):
        anchor_dates = site_cases["anchor_date"].map(parse_timestamp)
        site_window_start = anchor_dates.min() - pd.Timedelta(days=max_window)
        site_window_end = anchor_dates.max() + pd.Timedelta(days=max_window)
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
            core_df["final_fault"] = core_df["final_fault"].map(to_int_flag).astype(int)
            core_frames.append(core_df.loc[:, ["site", "panel_id", "date", "final_fault"]])
        if not gate_df.empty:
            ensure_columns(gate_df, ["site", "panel_id", "date"], f"{site}/{GATE_DAILY_NAME}")
            for col in ["ews_warning", "pre_alarm"]:
                gate_df[col] = gate_df[col].map(to_int_flag).astype(int)
            gate_frames.append(gate_df.loc[:, ["site", "panel_id", "date", "ews_warning", "pre_alarm"]])
    core_all = pd.concat(core_frames, ignore_index=True) if core_frames else pd.DataFrame(columns=["site", "panel_id", "date", "final_fault"])
    gate_all = pd.concat(gate_frames, ignore_index=True) if gate_frames else pd.DataFrame(columns=["site", "panel_id", "date", "ews_warning", "pre_alarm"])
    return core_all, gate_all


def aggregate_site_daily(core_df: pd.DataFrame, gate_df: pd.DataFrame) -> pd.DataFrame:
    core_panel = (
        core_df.groupby(["site", "panel_id", "date"], as_index=False)[["final_fault"]].max()
        if not core_df.empty
        else pd.DataFrame(columns=["site", "panel_id", "date", "final_fault"])
    )
    gate_panel = (
        gate_df.groupby(["site", "panel_id", "date"], as_index=False)[["ews_warning", "pre_alarm"]].max()
        if not gate_df.empty
        else pd.DataFrame(columns=["site", "panel_id", "date", "ews_warning", "pre_alarm"])
    )
    panel_daily = core_panel.merge(gate_panel, how="outer", on=["site", "panel_id", "date"])
    for col in ["final_fault", "ews_warning", "pre_alarm"]:
        if col not in panel_daily.columns:
            panel_daily[col] = 0
        panel_daily[col] = panel_daily[col].fillna(0).map(to_int_flag).astype(int)

    site_daily = (
        panel_daily.groupby(["site", "date"], as_index=False)
        .agg(
            site_panel_count_on_date=("panel_id", "nunique"),
            final_fault_panel_count_on_date=("final_fault", "sum"),
            pre_alarm_panel_count_on_date=("pre_alarm", "sum"),
            ews_warning_panel_count_on_date=("ews_warning", "sum"),
        )
    )
    denom = site_daily["site_panel_count_on_date"].clip(lower=1)
    site_daily["final_fault_panel_fraction_on_date"] = site_daily["final_fault_panel_count_on_date"] / denom
    site_daily["pre_alarm_panel_fraction_on_date"] = site_daily["pre_alarm_panel_count_on_date"] / denom
    site_daily["ews_warning_panel_fraction_on_date"] = site_daily["ews_warning_panel_count_on_date"] / denom
    return site_daily


def build_case_feature_frame(cases_df: pd.DataFrame, site_daily_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    max_window = max(WINDOW_DEFS.values())
    for case in cases_df.to_dict(orient="records"):
        anchor_ts = parse_timestamp(case["anchor_date"])
        site_window = site_daily_df.loc[
            site_daily_df["site"].eq(case["site"])
            & site_daily_df["date"].ge(anchor_ts - pd.Timedelta(days=max_window))
            & site_daily_df["date"].le(anchor_ts + pd.Timedelta(days=max_window))
        ].copy()

        all_dates = pd.date_range(anchor_ts - pd.Timedelta(days=max_window), anchor_ts + pd.Timedelta(days=max_window), freq="D")
        site_window = pd.DataFrame({"date": all_dates}).merge(site_window, how="left", on="date")
        site_window["site"] = case["site"]
        for col in [
            "site_panel_count_on_date",
            "final_fault_panel_count_on_date",
            "pre_alarm_panel_count_on_date",
            "ews_warning_panel_count_on_date",
            "final_fault_panel_fraction_on_date",
            "pre_alarm_panel_fraction_on_date",
            "ews_warning_panel_fraction_on_date",
        ]:
            if col not in site_window.columns:
                site_window[col] = 0
            site_window[col] = site_window[col].fillna(0)

        row: dict[str, object] = dict(case)
        for window_name, window_days in WINDOW_DEFS.items():
            window_df = site_window.loc[
                site_window["date"].ge(anchor_ts - pd.Timedelta(days=window_days))
                & site_window["date"].le(anchor_ts + pd.Timedelta(days=window_days))
            ].copy()
            if window_name == "same_day":
                window_df = site_window.loc[site_window["date"].eq(anchor_ts)].copy()
            suffix = "same_day" if window_name == "same_day" else ("3d" if window_name == "plusminus_3d" else "7d")
            row[f"max_final_fault_panel_fraction_{suffix}"] = float(window_df["final_fault_panel_fraction_on_date"].max()) if not window_df.empty else 0.0
            row[f"max_pre_alarm_panel_fraction_{suffix}"] = float(window_df["pre_alarm_panel_fraction_on_date"].max()) if not window_df.empty else 0.0
            row[f"max_ews_warning_panel_fraction_{suffix}"] = float(window_df["ews_warning_panel_fraction_on_date"].max()) if not window_df.empty else 0.0
            row[f"max_final_fault_panel_count_{suffix}"] = int(window_df["final_fault_panel_count_on_date"].max()) if not window_df.empty else 0
            row[f"max_pre_alarm_panel_count_{suffix}"] = int(window_df["pre_alarm_panel_count_on_date"].max()) if not window_df.empty else 0
            row[f"max_ews_warning_panel_count_{suffix}"] = int(window_df["ews_warning_panel_count_on_date"].max()) if not window_df.empty else 0
        rows.append(row)
    return pd.DataFrame(rows)


def compute_rule_hit(row: pd.Series, rule_family: str, window_name: str, threshold: float) -> int:
    suffix = "same_day" if window_name == "same_day" else ("3d" if window_name == "plusminus_3d" else "7d")
    features = RULE_FAMILIES[rule_family]
    values = [float(row[f"max_{feature}_panel_fraction_{suffix}"]) for feature in features]
    return int(max(values) >= threshold)


def build_threshold_sweep(case_features_df: pd.DataFrame) -> pd.DataFrame:
    positive_df = case_features_df.loc[case_features_df["case_group"].eq("positive")].copy()
    precursor_df = case_features_df.loc[case_features_df["case_group"].eq("precursor_negative")].copy()
    abrupt_df = case_features_df.loc[case_features_df["case_group"].eq("abrupt_negative")].copy()

    rows: list[dict[str, object]] = []
    for rule_family in RULE_FAMILIES:
        for window_name in WINDOW_DEFS:
            for threshold in THRESHOLDS:
                positive_hits = positive_df.apply(compute_rule_hit, axis=1, args=(rule_family, window_name, threshold)) if not positive_df.empty else pd.Series(dtype=int)
                precursor_hits = precursor_df.apply(compute_rule_hit, axis=1, args=(rule_family, window_name, threshold)) if not precursor_df.empty else pd.Series(dtype=int)
                abrupt_hits = abrupt_df.apply(compute_rule_hit, axis=1, args=(rule_family, window_name, threshold)) if not abrupt_df.empty else pd.Series(dtype=int)

                positive_case_count = int(len(positive_df))
                precursor_case_count = int(len(precursor_df))
                abrupt_case_count = int(len(abrupt_df))
                positive_capture_count = int(positive_hits.sum()) if not positive_hits.empty else 0
                precursor_trigger_count = int(precursor_hits.sum()) if not precursor_hits.empty else 0
                abrupt_trigger_count = int(abrupt_hits.sum()) if not abrupt_hits.empty else 0
                positive_capture_rate = float(positive_capture_count / positive_case_count) if positive_case_count else 0.0
                precursor_trigger_rate = float(precursor_trigger_count / precursor_case_count) if precursor_case_count else 0.0
                abrupt_trigger_rate = float(abrupt_trigger_count / abrupt_case_count) if abrupt_case_count else 0.0
                contamination_score = precursor_trigger_rate + abrupt_trigger_rate
                rule_name = f"{rule_family}|{window_name}|{threshold:.2f}"
                rows.append(
                    {
                        "rule_name": rule_name,
                        "rule_family": rule_family,
                        "window_name": window_name,
                        "threshold": threshold,
                        "positive_case_count": positive_case_count,
                        "positive_capture_count": positive_capture_count,
                        "positive_capture_rate": positive_capture_rate,
                        "precursor_negative_case_count": precursor_case_count,
                        "precursor_negative_trigger_count": precursor_trigger_count,
                        "precursor_negative_trigger_rate": precursor_trigger_rate,
                        "abrupt_negative_case_count": abrupt_case_count,
                        "abrupt_negative_trigger_count": abrupt_trigger_count,
                        "abrupt_negative_trigger_rate": abrupt_trigger_rate,
                        "contamination_score": contamination_score,
                        "note_ko": f"양성 capture {positive_capture_count}/{positive_case_count}, contamination {contamination_score:.3f}",
                    }
                )
    return pd.DataFrame(rows).reindex(columns=SWEEP_OUTPUT_COLS)


def pick_recommended_rule(sweep_df: pd.DataFrame) -> pd.Series:
    window_rank = {"same_day": 0, "plusminus_3d": 1, "plusminus_7d": 2}
    ranked = sweep_df.copy()
    ranked["window_rank"] = ranked["window_name"].map(window_rank)
    ranked = ranked.sort_values(
        by=["positive_capture_rate", "contamination_score", "window_rank", "threshold", "rule_family"],
        ascending=[False, True, True, False, True],
        kind="mergesort",
    )
    return ranked.iloc[0]


def build_summary(sweep_df: pd.DataFrame, recommended_row: pd.Series) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in sweep_df.to_dict(orient="records"):
        is_recommended = int(normalize_text(row["rule_name"]) == normalize_text(recommended_row["rule_name"]))
        rows.append(
            {
                "summary_type": "candidate_rule",
                "rule_name": row["rule_name"],
                "rule_family": row["rule_family"],
                "window_name": row["window_name"],
                "threshold": row["threshold"],
                "positive_capture_rate": row["positive_capture_rate"],
                "contamination_score": row["contamination_score"],
                "precursor_negative_trigger_rate": row["precursor_negative_trigger_rate"],
                "abrupt_negative_trigger_rate": row["abrupt_negative_trigger_rate"],
                "recommended_rule_flag": is_recommended,
                "why_ko": (
                    "양성 capture가 가장 높고 contamination이 가장 낮은 축에 있어 추천"
                    if is_recommended == 1
                    else ""
                ),
            }
        )
    rows.append(
        {
            "summary_type": "recommended",
            "rule_name": recommended_row["rule_name"],
            "rule_family": recommended_row["rule_family"],
            "window_name": recommended_row["window_name"],
            "threshold": recommended_row["threshold"],
            "positive_capture_rate": recommended_row["positive_capture_rate"],
            "contamination_score": recommended_row["contamination_score"],
            "precursor_negative_trigger_rate": recommended_row["precursor_negative_trigger_rate"],
            "abrupt_negative_trigger_rate": recommended_row["abrupt_negative_trigger_rate"],
            "recommended_rule_flag": 1,
            "why_ko": "positive capture를 최대로 유지하면서 contamination이 최소인 규칙이라 baseline breadth marker 후보로 가장 적합",
        }
    )
    return pd.DataFrame(rows).reindex(columns=SUMMARY_OUTPUT_COLS)


def build_positive_case_output(case_features_df: pd.DataFrame, recommended_row: pd.Series) -> pd.DataFrame:
    positive_df = case_features_df.loc[case_features_df["case_group"].eq("positive")].copy()
    rule_family = normalize_text(recommended_row["rule_family"])
    window_name = normalize_text(recommended_row["window_name"])
    threshold = float(recommended_row["threshold"])
    best_rule_name = normalize_text(recommended_row["rule_name"])

    hits = positive_df.apply(compute_rule_hit, axis=1, args=(rule_family, window_name, threshold))
    positive_df["best_breadth_rule_name"] = best_rule_name
    positive_df["best_breadth_rule_hit_flag"] = hits.astype(int)

    reasons: list[str] = []
    for row in positive_df.to_dict(orient="records"):
        current_marker = to_int_flag(row["current_marker_any_flag"])
        best_hit = to_int_flag(row["best_breadth_rule_hit_flag"])
        if current_marker == 0 and best_hit == 1:
            reasons.append("current marker는 비어 있지만 추천 breadth rule은 capture하여 breadth routing 후보로 의미가 있음")
        elif current_marker == 1 and best_hit == 1:
            reasons.append("current marker와 breadth rule이 함께 capture하여 routing 보강 후보로 해석 가능")
        else:
            reasons.append("추천 breadth rule로도 포착되지 않아 common-cause bucket을 아직 descriptive에 가깝게 봐야 함")
    positive_df["breadth_reason_ko"] = reasons

    return positive_df.reindex(columns=CASES_OUTPUT_COLS)


def write_outputs(root: Path, summary_df: pd.DataFrame, cases_df: pd.DataFrame, sweep_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    cases_df.to_csv(share_dir / CASES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    sweep_df.to_csv(share_dir / SWEEP_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    case_universe_df = load_case_universe(root)
    core_df, gate_df = load_site_windows(root, case_universe_df)
    site_daily_df = aggregate_site_daily(core_df, gate_df)
    case_features_df = build_case_feature_frame(case_universe_df, site_daily_df)
    sweep_df = build_threshold_sweep(case_features_df)
    recommended_row = pick_recommended_rule(sweep_df)
    summary_df = build_summary(sweep_df, recommended_row)
    cases_output_df = build_positive_case_output(case_features_df, recommended_row)
    write_outputs(root, summary_df, cases_output_df, sweep_df)


if __name__ == "__main__":
    main()
