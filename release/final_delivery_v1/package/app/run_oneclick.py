#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import traceback
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ENTRYPOINT = REPO_ROOT / "app/run_realtime.py"
LATEST_DIRNAME = "latest"
TEMPLATE_PATH = REPO_ROOT / "oneclick/daily_report_template.md"
INTEGRATED_TABLE_NAME = "integrated_result_table_v1.csv"
INTEGRATED_SUMMARY_NAME = "integrated_result_summary_v1.csv"
DAILY_REPORT_NAME = "daily_report_v1.md"
GPVS_REFERENCE_EXPORT_NAME = "gpvs_reference_export_v1.csv"
CAUSE_TRIAGE_EXPORT_NAME = "cause_candidate_triage_export_v1.csv"

PANEL_RESULT_NAME = "conalog_panel_result_v1.csv"
SITE_SUMMARY_NAME = "conalog_site_summary_v1.csv"
METADATA_NAME = "conalog_run_metadata_v1.json"
RUNTIME_LOG_NAME = "runtime_log_v1.jsonl"
FAILURE_LOG_NAME = "failure_log_v1.jsonl"
REFERENCE_SIDECAR_NAME = "conalog_reference_sidecar_v1.csv"

INTEGRATED_TABLE_COLS = [
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
INTEGRATED_SUMMARY_COLS = [
    "total_panel_count",
    "fault_panel_count",
    "non_fault_or_unresolved_count",
    "gpvs_core_reference_count",
    "gpvs_auxiliary_reference_count",
    "gpvs_not_used_count",
    "note_ko",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the package-local one-click conalog flow with stable outputs and optional experimental sidecars."
    )
    parser.add_argument("--input-root", type=Path, required=True, help="Input root directory.")
    parser.add_argument("--output-root", type=Path, required=True, help="Output root directory.")
    parser.add_argument("--config", type=Path, required=True, help="Runtime config path.")
    parser.add_argument("--include-experimental", choices=["off", "on"], default="off")
    parser.add_argument("--report", choices=["off", "on"], default="on")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_directory(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"missing {label}: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"{label} must be a directory: {path}")


def latest_dir(output_root: Path) -> Path:
    return output_root / LATEST_DIRNAME


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


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl_messages(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"message_ko": f"invalid jsonl line: {line}"})
    return rows


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def build_plan(args: argparse.Namespace) -> dict[str, object]:
    return {
        "generated_at_utc": now_utc(),
        "input_root": str(args.input_root.resolve()),
        "output_root": str(args.output_root.expanduser()),
        "config": str(args.config.resolve()),
        "include_experimental": args.include_experimental,
        "report": args.report,
        "dry_run": bool(args.dry_run),
        "note_ko": (
            "package-local one-click plan 임. panel multiaxis verdict 를 primary 로 유지하고, "
            "conalog 는 direct operational interpretation layer, GPVS 는 reference-only, heuristic 은 triage-only 로만 취급함."
        ),
    }


def latest_paths(output_root: Path) -> dict[str, Path]:
    current_latest_dir = latest_dir(output_root)
    return {
        "latest_dir": current_latest_dir,
        "runtime_log": current_latest_dir / RUNTIME_LOG_NAME,
        "failure_log": current_latest_dir / FAILURE_LOG_NAME,
        "plan": current_latest_dir / "oneclick_plan_v1.json",
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


def run_runtime(args: argparse.Namespace) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(RUNTIME_ENTRYPOINT),
        "--input-root",
        str(args.input_root.resolve()),
        "--output-root",
        str(args.output_root.expanduser()),
        "--config",
        str(args.config.resolve()),
        "--mode",
        "once",
        "--include-experimental",
        args.include_experimental,
    ]
    if args.dry_run:
        cmd.append("--dry-run")
    return subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)


def build_integrated_table(panel_df: pd.DataFrame, sidecar_df: pd.DataFrame | None) -> pd.DataFrame:
    sidecar_lookup: dict[tuple[str, str], dict[str, str]] = {}
    if sidecar_df is not None:
        for row in sidecar_df.to_dict(orient="records"):
            key = (normalize_text(row.get("site")), normalize_text(row.get("panel_id")))
            sidecar_lookup[key] = {column: normalize_text(value) for column, value in row.items()}
    rows: list[dict[str, str]] = []
    for row in panel_df.to_dict(orient="records"):
        key = (normalize_text(row.get("site")), normalize_text(row.get("panel_id")))
        sidecar_row = sidecar_lookup.get(key, {})
        rows.append(
            {
                "site": normalize_text(row.get("site")),
                "panel_id": normalize_text(row.get("panel_id")),
                "패널고장여부_ko": normalize_text(row.get("패널고장여부_ko")),
                "사건유형_ko": normalize_text(row.get("사건유형_ko")),
                "최종고장양상_ko": normalize_text(row.get("최종고장양상_ko")),
                "커널로그_원인군_ko": normalize_text(row.get("conalog_원인군_ko")),
                "1순위_의심원인_ko": normalize_text(sidecar_row.get("1순위_의심원인_ko")),
                "2순위_의심원인_ko": normalize_text(sidecar_row.get("2순위_의심원인_ko")),
                "3순위_의심원인_ko": normalize_text(sidecar_row.get("3순위_의심원인_ko")),
            }
        )
    return pd.DataFrame(rows).reindex(columns=INTEGRATED_TABLE_COLS)


