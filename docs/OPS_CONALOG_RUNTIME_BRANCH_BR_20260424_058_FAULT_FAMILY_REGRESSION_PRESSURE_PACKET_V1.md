<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_058_FAULT_FAMILY_REGRESSION_PRESSURE_PACKET_V1

## Purpose
- BR-057에서 분리한 `fault_family_regression_seed_flag = 11`을 반례/회귀 pressure packet으로 고정한다.
- 목적은 strong same-day evidence가 있어도 target exact-family closure나 operator promotion으로 오독하지 않게 만드는 것이다.
- 이 패치는 runtime verdict, threshold, row universe, operator-facing semantics를 바꾸지 않는다.

## Builder
- script:
  - `research/prognostics/build_panel_day_engine_fault_family_regression_pressure_packet_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_fault_family_regression_pressure_packet_v1.py`

## Input
- BR-057 exact-family closure readiness review:
  - `/private/tmp/exact_family_closure_readiness_review_check/panel_day_engine_exact_family_closure_readiness_review_v1.csv`

## Outputs
- `/private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv`
- `/private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_summary_v1.csv`
- `/private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_note_v1.md`

## Real Data Result
- packet rows:
  - `11`
- non-target hard same-day fault-family seeds:
  - `5`
- sensor-feedback ambiguity pressure seeds:
  - `6`
- target exact closure candidates:
  - `0`
- operator promotion allowed:
  - `0`
- engine patch candidates:
  - `0`

## Packet Buckets
| packet bucket | counterexample bucket | site | raw top1 | cases | role |
|---|---|---|---|---:|---|
| `non_target_hard_same_day_fault_family_seed` | `fault_family_boundary_pressure` | `conalog` | `다이오드·서브스트링형` | 3 | non-target family boundary regression seed |
| `non_target_hard_same_day_fault_family_seed` | `fault_family_boundary_pressure` | `conalog` | `접속·부분개방형` | 1 | non-target family boundary regression seed |
| `non_target_hard_same_day_fault_family_seed` | `fault_family_boundary_pressure` | `gangui` | `접속·부분개방형` | 1 | non-target family boundary regression seed |
| `sensor_feedback_hard_same_day_ambiguity_pressure` | `mlpe_ambiguous` | `gangui` | `센서·피드백형` | 6 | ambiguity/hold regression pressure |

## Regression Assertion
- Every packet row must remain:
  - `target_exact_closure_candidate_flag = 0`
  - `operator_promotion_allowed_flag = 0`
  - `engine_patch_candidate_flag = 0`
- Non-target hard same-day evidence must not be reinterpreted as missing target exact-family closure.
- Sensor-feedback hard same-day evidence must remain ambiguity/hold pressure unless a separate decision adds stronger evidence.

## Interpretation
- The packet is useful because the rows are strong enough to break sloppy future rules.
- The packet is not an approval to widen current runtime rules.
- These rows should be used before any future `panel_day_engine.py` patch as regression/counterexample pressure.
- Exact target-family closure remains open.

## Decision
- Accept BR-058 as the regression/counterexample packet for BR-057 seeds.
- Link this packet from the counterexample set and Gate 7 order.
- Do not open an engine patch from this packet.

## Repro Command
```bash
python3 research/prognostics/build_panel_day_engine_fault_family_regression_pressure_packet_v1.py --readiness-input /private/tmp/exact_family_closure_readiness_review_check/panel_day_engine_exact_family_closure_readiness_review_v1.csv --output-dir /private/tmp/fault_family_regression_pressure_packet_check
```
