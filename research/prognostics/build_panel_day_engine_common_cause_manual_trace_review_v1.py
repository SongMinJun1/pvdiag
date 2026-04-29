#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_BLOCKER_INPUT = Path(
    "/private/tmp/common_cause_structural_blocker_review_check/"
    "panel_day_engine_common_cause_structural_blocker_review_v1.csv"
)
DEFAULT_CURRENT_INPUT = Path("/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_current_v1.csv")
DEFAULT_PRECURSOR_INPUT = Path(
    "/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_precursor_report_v1.csv"
)
DEFAULT_RAWONLY_SIGNAL_INPUT = Path(
    "/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_raw_only_fault_signal_report_v1.csv"
)
DEFAULT_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"

DETAIL_OUTPUT_NAME = "panel_day_engine_common_cause_manual_trace_review_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_common_cause_manual_trace_review_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_common_cause_manual_trace_review_note_v1.md"

REQUIRED_COLS = [
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
    "raw_direct_common_cause_row_count",
    "raw_direct_common_cause_dates",
    "raw_direct_common_cause_family",
    "official_current_entry_flag",
    "official_current_dates",
    "nearest_official_current_gap_days",
    "report_lane_presence",
    "best_report_lane",
    "synchrony_bucket",
    "friction_blocker_types",
]

RAW_REQUIRED_COLS = [
    "date",
    "panel_id",
    "group_off_date",
    "site_event_soft",
    "site_event_hard",
    "pre_ews",
    "prefault_B",
    "fault_like_day",
    "final_fault",
    "critical_fault",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "co_drop_frac",
    "source_csv",
]

DETAIL_COLS = [
    "trace_case_id",
    "source_review_case_id",
    "source_search_case_id",
    "site",
    "panel_id",
    "panel_root_id",
    "structural_blocker_subtype",
    "trace_outcome_bucket",
    "trace_bridge_scope",
    "rawonly_report_bridge_candidate_flag",
    "official_current_bridge_candidate_flag",
    "semantic_patch_candidate_flag",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "threshold_patch_allowed_flag",
    "raw_direct_common_cause_dates",
    "raw_direct_common_cause_family",
    "official_current_dates",
    "rawonly_signal_dates",
    "precursor_dates",
    "nearest_official_current_signed_gap_days",
    "nearest_rawonly_signal_signed_gap_days",
    "nearest_precursor_signed_gap_days",
    "raw_direct_trace_row_count",
    "raw_mid_ratio_min",
    "raw_mid_v_ratio_median",
    "raw_mid_i_ratio_median",
    "raw_co_drop_frac_max",
    "same_root_same_date_direct_count",
    "raw_trace_source_files",
    "required_next_evidence",
    "review_note",
]

