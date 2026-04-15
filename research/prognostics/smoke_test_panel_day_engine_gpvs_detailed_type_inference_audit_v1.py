#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import joblib
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.prognostics.build_panel_day_engine_gpvs_detailed_type_inference_audit_v1 import (  # noqa: E402
    build_realpanel_sanity_df,
)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_training_rows(rows: list[dict[str, object]], fault_type: str, center: tuple[float, float, float, float, float]) -> None:
    offsets = [-0.08, -0.04, 0.0, 0.04, 0.08]
    for idx, offset in enumerate(offsets):
        rows.append(
            {
                "sample_id": f"{fault_type}::w{idx:03d}",
                "source_id": fault_type,
                "window_idx": idx,
                "window_ord": idx,
                "n_windows": len(offsets),
                "t0": "1970-01-01 00:00:00",
                "t1": "1970-01-01 00:00:00",
                "label_fault": 1,
                "is_fault_window": 1,
                "fault_sid": 1,
                "fault_mode": fault_type[-1],
                "fault_type": fault_type,
                "is_fault_file": 1,
                "v_pv_mean": 100 + idx,
                "i_pv_mean": 1.0 + idx * 0.01,
                "p_pv_mean": 140 + idx,
                "level_drop_raw": center[0] + offset,
                "v_drop_raw": center[1] + offset,
                "hs_raw": center[2] + offset,
                "dtw_raw": center[3] + offset,
                "ae_raw": center[4] + offset,
                "level_drop_like": 0.0,
                "v_drop_like": 0.0,
                "hs_like": 0.0,
                "dtw_like": 0.0,
                "ae_like": 0.0,
            }
        )


def add_panel_core_row(rows: list[dict[str, object]], panel_id: str, date: str, feature_tuple: tuple[float, float, float, float, float]) -> None:
    level_drop_raw, v_drop_raw, hs_raw, dtw_raw, ae_raw = feature_tuple
    rows.append(
        {
            "date": date,
            "panel_id": panel_id,
            "mid_ratio": 1.0 - level_drop_raw,
            "v_drop": v_drop_raw,
            "dtw_dist": dtw_raw,
            "hs_score": hs_raw,
            "recon_error": ae_raw,
        }
    )


