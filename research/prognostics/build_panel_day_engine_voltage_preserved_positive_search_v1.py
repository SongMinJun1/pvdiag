#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


CANDIDATE_OUTPUT_NAME = "panel_day_engine_voltage_preserved_positive_search_candidates_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_voltage_preserved_positive_search_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_voltage_preserved_positive_search_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_voltage_preserved_positive_search_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_voltage_preserved_positive_search_v1.json"

DEFAULT_SHAPE_INPUT = (
    "/private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check/"
    "panel_day_engine_episode_truth_durable_shape_review_v1.csv"
)
DEFAULT_HOLD_INPUT = (
    "/private/tmp/panel_day_engine_durable_hold_raw_shape_review_br091_check/"
    "panel_day_engine_durable_hold_raw_shape_review_summary_v1.csv"
)
DEFAULT_DATA_ROOT = "/Users/b9gc/pvdiag/data"
DEFAULT_OUTPUT_DIR = "/private/tmp/panel_day_engine_voltage_preserved_positive_search_br092_check"

CORE_REQUIRED_COLUMNS = [
    "date",
    "panel_id",
    "source_csv",
    "event_A",
    "is_ae_abn",
    "is_ae_strong",
    "re_drop",
    "fault_like_day",
    "critical_fault",
    "confirmed_fault",
    "final_fault",
    "degraded_candidate",
    "data_bad",
    "subgroup_common_cause_candidate",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "dtw_dist",
    "co_drop_frac",
]

