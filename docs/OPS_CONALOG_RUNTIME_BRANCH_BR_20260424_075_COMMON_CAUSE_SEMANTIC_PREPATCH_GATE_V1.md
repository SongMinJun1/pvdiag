<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_075_COMMON_CAUSE_SEMANTIC_PREPATCH_GATE_V1

## Purpose
- Convert BR-071 through BR-074 common-cause hold/regression evidence into an executable prepatch gate.
- Prevent future semantic algorithm patches from accidentally treating common-cause synchrony, raw-only near-anchor traces, or post-current date-displaced rows as official/current closure.
- Keep this branch evidence/safety-only; no production semantics are changed.

## Gate
- gate:
  - `research/prognostics/check_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py`

## Inputs
- BR-071 strong common-cause blocker regression packet:
  - `/private/tmp/strong_common_cause_blocker_regression_packet_check/panel_day_engine_strong_common_cause_blocker_regression_packet_v1.csv`
- BR-072 common-cause exact seed search:
  - `/private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv`
- BR-073 structural blocker review:
  - `/private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_v1.csv`
- BR-074 manual trace review:
  - `/private/tmp/common_cause_manual_trace_review_check/panel_day_engine_common_cause_manual_trace_review_v1.csv`

## Outputs
- `/private/tmp/common_cause_semantic_prepatch_gate_check/panel_day_engine_common_cause_semantic_prepatch_gate_v1.csv`
- `/private/tmp/common_cause_semantic_prepatch_gate_check/panel_day_engine_common_cause_semantic_prepatch_gate_summary_v1.csv`
- `/private/tmp/common_cause_semantic_prepatch_gate_check/panel_day_engine_common_cause_semantic_prepatch_gate_note_v1.md`

## Real Data Result
- overall status: `pass`
- required gate count: `12`
- failed required gate count: `0`
- warning gate count: `1`
- BR-071 strong blocker rows: `50`
- BR-072 exact search rows: `176`
- BR-073 structural rows: `49`
- BR-074 trace rows: `2`
- exact family closure sum: `0`
- candidate reservoir sum: `49`
- structural blocker sum: `49`
- raw direct common-cause row sum: `101`
- manual trace review sum: `2`
- raw-only report bridge candidate sum: `1`
- official/current bridge candidate sum: `0`
- semantic patch candidate sum: `0`
- operator promotion allowed sum: `0`
- engine patch candidate sum: `0`
- threshold patch allowed sum: `0`

## Warning
- `W01_rawonly_trace_is_context_only` is expected and non-blocking:
  - observed value: `1`
  - meaning: one raw-only near-anchor trace exists
  - boundary: this is context only and must not become official/current closure

## Interpretation
- This gate passing does not approve a common-cause semantic patch.
- This gate passing means the known common-cause hold/regression evidence is intact:
  - strong common-cause blockers remain blockers
  - exact closure remains `0`
  - structural blockers remain accounted for
  - manual trace rows remain non-closure and non-promoting
- Any future common-cause semantic patch must still attach one of the following:
  - independent same-day official/current closure evidence
  - explicit report-date correction evidence
  - a separate decision log changing the evidence contract

## Decision
- Run this gate before any semantic algorithm patch that could affect common-cause panel-local promotion.
- Do not use raw-only near-anchor traces as official/current closure.
- Do not use post-current common-cause rows as current closure without independent report-date correction.
- Keep BR-071~BR-075 in the blocker/regression/safety layer until stronger current-layer evidence is attached.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/check_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py research/prognostics/smoke_test_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py
python3 research/prognostics/check_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py --strong-blocker-input /private/tmp/strong_common_cause_blocker_regression_packet_check/panel_day_engine_strong_common_cause_blocker_regression_packet_v1.csv --exact-search-input /private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv --structural-input /private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_v1.csv --trace-input /private/tmp/common_cause_manual_trace_review_check/panel_day_engine_common_cause_manual_trace_review_v1.csv --output-dir /private/tmp/common_cause_semantic_prepatch_gate_check
```
