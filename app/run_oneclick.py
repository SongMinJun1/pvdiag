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
RUNTIME_LOG_NAME = "runtime_log_v1.jsonl"
FAILURE_LOG_NAME = "failure_log_v1.jsonl"
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


def append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def ensure_jsonl_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)


def latest_dir(output_root: Path) -> Path:
    return output_root / LATEST_DIRNAME


def latest_paths(output_root: Path) -> dict[str, Path]:
    current_latest_dir = latest_dir(output_root)
    return {
        "latest_dir": current_latest_dir,
        "runtime_log": current_latest_dir / RUNTIME_LOG_NAME,
        "failure_log": current_latest_dir / FAILURE_LOG_NAME,
        "plan": current_latest_dir / "oneclick_plan_v1.json",
    }


def validate_foundations(input_root: Path, output_root: Path, config_path: Path) -> None:
    ensure_directory(input_root, "input root")
    if not config_path.exists():
        raise FileNotFoundError(f"missing config: {config_path}")
    parse_simple_yaml(config_path)
    output_root.mkdir(parents=True, exist_ok=True)


def build_plan(args: argparse.Namespace) -> dict[str, object]:
    latest_output_dir = latest_dir(args.output_root.expanduser())
    steps = [
        "stable conalog runtime wrapper 실행",
        "stable latest output 구조 유지",
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


def log_event(path: Path, *, level: str, status: str, message_ko: str, extra: dict[str, object] | None = None) -> None:
    payload: dict[str, object] = {
        "logged_at_utc": now_utc(),
        "level": level,
        "status": status,
        "message_ko": message_ko,
    }
    if extra:
        payload.update(extra)
    append_jsonl(path, payload)


def short_runtime_failure_message(*, dry_run: bool) -> str:
    if dry_run:
        return "one-click dry-run 실패: runtime wrapper 실행을 확인하십시오."
    return "one-click 실행 실패: runtime wrapper 실행을 확인하십시오."


def short_report_failure_message() -> str:
    return "one-click 실행 실패: daily report 생성 단계를 확인하십시오."


def detail_text(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stderr or result.stdout or "").strip()


def record_failure(
    paths: dict[str, Path],
    *,
    stage: str,
    message_ko: str,
    detail_ko: str,
    plan: dict[str, object] | None = None,
) -> None:
    ensure_jsonl_file(paths["runtime_log"])
    ensure_jsonl_file(paths["failure_log"])
    log_event(
        paths["runtime_log"],
        level="error",
        status="failed",
        message_ko=message_ko,
        extra={"stage": stage},
    )
    append_jsonl(
        paths["failure_log"],
        {
            "logged_at_utc": now_utc(),
            "stage": stage,
            "message_ko": message_ko,
            "detail_ko": detail_ko,
        },
    )
    if plan is not None:
        failed_plan = dict(plan)
        failed_plan["status"] = "failed"
        failed_plan["operator_message_ko"] = message_ko
        write_json(paths["plan"], failed_plan)


def copy_exports(target_latest_dir: Path, include_experimental: str) -> None:
    target_latest_dir.mkdir(parents=True, exist_ok=True)
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
    paths = latest_paths(output_root)
    latest_output_dir = paths["latest_dir"]
    latest_output_dir.mkdir(parents=True, exist_ok=True)
    ensure_jsonl_file(paths["runtime_log"])
    ensure_jsonl_file(paths["failure_log"])
    log_event(
        paths["runtime_log"],
        level="info",
        status="started",
        message_ko="one-click orchestration 시작",
        extra={"dry_run": bool(args.dry_run), "include_experimental": args.include_experimental, "report": args.report},
    )

    if args.dry_run:
        optional_missing: list[str] = []
        if args.include_experimental == "on":
            optional_missing = [
                name for name, source_path in EXPERIMENTAL_EXPORTS.items() if not source_path.exists()
            ]
        plan["optional_missing_exports"] = optional_missing
        plan["report_builder_available_flag"] = int(DAILY_REPORT_BUILDER.exists())
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
            operator_message = short_runtime_failure_message(dry_run=True)
            record_failure(
                paths,
                stage="runtime_wrapper",
                message_ko=operator_message,
                detail_ko=detail_text(runtime_result),
                plan=plan,
            )
            print(operator_message, file=sys.stderr)
            return 1
        log_event(
            paths["runtime_log"],
            level="info",
            status="dry_run_plan",
            message_ko="one-click dry-run 계획 생성 완료",
            extra={
                "optional_missing_exports": optional_missing,
                "report_builder_available_flag": int(DAILY_REPORT_BUILDER.exists()),
            },
        )
        write_json(paths["plan"], plan)
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
        operator_message = short_runtime_failure_message(dry_run=False)
        record_failure(
            paths,
            stage="runtime_wrapper",
            message_ko=operator_message,
            detail_ko=detail_text(runtime_result),
            plan=plan,
        )
        print(operator_message, file=sys.stderr)
        return 1

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
            operator_message = short_report_failure_message()
            record_failure(
                paths,
                stage="daily_report",
                message_ko=operator_message,
                detail_ko=detail_text(report_result),
                plan=plan,
            )
            print(operator_message, file=sys.stderr)
            return 1

    log_event(
        paths["runtime_log"],
        level="info",
        status="completed",
        message_ko="one-click orchestration 완료",
        extra={"include_experimental": args.include_experimental, "report": args.report},
    )
    write_json(paths["plan"], plan)
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
