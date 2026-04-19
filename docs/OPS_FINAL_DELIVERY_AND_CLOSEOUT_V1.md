# OPS Final Delivery And Closeout V1

## 1. 목적
- 본 문서는 `release/final_delivery_v1` 단계에서 무엇을 최종 전달 대상으로 보고, 어떤 순서로 release 및 closeout 을 진행하는지 정리한 overview 문서임.
- panel multiaxis verdict 는 primary 결과층임.
- conalog 는 direct operational interpretation layer 임.
- GPVS 는 reference-only 층임.
- heuristic 은 triage-only 층임.

## 2. 현재 포함 범위
- stable 범위에는 conalog stable handoff pack, package/app 실행 entrypoint, package/bin Windows wrapper, package/config runtime 설정, current frozen integrated result snapshot 이 포함됨.
- reference-only 범위에는 GPVS external data inventory, GPVS usage 설명 문서, GPVS evidence summary 와 같은 보조 참조 자산이 포함됨.
- triage-only 범위에는 cause candidate heuristic summary 와 같이 field-trial triage 지원용 자산이 포함됨.
- documentation 범위에는 conalog rulebase vs hybrid 비교, fault coverage/model performance, runtime readiness, one-click/daily-report guide 와 같은 설명 문서가 포함됨.
- final front-facing integrated table schema 는 현재 고정되어 있으며 본 단계에서 변경하지 않음.

## 3. stable / reference-only / triage-only 경계
- stable 은 conalog 운영 전달의 기본 경로로 사용 가능한 자산을 뜻함.
- stable 에서는 panel multiaxis verdict 와 conalog 해석 결과를 우선적으로 읽어야 함.
- reference-only 는 GPVS 와 같이 해석 보조 축으로만 사용하는 자산을 뜻함.
- GPVS 는 direct root-cause classifier 로 읽으면 안 되며 stable default output 과 혼동하면 안 됨.
- triage-only 는 heuristic 과 같이 현장 점검 우선순위 보조에만 쓰는 자산을 뜻함.
- heuristic 은 최종 진단 확정 출력이 아니며 field-trial triage 용도로만 사용해야 함.

## 4. 최종 release 절차
- 현재 frozen public baseline 은 본 hotfix merge 전까지 `project-main-freeze-v10` 기준으로 읽어야 함.
- release 전에는 stable handoff, runtime foundation, one-click foundation, coverage/performance, validation framework 의 문서와 예시 산출물이 현재 main 상태와 모순되지 않는지 확인해야 함.
- `research/prognostics/build_final_delivery_pack_v1.py` 를 실행하여 `release/final_delivery_v1/package/` 를 materialize 하여야 함.
- 생성 후 `final_delivery_manifest_v1.csv` 와 `final_delivery_summary_v1.json` 을 확인하여 stable / reference-only / triage-only 구분이 올바르게 반영되었는지 점검하여야 함.
- 외부 전달 시에는 `package/bin/run_demo.bat` 를 시연 시작점으로, `package/bin/run_real.bat` 를 실제 입력 폴더 실행 시작점으로 안내하여야 함.
- dashboard 또는 외부 시스템 연동은 `package/app/run_conalog_infer.py` 또는 `package/app/run_oneclick.py` 를 직접 호출하는 방식으로 정리하여야 함.

## 5. closeout 절차
- closeout 에서는 stable 전달 자산과 experimental/reference 자산이 혼합되지 않았는지 다시 확인하여야 함.
- release pack 에 포함된 문서, config, examples, summary 가 실제 현재 frozen semantics 와 일치하는지 점검하여야 함.
- package/app, package/config, package/bin 이 실제 executable delivery 경로로 동작하는지 점검하여야 함.
- runtime 은 feasibility/readiness 단계임을, one-click 은 foundation 단계임을, GPVS 와 heuristic 은 stable default output 이 아님을 closeout note 에 명시하여야 함.
- 최종 closeout 기록에는 전달 경로, 사용 시작점, 비주장 항목, known limits 를 함께 남겨야 함.

## 6. 현재 한계와 비주장 항목
- GPVS 는 reference-only 이며 direct root-cause 확정 기능을 주장하지 않음.
- heuristic 은 triage-only 이며 최종 진단 classifier 성숙도를 주장하지 않음.
- runtime 은 feasibility/readiness 결과만 확보된 상태이며 production SLA 를 주장하지 않음.
- one-click 은 operator foundation 이며 full production scheduler 또는 완전 자동 운영 체계를 주장하지 않음.
- 본 final delivery 단계는 assembly/packaging 중심 단계이며 알고리즘 semantics 상향이나 새로운 maturity claim 을 포함하지 않음.
