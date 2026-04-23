#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RELEASE_ROOT = REPO_ROOT / "release/final_delivery_v1"
PACKAGE_ROOT = RELEASE_ROOT / "package"
MANIFEST_PATH = RELEASE_ROOT / "final_delivery_manifest_v1.csv"
SUMMARY_PATH = RELEASE_ROOT / "final_delivery_summary_v1.json"
OFFICIAL_FREEZE_TAG = "project-main-freeze-v10"

HANDOFF_BUILD_SCRIPT = REPO_ROOT / "research/prognostics/build_conalog_handoff_pack_v1.py"
HANDOFF_ROOT = REPO_ROOT / "delivery/conalog_handoff_v1"

PACKAGE_POINTER_TEXT = """# Integrated Result Table Pointer

- final front-facing integrated table schema is fixed and unchanged.
- current stable snapshot source:
  - `_share/panel_day_engine_integrated_result_table_v1.csv`
  - `_share/panel_day_engine_integrated_result_summary_v1.csv`
- release package also includes copied snapshot examples under `package/examples/`.
- package one-click path keeps the same integrated table schema and stable output filenames.
- panel multiaxis verdict remains primary.
- conalog remains the direct operational interpretation layer.
- GPVS remains reference-only.
- cause candidate heuristic remains triage-only.
"""

