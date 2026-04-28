<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_040_REPORT_ENTRY_FRICTION_AXIS_SIDECAR_V1

## Purpose
- `report_entry_friction_axis`를 temp one-off scan이 아니라, 반복 실행 가능한 evidence-only sidecar로 고정한다.

## Implementation
- added builder:
  - [build_panel_day_engine_report_entry_friction_axis_v1.py](/private/tmp/pvdiag_postmerge_j/research/prognostics/build_panel_day_engine_report_entry_friction_axis_v1.py)
- added smoke:
  - [smoke_test_panel_day_engine_report_entry_friction_axis_v1.py](/private/tmp/pvdiag_postmerge_j/research/prognostics/smoke_test_panel_day_engine_report_entry_friction_axis_v1.py)
- outputs:
  - `panel_day_engine_report_entry_friction_axis_v1.csv`
  - `panel_day_engine_report_entry_friction_axis_summary_v1.csv`

## Input Contract
- raw:
  - `data/<site>/out/ae_simple_fault_candidates.csv`
- result-layer:
  - `fault_panel_result_current_v1.csv` or `fault_panel_result_current_preview_v1.csv`
  - `fault_panel_result_precursor_report_v1.csv`
  - `fault_panel_result_raw_only_current_v1.csv`
  - `fault_panel_result_raw_only_fault_signal_report_v1.csv`

## What The Axis Explains
- `group_off_date`, `site_event` direct raw rows가
  - `current`
  - `precursor`
  - `rawonly`
  - `none`
  중 어디까지 진입했는지 설명한다.
- same-day exact가 없을 때는 다음 blocker subtype 중 하나로 떨어진다.
  - `no_report_lane_entry`
  - `current_date_displaced`
  - `precursor_carryover_without_exact_overlap`
  - `rawonly_date_displaced`
  - `rawonly_near_signal_anchor`

## Actual Check Snapshot
- run root:
  - [/private/tmp/conalog_mlpe_seed_expand_check/result](</private/tmp/conalog_mlpe_seed_expand_check/result>)
- sidecar output:
  - [/private/tmp/report_entry_friction_axis_sidecar_check/panel_day_engine_report_entry_friction_axis_v1.csv](/private/tmp/report_entry_friction_axis_sidecar_check/panel_day_engine_report_entry_friction_axis_v1.csv)
  - [/private/tmp/report_entry_friction_axis_sidecar_check/panel_day_engine_report_entry_friction_axis_summary_v1.csv](/private/tmp/report_entry_friction_axis_sidecar_check/panel_day_engine_report_entry_friction_axis_summary_v1.csv)

## Data Read
- `group_off_date`
  - `no_report_lane_entry = 1 panel`
  - `precursor_carryover_without_exact_overlap = 2 panels`
  - `rawonly_date_displaced = 15 panels`
  - `rawonly_near_signal_anchor = 1 panel`
- `site_event`
  - `current_date_displaced = 1 panel`
  - `no_report_lane_entry = 12 panels`
  - `precursor_carryover_without_exact_overlap = 17 panels`

## Why This Matters
- 이제 `group_off/site_event`를 다시 볼 때 “exact family가 비어 있다”만 말하지 않고,
  - lane 진입 실패인지
  - precursor carry-over인지
  - rawonly date displacement인지
  - near-anchor residual인지
  를 반복 가능하게 설명할 수 있다.

## Decision
- this branch is `implemented`.
- next preferred evidence-axis sidecar is `recovery_recurrence_axis`.
