#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

EVAL_BUCKETS_NAME = "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv"
ONSET_TRUTH_NAME = "panel_day_engine_precursor_onset_truth_v1.csv"
ONSET_LADDER_NAME = "panel_day_engine_precursor_onset_ladder_v1.csv"
ELIGIBILITY_CASES_NAME = "panel_day_engine_local_precursor_eligibility_cases_v1.csv"
FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME = "panel_day_engine_fault_panel_event_audit_summary_v1.csv"

CASES_OUTPUT_NAME = "panel_day_engine_precursor_performance_cases_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_precursor_performance_summary_v1.csv"
MARKER_COMPARISON_OUTPUT_NAME = "panel_day_engine_precursor_performance_marker_comparison_v1.csv"

MARKERS = [
    "first_cond_evt",
    "first_cond_evt_corroborated",
    "first_signalcount2",
    "first_pre_ews",
    "first_ews_warning",
    "first_pre_alarm",
]

ALLOWED_CAPTURE_CLASSES = {
    "exact_or_earlier",
    "within_3d_late",
    "within_7d_late",
    "late_over_7d",
    "missing",
}

REQUIRED_EVAL_BUCKETS_COLS = [
    "fault_family_id",
    "eval_bucket_v2",
]
REQUIRED_ONSET_TRUTH_COLS = [
    "site",
    "panel_id",
    "fault_start_date",
    "vendor_fault_family",
    "temporality_class",
    "operational_first_precursor_detected_date",
    "operational_first_precursor_marker_name",
    "operational_lead_days_to_fault_start",
    "interpretive_precursor_onset_date",
    "interpretive_lead_days_to_fault_start",
    "benchmark_precursor_onset_date",
    "benchmark_lead_days_to_fault_start",
    "preferred_precursor_onset_date",
    "preferred_onset_stage",
    "preferred_onset_confidence",
]
REQUIRED_ONSET_LADDER_COLS = [
    "site",
    "panel_id",
    "fault_start_date",
    "onset_marker",
    "onset_date",
    "lead_days",
    "available_flag",
]
REQUIRED_ELIGIBILITY_COLS = [
    "site",
    "panel_id",
    "fault_start_date",
    "vendor_fault_family",
    "temporality_class",
    "precursor_eligible_flag",
]
REQUIRED_FAULT_PANEL_EVENT_AUDIT_SUMMARY_COLS = ["사건유형_재판정_전조형수"]

EXPECTED_PRECURSOR_BENCHMARK_SUPPORT = 3
FORENSIC_PRECURSOR_PANEL_ID = "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"

SUMMARY_OUTPUT_COLS = [
    "marker_name",
    "case_count",
    "available_case_count",
    "available_rate",
    "median_lead_days",
    "min_lead_days",
    "max_lead_days",
    "median_onset_capture_gap_days",
    "exact_or_earlier_count",
    "within_3d_late_count",
    "within_7d_late_count",
    "late_over_7d_count",
    "missing_count",
    "exact_or_earlier_rate",
    "exact_or_earlier_plus_within_3d_rate",
]

MARKER_COMPARISON_OUTPUT_COLS = [
    "marker_name",
    "available_rate",
    "median_lead_days",
    "exact_or_earlier_rate",
    "exact_or_earlier_plus_within_3d_rate",
    "available_rate_rank",
    "median_lead_days_rank",
    "exact_or_earlier_rate_rank",
    "exact_or_earlier_plus_within_3d_rate_rank",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit precursor performance for precursor-bearing detectable-now cases only."
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


def classify_gap_days(gap_days: int | None) -> str:
    if gap_days is None:
        return "missing"
    if gap_days <= 0:
        return "exact_or_earlier"
    if gap_days <= 3:
        return "within_3d_late"
    if gap_days <= 7:
        return "within_7d_late"
    return "late_over_7d"


def compute_gap_days(marker_date: pd.Timestamp | pd.NaT, preferred_onset_date: pd.Timestamp | pd.NaT) -> int | None:
    if pd.isna(marker_date) or pd.isna(preferred_onset_date):
        return None
    return int((pd.Timestamp(marker_date) - pd.Timestamp(preferred_onset_date)).days)


def load_eval_bucket_map(root: Path) -> dict[str, str]:
    path = root / "_share" / EVAL_BUCKETS_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_EVAL_BUCKETS_COLS, path.name)
    df["fault_family_id"] = df["fault_family_id"].map(normalize_text)
    df["eval_bucket_v2"] = df["eval_bucket_v2"].map(normalize_text)
    return dict(zip(df["fault_family_id"], df["eval_bucket_v2"]))