TOP_LEVEL_DOCS = {
    "README.md": """# Final Delivery Pack V1

## 목적
- 본 디렉터리는 현재까지 구축된 stable, reference-only, triage-only foundation을 외부 전달 관점에서 한 번에 모아 보고 실행할 수 있도록 정리한 executable release pack 임.
- panel multiaxis verdict 는 primary 임.
- conalog 는 direct operational interpretation layer 임.
- final front-facing integrated table schema 는 고정되어 있으며 변경하지 않음.

## executable pack 에 무엇이 들어 있는가
- `package/app/`: dashboard 또는 외부 시스템이 직접 호출할 수 있는 CLI/UI entrypoint
- `package/bin/`: Windows operator wrapper
- `package/config/`: runtime config
- `package/stable_handoff/`: stable handoff docs/config/examples
- `package/runtime/`: runtime readiness/failure handling 문서
- `package/oneclick/`: one-click 및 daily-report 문서와 template
- `package/docs/`: 비교 문서, GPVS inventory, coverage/performance 문서
- `package/examples/`: stable snapshot 과 reference/triage summary snapshot

## 무엇이 stable 인가
- `package/app/run_conalog_infer.py`
- `package/app/run_realtime.py`
- `package/app/run_oneclick.py`
- `package/config/runtime.yaml`
- stable handoff pack
- stable output 계약과 integrated result schema
- stable CLI 는 현재 delivery pack 기준으로 검증된 기본 진입점임
- demo/real batch wrapper 는 현재 `package/app/run_conalog_infer.py` 위의 thin wrapper 임
- Python 3 설치는 여전히 필요함
- git executable 이 없어도 stable dry-run/demo flow 는 계속 수행 가능함
- git metadata 가 대상 장비에서 unavailable 일 수 있으나, 이는 stable dry-run 또는 stable output generation 을 막지 않음

## 무엇이 reference-only 인가
- GPVS inventory, GPVS usage mail draft, GPVS evidence summary snapshot
- optional experimental/reference export
- GPVS 는 direct root-cause classifier 가 아님

## 무엇이 triage-only 인가
- cause candidate heuristic summary snapshot
- optional heuristic triage export
- heuristic 은 field-trial triage-only 층임

## 권장 사용 순서
1. `package/bin/run_demo.bat`
2. `package/bin/run_real.bat`
3. dashboard / system integration 은 우선 `package/app/run_conalog_infer.py` 를 직접 호출해야 함
4. one-click / Streamlit 은 optional foundation utility 이며 이번 hotfix scope 에 포함되지 않음
""",
    "QUICKSTART.md": """# Quickstart

## 1. demonstration
- `package/bin/run_demo.bat`
- packaged example input 으로 `package/app/run_conalog_infer.py` 를 직접 실행하는 thin wrapper 임
- Python 3 설치는 필요하지만, git 설치는 dry-run/demo 흐름에 필수 아님

## 2. actual input folder 실행
- `package/bin/run_real.bat`
- 실행 시 input_root 를 직접 입력받고, output_root 는 비우면 `package/real_output` 을 기본값으로 사용함
- 내부적으로 `package/app/run_conalog_infer.py` 를 직접 실행하는 thin wrapper 임

## 3. system / dashboard integration
- stable direct CLI 는 `package/app/run_conalog_infer.py`
- demo/real batch wrapper 는 stable CLI 위의 thin wrapper 임
- 문서를 scraping 하지 말고 executable entrypoint 를 직접 호출해야 함
- git executable 이 대상 장비 PATH 에 없어도 stable dry-run 은 계속 수행 가능함

## 운영 원칙
- stable output 을 먼저 읽어야 함
- reference_only 와 triage_only 는 stable default output 과 혼동하면 안 됨
- final front-facing integrated table schema 는 그대로 유지됨
- one-click 과 Streamlit 은 optional foundation utility 이며 이번 hotfix scope 에 포함되지 않음
- demo/real wrapper 는 현재 minimal setup 기준으로 지원하지만, Python 설치 자체는 필요함
""",
    "RELEASE_NOTES.md": """# Release Notes

## 현재까지 완료된 단계
- backfill foundation 추가 완료
- validation framework 추가 완료
- fault coverage / model performance report 추가 완료
- conalog handoff pack foundation 추가 완료
- runtime feasibility foundation 추가 완료
- one-click / daily-report foundation 추가 완료

## current main 상태
- panel multiaxis verdict 는 primary 로 유지 중임
- conalog 는 direct operational interpretation layer 로 유지 중임
- GPVS 는 reference-only 로 유지 중임
- heuristic 은 triage-only 로 유지 중임

## 이번 release pack 이 추가하는 것
- 현재까지의 stable/reference/triage foundation 을 release 디렉터리 아래에 한 번에 모은 deliverable-facing package 를 추가하였음
- 어떤 자산이 stable 이고 어떤 자산이 reference_only / triage_only / documentation 인지 manifest 로 명시하였음

## 아직 production-grade 가 아닌 것
- runtime 은 feasibility/readiness 단계임
- one-click 은 foundation 단계이며 full production scheduler 가 아님
- GPVS 와 heuristic 은 stable default output 으로 승격되지 않았음
""",
    "KNOWN_LIMITS.md": """# Known Limits

- GPVS 는 reference-only 임
- heuristic 은 triage-only 임
- runtime 은 feasibility/readiness 이며 production SLA 가 아님
- one-click 과 Streamlit 은 optional foundation utility 이며 full production scheduler 가 아님
- stable output 과 experimental/reference output 은 혼동하면 안 됨
- dashboard 또는 외부 시스템은 문서를 scraping 하지 말고 `package/app/` entrypoint 를 직접 호출해야 함
- Python 3 설치는 여전히 필요함
- git executable 이 대상 장비에 없어도 demo/dry-run 흐름은 계속 수행 가능함
- git metadata 는 원본 저장소 밖에서 unavailable 일 수 있으나, 이는 stable dry-run 또는 stable output generation 을 막지 않음
- final front-facing integrated table schema 는 unchanged 상태로 유지됨
- demo/real batch wrapper 는 stable CLI thin wrapper 이며, one-click 과 Streamlit 은 이번 hotfix scope 에 포함되지 않음
""",
    "DELIVERY_MANIFEST.md": """# Delivery Manifest

## 먼저 볼 것
1. `package/bin/run_demo.bat`
2. `package/bin/run_real.bat`
3. `package/app/run_conalog_infer.py`
4. `package/app/run_oneclick.py`

## 폴더별 의미
- `package/app/`: executable entrypoint 모음
- `package/bin/`: Windows operator wrapper 와 설정 template
- `package/config/`: runtime config
- `package/stable_handoff/`: stable handoff docs/config/examples
- `package/runtime/`: runtime guide, failure handling, latency/readiness report
- `package/oneclick/`: one-click guide, daily-report guide, template
- `package/docs/`: comparison, GPVS inventory, GPVS mail draft, coverage/performance, integrated table pointer
- `package/examples/`: stable snapshot, reference-only summary, triage-only summary

## 주의
- stable / reference_only / triage_only 구분은 `final_delivery_manifest_v1.csv` 를 기준으로 읽어야 함
- stable default output 과 optional experimental output 은 혼동하면 안 됨
""",
}

