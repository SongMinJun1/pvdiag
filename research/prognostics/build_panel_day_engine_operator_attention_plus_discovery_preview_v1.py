#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import build_panel_day_engine_run_ranker_v2_holdout_audit as holdout_base

ATTENTION_NOW_NAME = "panel_day_engine_operator_attention_now_v1.csv"
SECONDARY_VALUE_PANELS_NAME = "panel_day_engine_operator_secondary_discovery_value_panels_v1.csv"

PREVIEW_OUTPUT_NAME = "panel_day_engine_operator_attention_plus_discovery_preview_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_attention_plus_discovery_preview_summary_v1.csv"

PANEL_KEY_COLS = ["site", "panel_id"]
ALLOWED_PREVIEW_CLASSES = {"queue_run", "watch_now_panel", "secondary_value_panel"}
CLASS_PRIORITY = {
    "queue_run": 0,
    "watch_now_panel": 1,
    "secondary_value_panel": 2,
}

REQUIRED_ATTENTION_COLS = [
    "attention_class",
    "site",
    "panel_id",
    "display_start_date",
    "display_end_date",
    "display_day_count",
    "display_shape_class",
    "display_status_or_tier",
    "clipped_operator_score",
    "raw_operator_score",
    "overlap_case_class",
    "attention_any_future_fault_linked_ref_flag",
    "attention_any_future_truth_linked_ref_flag",
]

REQUIRED_SECONDARY_COLS = [
    "site",
    "panel_id",
    "representative_run_start_date",
    "representative_run_end_date",
    "representative_run_day_count",
    "representative_run_shape_class",
    "representative_electrical_core_minus_broadshape_050",
    "representative_logistic_v3_discovery_score",
    "value_run_count_for_panel",
    "any_future_fault_linked_ref_flag",
    "any_future_truth_linked_ref_flag",
    "value_panel_reason_ko",
]

PREVIEW_COLS = [
    "preview_attention_class",
    "site",
    "panel_id",
    "display_start_date",
    "display_end_date",
    "display_day_count",
    "display_shape_class",
    "display_status_or_tier",
    "clipped_operator_score",
    "raw_operator_score",
    "overlap_case_class",
    "attention_any_future_fault_linked_ref_flag",
    "attention_any_future_truth_linked_ref_flag",
    "preview_reason_ko",
]

SUMMARY_COLS = [
    "record_type",
    "site",
    "preview_attention_count",
    "queue_run_count",
    "watch_now_panel_count",
    "secondary_value_panel_count",
    "overlap_panel_count",
    "preview_future_fault_linked_ref_count",
    "preview_future_truth_linked_ref_count",
    "secondary_incremental_fault_or_truth_linked_panel_count",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an operator-facing preview that combines current attention baseline with the secondary discovery value-panel lane."
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


def normalize_flag(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).gt(0).astype(int)


def ensure_unique_panels(df: pd.DataFrame, name: str) -> None:
    if df.duplicated(subset=PANEL_KEY_COLS).any():
        dup_df = df.loc[df.duplicated(subset=PANEL_KEY_COLS, keep=False), PANEL_KEY_COLS].drop_duplicates()
        raise SystemExit(f"{name} must be unique by {PANEL_KEY_COLS}, got duplicates: {dup_df.to_dict('records')}")


def load_baseline_attention(root: Path) -> pd.DataFrame:
    path = root / "_share" / ATTENTION_NOW_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_ATTENTION_COLS, path.name)
    df = normalize_panel_keys(df)
    ensure_unique_panels(df, path.name)
    df["attention_class"] = df["attention_class"].map(holdout_base.normalize_text)
    invalid_classes = sorted(set(df["attention_class"]) - {"queue_run", "watch_now_panel"})
    if invalid_classes:
        raise SystemExit(f"{path.name} contains unsupported attention_class values: {invalid_classes}")
    df["display_day_count"] = pd.to_numeric(df["display_day_count"], errors="coerce")
    df["clipped_operator_score"] = pd.to_numeric(df["clipped_operator_score"], errors="coerce")
    df["raw_operator_score"] = pd.to_numeric(df["raw_operator_score"], errors="coerce")
    df["attention_any_future_fault_linked_ref_flag"] = normalize_flag(df["attention_any_future_fault_linked_ref_flag"])
    df["attention_any_future_truth_linked_ref_flag"] = normalize_flag(df["attention_any_future_truth_linked_ref_flag"])
    baseline_reason_col = "attention_reason_ko" if "attention_reason_ko" in df.columns else ""
    merge_reason_col = "attention_merge_reason_ko" if "attention_merge_reason_ko" in df.columns else ""
    if baseline_reason_col:
        baseline_reason = df[baseline_reason_col].fillna("").astype(str)
    elif merge_reason_col:
        baseline_reason = df[merge_reason_col].fillna("").astype(str)
    else:
        baseline_reason = pd.Series("", index=df.index, dtype="object")

    preview_df = pd.DataFrame(
        {
            "preview_attention_class": df["attention_class"],
            "site": df["site"],
            "panel_id": df["panel_id"],
            "display_start_date": df["display_start_date"],
            "display_end_date": df["display_end_date"],
            "display_day_count": df["display_day_count"],
            "display_shape_class": df["display_shape_class"],
            "display_status_or_tier": df["display_status_or_tier"],
            "clipped_operator_score": df["clipped_operator_score"],
            "raw_operator_score": df["raw_operator_score"],
            "overlap_case_class": df["overlap_case_class"],
            "attention_any_future_fault_linked_ref_flag": df["attention_any_future_fault_linked_ref_flag"],
            "attention_any_future_truth_linked_ref_flag": df["attention_any_future_truth_linked_ref_flag"],
            "preview_reason_ko": baseline_reason.where(
                baseline_reason.str.len().gt(0),
                "current operator attention baseline row",
            ),
        }
    )
    return preview_df.loc[:, PREVIEW_COLS].copy()