def build_integrated_summary(panel_df: pd.DataFrame) -> pd.DataFrame:
    total = int(len(panel_df))
    fault_count = int(panel_df["패널고장여부_ko"].map(normalize_text).eq("고장").sum())
    row = {
        "total_panel_count": total,
        "fault_panel_count": fault_count,
        "non_fault_or_unresolved_count": total - fault_count,
        "gpvs_core_reference_count": 0,
        "gpvs_auxiliary_reference_count": 0,
        "gpvs_not_used_count": total,
        "note_ko": (
            "package-local executable hotfix 는 stable integrated table schema 를 유지하였음. "
            "GPVS 는 reference-only 이며 stable default summary count 로 승격하지 않았음."
        ),
    }
    return pd.DataFrame([row]).reindex(columns=INTEGRATED_SUMMARY_COLS)


def write_optional_experimental_exports(latest_output_dir: Path, sidecar_df: pd.DataFrame | None) -> None:
    if sidecar_df is None or sidecar_df.empty:
        return
    gpvs_df = sidecar_df[
        ["site", "panel_id", "GPVS_참조정책_ko", "GPVS_참조메모_ko", "note_ko"]
    ].copy()
    gpvs_df.to_csv(latest_output_dir / GPVS_REFERENCE_EXPORT_NAME, index=False, encoding="utf-8-sig")
    cause_df = sidecar_df[
        ["site", "panel_id", "1순위_의심원인_ko", "2순위_의심원인_ko", "3순위_의심원인_ko", "heuristic_운영정책_ko", "note_ko"]
    ].copy()
    cause_df.to_csv(latest_output_dir / CAUSE_TRIAGE_EXPORT_NAME, index=False, encoding="utf-8-sig")


def format_bullets(items: list[str], empty_text: str) -> str:
    clean_items = [item for item in items if normalize_text(item)]
    if not clean_items:
        return f"- {empty_text}"
    return "\n".join(f"- {item}" for item in clean_items)


