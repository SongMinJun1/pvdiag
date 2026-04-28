<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_064_FAULT_FAMILY_JUDGMENT_CANDIDATE_PACKET_V1

## Purpose
- BR-063 이후 바로 큰 semantic engine patch로 가지 않는다.
- 먼저 fault-family별 판단 기준 후보를 audit-only packet으로 분리한다.
- `duration/gap`, `continuity/recurrence`, `spatiality/common-cause`를 한 임계치로 섞지 않고 별도 축으로 유지한다.

## Builder
- builder:
  - `research/prognostics/build_panel_day_engine_fault_family_judgment_candidate_packet_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_fault_family_judgment_candidate_packet_v1.py`

## Inputs
- cross-axis review:
  - `/private/tmp/cross_axis_manifest_sync_review_check/panel_day_engine_cross_axis_manifest_sync_review_v1.csv`
- fault-family regression pressure packet:
  - `/private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv`
- threshold candidate seed:
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_THRESHOLD_CANDIDATE_V1.csv`
- fault subtype hypothesis map:
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_018_FAULT_SUBTYPE_HYPOTHESIS_MAP_V1.csv`

## Outputs
- `/private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv`
- `/private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_summary_v1.csv`
- `/private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_criteria_v1.csv`
- `/private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_note_v1.md`

## Real Data Result
- detail rows: `209`
- criteria rows: `17`
- operator promotion allowed sum: `0`
- engine patch candidate sum: `0`

## Bucket Summary
| judgment_bucket | candidate_family_label_ko | cases |
| --- | --- | ---: |
| `block_individual_precursor_common_cause` | `외부계통·공통원인 계열` | 50 |
| `hold_subgroup_or_breadth_context` | `외부계통·공통원인 계열` | 126 |
| `fault_family_regression_pressure_seed` | `다이오드·서브스트링 계열` | 3 |
| `fault_family_regression_pressure_seed` | `접속 불량·부분 개방 계열` | 2 |
| `fault_family_regression_pressure_seed` | `센서·피드백·계측 이상 계열` | 6 |
| `local_morphology_family_candidate_review` | `unassigned_family_needs_shape_review` | 10 |
| `weak_context_hold_review` | `unassigned_family_needs_shape_review` | 12 |

## Interpretation
- `block_individual_precursor_common_cause` rows are not panel-local precursor evidence.
  - They must be split as common-cause / spatiality blockers before any individual panel promotion discussion.
- `hold_subgroup_or_breadth_context` rows are context only.
  - They may guide review but cannot close a panel-local fault-family threshold.
- `fault_family_regression_pressure_seed` rows are counterexample material only.
  - They keep BR-058 pressure seeds alive without turning them into promotion or engine patch candidates.
- `local_morphology_family_candidate_review` is the next useful inspect pool.
  - It has recovery/recurrence pressure with weak common-cause context, but still lacks family-shape assignment.

## Decision
- BR-064 is review-only.
- No production result, runtime verdict, or `panel_day_engine.py` semantic behavior is changed.
- The next safe step is to inspect the `10` local morphology rows for family-shape evidence before thresholding.
- A later engine patch must still pass BR-060 runbook, BR-061 scorecard, and BR-062 compare.

## Repro Commands
```bash
python3 -m py_compile research/prognostics/build_panel_day_engine_fault_family_judgment_candidate_packet_v1.py research/prognostics/smoke_test_panel_day_engine_fault_family_judgment_candidate_packet_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_fault_family_judgment_candidate_packet_v1.py
python3 research/prognostics/build_panel_day_engine_fault_family_judgment_candidate_packet_v1.py --cross-axis-input /private/tmp/cross_axis_manifest_sync_review_check/panel_day_engine_cross_axis_manifest_sync_review_v1.csv --pressure-input /private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv --threshold-input docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_THRESHOLD_CANDIDATE_V1.csv --subtype-input docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_018_FAULT_SUBTYPE_HYPOTHESIS_MAP_V1.csv --output-dir /private/tmp/fault_family_judgment_candidate_packet_check
```
