#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

RELIABILITY_NAME = "panel_day_engine_project_eval_reliability_v1.csv"
FREEZE_CANDIDATES_NAME = "panel_day_engine_project_eval_freeze_candidates_v1.csv"
TRUTH_BACKLOG_NAME = "panel_day_engine_project_truth_acquisition_backlog_v1.csv"
TRUTH_EXPANSION_SUMMARY_NAME = "panel_day_engine_project_truth_expansion_plan_summary_v1.csv"
POLICY_RECOMMENDATION_NAME = "panel_day_engine_operator_attention_policy_recommendation_v1.csv"
PIPELINE_MANIFEST_NAME = "panel_day_engine_operator_pipeline_manifest_v1.csv"

FREEZE_PACK_OUTPUT_NAME = "panel_day_engine_project_current_data_freeze_pack_v1.csv"
FREEZE_SUMMARY_OUTPUT_NAME = "panel_day_engine_project_current_data_freeze_summary_v1.csv"
CLAIMS_OUTPUT_NAME = "panel_day_engine_project_current_data_claims_v1.csv"

FREEZE_PACK_COLS = [
    "eval_scope",
    "current_best_target_name",
    "current_best_metric_kind",
    "current_best_f1",
    "current_best_positive_support",
    "current_operational_workflow_name",
    "current_operational_workflow_reason_ko",
    "freeze_recommendation",
    "acquisition_blocked_flag",
    "current_data_decision",
    "allowed_claim_strength",
    "next_allowed_action",
    "freeze_reason_ko",
]

FREEZE_SUMMARY_COLS = [
    "current_data_decision",
    "scope_count",
    "operational_default_claim_count",
    "bounded_current_data_claim_count",
    "exploratory_claim_only_count",
    "workflow_claim_only_count",
    "note_ko",
]

CLAIMS_COLS = [
    "claim_id",
    "claim_scope",
    "claim_text_ko",
    "claim_strength",
    "prohibited_overclaim_ko",
]

EXPECTED_SCOPES = [
    "step1_taxonomy",
    "step2_onset_truth",
    "step3_precursor_performance",
    "step4_abrupt_no_precursor",
    "step4_common_cause_routing",
    "operator_policy_proxy",
]

