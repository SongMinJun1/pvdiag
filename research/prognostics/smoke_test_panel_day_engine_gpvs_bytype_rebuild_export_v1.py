#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


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


def add_training_windows(rows: list[dict[str, object]], source_id: str, fault_type: str, is_fault_window: int, center: tuple[float, float, float, float, float]) -> None:
    offsets = [-0.05, -0.02, 0.0, 0.02, 0.05, 0.08]
    for idx, offset in enumerate(offsets):
        rows.append(
            {
                "source_id": source_id,
                "fault_type": fault_type,
                "is_fault_window": is_fault_window,
                "fault_sid": 0 if is_fault_window == 0 else 1,
                "is_fault_file": is_fault_window,
                "fault_mode": fault_type[-1],
                "window_ord": idx,
                "level_drop_raw": center[0] + offset,
                "v_drop_raw": center[1] + offset,
                "dtw_raw": center[2] + offset,
                "hs_raw": center[3] + offset,
                "ae_raw": center[4] + offset,
                "level_drop_like": center[0] + offset,
                "v_drop_like": center[1] + offset,
                "dtw_like": center[2] + offset,
                "hs_like": center[3] + offset,
                "ae_like": center[4] + offset,
            }
        )


def add_panel_history(rows: list[dict[str, object]], panel_id: str, centers: list[tuple[str, tuple[float, float, float, float, float]]]) -> None:
    for date, (level_drop, v_drop, dtw, hs, ae) in centers:
        rows.append(
            {
                "date": date,
                "panel_id": panel_id,
                "mid_ratio": 1.0 - level_drop,
                "v_drop": v_drop,
                "dtw_dist": dtw,
                "hs_score": hs,
                "recon_error": ae,
            }
        )


