#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


REQUEST_INPUT_NAME = "panel_day_engine_voltage_preserved_evidence_request_packet_v1.csv"
CHECKLIST_INPUT_NAME = "panel_day_engine_voltage_preserved_evidence_request_checklist_v1.csv"
SOURCE_MAP_INPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_candidate_map_v1.csv"

ATTACHMENT_OUTPUT_NAME = "panel_day_engine_voltage_preserved_raw_source_attachment_index_v1.csv"
SOURCE_TRACE_OUTPUT_NAME = "panel_day_engine_voltage_preserved_raw_source_candidate_trace_v1.csv"
DAILY_TRACE_OUTPUT_NAME = "panel_day_engine_voltage_preserved_raw_source_daily_trace_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_voltage_preserved_raw_source_attachment_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_voltage_preserved_raw_source_attachment_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_voltage_preserved_raw_source_attachment_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_voltage_preserved_raw_source_attachment_v1.json"

DEFAULT_REQUEST_DIR = "/private/tmp/panel_day_engine_voltage_preserved_evidence_request_packet_br095_check"
DEFAULT_SOURCE_MAP = (
    "/private/tmp/panel_day_engine_voltage_preserved_confirmation_packet_br093_check/"
    "panel_day_engine_voltage_preserved_confirmation_candidate_map_v1.csv"
)
DEFAULT_DATA_ROOT = str(Path(__file__).resolve().parents[2] / "data")
DEFAULT_OUTPUT_DIR = "/private/tmp/panel_day_engine_voltage_preserved_raw_source_attachment_br096_check"

