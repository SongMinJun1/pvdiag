#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SWEEP_NAME = "panel_day_engine_common_cause_breadth_marker_threshold_sweep_v1.csv"
CASES_NAME = "panel_day_engine_common_cause_breadth_marker_cases_v1.csv"
EVAL_BUCKETS_NAME = "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv"
REAUDIT_NAME = "panel_date_reaudit_working.csv"
ELIGIBILITY_NAME = "panel_day_engine_local_precursor_eligibility_cases_v1.csv"
PRECURSOR_ONSET_TRUTH_NAME = "panel_day_engine_precursor_onset_truth_v1.csv"
PANEL_DAY_CORE_NAME = "panel_day_core.csv"
GATE_DAILY_NAME = "ae_simple_local_precursor_gate_daily.csv"

SUMMARY_OUTPUT_NAME = "panel_day_engine_common_cause_breadth_retrofit_summary_v1.csv"
PREVALENCE_OUTPUT_NAME = "panel_day_engine_common_cause_breadth_retrofit_prevalence_v1.csv"
RECOMMENDATION_OUTPUT_NAME = "panel_day_engine_common_cause_breadth_retrofit_recommendation_v1.csv"

PRECURSOR_BUCKET = "precursor_bearing_detectable_now"
ABRUPT_BUCKET = "abrupt_or_no_precursor_now"

MINIMUM_RULES_IF_PRESENT = {
    "final_fault_breadth_threshold|same_day|0.05",
    "final_fault_breadth_threshold|plusminus_3d|0.10",
    "any_breadth_threshold|same_day|0.05",
    "any_breadth_threshold|plusminus_3d|0.10",
}

RULE_FAMILY_FEATURES = {
    "final_fault_breadth_threshold": ["final_fault"],
    "pre_alarm_breadth_threshold": ["pre_alarm"],
    "ews_warning_breadth_threshold": ["ews_warning"],
    "any_breadth_threshold": ["final_fault", "pre_alarm", "ews_warning"],
}
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
SOURCE_COMPLEXITY_RANK = {
    "final_fault_breadth_threshold": 1,
    "pre_alarm_breadth_threshold": 2,
    "ews_warning_breadth_threshold": 3,
    "any_breadth_threshold": 4,
}
WINDOW_COMPLEXITY_RANK = {
    "same_day": 1,
    "plusminus_3d": 2,
    "plusminus_7d": 3,
}

REQUIRED_SWEEP_COLS = [
    "rule_name",
    "rule_family",
    "window_name",
    "threshold",
    "positive_capture_rate",
    "contamination_score",
]
REQUIRED_CASES_COLS = ["site", "panel_id", "anchor_date", "truth_case_id"]
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

SUMMARY_OUTPUT_COLS = [
    "rule_name",
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
    "triggered_site_day_count",
    "triggered_site_day_rate",
    "triggered_site_episode_count",
    "median_triggered_episode_length",
    "max_triggered_episode_length",
    "triggered_site_count",
    "source_complexity_rank",
    "window_complexity_rank",
    "threshold_rank",
    "recommended_rule_flag",
    "why_ko",
]

PREVALENCE_OUTPUT_COLS = [
    "rule_name",
    "site",
    "triggered_site_day_count",
    "triggered_site_day_rate",
    "triggered_site_episode_count",
    "median_triggered_episode_length",
]

RECOMMENDATION_OUTPUT_COLS = [
    "recommended_rule_name",
    "recommended_rule_reason_ko",
    "expected_use_ko",
    "caution_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Choose the least-broad viable common-cause breadth marker among tied candidates."
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


def read_site_full_csv(path: Path, *, requested_cols: list[str], site: str) -> pd.DataFrame:
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
        chunk["site"] = site
        chunk["panel_id"] = chunk["panel_id"].map(normalize_text)
        chunk["date"] = chunk["date"].map(parse_timestamp)
        chunk = chunk.loc[chunk["date"].notna()].copy()
        if chunk.empty:
            continue
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


def load_candidate_rules(root: Path) -> pd.DataFrame:
    path = root / "_share" / SWEEP_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_SWEEP_COLS, path.name)
    df["rule_name"] = df["rule_name"].map(normalize_text)
    df["rule_family"] = df["rule_family"].map(normalize_text)
    df["window_name"] = df["window_name"].map(normalize_text)
    df["threshold"] = pd.to_numeric(df["threshold"], errors="coerce")
    df["positive_capture_rate"] = pd.to_numeric(df["positive_capture_rate"], errors="coerce")
    df["contamination_score"] = pd.to_numeric(df["contamination_score"], errors="coerce")

    candidate_df = df.loc[
        df["positive_capture_rate"].sub(1.0).abs().le(1e-9)
        & df["contamination_score"].abs().le(1e-9)
    ].copy()
    if candidate_df.empty:
        raise SystemExit("no tied common-cause breadth candidates satisfy capture=1.0 and contamination=0.0")

    present_minimum = candidate_df["rule_name"].isin(MINIMUM_RULES_IF_PRESENT)
    if present_minimum.any():
        # Keep all tied candidates; this check just guarantees the canonical shortlist remains included when present.
        candidate_df = candidate_df.copy()
    return candidate_df.sort_values(by=["rule_family", "window_name", "threshold"], kind="mergesort").reset_index(drop=True)


