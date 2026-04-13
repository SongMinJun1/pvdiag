#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import build_panel_day_engine_run_ranker_v2_holdout_audit as holdout_base

VALUE_PANELS_NAME = "panel_day_engine_operator_secondary_discovery_value_panels_v1.csv"
CLUSTER_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_cluster_rollup_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_secondary_discovery_cluster_rollup_summary_v1.csv"

PANEL_KEY_COLS = ["site", "panel_id"]
CHAIN_GAP_DAYS = 3

REQUIRED_VALUE_PANEL_COLS = [
    "site",
    "panel_id",
    "representative_run_start_date",
    "representative_run_end_date",
    "representative_run_day_count",
    "representative_electrical_core_minus_broadshape_050",
    "representative_logistic_v3_discovery_score",
    "any_future_fault_linked_ref_flag",
    "any_future_truth_linked_ref_flag",
    "value_panel_reason_ko",
]

CLUSTER_COLS = [
    "site",
    "cluster_id",
    "cluster_start_date",
    "cluster_end_date",
    "cluster_span_days",
    "panel_count",
    "panel_ids_csv",
    "representative_panel_id",
    "representative_run_start_date",
    "representative_run_end_date",
    "representative_run_day_count",
    "representative_electrical_core_minus_broadshape_050",
    "representative_logistic_v3_discovery_score",
    "max_electrical_core_minus_broadshape_050_in_cluster",
    "max_logistic_v3_discovery_score_in_cluster",
    "future_fault_linked_ref_panel_count",
    "future_truth_linked_ref_panel_count",
    "any_future_fault_linked_ref_flag",
    "any_future_truth_linked_ref_flag",
    "cluster_reason_ko",
]

