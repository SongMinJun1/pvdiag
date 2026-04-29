#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pandas as pd


CASE_OUTPUT_NAME = "panel_day_engine_subtype_threshold_replay_pilot_cases_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_subtype_threshold_replay_pilot_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_subtype_threshold_replay_pilot_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_subtype_threshold_replay_pilot_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_subtype_threshold_replay_pilot_v1.json"

DEFAULT_SHAPE_INPUT = (
    "/private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check/"
    "panel_day_engine_episode_truth_durable_shape_review_v1.csv"
)
DEFAULT_REVIEWED_TRUTH_INPUT = (
    "/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br089_mixed_check/"
    "panel_day_engine_reviewed_episode_truth_rows_v1.csv"
)
DEFAULT_THRESHOLD_CANDIDATE_INPUT = "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_THRESHOLD_CANDIDATE_V1.csv"

SHAPE_REQUIRED_COLUMNS = [
    "shape_review_row_id",
    "shape_review_decision",
    "shape_confidence",
    "reviewer_truth_label",
    "reviewed_truth_row_id",
    "review_packet_id",
    "review_track",
    "site",
    "panel_id",
    "episode_anchor_date",
    "strict_trigger_date",
    "gap_days",
    "window_day_rows",
    "window_signal_days",
    "event_A_days",
    "low_mid_days",
    "voltage_low_current_ok_days",
    "hard_anchor_days",
    "common_cause_days",
    "data_bad_days",
    "median_signal_mid_v_ratio",
    "median_signal_mid_i_ratio",
    "positive_replay_candidate",
    "negative_replay_candidate",
    "threshold_replay_input_allowed_candidate",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

REVIEWED_TRUTH_REQUIRED_COLUMNS = [
    "reviewed_truth_row_id",
    "review_packet_id",
    "review_status",
    "truth_role",
    "threshold_replay_input_allowed",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

CASE_COLUMNS = [
    "owner_branch",
    "replay_case_row_id",
    "rule_id",
    "rule_axis",
    "rule_description",
    "rule_trigger_flag",
    "truth_partition",
    "review_status",
    "truth_role",
    "reviewer_truth_label",
    "shape_review_decision",
    "shape_confidence",
    "shape_review_row_id",
    "reviewed_truth_row_id",
    "review_packet_id",
    "review_track",
    "site",
    "panel_id",
    "episode_anchor_date",
    "strict_trigger_date",
    "gap_days",
    "rule_lead_days",
    "window_day_rows",
    "window_signal_days",
    "event_A_days",
    "low_mid_days",
    "voltage_low_current_ok_days",
    "hard_anchor_days",
    "common_cause_days",
    "data_bad_days",
    "median_signal_mid_v_ratio",
    "median_signal_mid_i_ratio",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "threshold_tuning_approved",
    "notes",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "rule_id",
    "rule_axis",
    "rule_description",
    "positive_truth_rows",
    "negative_truth_rows",
    "deferred_hold_rows",
    "true_positive_hits",
    "false_positive_hits",
    "false_negative_count",
    "true_negative_count",
    "deferred_hold_hits",
    "positive_hit_rate",
    "negative_hit_rate",
    "hold_pressure_rate",
    "precision_on_labeled",
    "recall_on_labeled",
    "f1_on_labeled",
    "pilot_decision",
    "threshold_tuning_approved",
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


def safe_div(numer: int | float, denom: int | float) -> float:
    return 0.0 if denom <= 0 else round(float(numer) / float(denom), 6)


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


def normalize_shape_input(shape_df: pd.DataFrame) -> pd.DataFrame:
    df = shape_df.copy()
    text_cols = [
        "shape_review_row_id",
        "shape_review_decision",
        "shape_confidence",
        "reviewer_truth_label",
        "reviewed_truth_row_id",
        "review_packet_id",
        "review_track",
        "site",
        "panel_id",
        "episode_anchor_date",
        "strict_trigger_date",
    ]
    for col in text_cols:
        df[col] = df[col].map(normalize_text)
    numeric_cols = [
        "gap_days",
        "window_day_rows",
        "window_signal_days",
        "event_A_days",
        "low_mid_days",
        "voltage_low_current_ok_days",
        "hard_anchor_days",
        "common_cause_days",
        "data_bad_days",
        "median_signal_mid_v_ratio",
        "median_signal_mid_i_ratio",
        "positive_replay_candidate",
        "negative_replay_candidate",
        "threshold_replay_input_allowed_candidate",
        "operator_facing_change_allowed",
        "engine_patch_allowed",
        "threshold_patch_allowed",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in [
        "positive_replay_candidate",
        "negative_replay_candidate",
        "threshold_replay_input_allowed_candidate",
        "operator_facing_change_allowed",
        "engine_patch_allowed",
        "threshold_patch_allowed",
    ]:
        df[col] = df[col].astype(int)
    return df


def normalize_reviewed_truth_input(rows_df: pd.DataFrame) -> pd.DataFrame:
    df = rows_df.copy()
    for col in ["reviewed_truth_row_id", "review_packet_id", "review_status", "truth_role"]:
        df[col] = df[col].map(normalize_text)
    for col in [
        "threshold_replay_input_allowed",
        "operator_facing_change_allowed",
        "engine_patch_allowed",
        "threshold_patch_allowed",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def assert_safe_inputs(shape_df: pd.DataFrame, truth_df: pd.DataFrame) -> None:
    for name, df, cols in [
        (
            "shape input",
            shape_df,
            ["operator_facing_change_allowed", "engine_patch_allowed", "threshold_patch_allowed"],
        ),
        (
            "reviewed truth input",
            truth_df,
            ["operator_facing_change_allowed", "engine_patch_allowed", "threshold_patch_allowed"],
        ),
    ]:
        for col in cols:
            total = int(df[col].sum())
            if total != 0:
                raise ValueError(f"BR-090 requires non-authorizing {name}; {col} sum is {total}")

    positive = int(shape_df["positive_replay_candidate"].sum())
    negative = int(shape_df["negative_replay_candidate"].sum())
    if positive <= 0 or negative <= 0:
        raise ValueError(
            "BR-090 pilot replay requires both positive and negative replay candidates from BR-089 mixed input"
        )

    shape_replay = int(shape_df["threshold_replay_input_allowed_candidate"].sum())
    truth_replay = int(truth_df["threshold_replay_input_allowed"].sum())
    if shape_replay != truth_replay:
        raise ValueError(
            f"shape replay candidate sum {shape_replay} does not match reviewed truth replay sum {truth_replay}"
        )

    shape_ids = set(shape_df.loc[shape_df["threshold_replay_input_allowed_candidate"].eq(1), "reviewed_truth_row_id"])
    truth_ids = set(truth_df.loc[truth_df["threshold_replay_input_allowed"].eq(1), "reviewed_truth_row_id"])
    if shape_ids != truth_ids:
        missing_shape = sorted(truth_ids - shape_ids)
        missing_truth = sorted(shape_ids - truth_ids)
        raise ValueError(
            "shape/reviewed truth replay row ids differ: "
            f"missing_shape={missing_shape}, missing_truth={missing_truth}"
        )


@dataclass(frozen=True)
class ReplayRule:
    rule_id: str
    axis: str
    description: str
    matcher: Callable[[pd.DataFrame], pd.Series]


def data_bad_limit(df: pd.DataFrame) -> pd.Series:
    return df["window_day_rows"].mul(0.05).round().clip(lower=1)


def build_rules() -> list[ReplayRule]:
    return [
        ReplayRule(
            "duration_gap_any_signal_2d",
            "duration+gap",
            "gap 7-120d, at least 2 signal days, and no common-cause days",
            lambda df: df["gap_days"].between(7, 120)
            & df["window_signal_days"].ge(2)
            & df["common_cause_days"].eq(0),
        ),
        ReplayRule(
            "duration_gap_eventA_2d",
            "duration+gap",
            "gap 7-120d, at least 2 event_A days, and no common-cause days",
            lambda df: df["gap_days"].between(7, 120)
            & df["event_A_days"].ge(2)
            & df["common_cause_days"].eq(0),
        ),
        ReplayRule(
            "severity_gap_low_mid_2d",
            "severity+gap",
            "gap 7-120d, at least 2 low-mid days, hard anchor, and no common-cause days",
            lambda df: df["gap_days"].between(7, 120)
            & df["low_mid_days"].ge(2)
            & df["hard_anchor_days"].ge(1)
            & df["common_cause_days"].eq(0),
        ),
        ReplayRule(
            "severity_gap_low_mid_10d",
            "severity+gap",
            "gap 7-120d, at least 10 low-mid days, hard anchor, and no common-cause days",
            lambda df: df["gap_days"].between(7, 120)
            & df["low_mid_days"].ge(10)
            & df["hard_anchor_days"].ge(1)
            & df["common_cause_days"].eq(0),
        ),
        ReplayRule(
            "voltage_preserved_gap_vlow_iok_2d",
            "voltage-preserved-shape",
            "gap 7-120d, at least 2 voltage-low/current-preserved days, hard anchor, and no common-cause days",
            lambda df: df["gap_days"].between(7, 120)
            & df["voltage_low_current_ok_days"].ge(2)
            & df["hard_anchor_days"].ge(1)
            & df["common_cause_days"].eq(0),
        ),
        ReplayRule(
            "voltage_preserved_gap_vlow_iok_10d",
            "voltage-preserved-shape",
            "gap 7-120d, at least 10 voltage-low/current-preserved days, hard anchor, and no common-cause days",
            lambda df: df["gap_days"].between(7, 120)
            & df["voltage_low_current_ok_days"].ge(10)
            & df["hard_anchor_days"].ge(1)
            & df["common_cause_days"].eq(0),
        ),
        ReplayRule(
            "br089_strong_voltage_seed_rule",
            "voltage-preserved-shape",
            "BR-089 strong positive seed rule with event, low-mid, voltage-preserved, anchor, common-cause, and data-quality gates",
            lambda df: df["window_day_rows"].ge(14)
            & df["event_A_days"].ge(10)
            & df["low_mid_days"].ge(10)
            & df["voltage_low_current_ok_days"].ge(10)
            & df["hard_anchor_days"].ge(1)
            & df["common_cause_days"].eq(0)
            & df["data_bad_days"].le(data_bad_limit(df))
            & df["median_signal_mid_v_ratio"].lt(0.75)
            & df["median_signal_mid_i_ratio"].ge(0.85),
        ),
    ]


def truth_partition(row: pd.Series) -> str:
    if numeric_int(row.get("positive_replay_candidate")) == 1:
        return "positive"
    if numeric_int(row.get("negative_replay_candidate")) == 1:
        return "negative"
    return "deferred_hold"


def build_cases(owner_branch: str, shape_df: pd.DataFrame, truth_df: pd.DataFrame) -> pd.DataFrame:
    truth_cols = ["reviewed_truth_row_id", "review_status", "truth_role"]
    merged = shape_df.merge(truth_df.loc[:, truth_cols], on="reviewed_truth_row_id", how="left")
    rows: list[dict[str, object]] = []
    for rule_idx, rule in enumerate(build_rules(), start=1):
        trigger = rule.matcher(merged).fillna(False).astype(bool)
        for row_idx, row in enumerate(merged.to_dict(orient="records"), start=1):
            partition = truth_partition(pd.Series(row))
            rule_trigger_flag = int(trigger.iloc[row_idx - 1])
            rows.append(
                {
                    "owner_branch": owner_branch,
                    "replay_case_row_id": f"BR090-RC-{rule_idx:02d}-{row_idx:03d}",
                    "rule_id": rule.rule_id,
                    "rule_axis": rule.axis,
                    "rule_description": rule.description,
                    "rule_trigger_flag": rule_trigger_flag,
                    "truth_partition": partition,
                    "review_status": normalize_text(row.get("review_status")),
                    "truth_role": normalize_text(row.get("truth_role")),
                    "reviewer_truth_label": normalize_text(row.get("reviewer_truth_label")),
                    "shape_review_decision": normalize_text(row.get("shape_review_decision")),
                    "shape_confidence": normalize_text(row.get("shape_confidence")),
                    "shape_review_row_id": normalize_text(row.get("shape_review_row_id")),
                    "reviewed_truth_row_id": normalize_text(row.get("reviewed_truth_row_id")),
                    "review_packet_id": normalize_text(row.get("review_packet_id")),
                    "review_track": normalize_text(row.get("review_track")),
                    "site": normalize_text(row.get("site")),
                    "panel_id": normalize_text(row.get("panel_id")),
                    "episode_anchor_date": normalize_text(row.get("episode_anchor_date")),
                    "strict_trigger_date": normalize_text(row.get("strict_trigger_date")),
                    "gap_days": numeric_int(row.get("gap_days")),
                    "rule_lead_days": numeric_int(row.get("gap_days")) if partition == "positive" and rule_trigger_flag else "",
                    "window_day_rows": numeric_int(row.get("window_day_rows")),
                    "window_signal_days": numeric_int(row.get("window_signal_days")),
                    "event_A_days": numeric_int(row.get("event_A_days")),
                    "low_mid_days": numeric_int(row.get("low_mid_days")),
                    "voltage_low_current_ok_days": numeric_int(row.get("voltage_low_current_ok_days")),
                    "hard_anchor_days": numeric_int(row.get("hard_anchor_days")),
                    "common_cause_days": numeric_int(row.get("common_cause_days")),
                    "data_bad_days": numeric_int(row.get("data_bad_days")),
                    "median_signal_mid_v_ratio": round(numeric_float(row.get("median_signal_mid_v_ratio")), 6),
                    "median_signal_mid_i_ratio": round(numeric_float(row.get("median_signal_mid_i_ratio")), 6),
                    "operator_facing_change_allowed": 0,
                    "engine_patch_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "threshold_tuning_approved": 0,
                    "notes": "BR-090 pilot replay only; no threshold tuning or runtime patch approval.",
                }
            )
    return pd.DataFrame(rows).reindex(columns=CASE_COLUMNS)


def classify_rule(
    positive_count: int,
    false_positive_hits: int,
    false_negative_count: int,
    deferred_hold_hits: int,
) -> tuple[str, str]:
    if false_positive_hits > 0:
        return (
            "blocked_negative_counterexample_hits",
            "rule hits reviewed negative counterexamples; do not tune",
        )
    if deferred_hold_hits > 0:
        return (
            "blocked_hold_pressure_and_insufficient_support",
            "rule hits still-unassigned durable holds; collect or adjudicate more evidence first",
        )
    if false_negative_count > 0:
        return (
            "blocked_misses_positive_seed",
            "rule misses the only current positive seed",
        )
    if positive_count < 3:
        return (
            "pilot_candidate_collect_more_positive_truth",
            "clean on this tiny labeled set, but positive support is below approval threshold",
        )
    return (
        "pilot_candidate_requires_external_validation",
        "clean pilot candidate, but still needs fresh tri-site replay and BR-076 gates",
    )


def build_summary(owner_branch: str, cases_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for rule_id, group in cases_df.groupby("rule_id", sort=False):
        rule_axis = normalize_text(group["rule_axis"].iloc[0])
        rule_description = normalize_text(group["rule_description"].iloc[0])
        positives = group.loc[group["truth_partition"].eq("positive")].copy()
        negatives = group.loc[group["truth_partition"].eq("negative")].copy()
        holds = group.loc[group["truth_partition"].eq("deferred_hold")].copy()

        tp = int(positives["rule_trigger_flag"].sum())
        fp = int(negatives["rule_trigger_flag"].sum())
        fn = int(len(positives) - tp)
        tn = int(len(negatives) - fp)
        hold_hits = int(holds["rule_trigger_flag"].sum())
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, len(positives))
        f1 = 0.0 if precision + recall == 0 else round(2 * precision * recall / (precision + recall), 6)
        decision, notes = classify_rule(len(positives), fp, fn, hold_hits)

        rows.append(
            {
                "owner_branch": owner_branch,
                "rule_id": rule_id,
                "rule_axis": rule_axis,
                "rule_description": rule_description,
                "positive_truth_rows": int(len(positives)),
                "negative_truth_rows": int(len(negatives)),
                "deferred_hold_rows": int(len(holds)),
                "true_positive_hits": tp,
                "false_positive_hits": fp,
                "false_negative_count": fn,
                "true_negative_count": tn,
                "deferred_hold_hits": hold_hits,
                "positive_hit_rate": safe_div(tp, len(positives)),
                "negative_hit_rate": safe_div(fp, len(negatives)),
                "hold_pressure_rate": safe_div(hold_hits, len(holds)),
                "precision_on_labeled": precision,
                "recall_on_labeled": recall,
                "f1_on_labeled": f1,
                "pilot_decision": decision,
                "threshold_tuning_approved": 0,
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "notes": notes,
            }
        )
    return pd.DataFrame(rows).reindex(columns=SUMMARY_COLUMNS)


def build_action_queue(owner_branch: str, summary_df: pd.DataFrame) -> pd.DataFrame:
    clean_candidates = ",".join(
        summary_df.loc[
            summary_df["pilot_decision"].eq("pilot_candidate_collect_more_positive_truth"),
            "rule_id",
        ].tolist()
    )
    rows = [
        {
            "owner_branch": owner_branch,
            "sequence": 1,
            "action_id": "BR090-ACT-001",
            "action": "collect more positive durable precursor truth for clean pilot candidates",
            "input_filter": f"pilot_candidate_collect_more_positive_truth: {clean_candidates}",
            "purpose": "test whether voltage-preserved/severity candidates generalize beyond one positive seed",
            "success_boundary": "at least 3 independent positives and no negative or hold-pressure drift",
            "recommended_next_artifact": "panel_day_engine_subtype_threshold_replay_expanded_truth_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "BR-090 identifies evidence direction only; it does not approve tuning.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 2,
            "action_id": "BR090-ACT-002",
            "action": "keep broad duration/event-only rules blocked",
            "input_filter": "pilot_decision=blocked_hold_pressure_and_insufficient_support",
            "purpose": "avoid promoting unadjudicated durable holds as positives",
            "success_boundary": "duration-only rules remain off until hold rows are adjudicated",
            "recommended_next_artifact": "durable_shape_hold_raw_waveform_review",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Hold pressure is the practical false-positive proxy while labels are sparse.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 3,
            "action_id": "BR090-ACT-003",
            "action": "preserve direct engine patch gate",
            "input_filter": "all BR-090 outputs",
            "purpose": "keep pilot replay separated from runtime semantics",
            "success_boundary": "operator/engine/threshold patch sums remain 0",
            "recommended_next_artifact": "BR-076 3-gate prepatch runbook only after stronger replay evidence",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "No direct panel_day_engine.py edit follows from BR-090 alone.",
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
    reviewed_truth_input: Path,
    threshold_candidate_input: Path,
    cases_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> None:
    compact_cols = [
        "rule_id",
        "rule_axis",
        "true_positive_hits",
        "false_positive_hits",
        "false_negative_count",
        "deferred_hold_hits",
        "pilot_decision",
    ]
    compact_summary = summary_df.loc[:, compact_cols].copy()
    lines = [
        "# panel_day_engine_subtype_threshold_replay_pilot_v1",
        "",
        "## Purpose",
        "- Replay fixed subtype-threshold candidates against the BR-089 mixed truth input.",
        "- Count labeled performance and deferred-hold pressure separately.",
        "- Keep threshold tuning and direct engine patches blocked.",
        "",
        "## Inputs",
        f"- BR-089 shape review: `{shape_input}`",
        f"- BR-084 mixed reviewed truth rows: `{reviewed_truth_input}`",
        f"- BR-017 threshold candidate axes: `{threshold_candidate_input}`",
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
        f"- replay case rows: `{len(cases_df)}`",
        f"- summary rows: `{len(summary_df)}`",
        f"- threshold tuning approved sum: `{int(summary_df['threshold_tuning_approved'].sum())}`",
        f"- operator-facing change allowed sum: `{int(summary_df['operator_facing_change_allowed'].sum())}`",
        f"- engine patch allowed sum: `{int(summary_df['engine_patch_allowed'].sum())}`",
        f"- threshold patch allowed sum: `{int(summary_df['threshold_patch_allowed'].sum())}`",
        "",
        "## Compact Summary",
        dataframe_to_markdown(compact_summary),
        "",
        "## Safety Boundary",
        "- BR-090 is a pilot replay review, not threshold tuning.",
        "- One positive seed is not enough to approve a generalized threshold.",
        "- Deferred hold hits are treated as ambiguity pressure, not as positives.",
        "- Direct `panel_day_engine.py` edits remain blocked by the BR-076 3-gate prepatch runbook.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(
    path: Path,
    owner_branch: str,
    repo_root: Path,
    output_dir: Path,
    shape_input: Path,
    reviewed_truth_input: Path,
    threshold_candidate_input: Path,
    cases_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> None:
    payload = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "shape_input": str(shape_input),
        "reviewed_truth_input": str(reviewed_truth_input),
        "threshold_candidate_input": str(threshold_candidate_input),
        "input_manifest": str(input_manifest_path) if input_manifest_path else "not provided",
        "input_resolution_sources": input_resolution_sources or {},
        "case_rows": int(len(cases_df)),
        "summary_rows": int(len(summary_df)),
        "threshold_tuning_approved_sum": int(summary_df["threshold_tuning_approved"].sum())
        if not summary_df.empty
        else 0,
        "operator_facing_change_allowed_sum": int(summary_df["operator_facing_change_allowed"].sum())
        if not summary_df.empty
        else 0,
        "engine_patch_allowed_sum": int(summary_df["engine_patch_allowed"].sum()) if not summary_df.empty else 0,
        "threshold_patch_allowed_sum": int(summary_df["threshold_patch_allowed"].sum()) if not summary_df.empty else 0,
        "pilot_decision_counts": summary_df["pilot_decision"].value_counts().sort_index().to_dict()
        if not summary_df.empty
        else {},
        "recommended_next_branch": "expand_positive_truth_for_voltage_preserved_candidates_before_tuning",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "cases": str(output_dir / CASE_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pilot subtype-threshold replay against BR-089 mixed truth rows.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--input-manifest", default=None)
    parser.add_argument("--shape-input", default=DEFAULT_SHAPE_INPUT, help="BR-089 durable shape review CSV.")
    parser.add_argument(
        "--reviewed-truth-input",
        default=DEFAULT_REVIEWED_TRUTH_INPUT,
        help="BR-084 mixed reviewed truth rows CSV.",
    )
    parser.add_argument(
        "--threshold-candidate-input",
        default=DEFAULT_THRESHOLD_CANDIDATE_INPUT,
        help="BR-017 threshold candidate axis CSV for provenance.",
    )
    parser.add_argument(
        "--output-dir",
        default="/private/tmp/panel_day_engine_subtype_threshold_replay_pilot_br090_check",
        help="Output directory for BR-090 artifacts.",
    )
    parser.add_argument("--owner-branch", default="BR-20260425-090")
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
            "--reviewed-truth-input",
        ]
        if cli_flag_provided(flag, argv)
    }
    shape_input, shape_source = resolve_chain_input(
        repo_root,
        args.shape_input,
        DEFAULT_SHAPE_INPUT,
        input_manifest,
        "shape_input",
        "--shape-input",
        explicit_flags,
    )
    reviewed_truth_input, reviewed_truth_source = resolve_chain_input(
        repo_root,
        args.reviewed_truth_input,
        DEFAULT_REVIEWED_TRUTH_INPUT,
        input_manifest,
        "reviewed_truth_input",
        "--reviewed-truth-input",
        explicit_flags,
    )
    input_resolution_sources = {
        "reviewed_truth_input": reviewed_truth_source,
        "shape_input": shape_source,
    }
    threshold_candidate_input = resolve_path(repo_root, args.threshold_candidate_input)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    shape_df = normalize_shape_input(read_required_csv(shape_input, SHAPE_REQUIRED_COLUMNS, "BR-089 shape review"))
    truth_df = normalize_reviewed_truth_input(
        read_required_csv(reviewed_truth_input, REVIEWED_TRUTH_REQUIRED_COLUMNS, "BR-084 mixed reviewed truth")
    )
    read_required_csv(threshold_candidate_input, ["axis", "feature", "promote_candidate", "hold_or_block"], "BR-017 threshold candidate axes")
    assert_safe_inputs(shape_df, truth_df)

    cases_df = build_cases(args.owner_branch, shape_df, truth_df)
    summary_df = build_summary(args.owner_branch, cases_df)
    action_df = build_action_queue(args.owner_branch, summary_df)

    cases_df.to_csv(output_dir / CASE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(
        output_dir / NOTE_OUTPUT_NAME,
        args.owner_branch,
        shape_input,
        reviewed_truth_input,
        threshold_candidate_input,
        cases_df,
        summary_df,
        input_manifest_path,
        input_resolution_sources,
    )
    write_json(
        output_dir / JSON_OUTPUT_NAME,
        args.owner_branch,
        repo_root,
        output_dir,
        shape_input,
        reviewed_truth_input,
        threshold_candidate_input,
        cases_df,
        summary_df,
        input_manifest_path,
        input_resolution_sources,
    )

    print(
        json.dumps(
            {
                "owner_branch": args.owner_branch,
                "case_rows": int(len(cases_df)),
                "summary_rows": int(len(summary_df)),
                "threshold_tuning_approved_sum": int(summary_df["threshold_tuning_approved"].sum()),
                "pilot_decision_counts": summary_df["pilot_decision"].value_counts().sort_index().to_dict(),
                "outputs": {
                    "cases": str(output_dir / CASE_OUTPUT_NAME),
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
