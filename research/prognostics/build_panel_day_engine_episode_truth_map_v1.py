#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


MAP_OUTPUT_NAME = "panel_day_engine_episode_truth_map_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_episode_truth_map_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_episode_truth_map_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_episode_truth_map_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_episode_truth_map_v1.json"

BR017_EPISODE_DEFAULT = "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_EPISODE_SHADOW_PANEL_V1.csv"
BR017_G1_DEFAULT = "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_G1_LONGGAP_CASES_V1.csv"
BR023_PACKET_DEFAULT = "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_023_BLOCKER_DETAIL_REVIEW_PACKET_V1.csv"
BR065_SHAPE_DEFAULT = (
    "/private/tmp/local_morphology_family_shape_review_check/"
    "panel_day_engine_local_morphology_family_shape_review_v1.csv"
)
BR080_BACKLOG_DEFAULT = (
    "/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check/"
    "panel_day_engine_subtype_truth_expansion_backlog_v1.csv"
)

MAP_COLUMNS = [
    "owner_branch",
    "episode_truth_case_id",
    "source_artifact",
    "source_case_id",
    "site",
    "panel_id",
    "family_key",
    "family_label_ko",
    "subtype_key",
    "subtype_label_ko",
    "episode_anchor_date",
    "episode_anchor_kind",
    "strict_trigger_date",
    "gap_days",
    "signal_start_date",
    "signal_end_date",
    "signal_span_days",
    "signal_day_count",
    "duration_proxy_days",
    "recurrence_proxy_days",
    "warning_proxy_days",
    "common_cause_flag_sum",
    "strict_trigger_proximal_common_cause_flag",
    "episode_truth_bucket",
    "episode_truth_status",
    "promotion_reading",
    "required_next_evidence",
    "recommended_next_artifact",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "episode_truth_bucket",
    "source_artifact",
    "case_count",
    "unique_panel_count",
    "p0_review_count",
    "operator_facing_change_allowed_sum",
    "engine_patch_allowed_sum",
    "threshold_patch_allowed_sum",
    "recommended_next_artifacts",
]

ACTION_COLUMNS = [
    "owner_branch",
    "sequence",
    "action_id",
    "action",
    "input_filter",
    "purpose",
    "recommended_artifact",
    "success_boundary",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

FAMILY_LABEL_TO_KEY = {
    "열화·오염·음영 계열": "degradation_soiling_shadow",
    "열화·오염·음영 계열 후보 보류": "degradation_soiling_shadow",
    "접속 불량·부분 개방 계열": "open_connection_partial",
    "다이오드·서브스트링 계열": "diode_substring",
    "센서·피드백·계측 이상 계열": "measurement_feedback",
    "센서·계측 피드백 계열": "measurement_feedback",
    "외부계통·공통원인 계열": "external_common_cause",
    "strict trigger anchored sudden fault": "strict_anchor_sudden",
    "개방/장치이상형": "open_connection_partial",
    "모듈손상형": "degradation_soiling_shadow",
}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def numeric_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


def numeric_float(value: object) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0.0 if pd.isna(numeric) else float(numeric)


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def load_input_manifest(repo_root: Path, value: str | Path) -> tuple[Path | None, dict[str, Any]]:
    text = normalize_text(value)
    if not text:
        return None, {}
    manifest_path = resolve_path(repo_root, text)
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing episode-truth input manifest: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"episode-truth input manifest must be a JSON object: {manifest_path}")
    return manifest_path, payload


def manifest_path_value(manifest: dict[str, Any], key: str) -> str:
    candidates: list[Any] = [manifest.get(key)]
    for section_name in ["inputs", "artifacts"]:
        section = manifest.get(section_name)
        if isinstance(section, dict):
            value = section.get(key)
            if isinstance(value, dict):
                candidates.extend([value.get("path"), value.get("artifact_path"), value.get("static_path")])
            else:
                candidates.append(value)
    for value in candidates:
        text = normalize_text(value)
        if text:
            return text
    return ""


