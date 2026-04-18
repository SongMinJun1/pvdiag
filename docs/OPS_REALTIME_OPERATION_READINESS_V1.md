# OPS Realtime Operation Readiness V1

## 1. 목적
- 본 문서는 현재 conalog runtime/near-real-time operation이 어느 수준까지 준비되어 있는지 현재 측정 산출물을 기준으로 정리한 readiness summary 문서다.
- 본 문서는 production SLA 문서가 아니라 feasibility/readiness 판단 문서다.
- 외부 공개 freeze 기준은 여전히 `project-main-freeze-v9` 로 두어야 하며, 본 문서는 current main의 runtime foundation 정리 결과를 운영 설명용으로 요약한 문서다.

## 2. 현재 구현 범위
- 현재 공식 runtime entrypoint 는 `app/run_realtime.py` 다.
- 구현 범위는 full streaming 이 아니라 stable mini-batch inference foundation 이다.
- `once` mode 는 frozen conalog stable inference entrypoint 를 호출하여 latest output 구조를 생성하는 경로다.
- `poll` mode 는 production daemon 이 아니라 simple repeated wrapper feasibility 경로다.
- `run_oneclick.py`, daily report builder, stable handoff pack은 이 runtime foundation 위에서 동작한다.
- panel multiaxis verdict 는 primary 이고, conalog 는 direct operational interpretation layer 이다.
- GPVS 는 reference-only 이고, heuristic 은 triage-only 이다.

## 3. 측정된 runtime feasibility 결과
- current runtime readiness summary 기준 `once` mode 는 `measured_flag=1`, `latest_run_possible_flag=1`, `include_experimental_supported_flag=1` 이다.
- 같은 summary 기준 `poll` mode 역시 `measured_flag=1`, `latest_run_possible_flag=1`, `include_experimental_supported_flag=1` 이다.
- current runtime latency report 기준 측정된 시간은 다음과 같다.
  - `runtime_cli_help = 0.033848 seconds`
  - `runtime_once_dry_run = 0.352775 seconds`
  - `runtime_poll_dry_run = 0.364156 seconds`
  - `runtime_once_foundation = 0.292333 seconds`
  - `runtime_once_foundation_experimental = 0.301969 seconds`
- 위 수치는 synthetic foundation 입력과 wrapper 경로를 기준으로 측정된 수치다.
- 따라서 현재 문서가 보여주는 것은 “latest output 구조를 생성할 수 있는가”와 “foundation wrapper가 한 번 실행 가능한가”이지, production tail latency 보장은 아니다.

## 4. 아직 측정되지 않은 것
- current runtime latency report 에는 `runtime_continuous_streaming` 항목이 비어 있으며, note 는 “continuous streaming steady-state latency 는 이번 feasibility 단계에서 측정하지 않았음”으로 남아 있다.
- multi-process / multi-site concurrent runtime latency 는 측정되지 않았다.
- external queue, broker, daemon supervisor overhead 는 측정되지 않았다.
- production hardware 별 tail latency 와 SLA window 역시 측정되지 않았다.

## 5. 운영 가능성 판단
- 현재 수준에서는 “runtime feasibility foundation 은 있음”이라고 판단하는 것이 적절하다.
- stable latest output 구조, runtime log, failure log, one-click foundation, daily report foundation까지는 실제로 연결되어 있다.
- 즉 once 기반의 near-real-time mini-batch 운용 foundation 은 현재 가능하다고 볼 수 있다.
- 그러나 poll mode 를 포함한 현재 runtime wrapper를 production-grade streaming service 로 바로 등치시키면 안 된다.
- 현재 판단은 readiness/feasibility 수준이지 production SLA 수준이 아니다.

## 6. 현재 한계
- 입력은 synthetic foundation sample 을 포함한다.
- poll mode 는 실서비스 daemon 이 아니라 wrapper feasibility 단계다.
- include-experimental 지원이 가능하더라도, GPVS 는 reference-only 이고 heuristic 은 triage-only 이므로 stable default output 과 분리해서 읽어야 한다.
- current runtime foundation 은 detector retraining, one-click scheduler, UI auth/session, queue-based automation을 포함하지 않는다.

## 7. 다음 단계
- 실제 운영 입력을 사용한 repeated once-run 측정을 추가할 필요가 있다.
- poll mode 의 장시간 반복 실행 안정성과 failure recovery 패턴을 따로 측정할 필요가 있다.
- production hardware / deployment boundary / scheduler 연동 시의 latency 와 failure mode 를 별도 실험으로 확보할 필요가 있다.
- 그 이후에도 stable default output, GPVS reference-only, heuristic triage-only 원칙은 그대로 유지해야 한다.