SHAPE_REQUIRED_COLUMNS = [
    "shape_review_row_id",
    "shape_review_decision",
    "reviewed_truth_row_id",
    "review_packet_id",
    "site",
    "panel_id",
    "strict_trigger_date",
    "positive_replay_candidate",
    "negative_replay_candidate",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

HOLD_REQUIRED_COLUMNS = [
    "raw_hold_review_id",
    "shape_review_row_id",
    "site",
    "panel_id",
    "strict_trigger_date",
    "raw_shape_decision",
    "positive_truth_candidate",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

CANDIDATE_COLUMNS = [
    "owner_branch",
    "search_candidate_row_id",
    "site",
    "panel_id",
    "hard_episode_anchor_date",
    "onset_candidate_date",
    "gap_days",
    "candidate_tier",
    "candidate_tier_rank",
    "known_review_role",
    "known_shape_review_row_id",
    "known_reviewed_truth_row_id",
    "known_review_packet_id",
    "known_shape_review_decision",
    "truth_search_action",
    "candidate_priority",
    "manual_review_ready",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "window_day_rows",
    "window_signal_days",
    "event_A_days",
    "ae_strong_days",
    "re_drop_days",
    "low_mid_days",
    "severe_low_mid_days",
    "voltage_low_current_ok_days",
    "current_low_voltage_ok_days",
    "both_low_vi_days",
    "hard_anchor_days",
    "common_cause_days",
    "data_bad_days",
    "data_bad_limit",
    "median_signal_mid_ratio",
    "median_signal_mid_v_ratio",
    "median_signal_mid_i_ratio",
    "min_window_mid_ratio",
    "median_signal_dtw_dist",
    "max_window_dtw_dist",
    "max_window_co_drop_frac",
    "anchor_source_csv",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "site",
    "candidate_tier",
    "known_review_role",
    "truth_search_action",
    "candidate_rows",
    "unique_panels",
    "unique_anchor_dates",
    "manual_review_ready_rows",
    "positive_truth_candidate_approved_sum",
    "threshold_tuning_approved_sum",
    "min_gap_days",
    "median_gap_days",
    "max_gap_days",
    "notes",
]

ACTION_COLUMNS = [
    "owner_branch",
    "sequence",
    "action_id",
    "action",
    "input_filter",
    "purpose",
    "success_boundary",
    "recommended_next_artifact",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

TIER_RANK = {
    "voltage_preserved_2d_review": 1,
    "voltage_preserved_10d": 2,
    "strong_b089_like": 3,
}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def numeric_float(value: object) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0.0 if pd.isna(numeric) else float(numeric)


def numeric_int(value: object) -> int:
    return int(numeric_float(value))


def rounded(value: object) -> float:
    return round(numeric_float(value), 6)


def safe_median(series: pd.Series) -> float:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    return rounded(clean.median()) if not clean.empty else 0.0


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def read_required_csv(path: Path, required_cols: list[str], name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing required input {name}: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")
    return df


def bool_series(df: pd.DataFrame, col: str) -> pd.Series:
    text = df[col].map(normalize_text).str.lower()
    truthy = text.isin(["1", "true", "t", "yes", "y"])
    numeric = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return truthy | (numeric > 0)


def core_path(data_root: Path, site: str) -> Path:
    return data_root / site / "out" / "panel_day_core.csv"


def data_bad_limit(row_count: int) -> int:
    return max(1, round(float(row_count) * 0.05))


def normalize_core(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["date"] = out["date"].map(normalize_text)
    out["date_dt"] = pd.to_datetime(out["date"], errors="coerce")
    out["panel_id"] = out["panel_id"].map(normalize_text)
    for col in [
        "event_A",
        "is_ae_abn",
        "is_ae_strong",
        "re_drop",
        "fault_like_day",
        "critical_fault",
        "confirmed_fault",
        "final_fault",
        "degraded_candidate",
        "data_bad",
        "subgroup_common_cause_candidate",
    ]:
        out[col] = bool_series(out, col).astype(int)
    for col in ["mid_ratio", "mid_v_ratio", "mid_i_ratio", "dtw_dist", "co_drop_frac"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out["low_mid_flag"] = out["mid_ratio"].lt(0.75).astype(int)
    out["severe_low_mid_flag"] = out["mid_ratio"].lt(0.5).astype(int)
    out["voltage_low_current_ok_flag"] = (
        out["mid_v_ratio"].lt(0.75) & out["mid_i_ratio"].ge(0.85)
    ).astype(int)
    out["current_low_voltage_ok_flag"] = (
        out["mid_i_ratio"].lt(0.75) & out["mid_v_ratio"].ge(0.85)
    ).astype(int)
    out["both_low_vi_flag"] = (out["mid_v_ratio"].lt(0.75) & out["mid_i_ratio"].lt(0.75)).astype(int)
    out["hard_anchor_flag"] = (
        out[["fault_like_day", "critical_fault", "confirmed_fault", "final_fault"]].sum(axis=1) > 0
    ).astype(int)
    out["signal_flag"] = (
        out[["event_A", "is_ae_abn", "is_ae_strong", "re_drop", "degraded_candidate"]].sum(axis=1) > 0
    ).astype(int)
    return out.dropna(subset=["date_dt"]).copy()


def normalize_shape_input(shape_df: pd.DataFrame) -> pd.DataFrame:
    df = shape_df.copy()
    for col in [
        "shape_review_row_id",
        "shape_review_decision",
        "reviewed_truth_row_id",
        "review_packet_id",
        "site",
        "panel_id",
        "strict_trigger_date",
    ]:
        df[col] = df[col].map(normalize_text)
    for col in [
        "positive_replay_candidate",
        "negative_replay_candidate",
        "operator_facing_change_allowed",
        "engine_patch_allowed",
        "threshold_patch_allowed",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def normalize_hold_input(hold_df: pd.DataFrame) -> pd.DataFrame:
    df = hold_df.copy()
    for col in ["raw_hold_review_id", "shape_review_row_id", "site", "panel_id", "strict_trigger_date"]:
        df[col] = df[col].map(normalize_text)
    for col in [
        "positive_truth_candidate",
        "operator_facing_change_allowed",
        "engine_patch_allowed",
        "threshold_patch_allowed",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def assert_safe_inputs(shape_df: pd.DataFrame, hold_df: pd.DataFrame) -> None:
    for name, df, cols in [
        (
            "BR-089 shape review",
            shape_df,
            ["operator_facing_change_allowed", "engine_patch_allowed", "threshold_patch_allowed"],
        ),
        (
            "BR-091 hold review",
            hold_df,
            [
                "positive_truth_candidate",
                "operator_facing_change_allowed",
                "engine_patch_allowed",
                "threshold_patch_allowed",
            ],
        ),
    ]:
        for col in cols:
            total = int(df[col].sum())
            if total != 0:
                raise ValueError(f"BR-092 requires non-authorizing {name}; {col} sum is {total}")


def known_case_map(shape_df: pd.DataFrame) -> dict[tuple[str, str, str], dict[str, str]]:
    known: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in shape_df.to_dict(orient="records"):
        decision = normalize_text(row["shape_review_decision"])
        if numeric_int(row["positive_replay_candidate"]) == 1:
            role = "known_positive_seed"
        elif decision == "defer_durable_shape_hold":
            role = "known_deferred_hold"
        elif numeric_int(row["negative_replay_candidate"]) == 1:
            role = "known_negative_counterexample"
        else:
            role = "known_other_reviewed_row"
        key = (
            normalize_text(row["site"]),
            normalize_text(row["panel_id"]),
            normalize_text(row["strict_trigger_date"]),
        )
        known[key] = {
            "known_review_role": role,
            "known_shape_review_row_id": normalize_text(row["shape_review_row_id"]),
            "known_reviewed_truth_row_id": normalize_text(row["reviewed_truth_row_id"]),
            "known_review_packet_id": normalize_text(row["review_packet_id"]),
            "known_shape_review_decision": decision,
        }
    return known


def window_metrics(window: pd.DataFrame) -> dict[str, Any]:
    signal = window.loc[window["signal_flag"].eq(1)].copy()
    return {
        "window_day_rows": int(len(window)),
        "window_signal_days": int(window["signal_flag"].sum()),
        "event_A_days": int(window["event_A"].sum()),
        "ae_strong_days": int(window["is_ae_strong"].sum()),
        "re_drop_days": int(window["re_drop"].sum()),
        "low_mid_days": int(window["low_mid_flag"].sum()),
        "severe_low_mid_days": int(window["severe_low_mid_flag"].sum()),
        "voltage_low_current_ok_days": int(window["voltage_low_current_ok_flag"].sum()),
        "current_low_voltage_ok_days": int(window["current_low_voltage_ok_flag"].sum()),
        "both_low_vi_days": int(window["both_low_vi_flag"].sum()),
        "hard_anchor_days": int(window["hard_anchor_flag"].sum()),
        "common_cause_days": int(window["subgroup_common_cause_candidate"].sum()),
        "data_bad_days": int(window["data_bad"].sum()),
        "data_bad_limit": data_bad_limit(len(window)),
        "median_signal_mid_ratio": safe_median(signal["mid_ratio"]),
        "median_signal_mid_v_ratio": safe_median(signal["mid_v_ratio"]),
        "median_signal_mid_i_ratio": safe_median(signal["mid_i_ratio"]),
        "min_window_mid_ratio": rounded(window["mid_ratio"].min(skipna=True)),
        "median_signal_dtw_dist": safe_median(signal["dtw_dist"]),
        "max_window_dtw_dist": rounded(window["dtw_dist"].max(skipna=True)),
        "max_window_co_drop_frac": rounded(window["co_drop_frac"].max(skipna=True)),
    }


def classify_tier(metrics: dict[str, Any], min_gap: int, max_gap: int, gap_days: int) -> str:
    if not (min_gap <= gap_days <= max_gap):
        return ""
    if int(metrics["hard_anchor_days"]) < 1 or int(metrics["common_cause_days"]) != 0:
        return ""
    if int(metrics["data_bad_days"]) > int(metrics["data_bad_limit"]):
        return ""
    if (
        int(metrics["window_day_rows"]) >= 14
        and int(metrics["event_A_days"]) >= 10
        and int(metrics["low_mid_days"]) >= 10
        and int(metrics["voltage_low_current_ok_days"]) >= 10
        and float(metrics["median_signal_mid_v_ratio"]) < 0.75
        and float(metrics["median_signal_mid_i_ratio"]) >= 0.85
    ):
        return "strong_b089_like"
    if int(metrics["voltage_low_current_ok_days"]) >= 10:
        return "voltage_preserved_10d"
    if int(metrics["voltage_low_current_ok_days"]) >= 2:
        return "voltage_preserved_2d_review"
    return ""


def action_for_role(role: str, tier: str) -> tuple[str, str, int, str]:
    if role == "known_positive_seed":
        return (
            "sanity_check_known_positive_seed",
            "sanity_known_positive",
            0,
            "Known BR-089 positive seed rediscovered; useful as a regression sanity check only.",
        )
    if role == "known_negative_counterexample":
        return (
            "block_known_negative_counterexample_overlap",
            "blocked_known_negative",
            0,
            "Search pattern also overlaps a reviewed negative counterexample; do not treat raw search hits as truth.",
        )
    if role == "known_deferred_hold":
        return (
            "exclude_known_deferred_hold",
            "blocked_known_hold",
            0,
            "Known BR-091 hold remains excluded from positive voltage-preserved truth.",
        )
    if tier == "strong_b089_like":
        return (
            "review_new_candidate_before_truth_use",
            "P0_independent_confirmation_review",
            1,
            "Strong BR-089-like new search hit; requires independent confirmation before truth use.",
        )
    if tier == "voltage_preserved_10d":
        return (
            "review_new_candidate_before_truth_use",
            "P1_shape_confirmation_review",
            1,
            "Repeated voltage-low/current-preserved new search hit; requires confirmation before truth use.",
        )
    return (
        "hold_low_support_search_hit",
        "P2_search_context_only",
        0,
        "Low-support search hit; keep as context unless stronger evidence is attached.",
    )


def build_candidates(
    owner_branch: str,
    data_root: Path,
    sites: list[str],
    known: dict[tuple[str, str, str], dict[str, str]],
    min_gap: int,
    max_gap: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for site in sites:
        core_df = read_required_csv(core_path(data_root, site), CORE_REQUIRED_COLUMNS, f"{site}/panel_day_core.csv")
        core = normalize_core(core_df).sort_values(["panel_id", "date_dt"]).reset_index(drop=True)
        for panel_id, group in core.groupby("panel_id", sort=False):
            panel = group.sort_values("date_dt").reset_index(drop=True)
            hard_starts = panel.loc[
                panel["hard_anchor_flag"].eq(1) & ~panel["hard_anchor_flag"].shift(fill_value=0).eq(1)
            ].copy()
            for _, anchor in hard_starts.iterrows():
                anchor_date = anchor["date_dt"]
                lookback = panel.loc[
                    panel["date_dt"].ge(anchor_date - pd.Timedelta(days=max_gap))
                    & panel["date_dt"].le(anchor_date - pd.Timedelta(days=min_gap))
                ].copy()
                qualifiers = lookback.loc[
                    lookback["voltage_low_current_ok_flag"].eq(1)
                    & lookback["signal_flag"].eq(1)
                    & lookback["data_bad"].eq(0)
                ].copy()
                best: tuple[int, int, str, dict[str, Any]] | None = None
                for _, onset in qualifiers.iterrows():
                    gap_days = int((anchor_date - onset["date_dt"]).days)
                    window = panel.loc[panel["date_dt"].ge(onset["date_dt"]) & panel["date_dt"].le(anchor_date)].copy()
                    metrics = window_metrics(window)
                    tier = classify_tier(metrics, min_gap=min_gap, max_gap=max_gap, gap_days=gap_days)
                    if not tier:
                        continue
                    score = (TIER_RANK[tier], gap_days, normalize_text(onset["date"]), metrics)
                    if best is None or score[:2] > best[:2]:
                        best = score
                if best is None:
                    continue

                tier_rank, gap_days, onset_date, metrics = best
                tier = next(key for key, value in TIER_RANK.items() if value == tier_rank)
                anchor_date_text = normalize_text(anchor["date"])
                known_info = known.get(
                    (site, normalize_text(panel_id), anchor_date_text),
                    {
                        "known_review_role": "new_search_candidate",
                        "known_shape_review_row_id": "",
                        "known_reviewed_truth_row_id": "",
                        "known_review_packet_id": "",
                        "known_shape_review_decision": "",
                    },
                )
                action, priority, manual_ready, note = action_for_role(known_info["known_review_role"], tier)
                rows.append(
                    {
                        "owner_branch": owner_branch,
                        "search_candidate_row_id": "",
                        "site": site,
                        "panel_id": normalize_text(panel_id),
                        "hard_episode_anchor_date": anchor_date_text,
                        "onset_candidate_date": onset_date,
                        "gap_days": gap_days,
                        "candidate_tier": tier,
                        "candidate_tier_rank": tier_rank,
                        "known_review_role": known_info["known_review_role"],
                        "known_shape_review_row_id": known_info["known_shape_review_row_id"],
                        "known_reviewed_truth_row_id": known_info["known_reviewed_truth_row_id"],
                        "known_review_packet_id": known_info["known_review_packet_id"],
                        "known_shape_review_decision": known_info["known_shape_review_decision"],
                        "truth_search_action": action,
                        "candidate_priority": priority,
                        "manual_review_ready": manual_ready,
                        "positive_truth_candidate_approved": 0,
                        "threshold_tuning_approved": 0,
                        "window_day_rows": metrics["window_day_rows"],
                        "window_signal_days": metrics["window_signal_days"],
                        "event_A_days": metrics["event_A_days"],
                        "ae_strong_days": metrics["ae_strong_days"],
                        "re_drop_days": metrics["re_drop_days"],
                        "low_mid_days": metrics["low_mid_days"],
                        "severe_low_mid_days": metrics["severe_low_mid_days"],
                        "voltage_low_current_ok_days": metrics["voltage_low_current_ok_days"],
                        "current_low_voltage_ok_days": metrics["current_low_voltage_ok_days"],
                        "both_low_vi_days": metrics["both_low_vi_days"],
                        "hard_anchor_days": metrics["hard_anchor_days"],
                        "common_cause_days": metrics["common_cause_days"],
                        "data_bad_days": metrics["data_bad_days"],
                        "data_bad_limit": metrics["data_bad_limit"],
                        "median_signal_mid_ratio": metrics["median_signal_mid_ratio"],
                        "median_signal_mid_v_ratio": metrics["median_signal_mid_v_ratio"],
                        "median_signal_mid_i_ratio": metrics["median_signal_mid_i_ratio"],
                        "min_window_mid_ratio": metrics["min_window_mid_ratio"],
                        "median_signal_dtw_dist": metrics["median_signal_dtw_dist"],
                        "max_window_dtw_dist": metrics["max_window_dtw_dist"],
                        "max_window_co_drop_frac": metrics["max_window_co_drop_frac"],
                        "anchor_source_csv": normalize_text(anchor["source_csv"]),
                        "operator_facing_change_allowed": 0,
                        "engine_patch_allowed": 0,
                        "threshold_patch_allowed": 0,
                        "notes": note,
                    }
                )

    out = pd.DataFrame(rows).reindex(columns=CANDIDATE_COLUMNS)
    if out.empty:
        return out
    out = out.sort_values(
        ["candidate_tier_rank", "gap_days", "site", "panel_id", "hard_episode_anchor_date"],
        ascending=[False, False, True, True, True],
    ).reset_index(drop=True)
    out["search_candidate_row_id"] = [f"BR092-VPPS-{idx:03d}" for idx in range(1, len(out) + 1)]
    return out


def build_summary(owner_branch: str, candidates_df: pd.DataFrame) -> pd.DataFrame:
    if candidates_df.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    rows: list[dict[str, object]] = []
    group_cols = ["site", "candidate_tier", "known_review_role", "truth_search_action"]
    for keys, group in candidates_df.groupby(group_cols, sort=False):
        site, tier, role, action = keys
        rows.append(
            {
                "owner_branch": owner_branch,
                "site": site,
                "candidate_tier": tier,
                "known_review_role": role,
                "truth_search_action": action,
                "candidate_rows": int(len(group)),
                "unique_panels": int(group["panel_id"].nunique()),
                "unique_anchor_dates": int(group["hard_episode_anchor_date"].nunique()),
                "manual_review_ready_rows": int(group["manual_review_ready"].sum()),
                "positive_truth_candidate_approved_sum": int(group["positive_truth_candidate_approved"].sum()),
                "threshold_tuning_approved_sum": int(group["threshold_tuning_approved"].sum()),
                "min_gap_days": numeric_int(group["gap_days"].min()),
                "median_gap_days": rounded(group["gap_days"].median()),
                "max_gap_days": numeric_int(group["gap_days"].max()),
                "notes": "BR-092 search summary only; candidate rows require review before truth or tuning use.",
            }
        )
    return pd.DataFrame(rows).reindex(columns=SUMMARY_COLUMNS)


def build_action_queue(owner_branch: str, candidates_df: pd.DataFrame) -> pd.DataFrame:
    new_ready = 0 if candidates_df.empty else int(candidates_df["manual_review_ready"].sum())
    known_negative = (
        0
        if candidates_df.empty
        else int(candidates_df["known_review_role"].eq("known_negative_counterexample").sum())
    )
    known_hold = 0 if candidates_df.empty else int(candidates_df["known_review_role"].eq("known_deferred_hold").sum())
    rows = [
        {
            "owner_branch": owner_branch,
            "sequence": 1,
            "action_id": "BR092-ACT-001",
            "action": "review new voltage-preserved search candidates before truth use",
            "input_filter": "known_review_role=new_search_candidate and manual_review_ready=1",
            "purpose": "grow positive truth support without mining the BR-091 holds or approving thresholds prematurely",
            "success_boundary": f"manual review may inspect {new_ready} rows, but truth/tuning approvals remain 0 in BR-092",
            "recommended_next_artifact": "voltage_preserved_candidate_confirmation_packet_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Attach independent source or physical confirmation before any row becomes positive truth.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 2,
            "action_id": "BR092-ACT-002",
            "action": "treat known negative overlap as a blocker against raw-search thresholding",
            "input_filter": "known_review_role=known_negative_counterexample",
            "purpose": "prove that voltage-preserved search hits are not equivalent to confirmed precursor truth",
            "success_boundary": f"known negative overlap rows={known_negative}; direct tuning remains blocked",
            "recommended_next_artifact": "threshold_replay_counterexample_update_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Any future rule must survive the known-negative overlap before replay approval.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 3,
            "action_id": "BR092-ACT-003",
            "action": "keep BR-091 holds out of the positive voltage-preserved lane",
            "input_filter": "known_review_role=known_deferred_hold",
            "purpose": "preserve the BR-091 conclusion that the six holds are not voltage-preserved positives",
            "success_boundary": f"known hold search hits={known_hold}; positive_truth_candidate_approved remains 0",
            "recommended_next_artifact": "current_limited_subtype_truth_backlog_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "If a hold appears in this search, it stays hold until separate evidence reopens it.",
        },
    ]
    return pd.DataFrame(rows).reindex(columns=ACTION_COLUMNS)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_empty_"
    lines = [
        "| " + " | ".join(str(col) for col in df.columns) + " |",
        "| " + " | ".join(["---"] * len(df.columns)) + " |",
    ]
    for row in df.to_dict(orient="records"):
        values = [normalize_text(row.get(col)) for col in df.columns]
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in values) + " |")
    return "\n".join(lines)


def write_note(
    path: Path,
    owner_branch: str,
    shape_input: Path,
    hold_input: Path,
    data_root: Path,
    sites: list[str],
    candidates_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    compact_cols = [
        "site",
        "candidate_tier",
        "known_review_role",
        "truth_search_action",
        "candidate_rows",
        "unique_panels",
        "manual_review_ready_rows",
        "max_gap_days",
    ]
    known_cols = [
        "search_candidate_row_id",
        "site",
        "panel_id",
        "hard_episode_anchor_date",
        "onset_candidate_date",
        "gap_days",
        "candidate_tier",
        "known_review_role",
        "truth_search_action",
    ]
    known_rows = (
        candidates_df.loc[candidates_df["known_review_role"].ne("new_search_candidate"), known_cols]
        if not candidates_df.empty
        else candidates_df
    )
    lines = [
        "# panel_day_engine_voltage_preserved_positive_search_v1",
        "",
        "## Purpose",
        "- Search tri-site panel-day core rows for voltage-low/current-preserved precursor-like windows outside the 6 BR-091 holds.",
        "- Keep one best candidate per panel hard episode to avoid repeated onset over-counting.",
        "- Mark overlaps with BR-089 known positive/negative/hold rows before any truth or threshold use.",
        "",
        "## Inputs",
        f"- BR-089 shape review: `{shape_input}`",
        f"- BR-091 hold review: `{hold_input}`",
        f"- data root: `{data_root}`",
        f"- sites: `{','.join(sites)}`",
        "",
        "## Real Result",
        f"- owner_branch: `{owner_branch}`",
        f"- candidate rows: `{len(candidates_df)}`",
        f"- new search candidates: `{int(candidates_df['known_review_role'].eq('new_search_candidate').sum()) if not candidates_df.empty else 0}`",
        f"- manual review ready rows: `{int(candidates_df['manual_review_ready'].sum()) if not candidates_df.empty else 0}`",
        f"- known positive sanity rows: `{int(candidates_df['known_review_role'].eq('known_positive_seed').sum()) if not candidates_df.empty else 0}`",
        f"- known negative overlap rows: `{int(candidates_df['known_review_role'].eq('known_negative_counterexample').sum()) if not candidates_df.empty else 0}`",
        f"- known hold overlap rows: `{int(candidates_df['known_review_role'].eq('known_deferred_hold').sum()) if not candidates_df.empty else 0}`",
        f"- positive truth candidate approved sum: `{int(candidates_df['positive_truth_candidate_approved'].sum()) if not candidates_df.empty else 0}`",
        f"- threshold tuning approved sum: `{int(candidates_df['threshold_tuning_approved'].sum()) if not candidates_df.empty else 0}`",
        f"- engine patch allowed sum: `{int(candidates_df['engine_patch_allowed'].sum()) if not candidates_df.empty else 0}`",
        "",
        "## Compact Summary",
        dataframe_to_markdown(summary_df.loc[:, compact_cols] if not summary_df.empty else summary_df),
        "",
        "## Known Reviewed Overlaps",
        dataframe_to_markdown(known_rows),
        "",
        "## Safety Boundary",
        "- BR-092 is a positive-truth search artifact only.",
        "- Search hits are not truth labels.",
        "- Known negative overlap proves that this search pattern cannot become a threshold by itself.",
        "- It does not approve threshold tuning, operator-facing changes, or direct `panel_day_engine.py` edits.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(
    path: Path,
    owner_branch: str,
    repo_root: Path,
    output_dir: Path,
    shape_input: Path,
    hold_input: Path,
    data_root: Path,
    sites: list[str],
    candidates_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    payload = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "shape_input": str(shape_input),
        "hold_input": str(hold_input),
        "data_root": str(data_root),
        "sites": sites,
        "candidate_rows": int(len(candidates_df)),
        "summary_rows": int(len(summary_df)),
        "new_search_candidate_rows": int(candidates_df["known_review_role"].eq("new_search_candidate").sum())
        if not candidates_df.empty
        else 0,
        "manual_review_ready_rows": int(candidates_df["manual_review_ready"].sum()) if not candidates_df.empty else 0,
        "known_positive_seed_rows": int(candidates_df["known_review_role"].eq("known_positive_seed").sum())
        if not candidates_df.empty
        else 0,
        "known_negative_overlap_rows": int(
            candidates_df["known_review_role"].eq("known_negative_counterexample").sum()
        )
        if not candidates_df.empty
        else 0,
        "known_hold_overlap_rows": int(candidates_df["known_review_role"].eq("known_deferred_hold").sum())
        if not candidates_df.empty
        else 0,
        "positive_truth_candidate_approved_sum": int(candidates_df["positive_truth_candidate_approved"].sum())
        if not candidates_df.empty
        else 0,
        "threshold_tuning_approved_sum": int(candidates_df["threshold_tuning_approved"].sum())
        if not candidates_df.empty
        else 0,
        "operator_facing_change_allowed_sum": int(candidates_df["operator_facing_change_allowed"].sum())
        if not candidates_df.empty
        else 0,
        "engine_patch_allowed_sum": int(candidates_df["engine_patch_allowed"].sum()) if not candidates_df.empty else 0,
        "threshold_patch_allowed_sum": int(candidates_df["threshold_patch_allowed"].sum())
        if not candidates_df.empty
        else 0,
        "candidate_tier_counts": candidates_df["candidate_tier"].value_counts().sort_index().to_dict()
        if not candidates_df.empty
        else {},
        "known_review_role_counts": candidates_df["known_review_role"].value_counts().sort_index().to_dict()
        if not candidates_df.empty
        else {},
        "recommended_next_branch": "voltage_preserved_candidate_confirmation_packet_v1",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "candidates": str(output_dir / CANDIDATE_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search for voltage-preserved precursor-like candidates.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--shape-input", default=DEFAULT_SHAPE_INPUT, help="BR-089 durable shape review CSV.")
    parser.add_argument("--hold-input", default=DEFAULT_HOLD_INPUT, help="BR-091 durable hold raw-shape summary CSV.")
    parser.add_argument("--data-root", default=DEFAULT_DATA_ROOT, help="Data root containing <site>/out/panel_day_core.csv.")
    parser.add_argument("--sites", default="conalog,gangui,ktc_ess", help="Comma-separated site list.")
    parser.add_argument("--min-gap-days", type=int, default=7)
    parser.add_argument("--max-gap-days", type=int, default=120)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory for BR-092 artifacts.")
    parser.add_argument("--owner-branch", default="BR-20260425-092")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    shape_input = resolve_path(repo_root, args.shape_input)
    hold_input = resolve_path(repo_root, args.hold_input)
    data_root = resolve_path(repo_root, args.data_root)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    sites = [site.strip() for site in str(args.sites).split(",") if site.strip()]

    shape_df = normalize_shape_input(read_required_csv(shape_input, SHAPE_REQUIRED_COLUMNS, "BR-089 shape review"))
    hold_df = normalize_hold_input(read_required_csv(hold_input, HOLD_REQUIRED_COLUMNS, "BR-091 hold review"))
    assert_safe_inputs(shape_df, hold_df)
    known = known_case_map(shape_df)

    candidates_df = build_candidates(
        args.owner_branch,
        data_root,
        sites,
        known,
        min_gap=int(args.min_gap_days),
        max_gap=int(args.max_gap_days),
    )
    summary_df = build_summary(args.owner_branch, candidates_df)
    action_df = build_action_queue(args.owner_branch, candidates_df)

    candidates_df.to_csv(output_dir / CANDIDATE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir / NOTE_OUTPUT_NAME, args.owner_branch, shape_input, hold_input, data_root, sites, candidates_df, summary_df)
    write_json(
        output_dir / JSON_OUTPUT_NAME,
        args.owner_branch,
        repo_root,
        output_dir,
        shape_input,
        hold_input,
        data_root,
        sites,
        candidates_df,
        summary_df,
    )

    print(
        json.dumps(
            {
                "owner_branch": args.owner_branch,
                "candidate_rows": int(len(candidates_df)),
                "summary_rows": int(len(summary_df)),
                "new_search_candidate_rows": int(candidates_df["known_review_role"].eq("new_search_candidate").sum())
                if not candidates_df.empty
                else 0,
                "manual_review_ready_rows": int(candidates_df["manual_review_ready"].sum())
                if not candidates_df.empty
                else 0,
                "known_positive_seed_rows": int(candidates_df["known_review_role"].eq("known_positive_seed").sum())
                if not candidates_df.empty
                else 0,
                "known_negative_overlap_rows": int(
                    candidates_df["known_review_role"].eq("known_negative_counterexample").sum()
                )
                if not candidates_df.empty
                else 0,
                "known_hold_overlap_rows": int(candidates_df["known_review_role"].eq("known_deferred_hold").sum())
                if not candidates_df.empty
                else 0,
                "positive_truth_candidate_approved_sum": int(candidates_df["positive_truth_candidate_approved"].sum())
                if not candidates_df.empty
                else 0,
                "threshold_tuning_approved_sum": int(candidates_df["threshold_tuning_approved"].sum())
                if not candidates_df.empty
                else 0,
                "candidate_tier_counts": candidates_df["candidate_tier"].value_counts().sort_index().to_dict()
                if not candidates_df.empty
                else {},
                "outputs": {
                    "candidates": str(output_dir / CANDIDATE_OUTPUT_NAME),
                    "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
                    "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
                    "note": str(output_dir / NOTE_OUTPUT_NAME),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
