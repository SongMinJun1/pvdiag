#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

FINAL_DECISION_PACK_NAME = "panel_day_engine_project_final_decision_pack_v1.csv"
FINAL_DECISION_SUMMARY_NAME = "panel_day_engine_project_final_decision_summary_v1.csv"
FINAL_DO_DONT_NAME = "panel_day_engine_project_final_do_and_dont_v1.csv"
POLICY_RECOMMENDATION_NAME = "panel_day_engine_operator_attention_policy_recommendation_v1.csv"
RELEASE_GATE_MANIFEST_NAME = "panel_day_engine_operator_release_gate_manifest_v1.csv"
PIPELINE_MANIFEST_NAME = "panel_day_engine_operator_pipeline_manifest_v1.csv"

HANDOFF_PACK_OUTPUT_NAME = "panel_day_engine_project_handoff_pack_v1.md"
HANDOFF_SUMMARY_OUTPUT_NAME = "panel_day_engine_project_handoff_summary_v1.csv"

HANDOFF_SUMMARY_COLS = [
    "eval_scope",
    "current_data_decision",
    "final_usage_decision",
    "allowed_claim_strength",
    "chosen_operational_workflow_name",
    "release_gate_pass_flag",
    "pipeline_pass_flag",
    "handoff_status_ko",
]

EXPECTED_SCOPES = [
    "step1_taxonomy",
    "step2_onset_truth",
    "step3_precursor_performance",
    "step4_abrupt_no_precursor",
    "step4_common_cause_routing",
    "operator_policy_proxy",
]

