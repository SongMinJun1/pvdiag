#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, recall_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


FAULT_PANEL_EVENT_AUDIT_NAME = "panel_day_engine_fault_panel_event_audit_v1.csv"
PANEL_MULTIAXIS_VERDICT_NAME = "panel_day_engine_panel_multiaxis_verdict_v1.csv"
GPVS_WINDOW_SCORES_NAME = "gpvs_window_scores.csv"
GPVS_BYTYPE_METRICS_NAME = "EXTERNAL_GPVS_BYTYPE_METRICS.csv"
RECOVERED_MODEL_NAME = "gpvs_bytype_recovered_model_v1.joblib"
RECOVERED_FEATURE_MANIFEST_NAME = "gpvs_bytype_recovered_feature_manifest_v1.json"

OUTPUT_AUDIT_NAME = "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv"
OUTPUT_SUMMARY_NAME = "panel_day_engine_gpvs_detailed_type_inference_summary_v1.csv"
OUTPUT_LABEL_DISTRIBUTION_NAME = "panel_day_engine_gpvs_detailed_type_label_distribution_v1.csv"
OUTPUT_CV_SUMMARY_NAME = "panel_day_engine_gpvs_detailed_type_cv_summary_v1.csv"
OUTPUT_REALPANEL_SANITY_NAME = "panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv"

TRAIN_EXCLUDE_COLS = {
    "sample_id",
    "source_id",
    "window_idx",
    "window_ord",
    "n_windows",
    "t0",
    "t1",
    "label_fault",
    "is_fault_window",
    "fault_sid",
    "fault_mode",
    "fault_type",
    "is_fault_file",
}

RAW_FEATURE_COLS = [
    "level_drop_raw",
    "v_drop_raw",
    "hs_raw",
    "dtw_raw",
    "ae_raw",
]

REAL_PANEL_RAW_BUILDERS = {
    "level_drop_raw": lambda row: max(0.0, 1.0 - _to_float(row.get("mid_ratio"))),
    "v_drop_raw": lambda row: max(0.0, _to_float(row.get("v_drop"))),
    "hs_raw": lambda row: _to_float(row.get("hs_score")),
    "dtw_raw": lambda row: _to_float(row.get("dtw_dist")),
    "ae_raw": lambda row: _to_float(row.get("recon_error")),
}
DEGENERATE_SPAN_EPS = 1e-12

AUDIT_TOP1_MIN_PROBA = 0.25
AUDIT_MIN_MARGIN = 0.10

AUDIT_COLS = [
    "site",
    "panel_id",
    "event_reference_date",
    "gpvs_detailed_model_source",
    "gpvs_family_label",
    "gpvs_detailed_top1_fault_type",
    "gpvs_detailed_top1_score",
    "gpvs_detailed_top2_fault_type",
    "gpvs_detailed_top2_score",
    "gpvs_detailed_margin",
    "gpvs_detailed_status_ko",
    "gpvs_detailed_reason_ko",
]

SUMMARY_COLS = [
    "fault_panel_count",
    "inference_success_count",
    "abstain_count",
    "inference_unavailable_count",
    "note_ko",
]

LABEL_DISTRIBUTION_COLS = [
    "fault_type",
    "train_window_count",
    "train_source_count",
]

CV_SUMMARY_COLS = [
    "cv_fold",
    "macro_recall",
    "macro_f1",
    "top1_accuracy",
    "unique_predicted_fault_type_count",
    "cv_macro_recall_mean",
    "cv_macro_f1_mean",
    "cv_top1_accuracy_mean",
    "cv_unique_predicted_fault_type_count_mean",
    "note_ko",
]

REALPANEL_SANITY_COLS = [
    "site",
    "panel_id",
    "gpvs_family_label",
    "gpvs_detailed_top1_fault_type",
    "gpvs_detailed_top1_score",
    "gpvs_detailed_top2_fault_type",
    "gpvs_detailed_top2_score",
    "gpvs_detailed_margin",
    "family_vs_detail_consistency_ko",
    "single_type_collapse_flag",
    "attach_recommendation_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit-only GPVS detailed fault-type inference for current real fault panels."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def _to_float(value: object) -> float:
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return float(number) if pd.notna(number) else np.nan


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def ensure_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"{name} missing columns: {missing}")


def normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in normalized.columns:
        if normalized[column].dtype == object:
            normalized[column] = normalized[column].map(normalize_text)
    return normalized


def relative_str(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def build_inputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    share_dir = root / "_share"
    fault_df = normalize_frame(read_csv(share_dir / FAULT_PANEL_EVENT_AUDIT_NAME))
    verdict_df = normalize_frame(read_csv(share_dir / PANEL_MULTIAXIS_VERDICT_NAME))
    ensure_columns(
        fault_df,
        ["site", "panel_id", "strict_trigger_date", "first_final_fault_date"],
        FAULT_PANEL_EVENT_AUDIT_NAME,
    )
    ensure_columns(
        verdict_df,
        ["site", "panel_id", "패널고장여부_ko", "GPVS_참고유형_ko"],
        PANEL_MULTIAXIS_VERDICT_NAME,
    )
    return fault_df, verdict_df


def choose_reference_date(row: pd.Series) -> str:
    strict_trigger = normalize_text(row.get("strict_trigger_date", ""))
    if strict_trigger:
        return strict_trigger
    first_final = normalize_text(row.get("first_final_fault_date", ""))
    if first_final:
        return first_final
    return ""


def load_serialized_bundle(path: Path) -> tuple[Any, list[str], str] | None:
    suffix = path.suffix.lower()
    payload: Any
    try:
        if suffix in {".pkl", ".pickle"}:
            with path.open("rb") as fp:
                payload = pickle.load(fp)
        elif suffix == ".joblib":
            import joblib  # type: ignore

            payload = joblib.load(path)
        elif suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
        else:
            return None
    except Exception:
        return None

    estimator = None
    feature_cols: list[str] = []
    if isinstance(payload, dict):
        estimator = payload.get("model") or payload.get("estimator") or payload.get("classifier")
        raw_feature_cols = payload.get("feature_cols") or payload.get("feature_names") or payload.get("columns")
        if isinstance(raw_feature_cols, list) and all(isinstance(item, str) for item in raw_feature_cols):
            feature_cols = [str(item) for item in raw_feature_cols]
    elif hasattr(payload, "predict_proba"):
        estimator = payload
        feature_cols = []

    if estimator is None or not hasattr(estimator, "predict_proba"):
        return None
    if not feature_cols:
        return None
    return estimator, feature_cols, f"serialized:{path.name}"


def load_training_frame(root: Path) -> pd.DataFrame:
    path = root / "data" / "gpvs" / "out" / GPVS_WINDOW_SCORES_NAME
    df = normalize_frame(read_csv(path))
    ensure_columns(df, ["fault_type"], GPVS_WINDOW_SCORES_NAME)
    return df


def positive_training_mask(training_df: pd.DataFrame) -> pd.Series:
    if "fault_sid" in training_df.columns:
        return pd.to_numeric(training_df["fault_sid"], errors="coerce").fillna(0).gt(0)
    if "is_fault_window" in training_df.columns:
        return pd.to_numeric(training_df["is_fault_window"], errors="coerce").fillna(0).eq(1)
    return training_df["fault_type"].map(normalize_text).str.startswith("F")


def build_fallback_estimator() -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=5000,
                    random_state=42,
                    class_weight="balanced",
                ),
            ),
        ]
    )


def choose_training_feature_cols(training_df: pd.DataFrame) -> list[str]:
    feature_cols: list[str] = []
    for column in training_df.columns:
        if column in TRAIN_EXCLUDE_COLS:
            continue
        if column not in REAL_PANEL_RAW_BUILDERS:
            continue
        if pd.api.types.is_numeric_dtype(training_df[column]):
            feature_cols.append(column)
    if not feature_cols:
        raise SystemExit(
            f"{GPVS_WINDOW_SCORES_NAME} does not expose reusable numeric feature columns overlapping the real-panel GPVS path"
        )
    return sorted(feature_cols)


