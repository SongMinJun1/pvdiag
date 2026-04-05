#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

FAULT_TAXONOMY_NAME = "panel_day_engine_fault_taxonomy_v1.csv"
BRANCH_INVENTORY_NAME = "panel_day_engine_branch_inventory_v1.csv"
METHOD_LAYER_STATUS_NAME = "panel_day_engine_method_layer_status_v1.csv"
PRECURSOR_ONSET_TRUTH_NAME = "panel_day_engine_precursor_onset_truth_v1.csv"

LITERATURE_CROSSWALK_OUTPUT_NAME = "panel_day_engine_fault_taxonomy_literature_crosswalk_v1.csv"
EVAL_BUCKETS_OUTPUT_NAME = "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv"
EVAL_BUCKETS_SUMMARY_OUTPUT_NAME = "panel_day_engine_fault_taxonomy_eval_buckets_summary_v2.csv"

ALLOWED_MODALITIES = {
    "daily_electrical_pipeline",
    "thermal_or_ir",
    "el_or_visual_inspection",
    "inverter_or_system_level",
    "mixed_or_unclear",
}

ALLOWED_EVAL_BUCKETS = [
    "precursor_bearing_detectable_now",
    "precursor_capable_but_not_detectable_now",
    "abrupt_or_no_precursor_now",
    "non_panel_or_common_cause",
    "unknown_needs_review",
]

REQUIRED_TAXONOMY_COLS = [
    "fault_family_id",
    "fault_family_name_ko",
    "family_group_ko",
    "precursor_capable_flag",
    "onset_labelable_flag",
    "recommended_eval_bucket",
    "evidence_source_files",
    "rationale_ko",
]

REQUIRED_INVENTORY_COLS = [
    "file_path",
    "artifact_class",
    "layer_name",
    "purpose_ko",
    "source_of_truth_flag",
    "active_for_next_phase_flag",
    "note_ko",
]

REQUIRED_LAYER_STATUS_COLS = [
    "layer_name",
    "current_status",
    "why_ko",
    "immediate_need_ko",
    "next_action_ko",
]

REQUIRED_ONSET_TRUTH_COLS = [
    "site",
    "panel_id",
    "vendor_fault_family",
    "preferred_onset_stage",
    "preferred_onset_confidence",
]

CROSSWALK_OUTPUT_COLS = [
    *REQUIRED_TAXONOMY_COLS,
    "literature_precursor_capable_flag",
    "current_pipeline_detectable_flag",
    "preferred_sensor_modality",
    "eval_bucket_v2",
    "eval_bucket_reason_ko",
    "literature_rationale_ko",
]

EVAL_BUCKETS_OUTPUT_COLS = [
    "fault_family_id",
    "fault_family_name_ko",
    "family_group_ko",
    "literature_precursor_capable_flag",
    "current_pipeline_detectable_flag",
    "preferred_sensor_modality",
    "eval_bucket_v2",
    "eval_bucket_reason_ko",
]

