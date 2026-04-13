#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

NON_PRECURSOR_CASES_NAME = "panel_day_engine_non_precursor_performance_cases_v1.csv"
NON_PRECURSOR_SUMMARY_NAME = "panel_day_engine_non_precursor_performance_summary_v1.csv"
RETROFIT_RECOMMENDATION_NAME = "panel_day_engine_common_cause_breadth_retrofit_recommendation_v1.csv"
RETROFIT_SUMMARY_NAME = "panel_day_engine_common_cause_breadth_retrofit_summary_v1.csv"
PRECURSOR_ONSET_TRUTH_NAME = "panel_day_engine_precursor_onset_truth_v1.csv"
EVAL_BUCKETS_NAME = "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv"
PANEL_DAY_CORE_NAME = "panel_day_core.csv"
GATE_DAILY_NAME = "ae_simple_local_precursor_gate_daily.csv"

CASES_OUTPUT_NAME = "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_common_cause_descriptive_retrofit_summary_v1.csv"
COMPARISON_OUTPUT_NAME = "panel_day_engine_common_cause_descriptive_retrofit_comparison_v1.csv"

NON_PANEL_BUCKET = "non_panel_or_common_cause"
ABRUPT_BUCKET = "abrupt_or_no_precursor_now"
PRECURSOR_BUCKET = "precursor_bearing_detectable_now"

WINDOW_NAME_TO_SUFFIX = {
    "same_day": "same_day",
    "plusminus_3d": "3d",
    "plusminus_7d": "7d",
}
WINDOW_NAME_TO_DAYS = {
    "same_day": 0,
    "plusminus_3d": 3,
    "plusminus_7d": 7,
}
RULE_FAMILY_FEATURES = {
    "final_fault_breadth_threshold": ["final_fault"],
    "pre_alarm_breadth_threshold": ["pre_alarm"],
    "ews_warning_breadth_threshold": ["ews_warning"],
    "any_breadth_threshold": ["final_fault", "pre_alarm", "ews_warning"],
}

REQUIRED_NON_PRECURSOR_CASES_COLS = [
    "eval_bucket_v2",
    "site",
    "panel_id",
    "anchor_date",
    "truth_case_id",
]
REQUIRED_NON_PRECURSOR_SUMMARY_COLS = [
    "eval_bucket_v2",
    "case_count",
    "common_cause_like_rate",
]
REQUIRED_RECOMMENDATION_COLS = ["recommended_rule_name"]
REQUIRED_RETROFIT_SUMMARY_COLS = ["rule_name", "positive_capture_rate", "contamination_score", "triggered_site_day_rate"]
REQUIRED_ONSET_TRUTH_COLS = [
    "site",
    "panel_id",
    "fault_start_date",
    "vendor_fault_family",
    "temporality_class",
]
REQUIRED_EVAL_COLS = ["fault_family_id", "eval_bucket_v2"]
CORE_REQUESTED_COLS = ["panel_id", "date", "final_fault", "group_off_like", "shadow_like"]
GATE_REQUESTED_COLS = ["panel_id", "date", "group_off_date", "ews_warning", "pre_alarm"]

CASES_OUTPUT_COLS = [
    "eval_bucket_v2",
    "site",
    "panel_id",
    "anchor_date",
    "truth_case_id",
    "current_marker_only_flag",
    "breadth_marker_only_flag",
    "combined_marker_flag",
    "explanation_mode_class",
    "retrofit_reason_ko",
]

SUMMARY_OUTPUT_COLS = [
    "eval_bucket_v2",
    "case_count",
    "current_marker_explained_count",
    "current_marker_explained_rate",
    "breadth_marker_explained_count",
    "breadth_marker_explained_rate",
    "combined_marker_explained_count",
    "combined_marker_explained_rate",
    "combined_increment_vs_current",
]

