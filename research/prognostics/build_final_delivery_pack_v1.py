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
OFFICIAL_FREEZE_TAG = "project-main-freeze-v9"

HANDOFF_BUILD_SCRIPT = REPO_ROOT / "research/prognostics/build_conalog_handoff_pack_v1.py"
HANDOFF_ROOT = REPO_ROOT / "delivery/conalog_handoff_v1"

PACKAGE_POINTER_TEXT = """# Integrated Result Table Pointer

- final front-facing integrated table schema is fixed and unchanged.
- current stable snapshot source:
  - `_share/panel_day_engine_integrated_result_table_v1.csv`
  - `_share/panel_day_engine_integrated_result_summary_v1.csv`
- release package also includes copied snapshot examples under `package/examples/`.
- panel multiaxis verdict remains primary.
- conalog remains the direct operational interpretation layer.
- GPVS remains reference-only.
- cause candidate heuristic remains triage-only.
"""

PACKAGE_ITEMS = [
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
        "source": REPO_ROOT / "config/runtime.yaml",
        "dest": PACKAGE_ROOT / "runtime/runtime.yaml",
        "artifact_kind": "runtime_config",
        "stability_level_ko": "stable",
        "note_ko": "runtime foundation config snapshot",
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


TOP_LEVEL_DOCS = {
    "README.md": """# Final Delivery Pack V1

## 목적
- 본 디렉터리는 현재까지 구축된 stable, reference-only, triage-only foundation을 외부 전달 관점에서 한 번에 모아 보는 release pack 임.
- panel multiaxis verdict 는 primary 임.
- conalog 는 direct operational interpretation layer 임.
- final front-facing integrated table schema 는 고정되어 있으며 변경하지 않음.

## 무엇이 stable 인가
- stable handoff pack
- stable runtime foundation 관련 config 와 latest-output 설명 문서
- current frozen integrated result snapshot

## 무엇이 reference-only 인가
- GPVS inventory, GPVS usage mail draft, GPVS evidence summary snapshot
- GPVS 는 direct root-cause classifier 가 아님

## 무엇이 triage-only 인가
- cause candidate heuristic summary snapshot
- heuristic 은 field-trial triage-only 층임

## conalog가 먼저 써야 할 것
1. `package/stable_handoff/`
2. `package/runtime/`
3. `package/oneclick/`
4. 필요 시 `package/docs/`, `package/examples/`
""",
    "QUICKSTART.md": """# Quickstart

## 1. stable handoff CLI 먼저 사용
- `package/stable_handoff/README.md`
- `package/stable_handoff/RUNBOOK.md`

## 2. one-click foundation 사용
- `package/oneclick/OPS_ONECLICK_OPERATION_GUIDE_V1.md`

## 3. daily report 생성
- `package/oneclick/OPS_DAILY_REPORT_AUTOMATION_V1.md`
- `package/oneclick/daily_report_template.md`

## 4. optional experimental/reference output
- GPVS 관련 문서는 `package/docs/OPS_GPVS_EXTERNAL_DATA_INVENTORY_V1.md`
- heuristic 관련 snapshot 은 `package/examples/panel_day_engine_cause_candidate_summary_v1.csv`

## 운영 원칙
- stable output 을 먼저 읽어야 함
- reference_only 와 triage_only 는 stable default output 과 혼동하면 안 됨
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
- one-click 은 foundation 이며 full production scheduler 가 아님
- stable output 과 experimental/reference output 은 혼동하면 안 됨
""",
    "DELIVERY_MANIFEST.md": """# Delivery Manifest

## 먼저 볼 것
1. `package/stable_handoff/`
2. `package/runtime/`
3. `package/oneclick/`

## 폴더별 의미
- `package/stable_handoff/`: stable handoff docs/config/examples
- `package/runtime/`: runtime guide, failure handling, latency/readiness report, runtime config
- `package/oneclick/`: one-click guide, daily-report guide, template
- `package/docs/`: comparison, GPVS inventory, GPVS mail draft, coverage/performance, integrated table pointer
- `package/examples/`: stable snapshot, reference-only summary, triage-only summary

## 주의
- stable / reference_only / triage_only 구분은 `final_delivery_manifest_v1.csv` 를 기준으로 읽어야 함
""",
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
    shutil.copytree(src, dst, dirs_exist_ok=True)


def relative_to_release(path: Path) -> str:
    return str(path.relative_to(RELEASE_ROOT))


def main() -> None:
    ensure_handoff_pack()
    if PACKAGE_ROOT.exists():
        shutil.rmtree(PACKAGE_ROOT)
    PACKAGE_ROOT.mkdir(parents=True, exist_ok=True)
    for dirname in ["docs", "stable_handoff", "runtime", "oneclick", "examples"]:
        (PACKAGE_ROOT / dirname).mkdir(parents=True, exist_ok=True)

    manifest_rows: list[dict[str, object]] = []

    for filename, content in TOP_LEVEL_DOCS.items():
        path = RELEASE_ROOT / filename
        write_text(path, content)
        manifest_rows.append(
            {
                "relative_path": relative_to_release(path),
                "artifact_kind": "release_doc",
                "stability_level_ko": "documentation",
                "included_flag": 1,
                "note_ko": "release top-level 안내 문서",
            }
        )

    copy_tree(HANDOFF_ROOT, PACKAGE_ROOT / "stable_handoff")
    for path in sorted((PACKAGE_ROOT / "stable_handoff").rglob("*")):
        if path.is_file():
            manifest_rows.append(
                {
                    "relative_path": relative_to_release(path),
                    "artifact_kind": "stable_handoff_asset",
                    "stability_level_ko": "stable",
                    "included_flag": 1,
                    "note_ko": "stable conalog handoff pack 자산",
                }
            )

    for item in PACKAGE_ITEMS:
        copy_file(item["source"], item["dest"])
        manifest_rows.append(
            {
                "relative_path": relative_to_release(item["dest"]),
                "artifact_kind": item["artifact_kind"],
                "stability_level_ko": item["stability_level_ko"],
                "included_flag": 1,
                "note_ko": item["note_ko"],
            }
        )

    pointer_path = PACKAGE_ROOT / "docs/INTEGRATED_RESULT_TABLE_POINTER.md"
    write_text(pointer_path, PACKAGE_POINTER_TEXT)
    manifest_rows.append(
        {
            "relative_path": relative_to_release(pointer_path),
            "artifact_kind": "integrated_table_pointer",
            "stability_level_ko": "documentation",
            "included_flag": 1,
            "note_ko": "final integrated result table schema pointer",
        }
    )

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
            "본 release pack 은 assembly/packaging 전용 결과임. stable/default semantics 를 바꾸지 않았고, "
            "GPVS 는 reference_only, heuristic 은 triage_only 로만 유지하였음."
        ),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] materialized {RELEASE_ROOT}")


if __name__ == "__main__":
    main()
