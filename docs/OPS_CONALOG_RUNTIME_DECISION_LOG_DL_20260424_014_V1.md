<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_014_V1

## 빠른 요약
| decision_id | status | related_gate | topic | decision | owner | date_decided |
| --- | --- | --- | --- | --- | --- | --- |
| DL-20260424-014 | accepted | Gate 2C / Gate 5 / Gate 7 | score-to-projection precedence lock | projection은 `가장 큰 점수`가 아니라 `가장 강한 eligible evidence lane`을 먼저 고르고, 그 뒤 common-cause / ambiguity hold와 actionability ceiling을 적용하는 방식으로만 허용한다 | Codex + 사용자 합의 | 2026-04-24 |

## [DL-20260424-014] score-to-projection precedence lock
- `status`: accepted
- `date_first_raised`: 2026-04-24
- `date_decided`: 2026-04-24
- `related_gate`: Gate 2C / Gate 5 / Gate 7
- `owner`: Codex + 사용자 합의
- `related_branch_ids`: [BR-20260424-026, BR-20260424-027, BR-20260424-028, BR-20260424-029, BR-20260424-030]
- `related_parking_ids`: []

### 질문
- 이미 잠긴 score axis와 bundle rule을 실제 projection으로 내릴 때, 무엇이 우선순위를 가져야 하는가.
- 특히 `precursor_score`, `hard_evidence_score`, `common_cause_risk_score`, `mlpe_ambiguity_score`, `actionability_score`가 동시에 존재할 때 `가장 높은 점수 wins`로 읽을 수 있는가.

### 배경
- [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md) 는 이미 signal -> axis mapping 과 projection bundle tightening을 잠갔다.
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md) 는 `mlpe_ambiguous`, `common_cause_risk` 버킷이 hold/reroute bundle을 실제로 압박해야 한다고 잠갔다.
- [OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_028_MISSING_SEED_SCAN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_028_MISSING_SEED_SCAN_V1.md) 와 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_013_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_013_V1.md) 는 provisional shortlist를 curated seed로 쓸 수는 있지만, exact family closure와는 분리해야 한다고 잠갔다.
- 따라서 다음 algorithm patch 전에 `score -> projection` 순서를 한 번 더 고정하지 않으면, 아래 위험이 남는다.
  - 높은 `actionability_score`가 evidence lane을 앞질러 operator-facing promotion처럼 읽히는 위험
  - `common_cause_risk_score`와 `mlpe_ambiguity_score`가 hold 축이 아니라 direct competing top1처럼 읽히는 위험
  - explanation-only cue가 projection trigger로 잘못 재사용되는 위험

### 선택지
1. 선택지 A. axis score를 숫자적으로 비교해 가장 큰 score가 projection을 결정하게 둔다
   - 장점:
     - 구현은 단순하다.
     - scorecard/weighted model로 가기 쉬워 보인다.
   - 단점:
     - hold/reroute 축이 promotion 축과 동급이 된다.
     - common-cause와 ambiguity가 `승격 축`처럼 오독될 수 있다.
     - 현재 Gate 2C/BR-026 bundle 잠금과 충돌한다.
2. 선택지 B. 먼저 `eligible evidence lane`을 고르고, 그 뒤 hold/reroute 축과 actionability ceiling을 적용한다
   - 장점:
     - current docs 체인과 가장 정합적이다.
     - promotion lane과 hold lane의 역할이 섞이지 않는다.
     - operator-facing projection을 보수적으로 유지할 수 있다.
   - 단점:
     - numeric scorecard만 생각하면 덜 직관적으로 보일 수 있다.
3. 선택지 C. actionability를 최우선으로 두고, evidence lane은 설명 보조로만 둔다
   - 장점:
     - 운영 행동 추천 중심으로 빠르게 해석된다.
   - 단점:
     - 근거보다 행동이 앞서는 구조가 된다.
     - `maintenance_candidate` 과잉 승격 위험이 가장 크다.

### 최종 결정
- 선택지 B를 채택한다.
- projection 순서는 아래와 같이 고정한다.
  1. `eligible evidence lane`을 먼저 고른다.
     - precursor bundle이 최소 조건을 만족하면 `precursor lane`
     - hard evidence bundle이 최소 조건을 만족하면 `fault signal lane`
     - 둘 다 아니면 top-level promotion lane 없음
  2. `common_cause hold bundle`과 `mlpe ambiguity hold bundle`을 적용한다.
     - 이 둘은 promotion lane이 아니다.
     - promotion을 보류/하향/재분류하는 cap 또는 reroute 축이다.
  3. `actionability_score`는 마지막에 적용한다.
     - actionability는 이미 선택된 eligible evidence lane을 넘어서 직접 top-level 상태를 만들 수 없다.
  4. explanation-only 신호는 어떤 단계에서도 단독 projection trigger가 될 수 없다.

