<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1

## 1. 목적
- 본 문서는 `runtime redesign`에서 이미 존재하는 신호들을 버리지 않고 `다축 score axis`로 올리는 기준선이다.
- 목적은 아래 여섯 가지다.
  - 현재 있는 신호를 `즉시 버릴 것`이 아니라 `어느 score 축에 어떻게 반영할 것인가`로 재정리한다.
  - 신호를 곧바로 라벨로 쓰지 않고 `signal -> score axis -> state/cause/action projection` 순서로 읽게 한다.
  - Gate 3 precursor, Gate 4 hard evidence, Gate 6 taxonomy/action이 같은 signal inventory를 공유하게 한다.
  - additive evidence, gating requirement, suppressor, reroute, explanation-only를 구분한다.
  - 반례 세트와 algorithm gating patch 사이의 중간 설계 문서 역할을 한다.
  - 나중에 weighted score, rule ensemble, hybrid scorecard로 갈 때 drift를 줄인다.

## 2. 이 문서의 위치
- Gate 2 signal role matrix는 `각 신호의 주 역할`을 잠갔다.
- Gate 2A는 `어떤 판단을 하려면 어떤 관측 축이 필요한가`를 잠갔다.
- Gate 2B는 `판단 결과를 어떤 canonical object로 담을 것인가`를 잠갔다.
- Gate 2C는 그 사이를 메우는 문서다.
  - 이미 존재하는 신호를
  - 어떤 score axis에 넣고
  - 어떤 방식으로 반영하고
  - 어떤 축에는 넣지 말아야 하는지
  를 정한다.

## 3. 사용 규칙
- 이 문서는 `기존 신호의 score mapping`을 잠그는 문서다.
- 이 문서만으로 threshold 숫자나 최종 weighting을 확정하지 않는다.
- 이 문서는 아래를 먼저 정한다.
  - 어떤 신호가 어떤 score axis에 들어가는가
  - additive인지 gating인지 suppressor인지
  - operator-facing에서 직접 점수명으로 노출 가능한가
- 이 문서가 잠기기 전에는 아래 패치를 금지한다.
  - score 이름만 만들고 signal 투입 기준 없이 코드에 억지 aggregation을 넣는 것
  - single signal을 단독 top1 상태로 곧장 승격하는 것
  - `fault_like_day`, `v_drop`, `critical_source`를 점수 없이 바로 최종 상태명으로 번역하는 것

## 4. 상태
- 상태: `working draft`
- 의미:
  - 현재 signal inventory를 기준으로 한 baseline map
  - 아직 numeric weight나 exact threshold는 잠그지 않음
  - 하지만 어떤 신호를 어떤 축에 넣을지는 먼저 고정함

## 5. 기본 원칙

### 5.1 신호는 바로 라벨이 아니다
- `pre_ews`가 있다고 곧바로 `precursor candidate`가 아니다.
- `critical_fault`가 있다고 곧바로 `final_fault`가 아니다.
- `v_drop`가 있다고 곧바로 bypass 확정이 아니다.

### 5.2 score axis는 의미가 달라야 한다
- `precursor_score`는 warning accumulation을 본다.
- `hard_evidence_score`는 confirm path strength를 본다.
- `common_cause_risk_score`는 panel-local 해석을 얼마나 눌러야 하는지 본다.
- `mlpe_ambiguity_score`는 패널 이상과 장치/제어 개입이 얼마나 섞여 있는지 본다.
- `actionability_score`는 실제로 다음 행동을 얼마나 강하게 추천할 수 있는지 본다.

### 5.3 같은 신호라도 축마다 역할이 다를 수 있다
- 예:
  - `v_drop`는 `hard_evidence_score`의 보조 근거이고
  - `precursor_score`의 설명 보조이며
  - `cause_axis`에서는 `전압강하형` phenotype 설명에 쓰인다.

### 5.4 관측 불충분은 가산이 아니라 보류 조건이다
- `common_cause`를 배제할 정보가 없으면 score를 무작정 올리지 않는다.
- `온도`, `외부 센서`, `운영 이벤트`가 없으면 safety/control score는 abstain 또는 낮은 confidence로 둔다.

## 6. 제안 score axis

### 6.1 `precursor_score`
- 질문:
  - hard evidence 이전에 다축 warning accumulation이 얼마나 있는가
- 쓰는 곳:
  - `전조 흔적`
  - `precursor candidate`
  - `고위험 관찰`
- 직접 노출:
  - operator-facing에는 점수 숫자보다 상태 projection만 노출

