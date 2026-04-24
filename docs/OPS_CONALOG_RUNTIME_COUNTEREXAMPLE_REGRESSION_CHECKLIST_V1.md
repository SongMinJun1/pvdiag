<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1

## Purpose
- 본 문서는 `counterexample set`를 실제 patch gate로 쓰기 위한 최소 regression checklist 다.
- 목적은 아래 네 가지다.
  - Gate 2C projection bundle tightening 이후, 각 bucket이 어떤 hold/bundle을 압박하는지 고정한다.
  - algorithm gating patch 전에 어떤 버킷을 반드시 다시 확인해야 하는지 명시한다.
  - docs-only 변경과 code/rule 변경의 검증 강도를 구분한다.
  - `single helper`, `explanation-only`, `common-cause hold`, `MLPE ambiguity hold` 오독을 막는다.

## Scope
- 대상 버킷:
  - `official_only`
  - `precursor_only`
  - `raw_only_only`
  - `mlpe_ambiguous`
  - `common_cause_risk`
- 대상 문서:
  - [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md)

## When To Use
### docs-only patch
- wording / docs sync / checklist 보강만 하는 턴이면 아래 둘만 확인한다.
  - bucket coverage가 줄지 않았는가
  - 기존 금지 일반화 문구가 약해지지 않았는가

### code or rule patch
- 아래를 모두 확인한다.
  - bucket별 대표 사례 3개 이상 유지
  - Gate 2C bundle 규칙 위반 여부
  - artifact lane drift 여부
  - operator-facing over-promotion 여부

## Bucket Pressure-Test Matrix
| bucket | primary bundle under test | must stay true | must stay false | if broken |
|---|---|---|---|---|
| `official_only` | artifact-lane separation | official current가 primary lane으로 유지 | precursor/raw-only support artifact를 official current 근거로 재번역 | Gate 5 / DL-001 / DL-002 재검토 |
| `precursor_only` | precursor bundle | primary warning + corroboration 없이 direct 승격 금지 | `single secondary` 또는 helper 단독 hard-evidence/current 승격 | Gate 2C / Gate 3 재검토 |
| `raw_only_only` | hard evidence bundle + lane split | hard evidence는 support lane에서 유지 | raw-only row를 official current나 stable headline으로 승격 | Gate 4A / Gate 5 재검토 |
| `mlpe_ambiguous` | ambiguity hold bundle | 장치/제어/패널 경합이 `needs-more-evidence`를 허용 | top1 cause 또는 maintenance lane을 억지 확정 | Gate 2C / Gate 6B 재검토 |
| `common_cause_risk` | common-cause hold bundle | group/base/event overlap이 panel-local 승격을 억제 | cluster 흔들림을 singleton precursor/hard-evidence로 과대 승격 | Gate 2A / Gate 2C / Gate 6A 재검토 |

## Per-Bucket Checklist
### 1. `official_only`
- [ ] official current 사례를 precursor recall 실패나 raw-only exposure 확대 근거로 쓰지 않았는가
- [ ] stable/runtime contract boundary를 흐리지 않았는가
- [ ] official current headline에 analyst/support wording이 새지 않았는가

### 2. `precursor_only`
- [ ] primary warning family 없이 direct precursor candidate로 올린 row가 없는가
- [ ] `prefault_B_effective` 단독 승격을 허용하지 않았는가
- [ ] `fault_like_day`, `v_drop`, explanation-only 신호를 precursor headline trigger로 쓰지 않았는가

### 3. `raw_only_only`
- [ ] confirm path 없이 hard evidence bundle을 과장하지 않았는가
- [ ] raw-only row를 official current와 같은 공식성으로 설명하지 않았는가
- [ ] event semantics를 operator headline으로 직접 복제하지 않았는가

### 4. `mlpe_ambiguous`
- [ ] `장치 측정 이상형`, `제어 응답 이상형`, panel-local 후보 경합 시 hold/review가 유지되는가
- [ ] `critical_source`, `mid_v_ratio`, `mid_i_ratio`를 direct cause certainty로 쓰지 않았는가
- [ ] ambiguity가 높은데 maintenance/action top1을 강행하지 않았는가

### 5. `common_cause_risk`
- [ ] `group_off_like`, `work/event calendar hit`, `prefault_B_common_cause_overlap`가 suppressor로 유지되는가
- [ ] 다수 cluster 흔들림을 singleton precursor나 panel-local hard-evidence 강화 근거로 쓰지 않았는가
- [ ] official current direct overlap 부재를 무시하고 common-cause rule을 확대하지 않았는가

## Current Collection Priority
### Priority A
- `MLPE ambiguous`에서 `장치 응답 이상형`이 실제 top1으로 뜨는 사례
- 회복/재발이 함께 기록된 MLPE ambiguous 사례

### Priority B
- `common_cause_risk`에서 `work/event calendar hit` 또는 통신 흔들림과 직접 겹치는 사례
- precursor/current row와 `group_off_event`가 직접 겹치는 사례

### Priority C
- official current와 동시에 엮이는 common-cause direct overlap 사례
- `vdrop` 또는 `fault_like_day` 반복이 있지만 common-cause hold가 우선이어야 하는 사례

## BR-029 interpretation lock
- BR-028 provisional shortlist는 BR-029 기준을 만족하면 curated counterexample seed로 승격될 수 있다.
- 단, 그 승격은 `hold/reroute pressure-test seed` 의미만 가진다.
- 따라서 아래는 계속 `missing family`로 별도 추적한다.
  - `제어응답형 top1`
  - official/current row date direct overlap with common-cause

## Minimum Pass Rule Before Algorithm Patch
- `official_only`, `precursor_only`, `raw_only_only` 각 bucket 대표 사례 3개 이상
- `mlpe_ambiguous`, `common_cause_risk`는 대표 사례 3개 이상 + Priority A/B seed가 최소 1개 이상 보강
- 위 조건을 만족하지 못하면 algorithm gating patch는 `보류`로 둔다.

## Decision
- 본 체크리스트는 algorithm patch 허가 문서가 아니다.
- 목적은 `무엇이 아직 불충분한지`를 명확히 해, 다음 코드 패치가 반례 부재 상태에서 성급히 들어가지 않게 만드는 것이다.
