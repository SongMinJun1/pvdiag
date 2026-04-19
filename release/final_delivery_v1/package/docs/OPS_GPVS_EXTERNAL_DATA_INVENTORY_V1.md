# OPS GPVS External Data Inventory V1

## 1. 문서 목적
- 본 문서는 현재 프로젝트에서 실제로 사용한 GPVS external data/assets가 무엇인지, 무엇을 위해 사용하였는지, 무엇에는 사용하지 않았는지를 명확히 정리하기 위한 inventory 문서다.
- 대외 공개 freeze 기준은 여전히 `project-main-freeze-v9` 로 두어야 하며, 본 문서는 그 위에 쌓인 내부 reference usage 정리를 외부 설명용으로 재구성한 문서다.

## 2. 실제 사용한 GPVS 자산
- GPVS original family-eval artifact를 사용하였음.
  - 현재 model metrics 기준 `closed_world_macro_f1=0.936508` 수치가 존재하였음.
  - 다만 이 수치는 GPVS original family-eval artifact의 수치이지, current panel multiaxis verdict의 direct root-cause 성능 수치가 아님.
- recovered GPVS by-type artifact를 사용하였음.
  - current GPVS evidence summary note 에 `provenance=original_trained_head_recovered`, `rebuild_attachable=1` 이 명시되어 있음.
  - recovered by-type artifact는 detailed type reference attach와 reference explanation 정리에 사용하였음.
- GPVS compatibility / matching / evidence pack derived asset을 사용하였음.
  - compatibility 결과는 GPVS가 reference-only 로만 사용되어야 한다는 guardrail 근거로 사용하였음.
  - matching policy는 core/auxiliary/reference reservation rule을 고정하는 데 사용하였음.
  - evidence pack은 current 6 fault sample 기준 GPVS usage summary를 정리하는 데 사용하였음.

## 3. recovered by-type artifact 현황
- recovered by-type artifact는 현재 프로젝트에서 “존재 여부만 확인된 미사용 자산”이 아니라, current reference attach 경로를 성립시키는 실제 사용 자산이다.
- evidence summary 기준 external evidence available count 는 6 이며, current frozen sample 기준 모든 fault panel에서 external evidence가 확인되어 있다.
- 동일 summary 기준 `core_reference_count=2`, `auxiliary_reference_count=4`, `not_recommended_count=0` 이다.
- 즉 recovered by-type artifact는 current frozen sample에서 GPVS reference layer를 붙이는 근거 자산으로는 활용되고 있으나, 직접 판정기를 대체하는 용도로는 사용되지 않는다.

## 4. GPVS가 현재 기여하는 것
- GPVS는 external reference pattern을 제공한다.
- GPVS는 현재 panel multiaxis verdict와 conalog 위에 “이 패널이 외부 GPVS 실험 시나리오 중 어떤 pattern군과 닮았는가”를 설명하는 보조 근거를 제공한다.
- current evidence summary 기준 GPVS usage는 다음과 같이 정리된다.
  - core reference: 2
  - auxiliary reference: 4
  - compatibility reference-only flag: 1
- 따라서 GPVS는 current stack에서 explanation 보강과 triage 보조에는 기여하나, primary 판정층의 자리를 대체하지는 않는다.

## 5. GPVS가 현재 하지 않는 것
- GPVS는 direct root-cause classifier가 아니다.
- GPVS는 panel multiaxis verdict를 대체하는 primary output이 아니다.
- GPVS는 conalog를 대체하는 direct operational interpretation layer가 아니다.
- GPVS detailed code나 scenario family를 실제 물리 root-cause 이름으로 1대1 번역해서 사용하면 안 된다.
- current model metrics에 family-eval artifact 수치가 존재하더라도, 이를 current front-facing integrated table의 direct diagnosis metric으로 읽으면 안 된다.

## 6. 현재 운영 원칙
- panel multiaxis verdict가 primary 임.
- conalog는 direct operational interpretation layer 임.
- GPVS는 reference-only 임.
- cause candidate heuristic은 triage-only 임.
- 따라서 GPVS는 현재 운영에서 “외부 reference pattern 설명층”으로만 사용하며, direct root-cause classifier처럼 읽지 않는 것이 공식 원칙이다.

## 7. 요약 표
| 항목 | 현재 상태 |
| --- | --- |
| 실제 사용한 external GPVS 자산 | original family-eval artifact, recovered by-type artifact, compatibility/matching/evidence derived asset |
| recovered by-type artifact 상태 | current reference attach 경로에 실제 사용 중임 |
| current frozen sample support | external evidence available count=6 |
| current usage tier | core reference=2, auxiliary reference=4 |
| GPVS가 하는 일 | external reference pattern 제공, explanation 보강, triage 보조 |
| GPVS가 하지 않는 일 | direct root-cause classifier, primary 판정층, conalog 대체 |
