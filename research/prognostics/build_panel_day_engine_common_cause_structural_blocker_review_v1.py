#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_EXACT_SEED_INPUT = Path(
    "/private/tmp/common_cause_exact_seed_search_check/"
    "panel_day_engine_common_cause_exact_seed_search_v1.csv"
)

DETAIL_OUTPUT_NAME = "panel_day_engine_common_cause_structural_blocker_review_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_common_cause_structural_blocker_review_summary_v1.csv"
SITE_SUMMARY_OUTPUT_NAME = "panel_day_engine_common_cause_structural_blocker_site_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_common_cause_structural_blocker_review_note_v1.md"

REQUIRED_COLS = [
    "search_case_id",
    "source_candidate_case_id",
    "site",
    "panel_id",
    "panel_root_id",
    "primary_judgment_role",
    "usage_tag",
    "raw_direct_common_cause_row_count",
    "raw_direct_common_cause_dates",
    "raw_direct_common_cause_family",
    "official_current_entry_flag",
    "official_current_dates",
    "official_current_same_day_overlap_flag",
    "nearest_official_current_gap_days",
    "any_report_lane_entry_flag",
    "report_lane_presence",
    "best_report_lane",
    "synchrony_bucket",
    "common_cause_row_count",
    "site_event_row_count",
    "group_off_row_count",
    "subgroup_common_cause_row_count",
    "max_co_drop_frac",
    "friction_blocker_types",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "threshold_patch_allowed_flag",
]

DETAIL_COLS = [
    "review_case_id",
    "source_search_case_id",
    "source_candidate_case_id",
    "site",
    "panel_id",
    "panel_root_id",
    "structural_blocker_subtype",
    "blocker_axis",
    "patch_readiness_bucket",
    "manual_trace_review_flag",
    "structural_patch_target_review_flag",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "threshold_patch_allowed_flag",
    "raw_direct_common_cause_row_count",
    "raw_direct_common_cause_dates",
    "raw_direct_common_cause_family",
    "official_current_entry_flag",
    "official_current_dates",
    "official_current_same_day_overlap_flag",
    "nearest_official_current_gap_days",
    "report_lane_presence",
    "best_report_lane",
    "synchrony_bucket",
    "common_cause_row_count",
    "site_event_row_count",
    "group_off_row_count",
    "subgroup_common_cause_row_count",
    "max_co_drop_frac",
    "friction_blocker_types",
    "allowed_use",
    "required_next_evidence",
    "review_note",
]

SUMMARY_COLS = [
    "structural_blocker_subtype",
    "blocker_axis",
    "patch_readiness_bucket",
    "cases",
    "unique_panel_roots",
    "raw_direct_common_cause_rows",
    "manual_trace_review_sum",
    "structural_patch_target_review_sum",
    "operator_promotion_allowed_sum",
    "engine_patch_candidate_sum",
    "threshold_patch_allowed_sum",
]

SITE_SUMMARY_COLS = [
    "site",
    "structural_blocker_subtype",
    "cases",
    "unique_panel_roots",
    "raw_direct_common_cause_rows",
    "manual_trace_review_sum",
    "structural_patch_target_review_sum",
    "nearest_official_current_gap_min",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Split BR-072 common-cause structural blockers into report-lane/date-alignment "
            "subtypes without authorizing runtime semantics changes."
        )
    )
    parser.add_argument("--exact-seed-input", type=Path, default=DEFAULT_EXACT_SEED_INPUT)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def numeric_value(value: object) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0.0 if pd.isna(numeric) else float(numeric)


def int_value(value: object) -> int:
    return int(round(numeric_value(value)))


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def require_columns(df: pd.DataFrame, cols: list[str], label: str) -> None:
    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise SystemExit(f"{label} is missing columns: {missing}")


def normalize_input(df: pd.DataFrame) -> pd.DataFrame:
    require_columns(df, REQUIRED_COLS, "exact-seed input")
    out = df[REQUIRED_COLS].copy()
    for col in out.columns:
        if out[col].dtype == object:
            out[col] = out[col].map(normalize_text)
    return out.loc[out["primary_judgment_role"].eq("structural_blocker")].reset_index(drop=True)


