# Algorithm Spec

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
