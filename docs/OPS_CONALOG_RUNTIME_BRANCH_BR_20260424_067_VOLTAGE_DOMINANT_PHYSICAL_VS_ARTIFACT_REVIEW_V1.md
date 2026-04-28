<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_067_VOLTAGE_DOMINANT_PHYSICAL_VS_ARTIFACT_REVIEW_V1

## Purpose
- Follow BR-066's handoff target: inspect only the 2 BR-065 `voltage_dominant_hard_signal_review` rows.
- Separate panel-local physical voltage-axis evidence from measurement/reference/common-cause artifact evidence.
- Keep the result as audit-only review evidence; do not create operator promotion or direct engine patch candidates.

## Builder
- builder:
  - `research/prognostics/build_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py`

## Inputs
- BR-065 shape review:
  - `/private/tmp/local_morphology_family_shape_review_check/panel_day_engine_local_morphology_family_shape_review_v1.csv`
- read-only panel-day core:
  - `/Users/b9gc/pvdiag/data/<site>/out/panel_day_core.csv`

## Outputs
- `/private/tmp/voltage_dominant_physical_vs_artifact_review_check/panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.csv`
- `/private/tmp/voltage_dominant_physical_vs_artifact_review_check/panel_day_engine_voltage_dominant_physical_vs_artifact_review_summary_v1.csv`
- `/private/tmp/voltage_dominant_physical_vs_artifact_review_check/panel_day_engine_voltage_dominant_physical_vs_artifact_review_note_v1.md`

## Real Data Result
- detail rows: `2`
- physical-leaning voltage-axis review rows: `2`
- artifact/reference hold rows: `0`
- two-axis review ready rows: `2`
- operator promotion allowed sum: `0`
- engine patch candidate sum: `0`

## Detail Snapshot
| site | panel_id | target_vdom_signal_days | target_v_ref_ok_rate | target_data_bad_days | target_no_ref_days | peer_median_vdom_frac | peer_max_vdom_frac | physical_score | artifact_score | bucket |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `gangui` | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7` | 146 | 1.000000 | 0 | 0 | 0.013100 | 0.103030 | 9 | 0 | `physical_leaning_voltage_axis_review` |
| `ktc_ess` | `70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4` | 111 | 0.981982 | 0 | 2 | 0.000000 | 0.021858 | 9 | 0 | `physical_leaning_voltage_axis_review` |

## Interpretation
- Both rows have many target-panel voltage-dominant signal days.
- Peer voltage-dominant breadth is low:
  - `gangui` median peer vdom fraction `0.013100`, max `0.103030`
  - `ktc_ess` median peer vdom fraction `0.000000`, max `0.021858`
- Target data-bad days are `0` for both rows.
- Reference is not perfectly clean for `ktc_ess` because `no_ref_days = 2`, but the target v-ref ok rate is still `0.981982`, so this is not enough to classify as artifact/reference hold.
- Therefore BR-067 reads both rows as `physical_leaning_voltage_axis_review`.
- This is still not a confirmed physical fault family.
  - It only says artifact/reference evidence is currently weaker than panel-local voltage-axis evidence.

## Decision
- BR-067 keeps the 2 rows as review candidates.
- BR-067 promotes 0 rows to operator-facing result.
- BR-067 authorizes 0 direct engine patches.
- Next evidence should be physical confirmation material, such as waveform/IV shape, maintenance evidence, repeated same panel channel evidence, or an independently reproducible voltage-axis signature.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py research/prognostics/smoke_test_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py
python3 research/prognostics/build_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py --shape-input /private/tmp/local_morphology_family_shape_review_check/panel_day_engine_local_morphology_family_shape_review_v1.csv --data-root /Users/b9gc/pvdiag/data --output-dir /private/tmp/voltage_dominant_physical_vs_artifact_review_check
```
