<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_052_LOCAL_MORPHOLOGY_EXACT_SEED_SEARCH_V1

## Purpose
- BR-051에서 분리한 `local_signal_morphology_review` pool만 대상으로 exact-family missing seed를 다시 찾는다.
- `strong_common_cause_hold_review` rows는 promotion seed가 아니라 blocker/regression pressure로 유지한다.
- 이 패치는 algorithm gating이 아니라 evidence-only seed search다.

## Builder
- script:
  - `research/prognostics/build_panel_day_engine_local_morphology_exact_seed_search_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_local_morphology_exact_seed_search_v1.py`

## Inputs
- cross-axis review:
  - `/private/tmp/cross_axis_manifest_sync_review_check`
- raw daily candidates:
  - `/Users/b9gc/pvdiag/data/<site>/out/ae_simple_fault_candidates.csv`
- result root:
  - `/private/tmp/conalog_mlpe_seed_expand_check/result`
- raw-only share root:
  - `/private/tmp/conalog_mlpe_seed_expand_check/raw_only_chain_workspace/_share`
- live share root:
  - `/private/tmp/conalog_mlpe_seed_expand_check/live_chain_workspace/_share`

## Outputs
- `/private/tmp/local_morphology_exact_seed_search_check/panel_day_engine_local_morphology_exact_seed_search_v1.csv`
- `/private/tmp/local_morphology_exact_seed_search_check/panel_day_engine_local_morphology_exact_seed_search_summary_v1.csv`

## Exact Closure Rule
- `exact_family_candidate` requires both:
  - top1 cause is one of `제어응답형`, `장치 응답 이상형`, `전력변환부 이상형`
  - same-day local morphology evidence exists on a report/audit anchor date
- `GPVS_외부참조패턴_ko = 장치 응답 이상형` alone is not exact closure.
- top2/top3 device/sensor competition is not exact closure.
- same-day local morphology with diode/open/degradation top1 is not exact closure.

## Real Data Result
- scanned pool:
  - `local_signal_morphology_review = 21`
- `exact_family_candidate_flag = 0`
- `target_exact_top1_flag = 0`
- `supportive_seed_candidate_flag = 1`
- `device_response_external_flag = 2`
- `sensor_feedback_top1_flag = 6`
- `exact_same_day_local_morphology_flag = 12`
- `same_day_re_drop_row_count = 2`

## Search Status Counts
| search_status | site | panels |
|---|---|---:|
| `local_morphology_non_exact` | `gangui` | 1 |
| `no_report_heuristic_match` | `conalog` | 6 |
| `no_report_heuristic_match` | `gangui` | 1 |
| `no_report_heuristic_match` | `ktc_ess` | 1 |
| `same_day_local_non_target` | `conalog` | 4 |
| `same_day_local_non_target` | `gangui` | 1 |
| `sensor_feedback_local_morphology_candidate` | `gangui` | 6 |
| `supportive_device_response_recovery_seed` | `ktc_ess` | 1 |

## Notable Rows
- `supportive_device_response_recovery_seed`
  - `ktc_ess / 70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4`
  - live external GPVS is `장치 응답 이상형`
  - raw top1 is `열화형`, live top1 is `열화형`
  - same-day local morphology exists
  - result: supportive seed, not exact closure
- `local_morphology_non_exact`
  - `gangui / bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7`
  - live external GPVS is `장치 응답 이상형`
  - same-day local morphology condition is weak under this scan
  - result: not exact closure
- `sensor_feedback_local_morphology_candidate`
  - 6 gangui rows
  - raw top1 is `센서·피드백형`
  - same-day local morphology exists
  - result: pressure seed for ambiguity checks, not target exact closure

## Decision
- BR-052 does not close the exact family gap.
- `장치 응답 이상형/제어응답형 top1` remains missing in this local morphology pool.
- The best next cleanup/evidence target is not threshold tuning.
- Next safe step:
  - inspect `no_report_heuristic_match = 8` as a report-lane / heuristic attachment gap.
- Algorithm gating remains blocked.

## Repro Command
```bash
python3 research/prognostics/build_panel_day_engine_local_morphology_exact_seed_search_v1.py --cross-axis-root /private/tmp/cross_axis_manifest_sync_review_check --data-root /Users/b9gc/pvdiag/data --result-root /private/tmp/conalog_mlpe_seed_expand_check/result --raw-only-share-root /private/tmp/conalog_mlpe_seed_expand_check/raw_only_chain_workspace/_share --live-share-root /private/tmp/conalog_mlpe_seed_expand_check/live_chain_workspace/_share --output-dir /private/tmp/local_morphology_exact_seed_search_check --sites conalog gangui ktc_ess
```
