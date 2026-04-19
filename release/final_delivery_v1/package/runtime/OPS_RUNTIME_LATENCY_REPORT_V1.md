# OPS Runtime Latency Report V1

## 1. 보고 목적
- 본 문서는 conalog runtime feasibility foundation 에서 실제로 무엇을 측정하였고 무엇을 아직 측정하지 않았는지 구분하기 위한 보고서다.
- 본 문서는 production SLA 문서가 아니라 feasibility report 다.

## 2. 이번 단계에서 측정한 항목
- `app/run_realtime.py --help` 시작 시간
- runtime `once` dry-run 계획 생성 시간
- runtime `poll` dry-run 계획 생성 시간
- synthetic foundation 입력을 사용한 `once` stable wrapper 시간
- synthetic foundation 입력을 사용한 `once + include-experimental=on` wrapper 시간

## 3. 이번 단계에서 측정하지 않은 항목
- continuous streaming steady-state latency
- multi-process / multi-site concurrent runtime latency
- external queue, broker, daemon supervisor overhead
- production hardware 별 tail latency

## 4. 해석 원칙
- 이번 측정은 stable mini-batch inference wrapper feasibility 를 보기 위한 것이다.
- detector retraining 시간이나 historical backfill 전체 처리 시간은 runtime latency 에 포함하지 않는다.
- GPVS 는 reference-only 이고 heuristic 은 triage-only 이므로, runtime latency 보고에서도 stable default output 과 분리해서 읽어야 한다.

## 5. 왜 production SLA 가 아닌가
- 입력은 synthetic foundation sample 을 포함한다.
- poll mode 는 full daemon 이 아니라 feasibility wrapper 수준으로만 확인하였다.
- 따라서 이번 수치를 production real-time capable 선언으로 일반화하면 안 된다.

## 6. 현재 결론
- runtime wrapper 는 latest output 구조를 생성할 수 있는지 여부를 확인하는 단계까지는 도달하였다.
- 그러나 full streaming readiness 나 production SLA 는 별도 측정과 운영 검증이 필요하다.
