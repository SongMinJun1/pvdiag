#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]

OUTPUTS = [
    "panel_day_engine_gpvs_canonical_dictionary_v1.csv",
    "panel_day_engine_gpvs_mlpe_fault_matching_table_v1.csv",
    "panel_day_engine_gpvs_mlpe_fault_matching_summary_v1.csv",
    "panel_day_engine_gpvs_mlpe_fault_matching_note_v1.md",
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


def build_fixture(root: Path) -> None:
    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)

    verdict_rows = [
        {"site": "siteA", "panel_id": "panel_f4_1", "패널고장여부_ko": "고장", "GPVS_세부fault_code": "F4L", "GPVS_참고유형_ko": "전기적 고장 계열", "GPVS_시나리오명_ko": "PV 어레이 mismatch(부분 음영) 시나리오"},
        {"site": "siteA", "panel_id": "panel_f2_1", "패널고장여부_ko": "고장", "GPVS_세부fault_code": "F2M", "GPVS_참고유형_ko": "개방/장치이상 계열", "GPVS_시나리오명_ko": "제어 피드백 센서 이상 시나리오"},
        {"site": "siteA", "panel_id": "panel_f2_2", "패널고장여부_ko": "고장", "GPVS_세부fault_code": "F2M", "GPVS_참고유형_ko": "전기적 고장 계열", "GPVS_시나리오명_ko": "제어 피드백 센서 이상 시나리오"},
        {"site": "siteA", "panel_id": "panel_f2_3", "패널고장여부_ko": "고장", "GPVS_세부fault_code": "F2M", "GPVS_참고유형_ko": "전기적 고장 계열", "GPVS_시나리오명_ko": "제어 피드백 센서 이상 시나리오"},
        {"site": "siteA", "panel_id": "panel_f4_2", "패널고장여부_ko": "고장", "GPVS_세부fault_code": "F4L", "GPVS_참고유형_ko": "불확실", "GPVS_시나리오명_ko": "PV 어레이 mismatch(부분 음영) 시나리오"},
        {"site": "siteA", "panel_id": "panel_f2_4", "패널고장여부_ko": "고장", "GPVS_세부fault_code": "F2M", "GPVS_참고유형_ko": "전기적 고장 계열", "GPVS_시나리오명_ko": "제어 피드백 센서 이상 시나리오"},
    ]
    write_csv(
        share_dir / "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        verdict_rows,
        ["site", "panel_id", "패널고장여부_ko", "GPVS_세부fault_code", "GPVS_참고유형_ko", "GPVS_시나리오명_ko"],
    )

    agreement_rows = [
        {"site": "siteA", "panel_id": "panel_f4_1", "overall_gpvs_reference_usefulness_ko": "주의참고", "scenario_vs_kernellog_alignment_ko": "부분일치", "family_vs_kernellog_alignment_ko": "일치"},
        {"site": "siteA", "panel_id": "panel_f2_1", "overall_gpvs_reference_usefulness_ko": "비권장", "scenario_vs_kernellog_alignment_ko": "불일치", "family_vs_kernellog_alignment_ko": "일치"},
        {"site": "siteA", "panel_id": "panel_f2_2", "overall_gpvs_reference_usefulness_ko": "비권장", "scenario_vs_kernellog_alignment_ko": "불일치", "family_vs_kernellog_alignment_ko": "일치"},
        {"site": "siteA", "panel_id": "panel_f2_3", "overall_gpvs_reference_usefulness_ko": "비권장", "scenario_vs_kernellog_alignment_ko": "불일치", "family_vs_kernellog_alignment_ko": "일치"},
        {"site": "siteA", "panel_id": "panel_f4_2", "overall_gpvs_reference_usefulness_ko": "주의참고", "scenario_vs_kernellog_alignment_ko": "부분일치", "family_vs_kernellog_alignment_ko": "비교곤란"},
        {"site": "siteA", "panel_id": "panel_f2_4", "overall_gpvs_reference_usefulness_ko": "비권장", "scenario_vs_kernellog_alignment_ko": "불일치", "family_vs_kernellog_alignment_ko": "부분일치"},
    ]
    write_csv(
        share_dir / "panel_day_engine_gpvs_mlpe_panel_agreement_v1.csv",
        agreement_rows,
        ["site", "panel_id", "overall_gpvs_reference_usefulness_ko", "scenario_vs_kernellog_alignment_ko", "family_vs_kernellog_alignment_ko"],
    )

    write_csv(
        share_dir / "panel_day_engine_gpvs_mlpe_compatibility_summary_v1.csv",
        [
            {
                "fault_panel_count": 6,
                "recovered_model_present_flag": 1,
                "feature_schema_match_ratio": 1.0,
                "strong_shift_panel_count": 6,
                "mild_shift_panel_count": 0,
                "family_alignment_count": 4,
                "family_partial_alignment_count": 1,
                "family_conflict_count": 0,
                "scenario_alignment_count": 0,
                "scenario_partial_alignment_count": 2,
                "scenario_conflict_count": 4,
                "gpvs_reference_useful_count": 0,
                "gpvs_reference_caution_count": 2,
                "gpvs_reference_not_recommended_count": 4,
                "final_recommendation_ko": "참고축으로만 사용",
                "note_ko": "fixture",
            }
        ],
        [
            "fault_panel_count",
            "recovered_model_present_flag",
            "feature_schema_match_ratio",
            "strong_shift_panel_count",
            "mild_shift_panel_count",
            "family_alignment_count",
            "family_partial_alignment_count",
            "family_conflict_count",
            "scenario_alignment_count",
            "scenario_partial_alignment_count",
            "scenario_conflict_count",
            "gpvs_reference_useful_count",
            "gpvs_reference_caution_count",
            "gpvs_reference_not_recommended_count",
            "final_recommendation_ko",
            "note_ko",
        ],
    )

    detailed_rows = [
        {"site": "siteA", "panel_id": "panel_f4_1", "gpvs_detailed_top1_fault_type": "F4L"},
        {"site": "siteA", "panel_id": "panel_f2_1", "gpvs_detailed_top1_fault_type": "F2M"},
        {"site": "siteA", "panel_id": "panel_f2_2", "gpvs_detailed_top1_fault_type": "F2M"},
        {"site": "siteA", "panel_id": "panel_f2_3", "gpvs_detailed_top1_fault_type": "F2M"},
        {"site": "siteA", "panel_id": "panel_f4_2", "gpvs_detailed_top1_fault_type": "F4L"},
        {"site": "siteA", "panel_id": "panel_f2_4", "gpvs_detailed_top1_fault_type": "F2M"},
    ]
    write_csv(
        share_dir / "panel_day_engine_gpvs_detailed_type_inference_audit_v1.csv",
        detailed_rows,
        ["site", "panel_id", "gpvs_detailed_top1_fault_type"],
    )


