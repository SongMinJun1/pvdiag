#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_CROSS_AXIS_INPUT = Path(
    "/private/tmp/cross_axis_manifest_sync_review_check/"
    "panel_day_engine_cross_axis_manifest_sync_review_v1.csv"
)
DEFAULT_PRESSURE_INPUT = Path(
    "/private/tmp/fault_family_regression_pressure_packet_check/"
    "panel_day_engine_fault_family_regression_pressure_packet_v1.csv"
)
DEFAULT_THRESHOLD_INPUT = Path("docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_THRESHOLD_CANDIDATE_V1.csv")
DEFAULT_SUBTYPE_INPUT = Path("docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_018_FAULT_SUBTYPE_HYPOTHESIS_MAP_V1.csv")

DETAIL_OUTPUT_NAME = "panel_day_engine_fault_family_judgment_candidate_packet_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_fault_family_judgment_candidate_summary_v1.csv"
CRITERIA_OUTPUT_NAME = "panel_day_engine_fault_family_judgment_candidate_criteria_v1.csv"
NOTE_OUTPUT_NAME = "panel_day_engine_fault_family_judgment_candidate_note_v1.md"

CROSS_AXIS_REQUIRED_COLS = [
    "site",
    "panel_id",
    "axis_presence_count",
    "has_friction_axis",
    "has_recovery_axis",
    "has_common_cause_axis",
    "friction_blocker_types",
    "friction_direct_row_count",
    "friction_group_off_row_count",
    "friction_site_event_row_count",
    "recovery_bucket",
    "re_drop_row_count",
    "recovered_sustained_row_count",
    "synchrony_bucket",
    "common_cause_row_count",
    "site_event_row_count",
    "group_off_row_count",
    "subgroup_common_cause_row_count",
    "max_co_drop_frac",
    "strong_common_cause_flag",
    "subgroup_or_breadth_context_flag",
    "local_or_weak_synchrony_flag",
    "report_entry_blocker_flag",
    "recovery_morphology_pressure_flag",
    "review_focus_bucket",
]

PRESSURE_COLS = [
    "packet_case_id",
    "site",
    "panel_id",
    "packet_bucket",
    "counterexample_bucket",
    "evidence_grade",
    "raw_top1_ko",
    "raw_top1_score",
    "raw_top2_ko",
    "raw_top3_ko",
    "same_day_final_fault_row_count",
    "same_day_common_cause_row_count",
]

DETAIL_COLS = [
    "candidate_case_id",
    "site",
    "panel_id",
    "judgment_bucket",
    "candidate_family_label_ko",
    "candidate_family_track",
    "pressure_packet_case_id",
    "pressure_packet_bucket",
    "pressure_counterexample_bucket",
    "pressure_evidence_grade",
    "raw_top1_ko",
    "raw_top1_score",
    "raw_top2_ko",
    "raw_top3_ko",
    "axis_presence_count",
    "duration_gap_axis_flag",
    "continuity_recurrence_axis_flag",
    "spatiality_common_cause_axis_flag",
    "candidate_evidence_axis_count",
    "review_focus_bucket",
    "friction_blocker_types",
    "friction_direct_row_count",
    "friction_group_off_row_count",
    "friction_site_event_row_count",
    "recovery_bucket",
    "re_drop_row_count",
    "recovered_sustained_row_count",
    "synchrony_bucket",
    "common_cause_row_count",
    "site_event_row_count",
    "group_off_row_count",
    "subgroup_common_cause_row_count",
    "max_co_drop_frac",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "threshold_candidate_role",
    "required_next_evidence",
    "review_note",
]

SUMMARY_COLS = [
    "judgment_bucket",
    "candidate_family_label_ko",
    "site",
    "cases",
    "pressure_seed_cases",
    "duration_gap_axis_cases",
    "continuity_recurrence_axis_cases",
    "spatiality_common_cause_axis_cases",
    "strong_common_cause_cases",
    "operator_promotion_allowed_sum",
    "engine_patch_candidate_sum",
]

