# OPS Runtime Failure Handling V1

## 1. 목적
- 본 문서는 conalog runtime feasibility foundation 에서 예상되는 실패 상황과 기본 대응 원칙을 정리한 문서다.
- 이번 단계는 runtime wrapper 와 failure logging 구조를 고정하는 것이 목적이지, full production automation 을 선언하는 단계가 아니다.

## 2. missing input handling
- `--input-root` 가 없거나 디렉터리가 아니면 runtime wrapper 는 실패로 종료한다.
- once mode 에서 downstream handoff config 가 기대하는 입력 CSV 가 없으면 latest failure log 에 기록하고 non-zero exit 로 종료한다.
- dry-run 에서는 expected input 이 없어도 candidate csv 탐색과 metadata 계획을 남길 수 있다.

## 3. missing config handling
- `--config` 파일이 없거나 필수 key 가 빠져 있으면 실패로 종료한다.
- 이 경우에도 가능하면 `<output-root>/latest/` 아래에
  - `conalog_run_metadata_v1.json`
  - `runtime_log_v1.jsonl`
  - `failure_log_v1.jsonl`
  를 남겨 운영자가 즉시 실패 원인을 확인할 수 있게 한다.

## 4. missing model/output dependency handling
- runtime wrapper 는 detector retraining 을 수행하지 않는다.
- runtime wrapper 는 frozen handoff entrypoint `app/run_conalog_infer.py` 와 handoff config 에 의존한다.
- handoff config 또는 downstream stable output 이 누락되면 dependency failure 로 기록한다.
- 이 failure 는 연구 알고리즘의 성능 문제가 아니라 runtime packaging 의존성 문제로 읽어야 한다.

## 5. include_experimental off fallback
- `--include-experimental off` 가 기본값이다.
- experimental sidecar 생성에 필요한 경로가 불확실하거나 외부 전달 안정성이 우선일 때는 off 를 유지한다.
- stable default output 은 experimental sidecar 없이도 완결되게 읽혀야 한다.

## 6. failure logging behavior
- `runtime_log_v1.jsonl` 은 정상/실패를 모두 남기는 운영 로그다.
- `failure_log_v1.jsonl` 은 실패 이벤트를 별도로 남기는 로그다.
- 실패 시 metadata 의 `run_status_ko` 와 `failure_message_ko` 를 함께 확인해야 한다.

## 7. 운영 원칙
- failure 가 있더라도 GPVS 를 direct classifier 로 승격해 우회하면 안 된다.
- heuristic 을 stable default output 으로 승격해 우회하면 안 된다.
- stable output 우선, experimental output 분리, latest failure log 우선 확인의 원칙을 유지해야 한다.
