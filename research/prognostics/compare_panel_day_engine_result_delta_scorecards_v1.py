#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_SCORECARD_SUMMARY = Path(
    "/private/tmp/panel_engine_result_delta_scorecard_check/"
    "panel_day_engine_result_delta_scorecard_summary_v1.csv"
)
DETAIL_OUTPUT_NAME = "panel_day_engine_result_delta_scorecard_compare_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_result_delta_scorecard_compare_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_result_delta_scorecard_compare_note_v1.md"

COMPARE_METRICS = [
    "overall_status",
    "core_compared_site_count",
    "core_matched_site_count",
    "core_all_compared_sites_match",
    "core_total_diff_count",
    "raw_only_candidate_row_count",
    "published_current_row_count",
    "precursor_candidate_row_count",
    "raw_only_fault_signal_row_count",
    "fault_panel_count",
    "unresolved_panel_count",
    "proximal_common_cause_fault_signal_count",
    "proximal_common_cause_fault_signal_ratio",
    "fixed_reference_row_count",
    "fixed_reference_matched_row_key_count",
    "fixed_reference_overlap_decision_columns_match",
    "prepatch_runbook_status",
    "performance_improvement_claim_allowed",
    "result_change_claim_ko",
]
DETAIL_COLS = [
    "metric_name",
    "baseline_value",
    "post_value",
    "delta_value",
    "changed_flag",
    "claim_layer",
    "interpretation_ko",
]
SUMMARY_COLS = [
    "overall_status",
    "metric_count",
    "changed_metric_count",
    "core_result_changed_flag",
    "core_total_diff_count_delta",
    "raw_only_candidate_row_count_delta",
    "published_current_row_count_delta",
    "precursor_candidate_row_count_delta",
    "raw_only_fault_signal_row_count_delta",
    "fault_panel_count_delta",
    "proximal_common_cause_fault_signal_count_delta",
    "proximal_common_cause_fault_signal_ratio_delta",
    "baseline_performance_improvement_claim_allowed",
    "post_performance_improvement_claim_allowed",
    "performance_improvement_claim_allowed",
    "result_change_summary_ko",
    "next_required_action",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare two panel-day-engine result delta scorecards. This is audit-only and "
            "does not evaluate truth-label accuracy."
        )
    )
    parser.add_argument("--baseline-scorecard-summary", type=Path, default=DEFAULT_SCORECARD_SUMMARY)
    parser.add_argument("--post-scorecard-summary", type=Path, default=DEFAULT_SCORECARD_SUMMARY)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def read_single_row(path: Path) -> pd.Series:
    if not path.exists():
        raise SystemExit(f"missing scorecard summary: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    if df.empty:
        raise SystemExit(f"empty scorecard summary: {path}")
    return df.iloc[0]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def numeric_or_none(value: object) -> float | None:
    converted = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(converted):
        return None
    return float(converted)


def format_delta(value: float | str) -> object:
    if isinstance(value, str):
        return value
    if value.is_integer():
        return int(value)
    return round(value, 6)


def compare_value(metric_name: str, baseline: object, post: object) -> dict[str, object]:
    baseline_text = normalize_text(baseline)
    post_text = normalize_text(post)
    baseline_num = numeric_or_none(baseline)
    post_num = numeric_or_none(post)
    if baseline_num is not None and post_num is not None:
        delta: object = format_delta(post_num - baseline_num)
        changed = int(abs(post_num - baseline_num) > 1e-12)
    else:
        delta = "" if baseline_text == post_text else "changed"
        changed = int(baseline_text != post_text)
    return {
        "metric_name": metric_name,
        "baseline_value": baseline_text,
        "post_value": post_text,
        "delta_value": delta,
        "changed_flag": changed,
        "claim_layer": claim_layer_for(metric_name),
        "interpretation_ko": interpretation_for(metric_name),
    }


def claim_layer_for(metric_name: str) -> str:
    if metric_name.startswith("core_"):
        return "core_result_delta"
    if metric_name in {"performance_improvement_claim_allowed"}:
        return "claim_boundary"
    if metric_name in {"prepatch_runbook_status"}:
        return "safety_gate"
    if metric_name.startswith("fixed_reference"):
        return "reference_context"
    return "candidate_context"


def interpretation_for(metric_name: str) -> str:
    mapping = {
        "core_total_diff_count": "core 결과 diff 수가 늘었는지 본다.",
        "raw_only_candidate_row_count": "raw-only 후보 row 수 변화다.",
        "published_current_row_count": "published current row 수 변화다.",
        "precursor_candidate_row_count": "순수 precursor report row 수 변화다.",
        "raw_only_fault_signal_row_count": "이미 고장 신호가 있는 analyst/support row 수 변화다.",
        "fault_panel_count": "고장 panel row 수 변화다.",
        "proximal_common_cause_fault_signal_count": "공통원인 근접 문맥 row 수 변화다.",
        "performance_improvement_claim_allowed": "성능 향상 claim 허용 여부다.",
        "result_change_claim_ko": "결과 변화 claim 문구 변화다.",
    }
    return mapping.get(metric_name, "baseline scorecard와 post scorecard의 값 차이다.")


def delta_for(detail: pd.DataFrame, metric_name: str) -> object:
    rows = detail.loc[detail["metric_name"].eq(metric_name)]
    if rows.empty:
        return 0
    return rows.iloc[0]["delta_value"]


def numeric_delta(detail: pd.DataFrame, metric_name: str) -> float:
    value = delta_for(detail, metric_name)
    converted = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0.0 if pd.isna(converted) else float(converted)


def build_compare(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    baseline = read_single_row(args.baseline_scorecard_summary)
    post = read_single_row(args.post_scorecard_summary)
    rows = []
    for metric_name in COMPARE_METRICS:
        rows.append(compare_value(metric_name, baseline.get(metric_name, ""), post.get(metric_name, "")))
    detail = pd.DataFrame(rows, columns=DETAIL_COLS)
    changed_count = int(detail["changed_flag"].sum())
    core_result_changed = int(
        numeric_delta(detail, "core_total_diff_count") != 0.0
        or numeric_delta(detail, "core_all_compared_sites_match") != 0.0
    )
    baseline_claim = normalize_text(baseline.get("performance_improvement_claim_allowed"))
    post_claim = normalize_text(post.get("performance_improvement_claim_allowed"))
    performance_claim = (
        "not_allowed_without_truth_label_eval"
        if "no_truth_label" in baseline_claim or "no_truth_label" in post_claim
        else "review_truth_label_eval_required"
    )
    if changed_count == 0:
        result_summary = "no_result_change_detected"
        overall_status = "pass"
        next_action = "use_compare_as_neutral_baseline"
    elif core_result_changed:
        result_summary = "core_result_change_detected_review_required"
        overall_status = "review"
        next_action = "review_core_delta_before_claiming_improvement"
    else:
        result_summary = "candidate_context_change_detected_review_required"
        overall_status = "review"
        next_action = "review_candidate_context_delta_before_claiming_improvement"
    summary_row = {
        "overall_status": overall_status,
        "metric_count": len(detail),
        "changed_metric_count": changed_count,
        "core_result_changed_flag": core_result_changed,
        "core_total_diff_count_delta": delta_for(detail, "core_total_diff_count"),
        "raw_only_candidate_row_count_delta": delta_for(detail, "raw_only_candidate_row_count"),
        "published_current_row_count_delta": delta_for(detail, "published_current_row_count"),
        "precursor_candidate_row_count_delta": delta_for(detail, "precursor_candidate_row_count"),
        "raw_only_fault_signal_row_count_delta": delta_for(detail, "raw_only_fault_signal_row_count"),
        "fault_panel_count_delta": delta_for(detail, "fault_panel_count"),
        "proximal_common_cause_fault_signal_count_delta": delta_for(
            detail, "proximal_common_cause_fault_signal_count"
        ),
        "proximal_common_cause_fault_signal_ratio_delta": delta_for(
            detail, "proximal_common_cause_fault_signal_ratio"
        ),
        "baseline_performance_improvement_claim_allowed": baseline_claim,
        "post_performance_improvement_claim_allowed": post_claim,
        "performance_improvement_claim_allowed": performance_claim,
        "result_change_summary_ko": result_summary,
        "next_required_action": next_action,
    }
    summary = pd.DataFrame([summary_row], columns=SUMMARY_COLS)
    note = render_note(summary.iloc[0], detail)
    return detail, summary, note


def render_note(summary: pd.Series, detail: pd.DataFrame) -> str:
    lines = [
        "# panel_day_engine_result_delta_scorecard_compare_note_v1",
        "",
        "## Reading",
        "- This compare artifact is audit-only.",
        "- It compares two result delta scorecard summaries.",
        "- It still does not claim accuracy/F1 improvement without truth-label evaluation.",
        "",
        "## Summary",
        f"- overall_status: `{summary['overall_status']}`",
        f"- changed_metric_count: `{summary['changed_metric_count']}`",
        f"- core_result_changed_flag: `{summary['core_result_changed_flag']}`",
        f"- raw_only_candidate_row_count_delta: `{summary['raw_only_candidate_row_count_delta']}`",
        f"- precursor_candidate_row_count_delta: `{summary['precursor_candidate_row_count_delta']}`",
        f"- fault_panel_count_delta: `{summary['fault_panel_count_delta']}`",
        f"- performance_improvement_claim_allowed: `{summary['performance_improvement_claim_allowed']}`",
        f"- result_change_summary_ko: `{summary['result_change_summary_ko']}`",
        "",
        "## Changed Metrics",
    ]
    changed = detail.loc[detail["changed_flag"].eq(1)]
    if changed.empty:
        lines.append("- none")
    else:
        for _, row in changed.iterrows():
            lines.append(
                f"- `{row['metric_name']}`: `{row['baseline_value']}` -> "
                f"`{row['post_value']}` (delta `{row['delta_value']}`)"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    detail, summary, note = build_compare(args)
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    (args.output_dir / NOTE_OUTPUT_NAME).write_text(note, encoding="utf-8")


if __name__ == "__main__":
    main()
