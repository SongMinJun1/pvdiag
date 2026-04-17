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


OUTPUTS = [
    "panel_day_engine_gpvs_mlpe_feature_compatibility_v1.csv",
    "panel_day_engine_gpvs_mlpe_distribution_shift_v1.csv",
    "panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv",
    "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv",
    "panel_day_engine_gpvs_mlpe_compatibility_note_v1.md",
]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_training_rows(rows: list[dict[str, object]], fault_type: str, source_id: str, center: tuple[float, float, float, float, float]) -> None:
    offsets = [-0.04, -0.02, 0.00, 0.02, 0.04]
    for idx, offset in enumerate(offsets):
        rows.append(
            {
                "sample_id": f"{fault_type}::{idx}",
                "source_id": source_id,
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
                "i_pv_mean": 10 + idx,
                "p_pv_mean": 1000 + idx,
                "level_drop_raw": center[0] + offset,
                "v_drop_raw": center[1] + offset,
                "dtw_raw": center[2] + offset,
                "hs_raw": center[3] + offset,
                "ae_raw": center[4] + offset,
                "level_drop_like": 0.0,
                "v_drop_like": 0.0,
                "dtw_like": 0.0,
                "hs_like": 0.0,
                "ae_like": 0.0,
            }
        )


def add_panel_core_row(rows: list[dict[str, object]], panel_id: str, date: str, raw_tuple: tuple[float, float, float, float, float]) -> None:
    level_drop_raw, v_drop_raw, dtw_raw, hs_raw, ae_raw = raw_tuple
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
        {"site": "siteA", "panel_id": "panel_f4_1", "strict_trigger_date": "2025-01-10", "first_final_fault_date": "", "사건유형_재판정_ko": "전조형 고장", "최종고장양상_재판정_ko": "진행성 악화"},
        {"site": "siteA", "panel_id": "panel_f2_1", "strict_trigger_date": "2025-01-10", "first_final_fault_date": "", "사건유형_재판정_ko": "전조형 고장", "최종고장양상_재판정_ko": "급격 종료"},
        {"site": "siteA", "panel_id": "panel_f2_2", "strict_trigger_date": "2025-01-10", "first_final_fault_date": "", "사건유형_재판정_ko": "급작 고장", "최종고장양상_재판정_ko": "급작 발생"},
        {"site": "siteA", "panel_id": "panel_f2_3", "strict_trigger_date": "2025-01-10", "first_final_fault_date": "", "사건유형_재판정_ko": "급작 고장", "최종고장양상_재판정_ko": "급작 발생"},
        {"site": "siteA", "panel_id": "panel_f4_2", "strict_trigger_date": "2025-01-10", "first_final_fault_date": "", "사건유형_재판정_ko": "급작 고장", "최종고장양상_재판정_ko": "급작 발생"},
        {"site": "siteA", "panel_id": "panel_f2_4", "strict_trigger_date": "2025-01-10", "first_final_fault_date": "", "사건유형_재판정_ko": "전조형 고장", "최종고장양상_재판정_ko": "진행성 악화"},
    ]
    write_csv(
        share / "panel_day_engine_fault_panel_event_audit_v1.csv",
        fault_rows,
        ["site", "panel_id", "strict_trigger_date", "first_final_fault_date", "사건유형_재판정_ko", "최종고장양상_재판정_ko"],
    )

    verdict_rows = [
        {"site": "siteA", "panel_id": "panel_f4_1", "패널고장여부_ko": "고장", "사건유형_ko": "전조형 고장", "최종고장양상_ko": "진행성 악화", "커널로그_원인군_ko": "다이오드형", "GPVS_내부참고유형_ko": "전기적 고장 계열", "GPVS_외부참조패턴_ko": "패널·어레이 mismatch 참조"},
        {"site": "siteA", "panel_id": "panel_f2_1", "패널고장여부_ko": "고장", "사건유형_ko": "전조형 고장", "최종고장양상_ko": "급격 종료", "커널로그_원인군_ko": "개방/장치이상형", "GPVS_내부참고유형_ko": "개방/장치이상 계열", "GPVS_외부참조패턴_ko": "제어·계측 이상 힌트"},
        {"site": "siteA", "panel_id": "panel_f2_2", "패널고장여부_ko": "고장", "사건유형_ko": "급작 고장", "최종고장양상_ko": "급작 발생", "커널로그_원인군_ko": "다이오드형", "GPVS_내부참고유형_ko": "전기적 고장 계열", "GPVS_외부참조패턴_ko": "제어·계측 이상 힌트"},
        {"site": "siteA", "panel_id": "panel_f2_3", "패널고장여부_ko": "고장", "사건유형_ko": "급작 고장", "최종고장양상_ko": "급작 발생", "커널로그_원인군_ko": "다이오드형", "GPVS_내부참고유형_ko": "전기적 고장 계열", "GPVS_외부참조패턴_ko": "제어·계측 이상 힌트"},
        {"site": "siteA", "panel_id": "panel_f4_2", "패널고장여부_ko": "고장", "사건유형_ko": "급작 고장", "최종고장양상_ko": "급작 발생", "커널로그_원인군_ko": "다이오드형", "GPVS_내부참고유형_ko": "불확실", "GPVS_외부참조패턴_ko": "패널·어레이 mismatch 참조"},
        {"site": "siteA", "panel_id": "panel_f2_4", "패널고장여부_ko": "고장", "사건유형_ko": "전조형 고장", "최종고장양상_ko": "진행성 악화", "커널로그_원인군_ko": "모듈손상형", "GPVS_내부참고유형_ko": "전기적 고장 계열", "GPVS_외부참조패턴_ko": "제어·계측 이상 힌트"},
    ]
    write_csv(
        share / "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        verdict_rows,
        ["site", "panel_id", "패널고장여부_ko", "사건유형_ko", "최종고장양상_ko", "커널로그_원인군_ko", "GPVS_내부참고유형_ko", "GPVS_외부참조패턴_ko"],
    )

    detailed_rows = [
        {"site": "siteA", "panel_id": "panel_f4_1", "event_reference_date": "2025-01-10", "gpvs_family_label": "전기적 고장 계열", "gpvs_detailed_model_source": "recovered_artifact", "gpvs_detailed_top1_fault_type": "F4L", "gpvs_detailed_top1_score": 0.90, "gpvs_detailed_top2_fault_type": "F2M", "gpvs_detailed_top2_score": 0.10, "gpvs_detailed_margin": 0.80, "gpvs_detailed_status_ko": "추론성공"},
        {"site": "siteA", "panel_id": "panel_f2_1", "event_reference_date": "2025-01-10", "gpvs_family_label": "개방/장치이상 계열", "gpvs_detailed_model_source": "recovered_artifact", "gpvs_detailed_top1_fault_type": "F2M", "gpvs_detailed_top1_score": 0.95, "gpvs_detailed_top2_fault_type": "F4L", "gpvs_detailed_top2_score": 0.05, "gpvs_detailed_margin": 0.90, "gpvs_detailed_status_ko": "추론성공"},
        {"site": "siteA", "panel_id": "panel_f2_2", "event_reference_date": "2025-01-10", "gpvs_family_label": "전기적 고장 계열", "gpvs_detailed_model_source": "recovered_artifact", "gpvs_detailed_top1_fault_type": "F2M", "gpvs_detailed_top1_score": 0.94, "gpvs_detailed_top2_fault_type": "F4L", "gpvs_detailed_top2_score": 0.06, "gpvs_detailed_margin": 0.88, "gpvs_detailed_status_ko": "추론성공"},
        {"site": "siteA", "panel_id": "panel_f2_3", "event_reference_date": "2025-01-10", "gpvs_family_label": "전기적 고장 계열", "gpvs_detailed_model_source": "recovered_artifact", "gpvs_detailed_top1_fault_type": "F2M", "gpvs_detailed_top1_score": 0.93, "gpvs_detailed_top2_fault_type": "F4L", "gpvs_detailed_top2_score": 0.07, "gpvs_detailed_margin": 0.86, "gpvs_detailed_status_ko": "추론성공"},
        {"site": "siteA", "panel_id": "panel_f4_2", "event_reference_date": "2025-01-10", "gpvs_family_label": "불확실", "gpvs_detailed_model_source": "recovered_artifact", "gpvs_detailed_top1_fault_type": "F4L", "gpvs_detailed_top1_score": 0.89, "gpvs_detailed_top2_fault_type": "F2M", "gpvs_detailed_top2_score": 0.11, "gpvs_detailed_margin": 0.78, "gpvs_detailed_status_ko": "추론성공"},
        {"site": "siteA", "panel_id": "panel_f2_4", "event_reference_date": "2025-01-10", "gpvs_family_label": "전기적 고장 계열", "gpvs_detailed_model_source": "recovered_artifact", "gpvs_detailed_top1_fault_type": "F2M", "gpvs_detailed_top1_score": 0.92, "gpvs_detailed_top2_fault_type": "F4L", "gpvs_detailed_top2_score": 0.08, "gpvs_detailed_margin": 0.84, "gpvs_detailed_status_ko": "추론성공"},
    ]
    write_csv(
        share / "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv",
        detailed_rows,
        [
            "site",
            "panel_id",
            "event_reference_date",
            "gpvs_family_label",
            "gpvs_detailed_model_source",
            "gpvs_detailed_top1_fault_type",
            "gpvs_detailed_top1_score",
            "gpvs_detailed_top2_fault_type",
            "gpvs_detailed_top2_score",
            "gpvs_detailed_margin",
            "gpvs_detailed_status_ko",
        ],
    )

    write_csv(
        share / "panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv",
        [
            {
                "recovered_model_exported_flag": 1,
                "recovered_feature_manifest_exported_flag": 1,
                "recovered_model_source_ko": "fixture recovered path",
                "parity_overall_status_ko": "일치",
                "current_recovered_attachable_flag": 1,
                "note_ko": "fixture",
            }
        ],
        [
            "recovered_model_exported_flag",
            "recovered_feature_manifest_exported_flag",
            "recovered_model_source_ko",
            "parity_overall_status_ko",
            "current_recovered_attachable_flag",
            "note_ko",
        ],
    )

    training_rows: list[dict[str, object]] = []
    add_training_rows(training_rows, "F2M", "src_f2m", (0.12, 0.10, 0.18, 0.72, 0.18))
    add_training_rows(training_rows, "F4L", "src_f4l", (0.68, 0.70, 0.62, 0.22, 0.20))
    add_training_rows(training_rows, "F1L", "src_f1l", (0.35, 0.30, 0.30, 0.30, 0.78))
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
            "dtw_raw",
            "hs_raw",
            "ae_raw",
            "level_drop_like",
            "v_drop_like",
            "dtw_like",
            "hs_like",
            "ae_like",
        ],
    )

    feature_cols = ["level_drop_raw", "v_drop_raw", "dtw_raw", "hs_raw", "ae_raw"]
    training_df = pd.read_csv(gpvs_out / "gpvs_window_scores.csv", low_memory=False, encoding="utf-8-sig")
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
                "training_script_path": "research/prognostics/gpvs_train_supervised.py",
                "recovered_model_source_ko": "fixture recovered artifact",
                "feature_set": "fixture_raw_only",
                "kept_features": feature_cols,
                "removed_zero_var": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    panel_core_rows: list[dict[str, object]] = []
    add_panel_core_row(panel_core_rows, "panel_f4_1", "2025-01-10", (1.30, 1.25, 1.05, 0.35, 0.28))
    add_panel_core_row(panel_core_rows, "panel_f2_1", "2025-01-10", (0.18, 0.15, 0.22, 1.40, 0.30))
    add_panel_core_row(panel_core_rows, "panel_f2_2", "2025-01-10", (0.16, 0.18, 0.18, 1.30, 0.22))
    add_panel_core_row(panel_core_rows, "panel_f2_3", "2025-01-10", (0.15, 0.17, 0.20, 1.35, 0.24))
    add_panel_core_row(panel_core_rows, "panel_f4_2", "2025-01-10", (1.22, 1.18, 1.00, 0.32, 0.21))
    add_panel_core_row(panel_core_rows, "panel_f2_4", "2025-01-10", (0.14, 0.15, 0.21, 1.25, 0.20))
    write_csv(
        site_a_out / "panel_day_core.csv",
        panel_core_rows,
        ["date", "panel_id", "mid_ratio", "v_drop", "dtw_dist", "hs_score", "recon_error"],
    )


