#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_fault_family_regression_pressure_packet_v1.csv"
SUMMARY_NAME = "panel_day_engine_fault_family_regression_pressure_packet_summary_v1.csv"
NOTE_NAME = "panel_day_engine_fault_family_regression_pressure_packet_note_v1.md"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def readiness_row(panel_id: str, closure_class: str, regression_flag: int, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "site": "test",
        "panel_id": panel_id,
        "source_search_status": "same_day_local_non_target",
        "post_br056_closure_class": closure_class,
        "evidence_grade": "strong_non_target_fault_family_seed",
        "raw_top1_ko": "다이오드·서브스트링형",
        "raw_top1_score": 8,
        "raw_top2_ko": "접속·부분개방형",
        "raw_top3_ko": "열화형",
        "live_top1_ko": "",
        "live_external_gpvs_ko": "",
        "gpvs_pack_external_ko": "",
        "recovery_bucket": "re_drop_cycle",
        "synchrony_bucket": "panel_local_or_weak_synchrony",
        "anchor_dates": "2026-01-01",
        "same_day_dates": "2026-01-01",
        "target_exact_top1_flag": 0,
        "device_response_external_flag": 0,
        "sensor_feedback_top1_flag": 0,
        "recovery_recurrence_flag": 1,
        "exact_same_day_local_morphology_flag": 1,
        "same_day_fault_like_row_count": 0,
        "same_day_final_fault_row_count": 1,
        "same_day_common_cause_row_count": 0,
        "target_exact_closure_candidate_flag": 0,
        "fault_family_regression_seed_flag": regression_flag,
        "operator_promotion_allowed_flag": 0,
        "engine_patch_candidate_flag": 0,
    }
    row.update(overrides)
    return row


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = (
        repo_root
        / "research"
        / "prognostics"
        / "build_panel_day_engine_fault_family_regression_pressure_packet_v1.py"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        input_path = root / "readiness.csv"
        out_root = root / "out"
        write_csv(
            input_path,
            [
                readiness_row(
                    "hard_non_target",
                    "hard_same_day_non_target_fault_family_seed",
                    1,
                ),
                readiness_row(
                    "sensor_pressure",
                    "sensor_feedback_hard_same_day_pressure",
                    1,
                    evidence_grade="ambiguity_pressure_seed",
                    raw_top1_ko="센서·피드백형",
                    raw_top1_score=6,
                    sensor_feedback_top1_flag=1,
                    same_day_fault_like_row_count=1,
                ),
                readiness_row(
                    "closed_blocker",
                    "closed_non_fault_near_anchor_observation",
                    0,
                    evidence_grade="closed_non_closing_status_blocker",
                    raw_top1_ko="",
                    same_day_final_fault_row_count=0,
                    exact_same_day_local_morphology_flag=0,
                ),
            ],
        )
        completed = run(
            [
                sys.executable,
                str(script),
                "--readiness-input",
                str(input_path),
                "--output-dir",
                str(out_root),
            ],
            repo_root,
        )
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)
        detail = pd.read_csv(out_root / DETAIL_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(out_root / SUMMARY_NAME, encoding="utf-8-sig")
        note = (out_root / NOTE_NAME).read_text(encoding="utf-8")
        assert_true(len(detail) == 2, detail.to_string())
        assert_true(list(detail["packet_case_id"]) == ["BR058-001", "BR058-002"], detail.to_string())
        assert_true(set(detail["packet_bucket"]) == {
            "non_target_hard_same_day_fault_family_seed",
            "sensor_feedback_hard_same_day_ambiguity_pressure",
        }, detail.to_string())
        assert_true(int(detail["target_exact_closure_candidate_flag"].sum()) == 0, detail.to_string())
        assert_true(int(detail["operator_promotion_allowed_flag"].sum()) == 0, detail.to_string())
        assert_true(int(detail["engine_patch_candidate_flag"].sum()) == 0, detail.to_string())
        assert_true(int(summary["cases"].sum()) == 2, summary.to_string())
        assert_true("does not close target exact-family evidence" in note, note)
        assert_true("evidence input manifest: `not provided`" in note, "note missing no-manifest marker")
        assert_true("`readiness_input`: `explicit_cli`" in note, "note missing explicit readiness source")

        manifest = root / "regression_pressure_inputs.json"
        manifest.write_text(
            json.dumps({"inputs": {"readiness_input": str(input_path)}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest_out = root / "manifest_out"
        manifest_result = run(
            [
                sys.executable,
                str(script),
                "--input-manifest",
                str(manifest),
                "--output-dir",
                str(manifest_out),
            ],
            repo_root,
        )
        assert_true(manifest_result.returncode == 0, manifest_result.stderr or manifest_result.stdout)
        manifest_detail = pd.read_csv(manifest_out / DETAIL_NAME, encoding="utf-8-sig")
        manifest_note = (manifest_out / NOTE_NAME).read_text(encoding="utf-8")
        assert_true(
            manifest_detail["packet_bucket"].tolist() == detail["packet_bucket"].tolist(),
            "manifest packet buckets drifted",
        )
        assert_true(f"evidence input manifest: `{manifest}`" in manifest_note, "note missing manifest path")
        assert_true("`readiness_input`: `input_manifest`" in manifest_note, "note missing manifest readiness source")

        bad_manifest = root / "bad_regression_pressure_inputs.json"
        bad_manifest.write_text(
            json.dumps(
                {"inputs": {"readiness_input": str(root / "missing_readiness.csv")}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_out = root / "override_out"
        override_result = run(
            [
                sys.executable,
                str(script),
                "--readiness-input",
                str(input_path),
                "--input-manifest",
                str(bad_manifest),
                "--output-dir",
                str(override_out),
            ],
            repo_root,
        )
        assert_true(override_result.returncode == 0, override_result.stderr or override_result.stdout)
        override_note = (override_out / NOTE_NAME).read_text(encoding="utf-8")
        assert_true("`readiness_input`: `explicit_cli`" in override_note, "override readiness source drifted")

        missing_key_manifest = root / "missing_key_regression_pressure_inputs.json"
        missing_key_manifest.write_text(json.dumps({"inputs": {}}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        missing_key_result = run(
            [
                sys.executable,
                str(script),
                "--input-manifest",
                str(missing_key_manifest),
                "--output-dir",
                str(root / "missing_key_out"),
            ],
            repo_root,
        )
        assert_true(missing_key_result.returncode != 0, "missing-key manifest unexpectedly passed")
        assert_true(
            "missing `readiness_input`" in (missing_key_result.stderr + missing_key_result.stdout),
            missing_key_result.stderr + missing_key_result.stdout,
        )


if __name__ == "__main__":
    main()
