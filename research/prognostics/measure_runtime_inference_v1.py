#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_SCRIPT = REPO_ROOT / "app/run_realtime.py"
RUNTIME_CONFIG = REPO_ROOT / "config/runtime.yaml"
HANDOFF_BUILD_SCRIPT = REPO_ROOT / "research/prognostics/build_conalog_handoff_pack_v1.py"
HANDOFF_EXAMPLE_INPUT = REPO_ROOT / "delivery/conalog_handoff_v1/examples/input_sample.csv"
LATENCY_OUTPUT = REPO_ROOT / "_share/panel_day_engine_runtime_latency_report_v1.csv"
READINESS_OUTPUT = REPO_ROOT / "_share/panel_day_engine_runtime_readiness_summary_v1.csv"

LATENCY_COLS = ["measurement_scope", "metric_name", "metric_value", "unit", "note_ko"]
READINESS_COLS = [
    "runtime_mode_ko",
    "measured_flag",
    "latest_run_possible_flag",
    "include_experimental_supported_flag",
    "note_ko",
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def ensure_handoff_pack() -> None:
    if HANDOFF_EXAMPLE_INPUT.exists():
        return
    result = subprocess.run(
        [sys.executable, str(HANDOFF_BUILD_SCRIPT)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"failed to materialize handoff pack: {result.stderr or result.stdout}")


def run_timed(cmd: list[str]) -> tuple[float | None, subprocess.CompletedProcess[str]]:
    start = time.perf_counter()
    result = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    elapsed = time.perf_counter() - start
    if result.returncode != 0:
        return None, result
    return elapsed, result


def measurement_row(scope: str, name: str, value: float | None, note: str) -> dict[str, object]:
    return {
        "measurement_scope": scope,
        "metric_name": name,
        "metric_value": "" if value is None else round(value, 6),
        "unit": "seconds",
        "note_ko": note,
    }


def main() -> None:
    ensure_handoff_pack()
    latency_rows: list[dict[str, object]] = []

    help_elapsed, help_result = run_timed([sys.executable, str(RUNTIME_SCRIPT), "--help"])
    latency_rows.append(
        measurement_row(
            "runtime_cli_help",
            "elapsed_seconds",
            help_elapsed,
            "--help startup/argument parsing 시간임",
        )
    )

    dry_run_elapsed, dry_run_result = run_timed(
        [
            sys.executable,
            str(RUNTIME_SCRIPT),
            "--dry-run",
            "--input-root",
            ".",
            "--output-root",
            "/tmp/pvdiag_runtime_measure_dryrun",
            "--config",
            str(RUNTIME_CONFIG),
            "--mode",
            "once",
            "--include-experimental",
            "off",
        ]
    )
    latency_rows.append(
        measurement_row(
            "runtime_once_dry_run",
            "elapsed_seconds",
            dry_run_elapsed,
            "path/config 검증과 runtime plan 생성 시간을 측정하였음",
        )
    )

    poll_dry_run_elapsed, poll_dry_run_result = run_timed(
        [
            sys.executable,
            str(RUNTIME_SCRIPT),
            "--dry-run",
            "--input-root",
            ".",
            "--output-root",
            "/tmp/pvdiag_runtime_measure_poll",
            "--config",
            str(RUNTIME_CONFIG),
            "--mode",
            "poll",
            "--poll-seconds",
            "300",
            "--include-experimental",
            "off",
        ]
    )
    latency_rows.append(
        measurement_row(
            "runtime_poll_dry_run",
            "elapsed_seconds",
            poll_dry_run_elapsed,
            "poll wrapper 의 planning/startup 오버헤드만 측정하였음",
        )
    )

    once_elapsed: float | None = None
    once_experimental_elapsed: float | None = None
    latest_run_possible_flag = 0
    include_experimental_supported_flag = 0

    with tempfile.TemporaryDirectory(prefix="pvdiag_runtime_measure_input_") as input_dir, tempfile.TemporaryDirectory(
        prefix="pvdiag_runtime_measure_output_"
    ) as output_dir, tempfile.TemporaryDirectory(prefix="pvdiag_runtime_measure_output_ref_") as output_dir_ref:
        temp_input_root = Path(input_dir)
        shutil.copy2(HANDOFF_EXAMPLE_INPUT, temp_input_root / "input_sample.csv")

        once_elapsed, once_result = run_timed(
            [
                sys.executable,
                str(RUNTIME_SCRIPT),
                "--input-root",
                str(temp_input_root),
                "--output-root",
                str(Path(output_dir)),
                "--config",
                str(RUNTIME_CONFIG),
                "--mode",
                "once",
                "--include-experimental",
                "off",
            ]
        )
        latest_panel_path = Path(output_dir) / "latest/conalog_panel_result_v1.csv"
        latest_summary_path = Path(output_dir) / "latest/conalog_site_summary_v1.csv"
        latest_metadata_path = Path(output_dir) / "latest/conalog_run_metadata_v1.json"
        latest_run_possible_flag = int(
            once_elapsed is not None
            and latest_panel_path.exists()
            and latest_summary_path.exists()
            and latest_metadata_path.exists()
        )
        latency_rows.append(
            measurement_row(
                "runtime_once_foundation",
                "elapsed_seconds",
                once_elapsed,
                "stable mini-batch once wrapper 가 latest output 을 생성하는 시간을 측정하였음",
            )
        )

        once_experimental_elapsed, once_experimental_result = run_timed(
            [
                sys.executable,
                str(RUNTIME_SCRIPT),
                "--input-root",
                str(temp_input_root),
                "--output-root",
                str(Path(output_dir_ref)),
                "--config",
                str(RUNTIME_CONFIG),
                "--mode",
                "once",
                "--include-experimental",
                "on",
            ]
        )
        reference_sidecar_path = Path(output_dir_ref) / "latest/conalog_reference_sidecar_v1.csv"
        include_experimental_supported_flag = int(
            once_experimental_elapsed is not None and reference_sidecar_path.exists()
        )
        latency_rows.append(
            measurement_row(
                "runtime_once_foundation_experimental",
                "elapsed_seconds",
                once_experimental_elapsed,
                "experimental reference sidecar opt-in 경로의 wrapper 시간을 측정하였음",
            )
        )

    latency_rows.append(
        {
            "measurement_scope": "runtime_continuous_streaming",
            "metric_name": "elapsed_seconds",
            "metric_value": "",
            "unit": "seconds",
            "note_ko": "continuous streaming steady-state latency 는 이번 feasibility 단계에서 측정하지 않았음",
        }
    )

    latency_df = pd.DataFrame(latency_rows).reindex(columns=LATENCY_COLS)
    LATENCY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    latency_df.to_csv(LATENCY_OUTPUT, index=False, encoding="utf-8-sig")

    readiness_rows = [
        {
            "runtime_mode_ko": "once",
            "measured_flag": int(help_elapsed is not None and dry_run_elapsed is not None and once_elapsed is not None),
            "latest_run_possible_flag": latest_run_possible_flag,
            "include_experimental_supported_flag": include_experimental_supported_flag,
            "note_ko": "once mode 는 synthetic foundation 입력 기준 latest output 생성 가능성을 확인하였음",
        },
        {
            "runtime_mode_ko": "poll",
            "measured_flag": int(poll_dry_run_elapsed is not None),
            "latest_run_possible_flag": latest_run_possible_flag,
            "include_experimental_supported_flag": include_experimental_supported_flag,
            "note_ko": "poll mode 는 production daemon 이 아니라 single-wrapper feasibility 단계로만 측정하였음",
        },
    ]
    readiness_df = pd.DataFrame(readiness_rows).reindex(columns=READINESS_COLS)
    readiness_df.to_csv(READINESS_OUTPUT, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
