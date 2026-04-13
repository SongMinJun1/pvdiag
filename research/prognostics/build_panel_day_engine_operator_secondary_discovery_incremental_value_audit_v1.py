#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import build_panel_day_engine_run_ranker_v2_holdout_audit as holdout_base

ATTENTION_NAME = "panel_day_engine_operator_attention_now_v1.csv"
SECONDARY_VALUE_PANELS_NAME = "panel_day_engine_operator_secondary_discovery_value_panels_v1.csv"

CASES_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_incremental_value_cases_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_incremental_value_summary_v1.csv"

PANEL_KEY_COLS = ["site", "panel_id"]
ATTENTION_FAULT_COL = "attention_any_future_fault_linked_ref_flag"
ATTENTION_TRUTH_COL = "attention_any_future_truth_linked_ref_flag"
SECONDARY_FAULT_COL = "any_future_fault_linked_ref_flag"
SECONDARY_TRUTH_COL = "any_future_truth_linked_ref_flag"

REQUIRED_ATTENTION_COLS = [*PANEL_KEY_COLS, ATTENTION_FAULT_COL, ATTENTION_TRUTH_COL]
REQUIRED_SECONDARY_COLS = [*PANEL_KEY_COLS, SECONDARY_FAULT_COL, SECONDARY_TRUTH_COL]

INTERNAL_CASE_COLS = [
    *PANEL_KEY_COLS,
    "in_baseline_attention_flag",
    "in_secondary_value_flag",
    "panel_set_class",
    ATTENTION_FAULT_COL,
    ATTENTION_TRUTH_COL,
    SECONDARY_FAULT_COL,
    SECONDARY_TRUTH_COL,
    "future_fault_linked_ref_flag",
    "future_truth_linked_ref_flag",
    "incremental_value_flag",
    "incremental_reason_ko",
]

CASE_OUTPUT_COLS = [
    "site",
    "panel_id",
    "in_baseline_attention_flag",
    "in_secondary_value_flag",
    "panel_set_class",
    "future_fault_linked_ref_flag",
    "future_truth_linked_ref_flag",
    "incremental_value_flag",
    "incremental_reason_ko",
]

SUMMARY_COLS = [
    "record_type",
    "site",
    "baseline_panel_count",
    "baseline_future_fault_linked_ref_panel_count",
    "baseline_future_truth_linked_ref_panel_count",
    "secondary_value_panel_count",
    "secondary_value_future_fault_linked_ref_panel_count",
    "secondary_value_future_truth_linked_ref_panel_count",
    "union_panel_count",
    "union_future_fault_linked_ref_panel_count",
    "union_future_truth_linked_ref_panel_count",
    "incremental_fault_or_truth_linked_panel_count",
    "incremental_fault_or_truth_linked_panel_rate_over_secondary",
    "incremental_fault_or_truth_linked_panel_rate_over_union",
    "overlap_panel_count",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure the incremental retrospective panel-level value of the secondary discovery value lane."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the project root.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def normalize_panel_keys(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["site"] = out["site"].map(holdout_base.normalize_text)
    out["panel_id"] = out["panel_id"].map(holdout_base.normalize_text)
    return out


def normalize_flag_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).gt(0).astype(int)


def load_baseline_attention(root: Path) -> pd.DataFrame:
    path = root / "_share" / ATTENTION_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_ATTENTION_COLS, path.name)
    df = normalize_panel_keys(df)
    df[ATTENTION_FAULT_COL] = normalize_flag_series(df[ATTENTION_FAULT_COL])
    df[ATTENTION_TRUTH_COL] = normalize_flag_series(df[ATTENTION_TRUTH_COL])
    grouped = (
        df.groupby(PANEL_KEY_COLS, dropna=False, as_index=False)
        .agg(
            {
                ATTENTION_FAULT_COL: "max",
                ATTENTION_TRUTH_COL: "max",
            }
        )
        .reset_index(drop=True)
    )
    grouped["in_baseline_attention_flag"] = 1
    return grouped.loc[:, [*PANEL_KEY_COLS, "in_baseline_attention_flag", ATTENTION_FAULT_COL, ATTENTION_TRUTH_COL]]


def load_secondary_value_panels(root: Path) -> pd.DataFrame:
    path = root / "_share" / SECONDARY_VALUE_PANELS_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_SECONDARY_COLS, path.name)
    df = normalize_panel_keys(df)
    df[SECONDARY_FAULT_COL] = normalize_flag_series(df[SECONDARY_FAULT_COL])
    df[SECONDARY_TRUTH_COL] = normalize_flag_series(df[SECONDARY_TRUTH_COL])
    grouped = (
        df.groupby(PANEL_KEY_COLS, dropna=False, as_index=False)
        .agg(
            {
                SECONDARY_FAULT_COL: "max",
                SECONDARY_TRUTH_COL: "max",
            }
        )
        .reset_index(drop=True)
    )
    grouped["in_secondary_value_flag"] = 1
    return grouped.loc[:, [*PANEL_KEY_COLS, "in_secondary_value_flag", SECONDARY_FAULT_COL, SECONDARY_TRUTH_COL]]


