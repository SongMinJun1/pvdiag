<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_029_PROVISIONAL_SEED_PROMOTION_CRITERIA_V1

## Purpose
- Lock the rule for promoting BR-028 provisional shortlist rows into the curated counterexample set.
- Keep this branch docs-only.
- Prevent two different meanings from being mixed:
  - `counterexample seed로는 충분함`
  - `원래 찾던 exact missing family를 찾았음`

## Scope
- upstream findings:
  - [OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_028_MISSING_SEED_SCAN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_028_MISSING_SEED_SCAN_V1.md)
- affected docs:
  - [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
  - [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- related decision:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_013_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_013_V1.md)

## Review Result
### 1. BR-028 provisional shortlist는 `빈 버킷 메우기` 용도로는 유효하다
- `MLPE ambiguous`:
  - `장치 응답 이상형` 관련 live-chain shortlist 4건이 존재한다.
  - exact `제어응답형 top1`은 아직 0건이지만, ambiguity hold bundle을 압박하는 seed source로는 쓸 수 있다.
- `common_cause_risk`:
  - `gangui group_off` precursor overlap cluster
  - `ktc_ess 2025-10-26 co_drop_surge` hard-like overlap cluster
  - 두 source 모두 panel-local로 오독될 수 있는 긴장을 실제로 보여준다.

### 2. 하지만 `발견 완료`로 읽으면 안 된다
- 아래는 계속 missing 상태다.
  - `제어응답형 top1`
  - report-row 날짜 기준 `official/current direct overlap`
- 따라서 BR-028 shortlist는 `좋은 근사 seed`이지, `원래 찾던 exact family의 closure`는 아니다.

## Promotion Criteria
### curated counterexample seed로 올릴 수 있는 경우
- 아래 네 조건을 모두 만족할 때만 승격한다.
  1. `reproducible identity`
     - site / panel_id / date 또는 equivalent report-row key가 고정돼 있다.
  2. `bundle pressure`
     - BR-026에서 잠근 hold/reroute bundle을 직접 압박한다.
  3. `two-cue evidence`
     - 같은 사례 안에 독립적 cue가 최소 2개 있다.
  4. `prohibited overgeneralization`
     - 이 사례로부터 무엇을 일반화하면 안 되는지 함께 적는다.

### 계속 provisional로 남겨야 하는 경우
- 아래 중 하나라도 해당하면 승격하지 않는다.
  - external label만 있고 실제 candidate tension이 없다
  - helper 1개만 있다
  - group/event/date context가 없다
  - `missing` 사실만 있고, hold/reroute tension 자체는 없다

## Bucket-Specific Reading
### `mlpe_ambiguous`
- 승격 허용:
  - external/device-oriented hint + competing panel-local candidates
  - hold reading이 natural
- 승격 금지:
  - `제어응답형 top1`이 아직 없는데도 exact family가 채워진 것처럼 쓰는 경우

### `common_cause_risk`
- 승격 허용:
  - same-day `group_off` 또는 `site_event` 계열 직접 중첩
  - panel-local helper/hard-like trace 동시 존재
  - cluster/base/group context 기록
- 승격 금지:
  - `official/current direct overlap`이 없는데도 direct-overlap family closure처럼 쓰는 경우

## Decision
- BR-029는 아래를 잠근다.
  - BR-028 provisional shortlist는 curated counterexample seed로 승격될 수 있다.
  - 단, 그 승격은 `hold/reroute counterexample seed` 의미만 가진다.
  - exact missing family closure는 별도로 계속 추적한다.

## Next Safe Step
- next safe lane은 algorithm patch가 아니라 `score-to-projection decision log`다.
- 이유:
  - 이제 `무엇을 curated seed로 쓸 수 있는지`는 잠겼다.
  - 다음에는 그 seed가 실제로 `score axis -> projection` 판단에서 어떤 hold/reroute를 강제하는지 잠그면 된다.
