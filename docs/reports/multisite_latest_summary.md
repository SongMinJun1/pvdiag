# Multisite Latest Summary

## 1. 목적
- 최신 4사이트 rerun 결과를 한 문서로 고정한다.
- GPVS-informed phenotype tagging 1차 결과를 함께 요약한다.

## 2. 사이트별 rerun 요약

### 기간/산출 범위

| site | raw_first | raw_last | raw_count | out_first | out_last | out_count | core_panels |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Conalog | 2024-09-06 | 2026-02-18 | 529 | 2024-11-05 | 2026-02-18 | 469 | 349 |
| sinhyo | 2024-10-29 | 2026-02-19 | 479 | 2024-12-28 | 2026-02-19 | 419 | 117 |
| gangui | 2025-04-08 | 2026-02-19 | 318 | 2025-06-07 | 2026-02-19 | 258 | 230 |
| ktc_ess | 2024-08-13 | 2026-02-19 | 533 | 2024-10-12 | 2026-02-19 | 473 | 184 |

### latest ops snapshot

| site | latest_date | panel_count | alert_count | online_diag_count | critical_count | dead_count | final_fault_count |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Conalog | 2026-02-18 | 349 | 72 | 72 | 7 | 66 | 1 |
| sinhyo | 2026-02-19 | 117 | 20 | 0 | 0 | 0 | 0 |
| gangui | 2026-02-19 | 230 | 40 | 40 | 18 | 22 | 3 |
| ktc_ess | 2026-02-19 | 184 | 2 | 2 | 2 | 0 | 1 |

## 3. Phenotype / Dominant Family

### phenotype count

| site | compound | shape | instability | unclear |
| --- | ---: | ---: | ---: | ---: |
| Conalog | 72 | 0 | 1 | 0 |
| sinhyo | 0 | 0 | 0 | 0 |
| gangui | 27 | 13 | 0 | 0 |
| ktc_ess | 2 | 0 | 0 | 0 |

### dominant_family count

| site | electrical | shape | instability |
| --- | ---: | ---: | ---: |
| Conalog | 55 | 2 | 16 |
| sinhyo | 0 | 0 | 0 |
| gangui | 18 | 20 | 2 |
| ktc_ess | 0 | 2 | 0 |

## 4. 핵심 해석
- `Conalog`: latest 기준으로 `alert_count=72`, `online_diag_count=72`, `critical_count=7`, `dead_count=66`이며, dominant_family는 `electrical=55`, `instability=16`, `shape=2`다.
- `gangui`: latest 기준으로 `alert_count=40`, `online_diag_count=40`, `critical_count=18`, `dead_count=22`가 실제로 잡힌다. phenotype은 `compound=27`, `shape=13`이지만 dominant_family는 `electrical=18`, `shape=20`, `instability=2`라서 electrical 성격이 완전히 없는 것은 아니다.
- `ktc_ess`: latest 기준 `alert_count=2`, `online_diag_count=2`, `critical_count=2`, `final_fault_count=1`로 소수 이벤트만 잡히며 dominant_family는 `shape=2`다.
- `sinhyo`: latest 기준 `alert_count=20`이 있지만 이는 fault diagnosis가 아니라 high-risk latest alerts로 해석한다. `online_diag_count=0`, `critical_count=0`, `dead_count=0`이며 phenotype 이벤트는 없다.

## 5. 현장 근거
- 현재 수기 현장 근거는 모두 `gangui` 관련으로만 해석한다.
- `모듈 출력 저하`는 gangui의 electrical 기대 사례지만, `2025-04-24 14:19 / 2025-04-25 10:15`는 발생시각이 아니라 발견 또는 기록 시각일 가능성이 있다.
- 또한 현재 latest rerun score 시작일보다 이른 시점이므로 exact temporal validation은 하지 않았고, 정성 근거로만 사용한다.
- `스트링 단선`, `GARD`, `BSTR`, `250414 특이사항` 모듈은 정적 상태 태그로만 사용하고 subgroup annotation에만 반영한다.

## 6. 한계
- 현재 phenotype은 exact fault class `F1~F7` 분류기가 아니라 축 기반 phenotype tagging이다.
- `compound` 비율이 높아 규칙 임계값과 family 결합 규칙을 더 조정할 여지가 있다.
- 이번 결과는 latest rerun 기반 refresh 결과이며, 운영용 latest는 train 구간 고정 + score 구간 자동 확장 구조를 따른다.

## 7. 다음 단계
- phenotype 규칙의 `compound / dominant_family` 관계를 더 정교하게 조정할지 검토한다.
- Conalog, GPVS, TECNALIA를 합친 전체 검증 요약 문서로 연결한다.
