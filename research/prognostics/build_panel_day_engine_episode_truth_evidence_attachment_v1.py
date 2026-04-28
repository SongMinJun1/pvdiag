#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

import pandas as pd


INDEX_OUTPUT_NAME = "panel_day_engine_episode_truth_evidence_attachment_index_v1.csv"
TEMPLATE_OUTPUT_NAME = "panel_day_engine_episode_truth_review_input_template_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_episode_truth_evidence_attachment_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_episode_truth_evidence_attachment_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_episode_truth_evidence_attachment_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_episode_truth_evidence_attachment_v1.json"
CARDS_DIR_NAME = "panel_day_engine_episode_truth_evidence_cards_v1"

BR084_ROWS_DEFAULT = (
    "/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br084_check/"
    "panel_day_engine_reviewed_episode_truth_rows_v1.csv"
)

ALLOWED_REVIEWER_LABELS = (
    "real_precursor; episode_only_or_backdating; strict_sudden_no_precursor; "
    "common_cause_or_measurement_hold; insufficient_evidence_hold"
)

REQUIRED_ROW_COLUMNS = [
    "reviewed_truth_row_id",
    "review_packet_id",
    "review_status",
    "truth_role",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "review_priority",
    "review_track",
    "episode_truth_bucket",
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
    "source_lens_count",
    "source_artifacts",
    "source_case_ids",
    "episode_truth_case_ids",
    "candidate_reading",
    "default_review_disposition",
    "must_prove_axes",
    "must_reject_axes",
    "review_question",
    "threshold_replay_input_allowed",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

INDEX_COLUMNS = [
    "owner_branch",
    "attachment_row_id",
    "reviewed_truth_row_id",
    "review_packet_id",
    "evidence_status",
    "evidence_card_path",
    "review_input_template_ready",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "threshold_replay_input_allowed",
    "review_priority",
    "review_track",
    "episode_truth_bucket",
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
    "source_lens_count",
    "source_artifacts",
    "source_case_ids",
    "episode_truth_case_ids",
    "candidate_reading",
    "default_review_disposition",
    "must_prove_axes",
    "must_reject_axes",
    "must_prove_axis_count",
    "must_reject_axis_count",
    "review_question",
    "allowed_reviewer_truth_labels",
    "reviewer_next_action",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

TEMPLATE_COLUMNS = [
    "review_packet_id",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "reviewer_notes",
    "reviewed_truth_row_id",
    "evidence_card_path",
    "review_priority",
    "review_track",
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
    "allowed_reviewer_truth_labels",
    "fill_instruction",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "review_track",
    "site",
    "input_rows",
    "evidence_card_count",
    "review_input_template_rows",
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


def split_semicolon(value: object) -> list[str]:
    return [part.strip() for part in normalize_text(value).split(";") if part.strip()]


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


def assert_safe_input(rows_df: pd.DataFrame) -> None:
    for col in ["operator_facing_change_allowed", "engine_patch_allowed", "threshold_patch_allowed"]:
        total = int(rows_df[col].map(numeric_int).sum())
        if total != 0:
            raise ValueError(f"BR-085 requires non-authorizing BR-084 input; {col} sum is {total}")
    replay_total = int(rows_df["threshold_replay_input_allowed"].map(numeric_int).sum())
    if replay_total != 0:
        raise ValueError(
            "BR-085 evidence attachment template must start before replay-ready rows; "
            f"threshold_replay_input_allowed sum is {replay_total}"
        )


def safe_card_name(row: dict[str, object]) -> str:
    raw_name = f"{normalize_text(row.get('reviewed_truth_row_id'))}_{normalize_text(row.get('review_packet_id'))}"
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw_name).strip("_")
    return f"{name or 'episode_truth_evidence_card'}.md"


def reviewer_next_action(row: dict[str, object]) -> str:
    track = normalize_text(row.get("review_track"))
    if track == "long_gap_backdating_review":
        return "prove same-panel continuity across the long gap, or mark as sparse/backdating negative"
    if track == "strict_sudden_prior_episode_review":
        return "prove a defensible prior episode before the strict trigger, or mark as strict-sudden negative"
    if track == "durable_precursor_review":
        return "prove durable/recurrent same-family precursor, or mark as negative/hold"
    return "review evidence axes before assigning any truth label"


def build_card_text(row: dict[str, object]) -> str:
    prove_axes = split_semicolon(row.get("must_prove_axes"))
    reject_axes = split_semicolon(row.get("must_reject_axes"))
    source_refs = split_semicolon(row.get("source_case_ids"))
    truth_refs = split_semicolon(row.get("episode_truth_case_ids"))

    def bullets(values: list[str]) -> str:
        return "\n".join(f"- {value}" for value in values) if values else "- none"

    facts = [
        ("reviewed_truth_row_id", row.get("reviewed_truth_row_id")),
        ("review_packet_id", row.get("review_packet_id")),
        ("review_track", row.get("review_track")),
        ("episode_truth_bucket", row.get("episode_truth_bucket")),
        ("site", row.get("site")),
        ("panel_id", row.get("panel_id")),
        ("family_key", row.get("family_key")),
        ("family_label_ko", row.get("family_label_ko")),
        ("subtype_key", row.get("subtype_key")),
        ("subtype_label_ko", row.get("subtype_label_ko")),
        ("episode_anchor_date", row.get("episode_anchor_date")),
        ("episode_anchor_kind", row.get("episode_anchor_kind")),
        ("strict_trigger_date", row.get("strict_trigger_date")),
        ("gap_days", row.get("gap_days")),
        ("signal_start_date", row.get("signal_start_date")),
        ("signal_end_date", row.get("signal_end_date")),
        ("signal_span_days", row.get("signal_span_days")),
        ("signal_day_count", row.get("signal_day_count")),
        ("duration_proxy_days", row.get("duration_proxy_days")),
        ("recurrence_proxy_days", row.get("recurrence_proxy_days")),
        ("warning_proxy_days", row.get("warning_proxy_days")),
        ("common_cause_flag_sum", row.get("common_cause_flag_sum")),
        (
            "strict_trigger_proximal_common_cause_flag",
            row.get("strict_trigger_proximal_common_cause_flag"),
        ),
        ("candidate_reading", row.get("candidate_reading")),
        ("default_review_disposition", row.get("default_review_disposition")),
    ]
    fact_table = "\n".join(f"| {key} | {normalize_text(value)} |" for key, value in facts)

    return f"""# Episode Truth Evidence Card: {normalize_text(row.get("reviewed_truth_row_id"))}

## Guardrail
- This card is evidence packaging only.
- It is not a truth label, replay approval, threshold patch, or `panel_day_engine.py` authorization.
- To make a row replay-ready, a reviewer must add an accepted `reviewer_truth_label` and a real `reviewer_evidence_path` in the review input CSV.

## Review Question
{normalize_text(row.get("review_question"))}

## Current Facts
| field | value |
| --- | --- |
{fact_table}

## Must Prove Before Positive Label
{bullets(prove_axes)}

## Must Reject Before Negative Or Hold Label
{bullets(reject_axes)}

## Source Case References
{bullets(source_refs)}

## Episode Truth Case References
{bullets(truth_refs)}

## Allowed Reviewer Labels
{bullets(split_semicolon(ALLOWED_REVIEWER_LABELS))}

## Suggested Next Action
- {reviewer_next_action(row)}

## Reviewer Fill-In
- reviewer_truth_label:
- reviewer_evidence_path:
- reviewer_notes:
"""


def build_index_and_template(
    owner_branch: str,
    rows_df: pd.DataFrame,
    cards_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    index_rows: list[dict[str, object]] = []
    template_rows: list[dict[str, object]] = []
    for idx, row in enumerate(rows_df.to_dict(orient="records"), start=1):
        card_path = cards_dir / safe_card_name(row)
        card_path.write_text(build_card_text(row), encoding="utf-8")
        prove_count = len(split_semicolon(row.get("must_prove_axes")))
        reject_count = len(split_semicolon(row.get("must_reject_axes")))
        next_action = reviewer_next_action(row)
        label = normalize_text(row.get("reviewer_truth_label"))
        evidence_path = normalize_text(row.get("reviewer_evidence_path"))
        replay_allowed = 0

        index_rows.append(
            {
                "owner_branch": owner_branch,
                "attachment_row_id": f"BR085-EVA-{idx:03d}",
                "reviewed_truth_row_id": normalize_text(row.get("reviewed_truth_row_id")),
                "review_packet_id": normalize_text(row.get("review_packet_id")),
                "evidence_status": "card_created_needs_reviewer_label",
                "evidence_card_path": str(card_path),
                "review_input_template_ready": 1,
                "reviewer_truth_label": label,
                "reviewer_evidence_path": evidence_path,
                "threshold_replay_input_allowed": replay_allowed,
                "review_priority": normalize_text(row.get("review_priority")),
                "review_track": normalize_text(row.get("review_track")),
                "episode_truth_bucket": normalize_text(row.get("episode_truth_bucket")),
                "site": normalize_text(row.get("site")),
                "panel_id": normalize_text(row.get("panel_id")),
                "family_key": normalize_text(row.get("family_key")),
                "family_label_ko": normalize_text(row.get("family_label_ko")),
                "subtype_key": normalize_text(row.get("subtype_key")),
                "subtype_label_ko": normalize_text(row.get("subtype_label_ko")),
                "episode_anchor_date": normalize_text(row.get("episode_anchor_date")),
                "episode_anchor_kind": normalize_text(row.get("episode_anchor_kind")),
                "strict_trigger_date": normalize_text(row.get("strict_trigger_date")),
                "gap_days": numeric_int(row.get("gap_days")),
                "signal_start_date": normalize_text(row.get("signal_start_date")),
                "signal_end_date": normalize_text(row.get("signal_end_date")),
                "signal_span_days": numeric_int(row.get("signal_span_days")),
                "signal_day_count": numeric_int(row.get("signal_day_count")),
                "duration_proxy_days": numeric_int(row.get("duration_proxy_days")),
                "recurrence_proxy_days": numeric_int(row.get("recurrence_proxy_days")),
                "warning_proxy_days": numeric_int(row.get("warning_proxy_days")),
                "common_cause_flag_sum": numeric_int(row.get("common_cause_flag_sum")),
                "strict_trigger_proximal_common_cause_flag": numeric_int(
                    row.get("strict_trigger_proximal_common_cause_flag")
                ),
                "source_lens_count": numeric_int(row.get("source_lens_count")),
                "source_artifacts": normalize_text(row.get("source_artifacts")),
                "source_case_ids": normalize_text(row.get("source_case_ids")),
                "episode_truth_case_ids": normalize_text(row.get("episode_truth_case_ids")),
                "candidate_reading": normalize_text(row.get("candidate_reading")),
                "default_review_disposition": normalize_text(row.get("default_review_disposition")),
                "must_prove_axes": normalize_text(row.get("must_prove_axes")),
                "must_reject_axes": normalize_text(row.get("must_reject_axes")),
                "must_prove_axis_count": prove_count,
                "must_reject_axis_count": reject_count,
                "review_question": normalize_text(row.get("review_question")),
                "allowed_reviewer_truth_labels": ALLOWED_REVIEWER_LABELS,
                "reviewer_next_action": next_action,
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "notes": "template leaves reviewer_truth_label and reviewer_evidence_path blank by design",
            }
        )
        template_rows.append(
            {
                "review_packet_id": normalize_text(row.get("review_packet_id")),
                "reviewer_truth_label": "",
                "reviewer_evidence_path": "",
                "reviewer_notes": "",
                "reviewed_truth_row_id": normalize_text(row.get("reviewed_truth_row_id")),
                "evidence_card_path": str(card_path),
                "review_priority": normalize_text(row.get("review_priority")),
                "review_track": normalize_text(row.get("review_track")),
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
                "allowed_reviewer_truth_labels": ALLOWED_REVIEWER_LABELS,
                "fill_instruction": (
                    "Do not pass this row to BR-084 as replay evidence until reviewer_truth_label "
                    "and reviewer_evidence_path are intentionally filled."
                ),
            }
        )

    return (
        pd.DataFrame(index_rows).reindex(columns=INDEX_COLUMNS),
        pd.DataFrame(template_rows).reindex(columns=TEMPLATE_COLUMNS),
    )


def build_summary(owner_branch: str, index_df: pd.DataFrame, template_df: pd.DataFrame) -> pd.DataFrame:
    if index_df.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    rows: list[dict[str, object]] = []
    group_cols = ["review_track", "site"]
    for key, group in index_df.groupby(group_cols, dropna=False, sort=True):
        review_track, site = key
        template_group = template_df.loc[
            (template_df["review_track"] == review_track) & (template_df["site"] == site)
        ]
        rows.append(
            {
                "owner_branch": owner_branch,
                "review_track": review_track,
                "site": site,
                "input_rows": int(len(group)),
                "evidence_card_count": int(group["evidence_card_path"].map(lambda p: Path(p).exists()).sum()),
                "review_input_template_rows": int(len(template_group)),
                "reviewer_truth_label_assigned_count": int(
                    template_group["reviewer_truth_label"].map(normalize_text).astype(bool).sum()
                ),
                "reviewer_evidence_path_filled_count": int(
                    template_group["reviewer_evidence_path"].map(normalize_text).astype(bool).sum()
                ),
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
            "action_id": "BR085-ACT-001",
            "action": "review evidence cards and fill template labels",
            "input_filter": "all BR-085 template rows",
            "purpose": "turn structured card evidence into explicit reviewer labels only when defensible",
            "success_boundary": "labels are attached only with a real reviewer_evidence_path and notes",
            "recommended_next_artifact": "review_input_filled_for_br084.csv",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "blank template rows remain non-replay inputs",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 2,
            "action_id": "BR085-ACT-002",
            "action": "rebuild BR-084 with filled review input",
            "input_filter": "rows with accepted reviewer_truth_label and reviewer_evidence_path",
            "purpose": "create reviewed_positive/reviewed_negative rows before any replay",
            "success_boundary": "positive and negative replay-ready row counts are explicit",
            "recommended_next_artifact": "panel_day_engine_reviewed_episode_truth_rows_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "hold and insufficient-evidence labels must stay out of replay labels",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 3,
            "action_id": "BR085-ACT-003",
            "action": "open subtype-conditioned threshold replay only after BR-084 has replay rows",
            "input_filter": "reviewed_positive and reviewed_negative BR-084 rows",
            "purpose": "evaluate threshold movement against reviewed truth examples",
            "success_boundary": "replay is evidence-only and still not production authorization",
            "recommended_next_artifact": "panel_day_engine_subtype_threshold_replay_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "direct panel_day_engine.py edits still require BR-076 3-gate prepatch runbook",
        },
    ]
    return pd.DataFrame(rows).reindex(columns=ACTION_COLUMNS)


def write_note(
    output_path: Path,
    owner_branch: str,
    reviewed_rows_input: Path,
    index_df: pd.DataFrame,
    template_df: pd.DataFrame,
    cards_dir: Path,
) -> None:
    track_counts = index_df["review_track"].value_counts().sort_index().to_dict()
    site_counts = index_df["site"].value_counts().sort_index().to_dict()
    lines = [
        "# panel_day_engine_episode_truth_evidence_attachment_v1",
        "",
        "## Purpose",
        "- Package BR-084 `needs_evidence` rows into reviewer-facing evidence cards.",
        "- Produce a review input template that can later be filled and passed back to BR-084.",
        "- Do not infer or auto-fill truth labels.",
        "- Do not authorize threshold replay, operator-facing output changes, or `panel_day_engine.py` edits.",
        "",
        "## Inputs",
        f"- reviewed rows input: `{reviewed_rows_input}`",
        "",
        "## Outputs",
        f"- index: `{output_path.parent / INDEX_OUTPUT_NAME}`",
        f"- review input template: `{output_path.parent / TEMPLATE_OUTPUT_NAME}`",
        f"- summary: `{output_path.parent / SUMMARY_OUTPUT_NAME}`",
        f"- action queue: `{output_path.parent / ACTION_OUTPUT_NAME}`",
        f"- evidence cards dir: `{cards_dir}`",
        "",
        "## Real Result",
        f"- owner_branch: `{owner_branch}`",
        f"- input rows: `{len(index_df)}`",
        f"- evidence cards: `{len(list(cards_dir.glob('*.md')))}`",
        f"- review input template rows: `{len(template_df)}`",
        "- reviewer truth labels assigned: `0`",
        "- reviewer evidence paths filled: `0`",
        "- threshold replay ready rows: `0`",
        "- operator-facing change allowed sum: `0`",
        "- engine patch allowed sum: `0`",
        "- threshold patch allowed sum: `0`",
        "",
        "## Track Counts",
    ]
    for key, value in track_counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Site Counts"])
    for key, value in site_counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "- `reviewer_evidence_path` is intentionally blank in the template.",
            "- The generated evidence card path is a review aid, not automatic proof.",
            "- A reviewer must explicitly choose a label and evidence path before BR-084 can create replay-ready rows.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(
    output_path: Path,
    owner_branch: str,
    repo_root: Path,
    output_dir: Path,
    reviewed_rows_input: Path,
    index_df: pd.DataFrame,
    template_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    cards_dir: Path,
) -> None:
    payload = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "reviewed_rows_input": str(reviewed_rows_input),
        "input_rows": int(len(index_df)),
        "evidence_card_count": int(len(list(cards_dir.glob("*.md")))),
        "review_input_template_rows": int(len(template_df)),
        "summary_rows": int(len(summary_df)),
        "reviewer_truth_label_assigned_count": int(
            template_df["reviewer_truth_label"].map(normalize_text).astype(bool).sum()
        ),
        "reviewer_evidence_path_filled_count": int(
            template_df["reviewer_evidence_path"].map(normalize_text).astype(bool).sum()
        ),
        "threshold_replay_ready_count": 0,
        "operator_facing_change_allowed_sum": int(index_df["operator_facing_change_allowed"].sum()),
        "engine_patch_allowed_sum": int(index_df["engine_patch_allowed"].sum()),
        "threshold_patch_allowed_sum": int(index_df["threshold_patch_allowed"].sum()),
        "review_track_counts": index_df["review_track"].value_counts().sort_index().to_dict(),
        "site_counts": index_df["site"].value_counts().sort_index().to_dict(),
        "recommended_next_branch": "fill_br085_review_input_then_rebuild_br084",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "index": str(output_dir / INDEX_OUTPUT_NAME),
            "review_input_template": str(output_dir / TEMPLATE_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
            "cards_dir": str(cards_dir),
        },
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build reviewer evidence cards and an input template for BR-084 episode truth rows."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument(
        "--reviewed-rows-input",
        default=BR084_ROWS_DEFAULT,
        help="BR-084 reviewed episode truth rows CSV.",
    )
    parser.add_argument(
        "--output-dir",
        default="/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check",
        help="Output directory for BR-085 evidence attachment artifacts.",
    )
    parser.add_argument("--owner-branch", default="BR-20260425-085")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    reviewed_rows_input = resolve_path(repo_root, args.reviewed_rows_input)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cards_dir = output_dir / CARDS_DIR_NAME
    if cards_dir.exists():
        shutil.rmtree(cards_dir)
    cards_dir.mkdir(parents=True, exist_ok=True)

    rows_df = read_required_csv(reviewed_rows_input, REQUIRED_ROW_COLUMNS, "BR-084 reviewed rows")
    assert_safe_input(rows_df)

    index_df, template_df = build_index_and_template(args.owner_branch, rows_df, cards_dir)
    summary_df = build_summary(args.owner_branch, index_df, template_df)
    action_df = build_action_queue(args.owner_branch)

    index_df.to_csv(output_dir / INDEX_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    template_df.to_csv(output_dir / TEMPLATE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir / NOTE_OUTPUT_NAME, args.owner_branch, reviewed_rows_input, index_df, template_df, cards_dir)
    write_json(
        output_dir / JSON_OUTPUT_NAME,
        args.owner_branch,
        repo_root,
        output_dir,
        reviewed_rows_input,
        index_df,
        template_df,
        summary_df,
        cards_dir,
    )

    print(
        json.dumps(
            {
                "owner_branch": args.owner_branch,
                "input_rows": int(len(index_df)),
                "evidence_card_count": int(len(list(cards_dir.glob("*.md")))),
                "review_input_template_rows": int(len(template_df)),
                "reviewer_truth_label_assigned_count": 0,
                "reviewer_evidence_path_filled_count": 0,
                "threshold_replay_ready_count": 0,
                "outputs": {
                    "index": str(output_dir / INDEX_OUTPUT_NAME),
                    "review_input_template": str(output_dir / TEMPLATE_OUTPUT_NAME),
                    "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
                    "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
                    "note": str(output_dir / NOTE_OUTPUT_NAME),
                    "cards_dir": str(cards_dir),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
