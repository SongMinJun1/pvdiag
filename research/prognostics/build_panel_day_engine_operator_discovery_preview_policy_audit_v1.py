#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import build_panel_day_engine_run_ranker_v2_holdout_audit as holdout_base

VALUE_PANELS_NAME = "panel_day_engine_operator_secondary_discovery_value_panels_v1.csv"
PREVIEW_SUMMARY_NAME = "panel_day_engine_operator_attention_plus_discovery_preview_summary_v1.csv"

SWEEP_OUTPUT_NAME = "panel_day_engine_operator_discovery_preview_policy_sweep_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_operator_discovery_preview_policy_summary_v1.csv"
RECOMMENDATION_OUTPUT_NAME = "panel_day_engine_operator_discovery_preview_policy_recommendation_v1.csv"

KEY_COLS = ["site", "panel_id"]
SCORE_COL = "representative_electrical_core_minus_broadshape_050"
FAULT_COL = "any_future_fault_linked_ref_flag"
TRUTH_COL = "any_future_truth_linked_ref_flag"

REQUIRED_VALUE_PANEL_COLS = [*KEY_COLS, SCORE_COL, FAULT_COL, TRUTH_COL]
REQUIRED_PREVIEW_SUMMARY_COLS = [
    "record_type",
    "secondary_value_panel_count",
    "secondary_incremental_fault_or_truth_linked_panel_count",
]

SCORE_THRESHOLDS = [8, 10, 12, 14]
TOPK_THRESHOLDS = [1, 2, 3, 5]
COMBINED_SCORE_THRESHOLDS = [10, 12]
COMBINED_TOPK_THRESHOLDS = [1, 2, 3]

SWEEP_COLS = [
    "policy_family",
    "policy_spec",
    "selected_panel_count",
    "selected_fault_or_truth_linked_panel_count",
    "selected_fault_or_truth_linked_rate",
    "capture_rate_over_all_secondary_linked_panels",
    "selected_site_count",
    "max_single_site_share",
    "note_ko",
]

SUMMARY_COLS = [*SWEEP_COLS, "recommended_policy_flag"]

