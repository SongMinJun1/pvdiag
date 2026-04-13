#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

RELIABILITY_NAME = "panel_day_engine_project_eval_reliability_v1.csv"
ONSET_TRUTH_NAME = "panel_day_engine_precursor_onset_truth_v1.csv"
PRECURSOR_PERFORMANCE_NAME = "panel_day_engine_precursor_performance_cases_v1.csv"
NON_PRECURSOR_CASES_NAME = "panel_day_engine_non_precursor_performance_cases_v1.csv"
COMMON_CAUSE_CASES_NAME = "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv"
EVAL_BUCKETS_NAME = "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv"
ELIGIBILITY_CASES_NAME = "panel_day_engine_local_precursor_eligibility_cases_v1.csv"
REAUDIT_NAME = "panel_date_reaudit_working.csv"

SUPPORT_GAP_OUTPUT_NAME = "panel_day_engine_project_eval_support_gap_v1.csv"
SUPPORT_GAP_SUMMARY_OUTPUT_NAME = "panel_day_engine_project_eval_support_gap_summary_v1.csv"
SUPPORT_GAP_CANDIDATES_OUTPUT_NAME = "panel_day_engine_project_eval_support_gap_candidates_v1.csv"

SUPPORT_GAP_COLS = [
    "eval_scope",
    "target_name",
    "reliability_class",
    "freeze_recommendation",
    "current_positive_support",
    "current_negative_support",
    "additional_positive_needed_for_5",
    "additional_positive_needed_for_10",
    "current_artifact_candidate_pool_name",
    "current_artifact_candidate_pool_count",
    "can_reach_5_with_current_artifacts_flag",
    "can_reach_10_with_current_artifacts_flag",
    "support_gap_reason_ko",
]

SUPPORT_GAP_SUMMARY_COLS = [
    "eval_scope",
    "focused_target_count",
    "underpowered_target_count",
    "low_support_target_count",
    "total_additional_positive_needed_for_5",
    "total_additional_positive_needed_for_10",
    "total_current_artifact_candidate_pool_count",
    "any_scope_can_reach_5_with_current_artifacts_flag",
    "any_scope_can_reach_10_with_current_artifacts_flag",
    "note_ko",
]

