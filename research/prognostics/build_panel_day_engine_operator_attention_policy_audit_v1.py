#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

BASELINE_ONLY_NAME = "panel_day_engine_operator_attention_now_v1.csv"
DISCOVERY_PANEL_NAME = "panel_day_engine_operator_attention_plus_discovery_preview_v1.csv"
DISCOVERY_NARROW_NAME = "panel_day_engine_operator_attention_plus_discovery_preview_narrow_v1.csv"
DISCOVERY_CLUSTER_NAME = "panel_day_engine_operator_attention_plus_discovery_cluster_preview_v1.csv"

SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_attention_policy_summary_v1.csv"
RECOMMENDATION_OUTPUT_NAME = "panel_day_engine_operator_attention_policy_recommendation_v1.csv"

POLICY_ORDER = [
    "baseline_only",
    "baseline_plus_discovery_panel",
    "baseline_plus_discovery_narrow",
    "baseline_plus_discovery_cluster",
]

SUMMARY_COLS = [
    "policy_name",
    "total_item_count",
    "queue_run_count",
    "watch_now_panel_count",
    "discovery_panel_count",
    "discovery_cluster_count",
    "fault_linked_ref_count",
    "truth_linked_ref_count",
    "fault_or_truth_linked_ref_count",
    "incremental_fault_or_truth_linked_ref_count_vs_baseline",
    "incremental_fault_or_truth_linked_ref_rate_vs_baseline",
    "max_single_site_share",
    "note_ko",
]

RECOMMENDATION_COLS = [
    "recommended_policy_name",
    "recommended_policy_reason_ko",
    "expected_use_ko",
    "caution_ko",
]

BASELINE_REQUIRED_COLS = [
    "attention_class",
    "site",
    "attention_any_future_fault_linked_ref_flag",
    "attention_any_future_truth_linked_ref_flag",
]

PREVIEW_REQUIRED_COMMON_COLS = [
    "preview_attention_class",
    "site",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare operator attention policy views and recommend the default workflow."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the project root.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def normalize_flag(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).gt(0).astype(int)


def safe_rate(numerator: int, denominator: int) -> float:
    return float(numerator) / float(max(denominator, 1))


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def drop_repeated_header_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    header_mask = pd.Series(True, index=df.index)
    for col in df.columns:
        header_mask &= df[col].map(normalize_text).eq(col)
    return df.loc[~header_mask].reset_index(drop=True)


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def load_baseline_policy(root: Path) -> pd.DataFrame:
    path = root / "_share" / BASELINE_ONLY_NAME
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, BASELINE_REQUIRED_COLS, path.name)
    normalized = pd.DataFrame(
        {
            "site": df["site"].map(normalize_text),
            "attention_class": df["attention_class"].map(normalize_text),
            "linked_ref_flag": normalize_flag(df["attention_any_future_fault_linked_ref_flag"]),
            "truth_ref_flag": normalize_flag(df["attention_any_future_truth_linked_ref_flag"]),
        }
    )
    return normalized


def load_preview_policy(root: Path, file_name: str) -> pd.DataFrame:
    path = root / "_share" / file_name
    df = drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, PREVIEW_REQUIRED_COMMON_COLS, path.name)
    linked_col = "linked_ref_flag" if "linked_ref_flag" in df.columns else "attention_any_future_fault_linked_ref_flag"
    truth_col = "truth_ref_flag" if "truth_ref_flag" in df.columns else "attention_any_future_truth_linked_ref_flag"
    ensure_columns(df, [linked_col, truth_col], path.name)
    normalized = pd.DataFrame(
        {
            "site": df["site"].map(normalize_text),
            "attention_class": df["preview_attention_class"].map(normalize_text),
            "linked_ref_flag": normalize_flag(df[linked_col]),
            "truth_ref_flag": normalize_flag(df[truth_col]),
        }
    )
    return normalized


def load_policy_frames(root: Path) -> dict[str, pd.DataFrame]:
    return {
        "baseline_only": load_baseline_policy(root),
        "baseline_plus_discovery_panel": load_preview_policy(root, DISCOVERY_PANEL_NAME),
        "baseline_plus_discovery_narrow": load_preview_policy(root, DISCOVERY_NARROW_NAME),
        "baseline_plus_discovery_cluster": load_preview_policy(root, DISCOVERY_CLUSTER_NAME),
    }


def max_single_site_share(policy_df: pd.DataFrame) -> float | None:
    if policy_df.empty:
        return None
    site_counts = policy_df.groupby("site", dropna=False).size()
    if site_counts.empty:
        return None
    return float(site_counts.max()) / float(len(policy_df))


