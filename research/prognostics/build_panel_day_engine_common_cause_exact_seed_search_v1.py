#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_JUDGMENT_INPUT = Path(
    "/private/tmp/fault_family_judgment_candidate_packet_check/"
    "panel_day_engine_fault_family_judgment_candidate_packet_v1.csv"
)
DEFAULT_SYNCHRONY_INPUT = Path(
    "/private/tmp/common_cause_synchrony_axis_sidecar_check/"
    "panel_day_engine_common_cause_synchrony_axis_v1.csv"
)
DEFAULT_CURRENT_INPUT = Path("/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_current_v1.csv")
DEFAULT_PRECURSOR_INPUT = Path(
    "/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_precursor_report_v1.csv"
)
DEFAULT_RAWONLY_SIGNAL_INPUT = Path(
    "/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_raw_only_fault_signal_report_v1.csv"
)
DEFAULT_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"

DETAIL_OUTPUT_NAME = "panel_day_engine_common_cause_exact_seed_search_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_common_cause_exact_seed_search_summary_v1.csv"
SITE_STATUS_OUTPUT_NAME = "panel_day_engine_common_cause_exact_seed_site_status_summary_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_common_cause_exact_seed_search_note_v1.md"

JUDGMENT_REQUIRED_COLS = [
    "candidate_case_id",
    "site",
    "panel_id",
    "judgment_bucket",
    "candidate_family_label_ko",
    "candidate_family_track",
    "review_focus_bucket",
    "friction_blocker_types",
    "friction_direct_row_count",
    "friction_group_off_row_count",
    "friction_site_event_row_count",
    "synchrony_bucket",
    "common_cause_row_count",
    "site_event_row_count",
    "group_off_row_count",
    "subgroup_common_cause_row_count",
    "max_co_drop_frac",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "threshold_candidate_role",
]

SYNCHRONY_COLS = [
    "site",
    "panel_id",
    "best_report_lane",
    "synchrony_lane_bucket",
    "first_common_cause_date",
    "last_common_cause_date",
    "any_pre_ews",
    "any_prefault_B",
    "any_fault_like_day",
    "any_final_fault",
    "any_critical_fault",
]

DETAIL_COLS = [
    "search_case_id",
    "source_candidate_case_id",
    "site",
    "panel_id",
    "panel_root_id",
    "primary_judgment_role",
    "usage_tag",
    "common_cause_search_bucket",
    "exact_family_closure_flag",
    "candidate_reservoir_flag",
    "structural_blocker_flag",
    "supportive_hint_flag",
    "blocker_regression_seed_flag",
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
    "synchrony_lane_bucket",
    "common_cause_row_count",
    "site_event_row_count",
    "group_off_row_count",
    "subgroup_common_cause_row_count",
    "max_co_drop_frac",
    "friction_blocker_types",
    "friction_direct_row_count",
    "friction_group_off_row_count",
    "friction_site_event_row_count",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "threshold_patch_allowed_flag",
    "allowed_use",
    "still_missing",
    "review_note",
]

SUMMARY_COLS = [
    "primary_judgment_role",
    "usage_tag",
    "common_cause_search_bucket",
    "cases",
    "unique_panel_roots",
    "raw_direct_common_cause_rows",
    "exact_family_closure_sum",
    "candidate_reservoir_sum",
    "structural_blocker_sum",
    "supportive_hint_sum",
    "blocker_regression_seed_sum",
    "operator_promotion_allowed_sum",
    "engine_patch_candidate_sum",
    "threshold_patch_allowed_sum",
]

SITE_STATUS_COLS = [
    "site",
    "cases",
    "unique_panel_roots",
    "raw_direct_common_cause_panel_count",
    "raw_direct_common_cause_rows",
    "official_current_entry_count",
    "official_current_same_day_overlap_sum",
    "exact_family_closure_sum",
    "candidate_reservoir_sum",
    "structural_blocker_sum",
    "blocker_regression_seed_sum",
    "supportive_hint_sum",
    "nearest_official_current_gap_min",
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
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Re-search common-cause exact same-day evidence and classify each row by BR-036 "
            "judgment role before any semantic algorithm patch."
        )
    )
    parser.add_argument("--input-manifest", type=Path, default=None)
    parser.add_argument("--judgment-input", type=Path, default=DEFAULT_JUDGMENT_INPUT)
    parser.add_argument("--synchrony-input", type=Path, default=DEFAULT_SYNCHRONY_INPUT)
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


