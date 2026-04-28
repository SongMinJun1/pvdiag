#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import pandas as pd


DETAIL_OUTPUT_NAME = "panel_day_engine_latest_evidence_handoff_manifest_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_latest_evidence_handoff_manifest_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_latest_evidence_handoff_manifest_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_latest_evidence_handoff_manifest_v1.json"

BR064_REPRO = (
    "python3 research/prognostics/build_panel_day_engine_fault_family_judgment_candidate_packet_v1.py "
    "--cross-axis-input /private/tmp/cross_axis_manifest_sync_review_check/panel_day_engine_cross_axis_manifest_sync_review_v1.csv "
    "--pressure-input /private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv "
    "--threshold-input docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_THRESHOLD_CANDIDATE_V1.csv "
    "--subtype-input docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_018_FAULT_SUBTYPE_HYPOTHESIS_MAP_V1.csv "
    "--output-dir /private/tmp/fault_family_judgment_candidate_packet_check"
)
BR065_REPRO = (
    "python3 research/prognostics/build_panel_day_engine_local_morphology_family_shape_review_v1.py "
    "--packet-input /private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv "
    "--data-root /Users/b9gc/pvdiag/data "
    "--output-dir /private/tmp/local_morphology_family_shape_review_check"
)
BR067_REPRO = (
    "python3 research/prognostics/build_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py "
    "--shape-input /private/tmp/local_morphology_family_shape_review_check/panel_day_engine_local_morphology_family_shape_review_v1.csv "
    "--data-root /Users/b9gc/pvdiag/data "
    "--output-dir /private/tmp/voltage_dominant_physical_vs_artifact_review_check"
)
BR068_REPRO = (
    "python3 research/prognostics/build_panel_day_engine_raw_waveform_physical_support_review_v1.py "
    "--review-input /private/tmp/voltage_dominant_physical_vs_artifact_review_check/panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.csv "
    "--data-root /Users/b9gc/pvdiag/data "
    "--output-dir /private/tmp/raw_waveform_physical_support_review_check"
)
BR069_REPRO = (
    "python3 research/prognostics/build_panel_day_engine_physical_confirmation_requirements_review_v1.py "
    "--raw-review-input /private/tmp/raw_waveform_physical_support_review_check/panel_day_engine_raw_waveform_physical_support_review_v1.csv "
    "--manual-evidence-input docs/internal/manual_field_evidence_latest.csv "
    "--output-dir /private/tmp/physical_confirmation_requirements_review_check"
)
BR070_REPRO = (
    "python3 research/prognostics/build_panel_day_engine_physical_evidence_request_packet_v1.py "
    "--confirmation-input /private/tmp/physical_confirmation_requirements_review_check/panel_day_engine_physical_confirmation_requirements_review_v1.csv "
    "--checklist-input /private/tmp/physical_confirmation_requirements_review_check/panel_day_engine_physical_confirmation_requirements_checklist_v1.csv "
    "--output-dir /private/tmp/physical_evidence_request_packet_check"
)
BR071_REPRO = (
    "python3 research/prognostics/build_panel_day_engine_strong_common_cause_blocker_regression_packet_v1.py "
    "--judgment-input /private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv "
    "--output-dir /private/tmp/strong_common_cause_blocker_regression_packet_check"
)
BR072_REPRO = (
    "python3 research/prognostics/build_panel_day_engine_common_cause_exact_seed_search_v1.py "
    "--judgment-input /private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv "
    "--synchrony-input /private/tmp/common_cause_synchrony_axis_sidecar_check/panel_day_engine_common_cause_synchrony_axis_v1.csv "
    "--current-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_current_v1.csv "
    "--precursor-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_precursor_report_v1.csv "
    "--rawonly-signal-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_raw_only_fault_signal_report_v1.csv "
    "--data-root /Users/b9gc/pvdiag/data "
    "--output-dir /private/tmp/common_cause_exact_seed_search_check"
)
BR073_REPRO = (
    "python3 research/prognostics/build_panel_day_engine_common_cause_structural_blocker_review_v1.py "
    "--exact-seed-input /private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv "
    "--output-dir /private/tmp/common_cause_structural_blocker_review_check"
)
BR074_REPRO = (
    "python3 research/prognostics/build_panel_day_engine_common_cause_manual_trace_review_v1.py "
    "--blocker-input /private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_v1.csv "
    "--current-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_current_v1.csv "
    "--precursor-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_precursor_report_v1.csv "
    "--rawonly-signal-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_raw_only_fault_signal_report_v1.csv "
    "--data-root /Users/b9gc/pvdiag/data "
    "--output-dir /private/tmp/common_cause_manual_trace_review_check"
)
BR075_REPRO = (
    "python3 research/prognostics/check_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py "
    "--strong-blocker-input /private/tmp/strong_common_cause_blocker_regression_packet_check/panel_day_engine_strong_common_cause_blocker_regression_packet_v1.csv "
    "--exact-search-input /private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv "
    "--structural-input /private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_v1.csv "
    "--trace-input /private/tmp/common_cause_manual_trace_review_check/panel_day_engine_common_cause_manual_trace_review_v1.csv "
    "--output-dir /private/tmp/common_cause_semantic_prepatch_gate_check"
)
BR076_REPRO = (
    "python3 research/prognostics/check_panel_day_engine_algorithm_prepatch_runbook_v1.py "
    "--repo-root /private/tmp/pvdiag_postmerge_j "
    "--packet-input /private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv "
    "--common-cause-strong-blocker-input /private/tmp/strong_common_cause_blocker_regression_packet_check/panel_day_engine_strong_common_cause_blocker_regression_packet_v1.csv "
    "--common-cause-exact-search-input /private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv "
    "--common-cause-structural-input /private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_v1.csv "
    "--common-cause-trace-input /private/tmp/common_cause_manual_trace_review_check/panel_day_engine_common_cause_manual_trace_review_v1.csv "
    "--output-dir /private/tmp/panel_engine_algorithm_prepatch_runbook_br076_check"
)