### projection precedence 규칙
#### 1. precursor lane precedence
- precursor bundle 최소 조건이 충족돼도 아래가 높으면 direct 승격하지 않는다.
  - common-cause hold bundle
  - mlpe ambiguity hold bundle
- 즉 precursor lane의 기본 projection은 아래 중 하나여야 한다.
  - `전조 흔적`
  - `precursor candidate`
  - `고위험 관찰`
  - 또는 hold/reroute 결과인 `보류`, `추가 확인 필요`

#### 2. fault signal lane precedence
- hard evidence bundle이 충족되면 row는 `fault signal lane`으로 들어갈 수 있다.
- 하지만 아래는 그대로 유지한다.
  - common-cause hold bundle이 높으면 `common_cause_review` cap 가능
  - ambiguity hold bundle이 높으면 cause certainty와 actionability를 낮출 수 있음
- 즉 fault signal lane은 confirm path precedence를 가지지만, cause/action direct certainty까지 자동 보장하지 않는다.

#### 3. hold/reroute axis는 승격 축이 아니다
- `common_cause_risk_score`
- `mlpe_ambiguity_score`
- 위 둘은 아래 역할만 가진다.
  - promotion 억제
  - review lane reroute
  - cause/action certainty cap
- 위 둘이 높다고 해서 직접 top-level headline이나 cause top1이 생성되지는 않는다.

#### 4. actionability ceiling
- `actionability_score`는 아래 ceiling을 넘지 못한다.
  - eligible evidence lane 없음 -> top-level action promotion 금지
  - precursor lane only -> `monitor_only` 또는 `singleton_review` 범위
  - hard evidence lane + hold 높음 -> `common_cause_review` 또는 conservative maintenance
  - ambiguity hold 높음 -> direct maintenance escalation 금지

#### 5. explanation-only prohibition
- 아래는 projection trigger 금지 상태를 유지한다.
  - `critical_source`
  - `v_drop`
  - `mid_ratio`
  - `mid_v_ratio`
  - `mid_i_ratio`
  - `anom_subtype:*`
- explanation-only cue는 pattern summary, cause note, analyst support explanation까지만 허용한다.

### 이유
- gate consistency:
  - BR-026은 이미 bundle tightening을 잠갔고, DL-014는 그걸 projection 순서로 번역한 것이다.
- hold axis safety:
  - common-cause / ambiguity는 승격보다 `멈춤` 쪽의 역할이 더 중요하다.
- operator protection:
  - actionability가 증거 레인을 앞지르면 operator-facing 과대 권고가 발생하기 쉽다.
- implementation safety:
  - 이후 numeric scorecard나 hybrid model로 가더라도 precedence lock이 먼저 있어야 drift를 막을 수 있다.

### 허용 패치
- Gate 5 artifact wording/definitions/master report가 위 precedence를 반영하도록 정리하는 docs/surface patch
- curated counterexample seed가 어떤 hold/reroute precedence를 압박하는지 명시하는 docs patch
- 이후 algorithm patch에서 `eligible lane -> hold/reroute cap -> actionability ceiling` 순서를 코드로 shadow-apply 하는 패치

### 금지 패치
- `가장 큰 score`를 이유로 direct projection top1을 정하는 패치
- `common_cause_risk_score` 또는 `mlpe_ambiguity_score`를 promotion lane처럼 취급하는 패치
- actionability만 높다는 이유로 `maintenance_candidate`를 direct top-level projection으로 만드는 패치
- explanation-only cue를 direct projection trigger로 다시 쓰는 패치

### 필요한 문서 업데이트
- [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md)

### 필요한 코드 업데이트
- 없음
- 이 결정은 projection precedence lock이며, runtime code patch는 아직 열지 않는다.

### 검증 계획
- 문서 검증:
  - Gate 2C, counterexample checklist, Gate 7이 동일한 precedence를 참조하는지 확인
- 구조 검증:
  - promotion lane, hold lane, explanation lane이 역할상 충돌하지 않는지 확인
- 최소 실행 검증:
  - `git diff --check`

### 롤백 트리거
- curated seed pressure-test에서 hold/reroute precedence가 실제 사례를 반복적으로 오해하는 경우
- 이후 numeric scorecard 설계에서 precedence lock이 오히려 중요한 hold 사례를 숨기는 것으로 드러나는 경우

### 관련 근거
- [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md)
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_013_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_013_V1.md)
