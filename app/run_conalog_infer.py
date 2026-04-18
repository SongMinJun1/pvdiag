#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_INPUT_COLS = ["site", "panel_id"]
STABLE_PANEL_RESULT_COLS = [
    "site",
    "panel_id",
    "패널고장여부_ko",
    "사건유형_ko",
    "최종고장양상_ko",
    "conalog_원인군_ko",
]
SITE_SUMMARY_COLS = [
    "site",
    "total_panel_count",
    "fault_panel_count",
    "non_fault_or_unresolved_count",
    "note_ko",
]
ERROR_LOG_COLS = ["generated_at_utc", "level", "stage", "message_ko"]
EXPERIMENTAL_RESULT_COLS = [
    "site",
    "panel_id",
    "GPVS_참조정책_ko",
    "GPVS_참조메모_ko",
    "1순위_의심원인_ko",
    "2순위_의심원인_ko",
    "3순위_의심원인_ko",
    "heuristic_운영정책_ko",
    "note_ko",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the frozen conalog handoff entrypoint with a stable default output contract."
    )
    parser.add_argument("--input-root", type=Path, required=True, help="Input root directory.")
    parser.add_argument("--output-root", type=Path, required=True, help="Output root directory.")
    parser.add_argument("--config", type=Path, required=True, help="YAML config path.")
    parser.add_argument("--dry-run", action="store_true", help="Validate paths/config and emit a run plan without executing a full inference run.")
    parser.add_argument(
        "--include-experimental",
        choices=["off", "on"],
        default="off",
        help="Whether to emit experimental reference sidecar outputs. Defaults to off.",
    )
    return parser.parse_args(argv)


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def parse_simple_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        raise SystemExit(f"missing config: {path}")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            raise SystemExit(f"invalid config line: {raw_line}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("'").strip('"')
    return data


def ensure_directory(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"missing {label}: {path}")
    if not path.is_dir():
        raise SystemExit(f"{label} must be a directory: {path}")


def ensure_input_schema(df: pd.DataFrame, path: Path) -> None:
    missing = [column for column in REQUIRED_INPUT_COLS if column not in df.columns]
    if missing:
        raise SystemExit(f"{path} missing required input columns: {missing}")


def required_config(config: dict[str, str], keys: list[str], path: Path) -> None:
    missing = [key for key in keys if not normalize_text(config.get(key))]
    if missing:
        raise SystemExit(f"{path} missing required config keys: {missing}")


def git_value(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def discover_candidate_csvs(input_root: Path, limit: int = 12) -> list[str]:
    candidates: list[str] = []
    for path in sorted(input_root.rglob("*.csv")):
        if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        candidates.append(str(path.relative_to(input_root)))
        if len(candidates) >= limit:
            break
    return candidates


def output_paths(output_root: Path, config: dict[str, str]) -> dict[str, Path]:
    output_dir = output_root / normalize_text(config.get("output_subdir", "output"))
    return {
        "output_dir": output_dir,
        "panel_result": output_dir / normalize_text(config["panel_result_name"]),
        "site_summary": output_dir / normalize_text(config["site_summary_name"]),
        "metadata": output_dir / normalize_text(config["metadata_name"]),
        "error_log": output_dir / normalize_text(config["error_log_name"]),
        "experimental": output_dir / normalize_text(config["experimental_reference_name"]),
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_error_log(path: Path, rows: list[dict[str, str]]) -> None:
    df = pd.DataFrame(rows).reindex(columns=ERROR_LOG_COLS)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_run_metadata(
    *,
    config_path: Path,
    input_root: Path,
    output_root: Path,
    include_experimental: str,
    dry_run: bool,
    note_ko: str,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "generated_at_utc": now_utc(),
        "git_branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
        "git_head": git_value(["rev-parse", "HEAD"]),
        "config_path": str(config_path),
        "input_root": str(input_root),
        "output_root": str(output_root),
        "include_experimental": include_experimental,
        "dry_run": dry_run,
        "note_ko": note_ko,
    }
    if extra:
        payload.update(extra)
    return payload


def build_panel_result(df: pd.DataFrame, config: dict[str, str]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for row in df.to_dict(orient="records"):
        rows.append(
            {
                "site": normalize_text(row.get("site")),
                "panel_id": normalize_text(row.get("panel_id")),
                "패널고장여부_ko": normalize_text(config["default_fault_status"]),
                "사건유형_ko": normalize_text(config["default_event_type"]),
                "최종고장양상_ko": normalize_text(config["default_terminal_pattern"]),
                "conalog_원인군_ko": normalize_text(config["default_conalog_family"]),
            }
        )
    return pd.DataFrame(rows).reindex(columns=STABLE_PANEL_RESULT_COLS)


def build_site_summary(panel_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for site, site_df in panel_df.groupby("site", dropna=False):
        site_text = normalize_text(site)
        fault_count = int(site_df["패널고장여부_ko"].eq("고장").sum())
        rows.append(
            {
                "site": site_text,
                "total_panel_count": int(len(site_df)),
                "fault_panel_count": fault_count,
                "non_fault_or_unresolved_count": int(len(site_df) - fault_count),
                "note_ko": "stable handoff foundation output 기준 site summary 임",
            }
        )
    return pd.DataFrame(rows).reindex(columns=SITE_SUMMARY_COLS)


def build_experimental_reference(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for row in df.to_dict(orient="records"):
        rows.append(
            {
                "site": normalize_text(row.get("site")),
                "panel_id": normalize_text(row.get("panel_id")),
                "GPVS_참조정책_ko": "reference-only",
                "GPVS_참조메모_ko": "GPVS는 direct root-cause classifier가 아니라 reference-only 보조층임",
                "1순위_의심원인_ko": "원인미확정",
                "2순위_의심원인_ko": "",
                "3순위_의심원인_ko": "",
                "heuristic_운영정책_ko": "triage-only",
                "note_ko": "experimental reference output 이며 stable default output 이 아님",
            }
        )
    return pd.DataFrame(rows).reindex(columns=EXPERIMENTAL_RESULT_COLS)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_root = args.input_root.resolve()
    output_root = args.output_root.expanduser()
    config_path = args.config.resolve()

    ensure_directory(input_root, "input root")
    config = parse_simple_yaml(config_path)
    required_config(
        config,
        [
            "input_csv_name",
            "output_subdir",
            "panel_result_name",
            "site_summary_name",
            "metadata_name",
            "error_log_name",
            "experimental_reference_name",
            "default_fault_status",
            "default_event_type",
            "default_terminal_pattern",
            "default_conalog_family",
        ],
        config_path,
    )

    paths = output_paths(output_root, config)
    paths["output_dir"].mkdir(parents=True, exist_ok=True)
    input_csv_path = input_root / normalize_text(config["input_csv_name"])
    candidate_csvs = discover_candidate_csvs(input_root)
    error_rows: list[dict[str, str]] = []

    if args.dry_run:
        if not input_csv_path.exists():
            error_rows.append(
                {
                    "generated_at_utc": now_utc(),
                    "level": "warning",
                    "stage": "dry_run_input_discovery",
                    "message_ko": f"expected input file not found: {input_csv_path.name}; candidate csv 탐색 결과를 metadata 에 기록함",
                }
            )
            input_row_count = 0
            schema_ok = False
        else:
            input_df = pd.read_csv(input_csv_path, low_memory=False, encoding="utf-8-sig")
            ensure_input_schema(input_df, input_csv_path)
            input_row_count = int(len(input_df))
            schema_ok = True

        metadata = build_run_metadata(
            config_path=config_path,
            input_root=input_root,
            output_root=output_root,
            include_experimental=args.include_experimental,
            dry_run=True,
            note_ko=(
                "conalog stable handoff dry-run 계획임. stable output 이 delivery 기본값이며, "
                "GPVS 는 reference-only, heuristic 은 triage-only 로만 취급함."
            ),
            extra={
                "run_status_ko": "dry_run_plan",
                "expected_input_csv": str(input_csv_path),
                "expected_input_found_flag": bool(input_csv_path.exists()),
                "expected_input_schema_ok_flag": schema_ok,
                "candidate_input_csvs": candidate_csvs,
                "planned_outputs": [
                    str(paths["metadata"]),
                    str(paths["error_log"]),
                    str(paths["panel_result"]),
                    str(paths["site_summary"]),
                ]
                + ([str(paths["experimental"])] if args.include_experimental == "on" else []),
                "input_row_count": input_row_count,
            },
        )
        write_json(paths["metadata"], metadata)
        write_error_log(paths["error_log"], error_rows)
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "expected_input_csv": str(input_csv_path),
                    "candidate_input_csvs": candidate_csvs,
                    "output_dir": str(paths["output_dir"]),
                },
                ensure_ascii=False,
            )
        )
        return 0

    if not input_csv_path.exists():
        raise SystemExit(f"missing required input file for non-dry-run: {input_csv_path}")

    input_df = pd.read_csv(input_csv_path, low_memory=False, encoding="utf-8-sig")
    ensure_input_schema(input_df, input_csv_path)

    panel_df = build_panel_result(input_df, config)
    site_summary_df = build_site_summary(panel_df)
    panel_df.to_csv(paths["panel_result"], index=False, encoding="utf-8-sig")
    site_summary_df.to_csv(paths["site_summary"], index=False, encoding="utf-8-sig")

    if args.include_experimental == "on":
        experimental_df = build_experimental_reference(input_df)
        experimental_df.to_csv(paths["experimental"], index=False, encoding="utf-8-sig")

    metadata = build_run_metadata(
        config_path=config_path,
        input_root=input_root,
        output_root=output_root,
        include_experimental=args.include_experimental,
        dry_run=False,
        note_ko=(
            "conalog stable handoff foundation 실행 결과임. stable output 은 direct operational interpretation layer 기준의 "
            "기본 delivery 계약이며, GPVS 는 reference-only, heuristic 은 triage-only 로만 분리함."
        ),
        extra={
            "run_status_ko": "foundation_placeholder_run",
            "resolved_input_csv": str(input_csv_path),
            "input_row_count": int(len(input_df)),
        },
    )
    write_json(paths["metadata"], metadata)
    write_error_log(paths["error_log"], error_rows)
    print(
        json.dumps(
            {
                "dry_run": False,
                "panel_result": str(paths["panel_result"]),
                "site_summary": str(paths["site_summary"]),
                "experimental_emitted": args.include_experimental == "on",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