DOCUMENT_COPY_ITEMS = [
    {
        "source": REPO_ROOT / "docs/OPS_CONALOG_HANDOFF_PACK_V1.md",
        "dest": PACKAGE_ROOT / "docs/OPS_CONALOG_HANDOFF_PACK_V1.md",
        "artifact_kind": "handoff_doc",
        "stability_level_ko": "documentation",
        "note_ko": "conalog handoff pack 안내 문서",
    },
    {
        "source": REPO_ROOT / "docs/OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md",
        "dest": PACKAGE_ROOT / "docs/OPS_CONALOG_RULEBASE_VS_HYBRID_ENGINE_V1.md",
        "artifact_kind": "comparison_doc",
        "stability_level_ko": "documentation",
        "note_ko": "conalog rulebase vs hybrid engine 대외 설명 문서",
    },
    {
        "source": REPO_ROOT / "docs/OPS_FAULT_COVERAGE_AND_MODEL_PERFORMANCE_V1.md",
        "dest": PACKAGE_ROOT / "docs/OPS_FAULT_COVERAGE_AND_MODEL_PERFORMANCE_V1.md",
        "artifact_kind": "coverage_report",
        "stability_level_ko": "documentation",
        "note_ko": "fault coverage 및 model performance 설명 문서",
    },
    {
        "source": REPO_ROOT / "_share/panel_day_engine_fault_coverage_matrix_v1.csv",
        "dest": PACKAGE_ROOT / "docs/panel_day_engine_fault_coverage_matrix_v1.csv",
        "artifact_kind": "coverage_report_csv",
        "stability_level_ko": "documentation",
        "note_ko": "fault coverage matrix snapshot",
    },
    {
        "source": REPO_ROOT / "_share/panel_day_engine_model_metrics_v1.csv",
        "dest": PACKAGE_ROOT / "docs/panel_day_engine_model_metrics_v1.csv",
        "artifact_kind": "coverage_report_csv",
        "stability_level_ko": "documentation",
        "note_ko": "layer metric snapshot",
    },
    {
        "source": REPO_ROOT / "docs/OPS_GPVS_EXTERNAL_DATA_INVENTORY_V1.md",
        "dest": PACKAGE_ROOT / "docs/OPS_GPVS_EXTERNAL_DATA_INVENTORY_V1.md",
        "artifact_kind": "gpvs_inventory_doc",
        "stability_level_ko": "reference_only",
        "note_ko": "GPVS external data inventory 문서",
    },
    {
        "source": REPO_ROOT / "docs/MAIL_GPVS_DATA_USAGE_SUMMARY_V1.md",
        "dest": PACKAGE_ROOT / "docs/MAIL_GPVS_DATA_USAGE_SUMMARY_V1.md",
        "artifact_kind": "gpvs_mail_draft",
        "stability_level_ko": "reference_only",
        "note_ko": "GPVS usage 설명용 메일 초안",
    },
    {
        "source": REPO_ROOT / "docs/OPS_REALTIME_OPERATION_READINESS_V1.md",
        "dest": PACKAGE_ROOT / "docs/OPS_REALTIME_OPERATION_READINESS_V1.md",
        "artifact_kind": "runtime_readiness_doc",
        "stability_level_ko": "documentation",
        "note_ko": "runtime readiness 판단 문서",
    },
    {
        "source": REPO_ROOT / "docs/OPS_RUNTIME_INFERENCE_GUIDE_V1.md",
        "dest": PACKAGE_ROOT / "runtime/OPS_RUNTIME_INFERENCE_GUIDE_V1.md",
        "artifact_kind": "runtime_doc",
        "stability_level_ko": "documentation",
        "note_ko": "runtime guide",
    },
    {
        "source": REPO_ROOT / "docs/OPS_RUNTIME_FAILURE_HANDLING_V1.md",
        "dest": PACKAGE_ROOT / "runtime/OPS_RUNTIME_FAILURE_HANDLING_V1.md",
        "artifact_kind": "runtime_doc",
        "stability_level_ko": "documentation",
        "note_ko": "runtime failure handling guide",
    },
    {
        "source": REPO_ROOT / "docs/OPS_RUNTIME_LATENCY_REPORT_V1.md",
        "dest": PACKAGE_ROOT / "runtime/OPS_RUNTIME_LATENCY_REPORT_V1.md",
        "artifact_kind": "runtime_doc",
        "stability_level_ko": "documentation",
        "note_ko": "runtime latency explanation",
    },
    {
        "source": REPO_ROOT / "_share/panel_day_engine_runtime_latency_report_v1.csv",
        "dest": PACKAGE_ROOT / "runtime/panel_day_engine_runtime_latency_report_v1.csv",
        "artifact_kind": "runtime_report_csv",
        "stability_level_ko": "documentation",
        "note_ko": "measured runtime latency report",
    },
    {
        "source": REPO_ROOT / "_share/panel_day_engine_runtime_readiness_summary_v1.csv",
        "dest": PACKAGE_ROOT / "runtime/panel_day_engine_runtime_readiness_summary_v1.csv",
        "artifact_kind": "runtime_report_csv",
        "stability_level_ko": "documentation",
        "note_ko": "runtime readiness summary",
    },
    {
        "source": REPO_ROOT / "config/runtime.yaml",
        "dest": PACKAGE_ROOT / "runtime/runtime.yaml",
        "artifact_kind": "runtime_config_snapshot",
        "stability_level_ko": "documentation",
        "note_ko": "repo runtime config snapshot for comparison",
    },
    {
        "source": REPO_ROOT / "docs/OPS_ONECLICK_OPERATION_GUIDE_V1.md",
        "dest": PACKAGE_ROOT / "oneclick/OPS_ONECLICK_OPERATION_GUIDE_V1.md",
        "artifact_kind": "oneclick_doc",
        "stability_level_ko": "documentation",
        "note_ko": "one-click operation guide",
    },
    {
        "source": REPO_ROOT / "docs/OPS_DAILY_REPORT_AUTOMATION_V1.md",
        "dest": PACKAGE_ROOT / "oneclick/OPS_DAILY_REPORT_AUTOMATION_V1.md",
        "artifact_kind": "oneclick_doc",
        "stability_level_ko": "documentation",
        "note_ko": "daily report automation guide",
    },
    {
        "source": REPO_ROOT / "templates/daily_report_template.md",
        "dest": PACKAGE_ROOT / "oneclick/daily_report_template.md",
        "artifact_kind": "template",
        "stability_level_ko": "documentation",
        "note_ko": "daily report template",
    },
    {
        "source": REPO_ROOT / "_share/panel_day_engine_integrated_result_table_v1.csv",
        "dest": PACKAGE_ROOT / "examples/integrated_result_table_v1.csv",
        "artifact_kind": "stable_snapshot_csv",
        "stability_level_ko": "stable",
        "note_ko": "current frozen integrated result table snapshot",
    },
    {
        "source": REPO_ROOT / "_share/panel_day_engine_integrated_result_summary_v1.csv",
        "dest": PACKAGE_ROOT / "examples/integrated_result_summary_v1.csv",
        "artifact_kind": "stable_snapshot_csv",
        "stability_level_ko": "stable",
        "note_ko": "current frozen integrated result summary snapshot",
    },
    {
        "source": REPO_ROOT / "_share/panel_day_engine_gpvs_evidence_summary_v1.csv",
        "dest": PACKAGE_ROOT / "examples/panel_day_engine_gpvs_evidence_summary_v1.csv",
        "artifact_kind": "reference_summary_csv",
        "stability_level_ko": "reference_only",
        "note_ko": "GPVS reference usage summary snapshot",
    },
    {
        "source": REPO_ROOT / "_share/panel_day_engine_cause_candidate_summary_v1.csv",
        "dest": PACKAGE_ROOT / "examples/panel_day_engine_cause_candidate_summary_v1.csv",
        "artifact_kind": "triage_summary_csv",
        "stability_level_ko": "triage_only",
        "note_ko": "heuristic triage summary snapshot",
    },
]

