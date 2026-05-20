#!/usr/bin/env python3
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_SCRIPT = REPO_ROOT / "app/run_backfill.py"
BUILD_SCRIPT = REPO_ROOT / "research/prognostics/build_panel_day_engine_historical_backfill_v1.py"
SMOKE_SCRIPT = REPO_ROOT / "research/prognostics/smoke_test_panel_day_engine_historical_backfill_v1.py"

REQUIRED_OUTPUTS = [
    "panel_result_v1.csv",
    "site_day_summary_v1.csv",
    "period_summary_v1.csv",
    "cause_candidate_distribution_v1.csv",
    "run_metadata_v1.json",
    "error_log_v1.csv",
]

REQUIRED_METADATA_FIELDS = [
    "run_id",
    "generated_at_utc",
    "git_branch",
    "git_head",
    "site_filter",
    "start_date",
    "end_date",
    "gpvs_attach_flag",
    "report_flag",
    "mode",
    "note_ko",
]

PANEL_RESULT_REQUIRED_COLS = [
    "site",
    "panel_id",
    "target_window_start_date",
    "target_window_end_date",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "conalog_원인군_ko",
    "1순위_의심원인_ko",
    "2순위_의심원인_ko",
    "3순위_의심원인_ko",
    "result_source_ko",
    "note_ko",
]

WATCH_OUTPUTS = [
    REPO_ROOT / "_share/panel_day_engine_panel_multiaxis_verdict_v1.csv",
    REPO_ROOT / "_share/panel_day_engine_gpvs_evidence_pack_v1.csv",
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


def file_signature(path: Path) -> tuple[int, int] | None:
    if not path.exists():
        return None
    stat = path.stat()
    return (stat.st_size, stat.st_mtime_ns)


def main() -> None:
    py_compile.compile(str(REPO_ROOT / "pv_ae/panel_day_engine.py"), doraise=True)
    py_compile.compile(str(APP_SCRIPT), doraise=True)
    py_compile.compile(str(BUILD_SCRIPT), doraise=True)
    py_compile.compile(str(SMOKE_SCRIPT), doraise=True)

    help_result = run([sys.executable, str(APP_SCRIPT), "--help"])
    assert_true(help_result.returncode == 0, f"--help failed: {help_result.stderr or help_result.stdout}")
    help_text = help_result.stdout
    for token in [
        "--site",
        "--start-date",
        "--end-date",
        "--input-root",
        "--output-root",
        "--gpvs-attach",
        "--report",
        "--mode",
        "--dry-run",
    ]:
        assert_true(token in help_text, f"--help must expose {token}")

    before_signatures = {path: file_signature(path) for path in WATCH_OUTPUTS}

    with tempfile.TemporaryDirectory(prefix="pvdiag_backfill_smoke_") as tmp_dir:
        output_root = Path(tmp_dir) / "runs"
        dry_run_result = run(
            [
                sys.executable,
                str(APP_SCRIPT),
                "--dry-run",
                "--site",
                "conalog",
                "--start-date",
                "2024-01-01",
                "--end-date",
                "2024-01-07",
                "--input-root",
                ".",
                "--output-root",
                str(output_root),
                "--gpvs-attach",
                "on",
                "--report",
                "off",
                "--mode",
                "operational",
            ]
        )
        assert_true(dry_run_result.returncode == 0, f"dry-run failed: {dry_run_result.stderr or dry_run_result.stdout}")

        run_dirs = [path for path in output_root.iterdir() if path.is_dir()]
        assert_true(len(run_dirs) == 1, f"expected one backfill run directory, found {len(run_dirs)}")
        run_dir = run_dirs[0]

        for output_name in REQUIRED_OUTPUTS:
            assert_true((run_dir / output_name).exists(), f"missing required output: {run_dir / output_name}")

        metadata = json.loads((run_dir / "run_metadata_v1.json").read_text(encoding="utf-8"))
        for field in REQUIRED_METADATA_FIELDS:
            assert_true(field in metadata, f"metadata missing field: {field}")
            assert_true(normalize_text(metadata[field]) != "", f"metadata field must be populated: {field}")
        assert_true(metadata["site_filter"] == "conalog", "metadata site_filter mismatch")
        assert_true(metadata["start_date"] == "2024-01-01", "metadata start_date mismatch")
        assert_true(metadata["end_date"] == "2024-01-07", "metadata end_date mismatch")
        assert_true(metadata["gpvs_attach_flag"] == "on", "metadata gpvs_attach_flag mismatch")
        assert_true(metadata["report_flag"] == "off", "metadata report_flag mismatch")
        assert_true(metadata["mode"] == "operational", "metadata mode mismatch")
        assert_true(metadata.get("dry_run") is True, "metadata dry_run flag must be true for dry-run")

        panel_result_df = pd.read_csv(run_dir / "panel_result_v1.csv", low_memory=False, encoding="utf-8-sig")
        missing_panel_cols = [column for column in PANEL_RESULT_REQUIRED_COLS if column not in panel_result_df.columns]
        assert_true(not missing_panel_cols, f"panel_result missing columns: {missing_panel_cols}")
        assert_true(panel_result_df["site"].map(normalize_text).isin(["conalog"]).all(), "panel_result dry-run must stay site-filtered")
        assert_true(
            panel_result_df["result_source_ko"].map(normalize_text).eq("stable_snapshot_preview_dry_run").all(),
            "panel_result result_source_ko must show dry-run preview source",
        )

        site_day_df = pd.read_csv(run_dir / "site_day_summary_v1.csv", low_memory=False, encoding="utf-8-sig")
        assert_true(len(site_day_df) == 7, f"site_day_summary must contain 7 rows for requested date range, found {len(site_day_df)}")
        assert_true(site_day_df["site"].map(normalize_text).eq("conalog").all(), "site_day_summary must stay site-filtered")
        assert_true(site_day_df["run_status_ko"].map(normalize_text).eq("dry_run_plan").all(), "site_day_summary must show dry_run_plan")

        period_df = pd.read_csv(run_dir / "period_summary_v1.csv", low_memory=False, encoding="utf-8-sig")
        assert_true(len(period_df) >= 1, "period_summary must not be empty")
        assert_true(int(period_df.iloc[-1]["requested_day_count"]) == 7, "period_summary requested_day_count mismatch")

        cause_df = pd.read_csv(run_dir / "cause_candidate_distribution_v1.csv", low_memory=False, encoding="utf-8-sig")
        if not cause_df.empty:
            assert_true(cause_df["distribution_basis_ko"].map(normalize_text).eq("top1_preview").all(), "cause distribution basis mismatch")

        error_df = pd.read_csv(run_dir / "error_log_v1.csv", low_memory=False, encoding="utf-8-sig")
        assert_true(set(error_df.columns) == set(["logged_at_utc", "level", "site", "stage_ko", "code", "message_ko"]), "error_log schema mismatch")

    after_signatures = {path: file_signature(path) for path in WATCH_OUTPUTS}
    for path in WATCH_OUTPUTS:
        assert_true(before_signatures[path] == after_signatures[path], f"official output changed outside backfill output root: {path}")


if __name__ == "__main__":
    main()
