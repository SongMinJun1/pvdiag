#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = REPO_ROOT / "delivery/conalog_handoff_v1"
APP_SCRIPT = REPO_ROOT / "app/run_conalog_infer.py"

FILES: dict[str, str] = {
    "README.md": """# Conalog Handoff Pack V1

## What This Pack Is
- 본 pack은 conalog stable handoff foundation 을 외부 전달 가능한 형태로 묶은 첫 버전임.
- panel multiaxis verdict 는 primary semantics 로 유지함.
- conalog 는 direct operational interpretation layer 로 유지함.
- GPVS 는 reference-only 임.
- heuristic 은 triage-only 이며 stable default output 이 아님.

## Stable vs Experimental
- stable default output 은 `output/panel_result_v1.csv`, `output/site_summary_v1.csv`, `output/run_metadata_v1.json`, `output/error_log_v1.csv` 임.
- experimental output 은 `--include-experimental on` 일 때만 생성되는 `output/experimental_reference_result_v1.csv` 임.
- experimental output 의 GPVS/heuristic 필드는 direct root-cause output 으로 읽으면 안 됨.

## Quick Start
```bash
python app/run_conalog_infer.py \\
  --dry-run \\
  --input-root delivery/conalog_handoff_v1/examples \\
  --output-root /tmp/conalog_handoff_dryrun \\
  --config delivery/conalog_handoff_v1/config/default.yaml \\
  --include-experimental off
```

## Smoke Test
```bash
python delivery/conalog_handoff_v1/tests/smoke_test_conalog_handoff.py
```
""",
    "INPUT_SCHEMA.md": """# Input Schema

## Expected Input Directory Layout
- `input-root/` 아래에 config 가 가리키는 입력 CSV 가 있어야 함.
- 기본 config 에서는 `input_sample.csv` 를 기대함.

## Minimal Required File Naming Assumptions
- 기본값: `input-root/input_sample.csv`
- 실제 handoff 운영 시에는 `config/default.yaml` 의 `input_csv_name` 으로 제어함.

## Required Columns
- `site`
- `panel_id`

## Notes
- 본 handoff pack 은 conalog naming 만 사용함.
- full research tree 의 내부 feature schema 전체를 handoff 계약으로 노출하지 않음.
- dry-run 은 expected input 이 없어도 path/config 점검과 candidate csv 탐색 계획을 반환할 수 있음.
""",
    "OUTPUT_SCHEMA.md": """# Output Schema

## Stable Default Outputs
- `output/panel_result_v1.csv`
- `output/site_summary_v1.csv`
- `output/run_metadata_v1.json`
- `output/error_log_v1.csv`

## Stable `panel_result_v1.csv` Columns
- `site`
- `panel_id`
- `패널고장여부_ko`
- `사건유형_ko`
- `최종고장양상_ko`
- `conalog_원인군_ko`

## Stable `site_summary_v1.csv` Columns
- `site`
- `total_panel_count`
- `fault_panel_count`
- `non_fault_or_unresolved_count`
- `note_ko`

## Metadata Contract
`run_metadata_v1.json` 은 최소 아래 항목을 포함함.
- `generated_at_utc`
- `git_branch`
- `git_head`
- `config_path`
- `input_root`
- `output_root`
- `include_experimental`
- `dry_run`
- `note_ko`

## Optional Experimental Sidecar
- `output/experimental_reference_result_v1.csv`

이 sidecar 는 아래 성격의 보조 정보만 포함할 수 있음.
- GPVS reference-only field
- heuristic triage-only field

stable default output 과 experimental/reference output 은 반드시 분리해서 읽어야 함.
""",
    "ALGORITHM_SPEC.md": """# Algorithm Spec

## Primary Structure
- panel multiaxis verdict 가 primary 임.
- conalog 는 direct operational interpretation layer 임.

## Non-Primary Layers
- GPVS 는 reference-only 임.
- heuristic 은 triage-only 임.

## Delivery Principle
- stable default output 은 conalog-facing 결과만 포함함.
- experimental/reference output 은 opt-in sidecar 로만 분리함.
- direct root-cause 를 과장해서 확정 출력하면 안 됨.

## Foundation Scope
- 본 버전은 stable handoff foundation 이며 frozen detector logic 을 다시 정의하지 않음.
- handoff 계약과 실행 진입점 고정이 목적이지, research tree 전체를 외부 배포 계약으로 노출하는 단계가 아님.
""",
    "RUNBOOK.md": """# Runbook

## 1. Dry-Run First
```bash
python app/run_conalog_infer.py \\
  --dry-run \\
  --input-root delivery/conalog_handoff_v1/examples \\
  --output-root /tmp/conalog_handoff_dryrun \\
  --config delivery/conalog_handoff_v1/config/default.yaml \\
  --include-experimental off
```

## 2. Stable Run
```bash
python app/run_conalog_infer.py \\
  --input-root delivery/conalog_handoff_v1/examples \\
  --output-root /tmp/conalog_handoff_run \\
  --config delivery/conalog_handoff_v1/config/default.yaml \\
  --include-experimental off
```

## 3. Experimental Sidecar Run
```bash
python app/run_conalog_infer.py \\
  --input-root delivery/conalog_handoff_v1/examples \\
  --output-root /tmp/conalog_handoff_run_ref \\
  --config delivery/conalog_handoff_v1/config/default.yaml \\
  --include-experimental on
```

## 4. Reading Outputs
- 기본 전달은 stable output 기준으로 읽음.
- GPVS/heuristic sidecar 는 reference/triage 참고층으로만 읽음.
""",
    "KNOWN_LIMITS.md": """# Known Limits

- GPVS 는 direct classifier 가 아니라 reference-only 임.
- heuristic 은 experimental triage-only 임.
- stable delivery/use 에서는 stable output 을 우선해야 함.
- 본 pack 은 full research layout 을 외부 계약으로 그대로 노출하지 않음.
- 현재 runtime 은 foundation 단계이므로 contract-safe placeholder run 을 포함함.
""",
    "CHANGELOG.md": """# Changelog

## v1
- conalog stable handoff pack 초기 버전 추가
- stable default output contract 추가
- optional experimental sidecar contract 추가
- dry-run / smoke-test / sample files 추가
""",
    "config/default.yaml": """input_csv_name: input_sample.csv
output_subdir: output
panel_result_name: panel_result_v1.csv
site_summary_name: site_summary_v1.csv
metadata_name: run_metadata_v1.json
error_log_name: error_log_v1.csv
experimental_reference_name: experimental_reference_result_v1.csv
default_fault_status: 미확정
default_event_type: 불충분
default_terminal_pattern: 불충분
default_conalog_family: 불충분
""",
    "docker/Dockerfile": """FROM python:3.11-slim

WORKDIR /app
COPY . /app

ENTRYPOINT ["python", "app/run_conalog_infer.py"]
""",
    "examples/input_sample.csv": """site,panel_id,observation_date,alarm_flag
conalog,example-panel-001,2026-01-01,1
conalog,example-panel-002,2026-01-01,0
""",
    "tests/smoke_test_conalog_handoff.py": """#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACK_ROOT.parents[1]
APP_SCRIPT = REPO_ROOT / "app/run_conalog_infer.py"
CONFIG_PATH = PACK_ROOT / "config/default.yaml"
INPUT_ROOT = PACK_ROOT / "examples"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)


def main() -> None:
    for path in [
        PACK_ROOT / "README.md",
        PACK_ROOT / "INPUT_SCHEMA.md",
        PACK_ROOT / "OUTPUT_SCHEMA.md",
        PACK_ROOT / "ALGORITHM_SPEC.md",
        PACK_ROOT / "RUNBOOK.md",
        PACK_ROOT / "KNOWN_LIMITS.md",
        PACK_ROOT / "CHANGELOG.md",
        CONFIG_PATH,
        INPUT_ROOT / "input_sample.csv",
        APP_SCRIPT,
    ]:
        assert_true(path.exists(), f"missing required path: {path}")

    help_result = run([sys.executable, str(APP_SCRIPT), "--help"])
    assert_true(help_result.returncode == 0, f"--help failed: {help_result.stderr or help_result.stdout}")

    with tempfile.TemporaryDirectory(prefix="conalog_handoff_pack_") as tmp_dir:
        output_root = Path(tmp_dir) / "dry_run"
        result = run(
            [
                sys.executable,
                str(APP_SCRIPT),
                "--dry-run",
                "--input-root",
                str(INPUT_ROOT),
                "--output-root",
                str(output_root),
                "--config",
                str(CONFIG_PATH),
                "--include-experimental",
                "off",
            ]
        )
        assert_true(result.returncode == 0, f"dry-run failed: {result.stderr or result.stdout}")
        metadata_path = output_root / "output/run_metadata_v1.json"
        error_log_path = output_root / "output/error_log_v1.csv"
        assert_true(metadata_path.exists(), f"missing metadata: {metadata_path}")
        assert_true(error_log_path.exists(), f"missing error log: {error_log_path}")
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert_true(payload.get("dry_run") is True, "dry_run metadata flag must be true")
        assert_true(payload.get("include_experimental") == "off", "include_experimental metadata mismatch")


if __name__ == "__main__":
    main()
""",
}


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def materialize_examples() -> None:
    with tempfile.TemporaryDirectory(prefix="conalog_handoff_build_") as tmp_dir:
        output_root = Path(tmp_dir) / "example_run"
        result = subprocess.run(
            [
                sys.executable,
                str(APP_SCRIPT),
                "--input-root",
                str(PACK_ROOT / "examples"),
                "--output-root",
                str(output_root),
                "--config",
                str(PACK_ROOT / "config/default.yaml"),
                "--include-experimental",
                "off",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise SystemExit(f"failed to generate sample outputs: {result.stderr or result.stdout}")
        shutil.copy2(
            output_root / "output/panel_result_v1.csv",
            PACK_ROOT / "examples/output_panel_result_sample.csv",
        )


def main() -> None:
    for relative_path, content in FILES.items():
        write_file(PACK_ROOT / relative_path, content)
    materialize_examples()
    print(f"[OK] materialized {PACK_ROOT}")


if __name__ == "__main__":
    main()
