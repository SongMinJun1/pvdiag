#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import build_panel_day_engine_run_ranker_v2_holdout_audit as holdout_base

ATTENTION_NOW_NAME = "panel_day_engine_operator_attention_now_v1.csv"
SECONDARY_VALUE_PANELS_NAME = "panel_day_engine_operator_secondary_discovery_value_panels_v1.csv"
SECONDARY_CLUSTER_ROLLUP_NAME = "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.csv"
POLICY_RECOMMENDATION_NAME = "panel_day_engine_operator_discovery_preview_policy_recommendation_v1.csv"

PREVIEW_OUTPUT_NAME = "panel_day_engine_operator_attention_plus_discovery_preview_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_attention_plus_discovery_preview_summary_v1.csv"
NARROW_PREVIEW_OUTPUT_NAME = "panel_day_engine_operator_attention_plus_discovery_preview_narrow_v1.csv"
NARROW_SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_attention_plus_discovery_preview_narrow_summary_v1.csv"
CLUSTER_PREVIEW_OUTPUT_NAME = "panel_day_engine_operator_attention_plus_discovery_cluster_preview_v1.csv"
CLUSTER_PREVIEW_SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_attention_plus_discovery_cluster_preview_summary_v1.csv"

PANEL_KEY_COLS = ["site", "panel_id"]
ALLOWED_PREVIEW_CLASSES = {"queue_run", "watch_now_panel", "secondary_value_panel"}
ALLOWED_POLICY_FAMILIES = {
    "score_threshold",
    "topk_per_site",
    "threshold_plus_topk_per_site",
}
CLASS_PRIORITY = {
    "queue_run": 0,
    "watch_now_panel": 1,
    "secondary_value_panel": 2,
    "secondary_value_cluster": 3,
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
REQUIRED_CLUSTER_ROLLUP_COLS = [
    "site",
    "cluster_id",
    "cluster_start_date",
    "cluster_end_date",
    "cluster_span_days",
    "panel_count",
    "panel_ids_csv",
    "max_electrical_core_minus_broadshape_050_in_cluster",
    "any_future_fault_linked_ref_flag",
    "any_future_truth_linked_ref_flag",
    "cluster_reason_ko",
]
REQUIRED_POLICY_RECOMMENDATION_COLS = ["recommended_policy_name"]

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
NARROW_PREVIEW_COLS = [
    *PREVIEW_COLS,
    "preview_policy_name",
    "is_narrow_discovery_row_flag",
]
CLUSTER_PREVIEW_COLS = [
    "preview_attention_class",
    "site",
    "display_entity_id",
    "display_start_date",
    "display_end_date",
    "display_span_or_day_count",
    "display_shape_or_cluster_kind",
    "display_status_or_tier",
    "display_score",
    "linked_ref_flag",
    "truth_ref_flag",
    "cluster_panel_count",
    "member_overlap_with_attention_count",
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
NARROW_SUMMARY_COLS = [
    "record_type",
    "site",
    "preview_policy_name",
    "narrow_preview_attention_count",
    "queue_run_count",
    "watch_now_panel_count",
    "secondary_value_panel_count",
    "overlap_panel_count",
    "narrow_preview_future_fault_linked_ref_count",
    "narrow_preview_future_truth_linked_ref_count",
    "narrow_incremental_fault_or_truth_linked_panel_count",
    "narrow_selected_site_count",
    "narrow_max_single_site_share",
    "note_ko",
]
CLUSTER_PREVIEW_SUMMARY_COLS = [
    "record_type",
    "site",
    "cluster_preview_count",
    "queue_run_count",
    "watch_now_panel_count",
    "secondary_value_cluster_count",
    "cluster_panel_total_count",
    "clusters_with_future_fault_linked_ref_count",
    "clusters_with_future_truth_linked_ref_count",
    "total_member_overlap_with_attention_count",
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


def parse_numeric(value: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise SystemExit(f"invalid numeric threshold in preview policy recommendation: {value}") from exc


def parse_policy_name(policy_name: str) -> dict[str, object]:
    text = holdout_base.normalize_text(policy_name)
    if not text or "|" not in text:
        raise SystemExit(f"recommended_policy_name must be '<family>|<policy_spec>', got: {policy_name}")
    family, policy_spec = text.split("|", 1)
    family = holdout_base.normalize_text(family)
    policy_spec = holdout_base.normalize_text(policy_spec)
    if family not in ALLOWED_POLICY_FAMILIES:
        raise SystemExit(f"unsupported recommended policy family: {family}")

    if family == "score_threshold":
        if ">=" not in policy_spec:
            raise SystemExit(f"score_threshold policy must look like 'field>=value', got: {policy_spec}")
        field, threshold = policy_spec.split(">=", 1)
        field = holdout_base.normalize_text(field)
        if field != "representative_electrical_core_minus_broadshape_050":
            raise SystemExit(f"score_threshold field must be representative_electrical_core_minus_broadshape_050, got: {field}")
        return {
            "policy_name": text,
            "policy_family": family,
            "policy_spec": policy_spec,
            "threshold": parse_numeric(holdout_base.normalize_text(threshold)),
        }

    if family == "topk_per_site":
        prefix = "top_"
        suffix = "_per_site_by_representative_electrical_core_minus_broadshape_050"
        if not policy_spec.startswith(prefix) or not policy_spec.endswith(suffix):
            raise SystemExit(f"topk_per_site policy must match 'top_K_per_site_by_representative_electrical_core_minus_broadshape_050', got: {policy_spec}")
        top_k_text = policy_spec[len(prefix) : -len(suffix)]
        if not top_k_text.isdigit():
            raise SystemExit(f"topk_per_site K must be integer, got: {top_k_text}")
        return {
            "policy_name": text,
            "policy_family": family,
            "policy_spec": policy_spec,
            "top_k": int(top_k_text),
        }

    if family == "threshold_plus_topk_per_site":
        parts = policy_spec.split("&")
        if len(parts) != 2:
            raise SystemExit(
                "threshold_plus_topk_per_site policy must look like "
                "'representative_electrical_core_minus_broadshape_050>=T&top_K_per_site_by_representative_electrical_core_minus_broadshape_050'"
            )
        threshold_policy = parse_policy_name(f"score_threshold|{parts[0]}")
        topk_policy = parse_policy_name(f"topk_per_site|{parts[1]}")
        return {
            "policy_name": text,
            "policy_family": family,
            "policy_spec": policy_spec,
            "threshold": float(threshold_policy["threshold"]),
            "top_k": int(topk_policy["top_k"]),
        }

    raise SystemExit(f"unsupported recommended policy family: {family}")


def load_policy_recommendation(root: Path) -> dict[str, object]:
    path = root / "_share" / POLICY_RECOMMENDATION_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_POLICY_RECOMMENDATION_COLS, path.name)
    if len(df) != 1:
        raise SystemExit(f"{path.name} must contain exactly one row")
    policy_name = holdout_base.normalize_text(df.iloc[0]["recommended_policy_name"])
    if not policy_name:
        raise SystemExit(f"{path.name} must provide recommended_policy_name")
    return parse_policy_name(policy_name)


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


def load_secondary_value_panel_source(root: Path) -> pd.DataFrame:
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
    return df.loc[:, REQUIRED_SECONDARY_COLS].copy()


def load_cluster_rollup_source(root: Path) -> pd.DataFrame:
    path = root / "_share" / SECONDARY_CLUSTER_ROLLUP_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_CLUSTER_ROLLUP_COLS, path.name)
    df = df.copy()
    df["site"] = df["site"].map(holdout_base.normalize_text)
    df["cluster_id"] = df["cluster_id"].map(holdout_base.normalize_text)
    if df.duplicated(subset=["site", "cluster_id"]).any():
        dup_df = df.loc[df.duplicated(subset=["site", "cluster_id"], keep=False), ["site", "cluster_id"]].drop_duplicates()
        raise SystemExit(f"{path.name} must be unique by ['site', 'cluster_id'], got duplicates: {dup_df.to_dict('records')}")
    df["cluster_span_days"] = pd.to_numeric(df["cluster_span_days"], errors="coerce")
    df["panel_count"] = pd.to_numeric(df["panel_count"], errors="coerce")
    df["max_electrical_core_minus_broadshape_050_in_cluster"] = pd.to_numeric(
        df["max_electrical_core_minus_broadshape_050_in_cluster"],
        errors="coerce",
    )
    df["any_future_fault_linked_ref_flag"] = normalize_flag(df["any_future_fault_linked_ref_flag"])
    df["any_future_truth_linked_ref_flag"] = normalize_flag(df["any_future_truth_linked_ref_flag"])
    df["panel_ids_csv"] = df["panel_ids_csv"].fillna("").astype(str)
    return df.loc[:, REQUIRED_CLUSTER_ROLLUP_COLS].copy()


def build_secondary_preview_rows(df: pd.DataFrame) -> pd.DataFrame:
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


def load_secondary_value_panels(root: Path) -> pd.DataFrame:
    return build_secondary_preview_rows(load_secondary_value_panel_source(root))


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


def count_member_overlap(panel_ids_csv: str, site: str, baseline_keys: set[tuple[str, str]]) -> int:
    panel_ids = [
        holdout_base.normalize_text(panel_id)
        for panel_id in str(panel_ids_csv).split(",")
        if holdout_base.normalize_text(panel_id)
    ]
    site_text = holdout_base.normalize_text(site)
    return int(sum((site_text, panel_id) in baseline_keys for panel_id in panel_ids))


def build_cluster_preview(
    baseline_df: pd.DataFrame,
    cluster_source_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    baseline_keys = set(map(tuple, baseline_df.loc[:, PANEL_KEY_COLS].itertuples(index=False, name=None)))
    baseline_rows = pd.DataFrame(
        {
            "preview_attention_class": baseline_df["preview_attention_class"],
            "site": baseline_df["site"],
            "display_entity_id": baseline_df["panel_id"],
            "display_start_date": baseline_df["display_start_date"],
            "display_end_date": baseline_df["display_end_date"],
            "display_span_or_day_count": baseline_df["display_day_count"],
            "display_shape_or_cluster_kind": baseline_df["display_shape_class"],
            "display_status_or_tier": baseline_df["display_status_or_tier"],
            "display_score": baseline_df["clipped_operator_score"],
            "linked_ref_flag": baseline_df["attention_any_future_fault_linked_ref_flag"],
            "truth_ref_flag": baseline_df["attention_any_future_truth_linked_ref_flag"],
            "cluster_panel_count": 1,
            "member_overlap_with_attention_count": 0,
            "preview_reason_ko": baseline_df["preview_reason_ko"],
        }
    )

    cluster_enriched_df = cluster_source_df.copy()
    cluster_enriched_df["member_overlap_with_attention_count"] = cluster_enriched_df.apply(
        lambda row: count_member_overlap(row["panel_ids_csv"], row["site"], baseline_keys),
        axis=1,
    ).astype(int)

    cluster_reason_prefix = cluster_enriched_df["any_future_fault_linked_ref_flag"].eq(1).map(
        lambda flag: "cluster 압축 preview이며 retrospective fault linkage reference가 있음"
        if flag
        else None
    )
    cluster_reason_prefix = cluster_reason_prefix.where(
        cluster_reason_prefix.notna(),
        cluster_enriched_df["any_future_truth_linked_ref_flag"].eq(1).map(
            lambda flag: "cluster 압축 preview이며 retrospective truth linkage reference가 있음"
            if flag
            else "cluster 압축 preview로 site skew와 operator load를 낮춤"
        ),
    )
    cluster_rows = pd.DataFrame(
        {
            "preview_attention_class": "secondary_value_cluster",
            "site": cluster_enriched_df["site"],
            "display_entity_id": cluster_enriched_df["cluster_id"],
            "display_start_date": cluster_enriched_df["cluster_start_date"],
            "display_end_date": cluster_enriched_df["cluster_end_date"],
            "display_span_or_day_count": cluster_enriched_df["cluster_span_days"],
            "display_shape_or_cluster_kind": "discovery_cluster",
            "display_status_or_tier": "secondary_discovery_cluster",
            "display_score": cluster_enriched_df["max_electrical_core_minus_broadshape_050_in_cluster"],
            "linked_ref_flag": cluster_enriched_df["any_future_fault_linked_ref_flag"],
            "truth_ref_flag": cluster_enriched_df["any_future_truth_linked_ref_flag"],
            "cluster_panel_count": cluster_enriched_df["panel_count"],
            "member_overlap_with_attention_count": cluster_enriched_df["member_overlap_with_attention_count"],
            "preview_reason_ko": cluster_reason_prefix + ", " + cluster_enriched_df["cluster_reason_ko"].fillna("").astype(str),
        }
    )

    preview_df = pd.concat([baseline_rows.loc[:, CLUSTER_PREVIEW_COLS], cluster_rows.loc[:, CLUSTER_PREVIEW_COLS]], ignore_index=True)
    preview_df = sort_cluster_preview(preview_df)
    return preview_df, cluster_enriched_df


def sort_cluster_preview(preview_df: pd.DataFrame) -> pd.DataFrame:
    sorted_df = preview_df.copy()
    sorted_df["_class_priority"] = sorted_df["preview_attention_class"].map(CLASS_PRIORITY).fillna(99)
    sorted_df["display_score"] = pd.to_numeric(sorted_df["display_score"], errors="coerce")
    sorted_df["cluster_panel_count"] = pd.to_numeric(sorted_df["cluster_panel_count"], errors="coerce")
    sorted_df["display_span_or_day_count"] = pd.to_numeric(sorted_df["display_span_or_day_count"], errors="coerce")
    sorted_df = sorted_df.sort_values(
        ["_class_priority", "display_score", "cluster_panel_count", "display_span_or_day_count", "site", "display_entity_id"],
        ascending=[True, False, False, False, True, True],
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


def select_policy_source_rows(source_df: pd.DataFrame, policy: dict[str, object]) -> pd.DataFrame:
    family = str(policy["policy_family"])
    working = source_df.copy()
    working["site_rank_by_score"] = (
        working.sort_values(
            ["representative_electrical_core_minus_broadshape_050", "site", "panel_id"],
            ascending=[False, True, True],
            kind="mergesort",
        )
        .groupby("site", dropna=False)
        .cumcount()
        .add(1)
    )
    if family == "score_threshold":
        return working.loc[
            working["representative_electrical_core_minus_broadshape_050"].ge(float(policy["threshold"]))
        ].copy()
    if family == "topk_per_site":
        return working.loc[working["site_rank_by_score"].le(int(policy["top_k"]))].copy()
    if family == "threshold_plus_topk_per_site":
        return working.loc[
            working["representative_electrical_core_minus_broadshape_050"].ge(float(policy["threshold"]))
            & working["site_rank_by_score"].le(int(policy["top_k"]))
        ].copy()
    raise SystemExit(f"unsupported recommended policy family: {family}")


def build_narrow_preview(
    baseline_df: pd.DataFrame,
    narrow_secondary_df: pd.DataFrame,
    policy_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    baseline_keys = set(map(tuple, baseline_df.loc[:, PANEL_KEY_COLS].itertuples(index=False, name=None)))
    secondary_enriched_df = narrow_secondary_df.copy()
    secondary_enriched_df["overlap_with_baseline_flag"] = secondary_enriched_df.apply(
        lambda row: (row["site"], row["panel_id"]) in baseline_keys,
        axis=1,
    ).astype(int)

    baseline_rows = baseline_df.copy()
    baseline_rows["preview_policy_name"] = policy_name
    baseline_rows["is_narrow_discovery_row_flag"] = 0

    appended_secondary_df = secondary_enriched_df.loc[secondary_enriched_df["overlap_with_baseline_flag"].eq(0)].copy()
    appended_secondary_df["preview_policy_name"] = policy_name
    appended_secondary_df["is_narrow_discovery_row_flag"] = 1

    narrow_preview_df = pd.concat(
        [
            baseline_rows.loc[:, NARROW_PREVIEW_COLS],
            appended_secondary_df.loc[:, NARROW_PREVIEW_COLS],
        ],
        ignore_index=True,
    )
    narrow_preview_df = sort_preview(narrow_preview_df)
    return narrow_preview_df, secondary_enriched_df


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


def build_narrow_summary(
    narrow_preview_df: pd.DataFrame,
    baseline_df: pd.DataFrame,
    narrow_secondary_df: pd.DataFrame,
    policy_name: str,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    narrow_secondary_df = narrow_secondary_df.copy()
    narrow_secondary_df["narrow_incremental_fault_or_truth_linked_panel_flag"] = (
        narrow_secondary_df["overlap_with_baseline_flag"].eq(0)
        & (
            narrow_secondary_df["attention_any_future_fault_linked_ref_flag"].eq(1)
            | narrow_secondary_df["attention_any_future_truth_linked_ref_flag"].eq(1)
        )
    ).astype(int)
    narrow_secondary_df["included_in_narrow_preview_flag"] = narrow_secondary_df["overlap_with_baseline_flag"].eq(0).astype(int)

    def summarize(site: str, record_type: str) -> None:
        if record_type == "overall":
            preview_subset = narrow_preview_df.copy()
            secondary_subset = narrow_secondary_df.copy()
        else:
            preview_subset = narrow_preview_df.loc[narrow_preview_df["site"].eq(site)].copy()
            secondary_subset = narrow_secondary_df.loc[narrow_secondary_df["site"].eq(site)].copy()
        included_secondary = secondary_subset.loc[secondary_subset["included_in_narrow_preview_flag"].eq(1)].copy()
        if not included_secondary.empty:
            site_counts = included_secondary.groupby("site", dropna=False).size()
            max_site_share = float(site_counts.max()) / float(len(included_secondary))
            selected_site_count = int(included_secondary["site"].nunique())
        else:
            max_site_share = None
            selected_site_count = 0
        rows.append(
            {
                "record_type": record_type,
                "site": site,
                "preview_policy_name": policy_name,
                "narrow_preview_attention_count": int(len(preview_subset)),
                "queue_run_count": int(preview_subset["preview_attention_class"].eq("queue_run").sum()),
                "watch_now_panel_count": int(preview_subset["preview_attention_class"].eq("watch_now_panel").sum()),
                "secondary_value_panel_count": int(preview_subset["preview_attention_class"].eq("secondary_value_panel").sum()),
                "overlap_panel_count": int(secondary_subset["overlap_with_baseline_flag"].sum()) if not secondary_subset.empty else 0,
                "narrow_preview_future_fault_linked_ref_count": int(
                    normalize_flag(preview_subset["attention_any_future_fault_linked_ref_flag"]).sum()
                )
                if not preview_subset.empty
                else 0,
                "narrow_preview_future_truth_linked_ref_count": int(
                    normalize_flag(preview_subset["attention_any_future_truth_linked_ref_flag"]).sum()
                )
                if not preview_subset.empty
                else 0,
                "narrow_incremental_fault_or_truth_linked_panel_count": int(
                    included_secondary["narrow_incremental_fault_or_truth_linked_panel_flag"].sum()
                )
                if not included_secondary.empty
                else 0,
                "narrow_selected_site_count": selected_site_count,
                "narrow_max_single_site_share": max_site_share,
                "note_ko": "full preview는 유지하고, recommended current-state policy를 적용한 narrow discovery preview variant를 side-by-side로 제공",
            }
        )

    summarize("", "overall")
    all_sites = sorted(
        set(baseline_df["site"].dropna().map(holdout_base.normalize_text).unique()).union(
            set(narrow_secondary_df["site"].dropna().map(holdout_base.normalize_text).unique())
        )
    )
    for site in all_sites:
        summarize(site, "site")
    return pd.DataFrame(rows, columns=NARROW_SUMMARY_COLS)


def build_cluster_preview_summary(
    cluster_preview_df: pd.DataFrame,
    cluster_source_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def summarize(site: str, record_type: str) -> None:
        if record_type == "overall":
            preview_subset = cluster_preview_df.copy()
            cluster_subset = cluster_source_df.copy()
        else:
            preview_subset = cluster_preview_df.loc[cluster_preview_df["site"].eq(site)].copy()
            cluster_subset = cluster_source_df.loc[cluster_source_df["site"].eq(site)].copy()
        rows.append(
            {
                "record_type": record_type,
                "site": site,
                "cluster_preview_count": int(len(preview_subset)),
                "queue_run_count": int(preview_subset["preview_attention_class"].eq("queue_run").sum()),
                "watch_now_panel_count": int(preview_subset["preview_attention_class"].eq("watch_now_panel").sum()),
                "secondary_value_cluster_count": int(preview_subset["preview_attention_class"].eq("secondary_value_cluster").sum()),
                "cluster_panel_total_count": int(cluster_subset["panel_count"].sum()) if not cluster_subset.empty else 0,
                "clusters_with_future_fault_linked_ref_count": int(cluster_subset["any_future_fault_linked_ref_flag"].sum())
                if not cluster_subset.empty
                else 0,
                "clusters_with_future_truth_linked_ref_count": int(cluster_subset["any_future_truth_linked_ref_flag"].sum())
                if not cluster_subset.empty
                else 0,
                "total_member_overlap_with_attention_count": int(cluster_subset["member_overlap_with_attention_count"].sum())
                if not cluster_subset.empty
                else 0,
                "note_ko": "baseline queue/watch는 유지하고, secondary discovery cluster를 side-by-side preview로 추가",
            }
        )

    summarize("", "overall")
    all_sites = sorted(
        set(cluster_preview_df["site"].dropna().map(holdout_base.normalize_text).unique()).union(
            set(cluster_source_df["site"].dropna().map(holdout_base.normalize_text).unique())
        )
    )
    for site in all_sites:
        summarize(site, "site")
    return pd.DataFrame(rows, columns=CLUSTER_PREVIEW_SUMMARY_COLS)


def save_outputs(
    root: Path,
    preview_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    narrow_preview_df: pd.DataFrame,
    narrow_summary_df: pd.DataFrame,
    cluster_preview_df: pd.DataFrame,
    cluster_preview_summary_df: pd.DataFrame,
) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    preview_df.to_csv(share_dir / PREVIEW_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    narrow_preview_df.to_csv(share_dir / NARROW_PREVIEW_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    narrow_summary_df.to_csv(share_dir / NARROW_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    cluster_preview_df.to_csv(share_dir / CLUSTER_PREVIEW_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    cluster_preview_summary_df.to_csv(share_dir / CLUSTER_PREVIEW_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    baseline_df = load_baseline_attention(root)
    secondary_source_df = load_secondary_value_panel_source(root)
    secondary_df = build_secondary_preview_rows(secondary_source_df)
    preview_df, secondary_enriched_df = build_preview(baseline_df, secondary_df)
    summary_df = build_summary(preview_df, baseline_df, secondary_enriched_df)

    policy = load_policy_recommendation(root)
    narrow_source_df = select_policy_source_rows(secondary_source_df, policy)
    narrow_secondary_df = build_secondary_preview_rows(narrow_source_df)
    narrow_preview_df, narrow_secondary_enriched_df = build_narrow_preview(
        baseline_df,
        narrow_secondary_df,
        str(policy["policy_name"]),
    )
    narrow_summary_df = build_narrow_summary(
        narrow_preview_df,
        baseline_df,
        narrow_secondary_enriched_df,
        str(policy["policy_name"]),
    )
    cluster_source_df = load_cluster_rollup_source(root)
    cluster_preview_df, cluster_enriched_df = build_cluster_preview(baseline_df, cluster_source_df)
    cluster_preview_summary_df = build_cluster_preview_summary(cluster_preview_df, cluster_enriched_df)
    save_outputs(
        root,
        preview_df,
        summary_df,
        narrow_preview_df,
        narrow_summary_df,
        cluster_preview_df,
        cluster_preview_summary_df,
    )


if __name__ == "__main__":
    main()