### 6.2 `hard_evidence_score`
- 질문:
  - 현재 시점에 고장 신호 경계 또는 confirm path가 얼마나 강한가
- 쓰는 곳:
  - `고장 신호`
  - `강한 고장 신호`
  - `최종 고장 신호`
- 직접 노출:
  - operator-facing에는 score가 아니라 `고장 신호 요약`으로 projection

### 6.3 `common_cause_risk_score`
- 질문:
  - 현재 패턴을 panel-local보다 group/base/site common-cause로 먼저 봐야 하는가
- 쓰는 곳:
  - panel-local score 억제
  - `보류`, `공통원인 검토 필요`
- 직접 노출:
  - operator-facing headline보다는 analyst/support 보조 축

### 6.4 `mlpe_ambiguity_score`
- 질문:
  - MLPE 제어응답/장치 이상/패널 이상이 얼마나 섞여 있는가
- 쓰는 곳:
  - cause 확정 보류
  - `원인 미확정`, `추가 확인 필요`
- 직접 노출:
  - analyst-facing 위주, operator-facing에는 `장치/제어 개입 가능성` 수준만 허용

### 6.5 `actionability_score`
- 질문:
  - 지금 무엇을 하라고 말할 수 있을 정도로 증거와 범위가 갖춰졌는가
- 쓰는 곳:
  - `monitor_only`
  - `singleton_review`
  - `maintenance_candidate`
  - `common_cause_review`
- 직접 노출:
  - operator-facing에서는 action lane projection으로만 노출

## 7. score 반영 방식 타입
| 타입 | 의미 | 예 |
| --- | --- | --- |
| `additive` | 점수 가산 근거 | `pre_ews`, `ews_warning`, `critical_fault` |
| `gating` | 최소 조건, 없으면 승격 금지 | `critical_confirmed`, `confirmed_fault`, evidence availability |
| `suppressor` | 다른 축 해석을 눌러야 하는 신호 | `group_off_like`, `data_bad`, common-cause indicators |
| `reroute` | 점수는 올리지 않고 해석 레인을 바꿈 | `mlpe ambiguity`, control scope hints |
| `explanation_only` | 점수보다는 설명에만 쓰는 신호 | `critical_source`, `mid_v_ratio`, `anom_subtype` |