def build_fallback_model(root: Path) -> tuple[Pipeline, list[str], str]:
    training_df = load_training_frame(root)
    positive_mask = positive_training_mask(training_df)
    train_df = training_df.loc[positive_mask & training_df["fault_type"].map(normalize_text).ne("")].copy()
    if train_df.empty:
        raise SystemExit(f"{GPVS_WINDOW_SCORES_NAME} has no usable positive fault_type rows for fallback by-type training")

    feature_cols = choose_training_feature_cols(train_df)
    X = train_df[feature_cols].apply(pd.to_numeric, errors="coerce")
    y = train_df["fault_type"].map(normalize_text)
    if y.nunique() < 2:
        raise SystemExit(f"{GPVS_WINDOW_SCORES_NAME} must contain at least two fault_type classes for multiclass fallback training")

    model = build_fallback_estimator()
    model.fit(X, y)
    return model, feature_cols, f"fallback_lr:{GPVS_WINDOW_SCORES_NAME}"


def load_recovered_bundle(root: Path) -> tuple[Any, list[str], str] | None:
    model_path = root / "data" / "gpvs" / "out" / RECOVERED_MODEL_NAME
    manifest_path = root / "data" / "gpvs" / "out" / RECOVERED_FEATURE_MANIFEST_NAME
    if not model_path.exists() or not manifest_path.exists():
        return None
    loaded = load_serialized_bundle(model_path)
    if loaded is None:
        return None
    estimator, feature_cols, _raw_source = loaded
    return estimator, feature_cols, "recovered_artifact"


def load_model_bundle(root: Path) -> tuple[Any, list[str], str]:
    recovered = load_recovered_bundle(root)
    if recovered is not None:
        return recovered
    model, feature_cols, _source = build_fallback_model(root)
    return model, feature_cols, "fallback_lr"


def load_panel_core(root: Path, site: str) -> pd.DataFrame:
    path = root / "data" / site / "out" / "panel_day_core.csv"
    df = normalize_frame(read_csv(path))
    ensure_columns(df, ["date", "panel_id", "mid_ratio", "v_drop", "dtw_dist", "hs_score", "recon_error"], path.name)
    return df


def build_real_panel_feature_row(
    panel_df: pd.DataFrame,
    reference_date: str,
    feature_cols: list[str],
) -> tuple[pd.DataFrame | None, str]:
    panel_work = panel_df.copy()
    panel_work["date"] = pd.to_datetime(panel_work["date"], errors="coerce")
    ref_ts = pd.to_datetime(reference_date, errors="coerce")
    if pd.isna(ref_ts):
        return None, "event_reference_date 해석 실패"

    panel_work = panel_work.loc[panel_work["date"].notna()].sort_values("date", kind="stable").reset_index(drop=True)
    if panel_work.empty:
        return None, "real-panel panel_day_core row 가 비어 있음"

    for raw_col, builder in REAL_PANEL_RAW_BUILDERS.items():
        panel_work[raw_col] = panel_work.apply(builder, axis=1)
    panel_work["mode_L"] = 0.0
    panel_work["mode_M"] = 0.0

    for raw_col in RAW_FEATURE_COLS:
        numeric = pd.to_numeric(panel_work[raw_col], errors="coerce")
        panel_work[f"delta_{raw_col}"] = numeric.diff()
        panel_work[f"rollmean3_{raw_col}"] = numeric.rolling(window=3, min_periods=1).mean()
        panel_work[f"rollmax3_{raw_col}"] = numeric.rolling(window=3, min_periods=1).max()

        deg_values: list[float] = []
        clean_values: list[float] = []
        for value in numeric.tolist():
            if np.isfinite(value):
                clean_values.append(float(value))
            if not clean_values:
                deg = 1.0
            else:
                arr = np.asarray(clean_values, dtype=float)
                n_unique = int(pd.Series(arr).nunique(dropna=True))
                span = float(np.max(arr) - np.min(arr))
                deg = float(n_unique <= 1 or (np.isfinite(span) and span <= DEGENERATE_SPAN_EPS))
            deg_values.append(deg)
        panel_work[f"deg_{raw_col}"] = deg_values

    panel_work["active_axis_count"] = sum((1.0 - pd.to_numeric(panel_work[f"deg_{raw_col}"], errors="coerce").fillna(1.0)) for raw_col in RAW_FEATURE_COLS)

    event_rows = panel_work.loc[panel_work["date"].eq(ref_ts)].copy()
    if event_rows.empty:
        return None, "event_reference_date 와 일치하는 real-panel GPVS feature row 없음"
    event_row = event_rows.iloc[0]

    missing_feature_cols = [column for column in feature_cols if column not in panel_work.columns]
    if missing_feature_cols:
        return None, f"real-panel path로 재구성할 수 없는 feature가 있어 추론 불가: {missing_feature_cols}"

    feature_payload: dict[str, float] = {}
    for feature_col in feature_cols:
        feature_payload[feature_col] = _to_float(event_row.get(feature_col))
    feature_df = pd.DataFrame([feature_payload]).reindex(columns=feature_cols)
    finite_count = feature_df.apply(lambda column: column.map(np.isfinite)).sum(axis=1).iloc[0]
    if finite_count <= 0:
        return None, "real-panel feature vector가 모두 결측이라 추론 불가"
    return feature_df, ""