CRITERIA_COLS = [
    "family_key",
    "family_label_ko",
    "subtype_key",
    "subtype_label_ko",
    "recommended_shadow_action",
    "candidate_judgment_role",
    "minimum_evidence_shadow_ko",
    "positive_axis_hint",
    "negative_signature_ko",
    "threshold_basis",
    "operator_promotion_allowed_flag",
    "engine_patch_candidate_flag",
    "notes_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an audit-only fault-family judgment candidate packet by combining "
            "cross-axis evidence, regression pressure seeds, and BR-017/018 threshold criteria."
        )
    )
    parser.add_argument("--input-manifest", default=None)
    parser.add_argument("--cross-axis-input", type=Path, default=DEFAULT_CROSS_AXIS_INPUT)
    parser.add_argument("--pressure-input", type=Path, default=DEFAULT_PRESSURE_INPUT)
    parser.add_argument("--threshold-input", type=Path, default=DEFAULT_THRESHOLD_INPUT)
    parser.add_argument("--subtype-input", type=Path, default=DEFAULT_SUBTYPE_INPUT)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def resolve_path(base_root: Path, path_value: str | Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else base_root / path


def load_input_manifest(base_root: Path, value: str | Path | None) -> tuple[Path | None, dict[str, Any]]:
    if value is None or str(value).strip() == "":
        return None, {}
    path = resolve_path(base_root, value)
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


def resolve_chain_input(
    base_root: Path,
    cli_value: str | Path,
    legacy_default: str | Path,
    manifest: dict[str, Any],
    manifest_key: str,
    cli_flag: str,
    explicit_flags: set[str],
) -> tuple[Path, str]:
    if cli_flag in explicit_flags:
        return resolve_path(base_root, cli_value), "explicit_cli"
    if manifest:
        manifest_value = manifest_path_value(manifest, manifest_key)
        if not manifest_value:
            raise KeyError(
                f"panel-day evidence input manifest is missing `{manifest_key}`; "
                f"pass {cli_flag} explicitly or add inputs.{manifest_key}"
            )
        return resolve_path(base_root, manifest_value), "input_manifest"
    return resolve_path(base_root, legacy_default), "legacy_default"


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


def to_float(value: object) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0.0 if pd.isna(numeric) else float(numeric)


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


def normalize_cross_axis(df: pd.DataFrame) -> pd.DataFrame:
    require_columns(df, CROSS_AXIS_REQUIRED_COLS, "cross-axis input")
    out = df[CROSS_AXIS_REQUIRED_COLS].copy()
    text_cols = [
        "site",
        "panel_id",
        "friction_blocker_types",
        "recovery_bucket",
        "synchrony_bucket",
        "review_focus_bucket",
    ]
    flag_cols = [
        "has_friction_axis",
        "has_recovery_axis",
        "has_common_cause_axis",
        "strong_common_cause_flag",
        "subgroup_or_breadth_context_flag",
        "local_or_weak_synchrony_flag",
        "report_entry_blocker_flag",
        "recovery_morphology_pressure_flag",
    ]
    numeric_cols = [
        "axis_presence_count",
        "friction_direct_row_count",
        "friction_group_off_row_count",
        "friction_site_event_row_count",
        "re_drop_row_count",
        "recovered_sustained_row_count",
        "common_cause_row_count",
        "site_event_row_count",
        "group_off_row_count",
        "subgroup_common_cause_row_count",
        "max_co_drop_frac",
    ]
    for col in text_cols:
        out[col] = out[col].map(normalize_text)
    for col in flag_cols:
        out[col] = out[col].map(to_flag)
    for col in numeric_cols:
        out[col] = out[col].map(to_float)
    return out


def normalize_pressure(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=PRESSURE_COLS)
    require_columns(df, PRESSURE_COLS, "pressure input")
    out = df[PRESSURE_COLS].copy()
    text_cols = [
        "packet_case_id",
        "site",
        "panel_id",
        "packet_bucket",
        "counterexample_bucket",
        "evidence_grade",
        "raw_top1_ko",
        "raw_top2_ko",
        "raw_top3_ko",
    ]
    numeric_cols = ["raw_top1_score", "same_day_final_fault_row_count", "same_day_common_cause_row_count"]
    for col in text_cols:
        out[col] = out[col].map(normalize_text)
    for col in numeric_cols:
        out[col] = out[col].map(to_float)
    return out


def read_threshold_basis(path: Path) -> str:
    df = read_csv(path)
    require_columns(df, ["axis", "promote_candidate", "hold_or_block"], "threshold input")
    rows = []
    for row in df.to_dict(orient="records"):
        rows.append(
            f"{normalize_text(row['axis'])}: promote={normalize_text(row['promote_candidate'])}; "
            f"hold={normalize_text(row['hold_or_block'])}"
        )
    return " | ".join(rows)


def classify_criteria_role(action: str) -> str:
    action = normalize_text(action)
    if action.startswith("block_"):
        return "block_individual_precursor"
    if action.startswith("hold_"):
        return "hold_episode_only"
    if action.startswith("manual_review"):
        return "manual_review_candidate"
    if action.startswith("no_precursor"):
        return "strict_anchor_no_precursor"
    if action.startswith("shadow_subtype"):
        return "shadow_candidate_requires_two_axes"
    return "review_only"


def build_criteria(subtype_df: pd.DataFrame, threshold_basis: str) -> pd.DataFrame:
    require_columns(
        subtype_df,
        [
            "family_key",
            "family_label_ko",
            "subtype_key",
            "subtype_label_ko",
            "primary_signature_ko",
            "secondary_signature_ko",
            "negative_signature_ko",
            "minimum_evidence_shadow_ko",
            "recommended_shadow_action",
            "notes_ko",
        ],
        "subtype input",
    )
    rows: list[dict[str, object]] = []
    for row in subtype_df.to_dict(orient="records"):
        action = normalize_text(row["recommended_shadow_action"])
        rows.append(
            {
                "family_key": normalize_text(row["family_key"]),
                "family_label_ko": normalize_text(row["family_label_ko"]),
                "subtype_key": normalize_text(row["subtype_key"]),
                "subtype_label_ko": normalize_text(row["subtype_label_ko"]),
                "recommended_shadow_action": action,
                "candidate_judgment_role": classify_criteria_role(action),
                "minimum_evidence_shadow_ko": normalize_text(row["minimum_evidence_shadow_ko"]),
                "positive_axis_hint": " + ".join(
                    value
                    for value in [
                        normalize_text(row["primary_signature_ko"]),
                        normalize_text(row["secondary_signature_ko"]),
                    ]
                    if value
                ),
                "negative_signature_ko": normalize_text(row["negative_signature_ko"]),
                "threshold_basis": threshold_basis,
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
                "notes_ko": normalize_text(row["notes_ko"]),
            }
        )
    return pd.DataFrame(rows, columns=CRITERIA_COLS)


def family_track_from_label(label: str) -> tuple[str, str]:
    label = normalize_text(label)
    if "다이오드" in label or "서브스트링" in label:
        return "다이오드·서브스트링 계열", "diode_substring"
    if "접속" in label or "부분개방" in label or "개방" in label:
        return "접속 불량·부분 개방 계열", "open_connection_partial"
    if "센서" in label or "피드백" in label or "계측" in label:
        return "센서·피드백·계측 이상 계열", "measurement_feedback"
    if "열화" in label or "오염" in label or "음영" in label or "부분음영" in label:
        return "열화·오염·음영 계열", "degradation_soiling_shadow"
    if "공통" in label or "site" in label.lower() or "group" in label.lower():
        return "외부계통·공통원인 계열", "external_common_cause"
    return "unassigned_family_needs_shape_review", "unassigned_family_needs_shape_review"


def classify_packet_row(row: pd.Series) -> tuple[str, str, str, str, str]:
    pressure_case = normalize_text(row.get("packet_case_id"))
    raw_top1 = normalize_text(row.get("raw_top1_ko"))
    strong_common = to_flag(row.get("strong_common_cause_flag"))
    subgroup_context = to_flag(row.get("subgroup_or_breadth_context_flag"))
    local_or_weak = to_flag(row.get("local_or_weak_synchrony_flag"))
    recovery_pressure = to_flag(row.get("recovery_morphology_pressure_flag"))
    report_blocker = to_flag(row.get("report_entry_blocker_flag"))
    recovery_bucket = normalize_text(row.get("recovery_bucket"))
    synchrony_bucket = normalize_text(row.get("synchrony_bucket"))
    blocker = normalize_text(row.get("friction_blocker_types"))

    if pressure_case:
        family_label, family_track = family_track_from_label(raw_top1)
        return (
            "fault_family_regression_pressure_seed",
            family_label,
            family_track,
            "regression_pressure_only",
            "Use as a counterexample/regression seed only; do not promote or patch from this row.",
        )
    if strong_common:
        return (
            "block_individual_precursor_common_cause",
            "외부계통·공통원인 계열",
            "external_common_cause",
            "spatiality_blocks_panel_local_promotion",
            f"Strong synchrony `{synchrony_bucket}` must be separated before panel-local precursor reading.",
        )
    if subgroup_context:
        return (
            "hold_subgroup_or_breadth_context",
            "외부계통·공통원인 계열",
            "external_common_cause",
            "spatiality_context_hold",
            f"Subgroup/breadth context `{synchrony_bucket}` is context, not individual precursor proof.",
        )
    if recovery_pressure and local_or_weak:
        return (
            "local_morphology_family_candidate_review",
            "unassigned_family_needs_shape_review",
            "unassigned_family_needs_shape_review",
            "local_morphology_requires_family_shape",
            f"Recovery/recurrence pressure `{recovery_bucket}` is plausible, but family shape is still needed.",
        )
    if report_blocker:
        return (
            "report_lane_or_gap_boundary_review",
            "report_lane_boundary",
            "report_lane_boundary",
            "duration_gap_boundary_review",
            f"Report-entry or gap blocker remains visible: `{blocker}`.",
        )
    return (
        "weak_context_hold_review",
        "unassigned_family_needs_shape_review",
        "unassigned_family_needs_shape_review",
        "insufficient_axis_alignment",
        "Available axes do not yet align into a defensible family-specific threshold candidate.",
    )


def build_detail(cross_axis: pd.DataFrame, pressure: pd.DataFrame) -> pd.DataFrame:
    merged = cross_axis.merge(
        pressure,
        on=["site", "panel_id"],
        how="left",
        suffixes=("", "_pressure"),
    )
    for col in PRESSURE_COLS:
        if col in {"site", "panel_id"}:
            continue
        if col not in merged.columns:
            merged[col] = ""
        merged[col] = merged[col].fillna("")

    merged["duration_gap_axis_flag"] = (
        (merged["report_entry_blocker_flag"].map(to_flag) == 1)
        | (merged["friction_direct_row_count"].map(to_float) > 0)
        | (merged["friction_group_off_row_count"].map(to_float) > 0)
    ).astype(int)
    merged["continuity_recurrence_axis_flag"] = (
        (merged["recovery_morphology_pressure_flag"].map(to_flag) == 1)
        | (merged["re_drop_row_count"].map(to_float) > 0)
        | (merged["recovered_sustained_row_count"].map(to_float) > 0)
    ).astype(int)
    merged["spatiality_common_cause_axis_flag"] = (
        (merged["strong_common_cause_flag"].map(to_flag) == 1)
        | (merged["subgroup_or_breadth_context_flag"].map(to_flag) == 1)
        | (merged["common_cause_row_count"].map(to_float) > 0)
    ).astype(int)
    merged["candidate_evidence_axis_count"] = merged[
        ["duration_gap_axis_flag", "continuity_recurrence_axis_flag", "spatiality_common_cause_axis_flag"]
    ].sum(axis=1)

    classified = [classify_packet_row(row) for _, row in merged.iterrows()]
    merged[[
        "judgment_bucket",
        "candidate_family_label_ko",
        "candidate_family_track",
        "threshold_candidate_role",
        "required_next_evidence",
    ]] = pd.DataFrame(classified, index=merged.index)
    merged["operator_promotion_allowed_flag"] = 0
    merged["engine_patch_candidate_flag"] = 0
    merged["pressure_packet_case_id"] = merged["packet_case_id"].map(normalize_text)
    merged["pressure_packet_bucket"] = merged["packet_bucket"].map(normalize_text)
    merged["pressure_counterexample_bucket"] = merged["counterexample_bucket"].map(normalize_text)
    merged["pressure_evidence_grade"] = merged["evidence_grade"].map(normalize_text)
    merged["review_note"] = (
        "bucket="
        + merged["judgment_bucket"].map(normalize_text)
        + "; family_track="
        + merged["candidate_family_track"].map(normalize_text)
        + "; promotion=0; engine_patch=0"
    )
    merged = merged.sort_values(["judgment_bucket", "site", "panel_id"], kind="stable").reset_index(drop=True)
    merged["candidate_case_id"] = [f"BR064-{idx:03d}" for idx in range(1, len(merged) + 1)]
    return merged.reindex(columns=DETAIL_COLS)


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary = (
        detail.groupby(["judgment_bucket", "candidate_family_label_ko", "site"], dropna=False)
        .agg(
            cases=("candidate_case_id", "nunique"),
            pressure_seed_cases=("pressure_packet_case_id", lambda s: int(s.map(normalize_text).ne("").sum())),
            duration_gap_axis_cases=("duration_gap_axis_flag", "sum"),
            continuity_recurrence_axis_cases=("continuity_recurrence_axis_flag", "sum"),
            spatiality_common_cause_axis_cases=("spatiality_common_cause_axis_flag", "sum"),
            strong_common_cause_cases=("synchrony_bucket", lambda s: int(s.isin(["site_event_synchrony", "group_off_synchrony", "prefault_B_common_cause_overlap"]).sum())),
            operator_promotion_allowed_sum=("operator_promotion_allowed_flag", "sum"),
            engine_patch_candidate_sum=("engine_patch_candidate_flag", "sum"),
        )
        .reset_index()
    )
    return summary.reindex(columns=SUMMARY_COLS).sort_values(["judgment_bucket", "site", "candidate_family_label_ko"])


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int = 40) -> str:
    if df.empty:
        return "_No rows._"
    small = df.head(max_rows).copy()
    header = "| " + " | ".join(small.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(small.columns)) + " |"
    rows = [
        "| " + " | ".join(normalize_text(row[col]) for col in small.columns) + " |"
        for row in small.to_dict(orient="records")
    ]
    if len(df) > max_rows:
        rows.append(f"| ... | truncated {len(df) - max_rows} rows |" + " |" * (len(small.columns) - 2))
    return "\n".join([header, separator] + rows)