def policy_note(policy_name: str, row: dict[str, object]) -> str:
    if policy_name == "baseline_only":
        return "현재 queue/watch baseline만 사용하는 operator attention view"
    if policy_name == "baseline_plus_discovery_panel":
        return (
            f"baseline queue/watch에 discovery panel {int(row['discovery_panel_count'])}건을 그대로 추가한 확장 view"
        )
    if policy_name == "baseline_plus_discovery_narrow":
        return (
            f"baseline queue/watch에 recommended narrow discovery panel {int(row['discovery_panel_count'])}건만 추가한 축소 view"
        )
    return f"baseline queue/watch에 discovery cluster {int(row['discovery_cluster_count'])}건을 추가해 panel load를 압축한 view"


def summarize_policy(
    policy_name: str,
    policy_df: pd.DataFrame,
    *,
    baseline_total_count: int,
    baseline_fault_or_truth_count: int,
) -> dict[str, object]:
    total_item_count = int(len(policy_df))
    queue_run_count = int(policy_df["attention_class"].eq("queue_run").sum())
    watch_now_panel_count = int(policy_df["attention_class"].eq("watch_now_panel").sum())
    discovery_panel_count = int(policy_df["attention_class"].eq("secondary_value_panel").sum())
    discovery_cluster_count = int(policy_df["attention_class"].eq("secondary_value_cluster").sum())
    fault_linked_ref_count = int(policy_df["linked_ref_flag"].sum())
    truth_linked_ref_count = int(policy_df["truth_ref_flag"].sum())
    fault_or_truth_mask = policy_df["linked_ref_flag"].eq(1) | policy_df["truth_ref_flag"].eq(1)
    fault_or_truth_linked_ref_count = int(fault_or_truth_mask.sum())
    incremental_fault_or_truth = fault_or_truth_linked_ref_count - baseline_fault_or_truth_count
    extra_item_count = total_item_count - baseline_total_count
    row: dict[str, object] = {
        "policy_name": policy_name,
        "total_item_count": total_item_count,
        "queue_run_count": queue_run_count,
        "watch_now_panel_count": watch_now_panel_count,
        "discovery_panel_count": discovery_panel_count,
        "discovery_cluster_count": discovery_cluster_count,
        "fault_linked_ref_count": fault_linked_ref_count,
        "truth_linked_ref_count": truth_linked_ref_count,
        "fault_or_truth_linked_ref_count": fault_or_truth_linked_ref_count,
        "incremental_fault_or_truth_linked_ref_count_vs_baseline": incremental_fault_or_truth,
        "incremental_fault_or_truth_linked_ref_rate_vs_baseline": safe_rate(
            incremental_fault_or_truth, extra_item_count
        ),
        "max_single_site_share": max_single_site_share(policy_df),
    }
    row["note_ko"] = policy_note(policy_name, row)
    return row


def share_or_high(value: object) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 10.0 if pd.isna(numeric) else float(numeric)


