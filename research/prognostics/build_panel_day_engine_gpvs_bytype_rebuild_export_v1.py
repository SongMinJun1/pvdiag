#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.prognostics import gpvs_train_supervised as gpvs_supervised
from research.prognostics.build_panel_day_engine_gpvs_detailed_type_inference_audit_v1 import infer_rows


GPVS_WINDOW_SCORES_NAME = "gpvs_window_scores.csv"
GPVS_BYTYPE_METRICS_NAME = "EXTERNAL_GPVS_BYTYPE_METRICS.csv"
GPVS_FINAL_SUMMARY_NAME = "gpvs_final_summary.md"

RECOVERED_MODEL_NAME = "gpvs_bytype_recovered_model_v1.joblib"
RECOVERED_MANIFEST_NAME = "gpvs_bytype_recovered_feature_manifest_v1.json"
OUTPUT_PARITY_NAME = "panel_day_engine_gpvs_bytype_rebuild_parity_v1.csv"
OUTPUT_SUMMARY_NAME = "panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv"

PARITY_COLS = [
    "metric_scope",
    "metric_name",
    "recovered_value",
    "reference_value",
    "delta",
    "parity_status_ko",
]

SUMMARY_COLS = [
    "recovered_model_exported_flag",
    "recovered_feature_manifest_exported_flag",
    "recovered_model_source_ko",
    "parity_overall_status_ko",
    "current_recovered_attachable_flag",
    "note_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recover and export a reproducible GPVS by-type artifact from the existing supervised training path."
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


def compare_values(recovered_value: object, reference_value: object) -> tuple[object, str]:
    recovered_text = normalize_text(recovered_value)
    reference_text = normalize_text(reference_value)
    recovered_num = pd.to_numeric(pd.Series([recovered_value]), errors="coerce").iloc[0]
    reference_num = pd.to_numeric(pd.Series([reference_value]), errors="coerce").iloc[0]
    if pd.notna(recovered_num) and pd.notna(reference_num):
        delta = float(recovered_num - reference_num)
        if abs(delta) <= 1e-6:
            return delta, "일치"
        if abs(delta) <= 0.02:
            return delta, "근사일치"
        return delta, "불일치"
    if not recovered_text or not reference_text:
        return "", "비교불가"
    return ("", "일치") if recovered_text == reference_text else ("", "불일치")


def parse_docs_primary_summary(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if "### A. strict primary result" not in text:
        return {}
    block = text.split("### A. strict primary result", 1)[1]
    if "###" in block:
        block = block.split("###", 1)[0]

    def extract(label: str) -> str:
        pattern = rf"- {re.escape(label)}:\s*`?([^`\n]+)`?"
        match = re.search(pattern, block)
        return match.group(1).strip() if match else ""

    return {
        "model": extract("model"),
        "feature_set": extract("feature_set"),
        "split": extract("split"),
        "roc_auc": extract("roc_auc"),
        "ap": extract("ap"),
        "f1_best": extract("f1_best"),
        "f1_fpr1": extract("f1_fpr1"),
    }


def build_grouped_primary_metrics(scores_csv: Path) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, list[str], list[str]]:
    score_df = pd.read_csv(scores_csv, low_memory=False)
    gpvs_supervised._check_required(score_df)
    feat_df, _ = gpvs_supervised._feature_engineering(score_df)
    feature_set_cols = gpvs_supervised._candidate_feature_sets()["raw_no_norm_all"]

    y = feat_df["y"].to_numpy(dtype=int)
    groups = feat_df["source_id"].fillna("src").astype(str).to_numpy()
    gss = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=42)
    train_idx, test_idx = next(gss.split(feat_df, y, groups=groups))
    train_df = feat_df.iloc[train_idx].copy()
    test_df = feat_df.iloc[test_idx].copy()
    train_y = y[train_idx]
    test_y = y[test_idx]

    model = gpvs_supervised._build_logreg()
    train_score, test_score, kept_features, meta = gpvs_supervised._fit_predict_with_feature_set(
        model=model,
        train_df=train_df,
        test_df=test_df,
        train_y=train_y,
        feature_cols=feature_set_cols,
    )
    metrics_row = gpvs_supervised._evaluate_scores(
        model_name="LogisticRegression",
        feature_set="raw_no_norm_all",
        split_name="grouped_source",
        split_kind="stricter_file_split",
        train_y=train_y,
        test_y=test_y,
        train_score=train_score,
        test_score=test_score,
        candidate_feature_count=len(feature_set_cols),
        kept_features=kept_features,
        meta=meta,
        note="recovered grouped_source primary path",
    )
    metrics_df = pd.DataFrame([metrics_row])
    positive_mask = feat_df["y"].eq(1) & feat_df["fault_type"].map(normalize_text).ne("")
    positive_df = feat_df.loc[positive_mask].copy()
    label_space = sorted(positive_df["fault_type"].map(normalize_text).unique().tolist())
    return metrics_df, metrics_df.iloc[0], positive_df, feature_set_cols, label_space