SUMMARY_OUTPUT_COLS = [
    "eval_bucket_v2",
    "family_count",
    "literature_precursor_capable_family_count",
    "current_pipeline_detectable_family_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crosswalk branch-grounded fault taxonomy with PV fault literature and define evaluation buckets for step 3/4."
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


def to_int_flag(value: object) -> int:
    text = normalize_text(value).lower()
    if text in {"", "0", "0.0", "false", "f", "n", "no"}:
        return 0
    if text in {"1", "1.0", "true", "t", "y", "yes"}:
        return 1
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return int(bool(numeric)) if not pd.isna(numeric) else 0


def load_inputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    taxonomy = read_csv(root / "_share" / FAULT_TAXONOMY_NAME)
    ensure_columns(taxonomy, REQUIRED_TAXONOMY_COLS, FAULT_TAXONOMY_NAME)
    taxonomy["fault_family_id"] = taxonomy["fault_family_id"].map(normalize_text)

    inventory = read_csv(root / "_share" / BRANCH_INVENTORY_NAME)
    ensure_columns(inventory, REQUIRED_INVENTORY_COLS, BRANCH_INVENTORY_NAME)
    inventory["file_path"] = inventory["file_path"].map(normalize_text)
    inventory["layer_name"] = inventory["layer_name"].map(normalize_text)

    layer_status = read_csv(root / "_share" / METHOD_LAYER_STATUS_NAME)
    ensure_columns(layer_status, REQUIRED_LAYER_STATUS_COLS, METHOD_LAYER_STATUS_NAME)
    layer_status["layer_name"] = layer_status["layer_name"].map(normalize_text)
    layer_status["current_status"] = layer_status["current_status"].map(normalize_text)

    onset_truth = read_csv(root / "_share" / PRECURSOR_ONSET_TRUTH_NAME)
    ensure_columns(onset_truth, REQUIRED_ONSET_TRUTH_COLS, PRECURSOR_ONSET_TRUTH_NAME)
    onset_truth["vendor_fault_family"] = onset_truth["vendor_fault_family"].map(normalize_text)
    onset_truth["preferred_onset_stage"] = onset_truth["preferred_onset_stage"].map(normalize_text)
    onset_truth["preferred_onset_confidence"] = onset_truth["preferred_onset_confidence"].map(normalize_text)

    return taxonomy, inventory, layer_status, onset_truth


def build_branch_context(inventory: pd.DataFrame, layer_status: pd.DataFrame, onset_truth: pd.DataFrame) -> dict[str, object]:
    inventory_paths = set(inventory["file_path"].astype(str))
    layer_status_map = {
        normalize_text(row["layer_name"]): normalize_text(row["current_status"])
        for row in layer_status.to_dict(orient="records")
    }
    electrical_onset_case_count = int(
        onset_truth["vendor_fault_family"].isin(["diode_like", "module_damage_like"]).sum()
    )
    strong_or_medium_onset_case_count = int(
        onset_truth["preferred_onset_confidence"].isin(["strong", "medium"]).sum()
    )
    common_cause_artifact_count = int(
        inventory["file_path"].astype(str).str.contains("common_cause_precursor", case=False, regex=False).sum()
    )
    return {
        "has_detector_core": "pv_ae/panel_day_engine.py" in inventory_paths,
        "has_eligibility_doc": any("LOCAL_PRECURSOR_ELIGIBILITY" in path for path in inventory_paths),
        "has_fault_family_doc": "docs/OPS_GPVS_FAULT_FAMILY_F1.md" in inventory_paths,
        "detector_status": layer_status_map.get("detector", ""),
        "evaluation_status": layer_status_map.get("evaluation", ""),
        "electrical_onset_case_count": electrical_onset_case_count,
        "strong_or_medium_onset_case_count": strong_or_medium_onset_case_count,
        "common_cause_artifact_count": common_cause_artifact_count,
    }


def build_rule_table(context: dict[str, object]) -> dict[str, dict[str, object]]:
    electrical_case_count = int(context["electrical_onset_case_count"])
    strong_or_medium_case_count = int(context["strong_or_medium_onset_case_count"])
    common_cause_artifact_count = int(context["common_cause_artifact_count"])
    detector_ready = context["has_detector_core"] and context["detector_status"] in {"paused", "active"}

    return {
        "electrical_fault_like_progressive_local": {
            "literature_precursor_capable_flag": 1,
            "current_pipeline_detectable_flag": int(detector_ready),
            "preferred_sensor_modality": "daily_electrical_pipeline",
            "eval_bucket_v2": "precursor_bearing_detectable_now",
            "eval_bucket_reason_ko": (
                f"현재 branch에서 diode/module damage precursor onset truth {electrical_case_count}건이 있고 "
                f"그중 strong/medium onset {strong_or_medium_case_count}건이 daily electrical helper로 재구성되어 "
                "step 3 precursor-bearing 분모로 바로 사용할 수 있다."
            ),
            "literature_rationale_ko": (
                "PV module fault literature는 hotspot, cracked cell, delamination, corrosion, bypass-related electrical shifts를 "
                "전압·전류·I-V 기반 electrical characterisation으로 자주 탐지하며, 점진 열화형은 precursor-capable로 해석하는 것이 타당하다."
            ),
        },
        "electrical_fault_like_abrupt_local": {
            "literature_precursor_capable_flag": 0,
            "current_pipeline_detectable_flag": int(detector_ready),
            "preferred_sensor_modality": "daily_electrical_pipeline",
            "eval_bucket_v2": "abrupt_or_no_precursor_now",
            "eval_bucket_reason_ko": (
                "같은 electrical family라도 branch evidence에서는 fault 직전 급락형으로 분리되므로 "
                "precursor-bearing recall 분모에는 넣지 않고 step 4 abrupt/no-precursor 성능으로 분리한다."
            ),
            "literature_rationale_ko": (
                "모듈 electrical failure는 electrical monitoring으로 포착 가능하지만, row 자체가 abrupt onset bucket이므로 "
                "이 하위 bucket은 literature-grounded precursor family라기보다 non-precursor evaluation 대상으로 다루는 편이 맞다."
            ),
        },
        "electrical_fault_like_unknown_local_temporality": {
            "literature_precursor_capable_flag": 1,
            "current_pipeline_detectable_flag": int(detector_ready),
            "preferred_sensor_modality": "daily_electrical_pipeline",
            "eval_bucket_v2": "unknown_needs_review",
            "eval_bucket_reason_ko": (
                "literature상 electrical/module damage 계열은 precursor-capable 후보지만, 현재 branch에서는 onset temporality를 "
                "아직 안정적으로 못 나눴으므로 step 3 직행 대신 review bucket에 남긴다."
            ),
            "literature_rationale_ko": (
                "review literature는 electrical characterisation이 hotspot, degradation, cracked-cell and delamination effects를 "
                "잡는다고 보지만, 이 row는 branch temporality evidence가 아직 unknown이어서 literature만으로 분모를 확정하기 어렵다."
            ),
        },
        "group_or_inverter_side_like": {
            "literature_precursor_capable_flag": 1,
            "current_pipeline_detectable_flag": 0,
            "preferred_sensor_modality": "inverter_or_system_level",
            "eval_bucket_v2": "non_panel_or_common_cause",
            "eval_bucket_reason_ko": (
                f"branch inventory에 common-cause precursor 관련 artifact가 {common_cause_artifact_count}개 존재하지만 "
                "이 family는 panel-local precursor 분모가 아니라 system/common-cause 평가로 분리하는 것이 맞다."
            ),
            "literature_rationale_ko": (
                "PV inverter/system fault literature는 open-switch, diode, capacitor, sensor fault 같은 precursor-like signatures를 "
                "다루지만 이는 inverter or system-level modality의 문제이며 panel_day_engine daily local electrical head가 직접 책임질 분모는 아니다."
            ),
        },
        "none_visible_or_unconfirmed": {
            "literature_precursor_capable_flag": 0,
            "current_pipeline_detectable_flag": 0,
            "preferred_sensor_modality": "mixed_or_unclear",
            "eval_bucket_v2": "abrupt_or_no_precursor_now",
            "eval_bucket_reason_ko": (
                "현재 branch와 literature 모두 이 row를 특정 precursor-bearing physical family로 고정하지 못하므로 "
                "step 3 precursor-bearing 분모에서는 빼고 step 4 비전조/불확정 해석으로 분리한다."
            ),
            "literature_rationale_ko": (
                "visual/EL/IR literature는 cracks, corrosion, delamination, hotspot처럼 명시적 defect class를 전제로 한다. "
                "none_visible_or_unconfirmed는 그런 문헌형 fault family와 직접 대응되지 않아 precursor-capable family로 보지 않는다."
            ),
        },
        "recurring_chronic_monitor_like": {
            "literature_precursor_capable_flag": 0,
            "current_pipeline_detectable_flag": 0,
            "preferred_sensor_modality": "mixed_or_unclear",
            "eval_bucket_v2": "unknown_needs_review",
            "eval_bucket_reason_ko": (
                "현재 branch에서 operator/scorer context로는 중요하지만 confirmed fault family가 아니므로 "
                "step 3 precursor-bearing detectable-now 성능에서 제외하고 별도 monitor burden review로 남긴다."
            ),
            "literature_rationale_ko": (
                "literature는 hotspot, crack, delamination, inverter fault 같은 물리 fault class를 다루며 recurring chronic monitor pattern 자체를 "
                "fault family로 정의하지 않는다. 따라서 precursor-bearing family로 직접 승격하기 어렵다."
            ),
        },
        "isolated_unexplained": {
            "literature_precursor_capable_flag": 0,
            "current_pipeline_detectable_flag": 0,
            "preferred_sensor_modality": "mixed_or_unclear",
            "eval_bucket_v2": "unknown_needs_review",
            "eval_bucket_reason_ko": (
                "negative-like burden pattern으로는 유용하지만 확인된 physical fault family가 아니어서 "
                "step 3/4 fault-family evaluation bucket보다는 truth review 대상에 가깝다."
            ),
            "literature_rationale_ko": (
                "isolated unexplained burden은 branch operational pattern이지 PV literature의 명시적 fault family가 아니다. "
                "따라서 precursor-capable 여부를 문헌으로 직접 정당화하기 어렵다."
            ),
        },
    }


def build_crosswalk(
    taxonomy: pd.DataFrame,
    inventory: pd.DataFrame,
    layer_status: pd.DataFrame,
    onset_truth: pd.DataFrame,
) -> pd.DataFrame:
    context = build_branch_context(inventory, layer_status, onset_truth)
    rule_table = build_rule_table(context)

    rows: list[dict[str, object]] = []
    for row in taxonomy.to_dict(orient="records"):
        fault_family_id = normalize_text(row["fault_family_id"])
        if fault_family_id not in rule_table:
            raise SystemExit(f"missing literature crosswalk rule for fault_family_id={fault_family_id}")
        rule = rule_table[fault_family_id]
        preferred_sensor_modality = normalize_text(rule["preferred_sensor_modality"])
        eval_bucket_v2 = normalize_text(rule["eval_bucket_v2"])
        if preferred_sensor_modality not in ALLOWED_MODALITIES:
            raise SystemExit(f"invalid preferred_sensor_modality for {fault_family_id}: {preferred_sensor_modality}")
        if eval_bucket_v2 not in ALLOWED_EVAL_BUCKETS:
            raise SystemExit(f"invalid eval_bucket_v2 for {fault_family_id}: {eval_bucket_v2}")

        merged = dict(row)
        merged.update(
            {
                "literature_precursor_capable_flag": int(rule["literature_precursor_capable_flag"]),
                "current_pipeline_detectable_flag": int(rule["current_pipeline_detectable_flag"]),
                "preferred_sensor_modality": preferred_sensor_modality,
                "eval_bucket_v2": eval_bucket_v2,
                "eval_bucket_reason_ko": normalize_text(rule["eval_bucket_reason_ko"]),
                "literature_rationale_ko": normalize_text(rule["literature_rationale_ko"]),
            }
        )
        rows.append(merged)

    return pd.DataFrame(rows).reindex(columns=CROSSWALK_OUTPUT_COLS)


def build_eval_buckets_v2(crosswalk_df: pd.DataFrame) -> pd.DataFrame:
    return crosswalk_df.loc[:, EVAL_BUCKETS_OUTPUT_COLS].copy()


def build_eval_bucket_summary(eval_buckets_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for bucket in ALLOWED_EVAL_BUCKETS:
        bucket_df = eval_buckets_df.loc[eval_buckets_df["eval_bucket_v2"].eq(bucket)].copy()
        rows.append(
            {
                "eval_bucket_v2": bucket,
                "family_count": int(len(bucket_df)),
                "literature_precursor_capable_family_count": int(bucket_df["literature_precursor_capable_flag"].map(to_int_flag).sum()),
                "current_pipeline_detectable_family_count": int(bucket_df["current_pipeline_detectable_flag"].map(to_int_flag).sum()),
            }
        )
    return pd.DataFrame(rows).reindex(columns=SUMMARY_OUTPUT_COLS)


def write_outputs(root: Path, crosswalk_df: pd.DataFrame, eval_buckets_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    crosswalk_df.to_csv(share_dir / LITERATURE_CROSSWALK_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    eval_buckets_df.to_csv(share_dir / EVAL_BUCKETS_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / EVAL_BUCKETS_SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    taxonomy, inventory, layer_status, onset_truth = load_inputs(root)
    crosswalk_df = build_crosswalk(taxonomy, inventory, layer_status, onset_truth)
    eval_buckets_df = build_eval_buckets_v2(crosswalk_df)
    summary_df = build_eval_bucket_summary(eval_buckets_df)
    write_outputs(root, crosswalk_df, eval_buckets_df, summary_df)


if __name__ == "__main__":
    main()
