#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


AUDIT_OUTPUT_NAME = "panel_day_engine_direction_assumption_audit_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_direction_assumption_audit_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_direction_assumption_audit_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_direction_assumption_audit_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_direction_assumption_audit_v1.json"

BR079_ROOT_DEFAULT = "/private/tmp/panel_day_engine_algorithm_evolution_map_br079_check"
BR080_ROOT_DEFAULT = "/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check"
BR081_ROOT_DEFAULT = "/private/tmp/panel_day_engine_episode_truth_map_br081_check"
BR082_ROOT_DEFAULT = "/private/tmp/panel_day_engine_episode_truth_review_packet_br082_check"

EXPECTED_BR081_BUCKET_COUNTS = {
    "common_cause_or_group_episode_hold": 205,
    "recovery_recurrence_observation": 12,
    "long_gap_backdating_hold": 12,
    "durable_precursor_candidate_review": 7,
    "episode_truth_requirement": 5,
    "strict_anchor_sudden_review": 3,
}

EXPECTED_BR082_TRACK_COUNTS = {
    "durable_precursor_review": 7,
    "long_gap_backdating_review": 6,
    "strict_sudden_prior_episode_review": 3,
}

EXPECTED_BR082_PRIORITY_COUNTS = {
    "P0": 9,
    "P1": 7,
}

