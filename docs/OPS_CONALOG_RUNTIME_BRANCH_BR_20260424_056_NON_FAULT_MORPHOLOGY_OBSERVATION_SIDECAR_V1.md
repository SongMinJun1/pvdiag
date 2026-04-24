<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_056_NON_FAULT_MORPHOLOGY_OBSERVATION_SIDECAR_V1

## Purpose
- BR-055에서 남은 `near_anchor_1_3d` report-observation 후보 3건을 별도 sidecar로 고정한다.
- 목적은 `미확정` 상태-gated morphology를 fault promotion이나 engine bug로 오해하지 않도록, analyst/review evidence로만 읽히게 하는 것이다.
- 이 패치는 runtime verdict, threshold, row universe, operator-facing semantics를 바꾸지 않는다.

## Builder
- script:
  - `research/prognostics/build_panel_day_engine_non_fault_morphology_observation_sidecar_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_non_fault_morphology_observation_sidecar_v1.py`

## Input
- BR-055 gap review:
  - `/private/tmp/no_report_heuristic_gap_review_check/panel_day_engine_no_report_heuristic_gap_review_v1.csv`

## Outputs
- `/private/tmp/non_fault_morphology_observation_sidecar_check/panel_day_engine_non_fault_morphology_observation_sidecar_v1.csv`
- `/private/tmp/non_fault_morphology_observation_sidecar_check/panel_day_engine_non_fault_morphology_observation_sidecar_summary_v1.csv`
- `/private/tmp/non_fault_morphology_observation_sidecar_check/panel_day_engine_non_fault_morphology_observation_sidecar_note_v1.md`

## Selection Rule
- `report_patch_candidate_flag == 1`
- `engine_patch_candidate_flag == 0`
- `date_alignment_gap_type == near_anchor_1_3d`
- `heuristic_attachment_gap_type == expected_absent_non_fault_status_gate`
- `raw_audit_status_ko == 미확정`
- `raw_final_status_ko == 미확정`
- hard fault row counts are all zero:
  - `raw_fault_like_row_count = 0`
  - `raw_final_fault_row_count = 0`
  - `raw_critical_fault_row_count = 0`

## Real Data Result
- observation sidecar rows:
  - `3`
- site split:
  - `conalog = 2`
  - `gangui = 1`
- signal basis split:
  - `early_warning_only = 2`
  - `early_warning_plus_recovery = 1`
- operator promotion allowed:
  - `0`
- engine patch candidates:
  - `0`
- report observation sidecar rows:
  - `3`

## Site Summary
| site | observation scope | gap type | signal basis | panels | operator promotion allowed | engine patch candidates |
|---|---|---|---|---:|---:|---:|
| `conalog` | `near_anchor_non_fault_morphology` | `near_anchor_1_3d` | `early_warning_only` | 2 | 0 | 0 |
| `gangui` | `near_anchor_non_fault_morphology` | `near_anchor_1_3d` | `early_warning_plus_recovery` | 1 | 0 | 0 |

## Interpretation
- These rows are plausible local morphology observations near a non-fault anchor.
- They are not fault rows:
  - raw-only audit/final status remains `미확정`.
  - hard fault row counts are all zero.
- They are not evidence for a `panel_day_engine.py` heuristic bug:
  - BR-055 already showed the missing heuristic rows are expected because the heuristic is fault-status gated.
- They do not close the exact-family gap.
- Their safe role is an analyst/review sidecar that can preserve morphology context without changing operator-facing fault output.

## Decision
- Accept BR-056 as a sidecar-only closure for the 3 near-anchor non-fault morphology rows.
- Do not promote these rows to `전조형 고장`.
- Do not open an engine patch from these rows.
- Keep exact-family closure open.

## Repro Command
```bash
python3 research/prognostics/build_panel_day_engine_non_fault_morphology_observation_sidecar_v1.py --gap-review-input /private/tmp/no_report_heuristic_gap_review_check/panel_day_engine_no_report_heuristic_gap_review_v1.csv --output-dir /private/tmp/non_fault_morphology_observation_sidecar_check
```
