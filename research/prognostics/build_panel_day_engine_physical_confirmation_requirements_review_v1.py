#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


DEFAULT_RAW_REVIEW_INPUT = Path(
    "/private/tmp/raw_waveform_physical_support_review_check/"
    "panel_day_engine_raw_waveform_physical_support_review_v1.csv"
)
DEFAULT_MANUAL_EVIDENCE_INPUT = Path("docs/internal/manual_field_evidence_latest.csv")

DETAIL_OUTPUT_NAME = "panel_day_engine_physical_confirmation_requirements_review_v1.csv"
CHECKLIST_OUTPUT_NAME = "panel_day_engine_physical_confirmation_requirements_checklist_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_physical_confirmation_requirements_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_physical_confirmation_requirements_note_v1.md"

RAW_REVIEW_REQUIRED_COLS = [
    "raw_support_case_id",
    "source_review_case_id",
    "source_shape_case_id",
    "source_candidate_case_id",
    "site",
    "panel_id",
    "raw_waveform_support_bucket",
    "candidate_fault_family_label_ko",
    "target_vdom_signal_days",
    "raw_daily_support_frac",
    "raw_median_v_ratio",
    "raw_median_i_ratio",
    "physical_support_score",
    "raw_evidence_limitation_score",
]

DETAIL_COLS = [
    "confirmation_case_id",
    "source_raw_support_case_id",
    "source_review_case_id",
    "source_shape_case_id",
    "source_candidate_case_id",
    "site",
    "panel_id",
    "raw_waveform_support_bucket",
    "candidate_fault_family_label_ko",
    "confirmation_bucket",
    "confirmation_readiness_level",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "threshold_patch_allowed_flag",
    "raw_support_inherited_flag",
    "raw_support_is_independent_confirmation_flag",
    "raw_support_score",
    "raw_evidence_limitation_score",
    "target_vdom_signal_days",
    "raw_daily_support_frac",
    "raw_median_v_ratio",
    "raw_median_i_ratio",
    "manual_site_context_rows",
    "manual_exact_panel_rows",
    "manual_exact_usable_rows",
    "direct_physical_measurement_axis_met",
    "maintenance_or_inspection_axis_met",
    "field_reproducibility_axis_met",
    "same_panel_channel_repetition_axis_met",
    "independent_artifact_exclusion_axis_met",
    "independent_confirmation_required_axes_met",
    "independent_confirmation_required_axes_total",
    "independent_confirmation_optional_axes_met",
    "independent_confirmation_met_flag",
    "required_next_evidence",
    "review_note",
]

CHECKLIST_COLS = [
    "confirmation_case_id",
    "site",
    "panel_id",
    "source_raw_support_case_id",
    "confirmation_axis",
    "axis_required_for_packet_flag",
    "axis_status",
    "satisfies_axis_flag",
    "matched_manual_evidence_rows",
    "site_context_manual_evidence_rows",
    "support_source",
    "why_it_matters",
    "next_action",
]

SUMMARY_COLS = [
    "confirmation_bucket",
    "confirmation_readiness_level",
    "site",
    "cases",
    "independent_confirmation_met_sum",
    "operator_promotion_allowed_sum",
    "engine_patch_candidate_sum",
    "threshold_patch_allowed_sum",
    "manual_site_context_rows_sum",
    "manual_exact_usable_rows_sum",
    "required_axes_met_sum",
    "required_axes_total_sum",
]

