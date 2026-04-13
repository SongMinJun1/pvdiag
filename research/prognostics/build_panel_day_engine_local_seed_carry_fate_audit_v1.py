#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DELTA_REGISTRY_NAME = "panel_day_engine_local_seed_carry_delta_run_registry_v1.csv"
HELPER_FILENAME = "ae_simple_local_precursor_gate_daily.csv"
CORE_FILENAME = "panel_day_core.csv"
TRUTH_NAME = "panel_date_reaudit_working.csv"
TARGET_VERSION = "current_seed_carry1"
TARGET_DELTA_CLASSES = {"added_run", "extended_run"}
TARGET_OVERLAP_CLASS = "unmatched_to_review"
DEFAULT_TOP_N = 20
DEFAULT_TOP_PER_SITE = 5
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
CORE_FAULT_COLS = ["confirmed_fault", "critical_fault", "final_fault"]
CORE_REASON_COLS = ["recon_error", "dtw_dist", "hs_score", "mid_ratio", "mid_v_ratio", "mid_i_ratio", "v_drop"]
CORE_COLS = [*CORE_FAULT_COLS, *CORE_REASON_COLS]
CASE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "delta_run_class",
    "evidence_reason_ko",
    "future_confirmed_fault_7d",
    "future_critical_fault_7d",
    "future_final_fault_7d",
    "future_confirmed_fault_30d",
    "future_critical_fault_30d",
    "future_final_fault_30d",
    "future_confirmed_fault_60d",
    "future_critical_fault_60d",
    "future_final_fault_60d",
    "future_truth_overlap_30d",
    "future_truth_overlap_60d",
    "future_truth_candidate_validities",
    "future_truth_case_ids",
    "recurring_run_within_30d",
    "recurring_run_within_60d",
    "future_run_count_60d",
    "fate_class",
    "fate_reason_ko",
]
SUMMARY_COLS = [
    "record_type",
    "site",
    "selected_run_count",
    "chronic_run_count",
    "future_fault_linked_count",
    "future_truth_linked_count",
    "recurring_chronic_monitor_like_count",
    "isolated_unexplained_count",
    "future_fault_or_truth_linked_count",
    "future_fault_or_truth_linked_rate",
    "recurring_like_rate",
    "isolated_unexplained_rate",
    "excluded_conflicting_helper_key_count",
    "excluded_conflicting_core_key_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retrospectively classify top current_seed_carry1 unmatched runs by later fate."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the project root.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=DEFAULT_TOP_N,
        help="Top overall runs to select before per-site fill. Defaults to 20.",
    )
    parser.add_argument(
        "--top-per-site",
        type=int,
        default=DEFAULT_TOP_PER_SITE,
        help="Minimum top runs to include per site when available. Defaults to 5.",
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


def stable_unique_join(values: list[str]) -> str:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        text = normalize_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ";".join(ordered)


def normalize_helper_value(col: str, value: object) -> object:
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


def normalize_core_value(col: str, value: object) -> object:
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
    excluded = 0
    for _, group in dup_df.groupby(key_cols, sort=False, dropna=False):
        normalized_rows = {
            tuple(normalize_value(col, group.iloc[idx][col]) for col in value_cols)
            for idx in range(len(group))
        }
        if len(normalized_rows) > 1:
            excluded += 1
            continue
        keep_rows.append(group.nsmallest(1, "_row_order"))

    unique_rows = df.loc[~duplicated].copy()
    collapsed = pd.concat([unique_rows, *keep_rows], ignore_index=True) if keep_rows else unique_rows
    return collapsed.sort_values("_row_order", kind="stable").reset_index(drop=True), excluded


def load_delta_registry(root: Path) -> pd.DataFrame:
    path = root / "_share" / DELTA_REGISTRY_NAME
    df = read_csv(path)
    required = [
        "version",
        "site",
        "panel_id",
        "run_start_date",
        "run_end_date",
        "run_day_count",
        "run_shape_class",
        "delta_run_class",
        "overlap_case_class",
    ]
    ensure_columns(df, required, path.name)
    df = df.copy()
    for col in ["version", "site", "panel_id", "run_shape_class", "delta_run_class", "overlap_case_class"]:
        df[col] = df[col].map(normalize_text)
    for col in ["run_start_date", "run_end_date"]:
        df[col] = df[col].map(normalize_date)
    df["run_day_count"] = pd.to_numeric(df["run_day_count"], errors="coerce").fillna(0).astype(int)
    return df


def select_priority_runs(delta_df: pd.DataFrame, top_n: int, top_per_site: int) -> pd.DataFrame:
    candidates = delta_df.loc[
        delta_df["version"].eq(TARGET_VERSION)
        & delta_df["overlap_case_class"].eq(TARGET_OVERLAP_CLASS)
        & delta_df["delta_run_class"].isin(TARGET_DELTA_CLASSES)
    ].copy()
    if candidates.empty:
        return candidates
    priority = {
        "chronic_alert_run": 0,
        "medium_alert_run": 1,
        "short_alert_run": 2,
    }
    candidates["_shape_priority"] = candidates["run_shape_class"].map(priority).fillna(9).astype(int)
    candidates["_run_start_ts"] = candidates["run_start_date"].map(parse_date)
    candidates = candidates.sort_values(
        ["_shape_priority", "run_day_count", "_run_start_ts", "site", "panel_id", "run_end_date"],
        ascending=[True, False, True, True, True, True],
        kind="stable",
    ).reset_index(drop=True)
    selected = pd.concat(
        [
            candidates.head(top_n),
            candidates.groupby("site", sort=False, group_keys=False).head(top_per_site),
        ],
        ignore_index=True,
    )
    selected = selected.drop_duplicates(subset=RUN_KEY_COLS, keep="first")
    selected["run_start_ts"] = selected["run_start_date"].map(parse_date)
    selected["run_end_ts"] = selected["run_end_date"].map(parse_date)
    return selected.sort_values(
        ["_shape_priority", "run_day_count", "run_start_ts", "site", "panel_id", "run_end_date"],
        ascending=[True, False, True, True, True, True],
        kind="stable",
    ).reset_index(drop=True)


def load_helper_for_selected_panels(root: Path, selected_runs: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    selected_panels = selected_runs.loc[:, ["site", "panel_id"]].drop_duplicates().copy()
    panel_map = {
        site: set(group["panel_id"].tolist())
        for site, group in selected_panels.groupby("site", sort=False)
    }
    parts: list[pd.DataFrame] = []
    excluded_total = 0
    for site, panel_ids in panel_map.items():
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
        df = df.loc[df["site"].eq(site) & df["panel_id"].isin(panel_ids), [*DAY_KEY_COLS, *HELPER_COLS]].copy()
        df["_row_order"] = range(len(df))
        df, excluded = collapse_exact_duplicates(
            df,
            key_cols=DAY_KEY_COLS,
            value_cols=HELPER_COLS,
            normalize_value=normalize_helper_value,
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


def load_core_for_selected_panels(root: Path, selected_runs: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    selected_panels = selected_runs.loc[:, ["site", "panel_id"]].drop_duplicates().copy()
    panel_map = {
        site: set(group["panel_id"].tolist())
        for site, group in selected_panels.groupby("site", sort=False)
    }
    parts: list[pd.DataFrame] = []
    excluded_total = 0
    for site, panel_ids in panel_map.items():
        path = root / "data" / site / "out" / CORE_FILENAME
        df = read_csv(path)
        ensure_columns(df, ["panel_id", "date", *CORE_COLS], path.name)
        df = df.copy()
        df["site"] = site
        df["site"] = df["site"].map(normalize_text)
        df["panel_id"] = df["panel_id"].map(normalize_text)
        df["date"] = df["date"].map(normalize_date)
        df = df.loc[df["site"].eq(site) & df["panel_id"].isin(panel_ids), [*DAY_KEY_COLS, *CORE_COLS]].copy()
        df["_row_order"] = range(len(df))
        df, excluded = collapse_exact_duplicates(
            df,
            key_cols=DAY_KEY_COLS,
            value_cols=CORE_COLS,
            normalize_value=normalize_core_value,
        )
        excluded_total += excluded
        for col in CORE_FAULT_COLS:
            df[col] = df[col].map(to_int_flag).astype(int)
        for col in CORE_REASON_COLS:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["date_ts"] = df["date"].map(parse_date)
        parts.append(df.loc[:, [*DAY_KEY_COLS, "date_ts", *CORE_COLS]].copy())
    core = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=[*DAY_KEY_COLS, "date_ts", *CORE_COLS])
    return core.drop_duplicates(subset=DAY_KEY_COLS, keep="first").copy(), excluded_total


def load_truth(root: Path, selected_runs: pd.DataFrame) -> pd.DataFrame:
    path = root / "_share" / TRUTH_NAME
    df = read_csv(path)
    ensure_columns(df, ["site", "panel_id", "strict_trigger_date", "candidate_validity"], path.name)
    selected_panels = selected_runs.loc[:, ["site", "panel_id"]].drop_duplicates().copy()
    panel_pairs = {(row.site, row.panel_id) for row in selected_panels.itertuples(index=False)}
    df = df.copy()
    df["site"] = df["site"].map(normalize_text)
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["strict_trigger_date"] = df["strict_trigger_date"].map(normalize_date)
    df["candidate_validity"] = df["candidate_validity"].map(normalize_text)
    df["strict_trigger_ts"] = df["strict_trigger_date"].map(parse_date)
    df["panel_pair"] = list(zip(df["site"], df["panel_id"]))
    df = df.loc[df["panel_pair"].isin(panel_pairs)].copy()
    df["truth_case_id"] = df.apply(
        lambda row: f"{row['site']}|{row['panel_id']}|{row['strict_trigger_date']}",
        axis=1,
    )
    return df


def build_prealarm_runs(helper_df: pd.DataFrame) -> pd.DataFrame:
    active = helper_df.loc[helper_df["pre_alarm"].eq(1)].copy()
    if active.empty:
        return pd.DataFrame(columns=["site", "panel_id", "run_start_date", "run_end_date", "run_start_ts", "run_end_ts", "run_day_count"])
    active = active.sort_values(["site", "panel_id", "date_ts", "date"], kind="stable").reset_index(drop=True)
    one_day = pd.Timedelta(days=1)
    records: list[dict[str, object]] = []
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
            run_df = group.iloc[run_start_idx:idx]
            records.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "run_start_date": run_df.iloc[0]["date"],
                    "run_end_date": run_df.iloc[-1]["date"],
                    "run_start_ts": run_df.iloc[0]["date_ts"],
                    "run_end_ts": run_df.iloc[-1]["date_ts"],
                    "run_day_count": int(len(run_df)),
                }
            )
            run_start_idx = idx
    return pd.DataFrame(records)


def max_or_blank(df: pd.DataFrame, col: str) -> object:
    series = pd.to_numeric(df[col], errors="coerce")
    return float(series.max()) if series.notna().any() else ""


def min_or_blank(df: pd.DataFrame, col: str) -> object:
    series = pd.to_numeric(df[col], errors="coerce")
    return float(series.min()) if series.notna().any() else ""


def classify_evidence_reason(run_df: pd.DataFrame) -> str:
    cond_evt = run_df["cond_evt"].fillna(0).astype(int)
    cond_var = run_df["cond_var"].fillna(0).astype(int)
    cond_dtw = run_df["cond_dtw"].fillna(0).astype(int)
    cond_hs = run_df["cond_hs"].fillna(0).astype(int)
    early_any = (
        run_df["ae_mid_or_hi_early"].fillna(0).astype(int).eq(1)
        | run_df["dtw_mid_or_hi_early"].fillna(0).astype(int).eq(1)
        | run_df["hs_mid_or_hi_early"].fillna(0).astype(int).eq(1)
    )
    cond_evt_count = int(cond_evt.sum())
    cond_evt_only_count = int((cond_evt.eq(1) & cond_var.eq(0) & cond_dtw.eq(0) & cond_hs.eq(0)).sum())
    corroborated_count = int((cond_evt.eq(1) & early_any).sum())
    evt_only_ratio = cond_evt_only_count / cond_evt_count if cond_evt_count else 0.0
    corroborated_ratio = corroborated_count / cond_evt_count if cond_evt_count else 0.0
    run_day_count = len(run_df)
    electrical_flag = any(
        value != "" and value <= 0.75
        for value in [
            min_or_blank(run_df, "mid_ratio"),
            min_or_blank(run_df, "mid_v_ratio"),
            min_or_blank(run_df, "mid_i_ratio"),
        ]
    ) or (max_or_blank(run_df, "v_drop") != "" and max_or_blank(run_df, "v_drop") >= 0.15)
    if run_day_count >= 10 and cond_evt_count >= 5 and evt_only_ratio >= 0.7:
        return "evt_only_chronic"
    if run_day_count >= 10 and cond_evt_count >= 5 and corroborated_ratio >= 0.6:
        return "corroborated_chronic"
    if electrical_flag and run_day_count >= 5 and corroborated_ratio >= 0.4:
        return "electrical_drift_like"
    if electrical_flag or (
        (max_or_blank(run_df, "recon_error") != "" and max_or_blank(run_df, "recon_error") >= 0.8)
        or (max_or_blank(run_df, "dtw_dist") != "" and max_or_blank(run_df, "dtw_dist") >= 0.8)
        or (max_or_blank(run_df, "hs_score") != "" and max_or_blank(run_df, "hs_score") >= 0.8)
    ):
        return "mixed_shape_electrical"
    return "weak_short_run"


def any_future_flag(panel_core: pd.DataFrame, end_ts: pd.Timestamp, days: int, col: str) -> int:
    if panel_core.empty or pd.isna(end_ts):
        return 0
    window_end = end_ts + pd.Timedelta(days=days)
    mask = panel_core["date_ts"].gt(end_ts) & panel_core["date_ts"].le(window_end)
    return int(panel_core.loc[mask, col].fillna(0).astype(int).gt(0).any())


def future_truth_info(panel_truth: pd.DataFrame, end_ts: pd.Timestamp, days: int) -> pd.DataFrame:
    if panel_truth.empty or pd.isna(end_ts):
        return panel_truth.iloc[0:0].copy()
    window_end = end_ts + pd.Timedelta(days=days)
    return panel_truth.loc[panel_truth["strict_trigger_ts"].gt(end_ts) & panel_truth["strict_trigger_ts"].le(window_end)].copy()


def future_runs_info(panel_runs: pd.DataFrame, end_ts: pd.Timestamp, days: int) -> pd.DataFrame:
    if panel_runs.empty or pd.isna(end_ts):
        return panel_runs.iloc[0:0].copy()
    window_end = end_ts + pd.Timedelta(days=days)
    return panel_runs.loc[panel_runs["run_start_ts"].gt(end_ts) & panel_runs["run_start_ts"].le(window_end)].copy()


def classify_fate(row: dict[str, object]) -> tuple[str, str]:
    if any(int(row[col]) == 1 for col in [
        "future_confirmed_fault_30d",
        "future_critical_fault_30d",
        "future_final_fault_30d",
        "future_confirmed_fault_60d",
        "future_critical_fault_60d",
        "future_final_fault_60d",
    ]):
        return "future_fault_linked", "30~60일 내 동일 패널 fault 재확인으로 후행 linkage가 보임"
    if int(row["future_truth_overlap_30d"]) == 1 or int(row["future_truth_overlap_60d"]) == 1:
        return "future_truth_linked", "30~60일 내 같은 패널 truth row가 다시 붙어 후행 truth linkage가 보임"
    if int(row["recurring_run_within_60d"]) == 1:
        return "recurring_chronic_monitor_like", "fault/truth는 없지만 60일 내 pre_alarm run 재발이 있어 chronic monitor형으로 보임"
    return "isolated_unexplained", "후행 fault/truth/run recurrence가 없어 isolated burden으로 남음"


def build_case_rows(
    selected_runs: pd.DataFrame,
    helper_df: pd.DataFrame,
    core_df: pd.DataFrame,
    truth_df: pd.DataFrame,
    all_runs_df: pd.DataFrame,
) -> pd.DataFrame:
    helper_index = {
        (site, panel_id): group.sort_values(["date_ts", "date"], kind="stable").reset_index(drop=True)
        for (site, panel_id), group in helper_df.groupby(["site", "panel_id"], sort=False)
    }
    core_index = {
        (site, panel_id): group.sort_values(["date_ts", "date"], kind="stable").reset_index(drop=True)
        for (site, panel_id), group in core_df.groupby(["site", "panel_id"], sort=False)
    }
    truth_index = {
        (site, panel_id): group.sort_values(["strict_trigger_ts", "strict_trigger_date"], kind="stable").reset_index(drop=True)
        for (site, panel_id), group in truth_df.groupby(["site", "panel_id"], sort=False)
    }
    runs_index = {
        (site, panel_id): group.sort_values(["run_start_ts", "run_end_ts"], kind="stable").reset_index(drop=True)
        for (site, panel_id), group in all_runs_df.groupby(["site", "panel_id"], sort=False)
    }

    records: list[dict[str, object]] = []
    for run in selected_runs.itertuples(index=False):
        key = (run.site, run.panel_id)
        panel_helper = helper_index.get(key, pd.DataFrame(columns=[*DAY_KEY_COLS, "date_ts", *HELPER_COLS]))
        panel_core = core_index.get(key, pd.DataFrame(columns=[*DAY_KEY_COLS, "date_ts", *CORE_COLS]))
        panel_truth = truth_index.get(key, pd.DataFrame(columns=["truth_case_id", "candidate_validity", "strict_trigger_ts"]))
        panel_runs = runs_index.get(key, pd.DataFrame(columns=["run_start_ts", "run_end_ts"]))

        run_days = panel_helper.loc[
            panel_helper["date_ts"].ge(run.run_start_ts) & panel_helper["date_ts"].le(run.run_end_ts)
        ].copy()
        run_days = run_days.merge(core_df, on=DAY_KEY_COLS + ["date_ts"], how="left")
        evidence_reason = classify_evidence_reason(run_days) if not run_days.empty else "weak_short_run"

        row = {
            "site": run.site,
            "panel_id": run.panel_id,
            "run_start_date": run.run_start_date,
            "run_end_date": run.run_end_date,
            "run_day_count": int(run.run_day_count),
            "run_shape_class": run.run_shape_class,
            "delta_run_class": run.delta_run_class,
            "evidence_reason_ko": evidence_reason,
        }
        for days in [7, 30, 60]:
            row[f"future_confirmed_fault_{days}d"] = any_future_flag(panel_core, run.run_end_ts, days, "confirmed_fault")
            row[f"future_critical_fault_{days}d"] = any_future_flag(panel_core, run.run_end_ts, days, "critical_fault")
            row[f"future_final_fault_{days}d"] = any_future_flag(panel_core, run.run_end_ts, days, "final_fault")

        truth_30 = future_truth_info(panel_truth, run.run_end_ts, 30)
        truth_60 = future_truth_info(panel_truth, run.run_end_ts, 60)
        row["future_truth_overlap_30d"] = int(len(truth_30) > 0)
        row["future_truth_overlap_60d"] = int(len(truth_60) > 0)
        row["future_truth_candidate_validities"] = stable_unique_join(truth_60["candidate_validity"].tolist())
        row["future_truth_case_ids"] = stable_unique_join(truth_60["truth_case_id"].tolist())

        future_runs_30 = future_runs_info(panel_runs, run.run_end_ts, 30)
        future_runs_60 = future_runs_info(panel_runs, run.run_end_ts, 60)
        row["recurring_run_within_30d"] = int(len(future_runs_30) > 0)
        row["recurring_run_within_60d"] = int(len(future_runs_60) > 0)
        row["future_run_count_60d"] = int(len(future_runs_60))

        fate_class, fate_reason = classify_fate(row)
        row["fate_class"] = fate_class
        row["fate_reason_ko"] = fate_reason
        records.append(row)

    return pd.DataFrame(records).reindex(columns=CASE_COLS)


def build_summary(case_df: pd.DataFrame, *, excluded_helper: int, excluded_core: int) -> pd.DataFrame:
    def summarize(record_type: str, site: str, df: pd.DataFrame) -> dict[str, object]:
        selected_run_count = int(len(df))
        future_fault_linked_count = int(df["fate_class"].eq("future_fault_linked").sum()) if not df.empty else 0
        future_truth_linked_count = int(df["fate_class"].eq("future_truth_linked").sum()) if not df.empty else 0
        recurring_count = int(df["fate_class"].eq("recurring_chronic_monitor_like").sum()) if not df.empty else 0
        isolated_count = int(df["fate_class"].eq("isolated_unexplained").sum()) if not df.empty else 0
        linked_total = future_fault_linked_count + future_truth_linked_count
        return {
            "record_type": record_type,
            "site": site,
            "selected_run_count": selected_run_count,
            "chronic_run_count": int(df["run_shape_class"].eq("chronic_alert_run").sum()) if not df.empty else 0,
            "future_fault_linked_count": future_fault_linked_count,
            "future_truth_linked_count": future_truth_linked_count,
            "recurring_chronic_monitor_like_count": recurring_count,
            "isolated_unexplained_count": isolated_count,
            "future_fault_or_truth_linked_count": linked_total,
            "future_fault_or_truth_linked_rate": (linked_total / selected_run_count) if selected_run_count else 0.0,
            "recurring_like_rate": (recurring_count / selected_run_count) if selected_run_count else 0.0,
            "isolated_unexplained_rate": (isolated_count / selected_run_count) if selected_run_count else 0.0,
            "excluded_conflicting_helper_key_count": int(excluded_helper),
            "excluded_conflicting_core_key_count": int(excluded_core),
        }

    records = [summarize("overall", "", case_df)]
    for site in sorted(case_df["site"].dropna().astype(str).unique()):
        records.append(summarize("site", site, case_df.loc[case_df["site"].eq(site)].copy()))
    return pd.DataFrame(records).reindex(columns=SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    delta_df = load_delta_registry(root)
    selected_runs = select_priority_runs(delta_df, top_n=args.top_n, top_per_site=args.top_per_site)
    helper_df, excluded_helper = load_helper_for_selected_panels(root, selected_runs)
    core_df, excluded_core = load_core_for_selected_panels(root, selected_runs)
    truth_df = load_truth(root, selected_runs)
    all_runs_df = build_prealarm_runs(helper_df)
    case_df = build_case_rows(selected_runs, helper_df, core_df, truth_df, all_runs_df)
    summary_df = build_summary(case_df, excluded_helper=excluded_helper, excluded_core=excluded_core)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(
        share_dir / "panel_day_engine_local_seed_carry_fate_summary_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    case_df.to_csv(
        share_dir / "panel_day_engine_local_seed_carry_fate_cases_v1.csv",
        index=False,
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    main()
