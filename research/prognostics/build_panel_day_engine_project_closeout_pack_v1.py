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
PANEL_MULTIAXIS_VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
PANEL_MULTIAXIS_EVENT_SUPPLEMENT_NAME = "panel_day_engine_panel_multiaxis_event_supplement_v1.csv"
PANEL_MULTIAXIS_CLUSTER_SUPPLEMENT_NAME = "panel_day_engine_panel_multiaxis_cluster_supplement_v1.csv"
PANEL_MULTIAXIS_SUMMARY_NAME = "panel_day_engine_panel_multiaxis_verdict_summary_v1.csv"
FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME = "panel_day_engine_fault_panel_event_audit_summary_v1.csv"

HANDOFF_PACK_NAME = "panel_day_engine_project_handoff_pack_v1.md"
INTERNAL_SHARE_CLEAN_PACK_NAME = "panel_day_engine_internal_share_clean_pack_v1.md"

CLOSEOUT_PACK_OUTPUT_NAME = "panel_day_engine_project_closeout_pack_v1.md"
ARTIFACT_INDEX_OUTPUT_NAME = "panel_day_engine_project_artifact_index_v1.csv"
STATUS_SNAPSHOT_OUTPUT_NAME = "panel_day_engine_project_status_snapshot_v1.csv"

