#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
import sys

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


GPVS_WINDOW_SCORES_NAME = "gpvs_window_scores.csv"
GPVS_BYTYPE_METRICS_NAME = "EXTERNAL_GPVS_BYTYPE_METRICS.csv"
EXTERNAL_EVAL_SCRIPT_NAME = "external_eval_gpvs.py"
TRAIN_SCRIPT_NAME = "gpvs_train_supervised.py"
GPVS_FINAL_SUMMARY_NAME = "gpvs_final_summary.md"

CURRENT_AUDIT_NAME = "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv"
CURRENT_AUDIT_SUMMARY_NAME = "panel_day_engine_gpvs_detailed_type_inference_summary_v1.csv"
CURRENT_AUDIT_CV_NAME = "panel_day_engine_gpvs_detailed_type_cv_summary_v1.csv"

OUTPUT_INVENTORY_NAME = "panel_day_engine_gpvs_bytype_provenance_inventory_v1.csv"
OUTPUT_SUMMARY_NAME = "panel_day_engine_gpvs_bytype_provenance_summary_v1.csv"
OUTPUT_NOTE_NAME = "panel_day_engine_gpvs_bytype_provenance_note_v1.md"

SEARCH_ROOTS = [
    "data/gpvs",
    "research/prognostics",
    "docs",
]

SERIALIZED_PATTERNS = ["*.joblib", "*.pkl", "*.pickle", "*.json"]

INVENTORY_COLS = [
    "path",
    "artifact_kind",
    "exists_flag",
    "fault_type",
    "train_window_count",
    "unique_source_count",
    "unique_scenario_count",
    "notes_ko",
]

