<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_015_V1

## Decision
- widened `±7일 near-window overlap backlog`는 `separate provisional family`로 아직 승격하지 않는다.
- 현재는 `non-closing backlog`로 유지하고, `same-day exact missing family` 수집을 다음 우선순위로 둔다.

## Evidence
- BR-033 data assessment 기준:
  - `event rows = 9`
  - `independent report rows = 5`
  - `independent roots = 4`
  - slice mix:
    - `precursor_onset = 4 report rows`
    - `current_fault = 1 report row`
  - direct flag family mix:
    - `group_off_date = 3 report rows`
    - `site_event_soft+site_event_hard = 2 report rows`
  - gap direction mix:
    - `event_before_report = 3`
    - `event_after_report = 2`
    - `same_day = 0`
- 따라서 backlog는 존재하지만, 아직 하나의 coherent provisional family로 읽을 만큼 정렬되지 않았다.

## Why Not Promote Yet
- `group_off_date`와 `site_event_soft+site_event_hard`가 섞여 있다.
- `precursor_onset`와 `current_fault` slice가 섞여 있다.
- gap sign이 한 방향으로 정렬되지 않는다.
- `group_off_date` proto-cluster는 report row `3`, root `2`라서 반복성은 있지만 독립 root 수가 아직 얇다.
- `site_event` proto-cluster는 report row `2`라서 더 얇다.

## Future Promotion Criteria
- near-window backlog를 separate provisional family로 다시 검토하려면 아래를 동시에 만족해야 한다.
  1. 하나의 direct flag family로 수렴할 것
  2. 하나의 slice type으로 수렴할 것
  3. report row `3+` 이면서 root `3+` 를 가질 것
  4. gap direction sign이 대부분 같은 방향으로 정렬될 것
- 위 조건을 만족하기 전까지 near-window backlog는 `pressure-test hint`일 뿐 `family closure` 대체물이 아니다.

## Consequence
- 다음 patch gate에서는 near-window backlog를 exact precedent로 쓰지 않는다.
- 다음 안전 작업은 `제어응답형 top1`, `official/current direct overlap` 같은 `same-day exact` missing family search를 계속하는 것이다.