STATUS_SNAPSHOT_COLS = ["항목", "값", "설명_ko"]
ARTIFACT_INDEX_COLS = ["산출물명", "경로", "용도_ko", "지금_읽는_목적_ko", "비고_ko"]
HANDOFF_SUMMARY_REQUIRED_ITEMS = {
    "사건해석_전조형_패널수",
    "precursor_benchmark_support",
    "순수급작_benchmark_support",
    "common_cause_support",
    "GPVS_적용대상_패널수",
    "GPVS_부착수",
    "GPVS_비대상_패널수",
    "chosen_workflow",
    "release_gate",
    "pipeline_pass",
}

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
    "step4_common_cause_routing": "공통원인 이벤트",
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
        "panel_multiaxis_verdict": read_csv(share_dir / PANEL_MULTIAXIS_VERDICT_NAME),
        "panel_multiaxis_summary": read_csv(share_dir / PANEL_MULTIAXIS_SUMMARY_NAME),
        "fault_event_audit_summary": read_csv(share_dir / FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME),
        "handoff_pack_path": share_dir / HANDOFF_PACK_NAME,
        "internal_share_clean_pack_path": share_dir / INTERNAL_SHARE_CLEAN_PACK_NAME,
        "panel_multiaxis_verdict_path": share_dir / PANEL_MULTIAXIS_VERDICT_NAME,
        "panel_multiaxis_event_supplement_path": share_dir / PANEL_MULTIAXIS_EVENT_SUPPLEMENT_NAME,
        "panel_multiaxis_cluster_supplement_path": share_dir / PANEL_MULTIAXIS_CLUSTER_SUPPLEMENT_NAME,
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
            "항목",
            "값",
            "비고_ko",
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
        [
            "site",
            "panel_id",
            "고장시점",
            "사건유형_ko",
            "최종고장양상_ko",
            "순수급작_flag",
            "증상명_ko",
            "세부근거_ko",
            "source_field_ko",
            "비고_ko",
        ],
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
    ensure_columns(
        frames["panel_multiaxis_verdict"],
        [
            "site",
            "panel_id",
            "운영최초전조발견일",
            "운영최초전조마커",
            "사건해석상전조시작일",
            "benchmark전조시작일",
        ],
        PANEL_MULTIAXIS_VERDICT_NAME,
    )
    ensure_columns(
        frames["panel_multiaxis_summary"],
        [
            "전체_패널수",
            "고유_고장패널수",
            "사건해석_전조형_패널수",
            "사건해석_급작_패널수",
            "사건해석_전조형_급격종료_패널수",
            "사건해석_전조형_진행성악화_패널수",
            "전조흔적_패널수",
            "엄격전조평가셋_패널수",
            "순수급작평가셋_패널수",
            "해석과평가셋불일치_패널수",
            "커널로그_원인군_부착수",
            "GPVS_적용대상_패널수",
            "GPVS_부착수",
            "GPVS_미부착수",
            "GPVS_비대상수",
            "note_ko",
        ],
        PANEL_MULTIAXIS_SUMMARY_NAME,
    )
    ensure_columns(
        frames["fault_event_audit_summary"],
        ["사건유형_재판정_전조형수", "전조평가셋편입_패널수", "급작평가셋편입_패널수"],
        FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME,
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
    panel_multiaxis_summary = frames["panel_multiaxis_summary"]
    fault_event_audit_summary = frames["fault_event_audit_summary"]
    handoff_pack_path = frames["handoff_pack_path"]
    internal_share_clean_pack_path = frames["internal_share_clean_pack_path"]
    panel_multiaxis_verdict_path = frames["panel_multiaxis_verdict_path"]
    panel_multiaxis_event_supplement_path = frames["panel_multiaxis_event_supplement_path"]
    panel_multiaxis_cluster_supplement_path = frames["panel_multiaxis_cluster_supplement_path"]

    final_scopes = set(final_pack["eval_scope"])
    freeze_scopes = set(freeze_pack["eval_scope"])
    for name, scope_set in [
        (FINAL_DECISION_PACK_NAME, final_scopes),
        (CURRENT_FREEZE_PACK_NAME, freeze_scopes),
    ]:
        missing = [scope for scope in EXPECTED_SCOPES if scope not in scope_set]
        if missing:
            raise SystemExit(f"{name} missing eval_scope rows: {missing}")

    handoff_items = set(handoff_summary["항목"])
    missing_handoff_items = sorted(HANDOFF_SUMMARY_REQUIRED_ITEMS - handoff_items)
    if missing_handoff_items:
        raise SystemExit(f"{HANDOFF_SUMMARY_NAME} missing metric rows: {missing_handoff_items}")

    policy_name = normalize_text(policy.iloc[0]["recommended_policy_name"])
    if policy_name != EXPECTED_WORKFLOW_NAME:
        raise SystemExit(
            f"chosen operational workflow must resolve to {EXPECTED_WORKFLOW_NAME}, got: {policy_name or '<blank>'}"
        )

    if not do_dont["scope_or_topic"].eq("project_current_data_limit").any():
        raise SystemExit(f"{FINAL_DO_DONT_NAME} missing project_current_data_limit row")

    final_pack_lookup = row_lookup(final_pack, "eval_scope")
    freeze_lookup = row_lookup(freeze_pack, "eval_scope")
    handoff_lookup = row_lookup(handoff_summary, "항목")
    release_gate_flag = numeric_int(release_gate.iloc[0]["final_release_gate_pass_flag"])
    pipeline_flag = numeric_int(pipeline.iloc[0]["final_pipeline_pass_flag"])

    if normalize_text(handoff_lookup["chosen_workflow"]["값"]) != policy_name:
        raise SystemExit("handoff chosen_workflow must match policy recommendation")
    if numeric_int(handoff_lookup["release_gate"]["값"]) != release_gate_flag:
        raise SystemExit("handoff release_gate must match release gate manifest")
    if numeric_int(handoff_lookup["pipeline_pass"]["값"]) != pipeline_flag:
        raise SystemExit("handoff pipeline_pass must match pipeline manifest")

    for scope in EXPECTED_SCOPES:
        freeze_decision = normalize_text(freeze_lookup[scope]["current_data_decision"])
        expected_final_usage = FREEZE_TO_FINAL_USAGE.get(freeze_decision, "")
        actual_final_usage = normalize_text(final_pack_lookup[scope]["final_usage_decision"])
        if actual_final_usage != expected_final_usage:
            raise SystemExit(f"final usage mismatch for {scope}: {actual_final_usage} != {expected_final_usage}")
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

    if len(panel_multiaxis_summary) != 1:
        raise SystemExit(f"{PANEL_MULTIAXIS_SUMMARY_NAME} must contain exactly one row, found {len(panel_multiaxis_summary)}")
    if len(fault_event_audit_summary) != 1:
        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_SUMMARY_NAME} must contain exactly one row, found {len(fault_event_audit_summary)}")

    if not Path(handoff_pack_path).exists():
        raise SystemExit(f"missing required artifact: {handoff_pack_path}")
    if not Path(internal_share_clean_pack_path).exists():
        raise SystemExit(f"missing required artifact: {internal_share_clean_pack_path}")
    if not Path(panel_multiaxis_verdict_path).exists():
        raise SystemExit(f"missing required artifact: {panel_multiaxis_verdict_path}")
    if not Path(panel_multiaxis_event_supplement_path).exists():
        raise SystemExit(f"missing required artifact: {panel_multiaxis_event_supplement_path}")
    if not Path(panel_multiaxis_cluster_supplement_path).exists():
        raise SystemExit(f"missing required artifact: {panel_multiaxis_cluster_supplement_path}")

    branch = git_text(root, ["branch", "--show-current"])
    head = git_text(root, ["rev-parse", "HEAD"])
    if not branch or branch == "unavailable":
        raise SystemExit("git branch information is unavailable")
    if not head or head == "unavailable":
        raise SystemExit("git HEAD information is unavailable")


