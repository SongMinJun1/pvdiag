#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

FREEZE_PACK_NAME = "panel_day_engine_project_current_data_freeze_pack_v1.csv"
FREEZE_SUMMARY_NAME = "panel_day_engine_project_current_data_freeze_summary_v1.csv"
CLAIMS_NAME = "panel_day_engine_project_current_data_claims_v1.csv"
POLICY_RECOMMENDATION_NAME = "panel_day_engine_operator_attention_policy_recommendation_v1.csv"
RELEASE_GATE_MANIFEST_NAME = "panel_day_engine_operator_release_gate_manifest_v1.csv"
PIPELINE_MANIFEST_NAME = "panel_day_engine_operator_pipeline_manifest_v1.csv"
FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME = "panel_day_engine_fault_panel_event_audit_summary_v1.csv"

FINAL_DECISION_PACK_OUTPUT_NAME = "panel_day_engine_project_final_decision_pack_v1.csv"
FINAL_DECISION_SUMMARY_OUTPUT_NAME = "panel_day_engine_project_final_decision_summary_v1.csv"
FINAL_DO_DONT_OUTPUT_NAME = "panel_day_engine_project_final_do_and_dont_v1.csv"

FINAL_DECISION_PACK_COLS = [
    "eval_scope",
    "current_data_decision",
    "allowed_claim_strength",
    "current_best_target_name",
    "current_best_metric_kind",
    "current_best_f1",
    "current_best_positive_support",
    "chosen_operational_workflow_name",
    "release_gate_pass_flag",
    "pipeline_pass_flag",
    "final_usage_decision",
    "final_reason_ko",
]

FINAL_DECISION_SUMMARY_COLS = [
    "final_usage_decision",
    "scope_count",
    "operational_default_count",
    "bounded_reporting_use_count",
    "exploratory_only_count",
    "workflow_only_count",
    "release_gate_pass_flag",
    "chosen_operational_workflow_name",
    "note_ko",
]

FINAL_DO_DONT_COLS = [
    "row_id",
    "scope_or_topic",
    "do_text_ko",
    "dont_text_ko",
    "claim_strength",
    "priority_order",
]

EXPECTED_SCOPES = [
    "step1_taxonomy",
    "step2_onset_truth",
    "step3_precursor_performance",
    "step4_abrupt_no_precursor",
    "step4_common_cause_routing",
    "operator_policy_proxy",
]

FINAL_USAGE_DECISIONS = [
    "operational_default",
    "bounded_reporting_use",
    "exploratory_only",
    "workflow_only",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Produce the final decision / operational-default / handoff pack for the project under the current-data-only constraint."
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
        "freeze_pack": read_csv(share_dir / FREEZE_PACK_NAME),
        "freeze_summary": read_csv(share_dir / FREEZE_SUMMARY_NAME),
        "claims": read_csv(share_dir / CLAIMS_NAME),
        "policy": read_csv(share_dir / POLICY_RECOMMENDATION_NAME),
        "release_gate": read_csv(share_dir / RELEASE_GATE_MANIFEST_NAME),
        "pipeline": read_csv(share_dir / PIPELINE_MANIFEST_NAME),
        "fault_event_audit_summary": read_csv(share_dir / FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME),
    }

    ensure_columns(
        frames["freeze_pack"],
        [
            "eval_scope",
            "current_data_decision",
            "allowed_claim_strength",
            "current_best_target_name",
            "current_best_metric_kind",
            "current_best_f1",
            "current_best_positive_support",
            "freeze_reason_ko",
        ],
        FREEZE_PACK_NAME,
    )
    ensure_columns(
        frames["freeze_summary"],
        [
            "current_data_decision",
            "scope_count",
            "operational_default_claim_count",
            "bounded_current_data_claim_count",
            "exploratory_claim_only_count",
            "workflow_claim_only_count",
            "note_ko",
        ],
        FREEZE_SUMMARY_NAME,
    )
    ensure_columns(
        frames["claims"],
        ["claim_scope", "claim_text_ko", "claim_strength", "prohibited_overclaim_ko"],
        CLAIMS_NAME,
    )
    ensure_columns(
        frames["policy"],
        ["recommended_policy_name", "recommended_policy_reason_ko", "expected_use_ko", "caution_ko"],
        POLICY_RECOMMENDATION_NAME,
    )
    ensure_columns(
        frames["release_gate"],
        ["final_release_gate_pass_flag", "note_ko"],
        RELEASE_GATE_MANIFEST_NAME,
    )
    ensure_columns(
        frames["pipeline"],
        ["final_pipeline_pass_flag", "note_ko"],
        PIPELINE_MANIFEST_NAME,
    )
    ensure_columns(
        frames["fault_event_audit_summary"],
        ["사건유형_재판정_전조형수", "전조평가셋편입_패널수", "급작평가셋편입_패널수"],
        FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME,
    )
    return frames