SUMMARY_COLS = [
    "provenance_status",
    "serialized_model_found_flag",
    "feature_manifest_found_flag",
    "training_script_found_flag",
    "evaluation_script_found_flag",
    "external_eval_loads_serialized_model_flag",
    "external_eval_trains_model_flag",
    "external_eval_precomputed_scores_only_flag",
    "real_fault_panel_count",
    "fallback_top1_collapse_flag",
    "grouped_cv_degenerate_flag",
    "unique_source_count_per_fault_type_is_one_flag",
    "current_fallback_lr_attachable_flag",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit GPVS by-type provenance and determine whether an original trained head exists."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root. Defaults to project root.",
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


def read_optional_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def relative_str(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def collect_serialized_artifacts(root: Path) -> list[Path]:
    hits: list[Path] = []
    for rel_root in SEARCH_ROOTS:
        base = root / rel_root
        if not base.exists():
            continue
        for pattern in SERIALIZED_PATTERNS:
            for path in base.rglob(pattern):
                if not path.is_file():
                    continue
                name = path.name.lower()
                rel = relative_str(path, root).lower()
                if path.suffix.lower() == ".json":
                    # Keep JSON only when it looks like an exported model bundle, not a manifest.
                    if "manifest" in name:
                        continue
                    if not any(token in rel for token in ["model", "artifact", "bundle", "bytype", "fault_type"]):
                        continue
                hits.append(path)
    return sorted({path.resolve() for path in hits})


def collect_feature_manifests(root: Path) -> list[Path]:
    hits: list[Path] = []
    for rel_root in SEARCH_ROOTS:
        base = root / rel_root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = relative_str(path, root).lower()
            name = path.name.lower()
            if "manifest" in name and ("gpvs" in rel or "bytype" in rel or "fault_type" in rel):
                hits.append(path.resolve())
    return sorted({path for path in hits})


def audit_script_behavior(path: Path) -> dict[str, object]:
    if not path.exists():
        return {
            "exists_flag": 0,
            "loads_serialized_model_flag": 0,
            "trains_model_flag": 0,
            "precomputed_scores_only_flag": 0,
            "note_ko": "script not found",
        }

    text = path.read_text(encoding="utf-8")
    text_lower = text.lower()
    loads_serialized = int(
        any(
            token in text_lower
            for token in [
                "joblib.load",
                "pickle.load",
                "torch.load",
                "onnxruntime",
                "load_model(",
                ".pkl",
                ".joblib",
            ]
        )
    )
    trains_model = int(
        bool(re.search(r"\.fit\s*\(", text))
        or any(token in text for token in ["LogisticRegression(", "HistGradientBoostingClassifier(", "Pipeline("])
    )
    precomputed_scores_only = int(
        ("scores_csv" in text or "--scores-csv" in text or "read_csv" in text)
        and ("to_csv" in text)
        and not loads_serialized
        and not trains_model
    )
    if precomputed_scores_only:
        note = "precomputed GPVS score frame을 읽어 metrics/by-type 표만 계산함; serialized model load와 on-the-fly fit 흔적 없음"
    elif trains_model and not loads_serialized:
        note = "training code는 있으나 serialized model save/load 흔적은 없고 metrics/onepage 산출 중심으로 보임"
    elif loads_serialized:
        note = "serialized model load 흔적이 보임"
    else:
        note = "script behavior를 단정할 만한 load/fit 패턴이 뚜렷하지 않음"
    return {
        "exists_flag": 1,
        "loads_serialized_model_flag": loads_serialized,
        "trains_model_flag": trains_model,
        "precomputed_scores_only_flag": precomputed_scores_only,
        "note_ko": note,
    }


def build_training_asset_rows(root: Path) -> tuple[list[dict[str, object]], int]:
    path = root / "data" / "gpvs" / "out" / GPVS_WINDOW_SCORES_NAME
    df = read_csv(path)
    if "fault_type" not in df.columns:
        raise SystemExit(f"{GPVS_WINDOW_SCORES_NAME} missing required column: fault_type")

    scenario_col = ""
    for candidate in ["scenario", "scenario_id"]:
        if candidate in df.columns:
            scenario_col = candidate
            break

    rows: list[dict[str, object]] = []
    grouped = df.groupby("fault_type", dropna=False)
    for fault_type, grp in grouped:
        source_count = grp["source_id"].astype(str).nunique() if "source_id" in grp.columns else np.nan
        scenario_count = grp[scenario_col].astype(str).nunique() if scenario_col else np.nan
        notes = []
        if np.isfinite(source_count):
            notes.append(f"source_id unique={int(source_count)}")
        else:
            notes.append("source_id column 없음")
        if scenario_col:
            notes.append(f"{scenario_col} unique={int(scenario_count)}")
        else:
            notes.append("scenario/scenario_id column 없음")
        rows.append(
            {
                "path": "data/gpvs/out/gpvs_window_scores.csv",
                "artifact_kind": "score_frame_fault_type_audit",
                "exists_flag": 1,
                "fault_type": normalize_text(fault_type),
                "train_window_count": int(len(grp)),
                "unique_source_count": int(source_count) if np.isfinite(source_count) else "",
                "unique_scenario_count": int(scenario_count) if np.isfinite(scenario_count) else "",
                "notes_ko": "; ".join(notes),
            }
        )
    all_one = int(
        len(rows) > 0
        and all(pd.to_numeric(pd.Series([row["unique_source_count"]]), errors="coerce").fillna(np.nan).iloc[0] == 1 for row in rows)
    )
    return rows, all_one


def load_current_fallback_context(root: Path) -> dict[str, object]:
    share_dir = root / "_share"
    audit_df = read_optional_csv(share_dir / CURRENT_AUDIT_NAME)
    summary_df = read_optional_csv(share_dir / CURRENT_AUDIT_SUMMARY_NAME)
    cv_df = read_optional_csv(share_dir / CURRENT_AUDIT_CV_NAME)

    real_fault_panel_count = np.nan
    collapse_flag = 0
    fallback_model_flag = 0
    grouped_cv_degenerate_flag = 0

    if audit_df is not None and {"panel_id", "gpvs_detailed_top1_fault_type"} <= set(audit_df.columns):
        real_fault_panel_count = int(len(audit_df))
        top1 = audit_df["gpvs_detailed_top1_fault_type"].map(normalize_text)
        nonempty = top1[top1.ne("")]
        collapse_flag = int(len(audit_df) == 6 and len(nonempty) == 6 and nonempty.nunique() == 1)

    if summary_df is not None and not summary_df.empty:
        note = normalize_text(summary_df.iloc[0].get("note_ko", ""))
        fallback_model_flag = int("model_source=fallback_lr:" in note)

    if cv_df is not None and "cv_fold" in cv_df.columns:
        summary_row = cv_df.loc[cv_df["cv_fold"].map(str).eq("summary")]
        if not summary_row.empty:
            macro_f1 = pd.to_numeric(summary_row["cv_macro_f1_mean"], errors="coerce").iloc[0]
            top1_acc = pd.to_numeric(summary_row["cv_top1_accuracy_mean"], errors="coerce").iloc[0]
            grouped_cv_degenerate_flag = int(
                (pd.isna(macro_f1) or float(macro_f1) <= 0.0)
                and (pd.isna(top1_acc) or float(top1_acc) <= 0.0)
            )

    return {
        "real_fault_panel_count": real_fault_panel_count,
        "fallback_top1_collapse_flag": collapse_flag,
        "fallback_model_flag": fallback_model_flag,
        "grouped_cv_degenerate_flag": grouped_cv_degenerate_flag,
    }


def classify_provenance(
    serialized_model_found_flag: int,
    feature_manifest_found_flag: int,
    training_script_found_flag: int,
    evaluation_script_found_flag: int,
    score_frame_found_flag: int,
) -> str:
    if serialized_model_found_flag and feature_manifest_found_flag:
        return "original_trained_head_recovered"
    if (not serialized_model_found_flag) and evaluation_script_found_flag and (not training_script_found_flag):
        return "only_evaluation_assets_present"
    if (not serialized_model_found_flag) and (not evaluation_script_found_flag) and score_frame_found_flag:
        return "only_synthetic_score_assets_present"
    return "provenance_incomplete"


def build_inventory(root: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    inventory_rows: list[dict[str, object]] = []

    serialized_hits = collect_serialized_artifacts(root)
    if serialized_hits:
        for path in serialized_hits:
            inventory_rows.append(
                {
                    "path": relative_str(path, root),
                    "artifact_kind": "serialized_model",
                    "exists_flag": 1,
                    "fault_type": "",
                    "train_window_count": "",
                    "unique_source_count": "",
                    "unique_scenario_count": "",
                    "notes_ko": "serialized by-type model candidate found; provenance별 추가 확인 필요",
                }
            )
    else:
        inventory_rows.append(
            {
                "path": "data/gpvs|research/prognostics|docs/**/*.joblib|*.pkl|*.pickle|*.json",
                "artifact_kind": "serialized_model",
                "exists_flag": 0,
                "fault_type": "",
                "train_window_count": "",
                "unique_source_count": "",
                "unique_scenario_count": "",
                "notes_ko": "repo-local search 범위에서 serialized by-type model artifact 를 찾지 못함",
            }
        )

    manifest_hits = collect_feature_manifests(root)
    if manifest_hits:
        for path in manifest_hits:
            inventory_rows.append(
                {
                    "path": relative_str(path, root),
                    "artifact_kind": "feature_manifest",
                    "exists_flag": 1,
                    "fault_type": "",
                    "train_window_count": "",
                    "unique_source_count": "",
                    "unique_scenario_count": "",
                    "notes_ko": "gpvs/bytype feature manifest candidate",
                }
            )
    else:
        inventory_rows.append(
            {
                "path": "data/gpvs|research/prognostics|docs/**/*manifest*",
                "artifact_kind": "feature_manifest",
                "exists_flag": 0,
                "fault_type": "",
                "train_window_count": "",
                "unique_source_count": "",
                "unique_scenario_count": "",
                "notes_ko": "gpvs/bytype feature manifest 로 단정할 수 있는 파일을 찾지 못함",
            }
        )

    external_eval_path = root / "research" / "prognostics" / EXTERNAL_EVAL_SCRIPT_NAME
    external_eval_audit = audit_script_behavior(external_eval_path)
    inventory_rows.append(
        {
            "path": relative_str(external_eval_path, root),
            "artifact_kind": "evaluation_script",
            "exists_flag": int(external_eval_audit["exists_flag"]),
            "fault_type": "",
            "train_window_count": "",
            "unique_source_count": "",
            "unique_scenario_count": "",
            "notes_ko": str(external_eval_audit["note_ko"]),
        }
    )

    train_script_path = root / "research" / "prognostics" / TRAIN_SCRIPT_NAME
    train_script_audit = audit_script_behavior(train_script_path)
    inventory_rows.append(
        {
            "path": relative_str(train_script_path, root),
            "artifact_kind": "training_script",
            "exists_flag": int(train_script_audit["exists_flag"]),
            "fault_type": "",
            "train_window_count": "",
            "unique_source_count": "",
            "unique_scenario_count": "",
            "notes_ko": "supervised training benchmark script; fit는 하지만 serialized model save/load 흔적은 없음"
            if int(train_script_audit["exists_flag"])
            else "training script not found",
        }
    )

    fixed_assets = [
        (
            root / "data" / "gpvs" / "out" / GPVS_WINDOW_SCORES_NAME,
            "score_frame",
            "synthetic GPVS score frame; source_id/fault_type keyed training/evaluation asset",
        ),
        (
            root / "data" / "gpvs" / "out" / GPVS_BYTYPE_METRICS_NAME,
            "metrics_only",
            "fault_type별 metrics csv; trained classifier artifact 가 아니라 evaluation result",
        ),
        (
            root / "docs" / "reports" / GPVS_FINAL_SUMMARY_NAME,
            "metrics_only",
            "GPVS supervised benchmark 결과 요약 문서; model artifact 나 feature bundle 은 아님",
        ),
        (
            root / "data" / "gpvs" / "_download" / "GPVS_Faults" / "n76t439f65-1" / "CSV_Files",
            "synthetic_label_frame",
            "synthetic GPVS fault scenario CSV bundle; real panel UUID keyed detailed-type attachment source는 아님",
        ),
    ]
    for path, artifact_kind, notes in fixed_assets:
        inventory_rows.append(
            {
                "path": relative_str(path, root),
                "artifact_kind": artifact_kind,
                "exists_flag": int(path.exists()),
                "fault_type": "",
                "train_window_count": "",
                "unique_source_count": "",
                "unique_scenario_count": "",
                "notes_ko": notes,
            }
        )

    training_rows, unique_source_all_one_flag = build_training_asset_rows(root)
    inventory_rows.extend(training_rows)

    inventory_df = pd.DataFrame(inventory_rows).reindex(columns=INVENTORY_COLS)
    flags = {
        "serialized_model_found_flag": int(bool(serialized_hits)),
        "feature_manifest_found_flag": int(bool(manifest_hits)),
        "training_script_found_flag": int(train_script_path.exists()),
        "evaluation_script_found_flag": int(external_eval_path.exists()),
        "score_frame_found_flag": int((root / "data" / "gpvs" / "out" / GPVS_WINDOW_SCORES_NAME).exists()),
        "external_eval_loads_serialized_model_flag": int(external_eval_audit["loads_serialized_model_flag"]),
        "external_eval_trains_model_flag": int(external_eval_audit["trains_model_flag"]),
        "external_eval_precomputed_scores_only_flag": int(external_eval_audit["precomputed_scores_only_flag"]),
        "unique_source_count_per_fault_type_is_one_flag": int(unique_source_all_one_flag),
    }
    return inventory_df, flags


def build_summary(root: Path, inventory_flags: dict[str, object]) -> pd.DataFrame:
    current_context = load_current_fallback_context(root)
    provenance_status = classify_provenance(
        serialized_model_found_flag=int(inventory_flags["serialized_model_found_flag"]),
        feature_manifest_found_flag=int(inventory_flags["feature_manifest_found_flag"]),
        training_script_found_flag=int(inventory_flags["training_script_found_flag"]),
        evaluation_script_found_flag=int(inventory_flags["evaluation_script_found_flag"]),
        score_frame_found_flag=int(inventory_flags["score_frame_found_flag"]),
    )
    collapse_flag = int(current_context["fallback_top1_collapse_flag"])
    grouped_cv_degenerate_flag = int(current_context["grouped_cv_degenerate_flag"])
    unique_source_all_one_flag = int(inventory_flags["unique_source_count_per_fault_type_is_one_flag"])
    current_fallback_lr_attachable_flag = int(
        not (collapse_flag or grouped_cv_degenerate_flag or unique_source_all_one_flag)
    )
    note = (
        f"provenance_status={provenance_status}. "
        f"serialized_model_found={int(inventory_flags['serialized_model_found_flag'])}, "
        f"feature_manifest_found={int(inventory_flags['feature_manifest_found_flag'])}, "
        f"external_eval_loads_serialized_model={int(inventory_flags['external_eval_loads_serialized_model_flag'])}, "
        f"external_eval_trains_model={int(inventory_flags['external_eval_trains_model_flag'])}, "
        f"external_eval_precomputed_scores_only={int(inventory_flags['external_eval_precomputed_scores_only_flag'])}. "
        f"current_real_fault_panel_count={current_context['real_fault_panel_count']}. "
        f"current_audit_uses_fallback_model={int(current_context['fallback_model_flag'])}. "
        f"fallback_top1_collapse_flag={collapse_flag}, grouped_cv_degenerate_flag={grouped_cv_degenerate_flag}, "
        f"unique_source_count_per_fault_type_is_one_flag={unique_source_all_one_flag}. "
        f"따라서 current_fallback_lr_attachable_flag={current_fallback_lr_attachable_flag}."
    )
    return pd.DataFrame(
        [
            {
                "provenance_status": provenance_status,
                "serialized_model_found_flag": int(inventory_flags["serialized_model_found_flag"]),
                "feature_manifest_found_flag": int(inventory_flags["feature_manifest_found_flag"]),
                "training_script_found_flag": int(inventory_flags["training_script_found_flag"]),
                "evaluation_script_found_flag": int(inventory_flags["evaluation_script_found_flag"]),
                "external_eval_loads_serialized_model_flag": int(
                    inventory_flags["external_eval_loads_serialized_model_flag"]
                ),
                "external_eval_trains_model_flag": int(inventory_flags["external_eval_trains_model_flag"]),
                "external_eval_precomputed_scores_only_flag": int(
                    inventory_flags["external_eval_precomputed_scores_only_flag"]
                ),
                "real_fault_panel_count": current_context["real_fault_panel_count"],
                "fallback_top1_collapse_flag": collapse_flag,
                "grouped_cv_degenerate_flag": grouped_cv_degenerate_flag,
                "unique_source_count_per_fault_type_is_one_flag": unique_source_all_one_flag,
                "current_fallback_lr_attachable_flag": current_fallback_lr_attachable_flag,
                "note_ko": note,
            }
        ]
    ).reindex(columns=SUMMARY_COLS)


def build_note(root: Path, inventory_df: pd.DataFrame, summary_df: pd.DataFrame) -> str:
    summary = summary_df.iloc[0]
    found_assets = inventory_df.loc[
        inventory_df["exists_flag"].eq(1)
        & inventory_df["artifact_kind"].isin(
            [
                "serialized_model",
                "feature_manifest",
                "evaluation_script",
                "training_script",
                "score_frame",
                "metrics_only",
                "synthetic_label_frame",
            ]
        ),
        ["path", "artifact_kind", "notes_ko"],
    ].copy()
    found_lines = [
        f"- `{row['path']}` ({row['artifact_kind']}): {row['notes_ko']}"
        for row in found_assets.to_dict(orient="records")
    ]
    if not found_lines:
        found_lines = ["- 확인된 by-type 자산이 없다."]

    status = normalize_text(summary["provenance_status"])
    serialized_found = int(summary["serialized_model_found_flag"])
    manifest_found = int(summary["feature_manifest_found_flag"])
    collapse_flag = int(summary["fallback_top1_collapse_flag"])
    grouped_cv_degenerate_flag = int(summary["grouped_cv_degenerate_flag"])
    unique_source_flag = int(summary["unique_source_count_per_fault_type_is_one_flag"])
    attachable_flag = int(summary["current_fallback_lr_attachable_flag"])
    current_context = load_current_fallback_context(root)
    current_audit_uses_fallback_model = int(current_context["fallback_model_flag"])

    lines = [
        "# 1. 현재 확인된 by-type 자산",
        *found_lines,
        "",
        "# 2. 원본 모델 복구 가능 여부",
        f"- 현재 provenance_status 는 `{status}` 이다.",
        f"- serialized by-type model artifact 발견 여부는 `{serialized_found}` 이고, feature manifest 발견 여부는 `{manifest_found}` 이다.",
    ]
    if status == "original_trained_head_recovered":
        lines.append(
            "- 현재 repo/local output 자산 안에는 recovered export 형태의 by-type model + feature manifest 가 있어, recoverable head 는 확인된다."
        )
    else:
        lines.append("- 따라서 지금 repo/local output 자산만으로는 recoverable by-type head 가 충분히 확인되지 않는다.")
    lines.extend(
        [
            "",
            "# 3. 왜 fallback_lr를 붙이면 안 되는지",
        ]
    )
    if current_audit_uses_fallback_model:
        lines.append("- 현재 detailed-type audit 이 fallback_lr 경로를 사용 중이라, surrogate generalization 상태를 그대로 봐야 한다.")
    else:
        lines.append("- 현재 detailed-type audit 은 recovered artifact 를 쓰고 있더라도, fallback_lr surrogate 자체의 신뢰성 평가는 별도로 유지해야 한다.")
    if collapse_flag:
        lines.append("- fallback_lr 기준 real fault panel top1 이 한 label로 collapse 하는 신호가 관측됐다.")
    else:
        lines.append("- 현재 실산출물은 collapse 상태가 아니더라도, fallback_lr surrogate 자체는 아래 조건 때문에 여전히 attach 불가다.")
    lines.extend(
        [
        f"- grouped CV degenerate flag 는 `{grouped_cv_degenerate_flag}` 이고, fault_type별 unique_source_count==1 flag 는 `{unique_source_flag}` 이다.",
        f"- 그래서 current_fallback_lr_attachable_flag 는 `{attachable_flag}` 이며, main verdict attachment 용도로 쓰면 안 된다.",
        "",
        "# 4. 다음에 정말 필요한 것",
        "- 원본 GPVS by-type serialized model bundle 또는 그와 동등한 export artifact",
        "- 실제 inference 시 쓰였던 정확한 feature manifest / preprocessing manifest",
        "- real panel feature frame을 original by-type head 입력으로 연결하는 재현 가능한 inference path",
        "- source diversity 와 scenario provenance 가 보이는 학습 자산",
        ]
    )
    if collapse_flag:
        lines.insert(
            len(lines) - 5,
            "- 지금 있는 fallback_lr surrogate 는 audit용 surrogate 일 뿐이고, collapse 원인을 이해하기 전까지는 production attachment 근거가 될 수 없다.",
        )
    return "\n".join(lines) + "\n"


def write_outputs(root: Path, inventory_df: pd.DataFrame, summary_df: pd.DataFrame, note_text: str) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    inventory_df.to_csv(share_dir / OUTPUT_INVENTORY_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / OUTPUT_SUMMARY_NAME, index=False, encoding="utf-8-sig")
    (share_dir / OUTPUT_NOTE_NAME).write_text(note_text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    inventory_df, inventory_flags = build_inventory(root)
    summary_df = build_summary(root, inventory_flags)
    note_text = build_note(root, inventory_df, summary_df)
    write_outputs(root, inventory_df, summary_df, note_text)


if __name__ == "__main__":
    main()