def load_positive_cases(root: Path) -> pd.DataFrame:
    path = root / "_share" / CASES_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_CASES_COLS, path.name)
    for col in REQUIRED_CASES_COLS:
        df[col] = df[col].map(normalize_text)
    df["case_group"] = "positive"
    return df.loc[:, ["case_group", "site", "panel_id", "anchor_date", "truth_case_id"]]


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
    return df.loc[:, ["case_group", "site", "panel_id", "anchor_date", "truth_case_id"]]


def load_abrupt_negative_cases(root: Path, eval_bucket_map: dict[str, str]) -> pd.DataFrame:
    eligibility_path = root / "_share" / ELIGIBILITY_NAME
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

    combined = pd.concat(
        [
            eligibility_df.loc[:, ["case_group", "site", "panel_id", "anchor_date", "truth_case_id"]],
            reaudit_df.loc[:, ["case_group", "site", "panel_id", "anchor_date", "truth_case_id"]],
        ],
        ignore_index=True,
    )
    combined = combined.loc[combined["anchor_date"].ne("")].drop_duplicates(subset=["truth_case_id"], keep="first")
    return combined


def load_case_universe(root: Path) -> pd.DataFrame:
    eval_bucket_map = load_eval_bucket_map(root)
    frames = [
        load_positive_cases(root),
        load_precursor_negative_cases(root, eval_bucket_map),
        load_abrupt_negative_cases(root, eval_bucket_map),
    ]
    case_df = pd.concat(frames, ignore_index=True)
    for col in ["case_group", "site", "panel_id", "anchor_date", "truth_case_id"]:
        case_df[col] = case_df[col].map(normalize_text)
    case_df = case_df.drop_duplicates(subset=["truth_case_id"], keep="first").reset_index(drop=True)
    return case_df


def discover_sites(root: Path) -> list[str]:
    data_dir = root / "data"
    sites: list[str] = []
    if not data_dir.exists():
        return sites
    for child in sorted(data_dir.iterdir()):
        if not child.is_dir():
            continue
        out_dir = child / "out"
        if (out_dir / PANEL_DAY_CORE_NAME).exists() and (out_dir / GATE_DAILY_NAME).exists():
            sites.append(child.name)
    return sites