def build_status_snapshot(root: Path, frames: dict[str, object]) -> pd.DataFrame:
    do_dont = frames["do_dont"]
    final_pack = frames["final_pack"]
    policy = frames["policy"]
    release_gate = frames["release_gate"]
    pipeline = frames["pipeline"]
    panel_multiaxis_summary = frames["panel_multiaxis_summary"]

    branch = git_text(root, ["branch", "--show-current"])
    head = git_text(root, ["rev-parse", "HEAD"])
    chosen_workflow = normalize_text(policy.iloc[0]["recommended_policy_name"])
    release_gate_flag = numeric_int(release_gate.iloc[0]["final_release_gate_pass_flag"])
    pipeline_flag = numeric_int(pipeline.iloc[0]["final_pipeline_pass_flag"])

    current_limit_row = do_dont.loc[do_dont["scope_or_topic"].eq("project_current_data_limit")].iloc[0]
    final_pack_lookup = row_lookup(final_pack, "eval_scope")
    multiaxis_row = panel_multiaxis_summary.iloc[0]

    caution_scopes = [
        SCOPE_LABELS[scope]
        for scope in EXPECTED_SCOPES
        if normalize_text(final_pack_lookup[scope]["final_usage_decision"]) == "bounded_reporting_use"
    ]
    exploratory_scopes = [
        SCOPE_LABELS[scope]
        for scope in EXPECTED_SCOPES
        if normalize_text(final_pack_lookup[scope]["final_usage_decision"]) == "exploratory_only"
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
                "step1/step2 는 bounded current-data 범위로, 전조형/순수 급작/공통원인은 current handoff summary 기준 exploratory 범위로, "
                "operator workflow 는 운영 workflow 범위로 읽는다."
            ),
        },
        {
            "항목": "패널_3축통합판정_행수",
            "값": str(numeric_int(multiaxis_row["전체_패널수"])),
            "설명_ko": "panel-level 대표판정표에 현재 몇 개 panel row가 있는지 보여준다.",
        },
        {
            "항목": "패널_3축통합판정_GPVS부착수",
            "값": str(numeric_int(multiaxis_row["GPVS_부착수"])),
            "설명_ko": "panel-level 3축 대표판정표에서 GPVS reference type이 실제 붙은 panel 수다.",
        },
        {
            "항목": "패널_3축통합판정_GPVS미부착수",
            "값": str(numeric_int(multiaxis_row["GPVS_미부착수"])),
            "설명_ko": "panel-level 3축 대표판정표에서 GPVS가 아직 미부착으로 남은 panel 수다.",
        },
        {
            "항목": "패널_3축통합판정_커널로그원인군부착수",
            "값": str(numeric_int(multiaxis_row["커널로그_원인군_부착수"])),
            "설명_ko": "panel-level 3축 대표판정표에서 커널로그 원인군까지 붙은 panel 수다.",
        },
    ]
    return pd.DataFrame(rows).reindex(columns=STATUS_SNAPSHOT_COLS)


