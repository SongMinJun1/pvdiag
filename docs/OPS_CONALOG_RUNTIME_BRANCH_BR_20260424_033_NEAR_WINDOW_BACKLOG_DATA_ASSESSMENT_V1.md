<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_033_NEAR_WINDOW_BACKLOG_DATA_ASSESSMENT_V1

## Purpose
- BR-032에서 잠근 문서 경계를 실제 데이터로 다시 눌러 본다.
- 목표는 widened `±7일 near-window overlap backlog`가 separate provisional family로 승격 가능한지 판단하는 것이다.

## Scope
- source root:
  - `/private/tmp/conalog_mlpe_seed_expand_check`
- compared artifacts:
  - `fault_panel_result_precursor_report_v1.csv`
  - `fault_panel_result_current_v1.csv`
  - `data/<site>/out/ae_simple_local_precursor_gate_daily.csv`

## Assessment Rule
- 이번 평가는 `direct common-cause calendar/event`만 본다.
  - `group_off_date`
  - `site_event_soft`
  - `site_event_hard`
- `subgroup_common_cause_candidate`는 broader suppressor 이므로 이번 near-window family 판단에서는 제외한다.

## Result
### 1. widened near-window overlap backlog size
- `event rows = 9`
- `independent report rows = 5`
- `independent roots = 4`

### 2. slice / flag / sign composition
- slice:
  - `precursor_onset = 4 report rows`
  - `current_fault = 1 report row`
- direct flag family:
  - `group_off_date = 3 report rows`
  - `site_event_soft+site_event_hard = 2 report rows`
- gap sign:
  - `event_before_report = 3`
  - `event_after_report = 2`
  - `same_day = 0`

### 3. proto-cluster read
- `group_off_date` proto-cluster
  - report rows `3`
  - roots `2`
  - site `gangui` only
  - gap `+5`, `+6`, `-7`
- `site_event_soft+site_event_hard` proto-cluster
  - report rows `2`
  - roots `2`
  - site `ktc_ess` only
  - gap `-5`, `-2`

## Reading
- near-window backlog는 실제로 존재한다.
- 하지만 현재는 하나의 family 라기보다 `두 개의 얇은 proto-cluster`에 더 가깝다.
- 특히 `flag family`, `slice`, `gap direction`이 한 축으로 정렬되지 않아 아직 family 승격 근거가 부족하다.

## Decision
- BR-033 기준 near-window backlog는 `separate provisional family`로 승격하지 않는다.
- 대신 아래처럼 유지한다.
  - `non-closing backlog`
  - `pressure-test hint`
  - `same-day exact family`의 대체물 아님

## Next Safe Step
1. `제어응답형 top1` exact seed search를 계속
2. `official/current direct overlap` same-day exact seed search를 계속
3. near-window는 한 proto-cluster가 `same flag family + same slice + 3 roots + stable sign`을 만족할 때만 재승격 검토
