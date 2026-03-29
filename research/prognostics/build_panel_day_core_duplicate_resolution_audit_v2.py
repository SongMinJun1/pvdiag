#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
KEY_COLS = ["site", "panel_id", "date"]
BASE_EVIDENCE_CRITICAL_COLS = {
    "coverage_mid",
    "mid_ratio",
    "last_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "v_drop",
    "shadow_like",
    "group_off_like",
    "group_key_base",
}
PROVENANCE_HINTS = [
    "source",
    "file",
    "path",
    "ingest",
    "export",
    "created",
    "updated",
    "modified",
]
ABS_TOL = 1e-6
SUMMARY_COLS = [
    "record_type",
    "site",
    "total_row_count",
    "row_count",
    "duplicate_group_count",
    "duplicate_row_count",
    "provenance_only_duplicate_count",
    "evidence_equivalent_duplicate_count",
    "numeric_jitter_duplicate_count",
    "material_conflict_duplicate_count",
]
GROUP_COLS = [
    "duplicate_group_index",
    "site",
    "panel_id",
    "date",
    "duplicate_row_count",
    "provenance_diff_column_count",
    "auxiliary_diff_column_count",
    "critical_diff_column_count",
    "max_abs_diff_critical_numeric",
    "differing_critical_columns",
    "resolution_class",
    "recommended_handling",
]
CRITICAL_DIFF_COLS = [
    "duplicate_group_index",
    "site",
    "panel_id",
    "date",
    "field_name",
    "field_kind",
    "values_seen",
    "min_numeric_value",
    "max_numeric_value",
    "abs_range",
    "diff_severity",
]
REQUIRED_CORE_COLS = ["panel_id", "date"]
RESOLUTION_TO_HANDLING = {
    "provenance_only_duplicate": "safe_drop_provenance_copy",
    "evidence_equivalent_duplicate": "safe_keep_one_after_equivalence_check",
    "numeric_jitter_duplicate": "review_tolerance_before_dedupe",
    "material_conflict_duplicate": "upstream_or_rule_fix_required",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refine panel_day_core duplicate analysis using evidence-matrix-aware comparison tiers."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    parser.add_argument(
        "--sites",
        nargs="*",
        default=SITES,
        help="Sites to inspect. Defaults to the stable known sites.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def load_site_core(root: Path, site: str) -> tuple[pd.DataFrame, list[str]]:
    path = root / "data" / site / "out" / "panel_day_core.csv"
    df = read_csv(path)
    ensure_columns(df, REQUIRED_CORE_COLS, f"{site}/panel_day_core.csv")

    original_cols = list(df.columns)
    df = df.copy()
    df.insert(0, "site", site)
    df["_raw_row_order"] = range(len(df))
    df["panel_id"] = df["panel_id"].map(normalize_text)
    df["date"] = df["date"].map(normalize_text)
    return df, original_cols


def is_evidence_critical_col(col: str) -> bool:
    lower = col.lower()
    if lower in BASE_EVIDENCE_CRITICAL_COLS:
        return True
    if "shape" in lower:
        return True
    if "instability" in lower:
        return True
    return False


def is_provenance_col(col: str) -> bool:
    lower = col.lower()
    if lower == "date":
        return False
    return any(token in lower for token in PROVENANCE_HINTS)


def classify_columns(original_cols: list[str]) -> tuple[list[str], list[str], list[str]]:
    evidence_critical: list[str] = []
    provenance: list[str] = []
    auxiliary: list[str] = []
    for col in original_cols:
        if col in {"site", "panel_id", "date"}:
            continue
        if is_evidence_critical_col(col):
            evidence_critical.append(col)
        elif is_provenance_col(col):
            provenance.append(col)
        else:
            auxiliary.append(col)
    return evidence_critical, provenance, auxiliary


def detect_field_kind(series: pd.Series) -> str:
    normalized = series.map(normalize_text)
    nonblank = normalized.loc[normalized.ne("")]
    if nonblank.empty:
        return "categorical"
    numeric = pd.to_numeric(nonblank, errors="coerce")
    return "numeric" if numeric.notna().all() else "categorical"


def stable_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def analyze_group_column(group_df: pd.DataFrame, col: str) -> dict[str, object]:
    raw_values = group_df[col] if col in group_df.columns else pd.Series([pd.NA] * len(group_df), index=group_df.index)
    normalized = raw_values.map(normalize_text)
    field_kind = detect_field_kind(raw_values)

    if field_kind == "numeric":
        numeric_values = pd.to_numeric(normalized.replace("", pd.NA), errors="coerce")
        normalized_compare = numeric_values.map(lambda value: "" if pd.isna(value) else f"{float(value):.12g}")
        differing = normalized_compare.nunique(dropna=False) > 1
        min_numeric_value = numeric_values.min(skipna=True)
        max_numeric_value = numeric_values.max(skipna=True)
        if pd.notna(min_numeric_value) and pd.notna(max_numeric_value):
            abs_range = float(max_numeric_value - min_numeric_value)
        else:
            abs_range = pd.NA
        missingness_diff = normalized.eq("").any() and normalized.ne("").any()
        if not differing:
            diff_severity = "none"
        elif missingness_diff:
            diff_severity = "material"
        elif pd.notna(abs_range) and abs_range > ABS_TOL:
            diff_severity = "material"
        elif pd.notna(abs_range) and abs_range > 0:
            diff_severity = "jitter"
        else:
            diff_severity = "none"
        values_seen = "|".join(stable_unique(normalized_compare.astype(str).tolist()))
        return {
            "field_name": col,
            "field_kind": field_kind,
            "differing": bool(differing),
            "values_seen": values_seen,
            "min_numeric_value": min_numeric_value if pd.notna(min_numeric_value) else pd.NA,
            "max_numeric_value": max_numeric_value if pd.notna(max_numeric_value) else pd.NA,
            "abs_range": abs_range,
            "diff_severity": diff_severity,
        }

    differing = normalized.nunique(dropna=False) > 1
    values_seen = "|".join(stable_unique(normalized.astype(str).tolist()))
    return {
        "field_name": col,
        "field_kind": field_kind,
        "differing": bool(differing),
        "values_seen": values_seen,
        "min_numeric_value": pd.NA,
        "max_numeric_value": pd.NA,
        "abs_range": pd.NA,
        "diff_severity": "material" if differing else "none",
    }


def classify_resolution(
    critical_diffs: list[dict[str, object]],
    provenance_diff_cols: list[str],
    auxiliary_diff_cols: list[str],
) -> tuple[str, float]:
    critical_diff_count = len(critical_diffs)
    max_abs_diff = 0.0
    if critical_diffs:
        numeric_ranges = [
            float(diff["abs_range"])
            for diff in critical_diffs
            if diff["field_kind"] == "numeric" and pd.notna(diff["abs_range"])
        ]
        if numeric_ranges:
            max_abs_diff = max(numeric_ranges)

    if critical_diff_count == 0:
        if not auxiliary_diff_cols:
            return "provenance_only_duplicate", max_abs_diff
        return "evidence_equivalent_duplicate", max_abs_diff

    critical_categorical_material = any(
        diff["field_kind"] == "categorical" and diff["diff_severity"] == "material"
        for diff in critical_diffs
    )
    critical_numeric_material = any(
        diff["field_kind"] == "numeric" and diff["diff_severity"] == "material"
        for diff in critical_diffs
    )
    critical_numeric_jitter = any(
        diff["field_kind"] == "numeric" and diff["diff_severity"] == "jitter"
        for diff in critical_diffs
    )
    if not critical_categorical_material and not critical_numeric_material and critical_numeric_jitter:
        return "numeric_jitter_duplicate", max_abs_diff
    return "material_conflict_duplicate", max_abs_diff


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    site_frames: list[pd.DataFrame] = []
    original_cols: list[str] = []
    for site in sites:
        site_df, site_original_cols = load_site_core(root, site)
        site_frames.append(site_df)
        for col in site_original_cols:
            if col not in original_cols:
                original_cols.append(col)

    all_rows = pd.concat(site_frames, ignore_index=True, sort=False) if site_frames else pd.DataFrame(columns=["site"] + original_cols)
    duplicate_mask = all_rows.duplicated(subset=KEY_COLS, keep=False)
    duplicate_rows = all_rows.loc[duplicate_mask].copy()

    evidence_critical_cols, provenance_cols, auxiliary_cols = classify_columns(original_cols)
    group_rows: list[dict[str, object]] = []
    critical_diff_rows: list[dict[str, object]] = []

    if not duplicate_rows.empty:
        grouped = duplicate_rows.groupby(KEY_COLS, sort=True, dropna=False)
        for duplicate_group_index, (key, group_df) in enumerate(grouped, start=1):
            site, panel_id, date = key

            critical_analyses = [analyze_group_column(group_df, col) for col in evidence_critical_cols]
            provenance_analyses = [analyze_group_column(group_df, col) for col in provenance_cols]
            auxiliary_analyses = [analyze_group_column(group_df, col) for col in auxiliary_cols]

            critical_diffs = [analysis for analysis in critical_analyses if analysis["differing"]]
            provenance_diff_cols = [analysis["field_name"] for analysis in provenance_analyses if analysis["differing"]]
            auxiliary_diff_cols = [analysis["field_name"] for analysis in auxiliary_analyses if analysis["differing"]]

            resolution_class, max_abs_diff = classify_resolution(
                critical_diffs,
                provenance_diff_cols,
                auxiliary_diff_cols,
            )
            recommended_handling = RESOLUTION_TO_HANDLING[resolution_class]
            differing_critical_columns = [str(analysis["field_name"]) for analysis in critical_diffs]

            group_rows.append(
                {
                    "duplicate_group_index": duplicate_group_index,
                    "site": site,
                    "panel_id": panel_id,
                    "date": date,
                    "duplicate_row_count": int(len(group_df)),
                    "provenance_diff_column_count": int(len(provenance_diff_cols)),
                    "auxiliary_diff_column_count": int(len(auxiliary_diff_cols)),
                    "critical_diff_column_count": int(len(critical_diffs)),
                    "max_abs_diff_critical_numeric": round(float(max_abs_diff), 12),
                    "differing_critical_columns": "|".join(differing_critical_columns),
                    "resolution_class": resolution_class,
                    "recommended_handling": recommended_handling,
                }
            )

            for analysis in critical_diffs:
                critical_diff_rows.append(
                    {
                        "duplicate_group_index": duplicate_group_index,
                        "site": site,
                        "panel_id": panel_id,
                        "date": date,
                        "field_name": analysis["field_name"],
                        "field_kind": analysis["field_kind"],
                        "values_seen": analysis["values_seen"],
                        "min_numeric_value": analysis["min_numeric_value"],
                        "max_numeric_value": analysis["max_numeric_value"],
                        "abs_range": analysis["abs_range"],
                        "diff_severity": analysis["diff_severity"],
                    }
                )

    groups_output = pd.DataFrame(group_rows, columns=GROUP_COLS)
    critical_diffs_output = pd.DataFrame(critical_diff_rows, columns=CRITICAL_DIFF_COLS)

    summary_rows: list[dict[str, object]] = [
        {
            "record_type": "summary",
            "site": "",
            "total_row_count": int(len(all_rows)),
            "row_count": pd.NA,
            "duplicate_group_count": int(len(groups_output)),
            "duplicate_row_count": int(len(duplicate_rows)),
            "provenance_only_duplicate_count": int(groups_output["resolution_class"].eq("provenance_only_duplicate").sum()) if not groups_output.empty else 0,
            "evidence_equivalent_duplicate_count": int(groups_output["resolution_class"].eq("evidence_equivalent_duplicate").sum()) if not groups_output.empty else 0,
            "numeric_jitter_duplicate_count": int(groups_output["resolution_class"].eq("numeric_jitter_duplicate").sum()) if not groups_output.empty else 0,
            "material_conflict_duplicate_count": int(groups_output["resolution_class"].eq("material_conflict_duplicate").sum()) if not groups_output.empty else 0,
        }
    ]

    for site in sites:
        site_rows = all_rows.loc[all_rows["site"].eq(site)]
        site_groups = groups_output.loc[groups_output["site"].eq(site)] if not groups_output.empty else groups_output
        site_duplicate_rows = duplicate_rows.loc[duplicate_rows["site"].eq(site)] if not duplicate_rows.empty else duplicate_rows
        summary_rows.append(
            {
                "record_type": "site",
                "site": site,
                "total_row_count": pd.NA,
                "row_count": int(len(site_rows)),
                "duplicate_group_count": int(len(site_groups)),
                "duplicate_row_count": int(len(site_duplicate_rows)),
                "provenance_only_duplicate_count": int(site_groups["resolution_class"].eq("provenance_only_duplicate").sum()) if not site_groups.empty else 0,
                "evidence_equivalent_duplicate_count": int(site_groups["resolution_class"].eq("evidence_equivalent_duplicate").sum()) if not site_groups.empty else 0,
                "numeric_jitter_duplicate_count": int(site_groups["resolution_class"].eq("numeric_jitter_duplicate").sum()) if not site_groups.empty else 0,
                "material_conflict_duplicate_count": int(site_groups["resolution_class"].eq("material_conflict_duplicate").sum()) if not site_groups.empty else 0,
            }
        )

    summary_output = pd.DataFrame(summary_rows, columns=SUMMARY_COLS)
    return summary_output, groups_output, critical_diffs_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_output, groups_output, critical_diffs_output = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_output.to_csv(out_dir / "panel_day_core_duplicate_resolution_summary_v2.csv", index=False, encoding="utf-8-sig")
    groups_output.to_csv(out_dir / "panel_day_core_duplicate_resolution_groups_v2.csv", index=False, encoding="utf-8-sig")
    critical_diffs_output.to_csv(out_dir / "panel_day_core_duplicate_resolution_critical_diffs_v2.csv", index=False, encoding="utf-8-sig")
    print(
        "panel_day_core_duplicate_resolution_summary_v2="
        f"{len(summary_output)} panel_day_core_duplicate_resolution_groups_v2={len(groups_output)} "
        f"panel_day_core_duplicate_resolution_critical_diffs_v2={len(critical_diffs_output)}"
    )


if __name__ == "__main__":
    main()