COMPARISON_OUTPUT_COLS = [
    "bucket_name",
    "current_marker_explained_rate",
    "breadth_marker_explained_rate",
    "combined_marker_explained_rate",
    "combined_increment_vs_current",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the selected breadth-based common-cause marker as a descriptive step-4 retrofit."
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


def load_recommended_rule(root: Path) -> tuple[str, str, float, dict[str, object]]:
    rec_path = root / "_share" / RETROFIT_RECOMMENDATION_NAME
    rec_df = drop_repeated_header_rows(read_csv(rec_path))
    ensure_columns(rec_df, REQUIRED_RECOMMENDATION_COLS, rec_path.name)
    if len(rec_df) != 1:
        raise SystemExit(f"{rec_path.name} must contain exactly one recommended rule row")
    rule_name = normalize_text(rec_df.iloc[0]["recommended_rule_name"])
    parts = rule_name.split("|")
    if len(parts) != 3:
        raise SystemExit(f"unexpected recommended rule format: {rule_name}")
    rule_family, window_name, threshold_text = parts
    threshold = float(threshold_text)

    retrofit_summary_path = root / "_share" / RETROFIT_SUMMARY_NAME
    retrofit_summary_df = drop_repeated_header_rows(read_csv(retrofit_summary_path))
    ensure_columns(retrofit_summary_df, REQUIRED_RETROFIT_SUMMARY_COLS, retrofit_summary_path.name)
    retrofit_summary_df["rule_name"] = retrofit_summary_df["rule_name"].map(normalize_text)
    matched = retrofit_summary_df.loc[retrofit_summary_df["rule_name"].eq(rule_name)].copy()
    if matched.empty:
        raise SystemExit(f"recommended rule not found in {retrofit_summary_path.name}: {rule_name}")
    meta = matched.iloc[0].to_dict()
    return rule_name, rule_family, window_name, threshold, meta


def load_case_universe(root: Path, eval_bucket_map: dict[str, str]) -> pd.DataFrame:
    cases_path = root / "_share" / NON_PRECURSOR_CASES_NAME
    cases_df = drop_repeated_header_rows(read_csv(cases_path))
    ensure_columns(cases_df, REQUIRED_NON_PRECURSOR_CASES_COLS, cases_path.name)
    for col in REQUIRED_NON_PRECURSOR_CASES_COLS:
        cases_df[col] = cases_df[col].map(normalize_text)
    cases_df = cases_df.loc[cases_df["eval_bucket_v2"].isin([NON_PANEL_BUCKET, ABRUPT_BUCKET])].copy()
    cases_df = cases_df.loc[:, ["eval_bucket_v2", "site", "panel_id", "anchor_date", "truth_case_id"]]

    onset_path = root / "_share" / PRECURSOR_ONSET_TRUTH_NAME
    onset_df = drop_repeated_header_rows(read_csv(onset_path))
    ensure_columns(onset_df, REQUIRED_ONSET_TRUTH_COLS, onset_path.name)
    for col in REQUIRED_ONSET_TRUTH_COLS:
        onset_df[col] = onset_df[col].map(normalize_text)
    onset_df["fault_family_id"] = onset_df.apply(
        lambda row: derive_fault_family_id(row["vendor_fault_family"], row["temporality_class"]),
        axis=1,
    )
    onset_df["eval_bucket_v2"] = onset_df["fault_family_id"].map(lambda value: normalize_text(eval_bucket_map.get(value, "")))
    onset_df = onset_df.loc[onset_df["eval_bucket_v2"].eq(PRECURSOR_BUCKET)].copy()
    onset_df["anchor_date"] = onset_df["fault_start_date"]
    onset_df["truth_case_id"] = (
        "onset|"
        + onset_df["site"].astype(str)
        + "|"
        + onset_df["panel_id"].astype(str)
        + "|"
        + onset_df["fault_start_date"].astype(str)
    )
    onset_df = onset_df.loc[:, ["eval_bucket_v2", "site", "panel_id", "anchor_date", "truth_case_id"]]

    combined = pd.concat([cases_df, onset_df], ignore_index=True)
    for col in ["eval_bucket_v2", "site", "panel_id", "anchor_date", "truth_case_id"]:
        combined[col] = combined[col].map(normalize_text)
    return combined.drop_duplicates(subset=["truth_case_id"], keep="first").reset_index(drop=True)


def load_baseline_summary(root: Path) -> dict[str, dict[str, object]]:
    path = root / "_share" / NON_PRECURSOR_SUMMARY_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_NON_PRECURSOR_SUMMARY_COLS, path.name)
    df["eval_bucket_v2"] = df["eval_bucket_v2"].map(normalize_text)
    return {row["eval_bucket_v2"]: row for row in df.to_dict(orient="records")}


