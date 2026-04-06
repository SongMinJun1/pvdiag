#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import build_panel_day_engine_run_ranker_v2_holdout_audit as holdout_base

DISCOVERY_NAME = "panel_day_engine_operator_secondary_discovery_v1.csv"
TRUTH_NAME = "panel_date_reaudit_working.csv"
HELPER_FILENAME = "ae_simple_local_precursor_gate_daily.csv"
CORE_FILENAME = "panel_day_core.csv"

CASES_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_fate_cases_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_fate_summary_v1.csv"

KEY_COLS = holdout_base.KEY_COLS
REQUIRED_DISCOVERY_COLS = [
    *KEY_COLS,
    "run_day_count",
    "run_shape_class",
    "logistic_v3_discovery_score",
    "electrical_core_minus_broadshape_050",
]
REQUIRED_TRUTH_COLS = ["site", "panel_id", "strict_trigger_date", "candidate_validity"]
REQUIRED_HELPER_COLS = ["panel_id", "date", "pre_ews", "ews_warning", "pre_alarm"]
REQUIRED_CORE_COLS = ["panel_id", "date", "confirmed_fault", "critical_fault", "final_fault"]
SHAPE_ORDER = {
    "chronic_alert_run": 0,
    "medium_alert_run": 1,
    "short_alert_run": 2,
}
LINKED_CLASSES = {"future_fault_linked", "future_truth_linked"}

CASE_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "logistic_v3_discovery_score",
    "electrical_core_minus_broadshape_050",
    "future_confirmed_fault_30d",
    "future_critical_fault_30d",
    "future_final_fault_30d",
    "future_confirmed_fault_60d",
    "future_critical_fault_60d",
    "future_final_fault_60d",
    "future_truth_overlap_30d",
    "future_truth_overlap_60d",
    "future_truth_case_ids",
    "future_truth_candidate_validities",
    "recurring_run_within_30d",
    "recurring_run_within_60d",
    "future_run_count_60d",
    "discovery_fate_class",
    "discovery_fate_reason_ko",
]

SUMMARY_COLS = [
    "record_type",
    "site",
    "selected_discovery_count",
    "selected_short_count",
    "selected_medium_count",
    "selected_chronic_count",
    "future_fault_linked_count",
    "future_truth_linked_count",
    "recurring_monitor_like_count",
    "isolated_unexplained_count",
    "future_fault_or_truth_linked_count",
    "future_fault_or_truth_linked_rate",
    "recurring_monitor_like_rate",
    "isolated_unexplained_rate",
    "short_run_isolated_rate",
    "short_run_fault_or_truth_linked_rate",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retrospectively evaluate whether the operator secondary discovery lane finds hidden value or mostly noisy runs."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the project root.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def parse_date(value: object) -> pd.Timestamp | pd.NaT:
    text = holdout_base.normalize_date(value)
    if not text:
        return pd.NaT
    return pd.to_datetime(text, errors="coerce")


def stable_unique_join(values: list[object]) -> str:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        text = holdout_base.normalize_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ";".join(ordered)


def to_int_flag(value: object) -> int:
    text = holdout_base.normalize_text(value).lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return 1
    if text in {"0", "false", "f", "no", "n", ""}:
        return 0
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return int(bool(numeric)) if not pd.isna(numeric) else 0


def load_discovery(root: Path) -> pd.DataFrame:
    path = root / "_share" / DISCOVERY_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_DISCOVERY_COLS, path.name)
    df = holdout_base.normalize_key_cols(df)
    df["run_shape_class"] = df["run_shape_class"].map(holdout_base.normalize_text)
    for col in ["run_day_count", "logistic_v3_discovery_score", "electrical_core_minus_broadshape_050"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["run_end_ts"] = df["run_end_date"].map(parse_date)
    df["run_start_ts"] = df["run_start_date"].map(parse_date)
    return (
        df.loc[:, [*REQUIRED_DISCOVERY_COLS, "run_start_ts", "run_end_ts"]]
        .drop_duplicates(subset=KEY_COLS, keep="first")
        .reset_index(drop=True)
    )


def selected_panel_map(discovery_df: pd.DataFrame) -> dict[str, set[str]]:
    return {
        site: set(group["panel_id"].tolist())
        for site, group in discovery_df.groupby("site", sort=False)
    }


def load_truth(root: Path, discovery_df: pd.DataFrame) -> pd.DataFrame:
    path = root / "_share" / TRUTH_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_TRUTH_COLS, path.name)
    panel_pairs = {
        tuple(row)
        for row in discovery_df.loc[:, ["site", "panel_id"]].drop_duplicates().itertuples(index=False, name=None)
    }
    df["site"] = df["site"].map(holdout_base.normalize_text)
    df["panel_id"] = df["panel_id"].map(holdout_base.normalize_text)
    df["strict_trigger_date"] = df["strict_trigger_date"].map(holdout_base.normalize_date)
    df["candidate_validity"] = df["candidate_validity"].map(holdout_base.normalize_text)
    df["panel_pair"] = list(zip(df["site"], df["panel_id"]))
    df = df.loc[df["panel_pair"].isin(panel_pairs)].copy()
    df["strict_trigger_ts"] = df["strict_trigger_date"].map(parse_date)
    df["truth_case_id"] = df.apply(
        lambda row: f"{row['site']}|{row['panel_id']}|{row['strict_trigger_date']}",
        axis=1,
    )
    return df.loc[:, ["site", "panel_id", "strict_trigger_date", "strict_trigger_ts", "candidate_validity", "truth_case_id"]].copy()


