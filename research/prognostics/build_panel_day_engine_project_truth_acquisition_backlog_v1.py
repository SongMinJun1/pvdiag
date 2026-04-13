#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

TRUTH_EXPANSION_PLAN_NAME = "panel_day_engine_project_truth_expansion_plan_v1.csv"
SUPPORT_GAP_NAME = "panel_day_engine_project_eval_support_gap_v1.csv"
FREEZE_PLAN_NAME = "panel_day_engine_project_freeze_plan_v1.csv"

BACKLOG_OUTPUT_NAME = "panel_day_engine_project_truth_acquisition_backlog_v1.csv"
BACKLOG_SUMMARY_OUTPUT_NAME = "panel_day_engine_project_truth_acquisition_backlog_summary_v1.csv"
BACKLOG_NOTES_OUTPUT_NAME = "panel_day_engine_project_truth_acquisition_notes_v1.csv"

BACKLOG_COLS = [
    "eval_scope",
    "collection_unit",
    "expansion_action_class",
    "current_positive_support_unique",
    "additional_units_needed_for_5",
    "additional_units_needed_for_10",
    "requires_new_truth_or_data_flag",
    "suggested_collection_source_ko",
    "priority_rank",
    "freeze_status_ko",
    "backlog_reason_ko",
]

BACKLOG_SUMMARY_COLS = [
    "collection_unit",
    "expansion_action_class",
    "scope_count",
    "total_current_positive_support_unique",
    "total_additional_units_needed_for_5",
    "total_additional_units_needed_for_10",
    "requires_new_truth_or_data_count",
    "highest_priority_rank",
    "note_ko",
]

BACKLOG_NOTES_COLS = [
    "eval_scope",
    "why_target_level_sum_overcounts",
    "why_unique_unit_backlog_is_better",
    "note_ko",
]