def load_secondary_value_panels(root: Path) -> pd.DataFrame:
    path = root / "_share" / SECONDARY_VALUE_PANELS_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_SECONDARY_COLS, path.name)
    df = normalize_panel_keys(df)
    ensure_unique_panels(df, path.name)
    df["representative_run_day_count"] = pd.to_numeric(df["representative_run_day_count"], errors="coerce")
    df["representative_electrical_core_minus_broadshape_050"] = pd.to_numeric(
        df["representative_electrical_core_minus_broadshape_050"],
        errors="coerce",
    )
    df["representative_logistic_v3_discovery_score"] = pd.to_numeric(
        df["representative_logistic_v3_discovery_score"],
        errors="coerce",
    )
    df["value_run_count_for_panel"] = pd.to_numeric(df["value_run_count_for_panel"], errors="coerce")
    df["any_future_fault_linked_ref_flag"] = normalize_flag(df["any_future_fault_linked_ref_flag"])
    df["any_future_truth_linked_ref_flag"] = normalize_flag(df["any_future_truth_linked_ref_flag"])

    preview_reason = (
        "baseline attention에 없는 secondary discovery value panel preview, "
        + df["value_panel_reason_ko"].fillna("").astype(str)
    ).str.strip().str.rstrip(",")

    preview_df = pd.DataFrame(
        {
            "preview_attention_class": "secondary_value_panel",
            "site": df["site"],
            "panel_id": df["panel_id"],
            "display_start_date": df["representative_run_start_date"],
            "display_end_date": df["representative_run_end_date"],
            "display_day_count": df["representative_run_day_count"],
            "display_shape_class": df["representative_run_shape_class"],
            "display_status_or_tier": "secondary_discovery_value",
            "clipped_operator_score": df["representative_electrical_core_minus_broadshape_050"],
            "raw_operator_score": df["representative_electrical_core_minus_broadshape_050"],
            "overlap_case_class": "not_in_baseline_attention",
            "attention_any_future_fault_linked_ref_flag": df["any_future_fault_linked_ref_flag"],
            "attention_any_future_truth_linked_ref_flag": df["any_future_truth_linked_ref_flag"],
            "preview_reason_ko": preview_reason,
        }
    )
    return preview_df.loc[:, PREVIEW_COLS].copy()