def build_fixture(root: Path) -> None:
    gpvs_out = root / "data" / "gpvs" / "out"
    site_out = root / "data" / "siteA" / "out"
    share = root / "_share"
    docs_reports = root / "docs" / "reports"

    gpvs_out.mkdir(parents=True, exist_ok=True)
    site_out.mkdir(parents=True, exist_ok=True)
    share.mkdir(parents=True, exist_ok=True)
    docs_reports.mkdir(parents=True, exist_ok=True)

    training_rows: list[dict[str, object]] = []
    add_training_windows(training_rows, "h1", "F0L", 0, (0.10, 0.10, 0.10, 0.10, 0.10))
    add_training_windows(training_rows, "h2", "F0L", 0, (0.12, 0.11, 0.12, 0.11, 0.12))
    add_training_windows(training_rows, "f1a", "F1L", 1, (0.80, 0.78, 0.15, 0.15, 0.15))
    add_training_windows(training_rows, "f1b", "F1L", 1, (0.82, 0.80, 0.18, 0.18, 0.16))
    add_training_windows(training_rows, "f2a", "F2L", 1, (0.12, 0.12, 0.82, 0.84, 0.18))
    add_training_windows(training_rows, "f2b", "F2L", 1, (0.14, 0.14, 0.80, 0.82, 0.20))
    add_training_windows(training_rows, "f4a", "F4L", 1, (0.18, 0.75, 0.18, 0.20, 0.82))
    add_training_windows(training_rows, "f4b", "F4L", 1, (0.20, 0.78, 0.16, 0.18, 0.84))
    write_csv(
        gpvs_out / "gpvs_window_scores.csv",
        training_rows,
        [
            "source_id",
            "fault_type",
            "is_fault_window",
            "fault_sid",
            "is_fault_file",
            "fault_mode",
            "window_ord",
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

    write_csv(
        gpvs_out / "EXTERNAL_GPVS_BYTYPE_METRICS.csv",
        [
            {"fault_type": "F1L", "sid": 1, "score": "level_drop_like", "ap": 0.7},
            {"fault_type": "F2L", "sid": 2, "score": "hs_like", "ap": 0.8},
            {"fault_type": "F4L", "sid": 4, "score": "ae_like", "ap": 0.6},
        ],
        ["fault_type", "sid", "score", "ap"],
    )

    (docs_reports / "gpvs_final_summary.md").write_text(
        "\n".join(
            [
                "# GPVS Final Summary",
                "### A. strict primary result",
                "- model: `LogisticRegression`",
                "- feature_set: `raw_no_norm_all`",
                "- split: `grouped_source`",
                "- roc_auc: ``",
                "- ap: ``",
                "- f1_best: ``",
                "- f1_fpr1: ``",
            ]
        ),
        encoding="utf-8",
    )

    fault_rows = [
        {"site": "siteA", "panel_id": "panel_f1_a", "strict_trigger_date": "2025-01-03", "first_final_fault_date": ""},
        {"site": "siteA", "panel_id": "panel_f1_b", "strict_trigger_date": "2025-01-03", "first_final_fault_date": ""},
        {"site": "siteA", "panel_id": "panel_f2_a", "strict_trigger_date": "2025-01-03", "first_final_fault_date": ""},
        {"site": "siteA", "panel_id": "panel_f2_b", "strict_trigger_date": "2025-01-03", "first_final_fault_date": ""},
        {"site": "siteA", "panel_id": "panel_f4_a", "strict_trigger_date": "2025-01-03", "first_final_fault_date": ""},
        {"site": "siteA", "panel_id": "panel_f4_b", "strict_trigger_date": "2025-01-03", "first_final_fault_date": ""},
    ]
    write_csv(
        share / "panel_day_engine_fault_panel_event_audit_v1.csv",
        fault_rows,
        ["site", "panel_id", "strict_trigger_date", "first_final_fault_date"],
    )

    verdict_rows = [
        {"site": "siteA", "panel_id": "panel_f1_a", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "전기적 고장 계열"},
        {"site": "siteA", "panel_id": "panel_f1_b", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "전기적 고장 계열"},
        {"site": "siteA", "panel_id": "panel_f2_a", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "전압 변화 계열"},
        {"site": "siteA", "panel_id": "panel_f2_b", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "전압 변화 계열"},
        {"site": "siteA", "panel_id": "panel_f4_a", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "개방/장치이상 계열"},
        {"site": "siteA", "panel_id": "panel_f4_b", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "개방/장치이상 계열"},
    ]
    write_csv(
        share / "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        verdict_rows,
        ["site", "panel_id", "패널고장여부_ko", "GPVS_참고유형_ko"],
    )

    panel_core_rows: list[dict[str, object]] = []
    add_panel_history(panel_core_rows, "panel_f1_a", [("2025-01-01", (0.55, 0.54, 0.16, 0.16, 0.15)), ("2025-01-02", (0.70, 0.69, 0.17, 0.17, 0.16)), ("2025-01-03", (0.83, 0.81, 0.18, 0.18, 0.17))])
    add_panel_history(panel_core_rows, "panel_f1_b", [("2025-01-01", (0.58, 0.56, 0.18, 0.18, 0.16)), ("2025-01-02", (0.72, 0.70, 0.19, 0.18, 0.17)), ("2025-01-03", (0.85, 0.83, 0.20, 0.19, 0.18))])
    add_panel_history(panel_core_rows, "panel_f2_a", [("2025-01-01", (0.14, 0.14, 0.70, 0.72, 0.20)), ("2025-01-02", (0.15, 0.15, 0.76, 0.79, 0.21)), ("2025-01-03", (0.16, 0.16, 0.83, 0.86, 0.22))])
    add_panel_history(panel_core_rows, "panel_f2_b", [("2025-01-01", (0.16, 0.16, 0.68, 0.70, 0.22)), ("2025-01-02", (0.17, 0.17, 0.75, 0.77, 0.23)), ("2025-01-03", (0.18, 0.18, 0.81, 0.84, 0.24))])
    add_panel_history(panel_core_rows, "panel_f4_a", [("2025-01-01", (0.22, 0.58, 0.18, 0.20, 0.70)), ("2025-01-02", (0.24, 0.66, 0.19, 0.21, 0.76)), ("2025-01-03", (0.26, 0.79, 0.20, 0.22, 0.86))])
    add_panel_history(panel_core_rows, "panel_f4_b", [("2025-01-01", (0.24, 0.60, 0.17, 0.19, 0.72)), ("2025-01-02", (0.25, 0.69, 0.18, 0.20, 0.79)), ("2025-01-03", (0.27, 0.82, 0.19, 0.21, 0.88))])
    write_csv(
        site_out / "panel_day_core.csv",
        panel_core_rows,
        ["date", "panel_id", "mid_ratio", "v_drop", "dtw_dist", "hs_score", "recon_error"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_rebuild_script = repo_root / "research/prognostics/build_panel_day_engine_gpvs_bytype_rebuild_export_v1.py"
    build_audit_script = repo_root / "research/prognostics/build_panel_day_engine_gpvs_detailed_type_inference_audit_v1.py"
    smoke_script = repo_root / "research/prognostics/smoke_test_panel_day_engine_gpvs_bytype_rebuild_export_v1.py"

    py_compile.compile(str(build_rebuild_script), doraise=True)
    py_compile.compile(str(build_audit_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        repo_root / "data/gpvs/out/gpvs_bytype_recovered_model_v1.joblib",
        repo_root / "data/gpvs/out/gpvs_bytype_recovered_feature_manifest_v1.json",
        repo_root / "_share/panel_day_engine_gpvs_bytype_rebuild_parity_v1.csv",
        repo_root / "_share/panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv",
        repo_root / "_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv",
        repo_root / "_share/panel_day_engine_gpvs_detailed_type_inference_summary_v1.csv",
        repo_root / "_share/panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="gpvs_bytype_rebuild_export_smoke_") as tmp_dir:
        root = Path(tmp_dir)
        build_fixture(root)

        rebuild_result = run([sys.executable, str(build_rebuild_script), "--root", str(root)], repo_root)
        assert_true(rebuild_result.returncode == 0, f"rebuild export builder failed: {rebuild_result.stderr or rebuild_result.stdout}")

        model_path = root / "data/gpvs/out/gpvs_bytype_recovered_model_v1.joblib"
        manifest_path = root / "data/gpvs/out/gpvs_bytype_recovered_feature_manifest_v1.json"
        parity_path = root / "_share/panel_day_engine_gpvs_bytype_rebuild_parity_v1.csv"
        summary_path = root / "_share/panel_day_engine_gpvs_bytype_rebuild_summary_v1.csv"
        assert_true(model_path.exists(), "recovered model artifact must be exported")
        assert_true(manifest_path.exists(), "recovered feature manifest must be exported")
        assert_true(parity_path.exists(), "rebuild parity output must be generated")
        assert_true(summary_path.exists(), "rebuild summary output must be generated")

        summary_df = pd.read_csv(summary_path, low_memory=False, encoding="utf-8-sig")
        summary_row = summary_df.iloc[0]
        assert_true(int(summary_row["recovered_model_exported_flag"]) == 1, "summary must record exported model artifact")
        assert_true(int(summary_row["recovered_feature_manifest_exported_flag"]) == 1, "summary must record exported feature manifest")
        assert_true("gpvs_train_supervised" in str(summary_row["recovered_model_source_ko"]), "summary should mention gpvs_train_supervised reuse")

        audit_result = run([sys.executable, str(build_audit_script), "--root", str(root)], repo_root)
        assert_true(audit_result.returncode == 0, f"detailed-type audit builder failed after rebuild export: {audit_result.stderr or audit_result.stdout}")

        audit_df = pd.read_csv(root / "_share/panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv", low_memory=False, encoding="utf-8-sig")
        summary_audit_df = pd.read_csv(root / "_share/panel_day_engine_gpvs_detailed_type_inference_summary_v1.csv", low_memory=False, encoding="utf-8-sig")
        realpanel_sanity_df = pd.read_csv(root / "_share/panel_day_engine_gpvs_detailed_type_realpanel_sanity_v1.csv", low_memory=False, encoding="utf-8-sig")

        assert_true("gpvs_detailed_model_source" in audit_df.columns, "audit output must expose model_source column")
        assert_true(audit_df["gpvs_detailed_model_source"].isin(["recovered_artifact", "inference_unavailable"]).all(), "audit should prefer recovered artifact when export exists")
        assert_true("model_source=recovered_artifact" in str(summary_audit_df.iloc[0]["note_ko"]), "audit summary should expose recovered artifact usage")
        assert_true(len(realpanel_sanity_df) == 6, "real-panel sanity output must be regenerated")

    after = {path: file_digest(path) for path in official_outputs}
    assert_true(before == after, "official outputs changed during smoke test")


if __name__ == "__main__":
    main()
