#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pandas as pd

FINAL_DECISION_PACK_NAME = "panel_day_engine_project_final_decision_pack_v1.csv"
CURRENT_DATA_FREEZE_PACK_NAME = "panel_day_engine_project_current_data_freeze_pack_v1.csv"
EVAL_MATRIX_NAME = "panel_day_engine_project_eval_matrix_v1.csv"
EVAL_RELIABILITY_NAME = "panel_day_engine_project_eval_reliability_v1.csv"
PRECURSOR_ONSET_TRUTH_NAME = "panel_day_engine_precursor_onset_truth_v1.csv"
PANEL_MULTIAXIS_VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
STATUS_SNAPSHOT_NAME = "panel_day_engine_project_status_snapshot_v1.csv"
POLICY_RECOMMENDATION_NAME = "panel_day_engine_operator_attention_policy_recommendation_v1.csv"
RELEASE_GATE_MANIFEST_NAME = "panel_day_engine_operator_release_gate_manifest_v1.csv"
PIPELINE_MANIFEST_NAME = "panel_day_engine_operator_pipeline_manifest_v1.csv"

HANDOFF_PACK_OUTPUT_NAME = "panel_day_engine_project_handoff_pack_v1.md"
HANDOFF_SUMMARY_OUTPUT_NAME = "panel_day_engine_project_handoff_summary_v1.csv"

HANDOFF_SUMMARY_COLS = ["항목", "값", "비고_ko"]

EXPECTED_WORKFLOW_NAME = "baseline_plus_discovery_cluster"
EXPECTED_INTERPRETED_PRECURSOR_COUNT = 3
EXPECTED_PRECURSOR_SUPPORT = 3
EXPECTED_PURE_ABRUPT_SUPPORT = 3
EXPECTED_COMMON_CAUSE_SUPPORT = 4
EXPECTED_GPVS_APPLICABLE = 6
EXPECTED_GPVS_ATTACHED = 6
EXPECTED_GPVS_NON_TARGET = 19

C429_SITE = "conalog"
C429_PANEL_ID = "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"
C429_OPERATIONAL_DETECTION = "2025-02-20"
C429_INTERPRETIVE_ONSET = "2025-01-20"
C429_BENCHMARK_ONSET = "2025-03-18"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a synchronized Korean handoff pack from reset benchmark and onset-semantics outputs."
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


