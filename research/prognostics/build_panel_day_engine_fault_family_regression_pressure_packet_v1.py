#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_READINESS_INPUT = Path(
    "/private/tmp/exact_family_closure_readiness_review_check/panel_day_engine_exact_family_closure_readiness_review_v1.csv"
)
DETAIL_OUTPUT_NAME = "panel_day_engine_fault_family_regression_pressure_packet_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_fault_family_regression_pressure_packet_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_fault_family_regression_pressure_packet_note_v1.md"
NON_TARGET_CLASS = "hard_same_day_non_target_fault_family_seed"
SENSOR_PRESSURE_CLASS = "sensor_feedback_hard_same_day_pressure"

INPUT_COLS = [
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
    "target_exact_closure_candidate_flag",
    "fault_family_regression_seed_flag",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
]
DETAIL_COLS = [
    "packet_case_id",
    "site",
    "panel_id",
    "packet_bucket",
    "counterexample_bucket",
    "source_closure_class",
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
    "same_day_fault_like_row_count",
    "same_day_final_fault_row_count",
    "same_day_common_cause_row_count",
    "target_exact_top1_flag",
    "target_exact_closure_candidate_flag",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "expected_reading",
    "prohibited_overgeneralization",
    "regression_assertion",
    "recommended_next_action",
]
SUMMARY_COLS = [
    "packet_bucket",
    "counterexample_bucket",
    "site",
    "raw_top1_ko",
    "cases",
    "target_exact_closure_candidate_sum",
    "operator_promotion_allowed_sum",
    "engine_patch_candidate_sum",
    "same_day_final_fault_rows",
    "same_day_fault_like_rows",
    "same_day_common_cause_rows",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Package BR-057 fault-family regression/pressure seeds as a counterexample packet "
            "without changing runtime semantics."
        )
    )
    parser.add_argument("--readiness-input", type=Path, default=DEFAULT_READINESS_INPUT)
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