CURRENT_DATA_DECISIONS = [
    "freeze_as_current_default",
    "freeze_with_caution",
    "exploratory_only",
    "workflow_proxy_only",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Produce a bounded current-data-limited freeze/decision pack for the whole project."
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
        "freeze_candidates": read_csv(share_dir / FREEZE_CANDIDATES_NAME),
        "backlog": read_csv(share_dir / TRUTH_BACKLOG_NAME),
        "expansion_summary": read_csv(share_dir / TRUTH_EXPANSION_SUMMARY_NAME),
        "policy": read_csv(share_dir / POLICY_RECOMMENDATION_NAME),
        "pipeline": read_csv(share_dir / PIPELINE_MANIFEST_NAME),
    }

    ensure_columns(
        frames["reliability"],
        ["eval_scope", "target_name", "metric_kind", "positive_support", "f1", "freeze_recommendation", "reliability_reason_ko"],
        RELIABILITY_NAME,
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
    ensure_columns(
        frames["backlog"],
        [
            "eval_scope",
            "collection_unit",
            "expansion_action_class",
            "current_positive_support_unique",
            "requires_new_truth_or_data_flag",
            "priority_rank",
            "freeze_status_ko",
            "backlog_reason_ko",
        ],
        TRUTH_BACKLOG_NAME,
    )
    ensure_columns(
        frames["expansion_summary"],
        ["expansion_action_class", "note_ko"],
        TRUTH_EXPANSION_SUMMARY_NAME,
    )
    ensure_columns(
        frames["policy"],
        ["recommended_policy_name", "recommended_policy_reason_ko", "expected_use_ko", "caution_ko"],
        POLICY_RECOMMENDATION_NAME,
    )
    ensure_columns(
        frames["pipeline"],
        ["final_pipeline_pass_flag", "note_ko"],
        PIPELINE_MANIFEST_NAME,
    )
    return frames


def normalize_frames(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    frames = {key: value.copy() for key, value in frames.items()}
    for key, df in frames.items():
        if "eval_scope" in df.columns:
            df["eval_scope"] = df["eval_scope"].map(normalize_text)
        if "target_name" in df.columns:
            df["target_name"] = df["target_name"].map(normalize_text)
        if "metric_kind" in df.columns:
            df["metric_kind"] = df["metric_kind"].map(normalize_text)
    return frames


def validate_scopes(frames: dict[str, pd.DataFrame]) -> None:
    backlog_scopes = set(frames["backlog"]["eval_scope"])
    freeze_scopes = set(frames["freeze_candidates"]["eval_scope"])
    reliability_scopes = set(frames["reliability"]["eval_scope"])
    missing = {
        "backlog": sorted(set(EXPECTED_SCOPES) - backlog_scopes),
        "freeze_candidates": sorted(set(EXPECTED_SCOPES) - freeze_scopes),
        "reliability": sorted(set(EXPECTED_SCOPES) - reliability_scopes),
    }
    problems = {key: value for key, value in missing.items() if value}
    if problems:
        raise SystemExit(f"missing eval_scope coverage: {problems}")


def best_reliability_row(scope_df: pd.DataFrame) -> dict[str, object]:
    scope_df = scope_df.copy()
    scope_df["positive_support_num"] = pd.to_numeric(scope_df["positive_support"], errors="coerce").fillna(0.0)
    scope_df["f1_num"] = pd.to_numeric(scope_df["f1"], errors="coerce").fillna(-1.0)
    scope_df = scope_df.sort_values(
        by=["f1_num", "positive_support_num", "target_name"],
        ascending=[False, False, True],
        kind="stable",
    )
    return scope_df.iloc[0].to_dict()


def scope_type(scope: str, reliability_scope_df: pd.DataFrame) -> str:
    if scope == "operator_policy_proxy":
        return "proxy"
    metric_kinds = {normalize_text(value) for value in reliability_scope_df["metric_kind"].tolist()}
    if metric_kinds == {"structural_coverage_metric"}:
        return "structural"
    return "true_case"


def current_data_decision(scope: str, freeze_recommendation: str, scope_kind: str) -> str:
    if scope == "operator_policy_proxy":
        return "workflow_proxy_only"
    if scope_kind == "structural":
        return "freeze_with_caution"
    if freeze_recommendation == "freeze_as_current_default":
        return "freeze_as_current_default"
    if freeze_recommendation == "freeze_with_caution":
        return "freeze_with_caution"
    if freeze_recommendation == "do_not_freeze" and scope_kind == "true_case":
        return "exploratory_only"
    return "freeze_with_caution"


def allowed_claim_strength(decision: str) -> str:
    if decision == "freeze_as_current_default":
        return "operational_default_claim"
    if decision == "freeze_with_caution":
        return "bounded_current_data_claim"
    if decision == "exploratory_only":
        return "exploratory_claim_only"
    return "workflow_claim_only"


def next_allowed_action(decision: str) -> str:
    if decision == "freeze_as_current_default":
        return "keep_as_default"
    if decision == "freeze_with_caution":
        return "keep_with_caution_note"
    if decision == "exploratory_only":
        return "do_not_upgrade_without_new_truth"
    return "operator_workflow_only"


def freeze_reason(
    *,
    scope: str,
    decision: str,
    freeze_candidate_row: dict[str, object],
    backlog_row: dict[str, object],
    expansion_note: str,
    policy_row: dict[str, str],
    pipeline_row: dict[str, object],
    best_row: dict[str, object],
) -> str:
    backlog_reason = normalize_text(backlog_row["backlog_reason_ko"])
    rationale = normalize_text(freeze_candidate_row["rationale_ko"])
    best_target = normalize_text(best_row.get("target_name"))
    best_f1 = numeric_float_or_blank(best_row.get("f1"))
    best_support = numeric_float_or_blank(best_row.get("positive_support"))

    if scope == "operator_policy_proxy":
        recommended_policy = normalize_text(policy_row["recommended_policy_name"])
        pipeline_pass = numeric_int(pipeline_row["final_pipeline_pass_flag"])
        return (
            f"operator_policy_proxy 에서 retrospective proxy best target은 {normalize_text(freeze_candidate_row['recommended_target_name'])} 이고, "
            f"현재 선택된 operational workflow 는 {recommended_policy} 다. "
            f"pipeline pass={pipeline_pass} 이므로 workflow proxy 로는 사용할 수 있다. "
            f"{normalize_text(policy_row['expected_use_ko'])}. 선택 이유는 {normalize_text(policy_row['recommended_policy_reason_ko'])}. "
            f"다만 {normalize_text(policy_row['caution_ko'])}"
        )

    if scope in {"step1_taxonomy", "step2_onset_truth"}:
        return (
            f"{scope} 는 structural coverage/reference scope라 classifier target selection scope가 아니다. "
            f"current_best_target_name 은 coverage_only 로만 표기하고 bounded current-data claim으로만 유지한다. "
            f"{rationale or backlog_reason}"
        )

    if scope == "step4_abrupt_no_precursor":
        pure_support_text = best_support
        pure_support_int = numeric_int(best_support)
        need5 = max(0, 5 - pure_support_int)
        need10 = max(0, 10 - pure_support_int)
        support_gap_note = (
            f"pure abrupt unique backlog는 현재 {pure_support_int} panel_case 기준으로 +{need5}면 support 5, +{need10}이면 support 10이다."
        )
        if decision == "exploratory_only":
            return (
                f"step4 pure abrupt/no-precursor scope의 현재 최상위 target은 {best_target} (f1={best_f1}, positive_support={pure_support_text}) 이다. "
                "precursor-abrupt consistency audit 기준 overlap 2건은 전조형 고장(급격 종료)으로 재분류되어 pure abrupt event positive set에서 제외된다. "
                "또한 c42997a6-5881-47e7-9035-7de8a2673b54.1.1 은 strong trigger 이전 precursor-like evidence 때문에 pure abrupt typing holdout 으로 제외된다. "
                f"따라서 현재 pure abrupt support는 {pure_support_text}건이고 current data에서는 exploratory 수준으로만 유지해야 한다. "
                f"{support_gap_note} 현재 scope freeze 상태는 do_not_freeze 다. {expansion_note}"
            ).strip()
        return (
            f"step4 pure abrupt/no-precursor scope의 현재 최상위 target은 {best_target} (f1={best_f1}, positive_support={pure_support_text}) 이다. "
            "precursor-abrupt consistency audit 기준 overlap 2건은 전조형 고장(급격 종료)으로 재분류되어 pure abrupt event positive set에서 제외된다. "
            "또한 c42997a6-5881-47e7-9035-7de8a2673b54.1.1 은 strong trigger 이전 precursor-like evidence 때문에 pure abrupt typing holdout 으로 제외된다. "
            f"따라서 현재 pure abrupt support는 {pure_support_text}건으로 읽어야 한다. {support_gap_note} {rationale or expansion_note}"
        ).strip()

    if decision == "exploratory_only":
        return (
            f"{scope} 의 현재 최상위 target은 {best_target} (f1={best_f1}, positive_support={best_support}) 이지만, "
            f"현재 data만으로는 exploratory 수준에 머물러야 한다. {backlog_reason} {expansion_note}"
        ).strip()

    if decision == "freeze_as_current_default":
        return (
            f"{scope} 는 current data 기준 best target {best_target} (f1={best_f1}, positive_support={best_support}) 를 현재 default로 둘 수 있다. "
            f"다만 추가 collection이 막혀 있는 동안에는 현재 data 범위 내에서만 해석해야 한다. {rationale or expansion_note}"
        ).strip()

    return (
        f"{scope} 는 current data 기준 best target {best_target} (f1={best_f1}, positive_support={best_support}) 를 caution과 함께 유지할 수 있다. "
        f"{backlog_reason or rationale} {expansion_note}"
    ).strip()


def build_freeze_pack(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    freeze_lookup = {
        normalize_text(row["eval_scope"]): row
        for row in frames["freeze_candidates"].to_dict(orient="records")
    }
    backlog_lookup = {
        normalize_text(row["eval_scope"]): row
        for row in frames["backlog"].to_dict(orient="records")
    }
    expansion_lookup = {
        normalize_text(row["expansion_action_class"]): normalize_text(row["note_ko"])
        for row in frames["expansion_summary"].to_dict(orient="records")
    }
    policy_row = frames["policy"].iloc[0].to_dict()
    pipeline_row = frames["pipeline"].iloc[0].to_dict()

    rows: list[dict[str, object]] = []
    for scope in EXPECTED_SCOPES:
        scope_reliability_df = frames["reliability"].loc[frames["reliability"]["eval_scope"].eq(scope)].copy()
        if scope_reliability_df.empty:
            raise SystemExit(f"missing reliability scope: {scope}")
        best_row = best_reliability_row(scope_reliability_df)
        freeze_candidate_row = freeze_lookup[scope]
        backlog_row = backlog_lookup[scope]
        scope_kind = scope_type(scope, scope_reliability_df)

        if scope_kind == "structural":
            current_best_target_name = "coverage_only"
            current_best_metric_kind = "structural_coverage_metric"
            current_best_f1 = ""
            current_best_positive_support = numeric_float_or_blank(best_row["positive_support"])
        else:
            current_best_target_name = normalize_text(freeze_candidate_row["recommended_target_name"]) or normalize_text(best_row["target_name"])
            current_best_metric_kind = normalize_text(freeze_candidate_row["recommended_metric_kind"]) or normalize_text(best_row["metric_kind"])
            current_best_f1 = numeric_float_or_blank(freeze_candidate_row["recommended_f1"])
            if current_best_f1 == "":
                current_best_f1 = numeric_float_or_blank(best_row["f1"])
            current_best_positive_support = numeric_float_or_blank(freeze_candidate_row["recommended_positive_support"])
            if current_best_positive_support == "":
                current_best_positive_support = numeric_float_or_blank(best_row["positive_support"])

        if scope == "operator_policy_proxy":
            current_operational_workflow_name = normalize_text(policy_row["recommended_policy_name"])
            current_operational_workflow_reason_ko = normalize_text(policy_row["recommended_policy_reason_ko"])
        else:
            current_operational_workflow_name = ""
            current_operational_workflow_reason_ko = ""

        freeze_recommendation = normalize_text(freeze_candidate_row["recommended_freeze_recommendation"])
        acquisition_blocked_flag = int(numeric_int(backlog_row["requires_new_truth_or_data_flag"]) == 1)
        decision = current_data_decision(scope, freeze_recommendation, scope_kind)
        claim_strength = allowed_claim_strength(decision)
        next_action = next_allowed_action(decision)
        freeze_reason_ko = freeze_reason(
            scope=scope,
            decision=decision,
            freeze_candidate_row=freeze_candidate_row,
            backlog_row=backlog_row,
            expansion_note=expansion_lookup.get(normalize_text(backlog_row["expansion_action_class"]), ""),
            policy_row={k: normalize_text(v) for k, v in policy_row.items()},
            pipeline_row=pipeline_row,
            best_row=best_row,
        )

        rows.append(
            {
                "eval_scope": scope,
                "current_best_target_name": current_best_target_name,
                "current_best_metric_kind": current_best_metric_kind,
                "current_best_f1": current_best_f1,
                "current_best_positive_support": current_best_positive_support,
                "current_operational_workflow_name": current_operational_workflow_name,
                "current_operational_workflow_reason_ko": current_operational_workflow_reason_ko,
                "freeze_recommendation": freeze_recommendation,
                "acquisition_blocked_flag": acquisition_blocked_flag,
                "current_data_decision": decision,
                "allowed_claim_strength": claim_strength,
                "next_allowed_action": next_action,
                "freeze_reason_ko": freeze_reason_ko,
            }
        )
    return pd.DataFrame(rows, columns=FREEZE_PACK_COLS)


def summary_note(decision: str) -> str:
    if decision == "freeze_as_current_default":
        return "이 row들은 추가 collection 없이도 현재 기본 결론으로 유지할 수 있다."
    if decision == "freeze_with_caution":
        return "이 row들은 현재 data 범위 안에서만 caution과 함께 사용할 수 있다."
    if decision == "exploratory_only":
        return "이 row들은 informative 하지만 underpowered 또는 blocked 상태라 exploratory claim으로만 남겨야 한다."
    return "이 row들은 workflow/operator packaging proxy 로만 정당화된다."


def build_freeze_summary(pack_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for decision in CURRENT_DATA_DECISIONS:
        scope_df = pack_df.loc[pack_df["current_data_decision"].eq(decision)].copy()
        rows.append(
            {
                "current_data_decision": decision,
                "scope_count": int(len(scope_df)),
                "operational_default_claim_count": int(scope_df["allowed_claim_strength"].eq("operational_default_claim").sum()),
                "bounded_current_data_claim_count": int(scope_df["allowed_claim_strength"].eq("bounded_current_data_claim").sum()),
                "exploratory_claim_only_count": int(scope_df["allowed_claim_strength"].eq("exploratory_claim_only").sum()),
                "workflow_claim_only_count": int(scope_df["allowed_claim_strength"].eq("workflow_claim_only").sum()),
                "note_ko": summary_note(decision),
            }
        )
    return pd.DataFrame(rows, columns=FREEZE_SUMMARY_COLS)


def build_claims(pack_df: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    policy_row = frames["policy"].iloc[0].to_dict()
    pipeline_row = frames["pipeline"].iloc[0].to_dict()
    pipeline_pass = numeric_int(pipeline_row["final_pipeline_pass_flag"])
    recommended_policy = normalize_text(policy_row["recommended_policy_name"])

    pack_lookup = {normalize_text(row["eval_scope"]): row for row in pack_df.to_dict(orient="records")}
    step4_pack_row = pack_lookup["step4_abrupt_no_precursor"]
    step4_support = numeric_int(step4_pack_row["current_best_positive_support"])
    step4_decision = normalize_text(step4_pack_row["current_data_decision"])
    if step4_decision == "exploratory_only":
        step4_claim_text = (
            f"step4 pure abrupt/no-precursor 결과는 precursor-led fault with abrupt ending 2건과 c42997a6-5881-47e7-9035-7de8a2673b54.1.1 holdout을 제외하면 현재 stored data 기준 positive support={step4_support} 로 underpowered 이다. "
            "따라서 현재는 stable detector performance 로 freeze하지 말고 exploratory result 로만 써야 한다."
        )
        step4_overclaim = "pure abrupt support 3 결과를 large-support stable benchmark 나 전체 fault-6 event count로 과장하지 말 것."
    else:
        step4_claim_text = (
            f"step4 pure abrupt/no-precursor 결과는 precursor-led fault with abrupt ending 2건과 c42997a6-5881-47e7-9035-7de8a2673b54.1.1 holdout을 제외한 pure abrupt support={step4_support} 기준으로만 읽어야 하며, "
            "현재 data 범위에 한정된 bounded current-data conclusion 으로만 유지해야 한다."
        )
        step4_overclaim = "pure abrupt 결과를 overlap precursor-led fault까지 포함한 완결된 detector 성능으로 과장하지 말 것."
    rows = [
        {
            "claim_id": "claim_step1_taxonomy",
            "claim_scope": "step1_taxonomy",
            "claim_text_ko": "step1 taxonomy/support 범위는 structural coverage 설명으로만 유지해야 하며, classifier target 선택이나 precision/recall/F1 성능 주장으로 바꾸면 안 된다.",
            "claim_strength": pack_lookup["step1_taxonomy"]["allowed_claim_strength"],
            "prohibited_overclaim_ko": "taxonomy family/support coverage를 detector 일반화 성능으로 과장하지 말 것.",
        },
        {
            "claim_id": "claim_step2_onset_truth",
            "claim_scope": "step2_onset_truth",
            "claim_text_ko": "step2 onset rows는 onset coverage/reference 설명으로만 유지해야 하며, classifier target 선택이나 hit-rate 성능 주장으로 확대하면 안 된다.",
            "claim_strength": pack_lookup["step2_onset_truth"]["allowed_claim_strength"],
            "prohibited_overclaim_ko": "onset availability/lead reference를 precision/recall/F1 성능 주장으로 과장하지 말 것.",
        },
        {
            "claim_id": "claim_step3_precursor",
            "claim_scope": "step3_precursor_performance",
            "claim_text_ko": "step3 precursor marker 결과는 informative 하지만 underpowered 이므로, 현재 data에서는 stable detector performance 로 freeze하지 말고 exploratory result 로만 써야 한다.",
            "claim_strength": pack_lookup["step3_precursor_performance"]["allowed_claim_strength"],
            "prohibited_overclaim_ko": "step3 결과를 안정된 detector 성능 또는 배포 가능한 default rule로 주장하지 말 것.",
        },
        {
            "claim_id": "claim_step4_abrupt",
            "claim_scope": "step4_abrupt_no_precursor",
            "claim_text_ko": step4_claim_text,
            "claim_strength": step4_pack_row["allowed_claim_strength"],
            "prohibited_overclaim_ko": step4_overclaim,
        },
        {
            "claim_id": "claim_step4_common_cause",
            "claim_scope": "step4_common_cause_routing",
            "claim_text_ko": "step4 common-cause routing 은 현재 data 에서는 descriptive / exploratory 수준으로만 유지해야 하며, 안정된 routing classifier 성능으로 freeze하면 안 된다.",
            "claim_strength": pack_lookup["step4_common_cause_routing"]["allowed_claim_strength"],
            "prohibited_overclaim_ko": "common-cause routing 결과를 stable operational classifier 성능으로 주장하지 말 것.",
        },
        {
            "claim_id": "claim_operator_workflow",
            "claim_scope": "operator_policy_proxy",
            "claim_text_ko": (
                f"operator_policy_proxy 에서 retrospective proxy best target 은 {pack_lookup['operator_policy_proxy']['current_best_target_name']} 이지만, "
                f"현재 chosen operational workflow 는 {recommended_policy} 이고 pipeline pass={pipeline_pass} 기준으로 운영에 사용할 수 있다. "
                "다만 이것은 operator/workflow proxy 정당화이지, step3/step4 algorithmic evaluation scope 전체가 충분히 강해졌다는 뜻은 아니다."
            ),
            "claim_strength": pack_lookup["operator_policy_proxy"]["allowed_claim_strength"],
            "prohibited_overclaim_ko": "workflow packaging/QA/pipeline validation 을 detector algorithm generalization 성능 주장으로 바꾸지 말 것.",
        },
    ]
    return pd.DataFrame(rows, columns=CLAIMS_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    frames = normalize_frames(load_inputs(root))
    validate_scopes(frames)
    pack_df = build_freeze_pack(frames)
    summary_df = build_freeze_summary(pack_df)
    claims_df = build_claims(pack_df, frames)

    pack_df.to_csv(share_dir / FREEZE_PACK_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / FREEZE_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    claims_df.to_csv(share_dir / CLAIMS_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
