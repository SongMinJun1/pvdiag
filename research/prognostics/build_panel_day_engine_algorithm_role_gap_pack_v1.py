#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

FINAL_DECISION_PACK_NAME = "panel_day_engine_project_final_decision_pack_v1.csv"
CURRENT_FREEZE_PACK_NAME = "panel_day_engine_project_current_data_freeze_pack_v1.csv"
HANDOFF_SUMMARY_NAME = "panel_day_engine_project_handoff_summary_v1.csv"
PROJECT_EVAL_MATRIX_NAME = "panel_day_engine_project_eval_matrix_v1.csv"
NON_PRECURSOR_CASES_NAME = "panel_day_engine_non_precursor_performance_cases_v1.csv"
POLICY_RECOMMENDATION_NAME = "panel_day_engine_operator_attention_policy_recommendation_v1.csv"
PIPELINE_MANIFEST_NAME = "panel_day_engine_operator_pipeline_manifest_v1.csv"

ROLE_MAP_OUTPUT_NAME = "panel_day_engine_algorithm_role_map_v1.csv"
GAP_MAP_OUTPUT_NAME = "panel_day_engine_algorithm_gap_map_v1.csv"
DECISION_FLOW_OUTPUT_NAME = "panel_day_engine_algorithm_decision_flow_v1.md"

ROLE_MAP_COLS = [
    "알고리즘명",
    "현재_역할_ko",
    "주출력_ko",
    "직접_판정하는것_ko",
    "직접_판정못하는것_ko",
    "현재_프로젝트내_위치_ko",
    "현재_신뢰수준_ko",
    "근거_ko",
]

GAP_MAP_COLS = [
    "gap_topic",
    "현재_상태_ko",
    "해결여부",
    "아직_남은_한계_ko",
    "현재_허용_판정범위_ko",
    "금지_overclaim_ko",
]

EXPECTED_SCOPES = [
    "step1_taxonomy",
    "step2_onset_truth",
    "step3_precursor_performance",
    "step4_abrupt_no_precursor",
    "step4_common_cause_routing",
    "operator_policy_proxy",
]