def numeric_value(value: object) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0.0 if pd.isna(numeric) else float(numeric)


def int_value(value: object) -> int:
    return int(round(numeric_value(value)))


def flag_value(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"true", "t", "yes", "y", "1"}:
        return 1
    if text in {"false", "f", "no", "n", "0", ""}:
        return 0
    return int(numeric_value(value) > 0)


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


def normalize_date(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    ts = pd.to_datetime(text, errors="coerce")
    if pd.isna(ts):
        return ""
    return ts.strftime("%Y-%m-%d")


def panel_root_id(panel_id: str) -> str:
    parts = panel_id.split(".")
    if len(parts) >= 3:
        return ".".join(parts[:-1])
    return panel_id


def normalize_judgment(df: pd.DataFrame) -> pd.DataFrame:
    require_columns(df, JUDGMENT_REQUIRED_COLS, "judgment input")
    out = df[JUDGMENT_REQUIRED_COLS].copy()
    for col in out.columns:
        if out[col].dtype == object:
            out[col] = out[col].map(normalize_text)
    out = out.loc[out["candidate_family_track"].eq("external_common_cause")].copy()
    return out.reset_index(drop=True)


def normalize_synchrony(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=SYNCHRONY_COLS)
    require_columns(df, SYNCHRONY_COLS, "synchrony input")
    out = df[SYNCHRONY_COLS].copy()
    for col in ["site", "panel_id", "best_report_lane", "synchrony_lane_bucket"]:
        out[col] = out[col].map(normalize_text)
    for col in ["first_common_cause_date", "last_common_cause_date"]:
        out[col] = out[col].map(normalize_date)
    for col in ["any_pre_ews", "any_prefault_B", "any_fault_like_day", "any_final_fault", "any_critical_fault"]:
        out[col] = out[col].map(flag_value)
    return out.drop_duplicates(["site", "panel_id"])


def report_dates(df: pd.DataFrame, date_cols: list[str]) -> dict[tuple[str, str], list[str]]:
    if df.empty:
        return {}
    require_columns(df, ["site", "panel_id"], "report input")
    out: dict[tuple[str, str], set[str]] = {}
    available = [col for col in date_cols if col in df.columns]
    for row in df.to_dict(orient="records"):
        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]))
        for col in available:
            date = normalize_date(row.get(col))
            if date:
                out.setdefault(key, set()).add(date)
    return {key: sorted(values) for key, values in out.items()}


def report_presence(
    current_dates: dict[tuple[str, str], list[str]],
    precursor_dates: dict[tuple[str, str], list[str]],
    rawonly_dates: dict[tuple[str, str], list[str]],
    key: tuple[str, str],
) -> str:
    lanes: list[str] = []
    if key in current_dates:
        lanes.append("official_current")
    if key in precursor_dates:
        lanes.append("precursor")
    if key in rawonly_dates:
        lanes.append("rawonly_signal")
    return "|".join(lanes) if lanes else "none"


def raw_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    text = series.map(normalize_text).str.lower()
    numeric = pd.to_numeric(series, errors="coerce").fillna(0)
    return text.isin({"true", "t", "yes", "y", "1"}) | (numeric > 0)