def load_helper(root: Path, discovery_df: pd.DataFrame) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for site, panel_ids in selected_panel_map(discovery_df).items():
        path = root / "data" / site / "out" / HELPER_FILENAME
        df = read_csv(path)
        ensure_columns(df, REQUIRED_HELPER_COLS, path.name)
        df = df.copy()
        if "site" not in df.columns:
            df["site"] = site
        df["site"] = df["site"].map(holdout_base.normalize_text)
        df.loc[df["site"].eq(""), "site"] = site
        df["panel_id"] = df["panel_id"].map(holdout_base.normalize_text)
        df["date"] = df["date"].map(holdout_base.normalize_date)
        for col in ["pre_ews", "ews_warning", "pre_alarm"]:
            df[col] = df[col].map(to_int_flag).astype(int)
        df = df.loc[df["site"].eq(site) & df["panel_id"].isin(panel_ids), ["site", "panel_id", "date", "pre_ews", "ews_warning", "pre_alarm"]].copy()
        if df.empty:
            continue
        df = (
            df.groupby(["site", "panel_id", "date"], as_index=False, dropna=False)[["pre_ews", "ews_warning", "pre_alarm"]]
            .max()
        )
        df["date_ts"] = df["date"].map(parse_date)
        df["alert_active"] = (
            df["pre_ews"].eq(1) | df["ews_warning"].eq(1) | df["pre_alarm"].eq(1)
        ).astype(int)
        parts.append(df)
    if not parts:
        return pd.DataFrame(columns=["site", "panel_id", "date", "date_ts", "pre_ews", "ews_warning", "pre_alarm", "alert_active"])
    return pd.concat(parts, ignore_index=True)


def load_core(root: Path, discovery_df: pd.DataFrame) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for site, panel_ids in selected_panel_map(discovery_df).items():
        path = root / "data" / site / "out" / CORE_FILENAME
        df = read_csv(path)
        ensure_columns(df, REQUIRED_CORE_COLS, path.name)
        df = df.copy()
        df["site"] = site
        df["panel_id"] = df["panel_id"].map(holdout_base.normalize_text)
        df["date"] = df["date"].map(holdout_base.normalize_date)
        for col in ["confirmed_fault", "critical_fault", "final_fault"]:
            df[col] = df[col].map(to_int_flag).astype(int)
        df = df.loc[df["panel_id"].isin(panel_ids), ["site", "panel_id", "date", "confirmed_fault", "critical_fault", "final_fault"]].copy()
        if df.empty:
            continue
        df = (
            df.groupby(["site", "panel_id", "date"], as_index=False, dropna=False)[["confirmed_fault", "critical_fault", "final_fault"]]
            .max()
        )
        df["date_ts"] = df["date"].map(parse_date)
        parts.append(df)
    if not parts:
        return pd.DataFrame(columns=["site", "panel_id", "date", "date_ts", "confirmed_fault", "critical_fault", "final_fault"])
    return pd.concat(parts, ignore_index=True)


