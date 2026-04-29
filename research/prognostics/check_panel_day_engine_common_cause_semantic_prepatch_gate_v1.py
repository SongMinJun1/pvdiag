#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_STRONG_BLOCKER_INPUT = Path(
    "/private/tmp/strong_common_cause_blocker_regression_packet_check/"
    "panel_day_engine_strong_common_cause_blocker_regression_packet_v1.csv"
)
DEFAULT_EXACT_SEARCH_INPUT = Path(
    "/private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv"
)
DEFAULT_STRUCTURAL_INPUT = Path(
    "/private/tmp/common_cause_structural_blocker_review_check/"
    "panel_day_engine_common_cause_structural_blocker_review_v1.csv"
)
DEFAULT_TRACE_INPUT = Path(
    "/private/tmp/common_cause_manual_trace_review_check/"
    "panel_day_engine_common_cause_manual_trace_review_v1.csv"
)

DETAIL_OUTPUT_NAME = "panel_day_engine_common_cause_semantic_prepatch_gate_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_common_cause_semantic_prepatch_gate_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_common_cause_semantic_prepatch_gate_note_v1.md"

MIN_STRONG_BLOCKER_ROWS = 50
MIN_CANDIDATE_RESERVOIR_ROWS = 49
MIN_STRUCTURAL_BLOCKER_ROWS = 49
MIN_RAW_DIRECT_COMMON_CAUSE_ROWS = 101
EXPECTED_MANUAL_TRACE_ROWS = 2

EXPECTED_STRUCTURAL_SUBTYPES = {
    "no_report_lane_entry",
    "precursor_carryover_without_current_closure",
    "rawonly_date_displaced_without_current_closure",
    "rawonly_near_signal_anchor",
    "official_current_date_displaced",
}
EXPECTED_TRACE_OUTCOMES = {
    "rawonly_near_anchor_trace_only",
    "post_current_common_cause_late_event_hold",
}

REQUIRED_COLS = {
    "strong_blocker": [
        "blocker_case_id",
        "site",
        "panel_id",
        "panel_root_id",
        "common_cause_blocker_type",
        "operator_promotion_allowed_flag",
        "engine_patch_candidate_flag",
        "threshold_patch_allowed_flag",
        "panel_local_promotion_blocked_flag",
        "regression_seed_flag",
        "review_note",
    ],
    "exact_search": [
        "search_case_id",
        "site",
        "panel_id",
        "exact_family_closure_flag",
        "candidate_reservoir_flag",
        "structural_blocker_flag",
        "blocker_regression_seed_flag",
        "raw_direct_common_cause_row_count",
        "official_current_same_day_overlap_flag",
        "operator_promotion_allowed_flag",
        "engine_patch_candidate_flag",
        "threshold_patch_allowed_flag",
        "allowed_use",
        "still_missing",
        "review_note",
    ],
    "structural": [
        "review_case_id",
        "source_search_case_id",
        "site",
        "panel_id",
        "structural_blocker_subtype",
        "manual_trace_review_flag",
        "structural_patch_target_review_flag",
        "operator_promotion_allowed_flag",
        "engine_patch_candidate_flag",
        "threshold_patch_allowed_flag",
        "official_current_same_day_overlap_flag",
        "required_next_evidence",
        "review_note",
    ],
    "trace": [
        "trace_case_id",
        "source_review_case_id",
        "source_search_case_id",
        "site",
        "panel_id",
        "trace_outcome_bucket",
        "trace_bridge_scope",
        "rawonly_report_bridge_candidate_flag",
        "official_current_bridge_candidate_flag",
        "semantic_patch_candidate_flag",
        "operator_promotion_allowed_flag",
        "engine_patch_candidate_flag",
        "threshold_patch_allowed_flag",
        "nearest_official_current_signed_gap_days",
        "nearest_rawonly_signal_signed_gap_days",
        "required_next_evidence",
        "review_note",
    ],
}

