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
RUNNER_SCRIPT = REPO_ROOT / "research/prognostics/run_fault_validation_v1.py"
SMOKE_SCRIPT = REPO_ROOT / "research/prognostics/smoke_test_fault_validation_v1.py"

REQUIRED_COLS = [
    "case_id",
    "case_type",
    "validation_axis_ko",
    "input_scope",
    "expected_output_ko",
    "actual_output_ko",
    "pass_flag",
    "note_ko",
]

WATCH_FILENAMES = [
    "panel_day_engine_panel_multiaxis_verdict_v1.csv",
    "panel_day_engine_gpvs_evidence_pack_v1.csv",
    "panel_day_engine_cause_candidate_heuristics_v1.csv",
]

REQUIRED_SURROGATE_IDS = {
    "surrogate::부분음영형",
    "surrogate::접속불량·부분개방형",
    "surrogate::센서·계측피드백이상형",
    "surrogate::제어응답이상형",
    "surrogate::gpvs_attach_on_off_fallback",
    "surrogate::sparse_conalog",
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
    py_compile.compile(str(RUNNER_SCRIPT), doraise=True)
    py_compile.compile(str(SMOKE_SCRIPT), doraise=True)
    with tempfile.TemporaryDirectory(prefix="fault_validation_smoke_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        output_dir = tmp_root / "outputs/validation"
        with stage_missing_share_fixtures(tmp_root, WATCH_FILENAMES):
            watch_outputs = [tmp_root / "_share" / name for name in WATCH_FILENAMES]
            before_signatures = {path: file_signature(path) for path in watch_outputs}

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER_SCRIPT),
                    "--root",
                    str(tmp_root),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )
            assert_true(result.returncode == 0, f"validation runner failed: {result.stderr or result.stdout}")

            output_csv = output_dir / "fault_validation_report_v1.csv"
            output_md = output_dir / "fault_validation_report_v1.md"
            assert_true(output_csv.exists(), f"missing validation csv: {output_csv}")
            assert_true(output_md.exists(), f"missing validation md: {output_md}")

            report_df = pd.read_csv(output_csv, low_memory=False, encoding="utf-8-sig")
            missing_cols = [column for column in REQUIRED_COLS if column not in report_df.columns]
            assert_true(not missing_cols, f"validation csv missing columns: {missing_cols}")
            assert_true(report_df["validation_axis_ko"].map(normalize_text).ne("").all(), "validation_axis_ko must be populated for all rows")

            core_df = report_df.loc[report_df["case_type"].astype(str).str.startswith("core_")].copy()
            core_panel_ids = {
                case_id.split("::")[1]
                for case_id in core_df["case_id"].astype(str).tolist()
                if case_id.startswith("core::") and len(case_id.split("::")) >= 3
            }
            assert_true(len(core_panel_ids) == 6, f"core 6 fault panels must appear, found {len(core_panel_ids)}")

            surrogate_ids = set(report_df["case_id"].astype(str).tolist())
            missing_surrogates = sorted(REQUIRED_SURROGATE_IDS - surrogate_ids)
            assert_true(not missing_surrogates, f"missing surrogate rows: {missing_surrogates}")
            surrogate_df = report_df.loc[report_df["case_type"].astype(str).str.startswith("surrogate_")].copy()
            assert_true(len(surrogate_df) == 6, f"expected 6 surrogate rows, found {len(surrogate_df)}")

            action_note_df = report_df.loc[report_df["case_type"].astype(str).eq("core_heuristic_action_note")].copy()
            assert_true(len(action_note_df) == 6, f"expected 6 heuristic action-note rows, found {len(action_note_df)}")

            c429_row = action_note_df.loc[action_note_df["case_id"].astype(str).str.contains("c42997a6-5881-47e7-9035-7de8a2673b54.1.1")].copy()
            assert_true(len(c429_row) == 1, "expected c429 heuristic action-note validation row")
            assert_true(
                normalize_text(c429_row.iloc[0]["actual_output_ko"]) == "센서·피드백형과 접속·부분개방형을 함께 우선 점검",
                "c429 action-note wording mismatch",
            )

            row_70ad = action_note_df.loc[action_note_df["case_id"].astype(str).str.contains("70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4")].copy()
            assert_true(len(row_70ad) == 1, "expected 70ad heuristic action-note validation row")
            assert_true(
                normalize_text(row_70ad.iloc[0]["actual_output_ko"]) == "열화형, 센서·피드백형, 다이오드·서브스트링형을 함께 우선 점검",
                "70ad action-note wording must stay aligned with current top-ranked competition order",
            )

            assert_true(report_df["pass_flag"].astype(int).isin([0, 1]).all(), "pass_flag must stay binary")
            assert_true(report_df["note_ko"].map(normalize_text).ne("").all(), "note_ko must be populated for all rows")

            md_text = output_md.read_text(encoding="utf-8")
            assert_true("Fault Validation Report V1" in md_text, "markdown report title missing")
            assert_true("Surrogate Coverage Matrix" in md_text, "markdown report must contain surrogate coverage matrix section")
            assert_true("Known Limitations" in md_text, "markdown report must contain known limitations section")
            assert_true("skip cases: 0" in md_text, "markdown report must summarize skip count")
            assert_true("framework validation 우선 단계" in md_text, "markdown report must describe framework-first limitation")

            after_signatures = {path: file_signature(path) for path in watch_outputs}
            for path in watch_outputs:
                assert_true(before_signatures[path] == after_signatures[path], f"frozen production output changed: {path}")


if __name__ == "__main__":
    main()
