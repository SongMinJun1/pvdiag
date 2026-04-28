<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_013_V1

## 빠른 요약
| decision_id | status | related_gate | topic | decision | owner | date_decided |
| --- | --- | --- | --- | --- | --- | --- |
| DL-20260424-013 | accepted | Gate 2C / Gate 7 | provisional seed promotion criteria lock | BR-028에서 찾은 provisional shortlist는 `hold/reroute counterexample seed` 기준을 만족할 때만 curated counterexample set에 승격할 수 있고, 이 승격은 원래 찾고 있던 exact missing family의 `발견 완료`를 뜻하지 않는다 | Codex + 사용자 합의 | 2026-04-24 |

## [DL-20260424-013] provisional seed promotion criteria lock
- `status`: accepted
- `date_first_raised`: 2026-04-24
- `date_decided`: 2026-04-24
- `related_gate`: Gate 2C / Gate 7
- `owner`: Codex + 사용자 합의
- `related_branch_ids`: [BR-20260424-028, BR-20260424-029]
- `related_parking_ids`: []

### 질문
- BR-028에서 찾은 `live-chain / raw-daily provisional shortlist`를 언제 curated `counterexample seed`로 승격할 수 있는가.
- 특히 `제어응답형 top1`이나 `official/current direct overlap` 같은 exact missing family가 아직 없을 때도 seed 승격이 가능한가.

### 배경
- [OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_028_MISSING_SEED_SCAN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_028_MISSING_SEED_SCAN_V1.md) 기준으로 아래 두 사실이 동시에 확인됐다.
  - exact missing family는 여전히 비어 있다.
    - `제어응답형 top1 = 0`
    - report-row 날짜 기준 `site_event/group_off` direct overlap = `0`
  - 반면 next patch를 압박할 수 있는 provisional shortlist는 확보됐다.
    - `MLPE ambiguous` live-chain shortlist 4건
    - `gangui group_off` precursor overlap cluster
    - `ktc_ess 2025-10-26 co_drop_surge` hard-like overlap cluster
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md) 와 [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md) 의 역할상, seed set은 비어 있으면 안 되지만 근거가 약한 row를 무분별하게 curated seed로 올려도 안 된다.
- 따라서 `무엇이 curated seed로 충분한가`와 `무엇이 아직 missing family closure가 아닌가`를 분리해 잠글 필요가 있다.

### 선택지
1. 선택지 A. exact missing family가 직접 관측될 때까지 provisional shortlist는 모두 승격 금지
   - 장점:
     - 가장 보수적이다.
     - `찾고 싶던 이상적인 사례`와 `현재 있는 근사 사례`가 섞이지 않는다.
   - 단점:
     - `mlpe_ambiguous`, `common_cause_risk` 버킷의 압박 테스트가 계속 비게 된다.
     - BR-028에서 확보한 실제 사례를 regression gate에 활용하지 못한다.
2. 선택지 B. provisional shortlist는 `hold/reroute bundle`을 실제로 압박하는 representative seed라면 curated counterexample set에 승격할 수 있다. 단, exact missing family closure와는 분리해 기록한다
   - 장점:
     - regression gate를 비우지 않으면서도 과한 일반화를 막을 수 있다.
     - `seed 승격`과 `missing family 발견 완료`를 분리해 쓸 수 있다.
     - BR-026/027/028 findings를 실제 patch gate로 연결하기 쉽다.
   - 단점:
     - 문서에서 `승격됨`과 `발견 완료`를 엄격히 구분하지 않으면 혼선이 생길 수 있다.
3. 선택지 C. provisional shortlist는 모두 curated seed로 승격하고, 부족한 점은 후속 note로만 보완
   - 장점:
     - 빠르다.
     - branch 진행 속도는 가장 좋다.
   - 단점:
     - `single helper`, `explanation-only`, `cluster noise`가 seed로 섞일 위험이 크다.
     - 이후 algorithm patch가 약한 반례 위에서 과하게 움직일 수 있다.

### 최종 결정
- 선택지 B를 채택한다.
- 규칙은 아래와 같다.
  1. provisional shortlist는 `hold/reroute counterexample seed` 조건을 만족할 때만 curated counterexample set에 승격할 수 있다.
  2. 이 승격은 `missing family closure`가 아니다.
  3. 따라서 `제어응답형 top1`이나 `official/current direct overlap`이 여전히 0건이면, 그 사실은 계속 `미관측`으로 남긴다.
  4. curated seed 승격 기준은 아래 네 축을 모두 만족해야 한다.
     - `재현 가능 식별성`: site / panel_id / date 또는 report-row key가 문서에 고정돼 있어야 한다.
     - `bundle 직접성`: BR-026에서 잠근 hold/reroute bundle 하나 이상을 직접 압박해야 한다.
     - `이중 근거성`: 같은 사례 안에 독립적 evidence cue가 두 개 이상 있어야 한다.
     - `금지 일반화 명시`: 이 사례로부터 무엇을 일반화하면 안 되는지 문장으로 고정해야 한다.
  5. 위 네 축 중 하나라도 빠지면 provisional 상태를 유지한다.

