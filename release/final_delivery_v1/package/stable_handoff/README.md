# Conalog Handoff Pack V1

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
python app/run_conalog_infer.py \
  --dry-run \
  --input-root delivery/conalog_handoff_v1/examples \
  --output-root /tmp/conalog_handoff_dryrun \
  --config delivery/conalog_handoff_v1/config/default.yaml \
  --include-experimental off
```

## Smoke Test
```bash
python delivery/conalog_handoff_v1/tests/smoke_test_conalog_handoff.py
```
