# Release Notes

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