def build_fixture(root: Path) -> None:
    share = root / "_share"
    gpvs_out = root / "data" / "gpvs" / "out"
    site_a_out = root / "data" / "siteA" / "out"
    share.mkdir(parents=True, exist_ok=True)
    gpvs_out.mkdir(parents=True, exist_ok=True)
    site_a_out.mkdir(parents=True, exist_ok=True)

    fault_rows = [
        {"site": "siteA", "panel_id": "panel_success_1", "strict_trigger_date": "2025-01-10", "first_final_fault_date": ""},
        {"site": "siteA", "panel_id": "panel_success_2", "strict_trigger_date": "2025-01-10", "first_final_fault_date": ""},
        {"site": "siteA", "panel_id": "panel_abstain_1", "strict_trigger_date": "2025-01-10", "first_final_fault_date": ""},
        {"site": "siteA", "panel_id": "panel_abstain_2", "strict_trigger_date": "2025-01-10", "first_final_fault_date": ""},
        {"site": "siteA", "panel_id": "panel_unavailable_1", "strict_trigger_date": "2025-01-10", "first_final_fault_date": ""},
        {"site": "siteA", "panel_id": "panel_unavailable_2", "strict_trigger_date": "2025-01-10", "first_final_fault_date": ""},
    ]
    write_csv(
        share / "panel_day_engine_fault_panel_event_audit_v1.csv",
        fault_rows,
        ["site", "panel_id", "strict_trigger_date", "first_final_fault_date"],
    )

    verdict_rows = [
        {"site": "siteA", "panel_id": "panel_success_1", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "전기적 고장 계열"},
        {"site": "siteA", "panel_id": "panel_success_2", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "전압 변화 계열"},
        {"site": "siteA", "panel_id": "panel_abstain_1", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "전기적 고장 계열"},
        {"site": "siteA", "panel_id": "panel_abstain_2", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "전압 변화 계열"},
        {"site": "siteA", "panel_id": "panel_unavailable_1", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "전기적 고장 계열"},
        {"site": "siteA", "panel_id": "panel_unavailable_2", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "전압 변화 계열"},
    ]
    write_csv(
        share / "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        verdict_rows,
        ["site", "panel_id", "패널고장여부_ko", "GPVS_참고유형_ko"],
    )

    training_rows: list[dict[str, object]] = []
    add_training_rows(training_rows, "F1L", (0.85, 0.80, 0.10, 0.10, 0.10))
    add_training_rows(training_rows, "F2L", (0.10, 0.10, 0.90, 0.90, 0.10))
    add_training_rows(training_rows, "F3L", (0.10, 0.10, 0.10, 0.10, 0.90))
    write_csv(
        gpvs_out / "gpvs_window_scores.csv",
        training_rows,
        [
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
            "v_pv_mean",
            "i_pv_mean",
            "p_pv_mean",
            "level_drop_raw",
            "v_drop_raw",
            "hs_raw",
            "dtw_raw",
            "ae_raw",
            "level_drop_like",
            "v_drop_like",
            "hs_like",
            "dtw_like",
            "ae_like",
        ],
    )

    write_csv(
        gpvs_out / "EXTERNAL_GPVS_BYTYPE_METRICS.csv",
        [
            {"fault_type": "F1L", "sid": 1, "score": "level_drop_like", "threshold_fpr1": 0.5, "ap": 0.8, "roc_auc": 0.8},
            {"fault_type": "F2L", "sid": 2, "score": "hs_like", "threshold_fpr1": 0.5, "ap": 0.8, "roc_auc": 0.8},
            {"fault_type": "F3L", "sid": 3, "score": "ae_like", "threshold_fpr1": 0.5, "ap": 0.8, "roc_auc": 0.8},
        ],
        ["fault_type", "sid", "score", "threshold_fpr1", "ap", "roc_auc"],
    )

    panel_core_rows: list[dict[str, object]] = []
    add_panel_core_row(panel_core_rows, "panel_success_1", "2025-01-10", (0.88, 0.84, 0.12, 0.12, 0.11))
    add_panel_core_row(panel_core_rows, "panel_success_2", "2025-01-10", (0.11, 0.10, 0.95, 0.93, 0.10))
    add_panel_core_row(panel_core_rows, "panel_abstain_1", "2025-01-10", (0.48, 0.46, 0.52, 0.50, 0.10))
    add_panel_core_row(panel_core_rows, "panel_abstain_2", "2025-01-10", (0.12, 0.11, 0.48, 0.45, 0.45))
    add_panel_core_row(panel_core_rows, "panel_unavailable_1", "2025-01-09", (0.80, 0.78, 0.10, 0.10, 0.10))
    write_csv(
        site_a_out / "panel_day_core.csv",
        panel_core_rows,
        ["date", "panel_id", "mid_ratio", "v_drop", "dtw_dist", "hs_score", "recon_error"],
    )


