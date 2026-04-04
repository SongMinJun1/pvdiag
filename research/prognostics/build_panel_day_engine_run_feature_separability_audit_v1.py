#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

HELPER_FILENAME = "ae_simple_local_precursor_gate_daily.csv"
CORE_FILENAME = "panel_day_core.csv"
WINDOW_DAYS = 30
RUN_KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
DAY_KEY_COLS = ["site", "panel_id", "date"]
HELPER_BOOL_COLS = [
    "data_bad",
    "cond_var",
    "cond_evt",
    "cond_dtw",
    "cond_hs",
    "ae_mid_or_hi_early",
    "dtw_mid_or_hi_early",
    "hs_mid_or_hi_early",
    "pre_ews",
    "ews_warning",
    "site_event_soft",
    "site_event_hard",
    "group_off_date",
    "prefault_B",
    "pre_alarm",
    "prefault_cond_mid",
    "prefault_cond_ae",
    "prefault_cond_dtw",
    "prefault_cond_ews",
    "prealarm_cond_ae_mid_or_hi",
    "prealarm_cond_dtw_mid_or_hi",
    "prealarm_cond_hs_mid_or_hi",
]
HELPER_INT_COLS = ["signal_count", "ews_runlen"]
HELPER_COLS = [*HELPER_BOOL_COLS, *HELPER_INT_COLS]
CORE_NUMERIC_COLS = [
    "recon_error",
    "dtw_dist",
    "hs_score",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "v_drop",
]
NUMERIC_FEATURES = [
    "run_day_count",
    "pre_ews_day_count",
    "ews_warning_day_count",
    "pre_alarm_day_count",
    "prefault_B_day_count",
    "pre_ews_run_count",
    "ews_warning_run_count",
    "pre_alarm_run_count",
    "prefault_B_run_count",
    "pre_alarm_max_run",
    "max_signal_count",
    "mean_signal_count",
    "any_data_bad",
    "data_bad_day_ratio",
    "cond_evt_day_ratio",
    "cond_evt_only_day_ratio",
    "cond_evt_same_day_early_corroborated_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "dtw_mid_or_hi_early_day_ratio",
    "hs_mid_or_hi_early_day_ratio",
    "max_recon_error",
    "p95_recon_error",
    "max_dtw_dist",
    "p95_dtw_dist",
    "max_hs_score",
    "p95_hs_score",
    "min_mid_ratio",
    "min_mid_v_ratio",
    "min_mid_i_ratio",
    "max_v_drop",
    "recurring_run_within_60d",
    "future_fault_linked_flag",
    "future_truth_linked_flag",
]
FEATURE_TABLE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "overlap_case_class",
    "delta_run_class",
    "fate_class",
    "cohort_hint",
    "pre_ews_day_count",
    "ews_warning_day_count",
    "pre_alarm_day_count",
    "prefault_B_day_count",
    "pre_ews_run_count",
    "ews_warning_run_count",
    "pre_alarm_run_count",
    "prefault_B_run_count",
    "pre_alarm_max_run",
    "max_signal_count",
    "mean_signal_count",
    "any_data_bad",
    "data_bad_day_ratio",
    "cond_evt_day_ratio",
    "cond_evt_only_day_ratio",
    "cond_evt_same_day_early_corroborated_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "dtw_mid_or_hi_early_day_ratio",
    "hs_mid_or_hi_early_day_ratio",
    "max_recon_error",
    "p95_recon_error",
    "max_dtw_dist",
    "p95_dtw_dist",
    "max_hs_score",
    "p95_hs_score",
    "min_mid_ratio",
    "min_mid_v_ratio",
    "min_mid_i_ratio",
    "max_v_drop",
    "recurring_run_within_60d",
    "future_fault_linked_flag",
    "future_truth_linked_flag",
]
SUMMARY_COLS = [
    "record_type",
    "cohort_hint",
    "feature_name",
    "run_count",
    "median_value",
    "p25_value",
    "p75_value",
    "lhs_cohort",
    "rhs_cohort",
    "lhs_median",
    "rhs_median",
    "median_gap",
    "normalized_gap",
]
METHOD_HINT_COLS = [
    "feature_name",
    "comparison_target",
    "normalized_gap",
    "directional_hint",
    "method_relevance_class",
]
COMPARISON_PAIRS = [
    ("eligible_local", "nuisance_alert"),
    ("future_fault_linked", "recurring_monitor_like"),
    ("future_fault_linked", "isolated_unexplained"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a run-level feature table and separability audit for local precursor runs."
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
    if text.lower() == "nan":
        return ""
    return text


def normalize_date(value: object) -> str:
    text = normalize_text(value)
    return text[:10] if len(text) >= 10 else text


def parse_date(value: object) -> pd.Timestamp | pd.NaT:
    text = normalize_date(value)
    if not text:
        return pd.NaT
    return pd.to_datetime(text, errors="coerce")


def to_int_flag(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return 1
    if text in {"0", "false", "f", "no", "n", ""}:
        return 0
    try:
        return 1 if float(text) > 0 else 0
    except ValueError:
        return 0


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def discover_sites(root: Path) -> list[str]:
    sites = sorted(
        {
            path.parent.parent.name
            for path in (root / "data").glob("*/out/ae_simple_local_precursor_gate_daily.csv")
        }
    )
    if not sites:
        raise SystemExit("no helper files found under data/*/out")
    return sites


def normalized_helper_value(col: str, value: object) -> object:
    text = normalize_text(value)
    if text == "":
        return ""
    if col in HELPER_BOOL_COLS:
        return int(to_int_flag(value))
    if col in HELPER_INT_COLS:
        try:
            return int(float(text))
        except ValueError:
            return ""
    try:
        return round(float(text), 12)
    except ValueError:
        return text


def normalized_core_value(col: str, value: object) -> object:
    text = normalize_text(value)
    if text == "":
        return ""
    try:
        return round(float(text), 12)
    except ValueError:
        return text


def collapse_exact_duplicates(
    df: pd.DataFrame,
    *,
    key_cols: list[str],
    value_cols: list[str],
    normalize_value,
) -> tuple[pd.DataFrame, int]:
    if df.empty:
        return df.copy(), 0
    duplicated = df.duplicated(subset=key_cols, keep=False)
    if not duplicated.any():
        return df.sort_values("_row_order", kind="stable").reset_index(drop=True), 0

    dup_df = df.loc[duplicated].copy()
    keep_rows: list[pd.DataFrame] = []
    excluded_count = 0
    for _, group in dup_df.groupby(key_cols, sort=False, dropna=False):
        normalized_rows = {
            tuple(normalize_value(col, group.iloc[idx][col]) for col in value_cols)
            for idx in range(len(group))
        }
        if len(normalized_rows) > 1:
            excluded_count += 1
            continue
        keep_rows.append(group.nsmallest(1, "_row_order"))

    unique_rows = df.loc[~duplicated].copy()
    collapsed = pd.concat([unique_rows, *keep_rows], ignore_index=True) if keep_rows else unique_rows
    return collapsed.sort_values("_row_order", kind="stable").reset_index(drop=True), excluded_count


def load_helper_daily(root: Path, sites: list[str]) -> tuple[pd.DataFrame, int]:
    parts: list[pd.DataFrame] = []
    excluded_total = 0
    for site in sites:
        path = root / "data" / site / "out" / HELPER_FILENAME
        df = read_csv(path)
        ensure_columns(df, ["panel_id", "date", *HELPER_COLS], path.name)
        df = df.copy()
        if "site" not in df.columns:
            df["site"] = site
        df["site"] = df["site"].map(normalize_text)
        df.loc[df["site"].eq(""), "site"] = site
        df["panel_id"] = df["panel_id"].map(normalize_text)
        df["date"] = df["date"].map(normalize_date)
        df = df.loc[df["site"].eq(site), [*DAY_KEY_COLS, *HELPER_COLS]].copy()
        df["_row_order"] = range(len(df))
        df, excluded = collapse_exact_duplicates(
            df,
            key_cols=DAY_KEY_COLS,
            value_cols=HELPER_COLS,
            normalize_value=normalized_helper_value,
        )
        excluded_total += excluded
        for col in HELPER_BOOL_COLS:
            df[col] = df[col].map(to_int_flag).astype(int)
        for col in HELPER_INT_COLS:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        df["date_ts"] = df["date"].map(parse_date)
        parts.append(df.loc[:, [*DAY_KEY_COLS, "date_ts", *HELPER_COLS]].copy())
    helper = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=[*DAY_KEY_COLS, "date_ts", *HELPER_COLS])
    return helper.drop_duplicates(subset=DAY_KEY_COLS, keep="first").copy(), excluded_total


def load_core_daily(root: Path, sites: list[str]) -> tuple[pd.DataFrame, int]:
    parts: list[pd.DataFrame] = []
    excluded_total = 0
    for site in sites:
        path = root / "data" / site / "out" / CORE_FILENAME
        df = read_csv(path)
        ensure_columns(df, ["panel_id", "date", *CORE_NUMERIC_COLS], path.name)
        df = df.copy()
        df["site"] = site
        df["site"] = df["site"].map(normalize_text)
        df["panel_id"] = df["panel_id"].map(normalize_text)
        df["date"] = df["date"].map(normalize_date)
        df = df.loc[df["site"].eq(site), [*DAY_KEY_COLS, *CORE_NUMERIC_COLS]].copy()
        df["_row_order"] = range(len(df))
        df, excluded = collapse_exact_duplicates(
            df,
            key_cols=DAY_KEY_COLS,
            value_cols=CORE_NUMERIC_COLS,
            normalize_value=normalized_core_value,
        )
        excluded_total += excluded
        for col in CORE_NUMERIC_COLS:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["date_ts"] = df["date"].map(parse_date)
        parts.append(df.loc[:, [*DAY_KEY_COLS, "date_ts", *CORE_NUMERIC_COLS]].copy())
    core = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=[*DAY_KEY_COLS, "date_ts", *CORE_NUMERIC_COLS])
    return core.drop_duplicates(subset=DAY_KEY_COLS, keep="first").copy(), excluded_total


def classify_run_shape(run_day_count: int) -> str:
    if run_day_count <= 3:
        return "short_alert_run"
    if run_day_count <= 9:
        return "medium_alert_run"
    return "chronic_alert_run"


def build_runs(helper_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    active = helper_df.loc[helper_df["pre_alarm"].eq(1)].copy()
    if active.empty:
        empty_runs = pd.DataFrame(columns=[*RUN_KEY_COLS, "run_day_count", "run_shape_class", "run_start_ts", "run_end_ts"])
        empty_days = pd.DataFrame(columns=[*DAY_KEY_COLS, "date_ts", *HELPER_COLS, "run_start_date", "run_end_date"])
        return empty_runs, empty_days
    active = active.sort_values(["site", "panel_id", "date_ts", "date"], kind="stable").reset_index(drop=True)
    run_records: list[dict[str, object]] = []
    day_parts: list[pd.DataFrame] = []
    one_day = pd.Timedelta(days=1)
    for (site, panel_id), group in active.groupby(["site", "panel_id"], sort=False):
        group = group.reset_index(drop=True)
        run_start_idx = 0
        for idx in range(1, len(group) + 1):
            is_break = idx == len(group)
            if not is_break:
                prev_ts = group.loc[idx - 1, "date_ts"]
                current_ts = group.loc[idx, "date_ts"]
                is_break = pd.isna(prev_ts) or pd.isna(current_ts) or current_ts != prev_ts + one_day
            if not is_break:
                continue
            run_df = group.iloc[run_start_idx:idx].copy()
            run_start_date = run_df.iloc[0]["date"]
            run_end_date = run_df.iloc[-1]["date"]
            run_day_count = int(len(run_df))
            run_records.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "run_start_date": run_start_date,
                    "run_end_date": run_end_date,
                    "run_day_count": run_day_count,
                    "run_shape_class": classify_run_shape(run_day_count),
                    "run_start_ts": run_df.iloc[0]["date_ts"],
                    "run_end_ts": run_df.iloc[-1]["date_ts"],
                }
            )
            run_df["run_start_date"] = run_start_date
            run_df["run_end_date"] = run_end_date
            day_parts.append(run_df)
            run_start_idx = idx
    runs = pd.DataFrame(run_records)
    run_days = pd.concat(day_parts, ignore_index=True)
    return runs, run_days


