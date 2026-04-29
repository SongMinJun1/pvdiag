#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


SUMMARY_OUTPUT_NAME = "panel_day_engine_durable_hold_raw_shape_review_summary_v1.csv"
DAY_OUTPUT_NAME = "panel_day_engine_durable_hold_raw_shape_review_days_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_durable_hold_raw_shape_review_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_durable_hold_raw_shape_review_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_durable_hold_raw_shape_review_v1.json"

DEFAULT_SHAPE_INPUT = (
    "/private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check/"
    "panel_day_engine_episode_truth_durable_shape_review_v1.csv"
)
DEFAULT_DATA_ROOT = str(Path(__file__).resolve().parents[2] / "data")

SHAPE_REQUIRED_COLUMNS = [
    "shape_review_row_id",
    "shape_review_decision",
    "reviewed_truth_row_id",
    "review_packet_id",
    "site",
    "panel_id",
    "episode_anchor_date",
    "strict_trigger_date",
    "gap_days",
    "window_signal_days",
    "event_A_days",
    "low_mid_days",
    "voltage_low_current_ok_days",
    "current_low_voltage_ok_days",
    "both_low_vi_days",
    "hard_anchor_days",
    "common_cause_days",
    "data_bad_days",
    "median_signal_mid_v_ratio",
    "median_signal_mid_i_ratio",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

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
    "final_fault",
    "degraded_candidate",
    "data_bad",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "dtw_dist",
    "co_drop_frac",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "raw_hold_review_id",
    "raw_shape_decision",
    "raw_shape_confidence",
    "positive_truth_candidate",
    "threshold_tuning_approved",
    "defer_reason",
    "shape_review_row_id",
    "reviewed_truth_row_id",
    "review_packet_id",
    "site",
    "panel_id",
    "episode_anchor_date",
    "strict_trigger_date",
    "gap_days",
    "selected_day_count",
    "raw_recomputed_day_count",
    "raw_missing_day_count",
    "raw_low_mid_days",
    "raw_voltage_low_current_ok_days",
    "raw_current_low_voltage_ok_days",
    "raw_both_low_vi_days",
    "raw_median_mid_ratio",
    "raw_median_mid_v_ratio",
    "raw_median_mid_i_ratio",
    "core_window_signal_days",
    "core_event_A_days",
    "core_low_mid_days",
    "core_voltage_low_current_ok_days",
    "core_current_low_voltage_ok_days",
    "core_both_low_vi_days",
    "core_median_signal_mid_v_ratio",
    "core_median_signal_mid_i_ratio",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

DAY_COLUMNS = [
    "owner_branch",
    "raw_hold_review_id",
    "shape_review_row_id",
    "review_packet_id",
    "site",
    "panel_id",
    "date",
    "selection_rank",
    "selection_reason",
    "source_csv",
    "raw_file_exists",
    "raw_target_rows",
    "raw_mid_rows",
    "raw_mid_ratio",
    "raw_mid_v_ratio",
    "raw_mid_i_ratio",
    "raw_min_ratio",
    "raw_low_mid_flag",
    "raw_voltage_low_current_ok_flag",
    "raw_current_low_voltage_ok_flag",
    "raw_both_low_vi_flag",
    "core_event_A",
    "core_is_ae_strong",
    "core_re_drop",
    "core_fault_like_day",
    "core_critical_fault",
    "core_final_fault",
    "core_mid_ratio",
    "core_mid_v_ratio",
    "core_mid_i_ratio",
    "core_dtw_dist",
    "core_co_drop_frac",
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


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def load_input_manifest(repo_root: Path, value: str | Path | None) -> tuple[Path | None, dict[str, Any]]:
    if value is None or str(value).strip() == "":
        return None, {}
    path = resolve_path(repo_root, value)
    if not path.exists():
        raise FileNotFoundError(f"missing input manifest: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"input manifest must be a JSON object: {path}")
    return path, payload


def manifest_path_value(manifest: dict[str, Any], key: str) -> str:
    raw = manifest.get(key)
    if raw is None and isinstance(manifest.get("inputs"), dict):
        raw = manifest["inputs"].get(key)
    if isinstance(raw, dict):
        for field in ["path", "artifact_path", "static_path"]:
            if raw.get(field):
                return str(raw[field])
        return ""
    return "" if raw is None else str(raw)


def cli_flag_provided(flag: str, argv: list[str]) -> bool:
    return any(item == flag or item.startswith(f"{flag}=") for item in argv)


def resolve_chain_input(
    repo_root: Path,
    cli_value: str | Path,
    legacy_default: str | Path,
    manifest: dict[str, Any],
    manifest_key: str,
    cli_flag: str,
    explicit_flags: set[str],
) -> tuple[Path, str]:
    if cli_flag in explicit_flags:
        return resolve_path(repo_root, cli_value), "explicit_cli"
    if manifest:
        manifest_value = manifest_path_value(manifest, manifest_key)
        if not manifest_value:
            raise KeyError(
                f"panel-day evidence input manifest is missing `{manifest_key}`; "
                f"pass {cli_flag} explicitly or add inputs.{manifest_key}"
            )
        return resolve_path(repo_root, manifest_value), "input_manifest"
    return resolve_path(repo_root, legacy_default), "legacy_default"


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


def panel_group_key(pid: str) -> str:
    parts = str(pid).split(".")
    if len(parts) >= 3:
        return parts[0] + "." + parts[1]
    if len(parts) == 2:
        return parts[0]
    return str(pid)


def find_col(df: pd.DataFrame, *candidates: str) -> str | None:
    normalized = {str(col).strip().lower(): str(col) for col in df.columns}
    for candidate in candidates:
        key = candidate.strip().lower()
        if key in normalized:
            return normalized[key]
    return None


def assert_safe_input(shape_df: pd.DataFrame) -> None:
    for col in ["operator_facing_change_allowed", "engine_patch_allowed", "threshold_patch_allowed"]:
        total = int(pd.to_numeric(shape_df[col], errors="coerce").fillna(0).sum())
        if total != 0:
            raise ValueError(f"BR-091 requires non-authorizing BR-089 input; {col} sum is {total}")


def core_path(data_root: Path, site: str) -> Path:
    return data_root / site / "out" / "panel_day_core.csv"


def raw_path(data_root: Path, site: str, source_csv: str, date: str) -> Path:
    candidate = data_root / site / "raw" / source_csv
    if candidate.exists():
        return candidate
    matches = sorted((data_root / site / "raw").glob(f"{date}*.csv"))
    return matches[0] if matches else candidate


def read_site_core(data_root: Path, site: str, cache: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if site not in cache:
        df = read_required_csv(core_path(data_root, site), CORE_REQUIRED_COLUMNS, f"{site}/panel_day_core.csv")
        df = df.copy()
        df["date"] = df["date"].map(normalize_text)
        df["panel_id"] = df["panel_id"].map(normalize_text)
        for col in [
            "event_A",
            "is_ae_abn",
            "is_ae_strong",
            "re_drop",
            "fault_like_day",
            "critical_fault",
            "final_fault",
            "degraded_candidate",
            "data_bad",
        ]:
            df[col] = bool_series(df, col).astype(int)
        for col in ["mid_ratio", "mid_v_ratio", "mid_i_ratio", "dtw_dist", "co_drop_frac"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        cache[site] = df
    return cache[site]


def read_raw_file(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    except UnicodeDecodeError:
        return pd.read_csv(path, low_memory=False)


def estimate_raw_day_metrics(raw_df: pd.DataFrame, panel_id: str) -> dict[str, object]:
    if raw_df.empty:
        return {
            "raw_file_exists": 0,
            "raw_target_rows": 0,
            "raw_mid_rows": 0,
            "raw_mid_ratio": 0.0,
            "raw_mid_v_ratio": 0.0,
            "raw_mid_i_ratio": 0.0,
            "raw_min_ratio": 0.0,
        }

    c_dt = find_col(raw_df, "date_time", "datetime", "timestamp", "time")
    c_id = find_col(raw_df, "map_id", "panel_id", "id")
    c_v = find_col(raw_df, "v_in (V)", "v_in (v)", "v_in", "vin", "input_voltage")
    c_i = find_col(raw_df, "i_out (A)", "i_out (a)", "i_out", "i", "current")
    if not all([c_dt, c_id, c_v, c_i]):
        return {
            "raw_file_exists": 1,
            "raw_target_rows": 0,
            "raw_mid_rows": 0,
            "raw_mid_ratio": 0.0,
            "raw_mid_v_ratio": 0.0,
            "raw_mid_i_ratio": 0.0,
            "raw_min_ratio": 0.0,
        }

    df = raw_df.loc[raw_df[c_id].map(normalize_text).str.startswith(panel_group_key(panel_id) + ".")].copy()
    if df.empty:
        df = raw_df.copy()
    df["_dt"] = pd.to_datetime(df[c_dt], errors="coerce")
    df = df.dropna(subset=["_dt"]).copy()
    if df.empty:
        return {
            "raw_file_exists": 1,
            "raw_target_rows": 0,
            "raw_mid_rows": 0,
            "raw_mid_ratio": 0.0,
            "raw_mid_v_ratio": 0.0,
            "raw_mid_i_ratio": 0.0,
            "raw_min_ratio": 0.0,
        }

    df[c_id] = df[c_id].map(normalize_text)
    df[c_v] = pd.to_numeric(df[c_v], errors="coerce").clip(lower=0)
    df[c_i] = pd.to_numeric(df[c_i], errors="coerce").clip(lower=0)
    v_tbl = df.pivot_table(index="_dt", columns=c_id, values=c_v, aggfunc="mean")
    i_tbl = df.pivot_table(index="_dt", columns=c_id, values=c_i, aggfunc="mean")
    if panel_id not in v_tbl.columns or panel_id not in i_tbl.columns:
        return {
            "raw_file_exists": 1,
            "raw_target_rows": 0,
            "raw_mid_rows": 0,
            "raw_mid_ratio": 0.0,
            "raw_mid_v_ratio": 0.0,
            "raw_mid_i_ratio": 0.0,
            "raw_min_ratio": 0.0,
        }

    p_tbl = (v_tbl * i_tbl).clip(lower=0)
    peer_p = p_tbl.median(axis=1)
    peer_v = v_tbl.median(axis=1)
    peer_i = i_tbl.median(axis=1)
    if peer_p.empty or not (peer_p.max(skipna=True) > 0):
        return {
            "raw_file_exists": 1,
            "raw_target_rows": int(v_tbl[panel_id].notna().sum()),
            "raw_mid_rows": 0,
            "raw_mid_ratio": 0.0,
            "raw_mid_v_ratio": 0.0,
            "raw_mid_i_ratio": 0.0,
            "raw_min_ratio": 0.0,
        }

    target_p = p_tbl[panel_id]
    target_v = v_tbl[panel_id]
    target_i = i_tbl[panel_id]
    peer_frac = peer_p / float(peer_p.max(skipna=True))
    mid_mask = (peer_frac >= 0.2) & (peer_frac.index.hour >= 11) & (peer_frac.index.hour < 15)
    if not mid_mask.any():
        mid_mask = peer_frac >= 0.2

    ratio = target_p / peer_p.where(peer_p > 1e-9)
    v_ratio = target_v / peer_v.where(peer_v > 1e-9)
    i_ratio = target_i / peer_i.where(peer_i > 1e-9)
    ratio_mid = ratio.loc[mid_mask].dropna()
    v_mid = v_ratio.loc[mid_mask].dropna()
    i_mid = i_ratio.loc[mid_mask].dropna()

    return {
        "raw_file_exists": 1,
        "raw_target_rows": int(target_p.notna().sum()),
        "raw_mid_rows": int(ratio_mid.count()),
        "raw_mid_ratio": rounded(ratio_mid.mean()) if not ratio_mid.empty else 0.0,
        "raw_mid_v_ratio": rounded(v_mid.mean()) if not v_mid.empty else 0.0,
        "raw_mid_i_ratio": rounded(i_mid.mean()) if not i_mid.empty else 0.0,
        "raw_min_ratio": rounded(ratio.dropna().min()) if ratio.dropna().size else 0.0,
    }


def select_review_days(core_window: pd.DataFrame, max_days: int) -> pd.DataFrame:
    if core_window.empty:
        return core_window.copy()
    df = core_window.copy()
    bool_cols = [
        "event_A",
        "is_ae_abn",
        "is_ae_strong",
        "re_drop",
        "fault_like_day",
        "critical_fault",
        "final_fault",
        "degraded_candidate",
    ]
    df["signal_score"] = df.loc[:, bool_cols].sum(axis=1)
    df["low_shape_score"] = (
        df["mid_ratio"].lt(0.75).astype(int)
        + df["mid_v_ratio"].lt(0.75).astype(int)
        + df["mid_i_ratio"].lt(0.75).astype(int)
    )
    df["rank_score"] = (
        df["signal_score"] * 1000
        + df["low_shape_score"] * 200
        + (1.0 - df["mid_ratio"].fillna(1.0)).clip(lower=-1, upper=1) * 100
        + df["dtw_dist"].fillna(0)
    )
    selected = df.sort_values(["rank_score", "dtw_dist", "date"], ascending=[False, False, True]).head(max_days)
    return selected.reset_index(drop=True)


def classify_summary(raw_counts: dict[str, int], row: pd.Series) -> tuple[str, str, str]:
    vlow = int(raw_counts["raw_voltage_low_current_ok_days"])
    ilow = int(raw_counts["raw_current_low_voltage_ok_days"])
    both = int(raw_counts["raw_both_low_vi_days"])
    low_mid = int(raw_counts["raw_low_mid_days"])
    missing = int(raw_counts["raw_missing_day_count"])
    selected = int(raw_counts["selected_day_count"])

    if selected == 0 or missing == selected:
        return (
            "stay_hold_missing_raw_review",
            "blocked",
            "raw evidence could not be recomputed for selected days",
        )
    if vlow >= 2 and int(row["common_cause_days"]) == 0:
        return (
            "raw_voltage_preserved_candidate_needs_independent_confirmation",
            "raw_support_candidate",
            "raw waveform proxy has repeated voltage-low/current-preserved days, but independent confirmation is still required",
        )
    if ilow >= 2:
        return (
            "stay_hold_current_limited_shape",
            "hold_current_axis",
            "raw proxy points to current-low/voltage-preserved behavior, not the BR-090 voltage-preserved candidate",
        )
    if both > 0:
        return (
            "stay_hold_mixed_low_vi_shape",
            "hold_mixed_axis",
            "raw proxy has mixed low voltage/current days without repeatable voltage-preserved shape",
        )
    if low_mid <= 0:
        return (
            "stay_hold_no_low_shape_on_selected_raw_days",
            "hold_ae_recovery_only",
            "selected raw days do not show a repeated low-ratio family shape",
        )
    return (
        "stay_hold_weak_or_sparse_shape",
        "hold_sparse_shape",
        "raw proxy remains sparse or weak and cannot support positive truth",
    )


def build_review(owner_branch: str, shape_df: pd.DataFrame, data_root: Path, max_days: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    core_cache: dict[str, pd.DataFrame] = {}
    summary_rows: list[dict[str, object]] = []
    day_rows: list[dict[str, object]] = []

    holds = shape_df.loc[shape_df["shape_review_decision"].map(normalize_text).eq("defer_durable_shape_hold")].copy()
    holds = holds.sort_values(["site", "review_packet_id"]).reset_index(drop=True)
    for idx, row in enumerate(holds.to_dict(orient="records"), start=1):
        site = normalize_text(row["site"])
        panel_id = normalize_text(row["panel_id"])
        start = normalize_text(row["episode_anchor_date"])
        end = normalize_text(row["strict_trigger_date"])
        review_id = f"BR091-DHR-{idx:03d}"
        core = read_site_core(data_root, site, core_cache)
        core_window = core.loc[
            core["panel_id"].eq(panel_id) & core["date"].ge(start) & core["date"].le(end)
        ].copy()
        selected = select_review_days(core_window, max_days=max_days)

        raw_low_mid_days = 0
        raw_vlow_iok_days = 0
        raw_ilow_vok_days = 0
        raw_both_low_days = 0
        raw_missing_days = 0
        raw_mid_ratios: list[float] = []
        raw_mid_v_ratios: list[float] = []
        raw_mid_i_ratios: list[float] = []

        for day_idx, day in enumerate(selected.to_dict(orient="records"), start=1):
            date = normalize_text(day["date"])
            source_csv = normalize_text(day["source_csv"])
            path = raw_path(data_root, site, source_csv, date)
            raw_metrics = estimate_raw_day_metrics(read_raw_file(path), panel_id)
            missing = int(raw_metrics["raw_file_exists"]) == 0 or int(raw_metrics["raw_mid_rows"]) <= 0
            if missing:
                raw_missing_days += 1
            raw_mid_ratio = float(raw_metrics["raw_mid_ratio"])
            raw_mid_v_ratio = float(raw_metrics["raw_mid_v_ratio"])
            raw_mid_i_ratio = float(raw_metrics["raw_mid_i_ratio"])
            if not missing:
                raw_mid_ratios.append(raw_mid_ratio)
                raw_mid_v_ratios.append(raw_mid_v_ratio)
                raw_mid_i_ratios.append(raw_mid_i_ratio)
            low_mid_flag = int((not missing) and raw_mid_ratio < 0.75)
            vlow_iok_flag = int((not missing) and raw_mid_v_ratio < 0.75 and raw_mid_i_ratio >= 0.85)
            ilow_vok_flag = int((not missing) and raw_mid_i_ratio < 0.75 and raw_mid_v_ratio >= 0.85)
            both_low_flag = int((not missing) and raw_mid_v_ratio < 0.75 and raw_mid_i_ratio < 0.75)
            raw_low_mid_days += low_mid_flag
            raw_vlow_iok_days += vlow_iok_flag
            raw_ilow_vok_days += ilow_vok_flag
            raw_both_low_days += both_low_flag

            reasons = []
            for col, label in [
                ("event_A", "event_A"),
                ("is_ae_strong", "ae_strong"),
                ("re_drop", "re_drop"),
                ("fault_like_day", "fault_like"),
                ("critical_fault", "critical"),
                ("final_fault", "final"),
            ]:
                if numeric_int(day.get(col)) == 1:
                    reasons.append(label)
            if float(day.get("mid_ratio", 1.0)) < 0.75:
                reasons.append("low_mid")
            if not reasons:
                reasons.append("ranked_shape_context")

            day_rows.append(
                {
                    "owner_branch": owner_branch,
                    "raw_hold_review_id": review_id,
                    "shape_review_row_id": normalize_text(row["shape_review_row_id"]),
                    "review_packet_id": normalize_text(row["review_packet_id"]),
                    "site": site,
                    "panel_id": panel_id,
                    "date": date,
                    "selection_rank": day_idx,
                    "selection_reason": ";".join(reasons),
                    "source_csv": source_csv,
                    "raw_file_exists": int(raw_metrics["raw_file_exists"]),
                    "raw_target_rows": int(raw_metrics["raw_target_rows"]),
                    "raw_mid_rows": int(raw_metrics["raw_mid_rows"]),
                    "raw_mid_ratio": raw_mid_ratio,
                    "raw_mid_v_ratio": raw_mid_v_ratio,
                    "raw_mid_i_ratio": raw_mid_i_ratio,
                    "raw_min_ratio": float(raw_metrics["raw_min_ratio"]),
                    "raw_low_mid_flag": low_mid_flag,
                    "raw_voltage_low_current_ok_flag": vlow_iok_flag,
                    "raw_current_low_voltage_ok_flag": ilow_vok_flag,
                    "raw_both_low_vi_flag": both_low_flag,
                    "core_event_A": numeric_int(day.get("event_A")),
                    "core_is_ae_strong": numeric_int(day.get("is_ae_strong")),
                    "core_re_drop": numeric_int(day.get("re_drop")),
                    "core_fault_like_day": numeric_int(day.get("fault_like_day")),
                    "core_critical_fault": numeric_int(day.get("critical_fault")),
                    "core_final_fault": numeric_int(day.get("final_fault")),
                    "core_mid_ratio": rounded(day.get("mid_ratio")),
                    "core_mid_v_ratio": rounded(day.get("mid_v_ratio")),
                    "core_mid_i_ratio": rounded(day.get("mid_i_ratio")),
                    "core_dtw_dist": rounded(day.get("dtw_dist")),
                    "core_co_drop_frac": rounded(day.get("co_drop_frac")),
                    "notes": "raw waveform proxy recomputed from selected raw daily CSV; evidence-only.",
                }
            )

        raw_counts = {
            "selected_day_count": int(len(selected)),
            "raw_missing_day_count": raw_missing_days,
            "raw_low_mid_days": raw_low_mid_days,
            "raw_voltage_low_current_ok_days": raw_vlow_iok_days,
            "raw_current_low_voltage_ok_days": raw_ilow_vok_days,
            "raw_both_low_vi_days": raw_both_low_days,
        }
        decision, confidence, reason = classify_summary(raw_counts, pd.Series(row))
        summary_rows.append(
            {
                "owner_branch": owner_branch,
                "raw_hold_review_id": review_id,
                "raw_shape_decision": decision,
                "raw_shape_confidence": confidence,
                "positive_truth_candidate": 0,
                "threshold_tuning_approved": 0,
                "defer_reason": reason,
                "shape_review_row_id": normalize_text(row["shape_review_row_id"]),
                "reviewed_truth_row_id": normalize_text(row["reviewed_truth_row_id"]),
                "review_packet_id": normalize_text(row["review_packet_id"]),
                "site": site,
                "panel_id": panel_id,
                "episode_anchor_date": start,
                "strict_trigger_date": end,
                "gap_days": numeric_int(row["gap_days"]),
                "selected_day_count": int(len(selected)),
                "raw_recomputed_day_count": int(len(selected) - raw_missing_days),
                "raw_missing_day_count": raw_missing_days,
                "raw_low_mid_days": raw_low_mid_days,
                "raw_voltage_low_current_ok_days": raw_vlow_iok_days,
                "raw_current_low_voltage_ok_days": raw_ilow_vok_days,
                "raw_both_low_vi_days": raw_both_low_days,
                "raw_median_mid_ratio": rounded(pd.Series(raw_mid_ratios).median()) if raw_mid_ratios else 0.0,
                "raw_median_mid_v_ratio": rounded(pd.Series(raw_mid_v_ratios).median()) if raw_mid_v_ratios else 0.0,
                "raw_median_mid_i_ratio": rounded(pd.Series(raw_mid_i_ratios).median()) if raw_mid_i_ratios else 0.0,
                "core_window_signal_days": numeric_int(row["window_signal_days"]),
                "core_event_A_days": numeric_int(row["event_A_days"]),
                "core_low_mid_days": numeric_int(row["low_mid_days"]),
                "core_voltage_low_current_ok_days": numeric_int(row["voltage_low_current_ok_days"]),
                "core_current_low_voltage_ok_days": numeric_int(row["current_low_voltage_ok_days"]),
                "core_both_low_vi_days": numeric_int(row["both_low_vi_days"]),
                "core_median_signal_mid_v_ratio": rounded(row["median_signal_mid_v_ratio"]),
                "core_median_signal_mid_i_ratio": rounded(row["median_signal_mid_i_ratio"]),
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "notes": "BR-091 reviews durable holds with raw waveform proxy only; no truth or runtime change.",
            }
        )

    return (
        pd.DataFrame(summary_rows).reindex(columns=SUMMARY_COLUMNS),
        pd.DataFrame(day_rows).reindex(columns=DAY_COLUMNS),
    )


def build_action_queue(owner_branch: str) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": owner_branch,
            "sequence": 1,
            "action_id": "BR091-ACT-001",
            "action": "keep current-limited and mixed-axis holds out of positive voltage-preserved truth",
            "input_filter": "raw_shape_decision starts with stay_hold",
            "purpose": "avoid converting current-axis or AE/recovery-only morphology into voltage-preserved precursor labels",
            "success_boundary": "positive_truth_candidate remains 0 for reviewed holds",
            "recommended_next_artifact": "expanded_positive_voltage_preserved_truth_search",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Find new positives elsewhere rather than forcing these holds.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 2,
            "action_id": "BR091-ACT-002",
            "action": "separate current-axis hypothesis from voltage-preserved candidate",
            "input_filter": "raw_shape_decision=stay_hold_current_limited_shape",
            "purpose": "track a possible current-limited subtype separately from the voltage-preserved threshold lane",
            "success_boundary": "current-axis examples remain evidence-only until subtype truth support exists",
            "recommended_next_artifact": "current_limited_subtype_truth_backlog_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "This is a taxonomy/evidence split, not a runtime rule.",
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
    data_root: Path,
    summary_df: pd.DataFrame,
    day_df: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> None:
    compact_cols = [
        "raw_hold_review_id",
        "shape_review_row_id",
        "site",
        "raw_shape_decision",
        "raw_low_mid_days",
        "raw_voltage_low_current_ok_days",
        "raw_current_low_voltage_ok_days",
        "raw_both_low_vi_days",
        "positive_truth_candidate",
    ]
    lines = [
        "# panel_day_engine_durable_hold_raw_shape_review_v1",
        "",
        "## Purpose",
        "- Recompute selected raw-day waveform proxy metrics for the 6 BR-089 durable holds.",
        "- Separate voltage-preserved, current-limited, mixed-axis, and AE/recovery-only hold shapes.",
        "- Keep truth labels, threshold tuning, and direct engine patches blocked.",
        "",
        "## Inputs",
        f"- BR-089 shape review: `{shape_input}`",
        f"- data root: `{data_root}`",
        f"- evidence input manifest: `{input_manifest_path if input_manifest_path else 'not provided'}`",
        "",
        "## Input Resolution Sources",
        *(
            [f"- `{key}`: `{value}`" for key, value in sorted((input_resolution_sources or {}).items())]
            if input_resolution_sources
            else ["- no manifest-wrapped inputs"]
        ),
        "",
        "## Real Result",
        f"- owner_branch: `{owner_branch}`",
        f"- hold summary rows: `{len(summary_df)}`",
        f"- selected raw day rows: `{len(day_df)}`",
        f"- positive truth candidates: `{int(summary_df['positive_truth_candidate'].sum()) if not summary_df.empty else 0}`",
        f"- threshold tuning approved: `{int(summary_df['threshold_tuning_approved'].sum()) if not summary_df.empty else 0}`",
        f"- operator-facing change allowed sum: `{int(summary_df['operator_facing_change_allowed'].sum()) if not summary_df.empty else 0}`",
        f"- engine patch allowed sum: `{int(summary_df['engine_patch_allowed'].sum()) if not summary_df.empty else 0}`",
        f"- threshold patch allowed sum: `{int(summary_df['threshold_patch_allowed'].sum()) if not summary_df.empty else 0}`",
        "",
        "## Compact Summary",
        dataframe_to_markdown(summary_df.loc[:, compact_cols] if not summary_df.empty else summary_df),
        "",
        "## Safety Boundary",
        "- BR-091 is a raw-shape evidence review only.",
        "- It does not add positive truth labels.",
        "- It does not approve threshold tuning or direct `panel_day_engine.py` edits.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(
    path: Path,
    owner_branch: str,
    repo_root: Path,
    output_dir: Path,
    shape_input: Path,
    data_root: Path,
    summary_df: pd.DataFrame,
    day_df: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> None:
    payload = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "shape_input": str(shape_input),
        "input_manifest": str(input_manifest_path) if input_manifest_path else "",
        "input_resolution_sources": input_resolution_sources or {},
        "data_root": str(data_root),
        "summary_rows": int(len(summary_df)),
        "day_rows": int(len(day_df)),
        "positive_truth_candidate_sum": int(summary_df["positive_truth_candidate"].sum()) if not summary_df.empty else 0,
        "threshold_tuning_approved_sum": int(summary_df["threshold_tuning_approved"].sum()) if not summary_df.empty else 0,
        "operator_facing_change_allowed_sum": int(summary_df["operator_facing_change_allowed"].sum()) if not summary_df.empty else 0,
        "engine_patch_allowed_sum": int(summary_df["engine_patch_allowed"].sum()) if not summary_df.empty else 0,
        "threshold_patch_allowed_sum": int(summary_df["threshold_patch_allowed"].sum()) if not summary_df.empty else 0,
        "raw_shape_decision_counts": summary_df["raw_shape_decision"].value_counts().sort_index().to_dict()
        if not summary_df.empty
        else {},
        "recommended_next_branch": "expanded_positive_voltage_preserved_truth_search",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "days": str(output_dir / DAY_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review BR-089 durable holds with raw waveform proxy metrics.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--input-manifest", default=None)
    parser.add_argument("--shape-input", default=DEFAULT_SHAPE_INPUT, help="BR-089 durable shape review CSV.")
    parser.add_argument("--data-root", default=DEFAULT_DATA_ROOT, help="Data root containing <site>/raw and <site>/out.")
    parser.add_argument(
        "--output-dir",
        default="/private/tmp/panel_day_engine_durable_hold_raw_shape_review_br091_check",
        help="Output directory for BR-091 artifacts.",
    )
    parser.add_argument("--owner-branch", default="BR-20260425-091")
    parser.add_argument("--max-days-per-hold", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    input_manifest_path, input_manifest = load_input_manifest(repo_root, args.input_manifest)
    argv = sys.argv[1:]
    explicit_flags = {
        flag
        for flag in [
            "--shape-input",
        ]
        if cli_flag_provided(flag, argv)
    }
    shape_input, shape_input_source = resolve_chain_input(
        repo_root,
        args.shape_input,
        DEFAULT_SHAPE_INPUT,
        input_manifest,
        "shape_input",
        "--shape-input",
        explicit_flags,
    )
    input_resolution_sources = {
        "shape_input": shape_input_source,
    }
    data_root = resolve_path(repo_root, args.data_root)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    shape_df = read_required_csv(shape_input, SHAPE_REQUIRED_COLUMNS, "BR-089 shape review")
    assert_safe_input(shape_df)
    summary_df, day_df = build_review(args.owner_branch, shape_df, data_root, max_days=int(args.max_days_per_hold))
    action_df = build_action_queue(args.owner_branch)

    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    day_df.to_csv(output_dir / DAY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(
        output_dir / NOTE_OUTPUT_NAME,
        args.owner_branch,
        shape_input,
        data_root,
        summary_df,
        day_df,
        input_manifest_path,
        input_resolution_sources,
    )
    write_json(
        output_dir / JSON_OUTPUT_NAME,
        args.owner_branch,
        repo_root,
        output_dir,
        shape_input,
        data_root,
        summary_df,
        day_df,
        input_manifest_path,
        input_resolution_sources,
    )

    print(
        json.dumps(
            {
                "owner_branch": args.owner_branch,
                "summary_rows": int(len(summary_df)),
                "day_rows": int(len(day_df)),
                "positive_truth_candidate_sum": int(summary_df["positive_truth_candidate"].sum())
                if not summary_df.empty
                else 0,
                "threshold_tuning_approved_sum": int(summary_df["threshold_tuning_approved"].sum())
                if not summary_df.empty
                else 0,
                "raw_shape_decision_counts": summary_df["raw_shape_decision"].value_counts().sort_index().to_dict()
                if not summary_df.empty
                else {},
                "outputs": {
                    "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
                    "days": str(output_dir / DAY_OUTPUT_NAME),
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