EXECUTABLE_COPY_ITEMS = [
    {
        "source": REPO_ROOT / "app/run_realtime.py",
        "dest": PACKAGE_ROOT / "app/run_realtime.py",
        "artifact_kind": "package_entrypoint",
        "stability_level_ko": "stable",
        "note_ko": "runtime feasibility wrapper entrypoint",
    },
]

PACKAGE_RUN_CONALOG_INFER_TEXT = """#!/usr/bin/env python3
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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")


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
                "stable dry-run plan 임. git metadata 가 unavailable 이어도 dry-run 및 output metadata 생성은 계속 수행함."
            ),
            extra={
                "expected_input_csv": str(input_csv_path),
                "candidate_csvs": candidate_csvs,
                "input_row_count": input_row_count,
                "input_schema_ok": schema_ok,
                "stable_output_files": [
                    paths["panel_result"].name,
                    paths["site_summary"].name,
                    paths["metadata"].name,
                    paths["error_log"].name,
                ],
                "experimental_output_files": [paths["experimental"].name] if args.include_experimental == "on" else [],
            },
        )
        write_json(paths["metadata"], metadata)
        write_error_log(paths["error_log"], error_rows)
        print(json.dumps(metadata, ensure_ascii=False))
        return 0

    if not input_csv_path.exists():
        raise SystemExit(f"missing expected input csv: {input_csv_path}")

    input_df = pd.read_csv(input_csv_path, low_memory=False, encoding="utf-8-sig")
    ensure_input_schema(input_df, input_csv_path)

    panel_df = build_panel_result(input_df, config)
    site_summary_df = build_site_summary(panel_df)
    panel_df.to_csv(paths["panel_result"], index=False, encoding="utf-8-sig")
    site_summary_df.to_csv(paths["site_summary"], index=False, encoding="utf-8-sig")

    metadata = build_run_metadata(
        config_path=config_path,
        input_root=input_root,
        output_root=output_root,
        include_experimental=args.include_experimental,
        dry_run=False,
        note_ko=(
            "stable handoff foundation output 임. panel multiaxis verdict 를 primary 로 유지하며 conalog 를 direct operational interpretation layer 로 둠."
        ),
        extra={
            "input_row_count": int(len(input_df)),
            "candidate_csvs": candidate_csvs,
            "stable_output_files": [
                paths["panel_result"].name,
                paths["site_summary"].name,
                paths["metadata"].name,
                paths["error_log"].name,
            ],
            "experimental_output_files": [paths["experimental"].name] if args.include_experimental == "on" else [],
        },
    )
    write_json(paths["metadata"], metadata)

    if args.include_experimental == "on":
        experimental_df = build_experimental_reference(input_df)
        experimental_df.to_csv(paths["experimental"], index=False, encoding="utf-8-sig")

    write_error_log(paths["error_log"], error_rows)
    print(
        json.dumps(
            {
                "status": "completed",
                "panel_result": str(paths["panel_result"]),
                "site_summary": str(paths["site_summary"]),
                "metadata": str(paths["metadata"]),
                "experimental_reference": str(paths["experimental"]) if args.include_experimental == "on" else "",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

PACKAGE_RUNTIME_YAML_TEXT = """input_root: stable_handoff/examples
output_root: output
include_experimental: off
poll_seconds: 300
stable_output_subdir: latest
runtime_log_name: runtime_log_v1.jsonl
failure_log_name: failure_log_v1.jsonl
latest_summary_name: conalog_site_summary_v1.csv
handoff_config_path: stable_handoff/config/default.yaml
latest_panel_result_name: conalog_panel_result_v1.csv
latest_metadata_name: conalog_run_metadata_v1.json
latest_reference_sidecar_name: conalog_reference_sidecar_v1.csv
"""

PACKAGE_RUN_ONECLICK_TEXT = """#!/usr/bin/env python3
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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\\n")


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
    return "\\n".join(f"- {item}" for item in clean_items)


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
"""

PACKAGE_APP_STREAMLIT_TEXT = """#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ONECLICK_ENTRYPOINT = REPO_ROOT / "app/run_oneclick.py"

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None