def load_delta_registry(root: Path) -> pd.DataFrame:
    path = root / "_share" / "panel_day_engine_local_seed_carry_delta_run_registry_v1.csv"
    df = read_csv(path)
    ensure_columns(df, ["version", "site", "panel_id", "run_start_date", "run_end_date", "overlap_case_class", "delta_run_class"], path.name)
    df = df.copy()
    for col in ["version", "site", "panel_id", "overlap_case_class", "delta_run_class"]:
        df[col] = df[col].map(normalize_text)
    df["run_start_date"] = df["run_start_date"].map(normalize_date)
    df["run_end_date"] = df["run_end_date"].map(normalize_date)
    df = df.loc[df["version"].eq("current_seed_carry1"), [*RUN_KEY_COLS, "overlap_case_class", "delta_run_class"]].copy()
    return df.drop_duplicates(subset=RUN_KEY_COLS, keep="first")


def load_fate_cases(root: Path) -> pd.DataFrame:
    path = root / "_share" / "panel_day_engine_local_seed_carry_fate_cases_v1.csv"
    df = read_csv(path)
    required = [*RUN_KEY_COLS, "fate_class", "recurring_run_within_60d", "future_fault_linked_flag", "future_truth_linked_flag"]
    optional_fault_cols = [
        "future_confirmed_fault_30d",
        "future_critical_fault_30d",
        "future_final_fault_30d",
        "future_confirmed_fault_60d",
        "future_critical_fault_60d",
        "future_final_fault_60d",
        "future_truth_overlap_30d",
        "future_truth_overlap_60d",
    ]
    ensure_columns(df, [col for col in required if col in df.columns or col not in {"future_fault_linked_flag", "future_truth_linked_flag"}], path.name)
    df = df.copy()
    for col in ["site", "panel_id", "run_start_date", "run_end_date", "fate_class"]:
        df[col] = df[col].map(normalize_text if col == "fate_class" or col in {"site", "panel_id"} else normalize_date)
    if "future_fault_linked_flag" not in df.columns:
        df["future_fault_linked_flag"] = 0
        for col in optional_fault_cols[:6]:
            if col in df.columns:
                df["future_fault_linked_flag"] = df["future_fault_linked_flag"] | df[col].map(to_int_flag)
    if "future_truth_linked_flag" not in df.columns:
        df["future_truth_linked_flag"] = 0
        for col in optional_fault_cols[6:]:
            if col in df.columns:
                df["future_truth_linked_flag"] = df["future_truth_linked_flag"] | df[col].map(to_int_flag)
    df["recurring_run_within_60d"] = df["recurring_run_within_60d"].map(to_int_flag).astype(int)
    df["future_fault_linked_flag"] = df["future_fault_linked_flag"].map(to_int_flag).astype(int)
    df["future_truth_linked_flag"] = df["future_truth_linked_flag"].map(to_int_flag).astype(int)
    return df.loc[:, [*RUN_KEY_COLS, "fate_class", "recurring_run_within_60d", "future_fault_linked_flag", "future_truth_linked_flag"]].drop_duplicates(subset=RUN_KEY_COLS, keep="first")