def load_raw_direct_rows(data_root: Path, sites: list[str]) -> dict[tuple[str, str], dict[str, object]]:
    by_panel: dict[tuple[str, str], dict[str, object]] = {}
    for site in sites:
        path = data_root / site / "out" / "ae_simple_fault_candidates.csv"
        if not path.exists():
            continue
        raw = pd.read_csv(path, low_memory=False)
        require_columns(raw, RAW_REQUIRED_COLS, f"raw candidates for {site}")
        raw["date"] = raw["date"].map(normalize_date)
        raw["panel_id"] = raw["panel_id"].map(normalize_text)
        group_off = raw_bool(raw["group_off_date"])
        site_event_soft = pd.to_numeric(raw["site_event_soft"], errors="coerce").fillna(0) > 0
        site_event_hard = pd.to_numeric(raw["site_event_hard"], errors="coerce").fillna(0) > 0
        direct_common_cause = group_off | site_event_soft | site_event_hard
        signal = (
            raw_bool(raw["pre_ews"])
            | raw_bool(raw["prefault_B"])
            | raw_bool(raw["fault_like_day"])
            | raw_bool(raw["final_fault"])
            | raw_bool(raw["critical_fault"])
        )
        raw = raw.loc[direct_common_cause & signal].copy()
        for panel_id, group in raw.groupby("panel_id", dropna=False):
            if not panel_id:
                continue
            dates = sorted(date for date in group["date"].dropna().unique() if date)
            family_parts: list[str] = []
            if raw_bool(group["group_off_date"]).any():
                family_parts.append("group_off_date")
            if (pd.to_numeric(group["site_event_soft"], errors="coerce").fillna(0) > 0).any():
                family_parts.append("site_event_soft")
            if (pd.to_numeric(group["site_event_hard"], errors="coerce").fillna(0) > 0).any():
                family_parts.append("site_event_hard")
            by_panel[(site, panel_id)] = {
                "raw_direct_common_cause_row_count": int(len(group)),
                "raw_direct_common_cause_dates": dates,
                "raw_direct_common_cause_family": "|".join(family_parts),
            }
    return by_panel


def nearest_gap_days(left_dates: list[str], right_dates: list[str]) -> int | None:
    if not left_dates or not right_dates:
        return None
    gaps: list[int] = []
    for left in left_dates:
        left_ts = pd.Timestamp(left)
        for right in right_dates:
            gaps.append(abs((left_ts - pd.Timestamp(right)).days))
    return min(gaps) if gaps else None


def role_and_bucket(
    raw_count: int,
    official_current_overlap: int,
    official_current_dates: list[str],
    report_presence_value: str,
    friction_blocker: str,
    strong_common_cause: bool,
    subgroup_context: bool,
) -> tuple[str, str, int, int, int, int, int]:
    blocker_text = friction_blocker.lower()
    explicit_blocker = bool(blocker_text) and blocker_text not in {"none", "nan"}
    report_lane_entry = report_presence_value != "none"
    candidate_reservoir = int(raw_count > 0)
    structural_blocker = int(
        raw_count > 0
        and official_current_overlap == 0
        and (
            explicit_blocker
            or report_lane_entry
            or not official_current_dates
        )
    )
    supportive_hint = int(raw_count == 0 and (strong_common_cause or subgroup_context))
    blocker_seed = int(strong_common_cause)

    if official_current_overlap:
        return (
            "exact_family_closure",
            "exact_same_day_official_current_overlap",
            1,
            candidate_reservoir,
            structural_blocker,
            supportive_hint,
            blocker_seed,
        )
    if structural_blocker:
        return (
            "structural_blocker",
            "raw_direct_row_but_report_layer_misaligned",
            0,
            candidate_reservoir,
            structural_blocker,
            supportive_hint,
            blocker_seed,
        )
    if candidate_reservoir:
        return (
            "candidate_reservoir",
            "raw_direct_row_without_report_layer_closure",
            0,
            candidate_reservoir,
            structural_blocker,
            supportive_hint,
            blocker_seed,
        )
    if subgroup_context:
        return (
            "supportive_hint",
            "subgroup_or_breadth_context_hold",
            0,
            candidate_reservoir,
            structural_blocker,
            supportive_hint,
            blocker_seed,
        )
    return (
        "supportive_hint",
        "common_cause_context_hold",
        0,
        candidate_reservoir,
        structural_blocker,
        supportive_hint,
        blocker_seed,
    )


def allowed_use(role: str, usage_tag: str) -> str:
    if role == "exact_family_closure":
        return "candidate for exact missing-family closure review only; no automatic production promotion"
    if role == "structural_blocker":
        return "patch-target selection and blocker split only"
    if role == "candidate_reservoir":
        return "blocker search input and pressure-test seed source only"
    if usage_tag == "block_panel_local_promotion_regression_seed":
        return "regression pressure for future semantic patches only"
    return "context/explanation support only"


def still_missing(role: str) -> str:
    if role == "exact_family_closure":
        return "independent review before any operator-facing or semantic patch use"
    if role == "structural_blocker":
        return "report-layer same-day closure or explicit lane/date-alignment resolution"
    if role == "candidate_reservoir":
        return "report-layer entry plus official/current date coincidence"
    return "direct row or report-layer exact family evidence"


