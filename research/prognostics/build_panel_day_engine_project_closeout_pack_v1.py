#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pandas as pd

FINAL_DECISION_PACK_NAME = "panel_day_engine_project_final_decision_pack_v1.csv"
FINAL_DECISION_SUMMARY_NAME = "panel_day_engine_project_final_decision_summary_v1.csv"
FINAL_DO_DONT_NAME = "panel_day_engine_project_final_do_and_dont_v1.csv"
HANDOFF_SUMMARY_NAME = "panel_day_engine_project_handoff_summary_v1.csv"
CURRENT_FREEZE_PACK_NAME = "panel_day_engine_project_current_data_freeze_pack_v1.csv"
INTERNAL_SHARE_CLEAN_SUMMARY_NAME = "panel_day_engine_internal_share_clean_summary_v1.csv"
ABRUPT6_SYMPTOM_MAP_NAME = "panel_day_engine_abrupt6_symptom_map_v1.csv"
KERNELLOG_PROJECT_MAPPING_NAME = "panel_day_engine_kernellog_project_mapping_v1.csv"
GPV7_PERF_SUMMARY_NAME = "panel_day_engine_gpv7_perf_summary_v1.csv"
PROGRESS_SNAPSHOT_NAME = "panel_day_engine_project_progress_snapshot_v1.csv"
POLICY_RECOMMENDATION_NAME = "panel_day_engine_operator_attention_policy_recommendation_v1.csv"
RELEASE_GATE_MANIFEST_NAME = "panel_day_engine_operator_release_gate_manifest_v1.csv"
PIPELINE_MANIFEST_NAME = "panel_day_engine_operator_pipeline_manifest_v1.csv"

HANDOFF_PACK_NAME = "panel_day_engine_project_handoff_pack_v1.md"
INTERNAL_SHARE_CLEAN_PACK_NAME = "panel_day_engine_internal_share_clean_pack_v1.md"

CLOSEOUT_PACK_OUTPUT_NAME = "panel_day_engine_project_closeout_pack_v1.md"
ARTIFACT_INDEX_OUTPUT_NAME = "panel_day_engine_project_artifact_index_v1.csv"
STATUS_SNAPSHOT_OUTPUT_NAME = "panel_day_engine_project_status_snapshot_v1.csv"

STATUS_SNAPSHOT_COLS = ["항목", "값", "설명_ko"]
ARTIFACT_INDEX_COLS = ["산출물명", "경로", "용도_ko", "지금_읽는_목적_ko", "비고_ko"]

EXPECTED_SCOPES = [
    "step1_taxonomy",
    "step2_onset_truth",
    "step3_precursor_performance",
    "step4_abrupt_no_precursor",
    "step4_common_cause_routing",
    "operator_policy_proxy",
]

EXPECTED_INTERNAL_SHARE_SECTIONS = [
    "최신 성능",
    "급작 고장 6건",
    "커널로그-프로젝트 매핑",
    "GPV 7종",
    "진행률",
]

EXPECTED_WORKFLOW_NAME = "baseline_plus_discovery_cluster"

FINAL_USAGE_TO_HANDOFF = {
    "operational_default": "지금 기본값으로 사용",
    "bounded_reporting_use": "주의해서 사용",
    "exploratory_only": "탐색용으로만 유지",
    "workflow_only": "운영 workflow 용",
}

FREEZE_TO_FINAL_USAGE = {
    "freeze_as_current_default": "operational_default",
    "freeze_with_caution": "bounded_reporting_use",
    "exploratory_only": "exploratory_only",
    "workflow_proxy_only": "workflow_only",
}

