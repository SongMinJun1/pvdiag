#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

BRANCH_INVENTORY_OUTPUT_NAME = "panel_day_engine_branch_inventory_v1.csv"
METHOD_LAYER_STATUS_OUTPUT_NAME = "panel_day_engine_method_layer_status_v1.csv"
FAULT_TAXONOMY_OUTPUT_NAME = "panel_day_engine_fault_taxonomy_v1.csv"
FAULT_TAXONOMY_SUMMARY_OUTPUT_NAME = "panel_day_engine_fault_taxonomy_summary_v1.csv"

ELIGIBILITY_CASES_NAME = "panel_day_engine_local_precursor_eligibility_cases_v1.csv"
PRE_EWS_REPLAY_NAME = "panel_day_engine_local_pre_ews_replay_cases_v1.csv"
FATE_CASES_NAME = "panel_day_engine_local_seed_carry_fate_cases_v1.csv"
RUN_FEATURE_TABLE_NAME = "panel_day_engine_run_feature_table_v1.csv"
RUN_LABEL_PACK_NAME = "panel_day_engine_run_label_pack_v1.csv"

BRANCH_INVENTORY_COLS = [
    "file_path",
    "artifact_class",
    "layer_name",
    "purpose_ko",
    "source_of_truth_flag",
    "active_for_next_phase_flag",
    "note_ko",
]

METHOD_LAYER_STATUS_COLS = [
    "layer_name",
    "current_status",
    "why_ko",
    "immediate_need_ko",
    "next_action_ko",
]

FAULT_TAXONOMY_COLS = [
    "fault_family_id",
    "fault_family_name_ko",
    "family_group_ko",
    "precursor_capable_flag",
    "onset_labelable_flag",
    "recommended_eval_bucket",
    "evidence_source_files",
    "rationale_ko",
]

FAULT_TAXONOMY_SUMMARY_COLS = [
    "recommended_eval_bucket",
    "family_count",
    "precursor_capable_family_count",
    "onset_labelable_family_count",
]

ACTIVE_KEYWORDS = [
    "panel_day_engine.py",
    "local_precursor_eligibility",
    "local_seed_carry_fate",
    "run_feature_separability",
    "run_ranker_v0",
    "run_ranker_v1_holdout",
    "run_label_pack",
    "operator_run_consolidation",
    "operator_attention_delta",
    "operator_digest",
    "operator_baseline",
    "operator_refresh_v1",
    "operator_refresh_qa",
    "operator_pipeline",
    "branch_inventory_and_fault_taxonomy",
    "gpvs_fault_family_f1",
]