def main() -> None:
    build_script = REPO_ROOT / "research/prognostics/build_panel_day_engine_gpvs_mlpe_fault_matching_v1.py"
    smoke_script = REPO_ROOT / "research/prognostics/smoke_test_panel_day_engine_gpvs_mlpe_fault_matching_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        REPO_ROOT / "_share/panel_day_engine_panel_multiaxis_verdict_v1.csv",
        REPO_ROOT / "_share/panel_day_engine_project_handoff_pack_v1.md",
        REPO_ROOT / "_share/panel_day_engine_project_closeout_pack_v1.md",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="gpvs_mlpe_fault_matching_smoke_") as tmp_dir:
        root = Path(tmp_dir)
        build_fixture(root)
        result = run([sys.executable, str(build_script), "--root", str(root)], REPO_ROOT)
        if result.returncode != 0:
            raise SystemExit(f"build failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        for output_name in OUTPUTS:
            output_path = root / "_share" / output_name
            assert_true(output_path.exists(), f"missing output: {output_name}")

        dictionary_df = pd.read_csv(root / "_share" / OUTPUTS[0], low_memory=False, encoding="utf-8-sig")
        matching_df = pd.read_csv(root / "_share" / OUTPUTS[1], low_memory=False, encoding="utf-8-sig")
        summary_df = pd.read_csv(root / "_share" / OUTPUTS[2], low_memory=False, encoding="utf-8-sig")
        note_text = (root / "_share" / OUTPUTS[3]).read_text(encoding="utf-8")

        assert_true(len(dictionary_df) == 8, "canonical dictionary must contain 8 rows for F0~F7")
        assert_true(int(summary_df.iloc[0]["canonical_code_count"]) == 8, "canonical_code_count must equal 8")
        assert_true(int(summary_df.iloc[0]["core_reference_count"]) == 3, "core_reference_count must equal 3")
        assert_true(int(summary_df.iloc[0]["auxiliary_reference_count"]) == 1, "auxiliary_reference_count must equal 1")
        assert_true(int(summary_df.iloc[0]["confounder_count"]) == 1, "confounder_count must equal 1")
        assert_true(int(summary_df.iloc[0]["reserved_system_count"]) == 3, "reserved_system_count must equal 3")
        assert_true(not matching_df.empty, "matching table must not be empty")
        assert_true("L/M은 front-facing matching에서는 제거한다" in note_text, "note must mention removing L/M in front-facing matching")

    after = {path: file_digest(path) for path in official_outputs}
    for path in official_outputs:
        assert_true(before[path] == after[path], f"official output changed unexpectedly: {path}")


if __name__ == "__main__":
    main()