SCOPE_LABELS = {
    "step1_taxonomy": "step1 taxonomy",
    "step2_onset_truth": "step2 onset truth",
    "step3_precursor_performance": "전조형 고장",
    "step4_abrupt_no_precursor": "급작 고장",
    "step4_common_cause_routing": "같이 흔들리는 이상",
    "operator_policy_proxy": "operator workflow",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a final project closeout pack from already completed project outputs."
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
        return "unavailable"
    return normalize_text(result.stdout)


def load_inputs(root: Path) -> dict[str, object]:
    share_dir = root / "_share"
    frames: dict[str, object] = {
        "final_pack": read_csv(share_dir / FINAL_DECISION_PACK_NAME),
        "final_summary": read_csv(share_dir / FINAL_DECISION_SUMMARY_NAME),
        "do_dont": read_csv(share_dir / FINAL_DO_DONT_NAME),
        "handoff_summary": read_csv(share_dir / HANDOFF_SUMMARY_NAME),
        "freeze_pack": read_csv(share_dir / CURRENT_FREEZE_PACK_NAME),
        "clean_summary": read_csv(share_dir / INTERNAL_SHARE_CLEAN_SUMMARY_NAME),
        "abrupt6": read_csv(share_dir / ABRUPT6_SYMPTOM_MAP_NAME),
        "kernel_map": read_csv(share_dir / KERNELLOG_PROJECT_MAPPING_NAME),
        "gpv7": read_csv(share_dir / GPV7_PERF_SUMMARY_NAME),
        "progress": read_csv(share_dir / PROGRESS_SNAPSHOT_NAME),
        "policy": read_csv(share_dir / POLICY_RECOMMENDATION_NAME),
        "release_gate": read_csv(share_dir / RELEASE_GATE_MANIFEST_NAME),
        "pipeline": read_csv(share_dir / PIPELINE_MANIFEST_NAME),
        "handoff_pack_path": share_dir / HANDOFF_PACK_NAME,
        "internal_share_clean_pack_path": share_dir / INTERNAL_SHARE_CLEAN_PACK_NAME,
    }

    ensure_columns(
        frames["final_pack"],
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
        frames["final_summary"],
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
        frames["handoff_summary"],
        [
            "eval_scope",
            "current_data_decision",
            "final_usage_decision",
            "allowed_claim_strength",
            "chosen_operational_workflow_name",
            "release_gate_pass_flag",
            "pipeline_pass_flag",
            "handoff_status_ko",
        ],
        HANDOFF_SUMMARY_NAME,
    )
    ensure_columns(
        frames["freeze_pack"],
        [
            "eval_scope",
            "current_data_decision",
            "allowed_claim_strength",
            "current_best_target_name",
            "current_best_metric_kind",
            "current_best_positive_support",
            "freeze_reason_ko",
        ],
        CURRENT_FREEZE_PACK_NAME,
    )
    ensure_columns(
        frames["clean_summary"],
        ["섹션", "항목", "값_ko", "비고_ko"],
        INTERNAL_SHARE_CLEAN_SUMMARY_NAME,
    )
    ensure_columns(
        frames["abrupt6"],
        ["site", "panel_id", "고장시점", "증상명_ko", "세부근거_ko", "source_field_ko", "비고_ko"],
        ABRUPT6_SYMPTOM_MAP_NAME,
    )
    ensure_columns(
        frames["kernel_map"],
        ["커널로그_증상명", "주_프로젝트분류", "보조_프로젝트분류", "설명_ko", "주의_ko"],
        KERNELLOG_PROJECT_MAPPING_NAME,
    )
    ensure_columns(
        frames["gpv7"],
        ["고장유형_번호", "고장유형_설명_ko", "성능요약_ko", "수치_ko", "source_ref_ko"],
        GPV7_PERF_SUMMARY_NAME,
    )
    ensure_columns(
        frames["progress"],
        ["항목", "현재_완료율_추정", "현재_상태_ko", "근거_ko"],
        PROGRESS_SNAPSHOT_NAME,
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


def normalize_frames(frames: dict[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in frames.items():
        if isinstance(value, pd.DataFrame):
            df = value.copy()
            for column in df.columns:
                if df[column].dtype == object:
                    df[column] = df[column].map(normalize_text)
            normalized[key] = df
        else:
            normalized[key] = value
    return normalized


def row_lookup(df: pd.DataFrame, key: str) -> dict[str, dict[str, object]]:
    return {normalize_text(row[key]): row for row in df.to_dict(orient="records")}


def validate_inputs(root: Path, frames: dict[str, object]) -> None:
    final_pack = frames["final_pack"]
    final_summary = frames["final_summary"]
    do_dont = frames["do_dont"]
    handoff_summary = frames["handoff_summary"]
    freeze_pack = frames["freeze_pack"]
    clean_summary = frames["clean_summary"]
    abrupt6 = frames["abrupt6"]
    kernel_map = frames["kernel_map"]
    gpv7 = frames["gpv7"]
    progress = frames["progress"]
    policy = frames["policy"]
    release_gate = frames["release_gate"]
    pipeline = frames["pipeline"]
    handoff_pack_path = frames["handoff_pack_path"]
    internal_share_clean_pack_path = frames["internal_share_clean_pack_path"]

    final_scopes = set(final_pack["eval_scope"])
    handoff_scopes = set(handoff_summary["eval_scope"])
    freeze_scopes = set(freeze_pack["eval_scope"])
    for name, scope_set in [
        (FINAL_DECISION_PACK_NAME, final_scopes),
        (HANDOFF_SUMMARY_NAME, handoff_scopes),
        (CURRENT_FREEZE_PACK_NAME, freeze_scopes),
    ]:
        missing = [scope for scope in EXPECTED_SCOPES if scope not in scope_set]
        if missing:
            raise SystemExit(f"{name} missing eval_scope rows: {missing}")

    policy_name = normalize_text(policy.iloc[0]["recommended_policy_name"])
    if policy_name != EXPECTED_WORKFLOW_NAME:
        raise SystemExit(
            f"chosen operational workflow must resolve to {EXPECTED_WORKFLOW_NAME}, got: {policy_name or '<blank>'}"
        )

    if not do_dont["scope_or_topic"].eq("project_current_data_limit").any():
        raise SystemExit(f"{FINAL_DO_DONT_NAME} missing project_current_data_limit row")

    final_pack_lookup = row_lookup(final_pack, "eval_scope")
    handoff_lookup = row_lookup(handoff_summary, "eval_scope")
    freeze_lookup = row_lookup(freeze_pack, "eval_scope")
    release_gate_flag = numeric_int(release_gate.iloc[0]["final_release_gate_pass_flag"])
    pipeline_flag = numeric_int(pipeline.iloc[0]["final_pipeline_pass_flag"])

    for scope in EXPECTED_SCOPES:
        freeze_decision = normalize_text(freeze_lookup[scope]["current_data_decision"])
        expected_final_usage = FREEZE_TO_FINAL_USAGE.get(freeze_decision, "")
        actual_final_usage = normalize_text(final_pack_lookup[scope]["final_usage_decision"])
        if actual_final_usage != expected_final_usage:
            raise SystemExit(f"final usage mismatch for {scope}: {actual_final_usage} != {expected_final_usage}")
        expected_handoff = FINAL_USAGE_TO_HANDOFF.get(actual_final_usage, "")
        actual_handoff = normalize_text(handoff_lookup[scope]["handoff_status_ko"])
        if actual_handoff != expected_handoff:
            raise SystemExit(f"handoff status mismatch for {scope}: {actual_handoff} != {expected_handoff}")

    operator_row = final_pack_lookup["operator_policy_proxy"]
    if normalize_text(operator_row["chosen_operational_workflow_name"]) != policy_name:
        raise SystemExit("operator workflow mismatch between final decision pack and policy recommendation")
    if numeric_int(operator_row["release_gate_pass_flag"]) != release_gate_flag:
        raise SystemExit("release gate flag mismatch between final decision pack and release gate manifest")
    if numeric_int(operator_row["pipeline_pass_flag"]) != pipeline_flag:
        raise SystemExit("pipeline flag mismatch between final decision pack and pipeline manifest")

    summary_lookup = row_lookup(final_summary, "final_usage_decision")
    pack_counts = final_pack.groupby("final_usage_decision", dropna=False).size().to_dict()
    for decision, count in pack_counts.items():
        if decision not in summary_lookup:
            raise SystemExit(f"final decision summary missing row: {decision}")
        if numeric_int(summary_lookup[decision]["scope_count"]) != int(count):
            raise SystemExit(f"final decision summary scope_count mismatch for {decision}")

    clean_sections = set(clean_summary["섹션"])
    missing_sections = [section for section in EXPECTED_INTERNAL_SHARE_SECTIONS if section not in clean_sections]
    if missing_sections:
        raise SystemExit(f"{INTERNAL_SHARE_CLEAN_SUMMARY_NAME} missing sections: {missing_sections}")

    if len(abrupt6) != 6:
        raise SystemExit(f"{ABRUPT6_SYMPTOM_MAP_NAME} must contain 6 rows, found {len(abrupt6)}")
    if len(kernel_map) != 5:
        raise SystemExit(f"{KERNELLOG_PROJECT_MAPPING_NAME} must contain 5 rows, found {len(kernel_map)}")
    if len(gpv7) < 7:
        raise SystemExit(f"{GPV7_PERF_SUMMARY_NAME} must contain at least 7 rows, found {len(gpv7)}")

    progress_items = set(progress["항목"])
    expected_progress = {"연구/알고리즘 큰 줄기", "운영 스택", "내부 공유/정리 문서"}
    if progress_items != expected_progress:
        raise SystemExit(f"{PROGRESS_SNAPSHOT_NAME} rows mismatch: {sorted(progress_items)}")

    if not Path(handoff_pack_path).exists():
        raise SystemExit(f"missing required artifact: {handoff_pack_path}")
    if not Path(internal_share_clean_pack_path).exists():
        raise SystemExit(f"missing required artifact: {internal_share_clean_pack_path}")

    branch = git_text(root, ["branch", "--show-current"])
    head = git_text(root, ["rev-parse", "HEAD"])
    if not branch or branch == "unavailable":
        raise SystemExit("git branch information is unavailable")
    if not head or head == "unavailable":
        raise SystemExit("git HEAD information is unavailable")


def build_status_snapshot(root: Path, frames: dict[str, object]) -> pd.DataFrame:
    do_dont = frames["do_dont"]
    handoff_summary = frames["handoff_summary"]
    policy = frames["policy"]
    release_gate = frames["release_gate"]
    pipeline = frames["pipeline"]

    branch = git_text(root, ["branch", "--show-current"])
    head = git_text(root, ["rev-parse", "HEAD"])
    chosen_workflow = normalize_text(policy.iloc[0]["recommended_policy_name"])
    release_gate_flag = numeric_int(release_gate.iloc[0]["final_release_gate_pass_flag"])
    pipeline_flag = numeric_int(pipeline.iloc[0]["final_pipeline_pass_flag"])

    current_limit_row = do_dont.loc[do_dont["scope_or_topic"].eq("project_current_data_limit")].iloc[0]
    handoff_lookup = row_lookup(handoff_summary, "eval_scope")

    caution_scopes = [
        SCOPE_LABELS[scope]
        for scope in EXPECTED_SCOPES
        if normalize_text(handoff_lookup[scope]["handoff_status_ko"]) == "주의해서 사용"
    ]
    exploratory_scopes = [
        SCOPE_LABELS[scope]
        for scope in EXPECTED_SCOPES
        if normalize_text(handoff_lookup[scope]["handoff_status_ko"]) == "탐색용으로만 유지"
    ]

    final_range_value = (
        f"{', '.join(caution_scopes)}=주의 / {', '.join(exploratory_scopes)}=탐색 / "
        f"{SCOPE_LABELS['operator_policy_proxy']}=운영용"
    )

    rows = [
        {
            "항목": "현재_브랜치",
            "값": branch,
            "설명_ko": "closeout pack 생성 시점에 체크아웃된 git branch 이름이다.",
        },
        {
            "항목": "현재_HEAD_커밋",
            "값": head,
            "설명_ko": "현재 closeout 기준으로 묶인 git HEAD SHA 다.",
        },
        {
            "항목": "완료된_로드맵_최대단계",
            "값": "project_closeout_pack_v1",
            "설명_ko": "final decision, handoff, clean internal share를 거친 뒤 closeout index/summary까지 정리된 상태다.",
        },
        {
            "항목": "선택된_운영_workflow",
            "값": chosen_workflow,
            "설명_ko": "현재 운영 기본값으로 넘길 workflow choice 다. detector 일반 성능 고정 선언이 아니다.",
        },
        {
            "항목": "release_gate_통과여부",
            "값": str(release_gate_flag),
            "설명_ko": normalize_text(release_gate.iloc[0]["note_ko"]) or "operator release gate 기준 통과 여부다.",
        },
        {
            "항목": "pipeline_통과여부",
            "값": str(pipeline_flag),
            "설명_ko": normalize_text(pipeline.iloc[0]["note_ko"]) or "operator pipeline 기준 통과 여부다.",
        },
        {
            "항목": "현재_데이터_한계",
            "값": "추가 fault case 수집 불가",
            "설명_ko": normalize_text(current_limit_row["do_text_ko"]),
        },
        {
            "항목": "최종_권장_사용_범위",
            "값": final_range_value,
            "설명_ko": (
                "step1/step2 와 급작 고장은 bounded current-data 범위로, 전조형과 common-cause 는 exploratory 범위로, "
                "operator workflow 는 운영 workflow 범위로 읽는다."
            ),
        },
    ]
    return pd.DataFrame(rows).reindex(columns=STATUS_SNAPSHOT_COLS)


def artifact_specs() -> list[dict[str, str]]:
    return [
        {
            "산출물명": FINAL_DECISION_PACK_NAME,
            "경로": f"_share/{FINAL_DECISION_PACK_NAME}",
            "용도_ko": "scope별 최종 usage decision 과 claim boundary를 고정한 기준표",
            "지금_읽는_목적_ko": "지금 어떤 범위를 확정, 주의, 탐색으로 둘지 먼저 확인",
            "비고_ko": "closeout 판단의 source of truth",
        },
        {
            "산출물명": FINAL_DECISION_SUMMARY_NAME,
            "경로": f"_share/{FINAL_DECISION_SUMMARY_NAME}",
            "용도_ko": "최종 usage decision 분포를 한 줄로 요약한 표",
            "지금_읽는_목적_ko": "bounded/exploratory/workflow scope 개수를 빠르게 파악",
            "비고_ko": "workflow_only 1행 포함",
        },
        {
            "산출물명": FINAL_DO_DONT_NAME,
            "경로": f"_share/{FINAL_DO_DONT_NAME}",
            "용도_ko": "말해도 되는 것과 말하면 안 되는 것을 문장 단위로 정리한 표",
            "지금_읽는_목적_ko": "발표/공유 직전 금지 overclaim 문구를 확인",
            "비고_ko": "project current-data limit row 포함",
        },
        {
            "산출물명": HANDOFF_PACK_NAME,
            "경로": f"_share/{HANDOFF_PACK_NAME}",
            "용도_ko": "사람이 먼저 읽는 handoff markdown",
            "지금_읽는_목적_ko": "팀 내부 전달용 한 페이지 설명을 바로 읽기",
            "비고_ko": "metric table이 아니라 human-readable 문서",
        },
        {
            "산출물명": HANDOFF_SUMMARY_NAME,
            "경로": f"_share/{HANDOFF_SUMMARY_NAME}",
            "용도_ko": "eval_scope별 handoff 상태값을 요약한 표",
            "지금_읽는_목적_ko": "주의해서 사용 / 탐색용 / 운영 workflow 용 상태를 scope별로 확인",
            "비고_ko": "final usage decision을 한국어 상태로 변환",
        },
        {
            "산출물명": CURRENT_FREEZE_PACK_NAME,
            "경로": f"_share/{CURRENT_FREEZE_PACK_NAME}",
            "용도_ko": "current-data-limited freeze decision 원본",
            "지금_읽는_목적_ko": "closeout 전의 freeze reasoning을 역추적",
            "비고_ko": "closeout 이전 단계 source",
        },
        {
            "산출물명": INTERNAL_SHARE_CLEAN_PACK_NAME,
            "경로": f"_share/{INTERNAL_SHARE_CLEAN_PACK_NAME}",
            "용도_ko": "내부 공유용 clean markdown pack",
            "지금_읽는_목적_ko": "최신 성능, abrupt6, mapping, GPV, 진행률을 짧게 공유",
            "비고_ko": "seed-panel case flow 없이 묶은 요약 문서",
        },
        {
            "산출물명": ABRUPT6_SYMPTOM_MAP_NAME,
            "경로": f"_share/{ABRUPT6_SYMPTOM_MAP_NAME}",
            "용도_ko": "급작 고장 6건의 증상명 매칭표",
            "지금_읽는_목적_ko": "급작 positive universe의 증상명과 근거를 바로 확인",
            "비고_ko": "현재 stored abrupt positive 6건 기준",
        },
        {
            "산출물명": KERNELLOG_PROJECT_MAPPING_NAME,
            "경로": f"_share/{KERNELLOG_PROJECT_MAPPING_NAME}",
            "용도_ko": "커널로그 증상축과 프로젝트 사건축의 해석 매핑표",
            "지금_읽는_목적_ko": "증상명과 사건 성격을 섞어 말하지 않도록 경계 확인",
            "비고_ko": "confusion matrix가 아니라 interpretation table",
        },
        {
            "산출물명": GPV7_PERF_SUMMARY_NAME,
            "경로": f"_share/{GPV7_PERF_SUMMARY_NAME}",
            "용도_ko": "GPV 7종 by-type 성능 요약표",
            "지금_읽는_목적_ko": "외부/reference 축의 per-type stored metric을 확인",
            "비고_ko": "현재 field final decision owner는 아님",
        },
        {
            "산출물명": PROGRESS_SNAPSHOT_NAME,
            "경로": f"_share/{PROGRESS_SNAPSHOT_NAME}",
            "용도_ko": "연구, 운영 스택, 내부 공유 진행률 snapshot",
            "지금_읽는_목적_ko": "남은 마감 여지를 빠르게 파악",
            "비고_ko": "현재 85 / 95 / 70",
        },
        {
            "산출물명": POLICY_RECOMMENDATION_NAME,
            "경로": f"_share/{POLICY_RECOMMENDATION_NAME}",
            "용도_ko": "chosen operational workflow 와 선택 이유",
            "지금_읽는_목적_ko": "왜 baseline_plus_discovery_cluster 인지 근거 확인",
            "비고_ko": "operator workflow choice source",
        },
        {
            "산출물명": PIPELINE_MANIFEST_NAME,
            "경로": f"_share/{PIPELINE_MANIFEST_NAME}",
            "용도_ko": "operator pipeline pass 상태를 기록한 manifest",
            "지금_읽는_목적_ko": "운영 stack pipeline 통과 여부 확인",
            "비고_ko": "final_pipeline_pass_flag 포함",
        },
        {
            "산출물명": RELEASE_GATE_MANIFEST_NAME,
            "경로": f"_share/{RELEASE_GATE_MANIFEST_NAME}",
            "용도_ko": "operator release gate pass 상태를 기록한 manifest",
            "지금_읽는_목적_ko": "운영 stack release gate 통과 여부 확인",
            "비고_ko": "final_release_gate_pass_flag 포함",
        },
    ]


def build_artifact_index(root: Path) -> pd.DataFrame:
    rows = artifact_specs()
    for row in rows:
        path = root / row["경로"]
        if not path.exists():
            raise SystemExit(f"artifact index target is missing: {path}")
    return pd.DataFrame(rows).reindex(columns=ARTIFACT_INDEX_COLS)


def build_closeout_markdown(frames: dict[str, object]) -> str:
    final_pack = frames["final_pack"]
    do_dont = frames["do_dont"]
    policy = frames["policy"]
    release_gate = frames["release_gate"]
    pipeline = frames["pipeline"]

    pack_lookup = row_lookup(final_pack, "eval_scope")
    chosen_workflow = normalize_text(policy.iloc[0]["recommended_policy_name"])
    workflow_reason = normalize_text(policy.iloc[0]["recommended_policy_reason_ko"])
    expected_use = normalize_text(policy.iloc[0]["expected_use_ko"])
    workflow_caution = normalize_text(policy.iloc[0]["caution_ko"])
    release_gate_flag = numeric_int(release_gate.iloc[0]["final_release_gate_pass_flag"])
    pipeline_flag = numeric_int(pipeline.iloc[0]["final_pipeline_pass_flag"])
    current_limit_row = do_dont.loc[do_dont["scope_or_topic"].eq("project_current_data_limit")].iloc[0]

    return "\n".join(
        [
            "## 1. 지금 확정된 결론",
            f"- {normalize_text(current_limit_row['do_text_ko'])}",
            "- step1_taxonomy 와 step2_onset_truth 는 structural coverage/reference 범위로만 고정한다.",
            "- 급작 고장은 bounded current-data 수준으로는 사용 가능하다.",
            "",
            "## 2. 운영 기본값",
            f"- 현재 선택된 운영 기본 workflow 는 `{chosen_workflow}` 다.",
            f"- release gate 는 통과({release_gate_flag}) 했고 pipeline 도 통과({pipeline_flag}) 했다.",
            f"- 현재 운영 설명은 `{expected_use}` 이고, 선택 이유는 {workflow_reason}",
            "",
            "## 3. 조심해서만 말해야 하는 것",
            "- step1_taxonomy 는 classifier 성능이 아니라 structural coverage 로만 말한다.",
            "- step2_onset_truth 는 classifier 성능이 아니라 structural reference 로만 말한다.",
            "- 급작 고장은 `final_fault_hit_by_anchor` 기준 bounded current-data conclusion 으로만 말한다.",
            "",
            "## 4. 아직 탐색적으로만 남겨야 하는 것",
            "- 전조형 성능은 표본이 작아 탐색적이다.",
            "- common-cause/같이 흔들리는 이상은 아직 탐색적이다.",
            "- operator workflow 사용 가능 상태를 detector 일반 성능으로 과장하면 안 된다.",
            "",
            "## 5. 가장 먼저 볼 산출물",
            f"- `{FINAL_DECISION_PACK_NAME}`: scope별 최종 usage decision 을 먼저 확인한다.",
            f"- `{FINAL_DO_DONT_NAME}`: 말해도 되는 것과 말하면 안 되는 것을 바로 확인한다.",
            f"- `{HANDOFF_PACK_NAME}`: 사람이 바로 읽는 handoff 문장을 먼저 본다.",
            f"- `{INTERNAL_SHARE_CLEAN_PACK_NAME}`: 최신 성능, abrupt6, mapping, GPV, 진행률을 짧게 확인한다.",
            "",
            "## 6. 프로젝트를 다시 열면 어디서 시작할지",
            f"- 먼저 `{STATUS_SNAPSHOT_OUTPUT_NAME}` 로 branch, HEAD, workflow, release/pipeline 상태를 확인한다.",
            f"- 다음으로 `{FINAL_DECISION_PACK_NAME}` 과 `{HANDOFF_SUMMARY_NAME}` 로 scope별 사용 범위를 다시 잡는다.",
            f"- 그 다음 `{ABRUPT6_SYMPTOM_MAP_NAME}`, `{KERNELLOG_PROJECT_MAPPING_NAME}`, `{GPV7_PERF_SUMMARY_NAME}`, `{PROGRESS_SNAPSHOT_NAME}` 를 필요 순서대로 본다.",
            f"- 운영 재개가 필요하면 `{PIPELINE_MANIFEST_NAME}` 와 `{RELEASE_GATE_MANIFEST_NAME}` 를 확인하고 `{chosen_workflow}` 를 기준으로 이어간다.",
            f"- 주의: {workflow_caution}",
        ]
    ).strip() + "\n"


def write_outputs(root: Path, status_snapshot_df: pd.DataFrame, artifact_index_df: pd.DataFrame, markdown: str) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    status_snapshot_df.to_csv(share_dir / STATUS_SNAPSHOT_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    artifact_index_df.to_csv(share_dir / ARTIFACT_INDEX_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    (share_dir / CLOSEOUT_PACK_OUTPUT_NAME).write_text(markdown, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    frames = normalize_frames(load_inputs(root))
    validate_inputs(root, frames)
    status_snapshot_df = build_status_snapshot(root, frames)
    artifact_index_df = build_artifact_index(root)
    markdown = build_closeout_markdown(frames)
    write_outputs(root, status_snapshot_df, artifact_index_df, markdown)


if __name__ == "__main__":
    main()