DETAIL_COLS = [
    "gate_id",
    "severity",
    "pass_flag",
    "status",
    "observed_value",
    "requirement",
    "remediation",
]
SUMMARY_COLS = [
    "overall_status",
    "required_gate_count",
    "failed_required_gate_count",
    "passed_required_gate_count",
    "warn_gate_count",
    "strong_blocker_rows",
    "exact_search_rows",
    "structural_rows",
    "trace_rows",
    "exact_family_closure_sum",
    "candidate_reservoir_sum",
    "structural_blocker_sum",
    "raw_direct_common_cause_row_sum",
    "manual_trace_review_sum",
    "rawonly_report_bridge_candidate_sum",
    "official_current_bridge_candidate_sum",
    "semantic_patch_candidate_sum",
    "operator_promotion_allowed_sum",
    "engine_patch_candidate_sum",
    "threshold_patch_allowed_sum",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Gate BR-071~BR-074 common-cause evidence before any semantic panel-engine "
            "common-cause loosening."
        )
    )
    parser.add_argument("--input-manifest", type=Path, default=None)
    parser.add_argument("--strong-blocker-input", type=Path, default=DEFAULT_STRONG_BLOCKER_INPUT)
    parser.add_argument("--exact-search-input", type=Path, default=DEFAULT_EXACT_SEARCH_INPUT)
    parser.add_argument("--structural-input", type=Path, default=DEFAULT_STRUCTURAL_INPUT)
    parser.add_argument("--trace-input", type=Path, default=DEFAULT_TRACE_INPUT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--allow-fail",
        action="store_true",
        help="Write gate outputs but return success even when required gates fail.",
    )
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
                f"common-cause prepatch input manifest is missing `{key}`; "
                f"pass {flag} explicitly or add inputs.{key}"
            )
        return resolve_path(repo_root, manifest_value), "input_manifest"
    return resolve_path(repo_root, arg_value), "legacy_default"


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


def read_table(path: Path, required_cols: list[str]) -> tuple[pd.DataFrame, list[str], bool]:
    if not path.exists():
        return pd.DataFrame(columns=required_cols), required_cols[:], False
    df = pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
    missing = [col for col in required_cols if col not in df.columns]
    out = df.copy()
    for col in missing:
        out[col] = ""
    return out, missing, True


def flag_sum(df: pd.DataFrame, col: str) -> int:
    if df.empty or col not in df.columns:
        return 0
    return int(df[col].map(int_value).sum())


def int_sum(df: pd.DataFrame, col: str) -> int:
    if df.empty or col not in df.columns:
        return 0
    return int(df[col].map(int_value).sum())


def text_values(df: pd.DataFrame, col: str) -> set[str]:
    if df.empty or col not in df.columns:
        return set()
    return {normalize_text(value) for value in df[col] if normalize_text(value)}


def gate_row(
    gate_id: str,
    passed: bool,
    observed_value: object,
    requirement: str,
    remediation: str,
    severity: str = "required",
) -> dict[str, object]:
    if passed:
        status = "pass"
        pass_flag = 1
    elif severity == "required":
        status = "fail"
        pass_flag = 0
    else:
        status = "warn"
        pass_flag = 1
    return {
        "gate_id": gate_id,
        "severity": severity,
        "pass_flag": pass_flag,
        "status": status,
        "observed_value": normalize_text(observed_value),
        "requirement": requirement,
        "remediation": remediation,
    }


def empty_text_count(inputs: dict[str, pd.DataFrame], checks: dict[str, list[str]]) -> int:
    count = 0
    for label, cols in checks.items():
        df = inputs[label]
        for col in cols:
            if col not in df.columns:
                count += len(df)
            else:
                count += int(df[col].map(normalize_text).eq("").sum())
    return count


