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


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture(root: Path) -> None:
    share_dir = root / "_share"
    gpvs_out = root / "data" / "gpvs" / "out"
    gpvs_download = root / "data" / "gpvs" / "_download" / "GPVS_Faults" / "n76t439f65-1" / "CSV_Files"
    repro_dir = root / "research" / "prognostics"
    docs_dir = root / "docs" / "reports"

    share_dir.mkdir(parents=True, exist_ok=True)
    gpvs_out.mkdir(parents=True, exist_ok=True)
    gpvs_download.mkdir(parents=True, exist_ok=True)
    repro_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    training_rows: list[dict[str, object]] = []
    for fault_type, source_id, count in [("F1L", "src_f1l", 4), ("F2L", "src_f2l", 4), ("F4L", "src_f4l", 4)]:
        for idx in range(count):
            training_rows.append(
                {
                    "fault_type": fault_type,
                    "source_id": source_id,
                    "fault_sid": 1,
                    "is_fault_window": 1,
                    "is_fault_file": 1,
                    "level_drop_raw": 0.1 * (idx + 1),
                    "v_drop_raw": 0.2 * (idx + 1),
                    "dtw_raw": 0.3 * (idx + 1),
                    "hs_raw": 0.4 * (idx + 1),
                    "ae_raw": 0.5 * (idx + 1),
                }
            )
    write_csv(
        gpvs_out / "gpvs_window_scores.csv",
        training_rows,
        [
            "fault_type",
            "source_id",
            "fault_sid",
            "is_fault_window",
            "is_fault_file",
            "level_drop_raw",
            "v_drop_raw",
            "dtw_raw",
            "hs_raw",
            "ae_raw",
        ],
    )
    write_csv(
        gpvs_out / "EXTERNAL_GPVS_BYTYPE_METRICS.csv",
        [
            {"fault_type": "F1L", "sid": 1, "score": "level_drop_like", "ap": 0.7},
            {"fault_type": "F2L", "sid": 2, "score": "hs_like", "ap": 0.6},
            {"fault_type": "F4L", "sid": 4, "score": "dtw_like", "ap": 0.8},
        ],
        ["fault_type", "sid", "score", "ap"],
    )

    (gpvs_download / "F4L.csv").write_text("t,v\n0,1\n", encoding="utf-8")

    (repro_dir / "external_eval_gpvs.py").write_text(
        "\n".join(
            [
                "import argparse",
                "import pandas as pd",
                "def main():",
                "    ap = argparse.ArgumentParser()",
                "    ap.add_argument('--scores-csv', default='data/gpvs/out/gpvs_window_scores.csv')",
                "    args = ap.parse_args()",
                "    df = pd.read_csv(args.scores_csv)",
                "    df.to_csv('data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv', index=False)",
                "if __name__ == '__main__':",
                "    main()",
            ]
        ),
        encoding="utf-8",
    )
    (repro_dir / "gpvs_train_supervised.py").write_text(
        "\n".join(
            [
                "from sklearn.linear_model import LogisticRegression",
                "def train(train_x, train_y, out_csv):",
                "    model = LogisticRegression()",
                "    model.fit(train_x, train_y)",
                "    out_csv.write_text('metrics only', encoding='utf-8')",
            ]
        ),
        encoding="utf-8",
    )
    (docs_dir / "gpvs_final_summary.md").write_text(
        "# GPVS Final Summary\n- model: LogisticRegression\n- split: grouped_source\n",
        encoding="utf-8",
    )

    write_csv(
        share_dir / "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv",
        [
            {
                "site": "siteA",
                "panel_id": f"panel_{idx}",
                "event_reference_date": "2025-01-01",
                "gpvs_family_label": "전기적 고장 계열",
                "gpvs_detailed_top1_fault_type": "F4L",
                "gpvs_detailed_top1_score": 0.9,
                "gpvs_detailed_top2_fault_type": "F2L",
                "gpvs_detailed_top2_score": 0.1,
                "gpvs_detailed_margin": 0.8,
                "gpvs_detailed_status_ko": "추론성공",
                "gpvs_detailed_reason_ko": "model_source=fallback_lr:gpvs_window_scores.csv",
            }
            for idx in range(6)
        ],
        [
            "site",
            "panel_id",
            "event_reference_date",
            "gpvs_family_label",
            "gpvs_detailed_top1_fault_type",
            "gpvs_detailed_top1_score",
            "gpvs_detailed_top2_fault_type",
            "gpvs_detailed_top2_score",
            "gpvs_detailed_margin",
            "gpvs_detailed_status_ko",
            "gpvs_detailed_reason_ko",
        ],
    )
    write_csv(
        share_dir / "panel_day_engine_gpvs_detailed_type_inference_summary_v1.csv",
        [
            {
                "fault_panel_count": 6,
                "inference_success_count": 6,
                "abstain_count": 0,
                "inference_unavailable_count": 0,
                "note_ko": "model_source=fallback_lr:gpvs_window_scores.csv; current real-panel top1 unique fault_type count=1",
            }
        ],
        [
            "fault_panel_count",
            "inference_success_count",
            "abstain_count",
            "inference_unavailable_count",
            "note_ko",
        ],
    )
    write_csv(
        share_dir / "panel_day_engine_gpvs_detailed_type_cv_summary_v1.csv",
        [
            {
                "cv_fold": 1,
                "macro_recall": 0.0,
                "macro_f1": 0.0,
                "top1_accuracy": 0.0,
                "unique_predicted_fault_type_count": 1,
                "cv_macro_recall_mean": "",
                "cv_macro_f1_mean": "",
                "cv_top1_accuracy_mean": "",
                "cv_unique_predicted_fault_type_count_mean": "",
                "note_ko": "degenerate",
            },
            {
                "cv_fold": "summary",
                "macro_recall": "",
                "macro_f1": "",
                "top1_accuracy": "",
                "unique_predicted_fault_type_count": "",
                "cv_macro_recall_mean": 0.0,
                "cv_macro_f1_mean": 0.0,
                "cv_top1_accuracy_mean": 0.0,
                "cv_unique_predicted_fault_type_count_mean": 1.0,
                "note_ko": "degenerate",
            },
        ],
        [
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
        ],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research/prognostics/build_panel_day_engine_gpvs_bytype_provenance_audit_v1.py"
    smoke_script = repo_root / "research/prognostics/smoke_test_panel_day_engine_gpvs_bytype_provenance_audit_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        repo_root / "_share/panel_day_engine_gpvs_bytype_provenance_inventory_v1.csv",
        repo_root / "_share/panel_day_engine_gpvs_bytype_provenance_summary_v1.csv",
        repo_root / "_share/panel_day_engine_gpvs_bytype_provenance_note_v1.md",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="gpvs_bytype_provenance_audit_smoke_") as tmp_dir:
        root = Path(tmp_dir)
        build_fixture(root)

        result = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(result.returncode == 0, f"builder failed: {result.stderr or result.stdout}")

        inventory_path = root / "_share/panel_day_engine_gpvs_bytype_provenance_inventory_v1.csv"
        summary_path = root / "_share/panel_day_engine_gpvs_bytype_provenance_summary_v1.csv"
        note_path = root / "_share/panel_day_engine_gpvs_bytype_provenance_note_v1.md"
        assert_true(inventory_path.exists(), "missing provenance inventory output")
        assert_true(summary_path.exists(), "missing provenance summary output")
        assert_true(note_path.exists(), "missing provenance note output")

        inventory_df = pd.read_csv(inventory_path, low_memory=False, encoding="utf-8-sig")
        summary_df = pd.read_csv(summary_path, low_memory=False, encoding="utf-8-sig")
        note_text = note_path.read_text(encoding="utf-8")

        assert_true(not inventory_df.empty, "inventory output must not be empty")
        assert_true(len(summary_df) == 1, "summary output must contain exactly one row")

        summary_row = summary_df.iloc[0]
        assert_true(str(summary_row["provenance_status"]) != "original_trained_head_recovered", "fixture should not recover original trained head")
        assert_true(int(summary_row["serialized_model_found_flag"]) == 0, "serialized model should be absent in fixture")
        assert_true(int(summary_row["training_script_found_flag"]) == 1, "training script should be found in fixture")
        assert_true(int(summary_row["evaluation_script_found_flag"]) == 1, "evaluation script should be found in fixture")
        assert_true(int(summary_row["external_eval_loads_serialized_model_flag"]) == 0, "external_eval should not load serialized model in fixture")
        assert_true(int(summary_row["external_eval_trains_model_flag"]) == 0, "external_eval should not train model in fixture")
        assert_true(int(summary_row["external_eval_precomputed_scores_only_flag"]) == 1, "external_eval should be classified as precomputed-score evaluation in fixture")
        assert_true(int(summary_row["current_fallback_lr_attachable_flag"]) == 0, "fallback_lr attachable flag must be 0 in fixture")
        assert_true(int(summary_row["fallback_top1_collapse_flag"]) == 1, "collapse flag must be 1 in fixture")

        serialized_row = inventory_df.loc[inventory_df["artifact_kind"].eq("serialized_model")].iloc[0]
        assert_true(int(serialized_row["exists_flag"]) == 0, "serialized model inventory row should indicate absence")
        training_asset_rows = inventory_df.loc[inventory_df["artifact_kind"].eq("score_frame_fault_type_audit")].copy()
        assert_true(len(training_asset_rows) == 3, "fixture should emit three fault_type audit rows")
        assert_true(training_asset_rows["unique_source_count"].fillna(0).astype(float).eq(1).all(), "unique_source_count should be 1 for all fixture fault types")

        assert_true("# 1. 현재 확인된 by-type 자산" in note_text, "note section 1 missing")
        assert_true("# 2. 원본 모델 복구 가능 여부" in note_text, "note section 2 missing")
        assert_true("# 3. 왜 fallback_lr를 붙이면 안 되는지" in note_text, "note section 3 missing")
        assert_true("# 4. 다음에 정말 필요한 것" in note_text, "note section 4 missing")
        assert_true("fallback_lr" in note_text, "note should explicitly mention fallback_lr surrogate")
        assert_true("current_fallback_lr_attachable_flag" in note_text, "note should mention fallback attachability")

    after = {path: file_digest(path) for path in official_outputs}
    assert_true(before == after, "official outputs changed during smoke test")


if __name__ == "__main__":
    main()
