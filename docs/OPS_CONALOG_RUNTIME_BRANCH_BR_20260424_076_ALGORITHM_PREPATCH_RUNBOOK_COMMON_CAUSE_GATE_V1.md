<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_076_ALGORITHM_PREPATCH_RUNBOOK_COMMON_CAUSE_GATE_V1

## Purpose
- Integrate BR-075 common-cause semantic prepatch gate into the existing panel-engine algorithm prepatch runbook.
- Make the default direct `panel_day_engine.py` algorithm patch precondition cover three layers:
  - panel-engine patch safety gate
  - fault-family regression prepatch gate
  - common-cause semantic prepatch gate
- Keep this branch safety/runbook-only; no production semantics are changed.

## Changed Runbook
- runbook:
  - `research/prognostics/check_panel_day_engine_algorithm_prepatch_runbook_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_algorithm_prepatch_runbook_v1.py`

## New Inputs Added To Runbook
- `--common-cause-strong-blocker-input`
- `--common-cause-exact-search-input`
- `--common-cause-structural-input`
- `--common-cause-trace-input`

## Outputs
- `/private/tmp/panel_engine_algorithm_prepatch_runbook_br076_check/panel_day_engine_algorithm_prepatch_runbook_v1.csv`
- `/private/tmp/panel_engine_algorithm_prepatch_runbook_br076_check/panel_day_engine_algorithm_prepatch_runbook_summary_v1.csv`
- nested gate outputs:
  - `/private/tmp/panel_engine_algorithm_prepatch_runbook_br076_check/panel_engine_patch_safety_gate/`
  - `/private/tmp/panel_engine_algorithm_prepatch_runbook_br076_check/fault_family_regression_prepatch_gate/`
  - `/private/tmp/panel_engine_algorithm_prepatch_runbook_br076_check/common_cause_semantic_prepatch_gate/`

## Real Data Result
- overall status: `pass`
- gate count: `3`
- passed gate count: `3`
- failed gate count: `0`
- panel-engine gate status: `pass`
- fault-family gate status: `pass`
- common-cause gate status: `pass`
- engine change detected: `0`
- fault-family packet rows: `11`
- fault-family target exact closure candidate sum: `0`
- common-cause required gate count: `12`
- common-cause failed required gate count: `0`
- common-cause warning gate count: `1`
- common-cause exact family closure sum: `0`
- common-cause raw direct row sum: `101`
- common-cause official/current bridge candidate sum: `0`
- common-cause semantic patch candidate sum: `0`
- common-cause operator/engine/threshold patch sums: `0`

## Interpretation
- Before BR-076, the combined runbook covered panel-engine source safety and fault-family regression pressure.
- After BR-076, the same combined runbook also blocks accidental common-cause semantic loosening.
- Passing this runbook is still not algorithm patch approval.
- Passing means the minimum safety gates are intact before a human reviews whether a proposed algorithm patch has enough evidence.

## Decision
- Use `check_panel_day_engine_algorithm_prepatch_runbook_v1.py` as the default combined prepatch command before direct `panel_day_engine.py` algorithm review.
- Treat `gate_count=3` as the expected current contract.
- Do not treat the common-cause warning as failure:
  - it records that a raw-only near-anchor trace exists
  - it must stay context-only unless separate current-layer closure evidence appears

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/check_panel_day_engine_algorithm_prepatch_runbook_v1.py research/prognostics/smoke_test_panel_day_engine_algorithm_prepatch_runbook_v1.py research/prognostics/check_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py research/prognostics/smoke_test_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_algorithm_prepatch_runbook_v1.py
python3 research/prognostics/check_panel_day_engine_algorithm_prepatch_runbook_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --packet-input /private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv --common-cause-strong-blocker-input /private/tmp/strong_common_cause_blocker_regression_packet_check/panel_day_engine_strong_common_cause_blocker_regression_packet_v1.csv --common-cause-exact-search-input /private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv --common-cause-structural-input /private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_v1.csv --common-cause-trace-input /private/tmp/common_cause_manual_trace_review_check/panel_day_engine_common_cause_manual_trace_review_v1.csv --output-dir /private/tmp/panel_engine_algorithm_prepatch_runbook_br076_check
```
