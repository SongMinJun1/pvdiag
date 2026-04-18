# OPS Runtime Inference Guide V1

## 1. 목적
- 본 문서는 conalog 운영을 위한 runtime feasibility foundation 사용법을 정리한 안내서다.
- 이번 단계는 full streaming 이 아니라 stable mini-batch inference feasibility 를 확인하는 목적이다.
- panel multiaxis verdict 는 primary 이고, conalog 는 direct operational interpretation layer 로 사용한다.
- GPVS 는 reference-only 이고, heuristic 은 triage-only 이다.

## 2. 실행 진입점
- 공식 runtime CLI 는 `app/run_realtime.py` 다.
- training 은 포함하지 않으며 inference-only wrapper 로만 동작한다.

## 3. once vs poll
- `--mode once` 는 한 번의 stable mini-batch inference 를 수행하는 경로다.
- `--mode poll` 는 foundation 단계의 반복 wrapper 개념을 검증하는 경로다.
- 이번 버전의 poll mode 는 production-grade daemon 이 아니라 wrapper feasibility 확인용으로 읽어야 한다.

## 4. dry-run 먼저 수행
```bash
python app/run_realtime.py \
  --dry-run \
  --input-root . \
  --output-root /tmp/pvdiag_runtime_dryrun \
  --config config/runtime.yaml \
  --mode once \
  --include-experimental off
```

- dry-run 은 config/path 와 latest output 계획을 검증한다.
- dry-run 은 full inference completion 을 주장하지 않는다.

## 5. stable vs experimental output
- stable default output 은 `latest/` 아래의 conalog-facing 결과다.
- stable default output 은 다음 파일을 우선한다.
  - `latest/conalog_panel_result_v1.csv`
  - `latest/conalog_site_summary_v1.csv`
  - `latest/conalog_run_metadata_v1.json`
  - `latest/runtime_log_v1.jsonl`
  - `latest/failure_log_v1.jsonl`
- `--include-experimental on` 일 때만 `latest/conalog_reference_sidecar_v1.csv` 를 추가할 수 있다.
- experimental sidecar 안의 GPVS 는 reference-only 이고 heuristic 은 triage-only 이다.

## 6. 기대 출력 디렉터리 레이아웃
```text
<output-root>/
  latest/
    conalog_panel_result_v1.csv
    conalog_site_summary_v1.csv
    conalog_run_metadata_v1.json
    runtime_log_v1.jsonl
    failure_log_v1.jsonl
    conalog_reference_sidecar_v1.csv   # include-experimental=on 일 때만
```

## 7. 운영 해석 원칙
- stable output 을 delivery/use 기본값으로 읽는다.
- experimental/reference output 은 stable default output 과 분리해서 읽는다.
- conalog naming 만 사용하며 kernel-log 라는 명칭은 새 runtime 문서에서 사용하지 않는다.
