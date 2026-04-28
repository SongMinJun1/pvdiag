<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_071_STRONG_COMMON_CAUSE_BLOCKER_REGRESSION_PACKET_V1

## Purpose
- Package BR-064 `strong_common_cause_hold_review` rows as regression/blocker material.
- Prevent strong spatial/common-cause evidence from being re-read as panel-local precursor or fault-family threshold evidence.
- Keep this as audit-only evidence for future algorithm patch pressure tests.

## Builder
- builder:
  - `research/prognostics/build_panel_day_engine_strong_common_cause_blocker_regression_packet_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_strong_common_cause_blocker_regression_packet_v1.py`

## Inputs
- BR-064 fault-family judgment candidate packet:
  - `/private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv`

## Outputs
- `/private/tmp/strong_common_cause_blocker_regression_packet_check/panel_day_engine_strong_common_cause_blocker_regression_packet_v1.csv`
- `/private/tmp/strong_common_cause_blocker_regression_packet_check/panel_day_engine_strong_common_cause_blocker_regression_summary_v1.csv`
- `/private/tmp/strong_common_cause_blocker_regression_packet_check/panel_day_engine_strong_common_cause_blocker_regression_note_v1.md`

## Real Data Result
- detail rows: `50`
- unique panel roots: `13`
- operator promotion allowed sum: `0`
- engine patch candidate sum: `0`
- threshold patch allowed sum: `0`
- panel-local promotion blocked sum: `50`

## Summary
| site | common_cause_blocker_type | cases | unique_panel_roots | blocked_sum | max_co_drop_frac_max |
| --- | --- | ---: | ---: | ---: | ---: |
| `gangui` | `group_off_synchrony_blocker` | 20 | 5 | 20 | 0.302198 |
| `ktc_ess` | `site_event_synchrony_blocker` | 30 | 8 | 30 | 0.491979 |

## Interpretation
- These 50 rows are useful because they are strong counterexamples.
- They should pressure-test future algorithm patches:
  - a future rule must not accidentally convert them into panel-local precursor positives
  - a future rule must not treat common-cause spatiality as exact panel-local family evidence
- `gangui` and `ktc_ess` show different blocker shapes:
  - `gangui`: group-off synchrony blocker
  - `ktc_ess`: site-event synchrony blocker
- This means a single common-cause rule should not be tuned only on one site shape.

## Decision
- Keep all 50 rows as `block_panel_local_promotion_regression_seed`.
- Do not promote any row to an operator-facing result.
- Do not authorize an engine patch or threshold patch from these rows.
- Future semantic patches must prove these rows remain blocked unless new independent evidence explicitly reclassifies them.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_strong_common_cause_blocker_regression_packet_v1.py research/prognostics/smoke_test_panel_day_engine_strong_common_cause_blocker_regression_packet_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_strong_common_cause_blocker_regression_packet_v1.py
python3 research/prognostics/build_panel_day_engine_strong_common_cause_blocker_regression_packet_v1.py --judgment-input /private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv --output-dir /private/tmp/strong_common_cause_blocker_regression_packet_check
```
