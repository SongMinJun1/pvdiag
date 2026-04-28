<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_065_LOCAL_MORPHOLOGY_FAMILY_SHAPE_REVIEW_V1

## Purpose
- BR-064의 `local_morphology_family_candidate_review` 10건을 실제 panel-day shape 지표로 다시 본다.
- 목표는 family를 억지로 붙이는 것이 아니라, family-shape evidence가 있는 행과 recovery-only hold 행을 분리하는 것이다.
- 이번 단계도 audit-only이며 production verdict, operator promotion, engine patch 후보를 만들지 않는다.

## Builder
- builder:
  - `research/prognostics/build_panel_day_engine_local_morphology_family_shape_review_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_local_morphology_family_shape_review_v1.py`

## Inputs
- BR-064 packet:
  - `/private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv`
- read-only panel-day core:
  - `/Users/b9gc/pvdiag/data/<site>/out/panel_day_core.csv`

## Outputs
- `/private/tmp/local_morphology_family_shape_review_check/panel_day_engine_local_morphology_family_shape_review_v1.csv`
- `/private/tmp/local_morphology_family_shape_review_check/panel_day_engine_local_morphology_family_shape_review_summary_v1.csv`
- `/private/tmp/local_morphology_family_shape_review_check/panel_day_engine_local_morphology_family_shape_review_note_v1.md`

## Real Data Result
- detail rows: `10`
- two-axis review ready rows: `2`
- operator promotion allowed sum: `0`
- engine patch candidate sum: `0`

## Shape Summary
| family_shape_judgment_bucket | site | cases | interpretation |
| --- | --- | ---: | --- |
| `recovery_recurrence_only_no_family_shape_hold` | `conalog` | 6 | recurrence/recovery is visible, but hard/family-shape evidence is weak |
| `recovery_recurrence_only_no_family_shape_hold` | `gangui` | 1 | event/recovery evidence exists, but family-shape threshold is not defensible |
| `recovery_recurrence_only_no_family_shape_hold` | `ktc_ess` | 1 | recurrence evidence exists, but no direct family-shape assignment yet |
| `voltage_dominant_hard_signal_review` | `gangui` | 1 | hard signal plus voltage-dominant morphology; partial-open vs measurement/reference artifact must be separated |
| `voltage_dominant_hard_signal_review` | `ktc_ess` | 1 | hard signal plus voltage-dominant morphology; do not over-read as diode despite a few VI-shape days |

## Important Correction
- Initial shape reading could over-classify the KTC row as diode/substring because it had `diode_vi_shape_days = 3`.
- But the same row had `voltage_dominant_low_days = 111`.
- Therefore BR-065 prioritizes the dominant shape pattern:
  - many voltage-dominant hard-signal days > a few diode-like days
  - result bucket: `voltage_dominant_hard_signal_review`
- This is exactly why the family-shape layer is needed before thresholding.

## Decision
- BR-065 keeps 8 rows as recovery/recurrence-only hold.
- BR-065 promotes 0 rows to operator-facing result.
- BR-065 authorizes 0 direct engine patches.
- The next safe step is a focused review of the 2 `voltage_dominant_hard_signal_review` rows.
  - Required distinction: partial-open/contact issue vs measurement/reference artifact.
  - Only after that distinction is evidence-backed should a threshold candidate be proposed.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_local_morphology_family_shape_review_v1.py research/prognostics/smoke_test_panel_day_engine_local_morphology_family_shape_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_local_morphology_family_shape_review_v1.py
python3 research/prognostics/build_panel_day_engine_local_morphology_family_shape_review_v1.py --packet-input /private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv --data-root /Users/b9gc/pvdiag/data --output-dir /private/tmp/local_morphology_family_shape_review_check
```