### 버킷별 최소 기준
#### `mlpe_ambiguous`
- 아래를 모두 만족해야 curated seed로 승격할 수 있다.
  - external/device-oriented hint와 panel-local 후보 경합이 동시에 명시된다.
  - top1/top2/top3 또는 equivalent candidate ordering이 남아 있다.
  - `needs-more-evidence` 또는 hold reading이 자연스럽고, 단일 top1 강행이 금지돼 있다.
  - `제어응답형 top1`이 없어도 승격은 가능하지만, 그 경우 반드시 `exact target family still missing` note를 함께 남긴다.

#### `common_cause_risk`
- 아래를 모두 만족해야 curated seed로 승격할 수 있다.
  - 같은 날짜에 `group_off`, `site_event`, `work/event calendar hit`, `prefault_B_common_cause_overlap` 중 하나 이상이 직접 관측된다.
  - 같은 사례 안에 panel-local helper 또는 hard-like trace가 함께 있어 `panel-local로 오독될 위험`이 실제로 존재한다.
  - cluster/base/group context가 문서에 남아 있다.
  - `official/current direct overlap`이 없어도 승격은 가능하지만, 그 경우 반드시 `official direct overlap still missing` note를 함께 남긴다.

### 아직 부족한 경우
- 아래는 curated seed 승격에 불충분하다.
  - external label 또는 explanation-only wording만 있는 경우
  - helper 1개만 단독으로 있는 경우
  - site/group context 없이 single row만 있는 경우
  - `top1 absent`, `direct overlap absent` 같은 결손 사실만 있고 실제 hold/reroute tension이 없는 경우

### 이유
- regression gate 현실성:
  - 반례 세트가 비어 있으면 다음 algorithm patch가 실제 사례 압박 없이 진행된다.
- 과잉 일반화 방지:
  - 동시에 `exact missing family`가 채워진 것처럼 읽히면 안 된다.
- 문서/코드 순서:
  - 지금 단계는 docs-only이고, algorithm gating patch 전에는 `어떤 seed가 curated로 충분한가`를 먼저 잠가야 한다.
- operator safety:
  - curated seed 승격은 support/review/regression lane 결정이지, operator-facing verdict 승격 근거가 아니다.

### 허용 패치
- BR-028 shortlist를 `mlpe_ambiguous` 또는 `common_cause_risk` curated seed로 선별 편입하는 docs-only 패치
- seed 항목에 `exact target still missing` note를 함께 붙이는 패치
- 이후 score-to-projection decision log에서 이 curated seed를 regression input으로 참조하는 패치

### 금지 패치
- BR-028 provisional shortlist를 근거로 `제어응답형 top1`이 확보된 것처럼 서술하는 패치
- `official/current direct overlap = 0` 상태에서 common-cause direct overlap family가 채워졌다고 서술하는 패치
- curated seed 승격을 이유로 곧바로 algorithm threshold나 promotion rule을 바꾸는 패치
- single helper 또는 explanation-only row를 curated seed로 올리는 패치

### 필요한 문서 업데이트
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md)
- [OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)

### 필요한 코드 업데이트
- 없음
- 본 결정은 docs/regression gate 레벨이며 runtime rule/threshold는 바꾸지 않는다.

### 검증 계획
- 문서 검증:
  - BR-028 scan note, counterexample set, regression checklist가 본 결정을 모순 없이 참조하는지 확인
- 구조 검증:
  - curated seed로 승격된 사례가 `missing family closure`와 혼동되지 않게 note가 분리되는지 확인
- 최소 실행 검증:
  - `git diff --check`

### 롤백 트리거
- provisional shortlist 승격 후에도 실제 pressure-test에서 hold/reroute bundle을 거의 압박하지 못하는 경우
- seed 승격이 반복적으로 `target family 발견 완료`처럼 오독되는 경우
- 이후 exact missing family가 충분히 모여서 provisional/curated 구분 자체가 불필요해지는 경우

### 관련 근거
- [OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_028_MISSING_SEED_SCAN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_028_MISSING_SEED_SCAN_V1.md)
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_REGRESSION_CHECKLIST_V1.md)
- [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)