def load_onset_truth(root: Path) -> pd.DataFrame:
    path = root / "_share" / ONSET_TRUTH_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_ONSET_TRUTH_COLS, path.name)
    for col in ["site", "panel_id", "vendor_fault_family", "temporality_class", "preferred_onset_stage", "preferred_onset_confidence"]:
        df[col] = df[col].map(normalize_text)
    for col in [
        "fault_start_date",
        "operational_first_precursor_detected_date",
        "interpretive_precursor_onset_date",
        "benchmark_precursor_onset_date",
        "preferred_precursor_onset_date",
    ]:
        df[col] = df[col].map(normalize_date_text)
    for col in [
        "operational_first_precursor_marker_name",
    ]:
        df[col] = df[col].map(normalize_text)
    for col in [
        "operational_lead_days_to_fault_start",
        "interpretive_lead_days_to_fault_start",
        "benchmark_lead_days_to_fault_start",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_eligibility(root: Path) -> pd.DataFrame:
    path = root / "_share" / ELIGIBILITY_CASES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_ELIGIBILITY_COLS, path.name)
    for col in ["site", "panel_id", "vendor_fault_family", "temporality_class"]:
        df[col] = df[col].map(normalize_text)
    df["fault_start_date"] = df["fault_start_date"].map(normalize_date_text)
    df["precursor_eligible_flag"] = df["precursor_eligible_flag"].map(to_int_flag).astype(int)
    return df.loc[:, REQUIRED_ELIGIBILITY_COLS].drop_duplicates(subset=["site", "panel_id", "fault_start_date"], keep="first")


def load_onset_ladder(root: Path) -> pd.DataFrame:
    path = root / "_share" / ONSET_LADDER_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_ONSET_LADDER_COLS, path.name)
    for col in ["site", "panel_id", "onset_marker"]:
        df[col] = df[col].map(normalize_text)
    for col in ["fault_start_date", "onset_date"]:
        df[col] = df[col].map(normalize_date_text)
    df["available_flag"] = df["available_flag"].map(to_int_flag).astype(int)
    df["lead_days"] = pd.to_numeric(df["lead_days"], errors="coerce")
    return df.loc[df["onset_marker"].isin(MARKERS)].copy()


def load_fault_event_summary(root: Path) -> dict[str, int]:
    path = root / "_share" / FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_FAULT_PANEL_EVENT_AUDIT_SUMMARY_COLS, path.name)
    if len(df) != 1:
        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME} must contain exactly one row, found {len(df)}")
    precursor_count = numeric_int(df.iloc[0]["사건유형_재판정_전조형수"])
    if precursor_count != EXPECTED_PRECURSOR_BENCHMARK_SUPPORT:
        raise SystemExit(
            f"audited precursor benchmark support must be {EXPECTED_PRECURSOR_BENCHMARK_SUPPORT}, found {precursor_count}"
        )
    return {"precursor_benchmark_count": precursor_count}


def build_eval_universe(onset_truth_df: pd.DataFrame, expected_support: int) -> pd.DataFrame:
    universe = onset_truth_df.loc[onset_truth_df["preferred_precursor_onset_date"].map(normalize_text).ne("")].copy()
    universe = universe.reset_index(drop=True)
    if len(universe) != expected_support:
        raise SystemExit(
            f"precursor benchmark support after onset reset must be {expected_support}, found {len(universe)}"
        )
    benchmark_keys = {(normalize_text(row["site"]), normalize_text(row["panel_id"])) for row in universe.to_dict(orient="records")}
    if ("conalog", FORENSIC_PRECURSOR_PANEL_ID) not in benchmark_keys:
        raise SystemExit("c42997 must appear in rebuilt precursor performance benchmark universe")
    return universe


