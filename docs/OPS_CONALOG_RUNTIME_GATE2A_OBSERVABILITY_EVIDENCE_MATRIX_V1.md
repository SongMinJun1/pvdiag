<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1

## 1. 목적
Gate 2는 `신호의 역할`을 잠갔다.
하지만 그것만으로는 부족하다.

같은 신호라도,
- 어떤 판단은 전기 신호만으로 말해도 되고
- 어떤 판단은 위치/공통원인 확인이 있어야 하고
- 어떤 판단은 온도/외부 센서/차단 범위 정보 없이는 말하면 안 된다.

이 문서는 다음을 잠그기 위한 초안이다.
- 어떤 판단을 하려면 어떤 관측 축이 최소한 있어야 하는가
- 어떤 축이 없으면 `보류`, `원인미확정`, `추가 확인 필요`로 내려야 하는가
- 어떤 판단은 operator-facing에서 금지하고 analyst-facing에서만 허용해야 하는가

## 2. 사용 규칙
- 이 문서는 `알고리즘 수식` 문서가 아니라 `증거 가용성 계약` 문서다.
- 여기서 `필수`라고 적힌 축이 없으면, 그 판단은 잠그지 않거나 `보류`로 내려야 한다.
- 여기서 `권장`이라고 적힌 축이 없으면, analyst-facing에선 말할 수 있어도 operator-facing에선 낮은 확신도로 표현해야 한다.
- 여기서 `없으면 금지`라고 적힌 축이 없는데도 해당 판단을 direct label로 노출하면 설계 위반으로 본다.

## 3. 상태
- 상태: `draft`
- 현재 목적:
  - Gate 6 survey에서 드러난 누락 축을 Gate 3~6 전체에 반영하기 위한 최소 계약 초안
- 아직 하지 않는 것:
  - 센서 구현 여부별 site-specific branching
  - threshold patch
  - report column patch

## 4. 관측 축 분류

### 4.1 E0. 전기 상대 신호 축
예:
- `mid_ratio`
- `mid_v_ratio`
- `mid_i_ratio`
- `v_drop`
- `critical_source`
- `fault_like_day`
- `critical_fault`
- `critical_confirmed`
- `final_fault`

의미:
- panel_day_engine과 runtime이 직접 계산하는 핵심 전기 상대 신호

### 4.2 E1. 시간 전개 축
예:
- `pre_ews`
- `ews_warning`
- `pre_alarm`
- `prefault_cond_*`
- `anom_subtype:degradation`
- alert run length
- onset / trigger / final date 관계

의미:
- 단발 이상인지, 누적 경고인지, 급락 종결인지, 진행성 악화인지 판단하는 축

### 4.3 E2. 기준군/신뢰도/공통원인 축
예:
- peer availability
- reference quality
- group-off / site event 여부
- common-cause 의심 여부
- singleton vs clustered 여부

의미:
- 지금 보는 이상이 panel-local인지, 공통원인인지, 기준군이 믿을 만한지 판단하는 축

### 4.4 E3. 범위/위치 축
예:
- 모듈 위치
- 서브스트링/스트링/그룹 소속
- 인접 모듈 패턴
- locus 분류

의미:
- 모듈 국소, 그룹, 인버터/외부 쪽 영향을 구분하는 축

### 4.5 E4. 운영 이벤트/작업 이력 축
예:
- 최근 작업일
- 통신/운영 이벤트
- 점검/교체 이력
- 사이트 운용 특이사항

의미:
- 작업/교체/운영 이벤트 때문에 생긴 비정상과 실제 고장/전조를 구분하는 축

### 4.6 E5. 열/외부 센서 축
예:
- 온도
- 외부 연기/화재 센서
- 접속반 외부 센서

의미:
- 전기 이상을 safety/control lane으로 승격할 수 있는지 판단하는 축

### 4.7 E6. 제어/차단 가능 범위 축
예:
- 모듈 차단 가능
- 스트링/접속반 차단 가능
- 원격 차단 연계 여부
- 차단 우선순위 정책

