#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

RELIABILITY_NAME = "panel_day_engine_project_eval_reliability_v1.csv"
SUPPORT_GAP_NAME = "panel_day_engine_project_eval_support_gap_v1.csv"
SUPPORT_GAP_SUMMARY_NAME = "panel_day_engine_project_eval_support_gap_summary_v1.csv"
FREEZE_CANDIDATES_NAME = "panel_day_engine_project_eval_freeze_candidates_v1.csv"
EVAL_BUCKETS_NAME = "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv"

PLAN_OUTPUT_NAME = "panel_day_engine_project_truth_expansion_plan_v1.csv"
PLAN_SUMMARY_OUTPUT_NAME = "panel_day_engine_project_truth_expansion_plan_summary_v1.csv"
FREEZE_PLAN_OUTPUT_NAME = "panel_day_engine_project_freeze_plan_v1.csv"

PLAN_COLS = [
    "eval_scope",
    "target_name",
    "reliability_class",
    "freeze_recommendation",
    "current_positive_support",
    "current_negative_support",
    "additional_positive_needed_for_5",
    "additional_positive_needed_for_10",
    "current_artifact_candidate_pool_count",
    "requires_new_truth_or_data_flag",
    "expansion_action_class",
    "suggested_collection_unit",
    "suggested_collection_source_ko",
    "priority_rank",
    "expansion_reason_ko",
]

PLAN_SUMMARY_COLS = [
    "expansion_action_class",
    "target_count",
    "total_additional_positive_needed_for_5",
    "total_additional_positive_needed_for_10",
    "requires_new_truth_or_data_count",
    "highest_priority_rank",
    "note_ko",
]

FREEZE_PLAN_COLS = [
    "eval_scope",
    "recommended_target_name",
    "recommended_metric_kind",
    "recommended_f1",
    "recommended_positive_support",
    "recommended_reliability_class",
    "recommended_freeze_recommendation",
    "current_default_decision",
    "freeze_reason_ko",
]

ACTION_PRIORITY_RANK = {
    "collect_new_precursor_truth_cases": 1,
    "collect_new_common_cause_truth_cases": 2,
    "collect_new_abrupt_truth_cases": 3,
    "workflow_validation_not_truth": 4,
    "no_action_proxy": 5,
    "no_action_structural": 6,
}