def build_cases_output(universe_df: pd.DataFrame, ladder_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    ladder_lookup = {
        (
            normalize_text(row["site"]),
            normalize_text(row["panel_id"]),
            normalize_text(row["fault_start_date"]),
            normalize_text(row["onset_marker"]),
        ): row
        for row in ladder_df.to_dict(orient="records")
    }

    for case in universe_df.to_dict(orient="records"):
        preferred_onset_ts = parse_timestamp(case["preferred_precursor_onset_date"])
        row = {
            "site": normalize_text(case["site"]),
            "panel_id": normalize_text(case["panel_id"]),
            "fault_start_date": normalize_text(case["fault_start_date"]),
            "vendor_fault_family": normalize_text(case["vendor_fault_family"]),
            "operational_first_precursor_detected_date": normalize_text(case["operational_first_precursor_detected_date"]),
            "operational_first_precursor_marker_name": normalize_text(case["operational_first_precursor_marker_name"]),
            "operational_lead_days_to_fault_start": pd.to_numeric(pd.Series([case["operational_lead_days_to_fault_start"]]), errors="coerce").iloc[0],
            "interpretive_precursor_onset_date": normalize_text(case["interpretive_precursor_onset_date"]),
            "interpretive_lead_days_to_fault_start": pd.to_numeric(pd.Series([case["interpretive_lead_days_to_fault_start"]]), errors="coerce").iloc[0],
            "benchmark_precursor_onset_date": normalize_text(case["benchmark_precursor_onset_date"]) or normalize_text(case["preferred_precursor_onset_date"]),
            "benchmark_lead_days_to_fault_start": pd.to_numeric(pd.Series([case["benchmark_lead_days_to_fault_start"]]), errors="coerce").iloc[0],
            "preferred_precursor_onset_date": normalize_text(case["preferred_precursor_onset_date"]),
            "preferred_onset_stage": normalize_text(case["preferred_onset_stage"]),
            "preferred_onset_confidence": normalize_text(case["preferred_onset_confidence"]),
        }
        for marker in MARKERS:
            ladder_row = ladder_lookup.get((row["site"], row["panel_id"], row["fault_start_date"], marker), {})
            marker_available_flag = to_int_flag(ladder_row.get("available_flag", 0))
            marker_date_text = normalize_text(ladder_row.get("onset_date", ""))
            marker_date_ts = parse_timestamp(marker_date_text)
            lead_days = pd.to_numeric(pd.Series([ladder_row.get("lead_days")]), errors="coerce").iloc[0]
            onset_capture_gap_days = compute_gap_days(marker_date_ts, preferred_onset_ts)
            onset_capture_class = classify_gap_days(onset_capture_gap_days)
            row[f"{marker}_available_flag"] = marker_available_flag
            row[f"{marker}_marker_date"] = marker_date_text
            row[f"{marker}_lead_days"] = float(lead_days) if not pd.isna(lead_days) else None
            row[f"{marker}_onset_capture_gap_days"] = onset_capture_gap_days
            row[f"{marker}_onset_capture_class"] = onset_capture_class
        rows.append(row)
    return pd.DataFrame(rows)


def numeric_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return 0
    return int(numeric)


def summarize_numeric(series: pd.Series) -> tuple[float | None, float | None, float | None]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return (None, None, None)
    return (float(values.median()), float(values.min()), float(values.max()))


def build_summary(cases_df: pd.DataFrame) -> pd.DataFrame:
    case_count = int(len(cases_df))
    rows: list[dict[str, object]] = []
    for marker in MARKERS:
        available_flag_col = f"{marker}_available_flag"
        lead_col = f"{marker}_lead_days"
        gap_col = f"{marker}_onset_capture_gap_days"
        class_col = f"{marker}_onset_capture_class"

        available_case_count = int(cases_df[available_flag_col].map(to_int_flag).sum()) if case_count else 0
        median_lead_days, min_lead_days, max_lead_days = summarize_numeric(cases_df[lead_col]) if case_count else (None, None, None)
        median_gap_days, _, _ = summarize_numeric(cases_df[gap_col]) if case_count else (None, None, None)

        counts = {capture_class: int(cases_df[class_col].eq(capture_class).sum()) if case_count else 0 for capture_class in ALLOWED_CAPTURE_CLASSES}
        exact_or_earlier_rate = (counts["exact_or_earlier"] / case_count) if case_count else 0.0
        exact_or_earlier_plus_within_3d_rate = (
            (counts["exact_or_earlier"] + counts["within_3d_late"]) / case_count
        ) if case_count else 0.0

        rows.append(
            {
                "marker_name": marker,
                "case_count": case_count,
                "available_case_count": available_case_count,
                "available_rate": (available_case_count / case_count) if case_count else 0.0,
                "median_lead_days": median_lead_days,
                "min_lead_days": min_lead_days,
                "max_lead_days": max_lead_days,
                "median_onset_capture_gap_days": median_gap_days,
                "exact_or_earlier_count": counts["exact_or_earlier"],
                "within_3d_late_count": counts["within_3d_late"],
                "within_7d_late_count": counts["within_7d_late"],
                "late_over_7d_count": counts["late_over_7d"],
                "missing_count": counts["missing"],
                "exact_or_earlier_rate": exact_or_earlier_rate,
                "exact_or_earlier_plus_within_3d_rate": exact_or_earlier_plus_within_3d_rate,
            }
        )
    return pd.DataFrame(rows).reindex(columns=SUMMARY_OUTPUT_COLS)


def comparison_note(row: pd.Series) -> str:
    available_rate = float(row["available_rate"]) if not pd.isna(row["available_rate"]) else 0.0
    close_rate = float(row["exact_or_earlier_plus_within_3d_rate"]) if not pd.isna(row["exact_or_earlier_plus_within_3d_rate"]) else 0.0
    exact_rate = float(row["exact_or_earlier_rate"]) if not pd.isna(row["exact_or_earlier_rate"]) else 0.0
    if available_rate == 1.0 and close_rate == 1.0:
        return "coverage와 onset 정렬이 가장 안정적임"
    if available_rate < 0.5:
        return "coverage가 낮아 단독 marker로는 불충분함"
    if exact_rate == 1.0:
        return "preferred onset과 거의 같은 시점에 잡힘"
    if close_rate >= 0.5:
        return "preferred onset 대비 약간 늦지만 실용적 비교 대상"
    return "late or missing 비중이 높아 보조 marker로 해석"


def build_marker_comparison(summary_df: pd.DataFrame) -> pd.DataFrame:
    if summary_df.empty:
        return pd.DataFrame(columns=MARKER_COMPARISON_OUTPUT_COLS)
    comparison_df = summary_df.copy()
    comparison_df["available_rate_rank"] = comparison_df["available_rate"].rank(method="min", ascending=False).astype(int)
    comparison_df["median_lead_days_rank"] = comparison_df["median_lead_days"].rank(method="min", ascending=False, na_option="bottom").astype(int)
    comparison_df["exact_or_earlier_rate_rank"] = comparison_df["exact_or_earlier_rate"].rank(method="min", ascending=False).astype(int)
    comparison_df["exact_or_earlier_plus_within_3d_rate_rank"] = (
        comparison_df["exact_or_earlier_plus_within_3d_rate"].rank(method="min", ascending=False).astype(int)
    )
    comparison_df["note_ko"] = comparison_df.apply(comparison_note, axis=1)
    comparison_df = comparison_df.sort_values(
        [
            "exact_or_earlier_plus_within_3d_rate_rank",
            "available_rate_rank",
            "median_lead_days_rank",
            "marker_name",
        ]
    ).reset_index(drop=True)
    return comparison_df.loc[:, MARKER_COMPARISON_OUTPUT_COLS]


def write_outputs(root: Path, cases_df: pd.DataFrame, summary_df: pd.DataFrame, comparison_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    cases_df.to_csv(share_dir / CASES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    comparison_df.to_csv(share_dir / MARKER_COMPARISON_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    onset_truth_df = load_onset_truth(root)
    ladder_df = load_onset_ladder(root)
    fault_event_summary = load_fault_event_summary(root)

    universe_df = build_eval_universe(onset_truth_df, fault_event_summary["precursor_benchmark_count"])
    cases_df = build_cases_output(universe_df, ladder_df)
    summary_df = build_summary(cases_df)
    comparison_df = build_marker_comparison(summary_df)
    write_outputs(root, cases_df, summary_df, comparison_df)


if __name__ == "__main__":
    main()