def normalize_frames(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    normalized = {key: value.copy() for key, value in frames.items()}
    for df in normalized.values():
        if "eval_scope" in df.columns:
            df["eval_scope"] = df["eval_scope"].map(normalize_text)
        if "claim_scope" in df.columns:
            df["claim_scope"] = df["claim_scope"].map(normalize_text)
        if "current_data_decision" in df.columns:
            df["current_data_decision"] = df["current_data_decision"].map(normalize_text)
        if "allowed_claim_strength" in df.columns:
            df["allowed_claim_strength"] = df["allowed_claim_strength"].map(normalize_text)
    return normalized


def validate_scopes(frames: dict[str, pd.DataFrame]) -> None:
    freeze_scopes = set(frames["freeze_pack"]["eval_scope"])
    claim_scopes = set(frames["claims"]["claim_scope"])
    missing = {
        "freeze_pack": sorted(set(EXPECTED_SCOPES) - freeze_scopes),
        "claims": sorted(set(EXPECTED_SCOPES) - claim_scopes),
    }
    problems = {key: value for key, value in missing.items() if value}
    if problems:
        raise SystemExit(f"missing eval_scope coverage: {problems}")


def validate_freeze_summary(pack_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    summary_lookup = {
        normalize_text(row["current_data_decision"]): row
        for row in summary_df.to_dict(orient="records")
    }
    for decision, scope_df in pack_df.groupby("current_data_decision", dropna=False):
        decision_text = normalize_text(decision)
        if decision_text not in summary_lookup:
            raise SystemExit(f"freeze summary missing decision row: {decision_text}")
        summary_row = summary_lookup[decision_text]
        if numeric_int(summary_row["scope_count"]) != int(len(scope_df)):
            raise SystemExit(f"freeze summary scope_count mismatch for decision: {decision_text}")


def final_usage_decision(current_data_decision: str) -> str:
    if current_data_decision == "freeze_as_current_default":
        return "operational_default"
    if current_data_decision == "freeze_with_caution":
        return "bounded_reporting_use"
    if current_data_decision == "exploratory_only":
        return "exploratory_only"
    return "workflow_only"


def summary_note(decision: str, release_gate_pass_flag: int, chosen_workflow: str) -> str:
    if decision == "operational_default":
        return "이 row들은 현재 data 범위에서 default handoff 로 둘 수 있다."
    if decision == "bounded_reporting_use":
        return "이 row들은 bounded current-data reporting/handoff 로만 사용해야 한다."
    if decision == "exploratory_only":
        return "이 row들은 informative 하지만 현재는 exploratory conclusion 으로만 유지해야 한다."
    return (
        f"이 row들은 chosen operator workflow {chosen_workflow} 를 workflow 관점에서만 handoff 한다. "
        f"release gate pass={release_gate_pass_flag} 를 함께 읽어야 한다."
    ).strip()


def final_reason_for_scope(
    *,
    scope: str,
    pack_row: dict[str, object],
    chosen_workflow: str,
    chosen_workflow_reason: str,
    expected_use_ko: str,
    caution_ko: str,
    release_gate_pass_flag: int,
    pipeline_pass_flag: int,
    fault_event_summary_row: dict[str, object],
) -> str:
    current_decision = normalize_text(pack_row["current_data_decision"])
    usage_decision = final_usage_decision(current_decision)
    best_target = normalize_text(pack_row["current_best_target_name"])
    best_f1 = numeric_float_or_blank(pack_row["current_best_f1"])
    best_support = numeric_float_or_blank(pack_row["current_best_positive_support"])
    freeze_reason = normalize_text(pack_row["freeze_reason_ko"])
    interpreted_precursor_count = numeric_int(fault_event_summary_row["사건유형_재판정_전조형수"])
    strict_precursor_eval_count = numeric_int(fault_event_summary_row["전조평가셋편입_패널수"])
    pure_abrupt_eval_count = numeric_int(fault_event_summary_row["급작평가셋편입_패널수"])

    if scope == "operator_policy_proxy":
        return (
            f"현재는 추가 fault case 수집이 불가능하므로 operator scope는 detector 성능 freeze가 아니라 workflow handoff 로 읽어야 한다. "
            f"current data decision 은 {current_decision} 이고 final usage 는 {usage_decision} 다. "
            f"chosen operational workflow 는 {chosen_workflow} 이며 release gate pass={release_gate_pass_flag}, "
            f"pipeline pass={pipeline_pass_flag} 기준으로 사용할 수 있다. "
            f"{expected_use_ko}. 선택 이유는 {chosen_workflow_reason}. 다만 {caution_ko} "
            f"retrospective proxy best target ({best_target}) 과 chosen workflow 를 같은 뜻으로 쓰면 안 된다."
        ).strip()

    if scope in {"step1_taxonomy", "step2_onset_truth"}:
        return (
            f"현재는 추가 fault case 수집이 불가능하므로 {scope} 는 structural coverage/reference scope로만 유지한다. "
            f"current data decision 은 {current_decision} 이고 final usage 는 {usage_decision} 다. "
            f"이 판단은 operator workflow handoff 상태와 별개로 structural scope 자체의 reporting boundary 를 정한 것이다. "
            f"classifier target 이나 detector performance default 로 승격하면 안 된다. {freeze_reason}"
        ).strip()

    if scope == "step4_abrupt_no_precursor":
        if usage_decision == "exploratory_only":
            return (
                f"현재는 추가 fault case 수집이 불가능하고 사건 해석상 전조형 고장 패널은 {interpreted_precursor_count}개지만 순수 급작 평가셋 편입은 {pure_abrupt_eval_count}개뿐이므로, "
                "c42997a6-5881-47e7-9035-7de8a2673b54.1.1 은 전조형 고장/급격 종료로 해석하지만 엄격 전조 평가셋과 순수 급작 평가셋 모두에 넣지 않는다. "
                f"step4 pure abrupt/no-precursor scope는 positive support={best_support} 기준 exploratory only 로 유지한다. "
                f"현재 best row는 {best_target} (f1={best_f1}, positive_support={best_support}) 이지만 pure abrupt support가 작아 stable default 결론으로 쓰면 안 된다. "
                f"{freeze_reason}"
            ).strip()
        return (
            f"현재는 추가 fault case 수집이 불가능하므로 step4 pure abrupt/no-precursor scope는 사건 해석상 전조형 패널 수와 분리된 pure abrupt evaluation support={best_support} 기준으로만 읽는다. "
            f"현재 best row는 {best_target} (f1={best_f1}, positive_support={best_support}) 이고 final usage 는 {usage_decision} 다. "
            f"{freeze_reason}"
        ).strip()

    if scope == "step3_precursor_performance":
        return (
            f"현재는 추가 fault case 수집이 불가능하고 사건 해석상 전조형 고장 패널은 {interpreted_precursor_count}개지만 엄격 전조 평가셋 편입은 {strict_precursor_eval_count}개이므로, "
            f"step3 precursor scope는 positive support={best_support} 기준 exploratory only 로 유지한다. "
            f"현재 best row는 {best_target} (f1={best_f1}, positive_support={best_support}) 이지만 stable default 결론으로 쓰면 안 된다. "
            f"{freeze_reason}"
        ).strip()

    if usage_decision == "exploratory_only":
        return (
            f"현재는 추가 fault case 수집이 불가능하고 positive support 확대도 막혀 있으므로 {scope} 는 exploratory only 로 유지한다. "
            f"현재 best row는 {best_target} (f1={best_f1}, positive_support={best_support}) 이지만 stable default 결론으로 쓰면 안 된다. "
            f"이 판단은 operator workflow handoff 상태와 별개로 algorithmic evaluation scope 의 freeze boundary 를 정한 것이다. {freeze_reason}"
        ).strip()

    if usage_decision == "operational_default":
        return (
            f"현재는 추가 fault case 수집이 불가능하지만 {scope} 는 current data 안에서 operational default 로 handoff 할 수 있다. "
            f"현재 best row는 {best_target} (f1={best_f1}, positive_support={best_support}) 이고 freeze decision 도 default 허용 상태다. "
            f"다만 operator workflow status 와 별개로 current data 범위 밖으로 과장하면 안 된다. {freeze_reason}"
        ).strip()

    return (
        f"현재는 추가 fault case 수집이 불가능하므로 {scope} 는 bounded current-data reporting/handoff 로만 사용한다. "
        f"현재 best row는 {best_target} (f1={best_f1}, positive_support={best_support}) 이고 final usage 는 {usage_decision} 다. "
        f"operator workflow status 와 별개로 algorithmic default upgrade 는 보류한다. {freeze_reason}"
    ).strip()


def build_final_decision_pack(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    pack_lookup = {
        normalize_text(row["eval_scope"]): row
        for row in frames["freeze_pack"].to_dict(orient="records")
    }
    policy_row = {key: normalize_text(value) for key, value in frames["policy"].iloc[0].to_dict().items()}
    release_gate_row = frames["release_gate"].iloc[0].to_dict()
    pipeline_row = frames["pipeline"].iloc[0].to_dict()
    fault_event_summary_row = frames["fault_event_audit_summary"].iloc[0].to_dict()
    release_gate_pass_flag = numeric_int(release_gate_row["final_release_gate_pass_flag"])
    pipeline_pass_flag = numeric_int(pipeline_row["final_pipeline_pass_flag"])

    rows: list[dict[str, object]] = []
    for scope in EXPECTED_SCOPES:
        pack_row = pack_lookup[scope]
        current_data_decision_value = normalize_text(pack_row["current_data_decision"])
        usage_decision = final_usage_decision(current_data_decision_value)
        chosen_workflow = policy_row["recommended_policy_name"] if scope == "operator_policy_proxy" else ""
        final_reason_ko = final_reason_for_scope(
            scope=scope,
            pack_row=pack_row,
            chosen_workflow=chosen_workflow,
            chosen_workflow_reason=policy_row["recommended_policy_reason_ko"],
            expected_use_ko=policy_row["expected_use_ko"],
            caution_ko=policy_row["caution_ko"],
            release_gate_pass_flag=release_gate_pass_flag,
            pipeline_pass_flag=pipeline_pass_flag,
            fault_event_summary_row=fault_event_summary_row,
        )
        rows.append(
            {
                "eval_scope": scope,
                "current_data_decision": current_data_decision_value,
                "allowed_claim_strength": normalize_text(pack_row["allowed_claim_strength"]),
                "current_best_target_name": normalize_text(pack_row["current_best_target_name"]),
                "current_best_metric_kind": normalize_text(pack_row["current_best_metric_kind"]),
                "current_best_f1": numeric_float_or_blank(pack_row["current_best_f1"]),
                "current_best_positive_support": numeric_float_or_blank(pack_row["current_best_positive_support"]),
                "chosen_operational_workflow_name": chosen_workflow,
                "release_gate_pass_flag": release_gate_pass_flag,
                "pipeline_pass_flag": pipeline_pass_flag,
                "final_usage_decision": usage_decision,
                "final_reason_ko": final_reason_ko,
            }
        )
    return pd.DataFrame(rows, columns=FINAL_DECISION_PACK_COLS)


def build_final_decision_summary(pack_df: pd.DataFrame, policy_df: pd.DataFrame, release_gate_df: pd.DataFrame) -> pd.DataFrame:
    chosen_workflow = normalize_text(policy_df.iloc[0]["recommended_policy_name"])
    release_gate_pass_flag = numeric_int(release_gate_df.iloc[0]["final_release_gate_pass_flag"])

    rows: list[dict[str, object]] = []
    for decision in FINAL_USAGE_DECISIONS:
        scope_df = pack_df.loc[pack_df["final_usage_decision"].eq(decision)].copy()
        rows.append(
            {
                "final_usage_decision": decision,
                "scope_count": int(len(scope_df)),
                "operational_default_count": int(scope_df["final_usage_decision"].eq("operational_default").sum()),
                "bounded_reporting_use_count": int(scope_df["final_usage_decision"].eq("bounded_reporting_use").sum()),
                "exploratory_only_count": int(scope_df["final_usage_decision"].eq("exploratory_only").sum()),
                "workflow_only_count": int(scope_df["final_usage_decision"].eq("workflow_only").sum()),
                "release_gate_pass_flag": release_gate_pass_flag,
                "chosen_operational_workflow_name": chosen_workflow,
                "note_ko": summary_note(decision, release_gate_pass_flag, chosen_workflow),
            }
        )
    return pd.DataFrame(rows, columns=FINAL_DECISION_SUMMARY_COLS)


def build_final_do_and_dont(
    pack_df: pd.DataFrame,
    claims_df: pd.DataFrame,
    policy_df: pd.DataFrame,
    release_gate_df: pd.DataFrame,
    pipeline_df: pd.DataFrame,
) -> pd.DataFrame:
    pack_lookup = {normalize_text(row["eval_scope"]): row for row in pack_df.to_dict(orient="records")}
    claim_lookup = {normalize_text(row["claim_scope"]): row for row in claims_df.to_dict(orient="records")}
    chosen_workflow = normalize_text(policy_df.iloc[0]["recommended_policy_name"])
    release_gate_pass_flag = numeric_int(release_gate_df.iloc[0]["final_release_gate_pass_flag"])
    pipeline_pass_flag = numeric_int(pipeline_df.iloc[0]["final_pipeline_pass_flag"])

    rows = [
        {
            "row_id": "do_01_project_limit",
            "scope_or_topic": "project_current_data_limit",
            "do_text_ko": "모든 보고/발표/핸드오프에서 현재는 추가 fault case 수집이 불가능하다는 hard constraint 를 먼저 명시한다.",
            "dont_text_ko": "새 truth 없이 exploratory 또는 caution scope를 frozen default 결론으로 승격하지 말 것.",
            "claim_strength": "bounded_current_data_claim",
            "priority_order": 1,
        },
        {
            "row_id": "do_02_step1_taxonomy",
            "scope_or_topic": "step1_taxonomy",
            "do_text_ko": "step1 taxonomy 는 structural coverage/reference 설명으로만 사용한다.",
            "dont_text_ko": normalize_text(claim_lookup["step1_taxonomy"]["prohibited_overclaim_ko"]),
            "claim_strength": normalize_text(pack_lookup["step1_taxonomy"]["allowed_claim_strength"]),
            "priority_order": 2,
        },
        {
            "row_id": "do_03_step2_onset_truth",
            "scope_or_topic": "step2_onset_truth",
            "do_text_ko": "step2 onset truth 는 onset coverage/reference 설명으로만 사용한다.",
            "dont_text_ko": normalize_text(claim_lookup["step2_onset_truth"]["prohibited_overclaim_ko"]),
            "claim_strength": normalize_text(pack_lookup["step2_onset_truth"]["allowed_claim_strength"]),
            "priority_order": 3,
        },
        {
            "row_id": "do_04_step3_precursor",
            "scope_or_topic": "step3_precursor_performance",
            "do_text_ko": normalize_text(claim_lookup["step3_precursor_performance"]["claim_text_ko"]),
            "dont_text_ko": normalize_text(claim_lookup["step3_precursor_performance"]["prohibited_overclaim_ko"]),
            "claim_strength": normalize_text(pack_lookup["step3_precursor_performance"]["allowed_claim_strength"]),
            "priority_order": 4,
        },
        {
            "row_id": "do_05_step4_abrupt",
            "scope_or_topic": "step4_abrupt_no_precursor",
            "do_text_ko": normalize_text(claim_lookup["step4_abrupt_no_precursor"]["claim_text_ko"]),
            "dont_text_ko": normalize_text(claim_lookup["step4_abrupt_no_precursor"]["prohibited_overclaim_ko"]),
            "claim_strength": normalize_text(pack_lookup["step4_abrupt_no_precursor"]["allowed_claim_strength"]),
            "priority_order": 5,
        },
        {
            "row_id": "do_06_step4_common_cause",
            "scope_or_topic": "step4_common_cause_routing",
            "do_text_ko": normalize_text(claim_lookup["step4_common_cause_routing"]["claim_text_ko"]),
            "dont_text_ko": normalize_text(claim_lookup["step4_common_cause_routing"]["prohibited_overclaim_ko"]),
            "claim_strength": normalize_text(pack_lookup["step4_common_cause_routing"]["allowed_claim_strength"]),
            "priority_order": 6,
        },
        {
            "row_id": "do_07_operator_workflow",
            "scope_or_topic": "operator_workflow",
            "do_text_ko": (
                f"chosen operational workflow {chosen_workflow} 를 current operator workflow 로 handoff 하고, "
                f"release gate pass={release_gate_pass_flag}, pipeline pass={pipeline_pass_flag} 조건을 함께 적는다."
            ),
            "dont_text_ko": (
                f"{normalize_text(claim_lookup['operator_policy_proxy']['prohibited_overclaim_ko'])} "
                "retrospective proxy best target 과 chosen workflow 를 같은 뜻으로 쓰지 말 것."
            ).strip(),
            "claim_strength": normalize_text(pack_lookup["operator_policy_proxy"]["allowed_claim_strength"]),
            "priority_order": 7,
        },
    ]
    return pd.DataFrame(rows, columns=FINAL_DO_DONT_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    frames = normalize_frames(load_inputs(root))
    validate_scopes(frames)
    validate_freeze_summary(frames["freeze_pack"], frames["freeze_summary"])

    pack_df = build_final_decision_pack(frames)
    summary_df = build_final_decision_summary(pack_df, frames["policy"], frames["release_gate"])
    do_dont_df = build_final_do_and_dont(
        pack_df,
        frames["claims"],
        frames["policy"],
        frames["release_gate"],
        frames["pipeline"],
    )

    pack_df.to_csv(share_dir / FINAL_DECISION_PACK_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / FINAL_DECISION_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    do_dont_df.to_csv(share_dir / FINAL_DO_DONT_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