def build_future_alert_runs(helper_df: pd.DataFrame) -> pd.DataFrame:
    active = helper_df.loc[helper_df["alert_active"].eq(1)].copy()
    if active.empty:
        return pd.DataFrame(
            columns=["site", "panel_id", "run_start_date", "run_end_date", "run_start_ts", "run_end_ts", "run_day_count"]
        )
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
                cur_ts = group.loc[idx, "date_ts"]
                is_break = pd.isna(prev_ts) or pd.isna(cur_ts) or cur_ts != prev_ts + one_day
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
    future_fault_cols = [
        "future_confirmed_fault_30d",
        "future_critical_fault_30d",
        "future_final_fault_30d",
        "future_confirmed_fault_60d",
        "future_critical_fault_60d",
        "future_final_fault_60d",
    ]
    if any(int(row[col]) == 1 for col in future_fault_cols):
        return "future_fault_linked", "30~60일 내 동일 패널 후행 confirmed/critical/final fault가 재등장해 hidden value가 확인된다."
    if int(row["future_truth_overlap_30d"]) == 1 or int(row["future_truth_overlap_60d"]) == 1:
        return "future_truth_linked", "30~60일 내 같은 패널 truth row가 다시 붙어 learned discovery가 후행 truth와 연결된다."
    if int(row["recurring_run_within_60d"]) == 1:
        return "recurring_monitor_like", "후행 fault/truth는 없지만 60일 내 helper-derived alert run이 반복되어 monitor burden형으로 보인다."
    return "isolated_unexplained", "후행 fault, truth, recurrence가 없어 현재 시점에서는 isolated short/noisy discovery에 가깝다."


def build_case_rows(discovery_df: pd.DataFrame, core_df: pd.DataFrame, truth_df: pd.DataFrame, future_runs_df: pd.DataFrame) -> pd.DataFrame:
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
        for (site, panel_id), group in future_runs_df.groupby(["site", "panel_id"], sort=False)
    }

    rows: list[dict[str, object]] = []
    for run in discovery_df.itertuples(index=False):
        key = (run.site, run.panel_id)
        panel_core = core_index.get(key, pd.DataFrame(columns=["date_ts", "confirmed_fault", "critical_fault", "final_fault"]))
        panel_truth = truth_index.get(key, pd.DataFrame(columns=["strict_trigger_ts", "candidate_validity", "truth_case_id"]))
        panel_runs = runs_index.get(key, pd.DataFrame(columns=["run_start_ts", "run_end_ts"]))

        row = {
            "site": run.site,
            "panel_id": run.panel_id,
            "run_start_date": run.run_start_date,
            "run_end_date": run.run_end_date,
            "run_day_count": int(run.run_day_count),
            "run_shape_class": run.run_shape_class,
            "logistic_v3_discovery_score": float(run.logistic_v3_discovery_score),
            "electrical_core_minus_broadshape_050": float(run.electrical_core_minus_broadshape_050),
        }
        for days in [30, 60]:
            row[f"future_confirmed_fault_{days}d"] = any_future_flag(panel_core, run.run_end_ts, days, "confirmed_fault")
            row[f"future_critical_fault_{days}d"] = any_future_flag(panel_core, run.run_end_ts, days, "critical_fault")
            row[f"future_final_fault_{days}d"] = any_future_flag(panel_core, run.run_end_ts, days, "final_fault")

        truth_30 = future_truth_info(panel_truth, run.run_end_ts, 30)
        truth_60 = future_truth_info(panel_truth, run.run_end_ts, 60)
        row["future_truth_overlap_30d"] = int(len(truth_30) > 0)
        row["future_truth_overlap_60d"] = int(len(truth_60) > 0)
        row["future_truth_case_ids"] = stable_unique_join(truth_60["truth_case_id"].tolist())
        row["future_truth_candidate_validities"] = stable_unique_join(truth_60["candidate_validity"].tolist())

        future_runs_30 = future_runs_info(panel_runs, run.run_end_ts, 30)
        future_runs_60 = future_runs_info(panel_runs, run.run_end_ts, 60)
        row["recurring_run_within_30d"] = int(len(future_runs_30) > 0)
        row["recurring_run_within_60d"] = int(len(future_runs_60) > 0)
        row["future_run_count_60d"] = int(len(future_runs_60))

        fate_class, fate_reason = classify_fate(row)
        row["discovery_fate_class"] = fate_class
        row["discovery_fate_reason_ko"] = fate_reason
        rows.append(row)

    case_df = pd.DataFrame(rows, columns=CASE_COLS)
    case_df["_shape_priority"] = case_df["run_shape_class"].map(SHAPE_ORDER).fillna(9).astype(int)
    case_df = case_df.sort_values(
        ["_shape_priority", "logistic_v3_discovery_score", "run_day_count", "site", "panel_id", "run_start_date", "run_end_date"],
        ascending=[True, False, False, True, True, True, True],
        kind="stable",
    ).drop(columns="_shape_priority")
    return case_df.reindex(columns=CASE_COLS).reset_index(drop=True)


