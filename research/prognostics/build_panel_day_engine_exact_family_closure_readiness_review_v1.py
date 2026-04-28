#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_LOCAL_INPUT = Path(
    "/private/tmp/local_morphology_exact_seed_search_check/panel_day_engine_local_morphology_exact_seed_search_v1.csv"
)
DEFAULT_GAP_REVIEW_INPUT = Path(
    "/private/tmp/no_report_heuristic_gap_review_check/panel_day_engine_no_report_heuristic_gap_review_v1.csv"
)
DEFAULT_OBSERVATION_INPUT = Path(
    "/private/tmp/non_fault_morphology_observation_sidecar_check/panel_day_engine_non_fault_morphology_observation_sidecar_v1.csv"
)
DETAIL_OUTPUT_NAME = "panel_day_engine_exact_family_closure_readiness_review_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_exact_family_closure_readiness_review_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_exact_family_closure_readiness_review_note_v1.md"
NO_REPORT_STATUS = "no_report_heuristic_match"
SENSOR_FEEDBACK_TOP1 = "센서·피드백형"

LOCAL_COLS = [
    "site",
    "panel_id",
    "search_status",
    "recovery_bucket",
    "synchrony_bucket",
    "anchor_dates",
    "same_day_dates",
    "raw_top1_ko",
    "raw_top1_score",
    "raw_top2_ko",
    "raw_top3_ko",
    "live_top1_ko",
    "live_external_gpvs_ko",
    "gpvs_pack_external_ko",
    "target_exact_top1_flag",
    "device_response_external_flag",
    "sensor_feedback_top1_flag",
    "recovery_recurrence_flag",
    "exact_same_day_local_morphology_flag",
    "same_day_fault_like_row_count",
    "same_day_final_fault_row_count",
    "same_day_common_cause_row_count",
    "supportive_seed_candidate_flag",
    "exact_family_candidate_flag",
]
GAP_COLS = [
    "site",
    "panel_id",
    "date_alignment_gap_type",
    "heuristic_attachment_gap_type",
    "report_attachment_gap_type",
    "raw_audit_status_ko",
    "raw_final_status_ko",
]
DETAIL_COLS = [
    "site",
    "panel_id",
    "source_search_status",
    "post_br056_closure_class",
    "evidence_grade",
    "raw_top1_ko",
    "raw_top1_score",
    "raw_top2_ko",
    "raw_top3_ko",
    "live_top1_ko",
    "live_external_gpvs_ko",
    "gpvs_pack_external_ko",
    "recovery_bucket",
    "synchrony_bucket",
    "anchor_dates",
    "same_day_dates",
    "target_exact_top1_flag",
    "device_response_external_flag",
    "sensor_feedback_top1_flag",
    "recovery_recurrence_flag",
    "exact_same_day_local_morphology_flag",
    "same_day_fault_like_row_count",
    "same_day_final_fault_row_count",
    "same_day_common_cause_row_count",
    "gap_review_date_alignment_gap_type",
    "gap_review_heuristic_attachment_gap_type",
    "gap_review_report_attachment_gap_type",
    "gap_review_raw_audit_status_ko",
    "gap_review_raw_final_status_ko",
    "br056_sidecar_observation_flag",
    "target_exact_closure_candidate_flag",
    "fault_family_regression_seed_flag",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "recommended_next_action",
    "review_note",
]
SUMMARY_COLS = [
    "post_br056_closure_class",
    "evidence_grade",
    "site",
    "raw_top1_ko",
    "panels",
    "target_exact_closure_candidates",
    "fault_family_regression_seeds",
    "operator_promotion_allowed_sum",
    "engine_patch_candidate_sum",
    "same_day_final_fault_rows",
    "same_day_fault_like_rows",
    "same_day_common_cause_rows",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Review local morphology exact-family readiness after BR-055/BR-056, "
            "splitting target closure candidates from non-target fault-family seeds and closed blockers."
        )
    )
    parser.add_argument("--local-morphology-input", type=Path, default=DEFAULT_LOCAL_INPUT)
    parser.add_argument("--gap-review-input", type=Path, default=DEFAULT_GAP_REVIEW_INPUT)
    parser.add_argument("--observation-sidecar-input", type=Path, default=DEFAULT_OBSERVATION_INPUT)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def to_flag(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return 1
    if text in {"0", "false", "f", "no", "n", ""}:
        return 0
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(float(numeric) > 0)


def to_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def add_missing_columns(df: pd.DataFrame, cols: list[str], default: object = "") -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col not in out.columns:
            out[col] = default
    return out


def read_local(path: Path) -> pd.DataFrame:
    df = add_missing_columns(read_csv(path), LOCAL_COLS)
    missing = [col for col in ["site", "panel_id"] if col not in df.columns]
    if missing:
        raise SystemExit(f"local morphology input is missing columns: {missing}")
    out = df[LOCAL_COLS].copy()
    flag_cols = [
        "target_exact_top1_flag",
        "device_response_external_flag",
        "sensor_feedback_top1_flag",
        "recovery_recurrence_flag",
        "exact_same_day_local_morphology_flag",
        "supportive_seed_candidate_flag",
        "exact_family_candidate_flag",
    ]
    int_cols = [
        "same_day_fault_like_row_count",
        "same_day_final_fault_row_count",
        "same_day_common_cause_row_count",
    ]
    for col in out.columns:
        if col in flag_cols:
            out[col] = out[col].map(to_flag)
        elif col in int_cols:
            out[col] = out[col].map(to_int)
        else:
            out[col] = out[col].map(normalize_text)
    return out


def read_gap_review(path: Path) -> pd.DataFrame:
    df = add_missing_columns(read_csv(path), GAP_COLS)
    out = df[GAP_COLS].copy()
    for col in out.columns:
        out[col] = out[col].map(normalize_text)
    return out.drop_duplicates(["site", "panel_id"], keep="first")


def read_observation_sidecar(path: Path) -> pd.DataFrame:
    df = read_csv(path)
    if "site" not in df.columns or "panel_id" not in df.columns:
        raise SystemExit(f"observation sidecar input is missing site/panel_id: {path}")
    out = df[["site", "panel_id"]].copy()
    out["site"] = out["site"].map(normalize_text)
    out["panel_id"] = out["panel_id"].map(normalize_text)
    out["br056_sidecar_observation_flag"] = 1
    return out.drop_duplicates(["site", "panel_id"], keep="first")


def classify(row: pd.Series) -> tuple[str, str, int, int, str]:
    search_status = normalize_text(row["search_status"])
    raw_top1 = normalize_text(row["raw_top1_ko"])
    exact_candidate = int(row["exact_family_candidate_flag"]) == 1
    same_day_local = int(row["exact_same_day_local_morphology_flag"]) == 1
    same_day_final = int(row["same_day_final_fault_row_count"]) > 0
    same_day_fault_like = int(row["same_day_fault_like_row_count"]) > 0
    sensor_top1 = int(row["sensor_feedback_top1_flag"]) == 1
    supportive_seed = int(row["supportive_seed_candidate_flag"]) == 1
    device_external = int(row["device_response_external_flag"]) == 1
    sidecar = int(row["br056_sidecar_observation_flag"]) == 1
    gap_type = normalize_text(row["gap_review_date_alignment_gap_type"])

    if exact_candidate:
        return (
            "target_exact_family_closure_candidate",
            "exact_family_closure_candidate",
            1,
            1,
            "manual_exact_family_adjudication_before_any_patch",
        )
    if search_status == NO_REPORT_STATUS:
        if sidecar:
            return (
                "closed_non_fault_near_anchor_observation",
                "closed_non_closing_status_blocker",
                0,
                0,
                "closed_by_br056_sidecar_only",
            )
        if gap_type == "date_displaced_gt14d":
            return (
                "closed_non_fault_date_displaced_evidence",
                "closed_non_closing_date_blocker",
                0,
                0,
                "keep_date_displaced_evidence_only",
            )
        return (
            "closed_non_fault_status_gated_no_report",
            "closed_non_closing_status_blocker",
            0,
            0,
            "closed_by_br055_no_engine_patch",
        )
    if same_day_local and same_day_final and sensor_top1:
        return (
            "sensor_feedback_hard_same_day_pressure",
            "ambiguity_pressure_seed",
            0,
            1,
            "keep_as_sensor_feedback_ambiguity_pressure",
        )
    if same_day_local and same_day_final and raw_top1:
        return (
            "hard_same_day_non_target_fault_family_seed",
            "strong_non_target_fault_family_seed",
            0,
            1,
            "add_to_fault_family_regression_seed_review",
        )
    if same_day_local and same_day_fault_like and raw_top1:
        return (
            "fault_like_same_day_non_target_review",
            "fault_like_non_target_review_seed",
            0,
            1,
            "review_as_non_target_fault_family_pressure",
        )
    if supportive_seed:
        return (
            "supportive_device_response_recovery_seed",
            "supportive_hint_not_closure",
            0,
            0,
            "keep_supportive_not_closing",
        )
    if device_external:
        return (
            "external_device_response_supportive_hint",
            "supportive_hint_not_closure",
            0,
            0,
            "keep_external_reference_separate",
        )
    if same_day_local:
        return (
            "same_day_local_non_target_review",
            "non_closing_local_context",
            0,
            0,
            "keep_as_non_target_context",
        )
    return (
        "local_morphology_non_exact",
        "non_closing_local_context",
        0,
        0,
        "keep_as_context_only",
    )


def make_review_note(row: pd.Series) -> str:
    return (
        f"class={row['post_br056_closure_class']}; "
        f"target_exact={row['target_exact_closure_candidate_flag']}; "
        f"regression_seed={row['fault_family_regression_seed_flag']}; "
        f"raw_top1={row['raw_top1_ko'] or 'none'}; "
        f"same_day_final={row['same_day_final_fault_row_count']}; "
        f"operator_promotion=0; engine_patch=0"
    )


def build_detail(local: pd.DataFrame, gap: pd.DataFrame, observation: pd.DataFrame) -> pd.DataFrame:
    df = local.merge(gap, on=["site", "panel_id"], how="left", suffixes=("", "_gap"))
    df = df.merge(observation, on=["site", "panel_id"], how="left")
    df["br056_sidecar_observation_flag"] = df["br056_sidecar_observation_flag"].fillna(0).map(to_flag)
    df = df.rename(
        columns={
            "search_status": "source_search_status",
            "date_alignment_gap_type": "gap_review_date_alignment_gap_type",
            "heuristic_attachment_gap_type": "gap_review_heuristic_attachment_gap_type",
            "report_attachment_gap_type": "gap_review_report_attachment_gap_type",
            "raw_audit_status_ko": "gap_review_raw_audit_status_ko",
            "raw_final_status_ko": "gap_review_raw_final_status_ko",
        }
    )
    class_rows = []
    for _, row in df.iterrows():
        working = row.copy()
        working["search_status"] = row["source_search_status"]
        closure_class, grade, target_flag, regression_flag, next_action = classify(working)
        class_rows.append((closure_class, grade, target_flag, regression_flag, next_action))
    df[
        [
            "post_br056_closure_class",
            "evidence_grade",
            "target_exact_closure_candidate_flag",
            "fault_family_regression_seed_flag",
            "recommended_next_action",
        ]
    ] = pd.DataFrame(class_rows, index=df.index)
    df["operator_promotion_allowed_flag"] = 0
    df["engine_patch_candidate_flag"] = 0
    df["review_note"] = df.apply(make_review_note, axis=1)
    return df[DETAIL_COLS].sort_values(["post_br056_closure_class", "site", "panel_id"]).reset_index(drop=True)


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary = (
        detail.groupby(["post_br056_closure_class", "evidence_grade", "site", "raw_top1_ko"], dropna=False)
        .agg(
            panels=("panel_id", "nunique"),
            target_exact_closure_candidates=("target_exact_closure_candidate_flag", "sum"),
            fault_family_regression_seeds=("fault_family_regression_seed_flag", "sum"),
            operator_promotion_allowed_sum=("operator_promotion_allowed_flag", "sum"),
            engine_patch_candidate_sum=("engine_patch_candidate_flag", "sum"),
            same_day_final_fault_rows=("same_day_final_fault_row_count", "sum"),
            same_day_fault_like_rows=("same_day_fault_like_row_count", "sum"),
            same_day_common_cause_rows=("same_day_common_cause_row_count", "sum"),
        )
        .reset_index()
    )
    return summary[SUMMARY_COLS].sort_values(["post_br056_closure_class", "site", "raw_top1_ko"]).reset_index(drop=True)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    header = "| " + " | ".join(df.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows = [
        "| " + " | ".join(normalize_text(row[col]) for col in df.columns) + " |"
        for row in df.to_dict(orient="records")
    ]
    return "\n".join([header, separator] + rows)


def write_note(output_dir: Path, detail: pd.DataFrame, summary: pd.DataFrame) -> None:
    class_counts = detail["post_br056_closure_class"].value_counts().sort_index().to_dict()
    grade_counts = detail["evidence_grade"].value_counts().sort_index().to_dict()
    target_count = int(detail["target_exact_closure_candidate_flag"].sum())
    target_interpretation = (
        "Target exact-family closure is still absent."
        if target_count == 0
        else "Target exact-family closure candidates require manual adjudication before any patch."
    )
    text = "\n".join(
        [
            "# BR-057 Exact-Family Closure Readiness Review",
            "",
            "## Result",
            f"- reviewed rows: `{len(detail)}`",
            f"- closure class counts: `{class_counts}`",
            f"- evidence grade counts: `{grade_counts}`",
            f"- target exact closure candidates: `{target_count}`",
            f"- fault-family regression seeds: `{int(detail['fault_family_regression_seed_flag'].sum())}`",
            f"- operator promotion allowed sum: `{int(detail['operator_promotion_allowed_flag'].sum())}`",
            f"- engine patch candidate sum: `{int(detail['engine_patch_candidate_flag'].sum())}`",
            "",
            "## Interpretation",
            f"- {target_interpretation}",
            "- Non-target hard same-day fault-family seeds are preserved as regression/review material, not promotion evidence.",
            "- BR-055/BR-056 no-report rows remain closed as non-fault status/date blockers.",
            "- This review does not justify a `panel_day_engine.py` rule or threshold patch.",
            "",
            "## Summary Table",
            dataframe_to_markdown(summary),
            "",
        ]
    )
    (output_dir / NOTE_OUTPUT_NAME).write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    local = read_local(args.local_morphology_input)
    gap = read_gap_review(args.gap_review_input)
    observation = read_observation_sidecar(args.observation_sidecar_input)
    detail = build_detail(local, gap, observation)
    summary = build_summary(detail)
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(args.output_dir, detail, summary)


if __name__ == "__main__":
    main()
