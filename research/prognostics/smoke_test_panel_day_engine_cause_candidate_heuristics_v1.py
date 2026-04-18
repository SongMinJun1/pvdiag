#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "research/prognostics/build_panel_day_engine_cause_candidate_heuristics_v1.py"
OUTPUT_MAIN = REPO_ROOT / "_share/panel_day_engine_cause_candidate_heuristics_v1.csv"
OUTPUT_BREAKDOWN = REPO_ROOT / "_share/panel_day_engine_cause_candidate_score_breakdown_v1.csv"
OUTPUT_SUMMARY = REPO_ROOT / "_share/panel_day_engine_cause_candidate_summary_v1.csv"

CANDIDATES = [
    "부분음영형",
    "오염형",
    "열화형",
    "다이오드·서브스트링형",
    "접속·부분개방형",
    "센서·피드백형",
    "제어응답형",
    "외부계통교란형",
    "전력변환부형",
    "원인미확정",
]

MAIN_REQUIRED_COLS = [
    "site",
    "panel_id",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
    "GPVS_내부참고유형_ko",
    "GPVS_외부참조패턴_ko",
    "원인후보_top1_ko",
    "원인후보_top1_score",
    "원인후보_top2_ko",
    "원인후보_top2_score",
    "원인후보_top3_ko",
    "원인후보_top3_score",
    "원인후보_경합상태_ko",
    "원인후보_공동상위후보_csv",
    "원인후보_실증우선확인_ko",
    "원인후보_신뢰도_ko",
    "원인후보_해석메모_ko",
]

BREAKDOWN_REQUIRED_COLS = [
    "site",
    "panel_id",
    "candidate_ko",
    "raw_score",
    "support_signal_csv",
    "note_ko",
]

SUMMARY_REQUIRED_COLS = [
    "fault_panel_count",
    "unique_top1_candidate_count",
    "top1_부분음영형_count",
    "top1_오염형_count",
    "top1_열화형_count",
    "top1_다이오드·서브스트링형_count",
    "top1_접속·부분개방형_count",
    "top1_센서·피드백형_count",
    "top1_제어응답형_count",
    "top1_외부계통교란형_count",
    "top1_전력변환부형_count",
    "top1_원인미확정_count",
    "단일우세_count",
    "two_way_competition_count",
    "multi_way_competition_count",
    "note_ko",
]


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


