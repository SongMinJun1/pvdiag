#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HANDOFF_ENTRYPOINT = REPO_ROOT / "app/run_conalog_infer.py"
DEFAULT_STABLE_OUTPUT_SUBDIR = "latest"
DEFAULT_PANEL_RESULT_NAME = "conalog_panel_result_v1.csv"
DEFAULT_METADATA_NAME = "conalog_run_metadata_v1.json"
DEFAULT_REFERENCE_SIDECAR_NAME = "conalog_reference_sidecar_v1.csv"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the conalog runtime feasibility wrapper with stable mini-batch inference semantics."
    )
    parser.add_argument("--input-root", type=Path, required=True, help="Input root directory.")
    parser.add_argument("--output-root", type=Path, required=True, help="Output root directory.")
    parser.add_argument("--config", type=Path, required=True, help="Runtime YAML config path.")
    parser.add_argument("--mode", choices=["once", "poll"], default="once", help="Runtime mode. Defaults to once.")
    parser.add_argument("--poll-seconds", type=int, default=300, help="Planned poll interval in seconds. Defaults to 300.")
    parser.add_argument(
        "--include-experimental",
        choices=["off", "on"],
        default="off",
        help="Whether to emit experimental reference sidecar outputs. Defaults to off.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate config/paths and emit a runtime plan without executing a full inference run.")
    return parser.parse_args(argv)


def normalize_text(value: object) -> str:
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


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


def required_config(config: dict[str, str], path: Path) -> None:
    required = [
        "input_root",
        "output_root",
        "include_experimental",
        "poll_seconds",
        "stable_output_subdir",
        "runtime_log_name",
        "failure_log_name",
        "latest_summary_name",
        "handoff_config_path",
    ]
    missing = [key for key in required if not normalize_text(config.get(key))]
    if missing:
        raise RuntimeError(f"{path} missing required keys: {missing}")