def run_oneclick(
    *,
    input_root: str,
    output_root: str,
    config_path: str,
    include_experimental: bool,
    report: bool,
    dry_run: bool,
) -> tuple[int, str]:
    cmd = [
        sys.executable,
        str(ONECLICK_ENTRYPOINT),
        "--input-root",
        input_root,
        "--output-root",
        output_root,
        "--config",
        config_path,
        "--include-experimental",
        "on" if include_experimental else "off",
        "--report",
        "on" if report else "off",
    ]
    if dry_run:
        cmd.append("--dry-run")
    result = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    output_text = (result.stdout or "").strip()
    error_text = (result.stderr or "").strip()
    return result.returncode, "\\n".join(part for part in [output_text, error_text] if part)


def render_app() -> None:
    assert st is not None
    st.set_page_config(page_title="Conalog Delivery Pack", layout="wide")
    st.title("Conalog Delivery Pack GUI")
    st.caption("stable output 과 optional experimental/reference output 을 분리해서 보여주는 foundation UI")

    default_input_root = str(REPO_ROOT / "stable_handoff" / "examples")
    default_output_root = str(REPO_ROOT / "demo_output")
    default_config_path = str(REPO_ROOT / "config" / "runtime.yaml")

    input_root = st.text_input("입력 root 경로", value=default_input_root)
    output_root = st.text_input("출력 root 경로", value=default_output_root)
    config_path = st.text_input("config 경로", value=default_config_path)
    include_experimental = st.checkbox("optional experimental/reference output 포함", value=False)
    report = st.checkbox("daily report 생성", value=True)
    dry_run = st.checkbox("dry-run", value=True)

    if st.button("실행", type="primary"):
        code, text = run_oneclick(
            input_root=input_root,
            output_root=output_root,
            config_path=config_path,
            include_experimental=include_experimental,
            report=report,
            dry_run=dry_run,
        )
        if code == 0:
            st.success("실행 완료")
        else:
            st.error("실행 실패")
        st.text_area("결과 / 상태", value=text, height=260)