REQUIRED_GAP_TOPICS = [
    "세 알고리즘 역할 고정",
    "세 알고리즘 우선순위 고정",
    "커널로그 증상축 ↔ 프로젝트 사건축 매핑",
    "GPV 외부참고축 위치 고정",
    "물리 원인명 확정 한계",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Formalize the roles, boundaries, and interaction of the current project's three algorithm axes."
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


def numeric_float_or_blank(value: object) -> float | str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return "" if pd.isna(numeric) else float(numeric)


def numeric_int(value: object) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return 0 if pd.isna(numeric) else int(numeric)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def load_inputs(root: Path) -> dict[str, pd.DataFrame]:
    share_dir = root / "_share"
    frames = {
        "final_decision": read_csv(share_dir / FINAL_DECISION_PACK_NAME),
        "freeze_pack": read_csv(share_dir / CURRENT_FREEZE_PACK_NAME),
        "handoff_summary": read_csv(share_dir / HANDOFF_SUMMARY_NAME),
        "project_eval": read_csv(share_dir / PROJECT_EVAL_MATRIX_NAME),
        "non_precursor": read_csv(share_dir / NON_PRECURSOR_CASES_NAME),
        "policy": read_csv(share_dir / POLICY_RECOMMENDATION_NAME),
        "pipeline": read_csv(share_dir / PIPELINE_MANIFEST_NAME),
    }

    ensure_columns(
        frames["final_decision"],
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
        frames["freeze_pack"],
        [
            "eval_scope",
            "current_data_decision",
            "freeze_reason_ko",
        ],
        CURRENT_FREEZE_PACK_NAME,
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
        frames["project_eval"],
        [
            "eval_scope",
            "metric_kind",
            "target_name",
            "support_positive",
            "f1",
            "note_ko",
        ],
        PROJECT_EVAL_MATRIX_NAME,
    )
    ensure_columns(
        frames["non_precursor"],
        [
            "eval_bucket_v2",
            "vendor_fault_family",
            "candidate_validity",
            "vendor_reply_class",
        ],
        NON_PRECURSOR_CASES_NAME,
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
        frames["pipeline"],
        ["final_pipeline_pass_flag", "note_ko"],
        PIPELINE_MANIFEST_NAME,
    )

    for df in frames.values():
        for column in df.columns:
            if df[column].dtype == object:
                df[column] = df[column].map(normalize_text)
    return frames


def validate_scope_coverage(frames: dict[str, pd.DataFrame]) -> None:
    for frame_name in ["final_decision", "freeze_pack", "handoff_summary"]:
        scope_set = set(frames[frame_name]["eval_scope"].tolist())
        missing = sorted(set(EXPECTED_SCOPES) - scope_set)
        if missing:
            raise SystemExit(f"{frame_name} missing eval_scope rows: {missing}")


def existing_refs(root: Path, candidates: list[str]) -> list[str]:
    refs: list[str] = []
    for relative_path in candidates:
        if (root / relative_path).exists():
            refs.append(relative_path)
    return refs


def refs_text(root: Path, candidates: list[str]) -> str:
    refs = existing_refs(root, candidates)
    return ", ".join(refs) if refs else "repo-local refs not found"


def handoff_lookup(handoff_df: pd.DataFrame) -> dict[str, dict[str, object]]:
    return {
        normalize_text(row["eval_scope"]): row
        for row in handoff_df.to_dict(orient="records")
    }


def final_lookup(final_df: pd.DataFrame) -> dict[str, dict[str, object]]:
    return {
        normalize_text(row["eval_scope"]): row
        for row in final_df.to_dict(orient="records")
    }


def freeze_lookup(freeze_df: pd.DataFrame) -> dict[str, dict[str, object]]:
    return {
        normalize_text(row["eval_scope"]): row
        for row in freeze_df.to_dict(orient="records")
    }


def scope_status_summary(handoff_by_scope: dict[str, dict[str, object]]) -> str:
    parts = [
        f"step1={normalize_text(handoff_by_scope['step1_taxonomy']['handoff_status_ko'])}",
        f"step2={normalize_text(handoff_by_scope['step2_onset_truth']['handoff_status_ko'])}",
        f"step3={normalize_text(handoff_by_scope['step3_precursor_performance']['handoff_status_ko'])}",
        f"step4_abrupt={normalize_text(handoff_by_scope['step4_abrupt_no_precursor']['handoff_status_ko'])}",
        f"step4_common={normalize_text(handoff_by_scope['step4_common_cause_routing']['handoff_status_ko'])}",
    ]
    return ", ".join(parts)


def supported_abrupt_family_counts(non_precursor_df: pd.DataFrame) -> dict[str, int]:
    df = non_precursor_df.copy()
    mask = df["eval_bucket_v2"].eq("abrupt_or_no_precursor_now")
    mask &= ~df["candidate_validity"].eq("false_positive")
    mask &= ~df["vendor_reply_class"].eq("vendor_rejected")
    subset = df.loc[mask, "vendor_fault_family"].map(normalize_text)
    counts = subset.value_counts().to_dict()
    return {str(key): int(value) for key, value in counts.items()}


def build_algorithm_role_map(frames: dict[str, pd.DataFrame], root: Path) -> pd.DataFrame:
    handoff_by_scope = handoff_lookup(frames["handoff_summary"])
    final_by_scope = final_lookup(frames["final_decision"])
    freeze_by_scope = freeze_lookup(frames["freeze_pack"])

    policy_row = frames["policy"].iloc[0].to_dict()
    workflow_name = normalize_text(policy_row["recommended_policy_name"])
    workflow_reason = normalize_text(policy_row["recommended_policy_reason_ko"])
    pipeline_row = frames["pipeline"].iloc[0].to_dict()
    pipeline_pass_flag = numeric_int(pipeline_row["final_pipeline_pass_flag"])

    abrupt_family_counts = supported_abrupt_family_counts(frames["non_precursor"])
    abrupt_family_text = ", ".join(
        f"{family}={count}" for family, count in sorted(abrupt_family_counts.items())
    ) or "stored abrupt family counts unavailable"

    main_refs = ", ".join(
        [
            FINAL_DECISION_PACK_NAME,
            CURRENT_FREEZE_PACK_NAME,
            HANDOFF_SUMMARY_NAME,
            PROJECT_EVAL_MATRIX_NAME,
            POLICY_RECOMMENDATION_NAME,
            PIPELINE_MANIFEST_NAME,
        ]
    )
    kernel_ref_text = refs_text(
        root,
        [
            "_share/panel_day_engine_kernellog_project_mapping_v1.csv",
            "_share/kernelog1_case/CASE_STUDY_KERNELOG1.md",
            "_share/kernelog1_case/RESULTS_2SIGMA_KERNELOG1_ONEPAGE.md",
            "docs/OPS_PANEL_DAY_ENGINE_INTERNAL_SHARE_APPENDIX_V1.md",
        ],
    )
    gpv_ref_text = refs_text(
        root,
        [
            "_share/panel_day_engine_gpv7_perf_summary_v1.csv",
            "data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv",
            "docs/OPS_GPVS_FAULT_FAMILY_F1.md",
            "docs/internal/PROGRAM_INVENTORY.md",
            "docs/RELEASE_MANIFEST.md",
        ],
    )

    step3_target = normalize_text(final_by_scope["step3_precursor_performance"]["current_best_target_name"])
    step4_abrupt_target = normalize_text(final_by_scope["step4_abrupt_no_precursor"]["current_best_target_name"])
    step4_common_target = normalize_text(final_by_scope["step4_common_cause_routing"]["current_best_target_name"])

    rows = [
        {
            "알고리즘명": "메인 알고리즘",
            "현재_역할_ko": "프로젝트의 1차 사건축이다. 전조형 고장 / 급작 고장 / 같이 흔들리는 이상 / 반복 이상 / 오경보를 먼저 가르고 onset·performance·operator workflow 기본축을 만든다.",
            "주출력_ko": "사건 성격 bucket, onset/performance 기준, operator workflow 기본 판단 축",
            "직접_판정하는것_ko": "전조형 고장 / 급작 고장 / 같이 흔들리는 이상 / 반복 이상 / 오경보와 그에 따른 현재 보고·운영 경계",
            "직접_판정못하는것_ko": "다이오드형 / 개방·장치이상형 / 모듈손상형 같은 정밀 물리 원인명 최종 확정",
            "현재_프로젝트내_위치_ko": f"최우선 판정축이자 현재 운영 workflow `{workflow_name}` 로 넘어가는 기본 사건 해석 축",
            "현재_신뢰수준_ko": "사건축 기본 골격은 현재 pack에서 고정됐지만, step3 전조형과 step4 common-cause는 아직 탐색적이고 step4 abrupt는 bounded current-data 수준이다.",
            "근거_ko": (
                f"scope status={scope_status_summary(handoff_by_scope)}; "
                f"step3 best={step3_target}; step4 abrupt best={step4_abrupt_target}; "
                f"step4 common best={step4_common_target}; workflow={workflow_name}; pipeline pass={pipeline_pass_flag}; refs={main_refs}"
            ),
        },
        {
            "알고리즘명": "커널로그 알고리즘",
            "현재_역할_ko": "증상명 / 원인군 이름 축이다. 출력 저하형 / 전압 변화형 / 패턴 이상형 / 불안정형 / 복합형을 붙이고, 저장 truth가 있는 abrupt positive에서는 다이오드형 / 개방·장치이상형 / 모듈손상형 같은 family-like naming도 제공한다.",
            "주출력_ko": "증상명, 원인군 이름, 사건 해석 보조 라벨",
            "직접_판정하는것_ko": "증상명 / 원인군 이름 축과 보조 symptom narrative",
            "직접_판정못하는것_ko": "메인 사건축 우선순위, 최종 field decision, operator workflow 기본 선택",
            "현재_프로젝트내_위치_ko": "메인 알고리즘 뒤에서 증상명과 원인군 이름을 붙이는 naming / interpretation layer",
            "현재_신뢰수준_ko": "보조 naming 축으로는 현재 충분히 쓸 수 있지만, main event-flow owner로 올릴 수준은 아니다.",
            "근거_ko": (
                f"kernel mapping refs={kernel_ref_text}; "
                f"stored abrupt family counts={abrupt_family_text}; "
                f"freeze boundary follows main event axis rather than kernel labels"
            ),
        },
        {
            "알고리즘명": "GPV 기반 알고리즘",
            "현재_역할_ko": "외부/reference 축이다. similar-type, benchmark, outside-data support를 제공하고 current project 판단을 바깥 데이터 축에서 비교해 보는 역할을 한다.",
            "주출력_ko": "외부 benchmark metric, by-type score summary, coarse fault-family reference",
            "직접_판정하는것_ko": "외부 benchmark 상의 상대적 구분력과 coarse family reference",
            "직접_판정못하는것_ko": "현재 현장 final decision, 메인 사건축 우선 판정, 운영 기본 workflow 결정",
            "현재_프로젝트내_위치_ko": "메인 알고리즘과 커널로그 알고리즘 뒤에 붙는 3차 외부 참고 축",
            "현재_신뢰수준_ko": "외부 benchmark/reference로는 유용하지만, 현재 프로젝트의 final field decision owner는 아니다.",
            "근거_ko": (
                f"gpv refs={gpv_ref_text}; "
                "current project uses GPV as external benchmark/support axis only and not as final operational decision owner"
            ),
        },
    ]
    return pd.DataFrame(rows, columns=ROLE_MAP_COLS)


def build_algorithm_gap_map(frames: dict[str, pd.DataFrame], root: Path) -> pd.DataFrame:
    policy_row = frames["policy"].iloc[0].to_dict()
    workflow_name = normalize_text(policy_row["recommended_policy_name"])
    policy_reason = normalize_text(policy_row["recommended_policy_reason_ko"])
    pipeline_pass_flag = numeric_int(frames["pipeline"].iloc[0]["final_pipeline_pass_flag"])
    final_by_scope = final_lookup(frames["final_decision"])

    rows = [
        {
            "gap_topic": "세 알고리즘 역할 고정",
            "현재_상태_ko": "메인=사건축, 커널로그=증상축, GPV=외부참고축으로 현재 pack에서 역할을 고정했다.",
            "해결여부": "해결",
            "아직_남은_한계_ko": "역할을 고정했다고 해서 step3/common-cause의 표본 한계가 사라지는 것은 아니다.",
            "현재_허용_판정범위_ko": "세 축을 섞지 않고 각 축의 책임 범위 안에서만 보고·handoff 할 수 있다.",
            "금지_overclaim_ko": "커널로그나 GPV를 메인 사건 판정 owner처럼 말하지 말 것.",
        },
        {
            "gap_topic": "세 알고리즘 우선순위 고정",
            "현재_상태_ko": f"현재 순서는 메인 알고리즘 -> 커널로그 알고리즘 -> GPV 기반 알고리즘으로 고정됐다. 운영 workflow는 `{workflow_name}` 와 pipeline pass={pipeline_pass_flag} 위에서 소비한다.",
            "해결여부": "해결",
            "아직_남은_한계_ko": "후순위 축이 앞선 축의 판정을 뒤집는 공식 rule은 아직 없다.",
            "현재_허용_판정범위_ko": "메인이 사건 성격을 먼저 정하고, 그 뒤에 naming과 외부 reference를 붙이는 순서로 사용한다.",
            "금지_overclaim_ko": "증상명이나 GPV score가 메인 사건축 결론을 자동 대체한다고 말하지 말 것.",
        },
        {
            "gap_topic": "커널로그 증상축 ↔ 프로젝트 사건축 매핑",
            "현재_상태_ko": "커널로그 증상축은 프로젝트 사건축의 보조 해석 매핑으로 고정됐다. confusion matrix가 아니라 interpretation table이다.",
            "해결여부": "해결",
            "아직_남은_한계_ko": "출력 저하형/전압 변화형/패턴 이상형이 사건축과 1:1 동치인 것은 아니다.",
            "현재_허용_판정범위_ko": "사건축이 정해진 뒤 그 사건을 설명하는 symptom narrative로 쓸 수 있다.",
            "금지_overclaim_ko": "커널로그 증상명 하나만으로 전조형/급작/같이 흔들리는 이상을 바로 확정했다고 말하지 말 것.",
        },
        {
            "gap_topic": "GPV 외부참고축 위치 고정",
            "현재_상태_ko": f"GPV는 external/reference axis로 위치를 고정했다. `{policy_reason}` 같은 운영 선택 근거와도 별개로, GPV는 외부 benchmark support만 담당한다.",
            "해결여부": "해결",
            "아직_남은_한계_ko": "외부 benchmark가 좋아도 현재 현장 배포 판정을 직접 보증하지는 않는다.",
            "현재_허용_판정범위_ko": "유사 유형 참고, coarse family reference, 외부 benchmark 비교 근거로만 쓸 수 있다.",
            "금지_overclaim_ko": "GPV 성능을 현재 프로젝트의 최종 field decision 성능이나 operator default 근거로 과장하지 말 것.",
        },
        {
            "gap_topic": "물리 원인명 확정 한계",
            "현재_상태_ko": "정밀 물리 원인명은 아직 제한적으로만 허용된다. stored truth가 있는 row에서는 family-like naming을 붙일 수 있지만, main algorithm 자체가 물리 원인명을 직접 최종 확정하는 구조는 아니다.",
            "해결여부": "부분해결",
            "아직_남은_한계_ko": "step3 precursor와 step4 common-cause는 현재 데이터 한계 때문에 stable root-cause generalization을 말하기 어렵다.",
            "현재_허용_판정범위_ko": "다이오드형 / 개방·장치이상형 / 모듈손상형 등 stored truth가 있는 범위의 family-like naming까지만 허용한다.",
            "금지_overclaim_ko": (
                "detector가 precise physical root-cause를 일반적으로 확정한다고 말하지 말 것. "
                f"특히 {normalize_text(final_by_scope['step3_precursor_performance']['final_usage_decision'])} / "
                f"{normalize_text(final_by_scope['step4_common_cause_routing']['final_usage_decision'])} scope를 stable root-cause classifier로 과장하지 말 것."
            ),
        },
    ]
    return pd.DataFrame(rows, columns=GAP_MAP_COLS)


def build_decision_flow_md(frames: dict[str, pd.DataFrame]) -> str:
    final_by_scope = final_lookup(frames["final_decision"])
    handoff_by_scope = handoff_lookup(frames["handoff_summary"])
    policy_row = frames["policy"].iloc[0].to_dict()
    workflow_name = normalize_text(policy_row["recommended_policy_name"])
    policy_expected_use = normalize_text(policy_row["expected_use_ko"])
    pipeline_pass_flag = numeric_int(frames["pipeline"].iloc[0]["final_pipeline_pass_flag"])

    lines = [
        "## 1. 지금 쓰는 3개 알고리즘의 역할",
        f"- 메인 알고리즘은 사건 성격을 가르는 기본축이다. 현재 프로젝트에서는 전조형 고장 / 급작 고장 / 같이 흔들리는 이상 / 반복 이상 / 오경보를 먼저 정한다.",
        "- 커널로그 알고리즘은 증상명과 원인군 이름을 붙이는 보조축이다. 사건 성격을 대신 정하는 축은 아니다.",
        "- GPV 기반 알고리즘은 외부 benchmark/reference 축이다. 현재 프로젝트의 최종 현장 판정을 직접 소유하지 않는다.",
        "",
        "## 2. 실제 판정 순서",
        "1. 메인 알고리즘이 사건 성격을 먼저 판정한다.",
        "2. 커널로그 알고리즘이 증상명/원인군 이름을 붙인다.",
        "3. GPV 기반 알고리즘은 외부 참고 축으로 사용한다.",
        f"- 현재 운영에서는 이 결과를 `{workflow_name}` workflow로 넘기고, pipeline pass={pipeline_pass_flag} 상태에서 사용한다.",
        f"- 즉, `{workflow_name}` 는 운영 workflow choice이고 detector generalization claim 자체는 아니다. ({policy_expected_use})",
        "",
        "## 3. 지금 가능한 판정 / 아직 못 하는 판정",
        f"- 지금 가능한 판정: step1/2는 구조적 coverage/reference로, step4 abrupt는 `{normalize_text(handoff_by_scope['step4_abrupt_no_precursor']['handoff_status_ko'])}` 으로, operator workflow는 `{normalize_text(handoff_by_scope['operator_policy_proxy']['handoff_status_ko'])}` 으로 쓸 수 있다.",
        f"- 아직 못 하는 판정: step3 precursor와 step4 common-cause를 stable default detector 성능이나 precise physical root-cause classifier로 확정하는 일은 아직 못 한다. 현재 status는 step3=`{normalize_text(final_by_scope['step3_precursor_performance']['final_usage_decision'])}`, step4 common=`{normalize_text(final_by_scope['step4_common_cause_routing']['final_usage_decision'])}` 이다.",
        "",
        "## 4. 과장하면 안 되는 것",
        "- 커널로그 증상명 하나만으로 메인 사건축 판정이 끝났다고 말하면 안 된다.",
        "- GPV benchmark 수치를 현재 현장 final decision 성능으로 바로 옮겨 말하면 안 된다.",
        "- 메인 알고리즘이 다이오드형 / 개방·장치이상형 / 모듈손상형 같은 물리 원인명을 일반적으로 직접 확정한다고 말하면 안 된다.",
        "- 운영 workflow 사용 가능 상태를 detector 일반 성능 freeze로 바꿔 말하면 안 된다.",
    ]
    return "\n".join(lines).strip() + "\n"


def write_csv(df: pd.DataFrame, path: Path, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"

    frames = load_inputs(root)
    validate_scope_coverage(frames)

    role_map_df = build_algorithm_role_map(frames, root)
    gap_map_df = build_algorithm_gap_map(frames, root)
    decision_flow_md = build_decision_flow_md(frames)

    write_csv(role_map_df, share_dir / ROLE_MAP_OUTPUT_NAME, ROLE_MAP_COLS)
    write_csv(gap_map_df, share_dir / GAP_MAP_OUTPUT_NAME, GAP_MAP_COLS)
    write_text(share_dir / DECISION_FLOW_OUTPUT_NAME, decision_flow_md)

    print(f"wrote {share_dir / ROLE_MAP_OUTPUT_NAME}")
    print(f"wrote {share_dir / GAP_MAP_OUTPUT_NAME}")
    print(f"wrote {share_dir / DECISION_FLOW_OUTPUT_NAME}")


if __name__ == "__main__":
    main()
