#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


PACKET_OUTPUT_NAME = "panel_day_engine_episode_truth_review_packet_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_episode_truth_review_packet_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_episode_truth_review_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_episode_truth_review_packet_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_episode_truth_review_packet_v1.json"

BR081_MAP_DEFAULT = (
    "/private/tmp/panel_day_engine_episode_truth_map_br081_check/"
    "panel_day_engine_episode_truth_map_v1.csv"
)

REVIEW_BUCKETS = {
    "long_gap_backdating_hold",
    "strict_anchor_sudden_review",
    "durable_precursor_candidate_review",
}

PACKET_COLUMNS = [
    "owner_branch",
    "review_packet_id",
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
    "allowed_reviewer_truth_labels",
    "review_question",
    "recommended_next_if_positive",
    "recommended_next_if_negative",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "reviewer_notes",
    "notes",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "review_track",
    "episode_truth_bucket",
    "review_priority",
    "packet_row_count",
    "source_lens_row_count",
    "collapsed_duplicate_lens_count",
    "unique_panel_count",
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


def review_track(bucket: str) -> str:
    if bucket == "long_gap_backdating_hold":
        return "long_gap_backdating_review"
    if bucket == "strict_anchor_sudden_review":
        return "strict_sudden_prior_episode_review"
    if bucket == "durable_precursor_candidate_review":
        return "durable_precursor_review"
    return "manual_episode_review"


def review_priority(bucket: str, gap_days: int, common_cause: int) -> str:
    if bucket == "long_gap_backdating_hold" and gap_days >= 120:
        return "P0"
    if bucket == "strict_anchor_sudden_review":
        return "P0"
    if bucket == "durable_precursor_candidate_review" and common_cause == 0:
        return "P1"
    return "P2"


def review_contract(bucket: str) -> dict[str, str]:
    if bucket == "long_gap_backdating_hold":
        return {
            "candidate_reading": "possible_over_backdated_precursor_or_sparse_episode",
            "default_review_disposition": "hold_backdating_until_prior_signal_chain_is_proven",
            "must_prove_axes": "same-panel prior signal chain; continuity or recurrence; long normal-gap rebuttal; strict-trigger anchor relation; common-cause exclusion",
            "must_reject_axes": "one-day sparse signal; long normal gap; site/root/group synchrony; measurement displacement; no same-panel continuity",
            "review_question": "Was the distant onset a real same-panel precursor, or an over-backdated/sparse episode?",
            "recommended_next_if_positive": "add to positive episode truth rows, then threshold replay input only",
            "recommended_next_if_negative": "keep onset suppression/backdating hold as regression evidence",
        }
    if bucket == "strict_anchor_sudden_review":
        return {
            "candidate_reading": "strict_trigger_anchor_without_accepted_prior_episode",
            "default_review_disposition": "hold_strict_sudden_until_prior_episode_is_proven",
            "must_prove_axes": "prior normal period; validated preceding episode; same-panel recurrence; common-cause exclusion",
            "must_reject_axes": "trigger-day-only evidence; no prior episode; site/root/group synchrony; measurement displacement",
            "review_question": "Is there a defensible prior episode, or is this a strict-trigger anchored sudden case?",
            "recommended_next_if_positive": "add to positive episode truth rows, then threshold replay input only",
            "recommended_next_if_negative": "keep strict-sudden negative counterexample",
        }
    if bucket == "durable_precursor_candidate_review":
        return {
            "candidate_reading": "plausible_durable_precursor_candidate",
            "default_review_disposition": "manual_review_no_promotion_yet",
            "must_prove_axes": "duration or recurrence; family-shape match; same-panel continuity; common-cause exclusion; later strict/current anchor",
            "must_reject_axes": "common-cause overlap; recovery-only morphology; weak one-day signal; mismatched fault family",
            "review_question": "Does the repeated/durable signal really predict the later panel-local fault family?",
            "recommended_next_if_positive": "add to positive episode truth rows, then subtype-conditioned threshold replay",
            "recommended_next_if_negative": "add to negative episode counterexamples",
        }
    return {
        "candidate_reading": "manual_episode_review",
        "default_review_disposition": "manual_review_no_promotion_yet",
        "must_prove_axes": "review episode evidence",
        "must_reject_axes": "review blockers",
        "review_question": "Manual review required.",
        "recommended_next_if_positive": "review before replay",
        "recommended_next_if_negative": "hold as counterexample",
    }


def review_group_key(row: dict[str, object]) -> tuple[str, ...]:
    return (
        normalize_text(row.get("episode_truth_bucket")),
        normalize_text(row.get("site")),
        normalize_text(row.get("panel_id")),
        normalize_text(row.get("family_key")),
        normalize_text(row.get("episode_anchor_date")),
        normalize_text(row.get("strict_trigger_date")),
    )


def build_packet(owner_branch: str, map_df: pd.DataFrame) -> pd.DataFrame:
    work = map_df.copy()
    work["episode_truth_bucket"] = work["episode_truth_bucket"].map(normalize_text)
    selected = work.loc[work["episode_truth_bucket"].isin(REVIEW_BUCKETS)].copy()
    if selected.empty:
        return pd.DataFrame(columns=PACKET_COLUMNS)

    selected["_review_group_key"] = selected.apply(lambda row: review_group_key(row.to_dict()), axis=1)
    rows: list[dict[str, object]] = []
    for idx, (_, group) in enumerate(selected.groupby("_review_group_key", sort=False), start=1):
        first = group.iloc[0]
        bucket = normalize_text(first["episode_truth_bucket"])
        contract = review_contract(bucket)
        gap_days = max(numeric_int(value) for value in group["gap_days"])
        common_cause = max(numeric_int(value) for value in group["common_cause_flag_sum"])
        priority = review_priority(bucket, gap_days, common_cause)
        source_lens_count = int(len(group))
        rows.append(
            {
                "owner_branch": owner_branch,
                "review_packet_id": f"BR082-EPR-{idx:03d}",
                "review_priority": priority,
                "review_track": review_track(bucket),
                "episode_truth_bucket": bucket,
                "site": normalize_text(first.get("site")),
                "panel_id": normalize_text(first.get("panel_id")),
                "family_key": normalize_text(first.get("family_key")),
                "family_label_ko": normalize_text(first.get("family_label_ko")),
                "subtype_key": normalize_text(first.get("subtype_key")),
                "subtype_label_ko": normalize_text(first.get("subtype_label_ko")),
                "episode_anchor_date": normalize_text(first.get("episode_anchor_date")),
                "episode_anchor_kind": join_unique(group["episode_anchor_kind"]),
                "strict_trigger_date": normalize_text(first.get("strict_trigger_date")),
                "gap_days": gap_days,
                "signal_start_date": normalize_text(first.get("signal_start_date")),
                "signal_end_date": normalize_text(first.get("signal_end_date")),
                "signal_span_days": max(numeric_int(value) for value in group["signal_span_days"]),
                "signal_day_count": max(numeric_int(value) for value in group["signal_day_count"]),
                "duration_proxy_days": max(numeric_int(value) for value in group["duration_proxy_days"]),
                "recurrence_proxy_days": max(numeric_int(value) for value in group["recurrence_proxy_days"]),
                "warning_proxy_days": max(numeric_int(value) for value in group["warning_proxy_days"]),
                "common_cause_flag_sum": common_cause,
                "strict_trigger_proximal_common_cause_flag": max(
                    numeric_int(value) for value in group["strict_trigger_proximal_common_cause_flag"]
                ),
                "source_lens_count": source_lens_count,
                "source_artifacts": join_unique(group["source_artifact"]),
                "source_case_ids": join_unique(group["source_case_id"]),
                "episode_truth_case_ids": join_unique(group["episode_truth_case_id"]),
                "candidate_reading": contract["candidate_reading"],
                "default_review_disposition": contract["default_review_disposition"],
                "must_prove_axes": contract["must_prove_axes"],
                "must_reject_axes": contract["must_reject_axes"],
                "allowed_reviewer_truth_labels": "real_precursor; episode_only_or_backdating; strict_sudden_no_precursor; common_cause_or_measurement_hold; insufficient_evidence_hold",
                "review_question": contract["review_question"],
                "recommended_next_if_positive": contract["recommended_next_if_positive"],
                "recommended_next_if_negative": contract["recommended_next_if_negative"],
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "reviewer_truth_label": "",
                "reviewer_evidence_path": "",
                "reviewer_notes": "",
                "notes": join_unique(group["notes"]),
            }
        )
    packet_df = pd.DataFrame(rows, columns=PACKET_COLUMNS).sort_values(
        ["review_priority", "review_track", "site", "strict_trigger_date", "panel_id"],
        kind="stable",
    ).reset_index(drop=True)
    packet_df["review_packet_id"] = [f"BR082-EPR-{idx:03d}" for idx in range(1, len(packet_df) + 1)]
    return packet_df


def build_summary(owner_branch: str, packet_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if packet_df.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    for (track, bucket, priority), group in packet_df.groupby(
        ["review_track", "episode_truth_bucket", "review_priority"],
        sort=False,
    ):
        source_lens_count = int(group["source_lens_count"].sum())
        packet_row_count = int(len(group))
        rows.append(
            {
                "owner_branch": owner_branch,
                "review_track": track,
                "episode_truth_bucket": bucket,
                "review_priority": priority,
                "packet_row_count": packet_row_count,
                "source_lens_row_count": source_lens_count,
                "collapsed_duplicate_lens_count": int(source_lens_count - packet_row_count),
                "unique_panel_count": int(group["panel_id"].nunique()),
                "operator_facing_change_allowed_sum": int(group["operator_facing_change_allowed"].sum()),
                "engine_patch_allowed_sum": int(group["engine_patch_allowed"].sum()),
                "threshold_patch_allowed_sum": int(group["threshold_patch_allowed"].sum()),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def build_action_queue(owner_branch: str) -> pd.DataFrame:
    specs = [
        (
            "ACT-001",
            "review long-gap/backdating rows",
            "review_track == long_gap_backdating_review",
            "decide whether the distant onset is real precursor evidence or over-backdated sparse episode evidence",
            "all duplicate G1/source lenses are collapsed but traceable",
            "panel_day_engine_episode_truth_review_packet_v1",
            "Positive rows become replay inputs only; negative rows become backdating regression evidence.",
        ),
        (
            "ACT-002",
            "review strict-sudden rows",
            "review_track == strict_sudden_prior_episode_review",
            "look for defensible prior episode evidence before allowing a precursor reading",
            "trigger-day-only rows stay strict-sudden negative examples",
            "panel_day_engine_episode_truth_review_packet_v1",
            "No strict-sudden row can promote without prior episode proof.",
        ),
        (
            "ACT-003",
            "review durable precursor candidates",
            "review_track == durable_precursor_review",
            "find positive precursor examples with recurrence/duration, family shape, and common-cause exclusion",
            "accepted rows have explicit positive and blocker evidence",
            "panel_day_engine_episode_truth_review_packet_v1",
            "Still no operator-facing promotion in this branch.",
        ),
        (
            "ACT-004",
            "prepare reviewed truth rows for threshold replay",
            "reviewer_truth_label in accepted positive/negative labels",
            "turn reviewed rows into a balanced replay input set",
            "reviewed rows are separated into positive truth and counterexample roles",
            "panel_day_engine_subtype_threshold_replay_v1",
            "Threshold replay comes after review, not before.",
        ),
        (
            "ACT-005",
            "keep direct engine edits gated",
            "any proposed panel_day_engine.py behavior change",
            "prevent evidence review from becoming an unreviewed production patch",
            "BR-076 3-gate prepatch runbook passes before direct engine review",
            "check_panel_day_engine_algorithm_prepatch_runbook_v1.py",
            "Passing gates are preconditions, not approval.",
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


def write_note(output_dir: Path, owner_branch: str, packet_df: pd.DataFrame, summary_df: pd.DataFrame, action_df: pd.DataFrame) -> None:
    note = f"""# Panel Day Engine Episode Truth Review Packet V1

## Purpose
- Convert BR-081 truth-pending map rows into a smaller review packet.
- Collapse duplicate source lenses, especially the G1 long-gap lens, so each event is reviewed once.
- Keep source traceability through source artifacts, source case ids, and episode truth case ids.
- Keep this packet review-only: no engine patch, no threshold patch, and no operator-facing promotion.

## Outputs
- `{output_dir / PACKET_OUTPUT_NAME}`
- `{output_dir / SUMMARY_OUTPUT_NAME}`
- `{output_dir / ACTION_OUTPUT_NAME}`
- `{output_dir / JSON_OUTPUT_NAME}`

## Result
- review packet rows: `{len(packet_df)}`
- summary rows: `{len(summary_df)}`
- action rows: `{len(action_df)}`
- source lens rows represented: `{int(packet_df["source_lens_count"].sum()) if not packet_df.empty else 0}`
- collapsed duplicate lens rows: `{int(packet_df["source_lens_count"].sum() - len(packet_df)) if not packet_df.empty else 0}`
- operator-facing change allowed sum: `{int(packet_df["operator_facing_change_allowed"].sum() + action_df["operator_facing_change_allowed"].sum()) if not packet_df.empty else int(action_df["operator_facing_change_allowed"].sum())}`
- engine patch allowed sum: `{int(packet_df["engine_patch_allowed"].sum() + action_df["engine_patch_allowed"].sum()) if not packet_df.empty else int(action_df["engine_patch_allowed"].sum())}`
- threshold patch allowed sum: `{int(packet_df["threshold_patch_allowed"].sum() + action_df["threshold_patch_allowed"].sum()) if not packet_df.empty else int(action_df["threshold_patch_allowed"].sum())}`

## Reading
- Empty `reviewer_truth_label` means no truth has been assigned yet.
- Positive review rows become threshold replay inputs only, not production labels.
- Negative review rows become counterexamples or hold evidence.
- Direct `panel_day_engine.py` changes remain behind the BR-076 3-gate runbook.

## Repro Command
```bash
python3 research/prognostics/build_panel_day_engine_episode_truth_review_packet_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir {output_dir}
```
"""
    (output_dir / NOTE_OUTPUT_NAME).write_text(note, encoding="utf-8")


def build_outputs(repo_root: Path, output_dir: Path, owner_branch: str, episode_map_input: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    map_df = read_required_csv(
        episode_map_input,
        [
            "episode_truth_case_id",
            "source_artifact",
            "source_case_id",
            "site",
            "panel_id",
            "family_key",
            "episode_anchor_date",
            "strict_trigger_date",
            "gap_days",
            "episode_truth_bucket",
            "operator_facing_change_allowed",
            "engine_patch_allowed",
            "threshold_patch_allowed",
        ],
        "br081_episode_truth_map",
    )
    packet_df = build_packet(owner_branch, map_df)
    summary_df = build_summary(owner_branch, packet_df)
    action_df = build_action_queue(owner_branch)

    packet_df.to_csv(output_dir / PACKET_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir, owner_branch, packet_df, summary_df, action_df)

    source_lens_count = int(packet_df["source_lens_count"].sum()) if not packet_df.empty else 0
    payload = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "episode_map_input": str(episode_map_input),
        "input_episode_map_rows": int(len(map_df)),
        "selected_source_lens_rows": source_lens_count,
        "review_packet_rows": int(len(packet_df)),
        "summary_rows": int(len(summary_df)),
        "action_rows": int(len(action_df)),
        "collapsed_duplicate_lens_count": int(source_lens_count - len(packet_df)),
        "review_track_counts": {str(k): int(v) for k, v in packet_df["review_track"].value_counts().items()},
        "review_priority_counts": {str(k): int(v) for k, v in packet_df["review_priority"].value_counts().items()},
        "reviewer_truth_label_assigned_count": int(packet_df["reviewer_truth_label"].map(normalize_text).ne("").sum()),
        "operator_facing_change_allowed_sum": int(packet_df["operator_facing_change_allowed"].sum() + action_df["operator_facing_change_allowed"].sum()),
        "engine_patch_allowed_sum": int(packet_df["engine_patch_allowed"].sum() + action_df["engine_patch_allowed"].sum()),
        "threshold_patch_allowed_sum": int(packet_df["threshold_patch_allowed"].sum() + action_df["threshold_patch_allowed"].sum()),
        "recommended_next_branch": "panel_day_engine_reviewed_episode_truth_rows_v1",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "packet": str(output_dir / PACKET_OUTPUT_NAME),
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
    parser.add_argument("--output-dir", type=Path, default=Path("/private/tmp/panel_day_engine_episode_truth_review_packet_br082_check"))
    parser.add_argument("--owner-branch", default="BR-20260425-082")
    parser.add_argument("--episode-map-input", default=BR081_MAP_DEFAULT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_outputs(
        repo_root=repo_root,
        output_dir=args.output_dir,
        owner_branch=args.owner_branch,
        episode_map_input=resolve_path(repo_root, args.episode_map_input),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
