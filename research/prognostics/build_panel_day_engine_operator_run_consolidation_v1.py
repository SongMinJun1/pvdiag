#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
V0_SCORES_NAME = "panel_day_engine_run_ranker_v0_scores.csv"
FATE_CASES_NAME = "panel_day_engine_local_seed_carry_fate_cases_v1.csv"
RUN_REGISTRY_OUTPUT_NAME = "panel_day_engine_operator_run_registry_v1.csv"
RUN_QUEUE_OUTPUT_NAME = "panel_day_engine_operator_run_queue_v1.csv"
RUN_BACKLOG_OUTPUT_NAME = "panel_day_engine_operator_run_backlog_v1.csv"
RUN_SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_run_summary_v1.csv"

KEY_COLS = ["site", "panel_id", "run_start_date", "run_end_date"]
STRING_COLS = ["site", "panel_id", "run_start_date", "run_end_date", "run_shape_class", "overlap_case_class", "fate_class", "cohort_hint"]
REQUIRED_FEATURE_COLS = [
    *KEY_COLS,
    "run_day_count",
    "run_shape_class",
    "overlap_case_class",
    "fate_class",
    "cohort_hint",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "recurring_run_within_60d",
    "future_fault_linked_flag",
    "future_truth_linked_flag",
]
REQUIRED_SCORE_COLS = [*KEY_COLS, "electrical_core_score", "electrical_core_minus_broadshape_050"]
OPTIONAL_FATE_COLS = [*KEY_COLS, "fate_class"]
STATUS_PRIORITY = {
    "ongoing_run": 0,
    "new_run": 1,
    "recurring_run": 2,
    "recovered_run": 3,
    "historical_run": 4,
}
PRIORITY_PRIORITY = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
ACTION_BUCKET_PRIORITY = {
    "investigate_now": 0,
    "monitor_active": 1,
    "recurring_backlog": 2,
    "recovered_backlog": 3,
    "historical_archive": 4,
}
REGISTRY_OUTPUT_COLS = [
    "site",
    "panel_id",
    "run_start_date",
    "run_end_date",
    "run_day_count",
    "run_shape_class",
    "cohort_hint",
    "fate_class",
    "electrical_core_score",
    "electrical_core_minus_broadshape_050",
    "max_v_drop",
    "min_mid_v_ratio",
    "min_mid_ratio",
    "cond_evt_only_day_ratio",
    "ae_mid_or_hi_early_day_ratio",
    "status",
    "priority_band",
    "action_bucket",
    "queue_eligible_flag",
    "backlog_flag",
    "queue_reason_ko",
    "overlap_case_class",
    "future_fault_linked_flag",
    "future_truth_linked_flag",
]
SUMMARY_OUTPUT_COLS = [
    "record_type",
    "site",
    "total_runs",
    "ongoing_run_count",
    "new_run_count",
    "recurring_run_count",
    "recovered_run_count",
    "chronic_run_count",
    "p1_run_count",
    "p2_run_count",
    "investigate_now_count",
    "monitor_active_count",
    "recurring_backlog_count",
    "recovered_backlog_count",
    "historical_archive_count",
    "queue_count",
    "backlog_count",
    "queue_chronic_count",
    "backlog_chronic_count",
    "queue_future_fault_linked_count",
    "queue_future_truth_linked_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build operator-facing consolidated run artifacts from panel_day_engine run tables."
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


def load_feature_table(root: Path) -> pd.DataFrame:
    path = root / "_share" / FEATURE_TABLE_NAME
    df = read_csv(path)
    ensure_columns(df, REQUIRED_FEATURE_COLS, path.name)
    df = drop_repeated_header_rows(df).copy()
    for col in STRING_COLS:
        normalizer = normalize_date if col in {"run_start_date", "run_end_date"} else normalize_text
        df[col] = df[col].map(normalizer)
    for col in REQUIRED_FEATURE_COLS:
        if col in STRING_COLS:
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.loc[:, REQUIRED_FEATURE_COLS].copy()
    return df.drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_v0_scores(root: Path) -> pd.DataFrame:
    path = root / "_share" / V0_SCORES_NAME
    df = read_csv(path)
    ensure_columns(df, REQUIRED_SCORE_COLS, path.name)
    df = drop_repeated_header_rows(df).copy()
    for col in KEY_COLS:
        normalizer = normalize_date if col in {"run_start_date", "run_end_date"} else normalize_text
        df[col] = df[col].map(normalizer)
    for col in ["electrical_core_score", "electrical_core_minus_broadshape_050"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.loc[:, REQUIRED_SCORE_COLS].copy()
    return df.drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def load_optional_fate_cases(root: Path) -> pd.DataFrame:
    path = root / "_share" / FATE_CASES_NAME
    if not path.exists():
        return pd.DataFrame(columns=OPTIONAL_FATE_COLS)
    df = read_csv(path)
    ensure_columns(df, OPTIONAL_FATE_COLS, path.name)
    df = drop_repeated_header_rows(df).copy()
    for col in KEY_COLS:
        normalizer = normalize_date if col in {"run_start_date", "run_end_date"} else normalize_text
        df[col] = df[col].map(normalizer)
    df["fate_class"] = df["fate_class"].map(normalize_text)
    df = df.loc[:, OPTIONAL_FATE_COLS].copy()
    return df.drop_duplicates(subset=KEY_COLS, keep="first").reset_index(drop=True)


def assign_site_priority_bands(site_df: pd.DataFrame) -> pd.DataFrame:
    ordered = site_df.sort_values(
        ["electrical_core_minus_broadshape_050", "run_day_count", "panel_id", "run_start_date", "run_end_date"],
        ascending=[False, False, True, True, True],
        kind="mergesort",
    ).copy()
    n_rows = len(ordered)
    p1_cut = max(1, math.ceil(n_rows * 0.05))
    p2_cut = max(p1_cut, math.ceil(n_rows * 0.20))
    p3_cut = max(p2_cut, math.ceil(n_rows * 0.50))
    ordered["site_score_rank"] = range(1, n_rows + 1)
    ordered["priority_band"] = "P4"
    ordered.loc[ordered["site_score_rank"] <= p3_cut, "priority_band"] = "P3"
    ordered.loc[ordered["site_score_rank"] <= p2_cut, "priority_band"] = "P2"
    ordered.loc[ordered["site_score_rank"] <= p1_cut, "priority_band"] = "P1"
    return ordered


def assign_status(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["run_start_dt"] = pd.to_datetime(out["run_start_date"], errors="coerce")
    out["run_end_dt"] = pd.to_datetime(out["run_end_date"], errors="coerce")
    out["site_max_run_end_dt"] = out.groupby("site", dropna=False)["run_end_dt"].transform("max")

    start_delta = (out["site_max_run_end_dt"] - out["run_start_dt"]).dt.days
    end_delta = (out["site_max_run_end_dt"] - out["run_end_dt"]).dt.days

    ongoing = end_delta.between(0, 1, inclusive="both")
    new_run = start_delta.between(0, 3, inclusive="both")
    recurring = pd.to_numeric(out["recurring_run_within_60d"], errors="coerce").fillna(0).astype(int).eq(1)
    recovered = (~ongoing) & end_delta.between(0, 7, inclusive="both")

    status = pd.Series("historical_run", index=out.index)
    status.loc[recovered] = "recovered_run"
    status.loc[recurring] = "recurring_run"
    status.loc[new_run] = "new_run"
    status.loc[ongoing] = "ongoing_run"
    out["status"] = status
    return out


def assign_action_buckets(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    ongoing_or_new = out["status"].isin({"ongoing_run", "new_run"})
    investigate_now = ongoing_or_new & out["priority_band"].isin({"P1", "P2"})
    monitor_active = (
        ongoing_or_new
        & out["priority_band"].eq("P3")
        & out["run_shape_class"].isin({"medium_alert_run", "chronic_alert_run"})
    )
    recurring_backlog = out["status"].eq("recurring_run")
    recovered_backlog = out["status"].eq("recovered_run")

    action_bucket = pd.Series("historical_archive", index=out.index)
    action_bucket.loc[recovered_backlog] = "recovered_backlog"
    action_bucket.loc[recurring_backlog] = "recurring_backlog"
    action_bucket.loc[monitor_active] = "monitor_active"
    action_bucket.loc[investigate_now] = "investigate_now"
    out["action_bucket"] = action_bucket

    out["queue_eligible_flag"] = out["action_bucket"].isin({"investigate_now", "monitor_active"}).astype(int)
    out["backlog_flag"] = out["action_bucket"].isin({"recurring_backlog", "recovered_backlog"}).astype(int)

    reason = pd.Series("과거 archive", index=out.index)
    reason.loc[out["action_bucket"].eq("recovered_backlog")] = "최근 종료 backlog"
    reason.loc[out["action_bucket"].eq("recurring_backlog")] = "반복 chronic backlog"
    reason.loc[out["action_bucket"].eq("monitor_active")] = "진행중이며 중간 우선순위 chronic"
    reason.loc[out["action_bucket"].eq("investigate_now")] = "신규/진행중이며 상위 우선순위"
    out["queue_reason_ko"] = reason
    return out


def build_registry(root: Path) -> pd.DataFrame:
    feature_df = load_feature_table(root)
    v0_scores = load_v0_scores(root)
    fate_df = load_optional_fate_cases(root).rename(columns={"fate_class": "fate_class_fate"})

    merged = feature_df.merge(v0_scores, on=KEY_COLS, how="left", validate="one_to_one")
    if not fate_df.empty:
        merged = merged.merge(fate_df, on=KEY_COLS, how="left", validate="one_to_one")
        merged["fate_class"] = merged["fate_class"].map(normalize_text)
        merged["fate_class_fate"] = merged["fate_class_fate"].map(normalize_text)
        merged["fate_class"] = merged["fate_class"].where(merged["fate_class"].ne(""), merged["fate_class_fate"])
        merged = merged.drop(columns=["fate_class_fate"])
    else:
        merged["fate_class"] = merged["fate_class"].map(normalize_text)

    if merged["electrical_core_minus_broadshape_050"].isna().any():
        raise SystemExit("missing electrical_core_minus_broadshape_050 after merge")
    if merged["electrical_core_score"].isna().any():
        raise SystemExit("missing electrical_core_score after merge")

    merged["future_fault_linked_flag"] = pd.to_numeric(merged["future_fault_linked_flag"], errors="coerce").fillna(0).astype(int)
    merged["future_truth_linked_flag"] = pd.to_numeric(merged["future_truth_linked_flag"], errors="coerce").fillna(0).astype(int)

    merged = assign_status(merged)

    banded_parts = []
    for _, site_df in merged.groupby("site", sort=True, dropna=False):
        banded_parts.append(assign_site_priority_bands(site_df))
    registry = pd.concat(banded_parts, axis=0).sort_index()
    registry = assign_action_buckets(registry)
    registry = registry.sort_values(
        ["site", "site_score_rank", "run_day_count", "panel_id", "run_start_date", "run_end_date"],
        ascending=[True, True, False, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    return registry


def build_queue(registry: pd.DataFrame) -> pd.DataFrame:
    queue = registry.loc[registry["queue_eligible_flag"].eq(1)].copy()
    queue["_action_order"] = queue["action_bucket"].map(ACTION_BUCKET_PRIORITY).fillna(99)
    queue["_priority_order"] = queue["priority_band"].map(PRIORITY_PRIORITY).fillna(99)
    queue = queue.sort_values(
        [
            "_action_order",
            "_priority_order",
            "electrical_core_minus_broadshape_050",
            "run_day_count",
            "site",
            "panel_id",
            "run_start_date",
        ],
        ascending=[True, True, False, False, True, True, True],
        kind="mergesort",
    ).drop(columns=["_action_order", "_priority_order"])
    return queue.reset_index(drop=True)


def build_backlog(registry: pd.DataFrame) -> pd.DataFrame:
    backlog = registry.loc[registry["backlog_flag"].eq(1)].copy()
    backlog["_action_order"] = backlog["action_bucket"].map(ACTION_BUCKET_PRIORITY).fillna(99)
    backlog = backlog.sort_values(
        [
            "_action_order",
            "electrical_core_minus_broadshape_050",
            "run_day_count",
            "site",
            "panel_id",
            "run_start_date",
        ],
        ascending=[True, False, False, True, True, True],
        kind="mergesort",
    ).drop(columns=["_action_order"])
    return backlog.reset_index(drop=True)


def summarize_group(record_type: str, site: str, group: pd.DataFrame, queue: pd.DataFrame, backlog: pd.DataFrame) -> dict[str, object]:
    return {
        "record_type": record_type,
        "site": site,
        "total_runs": int(len(group)),
        "ongoing_run_count": int(group["status"].eq("ongoing_run").sum()),
        "new_run_count": int(group["status"].eq("new_run").sum()),
        "recurring_run_count": int(group["status"].eq("recurring_run").sum()),
        "recovered_run_count": int(group["status"].eq("recovered_run").sum()),
        "chronic_run_count": int(group["run_shape_class"].eq("chronic_alert_run").sum()),
        "p1_run_count": int(group["priority_band"].eq("P1").sum()),
        "p2_run_count": int(group["priority_band"].eq("P2").sum()),
        "investigate_now_count": int(group["action_bucket"].eq("investigate_now").sum()),
        "monitor_active_count": int(group["action_bucket"].eq("monitor_active").sum()),
        "recurring_backlog_count": int(group["action_bucket"].eq("recurring_backlog").sum()),
        "recovered_backlog_count": int(group["action_bucket"].eq("recovered_backlog").sum()),
        "historical_archive_count": int(group["action_bucket"].eq("historical_archive").sum()),
        "queue_count": int(len(queue)),
        "backlog_count": int(len(backlog)),
        "queue_chronic_count": int(queue["run_shape_class"].eq("chronic_alert_run").sum()),
        "backlog_chronic_count": int(backlog["run_shape_class"].eq("chronic_alert_run").sum()),
        "queue_future_fault_linked_count": int(queue["future_fault_linked_flag"].eq(1).sum()),
        "queue_future_truth_linked_count": int(queue["future_truth_linked_flag"].eq(1).sum()),
    }


def build_summary(registry: pd.DataFrame, queue: pd.DataFrame, backlog: pd.DataFrame) -> pd.DataFrame:
    rows = [summarize_group("overall", "", registry, queue, backlog)]
    for site, site_group in registry.groupby("site", sort=True, dropna=False):
        site_queue = queue.loc[queue["site"].eq(site)].copy()
        site_backlog = backlog.loc[backlog["site"].eq(site)].copy()
        rows.append(summarize_group("site", site, site_group, site_queue, site_backlog))
    return pd.DataFrame(rows, columns=SUMMARY_OUTPUT_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    registry = build_registry(root)
    queue = build_queue(registry)
    backlog = build_backlog(registry)
    summary = build_summary(registry, queue, backlog)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    registry.loc[:, REGISTRY_OUTPUT_COLS].to_csv(
        share_dir / RUN_REGISTRY_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    queue.loc[:, REGISTRY_OUTPUT_COLS].to_csv(
        share_dir / RUN_QUEUE_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    backlog.loc[:, REGISTRY_OUTPUT_COLS].to_csv(
        share_dir / RUN_BACKLOG_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )
    summary.to_csv(
        share_dir / RUN_SUMMARY_OUTPUT_NAME,
        index=False,
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    main()
