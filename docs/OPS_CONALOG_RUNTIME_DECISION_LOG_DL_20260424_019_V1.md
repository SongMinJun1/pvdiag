<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_019_V1

## Decision
- `group_off_date` same-day exact raw row가 존재할 때는, 먼저 아래 `report-lane entry blocker subtype`으로 분류한다.
  1. `no_report_lane_entry`
  2. `precursor_carryover_without_exact_overlap`
  3. `rawonly_date_displaced`
  4. `rawonly_near_signal_anchor`
- 위 subtype 분해를 하기 전에는 `group_off_date` raw row 존재를 `official/current exact family closure` 근거로 읽지 않는다.
- 특히 `rawonly_date_displaced`와 `precursor_carryover_without_exact_overlap`는 `group_off exact row exists`보다 stronger blocker로 읽는다.

## Evidence
- `/private/tmp/group_off_report_lane_entry_blocker_check/group_off_report_lane_blocker_summary_v1.csv` 기준:
  - `no_report_lane_entry`
    - `1 panel`
    - `1 group_off row`
  - `precursor_carryover_without_exact_overlap`
    - `2 panels`
    - `3 group_off rows`
    - nearest precursor gap minimum `6일`
  - `rawonly_date_displaced`
    - `15 panels`
    - `66 group_off rows`
    - nearest raw signal gap minimum `11일`
    - nearest raw start gap minimum `20일`
  - `rawonly_near_signal_anchor`
    - `1 panel`
    - `1 group_off row`
    - nearest raw signal gap `2일`
- representative panels:
  - `no_report_lane_entry`
    - `gangui / 4fd0...3.22`
    - `2025-12-04`
    - `pre_ews` only, no precursor/rawonly/current row
  - `precursor_carryover_without_exact_overlap`
    - `gangui / 4fd0...0.13`
    - group-off row dates `2025-11-23, 2025-12-03`
    - precursor date `2025-11-17`
    - nearest gap `6일`
    - reading stays `열화형 고위험 관찰`
  - `rawonly_date_displaced`
    - `gangui / bf1a...1.2`
    - group-off cluster `2025-11-23` to `2025-12-04`
    - raw-only `신호 기준일 = 2025-11-11`
    - repeated `급작 고장 / 장치 측정 이상형`
  - `rawonly_near_signal_anchor`
    - `gangui / bf1a...1.1`
    - group-off date `2025-11-28`
    - raw-only `신호 기준일 = 2025-11-26`
    - gap `2일`

## Reading
- `no_report_lane_entry`
  - raw row는 있지만 top-level artifact row를 전혀 만들지 못한 케이스다.
- `precursor_carryover_without_exact_overlap`
  - group-off row보다 earlier precursor onset이 먼저 artifact를 잡고 있어, exact overlap family가 아니라 precursor carry-over가 stronger reading이다.
- `rawonly_date_displaced`
  - raw-only artifact는 존재하지만 anchor date가 group-off cluster보다 충분히 earlier라, report-layer exact family closure가 아니다.
- `rawonly_near_signal_anchor`
  - exact는 아니지만 signal anchor가 가까워서, 향후 date-alignment blocker inspect 대상으로는 의미가 있다.

## Consequence
- 다음 common-cause same-day exact search에서는 `group_off_date` rows를 먼저 아래 순서로 자른다.
  1. lane entry 없음
  2. precursor carry-over
  3. raw-only anchor displacement
  4. near-anchor residual
- 따라서 `group_off_date` family의 다음 우선 질문은 “raw row가 더 있나”가 아니라, `near-anchor residual`을 report-layer exact closure로 바꿀 수 있는지 여부다.
