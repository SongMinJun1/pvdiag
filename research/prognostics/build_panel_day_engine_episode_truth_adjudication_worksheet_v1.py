#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


WORKSHEET_OUTPUT_NAME = "panel_day_engine_episode_truth_adjudication_worksheet_v1.csv"
DRAFT_INPUT_OUTPUT_NAME = "panel_day_engine_episode_truth_review_input_draft_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_episode_truth_adjudication_worksheet_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_episode_truth_adjudication_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_episode_truth_adjudication_worksheet_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_episode_truth_adjudication_worksheet_v1.json"

BR086_TRACE_DEFAULT = (
    "/private/tmp/panel_day_engine_episode_truth_source_trace_audit_br086_check/"
    "panel_day_engine_episode_truth_source_trace_audit_v1.csv"
)
BR085_INDEX_DEFAULT = (
    "/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/"
    "panel_day_engine_episode_truth_evidence_attachment_index_v1.csv"
)

REQUIRED_TRACE_COLUMNS = [
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
    "source_reference",
    "source_artifact",
    "source_current_event_type_ko",
    "source_current_final_pattern_ko",
    "source_algorithm_family_ko",
    "source_heuristic_top1_ko",
    "source_gap_days",
    "source_episode_class_shadow",
    "source_precursor_promotion_shadow_decision",
    "source_shadow_reason_ko",
    "evidence_card_exists",
    "template_row_exists",
    "template_blank_label",
    "template_blank_evidence_path",
    "trace_ready",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

REQUIRED_INDEX_COLUMNS = [
    "reviewed_truth_row_id",
    "review_packet_id",
    "evidence_card_path",
    "reviewer_truth_label",
    "reviewer_evidence_path",
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
    "source_lens_count",
    "source_artifacts",
    "source_case_ids",
    "episode_truth_case_ids",
    "candidate_reading",
    "default_review_disposition",
    "must_prove_axes",
    "must_reject_axes",
    "review_question",
    "allowed_reviewer_truth_labels",
    "reviewer_next_action",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

WORKSHEET_COLUMNS = [
    "owner_branch",
    "worksheet_row_id",
    "adjudication_status",
    "suggested_review_direction",
    "suggested_label_options",
    "must_not_auto_apply_label",
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
    "trace_ready_count",
    "trace_ready_all",
    "source_event_types",
    "source_final_patterns",
    "source_algorithm_families",
    "source_heuristic_top1_values",
    "source_gap_days_min",
    "source_gap_days_max",
    "source_episode_classes",
    "source_precursor_promotion_decisions",
    "source_shadow_reasons",
    "source_references",
    "evidence_card_path",
    "evidence_card_exists",
    "review_question",
    "must_prove_axes",
    "must_reject_axes",
    "candidate_reading",
    "default_review_disposition",
    "reviewer_next_action",
    "allowed_reviewer_truth_labels",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "reviewer_notes_seed",
    "threshold_replay_input_allowed",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

DRAFT_INPUT_COLUMNS = [
    "review_packet_id",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "reviewer_notes",
    "reviewed_truth_row_id",
    "worksheet_row_id",
    "suggested_review_direction",
    "suggested_label_options",
    "evidence_card_path",
    "fill_instruction",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "review_track",
    "site",
    "worksheet_rows",
    "source_reference_count_sum",
    "trace_ready_count_sum",
    "trace_ready_all_count",
    "negative_or_hold_direction_count",
    "strict_sudden_negative_direction_count",
    "manual_positive_or_hold_direction_count",
    "reviewer_truth_label_assigned_count",
    "reviewer_evidence_path_filled_count",
    "threshold_replay_ready_count",
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


def join_unique(values: pd.Series) -> str:
    parts = sorted({normalize_text(value) for value in values if normalize_text(value)})
    return "; ".join(parts)


def assert_safe_inputs(trace_df: pd.DataFrame, index_df: pd.DataFrame) -> None:
    for name, df in [("BR-086 trace", trace_df), ("BR-085 index", index_df)]:
        for col in ["operator_facing_change_allowed", "engine_patch_allowed", "threshold_patch_allowed"]:
            total = int(df[col].map(numeric_int).sum())
            if total != 0:
                raise ValueError(f"BR-087 requires non-authorizing {name} input; {col} sum is {total}")
    label_count = int(index_df["reviewer_truth_label"].map(normalize_text).astype(bool).sum())
    evidence_path_count = int(index_df["reviewer_evidence_path"].map(normalize_text).astype(bool).sum())
    if label_count or evidence_path_count:
        raise ValueError(
            "BR-087 must start from blank BR-085 review fields: "
            f"label_count={label_count}, evidence_path_count={evidence_path_count}"
        )


def direction_for_group(review_track: str, decisions: str, episode_classes: str) -> tuple[str, str, str]:
    if review_track == "long_gap_backdating_review":
        return (
            "negative_or_hold_candidate",
            "episode_only_or_backdating | insufficient_evidence_hold",
            "source shadow says block_precursor_backdating; prove continuity before any positive label",
        )
    if review_track == "strict_sudden_prior_episode_review":
        return (
            "strict_sudden_negative_candidate",
            "strict_sudden_no_precursor | insufficient_evidence_hold",
            "source shadow says no_precursor_promotion; prove prior episode before any positive label",
        )
    if review_track == "durable_precursor_review":
        return (
            "manual_positive_or_hold_candidate",
            "real_precursor | episode_only_or_backdating | common_cause_or_measurement_hold | insufficient_evidence_hold",
            "source shadow says manual_review_candidate; prove same-family continuity and reject common-cause before positive label",
        )
    if "block" in decisions or "hold" in episode_classes:
        return (
            "hold_candidate",
            "common_cause_or_measurement_hold | insufficient_evidence_hold",
            "source context is hold-like; do not promote without extra evidence",
        )
    return (
        "manual_review_candidate",
        "real_precursor | episode_only_or_backdating | insufficient_evidence_hold",
        "manual review required",
    )


def build_index_lookup(index_df: pd.DataFrame) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for row in index_df.to_dict(orient="records"):
        key = normalize_text(row.get("review_packet_id"))
        if key:
            rows[key] = row
    return rows


def build_worksheet(owner_branch: str, trace_df: pd.DataFrame, index_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    index_rows = build_index_lookup(index_df)
    worksheet_rows: list[dict[str, object]] = []
    draft_rows: list[dict[str, object]] = []
    grouped = trace_df.groupby("review_packet_id", sort=False)
    for idx, (review_packet_id, group) in enumerate(grouped, start=1):
        card_row = index_rows.get(normalize_text(review_packet_id), {})
        review_track = normalize_text(group["review_track"].iloc[0])
        source_decisions = join_unique(group["source_precursor_promotion_shadow_decision"])
        source_classes = join_unique(group["source_episode_class_shadow"])
        direction, label_options, direction_note = direction_for_group(review_track, source_decisions, source_classes)
        trace_ready_count = int(group["trace_ready"].map(numeric_int).sum())
        source_reference_count = int(len(group))
        trace_ready_all = int(trace_ready_count == source_reference_count)
        evidence_card_path = normalize_text(card_row.get("evidence_card_path"))
        evidence_card_exists = int(Path(evidence_card_path).exists()) if evidence_card_path else 0
        worksheet_row_id = f"BR087-ADJ-{idx:03d}"
        reviewer_notes_seed = (
            f"{direction_note}; source_decisions={source_decisions}; "
            f"source_classes={source_classes}; trace_ready={trace_ready_count}/{source_reference_count}"
        )
        base = {
            "owner_branch": owner_branch,
            "worksheet_row_id": worksheet_row_id,
            "adjudication_status": "ready_for_human_adjudication" if trace_ready_all else "blocked_until_trace_fixed",
            "suggested_review_direction": direction,
            "suggested_label_options": label_options,
            "must_not_auto_apply_label": 1,
            "reviewed_truth_row_id": normalize_text(group["reviewed_truth_row_id"].iloc[0]),
            "review_packet_id": normalize_text(review_packet_id),
            "review_priority": normalize_text(group["review_priority"].iloc[0]),
            "review_track": review_track,
            "episode_truth_bucket": normalize_text(group["episode_truth_bucket"].iloc[0]),
            "site": normalize_text(group["site"].iloc[0]),
            "panel_id": normalize_text(group["panel_id"].iloc[0]),
            "family_key": normalize_text(group["family_key"].iloc[0]),
            "subtype_key": normalize_text(group["subtype_key"].iloc[0]),
            "episode_anchor_date": normalize_text(group["episode_anchor_date"].iloc[0]),
            "strict_trigger_date": normalize_text(group["strict_trigger_date"].iloc[0]),
            "gap_days": numeric_int(card_row.get("gap_days")),
            "signal_day_count": numeric_int(card_row.get("signal_day_count")),
            "common_cause_flag_sum": numeric_int(card_row.get("common_cause_flag_sum")),
            "strict_trigger_proximal_common_cause_flag": numeric_int(
                card_row.get("strict_trigger_proximal_common_cause_flag")
            ),
            "source_reference_count": source_reference_count,
            "trace_ready_count": trace_ready_count,
            "trace_ready_all": trace_ready_all,
            "source_event_types": join_unique(group["source_current_event_type_ko"]),
            "source_final_patterns": join_unique(group["source_current_final_pattern_ko"]),
            "source_algorithm_families": join_unique(group["source_algorithm_family_ko"]),
            "source_heuristic_top1_values": join_unique(group["source_heuristic_top1_ko"]),
            "source_gap_days_min": int(group["source_gap_days"].map(numeric_int).min()),
            "source_gap_days_max": int(group["source_gap_days"].map(numeric_int).max()),
            "source_episode_classes": source_classes,
            "source_precursor_promotion_decisions": source_decisions,
            "source_shadow_reasons": join_unique(group["source_shadow_reason_ko"]),
            "source_references": join_unique(group["source_reference"]),
            "evidence_card_path": evidence_card_path,
            "evidence_card_exists": evidence_card_exists,
            "review_question": normalize_text(card_row.get("review_question")),
            "must_prove_axes": normalize_text(card_row.get("must_prove_axes")),
            "must_reject_axes": normalize_text(card_row.get("must_reject_axes")),
            "candidate_reading": normalize_text(card_row.get("candidate_reading")),
            "default_review_disposition": normalize_text(card_row.get("default_review_disposition")),
            "reviewer_next_action": normalize_text(card_row.get("reviewer_next_action")),
            "allowed_reviewer_truth_labels": normalize_text(card_row.get("allowed_reviewer_truth_labels")),
            "reviewer_truth_label": "",
            "reviewer_evidence_path": "",
            "reviewer_notes_seed": reviewer_notes_seed,
            "threshold_replay_input_allowed": 0,
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "worksheet is review guidance only; labels must be filled manually after adjudication",
        }
        worksheet_rows.append(base)
        draft_rows.append(
            {
                "review_packet_id": normalize_text(review_packet_id),
                "reviewer_truth_label": "",
                "reviewer_evidence_path": "",
                "reviewer_notes": "",
                "reviewed_truth_row_id": normalize_text(group["reviewed_truth_row_id"].iloc[0]),
                "worksheet_row_id": worksheet_row_id,
                "suggested_review_direction": direction,
                "suggested_label_options": label_options,
                "evidence_card_path": evidence_card_path,
                "fill_instruction": "Fill reviewer_truth_label/evidence_path only after human adjudication; do not use suggested direction as an automatic label.",
            }
        )
    return (
        pd.DataFrame(worksheet_rows).reindex(columns=WORKSHEET_COLUMNS),
        pd.DataFrame(draft_rows).reindex(columns=DRAFT_INPUT_COLUMNS),
    )


def build_summary(owner_branch: str, worksheet_df: pd.DataFrame) -> pd.DataFrame:
    if worksheet_df.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    rows: list[dict[str, object]] = []
    for (review_track, site), group in worksheet_df.groupby(["review_track", "site"], dropna=False, sort=True):
        directions = group["suggested_review_direction"].map(normalize_text)
        rows.append(
            {
                "owner_branch": owner_branch,
                "review_track": review_track,
                "site": site,
                "worksheet_rows": int(len(group)),
                "source_reference_count_sum": int(group["source_reference_count"].sum()),
                "trace_ready_count_sum": int(group["trace_ready_count"].sum()),
                "trace_ready_all_count": int(group["trace_ready_all"].sum()),
                "negative_or_hold_direction_count": int((directions == "negative_or_hold_candidate").sum()),
                "strict_sudden_negative_direction_count": int(
                    (directions == "strict_sudden_negative_candidate").sum()
                ),
                "manual_positive_or_hold_direction_count": int(
                    (directions == "manual_positive_or_hold_candidate").sum()
                ),
                "reviewer_truth_label_assigned_count": 0,
                "reviewer_evidence_path_filled_count": 0,
                "threshold_replay_ready_count": 0,
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
            "action_id": "BR087-ACT-001",
            "action": "adjudicate worksheet rows manually",
            "input_filter": "adjudication_status=ready_for_human_adjudication",
            "purpose": "decide whether prove/reject axes support a real label",
            "success_boundary": "each filled label has an evidence path and notes explaining the decision",
            "recommended_next_artifact": "filled_br087_review_input_for_br084.csv",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "suggested_review_direction is guidance only",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 2,
            "action_id": "BR087-ACT-002",
            "action": "rebuild BR-084 with filled review input",
            "input_filter": "reviewer_truth_label and reviewer_evidence_path non-empty",
            "purpose": "turn manually adjudicated rows into explicit positive/negative/hold statuses",
            "success_boundary": "BR-084 reports reviewed_positive/reviewed_negative counts explicitly",
            "recommended_next_artifact": "panel_day_engine_reviewed_episode_truth_rows_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "unfilled rows remain needs_evidence",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 3,
            "action_id": "BR087-ACT-003",
            "action": "keep threshold replay blocked until BR-084 has positive and negative replay rows",
            "input_filter": "threshold_replay_ready_count=0",
            "purpose": "avoid tuning on guidance-only worksheet rows",
            "success_boundary": "no threshold or engine patch is opened from BR-087 alone",
            "recommended_next_artifact": "panel_day_engine_subtype_threshold_replay_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "direct panel_day_engine.py edits still require BR-076 3-gate prepatch runbook",
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
    trace_input: Path,
    index_input: Path,
    worksheet_df: pd.DataFrame,
    draft_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    direction_counts = worksheet_df["suggested_review_direction"].value_counts().sort_index().to_dict()
    lines = [
        "# panel_day_engine_episode_truth_adjudication_worksheet_v1",
        "",
        "## Purpose",
        "- Compress BR-086 trace-ready source rows into one adjudication worksheet row per review packet.",
        "- Provide suggested review direction without assigning truth labels.",
        "- Keep the BR-084 review input draft blank until a reviewer fills labels and evidence paths.",
        "",
        "## Inputs",
        f"- BR-086 trace input: `{trace_input}`",
        f"- BR-085 index input: `{index_input}`",
        "",
        "## Real Result",
        f"- owner_branch: `{owner_branch}`",
        f"- worksheet rows: `{len(worksheet_df)}`",
        f"- draft review input rows: `{len(draft_df)}`",
        f"- trace-ready worksheet rows: `{int(worksheet_df['trace_ready_all'].sum()) if not worksheet_df.empty else 0}`",
        "- reviewer truth labels assigned: `0`",
        "- reviewer evidence paths filled: `0`",
        "- threshold replay ready rows: `0`",
        "- operator-facing change allowed sum: `0`",
        "- engine patch allowed sum: `0`",
        "- threshold patch allowed sum: `0`",
        "",
        "## Suggested Direction Counts",
    ]
    for key, value in direction_counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Summary",
            dataframe_to_markdown(summary_df),
            "",
            "## Safety Boundary",
            "- Suggested direction is not a reviewer truth label.",
            "- The draft input intentionally leaves `reviewer_truth_label`, `reviewer_evidence_path`, and `reviewer_notes` blank.",
            "- Rebuilding BR-084 with the unfilled draft must not create replay-ready rows.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(
    path: Path,
    owner_branch: str,
    repo_root: Path,
    output_dir: Path,
    trace_input: Path,
    index_input: Path,
    worksheet_df: pd.DataFrame,
    draft_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    payload = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "trace_input": str(trace_input),
        "index_input": str(index_input),
        "worksheet_rows": int(len(worksheet_df)),
        "draft_review_input_rows": int(len(draft_df)),
        "trace_ready_worksheet_rows": int(worksheet_df["trace_ready_all"].sum()) if not worksheet_df.empty else 0,
        "summary_rows": int(len(summary_df)),
        "reviewer_truth_label_assigned_count": 0,
        "reviewer_evidence_path_filled_count": 0,
        "threshold_replay_ready_count": 0,
        "operator_facing_change_allowed_sum": int(worksheet_df["operator_facing_change_allowed"].sum())
        if not worksheet_df.empty
        else 0,
        "engine_patch_allowed_sum": int(worksheet_df["engine_patch_allowed"].sum()) if not worksheet_df.empty else 0,
        "threshold_patch_allowed_sum": int(worksheet_df["threshold_patch_allowed"].sum())
        if not worksheet_df.empty
        else 0,
        "suggested_review_direction_counts": worksheet_df["suggested_review_direction"].value_counts()
        .sort_index()
        .to_dict()
        if not worksheet_df.empty
        else {},
        "recommended_next_branch": "manual_fill_br087_draft_then_rebuild_br084",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "worksheet": str(output_dir / WORKSHEET_OUTPUT_NAME),
            "draft_review_input": str(output_dir / DRAFT_INPUT_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a human adjudication worksheet from BR-086 source trace rows."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--trace-input", default=BR086_TRACE_DEFAULT, help="BR-086 source trace audit CSV.")
    parser.add_argument("--index-input", default=BR085_INDEX_DEFAULT, help="BR-085 evidence attachment index CSV.")
    parser.add_argument(
        "--output-dir",
        default="/private/tmp/panel_day_engine_episode_truth_adjudication_worksheet_br087_check",
        help="Output directory for BR-087 worksheet artifacts.",
    )
    parser.add_argument("--owner-branch", default="BR-20260425-087")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    trace_input = resolve_path(repo_root, args.trace_input)
    index_input = resolve_path(repo_root, args.index_input)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    trace_df = read_required_csv(trace_input, REQUIRED_TRACE_COLUMNS, "BR-086 trace audit")
    index_df = read_required_csv(index_input, REQUIRED_INDEX_COLUMNS, "BR-085 evidence attachment index")
    assert_safe_inputs(trace_df, index_df)

    worksheet_df, draft_df = build_worksheet(args.owner_branch, trace_df, index_df)
    summary_df = build_summary(args.owner_branch, worksheet_df)
    action_df = build_action_queue(args.owner_branch)

    worksheet_df.to_csv(output_dir / WORKSHEET_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    draft_df.to_csv(output_dir / DRAFT_INPUT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir / NOTE_OUTPUT_NAME, args.owner_branch, trace_input, index_input, worksheet_df, draft_df, summary_df)
    write_json(output_dir / JSON_OUTPUT_NAME, args.owner_branch, repo_root, output_dir, trace_input, index_input, worksheet_df, draft_df, summary_df)

    print(
        json.dumps(
            {
                "owner_branch": args.owner_branch,
                "worksheet_rows": int(len(worksheet_df)),
                "draft_review_input_rows": int(len(draft_df)),
                "trace_ready_worksheet_rows": int(worksheet_df["trace_ready_all"].sum()) if not worksheet_df.empty else 0,
                "reviewer_truth_label_assigned_count": 0,
                "threshold_replay_ready_count": 0,
                "suggested_review_direction_counts": worksheet_df["suggested_review_direction"].value_counts()
                .sort_index()
                .to_dict()
                if not worksheet_df.empty
                else {},
                "outputs": {
                    "worksheet": str(output_dir / WORKSHEET_OUTPUT_NAME),
                    "draft_review_input": str(output_dir / DRAFT_INPUT_OUTPUT_NAME),
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
