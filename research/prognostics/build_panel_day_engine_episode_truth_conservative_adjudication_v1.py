#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ADJUDICATION_OUTPUT_NAME = "panel_day_engine_episode_truth_conservative_adjudication_v1.csv"
REVIEW_INPUT_OUTPUT_NAME = "panel_day_engine_episode_truth_review_input_conservative_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_episode_truth_conservative_adjudication_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_episode_truth_conservative_adjudication_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_episode_truth_conservative_adjudication_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_episode_truth_conservative_adjudication_v1.json"

BR087_WORKSHEET_DEFAULT = (
    "/private/tmp/panel_day_engine_episode_truth_adjudication_worksheet_br087_check/"
    "panel_day_engine_episode_truth_adjudication_worksheet_v1.csv"
)

REQUIRED_WORKSHEET_COLUMNS = [
    "worksheet_row_id",
    "adjudication_status",
    "suggested_review_direction",
    "reviewed_truth_row_id",
    "review_packet_id",
    "review_priority",
    "review_track",
    "episode_truth_bucket",
    "site",
    "panel_id",
    "family_key",
    "subtype_key",
    "episode_anchor_date",
    "strict_trigger_date",
    "gap_days",
    "signal_day_count",
    "common_cause_flag_sum",
    "strict_trigger_proximal_common_cause_flag",
    "source_reference_count",
    "trace_ready_all",
    "source_gap_days_min",
    "source_gap_days_max",
    "source_episode_classes",
    "source_precursor_promotion_decisions",
    "source_shadow_reasons",
    "source_references",
    "evidence_card_path",
    "evidence_card_exists",
    "must_prove_axes",
    "must_reject_axes",
    "candidate_reading",
    "default_review_disposition",
    "allowed_reviewer_truth_labels",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "threshold_replay_input_allowed",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

ADJUDICATION_COLUMNS = [
    "owner_branch",
    "adjudication_row_id",
    "conservative_decision",
    "decision_confidence",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "reviewer_notes",
    "br084_expected_review_status",
    "br084_expected_truth_role",
    "threshold_replay_input_allowed_candidate",
    "positive_replay_candidate",
    "negative_replay_candidate",
    "defer_reason",
    "worksheet_row_id",
    "reviewed_truth_row_id",
    "review_packet_id",
    "review_priority",
    "review_track",
    "episode_truth_bucket",
    "site",
    "panel_id",
    "family_key",
    "subtype_key",
    "episode_anchor_date",
    "strict_trigger_date",
    "gap_days",
    "signal_day_count",
    "common_cause_flag_sum",
    "strict_trigger_proximal_common_cause_flag",
    "source_reference_count",
    "trace_ready_all",
    "source_gap_days_min",
    "source_gap_days_max",
    "source_episode_classes",
    "source_precursor_promotion_decisions",
    "source_shadow_reasons",
    "source_references",
    "evidence_card_path",
    "evidence_card_exists",
    "must_prove_axes",
    "must_reject_axes",
    "candidate_reading",
    "default_review_disposition",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

REVIEW_INPUT_COLUMNS = [
    "review_packet_id",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "reviewer_notes",
    "reviewed_truth_row_id",
    "adjudication_row_id",
    "conservative_decision",
    "decision_confidence",
    "evidence_card_path",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "review_track",
    "site",
    "rows",
    "filled_negative_rows",
    "filled_positive_rows",
    "deferred_rows",
    "threshold_replay_input_allowed_candidate_sum",
    "positive_replay_candidate_sum",
    "negative_replay_candidate_sum",
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


def assert_safe_input(worksheet_df: pd.DataFrame) -> None:
    for col in ["operator_facing_change_allowed", "engine_patch_allowed", "threshold_patch_allowed"]:
        total = int(worksheet_df[col].map(numeric_int).sum())
        if total != 0:
            raise ValueError(f"BR-088 requires non-authorizing worksheet input; {col} sum is {total}")
    existing_labels = int(worksheet_df["reviewer_truth_label"].map(normalize_text).astype(bool).sum())
    existing_paths = int(worksheet_df["reviewer_evidence_path"].map(normalize_text).astype(bool).sum())
    replay_sum = int(worksheet_df["threshold_replay_input_allowed"].map(numeric_int).sum())
    if existing_labels or existing_paths or replay_sum:
        raise ValueError(
            "BR-088 must start from guidance-only BR-087 rows: "
            f"label_count={existing_labels}, evidence_path_count={existing_paths}, replay_sum={replay_sum}"
        )


def has_token(value: object, token: str) -> bool:
    return token in normalize_text(value)


def evidence_card_ready(row: dict[str, object]) -> bool:
    path = normalize_text(row.get("evidence_card_path"))
    return bool(path) and int(numeric_int(row.get("evidence_card_exists"))) == 1 and Path(path).exists()


def decide_row(row: dict[str, object]) -> dict[str, object]:
    review_track = normalize_text(row.get("review_track"))
    suggested_direction = normalize_text(row.get("suggested_review_direction"))
    source_decisions = normalize_text(row.get("source_precursor_promotion_decisions"))
    source_classes = normalize_text(row.get("source_episode_classes"))
    source_gap_min = numeric_int(row.get("source_gap_days_min"))
    source_gap_max = numeric_int(row.get("source_gap_days_max"))
    signal_day_count = numeric_int(row.get("signal_day_count"))
    trace_ready_all = numeric_int(row.get("trace_ready_all"))
    card_ready = evidence_card_ready(row)

    if not trace_ready_all:
        return {
            "decision": "defer_trace_not_ready",
            "confidence": "blocked",
            "label": "",
            "evidence_path": "",
            "notes": "",
            "status": "needs_evidence",
            "truth_role": "unassigned",
            "replay": 0,
            "positive": 0,
            "negative": 0,
            "defer_reason": "source trace is not fully ready",
        }
    if not card_ready:
        return {
            "decision": "defer_missing_evidence_card",
            "confidence": "blocked",
            "label": "",
            "evidence_path": "",
            "notes": "",
            "status": "needs_evidence",
            "truth_role": "unassigned",
            "replay": 0,
            "positive": 0,
            "negative": 0,
            "defer_reason": "evidence card path is missing or not readable",
        }

    long_gap_negative = (
        review_track == "long_gap_backdating_review"
        and suggested_direction == "negative_or_hold_candidate"
        and has_token(source_decisions, "block_precursor_backdating")
        and has_token(source_classes, "long_gap_one_day_episode_hold")
        and source_gap_min >= 120
        and source_gap_max >= 120
    )
    if long_gap_negative:
        return {
            "decision": "fill_conservative_negative_long_gap_backdating",
            "confidence": "source_backed_negative_counterexample",
            "label": "episode_only_or_backdating",
            "evidence_path": normalize_text(row.get("evidence_card_path")),
            "notes": (
                "BR-088 conservative negative: BR-087/BR-086 show block_precursor_backdating, "
                f"long gap {source_gap_min}-{source_gap_max}d, and long_gap_one_day_episode_hold; "
                "do not treat as real precursor without extra continuity evidence."
            ),
            "status": "reviewed_negative",
            "truth_role": "negative_counterexample",
            "replay": 1,
            "positive": 0,
            "negative": 1,
            "defer_reason": "",
        }

    strict_sudden_negative = (
        review_track == "strict_sudden_prior_episode_review"
        and suggested_direction == "strict_sudden_negative_candidate"
        and has_token(source_decisions, "no_precursor_promotion")
        and has_token(source_classes, "sudden_fault_strict_anchor")
        and source_gap_min == 0
        and source_gap_max == 0
        and signal_day_count == 0
    )
    if strict_sudden_negative:
        return {
            "decision": "fill_conservative_negative_strict_sudden",
            "confidence": "source_backed_negative_counterexample",
            "label": "strict_sudden_no_precursor",
            "evidence_path": normalize_text(row.get("evidence_card_path")),
            "notes": (
                "BR-088 conservative negative: BR-087/BR-086 show no_precursor_promotion, "
                "gap 0d, signal_day_count 0, and sudden_fault_strict_anchor; "
                "do not treat as precursor without a validated prior episode."
            ),
            "status": "reviewed_negative",
            "truth_role": "negative_counterexample",
            "replay": 1,
            "positive": 0,
            "negative": 1,
            "defer_reason": "",
        }

    return {
        "decision": "defer_positive_or_hold_review",
        "confidence": "needs_family_shape_adjudication",
        "label": "",
        "evidence_path": "",
        "notes": "",
        "status": "needs_evidence",
        "truth_role": "unassigned",
        "replay": 0,
        "positive": 0,
        "negative": 0,
        "defer_reason": (
            "possible durable precursor, but BR-088 does not assign positive labels without "
            "family-shape match, same-panel continuity, and common-cause rejection evidence"
        ),
    }


def build_adjudication(owner_branch: str, worksheet_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    adjudication_rows: list[dict[str, object]] = []
    review_rows: list[dict[str, object]] = []
    for idx, row in enumerate(worksheet_df.to_dict(orient="records"), start=1):
        decision = decide_row(row)
        adjudication_row_id = f"BR088-CADJ-{idx:03d}"
        base = {
            "owner_branch": owner_branch,
            "adjudication_row_id": adjudication_row_id,
            "conservative_decision": decision["decision"],
            "decision_confidence": decision["confidence"],
            "reviewer_truth_label": decision["label"],
            "reviewer_evidence_path": decision["evidence_path"],
            "reviewer_notes": decision["notes"],
            "br084_expected_review_status": decision["status"],
            "br084_expected_truth_role": decision["truth_role"],
            "threshold_replay_input_allowed_candidate": decision["replay"],
            "positive_replay_candidate": decision["positive"],
            "negative_replay_candidate": decision["negative"],
            "defer_reason": decision["defer_reason"],
            "worksheet_row_id": normalize_text(row.get("worksheet_row_id")),
            "reviewed_truth_row_id": normalize_text(row.get("reviewed_truth_row_id")),
            "review_packet_id": normalize_text(row.get("review_packet_id")),
            "review_priority": normalize_text(row.get("review_priority")),
            "review_track": normalize_text(row.get("review_track")),
            "episode_truth_bucket": normalize_text(row.get("episode_truth_bucket")),
            "site": normalize_text(row.get("site")),
            "panel_id": normalize_text(row.get("panel_id")),
            "family_key": normalize_text(row.get("family_key")),
            "subtype_key": normalize_text(row.get("subtype_key")),
            "episode_anchor_date": normalize_text(row.get("episode_anchor_date")),
            "strict_trigger_date": normalize_text(row.get("strict_trigger_date")),
            "gap_days": numeric_int(row.get("gap_days")),
            "signal_day_count": numeric_int(row.get("signal_day_count")),
            "common_cause_flag_sum": numeric_int(row.get("common_cause_flag_sum")),
            "strict_trigger_proximal_common_cause_flag": numeric_int(
                row.get("strict_trigger_proximal_common_cause_flag")
            ),
            "source_reference_count": numeric_int(row.get("source_reference_count")),
            "trace_ready_all": numeric_int(row.get("trace_ready_all")),
            "source_gap_days_min": numeric_int(row.get("source_gap_days_min")),
            "source_gap_days_max": numeric_int(row.get("source_gap_days_max")),
            "source_episode_classes": normalize_text(row.get("source_episode_classes")),
            "source_precursor_promotion_decisions": normalize_text(row.get("source_precursor_promotion_decisions")),
            "source_shadow_reasons": normalize_text(row.get("source_shadow_reasons")),
            "source_references": normalize_text(row.get("source_references")),
            "evidence_card_path": normalize_text(row.get("evidence_card_path")),
            "evidence_card_exists": numeric_int(row.get("evidence_card_exists")),
            "must_prove_axes": normalize_text(row.get("must_prove_axes")),
            "must_reject_axes": normalize_text(row.get("must_reject_axes")),
            "candidate_reading": normalize_text(row.get("candidate_reading")),
            "default_review_disposition": normalize_text(row.get("default_review_disposition")),
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": (
                "BR-088 fills conservative negative labels only; deferred rows remain out of replay until manual review."
            ),
        }
        adjudication_rows.append(base)
        review_rows.append(
            {
                "review_packet_id": base["review_packet_id"],
                "reviewer_truth_label": decision["label"],
                "reviewer_evidence_path": decision["evidence_path"],
                "reviewer_notes": decision["notes"],
                "reviewed_truth_row_id": base["reviewed_truth_row_id"],
                "adjudication_row_id": adjudication_row_id,
                "conservative_decision": decision["decision"],
                "decision_confidence": decision["confidence"],
                "evidence_card_path": base["evidence_card_path"],
            }
        )
    return (
        pd.DataFrame(adjudication_rows).reindex(columns=ADJUDICATION_COLUMNS),
        pd.DataFrame(review_rows).reindex(columns=REVIEW_INPUT_COLUMNS),
    )


def build_summary(owner_branch: str, adjudication_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if adjudication_df.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    for (review_track, site), group in adjudication_df.groupby(["review_track", "site"], dropna=False, sort=True):
        rows.append(
            {
                "owner_branch": owner_branch,
                "review_track": review_track,
                "site": site,
                "rows": int(len(group)),
                "filled_negative_rows": int(group["negative_replay_candidate"].sum()),
                "filled_positive_rows": int(group["positive_replay_candidate"].sum()),
                "deferred_rows": int((group["conservative_decision"] == "defer_positive_or_hold_review").sum()),
                "threshold_replay_input_allowed_candidate_sum": int(
                    group["threshold_replay_input_allowed_candidate"].sum()
                ),
                "positive_replay_candidate_sum": int(group["positive_replay_candidate"].sum()),
                "negative_replay_candidate_sum": int(group["negative_replay_candidate"].sum()),
                "operator_facing_change_allowed_sum": int(group["operator_facing_change_allowed"].sum()),
                "engine_patch_allowed_sum": int(group["engine_patch_allowed"].sum()),
                "threshold_patch_allowed_sum": int(group["threshold_patch_allowed"].sum()),
            }
        )
    return pd.DataFrame(rows).reindex(columns=SUMMARY_COLUMNS)


def build_action_queue(owner_branch: str) -> pd.DataFrame:
    rows = [
        {
            "owner_branch": owner_branch,
            "sequence": 1,
            "action_id": "BR088-ACT-001",
            "action": "rebuild BR-084 with conservative review input",
            "input_filter": "reviewer_truth_label in negative labels only",
            "purpose": "materialize source-backed negative counterexamples while leaving positives unassigned",
            "success_boundary": "BR-084 reports reviewed_negative rows and zero reviewed_positive rows",
            "recommended_next_artifact": "panel_day_engine_reviewed_episode_truth_rows_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "negative-only replay rows do not authorize threshold tuning",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 2,
            "action_id": "BR088-ACT-002",
            "action": "manually adjudicate deferred durable precursor rows",
            "input_filter": "conservative_decision=defer_positive_or_hold_review",
            "purpose": "look for positive precursor evidence without forcing labels from weak guidance",
            "success_boundary": "positive labels require family-shape match, continuity, anchor relation, and common-cause rejection",
            "recommended_next_artifact": "filled_positive_episode_truth_review_input",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "threshold replay remains blocked until positive and negative rows both exist",
        },
    ]
    return pd.DataFrame(rows).reindex(columns=ACTION_COLUMNS)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_empty_"
    cols = [str(col) for col in df.columns]
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for row in df.to_dict(orient="records"):
        values = [normalize_text(row.get(col)) for col in df.columns]
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in values) + " |")
    return "\n".join(lines)


def write_note(
    path: Path,
    owner_branch: str,
    worksheet_input: Path,
    adjudication_df: pd.DataFrame,
    review_input_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    decision_counts = adjudication_df["conservative_decision"].value_counts().sort_index().to_dict()
    lines = [
        "# panel_day_engine_episode_truth_conservative_adjudication_v1",
        "",
        "## Purpose",
        "- Convert only source-backed negative counterexamples from BR-087 into a BR-084 review input.",
        "- Keep all possible durable precursor rows deferred until a human can prove family-shape continuity.",
        "- Do not create positive labels, threshold replay approval, or engine patch authorization.",
        "",
        "## Input",
        f"- BR-087 worksheet: `{worksheet_input}`",
        "",
        "## Real Result",
        f"- owner_branch: `{owner_branch}`",
        f"- adjudication rows: `{len(adjudication_df)}`",
        f"- conservative review input rows: `{len(review_input_df)}`",
        f"- filled negative labels: `{int(adjudication_df['negative_replay_candidate'].sum())}`",
        f"- filled positive labels: `{int(adjudication_df['positive_replay_candidate'].sum())}`",
        f"- deferred rows: `{int((adjudication_df['conservative_decision'] == 'defer_positive_or_hold_review').sum())}`",
        f"- threshold replay input candidate rows: `{int(adjudication_df['threshold_replay_input_allowed_candidate'].sum())}`",
        "- threshold tuning approved: `0`",
        "- operator-facing change allowed sum: `0`",
        "- engine patch allowed sum: `0`",
        "- threshold patch allowed sum: `0`",
        "",
        "## Decision Counts",
    ]
    for key, value in decision_counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Summary",
            dataframe_to_markdown(summary_df),
            "",
            "## Safety Boundary",
            "- BR-088 creates negative counterexample review-input rows only.",
            "- It creates zero positive precursor labels.",
            "- Negative-only replay candidates are not enough for threshold replay or algorithm tuning.",
            "- Direct `panel_day_engine.py` edits remain blocked by the BR-076 3-gate prepatch runbook.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(
    path: Path,
    owner_branch: str,
    repo_root: Path,
    output_dir: Path,
    worksheet_input: Path,
    adjudication_df: pd.DataFrame,
    review_input_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    payload = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "worksheet_input": str(worksheet_input),
        "adjudication_rows": int(len(adjudication_df)),
        "review_input_rows": int(len(review_input_df)),
        "filled_negative_rows": int(adjudication_df["negative_replay_candidate"].sum())
        if not adjudication_df.empty
        else 0,
        "filled_positive_rows": int(adjudication_df["positive_replay_candidate"].sum())
        if not adjudication_df.empty
        else 0,
        "deferred_rows": int((adjudication_df["conservative_decision"] == "defer_positive_or_hold_review").sum())
        if not adjudication_df.empty
        else 0,
        "threshold_replay_input_allowed_candidate_rows": int(
            adjudication_df["threshold_replay_input_allowed_candidate"].sum()
        )
        if not adjudication_df.empty
        else 0,
        "threshold_tuning_approved": 0,
        "operator_facing_change_allowed_sum": int(adjudication_df["operator_facing_change_allowed"].sum())
        if not adjudication_df.empty
        else 0,
        "engine_patch_allowed_sum": int(adjudication_df["engine_patch_allowed"].sum())
        if not adjudication_df.empty
        else 0,
        "threshold_patch_allowed_sum": int(adjudication_df["threshold_patch_allowed"].sum())
        if not adjudication_df.empty
        else 0,
        "decision_counts": adjudication_df["conservative_decision"].value_counts().sort_index().to_dict()
        if not adjudication_df.empty
        else {},
        "summary_rows": int(len(summary_df)),
        "recommended_next_branch": "rebuild_br084_negative_only_then_adjudicate_positive_candidates",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "adjudication": str(output_dir / ADJUDICATION_OUTPUT_NAME),
            "review_input": str(output_dir / REVIEW_INPUT_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a conservative negative-only episode-truth adjudication input from BR-087."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--worksheet-input", default=BR087_WORKSHEET_DEFAULT, help="BR-087 worksheet CSV.")
    parser.add_argument(
        "--output-dir",
        default="/private/tmp/panel_day_engine_episode_truth_conservative_adjudication_br088_check",
        help="Output directory for BR-088 artifacts.",
    )
    parser.add_argument("--owner-branch", default="BR-20260425-088")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    worksheet_input = resolve_path(repo_root, args.worksheet_input)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    worksheet_df = read_required_csv(worksheet_input, REQUIRED_WORKSHEET_COLUMNS, "BR-087 worksheet")
    assert_safe_input(worksheet_df)
    adjudication_df, review_input_df = build_adjudication(args.owner_branch, worksheet_df)
    summary_df = build_summary(args.owner_branch, adjudication_df)
    action_df = build_action_queue(args.owner_branch)

    adjudication_df.to_csv(output_dir / ADJUDICATION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    review_input_df.to_csv(output_dir / REVIEW_INPUT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir / NOTE_OUTPUT_NAME, args.owner_branch, worksheet_input, adjudication_df, review_input_df, summary_df)
    write_json(
        output_dir / JSON_OUTPUT_NAME,
        args.owner_branch,
        repo_root,
        output_dir,
        worksheet_input,
        adjudication_df,
        review_input_df,
        summary_df,
    )

    print(
        json.dumps(
            {
                "owner_branch": args.owner_branch,
                "adjudication_rows": int(len(adjudication_df)),
                "review_input_rows": int(len(review_input_df)),
                "filled_negative_rows": int(adjudication_df["negative_replay_candidate"].sum()),
                "filled_positive_rows": int(adjudication_df["positive_replay_candidate"].sum()),
                "deferred_rows": int(
                    (adjudication_df["conservative_decision"] == "defer_positive_or_hold_review").sum()
                ),
                "threshold_replay_input_allowed_candidate_rows": int(
                    adjudication_df["threshold_replay_input_allowed_candidate"].sum()
                ),
                "decision_counts": adjudication_df["conservative_decision"].value_counts().sort_index().to_dict(),
                "outputs": {
                    "adjudication": str(output_dir / ADJUDICATION_OUTPUT_NAME),
                    "review_input": str(output_dir / REVIEW_INPUT_OUTPUT_NAME),
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