def resolve_chain_input(
    repo_root: Path,
    arg_value: str | Path,
    default_value: str | Path,
    manifest: dict[str, Any],
    manifest_key: str,
    flag_name: str,
) -> tuple[Path, str]:
    if normalize_text(arg_value) != normalize_text(default_value):
        return resolve_path(repo_root, arg_value), "explicit_cli"
    if manifest:
        manifest_value = manifest_path_value(manifest, manifest_key)
        if not manifest_value:
            raise ValueError(
                f"episode-truth input manifest is missing `{manifest_key}`; "
                f"add it under top-level or `inputs`, or pass {flag_name}"
            )
        return resolve_path(repo_root, manifest_value), "input_manifest"
    return resolve_path(repo_root, arg_value), "legacy_default"


def read_optional_csv(path: Path, required_cols: list[str], name: str) -> tuple[pd.DataFrame, bool]:
    if not path.exists():
        return pd.DataFrame(columns=required_cols), False
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")
    return df, True


def family_key_from_label(label: str) -> str:
    return FAMILY_LABEL_TO_KEY.get(label, "")


def classify_episode(
    *,
    family_key: str,
    source_artifact: str,
    gap_days: int,
    duration_proxy_days: int,
    recurrence_proxy_days: int,
    warning_proxy_days: int,
    common_cause_flag_sum: int,
    strict_common_flag: int,
    episode_class: str,
    promotion_decision: str,
    g1_flag: int,
    shape_bucket: str,
) -> tuple[str, str, str, str, str]:
    if g1_flag and gap_days > 120 and ("long_gap" in episode_class or "backdating" in promotion_decision):
        return (
            "long_gap_backdating_hold",
            "truth_pending",
            "block_precursor_backdating",
            "confirm one-day degradation, long normal gap, and later strict-trigger anchor",
            "panel_day_engine_episode_truth_review_packet_v1",
        )
    if common_cause_flag_sum > 0 or "common_cause" in episode_class or "block_individual_precursor" in promotion_decision:
        return (
            "common_cause_or_group_episode_hold",
            "truth_pending",
            "block_individual_precursor",
            "verify group/site simultaneity, report-lane entry, and date alignment before panel-local reading",
            "panel_day_engine_episode_common_cause_review_packet_v1",
        )
    if "recovery" in shape_bucket or recurrence_proxy_days >= 20:
        return (
            "recovery_recurrence_observation",
            "truth_pending",
            "hold_observation_only",
            "separate recurrence/recovery morphology from actual fault-family evidence",
            "panel_day_engine_episode_recovery_recurrence_review_packet_v1",
        )
    if "voltage_dominant" in shape_bucket:
        return (
            "voltage_dominant_review_episode",
            "truth_pending",
            "hold_pending_physical_confirmation",
            "attach exact-panel physical measurement or maintenance evidence before thresholding",
            "rerun BR-069/BR-070 after evidence attachment",
        )
    if family_key == "strict_anchor_sudden" or (gap_days == 0 and duration_proxy_days <= 1):
        return (
            "strict_anchor_sudden_review",
            "truth_pending",
            "no_precursor_promotion_without_prior_episode",
            "prove prior normal period or find validated recurring precursor before reclassifying",
            "panel_day_engine_episode_truth_review_packet_v1",
        )
    if 7 <= gap_days <= 120 and (duration_proxy_days >= 2 or recurrence_proxy_days >= 2 or warning_proxy_days >= 2):
        return (
            "durable_precursor_candidate_review",
            "truth_pending",
            "manual_review_before_promotion",
            "verify episode continuity, recurrence, family shape, and common-cause exclusion",
            "panel_day_engine_episode_truth_review_packet_v1",
        )
    if duration_proxy_days <= 1:
        return (
            "one_day_episode_hold",
            "truth_pending",
            "hold_episode_only",
            "check fast recovery, sparse signal, and common-cause/date displacement before onset promotion",
            "panel_day_engine_episode_truth_review_packet_v1",
        )
    return (
        "manual_episode_review",
        "truth_pending",
        "manual_review_before_promotion",
        "review episode duration, recurrence, family shape, and blocker axes",
        "panel_day_engine_episode_truth_review_packet_v1",
    )


