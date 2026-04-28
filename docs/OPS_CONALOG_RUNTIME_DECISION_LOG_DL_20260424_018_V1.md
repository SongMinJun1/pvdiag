<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_018_V1

## Decision
- Gate 7에서 새 근거를 읽을 때는 먼저 아래 `judgment role` 중 하나로 분류한다.
  - `exact_family_closure`
  - `supportive_hint`
  - `candidate_reservoir`
  - `non_closing_backlog`
  - `structural_blocker`
- `curated pressure-test seed`는 별도 role이 아니라 `test usage tag`다.
- 따라서 pressure-test seed로 승격된 row라도, underlying role이 `supportive_hint`, `candidate_reservoir`, `non_closing_backlog`, `structural_blocker` 중 하나면 `exact_family_closure`로 읽지 않는다.
- algorithm gating patch는 `exact_family_closure` 또는 `structural_blocker`를 직접 겨냥한 해소 경로가 있을 때만 논의한다.
- `supportive_hint`, `candidate_reservoir`, `non_closing_backlog`는 단독으로 family closure나 rule patch justification이 아니다.

## Evidence
- BR-033 기준 widened `±7일 near-window overlap backlog`는 아래처럼 혼합 상태다.
  - `5 report rows`
  - `4 roots`
  - `group_off_date = 3 report rows`
  - `site_event_soft+site_event_hard = 2 report rows`
  - `precursor_onset = 4 report rows`
  - `current_fault = 1 report row`
  - gap sign:
    - `event_before_report = 3`
    - `event_after_report = 2`
    - `same_day = 0`
- BR-034 기준 `제어응답형 top1`은 runtime/live-chain 모두 `0`이지만, `제어응답형 raw_score > 0` 패널은 `4개`다.
- BR-035 기준 raw-daily same-day direct common-cause row reservoir는 존재한다.
  - `101 rows`
  - `49 panels`
  - top-level artifact presence:
    - `precursor = 19`
    - `rawonly = 16`
    - `none = 13`
    - `current = 1`
  - only current panel gap:
    - nearest current `고장날짜` gap `71일`
- 즉 현재 evidence는 `있다/없다`보다 `어떤 급의 근거인가`를 먼저 고정해야 과잉 일반화를 막을 수 있다.

## Reading
- `exact_family_closure`
  - report-layer row 존재
  - artifact-date coincidence 또는 동일 family identity가 직접 성립
  - helper/additive-only 설명으로 닫히지 않음
- `supportive_hint`
  - score나 설명축 보강에는 기여하지만, family closure를 만들지 못함
  - 예: `control_score > 0`, GPVS/usage add-on
- `candidate_reservoir`
  - raw-daily row reservoir는 충분하지만 report-layer exact closure는 아직 아님
  - 예: BR-035 same-day direct common-cause raw rows
- `non_closing_backlog`
  - 추적 가치는 있으나 아직 하나의 family/provisional family로 승격할 정도로 정렬되지 않음
  - 예: BR-033 near-window backlog
- `structural_blocker`
  - raw row가 있어도 report-lane entry, row universe, date alignment 문제 때문에 closure가 막힘
  - 예: BR-035 row-universe mismatch + summary date displacement

## Consequence
- 앞으로 Gate 7 문서/스캔/patch note는 새 근거를 제시할 때 아래 둘을 같이 적는다.
  1. `judgment role`
  2. `allowed use`
- allowed use 기본 규칙은 아래와 같다.
  - `exact_family_closure` -> exact missing family closure 근거 가능
  - `supportive_hint` -> ranking/explanation/support only
  - `candidate_reservoir` -> blocker search input only
  - `non_closing_backlog` -> backlog tracking and future promotion test only
  - `structural_blocker` -> patch target selection and blocker split only