CANDIDATE_COLS = [
    "eval_scope",
    "candidate_pool_name",
    "site",
    "panel_id",
    "anchor_date",
    "candidate_reason_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit support gaps for underpowered or caution-level project evaluation scopes."
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


def normalize_date_text(value: object) -> str:
    text = normalize_text(value)
    return text[:10] if len(text) >= 10 else text


def to_int_flag(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"", "0", "0.0", "false", "f", "n", "no"}:
        return 0
    if text in {"1", "1.0", "true", "t", "y", "yes"}:
        return 1
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return int(bool(numeric)) if not pd.isna(numeric) else 0


def numeric_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def derive_fault_family_id(vendor_fault_family: str, temporality_class: str) -> str:
    family = normalize_text(vendor_fault_family)
    temporality = normalize_text(temporality_class)
    if family in {"diode_like", "module_damage_like"}:
        if temporality == "progressive_local_precursor_expected":
            return "electrical_fault_like_progressive_local"
        if temporality == "abrupt_local_precursor_unexpected":
            return "electrical_fault_like_abrupt_local"
        return "electrical_fault_like_unknown_local_temporality"
    if family == "group_or_inverter_side_like":
        return "group_or_inverter_side_like"
    if family in {"none_visible", "none_visible_or_unconfirmed"}:
        return "none_visible_or_unconfirmed"
    return ""


def load_inputs(root: Path) -> dict[str, pd.DataFrame]:
    share_dir = root / "_share"
    frames = {
        "reliability": read_csv(share_dir / RELIABILITY_NAME),
        "onset_truth": read_csv(share_dir / ONSET_TRUTH_NAME),
        "precursor_perf": read_csv(share_dir / PRECURSOR_PERFORMANCE_NAME),
        "nonprec": read_csv(share_dir / NON_PRECURSOR_CASES_NAME),
        "common_cause": read_csv(share_dir / COMMON_CAUSE_CASES_NAME),
        "taxonomy": read_csv(share_dir / EVAL_BUCKETS_NAME),
        "eligibility": read_csv(share_dir / ELIGIBILITY_CASES_NAME),
        "reaudit": read_csv(share_dir / REAUDIT_NAME),
    }

    ensure_columns(frames["reliability"], ["eval_scope", "target_name", "reliability_class", "freeze_recommendation", "metric_kind", "positive_support", "negative_support"], RELIABILITY_NAME)
    ensure_columns(frames["onset_truth"], ["site", "panel_id", "fault_start_date"], ONSET_TRUTH_NAME)
    ensure_columns(frames["precursor_perf"], ["site", "panel_id", "fault_start_date"], PRECURSOR_PERFORMANCE_NAME)
    ensure_columns(frames["nonprec"], ["eval_bucket_v2", "site", "panel_id", "anchor_date", "truth_case_id"], NON_PRECURSOR_CASES_NAME)
    ensure_columns(frames["common_cause"], ["eval_bucket_v2", "site", "panel_id", "anchor_date", "truth_case_id"], COMMON_CAUSE_CASES_NAME)
    ensure_columns(frames["taxonomy"], ["fault_family_id", "eval_bucket_v2"], EVAL_BUCKETS_NAME)
    ensure_columns(frames["eligibility"], ["site", "panel_id", "fault_start_date", "precursor_eligible_flag"], ELIGIBILITY_CASES_NAME)
    ensure_columns(frames["reaudit"], ["site", "panel_id", "strict_trigger_date", "vendor_fault_family", "candidate_validity"], REAUDIT_NAME)
    return frames


def build_step3_candidates(eligibility_df: pd.DataFrame, onset_truth_df: pd.DataFrame) -> pd.DataFrame:
    eligibility_df = eligibility_df.copy()
    eligibility_df["site"] = eligibility_df["site"].map(normalize_text)
    eligibility_df["panel_id"] = eligibility_df["panel_id"].map(normalize_text)
    eligibility_df["fault_start_date"] = eligibility_df["fault_start_date"].map(normalize_date_text)
    eligibility_df["precursor_eligible_flag"] = eligibility_df["precursor_eligible_flag"].map(to_int_flag).astype(int)
    eligibility_df = eligibility_df.loc[eligibility_df["precursor_eligible_flag"].eq(1)].copy()

    onset_truth_df = onset_truth_df.copy()
    onset_truth_df["site"] = onset_truth_df["site"].map(normalize_text)
    onset_truth_df["panel_id"] = onset_truth_df["panel_id"].map(normalize_text)
    onset_truth_df["fault_start_date"] = onset_truth_df["fault_start_date"].map(normalize_date_text)
    onset_keys = set(
        onset_truth_df.loc[:, ["site", "panel_id", "fault_start_date"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )

    candidate_rows: list[dict[str, object]] = []
    for row in eligibility_df.to_dict(orient="records"):
        key = (normalize_text(row["site"]), normalize_text(row["panel_id"]), normalize_text(row["fault_start_date"]))
        if key in onset_keys:
            continue
        candidate_rows.append(
            {
                "eval_scope": "step3_precursor_performance",
                "candidate_pool_name": "precursor_eligible_not_yet_in_onset_truth",
                "site": key[0],
                "panel_id": key[1],
                "anchor_date": key[2],
                "candidate_reason_ko": "precursor_eligible_flag==1 이지만 onset truth/current precursor performance support에는 아직 포함되지 않은 current-artifact candidate",
            }
        )
    return pd.DataFrame(candidate_rows, columns=CANDIDATE_COLS)


def build_eval_bucket_map(taxonomy_df: pd.DataFrame) -> dict[str, str]:
    taxonomy_df = taxonomy_df.copy()
    taxonomy_df["fault_family_id"] = taxonomy_df["fault_family_id"].map(normalize_text)
    taxonomy_df["eval_bucket_v2"] = taxonomy_df["eval_bucket_v2"].map(normalize_text)
    return dict(zip(taxonomy_df["fault_family_id"], taxonomy_df["eval_bucket_v2"]))


def build_step4_abrupt_candidates(reaudit_df: pd.DataFrame, nonprec_df: pd.DataFrame, eval_bucket_map: dict[str, str]) -> pd.DataFrame:
    positive_ids = set(
        nonprec_df.loc[nonprec_df["eval_bucket_v2"].map(normalize_text).eq("abrupt_or_no_precursor_now"), "truth_case_id"]
        .map(normalize_text)
        .tolist()
    )

    reaudit_df = reaudit_df.copy()
    reaudit_df["site"] = reaudit_df["site"].map(normalize_text)
    reaudit_df["panel_id"] = reaudit_df["panel_id"].map(normalize_text)
    reaudit_df["strict_trigger_date"] = reaudit_df["strict_trigger_date"].map(normalize_date_text)
    reaudit_df["vendor_fault_family"] = reaudit_df["vendor_fault_family"].map(normalize_text)

    candidate_rows: list[dict[str, object]] = []
    for row in reaudit_df.to_dict(orient="records"):
        fault_family_id = derive_fault_family_id(normalize_text(row["vendor_fault_family"]), "")
        eval_bucket = normalize_text(eval_bucket_map.get(fault_family_id, ""))
        if eval_bucket != "abrupt_or_no_precursor_now":
            continue
        truth_case_id = f"reaudit|{normalize_text(row['site'])}|{normalize_text(row['panel_id'])}|{normalize_text(row['strict_trigger_date'])}"
        if truth_case_id in positive_ids:
            continue
        candidate_rows.append(
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "candidate_pool_name": "reaudit_abrupt_not_yet_in_nonprec_cases",
                "site": normalize_text(row["site"]),
                "panel_id": normalize_text(row["panel_id"]),
                "anchor_date": normalize_text(row["strict_trigger_date"]),
                "candidate_reason_ko": "reaudit row가 abrupt/no-precursor bucket으로 매핑되지만 current non_precursor positive abrupt case에는 아직 포함되지 않은 current-artifact candidate",
            }
        )
    return pd.DataFrame(candidate_rows, columns=CANDIDATE_COLS)


def build_step4_common_cause_candidates(reaudit_df: pd.DataFrame, common_cause_df: pd.DataFrame, eval_bucket_map: dict[str, str]) -> pd.DataFrame:
    positive_ids = set(
        common_cause_df.loc[common_cause_df["eval_bucket_v2"].map(normalize_text).eq("non_panel_or_common_cause"), "truth_case_id"]
        .map(normalize_text)
        .tolist()
    )

    reaudit_df = reaudit_df.copy()
    reaudit_df["site"] = reaudit_df["site"].map(normalize_text)
    reaudit_df["panel_id"] = reaudit_df["panel_id"].map(normalize_text)
    reaudit_df["strict_trigger_date"] = reaudit_df["strict_trigger_date"].map(normalize_date_text)
    reaudit_df["vendor_fault_family"] = reaudit_df["vendor_fault_family"].map(normalize_text)
    reaudit_df["candidate_validity"] = reaudit_df["candidate_validity"].map(normalize_text)

    candidate_rows: list[dict[str, object]] = []
    for row in reaudit_df.to_dict(orient="records"):
        fault_family_id = derive_fault_family_id(normalize_text(row["vendor_fault_family"]), "")
        mapped_bucket = normalize_text(eval_bucket_map.get(fault_family_id, ""))
        is_common_cause = mapped_bucket == "non_panel_or_common_cause" or normalize_text(row["candidate_validity"]) == "group_side"
        if not is_common_cause:
            continue
        truth_case_id = f"reaudit|{normalize_text(row['site'])}|{normalize_text(row['panel_id'])}|{normalize_text(row['strict_trigger_date'])}"
        if truth_case_id in positive_ids:
            continue
        candidate_rows.append(
            {
                "eval_scope": "step4_common_cause_routing",
                "candidate_pool_name": "reaudit_common_cause_not_yet_in_descriptive_cases",
                "site": normalize_text(row["site"]),
                "panel_id": normalize_text(row["panel_id"]),
                "anchor_date": normalize_text(row["strict_trigger_date"]),
                "candidate_reason_ko": "group-side/common-cause reaudit row지만 current descriptive retrofit positive common-cause support에는 아직 포함되지 않은 current-artifact candidate",
            }
        )
    return pd.DataFrame(candidate_rows, columns=CANDIDATE_COLS)


def build_candidate_pools(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, dict[str, dict[str, object]]]:
    eval_bucket_map = build_eval_bucket_map(frames["taxonomy"])
    step3_candidates = build_step3_candidates(frames["eligibility"], frames["onset_truth"])
    abrupt_candidates = build_step4_abrupt_candidates(frames["reaudit"], frames["nonprec"], eval_bucket_map)
    common_cause_candidates = build_step4_common_cause_candidates(frames["reaudit"], frames["common_cause"], eval_bucket_map)

    all_candidates = pd.concat([step3_candidates, abrupt_candidates, common_cause_candidates], ignore_index=True)
    pools = {
        "step3_precursor_performance": {
            "pool_name": "precursor_eligible_not_yet_in_onset_truth",
            "pool_count": int(len(step3_candidates)),
            "meaningful": True,
        },
        "step4_abrupt_no_precursor": {
            "pool_name": "reaudit_abrupt_not_yet_in_nonprec_cases",
            "pool_count": int(len(abrupt_candidates)),
            "meaningful": True,
        },
        "step4_common_cause_routing": {
            "pool_name": "reaudit_common_cause_not_yet_in_descriptive_cases",
            "pool_count": int(len(common_cause_candidates)),
            "meaningful": True,
        },
        "operator_policy_proxy": {
            "pool_name": "",
            "pool_count": "",
            "meaningful": False,
        },
        "step1_taxonomy": {
            "pool_name": "",
            "pool_count": "",
            "meaningful": False,
        },
        "step2_onset_truth": {
            "pool_name": "",
            "pool_count": "",
            "meaningful": False,
        },
    }
    return all_candidates, pools


def is_focused_row(row: dict[str, object]) -> bool:
    reliability_class = normalize_text(row.get("reliability_class"))
    freeze_recommendation = normalize_text(row.get("freeze_recommendation"))
    return (
        reliability_class in {"underpowered", "low_support"}
        or freeze_recommendation in {"do_not_freeze", "freeze_with_caution"}
    )


def support_gap_reason(
    *,
    eval_scope: str,
    reliability_class: str,
    freeze_recommendation: str,
    current_positive_support: int,
    pool_count: object,
    can_reach_5: object,
    can_reach_10: object,
) -> str:
    if eval_scope in {"step1_taxonomy", "step2_onset_truth"}:
        return "이 scope는 structural/support row라 classifier support gap으로 해석하지 않는다. current artifacts로 family/coverage support만 설명 가능하다."
    if eval_scope == "operator_policy_proxy":
        return "operator policy row는 retrospective proxy metric이라 true positive support gap 문제로 해석하지 않는다. 새 truth/data 확대보다 별도 workflow/load validation이 더 중요하다."
    if pool_count == "":
        return "현재 artifact candidate pool을 정의하지 않았다."
    if current_positive_support >= 10:
        return "이미 current positive support가 10 이상이라 support gap 자체는 작고, freeze 판단은 metric kind와 interval 해석이 더 중요하다."
    if can_reach_10 == 1:
        return "현재 artifact pool만으로도 positive support 10에 도달할 수 있어 추가 truth labeling 없이 current data 재정리로 support gap을 줄일 여지가 있다."
    if can_reach_5 == 1:
        return "현재 artifact pool만으로 support 5 수준까지는 도달 가능하지만 10까지는 부족해, freeze 수준을 높이려면 추가 truth/data 확장이 여전히 필요하다."
    return "현재 artifact pool만으로도 support gap을 메우기 어렵다. 보다 안정적인 freeze를 위해서는 genuinely new truth/data expansion이 필요하다."


def build_support_gap_rows(reliability_df: pd.DataFrame, pools: dict[str, dict[str, object]]) -> pd.DataFrame:
    reliability_df = reliability_df.copy()
    reliability_df["eval_scope"] = reliability_df["eval_scope"].map(normalize_text)
    reliability_df["target_name"] = reliability_df["target_name"].map(normalize_text)
    reliability_df["reliability_class"] = reliability_df["reliability_class"].map(normalize_text)
    reliability_df["freeze_recommendation"] = reliability_df["freeze_recommendation"].map(normalize_text)

    rows: list[dict[str, object]] = []
    for row in reliability_df.to_dict(orient="records"):
        if not is_focused_row(row):
            continue
        eval_scope = normalize_text(row["eval_scope"])
        pool_meta = pools.get(eval_scope, {"pool_name": "", "pool_count": "", "meaningful": False})
        current_positive_support = numeric_int(row.get("positive_support"))
        current_negative_support = numeric_int(row.get("negative_support")) if normalize_text(row.get("negative_support")) != "" else ""
        additional_positive_needed_for_5 = max(5 - current_positive_support, 0)
        additional_positive_needed_for_10 = max(10 - current_positive_support, 0)

        pool_count = pool_meta["pool_count"]
        if pool_meta["meaningful"]:
            can_reach_5 = int(current_positive_support + int(pool_count) >= 5)
            can_reach_10 = int(current_positive_support + int(pool_count) >= 10)
        else:
            can_reach_5 = ""
            can_reach_10 = ""

        rows.append(
            {
                "eval_scope": eval_scope,
                "target_name": normalize_text(row["target_name"]),
                "reliability_class": normalize_text(row["reliability_class"]),
                "freeze_recommendation": normalize_text(row["freeze_recommendation"]),
                "current_positive_support": current_positive_support,
                "current_negative_support": current_negative_support,
                "additional_positive_needed_for_5": additional_positive_needed_for_5,
                "additional_positive_needed_for_10": additional_positive_needed_for_10,
                "current_artifact_candidate_pool_name": pool_meta["pool_name"],
                "current_artifact_candidate_pool_count": pool_count,
                "can_reach_5_with_current_artifacts_flag": can_reach_5,
                "can_reach_10_with_current_artifacts_flag": can_reach_10,
                "support_gap_reason_ko": support_gap_reason(
                    eval_scope=eval_scope,
                    reliability_class=normalize_text(row["reliability_class"]),
                    freeze_recommendation=normalize_text(row["freeze_recommendation"]),
                    current_positive_support=current_positive_support,
                    pool_count=pool_count,
                    can_reach_5=can_reach_5,
                    can_reach_10=can_reach_10,
                ),
            }
        )
    return pd.DataFrame(rows, columns=SUPPORT_GAP_COLS)


def build_summary_rows(support_gap_df: pd.DataFrame, pools: dict[str, dict[str, object]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for eval_scope, scope_df in support_gap_df.groupby("eval_scope", dropna=False):
        eval_scope = normalize_text(eval_scope)
        pool_meta = pools.get(eval_scope, {"pool_count": 0, "meaningful": False})
        pool_count = int(pool_meta["pool_count"]) if pool_meta["meaningful"] else 0
        focused_target_count = int(len(scope_df))
        underpowered_target_count = int(scope_df["reliability_class"].astype(str).eq("underpowered").sum())
        low_support_target_count = int(scope_df["reliability_class"].astype(str).eq("low_support").sum())
        total_additional_positive_needed_for_5 = int(pd.to_numeric(scope_df["additional_positive_needed_for_5"], errors="coerce").fillna(0).sum())
        total_additional_positive_needed_for_10 = int(pd.to_numeric(scope_df["additional_positive_needed_for_10"], errors="coerce").fillna(0).sum())
        reach5_series = pd.to_numeric(scope_df["can_reach_5_with_current_artifacts_flag"], errors="coerce").fillna(0).astype(int)
        reach10_series = pd.to_numeric(scope_df["can_reach_10_with_current_artifacts_flag"], errors="coerce").fillna(0).astype(int)
        any_scope_can_reach_5 = int(reach5_series.eq(1).any()) if pool_meta["meaningful"] else 0
        any_scope_can_reach_10 = int(reach10_series.eq(1).any()) if pool_meta["meaningful"] else 0

        if eval_scope in {"step1_taxonomy", "step2_onset_truth"}:
            note_ko = "이 scope는 structural/support row라 classifier positive support gap으로 해석하지 않는다."
        elif eval_scope == "operator_policy_proxy":
            note_ko = "이 scope는 retrospective proxy row라 support-gap보다는 workflow validation 문제가 더 중요하다."
        elif pool_count == 0:
            note_ko = "현재 artifact만으로 추가 positive candidate를 찾지 못해 support gap을 줄이려면 새 truth/data 확장이 필요하다."
        elif any_scope_can_reach_10 == 1:
            note_ko = "현재 artifact pool만으로도 일부 target은 positive support 10까지 도달 가능하다."
        elif any_scope_can_reach_5 == 1:
            note_ko = "현재 artifact pool만으로 일부 target은 support 5 수준까지는 보강 가능하지만, 10까지는 여전히 부족하다."
        else:
            note_ko = "현재 artifact pool이 있더라도 gap을 메우기에는 부족하다."

        rows.append(
            {
                "eval_scope": eval_scope,
                "focused_target_count": focused_target_count,
                "underpowered_target_count": underpowered_target_count,
                "low_support_target_count": low_support_target_count,
                "total_additional_positive_needed_for_5": total_additional_positive_needed_for_5,
                "total_additional_positive_needed_for_10": total_additional_positive_needed_for_10,
                "total_current_artifact_candidate_pool_count": pool_count,
                "any_scope_can_reach_5_with_current_artifacts_flag": any_scope_can_reach_5,
                "any_scope_can_reach_10_with_current_artifacts_flag": any_scope_can_reach_10,
                "note_ko": note_ko,
            }
        )
    return pd.DataFrame(rows, columns=SUPPORT_GAP_SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    frames = load_inputs(root)
    candidate_df, pools = build_candidate_pools(frames)
    support_gap_df = build_support_gap_rows(frames["reliability"], pools)
    summary_df = build_summary_rows(support_gap_df, pools)

    support_gap_df.to_csv(share_dir / SUPPORT_GAP_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / SUPPORT_GAP_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    candidate_df.to_csv(share_dir / SUPPORT_GAP_CANDIDATES_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