SCOPE_CONFIG = {
    "step3_precursor_performance": {
        "collection_unit": "fault_case",
        "expansion_action_class": "collect_new_precursor_truth_cases",
        "priority_rank": 1,
    },
    "step4_common_cause_routing": {
        "collection_unit": "site_event",
        "expansion_action_class": "collect_new_common_cause_truth_cases",
        "priority_rank": 2,
    },
    "step4_abrupt_no_precursor": {
        "collection_unit": "panel_case",
        "expansion_action_class": "collect_new_abrupt_truth_cases",
        "priority_rank": 3,
    },
    "operator_policy_proxy": {
        "collection_unit": "workflow_observation",
        "expansion_action_class": "workflow_validation_not_truth",
        "priority_rank": 4,
    },
    "step1_taxonomy": {
        "collection_unit": "none",
        "expansion_action_class": "no_action_structural",
        "priority_rank": 6,
    },
    "step2_onset_truth": {
        "collection_unit": "none",
        "expansion_action_class": "no_action_structural",
        "priority_rank": 6,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert the target-level truth expansion plan into a deduplicated acquisition backlog at the correct collection unit."
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


def load_inputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    share_dir = root / "_share"
    plan_df = read_csv(share_dir / TRUTH_EXPANSION_PLAN_NAME)
    gap_df = read_csv(share_dir / SUPPORT_GAP_NAME)
    freeze_df = read_csv(share_dir / FREEZE_PLAN_NAME)

    ensure_columns(
        plan_df,
        [
            "eval_scope",
            "target_name",
            "current_positive_support",
            "current_artifact_candidate_pool_count",
            "requires_new_truth_or_data_flag",
            "expansion_action_class",
            "suggested_collection_unit",
            "suggested_collection_source_ko",
            "priority_rank",
            "freeze_recommendation",
        ],
        TRUTH_EXPANSION_PLAN_NAME,
    )
    ensure_columns(
        gap_df,
        [
            "eval_scope",
            "target_name",
            "current_positive_support",
            "additional_positive_needed_for_5",
            "additional_positive_needed_for_10",
        ],
        SUPPORT_GAP_NAME,
    )
    ensure_columns(
        freeze_df,
        [
            "eval_scope",
            "current_default_decision",
            "freeze_reason_ko",
        ],
        FREEZE_PLAN_NAME,
    )
    return (plan_df, gap_df, freeze_df)


def normalize_frames(plan_df: pd.DataFrame, gap_df: pd.DataFrame, freeze_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    plan_df = plan_df.copy()
    gap_df = gap_df.copy()
    freeze_df = freeze_df.copy()

    for df in (plan_df, gap_df, freeze_df):
        df["eval_scope"] = df["eval_scope"].map(normalize_text)
    if "target_name" in plan_df.columns:
        plan_df["target_name"] = plan_df["target_name"].map(normalize_text)
    if "target_name" in gap_df.columns:
        gap_df["target_name"] = gap_df["target_name"].map(normalize_text)
    if "current_default_decision" in freeze_df.columns:
        freeze_df["current_default_decision"] = freeze_df["current_default_decision"].map(normalize_text)
    if "freeze_reason_ko" in freeze_df.columns:
        freeze_df["freeze_reason_ko"] = freeze_df["freeze_reason_ko"].map(normalize_text)
    return (plan_df, gap_df, freeze_df)


def validate_scope_config(plan_df: pd.DataFrame) -> None:
    unknown_scopes = sorted(set(plan_df["eval_scope"]) - set(SCOPE_CONFIG))
    if unknown_scopes:
        raise SystemExit(f"unsupported eval_scope(s): {unknown_scopes}")


def validate_plan_vs_gap(plan_df: pd.DataFrame, gap_df: pd.DataFrame) -> None:
    gap_lookup = {
        (normalize_text(row["eval_scope"]), normalize_text(row["target_name"])): row
        for row in gap_df.to_dict(orient="records")
    }
    for row in plan_df.to_dict(orient="records"):
        key = (normalize_text(row["eval_scope"]), normalize_text(row["target_name"]))
        if key not in gap_lookup:
            raise SystemExit(f"plan row missing support-gap pair: {key}")
        gap_row = gap_lookup[key]
        if numeric_int(row["current_positive_support"]) != numeric_int(gap_row["current_positive_support"]):
            raise SystemExit(f"current_positive_support mismatch for {key}")


def freeze_status_for_scope(scope: str, scope_plan_df: pd.DataFrame, freeze_lookup: dict[str, dict[str, str]]) -> str:
    config = SCOPE_CONFIG[scope]
    if config["collection_unit"] in {"none", "workflow_observation"}:
        return "freeze_with_caution"

    target_freezes = [normalize_text(value) for value in scope_plan_df["freeze_recommendation"].tolist()]
    if target_freezes and all(value == "do_not_freeze" for value in target_freezes):
        return "do_not_freeze"

    freeze_plan_decision = freeze_lookup.get(scope, {}).get("current_default_decision", "")
    if freeze_plan_decision == "freeze_as_current_default":
        return "freeze_as_current_default"
    if any(value == "freeze_as_current_default" for value in target_freezes):
        return "freeze_as_current_default"
    return "freeze_with_caution"


def backlog_reason_for_scope(
    scope: str,
    current_positive_support_unique: int,
    additional_units_needed_for_5: int,
    additional_units_needed_for_10: int,
    scope_gap_df: pd.DataFrame,
    freeze_status_ko: str,
) -> str:
    sum_need_5 = int(pd.to_numeric(scope_gap_df["additional_positive_needed_for_5"], errors="coerce").fillna(0).sum())
    sum_need_10 = int(pd.to_numeric(scope_gap_df["additional_positive_needed_for_10"], errors="coerce").fillna(0).sum())

    if scope == "step3_precursor_performance":
        return (
            f"step3의 6개 marker row는 같은 precursor-bearing fault_case support를 공유하므로 target-level 합 {sum_need_5}건을 그대로 더하면 과대계산이다. "
            f"unique backlog는 현재 {current_positive_support_unique} fault_case 기준으로 +{additional_units_needed_for_5}면 support 5, +{additional_units_needed_for_10}이면 support 10에 도달한다. "
            f"현재 scope freeze 상태는 {freeze_status_ko} 다."
        )
    if scope == "step4_common_cause_routing":
        return (
            f"step4 common-cause의 3개 routing target은 같은 site_event support를 공유하므로 target-level 합 {sum_need_5}건을 그대로 더하면 과대계산이다. "
            f"unique backlog는 현재 {current_positive_support_unique} site_event 기준으로 +{additional_units_needed_for_5}면 support 5, +{additional_units_needed_for_10}이면 support 10이다. "
            f"현재 scope freeze 상태는 {freeze_status_ko} 다."
        )
    if scope == "step4_abrupt_no_precursor":
        return (
            f"step4 abrupt의 여러 hit target은 같은 abrupt panel_case support를 공유하므로 target-level support 10 gap 합 {sum_need_10}건은 과대계산이다. "
            f"unique backlog는 현재 {current_positive_support_unique} panel_case 기준으로 +{additional_units_needed_for_10}면 support 10이다. "
            f"support 5는 이미 충족했고 현재 scope freeze 상태는 {freeze_status_ko} 다."
        )
    if scope == "operator_policy_proxy":
        return "operator_policy_proxy 는 truth-label acquisition backlog가 아니라 workflow observation backlog로 읽어야 한다. 새 truth case 수집보다 reviewer load, shadow review, triage latency 검증이 우선이다."
    if scope in {"step1_taxonomy", "step2_onset_truth"}:
        return "이 scope는 structural/documentation row라 acquisition backlog로 세지지 않는다. support 정리는 유지하되 새 truth unit 수집 backlog로 해석하면 안 된다."
    raise SystemExit(f"unsupported backlog reason scope: {scope}")


def summary_note_for_combo(collection_unit: str, action_class: str) -> str:
    if (collection_unit, action_class) == ("fault_case", "collect_new_precursor_truth_cases"):
        return "step3 marker 여러 개가 같은 precursor fault_case support를 공유하므로 unique fault_case backlog로 관리해야 한다."
    if (collection_unit, action_class) == ("site_event", "collect_new_common_cause_truth_cases"):
        return "common-cause routing target 여러 개가 같은 site_event support를 공유하므로 unique site_event backlog가 적절하다."
    if (collection_unit, action_class) == ("panel_case", "collect_new_abrupt_truth_cases"):
        return "abrupt hit target 여러 개가 같은 panel_case support를 공유하므로 unique panel_case backlog가 적절하다."
    if (collection_unit, action_class) == ("workflow_observation", "workflow_validation_not_truth"):
        return "이 조합은 truth acquisition이 아니라 workflow validation backlog다."
    return "이 조합은 structural/documentation 유지 대상으로 acquisition backlog로 세지지 않는다."


def notes_row_for_scope(scope: str, scope_gap_df: pd.DataFrame) -> dict[str, object]:
    sum_need_5 = int(pd.to_numeric(scope_gap_df["additional_positive_needed_for_5"], errors="coerce").fillna(0).sum())
    sum_need_10 = int(pd.to_numeric(scope_gap_df["additional_positive_needed_for_10"], errors="coerce").fillna(0).sum())
    current_positive_support_unique = int(pd.to_numeric(scope_gap_df["current_positive_support"], errors="coerce").fillna(0).min())
    unique_need_5 = max(5 - current_positive_support_unique, 0)
    unique_need_10 = max(10 - current_positive_support_unique, 0)

    if scope == "step3_precursor_performance":
        return {
            "eval_scope": scope,
            "why_target_level_sum_overcounts": f"6개 marker row의 target-level need-for-5 합은 {sum_need_5}지만, 같은 precursor fault_case support를 공유하므로 18개의 서로 다른 새 case를 뜻하지 않는다.",
            "why_unique_unit_backlog_is_better": f"unique backlog는 fault_case 단위로 접어 +{unique_need_5} precursor-bearing fault_case 만 확보해도 6개 marker row를 함께 보강할 수 있다.",
            "note_ko": "step3 여섯 marker row는 +18 different new cases가 아니라, 같은 support 축을 공유하므로 +3 new precursor-bearing fault_case 로 같이 개선될 수 있다.",
        }
    if scope == "step4_common_cause_routing":
        return {
            "eval_scope": scope,
            "why_target_level_sum_overcounts": f"3개 routing target의 target-level need-for-5 합은 {sum_need_5}지만, 같은 common-cause site_event support를 공유하므로 서로 다른 3개 새 event를 뜻하지 않는다.",
            "why_unique_unit_backlog_is_better": f"unique backlog는 site_event 단위로 접어 +{unique_need_5} common-cause site_event 로 세 target을 함께 보강한다.",
            "note_ko": "step4 common-cause 세 target은 +3 different new site events가 아니라 +1 common-cause site_event 로 같이 개선될 수 있다.",
        }
    if scope == "step4_abrupt_no_precursor":
        return {
            "eval_scope": scope,
            "why_target_level_sum_overcounts": f"여러 abrupt target의 need-for-10 합은 {sum_need_10}이지만, 같은 abrupt panel_case support를 공유하므로 서로 다른 20개 case를 뜻하지 않는다.",
            "why_unique_unit_backlog_is_better": f"unique backlog는 panel_case 단위로 접어 +{unique_need_10} abrupt panel_case 로 support 10을 노린다.",
            "note_ko": "abrupt hit target들은 같은 panel_case 집합을 보므로 panel_case 단위 backlog가 더 직접적이다.",
        }
    if scope == "operator_policy_proxy":
        return {
            "eval_scope": scope,
            "why_target_level_sum_overcounts": "proxy scope를 truth case 수집 backlog처럼 세면 category error가 생긴다. 여기서 필요한 것은 새 truth case가 아니라 workflow observation이다.",
            "why_unique_unit_backlog_is_better": "workflow_observation 단위 backlog는 shadow review, triage latency, reviewer load 측정처럼 실제 운영 검증 행동으로 바로 연결된다.",
            "note_ko": "operator proxy scope는 truth acquisition이 아니라 workflow validation backlog로 읽어야 한다.",
        }
    return {
        "eval_scope": scope,
        "why_target_level_sum_overcounts": "structural/documentation row는 애초에 truth acquisition target이 아니므로 target-level 합산으로 backlog를 만들면 잘못된 해석이 된다.",
        "why_unique_unit_backlog_is_better": "none 단위 backlog는 새 case 수집이 아니라 coverage/documentation 유지라는 사실을 분명히 해 준다.",
        "note_ko": "step1/step2 는 structural/documentation 유지 대상이지 새 truth unit acquisition backlog가 아니다.",
    }


def build_outputs(plan_df: pd.DataFrame, gap_df: pd.DataFrame, freeze_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validate_scope_config(plan_df)
    validate_plan_vs_gap(plan_df, gap_df)

    freeze_lookup = {
        normalize_text(row["eval_scope"]): {
            "current_default_decision": normalize_text(row["current_default_decision"]),
            "freeze_reason_ko": normalize_text(row["freeze_reason_ko"]),
        }
        for row in freeze_df.to_dict(orient="records")
    }

    backlog_rows: list[dict[str, object]] = []
    notes_rows: list[dict[str, object]] = []

    scope_order = sorted(SCOPE_CONFIG, key=lambda scope: (SCOPE_CONFIG[scope]["priority_rank"], scope))
    for scope in scope_order:
        scope_plan_df = plan_df.loc[plan_df["eval_scope"].eq(scope)].copy()
        if scope_plan_df.empty:
            raise SystemExit(f"missing truth expansion scope: {scope}")
        scope_gap_df = gap_df.loc[gap_df["eval_scope"].eq(scope)].copy()
        if scope_gap_df.empty:
            raise SystemExit(f"missing support gap scope: {scope}")

        config = SCOPE_CONFIG[scope]
        current_positive_support_unique = int(pd.to_numeric(scope_gap_df["current_positive_support"], errors="coerce").fillna(0).min())
        additional_units_needed_for_5 = max(5 - current_positive_support_unique, 0)
        additional_units_needed_for_10 = max(10 - current_positive_support_unique, 0)

        if config["collection_unit"] in {"none", "workflow_observation"}:
            requires_new_truth_or_data_flag = 0
        else:
            requires_new_truth_or_data_flag = int(
                pd.to_numeric(scope_plan_df["requires_new_truth_or_data_flag"], errors="coerce").fillna(0).astype(int).eq(1).any()
            )

        sources = [normalize_text(value) for value in scope_plan_df["suggested_collection_source_ko"].tolist() if normalize_text(value)]
        suggested_collection_source_ko = sources[0] if sources else ""
        freeze_status_ko = freeze_status_for_scope(scope, scope_plan_df, freeze_lookup)

        backlog_rows.append(
            {
                "eval_scope": scope,
                "collection_unit": config["collection_unit"],
                "expansion_action_class": config["expansion_action_class"],
                "current_positive_support_unique": current_positive_support_unique,
                "additional_units_needed_for_5": additional_units_needed_for_5,
                "additional_units_needed_for_10": additional_units_needed_for_10,
                "requires_new_truth_or_data_flag": requires_new_truth_or_data_flag,
                "suggested_collection_source_ko": suggested_collection_source_ko,
                "priority_rank": config["priority_rank"],
                "freeze_status_ko": freeze_status_ko,
                "backlog_reason_ko": backlog_reason_for_scope(
                    scope=scope,
                    current_positive_support_unique=current_positive_support_unique,
                    additional_units_needed_for_5=additional_units_needed_for_5,
                    additional_units_needed_for_10=additional_units_needed_for_10,
                    scope_gap_df=scope_gap_df,
                    freeze_status_ko=freeze_status_ko,
                ),
            }
        )
        notes_rows.append(notes_row_for_scope(scope, scope_gap_df))

    backlog_df = pd.DataFrame(backlog_rows, columns=BACKLOG_COLS)
    notes_df = pd.DataFrame(notes_rows, columns=BACKLOG_NOTES_COLS)

    summary_rows: list[dict[str, object]] = []
    for (collection_unit, action_class), combo_df in backlog_df.groupby(["collection_unit", "expansion_action_class"], dropna=False):
        collection_unit = normalize_text(collection_unit)
        action_class = normalize_text(action_class)
        summary_rows.append(
            {
                "collection_unit": collection_unit,
                "expansion_action_class": action_class,
                "scope_count": int(len(combo_df)),
                "total_current_positive_support_unique": int(pd.to_numeric(combo_df["current_positive_support_unique"], errors="coerce").fillna(0).sum()),
                "total_additional_units_needed_for_5": int(pd.to_numeric(combo_df["additional_units_needed_for_5"], errors="coerce").fillna(0).sum()),
                "total_additional_units_needed_for_10": int(pd.to_numeric(combo_df["additional_units_needed_for_10"], errors="coerce").fillna(0).sum()),
                "requires_new_truth_or_data_count": int(pd.to_numeric(combo_df["requires_new_truth_or_data_flag"], errors="coerce").fillna(0).sum()),
                "highest_priority_rank": int(pd.to_numeric(combo_df["priority_rank"], errors="coerce").min()),
                "note_ko": summary_note_for_combo(collection_unit, action_class),
            }
        )
    summary_df = pd.DataFrame(summary_rows, columns=BACKLOG_SUMMARY_COLS)
    summary_df = summary_df.sort_values(
        by=["highest_priority_rank", "collection_unit", "expansion_action_class"],
        ascending=[True, True, True],
        kind="stable",
    ).reset_index(drop=True)

    return (backlog_df, summary_df, notes_df)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    plan_df, gap_df, freeze_df = load_inputs(root)
    plan_df, gap_df, freeze_df = normalize_frames(plan_df, gap_df, freeze_df)
    backlog_df, summary_df, notes_df = build_outputs(plan_df, gap_df, freeze_df)

    backlog_df.to_csv(share_dir / BACKLOG_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / BACKLOG_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    notes_df.to_csv(share_dir / BACKLOG_NOTES_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