EXPECTED_WORKFLOW_NAME = "baseline_plus_discovery_cluster"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a human-readable Korean handoff pack from the completed project final decision pack."
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
        "pack": read_csv(share_dir / FINAL_DECISION_PACK_NAME),
        "summary": read_csv(share_dir / FINAL_DECISION_SUMMARY_NAME),
        "do_dont": read_csv(share_dir / FINAL_DO_DONT_NAME),
        "policy": read_csv(share_dir / POLICY_RECOMMENDATION_NAME),
        "release_gate": read_csv(share_dir / RELEASE_GATE_MANIFEST_NAME),
        "pipeline": read_csv(share_dir / PIPELINE_MANIFEST_NAME),
    }

    ensure_columns(
        frames["pack"],
        [
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
        ],
        FINAL_DECISION_PACK_NAME,
    )
    ensure_columns(
        frames["summary"],
        [
            "final_usage_decision",
            "scope_count",
            "release_gate_pass_flag",
            "chosen_operational_workflow_name",
            "note_ko",
        ],
        FINAL_DECISION_SUMMARY_NAME,
    )
    ensure_columns(
        frames["do_dont"],
        ["row_id", "scope_or_topic", "do_text_ko", "dont_text_ko", "claim_strength", "priority_order"],
        FINAL_DO_DONT_NAME,
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
    return frames


def normalize_frames(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    normalized = {key: value.copy() for key, value in frames.items()}
    for df in normalized.values():
        for col in [
            "eval_scope",
            "current_data_decision",
            "allowed_claim_strength",
            "current_best_target_name",
            "current_best_metric_kind",
            "chosen_operational_workflow_name",
            "final_usage_decision",
            "scope_or_topic",
            "do_text_ko",
            "dont_text_ko",
            "recommended_policy_name",
            "recommended_policy_reason_ko",
            "expected_use_ko",
            "caution_ko",
        ]:
            if col in df.columns:
                df[col] = df[col].map(normalize_text)
    return normalized


def validate_inputs(frames: dict[str, pd.DataFrame]) -> None:
    pack_df = frames["pack"]
    summary_df = frames["summary"]
    policy_df = frames["policy"]
    release_gate_df = frames["release_gate"]
    pipeline_df = frames["pipeline"]

    scopes = list(pack_df["eval_scope"])
    missing_scopes = [scope for scope in EXPECTED_SCOPES if scope not in scopes]
    if missing_scopes:
        raise SystemExit(f"final decision pack missing eval_scope rows: {missing_scopes}")

    policy_name = normalize_text(policy_df.iloc[0]["recommended_policy_name"])
    if policy_name != EXPECTED_WORKFLOW_NAME:
        raise SystemExit(
            f"current recommended workflow must resolve to {EXPECTED_WORKFLOW_NAME}, got: {policy_name or '<blank>'}"
        )

    operator_row = pack_df.loc[pack_df["eval_scope"].eq("operator_policy_proxy")].iloc[0].to_dict()
    operator_pack_workflow = normalize_text(operator_row["chosen_operational_workflow_name"])
    if operator_pack_workflow and operator_pack_workflow != policy_name:
        raise SystemExit(
            "operator_policy_proxy chosen_operational_workflow_name does not match policy recommendation"
        )

    release_gate_flag = numeric_int(release_gate_df.iloc[0]["final_release_gate_pass_flag"])
    pipeline_flag = numeric_int(pipeline_df.iloc[0]["final_pipeline_pass_flag"])
    if numeric_int(operator_row["release_gate_pass_flag"]) != release_gate_flag:
        raise SystemExit("release gate flag mismatch between final decision pack and release gate manifest")
    if numeric_int(operator_row["pipeline_pass_flag"]) != pipeline_flag:
        raise SystemExit("pipeline flag mismatch between final decision pack and pipeline manifest")

    summary_counts = {
        normalize_text(row["final_usage_decision"]): numeric_int(row["scope_count"])
        for row in summary_df.to_dict(orient="records")
    }
    pack_counts = {
        decision: int(len(group))
        for decision, group in pack_df.groupby("final_usage_decision", dropna=False)
    }
    for decision, count in pack_counts.items():
        if summary_counts.get(normalize_text(decision), -1) != count:
            raise SystemExit(f"final decision summary scope_count mismatch for {decision}")


def handoff_status_ko(final_usage_decision: str) -> str:
    if final_usage_decision == "operational_default":
        return "지금 기본값으로 사용"
    if final_usage_decision == "bounded_reporting_use":
        return "주의해서 사용"
    if final_usage_decision == "exploratory_only":
        return "탐색용으로만 유지"
    return "운영 workflow 용"


def best_metric_text(row: dict[str, object]) -> str:
    target = normalize_text(row["current_best_target_name"])
    metric_kind = normalize_text(row["current_best_metric_kind"])
    f1 = numeric_float_or_blank(row["current_best_f1"])
    support = numeric_float_or_blank(row["current_best_positive_support"])

    if metric_kind == "structural_coverage_metric":
        return "classifier target 이 아니라 structural coverage/reference 범위다."
    return f"대표 기준은 `{target}` 이고 F1={f1}, 양성 표본수={support} 다."


def build_handoff_summary(
    pack_df: pd.DataFrame,
    chosen_workflow: str,
    release_gate_pass_flag: int,
    pipeline_pass_flag: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    pack_lookup = {normalize_text(row["eval_scope"]): row for row in pack_df.to_dict(orient="records")}
    for scope in EXPECTED_SCOPES:
        row = pack_lookup[scope]
        rows.append(
            {
                "eval_scope": scope,
                "current_data_decision": normalize_text(row["current_data_decision"]),
                "final_usage_decision": normalize_text(row["final_usage_decision"]),
                "allowed_claim_strength": normalize_text(row["allowed_claim_strength"]),
                "chosen_operational_workflow_name": chosen_workflow if scope == "operator_policy_proxy" else "",
                "release_gate_pass_flag": release_gate_pass_flag,
                "pipeline_pass_flag": pipeline_pass_flag,
                "handoff_status_ko": handoff_status_ko(normalize_text(row["final_usage_decision"])),
            }
        )
    return pd.DataFrame(rows, columns=HANDOFF_SUMMARY_COLS)


def do_dont_lines(do_dont_df: pd.DataFrame) -> list[str]:
    ordered = do_dont_df.sort_values("priority_order", kind="stable")
    lines: list[str] = []
    for row in ordered.to_dict(orient="records"):
        topic = normalize_text(row["scope_or_topic"])
        do_text = normalize_text(row["do_text_ko"])
        dont_text = normalize_text(row["dont_text_ko"])
        lines.append(f"- `{topic}`: {do_text}")
        lines.append(f"- `{topic}`: {dont_text}")
    return lines


def build_markdown(
    pack_df: pd.DataFrame,
    do_dont_df: pd.DataFrame,
    chosen_workflow: str,
    chosen_workflow_reason: str,
    expected_use_ko: str,
    caution_ko: str,
    release_gate_pass_flag: int,
    pipeline_pass_flag: int,
) -> str:
    lookup = {normalize_text(row["eval_scope"]): row for row in pack_df.to_dict(orient="records")}

    step1_row = lookup["step1_taxonomy"]
    step2_row = lookup["step2_onset_truth"]
    step3_row = lookup["step3_precursor_performance"]
    step4_abrupt_row = lookup["step4_abrupt_no_precursor"]
    step4_common_row = lookup["step4_common_cause_routing"]
    operator_row = lookup["operator_policy_proxy"]

    release_gate_text = "통과" if release_gate_pass_flag == 1 else "미통과"
    pipeline_text = "통과" if pipeline_pass_flag == 1 else "미통과"

    lines = [
        "## 1. 지금 확정해서 쓸 수 있는 것",
        "- detector 성능을 지금 `operational_default` 로 확정할 scope는 없다.",
        "- `step1_taxonomy`: structural coverage only 로 유지한다. family/support 범위를 설명하는 reference 이고 classifier 성능 결론이 아니다.",
        "- `step2_onset_truth`: structural coverage/reference only 로 유지한다. onset availability 와 lead reference 설명까지만 쓴다.",
        "",
        "## 2. 조심해서만 써야 하는 것",
        f"- `step4_abrupt_no_precursor`: bounded use / caution 범위로만 넘긴다. {best_metric_text(step4_abrupt_row)}",
        f"- `step1_taxonomy`: handoff status 는 `{handoff_status_ko(normalize_text(step1_row['final_usage_decision']))}` 이지만, structural coverage 설명으로만 쓴다.",
        f"- `step2_onset_truth`: handoff status 는 `{handoff_status_ko(normalize_text(step2_row['final_usage_decision']))}` 이지만, structural coverage/reference 설명으로만 쓴다.",
        "",
        "## 3. 아직 탐색적으로만 봐야 하는 것",
        f"- `step3_precursor_performance`: exploratory only 다. {best_metric_text(step3_row)} 표본이 작아 stable detector performance 로 말하지 않는다.",
        f"- `step4_common_cause_routing`: exploratory only 다. {best_metric_text(step4_common_row)} descriptive / exploratory 범위로만 유지한다.",
        "",
        "## 4. 운영 기본 workflow",
        f"- 현재 chosen operational workflow 는 `{chosen_workflow}` 다.",
        f"- release gate 상태는 `{release_gate_text}` (`final_release_gate_pass_flag={release_gate_pass_flag}`), pipeline 상태는 `{pipeline_text}` (`final_pipeline_pass_flag={pipeline_pass_flag}`) 다.",
        f"- 운영 목적 설명: {expected_use_ko}",
        f"- 선택 이유: {chosen_workflow_reason}",
        f"- 주의: {caution_ko}",
        f"- 이 선택은 운영 workflow choice 이지 detector generalization claim 이 아니다. retrospective proxy best target 은 `{normalize_text(operator_row['current_best_target_name'])}` 이고, chosen workflow 와 같은 뜻으로 쓰면 안 된다.",
        "",
        "## 5. 말해도 되는 것 / 말하면 안 되는 것",
    ]
    lines.extend(do_dont_lines(do_dont_df))
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    frames = normalize_frames(load_inputs(root))
    validate_inputs(frames)

    pack_df = frames["pack"]
    do_dont_df = frames["do_dont"]
    policy_row = frames["policy"].iloc[0].to_dict()
    chosen_workflow = normalize_text(policy_row["recommended_policy_name"])
    chosen_workflow_reason = normalize_text(policy_row["recommended_policy_reason_ko"])
    expected_use_ko = normalize_text(policy_row["expected_use_ko"])
    caution_ko = normalize_text(policy_row["caution_ko"])
    release_gate_pass_flag = numeric_int(frames["release_gate"].iloc[0]["final_release_gate_pass_flag"])
    pipeline_pass_flag = numeric_int(frames["pipeline"].iloc[0]["final_pipeline_pass_flag"])

    handoff_summary_df = build_handoff_summary(
        pack_df=pack_df,
        chosen_workflow=chosen_workflow,
        release_gate_pass_flag=release_gate_pass_flag,
        pipeline_pass_flag=pipeline_pass_flag,
    )
    markdown_text = build_markdown(
        pack_df=pack_df,
        do_dont_df=do_dont_df,
        chosen_workflow=chosen_workflow,
        chosen_workflow_reason=chosen_workflow_reason,
        expected_use_ko=expected_use_ko,
        caution_ko=caution_ko,
        release_gate_pass_flag=release_gate_pass_flag,
        pipeline_pass_flag=pipeline_pass_flag,
    )

    handoff_summary_df.to_csv(share_dir / HANDOFF_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    (share_dir / HANDOFF_PACK_OUTPUT_NAME).write_text(markdown_text, encoding="utf-8")


if __name__ == "__main__":
    main()
