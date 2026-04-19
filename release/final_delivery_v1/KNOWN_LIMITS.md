# Known Limits

- GPVS 는 reference-only 임
- heuristic 은 triage-only 임
- runtime 은 feasibility/readiness 이며 production SLA 가 아님
- one-click 은 foundation 이며 full production scheduler 가 아님
- stable output 과 experimental/reference output 은 혼동하면 안 됨
- dashboard 또는 외부 시스템은 문서를 scraping 하지 말고 `package/app/` entrypoint 를 직접 호출해야 함
- Python 3 설치는 여전히 필요함
- git executable 이 대상 장비에 없어도 demo/dry-run 흐름은 계속 수행 가능함
- git metadata 는 원본 저장소 밖에서 unavailable 일 수 있으나, 이는 stable dry-run 또는 stable output generation 을 막지 않음