CONFIRMATION_AXES = [
    {
        "axis": "direct_physical_measurement",
        "required": 1,
        "patterns": [
            r"\biv\b",
            r"i-v",
            r"curve",
            r"waveform",
            r"thermal",
            r"infrared",
            r"\bir\b",
            r"열화상",
            r"전압\s*측정",
            r"전류\s*측정",
        ],
        "why": "A raw algorithmic waveform proxy needs an independent physical artifact before thresholding.",
        "next": "attach exact-panel IV curve, waveform capture, thermal/IR, or measured electrical artifact",
    },
    {
        "axis": "maintenance_or_inspection_record",
        "required": 1,
        "patterns": [
            r"maintenance",
            r"inspection",
            r"repair",
            r"work\s*order",
            r"ticket",
            r"점검",
            r"정비",
            r"수리",
        ],
        "why": "A field or maintenance record turns morphology support into an auditable physical confirmation packet.",
        "next": "attach exact-panel maintenance, inspection, repair, or work-order record",
    },
    {
        "axis": "field_reproducibility_confirmation",
        "required": 0,
        "patterns": [
            r"field",
            r"confirm",
            r"reproduc",
            r"현장",
            r"확인",
            r"재현",
        ],
        "why": "A reproducible field signature reduces the chance that the observed morphology is a one-off artifact.",
        "next": "record exact-panel field confirmation or reproducible voltage-axis observation",
    },
    {
        "axis": "same_panel_channel_repetition",
        "required": 0,
        "patterns": [
            r"same[-_ ]?panel",
            r"channel",
            r"repeat",
            r"recurrent",
            r"반복",
            r"동일\s*패널",
            r"채널",
        ],
        "why": "Repeated same-panel channel evidence can support family-specific review, but raw support alone is not independent.",
        "next": "attach independent repeated same-panel channel or instrument evidence",
    },
    {
        "axis": "independent_artifact_exclusion",
        "required": 0,
        "patterns": [
            r"artifact[_ -]?excluded",
            r"sensor[_ -]?excluded",
            r"reference[_ -]?ok",
            r"instrumentation",
            r"계측",
            r"센서",
            r"참조",
        ],
        "why": "An explicit artifact-exclusion note keeps measurement/reference issues from being promoted as panel faults.",
        "next": "record exact-panel sensor/reference/instrumentation exclusion evidence",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an audit-only physical confirmation requirements review for BR-068 "
            "raw waveform physical-support rows."
        )
    )
    parser.add_argument("--raw-review-input", type=Path, default=DEFAULT_RAW_REVIEW_INPUT)
    parser.add_argument("--manual-evidence-input", type=Path, default=DEFAULT_MANUAL_EVIDENCE_INPUT)
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


def to_flag(value: object) -> bool:
    text = normalize_text(value).lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return True
    if text in {"0", "false", "f", "no", "n", ""}:
        return False
    return numeric_value(value) > 0


def read_csv(path: Path, required: bool = True) -> pd.DataFrame:
    if not path.exists():
        if required:
            raise SystemExit(f"missing input: {path}")
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def require_columns(df: pd.DataFrame, cols: list[str], label: str) -> None:
    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise SystemExit(f"{label} is missing columns: {missing}")


def normalize_raw_review(raw_review: pd.DataFrame) -> pd.DataFrame:
    require_columns(raw_review, RAW_REVIEW_REQUIRED_COLS, "raw review input")
    out = raw_review.loc[
        raw_review["raw_waveform_support_bucket"]
        .map(normalize_text)
        .isin(
            {
                "raw_waveform_physical_support_review",
                "raw_waveform_physical_support_with_limitations_review",
            }
        )
    ].copy()
    for col in RAW_REVIEW_REQUIRED_COLS:
        out[col] = out[col].map(normalize_text) if out[col].dtype == object else out[col]
    return out.sort_values(["site", "panel_id"]).reset_index(drop=True)


def normalize_manual_evidence(manual: pd.DataFrame) -> pd.DataFrame:
    if manual.empty:
        return pd.DataFrame(
            columns=[
                "site",
                "panel_id",
                "evidence_type",
                "description",
                "note",
                "usable_for_exact_validation",
                "_search_text",
            ]
        )
    out = manual.copy()
    if "site" not in out.columns:
        return pd.DataFrame(
            columns=[
                "site",
                "panel_id",
                "evidence_type",
                "description",
                "note",
                "usable_for_exact_validation",
                "_search_text",
            ]
        )
    for col in ["site", "panel_id", "evidence_type", "description", "note", "usable_for_exact_validation"]:
        if col not in out.columns:
            out[col] = ""
        out[col] = out[col].map(normalize_text)
    out["_search_text"] = (
        out["evidence_type"]
        + " "
        + out["description"]
        + " "
        + out["note"]
    ).str.lower()
    return out