def build_detail(
    tables: dict[str, pd.DataFrame],
    missing: dict[str, list[str]],
    exists: dict[str, bool],
) -> pd.DataFrame:
    strong = tables["strong_blocker"]
    exact = tables["exact_search"]
    structural = tables["structural"]
    trace = tables["trace"]

    strong_rows = len(strong)
    exact_rows = len(exact)
    structural_rows = len(structural)
    trace_rows = len(trace)
    all_missing = {label: cols for label, cols in missing.items() if cols}

    strong_promotion_sum = flag_sum(strong, "operator_promotion_allowed_flag")
    strong_engine_sum = flag_sum(strong, "engine_patch_candidate_flag")
    strong_threshold_sum = flag_sum(strong, "threshold_patch_allowed_flag")
    strong_blocked_sum = flag_sum(strong, "panel_local_promotion_blocked_flag")
    strong_regression_sum = flag_sum(strong, "regression_seed_flag")

    exact_closure_sum = flag_sum(exact, "exact_family_closure_flag")
    exact_candidate_sum = flag_sum(exact, "candidate_reservoir_flag")
    exact_structural_sum = flag_sum(exact, "structural_blocker_flag")
    exact_regression_sum = flag_sum(exact, "blocker_regression_seed_flag")
    exact_raw_sum = int_sum(exact, "raw_direct_common_cause_row_count")
    exact_same_day_sum = flag_sum(exact, "official_current_same_day_overlap_flag")

    structural_manual_sum = flag_sum(structural, "manual_trace_review_flag")
    structural_patch_target_sum = flag_sum(structural, "structural_patch_target_review_flag")
    structural_same_day_sum = flag_sum(structural, "official_current_same_day_overlap_flag")

    trace_rawonly_bridge_sum = flag_sum(trace, "rawonly_report_bridge_candidate_flag")
    trace_current_bridge_sum = flag_sum(trace, "official_current_bridge_candidate_flag")
    trace_semantic_sum = flag_sum(trace, "semantic_patch_candidate_flag")
    trace_outcomes = text_values(trace, "trace_outcome_bucket")

    total_promotion_sum = sum(flag_sum(df, "operator_promotion_allowed_flag") for df in tables.values())
    total_engine_sum = sum(flag_sum(df, "engine_patch_candidate_flag") for df in tables.values())
    total_threshold_sum = sum(flag_sum(df, "threshold_patch_allowed_flag") for df in tables.values())

    structural_links = set(structural["source_search_case_id"].map(normalize_text)) if "source_search_case_id" in structural else set()
    exact_ids = set(exact["search_case_id"].map(normalize_text)) if "search_case_id" in exact else set()
    trace_review_links = set(trace["source_review_case_id"].map(normalize_text)) if "source_review_case_id" in trace else set()
    structural_ids = set(structural["review_case_id"].map(normalize_text)) if "review_case_id" in structural else set()
    missing_structural_links = sorted(value for value in structural_links - exact_ids if value)
    missing_trace_links = sorted(value for value in trace_review_links - structural_ids if value)

    rows: list[dict[str, object]] = []
    rows.append(
        gate_row(
            "G01_inputs_exist_and_non_empty",
            all(exists.values()) and all(len(df) > 0 for df in tables.values()),
            ", ".join(f"{label}=exists:{exists[label]},rows:{len(tables[label])}" for label in tables),
            "BR-071, BR-072, BR-073, and BR-074 inputs must exist and be non-empty.",
            "Regenerate the missing common-cause evidence packet before semantic patch review.",
        )
    )
    rows.append(
        gate_row(
            "G02_required_columns_present",
            not all_missing,
            str(all_missing),
            "All input packets must contain the columns required by this gate.",
            "Regenerate stale packets with the current builders.",
        )
    )
    rows.append(
        gate_row(
            "G03_strong_common_cause_blockers_preserved",
            strong_rows >= MIN_STRONG_BLOCKER_ROWS
            and strong_blocked_sum == strong_rows
            and strong_regression_sum == strong_rows,
            f"rows={strong_rows}, blocked={strong_blocked_sum}, regression={strong_regression_sum}",
            "BR-071 strong common-cause blockers must remain blocker/regression rows.",
            "Do not proceed if common-cause blocker rows were dropped or reclassified.",
        )
    )
    rows.append(
        gate_row(
            "G04_strong_blockers_not_promoting",
            strong_promotion_sum == 0 and strong_engine_sum == 0 and strong_threshold_sum == 0,
            f"promotion={strong_promotion_sum}, engine={strong_engine_sum}, threshold={strong_threshold_sum}",
            "BR-071 blockers must not authorize promotion, engine patching, or threshold patching.",
            "Revert any interpretation that promotes strong common-cause synchrony as panel-local evidence.",
        )
    )
    rows.append(
        gate_row(
            "G05_exact_search_no_current_closure",
            exact_closure_sum == 0 and exact_same_day_sum == 0,
            f"exact_closure={exact_closure_sum}, same_day_current_overlap={exact_same_day_sum}",
            "BR-072 must still have zero exact family closure and zero official/current same-day overlap.",
            "Attach true same-day current closure evidence before loosening common-cause semantics.",
        )
    )
    rows.append(
        gate_row(
            "G06_exact_search_reservoir_preserved",
            exact_candidate_sum >= MIN_CANDIDATE_RESERVOIR_ROWS
            and exact_structural_sum >= MIN_STRUCTURAL_BLOCKER_ROWS
            and exact_raw_sum >= MIN_RAW_DIRECT_COMMON_CAUSE_ROWS
            and exact_regression_sum >= MIN_STRONG_BLOCKER_ROWS,
            (
                f"candidate={exact_candidate_sum}, structural={exact_structural_sum}, "
                f"raw_direct_rows={exact_raw_sum}, regression={exact_regression_sum}"
            ),
            "BR-072 reservoir/blocker counts must not shrink before semantic discussion.",
            "Rerun BR-072 and inspect missing rows before reviewing any rule change.",
        )
    )
    rows.append(
        gate_row(
            "G07_structural_review_matches_reservoir",
            structural_rows == exact_structural_sum
            and structural_manual_sum == EXPECTED_MANUAL_TRACE_ROWS
            and structural_patch_target_sum == EXPECTED_MANUAL_TRACE_ROWS
            and structural_same_day_sum == 0,
            (
                f"structural_rows={structural_rows}, exact_structural={exact_structural_sum}, "
                f"manual_trace={structural_manual_sum}, patch_target={structural_patch_target_sum}, "
                f"same_day={structural_same_day_sum}"
            ),
            "BR-073 must account for BR-072 structural blockers and keep only two trace targets.",
            "Rerun BR-073 before interpreting common-cause blocker rows.",
        )
    )
    rows.append(
        gate_row(
            "G08_structural_subtype_coverage_present",
            EXPECTED_STRUCTURAL_SUBTYPES.issubset(text_values(structural, "structural_blocker_subtype")),
            "|".join(sorted(text_values(structural, "structural_blocker_subtype"))),
            "BR-073 must preserve all structural blocker subtype buckets.",
            "Do not collapse subtype-specific blockers into a single promotion rule.",
        )
    )
    rows.append(
        gate_row(
            "G09_manual_trace_non_closure",
            trace_rows == structural_manual_sum
            and trace_current_bridge_sum == 0
            and trace_semantic_sum == 0
            and total_promotion_sum == 0
            and total_engine_sum == 0
            and total_threshold_sum == 0,
            (
                f"trace_rows={trace_rows}, structural_manual={structural_manual_sum}, "
                f"current_bridge={trace_current_bridge_sum}, semantic={trace_semantic_sum}, "
                f"promotion={total_promotion_sum}, engine={total_engine_sum}, threshold={total_threshold_sum}"
            ),
            "BR-074 trace rows must remain non-closure and non-promoting.",
            "Do not use raw-only traces or post-current mismatch rows as official/current closure.",
        )
    )
    rows.append(
        gate_row(
            "G10_manual_trace_expected_outcomes",
            trace_outcomes == EXPECTED_TRACE_OUTCOMES and trace_rawonly_bridge_sum == 1,
            f"outcomes={sorted(trace_outcomes)}, rawonly_bridge={trace_rawonly_bridge_sum}",
            "BR-074 must preserve one raw-only trace-only row and one post-current mismatch row.",
            "Rerun BR-074 and inspect any changed trace bucket before semantic review.",
        )
    )
    rows.append(
        gate_row(
            "G11_cross_packet_linkage_integrity",
            not missing_structural_links and not missing_trace_links,
            f"structural_missing={missing_structural_links}, trace_missing={missing_trace_links}",
            "BR-073 rows must link to BR-072 rows, and BR-074 rows must link to BR-073 rows.",
            "Repair or regenerate stale packet inputs before using this gate.",
        )
    )
    text_count = empty_text_count(
        tables,
        {
            "strong_blocker": ["review_note"],
            "exact_search": ["allowed_use", "still_missing", "review_note"],
            "structural": ["required_next_evidence", "review_note"],
            "trace": ["required_next_evidence", "review_note"],
        },
    )
    rows.append(
        gate_row(
            "G12_interpretation_text_present",
            text_count == 0,
            text_count,
            "All common-cause hold/regression rows must carry interpretation text.",
            "Do not use packet rows as safety gates without explicit interpretation text.",
        )
    )
    rows.append(
        gate_row(
            "W01_rawonly_trace_is_context_only",
            trace_rawonly_bridge_sum == 0,
            trace_rawonly_bridge_sum,
            "Raw-only bridge candidates are context-only and must not become official/current closure.",
            "Keep raw-only near-anchor evidence outside operator-facing current promotion.",
            severity="warn",
        )
    )
    return pd.DataFrame(rows, columns=DETAIL_COLS)


