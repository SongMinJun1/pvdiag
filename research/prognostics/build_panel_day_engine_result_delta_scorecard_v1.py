#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_RUNTIME_ROOT = Path("/private/tmp/pvdiag_postmerge_j_conalog_smoke_algorithm_prepatch_runbook")
DEFAULT_PREPATCH_SUMMARY = Path(
    "/private/tmp/panel_engine_algorithm_prepatch_runbook_check/"
    "panel_day_engine_algorithm_prepatch_runbook_summary_v1.csv"
)
DETAIL_OUTPUT_NAME = "panel_day_engine_result_delta_scorecard_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_result_delta_scorecard_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_result_delta_scorecard_note_v1.md"

DETAIL_COLS = [
    "metric_group",
    "metric_name",
    "current_value",
    "reference_value",
    "delta_value",
    "claim_layer",
    "claim_allowed",
    "interpretation_ko",
]
SUMMARY_COLS = [
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
    "next_required_action",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an audit-only result delta scorecard for panel-day-engine runtime outputs. "
            "The scorecard distinguishes actual result deltas from safety/evidence improvements."
        )
    )
    parser.add_argument("--input-manifest", type=Path, default=None)
    parser.add_argument("--runtime-root", type=Path, default=DEFAULT_RUNTIME_ROOT)
    parser.add_argument("--prepatch-runbook-summary", type=Path, default=DEFAULT_PREPATCH_SUMMARY)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def load_input_manifest(repo_root: Path, value: str | Path | None) -> tuple[Path | None, dict[str, Any]]:
    if value is None or str(value).strip() == "":
        return None, {}
    path = resolve_path(repo_root, value)
    if not path.exists():
        raise FileNotFoundError(f"missing input manifest: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"input manifest must be a JSON object: {path}")
    return path, payload


def manifest_path_value(manifest: dict[str, Any], key: str) -> str:
    raw = manifest.get(key)
    if raw is None and isinstance(manifest.get("inputs"), dict):
        raw = manifest["inputs"].get(key)
    if isinstance(raw, dict):
        for field in ["path", "artifact_path", "static_path"]:
            if raw.get(field):
                return str(raw[field])
        return ""
    return "" if raw is None else str(raw)


def cli_flag_provided(flag: str, argv: list[str]) -> bool:
    return any(item == flag or item.startswith(f"{flag}=") for item in argv)


def resolve_manifest_input(
    repo_root: Path,
    key: str,
    flag: str,
    arg_value: str | Path,
    manifest: dict[str, Any],
    explicit_flags: set[str],
) -> tuple[Path, str]:
    if flag in explicit_flags:
        return resolve_path(repo_root, arg_value), "explicit_cli"
    if manifest:
        manifest_value = manifest_path_value(manifest, key)
        if not manifest_value:
            raise KeyError(
                f"prepatch scorecard input manifest is missing `{key}`; "
                f"pass {flag} explicitly or add inputs.{key}"
            )
        return resolve_path(repo_root, manifest_value), "input_manifest"
    return resolve_path(repo_root, arg_value), "legacy_default"


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing required csv: {path}")
    return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        raise SystemExit(f"missing required json: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def count_eq(df: pd.DataFrame, column: str, value: str) -> int:
    if column not in df.columns:
        return 0
    return int(df[column].fillna("").astype(str).eq(value).sum())


def value_counts(df: pd.DataFrame, column: str) -> dict[str, int]:
    if column not in df.columns:
        return {}
    counts = df[column].fillna("").astype(str).value_counts()
    return {str(k): int(v) for k, v in counts.items()}


def metric(
    metric_group: str,
    metric_name: str,
    current_value: object,
    reference_value: object = "",
    delta_value: object = "",
    claim_layer: str = "audit_only",
    claim_allowed: str = "yes",
    interpretation_ko: str = "",
) -> dict[str, object]:
    return {
        "metric_group": metric_group,
        "metric_name": metric_name,
        "current_value": current_value,
        "reference_value": reference_value,
        "delta_value": delta_value,
        "claim_layer": claim_layer,
        "claim_allowed": claim_allowed,
        "interpretation_ko": interpretation_ko,
    }


def safe_bool(value: object) -> bool:
    return bool(value) if value is not None else False


def summarize_shadow_compare(shadow: dict[str, object]) -> tuple[list[dict[str, object]], dict[str, object]]:
    sites = shadow.get("sites", {})
    site_values = sites.values() if isinstance(sites, dict) else []
    total_diff_count = 0
    total_expected_rows = 0
    total_actual_rows = 0
    for site in site_values:
        if not isinstance(site, dict):
            continue
        diffs = site.get("diffs", [])
        if isinstance(diffs, list):
            total_diff_count += len(diffs)
        expected = site.get("expected", {})
        actual = site.get("actual", {})
        if isinstance(expected, dict):
            total_expected_rows += int(expected.get("row_count", 0) or 0)
        if isinstance(actual, dict):
            total_actual_rows += int(actual.get("row_count", 0) or 0)
    all_match = safe_bool(shadow.get("all_compared_sites_match"))
    metrics = [
        metric(
            "core_shadow_compare",
            "core_all_compared_sites_match",
            str(all_match),
            "True",
            int(all_match) - 1,
            "result_delta",
            "yes",
            "baseline core digest가 유지됐는지 보는 결과 변화 지표다.",
        ),
        metric(
            "core_shadow_compare",
            "core_row_count",
            total_actual_rows,
            total_expected_rows,
            total_actual_rows - total_expected_rows,
            "result_delta",
            "yes",
            "core row 수 변화량이다.",
        ),
        metric(
            "core_shadow_compare",
            "core_diff_count",
            total_diff_count,
            0,
            total_diff_count,
            "result_delta",
            "yes",
            "shadow compare가 발견한 core diff 수다.",
        ),
    ]
    summary = {
        "core_compared_site_count": int(shadow.get("compared_site_count", 0) or 0),
        "core_matched_site_count": int(shadow.get("matched_site_count", 0) or 0),
        "core_all_compared_sites_match": int(all_match),
        "core_total_diff_count": total_diff_count,
    }
    return metrics, summary


def build_scorecard(
    args: argparse.Namespace,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    runtime_root = args.runtime_root
    result_root = runtime_root / "result"
    share_root = runtime_root / "raw_only_chain_workspace" / "_share"
    shadow = read_json(runtime_root / "shadow_compare_v1.json")
    raw_summary = read_json(result_root / "raw_only_chain_summary_v1.json")
    final_df = read_csv(share_root / "panel_day_engine_runtime_final_verdict_v1.csv")
    heur_df = read_csv(share_root / "panel_day_engine_runtime_cause_candidate_heuristics_v1.csv")
    precursor_df = read_csv(result_root / "fault_panel_result_precursor_report_v1.csv")
    fault_signal_df = read_csv(result_root / "fault_panel_result_raw_only_fault_signal_report_v1.csv")

    detail_rows, shadow_summary = summarize_shadow_compare(shadow)
    fixed_compare = raw_summary.get("fixed_fault_reference_compare", {})
    if not isinstance(fixed_compare, dict):
        fixed_compare = {}
    publish_meta = raw_summary.get("publish_meta", {})
    if not isinstance(publish_meta, dict):
        publish_meta = {}

    fault_panel_count = count_eq(final_df, "패널고장여부_ko", "고장")
    unresolved_panel_count = count_eq(final_df, "패널고장여부_ko", "미확정")
    final_verdict_counts = value_counts(final_df, "대표판정_ko")
    morphology_counts = value_counts(final_df, "최종고장양상_ko")
    top1_counts = value_counts(heur_df, "원인후보_top1_ko")
    confidence_counts = value_counts(heur_df, "원인후보_신뢰도_ko")
    proximal_common_cause_count = 0
    if "근접 공통원인" in fault_signal_df.columns:
        proximal_common_cause_count = int(
            fault_signal_df["근접 공통원인"].fillna("").astype(str).str.strip().ne("").sum()
        )
    fault_signal_rows = len(fault_signal_df)
    proximal_ratio = (
        round(proximal_common_cause_count / fault_signal_rows, 6)
        if fault_signal_rows
        else 0.0
    )
    raw_candidate_rows = int(publish_meta.get("candidate_row_count", len(heur_df)) or 0)
    published_current_rows = int(publish_meta.get("published_current_row_count", fault_panel_count) or 0)
    reference_rows = int(fixed_compare.get("reference_row_count", 0) or 0)
    matched_reference_keys = int(fixed_compare.get("matched_row_key_count", 0) or 0)
    overlap_match = fixed_compare.get("overlap_decision_columns_match")
    overlap_match_bool = safe_bool(overlap_match)
    overlap_diff_columns = fixed_compare.get("overlap_diff_columns", [])
    overlap_diff_count = len(overlap_diff_columns) if isinstance(overlap_diff_columns, list) else 0

    detail_rows.extend(
        [
            metric(
                "raw_only_current",
                "fault_panel_count",
                fault_panel_count,
                "",
                "",
                "candidate_result",
                "yes",
                "raw-only final verdict에서 고장으로 분류된 panel row 수다.",
            ),
            metric(
                "raw_only_current",
                "unresolved_panel_count",
                unresolved_panel_count,
                "",
                "",
                "candidate_result",
                "yes",
                "raw-only final verdict에서 미확정으로 남은 panel row 수다.",
            ),
            metric(
                "raw_only_current",
                "published_current_row_count",
                published_current_rows,
                "",
                "",
                "candidate_result",
                "yes",
                "strict current subset으로 공개된 raw-only current row 수다.",
            ),
            metric(
                "report_split",
                "precursor_candidate_row_count",
                len(precursor_df),
                "",
                "",
                "candidate_result",
                "yes",
                "아직 고장 신호가 없는 precursor report row 수다.",
            ),
            metric(
                "report_split",
                "raw_only_fault_signal_row_count",
                fault_signal_rows,
                "",
                "",
                "candidate_result",
                "yes",
                "이미 고장 신호가 있는 raw-only analyst/support row 수다.",
            ),
            metric(
                "common_cause_context",
                "proximal_common_cause_fault_signal_count",
                proximal_common_cause_count,
                fault_signal_rows,
                proximal_ratio,
                "evidence_context",
                "yes",
                "fault signal row 중 strict_trigger 근처 공통원인 문맥이 있는 row 수와 비율이다.",
            ),
            metric(
                "fixed_reference_overlap",
                "fixed_reference_row_count",
                reference_rows,
                "",
                "",
                "reference_context",
                "yes",
                "릴리즈 번들의 fixed fault reference row 수다.",
            ),
            metric(
                "fixed_reference_overlap",
                "fixed_reference_matched_row_key_count",
                matched_reference_keys,
                reference_rows,
                matched_reference_keys - reference_rows,
                "reference_context",
                "yes",
                "raw-only current와 fixed reference 사이의 key overlap 수다.",
            ),
            metric(
                "fixed_reference_overlap",
                "fixed_reference_overlap_decision_columns_match",
                str(overlap_match_bool),
                "True",
                int(overlap_match_bool) - 1,
                "reference_context",
                "yes",
                "overlap row에서 decision column이 완전히 같은지 본다.",
            ),
            metric(
                "fixed_reference_overlap",
                "fixed_reference_overlap_diff_column_count",
                overlap_diff_count,
                0,
                overlap_diff_count,
                "reference_context",
                "yes",
                "overlap row에서 차이가 나는 decision column 수다.",
            ),
        ]
    )

    for name, count in final_verdict_counts.items():
        detail_rows.append(
            metric("raw_only_current_distribution", f"대표판정_ko::{name or '<blank>'}", count)
        )
    for name, count in morphology_counts.items():
        detail_rows.append(
            metric("raw_only_morphology_distribution", f"최종고장양상_ko::{name or '<blank>'}", count)
        )
    for name, count in top1_counts.items():
        detail_rows.append(
            metric("cause_candidate_distribution", f"원인후보_top1_ko::{name or '<blank>'}", count)
        )
    for name, count in confidence_counts.items():
        detail_rows.append(
            metric("cause_candidate_distribution", f"원인후보_신뢰도_ko::{name or '<blank>'}", count)
        )

    prepatch_status = "not_provided"
    if args.prepatch_runbook_summary and args.prepatch_runbook_summary.exists():
        prepatch = read_csv(args.prepatch_runbook_summary)
        if not prepatch.empty:
            prepatch_status = normalize_text(prepatch.iloc[0].get("overall_status")) or "unknown"
    detail_rows.append(
        metric(
            "prepatch_safety",
            "prepatch_runbook_status",
            prepatch_status,
            "pass",
            "",
            "safety_gate",
            "yes",
            "직접 엔진 패치 전 combined runbook 통과 여부다.",
        )
    )

    core_pass = bool(shadow_summary["core_all_compared_sites_match"]) and shadow_summary["core_total_diff_count"] == 0
    prepatch_pass = prepatch_status in {"pass", "not_provided"}
    overall_status = "pass" if core_pass and prepatch_pass else "review"
    performance_claim_allowed = "no_truth_label_not_claimed"
    result_change_claim = (
        "core_result_delta_0"
        if core_pass
        else "core_result_delta_detected_review_required"
    )
    summary_row = {
        "overall_status": overall_status,
        **shadow_summary,
        "raw_only_candidate_row_count": raw_candidate_rows,
        "published_current_row_count": published_current_rows,
        "precursor_candidate_row_count": len(precursor_df),
        "raw_only_fault_signal_row_count": fault_signal_rows,
        "fault_panel_count": fault_panel_count,
        "unresolved_panel_count": unresolved_panel_count,
        "proximal_common_cause_fault_signal_count": proximal_common_cause_count,
        "proximal_common_cause_fault_signal_ratio": proximal_ratio,
        "fixed_reference_row_count": reference_rows,
        "fixed_reference_matched_row_key_count": matched_reference_keys,
        "fixed_reference_overlap_decision_columns_match": int(overlap_match_bool),
        "prepatch_runbook_status": prepatch_status,
        "performance_improvement_claim_allowed": performance_claim_allowed,
        "result_change_claim_ko": result_change_claim,
        "next_required_action": "use_scorecard_as_future_patch_delta_baseline",
    }
    detail = pd.DataFrame(detail_rows, columns=DETAIL_COLS)
    summary = pd.DataFrame([summary_row], columns=SUMMARY_COLS)
    note = render_note(summary.iloc[0], detail, input_manifest_path, input_resolution_sources)
    return detail, summary, note


def render_note(
    summary: pd.Series,
    detail: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> str:
    source_map = input_resolution_sources or {}
    lines = [
        "# panel_day_engine_result_delta_scorecard_note_v1",
        "",
        "## Reading",
        "- This scorecard is audit-only.",
        "- It does not claim accuracy/F1 improvement because no new truth-label evaluation was run.",
        "- It records whether runtime core results changed, and what candidate/result context exists now.",
        "",
        "## Inputs",
        f"- evidence input manifest: `{input_manifest_path if input_manifest_path is not None else 'not provided'}`",
        "",
        "## Input Resolution Sources",
        f"- `runtime_root`: `{source_map.get('runtime_root', 'legacy_default')}`",
        f"- `prepatch_runbook_summary`: `{source_map.get('prepatch_runbook_summary', 'legacy_default')}`",
        "",
        "## Summary",
        f"- overall_status: `{summary['overall_status']}`",
        f"- core_all_compared_sites_match: `{summary['core_all_compared_sites_match']}`",
        f"- core_total_diff_count: `{summary['core_total_diff_count']}`",
        f"- raw_only_candidate_row_count: `{summary['raw_only_candidate_row_count']}`",
        f"- published_current_row_count: `{summary['published_current_row_count']}`",
        f"- precursor_candidate_row_count: `{summary['precursor_candidate_row_count']}`",
        f"- raw_only_fault_signal_row_count: `{summary['raw_only_fault_signal_row_count']}`",
        f"- proximal_common_cause_fault_signal_count: `{summary['proximal_common_cause_fault_signal_count']}`",
        f"- fixed_reference_matched_row_key_count: `{summary['fixed_reference_matched_row_key_count']}`",
        f"- prepatch_runbook_status: `{summary['prepatch_runbook_status']}`",
        "",
        "## Claim Boundary",
        "- Allowed: result stability and candidate context can be reported.",
        "- Not allowed: percentage performance improvement or accuracy/F1 improvement.",
        "- Future engine patches should compare against this scorecard before claiming result improvement.",
    ]
    top_rows = detail.loc[detail["metric_group"].eq("cause_candidate_distribution")].head(10)
    if not top_rows.empty:
        lines.extend(["", "## Top Cause Candidate Distribution"])
        for _, row in top_rows.iterrows():
            lines.append(f"- `{row['metric_name']}`: `{row['current_value']}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    input_manifest_path, input_manifest = load_input_manifest(repo_root, args.input_manifest)
    argv = sys.argv[1:]
    explicit_flags = {
        flag
        for flag in ["--runtime-root", "--prepatch-runbook-summary"]
        if cli_flag_provided(flag, argv)
    }
    runtime_root, runtime_root_source = resolve_manifest_input(
        repo_root,
        "runtime_root",
        "--runtime-root",
        args.runtime_root,
        input_manifest,
        explicit_flags,
    )
    prepatch_runbook_summary, prepatch_runbook_summary_source = resolve_manifest_input(
        repo_root,
        "prepatch_runbook_summary",
        "--prepatch-runbook-summary",
        args.prepatch_runbook_summary,
        input_manifest,
        explicit_flags,
    )
    args.runtime_root = runtime_root
    args.prepatch_runbook_summary = prepatch_runbook_summary
    input_resolution_sources = {
        "runtime_root": runtime_root_source,
        "prepatch_runbook_summary": prepatch_runbook_summary_source,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    detail, summary, note = build_scorecard(args, input_manifest_path, input_resolution_sources)
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    (args.output_dir / NOTE_OUTPUT_NAME).write_text(note, encoding="utf-8")
    if summary.iloc[0]["overall_status"] != "pass":
        raise SystemExit("panel-day-engine result delta scorecard requires review")


if __name__ == "__main__":
    main()
