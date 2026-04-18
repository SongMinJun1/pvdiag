#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ENTRYPOINT = REPO_ROOT / "app/run_realtime.py"
DAILY_REPORT_BUILDER = REPO_ROOT / "research/prognostics/build_daily_report_v1.py"
LATEST_DIRNAME = "latest"
FROZEN_EXPORTS = {
    "integrated_result_table_v1.csv": REPO_ROOT / "_share/panel_day_engine_integrated_result_table_v1.csv",
    "integrated_result_summary_v1.csv": REPO_ROOT / "_share/panel_day_engine_integrated_result_summary_v1.csv",
}
EXPERIMENTAL_EXPORTS = {
    "gpvs_evidence_pack_v1.csv": REPO_ROOT / "_share/panel_day_engine_gpvs_evidence_pack_v1.csv",
    "cause_candidate_heuristics_v1.csv": REPO_ROOT / "_share/panel_day_engine_cause_candidate_heuristics_v1.csv",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the conalog one-click operation foundation with stable outputs and optional report generation."
    )
    parser.add_argument("--input-root", type=Path, required=True, help="Input root directory.")
    parser.add_argument("--output-root", type=Path, required=True, help="Output root directory.")
    parser.add_argument("--config", type=Path, required=True, help="Runtime config path.")
    parser.add_argument(
        "--include-experimental",
        choices=["off", "on"],
        default="off",
        help="Whether to include experimental/reference exports. Defaults to off.",
    )
    parser.add_argument(
        "--report",
        choices=["off", "on"],
        default="on",
        help="Whether to generate daily report markdown. Defaults to on.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate config/paths and emit an execution plan without executing the full flow.")
    return parser.parse_args(argv)


def normalize_text(value: object) -> str:
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_simple_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        raise FileNotFoundError(f"missing config: {path}")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            raise RuntimeError(f"invalid config line: {raw_line}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("'").strip('"')
    return data


def ensure_directory(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"missing {label}: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"{label} must be a directory: {path}")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)


def latest_dir(output_root: Path) -> Path:
    return output_root / LATEST_DIRNAME


def validate_foundations(input_root: Path, output_root: Path, config_path: Path) -> None:
    ensure_directory(input_root, "input root")
    if not config_path.exists():
        raise FileNotFoundError(f"missing config: {config_path}")
    parse_simple_yaml(config_path)
    output_root.mkdir(parents=True, exist_ok=True)
    for path in FROZEN_EXPORTS.values():
        if not path.exists():
            raise FileNotFoundError(f"missing frozen export dependency: {path}")


def build_plan(args: argparse.Namespace) -> dict[str, object]:
    latest_output_dir = latest_dir(args.output_root.expanduser())
    steps = [
        "stable conalog runtime wrapper 실행",
        "frozen integrated result snapshot export 복사",
    ]
    if args.include_experimental == "on":
        steps.append("experimental/reference snapshot export 복사")
    if args.report == "on":
        steps.append("daily report markdown 생성")
    return {
        "generated_at_utc": now_utc(),
        "input_root": str(args.input_root.resolve()),
        "output_root": str(args.output_root.expanduser()),
        "config": str(args.config.resolve()),
        "include_experimental": args.include_experimental,
        "report": args.report,
        "dry_run": bool(args.dry_run),
        "latest_dir": str(latest_output_dir),
        "steps": steps,
        "note_ko": (
            "one-click foundation plan 이며 panel multiaxis verdict 를 primary 로 유지한다. "
            "conalog 는 direct operational interpretation layer, GPVS 는 reference-only, heuristic 은 triage-only 로만 취급한다."
        ),
    }


def copy_exports(target_latest_dir: Path, include_experimental: str) -> None:
    target_latest_dir.mkdir(parents=True, exist_ok=True)
    for target_name, source_path in FROZEN_EXPORTS.items():
        shutil.copy2(source_path, target_latest_dir / target_name)
    if include_experimental == "on":
        for target_name, source_path in EXPERIMENTAL_EXPORTS.items():
            shutil.copy2(source_path, target_latest_dir / target_name)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_root = args.input_root.resolve()
    output_root = args.output_root.expanduser()
    config_path = args.config.resolve()

    validate_foundations(input_root, output_root, config_path)
    plan = build_plan(args)
    latest_output_dir = latest_dir(output_root)
    latest_output_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        runtime_result = run(
            [
                sys.executable,
                str(RUNTIME_ENTRYPOINT),
                "--dry-run",
                "--input-root",
                str(input_root),
                "--output-root",
                str(output_root),
                "--config",
                str(config_path),
                "--mode",
                "once",
                "--include-experimental",
                args.include_experimental,
            ]
        )
        if runtime_result.returncode != 0:
            raise SystemExit(runtime_result.stderr or runtime_result.stdout)
        write_json(latest_output_dir / "oneclick_plan_v1.json", plan)
        print(json.dumps(plan, ensure_ascii=False))
        return 0

    runtime_result = run(
        [
            sys.executable,
            str(RUNTIME_ENTRYPOINT),
            "--input-root",
            str(input_root),
            "--output-root",
            str(output_root),
            "--config",
            str(config_path),
            "--mode",
            "once",
            "--include-experimental",
            args.include_experimental,
        ]
    )
    if runtime_result.returncode != 0:
        raise SystemExit(runtime_result.stderr or runtime_result.stdout)

    copy_exports(latest_output_dir, args.include_experimental)

    if args.report == "on":
        report_result = run(
            [
                sys.executable,
                str(DAILY_REPORT_BUILDER),
                "--output-root",
                str(output_root),
            ]
        )
        if report_result.returncode != 0:
            raise SystemExit(report_result.stderr or report_result.stdout)

    write_json(latest_output_dir / "oneclick_plan_v1.json", plan)
    print(
        json.dumps(
            {
                "status": "completed",
                "latest_dir": str(latest_output_dir),
                "include_experimental": args.include_experimental,
                "report": args.report,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
