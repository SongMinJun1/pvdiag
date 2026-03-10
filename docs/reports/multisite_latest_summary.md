# Multisite Latest Summary

## 1. 목적
- 최신 4사이트 rerun 결과를 한 문서로 고정한다.
- GPVS-informed phenotype tagging 1차 결과를 함께 요약한다.

## 2. 사이트별 rerun 요약

| site | raw_first | raw_last | raw_count | out_first | out_last | out_count | core_panels | dead_count | critical_count | online_diag_count | final_fault_count |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| kernelog1 | 2024-09-06 | 2026-02-18 | 529 | 2024-11-05 | 2026-02-18 | 469 | 349 | 66 | 7 | 72 | 72 |
| sinhyo | 2024-10-29 | 2026-02-19 | 479 | 2024-12-28 | 2026-02-19 | 419 | 117 | 0 | 0 | 0 | 0 |
| gangui | 2025-04-08 | 2026-02-19 | 318 | 2025-06-07 | 2026-02-19 | 258 | 230 | 22 | 18 | 40 | 28 |
| ktc_ess | 2024-08-13 | 2026-02-19 | 533 | 2024-10-12 | 2026-02-19 | 473 | 187 | 0 | 2 | 2 | 1 |

## 3. Phenotype / Dominant Family

### phenotype count

| site | compound | shape | instability | unclear |
| --- | ---: | ---: | ---: | ---: |
| kernelog1 | 72 | 0 | 1 | 0 |
| sinhyo | 0 | 0 | 0 | 0 |
| gangui | 27 | 13 | 0 | 0 |
| ktc_ess | 2 | 0 | 0 | 0 |

### dominant_family count

| site | electrical | shape | instability |
| --- | ---: | ---: | ---: |
| kernelog1 | 55 | 2 | 16 |
| sinhyo | 0 | 0 | 0 |
| gangui | 18 | 20 | 2 |
| ktc_ess | 0 | 2 | 0 |

## 4. 핵심 해석
- `kernelog1`: phenotype count만 보면 `compound`가 지배적이지만, dominant_family 기준으로는 `electrical=55`, `instability=16`, `shape=2`다. 즉 최신 rerun 기준 사건군의 중심 축은 electrical 쪽으로 보는 편이 맞다.
- `gangui`: phenotype은 `compound=27`, `shape=13`으로 보이지만, dominant_family는 `electrical=18`, `shape=20`, `instability=2`다. 따라서 gangui는 shape 중심 경향이 있으면서도 electrical 성격이 완전히 없는 것은 아니다.
- `ktc_ess`: 이벤트 수는 적고, dominant_family 기준으로는 `shape=2`만 남는다.
- `sinhyo`: 최신 rerun 기준 `online_diag_count=0`이며 phenotype 이벤트도 없다.

## 5. 현장 근거
- 현재 수기 현장 근거는 모두 `gangui` 관련으로만 해석한다.
- `모듈 출력 저하`는 gangui의 electrical 기대 사례지만, `2025-04-24 14:19 / 2025-04-25 10:15`는 발생시각이 아니라 발견 또는 기록 시각일 가능성이 있다.
- 또한 현재 latest rerun score 시작일보다 이른 시점이므로 exact temporal validation은 하지 않았고, 정성 근거로만 사용한다.
- `스트링 단선`, `GARD`, `BSTR`, `250414 특이사항` 모듈은 정적 상태 태그로만 사용하고 subgroup annotation에만 반영한다.

## 6. 한계
- 현재 phenotype은 exact fault class `F1~F7` 분류기가 아니라 축 기반 phenotype tagging이다.
- `compound` 비율이 높아 규칙 임계값과 family 결합 규칙을 더 조정할 여지가 있다.
- 이번 결과는 latest rerun 기반 refresh 결과다.

## 7. 다음 단계
- phenotype 규칙의 `compound / dominant_family` 관계를 더 정교하게 조정할지 검토한다.
- kernelog1, GPVS, TECNALIA를 합친 전체 검증 요약 문서로 연결한다.