def sort_preview(preview_df: pd.DataFrame) -> pd.DataFrame:
    sorted_df = preview_df.copy()
    sorted_df["_class_priority"] = sorted_df["preview_attention_class"].map(CLASS_PRIORITY).fillna(99)
    sorted_df["display_day_count"] = pd.to_numeric(sorted_df["display_day_count"], errors="coerce")
    sorted_df["clipped_operator_score"] = pd.to_numeric(sorted_df["clipped_operator_score"], errors="coerce")
    sorted_df["raw_operator_score"] = pd.to_numeric(sorted_df["raw_operator_score"], errors="coerce")
    sorted_df = sorted_df.sort_values(
        ["_class_priority", "clipped_operator_score", "display_day_count", "site", "panel_id"],
        ascending=[True, False, False, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    return sorted_df.drop(columns="_class_priority")


def build_preview(baseline_df: pd.DataFrame, secondary_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    baseline_keys = set(map(tuple, baseline_df.loc[:, PANEL_KEY_COLS].itertuples(index=False, name=None)))
    secondary_df = secondary_df.copy()
    secondary_df["overlap_with_baseline_flag"] = secondary_df.apply(
        lambda row: (row["site"], row["panel_id"]) in baseline_keys,
        axis=1,
    ).astype(int)
    appended_secondary_df = secondary_df.loc[secondary_df["overlap_with_baseline_flag"].eq(0)].copy()
    preview_df = pd.concat([baseline_df, appended_secondary_df.loc[:, PREVIEW_COLS]], ignore_index=True)
    preview_df = sort_preview(preview_df)
    return preview_df, secondary_df


def build_summary(preview_df: pd.DataFrame, baseline_df: pd.DataFrame, secondary_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    secondary_df = secondary_df.copy()
    secondary_df["secondary_incremental_fault_or_truth_linked_panel_flag"] = (
        secondary_df["overlap_with_baseline_flag"].eq(0)
        & (
            secondary_df["attention_any_future_fault_linked_ref_flag"].eq(1)
            | secondary_df["attention_any_future_truth_linked_ref_flag"].eq(1)
        )
    ).astype(int)

    def summarize(site: str, record_type: str) -> None:
        if record_type == "overall":
            preview_subset = preview_df.copy()
            baseline_subset = baseline_df.copy()
            secondary_subset = secondary_df.copy()
        else:
            preview_subset = preview_df.loc[preview_df["site"].eq(site)].copy()
            baseline_subset = baseline_df.loc[baseline_df["site"].eq(site)].copy()
            secondary_subset = secondary_df.loc[secondary_df["site"].eq(site)].copy()
        rows.append(
            {
                "record_type": record_type,
                "site": site,
                "preview_attention_count": int(len(preview_subset)),
                "queue_run_count": int(preview_subset["preview_attention_class"].eq("queue_run").sum()),
                "watch_now_panel_count": int(preview_subset["preview_attention_class"].eq("watch_now_panel").sum()),
                "secondary_value_panel_count": int(preview_subset["preview_attention_class"].eq("secondary_value_panel").sum()),
                "overlap_panel_count": int(secondary_subset["overlap_with_baseline_flag"].sum()) if not secondary_subset.empty else 0,
                "preview_future_fault_linked_ref_count": int(
                    normalize_flag(preview_subset["attention_any_future_fault_linked_ref_flag"]).sum()
                )
                if not preview_subset.empty
                else 0,
                "preview_future_truth_linked_ref_count": int(
                    normalize_flag(preview_subset["attention_any_future_truth_linked_ref_flag"]).sum()
                )
                if not preview_subset.empty
                else 0,
                "secondary_incremental_fault_or_truth_linked_panel_count": int(
                    secondary_subset["secondary_incremental_fault_or_truth_linked_panel_flag"].sum()
                )
                if not secondary_subset.empty
                else 0,
                "note_ko": "queue/watch baseline은 유지하고, non-overlap secondary value panel만 preview에 별도 추가해 unified operator preview를 만든다",
            }
        )

    summarize("", "overall")
    all_sites = sorted(
        set(baseline_df["site"].dropna().map(holdout_base.normalize_text).unique()).union(
            set(secondary_df["site"].dropna().map(holdout_base.normalize_text).unique())
        )
    )
    for site in all_sites:
        summarize(site, "site")
    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def save_outputs(root: Path, preview_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    preview_df.to_csv(share_dir / PREVIEW_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    baseline_df = load_baseline_attention(root)
    secondary_df = load_secondary_value_panels(root)
    preview_df, secondary_enriched_df = build_preview(baseline_df, secondary_df)
    summary_df = build_summary(preview_df, baseline_df, secondary_enriched_df)
    save_outputs(root, preview_df, summary_df)


if __name__ == "__main__":
    main()
