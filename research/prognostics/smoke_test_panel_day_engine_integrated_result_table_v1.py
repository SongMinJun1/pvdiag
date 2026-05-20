#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
if __package__ in {None, ""}:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from research.prognostics.heuristic_display_registry_v1 import (
        DISPLAY_HEURISTIC_NAME_MAP,
        LEGACY_HEURISTIC_DISPLAY_NAMES,
    )
else:
    from .heuristic_display_registry_v1 import (
        DISPLAY_HEURISTIC_NAME_MAP,
        LEGACY_HEURISTIC_DISPLAY_NAMES,
    )
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
    "1순위_의심원인_ko",
    "2순위_의심원인_ko",
    "3순위_의심원인_ko",
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
    "GPVS_내부참고유형_ko",
    "GPVS_외부참조패턴_ko",
    "GPVS_최종사용권고_ko",
    "대표판정요약_ko",
    "판정근거요약_ko",
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

UNMAPPED_LABELS = {"부분음영형", "오염형", "열화형", "원인미확정"}


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
    assert_true(table_df.columns.tolist() == TABLE_REQUIRED_COLS, f"integrated table columns must match exactly: {TABLE_REQUIRED_COLS}")
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

    for column in ["1순위_의심원인_ko", "2순위_의심원인_ko", "3순위_의심원인_ko"]:
        assert_true(fault_df[column].map(normalize_text).ne("").all(), f"fault rows must populate {column}")
        assert_true(non_fault_df[column].map(normalize_text).eq("").all(), f"non-fault/unresolved rows must keep {column} blank")

    c429_row = table_df.loc[
        table_df["site"].eq("conalog")
        & table_df["panel_id"].eq("c42997a6-5881-47e7-9035-7de8a2673b54.1.1")
    ]
    assert_true(len(c429_row) == 1, "expected c429 row in integrated table")
    c429 = c429_row.iloc[0]
    assert_true(normalize_text(c429["1순위_의심원인_ko"]) == "센서·계측 피드백 이상형", "c429 top1 display label mismatch")
    assert_true(normalize_text(c429["2순위_의심원인_ko"]) == "접속 불량·부분 개방형", "c429 top2 display label mismatch")
    assert_true(normalize_text(c429["3순위_의심원인_ko"]) == "제어 응답 이상형", "c429 top3 display label mismatch")

    row_10305 = table_df.loc[
        table_df["site"].eq("ktc_ess")
        & table_df["panel_id"].eq("10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12")
    ]
    assert_true(len(row_10305) == 1, "expected 10305 row in integrated table")
    row_10305_data = row_10305.iloc[0]
    assert_true(normalize_text(row_10305_data["1순위_의심원인_ko"]) == "다이오드·서브스트링 이상형", "10305 top1 display label mismatch")
    assert_true(normalize_text(row_10305_data["2순위_의심원인_ko"]) == "부분음영형", "10305 top2 should stay unrenamed")
    assert_true(normalize_text(row_10305_data["3순위_의심원인_ko"]) == "접속 불량·부분 개방형", "10305 top3 display label mismatch")

    row_70ad = table_df.loc[
        table_df["site"].eq("ktc_ess")
        & table_df["panel_id"].eq("70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4")
    ]
    assert_true(len(row_70ad) == 1, "expected 70ad row in integrated table")
    row_70ad_data = row_70ad.iloc[0]
    assert_true(normalize_text(row_70ad_data["1순위_의심원인_ko"]) == "열화형", "70ad top1 should stay unrenamed")
    assert_true(normalize_text(row_70ad_data["2순위_의심원인_ko"]) == "센서·계측 피드백 이상형", "70ad top2 display label mismatch")
    assert_true(normalize_text(row_70ad_data["3순위_의심원인_ko"]) == "다이오드·서브스트링 이상형", "70ad top3 display label mismatch")

    display_values = [normalize_text(value) for value in table_df[["1순위_의심원인_ko", "2순위_의심원인_ko", "3순위_의심원인_ko"]].stack().tolist()]
    for raw_label, display_label in DISPLAY_HEURISTIC_NAME_MAP.items():
        assert_true(raw_label not in display_values, f"raw heuristic label must not appear in integrated table display: {raw_label}")
        if display_label in display_values:
            continue
        if raw_label in {"전력변환부형", "외부계통교란형"}:
            continue
        raise SystemExit(f"expected display-renamed label missing from integrated table: {display_label}")
    for legacy_label in LEGACY_HEURISTIC_DISPLAY_NAMES:
        assert_true(legacy_label not in display_values, f"legacy softened heuristic label must not appear: {legacy_label}")
    for label in UNMAPPED_LABELS:
        if label in {"부분음영형", "열화형"}:
            assert_true(label in display_values, f"unmapped heuristic label should stay visible: {label}")

    flat_text = "\n".join(
        [column for column in table_df.columns] + [normalize_text(value) for value in table_df.astype(str).stack().tolist()]
    )
    for pattern in FORBIDDEN_VALUE_PATTERNS:
        assert_true(re.search(pattern, flat_text) is None, f"integrated front-facing output exposed forbidden GPVS token: {pattern}")

    note_text = normalize_text(summary_row["note_ko"])
    assert_true("최종 front-facing table" in note_text, "summary note must mention final front-facing table")
    assert_true("evidence pack" in note_text, "summary note must mention evidence pack location for GPVS details")
    assert_true("heuristic" in note_text, "summary note must mention suspected-cause heuristic ranking")


if __name__ == "__main__":
    main()