DETAIL_COLUMNS = [
    "branch_id",
    "branch_title",
    "evidence_layer",
    "judgment_role",
    "handoff_state",
    "primary_doc_path",
    "primary_doc_exists",
    "primary_artifact_path",
    "primary_artifact_kind",
    "primary_artifact_exists",
    "artifact_location_type",
    "repro_command",
    "repro_required_if_missing",
    "key_result",
    "next_action",
    "operator_promotion_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "stable_contract_change_allowed",
    "release_regeneration_allowed",
    "notes",
]

SUMMARY_COLUMNS = [
    "evidence_layer",
    "handoff_state",
    "branches",
    "repo_docs_present",
    "primary_artifacts_present",
    "temp_artifacts_missing",
    "operator_promotion_allowed_sum",
    "engine_patch_allowed_sum",
    "threshold_patch_allowed_sum",
    "next_actions",
]

BRANCH_SPECS = [
    {
        "branch_id": "BR-20260424-064",
        "branch_title": "fault_family_judgment_candidate_packet",
        "evidence_layer": "fault_family_candidate_pool",
        "judgment_role": "review_bucket_split",
        "handoff_state": "indexed_for_review",
        "primary_doc_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_064_FAULT_FAMILY_JUDGMENT_CANDIDATE_PACKET_V1.md",
        "primary_artifact_path": "/private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv",
        "primary_artifact_kind": "detail_csv",
        "repro_command": BR064_REPRO,
        "key_result": "209 rows split: common-cause hold/block 176, regression pressure 11, local morphology 10, weak hold 12; promotion/engine patch 0",
        "next_action": "start family-shape review from local morphology rows only",
    },
    {
        "branch_id": "BR-20260424-065",
        "branch_title": "local_morphology_family_shape_review",
        "evidence_layer": "local_morphology_shape",
        "judgment_role": "threshold_blocker_split",
        "handoff_state": "indexed_for_review",
        "primary_doc_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_065_LOCAL_MORPHOLOGY_FAMILY_SHAPE_REVIEW_V1.md",
        "primary_artifact_path": "/private/tmp/local_morphology_family_shape_review_check/panel_day_engine_local_morphology_family_shape_review_v1.csv",
        "primary_artifact_kind": "detail_csv",
        "repro_command": BR065_REPRO,
        "key_result": "10 rows split into 8 recovery-only holds and 2 voltage-dominant hard-signal review rows; promotion/engine patch 0",
        "next_action": "review the 2 voltage-dominant rows for physical-vs-artifact evidence",
    },
    {
        "branch_id": "BR-20260424-066",
        "branch_title": "evidence_handoff_index",
        "evidence_layer": "handoff_navigation",
        "judgment_role": "handoff_index",
        "handoff_state": "superseded_by_br078_refresh",
        "primary_doc_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_066_EVIDENCE_HANDOFF_INDEX_V1.md",
        "primary_artifact_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_066_EVIDENCE_HANDOFF_INDEX_V1.md",
        "primary_artifact_kind": "repo_doc",
        "repro_command": "python3 -m py_compile pv_ae/panel_day_engine.py",
        "key_result": "handoff_ready_with_index after BR-065, but stale after BR-067 through BR-076",
        "next_action": "use BR-078 latest handoff manifest instead of BR-066 as current map",
    },
    {
        "branch_id": "BR-20260424-067",
        "branch_title": "voltage_dominant_physical_vs_artifact_review",
        "evidence_layer": "physical_evidence_voltage",
        "judgment_role": "physical_leaning_review",
        "handoff_state": "indexed_for_review",
        "primary_doc_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_067_VOLTAGE_DOMINANT_PHYSICAL_VS_ARTIFACT_REVIEW_V1.md",
        "primary_artifact_path": "/private/tmp/voltage_dominant_physical_vs_artifact_review_check/panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.csv",
        "primary_artifact_kind": "detail_csv",
        "repro_command": BR067_REPRO,
        "key_result": "2 rows physical-leaning voltage-axis review, artifact/reference hold 0; no confirmed family or engine patch",
        "next_action": "add raw waveform support, then require independent confirmation",
    },
    {
        "branch_id": "BR-20260424-068",
        "branch_title": "raw_waveform_physical_support_review",
        "evidence_layer": "physical_evidence_voltage",
        "judgment_role": "raw_waveform_support",
        "handoff_state": "indexed_for_review",
        "primary_doc_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_068_RAW_WAVEFORM_PHYSICAL_SUPPORT_REVIEW_V1.md",
        "primary_artifact_path": "/private/tmp/raw_waveform_physical_support_review_check/panel_day_engine_raw_waveform_physical_support_review_v1.csv",
        "primary_artifact_kind": "detail_csv",
        "repro_command": BR068_REPRO,
        "key_result": "2 rows have low-voltage/current-preserved raw timestamp support; still not independent physical confirmation",
        "next_action": "define and run physical-confirmation checklist before thresholding",
    },
    {
        "branch_id": "BR-20260424-069",
        "branch_title": "physical_confirmation_requirements_review",
        "evidence_layer": "physical_evidence_voltage",
        "judgment_role": "independent_confirmation_gap",
        "handoff_state": "blocked_pending_evidence",
        "primary_doc_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_069_PHYSICAL_CONFIRMATION_REQUIREMENTS_REVIEW_V1.md",
        "primary_artifact_path": "/private/tmp/physical_confirmation_requirements_review_check/panel_day_engine_physical_confirmation_requirements_review_v1.csv",
        "primary_artifact_kind": "detail_csv",
        "repro_command": BR069_REPRO,
        "key_result": "2 rows remain raw_supported_confirmation_gap_hold; required independent axes met 0/2 for both rows",
        "next_action": "attach exact-panel physical measurement and maintenance/inspection evidence",
    },
    {
        "branch_id": "BR-20260424-070",
        "branch_title": "physical_evidence_request_packet",
        "evidence_layer": "physical_evidence_voltage",
        "judgment_role": "evidence_acquisition_request",
        "handoff_state": "blocked_pending_evidence",
        "primary_doc_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_070_PHYSICAL_EVIDENCE_REQUEST_PACKET_V1.md",
        "primary_artifact_path": "/private/tmp/physical_evidence_request_packet_check/panel_day_engine_physical_evidence_request_packet_v1.csv",
        "primary_artifact_kind": "detail_csv",
        "repro_command": BR070_REPRO,
        "key_result": "2 high-priority exact-panel evidence requests; promotion/engine/threshold patch sums 0",
        "next_action": "collect evidence, then rerun BR-069 and BR-070",
    },
    {
        "branch_id": "BR-20260424-071",
        "branch_title": "strong_common_cause_blocker_regression_packet",
        "evidence_layer": "common_cause_boundary",
        "judgment_role": "regression_blocker_seed",
        "handoff_state": "indexed_as_safety_material",
        "primary_doc_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_071_STRONG_COMMON_CAUSE_BLOCKER_REGRESSION_PACKET_V1.md",
        "primary_artifact_path": "/private/tmp/strong_common_cause_blocker_regression_packet_check/panel_day_engine_strong_common_cause_blocker_regression_packet_v1.csv",
        "primary_artifact_kind": "detail_csv",
        "repro_command": BR071_REPRO,
        "key_result": "50 strong common-cause hold rows packaged as blocker/regression seeds; panel-local promotion blocked sum 50",
        "next_action": "use before semantic patches that could promote common-cause rows",
    },
    {
        "branch_id": "BR-20260424-072",
        "branch_title": "common_cause_exact_seed_search",
        "evidence_layer": "common_cause_boundary",
        "judgment_role": "candidate_reservoir_structural_blocker",
        "handoff_state": "indexed_as_non_closure",
        "primary_doc_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_072_COMMON_CAUSE_EXACT_SEED_SEARCH_V1.md",
        "primary_artifact_path": "/private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv",
        "primary_artifact_kind": "detail_csv",
        "repro_command": BR072_REPRO,
        "key_result": "exact closure 0; 49 panels / 101 raw direct rows preserved as reservoir plus structural blockers",
        "next_action": "resolve report-lane/date-alignment blockers before any closure claim",
    },
    {
        "branch_id": "BR-20260424-073",
        "branch_title": "common_cause_structural_blocker_review",
        "evidence_layer": "common_cause_boundary",
        "judgment_role": "structural_blocker_split",
        "handoff_state": "indexed_as_non_closure",
        "primary_doc_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_073_COMMON_CAUSE_STRUCTURAL_BLOCKER_REVIEW_V1.md",
        "primary_artifact_path": "/private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_v1.csv",
        "primary_artifact_kind": "detail_csv",
        "repro_command": BR073_REPRO,
        "key_result": "49 blockers split; only 2 manual trace targets, promotion/engine/threshold patch 0",
        "next_action": "trace gangui raw-only near-anchor and ktc_ess 71-day mismatch",
    },
    {
        "branch_id": "BR-20260424-074",
        "branch_title": "common_cause_manual_trace_review",
        "evidence_layer": "common_cause_boundary",
        "judgment_role": "manual_trace_non_closure",
        "handoff_state": "indexed_as_non_closure",
        "primary_doc_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_074_COMMON_CAUSE_MANUAL_TRACE_REVIEW_V1.md",
        "primary_artifact_path": "/private/tmp/common_cause_manual_trace_review_check/panel_day_engine_common_cause_manual_trace_review_v1.csv",
        "primary_artifact_kind": "detail_csv",
        "repro_command": BR074_REPRO,
        "key_result": "2 traces remain non-closure: raw-only near-anchor trace-only and post-current 71-day mismatch",
        "next_action": "preserve as regression/hold evidence, not semantic approval",
    },
    {
        "branch_id": "BR-20260424-075",
        "branch_title": "common_cause_semantic_prepatch_gate",
        "evidence_layer": "prepatch_safety_gate",
        "judgment_role": "common_cause_semantic_gate",
        "handoff_state": "required_before_semantic_review",
        "primary_doc_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_075_COMMON_CAUSE_SEMANTIC_PREPATCH_GATE_V1.md",
        "primary_artifact_path": "/private/tmp/common_cause_semantic_prepatch_gate_check/panel_day_engine_common_cause_semantic_prepatch_gate_v1.csv",
        "primary_artifact_kind": "gate_csv",
        "repro_command": BR075_REPRO,
        "key_result": "overall pass; 12 required gates, failed 0, warning 1; exact closure 0, raw direct rows 101",
        "next_action": "run before common-cause semantic loosening; pass is precondition not approval",
    },
    {
        "branch_id": "BR-20260424-076",
        "branch_title": "algorithm_prepatch_runbook_common_cause_gate",
        "evidence_layer": "prepatch_safety_gate",
        "judgment_role": "combined_algorithm_prepatch_runbook",
        "handoff_state": "required_before_algorithm_review",
        "primary_doc_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_076_ALGORITHM_PREPATCH_RUNBOOK_COMMON_CAUSE_GATE_V1.md",
        "primary_artifact_path": "/private/tmp/panel_engine_algorithm_prepatch_runbook_br076_check/panel_day_engine_algorithm_prepatch_runbook_v1.csv",
        "primary_artifact_kind": "gate_csv",
        "repro_command": BR076_REPRO,
        "key_result": "overall pass; 3 gates passed, failed 0; panel-engine/fault-family/common-cause statuses pass",
        "next_action": "run 3-gate runbook before direct panel_day_engine.py algorithm review",
    },
    {
        "branch_id": "BR-20260424-077",
        "branch_title": "project_completion_checkpoint",
        "evidence_layer": "handoff_navigation",
        "judgment_role": "current_project_map",
        "handoff_state": "current_checkpoint_before_br078",
        "primary_doc_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_077_PROJECT_COMPLETION_CHECKPOINT_V1.md",
        "primary_artifact_path": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_077_PROJECT_COMPLETION_CHECKPOINT_V1.md",
        "primary_artifact_kind": "repo_doc",
        "repro_command": "python3 -m py_compile pv_ae/panel_day_engine.py && git diff --check",
        "key_result": "whole-project map says safety/evidence lanes are stronger, but latest manifest/handoff indexing is stale",
        "next_action": "refresh latest evidence/handoff manifest for BR-064 through BR-076",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a latest evidence/handoff manifest for BR-064 through BR-077, "
            "including temp artifact presence, repro commands, and patch-authorization boundaries."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root to resolve tracked docs.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory for manifest artifacts.")
    parser.add_argument("--owner-branch", default="", help="Optional branch label. Defaults to current git branch.")
    return parser.parse_args()


def detect_owner_branch(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if completed.returncode == 0:
        return completed.stdout.strip() or "unknown"
    return "unknown"


def classify_artifact(path_text: str) -> str:
    if path_text.startswith("/private/tmp/") or path_text.startswith("/tmp/") or path_text.startswith("/private/var/"):
        return "temp"
    return "repo"


def resolve_path(repo_root: Path, path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return repo_root / path


def build_manifest(repo_root: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for spec in BRANCH_SPECS:
        doc_path = resolve_path(repo_root, spec["primary_doc_path"])
        artifact_path = resolve_path(repo_root, spec["primary_artifact_path"])
        artifact_location_type = classify_artifact(spec["primary_artifact_path"])
        artifact_exists = artifact_path.exists()
        repro_required = int(artifact_location_type == "temp" and not artifact_exists)
        rows.append(
            {
                "branch_id": spec["branch_id"],
                "branch_title": spec["branch_title"],
                "evidence_layer": spec["evidence_layer"],
                "judgment_role": spec["judgment_role"],
                "handoff_state": spec["handoff_state"],
                "primary_doc_path": spec["primary_doc_path"],
                "primary_doc_exists": int(doc_path.exists()),
                "primary_artifact_path": spec["primary_artifact_path"],
                "primary_artifact_kind": spec["primary_artifact_kind"],
                "primary_artifact_exists": int(artifact_exists),
                "artifact_location_type": artifact_location_type,
                "repro_command": spec["repro_command"],
                "repro_required_if_missing": repro_required,
                "key_result": spec["key_result"],
                "next_action": spec["next_action"],
                "operator_promotion_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "stable_contract_change_allowed": 0,
                "release_regeneration_allowed": 0,
                "notes": "handoff_only_no_runtime_semantics_change",
            }
        )
    return pd.DataFrame(rows, columns=DETAIL_COLUMNS)


def join_unique(values: pd.Series) -> str:
    items = sorted({str(value) for value in values if str(value).strip()})
    return " | ".join(items)


def build_summary(detail_df: pd.DataFrame) -> pd.DataFrame:
    if detail_df.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    summary = (
        detail_df.groupby(["evidence_layer", "handoff_state"], as_index=False, dropna=False)
        .agg(
            branches=("branch_id", "count"),
            repo_docs_present=("primary_doc_exists", "sum"),
            primary_artifacts_present=("primary_artifact_exists", "sum"),
            temp_artifacts_missing=("repro_required_if_missing", "sum"),
            operator_promotion_allowed_sum=("operator_promotion_allowed", "sum"),
            engine_patch_allowed_sum=("engine_patch_allowed", "sum"),
            threshold_patch_allowed_sum=("threshold_patch_allowed", "sum"),
            next_actions=("next_action", join_unique),
        )
        .loc[:, SUMMARY_COLUMNS]
        .sort_values(["evidence_layer", "handoff_state"], kind="stable")
    )
    return summary


def write_json(output_dir: Path, owner_branch: str, detail_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    payload = {
        "owner_branch": owner_branch,
        "branch_count": int(len(detail_df)),
        "branch_min": str(detail_df["branch_id"].min()) if not detail_df.empty else "",
        "branch_max": str(detail_df["branch_id"].max()) if not detail_df.empty else "",
        "repo_doc_missing_count": int((detail_df["primary_doc_exists"] == 0).sum()) if not detail_df.empty else 0,
        "temp_artifact_missing_count": int(detail_df["repro_required_if_missing"].sum()) if not detail_df.empty else 0,
        "engine_patch_allowed_sum": int(detail_df["engine_patch_allowed"].sum()) if not detail_df.empty else 0,
        "threshold_patch_allowed_sum": int(detail_df["threshold_patch_allowed"].sum()) if not detail_df.empty else 0,
        "operator_promotion_allowed_sum": int(detail_df["operator_promotion_allowed"].sum()) if not detail_df.empty else 0,
        "evidence_layers": sorted(detail_df["evidence_layer"].unique().tolist()) if not detail_df.empty else [],
        "handoff_states": sorted(detail_df["handoff_state"].unique().tolist()) if not detail_df.empty else [],
        "summary_rows": int(len(summary_df)),
    }
    (output_dir / JSON_OUTPUT_NAME).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_note(output_dir: Path, owner_branch: str, detail_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    temp_missing = int(detail_df["repro_required_if_missing"].sum()) if not detail_df.empty else 0
    doc_missing = int((detail_df["primary_doc_exists"] == 0).sum()) if not detail_df.empty else 0
    lines = [
        "# panel_day_engine_latest_evidence_handoff_manifest_v1",
        "",
        "## Purpose",
        "- Refresh the BR-064 through BR-077 evidence/handoff map after BR-077.",
        "- Keep temp artifact paths, repro commands, patch boundaries, and next actions readable from one manifest.",
        "- This is handoff-only and does not change runtime semantics.",
        "",
        "## Snapshot",
        f"- owner_branch: `{owner_branch}`",
        f"- indexed branches: `{len(detail_df)}`",
        f"- repo docs missing: `{doc_missing}`",
        f"- temp artifacts requiring repro if missing: `{temp_missing}`",
        f"- engine patch allowed sum: `{int(detail_df['engine_patch_allowed'].sum())}`",
        f"- threshold patch allowed sum: `{int(detail_df['threshold_patch_allowed'].sum())}`",
        f"- operator promotion allowed sum: `{int(detail_df['operator_promotion_allowed'].sum())}`",
        "",
        "## Interpretation",
        "- Missing `/private/tmp` artifacts are not failures by themselves; they mean the row must be regenerated with its `repro_command`.",
        "- A present gate or packet artifact is evidence for review, not approval for production semantics.",
        "- The current next action remains a latest manifest/handoff refresh before more scattered scans or algorithm proposals.",
        "",
        "## Summary Rows",
    ]
    for row in summary_df.to_dict(orient="records"):
        lines.append(
            f"- `{row['evidence_layer']}` / `{row['handoff_state']}`: branches `{row['branches']}`, "
            f"temp_missing `{row['temp_artifacts_missing']}`"
        )
    (output_dir / NOTE_OUTPUT_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    owner_branch = args.owner_branch or detect_owner_branch(repo_root)
    detail_df = build_manifest(repo_root)
    summary_df = build_summary(detail_df)
    detail_df.insert(0, "owner_branch", owner_branch)
    detail_df.to_csv(output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_json(output_dir, owner_branch, detail_df, summary_df)
    write_note(output_dir, owner_branch, detail_df, summary_df)


if __name__ == "__main__":
    main()
