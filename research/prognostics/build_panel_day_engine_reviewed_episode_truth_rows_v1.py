#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


ROWS_OUTPUT_NAME = "panel_day_engine_reviewed_episode_truth_rows_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_reviewed_episode_truth_rows_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_reviewed_episode_truth_rows_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_reviewed_episode_truth_rows_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_reviewed_episode_truth_rows_v1.json"

BR082_PACKET_DEFAULT = (
    "/private/tmp/panel_day_engine_episode_truth_review_packet_br082_check/"
    "panel_day_engine_episode_truth_review_packet_v1.csv"
)
BR083_AUDIT_JSON_DEFAULT = (
    "/private/tmp/panel_day_engine_direction_assumption_audit_br083_check/"
    "panel_day_engine_direction_assumption_audit_v1.json"
)

ALLOWED_REVIEWER_LABELS = {
    "",
    "real_precursor",
    "episode_only_or_backdating",
    "strict_sudden_no_precursor",
    "common_cause_or_measurement_hold",
    "insufficient_evidence_hold",
}

POSITIVE_LABELS = {"real_precursor"}
NEGATIVE_LABELS = {"episode_only_or_backdating", "strict_sudden_no_precursor"}
HOLD_LABELS = {"common_cause_or_measurement_hold", "insufficient_evidence_hold"}

