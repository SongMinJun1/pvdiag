#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


TRACE_OUTPUT_NAME = "panel_day_engine_episode_truth_source_trace_audit_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_episode_truth_source_trace_audit_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_episode_truth_source_trace_audit_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_episode_truth_source_trace_audit_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_episode_truth_source_trace_audit_v1.json"

BR085_INDEX_DEFAULT = (
    "/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/"
    "panel_day_engine_episode_truth_evidence_attachment_index_v1.csv"
)
BR085_TEMPLATE_DEFAULT = (
    "/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/"
    "panel_day_engine_episode_truth_review_input_template_v1.csv"
)

SOURCE_ARTIFACT_FILES = {
    "br017_episode_shadow": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_EPISODE_SHADOW_PANEL_V1.csv",
    "br017_g1_longgap_cases": "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_G1_LONGGAP_CASES_V1.csv",
}

REQUIRED_INDEX_COLUMNS = [
    "reviewed_truth_row_id",
    "review_packet_id",
    "evidence_card_path",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "threshold_replay_input_allowed",
    "review_priority",
    "review_track",
    "episode_truth_bucket",
    "site",
    "panel_id",
    "family_key",
    "subtype_key",
    "episode_anchor_date",
    "strict_trigger_date",
    "source_artifacts",
    "source_case_ids",
    "must_prove_axes",
    "must_reject_axes",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

REQUIRED_TEMPLATE_COLUMNS = [
    "review_packet_id",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "reviewed_truth_row_id",
    "evidence_card_path",
]

TRACE_COLUMNS = [
    "owner_branch",
    "trace_row_id",
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
    "source_row_number",
    "source_file_path",
    "source_file_exists",
    "source_row_resolved",
    "source_identity_match",
    "source_identity_mismatch_fields",
    "source_current_event_type_ko",
    "source_current_final_pattern_ko",
    "source_algorithm_family_ko",
    "source_heuristic_top1_ko",
    "source_episode_basis_date",
    "source_episode_basis_kind",
    "source_strict_trigger_date",
    "source_gap_days",
    "source_episode_class_shadow",
    "source_precursor_promotion_shadow_decision",
    "source_shadow_reason_ko",
    "evidence_card_exists",
    "template_row_exists",
    "template_blank_label",
    "template_blank_evidence_path",
    "trace_ready",
    "label_fill_status",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "review_track",
    "site",
    "review_rows",
    "source_reference_count",
    "source_file_exists_sum",
    "source_row_resolved_sum",
    "source_identity_match_sum",
    "source_identity_mismatch_count",
    "evidence_card_exists_sum",
    "template_row_exists_sum",
    "template_blank_label_sum",
    "template_blank_evidence_path_sum",
    "trace_ready_sum",
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


def parse_source_ref(value: str) -> tuple[str, int | None]:
    text = normalize_text(value)
    if ":" not in text:
        return text, None
    artifact, row_number_text = text.rsplit(":", 1)
    try:
        row_number = int(row_number_text)
    except ValueError:
        row_number = None
    return normalize_text(artifact), row_number


def assert_safe_input(index_df: pd.DataFrame) -> None:
    for col in ["operator_facing_change_allowed", "engine_patch_allowed", "threshold_patch_allowed"]:
        total = int(index_df[col].map(numeric_int).sum())
        if total != 0:
            raise ValueError(f"BR-086 requires non-authorizing BR-085 input; {col} sum is {total}")
    replay_total = int(index_df["threshold_replay_input_allowed"].map(numeric_int).sum())
    if replay_total != 0:
        raise ValueError(
            "BR-086 source trace audit must run before replay-ready rows; "
            f"threshold_replay_input_allowed sum is {replay_total}"
        )


def load_source_tables(repo_root: Path) -> dict[str, tuple[Path, pd.DataFrame | None]]:
    tables: dict[str, tuple[Path, pd.DataFrame | None]] = {}
    for artifact, rel_path in SOURCE_ARTIFACT_FILES.items():
        path = resolve_path(repo_root, rel_path)
        if path.exists():
            tables[artifact] = (path, pd.read_csv(path, encoding="utf-8-sig", low_memory=False))
        else:
            tables[artifact] = (path, None)
    return tables


def source_value(source_row: pd.Series | None, col: str) -> str:
    if source_row is None or col not in source_row.index:
        return ""
    return normalize_text(source_row[col])


def identity_check(card_row: dict[str, object], source_row: pd.Series | None) -> tuple[int, str]:
    if source_row is None:
        return 0, "source_row_missing"
    checks = [
        ("site", normalize_text(card_row.get("site")), source_value(source_row, "site")),
        ("panel_id", normalize_text(card_row.get("panel_id")), source_value(source_row, "panel_id")),
        (
            "episode_anchor_date",
            normalize_text(card_row.get("episode_anchor_date")),
            source_value(source_row, "episode_basis_date"),
        ),
        (
            "strict_trigger_date",
            normalize_text(card_row.get("strict_trigger_date")),
            source_value(source_row, "strict_trigger_date"),
        ),
    ]
    mismatches = [name for name, expected, actual in checks if expected != actual]
    return (0 if mismatches else 1, "; ".join(mismatches))


def template_lookup(template_df: pd.DataFrame) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for row in template_df.to_dict(orient="records"):
        key = normalize_text(row.get("review_packet_id"))
        if key:
            rows[key] = row
    return rows


def build_trace(
    owner_branch: str,
    repo_root: Path,
    index_df: pd.DataFrame,
    template_df: pd.DataFrame,
) -> pd.DataFrame:
    source_tables = load_source_tables(repo_root)
    templates = template_lookup(template_df)
    trace_rows: list[dict[str, object]] = []

    for card_idx, card_row in enumerate(index_df.to_dict(orient="records"), start=1):
        refs = split_semicolon(card_row.get("source_case_ids"))
        if not refs:
            refs = [""]
        template_row = templates.get(normalize_text(card_row.get("review_packet_id")))
        template_exists = 1 if template_row is not None else 0
        template_blank_label = 1 if template_row is not None and not normalize_text(template_row.get("reviewer_truth_label")) else 0
        template_blank_evidence = (
            1 if template_row is not None and not normalize_text(template_row.get("reviewer_evidence_path")) else 0
        )
        card_path = Path(normalize_text(card_row.get("evidence_card_path")))
        card_exists = 1 if card_path.exists() else 0

        for ref_idx, ref in enumerate(refs, start=1):
            source_artifact, row_number = parse_source_ref(ref)
            source_file, source_df = source_tables.get(source_artifact, (Path(""), None))
            source_file_exists = 1 if source_df is not None else 0
            source_row = None
            source_row_resolved = 0
            if source_df is not None and row_number is not None and 1 <= row_number <= len(source_df):
                source_row = source_df.iloc[row_number - 1]
                source_row_resolved = 1
            source_identity_match, mismatch_fields = identity_check(card_row, source_row)
            trace_ready = int(
                source_file_exists
                and source_row_resolved
                and source_identity_match
                and card_exists
                and template_exists
                and template_blank_label
                and template_blank_evidence
            )
            label_fill_status = (
                "trace_ready_needs_human_label" if trace_ready else "blocked_until_trace_or_template_fixed"
            )
            trace_rows.append(
                {
                    "owner_branch": owner_branch,
                    "trace_row_id": f"BR086-TRACE-{card_idx:03d}-{ref_idx:02d}",
                    "reviewed_truth_row_id": normalize_text(card_row.get("reviewed_truth_row_id")),
                    "review_packet_id": normalize_text(card_row.get("review_packet_id")),
                    "review_priority": normalize_text(card_row.get("review_priority")),
                    "review_track": normalize_text(card_row.get("review_track")),
                    "episode_truth_bucket": normalize_text(card_row.get("episode_truth_bucket")),
                    "site": normalize_text(card_row.get("site")),
                    "panel_id": normalize_text(card_row.get("panel_id")),
                    "family_key": normalize_text(card_row.get("family_key")),
                    "subtype_key": normalize_text(card_row.get("subtype_key")),
                    "episode_anchor_date": normalize_text(card_row.get("episode_anchor_date")),
                    "strict_trigger_date": normalize_text(card_row.get("strict_trigger_date")),
                    "source_reference": normalize_text(ref),
                    "source_artifact": source_artifact,
                    "source_row_number": row_number or 0,
                    "source_file_path": str(source_file),
                    "source_file_exists": source_file_exists,
                    "source_row_resolved": source_row_resolved,
                    "source_identity_match": source_identity_match,
                    "source_identity_mismatch_fields": mismatch_fields,
                    "source_current_event_type_ko": source_value(source_row, "current_event_type_ko"),
                    "source_current_final_pattern_ko": source_value(source_row, "current_final_pattern_ko"),
                    "source_algorithm_family_ko": source_value(source_row, "algorithm_family_ko"),
                    "source_heuristic_top1_ko": source_value(source_row, "heuristic_top1_ko"),
                    "source_episode_basis_date": source_value(source_row, "episode_basis_date"),
                    "source_episode_basis_kind": source_value(source_row, "episode_basis_kind"),
                    "source_strict_trigger_date": source_value(source_row, "strict_trigger_date"),
                    "source_gap_days": numeric_int(source_value(source_row, "gap_days")),
                    "source_episode_class_shadow": source_value(source_row, "episode_class_shadow"),
                    "source_precursor_promotion_shadow_decision": source_value(
                        source_row, "precursor_promotion_shadow_decision"
                    ),
                    "source_shadow_reason_ko": source_value(source_row, "shadow_reason_ko"),
                    "evidence_card_exists": card_exists,
                    "template_row_exists": template_exists,
                    "template_blank_label": template_blank_label,
                    "template_blank_evidence_path": template_blank_evidence,
                    "trace_ready": trace_ready,
                    "label_fill_status": label_fill_status,
                    "operator_facing_change_allowed": 0,
                    "engine_patch_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "notes": "source trace confirms reference availability only; it does not assign truth labels",
                }
            )
    return pd.DataFrame(trace_rows).reindex(columns=TRACE_COLUMNS)


def build_summary(owner_branch: str, trace_df: pd.DataFrame) -> pd.DataFrame:
    if trace_df.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    rows: list[dict[str, object]] = []
    for (review_track, site), group in trace_df.groupby(["review_track", "site"], dropna=False, sort=True):
        rows.append(
            {
                "owner_branch": owner_branch,
                "review_track": review_track,
                "site": site,
                "review_rows": int(group["review_packet_id"].nunique()),
                "source_reference_count": int(len(group)),
                "source_file_exists_sum": int(group["source_file_exists"].sum()),
                "source_row_resolved_sum": int(group["source_row_resolved"].sum()),
                "source_identity_match_sum": int(group["source_identity_match"].sum()),
                "source_identity_mismatch_count": int((group["source_identity_match"] == 0).sum()),
                "evidence_card_exists_sum": int(group["evidence_card_exists"].sum()),
                "template_row_exists_sum": int(group["template_row_exists"].sum()),
                "template_blank_label_sum": int(group["template_blank_label"].sum()),
                "template_blank_evidence_path_sum": int(group["template_blank_evidence_path"].sum()),
                "trace_ready_sum": int(group["trace_ready"].sum()),
                "reviewer_truth_label_assigned_count": 0,
                "reviewer_evidence_path_filled_count": 0,
                "threshold_replay_ready_count": 0,
                "operator_facing_change_allowed_sum": int(group["operator_facing_change_allowed"].sum()),
                "engine_patch_allowed_sum": int(group["engine_patch_allowed"].sum()),
                "threshold_patch_allowed_sum": int(group["threshold_patch_allowed"].sum()),
            }
        )
    return pd.DataFrame(rows).reindex(columns=SUMMARY_COLUMNS)


def build_action_queue(owner_branch: str, trace_df: pd.DataFrame) -> pd.DataFrame:
    all_ready = int(trace_df["trace_ready"].sum()) == int(len(trace_df)) if not trace_df.empty else False
    rows = [
        {
            "owner_branch": owner_branch,
            "sequence": 1,
            "action_id": "BR086-ACT-001",
            "action": "review trace-ready source rows against evidence cards",
            "input_filter": "trace_ready=1",
            "purpose": "use resolved source rows as review context before selecting any truth label",
            "success_boundary": "reviewer documents why prove/reject axes are satisfied or not satisfied",
            "recommended_next_artifact": "filled_br085_review_input_template_v1.csv",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "all source references are trace-ready" if all_ready else "fix trace gaps before label filling",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 2,
            "action_id": "BR086-ACT-002",
            "action": "rebuild BR-084 only after explicit labels and evidence paths are filled",
            "input_filter": "reviewer_truth_label and reviewer_evidence_path non-empty",
            "purpose": "create reviewed positive/negative rows without guessing",
            "success_boundary": "BR-084 reports explicit positive/negative replay-ready counts",
            "recommended_next_artifact": "panel_day_engine_reviewed_episode_truth_rows_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "BR-086 does not fill labels",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 3,
            "action_id": "BR086-ACT-003",
            "action": "keep threshold replay blocked until BR-084 has replay-ready truth rows",
            "input_filter": "threshold_replay_ready_count=0",
            "purpose": "avoid tuning against unlabeled review context",
            "success_boundary": "no threshold or engine patch is opened from source trace alone",
            "recommended_next_artifact": "panel_day_engine_subtype_threshold_replay_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "direct panel_day_engine.py edits still require the BR-076 3-gate prepatch runbook",
        },
    ]
    return pd.DataFrame(rows).reindex(columns=ACTION_COLUMNS)


def write_note(
    path: Path,
    owner_branch: str,
    index_input: Path,
    template_input: Path,
    trace_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    track_counts = trace_df.groupby("review_track")["source_reference"].count().sort_index().to_dict()
    summary_table = dataframe_to_markdown(summary_df)
    lines = [
        "# panel_day_engine_episode_truth_source_trace_audit_v1",
        "",
        "## Purpose",
        "- Verify that BR-085 evidence cards and review-template rows trace back to concrete source CSV rows.",
        "- Keep this audit source-trace-only: no truth label, replay approval, threshold patch, or engine edit.",
        "",
        "## Inputs",
        f"- BR-085 index: `{index_input}`",
        f"- BR-085 review template: `{template_input}`",
        "",
        "## Real Result",
        f"- owner_branch: `{owner_branch}`",
        f"- review rows: `{trace_df['review_packet_id'].nunique() if not trace_df.empty else 0}`",
        f"- source references: `{len(trace_df)}`",
        f"- source files existing: `{int(trace_df['source_file_exists'].sum()) if not trace_df.empty else 0}`",
        f"- source rows resolved: `{int(trace_df['source_row_resolved'].sum()) if not trace_df.empty else 0}`",
        f"- source identity matches: `{int(trace_df['source_identity_match'].sum()) if not trace_df.empty else 0}`",
        f"- trace-ready references: `{int(trace_df['trace_ready'].sum()) if not trace_df.empty else 0}`",
        "- reviewer truth labels assigned: `0`",
        "- reviewer evidence paths filled: `0`",
        "- threshold replay ready rows: `0`",
        "- operator-facing change allowed sum: `0`",
        "- engine patch allowed sum: `0`",
        "- threshold patch allowed sum: `0`",
        "",
        "## Track Reference Counts",
    ]
    for key, value in track_counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
        "## Summary",
        summary_table,
            "",
            "## Safety Boundary",
            "- Source trace readiness means the referenced source rows are available and identity-matched.",
            "- It does not mean the row is a confirmed precursor or counterexample.",
            "- A reviewer still has to fill labels and evidence paths before BR-084 can create replay-ready rows.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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


def write_json(
    path: Path,
    owner_branch: str,
    repo_root: Path,
    output_dir: Path,
    index_input: Path,
    template_input: Path,
    trace_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    payload = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "index_input": str(index_input),
        "template_input": str(template_input),
        "review_rows": int(trace_df["review_packet_id"].nunique()) if not trace_df.empty else 0,
        "source_reference_count": int(len(trace_df)),
        "source_file_exists_count": int(trace_df["source_file_exists"].sum()) if not trace_df.empty else 0,
        "source_row_resolved_count": int(trace_df["source_row_resolved"].sum()) if not trace_df.empty else 0,
        "source_identity_match_count": int(trace_df["source_identity_match"].sum()) if not trace_df.empty else 0,
        "source_identity_mismatch_count": int((trace_df["source_identity_match"] == 0).sum()) if not trace_df.empty else 0,
        "trace_ready_count": int(trace_df["trace_ready"].sum()) if not trace_df.empty else 0,
        "summary_rows": int(len(summary_df)),
        "reviewer_truth_label_assigned_count": 0,
        "reviewer_evidence_path_filled_count": 0,
        "threshold_replay_ready_count": 0,
        "operator_facing_change_allowed_sum": int(trace_df["operator_facing_change_allowed"].sum())
        if not trace_df.empty
        else 0,
        "engine_patch_allowed_sum": int(trace_df["engine_patch_allowed"].sum()) if not trace_df.empty else 0,
        "threshold_patch_allowed_sum": int(trace_df["threshold_patch_allowed"].sum()) if not trace_df.empty else 0,
        "review_track_reference_counts": trace_df["review_track"].value_counts().sort_index().to_dict()
        if not trace_df.empty
        else {},
        "recommended_next_branch": "fill_trace_ready_br085_template_then_rebuild_br084",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "trace": str(output_dir / TRACE_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit BR-085 evidence cards/template against source artifact row references."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--index-input", default=BR085_INDEX_DEFAULT, help="BR-085 evidence attachment index CSV.")
    parser.add_argument("--template-input", default=BR085_TEMPLATE_DEFAULT, help="BR-085 review input template CSV.")
    parser.add_argument(
        "--output-dir",
        default="/private/tmp/panel_day_engine_episode_truth_source_trace_audit_br086_check",
        help="Output directory for BR-086 source trace audit artifacts.",
    )
    parser.add_argument("--owner-branch", default="BR-20260425-086")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    index_input = resolve_path(repo_root, args.index_input)
    template_input = resolve_path(repo_root, args.template_input)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    index_df = read_required_csv(index_input, REQUIRED_INDEX_COLUMNS, "BR-085 evidence attachment index")
    template_df = read_required_csv(template_input, REQUIRED_TEMPLATE_COLUMNS, "BR-085 review input template")
    assert_safe_input(index_df)

    trace_df = build_trace(args.owner_branch, repo_root, index_df, template_df)
    summary_df = build_summary(args.owner_branch, trace_df)
    action_df = build_action_queue(args.owner_branch, trace_df)

    trace_df.to_csv(output_dir / TRACE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir / NOTE_OUTPUT_NAME, args.owner_branch, index_input, template_input, trace_df, summary_df)
    write_json(output_dir / JSON_OUTPUT_NAME, args.owner_branch, repo_root, output_dir, index_input, template_input, trace_df, summary_df)

    print(
        json.dumps(
            {
                "owner_branch": args.owner_branch,
                "review_rows": int(trace_df["review_packet_id"].nunique()) if not trace_df.empty else 0,
                "source_reference_count": int(len(trace_df)),
                "source_row_resolved_count": int(trace_df["source_row_resolved"].sum()) if not trace_df.empty else 0,
                "source_identity_match_count": int(trace_df["source_identity_match"].sum()) if not trace_df.empty else 0,
                "trace_ready_count": int(trace_df["trace_ready"].sum()) if not trace_df.empty else 0,
                "reviewer_truth_label_assigned_count": 0,
                "threshold_replay_ready_count": 0,
                "outputs": {
                    "trace": str(output_dir / TRACE_OUTPUT_NAME),
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