def main() -> None:
    py_compile.compile(str(REPO_ROOT / "pv_ae/panel_day_engine.py"), doraise=True)
    py_compile.compile(str(BUILD_SCRIPT), doraise=True)
    py_compile.compile(str(REPO_ROOT / "research/prognostics/smoke_test_panel_day_engine_cause_candidate_heuristics_v1.py"), doraise=True)

    result = run([sys.executable, str(BUILD_SCRIPT)])
    assert_true(result.returncode == 0, f"build failed: {result.stderr or result.stdout}")

    assert_true(OUTPUT_MAIN.exists(), f"missing output: {OUTPUT_MAIN}")
    assert_true(OUTPUT_BREAKDOWN.exists(), f"missing output: {OUTPUT_BREAKDOWN}")
    assert_true(OUTPUT_SUMMARY.exists(), f"missing output: {OUTPUT_SUMMARY}")

    main_df = pd.read_csv(OUTPUT_MAIN, low_memory=False, encoding="utf-8-sig")
    breakdown_df = pd.read_csv(OUTPUT_BREAKDOWN, low_memory=False, encoding="utf-8-sig")
    summary_df = pd.read_csv(OUTPUT_SUMMARY, low_memory=False, encoding="utf-8-sig")

    missing_main = [column for column in MAIN_REQUIRED_COLS if column not in main_df.columns]
    missing_breakdown = [column for column in BREAKDOWN_REQUIRED_COLS if column not in breakdown_df.columns]
    missing_summary = [column for column in SUMMARY_REQUIRED_COLS if column not in summary_df.columns]
    assert_true(not missing_main, f"main output missing columns: {missing_main}")
    assert_true(not missing_breakdown, f"breakdown output missing columns: {missing_breakdown}")
    assert_true(not missing_summary, f"summary output missing columns: {missing_summary}")

    assert_true(len(main_df) == 6, f"fault panel count must be 6, found {len(main_df)}")
    assert_true(len(summary_df) == 1, f"summary row count must be 1, found {len(summary_df)}")
    assert_true(len(breakdown_df) == 6 * len(CANDIDATES), f"breakdown row count must be {6 * len(CANDIDATES)}, found {len(breakdown_df)}")

    for column in [
        "원인후보_top1_ko",
        "원인후보_top2_ko",
        "원인후보_top3_ko",
        "원인후보_경합상태_ko",
        "원인후보_공동상위후보_csv",
        "원인후보_실증우선확인_ko",
        "원인후보_신뢰도_ko",
        "원인후보_해석메모_ko",
    ]:
        assert_true(main_df[column].map(normalize_text).ne("").all(), f"{column} must be populated for every fault row")

    for column in ["원인후보_top1_score", "원인후보_top2_score", "원인후보_top3_score"]:
        assert_true(pd.to_numeric(main_df[column], errors="coerce").notna().all(), f"{column} must be numeric for every fault row")

    assert_true(set(main_df["원인후보_신뢰도_ko"].map(normalize_text)).issubset({"high", "medium", "low"}), "confidence labels must stay in {high, medium, low}")

    summary_row = summary_df.iloc[0]
    assert_true(int(summary_row["fault_panel_count"]) == 6, "summary fault_panel_count must be 6")

    expected_rows = {
        ("conalog", "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0"): {
            "top1": "다이오드·서브스트링형",
            "confidence": "high",
            "competition": "단일우세",
            "joint": "다이오드·서브스트링형",
            "action": "다이오드·서브스트링형 우선 점검",
        },
        ("conalog", "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"): {
            "top1": "센서·피드백형",
            "confidence": "medium",
            "competition": "2자경합",
            "joint": "센서·피드백형,접속·부분개방형",
            "action": "센서·피드백형과 접속·부분개방형을 함께 우선 점검",
        },
        ("gangui", "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7"): {
            "top1": "다이오드·서브스트링형",
            "confidence": "low",
            "competition": "다자경합",
            "joint": "다이오드·서브스트링형,센서·피드백형,접속·부분개방형,제어응답형",
            "action": "다이오드·서브스트링형, 센서·피드백형, 접속·부분개방형을 함께 우선 점검",
        },
        ("gangui", "bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16"): {
            "top1": "다이오드·서브스트링형",
            "confidence": "low",
            "competition": "다자경합",
            "joint": "다이오드·서브스트링형,센서·피드백형,접속·부분개방형,제어응답형",
            "action": "다이오드·서브스트링형, 센서·피드백형, 접속·부분개방형을 함께 우선 점검",
        },
        ("ktc_ess", "10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12"): {
            "top1": "다이오드·서브스트링형",
            "confidence": "high",
            "competition": "단일우세",
            "joint": "다이오드·서브스트링형",
            "action": "다이오드·서브스트링형 우선 점검",
        },
        ("ktc_ess", "70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4"): {
            "top1": "열화형",
            "confidence": "low",
            "competition": "다자경합",
            "joint": "열화형,센서·피드백형,다이오드·서브스트링형,제어응답형",
            "action": "열화형, 센서·피드백형, 다이오드·서브스트링형을 함께 우선 점검",
        },
    }
    for (site, panel_id), expected in expected_rows.items():
        row = main_df.loc[main_df["site"].eq(site) & main_df["panel_id"].eq(panel_id)]
        assert_true(len(row) == 1, f"expected row for {site}/{panel_id}")
        data = row.iloc[0]
        assert_true(normalize_text(data["원인후보_top1_ko"]) == expected["top1"], f"{site}/{panel_id} top1 mismatch")
        assert_true(normalize_text(data["원인후보_신뢰도_ko"]) == expected["confidence"], f"{site}/{panel_id} confidence mismatch")
        assert_true(normalize_text(data["원인후보_경합상태_ko"]) == expected["competition"], f"{site}/{panel_id} competition mismatch")
        assert_true(normalize_text(data["원인후보_공동상위후보_csv"]) == expected["joint"], f"{site}/{panel_id} joint-candidate csv mismatch")
        assert_true(normalize_text(data["원인후보_실증우선확인_ko"]) == expected["action"], f"{site}/{panel_id} action note mismatch")

    top1_counts = main_df["원인후보_top1_ko"].value_counts().to_dict()
    competition_counts = main_df["원인후보_경합상태_ko"].value_counts().to_dict()
    assert_true(int(summary_row["unique_top1_candidate_count"]) == 3, "summary unique_top1_candidate_count must be 3")
    assert_true(int(summary_row["top1_다이오드·서브스트링형_count"]) == int(top1_counts.get("다이오드·서브스트링형", 0)) == 4, "top1_다이오드·서브스트링형_count must be 4")
    assert_true(int(summary_row["top1_센서·피드백형_count"]) == int(top1_counts.get("센서·피드백형", 0)) == 1, "top1_센서·피드백형_count must be 1")
    assert_true(int(summary_row["top1_열화형_count"]) == int(top1_counts.get("열화형", 0)) == 1, "top1_열화형_count must be 1")
    assert_true(int(summary_row["단일우세_count"]) == int(competition_counts.get("단일우세", 0)) == 2, "단일우세_count must be 2")
    assert_true(int(summary_row["two_way_competition_count"]) == int(competition_counts.get("2자경합", 0)) == 1, "two_way_competition_count must be 1")
    assert_true(int(summary_row["multi_way_competition_count"]) == int(competition_counts.get("다자경합", 0)) == 3, "multi_way_competition_count must be 3")

    candidate_counts = breakdown_df.groupby(["site", "panel_id"])["candidate_ko"].nunique().to_dict()
    assert_true(all(count == len(CANDIDATES) for count in candidate_counts.values()), "every panel must contain every canonical candidate in breakdown")

    note_text = normalize_text(summary_row["note_ko"])
    assert_true("heuristic candidate-ranking layer" in note_text, "summary note must mention heuristic candidate-ranking layer")
    assert_true("field trial triage" in note_text, "summary note must mention field trial triage")
    assert_true("final root-cause confirmation" in note_text, "summary note must forbid definitive diagnosis wording")
    assert_true("공동 현장점검 후보" in note_text, "summary note must mention joint inspection interpretation for competition rows")


if __name__ == "__main__":
    main()
