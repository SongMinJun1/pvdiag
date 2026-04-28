<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_059_FAULT_FAMILY_REGRESSION_PREPATCH_GATE_V1

## Purpose
- BR-058 fault-family regression pressure packet을 future algorithm patch 전 실행 가능한 gate로 고정한다.
- 목적은 packet rows가 target exact closure, operator promotion, engine patch candidate로 변질되는지 먼저 막는 것이다.
- 이 패치는 runtime verdict, threshold, row universe, operator-facing semantics를 바꾸지 않는다.

## Gate
- script:
  - `research/prognostics/check_panel_day_engine_fault_family_regression_prepatch_gate_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_fault_family_regression_prepatch_gate_v1.py`

## Input
- BR-058 pressure packet:
  - `/private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv`

## Outputs
- `/private/tmp/fault_family_regression_prepatch_gate_check/panel_day_engine_fault_family_regression_prepatch_gate_v1.csv`
- `/private/tmp/fault_family_regression_prepatch_gate_check/panel_day_engine_fault_family_regression_prepatch_gate_summary_v1.csv`

## Required Gate Rules
- packet exists and is non-empty.
- required regression columns are present.
- minimum pressure bucket counts are preserved:
  - `non_target_hard_same_day_fault_family_seed >= 5`
  - `sensor_feedback_hard_same_day_ambiguity_pressure >= 6`
- both counterexample buckets are present:
  - `fault_family_boundary_pressure`
  - `mlpe_ambiguous`
- packet rows must keep:
  - `target_exact_closure_candidate_sum = 0`
  - `operator_promotion_allowed_sum = 0`
  - `engine_patch_candidate_sum = 0`
- every packet row must carry same-day final fault pressure context.
- common-cause rows must not be mixed into this packet.
- packet case IDs and interpretation text must remain populated.

## Real Data Result
- packet rows:
  - `11`
- required gates:
  - `12`
- failed required gates:
  - `0`
- overall status:
  - `pass`
- target exact closure candidates:
  - `0`
- operator promotion allowed:
  - `0`
- engine patch candidates:
  - `0`

## Decision
- Accept BR-059 as the pre-patch gate for BR-058 packet rows.
- Any future `panel_day_engine.py` algorithm patch must run this gate before threshold/rule discussion.
- Passing this gate does not approve an algorithm patch; it only confirms regression pressure packet integrity.

## Repro Command
```bash
python3 research/prognostics/check_panel_day_engine_fault_family_regression_prepatch_gate_v1.py --packet-input /private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv --output-dir /private/tmp/fault_family_regression_prepatch_gate_check
```
