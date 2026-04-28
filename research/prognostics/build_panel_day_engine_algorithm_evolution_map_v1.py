#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


LAYER_OUTPUT_NAME = "panel_day_engine_algorithm_evolution_layer_map_v1.csv"
GAP_OUTPUT_NAME = "panel_day_engine_algorithm_evolution_gap_audit_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_algorithm_evolution_action_queue_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_algorithm_evolution_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_algorithm_evolution_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_algorithm_evolution_map_v1.json"


LAYER_COLUMNS = [
    "owner_branch",
    "layer_id",
    "engine_location_hint",
    "current_role",
    "current_promotion_power",
    "main_evidence_axes",
    "protective_gates",
    "known_gap",
    "next_evidence_work",
    "allowed_next_action",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

GAP_COLUMNS = [
    "owner_branch",
    "gap_id",
    "gap_family",
    "risk_if_ignored",
    "current_evidence_boundary",
    "required_evidence_to_close",
    "blocked_patch_type",
    "recommended_artifact",
    "priority",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

ACTION_COLUMNS = [
    "owner_branch",
    "sequence",
    "action_id",
    "action",
    "purpose",
    "entrypoint_or_artifact",
    "requires_before_start",
    "success_boundary",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "metric",
    "value",
    "interpretation",
]


PATTERNS = {
    "train_only_vbin_reference": "def build_vbin_map_from_train",
    "ae_reconstruction_anomaly": "class AE",
    "event_feature_rule_labels": 'out["anom_subtype"]',
    "group_off_common_cause_gate": "def _detect_group_off",
    "vdrop_critical_like_ssot": "def compute_vdrop_labels",
    "final_fault_confirmation": "    # final_fault",
    "ews_local_precursor": "def _compute_ews",
    "site_event_context": "def _compute_site_events",
    "prefault_b_template": 'out["prefault_B"] =',
    "output_audit_reports": 'out_path = out_dir / "panel_day_core.csv"',
}


def locate_patterns(engine_path: Path) -> dict[str, str]:
    lines = engine_path.read_text(encoding="utf-8").splitlines()
    locations: dict[str, str] = {}
    for layer_id, pattern in PATTERNS.items():
        match_line = None
        for idx, line in enumerate(lines, start=1):
            if pattern in line:
                match_line = idx
                break
        if match_line is None:
            locations[layer_id] = f"{engine_path.as_posix()}:MISSING_PATTERN"
        else:
            locations[layer_id] = f"{engine_path.as_posix()}:{match_line}"
    return locations


def bool_int(value: bool) -> int:
    return 1 if value else 0


def build_layer_rows(owner_branch: str, locations: dict[str, str]) -> list[dict[str, object]]:
    return [
        {
            "owner_branch": owner_branch,
            "layer_id": "train_only_vbin_reference",
            "engine_location_hint": locations["train_only_vbin_reference"],
            "current_role": "panel voltage-bin reference construction",
            "current_promotion_power": "reference_context_only",
            "main_evidence_axes": "train-only mid_v_ratio, panel median, group_key split, bad/dead-like exclusion",
            "protective_gates": "train files only; no test leakage; no operator verdict promotion",
            "known_gap": "vbin explains peer grouping but does not identify fault subtype by itself",
            "next_evidence_work": "keep as baseline context; use only as stratification for subtype replay",
            "allowed_next_action": "shadow stratification",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Safe as a reference layer; not a fault-family decision layer.",
        },
        {
            "owner_branch": owner_branch,
            "layer_id": "ae_reconstruction_anomaly",
            "engine_location_hint": locations["ae_reconstruction_anomaly"],
            "current_role": "morphology/anomaly detector",
            "current_promotion_power": "candidate_signal_only",
            "main_evidence_axes": "AE reconstruction error, train quantile threshold, peer-normalized daily curve",
            "protective_gates": "train-period threshold; final_fault is not assigned from AE alone",
            "known_gap": "AE does not explain root cause and has no supervised subtype calibration yet",
            "next_evidence_work": "episode-level anomaly recurrence and subtype-conditioned calibration replay",
            "allowed_next_action": "shadow evidence expansion",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Use AE as shape evidence, not as a root-cause classifier.",
        },
        {
            "owner_branch": owner_branch,
            "layer_id": "event_feature_rule_labels",
            "engine_location_hint": locations["event_feature_rule_labels"],
            "current_role": "daily rule/subtype hypothesis assignment",
            "current_promotion_power": "hypothesis_or_review_context",
            "main_evidence_axes": "fault_like_day, degraded_candidate, shadow_like, anom_level, anom_subtype",
            "protective_gates": "group-off guard; subtype remains hypothesis unless multi-axis evidence closes",
            "known_gap": "daily label can overread one-day episodes without episode-level persistence context",
            "next_evidence_work": "convert daily rows into episode chains with persistence, recurrence, and strict-trigger distance",
            "allowed_next_action": "episode sidecar",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "This is the best place to add evidence columns before changing semantics.",
        },
        {
            "owner_branch": owner_branch,
            "layer_id": "group_off_common_cause_gate",
            "engine_location_hint": locations["group_off_common_cause_gate"],
            "current_role": "common-cause / group-off suppression gate",
            "current_promotion_power": "panel_local_promotion_blocker",
            "main_evidence_axes": "date-group dead fraction, stable panel set, same-day group behavior",
            "protective_gates": "masks local categories and EWS where site/group-off context dominates",
            "known_gap": "raw-only common-cause reservoirs are not official/current closure",
            "next_evidence_work": "official/current bridge evidence plus regression blocker preservation",
            "allowed_next_action": "regression blocker audit",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Keep conservative until BR-075/076 style gates pass.",
        },
        {
            "owner_branch": owner_branch,
            "layer_id": "vdrop_critical_like_ssot",
            "engine_location_hint": locations["vdrop_critical_like_ssot"],
            "current_role": "critical-like voltage drop single source of truth",
            "current_promotion_power": "hard_evidence_candidate",
            "main_evidence_axes": "v_ref trust, v_drop, current preservation, data quality, group-off mask",
            "protective_gates": "critical confirmed/suspect split; v_ref and data_bad guards",
            "known_gap": "physical-leaning raw waveform support is not independent physical confirmation",
            "next_evidence_work": "exact-panel physical measurement and maintenance/inspection evidence attachment",
            "allowed_next_action": "physical confirmation acquisition",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Do not loosen voltage thresholds until physical confirmation gap is closed.",
        },
        {
            "owner_branch": owner_branch,
            "layer_id": "final_fault_confirmation",
            "engine_location_hint": locations["final_fault_confirmation"],
            "current_role": "operator-facing confirmed fault boundary",
            "current_promotion_power": "operator_facing_final_verdict",
            "main_evidence_axes": "confirmed dead-like run, critical_confirmed run, tuning-level p2 policy",
            "protective_gates": "candidate/suspect/prefault signals do not automatically become final_fault",
            "known_gap": "performance/accuracy claim blocked without truth-label evaluation",
            "next_evidence_work": "before/after result delta scorecard plus subtype truth expansion",
            "allowed_next_action": "baseline and truth-gap audit",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Keep conservative; this layer should move last, not first.",
        },
        {
            "owner_branch": owner_branch,
            "layer_id": "ews_local_precursor",
            "engine_location_hint": locations["ews_local_precursor"],
            "current_role": "causal local early-warning signal",
            "current_promotion_power": "precursor_candidate_signal",
            "main_evidence_axes": "rolling variance, eventA frequency, DTW, Hampel score, panel-month baseline",
            "protective_gates": "causal past-only thresholds; disabled on final_fault, site_event, group_off_date",
            "known_gap": "EWS recurrence can indicate context but not the eventual fault family alone",
            "next_evidence_work": "family-conditioned episode replay and false-positive pressure seeds",
            "allowed_next_action": "shadow threshold replay",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Use as one axis in multi-axis precursor evidence, not direct promotion.",
        },
        {
            "owner_branch": owner_branch,
            "layer_id": "site_event_context",
            "engine_location_hint": locations["site_event_context"],
            "current_role": "site-wide event and external context marker",
            "current_promotion_power": "local_promotion_suppressor_or_context",
            "main_evidence_axes": "peer collapse, co_drop surge, degraded surge, shadow-like surge",
            "protective_gates": "blocks EWS/local promotion when site-wide context dominates",
            "known_gap": "site-event context needs official/current bridge before semantic loosening",
            "next_evidence_work": "official report-lane entry and date-alignment bridge audit",
            "allowed_next_action": "common-cause bridge audit",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Essential false-positive guard for panel-local claims.",
        },
        {
            "owner_branch": owner_branch,
            "layer_id": "prefault_b_template",
            "engine_location_hint": locations["prefault_b_template"],
            "current_role": "conservative prefault template heuristic",
            "current_promotion_power": "review_candidate_only",
            "main_evidence_axes": "40-day rolling mid ratio, AE ratio, DTW ratio, EWS ratio, common-cause overlap",
            "protective_gates": "requires multiple conditions; excludes final_fault; common-cause overlap masked",
            "known_gap": "fixed thresholds are not subtype-calibrated or truth-label validated",
            "next_evidence_work": "run subtype-specific threshold replay and episode truth audit",
            "allowed_next_action": "calibration shadow replay",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Good starting template, but not proof of true early prediction yet.",
        },
        {
            "owner_branch": owner_branch,
            "layer_id": "output_audit_reports",
            "engine_location_hint": locations["output_audit_reports"],
            "current_role": "audit/report output surface",
            "current_promotion_power": "traceability_surface",
            "main_evidence_axes": "panel_day_core, diagnosis summaries, critical confirmed/suspect reports, meta json",
            "protective_gates": "separate outputs allow shadow evidence without changing final verdict",
            "known_gap": "artifact sprawl can confuse current evidence entry point if not indexed",
            "next_evidence_work": "keep BR-078/BR-079 manifests as current read maps",
            "allowed_next_action": "handoff manifest refresh",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "This branch uses outputs for navigation only; no release regeneration.",
        },
    ]


def build_gap_rows(owner_branch: str) -> list[dict[str, object]]:
    return [
        {
            "owner_branch": owner_branch,
            "gap_id": "GAP-001",
            "gap_family": "fault_subtype_truth",
            "risk_if_ignored": "model may look organized but cannot support precision/recall or subtype accuracy claims",
            "current_evidence_boundary": "subtype hypotheses and family buckets exist, but exact truth labels remain sparse",
            "required_evidence_to_close": "exact-panel fault subtype truth rows with event windows and reviewed non-fault counterexamples",
            "blocked_patch_type": "operator-facing subtype label or performance claim",
            "recommended_artifact": "panel_day_engine_subtype_truth_expansion_backlog_v1",
            "priority": "P0",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "This is the main blocker for saying how much performance improved.",
        },
        {
            "owner_branch": owner_branch,
            "gap_id": "GAP-002",
            "gap_family": "episode_ground_truth",
            "risk_if_ignored": "one-day anomalies may be misread as real precursors or real precursors may be suppressed as noise",
            "current_evidence_boundary": "daily rows and branch packets exist, but episode-level onset/continuity truth is not locked",
            "required_evidence_to_close": "episode rows with start/end, recurrence, duration, strict-trigger distance, and family hypothesis",
            "blocked_patch_type": "precursor onset threshold patch",
            "recommended_artifact": "panel_day_engine_episode_truth_map_v1",
            "priority": "P0",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "This directly answers whether a long-gap onset was real precursor or over-backdating.",
        },
        {
            "owner_branch": owner_branch,
            "gap_id": "GAP-003",
            "gap_family": "physical_confirmation",
            "risk_if_ignored": "raw waveform support could be overstated as independent physical confirmation",
            "current_evidence_boundary": "BR-067/068 support voltage-axis plausibility; BR-069/070 show independent axes still missing",
            "required_evidence_to_close": "exact-panel physical measurement plus maintenance/inspection evidence attached to the same panel/event",
            "blocked_patch_type": "voltage-axis threshold loosening",
            "recommended_artifact": "rerun BR-069/BR-070 after evidence attachment",
            "priority": "P0",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Keep voltage-dominant cases review-only until this closes.",
        },
        {
            "owner_branch": owner_branch,
            "gap_id": "GAP-004",
            "gap_family": "official_current_common_cause_bridge",
            "risk_if_ignored": "raw-only common-cause context could be promoted as panel-local official/current fault evidence",
            "current_evidence_boundary": "BR-071 through BR-075 preserve common-cause rows as blocker/reservoir/non-closure evidence",
            "required_evidence_to_close": "official/current same-day bridge evidence or a scoped structural-blocker patch target proven by gate",
            "blocked_patch_type": "common-cause semantic loosening",
            "recommended_artifact": "common_cause_bridge_exact_closure_packet_v1",
            "priority": "P0",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "BR-076 3-gate runbook remains mandatory before any semantic review.",
        },
        {
            "owner_branch": owner_branch,
            "gap_id": "GAP-005",
            "gap_family": "threshold_calibration",
            "risk_if_ignored": "hand thresholds may become sticky without evidence that they generalize by site/family",
            "current_evidence_boundary": "thresholds are domain-reasonable but not yet replayed against subtype truth sets",
            "required_evidence_to_close": "shadow replay grid with candidate threshold, result delta, false-positive pressure seeds, and holdout rows",
            "blocked_patch_type": "threshold update",
            "recommended_artifact": "panel_day_engine_subtype_threshold_replay_v1",
            "priority": "P1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Tune only after truth/episode gaps are structured.",
        },
        {
            "owner_branch": owner_branch,
            "gap_id": "GAP-006",
            "gap_family": "ae_role_boundary",
            "risk_if_ignored": "AE anomaly could be mistaken for root-cause classification",
            "current_evidence_boundary": "AE is useful morphology evidence but not supervised family classifier",
            "required_evidence_to_close": "documented AE role boundary plus subtype-conditioned separability audit if classification is proposed",
            "blocked_patch_type": "AE-based root-cause claim",
            "recommended_artifact": "panel_day_engine_ae_family_separability_audit_v1",
            "priority": "P1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "A better AE is optional; a clearer AE role boundary is required.",
        },
        {
            "owner_branch": owner_branch,
            "gap_id": "GAP-007",
            "gap_family": "monolithic_engine_maintainability",
            "risk_if_ignored": "safe logic may become harder to review because ingestion, ML, rules, and reports share one large file",
            "current_evidence_boundary": "safety gates and scorecards exist; no modular refactor boundary is locked",
            "required_evidence_to_close": "refactor-only plan with byte-equivalent outputs and source/package sync checks",
            "blocked_patch_type": "large direct refactor mixed with semantics",
            "recommended_artifact": "panel_day_engine_refactor_equivalence_runbook_v1",
            "priority": "P2",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Do not mix cleanup refactor with algorithm behavior changes.",
        },
    ]


def build_action_rows(owner_branch: str) -> list[dict[str, object]]:
    return [
        {
            "owner_branch": owner_branch,
            "sequence": 1,
            "action_id": "ACT-001",
            "action": "freeze current algorithm layers as baseline map",
            "purpose": "make future changes comparable against a known layer contract",
            "entrypoint_or_artifact": LAYER_OUTPUT_NAME,
            "requires_before_start": "BR-078 latest evidence manifest",
            "success_boundary": "all current layers mapped; operator/engine/threshold allowed sums remain 0",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "This BR implements this step.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 2,
            "action_id": "ACT-002",
            "action": "build subtype truth expansion backlog",
            "purpose": "separate fault family/subtype labels from weak morphology hypotheses",
            "entrypoint_or_artifact": "panel_day_engine_subtype_truth_expansion_backlog_v1",
            "requires_before_start": "layer map and gap audit",
            "success_boundary": "P0 missing truth rows are listed with required evidence and source lane",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "This is the cleanest next branch after BR-079.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 3,
            "action_id": "ACT-003",
            "action": "convert day-level precursor rows into episode chains",
            "purpose": "decide whether candidates are durable precursor, one-day episode, recovery-only, or displaced context",
            "entrypoint_or_artifact": "panel_day_engine_episode_truth_map_v1",
            "requires_before_start": "candidate row universe from BR-064/065 and current engine outputs",
            "success_boundary": "episode start/end, recurrence, duration, strict-trigger distance, site/common-cause overlap present",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "This targets the exact confusion around real precursor vs over-backdating.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 4,
            "action_id": "ACT-004",
            "action": "run subtype-conditioned threshold replay",
            "purpose": "move thresholds from hand-tuned defaults toward evidence-backed candidates",
            "entrypoint_or_artifact": "panel_day_engine_subtype_threshold_replay_v1",
            "requires_before_start": "episode truth map and regression pressure seeds",
            "success_boundary": "candidate threshold table has result delta and blocker impact before any code change",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Replay first, patch later.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 5,
            "action_id": "ACT-005",
            "action": "run BR-076 3-gate prepatch runbook before direct engine review",
            "purpose": "prove engine safety, fault-family regression, and common-cause boundaries before semantics move",
            "entrypoint_or_artifact": "check_panel_day_engine_algorithm_prepatch_runbook_v1.py",
            "requires_before_start": "a concrete one-rule candidate plus replay artifacts",
            "success_boundary": "all required gates pass; still not automatic patch approval",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "This remains a safety precondition, not a green light by itself.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 6,
            "action_id": "ACT-006",
            "action": "shadow-apply one selected rule candidate",
            "purpose": "measure semantic impact without touching production verdicts first",
            "entrypoint_or_artifact": "future BR shadow sidecar",
            "requires_before_start": "successful gates, truth/episode evidence, scorecard baseline",
            "success_boundary": "operator-facing production write 0 and result delta quantified",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Only after this should a small production patch be discussed.",
        },
    ]


def write_note(
    output_dir: Path,
    owner_branch: str,
    layer_df: pd.DataFrame,
    gap_df: pd.DataFrame,
    action_df: pd.DataFrame,
) -> None:
    p0_gaps = int(gap_df["priority"].eq("P0").sum())
    note = f"""# Panel Day Engine Algorithm Evolution Map V1

## Purpose
- Freeze the current `panel_day_engine.py` algorithm as layered evidence roles before changing it.
- Separate diagnostic baseline, precursor candidate logic, physical/common-cause blockers, and future threshold work.
- Keep this branch documentation/audit-only: no engine patch, no threshold patch, no operator-facing promotion.

## Outputs
- `{output_dir / LAYER_OUTPUT_NAME}`
- `{output_dir / GAP_OUTPUT_NAME}`
- `{output_dir / ACTION_OUTPUT_NAME}`
- `{output_dir / SUMMARY_OUTPUT_NAME}`
- `{output_dir / JSON_OUTPUT_NAME}`

## Result
- mapped layers: `{len(layer_df)}`
- evidence gaps: `{len(gap_df)}`
- P0 gaps: `{p0_gaps}`
- next actions: `{len(action_df)}`
- operator-facing change allowed sum: `{int(layer_df["operator_facing_change_allowed"].sum() + gap_df["operator_facing_change_allowed"].sum() + action_df["operator_facing_change_allowed"].sum())}`
- engine patch allowed sum: `{int(layer_df["engine_patch_allowed"].sum() + gap_df["engine_patch_allowed"].sum() + action_df["engine_patch_allowed"].sum())}`
- threshold patch allowed sum: `{int(layer_df["threshold_patch_allowed"].sum() + gap_df["threshold_patch_allowed"].sum() + action_df["threshold_patch_allowed"].sum())}`

## Reading
- The strongest current algorithm posture is conservative diagnosis plus evidence-gated candidate discovery.
- The main development blocker is not more model complexity; it is subtype truth, episode truth, and physical/common-cause closure evidence.
- AE/EWS should remain morphology and precursor-candidate axes until subtype-conditioned replay proves promotion is safe.
- Direct `panel_day_engine.py` review still requires the BR-076 3-gate prepatch runbook first.

## Recommended Next Branch
- Build `panel_day_engine_subtype_truth_expansion_backlog_v1`.
- Then build `panel_day_engine_episode_truth_map_v1`.
- Only after those should threshold replay or shadow semantic application be reopened.

## Repro Command
```bash
python3 research/prognostics/build_panel_day_engine_algorithm_evolution_map_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir {output_dir}
```
"""
    (output_dir / NOTE_OUTPUT_NAME).write_text(note, encoding="utf-8")


def build_outputs(repo_root: Path, output_dir: Path, owner_branch: str) -> dict[str, object]:
    engine_path = repo_root / "pv_ae/panel_day_engine.py"
    if not engine_path.exists():
        raise FileNotFoundError(engine_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    locations = locate_patterns(engine_path)

    layer_df = pd.DataFrame(build_layer_rows(owner_branch, locations), columns=LAYER_COLUMNS)
    gap_df = pd.DataFrame(build_gap_rows(owner_branch), columns=GAP_COLUMNS)
    action_df = pd.DataFrame(build_action_rows(owner_branch), columns=ACTION_COLUMNS)

    total_operator_allowed = int(
        layer_df["operator_facing_change_allowed"].sum()
        + gap_df["operator_facing_change_allowed"].sum()
        + action_df["operator_facing_change_allowed"].sum()
    )
    total_engine_allowed = int(
        layer_df["engine_patch_allowed"].sum()
        + gap_df["engine_patch_allowed"].sum()
        + action_df["engine_patch_allowed"].sum()
    )
    total_threshold_allowed = int(
        layer_df["threshold_patch_allowed"].sum()
        + gap_df["threshold_patch_allowed"].sum()
        + action_df["threshold_patch_allowed"].sum()
    )

    summary_rows = [
        {
            "owner_branch": owner_branch,
            "metric": "mapped_layer_count",
            "value": len(layer_df),
            "interpretation": "current engine layers with role, evidence, gap, and next action",
        },
        {
            "owner_branch": owner_branch,
            "metric": "evidence_gap_count",
            "value": len(gap_df),
            "interpretation": "known gaps that block overconfident promotion or thresholding",
        },
        {
            "owner_branch": owner_branch,
            "metric": "p0_gap_count",
            "value": int(gap_df["priority"].eq("P0").sum()),
            "interpretation": "must close or explicitly hold before semantic/threshold patch",
        },
        {
            "owner_branch": owner_branch,
            "metric": "next_action_count",
            "value": len(action_df),
            "interpretation": "ordered follow-up actions from evidence map to shadow-only rule testing",
        },
        {
            "owner_branch": owner_branch,
            "metric": "operator_facing_change_allowed_sum",
            "value": total_operator_allowed,
            "interpretation": "must stay 0 for this audit-only branch",
        },
        {
            "owner_branch": owner_branch,
            "metric": "engine_patch_allowed_sum",
            "value": total_engine_allowed,
            "interpretation": "must stay 0 until prepatch gates and shadow replay pass",
        },
        {
            "owner_branch": owner_branch,
            "metric": "threshold_patch_allowed_sum",
            "value": total_threshold_allowed,
            "interpretation": "must stay 0 until subtype/episode truth and replay evidence exist",
        },
    ]
    summary_df = pd.DataFrame(summary_rows, columns=SUMMARY_COLUMNS)

    layer_df.to_csv(output_dir / LAYER_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    gap_df.to_csv(output_dir / GAP_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir, owner_branch, layer_df, gap_df, action_df)

    payload = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "layer_count": len(layer_df),
        "gap_count": len(gap_df),
        "p0_gap_count": int(gap_df["priority"].eq("P0").sum()),
        "action_count": len(action_df),
        "operator_facing_change_allowed_sum": total_operator_allowed,
        "engine_patch_allowed_sum": total_engine_allowed,
        "threshold_patch_allowed_sum": total_threshold_allowed,
        "recommended_next_branch": "panel_day_engine_subtype_truth_expansion_backlog_v1",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "layer_map": str(output_dir / LAYER_OUTPUT_NAME),
            "gap_audit": str(output_dir / GAP_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
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
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to this script's repository.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/private/tmp/panel_day_engine_algorithm_evolution_map_br079_check"),
        help="Directory for generated audit artifacts.",
    )
    parser.add_argument(
        "--owner-branch",
        default="BR-20260425-079",
        help="Branch/work item id written into output rows.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_outputs(
        repo_root=args.repo_root.resolve(),
        output_dir=args.output_dir,
        owner_branch=args.owner_branch,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