OUTPUT_COLUMNS = [
    "owner_branch",
    "reviewed_truth_row_id",
    "review_packet_id",
    "review_status",
    "truth_role",
    "reviewer_truth_label",
    "truth_label_source",
    "reviewer_evidence_path",
    "reviewer_notes",
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
    "threshold_replay_role",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "review_status",
    "truth_role",
    "review_track",
    "row_count",
    "threshold_replay_input_allowed_sum",
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


def read_json(path: Path, name: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing required json {name}: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_optional_review_input(path: Path | None) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame(columns=["review_packet_id", "reviewer_truth_label", "reviewer_evidence_path", "reviewer_notes"])
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    missing = [col for col in ["review_packet_id", "reviewer_truth_label"] if col not in df.columns]
    if missing:
        raise ValueError(f"review input missing columns: {missing}")
    for col in ["reviewer_evidence_path", "reviewer_notes"]:
        if col not in df.columns:
            df[col] = ""
    return df


def assert_green_guard(payload: dict[str, Any], allow_failed_guard: bool) -> None:
    fail_count = int(payload.get("fail_count", 0))
    p0_fail_count = int(payload.get("p0_fail_count", 0))
    auth_sum = (
        int(payload.get("operator_facing_change_allowed_sum", 0))
        + int(payload.get("engine_patch_allowed_sum", 0))
        + int(payload.get("threshold_patch_allowed_sum", 0))
    )
    if allow_failed_guard:
        return
    if fail_count != 0 or p0_fail_count != 0 or auth_sum != 0:
        raise ValueError(
            "BR-083 direction guard is not green: "
            f"fail_count={fail_count}, p0_fail_count={p0_fail_count}, authorization_sum={auth_sum}"
        )


def validate_review_labels(review_df: pd.DataFrame) -> None:
    labels = {normalize_text(value) for value in review_df.get("reviewer_truth_label", pd.Series(dtype=str))}
    invalid = sorted(label for label in labels if label not in ALLOWED_REVIEWER_LABELS)
    if invalid:
        raise ValueError(f"invalid reviewer_truth_label values: {invalid}")


def merge_review_inputs(packet_df: pd.DataFrame, review_df: pd.DataFrame) -> pd.DataFrame:
    packet = packet_df.copy()
    packet["review_packet_id"] = packet["review_packet_id"].map(normalize_text)
    if review_df.empty:
        for col in ["reviewer_truth_label", "reviewer_evidence_path", "reviewer_notes"]:
            if col not in packet.columns:
                packet[col] = ""
        return packet

    review = review_df.copy()
    review["review_packet_id"] = review["review_packet_id"].map(normalize_text)
    review["reviewer_truth_label"] = review["reviewer_truth_label"].map(normalize_text)
    review["reviewer_evidence_path"] = review["reviewer_evidence_path"].map(normalize_text)
    review["reviewer_notes"] = review["reviewer_notes"].map(normalize_text)
    validate_review_labels(review)
    duplicate_count = int(review["review_packet_id"].duplicated().sum())
    if duplicate_count:
        raise ValueError(f"review input has duplicate review_packet_id rows: {duplicate_count}")
    unknown = sorted(set(review["review_packet_id"]) - set(packet["review_packet_id"]))
    if unknown:
        raise ValueError(f"review input has unknown review_packet_id values: {unknown}")

    packet = packet.drop(columns=[col for col in ["reviewer_truth_label", "reviewer_evidence_path", "reviewer_notes"] if col in packet.columns])
    return packet.merge(
        review[["review_packet_id", "reviewer_truth_label", "reviewer_evidence_path", "reviewer_notes"]],
        on="review_packet_id",
        how="left",
    )


def status_for_label(label: str, evidence_path: str) -> tuple[str, str, int, str]:
    if not label:
        return "needs_evidence", "unassigned", 0, "not_replay_input"
    if not evidence_path:
        return "needs_evidence_path", "unassigned", 0, "not_replay_input"
    if label in POSITIVE_LABELS:
        return "reviewed_positive", "positive_precursor_truth", 1, "positive_precursor"
    if label in NEGATIVE_LABELS:
        return "reviewed_negative", "negative_counterexample", 1, "negative_counterexample"
    if label in HOLD_LABELS:
        return "reviewed_hold", "hold_or_insufficient_evidence", 0, "not_replay_input"
    return "needs_evidence", "unassigned", 0, "not_replay_input"


def build_rows(owner_branch: str, packet_df: pd.DataFrame, review_df: pd.DataFrame) -> pd.DataFrame:
    merged = merge_review_inputs(packet_df, review_df)
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(merged.to_dict(orient="records"), start=1):
        label = normalize_text(row.get("reviewer_truth_label"))
        evidence_path = normalize_text(row.get("reviewer_evidence_path"))
        reviewer_notes = normalize_text(row.get("reviewer_notes"))
        review_status, truth_role, replay_allowed, replay_role = status_for_label(label, evidence_path)
        truth_label_source = "manual_review_input" if label else "none"
        rows.append(
            {
                "owner_branch": owner_branch,
                "reviewed_truth_row_id": f"BR084-RTR-{idx:03d}",
                "review_packet_id": normalize_text(row.get("review_packet_id")),
                "review_status": review_status,
                "truth_role": truth_role,
                "reviewer_truth_label": label,
                "truth_label_source": truth_label_source,
                "reviewer_evidence_path": evidence_path,
                "reviewer_notes": reviewer_notes,
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
                "strict_trigger_proximal_common_cause_flag": numeric_int(row.get("strict_trigger_proximal_common_cause_flag")),
                "source_lens_count": numeric_int(row.get("source_lens_count")),
                "source_artifacts": normalize_text(row.get("source_artifacts")),
                "source_case_ids": normalize_text(row.get("source_case_ids")),
                "episode_truth_case_ids": normalize_text(row.get("episode_truth_case_ids")),
                "candidate_reading": normalize_text(row.get("candidate_reading")),
                "default_review_disposition": normalize_text(row.get("default_review_disposition")),
                "must_prove_axes": normalize_text(row.get("must_prove_axes")),
                "must_reject_axes": normalize_text(row.get("must_reject_axes")),
                "review_question": normalize_text(row.get("review_question")),
                "threshold_replay_input_allowed": replay_allowed,
                "threshold_replay_role": replay_role,
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "notes": normalize_text(row.get("notes")),
            }
        )
    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def build_summary(owner_branch: str, rows_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if rows_df.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    for (status, role, track), group in rows_df.groupby(["review_status", "truth_role", "review_track"], sort=False):
        rows.append(
            {
                "owner_branch": owner_branch,
                "review_status": status,
                "truth_role": role,
                "review_track": track,
                "row_count": int(len(group)),
                "threshold_replay_input_allowed_sum": int(group["threshold_replay_input_allowed"].sum()),
                "operator_facing_change_allowed_sum": int(group["operator_facing_change_allowed"].sum()),
                "engine_patch_allowed_sum": int(group["engine_patch_allowed"].sum()),
                "threshold_patch_allowed_sum": int(group["threshold_patch_allowed"].sum()),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def build_action_queue(owner_branch: str, rows_df: pd.DataFrame) -> pd.DataFrame:
    needs_evidence = int(rows_df["review_status"].map(normalize_text).isin({"needs_evidence", "needs_evidence_path"}).sum()) if not rows_df.empty else 0
    replay_ready = int(rows_df["threshold_replay_input_allowed"].sum()) if not rows_df.empty else 0
    specs = [
        (
            "ACT-001",
            "attach evidence paths and reviewer labels",
            "review_status in {needs_evidence, needs_evidence_path}",
            "turn BR-082 review rows into defensible positive/negative/hold truth rows",
            "each accepted label has reviewer_evidence_path and reviewer_notes",
            "panel_day_engine_reviewed_episode_truth_rows_v1",
            f"current needs_evidence_count={needs_evidence}",
        ),
        (
            "ACT-002",
            "split replay-ready positive and negative rows",
            "threshold_replay_input_allowed == 1",
            "prepare a balanced input set for subtype-conditioned threshold replay",
            "positive and negative roles are both explicit",
            "panel_day_engine_subtype_threshold_replay_v1",
            f"current replay_ready_count={replay_ready}",
        ),
        (
            "ACT-003",
            "keep hold rows out of replay",
            "truth_role == hold_or_insufficient_evidence",
            "avoid treating common-cause, measurement, or insufficient evidence as labels",
            "hold rows remain review context only",
            "panel_day_engine_reviewed_episode_truth_rows_v1",
            "hold rows can inform blockers but not replay labels",
        ),
        (
            "ACT-004",
            "keep production semantics gated",
            "any threshold or engine behavior change",
            "prevent reviewed truth rows from becoming a direct production patch",
            "threshold replay and BR-076 gates pass before implementation review",
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


def write_note(output_dir: Path, owner_branch: str, rows_df: pd.DataFrame, summary_df: pd.DataFrame, action_df: pd.DataFrame, guard_payload: dict[str, Any]) -> None:
    assigned_count = int(rows_df["reviewer_truth_label"].map(normalize_text).ne("").sum()) if not rows_df.empty else 0
    replay_ready = int(rows_df["threshold_replay_input_allowed"].sum()) if not rows_df.empty else 0
    note = f"""# Panel Day Engine Reviewed Episode Truth Rows V1

## Purpose
- Convert BR-082 review packet rows into a reviewed-truth-row intake table.
- Require BR-083 direction guard to be green before building.
- Keep unreviewed rows as `needs_evidence` rather than inventing truth labels.
- Keep this artifact truth-intake-only: no engine patch, no threshold patch, and no operator-facing promotion.

## Outputs
- `{output_dir / ROWS_OUTPUT_NAME}`
- `{output_dir / SUMMARY_OUTPUT_NAME}`
- `{output_dir / ACTION_OUTPUT_NAME}`
- `{output_dir / JSON_OUTPUT_NAME}`

## Result
- reviewed truth rows: `{len(rows_df)}`
- reviewer truth labels assigned: `{assigned_count}`
- threshold replay ready rows: `{replay_ready}`
- BR-083 fail count: `{int(guard_payload.get("fail_count", 0))}`
- BR-083 P0 fail count: `{int(guard_payload.get("p0_fail_count", 0))}`
- operator-facing change allowed sum: `{int(rows_df["operator_facing_change_allowed"].sum() + action_df["operator_facing_change_allowed"].sum()) if not rows_df.empty else int(action_df["operator_facing_change_allowed"].sum())}`
- engine patch allowed sum: `{int(rows_df["engine_patch_allowed"].sum() + action_df["engine_patch_allowed"].sum()) if not rows_df.empty else int(action_df["engine_patch_allowed"].sum())}`
- threshold patch allowed sum: `{int(rows_df["threshold_patch_allowed"].sum() + action_df["threshold_patch_allowed"].sum()) if not rows_df.empty else int(action_df["threshold_patch_allowed"].sum())}`

## Reading
- Blank `reviewer_truth_label` means `needs_evidence`.
- A label without `reviewer_evidence_path` stays `needs_evidence_path`.
- Only positive/negative labels with evidence paths can become threshold replay inputs.
- Threshold replay input is not production authorization.
- Direct `panel_day_engine.py` edits remain behind the BR-076 3-gate runbook.

## Repro Command
```bash
python3 research/prognostics/build_panel_day_engine_reviewed_episode_truth_rows_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir {output_dir}
```
"""
    (output_dir / NOTE_OUTPUT_NAME).write_text(note, encoding="utf-8")


def build_outputs(
    repo_root: Path,
    output_dir: Path,
    owner_branch: str,
    packet_input: Path,
    guard_json_input: Path,
    review_input: Path | None,
    allow_failed_guard: bool,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    guard_payload = read_json(guard_json_input, "br083_direction_assumption_audit")
    assert_green_guard(guard_payload, allow_failed_guard)
    packet_df = read_required_csv(
        packet_input,
        [
            "review_packet_id",
            "review_priority",
            "review_track",
            "episode_truth_bucket",
            "site",
            "panel_id",
            "source_lens_count",
            "source_artifacts",
            "operator_facing_change_allowed",
            "engine_patch_allowed",
            "threshold_patch_allowed",
        ],
        "br082_episode_truth_review_packet",
    )
    review_df = read_optional_review_input(review_input)
    rows_df = build_rows(owner_branch, packet_df, review_df)
    summary_df = build_summary(owner_branch, rows_df)
    action_df = build_action_queue(owner_branch, rows_df)

    rows_df.to_csv(output_dir / ROWS_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir, owner_branch, rows_df, summary_df, action_df, guard_payload)

    assigned_count = int(rows_df["reviewer_truth_label"].map(normalize_text).ne("").sum()) if not rows_df.empty else 0
    replay_ready_count = int(rows_df["threshold_replay_input_allowed"].sum()) if not rows_df.empty else 0
    payload: dict[str, Any] = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "packet_input": str(packet_input),
        "guard_json_input": str(guard_json_input),
        "review_input": str(review_input) if review_input else "",
        "input_review_packet_rows": int(len(packet_df)),
        "reviewed_truth_rows": int(len(rows_df)),
        "summary_rows": int(len(summary_df)),
        "action_rows": int(len(action_df)),
        "review_status_counts": {str(k): int(v) for k, v in rows_df["review_status"].value_counts().items()},
        "truth_role_counts": {str(k): int(v) for k, v in rows_df["truth_role"].value_counts().items()},
        "reviewer_truth_label_assigned_count": assigned_count,
        "threshold_replay_ready_count": replay_ready_count,
        "br083_fail_count": int(guard_payload.get("fail_count", 0)),
        "br083_p0_fail_count": int(guard_payload.get("p0_fail_count", 0)),
        "operator_facing_change_allowed_sum": int(rows_df["operator_facing_change_allowed"].sum() + action_df["operator_facing_change_allowed"].sum()),
        "engine_patch_allowed_sum": int(rows_df["engine_patch_allowed"].sum() + action_df["engine_patch_allowed"].sum()),
        "threshold_patch_allowed_sum": int(rows_df["threshold_patch_allowed"].sum() + action_df["threshold_patch_allowed"].sum()),
        "recommended_next_branch": "attach_episode_truth_evidence_before_threshold_replay" if replay_ready_count == 0 else "panel_day_engine_subtype_threshold_replay_v1",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "rows": str(output_dir / ROWS_OUTPUT_NAME),
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
    parser.add_argument("--output-dir", type=Path, default=Path("/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br084_check"))
    parser.add_argument("--owner-branch", default="BR-20260425-084")
    parser.add_argument("--packet-input", default=BR082_PACKET_DEFAULT)
    parser.add_argument("--guard-json-input", default=BR083_AUDIT_JSON_DEFAULT)
    parser.add_argument("--review-input", type=Path, default=None)
    parser.add_argument("--allow-failed-guard", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_outputs(
        repo_root=repo_root,
        output_dir=args.output_dir,
        owner_branch=args.owner_branch,
        packet_input=resolve_path(repo_root, args.packet_input),
        guard_json_input=resolve_path(repo_root, args.guard_json_input),
        review_input=args.review_input,
        allow_failed_guard=args.allow_failed_guard,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