## 8. 기존 신호 -> score axis 매핑
| 신호 | precursor_score | hard_evidence_score | common_cause_risk_score | mlpe_ambiguity_score | actionability_score | 반영 방식 | 비고 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pre_ews` | 예 | 아니오 | 아니오 | 아니오 | 약하게 예 | additive | 초기 warning accumulation |
| `ews_warning` | 예 | 아니오 | 아니오 | 아니오 | 약하게 예 | additive | primary warning 축 |
| `pre_alarm` | 예 | 아니오 | 아니오 | 아니오 | 예 | additive | 경고 강도 높음 |
| `prefault_B_effective` | 예 | 아니오 | 아니오 | 아니오 | 약하게 예 | additive | common-cause overlap 제거 후 precursor eligibility에 우선 반영, 단독 attention-grade trigger는 아직 금지 |
| `prefault_B_common_cause_overlap` | 아니오 | 아니오 | 예 | 아니오 | 약하게 예 | suppressor | raw helper는 남기되 panel-local precursor 승격은 눌러야 하는 common-cause overlap 신호 |
| `prefault_cond_mid` | 예 | 아니오 | 아니오 | 아니오 | 약하게 예 | additive | 단독 승격 금지 |
| `prefault_cond_ae` | 예 | 아니오 | 아니오 | 아니오 | 약하게 예 | additive | AE 기반 보조 |
| `prefault_cond_dtw` | 예 | 아니오 | 아니오 | 아니오 | 약하게 예 | additive | DTW 기반 보조 |
| `prefault_cond_ews` | 예 | 아니오 | 아니오 | 아니오 | 약하게 예 | additive | EWS 결합형 |
| `prealarm_cond_ae_mid_or_hi` | 예 | 아니오 | 아니오 | 아니오 | 약하게 예 | additive | 전조 강화 보조 |
| `prealarm_cond_dtw_mid_or_hi` | 예 | 아니오 | 아니오 | 아니오 | 약하게 예 | additive | 전조 강화 보조 |
| `prealarm_cond_hs_mid_or_hi` | 예 | 아니오 | 아니오 | 아니오 | 약하게 예 | additive | 전조 강화 보조 |
| `fault_like_day` | 경계적으로 예 | 경계적으로 예 | 아니오 | 아니오 | 아니오 | reroute | 단독 승격 금지, event trigger 보조 |
| `critical_fault` | 아니오 | 예 | 아니오 | 약하게 예 | 예 | additive | sustained critical path |
| `critical_confirmed` | 아니오 | 강하게 예 | 아니오 | 약하게 예 | 예 | gating | confirm path |
| `final_fault` | 아니오 | 최상위 예 | 아니오 | 아니오 | 예 | gating | 최종 확정 경로 |
| `confirmed_fault` | 아니오 | 강하게 예 | 아니오 | 아니오 | 예 | gating | dead-like confirm path |
| `v_drop` | 약하게 예 | 보조적으로 예 | 아니오 | 약하게 예 | 아니오 | explanation_only | 전압강하 설명 신호 |
| `critical_source` | 아니오 | 아니오 | 아니오 | 약하게 예 | 아니오 | explanation_only | source tag, 상태 아님 |
| `anom_subtype:degradation` | 약하게 예 | 아니오 | 아니오 | 아니오 | 약하게 예 | explanation_only | primary promotion path 금지 |
| `anom_subtype:shadow` | 아니오 | 아니오 | 약하게 예 | 아니오 | 약하게 예 | explanation_only | common-cause / 환경 영향 보조 |
| `mid_ratio` | 아니오 | 약하게 예 | 아니오 | 아니오 | 아니오 | explanation_only | 단독 라벨 금지 |
| `mid_v_ratio` | 아니오 | 약하게 예 | 아니오 | 예 | 아니오 | explanation_only | MLPE 해석 핵심 |
| `mid_i_ratio` | 아니오 | 약하게 예 | 아니오 | 예 | 아니오 | explanation_only | 전류 단절/장치 개입 보조 |
| `event_A` | 아니오 | 아니오 | 아니오 | 아니오 | 아니오 | explanation_only | lineage 전용, direct exposure 금지 |
| `group_off_like` | 아니오 | 아니오 | 예 | 아니오 | 예 | suppressor | panel-local 승격 억제 |
| `data_bad` | 아니오 | 아니오 | 예 | 아니오 | 아니오 | suppressor | score 가산보다 억제 |
| `mid_peer 부족` | 아니오 | 아니오 | 예 | 아니오 | 아니오 | suppressor | peer-relative 해석 신뢰도 저하 |
| `work/event calendar hit` | 아니오 | 아니오 | 예 | 아니오 | 예 | suppressor | 운영 이벤트와 겹치면 보류 우선 |

## 9. 축별 읽기 규칙

### 9.1 `precursor_score` 읽기 규칙
- `secondary one-shot`만 있으면 `전조 흔적`에서 멈춘다.
- `primary warning + prefault 계열` 또는 `다른 secondary family 복수`일 때 `precursor candidate` 후보가 된다.
- `prefault_B_effective`는 `precursor_score`의 additive helper로는 사용하지만, 현 단계에서는 이것만으로 `고위험 관찰` direct threshold를 만들지 않는다.
- `common_cause_risk_score`가 높으면 panel-local precursor 승격을 억제한다.
- `hard_evidence_score`가 이미 높으면 precursor 대신 fault signal lane으로 reroute한다.

### 9.2 `hard_evidence_score` 읽기 규칙
- `final_fault`가 있으면 최상위로 닫는다.
- `critical_confirmed`는 confirm된 hard evidence지만 `final_fault`와 이중 카운트하지 않는다.
- `critical_fault`는 analyst-facing 강 신호다.
- `fault_like_day`는 단독 hard evidence가 아니다.

### 9.3 `common_cause_risk_score` 읽기 규칙
- `group_off_like`, `data_bad`, peer coverage 부족, 운영 이벤트 hit는 panel-local 해석을 누른다.
- `prefault_B_common_cause_overlap`는 raw helper를 지우기 위한 신호가 아니라, `prefault_B_effective`와 분리해서 panel-local precursor 승격을 보수화하는 suppressor로 읽는다.
- 이 score가 높으면 `precursor_score`와 `hard_evidence_score`를 직접 0으로 만들기보다
  - `보류`
  - `공통원인 검토 필요`
  - `singleton_review 금지`
  쪽으로 projection한다.

### 9.4 `mlpe_ambiguity_score` 읽기 규칙
- `mid_v_ratio 유지 + mid_i_ratio 급락 + output 붕괴` 조합은 ambiguity를 올린다.
- `critical_source`, `장치 측정 이상형`, `장치 응답 이상형`이 경합할수록 ambiguity를 올린다.
- ambiguity가 높으면 cause top1을 억지 확정하지 않고 `원인 미확정` 또는 `장치/제어 개입 가능성`으로 둔다.

### 9.5 `actionability_score` 읽기 규칙
- precursor만 높고 공통원인 위험이 낮으면 `monitor_only` 또는 `singleton_review`
- hard evidence가 높고 scope가 모듈/장치에 모이면 `maintenance_candidate`
- common-cause 위험이 높으면 `common_cause_review`
- 외부 센서/안전 정보가 없으면 safety/control action은 보수적으로 낮춘다

## 10. 금지 규칙
- `single signal -> final label` 직결 금지
- `v_drop` 단독으로 hard evidence 승격 금지
- `fault_like_day` 단독으로 precursor/hard-evidence 둘 다 자동 승격 금지
- `critical_source`를 상태 등급으로 번역 금지
- `mid_v_ratio`, `mid_i_ratio`, `mid_ratio` 숫자를 단독 cause 확정 근거로 사용 금지
- `common_cause_risk_score`가 높을 때 panel-local cause/action top1을 강행 금지
- `mlpe_ambiguity_score`가 높은데도 `패널 자체 고장`으로 단정 금지

## 11. projection 예시

### 11.1 precursor candidate 예시
- 입력:
  - `pre_ews=1`, `ews_warning=1`, `prefault_cond_dtw=1`
  - `critical_fault=0`, `final_fault=0`
  - `group_off_like=0`
- 읽기:
  - `precursor_score`: 높음
  - `hard_evidence_score`: 낮음
  - `common_cause_risk_score`: 낮음
  - `actionability_score`: 중간
- projection:
  - `operational_state = precursor candidate`
  - `maintenance_lane = monitor_only`

### 11.2 raw-only hard evidence 예시
- 입력:
  - `critical_fault=1`, `critical_confirmed=1`, `final_fault=1`
  - `v_drop` 동반
  - official current 미포함
- 읽기:
  - `hard_evidence_score`: 매우 높음
  - `precursor_score`: 사용 안 함
  - `actionability_score`: 높음
- projection:
  - `analyst/support 고장 신호`
  - `master report에서는 direct primary reading order 제외`

### 11.3 common-cause 보류 예시
- 입력:
  - `pre_ews=1`, `prefault_cond_mid=1`
  - `group_off_like=1`
  - `work/event calendar hit=1`
- 읽기:
  - `precursor_score`: 중간
  - `common_cause_risk_score`: 높음
- projection:
  - `operational_state = 보류`
  - `maintenance_lane = common_cause_review`

## 12. 반례 세트와의 연결
- `official_only`
  - score map이 official current를 analyst artifact로 낮추지 않는지 확인
- `precursor_only`
  - precursor_score가 과도하게 hard_evidence_score로 새지 않는지 확인
- `raw_only_only`
  - hard_evidence_score가 높아도 official current와 공식성을 혼동하지 않는지 확인
- `mlpe_ambiguous`
  - mlpe_ambiguity_score가 cause 과확정을 막는지 확인
- `common_cause_risk`
  - common_cause_risk_score가 panel-local 승격을 억제하는지 확인

## 13. projection bundle tightening

### 13.1 목적
- Gate 2C의 목적은 `신호 -> 축`까지만 적는 데서 멈추지 않고, 어떤 축 조합일 때만 projection으로 올라갈 수 있는지 보수적으로 잠그는 것이다.
- 이 절은 numeric threshold를 잠그지 않는다.
- 대신 `어떤 축은 직접 승격 축이 아니고`, `어떤 축 조합일 때만 review/precursor/hard-evidence/action lane으로 갈 수 있는지`를 고정한다.

### 13.2 precursor bundle 최소 조건
- 아래 둘 중 하나는 반드시 있어야 한다.
  - `pre_ews`, `ews_warning`, `pre_alarm` 중 하나 이상의 primary warning family
  - 또는 동일 precursor family의 반복/누적 흔적
- 그리고 아래 중 하나 이상의 corroboration이 따라야 한다.
  - `prefault_cond_mid`
  - `prefault_cond_ae`
  - `prefault_cond_dtw`
  - `prefault_cond_ews`
  - `prealarm_cond_*_mid_or_hi`
- 즉 `single secondary one-shot`은 `전조 흔적`에서 멈추고, direct `precursor candidate`로 승격하지 않는다.
- `prefault_B_effective`는 precursor bundle의 additive helper이지만, 이것만으로 `고위험 관찰`이나 direct headline 승격을 만들지 않는다.

### 13.3 hard evidence bundle 최소 조건
- 아래 gating family 중 하나는 반드시 있어야 한다.
  - `confirmed_fault`
  - `critical_confirmed`
  - `final_fault`
- `critical_fault` 단독은 analyst/support 강신호로는 읽을 수 있지만, confirm path를 대체하지 않는다.
- `fault_like_day`와 `v_drop`는 hard evidence bundle을 보조할 수는 있어도 단독 bundle 시작점이 아니다.
- hard evidence bundle이 성립하면 row는 `fault signal lane`으로 reroute하고, precursor report headline과 혼합하지 않는다.

### 13.4 common-cause hold bundle
- 아래 중 하나라도 강하게 겹치면 panel-local promotion보다 hold/review가 우선이다.
  - `group_off_like`
  - `data_bad`
  - `mid_peer 부족`
  - `work/event calendar hit`
  - `prefault_B_common_cause_overlap`
- common-cause hold bundle은 `precursor_score`나 `hard_evidence_score`를 삭제하는 축이 아니라,
  - `singleton_review 금지`
  - `common_cause_review 우선`
  - `panel-local cause/action top1 보류`
  를 강제하는 suppressor bundle로 읽는다.

### 13.5 MLPE ambiguity hold bundle
- 아래 조합은 `mlpe_ambiguity_score`를 높이고, cause 확정 강도를 낮춘다.
  - `mid_v_ratio 유지 + mid_i_ratio 급락`
  - `critical_source`가 장치/제어 해석과 경합
  - `장치 측정 이상형`, `제어 응답 이상형`, panel-local fault 후보가 동시에 경합
- ambiguity hold bundle이 높을 때는 아래를 금지한다.
  - panel hardware top1 단정
  - maintenance lane direct escalation
  - explanation-only signal을 cause rank certainty로 번역
- 허용되는 projection은 아래 수준까지다.
  - `원인 미확정`
  - `장치/제어 개입 가능성`
  - `추가 확인 필요`

### 13.6 actionability ceiling
- `actionability_score`는 독립 승격 축이 아니다.
- actionability는 아래 ceiling을 넘지 못한다.
  - precursor bundle만 있으면 `monitor_only` 또는 `singleton_review`
  - hard evidence bundle이 있어도 common-cause hold bundle이 높으면 `common_cause_review`
  - ambiguity hold bundle이 높으면 `maintenance_candidate`를 보수적으로 낮춤
- 즉 actionability는 `가장 강한 eligible evidence lane`을 넘어서 직접 top-level 상태를 만들 수 없다.

### 13.7 explanation-only 신호 사용 제한
- 아래 신호는 phenotype 설명과 패턴 요약에는 쓰되, direct projection trigger로 쓰지 않는다.
  - `critical_source`
  - `v_drop`
  - `mid_ratio`
  - `mid_v_ratio`
  - `mid_i_ratio`
  - `anom_subtype:*`
- explanation-only 신호는 아래 항목을 단독으로 만들 수 없다.
  - `operational_state`
  - `cause top1`
  - `maintenance lane`
  - `official current headline`

### 13.8 Gate 5 / Gate 6와의 연결
- Gate 5에서는 위 bundle 규칙을 깨지 않는 범위에서만 artifact wording을 조정한다.
- Gate 6에서는 위 bundle 규칙을 넘어서 `single signal -> taxonomy/action`으로 바로 번역하지 않는다.
- 이후 algorithm gating patch가 오더라도, 이 bundle 규칙보다 먼저 `single helper`를 top-level 승격시키는 패치는 금지한다.

## 14. 다음 단계
- `DL-20260424-014` 기준으로 projection은 `eligible evidence lane -> hold/reroute cap -> actionability ceiling` 순서로만 읽는다.
- `DL-008`에서 operator-facing artifact에 `event_type/terminal_pattern`을 어디까지 허용할지 잠글 때, 이 score map을 함께 본다.
- `MLPE ambiguous`와 `common_cause_risk` 반례 seed를 더 보강해, 위 projection bundle이 실제 tri-site 사례와 충돌하지 않는지 먼저 확인한다.
- algorithm gating patch 전에는
  - counterexample set
  - counterexample regression checklist
  - Gate 3
  - Gate 4
  - 본 문서
  - `DL-20260424-014`
  를 함께 확인한다.
- 이후 필요 시 아래로 확장한다.
  - numeric weighting table
  - score calibration note

## 14. 관련 문서
- [OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md)
- [OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md)
- [OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md)
- [OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md)
- [OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md)
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