def load_site_windows(root: Path, cases_df: pd.DataFrame, selected_window_days: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    load_window_days = max(selected_window_days, 3)
    core_frames: list[pd.DataFrame] = []
    gate_frames: list[pd.DataFrame] = []
    for site, site_cases in cases_df.groupby("site"):
        anchor_dates = site_cases["anchor_date"].map(parse_timestamp)
        site_window_start = anchor_dates.min() - pd.Timedelta(days=load_window_days)
        site_window_end = anchor_dates.max() + pd.Timedelta(days=load_window_days)
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
            for col in ["final_fault", "group_off_like", "shadow_like"]:
                if col not in core_df.columns:
                    core_df[col] = 0
                core_df[col] = core_df[col].map(to_int_flag).astype(int)
            core_frames.append(core_df.loc[:, ["site", "panel_id", "date", "final_fault", "group_off_like", "shadow_like"]])
        if not gate_df.empty:
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


def aggregate_frames(core_df: pd.DataFrame, gate_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    core_panel = (
        core_df.groupby(["site", "panel_id", "date"], as_index=False)[["final_fault", "group_off_like", "shadow_like"]].max()
        if not core_df.empty
        else pd.DataFrame(columns=["site", "panel_id", "date", "final_fault", "group_off_like", "shadow_like"])
    )
    gate_panel = (
        gate_df.groupby(["site", "panel_id", "date"], as_index=False)[["group_off_date", "ews_warning", "pre_alarm"]].max()
        if not gate_df.empty
        else pd.DataFrame(columns=["site", "panel_id", "date", "group_off_date", "ews_warning", "pre_alarm"])
    )
    panel_daily = core_panel.merge(gate_panel, how="outer", on=["site", "panel_id", "date"])
    for col in ["final_fault", "group_off_like", "shadow_like", "group_off_date", "ews_warning", "pre_alarm"]:
        if col not in panel_daily.columns:
            panel_daily[col] = 0
        panel_daily[col] = panel_daily[col].fillna(0).map(to_int_flag).astype(int)
    panel_daily["group_off_like_effective"] = panel_daily[["group_off_like", "group_off_date"]].max(axis=1)

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
    return panel_daily, site_daily


def build_site_feature_frame(site_daily_df: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for site, scoped_df in site_daily_df.groupby("site"):
        scoped_df = scoped_df.sort_values("date").reset_index(drop=True)
        full_index = pd.date_range(scoped_df["date"].min(), scoped_df["date"].max(), freq="D")
        full_df = pd.DataFrame({"date": full_index}).merge(scoped_df, how="left", on="date")
        full_df["site"] = site
        for base_col in [
            "site_panel_count_on_date",
            "final_fault_panel_fraction_on_date",
            "pre_alarm_panel_fraction_on_date",
            "ews_warning_panel_fraction_on_date",
        ]:
            full_df[base_col] = pd.to_numeric(full_df[base_col], errors="coerce").fillna(0)

        for feature in ["final_fault", "pre_alarm", "ews_warning"]:
            source_col = f"{feature}_panel_fraction_on_date"
            full_df[f"max_{feature}_panel_fraction_same_day"] = full_df[source_col]
            full_df[f"max_{feature}_panel_fraction_3d"] = (
                full_df[source_col].rolling(window=7, center=True, min_periods=1).max()
            )
            full_df[f"max_{feature}_panel_fraction_7d"] = (
                full_df[source_col].rolling(window=15, center=True, min_periods=1).max()
            )
        frames.append(full_df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def compute_breadth_flag(site_feature_row: pd.Series, rule_family: str, window_name: str, threshold: float) -> int:
    suffix = WINDOW_NAME_TO_SUFFIX[window_name]
    values = [
        float(site_feature_row[f"max_{feature}_panel_fraction_{suffix}"])
        for feature in RULE_FAMILY_FEATURES[rule_family]
    ]
    return int(max(values) >= threshold)


def build_case_output(
    cases_df: pd.DataFrame,
    panel_daily_df: pd.DataFrame,
    site_feature_df: pd.DataFrame,
    rule_family: str,
    window_name: str,
    threshold: float,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for case in cases_df.to_dict(orient="records"):
        site = normalize_text(case["site"])
        panel_id = normalize_text(case["panel_id"])
        anchor_text = normalize_text(case["anchor_date"])
        anchor_ts = parse_timestamp(anchor_text)

        panel_window = panel_daily_df.loc[
            panel_daily_df["site"].eq(site)
            & panel_daily_df["panel_id"].eq(panel_id)
            & panel_daily_df["date"].ge(anchor_ts - pd.Timedelta(days=3))
            & panel_daily_df["date"].le(anchor_ts + pd.Timedelta(days=3))
        ].copy()
        current_marker_flag = int(
            panel_window["group_off_like_effective"].sum() > 0 or panel_window["shadow_like"].sum() > 0
        )

        site_feature_row_df = site_feature_df.loc[
            site_feature_df["site"].eq(site) & site_feature_df["date"].eq(anchor_ts)
        ]
        if site_feature_row_df.empty:
            breadth_marker_flag = 0
        else:
            breadth_marker_flag = compute_breadth_flag(site_feature_row_df.iloc[0], rule_family, window_name, threshold)
        combined_flag = int(current_marker_flag == 1 or breadth_marker_flag == 1)

        if current_marker_flag == 1 and breadth_marker_flag == 0:
            mode = "current_only"
            reason = "기존 current marker만으로 설명되는 case"
        elif current_marker_flag == 0 and breadth_marker_flag == 1:
            mode = "breadth_only"
            reason = "선택된 breadth marker가 새로 설명을 추가한 case"
        elif current_marker_flag == 1 and breadth_marker_flag == 1:
            mode = "both"
            reason = "current marker와 breadth marker가 모두 설명하는 case"
        else:
            mode = "neither"
            reason = "current/breadth 모두로도 설명되지 않아 descriptive review가 더 필요함"

        rows.append(
            {
                "eval_bucket_v2": normalize_text(case["eval_bucket_v2"]),
                "site": site,
                "panel_id": panel_id,
                "anchor_date": anchor_text,
                "truth_case_id": normalize_text(case["truth_case_id"]),
                "current_marker_only_flag": current_marker_flag,
                "breadth_marker_only_flag": breadth_marker_flag,
                "combined_marker_flag": combined_flag,
                "explanation_mode_class": mode,
                "retrofit_reason_ko": reason,
            }
        )
    return pd.DataFrame(rows).reindex(columns=CASES_OUTPUT_COLS)


def safe_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator)


def build_summary(case_output_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for bucket in [NON_PANEL_BUCKET, ABRUPT_BUCKET, PRECURSOR_BUCKET]:
        scoped_df = case_output_df.loc[case_output_df["eval_bucket_v2"].eq(bucket)].copy()
        case_count = int(len(scoped_df))
        current_count = int(scoped_df["current_marker_only_flag"].map(to_int_flag).sum()) if case_count else 0
        breadth_count = int(scoped_df["breadth_marker_only_flag"].map(to_int_flag).sum()) if case_count else 0
        combined_count = int(scoped_df["combined_marker_flag"].map(to_int_flag).sum()) if case_count else 0
        current_rate = safe_rate(current_count, case_count)
        breadth_rate = safe_rate(breadth_count, case_count)
        combined_rate = safe_rate(combined_count, case_count)
        rows.append(
            {
                "eval_bucket_v2": bucket,
                "case_count": case_count,
                "current_marker_explained_count": current_count,
                "current_marker_explained_rate": current_rate,
                "breadth_marker_explained_count": breadth_count,
                "breadth_marker_explained_rate": breadth_rate,
                "combined_marker_explained_count": combined_count,
                "combined_marker_explained_rate": combined_rate,
                "combined_increment_vs_current": combined_rate - current_rate,
            }
        )
    return pd.DataFrame(rows).reindex(columns=SUMMARY_OUTPUT_COLS)


def build_comparison(summary_df: pd.DataFrame, baseline_summary_map: dict[str, dict[str, object]], recommended_rule_name: str, retrofit_meta: dict[str, object]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in summary_df.to_dict(orient="records"):
        bucket = normalize_text(row["eval_bucket_v2"])
        current_rate = float(row["current_marker_explained_rate"])
        combined_rate = float(row["combined_marker_explained_rate"])
        increment = float(row["combined_increment_vs_current"])
        if bucket == NON_PANEL_BUCKET:
            baseline_rate = pd.to_numeric(pd.Series([baseline_summary_map.get(bucket, {}).get("common_cause_like_rate", 0)]), errors="coerce").iloc[0]
            baseline_rate = 0.0 if pd.isna(baseline_rate) else float(baseline_rate)
            note = (
                f"step4 baseline current marker rate {baseline_rate:.3f}에서 selected breadth rule "
                f"{recommended_rule_name}를 합치면 {combined_rate:.3f}까지 설명률이 오른다."
            )
        elif bucket == ABRUPT_BUCKET:
            note = "abrupt bucket에서 combined 설명률이 0으로 유지되면 descriptive retrofit contamination이 없다."
        else:
            note = (
                "precursor bucket에서 combined 설명률이 0으로 유지되면 retrofit summary의 zero contamination "
                f"(triggered_site_day_rate={float(retrofit_meta.get('triggered_site_day_rate', 0.0)):.3f})와 정렬된다."
            )
        rows.append(
            {
                "bucket_name": bucket,
                "current_marker_explained_rate": current_rate,
                "breadth_marker_explained_rate": float(row["breadth_marker_explained_rate"]),
                "combined_marker_explained_rate": combined_rate,
                "combined_increment_vs_current": increment,
                "note_ko": note,
            }
        )
    return pd.DataFrame(rows).reindex(columns=COMPARISON_OUTPUT_COLS)


def write_outputs(root: Path, cases_df: pd.DataFrame, summary_df: pd.DataFrame, comparison_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    cases_df.to_csv(share_dir / CASES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    comparison_df.to_csv(share_dir / COMPARISON_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    eval_bucket_map = load_eval_bucket_map(root)
    recommended_rule_name, rule_family, window_name, threshold, retrofit_meta = load_recommended_rule(root)
    cases_df = load_case_universe(root, eval_bucket_map)
    baseline_summary_map = load_baseline_summary(root)
    core_df, gate_df = load_site_windows(root, cases_df, WINDOW_NAME_TO_DAYS[window_name])
    panel_daily_df, site_daily_df = aggregate_frames(core_df, gate_df)
    site_feature_df = build_site_feature_frame(site_daily_df)
    case_output_df = build_case_output(
        cases_df,
        panel_daily_df,
        site_feature_df,
        rule_family,
        window_name,
        threshold,
    )
    summary_df = build_summary(case_output_df)
    comparison_df = build_comparison(summary_df, baseline_summary_map, recommended_rule_name, retrofit_meta)
    write_outputs(root, case_output_df, summary_df, comparison_df)


if __name__ == "__main__":
    main()
