#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_result_delta_scorecard_v1.csv"
SUMMARY_NAME = "panel_day_engine_result_delta_scorecard_summary_v1.csv"
NOTE_NAME = "panel_day_engine_result_delta_scorecard_note_v1.md"


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def seed_runtime_root(root: Path) -> tuple[Path, Path]:
    runtime = root / "runtime"
    share = runtime / "raw_only_chain_workspace" / "_share"
    result = runtime / "result"
    write_json(
        runtime / "shadow_compare_v1.json",
        {
            "compared_site_count": 1,
            "matched_site_count": 1,
            "all_compared_sites_match": True,
            "sites": {
                "fixture": {
                    "match": True,
                    "diffs": [],
                    "expected": {"row_count": 10, "digest_sha256": "abc"},
                    "actual": {"row_count": 10, "digest_sha256": "abc"},
                }
            },
        },
    )
    write_json(
        result / "raw_only_chain_summary_v1.json",
        {
            "fixed_fault_reference_compare": {
                "reference_available": True,
                "reference_row_count": 2,
                "candidate_row_count": 3,
                "matched_row_key_count": 1,
                "overlap_decision_columns_match": False,
                "overlap_diff_columns": ["2순위_의심원인_ko"],
            },
            "publish_meta": {
                "candidate_row_count": 3,
                "published_current_row_count": 3,
                "dropped_candidate_row_count": 0,
            },
        },
    )
    write_csv(
        share / "panel_day_engine_runtime_final_verdict_v1.csv",
        [
            {
                "site": "fixture",
                "panel_id": "p1",
                "패널고장여부_ko": "고장",
                "대표판정_ko": "전조형 고장",
                "최종고장양상_ko": "진행성 악화",
            },
            {
                "site": "fixture",
                "panel_id": "p2",
                "패널고장여부_ko": "고장",
                "대표판정_ko": "전조형 고장",
                "최종고장양상_ko": "급격 종료",
            },
            {
                "site": "fixture",
                "panel_id": "p3",
                "패널고장여부_ko": "미확정",
                "대표판정_ko": "미확정",
                "최종고장양상_ko": "",
            },
        ],
    )
    write_csv(
        share / "panel_day_engine_runtime_cause_candidate_heuristics_v1.csv",
        [
            {"site": "fixture", "panel_id": "p1", "원인후보_top1_ko": "센서·피드백형", "원인후보_신뢰도_ko": "중간"},
            {"site": "fixture", "panel_id": "p2", "원인후보_top1_ko": "다이오드·서브스트링형", "원인후보_신뢰도_ko": "높음"},
        ],
    )
    write_csv(
        result / "fault_panel_result_precursor_report_v1.csv",
        [],
        columns=["site", "panel_id"],
    )
    write_csv(
        result / "fault_panel_result_raw_only_fault_signal_report_v1.csv",
        [
            {"site": "fixture", "panel_id": "p1", "근접 공통원인": "strict_trigger 근처 공통원인 흔들림 동반"},
            {"site": "fixture", "panel_id": "p2", "근접 공통원인": ""},
        ],
    )
    prepatch = root / "prepatch.csv"
    write_csv(prepatch, [{"overall_status": "pass", "gate_count": 2}])
    return runtime, prepatch


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_panel_day_engine_result_delta_scorecard_v1.py"
    with tempfile.TemporaryDirectory(prefix="result_delta_scorecard_") as tmp_dir:
        root = Path(tmp_dir)
        runtime, prepatch = seed_runtime_root(root)
        input_manifest = root / "input_manifest.json"
        write_json(input_manifest, {"inputs": {"prepatch_runbook_summary": str(prepatch)}})
        out = root / "out"
        completed = run(
            [
                sys.executable,
                str(script),
                "--runtime-root",
                str(runtime),
                "--input-manifest",
                str(input_manifest),
                "--output-dir",
                str(out),
            ],
            repo_root,
        )
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)
        detail = pd.read_csv(out / DETAIL_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(out / SUMMARY_NAME, encoding="utf-8-sig")
        note = (out / NOTE_NAME).read_text(encoding="utf-8")
        row = summary.iloc[0]
        assert_true(row["overall_status"] == "pass", summary.to_string())
        assert_true(int(row["core_total_diff_count"]) == 0, summary.to_string())
        assert_true(int(row["fault_panel_count"]) == 2, summary.to_string())
        assert_true(int(row["precursor_candidate_row_count"]) == 0, summary.to_string())
        assert_true(int(row["proximal_common_cause_fault_signal_count"]) == 1, summary.to_string())
        assert_true(row["performance_improvement_claim_allowed"] == "no_truth_label_not_claimed", summary.to_string())
        assert_true("core_diff_count" in set(detail["metric_name"]), detail.to_string())
        assert_true("accuracy/F1 improvement" in note, note)
        assert_true("`prepatch_runbook_summary`: `input_manifest`" in note, note)


if __name__ == "__main__":
    main()