의미:
- maintenance action과 safety/control action을 분리하고, 실제 개입 범위를 결정하는 축

## 5. 증거 가용성 등급
| 등급 | 의미 |
| --- | --- |
| `필수` | 없으면 그 판단을 direct label로 말하면 안 됨 |
| `필수 또는 보류` | 없으면 `보류/원인미확정/추가 확인 필요`로 내려야 함 |
| `권장` | 없더라도 말할 수는 있지만 확신도를 낮추거나 analyst-facing으로 제한해야 함 |
| `설명용` | 판단의 직접 조건은 아니지만 이유 설명에 유용 |
| `없으면 금지` | 해당 축이 없는데 그 판단을 노출하면 안 됨 |

## 6. 판단별 관측 가능성 매트릭스

### 6.1 전조 흔적
| 축 | 요구 수준 | 이유 |
| --- | --- | --- |
| E0 전기 상대 신호 | 필수 | 전기 이상 자체가 있어야 함 |
| E1 시간 전개 | 필수 | 단발 이상과 누적 경고를 구분해야 함 |
| E2 기준군/공통원인 | 권장 | 공통원인 오염을 줄이기 위함 |
| E3 범위/위치 | 설명용 | locus 해석에 도움 |
| E4 운영 이벤트 | 권장 | 작업일 영향 배제 필요 |
| E5 열/외부 센서 | 불필요 | precursor trace 자체엔 직접 필수 아님 |
| E6 제어/차단 범위 | 불필요 | precursor trace 자체엔 직접 필수 아님 |

정책:
- E0와 E1이 없으면 `전조 흔적`이라고 말하지 않는다.
- E2/E4가 없으면 analyst-facing trace는 가능하지만 operator-facing에선 확신도를 낮춘다.

### 6.2 precursor candidate
| 축 | 요구 수준 | 이유 |
| --- | --- | --- |
| E0 전기 상대 신호 | 필수 | 전조 신호 기반 필요 |
| E1 시간 전개 | 필수 | 누적/반복 조건 필요 |
| E2 기준군/공통원인 | 필수 또는 보류 | panel-local precursor인지 판별 필요 |
| E3 범위/위치 | 권장 | locus 해석 정교화 |
| E4 운영 이벤트 | 필수 또는 보류 | 작업일/운영 이벤트 영향 배제 필요 |
| E5 열/외부 센서 | 불필요 | precursor candidate 자체엔 직접 필수 아님 |
| E6 제어/차단 범위 | 불필요 | precursor candidate 자체엔 직접 필수 아님 |

정책:
- E2 또는 E4가 비어 있으면 `precursor candidate` 직접 승격보다 `고위험 관찰` 또는 `보류`가 안전하다.
- 공통원인 의심이 남아 있으면 panel-local precursor로 direct label 금지.

### 6.3 고위험 관찰
| 축 | 요구 수준 | 이유 |
| --- | --- | --- |
| E0 전기 상대 신호 | 필수 | 강한 이상 축 필요 |
| E1 시간 전개 | 필수 | 누적 또는 반복성 필요 |
| E2 기준군/공통원인 | 필수 | panel-local vs common-cause 분기 필요 |
| E3 범위/위치 | 권장 | 모듈/그룹 해석 분리 |
| E4 운영 이벤트 | 필수 또는 보류 | 작업 영향 배제 |
| E5 열/외부 센서 | 설명용 | safety lane 판단 전 보조 근거 |
| E6 제어/차단 범위 | 설명용 | 아직 direct action 전 단계 |

정책:
- `고위험 관찰`은 precursor보다 좁고 hard evidence보다 약한 상태다.
- E2/E4가 비면 analyst-facing엔 가능해도 operator-facing current 표엔 보수적으로 내려야 한다.

