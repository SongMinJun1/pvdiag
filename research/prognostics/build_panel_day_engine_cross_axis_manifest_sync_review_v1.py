#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


FRICTION_DETAIL_NAME = "panel_day_engine_report_entry_friction_axis_v1.csv"
RECOVERY_DETAIL_NAME = "panel_day_engine_recovery_recurrence_axis_v1.csv"
COMMON_CAUSE_DETAIL_NAME = "panel_day_engine_common_cause_synchrony_axis_v1.csv"
MANIFEST_DETAIL_NAME = "panel_day_engine_evidence_manifest_v1.csv"
ROLE_MANIFEST_NAME = "repo_role_boundary_manifest_v1.csv"
MIRROR_MANIFEST_NAME = "repo_mirror_boundary_manifest_v1.csv"
BUILDER_REGISTRY_NAME = "repo_active_builder_entrypoint_registry_v1.csv"

DETAIL_OUTPUT_NAME = "panel_day_engine_cross_axis_manifest_sync_review_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_cross_axis_manifest_sync_review_summary_v1.csv"
SYNC_OUTPUT_NAME = "panel_day_engine_cross_axis_manifest_sync_status_v1.csv"

DETAIL_COLS = [
    "site",
    "panel_id",
    "axis_presence_count",
    "has_friction_axis",
    "has_recovery_axis",
    "has_common_cause_axis",
    "friction_direct_families",
    "friction_blocker_types",
    "friction_best_lanes",
    "friction_direct_row_count",
    "friction_group_off_row_count",
    "friction_site_event_row_count",
    "recovery_bucket",
    "recovery_best_report_lane",
    "recovery_row_count",
    "re_drop_row_count",
    "recovered_sustained_row_count",
    "synchrony_bucket",
    "synchrony_best_report_lane",
    "common_cause_row_count",
    "site_event_row_count",
    "group_off_row_count",
    "subgroup_common_cause_row_count",
    "prefault_B_overlap_row_count",
    "co_drop_hint_row_count",
    "max_co_drop_frac",
    "strong_common_cause_flag",
    "subgroup_or_breadth_context_flag",
    "local_or_weak_synchrony_flag",
    "report_entry_blocker_flag",
    "recovery_morphology_pressure_flag",
    "review_focus_bucket",
    "review_note",
]
SUMMARY_COLS = [
    "review_focus_bucket",
    "site",
    "panels",
    "panels_with_friction_axis",
    "panels_with_recovery_axis",
    "panels_with_common_cause_axis",
    "panels_with_strong_common_cause",
    "panels_with_report_entry_blocker",
    "panels_with_recovery_pressure",
    "total_common_cause_rows",
    "max_co_drop_frac",
]
SYNC_COLS = [
    "sync_item",
    "sync_family",
    "expected_path",
    "artifact_exists",
    "manifest_rows",
    "manifest_existing_rows",
    "registry_rows",
    "sync_status",
    "sync_note",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a cross-axis review over report-entry friction, recovery/recurrence, "
            "common-cause synchrony, and the evidence/cleanup manifests."
        )
    )
    parser.add_argument("--friction-root", type=Path, required=True, help="Root containing report-entry friction axis CSVs.")
    parser.add_argument("--recovery-root", type=Path, required=True, help="Root containing recovery/recurrence axis CSVs.")
    parser.add_argument("--common-cause-root", type=Path, required=True, help="Root containing common-cause synchrony axis CSVs.")
    parser.add_argument("--manifest-root", type=Path, required=True, help="Root containing evidence manifest CSVs.")
    parser.add_argument("--role-root", type=Path, required=True, help="Root containing repo role boundary manifest CSVs.")
    parser.add_argument("--mirror-root", type=Path, required=True, help="Root containing repo mirror boundary manifest CSVs.")
    parser.add_argument("--builder-registry-root", type=Path, required=True, help="Root containing builder entrypoint registry CSVs.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Folder where review CSVs will be written.")
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def to_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return 0
    return int(numeric)


def read_csv(path: Path, required: bool = True) -> pd.DataFrame:
    if not path.exists():
        if required:
            raise SystemExit(f"missing input: {path}")
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def add_missing_columns(df: pd.DataFrame, cols: list[str], default: object = 0) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col not in out.columns:
            out[col] = default
    return out


def join_unique(values: pd.Series) -> str:
    items = sorted({normalize_text(value) for value in values.tolist() if normalize_text(value)})
    return "|".join(items)


def pick_priority(values: pd.Series, priority: list[str], default: str = "") -> str:
    present = {normalize_text(value) for value in values.tolist() if normalize_text(value)}
    for item in priority:
        if item in present:
            return item
    return sorted(present)[0] if present else default