def build_summary(detail: pd.DataFrame, tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    required = detail.loc[detail["severity"] == "required"].copy()
    failed_required = required.loc[required["status"] == "fail"]
    warn_rows = detail.loc[detail["status"] == "warn"]
    row = {
        "overall_status": "pass" if failed_required.empty else "fail",
        "required_gate_count": len(required),
        "failed_required_gate_count": len(failed_required),
        "passed_required_gate_count": int(required["pass_flag"].sum()) if not required.empty else 0,
        "warn_gate_count": len(warn_rows),
        "strong_blocker_rows": len(tables["strong_blocker"]),
        "exact_search_rows": len(tables["exact_search"]),
        "structural_rows": len(tables["structural"]),
        "trace_rows": len(tables["trace"]),
        "exact_family_closure_sum": flag_sum(tables["exact_search"], "exact_family_closure_flag"),
        "candidate_reservoir_sum": flag_sum(tables["exact_search"], "candidate_reservoir_flag"),
        "structural_blocker_sum": flag_sum(tables["exact_search"], "structural_blocker_flag"),
        "raw_direct_common_cause_row_sum": int_sum(tables["exact_search"], "raw_direct_common_cause_row_count"),
        "manual_trace_review_sum": flag_sum(tables["structural"], "manual_trace_review_flag"),
        "rawonly_report_bridge_candidate_sum": flag_sum(tables["trace"], "rawonly_report_bridge_candidate_flag"),
        "official_current_bridge_candidate_sum": flag_sum(tables["trace"], "official_current_bridge_candidate_flag"),
        "semantic_patch_candidate_sum": flag_sum(tables["trace"], "semantic_patch_candidate_flag"),
        "operator_promotion_allowed_sum": sum(
            flag_sum(df, "operator_promotion_allowed_flag") for df in tables.values()
        ),
        "engine_patch_candidate_sum": sum(flag_sum(df, "engine_patch_candidate_flag") for df in tables.values()),
        "threshold_patch_allowed_sum": sum(flag_sum(df, "threshold_patch_allowed_flag") for df in tables.values()),
    }
    return pd.DataFrame([row], columns=SUMMARY_COLS)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    def cell(value: object) -> str:
        return normalize_text(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")

    header = "| " + " | ".join(df.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows = [
        "| " + " | ".join(cell(row[col]) for col in df.columns)
        + " |"
        for row in df.to_dict(orient="records")
    ]
    return "\n".join([header, separator] + rows)


def write_note(
    output_dir: Path,
    detail: pd.DataFrame,
    summary: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> None:
    source_map = input_resolution_sources or {}
    lines = [
        "# panel_day_engine_common_cause_semantic_prepatch_gate_note_v1",
        "",
        "## Purpose",
        "- Gate BR-071 through BR-074 common-cause evidence before any semantic algorithm patch.",
        "- Prevent common-cause synchrony, raw-only near-anchor traces, or post-current mismatches from becoming official/current closure by accident.",
        "",
        "## Inputs",
        f"- evidence input manifest: `{input_manifest_path if input_manifest_path is not None else 'not provided'}`",
        "",
        "## Input Resolution Sources",
        f"- `strong_blocker_input`: `{source_map.get('strong_blocker_input', 'legacy_default')}`",
        f"- `exact_search_input`: `{source_map.get('exact_search_input', 'legacy_default')}`",
        f"- `structural_input`: `{source_map.get('structural_input', 'legacy_default')}`",
        f"- `trace_input`: `{source_map.get('trace_input', 'legacy_default')}`",
        "",
        "## Summary",
        dataframe_to_markdown(summary),
        "",
        "## Gate Detail",
        dataframe_to_markdown(detail),
        "",
        "## Interpretation",
        "- Passing this gate does not approve a common-cause semantic patch.",
        "- Passing means the known hold/regression evidence is preserved and no forbidden promotion/closure drift is present.",
        "- Any future semantic patch must still provide independent same-day current closure or explicit report-date correction evidence.",
    ]
    (output_dir / NOTE_OUTPUT_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    input_manifest_path, input_manifest = load_input_manifest(repo_root, args.input_manifest)
    argv = sys.argv[1:]
    explicit_flags = {
        flag
        for flag in [
            "--strong-blocker-input",
            "--exact-search-input",
            "--structural-input",
            "--trace-input",
        ]
        if cli_flag_provided(flag, argv)
    }
    strong_blocker_input, strong_blocker_input_source = resolve_manifest_input(
        repo_root,
        "strong_blocker_input",
        "--strong-blocker-input",
        args.strong_blocker_input,
        input_manifest,
        explicit_flags,
    )
    exact_search_input, exact_search_input_source = resolve_manifest_input(
        repo_root,
        "exact_search_input",
        "--exact-search-input",
        args.exact_search_input,
        input_manifest,
        explicit_flags,
    )
    structural_input, structural_input_source = resolve_manifest_input(
        repo_root,
        "structural_input",
        "--structural-input",
        args.structural_input,
        input_manifest,
        explicit_flags,
    )
    trace_input, trace_input_source = resolve_manifest_input(
        repo_root,
        "trace_input",
        "--trace-input",
        args.trace_input,
        input_manifest,
        explicit_flags,
    )
    input_resolution_sources = {
        "strong_blocker_input": strong_blocker_input_source,
        "exact_search_input": exact_search_input_source,
        "structural_input": structural_input_source,
        "trace_input": trace_input_source,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    input_paths = {
        "strong_blocker": strong_blocker_input,
        "exact_search": exact_search_input,
        "structural": structural_input,
        "trace": trace_input,
    }
    tables: dict[str, pd.DataFrame] = {}
    missing: dict[str, list[str]] = {}
    exists: dict[str, bool] = {}
    for label, path in input_paths.items():
        table, missing_cols, input_exists = read_table(path, REQUIRED_COLS[label])
        tables[label] = table
        missing[label] = missing_cols
        exists[label] = input_exists
    detail = build_detail(tables, missing, exists)
    summary = build_summary(detail, tables)
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(args.output_dir, detail, summary, input_manifest_path, input_resolution_sources)
    if summary.iloc[0]["overall_status"] != "pass" and not args.allow_fail:
        raise SystemExit("common-cause semantic prepatch gate failed")


if __name__ == "__main__":
    main()
