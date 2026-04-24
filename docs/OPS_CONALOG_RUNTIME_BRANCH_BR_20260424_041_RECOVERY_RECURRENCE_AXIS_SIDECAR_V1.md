<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_041_RECOVERY_RECURRENCE_AXIS_SIDECAR_V1

## Purpose
- `recovery_recurrence_axis`를 temp one-off scan이 아니라, 재현 가능한 evidence-only sidecar로 고정한다.

## Implementation
- added builder:
  - [build_panel_day_engine_recovery_recurrence_axis_v1.py](/private/tmp/pvdiag_postmerge_j/research/prognostics/build_panel_day_engine_recovery_recurrence_axis_v1.py)
- added smoke:
  - [smoke_test_panel_day_engine_recovery_recurrence_axis_v1.py](/private/tmp/pvdiag_postmerge_j/research/prognostics/smoke_test_panel_day_engine_recovery_recurrence_axis_v1.py)
- outputs:
  - `panel_day_engine_recovery_recurrence_axis_v1.csv`
  - `panel_day_engine_recovery_recurrence_axis_summary_v1.csv`

## Input Contract
- raw:
  - `data/<site>/out/ae_simple_fault_candidates.csv`
- result-layer:
  - `fault_panel_result_current_v1.csv` or `fault_panel_result_current_preview_v1.csv`
  - `fault_panel_result_raw_only_current_v1.csv` or `fault_panel_result_raw_only_current_preview_v1.csv`
  - `fault_panel_result_precursor_report_v1.csv`
  - `fault_panel_result_raw_only_fault_signal_report_v1.csv`

## What The Axis Explains
- panel별 raw candidate rows를 보고:
  - `transient_recovery`
  - `sustained_recovery`
  - `re_drop_cycle`
  - `persistent_non_recovery`
  로 먼저 분류한다.
- 그 다음 같은 panel이 어느 report lane까지 올라왔는지:
  - `official_current`
  - `rawonly_current`
  - `precursor`
  - `rawonly_signal`
  - `none`
  으로 읽는다.
- first use is:
  - morphology explanation
  - hold/review explanation
  - site-wise lane bias explanation

## Actual Check Snapshot
- run root:
  - [/private/tmp/conalog_mlpe_seed_expand_check/result](</private/tmp/conalog_mlpe_seed_expand_check/result>)
- sidecar output:
  - [/private/tmp/recovery_recurrence_axis_sidecar_check/panel_day_engine_recovery_recurrence_axis_v1.csv](/private/tmp/recovery_recurrence_axis_sidecar_check/panel_day_engine_recovery_recurrence_axis_v1.csv)
  - [/private/tmp/recovery_recurrence_axis_sidecar_check/panel_day_engine_recovery_recurrence_axis_summary_v1.csv](/private/tmp/recovery_recurrence_axis_sidecar_check/panel_day_engine_recovery_recurrence_axis_summary_v1.csv)

## Data Read
- `conalog`
  - `rawonly_current + re_drop_cycle = 28 panels`
  - `rawonly_current + sustained_recovery = 26 panels`
  - `rawonly_current + transient_recovery = 8 panels`
  - `rawonly_current + persistent_non_recovery = 8 panels`
- `gangui`
  - `rawonly_current + transient_recovery = 16 panels`
  - `rawonly_current + re_drop_cycle = 8 panels`
  - `precursor + transient_recovery = 3 panels`
  - `precursor + re_drop_cycle = 1 panel`
- `ktc_ess`
  - `none + re_drop_cycle = 24 panels`
  - `precursor + re_drop_cycle = 19 panels`
  - `none + transient_recovery = 14 panels`
  - `none + sustained_recovery = 10 panels`

## Why This Matters
- 이제 recovery-like raw evidence를 볼 때
  - 일시 회복인지
  - 지속 회복인지
  - 재드랍인지
  - 아예 회복이 없는 persistent인지
  를 반복 가능하게 설명할 수 있다.
- 동시에 site별로 왜 어떤 곳은 `rawonly_current`로 잘 올라오고, 어떤 곳은 `precursor`나 `none`에 남는지도 같이 볼 수 있다.

## Decision
- this branch is `implemented`.
- next preferred evidence-axis sidecar is `common_cause_synchrony_axis`.
