#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


BACKLOG_OUTPUT_NAME = "panel_day_engine_subtype_truth_expansion_backlog_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_subtype_truth_expansion_backlog_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_subtype_truth_expansion_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_subtype_truth_expansion_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_subtype_truth_expansion_backlog_v1.json"

SUBTYPE_MAP_DEFAULT = "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_018_FAULT_SUBTYPE_HYPOTHESIS_MAP_V1.csv"
MORPHOLOGY_ATLAS_DEFAULT = "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_FAULT_MORPHOLOGY_ATLAS_V1.csv"
BR079_GAP_DEFAULT = (
    "/private/tmp/panel_day_engine_algorithm_evolution_map_br079_check/"
    "panel_day_engine_algorithm_evolution_gap_audit_v1.csv"
)
BR019_SHADOW_SUMMARY_DEFAULT = "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_019_FAULT_SUBTYPE_SHADOW_SUMMARY_V1.csv"
BR064_PACKET_DEFAULT = (
    "/private/tmp/fault_family_judgment_candidate_packet_check/"
    "panel_day_engine_fault_family_judgment_candidate_packet_v1.csv"
)
BR065_SHAPE_DEFAULT = (
    "/private/tmp/local_morphology_family_shape_review_check/"
    "panel_day_engine_local_morphology_family_shape_review_v1.csv"
)
BR069_CONFIRMATION_DEFAULT = (
    "/private/tmp/physical_confirmation_requirements_review_check/"
    "panel_day_engine_physical_confirmation_requirements_review_v1.csv"
)
BR072_COMMON_CAUSE_DEFAULT = (
    "/private/tmp/common_cause_exact_seed_search_check/"
    "panel_day_engine_common_cause_exact_seed_search_v1.csv"
)

BACKLOG_COLUMNS = [
    "owner_branch",
    "backlog_case_id",
    "family_key",
    "family_label_ko",
    "subtype_key",
    "subtype_label_ko",
    "recommended_shadow_action",
    "truth_collection_unit",
    "truth_target_role",
    "truth_priority",
    "current_shadow_panel_count",
    "current_candidate_pool_count",
    "current_local_shape_review_count",
    "current_physical_confirmation_gap_count",
    "current_common_cause_reservoir_count",
    "current_exact_truth_support_count",
    "minimum_positive_truth_needed",
    "minimum_negative_counterexamples_needed",
    "required_positive_evidence_axes",
    "required_negative_evidence_axes",
    "blocked_claim_until_closed",
    "recommended_next_artifact",
    "review_question_ko",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "family_key",
    "family_label_ko",
    "subtype_count",
    "p0_backlog_count",
    "p1_backlog_count",
    "current_shadow_panel_count_sum",
    "current_candidate_pool_family_count",
    "current_local_shape_review_family_count",
    "current_physical_confirmation_gap_family_count",
    "current_common_cause_reservoir_family_count",
    "operator_facing_change_allowed_sum",
    "engine_patch_allowed_sum",
    "threshold_patch_allowed_sum",
    "next_artifacts",
]

