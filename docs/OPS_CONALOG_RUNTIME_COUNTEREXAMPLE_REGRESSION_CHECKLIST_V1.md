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

## Judgment Role Precheck
- 새 evidence를 제시할 때는 bucket에 넣기 전에 먼저 아래 role 중 하나로 분류한다.
  - `exact_family_closure`
  - `supportive_hint`
  - `candidate_reservoir`
  - `non_closing_backlog`
  - `structural_blocker`
- [ ] 새 evidence의 `judgment role`을 먼저 적었는가
- [ ] `curated pressure-test seed`를 role처럼 쓰지 않고 usage tag로만 적었는가
- [ ] `supportive_hint`, `candidate_reservoir`, `non_closing_backlog`를 `exact_family_closure`처럼 읽지 않았는가
- [ ] `structural_blocker`를 `signal absence`로 오독하지 않았는가

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
- [ ] `control_score > 0` 또는 GPVS/usage 보조 가산만으로 `제어응답형 top1 family`를 확보한 것처럼 읽지 않았는가

### 5. `common_cause_risk`
- [ ] `group_off_like`, `work/event calendar hit`, `prefault_B_common_cause_overlap`가 suppressor로 유지되는가
- [ ] 다수 cluster 흔들림을 singleton precursor나 panel-local hard-evidence 강화 근거로 쓰지 않았는가
- [ ] official current direct overlap 부재를 무시하고 common-cause rule을 확대하지 않았는가
- [ ] `±7일 near-window overlap backlog`를 `same-day exact family closure`처럼 읽지 않았는가
- [ ] raw-daily same-day direct row 존재만으로 `report-layer exact family`가 닫힌 것처럼 읽지 않았는가
- [ ] `group_off_date` exact row는 `no_report_lane_entry / precursor_carryover / rawonly_date_displaced / rawonly_near_signal_anchor` subtype으로 먼저 분리했는가

## Current Collection Priority
### Priority A
- `MLPE ambiguous`에서 `장치 응답 이상형`이 실제 top1으로 뜨는 사례
- 회복/재발이 함께 기록된 MLPE ambiguous 사례

### Priority B
- `common_cause_risk`에서 `work/event calendar hit` 또는 통신 흔들림과 직접 겹치는 사례
- precursor/current row와 `group_off_event`가 직접 겹치는 `same-day exact` 사례

### Priority C
- official current와 동시에 엮이는 common-cause `same-day exact` direct overlap 사례
- `±7일 near-window overlap backlog` 대표 사례
- `vdrop` 또는 `fault_like_day` 반복이 있지만 common-cause hold가 우선이어야 하는 사례

## BR-029 / BR-031 / BR-033 / BR-034 / BR-035 / BR-036 / BR-037 interpretation lock
- BR-028 provisional shortlist는 BR-029 기준을 만족하면 curated counterexample seed로 승격될 수 있다.
- 단, 그 승격은 `hold/reroute pressure-test seed` 의미만 가진다.
- 따라서 아래는 계속 `missing family`로 별도 추적한다.
  - `제어응답형 top1`
  - official/current row date direct overlap with common-cause
- BR-031 기준 widened `±7일 near-window overlap backlog`는 별도 추적 backlog 이다.
- 따라서 near-window backlog는 pressure-test에는 쓸 수 있지만 `same-day exact family closure` 대체물로 쓰면 안 된다.
- BR-033 기준 current backlog는 아직 `separate provisional family`가 아니다.
- future promotion은 아래를 동시에 만족할 때만 다시 검토한다.
  - one direct flag family
  - one slice type
  - report row `3+` and root `3+`
  - gap sign mostly aligned
- BR-034 기준 `제어응답형 raw_score > 0`는 supportive hint 이지 `top1 family closure`가 아니다.
- BR-034 기준 raw-only artifact date expanded scan도 `same-day direct overlap family closure`를 만들지 못했다.
- BR-035 기준 raw-daily same-day direct row reservoir는 존재하지만, report-layer exact family는 계속 비어 있다.
- 따라서 same-day exact family search는 `row existence`보다 `report-lane entry + artifact-date coincidence`를 함께 본다.
- BR-036 기준 judgment role을 먼저 잠근다.
  - `supportive_hint` -> ranking/explanation/support only
  - `candidate_reservoir` -> blocker search input only
  - `non_closing_backlog` -> backlog tracking only
  - `structural_blocker` -> patch target selection only
  - `exact_family_closure`만 missing family closure 주장 가능
- BR-037 기준 `group_off_date` exact row는 blocker subtype을 먼저 가른다.
  - `rawonly_near_signal_anchor`만 next inspect 우선순위가 높다.
  - 나머지 subtype은 immediate exact-family closure 근거가 아니다.

## BR-058 / BR-059 fault-family regression pressure lock
- BR-058 packet rows are regression/counterexample pressure only.
- BR-059 makes this packet executable as a prepatch gate:
  - script: `research/prognostics/check_panel_day_engine_fault_family_regression_prepatch_gate_v1.py`
  - required gates: `12`
  - real packet status: `pass`
- Before any future panel-engine algorithm patch, the gate must verify:
  - `non_target_hard_same_day_fault_family_seed >= 5`
  - `sensor_feedback_hard_same_day_ambiguity_pressure >= 6`
  - `target_exact_closure_candidate_sum = 0`
  - `operator_promotion_allowed_sum = 0`
  - `engine_patch_candidate_sum = 0`
- A passing BR-059 gate preserves packet integrity only.
- It does not approve threshold changes or target exact-family closure.

## Minimum Pass Rule Before Algorithm Patch
- `official_only`, `precursor_only`, `raw_only_only` 각 bucket 대표 사례 3개 이상
- `mlpe_ambiguous`, `common_cause_risk`는 대표 사례 3개 이상 + Priority A/B seed가 최소 1개 이상 보강
- `near-window overlap backlog`를 separate provisional family로 쓰려면 representative seed 1개 이상 + `same-day exact 아님` 금지 문구 1개 이상을 같이 유지
- BR-033 future promotion criteria를 만족하지 못하면 near-window backlog는 계속 non-closing backlog로 둔다
- BR-059 fault-family regression prepatch gate가 실패하면 algorithm gating patch는 `보류`로 둔다.
- 위 조건을 만족하지 못하면 algorithm gating patch는 `보류`로 둔다.

## Decision
- 본 체크리스트는 algorithm patch 허가 문서가 아니다.
- 목적은 `무엇이 아직 불충분한지`를 명확히 해, 다음 코드 패치가 반례 부재 상태에서 성급히 들어가지 않게 만드는 것이다.