def build_case_windows(df: pd.DataFrame, *, anchor_col: str, case_type: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["site", "panel_id", "window_start_ts", "window_end_ts", "case_type"])
    out = df.loc[:, ["site", "panel_id", anchor_col]].copy()
    out[anchor_col] = out[anchor_col].map(normalize_date)
    out["anchor_ts"] = out[anchor_col].map(parse_date)
    out["window_start_ts"] = out["anchor_ts"] - pd.Timedelta(days=WINDOW_DAYS)
    out["window_end_ts"] = out["anchor_ts"] - pd.Timedelta(days=1)
    out["case_type"] = case_type
    return out.loc[:, ["site", "panel_id", "window_start_ts", "window_end_ts", "case_type"]]


def load_eligible_windows(root: Path) -> pd.DataFrame:
    path = root / "_share" / "panel_day_engine_local_precursor_eligibility_cases_v1.csv"
    df = read_csv(path)
    ensure_columns(df, ["site", "panel_id", "fault_start_date", "precursor_eligible_flag"], path.name)
    df = df.copy()
    df["site"] = df["site"].map(normalize_text)
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["precursor_eligible_flag"] = df["precursor_eligible_flag"].map(to_int_flag).astype(int)
    df = df.loc[df["precursor_eligible_flag"].eq(1)].copy()
    return build_case_windows(df, anchor_col="fault_start_date", case_type="eligible_local")