def load_full_site_data(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    core_frames: list[pd.DataFrame] = []
    gate_frames: list[pd.DataFrame] = []
    for site in sites:
        out_dir = root / "data" / site / "out"
        core_df = read_site_full_csv(out_dir / PANEL_DAY_CORE_NAME, requested_cols=CORE_REQUESTED_COLS, site=site)
        gate_df = read_site_full_csv(out_dir / GATE_DAILY_NAME, requested_cols=GATE_REQUESTED_COLS, site=site)
        if not core_df.empty:
            core_df["final_fault"] = core_df["final_fault"].map(to_int_flag).astype(int)
            core_frames.append(core_df.loc[:, ["site", "panel_id", "date", "final_fault"]])
        if not gate_df.empty:
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


def build_prevalence_feature_frame(site_daily_df: pd.DataFrame) -> pd.DataFrame:
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
            for window_name, days in WINDOW_NAME_TO_DAYS.items():
                if window_name == "same_day":
                    continue
                suffix = WINDOW_NAME_TO_SUFFIX[window_name]
                full_df[f"max_{feature}_panel_fraction_{suffix}"] = (
                    full_df[source_col]
                    .rolling(window=(2 * days + 1), center=True, min_periods=1)
                    .max()
                )

        observed_cols = [
            "date",
            "site",
            "site_panel_count_on_date",
            "max_final_fault_panel_fraction_same_day",
            "max_final_fault_panel_fraction_3d",
            "max_final_fault_panel_fraction_7d",
            "max_pre_alarm_panel_fraction_same_day",
            "max_pre_alarm_panel_fraction_3d",
            "max_pre_alarm_panel_fraction_7d",
            "max_ews_warning_panel_fraction_same_day",
            "max_ews_warning_panel_fraction_3d",
            "max_ews_warning_panel_fraction_7d",
        ]
        observed_df = scoped_df.loc[:, ["date"]].merge(full_df.loc[:, observed_cols], how="left", on="date")
        observed_df["site"] = site
        frames.append(observed_df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def build_case_feature_frame(case_df: pd.DataFrame, prevalence_features_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for case in case_df.to_dict(orient="records"):
        anchor_ts = parse_timestamp(case["anchor_date"])
        matched = prevalence_features_df.loc[
            prevalence_features_df["site"].eq(case["site"]) & prevalence_features_df["date"].eq(anchor_ts)
        ]
        if matched.empty:
            feature_row = {col: 0.0 for col in prevalence_features_df.columns if col.startswith("max_")}
        else:
            feature_row = matched.iloc[0].to_dict()
        rows.append({**case, **feature_row})
    return pd.DataFrame(rows)


def compute_rule_hit_from_row(row: pd.Series, rule_family: str, window_name: str, threshold: float) -> int:
    suffix = WINDOW_NAME_TO_SUFFIX[window_name]
    values = [float(row[f"max_{feature}_panel_fraction_{suffix}"]) for feature in RULE_FAMILY_FEATURES[rule_family]]
    return int(max(values) >= threshold)


def compute_rule_hit_from_prevalence_row(row: pd.Series, rule_family: str, window_name: str, threshold: float) -> int:
    return compute_rule_hit_from_row(row, rule_family, window_name, threshold)


def build_episode_lengths(trigger_dates: pd.Series) -> list[int]:
    if trigger_dates.empty:
        return []
    dates = pd.to_datetime(trigger_dates).sort_values().tolist()
    lengths: list[int] = []
    current_length = 1
    for idx in range(1, len(dates)):
        if (dates[idx] - dates[idx - 1]).days == 1:
            current_length += 1
        else:
            lengths.append(current_length)
            current_length = 1
    lengths.append(current_length)
    return lengths


def safe_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator)


def safe_median(values: list[int]) -> float:
    if not values:
        return 0.0
    return float(pd.Series(values, dtype=float).median())


def evaluate_candidates(candidate_df: pd.DataFrame, case_features_df: pd.DataFrame, prevalence_features_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    prevalence_rows: list[dict[str, object]] = []

    positive_df = case_features_df.loc[case_features_df["case_group"].eq("positive")].copy()
    precursor_df = case_features_df.loc[case_features_df["case_group"].eq("precursor_negative")].copy()
    abrupt_df = case_features_df.loc[case_features_df["case_group"].eq("abrupt_negative")].copy()

    global_site_day_count = int(len(prevalence_features_df))

    for candidate in candidate_df.to_dict(orient="records"):
        rule_name = normalize_text(candidate["rule_name"])
        rule_family = normalize_text(candidate["rule_family"])
        window_name = normalize_text(candidate["window_name"])
        threshold = float(candidate["threshold"])

        positive_hits = positive_df.apply(compute_rule_hit_from_row, axis=1, args=(rule_family, window_name, threshold)) if not positive_df.empty else pd.Series(dtype=int)
        precursor_hits = precursor_df.apply(compute_rule_hit_from_row, axis=1, args=(rule_family, window_name, threshold)) if not precursor_df.empty else pd.Series(dtype=int)
        abrupt_hits = abrupt_df.apply(compute_rule_hit_from_row, axis=1, args=(rule_family, window_name, threshold)) if not abrupt_df.empty else pd.Series(dtype=int)

        prevalence_hits = prevalence_features_df.apply(
            compute_rule_hit_from_prevalence_row,
            axis=1,
            args=(rule_family, window_name, threshold),
        ) if not prevalence_features_df.empty else pd.Series(dtype=int)
        prevalence_scored_df = prevalence_features_df.copy()
        prevalence_scored_df["rule_hit_flag"] = prevalence_hits.astype(int) if not prevalence_hits.empty else 0

        triggered_site_day_count = int(prevalence_scored_df["rule_hit_flag"].sum()) if not prevalence_scored_df.empty else 0
        triggered_site_day_rate = safe_rate(triggered_site_day_count, global_site_day_count)

        all_episode_lengths: list[int] = []
        triggered_site_count = 0
        for site, site_df in prevalence_scored_df.groupby("site"):
            site_trigger_df = site_df.loc[site_df["rule_hit_flag"].eq(1)].copy()
            episode_lengths = build_episode_lengths(site_trigger_df["date"])
            if episode_lengths:
                triggered_site_count += 1
            all_episode_lengths.extend(episode_lengths)
            prevalence_rows.append(
                {
                    "rule_name": rule_name,
                    "site": site,
                    "triggered_site_day_count": int(site_trigger_df.shape[0]),
                    "triggered_site_day_rate": safe_rate(int(site_trigger_df.shape[0]), int(site_df.shape[0])),
                    "triggered_site_episode_count": int(len(episode_lengths)),
                    "median_triggered_episode_length": safe_median(episode_lengths),
                }
            )

        positive_case_count = int(len(positive_df))
        precursor_case_count = int(len(precursor_df))
        abrupt_case_count = int(len(abrupt_df))
        positive_capture_count = int(positive_hits.sum()) if not positive_hits.empty else 0
        precursor_trigger_count = int(precursor_hits.sum()) if not precursor_hits.empty else 0
        abrupt_trigger_count = int(abrupt_hits.sum()) if not abrupt_hits.empty else 0
        positive_capture_rate = safe_rate(positive_capture_count, positive_case_count)
        precursor_trigger_rate = safe_rate(precursor_trigger_count, precursor_case_count)
        abrupt_trigger_rate = safe_rate(abrupt_trigger_count, abrupt_case_count)
        contamination_score = precursor_trigger_rate + abrupt_trigger_rate

        summary_rows.append(
            {
                "rule_name": rule_name,
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
                "triggered_site_day_count": triggered_site_day_count,
                "triggered_site_day_rate": triggered_site_day_rate,
                "triggered_site_episode_count": int(len(all_episode_lengths)),
                "median_triggered_episode_length": safe_median(all_episode_lengths),
                "max_triggered_episode_length": int(max(all_episode_lengths)) if all_episode_lengths else 0,
                "triggered_site_count": triggered_site_count,
                "source_complexity_rank": SOURCE_COMPLEXITY_RANK[rule_family],
                "window_complexity_rank": WINDOW_COMPLEXITY_RANK[window_name],
                "threshold_rank": int(round(threshold * 100)),
                "recommended_rule_flag": 0,
                "why_ko": "",
            }
        )

    return (
        pd.DataFrame(summary_rows).reindex(columns=SUMMARY_OUTPUT_COLS),
        pd.DataFrame(prevalence_rows).reindex(columns=PREVALENCE_OUTPUT_COLS),
    )


def pick_recommended_rule(summary_df: pd.DataFrame) -> pd.Series:
    ranked = summary_df.sort_values(
        by=[
            "positive_capture_rate",
            "contamination_score",
            "triggered_site_day_rate",
            "source_complexity_rank",
            "window_complexity_rank",
            "threshold_rank",
            "rule_name",
        ],
        ascending=[False, True, True, True, True, False, True],
        kind="mergesort",
    )
    return ranked.iloc[0]


def annotate_recommendation(summary_df: pd.DataFrame, recommended_row: pd.Series) -> pd.DataFrame:
    summary_df = summary_df.copy()
    mask = summary_df["rule_name"].eq(normalize_text(recommended_row["rule_name"]))
    summary_df.loc[mask, "recommended_rule_flag"] = 1
    summary_df.loc[mask, "why_ko"] = (
        "capture/contamination 동률 후보 중 global prevalence가 가장 낮고, source/window가 가장 단순하며, threshold도 충분히 높아 least-broad viable candidate로 선택"
    )
    return summary_df


def build_recommendation_output(recommended_row: pd.Series) -> pd.DataFrame:
    rule_name = normalize_text(recommended_row["rule_name"])
    return pd.DataFrame(
        [
            {
                "recommended_rule_name": rule_name,
                "recommended_rule_reason_ko": "동률 capture/contamination 후보 중 prevalence가 가장 낮고 더 단순한 source/window 조합이라 descriptive routing marker candidate로 가장 보수적이다.",
                "expected_use_ko": "공식 detector 변경 전, common-cause descriptive routing candidate 또는 review aid로 먼저 사용",
                "caution_ko": "현재는 retrofit audit 결과일 뿐이며, 운영/탐지 로직 승격 전에는 추가 truth와 contamination 재검증이 필요",
            }
        ]
    ).reindex(columns=RECOMMENDATION_OUTPUT_COLS)


def write_outputs(root: Path, summary_df: pd.DataFrame, prevalence_df: pd.DataFrame, recommendation_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    prevalence_df.to_csv(share_dir / PREVALENCE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    recommendation_df.to_csv(share_dir / RECOMMENDATION_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    candidate_df = load_candidate_rules(root)
    case_df = load_case_universe(root)
    sites = discover_sites(root)
    core_df, gate_df = load_full_site_data(root, sites)
    site_daily_df = aggregate_site_daily(core_df, gate_df)
    prevalence_features_df = build_prevalence_feature_frame(site_daily_df)
    case_features_df = build_case_feature_frame(case_df, prevalence_features_df)
    summary_df, prevalence_df = evaluate_candidates(candidate_df, case_features_df, prevalence_features_df)
    recommended_row = pick_recommended_rule(summary_df)
    summary_df = annotate_recommendation(summary_df, recommended_row)
    recommendation_df = build_recommendation_output(recommended_row)
    write_outputs(root, summary_df, prevalence_df, recommendation_df)


if __name__ == "__main__":
    main()