AUDIT_COLUMNS = [
    "owner_branch",
    "audit_id",
    "source_branch",
    "assumption_family",
    "check_name",
    "expected_value",
    "actual_value",
    "audit_status",
    "severity",
    "failure_impact",
    "required_action_if_failed",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "source_branch",
    "assumption_family",
    "total_checks",
    "pass_count",
    "warn_count",
    "fail_count",
    "p0_fail_count",
    "operator_facing_change_allowed_sum",
    "engine_patch_allowed_sum",
    "threshold_patch_allowed_sum",
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


def numeric_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


def value_to_text(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


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


def read_json(path: Path, name: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing required json {name}: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path, required_cols: list[str], name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing required csv {name}: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")
    return df


def add_check(
    rows: list[dict[str, object]],
    *,
    owner_branch: str,
    audit_id: str,
    source_branch: str,
    assumption_family: str,
    check_name: str,
    expected_value: object,
    actual_value: object,
    ok: bool,
    severity: str,
    failure_impact: str,
    required_action_if_failed: str,
    notes: str = "",
) -> None:
    rows.append(
        {
            "owner_branch": owner_branch,
            "audit_id": audit_id,
            "source_branch": source_branch,
            "assumption_family": assumption_family,
            "check_name": check_name,
            "expected_value": value_to_text(expected_value),
            "actual_value": value_to_text(actual_value),
            "audit_status": "PASS" if ok else "FAIL",
            "severity": severity,
            "failure_impact": failure_impact,
            "required_action_if_failed": required_action_if_failed,
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": notes,
        }
    )


def auth_sum_from_payload(payload: dict[str, Any]) -> int:
    return int(payload.get("operator_facing_change_allowed_sum", 0)) + int(payload.get("engine_patch_allowed_sum", 0)) + int(payload.get("threshold_patch_allowed_sum", 0))


def auth_sum_from_frame(df: pd.DataFrame) -> int:
    total = 0
    for col in ["operator_facing_change_allowed", "engine_patch_allowed", "threshold_patch_allowed"]:
        if col in df.columns:
            total += int(df[col].fillna(0).map(numeric_int).sum())
    return total


def count_p0(df: pd.DataFrame, col: str = "priority") -> int:
    if col not in df.columns:
        return 0
    return int(df[col].map(normalize_text).eq("P0").sum())


def add_json_metric_check(
    rows: list[dict[str, object]],
    *,
    owner_branch: str,
    audit_id: str,
    source_branch: str,
    assumption_family: str,
    payload: dict[str, Any],
    metric: str,
    expected: object,
    severity: str,
    failure_impact: str,
    required_action_if_failed: str,
) -> None:
    actual = payload.get(metric)
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id,
        source_branch=source_branch,
        assumption_family=assumption_family,
        check_name=f"json.{metric}",
        expected_value=expected,
        actual_value=actual,
        ok=actual == expected,
        severity=severity,
        failure_impact=failure_impact,
        required_action_if_failed=required_action_if_failed,
    )


def build_audit(
    owner_branch: str,
    br079_root: Path,
    br080_root: Path,
    br081_root: Path,
    br082_root: Path,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    next_id = 1

    def audit_id() -> str:
        nonlocal next_id
        value = f"BR083-AUD-{next_id:03d}"
        next_id += 1
        return value

    # BR-079: algorithm evolution map stays a map, not permission to patch.
    br079_json = read_json(br079_root / "panel_day_engine_algorithm_evolution_map_v1.json", "br079")
    br079_layers = read_csv(
        br079_root / "panel_day_engine_algorithm_evolution_layer_map_v1.csv",
        ["layer_id", "operator_facing_change_allowed", "engine_patch_allowed", "threshold_patch_allowed"],
        "br079_layers",
    )
    br079_gaps = read_csv(
        br079_root / "panel_day_engine_algorithm_evolution_gap_audit_v1.csv",
        ["gap_id", "priority", "operator_facing_change_allowed", "engine_patch_allowed", "threshold_patch_allowed"],
        "br079_gaps",
    )
    br079_actions = read_csv(
        br079_root / "panel_day_engine_algorithm_evolution_action_queue_v1.csv",
        ["action_id", "operator_facing_change_allowed", "engine_patch_allowed", "threshold_patch_allowed"],
        "br079_actions",
    )
    for metric, expected in [
        ("layer_count", 10),
        ("gap_count", 7),
        ("p0_gap_count", 4),
        ("action_count", 6),
        ("recommended_next_branch", "panel_day_engine_subtype_truth_expansion_backlog_v1"),
    ]:
        add_json_metric_check(
            rows,
            owner_branch=owner_branch,
            audit_id=audit_id(),
            source_branch="BR-20260425-079",
            assumption_family="sequence_and_scope",
            payload=br079_json,
            metric=metric,
            expected=expected,
            severity="P0",
            failure_impact="algorithm evolution map no longer matches its documented contract",
            required_action_if_failed="rerun BR-079 builder and update downstream docs before continuing",
        )
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-079",
        assumption_family="authorization_boundary",
        check_name="csv_and_json_authorization_sum",
        expected_value=0,
        actual_value=auth_sum_from_payload(br079_json) + auth_sum_from_frame(br079_layers) + auth_sum_from_frame(br079_gaps) + auth_sum_from_frame(br079_actions),
        ok=auth_sum_from_payload(br079_json) + auth_sum_from_frame(br079_layers) + auth_sum_from_frame(br079_gaps) + auth_sum_from_frame(br079_actions) == 0,
        severity="P0",
        failure_impact="BR-079 would be authorizing behavior changes despite being map-only",
        required_action_if_failed="stop and split any authorization change into a separate reviewed patch",
    )
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-079",
        assumption_family="row_count_consistency",
        check_name="csv_counts_match_json",
        expected_value={"layers": br079_json.get("layer_count"), "gaps": br079_json.get("gap_count"), "actions": br079_json.get("action_count"), "p0_gaps": br079_json.get("p0_gap_count")},
        actual_value={"layers": len(br079_layers), "gaps": len(br079_gaps), "actions": len(br079_actions), "p0_gaps": count_p0(br079_gaps)},
        ok=len(br079_layers) == br079_json.get("layer_count")
        and len(br079_gaps) == br079_json.get("gap_count")
        and len(br079_actions) == br079_json.get("action_count")
        and count_p0(br079_gaps) == br079_json.get("p0_gap_count"),
        severity="P0",
        failure_impact="summary counts could be stale relative to actual CSV artifacts",
        required_action_if_failed="rebuild BR-079 outputs before using downstream decisions",
    )

    # BR-080: subtype backlog stays truth pending; exact truth support remains zero.
    br080_json = read_json(br080_root / "panel_day_engine_subtype_truth_expansion_backlog_v1.json", "br080")
    br080_backlog = read_csv(
        br080_root / "panel_day_engine_subtype_truth_expansion_backlog_v1.csv",
        ["backlog_case_id", "truth_priority", "current_exact_truth_support_count", "operator_facing_change_allowed", "engine_patch_allowed", "threshold_patch_allowed"],
        "br080_backlog",
    )
    for metric, expected in [
        ("subtype_backlog_rows", 17),
        ("p0_subtype_backlog_rows", 12),
        ("current_exact_truth_support_sum", 0),
        ("missing_optional_input_count", 0),
        ("recommended_next_branch", "panel_day_engine_episode_truth_map_v1"),
    ]:
        add_json_metric_check(
            rows,
            owner_branch=owner_branch,
            audit_id=audit_id(),
            source_branch="BR-20260425-080",
            assumption_family="truth_backlog_boundary",
            payload=br080_json,
            metric=metric,
            expected=expected,
            severity="P0",
            failure_impact="subtype backlog could be read as stronger truth than current evidence supports",
            required_action_if_failed="rebuild BR-080 and do not open threshold replay until exact truth support is reconciled",
        )
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-080",
        assumption_family="truth_backlog_boundary",
        check_name="csv_exact_truth_support_sum",
        expected_value=0,
        actual_value=int(br080_backlog["current_exact_truth_support_count"].fillna(0).map(numeric_int).sum()),
        ok=int(br080_backlog["current_exact_truth_support_count"].fillna(0).map(numeric_int).sum()) == 0,
        severity="P0",
        failure_impact="BR-080 would no longer be a backlog-only truth layer",
        required_action_if_failed="create a reviewed truth artifact instead of changing backlog semantics",
    )
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-080",
        assumption_family="authorization_boundary",
        check_name="csv_and_json_authorization_sum",
        expected_value=0,
        actual_value=auth_sum_from_payload(br080_json) + auth_sum_from_frame(br080_backlog),
        ok=auth_sum_from_payload(br080_json) + auth_sum_from_frame(br080_backlog) == 0,
        severity="P0",
        failure_impact="BR-080 would be authorizing subtype or threshold changes despite being backlog-only",
        required_action_if_failed="stop and separate authorization from backlog generation",
    )
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-080",
        assumption_family="row_count_consistency",
        check_name="csv_counts_match_json",
        expected_value={"backlog_rows": br080_json.get("subtype_backlog_rows"), "p0_rows": br080_json.get("p0_subtype_backlog_rows")},
        actual_value={"backlog_rows": len(br080_backlog), "p0_rows": int(br080_backlog["truth_priority"].map(normalize_text).eq("P0").sum())},
        ok=len(br080_backlog) == br080_json.get("subtype_backlog_rows")
        and int(br080_backlog["truth_priority"].map(normalize_text).eq("P0").sum()) == br080_json.get("p0_subtype_backlog_rows"),
        severity="P0",
        failure_impact="BR-080 summary could be stale relative to backlog rows",
        required_action_if_failed="rebuild BR-080 or update docs before continuing",
    )

    # BR-081: episode map preserves truth-pending status and G1 precedence after the earlier near-miss.
    br081_json = read_json(br081_root / "panel_day_engine_episode_truth_map_v1.json", "br081")
    br081_map = read_csv(
        br081_root / "panel_day_engine_episode_truth_map_v1.csv",
        [
            "episode_truth_case_id",
            "source_artifact",
            "episode_truth_bucket",
            "episode_truth_status",
            "common_cause_flag_sum",
            "operator_facing_change_allowed",
            "engine_patch_allowed",
            "threshold_patch_allowed",
        ],
        "br081_map",
    )
    for metric, expected in [
        ("episode_truth_map_rows", 244),
        ("bucket_counts", EXPECTED_BR081_BUCKET_COUNTS),
        ("truth_status_counts", {"truth_pending": 244}),
        ("missing_optional_input_count", 0),
        ("recommended_next_branch", "panel_day_engine_episode_truth_review_packet_v1"),
    ]:
        add_json_metric_check(
            rows,
            owner_branch=owner_branch,
            audit_id=audit_id(),
            source_branch="BR-20260425-081",
            assumption_family="episode_truth_boundary",
            payload=br081_json,
            metric=metric,
            expected=expected,
            severity="P0",
            failure_impact="episode map may no longer separate truth-pending categories correctly",
            required_action_if_failed="rerun BR-081 and inspect bucket precedence before continuing",
        )
    br081_bucket_counts = {str(k): int(v) for k, v in br081_map["episode_truth_bucket"].value_counts().items()}
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-081",
        assumption_family="bucket_precedence",
        check_name="csv_bucket_counts_match_expected",
        expected_value=EXPECTED_BR081_BUCKET_COUNTS,
        actual_value=br081_bucket_counts,
        ok=br081_bucket_counts == EXPECTED_BR081_BUCKET_COUNTS,
        severity="P0",
        failure_impact="bucket precedence drift could hide long-gap or strict-sudden rows",
        required_action_if_failed="fix bucket precedence and regenerate BR-081 before deriving review packets",
    )
    g1 = br081_map.loc[br081_map["source_artifact"].map(normalize_text).eq("br017_g1_longgap_cases")]
    g1_long = int(g1["episode_truth_bucket"].map(normalize_text).eq("long_gap_backdating_hold").sum())
    g1_common = int(g1["episode_truth_bucket"].map(normalize_text).eq("common_cause_or_group_episode_hold").sum())
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-081",
        assumption_family="bucket_precedence",
        check_name="g1_longgap_lens_preserved",
        expected_value={"long_gap_backdating_hold": 6, "common_cause_or_group_episode_hold": 1},
        actual_value={"long_gap_backdating_hold": g1_long, "common_cause_or_group_episode_hold": g1_common},
        ok=g1_long == 6 and g1_common == 1,
        severity="P0",
        failure_impact="the known near-miss could reappear by hiding G1 long-gap rows under common-cause",
        required_action_if_failed="fix BR-081 classification before trusting any reviewed truth packet",
    )
    durable = br081_map.loc[br081_map["episode_truth_bucket"].map(normalize_text).eq("durable_precursor_candidate_review")]
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-081",
        assumption_family="common_cause_separation",
        check_name="durable_candidates_common_cause_zero",
        expected_value=0,
        actual_value=int(durable["common_cause_flag_sum"].fillna(0).map(numeric_int).max()) if not durable.empty else 0,
        ok=(not durable.empty) and int(durable["common_cause_flag_sum"].fillna(0).map(numeric_int).max()) == 0,
        severity="P0",
        failure_impact="durable precursor candidates could include common-cause rows",
        required_action_if_failed="split common-cause rows out before review or replay",
    )
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-081",
        assumption_family="authorization_boundary",
        check_name="csv_and_json_authorization_sum",
        expected_value=0,
        actual_value=auth_sum_from_payload(br081_json) + auth_sum_from_frame(br081_map),
        ok=auth_sum_from_payload(br081_json) + auth_sum_from_frame(br081_map) == 0,
        severity="P0",
        failure_impact="BR-081 would be authorizing behavior changes despite being truth-map-only",
        required_action_if_failed="stop and separate any production change into a gated patch",
    )

    # BR-082: review packet collapses duplicate lenses without assigning truth or granting patch permission.
    br082_json = read_json(br082_root / "panel_day_engine_episode_truth_review_packet_v1.json", "br082")
    br082_packet = read_csv(
        br082_root / "panel_day_engine_episode_truth_review_packet_v1.csv",
        [
            "review_packet_id",
            "review_track",
            "review_priority",
            "source_lens_count",
            "source_artifacts",
            "reviewer_truth_label",
            "operator_facing_change_allowed",
            "engine_patch_allowed",
            "threshold_patch_allowed",
        ],
        "br082_packet",
    )
    for metric, expected in [
        ("input_episode_map_rows", 244),
        ("selected_source_lens_rows", 22),
        ("review_packet_rows", 16),
        ("collapsed_duplicate_lens_count", 6),
        ("review_track_counts", EXPECTED_BR082_TRACK_COUNTS),
        ("review_priority_counts", EXPECTED_BR082_PRIORITY_COUNTS),
        ("reviewer_truth_label_assigned_count", 0),
        ("recommended_next_branch", "panel_day_engine_reviewed_episode_truth_rows_v1"),
    ]:
        add_json_metric_check(
            rows,
            owner_branch=owner_branch,
            audit_id=audit_id(),
            source_branch="BR-20260425-082",
            assumption_family="review_packet_boundary",
            payload=br082_json,
            metric=metric,
            expected=expected,
            severity="P0",
            failure_impact="review packet could be stale or could have started assigning truth prematurely",
            required_action_if_failed="rebuild BR-082 and inspect review packet derivation",
        )
    packet_ids = br082_packet["review_packet_id"].map(normalize_text).tolist()
    expected_ids = [f"BR082-EPR-{idx:03d}" for idx in range(1, len(br082_packet) + 1)]
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-082",
        assumption_family="review_packet_boundary",
        check_name="review_packet_ids_sequential_after_sort",
        expected_value=expected_ids,
        actual_value=packet_ids,
        ok=packet_ids == expected_ids,
        severity="P1",
        failure_impact="review packet remains usable but human review can become confusing",
        required_action_if_failed="renumber packet ids after final sort",
    )
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-082",
        assumption_family="review_packet_boundary",
        check_name="csv_review_track_counts_match_expected",
        expected_value=EXPECTED_BR082_TRACK_COUNTS,
        actual_value={str(k): int(v) for k, v in br082_packet["review_track"].value_counts().items()},
        ok={str(k): int(v) for k, v in br082_packet["review_track"].value_counts().items()} == EXPECTED_BR082_TRACK_COUNTS,
        severity="P0",
        failure_impact="review packet row universe may no longer match the intended high-risk buckets",
        required_action_if_failed="rebuild packet from BR-081 map and recheck selected buckets",
    )
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-082",
        assumption_family="review_packet_boundary",
        check_name="source_lens_collapse_counts",
        expected_value={"source_lens_rows": 22, "packet_rows": 16, "collapsed": 6},
        actual_value={
            "source_lens_rows": int(br082_packet["source_lens_count"].fillna(0).map(numeric_int).sum()),
            "packet_rows": len(br082_packet),
            "collapsed": int(br082_packet["source_lens_count"].fillna(0).map(numeric_int).sum() - len(br082_packet)),
        },
        ok=int(br082_packet["source_lens_count"].fillna(0).map(numeric_int).sum()) == 22
        and len(br082_packet) == 16
        and int(br082_packet["source_lens_count"].fillna(0).map(numeric_int).sum() - len(br082_packet)) == 6,
        severity="P0",
        failure_impact="duplicate G1 lens handling may have drifted",
        required_action_if_failed="inspect source lens grouping before manual review",
    )
    long_gap_packet = br082_packet.loc[br082_packet["review_track"].map(normalize_text).eq("long_gap_backdating_review")]
    g1_trace_ok = (
        len(long_gap_packet) == 6
        and long_gap_packet["source_lens_count"].fillna(0).map(numeric_int).eq(2).all()
        and long_gap_packet["source_artifacts"].map(normalize_text).str.contains("br017_episode_shadow").all()
        and long_gap_packet["source_artifacts"].map(normalize_text).str.contains("br017_g1_longgap_cases").all()
    )
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-082",
        assumption_family="review_packet_boundary",
        check_name="g1_duplicate_trace_retained",
        expected_value="6 long-gap packet rows with 2 source lenses and both source artifacts",
        actual_value=f"rows={len(long_gap_packet)}, source_lens_counts={long_gap_packet['source_lens_count'].map(numeric_int).tolist()}",
        ok=g1_trace_ok,
        severity="P0",
        failure_impact="review packet could lose traceability to the duplicate G1 lens",
        required_action_if_failed="preserve source_artifacts/source_case_ids before review",
    )
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-082",
        assumption_family="truth_assignment_boundary",
        check_name="reviewer_truth_labels_blank",
        expected_value=0,
        actual_value=int(br082_packet["reviewer_truth_label"].map(normalize_text).ne("").sum()),
        ok=int(br082_packet["reviewer_truth_label"].map(normalize_text).ne("").sum()) == 0,
        severity="P0",
        failure_impact="BR-082 would start assigning truth without evidence attachment",
        required_action_if_failed="move truth assignment into reviewed truth rows artifact",
    )
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-082",
        assumption_family="authorization_boundary",
        check_name="csv_and_json_authorization_sum",
        expected_value=0,
        actual_value=auth_sum_from_payload(br082_json) + auth_sum_from_frame(br082_packet),
        ok=auth_sum_from_payload(br082_json) + auth_sum_from_frame(br082_packet) == 0,
        severity="P0",
        failure_impact="BR-082 would authorize behavior changes despite being review-packet-only",
        required_action_if_failed="stop and split any production authorization into a later gated patch",
    )

    # Cross-branch guardrails.
    sequence_expected = [
        br079_json.get("recommended_next_branch"),
        br080_json.get("recommended_next_branch"),
        br081_json.get("recommended_next_branch"),
        br082_json.get("recommended_next_branch"),
    ]
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-079..082",
        assumption_family="sequence_and_scope",
        check_name="recommended_next_branch_chain",
        expected_value=[
            "panel_day_engine_subtype_truth_expansion_backlog_v1",
            "panel_day_engine_episode_truth_map_v1",
            "panel_day_engine_episode_truth_review_packet_v1",
            "panel_day_engine_reviewed_episode_truth_rows_v1",
        ],
        actual_value=sequence_expected,
        ok=sequence_expected
        == [
            "panel_day_engine_subtype_truth_expansion_backlog_v1",
            "panel_day_engine_episode_truth_map_v1",
            "panel_day_engine_episode_truth_review_packet_v1",
            "panel_day_engine_reviewed_episode_truth_rows_v1",
        ],
        severity="P0",
        failure_impact="roadmap order could drift toward premature threshold or engine work",
        required_action_if_failed="repair register/order lock before continuing implementation",
    )
    boundaries = [
        br079_json.get("direct_engine_patch_boundary", ""),
        br080_json.get("direct_engine_patch_boundary", ""),
        br081_json.get("direct_engine_patch_boundary", ""),
        br082_json.get("direct_engine_patch_boundary", ""),
    ]
    add_check(
        rows,
        owner_branch=owner_branch,
        audit_id=audit_id(),
        source_branch="BR-20260425-079..082",
        assumption_family="authorization_boundary",
        check_name="direct_engine_boundary_mentions_br076",
        expected_value="all payload boundaries mention BR-076 3-gate",
        actual_value=boundaries,
        ok=all("BR-076" in boundary and "3-gate" in boundary for boundary in boundaries),
        severity="P0",
        failure_impact="direct panel engine edit boundary could be weakened",
        required_action_if_failed="restore BR-076 3-gate boundary before any engine review",
    )

    return pd.DataFrame(rows, columns=AUDIT_COLUMNS)