def load_nuisance_windows(root: Path) -> pd.DataFrame:
    path = root / "_share" / "panel_day_engine_local_pre_ews_replay_cases_v1.csv"
    df = read_csv(path)
    ensure_columns(df, ["rule_id", "cohort_type", "site", "panel_id", "strict_trigger_date", "any_pre_alarm_replay_hit_flag"], path.name)
    df = df.copy()
    for col in ["rule_id", "cohort_type", "site", "panel_id"]:
        df[col] = df[col].map(normalize_text)
    df["any_pre_alarm_replay_hit_flag"] = df["any_pre_alarm_replay_hit_flag"].map(to_int_flag).astype(int)
    df = df.loc[
        df["rule_id"].eq("current_pre_ews")
        & df["cohort_type"].eq("nuisance_nonlocal")
        & df["any_pre_alarm_replay_hit_flag"].eq(1)
    ].copy()
    return build_case_windows(df, anchor_col="strict_trigger_date", case_type="nuisance_alert")


def run_overlaps_windows(run_row: pd.Series, windows_by_panel: dict[tuple[str, str], list[tuple[pd.Timestamp, pd.Timestamp]]]) -> bool:
    windows = windows_by_panel.get((run_row["site"], run_row["panel_id"]), [])
    for start_ts, end_ts in windows:
        if pd.isna(start_ts) or pd.isna(end_ts):
            continue
        if start_ts <= run_row["run_end_ts"] and run_row["run_start_ts"] <= end_ts:
            return True
    return False


