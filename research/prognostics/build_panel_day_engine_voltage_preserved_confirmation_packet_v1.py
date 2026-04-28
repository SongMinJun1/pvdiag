#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


PACKET_OUTPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_packet_v1.csv"
FAMILY_OUTPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_family_summary_v1.csv"
MAP_OUTPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_candidate_map_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_voltage_preserved_confirmation_packet_v1.json"

DEFAULT_CANDIDATE_INPUT = (
    "/private/tmp/panel_day_engine_voltage_preserved_positive_search_br092_check/"
    "panel_day_engine_voltage_preserved_positive_search_candidates_v1.csv"
)
DEFAULT_OUTPUT_DIR = "/private/tmp/panel_day_engine_voltage_preserved_confirmation_packet_br093_check"

CANDIDATE_REQUIRED_COLUMNS = [
    "search_candidate_row_id",
    "site",
    "panel_id",
    "hard_episode_anchor_date",
    "onset_candidate_date",
    "gap_days",
    "candidate_tier",
    "candidate_tier_rank",
    "known_review_role",
    "truth_search_action",
    "candidate_priority",
    "manual_review_ready",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "window_day_rows",
    "window_signal_days",
    "event_A_days",
    "low_mid_days",
    "voltage_low_current_ok_days",
    "current_low_voltage_ok_days",
    "both_low_vi_days",
    "hard_anchor_days",
    "common_cause_days",
    "data_bad_days",
    "median_signal_mid_ratio",
    "median_signal_mid_v_ratio",
    "median_signal_mid_i_ratio",
    "min_window_mid_ratio",
    "median_signal_dtw_dist",
    "max_window_dtw_dist",
    "max_window_co_drop_frac",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

PACKET_COLUMNS = [
    "owner_branch",
    "confirmation_packet_row_id",
    "confirmation_family_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "review_priority",
    "confirmation_status",
    "representative_candidate_row_id",
    "representative_candidate_tier",
    "representative_anchor_date",
    "representative_onset_date",
    "representative_gap_days",
    "candidate_rows_for_panel",
    "unique_anchor_dates_for_panel",
    "min_gap_days_for_panel",
    "median_gap_days_for_panel",
    "max_gap_days_for_panel",
    "max_candidate_tier_rank_for_panel",
    "max_voltage_low_current_ok_days_for_panel",
    "max_event_A_days_for_panel",
    "max_low_mid_days_for_panel",
    "representative_window_day_rows",
    "representative_window_signal_days",
    "representative_voltage_low_current_ok_days",
    "representative_median_signal_mid_ratio",
    "representative_median_signal_mid_v_ratio",
    "representative_median_signal_mid_i_ratio",
    "representative_min_window_mid_ratio",
    "same_root_known_positive_seed_count",
    "same_root_known_negative_overlap_count",
    "same_root_known_hold_overlap_count",
    "same_panel_known_positive_seed_count",
    "same_panel_known_negative_overlap_count",
    "counterexample_risk_flag",
    "required_confirmation_axes",
    "independent_source_attached",
    "raw_waveform_confirmation_attached",
    "physical_or_maintenance_confirmation_attached",
    "common_cause_cleared",
    "measurement_artifact_cleared",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

FAMILY_COLUMNS = [
    "owner_branch",
    "confirmation_family_id",
    "site",
    "root_id",
    "family_review_priority",
    "confirmation_status",
    "packet_rows",
    "source_candidate_rows",
    "unique_panel_groups",
    "unique_panels",
    "unique_anchor_dates",
    "best_candidate_row_id",
    "best_candidate_tier",
    "max_candidate_tier_rank",
    "min_gap_days",
    "median_gap_days",
    "max_gap_days",
    "max_voltage_low_current_ok_days",
    "counterexample_risk_flag",
    "same_root_known_positive_seed_count",
    "same_root_known_negative_overlap_count",
    "same_root_known_hold_overlap_count",
    "positive_truth_candidate_approved_sum",
    "threshold_tuning_approved_sum",
    "operator_facing_change_allowed_sum",
    "engine_patch_allowed_sum",
    "threshold_patch_allowed_sum",
    "next_review_action",
    "notes",
]

MAP_COLUMNS = [
    "owner_branch",
    "confirmation_family_id",
    "confirmation_packet_row_id",
    "search_candidate_row_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "hard_episode_anchor_date",
    "onset_candidate_date",
    "gap_days",
    "candidate_tier",
    "candidate_priority",
    "known_review_role",
    "manual_review_ready",
    "map_role",
    "positive_truth_candidate_approved",
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


def rounded(value: object) -> float:
    return round(numeric_float(value), 6)


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


def panel_root(panel_id: object) -> str:
    return normalize_text(panel_id).split(".")[0]


def panel_group_key(panel_id: object) -> str:
    parts = normalize_text(panel_id).split(".")
    if len(parts) >= 2:
        return ".".join(parts[:2])
    return normalize_text(panel_id)


def normalize_candidates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in [
        "search_candidate_row_id",
        "site",
        "panel_id",
        "hard_episode_anchor_date",
        "onset_candidate_date",
        "candidate_tier",
        "known_review_role",
        "truth_search_action",
        "candidate_priority",
    ]:
        out[col] = out[col].map(normalize_text)
    for col in [
        "gap_days",
        "candidate_tier_rank",
        "manual_review_ready",
        "positive_truth_candidate_approved",
        "threshold_tuning_approved",
        "window_day_rows",
        "window_signal_days",
        "event_A_days",
        "low_mid_days",
        "voltage_low_current_ok_days",
        "current_low_voltage_ok_days",
        "both_low_vi_days",
        "hard_anchor_days",
        "common_cause_days",
        "data_bad_days",
        "median_signal_mid_ratio",
        "median_signal_mid_v_ratio",
        "median_signal_mid_i_ratio",
        "min_window_mid_ratio",
        "median_signal_dtw_dist",
        "max_window_dtw_dist",
        "max_window_co_drop_frac",
        "operator_facing_change_allowed",
        "engine_patch_allowed",
        "threshold_patch_allowed",
    ]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    for col in [
        "manual_review_ready",
        "positive_truth_candidate_approved",
        "threshold_tuning_approved",
        "operator_facing_change_allowed",
        "engine_patch_allowed",
        "threshold_patch_allowed",
    ]:
        out[col] = out[col].astype(int)
    out["root_id"] = out["panel_id"].map(panel_root)
    out["panel_group_key"] = out["panel_id"].map(panel_group_key)
    return out


def assert_safe_input(df: pd.DataFrame) -> None:
    for col in [
        "positive_truth_candidate_approved",
        "threshold_tuning_approved",
        "operator_facing_change_allowed",
        "engine_patch_allowed",
        "threshold_patch_allowed",
    ]:
        total = int(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())
        if total != 0:
            raise ValueError(f"BR-093 requires non-authorizing BR-092 input; {col} sum is {total}")


def best_candidate(group: pd.DataFrame) -> pd.Series:
    sort_cols = [
        "candidate_tier_rank",
        "voltage_low_current_ok_days",
        "window_signal_days",
        "low_mid_days",
        "gap_days",
        "hard_episode_anchor_date",
    ]
    ranked = group.sort_values(sort_cols, ascending=[False, False, False, False, False, True])
    return ranked.iloc[0]


def review_priority(max_rank: int, anchor_count: int) -> str:
    if max_rank >= 3 and anchor_count >= 2:
        return "P0_multi_anchor_strong_voltage_preserved"
    if max_rank >= 3:
        return "P0_single_anchor_strong_voltage_preserved"
    if max_rank >= 2:
        return "P1_repeated_voltage_preserved_10d"
    return "P2_context_only"


def family_priority(packet_group: pd.DataFrame) -> str:
    if packet_group["review_priority"].str.startswith("P0_multi").any():
        return "P0_family_multi_anchor_strong"
    if packet_group["review_priority"].str.startswith("P0").any():
        return "P0_family_strong"
    if packet_group["review_priority"].str.startswith("P1").any():
        return "P1_family_repeated_voltage"
    return "P2_family_context_only"


def known_counts(df: pd.DataFrame, site: str, root_id: str, panel_id: str) -> dict[str, int]:
    same_root = df.loc[df["site"].eq(site) & df["root_id"].eq(root_id)].copy()
    same_panel = same_root.loc[same_root["panel_id"].eq(panel_id)].copy()
    return {
        "same_root_known_positive_seed_count": int(same_root["known_review_role"].eq("known_positive_seed").sum()),
        "same_root_known_negative_overlap_count": int(
            same_root["known_review_role"].eq("known_negative_counterexample").sum()
        ),
        "same_root_known_hold_overlap_count": int(same_root["known_review_role"].eq("known_deferred_hold").sum()),
        "same_panel_known_positive_seed_count": int(same_panel["known_review_role"].eq("known_positive_seed").sum()),
        "same_panel_known_negative_overlap_count": int(
            same_panel["known_review_role"].eq("known_negative_counterexample").sum()
        ),
    }


def build_packet(owner_branch: str, candidates_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    manual = candidates_df.loc[
        candidates_df["known_review_role"].eq("new_search_candidate") & candidates_df["manual_review_ready"].eq(1)
    ].copy()
    rows: list[dict[str, object]] = []
    map_rows: list[dict[str, object]] = []
    groups = manual.groupby(["site", "root_id", "panel_group_key", "panel_id"], sort=True)
    family_ids: dict[tuple[str, str], str] = {}
    for family_idx, key in enumerate(sorted(manual.groupby(["site", "root_id"]).groups.keys()), start=1):
        family_ids[key] = f"BR093-VPCF-{family_idx:03d}"

    packet_idx = 0
    for (site, root_id, group_key, panel_id), group in groups:
        packet_idx += 1
        family_id = family_ids[(site, root_id)]
        packet_id = f"BR093-VPCP-{packet_idx:03d}"
        best = best_candidate(group)
        anchor_count = int(group["hard_episode_anchor_date"].nunique())
        max_rank = numeric_int(group["candidate_tier_rank"].max())
        counts = known_counts(candidates_df, site, root_id, panel_id)
        risk = int(counts["same_root_known_negative_overlap_count"] > 0)
        rows.append(
            {
                "owner_branch": owner_branch,
                "confirmation_packet_row_id": packet_id,
                "confirmation_family_id": family_id,
                "site": site,
                "root_id": root_id,
                "panel_group_key": group_key,
                "panel_id": panel_id,
                "review_priority": review_priority(max_rank, anchor_count),
                "confirmation_status": "needs_independent_confirmation",
                "representative_candidate_row_id": normalize_text(best["search_candidate_row_id"]),
                "representative_candidate_tier": normalize_text(best["candidate_tier"]),
                "representative_anchor_date": normalize_text(best["hard_episode_anchor_date"]),
                "representative_onset_date": normalize_text(best["onset_candidate_date"]),
                "representative_gap_days": numeric_int(best["gap_days"]),
                "candidate_rows_for_panel": int(len(group)),
                "unique_anchor_dates_for_panel": anchor_count,
                "min_gap_days_for_panel": numeric_int(group["gap_days"].min()),
                "median_gap_days_for_panel": rounded(group["gap_days"].median()),
                "max_gap_days_for_panel": numeric_int(group["gap_days"].max()),
                "max_candidate_tier_rank_for_panel": max_rank,
                "max_voltage_low_current_ok_days_for_panel": numeric_int(group["voltage_low_current_ok_days"].max()),
                "max_event_A_days_for_panel": numeric_int(group["event_A_days"].max()),
                "max_low_mid_days_for_panel": numeric_int(group["low_mid_days"].max()),
                "representative_window_day_rows": numeric_int(best["window_day_rows"]),
                "representative_window_signal_days": numeric_int(best["window_signal_days"]),
                "representative_voltage_low_current_ok_days": numeric_int(best["voltage_low_current_ok_days"]),
                "representative_median_signal_mid_ratio": rounded(best["median_signal_mid_ratio"]),
                "representative_median_signal_mid_v_ratio": rounded(best["median_signal_mid_v_ratio"]),
                "representative_median_signal_mid_i_ratio": rounded(best["median_signal_mid_i_ratio"]),
                "representative_min_window_mid_ratio": rounded(best["min_window_mid_ratio"]),
                **counts,
                "counterexample_risk_flag": risk,
                "required_confirmation_axes": (
                    "independent_source_or_raw_waveform;"
                    "physical_or_maintenance_record;"
                    "common_cause_clearance;"
                    "measurement_artifact_clearance"
                ),
                "independent_source_attached": 0,
                "raw_waveform_confirmation_attached": 0,
                "physical_or_maintenance_confirmation_attached": 0,
                "common_cause_cleared": 0,
                "measurement_artifact_cleared": 0,
                "positive_truth_candidate_approved": 0,
                "threshold_tuning_approved": 0,
                "operator_facing_change_allowed": 0,
                "engine_patch_allowed": 0,
                "threshold_patch_allowed": 0,
                "notes": (
                    "Review packet only; same-root known negative overlap requires extra caution."
                    if risk
                    else "Review packet only; attach independent confirmation before truth use."
                ),
            }
        )
        for row in group.to_dict(orient="records"):
            map_rows.append(
                {
                    "owner_branch": owner_branch,
                    "confirmation_family_id": family_id,
                    "confirmation_packet_row_id": packet_id,
                    "search_candidate_row_id": normalize_text(row["search_candidate_row_id"]),
                    "site": site,
                    "root_id": root_id,
                    "panel_group_key": group_key,
                    "panel_id": panel_id,
                    "hard_episode_anchor_date": normalize_text(row["hard_episode_anchor_date"]),
                    "onset_candidate_date": normalize_text(row["onset_candidate_date"]),
                    "gap_days": numeric_int(row["gap_days"]),
                    "candidate_tier": normalize_text(row["candidate_tier"]),
                    "candidate_priority": normalize_text(row["candidate_priority"]),
                    "known_review_role": normalize_text(row["known_review_role"]),
                    "manual_review_ready": numeric_int(row["manual_review_ready"]),
                    "map_role": "source_candidate_for_confirmation_packet",
                    "positive_truth_candidate_approved": 0,
                    "threshold_tuning_approved": 0,
                    "operator_facing_change_allowed": 0,
                    "engine_patch_allowed": 0,
                    "threshold_patch_allowed": 0,
                    "notes": "Trace row from BR-092 candidate reservoir to BR-093 confirmation packet.",
                }
            )
    return (
        pd.DataFrame(rows).reindex(columns=PACKET_COLUMNS),
        pd.DataFrame(map_rows).reindex(columns=MAP_COLUMNS),
    )


def build_family_summary(owner_branch: str, packet_df: pd.DataFrame, candidate_map_df: pd.DataFrame) -> pd.DataFrame:
    if packet_df.empty:
        return pd.DataFrame(columns=FAMILY_COLUMNS)
    rows: list[dict[str, object]] = []
    for family_id, group in packet_df.groupby("confirmation_family_id", sort=False):
        site = normalize_text(group["site"].iloc[0])
        root_id = normalize_text(group["root_id"].iloc[0])
        mapped = candidate_map_df.loc[candidate_map_df["confirmation_family_id"].eq(family_id)].copy()
        best = group.sort_values(
            [
                "max_candidate_tier_rank_for_panel",
                "max_voltage_low_current_ok_days_for_panel",
                "unique_anchor_dates_for_panel",
                "max_gap_days_for_panel",
            ],
            ascending=[False, False, False, False],
        ).iloc[0]
        risk = int(group["counterexample_risk_flag"].max())
        rows.append(
            {
                "owner_branch": owner_branch,
                "confirmation_family_id": family_id,
                "site": site,
                "root_id": root_id,
                "family_review_priority": family_priority(group),
                "confirmation_status": "needs_independent_confirmation",
                "packet_rows": int(len(group)),
                "source_candidate_rows": int(len(mapped)),
                "unique_panel_groups": int(group["panel_group_key"].nunique()),
                "unique_panels": int(group["panel_id"].nunique()),
                "unique_anchor_dates": int(mapped["hard_episode_anchor_date"].nunique()) if not mapped.empty else 0,
                "best_candidate_row_id": normalize_text(best["representative_candidate_row_id"]),
                "best_candidate_tier": normalize_text(best["representative_candidate_tier"]),
                "max_candidate_tier_rank": numeric_int(group["max_candidate_tier_rank_for_panel"].max()),
                "min_gap_days": numeric_int(mapped["gap_days"].min()) if not mapped.empty else 0,
                "median_gap_days": rounded(mapped["gap_days"].median()) if not mapped.empty else 0.0,
                "max_gap_days": numeric_int(mapped["gap_days"].max()) if not mapped.empty else 0,
                "max_voltage_low_current_ok_days": numeric_int(
                    group["max_voltage_low_current_ok_days_for_panel"].max()
                ),
                "counterexample_risk_flag": risk,
                "same_root_known_positive_seed_count": numeric_int(
                    group["same_root_known_positive_seed_count"].max()
                ),
                "same_root_known_negative_overlap_count": numeric_int(
                    group["same_root_known_negative_overlap_count"].max()
                ),
                "same_root_known_hold_overlap_count": numeric_int(group["same_root_known_hold_overlap_count"].max()),
                "positive_truth_candidate_approved_sum": 0,
                "threshold_tuning_approved_sum": 0,
                "operator_facing_change_allowed_sum": 0,
                "engine_patch_allowed_sum": 0,
                "threshold_patch_allowed_sum": 0,
                "next_review_action": (
                    "counterexample_guarded_confirmation_review"
                    if risk
                    else "independent_confirmation_review"
                ),
                "notes": (
                    "Same root has known negative overlap; require stronger confirmation before truth use."
                    if risk
                    else "Candidate family is ready for independent confirmation packet review."
                ),
            }
        )
    return pd.DataFrame(rows).reindex(columns=FAMILY_COLUMNS)


def build_action_queue(owner_branch: str, packet_df: pd.DataFrame, family_df: pd.DataFrame) -> pd.DataFrame:
    p0_rows = 0 if packet_df.empty else int(packet_df["review_priority"].str.startswith("P0").sum())
    risk_families = 0 if family_df.empty else int(family_df["counterexample_risk_flag"].sum())
    rows = [
        {
            "owner_branch": owner_branch,
            "sequence": 1,
            "action_id": "BR093-ACT-001",
            "action": "attach independent confirmation to P0 packet rows",
            "input_filter": "review_priority starts with P0",
            "purpose": "turn repeated voltage-preserved search hits into evidence-backed truth candidates only when independently confirmed",
            "success_boundary": f"P0 packet rows={p0_rows}; approvals remain 0 until confirmation fields are filled",
            "recommended_next_artifact": "voltage_preserved_confirmation_attachment_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Raw waveform, physical inspection, maintenance, or independent source evidence is required.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 2,
            "action_id": "BR093-ACT-002",
            "action": "treat same-root known negative overlap as a review blocker",
            "input_filter": "counterexample_risk_flag=1",
            "purpose": "avoid converting a search pattern into truth when a nearby reviewed counterexample exists",
            "success_boundary": f"risk families={risk_families}; threshold tuning remains 0",
            "recommended_next_artifact": "voltage_preserved_counterexample_guard_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "Counterexample-risk families need stronger evidence or exclusion before truth rebuild.",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 3,
            "action_id": "BR093-ACT-003",
            "action": "rebuild truth rows only after confirmation fields are populated",
            "input_filter": "all required confirmation axes cleared",
            "purpose": "keep canonical truth and replay input stable until review evidence is attached",
            "success_boundary": "positive truth rows are created in a later branch, not in BR-093",
            "recommended_next_artifact": "reviewed_episode_truth_rows_confirmed_positive_rebuild_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "BR-093 is a packet, not a truth rewrite.",
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
    candidate_input: Path,
    packet_df: pd.DataFrame,
    family_df: pd.DataFrame,
    candidate_map_df: pd.DataFrame,
) -> None:
    family_cols = [
        "confirmation_family_id",
        "site",
        "root_id",
        "family_review_priority",
        "packet_rows",
        "source_candidate_rows",
        "unique_panels",
        "max_gap_days",
        "counterexample_risk_flag",
        "next_review_action",
    ]
    priority_counts = (
        packet_df["review_priority"].value_counts().sort_index().to_dict() if not packet_df.empty else {}
    )
    lines = [
        "# panel_day_engine_voltage_preserved_confirmation_packet_v1",
        "",
        "## Purpose",
        "- Compress BR-092 manual-review-ready candidate rows into panel-level confirmation tasks and root-family summaries.",
        "- Preserve candidate-to-packet traceability while preventing repeated hard episodes from inflating truth support.",
        "- Keep all truth, threshold, operator-facing, and engine-patch approvals blocked.",
        "",
        "## Input",
        f"- BR-092 candidates: `{candidate_input}`",
        "",
        "## Real Result",
        f"- owner_branch: `{owner_branch}`",
        f"- source candidate map rows: `{len(candidate_map_df)}`",
        f"- confirmation packet rows: `{len(packet_df)}`",
        f"- confirmation family rows: `{len(family_df)}`",
        f"- review priority counts: `{json.dumps(priority_counts, ensure_ascii=False, sort_keys=True)}`",
        f"- counterexample-risk packet rows: `{int(packet_df['counterexample_risk_flag'].sum()) if not packet_df.empty else 0}`",
        f"- counterexample-risk families: `{int(family_df['counterexample_risk_flag'].sum()) if not family_df.empty else 0}`",
        f"- positive truth candidate approved sum: `{int(packet_df['positive_truth_candidate_approved'].sum()) if not packet_df.empty else 0}`",
        f"- threshold tuning approved sum: `{int(packet_df['threshold_tuning_approved'].sum()) if not packet_df.empty else 0}`",
        f"- engine patch allowed sum: `{int(packet_df['engine_patch_allowed'].sum()) if not packet_df.empty else 0}`",
        "",
        "## Family Summary",
        dataframe_to_markdown(family_df.loc[:, family_cols] if not family_df.empty else family_df),
        "",
        "## Safety Boundary",
        "- BR-093 is a confirmation packet only.",
        "- Packet rows are not positive truth labels.",
        "- No threshold tuning or direct `panel_day_engine.py` edit is approved.",
        "- Same-root known negative overlap is carried as a blocker/caution flag.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(
    path: Path,
    owner_branch: str,
    repo_root: Path,
    output_dir: Path,
    candidate_input: Path,
    packet_df: pd.DataFrame,
    family_df: pd.DataFrame,
    candidate_map_df: pd.DataFrame,
) -> None:
    payload = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "candidate_input": str(candidate_input),
        "source_candidate_map_rows": int(len(candidate_map_df)),
        "confirmation_packet_rows": int(len(packet_df)),
        "confirmation_family_rows": int(len(family_df)),
        "review_priority_counts": packet_df["review_priority"].value_counts().sort_index().to_dict()
        if not packet_df.empty
        else {},
        "counterexample_risk_packet_rows": int(packet_df["counterexample_risk_flag"].sum())
        if not packet_df.empty
        else 0,
        "counterexample_risk_families": int(family_df["counterexample_risk_flag"].sum())
        if not family_df.empty
        else 0,
        "positive_truth_candidate_approved_sum": int(packet_df["positive_truth_candidate_approved"].sum())
        if not packet_df.empty
        else 0,
        "threshold_tuning_approved_sum": int(packet_df["threshold_tuning_approved"].sum())
        if not packet_df.empty
        else 0,
        "operator_facing_change_allowed_sum": int(packet_df["operator_facing_change_allowed"].sum())
        if not packet_df.empty
        else 0,
        "engine_patch_allowed_sum": int(packet_df["engine_patch_allowed"].sum()) if not packet_df.empty else 0,
        "threshold_patch_allowed_sum": int(packet_df["threshold_patch_allowed"].sum())
        if not packet_df.empty
        else 0,
        "recommended_next_branch": "voltage_preserved_confirmation_attachment_v1",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "packet": str(output_dir / PACKET_OUTPUT_NAME),
            "family_summary": str(output_dir / FAMILY_OUTPUT_NAME),
            "candidate_map": str(output_dir / MAP_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a confirmation packet from BR-092 voltage-preserved candidates.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--candidate-input", default=DEFAULT_CANDIDATE_INPUT, help="BR-092 candidate CSV.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory for BR-093 artifacts.")
    parser.add_argument("--owner-branch", default="BR-20260425-093")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    candidate_input = resolve_path(repo_root, args.candidate_input)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    candidates_df = normalize_candidates(
        read_required_csv(candidate_input, CANDIDATE_REQUIRED_COLUMNS, "BR-092 candidates")
    )
    assert_safe_input(candidates_df)
    packet_df, candidate_map_df = build_packet(args.owner_branch, candidates_df)
    family_df = build_family_summary(args.owner_branch, packet_df, candidate_map_df)
    action_df = build_action_queue(args.owner_branch, packet_df, family_df)

    packet_df.to_csv(output_dir / PACKET_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    family_df.to_csv(output_dir / FAMILY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    candidate_map_df.to_csv(output_dir / MAP_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir / NOTE_OUTPUT_NAME, args.owner_branch, candidate_input, packet_df, family_df, candidate_map_df)
    write_json(
        output_dir / JSON_OUTPUT_NAME,
        args.owner_branch,
        repo_root,
        output_dir,
        candidate_input,
        packet_df,
        family_df,
        candidate_map_df,
    )

    print(
        json.dumps(
            {
                "owner_branch": args.owner_branch,
                "source_candidate_map_rows": int(len(candidate_map_df)),
                "confirmation_packet_rows": int(len(packet_df)),
                "confirmation_family_rows": int(len(family_df)),
                "review_priority_counts": packet_df["review_priority"].value_counts().sort_index().to_dict()
                if not packet_df.empty
                else {},
                "counterexample_risk_packet_rows": int(packet_df["counterexample_risk_flag"].sum())
                if not packet_df.empty
                else 0,
                "counterexample_risk_families": int(family_df["counterexample_risk_flag"].sum())
                if not family_df.empty
                else 0,
                "positive_truth_candidate_approved_sum": int(packet_df["positive_truth_candidate_approved"].sum())
                if not packet_df.empty
                else 0,
                "threshold_tuning_approved_sum": int(packet_df["threshold_tuning_approved"].sum())
                if not packet_df.empty
                else 0,
                "outputs": {
                    "packet": str(output_dir / PACKET_OUTPUT_NAME),
                    "family_summary": str(output_dir / FAMILY_OUTPUT_NAME),
                    "candidate_map": str(output_dir / MAP_OUTPUT_NAME),
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