def git_value(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return "git_unavailable"
    if result.returncode != 0:
        return "git_unavailable"
    value = result.stdout.strip()
    return value or "git_unavailable"


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_directory(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"missing {label}: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"{label} must be a directory: {path}")


def discover_candidate_csvs(input_root: Path, limit: int = 12) -> list[str]:
    candidates: list[str] = []
    for path in sorted(input_root.rglob("*.csv")):
        if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        candidates.append(str(path.relative_to(input_root)))
        if len(candidates) >= limit:
            break
    return candidates


def latest_paths(output_root: Path, config: dict[str, str]) -> dict[str, Path]:
    latest_dir = output_root / normalize_text(config.get("stable_output_subdir", DEFAULT_STABLE_OUTPUT_SUBDIR))
    return {
        "latest_dir": latest_dir,
        "panel_result": latest_dir / normalize_text(config.get("latest_panel_result_name", DEFAULT_PANEL_RESULT_NAME)),
        "site_summary": latest_dir / normalize_text(config["latest_summary_name"]),
        "metadata": latest_dir / normalize_text(config.get("latest_metadata_name", DEFAULT_METADATA_NAME)),
        "runtime_log": latest_dir / normalize_text(config["runtime_log_name"]),
        "failure_log": latest_dir / normalize_text(config["failure_log_name"]),
        "reference_sidecar": latest_dir / normalize_text(
            config.get("latest_reference_sidecar_name", DEFAULT_REFERENCE_SIDECAR_NAME)
        ),
    }


def append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def ensure_jsonl_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_metadata(
    *,
    runtime_mode: str,
    poll_seconds: int,
    input_root: Path,
    output_root: Path,
    config_path: Path,
    handoff_config_path: Path | None,
    include_experimental: str,
    dry_run: bool,
    note_ko: str,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "generated_at_utc": now_utc(),
        "git_branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
        "git_head": git_value(["rev-parse", "HEAD"]),
        "runtime_mode": runtime_mode,
        "poll_seconds": poll_seconds,
        "config_path": str(config_path),
        "handoff_config_path": str(handoff_config_path) if handoff_config_path is not None else "",
        "input_root": str(input_root),
        "output_root": str(output_root),
        "include_experimental": include_experimental,
        "dry_run": dry_run,
        "note_ko": note_ko,
    }
    if extra:
        payload.update(extra)
    return payload


def load_handoff_config(path: Path) -> dict[str, str]:
    config = parse_simple_yaml(path)
    required = ["input_csv_name", "panel_result_name", "site_summary_name", "metadata_name", "experimental_reference_name"]
    missing = [key for key in required if not normalize_text(config.get(key))]
    if missing:
        raise RuntimeError(f"{path} missing handoff keys: {missing}")
    return config


def log_runtime_event(path: Path, *, level: str, mode: str, status: str, message_ko: str, extra: dict[str, object] | None = None) -> None:
    payload: dict[str, object] = {
        "logged_at_utc": now_utc(),
        "level": level,
        "runtime_mode": mode,
        "status": status,
        "message_ko": message_ko,
    }
    if extra:
        payload.update(extra)
    append_jsonl(path, payload)


def run_handoff(
    *,
    input_root: Path,
    stage_output_root: Path,
    handoff_config_path: Path,
    include_experimental: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(HANDOFF_ENTRYPOINT),
            "--input-root",
            str(input_root),
            "--output-root",
            str(stage_output_root),
            "--config",
            str(handoff_config_path),
            "--include-experimental",
            include_experimental,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def copy_required_output(src: Path, dst: Path, label: str) -> None:
    if not src.exists():
        raise FileNotFoundError(f"missing downstream {label}: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def execute_once(
    *,
    input_root: Path,
    output_root: Path,
    config_path: Path,
    config: dict[str, str],
    handoff_config_path: Path,
    include_experimental: str,
    runtime_mode: str,
    poll_seconds: int,
) -> int:
    latest = latest_paths(output_root, config)
    latest["latest_dir"].mkdir(parents=True, exist_ok=True)
    ensure_jsonl_file(latest["runtime_log"])
    ensure_jsonl_file(latest["failure_log"])

    handoff_config = load_handoff_config(handoff_config_path)
    expected_input_csv = input_root / normalize_text(handoff_config["input_csv_name"])
    if not expected_input_csv.exists():
        raise FileNotFoundError(f"missing runtime input csv for once-mode inference: {expected_input_csv}")

    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="conalog_runtime_stage_", dir=str(output_root)) as tmp_dir:
        stage_output_root = Path(tmp_dir)
        result = run_handoff(
            input_root=input_root,
            stage_output_root=stage_output_root,
            handoff_config_path=handoff_config_path,
            include_experimental=include_experimental,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "run_conalog_infer.py failed")

        stage_output_dir = stage_output_root / normalize_text(handoff_config.get("output_subdir", "output"))
        copy_required_output(
            stage_output_dir / normalize_text(handoff_config["panel_result_name"]),
            latest["panel_result"],
            "panel result",
        )
        copy_required_output(
            stage_output_dir / normalize_text(handoff_config["site_summary_name"]),
            latest["site_summary"],
            "site summary",
        )
        if include_experimental == "on":
            copy_required_output(
                stage_output_dir / normalize_text(handoff_config["experimental_reference_name"]),
                latest["reference_sidecar"],
                "experimental reference sidecar",
            )

    elapsed = time.perf_counter() - start
    metadata = build_metadata(
        runtime_mode=runtime_mode,
        poll_seconds=poll_seconds,
        input_root=input_root,
        output_root=output_root,
        config_path=config_path,
        handoff_config_path=handoff_config_path,
        include_experimental=include_experimental,
        dry_run=False,
        note_ko=(
            "conalog runtime feasibility foundation 결과임. stable latest output 이 우선이며, "
            "GPVS 는 reference-only, heuristic 은 triage-only 로만 분리함."
        ),
        extra={
            "run_status_ko": "latest_run_completed",
            "latest_run_possible_flag": 1,
            "experimental_sidecar_emitted_flag": int(include_experimental == "on"),
            "elapsed_seconds": round(elapsed, 6),
        },
    )
    write_json(latest["metadata"], metadata)
    log_runtime_event(
        latest["runtime_log"],
        level="info",
        mode=runtime_mode,
        status="completed",
        message_ko="runtime latest output 생성 완료",
        extra={"elapsed_seconds": round(elapsed, 6), "include_experimental": include_experimental},
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_root = args.input_root.resolve()
    output_root = args.output_root.expanduser()
    config_path = args.config.resolve()
    fallback_latest_dir = output_root / DEFAULT_STABLE_OUTPUT_SUBDIR
    fallback_runtime_log = fallback_latest_dir / "runtime_log_v1.jsonl"
    fallback_failure_log = fallback_latest_dir / "failure_log_v1.jsonl"
    fallback_metadata = fallback_latest_dir / DEFAULT_METADATA_NAME

    try:
        output_root.mkdir(parents=True, exist_ok=True)
        ensure_directory(input_root, "input root")
        config = parse_simple_yaml(config_path)
        required_config(config, config_path)
        handoff_config_path = (REPO_ROOT / normalize_text(config["handoff_config_path"])).resolve()
        if not handoff_config_path.exists():
            raise FileNotFoundError(f"missing handoff config dependency: {handoff_config_path}")
        latest = latest_paths(output_root, config)
        latest["latest_dir"].mkdir(parents=True, exist_ok=True)
        ensure_jsonl_file(latest["runtime_log"])
        ensure_jsonl_file(latest["failure_log"])
        poll_seconds = args.poll_seconds if args.poll_seconds > 0 else int(normalize_text(config["poll_seconds"]) or "300")
        if poll_seconds <= 0:
            raise RuntimeError("poll_seconds must be positive")

        if args.dry_run:
            handoff_input_csv = ""
            handoff_input_found_flag = False
            handoff_cfg = load_handoff_config(handoff_config_path)
            handoff_input_csv = str(input_root / normalize_text(handoff_cfg["input_csv_name"]))
            handoff_input_found_flag = Path(handoff_input_csv).exists()
            metadata = build_metadata(
                runtime_mode=args.mode,
                poll_seconds=poll_seconds,
                input_root=input_root,
                output_root=output_root,
                config_path=config_path,
                handoff_config_path=handoff_config_path,
                include_experimental=args.include_experimental,
                dry_run=True,
                note_ko=(
                    "runtime dry-run 계획임. once/poll wrapper 와 latest 경로를 검증하며, "
                    "full streaming readiness 를 주장하지 않는 feasibility 단계임."
                ),
                extra={
                    "run_status_ko": "dry_run_plan",
                    "latest_run_possible_flag": 0,
                    "planned_latest_dir": str(latest["latest_dir"]),
                    "expected_handoff_input_csv": handoff_input_csv,
                    "expected_handoff_input_found_flag": handoff_input_found_flag,
                    "candidate_input_csvs": discover_candidate_csvs(input_root),
                    "planned_outputs": [
                        str(latest["metadata"]),
                        str(latest["runtime_log"]),
                        str(latest["failure_log"]),
                        str(latest["panel_result"]),
                        str(latest["site_summary"]),
                    ]
                    + ([str(latest["reference_sidecar"])] if args.include_experimental == "on" else []),
                },
            )
            write_json(latest["metadata"], metadata)
            log_runtime_event(
                latest["runtime_log"],
                level="info",
                mode=args.mode,
                status="dry_run_plan",
                message_ko="runtime dry-run 계획 생성 완료",
                extra={"include_experimental": args.include_experimental, "poll_seconds": poll_seconds},
            )
            print(
                json.dumps(
                    {
                        "dry_run": True,
                        "runtime_mode": args.mode,
                        "latest_dir": str(latest["latest_dir"]),
                        "include_experimental": args.include_experimental,
                    },
                    ensure_ascii=False,
                )
            )
            return 0

        if not handoff_config_path.exists():
            raise FileNotFoundError(f"missing handoff config dependency: {handoff_config_path}")

        if args.mode == "once":
            return execute_once(
                input_root=input_root,
                output_root=output_root,
                config_path=config_path,
                config=config,
                handoff_config_path=handoff_config_path,
                include_experimental=args.include_experimental,
                runtime_mode="once",
                poll_seconds=poll_seconds,
            )

        return execute_once(
            input_root=input_root,
            output_root=output_root,
            config_path=config_path,
            config=config,
            handoff_config_path=handoff_config_path,
            include_experimental=args.include_experimental,
            runtime_mode="poll",
            poll_seconds=poll_seconds,
        )
    except Exception as exc:
        fallback_latest_dir.mkdir(parents=True, exist_ok=True)
        ensure_jsonl_file(fallback_runtime_log)
        ensure_jsonl_file(fallback_failure_log)
        message = normalize_text(exc) or exc.__class__.__name__
        metadata = build_metadata(
            runtime_mode=args.mode,
            poll_seconds=args.poll_seconds,
            input_root=input_root,
            output_root=output_root,
            config_path=config_path,
            handoff_config_path=None,
            include_experimental=args.include_experimental,
            dry_run=bool(args.dry_run),
            note_ko="runtime feasibility foundation 실패 기록임. failure log 와 config/path 의존성을 먼저 확인해야 함.",
            extra={
                "run_status_ko": "failed",
                "latest_run_possible_flag": 0,
                "failure_message_ko": message,
            },
        )
        write_json(fallback_metadata, metadata)
        log_runtime_event(
            fallback_runtime_log,
            level="error",
            mode=args.mode,
            status="failed",
            message_ko=message,
            extra={"include_experimental": args.include_experimental},
        )
        append_jsonl(
            fallback_failure_log,
            {
                "logged_at_utc": now_utc(),
                "runtime_mode": args.mode,
                "stage": "runtime_wrapper",
                "message_ko": message,
            },
        )
        print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
