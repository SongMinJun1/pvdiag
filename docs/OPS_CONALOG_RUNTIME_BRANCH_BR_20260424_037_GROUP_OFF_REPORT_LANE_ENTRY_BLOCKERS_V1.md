<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_037_GROUP_OFF_REPORT_LANE_ENTRY_BLOCKERS_V1

## Purpose
- BR-035에서 확인한 `group_off_date` exact raw-row reservoir가 왜 report-layer exact family를 닫지 못하는지, 실제 blocker subtype으로 분해한다.

## Scope
- source:
  - `data/gangui/out/ae_simple_fault_candidates.csv`
  - `/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_precursor_report_v1.csv`
  - `/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_raw_only_fault_signal_report_v1.csv`
  - `/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_current_v1.csv`
- filter:
  - `group_off_date = 1`
  - plus any of:
    - `pre_ews`
    - `prefault_B`
    - `fault_like_day`
    - `final_fault`
    - `critical_fault`

## Result
### 1. group-off exact row reservoir is gangui-only in the current scan
- `71 rows`
- `19 panels`
- site split:
  - `gangui = 71`
  - `ktc_ess = 0`

### 2. report-lane entry distribution
- `no_report_lane_entry`
  - `1 panel`
  - `1 row`
- `precursor_carryover_without_exact_overlap`
  - `2 panels`
  - `3 rows`
- `rawonly_date_displaced`
  - `15 panels`
  - `66 rows`
- `rawonly_near_signal_anchor`
  - `1 panel`
  - `1 row`
- `current exact closure`
  - `0 panel`

### 3. subtype reading
- `no_report_lane_entry`
  - current/precursor/raw-only 어느 lane도 안 잡힘
  - example:
    - `gangui / 4fd0...3.22`
    - `2025-12-04`
    - `pre_ews only`
- `precursor_carryover_without_exact_overlap`
  - earlier precursor onset이 먼저 잡혀서 exact overlap family를 닫지 못함
  - examples:
    - `gangui / 4fd0...0.13`
      - precursor `2025-11-17`
      - nearest group-off gap `6일`
    - `gangui / bf1a...1.0`
      - precursor `2025-11-18`
      - nearest group-off gap `10일`
- `rawonly_date_displaced`
  - raw-only artifact는 존재하지만 `신호 기준일`이 group-off cluster보다 충분히 earlier
  - dominant shape:
    - `급작 고장 = 13`
    - `전조형 고장 = 2`
    - `장치 측정 이상형 = 9`
    - `다이오드·국소 회로 이상형 = 4`
  - representative cluster:
    - `bf1a...1.2/1.3/1.4/1.5/1.6/1.7/1.8/1.9`
    - group-off rows `2025-11-23` to `2025-12-04`
    - raw-only `신호 기준일 = 2025-11-11`
- `rawonly_near_signal_anchor`
  - exact는 아니지만 date gap이 좁아 다음 inspect 우선순위가 높음
  - example:
    - `gangui / bf1a...1.1`
    - group-off `2025-11-28`
    - raw-only `신호 기준일 = 2025-11-26`
    - gap `2일`

## Reading
- 현재 `group_off_date` family의 핵심 blocker는 `raw row 부재`가 아니다.
- stronger blocker는 아래다.
  - report-lane entry 없음
  - precursor carry-over가 먼저 lane을 잡음
  - raw-only lane은 잡지만 date anchor가 earlier signal에 묶임
- 따라서 `group_off_date` same-day raw row를 곧바로 `official/current same-day direct overlap family` 근거로 읽으면 안 된다.

## Next Safe Step
1. `rawonly_near_signal_anchor` 패널을 먼저 deeper inspect 한다.
2. `precursor_carryover_without_exact_overlap` 패널에서 group-off가 subtype hold인지, late-stage common-cause shadow인지 분리한다.
3. `rawonly_date_displaced` 대다수 클러스터는 exact-family search보다 `anchor displacement` pattern library로 관리한다.
