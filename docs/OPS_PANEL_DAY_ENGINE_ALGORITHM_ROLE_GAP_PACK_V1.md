# OPS PANEL DAY ENGINE ALGORITHM ROLE GAP PACK V1

## Purpose

This is a non-core audit/documentation pack.

It does not change detector logic.
It does not change the canonical truth contract.

Its job is to close the remaining roadmap-0 gap by formalizing:

1. what the main algorithm does
2. what the kernel-log algorithm does
3. what the GPV-based algorithm does
4. how the three axes interact in the current project
5. where the remaining boundary and uncertainty still remain

## Why This Is The Right Next Step

The project already has:

- current-data freeze boundaries
- final decision / handoff boundaries
- operator workflow choice

But those packs mainly answer:

- what we can say now
- what we should not overclaim now

They do not by themselves fix the role confusion between:

- the main project event-type axis
- the kernel-log symptom-name axis
- the GPV external-reference axis

This pack exists so that internal transfer and reporting do not mix those three responsibilities together.

## Inputs

- `_share/panel_day_engine_project_final_decision_pack_v1.csv`
- `_share/panel_day_engine_project_current_data_freeze_pack_v1.csv`
- `_share/panel_day_engine_project_handoff_summary_v1.csv`
- `_share/panel_day_engine_project_eval_matrix_v1.csv`
- `_share/panel_day_engine_non_precursor_performance_cases_v1.csv`
- `_share/panel_day_engine_operator_attention_policy_recommendation_v1.csv`
- `_share/panel_day_engine_operator_pipeline_manifest_v1.csv`
- current repo-local docs/notes where kernel-log or GPV references already exist

## Outputs

- `_share/panel_day_engine_algorithm_role_map_v1.csv`
- `_share/panel_day_engine_algorithm_gap_map_v1.csv`
- `_share/panel_day_engine_algorithm_decision_flow_v1.md`

## Core Interpretation

### 1) Main Algorithm

The main algorithm owns the project's primary event-type decision flow.

It is the axis that decides:

- precursor-bearing fault
- abrupt/no-precursor fault
- common-cause / together-moving anomaly
- recurring anomaly
- false-positive style rows

It also owns the current onset/performance/operator-workflow base axis.

It does **not** directly finalize precise physical root-cause names.

### 2) Kernel-Log Algorithm

The kernel-log algorithm is the symptom-name and cause-family naming axis.

Typical labels here are:

- 출력 저하형
- 전압 변화형
- 패턴 이상형
- 불안정형
- 복합형

And where stored truth supports it, the naming layer may also use:

- 다이오드형
- 개방·장치이상형
- 모듈손상형

This axis does **not** own the main event-type decision flow.

### 3) GPV-Based Algorithm

The GPV-based algorithm is the external/reference axis.

It is used for:

- benchmark comparison
- outside-data support
- coarse external family reference

It does **not** own the current project's final field decision.

## Current Decision Order

The current order must be read as:

1. the main algorithm decides the event type first
2. the kernel-log algorithm adds symptom/cause-family naming
3. the GPV-based algorithm is used only as an external reference axis

This is the intended current priority order.

## Remaining Boundary

This pack formalizes the role split, but it does not erase the current-data limits.

So the remaining boundary is:

- event-type interpretation can be frozen only within the already-defined current-data limits
- kernel-log naming remains a secondary interpretation layer
- GPV remains an external benchmark/reference layer
- precise physical root-cause finalization remains limited unless stored truth directly supports it

## Why This Pack Is Human-Facing

This is not another metric table for a paper appendix.

It is a handoff/control document so that internal readers can answer:

- which algorithm is deciding what
- which algorithm is only renaming or interpreting
- which algorithm is only external support

That is why the outputs are framed as:

- a role map
- a gap/boundary map
- a short Korean decision-flow markdown

## Smoke Coverage

The smoke test verifies:

- scripts compile
- the three required algorithm rows are emitted
- the required gap topics are emitted
- the decision-flow markdown sections are emitted
- official outputs are not modified by the smoke

## Reproduction

```bash
python -m py_compile research/prognostics/build_panel_day_engine_algorithm_role_gap_pack_v1.py research/prognostics/smoke_test_panel_day_engine_algorithm_role_gap_pack_v1.py
python research/prognostics/build_panel_day_engine_algorithm_role_gap_pack_v1.py
python research/prognostics/smoke_test_panel_day_engine_algorithm_role_gap_pack_v1.py
```
