# Final Delivery Pack V1

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