def artifact_specs() -> list[dict[str, str]]:
    return [
        {
            "산출물명": PANEL_MULTIAXIS_VERDICT_NAME,
            "경로": f"_share/{PANEL_MULTIAXIS_VERDICT_NAME}",
            "용도_ko": "패널별 대표판정 한 줄표",
            "지금_읽는_목적_ko": "한 패널의 우리판정, 커널로그 판정, GPVS 참고판정, 운영위치를 한 줄로 먼저 확인",
            "비고_ko": "현재 reader-facing main summary artifact",
        },
        {
            "산출물명": PANEL_MULTIAXIS_EVENT_SUPPLEMENT_NAME,
            "경로": f"_share/{PANEL_MULTIAXIS_EVENT_SUPPLEMENT_NAME}",
            "용도_ko": "한 패널의 복수 사건이력 보조표",
            "지금_읽는_목적_ko": "전조형 고장(급격 종료)처럼 event type과 terminal pattern을 같이 확인",
            "비고_ko": "대표판정 한 줄에 다 안 담기는 사건이력 보존용",
        },
        {
            "산출물명": PANEL_MULTIAXIS_CLUSTER_SUPPLEMENT_NAME,
            "경로": f"_share/{PANEL_MULTIAXIS_CLUSTER_SUPPLEMENT_NAME}",
            "용도_ko": "공통원인 이벤트 클러스터 보조표",
            "지금_읽는_목적_ko": "panel row와 분리된 discovery/common-cause cluster를 따로 확인",
            "비고_ko": "cluster row는 panel verdict 표와 분리 유지",
        },
        {
            "산출물명": PANEL_MULTIAXIS_SUMMARY_NAME,
            "경로": f"_share/{PANEL_MULTIAXIS_SUMMARY_NAME}",
            "용도_ko": "3축 판정 전체 개요",
            "지금_읽는_목적_ko": "패널 수, GPVS 부착 수, 커널로그 부착 수를 한 번에 확인",
            "비고_ko": "panel multiaxis verdict coverage summary",
        },
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
            "용도_ko": "handoff 핵심 지표를 세로형 row로 정리한 compact 요약표",
            "지금_읽는_목적_ko": "전조/급작/support/GPVS/workflow/release/pipeline 값을 한 번에 확인",
            "비고_ko": "old wide eval-scope table이 아니라 compact row summary",
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
            "용도_ko": "fault 6건의 증상명 + 사건유형/최종고장양상 매칭표",
            "지금_읽는_목적_ko": "순수 급작 3건, 전조형 고장(진행성 악화) 2건, 전조형 고장(급격 종료) 1건을 구분해서 확인",
            "비고_ko": "6행을 유지하지만 pure abrupt count는 3으로 읽고 사건유형과 최종고장양상은 분리해서 본다",
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


def build_closeout_markdown(frames: dict[str, object], status_snapshot_df: pd.DataFrame) -> str:
    final_pack = frames["final_pack"]
    do_dont = frames["do_dont"]
    policy = frames["policy"]
    release_gate = frames["release_gate"]
    pipeline = frames["pipeline"]
    panel_multiaxis_verdict = frames["panel_multiaxis_verdict"]
    panel_multiaxis_summary = frames["panel_multiaxis_summary"]
    fault_event_audit_summary = frames["fault_event_audit_summary"]
    status_snapshot_lookup = row_lookup(status_snapshot_df, "항목")

    pack_lookup = row_lookup(final_pack, "eval_scope")
    chosen_workflow = normalize_text(policy.iloc[0]["recommended_policy_name"])
    workflow_reason = normalize_text(policy.iloc[0]["recommended_policy_reason_ko"])
    expected_use = normalize_text(policy.iloc[0]["expected_use_ko"])
    workflow_caution = normalize_text(policy.iloc[0]["caution_ko"])
    release_gate_flag = numeric_int(release_gate.iloc[0]["final_release_gate_pass_flag"])
    pipeline_flag = numeric_int(pipeline.iloc[0]["final_pipeline_pass_flag"])
    current_limit_row = do_dont.loc[do_dont["scope_or_topic"].eq("project_current_data_limit")].iloc[0]
    multiaxis_row = panel_multiaxis_summary.iloc[0]
    fault_audit_row = fault_event_audit_summary.iloc[0]
    multiaxis_total = numeric_int(multiaxis_row["전체_패널수"])
    multiaxis_gpvs_applicable = numeric_int(multiaxis_row["GPVS_적용대상_패널수"])
    multiaxis_gpvs_attached = numeric_int(multiaxis_row["GPVS_부착수"])
    multiaxis_gpvs_unattached = numeric_int(multiaxis_row["GPVS_미부착수"])
    multiaxis_gpvs_nontarget = numeric_int(multiaxis_row["GPVS_비대상수"])
    interpreted_precursor_count = numeric_int(multiaxis_row["사건해석_전조형_패널수"])
    interpreted_abrupt_count = numeric_int(multiaxis_row["사건해석_급작_패널수"])
    precursor_abrupt_ending_count = numeric_int(multiaxis_row["사건해석_전조형_급격종료_패널수"])
    precursor_progressive_count = numeric_int(multiaxis_row["사건해석_전조형_진행성악화_패널수"])
    precursor_benchmark_support = numeric_int(pack_lookup["step3_precursor_performance"]["current_best_positive_support"])
    pure_abrupt_benchmark_support = numeric_int(pack_lookup["step4_abrupt_no_precursor"]["current_best_positive_support"])
    c429_df = panel_multiaxis_verdict.loc[
        panel_multiaxis_verdict["site"].eq("conalog")
        & panel_multiaxis_verdict["panel_id"].eq("c42997a6-5881-47e7-9035-7de8a2673b54.1.1")
    ].copy()
    if len(c429_df) != 1:
        raise SystemExit("closeout requires exactly one c42997 row in panel multiaxis verdict table")
    c429_row = c429_df.iloc[0]
    c429_operational_detection = normalize_text(c429_row["운영최초전조발견일"])
    c429_interpretive_onset = normalize_text(c429_row["사건해석상전조시작일"])
    c429_benchmark_onset = normalize_text(c429_row["benchmark전조시작일"])
    c429_operational_marker = normalize_text(c429_row["운영최초전조마커"])
    current_branch = normalize_text(status_snapshot_lookup["현재_브랜치"]["값"])
    current_head = normalize_text(status_snapshot_lookup["현재_HEAD_커밋"]["값"])
    if not (c429_operational_detection and c429_interpretive_onset and c429_benchmark_onset):
        raise SystemExit("closeout c42997 row must expose operational/interpretive/benchmark onset dates")
    if not current_branch or not current_head:
        raise SystemExit("closeout status snapshot must expose non-empty current branch/head values")
    if interpreted_precursor_count != numeric_int(fault_audit_row["사건유형_재판정_전조형수"]):
        raise SystemExit("closeout precursor interpretation count mismatch between multiaxis summary and fault audit summary")
    if precursor_benchmark_support != interpreted_precursor_count:
        raise SystemExit("closeout precursor benchmark support must match interpreted precursor count after benchmark reset")
    if pure_abrupt_benchmark_support != numeric_int(fault_audit_row["급작평가셋편입_패널수"]):
        raise SystemExit("closeout pure abrupt benchmark support mismatch between final pack and fault audit summary")

    return "\n".join(
        [
            "## 1. 지금 확정된 결론",
            f"- {normalize_text(current_limit_row['do_text_ko'])}",
            "- step1_taxonomy 와 step2_onset_truth 는 structural coverage/reference 범위로만 고정한다.",
            f"- 사건 해석상 전조형 고장 패널은 {interpreted_precursor_count}건이고, 이 중 {precursor_abrupt_ending_count}건은 급격 종료, {precursor_progressive_count}건은 진행성 악화로 본다.",
            "- 즉 전조형 고장이 급격 종료로 끝난 경우가 있어 event type 과 terminal failure pattern 을 분리해서 읽어야 한다.",
            f"- benchmark reset 이후 전조형 benchmark support 는 {precursor_benchmark_support}건이고, 순수 급작 benchmark support 는 {pure_abrupt_benchmark_support}건이다.",
            "- 이전 benchmark count wording은 obsolete 이며, closeout reporting 은 reset된 benchmark truth만을 기준으로 읽는다.",
            f"- 순수 급작 사건은 현재 stored data 기준 {pure_abrupt_benchmark_support}건이다.",
            "- c42997a6-5881-47e7-9035-7de8a2673b54.1.1 은 전조형 고장/급격 종료로 해석되며 precursor benchmark에는 포함되고 pure abrupt benchmark에서는 제외된다.",
            "- 운영상 최초 전조 발견일은 benchmark onset 과 다를 수 있다.",
            "- 사건 해석용 onset, 운영 detection onset, benchmark onset 을 분리해서 읽어야 한다.",
            f"- c42997a6-5881-47e7-9035-7de8a2673b54.1.1 예시: interpretive onset = {c429_interpretive_onset}, operational detection = {c429_operational_detection}, benchmark onset = {c429_benchmark_onset}",
            f"- 사건 해석상 급작 고장 패널은 현재 stored data 기준 {interpreted_abrupt_count}건이다.",
            f"- 패널별 대표판정표가 이제 완성돼서 `{PANEL_MULTIAXIS_VERDICT_NAME}` 한 장으로 panel {multiaxis_total}개의 대표상태를 볼 수 있다.",
            "",
            "## 2. 운영 기본값",
            f"- 현재 선택된 운영 기본 workflow 는 `{chosen_workflow}` 다.",
            f"- release gate 는 통과({release_gate_flag}) 했고 pipeline 도 통과({pipeline_flag}) 했다.",
            f"- 현재 운영 설명은 `{expected_use}` 이고, 선택 이유는 {workflow_reason}",
            f"- 한 패널에 대해 우리판정 / 커널로그 판정 / GPVS 참고판정 / 운영위치를 한 줄로 같이 본다.",
            "",
            "## 3. 조심해서만 말해야 하는 것",
            "- step1_taxonomy 는 classifier 성능이 아니라 structural coverage 로만 말한다.",
            "- step2_onset_truth 는 classifier 성능이 아니라 structural reference 로만 말한다.",
            "- event type 과 terminal failure pattern 을 같은 뜻으로 말하면 안 된다.",
            "- 운영상 최초 전조 발견일을 사건 해석 onset 이나 benchmark onset 과 같은 뜻으로 말하면 안 된다.",
            "- 사건 해석과 benchmark 편입을 섞어 한 문장으로 말하면 안 된다.",
            f"- 현재 사건 해석상 전조형 고장 패널은 {interpreted_precursor_count}개이고, precursor benchmark support 도 {precursor_benchmark_support}건이다.",
            "- c42997a6-5881-47e7-9035-7de8a2673b54.1.1 은 현재 재감사 family hint `open_or_device_issue_like` 를 유지하되 precursor benchmark에는 포함되고 pure abrupt benchmark에서는 제외한다.",
            f"- c42997a6-5881-47e7-9035-7de8a2673b54.1.1 의 운영상 최초 전조 발견은 `{c429_operational_marker or 'unknown'}` 기준 {c429_operational_detection} 이고, 사건 해석 onset {c429_interpretive_onset}, benchmark onset {c429_benchmark_onset} 과는 역할이 다르다.",
            f"- 순수 급작 고장은 `final_fault_hit_by_anchor` 기준 pure abrupt support {pure_abrupt_benchmark_support}건으로만 읽는다.",
            f"- GPVS 는 fault-family reference axis라 고장 panel {multiaxis_gpvs_applicable}개에만 적용하고, 그중 {multiaxis_gpvs_attached}개에만 현재 직접 부착돼 있다.",
            f"- 현재 direct GPVS 미부착 고장 panel 은 {multiaxis_gpvs_unattached}개이고, 비고장/미확정 panel {multiaxis_gpvs_nontarget}개는 GPVS 비대상이다.",
            "- `GPVS_내부참고유형_ko` 는 우리 시스템 내부 해석이다.",
            "- `GPVS_외부참조패턴_ko` 는 외부 GPVS 시나리오를 MLPE 운영 언어로 정리한 참조 패턴명이다. 예: `국소 출력 불균형형`, `장치 응답 이상형`.",
            "- `GPVS_참조사용등급_ko` 는 해당 패널에서 reference로 얼마나 믿을 수 있는지다.",
            "- GPVS 는 direct root-cause classifier 가 아니라 reference layer 다.",
            "",
            "## 4. 아직 탐색적으로만 남겨야 하는 것",
            "- 전조형 성능은 표본이 작아 탐색적이다.",
            "- 공통원인 이벤트는 아직 탐색적이다.",
            f"- precursor benchmark support {precursor_benchmark_support}건과 pure abrupt benchmark support {pure_abrupt_benchmark_support}건 모두 아직 작아 해석은 탐색적으로만 남겨야 한다.",
            "- operator workflow 사용 가능 상태를 detector 일반 성능으로 과장하면 안 된다.",
            "",
            "## 5. 가장 먼저 볼 산출물",
            f"- `{PANEL_MULTIAXIS_VERDICT_NAME}`: panel reader-facing 대표판정을 가장 먼저 본다.",
            f"- `{FINAL_DECISION_PACK_NAME}`: scope별 최종 usage decision 을 바로 이어서 확인한다.",
            f"- `panel_day_engine_operator_workflow_default_v1.csv`: 현재 운영 queue/watch 기본 row 를 확인한다.",
            f"- `{FINAL_DO_DONT_NAME}`: 말해도 되는 것과 말하면 안 되는 것을 마지막으로 체크한다.",
            "",
            "## 6. 프로젝트를 다시 열면 어디서 시작할지",
            f"- 먼저 `{STATUS_SNAPSHOT_OUTPUT_NAME}` 로 branch, HEAD, workflow, release/pipeline 상태를 확인한다.",
            f"- 현재 closeout snapshot 기준 git context 는 branch=`{current_branch}`, HEAD=`{current_head}` 다.",
            f"- 다음으로 `{PANEL_MULTIAXIS_VERDICT_NAME}` 와 `{PANEL_MULTIAXIS_EVENT_SUPPLEMENT_NAME}` 로 panel 대표판정과 사건유형/최종고장양상 보조정보를 같이 본다.",
            f"- 그 다음 `{FINAL_DECISION_PACK_NAME}` 과 `{HANDOFF_SUMMARY_NAME}` 로 scope별 사용 범위를 다시 잡는다.",
            f"- 이후 `{ABRUPT6_SYMPTOM_MAP_NAME}`, `{KERNELLOG_PROJECT_MAPPING_NAME}`, `{GPV7_PERF_SUMMARY_NAME}`, `{PROGRESS_SNAPSHOT_NAME}` 를 필요 순서대로 본다.",
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
    markdown = build_closeout_markdown(frames, status_snapshot_df)
    write_outputs(root, status_snapshot_df, artifact_index_df, markdown)


if __name__ == "__main__":
    main()
