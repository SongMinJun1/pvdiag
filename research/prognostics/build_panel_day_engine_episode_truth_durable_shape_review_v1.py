#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


DURABLE_REVIEW_OUTPUT_NAME = "panel_day_engine_episode_truth_durable_shape_review_v1.csv"
MIXED_REVIEW_INPUT_OUTPUT_NAME = "panel_day_engine_episode_truth_review_input_mixed_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_episode_truth_durable_shape_review_summary_v1.csv"
ACTION_OUTPUT_NAME = "panel_day_engine_episode_truth_durable_shape_review_action_queue_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_episode_truth_durable_shape_review_note_v1.md"
JSON_OUTPUT_NAME = "panel_day_engine_episode_truth_durable_shape_review_v1.json"

BR088_ADJUDICATION_DEFAULT = (
    "/private/tmp/panel_day_engine_episode_truth_conservative_adjudication_br088_check/"
    "panel_day_engine_episode_truth_conservative_adjudication_v1.csv"
)
DEFAULT_DATA_ROOT = str(Path(__file__).resolve().parents[2] / "data")

REQUIRED_BR088_COLUMNS = [
    "adjudication_row_id",
    "conservative_decision",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "reviewer_notes",
    "reviewed_truth_row_id",
    "review_packet_id",
    "review_track",
    "site",
    "panel_id",
    "episode_anchor_date",
    "strict_trigger_date",
    "gap_days",
    "source_episode_classes",
    "source_precursor_promotion_decisions",
    "evidence_card_path",
    "evidence_card_exists",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

CORE_REQUIRED_COLUMNS = [
    "date",
    "panel_id",
    "event_A",
    "is_ae_abn",
    "is_ae_strong",
    "fault_like_day",
    "critical_fault",
    "final_fault",
    "re_drop",
    "degraded_candidate",
    "subgroup_common_cause_candidate",
    "data_bad",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "dtw_dist",
    "co_drop_frac",
    "anom_level",
    "ae_strength",
    "anom_subtype",
]

DURABLE_REVIEW_COLUMNS = [
    "owner_branch",
    "shape_review_row_id",
    "shape_review_decision",
    "shape_confidence",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "reviewer_notes",
    "threshold_replay_input_allowed_candidate",
    "positive_replay_candidate",
    "negative_replay_candidate",
    "threshold_tuning_approved",
    "defer_reason",
    "source_adjudication_row_id",
    "source_conservative_decision",
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
    "ae_strong_days",
    "re_drop_days",
    "fault_like_days",
    "critical_fault_days",
    "final_fault_days",
    "hard_anchor_days",
    "common_cause_days",
    "data_bad_days",
    "low_mid_days",
    "severe_low_mid_days",
    "voltage_low_current_ok_days",
    "current_low_voltage_ok_days",
    "both_low_vi_days",
    "median_signal_mid_ratio",
    "median_signal_mid_v_ratio",
    "median_signal_mid_i_ratio",
    "min_window_mid_ratio",
    "median_signal_dtw_dist",
    "max_window_dtw_dist",
    "max_window_co_drop_frac",
    "evidence_card_path",
    "evidence_card_exists",
    "source_episode_classes",
    "source_precursor_promotion_decisions",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
    "notes",
]

MIXED_REVIEW_INPUT_COLUMNS = [
    "review_packet_id",
    "reviewer_truth_label",
    "reviewer_evidence_path",
    "reviewer_notes",
    "reviewed_truth_row_id",
    "shape_review_row_id",
    "shape_review_decision",
    "shape_confidence",
    "evidence_card_path",
]

SUMMARY_COLUMNS = [
    "owner_branch",
    "shape_review_decision",
    "site",
    "rows",
    "positive_replay_candidate_sum",
    "negative_replay_candidate_sum",
    "threshold_replay_input_allowed_candidate_sum",
    "threshold_tuning_approved_sum",
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


def bool_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    text = df[col].map(normalize_text).str.lower()
    truthy = text.isin(["1", "true", "t", "yes", "y"])
    numeric = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return truthy | (numeric > 0)


def numeric_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(0.0, index=df.index)
    return pd.to_numeric(df[col], errors="coerce")


def assert_safe_input(br088_df: pd.DataFrame) -> None:
    for col in ["operator_facing_change_allowed", "engine_patch_allowed", "threshold_patch_allowed"]:
        total = int(br088_df[col].map(numeric_int).sum())
        if total != 0:
            raise ValueError(f"BR-089 requires non-authorizing BR-088 input; {col} sum is {total}")
    invalid_positive = br088_df["reviewer_truth_label"].map(normalize_text).eq("real_precursor").sum()
    if invalid_positive:
        raise ValueError("BR-089 expects no existing positive precursor labels in BR-088 input")


def core_path(data_root: Path, site: str) -> Path:
    return data_root / site / "out" / "panel_day_core.csv"


def read_site_core(data_root: Path, site: str, cache: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if site not in cache:
        path = core_path(data_root, site)
        df = read_required_csv(path, CORE_REQUIRED_COLUMNS, f"{site}/panel_day_core.csv")
        df["panel_id"] = df["panel_id"].map(normalize_text)
        df["date"] = df["date"].map(normalize_text)
        cache[site] = df
    return cache[site]


def summarize_window(core_df: pd.DataFrame, panel_id: str, start_date: str, end_date: str) -> dict[str, object]:
    panel = core_df.loc[
        core_df["panel_id"].map(normalize_text).eq(panel_id)
        & core_df["date"].map(normalize_text).between(start_date, end_date)
    ].copy()
    if panel.empty:
        return {
            "window_day_rows": 0,
            "window_signal_days": 0,
            "event_A_days": 0,
            "ae_strong_days": 0,
            "re_drop_days": 0,
            "fault_like_days": 0,
            "critical_fault_days": 0,
            "final_fault_days": 0,
            "hard_anchor_days": 0,
            "common_cause_days": 0,
            "data_bad_days": 0,
            "low_mid_days": 0,
            "severe_low_mid_days": 0,
            "voltage_low_current_ok_days": 0,
            "current_low_voltage_ok_days": 0,
            "both_low_vi_days": 0,
            "median_signal_mid_ratio": 0.0,
            "median_signal_mid_v_ratio": 0.0,
            "median_signal_mid_i_ratio": 0.0,
            "min_window_mid_ratio": 0.0,
            "median_signal_dtw_dist": 0.0,
            "max_window_dtw_dist": 0.0,
            "max_window_co_drop_frac": 0.0,
        }

    flags = {
        "event_A": bool_series(panel, "event_A"),
        "is_ae_abn": bool_series(panel, "is_ae_abn"),
        "is_ae_strong": bool_series(panel, "is_ae_strong"),
        "fault_like_day": bool_series(panel, "fault_like_day"),
        "critical_fault": bool_series(panel, "critical_fault"),
        "final_fault": bool_series(panel, "final_fault"),
        "re_drop": bool_series(panel, "re_drop"),
        "degraded_candidate": bool_series(panel, "degraded_candidate"),
        "subgroup_common_cause_candidate": bool_series(panel, "subgroup_common_cause_candidate"),
        "data_bad": bool_series(panel, "data_bad"),
    }
    for col in ["mid_ratio", "mid_v_ratio", "mid_i_ratio", "dtw_dist", "co_drop_frac"]:
        panel[col] = numeric_series(panel, col)

    signal_mask = (
        flags["event_A"]
        | flags["is_ae_abn"]
        | flags["is_ae_strong"]
        | flags["fault_like_day"]
        | flags["critical_fault"]
        | flags["final_fault"]
        | flags["re_drop"]
        | flags["degraded_candidate"]
    )
    signal = panel.loc[signal_mask].copy()
    hard_anchor = flags["fault_like_day"] | flags["critical_fault"] | flags["final_fault"]
    low_mid = panel["mid_ratio"] < 0.75
    severe_mid = panel["mid_ratio"] < 0.50
    voltage_low_current_ok = (panel["mid_v_ratio"] < 0.75) & (panel["mid_i_ratio"] >= 0.85)
    current_low_voltage_ok = (panel["mid_i_ratio"] < 0.75) & (panel["mid_v_ratio"] >= 0.85)
    both_low_vi = (panel["mid_i_ratio"] < 0.75) & (panel["mid_v_ratio"] < 0.75)

    return {
        "window_day_rows": int(len(panel)),
        "window_signal_days": int(signal_mask.sum()),
        "event_A_days": int(flags["event_A"].sum()),
        "ae_strong_days": int(flags["is_ae_strong"].sum()),
        "re_drop_days": int(flags["re_drop"].sum()),
        "fault_like_days": int(flags["fault_like_day"].sum()),
        "critical_fault_days": int(flags["critical_fault"].sum()),
        "final_fault_days": int(flags["final_fault"].sum()),
        "hard_anchor_days": int(hard_anchor.sum()),
        "common_cause_days": int(flags["subgroup_common_cause_candidate"].sum()),
        "data_bad_days": int(flags["data_bad"].sum()),
        "low_mid_days": int(low_mid.sum()),
        "severe_low_mid_days": int(severe_mid.sum()),
        "voltage_low_current_ok_days": int(voltage_low_current_ok.sum()),
        "current_low_voltage_ok_days": int(current_low_voltage_ok.sum()),
        "both_low_vi_days": int(both_low_vi.sum()),
        "median_signal_mid_ratio": rounded(signal["mid_ratio"].median()) if not signal.empty else 0.0,
        "median_signal_mid_v_ratio": rounded(signal["mid_v_ratio"].median()) if not signal.empty else 0.0,
        "median_signal_mid_i_ratio": rounded(signal["mid_i_ratio"].median()) if not signal.empty else 0.0,
        "min_window_mid_ratio": rounded(panel["mid_ratio"].min()),
        "median_signal_dtw_dist": rounded(signal["dtw_dist"].median()) if not signal.empty else 0.0,
        "max_window_dtw_dist": rounded(panel["dtw_dist"].max()),
        "max_window_co_drop_frac": rounded(panel["co_drop_frac"].max()),
    }


def classify_durable(row: dict[str, object], metrics: dict[str, object]) -> dict[str, object]:
    if normalize_text(row.get("conservative_decision")) != "defer_positive_or_hold_review":
        return {
            "decision": "carry_forward_negative_counterexample",
            "confidence": "already_source_backed_negative",
            "label": normalize_text(row.get("reviewer_truth_label")),
            "evidence_path": normalize_text(row.get("reviewer_evidence_path")),
            "notes": normalize_text(row.get("reviewer_notes")),
            "replay": numeric_int(row.get("negative_replay_candidate")),
            "positive": 0,
            "negative": numeric_int(row.get("negative_replay_candidate")),
            "tuning": 0,
            "defer_reason": "",
        }

    evidence_card = normalize_text(row.get("evidence_card_path"))
    card_ready = bool(evidence_card) and numeric_int(row.get("evidence_card_exists")) == 1 and Path(evidence_card).exists()
    if not card_ready:
        return {
            "decision": "defer_missing_evidence_card",
            "confidence": "blocked",
            "label": "",
            "evidence_path": "",
            "notes": "",
            "replay": 0,
            "positive": 0,
            "negative": 0,
            "tuning": 0,
            "defer_reason": "evidence card missing or unreadable",
        }

    window_days = int(metrics["window_day_rows"])
    data_bad_limit = max(1, int(round(window_days * 0.05)))
    strong_voltage_precursor = (
        window_days >= 14
        and int(metrics["event_A_days"]) >= 10
        and int(metrics["low_mid_days"]) >= 10
        and int(metrics["voltage_low_current_ok_days"]) >= 10
        and int(metrics["hard_anchor_days"]) >= 1
        and int(metrics["common_cause_days"]) == 0
        and int(metrics["data_bad_days"]) <= data_bad_limit
        and float(metrics["median_signal_mid_v_ratio"]) < 0.75
        and float(metrics["median_signal_mid_i_ratio"]) >= 0.85
    )
    if strong_voltage_precursor:
        return {
            "decision": "fill_positive_durable_voltage_precursor",
            "confidence": "strong_shape_positive_seed",
            "label": "real_precursor",
            "evidence_path": evidence_card,
            "notes": (
                "BR-089 positive seed: durable window has "
                f"event_A_days={metrics['event_A_days']}, low_mid_days={metrics['low_mid_days']}, "
                f"voltage_low_current_ok_days={metrics['voltage_low_current_ok_days']}, "
                f"hard_anchor_days={metrics['hard_anchor_days']}, common_cause_days=0; "
                "threshold tuning is still not approved from this seed alone."
            ),
            "replay": 1,
            "positive": 1,
            "negative": 0,
            "tuning": 0,
            "defer_reason": "",
        }

    if int(metrics["window_signal_days"]) <= 0:
        reason = "no panel-day signal rows inside episode window"
    elif int(metrics["common_cause_days"]) > 0:
        reason = "common-cause overlap must be rejected before positive label"
    elif int(metrics["hard_anchor_days"]) <= 0:
        reason = "no strict/current hard anchor in the reviewed window"
    else:
        reason = (
            "durable evidence exists, but it does not meet the BR-089 strong voltage-preserved precursor rule; "
            "needs raw waveform or independent family-shape review"
        )
    return {
        "decision": "defer_durable_shape_hold",
        "confidence": "needs_more_shape_evidence",
        "label": "",
        "evidence_path": "",
        "notes": "",
        "replay": 0,
        "positive": 0,
        "negative": 0,
        "tuning": 0,
        "defer_reason": reason,
    }


def build_review(owner_branch: str, br088_df: pd.DataFrame, data_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    core_cache: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, object]] = []
    review_rows: list[dict[str, object]] = []
    for idx, row in enumerate(br088_df.to_dict(orient="records"), start=1):
        site = normalize_text(row.get("site"))
        panel_id = normalize_text(row.get("panel_id"))
        start = normalize_text(row.get("episode_anchor_date"))
        end = normalize_text(row.get("strict_trigger_date"))
        metrics = summarize_window(read_site_core(data_root, site, core_cache), panel_id, start, end)
        decision = classify_durable(row, metrics)
        shape_review_row_id = f"BR089-DSR-{idx:03d}"
        base = {
            "owner_branch": owner_branch,
            "shape_review_row_id": shape_review_row_id,
            "shape_review_decision": decision["decision"],
            "shape_confidence": decision["confidence"],
            "reviewer_truth_label": decision["label"],
            "reviewer_evidence_path": decision["evidence_path"],
            "reviewer_notes": decision["notes"],
            "threshold_replay_input_allowed_candidate": decision["replay"],
            "positive_replay_candidate": decision["positive"],
            "negative_replay_candidate": decision["negative"],
            "threshold_tuning_approved": decision["tuning"],
            "defer_reason": decision["defer_reason"],
            "source_adjudication_row_id": normalize_text(row.get("adjudication_row_id")),
            "source_conservative_decision": normalize_text(row.get("conservative_decision")),
            "reviewed_truth_row_id": normalize_text(row.get("reviewed_truth_row_id")),
            "review_packet_id": normalize_text(row.get("review_packet_id")),
            "review_track": normalize_text(row.get("review_track")),
            "site": site,
            "panel_id": panel_id,
            "episode_anchor_date": start,
            "strict_trigger_date": end,
            "gap_days": numeric_int(row.get("gap_days")),
            "evidence_card_path": normalize_text(row.get("evidence_card_path")),
            "evidence_card_exists": numeric_int(row.get("evidence_card_exists")),
            "source_episode_classes": normalize_text(row.get("source_episode_classes")),
            "source_precursor_promotion_decisions": normalize_text(row.get("source_precursor_promotion_decisions")),
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "BR-089 reviews durable positive shape only; threshold tuning remains approval 0.",
        }
        base.update(metrics)
        rows.append(base)
        review_rows.append(
            {
                "review_packet_id": base["review_packet_id"],
                "reviewer_truth_label": decision["label"],
                "reviewer_evidence_path": decision["evidence_path"],
                "reviewer_notes": decision["notes"],
                "reviewed_truth_row_id": base["reviewed_truth_row_id"],
                "shape_review_row_id": shape_review_row_id,
                "shape_review_decision": decision["decision"],
                "shape_confidence": decision["confidence"],
                "evidence_card_path": base["evidence_card_path"],
            }
        )
    return (
        pd.DataFrame(rows).reindex(columns=DURABLE_REVIEW_COLUMNS),
        pd.DataFrame(review_rows).reindex(columns=MIXED_REVIEW_INPUT_COLUMNS),
    )


def build_summary(owner_branch: str, review_df: pd.DataFrame) -> pd.DataFrame:
    if review_df.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    rows: list[dict[str, object]] = []
    for (decision, site), group in review_df.groupby(["shape_review_decision", "site"], dropna=False, sort=True):
        rows.append(
            {
                "owner_branch": owner_branch,
                "shape_review_decision": decision,
                "site": site,
                "rows": int(len(group)),
                "positive_replay_candidate_sum": int(group["positive_replay_candidate"].sum()),
                "negative_replay_candidate_sum": int(group["negative_replay_candidate"].sum()),
                "threshold_replay_input_allowed_candidate_sum": int(
                    group["threshold_replay_input_allowed_candidate"].sum()
                ),
                "threshold_tuning_approved_sum": int(group["threshold_tuning_approved"].sum()),
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
            "action_id": "BR089-ACT-001",
            "action": "rebuild BR-084 with mixed review input",
            "input_filter": "positive seed plus carried-forward negatives",
            "purpose": "verify positive/negative truth rows exist without touching runtime semantics",
            "success_boundary": "BR-084 reports reviewed_positive > 0, reviewed_negative > 0, and patch authorization sums 0",
            "recommended_next_artifact": "panel_day_engine_reviewed_episode_truth_rows_v1",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "mixed truth rows enable a pilot replay review, not tuning approval",
        },
        {
            "owner_branch": owner_branch,
            "sequence": 2,
            "action_id": "BR089-ACT-002",
            "action": "inspect remaining durable shape holds with raw waveform or independent evidence",
            "input_filter": "shape_review_decision=defer_durable_shape_hold",
            "purpose": "avoid turning AE/recovery-only morphology into positive precursor labels",
            "success_boundary": "additional positives require repeatable family-shape plus common-cause rejection",
            "recommended_next_artifact": "durable_shape_hold_raw_waveform_review",
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
            "notes": "do not open direct panel_day_engine.py edits from BR-089 alone",
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
    br088_input: Path,
    data_root: Path,
    review_df: pd.DataFrame,
    mixed_input_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    decision_counts = review_df["shape_review_decision"].value_counts().sort_index().to_dict()
    lines = [
        "# panel_day_engine_episode_truth_durable_shape_review_v1",
        "",
        "## Purpose",
        "- Review BR-088 deferred durable precursor rows against panel-day shape evidence.",
        "- Carry forward source-backed negative labels and add only high-confidence positive durable shape seeds.",
        "- Keep threshold tuning and direct engine patches blocked.",
        "",
        "## Inputs",
        f"- BR-088 adjudication: `{br088_input}`",
        f"- data root: `{data_root}`",
        "",
        "## Real Result",
        f"- owner_branch: `{owner_branch}`",
        f"- review rows: `{len(review_df)}`",
        f"- mixed review input rows: `{len(mixed_input_df)}`",
        f"- positive replay candidate rows: `{int(review_df['positive_replay_candidate'].sum())}`",
        f"- negative replay candidate rows: `{int(review_df['negative_replay_candidate'].sum())}`",
        f"- threshold replay input candidate rows: `{int(review_df['threshold_replay_input_allowed_candidate'].sum())}`",
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
            "- BR-089 adds a positive seed only when durable voltage-shape evidence is strong.",
            "- BR-089 still does not approve threshold tuning.",
            "- Direct `panel_day_engine.py` edits remain blocked by the BR-076 3-gate prepatch runbook.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(
    path: Path,
    owner_branch: str,
    repo_root: Path,
    output_dir: Path,
    br088_input: Path,
    data_root: Path,
    review_df: pd.DataFrame,
    mixed_input_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    payload = {
        "owner_branch": owner_branch,
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "br088_input": str(br088_input),
        "data_root": str(data_root),
        "review_rows": int(len(review_df)),
        "mixed_review_input_rows": int(len(mixed_input_df)),
        "positive_replay_candidate_rows": int(review_df["positive_replay_candidate"].sum()) if not review_df.empty else 0,
        "negative_replay_candidate_rows": int(review_df["negative_replay_candidate"].sum()) if not review_df.empty else 0,
        "threshold_replay_input_candidate_rows": int(review_df["threshold_replay_input_allowed_candidate"].sum())
        if not review_df.empty
        else 0,
        "threshold_tuning_approved": 0,
        "operator_facing_change_allowed_sum": int(review_df["operator_facing_change_allowed"].sum())
        if not review_df.empty
        else 0,
        "engine_patch_allowed_sum": int(review_df["engine_patch_allowed"].sum()) if not review_df.empty else 0,
        "threshold_patch_allowed_sum": int(review_df["threshold_patch_allowed"].sum()) if not review_df.empty else 0,
        "decision_counts": review_df["shape_review_decision"].value_counts().sort_index().to_dict()
        if not review_df.empty
        else {},
        "summary_rows": int(len(summary_df)),
        "recommended_next_branch": "rebuild_br084_mixed_truth_then_pilot_replay_review",
        "direct_engine_patch_boundary": "BR-076 3-gate prepatch runbook required before direct panel_day_engine.py algorithm review",
        "outputs": {
            "durable_shape_review": str(output_dir / DURABLE_REVIEW_OUTPUT_NAME),
            "mixed_review_input": str(output_dir / MIXED_REVIEW_INPUT_OUTPUT_NAME),
            "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
            "action_queue": str(output_dir / ACTION_OUTPUT_NAME),
            "note": str(output_dir / NOTE_OUTPUT_NAME),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review BR-088 deferred durable precursor rows for shape-backed positives.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--br088-input", default=BR088_ADJUDICATION_DEFAULT, help="BR-088 adjudication CSV.")
    parser.add_argument("--data-root", default=DEFAULT_DATA_ROOT, help="Data root containing <site>/out/panel_day_core.csv.")
    parser.add_argument(
        "--output-dir",
        default="/private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check",
        help="Output directory for BR-089 artifacts.",
    )
    parser.add_argument("--owner-branch", default="BR-20260425-089")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    br088_input = resolve_path(repo_root, args.br088_input)
    data_root = resolve_path(repo_root, args.data_root)
    output_dir = resolve_path(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    br088_df = read_required_csv(br088_input, REQUIRED_BR088_COLUMNS, "BR-088 adjudication")
    assert_safe_input(br088_df)
    review_df, mixed_input_df = build_review(args.owner_branch, br088_df, data_root)
    summary_df = build_summary(args.owner_branch, review_df)
    action_df = build_action_queue(args.owner_branch)

    review_df.to_csv(output_dir / DURABLE_REVIEW_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    mixed_input_df.to_csv(output_dir / MIXED_REVIEW_INPUT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    action_df.to_csv(output_dir / ACTION_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(output_dir / NOTE_OUTPUT_NAME, args.owner_branch, br088_input, data_root, review_df, mixed_input_df, summary_df)
    write_json(
        output_dir / JSON_OUTPUT_NAME,
        args.owner_branch,
        repo_root,
        output_dir,
        br088_input,
        data_root,
        review_df,
        mixed_input_df,
        summary_df,
    )

    print(
        json.dumps(
            {
                "owner_branch": args.owner_branch,
                "review_rows": int(len(review_df)),
                "mixed_review_input_rows": int(len(mixed_input_df)),
                "positive_replay_candidate_rows": int(review_df["positive_replay_candidate"].sum()),
                "negative_replay_candidate_rows": int(review_df["negative_replay_candidate"].sum()),
                "threshold_replay_input_candidate_rows": int(
                    review_df["threshold_replay_input_allowed_candidate"].sum()
                ),
                "threshold_tuning_approved": 0,
                "decision_counts": review_df["shape_review_decision"].value_counts().sort_index().to_dict(),
                "outputs": {
                    "durable_shape_review": str(output_dir / DURABLE_REVIEW_OUTPUT_NAME),
                    "mixed_review_input": str(output_dir / MIXED_REVIEW_INPUT_OUTPUT_NAME),
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