SCOPE_BUCKET_MAP = {
    "step3_precursor_performance": "precursor_bearing_detectable_now",
    "step4_abrupt_no_precursor": "abrupt_or_no_precursor_now",
    "step4_common_cause_routing": "non_panel_or_common_cause",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a concrete truth/data expansion plan from project evaluation reliability and support-gap audits."
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


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def numeric_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


def numeric_float_or_blank(value: object) -> float | str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return "" if pd.isna(numeric) else float(numeric)


def load_inputs(root: Path) -> dict[str, pd.DataFrame]:
    share_dir = root / "_share"
    frames = {
        "reliability": read_csv(share_dir / RELIABILITY_NAME),
        "support_gap": read_csv(share_dir / SUPPORT_GAP_NAME),
        "support_gap_summary": read_csv(share_dir / SUPPORT_GAP_SUMMARY_NAME),
        "freeze_candidates": read_csv(share_dir / FREEZE_CANDIDATES_NAME),
        "taxonomy": read_csv(share_dir / EVAL_BUCKETS_NAME),
    }

    ensure_columns(
        frames["reliability"],
        ["eval_scope", "target_name", "metric_kind", "reliability_class", "freeze_recommendation", "reliability_reason_ko"],
        RELIABILITY_NAME,
    )
    ensure_columns(
        frames["support_gap"],
        [
            "eval_scope",
            "target_name",
            "reliability_class",
            "freeze_recommendation",
            "current_positive_support",
            "current_negative_support",
            "additional_positive_needed_for_5",
            "additional_positive_needed_for_10",
            "current_artifact_candidate_pool_count",
            "can_reach_5_with_current_artifacts_flag",
            "can_reach_10_with_current_artifacts_flag",
            "support_gap_reason_ko",
        ],
        SUPPORT_GAP_NAME,
    )
    ensure_columns(
        frames["support_gap_summary"],
        ["eval_scope", "note_ko"],
        SUPPORT_GAP_SUMMARY_NAME,
    )
    ensure_columns(
        frames["freeze_candidates"],
        [
            "eval_scope",
            "recommended_target_name",
            "recommended_metric_kind",
            "recommended_f1",
            "recommended_positive_support",
            "recommended_reliability_class",
            "recommended_freeze_recommendation",
            "rationale_ko",
        ],
        FREEZE_CANDIDATES_NAME,
    )
    ensure_columns(frames["taxonomy"], ["fault_family_id", "eval_bucket_v2"], EVAL_BUCKETS_NAME)
    return frames


def build_reliability_lookup(reliability_df: pd.DataFrame) -> dict[tuple[str, str], dict[str, str]]:
    lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in reliability_df.to_dict(orient="records"):
        key = (normalize_text(row["eval_scope"]), normalize_text(row["target_name"]))
        if key in lookup:
            raise SystemExit(f"duplicate reliability row: {key}")
        lookup[key] = {
            "metric_kind": normalize_text(row["metric_kind"]),
            "reliability_class": normalize_text(row["reliability_class"]),
            "freeze_recommendation": normalize_text(row["freeze_recommendation"]),
            "reliability_reason_ko": normalize_text(row["reliability_reason_ko"]),
        }
    return lookup


def build_scope_note_lookup(summary_df: pd.DataFrame) -> dict[str, str]:
    return {
        normalize_text(row["eval_scope"]): normalize_text(row["note_ko"])
        for row in summary_df.to_dict(orient="records")
    }


def build_bucket_family_counts(taxonomy_df: pd.DataFrame) -> dict[str, int]:
    taxonomy_df = taxonomy_df.copy()
    taxonomy_df["fault_family_id"] = taxonomy_df["fault_family_id"].map(normalize_text)
    taxonomy_df["eval_bucket_v2"] = taxonomy_df["eval_bucket_v2"].map(normalize_text)
    counts: dict[str, int] = {}
    for bucket, bucket_df in taxonomy_df.groupby("eval_bucket_v2", dropna=False):
        bucket = normalize_text(bucket)
        counts[bucket] = int(bucket_df["fault_family_id"].replace("", pd.NA).dropna().nunique())
    return counts


def expansion_action_class(eval_scope: str) -> str:
    if eval_scope in {"step1_taxonomy", "step2_onset_truth"}:
        return "no_action_structural"
    if eval_scope == "operator_policy_proxy":
        return "workflow_validation_not_truth"
    if eval_scope == "step3_precursor_performance":
        return "collect_new_precursor_truth_cases"
    if eval_scope == "step4_abrupt_no_precursor":
        return "collect_new_abrupt_truth_cases"
    if eval_scope == "step4_common_cause_routing":
        return "collect_new_common_cause_truth_cases"
    return "no_action_proxy"


def suggested_collection_unit(action_class: str) -> str:
    if action_class == "collect_new_precursor_truth_cases":
        return "fault_case"
    if action_class == "collect_new_abrupt_truth_cases":
        return "panel_case"
    if action_class == "collect_new_common_cause_truth_cases":
        return "site_event"
    if action_class in {"workflow_validation_not_truth", "no_action_proxy"}:
        return "workflow_observation"
    return "none"


def suggested_collection_source(action_class: str, eval_scope: str, bucket_family_counts: dict[str, int]) -> str:
    bucket_name = SCOPE_BUCKET_MAP.get(eval_scope, "")
    family_count = bucket_family_counts.get(bucket_name, 0)
    if action_class == "no_action_structural":
        return "추가 truth 수집보다 현재 taxonomy/onset coverage 문서와 support 해석을 유지"
    if action_class == "workflow_validation_not_truth":
        return "operator shadow review, reviewer workload 기록, triage latency 관측 같은 workflow 관찰 데이터"
    if action_class == "collect_new_precursor_truth_cases":
        return (
            f"taxonomy상 {bucket_name} family {family_count}개 기준으로 새 precursor-bearing fault_case truth와 onset corroboration 수집"
        )
    if action_class == "collect_new_abrupt_truth_cases":
        return (
            f"taxonomy상 {bucket_name} family {family_count}개 기준으로 abrupt/no-precursor panel_case anchor truth 수집"
        )
    if action_class == "collect_new_common_cause_truth_cases":
        return (
            f"taxonomy상 {bucket_name} family {family_count}개 기준으로 group-side/common-cause site_event truth 수집"
        )
    return "별도 proxy/workflow validation 해석 유지"


def requires_new_truth_or_data(pool_count_text: str, freeze_recommendation: str) -> int:
    if freeze_recommendation == "freeze_as_current_default":
        return 0
    if pool_count_text == "":
        return 0
    return int(numeric_int(pool_count_text) == 0)


def expansion_reason(
    *,
    action_class: str,
    requires_new_truth_or_data_flag: int,
    current_positive_support: int,
    additional_positive_needed_for_5: int,
    additional_positive_needed_for_10: int,
    can_reach_5: int | None,
    can_reach_10: int | None,
    support_gap_reason_ko: str,
    scope_note_ko: str,
    reliability_reason_ko: str,
) -> str:
    if action_class == "no_action_structural":
        return (
            "현재 row는 structural/support 해석 대상이라 추가 truth collection action보다 coverage 문서 유지가 우선이다. "
            f"{reliability_reason_ko}"
        ).strip()
    if action_class in {"workflow_validation_not_truth", "no_action_proxy"}:
        return (
            "이 row는 operator proxy/workflow 판단 대상이라 truth label 확대보다 workflow validation이 우선이다. "
            f"{support_gap_reason_ko}"
        ).strip()
    if requires_new_truth_or_data_flag == 1:
        return (
            f"current positive support가 {current_positive_support}건이고 current artifact candidate pool이 비어 있어 "
            f"support 5까지 {additional_positive_needed_for_5}건, support 10까지 {additional_positive_needed_for_10}건을 메우려면 "
            f"새 truth/data expansion이 필요하다. {scope_note_ko or support_gap_reason_ko}"
        ).strip()
    if can_reach_10 == 1:
        return (
            f"current artifacts 재정리만으로 support 10까지 도달 가능해, 우선 기존 artifact 정리와 추가 labeling으로 gap을 줄일 수 있다. "
            f"{support_gap_reason_ko}"
        ).strip()
    if can_reach_5 == 1:
        return (
            f"support 5 수준까지는 current artifacts로 보강 가능하지만 support 10까지는 {additional_positive_needed_for_10}건이 더 필요하다. "
            f"{support_gap_reason_ko}"
        ).strip()
    return (
        f"support 5까지 {additional_positive_needed_for_5}건, support 10까지 {additional_positive_needed_for_10}건이 더 필요하며 "
        f"current artifacts만으로는 부족하다. {support_gap_reason_ko}"
    ).strip()


def build_plan_rows(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    reliability_lookup = build_reliability_lookup(frames["reliability"])
    scope_note_lookup = build_scope_note_lookup(frames["support_gap_summary"])
    bucket_family_counts = build_bucket_family_counts(frames["taxonomy"])

    rows: list[dict[str, object]] = []
    for row in frames["support_gap"].to_dict(orient="records"):
        eval_scope = normalize_text(row["eval_scope"])
        target_name = normalize_text(row["target_name"])
        key = (eval_scope, target_name)
        if key not in reliability_lookup:
            raise SystemExit(f"support gap row missing reliability pair: {key}")

        reliability_row = reliability_lookup[key]
        reliability_class = normalize_text(row["reliability_class"])
        freeze_recommendation = normalize_text(row["freeze_recommendation"])
        if reliability_class != reliability_row["reliability_class"]:
            raise SystemExit(f"reliability_class mismatch for {key}")
        if freeze_recommendation != reliability_row["freeze_recommendation"]:
            raise SystemExit(f"freeze_recommendation mismatch for {key}")

        current_positive_support = numeric_int(row["current_positive_support"])
        current_negative_support_text = normalize_text(row["current_negative_support"])
        current_negative_support: int | str = (
            "" if current_negative_support_text == "" else numeric_int(current_negative_support_text)
        )
        additional_positive_needed_for_5 = numeric_int(row["additional_positive_needed_for_5"])
        additional_positive_needed_for_10 = numeric_int(row["additional_positive_needed_for_10"])
        pool_count_text = normalize_text(row["current_artifact_candidate_pool_count"])
        pool_count: int | str = "" if pool_count_text == "" else numeric_int(pool_count_text)
        can_reach_5 = None if normalize_text(row["can_reach_5_with_current_artifacts_flag"]) == "" else numeric_int(row["can_reach_5_with_current_artifacts_flag"])
        can_reach_10 = None if normalize_text(row["can_reach_10_with_current_artifacts_flag"]) == "" else numeric_int(row["can_reach_10_with_current_artifacts_flag"])

        action_class = expansion_action_class(eval_scope)
        priority_rank = ACTION_PRIORITY_RANK[action_class]
        requires_flag = requires_new_truth_or_data(pool_count_text, freeze_recommendation)
        source_ko = suggested_collection_source(action_class, eval_scope, bucket_family_counts)
        rows.append(
            {
                "eval_scope": eval_scope,
                "target_name": target_name,
                "reliability_class": reliability_class,
                "freeze_recommendation": freeze_recommendation,
                "current_positive_support": current_positive_support,
                "current_negative_support": current_negative_support,
                "additional_positive_needed_for_5": additional_positive_needed_for_5,
                "additional_positive_needed_for_10": additional_positive_needed_for_10,
                "current_artifact_candidate_pool_count": pool_count,
                "requires_new_truth_or_data_flag": requires_flag,
                "expansion_action_class": action_class,
                "suggested_collection_unit": suggested_collection_unit(action_class),
                "suggested_collection_source_ko": source_ko,
                "priority_rank": priority_rank,
                "expansion_reason_ko": expansion_reason(
                    action_class=action_class,
                    requires_new_truth_or_data_flag=requires_flag,
                    current_positive_support=current_positive_support,
                    additional_positive_needed_for_5=additional_positive_needed_for_5,
                    additional_positive_needed_for_10=additional_positive_needed_for_10,
                    can_reach_5=can_reach_5,
                    can_reach_10=can_reach_10,
                    support_gap_reason_ko=normalize_text(row["support_gap_reason_ko"]),
                    scope_note_ko=scope_note_lookup.get(eval_scope, ""),
                    reliability_reason_ko=reliability_row["reliability_reason_ko"],
                ),
            }
        )

    plan_df = pd.DataFrame(rows, columns=PLAN_COLS)
    return plan_df.sort_values(
        by=["priority_rank", "eval_scope", "target_name"],
        ascending=[True, True, True],
        kind="stable",
    ).reset_index(drop=True)


def summary_note_for_action(action_class: str) -> str:
    if action_class == "collect_new_precursor_truth_cases":
        return "precursor-bearing scope는 current artifacts만으로 부족해 새 fault_case truth와 onset corroboration 확장이 우선이다."
    if action_class == "collect_new_common_cause_truth_cases":
        return "common-cause scope는 새 site_event truth와 routing evidence 확장이 필요하다."
    if action_class == "collect_new_abrupt_truth_cases":
        return "abrupt/no-precursor scope는 panel_case anchor truth를 더 늘려 low-support 상태를 줄여야 한다."
    if action_class == "workflow_validation_not_truth":
        return "operator proxy scope는 truth expansion보다 workflow validation이 우선이다."
    if action_class == "no_action_proxy":
        return "proxy scope는 별도 workflow 해석을 유지하며 truth expansion action은 우선순위가 낮다."
    return "structural/support scope라 별도 truth expansion action보다는 문서/coverage 유지가 적절하다."


def build_plan_summary(plan_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for action_class, action_df in plan_df.groupby("expansion_action_class", dropna=False):
        action_class = normalize_text(action_class)
        rows.append(
            {
                "expansion_action_class": action_class,
                "target_count": int(len(action_df)),
                "total_additional_positive_needed_for_5": int(pd.to_numeric(action_df["additional_positive_needed_for_5"], errors="coerce").fillna(0).sum()),
                "total_additional_positive_needed_for_10": int(pd.to_numeric(action_df["additional_positive_needed_for_10"], errors="coerce").fillna(0).sum()),
                "requires_new_truth_or_data_count": int(pd.to_numeric(action_df["requires_new_truth_or_data_flag"], errors="coerce").fillna(0).sum()),
                "highest_priority_rank": int(pd.to_numeric(action_df["priority_rank"], errors="coerce").min()),
                "note_ko": summary_note_for_action(action_class),
            }
        )
    summary_df = pd.DataFrame(rows, columns=PLAN_SUMMARY_COLS)
    return summary_df.sort_values(
        by=["highest_priority_rank", "expansion_action_class"],
        ascending=[True, True],
        kind="stable",
    ).reset_index(drop=True)


def freeze_decision(recommended_freeze_recommendation: str) -> str:
    if recommended_freeze_recommendation == "freeze_as_current_default":
        return "freeze_as_current_default"
    if recommended_freeze_recommendation == "freeze_with_caution":
        return "freeze_with_caution"
    return "do_not_freeze"


def freeze_reason(decision: str, rationale_ko: str) -> str:
    if decision == "freeze_as_current_default":
        return f"현재 reliability 판단상 기본값으로 freeze 가능하다. {rationale_ko}".strip()
    if decision == "freeze_with_caution":
        return f"현재는 caution 수준으로만 freeze하고 추가 support/validation을 병행해야 한다. {rationale_ko}".strip()
    return f"현재는 freeze하지 말고 support/data expansion 또는 validation을 먼저 진행해야 한다. {rationale_ko}".strip()


def build_freeze_plan(freeze_candidates_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in freeze_candidates_df.to_dict(orient="records"):
        decision = freeze_decision(normalize_text(row["recommended_freeze_recommendation"]))
        rows.append(
            {
                "eval_scope": normalize_text(row["eval_scope"]),
                "recommended_target_name": normalize_text(row["recommended_target_name"]),
                "recommended_metric_kind": normalize_text(row["recommended_metric_kind"]),
                "recommended_f1": numeric_float_or_blank(row["recommended_f1"]),
                "recommended_positive_support": numeric_float_or_blank(row["recommended_positive_support"]),
                "recommended_reliability_class": normalize_text(row["recommended_reliability_class"]),
                "recommended_freeze_recommendation": normalize_text(row["recommended_freeze_recommendation"]),
                "current_default_decision": decision,
                "freeze_reason_ko": freeze_reason(decision, normalize_text(row["rationale_ko"])),
            }
        )
    freeze_df = pd.DataFrame(rows, columns=FREEZE_PLAN_COLS)
    return freeze_df.sort_values(by=["eval_scope"], ascending=[True], kind="stable").reset_index(drop=True)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    frames = load_inputs(root)
    plan_df = build_plan_rows(frames)
    summary_df = build_plan_summary(plan_df)
    freeze_df = build_freeze_plan(frames["freeze_candidates"])

    plan_df.to_csv(share_dir / PLAN_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / PLAN_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    freeze_df.to_csv(share_dir / FREEZE_PLAN_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
