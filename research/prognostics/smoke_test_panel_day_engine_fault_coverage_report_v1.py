#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    if str(Path(__file__).resolve().parents[2]) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from research.prognostics.smoke_frozen_share_fixture_v1 import stage_missing_share_fixtures
else:
    from .smoke_frozen_share_fixture_v1 import stage_missing_share_fixtures


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "research/prognostics/build_panel_day_engine_fault_coverage_report_v1.py"
SMOKE_SCRIPT = REPO_ROOT / "research/prognostics/smoke_test_panel_day_engine_fault_coverage_report_v1.py"

COVERAGE_REQUIRED_COLS = [
    "target_fault_or_anomaly_ko",
    "detection_signal_or_pattern_ko",
    "primary_layer_ko",
    "supporting_layers_csv",
    "key_features_or_patterns_ko",
    "final_output_field_ko",
    "coverage_level_ko",
    "note_ko",
]

METRIC_REQUIRED_COLS = [
    "layer_ko",
    "metric_family_ko",
    "metric_name",
    "metric_value",
    "dataset_scope_ko",
    "official_flag",
    "note_ko",
]

WATCH_FILENAMES = [
    "panel_day_engine_panel_multiaxis_verdict_v1.csv",
    "panel_day_engine_gpvs_evidence_pack_v1.csv",
    "panel_day_engine_cause_candidate_heuristics_v1.csv",
    "panel_day_engine_gpvs_evidence_summary_v1.csv",
    "panel_day_engine_cause_candidate_summary_v1.csv",
]

REQUIRED_COVERAGE_TARGETS = {
    "패널고장여부",
    "전조형 고장",
    "급작 고장",
    "진행성 악화",
    "급격 종료",
    "급작 발생",
    "conalog 다이오드형",
    "conalog 개방/장치이상형",
    "conalog 모듈손상형",
    "GPVS reference attach",
    "heuristic suspected-cause ranking",
}

REQUIRED_LAYERS = {
    "panel multiaxis verdict",
    "사건유형/고장양상 판단",
    "conalog 해석층",
    "GPVS reference layer",
    "cause candidate heuristic",
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def file_signature(path: Path) -> tuple[int, int] | None:
    if not path.exists():
        return None
    stat = path.stat()
    return (stat.st_size, stat.st_mtime_ns)


def main() -> None:
    py_compile.compile(str(REPO_ROOT / "pv_ae/panel_day_engine.py"), doraise=True)
    py_compile.compile(str(BUILD_SCRIPT), doraise=True)
    py_compile.compile(str(SMOKE_SCRIPT), doraise=True)
    with tempfile.TemporaryDirectory(prefix="fault_coverage_smoke_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        with stage_missing_share_fixtures(tmp_root, WATCH_FILENAMES):
            watch_outputs = [tmp_root / "_share" / name for name in WATCH_FILENAMES]
            before_signatures = {path: file_signature(path) for path in watch_outputs}

            result = subprocess.run(
                [sys.executable, str(BUILD_SCRIPT), "--root", str(tmp_root)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )
            assert_true(result.returncode == 0, f"build failed: {result.stderr or result.stdout}")

            output_coverage = tmp_root / "_share/panel_day_engine_fault_coverage_matrix_v1.csv"
            output_metrics = tmp_root / "_share/panel_day_engine_model_metrics_v1.csv"
            output_doc = tmp_root / "docs/OPS_FAULT_COVERAGE_AND_MODEL_PERFORMANCE_V1.md"
            assert_true(output_coverage.exists(), f"missing coverage output: {output_coverage}")
            assert_true(output_metrics.exists(), f"missing metrics output: {output_metrics}")
            assert_true(output_doc.exists(), f"missing report doc: {output_doc}")

            coverage_df = pd.read_csv(output_coverage, low_memory=False, encoding="utf-8-sig")
            metrics_df = pd.read_csv(output_metrics, low_memory=False, encoding="utf-8-sig")

            missing_coverage_cols = [column for column in COVERAGE_REQUIRED_COLS if column not in coverage_df.columns]
            assert_true(not missing_coverage_cols, f"coverage matrix missing columns: {missing_coverage_cols}")
            missing_metric_cols = [column for column in METRIC_REQUIRED_COLS if column not in metrics_df.columns]
            assert_true(not missing_metric_cols, f"model metrics missing columns: {missing_metric_cols}")

            coverage_targets = set(coverage_df["target_fault_or_anomaly_ko"].map(normalize_text).tolist())
            missing_targets = sorted(REQUIRED_COVERAGE_TARGETS - coverage_targets)
            assert_true(not missing_targets, f"coverage matrix missing required targets: {missing_targets}")

            coverage_levels = set(coverage_df["coverage_level_ko"].map(normalize_text).tolist())
            assert_true(coverage_levels.issubset({"직접커버", "보조커버", "보류", "미커버"}), f"unexpected coverage levels: {sorted(coverage_levels)}")
            assert_true(coverage_df["note_ko"].map(normalize_text).ne("").all(), "coverage matrix note_ko must be populated")

            layer_values = set(metrics_df["layer_ko"].map(normalize_text).tolist())
            missing_layers = sorted(REQUIRED_LAYERS - layer_values)
            assert_true(not missing_layers, f"metrics table missing required layers: {missing_layers}")
            assert_true(metrics_df["note_ko"].map(normalize_text).ne("").all(), "metrics table note_ko must be populated")
            assert_true(metrics_df["official_flag"].fillna(0).astype(int).isin([0, 1]).all(), "official_flag must stay binary")

            gpvs_rows = metrics_df.loc[metrics_df["layer_ko"].map(normalize_text).eq("GPVS reference layer")].copy()
            assert_true(len(gpvs_rows) >= 3, "expected at least 3 GPVS reference layer metric rows")

            doc_text = output_doc.read_text(encoding="utf-8")
            for token in [
                "1. 보고 목적",
                "2. 현재 알고리즘 스택",
                "3. 입력 데이터와 학습/참조 자산",
                "4. fault/anomaly 커버리지 1대1 매핑",
                "5. 레이어별 성능지표 원칙",
                "6. 현재 확보된 지표와 해석",
                "7. 현재 한계와 주의사항",
                "panel multiaxis verdict가 primary",
                "conalog는 direct operational interpretation layer",
                "GPVS는 reference-only",
                "heuristic은 triage-only",
                "25 panel / 6 fault",
            ]:
                assert_true(token in doc_text, f"report doc missing required text: {token}")

            after_signatures = {path: file_signature(path) for path in watch_outputs}
            for path in watch_outputs:
                assert_true(before_signatures[path] == after_signatures[path], f"frozen production output changed: {path}")


if __name__ == "__main__":
    main()
