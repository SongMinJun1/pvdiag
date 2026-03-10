# Multisite Latest Summary

## 1. 목적
- 최신 4사이트 rerun 결과를 한 문서로 고정한다.
- GPVS-informed phenotype tagging 1차 결과를 함께 요약한다.

## 2. 사이트별 rerun 요약

| site | raw_first | raw_last | raw_count | out_first | out_last | out_count | core_panels | dead_count | critical_count | online_diag_count |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| kernelog1 | 2024-09-06 | 2026-02-18 | 529 | 2025-03-01 | 2026-02-18 | 353 | 349 | 2 | 2 | 4 |
| sinhyo | 2024-10-29 | 2026-02-19 | 479 | 2025-07-01 | 2026-02-19 | 234 | 117 | 0 | 0 | 0 |
| gangui | 2025-04-08 | 2026-02-19 | 318 | 2025-09-01 | 2026-02-19 | 172 | 230 | 22 | 17 | 39 |
| ktc_ess | 2024-08-13 | 2026-02-19 | 533 | 2025-07-01 | 2026-02-19 | 211 | 187 | 0 | 1 | 1 |

## 3. Phenotype Count

| site | electrical | shape | instability | compound | unclear |
| --- | ---: | ---: | ---: | ---: | ---: |
| kernelog1 | 0 | 0 | 1 | 3 | 0 |
| sinhyo | 0 | 0 | 0 | 0 | 0 |
| gangui | 0 | 12 | 2 | 25 | 0 |
| ktc_ess | 0 | 0 | 0 | 1 | 0 |

## 4. 핵심 해석
- `kernelog1`: 현재 최신 rerun 기준 이벤트는 4건이며, phenotype은 `compound` 3건과 `instability` 1건으로 요약된다.
- `gangui`: 이벤트가 가장 많고(39건), phenotype은 `compound`와 `shape` 중심이다.
- `ktc_ess`: 현재 이벤트 수는 1건으로 적고, phenotype은 `compound` 1건이다.
- `sinhyo`: 최신 rerun 기준 `online_diag_count=0`이며 phenotype 이벤트도 없다.

## 5. 현장 근거
- 현재 수기 현장 근거는 모두 `gangui` 관련으로만 해석한다.
- `모듈 출력 저하`는 electrical 기대 사례이지만, `2025-04-24 14:19 / 2025-04-25 10:15`는 발생시각이 아니라 발견 또는 기록 시각일 가능성이 있고 현재 latest rerun score 시작일(`2025-09-01`)보다 이르다.
- 따라서 `모듈 출력 저하`는 gangui의 약한 시간 앵커로만 남기고 direct temporal validation에는 사용하지 않는다.
- `스트링 단선`, `GARD`, `BSTR`, `250414 특이사항` 모듈은 정적 상태 태그 또는 설비 속성으로 보고 subgroup annotation에만 사용한다.
- 이번 문서에서는 exact field validation은 수행하지 않았고, 위 근거는 정성 보조 근거로만 사용한다.

## 6. 한계
- 현재 phenotype은 exact fault class `F1~F7` 분류기가 아니라 축 기반 phenotype tagging이다.
- `compound` 비율이 높아 규칙 임계값과 family 결합 규칙을 더 조정할 여지가 있다.
- 이번 결과는 latest wrappers로 rerun한 1차 결과 요약이다.

## 7. 다음 단계
- phenotype 규칙의 `compound / unclear` 경계 조정 여부를 검토한다.
- kernelog1, GPVS, TECNALIA를 합친 전체 검증 요약 문서로 연결한다.