def panel_set_class(row: pd.Series) -> str:
    if int(row["in_baseline_attention_flag"]) == 1 and int(row["in_secondary_value_flag"]) == 1:
        return "in_both"
    if int(row["in_baseline_attention_flag"]) == 1:
        return "baseline_only"
    return "secondary_only"


def incremental_reason(row: pd.Series) -> str:
    if int(row["incremental_value_flag"]) == 1:
        return "baseline attention에 없는 secondary value panel이며 retrospective fault/truth reference가 있어 incremental value가 확인됨"
    if str(row["panel_set_class"]) == "secondary_only":
        return "secondary value panel이지만 retrospective fault/truth reference가 없어 incremental value는 제한적이다"
    if str(row["panel_set_class"]) == "in_both":
        return "baseline attention과 secondary value lane이 모두 포착한 panel이다"
    return "current operator attention baseline에만 포함된 panel이다"


def build_case_table(baseline_df: pd.DataFrame, secondary_df: pd.DataFrame) -> pd.DataFrame:
    merged = baseline_df.merge(
        secondary_df,
        on=PANEL_KEY_COLS,
        how="outer",
        validate="one_to_one",
    )
    for col in [
        "in_baseline_attention_flag",
        "in_secondary_value_flag",
        ATTENTION_FAULT_COL,
        ATTENTION_TRUTH_COL,
        SECONDARY_FAULT_COL,
        SECONDARY_TRUTH_COL,
    ]:
        merged[col] = normalize_flag_series(merged[col])
    merged["panel_set_class"] = merged.apply(panel_set_class, axis=1)
    merged["future_fault_linked_ref_flag"] = merged[[ATTENTION_FAULT_COL, SECONDARY_FAULT_COL]].max(axis=1).astype(int)
    merged["future_truth_linked_ref_flag"] = merged[[ATTENTION_TRUTH_COL, SECONDARY_TRUTH_COL]].max(axis=1).astype(int)
    merged["incremental_value_flag"] = (
        merged["in_secondary_value_flag"].eq(1)
        & merged["in_baseline_attention_flag"].eq(0)
        & (
            merged["future_fault_linked_ref_flag"].eq(1)
            | merged["future_truth_linked_ref_flag"].eq(1)
        )
    ).astype(int)
    merged["incremental_reason_ko"] = merged.apply(incremental_reason, axis=1)
    merged = merged.sort_values(PANEL_KEY_COLS, ascending=[True, True], kind="mergesort").reset_index(drop=True)
    return merged.loc[:, INTERNAL_CASE_COLS].copy()


def safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return float(numerator) / float(denominator)


def build_summary(case_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def summarize(site: str, record_type: str) -> None:
        if record_type == "overall":
            subset = case_df.copy()
        else:
            subset = case_df.loc[case_df["site"].eq(site)].copy()
        baseline_subset = subset.loc[subset["in_baseline_attention_flag"].eq(1)].copy()
        secondary_subset = subset.loc[subset["in_secondary_value_flag"].eq(1)].copy()
        overlap_count = int(
            subset["in_baseline_attention_flag"].eq(1).mul(subset["in_secondary_value_flag"].eq(1)).sum()
        )
        incremental_count = int(subset["incremental_value_flag"].sum())
        rows.append(
            {
                "record_type": record_type,
                "site": site,
                "baseline_panel_count": int(len(baseline_subset)),
                "baseline_future_fault_linked_ref_panel_count": int(baseline_subset[ATTENTION_FAULT_COL].sum()),
                "baseline_future_truth_linked_ref_panel_count": int(baseline_subset[ATTENTION_TRUTH_COL].sum()),
                "secondary_value_panel_count": int(len(secondary_subset)),
                "secondary_value_future_fault_linked_ref_panel_count": int(secondary_subset[SECONDARY_FAULT_COL].sum()),
                "secondary_value_future_truth_linked_ref_panel_count": int(secondary_subset[SECONDARY_TRUTH_COL].sum()),
                "union_panel_count": int(len(subset)),
                "union_future_fault_linked_ref_panel_count": int(subset["future_fault_linked_ref_flag"].sum()),
                "union_future_truth_linked_ref_panel_count": int(subset["future_truth_linked_ref_flag"].sum()),
                "incremental_fault_or_truth_linked_panel_count": incremental_count,
                "incremental_fault_or_truth_linked_panel_rate_over_secondary": safe_rate(
                    incremental_count,
                    int(len(secondary_subset)),
                ),
                "incremental_fault_or_truth_linked_panel_rate_over_union": safe_rate(
                    incremental_count,
                    int(len(subset)),
                ),
                "overlap_panel_count": overlap_count,
                "note_ko": "secondary discovery value-panel lane가 current operator attention baseline 대비 panel-level retrospective coverage를 얼마나 더 보태는지 요약",
            }
        )

    summarize("", "overall")
    for site in sorted(case_df["site"].dropna().map(holdout_base.normalize_text).unique()):
        summarize(site, "site")
    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def save_outputs(root: Path, case_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    case_df.loc[:, CASE_OUTPUT_COLS].to_csv(share_dir / CASES_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    baseline_df = load_baseline_attention(root)
    secondary_df = load_secondary_value_panels(root)
    case_df = build_case_table(baseline_df, secondary_df)
    summary_df = build_summary(case_df)
    save_outputs(root, case_df, summary_df)


if __name__ == "__main__":
    main()