def choose_recommendation(summary_df: pd.DataFrame) -> dict[str, str]:
    lookup = {row["policy_name"]: row for _, row in summary_df.iterrows()}
    baseline = lookup["baseline_only"]
    panel = lookup["baseline_plus_discovery_panel"]
    narrow = lookup["baseline_plus_discovery_narrow"]
    cluster = lookup["baseline_plus_discovery_cluster"]

    baseline_total = int(baseline["total_item_count"])

    def extra_items(row: pd.Series) -> int:
        return max(int(row["total_item_count"]) - baseline_total, 0)

    def gain(row: pd.Series) -> int:
        return int(row["incremental_fault_or_truth_linked_ref_count_vs_baseline"])

    best_added_gain = max(gain(panel), gain(narrow), gain(cluster))
    if best_added_gain <= 0:
        return {
            "recommended_policy_name": "baseline_only",
            "recommended_policy_reason_ko": (
                "추가 preview들이 baseline 대비 retrospective linked proxy를 거의 늘리지 못해 기본 queue/watch workflow를 유지하는 편이 낫다."
            ),
            "expected_use_ko": "현재 baseline attention을 기본 operator workflow로 유지",
            "caution_ko": "linked_ref/truth_ref는 retrospective proxy이며, 실제 운영 selection rule을 뜻하지는 않는다.",
        }

    cluster_compelling = (
        gain(cluster) > 0
        and extra_items(cluster) < extra_items(panel)
        and gain(cluster) >= max(1, (gain(panel) + 1) // 2)
    )
    narrow_nearly_matches_cluster = (
        gain(narrow) >= max(gain(cluster) - 1, 0)
        and extra_items(narrow) < extra_items(cluster)
        and share_or_high(narrow["max_single_site_share"]) <= share_or_high(cluster["max_single_site_share"]) + 0.05
    )

    if cluster_compelling:
        if narrow_nearly_matches_cluster:
            return {
                "recommended_policy_name": "baseline_plus_discovery_narrow",
                "recommended_policy_reason_ko": (
                    f"narrow preview가 baseline 대비 linked proxy +{gain(narrow)}를 유지하면서 total={int(narrow['total_item_count'])}로 "
                    f"cluster view보다 더 가볍게 운영될 수 있어 default workflow 후보로 가장 균형이 좋다."
                ),
                "expected_use_ko": "queue/watch baseline에 recommended narrow discovery panel만 side-by-side로 추가한 기본 workflow",
                "caution_ko": "narrow panel view는 cluster보다 operator reread 부담이 늘 수 있어 site skew를 계속 관찰해야 한다.",
            }
        return {
            "recommended_policy_name": "baseline_plus_discovery_cluster",
            "recommended_policy_reason_ko": (
                f"cluster preview가 baseline 대비 linked proxy +{gain(cluster)}를 유지하면서 total={int(cluster['total_item_count'])}, "
                f"extra={extra_items(cluster)}, max_single_site_share={share_or_high(cluster['max_single_site_share']):.3f}로 "
                "panel view보다 operator load와 site skew를 더 잘 억제한다."
            ),
            "expected_use_ko": "queue/watch baseline에 discovery cluster를 side-by-side로 붙인 기본 operator workflow",
            "caution_ko": "cluster view는 panel-level 세부 문맥을 압축하므로 analyst drill-down이 필요할 때는 panel preview를 함께 봐야 한다.",
        }

    ranked = summary_df.loc[summary_df["policy_name"].ne("baseline_only")].copy()
    ranked["_gain"] = pd.to_numeric(
        ranked["incremental_fault_or_truth_linked_ref_count_vs_baseline"], errors="coerce"
    ).fillna(-10**9)
    ranked["_total"] = pd.to_numeric(ranked["total_item_count"], errors="coerce").fillna(10**9)
    ranked["_share"] = pd.to_numeric(ranked["max_single_site_share"], errors="coerce").fillna(10.0)
    ranked = ranked.sort_values(
        ["_gain", "_total", "_share", "policy_name"],
        ascending=[False, True, True, True],
        kind="mergesort",
    )
    best = ranked.iloc[0]
    if gain(best) <= 1:
        return {
            "recommended_policy_name": "baseline_only",
            "recommended_policy_reason_ko": (
                "추가 view들의 incremental linked proxy gain이 작아, workflow 기본값은 baseline_only가 가장 보수적이다."
            ),
            "expected_use_ko": "현재 baseline attention을 기본 operator workflow로 유지",
            "caution_ko": "supplemental discovery view는 analyst 보조 확인 용도로만 유지하는 편이 안전하다.",
        }
    if best["policy_name"] == "baseline_plus_discovery_narrow":
        return {
            "recommended_policy_name": "baseline_plus_discovery_narrow",
            "recommended_policy_reason_ko": (
                f"narrow preview가 baseline 대비 linked proxy +{gain(best)}를 확보하면서 total={int(best['total_item_count'])}로 "
                "added views 중 가장 균형 잡힌 workflow를 제공한다."
            ),
            "expected_use_ko": "queue/watch baseline에 recommended narrow discovery panel만 추가한 기본 workflow",
            "caution_ko": "panel-level discovery rows가 남아 있어 cluster view보다 site skew가 커질 수 있다.",
        }
    return {
        "recommended_policy_name": "baseline_plus_discovery_panel",
        "recommended_policy_reason_ko": (
            f"full panel preview가 baseline 대비 linked proxy +{gain(best)}로 가장 큰 gain을 제공해 discovery recall을 우선하는 default workflow에 가깝다."
        ),
        "expected_use_ko": "queue/watch baseline에 discovery panel 전체를 추가한 확장 workflow",
        "caution_ko": "panel row 수와 site skew가 커져 operator load가 빠르게 증가할 수 있다.",
    }


def build_outputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    policy_frames = load_policy_frames(root)
    baseline_df = policy_frames["baseline_only"]
    baseline_fault_or_truth_count = int(
        (baseline_df["linked_ref_flag"].eq(1) | baseline_df["truth_ref_flag"].eq(1)).sum()
    )
    baseline_total_count = int(len(baseline_df))

    summary_rows = [
        summarize_policy(
            policy_name,
            policy_frames[policy_name],
            baseline_total_count=baseline_total_count,
            baseline_fault_or_truth_count=baseline_fault_or_truth_count,
        )
        for policy_name in POLICY_ORDER
    ]
    summary = pd.DataFrame(summary_rows, columns=SUMMARY_COLS)
    recommendation = pd.DataFrame(
        [choose_recommendation(summary)],
        columns=RECOMMENDATION_COLS,
    )
    return summary, recommendation


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    summary, recommendation = build_outputs(root)
    summary.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    recommendation.to_csv(share_dir / RECOMMENDATION_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