def build_detail(
    judgment: pd.DataFrame,
    synchrony: pd.DataFrame,
    raw_direct: dict[tuple[str, str], dict[str, object]],
    current_dates: dict[tuple[str, str], list[str]],
    precursor_dates: dict[tuple[str, str], list[str]],
    rawonly_dates: dict[tuple[str, str], list[str]],
) -> pd.DataFrame:
    sync_lookup = synchrony.set_index(["site", "panel_id"]).to_dict(orient="index") if not synchrony.empty else {}
    rows: list[dict[str, object]] = []
    sort_cols = ["site", "panel_id", "candidate_case_id"]
    for idx, row in judgment.sort_values(sort_cols).reset_index(drop=True).iterrows():
        site = normalize_text(row["site"])
        panel_id = normalize_text(row["panel_id"])
        key = (site, panel_id)
        sync = sync_lookup.get(key, {})
        raw = raw_direct.get(
            key,
            {
                "raw_direct_common_cause_row_count": 0,
                "raw_direct_common_cause_dates": [],
                "raw_direct_common_cause_family": "",
            },
        )
        raw_dates = list(raw["raw_direct_common_cause_dates"])
        current_panel_dates = current_dates.get(key, [])
        current_overlap = int(bool(set(raw_dates) & set(current_panel_dates)))
        report_presence_value = report_presence(current_dates, precursor_dates, rawonly_dates, key)
        current_gap = nearest_gap_days(raw_dates, current_panel_dates)
        strong = normalize_text(row["review_focus_bucket"]) == "strong_common_cause_hold_review"
        subgroup_context = normalize_text(row["review_focus_bucket"]) == "subgroup_or_breadth_context_review"
        (
            role,
            bucket,
            exact_flag,
            reservoir_flag,
            structural_flag,
            supportive_flag,
            blocker_seed_flag,
        ) = role_and_bucket(
            raw_count=int(raw["raw_direct_common_cause_row_count"]),
            official_current_overlap=current_overlap,
            official_current_dates=current_panel_dates,
            report_presence_value=report_presence_value,
            friction_blocker=normalize_text(row["friction_blocker_types"]),
            strong_common_cause=strong,
            subgroup_context=subgroup_context,
        )
        usage_tag = "block_panel_local_promotion_regression_seed" if blocker_seed_flag else "review_context_only"
        rows.append(
            {
                "search_case_id": f"BR072-{idx + 1:03d}",
                "source_candidate_case_id": normalize_text(row["candidate_case_id"]),
                "site": site,
                "panel_id": panel_id,
                "panel_root_id": panel_root_id(panel_id),
                "primary_judgment_role": role,
                "usage_tag": usage_tag,
                "common_cause_search_bucket": bucket,
                "exact_family_closure_flag": exact_flag,
                "candidate_reservoir_flag": reservoir_flag,
                "structural_blocker_flag": structural_flag,
                "supportive_hint_flag": supportive_flag,
                "blocker_regression_seed_flag": blocker_seed_flag,
                "raw_direct_common_cause_row_count": int(raw["raw_direct_common_cause_row_count"]),
                "raw_direct_common_cause_dates": "|".join(raw_dates),
                "raw_direct_common_cause_family": normalize_text(raw["raw_direct_common_cause_family"]),
                "official_current_entry_flag": int(bool(current_panel_dates)),
                "official_current_dates": "|".join(current_panel_dates),
                "official_current_same_day_overlap_flag": current_overlap,
                "nearest_official_current_gap_days": "" if current_gap is None else current_gap,
                "any_report_lane_entry_flag": int(report_presence_value != "none"),
                "report_lane_presence": report_presence_value,
                "best_report_lane": normalize_text(sync.get("best_report_lane")),
                "synchrony_bucket": normalize_text(row["synchrony_bucket"]),
                "synchrony_lane_bucket": normalize_text(sync.get("synchrony_lane_bucket")),
                "common_cause_row_count": int_value(row["common_cause_row_count"]),
                "site_event_row_count": int_value(row["site_event_row_count"]),
                "group_off_row_count": int_value(row["group_off_row_count"]),
                "subgroup_common_cause_row_count": int_value(row["subgroup_common_cause_row_count"]),
                "max_co_drop_frac": round(numeric_value(row["max_co_drop_frac"]), 6),
                "friction_blocker_types": normalize_text(row["friction_blocker_types"]),
                "friction_direct_row_count": int_value(row["friction_direct_row_count"]),
                "friction_group_off_row_count": int_value(row["friction_group_off_row_count"]),
                "friction_site_event_row_count": int_value(row["friction_site_event_row_count"]),
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
                "threshold_patch_allowed_flag": 0,
                "allowed_use": allowed_use(role, usage_tag),
                "still_missing": still_missing(role),
                "review_note": (
                    "Common-cause exact evidence is role-tagged by BR-036; this search does not "
                    "authorize operator promotion, engine patch, or threshold patch."
                ),
            }
        )
    return pd.DataFrame(rows).reindex(columns=DETAIL_COLS)


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary = (
        detail.groupby(["primary_judgment_role", "usage_tag", "common_cause_search_bucket"], dropna=False)
        .agg(
            cases=("search_case_id", "nunique"),
            unique_panel_roots=("panel_root_id", "nunique"),
            raw_direct_common_cause_rows=("raw_direct_common_cause_row_count", "sum"),
            exact_family_closure_sum=("exact_family_closure_flag", "sum"),
            candidate_reservoir_sum=("candidate_reservoir_flag", "sum"),
            structural_blocker_sum=("structural_blocker_flag", "sum"),
            supportive_hint_sum=("supportive_hint_flag", "sum"),
            blocker_regression_seed_sum=("blocker_regression_seed_flag", "sum"),
            operator_promotion_allowed_sum=("operator_promotion_allowed_flag", "sum"),
            engine_patch_candidate_sum=("engine_patch_candidate_flag", "sum"),
            threshold_patch_allowed_sum=("threshold_patch_allowed_flag", "sum"),
        )
        .reset_index()
    )
    return summary.reindex(columns=SUMMARY_COLS).sort_values(
        ["primary_judgment_role", "usage_tag", "common_cause_search_bucket"]
    )