def build_episode_shadow_rows(owner_branch: str, episode_df: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(episode_df.to_dict(orient="records"), start=1):
        family_label = normalize_text(row.get("fault_family_hypothesis_shadow_ko")) or normalize_text(row.get("algorithm_family_ko"))
        family_key = family_key_from_label(family_label)
        gap_days = numeric_int(row.get("gap_days"))
        duration_proxy_days = max(
            numeric_int(row.get("degradation_days_in_window")),
            numeric_int(row.get("shadow_days_in_window")),
            numeric_int(row.get("low_mid_ratio_days_in_window")),
        )
        recurrence_proxy_days = max(
            numeric_int(row.get("event_A_days_after_onset")),
            numeric_int(row.get("low_mid_ratio_days_after_onset")),
        )
        warning_proxy_days = max(
            numeric_int(row.get("pre_ews_days_in_window")),
            numeric_int(row.get("ews_warning_days_in_window")),
            numeric_int(row.get("pre_alarm_days_in_window")),
            numeric_int(row.get("prefault_B_effective_days_in_window")),
        )
        common_cause_flag_sum = (
            numeric_int(row.get("subgroup_common_cause_history_flag"))
            + numeric_int(row.get("strict_trigger_proximal_common_cause_flag"))
            + (1 if numeric_float(row.get("group_event_A_fraction_on_episode")) >= 0.3 else 0)
        )
        bucket, status, promotion, required, artifact = classify_episode(
            family_key=family_key,
            source_artifact="br017_episode_shadow",
            gap_days=gap_days,
            duration_proxy_days=duration_proxy_days,
            recurrence_proxy_days=recurrence_proxy_days,
            warning_proxy_days=warning_proxy_days,
            common_cause_flag_sum=common_cause_flag_sum,
            strict_common_flag=numeric_int(row.get("strict_trigger_proximal_common_cause_flag")),
            episode_class=normalize_text(row.get("episode_class_shadow")),
            promotion_decision=normalize_text(row.get("precursor_promotion_shadow_decision")),
            g1_flag=numeric_int(row.get("g1_suppressed_event_shadow_flag")),
            shape_bucket="",
        )
        rows.append(
            {
                "owner_branch": owner_branch,
                "episode_truth_case_id": f"BR081-EPS-{idx:03d}",
                "source_artifact": "br017_episode_shadow",
                "source_case_id": f"br017_episode_shadow:{idx}",
                "site": normalize_text(row.get("site")),
                "panel_id": normalize_text(row.get("panel_id")),
                "family_key": family_key,
                "family_label_ko": family_label,
                "subtype_key": "long_gap_one_day_stress" if numeric_int(row.get("g1_suppressed_event_shadow_flag")) else "",
                "subtype_label_ko": "장기 gap 단일 저하 보류형" if numeric_int(row.get("g1_suppressed_event_shadow_flag")) else "",
                "episode_anchor_date": normalize_text(row.get("episode_basis_date")),
                "episode_anchor_kind": normalize_text(row.get("episode_basis_kind")),
                "strict_trigger_date": normalize_text(row.get("strict_trigger_date")),
                "gap_days": gap_days,
                "signal_start_date": normalize_text(row.get("episode_basis_date")),
                "signal_end_date": normalize_text(row.get("strict_trigger_date")),
                "signal_span_days": gap_days,
                "signal_day_count": duration_proxy_days,
                "duration_proxy_days": duration_proxy_days,
                "recurrence_proxy_days": recurrence_proxy_days,
                "warning_proxy_days": warning_proxy_days,
                "common_cause_flag_sum": common_cause_flag_sum,
                "strict_trigger_proximal_common_cause_flag": numeric_int(row.get("strict_trigger_proximal_common_cause_flag")),
                "episode_truth_bucket": bucket,
                "episode_truth_status": status,
                "promotion_reading": promotion,
                "required_next_evidence": required,
                "recommended_next_artifact": artifact,
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "notes": normalize_text(row.get("shadow_reason_ko")),
            }
        )
    return rows


def build_shape_rows(owner_branch: str, shape_df: pd.DataFrame, start_idx: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for offset, row in enumerate(shape_df.to_dict(orient="records"), start=0):
        idx = start_idx + offset
        family_key = normalize_text(row.get("candidate_family_track"))
        if family_key == "open_connection_or_measurement_voltage_axis":
            family_key = "open_connection_partial"
        shape_bucket = normalize_text(row.get("family_shape_judgment_bucket"))
        signal_day_count = numeric_int(row.get("signal_day_count"))
        recurrence_days = max(numeric_int(row.get("re_drop_days")), numeric_int(row.get("recovered_sustained_days")))
        common_cause = numeric_int(row.get("subgroup_common_cause_days")) + (1 if numeric_float(row.get("max_co_drop_frac")) >= 0.3 else 0)
        bucket, status, promotion, required, artifact = classify_episode(
            family_key=family_key,
            source_artifact="br065_local_shape_review",
            gap_days=numeric_int(row.get("signal_span_days")),
            duration_proxy_days=signal_day_count,
            recurrence_proxy_days=recurrence_days,
            warning_proxy_days=0,
            common_cause_flag_sum=common_cause,
            strict_common_flag=0,
            episode_class="",
            promotion_decision="",
            g1_flag=0,
            shape_bucket=shape_bucket,
        )
        rows.append(
            {
                "owner_branch": owner_branch,
                "episode_truth_case_id": f"BR081-SHP-{idx:03d}",
                "source_artifact": "br065_local_shape_review",
                "source_case_id": normalize_text(row.get("shape_case_id")),
                "site": normalize_text(row.get("site")),
                "panel_id": normalize_text(row.get("panel_id")),
                "family_key": family_key,
                "family_label_ko": normalize_text(row.get("candidate_family_label_ko")),
                "subtype_key": "",
                "subtype_label_ko": "",
                "episode_anchor_date": normalize_text(row.get("first_signal_date")),
                "episode_anchor_kind": "first_signal_date",
                "strict_trigger_date": "",
                "gap_days": numeric_int(row.get("signal_span_days")),
                "signal_start_date": normalize_text(row.get("first_signal_date")),
                "signal_end_date": normalize_text(row.get("last_signal_date")),
                "signal_span_days": numeric_int(row.get("signal_span_days")),
                "signal_day_count": signal_day_count,
                "duration_proxy_days": signal_day_count,
                "recurrence_proxy_days": recurrence_days,
                "warning_proxy_days": 0,
                "common_cause_flag_sum": common_cause,
                "strict_trigger_proximal_common_cause_flag": 0,
                "episode_truth_bucket": bucket,
                "episode_truth_status": status,
                "promotion_reading": promotion,
                "required_next_evidence": required,
                "recommended_next_artifact": artifact,
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "notes": normalize_text(row.get("review_note")),
            }
        )
    return rows


def build_blocker_rows(owner_branch: str, packet_df: pd.DataFrame, start_idx: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for offset, row in enumerate(packet_df.to_dict(orient="records"), start=0):
        idx = start_idx + offset
        family_label = normalize_text(row.get("fault_family_hypothesis_shadow_ko"))
        family_key = family_key_from_label(family_label)
        common_cause = (
            numeric_int(row.get("site_event_history_flag"))
            + numeric_int(row.get("group_off_history_flag"))
            + numeric_int(row.get("subgroup_common_cause_history_flag"))
            + numeric_int(row.get("common_cause_history_flag"))
            + numeric_int(row.get("strict_trigger_proximal_common_cause_flag"))
        )
        bucket, status, promotion, required, artifact = classify_episode(
            family_key=family_key,
            source_artifact="br023_blocker_detail_packet",
            gap_days=numeric_int(row.get("gap_days")),
            duration_proxy_days=1,
            recurrence_proxy_days=numeric_int(row.get("secondary_window_qualified_count")),
            warning_proxy_days=0,
            common_cause_flag_sum=common_cause,
            strict_common_flag=numeric_int(row.get("strict_trigger_proximal_common_cause_flag")),
            episode_class=normalize_text(row.get("subtype_promotion_blocker_detail_shadow")),
            promotion_decision=normalize_text(row.get("promotion_decision_bucket")),
            g1_flag=0,
            shape_bucket="",
        )
        rows.append(
            {
                "owner_branch": owner_branch,
                "episode_truth_case_id": f"BR081-BLK-{idx:03d}",
                "source_artifact": "br023_blocker_detail_packet",
                "source_case_id": normalize_text(row.get("review_packet_id")),
                "site": normalize_text(row.get("site")),
                "panel_id": normalize_text(row.get("panel_id")),
                "family_key": family_key,
                "family_label_ko": family_label,
                "subtype_key": "",
                "subtype_label_ko": normalize_text(row.get("fault_subtype_hypothesis_shadow_ko")),
                "episode_anchor_date": normalize_text(row.get("retrospective_onset_date") or row.get("strict_trigger_date")),
                "episode_anchor_kind": normalize_text(row.get("onset_method")),
                "strict_trigger_date": normalize_text(row.get("strict_trigger_date")),
                "gap_days": numeric_int(row.get("gap_days")),
                "signal_start_date": normalize_text(row.get("earliest_warning_date")),
                "signal_end_date": normalize_text(row.get("strict_trigger_date")),
                "signal_span_days": numeric_int(row.get("gap_days")),
                "signal_day_count": 1,
                "duration_proxy_days": 1,
                "recurrence_proxy_days": numeric_int(row.get("secondary_window_qualified_count")),
                "warning_proxy_days": 0,
                "common_cause_flag_sum": common_cause,
                "strict_trigger_proximal_common_cause_flag": numeric_int(row.get("strict_trigger_proximal_common_cause_flag")),
                "episode_truth_bucket": bucket,
                "episode_truth_status": status,
                "promotion_reading": promotion,
                "required_next_evidence": required,
                "recommended_next_artifact": artifact,
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "notes": normalize_text(row.get("review_question_ko")),
            }
        )
    return rows


def build_backlog_rows(owner_branch: str, backlog_df: pd.DataFrame, start_idx: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    relevant = backlog_df.loc[
        backlog_df["recommended_next_artifact"].map(normalize_text).eq("panel_day_engine_episode_truth_map_v1")
    ].copy()
    for offset, row in enumerate(relevant.to_dict(orient="records"), start=0):
        idx = start_idx + offset
        rows.append(
            {
                "owner_branch": owner_branch,
                "episode_truth_case_id": f"BR081-REQ-{idx:03d}",
                "source_artifact": "br080_subtype_truth_backlog",
                "source_case_id": normalize_text(row.get("backlog_case_id")),
                "site": "",
                "panel_id": "",
                "family_key": normalize_text(row.get("family_key")),
                "family_label_ko": normalize_text(row.get("family_label_ko")),
                "subtype_key": normalize_text(row.get("subtype_key")),
                "subtype_label_ko": normalize_text(row.get("subtype_label_ko")),
                "episode_anchor_date": "",
                "episode_anchor_kind": "subtype_requirement",
                "strict_trigger_date": "",
                "gap_days": "",
                "signal_start_date": "",
                "signal_end_date": "",
                "signal_span_days": "",
                "signal_day_count": "",
                "duration_proxy_days": "",
                "recurrence_proxy_days": "",
                "warning_proxy_days": "",
                "common_cause_flag_sum": "",
                "strict_trigger_proximal_common_cause_flag": "",
                "episode_truth_bucket": "episode_truth_requirement",
                "episode_truth_status": "truth_pending",
                "promotion_reading": "require_episode_truth_before_threshold_replay",
                "required_next_evidence": normalize_text(row.get("required_positive_evidence_axes")),
                "recommended_next_artifact": "panel_day_engine_episode_truth_review_packet_v1",
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "notes": normalize_text(row.get("review_question_ko")),
            }
        )
    return rows


def build_summary(owner_branch: str, map_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (bucket, source), group in map_df.groupby(["episode_truth_bucket", "source_artifact"], sort=False):
        p0 = int(
            group["episode_truth_bucket"].isin(
                [
                    "long_gap_backdating_hold",
                    "durable_precursor_candidate_review",
                    "strict_anchor_sudden_review",
                    "common_cause_or_group_episode_hold",
                    "episode_truth_requirement",
                ]
            ).sum()
        )
        rows.append(
            {
                "owner_branch": owner_branch,
                "episode_truth_bucket": bucket,
                "source_artifact": source,
                "case_count": int(len(group)),
                "unique_panel_count": int(group["panel_id"].map(normalize_text).replace("", pd.NA).dropna().nunique()),
                "p0_review_count": p0,
                "operator_facing_change_allowed_sum": int(group["operator_facing_change_allowed"].sum()),
                "engine_patch_allowed_sum": int(group["engine_patch_allowed"].sum()),
                "threshold_patch_allowed_sum": int(group["threshold_patch_allowed"].sum()),
                "recommended_next_artifacts": "; ".join(sorted(set(group["recommended_next_artifact"].map(normalize_text)))),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def build_action_queue(owner_branch: str) -> pd.DataFrame:
    specs = [
        (
            "ACT-001",
            "review long-gap/backdating and strict-sudden rows",
            "episode_truth_bucket in {long_gap_backdating_hold, strict_anchor_sudden_review}",
            "settle the user's core question: no precursor, over-backdating, or overly conservative missed precursor",
            "panel_day_engine_episode_truth_review_packet_v1",
            "each row has reviewed prior signal chain, normal gap, and strict-trigger anchor",
            "This comes before any precursor-vs-abrupt rule change.",
        ),
        (
            "ACT-002",
            "review durable precursor candidates",
            "episode_truth_bucket == durable_precursor_candidate_review",
            "identify real recurring/continuous precursor episodes without direct promotion",
            "panel_day_engine_episode_truth_review_packet_v1",
            "episode continuity, recurrence, family shape, and common-cause exclusion are explicit",
            "Positive review rows become threshold replay inputs, not production labels.",
        ),
        (
            "ACT-003",
            "review common-cause and group episodes",
            "episode_truth_bucket == common_cause_or_group_episode_hold",
            "keep site/root/group synchrony from leaking into panel-local precursor claims",
            "panel_day_engine_episode_common_cause_review_packet_v1",
            "official/current bridge or structural blocker role is resolved",
            "BR-076 gates remain mandatory before semantic loosening.",
        ),
        (
            "ACT-004",
            "review recovery/recurrence observations",
            "episode_truth_bucket == recovery_recurrence_observation",
            "separate operational recurrence from fault-family evidence",
            "panel_day_engine_episode_recovery_recurrence_review_packet_v1",
            "recovery-only rows are either linked to a family shape or kept observation-only",
            "Do not treat long recurrence alone as subtype truth.",
        ),
        (
            "ACT-005",
            "open subtype-conditioned threshold replay",
            "reviewed positive/negative episode truth exists",
            "only after episode truth rows exist, compare threshold candidates safely",
            "panel_day_engine_subtype_threshold_replay_v1",
            "result delta, false-positive pressure, common-cause blockers, and holdout impact are quantified",
            "Replay first; production patch later.",
        ),
    ]
    rows = [
        {
            "owner_branch": owner_branch,
            "sequence": idx,
            "action_id": action_id,
            "action": action,
            "input_filter": input_filter,
            "purpose": purpose,
            "recommended_artifact": artifact,
            "success_boundary": boundary,
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": notes,
        }
        for idx, (action_id, action, input_filter, purpose, artifact, boundary, notes) in enumerate(specs, start=1)
    ]
    return pd.DataFrame(rows, columns=ACTION_COLUMNS)


def write_note(
    output_dir: Path,
    owner_branch: str,
    map_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    action_df: pd.DataFrame,
    input_presence: dict[str, bool],
    input_manifest_path: Path | None,
    shape_input_source: str,
    backlog_input_source: str,
) -> None:
    missing_inputs = [name for name, present in input_presence.items() if not present]
    note = f"""# Panel Day Engine Episode Truth Map V1

## Purpose
- Convert day/panel candidate rows into an episode-level truth review map.
- Separate durable precursor, one-day episode, long-gap backdating, strict-sudden, recovery-only, voltage-review, and common-cause/group episodes.
- Keep this map truth-review-only: no engine patch, no threshold patch, no operator-facing promotion.

## Outputs
- `{output_dir / MAP_OUTPUT_NAME}`
- `{output_dir / SUMMARY_OUTPUT_NAME}`
- `{output_dir / ACTION_OUTPUT_NAME}`
- `{output_dir / JSON_OUTPUT_NAME}`

## Result
- episode truth map rows: `{len(map_df)}`
- summary rows: `{len(summary_df)}`
- action rows: `{len(action_df)}`
- operator-facing change allowed sum: `{int(map_df["operator_facing_change_allowed"].sum() + action_df["operator_facing_change_allowed"].sum())}`
- engine patch allowed sum: `{int(map_df["engine_patch_allowed"].sum() + action_df["engine_patch_allowed"].sum())}`
- threshold patch allowed sum: `{int(map_df["threshold_patch_allowed"].sum() + action_df["threshold_patch_allowed"].sum())}`
- missing optional inputs: `{len(missing_inputs)}`
- episode-truth input manifest: `{input_manifest_path if input_manifest_path else 'not provided'}`
- shape input source: `{shape_input_source}`
- backlog input source: `{backlog_input_source}`

## Reading
- `episode_truth_status` is `truth_pending` for all rows.
- This map does not prove a precursor; it creates the review row universe needed to prove or reject one.
- Current exact changes remain blocked until reviewed episode truth and counterexamples exist.

## Missing Optional Inputs
{chr(10).join(f"- `{name}`" for name in missing_inputs) if missing_inputs else "- none"}

## Repro Command
```bash
python3 research/prognostics/build_panel_day_engine_episode_truth_map_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir {output_dir}
```
"""
    (output_dir / NOTE_OUTPUT_NAME).write_text(note, encoding="utf-8")


def build_outputs(
    repo_root: Path,
    output_dir: Path,
    owner_branch: str,
    episode_input: Path,
    g1_input: Path,
    blocker_input: Path,
    shape_input: Path,
    backlog_input: Path,
    input_manifest_path: Path | None = None,
    shape_input_source: str = "legacy_default",
    backlog_input_source: str = "legacy_default",
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    episode_df, episode_present = read_optional_csv(
        episode_input,
        ["site", "panel_id", "episode_basis_date", "strict_trigger_date", "gap_days", "episode_class_shadow"],
        "br017_episode_shadow",
    )
    g1_df, g1_present = read_optional_csv(
        g1_input,
        ["site", "panel_id", "gap_days", "g1_suppressed_event_shadow_flag", "episode_class_shadow"],
        "br017_g1_longgap",
    )
    blocker_df, blocker_present = read_optional_csv(
        blocker_input,
        ["review_packet_id", "site", "panel_id", "gap_days", "fault_family_hypothesis_shadow_ko"],
        "br023_blocker_packet",
    )
    shape_df, shape_present = read_optional_csv(
        shape_input,
        ["shape_case_id", "site", "panel_id", "family_shape_judgment_bucket", "signal_day_count"],
        "br065_shape_review",
    )
    backlog_df, backlog_present = read_optional_csv(
        backlog_input,
        ["backlog_case_id", "family_key", "subtype_key", "recommended_next_artifact", "required_positive_evidence_axes"],
        "br080_subtype_truth_backlog",
    )

    rows: list[dict[str, object]] = []
    if episode_present:
        rows.extend(build_episode_shadow_rows(owner_branch, episode_df))
    # Keep the dedicated G1 file as an explicit duplicate review lens because it is the historical backdating question.
    if g1_present:
        g1_rows = build_episode_shadow_rows(owner_branch, g1_df)
        for row in g1_rows:
            row["episode_truth_case_id"] = row["episode_truth_case_id"].replace("BR081-EPS", "BR081-G1")
            row["source_artifact"] = "br017_g1_longgap_cases"
            row["source_case_id"] = row["source_case_id"].replace("br017_episode_shadow", "br017_g1_longgap_cases")
        rows.extend(g1_rows)
    if shape_present:
        rows.extend(build_shape_rows(owner_branch, shape_df, len(rows) + 1))
    if blocker_present:
        rows.extend(build_blocker_rows(owner_branch, blocker_df, len(rows) + 1))
    if backlog_present:
        rows.extend(build_backlog_rows(owner_branch, backlog_df, len(rows) + 1))

    map_df = pd.DataFrame(rows, columns=MAP_COLUMNS)
    summary_df = build_summary(owner_branch, map_df)
    action_df = build_action_queue(owner_branch)

    map_df.to_csv(output_dir / MAP_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")

    input_presence = {
        "br017_episode_shadow": episode_present,
        "br017_g1_longgap": g1_present,
        "br023_blocker_packet": blocker_present,
        "br065_shape_review": shape_present,
        "br080_subtype_truth_backlog": backlog_present,
    }
    write_note(
        output_dir,
        owner_branch,
        map_df,
        summary_df,
        action_df,
        input_presence,
        input_manifest_path,
        shape_input_source,
        backlog_input_source,
    )

    payload = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "input_manifest": str(input_manifest_path) if input_manifest_path else "",
        "shape_input": str(shape_input),
        "shape_input_source": shape_input_source,
        "backlog_input": str(backlog_input),
        "backlog_input_source": backlog_input_source,
        "episode_truth_map_rows": int(len(map_df)),
        "summary_rows": int(len(summary_df)),
        "action_rows": int(len(action_df)),
        "bucket_counts": {str(k): int(v) for k, v in map_df["episode_truth_bucket"].value_counts().items()},
        "truth_status_counts": {str(k): int(v) for k, v in map_df["episode_truth_status"].value_counts().items()},
        "operator_facing_change_allowed_sum": int(map_df["operator_facing_change_allowed"].sum() + action_df["operator_facing_change_allowed"].sum()),
        "engine_patch_allowed_sum": int(map_df["engine_patch_allowed"].sum() + action_df["engine_patch_allowed"].sum()),
        "threshold_patch_allowed_sum": int(map_df["threshold_patch_allowed"].sum() + action_df["threshold_patch_allowed"].sum()),
        "input_presence": input_presence,
        "missing_optional_input_count": int(sum(1 for present in input_presence.values() if not present)),
        "recommended_next_branch": "panel_day_engine_episode_truth_review_packet_v1",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "map": str(output_dir / MAP_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    (output_dir / JSON_OUTPUT_NAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output-dir", type=Path, default=Path("/private/tmp/panel_day_engine_episode_truth_map_br081_check"))
    parser.add_argument("--owner-branch", default="BR-20260425-081")
    parser.add_argument("--episode-input", default=BR017_EPISODE_DEFAULT)
    parser.add_argument("--g1-input", default=BR017_G1_DEFAULT)
    parser.add_argument("--blocker-input", default=BR023_PACKET_DEFAULT)
    parser.add_argument("--shape-input", default=BR065_SHAPE_DEFAULT)
    parser.add_argument("--backlog-input", default=BR080_BACKLOG_DEFAULT)
    parser.add_argument(
        "--input-manifest",
        default="",
        help=(
            "Optional JSON manifest with `shape_input` and `backlog_input`. "
            "Explicit --shape-input/--backlog-input values take precedence."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    input_manifest_path, input_manifest = load_input_manifest(repo_root, args.input_manifest)
    shape_input, shape_input_source = resolve_chain_input(
        repo_root,
        args.shape_input,
        BR065_SHAPE_DEFAULT,
        input_manifest,
        "shape_input",
        "--shape-input",
    )
    backlog_input, backlog_input_source = resolve_chain_input(
        repo_root,
        args.backlog_input,
        BR080_BACKLOG_DEFAULT,
        input_manifest,
        "backlog_input",
        "--backlog-input",
    )
    payload = build_outputs(
        repo_root=repo_root,
        output_dir=args.output_dir,
        owner_branch=args.owner_branch,
        episode_input=resolve_path(repo_root, args.episode_input),
        g1_input=resolve_path(repo_root, args.g1_input),
        blocker_input=resolve_path(repo_root, args.blocker_input),
        shape_input=shape_input,
        backlog_input=backlog_input,
        input_manifest_path=input_manifest_path,
        shape_input_source=shape_input_source,
        backlog_input_source=backlog_input_source,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