def main() -> None:
    if st is None:
        raise SystemExit("streamlit is not installed; UI execution requires streamlit.")
    render_app()


if __name__ == "__main__":
    main()
"""

RUN_DEMO_BAT_TEXT = """@echo off
setlocal
set PACKAGE_ROOT=%~dp0..
set INPUT_ROOT=%PACKAGE_ROOT%\\stable_handoff\\examples
set OUTPUT_ROOT=%PACKAGE_ROOT%\\demo_output
set OUTPUT_DIR=%OUTPUT_ROOT%\\output
set CONFIG_PATH=%PACKAGE_ROOT%\\stable_handoff\\config\\default.yaml

where py >nul 2>nul
if %errorlevel%==0 goto use_py
where python >nul 2>nul
if %errorlevel%==0 goto use_python
echo Python 3가 필요합니다. Python을 설치한 뒤 다시 실행하십시오.
exit /b 1

:use_py
py -3 "%PACKAGE_ROOT%\\app\\run_conalog_infer.py" --input-root "%INPUT_ROOT%" --output-root "%OUTPUT_ROOT%" --config "%CONFIG_PATH%"
if errorlevel 1 exit /b %errorlevel%
if exist "%OUTPUT_DIR%" start "" "%OUTPUT_DIR%"
exit /b 0

:use_python
python "%PACKAGE_ROOT%\\app\\run_conalog_infer.py" --input-root "%INPUT_ROOT%" --output-root "%OUTPUT_ROOT%" --config "%CONFIG_PATH%"
if errorlevel 1 exit /b %errorlevel%
if exist "%OUTPUT_DIR%" start "" "%OUTPUT_DIR%"
exit /b 0
"""

RUN_REAL_BAT_TEXT = """@echo off
setlocal
set PACKAGE_ROOT=%~dp0..
set CONFIG_PATH=%PACKAGE_ROOT%\\stable_handoff\\config\\default.yaml
set DEFAULT_OUTPUT_ROOT=%PACKAGE_ROOT%\\real_output

where py >nul 2>nul
if %errorlevel%==0 goto have_python
where python >nul 2>nul
if %errorlevel%==0 goto have_python
echo Python 3가 필요합니다. Python을 설치한 뒤 다시 실행하십시오.
exit /b 1

:have_python
set /p INPUT_ROOT=입력 폴더 경로를 입력하십시오: 
if "%INPUT_ROOT%"=="" goto invalid_input
if not exist "%INPUT_ROOT%" goto invalid_input

set /p OUTPUT_ROOT=출력 폴더 경로를 입력하십시오(빈칸이면 기본값 사용): 
if "%OUTPUT_ROOT%"=="" set OUTPUT_ROOT=%DEFAULT_OUTPUT_ROOT%

where py >nul 2>nul
if %errorlevel%==0 goto run_with_py
python "%PACKAGE_ROOT%\\app\\run_conalog_infer.py" --input-root "%INPUT_ROOT%" --output-root "%OUTPUT_ROOT%" --config "%CONFIG_PATH%"
if errorlevel 1 exit /b %errorlevel%
if exist "%OUTPUT_ROOT%\\output" start "" "%OUTPUT_ROOT%\\output"
exit /b 0