def build_summary(owner_branch: str, audit_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (source_branch, family), group in audit_df.groupby(["source_branch", "assumption_family"], sort=False):
        rows.append(
            {
                "owner_branch": owner_branch,
                "source_branch": source_branch,
                "assumption_family": family,
                "total_checks": int(len(group)),
                "pass_count": int(group["audit_status"].eq("PASS").sum()),
                "warn_count": int(group["audit_status"].eq("WARN").sum()),
                "fail_count": int(group["audit_status"].eq("FAIL").sum()),
                "p0_fail_count": int((group["audit_status"].eq("FAIL") & group["severity"].eq("P0")).sum()),
                "operator_facing_change_allowed_sum": int(group["operator_facing_change_allowed"].sum()),
                "engine_patch_allowed_sum": int(group["engine_patch_allowed"].sum()),
                "threshold_patch_allowed_sum": int(group["threshold_patch_allowed"].sum()),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def build_action_queue(owner_branch: str, audit_df: pd.DataFrame) -> pd.DataFrame:
    failed = audit_df.loc[audit_df["audit_status"].eq("FAIL")]
    fail_count = int(len(failed))
    p0_fail_count = int((failed["severity"].eq("P0")).sum()) if not failed.empty else 0
    specs = [
        (
            "ACT-001",
            "block downstream truth/replay work if any P0 audit fails",
            "p0_fail_count > 0",
            "prevent a known direction error from becoming threshold or engine work",
            "P0 fail count is 0 before continuing",
            "panel_day_engine_direction_assumption_audit_v1",
            f"current p0_fail_count={p0_fail_count}",
        ),
        (
            "ACT-002",
            "if only P1 review-usability checks fail, repair packet ergonomics first",
            "fail_count > 0 and p0_fail_count == 0",
            "keep human review packet readable without changing semantics",
            "review ids and trace columns are stable",
            "panel_day_engine_episode_truth_review_packet_v1",
            f"current fail_count={fail_count}",
        ),
        (
            "ACT-003",
            "continue to reviewed episode truth rows only after all checks pass",
            "fail_count == 0",
            "attach evidence labels after the guard confirms the prior roadmap is consistent",
            "all checks pass and reviewer labels remain blank in BR-082",
            "panel_day_engine_reviewed_episode_truth_rows_v1",
            "manual evidence attachment or reviewed-truth-row builder comes next",
        ),
        (
            "ACT-004",
            "keep direct engine edits behind BR-076",
            "any direct panel_day_engine.py behavior proposal",
            "avoid treating review artifacts as production authorization",
            "BR-076 3-gate runbook passes before direct engine review",
            "check_panel_day_engine_algorithm_prepatch_runbook_v1.py",
            "passing gates are preconditions, not approval",
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
            "success_boundary": boundary,
            "recommended_next_artifact": artifact,
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": notes,
        }
        for idx, (action_id, action, input_filter, purpose, boundary, artifact, notes) in enumerate(specs, start=1)
    ]
    return pd.DataFrame(rows, columns=ACTION_COLUMNS)


def write_note(
    output_dir: Path,
    owner_branch: str,
    audit_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    action_df: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> None:
    fail_count = int(audit_df["audit_status"].eq("FAIL").sum())
    p0_fail_count = int((audit_df["audit_status"].eq("FAIL") & audit_df["severity"].eq("P0")).sum())
    note = f"""# Panel Day Engine Direction Assumption Audit V1

## Purpose
- Audit BR-079 through BR-082 before continuing to reviewed truth rows.
- Catch direction errors like bucket precedence drift, duplicate-lens confusion, premature truth assignment, or accidental patch authorization.
- Keep this audit guard-only: no engine patch, no threshold patch, and no operator-facing promotion.

## Outputs
- `{output_dir / AUDIT_OUTPUT_NAME}`
- `{output_dir / SUMMARY_OUTPUT_NAME}`
- `{output_dir / ACTION_OUTPUT_NAME}`
- `{output_dir / JSON_OUTPUT_NAME}`

## Result
- total checks: `{len(audit_df)}`
- pass count: `{int(audit_df["audit_status"].eq("PASS").sum())}`
- fail count: `{fail_count}`
- P0 fail count: `{p0_fail_count}`
- operator-facing change allowed sum: `{int(audit_df["operator_facing_change_allowed"].sum() + action_df["operator_facing_change_allowed"].sum())}`
- engine patch allowed sum: `{int(audit_df["engine_patch_allowed"].sum() + action_df["engine_patch_allowed"].sum())}`
- threshold patch allowed sum: `{int(audit_df["threshold_patch_allowed"].sum() + action_df["threshold_patch_allowed"].sum())}`
- evidence input manifest: `{input_manifest_path if input_manifest_path else 'not provided'}`

## Reading
- If `P0 fail count` is non-zero, stop before reviewed truth rows, threshold replay, or engine work.
- A pass means prior evidence/review scaffolding is internally consistent; it still does not approve production semantics.
- Direct `panel_day_engine.py` edits remain behind the BR-076 3-gate runbook.

## Input Resolution Sources
{chr(10).join(f"- `{key}`: `{value}`" for key, value in sorted((input_resolution_sources or {}).items())) if input_resolution_sources else "- no manifest-wrapped inputs"}

## Repro Command
```bash
python3 research/prognostics/build_panel_day_engine_direction_assumption_audit_v1.py --repo-root "$(pwd)" --output-dir {output_dir}
```
"""
    (output_dir / NOTE_OUTPUT_NAME).write_text(note, encoding="utf-8")


def build_outputs(
    repo_root: Path,
    output_dir: Path,
    owner_branch: str,
    br079_root: Path,
    br080_root: Path,
    br081_root: Path,
    br082_root: Path,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_df = build_audit(owner_branch, br079_root, br080_root, br081_root, br082_root)
    summary_df = build_summary(owner_branch, audit_df)
    action_df = build_action_queue(owner_branch, audit_df)

    audit_df.to_csv(output_dir / AUDIT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    input_resolution_sources = input_resolution_sources or {}
    write_note(output_dir, owner_branch, audit_df, summary_df, action_df, input_manifest_path, input_resolution_sources)

    fail_count = int(audit_df["audit_status"].eq("FAIL").sum())
    p0_fail_count = int((audit_df["audit_status"].eq("FAIL") & audit_df["severity"].eq("P0")).sum())
    payload = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "total_checks": int(len(audit_df)),
        "pass_count": int(audit_df["audit_status"].eq("PASS").sum()),
        "fail_count": fail_count,
        "p0_fail_count": p0_fail_count,
        "summary_rows": int(len(summary_df)),
        "action_rows": int(len(action_df)),
        "status_counts": {str(k): int(v) for k, v in audit_df["audit_status"].value_counts().items()},
        "source_branch_counts": {str(k): int(v) for k, v in audit_df["source_branch"].value_counts().items()},
        "operator_facing_change_allowed_sum": int(audit_df["operator_facing_change_allowed"].sum() + action_df["operator_facing_change_allowed"].sum()),
        "engine_patch_allowed_sum": int(audit_df["engine_patch_allowed"].sum() + action_df["engine_patch_allowed"].sum()),
        "threshold_patch_allowed_sum": int(audit_df["threshold_patch_allowed"].sum() + action_df["threshold_patch_allowed"].sum()),
        "input_manifest": str(input_manifest_path) if input_manifest_path else "",
        "input_resolution_sources": input_resolution_sources,
        "br079_root_source": input_resolution_sources.get("br079_root", ""),
        "br080_root_source": input_resolution_sources.get("br080_root", ""),
        "br081_root_source": input_resolution_sources.get("br081_root", ""),
        "br082_root_source": input_resolution_sources.get("br082_root", ""),
        "recommended_next_branch": "panel_day_engine_reviewed_episode_truth_rows_v1" if fail_count == 0 else "repair_direction_assumption_audit_failures_first",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "audit": str(output_dir / AUDIT_OUTPUT_NAME),
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
    parser.add_argument("--output-dir", type=Path, default=Path("/private/tmp/panel_day_engine_direction_assumption_audit_br083_check"))
    parser.add_argument("--owner-branch", default="BR-20260425-083")
    parser.add_argument("--input-manifest", default=None)
    parser.add_argument("--br079-root", type=Path, default=Path(BR079_ROOT_DEFAULT))
    parser.add_argument("--br080-root", type=Path, default=Path(BR080_ROOT_DEFAULT))
    parser.add_argument("--br081-root", type=Path, default=Path(BR081_ROOT_DEFAULT))
    parser.add_argument("--br082-root", type=Path, default=Path(BR082_ROOT_DEFAULT))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    input_manifest_path, input_manifest = load_input_manifest(repo_root, args.input_manifest)
    argv = sys.argv[1:]
    explicit_flags = {
        flag
        for flag in [
            "--br079-root",
            "--br080-root",
            "--br081-root",
            "--br082-root",
        ]
        if cli_flag_provided(flag, argv)
    }
    br079_root, br079_root_source = resolve_chain_input(
        repo_root,
        args.br079_root,
        BR079_ROOT_DEFAULT,
        input_manifest,
        "br079_root",
        "--br079-root",
        explicit_flags,
    )
    br080_root, br080_root_source = resolve_chain_input(
        repo_root,
        args.br080_root,
        BR080_ROOT_DEFAULT,
        input_manifest,
        "br080_root",
        "--br080-root",
        explicit_flags,
    )
    br081_root, br081_root_source = resolve_chain_input(
        repo_root,
        args.br081_root,
        BR081_ROOT_DEFAULT,
        input_manifest,
        "br081_root",
        "--br081-root",
        explicit_flags,
    )
    br082_root, br082_root_source = resolve_chain_input(
        repo_root,
        args.br082_root,
        BR082_ROOT_DEFAULT,
        input_manifest,
        "br082_root",
        "--br082-root",
        explicit_flags,
    )
    input_resolution_sources = {
        "br079_root": br079_root_source,
        "br080_root": br080_root_source,
        "br081_root": br081_root_source,
        "br082_root": br082_root_source,
    }
    payload = build_outputs(
        repo_root=repo_root,
        output_dir=args.output_dir,
        owner_branch=args.owner_branch,
        br079_root=br079_root,
        br080_root=br080_root,
        br081_root=br081_root,
        br082_root=br082_root,
        input_manifest_path=input_manifest_path,
        input_resolution_sources=input_resolution_sources,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