def exact_manual_rows(manual: pd.DataFrame, site: str, panel_id: str) -> pd.DataFrame:
    if manual.empty:
        return manual.copy()
    return manual.loc[manual["site"].eq(site) & manual["panel_id"].eq(panel_id)].copy()


def site_context_rows(manual: pd.DataFrame, site: str) -> pd.DataFrame:
    if manual.empty:
        return manual.copy()
    return manual.loc[manual["site"].eq(site)].copy()


def usable_exact_rows(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return rows.copy()
    return rows.loc[rows["usable_for_exact_validation"].map(to_flag)].copy()


def axis_matched_rows(rows: pd.DataFrame, axis: dict[str, object]) -> pd.DataFrame:
    if rows.empty:
        return rows.copy()
    pattern = re.compile("|".join(str(p) for p in axis["patterns"]), flags=re.IGNORECASE)
    return rows.loc[rows["_search_text"].map(lambda text: bool(pattern.search(text)))].copy()


def raw_support_present(row: pd.Series) -> bool:
    return normalize_text(row["raw_waveform_support_bucket"]) in {
        "raw_waveform_physical_support_review",
        "raw_waveform_physical_support_with_limitations_review",
    }


def axis_status(axis_id: str, matched: int, axis_site_context_count: int, inherited_raw_support: bool) -> tuple[str, str]:
    if matched > 0:
        return "exact_usable_evidence_present", "manual_field_evidence_exact_panel"
    if inherited_raw_support and axis_id in {"same_panel_channel_repetition", "independent_artifact_exclusion"}:
        return "raw_or_proxy_support_present_not_independent", "br067_br068_proxy_support"
    if axis_site_context_count > 0:
        return "site_context_only_not_exact", "manual_field_evidence_site_context"
    return "missing", "none"


def build_case_rows(
    raw_review: pd.DataFrame,
    manual: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    detail_rows: list[dict[str, object]] = []
    checklist_rows: list[dict[str, object]] = []
    required_total = sum(int(axis["required"]) for axis in CONFIRMATION_AXES)

    for idx, raw_row in raw_review.reset_index(drop=True).iterrows():
        site = normalize_text(raw_row["site"])
        panel_id = normalize_text(raw_row["panel_id"])
        confirmation_case_id = f"BR069-{idx + 1:03d}"
        inherited_raw_support = raw_support_present(raw_row)
        exact_rows = exact_manual_rows(manual, site, panel_id)
        exact_usable = usable_exact_rows(exact_rows)
        site_context = site_context_rows(manual, site)

        axis_flags: dict[str, int] = {}
        required_met = 0
        optional_met = 0
        missing_required_axes: list[str] = []

        for axis in CONFIRMATION_AXES:
            axis_id = str(axis["axis"])
            axis_required = int(axis["required"])
            matched = axis_matched_rows(exact_usable, axis)
            matched_count = int(len(matched))
            axis_site_context_count = int(len(axis_matched_rows(site_context, axis)))
            satisfies = int(matched_count > 0)
            if axis_required:
                required_met += satisfies
                if not satisfies:
                    missing_required_axes.append(axis_id)
            else:
                optional_met += satisfies
            axis_flags[f"{axis_id}_axis_met"] = satisfies
            status, support_source = axis_status(
                axis_id,
                matched_count,
                axis_site_context_count,
                inherited_raw_support,
            )
            checklist_rows.append(
                {
                    "confirmation_case_id": confirmation_case_id,
                    "site": site,
                    "panel_id": panel_id,
                    "source_raw_support_case_id": normalize_text(raw_row["raw_support_case_id"]),
                    "confirmation_axis": axis_id,
                    "axis_required_for_packet_flag": axis_required,
                    "axis_status": status,
                    "satisfies_axis_flag": satisfies,
                    "matched_manual_evidence_rows": matched_count,
                    "site_context_manual_evidence_rows": axis_site_context_count,
                    "support_source": support_source,
                    "why_it_matters": str(axis["why"]),
                    "next_action": str(axis["next"]) if not satisfies else "preserve exact evidence link in confirmation packet",
                }
            )

        independent_met = int(required_met == required_total)
        if independent_met:
            confirmation_bucket = "independent_confirmation_packet_ready_review"
            readiness = "medium"
            next_evidence = "review confirmation packet; still run prepatch gates before threshold proposal"
            review_note = "Required independent physical-confirmation axes are present, but this review still does not approve production thresholding."
        elif inherited_raw_support:
            confirmation_bucket = "raw_supported_confirmation_gap_hold"
            readiness = "low"
            next_evidence = "collect exact-panel " + ", ".join(missing_required_axes)
            review_note = "Raw waveform support is present, but required independent confirmation axes are missing."
        else:
            confirmation_bucket = "independent_confirmation_gap_hold"
            readiness = "low"
            next_evidence = "collect raw support and exact-panel " + ", ".join(missing_required_axes)
            review_note = "Independent physical confirmation is missing."

        detail_rows.append(
            {
                "confirmation_case_id": confirmation_case_id,
                "source_raw_support_case_id": normalize_text(raw_row["raw_support_case_id"]),
                "source_review_case_id": normalize_text(raw_row["source_review_case_id"]),
                "source_shape_case_id": normalize_text(raw_row["source_shape_case_id"]),
                "source_candidate_case_id": normalize_text(raw_row["source_candidate_case_id"]),
                "site": site,
                "panel_id": panel_id,
                "raw_waveform_support_bucket": normalize_text(raw_row["raw_waveform_support_bucket"]),
                "candidate_fault_family_label_ko": normalize_text(raw_row["candidate_fault_family_label_ko"]),
                "confirmation_bucket": confirmation_bucket,
                "confirmation_readiness_level": readiness,
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
                "threshold_patch_allowed_flag": 0,
                "raw_support_inherited_flag": int(inherited_raw_support),
                "raw_support_is_independent_confirmation_flag": 0,
                "raw_support_score": int_value(raw_row["physical_support_score"]),
                "raw_evidence_limitation_score": int_value(raw_row["raw_evidence_limitation_score"]),
                "target_vdom_signal_days": int_value(raw_row["target_vdom_signal_days"]),
                "raw_daily_support_frac": round(numeric_value(raw_row["raw_daily_support_frac"]), 6),
                "raw_median_v_ratio": round(numeric_value(raw_row["raw_median_v_ratio"]), 6),
                "raw_median_i_ratio": round(numeric_value(raw_row["raw_median_i_ratio"]), 6),
                "manual_site_context_rows": int(len(site_context)),
                "manual_exact_panel_rows": int(len(exact_rows)),
                "manual_exact_usable_rows": int(len(exact_usable)),
                "direct_physical_measurement_axis_met": axis_flags["direct_physical_measurement_axis_met"],
                "maintenance_or_inspection_axis_met": axis_flags["maintenance_or_inspection_record_axis_met"],
                "field_reproducibility_axis_met": axis_flags["field_reproducibility_confirmation_axis_met"],
                "same_panel_channel_repetition_axis_met": axis_flags["same_panel_channel_repetition_axis_met"],
                "independent_artifact_exclusion_axis_met": axis_flags["independent_artifact_exclusion_axis_met"],
                "independent_confirmation_required_axes_met": required_met,
                "independent_confirmation_required_axes_total": required_total,
                "independent_confirmation_optional_axes_met": optional_met,
                "independent_confirmation_met_flag": independent_met,
                "required_next_evidence": next_evidence,
                "review_note": review_note,
            }
        )

    return (
        pd.DataFrame(detail_rows).reindex(columns=DETAIL_COLS),
        pd.DataFrame(checklist_rows).reindex(columns=CHECKLIST_COLS),
    )


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary = (
        detail.groupby(["confirmation_bucket", "confirmation_readiness_level", "site"], dropna=False)
        .agg(
            cases=("confirmation_case_id", "nunique"),
            independent_confirmation_met_sum=("independent_confirmation_met_flag", "sum"),
            operator_promotion_allowed_sum=("operator_promotion_allowed_flag", "sum"),
            engine_patch_candidate_sum=("engine_patch_candidate_flag", "sum"),
            threshold_patch_allowed_sum=("threshold_patch_allowed_flag", "sum"),
            manual_site_context_rows_sum=("manual_site_context_rows", "sum"),
            manual_exact_usable_rows_sum=("manual_exact_usable_rows", "sum"),
            required_axes_met_sum=("independent_confirmation_required_axes_met", "sum"),
            required_axes_total_sum=("independent_confirmation_required_axes_total", "sum"),
        )
        .reset_index()
    )
    return summary.reindex(columns=SUMMARY_COLS).sort_values(["confirmation_bucket", "site"])


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


def write_note(output_dir: Path, detail: pd.DataFrame, checklist: pd.DataFrame, summary: pd.DataFrame) -> None:
    axis_summary = (
        checklist.groupby(["confirmation_axis", "axis_status"], dropna=False)
        .agg(rows=("confirmation_case_id", "count"), satisfied=("satisfies_axis_flag", "sum"))
        .reset_index()
        if not checklist.empty
        else pd.DataFrame(columns=["confirmation_axis", "axis_status", "rows", "satisfied"])
    )
    lines = [
        "# panel_day_engine_physical_confirmation_requirements_note_v1",
        "",
        "## Purpose",
        "- Convert BR-068 raw waveform support into an explicit independent-confirmation checklist.",
        "- Do not treat raw algorithmic waveform support as direct field confirmation.",
        "- Keep this review audit-only; it does not approve operator promotion, engine patching, or thresholding.",
        "",
        "## Guardrails",
        f"- detail rows: `{len(detail)}`",
        f"- checklist rows: `{len(checklist)}`",
        f"- independent confirmation met sum: `{int(detail['independent_confirmation_met_flag'].sum()) if len(detail) else 0}`",
        f"- operator promotion allowed sum: `{int(detail['operator_promotion_allowed_flag'].sum()) if len(detail) else 0}`",
        f"- engine patch candidate sum: `{int(detail['engine_patch_candidate_flag'].sum()) if len(detail) else 0}`",
        f"- threshold patch allowed sum: `{int(detail['threshold_patch_allowed_flag'].sum()) if len(detail) else 0}`",
        "",
        "## Summary",
        dataframe_to_markdown(summary),
        "",
        "## Axis Status",
        dataframe_to_markdown(axis_summary),
        "",
        "## Interpretation",
        "- `raw_supported_confirmation_gap_hold` means the BR-068 waveform proxy is strong, but exact-panel independent confirmation is still missing.",
        "- A packet is not threshold-ready unless required independent axes are present.",
        "- Even `independent_confirmation_packet_ready_review` would still require BR-060/061/062-style prepatch validation before any semantic rule proposal.",
    ]
    (output_dir / NOTE_OUTPUT_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_review = normalize_raw_review(read_csv(args.raw_review_input))
    manual = normalize_manual_evidence(read_csv(args.manual_evidence_input, required=False))
    detail, checklist = build_case_rows(raw_review, manual)
    summary = build_summary(detail)
    if len(detail) and int(detail["operator_promotion_allowed_flag"].sum()) != 0:
        raise SystemExit("physical confirmation review must not allow operator promotion")
    if len(detail) and int(detail["engine_patch_candidate_flag"].sum()) != 0:
        raise SystemExit("physical confirmation review must not allow direct engine patch")
    if len(detail) and int(detail["threshold_patch_allowed_flag"].sum()) != 0:
        raise SystemExit("physical confirmation review must not allow threshold patching")
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    checklist.to_csv(args.output_dir / CHECKLIST_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(args.output_dir, detail, checklist, summary)


if __name__ == "__main__":
    main()