def export_recovered_artifact(root: Path) -> tuple[Path, Path, dict[str, object]]:
    scores_csv = root / "data" / "gpvs" / "out" / GPVS_WINDOW_SCORES_NAME
    metrics_df, primary_row, positive_df, feature_set_cols, label_space = build_grouped_primary_metrics(scores_csv)

    if positive_df.empty:
        raise SystemExit(f"{GPVS_WINDOW_SCORES_NAME} has no positive fault_type rows for by-type export")

    X_train, _, kept_features, meta = gpvs_supervised._stabilize_feature_frames(
        positive_df,
        positive_df,
        feature_set_cols,
    )
    y_train = positive_df["fault_type"].map(normalize_text)
    if len(kept_features) == 0 or y_train.nunique() < 2:
        raise SystemExit("recovered by-type export does not have enough kept features or label diversity")

    model = gpvs_supervised._build_logreg()
    model.fit(X_train, y_train)

    out_dir = root / "data" / "gpvs" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / RECOVERED_MODEL_NAME
    manifest_path = out_dir / RECOVERED_MANIFEST_NAME

    joblib.dump(
        {
            "model": model,
            "feature_cols": kept_features,
            "label_space": label_space,
            "model_source": "gpvs_train_supervised::LogisticRegression::raw_no_norm_all::multiclass_rebuild",
        },
        model_path,
    )
    manifest = {
        "training_script_path": "research/prognostics/gpvs_train_supervised.py",
        "recovered_model_source_ko": "gpvs_train_supervised selected primary path reuse",
        "model_class": "LogisticRegression",
        "feature_set": "raw_no_norm_all",
        "candidate_feature_count": int(len(feature_set_cols)),
        "kept_feature_count": int(len(kept_features)),
        "kept_features": kept_features,
        "removed_all_nan": list(meta.get("removed_all_nan", [])),
        "removed_zero_var": list(meta.get("removed_zero_var", [])),
        "label_space": label_space,
        "positive_training_row_count": int(len(positive_df)),
        "divergence_note_ko": (
            "원 gpvs_train_supervised.py 는 binary fault-vs-healthy benchmark 이다. "
            "이번 export 는 동일 feature engineering, 동일 selected feature_set(raw_no_norm_all), "
            "동일 LogisticRegression preprocessing path 를 재사용해 raw fault_type multiclass head 로 기계적으로 재학습했다."
        ),
        "grouped_source_primary_metrics": metrics_df.iloc[0].to_dict(),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return model_path, manifest_path, manifest


def build_parity_df(root: Path, manifest: dict[str, object]) -> tuple[pd.DataFrame, str]:
    rows: list[dict[str, object]] = []
    scores_csv = root / "data" / "gpvs" / "out" / GPVS_WINDOW_SCORES_NAME
    bytype_metrics_csv = root / "data" / "gpvs" / "out" / GPVS_BYTYPE_METRICS_NAME
    docs_path = root / "docs" / "reports" / GPVS_FINAL_SUMMARY_NAME

    primary_metrics = manifest["grouped_source_primary_metrics"]
    docs_summary = parse_docs_primary_summary(docs_path)

    comparisons = [
        ("docs_strict_primary", "model", "LogisticRegression", docs_summary.get("model", "")),
        ("docs_strict_primary", "feature_set", "raw_no_norm_all", docs_summary.get("feature_set", "")),
        ("docs_strict_primary", "split", "grouped_source", docs_summary.get("split", "")),
        ("docs_strict_primary", "roc_auc", primary_metrics.get("roc_auc", ""), docs_summary.get("roc_auc", "")),
        ("docs_strict_primary", "ap", primary_metrics.get("ap", ""), docs_summary.get("ap", "")),
        ("docs_strict_primary", "f1_best", primary_metrics.get("f1_best", ""), docs_summary.get("f1_best", "")),
        ("docs_strict_primary", "f1_fpr1", primary_metrics.get("f1_fpr1", ""), docs_summary.get("f1_fpr1", "")),
    ]

    bytype_df = read_csv(bytype_metrics_csv)
    ref_fault_types = (
        bytype_df.loc[pd.to_numeric(bytype_df.get("sid"), errors="coerce").fillna(0).gt(0), "fault_type"]
        if "sid" in bytype_df.columns
        else bytype_df["fault_type"]
    )
    ref_fault_types = sorted({normalize_text(value) for value in ref_fault_types.tolist() if normalize_text(value)})
    recovered_fault_types = sorted({normalize_text(value) for value in manifest["label_space"] if normalize_text(value)})
    overlap_count = len(set(recovered_fault_types) & set(ref_fault_types))
    comparisons.extend(
        [
            ("external_bytype_metrics", "unique_fault_type_count", len(recovered_fault_types), len(ref_fault_types)),
            ("external_bytype_metrics", "fault_type_overlap_count", overlap_count, len(ref_fault_types)),
        ]
    )

    statuses: list[str] = []
    for metric_scope, metric_name, recovered_value, reference_value in comparisons:
        delta, status = compare_values(recovered_value, reference_value)
        statuses.append(status)
        rows.append(
            {
                "metric_scope": metric_scope,
                "metric_name": metric_name,
                "recovered_value": recovered_value,
                "reference_value": reference_value,
                "delta": delta,
                "parity_status_ko": status,
            }
        )

    if any(status == "불일치" for status in statuses):
        overall = "불일치"
    elif any(status == "근사일치" for status in statuses):
        overall = "근사일치"
    elif any(status == "일치" for status in statuses):
        overall = "일치"
    else:
        overall = "비교불가"

    return pd.DataFrame(rows).reindex(columns=PARITY_COLS), overall


def build_summary(root: Path, model_path: Path, manifest_path: Path, manifest: dict[str, object], parity_df: pd.DataFrame, parity_overall_status_ko: str) -> pd.DataFrame:
    audit_df, audit_summary_df, _label_distribution_df, _cv_summary_df, realpanel_sanity_df = infer_rows(root)
    recovered_model_used_flag = int(
        "gpvs_detailed_model_source" in audit_df.columns
        and audit_df["gpvs_detailed_model_source"].eq("recovered_artifact").any()
    )
    collapse_flag = int(
        not realpanel_sanity_df.empty
        and realpanel_sanity_df["single_type_collapse_flag"].fillna(0).astype(int).eq(1).all()
    )
    current_recovered_attachable_flag = int(
        model_path.exists()
        and manifest_path.exists()
        and recovered_model_used_flag
        and parity_overall_status_ko != "불일치"
        and collapse_flag == 0
    )
    note = (
        "recovered export 는 gpvs_train_supervised selected primary path를 재사용해 만든 multiclass by-type artifact 다. "
        f"recovered_model_used_flag={recovered_model_used_flag}, parity_overall_status_ko={parity_overall_status_ko}, "
        f"realpanel_collapse_flag={collapse_flag}, current_recovered_attachable_flag={current_recovered_attachable_flag}. "
        "do_not_attach 결론은 parity 와 real-panel collapse 둘 다 풀리기 전까지 유지해야 한다."
    )
    return pd.DataFrame(
        [
            {
                "recovered_model_exported_flag": int(model_path.exists()),
                "recovered_feature_manifest_exported_flag": int(manifest_path.exists()),
                "recovered_model_source_ko": manifest.get("recovered_model_source_ko", ""),
                "parity_overall_status_ko": parity_overall_status_ko,
                "current_recovered_attachable_flag": current_recovered_attachable_flag,
                "note_ko": note,
            }
        ]
    ).reindex(columns=SUMMARY_COLS)


def write_outputs(root: Path, parity_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    parity_df.to_csv(share_dir / OUTPUT_PARITY_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / OUTPUT_SUMMARY_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    model_path, manifest_path, manifest = export_recovered_artifact(root)
    parity_df, parity_overall_status_ko = build_parity_df(root, manifest)
    summary_df = build_summary(root, model_path, manifest_path, manifest, parity_df, parity_overall_status_ko)
    write_outputs(root, parity_df, summary_df)


if __name__ == "__main__":
    main()