def build_label_distribution_df(training_df: pd.DataFrame) -> pd.DataFrame:
    positive_df = training_df.loc[
        positive_training_mask(training_df) & training_df["fault_type"].map(normalize_text).ne("")
    ].copy()
    if positive_df.empty:
        return pd.DataFrame(columns=LABEL_DISTRIBUTION_COLS)

    source_series = (
        positive_df["source_id"].map(normalize_text)
        if "source_id" in positive_df.columns
        else pd.Series([""] * len(positive_df), index=positive_df.index)
    )
    working = positive_df.assign(_source_id_norm=source_series)
    distribution_df = (
        working.groupby("fault_type", dropna=False)
        .agg(
            train_window_count=("fault_type", "size"),
            train_source_count=("_source_id_norm", lambda values: values[values.ne("")].nunique()),
        )
        .reset_index()
        .sort_values(["train_window_count", "fault_type"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
    )
    return distribution_df.reindex(columns=LABEL_DISTRIBUTION_COLS)


def build_grouped_cv_summary_df(training_df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    positive_df = training_df.loc[
        positive_training_mask(training_df) & training_df["fault_type"].map(normalize_text).ne("")
    ].copy()
    if positive_df.empty:
        return pd.DataFrame(
            [
                {
                    "cv_fold": "summary",
                    "macro_recall": np.nan,
                    "macro_f1": np.nan,
                    "top1_accuracy": np.nan,
                    "unique_predicted_fault_type_count": np.nan,
                    "cv_macro_recall_mean": np.nan,
                    "cv_macro_f1_mean": np.nan,
                    "cv_top1_accuracy_mean": np.nan,
                    "cv_unique_predicted_fault_type_count_mean": np.nan,
                    "note_ko": "usable positive training rows 가 없어 grouped CV 를 계산하지 못함",
                }
            ]
        ).reindex(columns=CV_SUMMARY_COLS)

    X = positive_df[feature_cols].apply(pd.to_numeric, errors="coerce")
    y = positive_df["fault_type"].map(normalize_text)
    group_values = (
        positive_df["source_id"].map(normalize_text)
        if "source_id" in positive_df.columns
        else pd.Series([""] * len(positive_df), index=positive_df.index)
    )
    groups = group_values.where(group_values.ne(""), y)
    unique_groups = sorted({value for value in groups.tolist() if value})
    if len(unique_groups) >= 3:
        splitter = GroupKFold(n_splits=min(5, len(unique_groups)))
        split_iter = splitter.split(X, y, groups=groups)
        split_note = f"GroupKFold(source_id_or_fault_type), n_splits={min(5, len(unique_groups))}"
    elif len(unique_groups) >= 2:
        splitter = GroupShuffleSplit(n_splits=min(5, len(unique_groups)), test_size=0.3, random_state=42)
        split_iter = splitter.split(X, y, groups=groups)
        split_note = f"GroupShuffleSplit(source_id_or_fault_type), n_splits={min(5, len(unique_groups))}"
    else:
        return pd.DataFrame(
            [
                {
                    "cv_fold": "summary",
                    "macro_recall": np.nan,
                    "macro_f1": np.nan,
                    "top1_accuracy": np.nan,
                    "unique_predicted_fault_type_count": np.nan,
                    "cv_macro_recall_mean": np.nan,
                    "cv_macro_f1_mean": np.nan,
                    "cv_top1_accuracy_mean": np.nan,
                    "cv_unique_predicted_fault_type_count_mean": np.nan,
                    "note_ko": "grouped CV 를 위한 unique group 수가 2 미만이라 계산하지 못함",
                }
            ]
        ).reindex(columns=CV_SUMMARY_COLS)

    fold_rows: list[dict[str, object]] = []
    for fold_idx, (train_idx, test_idx) in enumerate(split_iter, start=1):
        model = clone(build_fallback_estimator())
        X_train = X.iloc[train_idx]
        y_train = y.iloc[train_idx]
        X_test = X.iloc[test_idx]
        y_test = y.iloc[test_idx]

        if y_train.nunique() < 2 or len(X_test) == 0:
            fold_rows.append(
                {
                    "cv_fold": fold_idx,
                    "macro_recall": np.nan,
                    "macro_f1": np.nan,
                    "top1_accuracy": np.nan,
                    "unique_predicted_fault_type_count": np.nan,
                    "cv_macro_recall_mean": np.nan,
                    "cv_macro_f1_mean": np.nan,
                    "cv_top1_accuracy_mean": np.nan,
                    "cv_unique_predicted_fault_type_count_mean": np.nan,
                    "note_ko": f"{split_note}; fold 학습 class 수 부족 또는 test row 없음",
                }
            )
            continue

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        fold_rows.append(
            {
                "cv_fold": fold_idx,
                "macro_recall": recall_score(y_test, y_pred, average="macro", zero_division=0),
                "macro_f1": f1_score(y_test, y_pred, average="macro", zero_division=0),
                "top1_accuracy": accuracy_score(y_test, y_pred),
                "unique_predicted_fault_type_count": int(pd.Series(y_pred).nunique()),
                "cv_macro_recall_mean": np.nan,
                "cv_macro_f1_mean": np.nan,
                "cv_top1_accuracy_mean": np.nan,
                "cv_unique_predicted_fault_type_count_mean": np.nan,
                "note_ko": split_note,
            }
        )

    fold_df = pd.DataFrame(fold_rows).reindex(columns=CV_SUMMARY_COLS)
    valid_fold_df = fold_df.loc[fold_df["cv_fold"].map(str).ne("summary")].copy()
    summary_row = {
        "cv_fold": "summary",
        "macro_recall": np.nan,
        "macro_f1": np.nan,
        "top1_accuracy": np.nan,
        "unique_predicted_fault_type_count": np.nan,
        "cv_macro_recall_mean": pd.to_numeric(valid_fold_df["macro_recall"], errors="coerce").mean(),
        "cv_macro_f1_mean": pd.to_numeric(valid_fold_df["macro_f1"], errors="coerce").mean(),
        "cv_top1_accuracy_mean": pd.to_numeric(valid_fold_df["top1_accuracy"], errors="coerce").mean(),
        "cv_unique_predicted_fault_type_count_mean": pd.to_numeric(
            valid_fold_df["unique_predicted_fault_type_count"], errors="coerce"
        ).mean(),
        "note_ko": split_note,
    }
    return pd.concat([fold_df, pd.DataFrame([summary_row]).reindex(columns=CV_SUMMARY_COLS)], ignore_index=True)


def build_realpanel_sanity_df(audit_df: pd.DataFrame, cv_summary_df: pd.DataFrame) -> pd.DataFrame:
    top1_labels = audit_df["gpvs_detailed_top1_fault_type"].map(normalize_text)
    nonempty_top1 = top1_labels[top1_labels.ne("")]
    single_type_collapse = int(len(audit_df) == 6 and len(nonempty_top1) == 6 and nonempty_top1.nunique() == 1)

    cv_summary_row = cv_summary_df.loc[cv_summary_df["cv_fold"].map(str).eq("summary")]
    cv_macro_f1_mean = (
        pd.to_numeric(cv_summary_row["cv_macro_f1_mean"], errors="coerce").iloc[0]
        if not cv_summary_row.empty
        else np.nan
    )
    cv_unique_pred_count_mean = (
        pd.to_numeric(cv_summary_row["cv_unique_predicted_fault_type_count_mean"], errors="coerce").iloc[0]
        if not cv_summary_row.empty
        else np.nan
    )
    poor_cv = (
        pd.isna(cv_macro_f1_mean)
        or pd.isna(cv_unique_pred_count_mean)
        or float(cv_macro_f1_mean) < 0.50
        or float(cv_unique_pred_count_mean) < 2.0
    )

    sanity_rows: list[dict[str, object]] = []
    for row in audit_df.to_dict(orient="records"):
        family_label = normalize_text(row.get("gpvs_family_label", ""))
        status = normalize_text(row.get("gpvs_detailed_status_ko", ""))

        model_source = normalize_text(row.get("gpvs_detailed_model_source", ""))

        if single_type_collapse:
            family_vs_detail = "real fault 6건이 동일 top1 detailed type 으로 collapse 되어 family 대비 directional consistency를 신뢰하기 어려움"
            attach_recommendation = "do_not_attach"
        elif model_source == "fallback_lr" and poor_cv:
            family_vs_detail = "grouped CV macro 성능 또는 predicted type 다양성이 낮아 family 대비 detailed type 신뢰가 부족함"
            attach_recommendation = "do_not_attach"
        elif not family_label:
            family_vs_detail = "attached GPVS family label 이 비어 있어 directional consistency 판단을 보류함"
            attach_recommendation = "caution_only" if status == "추론성공" else "do_not_attach"
        elif status == "추론성공":
            family_vs_detail = "broad GPVS family 와 fine detailed type 사이 직접 충돌 근거는 현재 audit 자산에서 확인되지 않음"
            attach_recommendation = "attach_ok"
        else:
            family_vs_detail = "fine detailed type 자체가 판정유보/추론불가 상태라 family 대비 consistency도 함께 보류함"
            attach_recommendation = "caution_only"

        sanity_rows.append(
            {
                "site": normalize_text(row.get("site", "")),
                "panel_id": normalize_text(row.get("panel_id", "")),
                "gpvs_family_label": family_label,
                "gpvs_detailed_top1_fault_type": normalize_text(row.get("gpvs_detailed_top1_fault_type", "")),
                "gpvs_detailed_top1_score": row.get("gpvs_detailed_top1_score", ""),
                "gpvs_detailed_top2_fault_type": normalize_text(row.get("gpvs_detailed_top2_fault_type", "")),
                "gpvs_detailed_top2_score": row.get("gpvs_detailed_top2_score", ""),
                "gpvs_detailed_margin": row.get("gpvs_detailed_margin", ""),
                "family_vs_detail_consistency_ko": family_vs_detail,
                "single_type_collapse_flag": single_type_collapse,
                "attach_recommendation_ko": attach_recommendation,
            }
        )

    return pd.DataFrame(sanity_rows).reindex(columns=REALPANEL_SANITY_COLS)


def infer_rows(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fault_df, verdict_df = build_inputs(root)
    fault_only = fault_df.copy()
    if len(fault_only) != 6:
        raise SystemExit(f"{FAULT_PANEL_EVENT_AUDIT_NAME} must contain exactly 6 current fault panels, found {len(fault_only)}")

    verdict_fault_df = verdict_df.loc[verdict_df["패널고장여부_ko"].eq("고장"), ["site", "panel_id", "GPVS_참고유형_ko"]].copy()
    if len(verdict_fault_df) != 6:
        raise SystemExit(f"{PANEL_MULTIAXIS_VERDICT_NAME} must contain exactly 6 fault rows by 패널고장여부_ko==고장, found {len(verdict_fault_df)}")
    if verdict_fault_df.duplicated(subset=["site", "panel_id"]).any():
        raise SystemExit(f"{PANEL_MULTIAXIS_VERDICT_NAME} fault rows must be unique by (site, panel_id)")
    family_by_key = {
        (normalize_text(row["site"]), normalize_text(row["panel_id"])): normalize_text(row["GPVS_참고유형_ko"])
        for row in verdict_fault_df.to_dict(orient="records")
    }

    training_df = load_training_frame(root)
    label_distribution_df = build_label_distribution_df(training_df)
    feature_cols = choose_training_feature_cols(
        training_df.loc[
            positive_training_mask(training_df) & training_df["fault_type"].map(normalize_text).ne("")
        ].copy()
    )
    cv_summary_df = build_grouped_cv_summary_df(training_df, feature_cols)
    model, feature_cols, model_source = load_model_bundle(root)
    panel_core_cache: dict[str, pd.DataFrame] = {}
    audit_rows: list[dict[str, object]] = []

    for row in fault_only.to_dict(orient="records"):
        site = normalize_text(row["site"])
        panel_id = normalize_text(row["panel_id"])
        key = (site, panel_id)
        reference_date = choose_reference_date(pd.Series(row))
        gpvs_family_label = family_by_key.get(key, "")

        if not reference_date:
            audit_rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "event_reference_date": "",
                    "gpvs_detailed_model_source": "inference_unavailable",
                    "gpvs_family_label": gpvs_family_label,
                    "gpvs_detailed_top1_fault_type": "",
                    "gpvs_detailed_top1_score": "",
                    "gpvs_detailed_top2_fault_type": "",
                    "gpvs_detailed_top2_score": "",
                    "gpvs_detailed_margin": "",
                    "gpvs_detailed_status_ko": "추론불가",
                    "gpvs_detailed_reason_ko": f"model_source={model_source}; strict_trigger_date/first_final_fault_date 모두 없음",
                }
            )
            continue

        if site not in panel_core_cache:
            try:
                panel_core_cache[site] = load_panel_core(root, site)
            except SystemExit as exc:
                audit_rows.append(
                    {
                        "site": site,
                        "panel_id": panel_id,
                        "event_reference_date": reference_date,
                        "gpvs_detailed_model_source": "inference_unavailable",
                        "gpvs_family_label": gpvs_family_label,
                        "gpvs_detailed_top1_fault_type": "",
                        "gpvs_detailed_top1_score": "",
                        "gpvs_detailed_top2_fault_type": "",
                        "gpvs_detailed_top2_score": "",
                        "gpvs_detailed_margin": "",
                        "gpvs_detailed_status_ko": "추론불가",
                        "gpvs_detailed_reason_ko": f"model_source={model_source}; {exc}",
                    }
                )
                continue

        panel_df = panel_core_cache[site].loc[panel_core_cache[site]["panel_id"].eq(panel_id)].copy()
        feature_df, feature_error = build_real_panel_feature_row(panel_df, reference_date, feature_cols)
        if feature_error:
            audit_rows.append(
                {
                    "site": site,
                    "panel_id": panel_id,
                    "event_reference_date": reference_date,
                    "gpvs_detailed_model_source": "inference_unavailable",
                    "gpvs_family_label": gpvs_family_label,
                    "gpvs_detailed_top1_fault_type": "",
                    "gpvs_detailed_top1_score": "",
                    "gpvs_detailed_top2_fault_type": "",
                    "gpvs_detailed_top2_score": "",
                    "gpvs_detailed_margin": "",
                    "gpvs_detailed_status_ko": "추론불가",
                    "gpvs_detailed_reason_ko": f"model_source={model_source}; {feature_error}",
                }
            )
            continue

        proba = model.predict_proba(feature_df)[0]
        classes = [str(item) for item in model.classes_]
        ranking = sorted(zip(classes, proba), key=lambda item: item[1], reverse=True)
        top1_label, top1_score = ranking[0]
        if len(ranking) > 1:
            top2_label, top2_score = ranking[1]
        else:
            top2_label, top2_score = "", np.nan
        margin = float(top1_score - top2_score) if np.isfinite(top2_score) else float(top1_score)
        top2_score_text = f"{top2_score:.6g}" if np.isfinite(top2_score) else "nan"

        if float(top1_score) < AUDIT_TOP1_MIN_PROBA or margin < AUDIT_MIN_MARGIN:
            status = "판정유보"
            reason = (
                f"model_source={model_source}; fallback multiclass margin rule 적용; "
                f"top1={top1_label}:{top1_score:.6g}; top2={top2_label or '<none>'}:{top2_score_text}"
            )
        else:
            status = "추론성공"
            reason = (
                f"model_source={model_source}; top1={top1_label}:{top1_score:.6g}; "
                f"top2={top2_label or '<none>'}:{top2_score_text}"
            )

        audit_rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "event_reference_date": reference_date,
                "gpvs_detailed_model_source": model_source,
                "gpvs_family_label": gpvs_family_label,
                "gpvs_detailed_top1_fault_type": top1_label,
                "gpvs_detailed_top1_score": float(top1_score),
                "gpvs_detailed_top2_fault_type": top2_label,
                "gpvs_detailed_top2_score": float(top2_score) if np.isfinite(top2_score) else "",
                "gpvs_detailed_margin": margin,
                "gpvs_detailed_status_ko": status,
                "gpvs_detailed_reason_ko": reason,
            }
        )

    audit_df = pd.DataFrame(audit_rows).reindex(columns=AUDIT_COLS)
    if len(audit_df) != 6:
        raise SystemExit(f"{OUTPUT_AUDIT_NAME} must contain exactly 6 fault-panel rows, found {len(audit_df)}")
    if audit_df.duplicated(subset=["site", "panel_id"]).any():
        raise SystemExit(f"{OUTPUT_AUDIT_NAME} must be unique by (site, panel_id)")

    success_count = int(audit_df["gpvs_detailed_status_ko"].eq("추론성공").sum())
    abstain_count = int(audit_df["gpvs_detailed_status_ko"].eq("판정유보").sum())
    unavailable_count = int(audit_df["gpvs_detailed_status_ko"].eq("추론불가").sum())
    unique_real_top1_count = int(audit_df["gpvs_detailed_top1_fault_type"].map(normalize_text).replace("", np.nan).nunique(dropna=True))
    summary_df = pd.DataFrame(
        [
            {
                "fault_panel_count": int(len(audit_df)),
                "inference_success_count": success_count,
                "abstain_count": abstain_count,
                "inference_unavailable_count": unavailable_count,
                "note_ko": (
                    "이 파일은 audit-only real-panel GPVS by-type inference 결과다. "
                    "PVFAULT_labels_day.csv 는 synthetic-string keyed 라 real UUID panel bridge source로 쓰지 않았다. "
                    "recovered export artifact 가 있으면 그것을 우선 사용하고, 없으면 data/gpvs/out/gpvs_window_scores.csv 기반 fallback_lr surrogate 를 사용한다. "
                    f"현재 model_source={model_source}. "
                    "repo 안에 explicit abstain rule이 없으면 이 audit 파일에서만 top1 probability / top2 margin 기반 투명한 판정유보 flag를 쓴다. "
                    f"현재 real-panel top1 unique fault_type count={unique_real_top1_count}. "
                    "GPVS family result와 GPVS detailed fault result는 서로 다른 layer다. "
                    "label distribution / grouped CV / real-panel sanity output 을 함께 봐야 attach 가능성을 판단할 수 있다."
                ),
            }
        ]
    ).reindex(columns=SUMMARY_COLS)
    realpanel_sanity_df = build_realpanel_sanity_df(audit_df, cv_summary_df)
    return audit_df, summary_df, label_distribution_df, cv_summary_df, realpanel_sanity_df


def write_outputs(
    root: Path,
    audit_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    label_distribution_df: pd.DataFrame,
    cv_summary_df: pd.DataFrame,
    realpanel_sanity_df: pd.DataFrame,
) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    audit_df.to_csv(share_dir / OUTPUT_AUDIT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(share_dir / OUTPUT_SUMMARY_NAME, index=False, encoding="utf-8-sig")
    label_distribution_df.to_csv(share_dir / OUTPUT_LABEL_DISTRIBUTION_NAME, index=False, encoding="utf-8-sig")
    cv_summary_df.to_csv(share_dir / OUTPUT_CV_SUMMARY_NAME, index=False, encoding="utf-8-sig")
    realpanel_sanity_df.to_csv(share_dir / OUTPUT_REALPANEL_SANITY_NAME, index=False, encoding="utf-8-sig")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    audit_df, summary_df, label_distribution_df, cv_summary_df, realpanel_sanity_df = infer_rows(root)
    write_outputs(root, audit_df, summary_df, label_distribution_df, cv_summary_df, realpanel_sanity_df)


if __name__ == "__main__":
    main()