RECOMMENDATION_COLS = [
    "recommended_policy_name",
    "recommended_policy_reason_ko",
    "expected_use_ko",
    "caution_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit narrower preview policies for the operator secondary discovery value-panel lane."
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


def safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return float(numerator) / float(denominator)


def load_value_panels(root: Path) -> pd.DataFrame:
    path = root / "_share" / VALUE_PANELS_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_VALUE_PANEL_COLS, path.name)
    df = normalize_panel_keys(df)
    df[SCORE_COL] = pd.to_numeric(df[SCORE_COL], errors="coerce")
    df[FAULT_COL] = normalize_flag(df[FAULT_COL])
    df[TRUTH_COL] = normalize_flag(df[TRUTH_COL])
    df["fault_or_truth_linked_ref_flag"] = df[[FAULT_COL, TRUTH_COL]].max(axis=1).astype(int)
    df = df.sort_values(
        [SCORE_COL, "site", "panel_id"],
        ascending=[False, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    df["site_rank_by_score"] = (
        df.groupby("site", dropna=False).cumcount() + 1
    )
    return df


def load_preview_context(root: Path) -> dict[str, int]:
    path = root / "_share" / PREVIEW_SUMMARY_NAME
    df = holdout_base.drop_repeated_header_rows(read_csv(path))
    ensure_columns(df, REQUIRED_PREVIEW_SUMMARY_COLS, path.name)
    df["record_type"] = df["record_type"].map(holdout_base.normalize_text)
    overall_df = df.loc[df["record_type"].eq("overall")].copy()
    if len(overall_df) != 1:
        raise SystemExit(f"{path.name} must contain exactly one overall row")
    row = overall_df.iloc[0]
    return {
        "current_preview_secondary_panel_count": int(pd.to_numeric(row["secondary_value_panel_count"], errors="coerce")),
        "current_preview_incremental_linked_count": int(
            pd.to_numeric(row["secondary_incremental_fault_or_truth_linked_panel_count"], errors="coerce")
        ),
    }


def build_policy_specs() -> list[dict[str, object]]:
    specs: list[dict[str, object]] = []
    for threshold in SCORE_THRESHOLDS:
        specs.append(
            {
                "policy_family": "score_threshold",
                "policy_spec": f"{SCORE_COL}>={threshold}",
                "threshold": float(threshold),
            }
        )
    for top_k in TOPK_THRESHOLDS:
        specs.append(
            {
                "policy_family": "topk_per_site",
                "policy_spec": f"top_{top_k}_per_site_by_{SCORE_COL}",
                "top_k": int(top_k),
            }
        )
    for threshold in COMBINED_SCORE_THRESHOLDS:
        for top_k in COMBINED_TOPK_THRESHOLDS:
            specs.append(
                {
                    "policy_family": "threshold_plus_topk_per_site",
                    "policy_spec": f"{SCORE_COL}>={threshold}&top_{top_k}_per_site_by_{SCORE_COL}",
                    "threshold": float(threshold),
                    "top_k": int(top_k),
                }
            )
    return specs


def select_policy_rows(value_df: pd.DataFrame, spec: dict[str, object]) -> pd.DataFrame:
    family = str(spec["policy_family"])
    if family == "score_threshold":
        return value_df.loc[value_df[SCORE_COL].ge(float(spec["threshold"]))].copy()
    if family == "topk_per_site":
        return value_df.loc[value_df["site_rank_by_score"].le(int(spec["top_k"]))].copy()
    if family == "threshold_plus_topk_per_site":
        return value_df.loc[
            value_df[SCORE_COL].ge(float(spec["threshold"]))
            & value_df["site_rank_by_score"].le(int(spec["top_k"]))
        ].copy()
    raise SystemExit(f"unsupported policy family: {family}")


def max_single_site_share(selected_df: pd.DataFrame) -> float | None:
    if selected_df.empty:
        return None
    site_counts = selected_df.groupby("site", dropna=False).size()
    if site_counts.empty:
        return None
    return float(site_counts.max()) / float(len(selected_df))


def evaluate_policy(
    value_df: pd.DataFrame,
    spec: dict[str, object],
    total_linked_count: int,
    preview_context: dict[str, int],
) -> dict[str, object]:
    selected_df = select_policy_rows(value_df, spec)
    selected_count = int(len(selected_df))
    linked_count = int(selected_df["fault_or_truth_linked_ref_flag"].sum()) if selected_count else 0
    selected_site_count = int(selected_df["site"].nunique()) if selected_count else 0
    current_preview_count = int(preview_context["current_preview_secondary_panel_count"])
    preview_incremental_linked_count = int(preview_context["current_preview_incremental_linked_count"])
    note_parts = [
        f"current preview {current_preview_count}개 대비 {selected_count}개",
        f"linked {linked_count}/{total_linked_count}",
    ]
    if preview_incremental_linked_count > 0:
        note_parts.append(f"current preview incremental linked ref={preview_incremental_linked_count}")
    return {
        "policy_family": str(spec["policy_family"]),
        "policy_spec": str(spec["policy_spec"]),
        "selected_panel_count": selected_count,
        "selected_fault_or_truth_linked_panel_count": linked_count,
        "selected_fault_or_truth_linked_rate": safe_rate(linked_count, selected_count),
        "capture_rate_over_all_secondary_linked_panels": safe_rate(linked_count, total_linked_count),
        "selected_site_count": selected_site_count,
        "max_single_site_share": max_single_site_share(selected_df),
        "note_ko": ", ".join(note_parts),
    }


def policy_sort_frame(df: pd.DataFrame) -> pd.DataFrame:
    ranked = df.copy()
    ranked["_capture"] = pd.to_numeric(ranked["capture_rate_over_all_secondary_linked_panels"], errors="coerce").fillna(-1.0)
    ranked["_linked_rate"] = pd.to_numeric(ranked["selected_fault_or_truth_linked_rate"], errors="coerce").fillna(-1.0)
    ranked["_selected_count"] = pd.to_numeric(ranked["selected_panel_count"], errors="coerce").fillna(10**9)
    ranked["_max_share"] = pd.to_numeric(ranked["max_single_site_share"], errors="coerce").fillna(10**9)
    return ranked


def choose_recommended_policy(summary_df: pd.DataFrame) -> pd.Series:
    ranked = policy_sort_frame(summary_df)
    eligible = ranked.loc[ranked["_capture"].ge(0.75)].copy()
    if not eligible.empty:
        eligible = eligible.sort_values(
            ["_linked_rate", "_selected_count", "_max_share", "policy_family", "policy_spec"],
            ascending=[False, True, True, True, True],
            kind="mergesort",
        )
        return eligible.iloc[0]

    fallback = ranked.loc[ranked["_selected_count"].le(8)].copy()
    if fallback.empty:
        fallback = ranked.copy()
    fallback = fallback.sort_values(
        ["_linked_rate", "_capture", "_selected_count", "_max_share", "policy_family", "policy_spec"],
        ascending=[False, False, True, True, True, True],
        kind="mergesort",
    )
    return fallback.iloc[0]


def build_outputs(value_df: pd.DataFrame, preview_context: dict[str, int]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    total_linked_count = int(value_df["fault_or_truth_linked_ref_flag"].sum())
    sweep_rows = [
        evaluate_policy(value_df, spec, total_linked_count, preview_context)
        for spec in build_policy_specs()
    ]
    sweep_df = pd.DataFrame(sweep_rows, columns=SWEEP_COLS)
    recommended_row = choose_recommended_policy(sweep_df)
    summary_df = sweep_df.copy()
    summary_df["recommended_policy_flag"] = (
        summary_df["policy_family"].eq(str(recommended_row["policy_family"]))
        & summary_df["policy_spec"].eq(str(recommended_row["policy_spec"]))
    ).astype(int)
    summary_df = summary_df.loc[:, SUMMARY_COLS].copy()

    recommended_policy_name = f"{recommended_row['policy_family']}|{recommended_row['policy_spec']}"
    capture = float(pd.to_numeric(recommended_row["capture_rate_over_all_secondary_linked_panels"], errors="coerce"))
    linked_rate = float(pd.to_numeric(recommended_row["selected_fault_or_truth_linked_rate"], errors="coerce"))
    selected_count = int(pd.to_numeric(recommended_row["selected_panel_count"], errors="coerce"))
    max_share = float(pd.to_numeric(recommended_row["max_single_site_share"], errors="coerce"))
    recommendation_df = pd.DataFrame(
        [
            {
                "recommended_policy_name": recommended_policy_name,
                "recommended_policy_reason_ko": (
                    f"{recommended_policy_name} 정책이 capture={capture:.3f}, linked_rate={linked_rate:.3f}, "
                    f"selected={selected_count}, max_single_site_share={max_share:.3f}로 "
                    "current preview를 좁히면서 retrospective linked value를 가장 균형 있게 보존한다."
                ),
                "expected_use_ko": (
                    "secondary discovery preview를 operator workflow에 더 좁게 붙일 경우 우선 적용해볼 simple current-state narrowing policy"
                ),
                "caution_ko": (
                    "future fault/truth reference는 평가용이며, 실제 selection은 representative electrical score와 site top-K 같은 current-state rule만 사용해야 한다."
                ),
            }
        ],
        columns=RECOMMENDATION_COLS,
    )
    return sweep_df, summary_df, recommendation_df


def save_outputs(root: Path, sweep_df: pd.DataFrame, summary_df: pd.DataFrame, recommendation_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    sweep_df.to_csv(share_dir / SWEEP_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    recommendation_df.to_csv(share_dir / RECOMMENDATION_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    value_df = load_value_panels(root)
    preview_context = load_preview_context(root)
    sweep_df, summary_df, recommendation_df = build_outputs(value_df, preview_context)
    save_outputs(root, sweep_df, summary_df, recommendation_df)


if __name__ == "__main__":
    main()