### 6.4 hard evidence
| 축 | 요구 수준 | 이유 |
| --- | --- | --- |
| E0 전기 상대 신호 | 필수 | `critical_*`, `final_fault` 등 핵심 |
| E1 시간 전개 | 필수 | confirm path와 duration 필요 |
| E2 기준군/공통원인 | 필수 또는 보류 | common-cause 오염 방지 |
| E3 범위/위치 | 권장 | panel-local인지 group-side인지 분리 |
| E4 운영 이벤트 | 권장 | 작업/운영 이벤트와 혼동 방지 |
| E5 열/외부 센서 | 불필요 | hard evidence 자체의 필수는 아님 |
| E6 제어/차단 범위 | 불필요 | 상태 판정 자체의 필수는 아님 |

정책:
- event semantics에서 hard evidence를 닫는 것과 operator-facing에서 고장 신호로 노출하는 것은 분리한다.
- E2가 약하면 event semantics는 가능해도 operator-facing current에서 `panel 고장 신호` direct 노출은 보수적으로 본다.

### 6.5 원인 후보
| 축 | 요구 수준 | 이유 |
| --- | --- | --- |
| E0 전기 상대 신호 | 필수 | phenotype 해석 필요 |
| E1 시간 전개 | 필수 | temporal pattern 필요 |
| E2 기준군/공통원인 | 필수 또는 보류 | common-cause를 원인 후보와 분리 |
| E3 범위/위치 | 필수 또는 보류 | locus가 원인 후보에 직접 영향 |
| E4 운영 이벤트 | 권장 | 작업/교체/운영 영향 반영 |
| E5 열/외부 센서 | 권장 | 일부 cause/safety 해석에 필요 |
| E6 제어/차단 범위 | 불필요 | 원인 후보 자체엔 직접 필수 아님 |

정책:
- E3가 없으면 `모듈 국소`, `그룹`, `외부` 계열 원인 후보를 강하게 말하면 안 된다.
- E4가 없으면 `설치 초기 불량`, `작업일 영향`, `운영 이벤트 영향`은 `investigation note` 수준으로만 둔다.

### 6.6 maintenance action
| 축 | 요구 수준 | 이유 |
| --- | --- | --- |
| E0 전기 상대 신호 | 필수 | 이상 근거 필요 |
| E1 시간 전개 | 필수 | 지속성/재발성 필요 |
| E2 기준군/공통원인 | 필수 | 공통원인 review와 panel maintenance 분리 |
| E3 범위/위치 | 필수 또는 보류 | 현장 점검 locus 결정 |
| E4 운영 이벤트 | 필수 또는 보류 | 작업/교체 이력 반영 |
| E5 열/외부 센서 | 권장 | 일부 현장 점검 우선순위에 도움 |
| E6 제어/차단 범위 | 설명용 | maintenance lane과 safety lane 분리 설명 |

정책:
- `세척`, `음영 구조 확인`, `배선/접속부 점검`, `MLPE/계측 동시 점검`은 E3/E4 없이 강하게 말하지 않는다.
- E2가 약하면 `maintenance_candidate`보다 `common_cause_review` 또는 `추가 확인 필요`가 안전하다.

### 6.7 safety / control action
| 축 | 요구 수준 | 이유 |
| --- | --- | --- |
| E0 전기 상대 신호 | 필수 | 전기 이상 감지 필요 |
| E1 시간 전개 | 필수 | 단발 노이즈 vs 실제 이상 구분 |
| E2 기준군/공통원인 | 필수 | 개입 범위 결정에 중요 |
| E3 범위/위치 | 필수 | 모듈 차단 vs 스트링/접속반 차단 판단 |
| E4 운영 이벤트 | 권장 | 작업 중 차단 오판 방지 |
| E5 열/외부 센서 | 필수 또는 보류 | safety lane direct 승격 핵심 |
| E6 제어/차단 범위 | 필수 또는 보류 | 실제 어떤 차단이 가능한지 필요 |