def classify_subtype(row: pd.Series) -> tuple[str, str, str, int, int, str, str]:
    lane = normalize_text(row["report_lane_presence"])
    best_lane = normalize_text(row["best_report_lane"])
    blocker = normalize_text(row["friction_blocker_types"])
    raw_family = normalize_text(row["raw_direct_common_cause_family"])
    official_current = int_value(row["official_current_entry_flag"]) > 0
    current_overlap = int_value(row["official_current_same_day_overlap_flag"]) > 0
    raw_rows = int_value(row["raw_direct_common_cause_row_count"])

    if official_current and not current_overlap:
        return (
            "official_current_date_displaced",
            "date_alignment",
            "manual_trace_review_only",
            1,
            1,
            "Trace raw direct dates against current fault date and explain the displacement before any rule change.",
            "Official/current entry exists but does not coincide with the raw direct common-cause date.",
        )
    if blocker == "rawonly_near_signal_anchor":
        return (
            "rawonly_near_signal_anchor",
            "near_anchor_trace",
            "manual_trace_review_only",
            1,
            1,
            "Inspect whether the near-anchor raw-only signal can be linked to a report-layer event without overgeneralizing.",
            "Near-anchor raw-only row is plausible for manual trace review but not closure.",
        )
    if lane == "none" or best_lane == "none":
        return (
            "no_report_lane_entry",
            "report_lane_entry",
            "hold_until_report_entry_exists",
            0,
            0,
            "Add or identify a report-layer entry before exact-family closure can be considered.",
            "Raw direct common-cause rows exist, but no report lane entry exists.",
        )
    if "precursor" in lane:
        return (
            "precursor_carryover_without_current_closure",
            "lane_semantics",
            "hold_as_precursor_only_context",
            0,
            0,
            "Separate precursor carryover from official/current exact closure.",
            "The row enters a precursor lane but does not close official/current same-day common-cause evidence.",
        )
    if "rawonly" in lane or "rawonly" in blocker or "rawonly" in raw_family:
        return (
            "rawonly_date_displaced_without_current_closure",
            "rawonly_date_alignment",
            "hold_as_rawonly_context",
            0,
            0,
            "Resolve raw-only date displacement and report-layer absence before any semantic patch.",
            "Raw-only evidence exists but remains outside official/current same-day closure.",
        )
    if raw_rows > 0:
        return (
            "raw_direct_unresolved_structural_blocker",
            "unresolved_alignment",
            "hold_for_manual_triage",
            1,
            0,
            "Manually inspect the raw direct row because it did not match a known blocker subtype.",
            "Raw direct common-cause row exists but no known blocker subtype matched.",
        )
    return (
        "non_raw_structural_context",
        "context_only",
        "hold_as_context",
        0,
        0,
        "Collect direct raw or report-layer evidence before further review.",
        "Structural blocker row lacks direct raw common-cause evidence.",
    )


def allowed_use(patch_readiness: str) -> str:
    if patch_readiness == "manual_trace_review_only":
        return "manual trace review and blocker-target triage only"
    if patch_readiness.startswith("hold_as"):
        return "context and blocker explanation only"
    if patch_readiness == "hold_until_report_entry_exists":
        return "report-lane gap tracking only"
    return "manual triage only"