def build_daily_report(latest_output_dir: Path, panel_df: pd.DataFrame, site_df: pd.DataFrame, sidecar_df: pd.DataFrame | None) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    integrated_df = read_csv(latest_output_dir / INTEGRATED_TABLE_NAME)
    integrated_summary_df = read_csv(latest_output_dir / INTEGRATED_SUMMARY_NAME)
    metadata = read_json(latest_output_dir / METADATA_NAME)
    failure_rows = read_jsonl_messages(latest_output_dir / FAILURE_LOG_NAME)

    site_summary = format_bullets(
        [
            (
                f"{normalize_text(row.get('site'))}: total={normalize_text(row.get('total_panel_count'))}, "
                f"fault={normalize_text(row.get('fault_panel_count'))}, "
                f"non_fault_or_unresolved={normalize_text(row.get('non_fault_or_unresolved_count'))}"
            )
            for row in site_df.to_dict(orient="records")
        ],
        "site summary 없음",
    )
    summary_row = integrated_summary_df.iloc[0].to_dict()
    conalog_distribution = format_bullets(
        [
            f"{name}: {count}"
            for name, count in integrated_df["커널로그_원인군_ko"].map(normalize_text).replace("", "미기재").value_counts().to_dict().items()
        ],
        "conalog family 분포 없음",
    )
    if sidecar_df is not None and not sidecar_df.empty:
        gpvs_usage = format_bullets(
            [
                f"reference sidecar rows={len(sidecar_df)}",
                "GPVS 는 reference-only 이며 direct root-cause classifier 가 아님",
                "heuristic 은 triage-only 이며 stable default output 이 아님",
            ],
            "GPVS usage summary 없음",
        )
    else:
        gpvs_usage = "- stable-only 실행이므로 optional experimental/reference section 을 생략하였음"
    suspected_cause = format_bullets(
        [
            f"{name}: {count}"
            for name, count in integrated_df["1순위_의심원인_ko"].map(normalize_text).loc[lambda s: s.ne("")].value_counts().to_dict().items()
        ],
        "suspected-cause distribution 없음",
    )
    new_faults = format_bullets(
        [
            (
                f"{normalize_text(row.get('site'))}/{normalize_text(row.get('panel_id'))}: "
                f"{normalize_text(row.get('사건유형_ko'))} / {normalize_text(row.get('최종고장양상_ko'))} / "
                f"{normalize_text(row.get('conalog_원인군_ko'))}"
            )
            for row in panel_df.loc[panel_df["패널고장여부_ko"].map(normalize_text).eq("고장")].to_dict(orient="records")
        ],
        "신규 fault panel 없음 또는 미확인",
    )
    interpretation_notes = format_bullets(
        [
            "panel multiaxis verdict 를 primary 로 읽어야 함",
            "conalog 는 direct operational interpretation layer 임",
            "GPVS 는 reference-only 임",
            "heuristic 은 triage-only 임",
            f"runtime mode={normalize_text(metadata.get('runtime_mode', 'once'))}",
            f"run status={normalize_text(metadata.get('run_status_ko', 'unknown'))}",
        ],
        "주요 해석 메모 없음",
    )
    error_summary = format_bullets(
        [
            (
                f"{normalize_text(row.get('stage', 'runtime'))}: "
                f"{normalize_text(row.get('message_ko', row.get('message', '')))}"
            )
            for row in failure_rows[-5:]
        ],
        "실행 오류 없음",
    )
    return template.format(
        generated_at=now_utc(),
        site_summary=site_summary,
        total_panel_count=normalize_text(summary_row.get("total_panel_count", "")),
        fault_panel_count=normalize_text(summary_row.get("fault_panel_count", "")),
        non_fault_or_unresolved_count=normalize_text(summary_row.get("non_fault_or_unresolved_count", "")),
        conalog_fault_family_distribution=conalog_distribution,
        gpvs_usage_summary=gpvs_usage,
        suspected_cause_distribution=suspected_cause,
        new_fault_panel_list=new_faults,
        day_over_day_changes="- foundation 단계이므로 전일 비교는 placeholder 로 둠",
        interpretation_notes=interpretation_notes,
        error_summary=error_summary,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_root = args.input_root.resolve()
    output_root = args.output_root.expanduser()
    config_path = args.config.resolve()
    ensure_directory(input_root, "input root")
    if not config_path.exists():
        raise FileNotFoundError(f"missing config: {config_path}")
    output_root.mkdir(parents=True, exist_ok=True)
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

    plan = build_plan(args)
    if args.dry_run:
        plan["optional_sections_note_ko"] = (
            "dry-run 에서는 optional experimental/reference section 과 daily report 상세 section 이 실제 생성되지 않을 수 있음."
        )
        plan["daily_report_template_available_flag"] = int(TEMPLATE_PATH.exists())
        runtime_result = run_runtime(args)
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
            extra={"daily_report_template_available_flag": int(TEMPLATE_PATH.exists())},
        )
        write_json(paths["plan"], plan)
        print(json.dumps(plan, ensure_ascii=False))
        return 0

    runtime_result = run_runtime(args)
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

    panel_df = read_csv(latest_output_dir / PANEL_RESULT_NAME)
    site_df = read_csv(latest_output_dir / SITE_SUMMARY_NAME)
    sidecar_path = latest_output_dir / REFERENCE_SIDECAR_NAME
    sidecar_df = read_csv(sidecar_path) if sidecar_path.exists() else None

    integrated_df = build_integrated_table(panel_df, sidecar_df)
    integrated_df.to_csv(latest_output_dir / INTEGRATED_TABLE_NAME, index=False, encoding="utf-8-sig")
    integrated_summary_df = build_integrated_summary(panel_df)
    integrated_summary_df.to_csv(latest_output_dir / INTEGRATED_SUMMARY_NAME, index=False, encoding="utf-8-sig")

    if args.include_experimental == "on":
        write_optional_experimental_exports(latest_output_dir, sidecar_df)

    if args.report == "on":
        try:
            report_text = build_daily_report(latest_output_dir, panel_df, site_df, sidecar_df)
            (latest_output_dir / DAILY_REPORT_NAME).write_text(report_text, encoding="utf-8")
        except Exception:
            operator_message = short_report_failure_message()
            record_failure(
                paths,
                stage="daily_report",
                message_ko=operator_message,
                detail_ko=traceback.format_exc().strip(),
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