SUMMARY_COLS = [
    "record_type",
    "site",
    "value_panel_count",
    "cluster_count",
    "panel_reduction_count",
    "panel_reduction_rate",
    "clusters_with_future_fault_linked_ref_count",
    "clusters_with_future_truth_linked_ref_count",
    "max_panels_in_one_cluster",
    "median_panels_per_cluster",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Roll up secondary discovery value panels into site-time clusters."
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


def normalize_flag(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).gt(0).astype(int)


def normalize_panel_keys(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["site"] = out["site"].map(holdout_base.normalize_text)
    out["panel_id"] = out["panel_id"].map(holdout_base.normalize_text)
    return out


def ensure_unique_panels(df: pd.DataFrame, name: str) -> None:
    if df.duplicated(subset=PANEL_KEY_COLS).any():
        dup_df = df.loc[df.duplicated(subset=PANEL_KEY_COLS, keep=False), PANEL_KEY_COLS].drop_duplicates()
        raise SystemExit(f"{name} must be unique by {PANEL_KEY_COLS}, got duplicates: {dup_df.to_dict('records')}")


def date_to_text(value: pd.Timestamp) -> str:
    if pd.isna(value):
        return ""
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def load_value_panels(root: Path) -> pd.DataFrame:
    path = root / "_share" / VALUE_PANELS_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_VALUE_PANEL_COLS, path.name)
    df = normalize_panel_keys(df)
    ensure_unique_panels(df, path.name)

    df["representative_run_start_date"] = pd.to_datetime(df["representative_run_start_date"], errors="coerce")
    df["representative_run_end_date"] = pd.to_datetime(df["representative_run_end_date"], errors="coerce")
    if df["representative_run_start_date"].isna().any() or df["representative_run_end_date"].isna().any():
        raise SystemExit(f"{path.name} contains invalid representative dates")
    df["representative_run_day_count"] = pd.to_numeric(df["representative_run_day_count"], errors="coerce")
    df["representative_electrical_core_minus_broadshape_050"] = pd.to_numeric(
        df["representative_electrical_core_minus_broadshape_050"], errors="coerce"
    )
    df["representative_logistic_v3_discovery_score"] = pd.to_numeric(
        df["representative_logistic_v3_discovery_score"], errors="coerce"
    )
    df["any_future_fault_linked_ref_flag"] = normalize_flag(df["any_future_fault_linked_ref_flag"])
    df["any_future_truth_linked_ref_flag"] = normalize_flag(df["any_future_truth_linked_ref_flag"])
    return df.copy()


def select_representative_panel(cluster_df: pd.DataFrame) -> pd.Series:
    ranked = cluster_df.sort_values(
        [
            "representative_electrical_core_minus_broadshape_050",
            "representative_logistic_v3_discovery_score",
            "representative_run_end_date",
            "representative_run_day_count",
            "representative_run_start_date",
            "panel_id",
        ],
        ascending=[False, False, False, False, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    return ranked.iloc[0]


def build_cluster_reason(cluster_df: pd.DataFrame, fault_count: int, truth_count: int) -> str:
    if len(cluster_df) > 1:
        if fault_count > 0:
            return "동일 site 인접 시점 value panel을 묶은 cluster이며 retrospective fault linkage reference가 포함됨"
        if truth_count > 0:
            return "동일 site 인접 시점 value panel을 묶은 cluster이며 retrospective truth linkage reference가 포함됨"
        return "동일 site 인접 시점 value panel을 하나의 operator cluster로 압축"
    if fault_count > 0:
        return "단일 value panel cluster이며 retrospective fault linkage reference가 포함됨"
    if truth_count > 0:
        return "단일 value panel cluster이며 retrospective truth linkage reference가 포함됨"
    return "단일 value panel cluster"


def summarize_cluster(site: str, cluster_index: int, cluster_df: pd.DataFrame) -> dict[str, object]:
    cluster_start = cluster_df["representative_run_start_date"].min()
    cluster_end = cluster_df["representative_run_end_date"].max()
    representative = select_representative_panel(cluster_df)
    panel_count = int(len(cluster_df))
    fault_count = int(cluster_df["any_future_fault_linked_ref_flag"].sum())
    truth_count = int(cluster_df["any_future_truth_linked_ref_flag"].sum())
    panel_ids_csv = ",".join(
        cluster_df.sort_values(
            ["representative_run_start_date", "representative_run_end_date", "panel_id"],
            ascending=[True, True, True],
            kind="mergesort",
        )["panel_id"].astype(str)
    )
    return {
        "site": site,
        "cluster_id": f"{site}_cluster_{cluster_index:03d}",
        "cluster_start_date": date_to_text(cluster_start),
        "cluster_end_date": date_to_text(cluster_end),
        "cluster_span_days": int((cluster_end - cluster_start).days + 1),
        "panel_count": panel_count,
        "panel_ids_csv": panel_ids_csv,
        "representative_panel_id": representative["panel_id"],
        "representative_run_start_date": date_to_text(representative["representative_run_start_date"]),
        "representative_run_end_date": date_to_text(representative["representative_run_end_date"]),
        "representative_run_day_count": int(representative["representative_run_day_count"]),
        "representative_electrical_core_minus_broadshape_050": float(
            representative["representative_electrical_core_minus_broadshape_050"]
        ),
        "representative_logistic_v3_discovery_score": float(
            representative["representative_logistic_v3_discovery_score"]
        ),
        "max_electrical_core_minus_broadshape_050_in_cluster": float(
            cluster_df["representative_electrical_core_minus_broadshape_050"].max()
        ),
        "max_logistic_v3_discovery_score_in_cluster": float(
            cluster_df["representative_logistic_v3_discovery_score"].max()
        ),
        "future_fault_linked_ref_panel_count": fault_count,
        "future_truth_linked_ref_panel_count": truth_count,
        "any_future_fault_linked_ref_flag": int(fault_count > 0),
        "any_future_truth_linked_ref_flag": int(truth_count > 0),
        "cluster_reason_ko": build_cluster_reason(cluster_df, fault_count, truth_count),
    }


def cluster_site_rows(site_df: pd.DataFrame) -> list[pd.DataFrame]:
    sorted_df = site_df.sort_values(
        ["representative_run_start_date", "representative_run_end_date", "panel_id"],
        ascending=[True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    clusters: list[pd.DataFrame] = []
    current_rows: list[int] = []
    current_end: pd.Timestamp | None = None

    for idx, row in sorted_df.iterrows():
        row_start = pd.Timestamp(row["representative_run_start_date"])
        row_end = pd.Timestamp(row["representative_run_end_date"])
        if not current_rows:
            current_rows = [idx]
            current_end = row_end
            continue
        assert current_end is not None
        if row_start <= current_end + pd.Timedelta(days=CHAIN_GAP_DAYS):
            current_rows.append(idx)
            current_end = max(current_end, row_end)
            continue
        clusters.append(sorted_df.loc[current_rows].copy())
        current_rows = [idx]
        current_end = row_end

    if current_rows:
        clusters.append(sorted_df.loc[current_rows].copy())
    return clusters


def build_cluster_rollup(value_panels_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for site in sorted(value_panels_df["site"].dropna().unique()):
        site_df = value_panels_df.loc[value_panels_df["site"].eq(site)].copy()
        site_clusters = cluster_site_rows(site_df)
        for cluster_index, cluster_df in enumerate(site_clusters, start=1):
            rows.append(summarize_cluster(site, cluster_index, cluster_df))

    cluster_df = pd.DataFrame(rows, columns=CLUSTER_COLS)
    if cluster_df.empty:
        return cluster_df
    cluster_df = cluster_df.sort_values(
        [
            "max_electrical_core_minus_broadshape_050_in_cluster",
            "panel_count",
            "cluster_span_days",
            "site",
            "cluster_id",
        ],
        ascending=[False, False, False, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    return cluster_df.loc[:, CLUSTER_COLS].copy()


def build_summary(value_panels_df: pd.DataFrame, cluster_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def summarize(site: str, record_type: str) -> None:
        if record_type == "overall":
            value_subset = value_panels_df.copy()
            cluster_subset = cluster_df.copy()
        else:
            value_subset = value_panels_df.loc[value_panels_df["site"].eq(site)].copy()
            cluster_subset = cluster_df.loc[cluster_df["site"].eq(site)].copy()
        value_panel_count = int(len(value_subset))
        cluster_count = int(len(cluster_subset))
        panel_reduction_count = int(value_panel_count - cluster_count)
        panel_reduction_rate = (panel_reduction_count / value_panel_count) if value_panel_count > 0 else None
        rows.append(
            {
                "record_type": record_type,
                "site": site,
                "value_panel_count": value_panel_count,
                "cluster_count": cluster_count,
                "panel_reduction_count": panel_reduction_count,
                "panel_reduction_rate": panel_reduction_rate,
                "clusters_with_future_fault_linked_ref_count": int(cluster_subset["any_future_fault_linked_ref_flag"].sum())
                if not cluster_subset.empty
                else 0,
                "clusters_with_future_truth_linked_ref_count": int(cluster_subset["any_future_truth_linked_ref_flag"].sum())
                if not cluster_subset.empty
                else 0,
                "max_panels_in_one_cluster": int(cluster_subset["panel_count"].max()) if not cluster_subset.empty else 0,
                "median_panels_per_cluster": float(cluster_subset["panel_count"].median()) if not cluster_subset.empty else None,
                "note_ko": "site-time chaining(3일)으로 secondary discovery value panel을 cluster 단위로 압축",
            }
        )

    summarize("", "overall")
    for site in sorted(value_panels_df["site"].dropna().unique()):
        summarize(site, "site")
    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def save_outputs(root: Path, cluster_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    cluster_df.to_csv(share_dir / CLUSTER_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    value_panels_df = load_value_panels(root)
    cluster_df = build_cluster_rollup(value_panels_df)
    summary_df = build_summary(value_panels_df, cluster_df)
    save_outputs(root, cluster_df, summary_df)


if __name__ == "__main__":
    main()