SUMMARY_COLS = [
    "trace_outcome_bucket",
    "trace_bridge_scope",
    "cases",
    "unique_panel_roots",
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
            "Trace BR-073 common-cause manual targets against raw/report dates to determine whether "
            "they are bridgeable evidence or must remain hold/context."
        )
    )
    parser.add_argument("--input-manifest", type=Path, default=None)
    parser.add_argument("--blocker-input", type=Path, default=DEFAULT_BLOCKER_INPUT)
    parser.add_argument("--current-input", type=Path, default=DEFAULT_CURRENT_INPUT)
    parser.add_argument("--precursor-input", type=Path, default=DEFAULT_PRECURSOR_INPUT)
    parser.add_argument("--rawonly-signal-input", type=Path, default=DEFAULT_RAWONLY_SIGNAL_INPUT)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
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
                f"panel-day evidence input manifest is missing `{key}`; "
                f"pass {flag} explicitly or add inputs.{key}"
            )
        return resolve_path(repo_root, manifest_value), "input_manifest"
    return resolve_path(repo_root, arg_value), "legacy_default"


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def normalize_date(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    ts = pd.to_datetime(text, errors="coerce")
    if pd.isna(ts):
        return ""
    return ts.strftime("%Y-%m-%d")


def numeric_value(value: object) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0.0 if pd.isna(numeric) else float(numeric)


def int_value(value: object) -> int:
    return int(round(numeric_value(value)))


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


def split_dates(value: object) -> list[str]:
    dates: list[str] = []
    for part in normalize_text(value).split("|"):
        date = normalize_date(part)
        if date:
            dates.append(date)
    return sorted(set(dates))


def signed_nearest_gap(raw_dates: list[str], report_dates: list[str]) -> int | str:
    if not raw_dates or not report_dates:
        return ""
    best_gap: int | None = None
    for raw_date in raw_dates:
        raw_ts = pd.Timestamp(raw_date)
        for report_date in report_dates:
            gap = int((raw_ts - pd.Timestamp(report_date)).days)
            if best_gap is None or abs(gap) < abs(best_gap):
                best_gap = gap
    return "" if best_gap is None else best_gap


def date_map(df: pd.DataFrame, date_cols: list[str]) -> dict[tuple[str, str], list[str]]:
    if df.empty:
        return {}
    require_columns(df, ["site", "panel_id"], "report input")
    available = [col for col in date_cols if col in df.columns]
    out: dict[tuple[str, str], set[str]] = {}
    for row in df.to_dict(orient="records"):
        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        for col in available:
            date = normalize_date(row.get(col))
            if date:
                out.setdefault(key, set()).add(date)
    return {key: sorted(values) for key, values in out.items()}


def raw_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    text = series.map(normalize_text).str.lower()
    numeric = pd.to_numeric(series, errors="coerce").fillna(0)
    return text.isin({"true", "t", "yes", "y", "1"}) | (numeric > 0)


def panel_root_id(panel_id: str) -> str:
    parts = panel_id.split(".")
    if len(parts) >= 3:
        return ".".join(parts[:-1])
    return panel_id


def load_site_raw(data_root: Path, site: str) -> pd.DataFrame:
    path = data_root / site / "out" / "ae_simple_fault_candidates.csv"
    if not path.exists():
        return pd.DataFrame(columns=RAW_REQUIRED_COLS)
    raw = pd.read_csv(path, low_memory=False)
    require_columns(raw, RAW_REQUIRED_COLS, f"raw candidates for {site}")
    raw["date"] = raw["date"].map(normalize_date)
    raw["panel_id"] = raw["panel_id"].map(normalize_text)
    raw["panel_root_id"] = raw["panel_id"].map(panel_root_id)
    for col in ["mid_ratio", "mid_v_ratio", "mid_i_ratio", "co_drop_frac"]:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
    raw["_direct_common_cause"] = (
        raw_bool(raw["group_off_date"])
        | (pd.to_numeric(raw["site_event_soft"], errors="coerce").fillna(0) > 0)
        | (pd.to_numeric(raw["site_event_hard"], errors="coerce").fillna(0) > 0)
    )
    raw["_signal"] = (
        raw_bool(raw["pre_ews"])
        | raw_bool(raw["prefault_B"])
        | raw_bool(raw["fault_like_day"])
        | raw_bool(raw["final_fault"])
        | raw_bool(raw["critical_fault"])
    )
    return raw


def raw_trace_stats(raw: pd.DataFrame, panel_id: str, panel_root: str, dates: list[str]) -> dict[str, object]:
    if raw.empty or not dates:
        return {
            "raw_direct_trace_row_count": 0,
            "raw_mid_ratio_min": "",
            "raw_mid_v_ratio_median": "",
            "raw_mid_i_ratio_median": "",
            "raw_co_drop_frac_max": "",
            "same_root_same_date_direct_count": 0,
            "raw_trace_source_files": "",
        }
    trace = raw.loc[raw["panel_id"].eq(panel_id) & raw["date"].isin(dates) & raw["_direct_common_cause"] & raw["_signal"]].copy()
    same_root = raw.loc[
        raw["panel_root_id"].eq(panel_root)
        & raw["date"].isin(dates)
        & raw["_direct_common_cause"]
        & raw["_signal"]
    ]
    if trace.empty:
        return {
            "raw_direct_trace_row_count": 0,
            "raw_mid_ratio_min": "",
            "raw_mid_v_ratio_median": "",
            "raw_mid_i_ratio_median": "",
            "raw_co_drop_frac_max": "",
            "same_root_same_date_direct_count": int(len(same_root)),
            "raw_trace_source_files": "",
        }
    return {
        "raw_direct_trace_row_count": int(len(trace)),
        "raw_mid_ratio_min": round(float(trace["mid_ratio"].min()), 6),
        "raw_mid_v_ratio_median": round(float(trace["mid_v_ratio"].median()), 6),
        "raw_mid_i_ratio_median": round(float(trace["mid_i_ratio"].median()), 6),
        "raw_co_drop_frac_max": round(float(trace["co_drop_frac"].max()), 6),
        "same_root_same_date_direct_count": int(len(same_root)),
        "raw_trace_source_files": "|".join(sorted(trace["source_csv"].map(normalize_text).dropna().unique())),
    }


def normalize_blockers(df: pd.DataFrame) -> pd.DataFrame:
    require_columns(df, REQUIRED_COLS, "blocker input")
    out = df[REQUIRED_COLS].copy()
    for col in out.columns:
        if out[col].dtype == object:
            out[col] = out[col].map(normalize_text)
    return out.loc[out["manual_trace_review_flag"].map(int_value).eq(1)].reset_index(drop=True)


def classify_trace(
    subtype: str,
    current_dates: list[str],
    rawonly_dates: list[str],
    current_gap: int | str,
    rawonly_gap: int | str,
) -> tuple[str, str, int, int, int, str, str]:
    if current_dates and isinstance(current_gap, int) and current_gap == 0:
        return (
            "exact_current_bridge_review",
            "official_current_same_day",
            0,
            1,
            0,
            "Independent review before any semantic use.",
            "Official/current date and raw direct date coincide, but production use is still blocked pending review.",
        )
    if current_dates and isinstance(current_gap, int) and current_gap > 30:
        return (
            "post_current_common_cause_late_event_hold",
            "official_current_mismatch",
            0,
            0,
            0,
            "Attach evidence that the current date should be corrected before any bridge is considered.",
            "Raw common-cause date occurs long after the official/current fault date.",
        )
    if subtype == "rawonly_near_signal_anchor" and rawonly_dates and isinstance(rawonly_gap, int) and abs(rawonly_gap) <= 3:
        return (
            "rawonly_near_anchor_trace_only",
            "rawonly_report_near_anchor",
            1,
            0,
            0,
            "Trace raw-only report generation before considering any report-layer bridge.",
            "Raw direct date is near a raw-only report date, but there is no official/current closure.",
        )
    return (
        "manual_trace_hold_unresolved",
        "unresolved_manual_trace",
        0,
        0,
        0,
        "Collect stronger report-layer evidence before reopening semantic discussion.",
        "Manual trace did not establish a bridgeable current/report-layer relation.",
    )


def build_detail(
    blockers: pd.DataFrame,
    raw_by_site: dict[str, pd.DataFrame],
    current_dates: dict[tuple[str, str], list[str]],
    precursor_dates: dict[tuple[str, str], list[str]],
    rawonly_dates: dict[tuple[str, str], list[str]],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for idx, row in blockers.sort_values(["site", "panel_id", "review_case_id"]).reset_index(drop=True).iterrows():
        site = normalize_text(row["site"])
        panel_id = normalize_text(row["panel_id"])
        panel_root = normalize_text(row["panel_root_id"])
        key = (site, panel_id)
        raw_dates = split_dates(row["raw_direct_common_cause_dates"])
        current_panel_dates = current_dates.get(key, [])
        precursor_panel_dates = precursor_dates.get(key, [])
        rawonly_panel_dates = rawonly_dates.get(key, [])
        current_gap = signed_nearest_gap(raw_dates, current_panel_dates)
        precursor_gap = signed_nearest_gap(raw_dates, precursor_panel_dates)
        rawonly_gap = signed_nearest_gap(raw_dates, rawonly_panel_dates)
        stats = raw_trace_stats(raw_by_site.get(site, pd.DataFrame()), panel_id, panel_root, raw_dates)
        outcome, scope, rawonly_bridge, current_bridge, semantic_flag, next_evidence, note = classify_trace(
            normalize_text(row["structural_blocker_subtype"]),
            current_panel_dates,
            rawonly_panel_dates,
            current_gap,
            rawonly_gap,
        )
        rows.append(
            {
                "trace_case_id": f"BR074-{idx + 1:03d}",
                "source_review_case_id": normalize_text(row["review_case_id"]),
                "source_search_case_id": normalize_text(row["source_search_case_id"]),
                "site": site,
                "panel_id": panel_id,
                "panel_root_id": panel_root,
                "structural_blocker_subtype": normalize_text(row["structural_blocker_subtype"]),
                "trace_outcome_bucket": outcome,
                "trace_bridge_scope": scope,
                "rawonly_report_bridge_candidate_flag": rawonly_bridge,
                "official_current_bridge_candidate_flag": current_bridge,
                "semantic_patch_candidate_flag": semantic_flag,
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
                "threshold_patch_allowed_flag": 0,
                "raw_direct_common_cause_dates": "|".join(raw_dates),
                "raw_direct_common_cause_family": normalize_text(row["raw_direct_common_cause_family"]),
                "official_current_dates": "|".join(current_panel_dates),
                "rawonly_signal_dates": "|".join(rawonly_panel_dates),
                "precursor_dates": "|".join(precursor_panel_dates),
                "nearest_official_current_signed_gap_days": current_gap,
                "nearest_rawonly_signal_signed_gap_days": rawonly_gap,
                "nearest_precursor_signed_gap_days": precursor_gap,
                **stats,
                "required_next_evidence": next_evidence,
                "review_note": note,
            }
        )
    return pd.DataFrame(rows).reindex(columns=DETAIL_COLS)


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary = (
        detail.groupby(["trace_outcome_bucket", "trace_bridge_scope"], dropna=False)
        .agg(
            cases=("trace_case_id", "nunique"),
            unique_panel_roots=("panel_root_id", "nunique"),
            rawonly_report_bridge_candidate_sum=("rawonly_report_bridge_candidate_flag", "sum"),
            official_current_bridge_candidate_sum=("official_current_bridge_candidate_flag", "sum"),
            semantic_patch_candidate_sum=("semantic_patch_candidate_flag", "sum"),
            operator_promotion_allowed_sum=("operator_promotion_allowed_flag", "sum"),
            engine_patch_candidate_sum=("engine_patch_candidate_flag", "sum"),
            threshold_patch_allowed_sum=("threshold_patch_allowed_flag", "sum"),
        )
        .reset_index()
    )
    return summary.reindex(columns=SUMMARY_COLS).sort_values(["trace_outcome_bucket", "trace_bridge_scope"])


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


def write_note(
    output_dir: Path,
    detail: pd.DataFrame,
    summary: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> None:
    source_map = input_resolution_sources or {}
    lines = [
        "# panel_day_engine_common_cause_manual_trace_review_note_v1",
        "",
        "## Purpose",
        "- Trace BR-073 manual targets against raw and report dates.",
        "- Distinguish raw-only report bridge candidates from official/current closure.",
        "",
        "## Inputs",
        f"- evidence input manifest: `{input_manifest_path if input_manifest_path is not None else 'not provided'}`",
        "",
        "## Input Resolution Sources",
        f"- `blocker_input`: `{source_map.get('blocker_input', 'legacy_default')}`",
        f"- `current_input`: `{source_map.get('current_input', 'legacy_default')}`",
        f"- `precursor_input`: `{source_map.get('precursor_input', 'legacy_default')}`",
        f"- `rawonly_signal_input`: `{source_map.get('rawonly_signal_input', 'legacy_default')}`",
        "",
        "## Guardrails",
        f"- detail rows: `{len(detail)}`",
        f"- raw-only report bridge candidate sum: `{int(detail['rawonly_report_bridge_candidate_flag'].sum()) if len(detail) else 0}`",
        f"- official/current bridge candidate sum: `{int(detail['official_current_bridge_candidate_flag'].sum()) if len(detail) else 0}`",
        f"- semantic patch candidate sum: `{int(detail['semantic_patch_candidate_flag'].sum()) if len(detail) else 0}`",
        f"- operator promotion allowed sum: `{int(detail['operator_promotion_allowed_flag'].sum()) if len(detail) else 0}`",
        f"- engine patch candidate sum: `{int(detail['engine_patch_candidate_flag'].sum()) if len(detail) else 0}`",
        f"- threshold patch allowed sum: `{int(detail['threshold_patch_allowed_flag'].sum()) if len(detail) else 0}`",
        "",
        "## Summary",
        dataframe_to_markdown(summary),
        "",
        "## Detail",
        dataframe_to_markdown(detail),
        "",
        "## Interpretation",
        "- A raw-only near-anchor can explain a raw-only report trace, but not official/current exact closure.",
        "- A post-current common-cause date is a mismatch unless the current report date is independently corrected.",
        "- No semantic patch is authorized by this trace review.",
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
            "--blocker-input",
            "--current-input",
            "--precursor-input",
            "--rawonly-signal-input",
        ]
        if cli_flag_provided(flag, argv)
    }
    blocker_input, blocker_input_source = resolve_manifest_input(
        repo_root,
        "blocker_input",
        "--blocker-input",
        args.blocker_input,
        input_manifest,
        explicit_flags,
    )
    current_input, current_input_source = resolve_manifest_input(
        repo_root,
        "current_input",
        "--current-input",
        args.current_input,
        input_manifest,
        explicit_flags,
    )
    precursor_input, precursor_input_source = resolve_manifest_input(
        repo_root,
        "precursor_input",
        "--precursor-input",
        args.precursor_input,
        input_manifest,
        explicit_flags,
    )
    rawonly_signal_input, rawonly_signal_input_source = resolve_manifest_input(
        repo_root,
        "rawonly_signal_input",
        "--rawonly-signal-input",
        args.rawonly_signal_input,
        input_manifest,
        explicit_flags,
    )
    input_resolution_sources = {
        "blocker_input": blocker_input_source,
        "current_input": current_input_source,
        "precursor_input": precursor_input_source,
        "rawonly_signal_input": rawonly_signal_input_source,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    blockers = normalize_blockers(read_csv(blocker_input))
    current = date_map(read_csv(current_input, required=False), ["고장날짜"])
    precursor = date_map(read_csv(precursor_input, required=False), ["전조날짜"])
    rawonly = date_map(read_csv(rawonly_signal_input, required=False), ["신호 기준일", "전조 시작일"])
    raw_by_site = {site: load_site_raw(args.data_root, site) for site in sorted(blockers["site"].unique())}
    detail = build_detail(blockers, raw_by_site, current, precursor, rawonly)
    summary = build_summary(detail)
    if len(detail) and int(detail["semantic_patch_candidate_flag"].sum()) != 0:
        raise SystemExit("manual trace review must not authorize semantic patch candidates")
    if len(detail) and int(detail["operator_promotion_allowed_flag"].sum()) != 0:
        raise SystemExit("manual trace review must not allow operator promotion")
    if len(detail) and int(detail["engine_patch_candidate_flag"].sum()) != 0:
        raise SystemExit("manual trace review must not allow engine patch")
    if len(detail) and int(detail["threshold_patch_allowed_flag"].sum()) != 0:
        raise SystemExit("manual trace review must not allow threshold patch")
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(args.output_dir, detail, summary, input_manifest_path, input_resolution_sources)


if __name__ == "__main__":
    main()
