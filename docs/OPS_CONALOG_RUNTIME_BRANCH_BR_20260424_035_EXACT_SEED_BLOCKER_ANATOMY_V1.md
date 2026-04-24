<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_035_EXACT_SEED_BLOCKER_ANATOMY_V1

## Purpose
- BR-034 이후 exact seed search를 더 효율적으로 하기 위해, `왜 exact family가 안 닫히는지`를 blocker anatomy 관점에서 분해한다.
- 이번 턴의 초점은 `same-day direct overlap` family다.

## Scope
- source:
  - `data/<site>/out/ae_simple_fault_candidates.csv`
  - `/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_current_v1.csv`
  - `/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_precursor_report_v1.csv`
  - `/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_raw_only_fault_signal_report_v1.csv`
- filter:
  - direct common-cause same-day row
    - `group_off_date = 1`
    - or `site_event_soft/site_event_hard > 0`
  - plus at least one signal-strength marker
    - `pre_ews`, `prefault_B`, `fault_like_day`, `final_fault`, `critical_fault`

## Result
### 1. raw-daily exact row reservoir exists
- `101 rows`
- `49 panels`
- site split:
  - `gangui = 71`
  - `ktc_ess = 30`

### 2. but report-layer exact family still does not exist
- top-level artifact presence by panel:
  - `precursor = 19`
  - `rawonly = 16`
  - `none = 13`
  - `current = 1`
- only current panel:
  - `ktc_ess 10305...2.12`
  - same-day exact raw row is `2025-10-26`
  - nearest current `고장날짜` is `2025-08-16`
  - gap `71일`

### 3. blocker split
- `group_off_date` family:
  - mainly `rawonly`
  - exact row reservoir exists, but current lane entry is weak
- `site_event` family:
  - mainly `precursor` or `none`
  - exact row reservoir exists, but report-lane date coincidence is weak

## Reading
- `same-day exact` family missing is not the same thing as `raw-daily exact row missing`.
- current evidence says the stronger blocker is:
  - top-level row universe mismatch
  - summary/report date displacement
- therefore next exact seed search should target blocker removal opportunities, not just more raw-row enumeration.

## Next Safe Step
1. `group_off_date -> current/report-lane entry` blocker 사례를 먼저 찾기
2. `site_event -> report-date coincidence` blocker 사례를 먼저 찾기
3. control-family는 separate lane에서 계속 native non-GPVS evidence를 찾기