def build_detail(blockers: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for idx, row in blockers.sort_values(["site", "panel_id", "search_case_id"]).reset_index(drop=True).iterrows():
        subtype, axis, readiness, manual_flag, patch_review_flag, next_evidence, note = classify_subtype(row)
        rows.append(
            {
                "review_case_id": f"BR073-{idx + 1:03d}",
                "source_search_case_id": normalize_text(row["search_case_id"]),
                "source_candidate_case_id": normalize_text(row["source_candidate_case_id"]),
                "site": normalize_text(row["site"]),
                "panel_id": normalize_text(row["panel_id"]),
                "panel_root_id": normalize_text(row["panel_root_id"]),
                "structural_blocker_subtype": subtype,
                "blocker_axis": axis,
                "patch_readiness_bucket": readiness,
                "manual_trace_review_flag": manual_flag,
                "structural_patch_target_review_flag": patch_review_flag,
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
                "threshold_patch_allowed_flag": 0,
                "raw_direct_common_cause_row_count": int_value(row["raw_direct_common_cause_row_count"]),
                "raw_direct_common_cause_dates": normalize_text(row["raw_direct_common_cause_dates"]),
                "raw_direct_common_cause_family": normalize_text(row["raw_direct_common_cause_family"]),
                "official_current_entry_flag": int_value(row["official_current_entry_flag"]),
                "official_current_dates": normalize_text(row["official_current_dates"]),
                "official_current_same_day_overlap_flag": int_value(row["official_current_same_day_overlap_flag"]),
                "nearest_official_current_gap_days": normalize_text(row["nearest_official_current_gap_days"]),
                "report_lane_presence": normalize_text(row["report_lane_presence"]),
                "best_report_lane": normalize_text(row["best_report_lane"]),
                "synchrony_bucket": normalize_text(row["synchrony_bucket"]),
                "common_cause_row_count": int_value(row["common_cause_row_count"]),
                "site_event_row_count": int_value(row["site_event_row_count"]),
                "group_off_row_count": int_value(row["group_off_row_count"]),
                "subgroup_common_cause_row_count": int_value(row["subgroup_common_cause_row_count"]),
                "max_co_drop_frac": round(numeric_value(row["max_co_drop_frac"]), 6),
                "friction_blocker_types": normalize_text(row["friction_blocker_types"]),
                "allowed_use": allowed_use(readiness),
                "required_next_evidence": next_evidence,
                "review_note": note,
            }
        )
    return pd.DataFrame(rows).reindex(columns=DETAIL_COLS)


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary = (
        detail.groupby(["structural_blocker_subtype", "blocker_axis", "patch_readiness_bucket"], dropna=False)
        .agg(
            cases=("review_case_id", "nunique"),
            unique_panel_roots=("panel_root_id", "nunique"),
            raw_direct_common_cause_rows=("raw_direct_common_cause_row_count", "sum"),
            manual_trace_review_sum=("manual_trace_review_flag", "sum"),
            structural_patch_target_review_sum=("structural_patch_target_review_flag", "sum"),
            operator_promotion_allowed_sum=("operator_promotion_allowed_flag", "sum"),
            engine_patch_candidate_sum=("engine_patch_candidate_flag", "sum"),
            threshold_patch_allowed_sum=("threshold_patch_allowed_flag", "sum"),
        )
        .reset_index()
    )
    return summary.reindex(columns=SUMMARY_COLS).sort_values(["structural_blocker_subtype", "blocker_axis"])


def build_site_summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=SITE_SUMMARY_COLS)
    work = detail.copy()
    work["_nearest_gap"] = pd.to_numeric(work["nearest_official_current_gap_days"], errors="coerce")
    summary = (
        work.groupby(["site", "structural_blocker_subtype"], dropna=False)
        .agg(
            cases=("review_case_id", "nunique"),
            unique_panel_roots=("panel_root_id", "nunique"),
            raw_direct_common_cause_rows=("raw_direct_common_cause_row_count", "sum"),
            manual_trace_review_sum=("manual_trace_review_flag", "sum"),
            structural_patch_target_review_sum=("structural_patch_target_review_flag", "sum"),
            nearest_official_current_gap_min=("_nearest_gap", "min"),
        )
        .reset_index()
    )
    summary["nearest_official_current_gap_min"] = summary["nearest_official_current_gap_min"].fillna("")
    return summary.reindex(columns=SITE_SUMMARY_COLS).sort_values(["site", "structural_blocker_subtype"])


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    header = "| " + " | ".join(df.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows = [
        "| " + " | ".join(normalize_text(row[col]) for col in df.columns)
        + " |"
        for row in df.to_dict(orient="records")
    ]
    return "\n".join([header, separator] + rows)


def write_note(output_dir: Path, detail: pd.DataFrame, summary: pd.DataFrame, site_summary: pd.DataFrame) -> None:
    manual_sum = int(detail["manual_trace_review_flag"].sum()) if len(detail) else 0
    patch_review_sum = int(detail["structural_patch_target_review_flag"].sum()) if len(detail) else 0
    lines = [
        "# panel_day_engine_common_cause_structural_blocker_review_note_v1",
        "",
        "## Purpose",
        "- Split BR-072 structural blockers into concrete report-lane/date-alignment subtypes.",
        "- Identify manual trace review targets without authorizing runtime semantic changes.",
        "",
        "## Guardrails",
        f"- detail rows: `{len(detail)}`",
        f"- manual trace review targets: `{manual_sum}`",
        f"- structural patch-target review rows: `{patch_review_sum}`",
        f"- operator promotion allowed sum: `{int(detail['operator_promotion_allowed_flag'].sum()) if len(detail) else 0}`",
        f"- engine patch candidate sum: `{int(detail['engine_patch_candidate_flag'].sum()) if len(detail) else 0}`",
        f"- threshold patch allowed sum: `{int(detail['threshold_patch_allowed_flag'].sum()) if len(detail) else 0}`",
        "",
        "## Summary",
        dataframe_to_markdown(summary),
        "",
        "## Site Summary",
        dataframe_to_markdown(site_summary),
        "",
        "## Interpretation",
        "- Most rows remain lane/date context, not patch-ready semantics.",
        "- Manual trace targets are review targets only; they do not authorize production promotion.",
        "- A future patch would need to prove that a blocker subtype is a data/reporting alignment issue rather than a real common-cause hold condition.",
    ]
    (output_dir / NOTE_OUTPUT_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    blockers = normalize_input(read_csv(args.exact_seed_input))
    detail = build_detail(blockers)
    summary = build_summary(detail)
    site_summary = build_site_summary(detail)
    if len(detail) and int(detail["operator_promotion_allowed_flag"].sum()) != 0:
        raise SystemExit("structural blocker review must not allow operator promotion")
    if len(detail) and int(detail["engine_patch_candidate_flag"].sum()) != 0:
        raise SystemExit("structural blocker review must not allow engine patch")
    if len(detail) and int(detail["threshold_patch_allowed_flag"].sum()) != 0:
        raise SystemExit("structural blocker review must not allow threshold patch")
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    site_summary.to_csv(args.output_dir / SITE_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(args.output_dir, detail, summary, site_summary)


if __name__ == "__main__":
    main()