SOURCE_OF_TRUTH_KEYWORDS = [
    "panel_day_engine.py",
    "local_precursor_eligibility",
    "local_seed_carry_fate",
    "run_label_pack",
    "operator_run_consolidation",
    "operator_baseline",
    "operator_refresh_v1",
    "operator_refresh_qa",
    "operator_pipeline",
    "branch_inventory_and_fault_taxonomy",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory current panel_day_engine branch artifacts and define a coarse precursor-bearing fault taxonomy."
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


def read_csv_if_exists(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def contains_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def collect_relevant_files(root: Path) -> list[Path]:
    candidates: set[Path] = set()
    explicit_paths = [
        root / "pv_ae" / "panel_day_engine.py",
        root / "docs" / "OPS_GPVS_FAULT_FAMILY_F1.md",
        root / "research" / "prognostics" / "run_panel_day_site.py",
        root / "research" / "prognostics" / "evaluate_gpvs_fault_family_f1.py",
        root / "research" / "prognostics" / "smoke_test_evaluate_gpvs_fault_family_f1.py",
    ]
    for path in explicit_paths:
        if path.exists():
            candidates.add(path)

    for pattern in [
        "docs/OPS_PANEL_DAY_ENGINE_*.md",
        "docs/OPS_COMMON_CAUSE_PRECURSOR_*.md",
        "research/prognostics/build_panel_day_engine_*.py",
        "research/prognostics/smoke_test_panel_day_engine_*.py",
        "research/prognostics/build_common_cause_precursor_*.py",
        "research/prognostics/smoke_test_common_cause_precursor_*.py",
    ]:
        candidates.update(root.glob(pattern))

    return sorted(candidates, key=lambda path: path.as_posix())


def infer_layer_name(rel_path: str) -> str:
    name = rel_path.lower()
    if rel_path == "pv_ae/panel_day_engine.py":
        return "detector"
    if contains_any(name, ["operator_baseline", "operator_refresh_v1", "operator_pipeline", "run_panel_day_site"]):
        return "packaging"
    if contains_any(name, ["operator_refresh_qa", "gpvs_fault_family_f1", "local_precursor_cohort", "fault_taxonomy"]):
        return "evaluation"
    if contains_any(name, ["operator_"]):
        return "operator"
    if contains_any(name, ["run_ranker", "run_feature_separability"]):
        return "scorer"
    if contains_any(name, ["run_label_pack", "local_seed_carry_fate", "local_precursor_eligibility"]):
        return "label_truth"
    if contains_any(name, ["common_cause_precursor", "local_precursor_shadow", "local_precursor_threshold_replay", "local_precursor_decision_path", "local_precursor_miss"]):
        return "detector"
    return "evaluation"


def infer_artifact_class(rel_path: str, layer_name: str) -> str:
    if rel_path == "pv_ae/panel_day_engine.py":
        return "core"
    if rel_path.startswith("docs/"):
        return "documentation"
    if layer_name == "detector":
        return "detector_audit"
    if layer_name == "scorer":
        return "scorer_audit"
    if layer_name == "operator":
        return "operator_artifact"
    if layer_name == "label_truth":
        return "label_truth_audit"
    if layer_name == "packaging":
        return "packaging_orchestrator"
    return "evaluation_audit"


def infer_purpose_ko(rel_path: str) -> str:
    name = rel_path.lower()
    if rel_path == "pv_ae/panel_day_engine.py":
        return "panel_day_engine detector core 엔진"
    if "branch_inventory_and_fault_taxonomy" in name:
        return "branch inventory와 precursor-bearing fault taxonomy 정의"
    if "local_precursor_eligibility" in name:
        return "local fault temporality와 precursor eligibility 정의"
    if "local_seed_carry_fate" in name:
        return "run future linkage·recurring fate 분류"
    if "run_feature_separability" in name:
        return "run-level feature separability audit"
    if "run_ranker_v1_holdout" in name:
        return "learned run scorer holdout audit"
    if "run_ranker_v1_prototype" in name:
        return "learned run scorer optimistic prototype audit"
    if "run_ranker_v0" in name:
        return "hand-built run scorer v0 audit"
    if "run_label_pack" in name:
        return "next scorer용 run-level label pack 생성"
    if "local_precursor_cohort" in name:
        return "local precursor cohort fairness evaluation"
    if "local_precursor_shadow" in name:
        return "existing local precursor head shadow 관측"
    if "local_precursor_threshold_replay" in name:
        return "local precursor threshold/source replay audit"
    if "local_precursor_decision_path" in name:
        return "local precursor decision path reconstruction"
    if "local_precursor_miss" in name:
        return "local precursor miss case audit"
    if "common_cause_precursor_case_forensics" in name:
        return "common-cause precursor candidate case forensics"
    if "common_cause_precursor_decision_pack" in name:
        return "common-cause precursor addon decision pack"
    if "common_cause_precursor_audit" in name:
        return "common-cause precursor site/day audit"
    if "operator_run_consolidation" in name:
        return "operator run registry/queue/backlog/watchlist baseline 생성"
    if "operator_attention_delta" in name:
        return "attention snapshot delta 생성"
    if "operator_digest" in name:
        return "current attention + latest delta digest 생성"
    if "operator_score_hygiene" in name:
        return "operator ranking clipping/outlier sensitivity audit"
    if "operator_baseline" in name:
        return "operator baseline orchestration"
    if "operator_refresh_qa" in name:
        return "refresh 결과 coherence QA gate"
    if "operator_refresh_v1" in name:
        return "selected site rerun 후 baseline refresh"
    if "operator_pipeline" in name:
        return "refresh + QA end-to-end pipeline"
    if "run_panel_day_site" in name:
        return "site별 panel_day_engine 실행 wrapper"
    if "gpvs_fault_family_f1" in name:
        return "fault family coarse evaluation/taxonomy grounding"
    if rel_path.startswith("docs/"):
        return "현재 branch artifact 해석/운영 문서"
    return "관련 audit/packaging 참고 파일"


def infer_source_of_truth_flag(rel_path: str) -> int:
    if rel_path.startswith("docs/") or "/smoke_test_" in rel_path:
        return 0
    return int(contains_any(rel_path.lower(), [needle.lower() for needle in SOURCE_OF_TRUTH_KEYWORDS]))


def infer_active_for_next_phase_flag(rel_path: str) -> int:
    if "/smoke_test_" in rel_path:
        return 0
    return int(contains_any(rel_path.lower(), [needle.lower() for needle in ACTIVE_KEYWORDS]))


def infer_note_ko(rel_path: str, source_of_truth_flag: int, active_for_next_phase_flag: int) -> str:
    if "/smoke_test_" in rel_path:
        return "smoke/regression guard"
    if rel_path.startswith("docs/"):
        return "설계·해석 문서"
    if source_of_truth_flag == 1:
        return "현재 branch 기준 정의/재생성 기준"
    if active_for_next_phase_flag == 1:
        return "다음 단계 reference로 유지"
    return "historical exploratory 참고물"


def build_branch_inventory(root: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for path in collect_relevant_files(root):
        rel_path = path.relative_to(root).as_posix()
        layer_name = infer_layer_name(rel_path)
        source_of_truth_flag = infer_source_of_truth_flag(rel_path)
        active_for_next_phase_flag = infer_active_for_next_phase_flag(rel_path)
        rows.append(
            {
                "file_path": rel_path,
                "artifact_class": infer_artifact_class(rel_path, layer_name),
                "layer_name": layer_name,
                "purpose_ko": infer_purpose_ko(rel_path),
                "source_of_truth_flag": source_of_truth_flag,
                "active_for_next_phase_flag": active_for_next_phase_flag,
                "note_ko": infer_note_ko(rel_path, source_of_truth_flag, active_for_next_phase_flag),
            }
        )
    return pd.DataFrame(rows).reindex(columns=BRANCH_INVENTORY_COLS)


def build_method_layer_status() -> pd.DataFrame:
    rows = [
        {
            "layer_name": "detector",
            "current_status": "paused",
            "why_ko": "day-level gate tweaking은 이미 여러 replay/shadow audit를 거쳐 수익이 줄었고 core detector를 SSOT로 고정할 시점이다.",
            "immediate_need_ko": "새 detector patch보다 현재 detector inventory와 fault taxonomy 정리가 우선이다.",
            "next_action_ko": "current detector를 baseline으로 두고 precursor onset/성능 평가를 분리한다.",
        },
        {
            "layer_name": "scorer",
            "current_status": "exploratory",
            "why_ko": "v1 prototype은 optimistic했고 holdout에서는 v0 reference 우위를 못 넘었으며 label scarcity가 병목으로 남아 있다.",
            "immediate_need_ko": "label pack과 fault bucket 정의로 v2 scorer target을 명확히 해야 한다.",
            "next_action_ko": "run_label_pack 기반으로 run_ranker_v2 holdout 설계를 다시 잡는다.",
        },
        {
            "layer_name": "operator",
            "current_status": "stable_baseline",
            "why_ko": "run consolidation, attention, delta, digest까지 operator-facing baseline이 정리되었다.",
            "immediate_need_ko": "현재 baseline을 유지하면서 attention 규모와 burden만 모니터링하면 된다.",
            "next_action_ko": "operator baseline을 refresh/pipeline entrypoint로 고정해 운영 레이어를 안정화한다.",
        },
        {
            "layer_name": "label_truth",
            "current_status": "active",
            "why_ko": "eligibility, fate, run label pack이 모여 next scorer truth expansion의 핵심 레이어가 되었다.",
            "immediate_need_ko": "precursor-bearing vs abrupt/no-precursor taxonomy를 truth 레이어에 연결해야 한다.",
            "next_action_ko": "fault taxonomy와 onset labeling policy를 고정해 usable labels를 늘린다.",
        },
        {
            "layer_name": "evaluation",
            "current_status": "needs_definition",
            "why_ko": "fault family/temporality에 따라 precursor performance와 non-precursor detection performance를 분리해야 한다.",
            "immediate_need_ko": "recommended_eval_bucket 기준을 먼저 정의해야 한다.",
            "next_action_ko": "precursor onset labeling, precursor performance, non-precursor classification 성능을 분리 평가한다.",
        },
        {
            "layer_name": "packaging",
            "current_status": "stable_baseline",
            "why_ko": "baseline, refresh, QA, pipeline orchestrator가 end-to-end operational entrypoint를 이미 제공한다.",
            "immediate_need_ko": "실행 순서보다 각 레이어 meaning과 QA gate 해석을 고정하는 것이 중요하다.",
            "next_action_ko": "refresh -> QA -> pipeline manifest를 표준 운영 경로로 사용한다.",
        },
    ]
    return pd.DataFrame(rows).reindex(columns=METHOD_LAYER_STATUS_COLS)


def load_grounding_tables(root: Path) -> dict[str, pd.DataFrame]:
    share_dir = root / "_share"
    tables: dict[str, pd.DataFrame] = {}
    for name in [
        ELIGIBILITY_CASES_NAME,
        PRE_EWS_REPLAY_NAME,
        FATE_CASES_NAME,
        RUN_FEATURE_TABLE_NAME,
        RUN_LABEL_PACK_NAME,
    ]:
        df = read_csv_if_exists(share_dir / name)
        if df is not None:
            tables[name] = df
    return tables


def count_mask(df: pd.DataFrame | None, mask: pd.Series | None) -> int:
    if df is None or mask is None:
        return 0
    return int(mask.fillna(False).sum())


def build_fault_taxonomy(root: Path) -> pd.DataFrame:
    tables = load_grounding_tables(root)
    eligibility = tables.get(ELIGIBILITY_CASES_NAME)
    replay = tables.get(PRE_EWS_REPLAY_NAME)
    fate = tables.get(FATE_CASES_NAME)
    label_pack = tables.get(RUN_LABEL_PACK_NAME)

    progressive_electrical_count = 0
    abrupt_electrical_count = 0
    unknown_electrical_count = 0
    group_like_count = 0
    none_visible_count = 0
    monitor_like_count = 0
    isolated_like_count = 0

    if eligibility is not None:
        vendor = eligibility.get("vendor_fault_family", pd.Series("", index=eligibility.index)).map(normalize_text)
        temporality = eligibility.get("temporality_class", pd.Series("", index=eligibility.index)).map(normalize_text)
        electrical_mask = vendor.isin({"diode_like", "module_damage_like"})
        progressive_electrical_count = count_mask(
            eligibility, electrical_mask & temporality.eq("progressive_local_precursor_expected")
        )
        abrupt_electrical_count = count_mask(
            eligibility, electrical_mask & temporality.eq("abrupt_local_precursor_unexpected")
        )
        unknown_electrical_count = count_mask(
            eligibility, electrical_mask & temporality.eq("unknown_local_temporality")
        )

    if replay is not None and "vendor_fault_family" in replay.columns:
        vendor = replay["vendor_fault_family"].map(normalize_text)
        group_like_count = int(vendor.eq("group_or_inverter_side_like").sum())
        none_visible_count = int(vendor.eq("none_visible").sum())

    if fate is not None and "fate_class" in fate.columns:
        fate_class = fate["fate_class"].map(normalize_text)
        monitor_like_count = int(fate_class.eq("recurring_chronic_monitor_like").sum())
        isolated_like_count = int(fate_class.eq("isolated_unexplained").sum())
    elif label_pack is not None:
        label_bucket = label_pack.get("label_bucket", pd.Series("", index=label_pack.index)).map(normalize_text)
        fate_class = label_pack.get("fate_class", pd.Series("", index=label_pack.index)).map(normalize_text)
        monitor_like_count = int(label_bucket.eq("monitor_like").sum() + fate_class.eq("recurring_chronic_monitor_like").sum())
        isolated_like_count = int(label_bucket.eq("nuisance_like").sum() + fate_class.eq("isolated_unexplained").sum())

    rows = [
        {
            "fault_family_id": "electrical_fault_like_progressive_local",
            "fault_family_name_ko": "개별 패널 전기/모듈 열화형-점진 전조형",
            "family_group_ko": "개별 패널 전기/모듈 손상형",
            "precursor_capable_flag": 1,
            "onset_labelable_flag": 1,
            "recommended_eval_bucket": "precursor_bearing",
            "evidence_source_files": ",".join(
                [
                    ELIGIBILITY_CASES_NAME,
                    PRE_EWS_REPLAY_NAME,
                    "docs/OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_ELIGIBILITY_AUDIT_V1.md",
                    "docs/OPS_GPVS_FAULT_FAMILY_F1.md",
                ]
            ),
            "rationale_ko": f"eligibility audit에서 diode_like/module_damage_like progressive case {progressive_electrical_count}건이 확인되어 precursor-bearing으로 다루는 것이 합리적이다.",
        },
        {
            "fault_family_id": "electrical_fault_like_abrupt_local",
            "fault_family_name_ko": "개별 패널 전기/모듈 열화형-급작 발현형",
            "family_group_ko": "개별 패널 전기/모듈 손상형",
            "precursor_capable_flag": 0,
            "onset_labelable_flag": 1,
            "recommended_eval_bucket": "abrupt_or_no_precursor",
            "evidence_source_files": ",".join(
                [
                    ELIGIBILITY_CASES_NAME,
                    "docs/OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_ELIGIBILITY_AUDIT_V1.md",
                ]
            ),
            "rationale_ko": f"같은 electrical family 안에서도 abrupt_local_precursor_unexpected case {abrupt_electrical_count}건이 관측되어 precursor recall 분모에서 분리해야 한다.",
        },
        {
            "fault_family_id": "electrical_fault_like_unknown_local_temporality",
            "fault_family_name_ko": "개별 패널 전기/모듈 열화형-온셋 미정형",
            "family_group_ko": "개별 패널 전기/모듈 손상형",
            "precursor_capable_flag": 0,
            "onset_labelable_flag": 1,
            "recommended_eval_bucket": "unknown_needs_review",
            "evidence_source_files": ",".join(
                [
                    ELIGIBILITY_CASES_NAME,
                    "docs/OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_ELIGIBILITY_AUDIT_V1.md",
                ]
            ),
            "rationale_ko": f"unknown_local_temporality case {unknown_electrical_count}건이 남아 있어 onset review 없이 precursor 성능에 바로 포함하면 해석이 흔들린다.",
        },
        {
            "fault_family_id": "group_or_inverter_side_like",
            "fault_family_name_ko": "그룹/인버터/상위설비 공통원인형",
            "family_group_ko": "상위설비·그룹 공통원인형",
            "precursor_capable_flag": 1,
            "onset_labelable_flag": 0,
            "recommended_eval_bucket": "unknown_needs_review",
            "evidence_source_files": ",".join(
                [
                    PRE_EWS_REPLAY_NAME,
                    "docs/OPS_COMMON_CAUSE_PRECURSOR_AUDIT_V1.md",
                    "docs/OPS_GPVS_FAULT_FAMILY_F1.md",
                ]
            ),
            "rationale_ko": f"group_or_inverter_side_like evidence {group_like_count}건이 replay/common-cause 쪽에는 있지만 panel-level onset 정의는 아직 안정되지 않아 별도 review bucket이 적절하다.",
        },
        {
            "fault_family_id": "none_visible_or_unconfirmed",
            "fault_family_name_ko": "가시 fault 없음/불확정형",
            "family_group_ko": "비가시·비확정 truth형",
            "precursor_capable_flag": 0,
            "onset_labelable_flag": 0,
            "recommended_eval_bucket": "abrupt_or_no_precursor",
            "evidence_source_files": ",".join(
                [
                    PRE_EWS_REPLAY_NAME,
                    "docs/OPS_GPVS_FAULT_FAMILY_F1.md",
                ]
            ),
            "rationale_ko": f"none_visible evidence {none_visible_count}건은 fault onset 자체가 약해 precursor 평가보다 non-precursor/none-visible bucket으로 다루는 편이 안전하다.",
        },
        {
            "fault_family_id": "recurring_chronic_monitor_like",
            "fault_family_name_ko": "반복 chronic monitor 패턴",
            "family_group_ko": "run fate/monitor 패턴",
            "precursor_capable_flag": 0,
            "onset_labelable_flag": 0,
            "recommended_eval_bucket": "unknown_needs_review",
            "evidence_source_files": ",".join(
                [
                    FATE_CASES_NAME,
                    RUN_LABEL_PACK_NAME,
                    "docs/OPS_PANEL_DAY_ENGINE_RUN_LABEL_PACK_V1.md",
                ]
            ),
            "rationale_ko": f"recurring_chronic_monitor_like {monitor_like_count}건은 operator/scorer context에는 중요하지만 direct fault onset label로는 쓰기 어려워 별도 review bucket이 필요하다.",
        },
        {
            "fault_family_id": "isolated_unexplained",
            "fault_family_name_ko": "고립 unexplained burden 패턴",
            "family_group_ko": "run fate/negative-like 패턴",
            "precursor_capable_flag": 0,
            "onset_labelable_flag": 0,
            "recommended_eval_bucket": "unknown_needs_review",
            "evidence_source_files": ",".join(
                [
                    FATE_CASES_NAME,
                    RUN_LABEL_PACK_NAME,
                ]
            ),
            "rationale_ko": f"isolated_unexplained {isolated_like_count}건은 nuisance-like negative evidence로는 유용하지만 fault family onset truth로는 아직 정의가 약하다.",
        },
    ]
    return pd.DataFrame(rows).reindex(columns=FAULT_TAXONOMY_COLS)


def build_fault_taxonomy_summary(taxonomy_df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        taxonomy_df.groupby("recommended_eval_bucket", dropna=False, sort=True)
        .agg(
            family_count=("fault_family_id", "count"),
            precursor_capable_family_count=("precursor_capable_flag", lambda s: int(pd.to_numeric(s, errors="coerce").fillna(0).astype(int).sum())),
            onset_labelable_family_count=("onset_labelable_flag", lambda s: int(pd.to_numeric(s, errors="coerce").fillna(0).astype(int).sum())),
        )
        .reset_index()
    )
    return grouped.reindex(columns=FAULT_TAXONOMY_SUMMARY_COLS)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    branch_inventory = build_branch_inventory(root)
    method_layer_status = build_method_layer_status()
    fault_taxonomy = build_fault_taxonomy(root)
    fault_taxonomy_summary = build_fault_taxonomy_summary(fault_taxonomy)

    branch_inventory.to_csv(share_dir / BRANCH_INVENTORY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    method_layer_status.to_csv(share_dir / METHOD_LAYER_STATUS_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    fault_taxonomy.to_csv(share_dir / FAULT_TAXONOMY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    fault_taxonomy_summary.to_csv(share_dir / FAULT_TAXONOMY_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
