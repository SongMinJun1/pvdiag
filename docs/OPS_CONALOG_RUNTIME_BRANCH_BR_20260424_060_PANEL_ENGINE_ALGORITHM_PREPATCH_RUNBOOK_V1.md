<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_060_PANEL_ENGINE_ALGORITHM_PREPATCH_RUNBOOK_V1

## Purpose
- Direct `pv_ae/panel_day_engine.py` algorithm patches now need one executable prepatch runbook before code review.
- BR-060 combines the BR-054 panel-engine patch safety gate with the BR-059 fault-family regression prepatch gate.
- This patch does not change runtime verdicts, thresholds, row universe, package outputs, or operator-facing semantics.

## Runbook
- script:
  - `research/prognostics/check_panel_day_engine_algorithm_prepatch_runbook_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_algorithm_prepatch_runbook_v1.py`

## Inputs
- panel-engine safety gate:
  - current repo diff against `HEAD` unless `--changed-paths-file` is supplied
- BR-058 pressure packet:
  - `/private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv`

## Outputs
- `/private/tmp/panel_engine_algorithm_prepatch_runbook_check/panel_day_engine_algorithm_prepatch_runbook_v1.csv`
- `/private/tmp/panel_engine_algorithm_prepatch_runbook_check/panel_day_engine_algorithm_prepatch_runbook_summary_v1.csv`
- nested panel-engine safety gate outputs:
  - `/private/tmp/panel_engine_algorithm_prepatch_runbook_check/panel_engine_patch_safety_gate/`
- nested fault-family regression gate outputs:
  - `/private/tmp/panel_engine_algorithm_prepatch_runbook_check/fault_family_regression_prepatch_gate/`

## Required Gate Rules
- Both sub-gates must report `overall_status = pass`.
- The panel-engine safety gate must keep direct engine edits tied to the BR-054 contract:
  - decision docs,
  - safety/shadow evidence,
  - smoke coverage,
  - source/package pair consistency,
  - public behavior docs when behavior can change.
- The fault-family regression gate must preserve the BR-058 pressure packet:
  - packet rows remain `11`,
  - target exact closure candidates remain `0`,
  - operator promotion allowed remains `0`,
  - engine patch candidates remain `0`.

## Real Data Result
- runbook gate count:
  - `2`
- passed gates:
  - `2`
- failed gates:
  - `0`
- panel-engine gate status:
  - `pass`
- fault-family gate status:
  - `pass`
- engine change detected in this run:
  - `0`
- fault-family packet rows:
  - `11`
- target exact closure candidates:
  - `0`
- operator promotion allowed:
  - `0`
- engine patch candidates:
  - `0`

## Decision
- Accept BR-060 as the executable prepatch runbook for any future direct panel-engine algorithm patch.
- Passing BR-060 does not approve an algorithm patch.
- A passing runbook only means the patch discussion may start from a clean safety baseline.
- If either sub-gate fails, the algorithm patch is blocked until the failed gate is resolved.

## Repro Command
```bash
python3 research/prognostics/check_panel_day_engine_algorithm_prepatch_runbook_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --packet-input /private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv --output-dir /private/tmp/panel_engine_algorithm_prepatch_runbook_check
```