def git_text(root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return normalize_text(result.stdout)


def load_inputs(root: Path) -> dict[str, pd.DataFrame | None]:
    share_dir = root / "_share"
    frames: dict[str, pd.DataFrame | None] = {
        "final_pack": read_csv(share_dir / FINAL_DECISION_PACK_NAME),
        "freeze_pack": read_csv(share_dir / CURRENT_DATA_FREEZE_PACK_NAME),
        "eval_matrix": read_csv(share_dir / EVAL_MATRIX_NAME),
        "eval_reliability": read_csv(share_dir / EVAL_RELIABILITY_NAME),
        "precursor_truth": read_csv(share_dir / PRECURSOR_ONSET_TRUTH_NAME),
        "panel_multiaxis": read_csv(share_dir / PANEL_MULTIAXIS_VERDICT_NAME),
        "status_snapshot": read_csv(share_dir / STATUS_SNAPSHOT_NAME),
        "policy": read_csv(share_dir / POLICY_RECOMMENDATION_NAME),
        "release_gate": read_csv(share_dir / RELEASE_GATE_MANIFEST_NAME),
        "pipeline": read_csv(share_dir / PIPELINE_MANIFEST_NAME),
    }

    ensure_columns(
        frames["final_pack"],
        [
            "eval_scope",
            "current_data_decision",
            "current_best_target_name",
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
        frames["freeze_pack"],
        [
            "eval_scope",
            "current_best_target_name",
            "current_best_positive_support",
            "current_data_decision",
            "freeze_reason_ko",
        ],
        CURRENT_DATA_FREEZE_PACK_NAME,
    )
    ensure_columns(
        frames["eval_matrix"],
        [
            "eval_scope",
            "target_name",
            "support_positive",
            "note_ko",
        ],
        EVAL_MATRIX_NAME,
    )
    ensure_columns(
        frames["eval_reliability"],
        [
            "eval_scope",
            "target_name",
            "positive_support",
            "reliability_class",
            "freeze_recommendation",
            "reliability_reason_ko",
        ],
        EVAL_RELIABILITY_NAME,
    )
    ensure_columns(
        frames["precursor_truth"],
        [
            "site",
            "panel_id",
            "operational_first_precursor_detected_date",
            "operational_first_precursor_marker_name",
            "interpretive_precursor_onset_date",
            "benchmark_precursor_onset_date",
        ],
        PRECURSOR_ONSET_TRUTH_NAME,
    )
    ensure_columns(
        frames["panel_multiaxis"],
        [
            "site",
            "panel_id",
            "사건유형_ko",
            "사건유형_해석_ko",
            "최종고장양상_ko",
            "운영최초전조발견일",
            "운영최초전조마커",
            "사건해석상전조시작일",
            "benchmark전조시작일",
            "전조평가셋편입_flag",
            "급작평가셋편입_flag",
            "GPVS_적용대상_ko",
            "GPVS_부착상태_ko",
        ],
        PANEL_MULTIAXIS_VERDICT_NAME,
    )
    ensure_columns(
        frames["status_snapshot"],
        ["항목", "값", "설명_ko"],
        STATUS_SNAPSHOT_NAME,
    )
    ensure_columns(
        frames["policy"],
        [
            "recommended_policy_name",
            "recommended_policy_reason_ko",
            "expected_use_ko",
            "caution_ko",
        ],
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


def single_match(df: pd.DataFrame, *, site: str, panel_id: str, name: str) -> pd.Series:
    match = df.loc[df["site"].map(normalize_text).eq(site) & df["panel_id"].map(normalize_text).eq(panel_id)].copy()
    if len(match) != 1:
        raise SystemExit(f"{name} must contain exactly one row for {site}/{panel_id}, found {len(match)}")
    return match.iloc[0]


def single_scope_row(df: pd.DataFrame, eval_scope: str, name: str) -> pd.Series:
    match = df.loc[df["eval_scope"].map(normalize_text).eq(eval_scope)].copy()
    if len(match) != 1:
        raise SystemExit(f"{name} must contain exactly one row for eval_scope={eval_scope}, found {len(match)}")
    return match.iloc[0]


def unique_scope_support(df: pd.DataFrame, eval_scope: str, name: str) -> int:
    scope_df = df.loc[df["eval_scope"].map(normalize_text).eq(eval_scope)].copy()
    if scope_df.empty:
        raise SystemExit(f"{name} has no rows for eval_scope={eval_scope}")
    values = sorted(
        {
            numeric_int(value)
            for value in scope_df["support_positive"].tolist()
            if pd.notna(pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0])
        }
    )
    if len(values) != 1:
        raise SystemExit(f"{name} support_positive must collapse to one value for {eval_scope}, got {values}")
    return values[0]


def unique_scope_reliability(df: pd.DataFrame, eval_scope: str) -> tuple[str, str]:
    scope_df = df.loc[df["eval_scope"].map(normalize_text).eq(eval_scope)].copy()
    if scope_df.empty:
        raise SystemExit(f"{EVAL_RELIABILITY_NAME} has no rows for eval_scope={eval_scope}")
    reliability_values = sorted({normalize_text(v) for v in scope_df["reliability_class"].tolist() if normalize_text(v)})
    freeze_values = sorted({normalize_text(v) for v in scope_df["freeze_recommendation"].tolist() if normalize_text(v)})
    if len(reliability_values) != 1 or len(freeze_values) != 1:
        raise SystemExit(
            f"{EVAL_RELIABILITY_NAME} must have single reliability/freeze values for {eval_scope}, "
            f"got reliability={reliability_values}, freeze={freeze_values}"
        )
    return reliability_values[0], freeze_values[0]


def collect_facts(root: Path, frames: dict[str, pd.DataFrame | None]) -> dict[str, object]:
    final_pack = frames["final_pack"]
    freeze_pack = frames["freeze_pack"]
    eval_matrix = frames["eval_matrix"]
    eval_reliability = frames["eval_reliability"]
    precursor_truth = frames["precursor_truth"]
    panel_multiaxis = frames["panel_multiaxis"]
    policy = frames["policy"]
    release_gate = frames["release_gate"]
    pipeline = frames["pipeline"]
    status_snapshot = frames["status_snapshot"]

    policy_row = policy.iloc[0]
    chosen_workflow = normalize_text(policy_row["recommended_policy_name"])
    if chosen_workflow != EXPECTED_WORKFLOW_NAME:
        raise SystemExit(
            f"recommended workflow must be {EXPECTED_WORKFLOW_NAME}, got {chosen_workflow or '<blank>'}"
        )

    release_gate_flag = numeric_int(release_gate.iloc[0]["final_release_gate_pass_flag"])
    pipeline_pass_flag = numeric_int(pipeline.iloc[0]["final_pipeline_pass_flag"])
    if release_gate_flag != 1:
        raise SystemExit("release gate must be pass(1) for current handoff synchronization")
    if pipeline_pass_flag != 1:
        raise SystemExit("pipeline must be pass(1) for current handoff synchronization")

    step3_final = single_scope_row(final_pack, "step3_precursor_performance", FINAL_DECISION_PACK_NAME)
    step4_final = single_scope_row(final_pack, "step4_abrupt_no_precursor", FINAL_DECISION_PACK_NAME)
    if normalize_text(step3_final["final_usage_decision"]) != "exploratory_only":
        raise SystemExit("step3 precursor final_usage_decision must be exploratory_only")
    if normalize_text(step4_final["final_usage_decision"]) != "exploratory_only":
        raise SystemExit("step4 abrupt final_usage_decision must be exploratory_only")

    step3_freeze = single_scope_row(freeze_pack, "step3_precursor_performance", CURRENT_DATA_FREEZE_PACK_NAME)
    step4_freeze = single_scope_row(freeze_pack, "step4_abrupt_no_precursor", CURRENT_DATA_FREEZE_PACK_NAME)
    if normalize_text(step3_freeze["current_data_decision"]) != "exploratory_only":
        raise SystemExit("step3 precursor freeze/current_data_decision must be exploratory_only")
    if normalize_text(step4_freeze["current_data_decision"]) != "exploratory_only":
        raise SystemExit("step4 abrupt freeze/current_data_decision must be exploratory_only")

    precursor_benchmark_support = unique_scope_support(eval_matrix, "step3_precursor_performance", EVAL_MATRIX_NAME)
    pure_abrupt_benchmark_support = unique_scope_support(eval_matrix, "step4_abrupt_no_precursor", EVAL_MATRIX_NAME)
    common_cause_support = unique_scope_support(eval_matrix, "step4_common_cause_routing", EVAL_MATRIX_NAME)

    if precursor_benchmark_support != EXPECTED_PRECURSOR_SUPPORT:
        raise SystemExit(
            f"precursor benchmark support must be {EXPECTED_PRECURSOR_SUPPORT}, found {precursor_benchmark_support}"
        )
    if pure_abrupt_benchmark_support != EXPECTED_PURE_ABRUPT_SUPPORT:
        raise SystemExit(
            f"pure abrupt benchmark support must be {EXPECTED_PURE_ABRUPT_SUPPORT}, found {pure_abrupt_benchmark_support}"
        )
    if common_cause_support != EXPECTED_COMMON_CAUSE_SUPPORT:
        raise SystemExit(
            f"common-cause support must be {EXPECTED_COMMON_CAUSE_SUPPORT}, found {common_cause_support}"
        )

    step3_reliability_class, step3_freeze_recommendation = unique_scope_reliability(
        eval_reliability, "step3_precursor_performance"
    )
    step4_reliability_class, step4_freeze_recommendation = unique_scope_reliability(
        eval_reliability, "step4_abrupt_no_precursor"
    )
    if step3_reliability_class != "underpowered" or step3_freeze_recommendation != "do_not_freeze":
        raise SystemExit("step3 precursor reliability must stay underpowered/do_not_freeze")
    if step4_reliability_class != "underpowered" or step4_freeze_recommendation != "do_not_freeze":
        raise SystemExit("step4 abrupt reliability must stay underpowered/do_not_freeze")

    interpreted_precursor_count = int(panel_multiaxis["사건유형_해석_ko"].map(normalize_text).eq("전조형 고장").sum())
    gpvs_applicable_count = int(panel_multiaxis["GPVS_적용대상_ko"].map(normalize_text).eq("적용대상").sum())
    gpvs_attached_count = int(panel_multiaxis["GPVS_부착상태_ko"].map(normalize_text).eq("부착").sum())
    gpvs_non_target_count = int(panel_multiaxis["GPVS_부착상태_ko"].map(normalize_text).eq("비대상").sum())

    if interpreted_precursor_count != EXPECTED_INTERPRETED_PRECURSOR_COUNT:
        raise SystemExit(
            f"interpreted precursor panel count must be {EXPECTED_INTERPRETED_PRECURSOR_COUNT}, found {interpreted_precursor_count}"
        )
    if gpvs_applicable_count != EXPECTED_GPVS_APPLICABLE:
        raise SystemExit(f"GPVS applicable fault-panel count must be {EXPECTED_GPVS_APPLICABLE}, found {gpvs_applicable_count}")
    if gpvs_attached_count != EXPECTED_GPVS_ATTACHED:
        raise SystemExit(f"GPVS attached count must be {EXPECTED_GPVS_ATTACHED}, found {gpvs_attached_count}")
    if gpvs_non_target_count != EXPECTED_GPVS_NON_TARGET:
        raise SystemExit(f"GPVS non-target count must be {EXPECTED_GPVS_NON_TARGET}, found {gpvs_non_target_count}")

    if len(precursor_truth) != EXPECTED_PRECURSOR_SUPPORT:
        raise SystemExit(
            f"{PRECURSOR_ONSET_TRUTH_NAME} must contain {EXPECTED_PRECURSOR_SUPPORT} precursor benchmark rows, found {len(precursor_truth)}"
        )

    c429_panel_row = single_match(
        panel_multiaxis,
        site=C429_SITE,
        panel_id=C429_PANEL_ID,
        name=PANEL_MULTIAXIS_VERDICT_NAME,
    )
    c429_truth_row = single_match(
        precursor_truth,
        site=C429_SITE,
        panel_id=C429_PANEL_ID,
        name=PRECURSOR_ONSET_TRUTH_NAME,
    )

    if normalize_text(c429_panel_row["사건유형_ko"]) != "전조형 고장":
        raise SystemExit("c429 panel_multiaxis row must be 사건유형_ko=전조형 고장")
    if normalize_text(c429_panel_row["최종고장양상_ko"]) != "급격 종료":
        raise SystemExit("c429 panel_multiaxis row must be 최종고장양상_ko=급격 종료")

    c429_operational_detection = normalize_text(c429_panel_row["운영최초전조발견일"])
    c429_operational_marker = normalize_text(c429_panel_row["운영최초전조마커"])
    c429_interpretive_onset = normalize_text(c429_panel_row["사건해석상전조시작일"])
    c429_benchmark_onset = normalize_text(c429_panel_row["benchmark전조시작일"])
    c429_precursor_eval_flag = numeric_int(c429_panel_row["전조평가셋편입_flag"])
    c429_abrupt_eval_flag = numeric_int(c429_panel_row["급작평가셋편입_flag"])
    live_branch = git_text(root, ["branch", "--show-current"])
    live_head = git_text(root, ["rev-parse", "HEAD"])
    if not live_branch or not live_head:
        raise SystemExit("live git branch/head are unavailable for handoff metadata synchronization")

    branch_match = status_snapshot.loc[status_snapshot["항목"].map(normalize_text).eq("현재_브랜치")].copy()
    head_match = status_snapshot.loc[status_snapshot["항목"].map(normalize_text).eq("현재_HEAD_커밋")].copy()
    if len(branch_match) != 1 or len(head_match) != 1:
        raise SystemExit(f"{STATUS_SNAPSHOT_NAME} must contain exactly one 현재_브랜치 row and one 현재_HEAD_커밋 row")
    current_branch = normalize_text(branch_match.iloc[0]["값"])
    current_head = normalize_text(head_match.iloc[0]["값"])
    if current_branch != live_branch:
        raise SystemExit(f"{STATUS_SNAPSHOT_NAME} branch is stale: {current_branch or '<blank>'} != {live_branch}")
    if current_head != live_head:
        raise SystemExit(f"{STATUS_SNAPSHOT_NAME} head is stale: {current_head or '<blank>'} != {live_head}")

    for actual, expected, field_name in [
        (c429_operational_detection, C429_OPERATIONAL_DETECTION, "운영최초전조발견일"),
        (c429_interpretive_onset, C429_INTERPRETIVE_ONSET, "사건해석상전조시작일"),
        (c429_benchmark_onset, C429_BENCHMARK_ONSET, "benchmark전조시작일"),
        (normalize_text(c429_truth_row["operational_first_precursor_detected_date"]), C429_OPERATIONAL_DETECTION, "operational_first_precursor_detected_date"),
        (normalize_text(c429_truth_row["interpretive_precursor_onset_date"]), C429_INTERPRETIVE_ONSET, "interpretive_precursor_onset_date"),
        (normalize_text(c429_truth_row["benchmark_precursor_onset_date"]), C429_BENCHMARK_ONSET, "benchmark_precursor_onset_date"),
    ]:
        if actual != expected:
            raise SystemExit(f"c429 {field_name} must be {expected}, found {actual or '<blank>'}")
    if c429_operational_marker != "first_cond_evt":
        raise SystemExit("c429 operational first precursor marker must be first_cond_evt")
    if c429_precursor_eval_flag != 1:
        raise SystemExit("c429 panel_multiaxis row must keep 전조평가셋편입_flag=1 after benchmark sync")
    if c429_abrupt_eval_flag != 0:
        raise SystemExit("c429 panel_multiaxis row must keep 급작평가셋편입_flag=0 after benchmark sync")

    return {
        "chosen_workflow": chosen_workflow,
        "chosen_workflow_reason": normalize_text(policy_row["recommended_policy_reason_ko"]),
        "expected_use_ko": normalize_text(policy_row["expected_use_ko"]),
        "caution_ko": normalize_text(policy_row["caution_ko"]),
        "release_gate_pass_flag": release_gate_flag,
        "pipeline_pass_flag": pipeline_pass_flag,
        "interpreted_precursor_count": interpreted_precursor_count,
        "precursor_benchmark_support": precursor_benchmark_support,
        "pure_abrupt_benchmark_support": pure_abrupt_benchmark_support,
        "common_cause_support": common_cause_support,
        "gpvs_applicable_count": gpvs_applicable_count,
        "gpvs_attached_count": gpvs_attached_count,
        "gpvs_non_target_count": gpvs_non_target_count,
        "step3_reliability_class": step3_reliability_class,
        "step4_reliability_class": step4_reliability_class,
        "step3_final_usage_decision": normalize_text(step3_final["final_usage_decision"]),
        "step4_final_usage_decision": normalize_text(step4_final["final_usage_decision"]),
        "step3_target_name": normalize_text(step3_final["current_best_target_name"]),
        "step4_target_name": normalize_text(step4_final["current_best_target_name"]),
        "c429_event_type": normalize_text(c429_panel_row["사건유형_ko"]),
        "c429_terminal_pattern": normalize_text(c429_panel_row["최종고장양상_ko"]),
        "c429_operational_detection": c429_operational_detection,
        "c429_operational_marker": c429_operational_marker,
        "c429_interpretive_onset": c429_interpretive_onset,
        "c429_benchmark_onset": c429_benchmark_onset,
        "c429_precursor_eval_flag": c429_precursor_eval_flag,
        "c429_abrupt_eval_flag": c429_abrupt_eval_flag,
        "current_branch": current_branch,
        "current_head": current_head,
    }


def build_handoff_summary(facts: dict[str, object]) -> pd.DataFrame:
    rows = [
        {"항목": "사건해석_전조형_패널수", "값": facts["interpreted_precursor_count"], "비고_ko": "panel_multiaxis 사건 해석 기준"},
        {"항목": "precursor_benchmark_support", "값": facts["precursor_benchmark_support"], "비고_ko": "reset benchmark onset truth 기준"},
        {"항목": "순수급작_benchmark_support", "값": facts["pure_abrupt_benchmark_support"], "비고_ko": "step4 pure abrupt eval matrix 기준"},
        {"항목": "common_cause_support", "값": facts["common_cause_support"], "비고_ko": "step4 common-cause eval matrix 기준"},
        {"항목": "GPVS_적용대상_패널수", "값": facts["gpvs_applicable_count"], "비고_ko": "panel_multiaxis fault panel 기준"},
        {"항목": "GPVS_부착수", "값": facts["gpvs_attached_count"], "비고_ko": "panel_multiaxis direct attach 기준"},
        {"항목": "GPVS_비대상_패널수", "값": facts["gpvs_non_target_count"], "비고_ko": "비고장/미확정 panel 기준"},
        {"항목": "chosen_workflow", "값": facts["chosen_workflow"], "비고_ko": "operator attention policy recommendation 기준"},
        {"항목": "release_gate", "값": facts["release_gate_pass_flag"], "비고_ko": "release gate manifest 기준"},
        {"항목": "pipeline_pass", "값": facts["pipeline_pass_flag"], "비고_ko": "pipeline manifest 기준"},
    ]
    return pd.DataFrame(rows, columns=HANDOFF_SUMMARY_COLS)


def build_markdown(facts: dict[str, object]) -> str:
    lines = [
        "## 1. 지금 확정된 기준",
        f"- 사건 해석상 전조형 고장 패널 수는 `{facts['interpreted_precursor_count']}` 이다.",
        f"- 전조형 benchmark support 는 `{facts['precursor_benchmark_support']}` 이다.",
        f"- 순수 급작 benchmark support 는 `{facts['pure_abrupt_benchmark_support']}` 이다.",
        f"- 공통원인 이벤트 support 는 `{facts['common_cause_support']}` 이다.",
        f"- step3 precursor 와 step4 pure abrupt 는 둘 다 `{facts['step3_reliability_class']}` / `{facts['step3_final_usage_decision']}` 수준으로 유지한다.",
        "",
        "## 2. 운영 기본값",
        f"- 운영 기본 workflow 는 `{facts['chosen_workflow']}` 다.",
        f"- release gate 는 `통과` (`{facts['release_gate_pass_flag']}`) 이고 pipeline 도 `통과` (`{facts['pipeline_pass_flag']}`) 다.",
        f"- 운영 설명: {facts['expected_use_ko']}",
        f"- 선택 이유: {facts['chosen_workflow_reason']}",
        f"- 운영 주의: {facts['caution_ko']}",
        f"- GPVS 는 고장 패널 `{facts['gpvs_applicable_count']}` 개에만 적용하고 현재 `{facts['gpvs_attached_count']}` 개 모두 부착됐다.",
        f"- 비고장/미확정 패널 `{facts['gpvs_non_target_count']}` 개는 GPVS 비대상이다.",
        "",
        "## 3. 전조/급작 읽는 법",
        "- 사건 해석, 운영 최초 전조 발견일, benchmark onset, 평가셋 편입은 같은 뜻이 아니다.",
        f"- `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 은 사건 해석상 `{facts['c429_event_type']}` 이고 최종고장양상은 `{facts['c429_terminal_pattern']}` 다.",
        f"- c429 운영 최초 전조 발견은 `{facts['c429_operational_detection']}` (`{facts['c429_operational_marker']}`) 이다.",
        f"- c429 사건 해석 onset 은 `{facts['c429_interpretive_onset']}` 이고 benchmark onset 은 `{facts['c429_benchmark_onset']}` 이다.",
        f"- c429 panel row의 평가셋 편입 flag 는 전조=`{facts['c429_precursor_eval_flag']}`, 급작=`{facts['c429_abrupt_eval_flag']}` 로 분리돼 있다.",
        "- handoff benchmark 보고에서는 c429를 precursor benchmark 포함, pure abrupt benchmark 제외로 읽는다.",
        "",
        "## 4. 조심해서만 말해야 하는 것",
        "- 예전 support 문구를 그대로 재사용하면 안 된다. handoff 보고는 reset benchmark 기준만 쓴다.",
        "- 사건 해석상 전조형 패널 수와 benchmark support 를 같은 숫자라고 자동 가정하면 안 된다.",
        "- 운영 최초 전조 발견일을 사건 해석 onset 이나 benchmark onset 과 같은 뜻으로 말하면 안 된다.",
        "- step3 precursor 와 step4 pure abrupt 는 둘 다 underpowered / exploratory 이므로 detector 일반화 결론처럼 말하면 안 된다.",
        "",
        "## 5. 가장 먼저 볼 파일",
        "- `panel_day_engine_panel_multiaxis_verdict_v1.csv`",
        "- `panel_day_engine_precursor_onset_truth_v1.csv`",
        "- `panel_day_engine_project_eval_matrix_v1.csv`",
        "- `panel_day_engine_project_final_decision_pack_v1.csv`",
        "- `panel_day_engine_operator_attention_policy_recommendation_v1.csv`",
    ]
    lines.append("")
    lines.append(
        f"현재 status snapshot 기준 git context 는 branch=`{facts['current_branch']}`, HEAD=`{facts['current_head']}` 다."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    frames = load_inputs(root)
    facts = collect_facts(root, frames)
    summary_df = build_handoff_summary(facts)
    markdown_text = build_markdown(facts)

    summary_df.to_csv(share_dir / HANDOFF_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    (share_dir / HANDOFF_PACK_OUTPUT_NAME).write_text(markdown_text, encoding="utf-8")


if __name__ == "__main__":
    main()