def build_recovered_artifact(root: Path) -> None:
    gpvs_out = root / "data" / "gpvs" / "out"
    training_df = pd.read_csv(gpvs_out / "gpvs_window_scores.csv", low_memory=False, encoding="utf-8-sig")
    feature_cols = ["level_drop_raw", "v_drop_raw", "hs_raw", "dtw_raw", "ae_raw"]
    X = training_df[feature_cols].apply(pd.to_numeric, errors="coerce")
    y = training_df["fault_type"].astype(str)
    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, random_state=42, class_weight="balanced")),
        ]
    )
    model.fit(X, y)
    joblib.dump(
        {
            "model": model,
            "feature_cols": feature_cols,
            "model_source": "fixture_recovered_artifact",
        },
        gpvs_out / "gpvs_bytype_recovered_model_v1.joblib",
    )
    (gpvs_out / "gpvs_bytype_recovered_feature_manifest_v1.json").write_text(
        json.dumps(
            {
                "feature_set": "fixture_feature_set",
                "kept_features": feature_cols,
                "recovered_model_source_ko": "fixture recovered artifact",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    repo_root = REPO_ROOT
    build_script = repo_root / "research/prognostics/build_panel_day_engine_gpvs_detailed_type_inference_audit_v1.py"
    smoke_script = repo_root / "research/prognostics/smoke_test_panel_day_engine_gpvs_detailed_type_inference_audit_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        repo_root / "_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv",
        repo_root / "_share/panel_day_engine_gpvs_detailed_type_inference_summary_v1.csv",
        repo_root / "_share/panel_day_engine_gpvs_detailed_type_label_distribution_v1.csv",
        repo_root / "_share/panel_day_engine_gpvs_detailed_type_cv_summary_v1.csv",
        repo_root / "_share/panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="gpvs_detailed_type_inference_audit_smoke_") as tmp_dir:
        root = Path(tmp_dir)
        build_fixture(root)
        assert_true(not any(root.rglob("PVFAULT_labels_day.csv")), "synthetic PVFAULT bridge source must not exist in this audit fixture")

        result = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(result.returncode == 0, f"builder failed: {result.stderr or result.stdout}")

        audit_path = root / "_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv"
        summary_path = root / "_share/panel_day_engine_gpvs_detailed_type_inference_summary_v1.csv"
        label_distribution_path = root / "_share/panel_day_engine_gpvs_detailed_type_label_distribution_v1.csv"
        cv_summary_path = root / "_share/panel_day_engine_gpvs_detailed_type_cv_summary_v1.csv"
        realpanel_sanity_path = root / "_share/panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv"
        assert_true(audit_path.exists(), "missing gpvs detailed-type audit output")
        assert_true(summary_path.exists(), "missing gpvs detailed-type summary output")
        assert_true(label_distribution_path.exists(), "missing label distribution audit output")
        assert_true(cv_summary_path.exists(), "missing grouped CV audit output")
        assert_true(realpanel_sanity_path.exists(), "missing real-panel sanity audit output")

        audit_df = pd.read_csv(audit_path, low_memory=False, encoding="utf-8-sig")
        summary_df = pd.read_csv(summary_path, low_memory=False, encoding="utf-8-sig")
        label_distribution_df = pd.read_csv(label_distribution_path, low_memory=False, encoding="utf-8-sig")
        cv_summary_df = pd.read_csv(cv_summary_path, low_memory=False, encoding="utf-8-sig")
        realpanel_sanity_df = pd.read_csv(realpanel_sanity_path, low_memory=False, encoding="utf-8-sig")

        assert_true(len(audit_df) == 6, f"fault panel count must be 6, found {len(audit_df)}")
        assert_true(not audit_df.duplicated(subset=["site", "panel_id"]).any(), "audit output must be unique by (site, panel_id)")

        success_count = int(audit_df["gpvs_detailed_status_ko"].eq("추론성공").sum())
        abstain_count = int(audit_df["gpvs_detailed_status_ko"].eq("판정유보").sum())
        unavailable_count = int(audit_df["gpvs_detailed_status_ko"].eq("추론불가").sum())
        assert_true(success_count >= 1, "audit should materialize at least one success path in fixture")
        assert_true(abstain_count >= 1, "audit should materialize at least one abstain path in fixture")
        assert_true(unavailable_count >= 1, "audit should materialize at least one unavailable path in fixture")

        success_row = audit_df.loc[audit_df["panel_id"].eq("panel_success_1")].iloc[0]
        abstain_row = audit_df.loc[audit_df["panel_id"].eq("panel_abstain_1")].iloc[0]
        unavailable_row = audit_df.loc[audit_df["panel_id"].eq("panel_unavailable_1")].iloc[0]

        assert_true(success_row["gpvs_detailed_status_ko"] == "추론성공", "success fixture row should infer successfully")
        assert_true(normalize_text(success_row["gpvs_detailed_top1_fault_type"]) != "", "success row must keep top1 label")
        assert_true(float(success_row["gpvs_detailed_top1_score"]) > 0, "success row must keep positive top1 score")
        assert_true(abstain_row["gpvs_detailed_status_ko"] == "판정유보", "abstain fixture row should abstain")
        assert_true("margin rule" in str(abstain_row["gpvs_detailed_reason_ko"]), "abstain reason should explain margin rule")
        assert_true(unavailable_row["gpvs_detailed_status_ko"] == "추론불가", "unavailable fixture row should stay unavailable")
        assert_true(
            "일치하는 real-panel GPVS feature row 없음" in str(unavailable_row["gpvs_detailed_reason_ko"])
            or "재구성할 수 없는 feature" in str(unavailable_row["gpvs_detailed_reason_ko"]),
            "unavailable reason should explain missing feature join path",
        )

        summary_row = summary_df.iloc[0]
        assert_true(int(summary_row["fault_panel_count"]) == 6, "summary fault panel count mismatch")
        assert_true(int(summary_row["inference_success_count"]) == success_count, "summary success count mismatch")
        assert_true(int(summary_row["abstain_count"]) == abstain_count, "summary abstain count mismatch")
        assert_true(int(summary_row["inference_unavailable_count"]) == unavailable_count, "summary unavailable count mismatch")
        assert_true("PVFAULT_labels_day.csv 는 synthetic-string keyed" in str(summary_row["note_ko"]), "summary note should explain PVFAULT bridge exclusion")
        assert_true("audit-only" in str(summary_row["note_ko"]), "summary note should explain audit-only semantics")
        assert_true("model_source=fallback_lr" in str(summary_row["note_ko"]), "fallback path should be explicit when recovered artifact is absent")

        assert_true({"fault_type", "train_window_count", "train_source_count"} <= set(label_distribution_df.columns), "label distribution columns missing")
        assert_true(len(label_distribution_df) == 3, "fixture label distribution should expose three training fault types")
        assert_true(int(label_distribution_df["train_window_count"].sum()) == 15, "fixture train window count should sum to 15")
        assert_true(int(label_distribution_df["train_source_count"].sum()) == 3, "fixture train source count should sum to 3")

        assert_true({"cv_fold", "macro_recall", "macro_f1", "top1_accuracy", "unique_predicted_fault_type_count"} <= set(cv_summary_df.columns), "CV summary columns missing")
        assert_true(cv_summary_df["cv_fold"].map(str).eq("summary").any(), "CV summary must contain a summary row")
        assert_true(cv_summary_df["cv_fold"].map(str).ne("summary").any(), "CV summary must contain per-fold rows")

        assert_true(len(realpanel_sanity_df) == 6, "real-panel sanity output must contain 6 rows")
        assert_true({"single_type_collapse_flag", "attach_recommendation_ko"} <= set(realpanel_sanity_df.columns), "real-panel sanity columns missing")
        assert_true(realpanel_sanity_df["single_type_collapse_flag"].fillna(0).eq(0).all(), "fixture real-panel predictions should not collapse to one type")

        collapse_fixture_df = pd.DataFrame(
            [
                {
                    "site": "siteA",
                    "panel_id": f"panel_{idx}",
                    "gpvs_family_label": "전기적 고장 계열",
                    "gpvs_detailed_top1_fault_type": "F4L",
                    "gpvs_detailed_top1_score": 0.81,
                    "gpvs_detailed_top2_fault_type": "F2L",
                    "gpvs_detailed_top2_score": 0.11,
                    "gpvs_detailed_margin": 0.70,
                    "gpvs_detailed_status_ko": "추론성공",
                }
                for idx in range(6)
            ]
        )
        collapse_cv_df = pd.DataFrame(
            [
                {
                    "cv_fold": "summary",
                    "cv_macro_recall_mean": 0.72,
                    "cv_macro_f1_mean": 0.68,
                    "cv_top1_accuracy_mean": 0.76,
                    "cv_unique_predicted_fault_type_count_mean": 3.0,
                }
            ]
        )
        collapse_sanity_df = build_realpanel_sanity_df(collapse_fixture_df, collapse_cv_df)
        assert_true(collapse_sanity_df["single_type_collapse_flag"].eq(1).all(), "single-type collapse fixture should be detected")
        assert_true(collapse_sanity_df["attach_recommendation_ko"].eq("do_not_attach").all(), "collapse fixture should force do_not_attach")

        build_recovered_artifact(root)
        result_recovered = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(result_recovered.returncode == 0, f"builder with recovered artifact failed: {result_recovered.stderr or result_recovered.stdout}")

        audit_df_recovered = pd.read_csv(audit_path, low_memory=False, encoding="utf-8-sig")
        summary_df_recovered = pd.read_csv(summary_path, low_memory=False, encoding="utf-8-sig")

        success_row_recovered = audit_df_recovered.loc[audit_df_recovered["panel_id"].eq("panel_success_1")].iloc[0]
        abstain_row_recovered = audit_df_recovered.loc[audit_df_recovered["panel_id"].eq("panel_abstain_1")].iloc[0]
        unavailable_row_recovered = audit_df_recovered.loc[audit_df_recovered["panel_id"].eq("panel_unavailable_1")].iloc[0]
        assert_true(success_row_recovered["gpvs_detailed_model_source"] == "recovered_artifact", "success row should prefer recovered artifact when present")
        assert_true(abstain_row_recovered["gpvs_detailed_model_source"] == "recovered_artifact", "abstain row should prefer recovered artifact when present")
        assert_true(unavailable_row_recovered["gpvs_detailed_model_source"] == "inference_unavailable", "unavailable row should keep inference_unavailable source")
        assert_true(
            "model_source=recovered_artifact" in str(summary_df_recovered.iloc[0]["note_ko"]),
            "summary note should expose recovered artifact model_source when present",
        )

    after = {path: file_digest(path) for path in official_outputs}
    assert_true(before == after, "official outputs changed during smoke test")


if __name__ == "__main__":
    main()