def build_site_status(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=SITE_STATUS_COLS)
    work = detail.copy()
    gap = pd.to_numeric(work["nearest_official_current_gap_days"], errors="coerce")
    work["_nearest_gap"] = gap
    summary = (
        work.groupby("site", dropna=False)
        .agg(
            cases=("search_case_id", "nunique"),
            unique_panel_roots=("panel_root_id", "nunique"),
            raw_direct_common_cause_panel_count=("candidate_reservoir_flag", "sum"),
            raw_direct_common_cause_rows=("raw_direct_common_cause_row_count", "sum"),
            official_current_entry_count=("official_current_entry_flag", "sum"),
            official_current_same_day_overlap_sum=("official_current_same_day_overlap_flag", "sum"),
            exact_family_closure_sum=("exact_family_closure_flag", "sum"),
            candidate_reservoir_sum=("candidate_reservoir_flag", "sum"),
            structural_blocker_sum=("structural_blocker_flag", "sum"),
            blocker_regression_seed_sum=("blocker_regression_seed_flag", "sum"),
            supportive_hint_sum=("supportive_hint_flag", "sum"),
            nearest_official_current_gap_min=("_nearest_gap", "min"),
        )
        .reset_index()
    )
    summary["nearest_official_current_gap_min"] = summary["nearest_official_current_gap_min"].fillna("")
    return summary.reindex(columns=SITE_STATUS_COLS).sort_values("site")


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
    site_status: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> None:
    exact_sum = int(detail["exact_family_closure_flag"].sum()) if len(detail) else 0
    reservoir_sum = int(detail["candidate_reservoir_flag"].sum()) if len(detail) else 0
    structural_sum = int(detail["structural_blocker_flag"].sum()) if len(detail) else 0
    blocker_sum = int(detail["blocker_regression_seed_flag"].sum()) if len(detail) else 0
    supportive_sum = int(detail["supportive_hint_flag"].sum()) if len(detail) else 0
    raw_rows = int(detail["raw_direct_common_cause_row_count"].sum()) if len(detail) else 0
    source_map = input_resolution_sources or {}
    lines = [
        "# panel_day_engine_common_cause_exact_seed_search_note_v1",
        "",
        "## Purpose",
        "- Re-read external/common-cause candidates as BR-036 judgment roles.",
        "- Check whether conservatism is blocking all progress or preserving a useful next search frontier.",
        "",
        "## Inputs",
        f"- evidence input manifest: `{input_manifest_path if input_manifest_path is not None else 'not provided'}`",
        "",
        "## Input Resolution Sources",
        f"- `judgment_input`: `{source_map.get('judgment_input', 'legacy_default')}`",
        f"- `synchrony_input`: `{source_map.get('synchrony_input', 'legacy_default')}`",
        f"- `current_input`: `{source_map.get('current_input', 'legacy_default')}`",
        f"- `precursor_input`: `{source_map.get('precursor_input', 'legacy_default')}`",
        f"- `rawonly_signal_input`: `{source_map.get('rawonly_signal_input', 'legacy_default')}`",
        "",
        "## Guardrails",
        f"- detail rows: `{len(detail)}`",
        f"- exact family closure candidates: `{exact_sum}`",
        f"- candidate reservoir panels: `{reservoir_sum}`",
        f"- structural blocker panels: `{structural_sum}`",
        f"- blocker/regression seed panels: `{blocker_sum}`",
        f"- supportive/context hold panels: `{supportive_sum}`",
        f"- raw direct common-cause rows represented: `{raw_rows}`",
        f"- operator promotion allowed sum: `{int(detail['operator_promotion_allowed_flag'].sum()) if len(detail) else 0}`",
        f"- engine patch candidate sum: `{int(detail['engine_patch_candidate_flag'].sum()) if len(detail) else 0}`",
        f"- threshold patch allowed sum: `{int(detail['threshold_patch_allowed_flag'].sum()) if len(detail) else 0}`",
        "",
        "## Judgment Summary",
        dataframe_to_markdown(summary),
        "",
        "## Site Status",
        dataframe_to_markdown(site_status),
        "",
        "## Interpretation",
        "- `exact_family_closure = 0` means no production semantic patch is justified from this search alone.",
        "- This is still progress: raw same-day direct common-cause rows are retained as a candidate reservoir, while BR-071 rows stay regression blockers.",
        "- The next useful move is not to loosen the rule blindly, but to resolve report-lane/date-alignment blockers or attach independent evidence.",
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
            "--judgment-input",
            "--synchrony-input",
            "--current-input",
            "--precursor-input",
            "--rawonly-signal-input",
        ]
        if cli_flag_provided(flag, argv)
    }
    judgment_input, judgment_input_source = resolve_manifest_input(
        repo_root,
        "judgment_input",
        "--judgment-input",
        args.judgment_input,
        input_manifest,
        explicit_flags,
    )
    synchrony_input, synchrony_input_source = resolve_manifest_input(
        repo_root,
        "synchrony_input",
        "--synchrony-input",
        args.synchrony_input,
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
        "judgment_input": judgment_input_source,
        "synchrony_input": synchrony_input_source,
        "current_input": current_input_source,
        "precursor_input": precursor_input_source,
        "rawonly_signal_input": rawonly_signal_input_source,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    judgment = normalize_judgment(read_csv(judgment_input))
    synchrony = normalize_synchrony(read_csv(synchrony_input, required=False))
    current_dates = report_dates(read_csv(current_input, required=False), ["고장날짜"])
    precursor_dates = report_dates(read_csv(precursor_input, required=False), ["전조날짜"])
    rawonly_dates = report_dates(read_csv(rawonly_signal_input, required=False), ["신호 기준일", "전조 시작일"])
    sites = sorted(judgment["site"].dropna().map(normalize_text).unique())
    raw_direct = load_raw_direct_rows(args.data_root, sites)
    detail = build_detail(judgment, synchrony, raw_direct, current_dates, precursor_dates, rawonly_dates)
    summary = build_summary(detail)
    site_status = build_site_status(detail)
    if len(detail) and int(detail["operator_promotion_allowed_flag"].sum()) != 0:
        raise SystemExit("exact seed search must not allow operator promotion")
    if len(detail) and int(detail["engine_patch_candidate_flag"].sum()) != 0:
        raise SystemExit("exact seed search must not allow engine patch")
    if len(detail) and int(detail["threshold_patch_allowed_flag"].sum()) != 0:
        raise SystemExit("exact seed search must not allow threshold patch")
    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    site_status.to_csv(args.output_dir / SITE_STATUS_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(
        args.output_dir,
        detail,
        summary,
        site_status,
        input_manifest_path,
        input_resolution_sources,
    )


if __name__ == "__main__":
    main()