:run_with_py
py -3 "%PACKAGE_ROOT%\\app\\run_conalog_infer.py" --input-root "%INPUT_ROOT%" --output-root "%OUTPUT_ROOT%" --config "%CONFIG_PATH%"
if errorlevel 1 exit /b %errorlevel%
if exist "%OUTPUT_ROOT%\\output" start "" "%OUTPUT_ROOT%\\output"
exit /b 0

:invalid_input
echo 입력 폴더 경로를 다시 확인하십시오.
exit /b 0
"""

OPEN_RESULTS_BAT_TEXT = """@echo off
setlocal
set PACKAGE_ROOT=%~dp0..
set SETTINGS_FILE=%PACKAGE_ROOT%\\bin\\settings.json
if exist "%SETTINGS_FILE%" goto have_settings
set SETTINGS_FILE=%PACKAGE_ROOT%\\bin\\settings.template.json

:have_settings
for /f "delims=" %%I in ('python -c "import json, pathlib; root = pathlib.Path(r'%PACKAGE_ROOT%'); settings = json.loads(pathlib.Path(r'%SETTINGS_FILE%').read_text(encoding='utf-8')); latest = pathlib.Path(settings.get('output_root', str(root / 'demo_output'))) / 'latest'; print(str(latest))"') do set LATEST_DIR=%%I