def aggregate_friction(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["site", "panel_id"])
    out = add_missing_columns(
        df,
        [
            "site",
            "panel_id",
            "direct_flag_family",
            "blocker_type",
            "best_report_lane",
            "direct_row_count",
            "group_off_row_count",
            "site_event_soft_row_count",
            "site_event_hard_row_count",
        ],
        default=0,
    )
    out["site"] = out["site"].map(normalize_text)
    out["panel_id"] = out["panel_id"].map(normalize_text)
    for col in ["direct_row_count", "group_off_row_count", "site_event_soft_row_count", "site_event_hard_row_count"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    grouped = (
        out.groupby(["site", "panel_id"], as_index=False)
        .agg(
            friction_direct_families=("direct_flag_family", join_unique),
            friction_blocker_types=("blocker_type", join_unique),
            friction_best_lanes=("best_report_lane", join_unique),
            friction_direct_row_count=("direct_row_count", "sum"),
            friction_group_off_row_count=("group_off_row_count", "sum"),
            friction_site_event_soft_row_count=("site_event_soft_row_count", "sum"),
            friction_site_event_hard_row_count=("site_event_hard_row_count", "sum"),
        )
    )
    grouped["has_friction_axis"] = 1
    grouped["friction_site_event_row_count"] = (
        grouped["friction_site_event_soft_row_count"] + grouped["friction_site_event_hard_row_count"]
    )
    return grouped.drop(columns=["friction_site_event_soft_row_count", "friction_site_event_hard_row_count"])


def aggregate_recovery(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["site", "panel_id"])
    out = add_missing_columns(
        df,
        [
            "site",
            "panel_id",
            "recovery_bucket",
            "best_report_lane",
            "recovery_row_count",
            "re_drop_row_count",
            "recovered_sustained_row_count",
        ],
        default=0,
    )
    out["site"] = out["site"].map(normalize_text)
    out["panel_id"] = out["panel_id"].map(normalize_text)
    for col in ["recovery_row_count", "re_drop_row_count", "recovered_sustained_row_count"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    priority = ["re_drop_cycle", "persistent_non_recovery", "sustained_recovery", "transient_recovery"]
    grouped = (
        out.groupby(["site", "panel_id"], as_index=False)
        .agg(
            recovery_bucket=("recovery_bucket", lambda s: pick_priority(s, priority)),
            recovery_best_report_lane=("best_report_lane", join_unique),
            recovery_row_count=("recovery_row_count", "sum"),
            re_drop_row_count=("re_drop_row_count", "sum"),
            recovered_sustained_row_count=("recovered_sustained_row_count", "sum"),
        )
    )
    grouped["has_recovery_axis"] = 1
    return grouped


def aggregate_common_cause(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["site", "panel_id"])
    out = add_missing_columns(
        df,
        [
            "site",
            "panel_id",
            "synchrony_bucket",
            "best_report_lane",
            "common_cause_row_count",
            "site_event_row_count",
            "group_off_row_count",
            "subgroup_common_cause_row_count",
            "prefault_B_overlap_row_count",
            "co_drop_hint_row_count",
            "max_co_drop_frac",
        ],
        default=0,
    )
    out["site"] = out["site"].map(normalize_text)
    out["panel_id"] = out["panel_id"].map(normalize_text)
    numeric_cols = [
        "common_cause_row_count",
        "site_event_row_count",
        "group_off_row_count",
        "subgroup_common_cause_row_count",
        "prefault_B_overlap_row_count",
        "co_drop_hint_row_count",
        "max_co_drop_frac",
    ]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    priority = [
        "site_event_synchrony",
        "group_off_synchrony",
        "prefault_B_common_cause_overlap",
        "subgroup_synchrony_candidate",
        "co_drop_breadth_hint",
        "panel_local_or_weak_synchrony",
    ]
    grouped = (
        out.groupby(["site", "panel_id"], as_index=False)
        .agg(
            synchrony_bucket=("synchrony_bucket", lambda s: pick_priority(s, priority)),
            synchrony_best_report_lane=("best_report_lane", join_unique),
            common_cause_row_count=("common_cause_row_count", "sum"),
            site_event_row_count=("site_event_row_count", "sum"),
            group_off_row_count=("group_off_row_count", "sum"),
            subgroup_common_cause_row_count=("subgroup_common_cause_row_count", "sum"),
            prefault_B_overlap_row_count=("prefault_B_overlap_row_count", "sum"),
            co_drop_hint_row_count=("co_drop_hint_row_count", "sum"),
            max_co_drop_frac=("max_co_drop_frac", "max"),
        )
    )
    grouped["has_common_cause_axis"] = 1
    return grouped


def classify_review(row: dict[str, object]) -> tuple[str, str]:
    sync_bucket = normalize_text(row.get("synchrony_bucket"))
    recovery_bucket = normalize_text(row.get("recovery_bucket"))
    blocker = normalize_text(row.get("friction_blocker_types"))
    has_strong_common = to_int(row.get("strong_common_cause_flag")) == 1
    has_context = to_int(row.get("subgroup_or_breadth_context_flag")) == 1
    has_recovery_pressure = to_int(row.get("recovery_morphology_pressure_flag")) == 1
    has_blocker = to_int(row.get("report_entry_blocker_flag")) == 1

    if has_strong_common:
        return (
            "strong_common_cause_hold_review",
            "site/group/prefault overlap context is strong enough to review before any panel-local reading.",
        )
    if has_context:
        return (
            "subgroup_or_breadth_context_review",
            "subgroup or broad co-drop context exists; keep as context until paired with stronger local evidence.",
        )
    if has_recovery_pressure and sync_bucket in {"", "panel_local_or_weak_synchrony"}:
        return (
            "local_signal_morphology_review",
            f"recovery morphology pressure exists with weak common-cause context: {recovery_bucket}.",
        )
    if has_blocker:
        return (
            "report_entry_blocker_review",
            f"report-lane friction remains visible: {blocker}.",
        )
    return (
        "single_or_weak_axis_context_review",
        "available axes do not yet align into a stronger review focus.",
    )


def build_detail(friction_df: pd.DataFrame, recovery_df: pd.DataFrame, common_df: pd.DataFrame) -> pd.DataFrame:
    detail = pd.merge(friction_df, recovery_df, on=["site", "panel_id"], how="outer")
    detail = pd.merge(detail, common_df, on=["site", "panel_id"], how="outer")

    for col in ["has_friction_axis", "has_recovery_axis", "has_common_cause_axis"]:
        if col not in detail.columns:
            detail[col] = 0
        detail[col] = pd.to_numeric(detail.get(col, 0), errors="coerce").fillna(0).astype(int)
    detail["axis_presence_count"] = detail[["has_friction_axis", "has_recovery_axis", "has_common_cause_axis"]].sum(axis=1)

    fill_text_cols = [
        "friction_direct_families",
        "friction_blocker_types",
        "friction_best_lanes",
        "recovery_bucket",
        "recovery_best_report_lane",
        "synchrony_bucket",
        "synchrony_best_report_lane",
    ]
    for col in fill_text_cols:
        if col not in detail.columns:
            detail[col] = ""
        detail[col] = detail[col].fillna("").map(normalize_text)
    numeric_cols = [
        "friction_direct_row_count",
        "friction_group_off_row_count",
        "friction_site_event_row_count",
        "recovery_row_count",
        "re_drop_row_count",
        "recovered_sustained_row_count",
        "common_cause_row_count",
        "site_event_row_count",
        "group_off_row_count",
        "subgroup_common_cause_row_count",
        "prefault_B_overlap_row_count",
        "co_drop_hint_row_count",
        "max_co_drop_frac",
    ]
    for col in numeric_cols:
        if col not in detail.columns:
            detail[col] = 0
        detail[col] = pd.to_numeric(detail[col], errors="coerce").fillna(0)

    strong_buckets = {"site_event_synchrony", "group_off_synchrony", "prefault_B_common_cause_overlap"}
    context_buckets = {"subgroup_synchrony_candidate", "co_drop_breadth_hint"}
    recovery_pressure_buckets = {"re_drop_cycle", "persistent_non_recovery", "sustained_recovery"}
    detail["strong_common_cause_flag"] = detail["synchrony_bucket"].isin(strong_buckets).astype(int)
    detail["subgroup_or_breadth_context_flag"] = detail["synchrony_bucket"].isin(context_buckets).astype(int)
    detail["local_or_weak_synchrony_flag"] = (
        detail["synchrony_bucket"].eq("panel_local_or_weak_synchrony") | detail["synchrony_bucket"].eq("")
    ).astype(int)
    detail["report_entry_blocker_flag"] = detail["friction_blocker_types"].ne("").astype(int)
    detail["recovery_morphology_pressure_flag"] = detail["recovery_bucket"].isin(recovery_pressure_buckets).astype(int)

    buckets = detail.apply(lambda row: classify_review(row.to_dict()), axis=1)
    detail["review_focus_bucket"] = [bucket for bucket, _note in buckets]
    detail["review_note"] = [note for _bucket, note in buckets]

    return detail.reindex(columns=DETAIL_COLS).sort_values(["review_focus_bucket", "site", "panel_id"], kind="stable")


def build_summary(detail_df: pd.DataFrame) -> pd.DataFrame:
    if detail_df.empty:
        return pd.DataFrame(columns=SUMMARY_COLS)
    summary = (
        detail_df.groupby(["review_focus_bucket", "site"], as_index=False)
        .agg(
            panels=("panel_id", "nunique"),
            panels_with_friction_axis=("has_friction_axis", "sum"),
            panels_with_recovery_axis=("has_recovery_axis", "sum"),
            panels_with_common_cause_axis=("has_common_cause_axis", "sum"),
            panels_with_strong_common_cause=("strong_common_cause_flag", "sum"),
            panels_with_report_entry_blocker=("report_entry_blocker_flag", "sum"),
            panels_with_recovery_pressure=("recovery_morphology_pressure_flag", "sum"),
            total_common_cause_rows=("common_cause_row_count", "sum"),
            max_co_drop_frac=("max_co_drop_frac", "max"),
        )
    )
    return summary.reindex(columns=SUMMARY_COLS).sort_values(["review_focus_bucket", "site"], kind="stable")


def manifest_counts(manifest_df: pd.DataFrame, family: str) -> tuple[int, int]:
    if manifest_df.empty or "evidence_family" not in manifest_df.columns:
        return 0, 0
    family_df = manifest_df.loc[manifest_df["evidence_family"].eq(family)]
    existing = pd.to_numeric(family_df.get("artifact_exists", 0), errors="coerce").fillna(0).astype(int)
    return int(len(family_df)), int(existing.sum())


def build_sync_status(args: argparse.Namespace) -> pd.DataFrame:
    manifest_df = read_csv(args.manifest_root / MANIFEST_DETAIL_NAME, required=False)
    registry_specs = [
        (
            "report_entry_friction_axis",
            "evidence_axis",
            args.friction_root / FRICTION_DETAIL_NAME,
            "report_entry_friction_axis",
            "report-entry friction detail exists and should be indexed by manifest.",
        ),
        (
            "recovery_recurrence_axis",
            "evidence_axis",
            args.recovery_root / RECOVERY_DETAIL_NAME,
            "recovery_recurrence_axis",
            "recovery/recurrence detail exists and should be indexed by manifest.",
        ),
        (
            "common_cause_synchrony_axis",
            "evidence_axis",
            args.common_cause_root / COMMON_CAUSE_DETAIL_NAME,
            "common_cause_synchrony_axis",
            "common-cause synchrony detail exists and should be indexed by manifest.",
        ),
        (
            "repo_role_boundary_manifest",
            "cleanup_registry",
            args.role_root / ROLE_MANIFEST_NAME,
            "",
            "role boundary manifest is a cleanup map, not an evidence-family row.",
        ),
        (
            "repo_mirror_boundary_manifest",
            "cleanup_registry",
            args.mirror_root / MIRROR_MANIFEST_NAME,
            "",
            "mirror boundary manifest is a cleanup map, not an evidence-family row.",
        ),
        (
            "repo_active_builder_entrypoint_registry",
            "cleanup_registry",
            args.builder_registry_root / BUILDER_REGISTRY_NAME,
            "",
            "builder registry is a cleanup map, not an evidence-family row.",
        ),
    ]
    rows: list[dict[str, object]] = []
    for item, family, path, manifest_family, note in registry_specs:
        exists = int(path.exists())
        registry_rows = 0
        if exists:
            registry_rows = len(read_csv(path))
        manifest_rows, manifest_existing = manifest_counts(manifest_df, manifest_family)
        if family == "evidence_axis":
            sync_status = "synced" if exists and manifest_rows >= 2 and manifest_existing >= 2 else "manifest_review_needed"
        else:
            sync_status = "available_cleanup_map" if exists and registry_rows > 0 else "missing_cleanup_map"
        rows.append(
            {
                "sync_item": item,
                "sync_family": family,
                "expected_path": str(path),
                "artifact_exists": exists,
                "manifest_rows": manifest_rows,
                "manifest_existing_rows": manifest_existing,
                "registry_rows": registry_rows,
                "sync_status": sync_status,
                "sync_note": note,
            }
        )
    return pd.DataFrame(rows, columns=SYNC_COLS)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    friction_df = aggregate_friction(read_csv(args.friction_root / FRICTION_DETAIL_NAME))
    recovery_df = aggregate_recovery(read_csv(args.recovery_root / RECOVERY_DETAIL_NAME))
    common_df = aggregate_common_cause(read_csv(args.common_cause_root / COMMON_CAUSE_DETAIL_NAME))

    detail_df = build_detail(friction_df, recovery_df, common_df)
    summary_df = build_summary(detail_df)
    sync_df = build_sync_status(args)

    detail_df.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    sync_df.to_csv(args.output_dir / SYNC_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