def build_summary(case_df: pd.DataFrame) -> pd.DataFrame:
    def summarize(record_type: str, site: str, df: pd.DataFrame) -> dict[str, object]:
        selected_count = int(len(df))
        short_df = df.loc[df["run_shape_class"].eq("short_alert_run")].copy()
        linked_count = int(df["discovery_fate_class"].isin(LINKED_CLASSES).sum()) if not df.empty else 0
        row = {
            "record_type": record_type,
            "site": site,
            "selected_discovery_count": selected_count,
            "selected_short_count": int(df["run_shape_class"].eq("short_alert_run").sum()) if not df.empty else 0,
            "selected_medium_count": int(df["run_shape_class"].eq("medium_alert_run").sum()) if not df.empty else 0,
            "selected_chronic_count": int(df["run_shape_class"].eq("chronic_alert_run").sum()) if not df.empty else 0,
            "future_fault_linked_count": int(df["discovery_fate_class"].eq("future_fault_linked").sum()) if not df.empty else 0,
            "future_truth_linked_count": int(df["discovery_fate_class"].eq("future_truth_linked").sum()) if not df.empty else 0,
            "recurring_monitor_like_count": int(df["discovery_fate_class"].eq("recurring_monitor_like").sum()) if not df.empty else 0,
            "isolated_unexplained_count": int(df["discovery_fate_class"].eq("isolated_unexplained").sum()) if not df.empty else 0,
            "future_fault_or_truth_linked_count": linked_count,
            "future_fault_or_truth_linked_rate": (linked_count / selected_count) if selected_count else 0.0,
            "recurring_monitor_like_rate": (int(df["discovery_fate_class"].eq("recurring_monitor_like").sum()) / selected_count) if selected_count else 0.0,
            "isolated_unexplained_rate": (int(df["discovery_fate_class"].eq("isolated_unexplained").sum()) / selected_count) if selected_count else 0.0,
            "short_run_isolated_rate": (
                int(short_df["discovery_fate_class"].eq("isolated_unexplained").sum()) / int(len(short_df))
                if len(short_df) else 0.0
            ),
            "short_run_fault_or_truth_linked_rate": (
                int(short_df["discovery_fate_class"].isin(LINKED_CLASSES).sum()) / int(len(short_df))
                if len(short_df) else 0.0
            ),
            "note_ko": "secondary discovery lane가 hidden value를 찾는지, 아니면 short/noisy burden 중심인지 retrospective fate로 요약",
        }
        return row

    rows = [summarize("overall", "", case_df)]
    for site in sorted(case_df["site"].dropna().map(holdout_base.normalize_text).unique()):
        rows.append(summarize("site", site, case_df.loc[case_df["site"].eq(site)].copy()))
    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def save_outputs(root: Path, case_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    case_df.to_csv(share_dir / CASES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    discovery_df = load_discovery(root)
    truth_df = load_truth(root, discovery_df)
    helper_df = load_helper(root, discovery_df)
    core_df = load_core(root, discovery_df)
    future_runs_df = build_future_alert_runs(helper_df)
    case_df = build_case_rows(discovery_df, core_df, truth_df, future_runs_df)
    summary_df = build_summary(case_df)
    save_outputs(root, case_df, summary_df)


if __name__ == "__main__":
    main()