def read_readiness(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing readiness input: {path}")
    df = pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
    missing = [col for col in INPUT_COLS if col not in df.columns]
    if missing:
        raise SystemExit(f"readiness input is missing columns: {missing}")
    out = df[INPUT_COLS].copy()
    flag_cols = [
        "target_exact_top1_flag",
        "device_response_external_flag",
        "sensor_feedback_top1_flag",
        "recovery_recurrence_flag",
        "exact_same_day_local_morphology_flag",
        "target_exact_closure_candidate_flag",
        "fault_family_regression_seed_flag",
        "operator_promotion_allowed_flag",
        "engine_patch_candidate_flag",
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


def classify_packet(row: pd.Series) -> tuple[str, str, str, str, str, str]:
    closure_class = normalize_text(row["post_br056_closure_class"])
    raw_top1 = normalize_text(row["raw_top1_ko"]) or "unknown"
    if closure_class == NON_TARGET_CLASS:
        packet_bucket = "non_target_hard_same_day_fault_family_seed"
        counterexample_bucket = "fault_family_boundary_pressure"
        expected_reading = (
            f"same-day hard/final evidence with non-target top1 `{raw_top1}`; "
            "use as family-boundary regression seed only"
        )
        prohibited = (
            "do not reinterpret non-target hard same-day evidence as missing target exact-family closure "
            "or automatic operator promotion"
        )
        assertion = (
            "must remain target_exact_closure_candidate_flag=0 and operator_promotion_allowed_flag=0 "
            "unless a separate family-specific decision changes the contract"
        )
        action = "include_in_fault_family_boundary_regression_packet"
    elif closure_class == SENSOR_PRESSURE_CLASS:
        packet_bucket = "sensor_feedback_hard_same_day_ambiguity_pressure"
        counterexample_bucket = "mlpe_ambiguous"
        expected_reading = (
            "same-day hard/final evidence with sensor-feedback top1; "
            "use as MLPE/device-vs-panel ambiguity pressure only"
        )
        prohibited = (
            "do not collapse sensor-feedback top1 into panel-local target exact-family closure "
            "or confirmed device response without extra evidence"
        )
        assertion = (
            "must remain ambiguity/hold pressure and not become target exact closure or direct promotion"
        )
        action = "include_in_mlpe_ambiguity_regression_packet"
    else:
        raise ValueError(f"unsupported closure class for packet: {closure_class}")
    return packet_bucket, counterexample_bucket, expected_reading, prohibited, assertion, action


def build_detail(readiness: pd.DataFrame) -> pd.DataFrame:
    selected = readiness.loc[readiness["fault_family_regression_seed_flag"] == 1].copy()
    allowed = {NON_TARGET_CLASS, SENSOR_PRESSURE_CLASS}
    unexpected = sorted(set(selected["post_br056_closure_class"]) - allowed)
    if unexpected:
        raise SystemExit(f"unexpected regression seed closure classes: {unexpected}")
    selected = selected.sort_values(["post_br056_closure_class", "site", "raw_top1_ko", "panel_id"]).reset_index(drop=True)
    if selected.empty:
        return pd.DataFrame(columns=DETAIL_COLS)

    class_rows = [classify_packet(row) for _, row in selected.iterrows()]
    selected[
        [
            "packet_bucket",
            "counterexample_bucket",
            "expected_reading",
            "prohibited_overgeneralization",
            "regression_assertion",
            "recommended_next_action",
        ]
    ] = pd.DataFrame(class_rows, index=selected.index)
    selected["packet_case_id"] = [f"BR058-{idx:03d}" for idx in range(1, len(selected) + 1)]
    selected["source_closure_class"] = selected["post_br056_closure_class"]
    selected["operator_promotion_allowed_flag"] = 0
    selected["engine_patch_candidate_flag"] = 0
    selected["target_exact_closure_candidate_flag"] = 0
    return selected[DETAIL_COLS]


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary = (
        detail.groupby(["packet_bucket", "counterexample_bucket", "site", "raw_top1_ko"], dropna=False)
        .agg(
            cases=("packet_case_id", "nunique"),
            target_exact_closure_candidate_sum=("target_exact_closure_candidate_flag", "sum"),
            operator_promotion_allowed_sum=("operator_promotion_allowed_flag", "sum"),
            engine_patch_candidate_sum=("engine_patch_candidate_flag", "sum"),
            same_day_final_fault_rows=("same_day_final_fault_row_count", "sum"),
            same_day_fault_like_rows=("same_day_fault_like_row_count", "sum"),
            same_day_common_cause_rows=("same_day_common_cause_row_count", "sum"),
        )
        .reset_index()
    )
    return summary[SUMMARY_COLS].sort_values(["packet_bucket", "site", "raw_top1_ko"]).reset_index(drop=True)


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


def write_note(output_dir: Path, readiness: pd.DataFrame, detail: pd.DataFrame, summary: pd.DataFrame) -> None:
    source_class_counts = readiness["post_br056_closure_class"].value_counts().sort_index().to_dict()
    packet_counts = detail["packet_bucket"].value_counts().sort_index().to_dict() if not detail.empty else {}
    target_sum = int(detail["target_exact_closure_candidate_flag"].sum()) if not detail.empty else 0
    promotion_sum = int(detail["operator_promotion_allowed_flag"].sum()) if not detail.empty else 0
    engine_sum = int(detail["engine_patch_candidate_flag"].sum()) if not detail.empty else 0
    text = "\n".join(
        [
            "# BR-058 Fault-Family Regression Pressure Packet",
            "",
            "## Source Review Context",
            f"- source readiness rows: `{len(readiness)}`",
            f"- source closure class counts: `{source_class_counts}`",
            "",
            "## Packet Result",
            f"- packet rows: `{len(detail)}`",
            f"- packet bucket counts: `{packet_counts}`",
            f"- target exact closure candidate sum: `{target_sum}`",
            f"- operator promotion allowed sum: `{promotion_sum}`",
            f"- engine patch candidate sum: `{engine_sum}`",
            "",
            "## Interpretation",
            "- This packet is regression/counterexample material only.",
            "- It preserves non-target hard same-day and sensor-feedback ambiguity cases as patch pressure tests.",
            "- It does not close target exact-family evidence.",
            "- It does not justify a `panel_day_engine.py` rule or threshold patch.",
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
    readiness = read_readiness(args.readiness_input)
    detail = build_detail(readiness)
    summary = build_summary(detail)
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(args.output_dir, readiness, detail, summary)


if __name__ == "__main__":
    main()