REQUEST_REQUIRED_COLUMNS = [
    "evidence_request_id",
    "source_confirmation_packet_row_id",
    "source_confirmation_family_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "request_priority",
    "evidence_request_status",
    "representative_candidate_row_id",
    "representative_anchor_date",
    "representative_onset_date",
    "representative_gap_days",
    "candidate_rows_for_panel",
    "unique_anchor_dates_for_panel",
    "min_gap_days_for_panel",
    "median_gap_days_for_panel",
    "max_gap_days_for_panel",
    "counterexample_risk_flag",
    "raw_waveform_request_required",
    "raw_waveform_is_independent_confirmation",
    "physical_measurement_or_iv_required",
    "maintenance_or_inspection_required",
    "common_cause_clearance_required",
    "measurement_artifact_clearance_required",
    "counterexample_clearance_required",
    "evidence_ready_for_truth_use",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

SOURCE_MAP_REQUIRED_COLUMNS = [
    "confirmation_packet_row_id",
    "search_candidate_row_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "hard_episode_anchor_date",
    "onset_candidate_date",
    "gap_days",
    "candidate_tier",
    "candidate_priority",
    "known_review_role",
    "manual_review_ready",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

CORE_REQUIRED_COLUMNS = [
    "date",
    "panel_id",
    "source_csv",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "event_A",
    "degraded_candidate",
    "fault_like_day",
    "data_bad",
    "co_drop_frac",
    "dtw_dist",
    "hs_score",
    "critical_fault",
    "final_fault",
    "group_off_like",
    "subgroup_common_cause_candidate",
]

ATTACHMENT_COLUMNS = [
    "owner_branch",
    "attachment_row_id",
    "evidence_request_id",
    "source_confirmation_packet_row_id",
    "source_confirmation_family_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "request_priority",
    "attachment_status",
    "raw_waveform_attachment_status",
    "source_candidate_trace_status",
    "core_window_trace_status",
    "raw_file_reference_status",
    "source_candidate_rows_attached",
    "unique_source_candidate_anchor_dates",
    "source_candidate_min_gap_days",
    "source_candidate_median_gap_days",
    "source_candidate_max_gap_days",
    "core_window_start_date",
    "core_window_end_date",
    "core_window_days_expected",
    "core_window_rows_attached",
    "core_signal_days_attached",
    "core_voltage_preserved_days_attached",
    "core_common_cause_flag_days",
    "core_measurement_artifact_hold_days",
    "raw_file_refs_total",
    "raw_file_refs_found",
    "raw_file_refs_missing",
    "raw_file_ref_examples",
    "source_candidate_id_list",
    "raw_waveform_is_independent_confirmation",
    "physical_or_maintenance_evidence_attached",
    "common_cause_clearance_attached",
    "measurement_artifact_clearance_attached",
    "counterexample_clearance_attached",
    "evidence_ready_for_truth_use",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "next_review_action",
    "notes",
]

SOURCE_TRACE_COLUMNS = [
    "owner_branch",
    "source_trace_row_id",
    "evidence_request_id",
    "source_confirmation_packet_row_id",
    "search_candidate_row_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "hard_episode_anchor_date",
    "onset_candidate_date",
    "gap_days",
    "candidate_tier",
    "candidate_priority",
    "known_review_role",
    "anchor_core_row_found",
    "onset_core_row_found",
    "anchor_source_csv",
    "onset_source_csv",
    "anchor_raw_csv_exists",
    "onset_raw_csv_exists",
    "trace_status",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

DAILY_TRACE_COLUMNS = [
    "owner_branch",
    "daily_trace_row_id",
    "evidence_request_id",
    "source_confirmation_packet_row_id",
    "site",
    "root_id",
    "panel_id",
    "date",
    "source_csv",
    "raw_csv_path",
    "raw_csv_exists",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "event_A",
    "degraded_candidate",
    "fault_like_day",
    "data_bad",
    "co_drop_frac",
    "dtw_dist",
    "hs_score",
    "critical_fault",
    "final_fault",
    "group_off_like",
    "subgroup_common_cause_candidate",
    "voltage_preserved_core_signal",
    "common_cause_context_flag",
    "measurement_artifact_hold_flag",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "summary_scope",
    "summary_key",
    "request_rows",
    "attachment_rows",
    "source_candidate_trace_rows",
    "daily_trace_rows",
    "raw_attached_request_rows",
    "raw_file_refs_total",
    "raw_file_refs_found",
    "raw_file_refs_missing",
    "core_signal_days_attached",
    "core_voltage_preserved_days_attached",
    "counterexample_risk_rows",
    "physical_or_maintenance_evidence_attached_sum",
    "common_cause_clearance_attached_sum",
    "measurement_artifact_clearance_attached_sum",
    "counterexample_clearance_attached_sum",
    "evidence_ready_for_truth_use_sum",
    "positive_truth_candidate_approved_sum",
    "threshold_tuning_approved_sum",
    "operator_facing_change_allowed_sum",
    "engine_patch_allowed_sum",
    "threshold_patch_allowed_sum",
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
    return int(round(numeric_float(value)))


def rounded(value: object) -> float:
    return round(numeric_float(value), 6)


def to_bool(value: object) -> bool:
    text = normalize_text(value).lower()
    if text in {"true", "t", "yes", "y", "1"}:
        return True
    if text in {"false", "f", "no", "n", "0", ""}:
        return False
    return numeric_float(value) > 0


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


def resolve_request_input(
    repo_root: Path,
    request_input_value: str | Path,
    request_dir_value: str | Path,
    manifest: dict[str, Any],
    explicit_flags: set[str],
) -> tuple[Path, str]:
    if "--request-input" in explicit_flags:
        return resolve_path(repo_root, request_input_value), "explicit_cli"
    if "--request-dir" in explicit_flags:
        return resolve_path(repo_root, request_dir_value) / REQUEST_INPUT_NAME, "explicit_cli"
    if manifest:
        manifest_value = manifest_path_value(manifest, "request_input")
        if not manifest_value:
            raise KeyError(
                "panel-day evidence input manifest is missing `request_input`; "
                "pass --request-input/--request-dir explicitly or add inputs.request_input"
            )
        return resolve_path(repo_root, manifest_value), "input_manifest"
    return resolve_path(repo_root, request_dir_value) / REQUEST_INPUT_NAME, "legacy_default"


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


def normalize_request(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in REQUEST_REQUIRED_COLUMNS:
        if col in {
            "representative_gap_days",
            "candidate_rows_for_panel",
            "unique_anchor_dates_for_panel",
            "min_gap_days_for_panel",
            "median_gap_days_for_panel",
            "max_gap_days_for_panel",
            "counterexample_risk_flag",
            "raw_waveform_request_required",
            "raw_waveform_is_independent_confirmation",
            "physical_measurement_or_iv_required",
            "maintenance_or_inspection_required",
            "common_cause_clearance_required",
            "measurement_artifact_clearance_required",
            "counterexample_clearance_required",
            "evidence_ready_for_truth_use",
            "positive_truth_candidate_approved",
            "threshold_tuning_approved",
            "operator_facing_change_allowed",
            "engine_patch_allowed",
            "threshold_patch_allowed",
        }:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
        else:
            out[col] = out[col].map(normalize_text)
    return out.sort_values(["site", "root_id", "panel_group_key", "panel_id"]).reset_index(drop=True)


def normalize_source_map(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in SOURCE_MAP_REQUIRED_COLUMNS:
        if col in {
            "gap_days",
            "manual_review_ready",
            "positive_truth_candidate_approved",
            "threshold_tuning_approved",
            "operator_facing_change_allowed",
            "engine_patch_allowed",
            "threshold_patch_allowed",
        }:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
        else:
            out[col] = out[col].map(normalize_text)
    return out.sort_values(["site", "root_id", "panel_group_key", "panel_id"]).reset_index(drop=True)


def assert_safe_input(request_df: pd.DataFrame, source_map_df: pd.DataFrame) -> None:
    for name, df in [("BR-095 requests", request_df), ("BR-093 source map", source_map_df)]:
        for col in [
            "positive_truth_candidate_approved",
            "threshold_tuning_approved",
            "operator_facing_change_allowed",
            "engine_patch_allowed",
            "threshold_patch_allowed",
        ]:
            total = int(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())
            if total != 0:
                raise ValueError(f"BR-096 requires non-authorizing input; {name} {col} sum is {total}")


def raw_csv_path(data_root: Path, site: str, source_csv: str) -> Path:
    return data_root / site / "raw" / source_csv


def load_site_core(data_root: Path, site: str) -> pd.DataFrame:
    path = data_root / site / "out" / "panel_day_core.csv"
    df = read_required_csv(path, CORE_REQUIRED_COLUMNS, f"{site} panel_day_core")
    out = df[CORE_REQUIRED_COLUMNS].copy()
    out["date"] = out["date"].map(normalize_text)
    out["panel_id"] = out["panel_id"].map(normalize_text)
    out["source_csv"] = out["source_csv"].map(normalize_text)
    for col in [
        "mid_ratio",
        "mid_v_ratio",
        "mid_i_ratio",
        "co_drop_frac",
        "dtw_dist",
        "hs_score",
    ]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    for col in [
        "event_A",
        "degraded_candidate",
        "fault_like_day",
        "data_bad",
        "critical_fault",
        "final_fault",
        "group_off_like",
        "subgroup_common_cause_candidate",
    ]:
        out[col] = out[col].map(to_bool).astype(int)
    return out


def core_lookup(site_core: pd.DataFrame) -> dict[tuple[str, str], dict[str, object]]:
    return {
        (normalize_text(row["panel_id"]), normalize_text(row["date"])): row
        for row in site_core.to_dict(orient="records")
    }


def source_csv_for(lookup: dict[tuple[str, str], dict[str, object]], panel_id: str, date: str) -> str:
    return normalize_text(lookup.get((panel_id, date), {}).get("source_csv", ""))


def source_exists(data_root: Path, site: str, source_csv: str) -> int:
    return int(bool(source_csv) and raw_csv_path(data_root, site, source_csv).exists())


def daily_window(site_core: pd.DataFrame, panel_id: str, start: str, end: str) -> pd.DataFrame:
    core = site_core.loc[site_core["panel_id"].eq(panel_id)].copy()
    if core.empty:
        return core
    core = core.loc[core["date"].ge(start) & core["date"].le(end)].copy()
    return core.sort_values("date").reset_index(drop=True)


def candidate_window(source_group: pd.DataFrame, request_row: dict[str, object]) -> tuple[str, str, int]:
    if source_group.empty:
        start = normalize_text(request_row["representative_onset_date"])
        end = normalize_text(request_row["representative_anchor_date"])
    else:
        start = normalize_text(source_group["onset_candidate_date"].min())
        end = normalize_text(source_group["hard_episode_anchor_date"].max())
    start_dt = pd.to_datetime(start, errors="coerce")
    end_dt = pd.to_datetime(end, errors="coerce")
    if pd.isna(start_dt) or pd.isna(end_dt):
        return start, end, 0
    return start, end, int((end_dt - start_dt).days) + 1


def voltage_preserved_signal(row: dict[str, object]) -> int:
    return int(
        numeric_float(row.get("mid_v_ratio")) <= 0.75
        and numeric_float(row.get("mid_i_ratio")) >= 0.85
        and not bool(numeric_int(row.get("data_bad")))
    )


def common_cause_context(row: dict[str, object]) -> int:
    return int(bool(numeric_int(row.get("group_off_like"))) or bool(numeric_int(row.get("subgroup_common_cause_candidate"))))


def measurement_artifact_hold(row: dict[str, object]) -> int:
    return int(bool(numeric_int(row.get("data_bad"))))


def build_source_trace(
    owner_branch: str,
    data_root: Path,
    request_df: pd.DataFrame,
    source_map_df: pd.DataFrame,
    site_lookups: dict[str, dict[tuple[str, str], dict[str, object]]],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    request_lookup = {
        normalize_text(row["source_confirmation_packet_row_id"]): row for row in request_df.to_dict(orient="records")
    }
    for idx, source in enumerate(source_map_df.to_dict(orient="records"), start=1):
        packet_id = normalize_text(source["confirmation_packet_row_id"])
        request = request_lookup.get(packet_id, {})
        request_id = normalize_text(request.get("evidence_request_id", ""))
        site = normalize_text(source["site"])
        panel_id = normalize_text(source["panel_id"])
        lookup = site_lookups.get(site, {})
        anchor_date = normalize_text(source["hard_episode_anchor_date"])
        onset_date = normalize_text(source["onset_candidate_date"])
        anchor_csv = source_csv_for(lookup, panel_id, anchor_date)
        onset_csv = source_csv_for(lookup, panel_id, onset_date)
        anchor_found = int((panel_id, anchor_date) in lookup)
        onset_found = int((panel_id, onset_date) in lookup)
        anchor_exists = source_exists(data_root, site, anchor_csv)
        onset_exists = source_exists(data_root, site, onset_csv)
        trace_status = (
            "source_candidate_anchor_and_onset_attached"
            if anchor_found and onset_found and anchor_exists and onset_exists
            else "source_candidate_partial_attachment"
        )
        rows.append(
            {
                "owner_branch": owner_branch,
                "source_trace_row_id": f"BR096-VPST-{idx:03d}",
                "evidence_request_id": request_id,
                "source_confirmation_packet_row_id": packet_id,
                "search_candidate_row_id": normalize_text(source["search_candidate_row_id"]),
                "site": site,
                "root_id": normalize_text(source["root_id"]),
                "panel_group_key": normalize_text(source["panel_group_key"]),
                "panel_id": panel_id,
                "hard_episode_anchor_date": anchor_date,
                "onset_candidate_date": onset_date,
                "gap_days": numeric_int(source["gap_days"]),
                "candidate_tier": normalize_text(source["candidate_tier"]),
                "candidate_priority": normalize_text(source["candidate_priority"]),
                "known_review_role": normalize_text(source["known_review_role"]),
                "anchor_core_row_found": anchor_found,
                "onset_core_row_found": onset_found,
                "anchor_source_csv": anchor_csv,
                "onset_source_csv": onset_csv,
                "anchor_raw_csv_exists": anchor_exists,
                "onset_raw_csv_exists": onset_exists,
                "trace_status": trace_status,
                "positive_truth_candidate_approved": 0,
                "threshold_tuning_approved": 0,
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "notes": "Source-candidate trace only; raw file presence is not independent physical confirmation.",
            }
        )
    return pd.DataFrame(rows).reindex(columns=SOURCE_TRACE_COLUMNS)


def build_daily_trace(
    owner_branch: str,
    data_root: Path,
    request_df: pd.DataFrame,
    source_map_df: pd.DataFrame,
    site_cores: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    daily_idx = 0
    for request in request_df.to_dict(orient="records"):
        request_id = normalize_text(request["evidence_request_id"])
        packet_id = normalize_text(request["source_confirmation_packet_row_id"])
        site = normalize_text(request["site"])
        panel_id = normalize_text(request["panel_id"])
        source_group = source_map_df.loc[source_map_df["confirmation_packet_row_id"].eq(packet_id)].copy()
        start, end, _expected = candidate_window(source_group, request)
        window = daily_window(site_cores[site], panel_id, start, end)
        for row in window.to_dict(orient="records"):
            daily_idx += 1
            source_csv = normalize_text(row["source_csv"])
            raw_path = raw_csv_path(data_root, site, source_csv)
            row_dict = {
                "owner_branch": owner_branch,
                "daily_trace_row_id": f"BR096-VPDT-{daily_idx:04d}",
                "evidence_request_id": request_id,
                "source_confirmation_packet_row_id": packet_id,
                "site": site,
                "root_id": normalize_text(request["root_id"]),
                "panel_id": panel_id,
                "date": normalize_text(row["date"]),
                "source_csv": source_csv,
                "raw_csv_path": str(raw_path),
                "raw_csv_exists": int(raw_path.exists()),
                "mid_ratio": rounded(row["mid_ratio"]),
                "mid_v_ratio": rounded(row["mid_v_ratio"]),
                "mid_i_ratio": rounded(row["mid_i_ratio"]),
                "event_A": numeric_int(row["event_A"]),
                "degraded_candidate": numeric_int(row["degraded_candidate"]),
                "fault_like_day": numeric_int(row["fault_like_day"]),
                "data_bad": numeric_int(row["data_bad"]),
                "co_drop_frac": rounded(row["co_drop_frac"]),
                "dtw_dist": rounded(row["dtw_dist"]),
                "hs_score": rounded(row["hs_score"]),
                "critical_fault": numeric_int(row["critical_fault"]),
                "final_fault": numeric_int(row["final_fault"]),
                "group_off_like": numeric_int(row["group_off_like"]),
                "subgroup_common_cause_candidate": numeric_int(row["subgroup_common_cause_candidate"]),
                "voltage_preserved_core_signal": voltage_preserved_signal(row),
                "common_cause_context_flag": common_cause_context(row),
                "measurement_artifact_hold_flag": measurement_artifact_hold(row),
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
            }
            rows.append(row_dict)
    return pd.DataFrame(rows).reindex(columns=DAILY_TRACE_COLUMNS)


def semicolon(values: list[object], limit: int = 12) -> str:
    normalized = [normalize_text(value) for value in values if normalize_text(value)]
    deduped = list(dict.fromkeys(normalized))
    shown = deduped[:limit]
    suffix = "" if len(deduped) <= limit else f";...(+{len(deduped) - limit})"
    return ";".join(shown) + suffix


def attachment_status(source_rows: int, daily_rows: int, raw_refs_total: int, raw_refs_missing: int) -> str:
    if source_rows <= 0 and daily_rows <= 0:
        return "missing_source_and_core_trace"
    if daily_rows <= 0:
        return "source_attached_core_trace_missing"
    if raw_refs_total > 0 and raw_refs_missing == 0:
        return "raw_source_trace_attached"
    return "raw_source_trace_partial"


def build_attachment_index(
    owner_branch: str,
    request_df: pd.DataFrame,
    source_trace_df: pd.DataFrame,
    daily_trace_df: pd.DataFrame,
    source_map_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for idx, request in enumerate(request_df.to_dict(orient="records"), start=1):
        request_id = normalize_text(request["evidence_request_id"])
        packet_id = normalize_text(request["source_confirmation_packet_row_id"])
        source_group = source_map_df.loc[source_map_df["confirmation_packet_row_id"].eq(packet_id)].copy()
        source_trace = source_trace_df.loc[source_trace_df["evidence_request_id"].eq(request_id)].copy()
        daily_trace = daily_trace_df.loc[daily_trace_df["evidence_request_id"].eq(request_id)].copy()
        start, end, expected_days = candidate_window(source_group, request)
        raw_refs_total = int(daily_trace["raw_csv_path"].nunique()) if not daily_trace.empty else 0
        raw_refs_found = int(daily_trace.loc[daily_trace["raw_csv_exists"].eq(1), "raw_csv_path"].nunique()) if not daily_trace.empty else 0
        raw_refs_missing = raw_refs_total - raw_refs_found
        source_rows = int(len(source_group))
        daily_rows = int(len(daily_trace))
        core_signal_days = int(daily_trace["fault_like_day"].sum()) if not daily_trace.empty else 0
        vpres_days = int(daily_trace["voltage_preserved_core_signal"].sum()) if not daily_trace.empty else 0
        common_days = int(daily_trace["common_cause_context_flag"].sum()) if not daily_trace.empty else 0
        artifact_days = int(daily_trace["measurement_artifact_hold_flag"].sum()) if not daily_trace.empty else 0
        status = attachment_status(source_rows, daily_rows, raw_refs_total, raw_refs_missing)
        rows.append(
            {
                "owner_branch": owner_branch,
                "attachment_row_id": f"BR096-VPRA-{idx:03d}",
                "evidence_request_id": request_id,
                "source_confirmation_packet_row_id": packet_id,
                "source_confirmation_family_id": normalize_text(request["source_confirmation_family_id"]),
                "site": normalize_text(request["site"]),
                "root_id": normalize_text(request["root_id"]),
                "panel_group_key": normalize_text(request["panel_group_key"]),
                "panel_id": normalize_text(request["panel_id"]),
                "request_priority": normalize_text(request["request_priority"]),
                "attachment_status": status,
                "raw_waveform_attachment_status": status,
                "source_candidate_trace_status": (
                    "source_candidate_trace_attached"
                    if source_rows == len(source_trace) and source_rows > 0
                    else "source_candidate_trace_partial"
                ),
                "core_window_trace_status": "core_window_attached" if daily_rows > 0 else "core_window_missing",
                "raw_file_reference_status": (
                    "raw_file_refs_all_found" if raw_refs_total > 0 and raw_refs_missing == 0 else "raw_file_refs_partial"
                ),
                "source_candidate_rows_attached": source_rows,
                "unique_source_candidate_anchor_dates": int(source_group["hard_episode_anchor_date"].nunique())
                if not source_group.empty
                else 0,
                "source_candidate_min_gap_days": numeric_int(source_group["gap_days"].min()) if not source_group.empty else 0,
                "source_candidate_median_gap_days": rounded(source_group["gap_days"].median())
                if not source_group.empty
                else 0.0,
                "source_candidate_max_gap_days": numeric_int(source_group["gap_days"].max()) if not source_group.empty else 0,
                "core_window_start_date": start,
                "core_window_end_date": end,
                "core_window_days_expected": expected_days,
                "core_window_rows_attached": daily_rows,
                "core_signal_days_attached": core_signal_days,
                "core_voltage_preserved_days_attached": vpres_days,
                "core_common_cause_flag_days": common_days,
                "core_measurement_artifact_hold_days": artifact_days,
                "raw_file_refs_total": raw_refs_total,
                "raw_file_refs_found": raw_refs_found,
                "raw_file_refs_missing": raw_refs_missing,
                "raw_file_ref_examples": semicolon(daily_trace["raw_csv_path"].tolist()) if not daily_trace.empty else "",
                "source_candidate_id_list": semicolon(source_group["search_candidate_row_id"].tolist())
                if not source_group.empty
                else "",
                "raw_waveform_is_independent_confirmation": 0,
                "physical_or_maintenance_evidence_attached": 0,
                "common_cause_clearance_attached": 0,
                "measurement_artifact_clearance_attached": 0,
                "counterexample_clearance_attached": 0,
                "evidence_ready_for_truth_use": 0,
                "positive_truth_candidate_approved": 0,
                "threshold_tuning_approved": 0,
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "next_review_action": (
                    "attach independent physical or maintenance evidence and clear counterexample/common-cause blockers"
                    if numeric_int(request["counterexample_risk_flag"])
                    else "attach independent physical or maintenance evidence and clear blockers"
                ),
                "notes": "Raw/source attachment only; not independent confirmation and not truth approval.",
            }
        )
    return pd.DataFrame(rows).reindex(columns=ATTACHMENT_COLUMNS)


def summarize_group(
    owner_branch: str,
    request_subset: pd.DataFrame,
    attachment_df: pd.DataFrame,
    source_trace_df: pd.DataFrame,
    daily_trace_df: pd.DataFrame,
    summary_scope: str,
    summary_key: str,
) -> dict[str, object]:
    request_ids = set(request_subset["evidence_request_id"].map(normalize_text))
    attachment_subset = attachment_df.loc[attachment_df["evidence_request_id"].map(normalize_text).isin(request_ids)]
    source_subset = source_trace_df.loc[source_trace_df["evidence_request_id"].map(normalize_text).isin(request_ids)]
    daily_subset = daily_trace_df.loc[daily_trace_df["evidence_request_id"].map(normalize_text).isin(request_ids)]
    return {
        "owner_branch": owner_branch,
        "summary_scope": summary_scope,
        "summary_key": summary_key,
        "request_rows": int(len(request_subset)),
        "attachment_rows": int(len(attachment_subset)),
        "source_candidate_trace_rows": int(len(source_subset)),
        "daily_trace_rows": int(len(daily_subset)),
        "raw_attached_request_rows": int(
            attachment_subset["attachment_status"].map(normalize_text).eq("raw_source_trace_attached").sum()
        )
        if not attachment_subset.empty
        else 0,
        "raw_file_refs_total": int(attachment_subset["raw_file_refs_total"].sum()) if not attachment_subset.empty else 0,
        "raw_file_refs_found": int(attachment_subset["raw_file_refs_found"].sum()) if not attachment_subset.empty else 0,
        "raw_file_refs_missing": int(attachment_subset["raw_file_refs_missing"].sum())
        if not attachment_subset.empty
        else 0,
        "core_signal_days_attached": int(attachment_subset["core_signal_days_attached"].sum())
        if not attachment_subset.empty
        else 0,
        "core_voltage_preserved_days_attached": int(attachment_subset["core_voltage_preserved_days_attached"].sum())
        if not attachment_subset.empty
        else 0,
        "counterexample_risk_rows": int(request_subset["counterexample_risk_flag"].sum())
        if not request_subset.empty
        else 0,
        "physical_or_maintenance_evidence_attached_sum": int(
            attachment_subset["physical_or_maintenance_evidence_attached"].sum()
        )
        if not attachment_subset.empty
        else 0,
        "common_cause_clearance_attached_sum": int(attachment_subset["common_cause_clearance_attached"].sum())
        if not attachment_subset.empty
        else 0,
        "measurement_artifact_clearance_attached_sum": int(
            attachment_subset["measurement_artifact_clearance_attached"].sum()
        )
        if not attachment_subset.empty
        else 0,
        "counterexample_clearance_attached_sum": int(attachment_subset["counterexample_clearance_attached"].sum())
        if not attachment_subset.empty
        else 0,
        "evidence_ready_for_truth_use_sum": int(attachment_subset["evidence_ready_for_truth_use"].sum())
        if not attachment_subset.empty
        else 0,
        "positive_truth_candidate_approved_sum": int(attachment_subset["positive_truth_candidate_approved"].sum())
        if not attachment_subset.empty
        else 0,
        "threshold_tuning_approved_sum": int(attachment_subset["threshold_tuning_approved"].sum())
        if not attachment_subset.empty
        else 0,
        "operator_facing_change_allowed_sum": int(attachment_subset["operator_facing_change_allowed"].sum())
        if not attachment_subset.empty
        else 0,
        "engine_patch_allowed_sum": int(attachment_subset["engine_patch_allowed"].sum())
        if not attachment_subset.empty
        else 0,
        "threshold_patch_allowed_sum": int(attachment_subset["threshold_patch_allowed"].sum())
        if not attachment_subset.empty
        else 0,
        "notes": "raw/source trace attached; independent physical/field confirmation still missing",
    }


def build_summary(
    owner_branch: str,
    request_df: pd.DataFrame,
    attachment_df: pd.DataFrame,
    source_trace_df: pd.DataFrame,
    daily_trace_df: pd.DataFrame,
) -> pd.DataFrame:
    rows = [summarize_group(owner_branch, request_df, attachment_df, source_trace_df, daily_trace_df, "overall", "all")]
    for site, group in request_df.groupby("site", sort=True):
        rows.append(summarize_group(owner_branch, group, attachment_df, source_trace_df, daily_trace_df, "site", site))
    for priority, group in request_df.groupby("request_priority", sort=True):
        rows.append(
            summarize_group(owner_branch, group, attachment_df, source_trace_df, daily_trace_df, "request_priority", priority)
        )
    return pd.DataFrame(rows).reindex(columns=SUMMARY_COLUMNS)


def build_action_queue(owner_branch: str, attachment_df: pd.DataFrame) -> pd.DataFrame:
    raw_attached = (
        int(attachment_df["attachment_status"].map(normalize_text).eq("raw_source_trace_attached").sum())
        if not attachment_df.empty
        else 0
    )
    risk_rows = int(attachment_df["counterexample_clearance_attached"].count()) if not attachment_df.empty else 0
    rows = [
        {
            "owner_branch": owner_branch,
            "sequence": 1,
            "action_id": "BR096-ACT-001",
            "action": "review attached raw/source traces",
            "input_filter": "attachment_status=raw_source_trace_attached",
            "purpose": "verify that the BR-092 source candidates and core daily windows actually point to available raw CSV references",
            "success_boundary": f"raw/source attached request rows={raw_attached}; approvals remain 0",
            "recommended_next_artifact": "voltage_preserved_independent_confirmation_attachment_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "This action checks traceability only; it is not physical confirmation.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 2,
            "action_id": "BR096-ACT-002",
            "action": "attach independent physical or maintenance evidence",
            "input_filter": "all BR-096 attachment rows",
            "purpose": "move from algorithmic raw support to auditable exact-panel confirmation",
            "success_boundary": "physical_or_maintenance_evidence_attached can become 1 only from external evidence, not this builder",
            "recommended_next_artifact": "voltage_preserved_independent_confirmation_attachment_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Expected next missing axis after BR-096.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 3,
            "action_id": "BR096-ACT-003",
            "action": "resolve blocker clearance axes",
            "input_filter": "common-cause, measurement-artifact, or counterexample risk rows",
            "purpose": "keep raw/source support from becoming truth while blockers are uncleared",
            "success_boundary": f"request rows needing blocker review={risk_rows}; truth/threshold/engine approvals remain 0",
            "recommended_next_artifact": "voltage_preserved_blocker_clearance_attachment_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Counterexample-risk rows need explicit reviewer clearance before truth rebuild.",
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
    request_input: Path,
    source_map_input: Path,
    data_root: Path,
    attachment_df: pd.DataFrame,
    source_trace_df: pd.DataFrame,
    daily_trace_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> None:
    source_map = input_resolution_sources or {}
    status_counts = (
        attachment_df["attachment_status"].value_counts().sort_index().to_dict() if not attachment_df.empty else {}
    )
    summary_cols = [
        "summary_scope",
        "summary_key",
        "request_rows",
        "raw_attached_request_rows",
        "source_candidate_trace_rows",
        "daily_trace_rows",
        "raw_file_refs_found",
        "raw_file_refs_missing",
        "evidence_ready_for_truth_use_sum",
        "engine_patch_allowed_sum",
    ]
    lines = [
        "# panel_day_engine_voltage_preserved_raw_source_attachment_v1",
        "",
        "## Purpose",
        "- Attach source-candidate trace and core/raw-file references to BR-095 evidence request rows.",
        "- Keep this as raw/source support only, not independent physical or maintenance confirmation.",
        "- Keep truth, threshold, operator-facing, and engine approvals blocked.",
        "",
        "## Inputs",
        f"- BR-095 request packet: `{request_input}`",
        f"- BR-093 source candidate map: `{source_map_input}`",
        f"- evidence input manifest: `{input_manifest_path if input_manifest_path is not None else 'not provided'}`",
        f"- data root: `{data_root}`",
        "",
        "## Input Resolution Sources",
        f"- `request_input`: `{source_map.get('request_input', 'legacy_default')}`",
        f"- `source_map_input`: `{source_map.get('source_map_input', 'legacy_default')}`",
        "",
        "## Real Result",
        f"- owner_branch: `{owner_branch}`",
        f"- attachment rows: `{len(attachment_df)}`",
        f"- source candidate trace rows: `{len(source_trace_df)}`",
        f"- daily trace rows: `{len(daily_trace_df)}`",
        f"- attachment status counts: `{json.dumps(status_counts, ensure_ascii=False, sort_keys=True)}`",
        f"- raw file refs found: `{int(attachment_df['raw_file_refs_found'].sum()) if not attachment_df.empty else 0}`",
        f"- raw file refs missing: `{int(attachment_df['raw_file_refs_missing'].sum()) if not attachment_df.empty else 0}`",
        f"- raw waveform independent confirmation rows: `{int(attachment_df['raw_waveform_is_independent_confirmation'].sum()) if not attachment_df.empty else 0}`",
        f"- physical/maintenance evidence attached sum: `{int(attachment_df['physical_or_maintenance_evidence_attached'].sum()) if not attachment_df.empty else 0}`",
        f"- evidence ready for truth use sum: `{int(attachment_df['evidence_ready_for_truth_use'].sum()) if not attachment_df.empty else 0}`",
        f"- threshold tuning approved sum: `{int(attachment_df['threshold_tuning_approved'].sum()) if not attachment_df.empty else 0}`",
        f"- engine patch allowed sum: `{int(attachment_df['engine_patch_allowed'].sum()) if not attachment_df.empty else 0}`",
        "",
        "## Summary",
        dataframe_to_markdown(summary_df.loc[:, summary_cols] if not summary_df.empty else summary_df),
        "",
        "## Safety Boundary",
        "- BR-096 attaches traceability evidence only.",
        "- Raw/core/source CSV references are not independent physical confirmation.",
        "- No truth rebuild, threshold replay, operator-facing promotion, or direct `panel_day_engine.py` edit is approved.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(
    path: Path,
    owner_branch: str,
    repo_root: Path,
    output_dir: Path,
    request_input: Path,
    source_map_input: Path,
    data_root: Path,
    attachment_df: pd.DataFrame,
    source_trace_df: pd.DataFrame,
    daily_trace_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "request_input": str(request_input),
        "source_map_input": str(source_map_input),
        "input_manifest": str(input_manifest_path) if input_manifest_path is not None else "",
        "input_resolution_sources": input_resolution_sources or {},
        "data_root": str(data_root),
        "attachment_rows": int(len(attachment_df)),
        "source_candidate_trace_rows": int(len(source_trace_df)),
        "daily_trace_rows": int(len(daily_trace_df)),
        "attachment_status_counts": attachment_df["attachment_status"].value_counts().sort_index().to_dict()
        if not attachment_df.empty
        else {},
        "raw_file_refs_found_sum": int(attachment_df["raw_file_refs_found"].sum()) if not attachment_df.empty else 0,
        "raw_file_refs_missing_sum": int(attachment_df["raw_file_refs_missing"].sum()) if not attachment_df.empty else 0,
        "raw_waveform_independent_confirmation_sum": int(
            attachment_df["raw_waveform_is_independent_confirmation"].sum()
        )
        if not attachment_df.empty
        else 0,
        "physical_or_maintenance_evidence_attached_sum": int(
            attachment_df["physical_or_maintenance_evidence_attached"].sum()
        )
        if not attachment_df.empty
        else 0,
        "common_cause_clearance_attached_sum": int(attachment_df["common_cause_clearance_attached"].sum())
        if not attachment_df.empty
        else 0,
        "measurement_artifact_clearance_attached_sum": int(
            attachment_df["measurement_artifact_clearance_attached"].sum()
        )
        if not attachment_df.empty
        else 0,
        "counterexample_clearance_attached_sum": int(attachment_df["counterexample_clearance_attached"].sum())
        if not attachment_df.empty
        else 0,
        "evidence_ready_for_truth_use_sum": int(attachment_df["evidence_ready_for_truth_use"].sum())
        if not attachment_df.empty
        else 0,
        "positive_truth_candidate_approved_sum": int(attachment_df["positive_truth_candidate_approved"].sum())
        if not attachment_df.empty
        else 0,
        "threshold_tuning_approved_sum": int(attachment_df["threshold_tuning_approved"].sum())
        if not attachment_df.empty
        else 0,
        "operator_facing_change_allowed_sum": int(attachment_df["operator_facing_change_allowed"].sum())
        if not attachment_df.empty
        else 0,
        "engine_patch_allowed_sum": int(attachment_df["engine_patch_allowed"].sum()) if not attachment_df.empty else 0,
        "threshold_patch_allowed_sum": int(attachment_df["threshold_patch_allowed"].sum())
        if not attachment_df.empty
        else 0,
        "summary_rows": int(len(summary_df)),
        "recommended_next_branch": "voltage_preserved_independent_confirmation_attachment_v1",
        "outputs": {
            "attachment_index": str(output_dir / ATTACHMENT_OUTPUT_NAME),
            "source_candidate_trace": str(output_dir / SOURCE_TRACE_OUTPUT_NAME),
            "daily_trace": str(output_dir / DAILY_TRACE_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Attach raw/source traceability evidence to BR-095 voltage-preserved evidence requests."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument(
        "--input-manifest",
        default=None,
        help="Optional JSON manifest for BR-095 request and BR-093 source-map inputs.",
    )
    parser.add_argument("--request-dir", default=DEFAULT_REQUEST_DIR, help="BR-095 evidence request output dir.")
    parser.add_argument("--request-input", default="", help="Optional direct BR-095 request CSV.")
    parser.add_argument("--source-map-input", default=DEFAULT_SOURCE_MAP, help="BR-093 candidate map CSV.")
    parser.add_argument("--data-root", default=DEFAULT_DATA_ROOT, help="Root containing data/<site>/out and raw CSVs.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory for BR-096 artifacts.")
    parser.add_argument("--owner-branch", default="BR-20260425-096")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    input_manifest_path, input_manifest = load_input_manifest(repo_root, args.input_manifest)
    argv = sys.argv[1:]
    explicit_flags = {
        flag
        for flag in [
            "--request-input",
            "--request-dir",
            "--source-map-input",
        ]
        if cli_flag_provided(flag, argv)
    }
    request_input, request_input_source = resolve_request_input(
        repo_root,
        args.request_input,
        args.request_dir,
        input_manifest,
        explicit_flags,
    )
    source_map_input, source_map_input_source = resolve_chain_input(
        repo_root,
        args.source_map_input,
        DEFAULT_SOURCE_MAP,
        input_manifest,
        "source_map_input",
        "--source-map-input",
        explicit_flags,
    )
    input_resolution_sources = {
        "request_input": request_input_source,
        "source_map_input": source_map_input_source,
    }
    data_root = resolve_path(repo_root, args.data_root)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    request_df = normalize_request(read_required_csv(request_input, REQUEST_REQUIRED_COLUMNS, "BR-095 requests"))
    source_map_df = normalize_source_map(read_required_csv(source_map_input, SOURCE_MAP_REQUIRED_COLUMNS, "BR-093 map"))
    assert_safe_input(request_df, source_map_df)
    sites = sorted(set(request_df["site"].map(normalize_text)))
    site_cores = {site: load_site_core(data_root, site) for site in sites}
    site_lookups = {site: core_lookup(site_cores[site]) for site in sites}

    source_trace_df = build_source_trace(args.owner_branch, data_root, request_df, source_map_df, site_lookups)
    daily_trace_df = build_daily_trace(args.owner_branch, data_root, request_df, source_map_df, site_cores)
    attachment_df = build_attachment_index(args.owner_branch, request_df, source_trace_df, daily_trace_df, source_map_df)
    summary_df = build_summary(args.owner_branch, request_df, attachment_df, source_trace_df, daily_trace_df)
    action_df = build_action_queue(args.owner_branch, attachment_df)

    attachment_df.to_csv(output_dir / ATTACHMENT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    source_trace_df.to_csv(output_dir / SOURCE_TRACE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    daily_trace_df.to_csv(output_dir / DAILY_TRACE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(
        output_dir / NOTE_OUTPUT_NAME,
        args.owner_branch,
        request_input,
        source_map_input,
        data_root,
        attachment_df,
        source_trace_df,
        daily_trace_df,
        summary_df,
        input_manifest_path,
        input_resolution_sources,
    )
    write_json(
        output_dir / JSON_OUTPUT_NAME,
        args.owner_branch,
        repo_root,
        output_dir,
        request_input,
        source_map_input,
        data_root,
        attachment_df,
        source_trace_df,
        daily_trace_df,
        summary_df,
        input_manifest_path,
        input_resolution_sources,
    )

    print(
        json.dumps(
            {
                "owner_branch": args.owner_branch,
                "attachment_rows": int(len(attachment_df)),
                "source_candidate_trace_rows": int(len(source_trace_df)),
                "daily_trace_rows": int(len(daily_trace_df)),
                "attachment_status_counts": attachment_df["attachment_status"].value_counts().sort_index().to_dict()
                if not attachment_df.empty
                else {},
                "raw_file_refs_found_sum": int(attachment_df["raw_file_refs_found"].sum())
                if not attachment_df.empty
                else 0,
                "raw_file_refs_missing_sum": int(attachment_df["raw_file_refs_missing"].sum())
                if not attachment_df.empty
                else 0,
                "raw_waveform_independent_confirmation_sum": int(
                    attachment_df["raw_waveform_is_independent_confirmation"].sum()
                )
                if not attachment_df.empty
                else 0,
                "physical_or_maintenance_evidence_attached_sum": int(
                    attachment_df["physical_or_maintenance_evidence_attached"].sum()
                )
                if not attachment_df.empty
                else 0,
                "evidence_ready_for_truth_use_sum": int(attachment_df["evidence_ready_for_truth_use"].sum())
                if not attachment_df.empty
                else 0,
                "threshold_tuning_approved_sum": int(attachment_df["threshold_tuning_approved"].sum())
                if not attachment_df.empty
                else 0,
                "outputs": {
                    "attachment_index": str(output_dir / ATTACHMENT_OUTPUT_NAME),
                    "source_candidate_trace": str(output_dir / SOURCE_TRACE_OUTPUT_NAME),
                    "daily_trace": str(output_dir / DAILY_TRACE_OUTPUT_NAME),
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