ACTION_COLUMNS = [
    "owner_branch",
    "sequence",
    "action_id",
    "action_family",
    "action",
    "input_backlog_filter",
    "purpose",
    "recommended_artifact",
    "success_boundary",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

FAMILY_TRACK_ALIASES = {
    "degradation_soiling_shadow": {"degradation_soiling_shadow"},
    "open_connection_partial": {"open_connection_partial", "open_connection_or_measurement_voltage_axis"},
    "diode_substring": {"diode_substring"},
    "measurement_feedback": {"measurement_feedback", "open_connection_or_measurement_voltage_axis"},
    "external_common_cause": {"external_common_cause"},
    "strict_anchor_sudden": {"strict_anchor_sudden"},
}

ATLAS_FAMILY_ALIASES = {
    "degradation_soiling_shadow": {"degradation_soiling_shadow"},
    "open_connection_partial": {"open_connection_partial", "intermittent_open_connection"},
    "diode_substring": {"diode_substring", "diode_substring_vdrop"},
    "measurement_feedback": {"measurement_feedback", "sensor_feedback_measurement"},
    "external_common_cause": {"external_common_cause"},
    "strict_anchor_sudden": {"strict_anchor_sudden"},
}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def numeric_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


def bool_int(value: bool) -> int:
    return 1 if value else 0


def resolve_path(repo_root: Path, path_value: str | Path) -> Path:
    path = Path(path_value)
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


def read_optional_csv(path: Path, required_cols: list[str], name: str) -> tuple[pd.DataFrame, bool]:
    if not path.exists():
        return pd.DataFrame(columns=required_cols), False
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")
    return df, True


def count_by_column(df: pd.DataFrame, column: str) -> dict[str, int]:
    if df.empty or column not in df.columns:
        return {}
    work = df.copy()
    work[column] = work[column].map(normalize_text)
    return {str(key): int(value) for key, value in work[column].value_counts(dropna=False).items() if str(key)}


def count_shadow_panels(shadow_summary: pd.DataFrame) -> dict[tuple[str, str], int]:
    if shadow_summary.empty:
        return {}
    result: dict[tuple[str, str], int] = {}
    for row in shadow_summary.to_dict(orient="records"):
        key = (
            normalize_text(row["fault_family_hypothesis_shadow_ko"]),
            normalize_text(row["fault_subtype_hypothesis_shadow_ko"]),
        )
        result[key] = result.get(key, 0) + numeric_int(row["panel_count"])
    return result


def family_candidate_count(family_key: str, packet_counts: dict[str, int]) -> int:
    aliases = FAMILY_TRACK_ALIASES.get(family_key, {family_key})
    return sum(packet_counts.get(alias, 0) for alias in aliases)


def local_shape_count(family_key: str, shape_counts: dict[str, int]) -> int:
    aliases = FAMILY_TRACK_ALIASES.get(family_key, {family_key})
    return sum(shape_counts.get(alias, 0) for alias in aliases)


def physical_gap_count(family_key: str, confirmation_df: pd.DataFrame) -> int:
    if confirmation_df.empty:
        return 0
    if family_key not in {"open_connection_partial", "measurement_feedback"}:
        return 0
    return int(confirmation_df["confirmation_bucket"].map(normalize_text).eq("raw_supported_confirmation_gap_hold").sum())


def common_cause_count(family_key: str, common_df: pd.DataFrame) -> int:
    if common_df.empty or family_key != "external_common_cause":
        return 0
    return int(
        common_df["candidate_reservoir_flag"].fillna(0).map(numeric_int).sum()
        + common_df["structural_blocker_flag"].fillna(0).map(numeric_int).sum()
    )


def profile_for_subtype(family_key: str, subtype_key: str, action: str) -> dict[str, str | int]:
    profile = {
        "truth_collection_unit": "subtype_case",
        "truth_target_role": "positive_and_negative_truth",
        "truth_priority": "P1",
        "minimum_positive_truth_needed": 5,
        "minimum_negative_counterexamples_needed": 5,
        "required_positive_evidence_axes": "exact panel id; event window; family/subtype decision; at least two supporting axes",
        "required_negative_evidence_axes": "same-feature non-fault or different-family counterexample; site/common-cause exclusion",
        "blocked_claim_until_closed": "operator-facing subtype label or performance claim",
        "recommended_next_artifact": "panel_day_engine_subtype_truth_expansion_backlog_v1",
        "review_question_ko": "이 subtype을 실제 고장 세부형으로 말할 수 있는 exact truth와 counterexample가 있는가?",
    }

    if family_key == "degradation_soiling_shadow":
        profile.update(
            {
                "truth_collection_unit": "episode_chain",
                "truth_priority": "P0" if subtype_key in {"progressive_soiling_or_degradation", "long_gap_one_day_stress"} else "P1",
                "required_positive_evidence_axes": "duration/continuity; recurrence or incomplete recovery; common-cause exclusion; strict-trigger distance",
                "required_negative_evidence_axes": "one-day episode; long normal gap; site/root/subgroup simultaneity; displaced onset",
                "blocked_claim_until_closed": "precursor onset or degradation backdating rule",
                "recommended_next_artifact": "panel_day_engine_episode_truth_map_v1",
                "review_question_ko": "반복/누적 저하인가, 하루짜리 episode 또는 long-gap backdating인가?",
            }
        )
    elif family_key == "open_connection_partial":
        profile.update(
            {
                "truth_collection_unit": "exact_panel_fault_case",
                "truth_priority": "P0",
                "required_positive_evidence_axes": "recurrence; VI shape similarity; exact-panel inspection or maintenance; strict-trigger proximity",
                "required_negative_evidence_axes": "site-wide drop; measurement artifact; one-off recovery; no physical confirmation",
                "blocked_claim_until_closed": "open/partial-open subtype promotion or voltage-axis threshold loosening",
                "recommended_next_artifact": "panel_day_engine_open_connection_truth_packet_v1",
                "review_question_ko": "간헐/부분개방 신호가 실제 패널/접속부 문제로 확인되는가?",
            }
        )
    elif family_key == "diode_substring":
        profile.update(
            {
                "truth_collection_unit": "exact_panel_vi_shape_case",
                "truth_priority": "P0",
                "required_positive_evidence_axes": "V/I ratio morphology; repeated daytime curve shape; electrical grouping; inspection or module-level evidence",
                "required_negative_evidence_axes": "sensor scale drift; site-wide irradiance/weather; transient one-day curve",
                "blocked_claim_until_closed": "diode/sub-string subtype label or threshold claim",
                "recommended_next_artifact": "panel_day_engine_diode_substring_truth_packet_v1",
                "review_question_ko": "V/I morphology가 다이오드·서브스트링 계열로 반복 확인되는가?",
            }
        )
    elif family_key == "measurement_feedback":
        profile.update(
            {
                "truth_collection_unit": "measurement_qa_case",
                "truth_target_role": "non_panel_fault_truth",
                "truth_priority": "P1",
                "minimum_positive_truth_needed": 5,
                "minimum_negative_counterexamples_needed": 3,
                "required_positive_evidence_axes": "sensor/channel/timestamp evidence; impossible value or abrupt recovery; site/root consistency",
                "required_negative_evidence_axes": "exact-panel physical fault; persistent VI morphology; inspection-confirmed panel fault",
                "blocked_claim_until_closed": "AE or V/I anomaly as root-cause classifier",
                "recommended_next_artifact": "panel_day_engine_measurement_feedback_truth_packet_v1",
                "review_question_ko": "패널 고장이 아니라 계측/피드백/채널 문제로 분리할 근거가 있는가?",
            }
        )
    elif family_key == "external_common_cause":
        profile.update(
            {
                "truth_collection_unit": "site_or_group_event",
                "truth_target_role": "common_cause_bridge_truth",
                "truth_priority": "P0",
                "minimum_positive_truth_needed": 3,
                "minimum_negative_counterexamples_needed": 5,
                "required_positive_evidence_axes": "official/current bridge; same-day report-lane entry; group/site synchrony; direct raw support",
                "required_negative_evidence_axes": "panel-local isolated fault; no report-lane entry; date-displaced raw-only trace",
                "blocked_claim_until_closed": "common-cause semantic loosening or individual precursor promotion",
                "recommended_next_artifact": "common_cause_bridge_exact_closure_packet_v1",
                "review_question_ko": "공통원인 후보가 official/current 같은 날 bridge까지 닫히는가?",
            }
        )
    elif family_key == "strict_anchor_sudden":
        profile.update(
            {
                "truth_collection_unit": "abrupt_fault_case",
                "truth_target_role": "no_precursor_or_sudden_truth",
                "truth_priority": "P0",
                "minimum_positive_truth_needed": 5,
                "minimum_negative_counterexamples_needed": 5,
                "required_positive_evidence_axes": "strict-trigger anchor; no durable pre-event episode; first hard fault proximity; reviewed prior normal period",
                "required_negative_evidence_axes": "validated prior recurring precursor; common-cause displacement; data gap",
                "blocked_claim_until_closed": "precursor-vs-abrupt conversion rule",
                "recommended_next_artifact": "panel_day_engine_episode_truth_map_v1",
                "review_question_ko": "전조가 없던 급작 고장인지, 우리가 전조를 너무 보수적으로 누락한 것인지?",
            }
        )

    if action in {"block_individual_precursor", "block_precursor_backdating", "no_precursor_promotion"}:
        profile["truth_priority"] = "P0"
    return profile


def build_backlog(
    owner_branch: str,
    subtype_map: pd.DataFrame,
    shadow_summary: pd.DataFrame,
    packet_df: pd.DataFrame,
    shape_df: pd.DataFrame,
    confirmation_df: pd.DataFrame,
    common_df: pd.DataFrame,
) -> pd.DataFrame:
    shadow_counts = count_shadow_panels(shadow_summary)
    packet_counts = count_by_column(packet_df, "candidate_family_track")
    shape_counts = count_by_column(shape_df, "candidate_family_track")

    rows: list[dict[str, object]] = []
    for idx, row in enumerate(subtype_map.to_dict(orient="records"), start=1):
        family_key = normalize_text(row["family_key"])
        family_label = normalize_text(row["family_label_ko"])
        subtype_key = normalize_text(row["subtype_key"])
        subtype_label = normalize_text(row["subtype_label_ko"])
        action = normalize_text(row["recommended_shadow_action"])
        profile = profile_for_subtype(family_key, subtype_key, action)
        candidate_count = family_candidate_count(family_key, packet_counts)
        shape_count = local_shape_count(family_key, shape_counts)
        phys_count = physical_gap_count(family_key, confirmation_df)
        common_count = common_cause_count(family_key, common_df)
        shadow_count = shadow_counts.get((family_label, subtype_label), 0)
        notes = [
            f"primary_signature={normalize_text(row['primary_signature_ko'])}",
            f"minimum_shadow_evidence={normalize_text(row['minimum_evidence_shadow_ko'])}",
            "existing candidates are context/backlog material, not exact truth",
        ]
        rows.append(
            {
                "owner_branch": owner_branch,
                "backlog_case_id": f"BR080-{idx:03d}",
                "family_key": family_key,
                "family_label_ko": family_label,
                "subtype_key": subtype_key,
                "subtype_label_ko": subtype_label,
                "recommended_shadow_action": action,
                "truth_collection_unit": profile["truth_collection_unit"],
                "truth_target_role": profile["truth_target_role"],
                "truth_priority": profile["truth_priority"],
                "current_shadow_panel_count": shadow_count,
                "current_candidate_pool_count": candidate_count,
                "current_local_shape_review_count": shape_count,
                "current_physical_confirmation_gap_count": phys_count,
                "current_common_cause_reservoir_count": common_count,
                "current_exact_truth_support_count": 0,
                "minimum_positive_truth_needed": profile["minimum_positive_truth_needed"],
                "minimum_negative_counterexamples_needed": profile["minimum_negative_counterexamples_needed"],
                "required_positive_evidence_axes": profile["required_positive_evidence_axes"],
                "required_negative_evidence_axes": profile["required_negative_evidence_axes"],
                "blocked_claim_until_closed": profile["blocked_claim_until_closed"],
                "recommended_next_artifact": profile["recommended_next_artifact"],
                "review_question_ko": profile["review_question_ko"],
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "notes": " | ".join(notes),
            }
        )
    return pd.DataFrame(rows, columns=BACKLOG_COLUMNS)


def build_summary(owner_branch: str, backlog_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (family_key, family_label), group in backlog_df.groupby(["family_key", "family_label_ko"], sort=False):
        rows.append(
            {
                "owner_branch": owner_branch,
                "family_key": family_key,
                "family_label_ko": family_label,
                "subtype_count": int(len(group)),
                "p0_backlog_count": int(group["truth_priority"].eq("P0").sum()),
                "p1_backlog_count": int(group["truth_priority"].eq("P1").sum()),
                "current_shadow_panel_count_sum": int(group["current_shadow_panel_count"].sum()),
                "current_candidate_pool_family_count": int(group["current_candidate_pool_count"].max()),
                "current_local_shape_review_family_count": int(group["current_local_shape_review_count"].max()),
                "current_physical_confirmation_gap_family_count": int(group["current_physical_confirmation_gap_count"].max()),
                "current_common_cause_reservoir_family_count": int(group["current_common_cause_reservoir_count"].max()),
                "operator_facing_change_allowed_sum": int(group["operator_facing_change_allowed"].sum()),
                "engine_patch_allowed_sum": int(group["engine_patch_allowed"].sum()),
                "threshold_patch_allowed_sum": int(group["threshold_patch_allowed"].sum()),
                "next_artifacts": "; ".join(sorted(set(group["recommended_next_artifact"].map(normalize_text)))),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def build_action_queue(owner_branch: str, backlog_df: pd.DataFrame) -> pd.DataFrame:
    specs = [
        {
            "action_id": "ACT-001",
            "action_family": "subtype_truth",
            "action": "collect exact subtype truth and counterexamples",
            "input_backlog_filter": "truth_priority == P0 and truth_target_role in positive_and_negative_truth",
            "purpose": "support future subtype labels and performance claims with actual truth rows",
            "recommended_artifact": "panel_day_engine_subtype_truth_review_packet_v1",
            "success_boundary": "each target subtype has exact-panel positive truth and reviewed negative counterexamples",
            "notes": "Start with open/diode/degradation/strict-sudden rows before threshold replay.",
        },
        {
            "action_id": "ACT-002",
            "action_family": "episode_truth",
            "action": "map precursor episodes with start/end and strict-trigger distance",
            "input_backlog_filter": "recommended_next_artifact == panel_day_engine_episode_truth_map_v1",
            "purpose": "separate durable precursor, one-day episode, long-gap backdating, and true sudden faults",
            "recommended_artifact": "panel_day_engine_episode_truth_map_v1",
            "success_boundary": "episode rows include duration, recurrence, recovery, site/common-cause overlap, and outcome",
            "notes": "This is the key bridge from daily flags to reliable onset semantics.",
        },
        {
            "action_id": "ACT-003",
            "action_family": "physical_confirmation",
            "action": "attach exact-panel physical confirmation evidence",
            "input_backlog_filter": "current_physical_confirmation_gap_count > 0",
            "purpose": "avoid treating raw waveform support as independent physical proof",
            "recommended_artifact": "rerun BR-069/BR-070 after exact-panel evidence attachment",
            "success_boundary": "direct measurement or maintenance/inspection axes close for the exact panel/event",
            "notes": "Blocks voltage-axis threshold loosening until closed.",
        },
        {
            "action_id": "ACT-004",
            "action_family": "common_cause_bridge",
            "action": "close official/current bridge for common-cause candidates",
            "input_backlog_filter": "family_key == external_common_cause",
            "purpose": "keep raw-only common-cause reservoirs from becoming panel-local official/current evidence",
            "recommended_artifact": "common_cause_bridge_exact_closure_packet_v1",
            "success_boundary": "same-day official/current bridge or scoped structural blocker target is proven",
            "notes": "BR-076 3-gate runbook remains mandatory before semantic loosening.",
        },
        {
            "action_id": "ACT-005",
            "action_family": "threshold_replay",
            "action": "run subtype-conditioned threshold replay only after truth rows exist",
            "input_backlog_filter": "current_exact_truth_support_count >= minimum_positive_truth_needed",
            "purpose": "move from hand thresholds to evidence-backed threshold candidates",
            "recommended_artifact": "panel_day_engine_subtype_threshold_replay_v1",
            "success_boundary": "candidate thresholds have result delta, false-positive pressure, and holdout impact",
            "notes": "Replay first; production patch later.",
        },
    ]
    rows: list[dict[str, object]] = []
    for idx, spec in enumerate(specs, start=1):
        rows.append(
            {
                "owner_branch": owner_branch,
                "sequence": idx,
                **spec,
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
            }
        )
    return pd.DataFrame(rows, columns=ACTION_COLUMNS)


def write_note(
    output_dir: Path,
    owner_branch: str,
    backlog_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    action_df: pd.DataFrame,
    input_presence: dict[str, bool],
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> None:
    total_operator = int(backlog_df["operator_facing_change_allowed"].sum() + action_df["operator_facing_change_allowed"].sum())
    total_engine = int(backlog_df["engine_patch_allowed"].sum() + action_df["engine_patch_allowed"].sum())
    total_threshold = int(backlog_df["threshold_patch_allowed"].sum() + action_df["threshold_patch_allowed"].sum())
    missing_inputs = [name for name, present in input_presence.items() if not present]
    note = f"""# Panel Day Engine Subtype Truth Expansion Backlog V1

## Purpose
- Convert the BR-018 subtype hypothesis map into a concrete truth/evidence backlog.
- Keep subtype labels as review hypotheses until exact truth rows and counterexamples exist.
- Preserve BR-079's boundary: this is evidence planning, not an engine or threshold patch.

## Outputs
- `{output_dir / BACKLOG_OUTPUT_NAME}`
- `{output_dir / SUMMARY_OUTPUT_NAME}`
- `{output_dir / ACTION_OUTPUT_NAME}`
- `{output_dir / JSON_OUTPUT_NAME}`

## Result
- subtype backlog rows: `{len(backlog_df)}`
- family summaries: `{len(summary_df)}`
- P0 subtype backlog rows: `{int(backlog_df["truth_priority"].eq("P0").sum())}`
- ordered actions: `{len(action_df)}`
- operator-facing change allowed sum: `{total_operator}`
- engine patch allowed sum: `{total_engine}`
- threshold patch allowed sum: `{total_threshold}`
- missing optional inputs: `{len(missing_inputs)}`
- evidence input manifest: `{input_manifest_path if input_manifest_path else 'not provided'}`

## Reading
- Current subtype artifacts are shadow/review context only.
- `current_candidate_pool_count` and related counts are not exact truth support.
- `current_exact_truth_support_count` is intentionally `0` for every subtype row until exact-panel truth is attached.
- The next safe implementation is an episode truth map and exact subtype review packets, not threshold tuning.

## Missing Optional Inputs
{chr(10).join(f"- `{name}`" for name in missing_inputs) if missing_inputs else "- none"}

## Input Resolution Sources
{chr(10).join(f"- `{key}`: `{value}`" for key, value in sorted((input_resolution_sources or {}).items())) if input_resolution_sources else "- no manifest-wrapped inputs"}

## Repro Command
```bash
python3 research/prognostics/build_panel_day_engine_subtype_truth_expansion_backlog_v1.py --repo-root "$(pwd)" --output-dir {output_dir}
```
"""
    (output_dir / NOTE_OUTPUT_NAME).write_text(note, encoding="utf-8")


def build_outputs(
    repo_root: Path,
    output_dir: Path,
    owner_branch: str,
    subtype_map_path: Path,
    morphology_atlas_path: Path,
    br079_gap_path: Path,
    shadow_summary_path: Path,
    candidate_packet_path: Path,
    shape_review_path: Path,
    physical_confirmation_path: Path,
    common_cause_search_path: Path,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)

    subtype_map = read_required_csv(
        subtype_map_path,
        [
            "family_key",
            "family_label_ko",
            "subtype_key",
            "subtype_label_ko",
            "primary_signature_ko",
            "minimum_evidence_shadow_ko",
            "recommended_shadow_action",
        ],
        "subtype_map",
    )
    morphology_atlas, atlas_present = read_optional_csv(
        morphology_atlas_path,
        ["family_key", "family_label_ko"],
        "morphology_atlas",
    )
    br079_gap, gap_present = read_optional_csv(
        br079_gap_path,
        ["gap_id", "gap_family", "priority", "recommended_artifact"],
        "br079_gap_audit",
    )
    shadow_summary, shadow_present = read_optional_csv(
        shadow_summary_path,
        [
            "fault_family_hypothesis_shadow_ko",
            "fault_subtype_hypothesis_shadow_ko",
            "subtype_confidence_shadow",
            "panel_count",
        ],
        "br019_shadow_summary",
    )
    packet_df, packet_present = read_optional_csv(
        candidate_packet_path,
        ["candidate_family_track", "candidate_family_label_ko", "operator_promotion_allowed_flag", "engine_patch_candidate_flag"],
        "br064_candidate_packet",
    )
    shape_df, shape_present = read_optional_csv(
        shape_review_path,
        ["candidate_family_track", "family_shape_judgment_bucket", "operator_promotion_allowed_flag", "engine_patch_candidate_flag"],
        "br065_shape_review",
    )
    confirmation_df, confirmation_present = read_optional_csv(
        physical_confirmation_path,
        ["confirmation_bucket", "operator_promotion_allowed_flag", "engine_patch_candidate_flag", "threshold_patch_allowed_flag"],
        "br069_physical_confirmation",
    )
    common_df, common_present = read_optional_csv(
        common_cause_search_path,
        [
            "candidate_reservoir_flag",
            "structural_blocker_flag",
            "operator_promotion_allowed_flag",
            "engine_patch_candidate_flag",
            "threshold_patch_allowed_flag",
        ],
        "br072_common_cause_search",
    )

    known_families = set(subtype_map["family_key"].map(normalize_text))
    if atlas_present:
        atlas_families = set(morphology_atlas["family_key"].map(normalize_text))
        missing_from_atlas = sorted(
            family
            for family in known_families
            if not (ATLAS_FAMILY_ALIASES.get(family, {family}) & atlas_families)
        )
    else:
        missing_from_atlas = sorted(known_families)

    backlog_df = build_backlog(
        owner_branch=owner_branch,
        subtype_map=subtype_map,
        shadow_summary=shadow_summary,
        packet_df=packet_df,
        shape_df=shape_df,
        confirmation_df=confirmation_df,
        common_df=common_df,
    )
    summary_df = build_summary(owner_branch, backlog_df)
    action_df = build_action_queue(owner_branch, backlog_df)

    backlog_df.to_csv(output_dir / BACKLOG_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")

    input_presence = {
        "morphology_atlas": atlas_present,
        "br079_gap_audit": gap_present,
        "br019_shadow_summary": shadow_present,
        "br064_candidate_packet": packet_present,
        "br065_shape_review": shape_present,
        "br069_physical_confirmation": confirmation_present,
        "br072_common_cause_search": common_present,
    }
    input_resolution_sources = input_resolution_sources or {}
    write_note(
        output_dir,
        owner_branch,
        backlog_df,
        summary_df,
        action_df,
        input_presence,
        input_manifest_path,
        input_resolution_sources,
    )

    payload = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "subtype_backlog_rows": int(len(backlog_df)),
        "family_summary_rows": int(len(summary_df)),
        "p0_subtype_backlog_rows": int(backlog_df["truth_priority"].eq("P0").sum()),
        "current_exact_truth_support_sum": int(backlog_df["current_exact_truth_support_count"].sum()),
        "operator_facing_change_allowed_sum": int(
            backlog_df["operator_facing_change_allowed"].sum() + action_df["operator_facing_change_allowed"].sum()
        ),
        "engine_patch_allowed_sum": int(backlog_df["engine_patch_allowed"].sum() + action_df["engine_patch_allowed"].sum()),
        "threshold_patch_allowed_sum": int(
            backlog_df["threshold_patch_allowed"].sum() + action_df["threshold_patch_allowed"].sum()
        ),
        "input_presence": input_presence,
        "input_manifest": str(input_manifest_path) if input_manifest_path else "",
        "input_resolution_sources": input_resolution_sources,
        "br079_gap_input_source": input_resolution_sources.get("br079_gap_input", ""),
        "candidate_packet_input_source": input_resolution_sources.get("candidate_packet_input", ""),
        "shape_review_input_source": input_resolution_sources.get("shape_review_input", ""),
        "physical_confirmation_input_source": input_resolution_sources.get("physical_confirmation_input", ""),
        "common_cause_search_input_source": input_resolution_sources.get("common_cause_search_input", ""),
        "missing_optional_input_count": int(sum(1 for present in input_presence.values() if not present)),
        "missing_subtype_families_from_morphology_atlas": missing_from_atlas,
        "br079_gap_audit_recommended_artifacts": sorted(set(br079_gap["recommended_artifact"].map(normalize_text))) if gap_present else [],
        "recommended_next_branch": "panel_day_engine_episode_truth_map_v1",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "backlog": str(output_dir / BACKLOG_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    (output_dir / JSON_OUTPUT_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check"),
    )
    parser.add_argument("--owner-branch", default="BR-20260425-080")
    parser.add_argument("--subtype-map", default=SUBTYPE_MAP_DEFAULT)
    parser.add_argument("--morphology-atlas", default=MORPHOLOGY_ATLAS_DEFAULT)
    parser.add_argument("--input-manifest", default=None)
    parser.add_argument("--br079-gap-input", default=BR079_GAP_DEFAULT)
    parser.add_argument("--shadow-summary-input", default=BR019_SHADOW_SUMMARY_DEFAULT)
    parser.add_argument("--candidate-packet-input", default=BR064_PACKET_DEFAULT)
    parser.add_argument("--shape-review-input", default=BR065_SHAPE_DEFAULT)
    parser.add_argument("--physical-confirmation-input", default=BR069_CONFIRMATION_DEFAULT)
    parser.add_argument("--common-cause-search-input", default=BR072_COMMON_CAUSE_DEFAULT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    input_manifest_path, input_manifest = load_input_manifest(repo_root, args.input_manifest)
    argv = sys.argv[1:]
    explicit_flags = {
        flag
        for flag in [
            "--br079-gap-input",
            "--candidate-packet-input",
            "--shape-review-input",
            "--physical-confirmation-input",
            "--common-cause-search-input",
        ]
        if cli_flag_provided(flag, argv)
    }
    br079_gap_path, br079_gap_source = resolve_chain_input(
        repo_root,
        args.br079_gap_input,
        BR079_GAP_DEFAULT,
        input_manifest,
        "br079_gap_input",
        "--br079-gap-input",
        explicit_flags,
    )
    candidate_packet_path, candidate_packet_source = resolve_chain_input(
        repo_root,
        args.candidate_packet_input,
        BR064_PACKET_DEFAULT,
        input_manifest,
        "candidate_packet_input",
        "--candidate-packet-input",
        explicit_flags,
    )
    shape_review_path, shape_review_source = resolve_chain_input(
        repo_root,
        args.shape_review_input,
        BR065_SHAPE_DEFAULT,
        input_manifest,
        "shape_review_input",
        "--shape-review-input",
        explicit_flags,
    )
    physical_confirmation_path, physical_confirmation_source = resolve_chain_input(
        repo_root,
        args.physical_confirmation_input,
        BR069_CONFIRMATION_DEFAULT,
        input_manifest,
        "physical_confirmation_input",
        "--physical-confirmation-input",
        explicit_flags,
    )
    common_cause_search_path, common_cause_search_source = resolve_chain_input(
        repo_root,
        args.common_cause_search_input,
        BR072_COMMON_CAUSE_DEFAULT,
        input_manifest,
        "common_cause_search_input",
        "--common-cause-search-input",
        explicit_flags,
    )
    input_resolution_sources = {
        "br079_gap_input": br079_gap_source,
        "candidate_packet_input": candidate_packet_source,
        "shape_review_input": shape_review_source,
        "physical_confirmation_input": physical_confirmation_source,
        "common_cause_search_input": common_cause_search_source,
    }
    payload = build_outputs(
        repo_root=repo_root,
        output_dir=args.output_dir,
        owner_branch=args.owner_branch,
        subtype_map_path=resolve_path(repo_root, args.subtype_map),
        morphology_atlas_path=resolve_path(repo_root, args.morphology_atlas),
        br079_gap_path=br079_gap_path,
        shadow_summary_path=resolve_path(repo_root, args.shadow_summary_input),
        candidate_packet_path=candidate_packet_path,
        shape_review_path=shape_review_path,
        physical_confirmation_path=physical_confirmation_path,
        common_cause_search_path=common_cause_search_path,
        input_manifest_path=input_manifest_path,
        input_resolution_sources=input_resolution_sources,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