def build_window_index(windows_df: pd.DataFrame) -> dict[tuple[str, str], list[tuple[pd.Timestamp, pd.Timestamp]]]:
    index: dict[tuple[str, str], list[tuple[pd.Timestamp, pd.Timestamp]]] = {}
    for row in windows_df.itertuples(index=False):
        index.setdefault((row.site, row.panel_id), []).append((row.window_start_ts, row.window_end_ts))
    return index


def count_true_runs(flag_series: pd.Series) -> int:
    flags = flag_series.fillna(0).astype(int).eq(1)
    if flags.empty:
        return 0
    starts = flags & ~flags.shift(1, fill_value=False)
    return int(starts.sum())


def max_true_run(flag_series: pd.Series) -> int:
    flags = flag_series.fillna(0).astype(int).eq(1)
    if flags.empty or not flags.any():
        return 0
    group_ids = (~flags).cumsum()
    return int(flags.groupby(group_ids).sum().max())


def safe_max(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce")
    return float(numeric.max()) if numeric.notna().any() else float("nan")


def safe_mean(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce")
    return float(numeric.mean()) if numeric.notna().any() else float("nan")


def safe_quantile(series: pd.Series, q: float) -> float:
    numeric = pd.to_numeric(series, errors="coerce")
    return float(numeric.quantile(q)) if numeric.notna().any() else float("nan")


def safe_min(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce")
    return float(numeric.min()) if numeric.notna().any() else float("nan")


def build_run_feature_table(
    runs_df: pd.DataFrame,
    run_days_df: pd.DataFrame,
    core_df: pd.DataFrame,
    delta_df: pd.DataFrame,
    fate_df: pd.DataFrame,
    eligible_windows: pd.DataFrame,
    nuisance_windows: pd.DataFrame,
) -> pd.DataFrame:
    run_days = run_days_df.merge(core_df, on=DAY_KEY_COLS + ["date_ts"], how="left")
    delta_join = delta_df.drop_duplicates(subset=RUN_KEY_COLS, keep="first")
    fate_join = fate_df.drop_duplicates(subset=RUN_KEY_COLS, keep="first")
    runs = runs_df.merge(delta_join, on=RUN_KEY_COLS, how="left")
    runs = runs.merge(fate_join, on=RUN_KEY_COLS, how="left")
    runs["overlap_case_class"] = runs["overlap_case_class"].fillna("").map(normalize_text)
    runs["delta_run_class"] = runs["delta_run_class"].fillna("").map(normalize_text)
    runs["fate_class"] = runs["fate_class"].fillna("").map(normalize_text)
    for col in ["recurring_run_within_60d", "future_fault_linked_flag", "future_truth_linked_flag"]:
        runs[col] = runs[col].fillna(0).map(to_int_flag).astype(int)

    eligible_index = build_window_index(eligible_windows)
    nuisance_index = build_window_index(nuisance_windows)
    run_index = {
        (site, panel_id): group.sort_values(["run_start_ts", "run_end_ts"], kind="stable").reset_index(drop=True)
        for (site, panel_id), group in runs.groupby(["site", "panel_id"], sort=False)
    }

    feature_records: list[dict[str, object]] = []
    for run in runs.itertuples(index=False):
        mask = (
            run_days["site"].eq(run.site)
            & run_days["panel_id"].eq(run.panel_id)
            & run_days["run_start_date"].eq(run.run_start_date)
            & run_days["run_end_date"].eq(run.run_end_date)
        )
        run_df = run_days.loc[mask].sort_values(["date_ts", "date"], kind="stable").copy()
        run_day_count = int(run.run_day_count)
        any_early = (
            run_df["ae_mid_or_hi_early"].fillna(0).astype(int).eq(1)
            | run_df["dtw_mid_or_hi_early"].fillna(0).astype(int).eq(1)
            | run_df["hs_mid_or_hi_early"].fillna(0).astype(int).eq(1)
        )
        cond_evt_only = (
            run_df["cond_evt"].fillna(0).astype(int).eq(1)
            & run_df["cond_var"].fillna(0).astype(int).eq(0)
            & run_df["cond_dtw"].fillna(0).astype(int).eq(0)
            & run_df["cond_hs"].fillna(0).astype(int).eq(0)
        )
        cond_evt_same_day = run_df["cond_evt"].fillna(0).astype(int).eq(1) & any_early
        panel_runs = run_index.get((run.site, run.panel_id), pd.DataFrame(columns=["run_start_ts", "run_end_ts"]))
        future_runs_60d = panel_runs.loc[
            panel_runs["run_start_ts"].gt(run.run_end_ts)
            & panel_runs["run_start_ts"].le(run.run_end_ts + pd.Timedelta(days=60))
        ].copy()

        if run_overlaps_windows(pd.Series(run._asdict()), eligible_index):
            cohort_hint = "eligible_local"
        elif run_overlaps_windows(pd.Series(run._asdict()), nuisance_index):
            cohort_hint = "nuisance_alert"
        elif run.fate_class in {"future_fault_linked", "future_truth_linked"}:
            cohort_hint = "future_fault_linked"
        elif run.fate_class == "recurring_chronic_monitor_like":
            cohort_hint = "recurring_monitor_like"
        elif run.fate_class == "isolated_unexplained":
            cohort_hint = "isolated_unexplained"
        else:
            cohort_hint = "unmatched_other"

        feature_records.append(
            {
                "site": run.site,
                "panel_id": run.panel_id,
                "run_start_date": run.run_start_date,
                "run_end_date": run.run_end_date,
                "run_day_count": run_day_count,
                "run_shape_class": run.run_shape_class,
                "overlap_case_class": run.overlap_case_class,
                "delta_run_class": run.delta_run_class,
                "fate_class": run.fate_class,
                "cohort_hint": cohort_hint,
                "pre_ews_day_count": int(run_df["pre_ews"].fillna(0).astype(int).sum()),
                "ews_warning_day_count": int(run_df["ews_warning"].fillna(0).astype(int).sum()),
                "pre_alarm_day_count": int(run_df["pre_alarm"].fillna(0).astype(int).sum()),
                "prefault_B_day_count": int(run_df["prefault_B"].fillna(0).astype(int).sum()),
                "pre_ews_run_count": count_true_runs(run_df["pre_ews"]),
                "ews_warning_run_count": count_true_runs(run_df["ews_warning"]),
                "pre_alarm_run_count": count_true_runs(run_df["pre_alarm"]),
                "prefault_B_run_count": count_true_runs(run_df["prefault_B"]),
                "pre_alarm_max_run": max_true_run(run_df["pre_alarm"]),
                "max_signal_count": safe_max(run_df["signal_count"]),
                "mean_signal_count": safe_mean(run_df["signal_count"]),
                "any_data_bad": int(run_df["data_bad"].fillna(0).astype(int).gt(0).any()),
                "data_bad_day_ratio": float(run_df["data_bad"].fillna(0).astype(int).mean()) if run_day_count else 0.0,
                "cond_evt_day_ratio": float(run_df["cond_evt"].fillna(0).astype(int).mean()) if run_day_count else 0.0,
                "cond_evt_only_day_ratio": float(cond_evt_only.mean()) if run_day_count else 0.0,
                "cond_evt_same_day_early_corroborated_day_ratio": float(cond_evt_same_day.mean()) if run_day_count else 0.0,
                "ae_mid_or_hi_early_day_ratio": float(run_df["ae_mid_or_hi_early"].fillna(0).astype(int).mean()) if run_day_count else 0.0,
                "dtw_mid_or_hi_early_day_ratio": float(run_df["dtw_mid_or_hi_early"].fillna(0).astype(int).mean()) if run_day_count else 0.0,
                "hs_mid_or_hi_early_day_ratio": float(run_df["hs_mid_or_hi_early"].fillna(0).astype(int).mean()) if run_day_count else 0.0,
                "max_recon_error": safe_max(run_df["recon_error"]),
                "p95_recon_error": safe_quantile(run_df["recon_error"], 0.95),
                "max_dtw_dist": safe_max(run_df["dtw_dist"]),
                "p95_dtw_dist": safe_quantile(run_df["dtw_dist"], 0.95),
                "max_hs_score": safe_max(run_df["hs_score"]),
                "p95_hs_score": safe_quantile(run_df["hs_score"], 0.95),
                "min_mid_ratio": safe_min(run_df["mid_ratio"]),
                "min_mid_v_ratio": safe_min(run_df["mid_v_ratio"]),
                "min_mid_i_ratio": safe_min(run_df["mid_i_ratio"]),
                "max_v_drop": safe_max(run_df["v_drop"]),
                "recurring_run_within_60d": int(len(future_runs_60d) > 0),
                "future_fault_linked_flag": int(run.future_fault_linked_flag),
                "future_truth_linked_flag": int(run.future_truth_linked_flag),
            }
        )
    return pd.DataFrame(feature_records).reindex(columns=FEATURE_TABLE_COLS)


def build_distribution_summary(feature_df: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for cohort_hint in sorted(feature_df["cohort_hint"].dropna().astype(str).unique()):
        cohort_df = feature_df.loc[feature_df["cohort_hint"].eq(cohort_hint)].copy()
        for feature_name in NUMERIC_FEATURES:
            values = pd.to_numeric(cohort_df[feature_name], errors="coerce").dropna()
            records.append(
                {
                    "record_type": "cohort_distribution",
                    "cohort_hint": cohort_hint,
                    "feature_name": feature_name,
                    "run_count": int(len(values)),
                    "median_value": float(values.median()) if not values.empty else float("nan"),
                    "p25_value": float(values.quantile(0.25)) if not values.empty else float("nan"),
                    "p75_value": float(values.quantile(0.75)) if not values.empty else float("nan"),
                    "lhs_cohort": "",
                    "rhs_cohort": "",
                    "lhs_median": float("nan"),
                    "rhs_median": float("nan"),
                    "median_gap": float("nan"),
                    "normalized_gap": float("nan"),
                }
            )
    return pd.DataFrame(records).reindex(columns=SUMMARY_COLS)


def build_comparison_summary(feature_df: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for lhs, rhs in COMPARISON_PAIRS:
        lhs_df = feature_df.loc[feature_df["cohort_hint"].eq(lhs)].copy()
        rhs_df = feature_df.loc[feature_df["cohort_hint"].eq(rhs)].copy()
        for feature_name in NUMERIC_FEATURES:
            lhs_values = pd.to_numeric(lhs_df[feature_name], errors="coerce").dropna()
            rhs_values = pd.to_numeric(rhs_df[feature_name], errors="coerce").dropna()
            lhs_median = float(lhs_values.median()) if not lhs_values.empty else float("nan")
            rhs_median = float(rhs_values.median()) if not rhs_values.empty else float("nan")
            lhs_iqr = float(lhs_values.quantile(0.75) - lhs_values.quantile(0.25)) if not lhs_values.empty else float("nan")
            rhs_iqr = float(rhs_values.quantile(0.75) - rhs_values.quantile(0.25)) if not rhs_values.empty else float("nan")
            pooled_iqr = ((0.0 if pd.isna(lhs_iqr) else lhs_iqr) + (0.0 if pd.isna(rhs_iqr) else rhs_iqr)) / 2.0
            median_gap = lhs_median - rhs_median if not (pd.isna(lhs_median) or pd.isna(rhs_median)) else float("nan")
            normalized_gap = (
                abs(median_gap) / (pooled_iqr + 1e-6)
                if not pd.isna(median_gap)
                else float("nan")
            )
            records.append(
                {
                    "record_type": "comparison",
                    "cohort_hint": "",
                    "feature_name": feature_name,
                    "run_count": int(min(len(lhs_values), len(rhs_values))),
                    "median_value": float("nan"),
                    "p25_value": float("nan"),
                    "p75_value": float("nan"),
                    "lhs_cohort": lhs,
                    "rhs_cohort": rhs,
                    "lhs_median": lhs_median,
                    "rhs_median": rhs_median,
                    "median_gap": median_gap,
                    "normalized_gap": normalized_gap,
                }
            )
    return pd.DataFrame(records).reindex(columns=SUMMARY_COLS)


def build_method_hints(comparison_df: pd.DataFrame) -> pd.DataFrame:
    hints: list[dict[str, object]] = []
    for row in comparison_df.itertuples(index=False):
        comparison_target = f"{row.lhs_cohort}_vs_{row.rhs_cohort}"
        if pd.isna(row.normalized_gap):
            gap = float("nan")
            relevance = "weak_candidate"
            directional = "insufficient_data"
        else:
            gap = float(row.normalized_gap)
            if gap >= 1.0:
                relevance = "strong_run_ranker_candidate"
            elif gap >= 0.35:
                relevance = "possible_run_ranker_candidate"
            else:
                relevance = "weak_candidate"
            if pd.isna(row.median_gap) or row.median_gap == 0:
                directional = "similar_medians"
            elif row.median_gap > 0:
                directional = f"higher_in_{row.lhs_cohort}"
            else:
                directional = f"higher_in_{row.rhs_cohort}"
        hints.append(
            {
                "feature_name": row.feature_name,
                "comparison_target": comparison_target,
                "normalized_gap": gap,
                "directional_hint": directional,
                "method_relevance_class": relevance,
            }
        )
    hint_df = pd.DataFrame(hints).reindex(columns=METHOD_HINT_COLS)
    return hint_df.sort_values(["comparison_target", "normalized_gap", "feature_name"], ascending=[True, False, True], kind="stable").reset_index(drop=True)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    sites = discover_sites(root)
    helper_df, _ = load_helper_daily(root, sites)
    core_df, _ = load_core_daily(root, sites)
    runs_df, run_days_df = build_runs(helper_df)
    delta_df = load_delta_registry(root)
    fate_df = load_fate_cases(root)
    eligible_windows = load_eligible_windows(root)
    nuisance_windows = load_nuisance_windows(root)
    feature_df = build_run_feature_table(
        runs_df,
        run_days_df,
        core_df,
        delta_df,
        fate_df,
        eligible_windows,
        nuisance_windows,
    )
    distribution_df = build_distribution_summary(feature_df)
    comparison_df = build_comparison_summary(feature_df)
    summary_df = pd.concat([distribution_df, comparison_df], ignore_index=True)
    method_hints_df = build_method_hints(comparison_df)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    feature_df.to_csv(share_dir / "panel_day_engine_run_feature_table_v1.csv", index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / "panel_day_engine_run_feature_separability_summary_v1.csv", index=False, encoding="utf-8-sig")
    method_hints_df.to_csv(share_dir / "panel_day_engine_run_feature_method_hints_v1.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
