#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "research/prognostics/build_panel_day_engine_integrated_result_table_v1.py"
OUTPUT_TABLE = REPO_ROOT / "_share/panel_day_engine_integrated_result_table_v1.csv"
OUTPUT_SUMMARY = REPO_ROOT / "_share/panel_day_engine_integrated_result_summary_v1.csv"

TABLE_REQUIRED_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "커널로그_원인군_ko",
    "GPVS_내부참고유형_ko",
    "GPVS_외부참조패턴_ko",
    "GPVS_최종사용권고_ko",
    "대표판정요약_ko",
    "판정근거요약_ko",
]

SUMMARY_REQUIRED_COLS = [
    "total_panel_count",
    "fault_panel_count",
    "non_fault_or_unresolved_count",
    "gpvs_core_reference_count",
    "gpvs_auxiliary_reference_count",
    "gpvs_not_used_count",
    "note_ko",
]

FORBIDDEN_COLS = {
    "GPVS_세부fault_code",
    "GPVS_세부fault_score",
    "GPVS_세부fault_rank2_code",
    "GPVS_세부fault_rank2_score",
    "GPVS_세부fault_margin",
    "GPVS_운전모드_ko",
    "GPVS_해석주의_ko",
    "GPVS_시나리오_family_ko",
    "GPVS_시나리오명_ko",
    "GPVS_시나리오_고장상황설명_ko",
    "GPVS_시나리오_부착상태_ko",
}