정책:
- E5 또는 E6가 비어 있으면 `자동 차단`, `모듈 차단 후보`, `스트링/접속반 차단 후보`를 direct recommendation으로 내지 않는다.
- 이 경우 `원격 차단 연계 검토`, `외부 센서 확인 필요`, `화재안전 정책 검토` 수준으로 낮춘다.

## 7. 축별 금지 규칙

### 7.1 온도/외부 센서 없이 직접 말하면 안 되는 것
- `화재안전 우선 정책`
- `즉시 차단 권고`
- `외부 화재/연기 기반 차단`

### 7.2 위치/범위 정보 없이 직접 말하면 안 되는 것
- `모듈 국소`
- `그룹/인버터 측 공통원인`
- `접속반/차단 범위 확장 필요`

### 7.3 운영 이벤트/작업 이력 없이 직접 말하면 안 되는 것
- `작업일 영향`
- `최근 작업으로 인한 일시 이상`
- `설치 초기 불량 가능성`의 강한 판정

### 7.4 공통원인 체크 없이 직접 말하면 안 되는 것
- panel-local precursor candidate
- panel-local maintenance recommendation
- panel-local hard evidence direct wording

## 8. operator-facing과 analyst-facing 차이

### 8.1 analyst-facing에서 허용되는 것
- E2/E4/E5가 약해도, 가정과 한계를 밝히며 가설 수준 분석 가능
- phenotype, boundary signal, competing candidates를 함께 노출 가능

### 8.2 operator-facing에서 보수적으로 내려야 하는 것
- E2가 약한 panel-local direct label
- E5/E6가 없는 safety/control direct recommendation
- E3가 없는 locus-specific maintenance instruction

## 9. 현재 코드 기준으로 가장 취약한 지점
- `fault_like_day`를 event semantics에서 쓰는 것과 operator-facing에서 읽는 것 사이의 증거 계약이 아직 약하다.
- `common-cause / group-off` 배제는 Gate 3 초안에 있지만, 실제로 어떤 관측 축으로 확정할지 아직 문서화가 약하다.
- `설치 초기 불량`, `제품 자체 특성/결함`, `작업일 영향`은 E4 없이 강하게 말하면 안 되는데 현재 Gate 6 survey에도 아직 inventory 수준으로만 있다.
- safety/control lane은 E5/E6가 있어야 하는데, 현재 output policy에는 이 관측 가능성 계약이 직접 반영되진 않았다.

## 10. Decision Log에 바로 올릴 질문
- `common-cause 의심`을 선언하는 최소 관측 조건은 무엇인가
- E4 운영 이벤트가 비어 있는 사이트에서 `작업일 영향`을 어떻게 다룰 것인가
- E5 열/외부 센서가 없는 사이트에서 safety/control lane은 어디까지 operator-facing에 열 것인가
- E3 위치/범위 정보가 약한 경우 `모듈 국소`와 `그룹`을 어느 수준까지 구분할 것인가
- `설치 초기 불량 가능성`은 E4 없이도 조사 메모 수준으로 허용할 것인가

## 11. Gate 2A 체크리스트
- 어떤 판단이 어떤 관측 축 없이는 말해지면 안 되는지 분명한가
- operator-facing과 analyst-facing의 증거 요구 수준이 구분되는가
- maintenance lane과 safety/control lane의 증거 요구 수준이 분리되는가
- panel-local과 common-cause를 가르는 최소 관측 조건이 있는가
- 보류/미확정 상태가 단순 실패가 아니라 설계된 출력 상태로 취급되는가

## 12. 근거 source
- [OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md)
- [OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md)
- [OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)
- [3사 회의록.md](</Users/b9gc/Documents/1. 현장 시스템과 현재 구축 상태/3사 회의록.md>)

## 13. 다음 연결 문서
- 상위 로드맵:
  - [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- 교차 게이트 설계 허점 감사:
  - [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)
- Gate 2 signal role matrix:
  - [OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md)
- Gate 2B canonical multi-axis result model:
  - [OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md)