def main() -> None:
    repo_root = REPO_ROOT
    build_script = repo_root / "research/prognostics/build_panel_day_engine_gpvs_mlpe_compatibility_audit_v1.py"
    smoke_script = repo_root / "research/prognostics/smoke_test_panel_day_engine_gpvs_mlpe_compatibility_audit_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        repo_root / "_share/panel_day_engine_panel_multiaxis_verdict_v1.csv",
        repo_root / "_share/panel_day_engine_project_handoff_pack_v1.md",
        repo_root / "_share/panel_day_engine_project_closeout_pack_v1.md",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="gpvs_mlpe_compatibility_audit_smoke_") as tmp_dir:
        root = Path(tmp_dir)
        build_fixture(root)
        result = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        if result.returncode != 0:
            raise SystemExit(f"build failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
        combined_output = f"{result.stdout}\n{result.stderr}"
        assert_true("missing columns" not in combined_output, "current simplified verdict schema should not trigger missing columns path")

        for output_name in OUTPUTS:
            output_path = root / "_share" / output_name
            assert_true(output_path.exists(), f"missing output: {output_name}")

        feature_df = pd.read_csv(root / "_share" / OUTPUTS[0], low_memory=False, encoding="utf-8-sig")
        distribution_df = pd.read_csv(root / "_share" / OUTPUTS[1], low_memory=False, encoding="utf-8-sig")
        agreement_df = pd.read_csv(root / "_share" / OUTPUTS[2], low_memory=False, encoding="utf-8-sig")
        summary_df = pd.read_csv(root / "_share" / OUTPUTS[3], low_memory=False, encoding="utf-8-sig")
        note_text = (root / "_share" / OUTPUTS[4]).read_text(encoding="utf-8")
        summary_row = summary_df.iloc[0]

        assert_true(not feature_df.empty, "feature compatibility output must not be empty")
        assert_true(len(distribution_df) == 6, "distribution shift output must contain 6 fault panels")
        assert_true(len(agreement_df) == 6, "panel agreement output must contain 6 fault panels")
        assert_true(int(summary_row["fault_panel_count"]) == 6, "summary fault_panel_count must equal 6")
        assert_true(str(summary_row["final_recommendation_ko"]).strip() != "", "final_recommendation_ko must be populated")
        assert_true(int(summary_row["family_alignment_count"]) == 4, "family_alignment_count must stay 4")
        assert_true(int(summary_row["family_partial_alignment_count"]) == 1, "family_partial_alignment_count must stay 1")
        assert_true(int(summary_row["family_conflict_count"]) == 0, "family_conflict_count must stay 0")
        assert_true(int(summary_row["scenario_partial_alignment_count"]) == 2, "scenario_partial_alignment_count must stay 2")
        assert_true(int(summary_row["scenario_conflict_count"]) == 4, "scenario_conflict_count must stay 4")
        assert_true(int(summary_row["gpvs_reference_caution_count"]) == 2, "caution count must stay 2")
        assert_true(int(summary_row["gpvs_reference_not_recommended_count"]) == 4, "not recommended count must stay 4")
        scenario_map = {
            (str(row["site"]).strip(), str(row["panel_id"]).strip()): str(row["GPVS_외부참조시나리오명_ko"]).strip()
            for row in agreement_df.to_dict(orient="records")
        }
        assert_true(
            scenario_map[("siteA", "panel_f4_1")] == "PV 어레이 mismatch(부분 음영) 시나리오",
            "F4 scenario name should resolve from detailed provenance under simplified verdict schema",
        )
        assert_true(
            scenario_map[("siteA", "panel_f2_1")] == "제어 피드백 센서 이상 시나리오",
            "F2 scenario name should resolve from detailed provenance under simplified verdict schema",
        )
        assert_true(
            "GPVS original scenario space and MLPE official problem-type space are not identical" in note_text,
            "note must explain GPVS/MLPE label-space difference",
        )

    after = {path: file_digest(path) for path in official_outputs}
    for path in official_outputs:
        assert_true(before[path] == after[path], f"official output changed unexpectedly: {path}")


if __name__ == "__main__":
    main()