FORBIDDEN_VALUE_PATTERNS = [
    r"\bF[0-7][LM]\b",
    r"\bMPPT\b",
    r"\bIPPT\b",
    r"\bscore\b",
    r"\bmargin\b",
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
    py_compile.compile(str(REPO_ROOT / "research/prognostics/smoke_test_panel_day_engine_integrated_result_table_v1.py"), doraise=True)

    result = run([sys.executable, str(BUILD_SCRIPT)])
    assert_true(result.returncode == 0, f"build failed: {result.stderr or result.stdout}")

    assert_true(OUTPUT_TABLE.exists(), f"missing output: {OUTPUT_TABLE}")
    assert_true(OUTPUT_SUMMARY.exists(), f"missing output: {OUTPUT_SUMMARY}")

    table_df = pd.read_csv(OUTPUT_TABLE, low_memory=False, encoding="utf-8-sig")
    summary_df = pd.read_csv(OUTPUT_SUMMARY, low_memory=False, encoding="utf-8-sig")

    missing_table_cols = [column for column in TABLE_REQUIRED_COLS if column not in table_df.columns]
    assert_true(not missing_table_cols, f"table missing columns: {missing_table_cols}")
    missing_summary_cols = [column for column in SUMMARY_REQUIRED_COLS if column not in summary_df.columns]
    assert_true(not missing_summary_cols, f"summary missing columns: {missing_summary_cols}")

    forbidden_columns_present = sorted(FORBIDDEN_COLS.intersection(table_df.columns))
    assert_true(not forbidden_columns_present, f"integrated table re-exposed forbidden GPVS columns: {forbidden_columns_present}")

    assert_true(len(table_df) == 25, f"integrated table row count must be 25, found {len(table_df)}")
    assert_true(len(summary_df) == 1, f"integrated summary must contain exactly one row, found {len(summary_df)}")

    summary_row = summary_df.iloc[0]
    assert_true(int(summary_row["total_panel_count"]) == 25, "summary total_panel_count must be 25")
    assert_true(int(summary_row["fault_panel_count"]) == 6, "summary fault_panel_count must be 6")
    assert_true(int(summary_row["non_fault_or_unresolved_count"]) == 19, "summary non_fault_or_unresolved_count must be 19")
    assert_true(int(summary_row["gpvs_core_reference_count"]) == 2, "summary gpvs_core_reference_count must be 2")
    assert_true(int(summary_row["gpvs_auxiliary_reference_count"]) == 4, "summary gpvs_auxiliary_reference_count must be 4")
    assert_true(int(summary_row["gpvs_not_used_count"]) == 19, "summary gpvs_not_used_count must be 19")

    statuses = table_df["패널고장여부_ko"].map(normalize_text)
    fault_df = table_df.loc[statuses.eq("고장")].copy()
    non_fault_df = table_df.loc[~statuses.eq("고장")].copy()
    assert_true(len(fault_df) == 6, f"fault row count must be 6, found {len(fault_df)}")
    assert_true(len(non_fault_df) == 19, f"non-fault/unresolved row count must be 19, found {len(non_fault_df)}")
    assert_true(statuses.iloc[:6].eq("고장").all(), "fault panels must be ordered first in the integrated table")
    assert_true(not statuses.iloc[6:].eq("고장").any(), "non-fault/unresolved panels must follow the fault block")

    fault_recommendation_counts = fault_df["GPVS_최종사용권고_ko"].map(normalize_text).value_counts().to_dict()
    assert_true(int(fault_recommendation_counts.get("핵심참조", 0)) == 2, "fault block must contain 2 핵심참조 rows")
    assert_true(int(fault_recommendation_counts.get("보조참조", 0)) == 4, "fault block must contain 4 보조참조 rows")
    assert_true(int(fault_recommendation_counts.get("비권장", 0)) == 0, "fault block must not contain 비권장 rows")

    non_fault_gpvs = non_fault_df[
        ["GPVS_내부참고유형_ko", "GPVS_외부참조패턴_ko", "GPVS_최종사용권고_ko"]
    ].apply(lambda column: column.map(normalize_text))
    assert_true(not non_fault_gpvs.ne("").any().any(), "non-fault/unresolved rows must keep GPVS columns blank")
    assert_true(non_fault_df["판정근거요약_ko"].map(normalize_text).eq("").all(), "non-fault/unresolved rows must keep 판정근거요약_ko blank")

    c429_row = table_df.loc[
        table_df["site"].eq("conalog")
        & table_df["panel_id"].eq("c42997a6-5881-47e7-9035-7de8a2673b54.1.1")
    ]
    assert_true(len(c429_row) == 1, "expected c429 row in integrated table")
    c429 = c429_row.iloc[0]
    assert_true(normalize_text(c429["GPVS_외부참조패턴_ko"]) == "장치 응답 이상형", "c429 row must keep 장치 응답 이상형")
    assert_true(normalize_text(c429["GPVS_최종사용권고_ko"]) == "보조참조", "c429 row must keep 보조참조")
    assert_true("GPVS는 장치 응답 이상형을 보조참조로 제시" in normalize_text(c429["판정근거요약_ko"]), "c429 rationale summary mismatch")

    row_10305 = table_df.loc[
        table_df["site"].eq("ktc_ess")
        & table_df["panel_id"].eq("10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12")
    ]
    assert_true(len(row_10305) == 1, "expected 10305 row in integrated table")
    row_10305_data = row_10305.iloc[0]
    assert_true(normalize_text(row_10305_data["GPVS_외부참조패턴_ko"]) == "국소 출력 불균형형", "10305 row must keep 국소 출력 불균형형")
    assert_true(normalize_text(row_10305_data["GPVS_최종사용권고_ko"]) == "핵심참조", "10305 row must keep 핵심참조")
    assert_true("GPVS는 국소 출력 불균형형을 핵심참조로 제시" in normalize_text(row_10305_data["판정근거요약_ko"]), "10305 rationale summary mismatch")

    flat_text = "\n".join(
        [column for column in table_df.columns] + [normalize_text(value) for value in table_df.astype(str).stack().tolist()]
    )
    for pattern in FORBIDDEN_VALUE_PATTERNS:
        assert_true(re.search(pattern, flat_text) is None, f"integrated front-facing output exposed forbidden GPVS token: {pattern}")

    note_text = normalize_text(summary_row["note_ko"])
    assert_true("panel multiaxis verdict" in note_text, "summary note must mention panel multiaxis verdict as primary")
    assert_true("kernel-log" in note_text, "summary note must mention kernel-log interpretation layer")
    assert_true("reference-only" in note_text, "summary note must mention GPVS reference-only rule")


if __name__ == "__main__":
    main()
