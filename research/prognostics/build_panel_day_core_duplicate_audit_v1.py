#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
KEY_COLS = ["site", "panel_id", "date"]
SUMMARY_COLS = [
    "record_type",
    "site",
    "total_row_count",
    "row_count",
    "duplicate_group_count",
    "duplicate_row_count",
    "exact_duplicate_group_count",
    "conflicting_duplicate_group_count",
]
GROUP_COLS = [
    "duplicate_group_index",
    "site",
    "panel_id",
    "date",
    "duplicate_row_count",
    "duplicate_group_type",
    "differing_column_count",
    "differing_columns",
    "recommended_handling",
]
REQUIRED_CORE_COLS = ["panel_id", "date"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit duplicate raw panel_day_core keys before choosing any dedupe or normalization policy."
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


def normalize_compare_value(value: object) -> str:
    text = normalize_text(value)
    if text == "":
        return ""
    numeric = pd.to_numeric(pd.Series([text]), errors="coerce").iloc[0]
    if pd.notna(numeric):
        return f"{float(numeric):.12g}"
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


def find_differing_columns(group_df: pd.DataFrame, compare_cols: list[str]) -> list[str]:
    differing: list[str] = []
    for col in compare_cols:
        normalized_values = group_df[col].map(normalize_compare_value)
        if normalized_values.nunique(dropna=False) > 1:
            differing.append(col)
    return differing


def classify_duplicate_groups(
    all_rows: pd.DataFrame,
    original_cols: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    duplicate_mask = all_rows.duplicated(subset=KEY_COLS, keep=False)
    duplicate_rows = all_rows.loc[duplicate_mask].copy()
    if duplicate_rows.empty:
        empty_groups = pd.DataFrame(columns=GROUP_COLS)
        empty_rows = pd.DataFrame(
            columns=[
                "site",
                "panel_id",
                "date",
                "duplicate_group_index",
                "duplicate_group_type",
            ]
            + [col for col in original_cols if col not in {"site", "panel_id", "date"}]
        )
        return empty_groups, empty_rows

    compare_cols = [col for col in original_cols if col not in {"panel_id", "date", "site"}]
    group_rows: list[dict[str, object]] = []
    duplicate_frames: list[pd.DataFrame] = []

    grouped = duplicate_rows.groupby(KEY_COLS, sort=True, dropna=False)
    for duplicate_group_index, (key, group_df) in enumerate(grouped, start=1):
        site, panel_id, date = key
        differing_columns = find_differing_columns(group_df, compare_cols)
        duplicate_group_type = "exact_duplicate_group" if not differing_columns else "conflicting_duplicate_group"
        recommended_handling = (
            "safe_dedupe_candidate"
            if duplicate_group_type == "exact_duplicate_group"
            else "requires_rule_or_upstream_fix"
        )
        group_rows.append(
            {
                "duplicate_group_index": duplicate_group_index,
                "site": site,
                "panel_id": panel_id,
                "date": date,
                "duplicate_row_count": int(len(group_df)),
                "duplicate_group_type": duplicate_group_type,
                "differing_column_count": int(len(differing_columns)),
                "differing_columns": "|".join(differing_columns),
                "recommended_handling": recommended_handling,
            }
        )

        row_df = group_df.copy()
        row_df.insert(3, "duplicate_group_index", duplicate_group_index)
        row_df.insert(4, "duplicate_group_type", duplicate_group_type)
        duplicate_frames.append(row_df)

    groups_output = pd.DataFrame(group_rows, columns=GROUP_COLS)
    rows_output = pd.concat(duplicate_frames, ignore_index=True, sort=False)
    rows_output = rows_output.sort_values(["duplicate_group_index", "_raw_row_order"], ascending=[True, True]).reset_index(drop=True)

    keep_original_cols = [col for col in original_cols if col not in {"site", "panel_id", "date"}]
    rows_output = rows_output.loc[
        :,
        ["site", "panel_id", "date", "duplicate_group_index", "duplicate_group_type"] + keep_original_cols,
    ].copy()
    return groups_output, rows_output


def build_summary_output(all_rows: pd.DataFrame, groups_output: pd.DataFrame, rows_output: pd.DataFrame, sites: list[str]) -> pd.DataFrame:
    summary_rows: list[dict[str, object]] = [
        {
            "record_type": "summary",
            "site": "",
            "total_row_count": int(len(all_rows)),
            "row_count": pd.NA,
            "duplicate_group_count": int(len(groups_output)),
            "duplicate_row_count": int(len(rows_output)),
            "exact_duplicate_group_count": int(groups_output["duplicate_group_type"].eq("exact_duplicate_group").sum()) if not groups_output.empty else 0,
            "conflicting_duplicate_group_count": int(groups_output["duplicate_group_type"].eq("conflicting_duplicate_group").sum()) if not groups_output.empty else 0,
        }
    ]

    for site in sites:
        site_rows = all_rows.loc[all_rows["site"].eq(site)]
        site_groups = groups_output.loc[groups_output["site"].eq(site)] if not groups_output.empty else groups_output
        site_dup_rows = rows_output.loc[rows_output["site"].eq(site)] if not rows_output.empty else rows_output
        summary_rows.append(
            {
                "record_type": "site",
                "site": site,
                "total_row_count": pd.NA,
                "row_count": int(len(site_rows)),
                "duplicate_group_count": int(len(site_groups)),
                "duplicate_row_count": int(len(site_dup_rows)),
                "exact_duplicate_group_count": int(site_groups["duplicate_group_type"].eq("exact_duplicate_group").sum()) if not site_groups.empty else 0,
                "conflicting_duplicate_group_count": int(site_groups["duplicate_group_type"].eq("conflicting_duplicate_group").sum()) if not site_groups.empty else 0,
            }
        )

    return pd.DataFrame(summary_rows, columns=SUMMARY_COLS)


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
    groups_output, rows_output = classify_duplicate_groups(all_rows, original_cols)
    summary_output = build_summary_output(all_rows, groups_output, rows_output, sites)
    return summary_output, groups_output, rows_output


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary_output, groups_output, rows_output = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_output.to_csv(out_dir / "panel_day_core_duplicate_audit_summary_v1.csv", index=False, encoding="utf-8-sig")
    groups_output.to_csv(out_dir / "panel_day_core_duplicate_groups_v1.csv", index=False, encoding="utf-8-sig")
    rows_output.to_csv(out_dir / "panel_day_core_duplicate_rows_v1.csv", index=False, encoding="utf-8-sig")
    print(
        "panel_day_core_duplicate_audit_summary_v1="
        f"{len(summary_output)} panel_day_core_duplicate_groups_v1={len(groups_output)} "
        f"panel_day_core_duplicate_rows_v1={len(rows_output)}"
    )


if __name__ == "__main__":
    main()
