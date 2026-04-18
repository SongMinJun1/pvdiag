# OPS One-Click Operation Guide V1

## 1. 목적
- 본 문서는 conalog 운영 foundation 에서 non-developer 가 한 번의 명령 또는 최소 UI 로 stable 결과 묶음을 생성하는 절차를 설명한다.
- panel multiaxis verdict 는 primary 로 유지한다.
- conalog 는 direct operational interpretation layer 로 유지한다.
- GPVS 는 reference-only 이고, heuristic 은 triage-only 이다.

## 2. one-click 이 하는 일
- stable conalog runtime wrapper 실행
- frozen integrated result snapshot export 복사
- 선택적으로 experimental/reference export 복사
- 선택적으로 daily report markdown 생성

## 3. required paths / config
- `--input-root`: 입력 CSV root
- `--output-root`: 최신 결과를 쓸 root
- `--config`: 현재 foundation 에서는 `config/runtime.yaml`

## 4. stable vs experimental output
- stable output 이 기본이다.
  - `conalog_panel_result_v1.csv`
  - `conalog_site_summary_v1.csv`
  - `conalog_run_metadata_v1.json`
  - `integrated_result_table_v1.csv`
  - `integrated_result_summary_v1.csv`
  - `daily_report_v1.md`
  - `runtime_log_v1.jsonl`
  - `failure_log_v1.jsonl`
- experimental output 은 `--include-experimental on` 일 때만 추가된다.
  - `conalog_reference_sidecar_v1.csv`
  - `gpvs_evidence_pack_v1.csv`
  - `cause_candidate_heuristics_v1.csv`
- experimental output 은 stable default output 이 아니며 direct root-cause 결과로 읽으면 안 된다.

## 5. CLI usage
```bash
python app/run_oneclick.py --help
```

```bash
python app/run_oneclick.py \
  --dry-run \
  --input-root . \
  --output-root /tmp/pvdiag_oneclick_dryrun \
  --config config/runtime.yaml \
  --include-experimental off \
  --report on
```

```bash
python app/run_oneclick.py \
  --input-root delivery/conalog_handoff_v1/examples \
  --output-root /tmp/pvdiag_oneclick_run \
  --config config/runtime.yaml \
  --include-experimental on \
  --report on
```

## 6. Streamlit usage
- foundation UI entrypoint 는 `app/app_streamlit.py` 다.
- UI 는 다음 입력만 받는다.
  - input root path
  - output root path
  - config path
  - include experimental toggle
  - report toggle
  - dry-run toggle
- UI 역시 같은 `run_oneclick.py` 경로를 호출하므로 CLI 와 semantics 가 분리되지 않는다.

## 7. dry-run first
- dry-run 을 먼저 수행해 latest 경로, runtime metadata, runtime log, failure log, one-click plan 을 확인한다.
- foundation 단계이므로 production scheduler 나 auth/session 요구사항은 포함하지 않는다.

## 8. naming 원칙
- 새 운영 문서와 output 설명에는 conalog naming 만 사용한다.
- kernel-log 라는 명칭은 본 one-click foundation 문서에서 사용하지 않는다.
