<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_074_COMMON_CAUSE_MANUAL_TRACE_REVIEW_V1

## Purpose
- Trace the two BR-073 common-cause manual targets against raw candidate rows and report-layer dates.
- Separate raw-only near-anchor trace evidence from official/current closure evidence.
- Keep this branch evidence-only; no production semantics are changed.

## Builder
- builder:
  - `research/prognostics/build_panel_day_engine_common_cause_manual_trace_review_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_common_cause_manual_trace_review_v1.py`

## Inputs
- BR-073 structural blocker review:
  - `/private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_v1.csv`
- tri-site current report:
  - `/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_current_v1.csv`
- tri-site precursor report:
  - `/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_precursor_report_v1.csv`
- tri-site raw-only signal report:
  - `/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_raw_only_fault_signal_report_v1.csv`
- raw daily candidates:
  - `/Users/b9gc/pvdiag/data/<site>/out/ae_simple_fault_candidates.csv`

## Outputs
- `/private/tmp/common_cause_manual_trace_review_check/panel_day_engine_common_cause_manual_trace_review_v1.csv`
- `/private/tmp/common_cause_manual_trace_review_check/panel_day_engine_common_cause_manual_trace_review_summary_v1.csv`
- `/private/tmp/common_cause_manual_trace_review_check/panel_day_engine_common_cause_manual_trace_review_note_v1.md`

## Real Data Result
- detail rows: `2`
- raw-only report bridge candidate sum: `1`
- official/current bridge candidate sum: `0`
- semantic patch candidate sum: `0`
- operator promotion allowed sum: `0`
- engine patch candidate sum: `0`
- threshold patch allowed sum: `0`

## Trace Result
| site | panel_id | subtype | raw date | report dates | trace outcome | bridge read |
| --- | --- | --- | --- | --- | --- | --- |
| `gangui` | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.1.1` | `rawonly_near_signal_anchor` | `2025-11-28` | raw-only `2025-11-15`, `2025-11-26` | `rawonly_near_anchor_trace_only` | raw-only report trace candidate only |
| `ktc_ess` | `10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12` | `official_current_date_displaced` | `2025-10-26` | official/current `2025-08-16`, raw-only `2025-08-16` | `post_current_common_cause_late_event_hold` | official/current mismatch |

## Interpretation
- `gangui` is close enough to explain a raw-only report trace:
  - raw direct common-cause date is `2` days after the nearest raw-only signal date.
  - this is not official/current closure because no official/current report row exists for the panel/date.
- `ktc_ess` is not bridgeable as a current common-cause closure:
  - raw direct common-cause date is `71` days after the official/current date.
  - the row stays a post-current mismatch unless the current report date is independently corrected.
- Both rows remain review/evidence material only.
- This closes the BR-073 manual trace queue without authorizing semantic loosening.

## Decision
- Keep `rawonly_near_anchor_trace_only` as a raw-only report generation trace, not a positive common-cause current example.
- Keep `post_current_common_cause_late_event_hold` as a date-alignment mismatch, not a bridge.
- Keep production promotion, engine patching, and threshold patching at `0`.
- Next common-cause work should use BR-071/072/073/074 packets as regression and hold evidence before any semantic algorithm patch.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_common_cause_manual_trace_review_v1.py research/prognostics/smoke_test_panel_day_engine_common_cause_manual_trace_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_common_cause_manual_trace_review_v1.py
python3 research/prognostics/build_panel_day_engine_common_cause_manual_trace_review_v1.py --blocker-input /private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_v1.csv --current-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_current_v1.csv --precursor-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_precursor_report_v1.csv --rawonly-signal-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_raw_only_fault_signal_report_v1.csv --data-root /Users/b9gc/pvdiag/data --output-dir /private/tmp/common_cause_manual_trace_review_check
```
