<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_038_PATCH_DIRECTION_RATIONALE_LOCK_V1

## Purpose
- 최근 BR-033 ~ BR-037이 왜 `즉시 알고리즘 패치`가 아니라 `판단 기준 잠금 + blocker 해부` 방향으로 갔는지 명시적으로 남긴다.
- 목적은 이후 턴에서 “왜 이렇게 보수적으로 갔는지”를 다시 설명할 필요 없이, 방향 선택 이유 자체를 문서로 고정하는 것이다.

## What Direction Was Chosen
- chosen direction:
  - `docs/evidence-first`
  - `judgment-role-first`
  - `blocker-decomposition-first`
  - `algorithm gating last`

## Why This Direction Was Chosen
### 1. exact family가 아직 닫히지 않았다
- `제어응답형 top1`은 여전히 `0`
- official/current direct common-cause same-day exact family도 여전히 `0`
- therefore:
  - 지금 threshold/rule patch는 `existing exact closure 반영`이 아니라 `missing family를 추정으로 메우는 patch`가 되기 쉽다.

### 2. 근거는 있으나 대부분 exact보다 아래 급이다
- current evidence landscape:
  - `supportive_hint`
    - BR-034 `control_score > 0`
  - `candidate_reservoir`
    - BR-035 raw-daily same-day direct rows
  - `non_closing_backlog`
    - BR-033 near-window overlap backlog
  - `structural_blocker`
    - BR-035 row-universe/date-alignment mismatch
- therefore:
  - evidence exists
  - but most of it is not yet `exact_family_closure`

### 3. 지금 위험은 false negative보다 false closure에 더 가깝다
- raw rows, hint scores, backlog를 서둘러 exact family처럼 읽으면 아래 오판이 생긴다.
  - `supportive_hint -> exact family`
  - `candidate_reservoir -> report-layer closure`
  - `non_closing_backlog -> provisional family`
- 이런 오판은 operator-facing semantics와 later rule patch를 동시에 오염시킬 수 있다.

### 4. blocker가 구조적인지 먼저 확인해야 patch target이 생긴다
- BR-035 이후 핵심 질문은
  - “raw row가 더 있나?”가 아니라
  - “왜 report-layer exact로 못 올라오나?”다
- BR-037에서 `group_off_date` family를 다시 나누자 실제로는 하나의 blocker가 아니었다.
  - `no_report_lane_entry`
  - `precursor_carryover_without_exact_overlap`
  - `rawonly_date_displaced`
  - `rawonly_near_signal_anchor`
- therefore:
  - patch target은 family 전체가 아니라 blocker subtype이어야 한다.

### 5. 이 방향이 오히려 나중 patch를 더 강하게 만든다
- 지금 문서화로 얻는 것:
  - evidence grade 혼선 감소
  - patch justification 선명화
  - exact closure와 hold/review 근거 분리
  - next inspect target 명확화
- 즉 지금의 보수성은 “미루기”가 아니라 “나중 patch의 방어력 확보”다.

## What This Direction Explicitly Rejects
- exact family가 비어 있는데도 score/hint만으로 threshold patch 넣기
- raw-daily exact row reservoir를 report-layer exact closure처럼 읽기
- backlog를 coherent family처럼 승격하기
- blocker subtype을 나누지 않고 family 전체에 일괄 규칙을 넣기

## Consequence
- 다음 단계의 질문은 아래 순서로 고정한다.
  1. `이 evidence의 judgment role은 무엇인가`
  2. `exact closure가 아직 없으면 blocker subtype은 무엇인가`
  3. `near-anchor residual 같은 next inspect target이 있는가`
  4. `그 다음에야 algorithm patch target이 존재하는가`

## Next Safe Step
1. `group_off_date`의 `rawonly_near_signal_anchor` residual inspect
2. `site_event -> report-date coincidence` blocker inspect
3. control-family native non-GPVS evidence search