if exist "%LATEST_DIR%" (
  start "" "%LATEST_DIR%"
) else (
  echo latest output directory not found: %LATEST_DIR%
  exit /b 1
)
"""

SETTINGS_TEMPLATE = {
    "input_root": "C:/conalog/input",
    "output_root": "C:/conalog/output",
    "config": "C:/conalog/package/config/runtime.yaml",
    "include_experimental": "off",
    "report": "on",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def ensure_handoff_pack() -> None:
    if HANDOFF_ROOT.exists():
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


def copy_file(src: Path, dst: Path) -> None:
    if src.name.startswith("._"):
        return
    if not src.exists():
        raise SystemExit(f"missing source asset: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        raise SystemExit(f"missing source tree: {src}")
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("._*"))


def purge_appledouble(root: Path) -> None:
    for path in root.rglob("._*"):
        if path.is_file():
            path.unlink()


def relative_to_release(path: Path) -> str:
    return str(path.relative_to(RELEASE_ROOT))


def add_manifest_row(
    manifest_rows: list[dict[str, object]],
    *,
    path: Path,
    artifact_kind: str,
    stability_level_ko: str,
    note_ko: str,
) -> None:
    manifest_rows.append(
        {
            "relative_path": relative_to_release(path),
            "artifact_kind": artifact_kind,
            "stability_level_ko": stability_level_ko,
            "included_flag": 1,
            "note_ko": note_ko,
        }
    )


def materialize_release_docs(manifest_rows: list[dict[str, object]]) -> None:
    for filename, content in TOP_LEVEL_DOCS.items():
        path = RELEASE_ROOT / filename
        write_text(path, content)
        add_manifest_row(
            manifest_rows,
            path=path,
            artifact_kind="release_doc",
            stability_level_ko="documentation",
            note_ko="release top-level 안내 문서",
        )


def materialize_stable_handoff(manifest_rows: list[dict[str, object]]) -> None:
    copy_tree(HANDOFF_ROOT, PACKAGE_ROOT / "stable_handoff")
    for path in sorted((PACKAGE_ROOT / "stable_handoff").rglob("*")):
        if path.is_file():
            add_manifest_row(
                manifest_rows,
                path=path,
                artifact_kind="stable_handoff_asset",
                stability_level_ko="stable",
                note_ko="stable conalog handoff pack 자산",
            )


def materialize_copied_assets(manifest_rows: list[dict[str, object]]) -> None:
    for item in DOCUMENT_COPY_ITEMS + EXECUTABLE_COPY_ITEMS:
        copy_file(item["source"], item["dest"])
        add_manifest_row(
            manifest_rows,
            path=item["dest"],
            artifact_kind=item["artifact_kind"],
            stability_level_ko=item["stability_level_ko"],
            note_ko=item["note_ko"],
        )


def materialize_generated_assets(manifest_rows: list[dict[str, object]]) -> None:
    generated_items = [
        (
            PACKAGE_ROOT / "app/run_conalog_infer.py",
            PACKAGE_RUN_CONALOG_INFER_TEXT,
            "package_entrypoint",
            "stable",
            "package-local stable conalog handoff CLI entrypoint",
        ),
        (
            PACKAGE_ROOT / "app/run_oneclick.py",
            PACKAGE_RUN_ONECLICK_TEXT,
            "package_entrypoint",
            "stable",
            "package-local one-click executable wrapper",
        ),
        (
            PACKAGE_ROOT / "app/app_streamlit.py",
            PACKAGE_APP_STREAMLIT_TEXT,
            "package_entrypoint",
            "stable",
            "package-local streamlit GUI wrapper",
        ),
        (
            PACKAGE_ROOT / "config/runtime.yaml",
            PACKAGE_RUNTIME_YAML_TEXT,
            "package_config",
            "stable",
            "package-local runtime config",
        ),
        (
            PACKAGE_ROOT / "bin/run_demo.bat",
            RUN_DEMO_BAT_TEXT,
            "operator_wrapper",
            "stable",
            "Windows demo wrapper",
        ),
        (
            PACKAGE_ROOT / "bin/run_real.bat",
            RUN_REAL_BAT_TEXT,
            "operator_wrapper",
            "stable",
            "Windows real-run wrapper",
        ),
        (
            PACKAGE_ROOT / "bin/open_results.bat",
            OPEN_RESULTS_BAT_TEXT,
            "operator_wrapper",
            "stable",
            "Windows result opener",
        ),
        (
            PACKAGE_ROOT / "bin/settings.template.json",
            json.dumps(SETTINGS_TEMPLATE, ensure_ascii=False, indent=2) + "\n",
            "operator_wrapper",
            "stable",
            "Windows settings template",
        ),
        (
            PACKAGE_ROOT / "docs/INTEGRATED_RESULT_TABLE_POINTER.md",
            PACKAGE_POINTER_TEXT,
            "integrated_table_pointer",
            "documentation",
            "final integrated result table schema pointer",
        ),
    ]
    for path, content, artifact_kind, stability_level_ko, note_ko in generated_items:
        write_text(path, content)
        add_manifest_row(
            manifest_rows,
            path=path,
            artifact_kind=artifact_kind,
            stability_level_ko=stability_level_ko,
            note_ko=note_ko,
        )


def main() -> None:
    ensure_handoff_pack()
    if PACKAGE_ROOT.exists():
        shutil.rmtree(PACKAGE_ROOT)
    PACKAGE_ROOT.mkdir(parents=True, exist_ok=True)
    for dirname in ["docs", "stable_handoff", "runtime", "oneclick", "examples", "app", "config", "bin"]:
        (PACKAGE_ROOT / dirname).mkdir(parents=True, exist_ok=True)

    manifest_rows: list[dict[str, object]] = []
    materialize_release_docs(manifest_rows)
    materialize_stable_handoff(manifest_rows)
    materialize_copied_assets(manifest_rows)
    materialize_generated_assets(manifest_rows)
    purge_appledouble(PACKAGE_ROOT)

    manifest_rows = [row for row in manifest_rows if not Path(str(row["relative_path"])).name.startswith("._")]
    manifest_rows = sorted(manifest_rows, key=lambda row: str(row["relative_path"]))
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["relative_path", "artifact_kind", "stability_level_ko", "included_flag", "note_ko"],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    stable_count = sum(1 for row in manifest_rows if row["stability_level_ko"] == "stable")
    reference_count = sum(1 for row in manifest_rows if row["stability_level_ko"] == "reference_only")
    triage_count = sum(1 for row in manifest_rows if row["stability_level_ko"] == "triage_only")
    documentation_count = sum(1 for row in manifest_rows if row["stability_level_ko"] == "documentation")
    summary = {
        "generated_at_utc": now_utc(),
        "git_branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
        "git_head": git_value(["rev-parse", "HEAD"]),
        "official_freeze_tag_before_release": OFFICIAL_FREEZE_TAG,
        "delivery_pack_version": "final_delivery_v1",
        "stable_artifact_count": stable_count,
        "reference_only_artifact_count": reference_count,
        "triage_only_artifact_count": triage_count,
        "documentation_count": documentation_count,
        "note_ko": (
            "본 release pack 은 executable delivery hotfix 결과임. stable/default semantics 를 바꾸지 않았고, "
            "GPVS 는 reference_only, heuristic 은 triage_only 로만 유지하였음."
        ),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] materialized {RELEASE_ROOT}")


if __name__ == "__main__":
    main()