def write_note(
    output_dir: Path,
    detail: pd.DataFrame,
    summary: pd.DataFrame,
    criteria: pd.DataFrame,
    input_manifest_path: Path | None = None,
    input_resolution_sources: dict[str, str] | None = None,
) -> None:
    lines = [
        "# panel_day_engine_fault_family_judgment_candidate_note_v1",
        "",
        "## Purpose",
        "- Build an audit-only packet for choosing fault-family judgment criteria before any larger engine semantic patch.",
        "- Keep duration/gap, continuity/recurrence, and spatiality/common-cause axes separate.",
        "- Do not claim performance improvement, operator promotion, or engine patch readiness from this packet.",
        "",
        "## Guardrails",
        f"- detail rows: `{len(detail)}`",
        f"- criteria rows: `{len(criteria)}`",
        f"- operator promotion allowed sum: `{int(detail['operator_promotion_allowed_flag'].sum()) if len(detail) else 0}`",
        f"- engine patch candidate sum: `{int(detail['engine_patch_candidate_flag'].sum()) if len(detail) else 0}`",
        f"- evidence input manifest: `{input_manifest_path if input_manifest_path else 'not provided'}`",
        "",
        "## Summary",
        dataframe_to_markdown(summary),
        "",
        "## Input Resolution Sources",
        *(
            [f"- `{key}`: `{value}`" for key, value in sorted((input_resolution_sources or {}).items())]
            if input_resolution_sources
            else ["- no manifest-wrapped inputs"]
        ),
        "",
        "## Interpretation",
        "- `fault_family_regression_pressure_seed` rows are regression/counterexample material only.",
        "- `block_individual_precursor_common_cause` and `hold_subgroup_or_breadth_context` must be handled before panel-local precursor promotion.",
        "- `local_morphology_family_candidate_review` is the useful next inspect pool, but still requires family shape evidence before thresholding.",
        "- This packet is not a production verdict and does not modify `panel_day_engine.py`.",
    ]
    (output_dir / NOTE_OUTPUT_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    base_root = Path.cwd()
    input_manifest_path, input_manifest = load_input_manifest(base_root, args.input_manifest)
    argv = sys.argv[1:]
    explicit_flags = {
        flag
        for flag in [
            "--cross-axis-input",
            "--pressure-input",
        ]
        if cli_flag_provided(flag, argv)
    }
    cross_axis_path, cross_axis_source = resolve_chain_input(
        base_root,
        args.cross_axis_input,
        DEFAULT_CROSS_AXIS_INPUT,
        input_manifest,
        "cross_axis_input",
        "--cross-axis-input",
        explicit_flags,
    )
    pressure_path, pressure_source = resolve_chain_input(
        base_root,
        args.pressure_input,
        DEFAULT_PRESSURE_INPUT,
        input_manifest,
        "pressure_input",
        "--pressure-input",
        explicit_flags,
    )
    input_resolution_sources = {
        "cross_axis_input": cross_axis_source,
        "pressure_input": pressure_source,
    }

    cross_axis = normalize_cross_axis(read_csv(cross_axis_path))
    pressure = normalize_pressure(read_csv(pressure_path, required=False))
    threshold_basis = read_threshold_basis(args.threshold_input)
    subtype_df = read_csv(args.subtype_input)

    criteria = build_criteria(subtype_df, threshold_basis)
    detail = build_detail(cross_axis, pressure)
    summary = build_summary(detail)

    promotion_sum = int(detail["operator_promotion_allowed_flag"].sum()) if len(detail) else 0
    engine_patch_sum = int(detail["engine_patch_candidate_flag"].sum()) if len(detail) else 0
    if promotion_sum != 0 or engine_patch_sum != 0:
        raise SystemExit("fault-family judgment packet must remain review-only")

    detail.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    criteria.to_csv(args.output_dir / CRITERIA_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_note(args.output_dir, detail, summary, criteria, input_manifest_path, input_resolution_sources)


if __name__ == "__main__":
    main()
